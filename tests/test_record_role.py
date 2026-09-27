#!/usr/bin/env python3
"""test_record_role.py - a book's RECORD changes only by promote or restore; everything else runs on a draft.

The owner, 2026-09-26: "not save runs into the books db until it's approved so a scene is draft until it's approved and
then it's saved into record." Gate record-role puts the rule in the database: one row, `db_role`, says what a file is
(open | record | draft | history), and guards.py's record lock refuses every INSERT, UPDATE and DELETE on a record. This
suite drives the real primitives (db.adopt, copy_to, promote, restore, role_of) and real writers (Ledger.create_run,
claims.record, a raw sqlite3 connection - the stranger's script) on scratch files, never a book.

Stdlib only, script-style. Exit 0 = all pass.
"""
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from src.engine import claims, db, guards, integrity, world_events    # noqa: E402
from src.engine.ledger import Ledger                                   # noqa: E402
from src.engine.records import PATHS, EngineError, Event, TurnCommit   # noqa: E402

FAILS = []
TMP = tempfile.mkdtemp(prefix="swe_recordrole_")
CONFIG = {"catalog_version": 1}


def check(name, ok, detail=""):
    detail = str(detail)[:300].encode("ascii", "backslashreplace").decode("ascii")
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        FAILS.append(name)


def _p(*parts):
    return os.path.join(TMP, *parts)


def _code(fn):
    try:
        fn()
    except EngineError as exc:
        return exc.code
    except sqlite3.Error as exc:
        return "sqlite3.%s: %s" % (type(exc).__name__, str(exc)[:80])
    return None


def _counts(path):
    con = sqlite3.connect(path)
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' "
                                            "AND name NOT LIKE 'sqlite_%' AND name <> 'db_role'")]
        return {t: con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in tables}
    finally:
        con.close()


def _outcome(fn):
    """fn() -> its result, or {"refused": the code} - so a check prints FAIL where a raise would end the suite (any raise:
    a TypeError from a path form was the regression review 2 found)."""
    try:
        return fn()
    except Exception as exc:
        return {"refused": getattr(exc, "code", None) or "%s: %s" % (type(exc).__name__, str(exc)[:80])}


def _sql(path, sql):
    """One statement on a raw sqlite3 connection - the stranger's script -> None, or the refusal's text."""
    con = sqlite3.connect(path)
    try:
        con.execute(sql)
        con.commit()
        return None
    except sqlite3.Error as exc:
        return "%s: %s" % (type(exc).__name__, exc)
    finally:
        con.close()


_ROLE_GUARDS = {"db_role%s%s" % (guards.LOCK, s) for s in ("del", "upd", "ins")}


def _role_guards(path):
    """The role row's guard names a file carries, read raw - no engine open, which would re-install them."""
    con = sqlite3.connect(path)
    try:
        return {str(n) for (n,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'trigger' "
                                                "AND tbl_name = 'db_role'")}
    finally:
        con.close()


def _turn(n):
    return TurnCommit(run_id="r1", turn=n, actor="maren", thought="t%d" % n, action="a%d" % n,
                      tags={"type": "mundane"}, affect={p: 0.5 for p in PATHS}, events=[])


def _plain_tables(con):
    """Every table the lock should close, read straight from sqlite_master - not through guards.lock_tables."""
    return [n for n, sql in con.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'")
            if n != "db_role" and not n.startswith("sqlite_") and not sql.upper().startswith("CREATE VIRTUAL")]


def _book(name, runs=("r1",)):
    """A scratch book database with a run or two, opened and closed through the engine."""
    path = _p(name)
    led = Ledger(path)
    for r in runs:
        led.create_run(r, CONFIG)
    led.con.close()
    return path


def roles():
    print("[1] every file opens OPEN and takes writes as today; a v34 file migrates to OPEN")
    path = _book("open.db")
    check("a-fresh-file-is-open", db.role_of(path) == {"role": "open", "head": "", "parent": ""}, db.role_of(path))
    led = Ledger(path)
    check("an-open-file-takes-a-run", _code(lambda: led.create_run("r2", CONFIG)) is None)
    led.con.close()
    con = db.connect(path)
    locks = [n for n in guards.installed(con) if guards.LOCK in n]
    check("the-record-lock-is-installed-on-every-table-but-the-role-row",
          len(locks) == 3 * len(guards.lock_tables(con)) + 3 and "db_role" not in guards.lock_tables(con)
          and "events" in guards.lock_tables(con), (len(locks), len(guards.lock_tables(con))))
    tables = _plain_tables(con)
    on = {(str(t), str(n)) for n, t in con.execute("SELECT name, tbl_name FROM sqlite_master WHERE type = 'trigger'")}
    missing = [t + guards.LOCK + s for t in tables for s in ("ins", "upd", "del") if (t, t + guards.LOCK + s) not in on]
    missing += ["db_role%s%s" % (guards.LOCK, s) for s in ("del", "upd", "ins") if ("db_role", "db_role%s%s"
                % (guards.LOCK, s)) not in on]
    check("every-table-sqlite_master-lists-carries-its-three-locks-and-the-role-row-its-three-(counted-without-the-"
          "code-under-test)", not missing and len(tables) >= 30, (len(tables), missing[:4]))
    con.close()
    old = _book("v34.db")
    raw = sqlite3.connect(old)
    for name in list(guards.installed(raw)):
        raw.execute("DROP TRIGGER IF EXISTS %s" % name)
    raw.execute("DROP TABLE db_role")
    raw.execute("PRAGMA user_version = 34")
    raw.commit()
    raw.close()
    check("a-v34-file-reads-open-before-it-is-migrated", db.role_of(old)["role"] == "open")
    found = integrity.sweep(sqlite3.connect(old))
    lock_findings = [f for f in found if f["kind"] == "RECORD-LOCK-MISSING"]
    check("integrity-reports-the-missing-lock-ONCE,-amber", len(lock_findings) == 1
          and lock_findings[0]["tier"] == "amber", [f["kind"] for f in found][:12])
    con = db.connect(old)
    check("...and-the-v34-file-migrates-to-v35,-open,-locked", con.execute("PRAGMA user_version").fetchone()[0] == 35
          and db.role_of(old)["role"] == "open"
          and any(guards.LOCK in n for n in guards.installed(con)))
    con.close()


