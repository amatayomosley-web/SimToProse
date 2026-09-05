# The emotion list — every name, staged by degree

**Status: DRAFT.** The showrunner's vocabulary. One row per emotion family, five degrees each.

An emotion is a **name plus a location**. Most families are a span on one primitive's scale; a few
need two primitives together.

**SCOPE — the name tells you the degree, and that holds cleanly for the eight ladders only.**
*Annoyance* and *rage* are one circuit at two heights: the coordinate does not change, only the
value. Eight families, verified against `emotion-scales.md`'s anchors.

**LEAVE-ALONE — it does NOT hold for the compound families, and assuming it there is an error.**
Their RATIO can change as the degree rises, not just their magnitude. `hate` is the clearest case:
*dislike* carries no preoccupation at all, while *hatred* does — so the SEEKING term appears partway
up the ladder rather than scaling with the other two. Same for `pride`, where the PLAY term thins out
as *pride* becomes *hubris*. A compound row is five related coordinates, not one coordinate at five
heights, and each degree needs its own ratio written before the row is usable.

That distinction is also the test for which layer a family belongs in: **if the ratio is constant up
the ladder, it is a range name and belongs with the eight.**

**How to read a row.** The five columns are the spans `0.00–0.25 / 0.25–0.55 / 0.55–0.80 /
0.80–0.95 / 0.95–1.00`, matching `docs/emotion-scales.md`'s normative anchors. `sits on` names the
primitive or primitives the family is located in.

---

## The eight ladders — one primitive each

These are complete. Every state nameable on a single axis is here.

| family | floor | low | mid | high | ceiling | sits on |
|---|---|---|---|---|---|---|
| **drive** | incurious | interest | drive | obsession | compulsion | SEEKING |
| **fear** | unguarded | caution | wariness | dread | terror | FEAR |
| **anger** | unmoved | annoyance | anger | fury | rage | RAGE |
| **desire** | indifferent | attraction | desire | craving | consumed | LUST |
| **caring** | unclaimed | regard | kindness | devotion | sacrifice | CARE |
| **grieving** | content alone | missing | grief | mourning | desolation | PANIC_GRIEF |
| **play** | earnest | levity | play | absorption | flow | PLAY |
| **revulsion** | untroubled | distaste | aversion | revulsion | abhorrence | DISGUST |

## The compound families — two primitives, staged

Each needs a ratio, not just a height. The degrees stage the *intensity* of that ratio.

| family | floor | low | mid | high | ceiling | sits on |
|---|---|---|---|---|---|---|
| **love** | acquaintance | fondness | love | devotion | adoration | CARE + LUST + PANIC_GRIEF |
| **hate** | dislike | animosity | hatred | loathing | consuming hatred | RAGE + DISGUST + SEEKING |
| **shame** | self-consciousness | embarrassment | shame | humiliation | mortification | PANIC_GRIEF(self) + DISGUST(self) |
| **guilt** | qualm | compunction | guilt | remorse | self-condemnation | PANIC_GRIEF(self.act) + CARE(beneficiary) |
| **pride** | satisfaction | pride | vanity | arrogance | hubris | SEEKING(self) + PLAY |
| **envy** | comparison | envy | covetousness | resentment | bitterness | SEEKING + RAGE + DISGUST |
| **jealousy** | watchfulness | jealousy | possessiveness | fixation | frenzy | CARE(beneficiary) + RAGE + FEAR |
| **contempt** | dismissal | disdain | contempt | scorn | abomination | DISGUST + RAGE |
| **anxiety** | unease | nerves | anxiety | distress | panic | FEAR + SEEKING + PANIC_GRIEF |
| **loneliness** | solitude | loneliness | isolation | abandonment | forsakenness | PANIC_GRIEF + CARE-unbound |

## Families the engine cannot currently express

Not omissions — measured failures. Each names what blocks it.

| family | floor | low | mid | high | ceiling | blocked by |
|---|---|---|---|---|---|---|
| **joy** | contentment | pleasure | joy | elation | ecstasy | **no consummatory primitive.** MEASURED: any coordinate over the current eight lands at 0.996 cosine to `charming`. Joy is *a want met*, and no primitive registers a met want. |
| **hope** | openness | hope | confidence | conviction | certainty | same. Hope is anticipated satisfaction; without the slot it collapses into SEEKING. |
| **gratitude** | acknowledgment | thanks | gratitude | indebtedness | devotion-in-debt | same, plus no primitive registers *a benefit received from an agent*. |
| **relief** | easing | relief | reprieve | deliverance | absolution | the `relief` DIMENSION exists and lowers FEAR and PANIC_GRIEF, but nothing holds the resulting state. |
| **serenity** | ease | calm | serenity | peace | equanimity | every primitive at rest is *nothing happening*, which is not *being well*. |
| **awe** | notice | wonder | awe | reverence | transcendence | no size relation in the basis. Awe needs self-diminishment before something vast. |
| **sadness** | — | — | — | — | — | **needs negative coordinates.** `SEEKING −0.25, PLAY −0.30`. `validate()` returns ok; `compose()` silently clamps both to zero and yields grief without the flattening. |

