# Simulated World Evolve

Simulate worlds, record them, and write books from the lives inside them.

## What it is
A pipeline that (1) defines a **grounded world** (laws, religion, economy, geography, factions, rules), (2) populates it with **characters** who have deep backstories, goals, values, and flaws, then (3) **simulates** what those characters do when circumstances are placed in front of them — and renders the recorded results into prose.

## The core idea: live biographies → novel
The simulation produces, for each character, a **live biography** — the complete, chronological record of their thoughts and actions as they live through the world (`docs/recording-model.md`). That record is ground truth: exhaustive, per-character, bounded by what each person actually knew and did.

**The novel is a *cut* of those biographies — selected, ordered, and narrated, never invented.** Every line of the book traces to a recorded biographical moment. But "turning biographies into a novel" is **selection and dramatic shaping, not transcription**: a biography is a *life* (exhaustive, mostly inert); a novel is a *shaped story*. That transform is where the craft and the risk live (`docs/narration.md`, `docs/acceptance-criteria.md`) — it's the documentary editor's cut, not a dump of the footage.

Two consequences:
- **Faithfulness by construction** — the book can't contain what didn't happen in the sim.
- **One simulation → many novels** — the same run can be cut from different POVs, selections, and framings (the protagonist's book, the villain's book, a bystander's book). The biographies are the reusable asset; a novel is one rendering. Run once, novelize many.

Analogy: the sim *films* everyone's life continuously (thoughts = inner mic, actions = camera). The director *shoots* (steers lives via circumstance) and *edits* (cuts the film). The footage is exhaustive; the film is the art of the cut.

## The core stance: directors, not authors
We do **not** write the characters' actions. We **direct**: we control the world and the circumstances; the characters (the simulation) act autonomously; we record what they do.

To move a character for plot, we never *force* the character — we change the **world** so the plot-required move becomes what they would *autonomously choose*. Forcing is the failure mode; in-character motivation via circumstance is the tool. **If no circumstance can motivate a beat, the beat is wrong for these characters — revise the beat, not the character.** A faithful refusal is the integrity check on the plot.

## Two layers, one repo
The repo ships two independent layers. Pull the engine alone and every script runs, key-free, with a local model or `--stub`. Add the agent overlay only if you're driving the engine from Claude Code.

| | Layer 1 — ENGINE | Layer 2 — AGENT OVERLAY (optional) |
|---|---|---|
| **What** | Deterministic Python: `src/engine/` + `scripts/` + `tests/` + fixtures (`world/`, `characters/`) | `.claude/agents/` (9 roles) + `.claude/skills/` (9 craft toolboxes) + `runs/_TEMPLATE/` process notes |
| **Gives you** | The whole pipeline by hand: scene → simulate → consolidate → critic → narrate → cut, run turn by turn from the CLI | A showrunner that drives the same scripts + subagents for you — it fills the act/judge/write roles the engine already externalizes (its `--prompt-only` seams and LLM dispatch points) |
| **Requires** | Nothing but Python stdlib + (optionally) a local model or an OpenRouter key | The engine underneath (never stands alone) + Claude Code |
| **Standalone?** | Yes — pull the repo, ignore `.claude/`, run the scripts | No — a driver of the engine, never a replacement for it |
| **Status** | Built + verified (see **Status**, below) | Authored, not yet run end-to-end (see **Status**, below) |

**New here and want to make a book?** Start at [`docs/guide-user-path.md`](docs/guide-user-path.md) — everything a user needs, in the order they need it: the two entry points, setting the book up, the four normative authoring contracts, the tools, the nine roles, getting prose out, and judging it.

**Pull engine-only** if you want to run books by hand or integrate the pipeline elsewhere: clone, ignore `.claude/`, follow `docs/guide-operating.md`.
**Pull both** if you're operating from Claude Code and want the showrunner to drive the scripts and gate the seams for you: see `docs/orchestration.md`.

## The law: compute/generate, in both modes
**Every VALUE — state, checks, appraisal, perception, salience — is computed by the deterministic engine. The LLM acts, judges, and writes only.** Numbers live in the DB; prompts get direction, never numbers (`docs/design.md` — "The compute/generate split"). This holds identically whether a human is driving the scripts or the showrunner is: the agent layer is a **driver** of the engine, never a value-computer. See **Modes** in `CLAUDE.md` for how the two drivers split responsibility without touching this law.

## Status (2026-07-24)

**Layer 1 — engine: built and verified.** The full spine (ledger → state → scene+gate → consolidation → direction → prompt) plus the built pipeline (`direct.py`, `scene.py`, `critic.py`, `narrate.py`, `cut.py`, `lint_book.py`) — 8 test suites passing, coherence + director-circumstance probes passed. Verify block: `CLAUDE.md`.

**Layer 2 — agent overlay: authored, unproven.** 9 agents + 9 skill toolboxes (1 fully authored — `character-frameworks`; the other 8 are routers with planned references) + the `runs/_TEMPLATE` process-notes skeleton, written 2026-07-23 against the engine's existing `--prompt-only` seams and LLM dispatch points — not yet run end-to-end on a real book.

**Neither mode has produced a real book yet.** That's the next genuine step, in either mode (`docs/guide-operating.md` for Mode A, `docs/orchestration.md` for Mode B).

Known gaps — don't rediscover these as bugs: the critic is detect-only (no rewrite / compensating-event writer); the cutting room is views-only (no EDL); world/character generation tooling is unbuilt (hand-author per the guides, lazy-resolve the rest).

## Layout
| Dir | Layer | Holds |
|-----|-------|-------|
| `src/engine/` | 1 | the deterministic engine — ledger, state, scene, gate, consolidation, direction, prompt |
| `scripts/` | 1 | the CLIs: `direct.py` `scene.py` `critic.py` `narrate.py` `cut.py` `lint_book.py` `exp.py` |
| `tests/` | 1 | the regression + probe harness (8 suites + `coherence_probe.py`) |
| `world/`, `characters/` | 1 | ENGINE TEST FIXTURES ONLY (Maren/Ashford) — a real book's world/characters live in the author's vault |
| `runs/` | 1 | recorded simulation runs (`.db` files, gitignored) + world-state ledgers |
| `runs/_TEMPLATE/` | 2 | the process-notes skeleton — copy to `runs/<slug>/` to start a book, either mode |
| `books/` | 1 | rendered narrative output (real books live in the author's vault, never here — hard rule 1) |
| `docs/` | 1 | the full design (see **Docs**, below) |
| `.claude/agents/` | 2 | the 9 agent roles (showrunner + 8 specialists) |
| `.claude/skills/` | 2 | 9 craft toolboxes the agents draw on |

## Docs (the design, in reading order)
**Foundation**
- [`docs/generative-model.md`](docs/generative-model.md) — **the spine (first principles)**: virtues/emotions aren't stored — they're *generated* from a bounded motivational basis, shaped by genetics + history, transformed by situation, resolved narratively. The principle the rest of the character system implements.
- [`docs/design.md`](docs/design.md) — the two pipelines: **generation** (how the world + characters are made, law → main character, two-phase) + **runtime** (how a built world is simulated) + load-bearing constraints + the **compute/generate split** (a deterministic game engine computes every *value* — state, checks, emotions, perception; the LLM only frames scenes, acts characters, consolidates prose, and narrates) + **two drivers, one engine** (Mode A / Mode B)
- [`docs/acceptance-criteria.md`](docs/acceptance-criteria.md) — observable definition of "a finished book"

**The character system** (a character is a per-character belief store the sim acts from)
- [`docs/character-anatomy.md`](docs/character-anatomy.md) — **START HERE: the complete picture** — every factor that forms a person, in 10 layers, indexing all the deep-dives below
- [`docs/character-schema.md`](docs/character-schema.md) — **the consolidated stat block**: every value a character carries, organized by the **clock that changes it** (FIXED genotype/position · BASELINE temperament/traits/Model/drives/skills · CURRENT affect/condition/relationships/vault · DERIVED effective-levers). The DB contract — a slow character sheet + a fast state row; the three clocks *are* the write-paths (generation / arc-engine / consolidation-loop). The schema `character-anatomy.md` indexes conceptually, made concrete.
- [`docs/knowledge-model.md`](docs/knowledge-model.md) — the vault / injection model: knowledge is *acquired* (provenance, time-sliced, false belief); knowing gated, saying free; prior art restated in-doc
- [`docs/relevancy-gate.md`](docs/relevancy-gate.md) — what to inject: counterfactual relevance via trigger-matching + skill checks; backlinks as cost/difficulty (not a hop-cutoff); connection energy
- [`docs/character-model.md`](docs/character-model.md) — the levers that make a person real (conflict + state, not count); the realism test; prior-art schema + reuse/build delta; **models as sparse weight-diffs** (bias-not-set); **character roadmap (next: the decision engine)**
- [`docs/relationships.md`](docs/relationships.md) — per-perceiver belief edges (trust/affinity/respect/debt); prediction-error + negativity-bias update; trust gates transmission
- [`docs/recording-model.md`](docs/recording-model.md) — capture thoughts + actions; the visibility split *is* the POV boundary; a lie = recorded thought≠action
- [`docs/consolidation-loop.md`](docs/consolidation-loop.md) — **THE KEYSTONE: turning a turn into accurate events** (everything depends on it — the one error class that *compounds*). The **actor records its own action** (self-report, not an observer guessing) as structured **event-tags** in one pass; nobody records another's mind (engine resolves outcomes, cross-effects via perception); a **typed event schema** is the contract; and because everything rides on it, an explicit **measurement regime** (ground-truth replay · round-trip · cross-extractor agreement · the coherence probe). The binding engineering risk.
- [`docs/record-contract.md`](docs/record-contract.md) — **what the sim MUST write** (audit repair A1/A2/A3): downstream read-requirements ARE upstream write-requirements — `recall` events, the per-turn **decision-input manifest** (the consequence graph's read-side join key), `relationship-delta` events, dialogue-acts, stance snapshots; plus the **event catalog** as one artifact with four jobs (vocabulary + appraisal map + world map + durability class), growing empirically when containment meets an untaggable act.
- [`docs/voice.md`](docs/voice.md) — **the speech layer** (audit gap C2): the `voice` BASELINE profile (register · vocab domains · rhythm · assertiveness · tics · code-switch · silence), **generated from the same formative stack** as everything else, consumed by the character turn (stable prefix) and narration (POV texture); the **craft standards get a home** (`books/standards/` — An Axle imported from writers-desk; criterion #6 is explicitly unsatisfiable until then, visible instead of dangling); tested by blind voice-attribution mid-sim.
- [`docs/multi-character.md`](docs/multi-character.md) — **group conversation & 3+ debate**: turn-order, sides, interruption, and silence **emerge** from a per-character **urge-to-speak** scheduler (stake + addressed + disagreement-pressure + affect − inhibition), never round-robin. **Addressing** threads the back-and-forth; **sides emerge** from value-alignment; **stance dynamics** (with the backfire effect) give the debate its arc and explain why it polarizes. The biggest risk is debate-specific: the LLM's pull to **harmonize flattens disagreement** — characters must hold. The maximal stress test of the consolidation keystone.
- [`docs/trait-theory.md`](docs/trait-theory.md) — the dispositional-trait layer (OCEAN hierarchy → facets, HEXACO's Honesty-Humility, Dark Triad as low-H, whole-trait tracking) + the **decision: go fine-grain**, and how out-of-character behavior works (distribution tails)
- [`docs/self-and-perception.md`](docs/self-and-perception.md) — three diverging views of one person (ground truth vs self-image vs others-see); villains aren't villains to themselves; self-deception = self-image≠behavior
- [`docs/decision-engine.md`](docs/decision-engine.md) — **roadmap #1 (started)**: how the variable weights resolve into a choice — *tracked numerically, resolved narratively* (no code-side weighted-sum); hard→soft spectrum; weights as a function of baseline×state×situation×relationship; **weight-bearing layers 1·3·5·7·10** (operands 1/3/5/7, resolver 10)
- [`docs/state-engine.md`](docs/state-engine.md) — **exactly how state is computed**: the **three tiers** (temperament → current → effective) and the gap-fill — the **appraisal module** (event → emotion delta via dimensions × value-relevance × trait-sensitivity) + **decay** (time → temperament), with the **event-vs-condition rule** that stops appraisal and the catalog double-counting. The runtime face of the generative model; answers "two equally-brave people, different acts" by computation.
- [`docs/baseline-generation.md`](docs/baseline-generation.md) — **the keystone: where every per-character number is born**. Built once at creation by sparse bias from a grounded zero-point — **species prior ⊕ genetics ⊕ formative stack** (culture · class · environment · personal history) → the baseline (content + the Layer-10 baseline Model). Zero-point is the species prior (from the world's peoples), never "all 5s"; every number carries provenance; principals authored-backward / validated-forward. Feeds `state-engine.md` tier 1.
- [`docs/arc-engine.md`](docs/arc-engine.md) — **durable change: trauma debuffs, eudaimonic buffs, the through-line** (`character-model.md` roadmap #3, now designed). Not a new mechanism — **appraisal with a durable write**: the same event-impact that spikes transient state instead diffs the *baseline* when it overwhelms coping + strikes something core. The **menu sets the type** (betrayal→trust↓, mastery→competence↑); **resilience forks damage vs growth** (same event, PTSD or wisdom). **Unifies with `baseline-generation.md`** — generation is the arc pre-run to page one; backstory and arc are one engine.
- [`docs/values-and-stakes.md`](docs/values-and-stakes.md) — **what's being weighed**: the menu of "worth" (needs / Schwartz values / moral foundations / concrete stakes), grounded; the model = a person's weighting over it; conflicts = the menu's built-in tensions
- [`docs/drives-schema.md`](docs/drives-schema.md) — **the Layer-3 operands**: goals / fears+wounds / orientation (locus, coping) as structured *opposable* fields the decision engine resolves; formalizes the drives≠values boundary (drives reference the menu; the Model weights it)

**The world** (the other half — now the probe's prerequisite)
- [`docs/world-model.md`](docs/world-model.md) — **SEED (to co-design)**: the world's job in the loop (circumstance + consequence + ground-truth facts), the same state+ledger+lazy-resolution architecture as a character, candidate world layers, and the open design questions
- [`docs/universal-law.md`](docs/universal-law.md) — **step-1 guide**: the *rubric* of law-questions every world-setup must answer (physical law · the supernatural switch · mind/soul/death · fate · cosmological structure/extent) — not which laws are true, but which must be decided; with the mandatory Limit (teeth) + Epistemic (known-vs-believed) checks
- [`docs/broader-community.md`](docs/broader-community.md) — **step-1.5 gate**: does the world stand alone or sit in a wider community of worlds/peoples? No → planet; yes → define it (membership · connection · structure · *this world's place* · contact · who-knows) *before* the planet, because the community constrains it
- [`docs/planet.md`](docs/planet.md) — **step-2 guide**: the physical stage *sized to what the story needs* (scope first, not a default globe) → geology/terrain · **resource spread** (the conflict substrate) · climate/biomes · ecology · **creature habitats** — all before the people; depth-rule dominant
- [`docs/history.md`](docs/history.md) — **step-3 guide**: the *why* of the present (causal chain, not chronology), authored backward from the premise's demanded present and validated forward; opens with the origin of peoples, ends loaded with live tension. 8 process rules (curate-to-premise · causes-not-dates · earn-by-conditions-not-fiat · backward/forward · inherit-upstream · hinges/recency · end-on-tension · no-contradiction)
- [`docs/present-systems.md`](docs/present-systems.md) — **step-4 guide**: the operating present, decomposed in dependency order (economy+culture → law → factions → ledger). The **specials hook** (planet/law diffs over each preset) + agnostic **legal · custom · economy · factions** presets (schema + archetypes + specials, per culture) + the **multi-culture** contact layer (dominance · pluralism · friction → factions + character-positions).
- [`docs/world-state-ledger.md`](docs/world-state-ledger.md) — **step-4 "state" half + the runtime spine**: the live *now* as machinery (event log + folded snapshot; write-path action→event→fold; read-path slice→circumstance→loop). Designs the structure + logic; **line items are runtime builds**, not authored content. **This is the run DB — world-truth canon in both modes** (see **The law**, above).
- [`docs/world-dynamics.md`](docs/world-dynamics.md) — **how the world pushes back** (world-model open-Q #3, answered): **state + appraisal + decay like a character, but no will — its will is the director, its books are the engine's.** Three channels, all landing as events: **rule-resolved consequence** (world-appraisal by rule; **future-dated events** for delayed pushback; **recurrence rates** for famine-class standing processes), **director-resolved choice within the engine-computed plausible-response envelope** (factions as collective characters — choosing outside the envelope is the forcing failure, world-scale), and **placed circumstance**. Time passes by lazy **fold-forward(Δt)** at read time (pure, replay-deterministic, depth-rule scoped — the world is correct when observed, never computed when not). Makes the probe's teeth **computable**: denial = rule-impossible or envelope-implausible. LLM resolves nothing here.
- [`docs/scene-assembly.md`](docs/scene-assembly.md) — **the runtime seam (WORKING)**: how world-state becomes the literal context a character acts from. **Two streams, one wall** — *perception* (apprehend the now, scoped to vantage/senses) + *recall* (the gate's vault slice) through the same epistemic boundary; **perception = acquisition-in-progress** (closes `world-model.md` open-Q #4). The 7-step assembly pipeline · the packet (stable-prefix / volatile-body for cache cost) · **fully deterministic** — no render LLM; outputs a structured PerceptSet, and the LLM lives only at the *decision* + *narration*.

**Output**
- [`docs/cutting-room.md`](docs/cutting-room.md) — **the 2nd risk, designed: what we do with the data. The shape is not a pipeline (the author, 2026-06-10) — it's decided in DISCUSSION over the record**, the way every other decision here gets made. The principle: **the conversation owns the choices; the engine owns the views and the checks.** **Views** (computed): the consequence graph, "what changed this person" (arc-engine diffs), candidate throughlines as causal chains, the tension profile of a proposed cut — diagnostics the room consults, never gates that decide. **The EDL** records the room's decisions (append-only, with NOTE rationale); every prose line traces to it, every entry to recorded events — the discussion is free, its output is structured, so faithfulness stays a **mechanical audit** (provenance / POV-wall / continuity). Rules discussed *within*: recall-anchored flashbacks, summary-as-compression, omission licensed / contradiction forbidden, Chekhov flagged by graph reachability. Names the run-time constraint (POV-candidacy = recording depth during the sim) and stays consumer-agnostic (novel is one cut of the record). Ends with the **cut probe** (faithfulness / shape / distinctness / transcription-baseline control). Records the rejected same-day pipeline draft.
- [`docs/narration.md`](docs/narration.md) — "who says this?": a POV-bounded narrator (= the POV's vault), not omniscient — the second knowledge boundary

**De-risk**
- [`docs/probe-plan.md`](docs/probe-plan.md) — the make-or-break test that gated the engine build — ran, passed (see **Status**)
- [`docs/measurement.md`](docs/measurement.md) — **the measurement layer** (audit gap C1 — the probes were gated on detectors that didn't exist): state-sanity detectors (bounds/saturation/drift/oscillation/conservation, all mechanical), coupling detectors + the blind **longitudinal identity check** (acceptance #2's attribution test run *during* the sim), the **consistency critic designed** (mechanical floor + escalation LLM + the append-only `correction` event protocol), **judge protocols** for every probe judgment (role-separation, blinding, anchored rubrics, n≥2 + agreement, planted controls), and the **sequence-forcing audit** (C4 — the salami detector: option-set narrowing across consecutive director placements, surfaced to the room).
- [`docs/run-lifecycle.md`](docs/run-lifecycle.md) — **runs outlive sessions** (audit gap C3): the durable run-state inventory, the atomic **turn-commit** (idempotent retry by construction), scene-boundary checkpoints, resume = snapshot + log-tail replay with determinism asserted (divergence aborts loudly), API-failure parking (never half-written), model-version changes as run events, and the **budget governor** (per-run token ledger, soft per-scene budgets that surface instead of halt, run-level projection at 20% not at the invoice).
- [`docs/prior-art.md`](docs/prior-art.md) — **what's paved, what isn't** (deep-research, 2026-06-10; 26 sources, 25 claims adversarially verified): compute/generate split = **validated convergent practice** (AI Town ships it; "Hybrid Constitutional Architectures" names it); belief vaults **prefigured by Talk of the Town 2015** (lift their false-belief taxonomy); thought-vs-action split **empirically motivated** by Project Sid's documented incoherence failure; **unpaved**: lazy fold-forward as architecture, director-by-circumstance with refusal-as-integrity, and novel-grade prose with per-line provenance (the curation problem is the field's named bottleneck — Ryan). Plus the verified failure-mode catalog (cost blowup, hallucination cascades, long-horizon drift, lockstep waste) mapped to our mitigations.

**Orchestration & operating** (both modes read these — Mode B's showrunner calls the same scripts they document)
- [`docs/orchestration.md`](docs/orchestration.md) — **the showrunner, designed**: the process-brain that runs a whole book premise-to-manuscript, calling each specialist as a subagent, gating every seam, keeping the canonical notes. The wiring behind `.claude/agents/showrunner.md`.
- [`docs/guide-operating.md`](docs/guide-operating.md) — running books on the engine: recipes in execution order (start a book, lint, run a burst, run a scene, review, narrate, cut, inspect, resume/recover).
- [`docs/guide-content.md`](docs/guide-content.md) — authoring world/character JSONs: what each field DOES, live vs inert.
- [`docs/guide-engine.md`](docs/guide-engine.md) — working ON the engine: contracts, invariants, extension.
- [`docs/guide-continuing-the-story.md`](docs/guide-continuing-the-story.md) — what to author per generation step, and how much data drives each step.
- [`docs/driving-the-engine.md`](docs/driving-the-engine.md) — deep operational patterns: burst discipline, model choice, measured results.
- [`docs/agent-toolboxes.md`](docs/agent-toolboxes.md) — the standard every agent's skill toolbox follows: layout, wiring convention, progressive disclosure, the open/forkable stance, and the agent→toolbox roster.
- [`runs/_TEMPLATE/README.md`](runs/_TEMPLATE/README.md) — the per-book process-notes skeleton: copy to `runs/<slug>/` to start a book, either mode.

## Design completeness (audited 2026-06-10)
**Designed — the engine, end to end (now built; see Status, above):**
- *Character:* generative-model (spine) → **baseline-generation** (genotype + species-prior + formative stack) → **state-engine** (temperament → current → effective; appraisal + decay; severity = weapon × skill × context) → **arc-engine** (durable change; trauma/eudaimonic) → decision-engine (both-sides collision, catalog, no-argmax) → values-and-stakes (worth menu + harm-from-the-menu) → drives-schema · trait-theory · relationships · knowledge-model (vault) · relevancy-gate · recording-model · self-and-perception · character-model → **character-schema** (the consolidated stat block).
- *World:* world-model → universal-law → broader-community → planet → history → present-systems → world-state-ledger → **world-dynamics** (consequence: three channels, fold-forward, computable denial — the last runtime gap, closed 2026-06-10). (Workflow locked: premise → law → planet → history → present.)
- *Runtime:* **scene-assembly** (deterministic perception → PerceptSet) → **consolidation-loop** (THE keystone — recorded-event accuracy) → narration (POV-bound output).
- *Output:* **cutting-room** (the record → a shaped work, decided in discussion not by pipeline: computed views + EDL decision-record + mechanical faithfulness audits; designed 2026-06-10 — risk discharges at its probe, not at design).
- *Multi-character:* **conversation + 3+ debate** (urge-softmax scheduler, stance dynamics + backfire, convergence; `claude-suite` as proven prior art).
- *Architecture:* the **compute/generate split** + **value-granularity rule** (`design.md`); the probe reprioritization — **coupling > prompt-following**, faithfulness = prompt-structure (`probe-plan.md`, `scene-assembly.md`).
- *Orchestration:* the **showrunner** (`docs/orchestration.md`) — the process-brain, designed and authored as agents (2026-07-23); see **Status**, above, for its run status.

**Audited + repaired (2026-06-10):** full 191-agent design audit (`docs/audit-2026-06-10.md`) — four invariants held clean across 33 docs (one seam: the Director-set-DC fiat option, now **removed** from `relevancy-gate.md`); 26 confirmed findings all repaired same-day: the keystone contradiction (design.md rewritten to actor-self-report), the record-thinner-than-its-consumers class (→ `record-contract.md`), undefined arc operands (durability/resilience now sourced), and the three missing sections (→ `measurement.md`, `voice.md`, `run-lifecycle.md`).

**Open in design (what genuinely remains):**
1. **Nonverbal / surface layer** — body language + the observable cues an outside observer reads (`character-model` gap).
2. **World-bible retrieval** — retrieval over the world canon at book scale (flagged as prior-art reuse, not yet specified).

**Not design — pending:**
- **Calibration:** every threshold/coefficient (decay rates, urge weights, severity constants, genetics alleles). Numbers, not structure; probe-tuned.
- **The probe: RAN.** Coherence + director-circumstance probes passed (`CLAUDE.md` Status). `tests/coherence_probe.py --run --db` is the real-LLM path; `tests/probe_director_circumstance.py` is the scaffold it grew from.

**Two risks, not one:** director-via-circumstance + coherence are de-risked (probes passed, above). The **cut** (life → novel) is designed (`cutting-room.md` — discussion-driven, not a pipeline) but unproven — its probe (faithfulness / shape / distinctness / transcription-control) is the one gate left in the sequence.
