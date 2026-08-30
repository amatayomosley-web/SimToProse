# Basis verification — the blind-judge confusion matrix

**Status: RESOLVED 2026-08-24 — §12 is the first run in this document's history whose bias-floor control was VALID.** Read §11 for what was wrong with the control and §12 for the result under the repaired one. Earlier framing, kept because the correction is the point: PARTLY RESOLVED 2026-08-23, and read §11 before citing §10. Three void runs, then a fourth whose CELLS reproduce and whose bias-floor control does not: that control was scored by a parser that counted refusals as answers and inverted replies naming their choice first. Corrected and re-run — every cell identical, the control VOID. The primary result stands as a reproducible observation; the assurance that it is not a judge-bias artefact does not. Results §9, verdict §10, the correction and its exact cost §11. The design in §1-§8 is as pre-registered before any arm executed; nothing in it was edited after seeing a result. Every outcome measure and
threshold in §5 is fixed BEFORE any arm executes, so no metric can be chosen after seeing a result.
This is step 4 of `emotion-basis.md` §"How the basis gets verified", which that doc says should run
**before adding anything to the basis** — and did not: DISGUST, the `attraction` dimension and
per-primitive targets all landed first. That ordering violation is recorded rather than reordered.

---

## 1. The question, and why this layer

`emotion-basis.md`'s failure table has four rows. Three point at the basis; one points somewhere
else entirely:

| observation | repair |
|---|---|
| a state no coordinate reaches | missing primitive |
| two distinct states, same coordinate | missing dimension (target, or a primitive) |
| a primitive appearing in almost nothing | not an element — a special case |
| **coordinates differ, rendered words do not** | **the direction layer is the bottleneck, not the basis** |

**The last row is the question.** The engine can now compute coordinates that differ — shame and
contempt carry identical magnitudes and different targets, measured. What is unverified is whether
the WORDS carry that difference to anyone. If they do not, every hour spent on the basis has been
spent on the wrong layer, and the repair is 55 phrases rather than a ninth primitive.

**Under test:** `direction.direct_affect` — given a state the engine can compute, do the rendered
stage directions let a judge recover which state it was?

**NOT under test:** whether an actor obeys the directions (director probe), whether state holds over
a long horizon (coherence probe), or whether the prose is good (the cut). Those are downstream and
each would be unattributable if this layer is the constraint. Cheapest falsifying test first.

## 2. Prerequisite — CLEARED 2026-08-22

`compounds.validate()["drift"]` reported 5 recipes carrying a role `records.DIRECTEDNESS`
disallows, and **three of the four role-only pairs this test exists to measure contained one of
them** — so the central measure could not have run without testing data the basis says is wrong,
and a failure would have been unattributable between "the direction layer cannot carry roles" and
"the recipe was wrong".

