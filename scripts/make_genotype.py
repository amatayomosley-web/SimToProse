"""make_genotype.py — the combinatorial preset draw.

`docs/baseline-generation.md:28` states the purpose plainly, and it is the reason this layer
exists at all:

    "Genetics is a combinatorial preset draw — one allele per heritable axis (the tuple = a
     genotype)... perturbation jitters it so same-genotype people aren't clones. Seeded-random
     for background/supporting; authored for principals... **it's the layer that makes 10
     strangers react differently to the same betrayal.**"

Without it, two soldiers in the same battle feel the same thing. The genotype is what makes a
person's reaction *theirs* — and because `arc.py` never writes it (it writes temperament,
relationships and regard, and reads the genotype only for resilience), two people who then live
identical lives still end up different.

WHY THIS IS IN scripts/ AND NOT src/engine/: CLAUDE.md hard rule 4 — no randomness in the engine.
A seeded draw is a pure function of its seed, so reproducibility survives, but the rule is about
where the die is rolled. The engine consumes a genotype; it never produces one.

AUTHORED FOR PRINCIPALS, DRAWN FOR EVERYONE ELSE. The doc is explicit and it is a good rule: a
principal is authored *backward* from the character the story needs, then validated forward against
the world. Drawing a principal would be starting from the dice and hoping for a protagonist.

An allele is a small buff pack on the primaries' GAINS — the same object shape as a
`src/engine/levers.py` registry row, with no `when` clause, because a genotype is a permanent and
unconditional buff. That is `baseline-generation.md`'s own framing, not an analogy laid over it.
"""
import argparse
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.records import PRIMARIES                        # noqa: E402

# The six heritable axes, from docs/baseline-generation.md:50-57 — Class-B, from the
# behavioural-genetics literature rather than invented. The `gains` column is which primitives each
# axis biases; `sensitivity` and `effortful_control` are global rather than per-primitive, which is
# why they carry no primitive list.
_AXES = {
    "threat_reactivity":      {"gains": ("FEAR",),                "maps_to": "BIS / Neuroticism"},
    "approach_drive":         {"gains": ("SEEKING",),             "maps_to": "BAS / Extraversion"},
    "affiliation_attachment": {"gains": ("CARE", "PANIC_GRIEF"),  "maps_to": "attachment style"},
    "anger_proneness":        {"gains": ("RAGE",),                "maps_to": "(low) Agreeableness"},
    "effortful_control":      {"gains": (),                       "maps_to": "Conscientiousness / constraint"},
    "sensitivity":            {"gains": (),                       "maps_to": "sensory-processing sensitivity"},
}

# The alleles, matching src/engine/state.py:_ALLELE so a drawn genotype and an authored one mean
# the same thing. The scale is a probe-calibrated start and a claim about how much heredity
# matters; it is not retuned here.
_ALLELES = ("low", "typical", "elevated", "high")

# Population weights — "typical" is common and the tails are rare, which is what makes an unusual
# character read as unusual. Uniform draw would make one person in four exceptionally fearful.
_WEIGHTS = {"low": 0.22, "typical": 0.40, "elevated": 0.24, "high": 0.14}

_JITTER = 0.06   # perturbation width on the gain multiplier (character-model.md:109)


def _rand(seed, salt):
    """A deterministic [0,1) from a seed and a label. Hash-based, so no global RNG state exists to
    leak between draws and the same (seed, salt) always gives the same number on any machine."""
    h = hashlib.sha256(("%s|%s" % (seed, salt)).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") / float(1 << 64)


def _weighted(seed, salt):
    r = _rand(seed, salt)
    acc = 0.0
    for allele in _ALLELES:
        acc += _WEIGHTS[allele]
        if r < acc:
            return allele
    return _ALLELES[-1]


def draw(seed):
    """seed -> {axis: allele}. One allele per axis; the tuple IS the genotype.

    Pure in the seed: the same seed always gives the same person, and the seed is the only thing
    that needs recording to reproduce them.
    """
    return {axis: _weighted(seed, axis) for axis in sorted(_AXES)}


def perturb(genotype, seed, allele_values=None):
    """genotype + seed -> {axis: gain multiplier}, jittered.

    docs/character-model.md:109 — "jitter the model's means per character so same-model instances
    aren't identical." Two characters drawn with the SAME genotype are still not clones, which is
    what stops a preset library from reading as a set of flat types.
    """
    if allele_values is None:
        from src.engine.state import _ALLELE
        allele_values = _ALLELE
    out = {}
    for axis, allele in sorted(genotype.items()):
        base = float(allele_values.get(allele, 1.0))
        out[axis] = round(base * (1.0 + _JITTER * (2.0 * _rand(seed, "jitter:" + axis) - 1.0)), 4)
    return out


def as_rows(genotype, seed):
    """The genotype as unconditional buff rows — the shape src/engine/levers.py already consumes.

    baseline-generation.md calls an allele "a small buff/debuff pack on the primaries' gains", and
    a row with no `when` is exactly a permanent unconditional buff. Emitting this shape means the
    genotype and the situational catalog flow through one mechanism instead of two.
    """
    gains = perturb(genotype, seed)
    rows = []
    for axis, mult in sorted(gains.items()):
        for primitive in _AXES[axis]["gains"]:
            rows.append({"lever": primitive, "op": "x", "magnitude": mult,
                         "source": "genotype: %s %s" % (axis, genotype[axis])})
    return rows


def distinctness(n, trials, seed_base=0):
    """-> the measured fraction of trials in which n drawn characters are ALL distinct.

    docs/baseline-generation.md:41 publishes a table of these (6 axes x 3 alleles -> 729 genotypes,
    P(10 all distinct) ~0.94). It is a claim in the repo and cheap to check, so this checks it.
    """
    hits = 0
    for t in range(trials):
        seen = {tuple(sorted(draw("%d:%d" % (seed_base + t, i)).items())) for i in range(n)}
        hits += 1 if len(seen) == n else 0
    return hits / float(trials)


def main():
    ap = argparse.ArgumentParser(description="draw a genotype (background/supporting cast only)")
    ap.add_argument("--seed", default="1", help="any string; the same seed gives the same person")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--rows", action="store_true", help="emit as levers.py buff rows")
    ap.add_argument("--check", action="store_true", help="measure the distinctness table")
    args = ap.parse_args()

    if args.check:
        print("axes %d x alleles %d = %d genotypes (weighted draw, not uniform)"
              % (len(_AXES), len(_ALLELES), len(_ALLELES) ** len(_AXES)))
        for n in (2, 5, 10, 20):
            print("  P(%2d drawn characters all distinct) = %.3f" % (n, distinctness(n, 2000)))
        return 0

    for i in range(args.count):
        seed = args.seed if args.count == 1 else "%s:%d" % (args.seed, i)
        g = draw(seed)
        print(json.dumps({"seed": seed, "genotype": g,
                          "rows" if args.rows else "gains":
                              as_rows(g, seed) if args.rows else perturb(g, seed)},
                         sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
