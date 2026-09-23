# SEEKING — the outward band set (reference specimen)

**Status: DRAFT, for review. Not yet in `direction._PHRASES`.**

The first of the eight, written to establish the FORM before the other seven are attempted. If the
form is wrong it is cheaper to find out here.

## What this is

Twenty bands at 0.05 steps across the range, each labelled by its floor. The value stays
continuous — SEEKING 0.17 and 0.15 are different numbers the engine computes with; they render the
same sentence until the value crosses into the next band. Hysteresis on the switch (clear 60% into
the next band) so a value parked on a boundary does not flicker.

Anchors from `docs/emotion-scales.md` are normative and sit at 0.00 / 0.25 / 0.55 / 0.80 / 1.00.
The bands between them interpolate.

**The variable: how much of your attention is committed to what is not here yet.**

**The competing axis this set must NOT encode:** **goal-directedness.** MEASURED — this set's high
triad scored 2/6 (chance) with both extremes inverted, because at 0.70 the character completed an
errand and at 0.80 he did nothing and left. A reader keying on purposefulness ranks them backwards.
Pull-toward leads every clause; absence-from-the-present may flavour and must never lead.

## The rules every phrase obeys

1. **Felt state, never behaviour.** The actor decides what the character DOES. A phrase that names
   an action has already made the decision and left the actor nothing to act. All 32 phrases
   currently in `direction._PHRASES` fail this — they are behavioural, which is the defect this set
   exists to correct.
2. **Never name the emotion.** No "seeking", "driven", "curious", "restless". The actor should infer
   the state from the phenomenology the way a person does. Naming it collapses the performance.
3. **Target-neutral.** These ship with the engine and must fit pursuit of a person, a place, an
   answer, a fortune. `targets.py` supplies who or what.
4. **No digits** (hard rule 5, enforced by `tests/test_no_digits.py`).
5. **Second person, present tense**, one or two clauses.
6. **Legible in sequence.** Adjacent bands need not be distinguishable in isolation — they need to
   read as MOVEMENT when the actor sees one after another.

## The set

| band | phrase |
|---|---|
| 0.00 | nothing is pulling at you, and what is in front of you is all there is |
| 0.05 | no call has reached you, and you would not go looking |
| 0.10 | you are aware there are other rooms and feel no pull toward any of them |
| 0.15 | if someone opened a door you would look, without moving |
| 0.20 | something has caught slightly, not enough to turn your head |
| 0.25 | you would follow a lead if it were put in front of you, and not otherwise |
| 0.30 | a question has occurred to you and you have not put it down |
| 0.35 | you are half-listening for the thing that would tell you where to go next |
| 0.40 | you have started to want a direction, without having one |
| 0.45 | the openings are what you are noticing now, rather than the room |
| 0.50 | what comes next has a piece of you already, and the room keeps the rest |
| 0.55 | the next question is yours, and nobody handed it to you |
| 0.60 | what is ahead is doing the pulling now, and here is somewhere you are passing through |
| 0.65 | the next step has a grip on you, and everything else feels like delay |
| 0.70 | what you are after matters more than where you are, and this place has become the road to it |
| 0.75 | the pull has outrun the room, and waiting for the room to catch up costs you |
| 0.80 | what is next has most of you now, and what is here gets what is left |
| 0.85 | stopping has stopped being one of the things available to you |
| 0.90 | finishing has become something that happens behind you, if it happens |
| 0.95 | every answer is the next question before you finish having it, and there is no arriving |

## Why the top band is a change in kind

`docs/emotion-scales.md` fixes 1.00 as *arrival is impossible*, and that is not "more driven" — it
is the loss of the mechanism that would register having got there. This is Panksepp's own
distinction and the reason SEEKING is a separate circuit: it is the **anticipatory** system, and
consummation runs elsewhere. At the ceiling you get pure wanting with nothing that could receive the
having.

The top band therefore covers 0.95–1.00 rather than reserving 1.00 exactly. Saturation should be
rare, and anything inside that band is already over the rim.

## Known weak points in this draft

* **0.05 through 0.20 are thin.** Four bands describing degrees of not-being-pulled, and I am not
  confident a reader could tell 0.10 from 0.15 in sequence. The low end of an appetitive system may
  genuinely need fewer bands than the high end — worth measuring against a real run before
  authoring the other seven at uniform resolution.
* **0.75 and 0.80 both describe being ahead of the room.** They differ in whether the cost is felt,
  which is subtle. One of them may be redundant.
* **The set is untested against an actual actor.** Nothing here has been given to a model to
  perform. Everything above is craft judgement, not measurement.

---

# SEEKING — the reflexive band set

**Status: DRAFT, for review.** Twenty bands, same 0.05 steps, same rules.

SEEKING is one of only three primitives that admits a reflexive reading (`records.DIRECTEDNESS`).
The repo's own definition is narrow and is followed here rather than reinvented — from
`direction._REFLEXIVE_PHRASES`:

> *pursuit -> display. The basis licenses this as SEEKING-satisfied(self): the deed done, owned,
> shown. **Not hunger aimed inward** — that is SEEKING at a prospect, an object bind.*

So this is not ambition and not self-improvement. Those are outward SEEKING with the self as the
prospect. This is what happens to a person when something they DID starts doing the work of saying
who they are.

**The variable: how much of what you did is standing in for who you are.**

| band | phrase |
|---|---|
| 0.00 | what you have done sits behind you and asks nothing of the room |
| 0.05 | it does not occur to you that any of it needs saying |
| 0.10 | you would mention it if it came up, and you are not waiting for it to |
| 0.15 | there is a small pull to have it known, and ignoring it costs you nothing |
| 0.20 | you have noticed who in the room does not know |
| 0.25 | it would sit better with you if someone else said it aloud |
| 0.30 | the not-saying has started to have a shape |
| 0.35 | what you did feels like it should already be part of how they see you |
| 0.40 | you are standing slightly behind it and would rather stand in front |
| 0.45 | their picture of you is out of date and you can feel the gap |
| 0.50 | it has stopped being a thing you did and started being a thing you are |
| 0.55 | you would rather be understood for it than liked without it |
| 0.60 | the room's not knowing has become a small ongoing error |
| 0.65 | it is what you would offer if anyone asked what you are worth |
| 0.70 | you weigh what people say by whether they have accounted for it |
| 0.75 | it has become the ground you argue from |
| 0.80 | it answers most questions before they are finished |
| 0.85 | what is said to you lands on what you did, and most of it stops there |
| 0.90 | it stands between you and whatever is meant for you now |
| 0.95 | it does all the answering for you now, and who you are is not consulted |

## Notes

* **The bottom is not empty, and the existing table says it is.** `direction._REFLEXIVE_PHRASES`
  opens SEEKING with `None` — no reflexive reading at the lowest band. At four bands that was right;
  at twenty there is room for the states between *nothing to show* and *wanting it known*, which are
  where most people live most of the time.
* **The three existing phrases are BEHAVIOURAL and are superseded here.** "you put your name to what
  you did and let that stand", "you bring what you did into the conversation" — both name an action,
  which decides for the actor. The band set above conveys the state and leaves the telling to them.
* **The top band is a change in kind.** Below it, correction reaches a person who can still be told
  something. At 0.95 there is no self underneath the achievement for a correction to land on — the
  same structure as RAGE's ceiling, where the self-observer drops out.
* **Weak point:** bands 0.20-0.35 are four shades of wanting-it-known and I am not confident a reader
  distinguishes them in sequence. Same concern as the outward set's low end.
