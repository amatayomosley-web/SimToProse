# Run Lifecycle — save, resume, recover, govern (WORKING)

**Status: working.** Audit gap C3: a stated horizon of hundreds of turns, a prior-art catalog documenting API instability as a verified failure mode (`prior-art.md`), and no design for what a *run* is, where its durable state lives, or how it survives interruption. The event-sourced spine makes all of this nearly free — this doc just claims it explicitly.

## The run model
A **run** = one simulated world instance producing one record, executed across many *sessions* (work periods). Runs outlive sessions by design; nothing about a run may live only in a session's memory.

**Durable run-state (the complete inventory — if it's not here, it must be derivable):**
1. The **event log** (`world-state-ledger.md`, two clocks) — the source of truth.
2. **Folded snapshot** + per-character CURRENT rows — derivable (pure fold), persisted as cache.
3. **Character sheets** (FIXED + BASELINE) + arc-engine durable diffs — in the DB.
4. **Scheduler state** — active scene id, turn cursor, urge/floor state, stance snapshots (`record-contract.md`).
5. **PRNG state** — seed + position, if any seeded randomness is in play (the softmax knob).
6. **The recording policy** + the **edit-room state** (EDL, NOTE rationale) — the cut's side.
7. **Run config** — model ids + versions, prompt-template versions, catalog version (the event vocabulary evolves; a run pins its version — replay against a different catalog is not replay).

## Checkpoint discipline
- **The atomic unit is the TURN-COMMIT:** `{actor's {thought,action,tags} · validation result · appended events · appraisal deltas · fold}` commit together or not at all. A turn that fails mid-write (API hang, crash) leaves no partial state — the log either has the turn or it doesn't. This is the idempotent-retry boundary: re-running an uncommitted turn is safe by construction.
- **Scene boundaries are the named checkpoints:** cheap consistency points (no mid-conversation state in flight); resume defaults here. Mid-scene resume is possible (the turn-commit makes every committed turn a valid point) but scene-boundary is the clean default.
- **Resume = load snapshot + replay the log tail** since the last fold — the event-sourced resume the ledger already implies. Fold-forward determinism (`measurement.md` §1) is asserted on every resume: same log ⇒ same world, or the resume aborts loudly (`no-fallbacks` discipline — a divergent resume is a bug to fix, not to paper over).
- **Crash recovery is just resume.** No separate mechanism. The recovery test (run → kill mid-scene → resume → assert identical state to an uninterrupted control) is a standing regression — chaos-lite, one planned kill per milestone.

## Failure handling at the call layer
- **API instability** (the documented Smallville failure): bounded retry with backoff *inside* a turn-attempt; a turn that exhausts retries **parks the run** at the last commit — visible, resumable, never half-written. No silent skips: a skipped character-turn is a recorded `turn-skipped` event if the room decides to move on (it changes the scene; the record must say so).
- **Model-version change mid-run** is a *run event*: log it. Behavioral drift across a version boundary is then attributable instead of mysterious (the coupling detectors bracket it).

## The budget governor
Cost was answered architecturally (layered fidelity, lazy fold-forward, stable-prefix caching) but never *governed*. Minimal mechanism, room-facing:
- **Per-run token ledger** — every LLM call logs `{tokens, purpose, scene}` into run-state; the spend is a queryable view like everything else.
- **Per-scene soft budget** — exceeding it doesn't halt (no gate — the room decides); it *surfaces*: "this debate is 4× median scene cost" is a director-visible fact, often a convergence-failure symptom before it's a cost problem (the budget is a *diagnostic* wearing a cost hat).
- **Run-level projection** — spend ÷ scenes-elapsed × scenes-planned, recomputed at scene boundaries. The room hears about a blowup at 20%, not at the invoice.

## Character death / exit (the lifecycle inside the run)
Already owned by existing machinery — stated here once: death is an event (catalog: it's a `harm` terminal); the scheduler drops the actor (urge computation only ranges over the living-and-present); witnesses acquire it by perception (grief is appraisal, arc-grade); the biography **closes** and becomes immediately cuttable (a dead principal's book is complete). `life-status` in the snapshot is the flag; nothing schedules a closed biography.

## Open questions
1. Storage tech (SQLite vs the Kùzu polystore the vault wants) — an engine-build decision, post-probe.
2. Multi-run isolation (same world template, N runs) — namespacing, trivially solvable, decide at build.
3. The park-notification path — how a parked run reaches the author (lean: the same surface as the budget projection; one run-status view).

## Cross-links
- **Claims explicitly what the spine implied:** `world-state-ledger.md` (event-sourced resume), `world-dynamics.md` (fold-forward determinism on resume).
- **Commit unit wraps:** `consolidation-loop.md` (validate) + `state-engine.md` (appraise) + the fold.
- **Detectors:** `measurement.md` §1 (replay assertion, conservation); chaos-lite recovery test.
- **Repairs:** audit C3.
