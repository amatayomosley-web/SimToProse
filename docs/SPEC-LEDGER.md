# SPEC-LEDGER — every specified mechanism, against the code that does or does not implement it

**What this is.** The doc-vs-code reconciliation. Four separate times in one session a mechanism
was designed or rebuilt from scratch that a doc already specified in detail (§"The four incidents"
below); `docs/MAP.md:3-9` records an earlier session doing the same to the buff/debuff registry.
This file exists so that "is X built, and does it match the spec?" is one lookup, not a re-read of
56 docs.

**How it was made (2026-08-22).** Every doc in `docs/` read in full; every `built?` verdict
established by grep of `src/`+`scripts/`+`tests/`+`.claude/` or by running code — never by trusting
a doc's own status line (`state-engine.md:10-12` marked the effective-levers tier "done" for months
while it had zero lines of implementation). Test ground truth at review time: the repo's own
verify suites all pass run script-style (`python tests/test_X.py` — 18 suites green including
`test_effective.py`, `test_laws.py`, `test_orc_hooks.py`; `coherence_probe.py --stub` PASS).
Note: `pytest tests` mass-errors on a missing `con` fixture — an artifact of the script-style
harness, not failures.

**Divergence column vocabulary:**
- **SPEC-ONLY** — documented, no code implements it.
- **BUILT-AS-SPEC'D** — code matches the doc's mechanism.
- **BUILT-DIFFERENTLY** — code exists but departs from the spec; the departure is named.
- **DOC-STALE** — the doc describes something the code no longer does (or miscounts what exists).
- **PARTIAL** — a named subset is built; the rest is spec-only.

**Maintenance.** A row goes stale the moment its mechanism is built or its doc revised. When you
build something listed SPEC-ONLY here, flip the row in the same commit. Line numbers are as of
2026-08-22; prefer the cited symbol name if a file has shifted.

---

## The four incidents, checked (do not trust them — verified here)

1. **Lever/buff-debuff registry** — **CONFIRMED.** `decision-engine.md:61-113` fully specifies the
   catalog (`{trigger condition, affected lever, op, magnitude, source}` at :94, the effective
   formula at :101, guardrails :107-111, the falsification test :113). `MAP.md:5-8` records a prior
   session rebuilding a worse version under the coined word "vectors". Built 2026-08-22 as
   `src/engine/levers.py` (all four condition kinds :163-209), wired at `scene.py:127-141`,
   staged into the prompt at `prompt.py:41-46`, proven by `tests/test_effective.py`.
2. **Emotion-vector origin "cited by path"** — **HALF WRONG, substance right.** The current
   `decision-engine.md` does NOT cite the origin doc by path: it deliberately *inlines* the model —
   :62-63 "both restated here so this section stands alone", the borrowed formula verbatim at :69
   (`emovec = emovec_mat + (1 − sum(weight_vector)) × speaker_baseline`). So rederiving it from
   memory was worse than the claim states: the formula needed no external doc at all, one section
   away. The only by-path reference to an `emotion-vectors.md` in this repo is
   `goal-alignment-review.md:271` (a lineage note; the file itself lives outside this repo). The
   sum-dial is now implemented in `compounds.py:248-296` (`recipe_sum`, `blend`).