**One primitive would unblock five of the seven.** Joy, hope, gratitude, relief and serenity all fail
for the same reason: they are positive states that need a **met want** to sit on. That is the
consummatory system Panksepp pairs with SEEKING and this basis omitted — SEEKING's own ceiling is
defined as *arrival is impossible* precisely because consummation runs elsewhere, and there is no
elsewhere here.

---

## Every state the engine can render — all seventy

Direction changes the emotion, not just its object. DISGUST at 0.80 aimed outward is **revulsion**;
aimed at yourself it is **self-shielding**; aimed at nothing it is **fouled**. Three different states
at one number, and all three have written phrases.

Fourteen tables, five spans each. The eight OUTWARD rows are repeated from above for completeness.

| table | 0.00-0.25 | 0.25-0.55 | 0.55-0.80 | 0.80-0.95 | 0.95-1.00 |
|---|---|---|---|---|---|
| SEEKING outward | incurious | interest | drive | obsession | compulsion |
| **SEEKING reflexive** | unremarked | claiming | standing on it | identified | incorrigible |
| FEAR | unguarded | caution | wariness | dread | terror |
| RAGE | unmoved | annoyance | anger | fury | rage |
| LUST bound | indifferent | attraction | desire | craving | consumed |
| **LUST unbound** | unstirred | stirring | restlessness | yearning | aching |
| CARE bound | unclaimed | regard | kindness | devotion | sacrifice |
| **CARE unbound** | unneeded | readiness | tending | overspending | unspendable |
| PANIC_GRIEF bound | content alone | missing | grief | mourning | desolation |
| **PANIC_GRIEF reflexive** | whole | altered | self-grief | displaced | stranger to yourself |
| PLAY | earnest | levity | play | absorption | flow |
| DISGUST bound | untroubled | distaste | aversion | revulsion | abhorrence |
| **DISGUST reflexive** | clean | self-conscious | withholding | self-shielding | untouchable |
| **DISGUST unbound** | open | fastidious | recoiling | fouled | defiled |

**The thirty in bold are new** — those tables had bands but no names, so a showrunner reading
`DISGUST 0.85, aimed at self` had a rendered phrase and no word for what it was.

### Why these thirty are not synonyms of the outward forty

Each was named against its own table's declared variable, not by adding a modifier to the outward
name. Three worth checking, because they are the ones most likely to be mistaken for their neighbours:

* **self-shielding (DISGUST reflexive 0.80) is not shame.** Shame is the compound
  PANIC_GRIEF(self) + DISGUST(self) — loss AND imposition. This is the imposition alone: you as the
  thing others need distance from, with nothing lost. A character can be at self-shielding without
  grieving anything.
* **stranger to yourself (PANIC_GRIEF reflexive 0.95) is not self-loathing.** It carries no verdict.
  The former self is gone and the loss registers — nothing weighs whether the remaining self deserves
  to be here. Verdict is DISGUST's channel.
* **aching (LUST unbound 0.95) is not desolation.** The world is full and the wanting has no
  destination. Desolation is the world failing to add up. One is appetite without object, the other
  is a world without sum.

### The count, honestly

**70 states with written phrases and names.** Not 70 *emotions* — SEEKING reflexive and SEEKING
outward never co-render (`direction._phrase_for` picks one bind per primitive per beat), so no
character is ever in more than eight of them at once.

Names for the thirty are JUDGEMENT, written in one pass, uncalibrated — the same status as the
outward forty and flagged for the same reason.

## Not emotions

| name | what it actually is |
|---|---|
| **surprise** | an expectation violation — a prediction error that then RECRUITS an emotion. Belongs in the appraisal step as a property of an event, not in this list. MEASURED: any coordinate for it lands at 0.995 to `resolve`. |
| **trust** | a relationship axis in `bonds.py`, a property of an EDGE between two people, not a state of a person. Plutchik treats it as base; making it an affect here would double-book it. |
| **depression** | SEEKING floor + PLAY floor, with PANIC_GRIEF free. Already expressible, and it reads by subtraction — the one state the engine names by what has gone. |

## Notes

* **Where the two layers overlap, the ladder wins.** `fury`, `grief` and `revulsion` exist in
  `compounds.py` as single-primitive entries — they are range names, and naming them as ratios is
  what produced the collisions (`contempt`/`scorn` at 0.986 cosine, two names for one ratio).
* **The names are judgement.** No literature, no measurement, no anchor calibrated them — the same
  gap the primitives had before `emotion-scales.md`. The *ordering* within each row is the claim;
  the boundaries between degrees are not yet adjudicable the way the eight ladders' are.
* **The list is showrunner-facing only.** A degree name must never reach the actor — naming the
  emotion collapses the performance onto a stock reading (`docs/phrases-seeking.md` rule 2).
