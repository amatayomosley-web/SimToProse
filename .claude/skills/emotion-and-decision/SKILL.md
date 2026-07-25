---
name: emotion-and-decision
description: The character-simulator's reasoning toolbox — the substrate for acting a person. Appraisal theories of emotion (OCC, Lazarus, Scherer's component-process, Roseman, Smith & Ellsworth, Frijda's laws + action tendencies, Arnold, Weiner), core affect & dimensional emotion (Russell's circumplex, Barrett's constructed emotion, PAD, PANAS, Thayer, Plutchik, and how valence/arousal fall out of the Panksepp basis), theory of mind & mentalizing (false-belief, Dennett's intentional stance, theory-theory vs simulation, Dunbar's orders of intentionality, mind perception's agency/experience, cognitive vs affective empathy, thin-slicing, second-order belief, egocentric bias), naturalistic & bounded decision-making (Simon's satisficing, Klein's recognition-primed decision, Gigerenzer's fast-and-frugal heuristics, Rasmussen's skill-rule-knowledge, Endsley's situation awareness, Boyd's OODA, image theory, the somatic-marker hypothesis), heuristics & biases that tilt choice (prospect theory & loss aversion, framing, anchoring, availability, representativeness, confirmation/motivated reasoning, sunk cost, present bias, dual-process, the affect heuristic, attribution biases, appraisal-tendency), how emotion/energy/stress modulate cognition (Yerkes-Dodson, Easterbrook's cue-utilization, allostatic load, broaden-and-build, affect-as-information, the hot-cold empathy gap, mood-congruent memory, the ego-depletion caveat), and the house discipline of staying in-character and resisting narrative-completion bias (faithful refusal, beat-blindness, thought≠action, acting from self-image, negative capability, Stanislavski's magic-if). Open it when a turn needs an emotion computed from an event, a choice weighed between colliding pulls, another mind read from the outside, a stressed or exhausted state bent onto cognition, or a check that the move is truly the character's own. Framework-neutral — a well of peers, not one prescribed truth.
---

# Emotion & Decision — the character-simulator's reasoning well

This is the toolbox the **`character-simulator`** agent draws on while it works. The agent is the *will* (be one person for one turn; act faithfully; stay blind to the beat); this skill is the *well* — the emotion, cognition, and decision frameworks it reaches into to reason *as* that person well. It is the reasoning substrate for acting a human: how a moment becomes a feeling, how feelings and stakes resolve into a choice, how another mind is read from the outside, how a tired or terrified body bends thought, and how to keep all of it the character's own.

**It holds craft, never facts.** How to appraise an event, weigh a collision, or read a face lives here. *What* this character knows, wants, fears, and remembers — and *what* is in the scene — reach the simulator only through its context packet. Reading this toolbox is reading *how to be a person*, which never crosses the agent's knowledge wall; the toolbox is disciplined to hold only craft, so the two never blur.

**Framework-neutral and open.** Emotion has no one true taxonomy and choice no one true model. Every framework below is a peer in a well, not a rung on a ladder; where this project names a default it is a **reference point, marked swappable**, not a rule. A fork replaces one reference file and inherits the rest. The canon these files digest lives in `docs/` (once); if a reference and its doc disagree, the doc wins.

## How this toolbox is organized
The deep material lives in `references/`, one file per framework-cluster, grouped by the altitude of the problem — from the felt spark, through reading others and making the choice, to the body under load and the discipline that keeps it faithful. **This `SKILL.md` is the router** — it indexes what each file holds and when to pull it. Read the router to find the one file the moment needs; read that file; skip the rest. (The deep reference files are authored in a **later pass** — see `references/_index.md` for their outlines. The index below is the map they fill in.)

**A missing reference file is not a stall condition.** Entries not yet authored have no file on disk; when the router sends you to one that's missing, act on this index's own one-line summary for that entry and proceed — never stall on, or invent, the file.

