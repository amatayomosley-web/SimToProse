#!/usr/bin/env python3
"""test_keeper.py — the emitting seat: does the WORLD actually move, and does it refuse to?

WHAT WAS WRONG. The eight world-moving types appeared only inside `ledger._project` — the fold had
branches no real run could reach, because nothing emitted them. `agents[x].location`, `holdings`,
`information` and `tensions` were seeded and frozen for a whole book; a character could die and
`life_status` stayed "alive". `tests/test_world_events.py` proved each field MOVES when fed a
well-formed event; nothing proved anything ever fed one.

THE TWO HALVES, and only one is testable without a model. `world_events.py` states the rule the
engine enforces — AN EVENT IS A WORLD EVENT IFF FOLDING IT WOULD CHANGE THE SNAPSHOT — and that is
arithmetic, so it is tested here in full. The NOTICING is a prompt, tested for shape the way
`test_narrate` tests `build_narration_prompt`, because hard rule 3 keeps the model out of the
engine and no book has run to calibrate a detector against.

THE TEST THAT MATTERS MOST is the refusal: a well-formed, plausible proposal that leaves the world
identical must be REJECTED, and must leave no row behind in an append-only log. Without that, a
keeper narrates the snapshot into motion and the log stops meaning anything.

Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import keeper                                                # noqa: E402

from src.engine import world_events                          # noqa: E402
from src.engine.ledger import Ledger                         # noqa: E402
from src.engine.records import TurnCommit, PRIMARIES         # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _led(tmp, name, seed=None):
    led = Ledger(os.path.join(tmp, name + ".db"))
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    for cid in ("maren", "edda"):
        led.register_character("r1", cid, {"name": cid.title()},
                               {"temperament": "authored", "world_seed": seed or {}})
    for t in range(2):
        led.append_turn(TurnCommit(run_id="r1", turn=t, actor="maren", thought="t%d" % t,
                                   action="she walked out to the ridge", tags={"type": "mundane"},
                                   affect={p: 0.5 for p in PRIMARIES}, events=[]))
    return led


def test_a_move_ACTUALLY_moves_the_snapshot(tmp):
    """The whole point. Before this seat existed, no run could produce this transition."""
    led = _led(tmp, "move")
    before = led.fold("r1", 1)
    applied, rejected = keeper.apply_proposals(
        led, "r1", [{"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the ridge"}}])
    after = led.fold("r1", 1)
    check("the-move-was-applied", len(applied) == 1 and not rejected, str(rejected))
    check("the-SNAPSHOT-changed", before.get("agents") != after.get("agents"),
          "before=%r after=%r" % (before.get("agents"), after.get("agents")))
    check("and-it-says-where-she-is",
          "ridge" in json.dumps(after.get("agents") or {}), str(after.get("agents")))


def test_a_proposal_that_moves_NOTHING_is_refused_and_leaves_no_row(tmp):
    """THE REFUSAL, which is the gate that keeps a keeper honest. Applying the same move twice is
    well-formed and plausible and must be refused the second time: the world already says it. And
    the refused attempt must leave NO row, or an append-only log accumulates events that were
    judged not to have happened."""
    led = _led(tmp, "norepeat")
    prop = {"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the ridge"}}
    keeper.apply_proposals(led, "r1", [prop])
    n_after_first = led.con.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]

    applied, rejected = keeper.apply_proposals(led, "r1", [dict(prop)])
    check("the-repeat-was-REFUSED", not applied and len(rejected) == 1, str(applied))
    check("and-the-reason-names-the-rule",
          "would not change the snapshot" in rejected[0][1], rejected[0][1])
    n_after_second = led.con.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
    check("a-refused-proposal-left-NO-row", n_after_first == n_after_second,
          "%d -> %d" % (n_after_first, n_after_second))


def test_a_report_about_a_turn_the_run_never_had_is_invention(tmp):
    """The cheapest gate, and the one that stops the seat hallucinating a source. Every report
    names the turn it came from; a turn nobody recorded cannot have said anything."""
    led = _led(tmp, "notaturn")
    applied, rejected = keeper.apply_proposals(
        led, "r1", [{"turn": 99, "type": "move", "actor": "maren", "payload": {"to": "the ridge"}}])
    check("an-unrecorded-turn-is-refused", not applied and rejected, str(applied))
    check("and-the-reason-says-invention", "invention" in rejected[0][1], rejected[0][1])


def test_a_malformed_payload_is_refused_BEFORE_the_write(tmp):
    """`world_events.validate_payload` reads the keys `_project` actually reads, so a payload the
    fold cannot use is refused rather than folded into a silent no-op."""
    led = _led(tmp, "malformed")
    bad = [
        {"turn": 1, "type": "move", "actor": "maren", "payload": {}},              # no `to`
        {"turn": 1, "type": "not-a-type", "payload": {"to": "x"}},                 # unknown type
        {"turn": 1, "type": "reveal", "payload": {"fact": "the fever"}},           # no `to`
    ]
    applied, rejected = keeper.apply_proposals(led, "r1", bad)
    check("every-malformed-report-refused", not applied and len(rejected) == 3, str(applied))
    n = led.con.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
    check("nothing-malformed-reached-the-log", n == 0, "%d rows landed" % n)


def test_dry_run_writes_nothing(tmp):
    """An operator must be able to see what a keeper WOULD do to an append-only log before it does
    it, because there is no undo."""
    led = _led(tmp, "dry")
    applied, _ = keeper.apply_proposals(
        led, "r1", [{"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the ridge"}}],
        dry_run=True)
    n = led.con.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
    check("dry-run-reports-it-would-apply", len(applied) == 1, str(applied))
    check("dry-run-wrote-NOTHING", n == 0, "%d rows landed" % n)


def test_would_move_ignores_the_clock(tmp):
    """The one way the warrant test can pass for the wrong reason. `fold` stamps `clock.now` on
    every snapshot, so comparing whole dicts would call EVERY candidate a world event and the gate
    would be vacuous. Excluded by name, and asserted here so it stays excluded."""
    a = {"agents": {"maren": {"location": "home"}}, "clock": {"now": 3}}
    b = {"agents": {"maren": {"location": "home"}}, "clock": {"now": 9}}
    check("a-clock-tick-alone-is-NOT-a-world-event", not world_events.would_move(a, b))
    c = {"agents": {"maren": {"location": "the ridge"}}, "clock": {"now": 3}}
    check("but-a-real-field-change-IS", world_events.would_move(a, c))


def test_the_prompt_carries_the_rubric_and_forbids_invention(tmp):
    """The noticing half, tested for shape. The rubric is GENERATED from the same table `_project`
    folds, so the prompt cannot drift from what the engine will accept — the alternative is a
    hand-written copy, which is the duplicate class CLAUDE.md tabulates."""
    led = _led(tmp, "prompt")
    from critic import scene_turns
    turns = scene_turns(led, "r1")
    blob = json.dumps(keeper.build_keeper_prompt(turns, led.fold("r1", 1)))

    for t in ("move", "harm", "reveal", "seize", "destroy-asset", "betray", "bond"):
        check("prompt-carries-%s" % t, t in blob, "the rubric lost a type")
    check("prompt-carries-a-BOUNDARY-not-just-a-name", "crossing a room" in blob, blob[:200])
    check("prompt-forbids-invention", "do not invent" in blob.lower(), blob[:200])
    check("prompt-says-silence-is-correct", "Silence is a correct answer" in blob, blob[:200])
    check("prompt-carries-the-recorded-stream", "the ridge" in blob, blob[:200])


def test_the_keeper_also_records_what_was_SAID_about_the_world(tmp):
    """The second half of the seat, with a DIFFERENT rule. A world event must move the
    snapshot; an utterance binds nothing and is always warranted, because it is always true that
    the speaker said it. It enters SUPERPOSED and waits for a keeper to rule."""
    from src.engine import claims
    led = _led(tmp, "utterances")
    rec, rej = keeper.record_utterances(led, "r1", [
        {"turn": 1, "speaker": "maren", "said": "Clifford keeps the drowned-boat rite.",
         "extracts": [{"subject": "clifford", "predicate": "keeps rite", "object": "the drowned boat"}]},
        {"turn": 99, "speaker": "maren", "said": "anything"},
        {"turn": 1, "speaker": "maren", "said": "   "},
    ])
    check("the-utterance-was-recorded", len(rec) == 1, str(rec))
    check("an-unrecorded-turn-is-refused", any("invention" in w for _r, w in rej), str(rej))
    check("an-utterance-with-no-VERBATIM-text-is-refused",
          any("index into what was said" in w for _r, w in rej), str(rej))

    stored = claims.for_run(led.con, "r1")
    check("it-binds-NOTHING-until-a-keeper-rules",
          claims.tier_of(stored[0]) == claims.SUPERPOSED, str(stored))
    check("and-the-prompt-asks-for-claims-too",
          "SAID ABOUT THE WORLD" in json.dumps(
              keeper.build_keeper_prompt([{"turn": 0, "actor": "maren", "action": "x",
                                           "thought": "y"}], {})))

def test_EVERY_world_type_survives_the_gate(tmp):
    """All eight, not the two the first version of this suite covered.

    `move` and `reveal` were the only types routed through apply_proposals, and that is how a
    KeyError shipped: `_project`'s betray/bond branch reads `ev["effective_at"]`, which the
    candidate row did not supply, so two of eight types CRASHED the seat instead of being judged —
    and gate 3 was the one gate outside the try/except, so it took the run down after earlier
    proposals in the same file had already committed."""
    from src.engine import consolidation
    led = _led(tmp, "alltypes")
    cases = [
        ("move",          {"to": "the ridge"},                          "maren", None),
        ("harm",          {"terminal": True},                           "maren", "edda"),
        ("reveal",        {"fact": "the well is poisoned", "to": ["edda"]}, "maren", None),
        ("seize",         {"asset": "the mill"},                        "maren", None),
        ("destroy-asset", {"asset": "the barn"},                        "maren", None),
        ("betray",        {},                                           "maren", "edda"),
        ("bond",          {},                                           "maren", "edda"),
        ("tension",       {"name": "the water right", "temperature": 0.4}, "maren", None),
    ]
    props = [{"turn": 1, "type": t, "payload": pl, "actor": a, "target": tg}
             for t, pl, a, tg in cases]
    applied, rejected = keeper.apply_proposals(led, "r1", props)

    # None may CRASH. Each is either applied or refused with a reason — never an exception.
    seen = {p["type"] for p in applied} | {p["type"] for p, _w in rejected}
    check("all-eight-types-were-JUDGED", seen == {t for t, _p, _a, _g in cases},
          "missing: %s" % ({t for t, _p, _a, _g in cases} - seen))
    crashed = [w for _p, w in rejected if "could not judge" in w]
    check("none-crashed-the-fold", not crashed, str(crashed))

    # and the ones the world model actually moves must be APPLIED, or the seat is inert
    for t in ("move", "harm", "reveal", "seize", "betray", "bond"):
        check("%s-actually-moved-the-world" % t, t in {p["type"] for p in applied},
              str([w for p, w in rejected if p["type"] == t]))


def test_the_candidate_row_supplies_EVERY_field_the_fold_reads(tmp):
    """DERIVED, not hand-listed. `_candidate_row` mirrors what `_project` reads, and a
    hand-kept mirror of a source of truth is the defect class CLAUDE.md tabulates seven instances
    of — this one already went wrong once, on `effective_at`.

    So the field set is read out of `_project`'s OWN SOURCE. Add a read there and this fails,
    instead of two more types crashing in a book."""
    import inspect
    import re
    from src.engine.ledger import Ledger
    from src.engine.records import Event
    from src.engine.world_events import _candidate_row

    # THE BODY MOVED to `fold.py` on 2026-09-03; `Ledger._project` is now a delegating stub,
    # and `getsource` on it finds one line with no `ev[...]` in it. Read the body.
    from src.engine import fold as _fold
    src = inspect.getsource(_fold.project)
    # BOTH read forms. The first version matched subscripts only, and `_project`'s payload half
    # uses `.get` throughout — so an `ev.get("x")` added there would fail SOFT (returning None),
    # make the warrant judge a candidate the committed row does not match, and never trip this.
    # No such read exists today; the gap was latent, which is the kind that ships.
    reads = set(re.findall(r"""ev\[["']([\w_]+)["']\]""", src))
    reads |= set(re.findall(r"""ev\.get\(["']([\w_]+)""", src))
    check("the-fold-reads-something", bool(reads), "the regex found no ev[...] reads at all")
    row = set(_candidate_row(Event(type="move", payload={}), 0))
    check("the-candidate-supplies-all-of-them", reads <= row,
          "the fold reads %s which the candidate row does not supply" % sorted(reads - row))


def test_a_backdated_proposal_is_judged_where_it_LANDS(tmp):
    """The horizon. `append` inserts at the proposal's own turn, so judging against the HEAD
    asked whether a candidate would change a world it never enters.

    Measured before the fix: a backdated move was ACCEPTED while leaving the head fold identical —
    the module's stated invariant ("the answer cannot drift from what committing would do")
    violated by its own gate."""
    led = _led(tmp, "backdate")
    keeper.apply_proposals(led, "r1", [
        {"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the mill"}}])

    # turn 0 is BEFORE the mill move, so a move to the docks there genuinely changes that fold
    applied, rejected = keeper.apply_proposals(led, "r1", [
        {"turn": 0, "type": "move", "actor": "maren", "payload": {"to": "the docks"}}])
    check("a-backfill-that-changes-ITS-OWN-turn-is-accepted", len(applied) == 1, str(rejected))
    check("and-it-really-does-change-that-fold",
          led.fold("r1", 0)["agents"]["maren"]["location"] == "the docks",
          str(led.fold("r1", 0)["agents"]))
    # while the head still shows the later move — the log is ordered, not overwritten
    check("the-head-still-shows-the-later-move",
          led.fold("r1", 1)["agents"]["maren"]["location"] == "the mill",
          str(led.fold("r1", 1)["agents"]))


def test_park_then_KEEPER_then_RESUME(tmp):
    """THE SEQUENCE A USER ACTUALLY RUNS, which no test ran before.

    Every mechanism here was covered in isolation and the suite was green while this exact order
    bricked a run: `scene.py` persists a snapshot when it parks; the keeper appends events at or
    below that turn; `resume` replays only events AFTER the cached turn, so the incremental fold
    missed them, diverged from the from-zero fold, and refused — permanently, until someone deleted
    snapshot rows by hand.

    `test_place.py` happened to call `persist_snapshot` AFTER the append and so passed straight
    over the hole. Coverage before correctness, one layer up."""
    led = _led(tmp, "parkresume")
    led.persist_snapshot("r1", 1, led.fold("r1", 1))          # what scene.py does when it parks
    led.set_status("r1", "parked")

    applied, rejected = keeper.apply_proposals(
        led, "r1", [{"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the ridge"}}])
    check("the-keeper-applied-it", len(applied) == 1, str(rejected))

    try:
        out = led.resume("r1")
        check("the-run-still-RESUMES", True)
        check("and-the-resumed-world-carries-the-keepers-change",
              out["snapshot"]["agents"]["maren"]["location"] == "the ridge",
              str(out["snapshot"]["agents"]))
    except Exception as e:                                    # noqa: BLE001 — report, do not raise
        check("the-run-still-RESUMES", False, "%s: %s" % (type(e).__name__, str(e)[:120]))
        check("and-the-resumed-world-carries-the-keepers-change", False, "resume raised")


