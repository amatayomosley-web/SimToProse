# Consolidation Loop — turning a turn into accurate events (THE KEYSTONE) (WORKING)

**Status: working. The keystone (William, 2026-06-08): "the most important aspect of the whole process — everything depends on the accuracy of what the processing agent records."** This is the loop that turns each simulated turn into the structured events that feed state, the next turn, and ultimately the novel. It's the binding engineering risk (`probe-plan.md` reprioritization) and the one error class that **compounds**.

## Why this is the keystone (the precise reason)
Every other error is **local**; a recording error **propagates**:
- mis-record → wrong appraisal → wrong state delta → wrong next-turn direction → the character drifts → every later turn builds on a corrupted floor;
- and the **biography is the novel's ground truth** (`README`), so the error lands in the book too. **"Faithfulness by construction" *is* recording accuracy** — hold it and the book can't contain what didn't happen; drift and the guarantee is theater.

So it earns maximal design effort **and a measurement regime**, not just a mechanism.

## Principle 1 — the ACTOR records, not an observer
The biggest accuracy win: the agent that **made** the decision emits the structured event **as part of its own turn** — it *knows* its intent (it just chose it); an external agent reading the prose afterward is **guessing**. (Empirical receipt that the divergence is real: Project Sid documents **thought-action incoherence** in concurrent LLM agents — the chat call answers "Sure thing!" while the function call executes something unrelated (arXiv:2411.00114, verified 3-0, `prior-art.md`). Emitting prose + event-tags in **one pass from one call** is the containment: they cannot desynchronize if they're the same output.) So collapse the "processing agent" from an *interpreter* to a *validator*:
- the **character-turn LLM** emits in one pass: the **prose action** (for biography/narration) **and** a structured **event-tag** (`{act, target, instrument, intent, stance}`);
- consolidation then **validates** those tags (cheap, mechanical) instead of **mining** them from prose (expensive, lossy). The doer labels the deed — so the record can't drift from the act; they're emitted together.

## Principle 2 — nobody records anyone else's mind
Split who records what, so no agent guesses another's interior:
- **each character records its OWN action** (self-report — high fidelity);
- **the engine resolves OUTCOMES** (did the blow land? the combat check; did trust drop? the appraisal) — deterministic, not interpreted;
- **cross-character effects flow through PERCEPTION** — B learns of A's act by *perceiving* it (`scene-assembly.md`) and records *B's own* reaction. A's intent is A's record; B's read of A is B's record.
This deletes the entire "observer guessing at others' intent" error class — the POV wall already enforces it.

## Principle 3 — a TYPED event schema (the contract)
Tags are drawn from a **bounded event vocabulary** tied to the appraisal/menu (harm · aid · betray · reveal · acquire-knowledge · bond · threaten · relationship-act …). The simulator **picks from the schema**, never invents. This makes events (a) machine-**validatable** (conforms?), (b) directly **appraisable** (each type → appraisal dims + menu-items), (c) the stable **contract** between LLM and engine (schema-is-primary). The event schema *is* the loop's interface.

## The pipeline (per turn)
```
character-turn LLM → { prose action , event-tags[] }            (actor self-reports, one pass)
   ▼
mechanical validation
   · schema-conformance   (tags ∈ event vocabulary)
   · containment          (every referent ∈ the scene's PerceptSet — no hallucinated entity/act)
   · capability           (the actor could do it — in-skill, in-reach)
   ▼   fail → reject+regenerate, or flag low-confidence → critic
append to the world-state ledger                               (event-sourced, immutable)
   ▼
engine: appraise events → state deltas                         (state-engine / arc-engine)
   ▼
consistency critic (read-only backstop, design.md layer 6)
   does {events + new state} stay consistent with prose, prior state, world rules?
   ▼   contradiction → flag / correct via a COMPENSATING event (never silent, never mutate)
```

## Principle 4 — it must be MEASURED, not trusted
"Everything depends on accuracy" logically demands **we can verify accuracy** — treating it as the failure. The recorder's test suite (the mutation-testing analog for LLM-authored records):
- **Ground-truth replay** — author scenes with a *known* event-set; assert recorded == known. The recorder's unit test.
- **Round-trip / reconstruction** — rebuild a description from the recorded events; if it loses what the prose had, the recording is **lossy** → tighten the schema. (Information-preservation.)
- **Cross-extractor agreement** — N independent recorders on one turn; disagreement = ambiguity → flag low-confidence (ensemble, not a silent guess).
- **The coherence probe** (`probe-plan.md`) — over N turns, does state stay coupled to narrative? Accumulating divergence = recording errors compounding. The integration test.

**No record enters state on a low-confidence extraction** without critic escalation — ambiguity is flagged, never silently committed.

## Open questions
1. **The event vocabulary** — the minimal complete set of event-types. **Owned by the event catalog** (`record-contract.md`): one artifact carries the vocabulary + per-type appraisal map + durability class + world-appraisal targets; content is authored there (machinery vs content per `design.md`). The *list* is still open; its *home* no longer is.
2. **Confidence scoring — shape RESOLVED 2026-06-10, number pending.** Each event-tag carries a self-rated `confidence: 0–1` emitted in the same pass (the actor knows when its own act was ambiguous), composed with the mechanical-validation result (any soft-fail caps the composite). Escalation: composite `< θ_conf` → the critic (`measurement.md`). θ_conf is Class-B calibration; Principle 4's hard rule is now enforceable as written.
3. **Compensating-event correction — DESIGNED: `measurement.md` §the consistency critic.** Append-only `correction` event referencing the bad event-id; the fold applies the inverse delta; downstream consumers (narration, the cut) treat corrected events as superseded. Never silent, never mutate.

## Cross-links
- **Extends:** `recording-model.md` (capture thought+action → now with self-reported event-tags), `design.md` (consolidation step + critic + the one-way arrow).
- **Feeds:** `state-engine.md` / `arc-engine.md` (events → appraisal), `world-state-ledger.md` (immutable log).
- **Validated by:** `probe-plan.md` (the coherence probe measures accumulated accuracy).
