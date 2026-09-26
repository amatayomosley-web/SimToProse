#!/usr/bin/env python3
"""release_guards.py — drop a book's record guards so the engine installs its own on the next open.

THE OWNER'S WAY OUT of DB_GUARD_VOCABULARY_SKEW (gate record-guards): a book whose guards another engine at this schema
version stamped - an old branch, a scratch build - is refused by this one, and when that engine is gone its guards
must go. The guards hold no data (they are triggers the engine builds from its own constants), so no row is touched;
a trigger without a record-guards stamp is someone else's and stays. The book is opened by `db.release_guards` - the
engine's one writable opener, never `db.connect`, which would refuse the book. One command in any shell - the
documented Python one-liner it replaces ran in Git Bash and not in PowerShell (Fable's read of the gate, 2026-09-26).

    python scripts/release_guards.py <book.db>

Exit status: 0 when released (or nothing to release), 1 when refused (a lock held past the busy timeout, a file that
is not a database), 2 when the file does not exist.
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import db                                            # noqa: E402
from src.engine.errors import EngineError                            # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="drop a book's record guards; the next open installs the engine's own")
    ap.add_argument("db", help="path to a chronicle .db")
    a = ap.parse_args(argv)
    try:
        dropped = db.release_guards(a.db)
    except (EngineError, sqlite3.Error) as exc:
        print("release_guards: %s" % exc, file=sys.stderr)
        return 2 if getattr(exc, "code", None) == "DB_PATH_INVALID" else 1
    print("dropped %d record guard(s)%s" % (len(dropped), (": " + ", ".join(dropped)) if dropped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
