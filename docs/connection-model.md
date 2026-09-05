# Connection — what a character is invested in, and how much it multiplies

**Status: NORMATIVE.** The author settled these five decisions in session on 2026-08-31. Every
measurement quoted here was run against this repo's own code on that date and is reproducible by
the snippet named beside it.

`docs/character-model.md` "DECAY AND CONNECTION" states the rule this document builds out:
**the greater the connection, the larger the impact — and the longer it lasts.**

---

## 1. Connection is a MULTIPLIER, not a channel for harm

The author's words:

> "Connection isn't just bad, it's a multiplier of impact. For good or bad, a loyal soldier that
> sees their kingdom winning victories would have a boost from their connection to their kingdom."

This corrects an asymmetry that was in the shipped code. MEASURED — `connection.SCALED_DIMS`
against `state._DIM_TO_PRIMARY`:

| dimension | what it is | amplified? |
|---|---|---|
| `care_relevant` | someone you love is affected | yes |
| `loss` | something is gone | yes |
| `social_violation` | you were wronged | yes |
| `mastery` | **you or yours prevailed** | **no** |
| `relief` | **the bad thing ended** | **no** |
| `attraction` | **desire** | **no** |
| `threat` | danger | no |

Connection amplified grief, betrayal and concern — and no form of triumph, relief or desire. The
loyal soldier was the exact failing case: his kingdom's victory routes through `mastery`, which
connection never touched, so loyalty bought him nothing when they won and cost him everything when
they lost.

Two separate causes, recorded so neither recurs:

* **`relief` was excluded by a bad argument.** `connection.py` said it stays out because "its pushes
  are negative and a negative push binds no party to compose a connection from." That confuses the
  SIGN OF THE PUSH with the EXISTENCE OF A SUBJECT. Relief pushes FEAR -0.40 and PANIC_GRIEF -0.35 —
  a good thing happening — and it plainly has a subject: relief *about* something.
* **`mastery` and `attraction` were never considered.** The exclusion docstring argues `threat` and
  `relief` and is silent on both.

### THE RULE: scale a dimension when it has a SUBJECT you can be bonded to. Never by valence.

Under that test `mastery`, `relief` and `attraction` all come in. `threat` stays out, and the
existing argument for it is sound and survives: a threat's subject is the SOURCE OF DANGER, so
scaling by connection-to-the-subject would mean connection to the wolf. Fear FOR someone rides the
`care_relevant` half a threat-to-a-loved-one also emits, and that half is scaled.

The consequence is that connection becomes the mechanism by which a GOOD life amplifies. The loyal
soldier and the beaten slave are then the same machinery run in opposite directions, which is the
property that makes it a model of investment rather than a model of suffering.

---

## 2. Dimensions carry their own SUBJECT

The author's words:

> "We need the one that processes the scene for the db to also go over the scene and tag ... This
> way the engine can do the calculations without having to try and make semantic judgement."

The tagging step ALREADY EXISTS. `consolidation.py` runs an LLM that emits appraisal dimensions,
`_KNOWN_DIMS` derives from `state._DIM_TO_PRIMARY` rather than hand-copying it, and `validate_tags`
refuses unknown dimensions loudly. What is missing is narrower than "we need tagging".

**The defect: `dimensions` is a flat `{dim: float}` and `target` is a single event-level field.**
One event, one subject. The contract at `consolidation.py:449` reads:

```
{type, summary?, dimensions: {dim: <severity word>}, durability, target?, confidence?}
```

A battle where the kingdom wins and a friend dies emits `mastery` AND `loss` with DIFFERENT
subjects, and there is room for only one. Connection cannot route them separately, so either the
victory is amplified by grief or the death is amplified by loyalty. Both are wrong.

### THE CONTRACT CHANGE

```
dimensions: { mastery: {magnitude: 0.7, subject: "aldric_kingdom"},
              loss:    {magnitude: 0.9, subject: "sana"} }
```

The engine then looks each subject up independently and multiplies. **No semantic judgement
anywhere in `src/engine/`** — the tagger says which triumph belongs to which banner and which grief
to which person; the engine does arithmetic. This is the same compute/generate split as hard rule 5,
applied to aboutness instead of to numbers.

It also settles a question this design could not otherwise answer: WHICH abstraction a harm binds to
(`the_world` vs `the_law` vs `the_guild`). The tagger names it. The engine counts distinct subjects
against a floor.

### WHO TAGS: the consolidation pass, not the sim actor

The actor is inside the character and has a stake — asking it to label its own utterance's
`social_violation` invites self-serving tagging, and it cannot see what the other actors did.
Consolidation sees the whole scene from outside and is already the LLM whose vocabulary the
engine's dimension table was built for. **The actor's job is to BE the person; the recorder's job is
to say what happened.**

### GUARD REQUIRED

`validate_tags` must reject a subject naming nobody perceivable. `consolidation._is_perceived`
already performs that check for the single `target`; it must run PER SUBJECT, or a tagger can invent
an entity and open an edge to a hallucination.

