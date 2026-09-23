#!/usr/bin/env python3
"""test_fold.py — the correction skip rule (consolidation-loop.md open-q 3, built 2026-09-19).

`fold.py` had no suite of its own: the from-zero fold was exercised through `test_ledger.py`'s
spine checks and `test_world_events.py`'s branch derivation, and neither can pin the rule this
gate adds, because the rule is about what the fold does NOT project.

THE CLAIM UNDER TEST, stated as `fold.superseded_ids` states it: skipping a superseded event on
replay IS the inverse delta, for every projection `project` has today. That is a claim about ALL
of them, so it is checked over `world_events.TYPES` rather than over the one type a hand-picked
example happens to use — a run that folds an act and then supersedes it must land on the same
world as a run where the act never happened, whichever type it was.

And the two boundaries the protocol depends on: a correction does not apply before its own
`effective_at`, and a run carrying no correction folds exactly as it did before this rule existed.

Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import fold as _fold                                 # noqa: E402
from src.engine import world_events                                  # noqa: E402
from src.engine.ledger import Ledger                                 # noqa: E402
from src.engine.records import Event                                 # noqa: E402
from src.engine.world_events import TYPES                            # noqa: E402

CONFIG = {"catalog_version": 1, "models": {}, "prompt_versions": {}}
FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _run(led, run_id, cast=("maren", "torin")):
    led.create_run(run_id, CONFIG)
    for c in cast:
        led.register_character(run_id, c, {"name": c.title()}, {})
    return run_id


def _ids(led, run_id, etype):
    return [r["event_id"] for r in led.con.execute(
        "SELECT event_id FROM events WHERE run_id=? AND type=? ORDER BY event_id", (run_id, etype))]


def _last_id(led, run_id):
    """The id of the row just appended. Asked BY POSITION rather than by type on purpose: the
    every-type case below seeds a `tension` precondition and then tests a `tension` act, and a
    by-type lookup superseded both — which passed as a world that never happened for the wrong
    reason (the precondition vanished too) and was caught only because the CONTROL still had it."""
    return led.con.execute("SELECT MAX(event_id) AS m FROM events WHERE run_id=?",
                           (run_id,)).fetchone()["m"]


def _correction(led, run_id, turn, supersedes, issue="the ledger says otherwise"):
    world_events.append(led, run_id, turn, [Event(
        type="correction", actor="maren", visibility="private-to-actor",
        payload={"supersedes": list(supersedes), "turn": turn - 1, "issue": issue,
                 "source": "critic"})])


# ---------------------------------------------------------------------------------------------
# 1. THE HEADLINE CASE — a move, superseded, folds back to where the character was.
# ---------------------------------------------------------------------------------------------
def test_a_superseded_move_folds_back_to_the_previous_location(tmp):
    led = Ledger(os.path.join(tmp, "move.db"))
    _run(led, "r1")
    world_events.append(led, "r1", 1, [Event(type="move", actor="maren", payload={"to": "cottage"})])
    world_events.append(led, "r1", 2, [Event(type="move", actor="maren", payload={"to": "ward"})])
    bad = _ids(led, "r1", "move")[1]
    check("the-bad-move-folds-while-it-stands",
          led.fold("r1", 2)["agents"]["maren"]["location"] == "ward")

    _correction(led, "r1", 3, [bad], "she never left the cottage")
    snap = led.fold("r1", 3)
    check("superseded-move-folds-back-to-the-PRE-MOVE-value",
          snap["agents"]["maren"]["location"] == "cottage",
          str(snap["agents"]["maren"]))
    # ...and the log still HAS the bad move. Append-only repentance keeps both (hard rule 2).
    check("the-bad-event-is-still-in-the-log", len(_ids(led, "r1", "move")) == 2)
    check("the-correction-is-a-row-of-its-own", len(_ids(led, "r1", "correction")) == 1)


def test_a_superseded_FIRST_move_folds_back_to_None(tmp):
    """The seed value, not the previous event — there is no previous event. `seed` gives every
    registered character `location: None`, and a from-zero fold that skips the only move must
    land exactly there rather than on an empty dict or a KeyError."""
    led = Ledger(os.path.join(tmp, "first.db"))
    _run(led, "r2")
    world_events.append(led, "r2", 1, [Event(type="move", actor="maren", payload={"to": "ward"})])
    _correction(led, "r2", 2, _ids(led, "r2", "move"))
    snap = led.fold("r2", 2)
    check("superseded-first-move-folds-back-to-None",
          snap["agents"]["maren"]["location"] is None, str(snap["agents"]["maren"]))
    check("...and-the-agent-row-is-otherwise-the-seed",
          snap["agents"]["maren"] == {"location": None, "life_status": "alive", "possessions": []},
          str(snap["agents"]["maren"]))


# ---------------------------------------------------------------------------------------------
# 2. THE EFFECTIVE_AT BOUNDARY — a correction is an event, so it arrives like one.
# ---------------------------------------------------------------------------------------------
def test_a_correction_does_not_apply_before_its_own_effective_at(tmp):
    """`correct_run` appends at the run's NEXT tick, so this is the ordinary case rather than an
    exotic one: the fold of any turn already recorded must be unchanged by a correction written
    afterwards. The record is never rewritten behind a reader who folded yesterday."""
    led = Ledger(os.path.join(tmp, "later.db"))
    _run(led, "r3")
    world_events.append(led, "r3", 1, [Event(type="move", actor="maren", payload={"to": "ward"})])
    _correction(led, "r3", 5, _ids(led, "r3", "move"))
    check("not-yet-arrived-at-turn-4", led.fold("r3", 4)["agents"]["maren"]["location"] == "ward")
    check("arrived-at-turn-5", led.fold("r3", 5)["agents"]["maren"]["location"] is None)
    check("still-applied-above-its-tick", led.fold("r3", 9)["agents"]["maren"]["location"] is None)
    # The skip SET is the mechanism, so it is asserted directly too — an equal snapshot could
    # hide a skip that happened to make no difference.
    check("the-skip-set-is-empty-below-the-tick",
          _fold.superseded_ids(_fold.events_between(led.con, "r3", -1, 4)) == set())
    check("...and-carries-the-id-at-it",
          _fold.superseded_ids(_fold.events_between(led.con, "r3", -1, 5)) == set(_ids(led, "r3", "move")))


# ---------------------------------------------------------------------------------------------
# 3. THE CONTROL — a run with no correction folds exactly as it did before the rule existed.
# ---------------------------------------------------------------------------------------------
# HOW THE EXPECTED VALUE WAS ESTABLISHED, said plainly because "byte-identical to today" is a
# claim about a version of the code that no longer exists: this is a STORED FIXTURE, and it was
# not produced by the code it now checks. `git show HEAD:src/engine/fold.py` (01c3b5a, before the
# skip rule) was loaded as a module against the very database
# `test_an_uncorrected_run_folds_to_the_stored_fixture` builds, its `fold` called, and the result
# pasted here verbatim; the new `fold` was then run on the same connection and compared. So the
# new path has to reproduce the old answer exactly rather than merely agree with itself. The
# empty-skip-set assertion beside it is the mechanism: equality alone would also pass if the fold
# had skipped something that happened not to matter.
_UNCORRECTED = {
    "agents": {"maren": {"location": "ward", "life_status": "alive", "possessions": []},
               "torin": {"location": None, "life_status": "dead", "possessions": []}},
    "information": {"the-debt": ["maren", "torin"]},
    "holdings": {"the-mill": {"controller": "maren"}},
    "relationships": {},
    "tensions": {},
    "clock": {"now": 4},
}


def test_an_uncorrected_run_folds_to_the_stored_fixture(tmp):
    led = Ledger(os.path.join(tmp, "clean.db"))
    _run(led, "r4")
    world_events.append(led, "r4", 1, [Event(type="move", actor="maren", payload={"to": "ward"})])
    world_events.append(led, "r4", 2, [Event(type="reveal", actor="maren",
                                             payload={"fact": "the-debt", "to": ["torin"]})])
    world_events.append(led, "r4", 3, [Event(type="seize", actor="maren", payload={"asset": "the-mill"})])
    world_events.append(led, "r4", 4, [Event(type="harm", actor="maren", target="torin",
                                             payload={"terminal": True})])
    snap = led.fold("r4", 4)
    check("no-correction-means-an-EMPTY-skip-set",
          _fold.superseded_ids(_fold.events_between(led.con, "r4", -1, 4)) == set())
    check("an-uncorrected-fold-equals-the-pre-change-fixture", snap == _UNCORRECTED,
          json.dumps(snap, sort_keys=True))


# ---------------------------------------------------------------------------------------------
# 4. THE CLAIM ITSELF, over every type the fold has — skip-on-replay IS the inverse.
# ---------------------------------------------------------------------------------------------
_SAMPLE = {                              # payload, actor, target — built from each type's own keys
    "move":          ({"to": "the-north-road"}, "maren", None),
    "harm":          ({"terminal": True}, "maren", "torin"),
    "reveal":        ({"fact": "the-debt", "to": ["torin"]}, "maren", None),
    "seize":         ({"asset": "the-mill"}, "maren", None),
    "destroy-asset": ({"asset": "the-mill"}, "maren", None),
    "betray":        ({}, "maren", "torin"),
    "bond":          ({}, "maren", "torin"),
    "tension":       ({"id": "the-border", "temperature": 0.7, "factions": ["x"],
                       "watches": {"parties": ["maren"]}, "interests": {"threat": 0.5}}, "maren", None),
    "threaten":      ({"dimensions": {"threat": 0.78}}, "maren", "torin"),
}
# `threaten` prices itself against the LIVE tensions and folds to nothing on an empty register, so
# its precondition is seeded into both arms as an ordinary event — the same shape
# `tests/test_world_events.py` uses, expressed here as log rows because this is a real fold.
_SEED = Event(type="tension", payload={"id": "the-border", "temperature": 0.1, "factions": [],
                                       "cooling": "typical",
                                       "watches": {"parties": ["maren", "torin"]},
                                       "interests": {"threat": 0.5}})


def test_skipping_a_superseded_event_equals_it_never_happening_FOR_EVERY_TYPE(tmp):
    """DERIVED over `world_events.TYPES`, so a type added later is covered without anyone
    remembering to come back here — and the sample set is asserted against TYPES so a new type
    fails loudly instead of being silently untested."""
    check("the-sample-set-has-not-drifted-from-TYPES", set(_SAMPLE) == set(TYPES),
          str(sorted(set(_SAMPLE) ^ set(TYPES))))
    led = Ledger(os.path.join(tmp, "every.db"))
    for etype in sorted(TYPES):
        payload, actor, target = _SAMPLE[etype]
        with_act, without = _run(led, "w-%s" % etype), _run(led, "n-%s" % etype)
        for rid in (with_act, without):
            world_events.append(led, rid, 0, [_SEED])
        world_events.append(led, with_act, 1, [Event(type=etype, actor=actor, target=target,
                                                     payload=payload)])
        _correction(led, with_act, 2, [_last_id(led, with_act)])
        corrected, never = led.fold(with_act, 3), led.fold(without, 3)
        check("%s-superseded-folds-as-if-it-never-happened" % etype, corrected == never,
              "%s\n        vs %s" % (json.dumps(corrected, sort_keys=True),
                                     json.dumps(never, sort_keys=True)))


# ---------------------------------------------------------------------------------------------
# 5. THE ROW ITSELF IS NOT PROJECTED — the no-op branch, asserted rather than assumed.
# ---------------------------------------------------------------------------------------------
def test_the_correction_row_projects_to_nothing_on_its_own(tmp):
    """A correction naming NO ids must leave the world exactly as it was. That is the audit-trail
    case (`correct_run` writes an empty `supersedes` for a flag on a turn that moved nothing), and
    it is also the direct test of `project`'s system-type branch: a fall-through would be silent."""
    led = Ledger(os.path.join(tmp, "noop.db"))
    _run(led, "r5")
    world_events.append(led, "r5", 1, [Event(type="move", actor="maren", payload={"to": "ward"})])
    before = led.fold("r5", 1)
    _correction(led, "r5", 2, [], "a voice flag with no event behind it")
    after = led.fold("r5", 2)
    check("an-empty-correction-moves-no-field",
          {k: v for k, v in after.items() if k != "clock"} ==
          {k: v for k, v in before.items() if k != "clock"}, json.dumps(after, sort_keys=True))
    check("...but-it-IS-on-the-record", len(led.corrections_for("r5")) == 1)


