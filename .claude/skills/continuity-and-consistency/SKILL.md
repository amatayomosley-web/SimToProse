---
name: continuity-and-consistency
description: The continuity-critic's craft toolbox — how to validate a canonized scene against the World Bible + world-state ledger before it becomes canon (design.md's layer-6 critic gate, the no-contradiction floor). Covers canon & continuity management (story/series bibles, the ledger as living canon, canon/fanon/Word of God, retcon, sliding timescale, groundedness-as-retrieval), a taxonomy of contradictions (fact/timeline/spatial/character/causal/tonal/voice/rule, anchored to Zwaan's event-indexing dimensions and de Marneffe's contradiction typology), timeline reasoning (Allen's interval algebra, point algebra, temporal constraint networks, TimeML, travel-time feasibility), spatial reasoning (RCC-8, cardinal-direction calculus, the 180-degree rule/screen direction, spatial situation models, reachability), character & knowledge consistency (persona consistency, Dialogue NLI, out-of-character/Flanderization, the vault/knowledge check, dramatic irony vs the knowledge break), voice-consistency detection (stylometry, Burrows's Delta, function words, Mosteller-Wallace, distinct-idiom detection, the voice-collapse failure), checking a scene against a bible/ledger (integrity constraints/SHACL, ontology reasoners, NLI/entailment contradiction detection, FEVER claim-decomposition, groundedness/faithfulness), the flag-vs-correct policy (event sourcing, compensating events, the Saga pattern, never silent mutation, the remedy ladder, abstention), and the classic continuity-error patterns of long-form fiction (the movable wound, continuity snarl, plot hole, mood whiplash, Flanderization, dropped threads, LLM long-story consistency bugs). Open it to name a contradiction and route it, settle a timeline or spatial feasibility, check a scene against canon, tell a voice-collapse from a distinct idiom, or correct a bad record forward. Framework-neutral — a well of peers, not one prescribed truth.
triggers:
  keywords:
    - retcon
    - stylometry
    - contradiction
  concepts:
    - check continuity
    - does this contradict
    - against the bible
    - timeline error
    - out of character
    - voice drift
    - validate the scene
---

# Continuity & Consistency — the critic's craft well

This is the toolbox the **`continuity-critic`** agent draws on while it works. The agent is the *will* (gate each canonized scene against bible + ledger; flag contradictions, never rewrite; correct forward by compensating events, never mutate; never confuse a faithful surprise or a recorded lie with an error); this skill is the *well* — the taxonomies, calculi, and exemplars it reaches into to check faithfully.

**It holds craft, never facts.** How to name a contradiction, route it to the engine or to judgment, settle a timeline with interval algebra, check a scene against a knowledge base, tell a collapsed voice from a distinct one, or correct a bad record forward lives here. *What* is canon in this book — the laws, the established facts, who is where, who knows what — reaches the critic through its context (the bible slice, the ledger slice, the events, the stream), never through this toolbox.

**Why this toolbox exists — the no-contradiction floor.** The critic is design.md's layer-6 gate: it validates each canonized scene against bible + ledger (no rule violation, no contradiction, distinct voices) *before* the event joins the append-only ledger (`docs/world-state-ledger.md`: the no-contradiction floor, enforced at write time). It is the recorder's backstop — low-confidence records escalate here (`docs/consolidation-loop.md`) — and the second half of the keystone loop. So its disciplines are hard: it is a **non-author** (it flags, others fix); it is **hybrid** (contradiction-against-ledger is engine, distinct-voice/tone is LLM); it corrects **forward** by compensating events, never by silent mutation; and it is precise — a **faithful refusal, a recorded lie, and earned growth are not contradictions.**