def the_lock():
    print("\n[2] a RECORD refuses every write - the engine's writers and a stranger's sqlite3 alike")
    path = _book("rec.db")
    check("adopt-makes-it-a-record", db.adopt(path, "h1") == {"role": "record", "head": "h1", "parent": ""},
          db.role_of(path))
    led = Ledger(path)
    check("a-run-creation-is-DB_IS_RECORD", _code(lambda: led.create_run("r2", CONFIG)) == "DB_IS_RECORD",
          _code(lambda: led.create_run("r3", CONFIG)))
    check("a-guarded-writer-is-DB_IS_RECORD",
          _code(lambda: claims.record(led.con, "r1", 1, "maren", "the millhouse wheel is cracked")) == "DB_IS_RECORD")
    led.con.close()
    raw = sqlite3.connect(path)
    for what, sql in (("INSERT", "INSERT INTO runs (run_id, created_at, config) VALUES ('rx', 'now', '{}')"),
                      ("UPDATE", "UPDATE runs SET status = 'parked' WHERE run_id = 'r1'"),
                      ("DELETE", "DELETE FROM runs WHERE run_id = 'r1'")):     # a row that exists: a trigger
                                                                                # fires per row, so an empty
                                                                                # table proves nothing
        try:
            raw.execute(sql)
            got = "allowed"
        except sqlite3.IntegrityError as exc:
            got = str(exc)
        check("a-raw-%s-is-refused-by-the-lock" % what, got.startswith("DB_IS_RECORD:") and guards.LOCK_MARK in got,
              got)
    raw.rollback()
    raw.close()
    check("nothing-was-written", _counts(path)["runs"] == 1, _counts(path))
    tb = _p("turns.db")
    led = Ledger(tb)
    led.create_run("r1", CONFIG)
    led.register_character("r1", "maren", {"name": "Maren"}, {"temperament": "authored"})
    led.append_turn(_turn(0))                                   # a turn lands while the book is open
    led.con.close()
    db.adopt(tb, "t1")
    led = Ledger(tb)
    check("a-turn-commit-(the-drivers'-writer)-on-a-record-is-DB_IS_RECORD",
          _code(lambda: led.append_turn(_turn(1))) == "DB_IS_RECORD" and _counts(tb)["turns"] == 1, _counts(tb)["turns"])
    led.con.close()
    con = db.connect(path)                                     # a reader: DDL on open is allowed, and a fold writes nothing
    led = Ledger(path)
    folded = led.fold("r1")
    check("a-reader-still-opens-and-folds-a-record", folded is not None and db.role_of(path)["role"] == "record")
    led.con.close()
    con.close()
    check("adopting-a-record-again-is-DB_ROLE_WRONG", _code(lambda: db.adopt(path, "h2")) == "DB_ROLE_WRONG")
    check("an-empty-lineage-id-is-DB_ROLE_WRONG", _code(lambda: db.adopt(_book("blank.db"), " ")) == "DB_ROLE_WRONG")


