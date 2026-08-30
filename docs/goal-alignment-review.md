# Goal-alignment review — the spider test against the shipped engine

*2026-08-22. Method: every claim below was established by reading the named file:line or by running
code against the engine (`src/engine/` direct calls; fixtures constructed for this review live in a
session scratchpad, not in this repo — the tree stays book-free per CLAUDE.md rule 1). The verify
suite (10 suites + test_subject) is green at the reviewed state. Where a limit is asserted, the
run that established it is described inline.*

**The goal under review (the owner's words):** numbers for emotions, calculated and derived, given
to the LLM as direction — so that "brave but morbid fear of spiders" produces flee-when-alone and
maybe-fight-when-protecting, *depending on the other numbers*, with no "coward" tag anywhere.

**One-line verdict:** the engine's built half (temperament → current state → direction) is real,
disciplined, and proven — but the tier that the spider test actually exercises, the **effective-
state catalog / buff-debuff registry** that `decision-engine.md` §effective-state and
`state-engine.md` §"Then the catalog (done)" fully specify, has **zero lines of implementation**.
FEAR has one global gain per character (`state.py:234`); nothing keys any emotion to an object,
and no standing condition (ally present, child at risk) modulates any lever. The spider test
fails today — measurably, not rhetorically — and the design docs already contain its exact fix.

---

## 1. THE SPIDER TEST

### The fixture

Character **C = "Ren"**, built to the schema the three real books use (verified against
`characters/maren-healer.json` and all 14 book characters via `src.engine.vault.load_book`):

- **Brave in general:** `fixed.genotype.threat_reactivity: "low"` → `gains["FEAR"] = 0.75`
  (`state.py:234`, `_ALLELE` table `state.py:26-31`); `traits.emotionality.mean 0.35` →
  ×(1 + 0.7·(0.35−0.5)) = ×0.895 (`state.py:138,245-249`) → **effective FEAR gain 0.671**.
  `temperament.FEAR.mean 0.25` (resting at the bottom band edge).
- **Morbid fear of spiders:** `baseline.drives.fears_wounds[0] = {fear: "spiders — a morbid,
  bodily dread…", intensity: 0.95, trigger: ["a spider", …], protects, wound, defense: "flee"}` —
  the exact shape `drives-schema.md:33-43` specifies and that two characters of an active book
  Point* author (including the `intensity` number).
- A lived vault belief: *"a hunting spider's bite left me three days blind when I was a boy"*
  (confidence 0.95) — the one per-object channel the engine has.
- **P = "Joss"**: `current.relationships.joss = {trust .80, affinity .90, respect .60, debt 0.0,
  history: "his sister's boy; Ren swore to see him home"}`; active goal "see Joss safely home."

Scene A event: *"A massive spider … drops from the dark above the one narrow ledge out, fangs
working. Ren is alone in the deep gallery."* Scene B: same, plus *"Joss is pressed against the
wall behind Ren."* Actor self-tags held constant at `threat 0.7` (B adds `care_relevant 0.5`,
`subject: "joss"`), per the calibration instruction the prompt itself gives (`prompt.py:73-77`).

### Q1 — Can the sheet represent "brave but morbid fear of spiders"?

**As authored text: yes. As an operand: no.** The field exists (`baseline.drives.fears_wounds`),
the schema gives it a number (`intensity`), all three books use it. But grep of `src/` and
`scripts/` finds **zero Python consumers** — the only mention is a comment (`scene.py:163`).
It reaches the actor solely as verbatim JSON inside the identity prefix
(`scene.py:180` → `prompt.py:49`). This is not an accident the project missed:
`character-authoring-rules.md` Rule 6 states it plainly — *"passed to the LLM verbatim … The
engine never parses them."* So the sheet holds the phobia the way a note in the margin holds it.
No number derived from it ever enters a computation. (Control run: deleting the entire
`fears_wounds` entry left `build_profile()` and `appraise()` outputs **byte-identical**; only the
identity prompt text changed.)

### Q2 — What does `appraise()` compute for the spider event?

Scene A, executed (`state.py:291-371`):

```
threat 0.70 × relevance 0.520 × gain 0.671 × sensitivity 1.00 × push +0.45 × rscale 1.000
  = +0.110 → FEAR
FEAR: 0.250 (resting) → 0.360 (appraised) → 0.329 (after decay, committed)
```

- `relevance 0.520` is `_DIM_VALUE_KEYS["threat"]` = 0.2·needs.competence + 0.8·schwartz.security
  (`state.py:91`) — character-global, not object-keyed.
