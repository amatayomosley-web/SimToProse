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

## The five layers, and their lifetimes

Author them in this order, because each one is the input to the next. The lifetimes are the whole
reason there are five rather than one — a thing that never changes and a thing that changes per
turn are not the same field.

| # | layer | what it answers | changes |
|---|---|---|---|
| 1 | **genotype** (`fixed.genotype`) | the same thing happened to both of us — why did it hit you harder? | **never** — `arc.py` writes temperament, edges and regard, and never this |
| 2 | **temperament** (`baseline.temperament`) | where do you sit when nothing is happening? | slowly, per durable event (arc) |
| 3 | **the worth menu** (`baseline.model`) | why does this event matter to you *at all*? | slowly |
| 4 | **the catalog** (`baseline.catalog`) | why is *this* fear different from your ordinary fear? | never, but fires conditionally |
| 5 | **the edges** (`current.relationships`) | what do you make of *this person*? | every beat they act, and over time |
| 5b | **the second order** (`edge.their_view`) | what do you think *they* make of *you*? | when they act toward you — never authored, it accretes |
| 6 | **affect** (`current.affect`) | what are you feeling right now? | every beat |

A seventh thing is not authored per character at all: the **compound vocabulary**
(`src/engine/compounds.py`) is engine-owned. "Contempt" means the same shape for everyone, or the
word carries no information. What varies per person is which catalog rows FIRE, never what a name
means.

---

## 1. Genotype — draw it, or author it backward

**Background and supporting cast: draw.**

```bash
python scripts/make_genotype.py --seed <anything> --count 5
```

The seed IS the person: same seed, same character, forever. Record the seed and you can reproduce
them. `--rows` emits the genotype as `levers` buff rows, which is what it structurally is — a
permanent unconditional multiplier on a primitive's gain.

**Principals: author backward.** Start from the character the story needs, choose the alleles that
produce them, then validate forward — the world must plausibly make such a person. Drawing a
principal is starting from the dice and hoping for a protagonist.

**Why this layer exists at all:** without it two soldiers in the same battle feel the same thing.
And because nothing can write the genotype afterwards, two people who then live *identical lives*
still end up different. That is the entire point; if you skip it, your cast converges.

Vocabulary is exactly `low | typical | elevated | high` → 0.75 / 1.0 / 1.2 / 1.3. **Anything else
silently reads as typical** — the one place in the schema where a typo costs you a character trait
and says nothing.

## 2. Temperament — the resting face

**Do not type a number. Start from `reference-species-prior.md` and apply the diffs their life
earned.** That table gives the species zero-point for every field, the formative diffs that move
it, and a provenance tag per row so you know which numbers are definitional and which are a
calibration nobody has falsified.


Seven means, one per primitive. **The mean is the personality's resting face, not its starting
mood.** An anxious character is a high FEAR *mean*, not a high starting affect — start affect at or
near the means unless the book opens mid-crisis.

The mean also sets the ceiling. Under sustained maximum pressure a primitive settles at
`mean + (1 − mean) × r`, so a character resting at FEAR 0.10 tops out near 0.75 through the ordinary
path. That is correct for a resting level, and it is why layer 4 exists: without a catalog, calm
becomes an *immunity* rather than a disposition.

## 3. The worth menu — why it lands

`schwartz` / `moral_foundations` / `needs` weights decide *relevance*: the same event hits harder on
the character whose values it touches. Author only the weights you mean; **a missing key reads
neutral 0.5, not zero.** Silence is average, not absence.

## 4. The catalog — the situational half, and where the nuance actually lives

This is how "brave, but terrified of spiders" stops being a contradiction and becomes arithmetic.

```json
"catalog": { "rows": [
  { "when": {"percept": ["spider", "web"]},
    "lever": "FEAR", "op": "x", "magnitude": 3.4,
    "source": "the bite that blinded him three days as a boy" },
  { "when": {"present_edge": {"affinity": 0.70}},
    "lever": "FEAR", "op": "x", "magnitude": 0.62,
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
- **A wound needs an operational twin.** `drives.fears_wounds` is prose the actor reads. If it has a
  `trigger` list and no matching row, the phobia never enters a computation — `lint_book.py` warns
  on exactly this, and it found four such wounds in an active book the day the check was written.
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
- **`default_trust` in `baseline.relationship_priors` is where an edge RESTS**, not where it starts.
  Unreinforced edges relax toward it when a scene declares `elapsed`, affinity fading fastest.

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
                                                            # wounds with no catalog row
python tests/test_genotype.py                               # the draw is reproducible
python tests/test_compounds.py                              # the vocabulary is separable
```

Then render what the actor will actually receive — the only check that catches a number which
changed and a direction which did not:

```bash
python -c "import sys; sys.path.insert(0,'.'); import json; from src.engine.scene import assemble; from src.engine.direction import direct_affect; ch=json.load(open('characters/<x>.json')); w=json.load(open('world/<y>.json')); pk=assemble(ch,w,{'event':{'text':'<the event>','kind':'threat'},'recent':[],'location':'<loc>'},dict(ch['current']['affect']),ch['current']['condition']); st=pk['volatile']['state']; print(st['affect']); print(st['effective']); print([r['source'] for r in pk['volatile']['levers']]); print(direct_affect(st['effective'], ch['baseline']['temperament']))"
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

The genotype draws. Nothing else does. Temperament, the worth menu, the catalog and the vault are
authored, and the full creation pass the design calls for — position → formative environment →
baseline → individuation — is unbuilt. Author forward from the world where you can; the world is
supposed to be the input that produces the baseline, not decoration around it.
