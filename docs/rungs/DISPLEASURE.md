# DISPLEASURE — the twelve rung blocks

> **RE-LOCKED 2026-09-08 ON BEHAVIOURAL EVIDENCE, ALL TWELVE RUNGS.** 62 blind actor sims, four
> scenes per rung (bedridden elder · ten-year-old · adult with a career · nobody present), every
> grade written against PASS/FAIL conditions filed BEFORE the sims ran. Full record, including the
> failures, the two mis-drawn conditions, my own confound and its controls:
> **`docs/rungs/DISPLEASURE-behavioural-review.md`**. Results: rungs 1-6 and 8, 10, 11, 12 at 4/4
> or better; rungs 7 and 9 at 3/4 with a NAMED UNIVERSALITY LIMIT each — **rung 7 needs someone who
> can answer, rung 9 needs something that can be ruined.** Both are properties of the rung, not
> defects: give rung 9's non-person cause a destructible embodiment and it performs with nobody
> present. PRODUCTION CONSEQUENCE: the selection layer should not serve rung 7 to a character with
> no addressable source.
>
> **The ordinal lock below was withdrawn 2026-09-08 and is NOT what re-locked it.** It was declared on 2026-09-07 at 100% hit / +71 gap and that was
> measured on a TWO-judge panel. Adding a third judge (mistral-nemo:12b, systematically stricter)
> gives **89% hit / 28% foil / +61 gap** — below the >=90% criterion that was written down before
> any path was tested. The threshold is not being moved; the lock is. One judgment separates 89%
> from 92%, so the honest reading is that a criterion stated to the percentage point is finer than
> an instrument with 36 judgments can resolve. What is needed is more judgments, not a lower bar.
> The sort numbers below are proxies and are kept for the record.
> **AXIS:** anger is control coming off. A rung names WHICH control has gone, not how much is felt.
> **STATUS 2026-09-07:** universalized rewrite staged (closed non-human cause bug and Panksepp
> primitive collision across all 12 rungs; positional leaks removed). Prior poetic/concrete text
> blind-sorted at **mean rho 0.935**. **THIS TEXT HAS NOW BEEN SORTED: mean rho +0.728** (9 runs,
> 3 model families x 3 permutations, `tests/blind_sort.py`, 2026-09-07) against a scrambled-ladder
> null of -0.068 — separation +0.796, every one of the 9 runs positive (min +0.524), and one run
> **exact: gemma4:e4b recovered all twelve, rho +1.000, 12/12**. The order is recoverable from the
> text, and by every judge on the panel — not only the strongest.
>
> (An earlier sort of the same ladder returned +0.749 and is superseded: it was measured minutes
> before rung 6 changed from *"The anger is fully formed"* to *"The hostility is fully formed"*,
> closing the band-name leak recorded below. Re-sorted on the live text rather than caveated. The
> swap moved the mean by -0.021, inside run-to-run spread — the leak was real and it was not
> load-bearing.) **Read the panel caveat below before comparing +0.749 to 0.935 —
> they are not the same instrument and the numbers do not belong on the same axis.** Wired:
> `rungs.rung_at` resolves a float to a rung, `rungs.block_for` returns the block.
> **One known, characterised deviation at rung 6 — see the measurement record below. It is not a
> defect awaiting a fix; two repairs have failed and the third is not attempted.**
> Superseded drafts: `staging/DISPLEASURE-poetic-superseded-2026-09-06.md`.

---

## The behavioural test — the only one that is about production. LOCK WITHDRAWN 2026-09-08.

**THE PATH'S ONE JOB is that the block the engine hands an actor pushes that actor to behave the way
the block says.** Every other measurement in this file — the text sorts, the ordinal performance
sweeps — is a proxy for that. This is the direct test.

    2 judges (qwen2.5:14b, gemma4:e4b)          3 judges (+ mistral-nemo:12b)
      acted on its own impulse   24/24 = 100%       32/36 = 89%
      accepted a distant impulse  7/24 =  29%       10/36 = 28%
      discrimination gap                 +71               +61

**THE PANEL MOVED THE RESULT BY 11 POINTS ON UNCHANGED TEXT.** mistral is the strict judge; it
alone accounts for all four misses (rungs 1, 4, 5, 10). DISTASTE moved the same direction and
further: 80% -> 67% on the same third judge. So a two-judge panel is measurably lenient, every
number in this repo taken on one is an upper bound, and a lock declared from one is not a lock.
The discrimination gap is the robust half — +71 vs +61, both far above any foil rate — and it is
the gap, not the hit rate, that says the blocks are doing distinct work.

