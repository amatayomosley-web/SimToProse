"""test_basis_parser.py — the basis probe's answer parser, under a harness that actually runs it.

WHY THIS FILE EXISTS SEPARATELY. `basis_probe.py` carries `test__choice`, a pin over fourteen real
judge-reply shapes, written on 2026-08-23 as the regression guard for a scorer bug that had
contaminated every comparative number in the repo. The commit message presented it as the guard.
It has never executed: `tests/run_all.py` excludes `basis_probe.py` by name (`_PROBES`, because the
probe makes model calls), and nothing else calls it. A pin nobody runs is a comment.

The parse itself needs no model, so it belongs in a suite the verify block reaches. This file
imports the real function — it does not re-implement it, which would be the seventh hand-maintained
duplicate this project has found.

THE BUG IT GUARDS, so nobody re-introduces it while "simplifying":

    got = "ONE" if ("ONE" in r and "TWO" not in r) else ("TWO" if "TWO" in r else None)

A substring test over the whole reply, wrong in two directions at once. `ONE` is a substring of
NONE, DONE, ALONE and SOMEONE, so a refusal scored as an answer. And any reply that named its
choice before discussing the alternative INVERTED, because "ONE. Actor two is calmer" contains TWO
and fell through to the second branch — measured live, qwen2.5 answered "ONE\\n\\nThe description
provided does not actually differentiate..." and was recorded as TWO. A directional bias against
ONE, manufactured by the scorer, inside the control whose only job is detecting directional bias.
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

import basis_probe                                              # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def test_the_pin_runs():
    """Execute the pin that lives beside the function it guards."""
    print("\n[1] THE PIN — fourteen real reply shapes")
    try:
        n = basis_probe.test__choice()
        check("test__choice passes", True)
        print("       %d cases" % n)
    except AssertionError as e:
        check("test__choice passes", False, str(e))


def test_the_substring_bug_cannot_come_back():
    """The old rule and the current one must DISAGREE on the shapes that mattered.

    Stated as a difference rather than as expected values, so this stays a guard against the
    specific defect rather than a second copy of `_choice`'s behaviour.
    """
    print("\n[2] THE OLD RULE IS STILL WRONG — and the new one still differs from it")

    def substring_rule(reply):
        r = (reply or "").strip().upper()
        return "ONE" if ("ONE" in r and "TWO" not in r) else ("TWO" if "TWO" in r else None)

    inversions = ["ONE. Actor two is calmer.",
                  "ONE\n\nThe description provided does not actually differentiate between two actors."]
    refusals = ["none of them", "I am not done", "alone", "someone", "no one seems different"]

    for reply in inversions:
        old, new = substring_rule(reply), basis_probe._choice(reply)
        check("inversion-caught: %r" % reply[:26],
              old == "TWO" and new == "ONE", "old=%s new=%s" % (old, new))
    for reply in refusals:
        old, new = substring_rule(reply), basis_probe._choice(reply)
        check("refusal-not-an-answer: %r" % reply[:26],
              old == "ONE" and new is None, "old=%s new=%s" % (old, new))


def test_a_plain_answer_is_unaffected():
    """The fix must not have changed the ordinary case, or every prior number moves for a new reason."""
    print("\n[3] ORDINARY REPLIES — unchanged by the repair")
    for reply, want in (("ONE", "ONE"), ("TWO", "TWO"), ("one", "ONE"), ("Two.", "TWO"),
                        ("TWO, because one of them is louder", "TWO")):
        check("%r -> %s" % (reply, want), basis_probe._choice(reply) == want,
              basis_probe._choice(reply))


def test_the_floor_control_is_calibrated():
    """The bias floor's void criterion, checked as arithmetic rather than trusted as a number.

    Three forms of this control have now existed and the first two were unsound:

      "outside 2-10 of 12"   the floor emitted SIX rows, so `first` could never exceed 6 and the
                             excess-ONE arm was unreachable from the day it shipped. Half a
                             control — and the surviving half was an absolute count over a
                             denominator that shrinks every time a judge correctly refuses to
                             separate two identical renders.
      "[0.2, 0.8] rate"      written by me on 2026-08-23 as the repair, and no better: at n=6 it
                             voids on counts {0,1,5,6}, so FAIR judges void 21.9% of runs. A
                             control that fair coins fail one time in five is a dice roll.
      exact binomial         scales with however many answer, which is the property both lacked.

    That history is the reason this test states the false-void RATE and not just the band: a band
    looks reasonable at a glance, and both wrong ones did.
    """
    from math import comb
    print("")
    print("[4] THE FLOOR CONTROL — calibrated, not asserted")
    rej12 = [k for k in range(13) if basis_probe._binomial_rejects(k, 12)]
    check("n12-rejects-the-tails-only", rej12 == [0, 1, 2, 10, 11, 12], str(rej12))
    rate = sum(comb(12, k) for k in rej12) / 2.0 ** 12
    print("       fair-coin false-void at n=12: %.1f%%" % (100 * rate))
    check("fair-judges-rarely-void", rate <= 0.05, "%.3f" % rate)

    def old_rate(n):
        bad = [k for k in range(n + 1) if not (0.2 <= k / float(n) <= 0.8)]
        return sum(comb(n, k) for k in bad) / 2.0 ** n
    print("       the rate band I wrote first, at n=6:  %.1f%%" % (100 * old_rate(6)))
    check("and-beat-the-form-it-replaced", rate < old_rate(6), "%.3f vs %.3f" % (rate, old_rate(6)))

    check("a-lopsided-floor-still-voids", basis_probe._binomial_rejects(11, 12))
    check("an-even-split-does-not", not basis_probe._binomial_rejects(6, 12))
    check("too-few-answers-is-its-own-void", basis_probe._FLOOR_MIN_ANSWERS >= 4,
          basis_probe._FLOOR_MIN_ANSWERS)
    # The emitting loop itself, not a phrase that also appears in the header comment above it.
    src = io.open(os.path.join(REPO, "tests", "basis_probe.py"), encoding="utf-8").read()
    check("the-floor-asks-both-specs",
          'ask(judge, "BIASFLOOR", "ordinary", (same, same), spec["names"]' in src,
          "the floor still emits one spec's two asks — six rows, half a control")


def main():
    print("test_basis_parser.py — the probe's answer parser")
    for t in (test_the_pin_runs, test_the_substring_bug_cannot_come_back,
              test_a_plain_answer_is_unaffected, test_the_floor_control_is_calibrated):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
