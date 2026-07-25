-- schema.sql — v1 contract for the engine spine (world-state-ledger.md · record-contract.md · run-lifecycle.md)
-- The schema IS the primary artifact: every table here is named by a design doc; nothing is speculative.
-- Versioning: db.py applies this when PRAGMA user_version < SCHEMA_VERSION, then stamps it.

-- ---- the run (run-lifecycle.md: run config pins models, prompt versions, catalog version) ----
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'parked', 'closed')),
    config      TEXT NOT NULL                  -- JSON: {catalog_version, models, prompt_versions, ...}
);

-- ---- the event log: append-only, two clocks (world-state-ledger.md) ----
CREATE TABLE IF NOT EXISTS events (
    event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT    NOT NULL REFERENCES runs(run_id),
    turn         INTEGER NOT NULL,              -- the turn whose commit appended it
    caused_at    INTEGER NOT NULL,              -- tick the event entered the log
    effective_at INTEGER NOT NULL,              -- tick it folds (>= caused_at; future-dated consequences)
    type         TEXT    NOT NULL,              -- event-catalog name (record-contract.md)
    actor        TEXT,                          -- who (NULL for world events)
    target       TEXT,                          -- acted-upon, when the type has one
    location     TEXT,
    visibility   TEXT    NOT NULL DEFAULT 'public' CHECK (visibility IN ('public', 'private-to-actor')),
    payload      TEXT    NOT NULL,              -- JSON: what/consequence/dimensions/durability...
    CHECK (effective_at >= caused_at)
);
CREATE INDEX IF NOT EXISTS idx_events_fold ON events(run_id, effective_at, event_id);

-- ---- the turn-commit record (run-lifecycle.md: the atomic unit) ----
CREATE TABLE IF NOT EXISTS turns (
    run_id       TEXT    NOT NULL REFERENCES runs(run_id),
    turn         INTEGER NOT NULL,
    actor        TEXT    NOT NULL,
    thought      TEXT    NOT NULL DEFAULT '',
    action       TEXT    NOT NULL DEFAULT '',
    tags         TEXT    NOT NULL DEFAULT '{}', -- the actor's same-pass consolidation self-report (JSON)
    validation   TEXT    NOT NULL DEFAULT '{}', -- mechanical validation result (gate 4 fills this)
    committed_at TEXT    NOT NULL,
    PRIMARY KEY (run_id, turn, actor)
);

-- ---- characters: FIXED + BASELINE in the DB; CURRENT is per-turn rows (state-engine.md three tiers) ----
CREATE TABLE IF NOT EXISTS characters (
    run_id   TEXT NOT NULL REFERENCES runs(run_id),
    char_id  TEXT NOT NULL,
    fixed    TEXT NOT NULL,                     -- JSON (immutable)
    baseline TEXT NOT NULL,                     -- JSON (moves only via arc_diffs)
    PRIMARY KEY (run_id, char_id)
);

CREATE TABLE IF NOT EXISTS current_state (      -- per-turn CURRENT rows; effective is derived, never stored
    run_id    TEXT    NOT NULL,
    char_id   TEXT    NOT NULL,
    turn      INTEGER NOT NULL,
    affect    TEXT    NOT NULL,                 -- JSON {SEEKING..PLAY: 0..1}
    condition TEXT    NOT NULL DEFAULT '{}',    -- JSON energy/allostatic
    PRIMARY KEY (run_id, char_id, turn)
);

CREATE TABLE IF NOT EXISTS arc_diffs (          -- arc-engine durable baseline diffs (sparse)
    run_id  TEXT    NOT NULL,
    char_id TEXT    NOT NULL,
    turn    INTEGER NOT NULL,
    diff    TEXT    NOT NULL,                   -- JSON sparse diff against baseline
    PRIMARY KEY (run_id, char_id, turn)
);

CREATE TABLE IF NOT EXISTS acquisitions (       -- the vault grows: lived/told/deduced beliefs (knowledge-model.md acquisition)
    acquisition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id  TEXT    NOT NULL,
    char_id TEXT    NOT NULL,
    turn    INTEGER NOT NULL,
    belief  TEXT    NOT NULL                    -- JSON {claim, confidence, provenance, believed_value, links}
);

