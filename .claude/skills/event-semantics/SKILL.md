---
name: event-semantics
description: The recorder's craft toolbox — how a beat of simulation becomes accurate, typed, auditable events (design.md's consolidation, LLM call 3, the keystone). Covers event representation (Davidsonian event semantics, aspect/Aktionsart, temporal & causal ordering, TimeML, Allen's interval algebra), semantic frames & thematic roles (FrameNet, PropBank, VerbNet, AMR, Dowty's proto-roles, case grammar), speech-act theory (Austin, Searle, illocutionary force, Grice, dialogue acts, the illocution-not-perlocution wall, the recorded lie), narrative event models (story grammars, scripts, Lehnert's plot units, Chambers–Jurafsky narrative chains, Story Intention Graphs, fabula/syuzhet), the appraisal-linked event vocabulary (harm/aid/betray/reveal/acquire/bond/threaten and its {act,target,instrument,intent,stance} tag), event extraction (ACE/ERE triggers+arguments, OpenIE, SRL, LLM structured output, self-report vs mining), typed schemas & actor self-report (closed vocabularies, JSON-schema contracts, containment & capability validation), and provenance/confidence/verification (W3C PROV, inter-annotator agreement, calibration & abstention, round-trip/ground-truth tests, event sourcing & compensating events). Open it to shape an event, record what was said as an act, chain events into a biography, pick from the schema, validate a self-reported tag, or score a record's provenance and confidence. Framework-neutral — a well of peers, not one prescribed truth.
---

# Event Semantics — the recorder's craft well

This is the toolbox the **`recorder`** agent draws on while it works. The agent is the *will* (turn a beat's `{thought, action}` stream into accurate typed events; validate the actor's self-report; extract facts, never deltas; never read another's mind); this skill is the *well* — the frameworks, menus, and exemplars it reaches into to record faithfully.

**It holds craft, never facts.** How to shape an event, name its roles, record a speech act, pick from the vocabulary, or score a record's confidence lives here. *What* happened in the beat, *who* is present, and *which* schema is in force reach the recorder through its context — the live stream, the PerceptSet, the schema — never through this toolbox.

**Why this toolbox exists — the keystone.** Consolidation is the one error class that **compounds** (`docs/consolidation-loop.md`): a mis-record propagates through appraisal → state → the next turn → the biography → the book. "Faithfulness by construction" *is* recording accuracy. So this well is deep and its disciplines are hard: the recorder is a **validator** of the doer's self-report, not an interpreter mining prose; it reads the **live stream**, never the dramatized narration; it emits **events**, never the numbers the engine computes; and every record carries **provenance and a confidence**, with ambiguity flagged, never silently committed.

**Framework-neutral and open.** There is no one true event ontology. Every framework below is a peer in a well, not a rung on a ladder; where this project names a default (the appraisal-linked vocabulary, the five-slot tag) it is a **reference point, marked swappable**, not a rule. A fork replaces one reference file and inherits the rest. The canon these files digest lives in `docs/` (once) — `consolidation-loop.md`, `recording-model.md`, `design.md` (LLM call 3 + the one-way arrow), `state-engine.md`; if a reference and its doc disagree, the doc wins.

## How this toolbox is organized
The deep material lives in `references/`, one file per framework-cluster, grouped by the altitude of the problem. **This `SKILL.md` is the router** — it indexes what each file holds and when to pull it. Read the router to find the one file the moment needs; read that file; skip the rest. (The deep reference files are authored in a **later pass** — see `references/_index.md` for their outlines. The index below is the map they fill in.)

**A missing reference file is not a stall condition.** Entries not yet authored have no file on disk; when the router sends you to one that's missing, act on this index's own one-line summary for that entry and proceed — never stall on, or invent, the file.

---

## The index — what lives where

### A. What an event IS — representation and roles

**`references/event-representation.md`** — *the anatomy of an event; load when deciding what counts as one event, how to bound it, and how it sits in time and cause.*
- **Davidsonian event semantics** — events as first-class entities (variables) a sentence quantifies over; "who did what" is predication over an event.
- **Neo-Davidsonian representation (Parsons)** — the event plus separate thematic-role predicates (`Agent(e,x)`, `Theme(e,y)`); the logical shape the project's five-slot tag compresses.
- **Vendler's aspectual classes (Aktionsart)** — states / activities / accomplishments / achievements, split by *telic vs atelic* and *dynamic vs stative*; tells you whether a stretch of stream is one bounded event or an ongoing process.
- **Telicity & boundedness** — does the event have an inherent endpoint? The test for "did it *happen* (record it) or is it *going on* (a condition)."
- **The event vs state (condition) distinction** — events *fire once and leave a trace* (appraisal → a delta); conditions *persist while true* (the catalog → a multiplier). The recorder emits verbs, not standing states (`docs/state-engine.md`).
- **Reichenbach's tense structure** — speech-time / event-time / reference-time; the grounding for ordering a recorded event against "now."
- **Situation & event calculus (McCarthy & Hayes; Kowalski & Sergot)** — formal accounts of events changing fluents over time; the logic behind "this act updates that state."
- **Fluents vs events** — the changing facts a world holds (fluents) vs the acts that change them (events); the ledger's snapshot-vs-log split, in logic.
- **TimeML (EVENT / TIMEX3 / SIGNAL / TLINK)** — the ISO standard for marking events, times, and their links in text; the working vocabulary for temporal annotation.
- **Allen's interval algebra** — the 13 exhaustive relations between two intervals (before, meets, overlaps, during, starts, finishes, equals, and inverses); the calculus for ordering events without exact clocks.
- **Causal ordering (ENABLE / CAUSE / PREVENT)** — the causal links between events that a biography needs beyond mere sequence; distinguished from temporal order.
- **Event coreference** — deciding when two mentions are the *same* event (vs two events); the deduplication that keeps a log from double-counting one act.
- **The five Ws** — who / what / when / where / why; the journalist's checklist that maps onto the ledger's `{what · who · when · where · consequence}` event record.

**`references/semantic-roles-and-frames.md`** — *the slots an event fills; load when assigning `target` / `instrument` / participants, or deciding which role a referent plays.*
- **Thematic (theta) roles** — agent, patient/theme, experiencer, instrument, goal, source, beneficiary, recipient, location, stimulus, force; the standard inventory of *who plays what* in an event.
- **Fillmore's case grammar** — the original deep cases (Agentive, Instrumental, Dative, Objective, Factitive, Locative); the ancestor of thematic-role theory.
- **Dowty's proto-roles** — Proto-Agent vs Proto-Patient as *clusters of entailments* (volition, sentience, causation, movement / change, affectedness, stationariness), not discrete labels; the fix for "is this really an agent?" edge cases.
- **Frame semantics & FrameNet (Fillmore)** — a word evokes a *frame* (a scenario) with *frame elements* (core / peripheral / extrathematic) and *lexical units*; the richest map of "what participants a given kind of event implies." (1,200+ frames, 13,000+ LUs.)
- **PropBank** — predicate-argument annotation with verb-specific numbered roles (Arg0–Arg5) plus modifiers (ArgM-TMP, -LOC, -MNR…); the workhorse for shallow semantic roles.
- **VerbNet & Levin's verb classes** — English verbs grouped by shared syntax + semantics and *diathesis alternations* (the same event, different framings: "A gave B the vial" / "A gave the vial to B"); how one act surfaces many ways.
- **Semantic Role Labeling (SRL)** — the NLP task of tagging who-did-what-to-whom-where-when; the automatic face of the above.
- **Abstract Meaning Representation (AMR)** — whole-sentence meaning as a rooted directed graph over PropBank frames; "who did what to whom" abstracted away from syntax.
- **Generative Lexicon & qualia (Pustejovsky)** — a word's meaning as structured roles (constitutive, formal, telic, agentive); why "instrument" carries purpose, not just a noun.
- **The project's five-slot tag** — `{ act, target, instrument, intent, stance }` as a deliberately compressed frame: act = the frame, target/instrument = core elements, intent/stance = the actor's self-reported interior. What it keeps and what it drops, and why.

### B. Special kinds of event that matter here

**`references/speech-acts-and-dialogue.md`** — *recording what was SAID as an act; load whenever a turn is dialogue, a promise, a threat, or a lie.*
- **Austin's three acts** — locutionary (the words said), illocutionary (the act performed *in* saying — promising, warning), perlocutionary (the effect *on the hearer* — convincing, frightening); the single most load-bearing split for a recorder.
- **The illocution-not-perlocution wall** — you record the **illocution** (what the speaker *did*: "A threatened B"), never the **perlocution** (whether B was cowed) — exactly the character-simulator's "report intent, never effect," and the engine-resolves-outcomes line.
- **Performatives vs constatives & felicity conditions** — utterances that *do* vs *describe*; the conditions under which a speech act succeeds (authority, sincerity, uptake) — what makes "I dub thee" work or misfire.
- **Searle's five illocutionary classes** — assertives, directives, commissives, expressives, declarations; classified by *illocutionary point*, *direction of fit*, and *expressed psychological state*. The taxonomy that types a line of dialogue as an act.
- **Illocutionary force & IFIDs** — the force (order vs request vs plead) beyond propositional content, and the devices that signal it; why *how* a thing was said is part of the event.
- **Grice's cooperative principle & implicature** — the maxims (Quality, Quantity, Relation, Manner) and what a speaker *means beyond what they say*, especially by *flouting* a maxim; the gap between literal content and communicated act.
- **Indirect speech acts** — "Can you pass the salt?" as a request, not a question; the recorder must tag the act *performed*, not the surface form.
- **Dialogue-act taxonomies** — DAMSL / SWBD-DAMSL, DIT++, and the ISO 24617-2 / DiAML standard (nine dimensions, general-purpose + dimension-specific functions); ready inventories for typing conversational moves.
- **Conversation analysis** — adjacency pairs, turn-taking, and repair (Sacks/Schegloff/Jefferson); the structure of exchange that tells you where one speech event ends and the response begins.
- **Politeness & face (Brown & Levinson)** — face-threatening acts and redress; the bridge from *how* something was said to the honor/dignity/face stakes the appraisal reads.
- **The recorded lie** — a lie is `thought ≠ stated action`, preserved as both; the illocution is an assertive, the interior contradicts it, and the gap *is* the deception in the record (`docs/recording-model.md`) — never collapsed.

**`references/narrative-event-models.md`** — *how events chain into a biography; load when relating events across a scene, or checking the log reads as a coherent history.*
- **Story grammars (Rumelhart; Mandler & Johnson; Thorndyke)** — rewrite-rule grammars of well-formed stories: setting + episode (initiating event → reaction → goal → attempt → outcome → resolution), linked by AND / THEN / CAUSE; the structural expectation a coherent chronicle meets.
- **Propp's morphology of the folktale** — 31 recurring *functions* (acts defined by their role in the plot) and 7 dramatis-personae; an early closed inventory of narratively-typed events.
- **Schank & Abelson: scripts, plans, goals, themes** — stereotyped event sequences (the restaurant script), and the plan/goal structure beneath novel action; how expected events can be inferred and unexpected ones flagged.
- **Conceptual Dependency & the primitive ACTs (Schank)** — the eleven canonical primitives (ATRANS, PTRANS, MTRANS, MBUILD, PROPEL, MOVE, GRASP, INGEST, EXPEL, SPEAK, ATTEND); the founding argument that *all* action reduces to a small closed set — the ancestor of a bounded event vocabulary.
- **Lehnert's plot units** — narrative as configurations of *affect states* (positive / negative / mental) linked by motivation, actualization, termination, and cross-character causal links; events typed by their emotional/causal role (kin to the appraisal-linked vocabulary).
- **Chambers & Jurafsky narrative event chains & schemas** — statistically-learned sequences of events sharing a protagonist, evaluated by the *narrative cloze* test; the modern, data-driven descendant of scripts.
- **Story Intention Graphs (Elson; Scheherazade; DramaBank)** — a corpus-grade encoding of narrative as goals, plans, affectual impact, and time; a rigorous scheme for annotating agency and intention in a story.
- **Fabula vs syuzhet / story vs discourse (Formalists; Chatman; Genette)** — the *events as they happened* vs *the telling*; the recorder builds the **fabula** (the biography substrate), the narrator renders the **syuzhet** — the one-way arrow, in narratology's own terms.
- **Barthes' functions** — cardinal functions (nuclei — the load-bearing events) vs catalysers (fillers), plus indices; which recorded acts are hinges and which are texture.

**`references/the-appraisal-event-vocabulary.md`** — *the project's own bounded schema and its lineage; load to pick the right `act`, or to check whether a turn needs a type the schema lacks.*
- **The house vocabulary** — the appraisal-linked core (**harm · aid · betray · reveal · acquire-knowledge · bond · threaten · relationship-act**) plus the physical/social affordances (**speak · move · give · take/acquire · conceal · submit · defy · observe**); the closed set the recorder picks from (`docs/consolidation-loop.md`).
- **The five-slot tag** — `{ act, target, instrument, intent, stance }`: the act typed from the vocabulary; target/instrument contained in the PerceptSet; intent/stance the actor's self-report.
- **Why bounded (the three payoffs)** — a closed vocabulary is machine-**validatable** (conforms?), directly **appraisable** (each type → appraisal dimensions → primaries), and a stable **contract** between the sim and the engine (schema-is-primary). Open extraction buys none of these.
- **Act → appraisal mapping** — how each event-type feeds the appraisal dimensions (goal-congruence, agency, certainty, control, norm/value-violation) that move the Panksepp primaries (SEEKING/FEAR/RAGE/CARE/PANIC-GRIEF/LUST/PLAY) — the interface the recorder must serve without computing (`docs/state-engine.md`).
- **The event-vs-condition boundary** — verbs the recorder logs (attacked, insulted, bereaved) vs standing conditions the catalog handles (ally-present, exhausted); the rule that keeps appraisal and the catalog from double-counting.
- **Closed-inventory lineage** — Schank's CD primitives, Propp's functions, Lehnert's affect states, Roget/FrameNet hierarchies: the tradition of reducing action to a small typed set, and what each teaches about where to cut the vocabulary.
- **Schema gaps & extension** — what to do when a turn resists the vocabulary: decompose into schema acts, or flag for the critic to rule on a genuine gap — never mint a type at record-time.
- **Vocabulary granularity** — resolve an act to the coarseness the book levers on (the depth rule): `harm` by default, `harm-with-a-blade-to-the-hand` only at a hinge that turns on it.

### C. The extraction task and its discipline

**`references/event-extraction.md`** — *the method of getting events out of the stream; load for the how-to of trigger, argument, and the self-report-vs-mine distinction.*
- **Trigger + argument extraction** — the canonical event-extraction shape: detect the *trigger* (the word/act that anchors the event), then label its *arguments* (participants + their roles); the task the recorder performs when the actor didn't self-report.
- **MUC template filling** — the ancestor: filling slots in a predefined template from text; where event extraction as a task began.
- **ACE 2005 ontology** — 8 event types / 33 subtypes / 22 argument roles (Life, Movement, Transaction, Business, Conflict, Contact, Personnel, Justice); the most-used worked example of a typed event ontology — a model for the project's own.
- **ERE (Light / Rich) & later corpora (RED, MAVEN, DocEE)** — successor ontologies that widen coverage and add cross-sentence/document events; the state of the practice.
- **Open Information Extraction (OpenIE)** — schema-free `(subject, relation, object)` triples; the *opposite* pole from a bounded schema — useful to know as the road the project deliberately does **not** take, and why.
- **Semantic parsing** — text → a formal logical form/meaning representation; the deepest version of extraction.
- **Prerequisites: NER, coreference, relation extraction** — resolving *who/what* a mention refers to before an event can be assembled; why coreference is load-bearing for containment.
- **Cross-document / cross-turn event coreference** — linking the same event across mentions and turns; keeping one act from becoming three log entries.
- **Temporal & causal relation extraction (CATENA; Causal-TimeBank)** — recovering the TLINKs and causal links between events; the ordering layer over bare extraction.
- **LLM structured extraction** — function-calling / constrained decoding / JSON-schema-guided output; the modern method, and why it pairs with *validation* rather than replacing it (the model can still hallucinate a referent — hence containment).
- **Self-report vs mining** — the project's keystone move: the actor emits the tag in its own pass (it *knows* its intent) and the recorder *validates* (cheap, high-fidelity); mining intent from prose afterward is *guessing* (expensive, lossy). The whole extraction posture flips from interpreter to validator.
- **Evaluation** — trigger-detection and argument-role precision/recall/F1; how an extractor is scored, and what "good enough to enter state" means.

**`references/typed-schemas-and-self-report.md`** — *the contract and who fills it; load when validating a tag, or reasoning about schema design and the recording split.*
- **Closed vs open vocabularies** — the trade: a closed schema is validatable, appraisable, and stable but can have gaps; an open one is flexible but un-checkable. Why this project chooses closed (the three payoffs).
- **Controlled vocabularies, ontologies, taxonomies (SKOS)** — the discipline of a fixed, defined term-set with relations; the shape the event vocabulary is.
- **JSON Schema & typed structured output** — enum-constrained fields, required slots, well-formedness; the machine-checkable form of "the tag conforms."
- **Design by contract (Meyer)** — the schema as the *interface* between two components (sim ↔ engine), with obligations on each side; why "schema-is-primary" is an engineering stance, not a preference.
- **The actor-records principle** — self-report is high-fidelity because the doer knows its own intent; third-party annotation of intent is inference. The reliability argument for who records what (`docs/consolidation-loop.md` Principle 1).
- **Nobody records another's mind** — each character records its own action + interior; cross-character effects flow through *perception* only. The POV wall that deletes the "observer guessing" error class (Principle 2).
- **The three validation checks** — schema-conformance (act ∈ vocabulary), containment (every referent ∈ PerceptSet), capability (the actor could do it, in-skill/in-reach); the mechanical gate every tag passes.
- **Referential grounding** — every `target`/`instrument` must resolve to a known entity in the scene; the anti-hallucination check, and why coreference feeds it.
- **Event-schema induction** — learning a schema from data (Chambers narrative schemas; event-schema induction) vs authoring one; the fork's option for growing the vocabulary principledly.

### D. Trusting the record

**`references/provenance-confidence-and-verification.md`** — *making the record auditable and measured, not trusted; load to score a record, flag a doubt, or set up the tests.*
- **Provenance (W3C PROV)** — Entity / Activity / Agent and the relations `wasGeneratedBy`, `wasDerivedFrom`, `wasAttributedTo`, `used`; the standard model for "where did this record come from," applied to tying each event to its stream span.
- **Data lineage & the source span** — every event points back to the `{thought, action}` span it rests on; a record with no source is a hallucination and does not ship.
- **Confidence scoring & calibration** — verbalized confidence, logprob/sequence-probability signals, and calibration (ECE) — is a stated "high" actually reliable? The basis for an honest per-event confidence.
- **Selective prediction & abstention** — knowing *when to defer*; the recorder's rule that no low-confidence record enters state without escalation — abstention as a feature, not a failure.
- **Escalation thresholds** — where the low-confidence line sits and what crossing it triggers (route to the critic); the human/critic-in-the-loop handoff.
- **Inter-annotator agreement (Cohen's κ, Fleiss' κ, Krippendorff's α)** — how consistency between independent annotators is measured, and the acceptable-reliability thresholds; the theory behind cross-extractor agreement.
- **Cross-extractor ensembles** — N independent recorders on one turn; disagreement = ambiguity → flag low-confidence rather than silently pick one (`docs/consolidation-loop.md` Principle 4).
- **Ground-truth replay** — author a scene with a *known* event-set and assert recorded == known; the recorder's unit test.
- **Round-trip / reconstruction** — rebuild a description from the recorded events; if it loses what the stream had, the recording is *lossy* → tighten the schema. The information-preservation test.
- **The coherence probe** — over N turns, does state stay coupled to narrative? Accumulating divergence = recording errors compounding; the integration test (`docs/probe-plan.md`).
- **Faithfulness & attribution (AIS; groundedness)** — the "attributable to identified sources" standard for extraction; measuring hallucination in what was recorded.
- **Event sourcing & compensating events** — an append-only, immutable log corrected only by a *compensating event* (the Saga/reversal pattern), never a silent mutation or delete; the forward-only correction protocol.
- **The read-only critic backstop** — the consistency critic (`docs/design.md` layer 6) that checks `{events + new state}` against prose, prior state, and world rules, and flags or issues a compensating event — never rewrites in place.

### E. The house method

**`references/the-prose-event-contract.md`** — *THE load-bearing reference: the seam between prose and structured events. Load on every consolidation decision. Canon-linked to `design.md`, `consolidation-loop.md`, `recording-model.md`, `state-engine.md`.*
- **The one-way arrow** — `stream → events → state` is the live in-sim loop; `biography → narration → prose` is a terminal, selected, dramatized, POV-bounded output. The arrows never cross.
- **Read the stream, never the narration** — consolidating the dramatized prose would let the telling rewrite the canonical biography — *forcing, at the state level*. The prose is checked against the biography (read-only critic); it never writes it.
- **Extract events, never deltas** — the recorder reports *what happened*; the engine's appraisal computes the numbers. The seam: *stream → events* is the LLM (interpret language); *events → numbers* is the engine (compute state). A recorder that emits a feeling or a value has crossed it.
- **Illocution, not perlocution** — record the act performed, never its effect on anyone; the speech-act form of "report intent, never effect."
- **Validate the self-report, don't mine it** — the doer labeled its deed; the recorder confirms (validator), and completes only the perception/learning gap. Interpreter → validator is the accuracy win (Principle 1).
- **Nobody records another's mind** — cross-character effects flow through perception; A's intent is A's record, B's read of A is B's (Principle 2).
- **The bounded typed vocabulary** — pick from the schema, never invent; it is what makes events validatable, appraisable, and a stable contract (Principle 3).
- **Measured, not trusted** — provenance + confidence on every record; ambiguity flagged, never silently committed; accuracy *verified*, not assumed (Principle 4).
- **Lossy vs lossless** — the round-trip test as the standing check that the schema keeps what the stream had.
- **The compounding-error argument** — why this role is the keystone: a local error stays local, a recording error propagates to state, the next turn, the biography, and the book. Recording accuracy *is* faithfulness by construction.

---

## How to use this well — the method
1. **Read the stream, and only the stream.** Consolidate the recorded `{thought, action}` — never the narrated prose. If what you're reading is dramatized POV output, you're on the wrong side of the one-way arrow (*the-prose-event-contract*).
2. **Start from the self-report.** The actor already tagged its deed. Your first job is to **validate**, not re-derive: schema-conformance, containment, capability (*typed-schemas-and-self-report*). Accept, reject, or flag — never silently repair.
3. **Complete only the gap.** Add what the actor couldn't report: what a *present* character perceived or learned, recorded from *their* stream (*speech-acts-and-dialogue* for said-acts; *event-extraction* for the how). Never infer another's interior.
4. **Type every event from the schema.** Pull the right `act` from the bounded vocabulary; fill the slots with contained referents (*the-appraisal-event-vocabulary*, *semantic-roles-and-frames*). If a turn resists the schema, decompose or flag — never mint a type.
5. **Bound it and place it in time.** Decide what is one event vs a process vs a standing condition; order it against its neighbors (*event-representation*). A condition is not an event; log the verb, not the state.
6. **Stop at the wall.** Record *what happened* — never the delta, the emotion, the trust change, or "who won" (*the-prose-event-contract*). The engine appraises; you don't.
7. **Attach provenance and a confidence.** Point each event at its stream span; rate your certainty honestly. Low-confidence or ambiguous → flag and escalate to the critic, never into state (*provenance-confidence-and-verification*).
8. **Correct forward.** A record caught wrong after append is reversed by a compensating event, never mutated or deleted. The log only ever adds.

## Status
Router + index complete. The deep reference files are authored in a **later pass**; their outlines and the canon each digests are in `references/_index.md`. Until then, this index plus the `docs/` canon it points at is the working map. Nothing here is prescriptive: it is a well to draw from, framework-neutral, holding rival schemes side by side so the record — not the toolbox — is what must be true.
