"""db.py — SQLite connection + schema migration for the engine spine.

One job: hand back a WAL-mode connection with the v1 schema applied. The schema lives in
schema.sql (the contract); this module never defines tables inline. A DB stamped with a NEWER
version than this engine refuses to open — fail loud, never silently downgrade.
"""
import os
from .records import RecordError   # rule 6's bad-input type
import sqlite3

SCHEMA_VERSION = 22  # v22: + non-empty CHECK on the seven columns v21's sweep did not CONSIDER. v21 enumerated columns from the schema but classified them against a hand-written set of NAMES, so a column nobody had thought of was not reported as a hole - it was never asked. stance_snapshots.character and toward_deltas.primary_ sit inside a PRIMARY KEY and a UNIQUE; dialogue_acts.act, llm_calls.purpose, llm_calls.model, utterances.tier and relationship_deltas.ord are discriminators. tests/test_place.py is inverted to protected-or-explained so an unrecognised column now FAILS instead of being skipped. Same migration asymmetry as v21. v21: + non-empty CHECK on every identity and discriminator column. NOT NULL does not mean present - SQLite satisfies it with the empty string, and measured 2026-09-02 a run with an empty run_id, a character with an empty char_id, an event with an empty type and a bible with an empty fingerprint all inserted clean. The Python layer refused them; this is the second wall, the same argument that grew the v9 append-only triggers. NOTE: SQLite cannot add a CHECK by ALTER, so a MIGRATED database keeps the old columns unconstrained - fresh databases get the wall, and the Python guards remain the only check on migrated ones. v20: + append-only triggers on characters. It was the one table exempted with a FALSE reason ("re-registered on resume" - register_character runs only on the create-run branch), and the exemption was not free: Ledger._seed reads it to seed the fold's agents, so an unprotected DELETE changes every from-zero fold. v19: + append-only triggers on scenes, decision_manifests, bibles, bible_entities and bible_laws (the remaining log-like tables: `scenes` calls itself append-only in its own header and the v14 cfg pin depends on it; decision_manifests records what a decision READ; the bible trio is the hard-rule-1 pin), and a CHECK on scenes.voice. v18: + append-only triggers on claim_extracts and scene_cfgs, which were the two DERIVED halves of append-only pairs and were freely rewritable - an extract could be edited to make two utterances stop contradicting each other, and a pinned cfg body could be rewritten to lie about its own fingerprint. Triggers are idempotent so a v17 db gains them on re-run. v17: + edl.generation. The append-only triggers told a reader to "revise by appending" and there was nowhere to append to - PRIMARY KEY (run_id, ord_no) made a second pass collide, and appending at fresh ord_nos made narration render the UNION of both cuts. A run got exactly one cut, forever. A revision is now a whole new generation; entries_for reads the highest. v16: + utterances / claim_extracts / claim_resolutions (lore accretes). claims.py was a pure detector with no table and no writer, so a character could describe their home town for ten chapters and the world learned nothing; bible_entities.what is one authored line that never grows. Tier stays DERIVED - the utterances row records PROVENANCE only and every later verdict is a resolution row, because a flipping tier column would be an UPDATE the v9 triggers refuse. v15: + edl (the edit decision list, append-only with triggers). cutting-room.md divides the cut three ways and marks only the DISCUSSION human - the record and the checks are mechanical - but grepping the tree for `edl` returned nothing, so the cut was human AND unrecorded and the README's traceability guarantee had no mechanism. The rejected 7-step automation stays rejected; this is the record, not a selector. v14: + scenes.cfg_fingerprint and the scene_cfgs table (the scene cfg is pinned the way a run pins its bible: content-hashed, stored, drift DETECTED not aborted). Before this, scenes recorded only the boundary, so a resumed run could not say what location, cast, props or opening tags shaped the turns it replays - the bible defect, repeated one table over. v13: + scenes.voice / scenes.knowledge (mixed-voice books are per-scene rows, the same authority that already picks scenes.pov; voice is a rendering instruction, knowledge decides what narrate.pov_split SHOWS the narrator). Defaults close-third/pov state what every pre-v13 row was, since those were the only renderable values. v12: + time_declarations (the director declares elapsed; drift and wound erosion are DERIVED from it at replay rather than logged as effects, so the snapshot is once again derivable from the log — before this, drift mutated memory at scene start and was recorded nowhere, and a resumed cast lost it entirely). v11: + toward_deltas (the MICRO tier: a per-target PER-PRIMARY additive vector — what one specific person makes you feel, distinct from relationship_deltas whose axes are trust|affinity|respect|debt; folded onto an authored base by toward.replay). v10: + wound_deltas (the wound tier: a durable, append-only log of signed intensity movements, folded onto the sheet-authored value at resume by levers.replay_wound_deltas; the surrogate key + UNIQUE(run,char,turn,wound) deliberately avoids the arc_diffs single-row-per-turn trap, since two wounds can fire in one beat). v9: + append-only TRIGGERS on the log tables (events, turns, recall_events, acquisitions, arc_diffs, relationship_deltas). Hard rule 2 was enforced only by ledger.py's habit of never issuing UPDATE/DELETE; anything else with a connection could rewrite a committed turn. Triggers are idempotent (CREATE TRIGGER IF NOT EXISTS) so a v8 db gains them on re-run, same mechanism v3 used for the scenes table. v8: + relationship_deltas.ord (first- vs second-order edge movement; the second order rendered and evaporated because the row had nowhere to hold it). v7: + bible_laws.excepts (scoped PERMITS — a permit that names law ids disarms only those). v6: law domains/epistemic realigned to the authoring blueprint. v5: + bible_laws (computable denial: IMPOSSIBLE vs FORBIDS). v4: + bibles/bible_entities (the run pins the bible it ran against). v3: + scenes table (scene boundaries for book-assembly). v2: + acquisitions. schema.sql is idempotent (IF NOT EXISTS), so older DBs re-run it and gain the new tables; COLUMN additions to existing tables are applied explicitly in _migrate, because a re-run CREATE IF NOT EXISTS skips an existing table.
_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

