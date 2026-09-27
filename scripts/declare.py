#!/usr/bin/env python3
"""declare.py — the author's hand: a file of the owner's declarations, written into a run through the engine's own
writers (gate author-declarations).

The owner, 2026-09-26: "a way to add content directly into the db". A DECLARATION FILE is a JSON list; each entry is
one thing the owner says is so, in the owner's own words (`words`, kept verbatim), of one kind:

  {"kind": "event", "words": ..., "type": <a world type>, "payload": {...}, "actor"?, "target"?, "location"?}
      an off-page world event - scripts/keeper.py `apply_proposals`, every gate of it, landing at the run's last
      committed turn and judged in the world the next beat reads; everyone it names (actor, target, a reveal's knowers,
      a tension's watched parties) must be of the run's cast or a person its pinned bible names, every place it names
      a place that bible names, and every payload key one the fold reads
  {"kind": "correction", "words": ..., "turn": N}
      the owner's correction of a recorded beat - scripts/critic.py `correct_run`, at the run's next tick; the words
      are its issue; it retracts what the beat did, never an event the owner declared (`_world_moving_ids`)
  {"kind": "fact", "words": ..., "extracts": [{"subject", "predicate", "object"?}, ...]}
      a world fact of the AUTHORED tier (docs/keeper-of-truth.md T0) - src/engine/claims.py `record`, spoken by
      `author` (a name that speaks nothing else) at the run's last committed turn; the words are what was said

SOURCE `author` on every row - an event's and a correction's payload, a fact's tier and speaker. The path sets it and
a file never does: an entry naming its own turn or source is refused, a keeper report's `source` is trimmed
(`apply_proposals`) and no other claim may be spoken by `author` (claims.record), so nothing else passes for the
owner's hand. No turn before the one it lands at folds differently: a declaration never rewrites what came before it.

ALL OR NOTHING. The whole file is shape-checked before anything opens, then REHEARSED - every entry, in the order it
will be written, through the writers themselves - on a throwaway copy of the database (db.scratch_copy); the book is
written only if the rehearsal wrote every entry (review 1: a dry pass that judged each entry alone let two entries on
one world change, or a fact the claims writer refused, write half a file). Corrections go first, so one of the last beat
never supersedes an event the same file adds. The file is kept in the book (runs/declarations/<digest>.json), beside a
receipt of the rows each declaration of it wrote (<digest>.rows.jsonl); the same file declared into a database that
already holds those rows is refused (DECLARE_ALREADY_DECLARED).

ON AN ADOPTED BOOK the declaration goes into an open, current DRAFT (the record refuses it, drafts.writer_db; a stale
take is refused), under the book's lease; a `declare` line in the lineage names the kept file, its sha256 and the rows,
and the owner's yes lands it: `draft.py promote --in-advance`, the timing for a change dictated before it is written -
unless the draft also holds a beat played since it opened, which is approved after its review.

Usage: python scripts/declare.py --book <slug|folder> --run <run_id> --file <declarations.json> [--db <draft>] [--dry-run]
"""
import argparse
import contextlib
import datetime
import hashlib
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import bible, books, claims, db, drafts, lineage        # noqa: E402
from src.engine.errors import EngineError                               # noqa: E402
from src.engine.ledger import Ledger                                    # noqa: E402
from src.engine.records import RecordError                              # noqa: E402
from critic import correct_run                                          # noqa: E402  (the correction writer)
from keeper import _extracts, apply_proposals                           # noqa: E402  (the event writer, the extract reader)

SOURCE = claims.AUTHOR
#: per kind: (the fields it needs, the fields it may carry) - beside `kind` and `words`, nothing else is read
_FIELDS = {"event": (("type", "payload"), ("actor", "target", "location")),
           "correction": (("turn",), ()),
           "fact": (("extracts",), ())}


def _words(w):
    """The owner's words, exactly as given, or None when there are none (no letter or digit, a <placeholder>)."""
    shape = w.strip() if isinstance(w, str) else ""
    ok = isinstance(w, str) and any(ch.isalnum() for ch in w) and not (shape.startswith("<") and shape.endswith(">"))
    return w if ok else None


