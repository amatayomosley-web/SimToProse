# State Engine — exactly how character state is computed (WORKING)

**Status: working.** The deterministic computation of a character's state — the **vectors**, and the buff/debuff values that move them. This is the engine's center of gravity (`design.md` compute/generate split). It ties three tiers and **fills the one gap**: `design.md`'s named-but-unspecified **appraisal module** + emotion **decay** (the temporal dynamics that `relationships.md` already has for relationship edges but the emotion vector lacked).

## State is THREE tiers, not one vector
Conflating them is the confusion behind "how do we compute the state." Each tier is a value per vector, computed differently:

| Tier | What it is | Timescale | Computed by | Status |
|---|---|---|---|---|
| **Temperament** | the baseline lean of each primary (fear-proneness, care…) | ~fixed (arcs only) | generation: genetics + history + models | done (`generative-model.md`, `character-model.md`) |
| **Current state** | the *actual present* activation of each primary | fast (per beat) | **appraisal (events ↑) + decay (time ↓)** | **the gap — specified here** |
| **Effective levers** | what the decision actually sees, after context | instantaneous | the buff/debuff catalog | done (`decision-engine.md`) |

The vectors are the **Panksepp primaries** (`generative-model.md`): SEEKING · FEAR · RAGE · CARE · PANIC/GRIEF · LUST · PLAY — plus the drive, value, relationship, and condition (energy/allostatic) vectors. Each tier holds a value per primary.

**Why three, not two.** The current causal chain (`generative-model.md`) goes `baseline → +situation(catalog) → effective`, treating temperament as the only persistent level. That makes emotion **stateless** — fear reverts to baseline the instant the threat is gone; nothing lingers. Realism needs the **middle tier**: a fear *spike* that outlasts its cause, grief that sits for scenes, mood that carries between rooms. That persistent, event-driven level is **current state**, and computing it is **appraisal + decay**.

## The appraisal module — event → emotion delta (the gap, specified)
The **same shape** as the relationship update already specified (`relationships.md`: prediction-error + negativity-bias), applied to the primary vector instead of a trust edge. For each structured event `e` (from the consolidation LLM, `design.md`):

**1. Appraise `e` on a minimal dimension set** (compressed from OCC / Scherer — calibratable):
goal-congruence (helps / blocks an active drive?) · agency (self / other / circumstance) · certainty (expected / surprising) · control (can they act on it?) · norm-or-value-violation.

**2. Map dimensions → which primaries move:**
- blocked goal + other-agency → **RAGE** ↑
- threat-to-self + low control → **FEAR** ↑
- loss of an attachment → **PANIC/GRIEF** ↑
- threat to a cared-for → **CARE** ↑ + **FEAR** ↑
- goal progress + own-agency → **SEEKING** ↑
- safety + affiliation → **PLAY** ↑