def drafts_and_promote():
    print("\n[3] a DRAFT takes writes; promote lands it whole on the record and keeps the old record")
    rec = _book("book.db")
    db.adopt(rec, "h1")
    d1 = _p("drafts", "d1.db")
    got = _outcome(lambda: db.copy_to(rec, d1, "draft", "d1"))
    check("copy_to-makes-a-draft-of-the-record", got == {"role": "draft", "head": "d1", "parent": "h1"}, got)
    check("copy_to-refuses-an-existing-target", _code(lambda: db.copy_to(rec, d1, "draft", "d9"))
          == "DB_COPY_TARGET_EXISTS")
    check("copy_to-makes-only-drafts-and-history", _code(lambda: db.copy_to(rec, _p("x.db"), "record", "x"))
          == "DB_ROLE_WRONG")
    led = Ledger(d1)
    check("the-draft-takes-a-run", _code(lambda: led.create_run("r2", CONFIG)) is None)
    led.con.close()
    d2 = _p("drafts", "d2.db")
    db.copy_to(rec, d2, "draft", "d2")                          # a second take from the same head
    want = _counts(d1)
    reader = sqlite3.connect(rec)                  # an idle reader holds the file open, so closing the promote's own
    reader.execute("SELECT COUNT(*) FROM runs").fetchone()     # connection does not checkpoint the WAL for it - only
    # promote's explicit checkpoint does (measured: without it the WAL held the whole copy; "SELECT 1" never opens the
    # file, so a reader that ran only that proved nothing - the first form of this check stayed green without it)
    got = _outcome(lambda: db.promote(d1, rec, _p("history", "h1.db")))
    check("promote-returns-the-new-lineage", got.get("head") == "d1" and got.get("parent") == "h1", got)
    check("the-record-now-holds-exactly-the-draft", _counts(rec) == want, (_counts(rec), want))
    check("...in-role-record-with-the-draft's-head", db.role_of(rec) == {"role": "record", "head": "d1",
                                                                      "parent": "h1"}, db.role_of(rec))
    kept = _p("history", "h1.db")
    check("the-old-record-is-kept-as-history", os.path.isfile(kept) and db.role_of(kept) == {"role": "history",
          "head": "h1", "parent": ""} and _counts(kept)["runs"] == 1, os.path.isfile(kept))
    wal = rec + "-wal"
    check("the-WAL-is-emptied", not os.path.exists(wal) or os.path.getsize(wal) == 0,
          os.path.getsize(wal) if os.path.exists(wal) else None)
    reader.close()
    check("the-promoted-record-is-locked", _code(lambda: Ledger(rec).create_run("r9", CONFIG)) == "DB_IS_RECORD")
    before = _counts(rec)
    check("the-other-take-is-now-DB_PROMOTE_STALE", _code(lambda: db.promote(d2, rec, _p("history", "x1.db")))
          == "DB_PROMOTE_STALE" and _counts(rec) == before and not os.path.exists(_p("history", "x1.db")))
    check("a-record-onto-a-record-is-DB_ROLE_WRONG", _code(lambda: db.promote(rec, rec, _p("history", "x2.db")))
          == "DB_ROLE_WRONG")
    openfile = _book("unadopted.db")
    d3 = _p("drafts", "d3.db")
    db.copy_to(openfile, d3, "draft", "d3")
    check("a-draft-onto-an-unadopted-book-is-DB_ROLE_WRONG",
          _code(lambda: db.promote(d3, openfile, _p("history", "x3.db"))) == "DB_ROLE_WRONG")
    d4 = _p("drafts", "d4.db")
    db.copy_to(rec, d4, "draft", "d4")
    check("an-existing-history-path-is-refused-before-anything-moves",
          _code(lambda: db.promote(d4, rec, _p("history", "h1.db"))) == "DB_COPY_TARGET_EXISTS"
          and db.role_of(rec)["head"] == "d1")
    return rec


