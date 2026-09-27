"""drafts.py — the book's approval flow: adopt, open a draft, reject, promote, restore, over the record's primitives.

The owner, 2026-09-26: "a scene is draft until it's approved and then it's saved into record." Gate record-role made
the database hold that rule (`db_role`, the record lock, and `db.adopt` / `copy_to` / `promote` / `restore`, page
copies of whole states); this module is the flow that uses them, and `scripts/draft.py` is its command line (gate
draft-flow). Everything lives in the book's own `runs/` folder, beside the record:

  runs/<slug>.db                 the RECORD, once adopted - no writer touches it (DB_IS_RECORD); the lineage keeps its
                                 name, so a book folder renamed later still finds it (review 1)
  runs/drafts/<id>.db            a DRAFT: a copy the drivers write (`--db`); ids count up from d1
  runs/drafts/{promoted,rejected,stale}/   drafts set aside, never deleted
  runs/history/<head>.db         the record as it was before each promote or restore - one per state it left
  runs/lineage.jsonl             who approved what (lineage.py); runs/.lease the one-flow-at-a-time lock

Once a book is adopted, a WRITER may open only an existing draft the lineage opened (`writer_db`): a draft already
promoted, rejected or set aside, or a path nothing opened, is refused before any work, and the driver is told not to
create a file (review 1, MAJOR: a driver aimed at a promoted draft's old path had made a new, empty chronicle there
and run a paid scene on it).

A database's `<db>.directions/` folder (scripts/direct.py's per-actor direction files) travels with it: copied into
a new draft, swapped into the record by a promote, set aside with the record a restore removes - moved BEFORE the
landing's log line, so a line that says a state landed also says its directions did.

TWO APPROVAL TIMINGS, ONE PROMOTE (Fable review 2 s1.2e): a simulated scene is approved after its review; a dictated
change - a keeper ruling, a critic correction, a cut, an author's declaration - is approved before it is written, and
runs on a draft promoted in the same motion. The lineage records the owner's words exactly as given, who carried them
(`owner` or `partner-relayed`) and which timing, so a relayed yes never reads as the owner's own.

A REJECTED DRAFT is an observation declined, not a life undone: the record is the one history (Fable review 2 s1.5).
"""
import os
import shutil
import sqlite3

from . import books, db, lineage
from .records import RecordError

APPROVERS = ("owner", "partner-relayed")
_ASIDE = ("promoted", "rejected", "stale")
_ENDED = {"promote": "promoted", "reject": "set aside", "stale": "left stale by another landing"}


def _runs(book_dir, *parts):
    return os.path.join(book_dir, lineage.RUNS, *parts)


def _rel(book_dir, path):
    return os.path.relpath(path, book_dir).replace(os.sep, "/")


def _book(book_dir):
    return '--book "%s"' % book_dir


def _stems(book_dir):
    """The ids of every database file under runs/drafts and runs/history - counted by next_id, so a file a lost log
    forgot still keeps its id."""
    out = []
    for folder in [_runs(book_dir, "drafts")] + [_runs(book_dir, "drafts", a) for a in _ASIDE] + [_runs(book_dir, "history")]:
        if os.path.isdir(folder):
            out += [f.split(".")[0] for f in os.listdir(folder) if f.endswith(".db")]
    return out


def _adoption(book_dir, log=None):
    """The lineage's adopt entry, or None - also None once a later `release` ended it (scripts/draft.py release)."""
    last = next((e for e in reversed(log if log is not None else lineage.read(book_dir)) if e["op"] in ("adopt",
                                                                                                     "release")), None)
    return last if last is not None and last["op"] == "adopt" else None


def _record(book_dir):
    """The record's file: where the lineage adopted it, else the book's default (books.db_path)."""
    found = _adoption(book_dir)
    return os.path.join(book_dir, found["file"]) if found else books.db_path(book_dir)


def _role(path):
    try:
        return db.role_of(path)
    except sqlite3.DatabaseError:                      # a file that is no database: a copy cut short, or not ours
        return None


def adopted(book_dir):
    """Is the book adopted - by its lineage, or by its own database being a record? Every opener of a book asks: an
    adopted book's databases are never created by opening them, a reader's included (review 2: a critic review aimed at
    a promoted draft's old path had made an empty chronicle there and reported it clean)."""
    default = books.db_path(book_dir)
    return _adoption(book_dir) is not None or (os.path.isfile(default)
                                               and (_role(default) or {}).get("role") == "record")


