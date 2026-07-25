# Scene Assembly — how a character lives the scene (WORKING)

**Status: working.** The runtime seam that turns world-state into the literal context a character acts from. It closes `world-model.md` open-Q #4 (in-life fact→belief coupling) and specifies the per-turn assembly that `knowledge-model.md` (the vault) and `relevancy-gate.md` (the gate) implied but never laid out. The vault answers *what is knowable*; the gate answers *what is relevant*; **scene-assembly answers what the simulator actually sees this turn** — and how the present moment enters a character who can only ever act on their own context.

**Headline (revised 2026-06-08): scene-assembly is fully deterministic.** No LLM runs here. It computes a structured packet; the one generative call per turn is the *decision* that consumes it. See "No renderer here" below for why.

## The seam it fills
Three pieces are designed in isolation; scene-assembly is where they meet, every turn:

> `world-state-ledger.md` (ground-truth present) → **scene-assembly** → `decision-engine.md` (resolve to a choice)

drawing on `knowledge-model.md` (the vault) + `relevancy-gate.md` (the gate) for the recall half. The ledger holds an **omniscient** present; the decision engine needs an **operand set scoped to one mind**. Scene-assembly is the connective tissue that scopes the first into the second. Skip it and you either inject ground truth (omniscience — the default failure `knowledge-model.md` names) or inject nothing coherent.

## Core principle: two streams, one wall
To *live* a scene a character needs two different things, and conflating them is the trap:

1. **Perception** *(new here)* — what they **apprehend of the present moment**. The ledger's scene-slice is ground truth (third-person, omniscient). The character receives only their **share**: bounded by vantage (line of sight, earshot), attention, and sensory acuity — and reduced to **perceivable attributes**, with identity a *gated fact* ("the disguised assassin" → `[a hooded figure, cloaked, ~6ft, →door]`; the label "assassin" withheld behind a check). This scoping is **fully mechanical — no generation.**
2. **Recall** *(already designed — the gate)* — what the present **evokes** from the vault: the salient slice via trigger-matching + skills + hinges + energy (`relevancy-gate.md`).

**One wall.** Both streams pass the *same* epistemic boundary the vault already enforces (`knowledge-model.md`). Perception applies the wall to **now**; recall applies it to **memory**. Perception is not a new paradigm — it is the obsidian-vault wall pointed at the present instead of the past. Same structural guarantee: the simulator *cannot* see past the horizon, because the horizon ran before assembly.

## Perception is acquisition-in-progress (this is what closes open-Q #4)
The two streams are not parallel rails — they **meet**, and the meeting *is* the runtime fact→belief coupling `world-model.md` left open:

```
world event (ledger, ground truth)
   │  scope to vantage / senses / attention     ← perception wall (mechanical)
   ▼
apprehended scene (structured: perceivable attributes only)
   │  extract triggers → run the gate           ← relevancy-gate.md
   ▼
active recall (the vault beliefs the scene evokes)
   │  perception + recall → structured operand set
   ▼
decision-engine resolves → action               ← decision-engine.md (the LLM)
   │  apprehended scene logged as acquisition (provenance: witnessed, T)
   ▼
vault updated → next turn's recall reflects it   ← knowledge-model.md
```

Perception is the **live edge** of the vault; the vault is the **stored body**; each turn the edge becomes body via an acquisition event. "How does a world fact become a character belief mid-sim?" — **it is perceived, and perceiving is acquiring.** A *false* perception (a disguise that works, a misheard line) enters as a belief carrying witnessed-provenance that may be wrong — exactly the false-belief machinery the vault already stores (`knowledge-model.md` "vault stores BELIEFS, not facts"). No separate coupling mechanism is needed; **perception *is* the coupling.**

