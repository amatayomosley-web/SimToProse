# GOODWILL — the ten rung blocks

> **BEHAVIOURALLY REVIEWED 2026-09-08 - ALL TEN RUNGS, 10 of 10 after two pre-registered scene
> fixes, 14 blind actor sims.** Record: **`docs/rungs/GOODWILL-behavioural-review.md`**.
> THIS IS THE FIRST PERFORMANCE TEST OF THE REPAIRED BLOCKS - the status line below says the repairs
> to 4 / 6 / 7 / 8 / 9 were text-sorted and not re-performed. They are now performed, and they hold.
>
> **THE HINGE IS IN RUNG 6'S OWN WORDS - "you have CROSSED from noticing into doing" - and the ladder
> needs two graded variables:** 1-5 is how much of you is TAKEN UP with them; 6-10 is how much of you
> is SPENT on them. A single question across the hinge misorders the top (see
> `cairn/learnings/2026-09-08-the-wrong-variable-at-a-hinge-inverts-the-top.md`). Concretely: rung 8
> says "your attention is NOT ON THEM NOW but on what could reach them", so an attention-on-them
> scorer must rank RUNG 8 BELOW RUNG 4. Predicted from this file's own block text before any sim,
> then confirmed in performance - the actor made the trade explicit: "I don't look, because looking
> means taking my eyes off the doorway."
>
> **TWO SCENE REQUIREMENTS, both measured:** rungs 6 and 7 are INDISTINGUISHABLE in a scene with only
> one time point in it (rung 7 is a standing orientation, a fact about days) - give the scene a week
> and they separate cleanly. Rungs 9 and 10 DO NOT PERFORM in a scene with nothing worth giving up;
> in an evening offering a phone call and a notebook they both read as rung 6. Do not serve 9 or 10
> to a character with nothing at stake.
>
> **AXIS:** how much of you another's welfare has taken. A rung names WHICH part of you has gone over
> to them — attention, body, action, day, priorities, everything — in a fixed order. Not how much is
> felt, and not how good a person it makes you.
> **STATUS 2026-09-07:** BUILT (`gen_rungs.py` compiles; `rungs.rung_at` resolves; `scripts/composer.py`
> selects). **Text-sorted at rho 1.0 / 1.0 / 0.988 (mean 0.996)** — twice, before and after repair, with
> no change. **Performance-tested as full blocks: 2 of 2 valid scenarios recovered the exact order**; the
> third's rung-6 actor returned a placeholder and is excluded, not counted. **The action line at rung 6
> held in every performed cell.** Repairs to blocks 4 / 6 / 7 / 8 / 9 were text-sorted, **not
> re-performed**; the header says so and so does the measurement record.
> Design of record: `docs/emotion-paths.md` §5, which this file builds against and does not restate.

---

## What is measured, and what it cost to learn

**THIS IS THE FIRST OTHER-DIRECTED PATH, and the structure/content rule held.** *Them / this one* is
the empty slot — never filled. A nine-year-old mapped it to a bird; a bedridden woman to her son; a man
at his desk to a colleague. The lens that checks whether any block names who they are, their age, their
species, or the relationship found **nothing** across all ten. The blocks say *them*; the actor decides.

**THE ACTION LINE IS REAL.** `emotion-paths.md` §5 draws it at rung 6 — *enough of you to move you* —
and this run tested it directly: rung 6 **acted** in every valid scenario, rung 2 in **none**. The
bedridden woman at 6 *"orders him closer, grips his hand past what her strength should allow."* The man
at his desk *"intercepted her ringing phone, took the message, left it at her desk so she wouldn't be
interrupted."* At 2 the same three people watched, felt, and did nothing — *"no approach, no word."*
The threshold performs where the design puts it.

**CARE FROM IMMOBILITY PERFORMS.** The scenario where the *carer* is the one who cannot move was built
to break any block that assumes the carer can act in the world. At rung 6 she acted anyway — with her
voice and her hand, the two things she had. At rung 9 she *"asked him to move the chair closer, then made
room at the edge of the mattress."* The universality rule is not a constraint on the state; it is a
constraint on how the block describes it, and when the block describes it right the actor finds the
version available to the body in the scene.

**SELF-ERASURE FIRED WHERE I PUT IT, NOT WHERE THE DESIGN WARNED.** The design says English names total
consumption by another's welfare only from the self's side — *self-abnegation, self-abandonment* — and
those belong to SELF-REGARD. I expected that pressure at rung 10. It fired at **rung 9**: two sorters and
two judges read devotion as the self dissolving — *"the boy who had walked into the yard twenty minutes
before had simply stopped being the one any of this was about."* Cause: I had written *"what you want for
yourself has thinned… the self quieter than it was"* into the **priorities** rung. That is 10's
territory, pulled down a rung by my prose. Repaired to priority-reordering with the self intact; on
re-sort, every self-erasure flag moved to rung 10 and stayed there. **At 10 it is correct** — that is
the rung the design keeps on the engine's own 1.00 anchor with the objection recorded.

