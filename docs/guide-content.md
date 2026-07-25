# Content Guide — authoring a book's inputs

For a session AUTHORING per-book content (design.md Phase B). The other guides tell you how to
RUN (guide-operating.md) and how to EXTEND (guide-engine.md); this one tells you what to WRITE —
and, critically, **what each value actually does at runtime**, so you never tune a dead knob.
Precedence as everywhere: code > tests > this guide > design docs for what IS.

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
| `fixed.genotype` (6 axes) | state.build_profile gains | threat_reactivity→FEAR, approach_drive→SEEKING, affiliation_attachment→CARE+GRIEF, anger_proneness→RAGE, effortful_control→decay speed, sensitivity→global | vocabulary is EXACTLY `low\|typical\|elevated\|high` (.75/1.0/1.2/1.3); anything else silently reads as typical |
| `baseline.temperament` 7×`{mean,…}` | decay target + direction deviation marker | where emotions REST; "more than is usual for you" fires past ±0.15 from mean | the mean IS the personality's resting face; an anxious character = high FEAR mean, not high starting affect |
| `baseline.traits` `{mean}` | HEXACO slopes on gains | emotionality→FEAR/GRIEF sensitivity, agreeableness→RAGE (negative), extraversion→PLAY/SEEKING | only those three are read today; others are stored context |
| `baseline.model` (schwartz/moral_foundations/needs weights) | relevance weighting (state._DIM_VALUE_KEYS) | the same event lands harder on the character whose values it touches — this is where two people diverge | author only the levered weights; a MISSING key reads neutral 0.5 (depth rule: silence = average, not zero) |
| `baseline.drives.goals` | gate goal-salience + prompt | goal-bearing beliefs recall FIRST under budget | phrase goals with the nouns the vault claims use — salience is word overlap |
| `baseline.skills` | deterministic checks | perception ≥0.60 sees subtle cues; insight ≥0.55 recognizes entities; combat gates harm/threaten capability | these three are consulted today; others ride the stable prefix as context |
| `baseline.voice`, `drives.fears_wounds`, `orientation` | stable prefix verbatim | the LLM acts on them; the ENGINE never parses them | written for the actor's eyes — craft text, not config |
| `current.affect` 7×[0,1] | the starting CURRENT tier | turn-zero emotional state | start at/near temperament means unless the book opens mid-crisis |
| `current.condition.energy` + `.allostatic_load` | recall budget = energy×(1−load/2); direction bands | a drained character misses faint connections and reads "worn thin" | this is a LEVER: deplete to make a character miss what they know (relevancy-gate.md §energy — the director's legitimate cognition lever) |
| `current.active_goals` | same as drives.goals | — | keep in sync with drives.goals |
| `current.relationships` `{target: {trust,affinity,respect,debt}}` | volatile.edges → direction phrases | "Joss: guarded trust, fond of them" in the prompt | **keys MUST equal world.people ids** — edges surface ONLY for entities recognized in the PerceptSet (scene.py:_build_edges); a misspelled key never appears |
| `current.vault` `[{claim, believed_value, provenance, timestamp, confidence}]` | trigger-match on CLAIM TEXT; cost = 1−confidence; sureness wording | the belief fires when an event echoes its words AND budget covers its cost | THE craft field — see below |

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