def _problem(code, text):
    """One flaw of an entry -> (its code, its text) - a call, as every refusal in the engine is raised through one, so
    the registry's two-way scan (tests/test_errors.py) reads the code where it is decided."""
    return code, text


def _entry_problems(i, e):
    """One entry's shape -> [(code, text)], [] when it is sound."""
    if not isinstance(e, dict):
        return [_problem("DECLARE_ENTRY_MALFORMED", "entry %d is not an object" % i)]
    kind = e.get("kind")
    if kind not in _FIELDS:
        return [_problem("DECLARE_ENTRY_MALFORMED", "entry %d's kind is %r - one of %s" % (i, kind,
                                                                                          ", ".join(_FIELDS)))]
    need, may = _FIELDS[kind]
    out = []
    if _words(e.get("words")) is None:
        out.append(_problem("DECLARE_WORDS_MISSING", "entry %d (%s) carries no owner's words" % (i, kind)))
    extra = sorted(set(e) - {"kind", "words"} - set(need) - set(may))
    if extra:
        out.append(_problem("DECLARE_ENTRY_MALFORMED", "entry %d (%s) carries %s, which nothing reads%s" % (
            i, kind, ", ".join(extra), " - a declaration never picks its own turn or source; the path sets both"
            if {"turn", "source"} & set(extra) else "")))
    missing = [f for f in need if f not in e]
    if missing:
        out.append(_problem("DECLARE_ENTRY_MALFORMED", "entry %d (%s) lacks %s" % (i, kind, ", ".join(missing))))
        return out
    wrong = []
    if kind == "event":
        wrong = (["type"] if not isinstance(e["type"], str) else []) + (["payload"] if not isinstance(e["payload"], dict)
                                                                      else []) + [
            f for f in may if e.get(f) is not None and not (isinstance(e[f], str) and e[f].strip())]
    elif kind == "correction":
        wrong = ["turn"] if isinstance(e["turn"], bool) or not isinstance(e["turn"], int) or e["turn"] < 0 else []
    else:
        rows, bad, blank = _extracts(e["extracts"])
        wrong = bad + blank + ([] if rows else ["extracts (none - an authored sentence indexing nothing binds nothing)"])
        try:                                           # the claims writer's own reading, before anything opens
            if not wrong:
                claims.extracts_of({"extracts": rows, "id": "entry %d" % i})
        except EngineError as exc:
            wrong.append(str(exc))
    if wrong:
        out.append(_problem("DECLARE_ENTRY_MALFORMED", "entry %d (%s): %s - the wrong type or empty"
                            % (i, kind, ", ".join(wrong))))
    return out