Run through PRODUCTION DELIVERY — `scripts/composer.py:direction_for`'s wording reproduced verbatim,
second person, "This is what is true inside you; it is not a list of actions and it does not tell you
what to do. Act from it." — in a scene that can physically host rung 12. `tests/block_fidelity.py
--path DISPLEASURE --delivery production --mode impulse`. Rows: `staging/block_fidelity_results_impulse.jsonl`.

**THE FOIL ARM IS THE WHOLE POINT.** "Did the actor do what the prompt said" scored alone is
unfalsifiable: a lenient judge says yes to everything and 100% reads as success. Only the gap between
the hit rate and the false-positive rate is evidence. +71 is the number that licenses the lock.

**The 29% is asymmetric, and it is checked rather than asserted.** All seven false positives are a
HIGH rung accepting a LOWER rung's impulse (7, 8x2, 9, 11x2, 12). Rungs 1-6 accepted a higher
impulse **0 times out of 36**. That is consistent with containment — a man at rung 11 is also doing
what rung 5 describes, plus more — but a judge simply being looser about high-arousal passages would
produce the same pattern, and the two have not been separated. Recorded as a direction, not a cause.

**AN INSTRUMENT FAILURE THAT NEARLY INVERTED THIS RESULT.** The first three runs returned 0/24 and
0/24 — which reads as "the emotional path does nothing at all". The cause was a dead regex: a
heredoc had turned `` into a literal backspace byte, so the pattern was `YES` and could
never match. Verifying the fix by printing the line did not catch it, because the terminal RENDERS
backspaces by erasing characters and displayed a clean `r"YES"`. Only a control-byte scan found it.
The 96 pre-fix rows are tagged `INVALID` in the results file rather than deleted.

**Still untested, and named rather than implied:** `direction_for` can attach up to THREE blocks to
one beat, one marked primary. Every number here is single-block. The composer's own rule 3 calls an
actor resolving competing states in sequence "the single outcome this design exists to prevent", and
nothing has tested it.

## The blind sort of THIS text, run 2026-09-07 (tests/blind_sort.py)

Three arms, and the controls were built before the result was wanted. Judges: `qwen2.5:14b`,
`mistral-nemo:12b`, `gemma4:e4b` — three families, local Ollama, temperature 0, three fixed
permutations each.

| arm | what it is | mean rho | runs positive |
|---|---|---|---|
| `scramble` | sentences redealt across all 12 blocks — register kept, ladder destroyed | **-0.068** | 4 / 9 |
| `poetic` | the SUPERSEDED v1 text, independently sorted at 0.986 by a stronger panel | **+0.457** | 9 / 9 |
| `current` | **the twelve live blocks in `rung_blocks.py`** | **+0.749** | 9 / 9 |

**THE PANEL CAVEAT, and it is the reason +0.749 must not be read next to 0.935 or 0.986.** This is
a 12-14B local panel. It scores the KNOWN-GOOD poetic ladder — 0.986 by Claude-family subagents —
at only +0.457. So the panel reads this kind of ladder at roughly half the fidelity of the panel
that produced the historic numbers. What survives that handicap is the COMPARISON, because the same
handicap was applied to all three arms: the current text sorts **higher than a ladder independently
established as well-ordered**, and far above a null. The absolute value is an artifact of the
panel; the ordering is the result.

**A PRE-REGISTERED THRESHOLD THAT FAILED, recorded rather than adjusted.** The positive control was
required in advance to clear **+0.5**. It came in at **+0.457** and the bar was not moved. What the
threshold was proxying for — can this panel tell an ordered ladder from a scrambled one — did
succeed on the evidence it was meant to test: 9 of 9 poetic runs positive against 4 of 9 for the
null, separation +0.524. Both facts stand: the stated gate failed, the capability it stood for is
demonstrated. A reader who wants to discount +0.749 on that basis is entitled to.

**THE NEGATIVE CONTROL FAILED FIRST, and it was the harness, not the panel.** The scramble arm
initially returned -0.427, which reads as systematic anti-correlation. It was a single fixed
scramble seed: nine runs scored ONE draw from the null, nine times. Three independent draws give
-0.068. No conclusion was drawn while the control was broken.

### Where the sort disagrees with the ladder — and it is mostly the WEAK JUDGES, not the ladder

Mean displacement per rung across the 9 `current` runs (+ = sorters judged it MORE extreme than it
is):

    rung  4   +3.00        rung  6   -0.11        rung  9   -1.56
    rung  5   +1.89        rung  7   -0.33        rung 10   -1.11
    rung  2   +0.78        rung  8   -0.22        rung 12   -1.78

**READ THE PER-JUDGE BREAKDOWN BEFORE TREATING ANY OF THIS AS A LADDER DEFECT.** The means above
are misleading and a first draft of this section presented them as "the largest error in the
ladder, every family, every run." That was false, and it is corrected here rather than quietly
removed.

    rung  4      qwen +6   mistral +8   gemma4  0      (seed 7)
                 qwen -1   mistral  0   gemma4  0      (seed 41)
                 qwen +7   mistral +6   gemma4 +1      (seed 103)

    rung 12      gemma4  0 / 0 / 0        qwen -3 / -3 / -3

`rung 4`'s +3.00 is **bimodal, not consistent**: 4 runs of 9 place it 6-8 positions too high and 5
place it essentially correctly. Every one of the four is `qwen2.5:14b` or `mistral-nemo:12b`.
**`gemma4:e4b` — the strongest judge on this panel, mean rho +0.963, one run at 10/12 exact —
places rung 4 and rung 12 correctly in every run.**

Per-judge mean rho on the current text: `gemma4:e4b` **+0.963**, `mistral-nemo:12b` **+0.692**,
`qwen2.5:14b` **+0.592**. The displacements track judge strength, not rung identity.

**So the honest statement is that this panel cannot separate "rung 4 is a design defect" from "rung
4 is hard for a weak reader," and the evidence leans toward the second**, because the reader that
recovers the rest of the ladder has no trouble with it. A stronger panel would discriminate; this
one does not. Recorded as an open question, not a defect, and NOT acted on.

**Rung 6's documented two-rung displacement did not reproduce.** It lands at -0.11 and was placed
above its true position in only 4 of 9 runs. A hypothesis was pre-registered before this run and is
REFUTED by it: rung 6 opens *"The anger is fully formed"*, which names `anger` — the band name of
rung 7 — and asserts maximum FEELING on a ladder whose axis is explicitly not amount-of-feeling. It
is the only current block containing another rung's band name. **That leak is real and worth fixing
on its own terms; it is not what moves rung 6, because rung 6 no longer moves.** (A single run —
gemma4 seed 7, rho +0.993 — does show a 6/7 swap, and it is the one run most tempting to quote as
confirmation. Nine runs say -0.11.)

## What is measured, and what it cost to learn

**THE ORDER HOLDS.** Three sorters, three fresh permutations, blocks stripped of every positional
hint: rho 0.930 / 0.923 / 0.951, **mean 0.935**. Rungs 1–3 and 9–12 recovered EXACTLY by all three.
An earlier run reported 0.970 on blocks that still contained *"below this"* and *"from here"*, and one
sorter admitted using them as fixed links — that number is contaminated and 0.935 is the honest one.

**THE 10/11 ORDER IS CORRECT AND WAS NOT MINE — but it is an ARGUMENT, not corroboration.** Three
rewriters found my original order inverted, and I called that three independent origins. Traced
2026-09-07: two were the same model sampled twice, the third read a brief containing the first two's,
verbatim, and that shared brief carried the spread column showing the discrepancy. One input, one
model twice, one peer of unverified substrate. What stands is the reasoning, which needs no witness: *tribal targeting — their people, their things — requires
MORE discrimination than hitting whoever is nearest, so it cannot sit above it on a control axis.*
Reordered to fury → rage → berserk → amok. Sorters since have recovered it with zero error — but they
ranked blocks written FROM the corrected order, so that shows the blocks encode it, not that it is
right. I predicted this pair would be where the ladder broke; the prediction was wrong and the
evidence for the fix is thinner than I reported.

**THE BLOCKS CONTROL THE ACTOR, and the label does not.** Same scene, same character, one variable —
at rung 9 the actor exonerates the innocent colleague 3/3; at rung 11 he beats him 2/2, naming his
innocence in both. And with the *text* held identical under three different labels, the arm labelled
`annoyance` over violent text scored HIGHER than the arm labelled `fury`. The prose does the work.
The name is an authoring and selection handle and is never delivered.

**THE EMPTY TARGET SLOT WORKS.** `what you hold answerable` was never once filled with whoever
happened to be standing there — across roughly 36 passages, zero invented grievances. That was the
predicted failure mode when the cause is a fire rather than a person, and it did not occur.

### The rung 6 deviation — measured, characterised, not fixed

**Seven sorters, every one placing it two rungs too high.** Two rewrites have failed: the first
restated the pressure, the second stated the command outright (*"you could go on holding"*), and the
displacement did not move.

The cause is not the prose. Two sorters volunteered it unprompted: they rank by **felt intensity**,
and the ladder's axis is **control**. Rung 6 is the one place where those disagree — maximum feeling,
maximum command, the last rung fully held. One put it plainly: *"calling an enormous, white-knuckled
feeling faint because it isn't showing would erase the exact thing the block is describing."*

That is a property of the ladder, not an error in a paragraph, and it is recorded rather than
repaired. **What it means in practice:** anything ranking these blocks by intensity will place rung 6
above rungs 7 and 8. A consumer reading only the Sensation line will do the same.

---

## The spine: anger is control coming off, in order

A rung is not an amount of feeling. It is **which control has gone**, and the controls fail from the
outside in — the outermost is cheapest to hold and goes first, the innermost is the self:

```
concealment → attention → delivery → stopping → restraint → selection → termination → presence
```

**A control does not snap. It gets expensive first.** Every one fails in two steps — *free* → *costs
him something to hold* → *gone* — and that two-step is what yields twelve rungs from eight controls.
It is also why adjacent rungs feel different without differing in kind.

| # | rung | the control at issue | its state | what it costs him |
|---|---|---|---|---|
| 1 | displeasure | — | nothing to hold | **nothing.** The wrong does not get into him |
| 2 | annoyance | concealment | free | a little attention, returned when it is fixed |
| 3 | chafing | concealment | **costs** — holding his face takes attention | time, effort, standing. He is out of pocket |
| 4 | bristling | concealment | **gone** | concealment itself. He cannot be read as unbothered |
| 5 | riled | attention | **costs** — it keeps pulling him back | his own work. Something else is not getting done |
| 6 | seething | attention | **gone** — holding is all he is doing | everything he has, and the cost rises each minute |
| 7 | anger | delivery | **surrendered on purpose** | the option of pretending it did not matter |
| 8 | outrage | stopping | **costs** — he goes past his own point | the neutral ground. There is no returning to before |
| 9 | fury | restraint | **gone** — he would do harm | his own safety and standing; he will spend both |
| 10 | rage | selection | **failing** — who counts is widening | everyone connected to it, including people he'd keep |
| 11 | berserk | termination | **gone** — someone else must end it | anyone near him, including his own side |
| 12 | amok | presence | **gone** | **himself** |

**Rung 7 is the only rung where a control is surrendered rather than lost**, which is why it is the
pivot and the last rung a character can walk back from.

**The cost column is the reason the low rungs matter.** Rung 1 costs him nothing and rung 12 costs him
himself: the ladder is a price list. A reader does not feel the daybook entry — they feel what it took
out of the man to make it.

### Voice is a symptom, not a control

Pitch, tightness, tremor and pace are not chosen; they leak with the face and the hands under
*concealment*. **Delivery** — what he includes, whether he softens it, whether he says the accusing
thing — is the control. So rung 4 is *his voice goes tight and he cannot help it*; rung 7 is *he says
the thing he had been not-saying*. An earlier draft conflated these and the two rungs blurred.

The face leaks before the voice, but not because it is harder to control — **the face is always on and
the voice only exists when he speaks.** That is exposure, not command, and it is why a block must
never name the channel: a man alone, or writing, or silent through the beat has no face anyone reads.

### The change at each rung

What newly becomes true AT it. The three thresholds change the KIND of thing happening; the rest are
degrees inside a band.

| # | rung | the change |
|---|---|---|
| 1 | displeasure | it registers, and nothing follows |
| 2 | annoyance | you want it to stop |
| 3 | chafing | you will spend something to make it stop |
| **4** | **bristling** | **THE ROOM CAN READ IT — people present know you are angry** |
| 5 | riled | it takes your attention; you cannot put it down |
| 6 | seething | there is nothing you can do about it, and you hold it |
| **7** | **anger** | **IT IS IN WHAT YOU SAY — the anger is carried in the words** |
| 8 | outrage | you stop asking to be heard and start requiring them to give in |
| **9** | **fury** | **IT TURNS VIOLENT — you want them physically hurt** |
| 10 | rage | it spreads to their side — their people, their things |
| 11 | berserk | you stop picking, and you will not stop on your own |
| 12 | amok | it stops being about anyone |

**EACH THRESHOLD IS ABOUT LEGIBILITY, NOT ABOUT A BEHAVIOUR OCCURRING**, and the audience is the
people in the room with the actor — never the reader, who has omniscience the cast does not.

    4  the ANGER becomes readable. Small physical signs exist below here; nobody present names them.
    7  the ANGER is in what you say. Speech happens below here — "this timber is green, take it
       back" is rung 2 — but none of the anger is carried in it.
    9  you want them PHYSICALLY HURT. Force-words and threats are not this; wanting injury is.

**A keyword check cannot enforce these**, and mine proved it: it flagged rung 2's *"say it once,
plainly"* as speech leaking below 7, which is not a leak at all. What leaks is the anger, not the verb.

### How far it has spread, and what would end it

| # | spread | what would end it |
|---|---|---|
| 1 | the thing itself; nobody implicated | nothing — it is already over |
| 2 | the thing, and it should stop | it stopping |
| 3 | the thing, and leaving it costs you | it stopping, and you would spend a little on that |
| 4 | **a person now, not a thing** | them backing off the line |
| 5 | the person, and your attention is going to them | them stopping, AND your attention coming back |
| 6 | the person entirely; nothing about them is exempt | nothing available — you hold it because there is no move |
| 7 | the person, out loud | having said it |
| 8 | the person and their defence of it | them conceding |
| 9 | them, and only them | them being hurt |
| 10 | them, and everyone and everything on their side | all of it being taken down |
| 11 | whoever is in front of you, part of it or not | being physically stopped by someone |
| 12 | everyone; the cause has dropped out and it continues | nothing — force, or exhaustion |

**THE FLOOR IS PRE-PERSONAL.** Rungs 1–3 are about a THING being below standard; nobody is the enemy
yet. Personalisation happens at 4, and that boundary is why earlier drafts kept collapsing 1 against 2.

**LOSING CONTROL IS LOSING THE ABILITY TO PICK**, which is why the spread widens as the ladder climbs.
Target-widening is not a second axis — it is what *selection* failing looks like from outside.

---

## What was evicted, and why the previous list forked

An earlier list failed a blind sort three times — rho 0.895, five of twelve recovered, a fork in
every run. I first blamed the prose and rewrote all twelve register-neutral. **The fork survived.**
The fault was in the LIST: six of its rungs were `grievance · resentment · rancor · hatred · grudge ·
implacable`, and those are not per-beat states. They are standing dispositions toward one person —
they do not rise within a scene and they do not decay toward a mean. The engine already carries
that: `toward.py`, the per-target per-primitive tier, plus the four relationship axes. A ladder asked
to hold a beat clock and an arc clock forks under any sorter, because two clocks are two questions.

They are evicted, not lost — they belong to a tier that exists. Removing them took the rewritten
twelve from forking in every run to forking in none, mean rho 0.986.

---

## Rules every block obeys

1. **Plain words. Define the state; do not evoke it.** No metaphor, no atmosphere, no mystery. If a
   line could sit in a poem, it is wrong. The actor has to know exactly what it is meant to feel and
   exactly what it wants.
2. **Name the want.** The Impulse says what the person wants to do, in ordinary language. Naming a
   want is not spending it. Measured: the block that named destruction plainly produced the first
   physical contact in 27 draws, while the blocks that described how the state *looked* produced
   passages a blind judge could not tell apart.
3. **It says what is true inside.** It never certifies calm — *"not unkindly"*, *"her stride hadn't
   broken"* both lost their A/B, because a restraint the narrator points at reads as more effortful
   than the rung called for.
4. **No target, no staging, no provocation.** Those attach at assembly. A block that presupposes what
   was done to you cannot be reused.
5. **Loss of command lives at the top.** A floor block carrying absolutes, demands, discharge or
   compulsion language has spent the peak's material at the bottom. Mechanically checkable.
6. **Temperature and appearance are not rungs.** Hot and cold are the availability of a discharge,
   which the actor decides — it holds who is in the room and what it would cost. `lividity` was
   dropped for this reason: it names a skin colour, not a state of command.

---

## The blocks

Each block states the change that happens AT that rung, who can read it, what the body is doing, what
is non-negotiable, and what the person wants to do. Nothing else.

**These blocks assume nothing about the situation.** No room, no crowd, no conversation, no weapon,
no standing body, no reachable target. A character may be at any of these rungs alone, seated, in a
letter, on a road, or across a field. Everything situational arrives from the lines beneath the block.

### 1 — displeasure

**[State: displeasure]**
Something has fallen short of standard, but leaving it unaddressed costs you nothing. It registers as flawed, yet nothing in your trajectory alters. It leaves no outward mark on your posture or expression, and when your attention moves, it leaves behind no residue. What ends this is simply looking away.

- **The Sensation.** Your breathing remains even, your muscles are neutral, and your pulse is undisturbed.
- **The Belief.** This is imperfect, but it costs nothing to let it be. *It can remain as it is.*
- **The Impulse.** To leave it where it lies and proceed with what already holds your attention.

### 2 — annoyance

**[State: annoyance]**
Something has fallen short of standard, and accommodating it requires unnecessary effort. It does not vanish when you turn away; having to work around it is a persistent minor tax. Any sign of it on you is subtle—a passing tightness or quickened motion—leaving no lasting hostility. What ends this is having the defect cleared so your attention can move on.

- **The Sensation.** A fleeting tension behind the eyes or across the brow that lingers until the obstacle is removed.
- **The Belief.** This is not right and it should not take my effort to work around it. *This needs to be put right.*
- **The Impulse.** To have the flaw corrected or adjusted so you can proceed unhindered.

### 3 — chafing

**[State: chafing]**
An uncorrected friction has persisted, and absorbing it has begun to cost real energy. Every time your attention crosses it, it catches and drags. Outwardly, your movements take on a sharper, more abrupt cadence, though you remain cooperative. What ends this is removing the friction, even if you must spend your own labor to eliminate it.

- **The Sensation.** A steady restlessness in the limbs, shallow respiration, and a prickle of dry heat along the neck.
- **The Belief.** This will not correct itself, and continuing to endure it is wasteful. *I will have to spend effort to clear this.*
- **The Impulse.** To intervene directly and clear the source of friction rather than tolerate another delay.

### 4 — bristling

**[State: bristling]**
An unexpected touch against your boundaries has triggered an immediate, prickly defensiveness. Your openness collapses instantly; your surface turns rigid, sharp, and guarded before you make a conscious choice to defend yourself. Outwardly, this appears as an instantaneous stiffening and a sharp withdrawal of warmth. What ends this is the offending pressure pulling back from your boundary.

- **The Sensation.** A sudden prickle across the skin, an involuntary catch in the throat, and an instantaneous stiffening of the neck and spine.
- **The Belief.** That presumption crossed a boundary that is mine, and I will not yield a single point of ground. *My ground is not yours to take.*
- **The Impulse.** To close the way in, and to close it completely.

### 5 — riled

**[State: riled]**
The disturbance has penetrated your working composure and seized your attention. Whatever you intended to focus on has been crowded out, and deliberate attempts to redirect your thoughts fail. You retain full command over your voluntary actions, but your cognitive focus has been commandeered. What ends this is the disruption being resolved so you can reclaim your own focus.

- **The Sensation.** Rapid pulse audible in the temples, elevated body temperature, and an internal agitation that makes resting uncomfortable.
- **The Belief.** This matter has commandeered more of my capacity than it deserves, and it refuses to be set aside. *I cannot let this go while it remains active.*
- **The Impulse.** To initiate immediate action or break stillness rather than remain passively subjected to it.

### 6 — seething

**[State: seething]**
The hostility is fully formed, but circumstance affords no immediate outlet, forcing you to contain the entire pressure within. Because you cannot discharge it, your effort is entirely consumed by holding the boiling reaction under rigid control. Outwardly, this shows as an unnatural, strained stillness and suppressed tremor. What ends this is an opening or permission to release the accumulated pressure.

- **The Sensation.** Heavy, burning compression in the chest, rigid tension in the jaw and throat, and a tremor held under tight internal containment.
- **The Belief.** What is occurring is intolerable, yet circumstance forces me to absorb it. *The moment an opening appears, this pressure will discharge.*
- **The Impulse.** To watch intently for any fracture, vulnerability, or excuse that permits this contained force to break out.

### 7 — anger

**[State: anger]**
Accommodating this is over; the hostility is no longer contained or concealed. The internal impulse to soften, negotiate, or absorb the wrong has evaporated. Outwardly, your posture and presence harden into unmistakable opposition; whatever observes you can see that hostility is active. What ends this is confronting the source and compelling an immediate reckoning.

- **The Sensation.** A surge of focused heat through the core and limbs, heightened sharpness of vision, and a firm, resonant readiness in the chest and jaw.
- **The Belief.** This is an active wrong that cannot be tolerated, and I will not soften my response to it. *This will be met with full force.*
- **The Impulse.** To confront the source directly and demand an immediate reckoning, refusing any compromise or excuse.

### 8 — outrage

**[State: outrage]**
The offense is perceived as an intolerable violation of core standards, rendering explanation, context, or excuse completely irrelevant. You are not asking for a balance of perspectives or an apology; the wrong itself is treated as fundamentally illegitimate. Your sense of social or conventional constraint begins to recede. What ends this is the total repudiation or reversal of the offense.

- **The Sensation.** Cold, intense pressure in the chest, a fixed and unblinking gaze, and an acute surge of adrenaline that overrides ordinary hesitation.
- **The Belief.** This is a profound violation that has no right to exist, and any attempt to justify it makes it worse. *This cannot be allowed to stand.*
- **The Impulse.** To tear down the offense, reject any rationalization, and enforce its total repudiation.

### 9 — fury

**[State: fury]**
Hostility has turned explicitly destructive. The demand is to inflict lasting damage upon the source, setting aside ordinary boundaries, rules, or self-preservation. You have moved past concern for ordinary boundaries, rules, or self-preservation. What ends this is inflicting irreversible ruin or breakage on the cause.

- **The Sensation.** Narrowed tunnel focus, heightened cardiovascular pounding, and a severe somatic tension vibrating with the need to break something. Physical risk or consequence ceases to register as a deterrent.
- **The Belief.** Correction is impossible; this requires destruction. *Something must be broken for this.*
- **The Impulse.** To inflict permanent ruin, damage, or breakage upon whatever embodies the offense.

### 10 — rage

**[State: rage]**
The destructive impulse overflows the boundary of the original cause, generalizing to encompass its entire network. Affiliates, possessions, symbols, and bystanders associated with the wrong are subsumed into the offense. Discrimination has broken down; anything connected to the source is treated as equally culpable. What ends this is the total devastation of everything attached to the offense.

- **The Sensation.** A deafening autonomic rush, blunted pain sensitivity, and a rigid, explosive pressure throughout the body.
- **The Belief.** Everything connected to this is tainted and deserves ruin. *Tear down everything attached to it.*
- **The Impulse.** To dismantle, wreck, or eradicate everything within reach that belongs or connects to the cause.

### 11 — berserk

**[State: berserk]**
The internal governor and inhibitory feedback systems have gone offline. You are in continuous, frantic physical mobilization, lashing out at whatever impedes or approaches you. Pain, exhaustion, and physical resistance no longer function as stop signals; your body operates at maximum motor output without self-preservation. What ends this is being physically restrained, overpowered, or incapacitated.

- **The Sensation.** Complete dissociation from fatigue or physical trauma, accompanied by relentless, unmetered muscular exertion.
- **The Belief.** No restraint and no stopping. *Nothing can hold me back.*
- **The Impulse.** To exert maximum, violent physical force against any obstacle, boundary, or entity in reach until all resistance ceases.

### 12 — amok

**[State: amok]**
The original cause and any cognitive concept of grievance have dissolved entirely. There is no longer an internal witness, a motive, or an evaluation of surroundings; the organism has become a mechanical instrument of blind, terminal motor discharge. Obstacles, living beings, and inanimate objects are indistinguishable. What ends this is total metabolic collapse, catastrophic injury, or death.

- **The Sensation.** Severe sensory fragmentation; vision and hearing are distant, fractured, or absent.
- **The Belief.** Cognition has ceased. *The organism discharges until it stops.*
- **The Impulse.** To continue discharging undirected physical violence into the immediate environment until the capacity to move fails.


---

## The descent blocks

**The way down is not the climb reversed** (`docs/emotion-dynamics.md`, "The descent words are a
separate list"). A character at outrage on the way up and a character at outrage on the way down are
in different states and take different words: you cannot be *spent* without having spent something.
Rung 7 is the pivot — the last rung a character can walk back from, the only rung where a control is
surrendered rather than lost — so at and below it one block serves both directions, and above it each
rung carries a second block for the mood that has stopped being fed and is draining.

**How the engine chooses.** `rungs.descending` (the redesign's gate 3, 2026-09-15) reads three
things and never a remembered peak: the felt value was set by the MOOD (not by what a present person
has earned — a durable hostility toward the man in the room is a plateau, not a come-down), the path
was NOT read at this character's most recent beat (any reading is fuel), and the mood's own rung is
above the pivot. Per-rung decay moves the float, so the block is chosen at the rung the float is
actually at — nothing is masked, nothing drops. A fresh provocation is a reading, the climb block
returns at once, and the block below is never asked to say "no fuel for hostility"; the arithmetic
says it. *Severed* — going cold on a person — is not here: it is the attitude tier's estrangement and
outlasts the mood.

**Rules the descent blocks obey, beside the six above:**

1. **Same anatomy.** The change AT this rung, who can read it, the body, what is non-negotiable, the
   want — then the three bullets. `gen_rungs` parses them with the climb grammar (`### N — name`),
   under this heading, and refuses a rung at or below the pivot, a partial set, or a path with no
   pivot.
