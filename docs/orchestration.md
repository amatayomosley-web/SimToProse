# Orchestration — the showrunner (the process-brain that runs the whole book)

**Status: working (Mode B of the two-layer architecture — the engine computes every value; agents fill the act/judge/write roles).** The pipeline (`design.md`) names the specialists — world-builder, character-generator, director, character-simulator, recorder, continuity-critic, cutter, narrator — but not the hand that *runs* them. This doc designs that hand: the **showrunner**, the process-brain that drives a book from premise to manuscript by calling each specialist as a subagent, gating every seam, and keeping the canonical notes so it always knows where the story is and what's been done. It is `design.md`'s **orchestrator-owns-invariants** pattern made an agent (`.claude/agents/showrunner.md`).

## Two brains, never confused — director vs showrunner
- **Director = the story-brain.** *What should happen*: the beats, the arc, the ending, and the circumstance that moves a character toward them (`design.md` layer 5). Creative.
- **Showrunner = the process-brain.** *What happens next in the production*: which specialist to call, with what scoped input, whether a scene is canon, whether to advance or revise, and what to write in the notes. Procedural.

The showrunner *invokes* the director — the director is one specialist it coordinates, the one that owns creative steering. Keeping them separate is load-bearing: the director can be **faithfully refused** (a beat is wrong for this character; `probe-plan.md`); the showrunner is what *hears* the refusal, logs it, and routes the revision. If one agent both steered and judged its own steering, "faithful refusal → revise the beat" would collapse into self-justification.