def busy_and_abort(rec):
    print("\n[4] a held lock is DB_BUSY_TIMEOUT within the timeout - never a hang; an aborted copy leaves the record whole")
    d5 = _p("drafts", "d5.db")
    db.copy_to(rec, d5, "draft", "d5")
    holder = sqlite3.connect(rec, timeout=5)
    holder.execute("BEGIN IMMEDIATE")
    real = db.BUSY_TIMEOUT_SECONDS
    db.BUSY_TIMEOUT_SECONDS = 0.5
    box = {}

    def go():
        box["code"] = _code(lambda: db.promote(d5, rec, _p("history", "busy.db")))
    t0 = time.time()
    th = threading.Thread(target=go, daemon=True)
    th.start()
    th.join(20)
    db.BUSY_TIMEOUT_SECONDS = real
    holder.rollback()
    holder.close()
    check("promote-under-a-held-lock-is-DB_BUSY_TIMEOUT-not-a-hang", not th.is_alive()
          and box.get("code") == "DB_BUSY_TIMEOUT", (th.is_alive(), box, round(time.time() - t0, 1)))
    check("...and-moved-nothing", db.role_of(rec)["head"] == "d1" and not os.path.exists(_p("history", "busy.db")))

    # the bound itself, past the probe: sqlite's backup would spin; the progress callback must give up
    made = sqlite3.connect(_p("target.db"))
    made.execute("CREATE TABLE t (x)")
    made.commit()
    made.close()
    holder = sqlite3.connect(_p("target.db"), timeout=5)
    holder.execute("BEGIN IMMEDIATE")
    db.BUSY_TIMEOUT_SECONDS = 0.5
    box.clear()

    def copy():                                    # sqlite3 objects belong to the thread that made them
        src = sqlite3.connect(d5)
        dst = sqlite3.connect(_p("target.db"), timeout=db._BACKUP_SLEEP)     # as promote and copy_to open it
        t = time.monotonic()
        try:
            box["code"] = _code(lambda: db._bounded_copy(src, dst, "test"))
        finally:
            box["took"] = time.monotonic() - t
            src.close()
            dst.close()
    th = threading.Thread(target=copy, daemon=True)
    th.start()
    th.join(20)
    db.BUSY_TIMEOUT_SECONDS = real
    holder.rollback()
    holder.close()
    check("the-bounded-copy-gives-up-past-the-timeout-(the-raw-backup-would-spin)", not th.is_alive()
          and box.get("code") == "DB_BUSY_TIMEOUT", (th.is_alive(), box))
    check("...within-the-timeout-and-a-second-(review-1:-10.6s-at-a-5s-setting)", box.get("took", 99) < 0.5 + 1.0,
          box.get("took"))

    # past the probe INSIDE promote: a writer that takes the lock between the probe and the landing meets the same
    # bound, and the record is left as it was (the interleaving forced, not hoped for)
    d6 = _p("drafts", "d6.db")
    db.copy_to(rec, d6, "draft", "d6")
    before, head, real_probe = _counts(rec), db.role_of(rec)["head"], db._probe_lock
    box.clear()

    def late_writer():
        def probe(path, doing):
            real_probe(path, doing)
            box["holder"] = sqlite3.connect(path, timeout=5)
            box["holder"].execute("BEGIN IMMEDIATE")
        db._probe_lock = probe
        t = time.monotonic()
        try:
            box["code"] = _code(lambda: db.promote(d6, rec, _p("history", "late.db")))
        finally:
            box["took"] = time.monotonic() - t
            db._probe_lock = real_probe
            if "holder" in box:
                box["holder"].rollback()
                box["holder"].close()
    db.BUSY_TIMEOUT_SECONDS = 0.5
    th = threading.Thread(target=late_writer, daemon=True)
    th.start()
    th.join(20)
    db.BUSY_TIMEOUT_SECONDS = real
    check("a-lock-taken-after-the-probe-is-DB_BUSY_TIMEOUT-within-the-bound", not th.is_alive()
          and box.get("code") == "DB_BUSY_TIMEOUT" and box.get("took", 99) < 0.5 + 1.0,
          (th.is_alive(), box.get("code"), box.get("took")))
    check("...and-the-record-is-as-it-was", _counts(rec) == before and db.role_of(rec)["head"] == head)

    # the property promote rests on: a backup aborted part-way leaves its destination exactly as it was
    before = _counts(rec)
    big = _p("drafts", "big.db")
    db.copy_to(rec, big, "draft", "big")
    con = sqlite3.connect(big)
    con.executemany("INSERT INTO llm_calls (run_id, turn, purpose, model, tokens_in, tokens_out) "
                    "VALUES ('r1', ?, 'act', 'stub', 1, 1)", [(i,) for i in range(4000)])
    con.commit()
    steps = []

    def abort(_status, _remaining, _total):
        steps.append(1)
        if len(steps) == 2:
            raise RuntimeError("aborted part-way")
    target = sqlite3.connect(rec)
    try:
        con.backup(target, pages=1, progress=abort)
        aborted = False
    except RuntimeError:
        aborted = True
    target.close()
    con.close()
    ok = sqlite3.connect(rec).execute("PRAGMA integrity_check").fetchone()[0]
    check("an-aborted-copy-leaves-the-record-whole", aborted and _counts(rec) == before and ok == "ok",
          (aborted, ok))


def rewind(rec):
    print("\n[5] restore makes a history copy the record again and keeps what it removed")
    before_promote = _counts(_p("history", "h1.db"))
    now = _counts(rec)
    got = db.restore(_p("history", "h1.db"), rec, _p("history", "kept-d1.db"))
    check("restore-returns-the-restored-lineage", got["head"] == "h1" and got["kept"].endswith("kept-d1.db"), got)
    check("the-record-holds-the-history-copy's-content", _counts(rec) == before_promote,
          (_counts(rec), before_promote))
    check("...in-role-record-with-its-head", db.role_of(rec) == {"role": "record", "head": "h1", "parent": ""},
          db.role_of(rec))
    check("the-removed-state-is-kept", _counts(_p("history", "kept-d1.db")) == now
          and db.role_of(_p("history", "kept-d1.db"))["head"] == "d1")
    check("restore-refuses-a-non-history-source", _code(lambda: db.restore(rec, rec, _p("history", "k2.db")))
          == "DB_ROLE_WRONG")
    check("restore-refuses-an-existing-keep-path", _code(lambda: db.restore(_p("history", "h1.db"), rec,
          _p("history", "kept-d1.db"))) == "DB_COPY_TARGET_EXISTS")


