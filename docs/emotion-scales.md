# Emotion scales — what the numbers mean

**Status: NORMATIVE for what each value MEANS. Magnitudes elsewhere are calibration; these are
definitions.** Authored 2026-08-31 to close a gap the engine had carried since the basis was built:
`state._DIM_TO_PRIMARY` prices events to four decimal places against a scale nobody had defined.
The band edges in `direction.py` were the only thing cutting the range into named regions, which
made a RENDERING CONSTANT the de facto specification.

## Who reads what

| reader | gets | why |
|---|---|---|
| the **engine** | the float | it computes change; arithmetic needs a number |
| the **showrunner** | the float **and this document** | it must know that CARE 0.45 is a person who will help if it is cheap, so it can write the scene |
| the **actor** (sim agent) | prose only, never a number | hard rule 5. It does not know what 0.45 means and should not be asked to |

The author's framing, which this document serves: *"The numbers should be the guide the showrunner
has to understand what level the emotion is, and the numbers allow the engine to calculate how the
emotions change."*

## The anchor principle

**Five anchors per primitive are normative. Everything between them interpolates.**

An anchor is a THRESHOLD stated in felt or observable terms — something a director could adjudicate
without a number. Anchors are where the meaning is fixed; the twenty prompt bands
(`docs/connection-model.md` records the 0.05 quantisation decision) sit between them and inherit
their meaning from the anchors either side.

Anchors are placed at **0.00, 0.25, 0.55, 0.80, 1.00** — the existing `direction._BANDS` edges,
adopted deliberately rather than re-derived, because every authored character sheet and every
fixture in the repo was written against them. Moving them would silently re-interpret existing
content.

**The scales are NOT commensurable.** DISGUST 0.5 and LUST 0.5 do not describe comparable
intensities, and the engine already concedes this: `_DECAY_RATE` runs from 0.72 (FEAR) to 0.90
(PANIC_GRIEF), so the same number persists very differently per primitive. Read each scale on its
own terms.

**A scale measures ONE variable.** Each entry below names it. If a proposed anchor cannot be
expressed as a point on that one variable, the anchor is wrong, not the variable.

---

## SEEKING — *forward pull toward what might be found*

**The scale measures how much of your attention is committed to what is not here yet.**

| | |
|---|---|
| 0.00 | nothing pulls. You wait to be handed the next thing and are content to be. |
| 0.25 | you will follow a lead if it is put in front of you, and not otherwise. |
| 0.55 | you generate the next question yourself. The present is a place you are passing through. |
| 0.80 | you are already past what is here. It has become the route to what is next. |
| 1.00 | arrival is impossible. Every answer converts into the next question before you have finished having it. |

reflexive **yes** · kinds: entity, task, prospect · rest decay **0.78**
raised by mastery +0.35, attraction +0.18, threat +0.12, care_relevant +0.10 · lowered by loss −0.18

> Note the threat entry: threat → SEEKING is **hypervigilance**, not curiosity. The same number can
> mean a scholar or a hunted man, and only the company it keeps distinguishes them.

---

## FEAR — *withdrawal from anticipated harm*

**The scale measures how much of your capacity is spent on what might go wrong.**

| | |
|---|---|
| 0.00 | the room is taken at face value. You do not check the exits and it does not occur to you to. |
| 0.25 | you know where the exits are. It costs you nothing to know. |
| 0.55 | you are letting someone else commit first, and you are aware that you are. |
| 0.80 | you are managing the threat instead of doing anything else. Ordinary business has stopped. |
| 1.00 | there is no capacity left for anything but the danger. You could not attend to something else if it mattered. |

reflexive **no** · kinds: entity, prospect, belief · rest decay **0.72** — the fastest in the basis
raised by threat +0.45 · lowered by relief −0.40, mastery −0.10

> Fastest decay of the eight, and that is definitional: fear tracks a live threat and should not
> outlive it. A fear that persists after the danger is gone is the WOUND tier's business
> (`wound.py`), not this one.

---

## RAGE — *approach to remove an obstacle or redress a wrong*

**The scale measures how much of your response to a wrong is still under your own supervision.**

| | |
|---|---|
| 0.00 | slights do not register as wrongs. There is nothing to answer. |
| 0.25 | it registers, and you let it pass without marking it. |
| 0.55 | you are answering sharper than you meant to, and you notice that you are. |
| 0.80 | you are still watching yourself do this and you are not stopping. |
| 1.00 | the one in you who keeps watch has stepped out. |

