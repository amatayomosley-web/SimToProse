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
| `genotype` | one `{hit, hold}` cell per PATH (2026-09-10): **hit** = the gain `g` on a reading, **hold** = a multiplier on the path's half-life. Word = preset, number = authored. Where they REST is not genotype — see `temperament` below; a `rest` inside a cell is refused (`GENOTYPE_REST_MOVED`). `src/engine/heritable.py` | `baseline-generation.md`, `emotion-arithmetic.md` §3 |

### BASELINE — set at generation; shifts only via the arc engine (durable, slow)
| Field | What | Defined in |
|---|---|---|
| `temperament` | where each of the 9 paths RESTS — each `{rest, mean}`. **`rest` is AUTHORED, as a word** (`quiet \| low \| raised \| high` = rung 1..4, capped per path — `heritable.REST_CAP`) or a number, beside the voice and traits: a character-design choice (owner, 2026-09-10). `mean` is seeded from the word once (`heritable.ensure_temperament`) and stored because the arc engine writes durable diffs into it. The actor is told the rest as a sentence under `disposition` (`identity_view._REST_PHRASES`) | `state-engine.md` (tier 1), `heritable.py`, `BLUEPRINT-character.md` Part Three |
| `traits` | HEXACO facets — each `{mean, variability}` | `trait-theory.md` |
| `model` | Layer-10 weighting over the worth menu (Schwartz + Moral Foundations + needs + locus) **+** resolution-priority | `decision-engine.md`, `values-and-stakes.md` |
| `wounds` | ENGINE STATE (gate three, 2026-09-11) — `[{id, concept, path, intensity, source, text, trigger}]`, id = concept@PATH; minted by `scripts/composition_pass.py` from a formative profile (source `profile:<id>`) or by a run from a durable beat (source `run:<turn>`, a `wound_minted` row); never hand-written (lint refuses). The wound's intensity is the character's INVESTMENT in that concept on that path (`connection.for_about`); the actor reads it as "what has marked you" | `wound.py`, `concepts.py`, `emotion-arithmetic.md` §3 |
| `drives` (baseline) | goals `{priority, satisfaction}` · ~~fears/wounds~~ (moved to `wounds`, 2026-09-11) · orientation `{locus, coping}` | `drives-schema.md` |
| `skills` | leveled (combat, lore, insight, perception, persuasion, streetwise…) → gate checks | `relevancy-gate.md` |
| `relationship_priors` | the stranger's rest (`default_trust`) and the per-witness rates (`update`); `in_group` retired 2026-09-18 — see `current.attachments` | `relationships.md`, `bond-arithmetic.md` s3 |
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
| `resilience(event)` | derived on read, never stored: condition (allostatic load inverts) × attachment-security (priors + a current secure bond) × meaning-frame availability (Model coherence for the event-class). The `effortful_control` term was CUT with the primitive-era genotype 2026-09-10; its weight is renormalised onto the other two until an axis returns (`arc.py`) | `arc-engine.md` |

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
