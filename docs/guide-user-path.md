# The User Path — everything you need, in the order you need it

A router, not a manual. Every step names the artifact that owns it; where this file and that
artifact disagree, **the artifact wins** (`CLAUDE.md` precedence: for what IS, code > tests >
guides > design docs; for what SHOULD BE, design docs win).

`MAP.md`'s ROUTING table answers *"I am changing the engine, what do I open?"* This file answers
*"I want to make a book, what do I do?"* — a different question with a different order.

---

## 0. Decide which layer you are using

`README.md` §"Two layers, one repo" is the authority. In short:

| | Engine only | Engine + agent overlay |
|---|---|---|
| You run | the scripts, by hand, turn by turn | the `showrunner` skill, which drives the scripts for you |
| You need | Python stdlib + a local model or an OpenRouter key | the above, plus Claude Code |
| Status | built and verified | authored, not yet run end to end |

Everything below applies to both. The overlay is a **driver** of the engine, never a replacement:
every value is computed deterministically, and the LLM only acts, judges, and writes.

---

## 1. The two entry points

Both are skills, and both are on-ramps rather than craft:

- **`starting-a-book`** — the map from nothing to a world the engine can run. Open it for a new
  book, or when a book fails to load and it is not obvious which contract it broke.
- **`showrunner`** — **the one interface you talk to while running a book.** It proposes, argues
  from what the book actually contains, and can tell you no with a citation. It carries three live
  hooks: grounding injection before every answer, a citation gate on canon writes, and a
  beat-blind wall on simulator spawns. Use the skill, not the agent of the same name — the agent
  is the unattended batch path and carries none of those hooks.

You never address the nine specialist agents directly. The showrunner does that.

---

## 2. Set the book up

**`docs/new-book-manifest.md`** owns this end to end — what you COPY (`runs/_TEMPLATE/`, and
nothing else), what you CREATE (`world/ characters/ people/ scenes/ chapters/ runs/ staging/`),
and what you REFERENCE without copying.

The four things most likely to bite you, all verified:

1. **A book lives in your vault, never in this repo.** `SWE_BOOKS` is the env var holding the
   root; `books.resolve` takes a path or a slug under it.