def test_only_the_STALE_snapshots_are_dropped(tmp):
    """A snapshot BELOW the appended event is still correct — `fold` replays by effective_at,
    so an event effective at turn N cannot change the fold at any earlier turn. Dropping those too
    would make the next resume replay the whole log for nothing."""
    led = _led(tmp, "partial")
    led.persist_snapshot("r1", 0, led.fold("r1", 0))
    led.persist_snapshot("r1", 1, led.fold("r1", 1))
    keeper.apply_proposals(
        led, "r1", [{"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the ridge"}}])

    turns = {r["as_of_turn"] for r in led.con.execute(
        "SELECT DISTINCT as_of_turn FROM snapshots WHERE run_id = ?", ("r1",))}
    check("the-stale-snapshot-was-dropped", 1 not in turns, str(sorted(turns)))
    check("the-EARLIER-one-survived", 0 in turns, str(sorted(turns)))

def test_a_REVEALER_knows_their_own_fact(tmp):
    """You cannot tell someone a thing you do not know.

    The rubric never told the keeper to put the speaker in a reveal's `to` list, and nothing in
    the fold added them — so a well-formed reveal made the SPEAKER a non-knower of the fact they
    had just disclosed. `faithfulness.check_fact_leaks` would then flag them for stating it and
    regenerate a turn that was never wrong: the leak wall firing on the one person guaranteed to
    know. Fixed in the fold rather than the prompt, so no keeper can forget it."""
    from src.engine.faithfulness import check_fact_leaks
    led = _led(tmp, "revealer")
    applied, rejected = keeper.apply_proposals(led, "r1", [
        {"turn": 1, "type": "reveal", "actor": "maren",
         "payload": {"fact": "the well is poisoned", "to": ["edda"]}}])
    check("the-reveal-was-applied", len(applied) == 1, str(rejected))

    info = led.fold("r1", 1)["information"]
    knowers = info.get("the well is poisoned", [])
    check("the-listener-knows-it", "edda" in knowers, str(info))
    check("and-so-does-the-REVEALER", "maren" in knowers, str(info))
    check("so-the-leak-wall-does-not-flag-the-speaker",
          check_fact_leaks("The well is poisoned.", "maren", info) == [],
          "the revealer was flagged for stating their own fact")
    check("but-it-still-flags-a-third-party",
          check_fact_leaks("The well is poisoned.", "someone_else", info) != [],
          "the wall stopped working entirely")

