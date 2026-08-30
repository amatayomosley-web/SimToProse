---
name: starting-a-book
description: >-
  The entry point for a NEW book — the map from nothing to a world the engine can run. Points at the artifact that owns each part: where a book lives on disk and what files it must contain, how its chronicle db comes into existence (it makes itself — do not hand-create it), what the world note's engine block must carry, the laws/rules layer (the five defaults every world inherits, the three switches that must be answered, how a refusal gets computed), and the six-step world-design blueprint in its locked dependency order (premise, universal law, broader community, planet, history, present systems). Open it when starting a new book, setting up a book folder, asking "where do I begin", "how do I make a world", "what do I write first", "how do I add a book to the engine", or when a book fails to load and it is not obvious which contract it broke. A MAP, not a method — it holds no worldbuilding craft and no facts about any world; every step names the doc, module, or script that does.
triggers:
  keywords:
    - slug
    - vault
  concepts:
    - new book
    - start a new book
    - where do i begin
    - set up a book
    - add a book
    - make a world
    - what do i write first
    - book folder
    - book fails to load
---

# Starting a Book — the map

This is the on-ramp. Every other skill in this repo is a **craft well** paired to an agent
(`worldbuilding-frameworks` for the world-builder, `character-frameworks` for the
character-generator, and so on) — a place to reach into *while* working. This one is
different in kind: it is a **procedure**, and it is deliberately thin.

**It holds no craft and no facts.** How to design a magic system, source a wound, or make a
history plausible lives in the wells. What is true in *your* world lives in your book. This
file only answers: *what am I assembling, in what order, and which artifact owns each part.*

Where a pointer and the thing it points at disagree, **the thing it points at wins.** Read the
artifact; do not build from the summary. (`CLAUDE.md` precedence: for what IS, code > tests >
guides > design docs. For what SHOULD BE, design docs win.)

---

## You are assembling three things

| | what it is | where it lives |
|---|---|---|
| **The container** | the book folder + its chronicle db | your vault, never this repo |
| **The rules** | what your world permits, forbids, makes impossible | the world note's `laws` block → `bible_laws` |
| **The blueprint** | the six-step world-design order | `docs/world-model.md` and the five rubrics it fans out to |

Do them in that order. The container is ten minutes; the rules are the first real authoring
decision; the blueprint is the work.

---

## 1. The container — the book and its db

**A book is a folder outside this repo.** Hard rule 1 in `CLAUDE.md`: real books never live
here. `characters/` and `world/` *in this repo* are engine test fixtures, reached with
`--fixture` — never `--book`.

**Where books live:** `$SWE_BOOKS` (`src/engine/books.py`, `ROOT_ENV`). `books.resolve()` accepts
**three** spellings, tried in this order — and the order is the tie-break, so nothing that
resolves today can change meaning:

1. **a full path** — the old `--vault <path>` spelling, intact.
2. **the literal folder name** — `<$SWE_BOOKS>/<spec>`.
3. **the slug** — the folder name lowercased with spaces hyphenated (`books.slug`), so
   `The North Reach` answers to `the-north-reach`. This is also the string
   `books.db_path()` names the chronicle with, so a book and its db always agree.

If two folders slug alike, `resolve()` **raises and names both** rather than picking one — a
silent pick would write a run's events into the wrong book's chronicle. `books.available()`
returns **slugs** (not raw folder names), and counts a directory as a book only **if it contains
`world/`** — that marker gates resolution as well as listing, so a stray sibling folder can never
be adopted as a book.

> **Example configuration.**
> `SWE_BOOKS=/path/to/my-books` (or `C:\books` on Windows), set at User/environment scope.
> The convention it follows is `docs/guide-operating.md:41` — `vault/books/<your-book>/`.

**What the folder must contain** — this is a contract enforced by `src/engine/vault.py`, and
each of these is a distinct loud failure:

```
<book>/
  world/       exactly ONE note with type:world, and it MUST have an engine block
  characters/  at least ONE note; each engine block needs `fixed`, `baseline`, `current`
  people/      optional — type:person notes become world.people entries
  runs/        the chronicle db — YOU DO NOT MAKE THIS
```

> **`vault.py`'s contract is weaker than the runtime's.** It checks that `fixed`, `baseline` and
> `current` are *present* — not what is inside them. A note that loads fine can still crash on
> turn 1. The verified minimum is in **The shortest honest path**, below; use that, not this.