def the_role_row():
    print("\n[6] the role row cannot switch the lock off; a history copy is locked; a lineage id is never reused")
    rec = _book("r6.db")
    db.adopt(rec, "a1")
    hist = _p("history", "a1.db")
    check("a-history-copy-keeps-the-record's-own-lineage", db.copy_to(rec, hist, "history")
          == {"role": "history", "head": "a1", "parent": ""}, db.role_of(hist))
    got = _sql(hist, "INSERT INTO runs (run_id, created_at, config) VALUES ('rx', 'now', '{}')")
    check("a-history-copy-refuses-a-raw-INSERT", got is not None and "DB_IS_RECORD" in got and guards.LOCK_MARK in got,
          got)
    led = Ledger(hist)
    check("...and-a-run-creation-(DB_IS_RECORD)", _code(lambda: led.create_run("r2", CONFIG)) == "DB_IS_RECORD")
    led.con.close()
    for where, path in (("record", rec), ("history-copy", hist)):
        for what, sql in (("UPDATE", "UPDATE db_role SET role = 'open' WHERE id = 1"), ("DELETE", "DELETE FROM db_role")):
            got = _sql(path, sql)
            check("a-%s's-role-row-refuses-a-raw-%s" % (where, what), got is not None and "DB_IS_RECORD" in got, got)
    check("...and-both-are-still-what-they-were", db.role_of(rec)["role"] == "record"
          and db.role_of(hist)["role"] == "history")
    for where, path in (("record", rec), ("history-copy", hist)):
        for form in ("REPLACE", "INSERT OR REPLACE"):         # a raw connection: recursive_triggers off, so no
            got = _sql(path, "%s INTO db_role (id, role, head, parent) VALUES (1, 'open', 'a1', '')" % form)
            check("a-%s's-role-row-refuses-a-raw-%s" % (where, form.replace(" ", "-")),   # DELETE trigger fires
                  got is not None and "DB_IS_RECORD" in got and db.role_of(path)["role"] != "open", got)
    openfile = _book("o6.db")
    got = _sql(openfile, "DELETE FROM db_role")
    check("an-open-file's-role-row-is-never-deleted-either", got is not None and "DB_IS_RECORD" in got, got)
    d = _p("drafts", "e1.db")
    db.copy_to(rec, d, "draft", "e1")
    check("a-copy-carries-the-role-row's-three-guards-before-anything-opens-it", _role_guards(d) == _ROLE_GUARDS,
          _role_guards(d))
    got = _sql(d, "UPDATE db_role SET role = 'history', head = 'a1', parent = ''")
    check("a-draft-cannot-be-relabelled-a-history-copy", got is not None and "DB_IS_RECORD" in got
          and db.role_of(d)["role"] == "draft", got)
    got = _sql(openfile, "UPDATE db_role SET role = 'history', head = 'a1'")
    check("an-open-file-cannot-be-relabelled-a-history-copy", got is not None and "DB_IS_RECORD" in got
          and db.role_of(openfile)["role"] == "open", got)
    for where, path, role in (("draft", d, "draft"), ("open-file", openfile, "open")):     # review 3: REPLACE was
        for form in ("REPLACE", "INSERT OR REPLACE"):                                    # pinned on record/history only
            got = _sql(path, "%s INTO db_role (id, role, head, parent) VALUES (1, 'history', 'a1', '')" % form)
            check("a-%s's-role-row-refuses-a-raw-%s" % (where, form.replace(" ", "-")),
                  got is not None and "DB_IS_RECORD" in got and db.role_of(path)["role"] == role, got)
    got = _sql(d, "UPDATE db_role SET role = 'record', head = 'a1', parent = ''")
    check("a-draft-cannot-be-relabelled-a-record", got is not None and "DB_IS_RECORD" in got
          and db.role_of(d)["role"] == "draft", got)
    got = _sql(openfile, "UPDATE db_role SET role = 'draft', head = 'z9'")
    check("an-open-file-cannot-be-relabelled-a-draft", got is not None and "DB_IS_RECORD" in got
          and db.role_of(openfile)["role"] == "open", got)
    check("a-history-copy-of-a-draft-is-DB_ROLE_WRONG", _code(lambda: db.copy_to(d, _p("history", "e1.db"), "history"))
          == "DB_ROLE_WRONG" and not os.path.exists(_p("history", "e1.db")))
    check("a-history-copy-of-an-open-book-is-DB_ROLE_WRONG",
          _code(lambda: db.copy_to(openfile, _p("history", "o6.db"), "history")) == "DB_ROLE_WRONG")
    check("a-draft-under-its-source's-own-lineage-id-is-DB_ROLE_WRONG",
          _code(lambda: db.copy_to(rec, _p("drafts", "same.db"), "draft", "a1")) == "DB_ROLE_WRONG"
          and not os.path.exists(_p("drafts", "same.db")))
    twin = _p("drafts", "e1-twin.db")
    db.copy_to(rec, twin, "draft", "e1")           # the same new id twice is legal until one of them lands
    db.promote(d, rec, _p("history", "a1-before-e1.db"))
    check("a-promoted-record-carries-the-role-row's-three-guards-before-anything-opens-it",
          _role_guards(rec) == _ROLE_GUARDS, _role_guards(rec))
    before = _counts(rec)
    check("a-draft-reusing-the-id-that-landed-is-DB_ROLE_WRONG",
          _code(lambda: db.promote(twin, rec, _p("history", "x6.db"))) == "DB_ROLE_WRONG" and _counts(rec) == before
          and not os.path.exists(_p("history", "x6.db")))
    check("restore-onto-an-open-file-is-DB_ROLE_WRONG",
          _code(lambda: db.restore(hist, openfile, _p("history", "k6.db"))) == "DB_ROLE_WRONG"
          and not os.path.exists(_p("history", "k6.db")))
    newer = _p("history", "newer.db")
    db.copy_to(rec, newer, "history")
    raw = sqlite3.connect(newer)
    raw.execute("PRAGMA user_version = %d" % (db.SCHEMA_VERSION + 1))       # a newer engine's copy (a pragma, not DML)
    raw.commit()
    raw.close()
    check("restore-of-a-newer-engine's-copy-is-DB_SCHEMA_TOO_NEW-and-keeps-nothing",
          _code(lambda: db.restore(newer, rec, _p("history", "k7.db"))) == "DB_SCHEMA_TOO_NEW"
          and not os.path.exists(_p("history", "k7.db")) and db.role_of(rec)["head"] == "e1")
    open(_p("drafts", "side.db-wal"), "w").close()
    check("a-target-whose-WAL-file-exists-is-DB_COPY_TARGET_EXISTS",
          _code(lambda: db.copy_to(rec, _p("drafts", "side.db"), "draft", "s1")) == "DB_COPY_TARGET_EXISTS")
    led = Ledger(rec)
    check("a-world-event-on-a-record-(critic-correct,-the-keeper's-rulings)-is-DB_IS_RECORD",
          _code(lambda: world_events.append(led, "r1", 1, [Event(type="correction", payload={"note": "x"})]))
          == "DB_IS_RECORD")
    led.con.close()

    # two promotes, the second landing between the first's check and its copy: the kept copy is labelled from what the
    # record actually was, so the first sees the other landed and refuses - the interleaving forced by the probe
    ra, rb = _p("drafts", "fa.db"), _p("drafts", "fb.db")
    db.copy_to(rec, ra, "draft", "fa")
    db.copy_to(rec, rb, "draft", "fb")
    led = Ledger(rb)
    led.create_run("rb-only", CONFIG)
    led.con.close()
    want, real_probe = _counts(rb), db._probe_lock

    def probe(path, doing):
        db._probe_lock = real_probe
        db.promote(rb, rec, _p("history", "e1-before-fb.db"))
        real_probe(path, doing)
    db._probe_lock = probe
    try:
        code = _code(lambda: db.promote(ra, rec, _p("history", "raced.db")))
    finally:
        db._probe_lock = real_probe
    check("a-promote-overtaken-after-its-check-is-DB_PROMOTE_STALE", code == "DB_PROMOTE_STALE", code)
    check("...the-record-keeps-the-promote-that-won", db.role_of(rec)["head"] == "fb" and _counts(rec) == want,
          db.role_of(rec))
    check("...and-the-kept-copy-names-what-it-holds", db.role_of(_p("history", "raced.db"))
          == {"role": "history", "head": "fb", "parent": "e1"}, db.role_of(_p("history", "raced.db")))

    pd, ph = pathlib.Path(_p("drafts", "p1.db")), pathlib.Path(_p("history", "fb-before-p1.db"))
    got = _outcome(lambda: db.copy_to(rec, pd, "draft", "p1"))
    check("copy_to-takes-a-pathlib-target", got == {"role": "draft", "head": "p1", "parent": "fb"}, got)
    got = _outcome(lambda: db.promote(pd, rec, ph))
    check("...and-promote-a-pathlib-history-path", got.get("head") == "p1" and os.path.isfile(ph), got)
    kb = _book("k6.db")
    led = Ledger(kb)
    uid = claims.record(led.con, "r1", 1, "maren", "the millhouse wheel is cracked")
    led.con.close()
    db.adopt(kb, "k1")
    led = Ledger(kb)
    check("a-keeper-ruling-(claims.resolve,-keeper---rule---rulings)-on-a-record-is-DB_IS_RECORD",
          _code(lambda: claims.resolve(led.con, "r1", uid, 2, claims.TIERS[-1], "ruled")) == "DB_IS_RECORD")
    led.con.close()
    con = sqlite3.connect(openfile)
    check("the-role-guard-is-lifted-only-on-an-in-memory-copy,-never-a-file",
          _code(lambda: db._write_role(con, "record", "x1", "", "test", in_memory=True)) == "DB_ROLE_WRONG"
          and db.role_of(openfile)["role"] == "open")
    con.close()
    by_hand = _book("hand.db")
    got = _sql(by_hand, "UPDATE db_role SET role = 'record', head = 'z1'")
    check("...the-one-role-change-left-on-disk-is-open-to-record-(adopt;-a-forged-one-is-draft-flow's-lineage)",
          got is None and db.role_of(by_hand)["role"] == "record", got)


