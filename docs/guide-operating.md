# Operating Guide — running books on the engine

For a session RUNNING simulations. Recipes in execution order; concepts only where a wrong mental
model causes wrong action. Every claim cites its source; when this guide and the code disagree,
the code is right and this guide has a bug — fix the guide.

## The loop (one turn) — the mental model

```
scene_slice (you build: event + recent + location)
  → scene.assemble(char, world, slice, affect, condition)   # deterministic packet
  → prompt.build_turn_messages(packet, event_text, temperament)
  → ONE LLM call (action + thought + tags in one pass — they cannot desynchronize)
  → consolidation.validate_tags(tags, packet percepts, skills)
  → ok=False: tags never move state | flags: illegitimate dims stripped
  → state.appraise → state.decay → new affect
  → Ledger.append_turn(TurnCommit)                          # atomic: all rows or none
```
Reference implementation: `tests/coherence_probe.py:run_probe` — copy its shape, including the
per-turn try/except (any turn error degrades, records `turn-skipped`, never crashes the run).

**The packet** (what `assemble()` returns — the loop's most-referenced object):

| key | shape | consumed by |
|---|---|---|
| `packet["stable"]` | identity prefix dict (byte-stable per char — the prompt-cache unit) | `build_turn_messages` (system msg) |
| `packet["volatile"]["state"]` | `{affect, condition}` (numbers — never shown to the LLM raw) | direction rendering |
| `packet["volatile"]["percepts"]` | `[Percept{ref, channel, fidelity, attributes, recognized_as?}]` | the prompt AND `validate_tags` |
| `packet["volatile"]["recall"]` | `[{ref, claim, confidence, provenance}]` | the prompt |
| `packet["volatile"]["goals"]` / `["edges"]` | active goals / relationship edges to present entities | the prompt |
| `packet["manifest"]` | decision-input manifest (record-contract) | `TurnCommit(manifest=...)` |
| `packet["recall_refs"]` | belief refs list | `TurnCommit(recall=...)` ← note the NAME CHANGE: packet key `recall_refs` feeds TurnCommit field `recall` |

## Recipe: start a new book

**Books live in the author's Obsidian vault, NEVER in this repo** (the seam law, repo level).
A book is a folder of linked markdown notes — `world/`, `characters/`, `people/` — loaded by
`--vault`. Each note: prose canon + `[[links]]` on top, ONE fenced ```json engine block below;
characters add a `## Beliefs` section (`- (confidence, provenance) claim [[links]]`). The
`[[links]]` are LIVE: a belief fires when a trigger matches its claim text OR a linked note's
name — author-controlled recall edges. Template: any `vault/books/<your-book>/` folder following this layout.
The JSON shapes below are the engine-block contract (this repo's JSONs are test fixtures only).

1. **The world note** engine block: `world`, `season`, `standing_facts`, `locations[{id,what}]`,
   and the **lexicon** — this book's perception vocabulary:
   `lexicon.attribute_classes {class: [keywords]}` (overt percepts), `lexicon.subtle_cues
   {cue: [markers]}` (perception-check-gated), `lexicon.subtle_cue_classes [class,...]`.
   People go in `people/` notes (type: person; first prose line = the gated identity record).
   No lexicon = generic extraction (kind + leading words, no subtle percepts) — legal but thin.
2. **Character notes** (`characters/<Name>.md` — markdown with ONE fenced ```json engine block,
   per the note format above; `load_book` reads only `*.md`, and this repo's `characters/*.json`
   are engine TEST FIXTURES, not the vault format) per `docs/character-schema.md`. Required by the
   engine (build_profile/assemble validate these): `fixed.name`, `fixed.genotype` (6 axes,
   values low|typical|elevated|high), `baseline.temperament` (all 8 primaries × {mean,variability}),
   `baseline.traits` ({mean} per trait), `baseline.model` (schwartz/moral_foundations/needs weights),
   `baseline.drives`, `baseline.skills`, `baseline.voice`, `current.affect` (7 × 0..1),
   `current.condition` ({energy, allostatic_load, ...}), `current.active_goals`,
   `current.relationships`, `current.vault` ([{claim, believed_value, provenance, timestamp,
   confidence}]). Template: `characters/maren-healer.json`. Worked alien example (inline):
   `tests/test_portability.py` CHAR/WORLD.
3. **Open the run**:
   ```python
   led = Ledger("runs/<book>.db")
   led.create_run(run_id, {"catalog_version": 1, "models": {...}, "prompt_versions": {...}})
   led.register_character(run_id, char_id, char["fixed"], char["baseline"])
   ```
   Config MUST carry `catalog_version` (ledger.py:create_run raises otherwise; current correct
   value: `1` — it is replay provenance, stored verbatim, not enforced against anything). Pin model
   ids and prompt versions there — replay against a different catalog is not replay (run-lifecycle.md).
4. **The complete per-turn commit** (every meaningful TurnCommit kwarg — records.py is the contract):
   ```python
   led.append_turn(TurnCommit(
       run_id=run_id, turn=i, actor=char_id,
       thought=turn["thought"], action=turn["action"],
       tags=tags, affect=dict(affect),
       condition=dict(char["current"]["condition"]),   # required-by-validate; dict, may be {}
       validation=validation,                           # validate_tags() result
       events=[Event(type=tags.get("type","mundane"), payload={...}, actor=char_id)],
       manifest=packet["manifest"], recall=packet["recall_refs"]))
   ```

**Full manifest**: `docs/new-book-manifest.md` — what the user COPIES (`runs/_TEMPLATE`), CREATES
(the six directories and their notes), and REFERENCES without copying (`template-scene-blueprint.md`,
`actor-direction-format.md`). It covers `scenes/` and `chapters/`, which this recipe does not.

**New-book checklist** (everything above in one glance): world JSON (locations · people ·
standing_facts · lexicon) + character JSON (fixed.genotype · baseline.temperament×7 · traits ·
model · drives · skills · voice · current.affect/condition/goals/relationships/vault) →
`Ledger(db)` → `create_run(run_id, {"catalog_version": 1, ...})` → `register_character` →
per turn: slice → `assemble` → `build_turn_messages` → LLM → `validate_tags` → strip/floor →
`appraise` → `decay` → `append_turn` → (boundary: `persist_snapshot`) → on restart: `resume`.

## Recipe: lint before you run

The linters read each author file against its contract - `src/engine/contracts_sheet.py`,
`contracts_world.py`, `contracts_scene.py`, whose field tables the three blueprints carry, generated - and
REPORT:
```bash
python scripts/lint_book.py --vault "<book>"             # a real book: the world and every sheet
python scripts/lint_book.py --book ashford --char maren  # a fixture
python scripts/lint_scene.py --book "<book>" --scene <file>.json
```
A draft always loads and always lints, and the linter never edits. Each finding says what it is: a field
the engine would misread, or a required one absent; a key nothing declares (nothing reads it; an annotation
begins with `_`); a RETIRED field (it names what took its place, and whether to prune, move or refuse it); a
field nothing reads; advice. Every finding that refuses a run (below) is an ERROR - exit 1 - so a book that
lints clean starts. The linters also run the checks that span files (a relationship key that is not a
`world.people` id, a cast id that is not a character), and lint_scene calls errors some facts and craft rules a run
does not check (a subject that names nobody, a location or a hold's place the world does not register, a hold for
someone outside the scene, an act no law keys, a drive that copies the situation, a prop count outside three to
five).

**The run itself refuses what would break it** (gate run-start-refusal, 2026-09-25). Before either driver
opens the chronicle - `scene.py` reads the world, the scene's cast and the scene file as written; the chair
(`direct.py`) the world and its one character - an error, an undeclared key, or a retired field whose content
must move or which was refused stops the run with `CONTRACT_RUN_REFUSED`, naming each file and path, and
nothing is written. What loses nothing - a pruned field, one nothing reads, advice - is counted in one line
(`contract: nothing refused; ...`) and the run goes on. Only the sheets of those who play are checked; every
sheet in the book is still pinned with the run, so lint the whole book first - it lists the same, and what
reaches nothing too.

## Recipe: run a burst (the production rhythm)

**The director's chair** ("we are the directors", 2026-06-11) is the operating tool:
```bash
python scripts/direct.py --vault "<path to the book folder in your vault>" --char <char>   # a REAL book
python scripts/direct.py --book ashford --char maren                                        # engine test fixture
# --stub for deterministic | type a circumstance per turn | status | quit (parks; --resume <run_id>)
python scripts/direct.py --vault "<book>" --char <char> --at "day 1 06:00" --lasts 10m      # declares WHEN this session opens
python scripts/direct.py --vault "<book>" --char <char> --resume <run_id> --at "day 1 07:00"  # a LATER session, same chronicle
python scripts/direct.py --vault "<book>" --char <char> --resume <run_id> --no-keeper       # skip the canon gate this session
```
A real book's chronicle db lands in the BOOK's `runs/`, beside its notes — the machine repo
holds no book state.
You place circumstance ONLY — the tool has no affordance for writing the character's state or
words (steering = circumstance, never the character's hand; the discipline is structural).

**`--at` / `--lasts` / `--keeper` (one clock, two drivers, 2026-09-19).** The chair reads the SAME
clock a scene does, through `src/engine/passage.py:open_scene`: `--at "day N HH:MM"` (or bare
`"N HH:MM"`, or the JSON `{day, time}` shape scene cfgs use) declares when THIS invocation opens —
before its first turn, the gap since the chronicle's last opening (a prior chair session, or a
scene) is derived and applied: emotion decay, drift toward each edge's rest, wound erosion, arc
erosion, the toward vectors, exactly as a scene applies them. `--lasts` (minutes, or `"90m"`/`"2h"`/
`"1d"` sugar) says how long this session is authored to run; a lulled remainder is owed to whichever
session opens next. **Absent `--at`, nothing changes: no clock row is written, and the chair says so**
(`chair: no --at given — running on --minutes-per-turn only (no scene clock declared)`) —
`--minutes-per-turn` stays the chair's own knob for decay BETWEEN this invocation's own beats, a
separate and smaller thing than the clock between invocations. Since 2026-09-25 the gap is the
character's OWN (gate own-timelines: from the last beat they were in a room, a scene or a chair), and
the chair stays in their present (gate flashback-windows): an `--at` before their own latest scene is
refused (`CLOCK_RUNS_BACKWARDS`), and so is a session with no `--at` right after a scene set in their
past (`CLOCK_CHAIR_IN_A_WINDOW`). The author's rules for time - own timelines, overlapping scenes,
flashbacks as windows - are `docs/authoring/BLUEPRINT-scene.md` section 11. The canon gate — the same one a
scene runs (below) — fires over whatever this invocation committed, once it ends; see **the lore
licence's debt**, next, for when and what it reports.

**The lore licence's debt, and the keeper on by default (owner decision D1, 2026-09-19).** Every
saying a character commits — a double-quoted span inside their `action` — lands in the log with NO
facts extracted from it; only the keeper's noticing pass reads a saying closely enough to index it,
and until that happens it is invisible to the fence (`claims.about`, `read_api.established` — see
`docs/keeper-of-truth.md`). Before this date that noticing pass ran only when an invocation passed
`--keeper`, so a chair or scene session that forgot the flag (the common case: a real book's first
three live scenes all ran keeper-off) left its sayings permanently unindexed with nothing saying so.
Now: **the canon gate runs by DEFAULT on every non-`--stub` invocation of both `direct.py` and
`scene.py`** — `--keeper` is still accepted (it is a no-op there; it still forces the gate to run
under `--stub`, same as always) and `--no-keeper` is the opt-out. Either way, at the end of every
invocation — stub or live, keeper run or skipped — the driver prints ONE line naming the debt:

```
lore: 3 saying(s) since turn 12 await the keeper — run without --no-keeper, or scripts/keeper.py --prompt-only
lore: 3 saying(s) still unextracted (the keeper asked nothing under --stub)
lore: 3 saying(s) still unextracted after the keeper's pass
lore: every saying has been noticed
```
The first fires when the gate did not run this invocation; the second when it ran but under
`--stub` (asks nothing, by design); the third when it ran live and sayings are STILL outstanding —
extraction is the keeper's reading, not a guarantee it reads everything cleanly, so this can be
nonzero even after a real pass; the fourth is the clean state. `scripts/doctor.py`'s full report
carries the same count per run, as an AMBER `LORE-UNEXTRACTED` line, so the debt is visible on a
database even between invocations. **To clear it:** run the driver WITHOUT `--no-keeper` (the
default already does this), or run the keeper directly — `scripts/keeper.py --vault "<book>" --run
<run_id> --prompt-only` emits the noticing prompt, and `--propose <replies.json>` records what a
model reports back. A saying committed bare cannot be fixed in place (`claim_extracts` is
append-only, like every table hard rule 2 covers) — the debt line is about not LEAVING one, not
about repairing one after the fact.

≤5 turns per burst, ONE LLM call per turn, human inspection between bursts (decided 2026-06-10).
Model: haiku (`anthropic/claude-haiku-4.5`) — measured sufficient on the assembled spine
(blind judge 2026-06-11: no degradation vs pre-spine; sonnet = 3×/token buy-certainty fallback).
A 5-turn haiku burst costs cents; prompt-cache the stable prefix (it is byte-stable by design).

Probe-harness equivalents: `python tests/coherence_probe.py --run --db --max-calls 5`.

## Recipe: run a multi-character SCENE (emergent, persisted)

The chair (above) runs ONE actor against placed circumstance. The scene runner runs a SCENE —
several characters push the conversation, the floor passes by URGE (salience + addressed-bonus +
disruption-stake − recency − inhibition), and each beat commits to the ledger:
```bash
python scripts/scene.py --vault "<book>" --scene <scene.json>                     # a director-authored scene (the canon gate runs by default)
python scripts/scene.py --vault "<book>" --scene <scene.json> --resume <run_id>   # a LATER scene, same chronicle
python scripts/scene.py --vault "<book>" --stub                                   # the built-in DEFAULT_SCENE, no API, no canon gate
python scripts/scene.py --vault "<book>" --scene <scene.json> --no-keeper         # skip the canon gate this scene
```
The canon gate (2026-09-11; default-on 2026-09-19) notices what was said and rules the tested
claims — under `--stub` it rules nothing and prints the contested ones; see **the lore licence's
debt**, above, for the closing `lore:` line either way carries.
A scene cfg JSON (the director's interface): `{name, situation, subject:[id,group], cast:[{id,drive}], pov?}`.
A drive is a genuine standing WANT, blind to the scene's outcome (design.md scene-goals) — never the
ending in a costume. Each beat persists (turn + arc baseline diff + acquired/witnessed memory + any
overheard name-reveal); a name-leak the masking wall can't stop is REGENERATED, then the beat is
rejected if it persists (faithful_turn — a leak never enters the chronicle). At scene end a SCENE
BOUNDARY lands in the `scenes` table — the unit the cutting room + book narration iterate. `--resume`
rehydrates the cast the prior scene evolved (arc diffs + acquired vault + last affect) and continues
the turn numbering.

## Recipe: review a scene — the critic (continuity + voice)

The non-author check (design.md layer 6). Strong-model judgment, run Claude-in-the-loop (key-free):
```bash
python scripts/critic.py --vault "<book>" --run <run_id> --prompt-only   # emit the prompt → hand to Claude
python scripts/critic.py --vault "<book>" --run <run_id> --stub          # clean review, no API
python scripts/critic.py --vault "<book>" --run <run_id> --correct       # ...and APPEND the corrections
```
Reviews ONE RECORDED SCENE AT A TIME (2026-09-18): `--prompt-only` prints a list with one prompt per
scene row, and the model run prints `{scenes: [{scene_no, label, turns, continuity, voice}]}` — one
entry per scene, each judged on its own turns against the world's canon. A run with no scene rows
(the stub probes) is reviewed whole and returns the flat `{continuity, voice}`. Before this the
critic read the whole run as one transcript under a 6,000-char cap sized for the haiku probe's
121-char beats; the first live book (2,900 chars a beat) reached it with only its first 3 beats. The caps are
now sized to a 14-beat scene of that book and STILL WARN on stderr when anything falls off — read
those lines; a clean verdict never covers what the model did not see.

**`--correct` (2026-09-19) — the compensating-event half** (`consolidation-loop.md` open-q 3).
After the review, it appends ONE `correction` event per CONTINUITY flag at the run's next tick and
prints `N correction(s) appended (M supersede a world event)`. The correction names the flagged
turn's world-moving event ids in `supersedes`, and from that tick on the fold skips them — the
snapshot reads as if the act never happened, while the log keeps both the act and the correction
(hard rule 2: nothing is edited, nothing is deleted). Then `cut.py` marks the turn `corrected` with
the critic's words and `doctor.py` reports the per-run count.

Three things to know before using it. It is OPT-IN: the flags are a strong model's reading, and
appending is a write to an append-only log that cannot be taken back — read the report first. It is
IDEMPOTENT on `(turn, issue)`, so re-running the same review appends nothing; a differently-worded
finding on the same turn is a new correction. And it corrects the WORLD only: whatever that beat
already appraised into the characters (bonds, readings, wounds) stands — `measurement.md` open item
3. VOICE flags produce nothing; there is no event to supersede. Under `--prompt-only` the flag is
refused rather than ignored (there is no review yet to correct from). The rewrite half — changing
the prose — is still the author's and is not built.

## Recipe: narrate — chronicle to prose (POV-bound)

Renders committed turns into close-third prose bounded to ONE POV's knowledge (narration.md): the
POV's interiority + everyone else OBSERVABLE-only (never another mind — the dramatic-irony engine).
```bash
python scripts/narrate.py --vault "<book>" --run <id> --pov <char> --prompt-only   # one scene
python scripts/narrate.py --vault "<book>" --run <id> --book --prompt-only          # whole chronicle, POV per scene
```
`--book` renders every recorded scene in order, each from its scene's recorded pov (multi-POV =
switch the boundary per scene, never violate it). `--prompt-only` emits the prompt for Claude-in-the-loop.

## Recipe: the dailies — the cutting room's VIEWS

After a chronicle exists, the deterministic views that make a cut DISCUSSION possible (cutting-room.md:
the engine SHOWS, the discussion DECIDES — automated selection is deliberately NOT built):
```bash
python scripts/cut.py --vault "<book>" --run <run_id>
```
Prints the shot list (scenes + cast), biggest-moment candidates (beats by appraisal magnitude +
durability — candidates, NOT the cut: magnitude is consequence, not meaning), what changed each
person (arc hinges), and what each learned (acquisitions).

## The hybrid — who runs what (decided 2026-06-13; the seats re-decided 2026-09-11)

Character TURNS run on the model `--model` names (the local Ollama default, or any OpenRouter id)
— high-volume acting. The CRITIC + NARRATOR run on the STRONG model, Claude-in-the-loop:
`--prompt-only` builds the deterministic prompt, Claude (in a session) produces the review/prose.

**THE APPRAISER SEATS RUN ON THE FRONTIER MODEL, ALWAYS** (owner, 2026-09-11: *"since this will be
the basis for most of the system we will not use local models, we need accuracy"*). After every
live turn the EVENT seat rates the act and the EMOTION seat reads the interior
(`scripts/appraiser.py`), both through the one seam `scripts/provider.py`: OpenRouter, default
`anthropic/claude-opus-5` (override `SWE_SEAT_MODEL`), temperature 0, the constant prefix marked
for prompt caching, every call logged in `llm_calls`. That needs the key: set `SWE_ENV_FILE` to
the file holding `OPENROUTER_API_KEY` (or a gitignored `.env` at the repo root); without it a live
run stops at the first seat with `PROVIDER_NO_KEY`. `--stub` runs need no key and no model: the
actor's stub self-tags are the seats' double.

**A seat's prompt is a CONTRACT, and changing it breaks the cache's key, not the seat.** Every event
or emotion reply recorded on disk under a book's `runs/seats-<scene>` directories (and any
`--emit` re-answer staging dir) was fanned out against the SYSTEM prompt as it stood that day; when a
gate changes `_EVENT_SYSTEM` or `_EMOTION_SYSTEM` (a new rule, a new skeleton field — most recently
gate `seat-attribution`, 2026-09-19, which added the `attribution` field), the stored replies no
longer key-match the prompt `tests/reanswer_event_seat.py` would build today. That tool's `--verify`
still passes across a contract change (it compares the rebuilt USER turn only — the part that does
not change), but re-answering the beats under the new contract is a FRESH FAN-OUT, not a replay: the
old directory is a record of what the seat said under the old rules, not a cache of what it would
say now.

## Recipe: read a novel through the engine (the read-along bench)

```bash
python scripts/readalong.py --book red-badge --stub --thermometer 5   # deterministic; no model
python scripts/readalong.py --book red-badge --thermometer 5          # the seats on the frontier model (needs the key)
python scripts/readalong.py --book red-badge --patterns <run>         # the patterns report for a finished run
```

**Without a key: emit, answer, replay** (2026-09-11; owner: *"Use subagents"* — *"can you not
batch?"*). The seat prompts are built from the passage alone, so every prompt of a run can be
written out first and answered out of process, ONE FRESH AGENT PER PROMPT — never a batch, because
an agent that has seen its own earlier answers is carrying state the engine is supposed to carry
(emotion-arithmetic §7). The answers replay through the same seam and the same parsers, keyed on
the sha256 of the prompt, so an answer only ever meets the prompt it was written for:

```bash
python scripts/readalong.py --book red-badge --thermometer 5 --emit "$SWE_BOOKS/readalong/red-badge/seats"
#   -> <key>.prompt.json per seat call (the user turn + a pointer to system.<purpose>.<hash>.txt, written once)
#   answer each with a fresh agent that reads the system text and the one prompt and writes <key>.reply.txt
python scripts/readalong.py --book red-badge --thermometer 5 --replies "$SWE_BOOKS/readalong/red-badge/seats"
#   -> refuses by PROVIDER_REPLY_MISSING while any prompt is unanswered; otherwise the run as above,
#      the seat recorded as `subagent:opus` (--model to say otherwise), every call in llm_calls with NULL
#      token counts, a malformed answer an idle beat with a `seat-refused` row
python tests/appraiser_bakeoff.py --idle --n 30 --model subagent:opus --emit "$SWE_BOOKS/readalong/_idle"
python tests/appraiser_bakeoff.py --idle --n 30 --model subagent:opus --replies "$SWE_BOOKS/readalong/_idle"
```

The emit directory carries book text: it lives beside the book, never in this repo. Any driver
replays the same way with `SWE_SEAT_REPLIES=<dir>` in the environment.

**First live finding (Red Badge on Opus, 2026-09-11, 221 answers):** the model wrote the path name
in lower case in 105 answers (36 of 37 thermometer answers), and every one was refused as a rung
not on the path — a refusal naming the wrong defect. The parsers now match the PATH key without
regard to case (`readings.canonical_path`), as the rung name already was in `rungs.index_of`. The emotion-seat contract now
reads *one of the nine, written in capitals exactly as headed* — prompt version 4 (2026-09-11), which
also carries the ninth ladder; the two corpus reads above were under version 3. Two answers named a `lands_on` person not in the cast and
stay refused: an idle beat with a `seat-refused` row each.

A book is a directory under `$SWE_BOOKS/readalong/<slug>/` (never in this repo): `text.txt`,
`chapters.json` (offsets and the story clock `at`/`lasts` per chapter, authored from the text),
`characters/<id>.json` (the protagonist's sheet — rest words, genotype, NO wounds; the story
mints them) and `cast.json`. The chronicle lands in `<slug>/runs/`. **What the live runs are FOR** (owner, 2026-09-11):
not a grade — the patterns real text shows, from which the rules for the numbers are made. The
report gives, per path with counts: persistence after a peak in beats and story-minutes (→ the
half-lives), the longest elevated streak (→ λ), the height delta when the same thing lands again,
split for people by whether they are on the page (→ repetition and its two directions), the rung
at which a concept once read at the top comes back and for how long (→ the wound's multiplier),
which paths fire together (→ the basis), the idle rate (→ p; on the two control books it is the
noise floor), and the concept categories the seat wanted that the registry lacks. `--thermometer N`
runs a second, measurement-only seat every N beats that reads the character's STANDING level on
each ladder (the sensor is blind to it by design); its levels are logged beside the run and give
the half-life estimate directly, and the report's `state_vs_thermometer` block compares the
engine's CARRIED state with that level at every point (mean error in height, against rest as the
baseline; per path the median bias and how often the level sits at the lowest rung) — the one
figure that says whether the arithmetic holds on the text. Measure `p` first:
`python tests/appraiser_bakeoff.py --idle --n 30` (the frontier model by default).

## Recipe: inspect between bursts

What the validator already caught for you (run these on the book's db):
```sql
-- per-turn verdicts: ok / flags / confidence / escalate
SELECT turn, validation FROM turns WHERE run_id=? ORDER BY turn;
-- the turns that need your eye
SELECT turn, tags FROM turns WHERE run_id=? AND json_extract(validation,'$.escalate')=1;
-- skipped turns (LLM/parse failures — the scene moved on, recorded)
SELECT turn, payload FROM events WHERE run_id=? AND type='turn-skipped';
-- spend (the budget governor's view)
SELECT purpose, model, SUM(tokens_in), SUM(tokens_out) FROM llm_calls WHERE run_id=? GROUP BY 1,2;
```
Meaning of each signal:
- **escalate=1** — composite confidence < 0.45: the actor's self-report is suspect (wrong type for
  the dims, unperceived target, out-of-skill act). YOU are the critic until the LLM critic exists.
  Typical haiku rate on the probe: ~3/25 turns, all genuine (measured 2026-06-11).
- **ok=0** — schema-invalid tags; that turn moved NO state (conservative floor). Frequent ok=0 =
  prompt drift; compare against `prompt.py`.
- **flags but ok=1** — illegitimate dims were stripped before appraisal; state took only the
  catalog-legal part. Informational.

## Recipe: resume / crash recovery

Crash recovery IS resume — no separate mechanism (run-lifecycle.md):
```python
state = Ledger("runs/<book>.db").resume(run_id)   # {turn, snapshot}
affect = led.latest_affect(run_id, char_id)
```
`resume()` replays the log tail over the cached snapshot AND asserts it equals the from-zero fold.
**If it raises `LedgerError: RESUME DIVERGENCE`** — do NOT delete the db, do NOT force past it:
either the snapshot cache is corrupt or a projection changed under a live run. The log is intact
(append-only); investigate `ledger.py:_project` vs the cached rows. The error is the system working.
Park a run you're leaving: `led.set_status(run_id, "parked")` — appends are refused until reactivated.

## Failure playbook

| symptom | meaning | response |
|---|---|---|
| `[turn-error, degraded: ...]` + turn-skipped event | LLM call/parse failed after retries | normal at ~1/25 on haiku; re-run the turn next burst if it matters |
| escalate=1 on a turn | self-report incoherent with percepts/skills | inspect; the action/thought are usually fine — the TAGS are suspect |
| detector FLAG (probe) | state-sanity breach (saturation/oscillation/drift) | real coupling problem; check recent tag dims vs hints; `--corrupt` proves the detectors themselves |
| `CONTRACT_RUN_REFUSED` before the first beat | a file the run starts from breaks its contract | fix each named path (`lint_book` / `lint_scene` list them); nothing was written, so re-run as it was |
| `RESUME DIVERGENCE` | cache ≠ replay | never disable the CHECK; discard the CACHE — see "If a run refuses to resume" below |
| OpenRouter nulls/throttle | burst rate limit (~250 calls observed) | backoff; for judging, the fallback is an opus subagent on blinded transcript files (the 2026-06-10/11 pattern) |

## What the system does NOT do (don't look for it)

No mid-run editing of committed turns (append-only). No per-character LLM memory — ALL memory is the
vault + the ledger (if it isn't written, it didn't happen: record-contract.md). No raw stats in the
prompt (numbers → direction).

**Built, with known gaps (don't "discover" these as bugs):**
- The **critic** does not REWRITE — that half is the author's. It does now append compensating
  `correction` events (`--correct`, 2026-09-19); it never edits a committed turn.
- The **cutting room** has a built EDL (edit decision list), corrected 2026-09-19 — this bullet
  previously read that the cut was read-only with the list unbuilt. `src/engine/edl.py` records
  SCENE/SUMMARY/BREAK/NOTE entries; `scripts/cut.py
  --edl`/`--revise`/`--show-edl` writes and traces them; `scripts/narrate.py` renders from recorded
  entries. The cut DISCUSSION itself stays human (by design — cutting-room.md rejects automating the
  cut's judgment before the craft is done on real data); the EDL is the record of what the room
  decided, not a decider.
- World/character **GENERATION tooling** is unbuilt — the bible + sheets are hand-authored per
  docs/world-model.md + character-model.md (only the hinges; lazy-resolve the rest).
- `1.3` scene-assembly world-state coupling is a deferred refinement (the folded snapshot is sparse
  until move/harm/reveal events populate it).

The `runs/*.db` files are runtime artifacts, gitignored — back them up like save-files, not like code.

### If a run refuses to resume with RESUME DIVERGENCE

The message means the cached snapshot and the from-zero fold disagree. **The check is doing its job
— do not disable it.** In every case it means the CACHE is stale, and the cache is a cache: it is
safe to throw away, and the fold rebuilds it from the log.

    sqlite3 <run.db> "DELETE FROM snapshots WHERE run_id = '<run_id>';"

Then resume normally. Nothing is lost: `snapshots` is one of the two tables schema v9 deliberately
leaves mutable, because *a cache that cannot be rewritten is not a cache*.

**One known cause, now fixed forward.** Runs touched by `scripts/keeper.py` before 2026-09-01 can
hit this: the keeper appended world events at or below a parked snapshot's turn and did not
invalidate it, so `resume`'s incremental replay could not see them. `world_events.append` now
invalidates inside the same transaction as the insert. Runs created after that cannot reach this
state through the keeper; older ones need the DELETE above, once.
