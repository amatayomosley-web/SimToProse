"""test_genotype.py — the combinatorial preset draw (scripts/make_genotype.py).

THE POINT OF THE GENOTYPE, from `docs/baseline-generation.md:28` and from the project owner in the
same words: **without it, two soldiers in the same battle feel the same thing.** It is the layer
that makes ten strangers react differently to the same betrayal. And because `arc.py` writes
temperament, relationships and regard but NEVER the genotype, two people who then live identical
lives still end up different.

So this suite asks one question in five ways: does the draw actually produce different people, and
does it keep producing the SAME different people when you ask again?

  1. DETERMINISM. A seed is a person. The same seed must always give that person back, or a run
     cannot be reproduced and the seed is not a record of anything.
  2. VARIANCE. Different seeds give different people — measured, not assumed, and reported as the
     probability that N drawn characters are all distinct so `baseline-generation.md:41`'s
     published table is CHECKED rather than trusted.
  3. NOT CLONES. Two characters sharing a genotype still differ, per `character-model.md:109`.
     Without this a preset library reads as a set of flat types, which is the failure the whole
     project is trying to avoid one level up.
  4. THE ROWS ARE REAL ROWS. `as_rows` output must pass `levers._check_row`. An allele is "a small
     buff/debuff pack on the primaries' gains" in the doc's own words, so it must be the same
     object the effective tier already consumes — not a parallel shape that looks similar.
  5. THE DIE IS NOT ROLLED IN THE ENGINE. CLAUDE.md hard rule 4. This module lives in scripts/ and
     src/engine must not import it.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts.make_genotype import (                              # noqa: E402
    _AXES, _ALLELES, as_rows, distinctness, draw, perturb,
)
from src.engine.levers import _check_row                         # noqa: E402
from src.engine.records import PRIMARIES                         # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def test_determinism():
    print("\n[1] DETERMINISM — a seed IS a person")
    check("same-seed-same-genotype", draw("kestrel") == draw("kestrel"))
    check("same-seed-same-gains", perturb(draw("kestrel"), "kestrel") == perturb(draw("kestrel"), "kestrel"))
    check("covers-every-axis", set(draw("x")) == set(_AXES), set(_AXES) ^ set(draw("x")))
    check("every-allele-is-known", all(a in _ALLELES for a in draw("x").values()))
    # no global RNG state: drawing others in between must not disturb a repeat
    first = draw("kestrel")
    for i in range(50):
        draw("noise:%d" % i)
    check("no-global-rng-state", draw("kestrel") == first)


def test_variance():
    print("\n[2] VARIANCE — two soldiers do not feel the same thing")
    a, b = draw("soldier:0"), draw("soldier:1")
    check("different-seeds-different-people", a != b, "%s == %s" % (a, b))
    # the population must actually spread across the allele range, not pile on 'typical'
    seen = {}
    for i in range(400):
        for axis, allele in draw("pop:%d" % i).items():
            seen.setdefault(axis, set()).add(allele)
    thin = [ax for ax, s in seen.items() if len(s) < len(_ALLELES)]
    check("every-axis-reaches-every-allele", not thin, thin)
    for n in (5, 10, 20):
        p = distinctness(n, 400)
        print("       P(%2d drawn all distinct) = %.3f" % (n, p))
    check("ten-drawn-are-near-always-distinct", distinctness(10, 400) > 0.90)


def test_not_clones():
    print("\n[3] NOT CLONES — same genotype, still two people")
    g = draw("shared")
    a, b = perturb(g, "personA"), perturb(g, "personB")
    check("same-genotype-different-gains", a != b)
    check("every-axis-jittered", all(a[k] != b[k] for k in a), [k for k in a if a[k] == b[k]])
    # jitter is a nudge, not a re-roll: it must not push a 'low' past a 'typical'
    spread = max(abs(a[k] - b[k]) for k in a)
    check("jitter-stays-small", spread < 0.20, "max gain spread %.3f" % spread)


def test_rows_are_registry_rows():
    print("\n[4] THE ROWS ARE REAL ROWS — an allele IS an unconditional buff")
    rows = as_rows(draw("rowtest"), "rowtest")
    check("produces-rows", len(rows) > 0)
    bad = []
    for i, r in enumerate(rows):
        try:
            _check_row(r, i)
        except ValueError as e:
            bad.append(str(e)[:70])
    check("every-row-passes-levers-validation", not bad, bad[:2])
    check("every-lever-is-a-primitive", all(r["lever"] in PRIMARIES for r in rows))
    check("no-when-clause-a-genotype-is-unconditional", all("when" not in r for r in rows))
    check("every-row-names-its-source", all(r.get("source", "").startswith("genotype:") for r in rows))


def test_die_not_rolled_in_engine():
    print("\n[5] THE DIE IS NOT ROLLED IN THE ENGINE — CLAUDE.md hard rule 4")
    eng = os.path.join(REPO, "src", "engine")
    offenders = []
    for fn in sorted(os.listdir(eng)):
        if not fn.endswith(".py"):
            continue
        txt = open(os.path.join(eng, fn), encoding="utf-8").read()
        if "make_genotype" in txt or "import random" in txt:
            offenders.append(fn)
    check("engine-imports-neither-random-nor-this-module", not offenders, offenders)
    check("module-lives-in-scripts",
          os.path.isfile(os.path.join(REPO, "scripts", "make_genotype.py")))


def main():
    print("test_genotype.py — the combinatorial preset draw")
    for t in (test_determinism, test_variance, test_not_clones,
              test_rows_are_registry_rows, test_die_not_rolled_in_engine):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
