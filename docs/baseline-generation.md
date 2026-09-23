# Baseline Generation — where every per-character number is born (WORKING)

**Status: working.** The keystone. The engine runs on per-character values and they are *all* born here, once, at character creation. This specifies `design.md` Phase B's "baseline" step and `character-model.md` roadmap #2 down to the exact composition. Nothing here runs at sim-time — a baseline is built once, then `state-engine.md` moves it.

## What a baseline IS — and the content/model line it must respect
A baseline is the character's **resting configuration**, in two coupled halves (`character-model.md`'s content/model split, made generative):

- **Content** — the descriptive who-they-are: trait means + variability (`trait-theory.md`), **temperament** (where each path rests — a WORD per path authored beside the voice since 2026-09-10; `state-engine.md` tier 1 decays toward the mean seeded from it), the drive/wound set, the seeded vault, relationship priors. Distributional, not point (mean + variability per trait vector).
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

**The formative layers are sparse diffs, broad → specific** (culture → class → environment → personal history). Each biases the vectors it touches, leaves the rest at prior, and they **accumulate** (a bakehouse foundling who survived a flood stacks both — additive + clamped; formative influences compound, they don't overwrite). Culture/era and the value-laden layers write to the **baseline Model** (Layer-10 weighting); environment/history write mostly to **content** (temperament, traits, the wound, the vault).

**Every baseline number carries provenance** — *why* it has that value, traced to the layer/event that set it ("FEAR-temperament high → the flood, age 9"). A number you can't trace to their life is the **arbitrary insert the design rejects** (`world-model.md` grounding). Provenance does double duty: it **seeds the vault** (they remember the flood; the `{thought}` draws on it).

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

**The cells (REBUILT 2026-09-10 — owner: "the genotype is the starting vectors, then we assign the allele and then we assign the decay").** The six primitive-era axes (threat-reactivity, approach, affiliation, anger-proneness, effortful control, sensitivity) were a rename of Panksepp's table and are RETIRED; the engine refuses them (`GENOTYPE_OLD_AXES`). A genotype is now one cell per PATH, its fields drawn INDEPENDENTLY — and independently of where the person rests, which left the genotype the same day (owner: *"have temperament be a character design question, along with their voice and other personality options"*) so a character can rest calm and hold fear for weeks:

| cell | what it sets | words | where it lands |
|---|---|---|---|
| **hit** | how hard a reading lands — the gain `g` | `low` / `typical` / `elevated` / `high` | `fixed.genotype[path].hit` → `f <- f + v_k * g` (`emotion-arithmetic.md` §3), the only per-character term in the accumulation rule |
| **hold** | how long an excursion is kept | `brief` / `typical` / `long` / `lasting` | `fixed.genotype[path].hold` → a multiplier on the path's HALF-LIFE, `r_eff = r_path ** (1/hold)` — the same ratio on every path under any per-path law authored later |
| *rest* — NOT a genotype cell | the starting vector — where the float sits when nothing is happening, and what decay relaxes toward | `quiet` / `low` / `raised` / `high` = rung 1..4, **capped per path** at the last rung that reads as a disposition (STIRRING 3 · WARINESS 5 · DISPLEASURE 4 · GOODWILL 5 · DEFLATION 4 · DISTASTE 2 · RECEPTIVITY 5 · SELF-REGARD 4) | **`baseline.temperament[path].rest`, AUTHORED beside the voice** (a design choice, `BLUEPRINT-character.md` Part Three); the `mean` beside it is seeded from the word once (`heritable.ensure_temperament`) and the arc engine moves it after. Drawn (`make_genotype.draw_rest`) only for people nobody authors |

A word draws the preset; a NUMBER is used exactly as authored (rest: the mean; hit: `g`; hold: the factor). An authored rest above the cap is honoured and `lint_book` warns naming the rung; a `rest` inside a genotype cell is refused by name (`GENOTYPE_REST_MOVED`). **The preset VALUES are the conservative START** — `heritable.GAIN` / `PERSIST` carry the primitive-era numbers, adopted 2026-09-10 and tuned in real runs; `scripts/derive_genotype.py` is a tool for that loop and `tests/test_genotype_balance.py` guards reachability and rank order. Rest × hit × hold per path is 32..80 combinations; the whole space is ~2e14, so ten drawn strangers never collide.

**The hit cell IS `state-engine.md`'s `trait_sensitivity` term, alone.** The HEXACO slopes that used to bump it were cut as a second source of `g`; traits reach no engine arithmetic now (recorded dead vector).

**The betrayal trace (baseline + genetics only — no history; the test):** betrayal appraises to base `{DISPLEASURE↑, DEFLATION↑, trust↓}`; the genotype scales it —
- **DISPLEASURE hit high** → anger dominates → explosive confrontation;
- **DEFLATION hit high + hold lasting** → the loss dominates and does not lift → devastation, can't let go;
- **GOODWILL hit low, DISPLEASURE hold brief** → muted, over quickly → cold, deliberate distancing;
- **WARINESS hit low + STIRRING hit high** → shrugs, reframes, moves on.

Same event, four genotypes, four reactions — from baseline + one genotype each. **How many: 8 paths × (rest ≤ cap × 4 hit × 4 hold)** — 32 to 80 combinations per path, ~2e14 across the sheet — enough that 10 strangers reliably diverge while staying controllable. (History then layers *more* on top.)

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
