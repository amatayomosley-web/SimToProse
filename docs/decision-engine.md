# Decision engine — how the variable weights map and resolve into a choice
*(Roadmap #1, the "empty center." This is its core mechanism: how a character's many variable weights resolve into a recorded `{thought, action}`. Companion piece now detailed: the **drives schema** (`drives-schema.md`) — goals / fears+wounds / orientation as structured opposable fields.)*

## Principle: track numerically, resolve narratively
The temptation is a utility function — score each option by `Σ(weight × factor)`, pick the max. **Reject that as the resolver.** Explicit weighted-sums produce mechanical, brittle, gamey behavior, and we've staked realism on holistic judgment + the `{thought}` stream. Pure vibes is also wrong (inconsistent, no continuity).

**The split:** code maintains the *quantities* (deterministic mechanics → continuity + statefulness); the LLM does the *weighing* (conflict resolution → nuance), with the salient quantities injected as framing. **Weights are tracked numerically but resolved narratively.** Numbers give continuity (same person across scenes); the LLM gives the surprising-yet-inevitable choice. **The thought stream IS the visible weighing.**

## What's actually weighted (the tracked quantities)
Normalized to comparable, injectable scales:
- **Traits** — per facet: mean (the lean) + variability (spread). −1..+1 or 0–100.
- **Drives** — goals (priority), values (weight), fears (intensity). 0–1 salience.
- **Relationships** — per target: trust / affinity / respect / debt. 0–1 (or −1..+1).
- **Energy** — budget (0–1) + per-link traversal cost.
- **Emotional / arousal state** — zone + intensity (psych layer).
- **Belief salience** — recency / emotional charge on vault entries.

## Weights are VARIABLE — a function, not a constant
Effective weight at decision time = **character baseline × current state × situation × relationships**:
- **Character** sets baselines (trait means, drive priorities).
- **State** modulates moment-to-moment (exhausted → effort-avoidance up; frightened → threat up).
- **Situation** (relevance gate) raises the weight of *triggered* drives/beliefs.
- **Relationships** weight whose input counts (trust scales how much another's words move them).

So the layers we already built — **relevance gate, energy, state, relationships — ARE the weight modulators.** They compute the *effective* weight from the baseline.

## Where the weights live (by anatomy layer)
The **weight-bearing layers** of `character-anatomy.md` are **1, 3, 5, 7, and 10** — and that set is the formula above, decomposed. (Selected by *meaning*, not parity: 9 is odd and excluded, 10 is even and included.) Two **kinds** of weight live in it:

**Operands — within-layer magnitudes (1, 3, 5, 7):** the per-person, stateful quantities the formula multiplies.
- **1 Disposition** — baseline lean (facet mean + variability).
- **3 Drives** — goal priority, fear intensity, locus/coping bias (the baseline pulls).
- **5 Relationships** — trust/affinity/respect/debt: weight whose input counts.
- **7 State** — the moment-to-moment modulator that scales the rest.

**Resolver — cross-layer priority (10):**
- **10 The Model** — *what wins when the operands collide.* Not a source of weighted inputs; the priority over all of them. On the list, but a different *kind* of entry — don't double-count it as another magnitude.

**Why the rest are NOT weight-bearing (and that's correct):**
- **2 Worth (needs/values/morals)** — the *shared menu*, not a per-person weight store. Its per-person weighting is **administered by the Model (10)** ("the model = a person's weighting over this menu", `values-and-stakes.md`). The weight isn't *in* 2; it's *in 10, pointing at* 2. (This supersedes the loose "values (weight)" phrasing above — values are weighted *by 10*, not stored in 2.)
- **4 Mind** — mostly **hard gates** (knowledge presence, skill checks bound the option space) + the **situation trigger** (the relevance gate is the formula's *situation* term: it gates *which* weights are live, it isn't itself a stored weight). *Exception to track:* belief-salience and connection-energy are soft weights that live here (or migrate to 7) — don't lose them.
- **6 Identity/Self** — the **vantage** the decision runs *from*, not a magnitude; self-image *centrality* folds into the Model (10) with the rest of worth.
- **8/9 Surface/Position** — output and priors: read by observers, never weighed.

**Watch:** Layer 10 now does double duty — the worth-menu weighting *and* the conflict resolver. Acceptable for now; split if it overloads.

## The resolution spectrum (hard → soft)
Not everything is the LLM's call. Map each weight to where it acts:
- **Hard gates (code-decided, deterministic):** knowledge presence (have the fact or not); energy floor (too depleted → connection can't fire); absolute value lines (a refusal they will not cross). Resolve in code; they bound the option space.
- **Soft biases (injected, LLM weighs):** traits, drive priorities, relationship axes, mood — rendered into the decision context as salient state (*"exhausted; deeply distrusts him; desperate to protect her daughter"*), and the LLM produces the `{thought, action}` that honestly weighs them. **Default and bulk.**
- **Distribution sample (math sets, LLM colors):** the trait-as-distribution — math sets the lean + situational pull (where in the spread this moment lands); the LLM renders behavior consistent with that sample.

## Consistency guardrails (so "LLM weighs" doesn't drift)
- **Explicit-weighing thought:** the `{thought}` must *name the competing pulls* it's resolving (*"part of me wants X, but Y…"*) — forces the model to show its work over the injected weights instead of ignoring them.
- **Hard gates** keep the must-be-deterministic things deterministic.
- **Verify:** the critic checks the action is consistent with the injected state (did the exhausted, distrustful character act exhausted and distrustful?).

## Optional hybrid (performance/consistency)
For heavy decisions, numbers can PRE-RANK options (utility-AI *proposes* a shortlist) and the LLM picks + colors among them (*disposes*). Middle path; default is bias-not-sum. Calibrate by testing.

## The effective-state catalog — computing the quantities (buffs/debuffs)
How the "effective weight = baseline × state × situation × relationships" formula is actually computed and authored. Borrowed from the TTS emotion-vector model (`Claude Flow/projects/private/the-writers-desk/audio/emotion-vectors.md`: a base vector displaced by modifiers, `vector + (1−sum)×baseline`) and the RPG stat/modifier idiom.

**Catalog = the character's base levers as numbers.** Each emotion/drive/value carries a baseline magnitude (fear 10, protective-drive 6, loyalty 8…) on a fixed scale — the stat block. Bounded set (the levers), authored once, archetype-assignable. (Scale is calibration: 0–1, 0–10, 0–100 all work.)

**Buff/debuff registry = the table the system checks against.** Each entry: `{ trigger condition, affected lever, op (× or ±), magnitude, source }`:
- `{ trusted ally present → fear ×0.7 }` (relationship)
- `{ believes the threat is lethal → fear ×1.5 }` — **perception**, fired off a vault belief + its confidence (fear scales with how *they* read it, not the objective danger)
- `{ his child is the one at risk → protective-drive +5 }` (drive)
- `{ anger high → fear ×0.6 }` — **other emotions modulating each other**
- `{ exhausted / high allostatic load → fear +3 }` (state); `{ trait low Emotionality → fear ×0.6 }` (disposition)

At decision time the relevance gate surfaces the **active** conditions; the system applies only matching modifiers → `effective_fear = base × Π(multipliers) + Σ(buffs/debuffs)`, clamped. This is the same shape as TTS sum-vs-baseline: a baseline displaced by modifiers. The SAME computed effective-emotion vector can feed **two** consumers — the decision (as framing) **and** the TTS delivery vector for the rendered voice. One emotion-state, both layers.

**The hard line — the catalog computes STATE, it does not pick the ACTION.** We do NOT `if effective_courage > effective_fear: act_brave`; that argmax-on-the-sum is the gamey resolver rejected at the top of this doc. The effective levers are **injected as framing** ("effective fear maxed — exhausted, alone, believes it's lethal; protective-drive also maxed — it's his daughter") and the **LLM resolves**, naming the competing pulls in the `{thought}`. Where the calc *does* decide: **hard gates only** (absolute value lines, energy floor, knowledge presence) — the deterministic few that bound the option space.

**Why this is not the rejected weighted-sum:** the number stops at "the character's effective inner state," never at "the action with the highest score." Catalog → effective-state = endorsed ("code maintains the quantities"). Effective-state → argmax-action = rejected. The catalog gives RPG-stat *legibility* (authorable, inspectable, continuous degrees) without RPG-stat *gaminess* (the LLM, not max(), picks).

**Guardrails (or it rots into buff-soup):**
- Modifiers attach to the **bounded levers**, never per-action — no "courage in scene 47" entries.
- The relevance gate surfaces only **active** modifiers — never stack-check the whole catalog every turn.
- Resolution stays **narrative** — the LLM smooths imperfect stacking; the arithmetic frames, it doesn't adjudicate.
- Archetypes (`character-model.md` models) are **bias-packs over the catalog** — "Survivor" = a bundle of fear-up / survival-up modifiers.

**Falsifiable:** if injecting computed effective-levers does not differentiate behavior across two characters in the probe (same scene, fear-10-buffed-high vs fear-10-debuffed-low → same action), the calc is theater and we cut back to qualitative framing.

## Both sides of the collision — completing the calculation
The catalog + `state-engine.md` compute *one* drive's effective level. **A choice is never one drive — it's a contest**, and both sides run through the *same* machinery. A courage/cowardice choice:

```
FEAR-side (avoid)                  vs            ACT-side (the demanded act)
effective FEAR                                   effective[ activating primary: CARE / RAGE / SEEKING ]
 = baseline × genotype-gain                        × VALUE-WEIGHT (loyalty / honor / duty / justice — the Model, L10)
   × appraisal × catalog                           × goal-priority × relationship
                        ↘                       ↙
                  injected as DIRECTION; the LLM resolves (no argmax)
                  margin = how decisively one wins → the act's intensity
```

**Symmetry is the point — no new mechanism.** The other side is `state-engine.md` + the catalog applied to the *approach* primaries (CARE/RAGE/SEEKING) and multiplied by the **value-weight** the Model puts on what's at stake. We built FEAR's pipeline; the act-side is the identical pipeline on the other primaries × the Model's weighting.

**Where the act-side gets its "ought."** The competing pull's moral force *is* the **value-weight** — how strongly they hold the standard the act serves. That weight lives in the baseline **Model** (Layer 10), generated from the formative world + the affiliation genotype + any archetype overlay (`baseline-generation.md`). The worth *menu* is universal (`values-and-stakes.md`, Moral Foundations / Schwartz — Class-B); the *weighting* is per-person (Class-A).

**Cowardice is only meaningful against an ought.** No value-weighted act-side — nothing they *should* do — and fear winning is just **prudence**, not cowardice. The act-side is what turns flight into a *failure*. So the "other side that forces cowardly actions" is precisely the **value-weighted approach pull**; remove it and there is no cowardice to produce.

**Two knobs for the crossover** (where fear starts winning): **fear-side up** (high threat-reactivity, low effortful-control — Coward A) or **act-side down** (low value-weights on what's at stake — Coward B). Brave is the mirror (act-side reliably clears fear-side). The vice/virtue is the **ratio**, never a stored field.

## Net
Map the weights as **tracked, normalized state quantities** (per-character baselines, modulated by state/situation/relationships into *effective* weights — computed via the buff/debuff catalog above), **resolved by injecting the salient ones as framing for the LLM to weigh** — with hard gates for the deterministic few, and an explicit-weighing thought + verify for consistency. **Never a code-side weighted-sum as the resolver.**