reflexive **no** · kinds: entity, act · rest decay **0.80**
raised by social_violation +0.45, threat +0.10 · **lowered by NOTHING** — see the gap below

> **1.00 is a change in kind, not degree, and this is the best-evidenced anchor in the document.**
> A 2026 mixed-methods study in *Aggressive Behavior* compared rage episodes against anger episodes
> and found identical triggers and identical physiology; what differed was tunnel vision,
> controllability, and reduced awareness of one's own behaviour — some participants needed witnesses
> to tell them what had happened. At every band below, the character can watch themselves being
> angry. At the top they drop out of their own audience.
>
> Two corollaries the phrasing must respect. The top band is **quieter** than the band below (82% of
> officers in perceptual-distortion studies report diminished sound; shouting is the outside view).
> And the state is **appetitive** — people deliberately make themselves angrier before a
> confrontation — so it must not be written as an impairment nobody would choose.
>
> **RAGE is the name of the circuit, not of its ceiling.** Ordinary English uses "rage" for 1.00
> alone; here it spans from not-noticing-slights upward. That trap is closed by the named regions
> below rather than by renaming the primitive — a rename would touch 51 files and lose Panksepp's
> vocabulary; the regions cost nothing and put each word where English already puts it.

---

### The named regions — annoyance / anger / rage

The author's rule (2026-08-31): **annoyance turns to anger that turns into rage.** Those are not
three emotions. They are three regions of ONE scale, and naming them is what makes the number
readable to a showrunner without renaming the circuit.

| region | span | what is true in it |
|---|---|---|
| *(below)* | 0.00-0.25 | it does not register as a wrong |
| **annoyance** | 0.25-0.55 | it registers, and you let it pass |
| **anger** | 0.55-0.80 | you answer it, and you know you are answering |
| **fury** | 0.80-0.95 | you are watching yourself do this and not stopping |
| **rage** | 0.95-1.00 | the one who was watching has stepped out |

This dissolves the label trap without a rename. RAGE-the-circuit-name is Panksepp's and stays; RAGE
the WORD now refers only to the top region, where it belongs and where ordinary English already puts
it. `RAGE: 0.30` stops reading as "slightly murderous" and starts reading as **annoyance**, which is
what it means.

**The annoyance/anger boundary is the one that carries weight.** It is not intensity — it is whether
the wrong gets ANSWERED. A man at 0.50 who says nothing and a man at 0.60 who says one sharp thing
differ by a decision, not by a temperature.

**And rage is a genuinely distinct state, not the loud end of anger.** The 2026 *Aggressive Behavior*
study compared rage episodes against anger episodes and found identical triggers and identical
physiology; what differed was controllability and awareness of one's own behaviour. So the top region
earns its own word on evidence rather than for emphasis.

---

## LUST — *approach toward union*

**The scale measures how much of your attention the wanting has organised.**

| | |
|---|---|
| 0.00 | their presence is just presence. |
| 0.25 | you are aware of them in a way you would not report. |
| 0.55 | you are arranging yourself around the possibility, and choosing where to stand. |
| 0.80 | the rest of the room is scenery. |
| 1.00 | there is nothing else you are doing. |

reflexive **no** · kinds: entity · rest decay **0.80**
raised by attraction +0.45 · **lowered by NOTHING**

> The thinnest primitive in the system, measured: one input dimension, dominant in none of the 41
> compounds, and capped at 0.25 in the two it appears in (`love`, `longing`). It was unreachable
> entirely until `attraction` was added on 2026-08-22. Treat its calibration as the least settled.

---

## CARE — *act on another's behalf at cost to yourself*

**The scale measures how much of your own interest you would spend on them.**

| | |
|---|---|
| 0.00 | no one here has a claim on you. Your own business comes first and that is not a decision. |
| 0.25 | you will do a small thing if it costs you little. |
| 0.55 | their situation is competing with yours and sometimes winning. |
| 0.80 | you are acting for them before you have finished deciding to. |
| 1.00 | what you wanted for yourself is not in the calculation at all. |

reflexive **no** · kinds: entity · rest decay **0.82**
raised by care_relevant +0.40 · **lowered by NOTHING**

