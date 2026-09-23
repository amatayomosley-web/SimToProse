"""test_genotype_balance.py — the person system and the global system, checked against each other.

THE OWNER'S RULE, 2026-09-10: "genotype sets the person and their rates, then we see the global
rates. So we need to be sure that we can balance the 2 systems." Balance is SEPARABILITY: every
person term is a pure multiplier on a global term in units that mean the same thing on every path
(hit on the vector, hold on the half-life, rest a rung index). That much is by construction. The
one place the two systems COUPLE and cannot be factored is the idle floor
(`docs/emotion-arithmetic.md` section 3, "inherent nature"): a sensor that sometimes reads a
character at rest as feeling something adds `p * v * g` a beat, and where that settles against
decay depends on rest, hit and hold together. So this sweep runs the coupling over EVERY
combination the draw can produce and asserts an envelope — and it NAMES the path and the cells
when a combination leaves it, so a re-tuned lambda, a moved band, a new per-path law or a new
preset word cannot silently make one temperament unplayable.

Runs under run_all.py. Deterministic. No LLM. The globals and presets are the owner's
CONSERVATIVE START (2026-09-10: "we just need a conservative decay rate and we will tune during
testing"); this sweep guards what does not depend on a guess and REPORTS what does.

  E1  FLOOR STAYS HOME   INFORMATIONAL, never a check (owner, 2026-09-10 evening). It models a
                         sensor that misreads an idle character at rate p = 0.2 every 30-minute
                         beat — and BOTH of those are guesses: p has never been measured on the
                         appraiser, and a beat is as long as authored. Under those guesses 459 of
                         464 combinations drift out of their rest rung, which says how the guesses
                         interact, not what the engine does. It stays printed so that when p IS
                         measured in real runs the count is one edit from becoming a rule.
  E2  THE TOP IS REACHABLE  on every path, the STRONGEST combination (top rest, high hit,
                         lasting hold) reaches the top band under sustained top-rung readings
                         within `_REACH_MAX` beats. Per path, not per combination: whether the
                         top is reachable by someone is a property of lambda and the path's rate
                         (section 8 row 2 pins it for DISPLEASURE at g 1.3); which combinations
                         reach it is the design, not a defect.
  E3  NEVER ONE BEAT AWAY  no combination reaches the top band in fewer than `_REACH_MIN` beats;
                         section 8 row 1: a typical character takes seven beats to ENTER anger.
  E4  RANKS HOLD           after one reading and one beat, the value is strictly increasing in
                         hit and in hold on every path at every rest. Separability, observed —
                         at ONE beat, because under the minute clock a slow path fed a reading
                         every beat saturates at 1.0 and a clamp has no ranks (E1's finding).
"""
import itertools
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import heritable as _her                      # noqa: E402
from src.engine import rungs                                  # noqa: E402
from src.engine.decay_law import relax                        # noqa: E402
from src.engine.records import PATHS                          # noqa: E402
from src.engine.rung_blocks import BANDS                      # noqa: E402
from src.engine.state import retention_for, _HALF_LIFE         # noqa: E402

_FAILS = []

# ---- the envelope (STARTS; the owner sets these) ----
_P_IDLE = 0.20        # the sensor's false-positive rate on idle beats — section 8's bar
_REACH_MAX = 60       # beats of sustained top-rung readings within which the top must be reached
_REACH_MIN = 3        # ...and never fewer than this: section 8 row 1 enters anger at beat 7
_SETTLE = 400         # beats to let the idle floor converge
_BEAT_MINUTES = 10.0  # the sweep's beat — a TEST parameter; the engine has no beat duration (owner: none unless authored). MEASURED 2026-09-11: a ~300-word beat is a median 5 story-minutes on Red Badge and 10 on Holmes (readalong scene_clock); 10 is the longer of the two, so what is reachable here is reachable on both. Was 30 (what the pre-clock WARINESS rate implied) until the half-lives were measured.


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _combos(path):
    """Every (rest, hit, hold) the draw can produce on this path — word cells only."""
    rests = _her.REST_WORDS[:_her.REST_CAP[path]]
    return itertools.product(rests, tuple(_her.GAIN), tuple(_her.PERSIST))