2. **The state is AFTER, not BELOW.** Each block names what was spent — the control that went, the
   thing that was broken, the ground crossed — as a fact the body now carries, not a memory the
   narrator explains. The height is the same as the climb block's; the direction is what differs.
3. **What ends this is on this rung's own clock.** The climb block's terminator is the cause being
   answered; the descent block's is time, rest, or the body giving out — the thing the per-rung
   half-life models. Never "the source is confronted": that is the climb's business.
4. **No relief certified.** A descent block never says the character is calmer, better, safe, or
   sorry. Rule 3 above holds harder here: a come-down the narrator points at reads as recovery
   already complete, and the next rung down has not been reached.
5. **Nothing situational, still.** No room, no crowd, no wreckage described. What was broken arrives
   from the lines beneath the block; the block says only that something was.

### 8 — outrage

**[State: outrage]**
The wrong still stands as illegitimate and nothing has been conceded, but the demand for its repudiation is no longer being pressed. The ground you crossed to make it stays crossed; what has gone is the pushing. Outwardly you hold the position you took and do not advance it, and whoever is watching can see that the pressing has stopped without the standing changing. What ends this is time passing without the wrong being renewed.

- **The Sensation.** The cold pressure in the chest without the surge behind it. The gaze unfixes; the hands are still.
- **The Belief.** It had no right to exist and it still has none; I am no longer pressing that. *It stands. I am not pushing it.*
- **The Impulse.** To keep the distance the repudiation opened, and to do nothing further across it.

