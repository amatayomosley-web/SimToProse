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

import sqlite3

from . import db
from . import clock as _clock
from . import snapshots as _snap
from . import writeonce as _once
from . import fold as _fold
from .records import TurnCommit, RecordError
from .errors import EngineError

SNAPSHOT_KINDS = _snap.KINDS      # re-exported: several modules import it from here

class LedgerError(EngineError):
    """A spine invariant was violated (duplicate commit, divergent resume, unknown run). Never caught-and-continued."""

def _now():
    return datetime.now(timezone.utc).isoformat()

class Ledger:
    def __init__(self, db_path):
        self.con = db.connect(db_path)

    # ---- run lifecycle -------------------------------------------------------------------------
    def create_run(self, run_id, config):
        if not isinstance(run_id, str) or not run_id.strip():
            raise RecordError("LEDGER_RUN_ID_EMPTY",
                          "create_run: run_id must be a non-empty string — the run id scopes every "
                          "read and every write in this database, so an empty one belongs to "
                          "everything or to nothing")
        if not isinstance(config, dict) or "catalog_version" not in config:
            raise RecordError("LEDGER_RUN_CONFIG_INVALID",
                          "create_run: run config must be a dict carrying at least "
                          "catalog_version (run-lifecycle.md)")
        _once.write_once(self.con,
            lambda: _once.refuse_duplicate(self.con,
                "SELECT 1 FROM runs WHERE run_id=?", (run_id,), "LEDGER_RUN_EXISTS",
                "create_run: run %r already exists; continuing one is --resume" % run_id, LedgerError),
            lambda: self.con.execute("INSERT INTO runs (run_id, created_at, config) VALUES (?, ?, ?)",
                                     (run_id, _now(), json.dumps(config))))
        return run_id

    def load_run(self, run_id):
        row = self.con.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise LedgerError("LEDGER_RUN_UNKNOWN",
                              "load_run: no run %r in this database" % run_id)
        return {"run_id": row["run_id"], "created_at": row["created_at"],
                "status": row["status"], "config": json.loads(row["config"])}

    def run_config(self, run_id):
        """The run's stored config dict — the pinned bible fingerprint among it.

        THIS DID NOT EXIST, and `scripts/scene.py` guarded its only use with
        `if hasattr(led, "run_config")` — always false, so the pinned-bible divergence check never
        once ran. A run pins the bible it ran against (CLAUDE.md hard rule 1) precisely so a
        mid-book edit cannot silently change what earlier turns were computed from; the detector
        for that was unreachable from the day it was written.
        """
        return self.load_run(run_id)["config"]

    def set_status(self, run_id, status):
        self.load_run(run_id)
        with self.con:
            self.con.execute("UPDATE runs SET status = ? WHERE run_id = ?", (status, run_id))

    def register_character(self, run_id, char_id, fixed, baseline):
        self.load_run(run_id)
        if not isinstance(fixed, dict) or not isinstance(baseline, dict):
            raise RecordError("LEDGER_CHARACTER_SHEET_INVALID",
                          "register_character: fixed and baseline must both be dicts")
        _once.write_once(self.con,
            lambda: _once.refuse_duplicate(self.con,
                "SELECT 1 FROM characters WHERE run_id=? AND char_id=?", (run_id, char_id),
                "LEDGER_CHARACTER_EXISTS",
                "register_character: %r is already in the cast of run %r" % (char_id, run_id),
                LedgerError),
            lambda: self.con.execute(
                "INSERT INTO characters (run_id, char_id, fixed, baseline) VALUES (?, ?, ?, ?)",
                (run_id, char_id, json.dumps(fixed), json.dumps(baseline))))

    # ---- the atomic turn-commit (run-lifecycle.md: together or not at all) ----------------------
    def append_turn(self, commit):
        if not isinstance(commit, TurnCommit):
            raise RecordError("LEDGER_NOT_A_TURN_COMMIT",
                          "append_turn takes a TurnCommit, got %r" % type(commit).__name__)
        commit.validate()
        run = self.load_run(commit.run_id)
        if run["status"] != "active":
            raise LedgerError("LEDGER_RUN_NOT_ACTIVE",
                              "append_turn: run %r is %s — appending to a non-active run"
                              % (commit.run_id, run["status"]))
        # ONE QUESTION, ASKED TWICE — before the write, and again if the constraint answered first.
        # `append_turn` writes many rows in one transaction and so cannot take `write_once`'s
        # single-write shape, but it gets the same totality from its own except branch.
        #
        # A CLOSURE RATHER THAN A TUPLE OF ARGUMENTS, which is not style: the first draft hoisted
        # these into `dup = (sql, params, code, msg)` and passed `dup[2]`, which moved the string
        # "LEDGER_TURN_EXISTS" out of call-argument position — where `tests/test_errors.py` reads
        # codes from the AST. Both halves of the two-way registry rule went red at once, reporting
        # the code as registered-but-never-raised while it was raised on the very next line.
        def refuse_if_duplicate():
            _once.refuse_duplicate(self.con,
                "SELECT 1 FROM turns WHERE run_id=? AND turn=? AND actor=?",
                (commit.run_id, commit.turn, commit.actor), "LEDGER_TURN_EXISTS",
                "append_turn: run %r already holds turn %d by %r" % (commit.run_id, commit.turn,
                                                                     commit.actor), LedgerError)

        refuse_if_duplicate()
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
                        "INSERT INTO relationship_deltas (run_id, turn, perceiver, target, axis, delta, ord, cause_event) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (commit.run_id, commit.turn, rd.perceiver, rd.target, rd.axis, float(rd.delta),
                         rd.order, rd.cause_event))
                # INSIDE the turn's transaction, not after it. `append_arc_diff` is called AFTER
                # append_turn (scripts/scene.py, scripts/direct.py), so a crash between the two
                # leaves the turn permanently committed with the diff lost — and `turns`' PRIMARY
                # KEY (run_id, turn, actor) refuses a re-append, so it cannot be recovered by
                # replaying the beat. A durable trait movement is exactly the thing that must not
                # be able to go missing, so it rides with the turn.
                for td in commit.toward_deltas:
                    self.con.execute(
                        "INSERT INTO toward_deltas (run_id, turn, perceiver, target, primary_, delta, source) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (commit.run_id, commit.turn, td.perceiver, td.target, td.primary,
                         float(td.delta), td.source or ""))
                for wd in commit.wound_deltas:
                    self.con.execute(
                        "INSERT INTO wound_deltas (run_id, char_id, turn, wound_id, delta, kind, source) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (commit.run_id, wd.char_id, commit.turn, wd.wound_id, float(wd.delta),
                         wd.kind, wd.source or ""))
        except Exception as exc:
            if isinstance(exc, (LedgerError, RecordError)):
                raise
            # THE CONSTRAINT MAY HAVE ANSWERED FIRST, but only a constraint can have. Gated on
            # IntegrityError since 2026-09-03: re-asking after ANY failure ran a SELECT on a
            # connection whose transaction had just died, for every unrelated fault.
            if isinstance(exc, sqlite3.IntegrityError):
                refuse_if_duplicate()
            # THE SAME LOCK, THE SAME CODE. This branch used to call a busy timeout
            # LEDGER_TURN_COMMIT_ROLLED_BACK while `write_once` let the identical condition out
            # raw — one module answering one condition two ways, which is why neither was noticed.
            db.refuse_if_busy(exc, "append_turn (run=%s turn=%s)" % (commit.run_id, commit.turn))
            raise LedgerError("LEDGER_TURN_COMMIT_ROLLED_BACK",
                              "turn-commit (run=%s turn=%s actor=%s) rolled back: %s"
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
            raise RecordError("LEDGER_ARC_DIFF_INVALID", "append_arc_diff: the diff must be a dict")
        self.load_run(run_id)
        payload = json.dumps(diff)
        # IDEMPOTENT REPLAY, REFUSED REWRITE. This was `INSERT OR REPLACE`, and as the table's only
        # writer it was also the only way a committed arc row could change — through the exact path
        # the v9 BEFORE DELETE trigger could not see (SQLite's REPLACE deletes without firing delete
        # triggers unless recursive_triggers is on; db.connect now sets it).
        #
        # Replay is legitimate: `--resume` re-walks committed turns by design, so an identical diff
        # arriving twice is the documented path and must be a no-op. A DIFFERING diff for the same
        # (run, char, turn) is history being rewritten, which is what hard rule 2 forbids.
        # THREE-ANSWER CHECK, which is why `write_once` takes a callable: absent -> write,
        # identical -> replay no-op, different -> refuse. Routed 2026-09-03; before that this was
        # the same pre-check-then-INSERT race the four spine writers had, in the spine itself.
        def _check():
            existing = self.con.execute(
                "SELECT diff FROM arc_diffs WHERE run_id=? AND char_id=? AND turn=?",
                (run_id, char_id, turn)).fetchone()
            if existing is None:
                return False
            if existing["diff"] == payload:
                return True                               # same turn, same diff — a replay
            raise LedgerError(
                "LEDGER_ARC_DIFF_REWRITE",
                "run %r char %r turn %s already carries a DIFFERENT arc diff.\n"
                "  stored: %s\n"
                "  new:    %s\n"
                "  arc_diffs is append-only (CLAUDE.md hard rule 2): a correction is a NEW row at a\n"
                "  new turn, never a rewritten one. An identical replay is a no-op and would not\n"
                "  have reached this."
                % (run_id, char_id, turn, existing["diff"], payload))

        _once.write_once(self.con, _check,
            lambda: self.con.execute(
                "INSERT INTO arc_diffs (run_id, char_id, turn, diff) VALUES (?, ?, ?, ?)",
                (run_id, char_id, turn, payload)))

    def append_acquisition(self, run_id, char_id, turn, belief):
        """Persist a belief the character ACQUIRED this run (knowledge-model.md §acquisition): the
        simulated twin of an authored .md seed, provenance distinguishing them. One row per acquired
        belief. run_turn folds it forward in-session; resume-replay shares the arc_diffs gap."""
        if not isinstance(belief, dict) or "claim" not in belief:
            raise RecordError("LEDGER_ACQUISITION_INVALID",
                          "append_acquisition: belief must be a dict carrying a claim")
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

    # ---- the DECLARED clock. Bodies in `clock.py`, which carries the contract; these stay so the
    # existing call sites are unchanged and the cause/derivation seam is visible from here.
    def declare_time(self, run_id, turn, elapsed, source=""):
        return _clock.declare(self.con, run_id, turn, elapsed, source, on_rewrite=LedgerError)

    def elapsed_since(self, run_id, turn):
        """Declared units between a turn and the head. One clock, four tiers — see `clock.py`."""
        return _clock.elapsed_since(self.con, run_id, turn)

    def timeline_for(self, run_id, char_id):
        """Declarations and edge movements INTERLEAVED in turn order — the input to bonds.rehydrate.

        Order is the whole point. Drift is multiplicative toward a resting prior; a delta is
        additive. They do not commute, so a fold that applies every drift and then every delta
        arrives at a different number than the run actually held. Returning them merged by turn is
        what makes the rebuild equal the live value rather than merely resemble it.

        -> [("time", elapsed) | ("edge", target, axis, delta, order)], ascending by turn.
        """
        rows = [(int(r["turn"]), 0, ("time", float(r["elapsed"]))) for r in self.con.execute(
            "SELECT turn, elapsed FROM time_declarations WHERE run_id = ?", (run_id,))]
        # BOTH ORDERS. Filtering to 'first' here would silently drop the second-order tier —
        # what the perceiver believes the OTHER holds — which `bonds.replay` has always folded and
        # which schema v8 exists to hold. A first draft of this reader did exactly that and
        # tests/test_bonds.py caught it.
        rows += [(int(r["turn"]), 1,
                  ("edge", r["target"], r["axis"], float(r["delta"]), r["ord"]))
                 for r in self.con.execute(
                     "SELECT turn, target, axis, delta, ord FROM relationship_deltas "
                     "WHERE run_id = ? AND perceiver = ?", (run_id, char_id))]
        # a declaration takes effect BEFORE the turn's own movements, hence the 0/1 tiebreak
        return [item for _t, _k, item in sorted(rows, key=lambda r: (r[0], r[1]))]

    def toward_deltas_for(self, run_id, perceiver):
        """Every micro movement this character made, in turn order — fold with `toward.replay`.

        The twin of `edge_deltas_for` and `wound_deltas_for`. Ordered by (turn, delta_id) so several
        primaries moved by one event come back in the order they were priced; the fold sums before
        it clamps, so order does not change the answer, but a log a human reads should not shuffle.
        """
        return [(r["target"], r["primary_"], float(r["delta"])) for r in self.con.execute(
            "SELECT target, primary_, delta FROM toward_deltas WHERE run_id = ? AND perceiver = ? "
            "ORDER BY turn, delta_id", (run_id, perceiver))]

    def wound_deltas_for(self, run_id, char_id):
        """Every wound movement this character made, in turn order — replay onto the sheet-authored
        wounds with `levers.replay_wound_deltas`.

        The twin of `arc_diffs_for` and `edge_deltas_for`. Ordered by (turn, delta_id) so two wounds
        moving in the same beat come back in the order they were written; the fold sums before it
        clamps, so the order does not change the answer, but a log a human reads should not shuffle.

        WITHOUT THIS THE STORE IS THE DEFECT IT WAS BUILT TO END. `bonds.py` records what happened
        the last time a log had a writer and no reader: a resumed cast reverted to sheet-authored
        relationships and every movement in the log was invisible.
        """
        return [(r["wound_id"], float(r["delta"]), r["kind"]) for r in self.con.execute(
            "SELECT wound_id, delta, kind FROM wound_deltas WHERE run_id = ? AND char_id = ? "
            "ORDER BY turn, delta_id", (run_id, char_id))]

    def arc_diffs_for(self, run_id, char_id):
        """Every durable baseline diff for char_id, in turn order — replay onto the seed baseline
        (arc.apply) to rehydrate the arc-evolved character on resume."""
        rows = self.con.execute(
            "SELECT diff FROM arc_diffs WHERE run_id = ? AND char_id = ? ORDER BY turn",
            (run_id, char_id)).fetchall()
        return [json.loads(r["diff"]) for r in rows]

    def edge_deltas_for(self, run_id, perceiver):
        """Every edge movement this character made, in turn order — replay onto their sheet-authored
        edges to rehydrate relationships on resume.

        The twin of `arc_diffs_for`, and it did not exist. `relationship_deltas` had only two
        consumers (`citation._r_edge`, `read_api.edges`) and NOTHING rebuilt an edge from them, so
        once `arc.assess` stopped writing edges the resume path restored none: a cast resumed as the
        people the sheet says they are, with every trust movement from prior scenes silently gone.
        Hard rule 2 is what makes replay right rather than snapshotting — the log is the source of
        truth and the edge is a derivable cache.

        Returns [(target, axis, delta, order)] so a caller can fold first- and second-order onto
        their own slots.
        """
        rows = self.con.execute(
            "SELECT target, axis, delta, ord FROM relationship_deltas "
            "WHERE run_id = ? AND perceiver = ? ORDER BY turn, delta_id",
            (run_id, perceiver)).fetchall()
        return [(r["target"], r["axis"], float(r["delta"]), r["ord"]) for r in rows]

    def append_scene(self, run_id, scene_no, label, pov, start_turn, end_turn,
                     voice="close-third", knowledge="pov", cfg=None):
        """Record a scene boundary — the committed turn range that forms one scene. Append-only; one
        row per (run, scene_no). The book's structure for the cutting room + book-scale narration.

        `voice` and `knowledge` are the per-scene narration choice (schema v13) and default to what
        every pre-v13 scene was. They are RECORDED here and READ by `narrate.narrate_book`, which is
        the point: a column no reader consults is the defect class this repo keeps re-finding.

        `cfg` is the director-authored scene configuration this scene ran against (schema v14). It
        is fingerprinted and stored so a resumed run can say what location, cast, props and opening
        tags produced the turns it replays — the pin a run already has for its bible, which exists
        because that input was once re-parsed per invocation and recorded nowhere. `cfg=None` pins
        nothing and the scene reads as unpinned, which is what every pre-v14 row is."""
        self.load_run(run_id)
        # A migrated DB has NO CHECK on `knowledge`: SQLite cannot add one by ALTER, so a fresh
        # database and a v12 one that grew into v13 disagree about what they accept. The guard
        # belongs where BOTH paths pass, which is here — otherwise a bad value lands quietly and
        # only explodes at render time, in the manuscript.
        # BOTH axes, guarded where the vocabulary lives. A migrated database has no CHECK on these
        # columns (SQLite cannot add one by ALTER), so this is the only guard on that path.
        from . import narration_modes
        narration_modes.validate(voice, knowledge, err=LedgerError)
        from . import scene_cfg                       # local, matching this file's bible import style

        def _write():
            fp = scene_cfg.record(self.con, cfg)         # "" when nothing was passed
            self.con.execute(
                "INSERT INTO scenes (run_id, scene_no, label, pov, cfg_fingerprint, voice, knowledge, "
                "start_turn, end_turn) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, int(scene_no), str(label or ""), pov, fp, str(voice), str(knowledge),
                 int(start_turn), int(end_turn)))

        # THE FOURTH WRITE-ONCE IDENTITY, and the one that had no Python half at all: re-appending
        # a scene_no raised a bare `sqlite3.IntegrityError` carrying no `.code` ATTRIBUTE, from the
        # module CLAUDE.md calls the spine. Three coded identities were called the complete set on
        # 2026-09-03 and the count was taken from the sites already converted, not from the table.
        _once.write_once(self.con,
            lambda: _once.refuse_duplicate(self.con,
                "SELECT 1 FROM scenes WHERE run_id=? AND scene_no=?", (run_id, int(scene_no)),
                "LEDGER_SCENE_EXISTS",
                "append_scene: run %r already holds scene %d; a scene boundary is written once"
                % (run_id, int(scene_no)), LedgerError),
            _write)

    def scenes_for(self, run_id):
        """Every scene boundary for the run, in scene order — the book's structure."""
        rows = self.con.execute(
            "SELECT scene_no, label, pov, cfg_fingerprint, voice, knowledge, start_turn, end_turn "
            "FROM scenes WHERE run_id = ? ORDER BY scene_no",
            (run_id,)).fetchall()
        return [{"scene_no": r["scene_no"], "label": r["label"], "pov": r["pov"],
                 "cfg_fingerprint": r["cfg_fingerprint"],
                 "voice": r["voice"], "knowledge": r["knowledge"],
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

    # ---- the snapshot CACHE. Bodies in `snapshots.py`, which carries the contract; these stay so
    # the thirteen existing call sites are unchanged, and so the log/cache seam is visible here.
    def persist_snapshot(self, run_id, as_of_turn, snap):
        return _snap.persist(self.con, run_id, as_of_turn, snap)

    def invalidate_snapshots_from(self, run_id, turn):
        """Drop cached snapshots at or after `turn`. The obligation of ANY writer appending below
        the head — see `snapshots.py` for the failure this exists to prevent."""
        return _snap.drop_from(self.con, run_id, turn)   # owns its transaction; see snapshots.py

    def load_snapshot(self, run_id):
        return _snap.load(self.con, run_id)

    def latest_turn(self, run_id):
        row = self.con.execute("SELECT MAX(turn) AS t FROM turns WHERE run_id = ?", (run_id,)).fetchone()
        return -1 if row["t"] is None else row["t"]

    def previous_affect(self, run_id, char_id, before_turn):
        """The affect this character committed BEFORE `before_turn`, or None.

        `latest_affect`'s sibling, and the one that makes SLOPE answerable. The ledger already held
        every turn's affect; nothing ever compared turn N to turn N-1, so `direction.py`'s only
        movement marker measured distance from the temperament MEAN — a different fact. A character
        who leapt 0.1 -> 0.9 in one beat got the same phrase as one who climbed there over ten.

        None on the first turn, which renders exactly as it always did.
        """
        row = self.con.execute(
            "SELECT affect FROM current_state WHERE run_id = ? AND char_id = ? AND turn < ? "
            "ORDER BY turn DESC LIMIT 1", (run_id, char_id, int(before_turn))).fetchone()
        return json.loads(row["affect"]) if row else None

    def latest_affect(self, run_id, char_id):
        row = self.con.execute(
            "SELECT affect, condition FROM current_state WHERE run_id = ? AND char_id = ? ORDER BY turn DESC LIMIT 1",
            (run_id, char_id)).fetchone()
        if row is None:
            return None
        return {"affect": json.loads(row["affect"]), "condition": json.loads(row["condition"])}

    # ---- resume: snapshot + tail replay, determinism ASSERTED (run-lifecycle.md) ----------------
    def divergence(self, run_id):
        """Delegates to `snapshots.divergence` — the cache's own module owns the cache question."""
        from . import snapshots
        return snapshots.divergence(self, run_id)

    # ---- the FOLD: delegated. `fold.py` owns the pure log->snapshot function; these keep the
    # names every caller and `world_events.would_change` already use.
    def _seed(self, run_id):
        return _fold.seed(self.con, run_id)

    @staticmethod                      # as it always was: callers reach it on the CLASS
    def _project(snap, ev):
        return _fold.project(snap, ev)

    def _events_between(self, run_id, lo, hi):
        return _fold.events_between(self.con, run_id, lo, hi)

    def fold(self, run_id, as_of=None):
        self.load_run(run_id)          # the run-exists check is the SPINE's, not the fold's
        return _fold.fold(self.con, run_id, as_of)

    def resume(self, run_id):
        """Load latest snapshot, replay the log tail, and assert the incremental fold equals the
        from-zero fold. Same log => same world, or this raises — a divergent resume is a bug to fix,
        not to paper over (no-fallbacks discipline)."""
        diverged, _detail, t, full = self.divergence(run_id)
        if diverged:
            raise LedgerError(
                "LEDGER_RESUME_DIVERGENCE",
                "RESUME DIVERGENCE on run %r at turn %d: snapshot+tail replay != from-zero fold. "
                "The cached snapshot or the projection is corrupt — refusing to resume. The cache "
                "is derivable and safe to discard: DELETE FROM snapshots WHERE run_id = %r, then "
                "resume again (docs/guide-operating.md)." % (run_id, t, run_id))
        self.persist_snapshot(run_id, t, full)
        return {"turn": t, "snapshot": full}
