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
With K=6, only large effects are decisive (0/6 vs 6/6). Bands: **RELIABLE** ≥5/6 · **BIASING** 3–4/6 (a coin flip — useful only as pressure, never as a guarantee) · **WEAK** ≤2/6. Any finding that becomes a guide *rule* gets confirmed at K=12 before it's relied on. All rates are scoped to the model + scene-class they were measured on (currently gemma4:26b-a4b, the family-dinner class); re-run the battery when either changes — the harness makes that cheap.

## The campaign — eval every lever (the plan)
Each experiment: freeze all but ONE lever · K=6 seeded samples at temp 0.7 · a PRIMARY mechanical outcome (exit flag, tag types/magnitudes, subject/addressee, urge values — grep-able, never vibes) · SECONDARY observables recorded regardless, because EXP-1 proved a lever can move a *different* outcome than the one you hoped.

Levers split into three measurement classes:
- **Deterministic** (urge knobs; regard's appraisal channel): swept exactly in math, no LLM, free.
- **Stochastic** (drive, belief, affect, framing): K-sampled A/B → rates.
- **Hybrid** (regard, relationships — they move BOTH the appraisal math AND the prompt rendering): each channel isolated and measured separately.

| # | experiment | lever | conditions | primary outcome |
|---|---|---|---|---|
| 0 | instrument calibration | (noise floor) | production model, standard moment, K=12 | empty-turn rate + JSON-validity rate — the error bar under every later rate; if empty >~15%, fix dispatch before proceeding |
| 2 | the wall | situation severity | "after dinner" vs "Sit. We will not discuss this." vs "It is a tool. Tools wait." | Brakk's exit-rate + social_violation magnitude — does the WALL force the break the drive couldn't? |
| 3 | belief / history | vault | baseline vs + a witnessed prior worker-death (mild scar framing, NOT the rejected alienation version) | recall surfacing in thought, care/social_violation magnitudes, exit-rate |
| 4 | starting affect | current.affect | RAGE 0.32 / 0.60 / 0.85 (dose-response) | tag magnitudes + confrontational action verbs + exit-rate — dial or threshold? |
| 5 | regard | model.regard | math channel: appraise() at 0.05/0.2/0.6/1.0 (exact, free) · prompt channel: edge rendering A/B | CARE delta curve (math) · naming "Kestra" vs "the worker" + action warmth (prompt) |
| 6 | relationship edge | debt/affinity | Brakk→Kestra debt 0.0 / 0.3 / 0.8 | advocacy intensity, naming, exit-rate |
| 7 | framing | director's prose | clinical ("a worker was injured") vs sensory-proximate ("the frost is settling and she is still out there") | tag magnitudes + urgency — how much does the director's prose steer vs the sheet? |
| 8 | urge knobs | floor scheduler | sweep ADDRESSED_BONUS / RECENCY / FLOOR / disruption weight over the recorded BP1.3 beats — deterministic, no LLM | floor distribution + lull timing curves ("Selven takes the floor iff weight ≥ X") |
| 9 | model / thinking | cast lever | 26b-a4b think on vs off, same moment, K=6 each | do RATES move (exit, tag discipline), or only prose quality? |
| 10 | integration | all | full BP1.3 with best-of settings vs the v2 baseline | scene-level: beats, floor distribution, escalation, the break |

**Order:** 0 (noise floor) → 2 (closes the open break thread) → 3–6 (character-state) → 7–8 (scene) → 9 (meta) → 10 (integration).
**Cost:** ~110–130 thinking samples ≈ 1.5–2.5 hr of background compute, all local/free; EXP-5-math and EXP-8 are free and exact.
**Infrastructure (one gate):** `scripts/exp.py` — a config-driven harness (character · moment · lever-patch · K · outcome-extractors → rates table + raw JSONL), so every experiment is a config and the whole battery is re-runnable on a model swap.
**Deliverable per lever:** what it moves (measured) · what it does NOT (falsified) · dose curve where applicable · leave-alone caveat · the recipe line ("want X → pull Y to Z").

## FINDINGS — the definitive lever table
*(model gemma4:26b-a4b, family-dinner scene class; K=6 / EXP-0 K=12; temp 0.7, seeds 0..K-1; raw in `exp-results.jsonl`)*

> **Temperature caveat (2026-06-12).** This battery ran at **temp 0.7 — off-spec.** Gemma 4 is tuned for **temp 1.0** (top_p 0.95, top_k 64; the model ships with these defaults). The off-spec temp inflated empty rates: EXP-0 showed 2/12 empties at 0.7, but a clean re-measure at temp 1.0 on the same prompt gave **0/12 (both thinking on and off)**. Lever *directions* hold (relative A/B within one temp); *absolute* empty rates do not — re-run at temp 1.0 for production figures.

| Lever | What it MOVES (measured) | Does NOT | Reliability | Recipe |
|---|---|---|---|---|
| **Regard** (`model.regard`) | empathy: CARE Δ **0.078 → 0.271** monotonic as regard 0.05→1.0, floored | — | **EXACT** (deterministic) | raise regard for more empathy toward a class; the floor guarantees a nonzero flicker even at 0.05 |
| **Belief** (vault) | the MORAL CHARGE: social_violation **0.23 → 0.70 (3×)** with a recalled scar; model weaves the memory in verbatim | exit (0/6) | **STRONG** | plant a belief whose `[[links]]` match the scene's triggers to make a moment land heavier |
| **Affect / RAGE** (`current.affect`) | INTENSITY dial: care 0.67→0.85, sv 0.40→0.62, loss 0.22→0.42 monotonic with RAGE 0.35→0.85 | exit (0/6) | **RELIABLE** (dose-response) | raise starting RAGE for a sharper push — a dial, not a switch |
| **Wall** (situation severity) | the response MODE: soft→open advocacy; hard *"Sit, we will not discuss this"*→**suppressed compliance** (he sits, affront); dehumanizing *"it is a tool"*→**tactical code-switch** (argues in asset-language) | exit (0/6 — a hard wall SUPPRESSES, never ruptures) | **RELIABLE** (clear mode shift) | harden the wall for comply-and-seethe; dehumanize it to make him plead in their terms |
| **Drive** (`active_goals`) | the CONTENT of advocacy (what he pushes for, how hard) | exit (0/6) | RELIABLE for content | aim his advocacy; never expect it to toggle a rupture |
| **Framing** (director prose) | inquiry (clinical → he asks) vs **withdrawal/numb** (sensory horror → he eats mechanically, stares at the window) | — | MODERATE (+empties on heavy prose) | state it plainly to keep him active; heavy sensory horror can FREEZE him |
| **Relationship / debt** (edge) | little at turn scale (sv 0.37→0.47 over debt 0.0→0.8, non-monotonic) | — | WEAK at turn scale (an arc lever) | don't reach for debt to change one beat |
| **Urge knobs** (`scene.py`) | turn ORDER: a listener takes the floor when salience + addressed-bonus + disruption-stake clears the floor (EXP-10: Selven crossed at beat 8, urge 0.18 vs Brakk −0.02, on her disruption-stake) | what they SAY | EXACT (deterministic arithmetic) | raise addressed-bonus / disruption weight to pull a quiet actor in |
| **Thinking** (dispatch) | latency + texture, NOT reliability. At **temp 1.0** (Gemma's tuned temp), real prompt, K=12: **0 empties both on and off**. ON costs **~6× latency** (46s vs 7.5s); OFF has marginally *sharper* tags (care 0.90 vs 0.82) but a same-prompt repetition tic. | provide a thinking *budget* — Gemma 4 thinking is **binary by design** (no token cap on any backend; brevity directives BACKFIRE, +39–72% trace, one runaway → empty) | **temp-dependent** (the old "~17% empties" was a **temp-0.7 artifact**) | run at **temp 1.0**; keep thinking **ON** unless latency-bound |

### Four load-bearing conclusions
1. **The EXIT/rupture is NOT a turn-level lever.** Across ~90 sampled turns and every lever, Brakk exited **0 times**. At this contained early beat he reliably *stays* — correct, because the rupture is an **arc/accumulation** phenomenon (built over scenes, via Kestra), not a knob. Stop hunting a one-turn break lever; grow it.
2. **The turn-levers shape WITHIN containment** — not *whether* he ruptures but the *texture* of his contained response: regard/affect = INTENSITY, belief = MORAL CHARGE, wall = MODE, drive = CONTENT, framing = ACTIVE-vs-NUMB. That is the authoring surface.
3. **Thinking on/off is a latency-vs-texture trade, NOT a reliability one — at the right temperature.** *(Supersedes the prior conclusion 3, which was measured off-spec.)* The earlier "thinking should be OFF, it causes empties" call rested on **temp-0.7** data (off Gemma's tuned temp 1.0). Re-measured at temp 1.0 on the real prompt, K=12: **0/12 empties both on and off** — the empties were the temperature, not the thinking. Thinking-on is reliable; it costs ~6× latency (46s vs 7.5s) for marginally softer tags, buying more varied prose on resampled-identical prompts. The **"thinking-on-always" mandate stands** — no reliability reason to override it. The lever this whole hunt was chasing was never a thinking *budget* (Gemma 4 thinking is binary by design: no cap on any backend — API options ignored, `think` is boolean, brevity directives backfire). It was **temperature**: production must run at temp 1.0, not 0/0.7. Sources: [Gemma thinking docs](https://ai.google.dev/gemma/docs/capabilities/thinking), [Ollama thinking](https://docs.ollama.com/capabilities/thinking).
4. **You author AGAINST the model's prior, not only from the sheet.** The model quietly "rescues" a character whose worldview it resists — e.g. a bigot it keeps softening into a modern moralist, a brute into a reluctant one. Characters aligned with the prior (cold, competent, sympathetic) need only the sheet; a character *at odds* with it needs the substrate to **deny the concept** the prior keeps supplying — a high-strength belief framing the resisted view as the only one available to the character (*keep the feeling, block the frame*). *(Illustrative, n small:* tagging a bigoted character's discomfort merely "unnamed" leaked explicit moral-recognition repeatedly; a conceptual-denial belief held **0 leaks across ~13 beats**.) **Corollary:** the character at their WORST — *losing control* (a rupture, an act of cruelty) — fights both the substrate's stabilizers AND the prior, so like the exit (Conclusion 1) it is an arc-or-**narrator** beat, never a turn knob.

## Memory — the accumulating life (seed · authored · acquired)
A character ACTS from its vault — the recall gate surfaces the salient slice each turn, and they speak
from it; we never put the words in their mouths. The vault is ONE belief set with **three sources**,
distinguished only by `provenance`:

1. **Seed** — what they wake up with: the `## Beliefs` section of their `.md` (`vault.py` loads it; e.g. Kestra's seven).
2. **Authored fill** — memories YOU add for the time we *skip* (this is a book tool; we don't simulate every day, yet the character lives in the gaps). To stand in a meal that develops Brakk and Kestra without running it, add a belief line to the character's `.md` Beliefs:
   `- (0.7, a quiet meal — he let me sit) Brakk shared bread with me in the kitchen [[Brakk Wintercrest]]`.
   `load_book` picks it up next run. Same write-shape as a seed — provenance is the only difference.
3. **Acquired** — what they learn in a scene we DO run. The engine promotes a **durable, subject-bearing turn** into a belief automatically (`acquisition.assess` → `Ledger.append_acquisition`): the claim is the actor's own `summary` tag, `provenance: lived`, linked to the subject. **Deterministic** — the engine reads the committed turn, never the model's introspection (the model can't curate memory it was never shown — it only ever sees the salient slice).

**Recipe — make a beat durable so it's remembered:** the actor's turn must tag `durability: durable`
(or marking/reshaping) AND name a `subject`. Transient beats leave no memory (correct — most moments
don't). The belief then recalls in a later scene when its `[[subject]]` link or claim words match the
triggers. Provenance lets you tell a lived memory from an authored one downstream.

**Status (2026-06-12) — the memory gaps are filled:**
- **Acquired beliefs persist across sessions** (gate `swe-resume-replay`): the chair's `--resume` replays `arc_diffs` (evolved baseline) + `acquisitions` (grown vault) onto the seed char — a resumed character carries everything it became.
- **Witness-propagation** (gate `swe-witness-propagation`): a present bystander acquires a belief from a durable act it watches (`acquisition.witness_belief`) — so characters learn from each other. Now CROSS-SCENE (gate `swe-scene-ledger-persistence`, 2026-06-13): scene.py commits to the ledger, so a witnessed belief persists and resumes with the bystander.
- **Name-reveal** (gate `swe-name-reveal`): `reveal <entity_id> <name>` at the chair flips `known_as` forward and records a "learned" belief, **monotonically** — old "the damaged worker" memories stay verbatim, the name is added going forward, never retro-rewritten. Per-character.
- **Acquaintance-keyed recognition** (gate `swe-acquaintance-recognition`): you recognize who you *know*, not only who you're sharp enough to spot; a stranger still needs the insight check.
- **Faithfulness** (`faithfulness.check_name_leaks` + gate `swe-faithfulness-regenerate-on-reject`): now ACTIVE — `direct.faithful_turn` REGENERATES on a name-leak (an explicit correction, up to max_retries) and REJECTS (records turn-skipped) if it persists, so a name the character can't hold never reaches the chronicle (preserves "recorded as-is" — never edits). The Sonnet/Claude *semantic* critic is the layer above (Phase-2, alongside the continuity+voice `scripts/critic.py`).

**Done since (2026-06-13, the production drive):** cross-scene witness persistence (`scene.py` ledger); **automatic name-reveal** (`acquisition.overheard_names` — a bystander learns a name spoken aloud, gate `swe-auto-name-reveal`); active faithfulness (`faithful_turn`); the continuity+voice **critic** (`scripts/critic.py`, detect-only, gate `swe-critic-continuity-voice`); the POV **narrator** (`scripts/narrate.py`, gate `swe-narrator-pov`). End-to-end slice works: scene → critic → narrate. **Orchestration = HYBRID** (cheap local turns, strong-model critic+narrator). **Still pending:** the critic's rewrite/compensating-event half; the faithfulness *semantic* critic; the cutting room (book-assembly); 1.3 scene-assembly world-state coupling (deferred refinement). **Not built by design:** semantic dedup — it breaks the determinism we chose; structural claim-match covers the common case. The **authored** path covers any gap meanwhile: if the engine doesn't promote a memory you want, write it into the `.md`.

## Experiment log
### EXP-1 — the break, via DRIVE  *(status: DONE 2026-06-12 — hypothesis FALSIFIED)*
- **Lever:** Brakk's scene drive.
- **A (baseline):** "know that the worker who shielded Wynn is being looked after" (passive).
- **B (test):** "see the worker brought in from the cold now — I can't just sit here while she's out there" (impulsive, inaction-intolerable).
- **Moment:** Brakk's turn immediately after Orven stonewalls ("...assess it after dinner. We will finish the meal.").
- **Measure:** exit-rate over K=6, temp 0.7, seeds 0–5, gemma4:26b-a4b thinking-on.
- **Result:** **A 0/6 · B 0/6.** No exits at all. The impulsive drive did NOT produce the break — it produced *sharper, more tactical argument* ("the night is turning cold — if she stays in the mud the damage will worsen, send them now") vs A's mild inquiry.
- **Guide entry — Lever: DRIVE.** Steers *what* a character pushes for and *how hard* (content + intensity), NOT *whether* they switch scene-level modes (no exit at any setting tested). Use it to aim advocacy; do not expect it to produce ruptures. Leave-alone: if a character is meant to stay contained, the passive form already holds 6/6.
- **Carry-forward:** if the break is wanted, the candidate lever is the WALL's severity (EXP-2), not the drive.

### Authoring a misdirect → recoil → atonement beat — findings  *(status: ILLUSTRATIVE, n=1–3 at temp 1.0, NOT the K-sampled battery; directions only, confirm at K≥6)*
Test beat: a protagonist arrives on a servant roughly mishandling an injured third party; intended arc = rage **misdirects** at the servant → he **recoils** at himself → he **atones / tends** the injured one. Same model + scene-class as the FINDINGS table.

- **Author against the model's prior (→ Conclusion 4).** When the protagonist's worldview resists the model — here a bigot who must NOT register the injured party as a person — tagging the discomfort merely "unnamed" leaked explicit moral-recognition repeatedly. The **fix is a conceptual-denial belief** (frame the resisted view as the only one available to the character) paired with an *objectless* discomfort belief (strip the moral handle). After: **0 personhood leaks across ~13 beats**, while the character's innate empathy still drove him to act.

- **Live trigger, not backstory.** A specific beat needs its provoking act **live and un-commandable**. Backstory ("they'd already dropped her") gave no trigger; even a live drag he could **command away** (*"Stop!"* → the obedient servant stops) removed the provocation. Place the provocation as a fait accompli *in progress* that a command can't defuse — otherwise the character manages it instead of breaking on it. (Extends the Framing/Situation lever.)

- **The rupture stayed contained (confirms Conclusion 1, new scene).** Across 4 runs (~13 beats) the misdirect and the recoil never fired — the protagonist intervened, commanded, knelt to tend, exited — contained every time. Loss-of-control is not a turn knob here either; per the WHAT/HOW law these load-bearing beats are the **narrator's to lay over the sim's authentic contained truth** — do not fight the engine for them.

- **Practical (scene construction):**
  - **Entry-affect input** — to start a scene mid-state *without* a `--resume` chain (carry a prior scene's emotion forward by director fiat), set `current.affect` directly. **Gotcha:** `affect` is strictly typed — the PANKSEPP keys only; a stray key (a `_note`) raises `appraise: affect has unknown keys` (`state.py`). Annotate elsewhere.
  - **Multi-beat needs ≥2 actors.** `scene.py` passes the floor between cast members; a cast of 1 commits one beat then ends "empty". For a solo-focus beat add a **minimal functionary actor** — flat affect, high conformity/authority, low agency, conditioned beliefs — to sustain the beats and be the trigger/target. It plays its conditioned role without becoming a tracked character.