# ---------------------------------------------------------------------------------------------
# 6. THE CACHE — a correction reaches BACKWARD, and the writer must invalidate that far back.
# ---------------------------------------------------------------------------------------------
def _beats(led, run_id, turns):
    from src.engine.records import PATHS, TurnCommit
    for n in turns:
        led.append_turn(TurnCommit(run_id=run_id, turn=n, actor="maren", thought="", action="a%d" % n,
                                   tags={"type": "mundane"}, affect={p: 0.5 for p in PATHS},
                                   condition={}, events=[], validation={}))


def test_correcting_a_parked_run_does_not_brick_its_resume(tmp):
    """MEASURED, NOT ANTICIPATED. The first working version of this gate passed every check above
    and bricked a real sequence: park at turn N (which persists a snapshot), `critic --correct`,
    run one more turn, resume -> LEDGER_RESUME_DIVERGENCE. `snapshots.divergence` replays the tail
    onto a cached snapshot that had already folded the bad event, and a tail replay cannot un-apply
    it, while the from-zero fold beside it now skips it. The divergence check was right; the writer
    was wrong. `world_events._reaches_back_to` drops the cache back to the SUPERSEDED event's tick.

    THIS CASE IS THE NARROW ONE, and it is named so it stops claiming otherwise. The only cached
    snapshot here sits AT the bad move's own tick, so the drop removes every snapshot there is and
    `divergence` takes its `cached is None` branch — where the incremental fold IS the from-zero
    fold and the comparison is trivially equal. It proves the DROP, and nothing about the replay.
    The case below is the one that exercises the replay."""
    led = Ledger(os.path.join(tmp, "parked.db"))
    _run(led, "r6", cast=("maren",))
    _beats(led, "r6", (0, 1, 2))
    world_events.append(led, "r6", 2, [Event(type="move", actor="maren", payload={"to": "ward"})])
    led.persist_snapshot("r6", 2, led.fold("r6", 2))                 # park, AT the move's own tick
    check("the-parked-cache-holds-the-move",
          led.load_snapshot("r6")[1]["agents"]["maren"]["location"] == "ward")

    _correction(led, "r6", 3, _ids(led, "r6", "move"), "she never left the cottage")
    check("appending-the-correction-dropped-the-STALE-cache", led.load_snapshot("r6") is None,
          str(led.load_snapshot("r6")))
    _beats(led, "r6", (3,))                                          # the run carries on
    diverged, detail, _t, _full = led.divergence("r6")
    check("resume-holds-when-no-cache-survives", not diverged, detail)
    check("...and-lands-on-the-corrected-world-when-no-cache-survives",
          led.resume("r6")["snapshot"]["agents"]["maren"]["location"] is None,
          str(led.resume("r6")["snapshot"]["agents"]))
    # THE CONTROL: an ordinary world event must still invalidate only from its OWN tick, or this
    # repair would have quietly turned every append into a full cache flush.
    led.persist_snapshot("r6", 3, led.fold("r6", 3))
    world_events.append(led, "r6", 9, [Event(type="move", actor="maren", payload={"to": "road"})])
    check("an-ordinary-event-leaves-an-earlier-cache-alone",
          led.load_snapshot("r6") is not None and led.load_snapshot("r6")[0] == 3,
          str(led.load_snapshot("r6")))


