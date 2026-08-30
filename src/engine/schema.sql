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
    -- 'first'  = what the perceiver makes of the target
    -- 'second' = what the perceiver believes the TARGET makes of THEM (bonds.reflect;
    --            emotion-basis.md's rich layer). Without this the second order rendered and then
    --            evaporated at scene end, because the delta row had nowhere to put it.
    ord         TEXT    NOT NULL DEFAULT 'first',
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

-- ---- the pinned bible (orchestrator-design.md 7.1: the typed projection) ----
-- A run must be able to say WHAT IT RAN AGAINST. Before this, the bible was
-- re-parsed from markdown per invocation and never recorded, so editing a
-- character sheet mid-book silently changed what earlier turns were computed
-- from -- and resume could not see it (it verifies the fold of the log, not the
-- inputs the log came from). Keyed by fingerprint, not run_id: the bible is
-- usually unchanged across many runs, so this pins AND deduplicates.
CREATE TABLE IF NOT EXISTS bibles (
    fingerprint TEXT PRIMARY KEY,          -- sha256 over the canonical (world, characters)
    built_at    TEXT NOT NULL,
    world       TEXT NOT NULL,             -- JSON: the world engine block as loaded
    characters  TEXT NOT NULL              -- JSON: {char_id: sheet}
);

-- Entity existence, exact. This is what makes an `entity:` citation resolvable
-- and a "does X exist" gate computable, rather than a similarity guess.
CREATE TABLE IF NOT EXISTS bible_entities (
    fingerprint TEXT NOT NULL REFERENCES bibles(fingerprint),
    kind        TEXT NOT NULL CHECK (kind IN ('character','person','location')),
    entity_id   TEXT NOT NULL,
    what        TEXT NOT NULL DEFAULT '',  -- the authored identity line, for citation detail
    PRIMARY KEY (fingerprint, kind, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_bible_entities_id ON bible_entities(fingerprint, entity_id);

-- ---- laws: what the world permits, forbids, and makes impossible ----------
-- THE LOAD-BEARING DISTINCTION (orchestrator-design.md 7.1): a gate that denied
-- every ILLEGAL act would make crime unwritable. The world says no in two
-- different ways and they resolve differently:
--   IMPOSSIBLE  physical/supernatural -- it cannot occur   -> DENY the circumstance
--   FORBIDS     legal/custom -- it may not, but it can     -> ALLOW, attach `teeth`
--   REQUIRES    an obligation                              -> allow; omission is a violation
--   PERMITS     an explicit allowance overriding a forbid   -> allow
-- `epistemic` is mandatory (universal-law.md's known-vs-believed check): a law
-- people merely BELIEVE binds behaviour, never possibility. A gate must never
-- deny a circumstance because a character holds a false belief.
CREATE TABLE IF NOT EXISTS bible_laws (
    fingerprint    TEXT NOT NULL REFERENCES bibles(fingerprint),
    law_id         TEXT NOT NULL,
    domain         TEXT NOT NULL CHECK (domain IN (
                       -- step 1, universal-law.md A-E
                       'physical','supernatural','persons','fate','cosmology',
                       -- step 4, present-systems.md
                       'legal','custom','economic')),
    modality       TEXT NOT NULL CHECK (modality IN ('IMPOSSIBLE','FORBIDS','REQUIRES','PERMITS')),
    statement      TEXT NOT NULL,              -- the human-readable rule; what a denial quotes
    act            TEXT NOT NULL DEFAULT '',   -- '' = bears on any act
    actor_class    TEXT NOT NULL DEFAULT '',
    target_class   TEXT NOT NULL DEFAULT '',
    location_scope TEXT NOT NULL DEFAULT '',   -- '' = everywhere
    time_from      INTEGER,
    time_to        INTEGER,
    teeth          TEXT NOT NULL DEFAULT '',   -- the consequence a FORBIDS violation attaches
    epistemic      TEXT NOT NULL DEFAULT 'known-true' CHECK (epistemic IN (
                       'known-true','known-false','contested-unknowable')),
    source_note    TEXT NOT NULL DEFAULT '',   -- provenance: what a citation points back to
    excepts        TEXT NOT NULL DEFAULT '',   -- PERMITS only: space-joined law ids this permit
                                               -- disarms; '' = documented general allowance
    PRIMARY KEY (fingerprint, law_id)
);
CREATE INDEX IF NOT EXISTS idx_bible_laws_act ON bible_laws(fingerprint, act);

-- =====================================================================================
-- APPEND-ONLY, ENFORCED BY THE DATABASE (CLAUDE.md hard rule 2, schema v9)
--
-- "The log is append-only. No update, no delete on events — corrections are new
--  `correction` events. The snapshot is a derivable CACHE, never the source of truth."
--
-- Until v9 that rule was enforced by nothing but the habit of ledger.py, which happens not
-- to emit UPDATE or DELETE. Anything else holding a connection — a stranger's script, a
-- foreign driver on rails, an sqlite3 shell, a future writer added in good faith — could
-- rewrite a committed turn, leaving a folded snapshot that no longer matches the log it
-- claims to derive from. A rule stated absolutely and enforced by habit is a rule that has
-- simply never been tested.
--
-- Only the LOG is frozen. The caches (snapshots, current_state), the run's own status, the
-- bible tables and the scene index stay mutable — a cache that cannot be rewritten is not a
-- cache, and hard rule 2 names the log, not the fold.
-- =====================================================================================
CREATE TRIGGER IF NOT EXISTS events_no_update
BEFORE UPDATE ON events BEGIN
    SELECT RAISE(ABORT, 'events is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS events_no_delete
BEFORE DELETE ON events BEGIN
    SELECT RAISE(ABORT, 'events is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS turns_no_update
BEFORE UPDATE ON turns BEGIN
    SELECT RAISE(ABORT, 'turns is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS turns_no_delete
BEFORE DELETE ON turns BEGIN
    SELECT RAISE(ABORT, 'turns is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS recall_events_no_update
BEFORE UPDATE ON recall_events BEGIN
    SELECT RAISE(ABORT, 'recall_events is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS recall_events_no_delete
BEFORE DELETE ON recall_events BEGIN
    SELECT RAISE(ABORT, 'recall_events is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS acquisitions_no_update
BEFORE UPDATE ON acquisitions BEGIN
    SELECT RAISE(ABORT, 'acquisitions is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS acquisitions_no_delete
BEFORE DELETE ON acquisitions BEGIN
    SELECT RAISE(ABORT, 'acquisitions is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS arc_diffs_no_update
BEFORE UPDATE ON arc_diffs BEGIN
    SELECT RAISE(ABORT, 'arc_diffs is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS arc_diffs_no_delete
BEFORE DELETE ON arc_diffs BEGIN
    SELECT RAISE(ABORT, 'arc_diffs is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS relationship_deltas_no_update
BEFORE UPDATE ON relationship_deltas BEGIN
    SELECT RAISE(ABORT, 'relationship_deltas is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS relationship_deltas_no_delete
BEFORE DELETE ON relationship_deltas BEGIN
    SELECT RAISE(ABORT, 'relationship_deltas is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;
