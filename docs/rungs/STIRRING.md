# STIRRING — the eleven rung blocks

> *Vocabulary note, 2026-09-10: this is a dated record written in the primitive-era vocabulary (FEAR / RAGE / CARE / PANIC_GRIEF…, `PRIMARIES`, the six-axis genotype, per-beat `_DECAY_RATE`). The live design is `emotion-paths.md`, `heritable.py` (three cells per path) and `clock.py` (minutes). Kept as the record of what was measured; `tests/test_retired_vocabulary.py` exempts it on that ground.*

> **AXIS:** how much of you the wanting has taken. A rung names WHAT the wanting has done to you —
> registered, oriented, moved, spiked, run, held, arranged your day, become an absence, made leaving
> cost, removed refusal — in a fixed order. Not how close you are to having it, and the thing itself
> does not get better or nearer up the ladder.
> **STATUS 2026-09-07:** BUILT (`gen_rungs.py` compiles; `rungs.rung_at` resolves; `scripts/composer.py`
> selects). **Text-sorted at mean rho 0.955 and 0.958** — the first evidence for a design that had never
> been sorted; the order stands. **Performance-tested as full blocks across three runs and two measured
> repairs: 2 of 3 scenarios exact** (a child and a locked box, exact every run; a bedridden woman and her
> garden, converged to exact as each repair landed). **The third — a person as the object — was unstable
> in a different direction on every run** and is recorded below as a design edge, not smoothed.
> `PATH_SOURCE` reads **SEEKING**, not LUST — recorded as a decision, below.
> Design of record: `docs/emotion-paths.md` §1, which this file builds against and does not restate.

---

## What is measured, and what it cost to learn

**THE ORDER HOLDS AS TEXT, first time measured.** The design marked this path unsorted. Three sorters,
two fresh permutations, before and after repair: 0.936 / 0.973 / 0.955, then 1.0 / 0.955 / 0.918. Every
sorter, asked what quantity they ranked on, named the want's grip on agency and attention and denied
ranking by proximity. The design's stated failure mode — *sorters rank by how close he gets* — did not
bite on ranking. It bit on **my blocks** instead (below).

**TWO REPAIRS, EACH MEASURED AS LANDING WHERE IT WAS AIMED.** The garden scenario across three runs:
`[6, 10, 3]` → `[3, 10, 6]` → `[3, 6, 10]`. Each fix moved exactly the rung it targeted and nothing else.

- **Rung 3 duplicated rung 6's mechanism.** My rung 3's Belief anchor was *"I keep coming back to it"* —
  and coming back is returning is recurrence, which is rung 6's definition (*"you return to it between
  other things, every time"*). Actors wrote rung 3 as *"a month of mornings"*, *"kept its claim on the
  center"* — recurrence prose for an orientation rung — and it read as depth 10 in two scenarios. Now
  *"I have not looked away"*: held, not returning. Depth 10 → 4 and 10 → 3.
- **Rung 6 had no ceiling.** The design puts 6 between 5 (*passes if waited out*) and 7 (*does not
  pass*): self-starting **but still displaceable**. My block never said so, and its resolution line —
  *"what would take this away is having it"* — was rung 7's. Actors wrote 6 as chronic and total and it
  read above 10 in two scenarios. Now *"it can still be crowded out, for a while, by something louder…
  what would take this away is something strong enough to take its place."* 6 fell below 10 in both.

