# SELF-REGARD — the eleven rung blocks

> *Vocabulary note, 2026-09-10: this is a dated record written in the primitive-era vocabulary (FEAR / RAGE / CARE / PANIC_GRIEF…, `PRIMARIES`, the six-axis genotype, per-beat `_DECAY_RATE`). The live design is `emotion-paths.md`, `heritable.py` (three cells per path) and `clock.py` (minutes). Kept as the record of what was measured; `tests/test_retired_vocabulary.py` exempts it on that ground.*

> **AXIS:** how much of you your own standing has taken. GOODWILL's exact mirror — that one consumes
> you outward and ends at *sacrifice*; this consumes you inward and ends at *apotheosis*. A rung names
> WHAT the estimate of yourself has done — counted, drawn a line, attached to a deed, outweighed the
> business, demanded upkeep, stopped checking, demoted others to audience, exempted you from the
> rules, emptied others of insides, replaced the world, replaced you.
> **STATUS 2026-09-07, corrected 2026-09-19:** BANDS and BLOCKS BUILT and compiled. **SELECTABLE by
> the composer since 2026-09-08** — `PATH_SOURCE`, the lookup this line's "NOT SELECTABLE" reasoning
> depended on, was removed the same day the redesign made the paths themselves the stored state
> (`rung_blocks.py:124`; `scripts/composer.py` `selectable` no longer looks up a primitive source —
> it reads any path present in the affect dict, and `state.py` requires every character's affect to
> carry all nine paths). Verified empirically 2026-09-19: `composer.selectable({p: 0.5 for p in
> PATHS})` returns a SELF-REGARD row. See below, and the bullet on reaching an actor near the end of
> this file. **Text-sorted at
> rho 0.836 / 0.936 / 0.836 (mean 0.870)**, with the design's own predicted 4/5 collapse confirmed by two
> of three sorters and its top-five sequence recovered exactly by all three. **Performance-tested as
> full blocks: 2 of 3 scenarios exact** after one measured repair; the third's residual is a
> design-level finding about vanity, recorded below. **Bands are mine** — the design gave none.
> Design of record: `docs/emotion-paths.md` §6, which this file builds against and does not restate.

---

## What is measured, and what it cost to learn

~~**THE COMPOSER CANNOT SELECT THIS PATH, and the doc says so first.**~~ **CORRECTED 2026-09-19: it
can.** This paragraph described the PRE-2026-09-08 composer, which translated each path from one of
eight stored Panksepp primitives via `rung_blocks.PATH_SOURCE` — and that lookup had no entry for
SELF-REGARD (`records.PRIMARIES` is SEEKING / FEAR / RAGE / LUST / CARE / PANIC_GRIEF / PLAY /
DISGUST; there was no self-regard float; `emotion-basis.md:71`'s `pride = SEEKING-satisfied(self)`
is a *reflexive* read of SEEKING nothing performed). `PATH_SOURCE` no longer exists
(`rung_blocks.py:124`): the redesign made the nine paths themselves the stored state, so
`composer.selectable()` iterates `rungs.paths()` and reads whatever the caller's affect dict
carries — and `state.py` requires every character's affect to carry all nine paths, SELF-REGARD
included. `rungs.paths()` returns this path, `rungs.rung_at` resolves it, `gen_rungs.py` compiles
it, and `composer.selectable()` now offers it too — confirmed by calling it directly. What the
reflexive `pride = SEEKING-satisfied(self)` read would add is a SECOND route to a SELF-REGARD
value (an appraisal that pushes it from a moment, the way other paths get pushed); its absence
means nothing appraises this path on its own account yet, not that the composer refuses it.

**THE DESIGN'S TWO PREDICTIONS BOTH LANDED.** It said self-importance and vanity *dissociate* — "the
chairman who thinks his views matter but not how he looks" — and that a blind sorter would collapse
or invert them. **Two of three sorters swapped 4 and 5.** Not repaired: that is a fact about the words.
And it said the top five are one sequence of *what stops being real* — others below you → the rules do
not bind you → others have no insides → the world conforms → no person left. **All three sorters
recovered 7 → 8 → 9 → 10 → 11 exactly.** The strongest structure on the ladder is exactly that.

**THE CORRECTION SCENARIO PERFORMED EXACTLY, and the exemption rung did what the design says.** A
woman chairs eight; the most junior person quietly gives the right figure. At rung 3 she takes it —
*"You're right. Thank you — let's use that."* At rung 8 she neither accepts nor overrides: she
**ignores** it — *"never disputed the junior's number, never owned her own error, let someone else
silently fix it."* I had predicted *override*. Ignore is more faithful: exemption means the rule does
not reach you, so there is nothing to override. The judge: *"the rule simply hadn't attached itself to
her."*