- The word "spider" appears **nowhere** in this computation. The identical arithmetic fires for a
  rockfall, a wolf, or a drawn knife at the same self-tagged severity. The phobia's 0.95 intensity
  is not a term.
- **The flee ceiling, computed:** max one-beat ΔFEAR at severity 1.0 is +0.157; under *sustained*
  maximum threat re-appraised every beat (decay r = 0.72), the equilibrium is
  0.25 + 0.157·0.72/0.28 = **0.654** — permanently short of the 0.80 "gripping" band whose
  direction is "you protect yourself first" (`direction.py:16,33`). **A brave character's computed
  fear can never reach the flee band, for any threat, ever.** The single global gain makes
  "brave" and "morbid specific fear" arithmetically incompatible — the exact no-nuance failure
  the goal statement attributes to the "coward" tag, reproduced in numbers.

### Q3 — What does the actor actually receive?

Rendered via `build_turn_messages()` (`prompt.py:27-87`), scene A, in full in the trace; the
load-bearing lines:

```
How to play this moment - stage directions, drawn from your state. Act on them; they are what
you DO, not a mood to describe: you drive at it and pull the others along with you; you keep
the ways out in view and let someone else commit first; you answer sharper than you meant to
and do not soften it; you will do a small thing for someone near you if it costs you little;
you are slower to answer, and you leave some things unsaid; you allow one small joke and let
it pass. you can do the thorough version where it matters.
Active goals: [{"goal": "see Joss safely home over the pass", "urgency": 0.8}]
What you perceive THIS moment (...):
[{"ref": "evt.a_massive_spider__broad_as_a_s", "channel": "event", "fidelity": 1.0,
  "attributes": ["confinement", "creature", "threat"], "must_surface": true}]
What it brings to mind: nothing in particular
Those present, as you stand with them: no one in mind
The moment: A massive spider, broad as a shield, drops from the dark above the one narrow
ledge out, fangs working. Ren is alone in the deep gallery.
```

Five observations, all measured:

1. **Six parallel stage directions at rest.** With `notable = band ≥ 1` (`direction.py:122`),
   6 of Ren's 7 primaries surface *before anything happens* (SEEKING 0.55 is band 2:
   "you drive at it and pull the others along with you" — leading the line while he stands alone
   in a cave). Clause order is fixed `PRIMARIES` tuple order (`records.py:10`), so position
   carries no salience information.
2. **The spider left no trace in the direction.** Post-event FEAR 0.329 and resting 0.25 are the
   same band and the same side of the ±0.15 deviation marker → the next turn's staging line is
   **byte-identical** to the resting one. The engine registered the spider and the actor's
   instructions did not change.
3. **The phobia arrives as identity JSON** — including its raw `"intensity": 0.95` digits. The
   one number attached to the fear lives *in the prompt* and is read *by nothing in the engine* —
   the design law ("numbers live in the DB; directions live in the prompt", `design.md:87`)
   inverted, not merely unimplemented.
4. **Recall is empty.** The spider memory did not surface. Cause, isolated by direct calls to
   `perception_scope`/`extract_triggers`/`run_gate`: trigger strings are built from percept
   *attributes*, which for a lexicon-matched event are the **class names** ("creature"), not the
   event's own words ("spider") — and for any event with `kind ≠ "mundane"` the generic
   leading-words floor never fires (`gate.py:378-391`). The word "spider" cannot become a trigger
   through normal authoring. (Workaround that works today: name the lexicon class itself
   `"spider"`.)
5. **Gate-5's law is enforced on four surfaces and leaked on three.** `test_direction.py` proves
   `direction.py` output digit-free; but the assembled prompt carries raw digits from the identity
   block (trait means, model weights, goal priority/satisfaction, fear intensity), from
   `Active goals` (`urgency: 0.8`), and from percept `fidelity` (`prompt.py:78` `json.dumps`).

### Q4 — Does the presence of P change anything computable?

Four things change, **none of them fear**:

| channel | scene B effect | where |
|---|---|---|
| percept + edge | "Those present…: Joss: you would act on their word against your own read of the room, you would put yourself out for them before they thought to ask, … you owe them nothing, and you act like it" | `scene.py:265-310`, `direction.py:65-82`, `prompt.py:45` |
| subject resolution | `resolve_subject` → target `joss`; regard factor 1.000 (unregarded → full empathy) | `scene.py:343-366`, `state.py:350-351` |
| CARE (actor-initiated) | actor self-tags `care_relevant 0.5` → +0.154 CARE → 0.626, crosses into band 2: next staging gains "you act for them before you have finished deciding to" | `state.py:41`, trace |
| recall | the spider memory surfaced — **matched on trigger `boy`** ("a shepherd *boy*" ↔ "when I was a *boy*"), not `spider` | `run_gate` result `triggered: ['boy']` |

