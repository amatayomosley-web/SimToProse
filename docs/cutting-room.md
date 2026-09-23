# The Cutting Room — what we do with the data (WORKING)

**Status: working.** The project's **2nd risk**: turning the sim's record into a shaped work. **The shape is not a pipeline (the author, 2026-06-10): after the scene sim we have *data*, and the shaping happens in *discussion* — what was made, what choices the characters selected, what it means for the novel or whatever project the sim is feeding.** The cutting room is where director and editor sit over the dailies and decide the cut, turn by turn — the same way every other decision in this project gets made.

**A rejected draft, recorded:** an earlier same-day draft specified a 7-step cut *pipeline* (index → spine → select → shape → gate → render → audit) with automated throughline-finding, curve-fitted chapter breaks, and the director compressed to an input "brief." Rejected for the same class of reason `scene-assembly.md` deleted its hybrid renderer, mirrored: that seam handed the LLM an invariant to hold; this one handed machinery a *judgment* that belongs in the room. We have performed this craft zero times on real sim data — automating it first would calibrate gates against taste we haven't formed. If repeatable patterns emerge after cutting real books, automation is an efficiency play for book N, not architecture for book 1.

## The principle: the conversation owns the choices; the engine owns the views and the checks
The sim layer's invariant rule, applied one level up. Three parts, strictly divided:
1. **Views** (computed, deterministic) — queries over the record that make a discussion of hundreds of scenes possible. The engine *shows*; it never decides.
2. **The discussion** (director + editor, in conversation) — what the book is about, what's in, what's out, what order, whose POV, where it opens. Every shaping choice is made here and **recorded as a decision**.
3. **The record + the checks** (mechanical) — decisions append to the **EDL**; narration renders from it; audits verify the result. Faithfulness is never a vibe.

## Views — the dailies viewer
The sim wrote down not just what happened but **how much it mattered, numerically, as it happened**. The cutting room queries that record:
- **"What changed this person?"** — `arc-engine.md` baseline diffs: the trauma/growth hinges of a life, by construction.
- **"What were the biggest moments?"** — appraisal magnitudes (`state-engine.md`), relationship-edge deltas (persisted as `relationship-delta` events per `record-contract.md` — the update rule lives in `relationships.md`; the queryable log lives in the record), vault acquisitions — secrets learned, lies planted (`knowledge-model.md`).
- **"What led to this?"** — the **consequence graph**: events → the state they wrote → the later decisions that read that state. A DB join over recorded writes — the write-side key is the appraisal log; the read-side key is the per-turn **decision-input manifest** (`record-contract.md`; audit A2 found this half was never persisted). Causality is traceable, so candidate **throughlines** (connected causal chains through high-consequence moments) are computable *suggestions* for the discussion.
- **"Where did it boil over?"** — decision-engine collisions (the both-sides dilemmas), urge spikes and stance shifts in the debates (`multi-character.md`).
- **"How does this cut feel, shapewise?"** — the **tension profile** of a proposed EDL (recorded affect + stakes over its order). A *diagnostic we consult* — "act two is flat, look" — never a gate that decides.
- **"What's unwitnessed?"** — scenes no candidate POV attended (`narration.md` constraint), surfaced before we fall in love with them.

The atoms are free: the runtime already runs in scenes (`scene-assembly.md`), so the record arrives pre-segmented — cast, place, time-span per scene. The shot list exists the moment the sim stops.

**Guardrail the views inherit:** magnitude is consequence, not meaning. The quiet scene that carries the book may be numerically flat; the views surface candidates and patterns, and the discussion is where meaning gets recognized. That's *why* it's a discussion.

## The EDL — the record the discussion writes
Decisions made in the room land in an append-only **edit decision list** — the same discipline as everywhere else in the project (decisions recorded, revisable explicitly, never silently):

```
EDL entry kinds:
  SCENE   { scene_no, pov: character_id, trim: [event_id…] | FULL, placement: chrono | flashback(anchor: recall_event_id) }
          # trim names EVENT ids; the manuscript's unit is the TURN, and `edl.turns_for_trim`
          # resolves one to the other. They are different keys — the first renderer compared
          # them directly and a conforming trim silently emptied the scene.
  SUMMARY { span: [tick_a, tick_b], pov: character_id, basis: [event_id…] }     # compression, never invention
  BREAK   { level: chapter | act }
  NOTE    { rationale }                                                          # why we cut it this way — the room's memory

A cut is REVISED by appending a whole new GENERATION (schema v17); `edl.entries_for` renders the
highest one and the superseded decisions stay in the log, because the room's memory of what it
tried is worth keeping. Before that column the table's own append-only trigger said "revise by
appending" and there was nowhere to append to.
```
Every prose unit traces to an EDL entry; every entry traces to recorded events. *"Every line of the book traces to a recorded biographical moment"* (README) is auditable because the discussion's output is structured, even though the discussion itself is free.