> **Definitionally other-directed**, which is why reflexive is refused: "self-care" is welfare
> management through SEEKING and FEAR, not the nurturance circuit (`records.py` DIRECTEDNESS).
> Like LUST it is a SINGLE-DOOR primitive — one way in, no way out — which is the structural reason
> a brutalised character's capacity to love cannot currently fall.

---

## PANIC_GRIEF — *distress at a broken bond*

**The scale measures how much of the world still works without them.**

| | |
|---|---|
| 0.00 | alone is fine. Being alone is not a fact you are tracking. |
| 0.25 | you would rather they were here. |
| 0.55 | their absence is a thing in the room with you. |
| 0.80 | you are organising your day around not feeling this. |
| 1.00 | nothing has a point that does not have them in it. |

reflexive **yes** · kinds: entity, recall, belief · rest decay **0.90** — the slowest but one
raised by loss +0.50 · lowered by relief −0.35

> Slowest decay of the primaries that move on events, and that is the design: grief is supposed to
> outlast its cause. The `recall` kind matters — this is the one primitive the engine admits can be
> re-triggered by memory rather than by an event in the room.

---

## PLAY — *engagement for its own sake, without stake*

**The scale measures how much of what you are doing has no purpose beyond doing it.**

| | |
|---|---|
| 0.00 | everything is instrumental. Nothing is done because it is worth doing. |
| 0.25 | you let a joke through and do not chase it. |
| 0.55 | you are enjoying this and would keep going past the point of usefulness. |
| 0.80 | the purpose has fallen away and you have not noticed. |
| 1.00 | there is no outside to this. Stakes would have to be reintroduced from somewhere else. |

reflexive **no** · kinds: entity, act · rest decay **0.75**
raised by relief +0.20, mastery +0.15, attraction +0.10 · lowered by threat −0.22, loss −0.20, social_violation −0.15

> **The only primitive with a complete negative half**, and the only one that fell correctly in the
> measured slave case (0.750 → 0.090 across 80 durable diffs). Six input dimensions against CARE's
> one. It is the worked example of what the other seven should look like.

---

## DISGUST — *expel — this would contaminate me*

**The scale measures how much distance you need.**

| | |
|---|---|
| 0.00 | nothing here is beneath touching. |
| 0.25 | you would rather not, and you could. |
| 0.55 | you are managing your proximity to it deliberately. |
| 0.80 | contact would have to be justified to you. |
| 1.00 | proximity itself is intolerable, whatever the argument for it. |

reflexive **yes** · kinds: entity, act, percept · rest decay **0.88**
raised by social_violation +0.28, threat +0.08 · **lowered by NOTHING**

> **A deliberate departure from Panksepp**, recorded in `emotion-basis.md` so it cannot rot back: he
> classed disgust a sensory affect, an exclusion on circuit type rather than on irreducibility.
> Without it `social_violation → RAGE` is the only social path, and the engine cannot tell a man who
> squares up from a man who looks away. Second-slowest decay: contempt is the durable social
> residue.

---

---

## The named regions, for all eight

Every scale gets landmark words at its anchor boundaries. A region name is not a separate emotion —
it is the stretch of ONE scale where a particular English word is the right one. The BOUNDARY is the
load-bearing part: each is a change in what is true, adjudicable by a director without a number.

**Three primitives carry the RAGE trap** — the label names a region instead of the range, so the low
values read as nonsense. Marked ⚠.

| primitive | 0.00-0.25 | 0.25-0.55 | 0.55-0.80 | 0.80-0.95 | 0.95-1.00 |
|---|---|---|---|---|---|
| SEEKING | incurious | **interest** | **drive** | **obsession** | **compulsion** |
| FEAR | unguarded | **caution** | **wariness** | **dread** | **terror** |
| ⚠ RAGE | unmoved | **annoyance** | **anger** | **fury** | **rage** |
| ⚠ LUST | indifferent | **attraction** | **desire** | **craving** | **consumed** |
| CARE | unclaimed | **regard** | **kindness** | **devotion** | **sacrifice** |
| ⚠ PANIC_GRIEF | content alone | **missing** | **grief** | **mourning** | **desolation** |
| PLAY | earnest | **levity** | **play** | **absorption** | **flow** |
| DISGUST | untroubled | **distaste** | **aversion** | **revulsion** | **abhorrence** |

### What each boundary actually is

Not intensity. A change in what is true of the person.

