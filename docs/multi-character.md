# Multi-Character Conversation & Debate (3+) (WORKING)

**Status: working.** The logic for group conversation — especially **3+ characters in intuitive debate**, where turn-order, interruption, sides, and silence must *emerge*, not be scripted. The last big sim seam. Built on the single-character loop (`scene-assembly` → `decision-engine` → `consolidation-loop`) iterated in a turn-taking round; the new parts are the **floor scheduler**, **addressing**, **stance dynamics**, and **convergence**.

## Not a new engine — the loop in a turn-taking round
A conversation is single-character turns in sequence, each speaker perceiving what the others just said. The thought/action wall (`recording-model.md`) means hearers get the **words, not the intent** (subtext / lies / misunderstanding, for free); each line **appraises** into every hearer (`state-engine.md`); Insight checks read subtext (`relevancy-gate.md`). With 2 people turn-taking is trivial. **3+ is the hard case** — at any moment several want to speak, to different people, with different stakes.

## The heart: the urge-to-speak scheduler (intuitive, not round-robin)
The engine computes, per character per step, an **urge-to-speak** (deterministic — the compute side of the split):
```
urge = stake(topic) + addressed_bonus + disagreement_pressure + affect + relationship_defense − social_inhibition
```
- **stake** — how much the live point touches their goals/values (the Model);
- **addressed_bonus** — were they just spoken *to* / challenged? (spikes a reply);
- **disagreement_pressure** — how much the last line *violates* their position (× conviction × RAGE);
- **affect** — current emotional activation (the heated one);
- **relationship_defense** — urge to back an ally under attack / pile on a rival;
- **social_inhibition** — disposition threshold (timid vs dominant — HEXACO / genotype).