-- ---- folded snapshot cache (derivable; the fold is the only writer) ----
CREATE TABLE IF NOT EXISTS snapshots (
    run_id     TEXT    NOT NULL,
    as_of_turn INTEGER NOT NULL,
    kind       TEXT    NOT NULL CHECK (kind IN ('agents','holdings','information','relationships','tensions','clock')),
    key        TEXT    NOT NULL,
    value      TEXT    NOT NULL,                -- JSON
    PRIMARY KEY (run_id, as_of_turn, kind, key)
);

-- ---- record-contract required writes (record-contract.md: consumer queries ARE producer writes) ----
CREATE TABLE IF NOT EXISTS recall_events (      -- the gate's injected-recall set, per turn
    run_id      TEXT    NOT NULL,
    turn        INTEGER NOT NULL,
    actor       TEXT    NOT NULL,
    belief_refs TEXT    NOT NULL,               -- JSON array
    PRIMARY KEY (run_id, turn, actor)
);

CREATE TABLE IF NOT EXISTS decision_manifests ( -- scene-assembly packet contents, as refs
    run_id   TEXT    NOT NULL,
    turn     INTEGER NOT NULL,
    actor    TEXT    NOT NULL,
    manifest TEXT    NOT NULL,                  -- JSON {state_fields_read, beliefs_injected, percepts, edges}
    PRIMARY KEY (run_id, turn, actor)
);

CREATE TABLE IF NOT EXISTS relationship_deltas (-- every appraisal that moves a relationship edge
    delta_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL,
    turn        INTEGER NOT NULL,
    perceiver   TEXT    NOT NULL,
    target      TEXT    NOT NULL,
    axis        TEXT    NOT NULL,               -- trust | affinity | respect | debt
    delta       REAL    NOT NULL,
    cause_event INTEGER REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS dialogue_acts (      -- multi-character family; declared per contract, writer lands post-spine
    run_id TEXT NOT NULL,
    turn   INTEGER NOT NULL,
    actor  TEXT NOT NULL,
    act    TEXT NOT NULL,                       -- assert|rebut|concede|question|support|escalate|deflect
    target TEXT,
    PRIMARY KEY (run_id, turn, actor)
);

CREATE TABLE IF NOT EXISTS stance_snapshots (   -- per debate step; writer lands post-spine
    run_id     TEXT NOT NULL,
    step       INTEGER NOT NULL,
    character  TEXT NOT NULL,
    position   TEXT NOT NULL,
    conviction REAL NOT NULL,
    PRIMARY KEY (run_id, step, character)
);

-- ---- scene boundaries: which committed turns form one scene (book-assembly: cut + narrate per scene) ----
CREATE TABLE IF NOT EXISTS scenes (
    run_id     TEXT    NOT NULL REFERENCES runs(run_id),
    scene_no   INTEGER NOT NULL,
    label      TEXT    NOT NULL DEFAULT '',
    pov        TEXT,                              -- the POV the narrator renders this scene from (director's choice)
    start_turn INTEGER NOT NULL,
    end_turn   INTEGER NOT NULL,                  -- inclusive: the last turn committed in the scene
    PRIMARY KEY (run_id, scene_no)
);

-- ---- the token ledger (run-lifecycle.md budget governor: spend is a queryable view) ----
CREATE TABLE IF NOT EXISTS llm_calls (
    call_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id     TEXT NOT NULL,
    turn       INTEGER,
    purpose    TEXT NOT NULL,                   -- decide | consolidate | frame | narrate | critic
    model      TEXT NOT NULL,
    tokens_in  INTEGER,
    tokens_out INTEGER,
    scene      TEXT
);

-- ---- scheduler durable state (run-lifecycle.md inventory item 4) ----
CREATE TABLE IF NOT EXISTS scheduler_state (
    run_id TEXT NOT NULL,
    key    TEXT NOT NULL,
    value  TEXT NOT NULL,                       -- JSON
    PRIMARY KEY (run_id, key)
);
