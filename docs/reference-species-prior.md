# Reference — the species prior, and the formative diffs that move it

*(THE NUMBER TABLE. An author opens this when they need to write a value and do not want to invent
one. It closes `baseline-generation.md` open questions #1 and #2. `baseline-generation.md` owns the
COMPOSITION; `guide-emotional-authoring.md` owns the ORDER; this owns the VALUES.)*

## The rule this table exists to serve

> **"A number you can't trace to their life is the arbitrary insert the design rejects."**
> — `baseline-generation.md:31`

You do not type a temperament mean. You start at the species prior and apply the diffs their life
earned. If a field ends up different from the prior, some layer below must say why — and that
"why" is not decoration: `baseline-generation.md:31` says provenance **seeds the vault**, so the
reason they are afraid becomes a thing they remember.

```
SPECIES PRIOR  ⊕  GENETICS  ⊕  CULTURE/ERA  ⊕  CLASS/POSITION  ⊕  FORMATIVE ENV  ⊕  HISTORY
   (below)        (drawn)      (diffs, below, broad → specific, accumulating)
```

## PROVENANCE TAGS — read these before trusting any number

Every row is tagged. They are not equally solid and pretending otherwise is how a calibration
becomes folklore.

| tag | means |
|---|---|
| **[DEFINITIONAL]** | true by how the scale is constructed. Not a research finding, not a choice. |
| **[LITERATURE-ORDERED]** | the RANK ORDER is a replicated empirical finding; the exact magnitudes are fitted to this engine's 0–1 scale. |
| **[CALIBRATION]** | a chosen starting value. Theory constrains the direction, not the number. Falsifiable, and nobody has falsified it. |

---

## 1. Species prior — HEXACO traits

| facet | prior | provenance |
|---|---|---|
| honesty_humility | **0.50** | **[DEFINITIONAL]** |
| emotionality | **0.50** | **[DEFINITIONAL]** |
| extraversion | **0.50** | **[DEFINITIONAL]** |
| agreeableness | **0.50** | **[DEFINITIONAL]** |
| conscientiousness | **0.50** | **[DEFINITIONAL]** |
| openness | **0.50** | **[DEFINITIONAL]** |

**Why every one is 0.50 and this is not laziness:** HEXACO facets are *standardized* — the scale is
built so the population mean sits at the centre. Asking "what is the average person's
conscientiousness" is asking where the middle of a scale defined by its middle is. The interesting
number is never the mean; it is **variability**, which `trait-theory.md` carries separately.

Default **variability 0.10** **[CALIBRATION]** — the within-person spread. Raise it for someone
erratic, lower it for someone rigidly consistent. This is a real characterisation lever and it is
almost always left at default, which is a missed one.

## 2. Species prior — Panksepp primaries (resting means)

| primitive | prior | provenance |
|---|---|---|
| SEEKING | **0.45** | **[CALIBRATION]** — the baseline-active system; Panksepp treats it as tonically engaged, so it sits above the others |
| FEAR | **0.25** | **[CALIBRATION]** — resting vigilance, not alarm |
| RAGE | **0.20** | **[CALIBRATION]** — low tonic; RAGE is phasic by nature |
| LUST | **0.20** | **[CALIBRATION]** — reachable since 2026-08-22 via the `attraction` dimension |
| CARE | **0.40** | **[CALIBRATION]** — humans are a cooperatively-breeding species; tonic care is not low |
| PANIC_GRIEF | **0.25** | **[CALIBRATION]** — resting attachment-alertness |
| PLAY | **0.35** | **[CALIBRATION]** — present when safe, and the first to go under threat |
| DISGUST | **0.15** | **[CALIBRATION]** — the LOWEST resting value of the eight, and deliberately so: revulsion is phasic like RAGE, but unlike RAGE it also decays slowly (`state._DECAY_RATE` 0.88), so a high resting DISGUST would leave a character permanently contemptuous with nowhere to move |

**These eight are the softest numbers in this document.** There is no standardized instrument
giving "resting FEAR" a population value the way HEXACO gives trait means, so theory constrains
only the ordering: SEEKING tonically highest, RAGE / LUST / DISGUST phasic and low, PLAY conditional
on safety. **If any row here is wrong it is these**, and the falsification is behavioural — a cast
built on this prior that reads uniformly flat or uniformly frantic.

## 3. Species prior — the worth menu

### Schwartz values

| value | prior | provenance |
|---|---|---|
| benevolence | **0.70** | **[LITERATURE-ORDERED]** — Schwartz's pan-cultural hierarchy puts benevolence at or near the top in nearly every sample |
| self_direction | **0.65** | **[LITERATURE-ORDERED]** — consistently top-three |
| universalism | **0.60** | **[LITERATURE-ORDERED]** |
| security | **0.55** | **[LITERATURE-ORDERED]** — mid |
| conformity | **0.50** | **[LITERATURE-ORDERED]** — mid, and the most culture-variable, so the culture diff moves it most |
| achievement | **0.50** | **[LITERATURE-ORDERED]** — mid |
| hedonism | **0.45** | **[LITERATURE-ORDERED]** |
| tradition | **0.40** | **[LITERATURE-ORDERED]** — consistently low-ranked, and highly culture-variable |
| stimulation | **0.35** | **[LITERATURE-ORDERED]** — consistently near the bottom |
| power | **0.30** | **[LITERATURE-ORDERED]** — consistently last or near it |

The **order** is the replicated finding; the **spacing** is fitted to this scale. A character who
ranks power above benevolence is not impossible — they are *unusual*, and that is exactly what you
want the prior to tell you.

