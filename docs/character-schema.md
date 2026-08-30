# Character Schema — the consolidated stat block (WORKING)

**Status: working.** The one place that lists **every value a character carries**, organized by the timescale that changes it. This is the artifact `character-model.md` flagged as missing ("have the anatomy, not the schema") — the synthesis of the whole character system into a concrete stat block + DB shape. Each field points to the doc that defines its mechanics; this doc is the **index + the DB contract**, not new mechanics.

## Organized by TIMESCALE (the load-bearing split = the DB design)
A character's state lives on three clocks: set-once, shifts-slowly, mutates-each-turn. The split *is* the database: a slow **character sheet** + a fast **state row** + values computed on read.

### FIXED — set at generation, ~immutable (the substrate)
| Field | What | Defined in |
|---|---|---|
| `id, name, role_tier` | identity; principal / supporting / background (sets depth) | `character-model.md` |
| `people` | species → the species prior (the zero-point) | `baseline-generation.md`, `history.md` |
| `position` | place · class · era · niche | `design.md` Phase B |
| `genotype` | one allele per heritable axis (threat-reactivity · approach · affiliation · anger-proneness · effortful-control · sensitivity) → the per-primary **gains** (`trait_sensitivity`) | `baseline-generation.md` |

### BASELINE — set at generation; shifts only via the arc engine (durable, slow)
| Field | What | Defined in |
|---|---|---|
| `temperament` | the 8 primaries' resting levels — each `{mean, variability}` | `state-engine.md` (tier 1), `generative-model.md` |
| `traits` | HEXACO facets — each `{mean, variability}` | `trait-theory.md` |
| `model` | Layer-10 weighting over the worth menu (Schwartz + Moral Foundations + needs + locus) **+** resolution-priority | `decision-engine.md`, `values-and-stakes.md` |
| `drives` (baseline) | goals `{priority, satisfaction}` · fears/wounds `{trigger, avoidance}` · orientation `{locus, coping}` | `drives-schema.md` |
| `skills` | leveled (combat, lore, insight, perception, persuasion, streetwise…) → gate checks | `relevancy-gate.md` |
| `relationship_priors` | default trust/affinity by in-/out-group | `relationships.md` |
| `voice` | speech profile — register · vocabulary domains · rhythm · assertiveness · tics · code-switch contexts | `voice.md` |
| `provenance` | per baseline value: the formative source ("why it's that value") | `baseline-generation.md` |

### CURRENT STATE — mutable per turn (the volatile body)
| Field | What | Defined in |
|---|---|---|
| `affect` | the 8 primaries' **live** activation (current_A) | `state-engine.md` (tier 2) |
| `condition` | energy · allostatic_load · health · fatigue · injuries | `relevancy-gate.md` (energy), `character-model.md` |
| `active_goals` | currently-salient goals + urgencies | `drives-schema.md` |
| `relationships` | per-target edges `{trust, affinity, respect, debt, history}` | `relationships.md` |
| `vault` | belief store — `{claim, believed-value, provenance, timestamp, confidence}` | `knowledge-model.md` |
| `zone` | psych zone (hyper / optimal / hypo) | `character-model.md` (prior art) |
| `location` | where they are now / present scene | `world-state-ledger.md` |

### DERIVED — computed each turn, never stored
| Field | Computed as | Defined in |
|---|---|---|
| `effective_levers` | `affect × catalog(active conditions)`, clamped | `decision-engine.md`, `state-engine.md` |
| `effective_skills` | baseline skill × state/condition modifiers | `state-engine.md` |
| `severity(event)` | `damage-potential × hit-probability × context` (+ menu-violation for social) | `state-engine.md`, `values-and-stakes.md` |
| `resilience(event)` | derived on read, never stored: `effortful_control` (genotype) × attachment-security (priors + a current secure bond) × condition (allostatic load inverts) × meaning-frame availability (Model coherence for the event-class) | `arc-engine.md` |

## The three clocks ARE the write-paths
- **FIXED** — written once at generation; never moves.
- **BASELINE** — written at generation; moved only by the **arc engine** (durable diffs from trauma / eudaimonic events).
- **CURRENT** — one write-path per turn: events reach `current` **only via the consolidation loop** (the sole event source); the engine then computes the write as **appraisal** (spikes) + **decay** (relaxation). Consolidation supplies; appraisal/decay compute; nothing writes `current` around that path. *(Reworded 2026-06-10 — audit B3: the earlier phrasing named appraisal and the consolidation loop as if rival writers.)*
This is the engine's DB design directly: a slow **character sheet** (fixed + baseline) + a fast **state row** (current) + **derived** values computed on read. The consolidation-fed engine pass is the only writer of `current`; the arc engine the only writer of `baseline` post-generation.

## Depth by role (fill the schema to the character's tier)
- **Principal** — every field, deep (full drives, vault, provenance, fine traits).
- **Supporting** — genotype + position + an archetype-model + light drives/skills; thin vault.
- **Background** — genotype + position + archetype; no vault, no provenance.
The value-granularity rule (`design.md`) applied to the schema itself: fill to what the book levers on; the rest stays at class-default.

## Prior art
The mutable half mirrors the prior-art character-state record restated in full in
`character-model.md` — take its STATE fields from there (psych zone, allostatic load,
relationships, voice, interiority); this schema adds the structured **genotype · Model · drives · skills · provenance** the realism engine needs on top.

## Note
These are **runtime builds** (`design.md`): the schema (this doc) is authored once as machinery; the line items fill during generation (`baseline-generation.md`) and the sim (`state-engine.md` / `arc-engine.md` / `consolidation-loop.md`). This doc defines the *shape*; it never holds a character's content.
