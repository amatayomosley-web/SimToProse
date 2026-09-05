-- schema.sql — v1 contract for the engine spine (world-state-ledger.md · record-contract.md · run-lifecycle.md)
-- The schema IS the primary artifact: every table here is named by a design doc; nothing is speculative.
-- Versioning: db.py applies this when PRAGMA user_version < SCHEMA_VERSION, then stamps it.
--
-- AND THE FIRST SWEEP MISSED SEVEN, because it classified columns against a list of names it
-- had thought of rather than requiring every column to be guarded or explained. `character`
-- and `primary_` are identities inside key constraints and were not in it. The test is now
-- protected-or-explained: a new column FAILS until someone either guards it or writes down
-- why blank is legal there.
--
-- `NOT NULL` DOES NOT MEAN "PRESENT". SQLite satisfies it with the empty string, so every identity
-- and discriminator column here accepted `''` — measured 2026-09-02: a run with an empty run_id, a
-- character with an empty char_id, an event with an empty type, a bible with an empty fingerprint,
-- all inserted clean. An empty identity joins to everything or to nothing, and an empty type folds
-- to nothing while looking like a recorded event.
--
-- The Python layer refuses these at its own boundary; this is the second wall, for the same reason
-- schema v9 grew append-only TRIGGERS — a rule enforced only by the habit of one writer is a rule
-- that has never been tested against a stranger's script, an sqlite3 shell, or a future writer
-- added in good faith.
--
-- SCOPED DELIBERATELY to columns where empty is a LIE. The 17 columns carrying `DEFAULT ''` are
-- deliberately optional (`label`, `thought`, `action`, `rationale`, `what`, `source`…) and must NOT
-- get this check: for them, empty is a legitimate authored value meaning "none given".

-- ---- the run (run-lifecycle.md: run config pins models, prompt versions, catalog version) ----
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY CHECK (run_id <> ''),
    created_at  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'parked', 'closed')),
    config      TEXT NOT NULL                  -- JSON: {catalog_version, models, prompt_versions, ...}
);

-- ---- the event log: append-only, two clocks (world-state-ledger.md) ----
CREATE TABLE IF NOT EXISTS events (
    event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) CHECK (run_id <> ''),
    turn         INTEGER NOT NULL,              -- the turn whose commit appended it
    caused_at    INTEGER NOT NULL,              -- tick the event entered the log
    effective_at INTEGER NOT NULL,              -- tick it folds (>= caused_at; future-dated consequences)
    type TEXT NOT NULL CHECK (type <> ''),  -- event-catalog name (record-contract.md)
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
    run_id TEXT NOT NULL REFERENCES runs(run_id) CHECK (run_id <> ''),
    turn         INTEGER NOT NULL,
    actor TEXT NOT NULL CHECK (actor <> ''),
    thought      TEXT    NOT NULL DEFAULT '',
    action       TEXT    NOT NULL DEFAULT '',
    tags         TEXT    NOT NULL DEFAULT '{}', -- the actor's same-pass consolidation self-report (JSON)
    validation   TEXT    NOT NULL DEFAULT '{}', -- mechanical validation result (gate 4 fills this)
    committed_at TEXT    NOT NULL,
    PRIMARY KEY (run_id, turn, actor)
);

-- ---- characters: FIXED + BASELINE in the DB; CURRENT is per-turn rows (state-engine.md three tiers) ----
CREATE TABLE IF NOT EXISTS characters (
    run_id TEXT NOT NULL REFERENCES runs(run_id) CHECK (run_id <> ''),
    char_id TEXT NOT NULL CHECK (char_id <> ''),
    fixed    TEXT NOT NULL,                     -- JSON (immutable)
    baseline TEXT NOT NULL,                     -- JSON (moves only via arc_diffs)
    PRIMARY KEY (run_id, char_id)
);

CREATE TABLE IF NOT EXISTS current_state (      -- per-turn CURRENT rows; effective is derived, never stored
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    char_id TEXT NOT NULL CHECK (char_id <> ''),
    turn      INTEGER NOT NULL,
    affect    TEXT    NOT NULL,                 -- JSON {SEEKING..PLAY: 0..1}
    condition TEXT    NOT NULL DEFAULT '{}',    -- JSON energy/allostatic
    PRIMARY KEY (run_id, char_id, turn)
);