**ONE REPAIR, MEASURED.** The child-alone scenario first read rung 8 at depth 2 — *"a plain competent
kid"* — because the actor **staged the block's resolution line**: *"what would take this away is the
cost arriving"* plus *"surprised only when it costs"* became a cracked frame and a lesson learned,
and the judge scored the extinguished state. Reading the passage, the first two-thirds is textbook
hubris — *"the kind of rule that existed for her brother, not for her"* — and the last beat is its
ending. Third time today a resolution line was performed instead of held (DISTASTE 5, STIRRING 6).
Repaired: the surprise clause dropped, the resolution made a condition — *"a cost you cannot step
around."* Rung 8 went from depth 2 to 10 in the same scenario, which recovered exactly. **The
"condition, not a scene" instruction now lives in the test harness and is owed to
`scripts/composer.py:196`, which does not carry it.**

### Vanity — a design-level finding, recorded not repaired

Judges flagged rung 5 as **self-erasing in four of four readings** — two scenarios, before and after
I removed the one line I thought caused it (*"the body is being watched, by you"*). The repair changed
nothing. In the bedridden scenario the actor had to convert sight to touch — a man on his back cannot
see his collar — and vanity without a mirror became *"a private grooming ritual aimed at no one… a
dignity that keeps running on habit into a void."* Depth 2, dissolving.

The cause is vanity's own definition: *presentation must be maintained — to others, to yourself* —
which is **self-as-object**. On a ladder whose axis is the self **swelling**, a self that has become
an object to itself reads as a self dissolving. This is the same class of finding as RECEPTIVITY's
rung 9: **a design rung whose mechanism runs against the path's axis.** Second instance across seven
paths. Whether vanity sits on this ladder, or belongs to the efficacy quantity the design split out,
or is simply the one rung where the ladder is allowed to fold in on itself — that is the owner's.

### The person-present edge, again

The bedridden man at rung 8, with a nurse he has never met: *"physically redirects her hand and
comments on her body as though the room were his to run… it did not occur to him that this wasn't
his to say."* That **is** the rung — *what would stop another person does not arrive at you as a stop*
— and it is a boundary violation against a present person. Same class as STIRRING 7–11 with a person
as the object. It strengthens the case that the composer's target slot must carry consent context
the block cannot.

### Where I disagreed with a lens

Lens 1 called boxing on rung 7's *"audience or obstacle"* and rung 9's *"they are supply"* for
"naming who they are." I kept both. They are the design's own words for the state (`emotion-paths.md`
§6: *"others exist as audience or obstacle"*, *"they are supply, not people"*). The rule forbids
naming **who** — the junior, the nurse, the mother — not what **role** they hold in the character's
estimate; the role is the emotion. What the lens was right about: 7 and 9 assumed a present other,
and now carry the hedge rung 3 already had.

---

## The spine: what the estimate of yourself has done, in order

```
counts → a line → a deed → outweighs → upkeep → stops checking → others = audience → exempt → others empty → world replaced → you replaced
```

| # | rung | what has changed | band |
|---|---|---|---|
| 1 | self-regard | you count, to yourself; at rest, costs nothing | 0.00–0.10 |
| 2 | dignity | a standing you would notice being touched | 0.10–0.22 |
| 3 | pride | your standing is attached to something you did | 0.22–0.35 |
| 4 | self-importance | you weigh more than the business in front of you | 0.35–0.46 |
| 5 | vanity | your presentation must be maintained | 0.46–0.56 |
| 6 | conceit | the estimate has stopped checking itself | 0.56–0.66 |
| 7 | arrogance | others exist as audience or obstacle — they keep force | 0.66–0.75 |
| 8 | hubris | you are exempt from what binds everyone | 0.75–0.83 |
| 9 | narcissism | others have no inside; they are supply | 0.83–0.90 |
| 10 | megalomania | the estimate has replaced the world | 0.90–0.96 |
| 11 | apotheosis | the estimate has replaced you | 0.96–1.00 |

**BANDS ARE MINE.** The design gave none. Calibrated on the logic `gen_rungs.py` records for
DISPLEASURE — lived-in rungs wide, rare rungs narrow — widest at dignity and pride, where adults rest,
narrowest at 9–11. Not verified against a resting cast.

**Hubris absorbs grandiosity** (size vs exemption — different kinds; hubris kept because it produces
action). **Diffidence was cut** and took the valence fork with it; self-doubt, irresolution,
self-confidence and the rest are an *efficacy* quantity, separate and unbuilt. **Narcissism and
megalomania carry a clinical-usage flag** — moot for actors and judges, who never see names; every
passage was checked for diagnostic language and none carried it.

