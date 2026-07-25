# Knowledge & Injection Model (WORKING — the core problem)

A simulated character acts only on what is in its context. So the make-or-break is **what each character knows at the moment it decides** — not the prose, not the director.

## The inversion: the hard part is keeping the WRONG facts OUT
An LLM uses everything in its context. **Omniscience is the default failure** — dump the bible and the character "knows" it all. So injection is primarily **epistemic scoping**: deciding what each character does *not* get to see. It is subtractive as much as additive.

## Core principle: knowledge is ACQUIRED, not assumed
Every belief a character holds must trace to how they got it.

1. **World fact-base (ground truth)** — each fact tagged: entities/topic · when it became true · access class (public / station-gated / secret-held-by-{set}) · true value.
2. **Common-knowledge layers** — default belief sets by station / culture / locale / era. A character of type T knows these with no acquisition event ("the king rules from the capital").
3. **Per-character belief ledger** — acquisition events (witnessed / told / taught / deduced / assumed) → beliefs: {fact, value-as-THEY-believe-it, provenance, timestamp, confidence}. Supports **false / partial / uncertain** beliefs — characters act on *beliefs*, not facts, and that gap is where drama lives.
4. **Time index** — belief-set-as-of-T = common-knowledge(type) + acquisitions with timestamp ≤ T. Inject the **as-of-now slice**, never the future.
5. **Relevance retrieval (decision time)** — of their as-of-T beliefs, inject only the salient: (scene entities/topic ∩ beliefs) ∪ (goal-relevant) ∪ (recent/charged). Per-character RAG.
6. **The injection = the character's context** = scene + retrieved salient beliefs + persona/goals − everything past their epistemic horizon (no bible wholesale, no unacquired facts, no other minds, no director's beat).
7. **Acquisition during play** — when a character learns something in a scene, append an acquisition event → their ledger updates → future scenes reflect it. This is how information **flows through the cast**: A tells B → B knows → B acts → and A does not know B told C.

## The six questions
- **Logic for having info?** Acquired via a traceable channel, or common-knowledge of their type; held until forgotten. Provenance mandatory.
- **How much of the law?** Stratified by role: peasant knows the folk version (often wrong) of laws that touch them; a magistrate knows the code; a criminal knows the gaps. Partial + inaccurate by default.
- **When do they know it?** At/after the acquisition timestamp. Inject the as-of-T slice; never leak future knowledge.
- **What should they know?** common-knowledge(type) + their acquisitions, filtered to scene+goal relevance. Not their whole belief set; never the world's.
- **How decide relevance?** At decision time, by scene entities/topic + active goals (+ recency/emotion). Retrieval, not pre-loading.
- **Can we know what needs to be known?** No — not exhaustively, in advance. That is the frame problem ↓

## The frame problem — and why it does NOT sink the project
You cannot pre-enumerate every fact a character might need, because the sim is open-ended (the character may act in ways you didn't anticipate, needing a fact you didn't pre-load). So **stop trying to pre-know.** The design tolerates the gap:
- **Retrieve on demand, don't pre-load** — like an author consulting their own bible when a scene calls for it.
- **Query "what does X believe about Y?"** when the decision touches Y. If nothing, the character genuinely doesn't know — and acts on that (asks, guesses, errs). The gap is not a bug.
- **Gap-as-signal** — a needed-but-missing fact is either drama (acting on incomplete info) or a cue for the director to stage an acquisition event.
- **The bible grows from the sim** — you discover what must be authored by running it and watching what it reaches for. (Same shape as "you can't test a design you don't have.")

The viability condition: abandon omniscient pre-authoring; build for retrieve-on-demand + graceful ignorance. Under that condition, it's tractable.

## Fidelity spectrum (buildable in stages)
- **MVP:** common-knowledge-by-station + append-only "what each character has learned this story" log + scene-scoped retrieval. No false beliefs yet.
- **+ Drama fidelity:** false / uncertain beliefs + provenance (mandatory for mystery/intrigue; optional for picaresque).
- **+ Full:** confidence, forgetting, second-order beliefs (what A thinks B knows — needed for deception/politics).

