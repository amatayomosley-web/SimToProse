"""test_decay_law.py — the two identities every caller relies on, and the three refusals.

`relax` replaced two hand-spelled copies of the same equation (`state.decay`, `bonds.drift`) on
2026-09-04. The 50 existing suites are the EQUIVALENCE proof that the lift moved no behaviour —
state.decay is covered by test_state, bonds.drift by test_bonds, and both run end-to-end in
test_scene and test_pipeline_e2e. This file asserts the things neither of those can: the
identities, and the refusals that did not exist before the lift.

The identities matter because they are what a LONG RUN depends on. A decay that drifts a value on
a zero-length tick, or that walks a value already sitting at its rest point, is off by a rounding
error per beat and by something visible after a thousand — the kind of defect that never shows up
in a test that runs three turns.

    python tests/test_decay_law.py
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.decay_law import relax                    # noqa: E402
from src.engine.records import RecordError                # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, "" if cond else "  -- " + detail))
    if not cond:
        FAILS.append(name)


def test_zero_elapsed_returns_the_value_EXACTLY():
    """Not approximately. `retention ** 0` is 1.0 for every retention, so the arithmetic is
    `rest + (value - rest) * 1.0` and floating point has nothing to round."""
    for k in (0.0, 0.1, 0.5, 0.9, 0.99, 1.0):
        got = relax(0.8, 0.2, k, 0)
        check("zero-elapsed-exact-at-retention-%s" % k, got == 0.8, repr(got))


def test_a_value_already_at_rest_never_moves():
    """For any retention, any elapsed. A resting value that walks is a slow leak."""
    for k in (0.0, 0.5, 1.0):
        for e in (0, 1, 7, 1000):
            got = relax(0.42, 0.42, k, e)
            check("at-rest-stays-k%s-e%s" % (k, e), got == 0.42, repr(got))


def test_it_relaxes_toward_rest_and_never_past_it():
    """Monotone approach: each step is closer to rest and never overshoots."""
    prev, rest = 1.0, 0.0
    for e in range(1, 8):
        got = relax(1.0, rest, 0.5, e)
        check("monotone-step-%d" % e, rest <= got < prev, "%r not in [%r, %r)" % (got, rest, prev))
        prev = got


def test_retention_1_is_a_freeze_and_0_is_a_snap():
    """The two ends of the range, which the callers' tables actually use."""
    check("retention-1-freezes", relax(0.9, 0.1, 1.0, 50) == 0.9)
    check("retention-0-snaps-to-rest", relax(0.9, 0.1, 0.0, 1) == 0.1)


def _refuses(code, fn):
    try:
        fn()
        return False, "no refusal"
    except RecordError as e:
        return e.code == code, "got %s" % e.code
    except Exception as e:                                # noqa: BLE001
        return False, "wrong type %r" % (e,)


def test_the_three_refusals():
    """These did NOT exist before the lift — both inline spellings accepted anything float()
    would swallow, and a negative elapsed AMPLIFIED the deviation rather than shrinking it."""
    ok, d = _refuses("DECAY_ELAPSED_NEGATIVE", lambda: relax(0.5, 0.0, 0.9, -1))
    check("negative-elapsed-refused", ok, d)
    ok, d = _refuses("DECAY_RETENTION_OUT_OF_RANGE", lambda: relax(0.5, 0.0, 1.5, 1))
    check("retention-above-1-refused", ok, d)
    ok, d = _refuses("DECAY_RETENTION_OUT_OF_RANGE", lambda: relax(0.5, 0.0, -0.1, 1))
    check("retention-below-0-refused", ok, d)
    ok, d = _refuses("DECAY_INPUT_NOT_NUMERIC", lambda: relax("warm", 0.0, 0.9, 1))
    check("non-numeric-refused", ok, d)


def test_the_CONTROL_a_negative_exponent_really_would_amplify():
    """Proves the refusal above guards something real rather than a hypothetical. Computed
    directly, a negative elapsed moves the value AWAY from rest — which is what the old inline
    spellings would have done silently."""
    amplified = 0.0 + (1.0 - 0.0) * (0.5 ** -2)
    check("negative-exponent-amplifies", amplified > 1.0,
          "%r — if this is not >1 the refusal is guarding nothing" % (amplified,))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("\nVERDICT: %s%s" % ("FAIL -> " if FAILS else "PASS", FAILS or ""))
    sys.exit(1 if FAILS else 0)
