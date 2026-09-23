"""test_genotype.py — the combinatorial preset draw (scripts/make_genotype.py): hit + hold, and a resting face.

THE POINT OF THE GENOTYPE, from `docs/baseline-generation.md` and from the project owner in the
same words: **without it, two soldiers in the same battle feel the same thing.** It is the layer
that makes ten strangers react differently to the same betrayal. And because `arc.py` writes
temperament, relationships and regard but NEVER the genotype, two people who then live identical
lives still end up different.

REBUILT 2026-09-10 with the per-path genotype (owner: "the genotype is the starting vectors,
then we assign the allele and then we assign the decay"), and REBUILT AGAIN the same day when the
owner moved the resting cell out of it: "have temperament be a character design question, along
with their voice and other personality options." The genotype is {hit, hold}; the rest word lives
at baseline.temperament[path].rest and is drawn separately (`draw_rest`) for people nobody
authors. The suite asks the same question in six ways: does the draw produce different people,
does it keep producing the SAME different people, and does it respect what the owner ruled?

  1. DETERMINISM. A seed is a person.
  2. VARIANCE. Different seeds give different people — measured as P(N drawn are all distinct).
  3. NOT CLONES. Two characters sharing a genotype still differ (`character-model.md:109`).
  4. THE ROWS ARE REAL ROWS. `as_rows` output passes `levers._check_row` — the hit cell IS the
     unconditional buff the doc describes.
  5. THE DIE IS NOT ROLLED IN THE ENGINE. CLAUDE.md hard rule 4.
  6. THE CELLS ARE THE OWNER'S: drawn independently; rest never drawn above the path's cap;
     rest reads as a rung midpoint off the LIVE ladder; hold composes in half-life; a rest inside
     a genotype cell is refused by name.
"""
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts.make_genotype import (                              # noqa: E402
    _AXES, _WORDS, as_rows, distinctness, draw, draw_rest, perturb,
)
from src.engine.levers import _check_row                         # noqa: E402
from src.engine.records import PATHS                             # noqa: E402
from src.engine import heritable as _her                         # noqa: E402
from src.engine.rung_blocks import BANDS                         # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def test_determinism():
    print("\n[1] DETERMINISM — a seed IS a person")
    check("same-seed-same-genotype", draw("kestrel") == draw("kestrel"))
    check("same-seed-same-gains", perturb(draw("kestrel"), "kestrel") == perturb(draw("kestrel"), "kestrel"))
    g = draw("x")
    check("covers-every-path", set(g) == set(PATHS), set(PATHS) ^ set(g))
    check("every-path-has-every-cell", all(set(c) == set(_AXES) for c in g.values()))
    check("every-word-is-known", all(c[ax] in _WORDS[ax] for c in g.values() for ax in _AXES))
    t = draw_rest("x")
    check("same-seed-same-resting-face", draw_rest("kestrel") == draw_rest("kestrel"))
    check("resting-face-covers-every-path-with-a-rest-word",
          set(t) == set(PATHS) and all(set(r) == {"rest"} and r["rest"] in _WORDS["rest"] for r in t.values()), t)
    first = draw("kestrel")
    for i in range(50):
        draw("noise:%d" % i)
    check("no-global-rng-state", draw("kestrel") == first)


def test_variance():
    print("\n[2] VARIANCE — two soldiers do not feel the same thing")
    a, b = draw("soldier:0"), draw("soldier:1")
    check("different-seeds-different-people", a != b)
    seen = {}
    for i in range(400):
        sd = "pop:%d" % i
        for p, cell in draw(sd).items():
            for ax, w in cell.items():
                seen.setdefault((p, ax), set()).add(w)
        for p, row in draw_rest(sd).items():
            seen.setdefault((p, "rest"), set()).add(row["rest"])
    # hit and hold reach every word on every path; rest reaches every word UP TO THE CAP
    thin = [k for k, s in seen.items() if k[1] != "rest" and len(s) < len(_WORDS[k[1]])]
    check("hit-and-hold-reach-every-word", not thin, thin)
    thin_rest = [p for p in PATHS if len(seen[(p, "rest")]) < min(_her.REST_CAP[p], len(_her.REST_WORDS))]
    check("rest-reaches-every-word-under-the-cap", not thin_rest, thin_rest)
    for n in (5, 10, 20):
        print("       P(%2d drawn all distinct) = %.3f" % (n, distinctness(n, 400)))
    check("ten-drawn-are-near-always-distinct", distinctness(10, 400) > 0.99)


def test_not_clones():
    print("\n[3] NOT CLONES — same genotype, still two people")
    g = draw("shared")
    a, b = perturb(g, "personA"), perturb(g, "personB")
    check("same-genotype-different-gains", a != b)
    check("every-path-jittered", all(a[k] != b[k] for k in a), [k for k in a if a[k] == b[k]])
    spread = max(abs(a[k] - b[k]) for k in a)
    check("jitter-stays-small", spread < 0.20, "max gain spread %.3f" % spread)


def test_rows_are_registry_rows():
    print("\n[4] THE ROWS ARE REAL ROWS — a hit IS an unconditional buff")
    rows = as_rows(draw("rowtest"), "rowtest")
    check("one-row-per-path", len(rows) == len(PATHS), len(rows))
    bad = []
    for i, r in enumerate(rows):
        try:
            _check_row(r, i)
        except ValueError as e:
            bad.append(str(e)[:70])
    check("every-row-passes-levers-validation", not bad, bad[:2])
    check("every-lever-is-a-path", all(r["lever"] in PATHS for r in rows))
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
    check("module-lives-in-scripts", os.path.isfile(os.path.join(REPO, "scripts", "make_genotype.py")))