**Selection = a softmax over the urges, with a temperature knob** (over the floor threshold). At **temp 0** the highest urge always speaks — deterministic, **reproducible** (which the recorder's ground-truth-replay test wants), fully plot-controllable. **Raise the temperature** and the most-compelled is the most *likely* but not certain — natural jitter (the quiet one occasionally jumps in; the dominant one doesn't always win the floor; no monopoly). Default low, calibrate; the director can pin the speaker on plot hinges. Mid-turn, an urge over the higher **interrupt threshold** cuts in. **No urge over threshold → a lull → convergence.** Turn-order, interruptions, who-rebuts-whom, and *silence* all **emerge** from this one score — that is the "intuitive." **The urge calc is cheap deterministic arithmetic, not an LLM call**; inference runs exactly once per turn (the chosen speaker's line). The engine schedules; each character only generates their line.

## Addressing — the threads inside the group
Each line tags its **target** (a person, or the room) via the consolidation event-tags. The target gets the `addressed_bonus` next step → **threaded back-and-forth** (A rebuts B → B is pulled to answer A even as C strains for the floor). A broadcast (to the room) raises everyone's stake; a direct address opens a duel inside the crowd.

## Sides emerge — never assigned
A character's alignment to the live point = how it fits **their** values/goals (the Model) + their **relationships**. Shared values → urges fire together (they back each other); opposed values → rebuttal. **Coalitions form from who-values-what**, not an assigned side — the value model paying off at group scale.

## Stance dynamics — the debate's ARC (and why debates polarize)
Each character holds a **stance** on the live question `{position, conviction}`. Per-utterance appraisal updates it (`relationships.md` prediction-error, applied to beliefs):
- low conviction + a **trusted** source + a good argument → **stance moves** (persuasion);
- high conviction + a **distrusted / rival** source → the stance **HARDENS** — the **backfire / reactance effect**, which is why real debates *polarize* instead of converging.

The trajectory = stances converging (consensus), hardening (stalemate / polarization), or one **flipping** (a turn). Emergent, not scripted — and it gives the debate a measurable end-state.

## Typed contributions — the argument structure is the TRACE
Each line is an event-typed contribution from the **dialogue-act family** — **assert · rebut · concede · question · support · escalate · deflect** — a registered *extension* of the event catalog (`record-contract.md`), NOT the core schema itself (audit B5b: the core verbs — harm / aid / betray / reveal / … — are a disjoint family; both live in the one catalog and validate the same way; dialogue-acts additionally carry the `target` field that feeds `addressed_bonus`). The argument's logical structure is the *trace* of these — we never script the argument; each character argues from their position and the structure falls out. (Concede / flip are the dramatic beats; escalate is where heat — or violence — enters, carried by appraisal.)

## Convergence — when the debate ends
The engine ends the scene when: **all urges fall below the floor** (exhausted), or someone **concedes / flips** (a stance crosses a threshold), or the **decision is forced** (the scene goal resolves), or an **interrupt** (someone storms out / an external event). The lull is the default detector; the rest are sharper exits.

## The risks — concentrated here, all empirical
3+ debate stresses the system hardest. Honest about three:
1. **Coherence at N (the keystone, maximal).** Each of N characters must track the debate, their shifting stance, and everyone's positions over many turns, each only on their scoped view. The **worst-case stress on the consolidation/coherence loop** (`consolidation-loop.md`) — drift shows here first. **This is why the coherence probe should BE a 3+ debate.**
2. **The agreeableness pull (debate-specific sycophancy) — real but PROVEN-SOLVABLE.** LLMs trend toward harmonizing, which *can* flatten debate. **But the `claude-suite` is a running counter-example** (5-agent roundtables): a **`challenge`** scoring dimension, a challenger role (marcus), **penalties** for redundancy (−3) / off-directive (−5), and **convergence-detection** (fuzzy-match 80% — tracked because they usually *don't* converge). It sustains genuine challenge across many RTs and yields 100+ novel synthesis concepts. So the mitigation is **proven**: make challenge the *framed, incentivized task*, differentiate roles, detect convergence. The sim is **better-positioned** than the suite — its disagreement is *genuine* (characters' values truly differ), a stronger anti-convergence force than the suite's *incentivized* (spark) one. **Residual:** the suite proves it for *analytical* debate; the *dramatic / in-fiction* transfer (conviction as the in-fiction stake, not sparks) is what the probe confirms — recipe in hand, not a feared unknown.
3. **Over-clean argument.** Real debate has tangents, talking-past-each-other, emotional derailment. LLM debate trends too tidy/logical. The urge-model + value-misalignment + RAGE-derails-reason should rough it up — a quality risk to measure.

## v1 implementation + the first live finding (2026-06-11)

A first runner exists — **`scripts/scene.py`** — implementing the loop and a **reduced floor scheduler**: the floor passes to whoever the last line moved most by **appraisal salience** (|Δaffect| through each hearer's regard/traits), deterministic max, no temperature; the opener is whoever the opening situation moves most; termination is lull-or-budget. It reuses the single-actor spine unchanged (`scene-assembly` → turn → `state-engine` appraisal) — confirming this doc's "not a new engine" claim *in code*. The scene is set up by the **wants→drives discipline** (`design.md` load-bearing constraints): the director gives each actor a genuine standing DRIVE, never the outcome.

**Validated — BP1.3 (the superseded fixture scene), live, no scripted lines.** Three actors on genuine drives produced the casual *domestic* cruelty emergently — the father's asset-ledger framing (*"damaged goods… written off when spent… this is not cruelty"*) against the son's wordless innate discomfort (*"the wrongness crawl under my skin… I was raised to think like this and I cannot"*) — and surfaced the canonical *"assess it after dinner"* **unscripted**. The cruelty came from decent wants colliding over a being only one actor saw as a person: **no villain in the room** — the design's central bet, confirmed in a real run.

**The findings map straight onto this doc's own design — the reduced floor is exactly what falls short:**
- **Pure salience starves the quiet actor.** Corin never won the floor; the two most-provoked (father/son) locked it. This is *why* the documented urge model is richer than salience — **`addressed_bonus`** (she'd be pulled in when spoken *about*), **`social_inhibition`**, and the **softmax temperature** (the quiet one occasionally jumps in; no monopoly) are the fix. The v1 starvation **confirms** the fuller scheduler is needed, not optional.
- **The break needs a storm-out exit + budget.** Ilsa escalated but never walked out in 8 beats — the canonical exit beat (*"assess it **after dinner**"* → he can't wait → he leaves) was arriving exactly as the budget hit. The documented **convergence exits** (concede/flip, decision-forced, **storm-out**) need wiring; lull-or-budget alone under-stops.
- **Over-clean / repetition.** Every beat opened with the same gesture — the actors can't see what they've already done. Per-speaker rolling context (this doc's addressing + the recent stream) is the fix.

So the next build **grows the v1 salience floor into the full urge scheduler this doc already specifies** (`addressed_bonus`, `social_inhibition`, temperature, the dialogue-act `target` field) and wires the storm-out exit. The doc was the spec; the live run found precisely the gaps it predicted — and the `_note`/`note` stable-prefix leak (design notes reaching the prompt) is a separate, still-open fix that inflates how much of the voice is emergent.

## Cross-links / status
- **Composes:** `scene-assembly` (perceive the words), `recording-model` (thought/action wall = subtext), `state-engine` (per-line appraisal), `relationships` (stance update + backfire), `consolidation-loop` (tagged contributions — the keystone), `decision-engine` (the line is the action).
- **New mechanics here:** the urge scheduler, addressing, stance dynamics, convergence.
- **Prior art (LIFT — proven):** `claude-suite` — a running 5-agent debate that sustains challenge without collapsing to agreement. Reuse its **convergence detector** (→ our convergence), its **judge** (→ the consistency critic), and its **challenge-as-framed-task** incentive (→ bind each character's conviction/stance as the in-fiction equivalent of the spark economy). Proof the debate-sycophancy risk is solvable.
- **Probed by:** the coherence probe (a 3+ debate is the maximal-stress instance).
