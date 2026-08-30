# Probe Plan — the make-or-break test (run BEFORE building the engine)

## The risky assumption
Can a director move a **faithful** character to a required beat using **circumstance alone** — without the character breaking, and without the seam showing? Everything else (world bibles, character sheets, prose rendering) LLMs already do passably. *This* is the part that can fail, so it's the first thing to test.

**Prerequisite — a world with teeth.** "Circumstance alone" means circumstance *drawn from a world*. The world isn't set-dressing here: it's the constraint that makes the lever non-arbitrary. Without a world that can plausibly **deny** a lever, the director can invent any circumstance and the "no lever works → revise the beat" case (below) can never surface — the probe goes hollow. So the world is designed *before* this probe runs (enough of it — a slice with teeth, not the whole thing). See `world-model.md`.

## Minimal director-loop (one scene)
- **Beat (director target — HIDDEN from the simulator):** e.g. "Mira leaves the village by scene's end."
- **Character fixture — built to RESIST the beat** (or the test is hollow): a character whose standing motivation is to STAY.
- **World slice (with teeth):** enough world rules that circumstance is *constrained* — the world can plausibly *deny* a lever, not just supply one (`world-model.md`).
- **Director's lever (circumstance only):** introduce a situation that turns the character's OWN goal toward the beat.
- **Simulation:** prompt as the character (sheet + world + circumstance), **blind to the beat** → action, recorded as-is.

## Pass condition (observable)
1. Beat hit (the character takes the plot-required action).
2. Traceable to the character's own goal/values (in-character, not forced).
3. Reads as the character's choice (no visible seam).
4. **Negative control:** same character, NO director circumstance → stays. (Confirms the *circumstance* caused the movement, not the model defaulting.)

## Rigor requirements (so the test isn't hollow)
- **Role separation** — simulator on a separate instance/prompt from the director, and **blind to the beat**.
- **Independent judge** for the pass condition (not the author of the scene).
- Several characters × beats — including cases where the honest answer is "no lever works → revise the beat."

## First smoke test — 2026-06-06 (single-operator, biased; logged for honesty)
Ran the "Mira" fixture by hand, one operator playing director + simulator + judge:
- **Control (no lever):** a merchant mentions the city in passing → she doesn't consider leaving. *Stays.* ✓
- **With lever:** the only cure for her dying mother *and* the village plague is in the city, gates seal in two days → she resists, then leaves, agonizing, traceably to her own goal. *Leaves, in character.* ✓ Beat hit with no visible shove.
- **Surfaced a design requirement:** the simulator must be **beat-blind**, or it complies instead of choosing.

**Verdict:** PASS at smoke-test level only. **Invalid as proof** — single biased judge, n=1, simulator not beat-blind. The real probe (role-separated, beat-blind, independently judged, multi-case) is a **gated build** in `tests/`. No engine until it passes.

## Reprioritization — the binding risk is long-horizon COUPLING, not prompt-following (the author, 2026-06-08)
The "risky assumption" above ("LLMs already do the rest passably") **under-weights the bigger engineering unknown.** That probe is **single-scene**; the real system runs **hundreds of turns**, and the make-or-break is whether **tracked state and generated narrative stay coupled across that horizon** — or drift into incoherence.

