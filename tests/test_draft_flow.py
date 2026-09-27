#!/usr/bin/env python3
"""test_draft_flow.py - a book's approval flow through the real commands: adopt, the writers refused, a draft opened,
written and promoted on the owner's words, takes gone stale, a rejection, a rewind, the lease (gate draft-flow).

The owner, 2026-09-26: "a scene is draft until it's approved and then it's saved into record." Gate record-role put
the rule in the database; this suite drives what uses it - scripts/draft.py over src/engine/drafts.py and
src/engine/lineage.py - and every writer that must now refuse an adopted book's record up front (scene.py, direct.py,
critic --correct, cut --edl, keeper --propose / --rule --rulings), on scratch copies of the invented vault book.
Sections [7] to [12] are the reviews' findings, each on a book of its own.

SUBPROCESSES, as tests/test_driver_main.py: what is tested is that the COMMAND an operator types gives the result.
Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))
from src.engine import books, db, lineage                                # noqa: E402
from src.engine.ledger import Ledger                                     # noqa: E402
from test_vault import _mk_vault                                          # noqa: E402  one fixture, many suites

FAILS = []


def check(name, ok, detail=""):
    detail = str(detail)[-400:].encode("ascii", "backslashreplace").decode("ascii")
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        FAILS.append(name)


def _run(*args, typed=None, env=None):
    """-> (returncode, output). With nothing `typed`, stdin is DEVNULL: direct.py's REPL would otherwise wait on it
    (tests/test_driver_main); with `typed`, those lines are its input."""
    r = subprocess.run([sys.executable] + list(args), capture_output=True, text=True, timeout=300, cwd=REPO,
                       encoding="utf-8", errors="replace", env=env,
                       **({"input": typed} if typed is not None else {"stdin": subprocess.DEVNULL}))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _draft(book, *args, env=None):
    return _run(os.path.join("scripts", "draft.py"), args[0], "--book", book, *args[1:], env=env)


def _turn(book, dbp=None):
    """One chair turn through direct.py's REPL: a circumstance typed, then quit."""
    return _run(os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira", "--stub",
                *(("--db", dbp) if dbp else ()), typed="the lamp gutters and the wind turns\nquit\n")


def _counts(path):
    """Every table's row count but the role row's, read raw."""
    con = sqlite3.connect(path)
    try:
        names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' "
                                           "AND name NOT LIKE 'sqlite_%' AND name <> 'db_role'")]
        return {n: con.execute('SELECT COUNT(*) FROM "%s"' % n).fetchone()[0] for n in names}
    finally:
        con.close()


def _one(path, sql):
    con = sqlite3.connect(path)
    try:
        return con.execute(sql).fetchone()[0]
    finally:
        con.close()


def _text(path):
    """A small file's text, or None when it is not there."""
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _opened(out):
    """The path `draft.py open` printed."""
    return next((l[len("draft: "):].strip() for l in out.splitlines() if l.startswith("draft: ")), None)


def _id(path):
    return os.path.basename(path or "x.db")[:-3]


def _log(book, op=None):
    """The lineage's entries (of one op) - [] when it does not read, so a check fails by name rather than crashing."""
    try:
        return [e for e in lineage.read(book) if op is None or e["op"] == op]
    except Exception:                                 # noqa: BLE001 - a broken reader is a FAIL line, not a crash
        return []


def _kept(book, head):
    """The last `kept` line for a state."""
    return ([e for e in _log(book, "kept") if e["head"] == head] or [{}])[-1]


def _scene_cfg(tmp):
    path = os.path.join(tmp, "lamp_room.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"name": "lamp_room", "at": {"day": 1, "time": "06:00"}, "lasts": 10,
                   "situation": "Mira keeps the lamp through the gale.",
                   "cast": [{"id": "mira", "drive": "keep the lamp lit"}]}, fh)
    return path


def _adopted_book(tmp, name):
    """A fresh fixture book in its own folder, written once, then adopted -> (book, record)."""
    book = _mk_vault(os.path.join(tmp, name))
    _turn(book)
    _draft(book, "adopt")
    return book, books.db_path(book)


