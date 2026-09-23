# Agent Toolboxes — the standard every agent's skill follows

**Every agent in this project carries a *toolbox*: a Claude Code skill it draws on while it works.** The agent definition is the *will* (who acts, and the hard rules it acts under); the toolbox is the *well* (the frameworks, menus, and exemplars it reaches into to act well). Keeping them separate is the whole point — a lean, stable agent that names its job, backed by a deep, swappable reference library that can grow or be forked without touching the agent.

This file is the **contract**: the layout, the file formats, the wiring, and the open/forkable stance — so the pattern is legible and anyone can stamp a new toolbox (or fork an existing one) without guessing. It governs the toolboxes; the toolboxes govern the agents' craft; `docs/` remains the design canon both point back to.

## Why a skill, and not prose inside the agent
The agent body (`.claude/agents/<name>.md`) is a **hot path**: loaded on every invocation, read under pressure, and holding the non-negotiables (the walls the agent must not cross). If the craft — every trait model, every value taxonomy, every worked example — lived there, it would be enormous, always-loaded, and impossible to fork cleanly. So the craft moves to a skill, which buys four things:

- **Progressive disclosure.** The deep material loads only when the moment reaches for it (see below). The agent stays small.
- **Forkability at a seam.** Swap one reference file to change a default; the agent and the router are untouched. The fork lands exactly where it should.
- **Reuse.** Two agents can draw on the same reference (the values menu feeds both the character-generator and the character-simulator).
- **Legibility.** One agent ↔ one named toolbox, registered in the roster table below — the map is one lookup.

## Anatomy — one agent, one named toolbox
A toolbox is an ordinary Claude Code skill under the project's `.claude/skills/`. **Skills carry thematic names, not the agent's name** — a toolbox is named for the craft it holds (`emotion-and-decision`, `worldbuilding-frameworks`), not for the agent that calls it. Each agent names its toolbox exactly once, in a **"Your toolbox"** section in its own body (see the wiring convention below). The agent-to-toolbox mapping is not inferrable from either name alone — **the roster table below is the registry**; look there. Agents and skills still live in different namespaces (`.claude/agents/` vs `.claude/skills/`), so nothing collides either way.

```
.claude/
├── agents/
│   └── character-simulator.md        # the agent: will + hard rules (hot path)
└── skills/
    └── emotion-and-decision/         # its toolbox (a thematic name, not the agent's)
        ├── SKILL.md                  # the router: index + when-to-load pointers (<500 lines)
        └── references/               # the well: one deep file per framework-cluster
            ├── appraisal-theories.md      # planned
            ├── theory-of-mind.md          # planned
            ├── naturalistic-decision.md   # planned
            └── …
```

Optional sibling dirs the skill spec allows — `scripts/` (deterministic helpers) and `assets/` (templates) — are available but rarely needed for a reference toolbox; most toolboxes are `SKILL.md` + `references/` only.

## Progressive disclosure — the three levels
Skills load in three tiers; a toolbox is designed to exploit all three so the agent pays only for what it uses:

1. **Metadata** (`name` + `description`, ~1–2 sentences) — the pointer the agent resolves by name. Always cheap.
2. **`SKILL.md` body** — loaded when the agent opens its toolbox. This is a **router, not a manual**: a terse index of what lives in `references/` and *when to pull each file*. Keep it under ~500 lines; if it grows, push depth down into `references/`, not out into the body.
3. **`references/<topic>.md`** — the deep files. Loaded one at a time, only when the task hits the trigger the router named. Unlimited in aggregate; each is read in isolation.

The discipline: **the router routes; the references teach.** An agent mid-turn reads the router to find the one file it needs, reads that file, and never loads the other nine.

## The reference-entry file format
Every file in `references/` follows the same shape so a forker knows where to cut and an agent knows what it's getting. A reference entry is an **operational digest** — the "how, right now" — not a re-derivation of the design. Keep it terse; match the repo voice.

