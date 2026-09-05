#!/usr/bin/env python3
"""test_wound.py — the wound tier's MOVER (src/engine/wound.py).

What this pins, and why each matters:

  1. THE LAW. The intensity IS the prediction, so the signal is `observed - intensity`. Walking
     into the thing and finding it survivable is what eases a scar; being hurt there again is what
     deepens it. Both directions from ONE rule, not two branches with separate stories.
  2. THE PERCEPTION WALL. A wound moves only on what its owner PERCEIVED. `levers._row_active`
     matches raw ground-truth text and this deliberately does not copy that.
  3. THE ASYMMETRY. Deepening is faster than easing, so a chapter of progress can go in a night.
  4. RESILIENCE IS A GAIN, NEVER A THRESHOLD. Nothing switches at a boundary; the depleted are
     marked harder and consolidate less, continuously.
  5. THE FLOOR STOPS AN EASE AND MUST NOT CAUSE A DEEPENING. A single clamp into [floor, 1.0] looks
     right and is not — found by walking an arc, not by reading the line.
  6. THE ARC READS. A book-length sequence produces a curve a reader would believe.

Stdlib only, script-style, exit 0 = all pass.
"""
import copy
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import wound                                   # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def W(**kw):
    base = {"id": "w", "wound": "the bite that blinded him", "intensity": 0.95,
            "trigger": ["spider", "web", "something moving in the dark above"]}
    base.update(kw)
    return base


# PRODUCTION-SHAPED, not prose-shaped. These are what `gate.perceived_surfaces` returns: the raw
# attribute strings a percept carries. An earlier version of this fixture was a list of tidy
# phrases I invented, which is exactly how the phrase-trigger defect hid — the test agreed with my
# idea of the input instead of with the thing that produces it.
SEEN = ["a spider on the sill", "lamplight over the ledger"]


def test_the_error_term_is_the_whole_rule():
    print("\n[1] observed minus intensity, both directions from one rule")
    w = W()
    check("worse-than-feared-deepens", wound.trial(w, {"threat": 0.99}, 0.5, SEEN) > 0)
    check("better-than-feared-eases", wound.trial(w, {"threat": 0.10}, 0.5, SEEN) < 0)
    check("exactly-as-feared-does-nothing",
          wound.trial(W(intensity=0.40), {"threat": 0.40}, 0.5, SEEN) == 0.0)
    # self-limiting: as the wound falls toward what the world delivers, each trial pays less
    big = abs(wound.trial(W(intensity=0.95), {"threat": 0.10}, 0.5, SEEN))
    small = abs(wound.trial(W(intensity=0.30), {"threat": 0.10}, 0.5, SEEN))
    check("diminishing-returns-are-arithmetic", big > small, "%.4f then %.4f" % (big, small))


def test_the_perception_wall():
    print("\n[2] a wound moves only on what its owner perceived")
    w = W()
    check("no-cue-no-trial", wound.trial(w, {"threat": 0.99}, 0.5, ["a wolf", "frost"]) == 0.0)
    check("empty-percepts-no-trial", wound.trial(w, {"threat": 0.99}, 0.5, []) == 0.0)
    # the sharp case: the WORLD had a spider, the character did not see it
    check("unperceived-cue-does-not-move-it",
          wound.trial(w, {"threat": 0.99}, 0.5, ["lamplight", "the loft ladder"]) == 0.0)
    check("cue-without-a-relevant-dimension", wound.trial(w, {"loss": 0.99}, 0.5, SEEN) == 0.0)
    # WORD BOUNDARIES, not substrings — a scar going off on a coincidence inside a longer word is
    # a wound firing at random. Measured: 'web' does NOT match 'cobwebbed', 'spider' does NOT match
    # 'spiderling', and 'web' DOES match 'a web across the door'.
    # (A first draft of these three carried `or True` and could not fail — the same
    # fired-check-that-reports-clean defect this suite exists to catch elsewhere.)
    check("does-not-fire-inside-a-longer-word",
          wound.trial(W(trigger=["web"]), {"threat": 0.99}, 0.5, ["cobwebbed rafters and dust"]) == 0.0)
    check("does-not-fire-on-a-derived-word",
          wound.trial(W(trigger=["spider"]), {"threat": 0.99}, 0.5, ["a spiderling on the wall"]) == 0.0)
    check("does-fire-on-the-real-word",
          wound.trial(W(trigger=["web"]), {"threat": 0.99}, 0.5, ["a web across the door"]) != 0.0)
    check("a-different-word-entirely-does-not-fire",
          wound.trial(W(trigger=["web"]), {"threat": 0.99}, 0.5, ["a wolf on the road"]) == 0.0)