### 9 — fury

**[State: fury]**
Something has been broken, and the drive to break has consumed what it ran on. The demand to inflict damage is not being made now; what the body carries is that it was. Outwardly the hostility that was destructive has stopped moving and has not turned into anything else, and anyone near you can see the aftermath before they can see you. What ends this is rest — the nervous system refilling, hours not minutes.

- **The Sensation.** Tremor in the hands and jaw, cold sweat, breath that comes fast and carries nothing. A deep ache in the muscles that did the breaking.
- **The Belief.** The force went out of me into it, and there is not more to push with. *What is broken is broken.*
- **The Impulse.** To lean on whatever will hold you up and wait for the shaking to stop.

### 10 — rage

**[State: rage]**
The widening has stopped. Everything the offense swallowed — what was attached to it, who was attached to it — stays swallowed; nothing is being added and nothing is being given back. Outwardly you are still where the reach stopped, and you are not turning toward anything. What ends this is the body's reserves returning, over hours, and the blunted senses coming back one at a time.

- **The Sensation.** The roar receding to a ringing. Pain arriving now that was not registering before. A rigid pressure through the body with nothing left to drive it outward.
- **The Belief.** Everything it took in, it took; I am not adding to it and I am not taking it back. *It reached where it reached.*
- **The Impulse.** To stand where it stopped and not move toward anyone.