3. **Genotype purpose + combinatorics** — **CONFIRMED.** `baseline-generation.md:28` states the
   purpose verbatim ("it's the layer that makes 10 strangers react differently to the same
   betrayal"); :39-47 gives the axes×alleles arithmetic and the distinctness table; :49-57 the six
   axes; :59 the identity "Genetics IS where trait_sensitivity comes from" — which is exactly
   `state.py:268-296`.
4. **Appraisal dimension set** — **CONFIRMED.** `state-engine.md:21-22` specifies OCC/Scherer
   dims (goal-congruence · agency · certainty · **control** · norm-violation) and :24-30 a
   CONJUNCTIVE mapping ("blocked goal **+** other-agency → RAGE"). Shipped `state.py:53-70`
   `_DIM_TO_PRIMARY` uses six outcome-class dims (threat/loss/care_relevant/mastery/
   social_violation/relief), each an independent additive push-vector; no agency, no certainty, and
   `control` — which :38 says answers "same blade, different fear, by their skill" — appears
   nowhere (the only "control" in `state.py` is `effortful_control`, a decay-rate input). The
   whole severity factoring of :34-39 (damage-potential × hit-probability × context, defender
   skill filling `control`) is explicitly deferred (`state.py` appraise docstring: "severity =
   the raw dimension magnitude").

---

## THE LEDGER

### Emotion basis & compounds

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Seven Panksepp primaries as the state vector | `generative-model.md:8-16`, `state-engine.md:14` | YES | `records.py:10` `PRIMARIES` | BUILT-AS-SPEC'D |
| **DISGUST as the eighth primitive** (normative, settled 2026-08-22) | `emotion-basis.md:24-43` | **YES (built 2026-08-22)** | `records.py` PRIMARIES is 8 (DISGUST LAST — `compounds._vector` indexes by position); reached from `social_violation` 0.28 and `threat` 0.08; `_DECAY_RATE` 0.88 (slowest but PANIC_GRIEF); four direction phrases; species prior 0.15; suite `tests/test_disgust.py` | BUILT-AS-SPEC'D. 16 compounds went live and `goal-alignment-review.md`'s "**cold contempt is unrepresentable as state**" is retired — measured: three violations take DISGUST 0.150 -> 0.534 and stage as *"you keep a little more distance than the moment needs"*. Unblocking exposed a duplicate the block had hidden: `sarcastic` at cosine 0.996 to `mocking`, removed as a delivery REGISTER rather than a feeling. No new appraisal DIMENSION was added |
| Compound vocabulary: `{primitive: (weight, role)}` recipes, compose/recognise/separability | `emotion-basis.md:56-70`, `emotion-recipes.md` (generated) | YES | `compounds.py` `COMPOUNDS` (41 recipes), `compose` :187, `recognise` :217, `separability` :246; `tests/test_compounds.py` | BUILT-AS-SPEC'D as a module — but **zero runtime consumers**: nothing in `state/direction/prompt/scripts` calls it. A read-back vocabulary, not yet a pipeline stage |
| The sum as identity dial (`blend` = recipe + (1−sum)×baseline) | `decision-engine.md:66-79`, `emotion-recipes.md:15-25` | YES | `compounds.py:248-296` | BUILT-AS-SPEC'D (module-level; unconsumed at runtime) |
| Per-primary TARGETS on live state (`{primitive -> (magnitude, target)}`; `_regard` per-primitive) | `emotion-basis.md:72-99` (:93 "a change to what exists") | **YES (built 2026-08-22)** | `records.DIRECTEDNESS` (the 8-row registry) + `records.admits_role`; `targets.retarget` (5 binding rules); `state.appraise(..., targets=)` evaluates `_regard` per primitive; `direction._phrase_for` picks the reflexive variant; `compounds.validate()["drift"]` enforces the registry downstream; suite `tests/test_targets.py` | BUILT-AS-SPEC'D. Targets live in a SIBLING field (`current.targets`), not fused into affect as tuples — magnitude decays every beat and a target never does, and this project splits fields by lifetime everywhere. **READER-verified 2026-08-23** (`basis-verification.md` §10): same numbers (DISGUST 0.556, RAGE 0.572), only the target flipped, and blind judges recover shame from contempt at **11/12** — 12/12 for pursuit vs display, 23/24 pooled against a pre-registered threshold of 18/24, with a 12/12 positive control and a clean bias floor. `tests/test_targets.py` asserts the strings DIFFER; this measures that the difference is LEGIBLE. Took four runs — the first three could not reach the question and are recorded in §9 rather than discarded. The spec's own example works: fear stays on the wolf while rage moves to the man who let it in. Registry reasoned by Fable from what each Panksepp system makes a body do, NOT from the compound table — and following that rule caught 5 recipes that had already drifted FROM the basis |
| Tense via targets + vault `timestamp` | `emotion-basis.md:101-132` | NO | `vault.py:30-80` parses claim/confidence/provenance/links; `timestamp` dropped (also `guide-content.md:50`) | **SPEC-ONLY** — schema field authored, never parsed; the named prerequisite |
| LUST reachable by some appraisal dimension | `emotion-basis.md:136-140` (flagged blocking) | **YES (built 2026-08-22)** | seventh dimension `attraction` in `state._DIM_TO_PRIMARY` (LUST 0.45, SEEKING 0.18, PLAY 0.10), relevance via hedonism/relatedness/stimulation, admitted on the `bond` and `mundane` CATALOG entries only | BUILT-AS-SPEC'D. It needed its OWN dimension: none of the six was about desire, and reaching LUST from `care_relevant` would make every act of tenderness push attraction — the conflation a separate primitive exists to prevent. Measured: 0.200 -> 0.394 over three beats. **Deliberately NOT admitted on threat / harm / seize / threaten** — coercion is a real subject a book may need and must be authored as the violation it is, not reached through a dimension the engine hands out on threat events. `tests/test_disgust.py` now asserts EVERY primitive is reachable, so the next basis element cannot repeat this |
| Basis verification procedure (blind vocabulary, 3 signatures, confusion matrix) | `emotion-basis.md:148-177` | PARTIAL | `separability()` = the deterministic half; blind-judge render pass not run | PARTIAL |

### State engine (tiers 1–2)

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Three-tier state (temperament / current / effective) | `state-engine.md:5-16` | YES | tiers 1-2: `state.py`; tier 3: `levers.py` (built 2026-08-22) | BUILT-AS-SPEC'D **now**; the doc's own status column (:10-12, "done") described tier 3 as done for ~2 months while unbuilt — the trap this ledger exists for |
| Appraisal dims + dim→primary mapping | `state-engine.md:21-30` | YES, differently | `state.py:53-70` | **BUILT-DIFFERENTLY** — outcome-class dims, additive vector pushes, no conjunctions, no agency/certainty/`control` (incident #4 above) |
| Severity factoring for wielded threats (damage-potential × hit-probability × context; defender skill → `control`) | `state-engine.md:34-39` | NO | severity = raw self-tagged magnitude (`state.py` appraise docstring) | **SPEC-ONLY** (explicitly deferred; no world object model to read from) |
| Relevance = event dims × the character's Model weights ("where two people diverge") | `state-engine.md:40`, `values-and-stakes.md:24-33` | YES | `_DIM_VALUE_KEYS` `state.py:125-144`, `_relevance` :267-240; missing key = neutral 0.5 | BUILT-AS-SPEC'D |
| trait_sensitivity = genotype gains × HEXACO slopes | `state-engine.md:41`, `baseline-generation.md:49-59` | YES | `state.py:268-296` (`_ALLELE` :28-31; emotionality/agreeableness/extraversion slopes :169-183) | BUILT-AS-SPEC'D — 3 of 6 traits slope gains; the rest ride the prompt as context (`character-authoring-rules.md` Rule 5 documents this honestly) |
| Decay toward temperament, per-primary rates, regulation-scaled | `state-engine.md:45-47` | YES | `state.py:100-118` (FEAR .72, GRIEF .90), `decay()` :410-467 | BUILT-AS-SPEC'D. Consequence measured 2026-08-22: decay+mean cap current-state at `mean+(1−mean)r` (`goal-alignment-review.md:199-256`) — correct for tier 2, and the reason tier 3 had to exist |
| Subject-regard empathy scoping (bigotry floor 0.25; affinity lifts, never lowers) | no design doc owns it — `guide-emotional-authoring.md:110-115`, `driving-the-engine.md:14` | YES | `state.py:150-158` (`_CARE_FLOOR`, `_REGARD_SCALED_DIMS`), `_regard` :245-221; runtime subject resolution `scene.py:349-390`; proven `tests/test_subject.py` | BUILT (code-first; guides document it; no `docs/` design doc is its owner) |
| Event-vs-condition rule (appraisal fires on the change; catalog on the standing fact) | `state-engine.md:49-54` | YES | `levers.py:129-131` comment + `scene.py:122-126`; both fire | BUILT-AS-SPEC'D |

### Effective levers (tier 3) & the decision

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| **Buff/debuff registry** (`{when, lever, op, magnitude, source}`; `effective = current × Π(mult) + Σ(add)`, clamped) | `decision-engine.md:61-113`, `state-engine.md:56-57` | YES (2026-08-22) | `levers.py:70-111` (`effective`), :212-235 (`active_rows`); authored per-character as `baseline.catalog.rows`; validated by `lint_book.py:163`; `tests/test_effective.py` | BUILT-AS-SPEC'D — all four condition kinds from the doc's worked entries (`percept`, `present_edge`/`target_edge`, `affect_at_least`, `condition_at_most`), rows AND together, no-`when` = standing trait |
| Tier 3 wired into the acting path | `state-engine.md:12` ("what the decision actually sees") | YES | `scene.py:127-141` computes `volatile.state.effective` + `volatile.levers`; `prompt.py:41-46` stages direction FROM effective; fired rows land in the manifest (`scene.py:158`) | BUILT-AS-SPEC'D for the prompt path. NOT swapped at two display/salience call sites: the chair's status line (`scripts/direct.py:332-333`) and the scene-runner's `_salience` (`scripts/scene.py:107-115`) still read the current tier |
| Registry conditions can fire on event WORDS (a `percept: ["spider"]` row) | `decision-engine.md:96` (perception-fired entry) | YES | `levers.py:170-176` matches `when.percept` against raw event text | BUILT-AS-SPEC'D — note this matches EVENT TEXT directly, side-stepping the recall gate's class-name trigger gap (next section) |
| No code-side argmax; LLM resolves; margin = act intensity | `decision-engine.md:5-7,103,115-134` | YES / PARTIAL | no argmax anywhere (grep); the **margin** is never computed and direction clauses come in fixed `PRIMARIES` order with no salience ranking (`direction.py:117-131`, `records.py:10`) | PARTIAL — resolution is narrative as spec'd; the "margin → intensity" and clause-ordering half is SPEC-ONLY |
| Hard gates (knowledge presence, energy floor, capability, absolute lines) | `decision-engine.md:49` | YES | DCs `gate.py:40-42`; energy budget `gate.py:47`; combat capability `consolidation.py` CATALOG `capability_req`; absolute value lines: none authored | BUILT-AS-SPEC'D (the deterministic few) |
| Explicit-weighing thought ("name the competing pulls") | `decision-engine.md:54` | YES (2026-08-22) | `prompt.py:66-68` | BUILT-AS-SPEC'D (was missing at the goal-alignment review hours earlier) |
| Critic verifies action-vs-injected-state | `decision-engine.md:56`, `measurement.md:14-16` | NO | `scripts/critic.py:62-74` asks continuity + voice only | **SPEC-ONLY** — the third consistency guardrail has no checker |
| Optional utility pre-rank (propose/dispose hybrid) | `decision-engine.md:58-59` | NO | — | SPEC-ONLY (doc marks it optional) |

### Numbers → words (gate 5)

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Direction layer: digit-free bands, stage-direction phrasing, deviation-vs-temperament markers | `design.md:87`, `state-engine.md` | YES | `direction.py` (bands :16, phrases :24-53, `direct_affect` :249-134); digit-free proven `tests/test_direction.py` | BUILT-AS-SPEC'D — the strongest module (`goal-alignment-review.md:314-317`) |
| **"Numbers never reach the prompt"** | `design.md:87` ("The LLM never sees raw stats") | **YES (built 2026-08-22)** | `identity_view.direct_identity` :195 / `direct_goals` :269 / `direct_percepts` :277 (split out of `direction.py` on the identity/affect seam); `prompt.py` renders instead of dumping; guard `tests/test_no_digits.py` | BUILT-AS-SPEC'D. The leak was MEASURED at 13 floats before the fix. Guaranteed **by construction**, not by the test — but the construction is a BAND, not a refusal, and the difference cost two rounds. Draft 1 silently DROPPED unknown keys and the guard came back green (worse than leaking: authored content vanishing with nothing said). Draft 2 refused any number it had no phrase for and **took down 2 of 3 real books** — a novel authored field is not a defect. Shipped: `identity_view.py` `_say_scalars` :166 gives a known key its named phrase and anything else a banded generic (`identity_view.py` `_SCALAR_FALLBACK` :98); what still refuses is a number OUTSIDE [0,1], which is a scale error rather than a vocabulary gap. Two exemptions, both stated in the suite: INTEGERS (a year, an age) and the reply CONTRACT (the scale the actor reports ON) |
| Direction reads a salience order / one resolved staging line | `decision-engine.md:124` (injected as DIRECTION with margin) | NO | fixed tuple order; six parallel clauses at rest measured (`goal-alignment-review.md:108-115`) | SPEC-ONLY (ordering/margin) |

### Character generation

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Genotype: 6 axes × 4 alleles → per-primary gains | `baseline-generation.md:34-67`, `character-schema.md:14` | YES | `state.py:26-31,268-296`; seeded draw `scripts/make_genotype.py` (`--rows` emits lever rows); `tests/test_genotype.py` | BUILT-AS-SPEC'D. Allele vocabulary EXACTLY `low|typical|elevated|high`; anything else silently reads typical — now a lint ERROR (`lint_book.py:146`) |
| Species prior ⊕ culture ⊕ class ⊕ formative env ⊕ history composition | `baseline-generation.md:13-31` | **PARTIAL (2026-08-22)** | The SCRIPT half is built: `data/formative_profiles.json` (94 profiles, 8 categories, each with `baseline_diffs` + `catalog_rows` + `vault_belief_seeds`), `src/engine/profiles.py` (`compose` with the ±0.35 cap, `separability`, `admit`, and `path_for`/`prior_from`/`place` mapping every field to the nested path its consumer reads), `scripts/composition_pass.py`. Design: `docs/composition-pass.md`. Suites `test_formative_profiles.py`, `test_composition_pass.py` | **BUILT-DIFFERENTLY** — the LLM CLASSIFICATION step is still unbuilt, so picks are hand-supplied; and the species prior itself is a REFERENCE (`reference-species-prior.md`), not code. Measured end-to-end: one pick at weight 0.6 moves a temperament mean 0.450→0.522 at the path `build_profile` reads, seeds a vault belief, and places a catalog row that FIRES in `assemble` (effective FEAR 0.450→0.990) |
| Provenance per baseline number ("the raid, age 9") | `baseline-generation.md:32` | PARTIAL | `baseline.provenance` rides the stable prefix (`scene.py:205`); discipline is manual (`guide-content.md:112-117`) | PARTIAL — carried, never enforced or checked |
| Archetype models: sparse bias-packs over layers, assign+perturb, single-axis first | `character-model.md:81-115`, `baseline-generation.md:11` | NO | no model library, no overlay/perturbation machinery anywhere | **SPEC-ONLY** |
| Whole-trait `{mean, variability}`; out-of-character tail samples | `trait-theory.md:18-27,31-41`, `decision-engine.md:51` | NO (variability) | every sheet stores variability; `build_profile` reads `.mean` only (`state.py:281-283`); no distribution sampling anywhere | **SPEC-ONLY** — the distribution half is authored dead weight (`goal-alignment-review.md:296`) |
| Drives schema as structured OPERANDS (goal priority/serves chains; fear intensity/trigger; orientation) | `drives-schema.md` throughout | NO (as operands) | authored per the schema in real books; consumed as: goal TEXT → recall salience (`gate.py:288-324`) + prompt; everything else verbatim prompt JSON. `intensity`/`trigger`/`serves`/`protects`/`priority` numbers reach no arithmetic (`goal-alignment-review.md:289`); `blocked` transition logic (audit B7 "fix") in no code | **BUILT-DIFFERENTLY** — drives are prompt text, not computed operands. The built bridge: a wound gets teeth via a `baseline.catalog` row; `lint_book.py:179-183` warns on a wound trigger with no row |
| Character schema three clocks (FIXED/BASELINE/CURRENT + DERIVED never stored) | `character-schema.md` | YES | `schema.sql` characters + current_state; effective recomputed (`scene.py:137`), resilience derived (`arc.py:35-49`) | BUILT-AS-SPEC'D. Dead schema fields (stored, zero consumers, NOT doc'd as inert): `model.resolution_priority`, `fixed.role_tier`, `current.zone`, `goals[*].satisfaction`, edge `.history` (packeted then dropped at `prompt.py:49`), belief `.believed_value` (dropped at `scene.py:277-286`) — `goal-alignment-review.md:285-299`. **`baseline.relationship_priors` left this list on 2026-08-22**: `bonds.drift` reads `default_trust` as the resting point an unreinforced edge relaxes toward. |
| Voice profile GENERATED from the formative stack | `voice.md:18-19` | NO | voice hand-authored; consumed verbatim (stable prefix `scene.py:204`; narration lens `scripts/narrate.py`) | **SPEC-ONLY** (generation half; audit C2 half-closed) |
| Craft standards imported at `books/standards/` | `voice.md:25-28` | NO | `books/` is empty | SPEC-ONLY — acceptance criterion #6 explicitly unsatisfiable until import (as voice.md itself states) |

### Knowledge, vault, recall, perception

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Belief store `{claim, believed_value, provenance, timestamp, confidence}` + `## Beliefs` authoring contract | `knowledge-model.md:13`, `guide-content.md:49-63` | YES | `vault.py:22` (`_BELIEF_RE`), fail-loud on unparseable sections :74-78 (added after 41-52 of authored beliefs silently loaded as zero — `character-authoring-rules.md:8-10`) | BUILT-DIFFERENTLY in two spots: `timestamp` never parsed; `believed_value` carried by the gate then dropped at the packet |
| Acquisition during play (lived / witnessed / learned; monotonic-add; dedup) | `knowledge-model.md:17,104-110` | YES | `acquisition.py` (`assess` :22, `witness_belief` :112, `reveal_name` :63, `overheard_names` :161); persisted `ledger.py` `append_acquisition` :167; resume rehydrates | BUILT-AS-SPEC'D (channels told/taught/read/deduced not distinguished; forgetting not built — declared later-layer) |
| **Trust gates transmission** (believed fact vs discounted rumor scales with B's trust in A) | `knowledge-model.md:108`, `relationships.md:21-22` | **YES (built 2026-08-22)** | `witness_belief(..., trust=)` scales `confidence` and flips `provenance` to `reported` at/below 0.40, reframing the claim as *"X claims: …"*; `scene.py` computes the belief PER WITNESS from that witness's edge | BUILT-AS-SPEC'D. Ceiling 0.88 is calibrated against `direction._SURENESS`, which turns over at 0.90 — a second-hand account must never render as *"you do not entertain the alternative"*. Distrust is deliberately NOT routed through `believed_value` (inert — see the schema row above) |
| Talk-of-the-Town belief dynamics (confabulation/transference/mutation/forgetting) | `knowledge-model.md:112`, `prior-art.md:21` | NO | — | SPEC-ONLY (declared "+Full" tier) |
| Trigger-matching recall + goal salience + energy budget (cost = 1−confidence) | `relevancy-gate.md:9-21,34-41,99-118` | YES | `gate.py:257-360` (`run_gate`), budget `gate.py:47` = energy×(1−load/2); `[[links]]` join the match surface | BUILT-AS-SPEC'D — with one measured seam: **triggers are lexicon CLASS NAMES + event kind, not the event's own words** (`gate.py:378-391`); "spider" cannot become a trigger unless a class is named "spider" (`goal-alignment-review.md:121-127`: the spider memory surfaced on the word `boy`). Levers' `when.percept` (raw-text match) does not inherit this gap; recall still does |
| Deterministic checks, no randomness, **no director-set DCs** | `relevancy-gate.md:23-26` (B1 remediation) | YES | `gate.py:40-42,59`; no random anywhere in `src/engine` | BUILT-AS-SPEC'D — the one design-invariant violation stays dead |
| Perception-mode wall (PerceptSet whitelist; identity behind insight 0.55; subtle cues behind perception 0.60; acquaintance recognition) | `scene-assembly.md:17-21,74-97`, `relevancy-gate.md:28-32` | YES | `gate.py:90-210`; never-add structural (`test_scene` whitelist canary); known-entity bypass `gate.py:176` | BUILT-AS-SPEC'D |
| Graph recall: weighted hops, pathfinding to hinges, degree-penalty, multi-hop chains | `relevancy-gate.md:60-97` | NO | vault is FLAT by design; single-hop cost 1−confidence (`guide-engine.md:171-173` declares the reduction) | **BUILT-DIFFERENTLY (deliberate)** — the entire hop/path/DC-from-distance apparatus is spec-only behind the same interface |
| Authored hinges (director-planted checks that always surface + branch) | `relevancy-gate.md:39` (pipeline step 5) | NO | `must_surface` exists only as the event-anchor flag (`gate.py:24,144`); no hinge authoring surface, no branch mechanics | SPEC-ONLY |
| Name masking + latent-leak regeneration ("recorded as-is" preserved) | `knowledge-model.md` wall; status log `driving-the-engine.md:104-111` | YES | `gate.scope_names` :485 (prompt wall), `faithfulness.py:16-35` (output detector), `direct.py` `faithful_turn` :208-216 (regenerate → reject) ; `tests/test_faithful_turn.py` | BUILT-AS-SPEC'D |

### Scene assembly & the packet

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Deterministic 7-step assembly; no renderer; one LLM call per turn | `scene-assembly.md:5,43-50,71-97` | YES | `scene.py:37-171`; no LLM in `src/engine` (proven `test_portability`) | BUILT-AS-SPEC'D (steps 6-7 live in the harness — `direct.py:run_turn`) |
| Stable/volatile split; byte-stable cacheable prefix; `_note` stripping | `scene-assembly.md:52-67` (audit B8) | YES | `_build_stable` `scene.py:179-207`; `_strip_notes` :238-221 | BUILT-AS-SPEC'D. Cosmetic: a dead first `_sort_nested` definition shadowed by the fix (`scene.py:232-252`) |
| Excluded-by-construction (no bible wholesale, no other minds, no beat) | `scene-assembly.md:65`, `design.md:33` | YES | structural absence + `.claude/hooks/beat_blind_guard.py` (Mode-B PreToolUse deny) | BUILT-AS-SPEC'D |
| Decision-input manifest persisted per turn | `record-contract.md:13` | YES | `scene.py:147-160` (+`levers_fired`), `ledger.py:94-96` → `decision_manifests` | BUILT-AS-SPEC'D |
| Subject/group resolution (who the event is ABOUT; actor may name, engine validates) | `state-engine.md:40` relevance-includes-who; mechanics undocumented in docs/ | YES | `scene.py:349-390`; wired `direct.py:273`; proven `tests/test_subject.py` | BUILT (code-first; no owning design doc) |

### Relationships

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Directed per-perceiver multi-axis edges (trust/affinity/respect/debt) reaching the actor as banded phrases | `relationships.md:13-19` | YES | sheets → `_build_edges` `scene.py:289-333` (present-entities only) → `direct_edge` `direction.py` | BUILT-AS-SPEC'D. **No longer a static read (2026-08-22)** — `bonds` moves them per beat, gated by `bonds.witnessed` (a subtle act needs perception; pinning one on a stranger needs insight — both on gate.py's own DCs). Keys must still equal `world.people` ids |
| **Prediction-error + negativity-bias per-event edge UPDATE** ("Δ ∝ observed−expected", cliffs, value-scored, perception-routed) | `relationships.md:24-31` | **YES (built 2026-08-22)** | `src/engine/bonds.py` — `observe()` takes the CURRENT edge as the expectation, `_ALPHA_NEG` 0.30 > `_ALPHA_POS` 0.12, cliffs gated on severity AND the perceiver's relevance AND attribution, `_relevance` scoring; producers in `scene.py:_bond_moves` → `TurnCommit.rel_deltas`; suite `tests/test_bonds.py` | BUILT-AS-SPEC'D, and it fixed a DIRECTION defect the ledger had not caught: `arc.assess` ran on the SPEAKER, so a betrayal dropped the **betrayer's** trust in their victim (measured 0.80→0.7828) while the victim's edge never moved. It also had negativity bias INVERTED — resilience buffered damage, so at resilience 0.90 a kindness moved trust 6.0× further than an equal betrayal. Both are gone; `arc.py` no longer writes edges at all (`apply` still replays stored ones — rule 2) |
| **Second-order belief** ("what A thinks B feels about A") | `relationships.md:43` (rich layer) | **YES (built 2026-08-22)** | `bonds.reflect` → `edge["their_view"]`, fired only on a RECEIVED act, cliffs off; `_SECOND_ORDER_EXTRA` carries the one place the two orders read an act differently; rendered by `direct_edge` as *"and as you read them, …"* | BUILT-AS-SPEC'D. Unrequited attachment was previously unrepresentable — someone who adores a person they know to be indifferent stored exactly what someone who believes it is returned stored. The build's own test falsified its gate's frame assumption (that both orders read an act identically) and the assumption was retracted in the gate rather than the test being adjusted |
| Drift toward baseline (absence cools) | `relationships.md:30` | **YES (built 2026-08-22)** | `bonds.drift()`, wired at SCENE START in `scene.py` on an optional `cfg["elapsed"]`; per-axis retention with affinity fading fastest and debt slowest | BUILT-AS-SPEC'D beyond the declared MVP skip. Not per-beat — a beat has no duration, so drifting per beat would cool a friendship over one conversation. This is also the first runtime reader `baseline.relationship_priors` has ever had |
| Relationship-conditioned STATE (ally present → fear ×0.7) | `decision-engine.md:95-97` | YES (2026-08-22) | `levers.py` `present_edge`/`target_edge` rows incl. `_at_most` for enemies | BUILT-AS-SPEC'D — via the catalog, not via appraisal (appraisal itself has no relationship term) |

### Arc engine

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Durable-write threshold; menu-typed diffs; magnitude = impact × durability × (1−resilience) | `arc-engine.md:5-35` | YES | `arc.py:52-105` (`_ARC_THRESHOLD` 0.18); applied in-loop `direct.py:305` + scene runner; persisted `ledger.append_arc_diff`; resume replays; `tests/test_arc.py` | BUILT-AS-SPEC'D with named deltas: `durability` read from the actor's tag + severe-dim heuristic, NOT from the catalog's `durability_class` row (record-contract.md:28 assigns it there); type table subset — betrayal/violence/loss/mastery/connection built, **humiliation and meaning rows unbuilt** (humiliation needs shame/DISGUST) |
| Resilience DERIVED never stored; damage-vs-growth fork (PTG at ≥0.70) | `arc-engine.md:33-42` | YES | `arc.py:35-49` (meaning-frame term defaulted out — documented TODO), fork :86-91 | BUILT-AS-SPEC'D (3 of 4 resilience terms) |
| Backstory = pre-run arc (generation runs the same diffs) | `arc-engine.md:44-49` | NO | generation pass unbuilt (see Character generation) | SPEC-ONLY |
| Regard generalization (a bond erodes class-disregard) | `arc-engine.md` type table row 6 spirit | YES | `arc.py:84-85` (`_REGARD_GENERALIZE`), `test_subject.py` | BUILT-AS-SPEC'D |

### Consolidation, records, measurement

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Actor self-reports tags in the SAME pass as prose (no interpreter) | `consolidation-loop.md:12-15` (P1), `design.md:80-81` | YES | one-pass JSON contract `prompt.py:62-88`; validated not mined | BUILT-AS-SPEC'D |
| Mechanical validation: schema / containment / capability; strip illegitimate dims; ok=0 moves no state | `consolidation-loop.md:27-43` | YES | `consolidation.validate_tags` :337-489; wired `direct.py:run_turn` | BUILT-AS-SPEC'D |
| Confidence composite + θ_conf escalation | `consolidation-loop.md:56` (open-Q 2, resolved) | YES | `compose_confidence` :314-334, `THETA_CONF = 0.45` :66 (NB: a comment at :47 says "(0.70)" — stale comment, the constant is 0.45) | BUILT-AS-SPEC'D — but escalations route to a HUMAN; the recorder-agent path is an unwired seam (`orchestration.md:95`) and the LLM critic deliberately does not exist in-engine (`consolidation.py` invariant 4) |
| Event catalog: one artifact, four jobs (appraisal_map / world_map / durability_class / visibility) | `record-contract.md:19-31` | YES | `consolidation.CATALOG` :88-257 (15 content + 2 system rows; + `capability_req` beyond spec); completeness vs `ledger._project` tested | BUILT-AS-SPEC'D — EXCEPT the dialogue-act family (next row) and arc reading durability from tags not the catalog |
| **Dialogue-act events** (assert/rebut/concede/… + target) and **stance snapshots** | `record-contract.md:15-16`, `multi-character.md:35-36` | NO | `schema.sql:115-131` tables exist, comment "writer lands post-spine"; not in CATALOG; zero producers | **SPEC-ONLY** (tables idle) |
| `recall` events + relationship-delta log + manifests persisted | `record-contract.md:12-14` (audit A1/A2/A3 repairs) | YES / YES / idle | `ledger.append_turn` :66-107 writes recall_events + decision_manifests; relationship_deltas now written from `scene.py` (2026-08-22) | **YES, both drivers, both directions (2026-08-23).** WRITE: `scripts/scene.py` and `scripts/direct.py`, both orders (`RelationshipDelta.order`, schema v8 `relationship_deltas.ord`). The chair was the last half open: its bonds block sat AFTER `append_turn`, so it computed deltas for a turn already written and persisted none — the edge moved in memory, printed a BOND line, and was gone at process exit. Moving the block ABOVE the commit is the repair, and it is the ordering the contract asks for rather than merely a convenient one: appending afterwards would let a rolled-back turn leave orphan edge rows. READ: both scripts refold on resume via `Ledger.edge_deltas_for` -> `bonds.replay`. Before that read path existed NOTHING replayed the table at all, so a resumed cast reverted to sheet-authored edges. Verified live end to end: a `by:` turn persisted its row on turn 0 and a fresh process resumed with it refolded |
| Compensating `correction` events (append-only repentance; fold applies inverse) | `consolidation-loop.md:57`, `measurement.md:19-23` | NO | catalog row declared; `ledger.py` invariant 4: "fold support pending"; critic never writes one | **SPEC-ONLY** |
| Recording accuracy measured: ground-truth replay, round-trip + flat slope, planted corrupt control | `consolidation-loop.md:45-52` (P4), `probe-plan.md:63-76` | YES | `tests/coherence_probe.py` (roundtrip ERR/SLOPE, `--corrupt` MUST FAIL, `--stub` green) | BUILT-AS-SPEC'D — minus **cross-extractor agreement** (nowhere) |
| State-sanity detectors (bounds/saturation/drift/oscillation) | `measurement.md:5-11` | YES | coherence_probe (SAT .15 / OSC .18 / DRIFT .55 per `guide-engine.md:153-155`) | BUILT-AS-SPEC'D (probe-resident, not a continuous service; world-side conservation minimal) |
| Coupling mechanical pre-screen (manifest lever vs emitted act, unexplained against-the-grain flag) | `measurement.md:14-15` | NO | — | SPEC-ONLY |
| Longitudinal blind identity check + judge protocols (blinding, anchors, n≥2, planted controls) | `measurement.md:16-30` | PARTIAL | `tests/coherence_judge.py`; blind transcripts in `runs/` (2026-06-11 sessions); voice-attribution harness unbuilt | PARTIAL — protocol exercised manually; not a standing harness |
| **Salami-forcing audit** (option-set narrowing across director placements) | `measurement.md:32-33` (C4) | NO | grep: no implementation | **SPEC-ONLY** |
| Engine-fault detector (recurring validation flags → named structural gaps) + world-fault inbox | code-first; activation recipe `guide-content.md:92-98` | YES | `faults.py` (scan_run/render; chair prints at `direct.py:453`); `detect_world_faults` → book's `world-faults.md` `direct.py:201-235`; `tests/test_faults.py` | BUILT (no owning design doc) |
| Thought-stream retention POLICY (depth by declared cut-space) | `recording-model.md:22-25`, `record-contract.md:17`, `cutting-room.md:48-49` | NO | capture is uniformly full for every actor | BUILT-DIFFERENTLY — uniform depth; the policy knob doesn't exist |

### Ledger, run lifecycle, laws, grounding

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Append-only log, two clocks, pure fold, snapshot-as-cache, atomic turn-commit, loud divergent resume, parking | `world-state-ledger.md:12-24`, `run-lifecycle.md:17-25` (B4, C3) | YES | `ledger.py` (append_turn :66, `_project` :252, fold :230, resume :276); `db.py` v7 migrate-on-connect; `tests/test_ledger.py`, `test_pipeline_e2e` | BUILT-AS-SPEC'D. Fold families grow empirically (move/harm+terminal/reveal/seize/destroy-asset/betray/bond/tension) |
| Future-dated consequences (`effective_at > caused_at`) | `world-dynamics.md:17` | YES (mechanism) | `records.py:34-46`, fold orders by `effective_at` (`schema.sql:28`) | BUILT-AS-SPEC'D structurally; **no producer ever emits one** — delayed pushback never actually happens |
| **`fold_forward(Δt)`** — lazy time, recurrence rates, standing processes | `world-dynamics.md:18-19,29-33` | NO | grep: does not exist | **SPEC-ONLY** — time does not pass off-screen; the world is a recorder, not yet a system |
| **Plausible-response envelope** (factions as collective characters; director chooses within engine bounds) | `world-dynamics.md:20-24`, `present-systems.md` §Factions | NO | no faction store, no envelope computation (the `capability` lore table of `orchestrator-design.md:180` also unbuilt) | **SPEC-ONLY** — world channel 2 entirely on paper |
| Laws: typed store, modality IMPOSSIBLE/FORBIDS/REQUIRES/PERMITS(+excepts), 3-value epistemic, blueprint defaults, completeness/strict | `orchestrator-design.md:154-205`, `guide-content.md:120-224`, `universal-law.md:12,18-19` | YES | `bible.py` (defaults :79, completeness :274, build/strict :339-350, laws_bearing_on :400, verdict_for :411); `schema.sql:200-223`; `tests/test_laws.py` | BUILT-AS-SPEC'D — the lore-store GATE half. Serve half (shard corpus) and the other typed tables (`locations`/`chronicle`/`capability`/`relations`) SPEC-ONLY; `chronicle:` citations resolve UNVERIFIABLE (`citation.py:145-148`) |
| **Laws consulted while a scene RUNS** | `design.md` layer 6 floor; the store exists to refuse | **YES (built 2026-08-22)** | PRE-FLIGHT: `scripts/scene.py:run_scene` calls `verdict_for` before the beat loop when the scene cfg declares an `act`, and REFUSES a scene an IMPOSSIBLE law denies. POST-ACTION: the turn contract gained an optional `act` from the world's own vocabulary (`prompt.py`, injected only when the world declares laws), and `scripts/scene.py:_law_events` appends a `law-violation` Event carrying the FORBIDS teeth. Suite `tests/test_laws_preflight.py` | **BUILT-AS-SPEC'D** — with two scoped omissions: post-action NEVER retracts (append-only log), and teeth are RECORDED not APPLIED (a consequence is the director's judgment). The act is AUTHORED, not inferred: measured, `act=None` makes all 27 laws bear and 24 deny, so a blanket call would refuse every scene |
| Bible pinning + drift detection (run records what it ran against) | `orchestrator-design.md` §7 spirit | YES | `bibles`/`bible_entities` tables; `bible.for_run` :484, `drifted` :503; `tests/test_bible.py` | BUILT (beyond the docs — code-first addition) |
| Citation grammar, resolver, 3-state verdict (resolved/unresolved/UNVERIFIABLE), corrupt control | `grounding.md:41-62`, `orchestrator-design.md:301-307` | YES | `citation.py` (resolvers :133-143; entity/law resolve via bible :175); `tests/test_citation.py` incl. sabotage control | BUILT-AS-SPEC'D — `law:` now RESOLVES (store built), superseding the design's "unverifiable until lore store exists" |
| Typed envelope (CLAIM/kinds/unknowns) | `orchestrator-design.md:61-93` | YES (validation side) | `citation.verify_envelope`, KINDS :34 | BUILT-AS-SPEC'D as a checkable contract; emission discipline lives in the showrunner skill |
| Read-API (`said`/`state`/`knows`/`edges`/`snapshot_at`/`scene_of` with per-stage trace) | `orchestrator-design.md:126`, `grounding.md` | YES | `read_api.py:87-206`; `tests/test_read_api.py` | BUILT-AS-SPEC'D minus `thread_status` (no thread store exists) |
| Three orchestrator hooks: inject (UserPromptSubmit) / block (PreToolUse citation) / beat-blind (PreToolUse Task), each with corrupt control; skill-frontmatter arming | `orchestrator-design.md:246-307`, `grounding.md:50-62` | YES | `.claude/hooks/ground_from_book.py`, `citation_gate.py`, `beat_blind_guard.py`; armed via `.claude/skills/showrunner/SKILL.md` frontmatter; `tests/test_orc_hooks.py` | BUILT-AS-SPEC'D. The **Stop/omissions hook** is declared not-built (`citation_gate.py` header); full `withheld`-list guard beyond the beat case remains known-blocked (`orchestrator-design.md:369`) |
| Orchestrator ships as skill + specialist layer as PLUGIN | `orchestrator-design.md:284-287`, build step 4 | PARTIAL | skill: yes (frontmatter hooks live); plugin: no `.claude-plugin/` anywhere — the 9 agents stay unreachable from sessions rooted above the repo (the measured limitation) | PARTIAL |
| Partner-mode notices (observation≠invention, ranked+capped) | `orchestrator-design.md:97-113` | NO (as code) | all listed observations are computable from schema.sql; no notice engine exists | SPEC-ONLY (skill-discipline only) |
| Charter: author owns beats; director proposes | `orchestrator-design.md:338-345` (§12) | NO | `.claude/agents/director.md:10` still reads "You own: … the **beats**; the **arc / through-line**; the **ending**" — the exact text §12 flags; `orchestration.md` still carries the superseded producer charter | **DOC-vs-DOC LIVE CONFLICT** — build-order step 5 (rewrite showrunner/orchestration/director) not done |
| Budget governor (token ledger, per-scene soft budget, projection) | `run-lifecycle.md:27-31` | PARTIAL | `llm_calls` table + spend SQL (`guide-operating.md:190`); no soft-budget surfacing or projection | PARTIAL |
| Scheduler durable state / PRNG position | `run-lifecycle.md:29-30` | PARTIAL | `scheduler_state` table exists; scene endings + urge values are stdout-only (bounds §3 "the ledger does not persist scene endings or urges") | PARTIAL — table idle, the values that matter unpersisted |

### Multi-character scenes

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Urge-to-speak scheduler | `multi-character.md:8-20` (stake + addressed + disagreement×conviction + affect + relationship_defense − social_inhibition; **softmax temperature**; interrupt threshold) | YES, reduced | `scripts/scene.py:44-47,107-131`: salience(counterfactual appraise) + addressed_bonus + disruption_stake(social_violation × schwartz order-values) − recency − inhibition(extraversion); deterministic max, `_FLOOR_THRESHOLD` 0.06 | **BUILT-DIFFERENTLY** — no temperature, no interrupt threshold, no relationship_defense/conviction terms; recency substitutes as the anti-monopoly. `scene-brief-blueprint.md:6` documents the BUILT formula as canonical while `multi-character.md` still specifies the fuller one — read blueprint for what runs, multi-character for the roadmap |
| Addressing (target field, addressed_bonus, threads) | `multi-character.md:22-23` | YES | `addressee` in the tag contract (`prompt.py:70-73`); bonus in `_urge` | BUILT-AS-SPEC'D |
| Stance dynamics `{position, conviction}`, backfire/hardening, convergence detection (concede/flip/decision-forced) | `multi-character.md:28-39` | NO | no stance store; exits are lull / walkout / empty only (`scene-brief-blueprint.md:6-9`); `stance_snapshots` table idle | **SPEC-ONLY** |
| Scene persistence + resume rehydration (arc diffs + acquired vault + affect), witness propagation, overheard name-reveal | `driving-the-engine.md:104-111` | YES | `scripts/scene.py` commits per beat; `--resume`; `tests/test_scene_persistence.py`, `test_scenes.py`, `test_scene_config.py` | BUILT-AS-SPEC'D |
| Seed variation for K-sampling (seed = base×1000 + beat) | `bounds-experiment-design.md` §10.1 | YES | `scripts/scene.py:173-179`, `--seed-base` | BUILT-AS-SPEC'D (the replication hazard fixed) |

### Prose out & the cut

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| POV-bounded narrator (POV thoughts + everyone's observables; multi-POV = switch per scene) | `narration.md:10-24` | YES | `scripts/narrate.py` (+`--book` per-scene recorded POV); `tests/test_narrate.py` | BUILT-AS-SPEC'D. Note: the adapter license (compress/heighten/reorder, never change what happened) lives in narrate.py citing a book-side "Writing Conventions §6" — no docs/ file carries it |
| Per-paragraph source event-IDs + mechanical provenance/POV audits on rendered prose | `cutting-room.md:45-46` | NO | narrate emits no event-ids; no render audit exists | **SPEC-ONLY** |
| Dailies views (shot list, biggest moments, arc hinges, acquisitions) | `cutting-room.md:13-24` | YES (4 of 7) | `scripts/cut.py`; `tests/test_cut.py` | PARTIAL — consequence-graph view, tension profile, and unwitnessed-scenes view unbuilt (the manifests + deltas the graph needs are only half-persisted — see Relationships) |
| EDL (append-only edit decisions; SCENE/SUMMARY/BREAK/NOTE) | `cutting-room.md:26-36` | NO | mentioned only in cut.py's docstring | **SPEC-ONLY** (deliberately deferred until the craft is practiced — the doc says so; still the biggest unbuilt consumer of the record) |
| Continuity+voice critic (detect-only, strong model, `--prompt-only` seam) | `design.md` layer 6, hybrid split `measurement.md:19-23` | YES | `scripts/critic.py`; `tests/test_critic.py` | BUILT-AS-SPEC'D for the LLM half; mechanical half = validate_tags + probe detectors; the critic's thin prompt (facts+prose only, no events/state/ledger slice) is a flagged unwired seam (`orchestration.md:94`) |

### Probes & experiment harnesses

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Coherence probe (walking skeleton, N turns, detectors, corrupt + stub controls) | `probe-plan.md:50-80` | YES | `tests/coherence_probe.py` | BUILT-AS-SPEC'D |
| Director-via-circumstance probe (role-separated, beat-blind, judged, multi-case) | `probe-plan.md:8-32` | NO | `tests/probe_director_circumstance.py` is a stale prototype (foreign idiom, hand-rolled "R7StateManager") — not the probe; only the 2026-06-06 biased smoke test has ever run | **SPEC-ONLY** (the file's existence overstates it) |
| Cut probe (faithfulness/shape/distinctness/transcription control) | `cutting-room.md:54-60` | NO | — | SPEC-ONLY |
| Lever-eval harness (K-seeded A/B, extractors, rates) | `driving-the-engine.md` | YES, stale | `scripts/exp.py` — still imports the replaced BP13 cast ids and defaults temp 0.7 against its own temp-1.0 rule (`bounds-experiment-design.md` §10.3 says pin or retire) | **DOC-STALE↔CODE-STALE** — its FINDINGS table numbers are explicitly pending re-measurement (`driving-the-engine.md:61-68`) |
| Bounds battery runner (`scripts/bounds.py`) + arms | `bounds-experiment-design.md` §6, §10.2 | NO (runner) | D2 and D3 ran and are recorded in-doc (D2 falsified bound #3); no `bounds.py` | SPEC-ONLY (pre-registered, deliberately) |
| Book lint (vault/edges/location/goals/genotype/catalog/wound-row assertions) | `world/character/scene-authoring-rules.md` | YES | `scripts/lint_book.py`; `tests/test_lint_book.py` | BUILT-AS-SPEC'D |
| Books-by-slug resolution (`$SWE_BOOKS`) | code-first | YES | `books.py`; `tests/test_books.py` (one pytest-only "failure" is its own case-insensitive-FS skip signal) | BUILT |

---

## WHERE TWO DOCS CONTRADICT EACH OTHER

1. **`orchestrator-design.md` vs `orchestration.md` + `.claude/agents/director.md`** — the 2026-07-24
   charter explicitly supersedes the showrunner-as-autonomous-producer charter and reserves
   beats/ending for the AUTHOR (§1, §12), yet `orchestration.md` still teaches the old charter and
   `director.md:10` still claims ownership of beats/arc/ending — the exact sentence §12 quotes as
   wrong. Until build-order step 5 lands, which doc you open decides which architecture you build.
2. **`multi-character.md` vs `scene-brief-blueprint.md`** — two different urge formulas. The
   blueprint states the reduced built one as *the* formula (`salience + addressed_bonus +
   disruption_stake − recency − inhibition`); multi-character specifies the fuller model (conviction,
   relationship_defense, softmax temperature, interrupt) and records v1 as the reduction. Neither
   cites the other's formula.
3. **`emotion-basis.md:144` ("The compound layer does not exist") vs `emotion-recipes.md:3` /
   `compounds.py`** — stale within a day of being written; the layer exists as an engine module
   (unconsumed at runtime, which is the part still true in spirit).
4. **`emotion-basis.md` (eight primitives, normative) vs `records.py:10` / `state-engine.md:14` /
   `character-schema.md:19` (seven)** — the basis decision is settled doc-side and unimplemented
   code-side; every "7 primaries" statement in older docs is now normatively stale.
5. **`design.md:87` ("The LLM never sees raw stats") vs `guide-content.md`/`bounds` reality** — the
   law is stated absolutely; the shipped prompt carries raw digits on three routes (R2/R3/R7). No
   doc marks design.md's law as scoped-to-direction; `goal-alignment-review.md:433-437` flags it.
6. **`MAP.md` + repo `CLAUDE.md` counts vs the tree** — "49 design docs / 18 modules / 29 suites"
   (MAP:3, CLAUDE.md:18 says 48) vs actual 56 docs / 20 modules / 34 test files. MAP's inventory
   omits `emotion-basis`, `emotion-recipes`, `guide-emotional-authoring`, `goal-alignment-review`;
   its module table omits `levers` and `compounds` — the two newest, most-asked-about modules.
   DOC-STALE: regenerate with MAP's own script (MAP:15-18).
7. **`record-contract.md:28` (durability_class lives in the catalog) vs `arc.py:65`** (durability
   read from the actor's tag + a severe-dim heuristic; the catalog column exists and is not what
   arc consults). Minor but a real ownership drift.
8. **`agent-toolboxes.md` roster vs `orchestrator-design.md:241`** — the latter measured the
   roster "0/10 rows accurate" and rules that registries must be generated, never hand-maintained;
   the roster has since been hand-corrected and remains hand-maintained.
9. **`consolidation.py:47` comment ("well below THETA_CONF (0.70)") vs `consolidation.py:66`
   (`THETA_CONF = 0.45`)** — code-comment self-contradiction on a load-bearing constant.
10. **`goal-alignment-review.md` vs same-day code** — its headline ("zero lines of implementation",
    "explicit-weighing thought not requested") was made true-then-fixed within hours: `levers.py`
    and `prompt.py:66-68` landed after it was written. Its §1b ceiling analysis, §2 capability
    ledger and §3 inert-fields table remain accurate EXCEPT those two rows. Read it with this
    ledger beside it.

---

## START HERE FOR X — one doc, one module, by concern

(`MAP.md` routes by *question*; this routes by *engine concern* and adds the implementing module.
When they disagree on status, this file wins — it was verified against code.)

| concern | THE doc | THE module | status flag |
|---|---|---|---|
| appraisal + current state | `state-engine.md` | `src/engine/state.py` | dims diverge from spec (incident #4) |
| effective levers / catalog / buffs | `decision-engine.md` §effective-state | `src/engine/levers.py` (wired `scene.py:127-141`; authored via `baseline.catalog` — `guide-emotional-authoring.md` §4) | built 2026-08-22 |
| decay | `state-engine.md` §Decay | `state.py:decay` | — |
| emotion basis / compounds / naming a vector | `emotion-basis.md` | `src/engine/compounds.py` (+`records.py` PRIMARIES) | built 2026-08-22/23 — `PRIMARIES` is 8 and `targets.retarget` is live; `recognise` still reads MAGNITUDE only, so a role-differing pair (pride vs excited) is indistinguishable to it |
| the decision itself | `decision-engine.md` | no module — the LLM at the harness; `prompt.py` is the contract | by design |
| numbers→words seam | `design.md` §split | `src/engine/direction.py` + `prompt.py` | closed 2026-08-22 — the 13 leaked floats are gone and `tests/test_no_digits.py` guards it |
| knowledge / vault | `knowledge-model.md` | `src/engine/vault.py` (store) + `acquisition.py` (growth) | trust-gating built — `acquisition.witness_belief(..., trust=)` :104; frontmatter keys OTHER than type/id are silently dropped by `vault.parse_note` :30 (the whitelist is `vault.py:40`) (`source`, `pulled`, `note` exist in real books and never arrive) |
| recall + perception | `relevancy-gate.md` | `src/engine/gate.py` | flat vault; class-name triggers |
| scene assembly / the packet | `scene-assembly.md` | `src/engine/scene.py` | — |
| relationships | `relationships.md` | `src/engine/bonds.py` owns per-beat updates (wired in BOTH drivers); sheet-authored edges enter via `scene.py:_build_edges`; movements persist as `relationship_deltas` and replay through `bonds.replay` | built 2026-08-23. `read_api.edges` does not split first- from second-order |
| durable change / arc | `arc-engine.md` | `src/engine/arc.py` | — |
| consolidation / tag validation | `consolidation-loop.md` | `src/engine/consolidation.py` | — |
| record contracts | `record-contract.md` | `src/engine/records.py` + `schema.sql` | dialogue-acts/stances idle |
| ledger / lifecycle / resume | `world-state-ledger.md` + `run-lifecycle.md` | `src/engine/ledger.py` (+`db.py`) | — |
| laws / computable denial | `guide-content.md` §Laws (authoring) + `orchestrator-design.md` §7.1 (design); `universal-law.md` (the rubric) | `src/engine/bible.py` | store AND runtime both built — `bible.verdict_for` is called pre-flight at `scripts/scene.py:188` and post-action at `:223`, and scene.py is a Mode A script; superseded text: **no runtime consumer in Mode A** |
| grounding / citations | `grounding.md` | `src/engine/citation.py` + `.claude/hooks/` | Stop-hook unbuilt |
| orchestration (Mode B) | `orchestrator-design.md` (charter) · `orchestration.md` (wiring table only) | `read_api.py` + the three hooks + `.claude/skills/showrunner/` | director.md contradicts the charter |
| character generation | `baseline-generation.md` | `scripts/make_genotype.py` (genotype only); rest hand-authored per `guide-emotional-authoring.md` | composition pass PARTIAL — library + compose + placement built (`src/engine/profiles.py`, `scripts/composition_pass.py`); the LLM classification step is not |
| multi-character scenes | `scene-brief-blueprint.md` (what runs) · `multi-character.md` (the full spec) | `scripts/scene.py` | reduced scheduler |
| steering / levers / bounds | `driving-the-engine.md` + `bounds-experiment-design.md` | `scripts/direct.py` (the chair); `scripts/exp.py` (stale) | rates pending re-measurement |
| narration | `narration.md` | `scripts/narrate.py` | no provenance audit |
| the cut | `cutting-room.md` | `scripts/cut.py` (views only) | EDL unbuilt |
| measurement / critics | `measurement.md` | `scripts/critic.py` + `tests/coherence_probe.py` + `src/engine/faults.py` | salami audit + state-consistency check unbuilt |
| authoring contracts / lint | `world-/character-/scene-authoring-rules.md` | `scripts/lint_book.py` | — |

---

## THE DOCS THAT MOST REPAY READING

Ranked by unbuilt-or-divergent specification a reader would otherwise re-derive.

1. **`decision-engine.md`** — carries the registry this project rebuilt twice before finding it,
   AND the still-unbuilt remainder: the both-sides collision with a computed margin driving act
   intensity (:115-134), clause salience, the critic's verify guardrail. Surprise: the "empty
   center" doc is not empty — for the decision layer specifically, the hard calls are already made
   in its own sections (the registry :61-113, the resolution spectrum :47-59, the guardrails
   :53-56, both-sides :115-134), including what must never be built (the argmax). What it leaves
   genuinely open it names itself: calibration magnitudes, and the optional pre-rank hybrid.
2. **`relationships.md`** — reads as the most-built doc and is among the least: edges render into
   every prompt, so nobody notices that the growth/diminishment rule (prediction-error, negativity
   bias, cliffs, value-scoring, perception-routing) and trust-gated transmission have zero runtime
   producers. Surprise: no relationship in any run has ever moved except through an arc-grade
   durable event.
3. **`emotion-basis.md`** — the newest normative layer: the eighth primitive, per-primary targets,
   reachability, and a complete falsification procedure for the basis. Surprise: it names, with
   measurements, exactly why shame is currently indistinguishable from grief — and its own
   "compound layer does not exist" line is already stale.
4. **`world-dynamics.md`** — the entire world-reaction layer (fold_forward, recurrence rates,
   future-dated pushback, faction envelopes) is coherent, complete, and 90% unbuilt. Surprise:
   the world currently cannot do ANYTHING on its own — no time passes unobserved, no consequence
   arrives late, and the 27 authored laws refuse nothing while a scene runs (bounds route R9).
5. **`orchestrator-design.md`** — supersedes two other docs that still say otherwise; half its
   build-order is done and it says which half; its §7.1/§9.1 carry measured platform facts
   (nested-discovery asymmetry, hook lifecycles) that are invisible from the code. Surprise: the
   DISPUTE three-way and the observation≠invention boundary — the two behaviors that make the
   orchestrator worth having — exist nowhere in code and only here.

*(Near-misses: `bounds-experiment-design.md` §2 is the best code-verified map of what actually
reaches the actor — read it before touching any lever; `goal-alignment-review.md` is the deepest
single audit but two of its headline gaps were fixed the day it was written — read it WITH this
ledger; `record-contract.md` §catalog for the two idle tables waiting for the debate layer.)*

---

## Changelog — what has moved since this ledger was written

The ledger's own rule is to flip a row in the same commit that builds it. These were flipped after
the fact, in one pass, and the lag is recorded rather than hidden.

**2026-08-22, same day as the ledger:**

- **Laws consulted while a scene runs** — NO → **YES**. `verdict_for` had no caller; it now has two
  (pre-flight refusal in `scripts/scene.py:run_scene`, post-action teeth in
  `scripts/scene.py:_law_events`). Suite `tests/test_laws_preflight.py`. Three of the coordinating
  session's own diagnoses were wrong before the real one held: the laws were NOT unkeyable
  (`_applies` narrows only when the caller supplies an act), the modalities did NOT need
  rebalancing (25 physics laws are right for a hard magic system), and `scripts/critic.py` does NOT
  catch breaches (it asks continuity and voice only — verified, zero law references).
- **Composition** — NO → **PARTIAL**. Library + compose + placement built; the LLM classification
  step is not.
- ~~Still true and unmoved: `compounds.py` has no runtime consumer, LUST is reachable by no appraisal
  dimension, and the vault `timestamp` is specified and never parsed.~~ **All three wrong by
  2026-08-24, and this bullet contradicted rows two hundred lines above it — corrected in place
  rather than deleted, because a ledger that quietly loses its own wrong entries stops being one.**
  LUST is reachable: `state._DIM_TO_PRIMARY["attraction"]` weights it 0.45. `compounds` has real
  consumers (`basis_probe` uses `COMPOUNDS`/`blend` as its stimulus source; `separability` and
  `validate` run in `test_targets` and `test_disgust`) — what it lacks is a PIPELINE caller, which
  no doc ever asked for. And the vault `timestamp` is not "specified and never parsed": the word
  appears nowhere in `vault.py`. The real defect is broader — `vault.parse_note` :30 (the whitelist is `vault.py:40`) admits only
  `type` and `id` from frontmatter and SILENTLY DROPS everything else, and the three real books
  carry `source`, `pulled` and `note` that therefore never arrive.

**2026-08-22, later the same day — the relationship tier (`src/engine/bonds.py`):**

Four rows in the Relationships and Knowledge sections flipped from NO to YES. What matters for a
ledger reader is not the four rows but **what the ledger could not see**: it correctly recorded that
the update RULE was missing, and did not record that the edge write which *did* exist was pointed at
the wrong character. `arc.assess` runs on the speaker; an edge belongs to the perceiver. A betrayal
moved the betrayer's trust in their victim, 0.80 -> 0.7828, and the victim's edge was never
computed. Negativity bias was inverted for the same reason — resilience, which belongs on temperament
scars, was buffering edge damage, so at resilience 0.90 a kindness moved trust 6.0x further than an
equal betrayal.

**The lesson for this ledger's method:** a row that reads "the update rule is SPEC-ONLY" invites the
reading that nothing runs. Something did run, and it ran backwards. **An audit that checks whether a
mechanism EXISTS will not catch a mechanism that exists and is wrong** — only running it and reading
the number does. Both defects took a measurement, not a reading.

**Known limitation of any audit like this one:** an agent reading a repo mid-session reads the
*current* state as though it were the *original* design. This ledger's finding #2 about
`decision-engine.md` inlining its source rather than citing it by path was exactly that — the
inlining had been done hours earlier the same day, by the session that commissioned the audit.

