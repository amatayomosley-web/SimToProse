"""db.py — SQLite connection + schema migration for the engine spine.

One job: hand back a WAL-mode connection with the v1 schema applied. The schema lives in
schema.sql (the contract); this module never defines tables inline. A DB stamped with a NEWER
version than this engine refuses to open — fail loud, never silently downgrade.
"""
import os
import pathlib
import re
import time
from .records import RecordError   # rule 6's bad-input type
from . import guards as _guards    # the record's insert guards, installed on every open (gate record-guards)
import sqlite3

SCHEMA_VERSION = 35  # v35: + db_role and the record lock (gate record-role, 2026-09-26 — the owner: a scene is a draft until he approves it, and only then enters the record. One row, schema.sql `db_role`, says what a file is: open | record | draft | history; guards.py installs, on every open, a BEFORE INSERT/UPDATE/DELETE trigger on every other table that refuses the write while that row says 'record' (DB_IS_RECORD), so a record changes only by `promote` or `restore` - a page copy of a whole approved state, which no row trigger sees. Every existing and fresh file opens as 'open', under which nothing is locked; the lock's shape is part of the guards' WALL, which is why the version steps). v34: + the record's insert guards (gate record-guards, 2026-09-26 — one BEFORE INSERT trigger per table whose columns schema.sql held only to "not empty", or to nothing, where the record layer holds them to a closed vocabulary or a range: relationship_deltas, rest_declared, toward_deltas, target_binds, wound_deltas, wound_minted, readings, utterances, bible_laws. Built from the record layer's own constants by guards.py and installed by `connect` on EVERY open where missing or stale — not only on a version step — so a migrated database, which cannot gain a CHECK by ALTER, carries the wall; a vocabulary change steps this version (one vocabulary per version, held at run time by each guard's stamp: DB_GUARD_VOCABULARY_SKEW) and reaches every database on its next open. Triggers, not a rebuild: a rebuild copies history through the new CHECK, and three of the 79 book databases hold rows under the emotion names retired 2026-09-08 or an older order spelling - they would refuse to migrate; no row is rewritten). v33: wound_minted UNIQUE (run_id, char_id, wound_id, turn) (gate flashback-windows, 2026-09-25 — a scar minted in a scene set in a character's past never reaches their present, so the present may mint the same one again; v26's UNIQUE without the turn rolled that beat back; rebuilt like v32). v32: scene_clock.at_minutes may be NEGATIVE (gate own-timelines, 2026-09-25 — a scene may be set on day 0 or before, and v25's CHECK (at_minutes >= 0) refused it; SQLite cannot drop a CHECK, so an older table is rebuilt by `_v32_scene_clock`, its rows copied as they are). v31: + lands_on (docs/emotion-arithmetic.md section 5 step 5, 2026-09-19 — whom the emotion seat said a beat reached; it decided the floor from this gate on and was never stored, so a fold or an audit could not see why a listener was pruned; a new table arrives through the idempotent script; no ALTER — the v28/v30 pattern). v30: + attachment_declared (docs/bond-arithmetic.md section 3, 2026-09-18 — what a character HOLDS that is not a person, as append-only rows: seeded authored from the sheet, declared by the director at scene start, folded on rehydrate beside the rest rows; a hold that lived only on the sheet in memory would be the v12 defect for the third tier in a row. A new table arrives through the idempotent script; no ALTER — the v28 pattern). v29: + relationship_deltas.cause (bond-arithmetic.md s6, 2026-09-18 — for a debt row, WHAT changed hands: the seat now reports transfers as facts and bonds.debt_postings derives the entry; a row that says the account moved but not for what cannot be read back; ALTER on a migrated db, the v27 pattern). v28: + rest_declared (docs/bond-arithmetic.md section 6, 2026-09-17 — where each edge axis RESTS; drift relaxed every edge toward _NEUTRAL / default_trust, so a devoted friend became a stranger over a winter and no row said why; now seeded `authored` from the sheet and lowered by a `cliff` row riding the causing turn, folded on rehydrate; an edge with no row rests where a stranger does, so pre-v28 logs replay to the numbers they held. A new table arrives through the idempotent script; no ALTER). v27: + relationship_deltas.object (bond-arithmetic.md s5, 2026-09-17 — the seat's object, WHAT the act was about, beside cause_event: a delta row that says who moved and by how much but not about what cannot be read back as a reason; ALTER on a migrated db, the v8 `ord` pattern). v26: + wound_minted (gate three, 2026-09-11 — a wound is engine state keyed (concept, path); one minted mid-story is a fact the log must show, folded on resume before wound_deltas; docs/emotion-arithmetic.md section 3). v25: + scene_clock (the scene's own reading in MINUTES — when it opened and how long it ran; the gap before the next scene is DERIVED from it and logged as a time_declaration, so elapsed stops being a unitless number in the author's head and emotion decay joins the one clock as its fifth consumer; docs/emotion-arithmetic.md section 4, 2026-09-10). v24: + readings (the emotional CAUSE of a beat, docs/emotion-arithmetic.md section 5 step 8). `turns.affect` stores where a character ENDED a beat; nothing stored WHY, so a replay from zero could not reach the same numbers once Phase 3 begins accumulating -- hard rule 2 false for emotion, the same hole v23 closed for aboutness and v12 for elapsed time. The rung is stored by NAME, not index: "no number leaves the appraiser" (section 1), and a name survives a re-band where a position does not (gate.py:249 records what `vault[N]` cost). NO UNIQUE across (turn, actor, path) -- two readings on one path in one beat are two additions, and a UNIQUE would silently keep one. v23: + target_binds (aboutness accretes). `targets.retarget` computed per-primitive aboutness every beat and both drivers wrote it to memory only, so it died at process exit - measured 2026-09-06, targets was the one accumulating tier absent from BOTH drivers' rehydrate blocks while arc/vault/edges/toward/wounds all replayed. Unlike its four sibling delta tables the fold is LAST-WRITE-WINS, not a sum: a target is replaced, never accumulated. A release is a row with target = '' - logging only positive binds would make un-binding underivable and the replay would diverge from the live run. v22: + non-empty CHECK on the seven columns v21's sweep did not CONSIDER. v21 enumerated columns from the schema but classified them against a hand-written set of NAMES, so a column nobody had thought of was not reported as a hole - it was never asked. stance_snapshots.character and toward_deltas.primary_ sit inside a PRIMARY KEY and a UNIQUE; dialogue_acts.act, llm_calls.purpose, llm_calls.model, utterances.tier and relationship_deltas.ord are discriminators. tests/test_place.py is inverted to protected-or-explained so an unrecognised column now FAILS instead of being skipped. Same migration asymmetry as v21. v21: + non-empty CHECK on every identity and discriminator column. NOT NULL does not mean present - SQLite satisfies it with the empty string, and measured 2026-09-02 a run with an empty run_id, a character with an empty char_id, an event with an empty type and a bible with an empty fingerprint all inserted clean. The Python layer refused them; this is the second wall, the same argument that grew the v9 append-only triggers. NOTE: SQLite cannot add a CHECK by ALTER, so a MIGRATED database keeps the old columns unconstrained - fresh databases get the wall, and the Python guards remain the only check on migrated ones. v20: + append-only triggers on characters. It was the one table exempted with a FALSE reason ("re-registered on resume" - register_character runs only on the create-run branch), and the exemption was not free: Ledger._seed reads it to seed the fold's agents, so an unprotected DELETE changes every from-zero fold. v19: + append-only triggers on scenes, decision_manifests, bibles, bible_entities and bible_laws (the remaining log-like tables: `scenes` calls itself append-only in its own header and the v14 cfg pin depends on it; decision_manifests records what a decision READ; the bible trio is the hard-rule-1 pin), and a CHECK on scenes.voice. v18: + append-only triggers on claim_extracts and scene_cfgs, which were the two DERIVED halves of append-only pairs and were freely rewritable - an extract could be edited to make two utterances stop contradicting each other, and a pinned cfg body could be rewritten to lie about its own fingerprint. Triggers are idempotent so a v17 db gains them on re-run. v17: + edl.generation. The append-only triggers told a reader to "revise by appending" and there was nowhere to append to - PRIMARY KEY (run_id, ord_no) made a second pass collide, and appending at fresh ord_nos made narration render the UNION of both cuts. A run got exactly one cut, forever. A revision is now a whole new generation; entries_for reads the highest. v16: + utterances / claim_extracts / claim_resolutions (lore accretes). claims.py was a pure detector with no table and no writer, so a character could describe their home town for ten chapters and the world learned nothing; bible_entities.what is one authored line that never grows. Tier stays DERIVED - the utterances row records PROVENANCE only and every later verdict is a resolution row, because a flipping tier column would be an UPDATE the v9 triggers refuse. v15: + edl (the edit decision list, append-only with triggers). cutting-room.md divides the cut three ways and marks only the DISCUSSION human - the record and the checks are mechanical - but grepping the tree for `edl` returned nothing, so the cut was human AND unrecorded and the README's traceability guarantee had no mechanism. The rejected 7-step automation stays rejected; this is the record, not a selector. v14: + scenes.cfg_fingerprint and the scene_cfgs table (the scene cfg is pinned the way a run pins its bible: content-hashed, stored, drift DETECTED not aborted). Before this, scenes recorded only the boundary, so a resumed run could not say what location, cast, props or opening tags shaped the turns it replays - the bible defect, repeated one table over. v13: + scenes.voice / scenes.knowledge (mixed-voice books are per-scene rows, the same authority that already picks scenes.pov; voice is a rendering instruction, knowledge decides what narrate.pov_split SHOWS the narrator). Defaults close-third/pov state what every pre-v13 row was, since those were the only renderable values. v12: + time_declarations (the director declares elapsed; drift and wound erosion are DERIVED from it at replay rather than logged as effects, so the snapshot is once again derivable from the log — before this, drift mutated memory at scene start and was recorded nowhere, and a resumed cast lost it entirely). v11: + toward_deltas (the MICRO tier: a per-target PER-PRIMARY additive vector — what one specific person makes you feel, distinct from relationship_deltas whose axes are trust|affinity|respect|debt; folded onto an authored base by toward.replay). v10: + wound_deltas (the wound tier: a durable, append-only log of signed intensity movements, folded onto the sheet-authored value at resume by levers.replay_wound_deltas; the surrogate key + UNIQUE(run,char,turn,wound) deliberately avoids the arc_diffs single-row-per-turn trap, since two wounds can fire in one beat). v9: + append-only TRIGGERS on the log tables (events, turns, recall_events, acquisitions, arc_diffs, relationship_deltas). Hard rule 2 was enforced only by ledger.py's habit of never issuing UPDATE/DELETE; anything else with a connection could rewrite a committed turn. Triggers are idempotent (CREATE TRIGGER IF NOT EXISTS) so a v8 db gains them on re-run, same mechanism v3 used for the scenes table. v8: + relationship_deltas.ord (first- vs second-order edge movement; the second order rendered and evaporated because the row had nowhere to hold it). v7: + bible_laws.excepts (scoped PERMITS — a permit that names law ids disarms only those). v6: law domains/epistemic realigned to the authoring blueprint. v5: + bible_laws (computable denial: IMPOSSIBLE vs FORBIDS). v4: + bibles/bible_entities (the run pins the bible it ran against). v3: + scenes table (scene boundaries for book-assembly). v2: + acquisitions. schema.sql is idempotent (IF NOT EXISTS), so older DBs re-run it and gain the new tables; COLUMN additions to existing tables are applied explicitly in _migrate, because a re-run CREATE IF NOT EXISTS skips an existing table.
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