def adoption(tmp):
    print("[1] an unadopted book is written as always; adopt makes its database the record")
    book = _mk_vault(tmp)
    rc, out = _turn(book)
    rec = books.db_path(book)
    check("an-unadopted-book-takes-a-turn-as-today", rc == 0 and os.path.isfile(rec) and _counts(rec)["turns"] >= 1, out)
    rc, out = _draft(book, "open")
    check("a-draft-of-an-unadopted-book-is-DRAFT_BOOK_NOT_ADOPTED", rc == 1 and "[DRAFT_BOOK_NOT_ADOPTED]" in out, out)
    live = sqlite3.connect(rec)                      # a run still open on the book: adopting would cost it its next turn
    live.execute("SELECT COUNT(*) FROM runs").fetchone()
    rc, out = _draft(book, "adopt")
    live.close()
    check("adopting-a-book-still-open-in-a-run-is-DRAFT_IN_USE", rc == 1 and "[DRAFT_IN_USE]" in out
          and db.role_of(rec)["role"] == "open", out)
    rc, out = _draft(book, "adopt")
    check("adopt-makes-it-the-record-at-d0", rc == 0 and db.role_of(rec) == {"role": "record", "head": "d0", "parent": ""}
          and [e["head"] for e in _log(book, "adopt")] == ["d0"], out)
    rc, out = _draft(book, "adopt")
    check("adopting-it-again-is-DRAFT_BOOK_ADOPTED", rc == 1 and "[DRAFT_BOOK_ADOPTED]" in out, out)
    stray = os.path.join(tmp, "not a book")
    os.makedirs(stray)
    rc, out = _draft(stray, "adopt")
    check("a-folder-with-no-world/-is-DRAFT_NOT_A_BOOK-and-nothing-is-written-there", rc == 1
          and "[DRAFT_NOT_A_BOOK]" in out and os.listdir(stray) == [], (out, os.listdir(stray)))
    for flow, args in (("open", ("open",)), ("reject", ("reject", "--draft", "d1")),
                       ("promote", ("promote", "--draft", "d1", "--approved", "yes", "--by", "owner")),
                       ("restore", ("restore", "--to", "d0", "--approved", "yes", "--by", "owner"))):
        rc, out = _draft(stray, *args)
        check("...and-so-is-%s,-no-lease-left-behind" % flow, rc == 1 and "[DRAFT_NOT_A_BOOK]" in out
              and os.listdir(stray) == [], (out, os.listdir(stray)))
    fresh = _mk_vault(os.path.join(tmp, "fresh"))
    rc, out = _draft(fresh, "adopt")
    check("a-book-with-no-database-is-DRAFT_RECORD_MISSING-without---new", rc == 1 and "[DRAFT_RECORD_MISSING]" in out
          and "--new" in out, out)
    rc, out = _draft(fresh, "adopt", "--new")
    check("...and-adopt---new-starts-its-record-empty", rc == 0
          and db.role_of(books.db_path(fresh))["role"] == "record", out)
    return book, rec


def refusals(tmp, book, rec):
    print("\n[2] every writer refuses the record BEFORE any work; the readers still read it")
    before = _counts(rec)
    run_id = _one(rec, "SELECT run_id FROM runs")
    rc, out = _turn(book)
    check("direct.py-on-the-record-is-refused-up-front-naming-draft.py-open", rc != 0 and "[DB_IS_RECORD]" in out
          and "is the book's RECORD" in out and "draft.py open --book" in out and _counts(rec) == before, out)
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", _scene_cfg(tmp), "--stub",
                   "--budget", "1", "--no-keeper")
    check("scene.py-on-the-record-is-refused-up-front", rc != 0 and "[DB_IS_RECORD]" in out
          and "is the book's RECORD" in out and "draft.py open --book" in out and _counts(rec) == before, out)
    edl = os.path.join(tmp, "edl.json")
    with open(edl, "w", encoding="utf-8") as fh:
        json.dump([{"ord_no": 1, "kind": "keep", "turns": [0, 0]}], fh)
    props = os.path.join(tmp, "propose.json")
    with open(props, "w", encoding="utf-8") as fh:
        json.dump([], fh)
    for label, args in (("critic.py---correct", ("critic.py", "--run", run_id, "--stub", "--correct")),
                        ("cut.py---edl", ("cut.py", "--run", run_id, "--edl", edl)),
                        ("keeper.py---propose", ("keeper.py", "--run", run_id, "--propose", props)),
                        ("keeper.py---rule---rulings", ("keeper.py", "--run", run_id, "--rule", "--rulings", props))):
        rc, out = _run(os.path.join("scripts", args[0]), "--vault", book, *args[1:])
        check("%s-on-the-record-is-refused-up-front" % label, rc != 0 and "[DB_IS_RECORD]" in out
              and "is the book's RECORD" in out and "draft.py open --book" in out, out)
    for label, args in (("critic.py-review", ("critic.py", "--run", run_id, "--stub")),
                        ("cut.py-view", ("cut.py", "--run", run_id)),
                        ("keeper.py---propose---dry-run", ("keeper.py", "--run", run_id, "--propose", props, "--dry-run")),
                        ("keeper.py---rule---rulings---dry-run",
                         ("keeper.py", "--run", run_id, "--rule", "--rulings", props, "--dry-run"))):
        rc, out = _run(os.path.join("scripts", args[0]), "--vault", book, *args[1:])
        check("...while-%s-still-reads-it" % label, rc == 0 and "DB_IS_RECORD" not in out, out)
    check("...and-nothing-was-written", _counts(rec) == before, (_counts(rec), before))