def _holder(path):
    """The book folder a file sits in - its nearest ancestor holding world/ (books._book_dirs' marker) - or None."""
    here = os.path.dirname(os.path.abspath(path))
    while not os.path.isdir(os.path.join(here, "world")):
        if os.path.dirname(here) == here:
            return None
        here = os.path.dirname(here)
    return here


def may_create(db_path, book_dir):
    """May a reader's open create `db_path` -> False when the book it names, or the book folder the file sits in, is
    adopted (review 3: a --vault naming another, unadopted book let critic make an empty chronicle at an adopted book's
    promoted draft's old path). An unreadable lineage is still a lineage, so it answers no and the reader still reads
    an existing file; `draft.py list` and every flow refuse the log by name."""
    for book in (book_dir, _holder(db_path)):
        try:
            if book is not None and adopted(book):
                return False
        except RecordError as exc:
            if not exc.code.startswith("LINEAGE_"):
                raise
            return False
    return True


def _only_books(book_dir):
    """Refuse a folder with no world/ in it before a flow writes anything there - a lease included (review 2, nit)."""
    if not os.path.isdir(os.path.join(book_dir, "world")):
        raise RecordError("DRAFT_NOT_A_BOOK", "%s holds no world/ folder, so it is no book (books._book_dirs' marker) - "
                          "nothing was written there" % book_dir)


def writer_db(db_path, doing, book_dir=None):
    """Check, before any work, the database a WRITER is about to open -> (the path, may the opener create it). A book's
    RECORD or a HISTORY copy is refused (DB_IS_RECORD). Once the book is adopted, only an open draft the lineage opened
    passes (DRAFT_NOT_FOUND / DRAFT_NOT_OURS otherwise), and the opener must not create a file. An unadopted book - or
    no book at all - is written as it always was."""
    role = _role(db_path) if db_path and os.path.isfile(db_path) else None
    if role and role["role"] in ("record", "history"):
        raise RecordError("DB_IS_RECORD", "%s: %s is the book's %s (state %s), which changes only by promote or "
                          "restore - write on a draft: python scripts/draft.py open %s, then pass the path it prints "
                          "as --db" % (doing, db_path, role["role"].upper(), role["head"],
                                       _book(book_dir) if book_dir else "--book <book>"))
    if book_dir is None or not adopted(book_dir):
        held = _holder(db_path) if db_path else None
        if held is None or not adopted(held):
            return db_path, True                       # unadopted: by the lineage, and by the book's own database
        book_dir = held                                # the file sits in an adopted book, whatever --vault named (review 3)
    here =os.path.normcase(os.path.realpath(os.path.dirname(os.path.abspath(db_path))))
    if here != os.path.normcase(os.path.realpath(_runs(book_dir, "drafts"))) or not db_path.endswith(".db"):
        raise RecordError("DRAFT_NOT_FOUND", "%s: %s is not a draft of this adopted book, whose writers run on drafts "
                          "only - open one: python scripts/draft.py open %s" % (doing, db_path, _book(book_dir)))
    _draft_file(book_dir, os.path.basename(db_path)[:-3], doing)
    return db_path, False


def _record_role(book_dir):
    """-> (the record's file, its role row), refusing a book that is not adopted (DRAFT_BOOK_NOT_ADOPTED) and one whose
    adopted record is missing or no longer a record (DRAFT_RECORD_MISSING) - never advising adopt for that one."""
    rec, found = _record(book_dir), _adoption(book_dir)
    role = _role(rec) if os.path.isfile(rec) else None
    if found and (role is None or role["role"] != "record"):
        raise RecordError("DRAFT_RECORD_MISSING", "the lineage adopted %s as this book's record (%s), and it is %s - put "
                          "it back where the lineage names it; adopting again would abandon every approved state"
                          % (found["file"], found["ts"], "missing" if role is None else "a %s" % role["role"]))
    if role is None or role["role"] != "record":
        raise RecordError("DRAFT_BOOK_NOT_ADOPTED", "%s: the book's database is %s, not its record - adopt it first: "
                          "python scripts/draft.py adopt %s" % (rec, role["role"] if role else "missing", _book(book_dir)))
    return rec, role


