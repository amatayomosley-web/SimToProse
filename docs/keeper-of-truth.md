# The keeper of truth — how a world grows facts it was never authored with

**Status: NORMATIVE for the tier model and the collapse rule. The keeper agent itself is designed
here and not yet built.** The author approved this design in session on 2026-08-29; it is recorded
because a design that lives only in a conversation is a design that has already been lost once.

## The problem, in the author's words

> "Every world fact isn't created when the book is started. The actors create truth as they speak
> it, so if an actor makes up a fact like, their town only employs female guards. The maintainer
> adds this fact to the db but also creates lore to make this new fact consistent with the world
> it's in. So the maintainer by design needs to be a capable LLM."

And then the refinement that makes it tractable:

> "So can we have tiers of info in the db, authored by user is ground truth, utterances by agents
> are possibilities until they must become truth or fiction. The actor says all guards are women is
> a superposition until this utterance is tested. At this point an alert must be sent with the
> information in contest and either user or the showrunner must decide and then this becomes ground
> truth."

Two claims are being made and they are separable. The first is that **worlds grow**: a bible
written in advance cannot contain every fact a story will need, and demanding that it does either
freezes the story or forces the actors to speak only about what was pre-authored. The second is
that **growth must not be free**: if every offhand line an actor produces becomes world-truth on
utterance, the world accumulates contradictions faster than anyone can read them, and the bible
stops being able to deny anything.

The tier model is what separates them.

## The three tiers

| Tier | Name | What it is | Who may create it | Binding? |
|---|---|---|---|---|
| **T0** | authored | the bible as written before the run | the author | yes — ground truth |
| **T1** | established | a claim that was tested and resolved into truth | keeper or author, on collapse | yes — ground truth |
| **T2** | superposed | a claim an actor uttered, not yet tested | any actor, by speaking | **no** |

**T0 and T1 are indistinguishable downstream.** That is the point of T1: once a claim collapses
into truth it *is* the world, and nothing that reads the bible needs to know whether a fact was
authored on day one or established in chapter nine. The provenance is retained for audit, not for
arbitration.

**T2 binds nothing.** A superposed claim does not constrain any character, does not deny any act,
does not appear as a law, and cannot be cited. It is a recorded utterance with a flag on it. This
is the load-bearing property: an actor inventing a detail costs the world nothing until the detail
*matters*, so actors can speak freely and the world stays clean.

## Collapse — the moment a superposition must decide

A T2 claim stays superposed until something **tests** it. A test is any of:

1. **Contradiction with T0/T1.** The claim and a binding fact cannot both be true.
2. **Contradiction with another T2.** Two actors invented incompatible details.
3. **Reliance.** Something load-bearing depends on the claim being true — an act is permitted or
   denied by it, a decision is computed from it, or a downstream scene is built on it.

On a test, the claim collapses. It becomes T1 (true) or is marked fiction (the actor was wrong,
lying, or mistaken — all three are legitimate story outcomes and the model must not conflate them
with an error). **The engine detects the collapse; it never resolves it.**

### Fiction is a first-class outcome, not a failure

A collapsed-to-fiction claim is not deleted and is not a bug. An actor who said the guards are all
women and was wrong has *said something about themselves* — they were misinformed, or boasting, or
lying. That utterance stays in the log and stays in the speaker's `acquisitions` as a belief they
held. The world simply declines to adopt it. A model that treated fiction as an error would punish
the actors for the improvisation the design exists to permit.

## The split: what the engine does, and what the keeper does

This is where the design meets hard rule 3 (**no LLM calls inside `src/engine/`**) and hard rule 4
(**no randomness in the engine**), and the split is clean rather than a compromise.

**The engine DETECTS.** Deterministically, structurally, with no model in the loop:

* a new claim on a `(subject, predicate)` whose object differs from a binding fact's — contradiction
* two T2 claims on the same `(subject, predicate)` with different objects — contradiction
* a claim being read by anything that binds — reliance

**Be honest about the reach of this.** Structural detection catches *direct* contradiction: the same
subject and predicate carrying different objects. It does **not** catch semantic contradiction —
"the guards are all women" against "Captain Aldric commands the gate" requires knowing Aldric is a
man and a guard, which is inference, not a key comparison. The engine will miss those, and the
design does not pretend otherwise. Semantic conflict is the keeper's job precisely because it needs
a model; the engine's detector is a floor, not a ceiling. Claiming otherwise would be the kind of
coverage-versus-content confusion CLAUDE.md already records the cost of.

**The keeper RESOLVES**, and the author's original framing is exactly right about why it must be a
capable LLM:

* decides truth or fiction, or escalates to the author
* **authors the lore that makes an adopted fact consistent** — this is the part no rule engine can
  do. Adopting "this town only employs female guards" is not a row insert. It implies a history, a
  reason, probably a law, possibly an exception, and certainly consequences for scenes already
  written. The keeper writes that.
* writes the resulting T1 facts back through the normal bible path so they are auditable

**The alert is the seam between them.** The engine raises it with the contested information
attached; the keeper or the author decides. Nothing collapses silently.

## Where a claim lives — reuse the law structure, not a parallel one

`bible_laws` already carries `modality` (IMPOSSIBLE / FORBIDS / REQUIRES / PERMITS), `epistemic`
(known-true / known-false / contested-unknowable), `source_note` for provenance, and scoping by
actor class, location and time. A superposed claim is not a different *kind* of thing from a law —
it is a law-shaped assertion with a weaker warrant. Building a second store for it would be the
eighth entry in CLAUDE.md's duplicates table, and every one of the previous seven had already gone
wrong by the time it was found.

Claims in flight are RUN-scoped, not bible-scoped, so they need their own append-only home — they
are utterances, and utterances belong to the log. What must not be duplicated is the LAW structure:
an adopted T1 fact is written back as a `bible_law` or `bible_entity` through the normal path rather
than living forever in a second shape. `epistemic` is the tier column's
natural neighbour: `contested-unknowable` already encodes "the world does not settle this", which
is adjacent to but distinct from "the world has not yet settled this".

## Open questions, named rather than hidden

* **Reliance is the hard trigger.** Contradiction is a comparison; reliance means noticing that
  something *depended* on a claim, which needs the read path instrumented. The cheap version tests
  a claim when it is read by a binding computation, and that is where this should start.
* **Retroactive collapse.** If a claim is adopted in chapter nine and three earlier scenes are
  inconsistent with it, the log is append-only (hard rule 2) and cannot be rewritten. The
  continuity-critic surfaces the conflict; the cutting room resolves it in the prose. The DB records
  that the world changed its mind, which is the truthful thing to record.
* **Who speaks binds nothing, but who speaks matters.** A king's offhand claim and a beggar's are
  both T2 under this model. Whether authority should bias resolution is undecided and deliberately
  so — it is a story question, and the keeper is the right place to hold it.
