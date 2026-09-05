"""fold.py — the pure function from LOG to SNAPSHOT. The reading half of the spine.

`world-state-ledger.md`: *"the fold is the ONLY way the snapshot changes — a pure function of the
log."* That is a different job from writing the log, and this is that job on its own: seed the
agents from the cast, replay the events in effective order, project each onto the snapshot.

SPLIT FROM `ledger.py` ON 2026-09-03, and the line count was the trigger rather than the reason.
`ledger.py` sat at 499 of hard rule 6's 500 and had blocked THREE correct changes in two days —
`snapshots.divergence` and `writeonce.refuse_duplicate` were carved off for the same pressure, and
two more fixes were blocked outright. Three times I shaved comments to fit before doing the
structural thing; this is the structural thing, done before the fourth.

NOTHING HERE WRITES. Every function takes a connection and reads through it, which is what makes
the dependency one way: `ledger` imports `fold` (its `resume` compares two folds) and `fold`
imports nothing back.

TWO TESTS DERIVE FROM `_project`'s SOURCE BY FILE PATH — `tests/test_world_events.py` reads its
branch table out of this function to prove every declared world type is actually folded, and
`tests/test_capability_claims.py` reads it too. They were repointed at this file in the same gate
that moved it: a derivation left reading the old path does not go red, it goes GREEN against a
stale copy, which is the failure mode this repo has paid for seven times.
"""
import json

from .snapshots import KINDS as SNAPSHOT_KINDS


# ---- the fold: snapshot = pure function of the log (world-state-ledger.md) ------------------
def seed(con, run_id):
    snap = {kind: {} for kind in SNAPSHOT_KINDS}
    snap["clock"] = {"now": -1}
    for row in con.execute("SELECT char_id FROM characters WHERE run_id = ? ORDER BY char_id", (run_id,)):
        snap["agents"][row["char_id"]] = {"location": None, "life_status": "alive", "possessions": []}
    return snap

def project(snap, ev):
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
        # THE REVEALER KNOWS IT. You cannot tell someone a thing you do not know, so the actor
        # joins the knowers whether or not the report listed them. Semantics, not a prompt
        # instruction: leaving it to the keeper meant a `to` list that omitted the speaker made
        # the speaker a non-knower of their own fact — and `faithfulness.check_fact_leaks` would
        # then flag them for stating it, regenerating a turn that was never wrong.
        if ev["actor"]:
            knowers.add(ev["actor"])
        snap["information"][payload["fact"]] = sorted(knowers)
    elif etype in ("seize", "destroy-asset") and "asset" in payload:
        snap["holdings"][payload["asset"]] = (
            {"destroyed": True} if etype == "destroy-asset" else {"controller": ev["actor"]})
    elif etype in ("betray", "bond") and ev["actor"] and ev["target"]:
        key = "%s|%s" % (ev["actor"], ev["target"])
        snap["relationships"][key] = {"standing": "enmity" if etype == "betray" else "alliance",
                                      "since": ev["effective_at"]}
    elif etype == "threaten":                 # names no tension: priced against every live one
        from . import tensions as _t          # bodies in the world-appraisal chassis;
        _t.fold_act(snap["tensions"], payload.get("dimensions") or {}, ev["effective_at"],
                    actor=ev["actor"], target=ev["target"], location=ev["location"])
    elif etype == "tension":                  # ...the DISPATCH stays here, derived-from by tests
        from . import tensions as _t
        (_t.fold_seed if _t.is_seed(payload) else _t.fold_delta)(
            snap["tensions"], payload, ev["effective_at"])
    return snap

def events_between(con, run_id, after_turn, up_to_turn):
    return con.execute(
        "SELECT * FROM events WHERE run_id = ? AND effective_at > ? AND effective_at <= ? "
        "ORDER BY effective_at, event_id", (run_id, after_turn, up_to_turn)).fetchall()

def fold(con, run_id, as_of_turn):
    """From-zero fold: seed + every event whose effective_at has arrived, in log order.

    THE RUN-EXISTS CHECK STAYS WITH THE CALLER. This began `self.load_run(run_id)` — a SPINE call
    from inside the fold — and `Ledger.fold` performs it before delegating, which keeps an unknown
    run reporting LEDGER_RUN_UNKNOWN and keeps this module importing nothing back."""
    snap = seed(con, run_id)
    for ev in events_between(con, run_id, -1, as_of_turn):
        project(snap, ev)
    snap["clock"] = {"now": as_of_turn}
    return snap