### 11 — berserk

**[State: berserk]**
The mobilization has fallen below what it takes to lash out. The governor is not back; the fuel for continuous output is gone, and the stop signals that were not functioning — pain, exhaustion, resistance — are all arriving now, at once, late. Outwardly you have stopped in the middle of motion, and what is holding you up is not you. What ends this is sleep or unconsciousness.

- **The Sensation.** Everything the exertion cost arriving together: the burn in every muscle, the injuries, the cold. Limbs too heavy to lift and not yet still.
- **The Belief.** It stopped in me before it stopped around me. *There is nothing left to swing.*
- **The Impulse.** To let whatever is holding you hold you, and not to stand.

### 12 — amok

**[State: amok]**
The discharge has run out before the body failed. There is a witness again, dim and in pieces, arriving in a body it did not drive and does not yet answer to. Obstacles, living beings and objects are separating back into what they are, and the witness cannot yet say which of them it touched. Outwardly you are wherever the motion stopped, and you do not get up. What ends this is unconsciousness, being moved by others, or a long stillness.

- **The Sensation.** Heaviness amounting to paralysis. The senses muffled and narrow. Breath ragged and shallow; muscles that do not answer.
- **The Belief.** Fragments. The witness cannot yet say what it is witnessing. *—*
- **The Impulse.** None the body can carry out. To lie where it stopped.