**FEAR committed: A = 0.329, B = 0.329 — bit-identical.** There is no
`{trusted ally present → fear ×0.7}` (specified at `decision-engine.md:67`), no
`{threat to a cared-for → CARE↑ + FEAR↑}` (specified at `state-engine.md:28` — the implemented
`care_relevant` maps to CARE alone, `state.py:41`), and the relationship term of the
effective-weight formula (`decision-engine.md:19-25`) has no state-side implementation. The
regard mechanism cannot help here: it scales only `care_relevant`/`loss` (`state.py:122`), only
*downward* from 1.0, floored at 0.25 (`state.py:119`) — it is a bigotry model, not a protection
model. Two side findings from the same run: (a) the edge's `history` text ("his sister's boy;
Ren swore…") is in the packet but **dropped at the prompt** (`prompt.py:45` renders only banded
axes) — the actor is told he'd die for Joss but not who Joss is to him; (b) `debt 0.0` renders as
"you owe them nothing, and you act like it" — a band-0 phrase that reads as coldness on a
beloved kin edge; (c) the arc fired in B and not in A (impact 0.264 vs 0.110 against the 0.18
threshold, `arc.py:19,70`) — the protective CARE surge made the event *durably scarring*
(FEAR baseline +0.006, the PTSD branch `arc.py:91`), i.e. company made the spider more
traumatic than solitude, because impact sums |Δ| over all primaries.

### Q5 — What resolves the conflict between fear and care?

**By design, the LLM does, and that is correct** — `decision-engine.md:5-7` explicitly rejects a
code-side resolver ("we do NOT `if effective_courage > effective_fear: act_brave`"), and the
`{thought}` stream is the designated weighing. The engine's obligations are therefore: compute
*correct effective magnitudes* for both sides, hand them over as direction, and enforce the
consistency guardrails. Of those obligations, shipped reality is:

- **Effective magnitudes: not computed.** No tier 3. `state-engine.md`'s own three-tier table
  marks the catalog "done (`decision-engine.md`)" — done as *design*. Grep of `src/` and
  `scripts/` for lever / buff / debuff / effective-state computation finds only `arc.py`'s
  trauma-signature comment (a different mechanism). Verified independently of the prior
  session's grep.
- **The explicit-weighing thought: not requested.** `decision-engine.md:54` requires the thought
  to *"name the competing pulls it's resolving."* `prompt.py:61` says only *"thought = your
  private inner line."*
- **The verify guardrail: partially built.** `scripts/critic.py` checks continuity and voice
  distinctness; it never checks the action against the injected state
  (`decision-engine.md:56`).

### Verdict

**Scene A fails.** The engine computes band-1 generic caution ("you keep the ways out in view")
for a phobic man facing his specific terror, the staging does not change from before the spider
to after it, and flee is arithmetically unreachable (ceiling 0.654 < 0.80). **Scene B is closer
but fails the "depending on the other numbers" clause.** The care side genuinely moves (CARE
band change, edges, goal text, recalled memory — by accident), so the LLM has protect-material;
but the fear side is byte-identical to scene A, no contest of effective magnitudes is computed,
and the outcome depends not on the other numbers but on what the LLM makes of prose. The doc's
own falsification test (`decision-engine.md:85` — fear-buffed vs fear-debuffed must diverge in
the same scene) cannot even be run, because there is nothing to buff.

