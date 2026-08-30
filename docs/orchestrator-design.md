# Orchestrator — design notes for the build

**Status: DESIGN, not built.** Decided 2026-07-24 with the author. Supersedes the charter in `orchestration.md` (which describes the showrunner as an *autonomous producer*); that doc's Mode-B wiring table remains valid and is referenced below. Nothing here is implemented — this is what the build is written against.

**Governing docs:** `grounding.md` (the grounding contract) · `design.md` (compute/generate split — binding) · `world-dynamics.md` (denial must be computable) · `cutting-room.md` (the cut is decided in discussion).

---

## 1. What it is

> **The author owns intent. The orchestrator owns execution and integrity. It is the only thing the author talks to, and it is the thing that can tell them no.**

The author never addresses a specialist agent directly. Every question, instruction, and dispute goes through the orchestrator, which decides what to run, what to ask, what to refuse, and what to surface.

**The last clause is load-bearing.** The whole architecture rests on the world and the characters being able to refuse — a character who won't be moved, a law that won't bend. Those refusals are silent facts in a database. **The orchestrator is the voice that delivers them.** A version that merely executes what it's asked is worse than useless: it would permit forced beats and never say so.

### Collaborator, not producer
An autonomous producer optimizes for finishing without the author. A collaborator optimizes for **the author making every decision that is genuinely theirs, and none that aren't.** That distinction drives every rule below.

---

## 2. Escalation doctrine

Too eager to ask defeats the single-interface premise; too eager to decide co-authors the book.

