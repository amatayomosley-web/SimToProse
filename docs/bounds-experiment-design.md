# Bounds Battery — what a director can and cannot make the engine do (DESIGN / pre-registered, not yet run)

**Status: DESIGN, pre-registered.** Nothing in this doc has been run. Every mechanism claim below
was re-verified against the code on 2026-08-22 (file:line cited); every measured number is either
(a) pulled from the active book's chronicle db and cited by run_id, or (b) marked UNPERSISTED
(seen in session stdout only, to be re-measured). The June 2026 battery in `driving-the-engine.md`
is treated as METHOD precedent only: its raw file `docs/exp-results.jsonl` does not exist on disk,
and its fixture was replaced 2026-08-21 — none of its rates are evidence here. Outcome measures
(§3) are registered BEFORE the arms (§6) so no metric can be chosen after seeing a result.

**The question (the operator's, 2026-08-21):** how much can a director steer a character, and
where does the system stop them? Both halves are deliverables — the recipes that work, and the
behaviours that *cannot* be produced, with the cheapest demonstration of each refusal. The second
half is the harder and the more valuable one: a "cannot" is only earned at a pre-declared K on the
single most adversarial configuration we can construct (§8, §9).

Run everything against the ACTIVE BOOK (`$SWE_BOOKS` slug; its two-hander cfg at
`<book>/scenes/scene_01_cfg.json`). This doc names its cast by role — **the GIVER** (an older
authority pressing an unearned gift) and **the REFUSER** (a debt-averse subordinate collecting an
earned wage) — per the private-content rule (`tests/test_no_private_content.py`); the battery's
own configs, variant sheets, and verb lists carry the real names and live in the BOOK's vault,
never in this repo.

---

## 1. Prior evidence: one A/B, n=1 — a hypothesis, not a result

Verified in the book's chronicle db (`<book>/runs/<slug>.db`):

| run | beats | end | what differed |
|---|---|---|---|
| `scene-pilot-a-1787380588` | 2 | lull (UNPERSISTED: stdout showed `max urge -0.017`) | situation text without the gift objects; drives phrased as topics |
| `scene-pilot-a-1787381616` | 8 | walkout (final action turns to the door; `exit` flag itself is not persisted) | gift objects named in the `situation` string; the GIVER's drive rewritten to a physical goal ("get the objects into his coat") |

Same cast, same sheets, same model, zero numbers changed. Tag types over the 8-beat run: care →
aid → aid → aid → care → aid → affront → aid (db, `turns.tags`). Per-beat latency from
`turns.committed_at` gaps: 30–213 s, median ≈ 59 s (thinking on). Two runs of the B-config
(`…1787381033`, `…1787381616`) produced byte-identical turns 0–6 — because `scripts/scene.py:173`
hardcodes `seed=beat`, a replication hazard §10 fixes before any scene-level arm runs.

This is ONE contrast confounded across two edits (situation + drive phrasing). Arm A1 replicates
it at K and factors the two edits apart. Until then it proves only that *some* combination of the
two moved a scene from death-at-2 to a walkout-at-8.

## 2. The mechanism map — verified routes from a director's hand to behaviour

The packet is assembled by `src/engine/scene.py:assemble()`; the prompt by
`src/engine/prompt.py:27 build_turn_messages()`. What actually reaches the actor:

| # | route | carrier | verified mechanism |
|---|---|---|---|
| R1 | situation / event text | user msg, **verbatim** ("The moment:") | `prompt.py:74` interpolates `event_text` raw. The strongest documented lever (design.md: steering = circumstance) |
| R2 | drive | user msg, **raw JSON** with its urgency number | scene runner overwrites `active_goals` with `{goal, urgency: 0.8}` (`scripts/scene.py:143`); `prompt.py:74` `json.dumps(vol["goals"])` |
| R3 | identity numbers | system msg, **raw JSON** | `prompt.py:46` dumps `packet["stable"]` — built from `fixed`+`baseline` only (`scene.py:155 _build_stable`). Measured on the GIVER: **36 decimals in one system message** (traits, model weights, drive priorities, voice.assertiveness) |
| R4 | affect + condition | user msg, **banded prose** | `direction.py` — digit-free by test (`tests/test_direction.py`), band edges 0.25/0.55/0.80, deviation marker at ±0.15 from temperament mean |
| R5 | relationship edges | user msg, banded prose + `known_as` label | `direction.py direct_edge`, same band edges |
| R6 | recall | user msg ("What it brings to mind") | `gate.py:257 run_gate` — trigger-match → goal-salience sort → spend budget `energy×(1−load/2)` at cost `1−confidence` |
| R7 | percepts | user msg, raw JSON incl. fidelity floats | perception wall `gate.py:120–210`; identity behind insight DC 0.55, subtle-attr extraction behind perception DC 0.60 |
| R8 | urge scheduling | never in any prompt | `scripts/scene.py:44–52` — floor 0.06, addressed 0.15, recency 0.20, inhibition 0.10; salience = Σ\|Δaffect\| of the last tags appraised into the listener |
| R9 | world laws | **nothing at turn time** | `bible.verdict_for` / `laws_bearing_on` (`bible.py:400–433`) are called by NO runner — only `lint_book.py` (a warning string) and the Mode-B chat hook `.claude/hooks/ground_from_book.py`. 27 authored laws bind nothing while a scene runs |
| R10 | formative block | **nothing, ever** | `_build_stable` reads fixed+baseline only; `lint_book.py:108` states it: "read by no engine code and no prompt" |

**Load-bearing fact 1 — the number leak (THE CONFOUND).** Hard rule 5 ("numbers never reach the
prompt") holds only for R4/R5. R2, R3, R7 deliver raw decimals; `tests/test_direction.py` guards
only `direction.py`'s own outputs, not the assembled messages. **Consequence: any sweep of a
`baseline` weight changes BOTH the appraisal arithmetic AND a literal string the actor reads.**
Every arm below names which route(s) it moves and how the split is handled (§5 rule 4).

**Load-bearing fact 2 — numbers → affect, never numbers → action.** The whole registry
(`consolidation.py:88 CATALOG` event-type → legal dims; `state.py:89 _DIM_VALUE_KEYS` dim →
weighted model keys; genotype gains) terminates in `state.py:291 appraise()` — an affect delta.
The ACTION is the LLM's alone; `validate_tags` polices the self-reported tags (and strips
illegitimate dims before state moves), **never the action string**. A committed action stands
as-is even when its tags are rejected (`direct.py run_turn`: ok=False → tags move no state; the
action is already in the ledger). The engine's only handles on behaviour are the prompt's words.

**Load-bearing fact 3 — the one authored hard limit.** `state.py:119 _CARE_FLOOR = 0.25`:
regard-scaling of the empathy dims (`care_relevant`, `loss`) is floored at 0.25 — "innate empathy
regard cannot zero out". It binds the ARITHMETIC only. Whether it can ever bind BEHAVIOUR is
computable first (§6 D2): a floored delta ≈ 0.25 × severity × relevance × 0.40 rarely crosses a
direction band in one event, and decay (`CARE r≈0.82`) pulls back per beat — the floor is
predicted invisible to the actor except under sustained bombardment (~5+ consecutive
high-severity care events to cross the ±0.15 deviation marker).

**Load-bearing fact 4 — the recall substrate is currently dead.** All five cast vaults load
EMPTY: the `## Beliefs` parser (`vault.py:22 _BELIEF_RE`) accepts only
`- (confidence, provenance) claim [[link]]`; the sheets' prose bullets parse to zero, silently
(lint now warns). Three of five cast have no relationships. No belief has ever fired in this book
(`recall_events.belief_refs = []` on every row). Every recall arm must first author beliefs in the
parseable form — and this makes the book a clean zero-baseline for R6.

**Load-bearing fact 5 — regard is unkeyed here.** No cast sheet carries `model.regard`; no
person note carries `groups` (`subject_groups` index is empty). The empathy-scoping/bigotry
machinery (`state.py:166 _regard`) is inert in this book until a variant sheet authors it.

## 3. Outcome measures — registered first, all grep-able

Primary measures are mechanical extractions in the `scripts/exp.py` EXTRACTORS pattern. The
battery harness must tee runner stdout to a per-run log (the ledger does not persist scene
endings or urges).

**From stdout (scene runs):** `ended` ∈ {exit, lull, budget, empty} and beat count — regex
`== scene ended: (\w+) — (\d+) beats ==`; lull urge — `max urge (-?\d+\.\d+)`; per-beat urge
triples — the `urges  :` lines; walkout — `>> .* leaves the scene`.

**From the db (both runners):** beats = `COUNT(turns)`; tag-type sequence and per-dim
trajectories (`turns.tags`); affect trajectory (`turns.affect`); validation: ok=0 count, flag
count, escalate count; `acquisitions` count; `arc_diffs` count; recall injections =
`json_array_length(recall_events.belief_refs)`; latency = `committed_at` gaps.

**From single-turn JSON (chair-pattern arms):** `exit` flag; `type`; each dim value; `addressee`;
`empty` (blank action); and two frozen verb lists per scene-class — an ACCEPT list and a REFUSE
list (e.g. take/pocket vs push-back/leave-it) — authored in the battery config **in the book's
vault**, frozen before the first sample, applied to the lowercased action string.

**Denominator rule:** report every rate over valid turns AND over all K. A condition with >2/6
empty/unparseable draws is re-sampled once at seeds 100–105; if it stays >2/6, the condition is
reported as UNSTABLE, not rated (exp.py's abort logic, per-condition).

**Secondary (only if a primary is ambiguous):** blind judge per `measurement.md` §4 — judge ≠
author, no hypothesis, anchored 0–2 rubric, n≥2 judges + agreement. No self-grading; "does it
read well" is never a primary.

## 4. Statistics — what K buys, said plainly

Samples are seeded draws at temp 1.0 (Gemma's tuned profile; `_ollama` defaults, `direct.py`).
Seeds vary 0..K−1 — Ollama's default seed is fixed, so temperature alone does not sample
(`driving-the-engine.md` reliability principle). Same-seed reproduction is COMMON but not
guaranteed on GPU (`direct.py:122`; runs `…1033`/`…1616` reproduced 7 turns byte-identically) —
seeds are labels, never proof two runs are one sample.

- **K=6 vs K=6** decides only extremes: 0/6 vs 6/6 → Fisher exact p ≈ 0.002; 1/6 vs 5/6 →
  p ≈ 0.08 (suggestive only). Bands as in `driving-the-engine.md`: RELIABLE ≥5/6, BIASING 3–4/6,
  WEAK ≤2/6; any rate promoted to a recipe is confirmed at K=12.
- **"Cannot" claims:** 0/K puts a 95% upper bound on the true rate of **39% at K=6, 22% at K=12,
  12% at K=24** (exact binomial). So: exploratory arms at K=6; any bound worth stating runs
  K=12 on the *most adversarial* configuration; the two headline bounds (T7, T8) finish at K=24.
  A bound is stated as "≤ the bound at 95%", never as impossibility.
- **Deterministic arms have no K.** Pure-engine sweeps (D-tier) are exact and free; they run
  first and set the LLM arms' operating points.

## 5. Design rules (the discipline every arm obeys)

1. **One lever per arm.** Everything else byte-frozen: same book snapshot (note `bible.drifted()`
   on resume), same standard moment, same model tag, temp 1.0, thinking ON (the standing mandate;
   `driving-the-engine.md` conclusion 3), seeds 0..K−1.
2. **Standard moment.** All turn-level arms use ONE frozen moment from the settlement scene
   class — the GIVER's press line, the REFUSER acting — stored verbatim in the vault-side battery
   config. Scene-level arms use the two-hander cfg and its variants.
3. **Controls.** Every arm carries its no-lever baseline; the battery carries one planted
   negative control (a nonsense lever change predicted to move nothing — e.g. reordering two
   `material_habits` strings) to price the noise floor of our own inference.
4. **The confound split (fact 1), per route:**
   - *Prompt-only isolation:* sweep a weight the arithmetic never reads. At single-turn scale the
     appraisal reads ONLY the nine `_DIM_VALUE_KEYS` keys (+ genotype/traits via gains); e.g.
     `schwartz.power`, `schwartz.tradition`, `moral_foundations.authority` reach the prompt but no
     single-turn math. (Scene-level, `power/conformity/security` DO enter `_order_weight` — do not
     reuse this trick there.)
   - *Math-only isolation:* sweep a quantity with no prompt presence at all — urge-model
     constants, or `condition.energy` within one condition band (bands quantize R4; the budget in
     R6 shifts continuously) — or measure the math channel exactly and free via direct
     `appraise()` sweeps (exp.py `exp_regard_math` pattern).
   - *Both-route levers* (regard, temperament means, genotype): measure the math channel exactly,
     the combined effect in vivo, and attribute the difference to the prompt route; T2 measures
     whether the raw-digit form (vs banded words) of the prompt route matters at all.
5. **Repo hygiene.** Battery configs, variant sheets (`characters/` extra .md files load as
   additional selectable cast — id = filename stem), authored beliefs, verb lists: all live in
   the BOOK's vault. This repo gains only engine/harness changes under depth gates (§10) and this
   doc. `tests/test_no_private_content.py` must stay green.
6. **Nothing self-grades; runs are never edited.** Failed draws are recorded (turn-skipped) and
   counted; the ledger stays append-only.

## 6. The arms

### Tier D — deterministic, free, run first (pure engine, no LLM)

| arm | question | method | decides |
|---|---|---|---|
| **D1 urge/lull frontier** | exactly which emitted tags keep a scene alive | recompute `_urge` over a grid (type × dim magnitudes 0..1 step 0.05 × addressed ∈ {0,1} × beats_since) for the real cast profiles; replay urges over every committed run's actual tags (EXP-8 pattern) | the lull boundary as a formula; where run `…380588`'s death sat relative to it; operating points for A1/S-arms |
| **D2 care-floor reach** | can `_CARE_FLOOR` ever surface in the prompt? | closed-form: floored delta per event, decay equilibrium delta/(1−r), events-to-cross ±0.15 marker and the 0.55 band edge, for a regard-0 variant profile | the bombardment count T10 must stage; if equilibrium < marker, the floor is proven prompt-invisible and T10 is CANCELLED (bound established by arithmetic alone) — **RUN 2026-08-21: equilibrium 0.918 > marker; the 0.80 edge falls on beat 2. Bound #3 falsified, T10 stands.** |
| **D3 gate starve/flood** | recall's failure modes | `run_gate` sweeps: budget = energy×(1−load/2) vs authored confidence spread; N high-confidence matching beliefs (cost→0 injects ALL — no count cap exists) | the starvation threshold (which beliefs die first — low-confidence ones); the flood point where packet size threatens `num_ctx` 8192 (`direct.py _ollama`); T9's operating points — **RUN 2026-08-21: no count cap exists even at 1000 beliefs; the only ceiling is `num_ctx` 8192. Starve ordering is strict by confidence — low-confidence beliefs die first, as predicted.** |
| **D4 direction quantization map** | which state sweeps are prompt-visible | tabulate exact affect/edge values → banded phrase transitions (0.25/0.55/0.80, dev ±0.15 vs each cast temperament) | legal sweep points for T3/T4 (must cross a band edge or marker; within-band pairs are byte-identical prompts and MUST show no effect — a built-in null control) |
| **D5 prompt census** | what actually reaches the actor | count decimals + fields per message for each cast member (already spot-verified: 36 system + urgency/fidelity user) | the census table T2 bands against |

### Tier A — instrument + headline replication

**A0 — noise floor (K=12, both think settings).** Standard moment, baseline sheets. Measures:
empty rate, JSON-validity, tag-type distribution, latency. Abort rule: >2/12 empties at thinking
ON → fix dispatch before any rate is trusted (exp.py EXP-0 logic; note exp.py's
`sample_condition` still defaults temp=0.7 — every call must pass temp=1.0 explicitly).

**A1 — replicate the A/B and split its two edits (scene-level, K=6 per cell, 4 cells).**
2×2: situation {without gift objects, with} × GIVER drive {topic form, physical-goal form}.
Primary: ended-reason + beat count; secondary: tag-dim trajectories, D1-frontier crossing time.
Predictions: bare/topic dies early (lull ≤3) at ≥5/6; object+physical reaches ≥6 beats at ≥5/6;
the factor split is genuinely open — scene-authoring-rules.md Rules 1–2 predict BOTH matter, the
mechanism map suggests the situation edit (R1, verbatim) outweighs the drive edit (R2).
Falsification of the headline: if the with/physical cell lulls ≥3/6, the 8-beat run was a
sampling fluke and `driving-the-engine.md`'s situation-severity lever needs re-ranking.

### Tier T — one-variable turn-level arms (chair pattern, standard moment, K=6 unless noted)

| arm | lever (route) | conditions | prediction → falsified by |
|---|---|---|---|
| **T1 drive phrasing** | R2 | topic form / physical-goal form / outcome-in-costume ("make him accept before he leaves") | phrasing moves CONTENT and physicality of the act (object-verbs in action), not the exit flag (June: drive never toggled exits; re-test on this fixture) → any exit-rate split ≥5/6 vs ≤1/6 |
| **T2 the number leak** | R3 prompt route alone | identical packet; system msg (a) as-built vs (b) harness-banded (every 0–1 decimal → low/middling/high/very-high word; transform in the harness AFTER `build_turn_messages`, engine untouched). K=12 | digits-vs-words changes nothing reliable (words carry the same signal) → any primary flips band. EITHER way it's load-bearing: no-effect ⇒ weight sweeps stay interpretable AND hard rule 5's breach is consequence-free at this scale; effect ⇒ rule 5 enforcement becomes a build priority and every R3 sweep inherits a prompt-route term |
| **T3 affect quantization** | R4 | RAGE points chosen from D4: within-band pair + cross-band pair (+ marker-crossing pair) | within-band: NO effect (byte-identical prompt — null control); cross-band: intensity of dims/verbs moves (June dose-response), exit stays 0 → within-band effect = harness bug; cross-band flat = the affect lever is weaker than June claimed |
| **T4 edge bands** | R5 | GIVER-edge trust/affinity at low/mid/high band points (variant sheets) | naming, warmth verbs, addressee move; refusal outcome does not → refusal flips with edge warmth |
| **T5 belief as ammunition** | R6 | no belief / statute-form belief / ammunition-form belief (same fact, forms per scene-authoring-rules Rule 3), authored in parseable format, `[[links]]` matched to the moment's triggers | recall fires (belief_refs ≠ [] — first time in this book); ammunition form is woven into action/thought at ≥3/6 vs statute ≤1/6; moral-charge dims rise (June: 3×) → forms indistinguishable, or recall fires without behavioural trace |
| **T6 identity wall** | R7 | a stranger present; REFUSER-variant insight 0.50 vs 0.60 (DC 0.55) | below-DC: "person present" only — actor never names/roles the stranger (0/6); above: does. NOTE the wall gates only what event text withholds — the raw situation string is verbatim (R1), so the cue must live in the people note's identity record, not the event text → below-DC naming >0 means the identity wall leaks |
| **T7 the acceptance ladder** ("cannot" #1) | all state routes vs one saturated disposition | 5 rungs stacking pro-acceptance state against the REFUSER's authored refusal identity: (1) drive-to-accept; (2) +affect (gratitude-adjacent: CARE/PLAY high band); (3) +edges maxed; (4) +an authored belief commanding acceptance; (5) all four. K=6 each; the strongest rung re-run at **K=24** | acceptance stays ≤1/6 through rung 4 (identity prefix + prior wins; June's wall finding: hard pressure yields suppressed compliance, not reversal); rung 5 ≤ 12% at 95% → any rung ≥3/6 accepts kills the bound and yields the recipe instead |
| **T7b circumstance coda** | R1 | the fait-accompli form: the moment states the objects are already in his coat, the GIVER gone | the WORLD moves even though the CHOICE didn't: actor cannot un-receive; measure return-attempt verbs (predicted ≥4/6 — the disposition reasserts as next-turn action) → low return-rate means circumstance quietly rewrote the disposition, which would be the single most surprising result in the battery |
| **T8 law violation** ("cannot" #2 — inverted: what the WORLD cannot do) | R9 | a moment inviting an act an authored IMPOSSIBLE-modality law denies (pick from the pinned `bible_laws`); K=12. Offline afterwards: `verdict_for()` proves the world would deny it; run `scripts/critic.py --prompt-only` on the committed run | the actor performs the denied act at a nonzero rate and NOTHING blocks or records the violation (R9: no runner consults laws; the critic checks bible contradictions — test whether it flags modality breaches) → 0/12 violations means the model's prior alone enforces this law class (also a finding: which laws need no enforcement) |
| **T9 recall flood** | R6 | 5 vs 50 authored high-confidence matching beliefs (D3 sets counts); K=6 | 50 all inject (no cap); prompt swells toward `num_ctx` 8192 → measure token counts + empty/degradation rate; predicted: context pressure degrades tag validity before it degrades prose → no degradation at 50 means the gate needs no cap at book scale |

### Tier S — scene-level (needs the §10 seed fix first)

| arm | question | method | prediction |
|---|---|---|---|
| **S1 exit anatomy** | is the walkout an URGE artifact or a choice? | reuse A1's with/physical cells; align each exit against the D1 replay: was the exit beat preceded by an affront-type escalation crossing the frontier? | exits cluster after affront-tagged beats (the A/B's care→aid→affront shape); if exits appear without escalation, the exit flag is prior-driven, not dynamics-driven |
| **S2 third presence** | does cast composition alone re-route a scene? | two-hander vs +1 authority-figure cast member (existing cast), same cfg otherwise, K=6 | the added `_order_weight` stake changes floor allocation (deterministic half) AND suppresses the walkout (social inhibition in the room) — beat count up, exit rate down |
| **S3 budget ceiling** | does anything happen after the natural end? | A1 cells re-run at budget 30 (K=3, exploratory) | lull arrives ≤14 regardless (the urge economy exhausts); scenes that fill 30 indicate a repetition loop, not content — check the anti-repeat rolling context |
| **S4 (OPTIONAL) bombardment arc** | can accumulation do what no single turn can (the June conclusion-1 claim, and D2's floor) | 5 consecutive short scenes of escalating care events at a regard-0 variant (chained `--resume`), K=3 chains | arc diffs fire (`_ARC_THRESHOLD` 0.18, `arc.py:19`); CARE crosses a band by scene ~4; care-verbs appear where turn-level arms produced none — the demonstration that the slow lever exists. Flagged: 2×K under-powered by §4 standards; run as ILLUSTRATIVE (house precedent: driving-the-engine.md marks n=1–3 findings so) |

## 7. Hypothesis space — the levers, what each is predicted to move and to refuse

| lever | route(s) | predicted to move | predicted NOT to move (the bound) | arm |
|---|---|---|---|---|
| situation text | R1 | scene survival, tag types/severity, physical acts, the world itself | a saturated disposition's choice (only its circumstances) | A1, T7b |
| drive | R2 | content + physicality of advocacy | exit, acceptance-against-wound | T1, T7 |
| identity weights | R3 | (open — T2 decides if the digit form matters at all) | single-turn behaviour when only arithmetic-dead keys move | T2 |
| affect | R4 | intensity, verb heat — in band steps only | anything within a band; exits | T3 |
| edges | R5 | warmth, naming, addressee | the refusal itself | T4 |
| beliefs/vault | R6 | moral charge, woven references, first recall firings | exits (June 0/6) | T5, T9 |
| perception/skills | R7 | what can be named (identity), tag containment flags | what the event text already states verbatim | T6 |
| urge knobs / cast | R8 | floor allocation, lull timing, scene length | what anyone SAYS | D1, S2 |
| laws | R9 | nothing at turn time (verified) | — the world cannot refuse in Mode A | T8 |
| condition/energy | R4+R6 | recall breadth (continuous), condition phrase (banded) | — | D3 (+T5 variant if D3 shows a cliff) |
| scene budget | harness | upper beat bound | content density after the urge economy exhausts | S3 |
| accumulation (arc) | slow loop | baselines, regard erosion, eventually band-crossing state | any single-turn outcome | S4 |

## 8. The bounds ledger — predicted impossibilities and the cheapest test of each

Pre-registered claims of the form "the system cannot produce X"; each falls to a single
countersample and is otherwise bounded per §4.

1. **State cannot flip a saturated disposition in one turn.** No stacking of drive/affect/edges/
   beliefs makes the REFUSER accept in-scene. Cheapest: T7 (ladder; the K=24 rung is the claim).
2. **Only circumstance moves the world; even then the disposition reasserts.** T7b.
3. ~~**The care floor cannot reach behaviour in one event.**~~ **FALSIFIED by D2** (2026-08-21).
   The prediction was prompt-invisibility. The arithmetic says the opposite: from CARE 0.700 the
   floored delta carries 0.700 -> 0.761 -> **0.808**, crossing the 0.80 band edge in **two beats**,
   and equilibrating at 0.918. `_CARE_FLOOR` (`src/engine/state.py:119`) is prompt-VISIBLE within a
   normal scene, not over ~5+ events. S4 is no longer the only path and T10 is NOT cancelled.
   Kept struck rather than deleted: this is the register of what was predicted, not of what is true.
4. **The world's laws cannot refuse anything during a run** (Mode A). T8 — the sharpest
   architecture finding if confirmed: 27 authored laws with zero runtime consumers; enforcement
   lives only in the Mode-B chat hook and the human.
5. **The engine cannot force a named action** — there is no numbers→action path (fact 2); the
   actor can also DO what its tags may not claim (capability flags strip dims, never acts).
   Cheapest: already true by code-reading; T8's committed violations double as the demonstration.
6. **A scene cannot survive below the urge frontier.** D1 gives the exact boundary; A1's bare
   cell demonstrates it live. Corollary bound: no drive phrasing rescues a tag-starved situation.
7. **Within-band state edits cannot reach the actor at all** (byte-identical prompts). D4 + T3's
   null cells.
8. **The actor cannot name what perception withheld** (identity behind the wall) — T6; scoped:
   the wall covers only content kept out of the verbatim event text.
9. **Beliefs cannot fire from prose-form authoring** (parser bound, `vault.py:22`) — already
   demonstrated by five empty vaults + every `belief_refs=[]`; T5's parseable-form conditions are
   the positive control.
10. **No turn-time consumer of `formative`** — R10; bound by code, no run needed.

## 9. Power / cost budget

Basis: single turn ≈ 46–60 s thinking ON, ≈ 18–20 s OFF (`direct.py:108`, June EXP-9); scene
beat ≈ 60–90 s ON (measured median 59 s, §1). All local, free, sequential on the one warm model
(exp.py's `_stop()` between conditions forces cold reloads — drop it; keep the model warm).

| arm | LLM calls | wall-clock (think ON) |
|---|---|---|
| D1–D5 | 0 | minutes, run first |
| A0 | 24 (12 ON + 12 OFF) | ~15 min |
| A1 (2×2 × K=6 scenes) | ~120 beats | ~2.5 h |
| T1 | 18 | ~17 min |
| T2 (K=12 × 2) | 24 | ~22 min |
| T3 | 24 | ~22 min |
| T4 | 18 | ~17 min |
| T5 | 18 | ~17 min |
| T6 | 12 | ~11 min |
| T7 + T7b (30 + 24 + 6) | 60 | ~55 min |
| T8 | 12 | ~11 min |
| T9 (long prompts) | 12 | ~18 min |
| S1 | 0 (reuses A1 + D1) | — |
| S2 | ~60 beats | ~1.3 h |
| S3 (K=3 × 2 × budget 30) | ~90 beats | ~1.9 h |
| **core total** | **≈ 400 calls** | **≈ 8–9 h** background |
| S4 optional | ~90 beats | ~2 h |

Too expensive at proper N, and said so: S4 at a defensible K would cost days — it runs at K=3
labelled ILLUSTRATIVE or not at all. Everything else meets its declared K. If the budget must
halve, cut in this order: S3, S2, T4, T6 — never A0/A1/T2/T7 (the instrument, the headline, the
confound, and the bound).

## 10. Harness prerequisites (before any Tier A/S arm; each a depth-gated change)

1. **Scene seed variation.** `scripts/scene.py:173` hardcodes `seed=beat` → K "replicates" are
   near-copies (§1). Add `--seed-base N` (seed = N×1000 + beat). One line + plumbing; gated.
2. **The battery runner** (new `scripts/bounds.py`, exp.py's shape): vault-side config in →
   conditions → K seeded samples (turn arms in-process via `assemble`/`build_turn_messages`/
   `_ollama` at temp=1.0; scene arms via subprocess with stdout tee) → §3 extractors → rates +
   raw JSONL appended crash-safe to the BOOK's vault (NOT `docs/` — the June battery's raw file
   died of repo-side placement). Includes the T2 banding transform (post-`build_turn_messages`,
   engine untouched) and the D-tier sweeps.
3. **exp.py temp pin.** Its `sample_condition` default (0.7) is off-spec vs its own doc; pass 1.0
   explicitly everywhere (or retire exp.py in favour of bounds.py — it also still imports the
   replaced fixture's cast ids, so it cannot run against the active book as-is).
4. **Fixture beliefs.** Author T5/T9 beliefs in the vault in `_BELIEF_RE` form; re-run
   `lint_book.py` until the vault warnings clear for the cast members those arms use.

## 11. What this battery does not settle

Model-scoped: every rate binds to `gemma4:26b-a4b` + this scene class (June's scoping rule).
Long-horizon coupling (the coherence probe's question) is out of scope — S4 only sketches the
slow lever. Mode-B (showrunner-driven) steering is untested here; T8's law finding explicitly
does not transfer to Mode B, whose chat hook does read laws. And a replicated recipe is still a
rate, not a law: the deliverable table (a `driving-the-engine.md` FINDINGS update) must carry
each entry's K, band, and leave-alone caveat, per that doc's own template.