def promote_flow(tmp, book, rec):
    print("\n[3] open a draft, write it, promote it on the owner's words; its old path is never written again")
    _write(os.path.join(rec + ".directions", "x.mira.json"), "record's")
    rc, out = _draft(book, "open", "--note", "first take")
    d1 = _opened(out)
    check("open-prints-a-draft-the-lineage-minted", rc == 0 and d1 and os.path.isfile(d1)
          and db.role_of(d1) == {"role": "draft", "head": "d1", "parent": "d0"}
          and [e["note"] for e in _log(book, "open")] == ["first take"], out)
    check("...and-a-promote-hint-that-lands-nothing-if-run-as-printed", "--approved \"<the owner's words" in out
          and "--by owner" not in out and ('--book "%s"' % book) in out, out)
    check("...and-copies-the-record's-directions-into-it",
          _text(os.path.join(d1 + ".directions", "x.mira.json")) == "record's")
    _write(os.path.join(d1 + ".directions", "x.mira.json"), "draft's")
    rc, out = _turn(book, d1)
    resume = next((l for l in out.splitlines() if "resume with" in l), "")
    check("the-driver-writes-the-draft", rc == 0 and _counts(d1)["turns"] > _counts(rec)["turns"], out)
    check("...and-its-resume-line-names-the-draft", "--db" in resume and "d1.db" in resume
          and ('--book "%s"' % book) in resume, resume)
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--db", d1, "--scene", _scene_cfg(tmp), "--stub",
                   "--budget", "1", "--no-keeper")
    check("...and-scene.py-writes-it-too-(its-continue-line-naming-the-draft)", rc == 0 and "DB_IS_RECORD" not in out
          and "--db" in next((l for l in out.splitlines() if "continue with" in l), ""), out)
    want = _counts(d1)
    rc, out = _draft(book, "promote", "--draft", "d1", "--by", "owner")
    check("promote-without-the-owner's-words-is-DRAFT_APPROVAL_MISSING", rc == 1 and "[DRAFT_APPROVAL_MISSING]" in out,
          out)
    rc, out = _draft(book, "promote", "--draft", "d1", "--approved", "...", "--by", "owner")
    check("...and-so-is-punctuation-without-a-word", rc == 1 and "[DRAFT_APPROVAL_MISSING]" in out, out)
    rc, out = _draft(book, "promote", "--draft", "d1", "--approved", "<the owner's words, verbatim>", "--by", "owner")
    check("...and-so-is-the-printed-hint's-placeholder", rc == 1 and "[DRAFT_APPROVAL_MISSING]" in out, out)
    rc, out = _draft(book, "promote", "--draft", "d1", "--approved", "Yes, keep it.", "--by", "someone")
    check("...and-an-unknown-approver-is-DRAFT_APPROVER_UNKNOWN", rc == 1 and "[DRAFT_APPROVER_UNKNOWN]" in out, out)
    rc, out = _draft(book, "promote", "--draft", "d1", "--approved", "  Yes, keep it.  ", "--by", "owner")
    hist = os.path.join(book, "runs", "history", "d0.db")
    line, kept = (_log(book, "promote") or [{}])[-1], _kept(book, "d0")
    check("promote-lands-the-draft-whole", rc == 0 and _counts(rec) == want
          and db.role_of(rec) == {"role": "record", "head": "d1", "parent": "d0"}, out)
    check("...keeps-the-old-record-as-history-its-digest-logged-before-the-landing", os.path.isfile(hist)
          and db.role_of(hist)["head"] == "d0" and kept.get("digest") == lineage.digest(hist)
          and _log(book).index(kept) < _log(book).index(line), (kept, line))
    check("...records-the-owner's-words-exactly-as-given-who-and-when", line.get("approved") == "  Yes, keep it.  "
          and kept.get("approved") == "  Yes, keep it.  " and line.get("by") == "owner"
          and line.get("timing") == "after-review", line)
    check("...sets-the-draft-aside-and-swaps-the-directions",
          not os.path.exists(d1) and os.path.isfile(os.path.join(book, "runs", "drafts", "promoted", "d1.db"))
          and _text(os.path.join(rec + ".directions", "x.mira.json")) == "draft's"
          and _text(os.path.join(hist + ".directions", "x.mira.json")) == "record's")
    rc, out = _turn(book, d1)                          # review 1, MAJOR: the old path, from shell history
    check("a-driver-on-a-promoted-draft's-old-path-is-refused-and-creates-no-file", rc != 0
          and "[DRAFT_NOT_FOUND]" in out and "promoted" in out and not os.path.exists(d1), out)
    never = os.path.join(book, "runs", "drafts", "d99.db")
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--db", never, "--scene", _scene_cfg(tmp),
                   "--stub", "--budget", "1", "--no-keeper")
    check("...and-so-is-a-draft-path-never-opened", rc != 0 and "[DRAFT_NOT_FOUND]" in out and not os.path.exists(never),
          out)
    rc, out = _turn(book, os.path.join(book, "runs", "drafts", "promoted", "d1.db"))
    check("...and-a-draft-already-set-aside", rc != 0 and "[DRAFT_NOT_FOUND]" in out, out)
    try:
        Ledger(never, create=False)
        code = None
    except Exception as exc:                           # noqa: BLE001
        code = getattr(exc, "code", type(exc).__name__)
    check("...and-the-drivers'-opener-never-makes-a-file-that-is-not-there", code == "DB_PATH_INVALID"
          and not os.path.exists(never), code)
    run_id, outs = _one(rec, "SELECT run_id FROM runs"), []
    for label, args in (("critic.py-review", ("critic.py", "--run", run_id, "--stub")),
                        ("cut.py-view", ("cut.py", "--run", run_id)), ("narrate.py", ("narrate.py", "--run", run_id)),
                        ("keeper.py---prompt-only", ("keeper.py", "--run", run_id, "--prompt-only"))):
        rc, out = _run(os.path.join("scripts", args[0]), "--vault", book, "--db", d1, *args[1:])
        outs.append(out)
        check("a-reader-on-the-promoted-draft's-old-path-(%s)-makes-no-file" % label, rc != 0 and not os.path.exists(d1),
              out)
    check("...each-refused-in-one-coded-line,-never-a-traceback", all("[DB_PATH_INVALID]" in o and "Traceback" not in o
                                                                     for o in outs), outs)
    other = _mk_vault(os.path.join(tmp, "other"))      # review 3: --vault names another book, never adopted
    rc, out = _run(os.path.join("scripts", "critic.py"), "--vault", other, "--db", d1, "--run", run_id, "--stub")
    rc2, out2 = _run(os.path.join("scripts", "critic.py"), "--vault", other, "--db", d1, "--run", run_id, "--stub",
                     "--correct")
    check("...and-so-do-a-reader-and-a-writer-whose---vault-names-another,-unadopted-book", rc != 0 and rc2 != 0
          and "[DRAFT_NOT_FOUND]" in out2 and not os.path.exists(d1), (out, out2))
    kept_d1 = os.path.join(book, "runs", "drafts", "promoted", "d1.db")
    if os.path.isfile(kept_d1) and not os.path.exists(d1):
        shutil.copy2(kept_d1, d1)                      # a stray at the old path anyway
    rc, out = _draft(book, "reject", "--draft", "d1")
    check("...and-reject-sets-a-stray-aside-under-a-free-name", rc == 0 and not os.path.exists(d1)
          and os.path.isfile(os.path.join(book, "runs", "drafts", "promoted", "d1.2.db")), out)