The spine the whole toolbox serves is the repo's generative loop: **`genetics → +history → baseline vectors → +situation → effective vectors → [LLM resolves narratively] → {thought, action}`** (`docs/generative-model.md`). Emotions and virtues are **not stored** — they are generated on the Panksepp motivational basis, appraised up by events, decayed down by time, buffed/debuffed by the moment, and resolved by weighing — never by a code-side argmax. These files are that loop, decomposed into craft.

---

## The index — what lives where

### A. The felt layer — how a moment becomes an emotion
**`references/appraisal-theories.md`** — *event → emotion: the evaluations that turn a happening into a specific feeling. Load when computing what an event evokes, or why two people feel differently about the same thing. Canon-linked to `state-engine.md`.*
- **Appraisal, the core claim (Arnold, Lazarus)** — emotion follows the *evaluation* of an event for one's well-being, not the event itself; Magda Arnold coined "appraisal" and the appraisal→action-tendency sequence.
- **OCC model (Ortony, Clore, Collins, 1988)** — 22 emotion types as valenced reactions to three things: *consequences of events* (pleased/displeased), *actions of agents* (approve/disapprove), *aspects of objects* (like/dislike); the most implementation-ready, computationally beloved.
- **Lazarus — cognitive-motivational-relational** — *primary appraisal* (goal relevance, goal congruence, ego-involvement) + *secondary appraisal* (blame/credit, coping potential, future expectancy); each emotion has a **core relational theme** (anger = "a demeaning offense against me and mine").
- **Scherer — Component Process Model (CPM)** — emotion as an unfolding sequence of *stimulus evaluation checks*: relevance → implication → coping potential → normative significance; five components (cognition, physiology, motivation, expression, feeling) synchronize.
- **Roseman's appraisal model** — a compact dimension grid (unexpectedness · motive-consistency · appetitive/aversive · probability · agency · control potential · problem source) mapping onto discrete emotions.
- **Smith & Ellsworth (1985)** — six dimensions recovered empirically: pleasantness, anticipated effort, certainty, attentional activity, self/other responsibility, situational control.
- **Frijda — laws of emotion + action readiness** — emotion as a *state of action readiness* (an action tendency); the laws of *situational meaning*, *concern*, *apparent reality*, and *hedonic asymmetry*.
- **Weiner — attributional theory of emotion** — the *locus / stability / controllability* of a cause routes to specific emotions (pity, anger, guilt, shame, pride); the bridge to locus-of-control.

**`references/core-affect-and-dimensional.md`** — *the shape of feeling-space: the axes and bases emotions live on. Load when rendering an emotional state's texture, blending named emotions, or relating the Panksepp primaries to valence/arousal. Canon-linked to `generative-model.md`, `state-engine.md`.*
- **Panksepp's primary-process emotions (the house basis)** — SEEKING · FEAR · RAGE · CARE · PANIC/GRIEF · LUST · PLAY, distinct action-dispositional systems; the level genetics and history operate on.
- **Russell's circumplex / core affect** — two orthogonal axes, *valence* (pleasant–unpleasant) × *arousal* (activation–deactivation); named emotions sit around the ring.
- **Barrett — theory of constructed emotion** — emotions are *constructed* in the moment from core affect + interoception + learned concepts, not triggered as universal biological types; the honest counter to basic-emotion views.
- **PAD (Mehrabian & Russell)** — Pleasure, Arousal, **Dominance**; the third axis separates anger (high dominance) from fear (low) at equal valence/arousal.
- **PANAS / two-factor (Watson & Tellegen)** — Positive Affect and Negative Affect as two *independent* dimensions (rotated 45° from valence/arousal).
- **Thayer's two arousal dimensions** — *energetic* arousal (energy↔tiredness) and *tense* arousal (tension↔calm); the direct tie to the energy/state layer.
- **Plutchik's wheel** — eight primaries in four opposing pairs, with intensity and blends (dyads) — the color-mixing model of named emotions.
- **Basic emotion theory (Ekman)** — a small set of discrete, pan-cultural emotions with facial signatures; kept as a peer and a caution (about faces, not action-pulls).

