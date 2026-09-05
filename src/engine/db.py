"""db.py — SQLite connection + schema migration for the engine spine.

One job: hand back a WAL-mode connection with the v1 schema applied. The schema lives in
schema.sql (the contract); this module never defines tables inline. A DB stamped with a NEWER
version than this engine refuses to open — fail loud, never silently downgrade.
"""
import os
import sqlite3
from .errors import EngineError

SCHEMA_VERSION = 9   # v9: + append-only TRIGGERS on the log tables (events, turns, recall_events, acquisitions, arc_diffs, relationship_deltas). Hard rule 2 was enforced only by ledger.py's habit of never issuing UPDATE/DELETE; anything else with a connection could rewrite a committed turn. Triggers are idempotent (CREATE TRIGGER IF NOT EXISTS) so a v8 db gains them on re-run, same mechanism v3 used for the scenes table. v8: + relationship_deltas.ord (first- vs second-order edge movement; the second order rendered and evaporated because the row had nowhere to hold it). v7: + bible_laws.excepts (scoped PERMITS — a permit that names law ids disarms only those). v6: law domains/epistemic realigned to the authoring blueprint. v5: + bible_laws (computable denial: IMPOSSIBLE vs FORBIDS). v4: + bibles/bible_entities (the run pins the bible it ran against). v3: + scenes table (scene boundaries for book-assembly). v2: + acquisitions. schema.sql is idempotent (IF NOT EXISTS), so older DBs re-run it and gain the new tables; COLUMN additions to existing tables are applied explicitly in _migrate, because a re-run CREATE IF NOT EXISTS skips an existing table.
_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def connect(db_path):
    if not isinstance(db_path, (str, bytes, os.PathLike)):
        raise EngineError("DB_PATH_NOT_A_PATH", "db_path must be a filesystem path, got %r" % type(db_path).__name__)
    parent = os.path.dirname(os.path.abspath(os.fspath(db_path)))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    con = sqlite3.connect(db_path)
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
        raise EngineError("DB_SCHEMA_VERSION_MISMATCH", "db schema is v%d but this engine knows v%d — refusing to open" % (v, SCHEMA_VERSION))
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
        con.execute("PRAGMA user_version=%d" % SCHEMA_VERSION)
        con.commit()