**Note format** (`vault.py` header, and `docs/guide-content.md` is the authoring contract):
markdown frontmatter, then **exactly one fenced ```json block** — that block *is* the engine
payload. `[[links]]` are read as links; a `Beliefs` section in a character note becomes that
character's vault.

**The db makes itself. Do not hand-create it.** `src/engine/db.connect()` creates the parent
directory and applies `schema.sql` idempotently, then migrates by `PRAGMA user_version` up to
`db.SCHEMA_VERSION` (currently **6**). The default path is `<book>/runs/<slug>.db`
(`books.db_path`), which `scripts/direct.py` and `scripts/scene.py` both default to. So the
first run creates `runs/` and the db together. A db from an older schema opens and upgrades; a
db from a *newer* one refuses to open rather than corrupt itself.

**Check the book before running it:** `scripts/lint_book.py --vault "<book>"`. Report-only,
mechanical — it catches the authoring-error class (a missing baseline primary, a relationship
key that is not a world-people id and would therefore *silently* never surface, a malformed
belief) before a run turns them into a mid-run `KeyError` or a quiet no-op.

> **Three footguns, all verified by walking this path.**
> 1. `--book` means **a real book slug** in `direct.py` / `scene.py`, but means **a fixture
>    stem** in `lint_book.py` (which uses `--vault` for a real book). Same flag, opposite
>    meanings.
> 2. `lint_book.py` **does not know about laws** — it predates the law store, so it passes a
>    book whose world has answered nothing. `bible.completeness()` is that check (§2), and the
>    two are not wired together today.
> 3. **A clean lint does not mean a runnable book.** Measured: a character with
>    `baseline.temperament` primaries as bare floats lints clean and then dies at
>    `direction.py` with `AttributeError` (it wants `{"mean": …}` dicts); a character with no
>    `baseline.skills` lints as a *warning* ("thin") and then dies at `direct.py` with
>    `KeyError: 'skills'`. Until that gap closes, treat the shapes in **The shortest honest
>    path** as the contract and the lint as a first pass only.

---

## 2. The rules — what your world can refuse

This is the layer that lets the world say *no*, and it is why the probe can fail honestly
rather than hollowly (`docs/world-model.md`: a world without teeth can never deny a lever).

**You already have laws before you write any.** `src/engine/bible.py` projects the blueprint's
own defaults — `universal-law.md`'s *"default to mundane / earthlike; the premise must justify
each deviation… the bias is 'no, unless'"* — one per step-1 domain:

`default-no-flight` · `default-no-magic` · `default-death-is-final` ·
`default-future-is-open` · `default-one-plane`

So **authoring is overriding, not filling a blank page.** Declare a law with the same `act` and
yours replaces the default; nothing else suppresses it. Turn them all off with
`"blueprint_defaults": false`. A refusal always names what denied it, so `default-` in a
verdict means the blueprint refused, not you.

**Three questions you may not defer.** Most of the blueprint may sit at *"undetermined — fill
when levered."* The switches may not (`docs/universal-law.md`), because planet, history and
present all fork on them:

```json
{ "switches": { "magic": false, "divine": false, "beings": false } }
```

`bible.completeness(world)` reports what is missing — `switch-unanswered`, `unbounded-switch`
(you said a power exists and wrote nothing that limits it), `epistemic-unstated`. It **reports**;
`bible.build(..., strict=True)` is the version that refuses.

**Where each piece is owned:**

| | artifact |
|---|---|
| how to write a law (fields, worked examples) | `docs/guide-content.md` — the Laws section |
| which law-questions must be settled, and why | `docs/universal-law.md` |
| the modality rule: `IMPOSSIBLE` denies, `FORBIDS` allows + attaches teeth | `docs/orchestrator-design.md` §7.1 |
| the store, defaults, completeness, verdicts | `src/engine/bible.py` |
| the executable spec — read these when the prose is ambiguous | `tests/test_laws.py` |

**The one rule to internalise before writing any law:** do not reach for `IMPOSSIBLE` to mean
*characters shouldn't.* A gate that denied every illegal act would make crime unwritable. Your
thief breaks the curfew — that is the story; the `teeth` are what make it cost something.

---

## 3. The blueprint — the six steps, in locked order

Owned by **`docs/world-model.md`**. Read it before starting; it carries the depth rule and the
placement rule that govern every step below. The order is a **dependency** order — each layer
constrains the next, never the reverse.

| step | decides | rubric |
|---|---|---|
| **0** | **Premise** — the one-line conceit. The finish you work backward from; every law choice must serve it or it is arbitrary. | `docs/world-model.md` |
| **1** | **Universal law** — what is *actually* true: physics, the supernatural switches, souls & death, fate, the shape of reality. Every "yes" carries a **Limit** and an **Epistemic status**. | `docs/universal-law.md` |
| **1.5** | **Broader community** — a scope gate. Does this world stand alone, or sit inside a wider community of worlds? No → go to 2. Yes → settle it *before* the planet, because it constrains the planet. | `docs/broader-community.md` |
| **2** | **Planet** — the physical stage, sized to what the story needs. Scope first, then geology → hydrology/climate → ecology. | `docs/planet.md` |
| **3** | **History** — what happened, under the law, on the planet. Opens with the origin of peoples. It is the *justification*, not the deliverable. | `docs/history.md` |
| **4** | **Present systems** — history's current output and what the sim actually consumes: economy, governance, religion-as-lived, factions, culture, and the current world-state. | `docs/present-systems.md` |

**Three disciplines that apply at every step** — all from `world-model.md`, all easy to skip
and expensive to skip:

- **Depth rule.** Author only the hinges the story levers on. Mark the rest *"undetermined —
  fill when levered."* Do not pre-simulate. The switches at step 1 are the stated exception.
- **Author backward, validate forward.** When the premise demands a specific present, author
  society → the history that yields it → the planet/law that yields that history. Then run the
  dependency order forward and confirm it *actually produces* your target. A society decreed
  without a forward-plausible history is the forcing failure.
- **Placement rule.** Most elements live at three layers, not one: *existence* (the deepest
  layer that could forbid it), *presence* (where it physically sits), *significance* (where
  agents engage it). Monsters fork: supernatural existence at 1, presence at 2, role at 3–4.

**Craft, when you need it:** `worldbuilding-frameworks` is the well for any of steps 1–4 — it
grounds invented elements in real-world analogs. This map tells you *which* step you are on;
that skill helps you *do* it.

---

## 4. Then: characters, then run it

The world is the character-generator's **input** — baselines are derived from the formative
world, never set arbitrarily (`docs/world-model.md`, "Two timescales"). So the world comes
first, at least in the slice your opening characters grew up in.

- **Their emotional makeup, in order:** `docs/guide-emotional-authoring.md` — draw the genotype
  (`scripts/make_genotype.py`) for background cast, author it backward for principals, then
  temperament → worth menu → catalog. The catalog is where "brave, but terrified of spiders"
  becomes arithmetic instead of a contradiction.
- **Designing a person:** `docs/character-anatomy.md`, `docs/character-model.md`,
  `docs/character-schema.md`, and `docs/baseline-generation.md` for the no-free-sliders rule —
  every number traces to a life event or it is not ready. Craft well: `character-frameworks`.
- **Running it:** `docs/guide-operating.md` — `direct.py` for one character, `scene.py` for a
  cast, then `critic.py` / `narrate.py` / `cut.py` downstream.
- **Continuing it:** `docs/guide-continuing-the-story.md` — what to author per generation step.

---

## The shortest honest path

**Walked end-to-end before this was written.** Every shape below is what actually ran, not what
the loader merely accepts — the two differ, and the gap is where a first book dies.

1. `mkdir` the book under `$SWE_BOOKS` with `world/` and `characters/`. Name the folder however
   you want it to read on disk — spaces and capitals are fine, the slug is derived. Until
   `world/` exists the engine cannot see it, so make that subdirectory first.

2. **The world note** — frontmatter `type: world`, then one fenced ```json block:

   ```json
   { "world": "<name>",
     "switches": { "magic": false, "divine": false, "beings": false },
     "locations": [ { "id": "quay", "what": "the quay" } ] }
   ```

   The three switches even at `false` **are step 1 answered at its floor** — `completeness()`
   returns clean, and the five blueprint defaults pin into the bible. A `lexicon` is not
   required; without one you get a per-turn `world-fault` warning and the run continues.