## Rules of a valid cut (constraints we discuss *within*)
- **POV wall** — a scene renders only from a vault that covers it; the narrator is the POV's vault (`narration.md`). Head-hopping is caught by lookup.
- **Recall-anchored nonlinearity** — a real-time POV may show the past only where a recorded **recall event** says the character's mind went there. *(Audit blocker A1: nothing previously recorded recall — the gate computed it and discarded it. The `record-contract.md` now requires the gate's injected-recall set be logged per turn as lightweight `recall` events; this anchor consumes those.)* Retrospective/frame narrators order by tell-logic instead, bounded by their eventual vault. Either way nonlinearity stays in-record.
- **Summary is compression, never invention** — a SUMMARY's claims trace to its `basis` events at lower resolution. Same wall, lower magnification.
- **Omission is licensed; contradiction is not** — withholding the villain's thought-stream from the heroine's book is the form working as intended (dramatic irony *is* engineered omission). The hard rule: the cut may not render what ground truth contradicts. Misleading-by-omission is editorial ethics — the room's call, not an engine rule.
- **Setup/payoff is auditable** — the consequence graph flags climaxes whose causal ancestors aren't in the cut, and planted setups whose payoffs were dropped (graph reachability over the EDL). The audit *flags*; the room decides.

## Render + verify
Narration renders per EDL entry, POV-vault-bounded (`narration.md`), emitting **per-paragraph source event-IDs in the same pass** (actor-self-reports, `consolidation-loop.md` P1). Then mechanical audits: provenance (no sourceless claims — invention → re-render), POV-wall membership, continuity against ledger + bible (`acceptance-criteria.md` #1). The renderer's "never invent" is checked, not trusted. Rendered chapters come **back to the room** — reading the prose is itself discussion input; cuts get re-cut.

## A consequence upstream: POV-candidacy is decided at RUN time
`recording-model.md` captures thought at layered depth — full for designated characters, light for others — and recorded interiority **cannot be deepened post-hoc** (confabulating thoughts at render time is exactly what the recording model exists to prevent). So **"run once, novelize many" is bounded by capture depth**: anyone who might anchor a future cut needs principal-depth capture *during* the sim. The likely cut-space is declared (loosely) before the run as its **recording policy**. A bystander's book stays possible — thin-interiority by construction.

## Beyond the novel
The record is the asset; the novel is one consumer of it. The views, the EDL discipline, and the audits are consumer-agnostic — a different project cuts the same record to a different shape. Nothing in this room hard-wires "book" except the renderer it hands off to.

## The cut probe (3rd in the de-risk sequence)
Unchanged in substance by the reframe — it tests the *output*, not the process. Mirrors `probe-plan.md` discipline; needs no engine and no full sim (the coherence probe's N-turn run already yields a small real record, or hand-author mock biographies):
1. **Faithfulness** — provenance + POV-wall audits pass at 100% on rendered chapters. Mechanical.
2. **Shape** — blind reader: "a story," not "it meanders" (`acceptance-criteria.md` #3's own test).
3. **Distinctness** — two cutting-room sessions, different POV + premise, **same record** → judged as genuinely different books with different sympathies. The run-once-novelize-many claim, tested.
4. **Negative control** — a transcription baseline (chronological scene dump, no cutting) must score worse on shape than the discussed cut. Proves the room adds the value, the way the no-lever control proves the circumstance does.
Sequence stands: **coherence → director-via-circumstance → cut.**

## Open questions
1. **The view set** — which queries the room actually reaches for; build the catalog from real cutting sessions, not speculation.
2. **Intra-scene trim grain** — full scenes only, or beat-level trims? (Finer = better pacing, hairier provenance.)
3. **Multi-POV overlap** — when two captured POVs attended one scene: render once from one vault, or twice (Rashomon)? EDL supports both; default emerges from practice.
4. **EDL tooling** — how lightweight can the record-keeping be before it leaks? (A markdown decision log may beat a schema'd store for book 1.)

## Cross-links
- **Reads:** the record (`recording-model.md`, `world-state-ledger.md`) · scene log (`scene-assembly.md`) · consequence sources (`state-engine.md`, `arc-engine.md`, `relationships.md`, `decision-engine.md`, `knowledge-model.md`, `multi-character.md`).
- **Feeds:** `narration.md` (renders the EDL) · `acceptance-criteria.md` #1/#3 (its audits and its reader-test run here).
- **Constrains upstream:** `recording-model.md` depth policy (capture depth = the future cut-space).
- **Tested by:** the cut probe (above), third in the de-risk sequence (`probe-plan.md`).
