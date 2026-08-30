# The composition pass — how a backstory becomes a baseline

*(NORMATIVE. `baseline-generation.md` owns the composition EQUATION; this owns the MECHANISM that
evaluates it. `reference-species-prior.md` holds the zero-point and the starting library.)*

## The split

Two operations get conflated, and separating them is the whole design.

| | operation | who | why |
|---|---|---|---|
| **classify** | which formative profiles this backstory matches, and how strongly | **LLM**, once per character | no script reads "raised in a lighthouse by a grandmother who barely spoke" |
| **compose** | prior + Σ(weighted diffs), summed, clamped, capped | **script** | arithmetic, and the ±0.35 cap has to be enforceable |

Same seam the rest of the engine uses: the model judges, the code computes. If the LLM emits final
numbers instead, reproducibility goes, the cap stops being enforceable, and a classification error
becomes indistinguishable from a calibration one.

**Generation-time, once per character.** It belongs in `scripts/` beside the genotype draw and does
not touch CLAUDE.md rule 3 (no LLM in `src/engine/`).

## What the LLM sees

Three things and nothing else — no character sheet, no other characters, no target numbers.

```
BACKSTORY (prose, from the author)
LIBRARY   (every profile: name, one-line description, and its diffs — visible, not hidden)
RULES     pick from the library with weights. Propose a NEW profile ONLY if nothing
          above 0.5 fits the dominant feature. Every diff names a field and why.
```

Showing the diffs matters: a classifier that cannot see what a profile *does* is guessing at labels.

## What it returns

```json
{ "picks": [ {"profile": "neglect", "weight": 0.3,
              "why": "absence of tending, but no cruelty — partial match only"} ],
  "propose": {
    "name": "isolation",
    "gap": "no entry covers formative solitude without deprivation",
    "diffs": { "relatedness": -0.20, "PLAY": -0.15, "autonomy": +0.15 },
    "why": { "relatedness": "no peers to need",
             "PLAY": "play is social and there was no one to play with",
             "autonomy": "self-sufficiency was not chosen, it was the only option" } } }
```

`propose` is optional and usually absent. `picks` may be empty for a character whose backstory is
genuinely unremarkable — that is a legitimate answer, not a failure.

## Admission gate — before a proposal enters the library

Three checks, and they come from two places rather than one:

1. **Not a duplicate.** Cosine to every existing profile below ~0.95, the test
   `src/engine/compounds.py:separability` already applies to the compound table. A proposal above
   that line is an existing profile with a new name.
2. **Every diff names a field the engine reads.** The twin of
   `src/engine/compounds.py:validate` — a diff on a field nothing consumes is the
   authored-but-inert defect in a new place.
3. **Stacked total within ±0.35 of prior on any field**, per `reference-species-prior.md` §6.
   That cap is a precedent set in this repo on 2026-08-22, not an external finding.

A proposal that fails 1 is rewritten as a pick. Failing 2 or 3 is rejected outright.

## The two artifacts are different

- **The pick** is per-character and goes in that character's provenance — it is the "why" that
  `baseline-generation.md:31` requires, and the thing that seeds the vault.
- **The profile** is reusable and goes in the library.

**The library converges.** Early books propose often; later books mostly pick. That is what makes
this a machine rather than an LLM you re-ask forever, and it is the same growth path the compound
vocabulary follows.

## What the script does

```
baseline[field] = clamp( prior[field] + Σ over picks of weight × profile.diffs[field] )
```

Then the genotype draw supplies the gains, and the whole thing is written with its provenance
attached. Deterministic given the picks — so a recorded classification reproduces a character
exactly, and only the classification step needs a model.

## Falsification — run this from day one

**Same backstory, five runs.** If the classifications diverge materially, the approach is dead and
you know in ten minutes. If they are stable, note that the variation you actually WANT is already
coming from the genotype draw and its jitter, not from classifier noise.

Second check, cheaper: **a backstory that matches nothing should return empty picks.** A classifier
that always finds something is pattern-matching, and its output carries no information.

## What this does not do

- It does not author the vault, the catalog, the voice, or the edges — only the baseline fields the
  formative layers touch.
- It does not touch the genotype. That is drawn (`scripts/make_genotype.py`) or authored backward
  for principals, and nothing composed may write it — the genotype is the layer the story cannot
  change.
- **It is unbuilt.** This is the design; `SPEC-LEDGER.md` is where its status is tracked.
