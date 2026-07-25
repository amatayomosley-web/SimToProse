# Trait theory — OCEAN's structure + related models (research for the "add traits" decision)
Grounded research on the dispositional-trait layer (Level 1 from `character-model.md`). For discussion → then a tracking decision.

## The Big Five hierarchy (the structure *inside* OCEAN)
Four levels (DeYoung):
- **2 metatraits:** **Plasticity** (Extraversion + Openness — explore/integrate new info) · **Stability** (Agreeableness + Conscientiousness + Emotional-Stability — maintain goal-directed functioning). No general factor above.
- **5 domains (OCEAN):** Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.
- **10 aspects (2 per domain):** O→Openness/Intellect · C→Industriousness/Orderliness · E→Enthusiasm/Assertiveness · A→Compassion/Politeness · N→Volatility/Withdrawal. The useful mid-level — distinguishes two "high-X" people (warm-enthusiastic vs dominant-assertive).
- **30 facets (6 per domain, NEO-PI-R):** finest grain.

## HEXACO — add a 6th factor (recommended)
Lee & Ashton: adds **Honesty-Humility (H)** = fairness, sincerity, modesty, lack of greed/manipulation/entitlement. Big Five buries this in Agreeableness; HEXACO breaks it out. H predicts unethical/manipulative/deceptive vs prosocial behavior **over and above** Big Five. (Also: HEXACO routes quick-temper/anger to low-A not N; Emotionality ≈ N minus anger plus attachment/sentimentality.)
**Why it matters for us:** moral character (integrity ↔ manipulation) is central to drama and Big Five hides it. Recommend HEXACO's 6 — H, E, X, A, C, O — over pure Big Five.

## Dark Triad / Tetrad — NOT a separate system
Machiavellianism (strategic manipulation), narcissism (grandiosity, low empathy), psychopathy (callous, impulsive) + sadism (pleasure in others' pain) = Tetrad. Subclinical. A single core "**D factor**" = maximize own desires at others' expense — and it maps onto **low Honesty-Humility** (+ low A/E). So villains = the **low-H corner of HEXACO**, with named presets (Mach / narcissist / psychopath / sadist) as **antagonist overlays** on the trait space. No bolt-on dark system — a region + presets.

## Whole Trait Theory (Fleeson) — how to TRACK + USE traits
A trait is **not a fixed scalar — it's a density distribution of states** (a dynamic MEAN + VARIABILITY). A high-extraversion person is *usually-but-not-always* outgoing; the trait = the average + spread of how they actually behave. Two parts: **descriptive** (the distribution) + **explanatory** (the processes — goals, interpretations, situation — that produce each state).
**Why this is the key for us:** it's the bridge between Level 1 (traits) and our existing **state** layer (energy/mood/relevancy). The trait sets the **distribution** the character's momentary behavior samples from; **state + situation + relationships shift the sample** within it. And the *explanatory* side = our Level-2 levers (goals/values/fears). So traits don't replace our levers — the trait is the *style-distribution*; our levers are what produce the specific state within it. Whole-trait theory unifies the two.

## Recommendation (for the discussion → then track)
- **Adopt HEXACO (6):** H, E, X, A, C, O.
- **Track at domain (6) + the 10-aspect level for major characters**; 30 facets only if ever needed for a protagonist (sweet-spot: small + integrated). Metatraits = a *derived* summary view, not separately authored.
- **Store each dimension as a distribution (mean + variability), not a fixed value** (whole-trait). Momentary expression = a sample modulated by state/situation/relationships → feeds the **decision engine** (sets how the Level-2 drives express).
- **Villains = low-H trait profiles + a named dark-overlay**, not a separate system.
- Scale: bipolar continuum per dimension (−1..+1 or 0–100 percentile) for the mean + a variability param. Authorable + queryable.

Open for the discussion: how variability is set/used; which dark presets to predefine; HEXACO Emotionality vs Big-Five Neuroticism framing.

## Decision: go fine-grain — and how "no one is one way" is reflected
**Decision (William): track to the finest grain — facets, not just domains/aspects.** This stays coherent because facets are a *structured* refinement (facet → aspect → domain → metatrait), not unstructured lever-sprawl — so the earlier "more levers ≠ more real" caution doesn't apply (that was about disconnected attributes; a hierarchy stays coherent). Two mechanisms keep fine-grain affordable:
- **Sparse authoring + derivation:** author the facets that matter for a character; unspecified facets default from the parent aspect/domain mean. No hand-filling 30×N.
- **Salient-subset injection:** the decision engine surfaces only the facets relevant to the scene (same relevance discipline as everything else) — fine-grain in storage, never all-30 in the prompt.

### "People lean one way but act outside it" — the distribution tails
Whole-trait theory handles this exactly: each facet is **(mean, variability)**.
- **Mean = the lean** ("what they're usually like").
- **Variability/spread = the range** they swing through; a per-character variability says how *consistent vs erratic* they are.
- **Out-of-character behavior = a tail sample — and it is NOT random.** It's *produced* by the situation × the Level-2 levers (a goal/value/relationship overriding the trait-lean under pressure): the timid person acts brave because *protecting their child* overrode *timid*. The tails are where the **character-defining moments** live, and they're exactly the realism test (surprising-given-the-lean, inevitable-given-the-motivation). Store the spread, let situation+motivation push the sample; the memorable out-of-character beats fall out — caused, not noise.
