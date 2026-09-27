#!/usr/bin/env python3
"""ask.py — info requests to the engine, for the author's partner or the showrunner: one read, answered as JSON (gate
partner-contracts). The owner, 2026-09-27: "we also will need contracts for requesting info from the engine".

Every read goes through src/engine/read_api.py, as of the run's last turn unless --as-of; nothing is written (like
every engine reader, opening an older database brings its schema up to date). No database is created.

    python scripts/ask.py where  --book B                          the record's state, open drafts, each run's turns
    python scripts/ask.py scene  --book B --run R --turn T         what was done and said at that turn, and its scene
    python scripts/ask.py knows  --book B --run R --char C         what C knows
    python scripts/ask.py state  --book B --run R --char C         C's state
    python scripts/ask.py edges  --book B --run R --char C --with D   how C stands toward D
    python scripts/ask.py facts  --book B --run R --subject S      the facts in force on a subject
    python scripts/ask.py place  --book B --run R --place P        a place, as the world holds it
    [--db PATH]  a draft instead of the book's own database
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import books, drafts, read_api                      # noqa: E402
from src.engine.errors import EngineError                           # noqa: E402
from src.engine.ledger import Ledger                                # noqa: E402

_NEEDS = {"where": (), "scene": ("run", "turn"), "knows": ("run", "char"), "state": ("run", "char"),
          "edges": ("run", "char", "with_"), "facts": ("run", "subject"), "place": ("run", "place")}


def _where(book_dir, led):
    """The book at a glance: its record (drafts.listing) and each run's turns."""
    got = drafts.listing(book_dir)
    runs = [{"run": r[0], "status": r[1], "turns": r[2], "last_turn": r[3]} for r in led.con.execute(
        "SELECT r.run_id, r.status, COUNT(t.turn), MAX(t.turn) FROM runs r LEFT JOIN turns t ON t.run_id = r.run_id "
        "GROUP BY r.run_id ORDER BY r.rowid")] if led else []
    return {"book": book_dir, "record": got["record"], "drafts": got["drafts"], "aside": got["aside"],
            "approvals": got["log"], "warnings": got["gaps"] + [("orphaned directions: %s" % o) for o in got["orphans"]],
            "runs": runs}


def _read(a, led):
    at = a.as_of if a.as_of is not None else led.latest_turn(a.run)
    if a.what == "scene":
        return {"said": read_api.said(led.con, a.run, a.turn).as_dict(),
                "scene": read_api.scene_of(led.con, a.run, a.turn).as_dict()}
    call = {"knows": lambda: read_api.knows(led.con, a.run, a.char, at),
            "state": lambda: read_api.state(led.con, a.run, a.char, at),
            "edges": lambda: read_api.edges(led.con, a.run, a.char, a.with_, at),
            "facts": lambda: read_api.established(led.con, a.run, [a.subject], at),
            "place": lambda: read_api.place(led.con, a.run, a.place, at)}[a.what]
    return call().as_dict()


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="an info request to the engine, answered as JSON")
    ap.add_argument("what", choices=tuple(_NEEDS))
    ap.add_argument("--book", required=True, help="the book's slug or folder")
    ap.add_argument("--db", default=None, help="a draft (default: the book's own database)")
    ap.add_argument("--run")
    ap.add_argument("--turn", type=int)
    ap.add_argument("--char")
    ap.add_argument("--with", dest="with_")
    ap.add_argument("--subject")
    ap.add_argument("--place")
    ap.add_argument("--as-of", dest="as_of", type=int, default=None)
    a = ap.parse_args(argv)
    missing = ["--" + f.rstrip("_") for f in _NEEDS[a.what] if getattr(a, f) is None]
    if missing:
        ap.error("%s needs %s" % (a.what, ", ".join(missing)))
    try:
        book_dir = books.resolve(a.book)
        dbp = books.assert_db_for_book(book_dir, a.db)
        led = Ledger(dbp, create=False) if os.path.isfile(dbp) else None
        try:
            if a.what != "where" and led is None:
                raise EngineError("ASK_NO_CHRONICLE", "no chronicle at %s yet - nothing to read" % dbp)
            out = _where(book_dir, led) if a.what == "where" else _read(a, led)
        finally:
            if led is not None:
                led.con.close()
    except EngineError as exc:
        print("ask.py: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