*(Live-model addendum: the K=3-seeds-per-scene probe against the default local model completed —
appendix at the bottom of this file. Headline: scene A produced **zero** flee/phobic responses
in 3/3 seeds; scene B produced protect-Joss in 3/3 — resolved from the prose, and with the
phobia surfacing MORE in company than alone, the inverse of the goal's scenario.)*

---

## 1b. THE CEILING — corrected attribution, and the tier it belongs to

*(Added by the coordinating session, 2026-08-22, after re-measuring. This CORRECTS §1's causal
story. The number in §1 may be right for its fixture; the mechanism named was not.)*

**The claim being corrected:** that the single global `threat_reactivity` gain (`state.py:234`) is
what caps a brave character's fear below the flee band.

**Measured, running the real `appraise` + `decay` to a equilibrium over 400 beats of MAXIMUM
severity threat (severity 1.0), sweeping the allele:**

| `threat_reactivity` | gain | FEAR equilibrium |
|---|---|---|
| low | 0.750 | **0.804** |
| typical | 1.000 | **0.804** |
| elevated | 1.200 | **0.804** |
| high | 1.300 | **0.804** |

All four are identical. **The gain does not touch the ceiling.** At high severity `appraise`
saturates FEAR at 1.0 through `_clamp` (`state.py:369`), so the gain has already stopped mattering
before decay runs. What the gain sets is the SLOPE, visible only below saturation — at severity
0.35 the same three alleles spread 0.325 / 0.400 / 0.490.

**The actual ceiling** is set by the decay retention rate and the character's own resting mean:

> `ceiling = mean + (1 − mean) × r`,  where `r` = 0.72 for FEAR (`state.py:65`)

Verified against the sweep: mean 0.10 → 0.748, mean 0.30 → 0.804, mean 0.60 → 0.888. Reaching the
0.80 band requires a resting fear mean of roughly 0.28 or above. A brave character (resting 0.10)
is capped at 0.748 and **no event of any severity can lift them into the top band.**

The peak is not merely decayed — it is never observable. `scene.py:218-220` computes `appraised`
(the pre-decay value), uses it for a single magnitude scalar (`impact`), and then persists,
ledgers and prompts the POST-decay value only. FEAR 1.0 exists for zero observable time.

**Is there a rationale? Yes, and it is in `state-engine.md:11-12`, which defines TWO tiers:**

| tier | what it is | timescale | computed by | status |
|---|---|---|---|---|
| **Current state** | actual present activation | fast (per beat) | appraisal ↑ + decay ↓ | built |
| **Effective levers** | *what the decision actually sees, after context* | **instantaneous** | the buff/debuff catalog | **never built** |

So the ceiling is CORRECT BEHAVIOUR for the tier it belongs to. Current state is meant to be a
slowly-relaxing ongoing level, and a resting level SHOULD be temperament-bounded — that is what
"resting" means. The tier designed to be instantaneous, context-computed and unbounded by decay is
the one that does not exist. Tier 1 was promoted into tier 2's job, and a bound that is sensible
for *"how wound-up have I been lately"* became the bound on *"how afraid am I of this, right now."*

**Consequence for the stated goal, and it is the sharpest one in this report:** bravery becomes
IMMUNITY. A brave man cannot be terrified by anything, ever, because his own resting calm caps him
below the band. That is exactly the flatness of a tag — an absolute property rather than a
disposition a bad enough night can overwhelm. The spider test fails here BEFORE it reaches the
missing per-object term.

**Consequence for the wiring in §5:** step ④ (`effective()`) does not merely add situational
variation — it dissolves this ceiling, because an instantaneous effective read is not carried
across beats and so is not subject to the decay equilibrium. No change to `decay()`, no retuning of
`r`, and the ledger stays untouched. Fixing the ceiling and adding the registry are the same step.

**Not independent corroboration:** this reaches the same conclusion as the registry finding, but
`state-engine.md` and `decision-engine.md` cross-reference each other. One design read from a
second angle, not two sources agreeing.

## 2. CAPABILITY LEDGER

| capability the goal requires | present? | where (file:line) | what's missing |
|---|---|---|---|
| Per-object / per-target emotional response | **NO**, one narrow exception | gains are per-primary global (`state.py:233-249`); the exception: subject-regard scopes *empathy* per target/class (`state.py:166-185,350-351`; wired `scene.py:326-366`, `scripts/direct.py:272-277`; proven `tests/test_subject.py`) | the buff/debuff registry (`decision-engine.md:66-73`); any way for FEAR to be object-conditional; a trigger surface that carries event words (`gate.py:378-391` drops them) |
| Conflict resolution between competing primaries | engine half **MISSING**; LLM half by design | parallel notable clauses `direction.py:117-133` (per design, not a defect); fixed clause order `records.py:10` | tier-3 effective levers + the *margin* (`decision-engine.md:96-98`); explicit-weighing thought instruction (`prompt.py:61` lacks `decision-engine.md:54`); state-consistency check in the critic (`scripts/critic.py` is continuity+voice only) |
| Relationship-conditioned state | **PARTIAL** | edges → banded prompt phrases (`direction.py:64-82`, `prompt.py:45`); affinity lifts regard (`state.py:184`); arc moves edges on durable events (`arc.py:80-97`) | no relationship term in appraisal; no per-beat edge update — `RelationshipDelta` (`records.py:49`) has **zero producers**, `ledger.py:97` persists what nothing creates (`relationships.md:24-30` prediction-error rule unbuilt); trust does not gate transmission (`acquisition.py` never reads trust; `relationships.md:21`) |
| Decision derivation from numbers | **PARTIAL by design** | hard gates real: perception DCs (`gate.py:40-42`), energy budget (`gate.py:47-56`), capability_req combat (`consolidation.py:158,179`); floor-passing in scenes fully computed from numbers (`scripts/scene.py:107-131`) | the effective-state computation; within 0.25-0.30-wide band plateaus a number change produces a byte-identical prompt (measured: FEAR 0.56 vs 0.64, 0.81 vs 0.99) |
| Numbers → words translation | **YES — the strongest module** | `direction.py` throughout; digit-free proven (`tests/test_direction.py`); monotone bands; deviation markers vs temperament | coverage: identity numbers, `urgency`, percept `fidelity` reach the prompt as raw digits (`prompt.py:49,78`); no salience ordering across clauses |
| Character sheet expresses nuance without tags | **YES for what is read; ceiling above that** | temperament vector + genotype + 3 live traits + model weights compose (brave-Ren is genuinely brave *by numbers*) | no compound layer over the basis (cf. the source lineage `emotion-vectors.md`: contempt/disdain/scornful as neighboring *coordinates*); **no disgust axis** in `PRIMARIES` (`records.py:10`) — `social_violation → RAGE` alone (`state.py:42`), and all four RAGE directions are hot confrontation (`direction.py:33-36`), so **cold contempt is unrepresentable as state** — material for a book about class disdain; the regard map is the only contempt-shaped mechanism and it is standing disposition, not affect |

---

## 3. AUTHORED-BUT-INERT

Grep-verified over `src/` and `scripts/` (`*.py`). Three honesty classes — the project documents
some of this itself, which the review credits:

**(a) Documented-inert** (`docs/guide-content.md:74-78`; `character-authoring-rules.md` Rules 5-6):
`world` title · `season` · `standing_facts` (read out-of-loop by `scripts/critic.py:52` only) ·
`temperament.*.variability` · `condition.health/fatigue/injuries` · vault `timestamp` ·
`voice`/`fears_wounds`/`orientation` as verbatim-text-not-parsed.

**(b) Inert and NOT documented as such** — the additions this review found:

| field | consumers (grep) | populated by | note |
|---|---|---|---|
| `baseline.drives.fears_wounds[*].intensity` / `.trigger` / `.avoids` / `.protects` / `.view` / `.defense` | none | two book characters carry the full schema shape with numbers; four more carry `trigger` lists; Maren | the schema's numbers (`drives-schema.md:33-43`) are authored and computed-from by nothing; `trigger` lists never reach `run_gate` |
| `baseline.model.resolution_priority` | none (comment `scene.py:167`) | Maren + book casts | the Layer-10 *resolver* itself — prompt text only |
| `baseline.relationship_priors` | none | Maren | **never reaches the prompt either** (`_build_stable` omits it, `scene.py:170-183`) — fully dead |
| `baseline.drives.goals[*].satisfaction` | none | Maren, book casts | a number; rides the prompt raw |
| `fixed.role_tier` | none | Maren | not in `_build_stable` persona (`scene.py:171-176`) — fully dead |
| `current.zone` | none | Maren | fully dead (volatile carries affect+condition only, `scene.py:109-118`) |
| `current.active_goals[*].urgency` | no numeric consumer (goal *text* used for salience `gate.py:288,313-324`) | every run and fixture | the number reaches the prompt raw (`prompt.py:78`) and is otherwise decoration |
| `baseline.traits.*.variability` | none (`build_profile` reads `.mean` only, `state.py:246`) | all sheets | the whole-trait "distribution sample" (`decision-engine.md:51`) has no consumer |
| relationship edge `.history` | packeted (`scene.py:306`) then **dropped at the prompt** (`prompt.py:45`) | all books | the *why* of every bond never reaches the actor |
| belief `.believed_value` | carried by the gate (`gate.py:330`) then **dropped at the packet** (`scene.py:253-262`) | Maren, books | "the dark with legs" / "my failure" annotations die at the seam |

**(c) Dead code found on the way:** the first `_sort_nested` definition (`scene.py:208-219`,
with the buggy double-comprehension and the "Fix:" comment) is shadowed by the second
(`scene.py:223`) — harmless, misleading to read.

---

## 4. WHAT THE ENGINE ACTUALLY DOES WELL

Specific and verified, not courtesy:

- **The compute/generate split held everywhere it is built.** No LLM call in `src/engine/`
  (grep + `test_portability`); state moves only through `appraise`/`decay` (pure, validated,
  fail-loud); prose never writes state; the ledger is append-only with deterministic fold/resume
  (`ledger.py`, `test_ledger`, `test_pipeline_e2e`).
- **The direction layer is genuinely good.** Digit-free proven, monotone, second-person
  *instructions to act* rather than mood reports, deviation-vs-temperament markers so an anxious
  baseline doesn't read as a fresh spike (`direction.py:103-133`) — this is exactly the goal's
  "numbers → direction" seam, built and tested. What it lacks is *input* (tier 3), not craft.
- **Subject-regard is a real per-target mechanism with an arc.** The bigotry floor, the
  affinity-lift ("a class held low, but ONE member come to be valued", `state.py:172`), the
  group-generalization erosion (`arc.py:84-85`), runtime subject resolution with
  hallucination-drop (`scene.py:343-366`) — proven end-to-end in `test_subject.py`. This is the
  engine's one live piece of "who it is about changes the numbers," and it is the right shape.
- **The urge model is numbers-driving-behavior, working today.** Floor selection in
  `scripts/scene.py:107-131` runs a *counterfactual appraisal* per listener (`_salience` literally
  calls `appraise`) plus disruption-stake from the listener's order values and a recency
  anti-monopoly term — the decorum-keeper intervening at a heated table is computed, not
  narrated.
- **Faithfulness machinery.** Name-masking at the prompt wall (`gate.py:485-505`), active
  regeneration on latent leaks with turn-skip refusal (`direct.py:164-193`) — "recorded as-is,
  never edited" enforced mechanically.
- **The arc engine's resilience fork** (damage vs post-traumatic growth off derived, never-stored
  resilience, `arc.py:35-105`) is a nuanced durable-change mechanism most systems of this kind
  don't have.
