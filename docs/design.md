# Design — Simulated World Evolve

## Pipeline (layers)
1. **World Bible** — canon: laws, religion, economy, geography, factions, timeline. Structured + **indexed for retrieval** (it will exceed the context window at book scale, so groundedness is a retrieval problem, not an automatic property).
2. **Character sheets** — goal, values, flaw, voice, relationships, current state, and **per-character knowledge** (what THIS character knows vs. doesn't — the source of dramatic irony, and the menu of levers for steering them).
3. **World-State Ledger** — append-only event log + folded snapshot of current state (who's where, what changed, who knows what). Makes consequences real across the book; the world is consistent in its *history*, not just its *rules*.
4. **Simulation step** — given (retrieved world slice + character sheet + that character's knowledge + situation + recent state) → the character's action/dialogue, **recorded as-is, never edited**.
5. **Director** — owns the world, the prep, the **beats**, and the **ending**. Mid-scene control is **placing circumstance only**. Steers which events become canon by shaping *inputs*, not rewriting *outputs*.
6. **Continuity / Critic gate** — validates each canonized scene against bible + ledger (no rule violations, no contradictions, distinct voices). A non-author check.
7. **Narrator** — renders canon events into prose (POV, voice, interiority). Separate concern from "what happened."

## Generation pipeline (upstream — how the Bible + Sheets are MADE)
The runtime pipeline above *consumes* a World Bible (1) and Character Sheets (2). This is how those are generated — the accurate chain from universal law down to a main character. **It runs in TWO PHASES, not one linear pass:** the world is built once; each character is generated from it.

**Phase A — World (built ONCE; shared substrate).** `world-model.md` workflow:
premise → universal law → (broader community? — `world-model.md` step 1.5) → planet → history → **present systems & state**. Output (present systems + world-state ledger) is the substrate every character draws from. Probe-bounded (depth rule: hinges only).

**Phase B — Character (generated PER character; reads Phase A).** `character-model.md` creation:
- **Position** — where/who they're born: place, class, family, occupation-niche, era-moment. Phase A's present systems define the *space* of positions; a character occupies one (no guild-mage if history made no guilds). (anatomy Layer 9.)
- **Formative environment** — the local conditions that raise them, given position (streets, court, temple).
- **Baseline** — formative env → traits + relationship-priors + values-weighting + starting vault + drives/wounds. The world authors the baseline; nothing is an arbitrary slider. (`world-model.md` formative coupling.)
- **Individuation** — personal backstory (one level below world-history) + perturbation → this unique person.

**The seam is "present systems & state."** Phase A *produces* it; Phase B *queries* it — which is why this is two phases, not an impossible per-character re-derivation of the universe.

**Main character — authored BACKWARD, validated FORWARD** (principals are curated, not emergent — `character-model.md` §models):
1. *Backward:* start from the character the story needs → what position + formative history would produce them?
2. *Forward:* confirm the world plausibly *yields* that person via Phase B. If it can't, they're an arbitrary insert → add the justifying position/history to the world, or change the character. (Same discipline as the probe's "faithful refusal → revise the beat.")

**Depth rule throughout:** author only the hinges the probe/story levers on; stub the rest.

## Load-bearing constraints
- **The simulator must be BLIND to the director's beat.** If the character "knows" the intended outcome, it complies instead of choosing, and the autonomy premise collapses. The director sees the beat; the character sees only the circumstance.
- **Steering = circumstance, never the character's hand.** Move the world so the plot move becomes the character's own choice.
- **Autonomy is the integrity check on the plot.** A faithful refusal means the beat is wrong → revise the beat.
- **Destination fixed, route discovered.** Hold major beats + ending firm; let the simulation generate the path between; let the director revise the target if the sim produces something better (adaptive replanning).
- **Scene goals: author OUR wants, then build the drives — never the outcome into the drive.** (the author, 2026-06-11.) A scene is set up in two passes. FIRST establish *our* wants — the author's intent, from the blueprint: what the reader must *feel*, and the beats the scene must *reach*. THEN build each actor's DRIVE **backward** from those wants — but a drive is a genuine **standing want, blind to how the scene ends**, never the outcome wearing a costume. *"Ilsa wants to expose the family and leave"* is foreknowledge — the ending smuggled into the drive. *"Ilsa wants to know the worker who saved Pell is being cared for"* is a drive — a want that does not know there will be a fight. The cruelty, the break, the turn must **emerge** from decent drives colliding (often over a being only one actor sees as a person) — **verified by simulation**. If the wants don't appear, you re-tune the **drives**, never script the **lines**. This is "the simulator must be BLIND to the director's beat" (above) applied to scene setup: the *want* is the director's; the *drive* must not carry it into the actor. Validated live on BP1.3 (`multi-character.md` §v1) — decent drives produced the casual cruelty with no villain in the room.
- **Simulation produces life, not story.** The Director + selection + escalation are what turn a coherent chronicle into a shaped novel. Budget most effort there — it's the part the simulation can't give for free.
- **Design the machinery, not the instances.** Three layers: *engine design* (schemas, presets, rules, generators, the ledger structure + logic — reusable, authored once); *per-book creation* (instantiate the world + principals for this book); *sim runtime* (the ledger fills, sheets update during book-building). **Character sheets and the world-state ledger are runtime builds — their line items are populated as the book is simulated, never authored at design time.** Every preset and schema in `docs/` is machinery; none of it is content. (`world-state-ledger.md`.)
- **Value granularity follows the depth rule — resolve to what the book levers on.** No value (a weapon's threat, a wound's cost, a bribe's pull, a slight's sting) has a fixed universal resolution. Most instances sit at their **class default** (a thug's knife = "a knife"); an instance is refined to its **specific properties only at a hinge** — where a decision is *sensitive* to the difference (a duel where reach decides it → the "four-foot blade" the author wrote *because* it matters → reach computed from 4). Default for the long tail; instance-detail at the hinges, sourced from **the book's own authored description**, lazy-resolved when a scene reaches for it ("the bible grows from the sim"). This is the frame-problem discipline as the **universal granularity rule** — it recurs for every value-type, and it *is* the engine/per-book split: the engine ships class-defaults + functions; the book supplies the hinge-refinements.

## Intentional architecture reuse
The append-only ledger + folded snapshot + gated canon mirrors an event-sourced spine. The director-owns-invariants / sim-produces-candidates split is the orchestrator-owns-invariants pattern. (Same shapes as the Agent Collaboration Hub — not a coincidence; it's the same class of system.)

## Two drivers, one engine — Mode A / Mode B
The pipeline above runs under two drivers; neither one bends the split below.
- **Mode A — human drives.** A person runs the scripts directly (`docs/guide-operating.md`):
  `direct.py`, `scene.py`, `critic.py`, `narrate.py`, `cut.py`. The pipeline's specialists (above)
  are the human's own judgment calls, executed through the scripts.
- **Mode B — showrunner drives.** A `showrunner` subagent (`.claude/agents/showrunner.md`; wiring
  in `docs/orchestration.md`) runs the SAME scripts, calling one subagent per specialist (director,
  character-simulator, recorder, continuity-critic, cutter, narrator) at the engine's existing
  `--prompt-only` seams and LLM dispatch points. It is a driver, never a value-computer — the split
  below binds it exactly as it binds Mode A. There is no agents-only mode: the agent layer requires
  the engine.

**Canon, in both modes:** the run DB (the append-only ledger, `world-state-ledger.md`) is
world-truth canon. A book's `runs/<slug>/` markdown notes (production journal, story map, threads,
continuity register) are **process-truth** — the showrunner's memory of what it did, never a source
of what happened. A generated `canon-ledger.md` digest may summarize the DB for human reading; it
is non-authoritative and is never cited in place of the DB.

## The compute / generate split — the game engine vs the LLM
**Principle (the author, 2026-06-08): the LLM is invoked only where no script can perform the act — composing, acting, interpreting prose. Everything with a *value* — state, checks, emotions, perception, salience — is computed by a deterministic game engine over a DB, then appended to the prompt as *direction*. The LLM never calculates a stat or decides a check; it acts on engine-computed inputs.** This is the orchestrator-owns-invariants pattern (above) stated as a concrete division of labor — and it is the **game engine now built in `src/engine/`** (the division was designed pre-probe, the probe passed, the build followed — `probe-plan.md`).

### The game engine computes (deterministic, DB-backed — the source of truth)
- **State** (DB = canonical): vault/knowledge, emotion values, energy + allostatic load, goals, relationships (trust/affinity/respect/debt), position, traits.
- **Checks**: knowledge (binary, vault membership) + skill/perception/insight (graded vs DC), energy-modulated. Pass/fail is **computed**, never narrated into being.
- **Perception scoping**: line-of-sight, earshot, fidelity → the PerceptSet (`scene-assembly.md`).
- **Salience + energy budget**: which percepts/beliefs surface, and where truncation falls (`relevancy-gate.md`).
- **Appraisal** *(the load-bearing module)*: `(structured event + disposition/values) → emotion & relationship deltas`. This is how "the insult made her angry" becomes a number — **by rule, in the engine**, not by an LLM's guess (`generative-model.md` numeric-tracking; `relationships.md` prediction-error update).
- **Recall**: trigger-match + weighted pathfinding + connection-energy (`relevancy-gate.md`).
- **Ledger**: append-only event log + folded snapshot (`world-state-ledger.md`).

### The LLM is invoked only for the irreducibly generative / interpretive
| # | Call | Input (engine-computed + bible) | Why no script can do it |
|---|---|---|---|
| 1 | **Scene framing** | world-bible slice + present sheets + world-state | compose a *situation* from canon — creative, but **bounded**: frames within given facts, invents none |
| 2 | **Character turn** (×N, back-and-forth) | that character's engine-computed **direction** (scoped percepts + recall + qualitative state + goals + check outcomes) | *be* the person and choose / speak — the autonomy core; this is the sim |
| 3 | **Consolidation critic** (escalation only) | the actor's own `{thought, action, event-tags[]}` — emitted **in the same pass as the turn** (`consolidation-loop.md` P1) | the normal path is **mechanical validation** of the actor's self-reported tags (schema · containment · capability), no LLM at all; this call fires **only on low-confidence escalation**. The doer labels the deed; nothing mines prose. *(Rewritten 2026-06-10 — audit B2: this row previously described an interpret-the-prose extractor, contradicting the keystone design; consolidation-loop.md wins.)* |
| 4 | **Narration** (output stage) | the biographies (the cut) | biographies → POV-bound novel prose (`narration.md`) |

(Layer 6's continuity/critic gate is **hybrid**: contradiction-against-ledger is engine; distinct-voice / tone is LLM.)

### Three boundaries that keep the split honest
- **Consolidation extracts events, never deltas — and reads the LIVE STREAM, not the prose.** It runs over the recorded `{thought, action}` stream (ground truth), reporting "B caught A in the lie"; the **engine's appraisal** computes the trust drop and the anger spike. **Never the narrated prose** — narration is a terminal, *selected, dramatized, POV-bounded output*; feeding it back would let the dramatization rewrite the canonical biography ("forcing," at the state level). The arrows are **one-way**: `stream → events → state` (the loop, in-sim) and `biography → narration → prose` (terminal — the prose is *checked against* the biography by the critic, read-only, but never *writes* state). The seam: *stream → tags* is the actor's own same-pass self-report (validated mechanically; the LLM critic fires only on escalation); *events → numbers* is engine.
- **Append the *direction*, not the stats.** The engine computes `fear 8/10`; what enters the prompt is "gripped by fear, barely holding together" — a qualitative direction the engine translates from the number. The LLM never sees raw stats (backstage guardrail; `relevancy-gate.md` energy: "the prose never says 'spent 3 focus'"). Numbers live in the DB; directions live in the prompt.
- **Scene-framing composes, never invents.** Same wall as everywhere: the framing LLM gets the bible slice as input and stages within it; it cannot add a fact the world does not have.

### The loop (one beat)
```
engine  : compute each present character's input bundle (state · percepts · recall · checks)
          → translate numbers to qualitative DIRECTION
   ▼
LLM #1  scene-framing : compose the situation from bible + state         [once per scene]
   ▼
LLM #2  character turn: given direction → action / dialogue / thought    [×N, back-and-forth]
   ▼    (recorded as-is — never edited)
engine  consolidation : VALIDATE the actor's self-emitted event-tags (schema · containment · capability) — mechanical; LLM #3 = the critic, fires only on low-confidence escalation   (reads the live stream, NOT the narration)
   ▼
engine  : appraise events → emotion / relationship / knowledge deltas → write DB → re-fold ledger
   ▼
        (repeat next turn; the re-folded ledger feeds the next direction)
   ⋯
LLM #4  narration     : biographies → novel prose                        [output stage, later]
```
The engine is the spine; the LLM is the voice and the will. Every value is computed; every word is generated; the two never swap jobs.
