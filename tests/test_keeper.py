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
from src.engine.records import TurnCommit, PATHS         # noqa: E402

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
                                   affect={p: 0.5 for p in PATHS}, events=[]))
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


# ---------------------------------------------------------------------------------------------
# THE ATTACHMENT RUBRIC (2026-09-19, bond gate 5's third writer of a hold) — attach_candidates /
# attach_price / attach_scene driven directly, the pure halves without a provider, plus one stub
# pass through attach_scene and one through canon_gate. Invented fixture only (hard rule 1): a
# millhouse and "maren", already `_led`'s own cast.
# ---------------------------------------------------------------------------------------------
_ATTACH_WORLD = {"locations": [{"id": "millhouse", "what": "the old millhouse on the ford"}],
                 "people": []}
_ATTACH_ENTITY = "loc.millhouse"
_ATTACH_SENTENCE = "I have kept this millhouse my whole life, since my father died."


def _kept_established(led, run_id, turn, speaker, sentence, obj):
    """Record an utterance binding `speaker` to `obj` (the raw extract object — written as the
    world's own registered id, the shape attach_candidates needs post-normalisation; see
    attach_candidates' own docstring on why an un-normalised registered name could never match a
    normalised one) and rule it ESTABLISHED. -> (utterance_id, a rule_scene-shaped `applied` list
    of one). Uses claims.record + claims.resolve directly — the keeper's own write path (the
    fixture at :157 above), not keeper.record_utterances/apply_rulings — because this drives the
    pure attach_* halves directly, without a provider, the way the gate's GREEN_CONDITION asks."""
    from src.engine import claims
    uid = claims.record(led.con, run_id, turn, speaker, sentence,
                        [{"subject": speaker, "predicate": "keeps", "object": obj}])
    claims.resolve(led.con, run_id, uid, turn, claims.ESTABLISHED, "the story leans on it")
    return uid, [{"utterance_id": uid, "verdict": claims.ESTABLISHED, "rationale": "the story leans on it"}]


def test_attach_candidates_finds_the_one_self_bound_KEPT_saying(tmp):
    """Guards 1 + 2: only what rule_scene actually kept (guard 1) and only ESTABLISHED (guard 2)."""
    led = _led(tmp, "attach-find")
    uid, applied = _kept_established(led, "r1", 1, "maren", _ATTACH_SENTENCE, _ATTACH_ENTITY)
    cands = keeper.attach_candidates(led, "r1", applied, 1, 1, _ATTACH_WORLD)
    check("exactly-one-candidate", len(cands) == 1, cands)
    check("it-names-speaker-entity-sentence-and-utterance-id",
          cands == [("maren", _ATTACH_ENTITY, _ATTACH_SENTENCE, uid)], cands)


def test_attach_candidates_ignores_a_LEFT_superposed_claim(tmp):
    """Guard 2, the refusal side: a ruling that never made it into rule_scene's `applied` (still
    superposed, or fiction) is not a candidate — only a ruling dict naming verdict ESTABLISHED is."""
    led = _led(tmp, "attach-t2")
    from src.engine import claims
    uid = claims.record(led.con, "r1", 1, "maren", _ATTACH_SENTENCE,
                        [{"subject": "maren", "predicate": "keeps", "object": _ATTACH_ENTITY}])
    left_as_superposed = [{"utterance_id": uid, "verdict": claims.SUPERPOSED, "rationale": "untested"}]
    check("a-superposed-ruling-is-no-candidate",
          keeper.attach_candidates(led, "r1", left_as_superposed, 1, 1, _ATTACH_WORLD) == [])
    fiction = [{"utterance_id": uid, "verdict": claims.FICTION, "rationale": "declined"}]
    check("a-fiction-ruling-is-no-candidate",
          keeper.attach_candidates(led, "r1", fiction, 1, 1, _ATTACH_WORLD) == [])


