# World Dynamics — how the world pushes back (WORKING)

**Status: working.** Answers `world-model.md` **open-Q #3** (dynamics / consequence resolution) — the last runtime gap. The ledger (`world-state-ledger.md`) already gives the world memory: events append, the fold projects them into the snapshot, the slice supplies circumstance. What it doesn't give is **reaction** — the world *generating* pushback: the patrol that comes looking, the price that spikes, the rumor that spreads, the famine that deepens while no one is watching. A world that only records is a stage; this doc is what makes it a system.

## The principle
**The world has state, appraisal, and decay like a character — but no will of its own. Its will is the director; its books are the engine's.** Characters are autonomous (the sim acts them); the world is *directed* (the room acts it); the engine keeps both honest — it computes every consequence that follows from rules, tracks every disposition numerically, and bounds what the director may plausibly choose. This answers open-Q #3's framing question directly: *track-numerically / resolve-narratively, like the decision engine* — yes, with one substitution: **the world's "narrative resolver" seat is held by the director in conversation, not by an LLM.** Hard rules resolve the computable; the director resolves the willful; the LLM resolves nothing at this layer (it may *propose* options as a view — `cutting-room.md` principle: the conversation owns the choices; the engine owns the views and the checks).

Why no LLM in world-resolution: the world is the **constraint side** of the probe — it must be able to plausibly *deny* a lever (`world-model.md`). A generative resolver can always say yes; teeth require that denial be **computable**. And the director-steers-by-circumstance discipline already routes all willful world-moves through the room (`design.md`; `present-systems.md`: a faction's move *is* the circumstance placed before characters).

## Three channels of world-change
Everything that happens to the world arrives through exactly one of these, and **all three land as events** on the ledger (never fiat — `world-state-ledger.md` write-path):

### 1. Rule-resolved consequence (engine, deterministic)
The computable aftermath of any event — immediate and delayed:
- **Immediate resolution** — already designed: outcome checks (`design.md` engine: did the blow land), the fold's projection (a seizure updates holdings, a reveal updates info-state).
- **World-appraisal (new)** — the world-side mirror of `state-engine.md`: events carry typed consequences (`consolidation-loop.md` schema) that map **by rule** onto snapshot fields — a public killing raises the relevant *tension temperature*; a granary fire moves *scarce-resource levels*; an insult to the guild shifts its *disposition* toward the insulter (faction analog of a relationship edge, `present-systems.md` schema: Interest / Resources / Status / Relations / Cohesion). Same shape as character appraisal: `(typed event × standing interests) → state delta`, computed, never guessed.
- **Delayed consequence (new) — future-dated events.** Pushback that takes time travels *as an event with a future effective-tick*, appended at resolution time: "word reaches the guild ≈ 3 days" is written **now**, folds **then**. Event-sourced-native, replay-deterministic, and the world's memory of grudges costs nothing to keep.
- **Standing processes (new) — recurrence rules.** Ongoing conditions (famine, siege, plague, a closing pass) carry a *rate*: a rule attached to a snapshot entry declaring how it evolves per unit sim-time. Not ticked eagerly — applied by fold-forward (below).

### 2. Director-resolved choice within engine bounds (the world's "decisions")
When the world must *choose* — does the guild retaliate, does the crown investigate, does the village shelter the fugitive — that is a **willful** move, and will belongs to the director. Mechanics:
- The engine holds the institution's numbers (faction schema, `present-systems.md`) and **computes the plausible-response envelope** — a *view*: given disposition, Resources, Status, Cohesion, here is what this faction *can* do and how hard each option strains it. (A suppressed, fractured faction cannot field an army; the envelope says so.)
- The **director chooses within the envelope**, in the room; the choice lands as an event (often future-dated). Choosing *outside* the envelope is the forcing failure-mode, world-scale — the same "no lever works → revise the beat" honesty: if the world's books say the faction can't do it, the plot wants revising, not the books.
- This is `present-systems.md` made operational: factions are *collective characters* and *the director's primary circumstance-source* — Tier 2 is exactly where those two facts meet.

### 3. Placed circumstance (the director's creative lever)
Already canonical (`world-state-ledger.md` write-path #3, with the director role per `design.md`): the new pressure the world wouldn't derive on its own — the stranger arrives, the storm year, the decree. Enters as events like everything else; constrained by the bible and the no-contradiction floor. Dynamics adds only the bookkeeping: a placed circumstance acquires consequences via channel 1 the moment it lands (place the famine, and the recurrence rule + tension appraisal come with it).

## Fold-forward — time passes lazily
`world-model.md` already commits dynamics to lazy resolution ("resolved lazily, on-demand, where levered"). The mechanism: **`fold_forward(snapshot, Δt)`** — when scene-assembly reads the slice and the clock has jumped (next morning; three weeks later), the engine advances time-dependent state *at read time*: applies standing-process rates over Δt, folds any future-dated events whose effective-tick has arrived, decays what decays (tension temperatures cool absent fuel — the world-side analog of `state-engine.md` decay-toward-temperament).
- **Pure function** — `(log, Δt) → snapshot'`; same log + same Δt → same world. Replayable, testable, no hidden tick loop.
- **Depth-rule scoped** — only the levered evolves (the ledger never logged every peasant; fold-forward never simulates them). Unlevered spans cost nothing; the world is *correct when observed*, never computed when not.
- **Order:** fold future-dated events and rate-rules in tick order, so a famine that triggers a migration that triggers a border closure resolves as a chain, deterministically.

## Teeth, located (open-Q #5 gets its mechanism)
A world can now deny a lever in two computable ways: **a rule says impossible** (channel 1: the pass *is* snowed in; the law *does* hang horse-thieves) or **the envelope says implausible** (channel 2: the faction lacks the Resources/Status for the move the plot wants). The probe's "slice with teeth" = author exactly the hinges whose rules and envelopes the scenario will strain. Denial stops being the director's self-restraint and becomes the engine's verdict — which is what makes the probe's honest-failure case discoverable.

## Measurement (extends the coherence probe)
- **Fold-forward determinism** — replay test: identical log + Δt sequence → identical snapshots. (The world-side of `probe-plan.md`'s "tracked state stays sane.")
- **No silent mutation** — the snapshot changes only via fold / fold-forward of logged events and declared rates; any other write path is a bug by definition.
- **Envelope honesty** — sampled director choices re-checked against the envelope they were made under (the world-scale forcing audit).

## Open questions
1. **The world-appraisal map** — which event-types move which snapshot fields, per `consolidation-loop.md`'s vocabulary (its open-Q #1 and this resolve together; the menu and the map are one design move).
2. **Recurrence-rule grammar** — how standing processes declare rates (linear / threshold / staged), kept simple enough to author per-hinge.
3. **Second-hand spread** — direct witness is designed (perception); rumor *propagation* (B tells C tells D, with distortion) needs either a designed channel (transmission edges + per-hop fidelity loss) or stays director-mediated for book 1. Lean: director-mediated first; design the channel when a book actually levers on rumor mechanics (depth rule).
4. **Faction-disposition menu** — same appraisal dimensions as characters, or a faction-specific set (legitimacy, treasury, manpower, zeal)? `present-systems.md`'s schema suggests the latter; settle when the first faction is authored.

## Cross-links
- **Answers:** `world-model.md` open-Q #3 (this doc) and locates open-Q #5's teeth.
- **Extends:** `world-state-ledger.md` (fold → fold-forward; future-dated events; rate rules) · `state-engine.md` (appraisal + decay, world-side) · `present-systems.md` (the faction schema is Tier 2's operand).
- **Feeds:** `scene-assembly.md` (the slice it reads is now time-correct) · `probe-plan.md` (computable denial; coherence-probe extensions).
- **Bounded by:** `design.md` compute/generate split (LLM holds no world invariant and resolves no world choice) · `cutting-room.md` principle (conversation owns choices; engine owns views and checks).
