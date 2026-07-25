# Engine Guide — working on the machine

For a session EXTENDING `src/engine/`. One section per module: owns / never-does / API / invariants
(rule + why + violation symptom + enforcing test). Then the cross-cutting laws. Headings and names
match the code verbatim — grep them. Precedence: code > tests > this guide > design docs for what
IS; design docs (cited per section) are normative for what SHOULD BE.

## The shape of the machine

```
records.py ──→ ledger.py          the event-sourced spine (db.py + schema.sql beneath)
state.py                          appraisal + decay (the CURRENT tier)
gate.py ──→ scene.py              perception wall + recall → the packet
consolidation.py                  tag validation + the event CATALOG
direction.py ──→ prompt.py        numbers→words → the one-pass turn messages
```
No module calls an LLM. No module reads book content from source — content arrives as arguments
(char dict, world dict). `tests/test_portability.py` proves both mechanically; it must stay green.

## db.py + schema.sql (contract: world-state-ledger.md, run-lifecycle.md, record-contract.md)

- `connect(db_path) -> sqlite3.Connection` — WAL, foreign_keys=ON (pinned by
  test_ledger:test_fk_enforcement_survives_migration), migrate-on-connect, raises RuntimeError on a
  NEWER schema (never silently downgrades). Schema lives ONLY in schema.sql.
- Single-writer assumption: two processes on one db contend on the WAL writer lock and error —
  by design (run-lifecycle.md). Don't add pooling.

## records.py

Boundary validation: a record validates completely or the write refuses — `RecordError`, no coercion.
- `Event(type, payload, actor=None, target=None, location=None, visibility="public", caused_at=None,
  effective_at=None)` — two clocks: `effective_at >= caused_at`; defaults to the committing turn.
- `RelationshipDelta(perceiver, target, axis, delta, cause_event=None)` — axis ∈ trust/affinity/
  respect/debt; delta ∈ [-1,1].
- `TurnCommit(run_id, turn, actor, thought, action, tags, affect, condition={}, events=[],
  validation={}, recall=None, manifest=None, rel_deltas=[])` — affect must carry EXACTLY the 7
  PRIMARIES, each in [0,1]. PRIMARIES is defined here and only here.

## ledger.py (contract: world-state-ledger.md + run-lifecycle.md)

API: `create_run(run_id, config)` (config requires `catalog_version`) · `load_run` · `set_status`
(active|parked|closed; parked refuses appends) · `register_character(run_id, char_id, fixed,
baseline)` · `append_turn(TurnCommit)` · `record_turn_skipped(run_id, turn, actor, reason)` ·
`log_llm_call(...)` · `fold(run_id, as_of_turn)` · `persist_snapshot` / `load_snapshot` ·
`latest_turn` · `latest_affect` · `resume(run_id)`. Errors: `LedgerError`.

Invariants:
1. **append_turn is atomic** — every row lands or none do (one transaction). Why: a half-written
   turn is corrupted ground truth forever. Symptom of breakage: partial event rows after a failed
   commit. Test: test_ledger:test_atomic_rollback.
2. **The fold is a pure function of the log; the snapshot is a CACHE.** Why: derivability is what
   makes crash recovery free and staleness harmless. NEVER write the snapshot outside
   `_project`/`persist_snapshot`; NEVER treat it as authoritative. Symptom: resume divergence.
   Tests: test_fold_deterministic_and_projects, test_resume_equals_uninterrupted_control.
3. **resume() asserts incremental == from-zero or raises.** Why: a divergent resume silently forks
   the world (no-fallbacks discipline). Test: test_divergent_resume_aborts_loudly. Known limit: a
   bug in `_project` itself produces identical wrong results on both paths — the assert catches
   cache/ordering corruption, not projection-logic bugs (g1 reviewer finding C; covered instead by
   the projection-family tests).
4. **Append-only.** There is NO update, NO delete on events. Corrections are new `correction`
   events (catalog row declared; fold support pending). Why: the log is the biography's ground truth.
