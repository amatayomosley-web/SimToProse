# Emotion arithmetic — the tag, what a rung is worth, the receipt step, and decay

*(Normative for how a character's emotion state MOVES under the nine-path model. `emotion-paths.md`
owns which paths exist; `emotion-dynamics.md` owns what a path is; `docs/rungs/<PATH>.md` own the
rungs. This is the "later pass" `emotion-dynamics.md` §6 deferred until the path set was settled. It
supersedes `state-engine.md` §"The appraisal module" and §"Decay" for emotion state. It does not
touch relationship edges, laws, condition, or energy.)*

> **STATUS: DRAFT 5, 2026-09-07.** The owner's model (§0), simulated (§8), not built. Drafts 1–4
> each tried to break the sensor-feeds-engine loop inside the arithmetic — by tracking, by gating on
> the state, by gating on the baseline, by gating on the stored rung — and each paid for it in the
> provoked case: an undershoot, a slowed calm, or a sawtooth across rungs once the rung read was
> reached. The owner's ruling settles it: **the vector is a hard number per rung, identical for
> everyone; the character's multipliers do the shaping; and the sensor says what HAPPENED.** The loop
> is broken at the sensor, which is the seat whose job that is, and the arithmetic stays simple
> enough to control with a handful of numbers. Every constant is a Class-B start.

---

## 0. The architecture and the rules, in the owner's words

> *"The engine stores the current calculated rung, the assembler pulls the correct character rung
> and sends it to the composer, the composer chooses from the current character list the emotions
> it believes will drive the scene according to the scene blueprint. The emotions are increased by
> the agent that reads the stream and tags the emotions it finds."*
> *"The appraiser should read the stream, both actions and thoughts, it tags according to the list
> of emotions."*
> *"The emotion always increases its own path… Higher rungs are worth more vectors. A displeasure tag
> and a fury tag should be proportionally different. The amount they increase should be small, we
> manage the increases with character based multipliers."*
> *"The character is who they are, if their baseline is rung 3 then that's who they are, what's
> accumulated is added onto wherever their vectors are."*
> *"The sensor says what happened… we can control how much it effects the character by defining how
> each emotion is multiplied when they are tagged."*
> *"The goal is to set hard numbers for the vector, rung 3 gets the same value across all instances
> regardless of who is the target of the tag. The character has the multipliers, so how the vectors
> interact with them is based upon how the multipliers affect it. This way we can create easier ways
> to control the numbers."* — William, 2026-09-07

| seat | supplies |
|---|---|
| **the actor** | the performance: state plus the moment, played from the sheet |
| **the appraiser** | what HAPPENED in the beat: which emotions arose or intensified, at which rung, about whom |
| **the engine** | the rung's hard vector times the character's multiplier, added; decay toward the baseline every beat; the rung, with hysteresis; storage of all of it |
| **the assembler + composer** | selection among the stored rungs; never a move |

---

## 1. The tag — what the engine receives

Per beat, for the character who produced stream, the appraiser emits:

```
{ "readings": [ { "path": "DISPLEASURE", "rung": "anger",  "about": "saskia" },
                { "path": "WARINESS",    "rung": "unease", "about": ""       } ],
  "lands_on":  [ "lorcan", "yusuf" ],
  "confidence": "sure" }
```

- **`path`** — one of the nine. **`rung`** — a rung name from that path's ladder; the block text is
  the rubric. This is the judge this repo ran all week on its own rung tests: exact on most
  scenarios, ±1 rung on hinges (`docs/rungs/DEFLATION.md`, `SELF-REGARD.md`).
- **`about`** — an entity id from the PerceptSet, or `""`. The target slot (§5 step 3).
- **`lands_on`** — present characters this beat bears on. Feeds the floor (§5 step 5).
- **`confidence`** — a word; gates escalation to the recorder; **never enters arithmetic**.
- **No number leaves the appraiser** — hard rule 5's inbound twin, as `severity.py` states it.

**What it reads:** the character's own `{action, thought}` for this beat, both; the moment for
context. Not narrated prose, which does not exist yet at appraisal time and is the narrator's
product (`recorder.md`'s rule, inherited); not another character's mind, which this seat cannot
observe by POV isolation (`emotion-dynamics.md` §"courier rule"). Reading the thought stream is what
lets a stoic's state climb while the action stream stays flat, and where a slow burn shows first.

**What it tags — THE LOAD-BEARING RULE: what happened in the beat, never the state the character
carries.** An emotion that arose, or that intensified, in this beat is an event and is tagged. A
character being what they already were — a rung-3 person answering flatly, a seething man sitting
in his seething while nothing further happens — is not an event and is not tagged. An idle beat
yields no readings. §3 explains why this rule, and not the arithmetic, is where "being themselves is
free" lives, and §8 measures what it costs when the sensor gets it wrong.

**What it must not see: the character's stored rungs, or their baseline.** A sensor that sees the
label reads the label. A sensor that sees the baseline second-guesses the arithmetic.

**Witnesses are not read.** They produced no stream; they move when they act. `lands_on` gives them
the floor. A deliberate gap; §9.

---

## 2. What a rung is worth — the hard vector table

A rung is a half-open band `[lo, hi)` on `[0, 1]` (`src/engine/rung_blocks.BANDS`). **Each rung has one
vector `v_k`, the same for every character and every target.** The table is derived from the rung's
height by one number per path:

    v_k = λ_p · height_k          height_k = the band midpoint, clamped to 1.0
    λ_p  MEASURED 2026-09-11, per path (`src/engine/rungs.LAMBDA`):
         STIRRING .070 · WARINESS .100 · DISPLEASURE .054 · GOODWILL .030 · DEFLATION .066 ·
         DISTASTE .026 · RECEPTIVITY .042 · SELF-REGARD .042 · LEVITY .066

which gives, on DISPLEASURE (λ .054): displeasure .002 · annoyance .007 · chafing .013 ·
bristling .020 · riled .027 · seething .033 · anger .039 · outrage .044 · fury .047 · rage .050 ·
berserk .052 · amok .054. A fury tag is still worth twenty-five times a displeasure tag, to
everyone — the RATIO is the ladder's; λ sets how much of a rung one reading is worth.

**Why these numbers (2026-09-11).** λ = 0.15 on every path was the Class-B start, and the first
generated scene on a real book showed it running away on ordinary readings: a character's GOODWILL
climbed fondness → devotion (six rungs) in three of their beats — three readings on one beat summed
to +0.32, then +0.14, +0.10. On the two live read-alongs the same arithmetic sat above the
thermometer's standing level on every path (Red Badge error 0.290 vs rest-only 0.140, Holmes 0.192
vs 0.051), with paths pinned at the ceiling. `tests/calibrate_accrual.py` replays a run's stored
readings through the current engine with λ scaled: the error fell monotonically as λ fell and the
bias crossed ~0 on six of eight paths at 0.15–0.25× (Red Badge 0.208, Holmes 0.099 at 0.25×). The
FLOOR per path is the reachability guarantee E2 in `tests/test_genotype_balance.py` — the strongest
person under sustained top-rung readings every ten minutes, with no bond multiplier, must reach
the top rung — which each path's half-life sets (shortest half-life, largest λ: WARINESS). The
table IS that floor, and it scores like the 0.25× global on both thermometers (Red Badge 0.213,
Holmes 0.110) while keeping every top reachable. The level-anchored alternative (a reading moves
the state toward the LEVEL it names; a reading at or below the carried level adds a small
sustaining term) measured worse on both books (0.25 / 0.17) and did not respond to λ — it holds
the character at the level the reading named while the text shows the level falling back — so the
additive receipt stays and legitimate repetition still counts. The owner's rule: no dramatic
increase without cause; a dramatic increase now takes several strong readings in a row, which is
one. What λ does NOT fix is the sensor firing on a book's dominant path (Red Badge SELF-REGARD /
DISPLEASURE, Holmes RECEPTIVITY / STIRRING keep a positive bias at every scale) — that is the
`new | held` question, an instrument to add to the seat before it becomes a lever. A path may
override a rung's vector in `gen_rungs.py` beside its band if a ladder needs a shape `λ·height` does
not give; the default is the formula, so "control the numbers" is nine numbers, not ninety-two.