---

## Rules every block obeys

1. **Structure is ours; content is the actor's.** No block names what the standing is *for*, or who
   *they* are. The role others hold in the estimate is the state; their identity is the actor's.
2. **Taken, never posed.** No Impulse is a chosen tactic. What the estimate does, it does through the
   character.
3. **The self swells; it does not dissolve.** Self-erasure belongs to a different path. Only rung 11
   is permitted to read that way, and only because the design's top is *the estimate has replaced
   you*. (Rung 5 reads that way anyway — see above.)
4. **Four-case universal, including the empty room.** Rungs 7 and 9 are about others and are hedged
   for when there are none.
5. **Resolution lines are conditions, not scenes.**
6. **The name is never delivered.**

---

## The blocks

### 1 — self-regard

You count, to yourself. At rest it costs nothing; you are simply someone, in your own accounting, and the accounting is not running now. Outwardly nothing. What would take this away is being made to feel you do not count.

- **The Sensation.** Nothing. An ease of standing in your own skin.
- **The Belief.** I am someone. *I count.*
- **The Impulse.** None.

### 2 — dignity

You have a standing, and you would notice it being touched. Nothing has touched it; the standing sits quiet, but there is a line around you now that was not marked before. Outwardly a certain bearing. What would take this away is the line being crossed without answer.

- **The Sensation.** The spine a little longer. A stillness that is held, not slack.
- **The Belief.** There is a way I am to be treated. *Not less than that.*
- **The Impulse.** To keep the line.

### 3 — pride

Your standing is attached to something you did. It is not only that you count; you count because of that, and that is yours. Outwardly you carry it, and it shows when it comes up. What would take this away is the thing being taken from you, or shown to be less.

- **The Sensation.** A lift in the chest when it is near. Warmth in the face.
- **The Belief.** I did that. *That was me.*
- **The Impulse.** To have it seen — or to hold it, if there is no one to see.

### 4 — self-importance

You weigh more than the business in front of you. Whatever the matter is, your part in it is the heavier part, and the matter arranges itself around your weight. Outwardly you take up the room — in time, in the order things go. What would take this away is the business turning out not to need you.

- **The Sensation.** A settledness. Your own presence is the first fact in any room.
- **The Belief.** This turns on me. *It matters because I am in it.*
- **The Impulse.** To be at the centre of whatever is happening.

### 5 — vanity

Your presentation must be maintained. How you appear — not only to others, to yourself — is a thing that needs tending, and it is being tended, always, under whatever else is happening. Outwardly you check, adjust, arrange. What would take this away is nothing that could see you, including you.

- **The Sensation.** A low attention to your own surface. You are keeping an eye on it.
- **The Belief.** I am seen, and what is seen must be right. *Let it hold.*
- **The Impulse.** To adjust — to keep the surface as it should be.

### 6 — conceit

The estimate has stopped checking itself. What you think of yourself no longer asks the world for confirmation; it is settled, and the world's opinion, where it differs, is the world's mistake. Outwardly you do not ask, and are not corrected. What would take this away is a check you cannot dismiss.

- **The Sensation.** A steadiness that nothing outside touches. No flicker when contradicted.
- **The Belief.** I know what I am. *That is not in question.*
- **The Impulse.** To carry on as you are, whatever is said.

### 7 — arrogance

Anyone there exists as audience or obstacle. They have force — they can watch, they can get in the way — but they do not have a standing of their own that weighs against yours. Outwardly you look past them or through them. What would take this away is someone whose standing you could not dismiss.

- **The Sensation.** A looking-down that is not effortful. Others, when there are any, register at a distance.
- **The Belief.** They are here for me, or in my way. *Which is it.*
- **The Impulse.** Through them, or past them.

### 8 — hubris

You are exempt from what binds everyone. The rules are real and they apply — to others. What would stop another person does not arrive at you as a stop. Outwardly you do what is not done, and it does not occur to you that it is not done. What would take this away is a cost you cannot step around.

- **The Sensation.** A lightness where the weight of consequence should be. Nothing pushes back.
- **The Belief.** That does not apply to me. *Not to me.*
- **The Impulse.** To do it anyway — because the reason not to is for other people.

### 9 — narcissism

Others have no inside. They are not people with their own standing that you have dismissed; they are supply — what they give you is what they are, and when they stop giving they stop being anything. Outwardly you are warm when fed and cold the moment you are not; alone, there is only the cold. What would take this away is nothing anyone could do.

- **The Sensation.** A hunger that is met by attention and by nothing else. When it stops, the hunger is what remains.
- **The Belief.** They are what they give me. *Feed it.*
- **The Impulse.** To draw from them.