def refuse_if_record(exc, doing):
    """Re-raise the record lock's refusal under DB_IS_RECORD; return quietly for anything else (gate record-role)."""
    if isinstance(exc, sqlite3.IntegrityError) and _guards.LOCK_MARK in str(exc):
        raise RecordError(
            "DB_IS_RECORD",
            "%s: this file is a book's RECORD or a HISTORY copy of it, which changes only by promote or restore - a "
            "page copy of a whole approved state (gate record-role). Run the writer on a draft (scripts/draft.py, gate "
            "draft-flow)" % doing) from exc


def refuse_if_guarded(exc, doing):
    """Re-raise a record guard's refusal under a REGISTERED code; return quietly for anything else (gate record-guards).

    A writer's record layer validated the value before the write, so either the guard was installed by an engine with
    another vocabulary (one that stepped this book while this one was running), or a writer stored a spelling its
    validator had normalised. `refuse_if_busy`'s sibling, for the same reason - "rolled back" alone reads as this
    engine's own input at fault. A record lock's refusal is named first (DB_IS_RECORD), by every caller of this."""
    refuse_if_record(exc, doing)
    if isinstance(exc, sqlite3.IntegrityError) and _guards.refused_by_guard(exc):
        raise RecordError(
            "DB_GUARD_REFUSED",
            "%s: the database's record guard refused a value this engine's record layer accepted - a guard installed "
            "by an engine with another vocabulary, or a writer storing a spelling its validator normalised (this engine "
            "is schema v%d): %s" % (doing, SCHEMA_VERSION, exc)) from exc