def takes(tmp, book, rec):
    print("\n[4] takes from one state: the one promoted second is stale; reject sets any draft aside")
    d2, d3 = _opened(_draft(book, "open")[1]), _opened(_draft(book, "open")[1])
    _turn(book, d2)
    _write(os.path.join(d2 + ".directions", "x.mira.json"), "d2's")
    _write(os.path.join(d3 + ".directions", "x.mira.json"), "d3's")
    rc, out = _draft(book, "list")
    check("list-calls-both-takes-live", rc == 0 and "draft d2  from d1  live" in out and "draft d3  from d1  live" in out,
          out)
    check("...and-names-each-history-copy-a-kept-line-logged-plainly", "\nhistory: d0.db\n" in out, out)
    rc, out = _draft(book, "promote", "--draft", "d2", "--approved", "Apply the ruling.", "--by", "partner-relayed",
                     "--in-advance")
    check("a-dictated-change-lands-with-its-timing-and-its-relayed-yes", rc == 0
          and _log(book, "promote")[-1]["timing"] == "in-advance" and _log(book, "promote")[-1]["by"] == "partner-relayed",
          out)
    stale = os.path.join(book, "runs", "drafts", "stale", "d3.db")
    check("...and-the-other-take-from-d1-went-stale-with-its-directions", not os.path.exists(d3) and os.path.isfile(stale)
          and _text(os.path.join(stale + ".directions", "x.mira.json")) == "d3's"
          and [(e["draft"], e["sibling"]) for e in _log(book, "stale")] == [("d3", "d2")], out)
    rc, out = _draft(book, "promote", "--draft", "d3", "--approved", "yes", "--by", "owner")
    check("...which-cannot-be-promoted-(DRAFT_NOT_FOUND,-naming-stale)", rc == 1 and "[DRAFT_NOT_FOUND]" in out
          and "stale" in out, out)
    dk = _opened(_draft(book, "open")[1])
    rc, out = _run("-c", "import os, sqlite3, sys\nc = sqlite3.connect(sys.argv[1])\n"
                         "c.execute(\"INSERT INTO runs (run_id, created_at, config) VALUES ('killed', 'now', '{}')\")\n"
                         "c.commit()\nos._exit(0)\n", dk)    # a writer killed after its commit: the turn is in the WAL
    left = os.path.getsize(dk + "-wal") if os.path.exists(dk + "-wal") else 0
    rc2, out2 = _draft(book, "reject", "--draft", _id(dk), "--why", "killed")
    moved = os.path.join(book, "runs", "drafts", "rejected", os.path.basename(dk))
    check("a-killed-writer's-last-commit-travels-with-the-draft-set-aside", rc == 0 and left > 0 and rc2 == 0
          and os.path.isfile(moved) and _one(moved, "SELECT COUNT(*) FROM runs WHERE run_id = 'killed'") == 1
          and not os.path.exists(dk + "-wal"), (left, out, out2))
    d4 = _opened(_draft(book, "open", "--note", "the other road")[1])
    _write(os.path.join(d4 + ".directions", "x.mira.json"), "d4's")
    rc, out = _draft(book, "list")
    check("list-calls-a-take-from-the-current-state-live", rc == 0 and "draft %s  from d2  live" % _id(d4) in out, out)
    rc, out = _draft(book, "reject", "--draft", _id(d4), "--why", "wrong turn")
    aside = os.path.join(book, "runs", "drafts", "rejected", os.path.basename(d4))
    check("reject-sets-a-draft-aside-with-its-directions", rc == 0 and not os.path.exists(d4) and os.path.isfile(aside)
          and _text(os.path.join(aside + ".directions", "x.mira.json")) == "d4's"
          and _log(book, "reject")[-1]["why"] == "wrong turn", out)
    forged = os.path.join(book, "runs", "drafts", "d90.db")
    shutil.copy2(aside, forged)
    rc, out = _draft(book, "promote", "--draft", "d90", "--approved", "yes", "--by", "owner")
    check("a-file-the-lineage-never-opened-is-DRAFT_NOT_OURS", rc == 1 and "[DRAFT_NOT_OURS]" in out, out)
    nxt = _opened(_draft(book, "open")[1])
    check("...the-next-id-counts-past-the-stray-file", _id(nxt) == "d91", nxt)
    rc, out = _draft(book, "reject", "--draft", "d90")
    check("...and-reject-sets-the-stray-aside", rc == 0 and not os.path.exists(forged)
          and _log(book, "reject")[-1]["opened"] is False, out)
    d92 = _opened(_draft(book, "open")[1])            # two takes; one's file under the other's id
    os.rename(nxt, nxt + ".real")
    shutil.copy2(d92, nxt)
    rc, out = _draft(book, "promote", "--draft", _id(nxt), "--approved", "yes", "--by", "owner")
    check("another-take's-file-under-this-id-is-DRAFT_NOT_OURS", rc == 1 and "[DRAFT_NOT_OURS]" in out, out)
    if os.path.exists(nxt):                            # the real take back in place (guarded: a landing moved it)
        os.rename(nxt, nxt + ".swapped")
    if os.path.exists(nxt + ".real"):
        os.rename(nxt + ".real", nxt)
    holder = sqlite3.connect(d92)
    holder.execute("BEGIN IMMEDIATE")
    holder.execute("INSERT INTO runs (run_id, created_at, config) VALUES ('open-writer', 'now', '{}')")
    rc, out = _draft(book, "promote", "--draft", _id(d92), "--approved", "yes", "--by", "owner")
    rc2, out2 = _draft(book, "reject", "--draft", _id(d92))
    holder.rollback()
    holder.close()
    check("a-draft-still-open-somewhere-is-DRAFT_IN_USE-to-promote-and-to-reject", rc == 1 and "[DRAFT_IN_USE]" in out
          and rc2 == 1 and "[DRAFT_IN_USE]" in out2 and db.role_of(rec)["head"] == "d2", (out, out2))
    _draft(book, "reject", "--draft", _id(d92))
    handle = open(nxt, "rb")                          # review 1: a program that is not SQLite holds the draft open
    rc, out = _draft(book, "promote", "--draft", _id(nxt), "--approved", "Keep that one.", "--by", "owner")
    handle.close()
    check("a-handle-another-program-holds-cannot-undo-a-landing:-promote-lands,-and-notes-the-file-left",
          rc == 0 and db.role_of(rec)["head"] == _id(nxt) and "note:" in out and os.path.isfile(nxt), out)
    rc, out = _draft(book, "reject", "--draft", _id(nxt))
    check("...which-reject-later-sets-aside-where-it-belongs", rc == 0 and not os.path.exists(nxt)
          and os.path.isfile(os.path.join(book, "runs", "drafts", "promoted", os.path.basename(nxt))), out)
    return _id(nxt)


