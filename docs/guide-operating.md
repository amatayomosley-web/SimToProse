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

Catch authoring errors before they crash a run (or silently degrade it):
```bash
python scripts/lint_book.py --vault "<book>"             # a real book
python scripts/lint_book.py --book ashford --char maren  # a fixture
```
ERRORS would break a run (missing `fixed`/`baseline`/`current`, a `baseline.temperament` or
`current.affect` missing any of the 8 primaries, an affect value out of [0,1], `current.condition`
not a dict) — exit 1. WARNINGS flag thin or silently-degrading authoring (no lexicon; a relationship
key that is not a `world.people` id, so its edge will never surface; a vault belief missing a claim
or provenance). Report-only — fix the JSON, the linter never edits.

## Recipe: run a burst (the production rhythm)

**The director's chair** ("we are the directors", 2026-06-11) is the operating tool:
```bash
python scripts/direct.py --vault "<path to the book folder in your vault>" --char pell   # a REAL book
python scripts/direct.py --book ashford --char maren                                      # engine test fixture
# --stub for deterministic | type a circumstance per turn | status | quit (parks; --resume <run_id>)
```
A real book's chronicle db lands in the BOOK's `runs/`, beside its notes — the machine repo
holds no book state.
You place circumstance ONLY — the tool has no affordance for writing the character's state or
words (steering = circumstance, never the character's hand; the discipline is structural).

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
python scripts/scene.py --vault "<book>" --scene <scene.json>                     # a director-authored scene
python scripts/scene.py --vault "<book>" --scene <scene.json> --resume <run_id>   # a LATER scene, same chronicle
python scripts/scene.py --vault "<book>" --stub                                   # default BP13 fixture, no API
```
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
```
Returns `{continuity:[...], voice:[...]}` — statements that contradict the bible or an earlier line,
and indistinguishable voices. DETECT-only today (the rewrite/compensating-event half is unbuilt).

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

## The hybrid — who runs what (decided 2026-06-13)

Character TURNS run on the cheap LOCAL model (Ollama `gemma4` / `haiku`) — high-volume acting.
The CRITIC + NARRATOR run on the STRONG model, Claude-in-the-loop: `--prompt-only` builds the
deterministic prompt, Claude (in a session) produces the review/prose. Key-free — the sim is
local-only and the OpenRouter key is intentionally absent; the OpenRouter dispatch in critic/narrate
is a key-gated FALLBACK, off by default (re-adding the key is a the author call).

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
| `RESUME DIVERGENCE` | cache ≠ replay | never disable the CHECK; discard the CACHE — see "If a run refuses to resume" below |
| OpenRouter nulls/throttle | burst rate limit (~250 calls observed) | backoff; for judging, the fallback is an opus subagent on blinded transcript files (the 2026-06-10/11 pattern) |

## What the system does NOT do (don't look for it)

No mid-run editing of committed turns (append-only). No per-character LLM memory — ALL memory is the
vault + the ledger (if it isn't written, it didn't happen: record-contract.md). No raw stats in the
prompt (numbers → direction).

**Built, with known gaps (don't "discover" these as bugs):**
- The **critic** is DETECT-only — no rewrite / compensating-event writer yet.
- The **cutting room** is VIEWS-only — no EDL (edit decision list) record, no EDL-driven render, no
  cut audits yet. The cut DISCUSSION and its decision log are human (by design — cutting-room.md
  rejects automating the cut before the craft is done on real data).
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
