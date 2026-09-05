# CARE — the band sets

**Status: DRAFT, for review.** Forty bands. Same 0.05 steps, same rules as `docs/phrases-seeking.md`.

## Why CARE's two sides are BOUND / UNBOUND, not self / other

CARE **refuses a reflexive reading**, and the argument is recorded at `records.py:93`:

> *act on another's behalf at cost to yourself — definitionally other-directed, so reflexive is not
> admitted ("self-care" is welfare management through SEEKING and FEAR, not the nurturance circuit).*

So there is no self-directed CARE. The second table is UNBOUND: the nurturance drive running with
no beneficiary. High CARE, empty target slot — the person who tends a fire nobody asked about.

---

## BOUND — someone is who it is for

**The variable: how much of your own interest you would spend on them.**

**The competing axis this set must NOT encode:** **worry.** Fearing FOR someone is FEAR with a
care_relevant subject, not CARE. A band that renders as anxiety about their safety puts one note in
two slots of the vector.

| band | phrase |
|---|---|
| 0.00 | no one here has a claim on you, and that is not a decision you made |
| 0.05 | their business is theirs and yours is yours, and the line is not one you think about |
| 0.10 | you would not step over them, and you would not step toward them either |
| 0.15 | you notice when someone is struggling, the way you notice weather |
| 0.20 | you would point them toward help rather than be it |
| 0.25 | you will do a small thing for them if it costs you little |
| 0.30 | you would give up a few minutes, and you would want them back |
| 0.35 | how they are doing has started to matter to how you are doing |
| 0.40 | you are keeping track of how they are doing without meaning to |
| 0.45 | you would rearrange your evening for this |
| 0.50 | what they need and what you need are both on the table now |
| 0.55 | their situation is competing with yours, and sometimes it wins |
| 0.60 | you would take the worse end of it and not mention that you had |
| 0.65 | your own plans have gone provisional without you deciding that |
| 0.70 | you would take the hit before you would let them take it |
| 0.75 | the yes has already happened in you, and your reasons are catching up |
| 0.80 | by the time you notice there was a choice, it is already made in their favour |
| 0.85 | what it costs you has stopped being one of the inputs |
| 0.90 | there is no version of what comes next where you put yourself first |
| 0.95 | what you wanted for yourself is not in the calculation, and you could not put it back |

---

## UNBOUND — the impulse is real and the beneficiary is not

**The variable: how much you would spend, with nobody it is for.**

**The competing axis this set must NOT encode:** **the ache of having no one.** Distress at an absent
bond is PANIC_GRIEF's job. Unbound CARE must stay drive-flavoured — the impulse spilling onto
whatever is nearest — or it double-books a primitive that already owns the bereavement.

| band | phrase |
|---|---|
| 0.00 | nothing here has reached you as needing you |
| 0.05 | nothing asks anything of you, and you have not noticed the quiet |
| 0.10 | what is out of place registers, and asks nothing of you yet |
| 0.15 | there is a small readiness in you with nowhere to go |
| 0.20 | what wants tending is beginning to show itself to you, and it is small |
| 0.25 | you would tend to something if something needed tending |
| 0.30 | the readiness has started to feel like a question |
| 0.35 | you are looking for what is out of order, and finding little |
| 0.40 | the readiness has started inventing things for itself to be for |
| 0.45 | the impulse arrives fully formed and finds no one |
| 0.50 | the impulse has started landing on whatever is in reach |
| 0.55 | whatever is nearest has become what you are for |
| 0.60 | things that were not asking have started to feel like yours to tend |
| 0.65 | what you are spending it on cannot use it, and it is being spent anyway |
| 0.70 | anyone's business would be yours the moment you heard of it |
| 0.75 | a stranger would have your whole attention and would not have asked for it |
| 0.80 | who it is has stopped mattering, so long as there is someone |
| 0.85 | you are spending it on the room itself |
| 0.90 | you would spend yourself down to nothing on this, and no one here is who it is for |
| 0.95 | there is nothing you would not take on, and nothing that is asking |

## Notes

* **The two existing unbound phrases are preserved**, at 0.55 and 0.90 — they were bands 2 and 3 of
  four, and those positions are the nearest equivalents. Both are FELT-STATE already, unlike most of
  `direction._PHRASES`, so they survive the rewrite intact.
* **The existing table opens `(None, None, ...)`** — no unbound reading for the bottom two of four,
  because "the object phrases keep working; neither names a person". At twenty bands that boundary
  has to be re-found, and I have written low-end phrases rather than leaving them empty. The reason:
  at low CARE the bound and unbound readings genuinely converge — *no one here has a claim on you*
  and *nothing here needs you* describe nearly the same evening. **That convergence is the finding,
  not a defect**: an emotion with nothing to aim at and an emotion aimed at nobody in particular are
  the same state until there is enough of it to need a direction.
* **The unbound top band is bleaker than the bound one, and that is deliberate.** Bound 0.95 spends
  everything on someone. Unbound 0.95 spends everything on nothing. The second is the harder state
  and the engine should be able to say it.
* **Weak point:** unbound 0.30-0.45 are four shades of an impulse looking for an object. Same
  low-middle thinness flagged in the SEEKING sets. Still an untested suspicion, one author, no
  reader has been asked to tell them apart.