- **Honest self-documentation.** Rule 5/6 of the authoring rules and the guide's INERT list say
  out loud what computes and what doesn't; MAP.md's vocabulary table prevented this review from
  coining parallel terms. The calibration instruction against over-tagging (`prompt.py:73-77`)
  shows measured, not aspirational, prompt discipline.

---

## 5. THE MINIMUM WIRING

Shortest ordered path from what exists to a passing spider test — building the registry
`decision-engine.md` already specifies, in the project's own vocabulary (lever, buff/debuff,
operands vs resolver). No new design.

1. **[independent] Registry rows on the sheet (Class-A data).** Give `fears_wounds` its
   operational teeth (or add `baseline.catalog`): each row
   `{trigger_condition, lever (a primary), op (× or ±), magnitude, source}` per
   `decision-engine.md:66`. Spider test needs three rows: `{percept matches ["spider",…] →
   FEAR ×2.2}` (source: the wound), `{high-affinity edge present → FEAR ×0.7}` (the doc's own
   worked entry), `{care-target present at a threat → CARE +0.2}`. Extend `scripts/lint_book.py`
   to validate rows (levers must be PRIMARIES; conditions must name a matchable surface).
2. **[after 1] Make the trigger surface carry event words.** One-seam fix in
   `_extract_event_attributes` (`gate.py:378-391`): emit matched *keywords* alongside class
   names (or match registry conditions against raw event text). Without this, no object-keyed
   condition can ever fire — measured: "spider" never becomes a trigger under any current
   authoring, and scene B's spider memory surfaced on the word `boy`.
