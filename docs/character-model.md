# Character model — the levers that make a person real

A character is "real" when their recorded biography reads like a person's, not a puppet's. That does **not** come from the *number* of attributes — it comes from a few **conflicting, stateful levers applied consistently.**

## The core levers (each detailed in its own doc)
| Lever | What it drives | Doc |
|---|---|---|
| **Beliefs (vault)** | what they think is true (can be false) | `knowledge-model` |
| **Goals / wants** | what they pursue → action | (here) |
| **Values** | what they hold right → scores/constrains action | (here) |
| **Fears / wounds / flaws** | what they protect/avoid → the friction engine | (here) |
| **Relationships** | who they trust/love/owe → social action + transmission gain | `relationships` |
| **Skills** | which checks they can pass | `relevancy-gate` |
| **Energy / state** | focus, mood, allostatic load → modulates everything, moment to moment | `relevancy-gate` (energy) |
| **Voice** | how they express → makes them distinguishable | `narration` |

## Realism = lever CONFLICT + lever STATE, not lever count
- **Conflict.** A real person isn't one utility function — they hold **competing drives** (a want vs a value; a fear vs a desire; loyalty vs ambition). Every meaningful decision is an internal *negotiation*, surfaced in the `{thought}` stream. Ten static traits = a detailed cardboard cutout; two drives that genuinely oppose = a person. The drama and the realism are the same thing: which lever wins *this* time, given the state.
- **State.** The same person acts differently by moment — energy, mood, relationship flux, stress shift which lever dominates. Static levers read robotic; stateful levers read alive.

## More levers ≠ more real (the sweet spot)
Past a point, adding levers *hurts*: authoring burden explodes, the sim can't weigh 20 competing drives coherently, and readers infer rich personhood from a *few* well-chosen, consistently-applied traits (over-specification reads as mechanical). Aim for a **small set of high-leverage, conflicting, stateful levers**, depth-by-layer (full for protagonists, few for bystanders — the layer system). **Consistency of application beats quantity.**

## The realism test (falsifiable)
A character is real enough iff, faced with a genuine dilemma, their choice is **non-obvious but in-retrospect-inevitable** — it traces to their levers without being predictable from any single one.
- *Predictable from one trait* → too few / non-conflicting levers (cardboard).
- *Arbitrary or inconsistent* → levers not applied coherently.
- *Surprising yet earned* → real.
This is exactly the probe (`probe-plan.md`): Mira's want (save her mother) vs her identity (never abandon the sick), resolved by circumstance → a choice that is *hers*, not predetermined. The probe already tests lever-realism — not a coincidence; it *is* the criterion.

## Prior-art schema — what the maker actually tracked (grounded)
A prior author-mode project (a novelist agent that wrote chapters) carried a full per-chapter
character-state record. **The list below is the record** — it is restated here in full so this
document is self-contained; nothing outside this repo needs to be read to use it. That project
tracked:
- **Identity:** name, layer (1–5 importance)
- **Embodied state:** location, physical_state, injuries, possessions
- **Psych state:** emotional_state, psychological_zone (hyper/optimal/hypo), allostatic_load, blocked/accessible_emotions, coping_status
- **Arc:** arc_milestone, arc_ap (authenticity points)
- **Knowledge:** `knowledge[]` + `secrets_unknown[]` ← the injection model, in the schema
- **Relationships:** per-target {trust, affinity, power_dynamic, history}
- **Voice:** dialogue_profile (vocab tier, sentence structure, power markers, verbal tics, rhythm, metaphor prefs, authenticity markers)
- **Interiority:** cognitive_style, emotional_accessibility, sensory_dominance, metaphor_category, introspection_depth, memory_vividness
- **Deception (hidden in WRITING mode):** secret_motivations, hidden_identity, transformation_arc, sentience_level, deception_flags

Per-chapter deltas tracked separately (`CharacterChange`: emotional_shift, knowledge_gained/lost, arc_movement, relationship_changes) → the state half of realism, confirmed. A second author-mode system tracked the same dimensions split across specialist producers — a persona profile with psychometrics, a biographical state, and a clinical psych profile, plus a character-seed authoring input and an alias record for hidden identities. The split is the point: authoring input, stable profile, and mutable state are three different artifacts.

