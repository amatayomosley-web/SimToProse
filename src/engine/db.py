"""db.py — SQLite connection + schema migration for the engine spine.

One job: hand back a WAL-mode connection with the v1 schema applied. The schema lives in
schema.sql (the contract); this module never defines tables inline. A DB stamped with a NEWER
version than this engine refuses to open — fail loud, never silently downgrade.
"""
import os
import sqlite3

SCHEMA_VERSION = 3   # v3: + scenes table (scene boundaries for book-assembly). v2: + acquisitions. schema.sql is idempotent (IF NOT EXISTS), so older DBs re-run it and gain the new tables.
_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def connect(db_path):
    if not isinstance(db_path, (str, bytes, os.PathLike)):
        raise TypeError("db_path must be a filesystem path, got %r" % type(db_path).__name__)
    parent = os.path.dirname(os.path.abspath(os.fspath(db_path)))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    _migrate(con)
    return con


def _migrate(con):
    v = con.execute("PRAGMA user_version").fetchone()[0]
    if v > SCHEMA_VERSION:
        raise RuntimeError("db schema is v%d but this engine knows v%d — refusing to open" % (v, SCHEMA_VERSION))
    if v < SCHEMA_VERSION:
        with open(_SCHEMA_PATH, encoding="utf-8") as fh:
            con.executescript(fh.read())
        con.execute("PRAGMA user_version=%d" % SCHEMA_VERSION)
        con.commit()