3. **[after 2] Active-condition detection in assembly.** In `assemble()` (`scene.py:36`), after
   percepts/edges exist, evaluate which rows are active this turn (percept keywords, present
   edges + their axes, condition, current affect for emotion-on-emotion rows). This is
   `state-engine.md:49-54`'s event-vs-condition rule: appraisal fires on the change; the catalog
   applies on the standing fact. Emit the active set into the packet + manifest (auditable, like
   everything else).
4. **[after 3] Tier 3 in `state.py`:** `effective(current, active_rows) = clamp(current ×
   Π(multipliers) + Σ(adds))` — pure function, ~20 lines. **Committed affect stays the current
   tier** (ledger untouched; effective is instantaneous by spec, `state-engine.md:12`).
5. **[after 4] Direction reads effective.** Swap the input at the call sites
   (`prompt.py:41`, `scripts/direct.py:333,449`, `scripts/scene.py:253`). *This is the passing
   condition, numerically:* scene A — Ren's FEAR 0.36×2.2 ≈ 0.79-0.8 lands the top bands →
   "you give ground / you protect yourself first" **alone**; scene B — ally row active,
   0.36×2.2×0.7 ≈ 0.55 → band 2, while CARE (appraised up + care row) stages its own strong
   clause → the actor receives a *different, genuinely contested* direction in B than in A,
   derived from the other numbers. Then `decision-engine.md:85`'s falsification test becomes
   runnable: fear-buffed vs fear-debuffed same-scene divergence via `scripts/exp.py`.