## Reuse vs build (delta to this lever set)
- **Reuse wholesale:** knowledge+secrets (vault), relationships (trust/affinity/power/history), voice, interiority, rich psych-state (zone/allostatic/coping), deception, layer system, stateful + delta tracking. Prior art is strong on STATE.
- **BUILD (the gaps):**
  - **Goals / values / fears as *structured, opposable* fields** — prior art leaves these in free-text personality/backstory (Scribe's profile has goals+fears+core_wound, but not values, and not as conflicting drives). The realism engine needs them first-class + queryable.
  - **Skills** — absent in both (added for the relevancy-gate checks).
  - **Connection energy** — absent (they have allostatic_load = psych energy, adjacent but not the traversal-cost energy).

## Grounding against personhood science — do our levers feel real to an observer?
Checked the lever set against the established frameworks (McAdams' levels of personality; Big Five; thin-slicing person-perception). Verdict: **we're rich on Level 2 and thin on Levels 1 and 3 — and the thin ones are exactly what an outside observer reads.**

**McAdams' three levels (the standard "whole person" model):**
- **Level 1 — dispositional traits** (Big Five / OCEAN): broad, *stable* consistencies in *how* someone behaves across situations. **← we are THIN here.**
- **Level 2 — characteristic adaptations**: goals, values, beliefs, concerns, coping, social roles — contextual. **← we are RICH here** (our vault, goals, values, fears, relationships, coping/psych-state *are* Level 2).
- **Level 3 — narrative identity**: the internalized, evolving life-story that gives a life meaning/individuality. **← we LACK this** (we have backstory + arc-points, not the self-story the person acts from and revises).

**The observer lens (thin-slicing / zero-acquaintance):** strangers form *accurate* personality judgments from *seconds* of behavior — primarily from **nonverbal cues + appearance** — and the trait they read most easily is **Extraversion, then Conscientiousness, then Agreeableness** (all Level 1). So an outside observer reads **Level 1 first and fastest, off the observable nonverbal/physical surface** — the two layers we're thinnest on.

### The gaps, prioritized (grounded)
1. **Dispositional traits (Big Five) — highest value for observer-realism.** The layer observers infer in seconds, and the *behavioral-style through-line* that keeps a character recognizable across scenes (same goal, different pursuit: methodical vs impulsive = Conscientiousness; bold vs reserved = Extraversion). Add 5 traits as a **stable style layer that modulates HOW the Level-2 levers express** — small + integrated (per "more levers ≠ more real"), feeding the **decision engine** (roadmap #1).
2. **Observable surface — nonverbal + physical.** Body language, mannerisms, posture, expressions, appearance, habitual routines. The *channel* traits express through and the *cue* observers read; we emit verbal voice + actions but are thin on nonverbal/physical signal. Reuse prior-art **A4 Bio / `physical_state`**; extend with mannerisms/habits. (Surfaces in the recorded **actions**, so it's read by the observer/reader.)
3. **Narrative identity (Level 3) — the depth/meaning layer.** The evolving self-story of who they are. The soul of literary character — and *what the arc engine operates on* (an arc = narrative identity changing). Ties to roadmap #3 (arc/transformation).
4. *(minor)* **Demographic / social identity** — age, role, class, culture — shapes behavior and gives observers predictive priors. We have "station" for knowledge; widen to a social-identity layer.

**Net:** we built a strong *Level-2 engine* (why they act). To feel real **to an outside observer** it needs **Level-1 traits** (read first) expressed through an **observable nonverbal/physical surface**; for depth it needs **Level-3 narrative identity**. Traits + surface = realism-to-an-observer; narrative identity = realism-of-depth.

## Character roadmap — what's next (priority order)
We've built every INPUT and OUTPUT around the character's decision — senses (relevancy gate), memory (vault), social read (relationships), state (energy/psych), voice (narration), the recorded `{thought, action}`. **The empty center is the decision itself.**
1. **Motivation + decision engine — NEXT (the empty center AND the realism engine).** Structured opposable drives (goals: priority + satisfaction condition; values: what they score + weight; fears/wounds: trigger + avoidance), first-class not free-text. Plus the decision procedure: given (placed circumstance + injected vault slice + drives + relationships + state) → *weigh competing drives* → recorded `{thought, action}`, **beat-blind**. This is exactly what the **probe** tests → the direct path to the de-risk gate.
2. **Character creation / authoring** — the per-character generation pass (Phase B in `design.md`): **position → formative environment → baseline → individuation.** Position (place/class/family/niche, drawn from the world's present systems) → formative environment (what raises them) → baseline seeding (formative world → traits + relationship-priors + values-weighting + starting vault with provenance; *the world authors the baseline* — e.g. streets → low out-group trust, see `world-model.md` formative coupling) → individuation (personal backstory + perturbation). **Principals are authored backward** (start from the character the story needs → find the position/history that yields them) and **validated forward** (the world must plausibly produce them, or adjust world/character). Hand-made fixtures suffice for the probe, so the *engine* follows — but the *workflow* is locked now.
3. **Arc / transformation engine** — how *core* levers change over the book (a coward becomes brave; a value erodes), driven by accumulated experience + pivotal events. Distinct from momentary state-change (already designed); this is deep growth, the novel's through-line. Builds on the decision engine.

**Critical path:** decision engine (1) → run the probe (de-risk gate) → then creation (2) + arc (3).

## Character models (archetypes) — controlled variation for creation + testing
**Decision (the author): build a small set of "models" — preset, *sparse* weight-diffs — and assign them.** Strong: it gives *constants we control* (a few tuned profiles) while two characters on different models react differently. This is the MVP for **creation (roadmap #2)**.

**Separate the character into CONTENT and a WEIGHT-MODEL.**
- **Content** = who they are descriptively: traits, backstory, vault, relationships.
- **Model** = the *weight / priority structure* — how strongly each factor pulls and, crucially, **what wins when drives conflict** (loyalty vs fear, duty vs desire). This is the divergence dial.

The model is **separable from content**: two characters with the *same* personality but *different* models, facing the *same* event, **diverge — because the conflict resolves under a different priority structure.** (Real: two people both "loyal and brave" still differ in which wins when loyalty and fear collide — that hierarchy *is* the model.) Define ~6 models; running the same content + same event under model 2 vs model 5 yields two coherent, attributable, different outcomes.

### A model is a SPARSE TRANSFORM over the weight-bearing layers
A model needn't touch all five weight-bearing layers (`decision-engine.md` → 1·3·5·7·10). **Each model picks a subset and biases only those, leaving the rest at the character's baseline** — Model A re-weights only 3 (drive priority); Model B only 5+7 (relationship trust + state default); Model C only 10 (conflict resolution). Unset layers pass through unchanged. This is what yields a *spread* of emergent behavior from one understood constant — and it's **attributable**: divergence traces to the exact layers the model touched.

**Bias, not set (transform, not absolute value).** A model is a reusable function applied *to* content, not content itself — else "same content + different model" is incoherent (an absolute-set model overwrites the content it's meant to apply to). So a model touching 5 is *"trust ×0.6 toward strangers,"* not *"trust = 0.3"*; touching 3 is *"sharpen the top goal's priority,"* not *"goal = survive."* The specific facts (who they know, history, backstory, trait means) stay **content**; the model **re-weights how that content translates to behavior.** Matters most for 1 (traits) and 5 (relationships), which blur hardest into content — there, bias the lean, never replace the value. Worth (Layer 2) moves only *through* the model's **Layer-10 component** (10 administers the worth-weighting) — a "loyalty-over-fairness" archetype is a 10-diff, never a direct edit of Layer 2.

**Curate few + single-axis before composing.** Freely *stacking* diffs (Hardened + Driven + Fatalist) re-introduces the unpredictable interactions that "a constant we understand" exists to prevent. Start with a small curated set of **low-axis, named, non-stacked** models (each touches 1–2 layers, hand-tuned, understood); add composition only after the single-axis ones are calibrated. **Understandability first, combinatorial spread second.**

**Falsifiable by construction:** two copies of one character under two models differing on *exactly one layer*, same circumstance → coherent, attributable divergence = the mechanism works. A clean second probe after the core decision probe.

*(Naming: "model" here = the whole sparse archetype-diff; "The Model" in `character-anatomy.md` Layer 10 = the resolver-weight alone. Candidate cleanup: rename Layer 10 → "the Resolver" to free the word "model" for the archetype.)*

**It stays non-gamey (per `decision-engine.md`):** a model is NOT a weighted-sum that computes the answer — it's a named priority/bias configuration *injected* into the decision context. The LLM still resolves; different models just frame the conflict differently → divergent but coherent choices. Controllable knob + narrative resolution.

Same-*model* characters still read distinct because **content individuates** them (different backstory/vault/relationships/lived-experience + distribution sampling). Model = the priority dial; content + life = the individual.

**Assignment — split by role (don't let pure-random touch the load-bearing cast):**
- **Random (or controlled-random for coverage):** engine testing + minor/background NPCs — fast variety.
- **Deliberately curated:** the major cast. A novel needs a *designed ensemble* (contrasts, complementarity, the loyal one set up to be betrayed) — not a bag of strangers. The director composes principals for dramatic fit; random would waste them.

**Perturb on assignment (avoid clones / archetype-flattening):** jitter the model's means per character (add noise) so same-model instances aren't identical — controlled variation *within* an archetype family. With distribution-sampling + the tails (out-of-character moments) + heavy individuation, this keeps "models" from reading as flat types.

**The testing payoff (the constants-we-control gem):**
- **Same model, different situation** → isolates the *situation* effect.
- **Different model, same situation** → isolates the *model* effect.
A clean controlled-experiment design for the probe + calibration — assign by hand for those, random for scale.

## What's next: the world — NOW the probe's prerequisite (`world-model.md`)
We've gone deep on the *character* half; the **world** is the comparable other half. **It's now the gate before the probe** — the probe moves a character via *circumstance*, circumstance is world-state, and only a world with real constraints can plausibly *deny* a lever (without that, the probe can't surface the honest "no lever works" case → hollow). Seeded in `world-model.md`. The principle:
- **The world is the other half of the loop.** Characters act ON the world; the world's state pushes BACK as circumstance. A static set-dressing world starves the biographies — they go inert with nothing real to push against. Realism needs a world with real levers too.
- **Same architecture as a character:** ground-truth **bible** (laws, economy, religion, geography, factions, history — Scribe's W1–W7) + an evolving **world-state ledger** + **dynamics** (how it changes on its own and reacts to character action). Detail it **where it's levered on** (a source of circumstance and consequence); resolve consequences **lazily / on-demand** (don't pre-simulate the whole economy); author the hinges — same frame-problem discipline as the vault.
- So "design the world" isn't a new paradigm — it's *state + lazy-resolution + levers + ledger* applied to the world instead of the person, coupled to the characters through action and circumstance. (Seeded now: `world-model.md`.)

## THE THREE LAYERS — base, genotype, experience (NORMATIVE, 2026-08-31)

**The author's statement of the model, which this section exists to record:**

> *"The base sets their starting point. The genotype is their bias, their experiences shape who they are now.*
>
> *A base happy person who was a slave and beaten for years can be a very angry and hostile person today. Because their circumstances created the conditions for so many negative vectors to apply."*

Three layers, three jobs, and each must keep doing only its own:

| layer | what it is | who writes it | lifetime |
|---|---|---|---|
| **BASE** | where the person STARTED — the authored temperament means, relationship priors, wound intensities | the author, once | never moves; preserved even as the effective value changes |
| **GENOTYPE** | their BIAS — per-primary gains and the global sensitivity allele; how hard the same event lands on this person | the author or a seeded draw, once | fixed for life |
| **EXPERIENCE** | who they are NOW — the accumulated vectors of what happened to them | the engine, per durable event | additive over the base, in both directions |

### The four laws

1. **The base is preserved, never overwritten.** The effective value is `base + experience`; both must remain readable. A fold that writes the sum over the base destroys the only record of who the author wrote, and no later code can tell an authored trait from an accumulated one. (`arc.apply` did exactly this until 2026-08-31; `_authored_mean` and `_authored_regard` now hold the base, and `_authored_intensity` does the same for a wound.)

2. **Preserving the base is NOT flooring at it.** Experience may take the effective value BELOW where the person started. A happy man's joy can be destroyed; that is the point of the model. Any mechanism that can only accumulate upward is not implementing this.

3. **The genotype biases the write, at every tier.** If genotype is the bias, then an anger-prone person must accumulate RAGE faster than a placid one from the same beating. A durable write that ignores the per-primary gains applies the same experience identically to two different people, which is the tag this whole design exists to avoid.

4. **One pricing table, applied at every timescale.** What an event does to a person is a property of the event and the person, not of how long the effect lasts. `state._DIM_TO_PRIMARY` is that table: it prices all eight primaries and carries negatives. A second, thinner table for durable writes is a duplicate that will drift — and has.

### The measurement that made this normative

A base-happy character (PLAY 0.80, CARE 0.75, RAGE 0.15, FEAR 0.20) was run through **80 durable diffs** of beatings (`threat` 0.85 / `social_violation` 0.70) and degradation (`social_violation` 0.90 / `threat` 0.40) — a life of it.

| primary | authored | what the engine produced | what one pricing table produces |
|---|---|---|---|
| RAGE | 0.15 | **0.150 — never moves** | 1.000 |
| DISGUST | 0.20 | **0.200 — never moves** | 0.926 |
| PLAY | 0.80 | **0.800 — never moves** | 0.118 |
| FEAR | 0.20 | 1.000 *(saturated)* | 0.945 |
| CARE | 0.75 | 0.750 | 0.750 |

The engine produced **a maximally terrified man who was exactly as playful, as loving and as un-angry as the day he was born** — and once FEAR reached 1.000 he became incapable of further change of any kind. Forty more years moved no number.

The right-hand column is the same life priced with the table the CURRENT tier already uses. It is the character the author described: furious, contemptuous, frightened, his joy nearly gone — **and still able to love**, because nothing in the table maps threat or degradation onto CARE. That last detail was not designed; it fell out of a table that was already there, and it is the strongest argument for having only one.

### What violates the model today

- `arc.assess` writes **four** primaries (CARE, FEAR, SEEKING, PANIC_GRIEF) and **every one of its seven writes is positive** — RAGE, DISGUST, PLAY and LUST have no durable path at all. Law 2 and law 4.
- `arc.assess` scales by `_BASE_STEP x impact` and resilience; the genotype gains never enter the durable write. Law 3.
- `_regard` is the only connection-shaped term and is clamped to `[0,1]` with the comment "affinity lifts, never lowers", so a bond can recover impact lost to a bigotry but can never amplify it. A stranger's death and a beloved's death produce the same magnitude.
- Nothing holds a per-target per-primary vector, so the MICRO half of experience — what this person specifically does to you — has no home. `bonds` is per-target on four relationship axes; `targets` stores aboutness, not magnitude.

Law 1 holds everywhere as of 2026-08-31. Laws 2, 3 and 4 hold in the current tier and fail in the arc.

## DECAY AND CONNECTION (NORMATIVE, 2026-08-31)

**Every decay in this engine is already the same equation.** Nothing new needs inventing; the
tiers differ only in what they rest at, how fast, and on which clock.

```
value  <-  rest + (value - rest) x retention ^ elapsed
```

| what fades | rests at | how fast | clock |
|---|---|---|---|
| the feeling of the moment | the character's temperament | fast — a few beats | per beat |
| a relationship edge | the resting prior | slow | declared time |
| a wound | the wound's own permanence floor | very slow | declared time |
| a temperament mean | the AUTHORED base (`_authored_mean`) | barely at all | declared time |
| a feeling toward one person | **zero** | per primary, see below | declared time |

Two clocks and no third: per-BEAT for the moment's feeling, and the DIRECTOR'S DECLARED elapsed for
everything else. A single conversation must not erode a friendship, which is why the slow tiers do
not tick per beat.

### Feelings toward a person fade at different rates

Ordered as `state._DECAY_RATE` already orders the primaries, because the fast/slow ordering is a
property of the emotion system and not of which tier is asking:

  fear of someone fades FASTEST · then playfulness, which needs re-supply · then seeking, rage ·
  then lust, care · **contempt and grief fade SLOWEST**

That ordering does dramaturgy by itself. Someone wrongs you and you do not see them for a season:
the fear goes, the anger cools, the warmth you had drains away — and what is left standing is the
contempt. You have stopped being angry at them and started simply not respecting them. **That is
estrangement, produced by arithmetic with no further events.**

### CONNECTION SLOWS DECAY, and it is the same term that amplifies impact

The author's rule: the stronger the bond, the larger the impact — **and the longer it lasts.**
One quantity, two jobs, no second store:

```
retention_effective  =  retention + (1 - retention) x k x connection
```

Connection takes a bounded fraction of the remaining headroom toward 1.0 and can never reach it, so
no feeling becomes permanent by this route. At `k = 0.5` and full connection a feeling lasts roughly
TWICE as long: anger toward a stranger halving in about 14 units of story time, toward someone
beloved in about 27. `k` is CALIBRATION and needs a probe; the bounded-headroom FORM is what matters.

Three consequences worth stating, because each is a design claim and not an accident:

1. **A beloved's betrayal both cuts deeper and lasts longer.** The same connection term amplifies
   the magnitude and slows the fade. That is the archetype, and it falls out of applying one number
   in two places rather than being authored anywhere.
2. **Connection itself needs no decay.** It is READ LIVE off the relationship edge, which already
   drifts. When a friendship cools, both the amplification and the slowed fade cool with it —
   for free, and without a fifth store to keep in sync.
3. **Drifting apart accelerates forgetting.** As the edge relaxes toward its prior, feelings toward
   that person start fading faster. The mechanism describes exactly what it should: you get over
   people you have already grown away from.

### Connection needs three things (NORMATIVE)

The author's requirement: **a way to increase, a way to decrease, and a relevancy floor — low
connections get no modifiers at all.** Two of the three already exist, because connection is a READ
off the relationship edge rather than a store of its own, and so inherits everything that moves it.

**INCREASE** — `bonds.observe` raises affinity, trust and respect on a witnessed act, learning rate
`_ALPHA_POS` 0.12.

**DECREASE** — three distinct ways, which is more than the design needed to specify:
  · `_ALPHA_NEG` 0.30 — a bond leaves 2.5x faster than it arrives. Trust arrives on foot.
  · `bonds.drift` relaxes an untouched edge toward its resting prior over declared time.
  · **the cliff** — `_CLIFF_SEVERITY` 0.80 on an act of `_CLIFF_RELEVANCE` 0.60 collapses trust to
    `_CLIFF_FLOOR` 0.15 outright. Erosion AND rupture: a bond can fall off, not only wear down.

**THE RELEVANCY FLOOR — the part that does not exist yet, and must.**

Below a floor, connection contributes NOTHING: the magnitude multiplier is exactly 1.0 and the
retention is exactly its unmodified rate. Not a value that happens to be small — a DEAD ZONE where
the mechanism does not participate.

A HARD threshold, not a soft ramp, and the reason is the purpose. A book carries dozens of people
and only a handful should be moving anyone's numbers. Without a floor, every passing acquaintance at
affinity 0.52 earns a sliver of amplification and a sliver of slowed decay: every number in the run
becomes slightly different for no dramatic reason, the audit trail fills with rows that move
nothing a reader could notice, and any probe of the real effect is buried in that noise. The floor
buys SILENCE, and a ramp does not.

The precedent is `arc._ARC_THRESHOLD` 0.18 — below it no durable diff is written at all, and "most
events stay transient" is the stated intent. This is the same shape: most people are not close
enough to change how anything lands.

Stated so a reader can judge it rather than a number they cannot: **someone must be more than a
passing acquaintance before their presence changes any arithmetic at all.** The threshold value is
CALIBRATION and needs a probe; the dead-zone FORM is the normative part.

One consequence worth stating, because it is a feature: the floor means connection is INACTIVE for
most of a cast, most of the time. If a run shows connection modifying most of its beats, the floor
is set too low, and that is a measurable failure rather than a matter of taste.