def connect(db_path, create=True):
    """`create` False opens only a file that exists, and SQLite's own `mode=rw` refuses one gone by the time it opens
    (gate draft-flow, review 1: a driver aimed at a draft moved aside had created a new, empty chronicle there)."""
    if not isinstance(db_path, (str, bytes, os.PathLike)):
        raise RecordError("DB_PATH_INVALID", "db_path must be a filesystem path, got %r" % type(db_path).__name__)
    parent = os.path.dirname(os.path.abspath(os.fspath(db_path)))
    if create and parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    con = (sqlite3.connect(db_path, timeout=BUSY_TIMEOUT_SECONDS) if create else sqlite3.connect(
        pathlib.Path(_existing(db_path, "db.connect")).resolve().as_uri() + "?mode=rw", uri=True,
        timeout=BUSY_TIMEOUT_SECONDS))
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
    # A REFUSED OPEN WRITES NOTHING (gate record-guards, review 4): a book this engine's guards refuse - another
    # engine's wall, a taken name - is refused before a migration commits its version step, not after it.
    if con.execute("PRAGMA user_version").fetchone()[0] < SCHEMA_VERSION:
        _guards.check(con)
    _migrate(con)
    # THE RECORD'S INSERT GUARDS, on every open and not only on a version step (gate record-guards): built from the
    # record layer's constants, so the database refuses what the record layer refuses however it was created; writes
    # only when a guard is missing or older (guards.install; a same-version guard with other words refuses the book).
    # Its IMMEDIATE transaction waits out another writer for the busy timeout; past it, DB_BUSY_TIMEOUT. AFTER
    # _migrate, so a step that DROPS or retypes a guarded column must drop that table's guard first (SQLite refuses
    # to drop a column a trigger reads; a rename is rewritten into the trigger) - install() re-creates it here.
    try:
        _guards.install(con)
    except sqlite3.OperationalError as exc:
        refuse_if_busy(exc, "db.connect: installing the record guards")
        raise
    return con


