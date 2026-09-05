# PANIC_GRIEF — the band sets

**Status: DRAFT, for review.** Forty bands at 0.05 steps. Rules as `docs/phrases-seeking.md`.

Regions (`docs/emotion-scales.md`): content alone / missing / grief / mourning / desolation.

**The label is a compound of two severe words and it misleads at the floor.** The bottom of this
scale is *contentment at being alone*, not a small amount of panicked grief. A showrunner reading a
sheet would not guess that from the name.

**The channel PANIC_GRIEF owns**, for the composition rule: **the world's completeness** — whether
what is present amounts to a world. PLAY owns the current activity's stake and this owns the total,
which is why the two ceilings compose: grief respite inside absorption is a real beat.

---

## BOUND — someone is gone

**The variable: how much of the world still works without them.**

**The competing axis this set must NOT encode:** **dread.** A loss not yet suffered is FEAR with a
loss-shaped prospect. No band here is prospective — the break is already behind and registering now.

**Mood:** perfect-anchored present — what has already happened, persisting. The floor is habitual,
because contentment alone is a standing condition and never an event.

| band | phrase |
|---|---|
| 0.00 | being on your own is how things are, and it is not a fact you are keeping |
| 0.05 | where they are not is just more room |
| 0.10 | you think of them when something brings them up, and not otherwise |
| 0.15 | their being elsewhere sits easily, and now and then you notice that it does |
| 0.20 | something crosses your mind to tell them, and keeps until whenever |
| 0.25 | you would rather they were here, and the day works either way |
| 0.30 | the day keeps producing things that belong to them somehow, and you keep noticing |
| 0.35 | their not being here has a small weight now, and you can carry it without shifting |
| 0.40 | part of you keeps expecting them in the usual places, and keeps being corrected |
| 0.45 | what they would say keeps arriving on its own, in their voice or near it |
| 0.50 | their not being here has stopped waiting for reminders, and shows up on its own |
| 0.55 | their absence is a thing in the room with you, whichever room it is |
| 0.60 | whatever happens, part of it is that it happens without them |
| 0.65 | the absence has begun to reach the things that were only ever yours |
| 0.70 | more of the day happens at a remove now, on the other side of their not being here |
| 0.75 | some of what you turn toward, you turn toward because it is not this |
| 0.80 | the day has arranged itself around the places you cannot go in it, and you know every one |
| 0.85 | what does not touch them has begun to feel like it is not quite happening |
| 0.90 | the world has kept going and stopped adding up, and both are true all day |
| 0.95 | what is left does not add up to a world, and you are still in it |

0.45 leans on the `recall` kind — this is the one primitive the engine concedes can be re-triggered
by memory rather than by anything in the room. 0.75 and 0.80 render the anchor's *"organising your
day around not feeling this"* as felt avoidance-structure rather than scheduling acts.

**Flagged trade:** the whole table presumes the target absent, outright at 0.15. That is inherited
from the normative anchors themselves (*"you would rather they were here"*) rather than introduced
here — a bound target standing in the room misfires at anchor level, and that is the anchors' problem.

---

## REFLEXIVE — the bond's other end was you

**What it is.** `records.py:100` records the reflexive reading as *"the self as the thing severed
from the group, which is shame's ingredient"* — **belonging-loss, not identity-loss.** The
former-self phrasing covers it without contradiction, because the self that registers as missing when
you are severed is the you that belonged. The table is kept clear of self-verdict throughout, so
shame still composes from PG(self) + DISGUST(self) as two distinct ingredients.

**The variable: how much of the world still works without who you were.**

**The competing axis this set must NOT encode:** **self-verdict.** Unfitness, contamination and
deserving are reflexive DISGUST. This table registers only the absence — no band may weigh the lost
self or the remaining one.

| band | phrase |
|---|---|
| 0.00 | who you are now and who you have been are one piece, and you never check the seam |
| 0.05 | earlier is just earlier, and nothing back there is asking |
| 0.10 | now and then a difference between then and now surfaces, and it is only a difference |
| 0.15 | the things you used to be come up lightly, when they come up |
| 0.20 | an earlier you crosses your mind trailing something, and the something does not stay |
| 0.25 | you would rather still be who you were then, and the day works anyway |
| 0.30 | habits arrive that belonged to an earlier you, and you notice whose they were |
| 0.35 | what you no longer are has begun to weigh something, not much |
| 0.40 | part of you keeps expecting to be who you were, and keeps being corrected |
| 0.45 | how you would have taken this, before, arrives alongside how you are taking it |
| 0.50 | who you were has stopped needing reminders to come up, and comes up |
| 0.55 | the person you are not any more is a thing in the room with you |
| 0.60 | your days fit like they were cut for someone else, and they were |
| 0.65 | the difference has reached the small things now, the ones that used to be safe from it |
| 0.70 | more of the day happens at a remove now, on the far side of who you no longer are |
| 0.75 | some of what you turn toward, you turn toward because it carries no trace of who you were |
| 0.80 | the day has arranged itself around the places where the difference shows, and you know every one |
| 0.85 | being anyone at all has started to feel like standing in for someone who is not coming back |
| 0.90 | your life has kept going and stopped adding up, and you are the place where both are true |
| 0.95 | the person these days were built for is gone, and you are what is left to live them |

**Flagged trade at 0.60:** *"and they were"* states the character's own history flatly. Taken
deliberately — reflexive claims about one's own past are registration by nature, since the character
is the only registry of who they were, and the clause only colours register. The deliberate echoes of
the outward table at 0.40, 0.55 and 0.90 never co-render (one bind at a time per primitive) and make
the shared variable visible.

## Notes

* **Slowest event-driven decay in the basis (0.90)** — by design: grief outlasts its cause.
* **⚠ APPLYING THE REFLEXIVE TABLE CHANGES RECORDED DOCTRINE, AND THE CODE WILL USE IT IMMEDIATELY.**
  `records.py:105` sets `direction_changes: False` for this primitive, arguing *"the despair phase is
  autonomic and UNDIRECTED... the most self-directed primitive in the vocabulary needs no new words."*
  But `direction._phrase_for` selects the reflexive variant on `admits_role(p, "self")` alone and
  **never reads `direction_changes`**, despite its own docstring claiming it does and naming
  PANIC_GRIEF as the case that deliberately does not take the branch. The mismatch has been invisible
  only because `_REFLEXIVE_PHRASES` has no PANIC_GRIEF entry, so the branch falls through. The moment
  this table lands it goes live. Either flip the registry cell to True and amend its comment, or make
  `_phrase_for` read the field it cites — the second keeps the doctrine and leaves this table dormant.
  **Author's decision, not a mechanical fix.**
* The original argument was made about four *behavioural posture* phrases, which were role-free by
  construction. The felt-state rewrite carries them-deictics — *"you would rather they were here"*,
  *"their absence is a thing in the room with you"* — which misfire under a self bind. The felt-state
  form creates the need the behavioural form did not have.
* **Ceiling composition.** Claims the world-sum only: with PLAY (its own reason, inside a world that
  does not add up — respite), with SEEKING (the searching phase of grief), with CARE (the grieving
  carer). The reflexive ceiling composes with DISGUST-reflexive into shame entire — loss plus
  imposition, two ingredients, no overlap.
