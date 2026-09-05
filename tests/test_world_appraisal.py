#!/usr/bin/env python3
"""test_world_appraisal.py — the world-side mirror of state-engine, and its first register.

WHAT WAS WRONG FOR THREE MONTHS. `consolidation.CATALOG` declared `threaten` with
`world_map: "tensions"` on 2026-06-11 — the same day the `tension` fold branch landed — and no
`threaten` branch was ever written. The register was inert in every direction at once: not
authorable, not seeded, never emitted, no delta path, no decay. A type claimed a world effect it had
never once had, and `tests/test_world_events.py` printed it as DEBT on every run for months.

THE PIECE THAT WAS MISSING was the word "relevant". `world-dynamics.md` says an act raises *the
relevant* tension temperature and nothing decided which one. The answer was in the same sentence:
*"(typed event x standing interests) -> state delta, COMPUTED, NEVER GUESSED."* Identity is not
carried in a payload and not chosen by a model — it is priced, against every live entry.

WHY A CHASSIS AND NOT A TENSIONS MODULE. The same sentence names three registers: tension
temperature, scarce-resource levels, faction disposition. Written register-shaped, the next two
arrive as copies of this arithmetic — the duplicate class CLAUDE.md tabulates seven instances of.
Written mechanism-shaped, they arrive as callers. So the tests below are in two halves: the CHASSIS
(register-agnostic) and TENSIONS (its first caller).

Script-style, stdlib only, exit 0 = all pass.
"""
import io
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import tensions as T                          # noqa: E402
from src.engine import world_appraisal as WA                  # noqa: E402
from src.engine import world_events                           # noqa: E402
from src.engine.ledger import Ledger                          # noqa: E402
from src.engine.records import Event                          # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _seed(tid="harbour-levy", **over):
    row = {"id": tid, "temperature": 0.1, "factions": ["guild", "boatmen"],
           "watches": {"parties": ["guild", "tam"], "locations": ["crossing"]},
           "interests": {"social_violation": 0.6, "threat": 0.3}, "cooling": "slow"}
    row.update(over)
    return row


def _led(tmp, name):
    led = Ledger(os.path.join(tmp, name + ".db"))
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    return led


# ---- the CHASSIS ------------------------------------------------------------------------------

def test_the_dimension_vocabulary_is_DERIVED_not_copied(tmp):
    """`consolidation.py` imports the same table with the same comment, for the same reason: a
    second copy of this list already cost a live run every one of its appraisals."""
    from src.engine.state import _DIM_TO_PRIMARY
    check("the-chassis-derives-its-dimensions", WA.DIMENSIONS == frozenset(_DIM_TO_PRIMARY),
          "%s vs %s" % (sorted(WA.DIMENSIONS), sorted(_DIM_TO_PRIMARY)))


def test_relevance_is_the_docs_formula(tmp):
    """(typed event x standing interests). A matched dimension contributes; an unmatched one does
    not; and the result is normalised by interest mass so an entry that cares about many things is
    not thereby easier to move than one that cares about few."""
    interests = {"social_violation": 0.6, "threat": 0.3}
    check("a-matched-dimension-scores", WA.relevance({"social_violation": 0.8}, interests) > 0)
    check("an-unmatched-one-scores-nothing", WA.relevance({"mastery": 1.0}, interests) == 0.0)
    check("scoring-is-bounded", 0.0 <= WA.relevance({"social_violation": 1.0, "threat": 1.0},
                                                    interests) <= 1.0)
    # the normalisation, stated as a property rather than a number: caring about MORE things does
    # not make an entry more movable by the same single event
    narrow = WA.relevance({"threat": 0.8}, {"threat": 0.5})
    broad = WA.relevance({"threat": 0.8}, {"threat": 0.5, "loss": 0.5, "mastery": 0.5})
    check("caring-about-more-does-not-make-you-easier-to-move", broad < narrow,
          "narrow=%r broad=%r" % (narrow, broad))

    # ...AND the absolute dial still works. A first version divided by the raw mass, which made the
    # function scale-invariant: "barely about this" and "entirely about this" priced identically,
    # so an authored weight was decorative while the validator bounded it to [0,1] as if it were
    # not. Both properties or neither — that is the whole point of the max(1, mass) floor.
    barely = WA.relevance({"threat": 0.8}, {"threat": 0.1})
    wholly = WA.relevance({"threat": 0.8}, {"threat": 1.0})
    check("a-tension-BARELY-about-a-thing-moves-less", barely < wholly,
          "barely=%r wholly=%r — the authored weight is decorative" % (barely, wholly))
    check("and-the-weight-scales-it-proportionally", abs(barely * 10 - wholly) < 1e-9,
          "barely=%r wholly=%r" % (barely, wholly))