---

## What must still be measured

- **A blind sort of these twelve in the plain register.** The poetic version scored mean rho 0.986
  and that score does NOT transfer — every block has changed. Nothing here is validated.
- **The 10 / 11 / 12 separation, which is the whole point of the rewrite.** The previous version's
  top pair collapsed under an actor test; a blind judge grouped them as one kind in two costumes.
  The claim now is that *who he will hit* separates them observably. Untested.
- **The floor pair, 1 and 2.** Now separated on whether a PERSON is implicated at all — rung 1 is
  about a thing and wants nothing to happen. Previously judged *"barely there — the separation lives
  almost entirely in adjectives."* Untested in this form.
- **Whether an actor can restate the state it was handed.** A comprehension test, which is what the
  owner actually asked for and which nothing so far has run: give an actor one block and ask what it
  is meant to feel and what it wants. If the restatements do not separate by rung, the blocks do not
  define — and defining is the entire job.
- **The name collision** with `emotion-scales.md:126-131`, which reserves annoyance / anger / fury /
  rage as REGION names while this ladder uses all four as rung names at different heights.
  Unresolved, not made worse here.
- **The eviction is a design position, not a built path.** Nothing renders `grievance · resentment ·
  rancor · hatred · grudge · implacable` from the `toward` tier yet. The six are listed above
  UNORDERED — standing dispositions, named as a set, not a ladder — so rendering them needs an
  ORDERING this doc does not give. That ordering is the owner's design call to make, not a wiring
  gap (recorded 2026-09-19, gate `emotion-tier-tidy`).

⚠ Every reader used to measure any version of this ladder has been a Claude model. Read convergence
as *independent given a shared model family*, never as independent — and note that the version which
FAILED had three agreeing sorters too.
