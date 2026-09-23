#!/usr/bin/env python3
"""test_toward.py — the MICRO tier (src/engine/toward.py): what one specific person makes you feel.

`docs/character-model.md` "THE THREE LAYERS" records the author's model; this is its micro half.
The macro half moves who you are everywhere. This moves only what happens in one person's company.

What this pins:
  1. IT GOES BOTH WAYS. `_DIM_TO_PATH` carries seven negative pushes, so a degrading act
     produces a NEGATIVE delta — the direction the arc cannot express at all (measured: a
     base-happy character through 80 durable diffs ended with FEAR saturated and PLAY, CARE, RAGE
     and DISGUST unchanged).
  2. IT IS PER PERSON. The same character, the same scene, a different person in the room -> a
     different effective vector. That is the whole point and nothing else in the engine does it.
  3. PRESENT **or** SUBJECT — you can be moved by someone who is not there.
  4. THE AUTHORED BASE SURVIVES (law 1), stamped before the first fold, never re-baselined.
  5. It never reaches the actor as a number.
  6. SINCE 2026-09-12 (the redesign, gate 1) THE TIER IS ATTITUDE AND THE PLAYED STATE IS COMPOSED:
     mood (the flat float) + attitude (per person, uncapped) -> `balance`; a person above the mood
     is played at their attitude, a cooler person is met halfway down and never below rest; others
     present lift, damped; nobody engaged -> the mood itself. The additive `rows` and the cap are gone.
  7. SINCE 2026-09-19 (gate `attitude-staircase`) EROSION IS PER RUNG AND IN MINUTES: the same
     staircase the mood tier steps (`state._rung_half_life`) at a slower per-path scale whose
     BOTTOM rung is the old per-day rate converted — so a bottom-rung attitude over 1440 minutes is
     byte-for-byte what one flat day used to give, and a hatred at the top of the ladder is not.
  8. SINCE 2026-09-19 (gate `emotion-tier-tidy`) THE MAX-ACROSS-OTHERS CLAIM IS TESTED: three
     present — one engaged, two merely in the room with different attitudes — is the first case
     where "max" and "sum" give different numbers, and `balance` gives the max: `_OTHERS_DAMP` x
     whichever of them earned more, never their total.

Stdlib only, script-style, exit 0 = all pass.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import toward                                  # noqa: E402
from src.engine.decay_law import relax                         # noqa: E402
from src.engine.levers import effective                        # noqa: E402
from src.engine.records import PATHS                       # noqa: E402
from src.engine.rung_blocks import BANDS                       # noqa: E402
from src.engine.state import _rung_half_life                   # noqa: E402

_DAY = 1440.0                                # minutes in a day — what an `erode` day rate is now


def _mid(path, index):
    """The midpoint of a rung's band — a value unambiguously INSIDE rung `index`. The top band's
    upper edge sits above 1.0 (so a saturated vector lands on the peak), hence the min."""
    lo, hi, _n = BANDS[path][index - 1]
    return (lo + min(hi, 1.0)) / 2.0


def _eroded(path, value, minutes, c=None):
    """`value` on `path` after `minutes`, through the real `erode` — None when it was dropped."""
    ch = {"current": {"toward": {"j": {path: value}}}}
    toward.erode(ch, minutes, None if c is None else {"j": c})
    return ch["current"]["toward"]["j"].get(path)

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def test_it_goes_both_ways():
    print("\n[1] a degrading act produces a NEGATIVE feeling — the direction the arc cannot express")
    v = toward.observe({"social_violation": 0.9})
    # RETIRED 2026-09-08. Read `v.get("PLAY", 0) < 0` -- a degrading act COSTS playfulness. It
    # was `social_violation`'s ONLY negative weight; the table still has negatives elsewhere
    # (loss -> STIRRING -0.18, mastery -> WARINESS -0.10, relief -> WARINESS -0.40 / DEFLATION
    # -0.35). PLAY's path is LEVITY; LEVITY is not built
    # (docs/rungs/LEVITY.md), so no surviving path is lowered by social_violation and this
    # assertion has no successor rather than a new subject. The "goes both ways" property it
    # guarded is GONE from the engine, not merely untested -- recorded, not quietly dropped.
    check("degradation-raises-rage", v.get("DISPLEASURE", 0) > 0, str(v))
    check("degradation-raises-disgust", v.get("DISTASTE", 0) > 0, str(v))
    w = toward.observe({"care_relevant": 0.9})
    check("kindness-raises-care", w.get("GOODWILL", 0) > 0, str(w))
    check("nothing-from-an-empty-event", toward.observe({}) == {})
    # the SAME table the current tier uses — law 4, one pricing table at every timescale
    from src.engine.state import _DIM_TO_PATH
    check("prices-with-the-shared-table",
          set(v) <= {p for _d, prs in _DIM_TO_PATH.items() for p, _w in prs}, str(v))


def test_it_is_per_person():
    """THE POINT. Same character, same mood, a different person engaged -> a different played vector."""
    print("\n[2] the same room, a different person")
    ch = {"current": {}}
    toward.replay(ch, [("joss", "STIRRING", 0.05), ("joss", "DISPLEASURE", 0.60),
                       ("nell", "STIRRING", 0.55)])
    tw = ch["current"]["toward"]
    mood = {p: 0.40 for p in PATHS}
    rest = {p: 0.10 for p in PATHS}
    with_joss, _, _ = toward.balance(mood, tw, rest, engaged="joss", present=["joss"], me="ren")
    with_nell, _, _ = toward.balance(mood, tw, rest, engaged="nell", present=["nell"], me="ren")
    alone, _, _ = toward.balance(mood, tw, rest, engaged=None, present=[], me="ren")
    check("joss-cools-his-stirring", with_joss["STIRRING"] < alone["STIRRING"],
          "%.3f vs %.3f" % (with_joss["STIRRING"], alone["STIRRING"]))
    check("nell-heats-his-stirring", with_nell["STIRRING"] > alone["STIRRING"],
          "%.3f vs %.3f" % (with_nell["STIRRING"], alone["STIRRING"]))
    check("joss-raises-his-displeasure", with_joss["DISPLEASURE"] > alone["DISPLEASURE"])
    check("alone-is-the-identity", alone == mood, str(alone))
    check("the-two-differ", with_joss["STIRRING"] != with_nell["STIRRING"])


def test_engaged_or_present():
    """ENGAGED in full; others PRESENT lift, damped, and never lower; a concept or oneself is nobody."""
    print("\n[3] engaged in full, present damped")
    tw = {"nell": {"STIRRING": 0.60}, "ren": {"STIRRING": 0.90}}
    mood = {p: 0.20 for p in PATHS}
    rest = {p: 0.10 for p in PATHS}
    eng, _, _ = toward.balance(mood, tw, rest, engaged="nell", present=["nell"], me="ren")
    check("engaged-plays-the-attitude", abs(eng["STIRRING"] - 0.60) < 1e-9, eng["STIRRING"])
    pres, _, _ = toward.balance(mood, tw, rest, engaged=None, present=["nell"], me="ren")
    check("present-lifts-damped", abs(pres["STIRRING"] - toward._OTHERS_DAMP * 0.60) < 1e-9, pres["STIRRING"])
    low = {"nell": {"STIRRING": 0.05}}
    pres2, _, _ = toward.balance(mood, low, rest, engaged=None, present=["nell"], me="ren")
    check("present-never-lowers", abs(pres2["STIRRING"] - 0.20) < 1e-9, pres2["STIRRING"])
    absent, _, _ = toward.balance(mood, tw, rest, engaged="nell", present=[], me="ren")
    check("engaged-though-absent-still-composes", abs(absent["STIRRING"] - 0.60) < 1e-9)
    me_, _, _ = toward.balance(mood, tw, rest, engaged="ren", present=["ren"], me="ren")
    check("oneself-is-nobody", me_ == mood, str(me_))
    cpt, _, _ = toward.balance(mood, tw, rest, engaged="concept:debt", present=[], me="ren")
    check("a-concept-is-nobody", cpt == mood, str(cpt))
    stranger, _, _ = toward.balance(mood, {}, rest, engaged="nell", present=["nell"], me="ren")
    check("a-stranger-engaged-is-met-halfway-down-to-rest", abs(stranger["STIRRING"] - 0.15) < 1e-9, stranger["STIRRING"])


def test_the_authored_base_survives():
    """LAW 1. An author may write a starting disposition; the fold must not eat it."""
    print("\n[4] the authored base survives")
    ch = {"current": {"toward": {"sister": {"DISPLEASURE": 0.10}}}}     # "she has always resented her"
    toward.replay(ch, [("sister", "DISPLEASURE", 0.08), ("sister", "GOODWILL", -0.05)])
    cur = ch["current"]
    check("authored-preserved", cur["_authored_toward"]["sister"] == {"DISPLEASURE": 0.10},
          str(cur["_authored_toward"]))
    check("effective-is-base-plus-experience",
          abs(cur["toward"]["sister"]["DISPLEASURE"] - 0.18) < 1e-9, str(cur["toward"]))
    check("and-a-new-primary-lands", abs(cur["toward"]["sister"]["GOODWILL"] + 0.05) < 1e-9,
          str(cur["toward"]))
    # re-folding must not re-baseline from the moved value
    toward.replay(ch, [("sister", "DISPLEASURE", 0.08), ("sister", "GOODWILL", -0.05)])
    check("refold-keeps-the-ORIGINAL-authored",
          cur["_authored_toward"]["sister"] == {"DISPLEASURE": 0.10}, str(cur["_authored_toward"]))
    check("refold-is-not-cumulative", abs(cur["toward"]["sister"]["DISPLEASURE"] - 0.18) < 1e-9,
          "folding the same log twice must give the same answer: %s" % cur["toward"])


def test_the_fold_is_order_independent_and_uncapped():
    print("\n[5] order-independent, uncapped, unit-bounded")
    a, b = {"current": {}}, {"current": {}}
    toward.replay(a, [("x", "DISPLEASURE", 0.2), ("x", "DISPLEASURE", -0.15)])
    toward.replay(b, [("x", "DISPLEASURE", -0.15), ("x", "DISPLEASURE", 0.2)])
    check("order-does-not-matter", a["current"]["toward"] == b["current"]["toward"],
          "%s vs %s" % (a["current"]["toward"], b["current"]["toward"]))
    c = {"current": {}}
    toward.replay(c, [("x", "GOODWILL", 0.12)] * 4)
    check("the-cap-is-gone", abs(c["current"]["toward"]["x"]["GOODWILL"] - 0.48) < 1e-9,
          "%s (a person may earn any rung now)" % c["current"]["toward"])
    d = {"current": {}}
    toward.replay(d, [("x", "DISPLEASURE", 0.9)] * 20)
    check("bounded-by-the-unit-interval", abs(d["current"]["toward"]["x"]["DISPLEASURE"] - 1.0) < 1e-9,
          str(d["current"]["toward"]))
    e = {"current": {}}
    toward.replay(e, [("x", "STIRRING", -0.9)] * 20)
    check("symmetrically", abs(e["current"]["toward"]["x"]["STIRRING"] + 1.0) < 1e-9, str(e["current"]["toward"]))


def test_it_never_reaches_the_actor_as_a_number():
    """Tested on the REAL path. `_strip_notes` is NOT the guard here — it touches only the stable
    prefix, built from fixed+baseline. What protects `current` is that `assemble`'s volatile block
    selects its keys explicitly rather than dumping the dict."""
    print("\n[6] it does not reach the actor as a number")
    from src.engine.scene import assemble
    from src.engine.prompt import build_turn_messages
    ch = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    toward.replay(ch, [("marlo_clerk", "DISPLEASURE", 0.19), ("marlo_clerk", "STIRRING", -0.21)])
    packet = assemble(ch, world, {"event": {"text": "the clerk is here", "kind": "mundane"},
                                  "target": "marlo_clerk"},
                      ch["current"]["affect"], ch["current"]["condition"])
    msgs = json.dumps(build_turn_messages(packet, "the clerk is here",
                                          ch["baseline"]["temperament"], {}))
    check("no-toward-key-in-the-prompt", "toward" not in msgs)
    check("no-authored-key-either", "_authored_toward" not in msgs)
    # and prove the attitude DID reach the arithmetic, or this test proves nothing: the clerk is the
    # subject, so they are the engaged person and the played DISPLEASURE is composed with the 0.19
    eff = packet["volatile"]["state"]["effective"]
    check("but-it-reached-the-played-vector",
          packet["volatile"]["state"]["engaged"] == "marlo_clerk"
          and abs(eff["DISPLEASURE"] - toward.compose(ch["current"]["affect"]["DISPLEASURE"], 0.19,
                                                       ch["baseline"]["temperament"]["DISPLEASURE"]["mean"])) < 1e-9,
          "engaged=%r eff=%s" % (packet["volatile"]["state"].get("engaged"), eff.get("DISPLEASURE")))


def test_fail_loud():
    print("\n[7] fail loud")
    for bad, why in ((("notadict",), "dims not a dict"),):
        try:
            toward.observe(*bad)
            check("raises-on-%s" % why, False, "returned instead of raising")
        except ValueError:
            check("raises-on-%s" % why, True)
    try:
        toward.observe({"threat": "a lot"})
        check("raises-on-prose-dimension", False, "returned instead of raising")
    except ValueError as e:
        check("raises-on-prose-dimension", "not a number" in str(e), str(e)[:70])
    try:
        toward.replay("notadict", [])
        check("raises-on-bad-char", False, "returned instead of raising")
    except ValueError:
        check("raises-on-bad-char", True)


def test_it_is_fed_by_readings():
    """THE SECOND FEED (gate toward-from-readings), RE-SCALED (gate 1 of the redesign). A person-bound
    reading raises what THAT person has earned and nobody else; a concept, an empty about, or the
    character themself adds nothing; the delta is the reading's own vector x the connection
    multiplier x the durability gate; the cap is gone; a replayed run carries it."""
    print("\n[9] fed by the seat's person-bound readings, scaled by bond and durability")
    from src.engine.records import Reading
    from src.engine import rungs, connection
    rs = [Reading(path="DISPLEASURE", rung="anger", about="cobb", confidence="likely"),
          Reading(path="GOODWILL", rung="fondness", about="daughter", confidence="likely"),
          Reading(path="WARINESS", rung="misgiving", about="concept:debt", confidence="likely"),
          Reading(path="DEFLATION", rung="sadness", about="", confidence="likely"),
          Reading(path="SELF-REGARD", rung="pride", about="ren", confidence="likely")]
    out = toward.observe_readings(rs, me="ren", durable=True)
    check("a-reading-about-cobb-goes-to-cobb", ("cobb", "DISPLEASURE") in {(w, p) for w, p, _ in out})
    check("a-reading-about-the-daughter-goes-to-her", ("daughter", "GOODWILL") in {(w, p) for w, p, _ in out})
    check("concept-empty-and-self-add-nothing", {w for w, _, _ in out} == {"cobb", "daughter"}, out)
    v = dict(((w, p), d) for w, p, d in out)
    anger = rungs.vector_for("DISPLEASURE", rungs.index_of("DISPLEASURE", "anger"))
    check("durable-and-a-stranger-is-the-bare-vector", abs(v[("cobb", "DISPLEASURE")] - anger) < 1e-12,
          "%s vs %s" % (v[("cobb", "DISPLEASURE")], anger))
    passing = toward.observe_readings(rs[:1], me="ren", durable=False)
    check("a-passing-beat-charges-a-fraction", abs(passing[0][2] - anger * toward._ATTITUDE_PASSING) < 1e-12,
          passing)
    close = {"relationships": {"cobb": {"trust": 0.9, "affinity": 0.9, "respect": 0.9, "debt": 0.5}}, "held": {}}
    bonded = toward.observe_readings(rs[:1], me="ren", profile=close, durable=True)
    c = connection.for_about(close["relationships"], {}, "cobb", "DISPLEASURE")
    check("a-bond-multiplies-like-the-receipt", c > 0 and abs(bonded[0][2] - anger * connection.magnitude_scale(c)) < 1e-12,
          "c=%s got=%s" % (c, bonded[0][2]))
    ch = {"current": {}}
    toward.replay(ch, [(w, p, d) for w, p, d in out])
    tw = ch["current"]["toward"]
    check("cobb-and-not-the-daughter-carries-the-anger",
          tw["cobb"].get("DISPLEASURE", 0) > 0 and "DISPLEASURE" not in tw["daughter"], tw)
    many = toward.observe_readings([Reading(path="DISPLEASURE", rung="anger", about="cobb", confidence="likely")] * 12,
                                   me="ren", durable=True)
    ch2 = {"current": {}}
    toward.replay(ch2, [(w, p, d) for w, p, d in many])
    check("twelve-durable-readings-pass-the-old-cap", ch2["current"]["toward"]["cobb"]["DISPLEASURE"] > 0.25,
          ch2["current"]["toward"])
    for bad in (Reading(path="DISPLEASURE", rung="not-a-rung", about="cobb", confidence="likely"),):
        try:
            toward.observe_readings([bad], me="ren")
            check("an-invented-rung-is-refused", False, "did NOT raise")
        except Exception as exc:                          # noqa: BLE001 — RungError or RecordError, by name
            check("an-invented-rung-is-refused", "RUNG" in str(exc).upper() or "rung" in str(exc), str(exc)[:80])


def test_the_actor_is_told_what_a_person_stirs():
    """The words reach the prompt; the number does not; a present person at zero says nothing."""
    print("\n[10] the actor is told what a present person stirs, in words")
    from src.engine.scene import assemble
    from src.engine.prompt import build_turn_messages
    from src.engine.direction import direct_stirs
    check("a-plain-stir-reads-plain", direct_stirs({"GOODWILL": 0.12}) == "you go soft near them")
    check("a-faint-stir-says-so", direct_stirs({"WARINESS": 0.05}).startswith("a little, "))
    check("under-the-floor-is-silence", direct_stirs({"WARINESS": 0.01}) == "")
    check("the-two-largest-only", direct_stirs({"GOODWILL": 0.12, "WARINESS": 0.11, "STIRRING": 0.10}).count(";") == 1)
    check("a-lowering-reads-as-a-lowering", "cold" in direct_stirs({"GOODWILL": -0.12}))
    check("no-digit-in-any-phrase", not any(c.isdigit() for pair in __import__("src.engine.direction", fromlist=["_STIRS_PHRASES"])._STIRS_PHRASES.values() for c in "".join(pair)))
    ch = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    # Joss is the one person Ren's fixture sheet knows, so "Joss is here" makes a PRESENT edge
    toward.replay(ch, [("joss_apprentice", "DISPLEASURE", 0.45)])   # above any fixture mood
    packet = assemble(ch, world, {"event": {"text": "Joss is here", "kind": "mundane"}, "target": "joss_apprentice"},
                      ch["current"]["affect"], ch["current"]["condition"])
    msgs = build_turn_messages(packet, "Joss is here", ch["baseline"]["temperament"], {})
    text = json.dumps(msgs)
    check("the-edge-carries-stirs", any(e.get("stirs") for e in packet["volatile"]["edges"]), str(packet["volatile"]["edges"])[:200])
    check("the-phrase-reaches-the-actor", "they get under your skin" in text)
    check("the-word-toward-still-does-not", "toward" not in text)
    ch0 = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    from src.engine import heritable as _her
    _her.ensure_temperament(ch0)
    # AT REST, with no attitude toward Joss, the composition is the identity and the line is silent.
    # (A mood ABOVE rest with a zero attitude is a cooler person met halfway down — and that is
    # said, by design: see [12].)
    at_rest = {p: float(ch0["baseline"]["temperament"][p]["mean"]) for p in PATHS}
    packet0 = assemble(ch0, world, {"event": {"text": "Joss is here", "kind": "mundane"}, "target": "joss_apprentice"},
                       at_rest, ch0["current"]["condition"])
    text0 = json.dumps(build_turn_messages(packet0, "Joss is here", ch0["baseline"]["temperament"], {}))
    from src.engine.direction import _STIRS_PHRASES
    _all = [ph for pair in _STIRS_PHRASES.values() for ph in pair]
    check("a-person-at-the-mood-says-nothing", not any(ph in text0 for ph in _all))


def test_two_feeds_one_row_per_key():
    """THE FIRST BEAT WITH BOTH FEEDS LIVE DIED AT COMMIT (2026-09-11). The event route priced
    GOODWILL toward one person (care_relevant, subject = that person) and the reading route priced
    GOODWILL toward the same person again (a protectiveness reading); `toward_deltas` is UNIQUE on (run, turn,
    perceiver, target, path), so append_turn rolled the whole turn back. The gate before this one
    tested each route alone. This test commits BOTH through a real Ledger: the raw pair must still
    refuse (the constraint is the guard), and `toward.coalesce` must turn it into one summed row that
    commits and replays to the sum."""
    print('\n[11] two feeds, one row per (perceiver, target, path) per turn')
    from src.engine.ledger import Ledger, LedgerError
    from src.engine.records import Event, TowardDelta, TurnCommit
    from src.engine import bible
    a = TowardDelta(perceiver="ren", target="cobb", primary="GOODWILL", delta=0.03, source="the act")
    b = TowardDelta(perceiver="ren", target="cobb", primary="GOODWILL", delta=0.09, source="the reading")
    c = TowardDelta(perceiver="ren", target="cobb", primary="WARINESS", delta=0.02, source="the act")
    d = TowardDelta(perceiver="ren", target="mara", primary="GOODWILL", delta=0.01, source="the act")
    out = toward.coalesce([a, b, c, d])
    check("one-row-per-key", len(out) == 3, out)
    check("same-key-summed", abs(out[0].delta - 0.12) < 1e-9 and out[0].target == "cobb" and out[0].primary == "GOODWILL", out[0])
    check("sources-joined", out[0].source == "the act | the reading", out[0].source)
    check("distinct-keys-kept", [(t.target, t.primary) for t in out[1:]] == [("cobb", "WARINESS"), ("mara", "GOODWILL")], out[1:])
    check("empty-is-empty", toward.coalesce([]) == [] and toward.coalesce(None) == [])

    led = Ledger(":memory:")
    world = {"world": "w", "switches": {}, "locations": [{"id": "yard", "what": "the yard"}],
             "people": [{"id": "ren", "name": "Ren"}, {"id": "cobb", "name": "Cobb"}]}
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1},
                         bible.CONFIG_KEY: bible.build(led.con, world, {})})

    def commit(turn, rows):
        led.append_turn(TurnCommit(
            run_id="r", turn=turn, actor="ren", thought="-", action="-", tags={}, validation={"ok": True},
            affect={p: 0.2 for p in PATHS}, condition={"energy": 0.7},
            events=[Event(type="care", payload={"text": "x"}, actor="ren")], toward_deltas=rows))

    try:
        commit(0, [a, b])
        check("raw-pair-refused", False, "the UNIQUE constraint let two rows through")
    except LedgerError as e:
        check("raw-pair-refused", e.code == "LEDGER_TURN_COMMIT_ROLLED_BACK", e)
    commit(1, toward.coalesce([a, b]))
    stored = led.toward_deltas_for("r", "ren")
    check("coalesced-commits", stored == [("cobb", "GOODWILL", 0.12)] or (
        len(stored) == 1 and stored[0][:2] == ("cobb", "GOODWILL") and abs(stored[0][2] - 0.12) < 1e-9), stored)
    ch = {"fixed": {"id": "ren"}, "baseline": {}, "current": {}}
    vec = toward.replay(ch, stored)
    check("replays-to-the-sum", abs(vec["cobb"]["GOODWILL"] - 0.12) < 1e-9, vec)


def test_the_balance():
    """THE OWNER'S COMPOSITION (2026-09-12), on the numbers. a >= m -> a; a < m -> midpoint(m,
    max(a, rest)). The owner's example: engaged with A at rung 6 -> mood there; turn to B whose
    attitude is rung 1 -> B is met at the midpoint. And a reserved crossword setter: rest `quiet`,
    attitude toward her oldest friend at tenderness -> tender with the friend, `quiet` with the editor."""
    print("\n[12] the balance: the owner's table, on GOODWILL floats")
    from src.engine import rungs
    def mid(p, k):
        lo, hi, _n = rungs.BANDS[p][k - 1]
        return (lo + hi) / 2.0
    g = "GOODWILL"
    m6, a1, rest = mid(g, 6), mid(g, 1), mid(g, 1)
    check("a-above-the-mood-is-played", abs(toward.compose(0.2, 0.5, 0.1) - 0.5) < 1e-12)
    check("a-cooler-person-is-met-halfway", abs(toward.compose(m6, a1, rest) - (m6 + a1) / 2.0) < 1e-12)
    check("never-below-rest", abs(toward.compose(m6, 0.0, rest) - (m6 + rest) / 2.0) < 1e-12)
    check("at-the-mood-is-the-mood", abs(toward.compose(0.3, 0.3, 0.1) - 0.3) < 1e-12)
    check("a-negative-attitude-floors-at-rest", abs(toward.compose(0.3, -0.2, 0.1) - 0.2) < 1e-12)
    # the setter
    quiet, tender = mid(g, 1), mid(g, 5)
    tw = {"friend": {g: tender}}
    mood = {p: 0.0 for p in PATHS}; mood[g] = quiet
    rest_v = {p: 0.0 for p in PATHS}; rest_v[g] = quiet
    with_friend, stirs, _ = toward.balance(mood, tw, rest_v, engaged="friend", present=["friend"], me="setter")
    with_editor, _, _ = toward.balance(mood, tw, rest_v, engaged="editor", present=["editor"], me="setter")
    check("tender-with-the-friend", rungs.rung_at(g, with_friend[g])[1] == "tenderness", rungs.rung_at(g, with_friend[g]))
    check("quiet-with-the-editor", rungs.rung_at(g, with_editor[g])[0] == 1, rungs.rung_at(g, with_editor[g]))
    check("the-friend-in-the-room-softens-her-toward-the-editor-damped",
          abs(toward.balance(mood, tw, rest_v, engaged="editor", present=["editor", "friend"], me="setter")[0][g]
              - max(quiet, toward._OTHERS_DAMP * tender)) < 1e-12)
    check("stirs-says-what-the-friend-moves-her-by", abs(stirs["friend"][g] - (tender - quiet)) < 1e-12, stirs)
    # THE WIDENED FALSIFICATION: same mood, engage B (earned) vs C (nothing) -> a HOTTER rung for B
    mood2 = {p: 0.0 for p in PATHS}; mood2[g] = mid(g, 3)
    tw2 = {"b": {g: mid(g, 6)}, "c": {}}
    eb, _, _ = toward.balance(mood2, tw2, rest_v, engaged="b", present=["b", "c"], me="x")
    ec, _, _ = toward.balance(mood2, tw2, rest_v, engaged="c", present=["b", "c"], me="x")
    check("a-beat-about-b-reads-hotter-than-one-about-c-on-the-same-mood",
          rungs.rung_at(g, eb[g])[0] > rungs.rung_at(g, ec[g])[0], "%s vs %s" % (rungs.rung_at(g, eb[g]), rungs.rung_at(g, ec[g])))
    # THE MOOD IS MET IN FULL BY THE PERSON IT IS ABOUT (the brief's example: with A the mood plays;
    # B is met halfway). Synthetic numbers: x's mood (0.61) was raised by readings about a; a's own
    # attitude (0.08) sits below x's rest (0.22).
    mood4 = {p: 0.1 for p in PATHS}; mood4[g] = 0.61
    rest4 = {p: 0.1 for p in PATHS}; rest4[g] = 0.22
    tw4 = {"a": {g: 0.08}}
    with_a, _, _ = toward.balance(mood4, tw4, rest4, engaged="a", present=["a"], me="x",
                                  targets={g: "a"})
    with_b4, _, _ = toward.balance(mood4, tw4, rest4, engaged="b", present=["b"], me="x",
                                   targets={g: "a"})
    check("the-one-the-mood-is-about-meets-it-in-full", abs(with_a[g] - 0.61) < 1e-12, with_a[g])
    check("anyone-else-is-met-halfway-down", abs(with_b4[g] - (0.61 + 0.22) / 2.0) < 1e-12, with_b4[g])
    unbound, _, _ = toward.balance(mood4, tw4, rest4, engaged="a", present=["a"], me="x", targets={})
    check("without-the-aboutness-the-formula-alone-halves-it", abs(unbound[g] - (0.61 + 0.22) / 2.0) < 1e-12, unbound[g])
    # nobody engaged, nobody present: the identity, comments and all
    mood3 = dict(mood2); mood3["_note"] = "kept"
    e3, s3, _ = toward.balance(mood3, tw2, rest_v, engaged=None, present=[], me="x")
    check("nobody-is-the-identity", all(abs(e3[p] - mood3[p]) < 1e-12 for p in PATHS) and e3.get("_note") == "kept" and s3 == {})


def test_whom_the_mood_came_from_is_read_off_the_log():
    """THE BALANCE'S ABOUTNESS COMES FROM THE LOG (2026-09-12). `current.targets` clears once a path is
    within _AT_REST of rest, which under the measured lambda is nearly always inside one scene — so on
    a live performance the very person who had raised the speaker's GOODWILL a little above rest was met
    halfway down and the actor was told "a little, they leave you cold". `ledger.raised_by` answers
    from the order of the readings, and the driver hands it to assemble in the slice."""
    print("\n[13] whom the mood came from is read off the log")
    from src.engine.ledger import Ledger
    from src.engine.records import Event, Reading, TurnCommit
    from src.engine.scene import assemble
    from src.engine.prompt import build_turn_messages
    from src.engine import bible
    led = Ledger(":memory:")
    world = {"world": "w", "switches": {}, "locations": [{"id": "yard", "what": "the yard"}],
             "people": [{"id": "ren", "name": "Ren"}, {"id": "cobb", "name": "Cobb"}]}
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1},
                         bible.CONFIG_KEY: bible.build(led.con, world, {})})
    def commit(turn, readings):
        led.append_turn(TurnCommit(
            run_id="r", turn=turn, actor="ren", thought="-", action="-", tags={}, validation={"ok": True},
            affect={p: 0.2 for p in PATHS}, condition={"energy": 0.7},
            events=[Event(type="care", payload={"text": "x"}, actor="ren")], readings=readings))
    commit(0, [Reading(path="GOODWILL", rung="fondness", about="cobb", confidence="likely"),
               Reading(path="WARINESS", rung="unease", about="concept:debt", confidence="likely")])
    commit(1, [Reading(path="GOODWILL", rung="warmth", about="", confidence="likely"),
               Reading(path="DEFLATION", rung="sadness", about="cobb", confidence="likely")])
    rb = led.raised_by("r", "ren")
    check("the-last-reading-per-path", rb == {"GOODWILL": "", "WARINESS": "concept:debt", "DEFLATION": "cobb"}, rb)
    check("nobody-else", led.raised_by("r", "cobb") == {})
    # the same shape on the real path: mood within _AT_REST of rest, raised by the engaged person
    ch = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    world2 = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    from src.engine import heritable as _her
    _her.ensure_temperament(ch)
    rest = float(ch["baseline"]["temperament"]["GOODWILL"]["mean"])
    mood = {p: float(ch["baseline"]["temperament"][p]["mean"]) for p in PATHS}
    mood["GOODWILL"] = rest + 0.08                        # raised a little, and not by a bind that survives
    toward.replay(ch, [("joss_apprentice", "GOODWILL", 0.02)])
    ch["current"]["targets"] = {}                          # rule 5 has cleared it, as it does near rest
    ch["baseline"].pop("catalog", None)                    # the fixture's buff rows are not the question here
    slice_ = {"event": {"text": "Joss is here", "kind": "mundane"}, "target": "joss_apprentice",
              "engaged": "joss_apprentice", "raised_by": {"GOODWILL": "joss_apprentice"}}
    packet = assemble(ch, world2, slice_, mood, ch["current"]["condition"])
    eff = packet["volatile"]["state"]["effective"]
    check("raised-by-them-they-meet-the-mood-in-full", abs(eff["GOODWILL"] - mood["GOODWILL"]) < 1e-12, eff["GOODWILL"])
    text = json.dumps(build_turn_messages(packet, "Joss is here", ch["baseline"]["temperament"], {}))
    check("and-nothing-cold-is-said", "leave you cold" not in text)
    slice_no = dict(slice_); slice_no.pop("raised_by")
    packet_no = assemble(ch, world2, slice_no, mood, ch["current"]["condition"])
    check("without-the-log-answer-they-are-met-halfway",
          abs(packet_no["volatile"]["state"]["effective"]["GOODWILL"] - (mood["GOODWILL"] + rest) / 2.0) < 1e-12)


def test_both_drivers_accrue_it():
    """THE DRIVERS MUST NOT DISAGREE. Both `scene.py` (a cast) and `direct.py` (one character) are
    first-class ways to drive the engine (CLAUDE.md Modes), they write to the SAME chronicle through
    the SAME append_turn, and a durable consequence must not depend on which one the operator chose.

    Wired into scene.py first and direct.py second, hours apart — during which the same beat
    produced different history depending on the driver. A source-shape check, in the same register
    as tests/test_map.py and tests/test_citations.py, because the alternative is running two live
    drivers in a unit test."""
    print('\n[8] both drivers accrue the micro tier')
    import io as _io
    for name in ("scene.py", "direct.py"):
        src = _io.open(os.path.join(REPO, "scripts", name), encoding="utf-8").read()
        check("%s-accrues-micro" % name, "toward.observe(" in src)
        check("%s-accrues-readings" % name, "toward.observe_readings(" in src)
        check("%s-coalesces-before-commit" % name, "toward.coalesce(toward_deltas)" in src)
        check("%s-scales-attitude-by-bond-and-durability" % name, "durable=_durable" in src and "profile=" in src)
        check("%s-commits-it" % name, "toward_deltas=toward_deltas" in src)
        check("%s-trials-wounds" % name, "wound.trial(" in src)
        # THE FOLD, since gate erosion-derived-at-replay (2026-09-22): `toward.replay` rebuilt from the
        # authored base plus the deltas and lost every opening's fade; tests/test_passage.py pins the two
        # equal wherever no gap was declared.
        check("%s-refolds-on-resume" % name, "fold_toward(led.con, run_id" in src)
    src = _io.open(os.path.join(REPO, "scripts", "scene.py"), encoding="utf-8").read()
    check("scene.py-says-who-is-engaged", '"engaged": (log[-1]["who"]' in src)
    for name in ("scene.py", "direct.py"):
        src = _io.open(os.path.join(REPO, "scripts", name), encoding="utf-8").read()
        check("%s-says-whom-the-mood-came-from" % name, "led.raised_by(run_id" in src)


def test_the_balance_reports_its_origin():
    """THE FUNCTION THAT KNOWS THE BRANCH REPORTS IT (2026-09-12, resolved with the peer; built
    2026-09-15). A composed value can sit on a plateau three ways and the number alone cannot say
    which; only the mood drains on the fast clock, so `rungs.descending` needs `origin` to know
    whether a come-down is real. One case per branch, and the equality hand-off."""
    print("\n[14] the balance reports which branch set each path")
    rest_v = {p: 0.10 for p in PATHS}
    mood = {p: 0.10 for p in PATHS}
    mood["DISPLEASURE"] = 0.60
    mood["STIRRING"] = 0.30
    tw = {"b": {"DISPLEASURE": 0.70, "STIRRING": 0.10},      # b has earned MORE anger than the mood; less stirring
          "c": {"DISPLEASURE": 0.10, "GOODWILL": 0.90}}     # c: cool on anger; a big GOODWILL attitude
    e, _, o = toward.balance(mood, tw, rest_v, engaged="b", present=["b", "c"], me="x")
    check("a>=m-is-attitude", o["DISPLEASURE"] == "attitude" and abs(e["DISPLEASURE"] - 0.70) < 1e-12, (o["DISPLEASURE"], e["DISPLEASURE"]))
    check("a<m-midpoint-is-mood", o["STIRRING"] == "mood" and abs(e["STIRRING"] - (0.30 + 0.10) / 2) < 1e-12, (o["STIRRING"], e["STIRRING"]))
    check("a-present-other-lifting-is-lift", o["GOODWILL"] == "lift" and abs(e["GOODWILL"] - toward._OTHERS_DAMP * 0.90) < 1e-12, (o["GOODWILL"], e["GOODWILL"]))
    check("untouched-paths-are-mood", all(o[p] == "mood" for p in PATHS if p not in ("DISPLEASURE", "GOODWILL")), o)
    check("every-path-has-an-origin", set(o) == set(PATHS))
    e0, _, o0 = toward.balance(mood, tw, rest_v, engaged=None, present=[], me="x")
    check("alone-is-the-identity-and-all-mood", e0 == {p: mood[p] for p in PATHS} and all(v == "mood" for v in o0.values()))
    # the raised-by rule: whom the mood came from meets it in full; the attitude holds it only when a >= m
    _, _, oa = toward.balance(mood, {"b": {"DISPLEASURE": 0.60}}, rest_v, engaged="b", present=["b"], me="x", targets={"DISPLEASURE": "b"})
    check("raised-by-at-equality-is-attitude", oa["DISPLEASURE"] == "attitude", oa["DISPLEASURE"])
    _, _, ob = toward.balance(mood, {"b": {"DISPLEASURE": 0.20}}, rest_v, engaged="b", present=["b"], me="x", targets={"DISPLEASURE": "b"})
    check("raised-by-below-the-mood-is-mood", ob["DISPLEASURE"] == "mood", ob["DISPLEASURE"])
    check("attitude-passing-is-the-measured-half", toward._ATTITUDE_PASSING == 0.5, toward._ATTITUDE_PASSING)


def test_the_descent_signal_is_read_off_the_log():
    """THE FUEL COMES FROM THE LOG (2026-09-15, gate 3 wiring). `ledger.last_read_turn` and
    `ledger.last_turn` are the two readers; the drivers hand them to `assemble` in the slice beside
    `raised_by`, and `assemble` stores `state.descending` from the MOOD, the balance's origin and
    those two — the flag `rung_direction` hands to `composer.selectable`. The falsification in
    miniature: descent on the SECOND own beat with no reading on the path, never earlier."""
    print("\n[15] the descent signal is read off the log")
    from src.engine.ledger import Ledger
    from src.engine.records import Event, Reading, TurnCommit
    from src.engine.scene import assemble
    from src.engine import bible, rungs
    led = Ledger(":memory:")
    world = {"world": "w", "switches": {}, "locations": [{"id": "yard", "what": "the yard"}],
             "people": [{"id": "ren", "name": "Ren"}, {"id": "cobb", "name": "Cobb"}]}
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1},
                         bible.CONFIG_KEY: bible.build(led.con, world, {})})
    def commit(turn, actor, readings):
        led.append_turn(TurnCommit(
            run_id="r", turn=turn, actor=actor, thought="-", action="-", tags={}, validation={"ok": True},
            affect={p: 0.2 for p in PATHS}, condition={"energy": 0.7},
            events=[Event(type="care", payload={"text": "x"}, actor=actor)], readings=readings))
    check("before-any-beat-last_turn-is-None", led.last_turn("r", "ren") is None)
    check("before-any-beat-nothing-was-read", led.last_read_turn("r", "ren") == {})
    commit(0, "ren", [Reading(path="DISPLEASURE", rung="fury", about="cobb", confidence="likely")])
    commit(1, "cobb", [Reading(path="DISPLEASURE", rung="anger", about="ren", confidence="likely")])
    commit(2, "ren", [Reading(path="WARINESS", rung="unease", about="", confidence="likely")])
    commit(3, "cobb", [])
    check("last_turn-is-per-actor", led.last_turn("r", "ren") == 2 and led.last_turn("r", "cobb") == 3)
    lrt = led.last_read_turn("r", "ren")
    check("last_read_turn-is-the-max-turn-per-path", lrt == {"DISPLEASURE": 0, "WARINESS": 2}, lrt)
    check("...and-per-actor", led.last_read_turn("r", "cobb") == {"DISPLEASURE": 1})
    # through assemble: Ren's DISPLEASURE mood one rung above the pivot, set by the mood, nobody engaged
    ch = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    world2 = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    from src.engine import heritable as _her
    _her.ensure_temperament(ch)
    ch["baseline"].pop("catalog", None)
    ch["current"]["toward"] = {}
    piv = rungs.PIVOTS["DISPLEASURE"]
    mood = {p: float(ch["baseline"]["temperament"][p]["mean"]) for p in PATHS}
    mood["DISPLEASURE"] = rungs.BANDS["DISPLEASURE"][piv][0] + 1e-6           # one rung above anger
    base = {"event": {"text": "the yard is quiet", "kind": "mundane"}}
    # 1. his last own beat (turn 2) carried no DISPLEASURE reading; DISPLEASURE was last read at turn 0
    sl = dict(base, last_read_turn=led.last_read_turn("r", "ren"), last_turn=led.last_turn("r", "ren"))
    pk = assemble(ch, world2, sl, mood, ch["current"]["condition"])
    d = pk["volatile"]["state"]["descending"]
    check("no-fuel-at-the-last-beat-above-the-pivot-descends", d.get("DISPLEASURE") is True, d)
    check("the-other-paths-at-rest-do-not", all(not v for p, v in d.items() if p != "DISPLEASURE"), d)
    # 2. a reading on the path at his last own beat is fuel: the climb, even above the pivot
    commit(4, "ren", [Reading(path="DISPLEASURE", rung="outrage", about="cobb", confidence="likely")])
    sl2 = dict(base, last_read_turn=led.last_read_turn("r", "ren"), last_turn=led.last_turn("r", "ren"))
    d2 = assemble(ch, world2, sl2, mood, ch["current"]["condition"])["volatile"]["state"]["descending"]
    check("fuel-at-the-last-beat-keeps-the-climb", d2.get("DISPLEASURE") is False, d2)
    # 3. THE +1-OWN-BEAT LAG. d2 above IS beat 6's composition: turn 4 carried the reading, so beat 6
    #    (the first own beat where fuel stops) still climbs. Beat 8 — the SECOND own beat with no
    #    reading — is composed after 6 committed unread: last_turn 6, last read 4 -> the descent.
    commit(5, "cobb", [])
    commit(6, "ren", [])                                                        # fuel stops here
    sl3 = dict(base, last_read_turn=led.last_read_turn("r", "ren"), last_turn=led.last_turn("r", "ren"))
    d3 = assemble(ch, world2, sl3, mood, ch["current"]["condition"])["volatile"]["state"]["descending"]
    check("the-second-own-beat-without-a-reading-descends", d3.get("DISPLEASURE") is True, d3)
    # 4. a slice with no log behind it (tests, --fixture) carries the key and reads no fuel
    d4 = assemble(ch, world2, dict(base), mood, ch["current"]["condition"])["volatile"]["state"]["descending"]
    check("no-log-no-fuel-above-the-pivot-descends", d4.get("DISPLEASURE") is True, d4)
    # 5. a plateau held by the engaged person's attitude is not a come-down
    ch["current"]["toward"] = {"joss_apprentice": {"DISPLEASURE": mood["DISPLEASURE"] + 0.05}}
    sl5 = dict(sl, engaged="joss_apprentice")
    pk5 = assemble(ch, world2, sl5, mood, ch["current"]["condition"])
    check("an-attitude-held-plateau-keeps-the-climb", pk5["volatile"]["state"]["descending"].get("DISPLEASURE") is False)
    # 6. the flag reaches the rung seam: direct.rung_direction hands state.descending to selectable
    import io as _io
    src = _io.open(os.path.join(REPO, "scripts", "direct.py"), encoding="utf-8").read()
    check("rung_direction-passes-descending", 'descending=vs.get("descending")' in src)
    for name in ("scene.py", "direct.py"):
        src = _io.open(os.path.join(REPO, "scripts", name), encoding="utf-8").read()
        check("%s-hands-last_read_turn-and-last_turn" % name, "led.last_read_turn(run_id" in src and "led.last_turn(run_id" in src)


def test_the_attitude_staircase():
    """TWO TABLES, ONE SHAPE (gate `attitude-staircase`, 2026-09-19). Attitude stops decaying at one
    flat rate per path per DAY and steps the path's ladder in MINUTES, exactly as the mood tier does
    (`state.decay_over`), at a slower per-path scale.

    THE ANCHOR IS THE WHOLE ARGUMENT FOR THE SCALE and is asserted, not asserted-about: rung 1's
    half-life is `MINUTES_PER_DAY * ln(0.5) / ln(_RETENTION[path])`, so a bottom-rung attitude over
    1440 minutes is what `relax(v, 0, _RETENTION[path], 1.0)` gave before this gate — to 1e-9, for
    every path. Nothing re-measured the day rates; they are UNMEASURED and carried over, and this
    equality is what lets them be carried at all. The rung-to-rung RATIO is read off the mood
    staircase rather than re-chosen, so the two tiers cannot drift apart: that is asserted against
    `state._rung_half_life` directly, not against a copy of its numbers.
    """
    print("\n[16] the attitude staircase — per rung, in minutes, anchored at the bottom")
    import math
    from src.engine.clock import MINUTES_PER_DAY
    ret = toward._RETENTION

    # --- the derivation, both clauses, against their own sources ------------------------------
    bad = [p for p in ret
           if abs(toward._attitude_half_life(p, 1)
                  - MINUTES_PER_DAY * math.log(0.5) / math.log(ret[p])) > 1e-9]
    check("rung-1-IS-the-old-day-rate-converted-to-a-half-life", not bad, bad)
    off = [(p, k) for p in ret for k in range(1, len(BANDS[p]) + 1)
           if abs(toward._attitude_half_life(p, k) / toward._attitude_half_life(p, 1)
                  - _rung_half_life(p, k) / _rung_half_life(p, 1)) > 1e-12]
    check("every-other-rung-is-the-MOOD-staircase's-own-ratio", not off, off[:3])

    # --- the anchor invariant: a bottom-rung attitude over a day is what a flat day gave -------
    drift = []
    for p in sorted(ret):
        v = _mid(p, 1)
        got, want = _eroded(p, v, _DAY), relax(v, 0.0, ret[p], 1.0)
        if got is None or abs(got - want) > 1e-9:
            drift.append((p, got, want))
    check("a-bottom-rung-attitude-over-1440-min-EQUALS-the-old-flat-day", not drift, drift[:3])

    # --- the staircase bites: the top of DISPLEASURE cannot be held the way the bottom is ------
    top, bot = len(BANDS["DISPLEASURE"]), 1
    hi_v, lo_v = _mid("DISPLEASURE", top), _mid("DISPLEASURE", bot)
    hi_lost = (hi_v - _eroded("DISPLEASURE", hi_v, _DAY)) / hi_v
    lo_lost = (lo_v - _eroded("DISPLEASURE", lo_v, _DAY)) / lo_v
    check("DISPLEASURE's-top-rung-loses-MORE-over-a-day-than-its-bottom", hi_lost > lo_lost,
          "top lost %.4f of itself, bottom %.4f" % (hi_lost, lo_lost))
    check("...and-the-top's-half-life-is-the-SHORTER-one",
          toward._attitude_half_life("DISPLEASURE", top) < toward._attitude_half_life("DISPLEASURE", bot))

    # --- the sign is the person's; time only takes the magnitude down -------------------------
    neg = _eroded("GOODWILL", -0.30, _DAY)
    pos = _eroded("GOODWILL", 0.30, _DAY)
    check("a-NEGATIVE-attitude-stays-negative", neg < 0.0, neg)
    check("...and-decays-by-the-same-magnitude-as-its-mirror", abs(neg + pos) < 1e-12, (neg, pos))
    check("...toward-zero-not-through-it", neg > -0.30, neg)

    # --- connection slows EVERY rung, not just the one the old flat rate had ------------------
    unslowed = [(p, k) for p in sorted(ret) for k in range(1, len(BANDS[p]) + 1)
                if not _eroded(p, _mid(p, k), _DAY, c=1.0) > _eroded(p, _mid(p, k), _DAY)]
    check("connection-c=1.0-slows-every-rung-of-every-path", not unslowed, unslowed[:3])

    # --- the ordering is _RETENTION's, DERIVED from it rather than re-typed -------------------
    order = sorted(ret, key=lambda p: ret[p])            # the fastest-forgetting day rate first
    hls = [toward._attitude_half_life(p, 1) for p in order]
    check("bottom-rung-half-lives-rank-exactly-as-_RETENTION-does", hls == sorted(hls),
          list(zip(order, ["%.0f" % h for h in hls])))
    check("WARINESS-fades-fastest-and-DEFLATION-slowest",
          order[0] == "WARINESS" and order[-1] == "DEFLATION", order)

    # --- the two identities the tier has always had, on the new clock -------------------------
    still = {"current": {"toward": {"j": {"DISPLEASURE": 0.5, "GOODWILL": -0.2}}}}
    toward.erode(still, 0)
    check("minutes-0-leaves-the-vector-EXACTLY-as-it-was",
          still["current"]["toward"]["j"] == {"DISPLEASURE": 0.5, "GOODWILL": -0.2},
          still["current"]["toward"])
    check("a-magnitude-under-1e-9-is-DROPPED", _eroded("GOODWILL", 1e-12, _DAY) is None)
    check("...and-so-is-one-that-falls-under-it", _eroded("WARINESS", 1e-8, 400 * _DAY) is None)


def test_three_present_the_lift_is_the_max_not_the_sum():
    """[N] THREE PRESENT — the lift is the max across others, not the sum (gate emotion-tier-tidy,
    2026-09-19). `balance`'s own docstring: present others "may LIFT a path to `_OTHERS_DAMP` x
    their attitude, never lower one — a floor, not a sum, so no double count re-enters here." Every
    `present=` elsewhere in this suite carries at most ONE other besides the engaged person, so with
    only one other, "the max across others" and "the sum across others" are the same number and the
    claim was never actually exercised. Three present — engaged with one, two more merely in the
    room with DIFFERENT attitudes on the same path — is the first case where max and sum diverge."""
    print("\n[17] THREE PRESENT — the lift is the max across others, not the sum")
    g = "GOODWILL"
    # Mood and rest both ZERO on this path so the pre-lift value going into the others-loop is
    # exactly 0.0 — the point where "the floor" (max) and "mood + the lift" read as the same
    # number, so the assertion below can be written the way the claim is stated and still be
    # exactly what `balance` computes, not an approximation of it.
    mood = {p: 0.0 for p in PATHS}
    rest_v = {p: 0.0 for p in PATHS}
    tw = {"b": {g: 0.5}, "c": {g: 0.9}}           # "a" carries no attitude at all -> 0.0 every path
    eff, _stirs, origin = toward.balance(mood, tw, rest_v, engaged="a", present=["a", "b", "c"], me="x")
    lifted_max = mood[g] + toward._OTHERS_DAMP * max(tw["b"][g], tw["c"][g])
    lifted_sum = mood[g] + toward._OTHERS_DAMP * (tw["b"][g] + tw["c"][g])
    check("the-lift-is-mood-plus-the-damped-MAX-across-others",
          abs(eff[g] - lifted_max) < 1e-12, (eff[g], lifted_max))
    check("...and-specifically-NOT-mood-plus-the-damped-SUM",
          abs(eff[g] - lifted_sum) > 1e-6, (eff[g], lifted_sum))
    check("the-branch-that-set-it-is-reported-as-lift", origin[g] == "lift", origin[g])


def main():
    print("test_toward.py - the MICRO tier")
    for t in sorted((v for k, v in globals().items() if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
