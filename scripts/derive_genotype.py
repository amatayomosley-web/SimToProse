"""derive_genotype.py — what the idle-floor bound admits, per path, at a STATED sensor rate.

A TOOL FOR THE TUNING LOOP, NOT THE SOURCE OF THE TABLES. Owner, 2026-09-10 evening: "we just
need a conservative decay rate and we will tune during testing" — the half-lives, lambda and the
`GAIN` / `PERSIST` presets in `heritable.py` are the adopted START and move on evidence from real
runs. What this script adds is the one coupling that is hard to see in a run: given the live
globals and a sensor false-positive rate `p` YOU state (it has never been measured; 0.2 is the
spec's placeholder), it finds, per path, the widest hit and hold under which an idle character
stays in their rest rung, and the lambda ceiling for a typical character. Read the output as
"if the appraiser misreads this often, these presets would drift", never as the answer. It writes
NOTHING.

THE ONE COUPLING IT SOLVES. Everything about the person is a separable multiplier except the idle
floor (`docs/emotion-arithmetic.md` section 3, "inherent nature"): a sensor that misreads a
resting character on a fraction `p` of idle beats adds `p * v(current rung) * g` a beat, and where
that settles against decay `r ** (1/hold)` decides whether the character stays in their own rest
rung or drifts up out of it with nothing happening. For each path and each rest rung under the
cap, this finds by bisection:

  g_max(path, rest, hold)   the largest hit that still idles inside the rest rung at p
  hold_max(path, rest, hit) the largest hold that still idles inside the rest rung at p

and reports the minimum over rests (the value that is safe for EVERY rest the draw can produce)
next to the current preset. A preset above its ceiling is the corner the balance test's ratchet
counts.

    python scripts/derive_genotype.py            # the table, at p = 0.20
    python scripts/derive_genotype.py --p 0.3    # a more pessimistic sensor
"""
import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import heritable as _her                      # noqa: E402
from src.engine import rungs                                  # noqa: E402
from src.engine.decay_law import relax                        # noqa: E402
from src.engine.records import PATHS                          # noqa: E402
from src.engine.state import retention_for, _HALF_LIFE         # noqa: E402

_SETTLE = 400
# The sweep's beat is a STATED PARAMETER, not an engine constant: the engine has no beat duration
# (owner: none unless authored). Thirty minutes is the beat the pre-clock WARINESS rate (0.72) implied; the ceilings scale with it.
_BEAT_MINUTES = 30.0


def _idle_floor(path, b, gain, hold, p):
    f = b
    for _ in range(_SETTLE):
        k = _her.rung_of_mean(path, f)
        r = retention_for(path, f, hold, _BEAT_MINUTES)          # the zone follows the float
        f = max(0.0, min(1.0, relax(f, b, r, 1.0) + p * rungs.vector_for(path, k) * gain))   # decay first (spec s8)
    return f


def _stays_home(path, b, gain, hold, p):
    return _her.rung_of_mean(path, _idle_floor(path, b, gain, hold, p)) == _her.rung_of_mean(path, b)


def _bisect(pred, lo, hi, steps=40):
    """Largest x in [lo, hi] with pred(x) true, assuming pred is monotone (true below, false above)."""
    if not pred(lo):
        return None
    if pred(hi):
        return hi
    for _ in range(steps):
        mid = (lo + hi) / 2.0
        if pred(mid):
            lo = mid
        else:
            hi = mid
    return lo


def lambda_ceiling(path, p):
    """The largest lambda on this path at which a TYPICAL character (rest quiet, hit 1, hold 1)
    still idles inside their rest rung at sensor bar p, sweep beat _BEAT_MINUTES. The global's
    ceiling, before any genotype cell is considered — spec section 9 decision 1 answered by
    measurement: under the minute clock lambda must be per path."""
    b = _her.rung_midpoint(path, 1)
    base = rungs.LAMBDA[path]

    def stays(lam):
        rungs.LAMBDA[path] = lam
        try:
            return _stays_home(path, b, 1.0, 1.0, p)
        finally:
            rungs.LAMBDA[path] = base
    return _bisect(stays, 0.0005, 0.5)


def ceilings(path, p):
    """-> {rest_word: (g_max at hold=typical, g_max at hold=lasting, hold_max at hit=high)}."""
    out = {}
    for i, rest in enumerate(_her.REST_WORDS[:_her.REST_CAP[path]]):
        b = _her.rung_midpoint(path, i + 1)
        g_typ = _bisect(lambda g: _stays_home(path, b, g, 1.0, p), 0.5, 2.5)
        g_last = _bisect(lambda g: _stays_home(path, b, g, _her.PERSIST["lasting"], p), 0.5, 2.5)
        h_high = _bisect(lambda h: _stays_home(path, b, _her.GAIN["high"], h, p), 0.5, 2.0)
        out[rest] = (g_typ, g_last, h_high)
    return out


def main():
    ap = argparse.ArgumentParser(description="derive the genotype's hit and hold ceilings from the globals")
    ap.add_argument("--p", type=float, default=0.20, help="the sensor's idle false-positive rate (spec bar 0.20)")
    args = ap.parse_args()
    p = args.p
    print("derive_genotype — ceilings that keep every rest rung home at p=%.2f" % p)
    print("  globals: lambda %s; half-lives (episode, disposition) minutes %s; sweep beat %.1f min" % (
        {k: v for k, v in rungs.LAMBDA.items()}, {k: v for k, v in _HALF_LIFE.items()}, _BEAT_MINUTES))
    print("  presets today: hit max %.2f (%s); hold max %.2f (%s)  [the adopted START; tuned in runs]"
          % (max(_her.GAIN.values()), max(_her.GAIN, key=_her.GAIN.get),
             max(_her.PERSIST.values()), max(_her.PERSIST, key=_her.PERSIST.get)))
    print()
    print("  THE GLOBAL FIRST — lambda ceiling per path for a typical character to idle in rung 1 at p=%.2f:" % p)
    for path in PATHS:
        lc = lambda_ceiling(path, p)
        print("    %-12s lambda <= %s   (today %.3f%s)" % (
            path, "none" if lc is None else "%.4f" % lc, rungs.LAMBDA[path],
            "" if lc is None or rungs.LAMBDA[path] <= lc else "  OVER"))
    print()
    print("  %-12s %-8s %-14s %-14s %-14s" % ("path", "rest", "g_max@hold=1", "g_max@lasting", "hold_max@high"))
    worst_g, worst_h = 9.0, 9.0
    for path in PATHS:
        for rest, (g_typ, g_last, h_high) in ceilings(path, p).items():
            fmt = lambda x: "  none " if x is None else "%.3f" % x
            flag = ""
            if g_last is not None and g_last < max(_her.GAIN.values()):
                flag += " hit-preset-over"
            if h_high is not None and h_high < max(_her.PERSIST.values()):
                flag += " hold-preset-over"
            print("  %-12s %-8s %-14s %-14s %-14s%s" % (path, rest, fmt(g_typ), fmt(g_last), fmt(h_high), flag))
            if g_last is not None:
                worst_g = min(worst_g, g_last)
            if h_high is not None:
                worst_h = min(worst_h, h_high)
    print()
    print("  SAFE FOR EVERY DRAWN REST: hit <= %.3f at lasting hold; hold <= %.3f at high hit" % (worst_g, worst_h))
    print("  Adopt by editing heritable.GAIN / heritable.PERSIST; tests/test_genotype_balance.py then guards it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
