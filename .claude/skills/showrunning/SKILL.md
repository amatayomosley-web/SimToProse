---
name: showrunning
description: The showrunner's craft toolbox — how to run a whole book as a production. Covers the end-to-end loop (concept → world → cast → plan → simulate-to-beat → cut → render → assemble) and its inner scene loop; gate design (setup/beat/canon/coherence/cut/render/finish — pass conditions and fail actions, and how a gate maps to a real enforcement hook); the notes/state system (the canon ledger, production journal, story-map, thread & promise tracker, continuity register — notes as the save file); thread & promise tracking (open threads, foreshadow→payoff, mystery reveal schedules, what you owe the reader); adaptive replanning (destination fixed / route discovered, revising a beat only on a faithful refusal); and orchestration patterns (orchestrator-owns-invariants, scoped subagent handoff, the beat-blind and POV walls, admitting only gated candidates, resumability). Open it when planning the loop, designing or applying a gate, laying out the notes, tracking a promise, replanning around a refusal, or scoping a subagent handoff. Framework-neutral — a well of peers, not one prescribed truth.
---

# Showrunning — the process-brain's craft well

This is the toolbox the **`showrunner`** agent draws on. The showrunner runs the whole book — calling each specialist, gating each seam, keeping the canonical notes (`docs/orchestration.md`). This skill holds the *craft* of running that production: the loop, the gates, the notes, the tracking, the replanning, the handoff discipline.

**It holds craft, never canon.** *How* to run the loop, shape a gate, or lay out the notes lives here. *What* the story is — the world, the cast, the events — lives in the run's notes and the ledger, never in this toolbox.

## The index — reference files (deep files authored next)
- **`references/the-production-loop.md`** — the end-to-end loop and the inner simulate-to-beat loop; phase ordering; when each specialist is called and with what scoped input.
- **`references/gates-and-checkpoints.md`** — gate design: pass conditions and fail actions; quality gates; the acceptance criteria as the finish gate; how a gate maps to a real `settings.json` enforcement hook.
- **`references/the-notes-system.md`** — the notes schemas (canon ledger, production journal, story-map, threads, continuity register); notes-as-save-file; event sourcing; resumability.
- **`references/thread-and-promise-tracking.md`** — tracking open threads, promises, foreshadow→payoff, and mystery reveal schedules; the register of what you owe the reader.
- **`references/adaptive-replanning.md`** — destination-fixed / route-discovered; replanning on a faithful refusal; holding the arc firm while the route changes.
- **`references/orchestration-patterns.md`** — orchestrator-owns-invariants; scoped subagent handoff; the walls (beat-blind, POV-bound); admitting only gated candidates; resumability.

None of the six files above exist on disk yet — each bullet is its own summary. If you route to one and it's missing, act on that one-line summary and proceed; never stall on, or invent, the file.

## The method — run the production
1. **Own the invariants.** Canon, continuity, progress, and the notes are yours; specialists only propose.
2. **Gate every seam.** Nothing advances that hasn't passed its gate; a failure routes a revision, never a shove.
3. **Keep the notes meticulous and current.** Write them at every hook; they are the save file — state never lives only in your head.
4. **Hold the destination, discover the route.** Beats and ending are firm; the path emerges; revise a beat only on an honest refusal.
5. **Scope every handoff.** Give each specialist what its walls allow and nothing more (beat-blind simulator; POV-bound narrator).
6. **Correct forward.** Canon is append-only; a bad record is fixed by a compensating event, never a silent rewrite.

## Framework-neutral & portable
The patterns here are peers, not a rulebook; a production can run leaner or richer. Plain markdown, liftable to any harness — the loop, gates, and notes discipline work against any multi-agent narrative production, not only this repo's.

## Status
Router + method complete; the `references/` deep files are authored in the next pass, to the `docs/agent-toolboxes.md` standard.
