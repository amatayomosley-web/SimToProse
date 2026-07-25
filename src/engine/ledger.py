"""ledger.py — the event-sourced spine: append-only log + atomic turn-commit + pure fold + resume.

Contracts implemented here:
  world-state-ledger.md — event log (two clocks) + folded snapshot; the fold is the ONLY way the
                          snapshot changes — a pure function of the log.
  run-lifecycle.md      — the TURN-COMMIT atomic unit; resume = snapshot + log-tail replay with the
                          fold-forward determinism ASSERTED (divergence aborts loudly, never papers over).
  record-contract.md    — recall / decision-manifest / relationship-delta writes ride the same commit.

Storage is SQLite behind this class only — the seam that keeps a future polystore swap reversible.
"""
import json
import os
from datetime import datetime, timezone

from . import db
from .records import TurnCommit, RecordError

SNAPSHOT_KINDS = ("agents", "holdings", "information", "relationships", "tensions", "clock")


class LedgerError(RuntimeError):
    """A spine invariant was violated (duplicate commit, divergent resume, unknown run). Never caught-and-continued."""


def _now():
    return datetime.now(timezone.utc).isoformat()


class Ledger:
    def __init__(self, db_path):
        self.con = db.connect(db_path)

    # ---- run lifecycle -------------------------------------------------------------------------
    def create_run(self, run_id, config):
        if not isinstance(run_id, str) or not run_id.strip():
            raise RecordError("run_id must be a non-empty string")
        if not isinstance(config, dict) or "catalog_version" not in config:
            raise RecordError("run config must be a dict carrying at least catalog_version (run-lifecycle.md)")
        with self.con:
            self.con.execute("INSERT INTO runs (run_id, created_at, config) VALUES (?, ?, ?)",
                             (run_id, _now(), json.dumps(config)))
        return run_id

    def load_run(self, run_id):
        row = self.con.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise LedgerError("unknown run %r" % run_id)
        return {"run_id": row["run_id"], "created_at": row["created_at"],
                "status": row["status"], "config": json.loads(row["config"])}

    def set_status(self, run_id, status):
        self.load_run(run_id)
        with self.con:
            self.con.execute("UPDATE runs SET status = ? WHERE run_id = ?", (status, run_id))

    def register_character(self, run_id, char_id, fixed, baseline):
        self.load_run(run_id)
        if not isinstance(fixed, dict) or not isinstance(baseline, dict):
            raise RecordError("fixed and baseline must be dicts")
        with self.con:
            self.con.execute("INSERT INTO characters (run_id, char_id, fixed, baseline) VALUES (?, ?, ?, ?)",
                             (run_id, char_id, json.dumps(fixed), json.dumps(baseline)))

    # ---- the atomic turn-commit (run-lifecycle.md: together or not at all) ----------------------
    def append_turn(self, commit):
        if not isinstance(commit, TurnCommit):
            raise RecordError("append_turn takes a TurnCommit, got %r" % type(commit).__name__)
        commit.validate()
        run = self.load_run(commit.run_id)
        if run["status"] != "active":
            raise LedgerError("run %r is %s — appending to a non-active run" % (commit.run_id, run["status"]))
        try:
            with self.con:  # one transaction: every row below lands, or none do
                for ev in commit.events:
                    caused = commit.turn if ev.caused_at is None else ev.caused_at
                    effective = caused if ev.effective_at is None else ev.effective_at
                    self.con.execute(
                        "INSERT INTO events (run_id, turn, caused_at, effective_at, type, actor, target, location, visibility, payload) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (commit.run_id, commit.turn, caused, effective, ev.type, ev.actor, ev.target,
                         ev.location, ev.visibility, json.dumps(ev.payload)))
                self.con.execute(
                    "INSERT INTO turns (run_id, turn, actor, thought, action, tags, validation, committed_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (commit.run_id, commit.turn, commit.actor, commit.thought, commit.action,
                     json.dumps(commit.tags), json.dumps(commit.validation), _now()))
                self.con.execute(
                    "INSERT INTO current_state (run_id, char_id, turn, affect, condition) VALUES (?, ?, ?, ?, ?)",
                    (commit.run_id, commit.actor, commit.turn, json.dumps(commit.affect), json.dumps(commit.condition)))
                if commit.recall is not None:
                    self.con.execute("INSERT INTO recall_events (run_id, turn, actor, belief_refs) VALUES (?, ?, ?, ?)",
                                     (commit.run_id, commit.turn, commit.actor, json.dumps(commit.recall)))
                if commit.manifest is not None:
                    self.con.execute("INSERT INTO decision_manifests (run_id, turn, actor, manifest) VALUES (?, ?, ?, ?)",
                                     (commit.run_id, commit.turn, commit.actor, json.dumps(commit.manifest)))
                for rd in commit.rel_deltas:
                    self.con.execute(
                        "INSERT INTO relationship_deltas (run_id, turn, perceiver, target, axis, delta, cause_event) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (commit.run_id, commit.turn, rd.perceiver, rd.target, rd.axis, float(rd.delta), rd.cause_event))
        except Exception as exc:
            if isinstance(exc, (LedgerError, RecordError)):
                raise
            raise LedgerError("turn-commit (run=%s turn=%s actor=%s) rolled back: %s"
                              % (commit.run_id, commit.turn, commit.actor, exc)) from exc

    def record_turn_skipped(self, run_id, turn, actor, reason):
        """run-lifecycle.md failure handling: a skipped character-turn is a RECORDED event, never a
        silent skip — it changes the scene; the record must say so. Its own single-insert atomic unit
        (there is no TurnCommit to ride: the skip means no affect/decision was produced)."""
        self.load_run(run_id)
        with self.con:
            self.con.execute(
                "INSERT INTO events (run_id, turn, caused_at, effective_at, type, actor, visibility, payload) "
                "VALUES (?, ?, ?, ?, 'turn-skipped', ?, 'public', ?)",
                (run_id, turn, turn, turn, actor, json.dumps({"reason": str(reason)[:200]})))

    def append_arc_diff(self, run_id, char_id, turn, diff):
        """Persist a durable baseline diff (arc-engine.md) to the arc_diffs table — the arc's
        write-record. One diff per (run, char, turn); resume replays them onto the baseline."""
        if not isinstance(diff, dict):
            raise RecordError("arc diff must be a dict")
        self.load_run(run_id)
        with self.con:
            self.con.execute(
                "INSERT OR REPLACE INTO arc_diffs (run_id, char_id, turn, diff) VALUES (?, ?, ?, ?)",
                (run_id, char_id, turn, json.dumps(diff)))

    def append_acquisition(self, run_id, char_id, turn, belief):
        """Persist a belief the character ACQUIRED this run (knowledge-model.md §acquisition): the
        simulated twin of an authored .md seed, provenance distinguishing them. One row per acquired
        belief. run_turn folds it forward in-session; resume-replay shares the arc_diffs gap."""
        if not isinstance(belief, dict) or "claim" not in belief:
            raise RecordError("acquisition belief must be a dict carrying a claim")
        self.load_run(run_id)
        with self.con:
            self.con.execute(
                "INSERT INTO acquisitions (run_id, char_id, turn, belief) VALUES (?, ?, ?, ?)",
                (run_id, char_id, turn, json.dumps(belief)))

    def acquisitions_for(self, run_id, char_id):
        """Every belief char_id acquired this run, in acquisition order — the simulated additions to the
        seeded vault (rehydrate on resume by appending these to the .md seed)."""
        rows = self.con.execute(
            "SELECT belief FROM acquisitions WHERE run_id = ? AND char_id = ? ORDER BY turn, acquisition_id",
            (run_id, char_id)).fetchall()
        return [json.loads(r["belief"]) for r in rows]

    def arc_diffs_for(self, run_id, char_id):
        """Every durable baseline diff for char_id, in turn order — replay onto the seed baseline
        (arc.apply) to rehydrate the arc-evolved character on resume."""
        rows = self.con.execute(
            "SELECT diff FROM arc_diffs WHERE run_id = ? AND char_id = ? ORDER BY turn",
            (run_id, char_id)).fetchall()
        return [json.loads(r["diff"]) for r in rows]

    def append_scene(self, run_id, scene_no, label, pov, start_turn, end_turn):
        """Record a scene boundary — the committed turn range that forms one scene. Append-only; one
        row per (run, scene_no). The book's structure for the cutting room + book-scale narration."""
        self.load_run(run_id)
        with self.con:
            self.con.execute(
                "INSERT INTO scenes (run_id, scene_no, label, pov, start_turn, end_turn) VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, int(scene_no), str(label or ""), pov, int(start_turn), int(end_turn)))

    def scenes_for(self, run_id):
        """Every scene boundary for the run, in scene order — the book's structure."""
        rows = self.con.execute(
            "SELECT scene_no, label, pov, start_turn, end_turn FROM scenes WHERE run_id = ? ORDER BY scene_no",
            (run_id,)).fetchall()
        return [{"scene_no": r["scene_no"], "label": r["label"], "pov": r["pov"],
                 "start_turn": r["start_turn"], "end_turn": r["end_turn"]} for r in rows]

    def next_scene_no(self, run_id):
        """The next free scene number for the run (0 if none yet)."""
        row = self.con.execute("SELECT MAX(scene_no) AS m FROM scenes WHERE run_id = ?", (run_id,)).fetchone()
        return 0 if row["m"] is None else row["m"] + 1

    def log_llm_call(self, run_id, turn, purpose, model, tokens_in=None, tokens_out=None, scene=None):
        with self.con:
            self.con.execute(
                "INSERT INTO llm_calls (run_id, turn, purpose, model, tokens_in, tokens_out, scene) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, turn, purpose, model, tokens_in, tokens_out, scene))

    # ---- the fold: snapshot = pure function of the log (world-state-ledger.md) ------------------
    def _seed(self, run_id):
        snap = {kind: {} for kind in SNAPSHOT_KINDS}
        snap["clock"] = {"now": -1}
        for row in self.con.execute("SELECT char_id FROM characters WHERE run_id = ? ORDER BY char_id", (run_id,)):
            snap["agents"][row["char_id"]] = {"location": None, "life_status": "alive", "possessions": []}
        return snap

    @staticmethod
    def _project(snap, ev):
        """Apply ONE event to the snapshot. Projection rules are exactly the doc-named ones
        (world-state-ledger.md: move/seizure/reveal/betrayal/uprising). Types with no world_map
        (mundane, care, loss, threat — the probe's appraisal-only tags) correctly do not move the world."""
        etype, payload = ev["type"], json.loads(ev["payload"])
        agents = snap["agents"]
        if etype == "move" and ev["actor"]:
            agents.setdefault(ev["actor"], {"location": None, "life_status": "alive", "possessions": []})
            agents[ev["actor"]]["location"] = payload.get("to")
        elif etype == "harm" and payload.get("terminal"):
            victim = ev["target"] or ev["actor"]
            if victim:
                agents.setdefault(victim, {"location": None, "life_status": "alive", "possessions": []})
                agents[victim]["life_status"] = "dead"
        elif etype == "reveal" and "fact" in payload:
            knowers = set(snap["information"].get(payload["fact"], []))
            knowers.update(payload.get("to", []))
            snap["information"][payload["fact"]] = sorted(knowers)
        elif etype in ("seize", "destroy-asset") and "asset" in payload:
            snap["holdings"][payload["asset"]] = (
                {"destroyed": True} if etype == "destroy-asset" else {"controller": ev["actor"]})
        elif etype in ("betray", "bond") and ev["actor"] and ev["target"]:
            key = "%s|%s" % (ev["actor"], ev["target"])
            snap["relationships"][key] = {"standing": "enmity" if etype == "betray" else "alliance",
                                          "since": ev["effective_at"]}
        elif etype == "tension" and "name" in payload:
            snap["tensions"][payload["name"]] = {"temperature": payload.get("temperature"),
                                                 "factions": payload.get("factions", [])}
        return snap

    def _events_between(self, run_id, after_turn, up_to_turn):
        return self.con.execute(
            "SELECT * FROM events WHERE run_id = ? AND effective_at > ? AND effective_at <= ? "
            "ORDER BY effective_at, event_id", (run_id, after_turn, up_to_turn)).fetchall()

    def fold(self, run_id, as_of_turn):
        """From-zero fold: seed + every event whose effective_at has arrived, in log order."""
        self.load_run(run_id)
        snap = self._seed(run_id)
        for ev in self._events_between(run_id, -1, as_of_turn):
            self._project(snap, ev)
        snap["clock"] = {"now": as_of_turn}
        return snap

    def persist_snapshot(self, run_id, as_of_turn, snap):
        with self.con:
            self.con.execute("DELETE FROM snapshots WHERE run_id = ? AND as_of_turn = ?", (run_id, as_of_turn))
            for kind in SNAPSHOT_KINDS:
                for key, value in snap[kind].items() if kind != "clock" else [("now", snap["clock"]["now"])]:
                    self.con.execute(
                        "INSERT INTO snapshots (run_id, as_of_turn, kind, key, value) VALUES (?, ?, ?, ?, ?)",
                        (run_id, as_of_turn, kind, str(key), json.dumps(value)))

    def load_snapshot(self, run_id):
        """Latest persisted snapshot -> (as_of_turn, snap) or None."""
        row = self.con.execute("SELECT MAX(as_of_turn) AS t FROM snapshots WHERE run_id = ?", (run_id,)).fetchone()
        if row["t"] is None:
            return None
        as_of = row["t"]
        snap = {kind: {} for kind in SNAPSHOT_KINDS}
        for r in self.con.execute("SELECT kind, key, value FROM snapshots WHERE run_id = ? AND as_of_turn = ?",
                                  (run_id, as_of)):
            if r["kind"] == "clock":
                snap["clock"] = {"now": json.loads(r["value"])}
            else:
                snap[r["kind"]][r["key"]] = json.loads(r["value"])
        return as_of, snap

    def latest_turn(self, run_id):
        row = self.con.execute("SELECT MAX(turn) AS t FROM turns WHERE run_id = ?", (run_id,)).fetchone()
        return -1 if row["t"] is None else row["t"]

    def latest_affect(self, run_id, char_id):
        row = self.con.execute(
            "SELECT affect, condition FROM current_state WHERE run_id = ? AND char_id = ? ORDER BY turn DESC LIMIT 1",
            (run_id, char_id)).fetchone()
        if row is None:
            return None
        return {"affect": json.loads(row["affect"]), "condition": json.loads(row["condition"])}

    # ---- resume: snapshot + tail replay, determinism ASSERTED (run-lifecycle.md) ----------------
    def resume(self, run_id):
        """Load latest snapshot, replay the log tail, and assert the incremental fold equals the
        from-zero fold. Same log => same world, or this raises — a divergent resume is a bug to fix,
        not to paper over (no-fallbacks discipline)."""
        t = self.latest_turn(run_id)
        cached = self.load_snapshot(run_id)
        if cached is None:
            incremental = self.fold(run_id, t)
        else:
            as_of, snap = cached
            snap = json.loads(json.dumps(snap))  # deep copy; JSON-shaped by construction
            for ev in self._events_between(run_id, as_of, t):
                self._project(snap, ev)
            snap["clock"] = {"now": t}
            incremental = snap
        full = self.fold(run_id, t)
        if incremental != full:
            raise LedgerError(
                "RESUME DIVERGENCE on run %r at turn %d: snapshot+tail replay != from-zero fold. "
                "The cached snapshot or the projection is corrupt — refusing to resume." % (run_id, t))
        self.persist_snapshot(run_id, t, full)
        return {"turn": t, "snapshot": full}