def release_guards(db_path):
    """Drop every record guard a book carries - this engine's and another engine's, whatever the name -> the names
    dropped; the next `connect` installs this engine's own (gate record-guards). The owner's way out of
    DB_GUARD_VOCABULARY_SKEW, run by scripts/release_guards.py. HERE and not in the script: this module is the one
    place a chronicle is opened writable (tests/test_integrity.py), with `connect`'s append-only pragma - but never
    through `connect`, which migrates and would refuse the book. An existing file only (no file is DB_PATH_INVALID,
    and none is created); no row is touched; a lock held past the busy timeout is DB_BUSY_TIMEOUT, nothing dropped."""
    if not isinstance(db_path, (str, bytes, os.PathLike)) or not os.path.isfile(db_path):
        raise RecordError("DB_PATH_INVALID", "db.release_guards: no database file at %r - nothing to release" % (db_path,))
    con = sqlite3.connect(db_path, timeout=BUSY_TIMEOUT_SECONDS)
    try:
        con.execute("PRAGMA recursive_triggers=ON")
        try:
            return _guards.release(con)
        except sqlite3.OperationalError as exc:
            refuse_if_busy(exc, "db.release_guards")
            raise
    finally:
        con.close()


# ---- THE BOOK'S ROLE (gate record-role) - schema.sql `db_role`; guards.py builds the record lock ---------------------
ROLES = ("open", "record", "draft", "history")
_BUSY_STEPS = (5, 6)                   # SQLITE_BUSY, SQLITE_LOCKED - what sqlite3_backup_step returns on a held lock
_BACKUP_SLEEP = 0.25
_SIDECARS = ("", "-wal", "-shm", "-journal")
_ROLE_SINCE = 35                       # the schema version that brought db_role


def _role_row(con):
    """This file's role row. A file from before v35 has no role table and reads as open; a v35 file whose row - or whole
    table - is missing reads as a record: only tampering removes either, and the lock treats it the same way (fail
    closed, review 1)."""
    try:
        row = con.execute("SELECT role, head, parent FROM db_role WHERE id = 1").fetchone()
    except sqlite3.OperationalError:                   # no such table
        before = con.execute("PRAGMA user_version").fetchone()[0] < _ROLE_SINCE
        return {"role": "open" if before else "record", "head": "", "parent": ""}
    return {"role": row[0], "head": row[1], "parent": row[2]} if row else {"role": "record", "head": "", "parent": ""}


def _existing(path, doing):
    if not isinstance(path, (str, bytes, os.PathLike)) or not os.path.isfile(path):
        raise RecordError("DB_PATH_INVALID", "%s: no database file at %r" % (doing, path))
    return os.fspath(path)


