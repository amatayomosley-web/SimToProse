# Guide — authoring a character's emotional makeup

*(WORKFLOW. `emotion-basis.md` owns the theory — which emotions are irreducible and why.

THE REST OF THE EMOTION LAYER, which this guide referenced nowhere until 2026-09-03 and which the
character blueprint therefore could not reach through it: `emotion-scales.md` is **normative for
what a value MEANS** (authored 2026-08-31, and before it the rendering bands in `direction.py` were
the de facto specification — a display constant standing in for a definition); `emotion-vocabulary.md`
defines every nameable state and locates it on the primitives it sits on; `emotion-list.md` stages
those names by degree; and `docs/emotion-names/` splits each primitive by TARGET — outward,
reflexive, unbound — because a name that ignores who the feeling is aimed at names the wrong state.
`emotion-names/_ROUTING.md` records which names a rule moved off the table they were first swept
onto. This guide owns the ORDER you author in; those own the words and the numbers.

`emotion-recipes.md` is the generated recipe sheet. `guide-content.md` owns the per-field
live-vs-inert table. This owns the ORDER: what you do, in what sequence, and what proves each step
landed.)*

## The layers, and their lifetimes

Author them in this order, because each one is the input to the next. The lifetimes are the whole
reason there are eight rows below rather than one (the heading said
"five" until 2026-09-06; the table has listed 1-4, 4b, 5, 5b and 6 for longer than that) — a thing that never changes and a thing that changes per
turn are not the same field.

| # | layer | what it answers | changes |
|---|---|---|---|
| 1 | **genotype** (`fixed.genotype`) | the same thing happened to both of us — why does it land harder on you, and why does it stay with you longer? One `{hit, hold}` cell per path | **never** — `arc.py` writes temperament, edges and regard, and never this |
| 2 | **temperament** (`baseline.temperament`) | where do you sit when nothing is happening? | **AUTHORED as a rest word per path, beside the voice (2026-09-10)** — the mean is seeded from it once and then drifts slowly, per durable event (arc) |
| 3 | **the worth menu** (`baseline.model`) | why does this event matter to you *at all*? | slowly |
| 4 | **the wounds** (`baseline.wounds`) | why is *this* fear different from your ordinary fear? | **minted, not authored** — from a formative profile at creation, or by the story mid-run; moves per trial (walk into the cue and it deepens or eases) and erodes toward its floor between scenes |
| 4b | **the catalog** (`baseline.catalog`) | why does something ELSE about you shift under a standing condition — not a fear, a dampener (a forge-trained smith at half fright around sparks)? | never, but fires conditionally — a wound cannot live here any more; a dampener can, because a dampener is not an investment |
| 5 | **the edges** (`current.relationships`) | what do you make of *this person*? | every beat they act, and over time |
| 5b | **the second order** (`edge.their_view`) | what do you think *they* make of *you*? | when they act toward you — never authored, it accretes |
| 6 | **affect** (`current.affect`) | what are you feeling right now? | every beat |

One more thing is not authored per character at all: the **compound vocabulary**
(`src/engine/compounds.py`) is engine-owned. **Its NAMING half is retired as of 2026-09-06** —
`recognise` scored by cosine and named the same compound at every magnitude, so it was unwired from
`direction.py`; naming moves to the path layer (`emotion-dynamics.md`). The recipes still stand as
a shared vocabulary, and the principle below is why they are engine-owned: "Contempt" means the same shape for everyone, or the
word carries no information. What varies per person is which catalog rows FIRE, never what a name
means.

---

## 1. Genotype — draw it, or author it backward

**One `{hit, hold}` cell per PATH, drawn or authored independently** (the 2026-09-10 rebuild —
`src/engine/heritable.py`, its module docstring is the design). `hit` is how hard a reading on that
path lands: `low | typical | elevated | high`. `hold` is how long an excursion on that path stays
with them before it lets go: `brief | typical | long | lasting` — a multiplier on the path's
half-life, never an absolute rate, which is what lets the per-character and global systems be
balanced separately. Where the path sits when nothing is happening is a separate field now,
authored beside the voice — section 2, below.

**Background and supporting cast: draw.**

```bash
python scripts/make_genotype.py --seed <anything> --count 5
```

