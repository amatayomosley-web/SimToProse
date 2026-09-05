# MAP — what is in this project and what owns what

**Why this file exists.** `docs/` holds 87 design docs, `src/engine/` 50 modules,
`tests/` 76 suites. Nobody — human or agent — can hold that in their head, and reading it all every
session is not practical. **The failure this prevents is real and happened:** a session spent hours
reasoning about the decision layer from four docs and inference, invented a parallel vocabulary
("vectors"), and rebuilt a worse version of the buff/debuff registry that `decision-engine.md`
already specifies — including its guardrails and its falsification test. Read the ROUTING table and
the VOCABULARY below at session start. Open the specific artifact when its row matches your task.

**This file is GENERATED except for the ROUTING and VOCABULARY sections.** The inventories come from
each artifact's own title line or module docstring.

That used to be followed by "so they cannot drift from the code without the code changing", above a
shell one-liner you were trusted to paste. Half true, and the wrong half: a RENAMED title surfaces
on the next regeneration, but an ADDED file never does, because nothing re-runs it — and nobody runs
a one-liner that lives in a doc. Measured 2026-08-24, on the file every session is told to read
FIRST: the module table listed 18 of 24, docs 49 of 62, suites 29 of 40. Now a script, and a test:

```bash
python scripts/gen_map.py            # rewrite the tables
python scripts/gen_map.py --check    # exit 1 if they disagree with the tree (tests/test_map.py)
```

The old instruction, kept because it still documents what the rows are built FROM:

```bash
for f in docs/*.md; do n=$(basename $f .md); t=$(head -1 "$f" | sed 's/^# //'); l=$(wc -l < "$f"); echo "| \`$n\` | $l | ${t#* — } |"; done
for f in src/engine/*.py scripts/*.py; do n=$(basename $f .py); l=$(wc -l < "$f"); d=$(sed -n '1,4p' "$f" | grep -o '"""[^"]*' | head -1 | sed 's/"""//' | sed "s/^$n\.py — //"); echo "| \`$n\` | $l | $d |"; done
```

---

## ROUTING — what to open, by what you are doing

Ordered by how often it is the right answer. **`design.md` first, always** — it is 107 lines and it
carries the pipeline, the compute/generate split, and the load-bearing constraints that every other
doc assumes.

