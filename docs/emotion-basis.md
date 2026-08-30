# Emotion basis — the primitives, their targets, and where tense lives

*(Normative. Settled with the project owner 2026-08-22. This doc owns the QUESTION "what are the
irreducible emotions and how is everything else expressed in them." `state-engine.md` owns the
tiers; `decision-engine.md` owns the catalog; `direction.py` owns the words.)*

## The criterion

**A primitive is an emotion that cannot be derived from a combination of other emotions.**

Contempt can be built — anger and disgust, in proportion. Fear cannot be built from anything. That
asymmetry is the whole test, and it is the only test: not "is it universal," not "does it have a
face," not "is it in the literature." Irreducibility.

**Irreducibility is relative to what combining means**, which is why the standard proposals
disagree. Ekman's criterion is facial expression (6 states); Plutchik's is opposed adaptive
reactions (8, with compounds as dyads); Izard's is discrete developmental programs (10);
Panksepp's is distinct subcortical motivational circuits (7).

**We take Panksepp's criterion**, and not by preference. His test is *does this generate a distinct
class of behaviour* — and behaviour is this engine's entire output. Ekman's test is facial, which
is irrelevant here: there are no faces.

## The primitives — eight

| primitive | the thing nothing else produces |
|---|---|
| **SEEKING** | forward pull toward what might be found |
| **FEAR** | withdrawal from anticipated harm |
| **RAGE** | approach to remove an obstacle or redress a wrong |
| **LUST** | approach toward union |
| **CARE** | act on another's behalf at cost to yourself |
| **PANIC_GRIEF** | distress at a broken bond |
| **PLAY** | engagement for its own sake, without stake |
| **DISGUST** | expel — *this would contaminate me* |

**DISGUST is a deliberate departure from Panksepp and the reason is recorded here so it cannot rot
back.** He excluded it, classing it a sensory affect rather than a primary-process circuit — a
considered position, on a criterion of neural-circuit type. It is NOT an exclusion on
irreducibility. By the test above disgust passes cleanly: FEAR withdraws from danger, RAGE attacks,
and neither produces *get this away from me before it gets into me*. Ekman, Plutchik and Izard all
include it. Without it, `social_violation -> RAGE` is the only social path and every slight can only
produce anger — an engine that cannot tell a man who squares up from a man who looks away.

### What is NOT a primitive, and why

**SURPRISE passes irreducibility and fails the lever test.** You genuinely cannot mix it —
expectation-violation is orthogonal to valence. But it carries no action tendency beyond "orient,"
and it resolves in seconds rather than beats. It is primitive *and not motivational*, so it belongs
as an appraisal DIMENSION, not a lever. `relief` is already handled exactly this way and is the
precedent.

**SHAME is not primitive — it is the evidence that mixture alone was an incomplete model.** See the
next section; this is the finding that produced the target rule.

**Compounds, with recipes** (per-primary targets, per below):