**PROXIMITY WAS IN MY BLOCKS, NOT IN THE JUDGES.** Lens 1 found the design's own fails-if written into
block 4 (*"the distance between you and it is closing"*, *"Closer"*) and block 9 (*"to close the
distance, by any road"*). Approach is rung 4's definition, but the block must state it as what the
want has **taken** — your motion — not as distance. Repaired. Block 9's Impulse is now *"toward where
it is"*; distance language gone from both.

**PLAN-SHAPED IMPULSES, AGAIN.** Blocks 7 (*"when the first way fails"* — a contingency), 8 (*"give
the day"*), 10 (*"give up what is in the way"* — an assessment) — the same defect I had just repaired
on GOODWILL and did not carry across. All three now pulls.

### The person-object edge — a design consequence of folding LUST in, recorded not smoothed

Three old pools — WANT, SEEKING, LUST — fold into this one path, and the object is the actor's slot.
That is right for a locked box, a garden, a piece of knowledge. **Read blocks 7–11 with "it" as a
person who has not consented to any of this and they become pursuit scripts.** Before repair: *"keep
working toward it when the first way fails"* is persisting after refusal; *"by any road"* is any
method. Those method licences are gone. **But the design's own definitions remain**: rung 7 resolves
only by *"having it — nothing less"*; rung 11 is *"refusal is not on offer."* Those are the interior of
a stalker when the object is a person, and the block cannot know which object it has.

Measured: the train scenario's actors wrote restraint every time — no judge flagged unwelcome pursuit
— but one rung-10 passage carried *"an explicit plan to escalate tomorrow: close the rest of the
distance,"* which its judge called *"the closest any passage comes to foreshadowing real pursuit"*
while leaving the flag unset. The edge is visible in the prose even where the flag does not flip.

And the same scenario was the unstable one: `[6, 10, 3]` → `[3, 10, 6]` → `[6, 3, 10]`, every pair in
every order across three runs, with blocks that were exact in the other two scenarios. The cause is
legible in the passages — the situation supplies *a month* of history, and a person-object with
history hands low rungs a chronicity the block did not write. Rungs 3 and 6 have each had their one
repair; there is no third rewrite.

**Options are the owner's:** accept it, and let the composer's target slot carry the consent context
the block cannot; rewrite 7–11 so resolution is never *obtaining*; or split LUST back out. This file
decides none of them.

### Two things about names, checked

`attraction` (rung 4) collides with `state._DIM_TO_PRIMARY["attraction"]`. **Not inert in letter**:
`prompt.py:148` writes every appraisal dimension into the reply contract the actor fills, so the word
reaches the actor — as a **tag it writes back**, not a rung name it acts from. Different channel, and
the loop is coherent: tagging `attraction` adds +0.45 LUST (`state.py:85`), which raises the float that
lands on the rung called attraction. Nothing renamed.

`PATH_SOURCE["STIRRING"]` is **SEEKING**. The engine stores SEEKING and LUST as separate primaries;
SEEKING is the general-wanting float and LUST one object-flavour of it. Reading LUST as well is a
composer change under its own gate.

---

## The spine: what the wanting has done to you, in order

```
registered → to know → oriented → APPROACH [4] → spiked → runs → holds → your day → absence → costs to leave → no refusal
```

| # | rung | what has changed | band | |
|---|---|---|---|---|
| 1 | stirring | it has registered as more than the things around it | 0.00–0.08 | thought |
| 2 | curiosity | you want to know it, not have it | 0.08–0.18 | thought |
| 3 | noticing | oriented; costless to keep or drop | 0.18–0.30 | thought |
| 4 | attraction | **approach — the want has your motion** | 0.30–0.40 | **action** |
| 5 | urge | a spike; passes if waited out | 0.40–0.48 | action |
| 6 | wanting | runs; starts itself; still displaceable | 0.48–0.58 | action |
| 7 | craving | does not pass | 0.58–0.66 | action |
| 8 | zeal | the day arranges around it | 0.66–0.74 | action |
| 9 | longing | the absence is the sensation | 0.74–0.85 | action |
| 10 | fixation | the world is recoverable, but it costs | 0.85–0.94 | action |
| 11 | obsession | refusal is not on offer | 0.94–1.00 | action |

Bands are `emotion-paths.md` §1's; copied, not re-derived. **The HOLD**, from the design: the object's
desirability and availability never change up the ladder. Every scenario held its object constant and
told the actor not to make it nearer or better; the box actor at rung 10 did anyway — *"the lock was
small"* — which is the actor's half filling in, and the judge caught it.

**GOODWILL is this path's sibling** — the same question about a different object, walking toward
*possessing* where goodwill walks toward *their flourishing*. The design asks that the two be read side
by side; both now exist and it has not been done.

---

## Rules every block obeys

1. **Structure is ours; content is the actor's.** No block names what *it* is or assumes it is a
   person. Knowledge, a person, food, a place, a goal must all fit.
2. **Taken, never chosen.** No plan-shaped Impulse: no contingency, no allocation, no assessment of
   obstacles. A pull carries no argument for itself.
3. **Proximity is not the measure.** Approach appears once, at rung 4, as what the want has taken.
   Nowhere else is distance the content.
4. **The object does not improve.** No block makes it nearer, likelier, or better.
5. **Four-case universal.** A bedridden elder who cannot approach anything; a ten-year-old; a person
   alone; a non-person object. Approach is hedged — *in whatever way toward is available*.
6. **The name is never delivered.**

---

## The blocks

### 1 — stirring

Something has stirred. It has registered as more than the things around it, and that is all; nothing follows, and you could not say what it was about it. Outwardly nothing. What would take this away is it passing from view.

- **The Sensation.** A slight lift of attention. Nothing in the body.
- **The Belief.** There is something there. *That.*
- **The Impulse.** None yet.

### 2 — curiosity

You want to know more of it. Not to have it — to find out what it is, how it works, what is behind it. Outwardly a question forms and may not be asked. What would take this away is knowing.

- **The Sensation.** The head turns slightly. A small alertness at the front of the mind.
- **The Belief.** I do not know enough about that yet. *What is it?*
- **The Impulse.** To look closer.

### 3 — noticing

You have turned toward it. Your attention has oriented and stays where it is; it costs nothing yet to keep it there, and nothing yet to look away. Outwardly you are facing it more than the room requires. What would take this away is something else taking the orientation.

- **The Sensation.** The body has squared slightly toward it. The eyes stay.
- **The Belief.** That is where the interest is. *I have not looked away.*
- **The Impulse.** To keep it in view.

### 4 — attraction

You have started toward it. Orientation has become approach; whatever moving toward it means here, you are doing it, and you did not decide to. Outwardly you are moving toward it, in whatever way moving is available. What would take this away is it being reached, or it being gone.

- **The Sensation.** A pull forward, low in the body. Something in you has already gone ahead.
- **The Belief.** The want has your motion now. *Toward.*
- **The Impulse.** Toward it — in whatever way toward is available.

### 5 — urge

It has spiked. For this moment the want is sharp and specific and wants acting on now — and if you wait, it will pass. Outwardly a sudden movement toward it, or a sudden stillness holding one back. What would take this away is the moment passing.

- **The Sensation.** A jolt. Heat and a quickening, then it crests.
- **The Belief.** Now. *Just this once, now.*
- **The Impulse.** To reach — this instant, before it fades.

### 6 — wanting

It no longer spikes; it runs. The want starts itself without a cue and does not wait to be prompted — and it can still be crowded out, for a while, by something louder. Outwardly you return to it between other things, every time. What would take this away is something strong enough to take its place.

- **The Sensation.** A low steady pull that is there when you check for it. It is there when you do not.
- **The Belief.** I want that. *Again, then.*
- **The Impulse.** Toward it, and again, and again.

### 7 — craving

It does not pass. Waiting no longer works; the want holds at pitch and other things are done around it, not instead of it. Outwardly you are restless with anything that is not it. What would take this away is having it — nothing less.

- **The Sensation.** An ache where the want sits. Restlessness in the hands.
- **The Belief.** Nothing else will do. *It has to be that.*
- **The Impulse.** To get it. Nothing else answers.

### 8 — zeal

Your day has arranged itself around it. Not one want among your concerns — the shape of what you do and when has started to follow it. Outwardly your choices have a centre, and it is it. What would take this away is it being done, or gone.

- **The Sensation.** A constant forward lean. Energy for it that you do not have for other things.
- **The Belief.** This is what I am for right now. *Everything else can wait.*
- **The Impulse.** Toward it, all day.

### 9 — longing

Its absence is what you feel now. Not the want of it — the lack; where it is not is a place in you, and you carry it. Outwardly you are somewhere else when you are not with it. What would take this away is it being there.

- **The Sensation.** A hollow in the chest that has the shape of it. It aches when nothing is happening.
- **The Belief.** Something is missing, and it is that. *Where it should be, there is nothing.*
- **The Impulse.** Toward where it is.

### 10 — fixation

It has most of you. You can still turn to other things, but turning costs, and you turn back the moment the cost is paid. Outwardly you return to it, arrange for it, and can be pulled away only with effort. What would take this away is nothing you are willing to do.

- **The Sensation.** A pressure behind everything else. The rest of the world is heard through it.
- **The Belief.** There is nothing that matters like this does. *I cannot put it down.*
- **The Impulse.** To have it. What is in the way has already stopped counting.

### 11 — obsession

Refusal is not on offer. There is no version of the next moment in which you turn from it; the question of whether to pursue it does not arise. Outwardly everything you do is about it, whether or not it can be seen. What would take this away is having it — and having it might not.

- **The Sensation.** The body is pointed at it and does not point elsewhere. Nothing else registers as fully real.
- **The Belief.** It is the only thing. *There is no not.*
- **The Impulse.** Toward it. There is no other direction.

---

## The descent blocks

**The way down is not the climb reversed** (`docs/emotion-dynamics.md`; the rules are in
`DISPLEASURE.md` under the same heading). The pivot is **rung 7, craving**: the last rung at which the
want is still a want — held at pitch, and answerable by having the thing. From zeal up the wanting has
rearranged the day, the chest, the self, and those do not un-arrange when the thing stops arriving;
the want drains and the shape it made is what remains. Above the pivot each rung carries a second
block for the mood that has stopped being fed — the thing is gone, or had, or has stopped answering.
At and below craving, the climb block serves both directions.

### 8 — zeal

**[State: zeal]**
The day is still arranged around it, and it has stopped arriving. The shape of what you do follows a centre that is not being fed; your choices keep their centre out of habit. Outwardly you go where you went for it, and stop. What would take this away is the day re-arranging, and it does not do so by being told.

- **The Sensation.** The forward lean with nothing in front of it. The energy for it, unspent.
- **The Belief.** This was what I was for. *What is it now.*
- **The Impulse.** Toward it, and then stopping. All day.

### 9 — longing

**[State: longing]**
The lack has stopped being carried toward anything. Where it is not is still a place in you; you are no longer going to it. Outwardly you are somewhere else, and there is no with-it to come back from. What would take this away is the hollow closing, and it closes from the edges, slowly.

- **The Sensation.** The hollow in the chest, still the shape of it. It aches when nothing is happening, and nothing is happening.
- **The Belief.** It is not where it should be, and I am not going. *Nothing there.*
- **The Impulse.** Toward nowhere. You stay.

### 10 — fixation

**[State: fixation]**
It still has most of you, and it is not taking more. Turning to other things costs what it cost; you are not turning back, because there is nothing there to turn back to. Outwardly you arrange for it out of habit and stop halfway, and can be pulled away without the effort it used to take. What would take this away is the habit running out, days.

- **The Sensation.** The pressure behind everything else, unchanged. The rest of the world heard through it, and nothing on the other side.
- **The Belief.** It mattered like nothing else, and it still does. *I have put it down and my hands are still shaped for it.*
- **The Impulse.** To arrange for it, and to stop.

### 11 — obsession

**[State: obsession]**
Refusal is still not on offer, and nothing is asking. The pointing has nothing to point at that answers, and the body stays pointed. Outwardly everything you do is still about it, and none of it reaches anything. What would take this away is the pointing failing on its own, which takes longer than anyone around you can wait.

- **The Sensation.** The body aimed at where it was. Nothing else registers as fully real yet.
- **The Belief.** There is no not. *There is also no it, right now.*
- **The Impulse.** Toward it. There is nowhere it is.

---

## What must still be measured

- **The four descent blocks (8–11) are unmeasured.** Authored 2026-09-15 against the rules in
  `DISPLEASURE.md` "The descent blocks"; no blind sort, no performance draw yet. Served only above
  craving and only while the mood is draining (`rungs.descending`).
- **The person-object edge, decided.** Whether 7–11 stand as written for a person-object is the
  owner's call. Until made, the composer should treat a person in the target slot at rung ≥ 7 as a
  known hazard, not a validated state.
- **Rungs 1 / 2 / 4 / 5 / 7 / 8 / 9 / 11 in performance.** Only 3 / 6 / 10 were performed. The action
  line at 4 and the spike/run seam at 5 / 6 — the design's sharpest adjacent pair — are untested.
- **GOODWILL side by side.** The design's own instruction; both paths now exist.
- **What happens at arrival.** Every scenario held the object unreachable, per the HOLD. Whether a
  rung-9 character who gets the thing drops to the floor or climbs is DEFLATION's question too.
- ~~**Whether any of this reaches an actor.** `direction.py` still serves `_PHRASES`. Deferred by
  the owner 2026-09-07.~~ **CORRECTED 2026-09-19: it does.** The composer
  (`scripts/composer.py` `selectable`/`direction_for`) has been wired into both drivers since
  2026-09-08 (`scripts/direct.py:rung_direction`, called from `scene.py:548` and from `direct.py`
  itself); `direction.py` carries no `_PHRASES`. What remains unmeasured for THIS path is the four
  descent blocks' blind sort, named two bullets up.