### Moral foundations

| foundation | prior | provenance |
|---|---|---|
| care_harm | **0.65** | **[LITERATURE-ORDERED]** — highest-endorsed across groups |
| fairness | **0.60** | **[LITERATURE-ORDERED]** |
| liberty | **0.50** | **[CALIBRATION]** — least settled of the six |
| loyalty | **0.45** | **[LITERATURE-ORDERED]** — the binding foundations sit lower on average and vary most by group |
| authority | **0.45** | **[LITERATURE-ORDERED]** |
| sanctity | **0.40** | **[LITERATURE-ORDERED]** |

### Needs (self-determination)

| need | prior | provenance |
|---|---|---|
| relatedness | **0.60** | **[CALIBRATION]** — all three are posited as universal, so all three sit above mid |
| competence | **0.60** | **[CALIBRATION]** |
| autonomy | **0.55** | **[CALIBRATION]** — the most culture-variable of the three |

**A missing key reads 0.50, not 0.0** (`state.py:_relevance`). Silence is average, not absence. So
author only the weights their life bent, and leave the rest out.

## 4. Skills and relationship priors

| field | prior | provenance |
|---|---|---|
| any skill, untrained | **0.30** | **[CALIBRATION]** — competent-adult floor, not zero. Zero is an infant |
| `relationship_priors.default_trust` | **0.50** | **[CALIBRATION]** — this is the field the FORMATIVE ENV diff moves hardest |

**The three skills the engine actually consults** (`guide-content.md`): perception ≥ 0.60 sees
subtle cues, insight ≥ 0.55 recognises identity, combat gates harm capability. Author those
deliberately; the rest ride the prompt as context.

---

## 5. The formative diffs — sparse, broad → specific, accumulating

`baseline-generation.md:29` — each layer **biases what it touches and leaves the rest at prior**,
and they **accumulate**: a street-raised war-survivor stacks both. Additive, then clamped.

**Single-axis first** (`character-model.md` discipline). A profile that moves nine fields is a
character, not a preset — and you cannot tell which field did the work.

### CULTURE / ERA — writes the Model (value weighting), seeds the cultural vault

| profile | diff | why |
|---|---|---|
| honour culture | `loyalty +0.20`, `authority +0.15`, `fairness −0.10` | the binding foundations bind harder |
| mercantile | `achievement +0.15`, `fairness +0.10`, `tradition −0.15` | contract over kin |
| devotional | `sanctity +0.25`, `tradition +0.20`, `self_direction −0.15` | |
| besieged / wartime | `security +0.20`, `loyalty +0.15`, `stimulation −0.10` | |

### CLASS / POSITION — writes drives, resource-priors, role knowledge

| profile | diff | why |
|---|---|---|
| propertied | `power +0.15`, `security +0.10`, `autonomy +0.10` | |
| labouring | `competence +0.10`, `relatedness +0.10`, `power −0.10` | worth is what you can do |
| dispossessed | `security +0.20`, `default_trust −0.20`, `autonomy −0.15` | |
| clerical / lettered | `conformity +0.15`, `openness-variability −0.03` | |

### FORMATIVE ENVIRONMENT — the big shaper: disposition, relationship-priors, the wound

| profile | diff | why |
|---|---|---|
| stable household | `default_trust +0.15`, `FEAR −0.05`, `PLAY +0.05` | |
| neglect | `default_trust −0.25`, `PANIC_GRIEF +0.10`, `CARE −0.05` | |
| violence in the home | `FEAR +0.12`, `RAGE +0.08`, `default_trust −0.20`, `emotionality +0.10` | |
| the road / itinerancy | `autonomy +0.15`, `relatedness −0.10`, `SEEKING +0.05` | |
| institutional (barracks, cloister, ward) | `conformity +0.15`, `authority +0.10`, `autonomy −0.15` | |

### PERSONAL HISTORY — targeted diffs, and **every one seeds a vault entry**

Not a table. This is where a specific event moves a specific field and the same event becomes a
belief they carry. If it does not produce both, it is not history — it is a number with a story
attached afterwards.

## 6. Composition caps

`baseline-generation.md` open question #3, answered here as **[CALIBRATION]**:

- **Clamp each field to [0,1]** after summing — already true in code for affect, and it must be true
  at authoring for baselines.
- **Cap the total movement of any single field at ±0.35 from prior across ALL layers.** A
  multiply-traumatized character otherwise saturates every primitive and stops being legible: at
  FEAR 0.95 resting there is nowhere left for an event to take them, and every scene reads the same.
  The *ceiling* is where drama dies.
- **A character whose fields are all at prior is not finished** — they are the species. Somebody
  with no diffs anywhere has no life.

## 7. How to check your work

```bash
python scripts/lint_book.py --vault "$SWE_BOOKS/<book>"
```

Then the question this table exists for: **for every field that differs from the prior above, can
you name the layer that moved it?** If not, that number is the arbitrary insert.

## What is NOT settled

- **The seven resting means (§2) are the softest numbers here** and the most consequential — they
  set the ceiling every character can reach. Flagged rather than hidden.
- **The formative-profile library (§5) is a starter set**, single-axis-first as the discipline
  requires. It is not derived from anything; it is a first draft that authoring will correct.
- **The species prior is HUMAN.** `baseline-generation.md:26` says each people's prior is fixed at
  world-creation, so a non-human people needs its own table and this one does not apply to them.
- **None of this is generated.** The composition pass is unbuilt (`SPEC-LEDGER.md`), so this is a
  reference for hand-authoring what the design says should be composed. When the pass is built,
  this table becomes its input rather than its substitute.