---

## 3. Two floors, because binding and relevance are different questions

The author's words:

> "I think for connections there needs to be a floor that binds when a person can begin to project
> towards concepts. It can't be an always thing."

`connection._FLOOR = 0.20` asks: GIVEN a bond, is it strong enough to modify anything? That is a
RELEVANCE floor and it already exists.

The author's floor asks: does this entity exist as an object of feeling for this person AT ALL?
That is a BINDING floor and it does not exist. Collapsing the two would give every newborn a
relationship with the world sitting just under the dead zone.

**Abstract entities are LATENT until bound.** No edge, no rows, no cost. A sheltered character
never has a world-bond, and that is free rather than suppressed.

### BINDING FOR A CONCEPT: source variance, not volume

Eighty beatings from ONE overseer should make a character hate A MAN — that is a person-bond, and
the engine already does it well. Eighty beatings from twenty different hands, with no one to point
at, is what has nowhere to land, and that is when a person generalises.

**A concept binds when the harm stays constant and the source stops being attributable.** Solitary
confinement (no subject at all) binds to the world; a single abusive marriage does not; a slave
sold between owners does. The rule predicts those without extra clauses.

Cheap on evidence: `relationship_deltas` already records `(perceiver, target, axis, delta,
cause_event)` per turn, append-only. Counting distinct subjects behind a class of harm is a query
over data the engine already writes.

### HYSTERESIS IS REQUIRED

Bind high, unbind lower. A concept sitting exactly on the threshold would otherwise flicker between
scenes and jitter every number in the run — the same "buy silence" reasoning behind the existing
dead zone.

---

## 4. The same floor governs PEOPLE

The author's words:

> "It's the same logic for not creating connections with every person that an individual meets. We
> need a reason to record the connection. Loose connections are invisible and will clog the db."

MEASURED — repeated interaction with one person, from a neutral edge, via `bonds.observe`:

| repeated act | affinity plateau | connection | delta rows | ever visible? |
|---|---|---|---|---|
| ordinary courtesy | 0.575 | **0.000** | **251** | **never** — stops moving at #131 |
| real kindness | 0.800 | 0.450 | 296 | at interaction 10 |
| major kindness | 0.975 | 0.712 | 311 | at interaction 6 |

Ordinary courtesy repeated 131 times writes 251 delta rows and NEVER becomes visible. Not slow —
structurally incapable. The error-driven update converges to where the act's magnitude puts it, and
for ordinary pleasantness that asymptote sits below the relevancy floor forever.

`bonds.observe` has no threshold of any kind; its own docstring takes `{}` for a stranger, so
strangers are processed like anyone else. The fan-out is quadratic — `scripts/scene.py:170`, every
other person in the room re-reads the speaker each turn. A cast of 12 over 200 turns is roughly
4,400 delta rows, overwhelmingly pleasantries between people who will never matter to each other.

### THE RULE: gate on the ACT'S ASYMPTOTE, not on an accumulated count

An act whose repeated application converges below the relevancy floor never opens an edge. This is
computable at the moment it happens, from the act alone, with no history, deterministically.
Ordinary courtesy never opens one; real kindness does.

### NOTHING IS LOST BY NOT RECORDING

The obvious objection is that an unrecorded bond can never accumulate toward the threshold. It is
answered by the log. `events` retains `actor`, `target` and the full dimension payload, so when a
later act DOES open an edge, that pair's history is replayed out of the log. This is hard rule 2
exactly: the deltas table is a derivable cache, never the source of truth.

---

## 5. One binding rule for every entity

| entity | binds when |
|---|---|
| a person | the act's asymptote clears the relevancy floor |
| a concept | the same, PLUS the harm arrives from enough distinct subjects |

A concept needs the extra condition because it additionally requires the harm to stop being
attributable to any one person. Otherwise the rules are identical, and `bonds`, `connection` and
`toward` need no separate code path for abstractions — an abstract entity is an entity.

---

## What this does NOT settle

* **The binding thresholds themselves** are calibration and want a probe against a real book. The
  FORM (a hard dead zone, hysteresis, asymptote-gating) is the normative part; the numbers are not.
* **The negative half of the pricing table.** MEASURED: four of eight primaries — RAGE, LUST, CARE,
  DISGUST — have no dimension anywhere that lowers them, so no event can ever calm rage, dull
  desire, harden a heart or overcome revulsion; only `arc.erode`'s calendar can. `levers.effective`
  accepts signed authored rows, so the SYSTEM can lower them; but across every fixture in
  `characters/`, every authored magnitude is positive. Connection cannot fix this — a multiplier
  needs something to multiply. Tracked separately.
* **Whether a soured world-bond can heal, and through what.** The machinery permits it (`bonds.drift`
  relaxes toward the resting prior); whether a life can be redeemed is a story question the author
  has not yet ruled on.