5. **Projection grows empirically** — `_project` handles move/harm+terminal/reveal/seize/
   destroy-asset/betray/bond/tension; unknown types correctly do nothing to the world (their effect
   is appraisal-only). Add a branch ONLY with a catalog row + a test in test_projection_families.

## state.py (contract: state-engine.md)

API: `build_profile(char) -> {gains, decay_rates, relevance_weights, regulation, sensitivity,
model}` · `appraise(affect, tags, profile)` · `decay(affect, temperament, profile)`. Pure; ValueError
on malformed; unknown dims ignored (catalog-grows discipline).

Invariants:
1. **delta = severity × relevance × trait_sensitivity** — severity is the tag magnitude at this
   stage (wielded-threat factoring deferred to the world object model). Why: relevance is where two
   people diverge on the same event. Test: test_state (two-courageous-people case).
2. **Decay is per-primary retention** `A ← mean + (A−mean)·r` — FEAR sheds fast (r=.72), grief
   lingers (r=.90), regulation scales, floor .50. Constants are Class-B: theory-anchored,
   probe-calibrated — change them ONLY against the probe regression, never by taste.
3. **Effective state is never stored** (current × catalog multipliers is decision-engine.md, unbuilt)
   — recomputed on read; storing it would be a second source of truth.

## gate.py + scene.py (contracts: relevancy-gate.md, scene-assembly.md, knowledge-model.md)

API: `assemble(char, world, scene_slice, affect, condition) -> {stable, volatile{state, goals,
percepts, recall, edges}, manifest, recall_refs}` · `perception_scope(scene_slice, world, skills,
condition) -> [Percept]` · `extract_triggers(percepts)` · `run_gate(triggers, vault, skills, goals,
condition)`. Percept = `{ref, channel, fidelity, attributes, recognized_as?, must_surface}`.

Invariants:
1. **Never-add is structural** — assembly has no generator; every attribute derives from inputs.
   Why: a constraint an LLM must hold is a constraint it can violate; absence of a generator can't
   leak (scene-assembly.md "No renderer here"). Test: test_scene:test_whitelist (canary).
2. **The trigger wall** — triggers come from the PerceptSet ONLY; an unrecognized entity's identity
   (and its world description — identity-bearing words leak) contributes nothing. Why: you cannot
   be triggered by what you didn't perceive. Test: test_gate:test_trigger_wall.
3. **Failed check = ABSENT**, not marked. DCs: PLAIN 0.0 / IDENTITY 0.55 / SUBTLE 0.60 —
   deterministic skill-vs-DC; NO randomness, NO director-set DCs (2026-06-10 audit: the one
   invariant violation found in the design — do not reintroduce).
4. **Recall is energy-budgeted** — budget = energy×(1−allostatic_load×0.5); cost = 1−confidence;
   spend in salience order (goal-bearing first); exhausted budget = the connection doesn't fire.
   Why: stateful cognition — drained characters miss faint connections. Test: test_energy_narrowing.
5. **The stable prefix is byte-stable** for the same char (json.dumps sort_keys identical across
   turns) — it is the prompt-cache unit. Don't put volatile data in it (audit B8).
6. **Extraction vocabulary is CONTENT** — `world["lexicon"]` drives _extract_event_attributes /
   _extract_subtle_attributes / _has_subtle_cues. The stopword lists are language machinery and stay.
   Adding ANY book word to gate.py fails the portability sweep.

## consolidation.py (contract: consolidation-loop.md, record-contract.md)

API: `validate_tags(tags, percepts, skills) -> {ok, flags, confidence, escalate}` ·
`compose_confidence` · `CATALOG` (16 rows: {appraisal_map, world_map, durability_class, visibility,
capability_req}) · `THETA_CONF = 0.45` · constants `SOFT_FAIL_CAP_FACTOR = 0.65`.

