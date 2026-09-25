# Content Guide — authoring a book's inputs

For a session AUTHORING per-book content (design.md Phase B). The other guides tell you how to
RUN (guide-operating.md) and how to EXTEND (guide-engine.md); this one tells you what to WRITE —
and, critically, **what each value actually does at runtime**, so you never tune a dead knob.
Precedence as everywhere: code > tests > this guide > design docs for what IS.

> **Starting from nothing?** This guide assumes a book already exists. The map from *no book* to
> *a world the engine can run* — the folder contract, how the db creates itself, the laws layer,
> and the six-step world-design order — is `.claude/skills/starting-a-book/SKILL.md`. It points
> at the artifacts; this guide is one of them.

## The database needs NO setup

There is no schema to create, no migration to run, no seed data. `Ledger("runs/<book>.db")`
auto-creates and migrates everything from `src/engine/schema.sql` on first connect (db.py).
One `.db` file per book. Never hand-edit it — it is the chronicle (the product itself); back it
up like a save-file. Everything you AUTHOR lives in two JSON files; the db only ever holds what
the simulation generates.

## The machine's input contract

1. **World JSON** — the book's place + its perception vocabulary (template: `world/ashford-slice.json`)
2. **Character JSON(s)** — one per principal (template: `characters/maren-healer.json`;
   minimal alien example: `tests/test_portability.py` CHAR/WORLD)
3. **Run config** — `{"catalog_version": 1, "models": {...}, "prompt_versions": {...}}` at create_run
4. **Per turn, the scene slice** — the assembler's request, declared once in `src/engine/scene_slice.py`
   (`SceneSlice`): every key a driver may pass, with its shape. An undeclared key is refused naming it,
   and so is a declared key of the wrong shape (gate slice-contract, 2026-09-25). The drivers build it:
   the scene driver from the scene file and the log, the chair from its circumstance.

Around these, a scene run reads its scene file (`docs/authoring/BLUEPRINT-scene.md`), and every model
reply enters through its parser. This section used to end "The machine reads nothing else" while listing
three of the twelve keys the drivers sent; the slice's keys are now listed only in the code that refuses
the undeclared ones, and not here.

## Character JSON — what is LIVE (field → mechanism → effect → authoring rule)

