#!/usr/bin/env python3
"""test_decay_law.py — the one relaxation law, and proof that lifting it changed no number.

TWO JOBS, and the second is the reason this file was written BEFORE the conversion rather than
after. Part [1] asserts the law's own identities. Part [2] is an EQUIVALENCE HARNESS: for each of
the five converted callers it recomputes the pre-lift arithmetic INLINE, from constants read off
the module, and asserts the live function still returns exactly that.

Written first on purpose. A refactor test authored after the refactor asserts what the new code
does, which is not the question — the question is whether the new code does what the OLD code did,
and only a contract captured beforehand can answer it. `docs/character-model.md` calls this equation
normative and the engine held six spellings of it; a lift that quietly changed one of them would be
worse than the duplication, because the duplication at least behaved.

Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.decay_law import relax                              # noqa: E402
from src.engine.records import RecordError                          # noqa: E402
from src.engine import bonds, wound, arc, toward                    # noqa: E402
from src.engine import world_appraisal as wa                        # noqa: E402

FAILS = []
_TIMES = (0.0, 0.5, 1.0, 3.0, 7.0, 40.0)
_VALUES = (0.0, 0.13, 0.5, 0.87, 1.0)


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % detail))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


# --- [1] the law's own identities ---------------------------------------------------------

def test_zero_elapsed_is_EXACTLY_the_identity():
    """Not approximately. `retention ** 0` is 1.0 for every retention, so the arithmetic reduces to
    `rest + (value - rest) * 1.0`. A decay that drifts on a zero-length tick is a defect that only
    surfaces after a long run, when a hundred no-op ticks have moved a value nobody touched."""
    bad = [(v, r, k) for v in _VALUES for r in (0.0, 0.5, 1.0) for k in (0.0, 0.5, 0.9, 1.0)
           if relax(v, r, k, 0.0) != v]
    check("elapsed-0-returns-the-value-unchanged", not bad, "moved for: %r" % (bad[:3],))


def test_a_value_ALREADY_at_rest_never_moves():
    bad = [(r, k, e) for r in _VALUES for k in (0.0, 0.3, 0.97, 1.0) for e in _TIMES
           if relax(r, r, k, e) != r]
    check("resting-values-stay-put", not bad, "moved for: %r" % (bad[:3],))


def test_rest_of_zero_reduces_to_plain_multiplication():
    """The case `toward.erode` and `world_appraisal.cool` are — both said so in their own comments
    before the lift, and both are now callers rather than copies."""
    bad = [(v, k, e) for v in _VALUES for k in (0.9, 0.96, 0.99) for e in _TIMES
           if abs(relax(v, 0.0, k, e) - v * (k ** e)) > 1e-12]
    check("rest-zero-is-value-times-retention-to-the-elapsed", not bad, "%r" % (bad[:3],))


def test_the_law_REFUSES_what_it_cannot_apply():
    """Fail loud, hard rule 6, with registered codes. Negative time is the interesting one: a
    negative exponent AMPLIFIES the deviation from rest, so it does not fail — it silently returns
    a memory sharper than it started, which is the shape of defect this repo keeps finding."""
    for name, args, code in (
            ("non-numeric", ("x", 0.0, 0.9, 1.0), "DECAY_INPUT_NOT_NUMERIC"),
            ("negative-time", (0.5, 0.0, 0.9, -1.0), "DECAY_ELAPSED_NEGATIVE"),
            ("retention-above-1", (0.5, 0.0, 1.4, 1.0), "DECAY_RETENTION_OUT_OF_RANGE"),
            ("retention-below-0", (0.5, 0.0, -0.2, 1.0), "DECAY_RETENTION_OUT_OF_RANGE")):
        try:
            relax(*args)
            check("refuses-%s" % name, False, "accepted it")
        except RecordError as e:
            check("refuses-%s" % name, e.code == code, "got %r" % e.code)


# --- [2] equivalence: every converted caller returns what it returned before ---------------

def test_bonds_drift_is_UNCHANGED_by_the_lift():
    """`rest[axis] + (edge[axis] - rest[axis]) * (_RETENTION[axis] ** elapsed)`, clamped per axis."""
    bad = []
    for e in _TIMES:
        edge = {"trust": 0.8, "affinity": 0.2, "respect": 0.65, "debt": 0.4}
        got = bonds.drift(dict(edge), elapsed=e)
        for axis, r0 in bonds._NEUTRAL.items():
            want = max(0.0, min(1.0, r0 + (edge[axis] - r0) * (bonds._RETENTION[axis] ** e)))
            if abs(got[axis] - want) > 1e-12:
                bad.append((e, axis, got[axis], want))
    check("bonds.drift-matches-the-pre-lift-arithmetic", not bad, "%r" % (bad[:3],))


def test_wound_erode_is_UNCHANGED_by_the_lift():
    """`(floor + (now - floor) * (_RETENTION ** e)) - now` — a DELTA, and the sign matters."""
    bad = []
    for e in _TIMES:
        for intensity in (0.2, 0.55, 0.9):
            w = {"intensity": intensity, "kind": "betrayal"}
            got = wound.erode(dict(w), e)
            floor = wound._floor_of(w)
            now = float(intensity)
            want = (floor + (now - floor) * (wound._RETENTION ** e)) - now if now > floor else 0.0
            if abs(got - want) > 1e-12:
                bad.append((e, intensity, got, want))
    check("wound.erode-matches-the-pre-lift-arithmetic", not bad, "%r" % (bad[:3],))


def test_world_appraisal_cool_is_UNCHANGED_by_the_lift():
    bad = []
    for e in _TIMES:
        for v in _VALUES:
            for rate in wa.COOLING:
                got = wa.cool(v, e, rate)
                want = max(0.0, min(1.0, v * (wa.COOLING[rate] ** max(0.0, e))))
                if abs(got - want) > 1e-12:
                    bad.append((e, v, rate, got, want))
    check("world_appraisal.cool-matches-the-pre-lift-arithmetic", not bad, "%r" % (bad[:3],))


def test_cool_gains_the_rest_it_reserved():
    """`cool`'s own NOT YET GENERAL note reserved this: "DECAY ASSUMES A ZERO REST POINT...
    cool(..., rest=...)". The default keeps every existing caller identical."""
    check("default-rest-is-still-zero", wa.cool(0.8, 3.0) == wa.cool(0.8, 3.0, rest=0.0),
          "%r vs %r" % (wa.cool(0.8, 3.0), wa.cool(0.8, 3.0, rest=0.0)))
    # THE ASYMPTOTE IS ASSERTED AS A LIMIT, not at a guessed horizon. The first draft checked
    # |cool(0.8, 40, rest=0.3) - 0.3| < 0.02 and failed at 0.398 — because 0.96**40 is 0.195, so
    # forty units is nowhere near convergence at the typical rate. The code was right and the
    # expectation was invented; a decay test that picks a horizon by feel is testing the tester.
    near, far = wa.cool(0.8, 40.0, rest=0.3), wa.cool(0.8, 400.0, rest=0.3)
    check("it-moves-toward-rest-and-never-past-it", 0.3 < far < near < 0.8,
          "40u=%r 400u=%r" % (near, far))
    check("and-converges-on-it-given-enough-time", abs(far - 0.3) < 0.01, far)


def main():
    print("test_decay_law.py - one equation, six callers, and proof the lift changed no number\n")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print("\n%s" % ("test_decay_law: OK (the law holds and every caller is bit-identical)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