## The assembly pipeline (per acting character, per turn) — all deterministic
1. **Scene slice** — pull the present situation from the world-state ledger (location, present entities, recent events, in-flight consequences). Ground truth; **not yet injected**.
2. **Perception scope** — filter the slice to what *this* character apprehends: visibility + earshot + attention + skill checks on subtle cues / identity (`relevancy-gate.md` machinery). A failed check *removes* a detail (they didn't notice). Output: the **PerceptSet** — structured perceivable attributes, identity gated.
3. **Trigger extraction** — pull triggers (entities, symbols, names, claims, places, requests) from the **PerceptSet**, never from ground truth. *You cannot be triggered by what you didn't perceive.*
4. **Recall pass** — run the gate (trigger-match → vault → skill → goal-salience → authored hinges → energy budget). Output: **active recall**.
5. **Assemble the packet** — combine into a fixed **structured** object (below), minus everything past the horizon.
6. **Hand to the decision engine** — the packet *is* the operand set the engine resolves (`decision-engine.md`; weight-bearing layers 1·3·5·7 × state × situation × relationship). Assembly produces operands; the engine resolves them. **This is the only generative step.**
7. **Couple back** — the apprehended scene logs as an acquisition (`recording-model.md`); the vault gains the new belief(s); the chosen action emits an event to the ledger (consequence). Both halves of the loop close.

## The packet (what the simulator literally sees) — a structured object, not prose
A fixed structure, ordered for both **correctness** and **cost**:

**Stable prefix** (identity — changes rarely; cache across turns):
- Persona / disposition / values / drives / the Model — the Layer **1·3·5** operands + the **Layer-10 resolver** (`drives-schema.md`, `values-and-stakes.md`, `trait-theory.md`, `decision-engine.md`) + the `voice` profile (`voice.md`). Layer-7 state is volatile by definition and lives only below. *(Fixed 2026-06-10 — audit B8: the earlier "1·3·5·7" listed state in both halves.)*

**Volatile body** (recomputed this turn):
- Current **state** — emotion, energy, allostatic load (Layer-10 resolver inputs; `relevancy-gate.md` energy).
- Active **goals** (`drives-schema.md`).
- The **PerceptSet** (step 2) — structured perceivable attributes.
- **Active recall** (step 4) — structured beliefs.
- In-scene **relationship edges** to present entities (`relationships.md`: trust / affinity / respect / debt).

**Excluded by construction** — no bible wholesale, no other minds, no unacquired facts, no future, no director's beat (the beat-blind wall; `knowledge-model.md` + the Writer's-Desk prior art).

**The stable/volatile split is load-bearing, not cosmetic.** It is the cost answer to `knowledge-model.md`'s open question (per-character retrieval at cast × scene scale) and `relevancy-gate.md`'s token budget: the identity prefix is a cacheable stable-prefix; only the volatile body is recomputed per turn. Prompt structure lives **here** (the reasoning-contract layer), not in the domain model.