```markdown
# <Topic> — <the one question this file answers>

**When to load:** <the trigger — the situation in the agent's work that should pull this file>
**Canon:** `docs/<source>.md` <the design doc this digests; that file is the source of truth>

## The menu (framework-neutral)
<Several frameworks, presented as peers — a well to draw from, not a ladder.
 Name each, one line on what it's good for, one on where it breaks.>

## Repo default → <named default>
<The default this project runs, flagged explicitly as a REFERENCE POINT, not a rule.
 One line on why it's the default here. State plainly that a fork may swap it.>

## In practice
<1–3 vivid, concrete examples — the load-bearing part. Show the framework doing work,
 not defined in the abstract. Use real fixtures where possible.>

## Limits
<Honest edges: what this framework can't decide, where it double-counts, when to
 escalate to another reference. Never oversell.>
```

Rules that keep entries trustworthy:
- **Canon lives in `docs/`, once.** A reference file *digests* a design doc for work-time use and links back to it; it never becomes a second, drifting source of truth. If the reference and the doc disagree, the doc wins — fix the reference.
- **Plural by default.** Present the menu of frameworks before naming a default. The default is one entry in the well, marked as swappable — never the only door.
- **Examples over definitions.** The vivid, concrete instance is what makes a reference usable; a taxonomy without a worked case is inert.
- **Cite real sources; invent nothing.** Trait models, value taxonomies, and their attributions must be accurate — a fabricated dimension name poisons every agent that draws on it.

## The wiring convention — how an agent points at its toolbox
An agent adopts its toolbox with two small, explicit moves — no magic, no auto-binding:

1. **Grant the tools.** The agent's frontmatter `tools` must include `Skill` (to open the toolbox) and `Read` (to open individual reference files). E.g. `tools: Read, Skill`.
2. **Name the toolbox in the body.** A short *"Your toolbox"* section names the skill and says the agent should consult it — routing through the `SKILL.md` index to the reference the moment calls for.

```markdown
## Your toolbox
Your craft library is the `emotion-and-decision` skill. When a choice turns on how
this person weighs a conflict, how a trait tips behavior, or what a value is worth,
open the toolbox and pull the reference its router points you to. The toolbox holds
*craft* — how to act faithfully — never *facts*; character and world facts reach you
only through the context packet.
```
*(the real wiring of the `character-simulator` agent — note the thematic skill name)*

Two properties of this wiring:
- **By-name, not by-competition.** An agent consults *its* toolbox deterministically, because the body names it — it does not compete in the global skill auto-trigger pool. So a toolbox `description` is for human legibility, not for winning a triggering contest; write it plainly.
- **Craft, not omniscience.** Reading your own toolbox is reading *how to do your job well*, which never violates an agent's knowledge walls. The `character-simulator`'s hard rule — *never go looking for the wider world* — bars reading world/character **facts** outside the context packet; it does not bar reading craft references about how to be a person. The toolbox is disciplined to hold only craft, so the two never blur.

## Open and forkable — the standing stance
This is an **open, forkable** toolbox corpus. The frameworks in `docs/` and the defaults the references name are **reference points, not rules.** The stance, concretely:

- **Framework-neutral.** Where a real design choice exists, the reference presents the field — OCEAN *and* HEXACO *and* the Dark-Triad-as-low-H reading (`docs/trait-theory.md`); Schwartz values *and* Moral Foundations *and* Maslow needs (`docs/values-and-stakes.md`) — as a menu, never one prescribed truth.
- **Swappable defaults.** The repo *does* pick defaults, so an agent has something to run — but each is flagged in its reference as this project's choice and marked swappable. A fork that wants a culture-specific trait model replaces one `references/` file; the agent, the router, and every other toolbox are untouched.
- **Fork at the seams.** The seams are deliberate: the reference file is the unit of replacement, the router is the stable index above it, the agent is the stable will above that. A fork edits the layer it disagrees with and inherits the rest.
- **Honest about limits.** Every reference states where its frameworks break. The corpus is a well to draw from with judgment, not a pipeline to obey.

