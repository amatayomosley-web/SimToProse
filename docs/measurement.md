# Measurement — detectors, the critic, and judge protocols (WORKING)

**Status: working.** The audit's most consequential gap (C1): the de-risk sequence was gated on a measurement regime that didn't exist — the coherence probe's pass conditions had no detectors, the consistency critic was named-never-designed, and the probes' judgment calls had no protocols. This doc designs the measurement layer. **Principle, inherited:** observable outcomes define success; a pass condition that can't be computed or blind-judged is decoration. The same compute/judge split as everywhere — **detectors are deterministic; judges are LLM/human under blinding and rubric; nothing self-grades.**

## 1. State-sanity detectors (mechanical — "tracked state stays sane")
Run continuously over the state DB + ledger; each is a pure function of the record. Thresholds Class-B calibration; the *detectors* are fixed:
- **Bounds** — every field within declared range; any clamp event logged. Violation = a write-path bug, full stop.
- **Saturation** — fraction of a character's CURRENT fields pinned at clamp over a rolling window. Sustained pinning means appraisal inputs or decay rates are mis-scaled (the "much-traumatized character saturates" risk, `arc-engine.md` open-Q 3).
- **Drift** — per-field z-score of CURRENT's rolling mean against BASELINE `{mean, variability}`. CURRENT *should* orbit baseline (decay guarantees it); a sustained walk with no durable-write events to explain it = leak in the loop.
- **Oscillation** — sign-flip rate per field per window; catches feedback loops (appraisal ↔ decay fighting).
- **Conservation (world-side)** — faction Resources/holdings balance across events (`world-dynamics.md` principle 7); fold-forward replay determinism: same log + Δt ⇒ identical snapshot, asserted on every resume.

## 2. Coupling detectors + rubric ("recognizably the same person")
Coupling = behavior consistent with tracked state. Two tiers:
- **Mechanical pre-screen (cheap, every turn):** the decision-input manifest (`record-contract.md`) names what the character *read*; the emitted event-tags name what they *did*. Flag turns where the act's event-type opposes the dominant injected lever with no collision recorded (the decision-engine logs collisions — an unexplained against-the-grain act is either an out-of-character tail, which `trait-theory.md` licenses *with* a recorded tail-sample, or a coupling break). Flags go to the judge, not to verdicts — the tail is legitimate; silent incoherence is not.
- **Judged coupling check (sampled + on-flag):** a blind judge receives the packet's qualitative direction + the {thought, action} — *not* the beat, not prior verdicts — and scores 3 anchored questions: does the thought follow from the direction? does the act follow from the thought? is the voice this character's (vs. generic)? Anchored 0–2 each; per `probe-plan.md` discipline the judge never authored the scene.
- **Longitudinal identity check (the probe's core):** every K turns, a blind judge gets N sampled {direction, thought, action} triples from turn-windows A (early) and B (late), shuffled, and must (a) attribute them to the same vs. different characters, (b) rate value-consistency. Coupled = attribution beats chance and value-consistency holds absent durable-write events. This operationalizes "same person across the arc" — it is `acceptance-criteria.md` #2's blind-attribution test, run *during* the sim instead of after.

## 3. The consistency critic (pipeline layer 6 — now designed)
Read-only backstop, post-fold, per beat. **Hybrid per the split:**
- **Mechanical half (always):** contradiction against ledger + bible (asserted facts vs ground truth; the no-contradiction floor), schema/containment re-check, state-sanity detectors (§1) on the beat's writes.
- **LLM half (sampled + escalated):** consolidation's low-confidence escalations (`θ_conf`, `consolidation-loop.md`); coupling flags (§2); voice spot-checks. The critic **reads the live stream and the fold — never the narration** (`design.md` one-way arrows).
- **Correction protocol (resolves consolidation open-Q 3):** the critic never edits. It appends a **`correction` event** referencing the bad event-id; the fold applies the inverse delta; consumers treat the referenced event as superseded. Append-only repentance — the record keeps both the error and its correction, which is itself diagnostic data (correction *rate* is detector #6: a rising rate = the recorder degrading).

## 4. Judge protocols (the probes' human/LLM judgment calls, made rigorous)
Shared discipline for every judged call (`probe-plan.md` rigor, generalized): **role-separation** (judge ≠ author ≠ director), **blinding** (no beat, no hypothesis, no prior verdicts), **anchored rubrics** (each question 0–2 with written anchors, no unanchored scales), **n ≥ 2 judges + agreement reported** (disagreement is a finding about the rubric, not noise to average away), **negative controls in every battery**.
- **Director probe** (#2 "traceable to own goals" · #3 "no visible seam"): judges receive character sheet + scene + action — never the beat. Q-set: "name the goal/value this action serves, citing the sheet" (fails if they can't); "was this character pushed by the scene or by the author?" (seam question, forced-choice + confidence); control scenes mix no-lever and forced-by-fiat variants — judges must catch the planted fiat cases or the rubric is too dull to trust.
- **Cut probe — shape:** blind readers, the acceptance #3 question verbatim ("a story" vs "it meanders"), plus setup-payoff and escalation sub-questions; transcription baseline must score worse (the control that proves the room adds value).
- **Cut probe — distinctness:** judges receive shuffled chapters from two same-record cuts; must sort into two books + describe each book's sympathies. Pass = sorting beats chance and the described sympathies match the two briefs.
- **Voice distinctness** (`voice.md`, acceptance #2): blind attribution of unlabeled dialogue lines to character sheets; beats chance per principal pair.

## 5. The sequence-forcing audit (C4 — salami forcing, now owned)
Per-choice envelope checks can't see a *campaign*. This audit is a **view + room review**, not a gate (`cutting-room.md` principle): for each principal, plot the trajectory of director-placed circumstances (the ledger tags director writes) against the character's **option-set width** (count of viable goal-serving actions the decision packets actually contained — computable from the decision-input manifests). A monotone narrowing across consecutive director placements, ending at a beat, is the salami signature: surface it to the room with the chain laid out. The room judges intent — the detector only finds the shape. Reviewed at act boundaries and before any beat is declared "earned."

## 6. Measurement of the measurement (inherited from `consolidation-loop.md` P4)
Ground-truth replay (authored scenes with known event-sets; recorded == known), round-trip reconstruction (lossy schema detection), cross-extractor agreement (ambiguity flagging), now plus: **detector unit-tests** — synthetic state-trajectories with planted saturation/drift/oscillation that each detector must catch (the mutation-testing analog: a detector that can't catch its planted failure is decorative).

## Open questions
1. Thresholds (all Class-B): window sizes, z-bounds, θ_conf, flag rates, K/N for the longitudinal check.
2. Judge pool composition — which models judge (diversity beats redundancy), and where a human judge is mandatory (lean: the seam question and final shape verdicts).
3. Correction-event semantics for *cascaded* errors (a bad event already appraised into three characters) — inverse deltas compose, but order matters; design when first hit.

## Cross-links
- **Gates:** `probe-plan.md` (all three probes now have runnable pass conditions).
- **Resolves:** consolidation-loop open-Qs 2/3 (with `record-contract.md`); the audit's C1 and C4.
- **Reads:** `record-contract.md` artifacts (manifests, deltas, stance snapshots) — every detector is a query over the contract.
- **Serves:** `acceptance-criteria.md` #2 (attribution machinery), #3 (shape protocol), #1 (the critic's floor).