def _entries(path):
    """The declaration file -> (its bytes, its entries), refused whole on any flaw, before anything opens. A byte-order
    mark (as Windows PowerShell 5.1 writes one) is read past; the digest is of the bytes as they are."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        entries = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise RecordError("DECLARE_FILE_UNREADABLE", "%s: %s" % (path, exc))
    if not isinstance(entries, list) or not entries:
        raise RecordError("DECLARE_FILE_UNREADABLE", "%s holds %s - a declaration file is a non-empty LIST of entries"
                          % (path, "an empty list" if entries == [] else type(entries).__name__))
    problems = [p for i, e in enumerate(entries) for p in _entry_problems(i, e)]
    if problems:
        raise RecordError(problems[0][0], "nothing of %s was written: %s" % (path, "; ".join(t for _c, t in problems)))
    return raw, entries


def _world(led, run_id):
    """-> (the names the run knows, the places it names): its cast, and the people and places its pinned bible names."""
    names = {r[0] for r in led.con.execute("SELECT char_id FROM characters WHERE run_id = ?", (run_id,))}
    places, pinned = set(), bible.for_run(led.con, run_id)
    for eid, kind in led.con.execute("SELECT entity_id, kind FROM bible_entities WHERE fingerprint = ?",
                                     (pinned[0] if pinned else "",)):
        (places if kind == "location" else names).add(eid)
    return names, places


def _named(e):
    """An event entry -> ([(field, a name it gives)], [(field, a place it gives)]), as the fold would read them."""
    p = e["payload"]
    watch = p.get("watches") if isinstance(p.get("watches"), dict) else {}
    who = [(f, e[f]) for f in ("actor", "target") if e.get(f)] + [
        ("to", n) for n in (p.get("to") if e["type"] == "reveal" and isinstance(p.get("to"), list) else [])] + [
        ("watches.parties", n) for n in (watch.get("parties") if isinstance(watch.get("parties"), list) else [])]
    where = ([("location", e["location"])] if e.get("location") else []) + (
        [("to", p["to"])] if e["type"] == "move" and isinstance(p.get("to"), str) else []) + [
        ("watches.locations", n) for n in (watch.get("locations") if isinstance(watch.get("locations"), list) else [])]
    return who, where


def _check(led, run_id, entries):
    """Every entry against the run -> the plan to write, in the order it is written."""
    if led.con.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone() is None:
        raise RecordError("DECLARE_RUN_UNKNOWN", "the chronicle holds no run %r" % run_id)
    at = led.latest_turn(run_id)
    if at < 0:
        raise RecordError("DECLARE_RUN_EMPTY", "run %r has no committed turn yet - nothing for a declaration to land at"
                          % run_id)
    names, places = _world(led, run_id)
    turns = {r[0] for r in led.con.execute("SELECT turn FROM turns WHERE run_id = ?", (run_id,))}
    plan = {"at": at, "events": [], "corrections": [], "facts": []}
    for i, e in enumerate(entries):
        if e["kind"] == "event":
            who, where = _named(e)
            ghosts = ["%s %r" % (f, n) for f, n in who if n not in names]
            if ghosts:
                raise RecordError("DECLARE_NAME_UNKNOWN", "entry %d: %s - nobody run %r knows (its cast and the people "
                                  "its bible names: %s)" % (i, ", ".join(ghosts), run_id, ", ".join(sorted(names))))
            nowhere = ["%s %r" % (f, n) for f, n in where if n not in places]
            if nowhere:
                raise RecordError("DECLARE_PLACE_UNKNOWN", "entry %d: %s - no place run %r's bible names (%s)" % (
                    i, ", ".join(nowhere), run_id, ", ".join(sorted(places)) or "none"))
            plan["events"].append((i, dict({f: e[f] for f in ("actor", "target", "location") if e.get(f)},
                                           turn=at, type=e["type"], payload=e["payload"])))
        elif e["kind"] == "correction":
            if e["turn"] not in turns:
                raise RecordError("DECLARE_TURN_UNKNOWN", "entry %d corrects turn %d, which run %r never recorded"
                                  % (i, e["turn"], run_id))
            plan["corrections"].append((i, {"turn": e["turn"], "issue": e["words"]}))
        else:
            plan["facts"].append((i, e["words"], _extracts(e["extracts"])[0]))
    return plan


def _refusals(i, applied, rejected):
    """What the keeper's gates said of entry i's event -> [text]: refused, or kept only in part."""
    return (["entry %d: %s" % (i, reason) for _p, reason in rejected]
            + ["entry %d: kept only in part (%s)" % (i, ", ".join(map(str, a["extra"])) if isinstance(
                a["extra"], (list, tuple)) else a["extra"]) for a in applied if a.get("extra")])


def _write(led, run_id, plan):
    """Write the plan: corrections first (at the next tick), then events and facts (at the last committed turn) ->
    {"events": [{id, type, payload}], "utterances": [{id, said}]}, the rows written. Any refusal is raised naming its
    entry; on the rehearsal copy that is the whole answer, on the book it means the book changed since."""
    before = led.con.execute("SELECT COALESCE(MAX(event_id), 0) FROM events WHERE run_id = ?", (run_id,)).fetchone()[0]
    if plan["corrections"]:
        try:
            correct_run(led, run_id, {"continuity": [c for _i, c in plan["corrections"]]}, source=SOURCE)
        except EngineError as exc:
            raise RecordError("DECLARE_ENTRY_REFUSED", "the corrections (entries %s): %s" % (
                ", ".join(str(i) for i, _c in plan["corrections"]), exc))
    for i, p in plan["events"]:
        why = _refusals(i, *apply_proposals(led, run_id, [p], source=SOURCE, judge_at=plan["at"] + 1))
        if why:
            raise RecordError("DECLARE_ENTRY_REFUSED", "; ".join(why))
    uids = []
    for i, words, rows in plan["facts"]:
        try:
            uids.append({"id": claims.record(led.con, run_id, plan["at"], SOURCE, words, rows, tier=claims.AUTHORED),
                         "said": words})
        except EngineError as exc:
            raise RecordError("DECLARE_ENTRY_REFUSED", "entry %d: %s" % (i, exc))
    rows = led.con.execute("SELECT event_id, type, payload FROM events WHERE run_id = ? AND event_id > ? ORDER BY "
                           "event_id", (run_id, before)).fetchall()
    return {"events": [{"id": r[0], "type": r[1], "payload": json.loads(r[2])} for r in rows], "utterances": uids}


def _rehearse(dbp, run_id, entries):
    """The whole file, written on a throwaway copy of the database -> (the plan, what it wrote there). Raises what the
    writers refused, and the book is never opened for writing."""
    with tempfile.TemporaryDirectory(prefix="declare_rehearsal_", ignore_cleanup_errors=True) as tmp:
        led = Ledger(db.scratch_copy(dbp, os.path.join(tmp, "rehearsal.db")), create=False)
        try:
            plan = _check(led, run_id, entries)
            return plan, _write(led, run_id, plan)
        finally:
            led.con.close()


def _receipts(book_dir, digest):
    return os.path.join(book_dir, lineage.RUNS, "declarations", "%s.rows.jsonl" % digest[:16])


def _already(con, run_id, path):
    """A receipt of this file whose rows this database already holds, row for row -> it, or None."""
    try:
        with open(path, encoding="utf-8") as fh:
            receipts = [json.loads(line) for line in fh if line.strip()]
    except OSError:
        return None
    for r in receipts:
        if r.get("run") == run_id and all(_holds(con, run_id, e) for e in r.get("events") or []) and all(
                tuple(con.execute("SELECT speaker, said, tier FROM utterances WHERE run_id = ? AND utterance_id = ?",
                                  (run_id, u["id"])).fetchone() or ()) == (SOURCE, u["said"], claims.AUTHORED)
                for u in r.get("utterances") or []):
            return r
    return None


def _holds(con, run_id, e):
    """Does the database hold this event row - its id, type and payload?"""
    row = con.execute("SELECT type, payload FROM events WHERE run_id = ? AND event_id = ?", (run_id, e["id"])).fetchone()
    return row is not None and row[0] == e["type"] and json.loads(row[1]) == e["payload"]


def _keep(book_dir, raw, receipt):
    """The declaration file's bytes into the book, named by their sha256, and a receipt line of the rows written ->
    the kept path (never overwritten; the receipt only grows)."""
    digest = hashlib.sha256(raw).hexdigest()
    path = os.path.join(book_dir, lineage.RUNS, "declarations", "%s.json" % digest[:16])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.isfile(path):
        with open(path, "wb") as fh:
            fh.write(raw)
    with open(_receipts(book_dir, digest), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, sort_keys=True, ensure_ascii=True) + "\n")
    return path


def _counts(plan):
    return "%d event(s), %d correction(s), %d fact(s)" % (len(plan["events"]), len(plan["corrections"]),
                                                          len(plan["facts"]))


def _turns(path):
    led = Ledger(path, create=False)
    try:
        return led.con.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    finally:
        led.con.close()


def _declare(a, book_dir, raw, entries):
    """The flow, under the book's lease when it is adopted -> the lines to print."""
    dbp = drafts.writer_db(books.assert_db_for_book(book_dir, a.db), "declare.py", book_dir)[0]
    if not os.path.isfile(dbp):
        raise RecordError("DECLARE_RUN_UNKNOWN", "no chronicle at %s - a declaration lands in a run that was played, "
                          "and creates no database" % dbp)
    rec = None
    if drafts.adopted(book_dir):
        rec, role = drafts._record_role(book_dir)
        take = db.role_of(dbp)
        if take["parent"] != role["head"]:
            raise RecordError("DECLARE_DRAFT_STALE", "%s was taken from state %s and the record is state %s now - its "
                              "promote would be refused; open a new draft: python scripts/draft.py open --book \"%s\""
                              % (take["head"], take["parent"], role["head"], book_dir))
    led = Ledger(dbp, create=False)
    try:
        done = _already(led.con, a.run, _receipts(book_dir, hashlib.sha256(raw).hexdigest()))
    finally:
        led.con.close()
    if done:
        raise RecordError("DECLARE_ALREADY_DECLARED", "%s was declared into run %s at %s, and this database holds "
                          "every row it wrote" % (a.file, a.run, done.get("ts", "?")))
    plan, _ = _rehearse(dbp, a.run, entries)
    if a.dry_run:
        return ["would declare into run %s at turn %d: %s - source %s (rehearsed on a copy: nothing written)"
                % (a.run, plan["at"], _counts(plan), SOURCE)]
    led = Ledger(dbp, create=False)
    try:
        wrote = _write(led, a.run, plan)
    except EngineError as exc:                         # the rehearsal wrote it all: the book changed in between
        raise RecordError("DECLARE_ENTRY_REFUSED", "%s - after a rehearsal that wrote the whole file, so the database "
                          "changed in between and the entries before this one are written%s" % (
                              getattr(exc, "detail", exc), "; set the draft aside: python scripts/draft.py reject "
                              "--book \"%s\" --draft %s" % (book_dir, os.path.basename(dbp)[:-3]) if rec else ""))
    finally:
        led.con.close()
    receipt = dict(wrote, run=a.run, db=os.path.relpath(dbp, book_dir).replace(os.sep, "/"),
                   ts=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    rel = os.path.relpath(_keep(book_dir, raw, receipt), book_dir).replace(os.sep, "/")
    kept = os.path.join(book_dir, rel)
    skipped = len(plan["events"]) + len(plan["corrections"]) - len(wrote["events"])
    out = ["declared into run %s at turn %d: %s - source %s; wrote %d event row(s) and %d fact(s)%s; the file is kept "
           "at %s" % (a.run, plan["at"], _counts(plan), SOURCE, len(wrote["events"]), len(wrote["utterances"]),
                      " (%d correction(s) already recorded, not written again)" % skipped if skipped > 0 else "", rel)]
    if rec:
        did = os.path.basename(dbp)[:-3]
        lineage.append(book_dir, "declare", draft=did, run=a.run, file=rel, digest=lineage.digest(kept),
                       entries=len(entries), events=[e["id"] for e in wrote["events"]],
                       utterances=[u["id"] for u in wrote["utterances"]])
        played = _turns(dbp) - _turns(rec)
        land = "python scripts/draft.py promote --book \"%s\" --draft %s --approved \"<the owner's words, verbatim>\" " \
               "--by <owner or partner-relayed>" % (book_dir, did)
        out.append("the draft %s holds it. To land it, on the owner's yes: %s --in-advance" % (did, land) if played <= 0
                   else "the draft %s holds it and %d turn(s) played since it opened - those are approved after their "
                   "review (%s, without --in-advance); or declare on a fresh draft" % (did, played, land))
    return out


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="the author's hand: the owner's declarations, written into a run")
    ap.add_argument("--book", required=True, help="the book's slug or folder")
    ap.add_argument("--run", required=True, help="the run the declarations land in")
    ap.add_argument("--file", required=True, help="the declaration file: a JSON list of entries")
    ap.add_argument("--db", default=None, help="the database (an adopted book's open draft; default the book's own)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run", help="rehearse on a copy, write nothing")
    a = ap.parse_args(argv)
    try:
        book_dir = books.resolve(a.book)
    except EngineError as exc:
        print("declare.py: %s" % exc, file=sys.stderr)
        return 2
    try:
        raw, entries = _entries(a.file)
        drafts._only_books(book_dir)                   # a folder with no world/ is no book (review 1: a books root)
        with lineage.hold(book_dir, "declare") if drafts.adopted(book_dir) else contextlib.nullcontext():
            for line in _declare(a, book_dir, raw, entries):
                print(line)
    except EngineError as exc:
        print("declare.py: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