| state | recipe |
|---|---|
| contempt | RAGE(them) + DISGUST(them) |
| shame | PANIC_GRIEF(self) + DISGUST(self) |
| guilt | PANIC_GRIEF(self's act) + CARE(the person harmed) |
| indignation | RAGE(offender) + CARE(victim) |
| jealousy | CARE(beloved) + RAGE(rival) + FEAR(the loss) |
| pride | SEEKING-satisfied(self) |
| love | CARE + LUST + attachment-bond |

Note that **love is a compound**, so a recipe naming love as an ingredient is citing another
compound. That is allowed; it means love needs its own coordinate before contempt-toward-someone-
once-loved can cite it.

## Targets are per-PRIMARY, not per-compound

**The measurement that settled this** (2026-08-22): the best shame coordinate expressible by
mixture alone — PANIC_GRIEF high, FEAR mid, PLAY floored, SEEKING low — renders through
`direction.py` as a good behavioural profile (withdrawn, hedging, unreachable, humourless) and is
**indistinguishable from grief-plus-fear**. A man who just buried his brother and a man just
publicly humiliated receive identical directions.

The distinguishing feature of shame is not its intensity profile. It is its **aboutness**. Grief is
about a loss; shame is about *you*. A coordinate carries magnitudes and no object, so mixture
cannot express it.

**One target per compound is also insufficient.** It cannot separate shame from guilt (both
self-directed, opposite behaviour: shame hides, guilt repairs) nor anger from indignation (same
coordinate, same object, but indignation has a beneficiary).

**So the model is `{primitive -> (magnitude, target)}`.** Each primitive in a compound carries its
own target. The relational family then falls out with no special cases — jealousy is notoriously
hard to model and becomes three primitives pointing at three different objects, which is precisely
what makes it feel unstable to the person having it.

**This is a change to what exists, not an addition.** `state.appraise` takes ONE `target` per
EVENT, and `regard_factor` applies it uniformly across `_REGARD_SCALED_DIMS`. Per-primary targets
move the target from the event onto the state, and `_regard` becomes a per-primitive evaluation.

**Cost, stated plainly:** more to author (a target per primitive rather than one per row), and
`_regard` runs per-primitive. Worth it, because without it shame and grief render identically —
the no-nuance-in-a-tag failure, one level up from where it was found in the sheets.

### BUILT 2026-08-22 — and the registry it needed first

The gap this section did not name: there was no statement anywhere of **how each primitive is
directed**. `compounds.py` annotated roles per RECIPE and `state._REGARD_SCALED_DIMS` said which
DIMENSIONS were outward — the basis itself said nothing. Without it, the aboutness of eight
primitives would have been decided by whichever call site bound first.

`records.DIRECTEDNESS` is that registry, and it is NORMATIVE. Each row is argued from what the
Panksepp system makes a body do; the compound table's role counts were admitted as corroboration
only, because downstream aligns to the basis and never the reverse. Following that rule caught five
recipes that had already drifted FROM this doc — jealousy binds FEAR reflexively where this section
says FEAR of *the loss*, and four rows bind PLAY reflexively where covertness is a delivery
register. `compounds.validate()["drift"]` reports them.

**The role vocabulary collapses to one plus derivation.** `self` is not authored — it is the object
role where the bound id is the character's own, so the registry decides only whether a primitive
ADMITS it. `beneficiary` is CARE's object seen from inside a multi-party recipe; the one-slot model
cannot express a beneficiary distinct from an object on the same primitive anyway, and multi-party
states use several primitives with one target each — this doc's own jealousy example. `self.act` is
the object role with an event-typed target, which is where the tense section already puts this kind
of structure.

**THE LAW, so a ninth primitive does not re-litigate it:** *a primitive needs its own reflexive
stage directions exactly when its action tendency becomes incoherent aimed at the self.* Attack
survives — you can go at yourself. Shutdown survives — it never pointed at anything. Pursuit
inverts to display. Expulsion inverts to concealment.

That law is why the cost is seven phrases and not ninety-six, and why the two columns are
separate: **PANIC_GRIEF admits a reflexive bind and needs no new words at all** (its despair phase
is autonomic and undirected, which is exactly why all four of its measured phrases are posture),
while **DISGUST is rarely self-directed and needed all three live bands rewritten** (the object
phrase says *"you will not be in the room with it"*, and you cannot walk out of a room away from
yourself).

Measured on the same character with the same numbers — DISGUST 0.556, RAGE 0.572:

| the violation was HIS | the violation was HERS |
|---|---|
| you decline to touch it, and you let them see you decline | you keep yourself out of what is offered to you, and you give no reason |

**Still open here:** tense, which needs targets that name recall entries and beliefs plus the
unparsed vault `timestamp`; and the render GROUPING that would stage jealousy's three parties
separately, held back so a quality regression stays attributable.

## Tense is a property of the OBJECT, not the emotion

The basis does NOT encode tense, and an earlier claim in this project that it did (FEAR = future,
PANIC_GRIEF = past) is **wrong and retracted**: fear's object is usually PRESENT — the spider is on
the ledge now — and only the harm is future; grief can be anticipatory; rage concerns a past act but
demands present action.

Tense splits into three things that belong in three places:

**1. Where the object sits in time — already structural.** The packet separates `percepts` (now)
from `recall` (then) at `scene.py:116-117`. That IS the present/past distinction, living on the
thing the emotion is about. **But the structured time marker is missing:** `guide-content.md:49`
specifies vault entries as `{claim, believed_value, provenance, timestamp, confidence}` and
`vault.py:69` parses everything except `timestamp`. So the engine cannot distinguish a wound from
last week from one thirty years old. **Restoring it is a prerequisite**, not a nicety — without it
past targets have no depth.

**2. Which way the action tendency points — in the basis, but it is not tense. It is
REACHABILITY.** Can you act on the object? FEAR: the harm is preventable, act now. RAGE: the wrong
is redressable, act now. PANIC_GRIEF: the loss is done, nothing to act on — which is exactly why
its direction renders as *"you stop, and what the scene wants from you does not reach you."*
Reachability is what is behaviourally load-bearing; tense is only a proxy for it.

**3. Counterfactual and modal states — inexpressible, and a tense axis would not fix them.** Regret
is not past-tensed grief; it requires the alternative that did not happen. That is a PROPOSITION,
not a magnitude and not a timestamp, and propositions live in the vault. Same answer as guilt: the
affect is expressible, the aboutness is a belief.

**Therefore: no tense axis.** With per-primitive targets that may point at recall entries and
beliefs — not only present entities — **tense is inherited for free**. Grief targeting a recall
entry IS past. Fear targeting a percept IS present. Dread targeting a belief about what is coming IS
future. One mechanism, three jobs.

## Open, measured, and blocking

- ~~**LUST is unreachable by any appraisal dimension.**~~ **CLOSED 2026-08-22.** It sat at its
  temperament mean forever — a channel that emitted (four phrases, a stage direction fired for 4 of
  5 characters in a measured scene) and never received. Fixed with a seventh dimension,
  `attraction` (LUST 0.45, SEEKING 0.18, PLAY 0.10), admitted on the `bond` and `mundane` CATALOG
  entries only. Measured: 0.200 → 0.394 over three beats.

  **The rule this entry set was honoured, and it was the right rule.** It said *fix reachability
  before changing the basis size*, and reachability was in fact fixed in the same session that
  added DISGUST — but the ORDER went the other way, DISGUST first. That was a real (small)
  violation of this doc's own sequencing, and it is recorded here rather than quietly reordered.
  What made it survivable is that `tests/test_disgust.py` now asserts EVERY primitive is reachable,
  so the rule is enforced mechanically instead of by remembering to read this line.
- **`timestamp` is specified and never parsed** (above).
- **`_REGARD_SCALED_DIMS` is outward-only** (`care_relevant`, `loss`), so the reflexive case has no
  path today. Per-primitive targets require it.
- **The compound layer does not exist.** Until it does, none of the recipes above is testable, and
  the basis cannot be verified — "primitive" is a relation between an element and what it composes,
  so with nothing composed there is nothing to be primitive relative to.

### A character at REST is issued four stage directions

Surfaced 2026-08-22 by a control in `docs/basis-verification.md` that was built to render nothing
and did not. `direction.py:201` decides what the actor is told:

    notable = b >= 1 or abs(dev) > _DEV_THRESH

The first test is on the ABSOLUTE band, so a primitive surfaces whenever it clears 0.25 — whether or
not anything moved it. Measured on `characters/ren-traveler.json` sitting exactly at its own means:
SEEKING 0.50 (band 1), CARE 0.55 (band 2), PANIC_GRIEF 0.25 (band 1), PLAY 0.35 (band 1). Four of
eight primitives surface, and CARE surfaces at STRONG — so this character is permanently instructed
"you act for them before you have finished deciding to, and you interrupt yourself to do it", as
though it were news.

**This is arguably correct** — disposition IS how a person behaves at rest, and a warm character
should read as warm before anything happens. It is also, on the face of it, the noise floor every
event has to compete with.

**MEASURED 2026-08-23, and the floor is harmless** (`basis-verification.md` §10). The comparative
probe rendered the same pairs on this fixture (four standing clauses present) and on a flat one
(the differing clause is most of the text): **ordinary 24/24, flat 23/24**. The standing clauses
cost nothing when the differing clause is a genuine SUBSTITUTION rather than an absence. So
`direction.py:201` stands as written, and the salience-grouping repair is not indicated.

The distinction that survives is between a substituted clause and a missing one: `cold` vs
`embarrassment` differ by one clause that is PRESENT in one and ABSENT in the other, and no judge
separated them. A pair whose renders differ by an absence is the case to watch, not a pair whose
renders differ by a standing-clause count.

## How the basis gets verified

A basis cannot be proven sufficient, only fail to be falsified. The procedure, in the order it has
to happen:

1. **Author the target vocabulary BLIND to the basis.** ~40-60 states the engine must express. If
   the list is written after the basis is fixed, whoever writes it will unconsciously choose states
   the basis can express and the test confirms itself. Take it from an external lexicon, or from a
   judge naming the driver behind real scene output.
2. **Express each as a coordinate with per-primitive targets.**
3. **Measure three signatures.** Benchmarked against an independently-authored 58-state vocabulary
   built on a different 8-dimension basis for a different purpose (measured 2026-08-22): **no dead
   dimension** (each appeared in 19-84% of states), **mean mixture 3.00** dimensions per state, and
   **91% of states required mixing** (only 5 of 58 were single-dimension, and those five were the
   base tags themselves). A basis whose mean mixture is ~1 is a word list with extra steps; one
   where a primitive appears in almost nothing has a special case masquerading as an element.
4. **Render and blind-judge** — the confusion matrix over the rendered words.

The failure modes then read off, each pointing at a different repair:

| observation | repair |
|---|---|
| a state no coordinate reaches | missing primitive |
| two distinct states, same coordinate | missing dimension (target, or a primitive) |
| a primitive appearing in almost nothing | not an element — a special case |
| coordinates differ, rendered words do not | **the direction layer is the bottleneck, not the basis** |

That last row is why step 4 is worth running against the CURRENT eight before adding anything. It is
entirely possible the basis is fine and the 55 phrases in `direction.py` are the constraint — in
which case every hour spent on the basis is spent on the wrong layer.