## Open questions (unresolved)
- Detecting an omniscience leak at decision time (the character reaches for a fact it shouldn't have) — automated check or judge?
- Cost of per-character retrieval at cast × scene scale.
- How deep second-order theory-of-mind is worth modeling.

## Prior art — ALREADY IMPLEMENTED in The Writer's Desk (Feb 2026)
The earlier **author-mode** project `Claude Flow/projects/private/the-writers-desk` already builds this model. Different paradigm (a novelist agent *writes* chapters), but the knowledge machinery transfers directly — code, grep-verified:
- **Per-character knowledge with provenance + time** — `foundation_runner.py` character defs carry `knowledge: [...]` with acquisition tags: *"Chushe's death (learned mid-trek)"*, *"Samantha's capture (witnessed)"*, *"the Horde truth (told by agents)"*, *"Capital politics (growing)"*, *"Chimil Shire (partial — left before the raid)"*. Exactly acquired-not-assumed + timestamped + partial.
- **Knowledge-boundary loader** — `db/kuzu.py: load_character_knowledge()` ("knowledge boundaries", "RCoT Step 15") over a Kuzu knowledge graph.
- **information_asymmetry** persisted in `db/sqlite.py` `reader_model` ("what the reader knows, believes, and feels") = the Pinocchio Protocol, built.
- **Planning vs Writing mode separation** — `writers_desk/mode.py` + `planning_rationale` / `writing_instruction` directive columns. Planning data (secret motivations, arc destinations, deception flags) is invisible in writing mode. **This is the beat-blind constraint, already implemented.**
- **deception_flags per character** — "withholding family truth", "performing ambition while building infrastructure", "zero recovery rule".
- Possibly relevant to the omniscience-leak open question: `writers_desk/filters.py` + `writers_desk/critics/` (unread).

**Implication:** the injection model is NOT a from-scratch build — **lift it.** The only genuinely new work here is the paradigm swap: author-mode *trusts the novelist* to respect knowledge boundaries; sim-mode *enforces* them — the boundary becomes the literal context the character-simulator sees (a structural wall, not a trusted convention). Same model, harder enforcement.

**Caveat:** verified implemented + exercised to the foundation stage (real characters defined in `foundation_runner.py`); full end-to-end book production not verified from this read.

## Prior art #2 — Project Scribe Lang's Context Assembler (the injection engine, built — but author-mode)
"Lang scribe" = `IDE.code-workspace/Project Scribe Lang/` — a LangGraph multi-agent novel engine (A1 Architect, A9 Director, A11 Psychopathologist, A13 Librarian, A14 Chronicler, etc.). Its `CONTEXT_ASSEMBLER_SPEC.md` (v2.0, implementation-ready, 2026-02) IS an injection engine, with the knowledge machinery built:
- **Per-character knowledge graph (KùzuDB):** `(Character)-[:KNOWS]->(Fact)`, `(Character)-[:DOES_NOT_KNOW]->(Secret)`, plus `information_asymmetry: {char_id → secrets they DON'T know}` and per-scene `character_states {knowledge, emotion, location, inventory}`. Relationship edges carry trust/affinity.
- **Relevance-at-scale = "onion peeling":** when context exceeds the token budget, drop outside-in (style exemplars → supporting detail → history → atmosphere); NEVER drop POV profile / psych directives / must_include. Concrete solution to layer #3.
- **Layer system (1-5)**, polystore (Kùzu graph + LanceDB vectors + SQLite + files), and **RCoT verification** (A14) that reverse-checks output against a ground-truth knowledge baseline.

**The catch — it's AUTHOR-mode, and that inversion is the whole point for us.** Step 15 is explicit: the knowledge baseline is *"NOT used by A5 [the prose generator] for prose generation — passed through to the RCoT verification step."* So Scribe gives the writer EVERYTHING and **catches** knowledge leaks afterward (detect-and-correct). Sim-mode needs the opposite: the character sees ONLY its knowledge slice so it **cannot** leak (prevent) — the obsidian-vault wall.

**The move:** lift Scribe's knowledge graph + onion-peeling, but **invert the data flow** — feed the per-character knowledge slice INTO the simulator's context as the boundary, not into a post-hoc verifier. Scribe's RCoT verifier then becomes the *secondary* safety net (catch what the wall missed), not the primary mechanism. Same data model, inverted role.

**Gaps for sim-mode:** (a) Scribe generates PROSE from an authored scene plan — from the assembler + pipeline shape I see no autonomous *character-decision* step (its "characters" are profiles fed to a writer, not agents that act). That decision loop is the genuinely new build. (b) Model is KNOWS / DOES_NOT_KNOW, not FALSE-belief — weaker for deception/unreliable characters; extend.

## Transmission rule — the vault grows only by acquisition
- A vault grows ONLY by what the character **knows or learns**. Acquisition channels: **witnessed, overheard, read, told, taught, deduced** (inference — and inference can be wrong). Monotonic-add for the MVP (forgetting is a later layer).
- **Free consequence of the wall:** because the simulator sees only the *speaker's* vault, a character **cannot reveal a fact they don't have**. "No one can tell a secret they don't know" is enforced automatically by the per-character injection boundary — not a separate rule.
- **CRITICAL — knowing is gated, SAYING is not.** A character can still **lie, guess, bluff, or withhold**. A lie = asserting something not in (or contrary to) their vault. If transmission were limited to "only what you truly know," deception would be impossible — and deception / secrets / rumor is most of the drama. The vault gates **knowing**, never **saying**.
- **Therefore the vault stores BELIEFS, not facts:** `{claim, value-as-they-believe-it, provenance (witnessed | told-by-X | deduced | …), source_trust, timestamp}`. When A tells B something, B's vault gains *"told X by A (trust w)"* — possibly false; whether B acts on it scales with trust. This is how rumor, manipulation, and false belief propagate realistically.
- **Director corollary:** to get information to a character, the director stages an in-world **acquisition event** (a letter, a witness, an overheard line) — never fiat-injects it. Same discipline as steering characters by circumstance: route *facts* through the world, not by decree.
- **Scene mechanics:** turn-based; each turn injects the *actor's current* vault; A acts/speaks from A's vault → recorded → B's vault updated (trust-weighted belief) → B's turn sees the update. Information propagates, bounded by who-had-what.

## Belief dynamics — lift the Talk of the Town taxonomy (don't reinvent)
Acquisition (above) is only half of belief life. **Talk of the Town (Ryan et al. 2015) named the full mechanism set a decade ago** (`prior-art.md` — fetched/quoted, verification pass incomplete; confirm against the primary on first use): false beliefs arise by **lying** (ours already), **confabulation** (invented detail filling a gap), and **transference** (attributes of one entity mis-attached to another); held beliefs degrade by **mutation** (deterioration of a value in place) and terminate by **forgetting** — with mutation/forgetting governed by a per-character **memory attribute × facet salience**, computed by the engine, never authored per-incident. Slots directly into our fidelity spectrum: acquisition channels are MVP; lying is the "+ drama" layer; **confabulation/transference/mutation/forgetting are the "+ Full" layer's missing mechanics** — adopt their taxonomy and parameterization shape (per-character memory trait feeds from genotype/traits, `baseline-generation.md`) rather than designing our own.