# HOW LONG A WRITER WAITS FOR THE LOCK BEFORE GIVING UP. sqlite3 defaults this to 5.0 and the
# engine never said so, which meant an operator hitting it was hitting a decision nobody had made.
# Named here because `busy_timeout` is the only reason DB_BUSY_TIMEOUT ever fires, so the number
# and the code belong in one place.
BUSY_TIMEOUT_SECONDS = 5.0


def is_busy(exc):
    """Is this OperationalError the LOCK, rather than some other operational fault?

    `sqlite_errorname` is exact and has been on the exception since 3.11. A hand-CONSTRUCTED
    `sqlite3.OperationalError` carries no such attribute, so the message fallback is not belt-and-
    braces — it is what a test double hits. Measured on a real busy error from this engine's own
    connection: errorcode 5, errorname SQLITE_BUSY.
    """
    name = getattr(exc, "sqlite_errorname", None)
    if name is not None:
        return name in ("SQLITE_BUSY", "SQLITE_BUSY_SNAPSHOT", "SQLITE_BUSY_TIMEOUT")
    return "database is locked" in str(exc) or "database table is locked" in str(exc)


def refuse_if_busy(exc, doing):
    """Re-raise a lock timeout under a REGISTERED code; return quietly for anything else.

    A TIMEOUT, NEVER A REFUSAL, and the distinction is the whole reason it gets its own name rather
    than joining LEDGER_RUN_EXISTS or LEDGER_TURN_COMMIT_ROLLED_BACK. Every other code in the spine
    tells an operator to FIX THEIR INPUT; this one tells them the identical call will succeed once
    the other writer finishes. Folding it into either of those would make one code mean both.
    """
    if is_busy(exc):
        raise RecordError(
            "DB_BUSY_TIMEOUT",
            "%s: another writer held the database past the %.1fs busy timeout (db.py "
            "BUSY_TIMEOUT_SECONDS). Nothing is wrong with this call — retry it. If it keeps "
            "happening, a writer is holding a transaction open far longer than a turn should take."
            % (doing, BUSY_TIMEOUT_SECONDS)) from exc