Repaired in gate `compound-drift-repair`: `jealousy` binds FEAR at the loss (a prospect, per the
basis's own recipe) rather than at the self; `pride` / `spite` / `smug` / `passive_aggressive` bind
PLAY at what the pleasure is IN rather than reflexively. Magnitudes untouched, so a later
separability shift stays attributable to the roles alone.

**`passive_aggressive` was predicted to collapse into `mocking` and did not** — measured 0.962,
inside the shade band `decision-engine.md` deliberately populates. It stays in the stimulus set. The
prediction was Fable's and the measurement overrode it, which is the right order.

Drift is now empty and the closest pair in the whole table is unchanged at contempt~scorn 0.986.
**All four role-only pairs are available as stimuli.**

## 3. Design — two arms, because one arm cannot attribute

The single most likely way to fool ourselves: run targets-on, see judges separate shame from
contempt, and conclude the targets work did it — when the magnitudes alone may already have been
enough.

| arm | render |
|---|---|
| **A — targets OFF** | `direct_affect(state, temperament)` — the pre-session engine, object phrases only |
| **B — targets ON** | `direct_affect(state, temperament, targets=…, me=…)` — reflexive variants live |

Same stimuli, same judges, same order-randomisation. **The deliverable is B minus A**, not B.
An improvement that appears in both arms was never about targets.

## 4. Stimuli — declared now, in full

Rendered by `compounds.blend()` onto ONE invented fixture (`characters/ren-traveler.json`;
CLAUDE.md hard rule 1 — no book cast), so baseline is held constant and only the state varies.

- **Group M — the motivating case (3):** shame, grief, contempt. `emotion-basis.md`'s own example:
  "a man who just buried his brother and a man just publicly humiliated receive identical
  directions."
- **Group R — role-only pairs (2–4, pending §2):** cold~embarrassment, plus any pair that survives
  the drift repair. These are the ones targets were built for.
- **Group S — the shade family (3):** contempt, disdain, scorn. **Confusion inside this group is a
  PASS, not a failure** — `decision-engine.md` wants them as neighbouring coordinates on purpose.
  Scored as its own class.
- **Group P — single primitives (8):** each of the eight alone, at the `strong` band. Asks whether
  DISGUST reads as revulsion rather than fury, and whether any primitive is invisible.
- **Group C — controls (3):**
  - *planted duplicate* — one Group M state rendered twice at different list positions. Judge
    disagreeing with itself sets the reliability floor and caps every other number.
  - *resting state* — the fixture at temperament, nothing notable. A judge naming a state here is
    confabulating, and the rate bounds all positive findings.
  - *LUST unbound* — does "you are restless with wanting, and no one in the room is why" read as
    desire without an object, or get attached to a person the judge invents?

## 5. Outcome measures and thresholds — FIXED BEFORE ANY ARM RUNS

Judges see one rendered direction line and a closed candidate list plus "none of these". No sheet,
no numbers, no target names, no intended label. Three judges from three FAMILIES —
`qwen2.5:32b`, `gemma4:31b-it-q4_K_M`, `mistral-small` — so a single model's idiom cannot carry the
result. Order randomised per judge.

| # | measure | threshold for "the direction layer carries it" |
|---|---|---|
| 1 | exact match, basis-valid non-shade states | **≥ 40%** (chance ≈ 5% on a ~20-item list) |
| 2 | shade-family match (S collapsed to one class) | **≥ 65%** |
| 3 | shame NOT called grief | **≥ 2 of 3 judges** |
| 4 | role-only pairs separated | **≥ 2 of 3 judges**, per surviving pair |
| 5 | resting control names a state | **≤ 1 of 3 judges** |
| 6 | planted duplicate self-agreement | **≥ 2 of 3 judges** agree with themselves |

These numbers are a judgement call made blind, and they are deliberately modest: naming an emotion
from behaviour alone is hard for a person. **If measure 6 fails, measures 1–4 are uninterpretable
and the run is void** — an unreliable judge cannot falsify anything.

## 6. What each result licenses

| result | reading | repair |
|---|---|---|
| B passes, B >> A | targets carry aboutness to a reader | none — proceed to the director probe |
| B passes, B ≈ A | the distinctions were in the MAGNITUDES; targets bought nothing legible | keep targets for `_regard` and `recognise`, stop investing in reflexive phrases |
| both fail measure 1 | **the direction layer is the bottleneck** | rewrite phrases; STOP work on basis size |
| measure 5 fails | judges confabulate; every positive number is suspect | tighten the judge prompt, re-run |
| a Group P primitive never recovered | that primitive is invisible in words | its four phrases, not its existence |

## 7. Falsification of the session's own work

**The targets build is falsified if B ≈ A on measures 3 and 4.** That is the honest bet being
placed: the reflexive variants exist to make shame legible as shame, and if a blind judge cannot
tell shame from contempt any better with them than without, the seven phrases and the registry
bought correctness with no observable consequence.

Recording that in advance so the result cannot be reinterpreted afterwards.

## 8. Known limits, stated before the result

- **Judging a coordinate from behaviour is not the same as reading a scene.** A high exact-match
  rate says the words are distinguishable, not that they are good.
- **Local quantised models.** Three families reduce idiom risk; they do not eliminate model-class
  effects, and none of these is a strong model.
- **One fixture.** Baseline is held constant deliberately, so the result speaks to the phrases and
  not to the interaction between a character's temperament and the bands. That interaction is a
  separate arm and is not run here.
- **The candidate list makes this recognition, not recall.** Easier than naming unprompted. A
  failure here is therefore strong evidence; a pass is weaker than it looks.

---

## 9. RESULTS — run 2026-08-22, VOID

Two runs of the 25-way protocol, then a redesign. Raw judgements in
`tests/basis_probe_results.jsonl`.

### Run 1 — void on the instrument

34% of judgements (55 of 162) were lost: gemma4 returned EMPTY strings, and qwen answered "just
seek and nothing else" where the option read "just seeking and nothing else". The empty-reply cause
was already documented in this repo — `scripts/direct.py:109`, "the hidden trace otherwise consumes
the token budget and empties the reply" — and the probe simply had not asked. Fixed with
`think: False`, a 200-token budget, and NUMBERED options a judge answers with a digit.

**Measure 5 failed on a mis-specified control, not on judges.** The "resting" control was the
fixture at its own temperament, and it renders FOUR ACTIVE CLAUSES. `direction.py:201` —
`notable = b >= 1 or abs(dev) > _DEV_THRESH` — surfaces any primitive whose ABSOLUTE band clears
0.25, whether or not it has moved. Measured on `characters/ren-traveler.json`: SEEKING 0.50 (band
1), CARE 0.55 (band 2), PANIC_GRIEF 0.25 (band 1), PLAY 0.35 (band 1) all surface at rest. The
judges naming a state there were right. A genuinely flat fixture renders "nothing here pulls at
you, so act as you ordinarily would", and that is now the confabulation control; the
at-temperament case is reported as finding 5b with no threshold attached.

### Run 2 — instrument sound, VOID on measure 6

Unparsed fell to 0.6% (1 of 168) and the flat control passed 0 of 3. Measure 6 failed anyway:

| judge | arm | shame | duplicate (same line, options reordered) | |
|---|---|---|---|---|
| gemma4 | A | grief | cold | DISAGREE |
| gemma4 | B | cold | grief | DISAGREE |
| mistral-small | A | just fear… | shame | DISAGREE |
| mistral-small | B | shame | grief | DISAGREE |
| qwen2.5 | A | shame | grief | DISAGREE |
| qwen2.5 | B | cold | cold | AGREE |

**Five of six judge-arm pairs answered differently to the identical rendered line.** Per-judge
exact match ran 4.5-18.2% against ~4% chance. Those are one finding, not two: a near-chance judge
necessarily disagrees with itself.

### What is and is not concluded

- **VOID.** §5 says a measure-6 failure makes 1-4 uninterpretable, and it does.
- **§7's falsification did NOT fire.** B-minus-A came out +0.0 on the differing subset and -9.1
  overall, but a void instrument cannot falsify — and cannot vindicate. **The per-primitive targets
  work is untested, not disproven.** Recorded so the -9.1 is never cited as evidence against it.
- **PROVENANCE GAP.** `tests/basis_probe_results.jsonl` holds 168 rows — run 2 only. Run 1's 162
  judgements were deleted before run 2 and are on disk nowhere. The run-1 void verdict above rests
  on this document's word alone, which under this project's one-source rule is not evidence. Stated
  rather than quietly carried.
- **This says nothing yet about the direction layer.** The failure is at the JUDGE. 25-way emotion
  recognition from behaviour alone is beyond these local models, so the question in §1 is still open.
- **One real finding survives, from the broken control:** a character at rest is issued four
  standing stage directions, one of them at STRONG band. Whether disposition should speak that
  loudly every beat is a design question this probe surfaced by accident and is recorded in
  `emotion-basis.md` rather than left in a log.

### CORRECTION 2026-08-23 — run 3 could not have measured targets

Recounted from the raw JSONL after Fable examined it. Of the twelve pair-member stimuli in run 3,
**the arms differed on three.** Three separate reasons, and the first is self-inflicted:

- **`ROLE_PAIRS` went stale by this project's own hand.** Gate `compound-drift-repair` re-authored
  `passive_aggressive` and `spite` to all-object binds, and `basis_probe.py`'s `ROLE_PAIRS` was
  never re-derived. Verified: `mocking`, `passive_aggressive`, `spite` and `excited` now carry
  roles={object} only. Two of the four "role-only pairs" carried NO target content when the probe
  ran.
- **`cold`~`embarrassment` is a role pair on paper and empty at render.** embarrassment's
  `DISGUST (0.20, "self")` blends to 0.2375 — under the 0.25 band floor, deviation 0.0875 against a
  0.15 threshold — so its reflexive ingredient produces no clause and the arms render identically.
- **The one cell where arm B genuinely widened the gap** (`excited`~`pride`, 1 differing clause to
  3) was answered "pride" 24/24 across both arms and both orders. A manipulation cannot be measured
  in a cell the stimulus does not reach.

**So the earlier conclusion here — "targets bought nothing legible" — is an OVER-READ and is
retracted.** The defensible statement is narrower: *two instruments have failed to detect
reader-side benefit, and on real blends the reflexive variants produce at most one substituted
clause against a 5-7 clause shared body.* That lowers the posterior on the phrases' practical
weight. It does not settle whether they carry aboutness to a reader who can compare.

**The direction layer is also NOT convicted.** Every 50% pair sits at recipe cosine 0.948-1.000 —
near-identical coordinates rendering as near-identical words is the renderer being FAITHFUL. The
failure-table row needs DISTANT coordinates collapsing, and the one distant pair (cosine 0.564)
rendered 6 differing clauses and was read at 92%. The layer took one test and passed it.

**Judge reliability was fine in run 3**, unlike run 2: 3 order-flips in 72 duplicated
presentations, all from mistral-small; gemma4 and qwen2.5 flipped zero times in 48 each. The
constant answers are a stable policy, not noise — more n in that format would never move those
cells.

### The redesign — forced choice

25-way recognition is the wrong instrument for a near-chance judge. `--pairwise` asks a forced
choice between TWO named states, chance 50%, over exactly the six discriminations the design claims
to make (shame/grief, shame/contempt, and the four role-only pairs). Both orderings of every pair
are run, so an order-preferring judge scores 50% rather than 100%. Same blinding throughout.

---

## 10. VERDICT — run 4, comparative (see §11: the bias-floor control was NOT valid)

Raw judgements in `tests/basis_probe_results_compare.jsonl` (66 rows); run 3's in
`tests/basis_probe_results_2afc.jsonl` (144). Named here because §9 flags run 1's missing raw as a
PROVENANCE GAP and it would be the same gap to let the run that PASSES rest on this document's word.

The three earlier runs could not reach the question (§9 CORRECTION). Run 4 fixed both defects at
once: **isolated** stimuli (one vector, rendered twice with only the target flipped, so magnitudes
are identical by construction) and **comparative** presentation (both renders shown, judge assigns
the names) — the second because run 3's judges were near-perfectly self-consistent and still
answered one constant name per pair, a stable policy that no amount of extra n would move.

Crossed with a fixture axis so the same run rules on the noise floor: each pair rendered on the
ordinary fixture (four standing at-rest clauses present) and on a flat one (the differing clause is
most of the text).

    CONTROLS
      positive (shame|contempt, full blend)  12/12   (void if < 10/12)   OK
      bias floor (identical renders)         ONE 2 of 5  (void outside 2-10)   OK

    CELLS                          flat        ordinary
      disgust  (contempt|shame)    11/12       12/12
      seeking  (excited|pride)     12/12       12/12

    PRIMARY  flat pooled  23/24   (pre-registered threshold >=18/24)   PASS
    FLOOR    ordinary     24/24   -> noise floor HARMLESS at this legibility level

### What is now established

- **The reflexive phrases carry aboutness to a reader.** Identical magnitudes (DISGUST 0.556,
  RAGE 0.572), only the target flipped, and judges recover shame from contempt at 11/12 —
  12/12 for pursuit vs display. `tests/test_targets.py` could only assert the two strings DIFFER;
  this measures that the difference is legible.
- **The noise floor is harmless at this legibility level.** Ordinary 24/24 against flat 23/24: the
  four standing clauses cost nothing when the differing clause is a genuine substitution rather
  than an absence. `direction.py:201` stands. **Salience grouping is NOT indicated by this
  evidence** — which retires, for now, the repair §9 pointed at.
- **§7's falsification does not fire.** The bet was that B would not beat A; on stimuli that
  actually carry the manipulation, it does.

### The instrument failed three times, and how

Recorded because the failures were more instructive than the result:

1. **Run 1** lost 34% of judgements to gemma4's thinking trace — a failure documented in this
   repo's own `scripts/direct.py:109` and not read before building the probe.
2. **Run 2**'s control was mis-specified: "at temperament" is not "nothing happening", and the
   judges naming a state there were right.
3. **Run 4's first pass** carried a spurious term in the scorer that could only ever produce
   chance — and did, on the positive control, a pair already known readable at 92%. It printed
   "the phrases fail REGARDLESS of floor" as a pre-registered conclusion. **A scorer that can only
   output chance is indistinguishable from a null result**, and the only thing that caught it was
   the positive control existing at all. That is what controls are for, and they earned their cost
   three times over in one afternoon.

Two guards now exist so these cannot recur silently: `ROLE_PAIRS` is DERIVED from the compound
table rather than hand-listed (it had gone stale by the drift repair's own hand), and a dead-cell
check warns when a pair renders identically in both arms.


## 11. CORRECTION — the answer parser, and what it does and does not cost §10

Found 2026-08-23 while re-measuring §10's cells against a rewrite of `direction.py`'s phrases.
`run_compare` read the judge's answer as:

    got = "ONE" if ("ONE" in r and "TWO" not in r) else ("TWO" if "TWO" in r else None)

A SUBSTRING test over the whole reply. Wrong in two directions at once:

- `ONE` is a substring of **n**ONE, d**one**, al**one**, some**one**, so a REFUSAL scored as an
  answer. `"none of them"` registered as the answer ONE.
- Any reply that named its choice and then discussed the alternative INVERTED, because
  `"ONE. Actor two is calmer"` contains TWO and fell to the second branch. Measured live: qwen2.5
  replied `"ONE

The description provided does not actually differentiate..."` to the bias-floor
  stimulus and was recorded as **TWO**. That is a directional bias against ONE, produced by the
  scorer, inside the control whose only job is to detect directional bias.

**How it surfaced, and the lesson about instruments.** A rerun's bias floor voided where the
previous run's had passed — with mistral-small returning the SAME refusal both times. The log could
not explain that, because `raw` was clipped at 40 characters: the same PROVENANCE GAP this document
already records for run 1, in a different place. A stored result that cannot be re-derived from the
stored evidence is not a measurement. `raw` is now 400 characters and `test__choice` pins 14 real
reply shapes, including every string named above.

### What the fix costs §10, precisely

Re-run 2026-08-23 with the corrected parser, on the SAME strings §10 measured
(`tests/basis_probe_results_compare_oldstrings.jsonl`):

    positive control                      12/12   OK          (unchanged)
    disgust     flat 11/12  ordinary 12/12        (unchanged)
    seeking     flat 12/12  ordinary 12/12        (unchanged)
    PRIMARY     flat pooled 23/24  PASS           (unchanged)
    FLOOR       ordinary    24/24                 (unchanged)
    bias floor  answered ONE 1 of 3    VOID       <- THE ONLY THING THAT MOVED

**§10's cells reproduce exactly. Its control does not.** The recorded "ONE 2 of 5, OK" counted
refusals as answers; scored correctly the same judges answer 3 of 6, one of them ONE. So §10 is not
refuted — it is UNCONTROLLED, which is a smaller claim than it has been making. The primary result
stands as a reproducible observation; the assurance that it is not an artefact of judge bias does
not.

### The control is also mis-specified, and this is NOT being changed to rescue a run

`2 <= first <= 10` is an ABSOLUTE count. Its denominator is however many judges chose to answer,
and refusing is the CORRECT response to two identical renders — so the better the judges behave,
the more certainly the control voids. At n=3, `1` is the least-biased outcome available and it
still fails the band.

The threshold is deliberately left alone. Retuning a pre-registered criterion after seeing the data
it just failed is the move this document spent three void runs learning not to make. The rate-based
form is pre-registered HERE, for the next run, before that run is drawn: **report ONE as a
proportion of ANSWERED floor rows, void outside 0.2–0.8, and void separately if fewer than 4 of 6
rows answer at all** (too few answers is its own finding — it means the judges will not play the
control, not that bias is absent).

### The A/B this was run for

Old strings and new strings, same session, same judges, same corrected parser:

    cell                    old          new
    disgust  flat          11/12        11/12
    disgust  ordinary      12/12        12/12
    seeking  flat          12/12        12/12
    seeking  ordinary      12/12        11/12
    PRIMARY  flat pooled   23/24        23/24

One judgement apart, in one cell, on a void control. **That neither vindicates nor falsifies the
rewrite.** The rewrite ships on defects that need no judge — a grief clause rendering one period
from the identical condition clause, intensity markers appended to absence phrases, and three cells
stating their band as a quantity — all of which are readable in the output and are recorded in
`.depth/` gate `stage-direction-collisions`.


## 12. THE CONTROL WORKS — run 5, 2026-08-24, and the first valid bias floor

§11 pre-registered a replacement for the bias-floor control BEFORE the next run was drawn, because
retuning after seeing a failure is what the three void runs taught this document not to do. This is
that run. Two arms, same session, same three judges, same corrected parser and same repaired
control; the only difference between them is `_UNBOUND_PHRASES` gaining CARE and DISGUST cover.

    CONTROLS                                pre-cover        with cover
      positive (shame|contempt)             12/12  OK        12/12  OK
      bias floor (identical renders)        2 of 6  OK       3 of 8  OK      <- VALID, both arms

    CELLS                     flat / ordinary
      disgust  (contempt|shame)             11/12  12/12     11/12  12/12
      seeking  (excited|pride)              12/12  11/12     12/12  12/12

    PRIMARY  flat pooled                    23/24  PASS      23/24  PASS
    FLOOR    ordinary                       23/24            24/24

**What this settles.** §10's primary result was reproducible under a corrected parser and
UNCONTROLLED, because the floor it relied on was scored by a parser that counted refusals as
answers and by a band whose upper arm was unreachable. Under twelve asks and an exact binomial test
the floor passes on its own terms, in both arms. The 23/24 is now a controlled observation rather
than a reproducible one, which is the claim §11 had to withdraw.

**What it does not settle.** The cover moved `seeking` ordinary from 11/12 to 12/12 and the pooled
floor from 23/24 to 24/24 — ONE judgement each, which is noise at this n and is reported as
no-regression, not as improvement. CARE stands unbound in every ordinary-fixture render, so the
cover genuinely changed those stimuli; that it changed them without cost is the finding.

**The floor's own numbers are worth reading.** Six of twelve asks answered in one arm and eight of
twelve in the other — the judges decline to separate two identical renders roughly half the time,
which is the CORRECT response and which every earlier form of this control punished. That is why
the criterion is now a proportion tested against chance with a separate minimum-answers void, and
not a count.