def _a_run_with_a_cache_below_the_bad_move(tmp, name, run_id, correct):
    """Cache at turn 1, the bad move at 2, a park at 3, optionally a correction at 4, one more beat.

    THE SHAPE THAT MATTERS: `_reaches_back_to` drops from the MOVE's tick (2), so the turn-3 park
    goes and the turn-1 cache SURVIVES — and that survivor carries the bad move forward through the
    tail replay. Built twice, with and without the correction, so the control differs in exactly
    one row."""
    led = Ledger(os.path.join(tmp, name))
    _run(led, run_id, cast=("maren",))
    _beats(led, run_id, (0, 1, 2, 3))
    led.persist_snapshot(run_id, 1, led.fold(run_id, 1))             # the cache that survives
    world_events.append(led, run_id, 2, [Event(type="move", actor="maren", payload={"to": "ward"})])
    led.persist_snapshot(run_id, 3, led.fold(run_id, 3))             # the park that does not
    if correct:
        _correction(led, run_id, 4, _ids(led, run_id, "move"), "she never left the cottage")
    _beats(led, run_id, (4,))
    return led


def test_the_TAIL_REPLAY_applies_the_skip_rule_too(tmp):
    """THE GENERAL CASE the narrow one above cannot reach. A snapshot cached BELOW the superseded
    event survives the drop, so `snapshots.divergence` really does replay a tail that contains the
    bad move — and it must skip it, because the from-zero fold it is compared against does. Without
    this the incremental said "ward" and the fold said None on every resume.

    Skipping is EXACT here rather than a guess: `_reaches_back_to` guarantees a surviving cache
    sits below every superseded id, so every one of them is in the tail, and so is the correction
    naming them. `superseded_ids(tail)` is therefore the same set `fold` computes over the log."""
    led = _a_run_with_a_cache_below_the_bad_move(tmp, "below.db", "r7", correct=True)
    check("a-cache-BELOW-the-bad-move-survives-the-drop",
          led.load_snapshot("r7") is not None and led.load_snapshot("r7")[0] == 1,
          str(led.load_snapshot("r7")))
    check("...and-it-still-holds-the-pre-move-world",
          led.load_snapshot("r7")[1]["agents"]["maren"]["location"] is None,
          str(led.load_snapshot("r7")[1]["agents"]))
    tail = _fold.events_between(led.con, "r7", 1, led.latest_turn("r7"))
    check("the-superseded-move-IS-in-the-tail",
          _fold.superseded_ids(tail) == set(_ids(led, "r7", "move")),
          "%s vs %s" % (_fold.superseded_ids(tail), _ids(led, "r7", "move")))
    diverged, detail, _t, _full = led.divergence("r7")
    check("tail-replay-equals-the-from-zero-fold", not diverged, detail)
    check("...and-resume-lands-on-the-corrected-world",
          led.resume("r7")["snapshot"]["agents"]["maren"]["location"] is None,
          str(led.resume("r7")["snapshot"]["agents"]))


