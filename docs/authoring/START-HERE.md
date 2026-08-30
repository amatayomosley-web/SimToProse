# Start Here — Building a Book, by Hand

Three forms sit beside this page: `BLUEPRINT-world.md`, `BLUEPRINT-character.md`,
`BLUEPRINT-scene.md`. Each is a print-and-pen document that turns a plain-English answer into a
file the engine loads. This page is not a fourth form. It is the order to open the other three in,
the folder to put the results in, the one conversion none of them gives you, and the exact
commands that prove your book works.

Read this page once. It is short. Then open the world blueprint.

---

## The order, and why it is not arbitrary

**World first. Then characters. Then scenes.**

Every document asks you only for things you have already settled in a sibling document — never for
something that comes later:

- A **character's** relationships, regard groups, and `current.location` are all *ids*: another
  person's id, a group name, a place id. Those ids mean nothing until the **world** note has
  declared them. Write the world first and you are copying real ids, not inventing them.
- A **scene's** cast, location, subject, and optional act all point at things the **world** and the
  **characters** already declared. Write the scene last and every field is a lookup.

You can fill the forms in any order you like. Nothing stops you. But every check at the end will
fail the same way — *not found* — and you will not know whether the id or the thing it names was
the mistake.

---

## The folder you create

```
YourBook/
  world/        exactly ONE .md file.   BLUEPRINT-world.md builds this.
  characters/   one .md file per person the engine acts.  BLUEPRINT-character.md builds these.
  scenes/       one .json file per scene.  BLUEPRINT-scene.md builds these.
  people/       optional. One .md file per walk-on, if you prefer files to the world note's
                inline `people` list. Both routes work and they combine.
  chapters/     your outline, if you keep one. Nothing reads it — but an untyped file left in
                world/ counts as a second world note and stops the book loading. Outlines go here.
  runs/         the engine writes here. Never you, never by hand.
```

Make `world/`, `characters/`, and `scenes/` before you write anything. The rest can wait.

**The names of the files.** World and character notes are markdown: `world/YourWorld.md`,
`characters/tam.md`. A scene is **plain JSON, not markdown** — save it as `scenes/<name>.json`
(the reference book uses `scenes/scene_01_the_fourth_asking_cfg.json`). The scene blueprint shows
you the JSON but never names the file; this is the line that names it.

**You never name the database.** The engine builds `runs/<book-folder-name-lowercased-with-hyphens>.db`
on the first run. A folder called `Beck Hollow` gets `runs/beck-hollow.db`. Naming the folder is
naming the database.

---

## The shape every note shares

World, character, and person notes are all the same three-part `.md` file. The loader's own error
messages call the machine-readable part the **engine block**, so it is worth knowing the phrase
before you see it in an error:

```
---
type: world | character | person
id: a short id
---

Prose. Yours. The engine does not read it. Write it anyway.

```json
{ ... the content, in the shape that document's blueprint describes ... }
```

## Beliefs                        <- character notes only, BELOW the json block
- (0.9, where this came from) The claim, in the first person.
```

Four rules, identical in all three documents, collected here once:

- **Only the FIRST fenced ` ```json ` block is read.** A second one is ignored with no warning.
- **It must be valid JSON** — straight quotes, a comma between entries, none after the last one.
  A malformed block refuses the whole book by name.
- **Write the `type:` line explicitly.** An untyped note inherits the type its folder expects,
  which is exactly how a stray outline in `world/` becomes an invisible second world note.
- **A `## Beliefs` bullet must be `- (confidence, provenance) claim`.** Any other shape refuses
  the book to load rather than silently loading as zero beliefs.

---

## Before either checker will tell you anything

**A book with no character notes will not open — not for a scene, not for the linter.** Both tools
call the same loader, and it refuses a book whose `characters/` folder is empty
(`VAULT_NO_CHARACTERS`, `src/engine/vault.py:161-162`). You will get nothing back about your world,
not even a warning.

So, before you lint a half-finished world, write this whole file as `characters/Stub.md`:

```
---
type: character
id: stub
---

A placeholder, so the book has one character and the linters will run at all.

## Beliefs

- (0.8, seed) A placeholder belief, written only so the shape is not empty.
```

...followed by one fenced json block containing exactly `{ "fixed": {}, "baseline": {}, "current": {} }`.

The linter will print several `ERROR` lines about this stub's missing fields. **Ignore them.** It
collects every problem and prints them all, so your world's lines print in full regardless. Replace
the stub with a real character before you run the book.

---

## The one conversion no form gives you: circle → number

Every form asks you to write a sentence or circle one off a short list, and hands the number to
"the sizer" — a second person who turns your circle into the figure the engine stores. **If you
are working alone there is no sizer, and the file will not run until somebody does that pass.**

Here is that pass, in full. Every four-option ladder in `BLUEPRINT-character.md` is chosen by the
same three cut points, **0.25 / 0.55 / 0.80** (`src/engine/direction.py:133`, used at
`src/engine/identity_view.py:126`). Pick the middle of the band you circled:

| you circled | write | applies to |
|---|---|---|
| the 1st sentence | **0.15** | trait means (all six HEXACO facets), goal `priority`, goal `satisfaction`, wound `intensity`, `regard` weights, voice `assertiveness`, `agency`, `active_goals[].urgency`, and all four relationship axes (`trust`, `affinity`, `respect`, `debt`) |
| the 2nd sentence | **0.40** | (same list) |
| the 3rd sentence | **0.65** | (same list) |
| the 4th sentence | **0.90** | (same list) |

Three ladders use different cut points. They are the only exceptions:

- **Belief confidence** — cut points 0.35 / 0.65 / 0.90 (`src/engine/direction.py:153-156`).
  Write **0.25 / 0.50 / 0.80 / 0.95** for the four sentences in order.
- **`current.condition`** — the sentence is chosen off `energy × (1 − allostatic_load ÷ 2)`, not off
  energy alone, at cut points 0.25 / 0.50 / 0.75 (`src/engine/direction.py:127-130, 283`). For a
  character carrying a load of 0.35, the four sentences need an energy of roughly
  **0.20 / 0.45 / 0.70 / 0.95**. Compute it; do not eyeball it.
- **A scene's `opening_tags.dimensions`** — the four words in `BLUEPRINT-scene.md` §9 are the bands
  in `docs/standard-vectors.md` §3: *ordinary friction* = **0.2**, *real but bounded* = **0.4**,
  *severe* = **0.6**, *grave* = **0.8**. Omit any dimension the scene does not touch.

Two more that are not ladders at all:

- **`baseline.model` weights** (schwartz / moral_foundations / needs) — only the *order* matters. A
  missing key reads as exactly average, not as zero. Write **0.8** beside each thing they will not
  trade away, **0.2** beside each thing that weighs little with them, and leave every other name
  out.
- **`baseline.temperament` and `current.affect`** — eight numbers each, all eight required. Use the
  same 0.15 / 0.40 / 0.65 / 0.90 scale for "where do they sit when nothing is happening," and make
  `current.affect` equal to the temperament means unless the book opens mid-crisis.

**Do the conversion as a separate pass, after every sentence is written.** And when you are done,
sweep the sheet for any field that still holds a sentence where a number belongs — `intensity` is
the one people miss. Neither linter catches it, and it kills the run on the first beat.

---

## The commands — and the flags are not the same

Run these from the engine's project root, in this order. **Each tool spells the book folder
differently. This is not a typo in this page; copy each line as written.**

```
python scripts/lint_book.py  --vault "YourBook"
python scripts/lint_scene.py --book  "YourBook" --scene "YourBook/scenes/<name>.json"
python scripts/scene.py      --book  "YourBook" --scene "YourBook/scenes/<name>.json" --stub --prompt-only
```

1. **`lint_book.py --vault`** reads your world and every character. `--book` means something else
   entirely to this tool and will fail with a usage line.
2. **`lint_scene.py --book`** checks one scene against the book.
3. **`scene.py --stub --prompt-only`** builds the actual prompt for the first speaker and prints
   it, without calling any model and without writing a run. Run it as the last check.

> **Corrected 2026-08-30.** This page used to warn that a book could pass both linters with zero
> errors and still die at prompt-build, because a wound whose `intensity` was left as the circled
> sentence linted clean. That was true, and it happened: of three writers given only these forms,
> one shipped exactly that book. **`lint_book.py` now catches it**, as an ERROR naming the
> character and the exact field path — so the linter is a real pre-flight and you will not get
> that far with a sentence in a number's place. Do the conversion pass below anyway; the linter
> tells you a number is missing, not which number was meant.

**Read every line all three print.** An error means a run would break. A warning means something you
authored is switched off, and the message names which part of which form to go back to. A run with
warnings is not clean — the tool says so itself. Fix, re-run, until nothing prints.

**Two warnings are expected and are not your fault.** `lint_book.py` will always list the acts your
laws are keyed to (informational), and it will warn that each `fears_wounds` trigger has no
`baseline.catalog` row. That arithmetic tier is deliberately outside these three forms. Leave it.

---

## What a clean run does not mean

`lint_scene.py` prints, in its own output, the two things it did not check: whether the drives
actually collide, and whether anyone knows something they could not know. Those need a reader.
Before you spend a real run, check by hand:

- There is exactly **one** pressure in the scene. If it takes two clauses joined by "and", it is
  two scenes.
- Each drive is a physical goal, not a topic, and one person's want runs into something another is
  protecting.
- Every object a drive points at is in the props or in the situation prose.
- The point-of-view character is in the cast. Nothing checks this for you.
- Nothing in the situation, the props, or any drive mentions something these people could not know.
- No dialogue anywhere in the situation.

---

## Three traps worth carrying in your head from page one

They are each explained in full where they belong, but they cost the most when discovered late:

1. **A character trait written as `"very high"` is read as `typical`.** Only the first word is
   read, and an unrecognised word falls back silently. Put `low` / `typical` / `elevated` / `high`
   first, then a space, then any note you like.
2. **The scene's `drive` replaces that character's standing goals for the whole scene.** Not blends
   — replaces. If a long-running want still matters in this room, it has to be in the drive.
3. **A person id's FIRST WORD is the name matched in your event text.** Lowercase, no spaces, and
   make it their first name — `tam`, never `Tam Rill` or `the_miller`.

---

*Every claim and line number on this page was opened and checked against the code on 2026-08-30. If
a line has moved, the code is right and this page is stale — fix the page, the way the three
blueprints ask you to fix them.*
