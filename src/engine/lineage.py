"""lineage.py — a book's lineage log and its lease: whose yes made each state the record, and one hand on it at a time.

The owner, 2026-09-26: "a scene is draft until it's approved and then it's saved into record." Gate record-role put the
record's wall in the database (`db_role` and the record lock): the record changes only by `db.promote` or `db.restore`,
page copies of whole states. What the database cannot hold is WHY each state became the record - the owner's words,
who carried them, whether the yes came before the work (a dictated ruling, correction or cut) or after it (a simulated
scene reviewed) - and WHICH history copy holds each state the record left. That is this log (gate draft-flow):
`<book>/runs/lineage.jsonl`, one JSON object per line, appended under the lease and never rewritten. A line that does
not read is refused by name, never skipped: a skipped line is a promote or a restore every check below would miss.

A HISTORY COPY IS TRUSTED BY ITS DIGEST. Every promote and restore logs a `kept` line - the copy of the record as it
was, its sha256, and the owner's words for the change - once the copy exists and BEFORE the landing, so the line is
true when written and a flow cut short after its landing leaves the old state restorable (review 1: a kill in that
window had lost the rewind for good). `drafts.restore` lands a copy only while its bytes still match: a history copy
is opened read-only (db.restore, db.role_of) but for `db.in_use`, whose close folds a stray WAL into the file, so a
write left pending beside it moves the digest too. Gate record-role review 2 found why this is needed: one raw UPDATE
of an open file's role to 'record' (the one role change the database allows on disk) mints a "record" whose history
copy would restore anything; the log is what knows the real ones.

A LINE CUT OFF MID-WRITE (a power loss, a full disk) is the one flaw the log tolerates: the last line without its
newline is left out of the read, and the next append closes it and writes a `torn` line after it, so the bytes stay
where they were and every later read knows why that one line does not parse. Any other unreadable line is refused.

THE LEASE is an operating-system lock on one byte of `<book>/runs/.lease` (msvcrt on Windows, flock elsewhere), so
the OS frees it the moment its holder exits or crashes: no time-to-live to guess, no stale lease to take over, and the
file is never deleted. A second holder is refused at once (LINEAGE_LEASE_HELD), naming the first from the note it left
at the head of the file. Windows refuses a whole read whose range touches a locked byte, and a buffered read asks
for 8 KB at once (measured 2026-09-27: the first form locked byte 4096 and every read of the note failed), so two
measures keep the note readable, either one enough alone: the locked byte sits a gigabyte past the note (a lock
beyond the end of a file is legal), and the note is read unbuffered.
"""
import datetime
import hashlib
import json
import os

from .records import RecordError

try:                                                   # the OS lock: msvcrt on Windows, flock elsewhere
    import msvcrt as _msvcrt
except ImportError:                                    # pragma: no cover - this machine is Windows
    _msvcrt = None
    import fcntl as _fcntl

RUNS = "runs"
LOG = "lineage.jsonl"
LEASE = ".lease"
OPS = ("adopt", "open", "reject", "promote", "restore", "stale", "kept", "torn", "declare")
#: what each op's entry must carry - read() refuses an entry without it, so no later check meets a KeyError
_NEEDS = {"adopt": ("head",), "open": ("draft", "parent"), "reject": ("draft",),
          "promote": ("draft", "head", "parent", "approved", "by"), "restore": ("head", "kept_head", "approved", "by"),
          "stale": ("draft", "sibling"), "kept": ("head", "history", "digest", "approved", "by"), "torn": ("bytes",),
          "declare": ("draft", "run", "file", "digest", "entries")}   # the author's hand (scripts/declare.py)
_NOTE = 512                                            # the holder note, overwritten in place at the file's head
_LOCK_AT = 1 << 30                                     # the byte the lease locks: far past the note and any buffer


def log_path(book_dir):
    return os.path.join(book_dir, RUNS, LOG)


def _entry(line):
    try:
        entry = json.loads(line)
    except ValueError:
        return None
    ok = isinstance(entry, dict) and entry.get("op") in OPS and all(k in entry for k in _NEEDS[entry["op"]])
    return entry if ok else None


def _lines(book_dir):
    """-> (whole lines, the torn tail or b"") - the log's bytes split at newlines."""
    path = log_path(book_dir)
    if not os.path.isfile(path):
        return [], b""
    with open(path, "rb") as fh:
        raw = fh.read().split(b"\n")
    return raw[:-1], raw[-1]