def _approval(approved, by):
    """The owner's words exactly as given -> them; refused without a letter or digit in them, or an unknown approver."""
    words = "" if approved is None else str(approved)
    shape = words.strip()
    if not any(ch.isalnum() for ch in words) or (shape.startswith("<") and shape.endswith(">")):
        raise RecordError("DRAFT_APPROVAL_MISSING", "a promote or restore changes the record, and needs the owner's "
                          "words, verbatim (--approved) - words, not punctuation or a <placeholder>")
    if by not in APPROVERS:
        raise RecordError("DRAFT_APPROVER_UNKNOWN", "who gave the yes is %r - one of %s (a relayed yes is recorded "
                          "as relayed)" % (by, ", ".join(APPROVERS)))
    return words


def _draft_file(book_dir, draft_id, doing="draft.py"):
    """The open draft `draft_id` -> its path: a file in runs/drafts that the lineage opened and has not promoted,
    rejected or left stale since, still carrying the id and parent the lineage gave it (DRAFT_NOT_FOUND /
    DRAFT_NOT_OURS - gate record-role review 3: a file forged beside the record must not reach promote)."""
    path, log = _runs(book_dir, "drafts", "%s.db" % draft_id), lineage.read(book_dir)
    ended = [e["op"] for e in log if e.get("draft") == draft_id and e["op"] in _ENDED]
    if ended or not os.path.isfile(path):
        raise RecordError("DRAFT_NOT_FOUND", "%s: no open draft %r in %s%s - open a new one: python scripts/draft.py "
                          "open %s" % (doing, draft_id, _runs(book_dir, "drafts"), (" - it was %s" % _ENDED[ended[-1]])
                                       if ended else "", _book(book_dir)))
    opened, role = next((e for e in log if e["op"] == "open" and e["draft"] == draft_id), None), _role(path)
    if opened is None or role != {"role": "draft", "head": draft_id, "parent": opened["parent"]}:
        raise RecordError("DRAFT_NOT_OURS", "%s: %s is not the draft the lineage opened as %r (it reads %s) - only a "
                          "draft `draft.py open` made from this book's record is written or promoted; set it aside: "
                          "python scripts/draft.py reject %s --draft %s" % (doing, path, draft_id, role, _book(book_dir),
                                                                            draft_id))
    return path


def _extends(draft, rec):
    """Does the draft hold every run and turn of the record it names as its parent -> "" or what it lacks. A real draft
    always does: it began as a copy and the log is append-only (review 1: another book's draft, copied in under an id
    this book also minted, carried the right role row)."""
    a, b = db.connect(draft), db.connect(rec)
    try:
        runs = {r[0]: r[1] for r in a.execute("SELECT run_id, created_at FROM runs")}
        turns = {r[0]: r[1] for r in a.execute("SELECT run_id, COUNT(*) FROM turns GROUP BY run_id")}
        for run_id, created in b.execute("SELECT run_id, created_at FROM runs"):
            if runs.get(run_id) != created:
                return "the record's run %s is not in it" % run_id
        for run_id, n in b.execute("SELECT run_id, COUNT(*) FROM turns GROUP BY run_id"):
            if turns.get(run_id, 0) < n:
                return "it holds %d of the record's %d turns of run %s" % (turns.get(run_id, 0), n, run_id)
        return ""
    finally:
        a.close()
        b.close()


def _free(folder, head):
    """A name for a copy of state `head` in `folder` that no file or folder holds yet: <head>.db, <head>.2.db, ..."""
    os.makedirs(folder, exist_ok=True)
    k, name = 1, "%s.db" % head
    while any(os.path.exists(os.path.join(folder, name + s)) for s in ("", "-wal", "-shm", ".directions")):
        k += 1
        name = "%s.%d.db" % (head, k)
    return os.path.join(folder, name)


def _move(path, folder):
    """Set a database aside into `folder`, with its .directions -> the new path, under a name no kept file holds.
    Refuses one still open somewhere (DRAFT_IN_USE: an SQLite connection that outlives a close of our own, or another
    program's handle that refuses the move); nothing is deleted. db.in_use's close also folds a killed writer's WAL
    into the file first, so the move carries every committed turn (review 2, finding 3)."""
    busy = db.in_use(path)
    if busy:
        raise RecordError("DRAFT_IN_USE", "%s is still open somewhere (%s outlived a close) - close the run that holds "
                          "it first" % (path, busy))
    dst = _free(folder, os.path.basename(path)[:-3])  # <id>.db, else <id>.2.db ...: nothing kept is written over
    try:
        os.rename(path, dst)
    except OSError as exc:
        raise RecordError("DRAFT_IN_USE", "%s could not be moved - another program holds it open (%s)" % (path, exc))
    if os.path.isdir(path + ".directions"):
        try:
            os.rename(path + ".directions", dst + ".directions")
        except OSError as exc:                         # a file in it held: the database goes back, so nothing moved and
            try:                                       # the caller logs nothing (review 3: the refusal had said the
                os.rename(dst, path)                   # database stayed while it sat set aside)
                where = "%s stays where it is" % path
            except OSError:
                where = "%s is now %s, its .directions still beside the old name" % (path, dst)
            raise RecordError("DRAFT_IN_USE", "%s - a file in its .directions folder is held open by another program "
                              "(%s)" % (where, exc))
    return dst