def test_attach_price_prices_ONE_RUNG_BELOW_the_word(tmp):
    """attach_price prices a canned `life` reply at word_below('life') == 'post', source keeper —
    the exact shape declared_row(self_sourced=True) is pinned to in test_attachments.py."""
    from src.engine import attachments as A
    reply = {"holds": [{"entity": _ATTACH_ENTITY, "relation": "life", "because": _ATTACH_SENTENCE}],
            "gaps": []}
    row, code = keeper.attach_price("maren", _ATTACH_ENTITY, reply, _ATTACH_SENTENCE, _ATTACH_WORLD, [])
    check("priced-not-refused", row is not None and code is None, (row, code))
    check("priced-one-rung-below-life-i.e.-at-post",
          row is not None and abs(row.hold - A.hold_of(A.word_below("life"))) < 1e-9, row)
    check("the-source-is-keeper", row is not None and row.source == "keeper", row)
    check("the-entity-and-char-are-right",
          row is not None and row.char_id == "maren" and row.entity == _ATTACH_ENTITY, row)


def test_a_declared_hold_removes_its_own_candidate_guard_3(tmp):
    """Guard 3, both halves in sequence: price it, declare it, and the SAME saying stops being a
    candidate — a keeper cannot re-price what it has already priced as high as it ever can reach."""
    from src.engine import attachments as A
    led = _led(tmp, "attach-guard3")
    uid, applied = _kept_established(led, "r1", 1, "maren", _ATTACH_SENTENCE, _ATTACH_ENTITY)
    reply = {"holds": [{"entity": _ATTACH_ENTITY, "relation": "life", "because": _ATTACH_SENTENCE}],
            "gaps": []}
    row, code = keeper.attach_price("maren", _ATTACH_ENTITY, reply, _ATTACH_SENTENCE, _ATTACH_WORLD, [])
    check("priced-clean-before-declaring", row is not None and code is None, (row, code))
    written = A.declare(led.con, "r1", 1, [row])
    check("the-row-was-written", written == 1, written)
    check("...and-carries-utterance-uid-%d-worth-of-history-i.e.-really-happened" % uid, uid > 0)
    cands = keeper.attach_candidates(led, "r1", applied, 1, 1, _ATTACH_WORLD)
    check("re-running-candidates-for-the-SAME-saying-now-finds-none", cands == [], cands)


def test_an_unregistered_name_yields_no_candidate(tmp):
    """guard 1's other edge: a kept, ESTABLISHED, self-bound claim about something the world does
    not register is not a candidate — attach_candidates never invents an entity."""
    led = _led(tmp, "attach-unregistered")
    _uid, applied = _kept_established(led, "r1", 1, "maren", "I keep the lighthouse.", "loc.lighthouse")
    cands = keeper.attach_candidates(led, "r1", applied, 1, 1, _ATTACH_WORLD)
    check("an-unregistered-object-is-no-candidate", cands == [], cands)


def test_a_speaker_already_at_LIFE_gets_no_candidate(tmp):
    """Guard 3's first half, on its own: a DIRECTOR-declared life-tier hold (full price, .85) blocks
    a later self-bound claim on the SAME entity before any classifier is ever asked."""
    from src.engine import attachments as A
    led = _led(tmp, "attach-alreadylife")
    A.declare(led.con, "r1", 0, [A.declared_row("maren", _ATTACH_ENTITY, "life", "director")])
    _uid, applied = _kept_established(led, "r1", 1, "maren", _ATTACH_SENTENCE, _ATTACH_ENTITY)
    cands = keeper.attach_candidates(led, "r1", applied, 1, 1, _ATTACH_WORLD)
    check("already-held-at-life-is-no-candidate", cands == [], cands)


