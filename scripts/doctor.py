#!/usr/bin/env python3
"""doctor.py — what is wrong with a chronicle database, read-only.

WHY IT OPENS READ-ONLY, and this is the whole reason the CLI exists rather than a one-liner:
`db.connect` MIGRATES on open (`db.py:_migrate`). A doctor that opened normally would move this
repo's own v12 chronicle to v22 on the way to examining it — the diagnostic changing the thing it is
diagnosing, and destroying the evidence in the same motion. `mode=ro` reads a live WAL database
correctly and refuses writes. `immutable=1` does NOT: measured 2026-09-02, it fails outright on a
hot WAL, so it is not used.

Two tiers, because a number that can only stay red is a number everyone learns to skip:

    RED    rows and state that are ACTUALLY wrong. Zero on every real database in this repo.
    AMBER  walls this file does not carry. Fifty on the oldest one here, permanent until a rebuild.

`--fold` additionally opens the database WRITABLE (and therefore migrates it) so the snapshot-vs-log
divergence check can run. It is off by default for exactly the reason above, and the report says
which mode it ran in rather than reporting a silent pass on a check it never performed.

Exit status: 1 if anything RED, else 0. The amber tier never fails the command — it is coverage.
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import integrity                                     # noqa: E402


def open_readonly(path):
    """A connection that cannot write and cannot migrate."""
    uri = "file:%s?mode=ro" % os.path.abspath(path).replace("\\", "/")
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    return con


def examine(path, fold=False):
    """-> (findings, summary). `fold` trades read-only for the cache-divergence check."""
    if fold:
        from src.engine.ledger import Ledger           # migrates on open — the documented trade
        led = Ledger(path)
        try:
            return (integrity.sweep(led.con, fold_check=lambda r: led.divergence(r)[:2]),
                    integrity.schema_summary(led.con))
        finally:
            led.con.close()
    con = open_readonly(path)
    try:
        return integrity.sweep(con), integrity.schema_summary(con)
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser(
        description="report what is wrong with a chronicle database — reads, never repairs",
        epilog="A MIGRATED database keeps its original columns: SQLite cannot ALTER a CHECK in, so "
               "every guard added after that database was created is absent from it and the Python "
               "writers are its only wall. That is what the amber tier counts.")
    ap.add_argument("db", nargs="+", help="path(s) to a chronicle .db")
    ap.add_argument("--fold", action="store_true",
                    help="also compare each run's cached snapshot against a from-zero fold. Opens "
                         "the database WRITABLE, which migrates it — off by default")
    ap.add_argument("--brief", action="store_true", help="red tier and the coverage line only")
    args = ap.parse_args()

    worst = 0
    for path in args.db:
        if not os.path.exists(path):
            print("%s: no such file" % path)
            worst = 1
            continue
        findings, summary = examine(path, fold=args.fold)
        print(integrity.render(findings, brief=args.brief,
                               label=os.path.basename(path), summary=summary))
        if not args.fold:
            print("  -- CACHE-DIVERGED not checked (read-only); re-run with --fold to include it")
            # TWO NUMBERS FOR ONE FILE, and both are true. Read-only, this counts the guards missing
            # from the tables AS THEY ARE. Opening writable MIGRATES, and `db.py:_migrate` adds
            # `scenes.voice`, `scenes.knowledge` and `relationship_deltas.ord` by ALTER — which
            # cannot carry the CHECKs schema.sql declares for them — so the count RISES after the
            # first normal open. The module docstring and the drivers' startup line print the larger
            # figure because they run on an already-migrated connection. Measured 2026-09-02 on this
            # repo's two chronicles: 48 -> 50 and 31 -> 32.
            print("  -- this count is BEFORE migration; a normal open adds the ALTER-added columns "
                  "(voice, knowledge, ord), which cannot carry their declared CHECKs")
        # PRAGMA integrity_check is the one check that sees PHYSICAL page corruption, which nothing
        # else here can: every other check reads rows that SQLite was willing to hand back.
        con = open_readonly(path)
        try:
            phys = con.execute("PRAGMA integrity_check").fetchone()[0]
            fk = con.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            con.close()
        if phys != "ok":
            print("  !! PAGE-CORRUPTION        %s" % phys)
            worst = 1
        if fk:
            # Reported ALONGSIDE the anti-join, never instead of it: schema.sql declares
            # REFERENCES runs(run_id) on seven tables and omits it on fourteen, so this pragma is
            # blind to an orphan in `current_state` that ORPHAN-ROWS catches. Measured.
            print("  !! FK-VIOLATION           %d row(s) across %d table(s)"
                  % (len(fk), len({r[0] for r in fk})))
            worst = 1
        if any(f["tier"] == "red" for f in findings):
            worst = 1
        print()
    return worst


if __name__ == "__main__":
    sys.exit(main())