**The packet structure is also the FAITHFULNESS lever (William, 2026-06-08).** Whether a character *holds its position* or caves to the model's agreeableness is decided **here, by how the prompt is structured** — not by any inherent model trait. The `claude-suite` proves it (5 agents sustain genuine challenge purely from identity + challenge-directive structure), as does cairn's own per-turn anti-sycophancy injection. The division of labor: the **engine supplies the divergent content** (the Model's value-weights, the stance, the conviction — everything this design computes); the **packet structure binds it** (frame *acting in character / holding the position* as the task; inject conviction + stance as **non-negotiable** state). **Structure delivers; the engine substantiates — neither alone suffices** (perfect structure over a values-less character still converges; rich values under an agreeable frame still cave). Residual: structure *redirects* the agreeableness bias, it doesn't *delete* it — the leakage degree is model-specific, measured at the probe.

## No renderer here — scene-assembly is fully deterministic
**Revised (William, 2026-06-08): the LLM does not belong in scene-assembly at all.** An earlier draft put a "hybrid renderer" here — a light LLM that re-labelled percepts into the character's voice, fenced by a mechanical filter before and a validation pass after. It worked, but it left the LLM **tracking** refs, coverage, salience, and a never-add rule. *Any constraint the LLM must hold is a constraint it can violate.* The fix isn't a better-instructed LLM; it's to **delete the generative step from assembly** and let the deterministic layer do everything computable. This is the project's own invariant-ownership rule applied correctly: **the orchestrator owns what's perceivable; the LLM is never handed an invariant to hold.**

**Assembly outputs a structured PerceptSet — not prose:**
```
Percept    { ref, channel, fidelity, attributes:[…], recognized_as?, must_surface }
PerceptSet = [Percept, …]      # a whitelist; everything else is simply ABSENT
```
Identity is gated (`recognized_as` is filled only when a skill check passes or a vault recognition matches); a concealed blade enters `attributes` only if the Perception check passes — all via `relevancy-gate.md`'s `(trigger, skill, DC)` machinery, energy-modulated, run against the present scene instead of the vault. Because nothing is generated, the **never-add guarantee is vacuous** — the strongest kind: there is no generator that *could* add.

**The LLM lives at exactly two points in the whole sim — neither is here:**
1. **The decision** (`decision-engine.md`) — the character chooses and thinks, reasoning over the structured packet. One generative call per character-turn; this *is* where the character "lives" the scene. An LLM reads structured percepts at least as well as prose (less ambiguity).
2. **Narration** (`narration.md`) — biographies → prose, POV-bound, done **once** at output time with full context. This is where the character's *voice* and the scene's *texture* matter — for the reader, not the simulator.

**Where the old renderer's jobs went** — each to a place that's deterministic or already-LLM; none reintroduce tracking:

| Renderer job | Now done by | Deterministic? |
|---|---|---|
| Voice / diction / prose | **narration** (once, at output) | no — but it's the irreducible LLM step that already exists |
| Affective coloring ("closing in") | **the decision** (cognition reads `state`) | the LLM's existing job; belongs there per *perception ≠ cognition* |
| Salience order / attention / truncation | **the energy budget** (`relevancy-gate.md`) — low energy surfaces only high-salience percepts | **yes** |
| Conceptual framing (attributes → "a soldier") | **recall × decision** (vault recognition fills `recognized_as`; the decision reasons) | gate is deterministic; framing emerges at the decision |
| "Never add" enforcement | **gone** — no generative step to add anything | **vacuously true** |

**Net:** assembly is deterministic and cheap (**one** LLM call per turn — the decision — not two); the leak guarantee is structural by *absence of a generator*; and prose is **better**, because voice is rendered once at narration with full POV instead of reconstructed per-turn from fragments. (The two forks flagged earlier — tagged-fragments vs prose, whether tint is allowed — both *dissolve*; there's no renderer for them to be about. A simplification that deletes decisions rather than relocating them is the sign it's the right cut.)

**The one empirical hypothesis (probe-testable):** a decision-LLM reasons in-character over *structured* percepts as well as over prose. If it turns out to reason too literally or too modern, the fix is a thin naturalization **at the decision's input** — still no tracked render, no cross-percept constraints. Default is structured; the probe tests it.

### Worked trace — the hooded figure (skill × energy → different lived scene, no render)
| | Low Insight / drained | High Insight / sharp |
|---|---|---|
| **PerceptSet (mechanical)** | `{ref47, partial, [hooded, cloaked, →door]}`; Insight FAIL → `recognized_as` empty; Perception FAIL → blade absent | same + Insight PASS → `[+trained gait]`; Perception PASS → `[+blade at hip]` |
| **→ decision (LLM reads structure)** | mild unease; maybe ignore | fear; draw or flee |
| **→ narration (later, prose)** | "Some hooded figure slipped toward the door." | "A killer's gait, steel at the hip, making for the door." |

The *structured percept* differs by check outcome (deterministic); the *decision* reads it; the *voice* appears only at narration. That is the stateful-cognition payoff `relevancy-gate.md` promised — and it needs no in-the-moment LLM.

## Cross-links
- **Consumes:** `world-state-ledger.md` (scene slice), `knowledge-model.md` (vault), `relevancy-gate.md` (recall + perception checks + energy + salience).
- **Produces:** the structured operand packet for `decision-engine.md`; acquisitions for `recording-model.md`; events for the ledger (consequence).
- **Defers to:** `narration.md` for all voice/prose rendering (the only place a character's perception is ever put into words).

## Open questions
1. **Perception-check calibration** — what DC governs noticing a subtle cue / piercing a disguise, and what's the exact reuse of the gate's skill machinery? (Lean: reuse wholesale; a missed check is just absence, which the gate already treats as an outcome.)
2. **Structured-percept sufficiency** *(the empirical one)* — does the decision-LLM stay in-character reasoning over structured percepts, or does it need a thin naturalization at its input? Probe-testable; default structured.
3. **Multi-character interaction** — all of the above is single-actor-per-turn. Turn-taking, simultaneous perception, and shared scenes are the named under-designed area (`README` sim-mechanics) and the next seam after this one.
4. **Consequence granularity** — step 7 emits an event to the ledger; how much the world re-folds before the next character perceives is `world-model.md` open-Q #3 (dynamics) — adjacent, not solved here.