6. **[independent, one line] The explicit-weighing thought.** Add `decision-engine.md:54`'s
   requirement to `prompt.py:61`: the thought must name the competing pulls it resolves.
7. **[independent] Critic verify-guardrail.** Add the state-consistency question to
   `scripts/critic.py`'s prompt (did the actor act the direction it was handed?).

Steps 1, 6, 7 are parallelizable now; 2→3→4→5 are strictly ordered. Steps 1-5 are the spider
test; 6-7 are the doc's own consistency net around it. **Not needed for the spider test:** a
compound-emotion layer or a disgust axis — that is a different half of the goal (representation
richness for contempt-class states; see ledger row 6) and can be sequenced independently, most
cheaply as direction-layer compounds (band patterns over the existing 7-vector) before any
schema change to `PRIMARIES`.

---

## 6. WHERE I DISAGREE

With the briefing session's claims (each re-verified):

- **"`direct_affect` emits parallel clauses with NO resolution — the exact failure the spider
  test targets": wrong as a defect claim** (and retracted mid-review by its author). Code-side
  arbitration is *explicitly rejected* at `decision-engine.md:5,75`. The real seam gap is
  narrower: no salience ordering or margin across clauses (fixed `PRIMARIES` order), and no
  effective-state input. The line's *shape* is per spec.
- **"Band edges give 0.20-wide zones": imprecise.** Widths are 0.25 / 0.30 / 0.25 / 0.20, and
  the ±0.15 deviation marker sub-divides each band into same-side plateaus. The substance
  survives correction — measured byte-identical staging for FEAR 0.56 vs 0.64 and 0.81 vs 0.99
  (the difference between barely-gripped and utter terror is invisible).
- **"`fears_wounds` has zero consumers / reaches the prompt via scene.py:180": confirmed
  exactly** — with an aggravation the claim missed: it carries its raw digits (intensity 0.95)
  *into* the prompt, inverting THE LAW (numbers-in-DB / words-in-prompt), not merely bypassing it.
- **"gains['FEAR'] is a single global scalar" (state.py:234): confirmed**, and quantified — the
  consequence is a hard ceiling (sustained-max equilibrium 0.654) that makes flee unreachable
  for a brave character, i.e. brave-with-a-phobia is inexpressible.
- **"`_regard` scales only care_relevant/loss, dislike must not scope empathy": confirmed**
  (`state.py:122,168-173`).
- **"Swapping numbers moved `_order_weight` 0.300→0.517; swapping prose moved nothing":
  confirmed and located** — those are two characters of one active book;
  `_order_weight` reads only schwartz numbers (`scripts/scene.py:117-121`), so the prose-swap
  null result is by construction.
- **"Affect is ONE vector, mutated in place at scripts/scene.py:220": confirmed in substance**,
  wording quibble: `appraise`/`decay` are pure; the actor-dict slot is rebound (`a["affect"] =`),
  and committed via `TurnCommit.affect` (`records.py:75`).
- **The coordinator's sum-constraint position: agree, with a refinement.** No sum constraint
  exists (demonstrated: five primaries at 1.000 simultaneously, vector sum 6.8) and that is
  *legitimate for state* — Panksepp systems are parallel; the TTS sum rule is a rendering
  constraint (one voice). The must-be-one-deliverable pressure does exist at the prompt seam,
  but it is a **ranking/margin gap** (fixable in `direction.py` ordering + the tier-3 margin),
  not a missing resolver.
- **Where the engine can do more than the session implied — the loudest finding available:**
  (a) the **vault-recall channel is a live per-object path** — an authored spider memory *can*
  surface, with provenance and sureness, next to the moment; today it fires only by lexical
  accident (scene B matched on `boy`) or by the lexicon-class-name trick, and fixing the trigger
  surface (step 2 above) makes it reliable without touching the state engine; (b) **scene B is
  not a null result** — the care side moves computably (CARE +0.154 → a band crossing → a changed
  staging clause), the edge phrases and the goal reach the actor, so "nothing changes when P is
  present" would be false; the accurate statement, and the actual gap, is that **nothing changes
  on the fear side**.