The draw prints both blocks from one seed: `genotype` (`hit`/`hold` per path, `draw()`) and
`temperament` (the rest word per path, `draw_rest()`, section 2) — the seed IS the person, same
seed, same character, forever, and recording it reproduces them. `--rows` emits the `hit` cell of
each path as `levers` buff rows — the only one of the two cells that IS structurally a lever, a
permanent unconditional multiplier on a path's gain; hold is a rate and does not become a row.
`--check` prints the measured combination count per path and the drawn-cast distinctness table
instead of drawing anyone.

**Principals: author backward.** Start from the character the story needs, choose the `hit` /
`hold` cells that produce them, then validate forward — the world must plausibly make such a
person. Drawing a principal is starting from the dice and hoping for a protagonist.

**Why this layer exists at all:** without it two soldiers in the same battle feel the same thing.
And because nothing can write the genotype afterwards, two people who then live *identical lives*
still end up different. That is the entire point; if you skip it, your cast converges.

**The engine reads only the first word of a cell**, so annotate as `"high (anxious-leaning bond
style)"` — word first, note after. Anything else silently reads as that cell's default
(`heritable.word`, the one parse every module calls, `src/engine/heritable.py:111-118`) — the one
place in the schema where a typo costs you a character trait and says nothing. A NUMBER in either
cell is honoured exactly as authored instead of drawn from a preset; the preset numbers behind each
word (`GAIN`, `src/engine/heritable.py:84-89`; `PERSIST`, `src/engine/heritable.py:95-100`) are
the conservative START the owner tunes in real runs (2026-09-10) — write the word, and do not
treat the number behind it as final.

**Two shapes are refused, not translated.** `threat_reactivity`, `approach_drive`,
`affiliation_attachment`, `anger_proneness`, `effortful_control`, `sensitivity` no longer exist as a
genotype shape. A sheet that still carries any of them fails to run outright — `GENOTYPE_OLD_AXES`
(`heritable.OLD_AXES`, `src/engine/heritable.py:104-105`) — rather than being silently
reinterpreted. Nor does a `rest` key belong inside a genotype cell any more — that fails outright
too, `GENOTYPE_REST_MOVED` (`src/engine/heritable.py:151-157`), naming the path and pointing at
`baseline.temperament`, section 2. A book written against either old shape is migrated by hand,
once, with its author's eyes on every line; see `characters/maren-healer.json` and
`characters/ren-traveler.json` for two worked rewrites.

## 2. Temperament — where they rest (authored, as words)

**Write the rest word per path.** For a few hours on the morning of 2026-09-10 this section said
the opposite — `baseline.temperament` fell straight out of the genotype's `rest` cells and you
wrote nothing here. That did not survive the day: later the same 2026-09-10 the owner moved it back,
*"Have temperament be a character design question, along with their voice and other personality
options."* `baseline.temperament[path] = {rest, mean}`: `rest` is yours, a word naming a rung
(`quiet | low | raised | high`, `heritable.REST_WORDS`, `src/engine/heritable.py:63`), capped per
path (`heritable.REST_CAP`, `src/engine/heritable.py:72-81`) at the last rung that reads as a
disposition rather than an episode — the cap only actually stops a WORD on two paths (STIRRING at
`raised`, LEVITY at `raised`, DISTASTE at `low`); the other six paths' caps matter only for an authored NUMBER. A rest
above the cap, word or number, is still HONOURED — the pre-run check WARNS, naming the rung, so a
character resting at genuine loathing is a decision with a receipt, never a typo
(`scripts/lint_book.py:379-383`). The engine reads only the first word, lowercased, same as every
other word field (`heritable.word`, `src/engine/heritable.py:111-118`) — `"raised (watchful by
habit)"` reads as `raised`. A NUMBER in `rest` is the resting mean directly, clamped to `[0, 1]`
(`heritable.rest_mean`, `src/engine/heritable.py:235-240`), bypassing the rung system except for
the cap warning.

`mean` is not yours to write. The first time a sheet reaches the engine, every path's rest word is
read ONCE into a mean — the rung's band midpoint off the live ladder — and STORED
(`heritable.rest_mean`, `src/engine/heritable.py:235-240`; `heritable.ensure_temperament`,
`src/engine/heritable.py:276-298`, called at `src/engine/scene.py:96` and
`src/engine/state.py:301`). It is stored, not recomputed on every read, because the arc engine
writes durable diffs into it over the life of a run and `arc.erode` relaxes a character back toward
the value stamped here — a row that already carries a mean keeps it.