def lease(book):
    print("\n[5] the lease: one flow at a time, freed by the OS when its holder dies")
    with lineage.hold(book, "test-holder"):
        for flow, args in (("open", ("open",)), ("promote", ("promote", "--draft", "d1", "--approved", "yes", "--by",
                                                             "owner")),
                           ("restore", ("restore", "--to", "d1", "--approved", "yes", "--by", "owner")),
                           ("reject", ("reject", "--draft", "d1")), ("adopt", ("adopt",))):
            rc, out = _draft(book, *args)
            check("a-held-lease-refuses-%s-naming-its-holder" % flow, rc == 1 and "[LINEAGE_LEASE_HELD]" in out
                  and "test-holder" in out, out)
    rc, out = _draft(book, "open")
    check("...and-is-free-once-released", rc == 0 and _opened(out), out)
    _draft(book, "reject", "--draft", _id(_opened(out)))
    rc, out = _run("-c", "import os, sys; sys.path.insert(0, %r); from src.engine import lineage; "
                         "lineage.hold(%r, 'dies-holding').__enter__(); os._exit(0)" % (REPO, book))
    rc2, out2 = _draft(book, "open")
    check("a-holder-that-dies-without-releasing-leaves-it-free", rc == 0 and rc2 == 0 and _opened(out2), (out, out2))
    live = _opened(out2) or os.path.join(book, "runs", "drafts", "x.db")
    elsewhere = os.path.join(book, "runs", "elsewhere", os.path.basename(live))
    os.makedirs(os.path.dirname(elsewhere), exist_ok=True)
    if os.path.isfile(live):
        shutil.copy2(live, elsewhere)
    rc, out = _turn(book, elsewhere)                   # an open draft's name, but not the draft
    check("a-copy-of-an-open-draft-kept-elsewhere-in-the-book-is-refused", rc != 0 and "[DRAFT_NOT_FOUND]" in out
          and "not a draft of this adopted book" in out, out)
    _draft(book, "reject", "--draft", _id(live))