def test_a_severity_WORD_reaching_the_arithmetic_fails_LOUD(tmp):
    """Words resolve at the parse seam. If one reaches here, the seam was bypassed — and silently
    treating it as zero would make a severe act land as nothing."""
    try:
        WA.relevance({"threat": "marked"}, {"threat": 0.5})
        check("a-word-in-the-arithmetic-raises", False, "it was accepted")
    except WA.WorldAppraisalError as e:
        check("a-word-in-the-arithmetic-raises", "parse seam" in str(e), str(e)[:80])


def test_cooling_is_monotone_and_ordered(tmp):
    """Time only ever removes heat, and the authored rates rank the way their names claim."""
    check("cooling-never-adds", WA.cool(0.5, 10, "typical") <= 0.5)
    check("more-time-cools-more", WA.cool(0.5, 10, "typical") < WA.cool(0.5, 1, "typical"))
    check("zero-elapsed-changes-nothing", WA.cool(0.5, 0, "typical") == 0.5)
    check("slow-outlasts-typical-outlasts-fast",
          WA.cool(0.5, 5, "slow") > WA.cool(0.5, 5, "typical") > WA.cool(0.5, 5, "fast"))


def test_an_entry_that_can_never_move_is_REFUSED(tmp):
    """The authoring-time fence. An entry with no interests, or watching nothing, looks live and can
    never be moved by anything — it would sit inert for a whole book with no error anywhere."""
    for label, call in (
        ("no-interests", lambda: WA.validate_interests({})),
        ("unknown-dimension", lambda: WA.validate_interests({"vibes": 0.5})),
        ("out-of-range-weight", lambda: WA.validate_interests({"threat": 1.4})),
        ("watches-nothing", lambda: WA.validate_watches({})),
        ("watches-not-a-list", lambda: WA.validate_watches({"parties": "guild"})),
        # COUNTING ENTRIES IS NOT LOOKING AT THEM. `{"parties": [""]}` satisfied the
        # watches-nothing check above — the list is non-empty — and produced the identical
        # condition, because `in_scope` matches each member by name and no event carries a blank
        # actor, target or location. Measured 2026-09-02: it validated, folded, and could never
        # once be in scope.
        ("a-watch-list-of-BLANKS", lambda: WA.validate_watches({"parties": [""]})),
        ("a-blank-among-real-ones",
         lambda: WA.validate_watches({"parties": ["guild", "   "], "locations": []})),
        ("a-non-string-watch-member", lambda: WA.validate_watches({"locations": [None]})),
    ):
        try:
            call()
            check("refuses-%s" % label, False, "it was accepted")
        except WA.WorldAppraisalError:
            check("refuses-%s" % label, True)

    # ...and the control: real members still validate. A guard that refused everything would pass
    # every case above.
    check("a-real-watch-list-still-validates",
          WA.validate_watches({"parties": ["guild"], "locations": ["crossing"]}))

    # the same hole one container over — the snapshot carries `factions` verbatim for the room
    try:
        T.validate_seed(_seed("the-levy", factions=["", "the guild"]))
        check("refuses-a-blank-FACTION", False, "it was accepted")
    except T.TensionError as e:
        check("refuses-a-blank-FACTION", e.code == "TENSION_FACTION_EMPTY", e.code)


# ---- TENSIONS, the first caller ----------------------------------------------------------------