def _swap(pairs):
    """Move each .directions folder that exists -> notes on any a held handle kept in place."""
    notes = []
    for src, dst in pairs:
        if os.path.isdir(src):
            try:
                os.rename(src, dst)
            except OSError as exc:
                notes.append("%s stays where it is (%s)" % (src, exc))
    return notes


def adopt(book_dir, new=False):
    """Make the book's database its RECORD -> the lineage entry. A book is adopted once (DRAFT_BOOK_ADOPTED); only a
    book folder (DRAFT_NOT_A_BOOK: nothing is written into any other); `new` starts an empty record for a book that
    has no database yet (DRAFT_RECORD_MISSING without it). The adopted state is d0 (or the next id a surviving log or
    file leaves free); from here no writer touches the record."""
    _only_books(book_dir)
    rec = books.db_path(book_dir)
    with lineage.hold(book_dir, "adopt"):
        found = _adoption(book_dir)
        if found:
            raise RecordError("DRAFT_BOOK_ADOPTED", "the lineage adopted this book already (%s, record %s, state %s) - "
                              "a book is adopted once" % (found["ts"], found["file"], found["head"]))
        if not os.path.isfile(rec):
            if not new:
                raise RecordError("DRAFT_RECORD_MISSING", "%s has no database yet - run the book once, or start its "
                                  "record empty: python scripts/draft.py adopt %s --new" % (book_dir, _book(book_dir)))
            db.connect(rec).close()
        busy = db.in_use(rec)
        if busy:                                       # a run still open on it would lose its next turn to the lock
            raise RecordError("DRAFT_IN_USE", "%s is still open somewhere (%s outlived a close) - finish the run "
                              "that holds it, then adopt" % (rec, busy))
        head = lineage.next_id(book_dir, _stems(book_dir))
        db.adopt(rec, head)
        return lineage.append(book_dir, "adopt", head=head, parent="", file=_rel(book_dir, rec))


def open_draft(book_dir, note=""):
    """Copy the record into a new DRAFT -> its path, for the drivers' --db. Refuses an unadopted book. The lineage line
    comes first: a copy cut short leaves an id the lineage opened and `reject` sets aside, never an unexplained file."""
    _only_books(book_dir)
    with lineage.hold(book_dir, "open"):
        rec, role = _record_role(book_dir)
        did = lineage.next_id(book_dir, _stems(book_dir) + [role["head"]])   # the record's own state counts too
        path = _runs(book_dir, "drafts", "%s.db" % did)
        lineage.append(book_dir, "open", draft=did, parent=role["head"], file=_rel(book_dir, path), note=str(note or ""))
        db.copy_to(rec, path, "draft", did)
        if os.path.isdir(rec + ".directions"):
            shutil.copytree(rec + ".directions", path + ".directions")
    return path


def reject(book_dir, draft_id, why=""):
    """Set a file in runs/drafts aside -> the lineage entry: an open draft into drafts/rejected; one the lineage already
    promoted or left stale, but a held handle kept in place, into its own folder; one the lineage never opened (a copy
    cut short, a stray file) into drafts/rejected too. Nothing is deleted."""
    _only_books(book_dir)
    with lineage.hold(book_dir, "reject"):
        path = _runs(book_dir, "drafts", "%s.db" % draft_id)
        if not os.path.isfile(path):
            raise RecordError("DRAFT_NOT_FOUND", "no file %s in %s to set aside" % (os.path.basename(path),
                                                                                     _runs(book_dir, "drafts")))
        ended = [e["op"] for e in lineage.read(book_dir) if e.get("draft") == draft_id and e["op"] in ("promote", "stale")]
        rec = _record(book_dir)                        # a draft that landed without its log line is the record's own
        landed = os.path.isfile(rec) and (_role(rec) or {}).get("head") == draft_id
        into = {"promote": "promoted", "stale": "stale"}.get((ended[-1:] or [""])[0], "promoted" if landed else "rejected")
        moved = _move(path, _runs(book_dir, "drafts", into))
        return lineage.append(book_dir, "reject", draft=draft_id, why=str(why or ""), file=_rel(book_dir, moved),
                              into=into, opened=draft_id in lineage.minted(book_dir))