CREATE TABLE IF NOT EXISTS arc_diffs (          -- arc-engine durable baseline diffs (sparse)
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    char_id TEXT NOT NULL CHECK (char_id <> ''),
    turn    INTEGER NOT NULL,
    diff    TEXT    NOT NULL,                   -- JSON sparse diff against baseline
    PRIMARY KEY (run_id, char_id, turn)
);

CREATE TABLE IF NOT EXISTS acquisitions (       -- the vault grows: lived/told/deduced beliefs (knowledge-model.md acquisition)
    acquisition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    char_id TEXT NOT NULL CHECK (char_id <> ''),
    turn    INTEGER NOT NULL,
    belief  TEXT    NOT NULL                    -- JSON {claim, confidence, provenance, believed_value, links}
);

-- ---- folded snapshot cache (derivable; the fold is the only writer) ----
CREATE TABLE IF NOT EXISTS snapshots (
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    as_of_turn INTEGER NOT NULL,
    kind       TEXT    NOT NULL CHECK (kind IN ('agents','holdings','information','relationships','tensions','clock')),
    key TEXT NOT NULL CHECK (key <> ''),
    value      TEXT    NOT NULL,                -- JSON
    PRIMARY KEY (run_id, as_of_turn, kind, key)
);

-- ---- record-contract required writes (record-contract.md: consumer queries ARE producer writes) ----
CREATE TABLE IF NOT EXISTS recall_events (      -- the gate's injected-recall set, per turn
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    turn        INTEGER NOT NULL,
    actor TEXT NOT NULL CHECK (actor <> ''),
    belief_refs TEXT    NOT NULL,               -- JSON array
    PRIMARY KEY (run_id, turn, actor)
);

CREATE TABLE IF NOT EXISTS decision_manifests ( -- scene-assembly packet contents, as refs
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    turn     INTEGER NOT NULL,
    actor TEXT NOT NULL CHECK (actor <> ''),
    manifest TEXT    NOT NULL,                  -- JSON {state_fields_read, beliefs_injected, percepts, edges}
    PRIMARY KEY (run_id, turn, actor)
);