def test_a_third_life_claim_is_refused_ATTACH_LIFE_CAP_and_collected(tmp):
    """The cap is at the WORD the classifier names, not the discounted stored price — a self-sourced
    `life` prices at `post` (.60) and could never itself trip validate_block's >= .85 check, so this
    is applied directly against attachments._LIFE_CAP. Collected as a refusal code, never raised."""
    from src.engine import attachments as A
    existing = [(0, "loc.a", A.hold_of("life"), "+", "authored"),
               (0, "loc.b", A.hold_of("life"), "+", "authored")]
    world3 = {"locations": [{"id": "a"}, {"id": "b"}, {"id": "c"}], "people": []}
    reply = {"holds": [{"entity": "loc.c", "relation": "life", "because": "the third and last"}],
            "gaps": []}
    row, code = keeper.attach_price("maren", "loc.c", reply, "the third and last", world3, existing)
    check("the-third-life-claim-is-refused-not-raised", row is None and code == "ATTACH_LIFE_CAP", (row, code))
    check("a-second-life-claim-still-passes-the-cap (cap is 2)",
          keeper.attach_price("maren", "loc.c", reply, "the third and last", world3,
                              existing[:1])[1] != "ATTACH_LIFE_CAP")


def test_a_reply_about_a_DIFFERENT_entity_is_KEEPER_ATTACH_OFF_TARGET(tmp):
    """The one refusal that belongs to this seat, not the shared composition-pass parser: the reply
    parsed clean but named no entry for the ONE entity this candidate's prompt ever asked about."""
    world2 = {"locations": [{"id": "millhouse"}, {"id": "tower"}], "people": []}
    reply = {"holds": [{"entity": "loc.tower", "relation": "post", "because": _ATTACH_SENTENCE}],
            "gaps": []}
    row, code = keeper.attach_price("maren", _ATTACH_ENTITY, reply, _ATTACH_SENTENCE, world2, [])
    check("off-target-reply-is-refused-by-name", row is None and code == "KEEPER_ATTACH_OFF_TARGET", (row, code))


def test_attach_scene_under_stub_asks_nothing(tmp):
    """attach_scene mirrors rule_scene/notice_scene under --stub: the candidates are still computed
    (a real DB read, no provider), the count is printed, nothing is asked, nothing is attached."""
    led = _led(tmp, "attach-stub")
    _uid, applied = _kept_established(led, "r1", 1, "maren", _ATTACH_SENTENCE, _ATTACH_ENTITY)
    lines = []
    result = keeper.attach_scene(led, "r1", applied, 1, 1, _ATTACH_WORLD, "subagent:none", True,
                                 log=lines.append)
    check("stub-attaches-nothing", result["attached"] == [], result)
    check("stub-still-COUNTS-the-candidate", result["candidates"] == 1, result)
    check("stub-refuses-and-skips-nothing", result["refused"] == [] and result["skipped"] == 0, result)
    check("the-stub-line-names-the-count-and-asks-nothing",
          any("KEEPER (stub): 1 attachment candidate(s), nothing asked" in ln for ln in lines), lines)


