# The Record Contract — what the sim MUST write (WORKING)

**Status: working.** Born from the 2026-06-10 audit's strongest theme: *the record was thinner than its consumers assumed.* The cutting room, the probes, and the audits all read artifacts the recording layer never wrote (blocker A1: flashback anchors consumed recall events that didn't exist; A2: the consequence graph's read-side join key was never persisted; A3: relationship deltas had an update rule but no queryable log). This doc is the fix as a contract: **downstream read-requirements ARE upstream write-requirements.** If a consumer queries it, a producer logs it — enumerated here, owned here.

## The principle
The sim's record is not "whatever happened to get written" — it is a **deliverable with consumers**: the cutting room's views, the coherence probe's detectors, the faithfulness audits, the world's own fold. Every consumer query in the design must name its producing write here. A new view that needs a new artifact amends this contract *before* the run that wants it (capture cannot be retrofitted — `recording-model.md`'s post-hoc rule generalizes: **nothing is deepened after the fact**).

## Required writes (beyond the already-designed event log + thought/action streams)

| Artifact | Written by | When | Consumes it |
|---|---|---|---|
| **`recall` events** | the gate — its injected-recall set, logged as lightweight events `{actor, belief_refs, tick}` | every turn (it's already computed; logging is free) | flashback anchors (`cutting-room.md`), "where did their mind go" views, vault-usage diagnostics |
| **Decision-input manifest** | scene-assembly — the packet's contents as refs `{state_fields_read, beliefs_injected, percepts, edges}` | every turn (the packet is deterministic; its manifest is a byproduct) | the consequence graph's **read-side join** (state-write → the decision that consumed it), coupling detectors (`measurement.md`) |
| **`relationship-delta` events** | the engine — every appraisal that moves a relationship edge emits the delta as an event `{perceiver, target, axis, delta, cause_event}` | on write | "biggest moments" view, the social-plot throughline, betrayal/bond hinge detection |
| **`dialogue-act` events** | the actor's same-pass tags (multi-character family: assert · rebut · concede · question · support · escalate · deflect, + `target`) | per debate line | addressing (`addressed_bonus`), stance-arc views, debate-shape diagnostics |
| **Stance snapshots** | the engine — `{character, position, conviction}` per debate step | per scheduler step | stance-dynamics views, polarization/convergence measurement |
| **Thought-stream retention** | per the run's **recording policy** (`recording-model.md` depth layering) | per turn | narration interiority; POV-candidacy is decided here at run time — the policy IS the future cut-space |

## The event catalog — one artifact, four jobs (consolidates three open questions)
The typed event vocabulary was simultaneously open in `consolidation-loop.md` (open-Q 1), consumed by `world-dynamics.md` (the world-appraisal map, its open-Q 1), and needed by `arc-engine.md` (durability classes). These are **one table, owned here as machinery** (content authored per-book where the depth rule demands):

```
event_type:
  name                 # harm | aid | betray | reveal | acquire-knowledge | bond | threaten |
                       #   relationship-act | destroy-asset | seize | move | dialogue-act:* | …
  appraisal_map        # → which appraisal dimensions fire, against which menu items (state-engine)
  world_map            # → which snapshot fields move: tension temps, holdings, dispositions (world-dynamics)
                       # durability_class was REMOVED 2026-08-30. It had no reader, and wiring it
                       # would have made the engine assert permanence the actor never claimed
                       # (consolidation-loop.md Principle 1). Durability comes from the actor's
                       # self-report and is exactly transient | durable.
  visibility           # public (witnessable) | private-to-actor (thought-adjacent)
```
The audit's worked finding — "burning a granary has no event type" — is the catalog's test: the physical/asset family (`destroy-asset`, `seize`) sits beside the interpersonal verbs. **Completeness is empirical:** the catalog grows when consolidation's containment check meets an act it cannot tag (reject → extend → revalidate), the same way the bible grows from the sim.

## What is deliberately NOT logged
Depth rule, restated for the record: unlevered background characters' interiority (recording policy), unobserved world ticks (fold-forward computes, doesn't journal), derived values (recomputed on read — logging them would create a second source of truth). The contract is exhaustive about *kinds*, economical about *volume*.

## Cross-links
- **Repairs:** audit A1/A2/A3 (`audit-2026-06-10.md`).
- **Owns the catalog for:** `consolidation-loop.md` (vocabulary + validation), `world-dynamics.md` (world-appraisal map), `arc-engine.md` (durability class), `multi-character.md` (dialogue-act family).
- **Feeds:** `cutting-room.md` (every view), `measurement.md` (every detector), `narration.md` (interiority per policy).
- **Constrained by:** `recording-model.md` (depth layering; nothing deepened post-hoc).