CREATE TABLE IF NOT EXISTS relationship_deltas (-- every appraisal that moves a relationship edge
    delta_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    turn        INTEGER NOT NULL,
    perceiver TEXT NOT NULL CHECK (perceiver <> ''),
    target TEXT NOT NULL CHECK (target <> ''),
    axis TEXT NOT NULL CHECK (axis <> ''),  -- trust | affinity | respect | debt
    delta       REAL    NOT NULL,
    -- 'first'  = what the perceiver makes of the target
    -- 'second' = what the perceiver believes the TARGET makes of THEM (bonds.reflect;
    --            emotion-basis.md's rich layer). Without this the second order rendered and then
    --            evaporated at scene end, because the delta row had nowhere to put it.
    ord         TEXT    NOT NULL DEFAULT 'first' CHECK (ord <> ''),
    cause_event INTEGER REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS dialogue_acts (      -- multi-character family; declared per contract, writer lands post-spine
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    turn   INTEGER NOT NULL,
    actor TEXT NOT NULL CHECK (actor <> ''),
    act    TEXT NOT NULL CHECK (act <> ''),                       -- assert|rebut|concede|question|support|escalate|deflect
    target TEXT,
    PRIMARY KEY (run_id, turn, actor)
);

CREATE TABLE IF NOT EXISTS stance_snapshots (   -- per debate step; writer lands post-spine
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    step       INTEGER NOT NULL,
    character  TEXT NOT NULL CHECK (character <> ''),
    position   TEXT NOT NULL,
    conviction REAL NOT NULL,
    PRIMARY KEY (run_id, step, character)
);

-- ---- scene boundaries: which committed turns form one scene (book-assembly: cut + narrate per scene) ----
CREATE TABLE IF NOT EXISTS scenes (
    run_id TEXT NOT NULL REFERENCES runs(run_id) CHECK (run_id <> ''),
    scene_no   INTEGER NOT NULL,
    label      TEXT    NOT NULL DEFAULT '',
    pov        TEXT,                              -- the POV the narrator renders this scene from (director's choice)
    -- Mixed-voice books are per-scene rows, the same authority that already picks `pov`: Bleak House
    -- alternates first and third, Gone Girl alternates two first-person narrators, As I Lay Dying
    -- gives fifteen narrators a chapter each. `voice` is a rendering instruction and touches nothing;
    -- `knowledge` decides what the narrator is SHOWN (narrate.pov_split) and is the one with teeth.
    -- Defaults are what every pre-v13 row actually was, because they were the only renderable values.
    -- THE CFG THIS SCENE RAN AGAINST, pinned the way a run pins its bible (bible.py). Without it
    -- a resumed run replays every turn and cannot say what location, cast, props or opening tags
    -- produced them: edit the cfg between runs and the log claims a provenance it no longer has,
    -- with nothing to detect it. Empty = a scene recorded before pinning existed, which reads as
    -- "unknown", never as "unchanged".
    cfg_fingerprint TEXT NOT NULL DEFAULT '',
    voice      TEXT    NOT NULL DEFAULT 'close-third'
               CHECK (voice IN ('close-third', 'first', 'distant-third', 'second')),
    knowledge  TEXT    NOT NULL DEFAULT 'pov' CHECK (knowledge IN ('pov', 'omniscient')),
    start_turn INTEGER NOT NULL,
    end_turn   INTEGER NOT NULL,                  -- inclusive: the last turn committed in the scene
    PRIMARY KEY (run_id, scene_no)
);

-- The cfg bodies, content-addressed. Fingerprinting pins and DEDUPLICATES in one move (the same
-- argument bibles makes): two scenes run from one cfg share a row and are provably the same inputs.
CREATE TABLE IF NOT EXISTS scene_cfgs (
    fingerprint TEXT PRIMARY KEY CHECK (fingerprint <> ''),          -- sha256 over the canonical cfg payload, not the file bytes
    recorded_at TEXT NOT NULL,
    body        TEXT NOT NULL              -- JSON: the cfg as the run loaded it
);

-- ---- what was SAID about the world, so lore accretes (keeper-of-truth.md) ----
-- `bible_entities.what` is ONE authored line, written when the bible is pinned and never growing.
-- So a character could describe their home town for ten chapters and the world learned nothing.
-- These three tables are where it accumulates.
--
-- TIER IS NOT A COLUMN HERE except as PROVENANCE. keeper-of-truth.md derives tier by folding
-- resolutions, and hard rule 2 makes that mandatory rather than stylistic: a tier that flips
-- superposed -> fiction is an UPDATE, which the triggers refuse. `utterances.tier` records how the
-- claim ENTERED (authored from the bible, or spoken); everything after is a resolution row.
CREATE TABLE IF NOT EXISTS utterances (
    utterance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) CHECK (run_id <> ''),
    turn         INTEGER NOT NULL,
    speaker TEXT NOT NULL CHECK (speaker <> ''),
    said         TEXT    NOT NULL,          -- VERBATIM. The extract is an index into this, never a
                                            -- substitute: "when I was a girl" may be the whole point.
    tier         TEXT    NOT NULL DEFAULT 'superposed' CHECK (tier <> '')
);

-- The facts one utterance asserts — one row each, because an utterance carries as many as it
-- carries. Normalised at write time with `claims.normalise`, so the index agrees with the
-- comparator instead of racing it. This is the relational shape of `extracts`, not a second copy.
CREATE TABLE IF NOT EXISTS claim_extracts (
    utterance_id INTEGER NOT NULL REFERENCES utterances(utterance_id),
    ord_no       INTEGER NOT NULL,
    subject TEXT NOT NULL CHECK (subject <> ''),
    predicate TEXT NOT NULL CHECK (predicate <> ''),
    object       TEXT    NOT NULL DEFAULT '',
    PRIMARY KEY (utterance_id, ord_no)
);
CREATE INDEX IF NOT EXISTS idx_claim_subject ON claim_extracts(subject);

-- The keeper's verdicts, folded in order. Append-only: a keeper changes its mind by appending.
CREATE TABLE IF NOT EXISTS claim_resolutions (
    resolution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) CHECK (run_id <> ''),
    utterance_id  INTEGER NOT NULL REFERENCES utterances(utterance_id),
    at_turn       INTEGER NOT NULL,
    verdict       TEXT    NOT NULL CHECK (verdict IN ('authored','established','superposed','fiction')),
    rationale     TEXT    NOT NULL DEFAULT ''
);

-- claim_extracts is the INDEX that drives contradiction detection and read_api.place(). It had no
-- triggers, so the derived half of an append-only pair was freely rewritable: an extract could be
-- edited to make two utterances stop contradicting each other, with the verbatim text untouched.
CREATE TRIGGER IF NOT EXISTS claim_extracts_no_update BEFORE UPDATE ON claim_extracts
BEGIN SELECT RAISE(ABORT, 'claim_extracts is append-only (CLAUDE.md hard rule 2): it is derived from an utterance that cannot change'); END;
CREATE TRIGGER IF NOT EXISTS claim_extracts_no_delete BEFORE DELETE ON claim_extracts
BEGIN SELECT RAISE(ABORT, 'claim_extracts is append-only (CLAUDE.md hard rule 2): resolve the utterance to fiction instead'); END;

-- The pinned cfg BODY is evidence about what a scene ran against. A mutable body under a fixed
-- fingerprint could be rewritten to lie about the pin, which defeats the point of pinning.
CREATE TRIGGER IF NOT EXISTS scene_cfgs_no_update BEFORE UPDATE ON scene_cfgs
BEGIN SELECT RAISE(ABORT, 'scene_cfgs is append-only (CLAUDE.md hard rule 2): a cfg body must not change under its fingerprint'); END;
CREATE TRIGGER IF NOT EXISTS scene_cfgs_no_delete BEFORE DELETE ON scene_cfgs
BEGIN SELECT RAISE(ABORT, 'scene_cfgs is append-only (CLAUDE.md hard rule 2): a scene row still points at this pin'); END;

CREATE TRIGGER IF NOT EXISTS utterances_no_update BEFORE UPDATE ON utterances
BEGIN SELECT RAISE(ABORT, 'utterances is append-only (CLAUDE.md hard rule 2): tier is DERIVED by folding claim_resolutions, never rewritten'); END;
CREATE TRIGGER IF NOT EXISTS utterances_no_delete BEFORE DELETE ON utterances
BEGIN SELECT RAISE(ABORT, 'utterances is append-only (CLAUDE.md hard rule 2): a declined claim is resolved to fiction, never deleted'); END;
CREATE TRIGGER IF NOT EXISTS claim_resolutions_no_update BEFORE UPDATE ON claim_resolutions
BEGIN SELECT RAISE(ABORT, 'claim_resolutions is append-only (CLAUDE.md hard rule 2): append a new verdict'); END;
CREATE TRIGGER IF NOT EXISTS claim_resolutions_no_delete BEFORE DELETE ON claim_resolutions
BEGIN SELECT RAISE(ABORT, 'claim_resolutions is append-only (CLAUDE.md hard rule 2): append a new verdict'); END;

-- ---- the edit decision list (cutting-room.md: "decisions append to the EDL; narration renders
-- from it; audits verify the result. Faithfulness is never a vibe.") ----
-- The RECORD half of the cut. The discussion stays human and the automated selection pipeline stays
-- rejected; what lives here is what the room decided, typed so the prose can be traced back to it.
-- `ord_no` is manuscript position chosen by the room, NOT scene order — reordering is the point.
CREATE TABLE IF NOT EXISTS edl (
    run_id TEXT NOT NULL REFERENCES runs(run_id) CHECK (run_id <> ''),
    -- A cut is REVISED by appending a whole new generation, never by rewriting the old one. The
    -- triggers below say "revise by appending" and until schema v17 there was nowhere to append TO:
    -- PRIMARY KEY (run_id, ord_no) meant a second pass collided, and appending at fresh ord_nos
    -- made the renderer emit the UNION of both cuts. A run got exactly one cut, forever.
    generation INTEGER NOT NULL DEFAULT 0,
    ord_no   INTEGER NOT NULL,
    kind     TEXT    NOT NULL CHECK (kind IN ('SCENE', 'SUMMARY', 'BREAK', 'NOTE')),
    payload  TEXT    NOT NULL,             -- JSON, shape per kind (src/engine/edl.py)
    PRIMARY KEY (run_id, generation, ord_no)
);

-- Append-only, like every other decision log here (hard rule 2). The room revises by appending a
-- new list, never by rewriting what it decided last week.
CREATE TRIGGER IF NOT EXISTS edl_no_update BEFORE UPDATE ON edl
BEGIN SELECT RAISE(ABORT, 'edl is append-only (CLAUDE.md hard rule 2): revise by appending'); END;
CREATE TRIGGER IF NOT EXISTS edl_no_delete BEFORE DELETE ON edl
BEGIN SELECT RAISE(ABORT, 'edl is append-only (CLAUDE.md hard rule 2): revise by appending'); END;

-- ---- the token ledger (run-lifecycle.md budget governor: spend is a queryable view) ----
CREATE TABLE IF NOT EXISTS llm_calls (
    call_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    turn       INTEGER,
    purpose    TEXT NOT NULL CHECK (purpose <> ''),                   -- decide | consolidate | frame | narrate | critic
    model      TEXT NOT NULL CHECK (model <> ''),
    tokens_in  INTEGER,
    tokens_out INTEGER,
    scene      TEXT
);

-- ---- scheduler durable state (run-lifecycle.md inventory item 4) ----
CREATE TABLE IF NOT EXISTS scheduler_state (
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    key TEXT NOT NULL CHECK (key <> ''),
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
    fingerprint TEXT PRIMARY KEY CHECK (fingerprint <> ''),          -- sha256 over the canonical (world, characters)
    built_at    TEXT NOT NULL,
    world       TEXT NOT NULL,             -- JSON: the world engine block as loaded
    characters  TEXT NOT NULL              -- JSON: {char_id: sheet}
);

-- Entity existence, exact. This is what makes an `entity:` citation resolvable
-- and a "does X exist" gate computable, rather than a similarity guess.
CREATE TABLE IF NOT EXISTS bible_entities (
    fingerprint TEXT NOT NULL REFERENCES bibles(fingerprint) CHECK (fingerprint <> ''),
    kind        TEXT NOT NULL CHECK (kind IN ('character','person','location')),
    entity_id TEXT NOT NULL CHECK (entity_id <> ''),
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
    fingerprint TEXT NOT NULL REFERENCES bibles(fingerprint) CHECK (fingerprint <> ''),
    law_id TEXT NOT NULL CHECK (law_id <> ''),
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

-- ---- the wound tier: an intensity that MOVES, and the log that makes the move durable ----
-- A wound was write-once: authored, recited to the actor every scene, and unreachable by anything
-- that happened to the character. This is where a movement lands.
--
-- SIGNED DELTAS, NOT ABSOLUTES. The sheet holds the authored intensity permanently and the log
-- holds the changes; the current value is authored + SUM(deltas), folded at resume by
-- levers.replay_wound_deltas. Storing an absolute here would make the log a snapshot, and hard
-- rule 2 makes the log the source of truth with the snapshot a derivable cache.
--
-- SURROGATE KEY + UNIQUE, NOT A COMPOSITE PRIMARY KEY. arc_diffs is keyed
-- PRIMARY KEY (run_id, char_id, turn) and therefore cannot hold two rows for one turn — but two
-- wounds can fire in one beat, so wound_id joins the uniqueness tuple. The surrogate follows the
-- `acquisitions` precedent and gives replay a stable insertion order.
--
-- THE WRITER MUST SELECT-THEN-INSERT. Measured against sqlite 3.45.1 with both triggers present:
-- UPDATE and DELETE abort; INSERT OR REPLACE aborts via the BEFORE DELETE trigger (REPLACE is
-- delete-then-insert, and it only aborts because db.connect sets PRAGMA recursive_triggers=ON —
-- with the pragma off it silently rewrites the row); but INSERT OR IGNORE is ACCEPTED SILENTLY
-- with the pragma on OR off, fires nothing, raises nothing, and DISCARDS A DIFFERING DELTA. It is
-- the obvious shortcut for "make replay idempotent", it contains no word the database can object
-- to, and only ledger.py's SELECT-first can close it.
CREATE TABLE IF NOT EXISTS wound_deltas (
    delta_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    char_id TEXT NOT NULL CHECK (char_id <> ''),
    turn     INTEGER NOT NULL,
    wound_id TEXT NOT NULL CHECK (wound_id <> ''),  -- fears_wounds[].id; a wound without one is unreachable
    delta    REAL    NOT NULL,                  -- SIGNED change in intensity; sign carries direction
    kind     TEXT    NOT NULL CHECK (kind IN ('event', 'erosion', 'correction')),
    source   TEXT    NOT NULL DEFAULT '',       -- prose: WHY a durable trait moved
    UNIQUE (run_id, char_id, turn, wound_id)
);

CREATE TRIGGER IF NOT EXISTS wound_deltas_no_update
BEFORE UPDATE ON wound_deltas BEGIN
    SELECT RAISE(ABORT, 'wound_deltas is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS wound_deltas_no_delete
BEFORE DELETE ON wound_deltas BEGIN
    SELECT RAISE(ABORT, 'wound_deltas is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;

-- ---- the MICRO tier: what one specific person makes you feel ----
-- docs/character-model.md "THE THREE LAYERS", the author's model: a macro change moves the overall
-- attitude; a micro change is "their joy towards a person ... so when they interact with this
-- person it's applied". This is the log of the second.
--
-- NOT relationship_deltas. That table's `axis` is trust|affinity|respect|debt — do I trust them.
-- This one's `primary` is one of the eight affective primitives — what do they make me feel. You
-- can trust someone completely and find no joy in them, and the four axes have no word for it.
--
-- SIGNED, and folded onto an authored base the same way wound_deltas are: the sheet may carry a
-- starting disposition, `toward.replay` stamps `_authored_toward` before applying anything, and the
-- effective value is base + sum(deltas). UNIQUE excludes `primary` deliberately at the tuple level
-- -- one row PER PRIMARY per person per turn, since a single event prices several primaries at once.
CREATE TABLE IF NOT EXISTS toward_deltas (
    delta_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    turn      INTEGER NOT NULL,
    perceiver TEXT NOT NULL CHECK (perceiver <> ''),  -- whose feeling moved
    target TEXT NOT NULL CHECK (target <> ''),  -- who it is toward
    primary_  TEXT    NOT NULL CHECK (primary_ <> ''),                 -- one of records.PRIMARIES ('primary' is SQL-reserved)
    delta     REAL    NOT NULL,                 -- SIGNED; the sign carries the direction
    source    TEXT    NOT NULL DEFAULT '',      -- prose: what moved it
    UNIQUE (run_id, turn, perceiver, target, primary_)
);

CREATE TRIGGER IF NOT EXISTS toward_deltas_no_update
BEFORE UPDATE ON toward_deltas BEGIN
    SELECT RAISE(ABORT, 'toward_deltas is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS toward_deltas_no_delete
BEFORE DELETE ON toward_deltas BEGIN
    SELECT RAISE(ABORT, 'toward_deltas is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;

-- ---- declared time: the CAUSE, logged; drift and erosion DERIVED from it ----
-- The director says a winter passed. Edges relax toward their resting priors and wounds erode a
-- little. Before this table those changes happened in memory and were recorded nowhere, so a
-- resumed cast had every drift silently undone -- the snapshot could not be derived from the log,
-- which is exactly what CLAUDE.md hard rule 2 forbids.
--
-- LOG THE CAUSE, NOT THE EFFECT. One row per declaration serves BOTH slow tiers: bonds.drift and
-- wound.erode take the same caller-declared unit. Logging the effects instead would need one row
-- per edge per axis per declaration, and would still leave wound erosion unlogged unless it grew
-- its own row family too.
--
-- ORDER MATTERS. Drift is multiplicative toward a rest point; a relationship delta is additive.
-- They do not commute, so `ledger.timeline_for` returns declarations and deltas INTERLEAVED in turn
-- order and `bonds.rehydrate` walks them in that order. A fold that applies all drifts and then all
-- deltas produces a different number.
CREATE TABLE IF NOT EXISTS time_declarations (
    decl_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL CHECK (run_id <> ''),
    turn     INTEGER NOT NULL,                  -- the turn the declaration takes effect BEFORE
    elapsed  REAL    NOT NULL CHECK (elapsed > 0),
    source   TEXT    NOT NULL DEFAULT '',       -- prose: what the director said passed
    UNIQUE (run_id, turn)
);

CREATE TRIGGER IF NOT EXISTS time_declarations_no_update
BEFORE UPDATE ON time_declarations BEGIN
    SELECT RAISE(ABORT, 'time_declarations is append-only (CLAUDE.md hard rule 2): UPDATE refused. A correction is a NEW row, never a rewritten one.');
END;
CREATE TRIGGER IF NOT EXISTS time_declarations_no_delete
BEFORE DELETE ON time_declarations BEGIN
    SELECT RAISE(ABORT, 'time_declarations is append-only (CLAUDE.md hard rule 2): DELETE refused. A correction is a NEW row, never a rewritten one.');
END;

-- The remaining log-like tables. `scenes` says "Append-only" in its own section header and had no
-- trigger; the v14 cfg pin depends on that row's fingerprint, boundaries and pov not being
-- rewritten. `decision_manifests` records what a decision READ, so rewriting one falsifies
-- provenance — the most log-like table left unprotected, and the consequence-graph view depends on
-- it. The bible trio is the hard-rule-1 pin: the same "rewrite the body under its fingerprint"
-- argument that earned `scene_cfgs` its triggers applies verbatim, and `read_api.place` reads
-- `bible_entities.what` by fingerprint.
-- `characters` is the REPLAY SEED. `Ledger._seed` reads it to seed the fold's agents, so deleting a
-- row changes every from-zero fold and reopens the resume-divergence class. It was exempted with a
-- reason that was simply untrue — "re-registered on resume" — and `register_character` is called
-- only on the create-run branch of both drivers. An exemption resting on a false reason is worse
-- than no exemption, because it reads as considered.
CREATE TRIGGER IF NOT EXISTS characters_no_update BEFORE UPDATE ON characters
BEGIN SELECT RAISE(ABORT, 'characters is append-only (CLAUDE.md hard rule 2): the fold seeds its agents from this table'); END;
CREATE TRIGGER IF NOT EXISTS characters_no_delete BEFORE DELETE ON characters
BEGIN SELECT RAISE(ABORT, 'characters is append-only (CLAUDE.md hard rule 2): deleting a row changes every from-zero fold'); END;

CREATE TRIGGER IF NOT EXISTS scenes_no_update BEFORE UPDATE ON scenes
BEGIN SELECT RAISE(ABORT, 'scenes is append-only (CLAUDE.md hard rule 2): a scene boundary and its cfg pin are what a replay is checked against'); END;
CREATE TRIGGER IF NOT EXISTS scenes_no_delete BEFORE DELETE ON scenes
BEGIN SELECT RAISE(ABORT, 'scenes is append-only (CLAUDE.md hard rule 2)'); END;
CREATE TRIGGER IF NOT EXISTS decision_manifests_no_update BEFORE UPDATE ON decision_manifests
BEGIN SELECT RAISE(ABORT, 'decision_manifests is append-only (CLAUDE.md hard rule 2): it records what a decision READ, and a rewritten manifest falsifies the provenance of a committed turn'); END;
CREATE TRIGGER IF NOT EXISTS decision_manifests_no_delete BEFORE DELETE ON decision_manifests
BEGIN SELECT RAISE(ABORT, 'decision_manifests is append-only (CLAUDE.md hard rule 2)'); END;
CREATE TRIGGER IF NOT EXISTS bibles_no_update BEFORE UPDATE ON bibles
BEGIN SELECT RAISE(ABORT, 'bibles is append-only (CLAUDE.md hard rule 1): a bible body must not change under its fingerprint - that is what the pin means'); END;
CREATE TRIGGER IF NOT EXISTS bibles_no_delete BEFORE DELETE ON bibles
BEGIN SELECT RAISE(ABORT, 'bibles is append-only (CLAUDE.md hard rule 1): a run still pins this fingerprint'); END;
CREATE TRIGGER IF NOT EXISTS bible_entities_no_update BEFORE UPDATE ON bible_entities
BEGIN SELECT RAISE(ABORT, 'bible_entities is append-only (CLAUDE.md hard rule 1): read_api.place reads `what` by fingerprint'); END;
CREATE TRIGGER IF NOT EXISTS bible_entities_no_delete BEFORE DELETE ON bible_entities
BEGIN SELECT RAISE(ABORT, 'bible_entities is append-only (CLAUDE.md hard rule 1)'); END;
CREATE TRIGGER IF NOT EXISTS bible_laws_no_update BEFORE UPDATE ON bible_laws
BEGIN SELECT RAISE(ABORT, 'bible_laws is append-only (CLAUDE.md hard rule 1): a law is what the run was computed against'); END;
CREATE TRIGGER IF NOT EXISTS bible_laws_no_delete BEFORE DELETE ON bible_laws
BEGIN SELECT RAISE(ABORT, 'bible_laws is append-only (CLAUDE.md hard rule 1)'); END;