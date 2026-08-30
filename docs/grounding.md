# Grounding — how the orchestrator is kept speaking from facts

**Status: design.** The orchestrator is the author's single interface (`orchestration.md`): everything the author learns about the book arrives through it. That makes one property load-bearing above all others — **it must never assert a world-fact it cannot resolve to a record.**

This doc defines what a fact is, where facts live, and — the half that actually matters — **what forces the orchestrator to use them.** A query tool it *may* call is a rule with no teeth; capability is not discipline.

## The problem
An LLM asked about a world will answer from context plus training priors, and **it cannot tell you which**. Confabulation is not a failure state it enters; it is the default state it must be held out of. The author's remedy of "read everything and check" does not scale past a few scenes — a book is hundreds of turns. So grounding has to be **mechanical**: enforced by construction, and auditable without reading.

## What a fact is — three axes
Every world-fact resolves on three axes, or it is not a fact:

- **what** — the assertion itself
- **as-of when** — the tick it was true at. *A fact true at turn 40, asserted at turn 90, is confidently wrong while sounding perfectly grounded.*
- **known by whom** — world-truth, or the belief of a named character. *The vault is full of false beliefs by design (`knowledge-model.md`); a character sincerely asserting something untrue is the system working, never a lore error.*

An assertion missing any axis is not citable and must be spoken as **derived** or **unknown** (below), never as fact.

## What already grounds us
`src/engine/schema.sql` supplies all three axes for everything that **happened**:

| Axis | Where it lives |
|---|---|
| what | `events` (type · actor · target · location · payload) · `turns` (every thought, action, tag, validation verdict) |
| as-of when | `snapshots.as_of_turn` · `events.caused_at` + `events.effective_at` (two clocks — future-dated consequences fold correctly) |
| known by whom | `acquisitions` (`{claim, confidence, provenance, believed_value}`) · `events.visibility` · `snapshots.kind='information'` |

Two tables are unusually strong for this job: `relationship_deltas.cause_event` is a foreign key, so *"why does she distrust him"* resolves to the event that moved it; and `decision_manifests` records `{state_fields_read, beliefs_injected, percepts, edges}` per turn — **exactly what the character was shown when it chose**, so *"why did she do that"* is answerable from rows rather than reconstruction.

## The gap
**There are no lore tables.** No entities, no laws, no locations, no pre-run history. The world bible lives as prose-plus-JSON in the author's vault, loaded at runtime by `vault.py`, never landing in the DB.

> The engine has a perfect memory and no rulebook.

Everything about what *happened* is citable to a row. Everything about what is *true* or *possible* is currently ungrounded. Closing this is the prerequisite for the gate role — a denial must cite the law it rests on, and today there is no law to cite.

**Two retrieval regimes, matched to their failure tolerance:**
- **Gating → structured, exhaustive.** *"Does any law forbid this?"* requires complete coverage of the law set; a miss is a **false pass**, the one failure this whole design exists to prevent. A filtered query over a `laws` table is exhaustive by construction. Top-k similarity is not.
- **Serving → prose retrieval is fine.** A recall miss in *"remind me about the northern cities"* yields a thinner briefing, not a wrongly-approved beat.

## The speech contract
The orchestrator is always in exactly one of three modes, and the mode is explicit:

- **cited** — resolves to a row. *"She lied about the timing (turn 14)."*
- **derived** — inference over cited rows, marked as inference. *"So telling him now reads as desperation."*
- **unknown** — no row exists. *"Nothing in canon says whether the mill has a night watch."*

`unknown` is load-bearing. **Most confabulation happens because there is no comfortable slot for ignorance.** Make it normal, cheap, and expected, and the pressure to invent drops away.

## What forces it — five layers, strongest first

**1. Starve the context.** The orchestrator holds no bible, no lore dump — only the query interface. It cannot recall what it never held, and its training priors contain nothing about this world's specifics: there is no *Pell* to misremember. Retrieval stops being a discipline it must maintain and becomes **the only path to any world-fact at all.**

**2. Structured channels for everything load-bearing.** Rulings, briefs, and state reports are emitted as typed fields — `{claim, citation, as_of, perspective}` — not prose. A claim without a citation is *malformed output* and never reaches the author. This converts a stylistic omission (invisible) into a structural one (impossible).

**3. Resolution outside the model.** Every citation is checked against the store **by code**, before display: does the row exist, and does it say what was claimed? Unresolvable → blocked and surfaced. This is the actual forcing function — **the check must live outside the thing being checked.** An LLM cannot police its own grounding; a deterministic resolver can. Same shape as the compute/generate split (`design.md`) that governs the rest of the system.

**4. Make the honest path the cheapest path.** `unknown` is a one-word valid answer. A fabricated claim requires inventing a citation that will be mechanically resolved and caught. Design the cost gradient so grounding is the lazy option, not the virtuous one.

**5. Detect degradation over time.** Two cheap mechanisms, both running without a human:
- **Planted controls** — periodically ask something knowably absent from canon. If it answers, it is inventing. (`measurement.md` already uses planted controls in its judge protocols.)
- **The inverted unknown-rate** — if the orchestrator *never* says "not in canon," it is confabulating. **A backstop that always finds an answer is broken.** Zero unknowns is an alarm, not a success.

## The honest limit
Layers 2–3 enforce grounding on **structured output**. They cannot fully police free-form conversational prose — detecting "this sentence is an unmarked factual claim" is not a mechanical operation.

The design consequence: **push everything load-bearing into structured channels**, and treat chat as commentary that may only reference facts already cited in the structured part. Anything that decides, gates, or reports state is typed. Prose is where it explains — not where it establishes.

## Why this also answers "is it drifting?"
Because citations are row ids, verification is **mechanical, not editorial**:
1. A spot-check is one lookup, not a search through transcripts.
2. A citation-resolution sweep runs in code across a whole run — no LLM needed to audit the LLM.
3. The unknown-rate and planted-control results are metrics, watchable at a glance.

The author keeps full access to every generated artifact (that is the standing requirement — the book is never a black box). These layers exist so that **access is not the only defense**, because no one reads four hundred turns.

## Cross-links
- **Bounded by:** `design.md` (compute/generate split — the LLM holds no invariant) · `world-dynamics.md` (denial must be *computable*; a generative resolver can always say yes)
- **Grounds:** `orchestration.md` (the orchestrator's serve + gate roles) · `.claude/agents/showrunner.md`
- **Depends on:** the lore store (unbuilt — the gap above) · `world-state-ledger.md` (the run DB is the state half) · `knowledge-model.md` (the *known by whom* axis)
- **Open:** the lore schema itself — what tables, what a law row contains, and how it is authored alongside the prose so the world is not maintained twice.
