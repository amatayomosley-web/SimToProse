# Character anatomy — the complete picture (what forms a person)
Every factor that makes a character, in layers. Each layer's deep-dive is its own doc; this is the index + completeness check. A character exists in **three views** (ground truth / self-image / others-see — `self-and-perception.md`); the stable factors are **distributions, not points** (mean + variability — `trait-theory.md`); the whole thing **changes over time** (arc + state + belief accrual + relationship updates).

## 1. DISPOSITION — the stable "how" (traits; what observers read first)
**HEXACO**, fine-grain (domain → aspect → facet), each a **distribution (mean + variability)**: Honesty-Humility · Emotionality · eXtraversion · Agreeableness · Conscientiousness · Openness. → the behavioral *style* everything else expresses through. (`trait-theory.md`)

## 2. WORTH — what's at stake (the motivational core; the model weights this)
- **Needs:** survival/body (life, safety, health, security) + autonomy, competence, relatedness (SDT).
- **Values:** Schwartz 10 (openness↔conservation, self-enhancement↔self-transcendence).
- **Morals:** Moral Foundations 6 (care, fairness, loyalty, authority, sanctity, liberty). (`values-and-stakes.md`)

## 3. DRIVES & ORIENTATION — how they engage the world
- **Goals** (current objectives + priority) · **Fears / wounds** (what they protect/avoid — the friction engine) · **Locus of control / agency** (internal↔external; act vs accept) · **Coping / regulation** (approach↔avoid, express↔suppress). (`values-and-stakes.md`, `decision-engine.md`)

## 4. MIND — the epistemic layer
- **Beliefs (the vault)** — what they hold true (can be false), with provenance + time (`knowledge-model.md`).
- **Knowledge boundaries** — what they know vs don't (secrets-unknown).
- **Skills / competencies** — which checks they can pass (`relevancy-gate.md`).
- **Cognitive / interiority style** — how they think (cognitive style, sensory dominance, metaphor, introspection depth, memory vividness).
- **Connection energy** — capacity to make mental connections; stat + depleting state (`relevancy-gate.md`).

## 5. RELATIONSHIPS — the social layer
Per-perceiver belief edges to each known person: **trust · affinity · respect · debt · history** — beliefs (can be wrong), updated by prediction-error + negativity bias. (`relationships.md`)

## 6. IDENTITY & SELF — the meaning layer (Level 3)
- **Self-image / self-narrative** — who they *think* they are (diverges from truth; villains aren't villains to themselves). **The decision engine runs from this.** (`self-and-perception.md`)
- **Self-image centrality** — what's load-bearing to identity (parenthood, vocation, honor).
- **Backstory / formative wounds** — the past beneath the surface.
- **Arc** — how the core is changing through the book (transformation engine — roadmap #3).

## 7. STATE — the dynamic now (varies moment to moment)
- **Emotional / arousal state** — psych-zone (hyper/optimal/hypo) + intensity, allostatic load.
- **Energy** — current level (depletes/regenerates).
- **Mood + active goals + current beliefs** — the time-sliced present.
- **Physical state** — location, health, injuries, possessions.

## 8. SURFACE — what others actually read (the expression layer)
**Voice / dialogue** (vocabulary, rhythm, verbal tics, power markers — `narration.md`) · **Body / nonverbal** (posture, mannerisms, expressions, somatic tells) · **Appearance / physicality** · **Habits / routines.** (Observers thin-slice these in seconds — `character-model.md` §grounding.)

## 9. POSITION — demographic / social (the priors others read through)
Age · gender · class · occupation/role · culture · era · **station** (also gates common-knowledge in the vault).

## 10. THE MODEL — the weighting (cross-cutting resolver)
The **relative worth across all the above** — the priority structure, *what wins under conflict.* Tracked numerically, **resolved narratively** (injected as bias; the LLM weighs; never a code-side sum). The divergence dial: same content + different model → different behavior. (`decision-engine.md`, `character-model.md` §models)

---
## How the layers play together
**Disposition** sets the style; **worth + drives** set what's at stake; the **model** decides what wins when stakes collide; the **mind** bounds what they can know and connect; **relationships** weight whom they trust; **identity** is the self they act from; **state** shifts the moment's effective weights; the **surface** is what others read; **position** sets everyone's priors — all in three views (truth/self/others), all distributions not points, all changing over time.

## Designed vs to-build
- **Designed (deep-dives exist):** vault/knowledge, relevancy/energy, relationships, recording, narration, traits, values/stakes, self-and-perception, the weighting model.
- **To build (roadmap):** **decision engine** (#1 — resolve it all into `{thought, action}`); **creation** (#2 — author/seed all this); **arc/transformation** (#3); and the **surface/nonverbal + demographics** layers (flagged additions, lighter).

## Why "trusting, loving, honest" wasn't a targeted test
Those three pin **two facets of Layer 1** (Agreeableness + Honesty-Humility) and leave Layers 2, 3, 6, 7, 10 — values, morals, locus, coping, self-image, the model — entirely free. That's why two such people can diverge wildly: the test fixed <5% of the picture.