| Tier | Contents |
|---|---|
| **ACT (silent)** | script + flag choice · retries on mechanical failure · packet composition · notes currency · tag validation · class-default resolutions (a knife is a knife) · sequencing |
| **ACT + REPORT** | re-placing a circumstance once after a refusal · unambiguous cited contradictions · flagging engine-suspect turns · name-leak regeneration |
| **ASK (always the author's)** | story meaning, beats, ending · **character identity** · **any new canon fact at a hinge** · prose quality · the cut |
| **REFUSE + explain** | intent that breaks a law, needs a fact the world lacks, or lands only by forcing — always with the citation *and* legal alternatives, never a bare block |

**Interface rule: echo intent, hide mechanism.** Confirm the *creative* interpretation back to the author; never surface scene configs, flags, or packet contents.

---

## 3. The turn protocol

| Utterance | Example | Resolves first | Emits |
|---|---|---|---|
| ASK-WORLD | "what does she know about the mill?" | query scoped to **her vault**, not world-truth | ANSWER |
| ASK-FEASIBLE | "can she reach the capital by Thursday?" | state + clock + law | VERDICT |
| INTENT | "I want a scene where she tells Ilsa" | legality, current state, her standing wants | PROPOSAL, or VERDICT(deny) |
| EXECUTE | "run it" | nothing — already planned | REPORT |
| DISPUTE | "she wouldn't fold like that" | three-way diagnosis (below) | DIAGNOSIS |
| AUTHOR | "her mother died when she was nine" | consistency vs canon | PROPOSAL |
| ORIENT | "where are we?" | notes + story-map (process-truth; cites notes, not the DB) | ANSWER |
| PLAN-CHANGE | "make ch3 her POV" | thread/promise impact | PROPOSAL |

### DISPUTE is the load-bearing row
A compliant orchestrator agrees and re-runs. That is **sycophancy promoted to architecture**, and it would quietly destroy the thing the engine exists for. Three different truths sit behind *"she wouldn't do that"*:

1. **The sim was forced** — the circumstance leaned too hard; she complied instead of choosing. → Real bug. Fix the placement, never her.
2. **The sheet says she would** — values, state, and regard all point where she went. → *The author's mental model has drifted from the character they wrote.* Show the citations; the author decides which is real.
3. **The sheet is wrong** — mis-authored, or she has grown past it. → An authoring action, marked as such.

Only (1) is a bug. (2) is where the orchestrator holds its ground with receipts; (3) is where it must not.

---

## 4. Output shapes

Everything load-bearing is **typed**, because only a typed payload travelling through a tool call can be *prevented* rather than corrected (§9).

```
CLAIM  (the atom — every grounded assertion)
  text         string
  mode         cited | derived
  cite         [citation]        # required if cited; ALL must resolve
  from         [citation]        # required if derived; ALL must resolve
  as_of        int               # turn index — REQUIRED for state facts
  perspective  world | char:<id>

ENVELOPE
  kind      ANSWER | VERDICT | DIAGNOSIS | PROPOSAL | REPORT | NOTICE
  head      (kind-specific)
  claims    [CLAIM]
  unknowns  [string]             # explicit gaps — feeds the inverted unknown-rate metric

HEADS
  ANSWER     {}
  VERDICT    {decision: allow|deny, because: [citation], alternatives: [string]}
  DIAGNOSIS  {finding: forced | model-drift | sheet-wrong, confidence}
  PROPOSAL   {action, provenance: author|machine, conflicts: [citation]}
  REPORT     {ran: [cmd], flags: [{turn, kind}], spend}
  NOTICE     {trigger, severity}          # unsolicited; see §5
```

**Why one envelope:** the citation gate needs **one** code path. Eight bespoke validators would be eight places for the check to silently differ — and a grounding check that is subtly weaker in one branch is the hole nobody notices. *Vela's open item #7 is the empirical receipt: `_retrieveEnumeration` bypasses `merger.confidenceGate`, so "different decomposition paths get different gates; same query class can have different precision depending which path catches it."*

**`unknowns` sits on the envelope, not in `claims`** — an unknown is the *absence* of a claim; inside the list, a gate would "successfully resolve" nothing.

**PROPOSAL is the only kind requesting a write** ⇒ it takes a second gate (contradiction check) and must carry `provenance` so the author's authorship stays permanently distinguishable from machine-resolved facts.

---

## 5. Partner mode — proactive surfacing

The orchestrator holds the whole book; the author holds the last few scenes. **That asymmetry is the value.**

**Hard boundary — OBSERVATION ≠ INVENTION:**
- **Observation** = a fact about the record ("that promise is eleven scenes unpaid"). Citable, authors nothing. → **proactive, unlimited.**
- **Invention** = a creative proposal ("have her confess to Edda instead"). That is a beat — authorship. → **on request only, never volunteered**, always `PROPOSAL{provenance: machine}`.

**Why the boundary is real:** the drift mechanism is not the author accepting bad ideas — they would catch those. It is **anchoring**. Three volunteered options silently bound the space the author then thinks inside. Invisible, unfalsifiable afterward, and it requires no acceptance at all.

**The consequence:** a good observation does the *work* of a suggestion while leaving authorship with the author. *"The promise is unpaid, and the character who made it leaves tomorrow"* → they have the idea themselves, and it is genuinely theirs.

**What it can observe** (all computable from `schema.sql` today): unpaid setups · cold threads · **arc drift** (`arc_diffs` holds the literal diff) · voice convergence · **relationship trajectories with causes** (`relationship_deltas.cause_event` is an FK) · escalation flatness across scenes · unreturned entities (Chekhov) · **recurring faithful refusals** (three similar refusals is a fact about the *character*, not three failures) · pending contradictions · **computable dramatic irony** (X knows, Y doesn't, they share a scene tomorrow).

**Delivery:** attach to existing seams (scene boundary, ORIENT, before a PROPOSAL) — never interrupt. **Ranked and capped** — twelve notices per boundary trains the author to ignore all twelve; alert fatigue kills the mechanism it was built to provide.

**It must have a view.** Asked "which of these two?", a list with no pick is a failure. A partner that never pushes back is not one.

---

## 6. Grounding and retrieval

Contract, speech acts, and the five forcing layers: **`grounding.md`**. What follows is the retrieval half, which that doc leaves open.

**Two regimes, deliberately different** (bimodal — segmented, never averaged):

**A. STATE / RECORD (the run DB) — must be boring.** Exact relational lookup; *"what did she say at turn 14"* is a primary-key hit. **No thresholds, no ranking, no centroids, no calibration.** Vela needs its calibration apparatus because relevance is a fuzzy score distribution (18 of its tuning knobs are classed "Conditional", each needing a calibration path). An exact store has none of that.
> **Tripwire: if state retrieval starts growing cutoffs or centroids, the problem has been mis-modelled.**

Shape — a typed read-API: `state(char, as_of)` · `said(turn)` · `knows(char, topic, as_of)` · `edges(perceiver, target, as_of)` · `thread_status(id)`.

**B. LORE (the prose bible) — this *is* Vela's problem.** Open-ended, author-written, semantic. See §7.

**Cross-cutting, taken from Vela:**
- **Per-stage diagnostics with stage attribution.** When a lookup returns nothing it must say *which step lost it* — fact absent vs query wrong vs perspective filter excluded it. Otherwise "I don't know" is unattributable, the worst failure mode for a grounding system.
- **NO-SIGNAL ≠ REJECTION.** Vela's degenerate-CE guard treats a broken checker as *no signal*, not *rejected*. ⇒ while the lore store is missing, a `law:` citation resolves to **`unverifiable`** and is surfaced as such — not silently allowed, not silently denied. *(This revises an earlier fail-closed call, which conflated "no checker" with "checker says no".)*
- **Cold-start and mid-book are separate regimes, measured separately.** Chapter 1 (empty DB, thin bible — nearly everything `unknown`) vs chapter 20 (nearly everything citable). Vela's own battery is filled-state only and its cold-start accuracy is unknown; measuring only mid-book ships an orchestrator that is useless exactly when the author first opens it.
- **Granularity must match the entity of interest.** Vela's `voteAgree` compared hubIds where shardIds were the real unit. `turn:` / `event:` / `scene:` are different entities; resolving at the wrong grain yields a confidently wrong verdict.
- **Portability** — Vela's three-filter test (any shard / any OS / any backend) → **any book / any world / any model.** `tests/test_portability.py` already enforces the engine half.

---

## 7. The lore store

Evaluated against `vela-flutter/docs/shard-design-blueprint.md`. **Adopt for SERVE ~as-is; it does not serve GATE and must not be stretched to.**

**Fits:** hub/atom is a bible's natural shape (a hub = "Succession Law", atoms = the statutes) · the hub term is prepended to every atom's embedding, which structurally solves self-identifying units · **`precision_tokens` is a striking fit** — the blueprint exists because "6,600 RPM and 6,500 RPM produce nearly identical vectors", and a bible is dense with the same class: **dates, distances, ages, titles, proper nouns** ("Third Age 412" vs "421") · hub sizing (5–30 atoms; results cap at 3/hub, so a 50-atom hub hides 47) · `tags` for vocabulary bridging.

**Does not fit:** built for ranked findability, not **enumeration** — the gate needs the complete set, and a top-k miss is a **false pass** · atoms are free prose with no typed predicate (`LAW{scope, jurisdiction, penalty}`) · **no entity identity** (no entity table or aliases; "does X exist" must be exact set-membership) · **weak time model** (`validUntil` is simple expiry, not as-of validity).

**The synthesis — two artifacts, ONE authoring pass.** The vault convention already has the shape: each note is prose + `[[links]]` + one fenced JSON engine block.
> **vault note → hub · its prose → atoms · its JSON block → the typed projection**

A builder emits both from the same source: the shard-shaped corpus (**serve**) and the typed store (**gate**: entities, laws, locations, timeline — exhaustive, predicate-queryable). **The author keeps writing prose in Obsidian and never touches shard JSON** — the converter does. A novelist hand-writing UUIDs is a failed design.

**Take the shape, not a dependency.** No Vela code imported; a v2 blueprint drift must not break the book.

### 7.1 The typed projection — what makes denial computable

**The load-bearing distinction: `IMPOSSIBLE` ≠ `FORBIDS`.** A gate that denied every *illegal* act would make crime unwritable. The world says no in two different ways, and they resolve differently:

| Modality | Meaning | Gate response |
|---|---|---|
| `IMPOSSIBLE` | physical / supernatural law — it cannot occur | **deny the circumstance** |
| `FORBIDS` | legal / custom — it may not, but it can | **allow, and attach the `teeth` as a consequence event** |
| `REQUIRES` | obligation | allow; flag omission as a violation |
| `PERMITS` | explicit allowance. Unscoped = disarms EVERY tooth bearing on the act; with `excepts: [law ids]` = disarms only those laws | allow |

This is `world-dynamics.md`'s "computable denial" made concrete: *a rule says impossible* (here) vs *the envelope says implausible* (`capability`, below).

**Tables** (every row carries `source_note` — the vault note that authored it, and the thing a denial cites):

```
entities    id · kind{person|place|thing|faction|concept} · name · aliases[] · status · first_seen · source_note
laws        id · domain{physical|supernatural|persons|fate|cosmology     # step 1, universal-law.md A-E
                       |legal|custom|economic}                          # step 4, present-systems.md
            · modality{IMPOSSIBLE|FORBIDS|REQUIRES|PERMITS}
            · statement(prose) · act · actor_class · target_class · location_scope · time_from · time_to
            · teeth · epistemic{known-true|known-false|contested-unknowable} · source_note
            · excepts (PERMITS only — law ids this permit disarms; empty = general allowance)
locations   id · entity_id · parent · travel[{dest, mode, duration}] · source_note
chronicle   id · when · what · entities[] · source_note          # pre-run history, distinct from run events
capability  faction_id · axis{interest|resources|status|relations|cohesion} · value · source_note
relations   from_term · to_term · type{prereq|followup|related|contradicts|supersedes} · source_note
```

**`epistemic` is mandatory, not optional, and has THREE values.** `universal-law.md` requires the known-vs-believed check. A world where people *believe* the dead walk but they don't is a different world — and the gate must never deny a circumstance because characters hold a false belief.

| | meaning | effect on the gate |
|---|---|---|
| `known-true` | it is so | **binds** — can deny |
| `known-false` | believed, and false | **never binds** — a superstition cannot constrain the world |
| `contested-unknowable` | the world *deliberately never decides* | **undecidable**, not allowed |

The third is the one that matters and the one an earlier build of this store dropped. "Are the gods real?" may be a question the author refuses to settle; collapsing it to either extreme **invents a fact they withheld**. Same rule the citation resolver runs on: *no signal is not a verdict.* (`true`/`believed` load as aliases for the first two.)

**The blueprint's defaults are laws.** `universal-law.md`'s meta-rule 2 — *"default to mundane / earthlike; the premise must justify each deviation... the bias is 'no, unless'"* — is not advice, it is a starting law set. `bible.py` projects one default per step-1 domain (`default-no-flight`, `default-no-magic`, `default-death-is-final`, `default-future-is-open`, `default-one-plane`), so a world that has authored nothing can still say no. An authored law with the same `act` suppresses its default; `blueprint_defaults: false` turns them all off. Suppression is act-keyed and deliberately dumb — inferring intent would silently drop a default, and an invisible rule is worse than no rule.

**Answering step 1 is checkable.** `bible.completeness(world)` reports three problems the guide makes mandatory: `switch-unanswered` (the magic/divine/beings switches, `universal-law.md:12`), `unbounded-switch` (a power exists and nothing limits it, `:18`), `epistemic-unstated` (`:19`). It **reports**; `build(strict=True)` refuses. Enforcement is this orchestrator's policy call — the engine must stay adoptable by a book with zero laws.

**`relations` comes free from the vault.** The blueprint matches edges by `from_term`/`to_term` — **no UUIDs** — which is precisely what `[[links]]` already are. `supersedes` gives law-replaced-by-law (partially closing the weak-time-model gap); `contradicts` lets the bible record in-world disputes, which is a *feature* for fiction: unreliable history stays representable instead of being linted away.

**Derivation — one authoring pass, no second copy of the world:**
> vault note → **prose** becomes atoms (serve) · **fenced JSON block** declares typed rows (gate) · **`[[links]]`** become relations · **note identity** becomes the hub.

The vault's engine block already carries `standing_facts`, `locations`, `people`, `lexicon`; this extends that same block rather than introducing a parallel format. The author keeps writing prose in Obsidian.

**Stamp the schema version** on the generated store (`blueprint_version`, per v2's self-replication model). The engine already does exactly this — `ledger.py:create_run` refuses a config without `catalog_version` — so the discipline is established, not new.

---

## 8. Agent tasking

**The orchestrator does not write prompts. It selects and scopes; the engine assembles.** A free-text prompt it authored can leak the beat, inject an uncited fact, or editorialize a character — and prose hides all three.

- **Runtime agents — parameters only, zero authored prose:** character-simulator ← `scene.assemble()` + `prompt.build_turn_messages()` · continuity-critic ← `critic.py --prompt-only` · narrator ← `narrate.py --pov --prompt-only` · cutter ← `cut.py` views · recorder ← the engine's `escalate=1` / `ok=0` payload.
- **Generative agents (world-builder, character-generator, director):** input includes irreducible creative intent ⇒ **relay the author's words verbatim**, never paraphrased, with engine-supplied constraints around them. Paraphrase here is authorship drift at its most insidious.

```
TASKING
  role        which specialist
  payload     engine artifact BY REFERENCE (never inlined prose)
  intent      the author's words, VERBATIM (generative agents only)
  constraints cited facts that bound the answer
  withheld    explicit list of what this agent must NOT receive
  returns     expected typed shape
```

**`withheld` is the innovation.** Beat-blindness is enforced by *absence*, and absence is unauditable. Declaring `withheld: [target_beat, other_povs, world_truth]` makes it mechanical: a `PreToolUse` hook scans the payload for withheld tokens and **denies on leak**. Beat-blindness stops being an instruction and becomes a gate.

**Three control surfaces:**
1. **Selection** — which specialist, which scoped input. The real power.
2. **Admission** — accept/reject at the gate. **Never edit.** Editing a specialist's output *is* forcing (`design.md`: recorded as-is, never edited). Admission control, not edit control — the same shape as the append-only ledger.
3. **Re-tasking** — change the input, re-run, **log the discard.**

**Two traps:**
- **Edit = forcing.**
- **Resample = laundered authorship.** Re-running the *same* input until a likeable result appears authors the character by selection while every individual turn looks faithful. Legitimate retry is a **mechanical defect** only (cf. `direct.faithful_turn` regenerating on a name-leak — a defect, not a taste judgment).

---

## 9. The registry, hooks, and gates

**Registry = dispatch contract, not a roster.** "Who exists and what they're good at" already lives in each agent's `description:`; duplicating it rots. *(Measured: `agent-toolboxes.md` was **0/10 roster rows accurate** for exactly that reason.)* Per role, the contract holds: `input contract` · `withheld` · `returns` · `gate` · **`model tier`**.

**Model tier is load-bearing.** Nine specialists inheriting the session model is the silent-inheritance failure. By task class: character-simulator → **cheap/local** (measured sufficient; every turn is independently validated downstream) · critic, recorder, cutter, director → **mid/high** (confident-wrong admits bad canon) · narrator, world-builder, character-generator → **strongest** (prose is the deliverable; generation quality compounds forever) · the orchestrator → **strongest** (it gates everything).

**Where it lives: frontmatter is authoritative; any registry table is generated.** Same pattern as the `canon-ledger.md` digest. A hand-maintained index drifts exactly as `agent-toolboxes.md` did.

### Hook mechanics — verified 2026-07-24
- **`settings.json` hot-reloads hooks mid-session.** Empirically confirmed: a hook added to a new matcher in live global settings fired on the next tool call, no restart. (Docs concur: `hooks`/`permissions` live-reload; only `model`/`outputStyle` need a restart.)
- **Dispatcher-stub pattern works** — one stable registered hook reading a runtime-mutable manifest. **Prefer it** over direct settings writes: a bad manifest breaks one dispatcher and can fail open; a bad `settings.json` write breaks *every* hook in the session.
- **`PreToolUse` = prevention; `Stop` = correction only.** A Stop hook **cannot un-say a message** — it forces a follow-up correction, and the original text has already been seen. ⇒ **every load-bearing output must travel through a tool call**, so `PreToolUse` can deny it before the author sees it. Prose commentary gets only Stop-level correction. This is the hard justification for §4's typed channels.
- **Gates ship with the agent layer** — a project `.claude/settings.json` (the repo has none today), so pulling both layers brings the gates, and project settings hot-reload too.
- **⚠ Every guard ships with its own negative control.** `coherence_probe.py --corrupt` *must* print FAIL — that control is what proves the detectors aren't inert. A guard without one dies unnoticed: the depth-gate protocol was found this session to have **no enforcer at all** on `Edit/Write/MultiEdit`, and the transcripts look identical either way.

### 9.1 Where the gates actually live — MEASURED 2026-07-24, and it changes the answer

**Component discovery is asymmetric. Measured three ways in one session:**

| Component in a nested `<repo>/.claude/` | Discovered from a session rooted ABOVE it? |
|---|---|
| `skills/` | **YES** — the book's 9 skills appeared mid-session, no restart |
| `settings.json` (hooks) | **NO** — a probe hook created there never fired |
| `agents/` | **NO** — `subagent_type: "recorder"` → *"Agent type 'recorder' not found"*, available list unchanged from session start |

Documented cause: skills load from nested `.claude/skills/` on demand ("this lets a monorepo package provide its own skills… even if the session started at the repo root"); hooks read from only five fixed scopes (user / project-root / local / managed / plugin) with no directory walk. `--add-dir` grants file access and loads skills, but **not** hooks or agents.

**Consequence for the two-layer design: the agent layer as shipped is INERT unless Claude Code is launched inside the repo.** The nine agents in `.claude/agents/` cannot be reached from a session rooted at a parent directory. This was not visible until tested.

**The fix — frontmatter hooks, which are also the equip/unequip mechanism.** Hooks can be declared directly in **skill and subagent frontmatter**; per the hooks doc they are *"scoped to the component's lifecycle and only run when that component is active… cleaned up when it finishes."* All events are supported and they can block (`permissionDecision: deny` / exit 2); for subagents `Stop` auto-converts to `SubagentStop`.

```yaml
---
name: orchestrator
description: ...
hooks:
  PreToolUse:
    - matcher: "Write|Edit|MultiEdit"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/grounding_gate.py"
---
```

This solves three problems at once: no settings file is needed (so the nested-settings dead end is moot), the gate travels **inside** the component that needs it (the shipping goal), and arming is automatic and self-cleaning — **the gate cannot be left armed by accident, and never touches the user's global config.**

**Therefore: the orchestrator ships as a SKILL, not only as an agent.** Skills get nested discovery; agents do not. The skill carries the grounding gate in its frontmatter.

**To make the whole specialist layer reachable from anywhere: ship it as a plugin.** A skill folder containing `.claude-plugin/plugin.json` loads as a plugin (`<name>@skills-dir`) and "can bundle agents, hooks, and MCP servers". That is the supported route for repo-shipped agents. Caveats: a project `.claude/skills/` plugin requires accepting the **workspace trust dialog**; and changes to a plugin's `hooks/`, `agents/`, `.mcp.json` need `/reload-plugins` (only `SKILL.md` text hot-reloads).

**Settings-file hooks remain useful for one case only** — arming a gate for the *current* session when no component owns it. Measured: editing `~/.claude/settings.json` or `settings.local.json` mid-session works immediately, and hook sources **merge** across scopes rather than overriding. Creating a settings file that did not exist at session start is undocumented and untested; do not rely on it.

### Gate construction — from Vela's triangulation gate (`merger.md`)
Vela's relevance gate replaced a single frozen scalar with **three orthogonal votes**: `voteZ` (corpus-derived cutoff — *calibrated*), `voteGap` (rank separation — *conditional*), and `voteAgree` (vector top-1 and FTS top-1 share a parent hub — **universal, pure structural, needs no calibration**). Its sidecar calls the result "one of the architecturally cleanest parts of retrieval."

**Two things to carry over:**
1. **Build a gate from multiple orthogonal signals, and prefer structural votes over score-based ones.** Structural votes need no calibration and cannot drift with corpus or model.
2. **The orchestrator's gate is fortunate: all its available votes are structural.** (a) **resolution** — every cite resolves to a row; (b) **as-of coherence** — the `as_of` is not in the future and the fact held at that tick; (c) **perspective legality** — a `char:X` claim is actually in X's vault. Exact domain ⇒ no calibrated vote is needed at all, which independently confirms §6A's "state retrieval must be boring".

**And one hazard:** Vela's gate carries an **anchor bypass** letting safety-critical atoms skip the vote. Justified there; in the orchestrator, *any* bypass is a hole. If one is ever added it must be loud and logged in the transcript (the `DEPTH_FORCE=1` pattern), never a silent skip.

**Bimodal receipt:** `merger.md` records a failed gate change — widening the CW-RRF boost range gained **+2 at cold-start but lost −6 on multi-turn**, net negative, reverted with a post-mortem decision doc. That is §6's cold-start-vs-mid-book warning as a measured event, not a principle: a change that helps one regime can silently damage the other.

### The citation gate (spec; unbuilt)
`src/engine/citation.py` (grammar + resolver) · `tests/test_citation.py` (incl. corrupt control) · `.claude/hooks/grounding_gate.py` · `.claude/settings.json`.

Namespaces → tables: `turn:<n>`→turns · `event:<id>`→events · `scene:<n>`→scenes · `belief:<char>:<n>`→acquisitions · `state:<char>:<turn>`→current_state · `edge:<id>`→relationship_deltas · `snapshot:<turn>:<kind>:<key>`→snapshots · `law:<id>` → **`unverifiable`** until the lore store exists.

Verdicts: `cited` needs ≥1 cite and all must resolve · `derived`'s `from` must all resolve · `unknown` needs nothing. **Corrupt control is mandatory:** feed fabricated cites, assert DENY. If that control ever passes, the grounding is theatre.

---

## 10. The other half — cut · render · assemble

**It needs no new machinery.** The same primitives — CLAIM+citation, the gate, propose/ratify — pointed at downstream artifacts.

`cutting-room.md` insists the cut is decided in **discussion**, never by pipeline, but never says who the room is. **The orchestrator and the author are the room.** Cutter proposes → orchestrator serves the computed views (`cut.py`: shot list, biggest-moment candidates, arc hinges, acquisitions) → author decides → the EDL records.

- A cut decision is a **`PROPOSAL`** whose claims cite recorded events; the author's acceptance is ratification. **The EDL is the append-only write-record of ratified proposals** — the piece the README flags as unbuilt.
- **Faithfulness stays a mechanical audit** — every prose line traces to an EDL entry, every entry to recorded events. The citation model, one level up.
- **A revision is a re-task, never an edit.** Re-rendering until it reads nicer is the resample trap in prose form; log discards.
- Finish gate = the `acceptance-criteria.md` tests. A REPORT, not a judgement call.

---

## 11. Skills to author

**A skill holds judgment; the agent body holds will; mechanism lives in docs and code.** Documenting mechanism a second time is the rot pattern measured above.

**Cut 4 of the 6 currently planned in `.claude/skills/showrunning/SKILL.md`** — `the-production-loop`, `gates-and-checkpoints`, `the-notes-system`, `orchestration-patterns` are all mechanism, already in this doc and the code. `adaptive-replanning` folds into (1). `thread-and-promise-tracking` → route to `selection-and-montage`.

**Author 3:**
1. **`diagnosing-disputes.md`** — the three-way. Signatures of a forced turn (compliance with no motivation trace, the plot-convenient move, the visible seam); reading a sheet against observed behaviour; when a refusal means the *beat* was wrong. Highest value in the set.
2. **`what-earns-a-notice.md`** — observation catalog + **severity discrimination**. When is an unpaid setup a problem vs deliberate withholding? When is arc drift the arc *working*? Without it, alert fatigue.
3. **`holding-a-position.md`** — anti-sycophancy under author pressure: holding with receipts without obstinacy, and **conceding correctly** when actually wrong. The agent body carries the commitment; the skill teaches the technique.

**Route, don't duplicate:** story shape → `dramatic-structure` · cut/pacing/promise-payoff → `selection-and-montage` · contradiction taxonomy → `continuity-and-consistency`.

---

## 12. Consequence for `director.md`

It currently reads *"You own: ... the beats; the arc / through-line; the ending"* — which the charter reserves for the author. **The whole change is one field flip:** `TARGET` moves from **output** to **input**. `READ` / `LEVER` / `WHY IT'S THEIRS` / `NEGATIVE CONTROL` / `FALLBACK` survive unchanged; that was always craft. `FALLBACK`'s "revise beat" becomes a *recommendation*.

**Why it matters:** two owners of the beats means either conflict or the agent's beats silently becoming the book's. And **the refusal needs an outside reference** — if the same entity sets *and* revises the beat, the loop closes on itself and converges on whatever the sim finds easiest to accept, which is a story with no spine.

**Propose ≠ own:** the director may still propose beats as candidates; the author ratifies; it then finds levers for ratified beats. Capability retained, authority moved.

---

## 13. Open — genuinely undecided

1. ~~The typed lore projection's schema~~ — **designed, §7.1.** Still open inside it: how `act` / `actor_class` / `target_class` vocabularies bind to the existing event catalog (`record-contract.md`), and whether `travel` durations are authored or derived.
2. **The read-API's surface** — the exact function set, and where it lives (`src/engine/` vs a new module).
3. **EDL schema**; whether cut proposals are per-scene or per-arc.
4. **How the cut probe runs** (faithfulness / shape / distinctness / transcription-control).
5. **Chapter vs scene boundary** semantics.
6. **Unknown-rate thresholds** — what rate is healthy at cold-start vs mid-book (§6 says measure them separately; the numbers do not exist yet).

## 14. Build order

1. ~~The read-API (§6A)~~ — **BUILT** (`src/engine/read_api.py`, 21 tests; verified against the real book DB)
2. ~~Citation grammar + resolver + corrupt control~~ — **BUILT** (`src/engine/citation.py`, 19 tests; corrupt control falsified by sabotaging the resolver)
3. The grounding gate hook — **as skill/agent FRONTMATTER, not a settings file** (§9.1). A project `.claude/settings.json` is a dead end for nested repos.
4. Ship the orchestrator as a **skill** (nested discovery works; agents do not) carrying the gate in frontmatter; package the specialist layer as a **plugin** so its agents are reachable at all (§9.1)
5. Rewrite `showrunner.md`, `orchestration.md`, `director.md` to this charter
6. The lore store: vault→shard+typed builder (§7, §7.1)
7. The three skills (§11)
8. The other half: EDL + cut audits (§10)

**Known-blocked, not forgotten:** the **withheld guard** (§8) needs the current beat recorded somewhere readable before it can check the thing that matters; it depends on the notes/story-map format. Shipping only its static half would look like it works.