def rewind(book, rec, head):
    print("\n[6] restore brings back a state the lineage kept, and keeps what it removes")
    rc, out = _draft(book, "restore", "--to", "d77", "--approved", "go back", "--by", "owner")
    check("an-unknown-state-is-DRAFT_HEAD_UNKNOWN", rc == 1 and "[DRAFT_HEAD_UNKNOWN]" in out, out)
    rc, out = _draft(book, "restore", "--to", head, "--approved", "go back", "--by", "owner")
    check("the-current-state-is-DRAFT_HEAD_CURRENT", rc == 1 and "[DRAFT_HEAD_CURRENT]" in out, out)
    take = _opened(_draft(book, "open", "--note", "a take the rewind will leave behind")[1])
    want = _counts(os.path.join(book, "runs", "history", "d1.db"))
    rc, out = _draft(book, "restore", "--to", "d1", "--approved", "Go back one.", "--by", "owner")
    kept = os.path.join(book, "runs", "history", "%s.db" % head)
    line = (_log(book, "restore") or [{}])[-1]
    check("restore-returns-the-record-to-d1", rc == 0 and _counts(rec) == want
          and db.role_of(rec) == {"role": "record", "head": "d1", "parent": "d0"}, out)
    check("...keeping-what-it-removed-with-its-digest-logged-before-the-landing", os.path.isfile(kept)
          and db.role_of(kept)["head"] == head and _kept(book, head).get("digest") == lineage.digest(kept)
          and line.get("approved") == "Go back one." and _log(book).index(_kept(book, head)) < _log(book).index(line),
          line)
    check("...and-the-directions-follow-(the-record's-kept-aside,-d1's-brought-back)",
          _text(os.path.join(rec + ".directions", "x.mira.json")) == "draft's"
          and os.path.isdir(kept + ".directions"), _text(os.path.join(rec + ".directions", "x.mira.json")))
    con = sqlite3.connect(os.path.join(book, "runs", "history", "d0.db"))
    con.execute("CREATE TABLE tampered (x)")                   # DDL: the one write a history copy's lock lets through
    con.commit()
    con.close()
    rc, out = _draft(book, "restore", "--to", "d0", "--approved", "all the way", "--by", "owner")
    check("a-history-copy-written-since-is-DRAFT_HISTORY_CHANGED", rc == 1 and "[DRAFT_HISTORY_CHANGED]" in out
          and db.role_of(rec)["head"] == "d1", out)
    pending = sqlite3.connect(kept)                            # review 1: a write still in the history copy's WAL
    pending.execute("CREATE TABLE pending (x)")
    pending.commit()
    rc, out = _draft(book, "restore", "--to", head, "--approved", "Forward.", "--by", "owner")
    pending.close()
    check("...and-so-is-one-with-a-write-still-pending-beside-it", rc == 1 and "[DRAFT_HISTORY_CHANGED]" in out
          and db.role_of(rec)["head"] == "d1", out)
    rc, out = _draft(book, "list")
    check("list-calls-a-take-from-the-state-rewound-away-stale", "draft %s  from %s  stale" % (_id(take), head) in out,
          out)
    check("list-shows-the-record-its-drafts-and-the-log", rc == 0 and "state d1" in out and "history:" in out
          and "restore" in out and "WARNING" not in out, out)
    rc, out = _turn(book, os.path.join(book, "runs", "history", "d1.db"))
    check("a-history-copy-passed-as---db-is-refused-up-front", rc != 0 and "[DB_IS_RECORD]" in out
          and "is the book's HISTORY" in out, out)


def cut_short(tmp):
    print("\n[7] a promote cut short after its landing: the old state stays restorable, and the warning stays")
    book, rec = _adopted_book(tmp, "cut")
    d1 = _opened(_draft(book, "open")[1])
    _turn(book, d1)
    code = ("import os, sys\nsys.path.insert(0, %r)\nfrom src.engine import drafts, lineage\nreal = lineage.append\n"
            "def cut(book, op, **k):\n    if op == 'promote':\n        os._exit(9)\n    return real(book, op, **k)\n"
            "lineage.append = cut\ndrafts.promote(%r, 'd1', 'Cut short, but said.', 'owner')\n") % (REPO, book)
    rc, out = _run("-c", code)
    rc2, out2 = _draft(book, "list")
    check("the-landing-happened-and-list-warns-with-the-owner's-words", rc == 9 and db.role_of(rec)["head"] == "d1"
          and "WARNING: state d1 landed without its log line" in out2 and "Cut short, but said." in out2, (out, out2))
    check("...and-names-the-draft-as-landed", "draft d1  from d0  landed, its log line missing" in out2, out2)
    rc, out = _draft(book, "reject", "--draft", "d1")
    check("...which-reject-files-with-the-promoted", rc == 0
          and os.path.isfile(os.path.join(book, "runs", "drafts", "promoted", "d1.db")), out)
    rc, out = _draft(book, "restore", "--to", "d0", "--approved", "Back to where it was.", "--by", "owner")
    check("...the-state-it-left-is-still-restorable", rc == 0 and db.role_of(rec)["head"] == "d0", out)
    d2 = _opened(_draft(book, "open")[1])
    _draft(book, "promote", "--draft", _id(d2), "--approved", "Next.", "--by", "owner")
    rc, out = _draft(book, "list")
    check("...and-later-landings-do-not-hide-the-gap", rc == 0 and "WARNING: state d1 landed without its log line" in out,
          out)


