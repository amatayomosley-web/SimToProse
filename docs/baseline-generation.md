# Baseline Generation — where every per-character number is born (WORKING)

**Status: working.** The keystone. The engine runs on per-character values and they are *all* born here, once, at character creation. This specifies `design.md` Phase B's "baseline" step and `character-model.md` roadmap #2 down to the exact composition. Nothing here runs at sim-time — a baseline is built once, then `state-engine.md` moves it.

## What a baseline IS — and the content/model line it must respect
A baseline is the character's **resting configuration**, in two coupled halves (`character-model.md`'s content/model split, made generative):

- **Content** — the descriptive who-they-are: trait means + variability (`trait-theory.md`), **temperament** (the Panksepp primaries' resting levels — `state-engine.md` tier 1), the drive/wound set, the seeded vault, relationship priors. Distributional, not point (mean + variability per vector).
- **Baseline Model** — the character's *own* Layer-10 priority structure: their **weighting over the worth menu** (loyalty 0.9, fairness 0.4 — value-weights live in 10, not in Layer 2; `decision-engine.md`) + their default *what-wins-when-drives-collide*.

**Both are generated from the formative stack below.** The distinction that prevents a bug: the **archetype "models"** of `character-model.md` are **presets/overlays over the *Model* half** — a fast way to assign or vary the Layer-10 priority — **not** the baseline itself, and they **bias, never set** content (a model is "trust ×0.6 toward strangers," never "trust = 0.3"). So: *generation produces the whole baseline (content + baseline-Model); archetype-models are how you shortcut or test-vary the Model half.* Keep that straight or "same content, different model" becomes incoherent.

## The composition — species prior ⊕ genetics ⊕ formative stack

> **The MECHANISM that evaluates this equation is `composition-pass.md`** (2026-08-22): the LLM
> classifies which formative profiles a backstory matches and how strongly, the script does the
> arithmetic, and proposals grow a shared library through an admission gate. Unbuilt — status in
> `SPEC-LEDGER.md`.

A baseline is built by **sparse bias from a grounded zero-point** — never typed in:

```
SPECIES PRIOR        the population-typical config for their people          (Class-B constant, from the world)
  ⊕ GENETICS         one allele per heritable axis = a genotype (the per-primary gains)  (per-character)
  ⊕ CULTURE / ERA    value-weights (→ baseline Model) + seeds the cultural vault       (formative)
  ⊕ CLASS / POSITION drives, resource-priors, role-knowledge vault-seed                (formative)
  ⊕ FORMATIVE ENV    the big shaper: disposition + relationship-priors + the wound     (formative)
  ⊕ PERSONAL HISTORY targeted diffs + vault entries, each with provenance              (individuation)
  = BASELINE  (content: traits·temperament·drives·vault·relationship-priors  +  baseline Model: value-weighting·priority)
```

**The zero-point is the SPECIES PRIOR, not "all 5s."** The neutral start is the population-typical config for their people — for humans, the empirical central tendencies the personhood science gives (HEXACO standardized means, the primaries' typical resting levels, Schwartz modal weighting). **The world supplies it:** each people's prior is fixed at world-creation (origin-of-peoples — `history.md` / `universal-law.md`); a non-human people gets its own. So even the zero-point traces to the world, never to a guess.

**Genetics is a combinatorial preset draw** — one **allele** per heritable **axis** (the tuple = a genotype), each allele a small buff/debuff pack on the primaries' *gains*. The allele sets the mean; `trait-theory.md`'s variability gives within-allele spread; perturbation jitters it so same-genotype people aren't clones. Seeded-random for background/supporting; authored for principals. **Detailed below** — it's the layer that makes 10 strangers react differently to the same betrayal.

**The formative layers are sparse diffs, broad → specific** (culture → class → environment → personal history). Each biases the vectors it touches, leaves the rest at prior, and they **accumulate** (a street-raised war-survivor stacks both — additive + clamped; formative influences compound, they don't overwrite). Culture/era and the value-laden layers write to the **baseline Model** (Layer-10 weighting); environment/history write mostly to **content** (temperament, traits, the wound, the vault).

**Every baseline number carries provenance** — *why* it has that value, traced to the layer/event that set it ("FEAR-temperament high → the raid, age 9"). A number you can't trace to their life is the **arbitrary insert the design rejects** (`world-model.md` grounding). Provenance does double duty: it **seeds the vault** (they remember the raid; the `{thought}` draws on it).

## Genetics — the combinatorial preset layer (the ⊕ GENETICS term, detailed)
Genetics is **discrete, controllable presets** ("constants we control," applied to temperament) — but **combinatorial, not 1-of-N monolithic**, because monolithic collides.

**Why not monolithic 1-of-N.** One whole preset per person, small N → 10 people **share presets** (pigeonhole); with the same species baseline and no history yet, a shared preset = **identical betrayal reaction**. Making 10 reliably differ monolithically needs N ≈ 100+ (birthday problem) — heavy to author, and flat.

**The fix — genotype = one allele per heritable AXIS.** ~5–6 **axes** (heritable temperament dimensions), each ~3–4 **alleles** (low / typical / high / …). A character draws **one allele per axis**; the tuple is their **genotype**. Authoring is **linear**, variety is **exponential**:

| axes × alleles | authored pieces | genotypes | P(10 people all distinct) |
|---|---|---|---|
| 5 × 3 | 15 | 243 | ~0.83 |
| 6 × 3 | 18 | 729 | ~0.94 |
| 5 × 4 | 20 | 1024 | ~0.96 |

**Light per-character perturbation** (`character-model.md`) jitters allele centers, closing the residual collisions → effectively always distinct. Still "one genotype per entity," still named and inspectable.

**The axes (grounded in heritable temperament — Class-B from the behavioral-genetics literature, not invented):**
| Axis | Biases (the gains) | ~maps to |
|---|---|---|
| **Threat-reactivity** | FEAR-system gain, startle, anxiety-proneness | BIS / Neuroticism |
| **Approach / drive** | SEEKING gain, reward-pursuit | BAS / Extraversion |
| **Affiliation / attachment** | CARE + PANIC-GRIEF baseline, bonding style (secure/anxious/avoidant) | Agreeableness / attachment |
| **Anger-proneness** | RAGE-system gain, irritability threshold | (low) Agreeableness |
| **Effortful control** | regulation — how much affect reaches action | Conscientiousness / constraint |
| *(opt.)* **Sensitivity** | how deeply stimuli register | sensory-processing-sensitivity |

**Each allele is a buff/debuff pack on the primaries' GAINS — which is exactly `state-engine.md`'s `trait_sensitivity` term. Genetics IS where trait_sensitivity comes from.** So one appraised event scales differently per genotype.

**The betrayal trace (baseline + genetics only — no history; the test):** betrayal appraises to base `{RAGE↑, PANIC-GRIEF↑, trust↓}`; the genotype scales it —
- **high anger-proneness** → RAGE dominates → explosive confrontation;
- **anxious-attachment + high reactivity** → GRIEF/PANIC dominates → devastation, can't let go;
- **avoidant + high effortful-control** → muted + regulated → cold, deliberate distancing;
- **low reactivity + high approach** → shrugs, reframes, moves on.

Same event, four genotypes, four reactions — from baseline + one genotype each. **How many, precisely: ~5–6 axes × 3–4 alleles** (≈15–24 authored allele-packs) — enough that 10 strangers reliably diverge while staying controllable. (History then layers *more* on top.)

## Depth by role (who gets the full pass)
- **Principals — authored BACKWARD, validated FORWARD** (`design.md`, `character-model.md`): start from the baseline the story needs → find the species/genetics/formative stack that *forward-produces* it → run the composition and confirm it yields the target. If it can't, they're an arbitrary insert → add the justifying history to the world, or change the character. Numbers are **chosen, then earned**.
- **Supporting — forward from a formative-profile preset** (a bundled stack: "guttersnipe," "cloistered scribe") + an archetype-model + light individuation.
- **Background — species prior + position + perturbation.** No history.

(Perturbation jitters preset instances so same-preset characters aren't clones — `character-model.md`.)

## What it feeds
- **`state-engine.md` tier 1** — the baseline temperament is exactly what current-state **decays toward** and appraisal **diffs from**. (No baseline → nothing for the state engine to move.)
- **The archetype-model overlay** (`character-model.md`) — assigned on top of the baseline Model (curated for principals, random for background).
- **The vault** (`knowledge-model.md`) — seeded with the provenance entries.

## Open questions (calibration / authoring — not structure)

> **#1 and #2 are ANSWERED in `reference-species-prior.md`** (2026-08-22) — the species prior for
> every field with a per-row provenance tag, a starter single-axis formative-profile library, and
> a composition cap for #3. The seven resting means are flagged there as the softest numbers in
> the set. They are left listed below because the ANSWERS are calibration starts, not settled
> values, and the question is what gets re-asked when one is falsified.

1. **Species-prior numbers** — the human prior's actual values (HEXACO means standardized; primaries' resting levels + Schwartz modal weights set from the literature). Class-B calibration.
2. **Formative-profile library** — which named stacks to author, and their diffs — single-axis first (`character-model.md` discipline).
3. **Composition caps** — how stacked formative diffs clamp, so a multiply-traumatized character doesn't saturate every primary.
4. **Genetics variance width** — how much innate spread within a species (how different siblings can be).

## Cross-links
- **Extends:** `design.md` Phase B, `character-model.md` roadmap #2 + content/model split.
- **Feeds:** `state-engine.md` (baseline = tier 1), `knowledge-model.md` (seeded vault), the archetype-model overlay.
- **Grounds in:** `world-model.md` (formative coupling; species prior from origin-of-peoples), `trait-theory.md` (mean + variability), `values-and-stakes.md` (the worth menu the Model weights).
