# The generative model — how a character produces behavior (first principles)

> The spine. Virtues and emotions are **not stored** — they are **generated** from a bounded basis, shaped by genetics + history, transformed by situation, and resolved narratively. Everything in `character-anatomy.md` serves this loop; the detail docs (`drives-schema`, `decision-engine`, `values-and-stakes`, `character-model`, `trait-theory`, `world-model`) are this spine, decomposed.

## The one principle
A character is not a list of traits and virtues to author. It is a **small set of vectors** plus a **generator** that turns them into behavior. "Courageous," "loyal," "bitter" are **names an observer gives to patterns the generator produces** — never fields we set. Design the generator; the virtues emerge. (This is `character-model.md`'s "realism = lever conflict, not lever count," taken to its root.)

## The basis — what the vectors ARE
*(Recommended; pending the author's final ratify. Everything else in this doc is basis-agnostic — only this section changes if the basis changes.)*

The per-person vectors are the **motivational primaries** — distinct, action-dispositional systems (Panksepp's primary-process emotions): **SEEKING · FEAR · RAGE · CARE · PANIC/GRIEF · LUST · PLAY.** Chosen over valence-arousal (too lossy — it collapses fear and anger, which sit adjacent in that space yet drive *opposite* actions) and over facial-expression emotions (Ekman — about faces, not action) because:
- each primitive **is an action-pull** — the unit a decision engine actually runs on;
- it is **the level genetics and history operate on** — temperament is heritable variation in these systems; experience tunes them;
- valence / arousal **fall out as a derived summary view**, so the dimensional model is kept for free.

Named emotions and virtues are **coordinates / blends** in this space (color-mixing). The worth layer already uses this shape — Schwartz's values on 2 axes (`values-and-stakes.md`); this gives the affective layer the analogous principled basis instead of an ad-hoc emotion list.

## The causal chain — nothing is arbitrary
```
genetics (innate seed)
  → + history (slow transform: formative context + personal events)  → baseline vectors
    → + situation (fast transform: the buff/debuff catalog)           → effective vectors
      → [LLM resolves the collision, narratively]                     → {thought, action}
```
- **Genetics** seeds innate temperament (the vector they're born leaning toward).
- **History** bends it over a life: the world / era / class / culture they're born into (`world-model.md` formative coupling — "the world authors the baseline") **plus** their personal events (the wound, the mentor, the betrayal).
- **Lived events** move the *current* state during the story: appraisal spikes a primary on an event, decay relaxes it toward temperament between events. So the baseline is *temperament*, but what the catalog modifies is *current state* (baseline + what's happened, not-yet-faded) — the middle tier the chart compresses (`state-engine.md`).
- **Situation** computes the effective state in the moment via the catalog (`decision-engine.md`: base levers × perception / other-emotion / state / relationship buffs and debuffs).
- **Resolution** is the LLM weighing the salient effective vectors — **never a code-side argmax** (`decision-engine.md`, the hard line).

## Degrees, not switches
Nothing in the chain is binary. Vectors are continuous magnitudes; the collision yields a **margin** (how decisively one pull beats another), not a win/lose bit; the action space is continuous; the LLM **renders an act whose intensity matches the margin** (whisper → object → intervene → die on the sword). "Brave **to a point**" = the cost level where the rising situation drives the margin to zero — an **emergent, fuzzy crossover** (jittered by trait variability + state), never an authored threshold. The only boolean is the observer's after-the-fact label.

## Virtues are emergent names
Courage is not an emotion and not a field. It is **FEAR active (threat registers) + a stronger primary (SEEKING a goal / CARE for someone / RAGE at injustice) overriding it, resolved.** Loyalty = CARE-for-the-group vs self-interest. Honesty = an Honesty-Humility lean + a truth-value vs FEAR-of-consequence. **One generator produces every virtue at every degree** — which is why we never author a system per virtue or per action. (This is the answer to "design the system, not the conditions.") **And every vice the same way:** cowardice is that identical FEAR-vs-pull collision resolved the *other* way — fear *wins*. The coward and the hero can feel identical fear; they differ only in the competing pull's weight or fear's gain. So "coward" is a *low crossover* (fear wins early), never "high fear" — and a person with no fear at all is reckless, not brave (nothing registered to override). Betrayal (self-interested SEEKING beats CARE) and cruelty (RAGE unchecked by CARE) are the same machine, other cells.

## Determinism is the feature
Behavior is **fully caused** by the (genetics + history)-shaped vectors + situation. For a faithfulness engine that is the point — an uncaused choice is the "forcing" failure mode the project rejects; every action must trace to the character or the biography isn't faithful (`README.md` — faithfulness by construction). The surprise (the realism test's *non-obvious but in-retrospect-inevitable*) comes **not** from free will but from **(a) vectors being distributions, not points** — the same config samples differently moment to moment (`trait-theory.md`) — and **(b) interaction complexity** — too many vectors colliding to predict from any one. **Fully caused, not predictable** = the realism criterion.

## Creation by depth — the investment is the asset
Depth is **not a cost to minimize; it is what makes the outputs better, and it amortizes.** Spend lavishly where it is **levered** (the world's real systems; the principals; the plot hinges); spend nothing where it is **inert** (lazy-resolve the long tail — `knowledge-model.md` frame-problem discipline). Deep on load-bearing, lazy on inert — the two compose.

- **Principals (a handful):** generate-from-causes. **Authored backward** — start from the character the story needs, generate the genetics + history that *yield* those vectors — and **validated forward** — the world must plausibly produce them. The history is not only for the numbers: it **populates the vault** (they remember it; `{thought}` and dialogue draw on it) and gives every vector **provenance** (the fear traces to the wound).
- **Supporting cast:** archetype (a `character-model.md` model preset) + light individuation (position + a few formative facts + perturbation).
- **Background:** archetype + position, perturbed. No history.

**Why the investment pays:** provenance makes interiority real instead of hollow; a deep world can plausibly *deny* a lever (directing by circumstance without the seam showing); rich interacting vectors produce emergent surprise thin setups can't; and it **reuses** — one deep world → many novels, one deep principal → many POVs. The deeper the core, the more every downstream run benefits.

## Where the pieces live
- `drives-schema.md` — Layer-3 operands (goals / fears+wounds / orientation) expressed on the basis.
- `decision-engine.md` — the effective-state catalog (buffs/debuffs), narrative resolution, and the no-argmax hard line.
- `values-and-stakes.md` — the worth menu the vectors reference; the values' own 2-axis basis.
- `character-model.md` — model archetypes (bias-packs over the basis) + "realism = conflict, not count."
- `trait-theory.md` — disposition (HEXACO) + the (mean, variability) that grades expression and supplies the surprise.
- `world-model.md` — formative coupling (history shaping the baseline) + circumstance / consequence.
- `character-anatomy.md` — the 10 layers this loop runs across.