def promote(book_dir, draft_id, approved, by, in_advance=False):
    """Make an open draft the book's RECORD on the owner's words -> (the lineage entry, [notes]). In order: the draft
    must be ours, closed, and hold all the record holds (DRAFT_NOT_EXTENDING); the record as it is is kept in
    runs/history and a `kept` line logs it with the words (true when written - a landing cut short after it leaves the
    old state restorable); the draft lands whole (db.promote); the directions swap; the `promote` line is logged; the
    draft is set aside, and every other open draft from the same state goes to drafts/stale. After the landing nothing
    is fatal: a file a handle keeps in place is reported in the notes."""
    words = _approval(approved, by)
    timing = "in-advance" if in_advance else "after-review"
    _only_books(book_dir)
    with lineage.hold(book_dir, "promote"):
        path = _draft_file(book_dir, draft_id)
        busy = db.in_use(path)
        if busy:
            raise RecordError("DRAFT_IN_USE", "%s is still open somewhere (%s outlived a close) - close the run that "
                              "writes it, then promote" % (path, busy))
        rec, was = _record_role(book_dir)
        lacks = _extends(path, rec)
        if lacks:
            raise RecordError("DRAFT_NOT_EXTENDING", "%s does not extend the record it names as its parent (%s): %s - it "
                              "is not a copy of this book's record" % (path, was["head"], lacks))
        hist = _free(_runs(book_dir, "history"), was["head"])
        got = db.promote(path, rec, hist, on_kept=lambda copy: lineage.append(
            book_dir, "kept", head=was["head"], history=_rel(book_dir, copy), digest=lineage.digest(copy),
            draft=draft_id, approved=words, by=by, timing=timing))
        notes = _swap(((rec + ".directions", hist + ".directions"), (path + ".directions", rec + ".directions")))
        entry = lineage.append(book_dir, "promote", draft=draft_id, head=got["head"], parent=got["parent"],
                               history=_rel(book_dir, hist), approved=words, by=by, timing=timing)
        notes.append(_aside(book_dir, path, "promoted", draft_id))
        for did, opened in sorted(lineage.minted(book_dir).items()):
            take = _runs(book_dir, "drafts", "%s.db" % did)
            if did != draft_id and opened["parent"] == was["head"] and os.path.isfile(take):
                lineage.append(book_dir, "stale", draft=did, sibling=draft_id)
                notes.append(_aside(book_dir, take, "stale", did))
    return entry, [n for n in notes if n]


def _aside(book_dir, path, where, did):
    """Set a draft aside after a landing -> a note, "" when done; a refusal is reported, not raised."""
    try:
        _move(path, _runs(book_dir, "drafts", where))
        return ""
    except RecordError as exc:
        return "%s stays in drafts/ (%s) - set it aside later: python scripts/draft.py reject %s --draft %s" % (
            did, exc, _book(book_dir), did)


def restore(book_dir, head, approved, by):
    """Rewind: make the record the state `head` again, from the history copy the lineage kept for it -> (the lineage
    entry, [notes]). Refuses a state the log never kept (DRAFT_HEAD_UNKNOWN), the state the record is already in
    (DRAFT_HEAD_CURRENT) and a copy in use or whose bytes moved since (DRAFT_HISTORY_CHANGED). What the record held
    is kept first, logged as `restore` logs the promote's."""
    words = _approval(approved, by)
    _only_books(book_dir)
    with lineage.hold(book_dir, "restore"):
        rec, was = _record_role(book_dir)
        if head == was["head"]:
            raise RecordError("DRAFT_HEAD_CURRENT", "the record is already state %s" % head)
        kept = lineage.history_of(book_dir)
        if head not in kept:
            raise RecordError("DRAFT_HEAD_UNKNOWN", "the lineage kept no copy of state %r (kept: %s)"
                              % (head, ", ".join(sorted(kept)) or "none"))
        src = os.path.join(book_dir, kept[head][0])
        busy = db.in_use(src) if os.path.isfile(src) else ""    # its close folds a stray WAL in, which the digest sees
        if busy or not os.path.isfile(src) or lineage.digest(src) != kept[head][1] or db.role_of(src)["head"] != head:
            raise RecordError("DRAFT_HISTORY_CHANGED", "%s is not the copy of state %s the lineage logged - it is "
                              "missing, still open somewhere, or something wrote it since" % (src, head))
        keep = _free(_runs(book_dir, "history"), was["head"])
        got = db.restore(src, rec, keep, on_kept=lambda copy: lineage.append(
            book_dir, "kept", head=was["head"], history=_rel(book_dir, copy), digest=lineage.digest(copy),
            restore=head, approved=words, by=by))
        notes = _swap(((rec + ".directions", keep + ".directions"),))
        if os.path.isdir(src + ".directions") and not os.path.exists(rec + ".directions"):
            shutil.copytree(src + ".directions", rec + ".directions")
        entry = lineage.append(book_dir, "restore", head=got["head"], parent=got["parent"], source=kept[head][0],
                               kept_head=was["head"], kept=_rel(book_dir, keep), approved=words, by=by)
    return entry, notes