def main():
    print("test_keeper.py — the emitting seat (the world moves, and refuses to)\n")
    tmp = tempfile.mkdtemp(prefix="swe_keeper_test_")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn(tmp)
    print("\n%s" % ("test_keeper: OK (the snapshot moves; a beat is refused and leaves no row)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


def test_an_EMPTY_identity_never_reaches_the_LOG(tmp):
    """THE BRICK, end to end. This is the sequence, not the unit.

    Before 2026-09-02 every step here succeeded except the last two: the proposal was applied, the
    fold wrote `information[""]`, the event went into the APPEND-ONLY log, and from then on the run
    could neither be parked nor resumed — `CHECK constraint failed: key <> ''`, forever, with no
    correction event that removes an information key. One malformed keeper reply, one dead book.

    The schema CHECK did not cause that. It made it VISIBLE: the payload gate had never once looked
    at what a required key carried."""
    led = _led(tmp, "brick")
    for etype, payload in (("reveal", {"fact": "", "to": ["edda"]}),
                           ("seize", {"asset": ""}),
                           ("destroy-asset", {"asset": ""})):
        applied, rejected = keeper.apply_proposals(
            led, "r1", [{"turn": 1, "type": etype, "actor": "maren", "payload": payload}])
        check("empty-identity-REFUSED-%s" % etype, not applied and len(rejected) == 1,
              "applied=%r" % (applied,))
        check("...and-the-refusal-names-the-CODE-%s" % etype,
              "WORLD_EVENT_PAYLOAD_VALUE_EMPTY" in str(rejected), str(rejected)[:160])

    snap = led.fold("r1", 1)
    check("nothing-blank-is-in-the-world",
          "" not in snap["information"] and "" not in snap["holdings"],
          "info=%r holdings=%r" % (snap["information"], snap["holdings"]))

    # ...and the two operations the brick killed. These are the assertions that would have caught it.
    try:
        led.persist_snapshot("r1", 1, snap)
        check("the-run-can-still-be-PARKED", True)
    except Exception as e:                               # noqa: BLE001
        check("the-run-can-still-be-PARKED", False, "%s: %s" % (type(e).__name__, e))
    try:
        led.resume("r1")
        check("the-run-can-still-be-RESUMED", True)
    except Exception as e:                               # noqa: BLE001
        check("the-run-can-still-be-RESUMED", False, "%s: %s" % (type(e).__name__, e))


def test_an_utterance_with_no_SPEAKER_is_refused_by_NAME(tmp):
    """The seat reports to an operator, so the reason must name the FIELD.

    `utterances.speaker` became a constrained column on 2026-09-02, which turned a report with no
    speaker from silently-recorded-as-blank into a raw `CHECK constraint failed: speaker <> ''`
    surfacing through this seat's blanket except. True, and useless to whoever has to fix the
    report."""
    led = _led(tmp, "nospeaker")
    recorded, rejected = keeper.record_utterances(
        led, "r1", [{"turn": 1, "speaker": "", "said": "the levy was doubled"}])
    check("speakerless-utterance-refused", not recorded and len(rejected) == 1, str(recorded))
    check("...and-the-reason-says-SPEAKER", "SPEAKER" in str(rejected), str(rejected)[:160])
    check("...not-a-raw-constraint-error", "CHECK constraint" not in str(rejected),
          str(rejected)[:160])


if __name__ == "__main__":
    sys.exit(main())
