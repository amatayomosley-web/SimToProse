#!/usr/bin/env python3
"""test_toward.py — the MICRO tier (src/engine/toward.py): what one specific person makes you feel.

`docs/character-model.md` "THE THREE LAYERS" records the author's model; this is its micro half.
The macro half moves who you are everywhere. This moves only what happens in one person's company.

What this pins:
  1. IT GOES BOTH WAYS. `_DIM_TO_PRIMARY` carries seven negative pushes, so a degrading act
     produces a NEGATIVE delta — the direction the arc cannot express at all (measured: a
     base-happy character through 80 durable diffs ended with FEAR saturated and PLAY, CARE, RAGE
     and DISGUST unchanged).
  2. IT IS PER PERSON. The same character, the same scene, a different person in the room -> a
     different effective vector. That is the whole point and nothing else in the engine does it.
  3. PRESENT **or** SUBJECT — you can be moved by someone who is not there.
  4. THE AUTHORED BASE SURVIVES (law 1), stamped before the first fold, never re-baselined.
  5. It never reaches the actor as a number.

Stdlib only, script-style, exit 0 = all pass.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import toward                                  # noqa: E402
from src.engine.levers import effective                        # noqa: E402
from src.engine.records import PRIMARIES                       # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def test_it_goes_both_ways():
    print("\n[1] a degrading act produces a NEGATIVE feeling — the direction the arc cannot express")
    v = toward.observe({"social_violation": 0.9})
    check("degradation-costs-play", v.get("PLAY", 0) < 0, str(v))
    check("degradation-raises-rage", v.get("RAGE", 0) > 0, str(v))
    check("degradation-raises-disgust", v.get("DISGUST", 0) > 0, str(v))
    w = toward.observe({"care_relevant": 0.9})
    check("kindness-raises-care", w.get("CARE", 0) > 0, str(w))
    check("nothing-from-an-empty-event", toward.observe({}) == {})
    # the SAME table the current tier uses — law 4, one pricing table at every timescale
    from src.engine.state import _DIM_TO_PRIMARY
    check("prices-with-the-shared-table",
          set(v) <= {p for _d, prs in _DIM_TO_PRIMARY.items() for p, _w in prs}, str(v))


def test_it_is_per_person():
    """THE POINT. Same character, same scene, different person -> different vector."""
    print("\n[2] the same room, a different person")
    ch = {"current": {}}
    toward.replay(ch, [("joss", "PLAY", -0.18), ("joss", "RAGE", 0.12),
                       ("nell", "PLAY", 0.15)])
    tw = ch["current"]["toward"]
    base = {p: 0.40 for p in PRIMARIES}
    with_joss = effective(base, toward.rows(tw, {"edges": {"joss": {}}, "target": None}))
    with_nell = effective(base, toward.rows(tw, {"edges": {"nell": {}}, "target": None}))
    alone = effective(base, toward.rows(tw, {"edges": {}, "target": None}))
    check("joss-costs-him-play", with_joss["PLAY"] < alone["PLAY"],
          "%.3f vs %.3f" % (with_joss["PLAY"], alone["PLAY"]))
    check("nell-gives-him-play", with_nell["PLAY"] > alone["PLAY"],
          "%.3f vs %.3f" % (with_nell["PLAY"], alone["PLAY"]))
    check("joss-raises-his-rage", with_joss["RAGE"] > alone["RAGE"])
    check("alone-is-the-identity", alone == base, str(alone))
    # and the two are genuinely different, which is the claim
    check("the-two-differ", with_joss["PLAY"] != with_nell["PLAY"])


def test_present_or_subject():
    print("\n[3] present, or what the moment is about")
    tw = {"nell": {"PLAY": 0.2}}
    check("present-fires", len(toward.rows(tw, {"edges": {"nell": {}}, "target": None})) == 1)
    check("subject-fires-though-absent",
          len(toward.rows(tw, {"edges": {}, "target": "nell"})) == 1)
    check("neither-is-silent", toward.rows(tw, {"edges": {"other": {}}, "target": "x"}) == [])
    check("no-vector-no-rows", toward.rows({}, {"edges": {"nell": {}}, "target": None}) == [])


def test_the_authored_base_survives():
    """LAW 1. An author may write a starting disposition; the fold must not eat it."""
    print("\n[4] the authored base survives")
    ch = {"current": {"toward": {"sister": {"RAGE": 0.10}}}}     # "she has always resented her"
    toward.replay(ch, [("sister", "RAGE", 0.08), ("sister", "CARE", -0.05)])
    cur = ch["current"]
    check("authored-preserved", cur["_authored_toward"]["sister"] == {"RAGE": 0.10},
          str(cur["_authored_toward"]))
    check("effective-is-base-plus-experience",
          abs(cur["toward"]["sister"]["RAGE"] - 0.18) < 1e-9, str(cur["toward"]))
    check("and-a-new-primary-lands", abs(cur["toward"]["sister"]["CARE"] + 0.05) < 1e-9,
          str(cur["toward"]))
    # re-folding must not re-baseline from the moved value
    toward.replay(ch, [("sister", "RAGE", 0.08), ("sister", "CARE", -0.05)])
    check("refold-keeps-the-ORIGINAL-authored",
          cur["_authored_toward"]["sister"] == {"RAGE": 0.10}, str(cur["_authored_toward"]))
    check("refold-is-not-cumulative", abs(cur["toward"]["sister"]["RAGE"] - 0.18) < 1e-9,
          "folding the same log twice must give the same answer: %s" % cur["toward"])


def test_the_fold_is_order_independent_and_bounded():
    print("\n[5] order-independent, and bounded")
    a, b = {"current": {}}, {"current": {}}
    toward.replay(a, [("x", "RAGE", 0.2), ("x", "RAGE", -0.15)])
    toward.replay(b, [("x", "RAGE", -0.15), ("x", "RAGE", 0.2)])
    check("order-does-not-matter", a["current"]["toward"] == b["current"]["toward"],
          "%s vs %s" % (a["current"]["toward"], b["current"]["toward"]))
    c = {"current": {}}
    toward.replay(c, [("x", "RAGE", 0.9)] * 20)
    check("clamped-at-the-band", abs(c["current"]["toward"]["x"]["RAGE"] - 0.25) < 1e-9,
          str(c["current"]["toward"]))
    d = {"current": {}}
    toward.replay(d, [("x", "PLAY", -0.9)] * 20)
    check("clamped-symmetrically", abs(d["current"]["toward"]["x"]["PLAY"] + 0.25) < 1e-9,
          str(d["current"]["toward"]))


def test_it_never_reaches_the_actor_as_a_number():
    """Tested on the REAL path. `_strip_notes` is NOT the guard here — it touches only the stable
    prefix, built from fixed+baseline. What protects `current` is that `assemble`'s volatile block
    selects its keys explicitly rather than dumping the dict."""
    print("\n[6] it does not reach the actor as a number")
    from src.engine.scene import assemble
    from src.engine.prompt import build_turn_messages
    ch = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    toward.replay(ch, [("marlo_clerk", "RAGE", 0.19), ("marlo_clerk", "PLAY", -0.21)])
    packet = assemble(ch, world, {"event": {"text": "the clerk is here", "kind": "mundane"},
                                  "target": "marlo_clerk"},
                      ch["current"]["affect"], ch["current"]["condition"])
    msgs = json.dumps(build_turn_messages(packet, "the clerk is here",
                                          ch["baseline"]["temperament"], {}))
    check("no-toward-key-in-the-prompt", "toward" not in msgs)
    check("no-authored-key-either", "_authored_toward" not in msgs)
    # and prove the vector DID reach the arithmetic, or this test proves nothing
    check("but-it-reached-the-effective-vector",
          any(r.get("toward") == "marlo_clerk" for r in packet["volatile"]["levers"]),
          str(packet["volatile"]["levers"]))


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
        check("%s-commits-it" % name, "toward_deltas=toward_deltas" in src)
        check("%s-trials-wounds" % name, "wound.trial(" in src)
        check("%s-refolds-on-resume" % name, "toward.replay(" in src)


def main():
    print("test_toward.py - the MICRO tier")
    for t in sorted((v for k, v in globals().items() if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