def connect(db_path):
    if not isinstance(db_path, (str, bytes, os.PathLike)):
        raise RecordError("DB_PATH_INVALID", "db_path must be a filesystem path, got %r" % type(db_path).__name__)
    parent = os.path.dirname(os.path.abspath(os.fspath(db_path)))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    con = sqlite3.connect(db_path, timeout=BUSY_TIMEOUT_SECONDS)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    # WITHOUT THIS, THE APPEND-ONLY TRIGGERS DO NOT HOLD. Schema v9 added BEFORE DELETE triggers to
    # events/turns/recall_events/acquisitions/arc_diffs/relationship_deltas so that CLAUDE.md hard
    # rule 2 is enforced by the DATABASE and not by ledger.py's habit of never issuing UPDATE or
    # DELETE. But SQLite's REPLACE conflict resolution performs its delete WITHOUT firing delete
    # triggers unless recursive_triggers is on — and `ledger.append_arc_diff` was the table's only
    # writer, using INSERT OR REPLACE. So the one path that could rewrite a committed arc row was
    # the one path the trigger could not see. Demonstrated on a fresh db from this schema on
    # 2026-08-30: REPLACE overwrote the row; with the pragma on, the same statement is refused.
    con.execute("PRAGMA recursive_triggers=ON")
    _migrate(con)
    return con


def _migrate(con):
    v = con.execute("PRAGMA user_version").fetchone()[0]
    if v > SCHEMA_VERSION:
        raise RecordError("DB_SCHEMA_TOO_NEW", "db schema is v%d but this engine knows v%d — refusing to open" % (v, SCHEMA_VERSION))
    if v < SCHEMA_VERSION:
        with open(_SCHEMA_PATH, encoding="utf-8") as fh:
            con.executescript(fh.read())
        # v7: bible_laws.excepts. Fresh DBs get it from the CREATE; a DB whose
        # bible_laws predates v7 needs the ALTER, and the presence check makes
        # this idempotent without swallowing real errors.
        cols = {r[1] for r in con.execute("PRAGMA table_info(bible_laws)")}
        if "excepts" not in cols:
            con.execute("ALTER TABLE bible_laws ADD COLUMN excepts TEXT NOT NULL DEFAULT ''")
        # v8: relationship_deltas.ord. Every pre-v8 row IS first-order, so the default states
        # the truth about existing data rather than guessing at it.
        cols = {r[1] for r in con.execute("PRAGMA table_info(relationship_deltas)")}
        if "ord" not in cols:
            con.execute("ALTER TABLE relationship_deltas ADD COLUMN ord TEXT NOT NULL DEFAULT 'first'")
        # v13: scenes.voice / scenes.knowledge. Every pre-v13 scene rendered close-third and
        # POV-bounded — the prompt hardcoded the one and pov_split had no other branch — so the
        # defaults state the truth about existing rows rather than guessing at them.
        # v17: edl.generation. Pre-v17 rows are generation 0, which is what they were.
        cols = {r[1] for r in con.execute("PRAGMA table_info(edl)")}
        if cols and "generation" not in cols:
            con.execute("ALTER TABLE edl ADD COLUMN generation INTEGER NOT NULL DEFAULT 0")
        # v13: scenes.voice / scenes.knowledge, and v14 cfg_fingerprint. Every pre-v13 scene
        # rendered close-third and POV-bounded, so the defaults state the truth about existing rows.
        cols = {r[1] for r in con.execute("PRAGMA table_info(scenes)")}
        # v14: scenes.cfg_fingerprint. Empty means a scene recorded before pinning existed. That
        # reads as "unknown" and never as "unchanged" — `Ledger.cfg_drifted` returns False with a
        # reason for it, the way `bible.for_run` returns None for runs predating fingerprints.
        if "cfg_fingerprint" not in cols:
            con.execute("ALTER TABLE scenes ADD COLUMN cfg_fingerprint TEXT NOT NULL DEFAULT ''")
        if "voice" not in cols:
            con.execute("ALTER TABLE scenes ADD COLUMN voice TEXT NOT NULL DEFAULT 'close-third'")
        if "knowledge" not in cols:
            # SQLite cannot add a CHECK via ALTER, so a migrated DB lacks the constraint a fresh
            # one gets. `ledger.append_scene` validates instead — the guard has to live where both
            # paths pass, not only where the CREATE ran.
            con.execute("ALTER TABLE scenes ADD COLUMN knowledge TEXT NOT NULL DEFAULT 'pov'")
        con.execute("PRAGMA user_version=%d" % SCHEMA_VERSION)
        con.commit()