def test_an_act_heats_only_what_WATCHES_it(tmp):
    """FALSIFICATION #3 from the design review, as a standing test: two tensions, one watching and
    one not; only the watcher may move. This is the fence that keeps 'only the levered is written'
    true — `world-state-ledger.md`: 'the sim doesn't log every peasant'."""
    reg = {}
    T.fold_seed(reg, _seed(), 0)
    T.fold_seed(reg, _seed("the-blight", watches={"locations": ["fields"]},
                           interests={"loss": 0.9}), 0)
    before = json.loads(json.dumps(reg))

    heated = T.fold_act(reg, {"social_violation": 0.78}, 3,
                        actor="guild", target="tam", location="crossing")
    check("the-watching-tension-heated", heated == ["harbour-levy"], str(heated))
    check("and-it-really-moved", reg["harbour-levy"]["temperature"] > before["harbour-levy"]["temperature"])
    check("the-UNWATCHING-one-did-not",
          reg["the-blight"]["temperature"] == before["the-blight"]["temperature"],
          "an act nobody watches moved a tension")

    check("an-act-in-no-scope-at-all-heats-nothing",
          T.fold_act(reg, {"social_violation": 0.9}, 4, actor="stranger", location="moor") == [])


def test_ONE_act_may_heat_SEVERAL_tensions(tmp):
    """Not a collision — two true facts. `world-dynamics.md`'s public killing can raise both the
    levy dispute and the old blood-feud, and a design that forced a single winner would be choosing
    which one mattered, which is the guess the doc forbids."""
    reg = {}
    T.fold_seed(reg, _seed(), 0)
    T.fold_seed(reg, _seed("the-old-feud", watches={"parties": ["tam"]},
                           interests={"social_violation": 0.8}), 0)
    heated = T.fold_act(reg, {"social_violation": 0.78}, 2, actor="guild", target="tam")
    check("both-watching-tensions-heated", sorted(heated) == ["harbour-levy", "the-old-feud"],
          str(heated))


def test_the_KEEPER_cannot_mint_a_tension(tmp):
    """Minting is the director's. `world-dynamics.md`: 'the world is DIRECTED (the room acts it)...
    its will is the director.' A delta naming no live tension is a fold no-op AND is refused at the
    seat, where an operator is standing to see it."""
    reg = {}
    T.fold_delta(reg, {"id": "invented-by-a-model", "heat": 0.5}, 1)
    check("a-delta-cannot-create", reg == {}, str(reg))

    blob = json.dumps(T.rubric())
    check("the-rubric-tells-the-keeper-so", "never name a new one" in blob.lower(), blob[:120])


def test_threaten_MOVES_THE_WORLD_through_the_real_fold(tmp):
    """End to end, through `_project` — the thing that was false for three months."""
    led = _led(tmp, "endtoend")
    world_events.append(led, "r1", 0, [Event(type="tension", payload=_seed())])
    before = led.fold("r1", 0)["tensions"]["harbour-levy"]["temperature"]

    ev = Event(type="threaten", actor="guild", target="tam", location="crossing",
               payload={"dimensions": {"social_violation": 0.78}})
    check("the-warrant-test-says-it-MOVES-the-world",
          world_events.would_change(led, "r1", 1, ev, at_turn=1),
          "threaten still folds to nothing")
    world_events.append(led, "r1", 1, [ev])
    after = led.fold("r1", 1)["tensions"]["harbour-levy"]
    check("and-the-temperature-rose", after["temperature"] > before,
          "%r -> %r" % (before, after["temperature"]))
    check("and-the-heat-was-stamped", after["last_heated_at"] == 1, str(after))