| primitive | the boundary that carries the weight | what changes at it |
|---|---|---|
| SEEKING | interest -> drive | whether you generate the next question or wait to be handed it |
| FEAR | wariness -> dread | whether ordinary business continues |
| RAGE | annoyance -> anger | whether the wrong gets ANSWERED |
| LUST | attraction -> desire | whether where they are is something you are tracking without deciding to |
| CARE | kindness -> devotion | whether their need competes with yours and sometimes wins |
| PANIC_GRIEF | missing -> grief | whether the absence is a thing in the room with you |
| PLAY | play -> absorption | whether you have noticed that the purpose fell away |
| DISGUST | aversion -> revulsion | whether contact would have to be JUSTIFIED to you |

### Why PLAY's regions were rewritten (2026-08-31)

The first pass read *levity / amusement / delight / abandon*, and three of those measure the wrong
thing. PLAY's variable is **how much of what you are doing has no purpose beyond doing it** —
purposelessness, not pleasure. *Amusement* and *delight* name enjoyment; *abandon* names loss of
inhibition, which belongs to FEAR-down or DISGUST-down and not here. A child playing intently sits
at the ceiling of this scale and is the opposite of abandoned.

The referent for the top is well attested: Csikszentmihalyi's **flow** — complete absorption, loss of
self-consciousness, and the activity becoming its own reward. That last clause IS this primitive's
definition, so the ceiling is not a coincidence of naming.

Note the structural echo with RAGE: at both ceilings **the reflective self stops**. In RAGE the
self-observer drops out under arousal; in PLAY it dissolves under absorption. Phenomenologically
opposite — one is heat, one is ease — and the same shape. Whether that holds for the other six is
unchecked and worth checking rather than assuming.

**LUST's boundary was rewritten (2026-08-31).** It first read *whether you would report it if asked* —
which points the wrong way. The 0.25 anchor is already "aware of them in a way you would not report",
so under that test reportability RISES with intensity, while deepening desire is usually more
concealed, not less. An anchor whose direction is arguable is not an anchor.

The replacement is on the scale's own variable — the ORDERING OF ATTENTION — and it is observable
without asking the character anything: below the line their location is something you could work out;
above it, it is something you already know.

### The three traps, and why they matter more than the others

**⚠ LUST is RAGE's twin.** The word names the top region; the scale starts at *aware of them in a way
you would not report*. `LUST: 0.30` reads as lechery and means **attraction**. Same failure, same fix.

**⚠ PANIC_GRIEF is worse than a trap — it is a compound label.** Two words joined, reading as one
severe state, when the bottom of the scale is *contentment at being alone*. `PANIC_GRIEF: 0.10` does
not mean a small amount of panicked grief; it means the person is fine by themselves. This is the
only primitive whose low end is a POSITIVE state, and the label actively hides that.

**⚠ RAGE** — recorded above.

The other five span acceptably: FEAR at 0.1 is mild watchfulness and at 0.9 is terror, and the word
stretches to both. No rename is needed for any of the eight; the regions do the work.

### One thing the regions do NOT license

A region name is a READING AID for the showrunner. It must never reach the actor. Handing an actor
"you are in the fury band" names the emotion outright, which `docs/phrases-seeking.md` forbids and
which collapses the performance onto a stock reading. The actor gets the band phrase; the showrunner
gets the region word.

## What is NOT locked here, and must not be read as settled

* **The counters.** Four primitives — RAGE, LUST, CARE, DISGUST — have no dimension that lowers
  them, so their scales are currently one-way under events. `docs/state-engine.md:11` specifies the
  tier as "appraisal (events UP) + decay (time DOWN)", so this is the SPEC, not a bug — and it is
  the spec that is under revision. Proposed additions (`redress`, `degradation`) are designed and
  unbuilt.
* **The twenty prompt bands.** The 0.05 quantisation and its hysteresis are decided; the phrases are
  unwritten. They must be authored as FELT STATE, never as behaviour — all 32 current phrases in
  `direction._PHRASES` are behavioural, which makes the engine decide what the character does and
  leaves the actor nothing to act.
* **Whether expression renders primitives or directed compounds.** Under design. If it moves to
  compounds, the authoring target changes and so does the slot count.
* **Priming.** Nothing yet makes a worn character price an event differently, so a rested man and a
  man who has been afraid and thwarted for weeks receive the same insult identically.
* **Every magnitude in `_DIM_TO_PRIMARY`.** Calibration, not definition. This document fixes what
  the RESULTING VALUE means, not what any event should cost.
