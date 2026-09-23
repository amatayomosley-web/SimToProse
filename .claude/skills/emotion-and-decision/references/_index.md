# References — the deep files (outline / manifest)

The `emotion-and-decision` toolbox's deep material. **`SKILL.md` is the router** (the index + when-to-load pointers); these files are the *well* — one per framework-cluster, each read in isolation when the router points to it. **Status: outlined, not yet authored** — this file is the manifest for the later authoring pass. Until then the `SKILL.md` index plus the `docs/` canon each file digests is the working map.

## The format every reference file will follow
Per `docs/agent-toolboxes.md`, each `references/<topic>.md` is an **operational digest** — the "how, right now," not a re-derivation of the design — on this shape:

```
# <Topic> — <the one question this file answers>
**When to load:** <the trigger in the simulator's turn that pulls this file>
**Canon:** docs/<source>.md <the design doc(s) this digests; the source of truth>

## The menu (framework-neutral)   — several frameworks as peers; each: what it's good for, where it breaks
## Repo default → <named>          — this project's default, flagged a REFERENCE POINT, swappable
## In practice                     — 1–3 vivid, concrete examples (the load-bearing part), on real fixtures
## Limits                          — honest edges: what it can't decide, where it double-counts, when to escalate
```

Rules: **canon lives in `docs/`, once** (digest, don't fork the source of truth — if a reference and its doc disagree, the doc wins); **plural by default** (menu before any default); **examples over definitions**; **cite real sources, invent nothing** (a fabricated dimension, law, or attribution poisons every agent that draws on it — appraisal dimensions, emotion bases, and their authors must be accurate).

---

## A. The felt layer — how a moment becomes an emotion

### `appraisal-theories.md` — event → emotion: the evaluations that make a feeling specific
- **When to load:** computing "what it evokes" for a perceived event — which primary moves and why; or explaining why two characters feel oppositely about the same happening.
- **Canon:** `docs/state-engine.md` (the appraisal module — the named-but-unspecified gap this digests; the compressed dimension set; event→primary map), `docs/values-and-stakes.md` (relevance = which weighted values the event touches), `docs/generative-model.md` (appraisal spikes a primary; the causal chain's middle tier).
- **Holds:** appraisal's core claim (Arnold; Lazarus) · OCC model (Ortony/Clore/Collins — 22 types over events/agents/objects) · Lazarus (primary/secondary appraisal, core relational themes) · Scherer's Component Process Model (sequential stimulus-evaluation checks: relevance → implication → coping → normative) · Roseman's dimension grid · Smith & Ellsworth's six dimensions · Frijda's laws of emotion + action readiness/tendency · Weiner's attributional theory (locus/stability/controllability → emotion).
- **Repo default (swappable):** the **compressed 5-dimension set** in `state-engine.md` — goal-congruence · agency · certainty · control · norm/value-violation — a deliberate compression of OCC + Scherer, calibratable. The full theories are the well it was drawn from; refine toward OCC's typed granularity only where the book levers on a precise emotion.

### `core-affect-and-dimensional.md` — the shape of feeling-space: the axes and bases
- **When to load:** rendering the *texture* of an emotional state, blending named emotions, or relating the stored Panksepp vector to a valence/arousal summary for narration or the TTS delivery vector.
- **Canon:** `docs/generative-model.md` (the Panksepp basis; valence/arousal as a *derived* summary view; named emotions as coordinates/blends), `docs/state-engine.md` (the primary vectors + the three tiers).
- **Holds:** Panksepp's primary-process emotions (the house basis) · Russell's circumplex / core affect (valence × arousal) · Barrett's theory of constructed emotion (the honest constructionist counter) · PAD (Mehrabian & Russell — the dominance axis) · PANAS / two-factor (Watson & Tellegen) · Thayer's energetic vs tense arousal (the energy tie) · Plutchik's wheel (opposing pairs, blends) · basic emotion theory (Ekman — kept as a peer and a caution).
- **Repo default (swappable):** the **Panksepp primaries** as the stored, action-dispositional basis (chosen over valence-arousal because fear and anger sit adjacent yet drive opposite actions); **valence/arousal (circumplex) as the derived summary**, kept for free. Barrett's constructionism is flagged as the live scientific tension, not dismissed.

## B. Reading other minds

### `theory-of-mind.md` — mentalizing: inferring intent, knowledge, and feeling from the outside
- **When to load:** the character must read another's intent or trustworthiness, be deceived or deceive, model what someone else knows (or doesn't), or misread a mind — the interpersonal core of a scene.
- **Canon:** `docs/self-and-perception.md` (the three views: ground-truth / self-image / others-see — the character reads others' surfaces, never their true interior), `docs/knowledge-model.md` (per-character vaults; second-order beliefs; the no-omniscience wall), `docs/relationships.md` (trust/affinity/respect/debt as the belief-edges mentalizing runs on; thin-slicing updates).
- **Holds:** theory of mind (Premack & Woodruff) · the false-belief task (Wimmer & Perner; Baron-Cohen/Leslie/Frith's Sally–Anne) · Dennett's intentional stance · theory-theory vs simulation theory · Dunbar's orders of intentionality (the ~5th-order ceiling) · mind perception (Gray/Gray/Wegner — Agency & Experience) · cognitive vs affective empathy · thin-slicing (Ambady & Rosenthal) · second-order belief / mind-mindedness · egocentric bias / curse of knowledge.
- **Repo default (swappable):** the character mentalizes **only from its own vault** — reading others' *observable surfaces* (Layer 8), trust-weighted and often wrong; the **three views** are the machinery, second-order beliefs are the deception layer. No character ever reads another's ground-truth interior; that omniscience breaks the sim.

## C. How the choice actually gets made

### `naturalistic-decision.md` — how a real person under pressure actually decides: recognize, don't optimize
- **When to load:** shaping the *grain* of the `{thought}` that leads to the act — how an expert, a novice, a terrified or time-pressed person actually arrives at a move (not how a utility function would).
- **Canon:** `docs/decision-engine.md` (track numerically, resolve narratively; bias-not-sum; the explicit-weighing thought; hard gates vs soft biases; the no-argmax hard line).
- **Holds:** bounded rationality + satisficing (Simon) · recognition-primed decision / NDM (Klein) · fast-and-frugal heuristics / take-the-best / recognition heuristic (Gigerenzer) · skill–rule–knowledge (Rasmussen) · situation awareness (Endsley) · OODA loop (Boyd) · image theory (Beach & Mitchell) · somatic-marker hypothesis (Damasio).
- **Repo default (swappable):** **bias-not-sum** — the LLM weighs the salient injected framing and the `{thought}` *is* the visible weighing; **never a code-side weighted sum.** Satisficing + recognition-primed decision are the naturalistic grain the thought should *show* (recognize → simulate the first workable move → act), not an exhaustive option comparison. Optional hybrid: numbers may pre-rank a shortlist, the LLM disposes.

### `heuristics-and-biases.md` — the systematic tilts that bend choice, as character not universal error
- **When to load:** a decision should lean, flinch, over-commit, or rationalize — when a *bias* is part of who this person is under this state.
- **Canon:** `docs/decision-engine.md` (biases enter as state/disposition-modulated tilts on the framing, resolved narratively), `docs/self-and-perception.md` (self-serving/attribution biases = the self-image running the decision), `docs/relationships.md` (prediction-error + negativity bias — the built-in asymmetry biases are modeled on).
- **Holds:** prospect theory + loss aversion (Kahneman & Tversky) · framing effect · anchoring & adjustment · availability · representativeness / base-rate neglect · confirmation bias / motivated reasoning · sunk-cost / escalation of commitment · hyperbolic discounting / present bias · endowment / status-quo / default bias · dual-process (System 1/2) · affect heuristic (Slovic) · attribution biases (FAE, actor–observer, self-serving, hostile-attribution) · appraisal-tendency (Lerner & Keltner — fear vs anger and risk).
- **Repo default (swappable):** **bias is character, not a universal defect to simulate on everyone.** A bias is selected and scaled by this person's disposition and state — the fearful read threat up, the loyalty-weighted over-weight betrayal, the present-biased discount the cost tomorrow. It colors the `{thought}`; it is never a code-side utility correction. Loss aversion's ~2× asymmetry is the same negativity bias `relationships.md` already uses — reuse, don't re-derive.

## D. The body under load — state modulating cognition

### `stress-and-cognition.md` — how arousal, exhaustion, mood, and chronic stress bend thought
- **When to load:** the character's state is *extreme* — terrified, exhausted, enraged, grief-flattened, chronically worn — and it should change *how they think*, not only how they feel (tunnel vision, can't reason, mood-colored memory).
- **Canon:** `docs/state-engine.md` (current-state tier; appraisal spike + decay; allostatic load as a condition), `docs/relevancy-gate.md` (connection-energy as a depleting budget; attention/retrieval under load), `docs/decision-engine.md` (energy/allostatic buffs & debuffs in the catalog; the psych-zone).
- **Holds:** Yerkes–Dodson law (the inverted-U; optimum shifts by task difficulty) · Easterbrook's cue-utilization hypothesis (arousal narrows attention; weapon focus) · allostatic load (McEwen & Stellar) · fight–flight–freeze + the HPA axis · broaden-and-build (Fredrickson) · affect-as-information / feelings-as-information (Schwarz & Clore) · mood-congruent memory & judgment (Bower) · hot–cold empathy gap / visceral factors (Loewenstein) · cognitive load & working-memory limits · ego depletion (Baumeister — flagged replication-contested) · challenge-vs-threat appraisal (Lazarus).
- **Repo default (swappable):** the **state engine** — appraisal spikes a primary, decay relaxes it toward temperament; **energy + allostatic load** ride as catalog condition-modifiers; the **psych-zone** (hyper/optimal/hypo) is the Yerkes-Dodson curve made state. High arousal *narrows*; the `{thought}` should render the narrowing (fixation, tunnel vision, can't-think-straight), not just report high fear. Ego depletion is cited *with* its caveat.

## E. The house method — staying in-character

### `staying-in-character.md` — being one person faithfully and refusing the story's pull (THE load-bearing file)
- **When to load:** **every turn** — especially whenever the "obvious," genre-expected, or conflict-resolving move tempts, and whenever checking that a choice is genuinely the character's own.
- **Canon:** `docs/probe-plan.md` (the intent/narrative-completion bias; faithful refusal as the make-or-break LLM behavior; framing + beat-blindness as mitigation; measure the residual), `docs/design.md` (beat-blind sim; faithfulness by construction), `docs/self-and-perception.md` (act from self-image; the three views; self-deception as thought≠action), `docs/recording-model.md` (thought/action as two streams; the lie is the gap), `.claude/agents/character-simulator.md` (the agent's hard rules this file serves).
- **Holds:** faithful refusal (a valid success) · narrative/intent-completion bias (the thing to resist) · beat-blindness · thought ≠ action (the lie, self-deception) · act from self-image not ground truth · the three views · negative capability (Keats) · Stanislavski's magic-if + given circumstances · living truthfully under imaginary circumstances (Meisner) / "follow the character, not the plot" (improv) · determinism as faithfulness · the explicit-weighing thought · anti-sycophancy by framing.
- **Repo default (swappable in framing, not in principle):** this *is* the agent's thesis, not a swappable default — faithful-to-the-person, blind-to-the-outcome is non-negotiable. What a fork may swap is the *craft framing* (which acting or de-biasing lens to reach for); the discipline itself (refuse the false move; a refusal means the *situation* is wrong) is load-bearing and stated in `docs/probe-plan.md` and the agent definition.

---

## Cross-file spine
Files A–D are the reasoning field — the felt spark (A), the mind-reading (B), the choice (C), the body's distortion (D). File E is the **spine that runs through all of them**: whatever emotion is appraised, mind is read, or choice is weighed, it lands in this project only as *this person's own faithful act, blind to the beat*. Read the craft file for the *what*; read `staying-in-character.md` for *how it stays theirs* without the story completing itself through them.