**Framework-neutral and open.** There is no one true theory of contradiction or one true continuity practice. Every framework below is a peer in a well, not a rung on a ladder; where this project names a default (the hybrid gate, the compensating-event correction, the house taxonomy) it is a **reference point, marked swappable**, not a rule. A fork replaces one reference file and inherits the rest. The canon these files digest lives in `docs/` (once) — `design.md` (layer-6 critic + the one-way arrow + the compute/generate split), `world-state-ledger.md` (the immutable log + the continuity gate), `consolidation-loop.md` (the consistency critic + compensating events + measured-not-trusted), `knowledge-model.md` (the vault), `narration.md` (the distinct-voice/tone check), `probe-plan.md` (the coherence probe); if a reference and its doc disagree, the doc wins.

## How this toolbox is organized
The deep material lives in `references/`, one file per framework-cluster, grouped by the critic's working path: *what canon is → what can break it → how each break is decided → how the whole scene is checked → what to do with a catch → the catalogue → the house method.* **This `SKILL.md` is the router** — it indexes what each file holds and when to pull it. Read the router to find the one file the moment needs; read that file; skip the rest. (The deep reference files are authored in a **later pass** — see `references/_index.md` for their outlines. The index below is the map they fill in.)

**A missing reference file is not a stall condition.** Entries not yet authored have no file on disk; when the router sends you to one that's missing, act on this index's own one-line summary for that entry and proceed — never stall on, or invent, the file.

---

## The index — what lives where

### A. What canon IS — the ground truth being defended

**`references/canon-and-continuity.md`** — *the object of the check; load when reasoning about what "canon" means here and how it is tracked at scale.*
- **Canon (fiction)** — the body of material accepted as true within a fictional world; the ground truth continuity defends. Its origin in the Sherlockian corpus and the biblical sense.
- **The story / series / show bible** — the authoritative reference of characters, settings, world-rules, timeline, and open threads; the writers'-room continuity guide, and the analog of this project's World Bible.
- **The world-state ledger as living canon** — the project's append-only event log + folded snapshot *is* the canon of record: the bible fixes the *rules*, the ledger holds the *history* (`docs/world-state-ledger.md`). Continuity is consistency of history, not just of rules.
- **Canon vs fanon vs headcanon vs Word of God** — degrees of authority over "what's true," and who holds them; the author-pronouncement ("Word of God") and its limits.
- **Retcon (retroactive continuity)** — a later work adjusts, supplements, or contradicts an established fact; a *controlled* canon operation when logged and intended, a break when accidental.
- **Canon discontinuity / negative continuity / soft vs hard canon** — declaring prior events "never happened"; serials where nothing persists; tiers of how binding a fact is.
- **The sliding timescale / floating timeline** — long serials that hold characters ageless against a moving present; a deliberately managed inconsistency, not an error.
- **Continuity databases & fan wikis (Memory Alpha, Wookieepedia; the "continuity cop")** — how large franchises actually track canon at scale: a searchable, growing corpus queried before each new work. Groundedness as retrieval, in the wild.
- **Continuity vs consistency** — continuity = agreement across the surface of the telling (the same coat, the same scar); consistency = agreement with the world's rules and internal logic. Two distinct checks the gate runs together.
- **Groundedness is a retrieval problem (design.md)** — at book scale the bible exceeds the context window; consistency is *not* an automatic property but a retrieval-then-check. The critic's founding premise, and its subtlest failure (a missed retrieval reads as a false pass).

### B. The taxonomy — what can break