def test_a_threat_NOTHING_watches_is_refused_as_a_beat(tmp):
    """The scope fence meeting the warrant gate. This is what stops every squabble in a book minting
    world state, and it needs no new machinery — the emitting seat already refuses an event that
    would not change the snapshot."""
    import keeper
    led = _led(tmp, "beat")
    led.register_character("r1", "maren", {"name": "M"}, {"temperament": "a"})
    from src.engine.records import TurnCommit, PRIMARIES
    led.append_turn(TurnCommit(run_id="r1", turn=0, actor="maren", thought="t", action="a",
                               tags={"type": "mundane"}, affect={p: 0.5 for p in PRIMARIES},
                               events=[]))
    world_events.append(led, "r1", 0, [Event(type="tension", payload=_seed())])

    applied, rejected = keeper.apply_proposals(led, "r1", [
        {"turn": 0, "type": "threaten", "actor": "stranger", "target": "other",
         "payload": {"dimensions": {"social_violation": 0.78}}}])
    check("an-unwatched-threat-is-REFUSED", not applied and len(rejected) == 1, str(applied))
    check("and-the-reason-says-it-was-a-beat",
          rejected and "beat" in rejected[0][1], str(rejected))


def test_temperature_never_reaches_a_PROMPT_as_a_number(tmp):
    """Hard rule 5's gray zone, which this build makes due. `build_keeper_prompt` dumps the snapshot,
    so a live tension register would have put a float in front of a model."""
    import keeper
    snap = {"tensions": {"harbour-levy": {"temperature": 0.63, "factions": ["g"],
                                          "interests": {"threat": 0.5}}}, "clock": {"now": 3}}
    blob = json.dumps(keeper.build_keeper_prompt(
        [{"turn": 0, "actor": "a", "action": "x", "thought": "y"}], snap))
    check("no-raw-temperature-in-the-prompt", "0.63" not in blob, blob[:160])
    check("it-renders-as-a-severity-word", "marked" in blob, blob[:160])
    check("and-the-pricing-table-is-withheld", "interests" not in blob,
          "the keeper can see what it would be scored on")