def test_deepening_outruns_easing():
    print("\n[3] the asymmetry — a night can undo a chapter")
    w = W(intensity=0.50)
    up = wound.trial(w, {"threat": 0.90}, 0.5, SEEN)          # error +0.40
    down = wound.trial(w, {"threat": 0.10}, 0.5, SEEN)        # error -0.40, same magnitude
    check("same-error-deepens-more-than-it-eases", up > abs(down), "+%.4f vs %.4f" % (up, down))
    check("ratio-is-the-negativity-bias", abs(up / abs(down) - (0.30 / 0.12)) < 1e-9,
          "%.4f" % (up / abs(down)))


def test_resilience_is_a_gain_not_a_threshold():
    print("\n[4] resilience scales, nothing switches")
    w = W()
    hurt_low = wound.trial(w, {"threat": 0.99}, 0.20, SEEN)
    hurt_high = wound.trial(w, {"threat": 0.99}, 0.80, SEEN)
    check("depleted-is-marked-harder", hurt_low > hurt_high, "%.4f vs %.4f" % (hurt_low, hurt_high))
    heal_low = wound.trial(w, {"threat": 0.05}, 0.20, SEEN)
    heal_high = wound.trial(w, {"threat": 0.05}, 0.80, SEEN)
    check("resourced-consolidates-more", heal_high < heal_low, "%.4f vs %.4f" % (heal_high, heal_low))
    # CONTINUITY: no boundary anywhere. arc.assess forks at 0.70; this must not.
    vals = [wound.trial(w, {"threat": 0.99}, r / 100.0, SEEN) for r in range(60, 81)]
    gaps = [abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
    check("no-cliff-across-the-arc-fork-value", max(gaps) < 1e-3, "largest step %.6f" % max(gaps))


def test_the_floor_stops_an_ease_and_never_causes_a_deepening():
    print("\n[5] the floor — the bug a single clamp would have shipped")
    unhealable = W(permanence=1.0)
    check("permanence-1-holds-against-a-good-night",
          wound.trial(unhealable, {"threat": 0.05}, 0.9, SEEN) == 0.0,
          str(wound.trial(unhealable, {"threat": 0.05}, 0.9, SEEN)))
    check("permanence-1-still-deepens",
          wound.trial(unhealable, {"threat": 0.99}, 0.3, SEEN) > 0)
    # ASYMPTOTIC, not a single step. One trial from 0.20 moves -0.0216; the floor is what it
    # approaches and never passes, which is the property worth asserting. (A first draft of this
    # test expected one trial to land exactly on the floor and failed against correct code.)
    w = W(intensity=0.20)
    for _ in range(200):
        w["intensity"] += wound.trial(w, {"threat": 0.0}, 0.9, SEEN)
    check("ease-approaches-the-floor", abs(w["intensity"] - 0.15) < 1e-6, "%.8f" % w["intensity"])
    check("and-never-passes-it", w["intensity"] >= 0.15, "%.8f" % w["intensity"])
    check("already-below-the-floor-does-not-move",
          wound.trial(W(intensity=0.10), {"threat": 0.0}, 0.9, SEEN) == 0.0)
    v = W(intensity=0.20, permanence=0.0)
    for _ in range(200):
        v["intensity"] += wound.trial(v, {"threat": 0.0}, 0.9, SEEN)
    check("a-wound-can-be-authored-to-vanish", v["intensity"] < 1e-6, "%.8f" % v["intensity"])


def test_erosion_is_the_weak_second_rule():
    print("\n[6] time, with nothing firing")
    w = W(intensity=0.85)
    check("no-elapsed-no-change", wound.erode(w, 0) == 0.0)
    slow = wound.erode(w, 1)
    fast = wound.erode(w, 30)
    check("erosion-is-negative", slow < 0 and fast < 0, "%.6f / %.6f" % (slow, fast))
    check("more-time-erodes-more", fast < slow)
    check("erosion-is-far-weaker-than-a-trial",
          abs(slow) < abs(wound.trial(w, {"threat": 0.1}, 0.5, SEEN)) / 10.0,
          "one unit of time %.6f vs one trial" % slow)
    check("erosion-stops-at-the-floor",
          abs(wound.erode(W(intensity=0.15), 1000)) < 1e-9)
    check("an-unhealable-wound-does-not-erode",
          wound.erode(W(intensity=0.95, permanence=1.0), 1000) == 0.0)


def test_the_arc_a_reader_would_believe():
    print("\n[7] a book-length arc")
    w = W()
    for _ in range(14):                       # fourteen walked-into encounters, all survivable
        w["intensity"] += wound.trial(w, {"threat": 0.10}, 0.55, SEEN)
    check("it-takes-you-over-becomes-it-catches-you-sometimes",
          0.25 < w["intensity"] < 0.55, "%.4f after 14 trials" % w["intensity"])
    before = w["intensity"]
    w["intensity"] += wound.trial(w, {"threat": 0.90}, 0.35, SEEN)   # one bad night, depleted
    check("one-bad-night-costs-several-good-ones", w["intensity"] - before > 0.05,
          "+%.4f" % (w["intensity"] - before))
    check("but-does-not-undo-the-whole-book", w["intensity"] < 0.95)


def test_fail_loud():
    print("\n[8] fail loud, never a silent no-op")
    for bad, why in (({"id": "w", "trigger": ["spider"]}, "no intensity"),
                     ("not a dict", "not a dict")):
        try:
            wound.trial(bad, {"threat": 0.5}, 0.5, SEEN)
            check("raises-on-%s" % why, False, "returned instead of raising")
        except ValueError:
            check("raises-on-%s" % why, True)
    try:
        wound.trial(W(permanence="forever"), {"threat": 0.1}, 0.5, SEEN)
        check("raises-on-prose-permanence", False, "returned instead of raising")
    except ValueError as e:
        check("raises-on-prose-permanence", "permanence" in str(e), str(e)[:70])


def test_an_authored_phrase_fires():
    """THE DEFECT THIS CLOSED. `docs/authoring/BLUEPRINT-character.md` instructs authors to write
    triggers as "2-4 short phrases, in the words a scene would actually use". The matcher was handed
    the RECALL GATE's shredded word bag, which drops connectives and anything under three
    characters — so an authored phrase could never be a substring of it, and a wound written exactly
    as documented was permanently inert. MEASURED on this repo's own fixture before the fix."""
    print('\n[9] an authored PHRASE fires on a real percept surface')
    from src.engine.gate import perceived_surfaces, extract_triggers
    percepts = [{"ref": "evt.1", "kind": "event",
                 "attributes": ["a child with fever tosses in the cot"]}]
    surfaces = perceived_surfaces(percepts)
    phrase_wound = W(trigger=["a child with fever"], intensity=0.85, class_dim="loss")
    check("the-phrase-fires-on-the-surface", wound.fires(phrase_wound, surfaces), str(surfaces))
    # and prove the OLD input shape would NOT have — or this test proves nothing
    check("the-shredded-bag-would-NOT-have",
          not wound.fires(phrase_wound, extract_triggers(percepts)),
          str(extract_triggers(percepts)))
    # no false positive across unrelated percepts: a phrase must be satisfied by ONE thing seen
    split = perceived_surfaces([{"attributes": ["a child at the door"]},
                                {"attributes": ["a fever in the valley"]}])
    check("a-phrase-does-not-match-across-two-percepts",
          not wound.fires(phrase_wound, split), str(split))
    # single-word triggers still work, and still respect word boundaries
    check("single-word-still-fires",
          wound.fires(W(trigger=["spider"]), perceived_surfaces([{"attributes": ["a spider drops"]}])))
    check("and-still-not-inside-a-longer-word",
          not wound.fires(W(trigger=["web"]), perceived_surfaces([{"attributes": ["cobwebbed rafters"]}])))


def main():
    print("test_wound.py - the wound tier's mover")
    for t in sorted((v for k, v in globals().items() if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
