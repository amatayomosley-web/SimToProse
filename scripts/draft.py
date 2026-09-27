#!/usr/bin/env python3
"""draft.py — a book's approval flow: adopt its record, open a draft, promote it on the owner's words, reject, rewind.

The owner, 2026-09-26: "a scene is draft until it's approved and then it's saved into record." Once a book is ADOPTED,
its database is the record and no writer touches it - scene.py, direct.py, critic --correct, cut --edl and keeper
--propose / --rule --rulings all refuse it up front, and on an adopted book they write only a draft this command
opened. The work runs on a DRAFT, a copy the drivers take as --db; the owner's yes makes it the record (promote), and
the record as it was is kept (runs/history) so a rewind can bring it back (restore). Every change is logged with the
owner's words exactly as given in <book>/runs/lineage.jsonl (src/engine/drafts.py, src/engine/lineage.py; gates
record-role and draft-flow).

    python scripts/draft.py adopt   --book <slug|path> [--new]   (--new: a book with no database yet starts empty)
    python scripts/draft.py open    --book B [--note "what this take tries"]      -> prints the draft's path
    python scripts/draft.py list    --book B
    python scripts/draft.py reject  --book B --draft d3 [--why "..."]    (sets any file in runs/drafts aside)
    python scripts/draft.py promote --book B --draft d3 --approved "<the owner's words>" --by owner|partner-relayed
                                    [--in-advance]   (a dictated change: the yes came before the work)
    python scripts/draft.py restore --book B --to d2 --approved "<the owner's words>" --by owner|partner-relayed

Output is UTF-8 whatever the console or pipe (review 1: a cp1252 pipe had turned an accented book path into a path
that was not the file, and crashed `list` on a character outside cp1252).

Exit status: 0 done (notes on anything left in place are printed), 1 refused (the refusal names its code), 2 the book
could not be found.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import books, drafts                                 # noqa: E402
from src.engine.errors import EngineError                            # noqa: E402


def _show(book_dir):
    got = drafts.listing(book_dir)
    rec = got["record"]
    print("book: %s" % book_dir)
    print("record: %s" % ("none yet" if rec is None else "%s  role %s  state %s%s" % (
        rec["file"], rec["role"].upper() if rec["role"] == "missing" else rec["role"], rec["head"] or "-",
        ("  (from %s)" % rec["parent"]) if rec["parent"] else "")))
    for d in got["drafts"]:
        print("draft %s  from %s  %s%s" % (d["draft"], d["parent"] or "?", d["state"],
                                          ("  - " + d["note"]) if d["note"] else ""))
    for where, ids in sorted(got["aside"].items()):
        print("%s: %s" % (where, ", ".join(ids) or "none"))
    print("history: %s" % (", ".join(got["history"]) or "none"))
    for e in got["log"]:
        print("  %s %-7s %s" % (e["ts"], e["op"], ", ".join("%s=%s" % (k, str(e[k]).replace("\r", "\\r").replace("\n", "\\n"))
                                                          for k in sorted(e) if k not in ("ts", "op", "digest"))))
    for gap in got["gaps"]:
        print("WARNING: %s - a promote or restore was cut short after it landed; the record is intact, and the copy "
              "it kept is logged" % gap)
    for did in got["orphans"]:
        print("WARNING: runs/drafts/%s.db.directions has no database beside it - a set-aside cut short between its two "
              "moves left it; the database is in drafts/rejected, drafts/stale or drafts/promoted" % did)
    if got["torn"]:
        print("WARNING: the lineage log's last line was cut off mid-write (%d bytes); the next change marks it and "
              "carries on" % got["torn"])


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="a book's approval flow: drafts, promote, reject, restore")
    ap.add_argument("command", choices=("adopt", "open", "list", "reject", "promote", "restore"))
    ap.add_argument("--book", required=True, help="the book's slug or folder")
    ap.add_argument("--new", action="store_true", help="adopt: start the record empty (a book with no database yet)")
    ap.add_argument("--draft", help="the draft's id (reject, promote)")
    ap.add_argument("--to", help="the state to restore (restore)")
    ap.add_argument("--approved", help="the owner's words, verbatim (promote, restore)")
    ap.add_argument("--by", help="who gave the yes: owner or partner-relayed (promote, restore)")
    ap.add_argument("--in-advance", action="store_true", dest="in_advance",
                    help="promote: the yes came before the work (a dictated ruling, correction, cut or declaration)")
    ap.add_argument("--note", default="", help="open: what this draft tries")
    ap.add_argument("--why", default="", help="reject: why")
    a = ap.parse_args(argv)
    try:
        book_dir = books.resolve(a.book)
    except EngineError as exc:
        print("draft.py: %s" % exc, file=sys.stderr)
        return 2
    try:
        if a.command == "adopt":
            e = drafts.adopt(book_dir, a.new)
            print("adopted: %s is the record, state %s - writers now run on a draft (draft.py open)" % (e["file"], e["head"]))
        elif a.command == "open":
            path = drafts.open_draft(book_dir, a.note)
            print("draft: %s" % path)
            print("write it with --db \"%s\". To land it, on the owner's yes: python scripts/draft.py promote --book "
                  "\"%s\" --draft %s --approved \"<the owner's words, verbatim>\" --by <owner or partner-relayed>"
                  % (path, book_dir, os.path.basename(path)[:-3]))
        elif a.command == "list":
            _show(book_dir)
        elif a.command == "reject":
            e = drafts.reject(book_dir, a.draft, a.why)
            print("set aside: %s -> %s" % (a.draft, e["file"]))
        elif a.command == "promote":
            e, notes = drafts.promote(book_dir, a.draft, a.approved, a.by, a.in_advance)
            print("promoted: %s is the record (from %s); the previous record is kept at %s" % (e["head"], e["parent"],
                                                                                            e["history"]))
            for n in notes:
                print("  note: %s" % n)
        else:
            e, notes = drafts.restore(book_dir, a.to, a.approved, a.by)
            print("restored: the record is state %s again; what it held (%s) is kept at %s" % (e["head"], e["kept_head"],
                                                                                            e["kept"]))
            for n in notes:
                print("  note: %s" % n)
    except EngineError as exc:
        print("draft.py %s: %s" % (a.command, exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