**`references/contradiction-taxonomy.md`** — *the master map of contradiction classes; the toolbox's center of gravity. Load to name a contradiction and route it to the engine or to judgment.*
- **The event-indexing model (Zwaan, Langston & Graesser 1995)** — readers track five dimensions of a situation — **time, space, protagonist/entity, causation, intentionality** — and a discontinuity on any one measurably spikes reading time. The cognitive backbone: the reader *feels* a break on exactly these axes, which is why they are the axes to check.
- **The de Marneffe, Rafferty & Manning (2008) contradiction typology** — seven linguistic types: **antonymy, negation, numeric mismatch, factive/modal, structural (argument reversal), lexical, world-knowledge** — split into the easily-detectable (the first cluster) and those needing deep inference (lexical, world-knowledge). The NLP-side anatomy of a fact contradiction.
- **The definition of contradiction & event coreference** — two claims contradict when they *cannot both hold of the same situation*; the check first requires **event coreference** (are they even about the same event?) — the guard against flagging two compatible statements as a clash.
- **The house taxonomy** — the project's working classes — **fact · timeline · spatial · character/knowledge · causal · tonal · voice · rule** — each mapped onto Zwaan's dimensions and de Marneffe's types, each tagged with who decides it (engine vs critic).
- **Fact contradiction** — a claim negating an established fact: name, number, property, appearance (the antonymy/negation/numeric core).
- **Timeline contradiction** — an ordering or duration impossibility; anachronism; effect-before-cause (→ *timeline-reasoning*).
- **Spatial contradiction** — a geometry, reachability, or screen-direction break (→ *spatial-reasoning*).
- **Character / knowledge contradiction** — an out-of-character act, or an act on knowledge the vault lacks (→ *character-and-knowledge-consistency*).
- **Causal contradiction** — an effect with no recorded cause, or an established cause whose effect is missing; the plot hole's engine.
- **Tonal contradiction** — an unearned register snap (mood whiplash); tone that violates the scene's own set-up.
- **Voice contradiction** — collapsed idioms, or a character speaking against their sheet's diction (→ *voice-consistency*).
- **Rule / law contradiction** — a violation of the world's physics, magic-cost, economy, or social law as the bible fixes them.
- **Contradiction vs surprise vs lie — the false-positive discipline** — an unexpected-but-faithful act, an earned character arc, and a recorded thought≠action lie are **not** contradictions; the taxonomy screens beat-*vs-canon*, never the honest divergence *within* a beat.
- **Severity & blockingness** — which contradictions block canon and which are cosmetic; the depth rule (hinge vs tail) applied to error triage, so the gate spends effort where the book levers.

### C. The reasoning engines — how each break is decided

**`references/timeline-reasoning.md`** — *settling an ordering or duration; load on any temporal or anachronism check.*
- **Allen's interval algebra (1983)** — the 13 exhaustive, pairwise-disjoint relations between two intervals (before, meets, overlaps, starts, during, finishes, equals + inverses); the calculus for ordering events without exact clocks.
- **Point algebra (Vilain & Kautz)** — the simpler <, =, > calculus over time points; tractable where the full interval algebra is NP-complete.
- **Temporal constraint networks (TCSP / STP; Dechter, Meiri & Pearl)** — quantitative constraints over durations and distances; the machinery for "is there enough time to travel between?"
- **Composition tables & path-consistency** — propagating interval constraints to expose an impossible ordering; the mechanical detector for a timeline break.
- **Tractable subalgebras & NP-completeness** — the full algebra's satisfiability is NP-complete; the tractable fragments (e.g. ORD-Horn) that make real checks feasible.
- **TimeML / TLINK & timeline extraction** — annotating events, times, and their links; building the timeline the check runs over.
- **Reichenbach's tense structure** — speech / event / reference time; grounding a recorded event against "now."
- **The ledger clock & as-of-T slicing** — the project's own time spine: the clock gates what each vault could have learned; a timeline check is a query against it (`docs/world-state-ledger.md`, `docs/knowledge-model.md`).
- **Duration & travel-time feasibility** — the concrete book-scale check: given positions + a clock, could the character be here now? Resolve travel-time only at a hinge that turns on it (the depth rule).
- **Effect-before-cause / causal-temporal coupling** — the boundary where timeline meets causal: nothing may precede what enables it.