def renamed(tmp):
    print("\n[8] a book folder renamed after adoption keeps its record")
    book, rec = _adopted_book(tmp, "renamed")
    moved = book + " (second edition)"
    os.rename(book, moved)
    rc, out = _draft(moved, "list")
    check("list-finds-the-record-where-the-lineage-adopted-it", rc == 0 and "record: runs/%s" % os.path.basename(rec)
          in out and "role record" in out, out)
    rc, out = _draft(moved, "open")
    check("...a-draft-still-opens-from-it", rc == 0 and _opened(out), out)
    rc, out = _draft(moved, "adopt")
    check("...and-adopt-is-refused,-never-abandoning-it", rc == 1 and "[DRAFT_BOOK_ADOPTED]" in out, out)
    rc, out = _turn(moved)
    check("...and-a-driver-on-the-renamed-book-is-still-held-to-drafts", rc != 0 and "[DRAFT_NOT_FOUND]" in out
          and not os.path.exists(books.db_path(moved)), out)
    os.rename(os.path.join(moved, "runs", os.path.basename(rec)), os.path.join(moved, "runs", "moved-away.db"))
    rc, out = _draft(moved, "open")
    check("a-record-moved-away-is-DRAFT_RECORD_MISSING,-never-advising-adopt", rc == 1 and "[DRAFT_RECORD_MISSING]" in out
          and "adopt it first" not in out, out)
    rc, out = _draft(moved, "list")
    check("...and-list-says-it-is-MISSING,-not-none-yet", rc == 0 and "role MISSING" in out and "none yet" not in out, out)


def foreign(tmp):
    print("\n[9] another book's draft copied in under an id this book also minted is refused")
    one, _rec1 = _adopted_book(tmp, "one")
    two, rec2 = _adopted_book(tmp, "two")
    d_one, d_two = _opened(_draft(one, "open")[1]), _opened(_draft(two, "open")[1])
    _turn(one, d_one)
    os.rename(d_two, d_two + ".own")
    shutil.copy2(d_one, d_two)
    rc, out = _draft(two, "promote", "--draft", "d1", "--approved", "yes", "--by", "owner")
    check("it-is-DRAFT_NOT_EXTENDING-and-the-record-is-untouched", rc == 1 and "[DRAFT_NOT_EXTENDING]" in out
          and db.role_of(rec2)["head"] == "d0", out)


def encoding(tmp):
    print("\n[10] draft.py's output reaches a UTF-8 reader whole, whatever the pipe's own encoding")
    book = _mk_vault(os.path.join(tmp, "Łódź notes"))
    _turn(book)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    _draft(book, "adopt", env=env)
    rc, out = _draft(book, "open", env=env)
    check("open-prints-the-draft's-path-exactly", rc == 0 and _opened(out) and os.path.isfile(_opened(out)), out)
    rc, out = _draft(book, "promote", "--draft", "d1", "--approved", "Yes → keep it ✓\r\nall of it", "--by", "owner",
                     env=env)
    rc2, out2 = _draft(book, "list", env=env)
    check("...and-list-shows-the-owner's-words-intact-on-one-line", rc == 0 and rc2 == 0
          and "Yes → keep it ✓\\r\\nall of it" in out2
          and _log(book, "promote")[-1]["approved"] == "Yes → keep it ✓\r\nall of it", (out, out2))


