# Driving the Engine — an authoring guide (LIVING / experiment-driven)

**Purpose.** A tested playbook for getting a character to reliably produce an intended behavior — built from controlled experiments, not intuition. Each entry names a lever, a setting, and a **measured firing rate**, because the model is stochastic: "it worked once" is not "reliable."

## The reliability principle
The LLM is stochastic. A single temperature-0 run is one sample, not a law. So every claim here is a **rate over K samples at temperature > 0** ("drive B → exit in 7/8"). Production runs stay temperature 0 (reproducible replay); reliability is measured only in these experiments.

**Sampling requires a varying seed.** Ollama pins a *fixed* seed by default, so temperature alone is still deterministic — confirmed this session (temp 0.9 produced byte-identical output twice). To sample, set `temperature > 0` AND a distinct `seed` per sample (seeds `0..K-1`). That keeps each sample reproducible and the whole experiment re-runnable.

## The levers ("avenues")
**Character-state (shape WHAT they do):**
1. **Drive** (`current.active_goals`) — the standing want. *(Observed: flips argue↔act.)*
2. **Belief / history** (vault) — what the recall gate surfaces into the moment.
3. **Regard** (`model.regard`) — the empathy/bigotry dial; scales care toward a class. The arc lever.
4. **Relationship edge** (`trust / affinity / respect / debt`) — toward a specific present party.
5. **Starting affect** (`current.affect`) — where they open emotionally.

**Scene (shape the DYNAMICS):**
6. **Situation / framing** — the director's setup + rolling context.
7. **Urge knobs** — floor, addressed-bonus, disruption-stake, recency, inhibition (who takes the floor, when it lulls).
8. **Cast / model / thinking.**

## Experiment template
- **Hypothesis:** lever X set to Y produces behavior Z.
- **Method:** freeze all but X; K samples at temperature T>0; A/B vs the baseline setting of X.
- **Result:** rate of Z for each setting.
- **Entry:** X · setting · rate · leave-alone caveat (when applying it would be wrong).

## Reliability bands
With K=6, only large effects are decisive (0/6 vs 6/6). Bands: **RELIABLE** ≥5/6 · **BIASING** 3–4/6 (a coin flip — useful only as pressure, never as a guarantee) · **WEAK** ≤2/6. Any finding that becomes a guide *rule* gets confirmed at K=12 before it's relied on. All rates are scoped to the model + scene they were measured on (currently gemma4:26b-a4b and the retired fixture described under FINDINGS); re-run the battery when either changes — the harness makes that cheap.

## The campaign — eval every lever (the plan)
Each experiment: freeze all but ONE lever · K=6 seeded samples at temp 0.7 · a PRIMARY mechanical outcome (exit flag, tag types/magnitudes, subject/addressee, urge values — grep-able, never vibes) · SECONDARY observables recorded regardless, because EXP-1 proved a lever can move a *different* outcome than the one you hoped.