def tampering():
    print("\n[7] a removed role row fails closed; a stranger's trigger on a lock's name refuses the book; odd tables lock")
    path = _book("t7.db")
    raw = sqlite3.connect(path)
    raw.execute('DROP TRIGGER "db_role%sdel"' % guards.LOCK)           # DDL: outside the lock, declared
    raw.execute("DELETE FROM db_role")
    raw.commit()
    raw.close()
    check("a-file-whose-role-row-was-removed-reads-as-a-record", db.role_of(path)["role"] == "record", db.role_of(path))
    got = _sql(path, "INSERT INTO runs (run_id, created_at, config) VALUES ('rx', 'now', '{}')")
    check("...its-lock-holds", got is not None and "DB_IS_RECORD" in got, got)
    check("...adopting-it-is-DB_ROLE_WRONG", _code(lambda: db.adopt(path, "t1")) == "DB_ROLE_WRONG")
    check("...and-a-copy-that-cannot-set-its-role-is-DB_ROLE_WRONG-and-writes-no-file",
          _code(lambda: db.copy_to(path, _p("drafts", "t7.db"), "draft", "t2")) == "DB_ROLE_WRONG"
          and not os.path.exists(_p("drafts", "t7.db")))
    gone = _book("t8.db")
    got = _sql(gone, "DROP TABLE db_role")
    check("a-v35-file-whose-role-TABLE-was-dropped-reads-as-a-record", got is None
          and db.role_of(gone)["role"] == "record", (got, db.role_of(gone)))
    code = _code(lambda: db.connect(gone).close())
    got = _sql(gone, "INSERT INTO runs (run_id, created_at, config) VALUES ('rx', 'now', '{}')")
    check("...still-opens-for-a-reader-and-refuses-every-write-(sqlite's-own-words)", code is None
          and got is not None and "db_role" in got, (code, got))
    check("...and-a-copy-of-it-is-DB_ROLE_WRONG-and-writes-no-file",
          _code(lambda: db.copy_to(gone, _p("drafts", "t8.db"), "draft", "t3")) == "DB_ROLE_WRONG"
          and not os.path.exists(_p("drafts", "t8.db")))
    step, intact = _book("t12.db"), _book("t13.db")
    raw = sqlite3.connect(step)
    raw.execute('DROP TRIGGER "db_role%sdel"' % guards.LOCK)
    raw.execute("DELETE FROM db_role")
    raw.commit()
    raw.close()
    db.adopt(intact, "i1")
    real = db.SCHEMA_VERSION
    db.SCHEMA_VERSION = real + 1                        # the next version step, simulated: the schema runs again
    try:
        codes = [_code(lambda: db.connect(step).close()), _code(lambda: db.connect(intact).close())]
    finally:
        db.SCHEMA_VERSION = real
    got = [_sql(f, "INSERT INTO runs (run_id, created_at, config) VALUES ('rx', 'now', '{}')") for f in (step, intact)]
    check("through-a-version-step-a-removed-role-row-stays-removed-and-locks,-an-intact-record-stays-locked",
          codes == [None, None] and db.role_of(step)["role"] == "record" and db.role_of(intact)["role"] == "record"
          and all(g and "DB_IS_RECORD" in g for g in got), (codes, got, db.role_of(step)))

    taken = _book("t9.db")
    name = "runs%sins" % guards.LOCK
    raw = sqlite3.connect(taken)
    raw.execute('DROP TRIGGER "%s"' % name)
    raw.execute('CREATE TRIGGER "%s" BEFORE INSERT ON events BEGIN SELECT 1; END' % name)
    raw.commit()
    raw.close()
    check("a-stranger's-trigger-holding-a-lock's-name-is-DB_GUARD_NAME_TAKEN",
          _code(lambda: db.connect(taken).close()) == "DB_GUARD_NAME_TAKEN")

    one = _book("t10.db")
    raw = sqlite3.connect(one)
    raw.execute('DROP TRIGGER "events%supd"' % guards.LOCK)
    raw.commit()
    of = 3 * len(_plain_tables(raw)) + 3
    found = [f for f in integrity.sweep(raw) if f["kind"] == "RECORD-LOCK-MISSING"]
    raw.close()
    check("one-missing-lock-is-one-finding-that-counts-it", len(found) == 1
          and "on 1 trigger(s) of %d;" % of in found[0]["detail"], (of, found))

    odd = _book("t11.db")
    raw = sqlite3.connect(odd)
    raw.execute('CREATE TABLE "odd ""quoted"" name" (x)')
    raw.execute('CREATE TABLE "weird-name" (x)')
    raw.execute("CREATE VIRTUAL TABLE notes_fts USING fts5(body)")
    raw.commit()
    raw.close()
    check("odd-table-names-and-a-virtual-table-open", _code(lambda: db.connect(odd).close()) is None,
          _code(lambda: db.connect(odd).close()))
    raw = sqlite3.connect(odd)
    on_fts = [n for n, t in raw.execute("SELECT name, tbl_name FROM sqlite_master WHERE type = 'trigger'")
              if str(t).startswith("notes_fts")]
    exact = guards.lock_tables(raw)
    older = guards.lock_tables(_OlderSqlite(raw))
    raw.close()
    check("a-virtual-table-and-its-shadow-tables-carry-no-lock", on_fts == [] and "weird-name" in exact
          and not any(t.startswith("notes_fts") for t in exact), (on_fts, exact))
    check("...and-an-older-sqlite's-name-test-closes-the-same-tables", older == exact, (older, exact))
    # a lock on FTS5's shadow tables killed the PROCESS on the next write into it, on an open file where the lock does
    # not even fire (measured 2026-09-26) - so the write runs in a child, and a crash is a FAIL, not the suite's end
    child = subprocess.run([sys.executable, "-c", "import sqlite3, sys; c = sqlite3.connect(sys.argv[1]); "
                            "c.execute(\"INSERT INTO notes_fts (body) VALUES ('the millhouse wheel')\"); c.commit(); "
                            "print(c.execute('SELECT COUNT(*) FROM notes_fts').fetchone()[0])", odd],
                           capture_output=True, text=True, timeout=120)
    check("an-open-file's-FTS5-table-still-takes-a-write", child.returncode == 0 and child.stdout.strip() == "1",
          (child.returncode, child.stdout[-80:], child.stderr[-200:]))
    db.adopt(odd, "o1")
    for label, table in (("a-quoted-name", '"odd ""quoted"" name"'), ("a-dashed-name", '"weird-name"')):
        got = _sql(odd, "INSERT INTO %s (x) VALUES (1)" % table)
        check("a-raw-INSERT-into-%s-on-a-record-is-refused" % label, got is not None and "DB_IS_RECORD" in got, got)


