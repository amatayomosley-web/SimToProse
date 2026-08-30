# New-Book Manifest — what the user copies, creates, and references

The one-glance answer to *"what do I have to put in place to start a book?"*

**Books live in the author's vault, never in this repo** (the seam law). This repo holds the
machine; the vault holds the book. Nothing below puts book content into `simulated-world-evolve/`.

Three categories, and keeping them straight is most of the work:

| | Category | Count |
|---|---|---|
| **A** | **Copy** — templates that become the book's own files | 1 directory |
| **B** | **Create** — the book skeleton and its notes | 4 directories |
| **C** | **Reference** — engine contracts, read in place, never copied | 2 documents |

The most common mistake is copying category C. A contract with two homes drifts, and the copy is
the one that goes stale.

---

## A. Copy

### `runs/_TEMPLATE/` → `<book>/runs/`

The production notes: `canon-ledger.md`, `production-journal.md`, `story-map.md`, `threads.md`,
`continuity-register.md`, `cast/`. These are the production's **process memory** — together with
the run DB they let a fresh session resume mid-book. The template ships only the shape; the line
items fill as the sim runs. See `runs/_TEMPLATE/README.md` and `docs/world-state-ledger.md`.

That is the only directory that gets copied.

---

## B. Create — the book skeleton

```
<vault>/books/<book-slug>/
├── world/          ← REQUIRED. Exactly one note with `type: world`.
├── characters/     ← REQUIRED. At least one note with `type: character`.
├── people/         ← optional but almost always needed (see the four-place rule below)
├── scenes/         ← the production surface: one blueprint + one cfg per scene link
├── chapters/       ← the outline lives here (see "world/ is a typed namespace" below)
├── runs/           ← copied from A; the chronicle DB lands here too
└── staging/        ← retired files (this project never deletes; it stages)
```

`books.resolve` finds a book two ways: an absolute path, or a slug under the `SWE_BOOKS`
environment variable. `SWE_BOOKS` is machine-local — an env var, never a committed constant.

### Every note is markdown, not JSON

`vault.load_book` reads **only `*.md`**. The `.json` files in this repo's `characters/` and
`world/` are **engine test fixtures**, not the vault format. A note is:

```markdown
---
type: character
---
Prose canon on top, with [[links]] to other notes.

```json
{ "fixed": {...}, "baseline": {...}, "current": {...} }
```

## Beliefs
- (0.90, the arithmetic, checked more than once) A claim, in the character's own voice. [[links]]
```

Only the **first** fenced json block is read. `[[links]]` are live: a belief fires when a trigger
matches its claim text *or* a linked note's name.

### `world/` — exactly one `type: world` note

Its engine block carries `world`, `season`, `standing_facts`, `locations[{id, what}]`, and the
**lexicon** — this book's perception vocabulary: `lexicon.attribute_classes {class: [keywords]}`
for overt percepts, `lexicon.subtle_cues {cue: [markers]}` for perception-check-gated ones, and
`lexicon.subtle_cue_classes`. No lexicon is legal but thin: generic extraction, no subtle percepts.

#### `world/` is a typed namespace — what a misfiled note there actually costs

The filter is `vault.py:116`: `(n["type"] or "world") == "world"`. Three outcomes, and only one is
dangerous:

| The note's `type` | What happens |
|---|---|
| `world`, or **absent** (untyped defaults to world) | counts as a world note. With a real one present, `load_book` **raises** — `need exactly one world note, found 2`. Loud. |
| anything else (`concept`, `person`, …) | **inert.** Read by nothing. |
| — and the only real leak — | if it is the **sole** world-typed note, it *is* the world bible. That requires the real world note to be missing or mistyped. |

**Scope**: this is the whole mechanism — only `books.py:108` (an existence check) and `vault.py:116`
read the `world/` directory at all. Nothing reads it type-blind.

**The rule worth keeping**: an outline must never be the book's world note, and **a file should not
live in two directories** — a byte-identical copy in `chapters/` and `world/` drifts, and drift is
what actually bit this project (2026-08-28), not the load path.

**Leave-alone**: a `type:`-carrying non-world note in `world/` is harmless. If reference material
belongs there for a human reason, type it and it stays inert. Untyped is the sharp edge, because
untyped means world.