def test_the_effective_temperature_is_DERIVED_and_DETERMINISTIC(tmp):
    """Hard rule 2 survives the feature because time is applied at READ. The fold keeps the raw
    accumulated value; cooling is a pure function, so the same log and the same declared elapsed
    give the same answer in any process.

    THE HASH-SEED LOOP IS KEPT BUT IS NOT THE POINT, and saying so rather than implying otherwise:
    `_build_edges` needed it because it walked a SET, and set iteration varies per process. Nothing
    here can: `fold_act` sorts, dict iteration is insertion-ordered, `in_scope` is boolean. So the
    loop is a cheap standing check that no future rewrite introduces set iteration — not evidence of
    determinism today. The assertions that carry weight are the exact values and `eff < raw`."""
    prog = chr(10).join((
        "import sys, json",
        "sys.path.insert(0, %r)" % REPO,
        "from src.engine import tensions as T",
        "reg = {}",
        "T.fold_seed(reg, %r, 0)" % (_seed(),),
        "T.fold_act(reg, {'social_violation': 0.78}, 1, actor='guild', location='crossing')",
        "print(json.dumps([round(reg['harbour-levy']['temperature'], 12),"
        " round(T.effective(reg['harbour-levy'], 7), 12)]))",
    ))
    outs = []
    for seed in ("0", "1", "2", "5"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        outs.append(subprocess.run([sys.executable, "-c", prog], capture_output=True,
                                   text=True, env=env).stdout.strip())
    check("same-log-same-temperature-across-processes", len(set(outs)) == 1, str(set(outs)))
    raw, eff = json.loads(outs[0])
    check("and-time-has-actually-cooled-it", eff < raw, "raw=%r effective=%r" % (raw, eff))


def test_authored_tensions_SEED_as_events_not_as_a_decree(tmp):
    """`world-state-ledger.md` write-path #3: the director 'may seed ledger state... but always as an
    event, never a decree.' That is what makes creating a tension and minting one mid-run the same
    mechanism at different turns, rather than two mechanisms that can disagree."""
    world = {"tensions": [_seed(), _seed("the-blight", watches={"locations": ["fields"]},
                                         interests={"loss": 0.9})]}
    events = T.seed_events(world)
    check("one-event-per-authored-tension", len(events) == 2, str(events))
    check("and-they-are-tension-events", {e["type"] for e in events} == {"tension"}, str(events))
    check("a-world-with-none-seeds-nothing", T.seed_events({}) == [])


def test_the_SEVERITY_WORD_form_the_seat_ASKS_FOR_actually_works(tmp):
    """THE GUARD THAT WAS MISSING, and the reason 61 suites were green over a broken contract.

    `tensions.rubric()` instructs the keeper to grade "in the severity words" and `severity.rubric()`
    names this seat as its consumer — and no seam resolved them, so every conforming reply died in
    the fold with a type error. Every existing test graded in FLOATS, which is exactly why nothing
    noticed: the suite exercised a form the seat does not ask for."""
    import keeper
    from src.engine.records import TurnCommit, PRIMARIES
    led = _led(tmp, "wordform")
    led.register_character("r1", "maren", {"name": "M"}, {"temperament": "a"})
    led.append_turn(TurnCommit(run_id="r1", turn=0, actor="maren", thought="t", action="a",
                               tags={"type": "mundane"}, affect={p: 0.5 for p in PRIMARIES},
                               events=[]))
    world_events.append(led, "r1", 0, [Event(type="tension", payload=_seed(
        watches={"parties": ["maren"]}))])
    before = led.fold("r1", 0)["tensions"]["harbour-levy"]["temperature"]

    applied, rejected = keeper.apply_proposals(led, "r1", [
        {"turn": 0, "type": "threaten", "actor": "maren", "target": "x",
         "payload": {"dimensions": {"threat": "marked", "social_violation": "severe"}}}])
    check("a-WORD-graded-threat-is-applied", len(applied) == 1, str(rejected))
    check("and-it-heated-the-tension",
          led.fold("r1", 0)["tensions"]["harbour-levy"]["temperature"] > before)

    # ...and the ladder the seat asks the model to use is IN the prompt it sends
    blob = json.dumps(keeper.build_keeper_prompt(
        [{"turn": 0, "actor": "a", "action": "x", "thought": "y"}], {}))
    check("the-prompt-carries-the-ladder",
          all(w in blob for w in ("faint", "mild", "marked", "severe", "extreme")), blob[:120])
    check("and-the-tension-rubric-it-restated-by-hand",
          "never name a new one" in blob.lower(), blob[:120])


def test_an_AUTHORED_temperature_word_resolves_at_the_load_seam(tmp):
    """The validator's own message promised this and no seam existed — so an authored
    `"temperature": "mild"` was refused by the sentence saying it was legal."""
    row = _seed(temperature="mild")
    T.validate_seed(row)
    from src.engine.severity import value_of
    check("an-authored-word-resolves", row["temperature"] == value_of("mild"), str(row["temperature"]))
    try:
        T.validate_seed(_seed(temperature="loud"))
        check("an-off-ladder-word-is-refused", False, "accepted it")
    except Exception as e:
        check("an-off-ladder-word-is-refused", "not a severity word" in str(e), str(e)[:70])


def test_the_DECAY_has_a_reader(tmp):
    """It shipped with none: `effective()` was called only by tests, so "tension temperatures
    cool absent fuel" was true inside this file and nowhere else — the
    documented-mechanism-with-no-reader class, recommitted in the build that cites it.

    The one live consumer of the register is the keeper prompt, so that is where time is applied."""
    import keeper
    from src.engine.records import TurnCommit, PRIMARIES
    led = _led(tmp, "decayreader")
    led.register_character("r1", "m", {"name": "M"}, {"temperament": "a"})
    for t in range(3):
        led.append_turn(TurnCommit(run_id="r1", turn=t, actor="m", thought="t", action="a",
                                   tags={"type": "mundane"},
                                   affect={p: 0.5 for p in PRIMARIES}, events=[]))
    world_events.append(led, "r1", 0, [Event(type="tension", payload=_seed(
        temperature=0.6, cooling="fast", watches={"parties": ["m"]}))])
    snap = led.fold("r1", 2)

    hot = keeper._band_temperatures(snap)["tensions"]["harbour-levy"]["temperature"]
    led.declare_time("r1", 1, 12.0, "director")
    led.declare_time("r1", 2, 12.0, "director")
    cooled = keeper._band_temperatures(snap, led, "r1")["tensions"]["harbour-levy"]["temperature"]
    check("the-uncooled-band-is-hot", hot == "marked", hot)
    check("and-declared-time-COOLS-what-the-keeper-sees", cooled != hot, "%s -> %s" % (hot, cooled))


def test_a_delta_naming_no_live_tension_says_SO(tmp):
    """A reference error wearing a warrant failure. The fold no-ops (it must stay total over
    the log), so the operator was told "it would not change the snapshot — it is a beat", and went
    looking for a scope problem when what they had was a typo."""
    import keeper
    from src.engine.records import TurnCommit, PRIMARIES
    led = _led(tmp, "typo")
    led.register_character("r1", "m", {"name": "M"}, {"temperament": "a"})
    led.append_turn(TurnCommit(run_id="r1", turn=0, actor="m", thought="t", action="a",
                               tags={"type": "mundane"}, affect={p: 0.5 for p in PRIMARIES},
                               events=[]))
    world_events.append(led, "r1", 0, [Event(type="tension", payload=_seed(
        watches={"parties": ["m"]}))])

    _a, rejected = keeper.apply_proposals(led, "r1", [
        {"turn": 0, "type": "tension", "payload": {"id": "harbor-levy", "heat": 0.1}}])
    check("a-typo-is-called-a-REFERENCE-error",
          rejected and "names no live tension" in rejected[0][1], str(rejected))
    check("and-it-lists-what-IS-live",
          rejected and "harbour-levy" in rejected[0][1], str(rejected))

    applied, _r = keeper.apply_proposals(led, "r1", [
        {"turn": 0, "type": "tension", "payload": {"id": "harbour-levy", "heat": 0.1}}])
    check("while-the-real-id-still-applies", len(applied) == 1, str(_r))

def test_the_LOG_stores_floats_and_words_die_at_the_boundary(tmp):
    """THE CONVENTION, asserted rather than described.

    A severity word left in the log is a hostage to `severity._MAGNITUDE`: `fold_seed` resolves it
    at replay, so recalibrating that table would silently refold every historical run into a
    different world — hard rule 2's "pure function of the log" true in form, false in substance.
    Measured 2026-09-02: a keeper-minted seed stored "marked". The gate for that very build had
    rejected "a fold that accepts words" as a suppressed path, and then shipped one."""
    import keeper
    from src.engine.records import TurnCommit, PRIMARIES
    from src.engine.severity import value_of
    led = _led(tmp, "canonfloat")
    led.register_character("r1", "m", {"name": "M"}, {"temperament": "a"})
    led.append_turn(TurnCommit(run_id="r1", turn=0, actor="m", thought="t", action="a",
                               tags={"type": "mundane"}, affect={p: 0.5 for p in PRIMARIES},
                               events=[]))

    applied, rejected = keeper.apply_proposals(led, "r1", [
        {"turn": 0, "type": "tension",
         "payload": dict(_seed(), temperature="marked", watches={"parties": ["m"]})}])
    check("a-word-graded-seed-applies", len(applied) == 1, str(rejected))

    stored = json.loads(led.con.execute(
        "SELECT payload FROM events WHERE type='tension'").fetchone()["payload"])
    check("but-the-LOG-stores-the-FLOAT", stored["temperature"] == value_of("marked"),
          "the log holds %r — a word in the log is pinned to the ladder's current values"
          % (stored["temperature"],))

    # and an off-ladder word is a VALIDATION refusal at the seat, not a fold judgment
    _a, rej = keeper.apply_proposals(led, "r1", [
        {"turn": 0, "type": "tension",
         "payload": dict(_seed("x"), temperature="loud", watches={"parties": ["m"]})}])
    check("an-off-ladder-word-is-refused-AS-a-word",
          rej and "not a severity word" in rej[0][1] and "could not judge" not in rej[0][1],
          str(rej))


def test_the_rubric_teaches_the_PAYLOAD_SHAPE_not_only_the_meaning(tmp):
    """The seat was told to grade "in the severity words" and had to GUESS both the slot and
    the legal keys — one of seven dimension names reached the assembled prompt, and
    `social_violation` is not a guessable spelling. Rendered from `required_keys`, the same table
    the fold reads, so every future type carries its contract to every seat."""
    import keeper
    from src.engine.world_events import rubric, required_keys, TYPES
    text = rubric()
    for t in TYPES:
        for k in required_keys(t):
            check("rubric-teaches-%s-needs-%s" % (t, k), '"%s"' % k in text,
                  "the seat must guess %r for %r" % (k, t))
    for dim in WA.DIMENSIONS:
        check("rubric-names-the-dimension-%s" % dim, dim in text, "unguessable spelling")

    blob = keeper.build_keeper_prompt(
        [{"turn": 0, "actor": "a", "action": "x", "thought": "y"}], {})[0]["content"]
    check("and-it-reaches-the-assembled-prompt", "dimensions" in blob and "social_violation" in blob,
          blob[:120])
    check("the-never-mint-instruction-appears-ONCE",
          blob.lower().count("never name a new") == 1,
          "composed AND restated: %d copies" % blob.lower().count("never name a new"))


def test_the_clock_and_the_band_have_ONE_spelling_each(tmp):
    """Both lived in the keeper for an afternoon. A clock with two readings is two clocks, and
    two seats that disagree about what 0.55 is called will eventually print both."""
    import keeper
    from src.engine import clock
    led = _led(tmp, "onespelling")
    led.declare_time("r1", 1, 5.0, "d")
    led.declare_time("r1", 2, 7.0, "d")
    check("the-ledger-delegates-to-the-clock",
          led.elapsed_since("r1", 0) == clock.elapsed_since(led.con, "r1", 0) == 12.0,
          str(led.elapsed_since("r1", 0)))
    check("a-declaration-at-the-aged-turn-does-NOT-age-it",
          led.elapsed_since("r1", 2) == 0.0,
          "declare_time records time passed BEFORE its turn")

    # TWO DIRECTIONS, because a negative grep alone is the weakest shape there is: "no copy" is
    # satisfied by a seat that stopped doing the thing at all. Paired with a positive CALL check —
    # the idiom `test_capability_claims` already owns — the pair says the seat uses the one spelling
    # AND holds no second one.
    src = io.open(os.path.join(REPO, "scripts", "keeper.py"), encoding="utf-8").read()
    body = chr(10).join(l for l in src.splitlines()
                        if not l.lstrip().startswith(("import ", "from ", "#")))
    check("the-keeper-keeps-no-copy-of-the-clock", "time_declarations" not in src,
          "the seat re-implements the clock")
    check("and-CALLS-the-one-that-exists", "led.elapsed_since(" in body,
          "no copy and no call either — the seat stopped reading the clock at all")
    check("nor-its-own-band", "abs(value_of(" not in src, "the seat re-implements nearest-rung")
    check("and-CALLS-the-shared-band", "_wa.band(" in body,
          "no copy and no call either — the seat stopped banding at all")
    check("band-is-the-nearest-rung", WA.band(0.63) == "marked" and WA.band(0.0) == "faint",
          "%r %r" % (WA.band(0.63), WA.band(0.0)))

def main():
    print("test_world_appraisal.py — the world-side mirror, and its first register\n")
    tmp = tempfile.mkdtemp(prefix="swe_worldapp_test_")
    # PER-TEST, so one raiser does not take the file with it. Run bare, an assertion that RAISES
    # (rather than reporting through `check`) crashed the whole suite: nonzero exit, so run_all went
    # red — but the failure printed as a traceback instead of a named FAIL, and every test after it
    # was skipped silently. `test_ledger` and `test_place` already do it this way.
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        try:
            fn(tmp)
        except Exception as e:                       # noqa: BLE001 — a harness reports, never raises
            FAILS.append("%s RAISED %s: %s" % (fn.__name__, type(e).__name__, e))
            print("  FAIL  %s RAISED %s: %s" % (fn.__name__, type(e).__name__, str(e)[:90]))
    print("\n%s" % ("test_world_appraisal: OK (an act prices itself against every live tension, "
                    "heats only what watches it, and cools at read)" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