| doing this | open, in this order |
|---|---|
| **MAKING A BOOK, not changing the engine** | `guide-user-path.md` — the author-facing router: entry points, setup, the four normative contracts, the tools, the roles, prose out, judging. This table below is contributor-shaped; that one is author-shaped |
| **anything, first** | `design.md` — 7 pipeline layers · the compute/generate split · the LLM's 4 calls · the load-bearing constraints |
| **how a choice gets made** | `decision-engine.md` → `drives-schema.md` → `values-and-stakes.md` |
| **tuning behaviour / picking a lever** | `driving-the-engine.md` — measured firing rates, reliability bands, the lever recipes. `scripts/exp.py` is its harness |
| **mapping the system's limits / the bounds battery** | `bounds-experiment-design.md` — pre-registered arms, grep-able measures, the bounds ledger; the verified route map of what reaches the actor |
| **a character's numbers** | `baseline-generation.md` → `character-schema.md` → `character-anatomy.md` → `trait-theory.md` |
| **a character archetype / model** | `character-model.md` §models — models are sparse BIAS-NOT-SET diffs over layers 1·3·5·7·10 |
| **what a character knows** | `knowledge-model.md` → `relevancy-gate.md` |
| **what a character feels** | `state-engine.md` → `generative-model.md` |
| **which emotions are irreducible, and how the rest are expressed in them** | `emotion-basis.md` → `state-engine.md` |
| **how to AUTHOR a character's emotional makeup, in order** | `guide-emotional-authoring.md` → `guide-content.md` |
| **what NUMBER to write in a field** | `reference-species-prior.md` → `baseline-generation.md` |
| **how a backstory BECOMES a baseline (LLM classifies, script composes)** | `composition-pass.md` → `baseline-generation.md` |
| **what a given affect vector IS (naming a state)** | `src/engine/compounds.py` → `emotion-basis.md` |
| **what a character recalls** | `relevancy-gate.md` (recall half) → `src/engine/acquisition.py` |
| **relationships** | `relationships.md` → `src/engine/bonds.py` — trust/affinity/respect/debt; the prediction-error update runs PER WITNESS (`arc.py` no longer writes edges) |
| **durable change over a book** | `arc-engine.md` |
| **a turn becoming events** | `consolidation-loop.md` (**THE KEYSTONE**) → `record-contract.md` → `recording-model.md` |
| **a scene's inputs** | `scene-assembly.md` → `multi-character.md` → `scene-brief-blueprint.md` |
| **building a world** | `world-model.md` → `universal-law.md` → `broader-community.md` → `planet.md` → `history.md` → `present-systems.md` |
| **the world changing / state** | `world-dynamics.md` → `world-state-ledger.md` |
| **laws and refusals** | `universal-law.md` + `guide-content.md` (Laws section) + `orchestrator-design.md` §7.1 + `src/engine/bible.py` |
| **prose out** | `narration.md` → `voice.md` → `cutting-room.md` |
| **judging a scene** | `measurement.md` → `acceptance-criteria.md` |
| **driving this with a WEAK model / small context** | `small-model-mode.md` — the two minimum specs (actor 2.2k forced, driver 25-37k undefined), why 10k is the driver floor, rails = decompose + scriptify, toolboxes compile to menus, and what the human carries at each tier |
| **proving the MACHINERY works** (vs. the book being good) | `verification-sheet.md` — Part A automated (`python scripts/verify.py --slow`), Part B per-mechanism, Part C human reads, Part D what a full green sheet still does NOT prove |
| **running a book** | `guide-operating.md` · authoring content: `guide-content.md` · engine work: `guide-engine.md` · continuing: `guide-continuing-the-story.md` |
| **the agent layer** | `orchestration.md` → `orchestrator-design.md` → `grounding.md` → `agent-toolboxes.md` |
| **starting a NEW book** | the `starting-a-book` skill (a map, holds no craft) |
| **AUTHORING RULES — the normative contracts** | world note + people: `world-authoring-rules.md` · character notes + beliefs: `character-authoring-rules.md` · scene configs + drives: `scene-authoring-rules.md`. Enforced mechanically by `scripts/lint_book.py` |
| **what is already known-hard** | `prior-art.md` · `audit-2026-06-10.md` · `probe-plan.md` |

**Precedence** (`CLAUDE.md`): for what IS — code > tests > guides > design docs. For what SHOULD BE —
design docs win.

---

## VOCABULARY — use the project's words, not synonyms

The one that caused the incident above is first. **If you find yourself coining a term for a thing
the system already names, stop and search this table.**

| the word | means | where it is defined |
|---|---|---|
| **primitive** | an emotion that cannot be derived from a combination of other emotions. The eight: SEEKING FEAR RAGE LUST CARE PANIC_GRIEF PLAY DISGUST. A COMPOUND is a coordinate over them, each with its own TARGET | `emotion-basis.md` |
| **lever** | a bounded, authorable quantity on a character — the stat block. NOT "vector," NOT "axis." The set is **bounded and authored once** | `decision-engine.md` §effective-state catalog |
| **buff / debuff** | a conditional modifier on a lever: `{trigger condition, affected lever, op (× or ±), magnitude, source}`. This is the mechanism for "under condition X this person weights Y differently" | `decision-engine.md` §buff/debuff registry |
| **model** (Layer 10) | a person's weighting over the worth menu **and** the resolver — what wins when operands collide. As an archetype it is a **bias-pack over the catalog** | `character-model.md` §models · `decision-engine.md` §where the weights live |
| **operands vs resolver** | layers 1·3·5·7 hold *magnitudes*; layer 10 holds *priority over them*. Do not double-count 10 as another magnitude | `decision-engine.md` |
| **direction** | the qualitative translation of a computed number, and the ONLY form in which state enters a prompt. Numbers live in the DB | `design.md` · `src/engine/direction.py` |
| **the cut** | the selected, ordered biography that becomes prose. Selection, never invention | `cutting-room.md` |
| **faithful refusal** | a character declining a beat. Means the BEAT is wrong, never the character | `design.md` load-bearing constraints |
| book-invented terms (magic systems, ranks, institutions) | BOOK-specific, NOT engine vocabulary. Never in `src/` | that book's own `world/` note |