`standing_facts` is inert to perception (`src/engine/gate.py:101-104` — "read only by the
out-of-loop critic"). A fact that must reach an actor goes in the event text or a vault belief. It
does not arrive by being true in the world.

### `characters/` — one note per character

Engine block requires `fixed`, `baseline`, `current` (load_book raises without all three):

- `fixed.name`, `fixed.genotype` — 6 axes, each `low|typical|elevated|high`
- `fixed.position` — place · class · era · niche. **This is the live slot.**
  Anything filed under `formative.*` is read by **zero** engine code and reaches nothing.
- `baseline.temperament` — all 8 primaries × `{mean, variability}`
- `baseline.traits` — `{mean}` per HEXACO facet
- `baseline.model` — `schwartz` / `moral_foundations` / `needs` weights. An authored `0.5` means
  "average" and correctly renders as nothing; only departures from 0.5 rank.
- `baseline.drives`, `baseline.skills`, `baseline.voice`
- `current.affect` (7 × 0..1), `current.condition` (`{energy, allostatic_load, …}`),
  `current.active_goals`, `current.relationships`
- `## Beliefs` section — the vault. Contract: `- (confidence, provenance) claim`, parsed by
  `_BELIEF_RE` (`src/engine/vault.py:22`). A section with bullets that parse to zero beliefs
  **raises** rather than loading empty — that silence once cost 41 of 77 beliefs across 5 notes.

Shape reference: `characters/maren-healer.json` (convert to the `.md` form above). Worked
non-human example: `tests/test_portability.py` CHAR/WORLD.

### `people/` — the four-place rule

A character is **not** automatically an entity. `load_book` builds `world.people` from `people/*.md`
notes only. For character B to reach character A's turn, **four** things must all be true:

1. a `world.people` entry for B,
2. B's first name in the event text,
3. A's `insight ≥ 0.55`,
4. `A.current.relationships["b"]`, keyed by the same id.

**Adding a character is a four-place transaction, not one file.** A fully playable character
missing its `people/` note is invisible to the person it is talking to.

### `scenes/` — one pair per scene link

- `Scene_<id>_Blueprint.md` — the author's form.
- `scene_<id>_cfg.json` — **the only thing the engine reads.**

Required in the cfg: `situation` (non-empty string) and `cast` (non-empty, every entry
`{id, drive}`). Optional but consumed: `name`, `location`, `props`, `subject`, `opening_tags`,
`elapsed`. Everything else is carried and read by nothing.

`location` and `props` are the two most-omitted fields, and both are silently absent rather than
loudly wrong: no `location` means no PerceptSet place and no location-scoped laws; no `props` means
the objects in the room do not exist to anyone unless the `situation` prose names them.

---

## C. Reference — never copy

| Contract | Answers |
|---|---|
| `docs/template-scene-blueprint.md` | what the author writes: every field marked ENGINE or AUTHOR, plus a pre-flight checklist |
| `docs/actor-direction-format.md` | what the actor receives: both turn messages, the seven volatile parts, the reply contract |
| `docs/standard-vectors.md` | **what every event number means.** NORMATIVE, and the one most authors never find — §3 is the severity anchor scale (what 0.3 vs 0.7 vs 1.0 mean, per dimension), §8 the acceptance criteria for a vector you have written, §10 the anti-patterns. Read §3 before writing your first `opening_tags`. |

Also normative, same rule: `docs/world-authoring-rules.md`, `docs/character-authoring-rules.md`,
`docs/scene-authoring-rules.md` — enforced mechanically by `scripts/lint_book.py`.

---

## D. Verify before you spend a run

```bash
python scripts/lint_book.py --vault "<path to the BOOK folder>"
```

> ⚠ **`--vault` here means the book folder, not the vault root.** Point it at the vault root and it
> reports `need exactly one world note, found 0`, which reads like a broken book and is not.
> (`scripts/direct.py` uses the opposite convention: there `--book` is current and `--vault` is its
> older spelling, both taking a path or a slug.)

ERRORS break a run: missing `fixed`/`baseline`/`current`, a `baseline.temperament` or
`current.affect` missing any of the 8 primaries, an affect value outside [0,1], a non-dict
`current.condition`. Exit 1.

WARNINGS flag thin or silently-degrading authoring: no lexicon; a relationship key that is not a
`world.people` id, so its edge will never surface; a vault belief missing a claim or provenance.
Report-only — fix the notes yourself; the linter never edits.

Then open the chair:

```bash
python scripts/direct.py --book "<path or slug>" --char <note name>
```

The chronicle DB lands in the **book's** `runs/`, beside its notes. The machine repo holds no book
state, and `assert_db_for_book` refuses a `--db` belonging to a different book.

---

## E. The checklist, in one glance

1. `cp -r runs/_TEMPLATE <book>/runs`
2. `mkdir world characters people scenes chapters staging`
3. **world note** (`type: world`): world · season · standing_facts · locations · lexicon
4. **character notes** (`type: character`, one per character): fixed.genotype · fixed.position ·
   baseline.temperament×8 · traits · model · drives · skills · voice ·
   current.affect/condition/active_goals/relationships · `## Beliefs`
5. **people notes** (`type: person`) — one per character anyone must perceive
6. **scene pairs** in `scenes/` — blueprint + cfg, cfg carrying `location` and `props`
7. **outline** in `chapters/`, never in `world/`
8. `lint_book.py --vault "<book folder>"` → clean
9. `direct.py --book "<book>" --char <name>`
