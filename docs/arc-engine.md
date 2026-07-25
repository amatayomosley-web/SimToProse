# Arc Engine — durable change (trauma, growth, the through-line) (WORKING)

**Status: working.** How a character's **baseline** changes over the book — trauma debuffs, eudaimonic buffs, the slow transformation that is the novel's through-line. This is `character-model.md` roadmap #3 (the arc/transformation engine), and it answers "how do we set the values for trauma / eudaimonic *types*." The durable-timescale pair to `state-engine.md` (momentary state).

## Not a new mechanism — appraisal with a DURABLE write
`state-engine.md` already computes an event's impact (`severity × relevance × trait_sensitivity`) and writes a **transient** spike that decays. Trauma and eudaimonic events run the *same appraisal* — but the write is **durable**: instead of (or as well as) spiking current-state, the event diffs the **baseline** (temperament, value-weights, attachment, vault). Momentary state decays back; a durable diff **moves the floor**. One engine, two write-paths:
- **transient** → current state (the scene's emotion), decays (`state-engine.md`);
- **durable** → the baseline (who they now are), persists (here).

## When an event writes durable (the threshold)
Most events spike and fade. An event crosses into **durable** when its appraised impact is high **and** it is the *kind* that reshapes — grounded in the trauma / post-traumatic-growth literatures:
- **overwhelm** — exceeds the character's coping capacity in the moment (effortful-control + resources);
- **core-relevance** — strikes an identity-central value, an attachment, or a survival assumption (not a peripheral stake);
- **(trauma)** inescapability / violation of a core assumption ("the world/people are safe"); **(eudaimonic)** deep fulfilment of a core need — meaning, mastery, secure connection (the eudaimonic-wellbeing axes: autonomy, competence, relatedness, meaning).

Below the threshold → transient. Above → a durable baseline diff. (Threshold + coping/resource terms are Class-B calibration.)

## The "type" sets WHICH baseline value is diffed — from the menu (no per-event authoring)
The **kind** of trauma/eudaimonic event determines the **kind** of durable diff, by **which menu-item it engaged** (`values-and-stakes.md` — the same menu, now as the *reshape-target*). The menu does triple duty: values-held / harm-threatened / durable-reshape-target.

| Event type (menu-item hit) | Durable diff (the buff/debuff) |
|---|---|
| **Betrayal** (loyalty, by an intimate) | trust-prior ↓, attachment → anxious/avoidant, vigilance ↑ |
| **Violence / survival-threat** (body) | FEAR-baseline ↑, threat-reactivity ↑, startle (the PTSD signature) |
| **Loss** (attachment severed) | GRIEF-baseline, a wound; sometimes CARE-withdrawal (avoid re-attachment) |
| **Humiliation** (status-degradation) | shame-proneness ↑, status-sensitivity ↑; sometimes RAGE / vindictiveness |
| **Mastery** (competence fulfilled) | competence ↑, self-efficacy, SEEKING ↑, threat-reactivity ↓ (confidence buffers fear) |
| **Connection** (secure bond, relatedness) | attachment → secure, trust-prior ↑, CARE ↑ |
| **Meaning** (a value realized, purpose) | the value crystallizes / weights up; resilience ↑ (meaning buffers adversity) |

Magnitude = `appraised-impact × durability × (1 − resilience)`. A "type" has a **target** (the menu-item) and a **formula** — never a fixed authored number.

**The two operands, defined (audit B6 — they were formula terms with no source):**
- **`durability`** — how lasting this event-*class's* impact tends to be. A **class default carried by the event-type catalog** (`record-contract.md` — the same catalog row that carries the appraisal map): `transient | marking | reshaping`, refined upward by core-relevance at a hinge. Numeric mapping is Class-B calibration; the *source* is the catalog, not a per-event author.
- **`resilience`** — **DERIVED at read time, never stored** (`character-schema.md` DERIVED row): composed from four already-stored fields — `effortful_control` (genotype axis) × **attachment-security** (relationship priors + presence of a current secure bond, `relationships.md`) × **current condition** (high allostatic load depletes it, `relevancy-gate.md` energy state) × **meaning-frame availability** (does the Model give this event-class a coherent place — the meaning-making term, `values-and-stakes.md`). Combination form is Class-B calibration; the fields are these four. Open-Q 1 below narrows to the numeric form only.

## Same event, damage OR growth — by resilience (the fork)
The durable outcome is **not fixed by the event** — it's modulated by the person's **resilience** (genotype + existing resources + meaning-making):
- low resilience → a large debuff (damage / PTSD);
- high resilience (secure base, effortful-control, a meaning-frame) → a smaller debuff, or even a **eudaimonic** diff — **post-traumatic growth**, the same trial writing mastery or wisdom.

Same betrayal: one hardens into distrust, another into wary wisdom. The growth-vs-damage fork falls out of resilience — never authored per outcome. (The durable-timescale mirror of `state-engine.md`'s "two people, same event, different reaction.")

## The unification — this IS baseline-generation, run at runtime
A durable diff is the **identical operation** as a formative diff (`baseline-generation.md`): `event → typed baseline weight-diff`. So:
- **Generation** = the character's formative traumas/joys, **pre-run** before page one (a street childhood = many small violence/betrayal diffs → "Street-Hardened");
- **The arc** = the book's traumas/joys, run **during** it, moving the baseline as the story happens.

**Backstory and arc are one engine** — generation just pre-plays the arc up to the start. This is why a deep backstory and a transformative plot use the same machinery, and why "set trauma values" has the same answer as "set baseline values": the menu sets the target, appraisal sets the magnitude, resilience forks the sign.

## Granularity (the `design.md` value-granularity rule applies)
Don't author a diff per specific event. A background character's trauma → a **class-default** diff (the standard violence-signature); a **principal's** defining trauma → **refined** to its specifics (this betrayal, by this person, at this developmental moment) at the hinge, from the book's authored detail. Default for the long tail; precision where the book levers on it.

## Open questions
1. **Durability threshold + resilience terms** — the exact coping / overwhelm / core-relevance formula; Class-B calibration.
2. **Diff healing** — do durable diffs themselves slowly soften over the arc (a wound easing over years) or change only via new events? (Lean: very slow heal toward the pre-event baseline — far slower than state-decay; some scars permanent.)
3. **Accumulation** — many small traumas summing vs one large one (developmental vs single-incident), with caps so a much-traumatized character doesn't saturate.

## Cross-links
- **Same engine as:** `state-engine.md` (appraisal — durable is the other write-path), `baseline-generation.md` (the identical diff op, pre-run).
- **Types from:** `values-and-stakes.md` (the menu = the type-taxonomy).
- **Is:** `character-model.md` roadmap #3 (arc / transformation engine), now designed.