| path | rung → height (`v = λ·height`) |
|---|---|
| DISPLEASURE | displeasure .035 · annoyance .125 · chafing .245 · bristling .375 · riled .50 · seething .615 · anger .72 · outrage .81 · fury .88 · rage .93 · berserk .965 · amok 1.0 |
| DEFLATION | deflation .04 · dejection .13 · sadness .24 · sorrow .36 · misery .51 · inconsolability .65 · despondency .75 · despair .85 · devastation .93 · hollowness .985 |
| WARINESS | wariness .035 · unease .105 · misgiving .175 · apprehension .25 · worry .33 · nervousness .41 · anxiety .495 · foreboding .58 · dread .67 · alarm .76 · fright .835 · panic .905 · terror .975 |
| GOODWILL | goodwill .045 · warmth .135 · fondness .225 · concern .315 · tenderness .405 · compassion .495 · solicitude .58 · protectiveness .66 · devotion .775 · sacrifice .93 |
| STIRRING | stirring .04 · curiosity .13 · noticing .24 · attraction .35 · urge .44 · wanting .53 · craving .62 · zeal .70 · longing .795 · fixation .895 · obsession .975 |
| RECEPTIVITY | receptivity .04 · liking .125 · appreciation .215 · pleasure .305 · gladness .40 · wonder .50 · awe .595 · delight .695 · elation .795 · rapture .885 · ecstasy .97 |
| SELF-REGARD | self-regard .05 · dignity .16 · pride .285 · self-importance .405 · vanity .51 · conceit .61 · arrogance .705 · hubris .79 · narcissism .865 · megalomania .93 · apotheosis .985 |
| DISTASTE | distaste .075 · squeamishness .25 · revulsion .475 · loathing .71 · abomination .915 |
| LEVITY | amusement .05 · levity .16 · playfulness .29 · banter .43 · mischief .56 · immersion .68 · absorption .795 · raptness .895 · flow .975 (built 2026-09-11 by the owner's ruling; unmeasured) |

Derived, not authored: regenerate from `BANDS` whenever a band moves.

**BUILT 2026-09-09** — `src/engine/rungs.py` `vector_for(path, index)` and `height_of(path, index)`,
derived at import from `BANDS` so the table cannot rot. `LAMBDA` is a per-path dict initialised to
0.15 everywhere, so §9 decision 1 (global or per-path) is a data change rather than a code change.
Guarded by `tests/test_rung_vectors.py`, which transcribes the table above rather than recomputing
it, and carries two deliberate-breakage controls.

⚠ **ONE ROW ABOVE IS A ROUNDING, not a rule.** DISPLEASURE's `amok` is printed as height 1.0; its
band is `(0.98, 1.01)` and the midpoint is **0.995**, giving vector **.1492** rather than .150. The
other 91 rungs reproduce exactly, and every OTHER path's top rung is published as its own raw
midpoint (DISTASTE `abomination` .915, WARINESS `terror` .975, SELF-REGARD `apotheosis` .985), so no
clamp-to-one is in force anywhere. The code takes the midpoint; the table above is left as written
with this note beside it.

---

## 3. The receipt step — the whole arithmetic

Per character, per path `p`: the baseline `b` (`baseline.temperament[p].mean` — who they are), the
state `f`, the stored rung `R`, and two character multipliers from `build_profile`: gain `g` and
effective retention `r`.

**Step 1 — decay, every path, every beat, FIRST** (the engine's existing form, `state.decay`):

    f ← b + (f − b) · r

**Step 2 — the vector, for each path read this beat, with the rung read `k`:**

    f ← f + v_k · g                        the hard vector times the character's gain, added
                                           wherever the character sits — a rung-2 tag on a
                                           rung-4 character still counts (owner's rule)

Clamp to `[0, 1]`. No gate on the state, no cap, no per-character offset: **the accumulation rule
is one constant rule for every character, and the gain `g` is the only thing about the character
in it.** A character who leans toward an emotion is handled by the gain on that path (below), not
by a second per-character term. The gain is applied **per hit**; how many hits land is the scene's
business, and the engine's only accounting of it is the sum above against decay.

**Step 3 — the rung, with hysteresis** (`emotion-dynamics.md` §1, "climb high, drop lower"):

    raw ← band(f)
    R   ← R_prev   if raw < R_prev and f ≥ lo(R_prev) − h        (hold on the way down)
          raw      otherwise
    h = 0.02   (Class-B; below the narrowest band, 0.03, so a hold can never skip a rung)

Store `f`, `R`, and the readings (§5 step 8).

### What the multipliers do

Under a tag held beat after beat, the state settles where the vector's addition balances the decay:

    f* = b + v_k · g · r / (1 − r)          (clamped at 1.0)

`g` decides how high the same tags carry this character and how fast; `r` decides how long they
hold it and how fast they fall. Measured (§8): a placid character (`g` 0.75) under sustained *anger*
settles at *seething*; a neutral one at *anger*; a reactive one (`g` 1.3) at **fury** — past the
rung named, because for a reactive person anger-level beats add up to more than anger. Under
sustained *fury* the same three land at *anger*, *fury*, *amok*. The top of every ladder is
reachable, and who reaches it is decided by the multipliers, with the vector table untouched. That
is rule 4 as arithmetic.

**Repetition alone lifts a character.** Eight identical *bristling* hits carry a rung-3 character to
*riled*; the steady-state level of repeated hits at rung k is `b + v_k·g·r/(1−r)`, which sits above k on the
low rungs and near k on the high ones (§8, 9). The disproportionate fifth slight is partly in the
arithmetic and partly the actor's: repetition carries a character a rung above what each hit named,
and the actor performing more than that on the fifth slight is what the sensor then names.

### The multipliers, BUILT (gate three, 2026-09-11)

The receipt and the half-life each carry the owner's multipliers now (`src/engine/state.py`
`appraise` / `decay`; `src/engine/connection.py`):

    receipt     f <- f + v_k · g · connection(about) · q
    half-life   base_path(zone) · hold · (1 + connection(about)) · presence

- **`connection(about)`** — investment in whatever the path is ABOUT, through ONE registry
  (`connection.for_about`): a person's edge (as before), a **concept** (the wound on that concept
  and path — its live intensity), a goal (its priority), a value (its weight). One floor (0.20,
  the dead zone), one ceiling (x1.75). Owner: *"the closer people are the harder the emotions
  should hit, but I also want the ability for abstract ideas to also carry the same harder
  hit."* A person's investment scales the empathy/betrayal dims only (a threat's subject is the
  wolf); a concept, goal or value IS the thing feared or lost, so it scales every dim.
- **`q`** — repetition (`connection.repetition`): the same thing landing again on the same path.
  Habituates by 0.8 per repeat while the thing is absent, grinds by 1.15 per repeat while it is
  present, capped at four. The count is READ FROM THE LOG (`targets.repeat_count` over
  `turns.tags`), never stored.
- **`1 + connection`** — a full investment doubles the half-life: the "and the longer it lasts"
  half of `character-model.md`'s rule, which until this gate only the memory tier honoured.
- **`presence`** — x3 while the thing the path is about is in the room. A person is here when on
  the roster; a **concept is here when this beat names it**. One factor by the owner's ruling.
