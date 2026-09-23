"""make_genotype.py — the combinatorial preset draw: a genotype (hit, hold) and a resting face.

`docs/baseline-generation.md` §Genetics: a genotype is a draw of presets that makes ten strangers
from one species prior react differently to the same betrayal. Since 2026-09-10 the draw is per
PATH, each cell independent (owner's decision 2 of 2026-09-09 — one allele carrying everything
welds them). Two things are drawn, and they land in two places on the sheet:

    fixed.genotype[path]           hit    the gain on a reading — GAIN words
                                   hold   the half-life multiplier — PERSIST words
    baseline.temperament[path]     rest   where the float sits at rest — a rung word, drawn only
                                          up to the path's REST_CAP (`draw_rest`)

The rest word is a CHARACTER DESIGN choice, beside the voice (owner, 2026-09-10: "have
temperament be a character design question, along with their voice and other personality
options"); it is drawn here only for background people who get no author. Rest x hit x hold per
path is 32..80 combinations; across eight paths the space is ~2e14, so ten drawn characters never
collide, which is the foundation's whole job (`distinctness` measures it rather than trusting the
arithmetic). Weighted so `typical` / `quiet` are common and the tails rare — a uniform draw would
make one person in four exceptionally fearful.

AUTHORED FOR PRINCIPALS, DRAWN FOR EVERYONE ELSE. A principal is authored backward from the
character the story needs (word or NUMBER in any cell — `heritable` honours both), then validated
forward. Drawing a principal would be starting from the dice and hoping for a protagonist.

THE DIE IS ROLLED HERE AND NOWHERE IN THE ENGINE (CLAUDE.md hard rule 4). Hash-seeded, so the same
seed gives the same person on any machine and there is no global RNG state to leak between draws.

    python scripts/make_genotype.py --seed kestrel
    python scripts/make_genotype.py --check          # measure the distinctness table
"""
import argparse
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.records import PATHS                                   # noqa: E402
from src.engine import heritable as _her                               # noqa: E402

# The cells and their vocabularies come from heritable.py — one source, no mirror.
_AXES = _her.AXES                                                     # ("hit", "hold")
_WORDS = {"rest": _her.REST_WORDS, "hit": tuple(_her.GAIN), "hold": tuple(_her.PERSIST)}

# Population weights per cell, indexed like the word tuples. rest: most people rest at the floor
# of a path; the tails are the temperaments a reader would call a trait. hit/hold: 'typical'
# common, the tails rare. CALIBRATION, not theory; they shape how unusual an unusual person reads.
_WEIGHTS = {
    "rest": (0.50, 0.30, 0.15, 0.05),        # quiet, low, raised, high
    "hit":  (0.22, 0.40, 0.24, 0.14),        # low, typical, elevated, high
    "hold": (0.22, 0.40, 0.24, 0.14),        # brief, typical, long, lasting
}

_JITTER = 0.06   # perturbation width on the hit multiplier (character-model.md:109)


def _rand(seed, salt):
    """A deterministic [0,1) from a seed and a label."""
    h = hashlib.sha256(("%s|%s" % (seed, salt)).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") / float(1 << 64)


def _weighted(seed, salt, words, weights):
    r = _rand(seed, salt)
    acc = 0.0
    total = float(sum(weights))
    for w, p in zip(words, weights):
        acc += p / total
        if r < acc:
            return w
    return words[-1]


def draw(seed):
    """seed -> the genotype {path: {hit, hold}}. Two independent draws per path.

    Pure in the seed: the same seed always gives the same person, and the seed is the only thing
    that needs recording to reproduce them.
    """
    out = {}
    for p in PATHS:
        out[p] = {axis: _weighted(seed, "%s:%s" % (p, axis), _WORDS[axis], _WEIGHTS[axis])
                  for axis in _AXES}
    return out


def draw_rest(seed):
    """seed -> the resting face {path: {rest}} for `baseline.temperament`; never above the cap.

    Drawn from the same seed as the genotype but a separate salt, so the rest is independent of
    hit and hold on every path (the owner's "three cells, drawn independently").
    """
    out = {}
    for p in PATHS:
        n = min(_her.REST_CAP[p], len(_WORDS["rest"]))
        out[p] = {"rest": _weighted(seed, "%s:rest" % p, _WORDS["rest"][:n], _WEIGHTS["rest"][:n])}
    return out


def perturb(genotype, seed):
    """genotype + seed -> {path: hit multiplier}, jittered.

    docs/character-model.md:109 — "jitter the model's means per character so same-model instances
    aren't identical." Two characters drawn with the SAME genotype are still not clones.
    """
    out = {}
    for p in PATHS:
        base = _her.hit(p, genotype)
        out[p] = round(base * (1.0 + _JITTER * (2.0 * _rand(seed, "jitter:" + p) - 1.0)), 4)
    return out


def as_rows(genotype, seed):
    """The hit cells as unconditional buff rows — the shape src/engine/levers.py already consumes.

    An allele is "a small buff/debuff pack on the primaries' gains" in the doc's own words, and a
    row with no `when` is exactly a permanent unconditional buff. Hold is a rate, not a lever, so
    only the hit cell becomes a row.
    """
    gains = perturb(genotype, seed)
    return [{"lever": p, "op": "x", "magnitude": gains[p],
             "source": "genotype: %s hit %s" % (p, genotype[p]["hit"])}
            for p in PATHS]


def distinctness(n, trials, seed_base=0):
    """-> the measured fraction of trials in which n drawn characters are ALL distinct
    (genotype AND resting face together — that pair is the person)."""
    hits = 0
    for t in range(trials):
        seen = set()
        for i in range(n):
            sd = "%d:%d" % (seed_base + t, i)
            seen.add(json.dumps([draw(sd), draw_rest(sd)], sort_keys=True))
        hits += 1 if len(seen) == n else 0
    return hits / float(trials)


def main():
    ap = argparse.ArgumentParser(description="draw a genotype and a resting face (background/supporting cast only)")
    ap.add_argument("--seed", default="1", help="any string; the same seed gives the same person")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--rows", action="store_true", help="emit as levers.py buff rows")
    ap.add_argument("--check", action="store_true", help="measure the distinctness table")
    args = ap.parse_args()

    if args.check:
        per_path = {p: _her.REST_CAP[p] * len(_her.GAIN) * len(_her.PERSIST) for p in PATHS}
        total = 1
        for v in per_path.values():
            total *= v
        print("combinations per path %s; whole genotype %.2e (weighted draw, not uniform)"
              % (per_path, total))
        for n in (2, 5, 10, 20):
            print("  P(%2d drawn characters all distinct) = %.3f" % (n, distinctness(n, 2000)))
        return 0

    for i in range(args.count):
        seed = args.seed if args.count == 1 else "%s:%d" % (args.seed, i)
        g = draw(seed)
        print(json.dumps({"seed": seed, "genotype": g, "temperament": draw_rest(seed),
                          "rows" if args.rows else "gains":
                              as_rows(g, seed) if args.rows else perturb(g, seed)},
                         sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