def _gaps(log, record):
    """Every state the record reached that the log never logged landing -> [text]. Each landing must start where the
    last one left (a promote from its parent, a restore from its kept head), and the last must be the record's own
    state; a flow cut short between its landing and its log line breaks that chain, and the break stays visible."""
    out, last, words = [], None, {e.get("draft"): e for e in log if e["op"] == "kept" and e.get("draft")}
    for e in log:
        if e["op"] not in ("adopt", "promote", "restore"):
            continue
        start = e["parent"] if e["op"] == "promote" else e.get("kept_head")
        if last is not None and start != last:
            out.append(start)
        last = e["head"]
    if record is not None and last is not None and record["head"] != last:
        out.append(record["head"])
    return ["state %s landed without its log line%s" % (h, (" (the owner's words were: %r)" % words[h]["approved"])
                                                         if h in words else "") for h in out]


def listing(book_dir):
    """The book's states at a glance -> {"record", "drafts", "aside", "history", "log", "gaps", "torn", "orphans"} -
    read only. A record the lineage adopted but that is missing reads as role "missing", never as "none yet"."""
    rec, log = _record(book_dir), lineage.read(book_dir)
    record = dict(_role(rec) or {"role": "unreadable", "head": "", "parent": ""}, file=_rel(book_dir, rec)
                  ) if os.path.isfile(rec) else ({"role": "missing", "head": "", "parent": "", "file": _rel(book_dir, rec)}
                                                 if _adoption(book_dir, log) else None)
    opened = {e["draft"]: e for e in log if e["op"] == "open"}
    ended = {e["draft"]: e["op"] for e in log if e["op"] in _ENDED}
    drafts, folder = [], _runs(book_dir, "drafts")
    for f in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        did = f[:-3]
        if f.endswith(".db") and os.path.isfile(os.path.join(folder, f)):
            parent = opened.get(did, {}).get("parent")
            state = ("ended: %s" % _ENDED[ended[did]] if did in ended else "not opened by draft.py" if did not in opened
                     else "landed, its log line missing" if record is not None and record["head"] == did
                     else "incomplete - not the draft the lineage opened (a copy cut short?)"
                     if (_role(os.path.join(folder, f)) or {}).get("head") != did
                     else "live" if record is not None and parent == record["head"] else "stale")
            drafts.append({"draft": did, "parent": parent, "note": opened.get(did, {}).get("note", ""), "state": state})
    aside = {a: sorted(f[:-3] for f in os.listdir(_runs(book_dir, "drafts", a)) if f.endswith(".db"))
             for a in _ASIDE if os.path.isdir(_runs(book_dir, "drafts", a))}
    hist, logged = _runs(book_dir, "history"), {os.path.basename(e["history"]) for e in log if e["op"] == "kept"}
    history = [f if f in logged else "%s (no kept line - a copy cut short?)" % f
               for f in sorted(os.listdir(hist)) if f.endswith(".db")] if os.path.isdir(hist) else []
    orphans = sorted(f[:-len(".db.directions")] for f in os.listdir(folder)
                     if f.endswith(".db.directions") and not os.path.exists(os.path.join(folder, f[:-len(".directions")]))
                     ) if os.path.isdir(folder) else []
    return {"record": record, "drafts": drafts, "aside": aside, "history": history, "log": log[-10:],
            "gaps": _gaps(log, record) if record and record["role"] == "record" else [], "torn": lineage.torn(book_dir),
            "orphans": orphans}
