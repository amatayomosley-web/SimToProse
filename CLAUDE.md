# SimToProse

Simulates characters' lives turn-by-turn on a deterministic engine; an LLM acts only where no
script can (being the person, choosing). The recorded chronicle becomes novels downstream. Two
layers, one repo: the engine (below) stands alone; an optional agent overlay (`.claude/`) settles
on top for Claude Code users — see **Modes** and **The agent layer**, below.

## Guides (load on demand — this file stays thin)

- **Operating the system** (run books, inspect, recover — either driver): `docs/guide-operating.md`
- **Authoring content** (world/character JSONs, what each field DOES, live vs inert): `docs/guide-content.md`
- **Working on the engine** (contracts, invariants, extension): `docs/guide-engine.md`
- **Continuing a story** (what to author per generation step, how much data drives each step): `docs/guide-continuing-the-story.md`
- **Driving the engine** (burst discipline, model choice, measured results): `docs/driving-the-engine.md`
- Design intent (normative): the docs in `docs/` — start at `docs/design.md`

**Precedence:** for *what IS*: code > tests > guides > design docs. For *what SHOULD BE*: design docs win.

## Hard rules (always apply)

1. **Machine/content seam — code AND repo (not the Layer 1/2 split above).** Code: `src/engine/`
   carries ZERO book content (enforced: `tests/test_portability.py` token sweep). Repo: REAL BOOKS
   NEVER LIVE IN THIS REPO — **enforced across the whole tracked tree by
   `tests/test_no_private_content.py`.** This rule was stated, violated, scrubbed, and violated
   again before it had a guard; treat the sweep as the rule and the prose as commentary. **Extend
   its banned list, never add an exception to it** — the exception list becomes the leak. Books
   live as linked Obsidian notes in the author's vault, loaded via
   `scripts/direct.py --vault "<book folder>"` (`src/engine/vault.py`). This repo's `characters/`
   and `world/` hold ENGINE TEST FIXTURES ONLY (Maren/Ashford). A book's chronicle db lives in
   the book's own `runs/`, beside its notes. Machine-local paths are never hardcoded: `SWE_BOOK`
   points at a book vault, `SWE_ENV_FILE` at the file holding `OPENROUTER_API_KEY`.
2. **The log is append-only.** No update, no delete on events — corrections are new `correction`
   events. The snapshot is a derivable CACHE, never the source of truth.
3. **No LLM calls inside `src/engine/`** — the engine computes; the harness/runtime dispatches
   (either driver, below).
4. **No randomness in the engine.** Checks are deterministic (skill vs DC).
5. **Numbers never reach the prompt** — `direction.py` translates; numbers live in the DB. THE LAW
   (`docs/design.md` compute/generate split) — identical in both modes, below.
6. Files under 500 lines · stdlib only · modules fail loud (ValueError/RecordError/LedgerError) —
   scoped to the Layer 1 engine; the RUN degrades-not-crashes and records the failure (the boundary
   is run_probe's try/except).
7. Code writes require a depth gate (gates live in the Claude Flow workspace `.depth/`); `tests/`,
   `docs/`, JSON, and `.claude/` (agents/skills — markdown, no executable logic) are exempt.

## Verify (run after ANY change)

```bash
python tests/test_ledger.py && python tests/test_state.py && python tests/test_scene.py \
&& python tests/test_gate.py && python tests/test_consolidation.py \
&& python tests/test_direction.py && python tests/test_portability.py \
&& python tests/test_citation.py && python tests/test_read_api.py \
&& python tests/test_no_private_content.py   # 11 suites, all must pass
python tests/coherence_probe.py --stub      # detectors PASS (deterministic, no API)
python tests/coherence_probe.py --corrupt   # MUST print FAIL — the control proves the detectors
```

Real-LLM probe (OpenRouter, ~25 haiku calls): `python tests/coherence_probe.py --run --db`.
The probe is the permanent regression: a change that turns it red is wrong until proven otherwise.

## Modes

**Mode A — human drives.** You run the scripts directly (`docs/guide-operating.md`): `direct.py`
for one character, `scene.py` for a cast, `critic.py` / `narrate.py` / `cut.py` downstream.
Unchanged by the agent layer.

**Mode B — showrunner drives.** The showrunner (`.claude/agents/showrunner.md`) runs the SAME
scripts through subagents — filling the act/judge/write roles at the engine's existing
`--prompt-only` seams and LLM dispatch points. No agents-only mode: the agent layer requires the
engine; it drives the scripts, never replaces them.

**Canon vs process, in both modes.** The run DB (the SQLite ledger, `src/engine/ledger.py`) is
**world-truth canon**. The `runs/<slug>/` markdown notes (`production-journal.md`, `story-map.md`,
`threads.md`, `continuity-register.md`) are **process-truth** — the showrunner's memory of what it
did, not what happened. `canon-ledger.md` in the notes is a generated, non-authoritative DIGEST of
the DB — read it, never cite it in place of the DB.

## The agent layer (`.claude/`, optional)

`.claude/agents/` — 9 roles: showrunner (orchestrates) + director, world-builder,
character-generator, character-simulator, recorder, continuity-critic, cutter, narrator
(specialists, called as subagents). `.claude/skills/` — 9 craft toolboxes the agents draw on
(frameworks, menus, worked examples — never facts; facts reach an agent only through the
engine-computed packet). `runs/_TEMPLATE/` — the process-notes skeleton, copied per book.

**Law: the agent layer is a DRIVER of the engine, never a value-computer** — same split as rule 5,
above. Full wiring (the loop, the gates, the notes, the hooks): `docs/orchestration.md`.

## Status (2026-07-24)

**Engine (Layer 1): built + verified.** Spine + full pipeline, 8 test suites passing +
`coherence_probe.py` (`--stub` deterministic, `--corrupt` proves the detectors). Hybrid dispatch:
cheap LOCAL model acts (character turns); STRONG model judges + writes, Claude-in-the-loop
(`--prompt-only` emits the prompt). Key-free by default (the OpenRouter path is a key-gated
fallback).
**Agent overlay (Layer 2): authored, unproven.** 9 agents + 9 skills + `runs/_TEMPLATE`
(2026-07-23) — designed against the engine's existing seams, not yet run end-to-end.
**Neither mode has produced a real book yet.** Next genuine step: run one, either mode.
Known gaps (don't rediscover as bugs): critic is detect-only; cutting room is views-only (no EDL);
world/character generation tooling is unbuilt (hand-author, per the guides). See
`docs/guide-operating.md` "What the system does NOT do".