def test_the_cells_are_the_owners():
    print("\n[6] THE CELLS — independent, capped, on the live ladder, in half-life; rest is design")
    # rest never above the cap, over 400 draws
    over = []
    for i in range(400):
        t = draw_rest("cap:%d" % i)
        for p in PATHS:
            if _her.rest_rung(p, t) > _her.REST_CAP[p]:
                over.append((p, t[p]["rest"]))
    check("rest-is-never-drawn-above-the-cap", not over, over[:3])
    # the cells are INDEPENDENT: across the population, hit does not predict hold, and the
    # resting face does not predict the hit
    pairs, rest_hit = {}, {}
    for i in range(400):
        sd = "ind:%d" % i
        g, t = draw(sd), draw_rest(sd)
        for p in PATHS:
            pairs.setdefault(g[p]["hit"], set()).add(g[p]["hold"])
            rest_hit.setdefault(t[p]["rest"], set()).add(g[p]["hit"])
    check("hit-does-not-predict-hold", all(len(s) == len(_her.PERSIST) for s in pairs.values()),
          {k: sorted(v) for k, v in pairs.items()})
    check("rest-does-not-predict-hit", all(len(s) == len(_her.GAIN) for s in rest_hit.values()),
          {k: sorted(v) for k, v in rest_hit.items()})
    # rest is a rung midpoint read off the LIVE ladder, so a re-band would move it
    for p in PATHS:
        for i, w in enumerate(_her.REST_WORDS[:_her.REST_CAP[p]]):
            lo, hi, _ = BANDS[p][i]
            got = _her.rest_mean(p, {p: {"rest": w}})
            if abs(got - (lo + hi) / 2.0) > 1e-12:
                _FAILS.append("rest-midpoint:%s:%s" % (p, w))
                print("  FAIL  rest-midpoint %s %s -> %.4f not %.4f" % (p, w, got, (lo + hi) / 2.0))
    check("rest-reads-the-band-midpoint", not any(f.startswith("rest-midpoint") for f in _FAILS))
    # a number is honoured; a number above the cap is REPORTED, not refused
    over, rung = _her.over_cap("DISTASTE", {"DISTASTE": {"rest": 0.7}})
    check("an-authored-number-above-the-cap-is-honoured-and-named",
          over and rung == 4 and _her.rest_mean("DISTASTE", {"DISTASTE": {"rest": 0.7}}) == 0.7, (over, rung))
    # hold composes in HALF-LIFE: the same word, the same ratio on every path
    from src.engine.state import half_life_minutes as _hl
    ratios = set()
    for p in PATHS:
        for v in (0.02, 0.95):                                   # both zones
            ratios.add(round(_hl(p, v, _her.PERSIST["lasting"]) / _hl(p, v, 1.0), 9))
    check("hold-stretches-half-life-by-one-ratio-on-every-path-and-zone", ratios == {round(_her.PERSIST["lasting"], 9)}, ratios)
    # the resting mean a sheet gets is seeded from the authored rest WORD, nothing else; a row
    # that already carries a mean keeps it (the arc engine writes there)
    t = _her.resting(WARINESS="high", DEFLATION="raised (a sadness under him)")
    check("temperament-derives-from-rest",
          t["WARINESS"]["mean"] == _her.rung_midpoint("WARINESS", 4) and t["DEFLATION"]["mean"] == _her.rung_midpoint("DEFLATION", 3)
          and t["STIRRING"]["mean"] == _her.rung_midpoint("STIRRING", 1) and t["STIRRING"]["rest"] == "quiet", t)
    ch = {"fixed": {"genotype": {}}, "baseline": {"temperament": {"WARINESS": {"rest": "high", "mean": 0.61}}}, "current": {}}
    same = ch["baseline"]["temperament"]
    _her.ensure_temperament(ch)
    check("a-stored-mean-is-kept-and-the-seed-is-in-place",
          ch["baseline"]["temperament"] is same and same["WARINESS"]["mean"] == 0.61 and same["GOODWILL"] == {"rest": "quiet", "mean": _her.rung_midpoint("GOODWILL", 1)}, same)
    # the retired shapes are refused by name: the six axes, and a rest inside a genotype cell
    try:
        _her.hit("WARINESS", {"threat_reactivity": "high"})      # the retired shape, refused
        check("old-axes-are-refused", False, "no error raised")
    except Exception as exc:
        check("old-axes-are-refused", "GENOTYPE_OLD_AXES" in str(exc), str(exc)[:80])
    try:
        _her.hit("WARINESS", {"WARINESS": {"rest": "high", "hit": "high"}})   # the morning-of shape, refused
        check("rest-in-a-genotype-cell-is-refused", False, "no error raised")
    except Exception as exc:
        check("rest-in-a-genotype-cell-is-refused", "GENOTYPE_REST_MOVED" in str(exc), str(exc)[:80])


def main():
    print("test_genotype.py — the combinatorial preset draw: hit + hold, and a resting face")
    for t in (test_determinism, test_variance, test_not_clones, test_rows_are_registry_rows,
              test_die_not_rolled_in_engine, test_the_cells_are_the_owners):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