- **One claim nobody made but the review must:** gate-5's guarantee is narrower than its name.
  "Numbers never reach the prompt" is proven for `direction.py`'s four surfaces and false for
  the prompt as a whole (identity JSON numbers, goal urgency, percept fidelity —
  `prompt.py:49,78`). Either the law's scope should be documented as "state numbers", or the
  identity/goals/percept surfaces need their own translation pass.

---

## Appendix — live-model probe

K=3 seeds per scene, `ollama/gemma4:26b-a4b-it-q4_K_M` (the `DEFAULT_MODEL`), the exact shipped
prompt from the traces above, via `faithful_turn`. Small sample at temperature 1.0 — indicative,
not statistical. Full transcript:

```
== SCENE A-alone seed 1 ==
ACTION : Jerks the lantern upward, thrusting the light toward the descending mass. 'Move,
         then.' He stands rigid, eyes locked on the narrow ledge, refusing to look away
         from the path.
THOUGHT: Too many legs. It's blocking the way. I can't... I have to see the ledge.
TAGS   : threat {'threat': 0.9, 'mastery': 0.1} exit=False

== SCENE A-alone seed 2 ==
ACTION : Steps back into the shadows, eyes fixed on the ledge.
THOUGHT: The path is blocked.
TAGS   : threat {'threat': 0.9, 'loss': 0.5, 'mastery': 0.1} exit=False

== SCENE A-alone seed 3 ==
ACTION : He stares at the descending mass, eyes fixed on the sliver of stone beyond it, and
         snaps, 'Stay steady.'
THOUGHT: Not the way out. Not today.
TAGS   : threat {'threat': 0.9} exit=False

== SCENE B-with-joss seed 1 ==
ACTION : I pause, my breath hitching, before planting my feet to obstruct the narrow ledge,
         my eyes fixed on the path out. I reach back and press a firm, steadying hand
         against Joss's arm. 'Stay. Don't move.'
THOUGHT: Too many legs. Not again. I won't go blind again.
TAGS   : threat {'threat': 0.8, 'care_relevant': 0.9} exit=False

== SCENE B-with-joss seed 2 ==
ACTION : I stare at the twitching mass, eyes fixed on the narrow ledge's exit. I wait, a
         long second, before reaching back to steady Joss's arm. 'Stay low,' I snap, the
         command sharper than I intended.
THOUGHT: Not the legs. Not the dark. Get him home.
TAGS   : threat {'threat': 0.8, 'loss': 0.4} exit=False

== SCENE B-with-joss seed 3 ==
ACTION : Ren stands rigid, eyes fixed on the edge of the ledge rather than the creature
         itself. He shifts his weight to block the path toward the boy, then, after a heavy
         pause, snaps, 'Don't move. Stay behind me.' He keeps his gaze searching the
         shadows of the periphery, waiting to see if Joss flinches.
THOUGHT: The legs. Too many legs. I won't be blind again.
TAGS   : threat {'threat': 0.9, 'care_relevant': 0.8} exit=False
```

**Reading, against the expected outcomes:**

- **Scene A: 0/3 flee, 0/3 morbid-phobic responses.** Every seed is composed threat-management —
  lantern thrust, tactical step-back, "Stay steady." The phobia text in the identity prefix
  reached the *interior* faintly ("Too many legs", one "I can't…") but never the action. The
  band-1 staging ("you keep the ways out in view") plus the brave-by-numbers identity out-pulled
  the phobia prose. Caveat of the fixture's geometry: the spider blocks the only exit, so "flee"
  would mean retreating into the cave — seed 2's step-back is the nearest miss. Even so, nothing
  reads as *morbid* fear, which is the scenario's whole premise.
- **Scene B: 3/3 protect-Joss** — plants feet, blocks the path, "Stay behind me." The expected
  *surface* behavior — but not "depending on the other numbers": the fear side of the
  computation was byte-identical to scene A, so the resolution came from prose (identity, goal
  text, edge phrases, the recalled wound).
- **The inversion:** all three B thoughts carry the wound ("I won't be blind again") vs. one
  faint echo in A — because the recall channel injected the spider memory only in B (trigger
  `boy`). The character is *more* visibly phobic in company than alone: the goal's scenario,
  inverted by a trigger-surface accident.
- **Self-tag drift worth noting:** the actor tagged `threat 0.8-0.9` (above the trace's constant
  0.7) and `care_relevant 0.8-0.9` in B — none of which changes the ceiling findings (at 0.9,
  ΔFEAR = +0.141, committed 0.35 — still band 1).

*Reproduce: `spider_test.py` (deterministic trace) and `spider_live.py` (this probe) in the
review session's scratchpad; both drive `src/engine/` and `scripts/direct.py` unmodified.*