| field | mechanism | observable effect | authoring rule |
|---|---|---|---|
| `fixed.name` | stable prefix | identity in every prompt | — |
| `fixed.genotype` (one {hit, hold} cell per path, 2026-09-10) | state.build_profile gains + hold; **draw one with `scripts/make_genotype.py --seed <anything>`** for background/supporting cast (it prints the rest words too) — principals are authored backward from the character the story needs | hit / hold per path; the six primitive-era axes are retired, and `rest` is not a genotype cell (refused: `GENOTYPE_REST_MOVED`) | vocabulary is EXACTLY `low\|typical\|elevated\|high` (.75/1.0/1.2/1.3) and `brief\|typical\|long\|lasting`; anything else silently reads as typical |
| `baseline.temperament` 8×`{rest, mean}` | decay target + direction deviation marker; the rest WORD reaches the actor as a sentence under `disposition` | where emotions REST — **`rest` is AUTHORED, a word per path beside the voice** (`quiet\|low\|raised\|high`, capped per path; 2026-09-10 owner: a character design question); "more than is usual for you" fires past ±0.15 from the mean | the rest word IS the personality's resting face; an anxious character = WARINESS rest `raised`, not high starting affect. The mean is seeded from the word once and moved only by the arc engine; `variability` is gone |
| `baseline.traits` `{mean}` | HEXACO slopes on gains | emotionality→FEAR/GRIEF sensitivity, agreeableness→RAGE (negative), extraversion→PLAY/SEEKING | only those three are read today; others are stored context |
| `baseline.model` (schwartz/moral_foundations/needs weights) | relevance weighting (state._DIM_VALUE_KEYS) | the same event lands harder on the character whose values it touches — this is where two people diverge | author only the levered weights; a MISSING key reads neutral 0.5 (depth rule: silence = average, not zero) |
| `baseline.drives.goals` | gate goal-salience + prompt | goal-bearing beliefs recall FIRST under budget | phrase goals with the nouns the vault claims use — salience is word overlap |
| `baseline.skills` | deterministic checks | perception ≥0.60 sees subtle cues; insight ≥0.55 recognizes entities; combat gates harm/threaten capability | these three are consulted today; others ride the stable prefix as context |
| `baseline.wounds` (ENGINE STATE since 2026-09-11 — never written by hand; `drives.fears_wounds` is refused by lint) | stable prefix as "what has marked you" + the receipt (a wound's intensity is the investment that multiplies a reading about its concept on its path) + the half-life | a scar keyed concept@PATH, minted from a formative profile at creation or by a durable beat mid-story; moves per trial, erodes between scenes | pick the profile whose concept matches; make the scene ABOUT the concept and the appraiser names it |
| `baseline.voice`, `drives.goals` (the GOAL TEXT only) | stable prefix | the LLM acts on them; the ENGINE never parses them. **`orientation` no longer reaches the actor (2026-09-06)** — `coping` is an imperative and `locus` a routing bias, and both are rates the appraisal already spends (`scene-assembly.md` §Stable prefix) | written for the actor's eyes — craft text, not config. **A wound needs an operational twin in `baseline.catalog` or it is prose the engine cannot compute** — `lint_book.py` warns when a `trigger` list has no matching row |
| `baseline.catalog.rows` `[{when, lever, op, magnitude, source}]` | levers.active_rows → levers.effective → the TIER-3 vector the direction is staged from | *this* is how "brave, but terrified of spiders" becomes arithmetic: a row fires on a standing fact and multiplies a primitive. Four condition kinds: `percept` (words in the event), `present_edge` (an axis threshold on someone present), `affect_at_least` (emotion modulating emotion), `condition_at_most` (state) | `lever` must be a PRIMARY or it fails loud; rows are validated even when inactive. Calibrate against the direction bands (0.25/0.55/0.80) or a fired row is invisible inside a band |
| `current.affect` 7×[0,1] | the starting CURRENT tier | turn-zero emotional state | start at/near temperament means unless the book opens mid-crisis |
| `current.condition.energy` + `.allostatic_load` | recall budget = energy×(1−load/2); direction bands | a drained character misses faint connections and reads "worn thin" | this is a LEVER: deplete to make a character miss what they know (relevancy-gate.md §energy — the director's legitimate cognition lever). Write both keys or neither (the readers assume different values for a missing one; lint warns). A book that switches `condition` off (world `systems`) needs no block: absent says nothing and recalls on the full budget. A book that runs `condition_flow` must author both keys, and the engine moves them; a scene cfg's `condition` list states how someone arrives, in words (BLUEPRINT-scene 6c) |
| `baseline.body.strength` (gate body-exertion) | `body.capacity` - read only when the book runs `body` | how long the body keeps going: the reader's exertion word and the waking drain are divided by it | a WORD: frail / slight / ordinary / strong / powerful (BLUEPRINT 9.2); required when `body` runs, warned about when it does not |
| `current.active_goals` | same as drives.goals | — | keep in sync with drives.goals |
| `current.attachments` `{"loc.<id>" \| "grp.<tag>": {hold, sign, note}}` | `connection.held_map` (the emotion multiplier's registry) and `bonds.stake_of` / `act_from_tags(held=)` (the bond tier's stake and `received`); seeded as `attachment_declared` rows (v30) and folded on resume; linted against `world.locations` / `people[].groups` — an unregistered key is an ERROR; `relationship_priors.in_group` is RETIRED | an act on her held place is done TO her at her hold; the composition pass's `--attach-classify` fills the block from the backstory (a relation word per entity, never a number) | LIVE (2026-09-18, gate 5) |
| `current.relationships` `{target: {trust,affinity,respect,debt}}` | volatile.edges → direction phrases; `levers` `present_edge`/`target_edge` rows; **`bonds.observe` MOVES them every beat someone acts** | "Joss: guarded trust, fond of them" in the prompt — and what you author is their EXPECTATION, so a high trust makes a betrayal catastrophic and a low one makes the same act barely register | **keys MUST equal world.people ids** — edges surface ONLY for entities recognized in the PerceptSet (scene.py:_build_edges); a misspelled key never appears. Author the STARTING read; the run moves it. `scripts/direct.py` DOES move them — corrected 2026-09-06: it calls `bonds.act_from_tags` then `bonds.observe`/`bonds.reflect` and applies both (`direct.py:466-479`). The old claim here was that it moved none for want of a second party |
| `baseline.relationship_priors.default_trust` | `bond_rest.stranger_rest` — the STRANGER's rest on trust | where an edge the sheet did NOT author relaxes to across a declared gap; an AUTHORED edge rests where it was authored (its `rest_declared` rows, seeded at run creation), or lower after a cliff (bond-arithmetic.md s6, gate 4) | live since 2026-08-22 as the resting point of every edge; since 2026-09-17 only of the unauthored ones. It is a per-CHARACTER disposition, not a per-relationship value. `relationship_priors.update` (`grant_threshold` low/moderate/high, `withdraw_speed` slow/typical/fast) sets the character's own learning rates (`bonds.rates_of`) |
| `current.vault` `[{claim, believed_value, provenance, confidence}]` (`timestamp` is in the schema and **NOT parsed** — `vault.py` drops it, so the engine cannot tell a wound from last week from one thirty years old) | trigger-match on CLAIM TEXT; cost = 1−confidence; sureness wording | the belief fires when an event echoes its words AND budget covers its cost | THE craft field — see below |

## Vault authoring — the rules that matter most

1. **Claims must carry the words events will echo.** Trigger-matching is normalized text overlap
   (gate.py:run_gate) — a belief about "the winter fever" fires on fever events because the WORD
   `fever` is in the claim. A belief phrased abstractly ("what happened that year") can never fire.
2. **Confidence is the recall cost** (cost = 1−confidence): a 1.0-confidence wound costs nothing
   and surfaces always (constitutive memories SHOULD be 1.0); a 0.6 half-noticed suspicion costs 0.4
   and only surfaces on a sharp day. Author faintness as low confidence — it is mechanical, not flavor.
3. **Provenance and sureness reach the prompt** ("craft experience — sure"; "observation —
   fairly sure"): write provenance as the character would name their own source.
4. The vault is the answer key for blind tests (probe-plan.md): author it knowing each belief is
   ground truth a detector may check against.

## World JSON — what is LIVE

| field | mechanism | authoring rule |
|---|---|---|
| `lexicon.attribute_classes` | overt percept extraction | classes = the nouns this book's events are ABOUT; keywords in event-text register (the words your events will actually use, incl. character first names) |
| `lexicon.subtle_cues` | perception-gated fine detail (≥0.60) | what only the skilled notice: progressions, tells, concealments |
| `lexicon.subtle_cue_classes` | which classes imply gated detail | the danger-bearing classes |
| `people[{id, what}]` | entity recognition (insight ≥0.55) | `id` first-token = the name matched in event text; `what` is the IDENTITY record — revealed only on a passed check, so write it as what a knower knows |
| `locations[{id, what}]` | location percept when scene_slice.location set | — |
| `systems` `{name: true\|false}` (2026-09-22, gate systems-registry) | `systems.for_book` — read by both drivers, the pre-run check and the mood replay; an off system's sheet block is emptied before a scene's people are built and its per-beat mover is skipped | leave it out and every legacy system runs. Switchable today: `condition`, `wounds`, `attitude`, `arc`, and the NEW `condition_flow`, `body`, `tells` and `injuries` (each off until a book says `true`) (see **Which systems the book runs**, below); an unknown name, a non-boolean, a core system set `false`, or `condition_flow` without `condition` (or `body` without `condition_flow`, or `injuries` without `condition`) is refused by code before the first beat |

**Currently INERT to the machine** (stored, useful to authors and future modules, zero runtime
effect today): `world` title, `season`, `standing_facts`, `temperament.variability`,
`condition.health/fatigue` (and `condition.injuries` unless the book runs `injuries`), vault `timestamp`. Tuning these changes nothing — the
world-half of decisions arrives via the ledger fold + event text. If a standing fact must reach
the actor TODAY, put it in event text or a vault belief.

## Event authoring (the scripted stream / placed circumstance)

- `text` is the only world the actor perceives this turn: it must CONTAIN the lexicon keywords and
  entity first names you want perceived — unmentioned = imperceptible (the epistemic wall).
- `kind` ∈ the catalog's appraisal types (mundane/care/loss/threat/aid) — it becomes a percept
  attribute and the event's ledger type.
- For probes, `hint` = ground-truth dimensions; the round-trip detector measures the actor's tags
  against it (the keystone accuracy metric). Calibrate hints to the OBJECTIVE event, most turns low.
- The character's wound should rhyme with the event stream: the probe found legibility ("not
  enough" ×5, the Súil thread) is what the cutting room later finds — author the resonance in.

## The world-building pass (activation recipe)

Two triggers, one workflow. **Trigger A — book setup (once):** transcribe/derive the world from
the canon sources. **Trigger B — a hinge (forever after):** the sim reached for world that isn't
there — a `world-faults.md` checkbox in the book folder (written by the chair when it detects a
fault), or the director needing a place/law/person that has no note. The depth rule governs both:
author ONLY what the scene levers on, at the resolution it levers on ("the bible grows from the sim").

The pass itself (the Phase-A chain, design.md — docs are normative, run them in order at whatever
depth the trigger demands):
1. `world-model.md` (the spine): premise → universal law → broader community? → planet → history
   → **present systems & state** (the seam characters query)
2. consult `universal-law.md`, `planet.md`, `history.md`, `present-systems.md`,
   `world-dynamics.md` for the step you're deepening
3. OUTPUT = vault notes in the book folder: the world note's engine block grows (locations,
   standing_facts, lexicon classes/cues), `people/` gains person notes, concepts gain linked
   stubs. Every addition canon-traced; PROPOSED until the author confirms.
4. Lexicon growth rule: new scene domain = new attribute classes IN THE EVENT-TEXT REGISTER
   (the words the events will actually use); subtle cues for what only the skilled notice.

## Provenance discipline (baseline-generation.md — no free sliders)

Every number must trace to the life: "FEAR mean 0.72 ← the winter she lost Súil," never "felt
right." Principals are authored BACKWARD (the person the story needs) and validated FORWARD (the
world plausibly yields them — design.md Phase B). If you cannot say what life event set a value,
the value is not ready.


## Laws — what the world permits, forbids, and makes impossible

Declare rules in the **world note's engine block**, under `laws`. They project into
`bible_laws` when the bible is pinned, and they are what a refusal cites.

```json
{
  "world": "...",
  "laws": [
    { "id": "no-flight", "domain": "physical", "modality": "IMPOSSIBLE",
      "statement": "People cannot fly.", "act": "fly" },

    { "id": "curfew", "domain": "legal", "modality": "FORBIDS",
      "statement": "No one may walk the streets after the third bell.",
      "act": "move", "location_scope": "old_town",
      "teeth": "the watch detains you until dawn" },

    { "id": "physicians-writ", "domain": "legal", "modality": "PERMITS",
      "statement": "A physician's writ permits night travel.", "act": "move" },

    { "id": "dead-walk", "domain": "supernatural", "modality": "IMPOSSIBLE",
      "statement": "The dead walk on the third night.",
      "act": "rest", "epistemic": "known-false" }
  ]
}
```

### `modality` — the field that decides everything

| | meaning | what the gate does |
|---|---|---|
| `IMPOSSIBLE` | physical or supernatural: it **cannot** occur | **denies the circumstance** |
| `FORBIDS` | legal or custom: it **may not**, but it can | **allows**, and attaches `teeth` as a consequence |
| `REQUIRES` | an obligation | allows; the omission is recorded as a violation |
| `PERMITS` | an explicit allowance | allows, overriding a forbid or an impossible |

**Do not reach for `IMPOSSIBLE` to mean "characters shouldn't."** A gate that denied
every *illegal* act would make crime unwritable. Your thief can break the curfew —
that is the story; the `teeth` are what makes it cost something.

### `epistemic` — the known-vs-believed check

Straight from `universal-law.md`, which makes this **mandatory** on every "yes, X
exists". Three values, and the third is the one that matters:

| | meaning | effect on the gate |
|---|---|---|
| `known-true` | it is so | **binds** — can deny |
| `known-false` | people believe it; it isn't so | **never binds** — a superstition cannot constrain your world |
| `contested-unknowable` | the world *deliberately never decides* | verdict is **undecidable**, not allowed |

`known-false` is why the `dead-walk` example above is declared IMPOSSIBLE and still
refuses nothing. `contested-unknowable` is the "are the gods real?" case — the gate
must not invent a fact you withheld, in *either* direction, so it returns
`undecidable` and leaves the call to you. Omit the field and a law is `known-true`.
(`true` and `believed` still load, as aliases for the first two.)

### You start with laws even if you write none

`universal-law.md`'s second meta-rule is *"default to mundane / earthlike; the premise
must **justify** each deviation — the bias is 'no, unless.'"* That is a law set, so the
engine projects it. Write nothing and your world already holds:

| law_id | domain | it says | blueprint |
|---|---|---|---|
| `default-no-flight` | physical | people cannot fly | A — earthlike |
| `default-no-magic` | supernatural | there is no magic | B — the switch is off |
| `default-death-is-final` | persons | the dead do not return | C — the stakes floor |
| `default-future-is-open` | fate | the future cannot be foreseen | D — no operative destiny |
| `default-one-plane` | cosmology | this world is all there is | E — one plane |

**Authoring is overriding, not filling a blank.** Declare a law with the same `act` and
its default disappears — yours decides. Nothing else suppresses it: writing *some*
supernatural law does not switch magic on, because a rule that vanishes by inference is
worse than no rule. A refusal always names what denied it, so `denied_by:
["default-death-is-final"]` tells you the blueprint refused, not you.

Turn them all off with `"blueprint_defaults": false` in the world block — for a world
whose step 1 is fully authored and wants no rules it didn't write.

### The three switches — the questions you may not defer

Most of the guide may be left *"undetermined until levered."* Three may not
(`universal-law.md:12`), because planet, history and present all fork on them:

```json
{ "switches": { "magic": false, "divine": false, "beings": false } }
```

`bible.completeness(world)` reports what's missing — `switch-unanswered` for each one
left open, `unbounded-switch` if you answer `true` and write no `supernatural` law to
limit it (*"a power with no stated limit is the director's get-out-of-jail card"*), and
`epistemic-unstated` for a law in `supernatural` / `persons` / `fate` / `cosmology` that
never says known-vs-believed. It **reports**; it does not block. `bible.build(...,
strict=True)` is the version that refuses.

### Which systems the book runs — the switch beside the switches

Not every book needs every system the engine has. The world note says which it runs:

```json
{ "systems": { "wounds": false, "attitude": false } }
```

| system | off means |
|---|---|
| `condition` | no `current.condition` block is needed; the stage directions say nothing of energy; memory runs on a full budget, and the arc reads no load |
| `wounds` | no scar is minted, tested or shown |
| `attitude` | no attitude (`current.toward`) accrues, fades or is shown |
| `arc` | lasting beats move no resting level |
| `condition_flow` (**OFF by default** - a new system; `true` turns it on, and it needs `condition`) | energy and stress stay where the sheet or a scene put them. ON: each beat costs its minutes and, for whoever acted, what it did to them; fear, anger and grief running high build the load; between scenes each character's own gap follows the standard day - night hours (22:00-06:00) rest, day hours awake - unless the scene file's `condition` entry says `gap: rested` or `gap: awake` (`src/engine/condition.py`; its constants are START values with falsifiers) |
| `tells` (**OFF by default** - a new system) | every listener reads every other actor's act whole and the event reader is not asked. ON: the reader marks the small signs in each act only a sharp eye would catch (at most three quoted spans); a listener whose `baseline.skills.perception` clears the subtle-cue line (0.60) reads them and is told them as a percept, one who does not reads the act with those words cut; each beat's manifest records what was hidden and caught (`src/engine/tells.py`) - so a failed check REMOVES the detail, as `scene-assembly.md` always said. In a book that also runs `condition_flow`, a worn mind catches less (gate tired-eyes): the skill is weighed by what the mind has left, read the way the memory budget reads it, so a sharp listener who arrives spent can miss what they would catch rested - a mind with nothing left keeps half its eye |
| `body` (**OFF by default** - a new system; needs `condition_flow`) | no act costs physical effort and the event reader is never asked (its prompt is byte-identical). ON: each sheet carries `baseline.body.strength` (frail/slight/ordinary/strong/powerful); the reader names each act's exertion (none/light/moderate/hard/extreme) with a quote; the engine charges it for the beat's minutes against that strength, which also weighs the waking-time drain (`src/engine/body.py`). Energy then has THREE stores (gate energy-reserves): a shared pool, a mind reserve and a body reserve - effort never touches the mind's, thinking and feeling never the body's; memory reads the mind's side and the actor is told both when they differ |
| `injuries` (**OFF by default** - a new system; needs `condition`) | no injury is marked, kept or shown and the event reader is never asked (its prompt is byte-identical). ON: the reader marks harm done to a body in each act - who, the quote that shows it, and `minor`, `serious` or `grave`; each injury rides its event into the log and heals over STORY time on the clock by that word (fresh, then healing, then gone - a grave one leaves a lasting mark); the one hurt, the one who acted and whoever was present are told it every beat until it heals, and each beat's manifest records what it told. A sheet's `current.condition.injuries` - `{what, severity, ago?}` - are the hurts a character carries on page one, told to that character alone (`src/engine/injuries.py`). No bar and no number. One mechanical effect (gate injury-weakens): in a book that also runs `body`, a hurt still fresh or healing makes the body count strength words lower - one for a serious injury, two for a grave one, the worst governing, minor none - so its effort and waking time cost more until it heals, in the drivers, the opening's gap and the replay alike |

The core — `emotion`, `perception`, `memory`, `bonds`, `attachments`, `laws` — is listed in
`src/engine/systems.py` so the author can see the whole engine, and cannot be switched off
until each has its own proof that off changes nothing else. The pre-run check stops demanding
an off system's block, and warns on one authored anyway (it does nothing). OFF stops what a
system does from the next scene on; what it already did stays in the story. A book that
declares a set records it on every beat's manifest, so the mood replay strips exactly what the
beat ran without; a book that says nothing — or lists every system `true` — records nothing and
writes exactly the rows it wrote before the switch existed (`tests/test_systems.py`).

### The rest

`domain` follows the blueprint: `physical`, `supernatural`, `persons`, `fate`,
`cosmology` come from `universal-law.md`'s step-1 rubric (A–E); `legal`, `custom`,
`economic` from `present-systems.md`'s step-4. `act` and `location_scope` narrow when a law bears on a move; leave them out and it
bears on everything. `teeth` is the consequence a violation attaches. `source_note`
is provenance — the note a citation points back to. Every law needs an `id` (so it
can be cited) and a `statement` (so a refusal can quote it); a malformed law fails
the build loudly rather than being quietly repaired.