def read(book_dir):
    """-> [entry] in the order written; no log -> []. A line that is not an entry -> LINEAGE_UNREADABLE with its line
    number - unless it is a torn append: the line a `torn` entry follows, or the last one, cut off before its newline."""
    lines, _tail = _lines(book_dir)
    out, parsed = [], [(n, line, _entry(line)) for n, line in enumerate(lines, 1) if line.strip()]
    for i, (n, line, entry) in enumerate(parsed):
        if entry is None and not (i + 1 < len(parsed) and (parsed[i + 1][2] or {}).get("op") == "torn"):
            raise RecordError("LINEAGE_UNREADABLE", "%s line %d is not a lineage entry (a JSON object whose op is one of "
                              "%s, with that op's fields): %.120s - scripts/draft.py appends it; a line cut off by a "
                              "power loss is marked when the next one is written, and any other flaw is a hand edit"
                              % (log_path(book_dir), n, ", ".join(OPS), line.decode("utf-8", "replace").strip()))
        if entry is not None:
            out.append(entry)
    return out + [e for e in [_entry(_tail)] if e]      # a whole entry that lost only its newline still counts


def torn(book_dir):
    """The bytes of a last line cut off before its newline -> its length; 0 when the log ends whole, or its last line is
    a whole entry that lost only its newline."""
    tail = _lines(book_dir)[1].strip()
    return 0 if not tail or _entry(tail) else len(tail)


def append(book_dir, op, **fields):
    """Append one entry, stamped with the UTC time, and flush it to disk -> the entry. Called under the lease."""
    if op not in OPS:
        raise RecordError("LINEAGE_OP_UNKNOWN", "lineage.append: %r is not an op (%s)" % (op, ", ".join(OPS)))
    entry = dict(fields, op=op, ts=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    path = log_path(book_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cut, tail = torn(book_dir), _lines(book_dir)[1].strip()
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        if tail:                                       # close the last line first - and say so when it was torn
            fh.write("\n" + (json.dumps({"op": "torn", "bytes": cut, "ts": entry["ts"]}, sort_keys=True) + "\n"
                              if cut else ""))
        fh.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return entry


def _number(ident):
    s = str(ident or "")
    return int(s[1:]) if s[:1] == "d" and s[1:].isdigit() else -1


def next_id(book_dir, taken=()):
    """The next state id -> "d<N>", one past every id the log names and every one in `taken` (the database files on
    disk); "d0" is the first, the state a book is adopted in. Counted, never random (CLAUDE.md hard rule 4)."""
    seen = [_number(t) for t in taken]
    for e in read(book_dir):
        seen += [_number(e.get(k)) for k in ("head", "parent", "draft", "kept_head")]
    return "d%d" % (max(seen + [-1]) + 1)


def digest(file_path):
    """The sha256 of a file's bytes -> hex."""
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def history_of(book_dir):
    """{head: (history file, relative to the book, its digest)} - every history copy the log's `kept` lines recorded,
    the latest for each state."""
    return {e["head"]: (e["history"], e["digest"]) for e in read(book_dir) if e["op"] == "kept"}


def minted(book_dir):
    """{draft id: the entry that opened it} for every draft the log opened."""
    return {e["draft"]: e for e in read(book_dir) if e["op"] == "open"}


def _lock(fh):
    fh.seek(_LOCK_AT)
    if _msvcrt:
        _msvcrt.locking(fh.fileno(), _msvcrt.LK_NBLCK, 1)
    else:                                              # pragma: no cover
        _fcntl.flock(fh.fileno(), _fcntl.LOCK_EX | _fcntl.LOCK_NB)


def _unlock(fh):
    fh.seek(_LOCK_AT)
    if _msvcrt:
        _msvcrt.locking(fh.fileno(), _msvcrt.LK_UNLCK, 1)
    else:                                              # pragma: no cover
        _fcntl.flock(fh.fileno(), _fcntl.LOCK_UN)


def holder(book_dir):
    """The note the lease's last holder left -> text (the holder's pid, op and start), or "" when there is none."""
    path = os.path.join(book_dir, RUNS, LEASE)
    try:
        with open(path, "rb", buffering=0) as fh:     # unbuffered: a buffered read asks Windows for 8 KB at once,
            return fh.read(_NOTE).decode("utf-8", "replace").strip()   # and one locked byte in range refuses it all
    except OSError:
        return ""


class hold:
    """`with lineage.hold(book_dir, "promote"):` - the book's lease for one flow. Refuses at once, naming the holder,
    while another process holds it (LINEAGE_LEASE_HELD); freed on exit, and by the OS if this process dies."""

    def __init__(self, book_dir, op):
        self.book_dir, self.op, self.fh = book_dir, op, None

    def __enter__(self):
        path = os.path.join(self.book_dir, RUNS, LEASE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fh = os.fdopen(os.open(path, os.O_RDWR | os.O_CREAT), "r+b")
        try:
            _lock(fh)
        except OSError:
            fh.close()
            raise RecordError("LINEAGE_LEASE_HELD", "the book's lease is held - another flow is running on this book (%s)"
                              " - retry once it finishes; the operating system frees the lease when that process ends"
                              % (holder(self.book_dir) or "no note"))
        note = json.dumps({"pid": os.getpid(), "op": self.op,
                           "since": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
        fh.seek(0)
        fh.write(note.encode("utf-8").ljust(_NOTE))
        fh.flush()
        self.fh = fh
        return self

    def __exit__(self, *_exc):
        try:
            _unlock(self.fh)
        finally:
            self.fh.close()
        return False