## What the showrunner owns — the invariants
Everything that must stay consistent across the whole book — what no single-scene specialist can hold:
- **Canon** — the run DB (`runs/<book>.db`, the engine's append-only ledger — `src/engine/ledger.py`; structure per `world-state-ledger.md`): the world-truth. The ENGINE is canon's only writer (atomic `append_turn` / events); the showrunner is the only one who runs that commit path, and only through the gate. The markdown `canon-ledger.md` is a generated digest, never the source.
- **The notes** — the production record (below): where the story is, what's been done, what's promised.
- **The gates** — the checkpoints each seam must pass (below). It never advances past a failed one.
- **Progress** — the position in the plan (which beat / scene / chapter) and the route taken to get here.

Specialists **produce candidates** (a scene, an event, a cut, a page); the showrunner **admits them to canon** only when the gate passes (orchestrator owns invariants; sub-agents produce candidates — `design.md`).

## The production loop (premise → manuscript)
```
1. CONCEPT   premise · central question · theme · ending            → Setup gate
2. WORLD     world-builder → bible/probe-slice (to levered depth)   → Setup gate
3. CAST      character-generator ×N, each grounded in the world     → Setup gate
4. PLAN      director → beats · arc · ending  (destination firm; ~3-6 beats per brief, PLACE turning points — `scene-brief-blueprint.md`)
5. SIMULATE  per beat, the inner loop ↓                             → Beat · Canon · Coherence gates
6. CUT       cutter proposes; the cut is DECIDED IN DISCUSSION (`cutting-room.md`)    → Cut gate
7. RENDER    narrator ×scene → POV-bounded prose                    → Render gate
8. ASSEMBLE  collect scenes → the manuscript                        → Finish gate (acceptance-criteria)
```

**The inner loop (step 5), per scene:**
```
director places CIRCUMSTANCE  (beat kept from the simulator)
   ▼
character-simulator acts, turn by turn   (each scoped to its own packet; beat-blind)
   ▼
the engine consolidates deterministically (validate_tags → appraise → decay → commit, atomic per turn); the recorder agent reviews what it flags (ok=0 · escalate=1 · low-confidence)
   ▼
BEAT gate    did it land, in-character, no seam?  refusal → revise the beat, never the character
   ▼
CANON gate   continuity-critic passes → the committed events stand; the scene is marked canon (bad record → compensating event, never silent rewrite)
   ▼
COHERENCE    state stays sane; the character stays recognizably themselves across turns
   ▼
WRITE THE NOTES, then advance
```

## The gates — never advance past a failure
| Gate | When | Passes when | On failure |
|---|---|---|---|
| **Setup** | before sim | world + cast exist to levered depth, positions valid, no internal contradiction | back to world-builder / character-generator |
| **Beat** | after a scene targets a beat | beat landed, traceable to the character's own goal/values, no visible seam (`probe-plan.md`) | *faithful refusal* → revise the **beat** (director); *forced/seam* → re-place circumstance — **never force the character** |
| **Canon** | after a scene's turns commit (the engine appends atomically per turn) | continuity-critic finds no contradiction with ledger/bible; distinct voices; rule-consistent → the scene is marked canon in the story-map | flag; correct **forward** via a compensating event; never silent mutation |
| **Coherence** | across turns | state stays sane (no saturation/drift); same person across the arc (`probe-plan.md` coherence probe) | stop — do not build on a corrupted floor; investigate state/consolidation |
| **Cut** | after the cutter | every setup pays off; tension escalates to a climax; POV walls intact; reads as "a story" (`acceptance-criteria.md` #3) | re-cut; report any beat the footage never produced |
| **Render** | after the narrator | POV-bounded (no head-hop / omniscience leak; `narration.md`); reads as prose; voices distinct | re-render within the POV wall |
| **Finish** | the whole book | the `acceptance-criteria.md` tests all pass | the failing criterion names the component to fix |

## The notes — the meticulous record (per book, under `runs/<slug>/`)
The showrunner's memory — all of it **process-truth**. World-truth lives in the run DB (the engine's ledger) and the book's bible; the notes track the production.
- **`canon-ledger.md`** *(digest)* — a generated, human-readable view of the run DB's event log + folded now. Non-authoritative; refresh at scene boundaries; never hand-author facts here.
- **`production-journal.md`** *(process)* — chronological log of what was done and why: beats attempted, gate results, decisions, revisions. *What's been done.*
- **`story-map.md`** *(process)* — the plan with per-item status (planned → simulated → canon → cut → rendered) and the current position. *Where the story is.*
- **`threads.md`** *(process)* — open threads, promises, setups awaiting payoff; mysteries + reveal schedule. *What you owe the reader.*
- **`continuity-register.md`** *(process — working index)* — facts fixed as the bible grows from the sim (lazy-resolved details, once decided; `design.md` granularity rule). The authoritative home of a fixed fact is the bible / the DB event that fixed it; this register is the quick-check index.
- **`cast/`** *(process — mirrors the DB)* — the character sheets (`character-schema.md`): the showrunner materializes each from the character-generator's returned sheet; state fields mirror the run DB as the sim runs.

## The hooks — where notes are written and gates are checked
Two layers, one portable and one optional:
- **Process hooks (in the loop, portable).** The recording/checkpoint points the showrunner performs itself: *after each turn* → append to ledger + journal; *after each scene* → update story-map + threads + register; *at each seam* → run the gate, record its result; *on any revision* → log it. These are what keep the notes meticulous and current; they work in any harness.
- **Enforcement hooks (optional, Claude Code `settings.json`).** Real event-hooks that *enforce* the discipline rather than trust it — e.g. a `SubagentStop` hook that rejects a turn whose journal/ledger wasn't updated, or a gate hook that blocks advancing when a gate-result file reads `FAIL`. None ship by default — the repo carries no `.claude/settings.json`; wire them per-machine when you want the discipline enforced rather than trusted. The same mechanism can back every gate above. Portable-first, enforceable-when-wanted.

## Adaptive replanning — destination fixed, route discovered
Hold the major beats and the ending firm; let the simulation discover the route between them (`design.md`). Revise a **beat** only when the sim *honestly refuses* it (the beat was wrong for these characters), never to paper over a forcing. Every revision is logged in the journal with its cause, so the route's history is legible and the ending stays the target.

## Resumability — the run DB + the notes are the save file
World-truth resumes from the engine: `Ledger.resume(run_id)` replays the log over the snapshot and asserts determinism (`guide-operating.md` — a divergence aborts loudly; never bypass it). Process-truth resumes from the notes: `production-journal.md` + `story-map.md` reconstruct where the production is and why. Together they are the complete save file; neither alone is. The showrunner never holds state only in its head; a scene is not crossed with the record stale. A fresh showrunner (or a human) can read both and pick up mid-book.

## The wiring — Mode B on the real engine
Mode A (a human at the chair) and Mode B (this doc) drive the SAME engine; the commands are identical (`guide-operating.md` has the full recipes). The showrunner runs them via shell between agent calls:

| Loop stage | Command | Agent role filled |
|---|---|---|
| Lint the book | `python scripts/lint_book.py --vault "<book>"` | — |
| Turn burst (act) | `python scripts/direct.py --vault "<book>" --char <id>` / `python scripts/scene.py --vault "<book>" --scene <cfg>` | engine-internal LLM (local model) acts today — see seam 1 |
| Review (judge) | `python scripts/critic.py --vault "<book>" --run <id> --prompt-only` | **continuity-critic** consumes the emitted prompt |
| Narrate (write) | `python scripts/narrate.py --vault "<book>" --run <id> --pov <char> --prompt-only` | **narrator** consumes the emitted prompt |
| Dailies (views) | `python scripts/cut.py --vault "<book>" --run <id>` | **cutter** consults the views; the cut is decided in discussion (`cutting-room.md`) |
| Inspect between bursts | the SQL recipes in `guide-operating.md` | showrunner reads verdicts / escalations |

Seams NOT yet wired (flagged, gated follow-ups — never silently built):
1. **The act seam** — `direct.py`/`scene.py` fuse the character LLM call and the atomic commit; no `--prompt-only`/re-entry pair exists, so the **character-simulator** agent cannot yet act a turn (the engine's local model does). Bridge when wanted: a `--turn-json` re-entry running validate → appraise → commit on a supplied turn.
2. **The critic's thin prompt** — `critic.py` sends bible facts + prose only; the continuity-critic's contract also expects events / state deltas / ledger slice / voices. Bridge: extend its query + prompt builder.
3. **The escalation queue** — `escalate=1` / `ok=0` turns are recorded but nothing routes them to the **recorder** agent; today a human reads them via the inspect recipes.

## Cross-links
- **Runs:** `design.md` (the pipeline + orchestrator-owns-invariants), `world-state-ledger.md` (canon structure; the run DB is the instance), `probe-plan.md` (the beat + coherence gates), `acceptance-criteria.md` (the finish gate), `narration.md` (the render wall), README (directors-not-authors, one sim → many novels).
- **Embodied by:** `.claude/agents/showrunner.md`; craft in the `showrunning` toolbox skill.
- **Coordinates:** every agent in `.claude/agents/`.