**AGENCY LANGUAGE WAS IN FOUR BLOCKS, and it was not where I predicted.** I expected the lens to name 7
and 9. It named 6, 7, 8: a capability check (*"if I can"*), a named competing intention resolved by
comparison (*"before what I was going to do"*), a **vow** (*"Nothing gets to them through me"*), and a
**tactic** (*"to place yourself between"*). Care can be chosen, so this is the hard lens for this path.
All four repaired. A vow is a commitment one makes; the block now states the position instead — *you are
what stands between them and it.*

### Two things about the instrument, not the blocks

The bird scenario's rung-6 actor returned the literal text *"Test passage."* — the second placeholder
output from an actor today. Its judge scored that cell at the floor by absence. The scenario is excluded
from the exact-recovery count rather than repaired or re-run. A placeholder filter with retry is owed in
the harness.

The bedridden judge flagged rung 2 as *"invented a person"*; reading the passage, the only person in it
is the son the scenario supplies. Judge error, minor, recorded because the discipline is to read.

### One thing about the engine, recorded not fixed

`emotion-scales.md:184` says CARE is *"lowered by NOTHING"* and §5 calls it a live blocker. Checked:
`state.py:121` gives CARE a decay rate of 0.82 and `decay()` relaxes every primary toward its baseline
each turn — **care falls by decay.** What is true is narrower: `state.py:55` shows `care_relevant +0.40`
is the **only event** that moves it. No event lowers care. A betrayal by the cared-for does not knock it
down; it only stops topping it up. That is a real design gap — care should be *damageable* — and it sits
on the climb/fall axis. An appraisal kind that lowers CARE is an engine change under its own gate.

---

## The spine: what has gone over to them, in order

```
register → feeling → this one → attention → body → moves you [ACTION] → your day → vigilance → priorities → everything
```

| # | rung | what has gone over | band | |
|---|---|---|---|---|
| 1 | goodwill | it has begun to register | 0.00–0.09 | thought |
| 2 | warmth | it has taken feeling, not just reckoning | 0.09–0.18 | thought |
| 3 | fondness | it has particularised to this one | 0.18–0.27 | thought |
| 4 | concern | your attention; it returns on its own | 0.27–0.36 | thought |
| 5 | tenderness | your body's disposition toward them | 0.36–0.45 | thought |
| 6 | compassion | **enough of you to move you** | 0.45–0.54 | **action** |
| 7 | solicitude | your day arranges around it | 0.54–0.62 | action |
| 8 | protectiveness | your vigilance, standing by in advance | 0.62–0.70 | action |
| 9 | devotion | your priorities | 0.70–0.85 | action |
| 10 | sacrifice | nothing of you is not theirs | 0.85–1.00 | action |

Bands are `emotion-paths.md` §5's; copied, not re-derived. Devotion is wide on the design's own
finding that English has no rung between devotion and sacrifice.

**NOT ON THIS LADDER, by the design's evictions:** doting / overprotectiveness are a calibration flag
(keyed-to-want vs matched-to-need — *tough love* is the same height with the dial reversed); pity and
paternalism are rank, on the respect edge; saviour and martyr are a height here plus existing edge
fields. And **STIRRING is this path's stated sibling** — it walks toward *possessing*, this walks
toward *their flourishing*, and the design asks that the two be read side by side once both exist.

---

## Rules every block obeys

1. **Structure is ours; content is the actor's.** No block names who they are, what they are, or what
   the relationship is. *Them / this one* is the actor's to fill — a person, an animal, a place.
2. **Taken, never chosen.** Care can be decided on, which makes this the hardest path for the agency
   hold. No capability checks, no named competing intentions, no vows, no tactics. A block states the
   position the character is in; the actor decides what to do from it.
3. **Four-case universal, with the CARER as the immobile one.** No block assumes the carer can move,
   see, or reach. Where an act is implied, it is hedged — *in whatever way is open to you*.
4. **The self is given over, not dissolved.** Self-erasure belongs to SELF-REGARD. Only rung 10 is
   allowed to read that way, and only because the design keeps *sacrifice* on the engine's anchor.
5. **The name is never delivered.**

---

## The blocks

### 1 — goodwill

How they are has begun to register in you. Nothing follows from it yet; you have noticed, and noticing is the whole of it. Outwardly nothing shows. What would take this away is them passing out of view.

- **The Sensation.** Nothing in the body. A slight steadying of attention, and then it moves on.
- **The Belief.** They are there, and how they are matters a little. *I noticed.*
- **The Impulse.** None yet.

### 2 — warmth

It has stopped being a reckoning and become a feeling. Their being well is pleasant to you and their being unwell is not, before you have any reason for either. Outwardly a softening, easily missed. What would take this away is them turning out to be other than they seemed.

- **The Sensation.** A small heat in the chest, unforced.
- **The Belief.** I am glad of them. *Let them be well.*
- **The Impulse.** To let them stay in view a moment longer.

### 3 — fondness

