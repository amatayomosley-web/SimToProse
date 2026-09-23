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

from .consolidation import SYSTEM_TYPES        # the two rows the engine writes ABOUT ITSELF
from .snapshots import KINDS as SNAPSHOT_KINDS

# The append-only compensating row (consolidation-loop.md open-q 3, measurement.md s3). Named once
# here because three functions in this file read it and `ledger.py` delegates two more to them.
CORRECTION = "correction"


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
    elif etype in SYSTEM_TYPES:
        # THE ENGINE'S OWN BOOKKEEPING ROWS MOVE NO FIELD, and they say so here rather than falling
        # off the end of the chain. `turn-skipped` and `correction` are `consolidation.SYSTEM_TYPES`
        # — the two rows written ABOUT the record instead of about the world. A correction's entire
        # effect is the SKIP in `fold` below (the ids in its `supersedes` list); projecting the
        # correction itself must do nothing. An IMPLICIT nothing is indistinguishable from a branch
        # someone forgot to write, which is exactly how `threaten` folded to silence for three
        # months while the catalog claimed a world effect (see this file's header).
        #
        # Derived from the catalog rather than spelled out, so it cannot drift from the two system
        # rows — and so `tests/test_world_events._folded_types()`, which scrapes the literal type
        # spellings out of this source to answer "which WORLD types does the fold handle" (it reads
        # comments too — the first draft of THIS comment quoted a specimen branch and the guard
        # duly reported a folded type called `x`), does not count these. That
        # is correct rather than convenient: a system row is not a world type, has no entry in
        # `world_events.TYPES`, and must not be reported as a folded one.
        pass
    return snap

def events_between(con, run_id, after_turn, up_to_turn):
    return con.execute(
        "SELECT * FROM events WHERE run_id = ? AND effective_at > ? AND effective_at <= ? "
        "ORDER BY effective_at, event_id", (run_id, after_turn, up_to_turn)).fetchall()

def corrections(con, run_id, as_of=None):
    """This run's `correction` rows, in log order. `as_of=None` means EVERY one, arrived or not.

    The reader half of the correction protocol, beside the rule that consumes it. `as_of` gates on
    `effective_at` exactly as `events_between` does, so "what has the record repented of BY turn N"
    and "what does it carry at all" are two different questions with two different answers."""
    sql = "SELECT * FROM events WHERE run_id = ? AND type = ?"
    args = [run_id, CORRECTION]
    if as_of is not None:
        sql += " AND effective_at <= ?"
        args.append(int(as_of))
    return con.execute(sql + " ORDER BY effective_at, event_id", args).fetchall()

def superseded_ids(events):
    """The event ids named by every `correction` IN THIS LIST -> set of ints.

    SKIPPING A SUPERSEDED EVENT ON REPLAY *IS* THE INVERSE DELTA, for every projection `project`
    has today. Each branch above SETS a field (location, life_status, knowers, holdings, standing)
    or hands a delta to the tension chassis, which folds in order; none reads its own prior value.
    So in a from-zero fold there is nothing to un-apply — the superseded event simply never
    applies, which is exact for the set-style branches and is the only coherent reading for the
    additive one (an act that did not happen adds no heat). `tests/test_fold.py` pins that claim.
    A future projection that reads its own prior value falsifies it and must handle `correction`
    itself; `docs/measurement.md` open item 3 (cascaded errors) is the same boundary, still open.

    TAKES THE EVENT LIST, not a connection, and that is the "does not apply yet" rule rather than
    an accident of signature: a correction is itself an event with an `effective_at`, so a fold
    `as_of` a turn BEFORE it simply does not have it in hand and skips nothing.
    """
    dead = set()
    for ev in events:
        if ev["type"] == CORRECTION:
            dead.update(int(i) for i in (json.loads(ev["payload"]).get("supersedes") or []))
    return dead

def fold(con, run_id, as_of_turn):
    """From-zero fold: seed + every event whose effective_at has arrived, in log order, MINUS the
    ones an arrived `correction` supersedes (consolidation-loop.md open-q 3).

    THE RUN-EXISTS CHECK STAYS WITH THE CALLER. This began `self.load_run(run_id)` — a SPINE call
    from inside the fold — and `Ledger.fold` performs it before delegating, which keeps an unknown
    run reporting LEDGER_RUN_UNKNOWN and keeps this module importing nothing back.

    THE SKIP SET IS COLLECTED OVER THE WHOLE ARRIVED LOG BEFORE ANYTHING PROJECTS. A correction
    lands at a LATER tick than the event it names, so a single pass that asked "is this one dead?"
    as it went would already have folded the bad event by the time it read the row that kills it."""
    snap = seed(con, run_id)
    arrived = events_between(con, run_id, -1, as_of_turn)
    dead = superseded_ids(arrived)
    for ev in arrived:
        if ev["event_id"] in dead:
            continue
        project(snap, ev)
    snap["clock"] = {"now": as_of_turn}
    return snap