**`references/spatial-reasoning.md`** — *settling a geometry, reachability, or staging break; load on any spatial check.*
- **Region Connection Calculus (RCC-8)** — the 8 topological relations (DC, EC, PO, EQ, TPP, NTPP + inverses): is A inside / touching / disjoint from B? Co-location and containment checks.
- **Cardinal-direction calculus & the rectangle algebra** — N/S/E/W (and rectangle) relations; combining topology with direction for "who stands where relative to whom."
- **Qualitative spatial reasoning & path-consistency** — reasoning about space without coordinates; the tractable calculus a book's fuzzy geography actually supports.
- **Spatial situation models (Bower & Morrow 1990; Zwaan & Radvansky 1998)** — readers build and query a spatial mental map, tracking the protagonist's location and nearby objects; the reader catches a spatial break *because* they hold the map.
- **The 180-degree rule / axis of action & screen direction (script supervision)** — the film craft of keeping left/right, eyelines, and motion stable across cuts; the prose analog is who-faces-whom and who-stands-on-whose-side staying fixed.
- **Blocking & staging continuity** — where each body and prop sits and moves through a scene; the reach check (can the actor touch the instrument from where they stand?).
- **Reachability & line-of-sight (scene-assembly)** — the project's PerceptSet is already spatial: an act on an out-of-reach or unseen target is a spatial (and containment) break (`docs/scene-assembly.md`).
- **Mental maps & cognitive-map distortion** — how invented geography is remembered and misremembered; where spatial canon quietly drifts.
- **Map / floorplan invariance** — a place's fixed layout across scenes; the "room that changed shape" error, and the depth rule for space (a class-default "a tavern" until a scene turns on the exit's location).

