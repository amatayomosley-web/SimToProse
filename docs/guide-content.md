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

## The machine's complete input contract

1. **World JSON** — the book's place + its perception vocabulary (template: `world/ashford-slice.json`)
2. **Character JSON(s)** — one per principal (template: `characters/maren-healer.json`;
   minimal alien example: `tests/test_portability.py` CHAR/WORLD)
3. **Run config** — `{"catalog_version": 1, "models": {...}, "prompt_versions": {...}}` at create_run
4. **Per turn, the scene_slice** — `{"event": {"text", "kind"}, "recent": [...], "location": str|None}`
   (scripted for probes; circumstance-placed by the director later; built from the ledger fold at
   full runtime)

That is everything. The machine reads nothing else.

## Character JSON — what is LIVE (field → mechanism → effect → authoring rule)

| field | mechanism | observable effect | authoring rule |
|---|---|---|---|
| `fixed.name` | stable prefix | identity in every prompt | — |
| `fixed.genotype` (6 axes) | state.build_profile gains; **draw one with `scripts/make_genotype.py --seed <anything>`** for background/supporting cast — principals are authored backward from the character the story needs | threat_reactivity→FEAR, approach_drive→SEEKING, affiliation_attachment→CARE+GRIEF, anger_proneness→RAGE, effortful_control→decay speed, sensitivity→global | vocabulary is EXACTLY `low\|typical\|elevated\|high` (.75/1.0/1.2/1.3); anything else silently reads as typical |
| `baseline.temperament` 7×`{mean,…}` | decay target + direction deviation marker | where emotions REST; "more than is usual for you" fires past ±0.15 from mean | the mean IS the personality's resting face; an anxious character = high FEAR mean, not high starting affect |
| `baseline.traits` `{mean}` | HEXACO slopes on gains | emotionality→FEAR/GRIEF sensitivity, agreeableness→RAGE (negative), extraversion→PLAY/SEEKING | only those three are read today; others are stored context |
| `baseline.model` (schwartz/moral_foundations/needs weights) | relevance weighting (state._DIM_VALUE_KEYS) | the same event lands harder on the character whose values it touches — this is where two people diverge | author only the levered weights; a MISSING key reads neutral 0.5 (depth rule: silence = average, not zero) |
| `baseline.drives.goals` | gate goal-salience + prompt | goal-bearing beliefs recall FIRST under budget | phrase goals with the nouns the vault claims use — salience is word overlap |
| `baseline.skills` | deterministic checks | perception ≥0.60 sees subtle cues; insight ≥0.55 recognizes entities; combat gates harm/threaten capability | these three are consulted today; others ride the stable prefix as context |
| `baseline.voice`, `drives.fears_wounds`, `orientation` | stable prefix verbatim | the LLM acts on them; the ENGINE never parses them | written for the actor's eyes — craft text, not config. **A wound needs an operational twin in `baseline.catalog` or it is prose the engine cannot compute** — `lint_book.py` warns when a `trigger` list has no matching row |
| `baseline.catalog.rows` `[{when, lever, op, magnitude, source}]` | levers.active_rows → levers.effective → the TIER-3 vector the direction is staged from | *this* is how "brave, but terrified of spiders" becomes arithmetic: a row fires on a standing fact and multiplies a primitive. Four condition kinds: `percept` (words in the event), `present_edge` (an axis threshold on someone present), `affect_at_least` (emotion modulating emotion), `condition_at_most` (state) | `lever` must be a PRIMARY or it fails loud; rows are validated even when inactive. Calibrate against the direction bands (0.25/0.55/0.80) or a fired row is invisible inside a band |
| `current.affect` 7×[0,1] | the starting CURRENT tier | turn-zero emotional state | start at/near temperament means unless the book opens mid-crisis |
| `current.condition.energy` + `.allostatic_load` | recall budget = energy×(1−load/2); direction bands | a drained character misses faint connections and reads "worn thin" | this is a LEVER: deplete to make a character miss what they know (relevancy-gate.md §energy — the director's legitimate cognition lever) |
| `current.active_goals` | same as drives.goals | — | keep in sync with drives.goals |
| `current.relationships` `{target: {trust,affinity,respect,debt}}` | volatile.edges → direction phrases; `levers` `present_edge`/`target_edge` rows; **`bonds.observe` MOVES them every beat someone acts** | "Joss: guarded trust, fond of them" in the prompt — and what you author is their EXPECTATION, so a high trust makes a betrayal catastrophic and a low one makes the same act barely register | **keys MUST equal world.people ids** — edges surface ONLY for entities recognized in the PerceptSet (scene.py:_build_edges); a misspelled key never appears. Author the STARTING read; the run moves it. `scripts/direct.py` moves none (no second party) |
| `baseline.relationship_priors.default_trust` | `bonds.drift` resting point | where an unreinforced edge RELAXES to when a scene declares `elapsed` — affinity fades fastest, debt slowest | live since 2026-08-22; before that it was stored and read by nothing. It is a per-CHARACTER disposition, not a per-relationship value |
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

**Currently INERT to the machine** (stored, useful to authors and future modules, zero runtime
effect today): `world` title, `season`, `standing_facts`, `temperament.variability`,
`condition.health/fatigue/injuries`, vault `timestamp`. Tuning these changes nothing — the
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
      "act": "move", "location_scope": "city_hub",
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

### The rest

`domain` follows the blueprint: `physical`, `supernatural`, `persons`, `fate`,
`cosmology` come from `universal-law.md`'s step-1 rubric (A–E); `legal`, `custom`,
`economic` from `present-systems.md`'s step-4. `act` and `location_scope` narrow when a law bears on a move; leave them out and it
bears on everything. `teeth` is the consequence a violation attaches. `source_note`
is provenance — the note a citation points back to. Every law needs an `id` (so it
can be cited) and a `statement` (so a refusal can quote it); a malformed law fails
the build loudly rather than being quietly repaired.