def _params(path, rest, hit, hold):
    g = _her.typical(**{path: {"hit": hit, "hold": hold}})
    b = _her.rest_mean(path, _her.resting(**{path: rest}))     # the rest is design, not genotype
    gain = _her.hit(path, g)
    return b, gain, _her.hold(path, g)


def _rung_index(path, f):
    return rungs.rung_at(path, f)[0] if isinstance(rungs.rung_at(path, f), tuple) else _her.rung_of_mean(path, f)


# The CLIMB cadence (gate 2, 2026-09-12): reaching the top is a CONTINUOUS escalation, and the
# owner's rule is that a beat carries no authored duration unless the scene declares one, so within
# one escalation elapsed is 0 and decay does not fight the receipts. Per-rung decay (short at the
# top) leaves every ladder's top reachable continuously and at a 2-min beat; only a 10-min gap
# between readings makes the top unsustainable — which is the design ("the top cannot be sustained"),
# not an unreachability. The IDLE FLOOR below keeps the real `_BEAT_MINUTES`: it is a real-time
# saturation question, not a within-scene climb.
_CLIMB_BEAT_MINUTES = 0.0


def _beat(f, b, v, gain, hold, path, minutes=None):
    """One beat in the SPEC'S order: decay toward the rest FIRST, then the receipt `f += v*g`,
    then clamp. `docs/emotion-arithmetic.md` section 8 pins its rows "decay first" and row 12
    REJECTS vector-before-decay ("never entered anger at any lambda"). NOTE, recorded 2026-09-10:
    the live drivers run `decay(appraise(...))` — the rejected order — and under it no ladder's
    top band is reachable at all, because the clamp at 1.0 lands before the decay pulls back.
    That is Phase 3's receipt step to fix; this sweep models the arithmetic the spec specifies."""
    m = _BEAT_MINUTES if minutes is None else minutes
    r = retention_for(path, f, hold, m)                            # the rung follows the float
    return max(0.0, min(1.0, relax(f, b, r, 1.0) + v * gain))


def _idle_floor(path, b, gain, hold):
    """Expected-value idle floor: on every beat the sensor adds p * v(current rung) * g."""
    f = b
    for _ in range(_SETTLE):
        k = _her.rung_of_mean(path, f)
        f = _beat(f, b, _P_IDLE * rungs.vector_for(path, k), gain, hold, path)
    return f


def _beats_to_top(path, b, gain, hold):
    top = len(BANDS[path])
    v = rungs.vector_for(path, top)
    lo_top = float(BANDS[path][top - 1][0])
    f = b
    for n in range(1, _REACH_MAX + 1):
        f = _beat(f, b, v, gain, hold, path, _CLIMB_BEAT_MINUTES)
        if f >= lo_top:
            return n
    return None


def _settle_under(path, b, gain, hold, k):
    v = rungs.vector_for(path, k)
    f = b
    for _ in range(_SETTLE):
        f = _beat(f, b, v, gain, hold, path)
    return f


def test_E1_floor_stays_home():
    print("\n[E1] THE IDLE FLOOR — reported at a guessed p=%.2f; informational only" % _P_IDLE)
    bad = []
    for path in PATHS:
        cap = _her.REST_CAP[path]
        for rest, hit, hold in _combos(path):
            b, gain, hf = _params(path, rest, hit, hold)
            f = _idle_floor(path, b, gain, hf)
            k = _her.rung_of_mean(path, f)
            home = _her.rung_of_mean(path, b)
            if k != home:
                bad.append("%s rest=%s hit=%s hold=%s: idles at rung %d (%s), home is %d"
                           % (path, rest, hit, hold, k, BANDS[path][k - 1][2], home))
    print("       INFO  %d of %d combinations leave their rest rung at the GUESSED p=%.2f, %d-min beat "
          "(not a check: p is unmeasured and the beat is authored)"
          % (len(bad), sum(len(list(_combos(p))) for p in PATHS), _P_IDLE, int(_BEAT_MINUTES)))
    for line in bad[:4]:
        print("         " + line)