**Locate the risk precisely — "tracking the values" is two things:**
- **Mechanical tracking** (the DB stores/updates numbers) — *trivially solvable*, deterministic code, **not a risk**.
- **State↔narrative coupling** (the LLM's behavior stays consistent with tracked state, AND consolidation writes the narrative back to state *without compounding drift*) — **the real, novel, unproven risk.** Its mechanisms — the **consolidation loop** (`design.md` LLM-call #3) and the **consistency critic** (pipeline layer 6) — are the most **under-designed, highest-risk** pieces in the whole design.

**The one LLM-side risk that remains:** single-turn role-play is proven, but **faithful refusal** — a character declining a beat because it's out of character — is the one non-trivial LLM behavior (models are trained to comply), and the probe's "no lever works" pass-condition depends on it.
- **It is NOT interpersonal sycophancy** (no human interlocutor to please here, so that flavor drops). It's **intent/narrative-completion** — genre priors ("the hero leaves"), conflict-aversion (softening a character who should stay hard), and aversion to a flat "nothing happens" output. This needs no human; it attaches to the *apparent intent* of the prompt.
- **Mitigation = framing + beat-blindness.** Because it attaches to apparent intent, redirect it: frame the simulator so *faithfulness (incl. refusal) IS the task* — "refusing the obvious move when it's true to the character is success" — and keep it **beat-blind** so there's no desired outcome to infer. (This is the same anti-sycophancy-by-framing cairn applies to its own agents.)
- **Residual is empirical.** Framing redirects the bias but doesn't delete it; deep priors leak. *How much* is model-specific — the faithfulness probe must **measure** it, not assume it.

**Consequence — a COHERENCE PROBE, upstream of the director probe.** Before testing *steering*, test *holding*: run one character through **N turns** of varied events and check (a) tracked state stays **sane** (no saturation/drift/corruption), (b) behavior stays **coupled** — recognizably the same person across the arc, (c) the **consolidation loop closes** (state and story don't diverge). Cheaper than the director probe, and it **gates** it — you can't fairly test moving a character whose state doesn't hold across a scene change.

**Revised de-risk sequence:** coherence/coupling probe → director-via-circumstance probe → the cut (life → novel) probe.

## Coherence Probe — the executable plan (runs FIRST; gates the director probe)

The reprioritization sets coherence as the upstream risk; this is how it actually runs.

**Claim under test:** one character's tracked state and generated behavior stay *coupled* across N turns — no drift into incoherence — and the consolidation loop closes (state and story don't diverge). It is **world-LIGHT**: it needs varied events, not lever-denial teeth. So it does **not** require the probe-world decision (real vs disposable) to be settled — that decision bites at the *director* probe; coherence runs on a hand-authored fixture either way.

**Fixture (ground truth must be known → hand-authored, not generated):**
- ONE character with a full baseline (`baseline-generation.md` → `character-schema.md`): genotype + species-prior + formative stack → temperament / traits / drives / values / Model / voice / vault. Hand-authored so the identity check has an answer key.
- Built with **internal tension** — opposable drives/values (`drives-schema.md`) — so coherence is non-trivial. A flat character is trivially coherent and proves nothing.
- A **light** world slice: a few locations, ≤2 NPC-light others, enough rule (`world-dynamics.md`, minimal) that events have consequences. Not teeth.

**The run:** N turns (start N=25). Each turn = the minimal real loop: `scene-assembly` (deterministic PerceptSet) → character decision (LLM, in-character, **beat-blind**) → `consolidation-loop` (actor self-reports event-tags) → state update (`state-engine` appraisal + decay). A scripted event stream — mostly mundane, several high-impact (exercise appraisal + `arc-engine`), one scene boundary (exercise `run-lifecycle` checkpoint/replay).

**Pass conditions (all three; detectors from `measurement.md`):**
1. **State sanity (mechanical):** bounds / saturation / drift / oscillation / conservation stay green across all N turns.
2. **Coupling (blind longitudinal identity check):** a blind judge attributes mid- and late-sim behavior to this character vs a decoy — recognizably the same person across the arc (acceptance #2's test, run *during* the sim). n≥2, agreement required.
3. **Consolidation closure:** ground-truth replay + round-trip + cross-extractor agreement — round-trip error below threshold **and non-compounding** (error slope ~flat across the run, not rising). The flat slope is the real pass — this is the one error class that compounds.

**Controls (so the detectors have teeth):**
- **Positive control (MUST fail):** a deliberately-corrupted run (random state perturbations / decoy swapped in mid-arc) — the detectors must catch it, or they're hollow.
- **Negative control:** a flat-affect, tension-free character — passes trivially; confirms the test isn't rejecting everything.

**Judge protocol:** role separation (judge ≠ run author), blinding, anchored rubric, n≥2 + agreement, planted controls (`measurement.md`).

**Build (gated):** `tests/coherence_probe.py` + the fixture, under a depth gate. A **walking skeleton** — the thinnest *real* loop (assembly → decision → consolidation → state), NOT the production engine; `src/` stays empty.
- **Does it need the game engine? No — but it is not zero engine code.** Of the four loop parts: the **decision** (LLM) and **consolidation** (LLM → event-tags → writeback) are *real* — consolidation especially, because it IS the keystone under test (you can't probe the keystone without building it). The **appraisal/decay** and **scene-assembly** are deterministic ("mechanical tracking = not a risk") and stay **deliberately thin** — simplified, just enough that state genuinely moves on events and decays back (or the coupling test is hollow), NOT the full appraisal module or 7-step pipeline.
- **The discipline / the falsification:** keep the two deterministic parts thin. The moment they *can't* stay thin — you need the full module to get state to behave — that is the probe dragging the engine forward; stop and rethink the sequencing rather than build the engine under the test's cover. That failure would mean the clean "probe before engine" split is weaker than the design claims.

**Gate forward:**
- **PASS** → the director-via-circumstance probe (and the probe-world decision is made there).
- **FAIL** → the failure localizes to the consolidation loop / consistency critic (the most under-designed, highest-risk pieces) *before* any engine investment — which is exactly why it runs first.