## The roster — agent → toolbox → purpose
Every agent in the pipeline (`docs/design.md`: the four generative LLM calls, plus the director/critic/generation/output/de-risk roles) gets a toolbox on this standard. Status: all 9 agents and all 9 toolboxes exist. One of the 9 — `character-frameworks` — is fully authored (8/8 `references/` files). The other 8 are router + planned index: each `SKILL.md` is complete and names its reference files, but the files themselves are pending a later authoring pass (69 references total; each skill's own `references/_index.md` outlines them).

| Agent | Toolbox skill | One-line purpose | Status |
|-------|---------------|------------------|--------|
| `character-generator` | `character-frameworks` | Draw a character from the built world: position → formative stack → baseline. | Built — toolbox fully authored (8/8 references) |
| `character-simulator` | `emotion-and-decision` | Be one person for one turn and act faithfully, blind to the beat. | Built — router + planned index (7 references pending) |
| `continuity-critic` | `continuity-and-consistency` | Validate a canonized scene against bible + ledger; guard distinct voices. | Built — router + planned index (10 references pending) |
| `cutter` | `selection-and-montage` | Select, order, and escalate biographical moments into a shaped novel. | Built — router + planned index (6 references pending) |
| `director` | `dramatic-structure` | Steer lives by placing circumstance; own beats + ending; never force. | Built — router + planned index (9 references pending) |
| `narrator` | `narrative-craft` | Render the cut of biographies into POV-bounded prose. | Built — router + planned index (11 references pending) |
| `recorder` | `event-semantics` | Read the recorded `{thought, action}` stream → structured event-tags. | Built — router + planned index (9 references pending) |
| `showrunner` | `showrunning` | Run the whole book: call each specialist, gate every seam, keep the notes. | Built — router + planned index (6 references pending) |
| `world-builder` | `worldbuilding-frameworks` | Build the grounded world once: premise → law → planet → history → present. | Built — router + planned index (11 references pending) |

**Retired roster rows** — named in an earlier draft of this roster, never built: `scene-framer` (superseded — scene assembly is the engine's deterministic job, `src/engine/scene.py`; no agent role) and `judge` (probe-era judging; its function is covered by `continuity-critic` + `docs/measurement.md`).

Each of the 8 not-yet-authored toolboxes now states its own graceful-degradation rule in its `SKILL.md`: if a routed reference is still missing, the agent acts on the index's one-line summary for that entry and proceeds — it never stalls on, or invents, the file.

Each toolbox's `references/` are digests of the `docs/` files that role draws on — e.g. `character-simulator` digests `character-anatomy` · `character-schema` · `decision-engine` · `drives-schema` · `values-and-stakes` · `trait-theory` · `self-and-perception` · `relationships` · `knowledge-model`; `world-builder` digests `universal-law` · `broader-community` · `planet` · `history` · `present-systems` · `world-state-ledger`. The `docs/` file stays canon; the reference is its work-time face.

## Stamping a new toolbox — the minimal checklist
1. `mkdir -p .claude/skills/<skill-name>/references` — a thematic name for the craft, not the agent's name.
2. Write `SKILL.md`: frontmatter (`name: <skill-name>`, a plain one-line `description`) + a router body listing each `references/` file and its *when-to-load* trigger.
3. Write each `references/<topic>.md` on the format above: **When to load · Canon · menu · repo default (swappable) · in-practice examples · limits.**
4. Wire the agent: add `Skill` to its `tools`, add a *"Your toolbox"* section naming the skill.
5. Add the row to the roster table above.
6. Keep every reference pointed at its `docs/` canon — digest, don't fork the source of truth.

The worked instance to copy from: `.claude/skills/character-frameworks/` — the one fully-authored toolbox (8/8 references, used by `character-generator`); the other 8 routers show the planned-index stage of the same standard.