def test_E2_E3_reachability():
    print("\n[E2/E3] THE TOP IS REACHABLE, AND NEVER ONE BEAT AWAY")
    unreachable, too_fast = [], []
    slowest = (0, None)
    for path in PATHS:
        # E2: the strongest person on this path can get there
        strongest = _her.REST_WORDS[_her.REST_CAP[path] - 1] if _her.REST_CAP[path] <= len(_her.REST_WORDS) else _her.REST_WORDS[-1]
        b, gain, hf = _params(path, strongest, "high", "lasting")
        n = _beats_to_top(path, b, gain, hf)
        if n is None:
            unreachable.append("%s (rest=%s hit=high hold=lasting)" % (path, strongest))
        elif n > slowest[0]:
            slowest = (n, path)
        # E3: nobody gets there in a beat or two
        for rest, hit, hold in _combos(path):
            b, gain, hf = _params(path, rest, hit, hold)
            n = _beats_to_top(path, b, gain, hf)
            if n is not None and n < _REACH_MIN:
                too_fast.append("%s rest=%s hit=%s hold=%s in %d" % (path, rest, hit, hold, n))
    check("on-every-path-the-strongest-combination-reaches-the-top", not unreachable,
          "unreachable on: %s" % unreachable)
    check("no-combination-reaches-the-top-in-under-%d-beats" % _REACH_MIN, not too_fast,
          "%d do; first: %s" % (len(too_fast), too_fast[:3]))
    print("       slowest strongest-person to the top: %s beats (%s)" % slowest)


def test_E4_ranks_hold():
    print("\n[E4] RANKS HOLD — after one reading and one beat, hit and hold each order the result")
    # ONE beat, not a settling point. Under the minute clock a slow path (half-life in days) fed a
    # reading every beat saturates at 1.0 for every hit and hold, and a clamp has no ranks. That
    # saturation is the clock's real finding (see the module docstring and E1); separability is
    # asserted where it can be seen: the value after one receipt and one beat's decay is strictly
    # increasing in hit (the receipt) and in hold (the decay), on every path, at every rest.
    bad = []
    for path in PATHS:
        k = 2
        v = rungs.vector_for(path, k)
        for rest in _her.REST_WORDS[:_her.REST_CAP[path]]:
            b = _her.rest_mean(path, {path: {"rest": rest}})
            for hold in _her.PERSIST:
                hf = _her.PERSIST[hold]
                row = [_beat(b + 0.10, b, v, _her.GAIN[hit], hf, path) for hit in _her.GAIN]
                if not all(x < y for x, y in zip(row, row[1:])):
                    bad.append("%s rest=%s hold=%s: hit order broken %s" % (path, rest, hold, [round(x, 4) for x in row]))
            for hit in _her.GAIN:
                g = _her.GAIN[hit]
                row = [_beat(b + 0.10, b, v, g, _her.PERSIST[hold], path) for hold in _her.PERSIST]
                if not all(x < y for x, y in zip(row, row[1:])):
                    bad.append("%s rest=%s hit=%s: hold order broken %s" % (path, rest, hit, [round(x, 4) for x in row]))
    check("hit-and-hold-each-order-the-value-after-one-beat", not bad, "%d broken; first: %s" % (len(bad), bad[:3]))


def main():
    print("test_genotype_balance.py — the person system against the global system, every combination")
    n = sum(len(list(_combos(p))) for p in PATHS)
    print("  %d combinations across %d paths; envelope p=%.2f reach<=%d reach>=%d"
          % (n, len(PATHS), _P_IDLE, _REACH_MAX, _REACH_MIN))
    for t in (test_E1_floor_stays_home, test_E2_E3_reachability, test_E4_ranks_hold):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