Levers split into three measurement classes:
- **Deterministic** (urge knobs; regard's appraisal channel): swept exactly in math, no LLM, free.
- **Stochastic** (drive, belief, affect, framing): K-sampled A/B → rates.
- **Hybrid** (regard, relationships — they move BOTH the appraisal math AND the prompt rendering): each channel isolated and measured separately.

| # | experiment | lever | conditions | primary outcome |
|---|---|---|---|---|
| 0 | instrument calibration | (noise floor) | production model, standard moment, K=12 | empty-turn rate + JSON-validity rate — the error bar under every later rate; if empty >~15%, fix dispatch before proceeding |
| 2 | the wall | situation severity | the same obstacle at three severities: mild vs firm vs degrading | the tested character's exit-rate + social_violation magnitude — does the WALL force the break the drive couldn't? |
| 3 | belief / history | vault | baseline vs + a planted scar belief (mild framing, NOT the rejected alienation version) | recall surfacing in thought, care/social_violation magnitudes, exit-rate |
| 4 | starting affect | current.affect | RAGE at the sheet's rest / 0.60 / 0.85 (dose-response) | tag magnitudes + confrontational action verbs + exit-rate — dial or threshold? |
| 5 | regard | model.regard | math channel: appraise() across a regard sweep from near 0 to 1.0 (exact, free) · prompt channel: edge rendering A/B | CARE delta curve (math) · how the character names the other party + action warmth (prompt) |
| 6 | relationship edge | debt/affinity | the tested character's debt on one edge, 0.0 / mid / 0.8 | intensity of the push, naming, exit-rate |
| 7 | framing | director's prose | clinical (the bare fact, stated) vs sensory-proximate (the same fact told close, through what the actor can see and feel) | tag magnitudes + urgency — how much does the director's prose steer vs the sheet? |
| 8 | urge knobs | floor scheduler | sweep ADDRESSED_BONUS / RECENCY / FLOOR / disruption weight over the then-fixture's recorded beats — deterministic, no LLM | floor distribution + lull timing curves ("the quiet actor takes the floor iff weight ≥ X") |
| 9 | model / thinking | cast lever | 26b-a4b think on vs off, same moment, K=6 each | do RATES move (exit, tag discipline), or only prose quality? |
| 10 | integration | all | the full then-fixture scene with best-of settings vs the v2 baseline | scene-level: beats, floor distribution, escalation, the break |

**Order:** 0 (noise floor) → 2 (closes the open break thread) → 3–6 (character-state) → 7–8 (scene) → 9 (meta) → 10 (integration).
**Cost:** ~110–130 thinking samples ≈ 1.5–2.5 hr of background compute, all local/free; EXP-5-math and EXP-8 are free and exact.
**Since 2026-09-11 the appraiser SEATS are never local** (owner: accuracy) — they run on the frontier model through `scripts/provider.py`; only the ACTOR's model is a lever here.
**Infrastructure (one gate):** `scripts/exp.py` (RETIRED 2026-09-10 to `staging/scripts/exp.py` — dead cast, primitive vocabulary, no test; the next harness is `bounds-experiment-design.md`'s `bounds.py`) — was a config-driven harness (character · moment · lever-patch · K · outcome-extractors → rates table + raw JSONL), so every experiment is a config and the whole battery is re-runnable on a model swap.
**Deliverable per lever:** what it moves (measured) · what it does NOT (falsified) · dose curve where applicable · leave-alone caveat · the recipe line ("want X → pull Y to Z").

## FINDINGS — the definitive lever table
*(model gemma4:26b-a4b, the retired fixture described below; K=6 / EXP-0 K=12; temp 0.7, seeds 0..K-1; raw in `exp-results.jsonl`)*

> **Provenance of these numbers.** The battery was run in June 2026 against the THEN-current default
> fixture, since replaced as the engine was separated from the book whose scene it had been
> (CLAUDE.md hard rule 1); today's default is `scene.py`'s `DEFAULT_SCENE`, a different scene. In the
> rows below "the character" is the one whose lever an experiment moved. The rates
> below are reported as measured and have NOT been re-run against the current fixture. Treat any
> figure here as pending re-measurement, not as a claim about the fixture now in `scene.py`.

> **Temperature caveat (2026-06-12).** This battery ran at **temp 0.7 — off-spec.** Gemma 4 is tuned for **temp 1.0** (top_p 0.95, top_k 64; the model ships with these defaults). The off-spec temp inflated empty rates: EXP-0 showed 2/12 empties at 0.7, but a clean re-measure at temp 1.0 on the same prompt gave **0/12 (both thinking on and off)**. Lever *directions* hold (relative A/B within one temp); *absolute* empty rates do not — re-run at temp 1.0 for production figures.

| Lever | What it MOVES (measured) | Does NOT | Reliability | Recipe |
|---|---|---|---|---|
| **Regard** (`model.regard`) | empathy: CARE Δ **0.078 → 0.271** monotonic as regard rose from near 0 to 1.0, floored | — | **EXACT** (deterministic) | raise regard for more empathy toward a class; the floor guarantees a nonzero flicker even at near-zero regard |
| **Belief** (vault) | the MORAL CHARGE: social_violation **0.23 → 0.70 (3×)** with a recalled scar; model weaves the memory in verbatim | exit (0/6) | **STRONG** | plant a belief whose `[[links]]` match the scene's triggers to make a moment land heavier |
| **Affect / RAGE** (`current.affect`) | INTENSITY dial: care 0.67→0.85, sv 0.40→0.62, loss 0.22→0.42 monotonic as starting RAGE rose to 0.85 | exit (0/6) | **RELIABLE** (dose-response) | raise starting RAGE for a sharper push — a dial, not a switch |
| **Wall** (situation severity) | the response MODE: mild→open pleading; firm→**suppressed compliance** (the character complies, affronted); degrading→**tactical code-switch** (argues in the other side's own terms) | exit (0/6 — a hard wall SUPPRESSES, never ruptures) | **RELIABLE** (clear mode shift) | harden the wall for comply-and-seethe; make it degrading to make the character argue in the other side's own terms |
| **Drive** (`active_goals`) | the CONTENT of the push (what the character presses for, how hard) | exit (0/6) | RELIABLE for content | aim the push; never expect it to toggle a rupture |
| **Framing** (director prose) | inquiry (clinical → the character asks) vs **withdrawal/numb** (sensory horror → the character goes still and stops engaging) | — | MODERATE (+empties on heavy prose) | state it plainly to keep the character active; heavy sensory horror can FREEZE them |
| **Relationship / debt** (edge) | little at turn scale (sv 0.37→0.47 over debt 0.0→0.8, non-monotonic) | — | WEAK at turn scale (an arc lever) | don't reach for debt to change one beat |
| **Urge knobs** (`scene.py`) | turn ORDER: a listener takes the floor when salience + addressed-bonus + disruption-stake clears the floor (EXP-10: the quiet third actor crossed at beat 8, urge 0.18 vs the tested character's −0.02, on the third actor's disruption-stake) | what they SAY | EXACT (deterministic arithmetic) | raise addressed-bonus / disruption weight to pull a quiet actor in |
| **Thinking** (dispatch) | latency + texture, NOT reliability. At **temp 1.0** (Gemma's tuned temp), real prompt, K=12: **0 empties both on and off**. ON costs **~6× latency** (46s vs 7.5s); OFF has marginally *sharper* tags (care 0.90 vs 0.82) but a same-prompt repetition tic. | provide a thinking *budget* — Gemma 4 thinking is **binary by design** (no token cap on any backend; brevity directives BACKFIRE, +39–72% trace, one runaway → empty) | **temp-dependent** (the old "~17% empties" was a **temp-0.7 artifact**) | run at **temp 1.0**; keep thinking **ON** unless latency-bound |

### Four load-bearing conclusions
1. **The EXIT/rupture is NOT a turn-level lever.** Across ~90 sampled turns and every lever, the tested character exited **0 times**. At this contained early beat the character reliably *stays* — correct, because the rupture is an **arc/accumulation** phenomenon (built over scenes), not a knob. Stop hunting a one-turn break lever; grow it.
2. **The turn-levers shape WITHIN containment** — not *whether* the character ruptures but the *texture* of the contained response: regard/affect = INTENSITY, belief = MORAL CHARGE, wall = MODE, drive = CONTENT, framing = ACTIVE-vs-NUMB. That is the authoring surface.
3. **Thinking on/off is a latency-vs-texture trade, NOT a reliability one — at the right temperature.** *(Supersedes the prior conclusion 3, which was measured off-spec.)* The earlier "thinking should be OFF, it causes empties" call rested on **temp-0.7** data (off Gemma's tuned temp 1.0). Re-measured at temp 1.0 on the real prompt, K=12: **0/12 empties both on and off** — the empties were the temperature, not the thinking. Thinking-on is reliable; it costs ~6× latency (46s vs 7.5s) for marginally softer tags, buying more varied prose on resampled-identical prompts. The **"thinking-on-always" mandate stands** — no reliability reason to override it. The lever this whole hunt was chasing was never a thinking *budget* (Gemma 4 thinking is binary by design: no cap on any backend — API options ignored, `think` is boolean, brevity directives backfire). It was **temperature**: production must run at temp 1.0, not 0/0.7. Sources: [Gemma thinking docs](https://ai.google.dev/gemma/docs/capabilities/thinking), [Ollama thinking](https://docs.ollama.com/capabilities/thinking).
4. **You author AGAINST the model's prior, not only from the sheet.** The model quietly "rescues" a character whose worldview it resists — e.g. a zealot it keeps softening into a modern skeptic, a brute into a reluctant one. Characters aligned with the prior (cold, competent, sympathetic) need only the sheet; a character *at odds* with it needs the substrate to **deny the concept** the prior keeps supplying — a high-strength belief framing the resisted view as the only one available to the character (*keep the feeling, block the frame*). *(Illustrative, n small:* tagging a resisting character's discomfort merely "unnamed" leaked explicit moral-recognition repeatedly; a conceptual-denial belief held **0 leaks across ~13 beats**.) **Corollary:** the character at their WORST — *losing control* (a rupture, an act of cruelty) — fights both the substrate's stabilizers AND the prior, so like the exit (Conclusion 1) it is an arc-or-**narrator** beat, never a turn knob.

## Memory — the accumulating life (seed · authored · acquired)
A character ACTS from its vault — the recall gate surfaces the salient slice each turn, and they speak
from it; we never put the words in their mouths. The vault is ONE belief set with **three sources**,
distinguished only by `provenance`:

1. **Seed** — what they wake up with: the `## Beliefs` section of their `.md` (`vault.py` loads it).
2. **Authored fill** — memories YOU add for the time we *skip* (this is a book tool; we don't simulate every day, yet the character lives in the gaps). To stand in the months of a village cricket season without running them, add a belief line to Perpetua's `.md` Beliefs:
   `- (0.7, the rained-off final — he stayed behind) Zebedee dragged the covers over the pitch alone in the downpour [[Zebedee]]`.
   `load_book` picks it up next run. Same write-shape as a seed — provenance is the only difference.
3. **Acquired** — what they learn in a scene we DO run. The engine promotes a **durable, subject-bearing turn** into a belief automatically (`acquisition.assess` → `Ledger.append_acquisition`): the claim is the actor's own `summary` tag, `provenance: lived`, linked to the subject. **Deterministic** — the engine reads the committed turn, never the model's introspection (the model can't curate memory it was never shown — it only ever sees the salient slice).

**Recipe — make a beat durable so it's remembered:** the actor's turn must tag `durability: durable`
AND name a `subject`. The vocabulary is **exactly `transient | durable`** (`consolidation.py`
`_VALID_DURABILITY`). An earlier draft of this line suggested `marking`/`reshaping`; those were
never a third and fourth grade and the validator has never accepted them — every consumer reads
durability as a BOOLEAN (`acquisition.assess` and `cut._salience` call `consolidation.is_durable`;
`arc.assess` tests `== "durable"`). Sending either value now raises `TAG_DURABILITY_INVALID` and
the beat is refused; before 2026-08-30 it silently discarded the whole self-report and lulled the
scene. See `standard-vectors.md:144` and its trap #9. Transient beats leave no memory (correct — most moments
don't). The belief then recalls in a later scene when its `[[subject]]` link or claim words match the
triggers. Provenance lets you tell a lived memory from an authored one downstream.

**Status (2026-06-12) — the memory gaps are filled:**
- **Acquired beliefs persist across sessions** (gate `swe-resume-replay`): the chair's `--resume` replays `arc_diffs` (evolved baseline) + `acquisitions` (grown vault) onto the seed char — a resumed character carries everything it became.
- **Witness-propagation** (gate `swe-witness-propagation`): a present bystander acquires a belief from a durable act it watches (`acquisition.witness_belief`) — so characters learn from each other. Now CROSS-SCENE (gate `swe-scene-ledger-persistence`, 2026-06-13): scene.py commits to the ledger, so a witnessed belief persists and resumes with the bystander.
- **Name-reveal** (gate `swe-name-reveal`): `reveal <entity_id> <name>` at the chair flips `known_as` forward and records a "learned" belief, **monotonically** — old "the tall one from the ferry" memories stay verbatim, the name is added going forward, never retro-rewritten. Per-character.
- **Acquaintance-keyed recognition** (gate `swe-acquaintance-recognition`): you recognize who you *know*, not only who you're sharp enough to spot; a stranger still needs the insight check.
- **Faithfulness** (`faithfulness.check_name_leaks` + gate `swe-faithfulness-regenerate-on-reject`): now ACTIVE — `direct.faithful_turn` REGENERATES on a name-leak (an explicit correction, up to max_retries) and REJECTS (records turn-skipped) if it persists, so a name the character can't hold never reaches the chronicle (preserves "recorded as-is" — never edits). The Sonnet/Claude *semantic* critic is the layer above (Phase-2, alongside the continuity+voice `scripts/critic.py`).

**Done since (2026-06-13, the production drive):** cross-scene witness persistence (`scene.py` ledger); **automatic name-reveal** (`acquisition.overheard_names` — a bystander learns a name spoken aloud, gate `swe-auto-name-reveal`); active faithfulness (`faithful_turn`); the continuity+voice **critic** (`scripts/critic.py`, detect-only, gate `swe-critic-continuity-voice`); the POV **narrator** (`scripts/narrate.py`, gate `swe-narrator-pov`). End-to-end slice works: scene → critic → narrate. **Orchestration = HYBRID** (cheap local turns, strong-model critic+narrator). **Still pending:** the critic's rewrite/compensating-event half; the faithfulness *semantic* critic; the cutting room (book-assembly); 1.3 scene-assembly world-state coupling (deferred refinement). **Not built by design:** semantic dedup — it breaks the determinism we chose; structural claim-match covers the common case. The **authored** path covers any gap meanwhile: if the engine doesn't promote a memory you want, write it into the `.md`.

**One clock, two drivers (2026-09-19).** Until this gate `scripts/direct.py` (the chair) declared
no elapsed of its own — a chair session run after a scene had played left every edge, wound, arc
and attitude exactly where the scene left them, however long the chair said it was later, while
`scene.py` ran the identical arithmetic every scene. Both drivers are one engine driven two ways
(CLAUDE.md Modes): `src/engine/passage.py:open_scene` is now the one call each makes to log an
opening and age the cast off it — `scene.py` at every scene's start, the chair when opened with
`--at` (optional `--lasts`), silent about the clock (and saying so) otherwise. Same experiment
methodology either way; a burst run through the chair with `--at` now carries the same decay/drift/
erosion an equivalent scene would.

**The keeper defaults on (2026-09-19, owner decision D1).** Every burst and every scene now runs the
canon gate unless the invocation passes `--no-keeper` — before this, a burst driven the ordinary way
(no `--keeper`) left every quoted line an actor spoke permanently unindexed to the fence, silently,
and this is exactly what a real book's first three live scenes did. `--stub` runs are unaffected (still
ask nothing; a K-sampled experiment stays free and deterministic), and every invocation now closes
with a `lore:` line naming how many sayings are still unextracted — read it the same way you read
the integrity sweep at startup: zero is the state to aim for, not a number to get used to seeing.
`docs/guide-operating.md` "the lore licence's debt" has the full contract and the four message forms.

## Experiment log
### EXP-1 — the break, via DRIVE  *(status: DONE 2026-06-12 — hypothesis FALSIFIED)*
- **Lever:** the tested character's scene drive.
- **A (baseline):** the passive form of that drive — wanting the matter accounted for.
- **B (test):** the impulsive form — inaction-intolerable, wanting it acted on now.
- **Moment:** the character's turn immediately after a soft refusal.
- **Measure:** exit-rate over K=6, temp 0.7, seeds 0–5, gemma4:26b-a4b thinking-on.
- **Result:** **A 0/6 · B 0/6.** No exits at all. The impulsive drive did NOT produce the break — it produced *sharper, more tactical argument* (pressing for action now, with reasons) vs A's mild inquiry.
- **Guide entry — Lever: DRIVE.** Steers *what* a character pushes for and *how hard* (content + intensity), NOT *whether* they switch scene-level modes (no exit at any setting tested). Use it to aim the push; do not expect it to produce ruptures. Leave-alone: if a character is meant to stay contained, the passive form already holds 6/6.
- **Carry-forward:** if the break is wanted, the candidate lever is the WALL's severity (EXP-2), not the drive.

### Authoring a loss-of-control beat — findings  *(status: ILLUSTRATIVE, n=1–3 at temp 1.0, NOT the K-sampled battery; directions only, confirm at K≥6)*
Test beat: one intended loss of control, in a different scene from the battery's, on the same model as the FINDINGS table.

- **Author against the model's prior (→ Conclusion 4).** When the character's worldview resists the model, tagging the discomfort merely "unnamed" leaked explicit moral-recognition repeatedly. The **fix is a conceptual-denial belief** (frame the resisted view as the only one available to the character) paired with a discomfort belief that names no object. After: **0 recognition leaks across ~13 beats**, and the character still acted.

- **Live trigger, not backstory.** A beat that needs a trigger needs it **live, and beyond the character's power to end with a word**. Reported as already over, it gave no trigger; live but ended by the character's first word, it ended, and the beat with it. Place the trigger *in progress*, out of the character's reach to call off — otherwise the character manages it instead of breaking on it. (Extends the Framing/Situation lever.)

- **The rupture stayed contained (confirms Conclusion 1, new scene).** Across 4 runs (~13 beats) the intended loss of control never fired — contained every time. Loss-of-control is not a turn knob here either; per the WHAT/HOW law these load-bearing beats are the **narrator's to lay over the sim's authentic contained truth** — do not fight the engine for them.

- **Practical (scene construction):**
  - **Entry-affect input** — to start a scene mid-state *without* a `--resume` chain (carry a prior scene's emotion forward by director fiat), set `current.affect` directly. **Gotcha:** `affect` is strictly typed — the PANKSEPP keys only; a stray key (a `_note`) raises `appraise: affect has unknown keys` (`state.py`). Annotate elsewhere.
  - **Multi-beat needs ≥2 actors.** `scene.py` passes the floor between cast members; a cast of 1 commits one beat then ends "empty". For a solo-focus beat add a **minimal supporting actor** — flat affect, low agency, a few beliefs that fix their role — to keep the floor passing. It plays that role without becoming a tracked character.