**`references/character-and-knowledge-consistency.md`** — *deciding whether an act is in character and within what the character can know; load on a character or knowledge check.*
- **Persona consistency & the persona profile (PersonaChat)** — grounding a character in a fixed profile and holding behavior consistent with it; the dialogue-systems face of "stay in character."
- **Dialogue NLI (Welleck et al. 2019) & DECODE** — casting persona/utterance consistency as entailment vs neutral vs contradiction; the E/N/C ratio as a consistency metric, and contradiction detection across a dialogue history.
- **Characterization & the consistent character (Aristotle's *Poetics*; McKee)** — a character must be consistent (even if consistently inconsistent); the craft standard behind out-of-character detection.
- **Out-of-Character (OOC) & character derailment** — an act that violates the established self; the core character contradiction, and the line between it and earned change.
- **Flanderization** — a trait exaggerated over a serial until it consumes the character; the slow-drift failure a single-beat check misses (it needs the arc view).
- **Trait/value drift vs arc** — distinguishing unmotivated inconsistency from motivated growth (the arc-engine's earned change, `docs/arc-engine.md`); the discipline against flagging development as a break.
- **The vault / knowledge-consistency check (knowledge-model)** — a character can act only on what their vault holds; acting on unlearned information is the sharpest character break, and it is **computed** (vault membership), not judged (`docs/knowledge-model.md`).
- **Dramatic irony vs the knowledge break** — the reader knowing what the character doesn't is the *point*; the character knowing what they shouldn't is the *error*. The same asymmetry, two verdicts.
- **Motivation consistency & goal-tracking** — does the act serve a goal the character holds (Zwaan's intentionality dimension)? An unmotivated act reads as a break.
- **Capability & affordance** — could this actor do this here, in-skill and in-reach? The recorder's capability check re-run as a continuity gate.
- **Relationship-state consistency** — an act warm toward someone the ledger says they now hate, with no turn recorded between; a relationship contradiction (`docs/relationships.md`).

**`references/voice-consistency.md`** — *deciding whether voices stay distinct and true; load on a voice or diction check (the LLM half of the gate).*
- **Stylometry & the idiolect** — measurable, individual style; the premise that a voice is a fingerprint the critic can check.
- **Mosteller & Wallace (1964), the Federalist Papers** — the founding case: function-word frequencies settle disputed authorship; the proof that style is quantifiable.
- **Burrows's Delta (2002)** — the "gold-standard" distance over most-frequent-word z-scores; how far apart two voices are, numerically.
- **Function words as the signal** — short, high-frequency, topic-independent, grammaticalized words carry authorial style; why *they*, not content words, distinguish a voice.
- **Authorship verification vs attribution** — "are these two by the same hand?" (verification) is the critic's question: do two characters share one voice when they shouldn't, or does one character's voice hold across scenes?
- **Register, diction & idiolect/sociolect/dialect** — the craft face: lexical register (high/middle/low), Latinate vs Anglo-Saxon, sentence music; a character speaking against their sheet's diction.
- **Distinct-voice detection (the LLM half of the gate)** — design.md's "distinct-voice / tone is LLM": the irreducibly interpretive read that two minds have collapsed into one; no script decides it (`docs/design.md`, `docs/narration.md`).
- **The voice-collapse failure mode** — LLMs regress every character toward one fluent house style; the specific long-form pathology the critic guards against.
- **Character-n-gram, burstiness & richness features** — the wider stylometric feature space beyond function words; what a deeper voice-check could measure.
- **Verbal tics, catchphrases & lexical signatures** — deliberate per-character markers (a curse, a hedge, a cadence) whose presence or absence is a cheap voice check.
- **Voice as bounded by POV (narration)** — the narrator's voice is colored by the POV's vault; a "voice" break can be a POV-boundary leak, not merely a diction slip.

### D. The check — scene against bible/ledger

**`references/checking-against-canon.md`** — *the method of validating a whole beat against canon; load for the how-to of the scene-vs-bible/ledger check and its hybrid split.*
- **The scene-vs-canon check as knowledge-base validation** — the beat is a set of new claims; bible + ledger is the KB; the check is "does the KB stay consistent when these are added?"
- **Integrity constraints & closed-world validation (SHACL)** — constraints that must hold over concrete state; reject an update that violates one — the no-contradiction floor as an integrity constraint over the ledger's closed world.
- **Ontology / description-logic consistency checking (reasoners: Pellet, HermiT; tableaux)** — the open-world face: derive implicit facts, detect an unsatisfiable model; the world-rules half of the check.
- **Open-world vs closed-world assumption** — the bible's laws are open-world (infer what must follow); the ledger's state is closed-world (what isn't recorded didn't happen). Which assumption applies where, and why mixing them silently breaks the check.
- **Natural Language Inference / textual entailment (entail / neutral / contradict)** — the LLM-side detector: does the new claim contradict a retrieved canon fact? DeBERTa-style NLI over decomposed claims.
- **Claim decomposition & fact verification (FEVER)** — break the beat into atomic claims, retrieve evidence per claim, label supported / refuted / not-enough-info; the fact-verification pipeline shape.
- **Groundedness / faithfulness & attribution (AIS)** — every claim must be attributable to canon (or deliberately *added* as new canon); the RAG-faithfulness lens on "is this scene supported?"
- **Retrieval of the relevant slice** — at book scale the check is only as good as the canon slice retrieved; a missed retrieval reads as a false pass (design.md: groundedness is a retrieval problem).
- **Truth-maintenance systems (Doyle 1979; de Kleer's ATMS)** — tracking belief-dependencies so a retraction propagates; the classical-AI machinery behind "what else breaks if this is false."
- **The hybrid split at the check** — contradiction-against-a-stored-value → engine (integrity constraint / vault query); distinct-voice-and-tone → LLM (NLI / judgment). The seam that keeps the check honest and cheap (`docs/design.md`).
- **Self-consistency & cross-checking (SelfCheckGPT; cross-extractor agreement)** — sampling or independent checks to expose an unstable claim; ambiguity → flag, never a silent pass.
- **The one-way arrow at the check** — the narrated prose is checked *against* the biography, read-only; the check never lets the telling rewrite the record (`docs/design.md`).

### E. The policy — flag vs correct

**`references/flag-vs-correct.md`** — *what to do with a catch; load whenever deciding a remedy, and for the compensating-event protocol.*
- **The non-author stance** — the critic flags; it never authors the fix. Separating the checker from the writer is what makes the check trustworthy (design.md: "a non-author check").
- **Event sourcing & the append-only floor** — the log is immutable and only-adds; the structural reason silent mutation is *impossible*, not merely discouraged (`docs/world-state-ledger.md`).
- **Compensating events & the Saga pattern** — a wrong record is reversed by appending an inverse/correcting event, never edited or deleted; the forward-only correction protocol (`docs/consolidation-loop.md` open-Q #3).
- **Retcon as a controlled operation vs an accident** — a deliberate, logged canon revision (a compensating event with intent) versus an unnoticed contradiction; the same shape, opposite legitimacy.
- **The remedy ladder** — reject-and-regenerate (before append: re-run the beat) → director-revise (the beat itself was wrong) → compensating-event (after append: correct forward) → escalate (ambiguous: critic/human-in-the-loop). Which remedy fits which catch.
- **Never silent, never mutate** — the two prohibitions: a correction is always visible (an event on the log) and never destructive (no edit, no delete). The audit trail survives.
- **Flag-with-provenance & a remedy *class*** — a finding names the colliding pair and proposes a class of fix, not a patched line; the critic hands the fix to whoever owns it.
- **Selective prediction & abstention** — knowing when to defer: low-confidence or ambiguous → flag and escalate, never commit. Abstention is a feature, not a failure.
- **Confidence, calibration & the escalation threshold** — where the block / pass / escalate lines sit; an honest, calibrated confidence on the interpretive calls (`docs/consolidation-loop.md` open-Q #2).
- **Measured, not trusted — the coherence probe** — over N beats, does state stay coupled to narrative? Accumulating divergence = the gate is leaking; the integration test for the critic itself (`docs/probe-plan.md`).
- **The compounding-error asymmetry** — a false *pass* corrupts the floor every later beat builds on (unforgivable); a false *flag* costs only a regeneration (cheap). Bias accordingly.

### F. The catalogue and the house method

**`references/classic-continuity-errors.md`** — *the field guide of known long-form failures; load to pattern-match a suspected break against a named exemplar.*
- **The movable / floating fact** — Watson's wound migrating shoulder→leg from *A Study in Scarlet* to *The Sign of Four*; the canonical long-form fact-drift, and the "Great Game" impulse to rationalize it (never the critic's job).
- **Name & relation drift** — Watson's wife calling him "James," not "John"; a name or relation shifting between scenes; the cheapest, commonest break.
- **The Continuity Snarl** — accumulated changes that tangle a long serial into self-contradiction; the failure mode of an unmanaged canon at scale.
- **The Plot Hole** — a gap in internal logic: an unresolved detail, an effect with no origin, an established solution the characters inexplicably forget; the causal contradiction in the wild.
- **Negative continuity / the reset button** — a world where nothing sticks; state that should persist silently reverting — the ledger's exact opposite.
- **Mood Whiplash** — an unearned tonal snap; the tonal contradiction's exemplar.
- **Flanderization** — a trait amplified over a serial until it eats the character; the slow character-drift only an arc-scale check catches.
- **The dropped thread / Chekhov's gun unfired** — a setup with no payoff (a promised element abandoned), and its inverse, a payoff with no setup; the tension-ledger's job to track.
- **Off-screen teleportation & the resurrected object** — a character or object relocated or restored with no recorded transit or cause; the spatial/causal break.
- **The idiot ball & the out-of-character lapse** — a character acting against their established competence or self to serve a beat that can't otherwise reach; the character contradiction under plot pressure.
- **Conservation errors (the healing wound)** — injuries, resources, or scars that fail to persist their cost; state that should carry forward and doesn't.
- **Anachronism & era leakage** — a fact from the wrong time bleeding into the world; the timeline break at the world-rules layer.
- **Why these compound in long form (LLM long-story consistency bugs)** — the recent finding that generated long stories break most on *fact* and *temporal* dimensions, mid-narrative, in high-entropy spans; the empirical map of where to look first.

**`references/the-critic-gate.md`** — *THE load-bearing reference: the gate's whole philosophy. Load on every gating decision. Canon-linked to `design.md`, `world-state-ledger.md`, `consolidation-loop.md`, `narration.md`, `probe-plan.md`.*
- **The non-author gate (design.md layer 6)** — validate each canonized scene against bible + ledger: no rule violation, no contradiction, distinct voices; a check, never an author.
- **The no-contradiction floor at write time** — canon is admitted only on pass; the gate is *where* consistency is enforced, before the fold updates the snapshot (`docs/world-state-ledger.md`).
- **The hybrid engine/LLM split** — contradiction-against-ledger, timeline, spatial, knowledge, capability → engine (computed); distinct-voice, tone, out-of-character → LLM (judged). Compute what has a value; judge only what doesn't.
- **The one-way arrow** — check the `{thought, action}` stream as ground truth; check the narrated prose read-only *against* the biography; never let the telling write state (`docs/design.md`).
- **Flag, never fix; correct forward, never mutate** — the two policy walls, restated as the gate's identity (→ *flag-vs-correct*).
- **The false-positive discipline** — a faithful refusal, a recorded lie (thought≠action), and earned growth are **not** contradictions; precision is the gate's whole value (`docs/recording-model.md`).
- **Measured, not trusted** — provenance on every flag, calibrated confidence, ambiguity escalated; the coherence probe as the gate's own integration test (`docs/probe-plan.md`).
- **The compounding asymmetry** — a false pass corrupts every later beat (unforgivable); a false flag costs a regeneration (cheap); bias toward flagging the interpretive and computing the factual.
- **The critic as the recorder's backstop** — low-confidence records escalate here; the gate is the second half of the keystone consolidation loop (`docs/consolidation-loop.md`).
- **Groundedness is a retrieval problem** — the gate is only as good as the canon slice retrieved; a missed retrieval is a silent false pass, the gate's subtlest failure.

---

## How to use this well — the method
1. **Read the stream; check the prose read-only.** Gate the recorded `{thought, action}` and its events as ground truth. When you check the *narrated* prose, check it **against** the biography — read-only — never as the record (*the-critic-gate*).
2. **Name the contradiction, then route it.** Classify the suspected break on the house taxonomy — fact / timeline / spatial / character-knowledge / causal / tonal / voice / rule (*contradiction-taxonomy*) — and send it to whoever can decide it.
3. **Compute what has a value.** Contradiction against a stored fact, timeline feasibility (*timeline-reasoning*), spatial reachability (*spatial-reasoning*), vault-membership and capability (*character-and-knowledge-consistency*) — these are the engine's, deterministic. Do not argue a break you could have computed.
4. **Judge only the interpretive.** Distinct voice (*voice-consistency*), tonal coherence, and genuinely-out-of-character-vs-merely-surprising are your own reading — the LLM half of the gate. No script decides them.
5. **Check the whole beat against canon.** Decompose it into claims, retrieve the canon slice, test each claim for contradiction/entailment/groundedness (*checking-against-canon*). Remember: the check is only as good as the slice retrieved.
6. **Refuse the false positive.** A faithful refusal, an earned arc, and a recorded lie are not contradictions. Clear them explicitly; do not flag autonomy or honest divergence as inconsistency (*the-critic-gate*).
7. **Flag, never fix; correct forward.** Emit a finding with a cited colliding pair and a remedy *class* (reject+regenerate / director-revise / compensating-event / escalate) — never a rewrite. A bad record already appended is reversed by a compensating event, never a mutation (*flag-vs-correct*).
8. **Attach provenance and a confidence; escalate ambiguity.** Every flag names its established-fact ⟂ new-claim pair; rate your certainty; low-confidence or ambiguous → escalate, never a silent pass. A false pass is the one error that compounds.

## Status
Router + index complete. The deep reference files are authored in a **later pass**; their outlines and the canon each digests are in `references/_index.md`. Until then, this index plus the `docs/` canon it points at is the working map. Nothing here is prescriptive: it is a well to draw from, framework-neutral, holding rival schemes side by side so the *floor* — not the toolbox — is what must hold.
