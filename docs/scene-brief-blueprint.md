# The Scene-Brief Blueprint — sizing a sim run (how much plot fits)

**Purpose.** How big to make one sim brief: what a single run can and cannot produce, the measured beat-ceiling, and how to decompose a multi-part plot into briefs. Built from measured runs (gemma4:26b-a4b, a multi-character dinner scene-class). Pairs with `driving-the-engine.md` (the per-lever playbook); this doc is about *scene sizing*, that one is about *steering a beat*.

## What one sim run IS
A brief = **one situation** + a **cast**, each member carrying a **drive** (a standing want, blind to the outcome). Each beat the floor passes to the actor with the highest **urge** (`salience + addressed_bonus + disruption_stake − recency − inhibition`); that actor produces an emergent action + thought + self-report tags. The run ENDS — on its own, not at budget — when:
- **lull** — max urge falls below the floor (`_FLOOR_THRESHOLD`, 0.06): the pressure has spent itself and no one is moved to speak;
- **exit** — an actor walks out and the present cast drops below 2;
- **empty** — a cast of 1 commits a single beat and stops (no floor for it to pass to).

A run is therefore the **emergent discharge of one situation's pressure** — a positioning engine, not a plot engine.

## The measured ceiling
Beats per run, this session (temp 1.0; cast = present actors; "tensions" = distinct matters loaded into the brief):

| cast | tensions | beats | ended by |
|---|---|---|---|
| 1 | 1 | **1** | empty (no floor) |
| 3 | 1 | 2 | lull |
| 2 | 1 (calm) | 3 | exit |
| 3 | 1 | 4 | lull |
| 3 | 1 | 4 | lull |
| 2 | 1 (hot, live trigger) | 5 | exit |
| 3 | **3** | 6 | lull |

- **Cast of 1 → exactly 1 beat.** Multi-beat REQUIRES ≥2 actors — the floor must have somewhere to go.
- **A 2–3-actor scene self-terminates at ~3–6 beats**, by lull or exit. Budget is a ceiling, never a target; the scene stops when the pressure is spent.
- **Heat extends the tail a little** (a live, un-commandable trigger pushed a 2-actor scene to 5); calm scenes lull sooner. See *Reading the stop* for why.

## Reading the stop — the termination mode is diagnostic
The three stops are **not** interchangeable. *Which* one fires tells you what kind of scene you just ran and what you have to write next.

- **lull** — a **deliberation** scene: actors who can only *talk* (a table, a negotiation, a standoff with no action available to them). Positioning exhausts, every urge decays below the floor (0.06), the scene settles. The common stop.
- **exit** — an **actionable** scene: the situation affords a physical act (leave to fetch something, strike, flee). The actor pursues the drive, walks, and the present cast drops below 2. The scene ends on a *departure*.
- **empty** — a cast of 1: one beat, no floor to pass to.

**Measured this session:** a two-actor scene whose actor *could act* on his drive ran to **5 beats** and ended when he rose and left to do it (**exit**); the matched two-actor table scene, with no action available, **lulled at 4**. The actionable scene ran longer because the actor had somewhere to go — a talk-scene can only decay.

**An exit is still positioning, not resolution.** The actor leaves *to pursue* the want; the matter is not closed and the scripted turning-point still did not emerge. Lull and exit hand the pen back at the same depth (~5 beats, one tension) — they differ only in the *shape* of what they hand you:

- **lull → a settled tableau.** Everyone has said their piece. The seam you write is a **director-placed circumstance** that breaks the stillness (a letter, a drop, an arrival).
- **exit → a forward beat.** An actor left to act. The seam you write is **what happens when they get there** — the next brief opens on the arrival or the act.

**The same scene can stop both ways.** Re-run, the actor once left to act (exit) and once delegated and stayed (lull) — same drive, same substrate, different *tactic*, because the action is sampled (temp 1.0). The drive and the beliefs are the fixed inputs; the surface move is stochastic. So when a downstream beat depends on a *specific* action (a departure, a strike, a door slammed), **place it — do not count on the sim emitting it.** This is the same law as "the turning-point is placed, not emerged," seen from the run-to-run variance side.

The stop is the engine telling you which move it needs from you next.

## What one run PRODUCES — and does not
- **Produces: POSITIONING.** The cast reveal their stances and the friction between them — the emergent truth of who-wants-what and how it grinds. This is the gold: hand-authoring it is the puppeteering the engine exists to prevent.
- **Does NOT produce: RESOLUTION or a turning-point.** Across every run this session, no decision was reached and no one was moved to the decisive act on their own. Pressed on a matter, the authority *deferred* — the **same** deferral repeated beats later — and the scene circled and lulled. Nobody *decided*, *left*, or *acted* to close the matter. (Same shape as `driving-the-engine.md` Conclusion 1: the exit/rupture is not a turn-lever.)
- **Stacking tensions DIFFUSES the run.** Three matters loaded into one brief were each *touched* but none *driven home*; the single-tension brief pressed its one matter to its edge. More plot in the brief buys shallower coverage, not more plot resolved.

## The rule: ONE tension per brief
- **One turning-point / pressure per brief.** The cast will drive a single matter to its edge and surface it fully in ~4–6 beats. Stack three and you get diffuse positioning on all three and resolution on none.
- **The turning-point is PLACED, not emerged.** The decision, the departure, the event (a letter arrives, a servant drops the body, a character finally *goes*) is the **director's** to place — via a harder wall, a fresh circumstance, a sharper drive — or the **narrator's** to write. The sim hands you the pressure and the positions; the break is yours.

## Decomposing a multi-part plot (a blueprint beat-list of N events)
Sort each plot event into one of three bins:
1. **Emergent (sim).** Character positioning under *one* pressure → give it a brief, run ~4–6 beats, take the truth.
2. **Director-placed circumstance.** Something that happens *to* the cast (a letter, a drop, a death, an arrival) → write it into the *situation* of the relevant brief; do not expect the sim to generate it.
3. **Narrator-added load-bearing beat.** A turning-point, a decisive line, a loss-of-control the sim won't emerge → write it (see `driving-the-engine.md` Conclusion 4 + the misdirect/recoil findings).

Then **chain the emergent briefs with `--resume`** — affect, arc diffs, and acquired beliefs carry across the link (see `driving-the-engine.md`, the resume rehydration) — one tension per link, with a director-placed circumstance opening each new link and narrator beats laid over the seams.

**Sizing heuristic:** a heavy blueprint beat of ~7 plot events is NOT one run. Budget roughly **one tension (~4–6 beats) per brief → ~2–4 briefs per heavy beat**, plus the director-placed events between them and the narrator's load-bearing beats over them. When a scene refuses to advance, that is not a failure to tune away — it is the engine telling you the next move is a *placement*, not another beat.

## Status / confidence
Single runs, n small, temp 1.0, one model + one scene-class — **directions, not rates.** The beat-ceiling and the positioning-not-resolution finding are consistent across ~7 runs, but confirm at K≥6 (the `scripts/exp.py` harness) before a number is load-bearing. Re-measure on a model swap.