def _fresh(path, doing):
    """Refuse a target that exists - or whose WAL, shared-memory or journal file does, which SQLite would pair with a
    new file of that name. Takes a str or an os.PathLike path (review 2: a pathlib.Path had raised a TypeError here);
    bytes are no role primitive's path form (role_of refuses them too)."""
    path = os.fspath(path)
    taken = [path + s for s in _SIDECARS if os.path.exists(path + s)]
    if taken:
        raise RecordError("DB_COPY_TARGET_EXISTS", "%s: %s already exists - a copy is never written over a file, so "
                          "nothing kept is lost" % (doing, taken[0]))


def scratch_copy(src_path, dst_path, role=None):
    """A page copy of a book's database to a NEW file, role row and all -> dst_path. A writer rehearses a whole change
    on one and writes the book only if every step went in (scripts/declare.py, gate author-declarations review 1). No
    lineage minted it, so nothing can promote it; a record's copy stays a record. `role="open"` is the owner's exit
    from adoption (scripts/draft.py release): the COPY, and only the copy, is an open book at the record's state - the
    record itself is kept as it was (gate showrunner-drives-drafts)."""
    src, mem = connect(_existing(src_path, "db.scratch_copy")), sqlite3.connect(":memory:")
    try:
        _bounded_copy(src, mem, "db.scratch_copy: reading %s" % src_path)
        if role:
            _write_role(mem, role, _role_row(mem)["head"], _role_row(mem)["head"], "db.scratch_copy", in_memory=True)
        _fresh(dst_path, "db.scratch_copy")
        dst = sqlite3.connect(dst_path, timeout=_BACKUP_SLEEP)
        try:
            _bounded_copy(mem, dst, "db.scratch_copy: writing %s" % dst_path)
        finally:
            dst.close()
    finally:
        mem.close()
        src.close()
    return dst_path


def in_use(db_path):
    """Is a database still open somewhere? -> the sidecar file that proves it, or "". Opened and closed once here: the
    last connection to close removes a WAL database's -wal and -shm, so one that outlives this close belongs to another
    live connection. Their presence alone proves nothing - a read-only open (role_of) leaves both behind (measured
    2026-09-27, gate draft-flow). An existing file only (DB_PATH_INVALID)."""
    path = _existing(db_path, "db.in_use")
    con = sqlite3.connect(path, timeout=BUSY_TIMEOUT_SECONDS)
    try:
        con.execute("PRAGMA schema_version").fetchone()   # a read: the pager opens the WAL, so the close can tidy it
    finally:
        con.close()
    return next((path + s for s in ("-wal", "-shm") if os.path.exists(path + s)), "")


def role_of(db_path):
    """-> {"role", "head", "parent"} of a database file, read-only: no migration, no write (a file from before v35
    reads as open). An existing file only (DB_PATH_INVALID)."""
    path = _existing(db_path, "db.role_of")
    con = sqlite3.connect(pathlib.Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_TIMEOUT_SECONDS)
    try:
        return _role_row(con)
    finally:
        con.close()


def _bounded_copy(src, dst, doing):
    """Page-copy `src`'s database onto `dst` in ONE destination transaction, giving up past the busy timeout. sqlite's
    backup retries a busy destination forever (measured 2026-09-26, props/verify_backup_spin.py); the progress callback
    sees every retry's status and aborts once BUSY_TIMEOUT_SECONDS have passed on the clock, which leaves `dst` exactly
    as it was. The clock, not a count of sleeps: `dst`'s own busy handler waits inside a step too (review 1: counting
    sleeps measured 10.6 s at a 5 s setting), which is also why callers open `dst` with a timeout of _BACKUP_SLEEP.
    All pages go in one step, so every busy status comes before the copy starts."""
    start = time.monotonic()

    def progress(status, _remaining, _total):
        if status in _BUSY_STEPS:
            if time.monotonic() - start > BUSY_TIMEOUT_SECONDS:
                raise RecordError("DB_BUSY_TIMEOUT", "%s: another connection held the target past the %.1fs busy "
                                  "timeout (db.py BUSY_TIMEOUT_SECONDS) - nothing was copied; retry once it is released"
                                  % (doing, BUSY_TIMEOUT_SECONDS))
    src.backup(dst, pages=-1, progress=progress, sleep=_BACKUP_SLEEP)


