# World-State Ledger — the live now (design the machinery; the line items are runtime)

> Step 4's **"state"** half, and the engine's runtime spine. The ledger and character sheets are **instances** — their line items (events, current values, a character's filled-in state) are populated *during book-building*, never authored at design time. What we design is the **machinery**: the ledger's *structure*, the *logic that populates it*, and *how the system uses it*. (design.md: append-only event log + folded snapshot — the event-sourced spine.)

## The three layers (what's design vs build)
- **Engine design** *(now, reusable)* — the ledger structure + read/write logic. Built once; used for every book.
- **Per-book creation** *(setup)* — instantiate the world + author/generate principals → the *starting* snapshot + initial sheets.
- **Sim runtime** *(book-building)* — each turn appends events, folds them into the snapshot, updates sheets. **The line items are these — runtime additions.**

The ledger is the most *runtime* of all: it fills *during* the sim. So this doc designs the **logic**, not the contents.

## Structure (the schema — what *can* be tracked)
Two parts (design.md):
- **Event log** — append-only: `{what · who · where · consequence · caused_at · effective_at}` per canonized event. **Two clocks** (audit B4): `caused_at` = the tick the event entered the log; `effective_at` = the tick it folds (equal by default; a future-dated consequence — `world-dynamics.md` channel 1 — sets `effective_at > caused_at`, and fold / fold-forward applies the event only when its `effective_at` arrives). Immutable, only-adds (the no-contradiction floor). Also the **biography substrate** — recorded character actions *are* these events.
- **Folded snapshot** — the current *now*, derived from the log: **agents** (location / life-status / possessions) · **holdings** (control of assets / territory / scarce-resource levels) · **information** (who-knows-what) · **relationships** (alliances / enmities / debts) · **tensions** (each live tension's temperature + faction status) · **clock** (now). Scoped to the levered (the world's Layer-7, not a census).

## Population logic — how line items get written (runtime)
The write path, per sim-turn:
1. **Action → event.** The sim produces a character's `{thought, action}`; once **canonized** (passes the continuity/critic gate), the action is appended to the **event log**.
2. **Event → fold.** The new event projects onto the **snapshot** deterministically: a move updates the agent's location; a seizure updates holdings; a reveal updates info-state (and the relevant vaults — knowledge model); a betrayal updates relationships; an uprising updates tension-state. *The fold is the only way the snapshot changes — it is a pure function of the log.*
3. **Director writes too — in-world, never fiat.** Placing circumstance may seed ledger state (the famine worsens, the army arrives), but always as an **event** routed through the world, never a decree (the direct-by-circumstance discipline).
4. **Clock advances.** Time moves; the as-of-T marker updates (gates knowledge-slicing).

**Only the levered is written** — followed agents, plot-turning assets/tensions, relevant info-flow. The depth rule at runtime: the sim doesn't log every peasant.

## Usage logic — how the system reads it
The read path:
1. **Circumstance (decision-time).** The relevant ledger *slice* — what's happening around this character, as-of-now — is injected into their context as the **world-half** of the decision input (alongside their vault). This is how the ledger *supplies circumstance*.
2. **Consequence (the loop).** Character reads current state → acts → the action writes back (population logic). action ← state ← action. **The ledger is what closes the loop** — action changes the world, which becomes the next circumstance. Without it the world is a stage, not a system.
3. **Knowledge (time + info).** The clock provides the as-of-T slice; the info-state drives what each vault *can* have learned (knowledge model). The ledger is the ground truth vaults partially, fallibly project.
4. **Continuity (the gate).** The critic gate validates each new action against the ledger (+ bible): no contradiction with established state — the **no-contradiction floor**, enforced at write time.

## The character-sheet parallel (same runtime-build pattern)
Character sheets are the identical shape: the **generative model** (engine design) generates a **sheet** (per-book creation), whose **state fields update at runtime** (Layer-7: location, mood, energy, beliefs shift as the sim runs). So **model = design · sheet = creation · sheet-state + ledger = runtime.** We design the generator + the update logic; the sim builds the instances. The ledger is to the *world* what Layer-7 state is to a *character*.

## Prior art to lift
design.md already frames this as an event-sourced spine (append-only log + folded snapshot + gated canon); `world-model.md` open-question #2 flags Writer's Desk / Scribe world-state as prior art to check. **Reuse it** — the event-log + fold machinery — rather than reinvent, same as the vault lifted Scribe's knowledge graph.

## Cross-links
- `world-model.md` — ledger = the world's Layer-7 (open-Q #2, now answered here).
- `design.md` — event log + folded snapshot; the runtime pipeline reads the ledger slice and writes the action back.
- `knowledge-model.md` — the info-state + as-of-T clock drive vault knowledge.
- `present-systems.md` — the ledger is step 4's "state" half (the systems are its "systems" half).