3. **One character note** — `type: character`. The minimum that RUNS, not the minimum that
   loads. Note the two shapes differ on purpose:

   ```json
   { "fixed":    { "name": "<name>", "age": 30 },
     "baseline": {
       "temperament": { "SEEKING": { "mean": 0.5, "variability": 0.1 },  "…all 7…" : {} },
       "skills":      { "perception": 0.6, "insight": 0.5 }
     },
     "current":  {
       "affect":    { "SEEKING": 0.5, "…all 7…": 0.4 },
       "condition": { "energy": 0.7, "allostatic_load": 0.3, "health": 0.9,
                      "fatigue": 0.2, "injuries": [] } } }
   ```

   The seven primaries are `SEEKING · FEAR · RAGE · LUST · CARE · PANIC_GRIEF · PLAY`, and all
   seven are needed in **both** blocks. **`baseline.temperament` values are dicts with `mean`;
   `current.affect` values are bare floats.** `baseline.skills` is **required** — the lint calls
   it merely "thin", but the turn loop reads it directly.

4. `python scripts/lint_book.py --vault "<book>"` until the errors are gone. Warnings about
   `voice` / `drives` / `model` are genuinely optional.

5. `python scripts/direct.py --book <slug> --char <name> --stub`

   **This is an interactive loop, not a batch job.** It prints your status, then reads
   circumstances from stdin one line at a time (`status` and `quit` are commands). If it looks
   like it hung, it is waiting for you. Pipe it to run unattended:

   ```
   printf 'A stranger sets a lantern on the quay and waits.\nquit\n' | python scripts/direct.py --book <slug> --char <name> --stub
   ```

   `--stub` is deterministic and needs no API key. **`runs/` and the db appear on this run.** It
   parks at the end and prints the `--resume` command to continue.

6. Now go back and do the blueprint properly, one step at a time, deepening only where the
   story levers.

You do not need the whole cosmos to start. You need **a slice with teeth** — enough rules that
the world can plausibly refuse.
