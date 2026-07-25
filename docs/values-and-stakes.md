# What's being weighed — the menu of "worth" (the model weights this)
Before the weighting (`decision-engine.md`), define WHAT carries worth to a person. Grounded in the human values/needs/morals literatures. **The "model" is a person's individualized weighting over this menu — what's worth more to them** (Reiss's finding: motivation is an individual profile of desire-strengths over a shared menu — exactly the model concept).

## The menu (four tiers)
**1. Needs — the universal substrate (everyone has these; the model weights how strongly).**
- *Survival / body* (Maslow physiological + safety): life, safety, freedom from pain, health, material security. The floor — usually outweighs the rest *until met*, but people sacrifice it for higher stakes (the dramatic gold).
- *Psychological needs* (Self-Determination Theory): **autonomy** (choice/self-direction), **competence** (mastery), **relatedness** (connection/belonging). Innate, universal.

**2. Values — the worth-orientation (Schwartz's 10, the value spine).** self-direction, stimulation, hedonism, achievement, power, security, conformity, tradition, benevolence, universalism — arranged on **two conflict axes**: openness-to-change ↔ conservation, and self-enhancement ↔ self-transcendence. *Adjacent values cohere; opposite values conflict.* The map already encodes where the trade-offs are.

**3. Morals — the ethical weighting (Moral Foundations, Haidt's 6).** care/harm, fairness/cheating, loyalty/betrayal, authority/subversion, sanctity/degradation, liberty/oppression. *"Moral taste buds" — people weight them differently*, which is literally the model: a loyalty-weighted person and a fairness-weighted person clash even when both are "good." Adds the sacred/loyalty/authority axes Schwartz's values don't fully cover.

**4. Concrete stakes — the instantiated, in-scene worth.** The abstract tiers are *priors*; a scene puts concrete things on the table:
- *Attachments* — the specific people/things/places they love or are bound to (their child, their honor, a promise, a homeland).
- *Self-image / identity* (Level 3) — maintaining their narrative of who they are ("someone who never abandons the sick"). People sacrifice much to preserve it.
- *Situational goals* — the immediate objectives in play.

## The conflict structure IS the drama (not arbitrary)
Trade-offs aren't random — they're the **built-in tensions** of the menu: survival vs principle (Maslow floor vs higher value); self-enhancement vs self-transcendence and openness vs conservation (Schwartz axes); care vs loyalty, liberty vs authority (Moral Foundations); autonomy vs relatedness (SDT). A decision is *forced* when a situation pits two of these against each other; **the model says which wins for this person.** Two good people who weight care-vs-loyalty differently → tragic, principled conflict.

## Abstract priors → concrete stakes (how it's used)
The model sets the **priors** (this person's general weighting over needs/values/morals); the **situation supplies the concrete stakes** (this child, this danger, this promise); the decision **weighs the concrete instantiations under the priors.** Author the abstract weighting once (the model); each scene instantiates it.

## From worth to harm — computing an event's severity (no per-item authoring)
The menu does **double duty**: values = the menu *held*; harm = the menu *threatened or violated*. An event's severity (`state-engine.md`'s `severity(e)`) is **never an authored per-object number** — that's the "a system per action, impossible" trap. It's **computed** as the event's harm-vector resolved against the perceiver — the same generative move as emotions (bounded basis, not per-instance). An event carries a **structural harm-vector** (which menu-items it hits), not a magnitude:

- **Physical threats** (knife, gun, fall, fire) hit the **survival/body** need (tier 1). Magnitude = **physical affordances** — `damage × reliability × range × speed`, properties the world's object/physics model defines (a gun out-ranges a knife; a knife out-damages a fist; a knife at 1 m can out-threaten a gun at 50 m). Severity = affordance × the near-universal survival-weight × the perceiver's **threat-read skill**. **Objective-ish** — a new weapon's severity falls out of its stats, unauthored.
- **Social / moral acts** (lying, cheating, betrayal, insult) **violate a Moral Foundation** — and Haidt's foundations *are* a violation taxonomy (care/**harm**, fairness/**cheating**, loyalty/**betrayal**, sanctity/**degradation**): "cheating" is a fairness+loyalty violation *by definition*, "lying" a care+fairness violation — a **structural tag, no authoring**. Magnitude = the violated foundation × **the perceiver's weight on it** (the model) × the **relationship context** (`relationships.md` — betrayal by a sworn intimate ≫ a stranger's white lie). **Subjective / relational.**

**The elegance — one menu, so your values ARE your vulnerabilities.** Because harm is the menu-threatened and value is the menu-held, the *same* weight does both jobs: a loyalty-weighted person both *prizes* loyalty and is *devastated* by betrayal; a fairness-weighted person rages at cheating. **Harm-sourcing is free** from the value-sourcing already done (`baseline-generation.md`) — no separate harm table. A betrayal's severity is literally `loyalty-weight × prior-trust × violation-size`, all three already in the engine. Knife, gun, cheating, lying, and the next unanticipated thing all get severity from the **bounded basis** (the menu + the affordance dimensions) — "design the system, not the instances," applied to stakes.

## Don't quadruple-count — one spine + lenses
The four taxonomies overlap (benevolence ≈ care ≈ relatedness, from three angles). Practical: **Schwartz's 10 = the value spine; Moral Foundations = the ethics lens (adds loyalty/authority/sanctity); SDT + survival = the needs substrate; concrete stakes = the in-scene layer.** Track the spine + concrete for everyone; add moral/needs granularity for principals (fine-grain + sparse-authoring + salient-subset, per the trait decision).

## Net
"What's worth more to this person" = their weighting across **needs** (survival + autonomy/competence/relatedness), **values** (Schwartz 10), **morals** (Moral Foundations 6), and **concrete stakes** (attachments, self-image, goals). The **model = that weighting**; the **conflicts = the menu's built-in tensions**; the **decision = which stake wins when a scene forces the trade-off.** This is the drives/values schema the decision engine resolves.

## Worked example — two identical people, a son dies (what must differ)
"Trusting, loving, honest" fixes only *interpersonal style* (≈ Agreeableness + Honesty-Humility). It says nothing about the dimensions that govern a *loss response* — so two people identical on those three can react oppositely, because the loss-governing weights were never constrained. A son's death activates a *specific subset* of the menu; the divergence lives in the weights on that subset:
- **What the son represented** in their hierarchy: love-anchor (→ meaning collapse) vs legacy/future (→ lost tomorrow) vs proof-of-self-as-protector (→ identity shatter).
- **Moral construal of the death:** care → pure grief; fairness/justice → "someone is accountable," demand/vengeance; sanctity/authority → ritual, "God's will," acceptance; loyalty → turn to (or against) the family.
- **Locus of control / agency** (NEW — below): internal → self-blame + "I must act/fix/prevent"; external → fate/acceptance/surrender.
- **Coping / regulation** (psych-state, already modeled): approach/express (breaks down, reaches out) vs avoid/suppress (goes cold, functional, buries it).
- **Self-image centrality of parenthood:** identity shatters ("who am I if I couldn't protect him?") vs grief-but-self-intact.
- **Security ↔ openness** under a shattered world: cling to order/routine/ritual vs existential search.
- **Self-preservation ↔ self-transcendence** channeling: collapse inward (depression) vs turn grief outward (a cause, a foundation, advocacy).

Two concrete divergences from the *same* loving/honest pair, three weights flipped:
- **A** — care + internal-locus + approach-coping + parenthood-central: open collapse, blames herself, reaches for others, identity in crisis.
- **B** — justice + external-blame + avoidant-coping + legacy-framing: goes cold, suppresses, hunts who's responsible, channels grief into accountability / a monument.

**Design lesson:** the model is NOT the surface traits — it's the weighting across the dimensions the *situation* makes relevant. The son's death activates the loss subset; the divergence lives there. So the menu must be rich enough to contain the loss-governing dimensions, and the relevance gate surfaces the subset the event activates.

## Menu addition: Locus of control / agency-attribution
The example forces a dimension Schwartz/MFT/SDT don't cover (Rotter's construct): **how a person explains events and whether they act on or accept the world** — internal vs external locus, high vs low agency. It powerfully shapes the response to anything that happens *to* them (self-blame + action vs fate + acceptance). Add it as an attributional lever alongside needs/values/morals.