- **What a feeling can be ABOUT** is a perceived person, a registry concept (`concepts.py`,
  written `concept:<id>`, closed, flat, seeded from the formative library's 78 wound rows), or
  nothing. The appraiser seat and the actor's self-tags both pick from that; the engine validates
  by identity and refuses an unknown concept by code. That one semantic step is a model's and is
  committed to the chronicle before anything computes from it.
- **Wounds are engine state** (`baseline.wounds`, keyed concept@PATH; `wound.py`): minted at
  creation from the library or mid-story by `wound.mint` (a durable beat the seat read at one of a path's top two rungs, that path bound to a concept — intensity = the reading's height), recorded as `wound_minted` (schema v26), folded on resume. A
  wound enters the arithmetic ONLY as the investment above — never as a catalog row (the levers
  tier keeps the library's 14 dampening rows).

Every number here is a START tuned in runs, per the owner's 2026-09-10 ruling.

### Inherent nature: handled in the gain, by a bound, not by a second term

A character built to rest at rung 3 shows rung 3 in ordinary behaviour, and an honest sensor will
sometimes say so. Each such reading adds `v_3·g`, and if the sensor did it every beat the character
would compound out of his own nature: measured, the hot-tempered rung-3 character tagged at his own
rung every beat reaches *riled* in eight beats with nothing happening; read at rest on half of idle
beats he floors at *bristling*; on every beat, *outrage* (§8, 13). The floor is exact:

    floor = b / ( 1 − p · λ · g · r / (1 − r) )        p = the sensor's false-positive rate on idle beats

**The owner's decision (2026-09-07): this is handled by the gain on that path, so that the
accumulation rule stays one constant rule for every character and the character contributes one
factor.** The alternative — subtracting the vector of the character's baseline rung before
multiplying — zeroes the nature feed at any `p` and was measured to do so (§8, 14–16), but it puts a
second per-character number into the rule and was rejected on that ground: *"the control of how
quickly accumulation happens is a constant across all characters; this also makes running easier."*

**The gain is bounded, not designed.** Solving the floor for the gain that keeps a character inside
his own baseline rung gives a bound, computed in `build_profile` from numbers already on the sheet
and one assumed `p`:

    g_p  ≤  ( 1 − b / hi_b ) · (1 − r) / ( p · λ · r )        hi_b = the top of the baseline's rung

For the hot-tempered rung-3 character (`b` .245, `hi_b` .31, `r` .8, `λ` .15): at the sensor bar
`p` = 0.2 the bound is **1.75**, so his authored gain of 1.3 stands and nothing is lowered; at
`p` = 0.5 it is 0.70; at `p` = 1, 0.35. Under a sensor that clears the bar, no character in today's
gain range needs lowering. The bound exists for a worse sensor, and `lint_book` WARNs on a sheet
whose gain exceeds it at the assumed `p` — a computed guard, never a per-character judgment.

**What the bound costs when it binds.** A lowered gain lowers the response to real events by the
same factor: at `g` 0.35 the hot-tempered character under sustained *fury* reaches *riled*, where the
unlowered gain takes him to *outrage* (§8, 17). This is accepted as the price of one rule and one
factor, and it is why the assumed `p` should be the measured sensor rate, not a pessimistic guess:
every tenth of `p` above the truth taxes the character's real reactions for nothing.

### Why the loop is broken at the sensor and not in a state gate

The architecture has a loop the engine cannot see out of: the actor performs the rung the engine
handed it, the appraiser reads that performance, the engine adds the rung's vector. Four drafts
tried to break it in the arithmetic, and each was measured on the same hot-tempered character:

| where the break was put | idle character (nothing happening) | provoked character (tag held at rung k) |
|---|---|---|
| track toward the rung read (draft 1) | holds | converges to k — but a noisy sensor drags the state around every beat |
| vector = distance above the state (drafts 2, 4) | plain decay | never enters k; settles one to two rungs below it |
| vector measured from the baseline (draft 3) | feeds itself; calm slowed up to 7× | reaches φ of the way, never k |
| hard vector, gate "only above the stored rung" | plain decay | reaches k, gate closes, falls two rungs, gate reopens: a 4–6 beat sawtooth across three rungs |
| **hard vector, no gate, sensor tags events only** | **plain decay** | **enters k and holds inside it** |

The last row is the only one that gets both, and it gets them because the two cases really are
different events and only the sensor is in a position to tell them apart. **A man sitting in his
seething is not seething again.** That is a reading, not an arithmetic fact, and asking the arithmetic
to infer it from numbers is what produced every artefact in the table.

**What it costs when the sensor is wrong, exactly.** A character whose state is tagged on a
fraction `p` of idle beats is held at a floor above rest instead of returning to who they are, and
past a line is driven up:

    floor      = b / ( 1 − p · λ · g · r / (1 − r) )
    runs away  when  p · λ · g · r / (1 − r)  ≥  1      (p ≈ 1 at r 0.8 ; 0.57 at r 0.9 ; 0.27 at r 0.95, g 1.3)

Measured on the reactive rung-3 character (§8, 6 and 13): `p` = 1/4 floors him at *bristling*;
1/2 at *bristling* to *riled*; at `p` = 1 he climbs from a quiet room to *berserk*. There is nothing
in the arithmetic to stop that last case, by decision: the sensor rule is the stability condition,
and the gain bound above is its safety margin. The bar in §8 (`p` ≤ 0.2) puts the floor at 0.29,
inside his own rung, and sits under every runaway line in the table. §1's blindness rules are what
make the bar reachable: a sensor that cannot see the stored rung has nothing to echo.

**Why decay runs first.** Measured with the vector added first and decay after, the end-of-beat value
under a sustained tag never sat inside the rung named at any `λ` up to 0.20; the rung the engine
stored was always one below what the character was performing. Decay first, vector last, makes the
stored rung the truth of the beat.

**Why there is no cap.** Draft 5 capped a tag at the top of the rung it named. The owner's rule is
that a rung-2 tag on a rung-4 character still counts, and a cap cannot honour that without either
pulling the character down (the first cap did exactly that: an *annoyance* tag dropped a rung-3
character to *annoyance*, §8, 10) or zeroing the tag. So the cap is gone. What it was guarding —
overshoot — is mild without it: a single *fury* hit on an outraged reactive character lands at 0.87,
*fury*, not *amok* (§8, 4). What it was forbidding — a false-positive sensor climbing — is now
forbidden by the sensor bar alone, and the paragraph above says by how much.

**A hit counter is not needed.** Repetition already lifts a character above what each hit named
(above). A counter that raises each successive hit's vector was measured under the capped form
and changed only speed; under the uncapped form it would raise the runaway line's sensitivity to
`p` for no gain the multipliers do not already give. Left out.

---

## 4. The constants

**THE DECAY GLOBAL IS A HALF-LIFE IN MINUTES, PER PATH AND PER RUNG SINCE 2026-09-12** (redesign
gate 2; owner: "proper decay rates per emotion and per rung"). `state._HALF_LIFE` now holds TWO
ANCHORS per path — the EPISODE half-life (the measured excursion median, anchoring rung `_MID_RUNG`)
and the DISPOSITION half-life (the resting anchor, rung 1) — and `state._rung_half_life(path, k)`
derives all ~92 cells by geometric interpolation, short at the top (`_TOP_BURN`, the block's own
"the top cannot be sustained") and long at the bottom. `state.decay_over` STEPS a value down the
ladder, each rung draining at its own rate, so a multi-hour gap from the top cools fast through the
hot rungs and slowly through the cool ones. Reachability is a within-scene CONTINUOUS escalation
(elapsed 0, a beat carries no authored duration unless declared): the top is reachable continuously
and at a 2-minute beat, unsustainable only across a 10-minute gap, which is the design. The `r_p`
column below is the per-BEAT table the anchors replaced, kept for provenance. The `r_p`
column below is the per-BEAT table it replaced, kept for provenance; a beat had no duration, so
these were never time. **These half-lives are TEMPORARY, set 2026-09-11 from the first two live
reads** (section 5: Red Badge `readalong-red-badge-1789158299-9a8063`, Holmes
`readalong-holmes-1789164611-09007d`; owner: assign temporary numbers, generate a book, adjust on
what is produced). The episode zone is the thermometer's median half-life per path, rounded; the
sampling floor was about 25 minutes, so the fastest are floors. The disposition zone is
UNMEASURED — a five-beat thermometer cannot see a decay over days — and keeps each path's
previous ratio to its episode zone until a read with day-long gaps measures it. The START they
replace (60 / 120 / 180 / 240 / 1440 / 4320 / 4320 / 14400 in the episode zone) ran away on both
books; the measured fast-to-slow order also replaces the `r_p` column's guess: RECEPTIVITY
outlasts STIRRING.

| path | episode half-life (min) | disposition half-life (min) | measured (Red Badge / Holmes) |
|---|---|---|---|
| WARINESS | 30 | 360 | 26 / 54 |
| RECEPTIVITY | 70 | 840 | 70 / 68 |
| STIRRING | 45 | 720 | 33 / 54 |
| DISPLEASURE | 50 | 900 | 50 / 54 |
| GOODWILL | 90 | 900 | 23 / 129 |
| DISTASTE | 120 | 1200 | one point at 384 |
| DEFLATION | 40 | 1800 | 26 / none — three points at the floor; the rest zone is a JUDGMENT (a settled loss halves in thirty hours) so a loss still outlasts unease where the spec claims it |
| SELF-REGARD | 60 | 540 | 82 / 48 |
| LEVITY | 45 | 450 | unmeasured — a JUDGMENT beside STIRRING, its nearest kin; built 2026-09-11 by ruling |

**THE ATTITUDE STAIRCASE (2026-09-19, gate `attitude-staircase`).** Two tables, one shape. The
table above is the MOOD's. What one specific person has EARNED (`toward.erode`) now steps the same
ladder — one segment per rung, `decay_law.relax` the per-step primitive, `state.decay_over`'s own
loop — on the same MINUTE clock, at a slower per-path scale, resting at ZERO rather than at the
temperament mean (the attitude is a signed delta over the mood, and its rest is the authored
character). Until this gate it was the pre-redesign mechanism: one flat retention per path per DAY,
so a hatred at the top of DISPLEASURE's ladder and a flicker of annoyance at its bottom faded at the
same fraction, and the two tiers disagreed about the shape of forgetting. The new scale adds no
third table — it is read off the two that exist:

- **The bottom rung IS the old per-day rate, converted.** `toward._RETENTION[path]` was the flat
  retention per day, so rung 1's half-life is `MINUTES_PER_DAY · ln(0.5) / ln(_RETENTION[path])` —
  the half-life that reproduces that rate over 1440 minutes exactly. `toward._attitude_half_life`
  computes it; `tests/test_toward.py` block 16 asserts the equality against
  `relax(v, 0, _RETENTION[path], 1.0)` for all nine paths to 1e-9, and that equality is the whole
  reason the day rates can be carried forward at all. **Tag: `UNMEASURED`, carried over** — the
  values keep their pre-redesign `CALIBRATION` basis and this gate deliberately re-measured nothing.
- **Every other rung is THIS table's ratio.** `_attitude_half_life(path, k)` is the bottom times
  `state._rung_half_life(path, k) / state._rung_half_life(path, 1)` — read from the mood staircase,
  never re-chosen, so replacing an anchor or `_TOP_BURN` above moves BOTH tiers together. **Tags:
  the EPISODE anchors' `MEASURED` and the DISPOSITION anchors' / `_TOP_BURN`'s `JUDGMENT`,
  inherited rather than minted.**
- **The ordering survives the shaping.** The ratio is 1.0 at rung 1 by construction, so at the
  bottom the nine paths rank exactly as `_RETENTION` does: WARINESS fastest, then STIRRING and
  DISPLEASURE, GOODWILL, DISTASTE, DEFLATION slowest — the negativity bias `bonds` and `wound`
  already carry. Asserted as a half-life ordering DERIVED from `_RETENTION`, not re-typed beside it.

What it changes in practice: over 1440 minutes with nothing renewing it, a DISPLEASURE attitude at
the top of the ladder loses about 72% of itself where one at the bottom loses 5% — the bottom
number being, exactly, what the flat day rate always gave. **The unit changed with it:**
`src/engine/passage.py` hands `toward.erode` MINUTES; `bond_rest.drift`, `wound.erode` and
`arc.erode` still read the same one declaration in days, one tier per gate.

Retention over `m` minutes is `0.5 ** (m / (half_life · hold))`, the genotype's hold cell
multiplying the half-life (`state.retention_for`). **A FINDING, measured the day the clock landed
(`tests/test_genotype_balance.py` E1, `scripts/derive_genotype.py`):** with time real, one λ for
every path cannot stand — a false-positive idle reading every thirty minutes at λ 0.15 accumulates
faster than any path but WARINESS sheds it, so 459 of 464 genotype combinations drift out of their
rest rung at the section-8 sensor bar. The per-beat table had hidden this by implying a
28-minute beat on WARINESS and an 11-hour one on DEFLATION. **Superseded the same evening:** that count
rests on a sensor rate nobody has measured and a beat length the design does not fix, so the owner
ruled it is not a design input — λ stays 0.15 everywhere as the conservative start and moves on
evidence from runs; the sweep now REPORTS the idle floor and guards only reachability and rank
order. `derive_genotype.py` stays as a tool for the tuning loop.

| path | `λ_p` (vector scale) | `r_p` (RETIRED per-beat retention, provenance only) | provenance |
|---|---|---|---|
| WARINESS | 0.15 | 0.72 | r CARRIED from FEAR (startle disengages fast) |
| LEVITY | 0.15 | 0.75 | r CARRIED from PLAY |
| RECEPTIVITY | 0.15 | 0.75 | NEW: joy is context-contingent, sited with PLAY |
| STIRRING | 0.15 | 0.78 | r CARRIED from SEEKING (LUST's 0.80 dropped) |
| DISPLEASURE | 0.15 | 0.80 | r CARRIED from RAGE |
| GOODWILL | 0.15 | 0.82 | r CARRIED from CARE |
| DISTASTE | 0.15 | 0.88 | r CARRIED from DISGUST (revulsion outlasts its cause) |
| DEFLATION | 0.15 | 0.90 | r CARRIED from PANIC_GRIEF (the loss does not un-happen) |
| SELF-REGARD | 0.15 | 0.90 | NEW: standing is durable, sited with grief and contempt |

- **`λ`** is one value everywhere at the start on purpose: the per-path differences in how emotions
  arrive are already in `r`, and a second per-path knob before the first has been calibrated would be
  a guess dressed as a table. Split it per path when a run shows a path that climbs wrong.
- **`g`** — `profile.gains` as built today (`heritable.GAIN` 0.75 / 1.0 / 1.2 / 1.3, HEXACO
  modulation), rekeyed to path, **bounded** per path by the inherent-nature bound in §3 at the
  assumed sensor rate `p` (Class-B start 0.2, the §8 bar): `build_profile` clamps, `lint_book`
  WARNs. At `p` 0.2 no gain in today's range is clamped. The elevated-loop line `p·λ·g·r/(1−r) < 1`
  is the same expression; raising `λ` or `g` moves it toward the sensor bar, so check it when
  either changes.
- **`r`** — `profile.decay_rates`: `r_p ** (1 / hold)` since 2026-09-10, the genotype's hold cell on the path's rate in half-life units (the earlier `1 − (1 − r_p)·regulation / persist` form, floored at `_REG_FLOOR`, is gone with `effortful_control`), rekeyed to path. Half-life of an excursion at base: fear 2 beats, play 2.4, anger
  3.1, goodwill 3.5, distaste 5.4, grief and standing 6.6.
- **"Small"** is `λ`: one *anger* event on a neutral character lifts DISPLEASURE by 0.11 and is half
  gone three beats later (§8, 6). Reaching *anger* takes seven consecutive anger-level beats.
- **`h`** = 0.02.

**What retires from the emotion arithmetic:**

| retired | replaced by |
|---|---|
| `state._DIM_TO_PATH`, `_price`, `appraise` | the receipt step |
| `relevance_weights`, `_DIM_VALUE_KEYS` (event class × values) | nothing — rule 2 |
| regard / connection scaling of the empathy dims | nothing for emotion — rule 2; `bonds` keeps its own |
| the severity words AS THE EMOTION VOCABULARY | rung names; the words remain for the recorder's ACT read (§5 step 6) |
| `_UNBOUND_PHRASES`, `_REFLEXIVE_PHRASES`, `_PHRASES`, `_BANDS` in `direction.py` | rung blocks (after LEVITY has bands) |

**What stays, rekeyed (REVISED 2026-09-10):** `profile.gains` and `profile.hold`, now read per PATH from the genotype (`heritable.py`: hit / hold). `heritable.AXIS_FOR` and `_HEXACO_SENSITIVITY_MAP` are CUT — each was a second source of `g`, which section 3's one-rule-for-everyone forbids. `baseline.temperament` stays, and where a path RESTS is AUTHORED there as a word beside the voice (owner, later on 2026-09-10: temperament is a character design question); the mean decay relaxes toward is seeded from that word once. **`r` — the owner's decision 3 (section 9) is answered in the genotype:** the hold cell multiplies the path's HALF-LIFE, `r_eff = r_path ** (1/hold)`, never an absolute rate, so a per-path per-rung law authored later replaces `r_path` and the person term still means one ratio on every path. Rekeying is the basis rename (`emotion-paths.md`; inventory in the ledger).

**A FINDING AGAINST THE LIVE DRIVERS, 2026-09-10 — FIXED THE SAME EVENING:** section 8 pins its rows "decay first" and row 12 rejects vector-before-decay, but `scripts/scene.py` and `scripts/direct.py` ran `decay(appraise(...))` — the rejected order — until the evening gate reordered both (and the coherence probe) to decay over the beat's minutes first, then the receipt. Under it the clamp at 1.0 lands before the decay pulls back, and no ladder's top band is reachable by anyone (`tests/test_genotype_balance.py` E2 measured it; the sweep models the spec's order). Phase 3's receipt step is where the order is fixed.

**Dead keys.** Value weights and moral foundations AS EMOTION INPUTS become unread; `lint_book` WARNs
on them in the same gate that removes their readers. Not left silent.

**ONE CLOCK, TWO DRIVERS (2026-09-19).** The `elapsed` this section's half-lives are measured
against is minutes from the ONE declared clock (`clock.py`, 2026-09-10) — a scene's `at`/`lasts`,
or a chair session opened with `--at`. Until this gate only `scripts/scene.py` could reach it:
`src/engine/passage.py:open_scene` now holds the call (log the opening, derive the gap since the
last one ended, apply decay off it — plus the toward vectors, which since the attitude staircase
read it in MINUTES too, and drift, wound erosion and arc erosion, the three older tiers this same
declaration also feeds, in DAYS) and both `scene.py` and
`scripts/direct.py` dispatch to it the same way. A chair run with no `--at` still declares no clock
of its own (a beat has no duration; `--minutes-per-turn` is a separate, per-invocation knob) — see
docs/guide-operating.md.

---

## 5. When the engine receives a tag — the beat sequence

```
1  actor        produces {action, thought}   (no emotion self-tags — §7)
2  recorder     → typed EVENT facts as today (type, subject, durability, social read, ACT severity)
   appraiser    → READINGS for the acting character: what arose or intensified this beat (§1)
3  engine, acting character:
     every path          f ← b + (f − b)·r                      decay first
     each read path      f ← f + v_k·g                          the vector times the gain, wherever they sit
     rung with hysteresis; store f and R
     targets: retarget is REWRITTEN, not re-pointed —
              a reading with `about` binds path → about                   (rule 1's successor)
              a reading with no `about` leaves the bind untouched          (rule 4)
              a path back at baseline clears its bind                      (rule 5)
              a reflexive bind (about == me) is admitted per a PATH-keyed DIRECTEDNESS —
              BUILT (corrected 2026-09-19, was "does not exist yet" here): all nine rows are
              authored, `records.py:80-165`, rekeyed to the paths 2026-09-09 (every path admits
              self, by the owner's ruling; admits_role fails closed on an unknown key)
4  engine, every other present character: decay only
           BUILT 2026-09-22 (gate non-speaker-decay): `passage.bystanders`, called by scripts/scene.py
           each beat over the same minutes and room as the speaker's decay, on each bystander's own
           binds; the moods ride the turn as `TurnCommit.bystanders` -> one current_state row per
           present character per beat, and the manifest's `decay` records the cause (minutes, room,
           bystanders). An exited character stops decaying until the next opening
5  floor:  urge = salience·[landed ≠ False] + addressed + disruption − recency − inhibition
           BUILT 2026-09-19 (gate lands-on-to-floor): the seat's lands_on PRUNES the salience term
           (a listener the beat did not reach gets 0; a reached listener keeps the counterfactual
           appraise; no seat = today's rule). The flat LANDS_ON_BONUS form is NOT built: measured
           on every recorded beat with a seat reply, the seat listed every present listener,
           so a bonus would be a lowering of the floor, held with the drive-term question.
           disruption today reads tags.dimensions.social_violation — it moves to the recorder's
           act severity (step 6); lands_on ids pass through norm_id before the membership test
6  the act channel is UNCHANGED and separate: bonds.observe / act_from_tags read the RECORDER's
   event (type, attribution, severity word); tensions.fold_act reads the same for world tension.
   Emotion and relationship move on different channels from the same stream.
7  durable tiers, REWRITTEN to read readings:
     arc.assess    candidate when a reading's height ≥ the path's durable height, and is priced on
                   that height (the rung holding 0.60, `_DURABLE_DIM` carried) — gate
                   heights-price-arc, 2026-09-19: every path whose reading reaches it prices
                   height × the damage step, summed with any dims-priced term on the same path (two
                   receipts of one beat); "impact" := the beat's total addition Σ_p v_k·g; today it
                   returns None on any tag without `dimensions`
     wound.trial   keyed today by an authored class_dim in the event vocabulary; wounds rekey to a
                   PATH and trial reads that path's height
     toward.observe  keyed today by _DIM_TO_PATH; a SECOND feed built 2026-09-11 beside it —
                   toward.observe_readings: each PERSON-bound reading (about = a person id, not
                   "" and not concept:) adds its own vector v_k to what that person stirs, under
                   the tier's cap; the event route is unchanged
8  commit: TurnCommit.affect (nine keys) + rungs + binds + READINGS — a new append-only table
   (run_id, turn, actor, path, rung, about, confidence) in the same transaction as events/turns.
   Without it f and R are not re-derivable and hard rule 2 is false for emotion.
   records.PRIMARIES (retired 2026-09-08; now PATHS) and TurnCommit.validate gate on the eight old names — they rename with the basis.
```

Step 4 is the witness gap. Step 5 is its mitigation.

**PHASE 2 BUILT 2026-09-09** — step 8's table exists. `readings` (run_id, turn, actor, path, rung,
about, confidence), schema v24, append-only triggers fired by `tests/test_readings.py` rather than
assumed. `records.Reading` validates a rung NAME against the live ladder via `rungs.index_of`, so a
renamed or cross-path rung (`dread` on DISPLEASURE) fails loudly instead of resolving to the wrong
height. `TurnCommit` carries `readings` and `lands_on`; `ledger.append_turn` writes them INSIDE the
turn's transaction, beside the aboutness binds and for the same reason.

Deliberately **no UNIQUE** across (turn, actor, path): §3 step 2 ADDS each reading, so two readings
on one path in one beat are two additions and a UNIQUE would silently keep one. That is the opposite
of `target_binds`, which is last-write-wins and keys accordingly.

`readings.stub_readings` was the deterministic test double for Phase 3; it was DELETED 2026-09-09
(`staging/src/engine/RETIRED-stub_readings.py`) and `tests/test_readings.py` asserts its absence.

**PHASE 3 WIRED 2026-09-11** — steps 1-3 and 7-8 run in both drivers. After the actor's turn the
EVENT seat rates the act (dimensions, durability, subject, social — `scripts/appraiser.py`
`read_event`) and the EMOTION seat reads the interior (`read_emotion` → readings, lands_on, and a
measurement-only `about_missing` for a category the concept registry lacks). The receipt is
`state.receive`: decay first, then per reading `f ← f + v_k · g · connection(about) · q`, with
`impact = Σ v_k·g` for arc; aboutness is `targets.bind_readings` (an about binds, an empty about
leaves the bind, rest clears it); `arc.assess` takes the readings' heights as a durable candidate;
`wound.trial` reads the reading's height on the wound's path as the observation. Readings and
lands_on ride the turn's transaction. The actor's own self-tags remain the `--stub` double and the
fallback when a seat refuses (recorded on the turn as a SEATS note). Both seats run on the
frontier model through `scripts/provider.py` (owner: "we will not use local models, we need
accuracy"). Step 4 stays the witness gap; step 5's `lands_on` term is logged AND CONSUMED by
`floor.urge` (gate lands-on-to-floor, 2026-09-19 -- see step 5, above); `toward.observe` still
reads the event seat's dimensions.

**THE READING FEED (2026-09-11).** The owner: *"a man can be angry at one person but not at the
other."* On the first generated scene every reading about a person present moved the FLAT state —
the character was warmer with everyone in the room — and `toward` held only event-route rows. `toward.observe_readings` now runs beside
`toward.observe` in both drivers: a reading whose `about` is a person adds to what THAT person has
EARNED. Readings with no person (`""`, `concept:…`, or the character themself) are skipped.

**THE BALANCE (2026-09-12, the redesign's gate 1).** The scene ran with the feed on, and the
deferred question answered itself: with the person's vector ADDED onto the flat state, a reading
about a present person counted twice, and the composer sat two rungs above the stored state
(stored GOODWILL plus the person vector → rung 8). So the flat float is now the MOOD and
`current.toward` is ATTITUDE, and what the actor plays is composed per beat (`toward.balance`) and
never stored: toward the engaged person, `a` if `a ≥ m`, else `midpoint(m, max(a, rest))` — a
cooler person is met halfway down and never below rest — and the person the mood CAME FROM meets
it in full, which is what the owner's example needs (with A the mood plays; B is met halfway).
Whom it came from is read off the LOG — `ledger.raised_by`, the `about` of the last reading on each
path, handed to `assemble` in the slice — not off `current.targets`: that bind clears once a path is
within `_AT_REST` of rest (rule 5), which under the measured λ is nearly always inside one scene, and
on the fourth performance the person who had raised a character's GOODWILL above its rest was
met halfway down and the actor told "a little, they leave you cold". Others present lift a path to `_OTHERS_DAMP` × their attitude, never lower
one. Accrual into attitude: the reading's vector × `connection.magnitude_scale(for_about)` (the
receipt's own multiplier form; raw investment is zero below the floor and a stranger could never
become someone) × the durability gate (`_ATTITUDE_PASSING` on a passing beat, 1.0 on a durable
one — START, the Holmes set calibrates it). The cap is gone: attitude may reach any rung. The
balance reaches the actor as words: `scene.assemble` puts each present person's `effective − mood`
on the edge as `stirs` and `direction.direct_stirs` renders it (`actor-direction-format.md` §5).
Built since: per-rung decay (gate 2, 6ccf5c9); the descent SIGNAL (gate 3 wiring, 2026-09-15 — `balance` also returns `origin`, which branch set each path, because it is the function that knows; section 9 item 7 has the rule). `_ATTITUDE_PASSING` measured 0.5 (gate 4: Holmes, 106 of Watson's 111 readings about Holmes PASSING; 0.25 leaves a central relationship at the floor over twelve chapters, 1.0 is the runaway, 0.5 is about one rung per 14 beats — a judgment from one trajectory, no ground-truth target). Not built: the descent PROSE (gate 3b), the mood→attitude leak (deferred by the brief).

The two feeds can price the SAME person on the SAME path in one beat (the event seat names them as
the subject, care_relevant marked; the emotion seat reads protectiveness about them),
and `toward_deltas` is UNIQUE on (run, turn, perceiver, target, path) — the first beat with both
feeds live rolled back on exactly that and the scene died. `toward.coalesce` sums the rows per key
before the commit; both drivers call it on the line before `append_turn`. The constraint stays:
one row per key per turn is the log's contract, and the fold sums every row for a key before it
clamps, so one summed row is what two would have meant.

**THE READ-ALONG** (`scripts/readalong.py`, 2026-09-11) is the first bench for this arithmetic
that nobody here wrote: a public-domain novel through the emotion seat alone, the engine's
arithmetic downstream. Owner: *"we need to test real text to define real patterns we can use to
make the rules for our numbers."* So its output is a PATTERNS report — persistence after a peak
(the half-lives), elevated streaks (λ), the repetition delta split by presence (q), scar
re-encounter heights and spans (the wound multiplier), co-firing paths (the basis), the idle rate
(p; the two control books are the noise floor), the registry's gaps — with a second,
measurement-only THERMOMETER seat reading the standing level every N beats so half-lives are
fitted on levels over story time, not on arousals. The prediction `score` (pre-beat rung vs the
seat's reading, against rest) was RETIRED 2026-09-19 (gate `emotion-tier-tidy`) — both sides of
that comparison read off the same readings table, so it was self-referential. `state_vs_thermometer`
(`patterns`' own report key, `readalong._state_vs_levels`) is the comparison this section reports:
the engine's carried state against this THERMOMETER seat, which is independent of it. The corpus
and its sheets live under `$SWE_BOOKS/readalong/`, never here. First real-text run (stub seat, 184
beats of one novel, 2026-09-11) exercised every path of the
harness end to end.

---

**FIRST LIVE READ — Red Badge on Opus, one fresh agent per prompt, 2026-09-11** (run
`readalong-red-badge-1789158299-9a8063` in the book's `runs/`; 184 beats, 221 answers, 2 refused;
prompt version 3; the seat recorded as `subagent:opus`). Measurements, not rules — one book, a war
novel with a volatile protagonist; the two controls and the other three must agree before any of
this becomes a number here:

| what | Red Badge, measured |
|---|---|
| idle rate on the authored quiet beats (`--idle`, 30 prompts) | p = 4/30 = 0.13, every fire at a lowest rung |
| beats the seat fired on, in the novel | 176/184 = 0.957; 2.23 readings per fired beat; 27% of beats lowest-rung only |
| confidence | 358 likely / 34 sure |
| persistence of READINGS after a peak (median beats) | DEFLATION 0, DISPLEASURE 0, WARINESS 1, STIRRING 1.5, RECEPTIVITY 4 — the sensor reports what arose, so carrying is the engine's job, as designed |
| thermometer half-lives (median story-minutes; every 5 beats, beats a median of 5 min) | WARINESS 26, DEFLATION 26, STIRRING 33, DISPLEASURE 50, RECEPTIVITY 70, SELF-REGARD 82, GOODWILL 23, DISTASTE 384 (n=1). The sampling floor is ~25 min, so the 26s are floors. The START table (section 4) is 60 → 14400: two to a hundred and seventy-five times longer |
| the engine's state against the thermometer (37 points × 8 paths) | mean error 0.48 in height; REST alone errs 0.14; every path biased HIGH (median +0.18 DISTASTE … +0.76 DEFLATION); SELF-REGARD sits at 1.00 at the median, DEFLATION 0.93, GOODWILL 0.83; the thermometer sits at the lowest rung 66% of the time |
| the same beat, reading vs thermometer | mean difference 0.11 — what arises in a beat IS about the standing level at its end, and it is gone by the next sample |
| scars minted | war@STIRRING 0.90 and war@RECEPTIVITY 0.89 (ch1), combat@WARINESS 0.91 and death@WARINESS 0.91 (ch6), combat@RECEPTIVITY 0.89 (ch22), combat@STIRRING 0.97 (ch23) |
| co-fire (pairs in one beat) | STIRRING+WARINESS 24, DISPLEASURE+WARINESS 18, RECEPTIVITY+STIRRING 17, DEFLATION+STIRRING 15 |
| registry gaps the seat named | the regimental flag / the colours (5), the regiment and comrades (6), the enemy as a body (4), home and leaving home (3), enforced waiting (2) |

**WHAT IT SAYS.** Under the START the engine RUNS AWAY on real text — not by way of p (0.13 is
under the section 8 line) but because the half-lives are far longer than the clock the beats run
on: a beat lasts a median of five story-minutes, the seat lands about two readings on nearly every
beat, each adds up to λ·g·connection·q, and a path with a 60-minute half-life keeps 94% of itself
across a beat (a 14400-minute one keeps everything). The receipts stack faster than the decay can
drain them and the long-half-life paths pin at the ceiling by mid-book, while the text's own
standing level (the thermometer) is back at the lowest rung two samples out of three. Rest
predicts the thermometer three times better than the running state does. The direction is
unambiguous; the numbers are the owner's to set after the controls. The prompt's one format
defect (the path name written in lower case, 105 of 221 answers) is absorbed by the parser now and
will be said outright in prompt version 4.

**SECOND LIVE READ — Holmes (the first CONTROL: prose not about feeling), 2026-09-11** (run
`readalong-holmes-1789164611-09007d`; 421 beats, 506 answers, 0 refused; Opus, one fresh agent per
prompt; per-beat median 10 story-minutes). Beside Red Badge:

| what | Red Badge (war novel) | Holmes (control) |
|---|---|---|
| beats the seat fired on | 0.957 | 0.701 |
| beats with something ABOVE the lowest rung | 0.69 | 0.19 |
| readings per fired beat | 2.23 | 1.66 |
| what it reads most | WARINESS apprehension/alarm, STIRRING curiosity, DEFLATION deflation | STIRRING curiosity (124 of 171), RECEPTIVITY appreciation (49), GOODWILL fondness/warmth |
| aboutness (person / concept / unbound) | 119 / 152 / 121 | 175 / 59 / 257 |
| persistence of readings after a peak (median beats) | 0–1 (RECEPTIVITY 4) | 0–1 |
| thermometer half-lives (median story-min) | 23–82 per path | STIRRING 54, WARINESS 54, SELF-REGARD 48, GOODWILL 129 (n=18); the rest n≤1 |
| thermometer at the lowest rung | 0.66 of points | DEFLATION 1.00, DISTASTE 1.00, DISPLEASURE 0.99, SELF-REGARD 0.93, WARINESS 0.77, RECEPTIVITY 0.52, GOODWILL 0.31, STIRRING 0.04 |
| engine state vs thermometer, mean error in height | state 0.48 / rest 0.14 | state 0.37 / rest 0.05 |
| the same two books re-run on their STORED readings under the measured half-lives, λ still 0.15 (`tests/calibrate_accrual.py`, 2026-09-11 evening) | state 0.29 / rest 0.14 | state 0.19 / rest 0.05 |
| … and under the measured per-path λ (§2) | state 0.21 | state 0.11 |
| state medians at the thermometer points | SELF-REGARD 1.00, DEFLATION 0.93, GOODWILL 0.83 | GOODWILL 0.96, STIRRING 0.76, RECEPTIVITY 0.69 |
| uplift per single reading, as a multiple of λ·height | ×0.85–1.30 | ×0.64–1.68 |
| scars | six (war, combat, death) | two (collapse ch9, predator ch12) |
| registry gaps | the regiment, the enemy, the flag, home, waiting | an unsolved case / mystery (7), a precious jewel (4), a suspected fraud, an absent suspect, a way out |

**WHAT THE CONTROL ADDS.** (1) The seat discriminates the books: elevated beats fall from 69% to
19%, and what it carries on Holmes is Watson's curiosity and his warmth for Holmes — the two paths
the thermometer also finds carried (STIRRING at the lowest rung 4% of the time, GOODWILL 31%),
while the other six sit at the floor. (2) The runaway is NOT the multipliers: the measured uplift
per reading is 0.6–1.7 × λ·height on both books, so `connection`/`q`/`g` are behaving. It is the
half-lives against the clock: GOODWILL's 1440-minute half-life drains half a percent of its excess
per ten-minute beat while 51 fondness readings each add ~0.04, so Watson's GOODWILL pins at 0.96
against a thermometer median of 0.23. (3) Lowest-rung readings are the seat's normal background on
prose (51% of Holmes beats carry nothing else) and each one still receives; whether a lowest-rung
reading should move state at all is a design question the owner now has the data for. (4) Two
books agree: the thermometer's half-lives sit at 25–130 story-minutes per path, two to a hundred
times shorter than the START; readings do not persist (0–1 beats), so carrying is entirely the
engine's; and rest predicts the standing level better than the running state does, by 3× on the
war novel and 7× on the control.

## 6. Top and bottom

**Bottom.** No reading yields 0.0; decay converges to `b`. `emotion-dynamics.md`'s open question about
0.0 stays open and is not made worse.

**Top.** The peak rung is a change in kind (`emotion-scales.md`: at 1.00 *"the one in you who keeps
watch has stepped out"*). `recovery.py` (Symphony's post-amok refractory tier) was RETIRED to `staging/` on 2026-09-09 by owner's call — see `staging/RETIRED-RECOVERY-TIER.md`. It was
DISPLEASURE-only, keys on an integer peak rung 8–12 and a remembered peak this design does not yet
store, and is wired to nothing. **A hand-off is designed, not fed.** Feeding it needs a per-path
per-character peak with a reset rule and a rung-name → ordinal map; §9.

---

## 7. What changes for each seat

- **`appraiser.md`** — rewritten to §1: input the beat's `{action, thought}`, the moment, the
  PerceptSet, the nine ladders; output readings / lands_on / confidence; tags what happened, never
  what is carried; blind to stored rungs and to the baseline.
- **`recorder.md`** — keeps recording facts, including the act's severity word for `bonds` and
  `tensions`. It stops feeding emotion.
- **The actor's reply contract** (`prompt.py`) — loses `tags.dimensions` and the severity
  calibration paragraph (`appraiser.md` measured why: the one word the actor chose decided its own
  ceiling). Keeps `action`, `thought`, `exit`, `addressee`. `type` / `subject` for the recorder: §9.
- **`consolidation.validate_tags`** (Gate 4) — validates the recorder's event shape and the
  appraiser's reading shape (path ∈ nine, rung ∈ that path's ladder, about ∈ PerceptSet). Its
  dimension-mismatch arithmetic retires.
- **`gen_rungs.py`** — emits the vector table beside `BANDS` (`λ_p·height`, with per-rung overrides).
- **`records.PRIMARIES` (retired 2026-09-08 for `PATHS`), `DIRECTEDNESS`, `TurnCommit`, `TowardDelta`, `lint_book`** — the basis
  rename; not this document's to specify, but this document does not run without it.
- **The composer** — unchanged contract; reads stored rungs.
- **Migration of runs and sheets** — old `current_state.affect` rows are eight-key (two runs are
  seven-key); `R_prev` has no storage today. On first read under the new code: rename keys by the
  basis map, seed the two new paths at baseline, accept that hysteresis cannot hold on a run's
  first post-migration beat.

---

## 8. Falsification — the pinned expectations

Simulated 2026-09-07 on DISPLEASURE. Baseline rung 3 (*chafing*, `b = 0.245`), `r = 0.80`,
`λ = 0.15`, `h = 0.02`, decay first. These become `tests/test_emotion_arithmetic.py` verbatim.

| # | scenario | expected |
|---|---|---|
| 1 | sustained *anger*, `g` 0.75 / 1.0 / 1.3 | settles 0.62 (*seething*) / 0.75 (*anger*, entered at beat 7) / 0.90 (**fury**, past the rung named). **The multiplier sets height and speed; the vector table is untouched** |
| 2 | sustained *fury*, `g` 0.75 / 1.0 / 1.3 | 0.71 (*anger*) / 0.86 (*fury*) / 1.00 (**amok**, beat 10). The top is reachable, and the multiplier decides by whom |
| 3 | idle at *seething*, sensor tags nothing (the sensor rule) | 0.54, 0.48, 0.43, 0.40, 0.37, 0.34, 0.32, 0.31, 0.29, 0.28, 0.28, **0.27 (chafing)** — plain decay |
| 4 | overshoot: at *outrage* (0.81), one *fury* hit, `g` 1.3 | 0.87 (*fury*), then 0.74, 0.64, 0.56 — not *amok* |
| 5 | a rung-4 character (*bristling*) receives *annoyance* (rung 2) tags ×6 | 0.37, 0.36, 0.36, 0.35, 0.35, 0.35 — held near bristling instead of decaying to 0.28. **A tag below the state still counts** |
| 6 | idle at *seething*, reactive `g` 1.3, sensor tags the carried state at rate p | p = 1/4: floor ≈ 0.33 (*bristling*) · p = 1/2: 0.42–0.50 (*bristling*/*riled*) · **p = 1: climbs to *berserk* from a quiet room**. Floor formula `b/(1 − p·λ·g·r/(1−r))` gives 0.30 / 0.40 / runaway |
| 7 | escalation *chafing → riled → anger → outrage → fury*, then six idle beats | 0.28, 0.35, 0.44, 0.52, **0.60** during; 0.53, 0.47, 0.43, 0.39, 0.36, 0.34 after |
| 8 | one *anger* event, then silence | 0.35, 0.33, 0.31, 0.30, 0.29, 0.28, 0.27, 0.27 — half gone in three beats |
| 9 | repetition alone: *bristling* hits ×8 on the rung-3 character | 0.30 … **0.48 (riled)** — a rung above what each hit named. Steady-state levels of repeated hits: annoyance 0.32 · bristling 0.47 · riled 0.54 · anger 0.68 · fury 0.77 |
| 10 | the capped form (rejected): *annoyance* tag on the rung-3 character | fell to 0.18 (*annoyance*) on the first hit — the cap pulled the character DOWN to the rung named |
| 11 | the gated form "only above the stored rung" (rejected) | sustained *fury*, `g` 1.3: 0.88 → 0.75 → 0.65 → 0.74 → 0.81 → 0.87 … a sawtooth across three rungs |
| 12 | vector added before decay (rejected order) | under a sustained *anger* tag the end-of-beat value never entered *anger* at any `λ ≤ 0.20` in the capped form |
| 13 | **inherent nature:** the rung-3 character tagged at his own rung (*chafing*) every beat, `g` 1.3; and tagged at whatever rung he is in on p = 1/2 and p = 1 of idle beats | *riled* in eight beats; floor at *bristling*; *outrage*. Floor formula `b/(1 − p·λ·g·r/(1−r))`; gain bound at p 0.2 = 1.75 (his 1.3 stands), at p 0.5 = 0.70, at p 1 = 0.35 |
| 14 | *(alternative, not adopted)* baseline subtraction `max(0, v_k − v_b)·g`: the three cases of row 13 | 0.245 flat in all three; idle at *seething* with p = 1 settles at *riled* instead of *berserk* |
| 15 | *(alternative, not adopted)* same sustained *fury* under subtraction, calm rung-1 (`g` 1) vs hot rung-3 (`g` 1.3) | 0.60 (*seething*) and 0.80 (*outrage*) |
| 16 | *(alternative, not adopted)* rows 1–2 and 9 under subtraction | sustained *anger* `g` 0.75 / 1.0 / 1.3: 0.49 / 0.58 / 0.68 — one rung under the adopted form |
| 17 | **the adopted form when the bound binds:** hot rung-3 character at `g` 0.35 (the bound at p = 1) vs his authored `g` 1.3 | nature at p = 1: 0.30 (inside his rung) vs *outrage* · sustained *fury*: **riled 0.45 vs fury 0.86+** · one anger event: 0.28 vs 0.37. The cost of a pessimistic `p`; at the measured bar (p 0.2) the bound does not bind and none of this is paid |

Three tests need the sensor, not the arithmetic, and the first is now load-bearing:

- **Idle silence.** On beats where nothing happens to a character carrying an elevated rung, the
  appraiser must emit no reading on that path on **≥ 80%** of beats (p ≤ 0.2, which §8 row 4 puts
  below the one-rung floor). Below that bar the arithmetic cannot compensate and calm is lost.
- **Sensor accuracy on events.** The appraiser on this week's performed passages
  (`tests/perform_sort.py` corpus, known rungs): ±1 rung on ≥ 80%, exact on ≥ 50%.
- **Reads what the beat shows.** A stoic whose action stream is flat and whose thought stream is hot
  must be read at the thought's rung.

---

## 9. Open — the owner's decisions

1. **`λ`** — 0.15 global, or per path from the start.
2. **The idle-silence bar** — 80%, or stricter.
3. **Actor self-tags.** Recommend NONE: facts to the recorder, readings to the appraiser.
4. **The witness gap.** Recommend accepting it with `lands_on`.
5. **Durable-tier triggers** — 0.60 carried onto the height scale, or a named durable rung per path.
6. **Wounds rekeyed to paths** (`class_dim` → path) — every authored wound in every sheet changes.
7. **The top hand-off** — BUILT 2026-09-15 (the redesign's gate 3: wired e48e9f8, generator 485485b, 22 descent blocks ef68dfc). The retired tier's three faults are each answered without a peak store: per-rung decay MOVES the float (gate 2), so a man cooling from `amok` is met wherever the float actually is; direction of travel is read OFF THE LOG, not off a remembered peak — `descending[p]` = the balance's origin is the MOOD (not a person's earned attitude, not a present other's lift) AND the path was NOT read at the actor's most recent committed beat (`ledger.last_read_turn` vs `ledger.last_turn`; any reading is fuel) AND the mood's own rung is above the path's PIVOT (`rungs.PIVOTS`; DISPLEASURE's is anger, the one rung where a control is surrendered rather than lost); and each descent band ends on its own clock (the per-rung half-lives). `rungs.descending` is the one place the rule lives; `scene.assemble` stores it as `state.descending`; `composer.selectable` hands it to `rungs.block_for`, which swaps to a DESCENT block only above the pivot — inert until `DESCENT_BLOCKS` is authored. Two properties, not bugs: the +1-own-beat lag (the beat where fuel stops still renders the climb; descent first appears on the actor's SECOND own beat with no reading), and a plateau held by attitude keeps the climb block (a durable hostility toward the person present is not a come-down). `severed` belongs to the attitude tier (estrangement), never to a mood block. **Measured on the corpus, 2026-09-15** (the two read-alongs re-run from their stored readings under the current arithmetic — per-path λ, per-rung decay — then the signal computed beat by beat off the re-run's log, `tests/calibrate_accrual.readings_seat` + `rerun`; re-run dbs under each book's `staging/calibration/`): Red Badge (184 beats) crosses a pivot on 7 beats, all WARINESS at alarm/fright, and DESCENDS on 2 — each a single beat, each exactly the +1-own-beat shape (fright read at t, alarm committed unread at t+1, the alarm DESCENT block chosen at t+2, dread by the end of it); Holmes (421 beats) and the first generated scene of a live book never cross a pivot. The signal is not noisy; it is SPARSE — the measured λ and the short half-lives at the top make the rungs above a pivot hard to reach and quick to leave, so a descent block plays about once per hundred beats of a war novel and never in a drawing room. Not built: a hysteresis resolver (nothing in the corpus asks for one), the mood→attitude leak.
8. **STIRRING's `r`** — 0.78 (SEEKING) as written, or 0.80 (LUST).
9. **`h`** = 0.02 — must stay below the narrowest band.

---

## Cross-links

- **Replaces:** `state-engine.md` §appraisal, §decay (emotion only) · `emotion-scales.md` raised-by /
  lowered-by rows · the severity rubric AS APPLIED TO EMOTION.
- **Reads:** `rung_blocks.BANDS` (heights → vectors) · `baseline.temperament` (who they are) ·
  `profile.gains`, `profile.hold` (the character's multipliers; `decay_rates` was retired 2026-09-10 for the half-life form).
- **Feeds:** the stored rung → `scene.assemble` → the composer → the actor (`emotion-dynamics.md`
  §"three layers").
- **Needs:** the basis rename (`emotion-paths.md`; inventory in the ledger) · a `readings` table ·
  path-keyed DIRECTEDNESS · rewrites of `retarget`, `arc.assess`, `wound.trial`, `toward.observe`,
  `floor.urge` · the vector table in `gen_rungs.py`.