Invariants:
1. **Hard vs soft**: schema violations (unknown type, bad ranges) → ok=False; containment (target
   not perceived; dims outside the type's appraisal_map at ≥0.5) and capability → soft flags.
   A well-formed-but-invalid tag RETURNS ok=False — it never raises; a rejected tag is data.
2. **composite = self_rated × 0.65^len(flags)**; escalate = composite < 0.45. Calibrated so the
   clean stub stream (0.5 default) never escalates and one default-confidence miss does.
3. **The CATALOG is the contract AND the extension surface** — per-book types extend the dict;
   every type the ledger folds or the actor emits MUST have a row (test_consolidation checks
   completeness against ledger._project).
4. The LLM critic does NOT exist — escalate is recorded for the human/the future critic. Don't
   add a model call here (the engine never calls LLMs).

## direction.py + prompt.py (contracts: design.md compute/generate split, scene-assembly.md)

API: `direct_affect(affect, temperament)` · `direct_condition(condition)` · `direct_edge(edge)` ·
`sureness(confidence)` — all return digit-free, second-person strings. `build_turn_messages(packet,
event_text, temperament) -> [system, user]`; `ACTOR_TAG_TYPES` and the dimension list are DERIVED
from CATALOG and state's dim map — never hardcode a type list in a prompt.

Invariants:
1. **No numeral ever leaves direction.py** (the backstage guardrail: numbers in the DB, directions
   in the prompt). Test: test_direction:test_no_digits_ever (a sweep, keep it exhaustive).
2. **Deviation vs temperament mean** gets a marker; an anxious BASELINE must not read as a fresh
   spike. Test: test_deviation_markers.
3. **The never-invent line is scoped to WORLD facts; the interior is licensed** — clamping
   invention must not clamp interiority (blind-judge finding, 2026-06-11). Don't "tighten" it back.
4. Direction phrasing is neutral register — narration owns voice; a flowery direction colors the
   actor twice.

## Cross-cutting laws

- **Machinery/content seam**: enforced by test_portability's token sweep over `src/engine/*` —
  including comments. Extend the sweep's token list when a new book fixture appears.
- **fail-loud vs degrade-not-crash** (looks contradictory; isn't): MODULES raise on malformed input
  (ValueError/RecordError/LedgerError, immediately); the RUN LOOP catches per-turn, counts, records
  `turn-skipped`, continues. The boundary is the caller's try/except (see run_probe). Never add a
  silent fallback inside a module; never let a single turn kill a run.
- **500 lines/file · stdlib only · %-formatting · terse docstrings citing doc§.**
- **Every Class-B constant** carries provenance (theory + "probe-calibrated start") and changes only
  against the probe regression. The detector thresholds (SAT .15 / OSC .18 / DRIFT .55), roundtrip
  (ERR .30 / SLOPE .004), THETA .45, cap .65, DCs, decay table, direction bands are all calibrated
  against planted controls — the corrupt run and compound-control must keep FAILING after any change.
- **The strangler discipline**: the probe (`tests/coherence_probe.py`) is the permanent integration
  regression. Module change → run the suite block in CLAUDE.md → `--stub` PASS and `--corrupt` FAIL
  are both required (a detector that can't fail is hollow).
- **Depth gates**: src/ changes need a gate in the Claude Flow workspace `.depth/` (one gate at a
  time; verify with check_gate.py; archive before the next). tests/, docs/, JSON are exempt.
- **Built since (2026-06-13 production drive)** — don't list these as unbuilt: the LLM **critic**
  (continuity+voice, detect-only — `scripts/critic.py`); **regenerate-on-reject** (`direct.faithful_turn`);
  the **multi-character scheduler** WITH ledger persistence + scene boundaries (`scripts/scene.py`);
  the **arc durable-diffs applier** (`arc.apply` wired in run_turn/run_scene; resume replays diffs);
  the **narrator** (`scripts/narrate.py`); the cutting-room **dailies views** (`scripts/cut.py`);
  the **book linter** (`scripts/lint_book.py`).
- **Still deliberately unbuilt** (don't "discover" these as bugs): the critic's **compensating-event
  writer** + faithfulness **semantic** critic; `dialogue_acts`/`stance_snapshots` writers; the cutting
  room **EDL** + EDL-driven render + cut audits (the cut discussion is human — cutting-room.md);
  **effective-lever catalog**; **world/character generation tooling**; Kuzu vault graph (vault is flat
  by design; gate cost is single-hop 1−confidence behind the same interface).
