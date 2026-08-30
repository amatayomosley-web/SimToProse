# simulated-world-evolve — a working instance of SimToProse

Simulates characters' lives turn-by-turn on a deterministic engine; an LLM acts only where no
script can (being the person, choosing). The recorded chronicle becomes novels downstream.

**This repo is an INSTANCE, not the template.** The public template is
[SimToProse](https://github.com/amatayomosley-web/SimToProse) — bookless by design, so anyone can
clone it and build their own. *This* is the author's build: the same engine plus a real book, real
runs, and machine-local configuration. **It is supposed to diverge from the template** — that is
what an instance is. Engine improvements worth sharing get upstreamed deliberately (run the
private-content sweep first); everything book-shaped stays here and never goes back. Two
layers, one repo: the engine (below) stands alone; an optional agent overlay (`.claude/`) settles
on top for Claude Code users — see **Modes** and **The agent layer**, below.

## Guides (load on demand — this file stays thin)

**START HERE — `docs/MAP.md`.** The routing table: what every doc, engine module, script and test
OWNS, plus the project's VOCABULARY. There are 62 design docs, 24 engine modules and 40 suites —
more than anyone holds in their head, and reading them all every session is not practical. MAP tells you
which single artifact answers the question in front of you. **Read its ROUTING and VOCABULARY
sections before reasoning about the engine.** The cost of skipping it is measured, not theoretical: a
session reasoned about the decision layer from four docs plus inference, coined a parallel vocabulary
("vectors" for what the project calls *levers*), and rebuilt a worse version of the buff/debuff
registry that `decision-engine.md` already specifies — guardrails and falsification test included.
MAP's inventories are generated from each artifact's own title line by `scripts/gen_map.py`, and
`tests/test_map.py` fails when they disagree with the tree. That guard is new because the claim
was false without it: regeneration was a shell one-liner pasted into MAP, nobody ran it, and on
2026-08-24 the module table listed 18 of 24, docs 49 of 62, suites 29 of 40 — `bonds`, `targets`,
`levers`, `compounds`, `identity_view` and `profiles` all invisible in the file every session is
told to read FIRST.

- **Operating the system** (run books, inspect, recover — either driver): `docs/guide-operating.md`
- **Authoring content** (world/character JSONs, what each field DOES, live vs inert): `docs/guide-content.md`
- **Authoring a character's FEELINGS** (genotype draw → temperament → worth menu → catalog, in order, with the traps): `docs/guide-emotional-authoring.md`
- **What NUMBER to write** (the species prior + the formative diffs, each row tagged definitional / literature-ordered / calibration): `docs/reference-species-prior.md`
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
   `scripts/direct.py --book "<slug|path>"` (`src/engine/vault.py`, `src/engine/books.py`). This
   repo's `characters/` and `world/` hold ENGINE TEST FIXTURES ONLY, reached with `--fixture`
   (never `--book`). A book's chronicle db lives in the book's own `runs/`, beside its notes.
   **Several books can be active at once** — each is a directory under `$SWE_BOOKS`, resolved by
   slug, with its own db; they share nothing. Machine-local paths are never hardcoded: `SWE_BOOKS`
   is the books root, `SWE_ENV_FILE` the file holding `OPENROUTER_API_KEY`.

   **A run pins the bible it ran against** (`src/engine/bible.py`). Before this, the bible was
   re-parsed per invocation and never recorded, so a mid-book edit silently changed what earlier
   turns were computed from and `resume` could not see it — it asserts the fold of the *log*, not
   the *inputs*. `bible.drifted()` detects; it does not abort.
2. **The log is append-only, and since schema v9 the DATABASE enforces it.** No update, no delete
   on events — corrections are new `correction` events. The snapshot is a derivable CACHE, never the
   source of truth. Until 2026-08-24 this held only because `ledger.py` happens never to emit UPDATE
   or DELETE: `schema.sql` had **zero** triggers, so anything else with a connection — a stranger's
   script, a foreign driver, an sqlite3 shell, a future writer added in good faith — could rewrite a
   committed turn and leave a folded snapshot that no longer matched the log it claims to derive
   from. A rule stated absolutely and enforced by habit is a rule that has never been tested.
   `events`, `turns`, `recall_events`, `acquisitions`, `arc_diffs` and `relationship_deltas` now
   RAISE on UPDATE/DELETE, naming the rule. The caches (`snapshots`, `current_state`) and the run's
   own status stay mutable — a cache that cannot be rewritten is not a cache.
3. **No LLM calls inside `src/engine/`** — the engine computes; the harness/runtime dispatches
   (either driver, below).
4. **No randomness in the engine.** Checks are deterministic (skill vs DC).
5. **Numbers never reach the prompt** — `direction.py` translates; numbers live in the DB. THE LAW
   (`docs/design.md` compute/generate split) — identical in both modes, below. **Enforced since
   2026-08-22 by `tests/test_no_digits.py`, and by construction**: `direction.direct_identity`
   REFUSES a packet carrying a number it has no phrase for, naming the path. Before that the law
   held for four surfaces and leaked thirteen floats through three `json.dumps` sites — trait
   means, every worth-menu weight, the regard map, goal urgency, wound intensity, percept
   fidelity. The reply CONTRACT is exempt (it defines the scale the actor writes ON, not them).
6. Files under 500 lines · stdlib only · modules fail loud (ValueError/RecordError/LedgerError) —
   scoped to the Layer 1 engine; the RUN degrades-not-crashes and records the failure (the boundary
   is run_probe's try/except).
7. Code writes require a depth gate (gates live in a depth-gate workspace `.depth/` whose path is
   machine-local — it is named in your own agent config, never in this repo); `tests/`,
   `docs/`, JSON, and `.claude/` (agents/skills — markdown, no executable logic) are exempt.

## Verify (run after ANY change)

```bash
python tests/run_all.py                     # EVERY suite in tests/, discovered not listed
python tests/coherence_probe.py --stub      # detectors PASS (deterministic, no API)
python tests/coherence_probe.py --corrupt   # MUST print FAIL — the control proves the detectors
```

**The verify block used to name 21 suites BY HAND. `tests/` holds 39 files.** On 2026-08-23 three
of the eighteen that were never run were RED — `test_arc` still asserted the edge-writing that had
moved to `bonds.py`, `test_faithful_turn`'s stub predated the `acts` kwarg, `test_vault`'s affect
fixture predated DISGUST — every one broken by that same session's changes, and every one reported
as "21 suites green" while failing. `tests/run_all.py` DISCOVERS suites so the list cannot rot.

That was one of SEVEN hand-maintained duplicates of a source of truth found in a single session, and
every one had already gone wrong:

| The duplicate | What it cost |
|---|---|
| the verify block's list of 21 suites | 18 suites never run; 3 of them RED and reported green |
| `coherence_probe.py`'s own copy of PRIMARIES | blind to DISGUST, the eighth primitive |
| `basis_probe.py`'s hand-listed ROLE_PAIRS | pairs that no longer existed |
| `consolidation.py`'s `_KNOWN_DIMS` | silently discarded EVERY appraisal in a live run |
| `test_bonds.py`'s `_P` primitive tuple | the same copy that broke `test_vault` when DISGUST landed |
| `scene.py`'s `state_fields_read` | named 6 of the 13 fields the packet actually reads |
| `SPEC-LEDGER.md`'s `module.py:NN` citations | 12 pointed at the wrong line — 4 in one row |

**If you are about to write a list that mirrors something the code already knows, derive it.** The
last two now have guards that cannot rot: the manifest RECORDS its reads (`scene.py` `_Reads`), and
`tests/test_citations.py` resolves the docs' references against the tree. Both are in `run_all.py`.

**`test_no_private_content.py` is now IN the verify block, and green.** It used to be excluded on
the reasoning that a working instance legitimately carries its own book, so the sweep was "expected
to fail here" and was a pre-upstream ritual only. That reasoning is retired (the author, 2026-08-21:
*"No real cast, hard separation"*), and it was wrong in a measurable way: a rule whose guard is
never run is not a rule. On 2026-08-21 the sweep was refreshed to cover all three books' casts and
turned up **336 occurrences across 20 files** — including a private surname inside `src/engine/`,
and an entire scene from a private novel serving as `scene.py`'s DEFAULT fixture, which meant every
no-argument run played someone's book. All of it is gone.

**"The tree is clean" is how this paragraph used to end, and on 2026-08-24 that turned out to be
false.** A tracked file — `.claude/skills/starting-a-book/SKILL.md` — carried the operator's
machine path — an `SWE_BOOKS=` line naming the operator's home directory, Windows separators and
all — while the sweep reported zero hits, for three days, in the verify block, quoted right here
as proof. (The path is not reproduced in this file. The first draft of this paragraph did
reproduce it and `test_self_contained` flagged it immediately, which is the guard working and a
fair comment on how easily this happens.) THREE independent blind spots, each sufficient alone:

1. `.claude` was not in `test_self_contained._ROOTS`, so **42 tracked files were never walked** —
   including the one with the leak in it.
2. `_scan` lower-cased each line but did not normalise separators, so a token written with forward
   slashes could not match a path spelled with backslashes.
3. The book slug involved was not in `_BANNED` — and that one names no real book, so the title half
   was precaution rather than exposure. The machine path was the real thing.

`test_negative_control` passed the entire time. It proves the PATTERNS fire against a string literal
and says nothing about WHICH FILES get read; the gap between those two is where this lived.
`test_the_sweep_can_see_where_the_leak_was` closes it — it calls `_scan` on a bait file instead of
re-implementing the normalisation (the first draft did re-implement it, and stayed green when the
normalisation was deleted), and it fails if `.claude` leaves the roots or the normalisation goes.
Both verified by re-breaking them.

**The lesson is not "extend the list."** A guard reports on what it READS, so a green result is a
claim about COVERAGE before it is a claim about content. Ask what a sweep cannot see before quoting
it as proof of anything — including this paragraph.

**The rule, stated so it cannot rot back:** books live in the vault, and *nothing* about them —
cast, surnames, titles, place names, or PLOT — appears in this repo. Renaming a cast is not
compliance if the situation is still theirs. Fixtures are invented, or they are not fixtures.
**The private half of `_BANNED` is not in this repo.** It was a tuple naming the cast,
surnames, places and titles of four projects, in a tracked file exempt from its own sweep —
which made the guard the single most sensitive artifact here. Hard rule 1 already said
nothing about a book belongs in the repo; it had just never been turned on the guard that
enumerates one. The terms now live beside the books, at `$SWE_PRIVATE_TERMS` (default:
`<parent of $SWE_BOOKS>/private-terms.txt`). Add a new book's terms THERE, never here.

Machine paths stay in the repo — they name no book, they are the class of leak that actually
reached the remote, and a fresh clone keeps a working guard without carrying anyone's cast.
A checkout with no terms file still PASSES (the repo must clone and run) and prints that it
checked machine paths only, so a green run never reads as more than it covered.

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
Known gaps (don't rediscover as bugs): a failed perception check yields NO belief about an act rather than a wrong one (the false-belief layer is unbuilt engine-wide); critic is detect-only; cutting room is views-only (no EDL);
character generation is PARTIAL — genotype (scripts/make_genotype.py, seeded draw + jitter) and the composition pass's script half (94-profile library, src/engine/profiles.py, scripts/composition_pass.py) are built; the LLM classification step is not. See
`docs/guide-operating.md` "What the system does NOT do".