def _write_role(con, role, head, parent, doing, in_memory=False):
    """Set the role row. Refuses a bad role, an empty lineage id, and an update that matched no row (the row was
    removed) - DB_ROLE_WRONG. `in_memory` is for a private copy only (copy_to, _land): the role row's own guard lets a
    file's role change on disk only from open to record, so the copy lifts it, sets the row and puts the same guard
    back before the copy reaches any file - and refuses a connection that has a file behind it (review 2, nit e)."""
    if role not in ROLES or not isinstance(head, str) or not head.strip():
        raise RecordError("DB_ROLE_WRONG", "%s: role %r with lineage id %r - a role is one of %s and a lineage id is "
                          "non-empty text" % (doing, role, head, ", ".join(ROLES)))
    if in_memory and con.execute("PRAGMA database_list").fetchone()[2]:
        raise RecordError("DB_ROLE_WRONG", "%s: the role guard is lifted only on a private in-memory copy, never on a "
                          "file" % doing)
    held = con.execute("SELECT name, sql FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'db_role'"
                       ).fetchall() if in_memory else []
    try:
        for name, _sql in held:
            con.execute('DROP TRIGGER "%s"' % str(name).replace('"', '""'))
        cur = con.execute("UPDATE db_role SET role = ?, head = ?, parent = ? WHERE id = 1", (role, head, str(parent or "")))
        if cur.rowcount != 1:
            raise RecordError("DB_ROLE_WRONG", "%s: the file has no role row to set - it was removed" % doing)
        for _name, sql in held:
            con.execute(sql)
        con.commit()
    except sqlite3.OperationalError as exc:
        refuse_if_busy(exc, doing)
        if "no such table" in str(exc):
            raise RecordError("DB_ROLE_WRONG", "%s: the file has no role table to set - it was dropped" % doing) from exc
        raise
    except sqlite3.IntegrityError as exc:
        refuse_if_record(exc, doing)
        raise


def _probe_lock(path, doing):
    """Take and release the file's write lock under the busy timeout, so a writer still inside a transaction is named
    (DB_BUSY_TIMEOUT) before anything is copied."""
    con = sqlite3.connect(path, timeout=BUSY_TIMEOUT_SECONDS)
    try:
        con.execute("BEGIN IMMEDIATE")
        con.rollback()
    except sqlite3.OperationalError as exc:
        refuse_if_busy(exc, doing)
        raise
    finally:
        con.close()


def _land(src, record_path, role, head, parent, doing):
    """Read `src` into memory, set its role row there, and page-copy it onto the record file, then checkpoint the WAL:
    the record file never holds anything but a whole record - the old one until the copy's one transaction commits,
    the new one after (measured: a copy aborted part-way leaves the destination whole). A reader inside a read
    transaction at that moment keeps its snapshot, and the WAL empties once it lets go."""
    mem = sqlite3.connect(":memory:")
    try:
        _bounded_copy(src, mem, doing + ": reading")
        _write_role(mem, role, head, parent, doing, in_memory=True)
        rec = sqlite3.connect(record_path, timeout=_BACKUP_SLEEP)
        try:
            _bounded_copy(mem, rec, doing + ": writing the record")
            rec.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            rec.close()
    finally:
        mem.close()


def adopt(db_path, head):
    """Make an OPEN book's database its RECORD, lineage id `head` -> its role row. From here the record lock refuses
    every write and the book changes only by promote or restore. Refuses a file in any role but open (DB_ROLE_WRONG);
    the caller keeps the pre-adoption copy (scripts/draft.py, gate draft-flow)."""
    con = connect(_existing(db_path, "db.adopt"))      # migrated first: the role row and the lock exist after this
    try:
        now = _role_row(con)
        if now["role"] != "open":
            raise RecordError("DB_ROLE_WRONG", "db.adopt: %s is already a %s (head %r) - only an open file is adopted"
                              % (db_path, now["role"], now["head"]))
        _write_role(con, "record", head, "", "db.adopt")
        return _role_row(con)
    finally:
        con.close()