def log_flaws(tmp):
    print("\n[11] the lineage log: a torn last line is marked and passed; any other flaw is refused by name")
    book, _rec = _adopted_book(tmp, "torn")
    with open(lineage.log_path(book), "ab") as fh:
        fh.write(b'{"op": "open", "draft": "d1", "par')           # a power loss mid-append
    rc, out = _draft(book, "list")
    check("list-still-reads-and-warns-of-the-torn-line", rc == 0 and "cut off mid-write" in out, out)
    rc, out = _draft(book, "open")
    check("...the-next-change-marks-it-and-carries-on", rc == 0 and _opened(out) and _log(book, "torn")
          and _log(book, "torn")[-1]["bytes"] > 0, out)
    with open(lineage.log_path(book), "a", encoding="utf-8") as fh:
        fh.write('{"op": "promote", "draft": "d1"}\n')
    rc, out = _draft(book, "list")
    check("a-promote-line-missing-its-fields-is-LINEAGE_UNREADABLE", rc == 1 and "[LINEAGE_UNREADABLE]" in out, out)
    run_id, gone = _one(books.db_path(book), "SELECT run_id FROM runs"), os.path.join(book, "runs", "drafts", "d66.db")
    rc, out = _run(os.path.join("scripts", "critic.py"), "--vault", book, "--run", run_id, "--stub")
    rc2, out2 = _run(os.path.join("scripts", "cut.py"), "--vault", book, "--db", gone, "--run", run_id)
    check("...while-a-reader-still-reads-the-record,-and-creates-nothing,-in-one-coded-line", rc == 0 and rc2 != 0
          and not os.path.exists(gone) and "Traceback" not in out + out2, (out, out2))
    whole, _r = _adopted_book(tmp, "whole")
    with open(lineage.log_path(whole), "ab") as fh:        # a whole entry that lost only its newline
        fh.write(b'{"draft": "d77", "op": "reject", "ts": "2026-09-27T00:00:00Z", "why": "kept whole"}')
    check("a-whole-last-entry-without-its-newline-still-counts", [e["draft"] for e in _log(whole, "reject")] == ["d77"]
          and lineage.torn(whole) == 0, _log(whole))
    os.makedirs(os.path.join(whole, "runs", "drafts", "d88.db.directions"))
    _write(os.path.join(whole, "runs", "history", "d55.db"), "")     # a history copy cut short: no kept line names it
    rc, out = _draft(whole, "list")
    check("list-names-a-directions-folder-left-without-its-database", rc == 0
          and "runs/drafts/d88.db.directions has no database beside it" in out, out)
    check("...and-a-history-copy-no-kept-line-names", rc == 0 and "history: d55.db (no kept line" in out, out)
    cut, _r = _adopted_book(tmp, "cut open")
    code = ("import os, sys\nsys.path.insert(0, %r)\nfrom src.engine import db, drafts\n"
            "def cut(src, dst, role, head=None):\n    os.makedirs(os.path.dirname(dst), exist_ok=True)\n"
            "    open(dst, 'wb').close()\n    os._exit(9)\n"
            "db.copy_to = cut\ndrafts.open_draft(%r)\n") % (REPO, cut)
    rc, out = _run("-c", code)
    rc2, out2 = _draft(cut, "list")
    check("a-copy-cut-short-is-named-incomplete,-and-reject-sets-it-aside", rc == 9
          and "draft d1  from d0  incomplete" in out2 and _draft(cut, "reject", "--draft", "d1")[0] == 0, (out, out2))
    tore, _r = _adopted_book(tmp, "torn adopt")
    with open(lineage.log_path(tore), "rb") as fh:
        whole_log = fh.read()
    with open(lineage.log_path(tore), "wb") as fh:           # the adopt line cut off mid-write
        fh.write(whole_log.rstrip(b"\n")[:-9])
    rc, out = _draft(tore, "open")
    check("after-a-torn-adopt-line-the-next-draft-is-d1,-never-the-record's-own-d0", rc == 0
          and _id(_opened(out)) == "d1", out)


def held_directions(tmp):
    print("\n[12] a file held open in a draft's directions stops its set-aside whole (review 3)")
    if os.name != "nt":
        print("  SKIP  a held file blocks no rename on POSIX")
        return
    book, _rec = _adopted_book(tmp, "held")
    d1 = _opened(_draft(book, "open")[1])
    _write(os.path.join(d1 + ".directions", "x.mira.json"), "d1's")
    handle = open(os.path.join(d1 + ".directions", "x.mira.json"), "rb")
    rc, out = _draft(book, "reject", "--draft", "d1")
    rc2, out2 = _draft(book, "list")
    handle.close()
    check("reject-refuses-and-moves-nothing:-the-draft-stays-open-with-its-directions", rc == 1
          and "[DRAFT_IN_USE]" in out and "stays where it is" in out and os.path.isfile(d1) and not _log(book, "reject")
          and "draft d1  from d0  live" in out2, (out, out2))
    rc, out = _draft(book, "reject", "--draft", "d1")
    aside = os.path.join(book, "runs", "drafts", "rejected", "d1.db")
    check("...and-sets-it-aside-whole-once-the-file-is-let-go", rc == 0 and os.path.isfile(aside)
          and _text(os.path.join(aside + ".directions", "x.mira.json")) == "d1's", out)
    d2, d3 = _opened(_draft(book, "open")[1]), _opened(_draft(book, "open")[1])
    _write(os.path.join(d3 + ".directions", "x.mira.json"), "d3's")
    handle = open(os.path.join(d3 + ".directions", "x.mira.json"), "rb")
    rc, out = _draft(book, "promote", "--draft", _id(d2), "--approved", "Keep d2.", "--by", "owner")
    handle.close()
    stale = os.path.join(book, "runs", "drafts", "stale", os.path.basename(d3 or "x.db"))
    check("a-promote's-note-that-a-take-stays-in-drafts/-is-true", rc == 0 and "%s stays in drafts/" % _id(d3) in out
          and os.path.isfile(d3) and not os.path.exists(stale), out)
    rc, out = _draft(book, "reject", "--draft", _id(d3))
    check("...and-its-advised-reject-files-it-with-the-stale", rc == 0 and os.path.isfile(stale)
          and _text(os.path.join(stale + ".directions", "x.mira.json")) == "d3's", out)


def main():
    print("test_draft_flow.py - drafts, approval and the record (gate draft-flow)\n")
    with tempfile.TemporaryDirectory(prefix="swe_draftflow_", ignore_cleanup_errors=True) as tmp:
        book, rec = adoption(tmp)
        refusals(tmp, book, rec)
        promote_flow(tmp, book, rec)
        head = takes(tmp, book, rec)
        lease(book)
        rewind(book, rec, head)
        cut_short(tmp)
        renamed(tmp)
        foreign(tmp)
        encoding(tmp)
        log_flaws(tmp)
        held_directions(tmp)
    print("\n%s: %d failure(s)" % ("OK" if not FAILS else "FAIL", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