2. **Notes are `*.md` with one fenced ```json engine block.** `vault.load_book` reads only `.md`.
   This repo's `characters/*.json` and `world/*.json` are **engine test fixtures**, reached with
   `--fixture`, and following them as a template gives you a book that loads zero characters.
3. **A character is not automatically an entity.** For B to reach A's turn you need four things:
   a `people/` note for B, B's first name in the event text, A's insight ≥ 0.55, and
   `A.current.relationships["b"]`. Adding a character is a four-place transaction.
4. **`lint_book.py --vault` means the BOOK folder**, not the vault root. Point it at the root and
   it reports `need exactly one world note, found 0`, which reads like a broken book and is not.
   (`direct.py` uses the opposite convention: `--book` is current, `--vault` its older spelling.)

---

## 3. What to write — the normative contracts

Four documents bind what you author. They are contracts, not advice:

| Contract | Governs | Enforcement |
|---|---|---|
| `world-authoring-rules.md` | the world note + `people/` | `scripts/lint_book.py` |
| `character-authoring-rules.md` | character notes + the `## Beliefs` vault | `scripts/lint_book.py` |
| `scene-authoring-rules.md` | scene configs, drives, props, magnitudes | `scripts/lint_scene.py` (rules 1–3 only; 4–7 are unmechanized) |
| **`standard-vectors.md`** | **every number that describes an event** | none — read §3 |

`standard-vectors.md` is the one authors never find, so: **§3 is the severity anchor scale** —
what 0.3 vs 0.7 vs 1.0 actually mean, per dimension. `0.1–0.3` ordinary friction · `0.3–0.5` real
but bounded · `0.5–0.7` severe · `0.7–0.9` grave · `1.0` reserve. Omission is the default for most
dimensions of most events.

**Do not inflate a magnitude to make something happen.** §3 states plainly that a single appraisal
on a neutral sheet almost never changes the next staging line, *by design* — `care_relevant` needs
≈0.69 merely to leave a visible next-beat trace. When a scene goes flat, the lever order is: the
**event text** (much the strongest), then a catalog row, then accumulation, then the arc. Sizing
the vector up is anti-pattern §10.1.

Craft, as opposed to contract, lives in `guide-content.md` (what each value *does* at runtime, so
you never tune a dead knob), `guide-emotional-authoring.md`, `reference-species-prior.md` (what
number to write in a field), and `baseline-generation.md`.

---

## 4. The two seam contracts

These describe the boundary between what you write and what the model sees:

- **`template-scene-blueprint.md`** — what the author writes. Every field marked 🟢 ENGINE or
  ⚪ AUTHOR, because **the engine reads the cfg JSON and never your markdown.** Carries the
  pre-flight checklist.
- **`actor-direction-format.md`** — what the actor receives: both turn messages, the seven
  volatile parts, the reply contract, and where each identity block comes from.

The single most common authoring failure is putting something in a blueprint that never reaches
the cfg. `props` and `location` are the two most-omitted fields, and both fail *silently*: no
`location` means no PerceptSet place and no location-scoped laws; no `props` means the objects in
the room do not exist to anyone unless the situation prose names them.

---

## 5. Run it

```bash
python scripts/lint_book.py --vault "<book folder>"          # before anything
python scripts/lint_scene.py --book <book> --scene <cfg>     # per scene
python scripts/direct.py --book "<book>" --char <note>       # the director's chair, one actor
python scripts/scene.py  --book "<book>" --scene <cfg>       # multi-actor scene
```

You place **circumstance only** — the tools have no affordance for writing a character's state or
their lines. `--stub` runs deterministically with no model. The chronicle DB lands in the *book's*
`runs/`, and `assert_db_for_book` refuses a `--db` belonging to a different book.

A lint that comes back clean is not "all rules verified" — the tool prints what it did **not**
check, and rules 4–7 of the scene contract are unmechanized.

| Script | For |
|---|---|
| `direct.py` | the director's chair — one character, circumstance per turn |
| `scene.py` | multi-actor scene from a cfg; salience decides who speaks |
| `lint_book.py` / `lint_scene.py` | pre-run validation |
| `narrate.py` | canonized scene → POV-bound prose |
| `cut.py` | the dailies viewer for the cutting room |
| `critic.py` | continuity + voice check (the non-author gate) |
| `composition_pass.py` | backstory → baseline, deterministically |
| `make_genotype.py` | combinatorial genotype draw |
| `canon_digest.py` | regenerate a book's canon-ledger from its DB |
| `verify.py` | Part A of the verification sheet |
| `exp.py` | the lever-eval harness behind `driving-the-engine.md` |
| `gen_map.py` | regenerate `MAP.md` (run after adding a doc) |

---

## 6. The nine roles

Whether played by agents or by you, these are the seams the pipeline externalizes:

**world-builder** (the stage and its teeth) → **character-generator** (a whole person, every number
traced to a life) → **director** (places circumstance only; proposes beats, the author ratifies) →
**character-simulator** (one turn, blind to the intended outcome) → **recorder** (the keystone —
turn → typed events; the one error class that compounds) → **continuity-critic** (gates canon;
flags, never rewrites) → **cutter** (selects and orders, never invents) → **narrator** (renders
within the POV's knowledge) → **showrunner** (drives all of the above).

Two of these carry rules worth memorizing:

- **A faithful refusal is a success, not a failure.** If no circumstance can motivate a beat, the
  beat is wrong for these characters — revise the beat, not the character.
- **Correct forward, never backward.** The log is append-only, enforced by SQLite triggers. A bad
  record already appended is fixed by a compensating event, never a silent edit or delete
  (`Premise`-level rule: *the log is never rewound; it is forked*).

---

## 7. Getting prose out

`narration.md` and `voice.md` own the how; `cutting-room.md` owns the shape. The rule that governs
both: **the narrator's knowledge for a scene = the POV character's knowledge for that scene.** Get
it wrong and you re-open the omniscience leak at the prose layer even when the simulation was
clean.

The cut is deliberately **not** a pipeline. `cutting-room.md` records a rejected 7-step automated
draft: the shaping happens in discussion over the dailies, because automating it first would
calibrate gates against taste nobody has formed yet. `cut.py` computes views; the room decides.

---

## 8. Judging, and continuing

- **`verification-sheet.md`** — Part A automated (`python scripts/verify.py --slow`), Part B
  per-mechanism, Part C human reads, and Part D: what a fully green sheet still does **not** prove.
- **`measurement.md`** — detectors are deterministic, judges are blinded, **nothing self-grades.**
- **`acceptance-criteria.md`** — judging a scene as a scene.
- **`run-lifecycle.md`** — a run outlives its sessions; nothing about it may live only in session
  memory. Resume with `--resume <run_id>`.
- **`guide-continuing-the-story.md`** — what to author for each next step, under the depth rule:
  author only the hinges the story levers on, class-default the long tail, and let the bible grow
  from the sim.

---

## 9. Read these before your first run

Short list, in order: `README.md` (what this is) → `design.md` (107 lines; the pipeline, the
compute/generate split, the load-bearing constraints) → `new-book-manifest.md` (what to put on
disk) → the three authoring-rules contracts + `standard-vectors.md` §3 → `guide-operating.md` (the
loop, recipe by recipe).

`design.md` first, always. Every other doc assumes it.