def copy_to(src_path, dst_path, role, head=None):
    """Copy a book's database to a NEW file -> the copy's role row. A DRAFT, from a record or an open book, carries
    lineage id `head` - never its source's own - with the source's head as parent. A HISTORY copy is made only from a
    record and keeps that record's own head and parent: it IS that record, kept (review 1: a history copy of anything,
    restored, was a promote without the stale check). The role is read from, and set on, the in-memory copy - one
    snapshot - so the new file is never on disk in the source's role. Refuses an existing target."""
    src_path = _existing(src_path, "db.copy_to")
    if role not in ("draft", "history"):
        raise RecordError("DB_ROLE_WRONG", "db.copy_to: a copy is a draft or a history copy, not %r" % (role,))
    _fresh(dst_path, "db.copy_to")
    src = connect(src_path)                            # migrated and guarded, so the copy carries this engine's wall
    mem = sqlite3.connect(":memory:")
    try:
        _bounded_copy(src, mem, "db.copy_to: reading %s" % src_path)
        s = _role_row(mem)
        if role == "history" and s["role"] != "record":
            raise RecordError("DB_ROLE_WRONG", "db.copy_to: a history copy is made only from a record, not a %s" % s["role"])
        if role == "draft" and (s["role"] not in ("record", "open") or head == s["head"]):
            raise RecordError("DB_ROLE_WRONG", "db.copy_to: a draft is made from a record or an open book under a lineage "
                              "id of its own - here from a %s with id %r (the source's is %r)" % (s["role"], head, s["head"]))
        new_head, parent = (s["head"], s["parent"]) if role == "history" else (head, s["head"])
        _write_role(mem, role, new_head, parent, "db.copy_to", in_memory=True)
        os.makedirs(os.path.dirname(os.path.abspath(dst_path)) or ".", exist_ok=True)
        dst = sqlite3.connect(dst_path, timeout=_BACKUP_SLEEP)
        try:
            _bounded_copy(mem, dst, "db.copy_to: writing %s" % dst_path)
        finally:
            dst.close()
    finally:
        mem.close()
        src.close()
    return role_of(dst_path)


def promote(draft_path, record_path, history_path, on_kept=None):
    """Make an approved DRAFT the book's RECORD - a page copy of the whole draft, never a merge of rows -> {"head",
    "parent", "history"}. In order: the draft must be a draft under a lineage id of its own whose parent is the
    record's head (DB_PROMOTE_STALE: another promote got there first, or it was copied from another record), the
    record a record (DB_ROLE_WRONG); the record's write lock is probed (DB_BUSY_TIMEOUT, never a spin); the record as
    it is is kept at `history_path` in role history - and if its head is no longer the one checked, another promote
    landed meanwhile (DB_PROMOTE_STALE, the kept copy stays); then the draft lands in role record, parent the old head.
    Two promotes racing past that check are the book lease's to exclude (gate draft-flow). `on_kept(history_path)` is
    called once the kept copy exists and before the landing - where the lineage logs it (gate draft-flow, review 1)."""
    draft_path, record_path = _existing(draft_path, "db.promote"), _existing(record_path, "db.promote")
    _fresh(history_path, "db.promote")
    draft = connect(draft_path)
    try:
        d, r = _role_row(draft), role_of(record_path)
        if d["role"] != "draft" or r["role"] != "record" or d["head"] == r["head"]:
            raise RecordError("DB_ROLE_WRONG", "db.promote: a draft lands on a record under a lineage id of its own - "
                              "here a %s %r onto a %s %r (adopt the book first)" % (d["role"], d["head"], r["role"], r["head"]))
        if d["parent"] != r["head"]:
            raise RecordError("DB_PROMOTE_STALE", "db.promote: the draft was copied from head %r, and the record is at "
                              "%r - promoting it would drop what landed since; redo the work on a fresh draft"
                              % (d["parent"], r["head"]))
        _probe_lock(record_path, "db.promote")
        kept = copy_to(record_path, history_path, "history")
        if kept["head"] != r["head"]:
            raise RecordError("DB_PROMOTE_STALE", "db.promote: another promote landed (head %r) while this one checked "
                              "%r - the record as it now is was kept at %s; redo the work on a fresh draft"
                              % (kept["head"], r["head"], history_path))
        if on_kept:
            on_kept(history_path)
        _land(draft, record_path, "record", d["head"], r["head"], "db.promote")
    finally:
        draft.close()
    return {"head": d["head"], "parent": r["head"], "history": history_path}