def test_the_SAME_shape_with_no_correction_is_unchanged(tmp):
    """THE INVERSE CONTROL. Identical sequence minus the correction row: the surviving turn-1 cache
    replays the move and lands on "ward", the skip set over the tail is EMPTY, and divergence is
    still False. Without this, a `divergence` that skipped too much — or that had quietly stopped
    replaying the tail at all — would pass the test above and fail nothing."""
    led = _a_run_with_a_cache_below_the_bad_move(tmp, "below-clean.db", "r8", correct=False)
    cached = led.load_snapshot("r8")
    check("with-no-correction-the-PARK-is-the-surviving-cache", cached is not None and cached[0] == 3,
          str(cached))
    tail = _fold.events_between(led.con, "r8", 1, led.latest_turn("r8"))
    check("the-skip-set-over-the-tail-is-empty", _fold.superseded_ids(tail) == set(),
          str(_fold.superseded_ids(tail)))
    diverged, detail, _t, _full = led.divergence("r8")
    check("an-uncorrected-run-still-resumes-clean", not diverged, detail)
    check("...and-the-move-still-stands", led.resume("r8")["snapshot"]["agents"]["maren"]["location"] == "ward",
          str(led.resume("r8")["snapshot"]["agents"]))
    # ...and the same sequence forced onto the turn-1 cache (drop the park) replays the move itself
    led.invalidate_snapshots_from("r8", 2)
    check("the-turn-1-cache-replays-the-move-through-the-tail",
          led.load_snapshot("r8")[0] == 1 and not led.divergence("r8")[0],
          "%s / %s" % (led.load_snapshot("r8")[0], led.divergence("r8")[1]))


def main():
    print("test_fold.py — the correction skip rule\n")
    tmp = tempfile.mkdtemp(prefix="swe_fold_test_")
    try:
        for name, fn in sorted((k, v) for k, v in globals().items() if k.startswith("test_")):
            print("  --- %s" % name)
            fn(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("ALL PASS" if not FAILS else "FAILED:\n  " + "\n  ".join(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
