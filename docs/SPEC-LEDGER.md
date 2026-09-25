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
   sum-dial is now implemented in `staging/`staging/src/engine/compounds.py` (retired 2026-09-08):248-296` (`recipe_sum`, `blend`).
3. **Genotype purpose + combinatorics** — **CONFIRMED.** `baseline-generation.md:28` states the
   purpose verbatim ("it's the layer that makes 10 strangers react differently to the same
   betrayal"); :39-47 gives the axes×alleles arithmetic and the distinctness table; :49-57 the six
   axes; :59 the identity "Genetics IS where trait_sensitivity comes from" — which is exactly
   `state.py:268-296`.
4. **Appraisal dimension set** — **CONFIRMED.** `state-engine.md:21-22` specifies OCC/Scherer
   dims (goal-congruence · agency · certainty · **control** · norm-violation) and :24-30 a
   CONJUNCTIVE mapping ("blocked goal **+** other-agency → RAGE"). Shipped `state.py:53-70`
   `_DIM_TO_PATH` uses six outcome-class dims (threat/loss/care_relevant/mastery/
   social_violation/relief), each an independent additive push-vector; no agency, no certainty, and
   `control` — which :38 says answers "same blade, different fear, by their skill" — appears
   nowhere (the only "control" in `state.py` was the retired `effortful_control` allele, cut 2026-09-10). The
   whole severity factoring of :34-39 (damage-potential × hit-probability × context, defender
   skill filling `control`) is explicitly deferred (`state.py` appraise docstring: "severity =
   the raw dimension magnitude").

---

## THE LEDGER

### Emotion basis & compounds

| **A rate is spent once: the sheet's rate fields never reach the actor** (normative, ruled by the project owner 2026-09-06) | `scene-assembly.md` §Stable prefix | **YES (built 2026-09-06)** | `scene.py` `_build_stable` ships persona + voice + goal TEXT + wound TEXT only; `_manner_drives` filters the drives block and DROPS an unruled key rather than carrying it; `identity_view._said` no longer defaults an absent weight to 0.5; `_SCALARS["assertiveness"]` rewritten as sentence form per `voice.md:12`; suite `tests/test_prompt_manner.py` | **THE SHEET WAS BEING SPENT TWICE.** `state.build_profile` reads genotype, the trait means and the worth menu as gains, relevance and regard; `_build_stable` then put the SAME fields in the prefix and `direct_identity` rendered them as sentences — so a character was damped once in the arithmetic and again in the prose, and a rung stopped meaning the same thing for two people. Cut: `genotype`, `traits`, `model`, `provenance`, and inside `drives` everything but the goal and wound text. **The cut EXPOSED a second defect**: removing a field made `_said` invent a mid-band phrase for it ("it catches you sometimes" for a wound with no intensity), which is worse than leaking — an invented middle reads exactly like an authored one. `direct_identity` KEEPS its renderers for the cut blocks deliberately: it is the guard that refuses a number nobody has written a phrase for, and `test_no_digits` §4 now exercises it at the function rather than through a packet that no longer carries the fields |


| The keeper's tier model: an actor's utterance is T2 SUPERPOSED and binds nothing until tested | `keeper-of-truth.md` (normative, author-approved 2026-08-29) | **PARTLY (wired 2026-09-06; the debt made VISIBLE and the gate DEFAULT ON 2026-09-19)** | `claims.py` — `spoken` :76, `record` :212, `write` :245 (the no-transaction half, called inside `ledger.append_turn`), `contradictions` :179, `tier_of` :135, `unextracted` (new, 2026-09-19) — count/first_turn/last_turn/speakers for utterances with no `claim_extracts` row, folded from append-only `claim_resolutions`; `utterances`/`claim_extracts`/`claim_resolutions` in `schema.sql`; `scripts/scene.py`/`scripts/direct.py` `_keeper_runs`+`_report_lore` (the default and the closing `lore:` line); `scripts/doctor.py` `_lore_debt` (the AMBER report per run); `tests/test_claims.py`, `tests/test_lore.py`, `tests/test_doctor.py`, `tests/test_driver_main.py` | **THE ENGINE HALF WAS BUILT AND UNREACHED.** `claims.record` had exactly one caller (`scripts/keeper.py:292`) and neither driver imported the module, so `contradictions` ran over an empty table for every run driven normally — 24 blind actor draws on 2026-09-06 invented five place names and three mutually incompatible figures for one fact about one character and not one could have been detected. Both drivers now record one utterance per QUOTED SPAN at the commit site, tier superposed, **extracts NONE** — hard rule 3 puts the subject/predicate/object reading in the keeper agent and `record`'s own docstring calls an empty extract list the honest answer. STILL UNBUILT: the reliance trigger (`keeper-of-truth.md` names it the hard one); write-back of an adopted T1 fact through the bible path. **BUILT SINCE, corrected in this row 2026-09-19**: the keeper agent itself (`scripts/keeper.py` `rule_scene` :387, `notice_scene` :420, `attach_scene` :587, `canon_gate` :631 — real LLM-calling passes, not stubs) and extraction (the noticing prompt asks for structured `{subject, predicate, object}` extracts, `keeper.py:152`, and is `attach_candidates`'s producer per its own 2026-09-19 comment, `keeper.py:652`). `spoken` reads DOUBLE-QUOTED spans only and is deliberately narrower than the truth — a fact asserted in narration is missed, stated in its docstring. **2026-09-19 addendum (gate lore-licence-visible): the debt this row already named — "utterances land at commit WITHOUT extracts" — was TRUE and UNREPORTED; nothing counted it and nothing ran the noticing pass unless an invocation happened to pass `--keeper`. Measured on a real book's first three live scenes: all three ran keeper-off, so every utterance in them was (and remains — the debt cannot be paid off in place, only avoided going forward) invisible to `claims.about`. Fixed on the REPORTING side, not by inventing an engine-side extractor (hard rule 3 keeps that reading in the agent): `unextracted` makes the count visible, and the canon gate is now DEFAULT ON for a non-stub invocation of both drivers (owner decision D1) with `--no-keeper` as the opt-out, so the gap this row flags stops accumulating silently on any run that does not deliberately choose to skip it.** |


| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| **The nine emotion paths** (one axis per emotion, 0.00-1.00, the rung NAME changing along it; 92 rungs) | `emotion-paths.md` (the nine, their axes and rungs), `emotion-dynamics.md` (what a path IS) | **BUILT (corrected 2026-09-19)** | `src/engine/rungs.py` (`rung_at`, `block_for`) + `rung_blocks.py` (`BANDS`/`BLOCKS`/`DESCENT_BLOCKS`) — 9 paths, 92 climb blocks + 22 descent blocks (counted at HEAD 2026-09-19); `direction.py` carries no `_PHRASES` (retired 2026-09-08); consumer is the composer (`scripts/composer.py` `selectable`/`direction_for`), wired into both drivers via `direct.py:rung_direction` (called from `scene.py:548` and from `direct.py` itself) | **WIRED 2026-09-08 (composer selection/direction), 2026-09-12 (per-rung decay staircase, gate 2), 2026-09-15 (descent blocks authored); status corrected in this row 2026-09-19.** The paths were settled in conversation 2026-09-06 and now run end to end — see the WHERE column. Sort status as last measured, unchanged by this correction: one of nine has passed a blind sort (RECEPTIVITY, mean rho 0.900); one has FAILED one (DISPLEASURE, 0.895, 5 of 12 recovered, forked every run); seven are unsorted, so their rung ORDER is asserted rather than measured. 91 of the 92 rung prompts are unwritten. The 280 authored phrase bands in `docs/phrases-*.md` are the nearest existing artifact and nothing reads them either |
| Seven Panksepp primaries as the state vector | `generative-model.md:8-16`, `state-engine.md:14` | REPLACED 2026-09-08 | `records.py` `PATHS` — the eight paths ARE the stored state; the primitives were retired with `92a9942` (`emotion-paths.md`) | SUPERSEDED — the spec's primaries became the paths' "was" column |
| **DISGUST as the eighth primitive** (normative, settled 2026-08-22) | `emotion-basis.md:24-43` | **YES (built 2026-08-22)** | `records.py` PRIMARIES is 8 (DISGUST LAST — `compounds._vector` indexes by position); reached from `social_violation` 0.28 and `threat` 0.08; `_DECAY_RATE` 0.88 (slowest but PANIC_GRIEF); four direction phrases; species prior 0.15; suite `tests/test_disgust.py` | BUILT-AS-SPEC'D. 16 compounds went live and `goal-alignment-review.md`'s "**cold contempt is unrepresentable as state**" is retired — measured: three violations take DISGUST 0.150 -> 0.534 and stage as *"you keep a little more distance than the moment needs"*. Unblocking exposed a duplicate the block had hidden: `sarcastic` at cosine 0.996 to `mocking`, removed as a delivery REGISTER rather than a feeling. No new appraisal DIMENSION was added |
| Compound vocabulary: `{primitive: (weight, role)}` recipes, compose/recognise/separability | `emotion-basis.md:56-70`, `emotion-recipes.md` (generated) | YES | `compounds.py` (retired to staging 2026-09-08) `COMPOUNDS` (41 recipes), `compose` :187, `recognise` :217, `separability` :246; `tests/test_compounds.py` | BUILT, THEN PARTLY RETIRED. It had **zero runtime consumers** as written; `direction.name_compound` was later added as one, and **removed 2026-09-06** because it was measurably wrong: `recognise` scores by cosine, which is scale-invariant, so a pure RAGE vector was named `fury` at 0.10 as readily as at 0.95 — and at 0.10 the band-0 phrase is filtered by the notable gate, leaving that name as the WHOLE stage direction. Grounded at `emotion-dynamics.md:616-621`, which retires compounds as a naming basis. `compose`, `blend`, `validate` and `separability` remain and are exercised by `tests/test_compounds.py`; **`recognise` now has no runtime consumer again, deliberately**. Naming a magnitude belongs to the path layer (unbuilt), which must read position on an axis rather than the angle of a vector. Regression pinned by `tests/test_direction.py` §13 |
| The sum as identity dial (`blend` = recipe + (1−sum)×baseline) | `decision-engine.md:66-79`, `emotion-recipes.md:15-25` | YES | `staging/`staging/src/engine/compounds.py` (retired 2026-09-08):248-296` | BUILT-AS-SPEC'D (module-level; unconsumed at runtime) |
| Per-primary TARGETS on live state (`{primitive -> (magnitude, target)}`; `_regard` per-primitive) | `emotion-basis.md:72-99` (:93 "a change to what exists") | **YES (built 2026-08-22)** | `records.DIRECTEDNESS` (the 8-row registry) + `records.admits_role`; `targets.retarget` (5 binding rules); `state.appraise(..., targets=)` evaluates `_regard` per primitive; `direction._phrase_for` picks the reflexive variant; `compounds.validate()["drift"]` enforces the registry downstream; suite `tests/test_targets.py` | BUILT-AS-SPEC'D. Targets live in a SIBLING field (`current.targets`), not fused into affect as tuples — magnitude decays every beat and a target never does, and this project splits fields by lifetime everywhere. **READER-verified 2026-08-23** (`basis-verification.md` §10): same numbers (DISGUST 0.556, RAGE 0.572), only the target flipped, and blind judges recover shame from contempt at **11/12** — 12/12 for pursuit vs display, 23/24 pooled against a pre-registered threshold of 18/24, with a 12/12 positive control and a clean bias floor. `tests/test_targets.py` asserts the strings DIFFER; this measures that the difference is LEGIBLE. Took four runs — the first three could not reach the question and are recorded in §9 rather than discarded. The spec's own example works: fear stays on the wolf while rage moves to the man who let it in. Registry reasoned by Fable from what each Panksepp system makes a body do, NOT from the compound table — and following that rule caught 5 recipes that had already drifted FROM the basis |
| Tense via targets + vault `timestamp` | `emotion-basis.md:101-132` | NO | `vault.py:30-80` parses claim/confidence/provenance/links; `timestamp` dropped (also `guide-content.md:50`) | **SPEC-ONLY** — schema field authored, never parsed; the named prerequisite |
| LUST reachable by some appraisal dimension | `emotion-basis.md:136-140` (flagged blocking) | **YES (built 2026-08-22)** | seventh dimension `attraction` in `state._DIM_TO_PATH` (LUST 0.45, SEEKING 0.18, PLAY 0.10), relevance via hedonism/relatedness/stimulation, admitted on the `bond` and `mundane` CATALOG entries only | BUILT-AS-SPEC'D. It needed its OWN dimension: none of the six was about desire, and reaching LUST from `care_relevant` would make every act of tenderness push attraction — the conflation a separate primitive exists to prevent. Measured: 0.200 -> 0.394 over three beats. **Deliberately NOT admitted on threat / harm / seize / threaten** — coercion is a real subject a book may need and must be authored as the violation it is, not reached through a dimension the engine hands out on threat events. `tests/test_disgust.py` now asserts EVERY primitive is reachable, so the next basis element cannot repeat this |
| Basis verification procedure (blind vocabulary, 3 signatures, confusion matrix) | `emotion-basis.md:148-177` | PARTIAL | `separability()` = the deterministic half; blind-judge render pass not run | PARTIAL |

### State engine (tiers 1–2)

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Three-tier state (temperament / current / effective) | `state-engine.md:5-16` | YES | tiers 1-2: `state.py`; tier 3: `levers.py` (built 2026-08-22) | BUILT-AS-SPEC'D **now**; the doc's own status column (:10-12, "done") described tier 3 as done for ~2 months while unbuilt — the trap this ledger exists for |
| Appraisal dims + dim→primary mapping | `state-engine.md:21-30` | YES, differently | `state.py:53-70` | **BUILT-DIFFERENTLY** — outcome-class dims, additive vector pushes, no conjunctions, no agency/certainty/`control` (incident #4 above) |
| Severity factoring for wielded threats (damage-potential × hit-probability × context; defender skill → `control`) | `state-engine.md:34-39` | NO | severity = raw self-tagged magnitude (`state.py` appraise docstring) | **SPEC-ONLY** (explicitly deferred; no world object model to read from) |
| Relevance = event dims × the character's Model weights ("where two people diverge") | `state-engine.md:40`, `values-and-stakes.md:24-33` | YES | `_DIM_VALUE_KEYS` `state.py:255-281` (re-pointed 2026-09-19 — was 125-144, which is now `_HALF_LIFE`), `_relevance` :328; missing key = neutral 0.5 | BUILT-AS-SPEC'D |
| trait_sensitivity = genotype gains × HEXACO slopes | `state-engine.md:41`, `baseline-generation.md:49-59` | YES | `state.build_profile` reads `heritable.hit` per path; the HEXACO slopes were CUT 2026-09-10 (a second source of g) | REPLACED — trait_sensitivity is the genotype's HIT cell alone; traits reach no arithmetic (recorded dead vector, gate genotype-foundation) |
| Decay toward temperament, per-primary rates, regulation-scaled | `state-engine.md:45-47` | YES | `state._HALF_LIFE` (minutes, two ANCHORS per path — episode/disposition, the owner's conservative START, 2026-09-10 — deriving a 92-cell per-rung staircase via `_rung_half_life`, gate 2 2026-09-12; the earlier two-zone/`zone_of` boundary model was retired 2026-09-19, gate `emotion-tier-tidy`, `c008a4b`) × the genotype's hold; `decay()` runs BEFORE the receipt on every beat since 2026-09-10 evening (spec section 8 order) | BUILT-AS-SPEC'D. Consequence measured 2026-08-22: decay+mean cap current-state at `mean+(1−mean)r` (`goal-alignment-review.md:199-256`) — correct for tier 2, and the reason tier 3 had to exist |
| Subject-regard empathy scoping (bigotry floor 0.25; affinity lifts, never lowers) | no design doc owns it — `guide-emotional-authoring.md:110-115`, `driving-the-engine.md:14` | YES | `state.py:150-158` (`_CARE_FLOOR`, `_REGARD_SCALED_DIMS`), `_regard` :306; runtime subject resolution `scene.py:349-390`; proven `tests/test_subject.py` | BUILT (code-first; guides document it; no `docs/` design doc is its owner) |
| Event-vs-condition rule (appraisal fires on the change; catalog on the standing fact) | `state-engine.md:49-54` | YES | `levers.py:129-131` comment + `scene.py:122-126`; both fire | BUILT-AS-SPEC'D |

### Effective levers (tier 3) & the decision

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| **Buff/debuff registry** (`{when, lever, op, magnitude, source}`; `effective = current × Π(mult) + Σ(add)`, clamped) | `decision-engine.md:61-113`, `state-engine.md:56-57` | YES (2026-08-22) | `levers.py:70-111` (`effective`), :212-235 (`active_rows`); authored per-character as `baseline.catalog.rows`; validated by `lint_book.py:163`; `tests/test_effective.py` | BUILT-AS-SPEC'D — all four condition kinds from the doc's worked entries (`percept`, `present_edge`/`target_edge`, `affect_at_least`, `condition_at_most`), rows AND together, no-`when` = standing trait |
| Tier 3 wired into the acting path | `state-engine.md:12` ("what the decision actually sees") | YES | `scene.py:127-141` computes `volatile.state.effective` + `volatile.levers`; `prompt.py:41-46` stages direction FROM effective; fired rows land in the manifest (`scene.py:158`) | BUILT-AS-SPEC'D for the prompt path. NOT swapped at two display/salience call sites: the chair's status line (`scripts/direct.py:830-842` `show_status`, re-pointed 2026-09-19 — was :332-333, now unrelated code) and the scene-runner's `_salience` (alias at `scripts/scene.py:87` for `src/engine/floor.py:48` `salience`, re-pointed 2026-09-19 — was `scene.py:107-115`, now unrelated code) still read the current/raw tier, confirmed at HEAD |
| Registry conditions can fire on event WORDS (a `percept: ["spider"]` row) | `decision-engine.md:96` (perception-fired entry) | YES | `levers.py:170-176` matches `when.percept` against raw event text | BUILT-AS-SPEC'D — note this matches EVENT TEXT directly, side-stepping the recall gate's class-name trigger gap (next section) |
| No code-side argmax; LLM resolves; margin = act intensity | `decision-engine.md:5-7,103,115-134` | YES / PARTIAL | no argmax anywhere (grep); the **margin** is never computed and direction clauses came in fixed `PRIMARIES` order with no salience ranking; the clause renderer is RETIRED 2026-09-08 and SELECTION now belongs to `scripts/composer.py` (`records.py:10`) | PARTIAL — resolution is narrative as spec'd; the "margin → intensity" and clause-ordering half is SPEC-ONLY |
| Hard gates (knowledge presence, energy floor, capability, absolute lines) | `decision-engine.md:49` | YES | DCs `gate.py:40-42`; energy budget `gate.py:47`; combat capability `consolidation.py` CATALOG `capability_req`; absolute value lines: none authored | BUILT-AS-SPEC'D (the deterministic few) |
| Explicit-weighing thought ("name the competing pulls") | `decision-engine.md:54` | YES (2026-08-22) | `prompt.py:66-68` | BUILT-AS-SPEC'D (was missing at the goal-alignment review hours earlier) |
| Critic verifies action-vs-injected-state | `decision-engine.md:56`, `measurement.md:14-16` | NO | `scripts/critic.py:62-74` asks continuity + voice only | **SPEC-ONLY** — the third consistency guardrail has no checker |
| Optional utility pre-rank (propose/dispose hybrid) | `decision-engine.md:58-59` | NO | — | SPEC-ONLY (doc marks it optional) |

### Numbers → words (gate 5)

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Direction layer: digit-free bands, stage-direction phrasing, deviation-vs-temperament markers | `design.md:87`, `state-engine.md` | YES | `direction.py` — the band-phrase affect renderer (`_BANDS`, `_PHRASES`, `direct_affect`) is RETIRED 2026-09-08, replaced by the rung ladders; `direction.py` still renders edges, second-order regard, condition and sureness, digit-free proven `tests/test_direction.py` | BUILT-AS-SPEC'D — the strongest module (`goal-alignment-review.md:314-317`) |
| **"Numbers never reach the prompt"** | `design.md:87` ("The LLM never sees raw stats") | **YES (built 2026-08-22)** | `identity_view.direct_identity` :195 / `direct_goals` :269 / `direct_percepts` :277 (split out of `direction.py` on the identity/affect seam); `prompt.py` renders instead of dumping; guard `tests/test_no_digits.py` | BUILT-AS-SPEC'D. The leak was MEASURED at 13 floats before the fix. Guaranteed **by construction**, not by the test — but the construction is a BAND, not a refusal, and the difference cost two rounds. Draft 1 silently DROPPED unknown keys and the guard came back green (worse than leaking: authored content vanishing with nothing said). Draft 2 refused any number it had no phrase for and **took down most of the owner's real books** — a novel authored field is not a defect. Shipped: `identity_view.py` `_say_scalars` :259 gives a known key its named phrase and anything else a banded generic (`identity_view.py` `_SCALAR_FALLBACK` :107); what still refuses is a number OUTSIDE [0,1], which is a scale error rather than a vocabulary gap. Two exemptions, both stated in the suite: INTEGERS (a year, an age) and the reply CONTRACT (the scale the actor reports ON) |
| Direction reads a salience order / one resolved staging line | `decision-engine.md:124` (injected as DIRECTION with margin) | NO | fixed tuple order; six parallel clauses at rest measured (`goal-alignment-review.md:108-115`) | SPEC-ONLY (ordering/margin) |

### Character generation

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Genotype: 6 axes × 4 alleles → per-primary gains | `baseline-generation.md:34-67`, `character-schema.md:14` | YES | `state.py:26-31,268-296`; seeded draw `scripts/make_genotype.py` (`--rows` emits lever rows); `tests/test_genotype.py` | BUILT-AS-SPEC'D. Allele vocabulary EXACTLY `low|typical|elevated|high`; anything else silently reads typical — now a lint ERROR (`lint_book.py:146`) |
| Species prior ⊕ culture ⊕ class ⊕ formative env ⊕ history composition | `baseline-generation.md:13-31` | **PARTIAL (2026-08-22)** | The SCRIPT half is built: `data/formative_profiles.json` (94 profiles, 8 categories, each with `baseline_diffs` + `catalog_rows` + `vault_belief_seeds`), `src/engine/profiles.py` (`compose` with the ±0.35 cap, `separability`, `admit`, and `path_for`/`prior_from`/`place` mapping every field to the nested path its consumer reads), `scripts/composition_pass.py`. Design: `docs/composition-pass.md`. Suites `test_formative_profiles.py`, `test_composition_pass.py` | **BUILT-DIFFERENTLY, LLM classification step now BUILT (corrected 2026-09-19; was hand-supplied picks)** — `scripts/composition_pass.py` `build_classify_prompt` :182 / `picks_from_classification` :221 / `--classify` :348; `tests/test_composition_phase_a.py` (7/7 passing); the species prior itself remains a REFERENCE (`reference-species-prior.md`), not code. Measured end-to-end (2026-08-22): one pick at weight 0.6 moved a temperament mean 0.450→0.522, seeded a vault belief, and placed a catalog row that FIRES in `assemble` (effective FEAR 0.450→0.990). **REVISED 2026-09-10:** the pass no longer writes temperament at all — where a character rests is a DESIGN choice authored as a rest word beside the voice (`BLUEPRINT-character.md` Part Three); the 69 profiles that moved a path's mean keep that as a `rest_note` for the author, and `profiles.path_for` refuses a path field by name |
| Provenance per baseline number ("the flood, age 9") | `baseline-generation.md:32` | PARTIAL | `baseline.provenance` rides the stable prefix (`scene.py:205`); discipline is manual (`guide-content.md:112-117`) | PARTIAL — carried, never enforced or checked |
| Archetype models: sparse bias-packs over layers, assign+perturb, single-axis first | `character-model.md:81-115`, `baseline-generation.md:11` | NO | no model library, no overlay/perturbation machinery anywhere | **SPEC-ONLY** |
| Whole-trait `{mean, variability}`; out-of-character tail samples | `trait-theory.md:18-27,31-41`, `decision-engine.md:51` | NO (variability) | every sheet stores variability; `build_profile` reads `.mean` only (`state.py:281-283`); no distribution sampling anywhere | **SPEC-ONLY** — the distribution half is authored dead weight (`goal-alignment-review.md:296`) |
| Drives schema as structured OPERANDS (goal priority/serves chains; fear intensity/trigger; orientation) | `drives-schema.md` throughout | NO (as operands) | authored per the schema in real books; consumed as: goal TEXT → recall salience (`gate.py:288-324`) + prompt; everything else verbatim prompt JSON. `intensity`/`trigger`/`serves`/`protects`/`priority` numbers reach no arithmetic (`goal-alignment-review.md:289`); `blocked` transition logic (audit B7 "fix") in no code | **BUILT-DIFFERENTLY** — drives are prompt text, not computed operands. The built bridge: a wound gets teeth via a `baseline.catalog` row; `lint_book.py:179-183` warns on a wound trigger with no row |
| Character schema three clocks (FIXED/BASELINE/CURRENT + DERIVED never stored) | `character-schema.md` | YES | `schema.sql` characters + current_state; effective recomputed (`scene.py:137`), resilience derived (`arc.py:35-49`) | BUILT-AS-SPEC'D. Dead schema fields (stored, zero consumers, NOT doc'd as inert): `model.resolution_priority`, `fixed.role_tier`, `current.zone`, `goals[*].satisfaction`, edge `.history` (packeted then dropped at `prompt.py:49`), belief `.believed_value` (dropped at `scene.py:277-286`) — `goal-alignment-review.md:285-299`. **`baseline.relationship_priors` left this list on 2026-08-22**: `default_trust` is the STRANGER's rest on trust (`bond_rest.stranger_rest`, gate 4 — an authored edge rests at its own `rest_declared` rows) and `update` sets the character's learning rates (`bonds.rates_of`). |
| Voice profile GENERATED from the formative stack | `voice.md:18-19` | NO | voice hand-authored; consumed verbatim (stable prefix `scene.py:204`; narration lens `scripts/narrate.py`) | **SPEC-ONLY** (generation half; audit C2 half-closed) |
| Craft standards imported at `books/standards/` | `voice.md:25-28` | NO | `books/` is empty | SPEC-ONLY — acceptance criterion #6 explicitly unsatisfiable until import (as voice.md itself states) |

### Knowledge, vault, recall, perception

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Belief store `{claim, believed_value, provenance, timestamp, confidence}` + `## Beliefs` authoring contract | `knowledge-model.md:13`, `guide-content.md:49-63` | YES | `vault.py:22` (`_BELIEF_RE`), fail-loud on unparseable sections :74-78 (added after 41-52 of authored beliefs silently loaded as zero — `character-authoring-rules.md:8-10`) | BUILT-DIFFERENTLY in two spots: `timestamp` never parsed; `believed_value` carried by the gate then dropped at the packet |
| Acquisition during play (lived / witnessed / learned; monotonic-add; dedup) | `knowledge-model.md:17,104-110` | YES | `acquisition.py` (`assess` :24, `witness_belief` :137, `reveal_name` :87, `overheard_names` :194); persisted `ledger.py` `append_acquisition` :271; resume rehydrates | BUILT-AS-SPEC'D (channels told/taught/read/deduced not distinguished; forgetting not built — declared later-layer) |
| **Trust gates transmission** (believed fact vs discounted rumor scales with B's trust in A) | `knowledge-model.md:108`, `relationships.md:21-22` | **YES (built 2026-08-22)** | `witness_belief(..., trust=)` scales `confidence` and flips `provenance` to `reported` at/below 0.40, reframing the claim as *"X claims: …"*; `scene.py` computes the belief PER WITNESS from that witness's edge | BUILT-AS-SPEC'D. Ceiling 0.88 is calibrated against `direction._SURENESS`, which turns over at 0.90 — a second-hand account must never render as *"you do not entertain the alternative"*. Distrust is deliberately NOT routed through `believed_value` (inert — see the schema row above) |
| Talk-of-the-Town belief dynamics (confabulation/transference/mutation/forgetting) | `knowledge-model.md:112`, `prior-art.md:21` | NO | — | SPEC-ONLY (declared "+Full" tier) |
| Trigger-matching recall + goal salience + energy budget (cost = 1−confidence) | `relevancy-gate.md:9-21,34-41,99-118` | YES | `gate.py:257-360` (`run_gate`), budget `gate.py:47` = energy×(1−load/2); `[[links]]` join the match surface | BUILT-AS-SPEC'D — with one measured seam: **triggers are lexicon CLASS NAMES + event kind, not the event's own words** (`gate.py:378-391`); "spider" cannot become a trigger unless a class is named "spider" (`goal-alignment-review.md:121-127`: the spider memory surfaced on the word `boy`). Levers' `when.percept` (raw-text match) does not inherit this gap; recall still does |
| Deterministic checks, no randomness, **no director-set DCs** | `relevancy-gate.md:23-26` (B1 remediation) | YES | `gate.py:40-42,59`; no random anywhere in `src/engine` | BUILT-AS-SPEC'D — the one design-invariant violation stays dead |
| Perception-mode wall (PerceptSet whitelist; identity behind insight 0.55; subtle cues behind perception 0.60; acquaintance recognition) | `scene-assembly.md:17-21,74-97`, `relevancy-gate.md:28-32` | YES | `gate.py:90-210`; never-add structural (`test_scene` whitelist canary); known-entity bypass `gate.py:176` | BUILT-AS-SPEC'D |
| Graph recall: weighted hops, pathfinding to hinges, degree-penalty, multi-hop chains | `relevancy-gate.md:60-97` | NO | vault is FLAT by design; single-hop cost 1−confidence (`guide-engine.md:171-173` declares the reduction) | **BUILT-DIFFERENTLY (deliberate)** — the entire hop/path/DC-from-distance apparatus is spec-only behind the same interface |
| Authored hinges (director-planted checks that always surface + branch) | `relevancy-gate.md:39` (pipeline step 5) | NO | `must_surface` exists only as the event-anchor flag (`gate.py:24,144`); no hinge authoring surface, no branch mechanics | SPEC-ONLY |
| Name masking + latent-leak regeneration ("recorded as-is" preserved) | `knowledge-model.md` wall; status log `driving-the-engine.md:104-111` | YES | `gate.scope_names` :543 (prompt wall), `faithfulness.py:16-35` (output detector), `direct.py` `faithful_turn` :383-415 (regenerate → reject) ; `tests/test_faithful_turn.py` | BUILT-AS-SPEC'D |

### Scene assembly & the packet

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Deterministic 7-step assembly; no renderer; one LLM call per turn | `scene-assembly.md:5,43-50,71-97` | YES | `scene.py:37-171`; no LLM in `src/engine` (proven `test_portability`) | BUILT-AS-SPEC'D (steps 6-7 live in the harness — `direct.py:run_turn`) |
| Stable/volatile split; byte-stable cacheable prefix; `_note` stripping | `scene-assembly.md:52-67` (audit B8) | YES | `_build_stable` `scene.py:236-266`; `_strip_notes` `scene.py:268-287` | BUILT-AS-SPEC'D. Cosmetic: a dead first `_sort_nested` definition shadowed by the fix (`scene.py:289-302`, shadowed by `scene.py:304`) |
| Excluded-by-construction (no bible wholesale, no other minds, no beat) | `scene-assembly.md:65`, `design.md:33` | YES | structural absence + `.claude/hooks/beat_blind_guard.py` (Mode-B PreToolUse deny) | BUILT-AS-SPEC'D |
| Decision-input manifest persisted per turn | `record-contract.md:13` | YES | `scene.py:147-160` (+`levers_fired`), `ledger.py:94-96` → `decision_manifests` | BUILT-AS-SPEC'D |
| Subject/group resolution (who the event is ABOUT; actor may name, engine validates) | `state-engine.md:40` relevance-includes-who; mechanics undocumented in docs/ | YES | `scene.py:349-390`; wired `direct.py:273`; proven `tests/test_subject.py` | BUILT (code-first; no owning design doc) |

### Relationships

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Directed per-perceiver multi-axis edges (trust/affinity/respect/debt) reaching the actor as banded phrases | `relationships.md:13-19` | YES | sheets → `_build_edges` `scene.py:289-333` (present-entities only) → `direct_edge` `direction.py` | BUILT-AS-SPEC'D. **No longer a static read (2026-08-22)** — `bonds` moves them per beat, gated by `bonds.witnessed` (a subtle act needs perception; pinning one on a stranger needs insight — both on gate.py's own DCs). Keys must still equal `world.people` ids |
| **The signed, level-anchored edge UPDATE** (bond-arithmetic.md s6 — the act's word on a ladder; same wing: the rung one past the act is the ceiling; crossing: prediction error weighted by the word; stake in the object; per-witness rates; cliff on the floor word; the seat's debt entries) | `bond-arithmetic.md` s6 (normative since 2026-09-17); `relationships.md:24-31` as intent | **YES (built 2026-08-22; the law replaced 2026-09-17, gate 4)** | `src/engine/bonds.py` — `law_delta` / `observe(stake=, rates=)` / `stake_of` / `rates_of` / `cliff_axes` / `debt_postings` (2026-09-18: from the seat's `transfers`); `_ALPHA_NEG` 0.30 > `_ALPHA_POS` 0.12 as the defaults, `relationship_priors.update` per witness; cliffs on the floor act word AND relevance, attribution-shaped; producers in `floor.bond_moves` (scene) and the chair block (direct) → `TurnCommit.rel_deltas` + `rest_rows`; suites `tests/test_bonds.py`, `tests/test_bond_law.py` | BUILT-AS-SPEC'D, and it fixed a DIRECTION defect the ledger had not caught: `arc.assess` ran on the SPEAKER, so a betrayal dropped the **betrayer's** trust in their victim (measured 0.80→0.7828) while the victim's edge never moved. It also had negativity bias INVERTED — resilience buffered damage, so at resilience 0.90 a kindness moved trust 6.0× further than an equal betrayal. Both are gone; `arc.py` no longer writes edges at all (`apply` still replays stored ones — rule 2) |
| **Second-order belief** ("what A thinks B feels about A") | `relationships.md:43` (rich layer) | **YES (built 2026-08-22)** | `bonds.reflect` → `edge["their_view"]`, fired only on a RECEIVED act, cliffs off; since gate 4 it reads the act's AFFINITY word only (trust and respect never feed `their_view`); rendered by `direct_edge` as *"and as you read them, …"* | BUILT-AS-SPEC'D. Unrequited attachment was previously unrepresentable — someone who adores a person they know to be indifferent stored exactly what someone who believes it is returned stored. The build's own test falsified its gate's frame assumption (that both orders read an act identically) and the assumption was retracted in the gate rather than the test being adjusted |
| Drift toward REST (absence cools — toward where the edge was authored, not toward a stranger) | `relationships.md:30`; `bond-arithmetic.md` s6 | **YES (built 2026-08-22; per-edge rest 2026-09-17, gate 4)** | `bond_rest.drift()` toward `bond_rest.resolve` of the `rest_declared` rows (schema v28: `authored` at run creation / late join / pre-v28 resume, `cliff` on the causing turn; append-only), wired at SCENE START in `scene.py` on the gap DERIVED from the scene's required `at` (2026-09-10, `clock.py`); `bond_rest.rehydrate` folds rests, declarations and movements in log order on resume; per-axis retention with affinity fading fastest and debt slowest; **an undeclared edge is BORN whole at the stranger's rest** (`bond_rest.whole`, 2026-09-19, gate `stranger-edge-birth`) at every birth site — the fold's first movement, `floor.bond_moves`, both drivers' apply, `tests/bond_replay.py` — so `default_trust` applies at the first meeting, not only as a drift target | BUILT-AS-SPEC'D beyond the declared MVP skip. Not per-beat — a beat has no duration, so drifting per beat would cool a friendship over one conversation. **Per beat since 2026-09-24 (gate slow-tiers-run):** beats carry minutes since 2026-09-10, so that premise ended; a half-hour conversation now drifts an edge by its half-hour (about 0.2% of the way home on affinity, the fastest axis), for every cast member, and the fold replays the same stretches (`clock.time_items`). This is also the first runtime reader `baseline.relationship_priors` has ever had. Until 2026-09-19 the edge was created EMPTY and read .50 on the axis it lacked (found live, on a real book: a cast member with no authored edge) |
| Relationship-conditioned STATE (ally present → fear ×0.7) | `decision-engine.md:95-97` | YES (2026-08-22) | `levers.py` `present_edge`/`target_edge` rows incl. `_at_most` for enemies | BUILT-AS-SPEC'D — via the catalog, not via appraisal (appraisal itself has no relationship term) |

### Arc engine

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Durable-write threshold; menu-typed diffs; magnitude = impact × durability × (1−resilience) | `arc-engine.md:5-35` | YES | `arc.py:52-105` (`_ARC_THRESHOLD` 0.18); applied in-loop `direct.py:305` + scene runner; persisted `ledger.append_arc_diff`; resume replays; `tests/test_arc.py` | BUILT-AS-SPEC'D with named deltas: `durability` read from the actor's tag + severe-dim heuristic, NOT from the catalog's `durability_class` row (record-contract.md:28 assigns it there); type table subset — betrayal/violence/loss/mastery/connection built, **humiliation and meaning rows unbuilt** (humiliation needs shame/DISGUST) |
| Resilience DERIVED never stored; damage-vs-growth fork (PTG at ≥0.70) | `arc-engine.md:33-42` | YES | `arc.py:35-49` (meaning-frame term defaulted out — documented TODO), `_PTG_RESILIENCE` :45 | BUILT-AS-SPEC'D (3 of 4 resilience terms) |
| Backstory = pre-run arc (generation runs the same diffs) | `arc-engine.md:44-49` | NO | generation pass unbuilt (see Character generation) | SPEC-ONLY |
| Regard generalization (a bond erodes class-disregard) | `arc-engine.md` type table row 6 spirit | YES | `arc.py:84-85` (`_REGARD_GENERALIZE`), `test_subject.py` | BUILT-AS-SPEC'D |
| Readings receipt: RECEPTIVITY/SELF-REGARD (no `_DIM_TO_PATH` row) priced from a durable reading's height, not a dimension, summed with any dims-priced term on the same path; `wound._PATH_CLASS` derived from `_DIM_TO_PATH` instead of hand-written | `arc-engine.md` §Pricing the diff (2026-09-19); `emotion-arithmetic.md` §5 step 7 | YES | `arc.py:157-175` (the receipt loop, after `price_for`); `wound.py:_class_from_dims` (LEVITY now classes as `relief`, not the hand-written `mastery` — `relief` .20 outweighs `mastery` .15); `tests/test_arc.py` [16]-[18], `tests/test_wound.py` [10]-[12] | BUILT-AS-SPEC'D — gate `heights-price-arc`; owner decision D3: readings-only for the two paths, no new `_DIM_TO_PATH` rows authored |

### Consolidation, records, measurement

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Actor self-reports tags in the SAME pass as prose (no interpreter) | `consolidation-loop.md:12-15` (P1), `design.md:80-81` | YES | one-pass JSON contract `prompt.py:62-88`; validated not mined | BUILT-AS-SPEC'D |
| Mechanical validation: schema / containment / capability; strip illegitimate dims; ok=0 moves no state | `consolidation-loop.md:27-43` | YES | `consolidation.validate_tags` :337-489; wired `direct.py:run_turn` | BUILT-AS-SPEC'D |
| Confidence composite + θ_conf escalation | `consolidation-loop.md:56` (open-Q 2, resolved) | YES | `compose_confidence` :314-334, `THETA_CONF = 0.45` :66 (NB: a comment at :47 says "(0.70)" — stale comment, the constant is 0.45) | BUILT-AS-SPEC'D — but escalations route to a HUMAN; the recorder-agent path is an unwired seam (`orchestration.md:95`) and the LLM critic deliberately does not exist in-engine (`consolidation.py` invariant 4) |
| Event catalog: one artifact, four jobs (appraisal_map / world_map / durability_class / visibility) | `record-contract.md:19-31` | YES | `consolidation.CATALOG` :88-257 (15 content + 2 system rows; + `capability_req` beyond spec); completeness vs `ledger._project` tested | BUILT-AS-SPEC'D — EXCEPT the dialogue-act family (next row) and arc reading durability from tags not the catalog |
| **Dialogue-act events** (assert/rebut/concede/… + target) and **stance snapshots** | `record-contract.md:15-16`, `multi-character.md:35-36` | NO | `schema.sql:115-131` tables exist, comment "writer lands post-spine"; not in CATALOG; zero producers | **SPEC-ONLY** (tables idle) |
| `recall` events + relationship-delta log + manifests persisted | `record-contract.md:12-14` (audit A1/A2/A3 repairs) | YES / YES / idle | `ledger.append_turn` :96-107 writes recall_events + decision_manifests; relationship_deltas now written from `scene.py` (2026-08-22) | **YES, both drivers, both directions (2026-08-23).** WRITE: `scripts/scene.py` and `scripts/direct.py`, both orders (`RelationshipDelta.order`, schema v8 `relationship_deltas.ord`). The chair was the last half open: its bonds block sat AFTER `append_turn`, so it computed deltas for a turn already written and persisted none — the edge moved in memory, printed a BOND line, and was gone at process exit. Moving the block ABOVE the commit is the repair, and it is the ordering the contract asks for rather than merely a convenient one: appending afterwards would let a rolled-back turn leave orphan edge rows. READ: both scripts refold on resume via `Ledger.edge_deltas_for` -> `bonds.replay`. Before that read path existed NOTHING replayed the table at all, so a resumed cast reverted to sheet-authored edges. Verified live end to end: a `by:` turn persisted its row on turn 0 and a fresh process resumed with it refolded |
| Compensating `correction` events (append-only repentance; fold applies inverse) | `consolidation-loop.md:57`, `measurement.md:19-23` | YES | EMITTER `critic.py` (`world_moving_types` :242, `continuity_flags` :256, `correct_run` :283, `--correct`); FOLD `fold.py` (`corrections` :105, `superseded_ids` :118, skip in `fold` :140) + the cache reach-back `world_events.py` (`_reaches_back_to` :285) + the same skip in the tail replay `snapshots.py` (`divergence` :90); READERS `ledger.py` (`corrections_for` :583, `superseded_events` :586), `cut.py` (`corrected_turns` :32), `doctor.py` (`_corrections` :62); `tests/test_fold.py`, `test_critic.py`, `test_cut.py`, `test_ledger.py`, `test_doctor.py` | **BUILT 2026-09-19** — the inverse is the SKIP, not a per-type inverse table: the fold is from-zero, so a superseded event simply never applies. Pinned over every type in `world_events.TYPES`. CASCADES STILL OPEN (`measurement.md` open item 3): the additive tiers a bad beat already appraised into characters — relationship_deltas, readings, toward, wound rows — stand |
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
| Append-only log, two clocks, pure fold, snapshot-as-cache, atomic turn-commit, loud divergent resume, parking | `world-state-ledger.md:12-24`, `run-lifecycle.md:17-25` (B4, C3) | YES | `ledger.py` (`append_turn` :103, `_project` :570, `fold` :576, `corrections_for` :583, `superseded_events` :586, `resume` :589); `db.py` v7 migrate-on-connect; `tests/test_ledger.py`, `test_pipeline_e2e`, `test_fold.py` | BUILT-AS-SPEC'D. Fold families grow empirically (move/harm+terminal/reveal/seize/destroy-asset/betray/bond/tension), and since 2026-09-19 the fold also SKIPS every id an arrived `correction` supersedes (next row) |
| Future-dated consequences (`effective_at > caused_at`) | `world-dynamics.md:17` | YES (mechanism) | `records.py:34-46`, fold orders by `effective_at` (`schema.sql:28`) | BUILT-AS-SPEC'D structurally; **no producer ever emits one** — delayed pushback never actually happens |
| **`fold_forward(Δt)`** — lazy time, recurrence rates, standing processes | `world-dynamics.md:18-19,29-33` | NO | grep: does not exist | **SPEC-ONLY** — time does not pass off-screen; the world is a recorder, not yet a system |
| **Plausible-response envelope** (factions as collective characters; director chooses within engine bounds) | `world-dynamics.md:20-24`, `present-systems.md` §Factions | NO | no faction store, no envelope computation (the `capability` lore table of `orchestrator-design.md:180` also unbuilt) | **SPEC-ONLY** — world channel 2 entirely on paper |
| Laws: typed store, modality IMPOSSIBLE/FORBIDS/REQUIRES/PERMITS(+excepts), 3-value epistemic, blueprint defaults, completeness/strict | `orchestrator-design.md:154-205`, `guide-content.md:120-224`, `universal-law.md:12,18-19` | YES | `law.py` (`_BLUEPRINT_DEFAULTS` :77, `completeness` :218, `laws_bearing_on` :324, `verdict_for` :340), `bible.py` (`build` :105, strict); `schema.sql:200-223`; `tests/test_laws.py` | BUILT-AS-SPEC'D — the lore-store GATE half. Serve half (shard corpus) and the other typed tables (`locations`/`chronicle`/`capability`/`relations`) SPEC-ONLY; `chronicle:` citations resolve UNVERIFIABLE (`citation.py:145-148`) |
| **Laws consulted while a scene RUNS** | `design.md` layer 6 floor; the store exists to refuse | **YES (built 2026-08-22)** | PRE-FLIGHT: `scripts/scene.py:run_scene` calls `verdict_for` before the beat loop when the scene cfg declares an `act`, and REFUSES a scene an IMPOSSIBLE law denies. POST-ACTION: the turn contract gained an optional `act` from the world's own vocabulary (`prompt.py`, injected only when the world declares laws), and `scripts/scene.py:_law_events` appends a `law-violation` Event carrying the FORBIDS teeth. Suite `tests/test_laws_preflight.py` | **BUILT-AS-SPEC'D** — with two scoped omissions: post-action NEVER retracts (append-only log), and teeth are RECORDED not APPLIED (a consequence is the director's judgment). The act is AUTHORED, not inferred: measured on a real book, `act=None` makes every law bear and nearly all of them deny, so a blanket call would refuse every scene |
| Bible pinning + drift detection (run records what it ran against) | `orchestrator-design.md` §7 spirit | YES | `bibles`/`bible_entities` tables; `bible.for_run` :484, `drifted` :182; `tests/test_bible.py` | BUILT (beyond the docs — code-first addition) |
| Citation grammar, resolver, 3-state verdict (resolved/unresolved/UNVERIFIABLE), corrupt control | `grounding.md:41-62`, `orchestrator-design.md:301-307` | YES | `citation.py` (`_RESOLVERS` :135-143; entity/law resolve via bible :175); `tests/test_citation.py` incl. sabotage control | BUILT-AS-SPEC'D — `law:` now RESOLVES (store built), superseding the design's "unverifiable until lore store exists" |
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
| Urge-to-speak scheduler | `multi-character.md:8-20` (stake + addressed + disagreement×conviction + affect + relationship_defense − social_inhibition; **softmax temperature**; interrupt threshold) | YES, reduced | `scripts/scene.py:44-47,107-131`: salience(counterfactual appraise) + addressed_bonus + disruption_stake(social_violation × schwartz order-values) − recency − inhibition(extraversion); deterministic max, `_FLOOR_THRESHOLD` 0.06 | **BUILT-DIFFERENTLY** — no temperature, no interrupt threshold, no relationship_defense/conviction terms; recency substitutes as the anti-monopoly. `scene-brief-blueprint.md:6` documents the BUILT formula as canonical while `multi-character.md` still specifies the fuller one — read blueprint for what runs, multi-character for the roadmap; 2026-09-19: lands_on consumed (pruning) and persisted (v31) |
| Addressing (target field, addressed_bonus, threads) | `multi-character.md:22-23` | YES | `addressee` in the tag contract (`prompt.py:70-73`); bonus in `_urge` | BUILT-AS-SPEC'D |
| Stance dynamics `{position, conviction}`, backfire/hardening, convergence detection (concede/flip/decision-forced) | `multi-character.md:28-39` | NO | no stance store; exits are lull / walkout / empty only (`scene-brief-blueprint.md:6-9`); `stance_snapshots` table idle | **SPEC-ONLY** |
| Scene persistence + resume rehydration (arc diffs + acquired vault + affect), witness propagation, overheard name-reveal | `driving-the-engine.md:104-111` | YES | `scripts/scene.py` commits per beat; `--resume`; `tests/test_scene_persistence.py`, `test_scenes.py`, `test_scene_config.py` | BUILT-AS-SPEC'D |
| Seed variation for K-sampling (seed = base×1000 + beat) | `bounds-experiment-design.md` §10.1 | YES | `scripts/scene.py:173-179`, `--seed-base` | BUILT-AS-SPEC'D (the replication hazard fixed) |

### Prose out & the cut

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| POV-bounded narrator (POV thoughts + everyone's observables; multi-POV = switch per scene) | `narration.md:10-24` | YES | `scripts/narrate.py` (+`--book` per-scene recorded POV); `tests/test_narrate.py` | BUILT-AS-SPEC'D. Note: the adapter license (compress/heighten/reorder, never change what happened) lives in narrate.py's docstring — no docs/ file carries it |
| Per-paragraph source event-IDs + mechanical provenance/POV audits on rendered prose | `cutting-room.md:45-46` | NO | narrate emits no event-ids; no render audit exists | **SPEC-ONLY** |
| Dailies views (shot list, biggest moments, arc hinges, acquisitions) | `cutting-room.md:13-24` | YES (4 of 7) | `scripts/cut.py`; `tests/test_cut.py` | PARTIAL — consequence-graph view, tension profile, and unwitnessed-scenes view unbuilt (the manifests + deltas the graph needs are only half-persisted — see Relationships) |
| EDL (append-only edit decisions; SCENE/SUMMARY/BREAK/NOTE) | `cutting-room.md:26-36` | **YES (built 2026-09-05)** | `src/engine/edl.py` (`validate`, `append`, `entries_for`, `traces`); wired into `scripts/cut.py` `--edl`/`--revise`/`--show-edl` and `scripts/narrate.py` (renders from recorded EDL entries) | **BUILT-AS-SPEC'D, status corrected 2026-09-19** (previously read SPEC-ONLY; the record, its render path and its trace audit all exist now) |
| Continuity+voice critic (detect-only, strong model, `--prompt-only` seam) | `design.md` layer 6, hybrid split `measurement.md:19-23` | YES | `scripts/critic.py`; `tests/test_critic.py` | BUILT-AS-SPEC'D for the LLM half; mechanical half = validate_tags + probe detectors; the critic's thin prompt (facts+prose only, no events/state/ledger slice) is a flagged unwired seam (`orchestration.md:94`) |

### Probes & experiment harnesses

| mechanism | specified in | built? | where | divergence |
|---|---|---|---|---|
| Coherence probe (walking skeleton, N turns, detectors, corrupt + stub controls) | `probe-plan.md:50-80` | YES | `tests/coherence_probe.py` | BUILT-AS-SPEC'D |
| Director-via-circumstance probe (role-separated, beat-blind, judged, multi-case) | `probe-plan.md:8-32` | NO | `tests/probe_director_circumstance.py` is a stale prototype (foreign idiom, hand-rolled "R7StateManager") — not the probe; only the 2026-06-06 biased smoke test has ever run | **SPEC-ONLY** (the file's existence overstates it) |
| Cut probe (faithfulness/shape/distinctness/transcription control) | `cutting-room.md:54-60` | NO | — | SPEC-ONLY |
| Lever-eval harness (K-seeded A/B, extractors, rates) | `driving-the-engine.md` | **RETIRED 2026-09-10** | `scripts/exp.py` moved to `staging/scripts/exp.py` — it imported the default fixture's since-replaced cast ids, named experiments in the primitive vocabulary, defaulted temp 0.7 against its own temp-1.0 rule, and nothing tested or called it (`bounds-experiment-design.md` §10.3 said pin or retire) | **DOC-STALE, CODE RETIRED** — the FINDINGS table numbers stay pending re-measurement (`driving-the-engine.md:61-68`); the next harness is `bounds.py` per the design |
| Bounds battery runner (`scripts/bounds.py`) + arms | `bounds-experiment-design.md` §6, §10.2 | NO (runner) | D2 and D3 ran and are recorded in-doc (D2 falsified bound #3); no `bounds.py` | SPEC-ONLY (pre-registered, deliberately) |
| The appraiser seats as the emotional input (spec section 5 steps 1-3, 7-8) | `emotion-arithmetic.md` §5, §7 | YES (2026-09-11) | `scripts/appraiser.py` `read_event` / `read_emotion` called by both drivers after the actor's turn; `state.receive`; `targets.bind_readings`; `arc.assess(heights)`; `wound.trial` reads the reading's height; readings + lands_on ride `append_turn`; `scripts/provider.py` is the one model seam (frontier model, temperature 0, cached prefix, logged) | BUILT-AS-SPEC'D for steps 1-3, 7, 8; step 5's lands_on term is logged not consumed; `toward.observe` still reads the event seat's dimensions; the actor's self-tags are the `--stub` double and the refusal fallback |
| The read-along bench (a novel through the seat and the engine, scored as prediction) | `emotion-arithmetic.md` §5 (2026-09-11 note) | YES (2026-09-11) | `scripts/readalong.py` (segment / run / score), `tests/test_readalong.py` on a synthetic text; the corpus + sheets under `$SWE_BOOKS/readalong/` | BUILT; not yet run on the frontier model (the key file is the owner's) |
| Book lint (vault/edges/location/goals/genotype/catalog/engine-wound assertions; `fears_wounds` refused since 2026-09-11) | `world/character/scene-authoring-rules.md` | YES | `scripts/lint_book.py`; `tests/test_lint_book.py` | BUILT-AS-SPEC'D |
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
   `compounds.py` (retired to staging 2026-09-08)** — stale within a day of being written; the layer exists as an engine module
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
| emotion basis / compounds / naming a vector | `emotion-basis.md` | `staging/src/engine/compounds.py` (retired 2026-09-08) (+`records.py` PRIMARIES) | built 2026-08-22/23 — `PRIMARIES` is 8 and `targets.retarget` is live; `recognise` still reads MAGNITUDE only, so a role-differing pair (pride vs excited) is indistinguishable to it |
| the decision itself | `decision-engine.md` | no module — the LLM at the harness; `prompt.py` is the contract | by design |
| numbers→words seam | `design.md` §split | `src/engine/direction.py` + `prompt.py` | closed 2026-08-22 — the 13 leaked floats are gone and `tests/test_no_digits.py` guards it |
| knowledge / vault | `knowledge-model.md` | `src/engine/vault.py` (store) + `acquisition.py` (growth) | trust-gating built — `acquisition.witness_belief(..., trust=)` :104; frontmatter keys OTHER than type/id are silently dropped by `vault.parse_note` :30 (the whitelist is `vault.py:40`) (`source`, `pulled`, `note` exist in real books and never arrive) |
| recall + perception | `relevancy-gate.md` | `src/engine/gate.py` | flat vault; class-name triggers |
| scene assembly / the packet | `scene-assembly.md` | `src/engine/scene.py` | — |
| relationships | `relationships.md` → `bond-arithmetic.md` (2026-09-17) | `src/engine/bonds.py` owns the act and the LAW (s6: signed, level-anchored; `law_delta` / `observe` / `stake_of` / `rates_of` / `cliff_axes` / `debt_postings`), wired in BOTH drivers; `src/engine/bond_rest.py` owns where an edge RESTS (`rest_declared`, schema v28 — `authored` rows seeded at run creation / late join / pre-v28 resume, `cliff` rows on the causing turn; `drift` / `resolve` / `rehydrate`); sheet-authored edges enter via `scene.py:_build_edges`; movements persist as `relationship_deltas` (v27: + `object`; v29: + `cause`, the thing a debt row was for) and replay through `bond_rest.rehydrate` with the rest rows and the time declarations in log order; the event seat's `object` + `showed` on the act ladders are the read (`scripts/appraiser.py`), priced at `parse_event_reply` | built 2026-08-23; the seat contract, seam, object plumbing and the law rebuilt 2026-09-17 (bond gates 1, 3, 4); the ledger rule on live scenes lifted with gate 4. `read_api.edges` does not split first- from second-order; 2026-09-19: attachments rendered to the actor (direction.direct_holds) |
| durable change / arc | `arc-engine.md` | `src/engine/arc.py` | — |
| consolidation / tag validation | `consolidation-loop.md` | `src/engine/consolidation.py` | — |
| record contracts | `record-contract.md` | `src/engine/records.py` + `schema.sql` | dialogue-acts/stances idle |
| ledger / lifecycle / resume | `world-state-ledger.md` + `run-lifecycle.md` | `src/engine/ledger.py` (+`db.py`) | — |
| laws / computable denial | `guide-content.md` §Laws (authoring) + `orchestrator-design.md` §7.1 (design); `universal-law.md` (the rubric) | `src/engine/bible.py` | store AND runtime both built — `bible.verdict_for` is called pre-flight at `scripts/scene.py:188` and post-action at `:223`, and scene.py is a Mode A script; superseded text: **no runtime consumer in Mode A** |
| grounding / citations | `grounding.md` | `src/engine/citation.py` + `.claude/hooks/` | Stop-hook unbuilt |
| orchestration (Mode B) | `orchestrator-design.md` (charter) · `orchestration.md` (wiring table only) | `read_api.py` + the three hooks + `.claude/skills/showrunner/` | director.md contradicts the charter |
| character generation | `baseline-generation.md` | `scripts/make_genotype.py` (genotype only); rest hand-authored per `guide-emotional-authoring.md` | composition pass BUILT (corrected 2026-09-19) — library + compose + placement + LLM classification all built (`src/engine/profiles.py`; `scripts/composition_pass.py` `build_classify_prompt`/`picks_from_classification`/`--classify`) |
| multi-character scenes | `scene-brief-blueprint.md` (what runs) · `multi-character.md` (the full spec) | `scripts/scene.py` | reduced scheduler |
| steering / levers / bounds | `driving-the-engine.md` + `bounds-experiment-design.md` | `scripts/direct.py` (the chair); `scripts/exp.py` retired 2026-09-10 to staging | rates pending re-measurement; no harness until one is re-authored against the clock |
| narration | `narration.md` | `scripts/narrate.py` | no provenance audit |
| the cut | `cutting-room.md` | `scripts/cut.py` (views) + `src/engine/edl.py` (the EDL, built 2026-09-05) | EDL wired into `cut.py --edl`/`--revise`/`--show-edl` and `narrate.py`; corrected 2026-09-19, was "EDL unbuilt" |
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
   arrives late, and a book's authored laws refuse nothing while a scene runs (bounds route R9).
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
  rebalancing (a law set that is mostly physics is a legitimate design), and `scripts/critic.py` does NOT
  catch breaches (it asks continuity and voice only — verified, zero law references).
- **Composition** — NO → **PARTIAL**. Library + compose + placement built; the LLM classification
  step is not.
- ~~Still true and unmoved: `compounds.py` (retired to staging 2026-09-08) has no runtime consumer, LUST is reachable by no appraisal
  dimension, and the vault `timestamp` is specified and never parsed.~~ **All three wrong by
  2026-08-24, and this bullet contradicted rows two hundred lines above it — corrected in place
  rather than deleted, because a ledger that quietly loses its own wrong entries stops being one.**
  LUST is reachable: `state._DIM_TO_PATH["attraction"]` weights it 0.45. `compounds` has real
  consumers (`basis_probe` uses `COMPOUNDS`/`blend` as its stimulus source; `separability` and
  `validate` run in `test_targets` and `test_disgust`) — what it lacks is a PIPELINE caller, which
  no doc ever asked for. And the vault `timestamp` is not "specified and never parsed": the word
  appears nowhere in `vault.py`. The real defect is broader — `vault.parse_note` :30 (the whitelist is `vault.py:40`) admits only
  `type` and `id` from frontmatter and SILENTLY DROPS everything else, and the owner's real books
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

**2026-09-19 — one clock, two drivers (`src/engine/passage.py`):**

- **Time declared between openings** — `scripts/scene.py` ONLY → **BOTH DRIVERS**. The scene's
  clock (`clock.py`, 2026-09-10: log the opening, derive the gap since the last one ended, apply
  decay/drift/wound-erosion/arc-erosion/toward-erosion off it) lived inline in `scene.py`, and
  `scripts/direct.py`'s own comment named the asymmetry before anything moved ("This driver
  declares no elapsed of its own"). `src/engine/passage.py:open_scene` now holds the call — lifted
  verbatim, same order, same units — and both drivers dispatch to it: `scene.py` at every scene's
  start, `direct.py` when opened with `--at` (optional `--lasts`; absent, the chair still declares
  no clock of its own and says so on stdout). `--keeper` is now symmetric too
  (`scripts/keeper.py:canon_gate` at the end of a chair invocation that committed turns, same as a
  scene's). Suites: `tests/test_passage.py` (new), `tests/test_driver_main.py`, `tests/test_clock.py`.
  Byte-identical stub probe: `scripts/scene.py --stub` over the same fixture scene, before and
  after, diffed to nothing but wall-clock timestamps.

**2026-09-22 — the fade is derived at replay, as the clock always said (gate `erosion-derived-at-replay`):**
`open_scene` logs a declared gap as its CAUSE and applies the effects in memory; its own comment and
schema.sql said every effect is "DERIVED from it at replay". Only the bond drift was. The attitude,
wound and resting-mean fades were lost on resume, and worse, both drivers re-folded attitude and wounds
after every committed beat from the authored base plus the logged deltas, which erased the scene's own
opening fade at its first beat. `src/engine/passage.py` now carries three folds — `fold_toward`,
`fold_wounds`, `fold_arc` — that walk the log in turn order and apply each declaration's fade at its
place: after the turns before it, before its own turn's deltas (the opening precedes the scene's first
beat, which shares its turn). Between openings the deltas still sum and clamp once, so with no
declaration each fold equals the restorer it replaced EXACTLY. The attitude fade reads each person's
connection from the bonds as they stood at that opening (a truncated rehydrate from
`_authored_relationships`, stamped at load by `passage.stamp_authored`, which both drivers now call
before anything moves a sheet); an unstamped sheet meeting a declared gap raises
`PASSAGE_FOLD_UNSTAMPED`. Logging the fades as rows was not an option: each delta table allows one row
per turn per item, and an opening shares its turn with a beat. ALSO FIXED: the bond timeline handed
`bond_rest.rehydrate` the declaration in MINUTES where `drift` reads DAYS, so a replayed one-day gap
drifted every edge as if 1,440 days had passed (`bond_rest.timeline_rows`, which `Ledger.timeline_for`
now delegates to). ON A REAL BOOK'S RECORDED CHRONICLE (one short declared gap): with the
declaration hidden the folds equal the old restorers exactly for every character; with it they
differ by that gap's fade alone (attitude at most 3.4e-5, wounds 1.1e-5, resting means 0); every
edge sat at its rest at that opening, so the unit fix moves no recorded bond. Suite:
`tests/test_passage.py` [7]-[10]; nine mutations of the fix each turn at least one check red.

**2026-09-22 — the direction the actor received is recorded (gate `composer-direction-recorded`):**
`scripts/direct.py:rung_direction` built the actor's emotional direction on every call — both drivers
reach it through `faithful_turn` — and nothing kept it: no committed beat could say which paths and
rungs the actor was directed with, whether the LLM composer or the deterministic floor chose them, or
that the composer had fallen back (that reached stderr only). It now writes `manifest["direction"]`
(`scripts/composer.py:record`), which both drivers commit with the turn: `by` (composer | floor),
`fell_back` (the error, when the composer was asked and the floor answered), `offered` (every path at
its rung), `selected` (path, rung name and index, primary, the descent flag, and a hash of the block
sent), the composer's verified `about` verbatim, and a hash of the whole direction text. REFS, NOT
PROSE, per `record-contract.md`: the blocks are engine constants, so `rungs.block_for(path, index,
descending)` re-derives each one and its hash shows when the blocks were regenerated. A retry calls
the seam again, so the committed record is the kept attempt's. No `direction` key means the beat built
no prompt (a stub actor, a supplied turn, or a beat committed before this entry). NOT COVERED: the act
seam (`--prompt-only` then `--turn-json` builds the prompt in one invocation and commits in another),
and the composer's own usage in `llm_calls`. Suite: `tests/test_rung_delivery.py` (seven tests; eight
mutations of the fix each turn at least one red).

**2026-09-22 — the room ages with the speaker (gate `non-speaker-decay`):** emotion-arithmetic.md s5
step 4 ("every other present character: decay only") had no move logic: only the speaker decayed, so a
character who listened for five beats aged one beat's minutes when they next spoke, and their mood rows
existed only at their own turns, which is what a resume restored. `src/engine/passage.py:bystanders`
decays every other present character over the beat's minutes, against the same room the speaker's
decay reads, on each one's OWN binds (a fear whose object is in the room fades slower). The moods ride
the turn as `TurnCommit.bystanders` — one `current_state` row per present character per beat, in the
turn's transaction (`RECORD_BYSTANDER_IS_ACTOR` refuses the actor as its own bystander) — and the
manifest's `decay` key records the cause: the minutes, the room and the bystanders. The room's
in-memory moods follow once the commit holds, before the floor reads them. NOT COVERED: a character who
exits stops decaying until the next opening; a character absent from a scene is not aged by that
scene's duration at their next opening (the gap is measured from the previous scene's end) - both
CLOSED 2026-09-24 (gate `absent-age`): the next opening ages each of them over their own time away; the chair
holds no other present character. Suites: `tests/test_passage.py` [11], `tests/test_ledger.py`
(`test_bystander_rows_ride_the_turn`), `tests/test_scene_persistence.py` [4]; eight mutations each
turn at least one red.

**2026-09-22 — the mood is re-derived from the log (gate `mood-from-readings`):** hard rule 2 says every
snapshot is a derivable cache, and for the mood that was false. Each beat's mood lived only in
`current_state`, a mutable cache a resume restores from. emotion-arithmetic.md s5 step 8 logged the
readings so the mood would be re-derivable, and nothing did the derivation. `src/engine/mood_fold.py`
does it. `replay` rebuilds every cached mood, each speaker's and each step-4 bystander's, scene by scene,
from the sheets the run pinned (`bible.for_run`) and the log. It mirrors the driver:
- **Resume.** The arc, bonds, holds, binds and wounds are folded up to the scene's first turn, through
  new `before_turn` / `before` / `seeded_at` bounds on the gate-C folds, `bond_rest.timeline_rows` and
  `targets.binds_for`. The mood carried in is the replay's OWN, never the cache.
- **Opening.** The gap's effects come from `passage.apply_opening`, the application half of
  `open_scene`, split out verbatim.
- **Beats.** Decay first, then the logged readings' receipt or `appraise` on the logged tags. Step 4
  runs where the manifest recorded it, then rules 1-5 on the binds. The profile is rebuilt exactly
  where the driver rebuilds it.

`divergence` measures the replay against the cache. `scripts/scene.py` prints it on every resume
(reported, never repaired). The restore reads the saved mood, BY THE OWNER'S RULING (2026-09-22, "Keep
the mood"): a resume is not a story event, so it must not change how anyone feels; the replay is the
per-resume check that the saved mood still agrees with the log.

MEASURED:
- **Current-code runs.** An invented two-character book, a stub run and a seated run, each fresh then
  resumed after a gap: every cached row is re-derived equal to 1e-12.
- **Tampering.** A tampered row is named at its turn, character and path, and no other row moves, so
  the replay never reads the cache.
- **A real book's recorded chronicle** (three scenes, three engine dates). All rows but two are exact (0.0).
  One character's two rows in the third scene differ (5.8e-3, 9.6e-3), and emulating the two pre-fix
  resume restorers makes
  every row exact. The first is gate B's arc replayed before rest words were seeded. The second is gate
  C's wounds restored without the opening's fade: that character's WARINESS was about a concept whose
  investment is read off a wound. The recorded divergence is exactly those two bugs.

NOT COVERED: chair turns (outside every scene row) stop the replay. (A cliff rest row on a scene's first
beat replayed before that scene's opening drift - fixed 2026-09-23, gate `cliff-after-drift`.) (`connection.held_map`
said the profile is recomputed per beat while the scene driver built it before the opening's fade, so a
scene's first beats read pre-fade investment - fixed 2026-09-23, gate `opening-before-profile`.) Suites:
`tests/test_mood_fold.py`, `tests/test_passage.py` [12].

**2026-09-22 — a book says which systems it runs (gate `systems-registry`):** the owner: *"not every
book needs everything we had ... a plug and play mech for the book so user can decide what scripts
they want the engine to use."* A review of the engine found the unit is a SYSTEM (the block that feeds
it, its per-beat mover, its rows, its prompt line), not a script, and that most of the switch already
existed as absence. What was missing, now built: `src/engine/systems.py` (the registry and
`for_book`, which reads `world.systems` beside `switches` and refuses by code - `SYSTEMS_NOT_A_MAP`,
`SYSTEMS_UNKNOWN`, `SYSTEMS_VALUE_NOT_BOOL`, `SYSTEMS_NOT_SWITCHABLE`); `strip`, which empties an off
system's block right before a scene's people are built (after any resume's folds), in both drivers and
in `mood_fold._resumed`; the three movers gated (`wound.mint`, `toward.observe` / `observe_readings`,
`arc.assess`); and the one absence that LIED - a missing condition rendered the top energy band
(`direction.direct_condition` defaults 1.0 / 0.0) and now says nothing. Switchable: `condition`,
`wounds`, `attitude`, `arc`; the core six are listed, not switchable. A book that declares a set other
than the defaults records it on every beat's manifest (`systems`), and the replay strips by that; no
key, or every system `true`, records nothing and writes exactly the rows it wrote before (a frozen
two-scene run of the previous head re-runs identical). Two agreements fixed on the way:
`arc.derive_resilience` read an absent load as 0.3 - a copy of the attachment prior, never documented
for load - while the memory budget and the stage line read 0.0; it reads 0.0 now. And the replay's
`bond_rest.declared_rows(seeded_at=)` kept only `authored` rows at a scene's first turn, dropping the
director's holds, which are written before that scene's people are built; it keeps both. The pre-run
check stops demanding an off system's block, warns on one authored for an off system and on a
half-authored condition. Suites: `tests/test_systems.py`, `tests/test_coded_refusals.py`,
`tests/test_passage.py` [12]. NOT COVERED: the core six (each needs its own proof of identity when
off); the keeper stays a per-run flag.

**2026-09-22 — energy and stress move (gate `condition-flow`):** nothing moved `current.condition`
after a character was created (BLUEPRINT-character 11.2 said so). The owner ruled the engine carries
energy scene to scene and a scene can override it (C3a), drained by emotional load, time and exertion
(C3b). `src/engine/condition.py`, behind a NEW system `condition_flow` that ships OFF (and refuses to run
without `condition`, `SYSTEMS_NEEDS_UNMET`): a beat costs every present character its minutes and the
speaker its impact (`state.receive`'s own total); fear, anger or grief above the ladder's middle builds
the load slowly; an opening costs the last scene's owed minutes and then rests the declared gap
(v1: every gap is rest); a scene cfg's `condition` list states how a cast member ARRIVES in words the
engine prices (`spent|tired|steady|fresh`, each inside the stage-line band it names;
`calm|tense|strained|frayed`), applied after the rest - with the flow on or off, refused for a book
with no condition system. Both drivers compute the cost with the turn, commit it on the speaker's and
each bystander's `current_state` row, and apply it after the arc has read the condition the beat met.
No new table: the override lives in the scene cfg, which is pinned WHOLE in `scene_cfgs` and never
normalised onto a cfg that lacks it (no existing fingerprint moves). `mood_fold.replay` carries the
condition beside the mood and `divergence` measures the condition column; the resume prints both.
Constants: IMPACT_SPEND 0.2 is DERIVED from a real book's recorded chronicle (per-beat impact median 0.046, p90
0.096; its hardest scene's hardest-hit character summed 1.24 - about one stage-line band at 0.2); the
time, load and rest constants are START values, each with a falsifier in the module. Suites:
`tests/test_condition.py`, `tests/test_systems.py`, `tests/test_coded_refusals.py`. NOT COVERED:
exertion and strength (gate body-exertion); a character absent from a scene is not drained by it; energy
does not limit perception (the owner's question).

**2026-09-22 — the body: strength and exertion (gate `body-exertion`):** the owner ruled (C3b2) that the
READER rates how physically demanding an act is in itself and the engine weighs it against each character's
strength. `src/engine/body.py`, behind a NEW system `body` (off by default; needs `condition_flow`,
`SYSTEMS_NEEDS_UNMET`): `baseline.body.strength` is a WORD (frail/slight/ordinary/strong/powerful) priced as
CAPACITY; the event seat is asked `exertion` ONLY when the book runs `body` - its prompt is otherwise
byte-identical, so every recorded seat reply's sha256 key stands - and answers one word of
none/light/moderate/hard/extreme with a quote the parser checks (`APPRAISER_EXERTION_UNKNOWN`,
`APPRAISER_QUOTE_MISSING`, `APPRAISER_FACT_NOT_IN_ACTION`). A word is priced from minutes-to-exhaustion for an
ordinary body (light 960, moderate 240, hard 60, extreme 10 - START values from the exercise literature's
shape), charged for the beat's minutes (at least one) and divided by capacity; capacity also divides the
waking-time drain (the working assumption the owner was told). Only the READER's word reaches the log: an
actor's own `exertion` key (the stub double, the refusal fallback) is dropped before the commit, so the replay
reads the same word from `turns.tags`. The ladder's words were probed on real prose first: a real book's recorded
chronicle (a sedentary indoor scene: none/light only, the none/light line tightened) and public-domain labour and battle
passages with two independent raters. Also: `systems.strip` empties an off system's block only where the
sheet has one (condition excepted - the drivers index it), so a system that ships off adds nothing to a book
that never mentioned it. Suites: `tests/test_body.py`, `tests/test_coded_refusals.py`, `tests/test_systems.py`.
NOT COVERED: strength does not change over a story (the owner's question); exertion does not raise the load;
a bystander's own effort in someone else's beat is not rated. SUPERSEDED IN PART the same night by gate
`energy-reserves` (below): effort and feeling no longer draw one undivided pool. FOUND, NOT CHANGED: the chair's one-shot seam
(`--turn-json` / `--prompt-only`) passes no `--minutes-per-turn` to the turn, while the REPL does - mood
decay, and now effort, get 0 minutes there (flagged to the owner).

**2026-09-22 — one source, with reserves for the mind and the body (gate `energy-reserves`):** the owner,
asked whether body and mind share one energy: *"mental energy and physical are separate but also come from
the same source. Something like a shared pool but with reserves for each. A person can never use all energy
for one type of activity."* He confirmed the restatement built here. For a book running `body` only,
`condition.split` gives each sheet a `mind_reserve` and a `body_reserve` (a fifth of a full tank each) beside
the shared pool; `energy` stays the sheet's one number and the sum of the three. `condition.draw` pays a
kind's cost from the shared pool, then that kind's own reserve - a beat's impact is the mind's, `body.exert`
the body's, waking time the shared pool and then both reserves evenly - and never the other kind's reserve.
Rest refills each store toward full on one curve, so the TOTAL's rest is exactly the single pool's.
`gate._energy_budget` (memory) reads `mind_view`; `direction.direct_condition` says the mind's band and, when
the body's differs, the body's too ("...; your body is spent, and every movement costs you"). A stated arrival
re-splits the reserves. A condition without the reserve keys is the single pool, byte for byte (the frozen run
of 108f07b and the frozen seat-prompt hash re-run identical). Both drivers and `mood_fold._resumed` split at the
same point. Suite: `tests/test_reserves.py` (the porter keeps a memory budget after hauling all day; the clerk
keeps a body after arguing all day). NOT COVERED: the reserve size is the same for everyone; no word states body
or mind alone.

**2026-09-22 — the gap between scenes follows the standard day (gate `gap-day-and-night`):** the owner, after
raising POV cuts minutes apart: *"we have standard logic, anything written can supersede but no mention is
standard. So if a character was resting that must be stated otherwise if its day they were awake."* Until
this gate `condition.opening` rested the RUN's whole gap (`clock.gap_before` measures from the last scene of
any cast), so a POV cut of minutes rested everyone, a day off the page rested, and time a character spent
off the page in another POV's scene counted for nothing. For books running `condition_flow` now:
`clock.presence_end` finds each character's OWN last presence (the speaker, or one of the room a scene
beat's manifest records under `decay.here`) and that scene's declared end and unspent minutes;
`condition.between` charges the unspent minutes as awake time and walks the gap hour by hour - the night
(22:00 to 06:00, `NIGHT_FROM` / `NIGHT_UNTIL`, START) rests, the day is awake time with no stress load (the
mood off the page is not known); a scene cfg's `condition` entry `{char, gap: rested | awake}` supersedes
(`CONDITION_WORD_UNKNOWN` otherwise); a character's first appearance applies nothing. `passage.open_scene`
and `mood_fold.replay` compute the same gaps from the log. Mood, bonds, wounds, arc and attitude keep the
run-level gap exactly as before (the owner's open issue on absent characters) - for the mood, CLOSED 2026-09-24
(gate `absent-age`: it takes each character's own gap too, and a walk-out's `owed` now runs to the scene's end;
the other four were never stuck, since the folds replay every declared gap onto every character). MEASURED
(`tests/test_condition.py` [8]): A (10:00-10:30), a POV cut B (10:32-10:42) without her, A again at 10:45 -
her own gap is 10:30 to 10:45 and her opening is her last value minus exactly fifteen waking minutes, where
the old rule rested her; with `gap: rested` written she rests; the replay re-derives every condition.
NOT COVERED: the night is the same for every book and character; a chair character whose id differs from
its lower-cased name is not found in its own chair turns; POV scenes still cannot overlap in time
(`CLOCK_RUNS_BACKWARDS`).

**2026-09-22 — a missed tell is never read (gate `tells`):** the design says perception FILTERS what a character
apprehends - "a failed check removes a detail (they didn't notice)" (`scene-assembly.md:46`, `relevancy-gate.md:31`)
- and as built it removed nothing: every actor read the others' acts word for word in "The moment"
(`prompt.compose_event`), so a sign another actor let slip reached a dull listener exactly as a sharp one; the
subtle-cue check only withheld the lexicon's cue NAME. The owner asked where tells could even come from when the
actors play the scenes, and said "Yes" to: the event reader marks the parts of an act only a sharp eye would
catch; a listener who misses them never reads them. `src/engine/tells.py`, behind a NEW system `tells` (off by
default): the event seat, asked only then, quotes at most three signs per act (each checked against the act;
`APPRAISER_TELLS_SHAPE`, `APPRAISER_QUOTE_MISSING`, `APPRAISER_FACT_NOT_IN_ACTION`); the quotes ride the
committed turn; each beat, `tells.for_listener` cuts the other actors' marked signs from the log the speaker's
moment is composed from when the speaker's `perception` misses the subtle-cue line (`gate.PERCEPTION_DC_SUBTLE`),
and a speaker who catches them reads them whole and is told them as a percept (`gate.perception_scope`,
`tells_noticed`); a character's own acts are never cut; the beat's manifest records `tells: {hidden, noticed}`
for the beats the moment shows (`prompt.MOMENT_BEATS`, now named). Off, the reader's prompt and every moment are
byte-identical. Suite: `tests/test_tells.py`. NOT COVERED: energy does not yet change who catches a tell (the
owner's open question - answered the same evening, gate `tired-eyes`, below); the chair's seat is not asked; signs
in the director's situation text are not marked.

**2026-09-22 — a worn mind catches less (gate `tired-eyes`):** `tells.catches` read `baseline.skills.perception`
alone, so a sharp character arriving spent caught every sign a rested one would, while the same character's memory
already shrank with their energy (`gate._energy_budget`). The owner said "Yes" to: tiredness makes tells harder to
catch, reading the mind's side only, for books running both the energy system and tells. `tells.catches(char,
tired)` now weighs the skill by what the mind has left - the memory budget's own reading (the mind's side of
`condition`, less the load's penalty) - down to `tells.WORN_EYE` (0.5, START) of it for a mind with nothing left;
`scripts/scene.py` passes `tired` exactly when the book runs `condition_flow`. A book without it keeps the
skill-only check, byte for byte. Suite: `tests/test_tells.py` [5] (through the driver: the sharp keeper whose scene
file says she arrives spent never reads the other's sign; arriving fresh she reads it and is told). NOT COVERED:
the world lexicon's subtle cues still read the skill alone (`gate.perception_scope`) - fixed 2026-09-23, gate
`tired-lexicon`.

**2026-09-22 — bodily injuries kept as state, healed over time (gate `injuries`):** no act could leave
anyone hurt - the event seat was never asked about harm, a sheet's `current.condition.injuries` was read by no code
(BLUEPRINT-character 11.2 said so), and no actor was told anyone was hurt. The owner ruled "Track injuries as state
similar to props but for now I'm not interested in health bars", then "Heal over time". `src/engine/injuries.py`,
behind a NEW system `injuries` (off by default; needs `condition`, whose block holds a sheet's list): the event
seat, asked only then, marks at most three injuries per act - `who` (an id present, or self), a quote checked
against the act, and a severity word (`minor` 3 days, `serious` 3 weeks, `grave` 3 months then a lasting mark -
START values with falsifiers; `APPRAISER_INJURY_SHAPE`, `APPRAISER_INJURY_UNKNOWN`, `APPRAISER_QUOTE_MISSING`,
`APPRAISER_FACT_NOT_IN_ACTION`); the marks ride the event payload and are folded on demand through the one
reading of live payloads (`scene_facts.payloads`, which `scene_facts.run_rows` now uses too); each beat
`injuries.for_actor` ages every injury the speaker witnessed (`scene_facts.witnessed`) from the beat it was
taken (`clock.at_turn`) and their own sheet's from their own first scene (`clock.first_presence`, gate own-timelines; it was page one) less `ago`; `direction.direct_injuries`
appends one sentence of words to the actor's "what has happened" section; each beat's manifest records
`injuries: [who:stage]`. Off, the seat's prompt, every payload, manifest and prompt are byte-identical. The
reader's lines were probed before shipping (two raters of one model family, public-domain novel passages chosen by
fixed rules: 39/39 alike, then 18/18 alike on count and word) and carry the six doubts both raised, decided alike;
no `serious` or `grave` harm appeared, so those rungs' edges are untested. Suite: `tests/test_injuries.py`. NOT COVERED: no mechanical effect (strength, effort - the owner's D6; answered the same night, gate
`injury-weakens`, below); someone who did not see an injury happen never notices it; a scene file cannot state an
injury taken off-page; the chair's seat is not asked.

**2026-09-22 — a hurt weakens the body while it heals (gate `injury-weakens`):** `body.capacity` priced the sheet's
strength word whatever the body had suffered, so a character with a fresh grave injury hauled at an unhurt one's
cost. The owner said "Yes" to: a serious injury makes the body count one strength word lower until it heals, a
grave one two, a minor one nothing, back to normal once healed. `injuries.WEAKENS` and `injuries.weakening` (the
worst of the character's own injuries still fresh or healing, the log's and the sheet's - never a sum) feed
`body.capacity(char, weakened)`, which steps down the words and never below the lowest; every caller of strength
weakens alike when the book runs both `body` and `injuries`: `scripts/scene.py` each beat for each spender,
`scripts/direct.py`'s chair turn, `passage.open_scene` / `apply_opening` for the gap before an opening, and
`mood_fold`'s replay at its openings and beats - so the resume check still re-derives every cached condition.
Suite: `tests/test_injuries.py` [6]-[7]. NOT COVERED: several injuries weaken as the worst of them only; age and
training do not move strength; the gap is weakened by the injuries active at the opening, not re-checked across it.

**2026-09-23 — the chair keeps pace with the scene driver (gate `chair-parity`):** four gaps the 09-22 audit left
open. `scripts/direct.py` `run_turn` committed attitude deltas and never folded them (only `--resume` did), so a
chair session's attitude stayed where the session opened; it now folds after every commit, as `scripts/scene.py`
does, and prints the folded line. `main`'s one-shot seam passed no `--minutes-per-turn`, so a supplied turn decayed
nothing, and neither call site passed the brief, so the chair's composer always took the deterministic floor; both
now pass both. A supplied turn committed no direction: `--prompt-only` now keeps the direction its prompt carried
beside the chronicle (`<db>.directions/<run>.<actor>.json`, gitignored), and `--turn-json` commits it marked
`via: prompt-only` when run, actor and circumstance match, else `by: none` with the reason. Suite:
`tests/test_driver_main.py` (seven checks; the brief through an in-process spy, since `--stub` never reads it).
NOT COVERED: a prompt step run in another checkout hands nothing over.

**2026-09-23 — a scene's first beat feels the opening's fade (gate `opening-before-profile`):** `scripts/scene.py`
built each actor's profile when it assembled the cast, before `passage.open_scene` faded wounds, arcs and attitude
across the gap, and `mood_fold.replay` mirrored the order - so the resume check agreed with the defect, and for a
scene's first beats a scar that had faded over a month was still felt at its old depth (`connection.held_map`'s
investment). Both now build the profile after the opening (and the director's stated condition); the chair already
did. `connection.held_map`'s docstring said "recomputed per beat"; it now says when. Suite:
`tests/test_opening_profile.py` (a spy proves the rebuild lands between the opening and the first beat with the faded
scar; the replay re-derives every cached mood). NOT COVERED: runs recorded before this gate replay with the new
order, so their resume check reports a divergence at the first beats of scenes whose opening faded something the
profile reads - attributable to this gate.

**2026-09-23 — a beat's own rows replay after its turn's drift (gate `cliff-after-drift`):** `bond_rest.declared_rows`
gave every rest row slot 0 and every hold row slot 1, before the turn's time declaration (slot 2). A cliff that a
scene's FIRST beat wrote shares that turn with the opening's drift, so the resume (`Ledger.timeline_for`, both
drivers) drifted the edge toward the lowered rest before the beat, a value the live run never held, and
`passage.fold_toward`'s view of the bonds at that opening already counted the cliff. The row's source now says
when it was written: `authored` and `director` rows are laid down before the opening (slots 0/1); a `cliff`, or a
keeper's hold, comes with the beat's movements (slot 3). `tests/test_attachments.py` [6] asserted the old order for
exactly this case and now asserts the new one. Suite: `tests/test_passage.py` [cliff]. NOT COVERED: none known.

**2026-09-23 — the room's subtle cues dim with the mind (gate `tired-lexicon`):** the owner's ruling D3 made a
spent mind catch fewer of a speaker's tells (`tells.catches`), and `gate.perception_scope` went on checking the
world lexicon's subtle cues against the raw skill, so the same tired character missed a tell and caught every
faint sign in the room. The eye rule moved into `gate.worn_eye` (with `WORN_EYE`), read by both: the subtle-cue
line now weighs the skill by what the mind has left when the book runs `condition_flow`, through a `tired` keyword
on `perception_scope` and `scene.assemble` that both drivers set from the book's systems. Other percepts
(recognition by insight, props, the plain event) keep the raw skills. Suite: `tests/test_tells.py` [6] (fresh,
spent and energy-off; the two lines agree for every eye and mind; through `assemble`; both drivers pass the flag
exactly when the book runs `condition_flow`), 6 of 6 mutants red.

**2026-09-23 — the composer's calls are counted (gate `composer-usage`):** `rung_direction` asks the composer model
before the actor's call, and both dispatchers write the one `direct.LAST_USAGE`, so the actor's call overwrote the
composer's and both drivers logged a single `act` row: every composer call went uncounted in `llm_calls`. Each paid
call's usage is now kept (`direct.COMPOSE_USAGE`) and logged by both drivers as its own `compose` row - a retry is a
second call - including on a beat later skipped and on a `--prompt-only` step; a floor pick makes no call and logs
none. Suite: `tests/test_rung_delivery.py` (the unit, and both drivers through a scripted model), 5 of 5 mutants
red. NOT COVERED: the `act` row still carries only the actor's last attempt, as before.

**2026-09-23 — the ladders are pinned to the run (gate `ladder-pin`):** both drivers wrote `prompt_versions:
{turn: 1}` whatever the ladders held, so the rung ladders a run was directed from were pinned to nothing and
regenerating them silently changed what past direction meant (the composer audit's finding 11). Each selected
block was already hashed per beat (`composer.record`); what no record held was the ladder as a whole - BANDS
(which rung a value maps to), PIVOTS (where the descent begins), BLOCKS and DESCENT_BLOCKS. `rungs.fingerprint()`
digests the four; both drivers pin it in a new run's config (`prompt_versions.ladders`), every direction record
carries it (`ladders`), and a resume after the ladders changed prints a notice (`rungs.ladders_drifted`) -
detection, not refusal, as the bible pin does. Suite: `tests/test_rung_delivery.py`, 6 of 6 mutants red. NOT
COVERED: the prompt's other text (`prompt.py`'s sections, `direction.py`'s phrase tables) stays unpinned; the
record's `text` digest still pins each direction as sent.

**2026-09-24 — a character's mood ages by their own time out of the room (gate `absent-age`):** an opening
decayed the NEW scene's cast over the run's gap since the LAST scene ended plus that scene's unspent minutes
(`passage.apply_opening`), so someone who sat scenes out, or walked out early, came back feeling as they did
when they left - the owner's open issue on absent characters, approved 2026-09-24 as: they age with story time,
and a first appearance keeps the sheet's mood (as its condition already did). Each character's mood now decays
over `passage.own_minutes`: from the scene reading of the last beat they were in the room (`clock.presence_end`)
to this opening, plus the minutes of that scene they did not spend in it. `presence_end` counts those to the
character's OWN last beat - it counted every beat of the scene, so the rest of a scene someone walked out of was
no one's; now it is theirs, their energy's too in a `condition_flow` book. Presence is `clock.last_present`: the
speaker, or the room a beat's manifest records under `decay.here`; a beat logged before gate non-speaker-decay
records no room, so its scene's whole cast counts - the log cannot tell a listener from a walk-out there, and
staying is what every earlier opening assumed. MEASURED on a real book's three recorded scenes: without that
rule 2 of their 5 openings would move, for a character who spoke one beat before each scene ended and then
listened; with it the run replays IDENTICAL (33 moods, 33 conditions), and so do the frozen golden runs. Someone
in the last scene to its end gets exactly the old number. An opening after a run's first refuses to run without
presence (`PASSAGE_GAPS_MISSING`): a silent skip would freeze every mood. The slow tiers were never stuck and are
unchanged - `passage.fold_toward` / `fold_wounds` / `fold_arc` and `bond_rest.timeline_rows` replay every
declared gap onto every character, present or not. Suite: `tests/test_absent_age.py` (a POV cut, a walk-out, a
book without the energy flow, a log that records no room, the refusal); `tests/test_passage.py` [1]-[2] give
their characters a beat before the opening. 12 of 12 mutants red. NOT COVERED: no slow tier ages by a scene's own
minutes, for anyone, present or absent; the chair ages its one character by its own time and prints no line for it.

**2026-09-24 — the story clock (gate `story-clock`):** the owner ruled the rule every reader of time now follows
(`docs/design.md`, load-bearing constraints): *"their stat runs with or without us looking"* - a scene or a chapter
is where story time is read, never a cause. `clock.elapsed_since` summed the time DECLARED after a turn, which is the
gaps between scenes and nothing else, so a scene's own minutes and a lulled scene's unspent minutes passed for
nothing that read it. It now measures story time from the END of a beat (`clock.beat_end`) to how far the story has
reached (`clock.story_now`: the last committed beat's end, or a later scene's opening); a declaration at the turn
itself still predates that beat's end; a log with no scene reading (before schema v25) sums its declared gaps as
before. First reader moved: the keeper's tensions (`scripts/keeper.py` `_band_temperatures`) now cool over every
minute since they were heated. Suite: `tests/test_clock.py` [5] (two scenes: from beat 0, A's next beat + its
unspent ten + the gap + B = 70 minutes where the declared sum saw 30). NOT COVERED here, each its own gate: the slow
tiers still age only at openings (closed the same day, gate slow-tiers-run, below); the recall gate's `elapsed` is measured from the current beat and stays zero, so
no memory fades in a live run (measured: two stub scenes an hour and a half apart, zero on all ten beats); the
read-along bench never fades a scar.

**2026-09-24 — bonds, scars, attitudes and resting means run on story time (gate `slow-tiers-run`):** the slow tiers
aged only at `time_declarations` - the gaps between scenes - so a scene that lasted half a day drifted no bond, eased
no scar, faded no attitude, for anyone, and a lulled scene's unspent minutes aged them not at all (the opening took
`elapsed` alone). The owner's rule (`docs/design.md`: "their stat runs with or without us looking") made that the
defect it is. Every stretch of story time now ages them, through ONE step, `passage.age` (edges drift toward their
own rest, untouched scars ease, resting means return toward what was authored, attitudes fade on the bonds as they
have just drifted): at an opening by the gap plus the last scene's unspent minutes, and at every beat by the beat's
own minutes for the WHOLE cast, in the room or out of it - both drivers, before the beat's own movements, and the
mood replay at the same point (since gate own-timelines, below: for those in the room, each by their own time). The log already held the cause: `clock.time_items` derives the stretches from
`scene_clock` (each opening's gap + unspent, each committed beat's `beat_minutes`; a declared gap with no reading is
an opening, for logs before v25), and the folds (`fold_toward` / `fold_wounds` / `fold_arc`, `bond_rest.rehydrate`)
replay exactly those. The bond timeline's slots are now rest 0, hold 1, the opening's time 2, the beat's own time 3,
the beat's rows 4. `fold_toward` walks the bond timeline once (`rehydrate(..., rests=)` carries the rests), reading
the connections at every stretch. `clock.beat_minutes` counts a reading's per-beat minutes only for the beats its
declared span holds, so a chair session under one `--at` counts its span once (`clock.beat_end` too). Both drivers'
resume folds stop at the new scene's opening, so a reading an aborted launch left behind no longer ages anyone
twice. MEASURED: every difference in the frozen golden run comes from the new time - switched off, the golden is
identical; on a real book's three recorded scenes the replay moves 24 of 33 moods, by at most 1.3e-4, and the
largest replay-versus-saved difference is unchanged (9.6e-3, the same historical cause). Suite:
`tests/test_story_time.py` (a long scene aged beat by beat, and at every beat every cast member's state equals the
folds; an absentee aged through the scene they missed; unspent minutes at the next opening; an aborted launch; a
chair session's span; a beat's minutes before its own cliff). NOT COVERED: the chair's mood still ages by its own
`--minutes-per-turn` knob, not the story clock; profiles are rebuilt where they were (the held map is not rebuilt
every beat).

**2026-09-24 — memories fade on story time (gate `memory-fades`):** both drivers handed the recall gate
`clock.elapsed_days_since(con, run, turn_no)` - the time AFTER the current beat, zero at the head of the log - and
`decay.calculate_effective_confidence` returns the stored confidence when its time is zero, so NO memory faded in
any live run (measured: ten recall-gate calls over two stub scenes an hour and a half apart, all 0.0). Each memory
now has its own story time: `elapsed` may be a callable, and both drivers pass `clock.days_since` - from the end
of the beat that formed or last recalled the memory to the start of the beat that asks, or from page one for a
memory the sheet carries (since gate own-timelines, from the character's own first scene, `clock.first_presence`);
no reading, no time. A learned memory now carries the turn it was
learned: `Ledger.append_acquisition` stamps `created_turn` on the belief in place (so the vault's copy has it too),
the witness site stamps its two copies, and `Ledger.acquisitions_for` supplies it from the row for rows written
before. The three layers between (`scene.assemble`, `gate.run_gate`, `associative`) pass it through unchanged; a
numeric `elapsed` keeps its meaning. Suite: `tests/test_memory_decay.py` [9] (a sheet's memory from page one, a
learned one from its beat, a recalled one from its recall, core never, no clock none) and [10] (a live two-scene
run: the gate is handed a clock, the sheet's transient memory is whole at page one and a day weaker when the next
scene opens, exactly; every learned memory in the vault and in the log carries its turn). NOT COVERED: the chair
without `--at` declares no clock, so its memories do not fade; stored confidence is never rewritten (derived at
read, as before).

**2026-09-24 — the read-along bench runs on the same story time (gate `bench-clock`):** `scripts/readalong.py` aged
only the mood across a chapter gap and refolded its scars with `wound.fold`, which carries no time, so no scar the
bench minted ever faded - measured on the recorded read-along runs, one book's scars sat at full strength through
about 3,250 story days of chapter gaps. The owner: *"Chapters don't matter to fade mechanics, a chapter can be a
time skip or a change pov."* The bench now takes the drivers' one step, `passage.age`, over each chapter's opening
(the gap plus what the last chapter left unspent) and over every beat's own minutes, folds its scars with
`passage.fold_wounds` (the fold with time in it), and seeds its bonds' rests as the drivers do. A chapter is only
where the clock is read: a change of point of view that skips no time ages nothing. Suite:
`tests/test_readalong.py` [3] (every stretch the log holds is a step the bench took, in order; the bench's own scar
equals the fold of its log; the night before chapter two eased the fever's scar, where the timeless fold did not; an
unreinforced bond rests where the sheet put it). 4 of 4 mutants red. NOT COVERED: the recorded read-along runs are
not re-run (each costs the seat's model calls); `patterns` reads them as recorded.

**2026-09-24 — learned memories fade as meaningful ones (gate `learned-memories-durable`):** every memory learned
during a story - lived (`acquisition.assess` -> `_build_belief`), witnessed (`witness_belief`), a learned name
(`reveal_name`) - carried no `durability`, so `decay.calculate_effective_confidence` filed it as an everyday detail
(0.85 a day toward 0.05): a week after witnessing a durable act, a character barely recalled it. Harmless while no
memory faded; gate memory-fades made it matter the same day. Each is now built `durability: durable` (0.96 a day
toward a floor of 0.35), because the only events that become memories are durable ones and a name is a standing fact;
`Ledger.acquisitions_for` files a row logged before as durable too. Found answering the owner's question about which
memories fade. Suite: `tests/test_acquisition.py` [H]. NOT COVERED: a memory the sheet authors keeps the durability
its author wrote.

**2026-09-25 — each character on their own timeline (gate `own-timelines`):** the slow tiers aged every character by
every stretch of the RUN - each opening's run gap plus the last scene's unspent minutes, and every committed beat, in
the room or not - so a character who first walks on in a later scene arrived with bonds, scars and resting means
already aged from the run's first opening (the recorded book brings one in at its third scene), a sheet memory or a
sheet injury was dated from the run's first page, `clock.gap_before` refused any scene opening before the scene run
LAST had ended whoever was in it, and `clock.parse_at` with schema v25's CHECK refused a day before day 1. The owner
(plan step 3, approved 2026-09-25): each character ages by their own time; the sheet describes a character where they
first walk on; days may be 0 or before; refuse only the same character in two overlapping scenes. Now
`clock.time_items(con, run, char)` is ONE character's stretches: at each opening they are in the room for after an
earlier presence, their own time since (`clock.since_presence` - the arithmetic `passage.own_minutes` applies live,
so the fold and the opening cannot drift), and a beat's minutes only for the beats they were in the room for
(`clock.presences`: the speaker, the manifest's room, or the scene's cast for a beat that recorded none - the rule
`clock.last_present` had). `passage.apply_opening(chars, rest_rows, at, gaps, ...)` ages each character's slow tiers
by that own time and a first appearance by nothing; both drivers and the mood replay age the ROOM at each beat, not
the cast. `clock.first_presence` replaces page one (`clock.opening`, retired) for a sheet memory's age
(`clock.days_since` now takes the character) and for a sheet injury's `ago`. `clock.refuse_overlap`, called by
`passage.open_scene` before anything is logged (a refused opening used to leave its reading behind), replaces
`gap_before`'s refusal - CLOCK_TWO_PLACES_AT_ONCE when the opening's span overlaps one its cast member was in (to that
scene's DECLARED end if they were in the room at its last beat, since a lull ends the talk and not their being there;
to the end of their last beat if they walked out; spans that only touch are allowed), CLOCK_RUNS_BACKWARDS when it
opens before the latest point their own story reached (a scene in their past - the next gate's window). Scenes that
share no one may overlap and run in either order: `gap_before` is a signed measurement (the operator line; declared
only when positive) and `clock.story_now` is the furthest point any scene reached. Schema v32 lets
`scene_clock.at_minutes` go below zero: `db._v32_scene_clock` rebuilds an older table around the schema script (rows
copied as they are; an open interrupted part-way finishes on the next) - its detector matches the old CHECK on a word
boundary, because `beat_minutes >= 0` contains the text `at_minutes >= 0` and a substring test found it everywhere.
Suite: `tests/test_own_timelines.py` ([1] a walk-out stops ageing with the room and takes the rest at its next
opening, live equal to the folds at every beat; [2] two overlapping scenes that share no one, run in either order,
leave all four people identical; [3] a late first appearance walks on as the sheet says and dates its memories and
injuries from there; [4] day -3 read, stored, printed, and a v31 database migrated, interrupted or not; [5] the
refusals in both drivers, and a walk-out free inside the span it left). NOT COVERED: world-level state keeps run
order (tensions cool against `clock.story_now`; `fold.project`'s deaths and knowers fold in turn order); a scene set in
a character's past is refused until gate flashback-windows; the chair without `--at` declares no clock.

**2026-09-25 — a scene set in a character's past is a WINDOW for them (gate `flashback-windows`):** the owner (plan
step 4, approved 2026-09-25), from the worry that set it - *"we've followed X for 43 chapters, why suddenly does he have
these effects?"*: a scene set earlier than the point a character's own story has reached plays them as they were then
(bonds, scars, mood, condition, injuries, the memories formed by then, what their feelings were about) and nothing it
produces reaches their present; for a character new to the story it is where their timeline starts, and for one whose
story has not reached that time it goes on as their story; a notice before it, a report after. Until this gate such a
scene was refused (CLOCK_RUNS_BACKWARDS, gate own-timelines) and every reader of one character's history read their
whole log by turn, so had it run it would have leaked both ways (independent review 2026-09-25, B1-B4). `window.py`
derives it from the log and stores nothing: each character's scenes are classified in run order (a window when it
opens before the latest point their MAIN LINE - their scenes that were not windows - had reached), and a VIEW of their
log (`window.view`) says which of their rows a reader sees - their present, every row but their windows'; inside a
window at time T, their main-line rows from before T and the window's own. Windows do not chain (review I3). Every
per-character reader takes `view=` (default: their present, `window.current`): `clock.time_items` / `last_present` /
`presence_end` / `first_presence`, the three folds, `bond_rest.timeline_rows` and `bond_rest.rows_for` (the rests an
edge drifts toward - a cliff in a window must not lower a rest in the present; found building this, the review had not
listed it), the ledger's `latest_affect` `previous_affect` `raised_by` `last_read_turn` `last_turn` `acquisitions_for`
`timeline_for`, `targets.binds_for` / `repeat_count`, `scene_facts.facts_for`, `injuries.for_actor` / `weakening`,
`decay.fold_recall_history`. The default cannot be read off the log inside a window - before its first beat commits,
nothing in the log says who is in it (a first draft took the story's latest reading and turned a keeper's present into
a window after a scene with other people set earlier the same day) - so the scene driver hands each actor their view for
every read that scene. `window.admit` replaces the clock's refusal: one character in two places still refused, windows
included; a scene in someone's past admitted as a window; the chair refused one (CLOCK_RUNS_BACKWARDS); a window before a
character's first scene refused (CLOCK_WINDOW_BEFORE_FIRST_SCENE - no state of theirs exists before the moment their
sheet describes; the owner's call is pending); a chair with no `--at` right after a window for its character refused
(CLOCK_CHAIR_IN_A_WINDOW - its turns would silently join the window). The resume builds each cast member in their view
of the opening; the notice prints before the first beat and the report after it (`window.report`, words only: new
scars, scars that moved, bonds, feelings toward people, resting moods, memories, hurts). The mood replay replays each
cast member in their view at each scene and carries their mood from their last beat in it. Schema v33: `wound_minted`
UNIQUE gains the turn (review B4), rebuilt as v32 rebuilt `scene_clock`. Suite: `tests/test_windows.py` ([1] THE
DIFFERENTIAL - one story with two windows for one character and once without: her present and her companion's end
identical, moods beat for beat, bonds, scars, means, memories; inside the window she plays from her state after her
first scene and nothing of her second; the newcomer carries it; the second window does not see the first; the notice,
the report, the replay exact; [2] the scar table; [3] the refusals). NOT COVERED: world-level state keeps run order
(`fold.project`'s deaths and knowers - the faithfulness wall's `information` - tensions, the keeper's canon); a refusal
inside `run_scene` comes after the director's holds for that opening are written, as every refusal there did before;
the operator's resume counts of refolded movements count windows too.

**2026-09-19 — attitude decays per RUNG, in minutes (gate `attitude-staircase`):** `toward.erode` was the pre-redesign mechanism — one flat `toward._RETENTION[path]` per DAY for every rung, so a hatred and a flicker of annoyance faded alike — and now steps the ladder exactly as `state.decay_over` does, on the minute clock, at a per-path scale whose bottom rung is that same day rate converted (`toward._attitude_half_life`, anchored to 1e-9 in `tests/test_toward.py` block 16) and whose rung-to-rung ratio is the MOOD staircase's own, so the two tiers cannot disagree about the shape of forgetting; `src/engine/passage.py` hands it MINUTES while `bond_rest.drift` / `wound.erode` / `arc.erode` keep the day conversion. Spec: the redesign's "Decay — per path AND per rung" ("Two tables, one shape"), `docs/emotion-arithmetic.md` §4.

**2026-09-19 — the actor's reply contract drops `social`:** `src/engine/prompt.py`'s JSON reply skeleton and its `tags.social` paragraph still asked for a block bond-arithmetic.md §2 retired 2026-09-17 (`APPRAISER_SOCIAL_RETIRED`) and nothing read; removed (gate `actor-contract-cleanup`), `attribution` kept.

**2026-09-19 — four leftovers the redesign retired on paper, now retired in code (gate `emotion-tier-tidy`):** `state.zone_of` / `_ZONE_EPISODE` / `_ZONE_DISPOSITION` — the two-zone apparatus decay stopped reading at gate 2 (2026-09-12), kept alive only by `test_decay_asymmetry`'s zone-based spike — deleted; the asymmetry test is re-based onto `state._rung_half_life`'s two ladders' bottom rungs directly (`tests/test_state.py`). `scripts/readalong.py`'s `score()` and its `"score"` report key — self-referential, both sides read off the same `readings` table — retired; `state_vs_thermometer` (`patterns`' own key, `_state_vs_levels`) is the comparison `emotion-arithmetic.md` §5 actually reports, and was already the one built. `toward._OTHERS_DAMP`'s "max across others, never a sum" claim (`balance`'s own docstring) is now asserted by `tests/test_toward.py`'s THREE PRESENT block — no prior `present=` in that suite carried more than one other, so max and sum had never diverged. `docs/rungs/DISPLEASURE.md`'s six evicted disposition words are now noted as UNORDERED in that doc — rendering them from `toward` waits on the owner's ordering, not a wiring gap.

**2026-09-19 — the law's fifth input gets a producer (gate `seat-attribution`):** `bonds.act_from_tags` has read `tags["attribution"]` since gate 4 and `_ATTRIBUTION` has priced it since the same day, but no live seat ever wrote the key — every beat priced at `unknown` (full weight). The EVENT seat now answers it: a closed four (`severity.ATTRIBUTION_WORDS` — `intent | negligence | coerced | accident`; `malice` folds into `intent`, `unknown` is the omission, neither offered), with a quote checked the way `showed`'s is (`APPRAISER_FACT_NOT_IN_ACTION` / `APPRAISER_QUOTE_MISSING`; an off-list word refuses `APPRAISER_ATTRIBUTION_UNKNOWN`). `parse_event_reply` writes `out["attribution"]`; both drivers' `applied` already carried the key through unchanged, so neither driver needed a behavioural change. The actor's own `tags.attribution` self-tag (kept above, gate `actor-contract-cleanup`) stays the stub double and the seat-refusal fallback. No re-answer of the recorded beats (testing paused 2026-09-19); the next live scene is the first read of the field. Spec: `docs/bond-arithmetic.md` s4/s6; `docs/relationships.md:29`.

**2026-09-19 — the keeper becomes the third writer of a hold (gate `keeper-attachment-rubric`):**
`scripts/keeper.py:canon_gate`'s docstring named the seam since gate `bond-attachments`
(2026-09-18) and nothing called it; `attach_candidates` / `attach_price` / `attach_scene` now do,
wired in after `rule_scene` with the three guards `docs/bond-arithmetic.md` s3 point 3 names
(never per-beat, never a T2 claim, never a re-price — the last split before/after the classifier
call, since the word is not known until it answers). One new code, `KEEPER_ATTACH_OFF_TARGET` (the
classifier answered about an entity nobody asked it about); `ATTACH_LIFE_CAP` is now also raised
directly against `attachments._LIFE_CAP` outside `validate_block`, since a self-sourced row's
discounted price can never itself trip that check. `canon_gate` gained a `world=None` keyword;
both drivers (`scene.py`, `direct.py`) pass `world=world`.

**Follow-up, same day (review pass):** `_json_object` de-duplicated — `keeper.py` now imports
`appraiser._json_object` instead of carrying its own copy (no cycle: `appraiser` imports nothing
from `scripts/`). **The producer-side gap, found by review:** the match needs an extract whose
object is a registered name, but `build_keeper_prompt`'s `world=None` kwarg was unused — the
noticing pass was never shown the registry at all, so a live reply could only phrase an object in
prose and the rubric could never fire from one. Fixed: `build_keeper_prompt` gains a
"THE REGISTERED PLACES AND GROUPS" block in its system message, only when `world` is a dict (a
`world=None` call is unchanged, pinned by adjacency across the exact seam in
`tests/test_keeper.py`); `notice_scene` gained the same `world=None` keyword and passes it through;
`canon_gate` now threads its own `world` into `notice_scene`, not only `attach_scene`. Measured (a
read-only copy of a recorded book's chronicle db): 244 utterances, 0 extracts, 0 resolutions — the
keeper has never run with a model on that book, so nothing recorded there can exercise the trigger
either way yet; the printed candidate count on the keeper's first live model run is the falsifier.
No live scene has produced the trigger (testing paused). Spec: `docs/bond-arithmetic.md` s3 point 3,
s9 gate 5; `docs/keeper-of-truth.md`.


**2026-09-19 — the correction protocol is BUILT (gate `correction-events`).** `consolidation-loop.md`
open-Q 3 had been DESIGNED since 2026-06-10 and had an emitter, a fold rule and consumers in the
doc and none of them in the tree: `grep 'type="correction"'` returned nothing, `fold.project` had
no branch for the type, and the first model critic pass over real prose (2026-09-18) found fourteen
continuity contradictions that the record had no row able to carry. Now: `critic.py --correct`
appends ONE `correction` per continuity flag at the run's NEXT tick (`latest_turn + 1`), naming in
`supersedes` the flagged turn's world-moving event ids — derived from `CATALOG.world_map`, never a
hand list — and idempotent on `(turn, issue)`; `fold.fold` collects the superseded ids over the
whole arrived log BEFORE projecting and skips them, which is the inverse delta because the fold is
from-zero; `ledger.corrections_for` / `superseded_events`, `cut.py`'s corrected marker and
`doctor.py`'s per-run count are the consumers (the count is `measurement.md` detector #6). Nothing
is edited or deleted — the bad event stays in the log beside the correction, which is the point.
Three things deliberately NOT built: no inverse for the ADDITIVE tiers a bad beat already appraised
into characters (`measurement.md` open item 3, "design when first hit"), no prose rewrite (the
author's half), and no automatic correction — `--correct` is opt-in because the flags are a strong
model's reading and the owner decides. One side effect worth recording: `CATALOG.visibility` was on
`tests/test_declared_is_read.py`'s known-unread list and is now read — `correct_run` copies the
correction row's declared visibility onto the Event — so that exemption was retired. Exactly one of
the seventeen rows reaches a producer that way; the other sixteen still take `records.py`'s
"public" default.

**Same day, found by building it:** correcting a PARKED run bricked its resume. `snapshots.divergence`
replays the log tail onto the cached snapshot and compares against a from-zero fold; the from-zero
fold now skips the superseded event and the tail replay cannot un-apply what the cache already
folded, so park → `--correct` → one more turn → `resume` raised `LEDGER_RESUME_DIVERGENCE` every
time. A correction is the ONLY event type whose effect lands below its own tick, and
`world_events.append` was invalidating the cache from that tick. `_reaches_back_to` (`world_events.py`
:285) drops it from the earliest SUPERSEDED event's `effective_at` instead — read off the log rather
than off the payload's own turn field.

**And that was only half of it (same day, found in review).** The drop alone passes the obvious test
for the wrong reason: when the only cached snapshot sits AT the bad event's tick the drop removes
every snapshot, `divergence` takes its `cached is None` branch, and the incremental fold IS the
from-zero fold. A snapshot cached BELOW the bad event SURVIVES the drop, and the tail replay then
folds the bad event forward with no skip rule while the from-zero fold beside it skips — divergence
again. `snapshots.divergence` (`snapshots.py` :90) now collects `fold.superseded_ids` over the tail
and skips those ids as it replays. Skipping is exact there *because* of the drop: a surviving cache
always sits below every superseded id, so all of them, and the correction naming them, are in the
tail. The two move together. `tests/test_fold.py` carries all three cases — the narrow one (renamed
so it no longer claims the general case), the general one, and the inverse control where the same
sequence without a correction has an empty skip set and resumes unchanged; the general case was
re-run against the pre-fix replay and goes red with `LEDGER_RESUME_DIVERGENCE`.


**2026-09-19 — a hand-copied pair, recorded rather than lifted (status-docs-sync gate, item 16, not in this gate's FILES scope to fix):** `_keeper_runs` and `_report_lore` are duplicated verbatim (parity by copy, not a shared import) across `scripts/scene.py:1088` / `scripts/scene.py:1103` and `scripts/direct.py:876` / `scripts/direct.py:893`. `direct.py`'s copy of `_keeper_runs` carries two extra docstring lines naming the duplication as deliberate ("Identical to `scripts/scene.py`'s copy — parity, not a shared import, for the same reason the two drivers' `--keeper` help text has always been maintained in both places rather than one"); the bodies and `_report_lore` are otherwise identical. Tidy candidate: lift both into `src/engine/passage.py` (already the one-clock home both drivers dispatch to) or `scripts/keeper.py`. Not done here — the doc-sync gate's FILES do not include a lift, and CLAUDE.md's seven-duplicates lesson is "derive it," not "the docs agent derives it uninvited."

**2026-09-19 — `tests/test_map.py`'s code-line counter undercounts by one comment token per trailing-comment line (status-docs-sync gate, item 18; counter left AS-IS pending an owner ruling on the affected modules' split — see the dated note added to `_shape`'s docstring).** `_shape` (`test_map.py:123`) computes `code = total − COMMENT TOKENS − docstring lines − blank lines`; a `tokenize.COMMENT` token is emitted once per line that carries a comment, whether the line is comment-only or code-with-a-trailing-comment, so a trailing comment on a code line subtracts that whole line from the code count. Measured fresh at HEAD (33f75fc, 2026-09-19) with an independent script (AST-derived docstring line RANGES + tokenize-derived per-line code/comment classification, cross-checked against a second, string-heuristic implementation — both agree exactly): the true count is non-blank, non-docstring, **not comment-ONLY** lines (a code line keeps its trailing comment's line). Five modules exceed `CODE_BOUND` (300) by the true count; the old (buggy) checker's number is alongside for comparison:

| module | old (buggy) code count | true code count | over 300 by |
|---|---|---|---|
| `code_families.py` | 464 | 468 | 168 — **exempt**, 0 defs/0 branches, a lookup table by the existing test-enforced exemption |
| `state.py` | 275 | 332 | 32 |
| `ledger.py` | 299 | 331 | 31 |
| `consolidation.py` | 277 | 308 | 8 |
| `scene.py` (`src/engine/scene.py`) | 261 | 302 | 2 |

All other `src/engine/` modules stay under 300 by the true count. The fix (subtract comment-only LINES, not comment TOKENS) is a one-line change to `_shape`, deliberately not made by this gate: applying it immediately puts four real modules (plus the already-exempt table) over a hard-fail bound with no split authored yet, which is the owner's call, not a docs-sync agent's. `tests/test_map.py`'s `_shape` docstring now carries a dated pointer to this row.