def restore(history_path, record_path, keep_path, on_kept=None):
    """Rewind: make a HISTORY copy the book's RECORD again -> {"head", "parent", "kept"}. Refuses a copy from a newer
    engine (DB_SCHEMA_TOO_NEW - the record would then refuse this engine). The record as it is goes to `keep_path`
    first (a rewind keeps what it removed); then the history copy lands in role record with its own head and parent,
    in promote's order. Which history copy may be restored - one in the record's head chain - is the lineage's question
    (scripts/draft.py, gate draft-flow), not this primitive's. `on_kept(keep_path)` as in promote."""
    history_path, record_path = _existing(history_path, "db.restore"), _existing(record_path, "db.restore")
    _fresh(keep_path, "db.restore")
    h, r = role_of(history_path), role_of(record_path)
    if h["role"] != "history" or r["role"] != "record":
        raise RecordError("DB_ROLE_WRONG", "db.restore: a history copy lands on a record - here a %s onto a %s"
                          % (h["role"], r["role"]))
    hist = sqlite3.connect(pathlib.Path(history_path).resolve().as_uri() + "?mode=ro", uri=True,
                           timeout=BUSY_TIMEOUT_SECONDS)       # read-only: the kept copy is never rewritten
    try:
        v = hist.execute("PRAGMA user_version").fetchone()[0]
        if v > SCHEMA_VERSION:
            raise RecordError("DB_SCHEMA_TOO_NEW", "db.restore: %s is schema v%d, newer than this engine's v%d - restored, "
                              "the record would refuse this engine" % (history_path, v, SCHEMA_VERSION))
        _probe_lock(record_path, "db.restore")
        copy_to(record_path, keep_path, "history")
        if on_kept:
            on_kept(keep_path)
        _land(hist, record_path, "record", h["head"], h["parent"], "db.restore")
    finally:
        hist.close()
    return {"head": h["head"], "parent": h["parent"], "kept": keep_path}


def _migrate(con):
    v = con.execute("PRAGMA user_version").fetchone()[0]
    if v > SCHEMA_VERSION:
        raise RecordError("DB_SCHEMA_TOO_NEW", "db schema is v%d but this engine knows v%d — refusing to open" % (v, SCHEMA_VERSION))
    if v < SCHEMA_VERSION:
        with open(_SCHEMA_PATH, encoding="utf-8") as fh:
            _rebuild(con, fh.read())                    # runs the schema script, rebuilding v32's and v33's tables
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
        if "object" not in cols:
            con.execute("ALTER TABLE relationship_deltas ADD COLUMN object TEXT NOT NULL DEFAULT ''")
        if "cause" not in cols:
            con.execute("ALTER TABLE relationship_deltas ADD COLUMN cause TEXT NOT NULL DEFAULT ''")
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


# TABLES REBUILT AROUND THE SCHEMA SCRIPT, because SQLite cannot drop a CHECK or a UNIQUE: (table, the old shape's
# mark, where the old table waits, its columns). A WORD BOUNDARY, NOT A SUBSTRING: scene_clock's own
# `beat_minutes >= 0` contains "at_minutes >= 0", so a substring test found v25's CHECK in every scene_clock there is.
_REBUILT = (
    ("scene_clock", re.compile(r"\bat_minutes\s*>=\s*0"), "scene_clock_v31",
     "clock_id, run_id, turn, at_minutes, lasts_minutes, beat_minutes"),                          # v32
    ("wound_minted", re.compile(r"UNIQUE\s*\(\s*run_id\s*,\s*char_id\s*,\s*wound_id\s*\)"), "wound_minted_v32",
     "mint_id, run_id, turn, char_id, wound_id, concept, path, intensity, source, text, triggers"),   # v33
)


def _rebuild(con, schema):
    """Run the schema script, rebuilding each table of `_REBUILT` whose old shape is still on disk around it (v32: a
    scene may be set before day 1; v33: a scar may be minted again in a character's present after a window minted it).
    The old table is renamed aside with its append-only triggers dropped, the script creates the new one and its
    triggers, and the rows are copied across as they are before the old one goes. Each step is idempotent on its own
    condition, so an open interrupted part-way finishes the rebuild on the next."""
    for table, old_shape, aside, _cols in _REBUILT:
        old = con.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
        if old is not None and old_shape.search(old[0]):
            # its guard and record lock go too, or the aside would hold their names and the next open, meeting
            # them on another table, would refuse the book (gate record-role, review 1) - install re-creates them
            ours = [table + s for s in ("_no_update", "_no_delete", _guards.SUFFIX)]
            ours += [table + _guards.LOCK + short for short in ("ins", "upd", "del")]
            con.executescript("BEGIN; %s ALTER TABLE %s RENAME TO %s; COMMIT;"
                              % ("".join("DROP TRIGGER IF EXISTS %s; " % n for n in ours), table, aside))
    con.executescript(schema)
    for table, _old, aside, cols in _REBUILT:
        if con.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (aside,)).fetchone():
            con.executescript("BEGIN; INSERT INTO %s (%s) SELECT %s FROM %s; DROP TABLE %s; COMMIT;"
                              % (table, cols, cols, aside, aside))