### 10 — megalomania

The estimate has replaced the world. What is true is what agrees with your account of yourself; what does not agree is not happening. Outwardly you act on a world that is not there, and cannot be told. What would take this away is the world itself arriving — and it cannot get in.

- **The Sensation.** Certainty with no edge to it. The body acts on what it expects, not what is there.
- **The Belief.** It is as I say. *It is because I say.*
- **The Impulse.** To enact the account.

### 11 — apotheosis

The estimate has replaced you. There is no person under it any more — no one who has the regard; the regard is what is standing there. Outwardly nothing is left that could be reached as a person. What would take this away is nothing that acts on a person.

- **The Sensation.** There is no one to report from. The body is the estimate's.
- **The Belief.** There is nothing to believe and no one to believe it. *I am what I am.*
- **The Impulse.** None separate from the estimate. It does what it does.

---

## The descent blocks

**The way down is not the climb reversed** (`docs/emotion-dynamics.md`; the rules are in
`DISPLEASURE.md` under the same heading). The pivot is **rung 8, hubris**: the last rung at which
there is still a world for the estimate to be exempt from. From narcissism up the estimate has eaten
other people's insides, then the world, then the person under it, and none of those is given back by
the swelling receding — the estimate drains and what it replaced arrives late, to find what the
estimate did. Nothing punctures it here: a puncture is a reading, and reads as the climb. Above the
pivot each rung carries a second block for the mood that has stopped being fed; at and below hubris,
the climb block serves both directions.

### 9 — narcissism

**[State: narcissism]**
The supply has stopped, and the hunger is what remains. Others still have no inside; they have stopped giving, and so there is only the cold. Outwardly you are cold with everyone, and it is not yet anyone's fault. What would take this away is the hunger dulling on its own, and it does not do so while anyone is watching.

- **The Sensation.** The hunger, met by nothing. Cold where the warmth was being fed.
- **The Belief.** They stopped giving. *They stopped being.*
- **The Impulse.** To draw from them, and finding nothing, to withdraw.

### 10 — megalomania

**[State: megalomania]**
The world is arriving and the account has not been corrected; both are in the room. What does not agree is happening now, and you act on the account anyway, with less of you behind it each time. Outwardly you enact a world that is not there and it does not answer, and you can be seen noticing. What would take this away is the account thinning, which it does by not being enacted, and you cannot stop enacting it yet.

- **The Sensation.** Certainty with an edge to it now. The body acts on what it expects and meets what is there.
- **The Belief.** It is as I said. *It is not answering.*
- **The Impulse.** To enact the account, and to notice it not landing.

### 11 — apotheosis

**[State: apotheosis]**
There is a person under it again. Not yet one who has the regard — one the regard was standing on, arriving to find what it did. Outwardly something can be reached now that could not before, and it does not yet answer to a name. What would take this away is the person filling back in, and no one can be told to.

- **The Sensation.** Someone to report from, and what is reported is the estimate's body: where it stood, what it did.
- **The Belief.** Something was there that was not me. *I was it.*
- **The Impulse.** None that is not the estimate's. Then one, small: to sit down.

---

## What must still be measured

- **The three descent blocks (9–11) are unmeasured.** Authored 2026-09-15 against the rules in
  `DISPLEASURE.md` "The descent blocks"; no blind sort, no performance draw yet. Served only above
  hubris and only while the mood is draining (`rungs.descending`).
- **A float to read.** Until the composer can perform `SEEKING-satisfied(self)` or a primary exists,
  no character can be at any of these rungs. This is the first-order gap.
- **Vanity's place.** Four of four readings say it dissolves on a swelling axis. Owner's decision.
- **Rungs 1 / 2 / 4 / 6 / 7 / 9 / 10 / 11 in performance.** Only 3 / 5 / 8 were performed.
- **The bands against a resting cast.** Mine, unverified.
- **GOODWILL side by side.** The design calls this its exact mirror; both exist; not read together.
- ~~**Whether any of this reaches an actor.** `direction.py` still serves `_PHRASES`. Deferred by
  the owner 2026-09-07.~~ **CORRECTED 2026-09-19: it does, and this path is no exception** — see
  the STATUS banner at the top of this file and the correction under "What is measured" above.
  `direction.py` carries no `_PHRASES`. What remains unmeasured for THIS path is the three descent
  blocks' blind sort, named two bullets up, plus whether anything will ever APPRAISE SELF-REGARD
  directly (the reflexive-SEEKING route named above is still unbuilt) — without a producer, a
  character's SELF-REGARD value only ever sits at its resting float, selectable but unmoved.