**The mean is still the personality's resting face, not its starting mood.** An anxious character
is a high WARINESS *rest*, not a high starting affect — start affect (layer 6) at or near the
authored rest's mean unless the book opens mid-crisis.

**If a sheet already carries a mean that disagrees with its rest word** by a whole rung,
`lint_book.py` WARNS, naming both — this is how an old primitive-scale sheet, or a rest word moved
without its mean, gets caught (`scripts/lint_book.py:387-393`). Delete the mean to re-seed it from
the current rest word, or move the rest word to match.

**The actor sees it.** A rest word is rendered under `disposition`, as a sentence beside the six
HEXACO trait sentences — *"wariness at rest"*, and so on — because where someone sits on an
ordinary day is self-knowledge, the same as their traits and their voice
(`identity_view._REST_PHRASES`, `src/engine/identity_view.py:115-138`, rendered at
`src/engine/identity_view.py:303-317`). `quiet` and `low` render no sentence on purpose. Only the
WORD travels to the actor, never the seeded mean (`scene._rest_words`,
`src/engine/scene.py:271-280`).

The mean also sets the ceiling. Under sustained maximum pressure a path settles at
`mean + (1 − mean) × r`, so a character whose WARINESS rests at `quiet` tops out well short of one
whose WARINESS rests at `high`, through the ordinary path law. That is correct for a resting level,
and it is why layer 4 exists: without a catalog, calm becomes an *immunity* rather than a
disposition.

## 3. The worth menu — why it lands

`schwartz` / `moral_foundations` / `needs` weights decide *relevance*: the same event hits harder on
the character whose values it touches. Author only the weights you mean; **a missing key reads
neutral 0.5, not zero.** Silence is average, not absence.

## 4. The wounds — why THIS fear differs from your ordinary fear

**GATE THREE, 2026-09-11.** This is how "brave, but terrified of spiders" stops being a
contradiction — but it is no longer arithmetic you write. A wound is engine state at
`baseline.wounds`, minted rather than authored: from a formative profile pick at character
creation, or by the story itself when a durable beat lands hard enough on a path bound to a
concept. Full authoring workflow, the registry of 49 concepts, both worked fixtures, and the
pre-run check that refuses a hand-written one: `docs/authoring/BLUEPRINT-character.md` Part Five.
Nothing below is yours to write; it is here so you can read what the mechanism actually does.

Ren's spider scar reads, once minted:

```json
{"id": "predator@WARINESS", "concept": "predator", "path": "WARINESS", "intensity": 0.95,
 "source": "profile:fixture-spider", "trigger": ["spider", "web", "something moving in the dark above"]}
```

It is a MULTIPLIER, not a paragraph: a reading about `concept:predator` on WARINESS lands harder by
the wound's own intensity — the character's investment in that concept, through the same registry
that scales a bond. A person held at 0.8 and a concept held at 0.8 hit identically
(`src/engine/connection.py:37-51`, and the code itself, `for_about`, `src/engine/connection.py:164-181`).
The same investment stretches the half-life — a full wound doubles how long the excursion lasts
(`_HOLD_K = 1.0` at `src/engine/connection.py:108`; `half_life_scale`,
`src/engine/connection.py:193-195`) — and while the concept is in the room (this beat names it) it
barely fades at all, `PRESENCE_HOLD = 3.0` (`src/engine/connection.py:118`). None of this is sized
by hand, and none of it is a `baseline.catalog` row any more: Ren's old catalog row multiplying
FEAR x3.4 on the words `spider`/`web` is gone from the fixture.

## 4b. The catalog — the situational half for everything that is not a wound

The catalog still exists, for everything a wound is not: a standing dampener from the formative
library (a forge-trained smith at half fright around sparks), a passion, a conditioning, or any
other multiplier that is not an investment. A dampener cannot live in `baseline.wounds` — a wound's
intensity only ever amplifies (`connection.for_about` floors at zero, never goes negative), and a
dampener's whole job is to shrink a reading, so the two stay on separate tiers on purpose.

```json
"catalog": { "rows": [
  { "when": {"percept": ["forge", "sparks"]},
    "lever": "WARINESS", "op": "x", "magnitude": 0.5,
    "source": "years at the forge; the sparks stopped meaning danger" },
  { "when": {"present_edge": {"affinity": 0.70}},
    "lever": "WARINESS", "op": "x", "magnitude": 0.62,
    "source": "someone at his back he means to bring out" }
]}
```

Four condition kinds, and they are the whole vocabulary:

| `when` | fires on |
|---|---|
| `percept: [words]` | any of those words in the event text |
| `present_edge: {axis: threshold, id?}` | someone PRESENT whose edge clears the threshold |
| `present_edge: {axis_at_most: threshold}` | someone present whose edge sits BELOW it — **this is how an enemy is expressed** |
| `target_edge: {...}` | the same clauses, but against the party the EVENT IS ABOUT rather than merely present |
| `affect_at_least: {PRIMITIVE: v}` | emotion modulating emotion |
| `condition_at_most: {energy: v}` | state — exhaustion, load |

Clauses AND together. A row with no `when` is always active, which is how a standing trait is said
as a lever.

**Three rules that are not style:**

- **Appraisal fires on the CHANGE; the catalog applies on the STANDING FACT.** A spider *appearing*
  raises fear through `appraise()`. A spider *being present* multiplies it through a row. Both.
- **A wound no longer needs an operational twin here.** Before gate three an unmatched
  `fears_wounds` trigger list was prose no row computed. That is retired along with the field
  it described — a wound multiplies its own receipt automatically, through `connection.for_about`
  (4, above), not through anything you write in the catalog. The one thing the catalog can still do
  with a wound is legacy wiring, not something to reach for: a row carrying `"wound": "<id>"` is
  scaled by what remains of that SAME wound relative to when the row was authored
  (`src/engine/levers.py:72-150`, `scale_to_wounds`). Neither fixture in this repo uses it — Ren's
  spider wound multiplies through the receipt alone, with no row naming it at all.
- **Presence and aboutness are different triggers.** *"The man he hates is in the room"* is
  `present_edge`; *"this is about the man he hates"* is `target_edge`. Author both: presence
  suppresses (he will not joke while that man is there), aboutness amplifies (his rage is for
  *him*). A row that conflates them fires on the wrong scenes.
- **Antagonism goes in the catalog, never in the appraisal maths.** `state.py:184` lifts regard by
  affinity and never lowers it — *"affinity lifts, never lowers"* — and `_REGARD_SCALED_DIMS`
  covers only `care_relevant` and `loss`. That is deliberate: **dislike must not scope empathy
  down.** You can wince for a man you hate. So hatred is authored as RAGE/DISGUST *comportment*
  rising, not as CARE falling — which also keeps it a trait of this character rather than a rule
  about everyone.
- **Calibrate against the bands.** The direction layer has edges at 0.25 / 0.55 / 0.80. A row that
  moves a primitive without crossing one is invisible to the actor. Check by rendering, not by
  reading the number.

## 5. The edges — what you author is a STARTING READ, not a fact

`current.relationships` is per-perceiver: **your** edge to them, in *your* sheet. They hold their own,
and the two are allowed to disagree — that is where a manipulator lives.

```json
"relationships": { "joss_apprentice": { "trust": 0.80, "affinity": 0.65,
                                        "respect": 0.50, "debt": 0.0,
                                        "known_as": "the apprentice" } }
```

Four axes, and they move independently — you can love someone you do not trust:

| axis | the question | gates |
|---|---|---|
| **trust** | do I rely on their word? | whether what they tell me becomes a belief or a rumour |
| **affinity** | do I like them, feel close? | whether I help or sacrifice |
| **respect** | do I rate their judgement? | whether I defer or override |
| **debt** | who owes whom? | whether I comply, or call it in |

**Author sparsely and let the run move them.** The number you write is where they START. From the
first beat `bonds.observe` moves it, and the rule is a delta against what you wrote:

- **What you author IS their expectation.** Set trust at 0.85 and a betrayal is catastrophic; set it
  at 0.20 and the same act barely registers. This is the highest-leverage number on the sheet, and
  it is the one most often left at a lazy 0.5.
- **Trust is slow up, fast down** — and a severe enough betrayal is a *cliff*, not a slope, for a
  character who weights loyalty. Two people can watch the same act and only one of them falls off it.
- **A key that is not a `world.people` id yields NO edge, silently** — the trap that made a
  two-character scene come out byte-identical to the solo one.
- **`default_trust` in `baseline.relationship_priors` is where a STRANGER's edge rests** — an edge
  the sheet did not author. An authored edge rests where you wrote it (seeded as `rest_declared` rows
  at run creation; lowered only by a cliff), so a devoted friendship does not decay into a stranger's
  over a winter. Unreinforced edges relax toward their rest when a scene declares a gap, affinity
  fading fastest. `relationship_priors.update` sets how readily this person lets someone in
  (`grant_threshold`) or lets them go (`withdraw_speed`) — bond-arithmetic.md s6.

