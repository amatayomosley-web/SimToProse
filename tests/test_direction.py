#!/usr/bin/env python3
"""test_direction.py — gate-5 proof: numbers never reach the prompt (design.md guardrail).

Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.direction import direct_affect, direct_condition, direct_edge, sureness  # noqa: E402
from src.engine.records import PRIMARIES                                                 # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


def flat(v):
    return {p: v for p in PRIMARIES}


def temp(mean=0.5):
    return {p: {"mean": mean, "variability": 0.1} for p in PRIMARIES}


def test_no_digits_ever():
    """THE guardrail: across a sweep of vectors, no numeral appears in any output."""
    print("\n[1] DIGIT-FREE OUTPUT")
    maren_temp = json.load(open(os.path.join(REPO, "characters/maren-healer.json"), encoding="utf-8"))["baseline"]["temperament"]
    outs = []
    for v in (0.0, 0.13, 0.27, 0.42, 0.56, 0.71, 0.85, 0.99, 1.0):
        outs.append(direct_affect(flat(v), temp(0.5)))
        outs.append(direct_affect(flat(v), maren_temp))
        outs.append(direct_condition({"energy": v, "allostatic_load": 1.0 - v}))
        outs.append(direct_edge({"trust": v, "affinity": 1.0 - v, "respect": v, "debt": v}))
        outs.append(sureness(v))
    bad = [o for o in outs if re.search(r"\d", o)]
    check("no-numerals-in-any-direction", not bad, "leaked: %s" % bad[:3])


def test_monotone_bands():
    """Higher value -> strictly later band phrase for FEAR (monotone strength)."""
    print("\n[2] MONOTONE BANDS")
    t = temp(0.1)   # low mean so every level deviates -> always surfaces
    seen = []
    for v in (0.05, 0.4, 0.7, 0.95):
        line = direct_affect(dict(flat(0.1), FEAR=v), t)
        seen.append(line)
    check("fear-quiet-low", "settled" in seen[0] or "even-keeled" in seen[0], seen[0])
    check("fear-watchful-mid", "watchful" in seen[1], seen[1])
    check("fear-pressing-strong", "pressing" in seen[2], seen[2])
    check("fear-gripped-peak", "gripped" in seen[3], seen[3])


def test_deviation_markers():
    """A primary far above its mean reads 'more than is usual'; far below reads 'quieter'."""
    print("\n[3] DEVIATION MARKERS")
    t = temp(0.5)
    up = direct_affect(dict(flat(0.5), FEAR=0.9), t)
    down = direct_affect(dict(flat(0.5), CARE=0.1), t)
    check("rising-marker", "more than is usual" in up, up)
    check("settling-marker", "quieter than your usual" in down, down)
    # at-rest at an ANXIOUS baseline must NOT read as a spike (the anxious-baseline rule)
    anxious = {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES}
    anxious["FEAR"] = {"mean": 0.72, "variability": 0.1}
    at_rest = direct_affect(dict(flat(0.5), FEAR=0.72), anxious)
    check("anxious-baseline-not-a-spike", "more than is usual" not in at_rest, at_rest)


def test_condition_bands():
    print("\n[4] CONDITION BANDS")
    check("drained", "running on nothing" in direct_condition({"energy": 0.1, "allostatic_load": 0.9}))
    check("worn", "worn thin" in direct_condition({"energy": 0.5, "allostatic_load": 0.5}))
    check("rested", "rested and clear" in direct_condition({"energy": 0.95, "allostatic_load": 0.05}))


def test_edges_and_sureness():
    print("\n[5] EDGES + SURENESS")
    e = direct_edge({"trust": 0.9, "affinity": 0.6, "respect": 0.3, "debt": 0.05})
    check("edge-renders-all-axes", all(s in e for s in ("trust without reservation", "fond", "measured regard", "owes them nothing")), e)
    check("sureness-low", sureness(0.2) == "uncertain of it")
    check("sureness-high", sureness(0.95) == "knows it to the bone")


def test_fail_loud():
    print("\n[6] FAIL LOUD")
    for bad_call in (lambda: direct_affect({"FEAR": 0.5}, temp()),          # missing primaries
                     lambda: direct_affect(dict(flat(0.5), FEAR=1.5), temp()),
                     lambda: direct_condition({"energy": "high"}),
                     lambda: direct_edge({"trust": 2.0}),
                     lambda: sureness(-0.1)):
        try:
            bad_call()
            check("fail-loud", False, "malformed input accepted")
            return
        except ValueError:
            pass
    check("fail-loud-all-five", True)


def main():
    print("test_direction.py — gate 5 backstage guardrail\n")
    for t in (test_no_digits_ever, test_monotone_bands, test_deviation_markers,
              test_condition_bands, test_edges_and_sureness, test_fail_loud):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