**3. Scale the delta** — `ΔAᵢ = direction(dim, i) × magnitude`, where
`magnitude = severity(e) × relevance(e, V, D) × trait_sensitivity(T, i)`:
- **severity** — the event's strength. For a *wielded* threat it factors as **`damage-potential × hit-probability × context`**, not a per-weapon number:
  - **damage-potential** — harm if it lands (`damage × reach × reliability`, from the world's object model). **Property-based, not class-based**: a 4-ft blade out-reaches a 2-ft one — severity falls out of the *properties*, so it resolves to any grain. But you only resolve to that grain **where the book levers on it** (`design.md` value-granularity rule): default to the class ("a knife"), refine an instance to its specific properties at a hinge, from the book's authored detail. A **sword ≠ a knife** by affordance; **context** (distance, space) re-ranks them (a knife at 1 m beats a sword in a corridor).
  - **hit-probability** — a **combat check, attacker-skill vs defender-skill** (`relevancy-gate.md`). So threat is **weapon × wielder**, never weapon alone (a master's knife > a fool's sword); a skilled *defender* lowers it (parry/evade/disarm).
  - read through the perceiver's **threat-assessment skill** (accurate / under- / over-read) — how well they gauge the above.
  - **The defender's own combat skill also fills the appraisal's `control` dimension** → a master facing a thug has high control → low FEAR; a child has none → terror. *Same blade, different fear, by their skill.*
  Non-wielded stakes (a fall, a fire, an insult's `status-threat`) carry their severity from the world's object/action model directly. The percept must reach them first (`scene-assembly.md`): no perception → no severity → no fear.
- **relevance** — how much `e` touches *this character's* weighted values/drives (`values-and-stakes.md`, weighted by the Model). A betrayal lands harder on a loyalty-weighted person, a threat-to-my-child at max. **This is where two people diverge on the same event.**
- **trait_sensitivity** — disposition modulating gain per primary (high-Emotionality / the threat-reactivity genotype → bigger FEAR spikes; `trait-theory.md`, `baseline-generation.md`).

**4. Apply** to current state: `Aᵢ ← clamp(Aᵢ + ΔAᵢ)`. The spike persists into following beats — that *is* the statefulness.

## Decay — time pulls current toward temperament
Each beat, every primary relaxes toward its temperament baseline:
`Aᵢ ← baselineᵢ + (Aᵢ − baselineᵢ) × rᵢ`, with **per-primary rates** `rᵢ` (startle-FEAR fast; GRIEF slow; calibrated). A sustained cause (an ongoing threat) **re-appraises each beat**, holding the level up against decay; remove the cause and it relaxes. (Parallel to `relationships.md` "drift toward baseline.")

## The event-vs-condition rule — why appraisal and the catalog don't double-count
The one precise boundary that keeps the two tiers clean:
- **Events** — things that *happen* (attacked, insulted, bereaved): verbs, fire once, leave a trace → **appraisal** → a persistent Δ to **current state**.
- **Conditions** — standing states of affairs (ally present, believes-lethal, exhausted, child-at-risk): persist while true, no trace once gone → **catalog** → an instantaneous multiplier on **effective**.

So a threat that *appears* spikes FEAR via appraisal (and lingers); a threat that *persists* is also sustained via the catalog while present; when it's gone, the catalog modifier drops and the appraised spike decays. **Appraisal fires on the change; the catalog applies on the standing fact** — no double-count, and together they give both the jolt and the dread.

## Then the catalog (done) — current → effective
`decision-engine.md`: `effectiveᵢ = currentᵢ × Π(active multipliers) + Σ(active buffs)`, clamped — only the conditions the relevance gate surfaces as active. The catalog reads the **current** (stateful) vector — e.g. `{RAGE high → FEAR ×0.6}` reads current RAGE — plus standing conditions, and produces the effective levers injected as **qualitative direction** for the LLM. **No argmax** (the hard line).

## Where the values come from (provenance — no free sliders, no runtime LLM-picked numbers)
Every number the formulas consume is one of two kinds, with different origins. **At runtime the engine only *combines* pre-existing values; it never originates one** — the only thing arriving at runtime is the structured *event* (facts the consolidation LLM extracted, not numbers it chose).

**Class A — per-character values (the instance): from the character's formative world + history.**
Baselines (temperament per primary), value-weights, trait facets, drives/wounds, relationship priors — **derived at generation, never set by hand**. The world authors the baseline (`world-model.md` formative coupling; `design.md` Phase B): start from a neutral/archetype prior, apply the **models** that fit their life (each a sparse weight-diff, `character-model.md` — "War-Survivor" = FEAR-baseline-up + hypervigilance), sum to the baseline. The provenance of any per-character number is a *fact about their life* — "FEAR-baseline high → the war they survived as a child," never "the slider was at 7." Principals **authored-backward, validated-forward**; supporting cast from an **archetype model**; background from archetype + position. (Generation may use an LLM to map *history → which models apply*, but the numbers come from the calibrated model diffs, not an LLM free-pick.)

**Class B — rule coefficients (the machinery): theory → calibration → a few authored knobs.**
Appraisal maps, `trait_sensitivity` slopes, decay rates, catalog magnitudes, the scales — these apply to everyone, and come from three places in priority order:
1. **Established theory** (structure + ratios, not invented): Panksepp (primaries), HEXACO/Big-Five (facets, mean+variability), Schwartz + Moral Foundations (`values-and-stakes.md`), OCC/Scherer (appraisal → emotion), prediction-error + negativity-bias (~2–3× asymmetry, `relationships.md`), the TTS emotion-vector math (`decision-engine.md`). Built *on* validated work — the same reuse discipline as the vault.
2. **Calibration against the probe** (the magnitudes): exact numbers are **tuned by falsification**, never guessed — theory-anchored start → run the probe → adjust until behavior reads faithful (`relationships.md` / `relevancy-gate.md` / `decision-engine.md` all say *calibrate, don't guess*; `decision-engine.md`'s falsifiable test is the gate).
3. **A small authored archetype library** (the creative knobs): how hardened "Street-Hardened" is — authored once, named, inspectable, reusable; not arbitrary because it's consistent and forward-validated.

**The irreducible ground (the honest bottom):** two places hold authored/empirical input and everything else derives — (a) the **world + the character's history** (creative, but consistent and forward-plausible), and (b) the **calibrated constants** (theory-anchored, probe-tuned). You can't escape *some* authored world and *some* model constants; both here are principled, not free. There is no runtime step where a value is conjured.

## This is the answer to "two courageous people"
Same scene, same threat — the model produces different bravery, all computed, none stored:
- **ΔFEAR differs** — A's higher Emotionality (`trait_sensitivity`) spikes FEAR more on the same event.
- **The competing weight differs** — B weights the value at stake higher (`values-and-stakes.md` via the Model), so the goal opposing fear pulls harder.
- **The catalog differs** — B has `{believes just cause → SEEKING ×1.4}`; A has `{alone → FEAR ×1.3}`.

→ different **effective** FEAR vs competing pull → the LLM resolves a different act, at an intensity matching the margin (`generative-model.md` "degrees, not switches"). Courage was never a field — it **emerged** from the computation. That is "design the system, not the conditions," mechanized.

## Open questions (calibration, not structure)
1. **Appraisal dimension set** — the minimal 5 above, or a different compression? (Lean: start with 5; they span the primaries.)
2. **Decay rates per primary** — tuned to what reads as continuous across scenes; measured, not guessed.
3. **trait_sensitivity mapping** — which HEXACO facets gain which primaries (Emotionality→FEAR/GRIEF is clear; the rest to map).
4. **Stacking interactions** — default is additive buffs + multiplicative conditions, clamped; notable emotion-pair interactions (FEAR×RAGE) may need explicit catalog entries (`decision-engine.md`).

## Cross-links
- **Feeds:** `decision-engine.md` (effective levers → narrative resolution).
- **Parallels:** `relationships.md` (the same update shape, for relationship edges — reuse).
- **Basis:** `generative-model.md` (the primaries + causal chain — this tier patches the chain's middle).
- **Inputs:** `values-and-stakes.md` (relevance weighting), `trait-theory.md` (trait sensitivity), consolidation events (`design.md`).
- **Note:** momentary state-change (here) is distinct from the **arc engine** (`character-model.md` #3) — that moves *temperament* over the book; this moves *current state* over a scene.
