"""test_rung_vectors.py — what a rung is WORTH, and that the table cannot rot.

`docs/emotion-arithmetic.md` section 2. Phase 1 of the emotion-arithmetic migration: a rung's
vector is the same for every character and every target, and the character enters the arithmetic
once, later, as a gain.

THE PUBLISHED TABLE IS THE FIXTURE. Section 2 prints a height for all 92 built rungs. They are
reproduced here VERBATIM rather than recomputed, because a test that derives its expectation the
same way the code does proves only that the code is self-consistent — the sticky is
`an-instrument-that-agrees-with-itself-is-not-verified`.

TWO DELIBERATE-BREAKAGE CONTROLS, at the end. A table this regular is exactly the kind that passes
by accident, so the suite proves it can FAIL: change lambda and the vectors must move; move a band
and the vector must move with it.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import rungs                                      # noqa: E402
from src.engine.rung_blocks import BANDS                          # noqa: E402
from src.engine.rungs import RungError                            # noqa: E402

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    (PASS if ok else FAIL).append(name)


# docs/emotion-arithmetic.md section 2, transcribed. NOT derived.
PUBLISHED = {
    "DISPLEASURE": [.035, .125, .245, .375, .50, .615, .72, .81, .88, .93, .965, 1.0],
    "DEFLATION":   [.04, .13, .24, .36, .51, .65, .75, .85, .93, .985],
    "WARINESS":    [.035, .105, .175, .25, .33, .41, .495, .58, .67, .76, .835, .905, .975],
    "GOODWILL":    [.045, .135, .225, .315, .405, .495, .58, .66, .775, .93],
    "STIRRING":    [.04, .13, .24, .35, .44, .53, .62, .70, .795, .895, .975],
    "RECEPTIVITY": [.04, .125, .215, .305, .40, .50, .595, .695, .795, .885, .97],
    "SELF-REGARD": [.05, .16, .285, .405, .51, .61, .705, .79, .865, .93, .985],
    "DISTASTE":    [.075, .25, .475, .71, .915],
    "LEVITY":      [.05, .16, .29, .43, .56, .68, .795, .895, .975],
}

# The ONE row where the doc and the formula disagree, named so it cannot be quietly absorbed.
# DISPLEASURE's top band is (0.98, 1.01); its midpoint is 0.995 and the doc prints 1.0. Every other
# path's top rung is published as its own raw midpoint, so no clamp-to-one rule is in force — this
# is a rounding in the prose. Recorded rather than special-cased.
KNOWN_DOC_ROUNDING = {("DISPLEASURE", 12): (0.995, 1.0)}


def test_every_built_rung_has_a_vector():
    print("\n[1] EVERY RUNG IS WORTH SOMETHING")
    missing = []
    for path in rungs.paths():
        for i in range(1, len(BANDS[path]) + 1):
            try:
                v = rungs.vector_for(path, i)
            except RungError:
                missing.append("%s:%d" % (path, i)); continue
            if not isinstance(v, float) or v <= 0.0:
                missing.append("%s:%d=%r" % (path, i, v))
    total = sum(len(BANDS[p]) for p in rungs.paths())
    print("       %d built rungs across %d paths" % (total, len(rungs.paths())))
    check("every-rung-has-a-positive-vector", not missing, missing[:5])
    check("the-count-is-the-band-count", total == 92, total)


def test_the_published_heights_are_reproduced():
    print("\n[2] AGAINST THE DOC'S OWN TABLE — transcribed, not derived")
    off = []
    for path, expected in sorted(PUBLISHED.items()):
        if len(expected) != len(BANDS[path]):
            off.append("%s: %d published vs %d bands" % (path, len(expected), len(BANDS[path])))
            continue
        for i, exp in enumerate(expected, start=1):
            got = rungs.height_of(path, i)
            if (path, i) in KNOWN_DOC_ROUNDING:
                continue
            if abs(got - exp) > 0.0005:
                off.append("%s rung %d: %.4f vs published %.3f" % (path, i, got, exp))
    check("all-100-unambiguous-heights-match", not off, off[:4])
    # and the one that does not, asserted EXPLICITLY so it stays visible
    got, printed = rungs.height_of("DISPLEASURE", 12), KNOWN_DOC_ROUNDING[("DISPLEASURE", 12)][1]
    check("the-single-doc-rounding-is-where-it-was", abs(got - 0.995) < 1e-9 and printed == 1.0,
          "%.4f vs doc %.3f" % (got, printed))


def test_a_higher_rung_is_always_worth_more():
    print("\n[3] MONOTONE — a ladder that pays less to climb is not a ladder")
    bad = []
    for path in rungs.paths():
        vs = [rungs.vector_for(path, i) for i in range(1, len(BANDS[path]) + 1)]
        for i in range(1, len(vs)):
            if vs[i] <= vs[i - 1]:
                bad.append("%s rung %d (%.4f) <= rung %d (%.4f)" % (path, i + 1, vs[i], i, vs[i - 1]))
    check("strictly-increasing-on-every-path", not bad, bad[:4])


def test_the_owners_ratio_holds():
    print("\n[4] THE OWNER'S OWN EXAMPLE")
    fury = rungs.vector_for("DISPLEASURE", 9)
    displeasure = rungs.vector_for("DISPLEASURE", 1)
    ratio = fury / displeasure
    print("       fury %.4f / displeasure %.4f = %.1fx" % (fury, displeasure, ratio))
    # "A fury tag is worth twenty-five times a displeasure tag, to everyone." (section 2)
    check("a-fury-tag-is-about-25x-a-displeasure-tag", 24.0 <= ratio <= 26.0, "%.1fx" % ratio)


def test_the_vector_is_bounded_by_lambda():
    print("\n[5] BOUNDED — no rung is worth more than its path's lambda")
    over = [(p, i) for p in rungs.paths() for i in range(1, len(BANDS[p]) + 1)
            if rungs.vector_for(p, i) > rungs.LAMBDA[p] + 1e-12]
    check("no-vector-exceeds-lambda", not over, over[:4])
    check("lambda-covers-every-built-path",
          sorted(rungs.LAMBDA) == sorted(rungs.paths()), sorted(rungs.LAMBDA))


def test_it_refuses_what_it_should():
    print("\n[6] REFUSALS")
    for name, call in (("unknown-path", lambda: rungs.vector_for("COURAGE", 1)),
                       ("rung-zero", lambda: rungs.vector_for("DISPLEASURE", 0)),
                       ("rung-past-the-top", lambda: rungs.vector_for("DISTASTE", 6)),
                       ("rung-not-an-int", lambda: rungs.vector_for("DISPLEASURE", 1.5))):
        try:
            call()
            check(name, False, "did NOT raise")
        except RungError:
            check(name, True)


def test_the_controls():
    """Deliberate breakage. A derived table this regular passes by accident unless it can fail."""
    print("\n[7] CONTROLS — prove the instrument can fail")
    path, idx = "WARINESS", 5
    before = rungs.vector_for(path, idx)

    # C1: lambda is real — halve it and the vector must halve.
    live = rungs.LAMBDA[path]                     # the measured value, whatever it is today
    rungs.LAMBDA[path] = live / 2.0
    halved = rungs.vector_for(path, idx)
    rungs.LAMBDA[path] = live
    check("a-changed-lambda-is-detected", abs(halved - before / 2.0) < 1e-12,
          "%.5f then %.5f" % (before, halved))
    check("...and-it-was-restored", abs(rungs.vector_for(path, idx) - before) < 1e-12)

    # C2: the table is DERIVED from BANDS, not a copy of it — move a band, the vector must move.
    original = BANDS[path][idx - 1]
    BANDS[path][idx - 1] = (original[0], original[1] + 0.10, original[2])
    moved = rungs.vector_for(path, idx)
    BANDS[path][idx - 1] = original
    check("a-moved-band-moves-the-vector", moved > before + 1e-9,
          "%.5f then %.5f — if equal, the table is a hand-written copy" % (before, moved))
    check("...and-the-band-was-restored", abs(rungs.vector_for(path, idx) - before) < 1e-12)


def main():
    for t in (test_every_built_rung_has_a_vector,
              test_the_published_heights_are_reproduced,
              test_a_higher_rung_is_always_worth_more,
              test_the_owners_ratio_holds,
              test_the_vector_is_bounded_by_lambda,
              test_it_refuses_what_it_should,
              test_the_controls):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("VERDICT: FAIL -> %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