### B. Reading other minds
**`references/theory-of-mind.md`** — *mentalizing: inferring what the people in front of them think, want, and feel — from behavior alone, often wrongly. Load when the character must read intent, be deceived or deceive, or model what another knows. Canon-linked to `self-and-perception.md`, `knowledge-model.md`, `relationships.md`.*
- **Theory of mind (Premack & Woodruff, 1978)** — attributing mental states to others to predict behavior; the founding question.
- **False-belief task (Wimmer & Perner; Baron-Cohen, Leslie & Frith's Sally–Anne)** — the benchmark: representing that another holds a belief *you* know is false (~age 4); the root of deception and dramatic irony.
- **Dennett's intentional stance** — predict a system by ascribing beliefs + desires and assuming rationality; the stance, not the innards.
- **Theory-theory vs simulation theory** — do we mentalize via a tacit folk-psychological *theory*, or by running our *own* decision machinery offline on pretend inputs? (Gopnik vs Goldman/Gordon.)
- **Dunbar's orders of intentionality** — recursive mentalizing ("I believe *that you want that she thinks*…"); a normal adult ceiling near **5th order**; the depth budget for politics and deceit.
- **Mind perception (Gray, Gray & Wegner, 2007)** — two dimensions others are read on: **Agency** (planning, doing, self-control) and **Experience** (feeling, pain, hunger); moral standing tracks them.
- **Cognitive vs affective empathy** — *knowing* what they think (mentalizing) vs *feeling* what they feel (emotional contagion); dissociable systems.
- **Thin-slicing (Ambady & Rosenthal)** — fast trait/intent reads from brief observable behavior; the mechanism behind the "others-see" view — accurate *or* biased.
- **Second-order belief / mind-mindedness** — what A thinks B knows; the layer deception and secrets require.
- **Egocentric bias / curse of knowledge** — over-projecting one's own knowledge and feelings onto others; the standing failure mode of ToM.

### C. How the choice actually gets made
**`references/naturalistic-decision.md`** — *how a real person under time, stakes, and partial information actually decides — recognize, not optimize. Load when shaping the grain of the {thought} that leads to the act. Canon-linked to `decision-engine.md`.*
- **Bounded rationality + satisficing (Simon)** — limited info/compute/time → search until an option clears an aspiration threshold, take *that* — never the global max.
- **Recognition-Primed Decision / NDM (Klein)** — experts recognize a situation as typical, retrieve the *first* workable course, mentally simulate it, and act; serial, not comparative.
- **Fast-and-frugal heuristics / ecological rationality (Gigerenzer)** — the adaptive toolbox: *take-the-best* (decide on one best cue), the *recognition heuristic*, tallying — robust under uncertainty.
- **Skill–Rule–Knowledge (Rasmussen)** — behavior at three levels: skill (automatic), rule (if-situation-then-action), knowledge (effortful problem-solving); stress and expertise push *down*, novelty pushes *up*.
- **Situation awareness (Endsley)** — perceive → comprehend → project; "reading the room" before the choice, and where it fails.
- **OODA loop (Boyd)** — observe–orient–decide–act; *orientation* is the pivot where experience and expectation shape everything downstream.
- **Image theory (Beach & Mitchell)** — screen options against a *value* image, *trajectory* image (goals), and *strategic* image (plans) by a fast compatibility test before any profitability calculus.
- **Somatic-marker hypothesis (Damasio)** — bodily/affective markers tag options with anticipated value, pruning the space *before* deliberation; feeling as the front end of choosing.

**`references/heuristics-and-biases.md`** — *the systematic tilts that bend choice away from the "rational" answer — as character, not error to simulate on everyone. Load when a decision should lean, flinch, or rationalize. Canon-linked to `decision-engine.md`, `self-and-perception.md`.*
- **Prospect theory (Kahneman & Tversky)** — value over *reference-point changes*; **loss aversion** (losses hurt ~2×); risk-averse in gains, risk-*seeking* in losses; nonlinear probability weighting.
- **Framing effect** — the same outcome in a gain vs loss frame flips risk preference.
- **Anchoring & adjustment** — the first figure drags every estimate toward it.
- **Availability heuristic** — probability judged by ease of recall (vivid, recent, charged).
- **Representativeness** — judged by similarity to a prototype → base-rate neglect, the conjunction fallacy.
- **Confirmation bias / motivated reasoning** — seek and over-weight evidence for the wanted conclusion; the engine of self-justification.
- **Sunk-cost fallacy / escalation of commitment** — throwing good after bad to honor prior investment.
- **Hyperbolic discounting / present bias** — the hot now steeply outvalues the cold later.
- **Endowment / status-quo / default bias** — over-valuing the held and the current; inertia.
- **Dual-process (System 1 / System 2)** — fast intuitive vs slow deliberate; most biases are System-1 outputs left unchecked (Kahneman; Stanovich & Evans).
- **Affect heuristic (Slovic)** — the *feeling* about an option substitutes for its risk/benefit calculus.
- **Attribution biases (the ToM bridge)** — fundamental attribution error, actor–observer asymmetry, self-serving bias, hostile-attribution bias.
- **Appraisal-tendency (Lerner & Keltner)** — incidental emotions carry appraisal tendencies into unrelated choices (fear → pessimistic, risk-averse; anger → optimistic, risk-seeking, blame-outward).

### D. The body under load — state modulating cognition
**`references/stress-and-cognition.md`** — *how arousal, exhaustion, mood, and chronic stress bend attention, memory, and judgment. Load when the character's state is extreme and should *change how they think*, not just how they feel. Canon-linked to `state-engine.md`, `relevancy-gate.md`, `decision-engine.md`.*
- **Yerkes–Dodson law** — arousal–performance inverted-U; the optimum shifts *lower* for hard tasks (panic wrecks the delicate job first).
- **Easterbrook's cue-utilization hypothesis** — rising arousal *narrows* the range of cues attended (weapon focus, tunnel vision); the mechanism beneath Yerkes–Dodson.
- **Allostatic load (McEwen & Stellar, 1993)** — cumulative wear from chronic/repeated stress; shifted baselines, failure to shut off — the standing debuff of a hard life.
- **Fight–flight–freeze + the HPA axis** — the acute stress physiology under FEAR/RAGE (cortisol, sympathetic arousal); freeze as a third, non-optional response.
- **Broaden-and-build (Fredrickson)** — positive affect *broadens* attention and the thought-action repertoire; negative affect narrows it — the counter-force to threat-narrowing.
- **Affect-as-information / feelings-as-information (Schwarz & Clore)** — mood read as data ("how do I feel about it?"); sad → detailed, systematic, skeptical processing; happy → heuristic, top-down, trusting.
- **Mood-congruent memory & judgment (Bower)** — the current state cues state-congruent memories and reads, tilting what feels salient and true.
- **Hot–cold empathy gap / visceral factors (Loewenstein)** — the cold self under-predicts how a *hot* state (fear, rage, hunger, pain, craving, arousal) will drive behavior; the source of "I never thought I'd…".
- **Cognitive load & working-memory limits** — load crowds out deliberation and connection-making (ties to the connection-energy budget).
- **Ego depletion (Baumeister) — flagged honestly** — self-control as a depletable resource; the *mechanism* is replication-contested (cite the caveat), but the phenomenology (willpower frays under sustained strain) is still usable.
- **Challenge vs threat appraisal (Lazarus)** — the *same* stressor read as a mobilizing challenge or a constricting threat, by perceived coping resources.

### E. The house method — staying in-character
**`references/staying-in-character.md`** — *THE load-bearing file: being one person faithfully and refusing the story's pull. Load on every turn where the "obvious" move tempts, and whenever checking that a choice is truly the character's own. Canon-linked to `probe-plan.md`, `design.md`, `self-and-perception.md`, `recording-model.md`, the agent definition.*
- **Faithful refusal** — declining the genre-expected, conflict-resolving move when it isn't truly theirs is a *valid success*; a character who won't be moved tells the director the *situation* is wrong.
- **Narrative / intent-completion bias** — the model's pull toward the expected ending, the resolved conflict, the "something happens" output; it attaches to *apparent intent* — the bias to resist (`probe-plan.md`).
- **Beat-blindness** — never be told the target; a knowable outcome gets *completed* instead of *chosen*, and the seam shows.
- **Thought ≠ action** — the lie and the self-deception live in the gap; record both honestly, never collapse them to keep the character looking consistent (`recording-model.md`).
- **Act from self-image, not ground truth** — the villain isn't a villain to themselves; run the decision from the character's own narrative identity, free to diverge from what's true (`self-and-perception.md`).
- **The three views** — ground-truth / self-image / others-see; never leak another mind's true interior into the character's read.
- **Negative capability (Keats)** — the capacity to remain in uncertainty without reaching for resolution; being someone else without imposing yourself or the plot.
- **Stanislavski's magic-if + given circumstances** — reason "*if* I were this person in *these exact* conditions, what would I truly do?"; inhabit the given, author nothing.
- **Living truthfully under imaginary circumstances (Meisner) / "follow the character, not the plot" (improv)** — commit to what the character's logic dictates, not what the scene finds convenient.
- **Determinism as faithfulness** — every act must trace to the (genetics + history)-shaped vectors + situation; an uncaused, plot-convenient choice *is* the forcing failure (`generative-model.md`).
- **Explicit-weighing thought** — name the competing pulls in the `{thought}` ("part of me wants X, but Y…"); show the work over the injected state, or it drifts (`decision-engine.md`).
- **Anti-sycophancy by framing** — faithfulness (including refusal) *is* the task; there is no interlocutor to please and no outcome to infer.

---

## How to use this well — the method
1. **Run the loop, in order.** A turn is: *appraise* the event (A) → register the *felt state* (A) and how *stress/energy* bends cognition (D) → *read* the minds present (B) → *weigh* the colliding pulls into a choice (C) → and hold the whole thing *in character* (E). Most turns touch several files; pull each only when the moment reaches for it.
2. **Route by the question, not the file count.** What does this evoke, and why *this* feeling? → *appraisal-theories*. What does the state feel and look like? → *core-affect-and-dimensional*. What are they reading in the other person? → *theory-of-mind*. How does a real person under pressure actually pick? → *naturalistic-decision*. Which way should the choice *lean or flinch*? → *heuristics-and-biases*. Is the state extreme enough to change *how they think*? → *stress-and-cognition*. **Every turn also passes through *staying-in-character* — that is the spine, not one option among the files.**
3. **Generate, never look up a virtue.** Courage, loyalty, cruelty are *names for patterns the loop produces* — a FEAR-vs-stronger-pull collision resolved one way or the other. Never reach for "act brave"; compute the pulls and let the resolution name itself.
4. **Track numerically, resolve narratively.** The injected state (effective fear maxed, protective-drive maxed, deeply distrusts him) is *framing* — the `{thought}` weighs it and produces the act. **Never a code-side argmax**; the number stops at "the character's effective inner state," never at "the highest-scoring action" (`decision-engine.md`).
5. **Read the field, not one truth.** Each reference is a menu of peers; the repo's defaults (the compressed appraisal set, the Panksepp basis) are reference points, swappable. Reach for the framework that fits *this* person and moment.
6. **Bias is character, not universal error.** A bias enters as *this* person's state-modulated tilt — a fearful character reads threat up (appraisal-tendency), a loyalty-weighted one over-weights betrayal, a sunk-cost-prone one can't walk away. Don't simulate the same textbook bias on everyone; let disposition and state select and scale it.
7. **Stay behind the knowledge wall and the state wall.** Act only on what the packet gives — no facts outside their vault, no other mind's true interior, no future. If a detail isn't in what they perceive, it does not exist for them this turn.
8. **Let a refusal stand.** When no true pull moves them, the honest answer is "they stay, they say no, nothing changes." Report it plainly — that is success, not a failure to make the scene work.

## Status
Router + index complete. The deep reference files are authored in a **later pass**; their outlines and the canon each digests are in `references/_index.md`. Until then, this index plus the `docs/` canon it points at is the working map.