### Verify

```bash
python tests/test_bonds.py
```

Then run a scene and read the `BOND` lines — they say who re-read whom and by how much. If a beat
you expected to land shows no BOND line, the actor's tags carried no social dimension: `type` must
be a CATALOG key or `validate_tags` zeroes the dimensions and nothing moves.

## 6. Affect — turn zero only

Start at or near the temperament means. Everything after turn zero is computed.

---

## Verify — in this order, every one deterministic

```bash
python scripts/lint_book.py --vault "$SWE_BOOKS/<book>"     # empty vaults, missing edges,
                                                            # a hand-written fears_wounds block,
                                                            # a malformed baseline.wounds entry
python tests/test_genotype.py                               # the draw is reproducible
python tests/test_compounds.py                              # the vocabulary is separable
```

Then render what the actor will actually receive — the only check that catches a number which
changed and a direction which did not:

```bash
python -c "import sys; sys.path.insert(0,'.'); import json; from src.engine.scene import assemble; from scripts.direct import rung_summary; ch=json.load(open('characters/<x>.json')); w=json.load(open('world/<y>.json')); pk=assemble(ch,w,{'event':{'text':'<the event>','kind':'threat'},'recent':[],'location':'<loc>'},dict(ch['current']['affect']),ch['current']['condition']); st=pk['volatile']['state']; print(st['affect']); print(st['effective']); print([r['source'] for r in pk['volatile']['levers']]); print(rung_summary(st['effective']))"
```

If `effective` equals `affect`, no row fired — your `when` never matched. If they differ but the
direction line is unchanged, the change stayed inside a band and the actor cannot see it.

---

## The traps, all of them measured

- **A relationship key that is not a `world.people` id produces NO edge, silently.** Every
  `present_edge` row then fails to fire and a scene reads identically with and without the other
  person. Cost when it happened: a spider-test scene B that came out byte-identical to scene A.
- **`_note` and prose annotations do not reach the engine.** They are for the reader. If a number
  matters, it goes in a field the engine parses.
- **Beliefs need `- (confidence, provenance) claim`.** A plain prose bullet parses to zero
  beliefs — 52 of 88 authored beliefs were being discarded before `vault.py` was made to fail loud.
- **`[[links]]` in the provenance parenthetical are dropped.** Links are extracted from the CLAIM
  only. Put them in the claim.
- **A wrapped belief truncates at the line break.** One line per belief.
- **`timestamp` is in the vault schema and is not parsed.** The engine cannot tell a wound from last
  week from one thirty years old. Do not rely on it.
- **LUST is reachable by no appraisal dimension.** It has a temperament mean, four direction
  phrases, and nothing that can move it. Authoring it does nothing today.
- **`scripts/direct.py` moves edges ONLY when you say who acted.** Prefix the circumstance with
  `by:<entity_id>` — *`by:joss he takes the purse off the table`*. Without it nothing moves, because
  the actor is authored and never inferred (a classifier guessing which entity "he" is fails
  silently and poisons an edge). The chair also writes no `RelationshipDelta` rows; that is
  scene-only.
- **A witness who could not have registered the act forms NO edge move.** A SUBTLE act (severity
  under 0.55) needs `perception` ≥ 0.60, and pinning any act on a STRANGER needs `insight` ≥ 0.55 —
  an existing edge counts as acquaintance and skips that check. So an unobservant character can
  miss the slight everyone else caught, which is the point, but it also means a low-perception
  cast will look inert if all your acts are subtle.

## What is still hand-work

The genotype draws for background people. The rest words are HAND-WORK for principals and
supporting characters, the same as their voice — drawn only for background people who get no
author (2026-09-10; temperament is no longer computed from the genotype). The worth menu, the
catalog and the vault are authored, and the full creation pass the design calls for — position →
formative environment → baseline → individuation — is unbuilt. Author forward from the world where
you can; the world is supposed to be the input that produces the baseline, not decoration around it.

**The wounds are not.** Since gate three (2026-09-11) `baseline.wounds` is minted — from a
formative profile pick at creation, or by the story mid-run (`docs/authoring/BLUEPRINT-character.md`
Part Five) — never hand-written. If your story needs a specific scar, the hand-work is picking the
formative profile that carries it, not writing the wound itself.