def test_the_prompt_shows_registered_names_ONLY_when_a_world_is_given(tmp):
    """THE PRODUCER SIDE of the attachment-rubric match (follow-up to gate
    keeper-attachment-rubric, 2026-09-19): the noticing pass cannot phrase a claim's object as a
    registered loc./grp. name unless it is SHOWN those names. build_keeper_prompt gains that block
    only when a world is actually in hand; absent one the prompt is unchanged — pinned by adjacency
    across the exact seam the block would sit in, not by a frozen snapshot of the whole prompt."""
    from critic import scene_turns
    led = _led(tmp, "attach-prompt")
    turns = scene_turns(led, "r1")
    snap = led.fold("r1", 1)

    with_world_sys = keeper.build_keeper_prompt(turns, snap, world=_ATTACH_WORLD)[0]["content"]
    check("registered-names-appear", "loc.millhouse" in with_world_sys, with_world_sys[:400])
    check("the-header-is-there", "THE REGISTERED PLACES AND GROUPS" in with_world_sys, with_world_sys[:400])
    check("the-rule-names-the-exact-match", "exactly, letter for letter" in with_world_sys, with_world_sys[:400])
    # RAW CONTENT, not json.dumps'd: a dumped em dash escapes to "—", whose four hex digits
    # would fail a digit sweep for a reason that has nothing to do with the rubric leaking a number.
    names_span = with_world_sys.split("THE REGISTERED PLACES AND GROUPS")[1].split("Reply with a JSON list")[0]
    check("still-digit-free", not any(ch.isdigit() for ch in names_span), names_span)

    world_no_names = {"locations": [], "people": []}
    with_empty_world_sys = keeper.build_keeper_prompt(turns, snap, world=world_no_names)[0]["content"]
    check("an-empty-but-real-world-says-so-rather-than-listing-nothing",
          "(none registered)" in with_empty_world_sys, with_empty_world_sys[:400])

    without_world = keeper.build_keeper_prompt(turns, snap)[0]["content"]
    without_world_explicit = keeper.build_keeper_prompt(turns, snap, world=None)[0]["content"]
    check("no-world-carries-no-registered-block", "REGISTERED PLACES" not in without_world, without_world[:400])
    check("default-and-explicit-None-agree", without_world == without_world_explicit)
    check("no-world-is-unchanged-AT-THE-EXACT-SEAM (nothing inserted between the claims "
          "paragraph and the reply contract)",
          ("the clause you would drop may be the whole point." + chr(10) + chr(10)
           + "Reply with a JSON list") in without_world, without_world[-500:])


def test_the_full_round_trip_through_record_utterances_survives_normalisation(tmp):
    """THE FULL PATH, through the keeper's own write seat (keeper.record_utterances — what
    notice_scene actually calls), not claims.record directly (which _kept_established above uses,
    and stays: it is the simpler pure fixture for driving attach_candidates/attach_price on their
    own). This proves the round trip — claims.record -> write -> extracts_of (normalise) -> the DB
    -> claims.for_run -> extracts_of again -> attach_candidates' match — survives going through the
    ACTUAL production write path end to end, the same shape a live noticing reply would take once
    it is shown the registered name (the test above) and echoes it back."""
    from src.engine import claims
    led = _led(tmp, "attach-roundtrip")
    recorded, rejected = keeper.record_utterances(led, "r1", [
        {"turn": 1, "speaker": "maren", "said": _ATTACH_SENTENCE,
         "extracts": [{"subject": "maren", "predicate": "keeps", "object": _ATTACH_ENTITY}]}])
    check("recorded-through-the-keepers-own-write-path", len(recorded) == 1 and not rejected, (recorded, rejected))
    uid = recorded[0]["utterance_id"]
    claims.resolve(led.con, "r1", uid, 1, claims.ESTABLISHED, "the story leans on it")
    applied = [{"utterance_id": uid, "verdict": claims.ESTABLISHED, "rationale": "the story leans on it"}]
    cands = keeper.attach_candidates(led, "r1", applied, 1, 1, _ATTACH_WORLD)
    check("attach_candidates-finds-it-through-the-FULL-round-trip",
          cands == [("maren", _ATTACH_ENTITY, _ATTACH_SENTENCE, uid)], cands)


def test_canon_gate_with_no_world_skips_the_rubric_and_asks_nothing(tmp):
    """FAIL CLOSED (canon_gate's docstring): attachments.names_for needs the bible, and a caller
    with none in hand — every existing caller before this gate, and test_lore.py's own — gets a
    keeper that prices nothing rather than one that raises or guesses at what is registered."""
    led = _led(tmp, "attach-noworld")
    lines = []
    gate = keeper.canon_gate(led, "r1", 0, 1, "subagent:none", True, log=lines.append)
    check("canon_gate-still-returns-an-attached-block", "attached" in gate, gate)
    check("no-world-attaches-nothing", gate["attached"]["attached"] == [], gate["attached"])
    check("no-world-counts-zero-candidates", gate["attached"]["candidates"] == 0, gate["attached"])
    check("the-skip-is-logged-by-name",
          any("attachment rubric skipped (no world)" in ln for ln in lines), lines)


if __name__ == "__main__":
    sys.exit(main())