**Rejected resolvers, so they are not re-proposed:** a code-side weighted sum picking the action
(`decision-engine.md:5` — "reject that as the resolver"); an LLM that calculates a stat; anything
that lets narrated prose write state (`design.md` three boundaries).

---
## docs/ — 86 design docs (normative for what SHOULD BE)

| docs | lines | owns |
|---|---|---|
| `SPEC-LEDGER` | every specified mechanism, against the code that does or does not implement it |
| `acceptance-criteria` | "a finished book" |
| `actor-direction-format` | what an agent actually receives |
| `agent-toolboxes` | the standard every agent's skill follows |
| `arc-engine` | durable change (trauma, growth, the through-line) (WORKING) |
| `audit-2026-06-10` | 2026-06-10 |
| `BLUEPRINT-character` | The Character Blueprint |
| `BLUEPRINT-scene` | THE SCENE BLUEPRINT |
| `BLUEPRINT-world` | The World Blueprint |
| `START-HERE` | Building a Book, by Hand |
| `baseline-generation` | where every per-character number is born (WORKING) |
| `basis-verification` | the blind-judge confusion matrix |
| `bounds-experiment-design` | what a director can and cannot make the engine do (DESIGN / pre-registered, not yet run) |
| `broader-community` | the scope gate (before the planet) |
| `character-anatomy` | the complete picture (what forms a person) |
| `character-authoring-rules` | Normative Rules for Authoring SWE Character Notes |
| `character-model` | the levers that make a person real |
| `character-schema` | the consolidated stat block (WORKING) |
| `composition-pass` | how a backstory becomes a baseline |
| `connection-model` | what a character is invested in, and how much it multiplies |
| `consolidation-loop` | turning a turn into accurate events (THE KEYSTONE) (WORKING) |
| `cutting-room` | what we do with the data (WORKING) |
| `decision-engine` | how the variable weights map and resolve into a choice |
| `design` | Simulated World Evolve |
| `drives-schema` | goals, fears, and orientation as opposable fields (Layer 3) |
| `driving-the-engine` | an authoring guide (LIVING / experiment-driven) |
| `emotion-basis` | the primitives, their targets, and where tense lives |
| `emotion-list` | every name, staged by degree |
| `emotion-recipes` | every compound, its variations, and how much of the person survives it |
| `emotion-scales` | what the numbers mean |
| `emotion-vocabulary` | exhaustive |
| `generative-model` | how a character produces behavior (first principles) |
| `goal-alignment-review` | the spider test against the shipped engine |
| `grounding` | how the orchestrator is kept speaking from facts |
| `guide-building-a-world` | the procedure |
| `guide-content` | authoring a book's inputs |
| `guide-continuing-the-story` | what to author for each generation step (LLM guide) |
| `guide-emotional-authoring` | authoring a character's emotional makeup |
| `guide-engine` | working on the machine |
| `guide-operating` | running books on the engine |
| `guide-user-path` | everything you need, in the order you need it |
| `history` | the justification layer (the rules that govern its process) |
| `keeper-of-truth` | how a world grows facts it was never authored with |
| `knowledge-model` | the core problem) |
| `measurement` | detectors, the critic, and judge protocols (WORKING) |
| `multi-character` | Multi-Character Conversation & Debate (3+) (WORKING) |
| `narration` | "who says this?" (the prose voice and its knowledge boundary) |
| `new-book-manifest` | what the user copies, creates, and references |
| `orchestration` | the showrunner (the process-brain that runs the whole book) |
| `orchestrator-design` | design notes for the build |
| `phrases-care` | the band sets |
| `phrases-disgust` | the band sets |
| `phrases-fear` | the band set |
| `phrases-lust` | the band sets |
| `phrases-panic-grief` | the band sets |
| `phrases-play` | the band set |
| `phrases-rage` | the band set |
| `phrases-seeking` | the outward band set (reference specimen) |
| `planet` | the physical stage (sized to what's required) |
| `present-systems` | step 4 (the operating present) |
| `prior-art` | what's paved, what isn't (researched 2026-06-10) |
| `probe-plan` | the make-or-break test (run BEFORE building the engine) |
| `record-contract` | what the sim MUST write (WORKING) |
| `recording-model` | two streams: thoughts + actions |
| `reference-species-prior` | the species prior, and the formative diffs that move it |
| `relationships` | growth, diminishment, and how they gate everything |
| `relevancy-gate` | what to inject from the vault |
| `roadmap-character-memory` | the four advanced character memory tracks |
| `run-lifecycle` | save, resume, recover, govern (WORKING) |
| `scene-assembly` | how a character lives the scene (WORKING) |
| `scene-authoring-rules` | Normative Rules for Authoring SWE Scenes & Characters |
| `scene-brief-blueprint` | sizing a sim run (how much plot fits) |
| `self-and-perception` | three views of one person |
| `small-model-mode` | how a weak LLM drives this engine, and what it costs the human |
| `standard-vectors` | how a vector is derived, sized, and judged |
| `state-engine` | exactly how character state is computed (WORKING) |
| `template-scene-blueprint` | the authoring contract every book writes against |
| `trait-theory` | OCEAN's structure + related models (research for the "add traits" decision) |
| `universal-law` | the guide (what must be *settled*, not what's *true*) |
| `values-and-stakes` | the menu of "worth" (the model weights this) |
| `verification-sheet` | run these to prove the machinery works, not that the book is good |
| `voice` | the speech layer and the craft standards (WORKING) |
| `world-authoring-rules` | Normative Rules for Authoring the SWE World & Its People |
| `world-dynamics` | how the world pushes back (WORKING) |
| `world-model` | the other half of the loop (SEED — to co-design) |
| `world-state-ledger` | the live now (design the machinery; the line items are runtime) |

## src/engine/ — 50 modules (normative for what IS)

| src | lines | owns |
|---|---|---|
| `acquisition` | the vault grows: a durable, subject-bearing turn becomes a recallable belief. |
| `arc` | the Arc Engine: durable baseline change over the story (docs/arc-engine.md). |
| `associative` | Track 2 & 3: Multi-Hop Associative Graph Traversal with Temporal Decay. |
| `bible` | pin the authored bible into the run DB, and make entities exact. |
| `bonds` | the relationship tier: how one person's read of another MOVES. |
| `books` | resolve a book by slug, so several can be active at once. |
| `citation` | the grounding contract's enforcement core. |
| `claims` | what an actor asserted about the world, and when two assertions cannot both be true. |
| `clock` | the DECLARED clock. One cause, four consumers. |
| `code_families` | the code DATA. One dict per module family; `codes.py` holds the contract. |
| `codes` | the frozen registry of engine error codes. |
| `compounds` | the named emotions, as coordinates over the primitives. |
| `connection` | how much of the character is INVESTED in the person a moment is about. |
| `consolidation` | Gate 4: Consolidation Validation. |
| `db` | SQLite connection + schema migration for the engine spine. |
| `decay` | Track 3: Memory Decay & Temporal Forgetting Curves. |
| `decay_law` | the one equation every decay in this engine already was. |
| `direction` | numbers to qualitative DIRECTION (gate 5, the backstage guardrail). |
| `edl` | the edit decision list: what the room decided, recorded so the prose can be traced. |
| `errors` | the single typed refusal channel for the whole engine. |
| `facets` | what a belief is ABOUT, stamped when the belief is written. |
| `faithfulness` | the deterministic half of the faithfulness guard: catch NAME leaks in a turn. |
| `faults` | the engine-fault detector: the machine-side twin of the chair's world-fault inbox. |
| `floor` | who wants the floor next. |
| `fold` | the pure function from LOG to SNAPSHOT. The reading half of the spine. |
| `gate` | Relevancy Gate: perception-mode wall + recall-mode trigger-matching. |
| `heritable` | the genotype: how it is READ, and what each allele does. |
| `identity_view` | the STABLE identity prefix, said in words. |
| `integrity` | what is WRONG with a database that a fresh one could not be wrong about. |
| `law` | what the world PERMITS. The ruling half of the bible. |
| `ledger` | the event-sourced spine: append-only log + atomic turn-commit + pure fold + resume. |
| `levers` | the effective-levers tier (the buff/debuff catalog). |
| `narration_modes` | the two axes a narrator is set on, and only one touches the wall. |
| `profiles` | profiles.py ? the formative profiles library and composition gate. |
| `prompt` | the reasoning-contract layer as MACHINERY (gate 6, machine/content separation). |
| `read_api` | the orchestrator's typed read surface over the run DB. |
| `records` | typed record contracts for everything the engine writes (record-contract.md). |
| `scene` | Scene Assembly: deterministic 7-step pipeline producing the decision packet. |
| `scene_cfg` | the scene cfg a scene ran against, pinned so a replay can name its inputs. |
| `severity` | the event-strength vocabulary: seven engine-owned words on the existing 0..1 scale. |
| `snapshots` | the folded world, cached. NOT the source of truth, and the file says so. |
| `state` | State Engine, Gate 2. |
| `targets` | what each feeling is ABOUT. |
| `tensions` | the first register on the world-appraisal chassis. |
| `toward` | the MICRO tier: what one specific person makes you feel. |
| `vault` | the Obsidian book-vault loader (machine/content seam at the repository level). |
| `world_appraisal` | the world-side mirror of `state-engine.md`. ONE mechanism, three registers. |
| `world_events` | what makes an event worth recording to the WORLD, and what each type means. |
| `wound` | the wound tier's MOVER: what decides that a scar deepens or eases. |
| `writeonce` | the identities the spine writes ONCE, and the refusal when something writes twice. |

## scripts/ — the entry points

| script | lines | owns |
|---|---|---|
| `critic` | 125 | the continuity + voice critic (design.md layer 6, the non-author check). |
| `cut` | 133 | the cutting room's DAILIES VIEWER (cutting-room.md, the views half). |
| `direct` | 512 | the director's chair ( |
| `exp` | 237 | the lever-eval harness for docs/driving-the-engine.md. |
| `lint_book` | 124 | pre-run validation of a book's world + characters (production-hardening). |
| `narrate` | 232 | the narrator (design.md layer 7, narration.md): a canonized scene -> POV-bound prose. |
| `scene` | 393 | the multi-agent scene runner (the director sets the scene; the agents push it). |

## tests/ — 76 suites (each is a PROOF of the gate it names)

| tests | lines | owns |
|---|---|---|
| `test_acquisition` |  |
| `test_arc` |  |
| `test_basis_parser` | the basis probe's answer parser, under a harness that actually runs it. |
| `test_belief_facets` | a belief must carry what it is ABOUT, stamped when it is written. |
| `test_belief_identity` | a recorded belief reference must still name that belief tomorrow. |
| `test_belief_revision` |  |
| `test_bible` |  |
| `test_bonds` | the relationship tier (src/engine/bonds.py). |
| `test_books` |  |
| `test_canon_digest` | the digest must equal the DB it digests. |
| `test_capability_claims` | a mechanism a doc NAMES as available must have a code path. |
| `test_citation` |  |
| `test_citations` | the docs' `file.py:NN` references must point at what they claim. |
| `test_claims` | the structural collapse detector, exercised on the Clifford case. |
| `test_coded_refusals` |  |
| `test_compose_event` |  |
| `test_composition_pass` |  |
| `test_composition_phase_a` |  |
| `test_compounds` | the named emotions as coordinates over the primitives. |
| `test_connection` |  |
| `test_consolidation` |  |
| `test_critic` |  |
| `test_cut` |  |
| `test_decay_law` |  |
| `test_declared_is_read` | the guard for this repo's named dominant defect class. |
| `test_direction` |  |
| `test_disgust` | the eighth primitive, and what it unlocked. |
| `test_driver_main` |  |
| `test_edl` |  |
| `test_effective` | the effective-levers tier (src/engine/levers.py). |
| `test_errors` | the coded refusal channel, and the registry's two-way rule. |
| `test_faithful_turn` |  |
| `test_faults` |  |
| `test_floor` |  |
| `test_formative_profiles` |  |
| `test_gate` |  |
| `test_gate_multihop` |  |
| `test_genotype` | the combinatorial preset draw (scripts/make_genotype.py). |
| `test_integrity` |  |
| `test_keeper` |  |
| `test_laws` |  |
| `test_laws_preflight` | the world refuses something. |
| `test_ledger` |  |
| `test_lint_book` |  |
| `test_lint_scene` | each scene-cfg check must fire on exactly what it claims to catch. |
| `test_live_belief_revision` |  |
| `test_map` | the routing table must describe the tree it routes into. |
| `test_memory_decay` |  |
| `test_narrate` |  |
| `test_no_digits` | THE LAW: no number describing a character reaches them. |
| `test_no_private_content` |  |
| `test_numeric_slots` | a book that lints clean must be a book that runs. |
| `test_orc_hooks` |  |
| `test_pipeline_e2e` |  |
| `test_place` |  |
| `test_portability` |  |
| `test_profiles` |  |
| `test_prompt_sections` | every labelled section of the actor prompt holds ITS OWN content. |
| `test_reachable` |  |
| `test_read_api` |  |
| `test_recall_decay_is_wired` | through assemble(), not through decay's own unit tests. |
| `test_scene` |  |
| `test_scene_config` |  |
| `test_scene_persistence` |  |
| `test_scenes` |  |
| `test_self_contained` | the engine STANDS ALONE. |
| `test_severity` | the event-strength vocabulary resolves onto the EXISTING 0..1 scale. |
| `test_state` |  |
| `test_subject` |  |
| `test_targets` | per-primitive targets: what each feeling is ABOUT. |
| `test_theory_of_mind` |  |
| `test_toward` |  |
| `test_vault` |  |
| `test_world_appraisal` |  |
| `test_world_events` | the world types, checked against the fold that actually consumes them. |
| `test_wound` |  |

## .claude/ — the optional agent overlay

**9 agents:** `showrunner` (batch orchestrator; the interactive form is the *skill*) · `director` · `world-builder` · `character-generator` · `character-simulator` · `recorder` · `continuity-critic` · `cutter` · `narrator`.

**11 skills:** `starting-a-book` (entry map) · `showrunner` (the one you talk to) · `showrunning` · `worldbuilding-frameworks` (index only — its `references/` are UNWRITTEN) · `character-frameworks` (8 reference files, fully built) · `dramatic-structure` · `emotion-and-decision` · `event-semantics` · `narrative-craft` · `continuity-and-consistency` · `selection-and-montage`.

Agents get facts ONLY through the engine-computed packet; skills hold craft, never facts.