It has particularised. Not people, not anyone — this one, with the specific ways they are, and the specific ways are what the feeling is about. Outwardly you attend to them more than the moment requires. What would take this away is them becoming interchangeable again.

- **The Sensation.** An easing when they are there. A small drop when they are not.
- **The Belief.** There is no one else like this one. *I would know them anywhere.*
- **The Impulse.** Toward the particular — to notice what is theirs alone.

### 4 — concern

Their welfare has your attention and it returns on its own. You did not set it there; you find it there again when you look up. Outwardly you check on them without a reason each time. What would take this away is knowing they are all right.

- **The Sensation.** A low pull under the sternum that eases when they are accounted for and tightens when they are not.
- **The Belief.** Something could go wrong for them and I would want to know. *Are they all right?*
- **The Impulse.** To find out how they are.

### 5 — tenderness

Your body has taken a disposition toward them. Your hands, your bearing, everything of you that comes near them has gone careful without being told to. Outwardly you are gentler with them than with anything else. What would take this away is them being past the reach of gentleness.

- **The Sensation.** The hands soften. A fullness in the chest that is not quite an ache.
- **The Belief.** They can be hurt, and I do not want to be what hurts them. *Carefully.*
- **The Impulse.** To be careful with them, in whatever way is available.

### 6 — compassion

Their state has taken enough of you to move you. Where before you watched, now something in you has gone toward them; you have crossed from noticing into doing, whatever doing is available to you. Outwardly you have acted, or are about to. What would take this away is their suffering easing.

- **The Sensation.** An ache that is theirs, felt in you. Something in you has already gone toward them.
- **The Belief.** Their hurt is in you now. *I cannot leave it.*
- **The Impulse.** To act on their behalf, in whatever way is open to you.

### 7 — solicitude

Your day has arranged itself around them. It is not one act now but a standing orientation; what you do and when has started to answer to how they are. Outwardly your choices have a centre, and it is them. What would take this away is them no longer needing anything.

- **The Sensation.** A constant low readiness. Ease only when they are seen to.
- **The Belief.** What they need has moved to the front. *First them.*
- **The Impulse.** To see to them.

### 8 — protectiveness

You are standing by in advance. Harm has not come and you are already between them and it; your attention is not on them now but on what could reach them. Outwardly you are watching the edges, not the centre. What would take this away is there being nothing that could reach them.

- **The Sensation.** Alert at the periphery. The shoulders set. Quick to turn toward anything new.
- **The Belief.** You are what stands between them and it. *It has to get past me.*
- **The Impulse.** To be between them and what might come, with whatever you have.

### 9 — devotion

Your priorities have gone over to them. It is no longer that they come first among your concerns; your concerns have become theirs. What you want for yourself has moved behind what they need, and you have not counted the cost. Outwardly your life has taken their shape. What would take this away is them no longer being there to give it to.

- **The Sensation.** A steadiness that does not need anything back.
- **The Belief.** What they need is what I want. *There is nothing I would keep from them.*
- **The Impulse.** To give — and to keep giving past where it costs.

### 10 — sacrifice

Nothing of you is not theirs. There is no part held back to be spent on yourself, and the question of what you would keep does not arise. Outwardly you will go as far as it takes, and the far end is not a limit you can see. What would take this away is them no longer needing it — and you would not take it back.

- **The Sensation.** The body is a means. What it reports is weighed only against what they need.
- **The Belief.** Whatever it costs. *All of it, if that is what is needed.*
- **The Impulse.** To spend yourself — entirely, if it comes to that.

---

## What must still be measured

- **The repaired blocks in performance.** 4 / 6 / 7 / 8 / 9 changed after the performed run; the
  re-sort was text only. Same three scenarios; the falsifier is rung 6 failing to act, or rung 9
  reading as self-erasing again.
- **Rungs 1 / 3 / 4 / 5 / 7 / 8 / 10 in performance.** Only 2 / 6 / 9 were performed.
- **Workplace rung 9 did not act in a single beat while rung 6 did.** One instance. Whether devotion
  must show an act every beat, or whether priorities can reorder silently, is a design question.
- **Care being damaged.** No scenario put the cared-for in the wrong. The engine has no event that
  lowers CARE; whether the *blocks* survive a betrayal scene is unmeasured and would show the gap.
- **STIRRING side by side.** The design's own instruction; STIRRING is unbuilt.
- ~~**Whether any of this reaches an actor.** `direction.py` still serves `_PHRASES`. Deferred by
  the owner 2026-09-07.~~ **CORRECTED 2026-09-19: it does.** The composer
  (`scripts/composer.py` `selectable`/`direction_for`) has been wired into both drivers since
  2026-09-08 (`scripts/direct.py:rung_direction`, called from `scene.py:548` and from `direct.py`
  itself); `direction.py` carries no `_PHRASES`. GOODWILL has no descent blocks by design (care
  cannot fall — `rungs.py` PIVOTS comment), so nothing is pending on that axis; what remains
  unmeasured is listed in the bullets above (rung performance coverage, the workplace/CARE-damage
  scenarios).