class _OlderSqlite:
    """A connection whose SQLite predates `PRAGMA table_list` (3.37), which ignores an unknown pragma: no rows."""

    def __init__(self, con):
        self.con = con

    def execute(self, sql, *args):
        return iter(()) if sql.strip().upper() == "PRAGMA TABLE_LIST" else self.con.execute(sql, *args)


class _KilledAfterRename:
    """A connection that dies after `_rebuild`'s first script - the rename - as a killed process would."""

    def __init__(self, con):
        self.con, self.scripts = con, 0

    def execute(self, *args):
        return self.con.execute(*args)

    def executescript(self, sql):
        self.scripts += 1
        if self.scripts > 1:
            raise RuntimeError("killed after the rename")
        return self.con.executescript(sql)


def interrupted_rebuild():
    print("\n[8] a rebuild killed after its rename leaves no guard or lock name on the old table; the next open finishes")
    path = _book("rb.db")
    raw = sqlite3.connect(path)
    for (n,) in raw.execute("SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'wound_minted'"
                            ).fetchall():
        raw.execute('DROP TRIGGER "%s"' % n)
    raw.executescript("DROP TABLE wound_minted; CREATE TABLE wound_minted (mint_id INTEGER PRIMARY KEY, run_id TEXT, "
                      "turn INTEGER, char_id TEXT, wound_id TEXT, concept TEXT, path TEXT, intensity REAL, source TEXT, "
                      "text TEXT, triggers TEXT, UNIQUE (run_id, char_id, wound_id));")     # v32's shape
    guards.install(raw)                                # its guard and its locks, as a later engine leaves them
    raw.execute("PRAGMA user_version = 34")
    raw.commit()
    with open(db._SCHEMA_PATH, encoding="utf-8") as fh:
        schema = fh.read()
    try:
        db._rebuild(_KilledAfterRename(raw), schema)
        killed = False
    except RuntimeError:
        killed = True
    left = [n for (n,) in raw.execute("SELECT name FROM sqlite_master WHERE type = 'trigger' "
                                      "AND tbl_name = 'wound_minted_v32'")]
    raw.close()
    check("the-kill-left-the-old-table-holding-none-of-its-triggers", killed and left == [], (killed, left))
    code = _code(lambda: db.connect(path).close())
    check("the-next-open-finishes-the-rebuild", code is None, code)
    raw = sqlite3.connect(path)
    shape = raw.execute("SELECT sql FROM sqlite_master WHERE name = 'wound_minted'").fetchone()[0]
    names = {n for (n,) in raw.execute("SELECT name FROM sqlite_master WHERE type = 'trigger' "
                                       "AND tbl_name = 'wound_minted'")}
    aside = raw.execute("SELECT 1 FROM sqlite_master WHERE name = 'wound_minted_v32'").fetchone()
    raw.close()
    want = {"wound_minted" + guards.SUFFIX, "wound_minted_no_update", "wound_minted_no_delete"}
    want |= {"wound_minted%s%s" % (guards.LOCK, s) for s in ("ins", "upd", "del")}
    check("...with-the-new-shape,-its-guard,-locks-and-append-only-triggers,-and-no-old-table",
          "turn" in shape.split("UNIQUE")[-1] and aside is None and want <= names, (sorted(names), shape[-60:]))


def main():
    print("test_record_role.py - a record changes only by promote or restore (gate record-role)\n")
    try:
        roles()
        the_lock()
        rec = drafts_and_promote()
        busy_and_abort(rec)
        rewind(rec)
        the_role_row()
        tampering()
        interrupted_rebuild()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("\n%s: %d failure(s)" % ("OK" if not FAILS else "FAIL", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
