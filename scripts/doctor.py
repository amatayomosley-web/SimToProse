#!/usr/bin/env python3
"""doctor.py — what is wrong with a chronicle database, read-only.

WHY IT OPENS READ-ONLY, and this is the whole reason the CLI exists rather than a one-liner:
`db.connect` MIGRATES on open (`db.py:_migrate`). A doctor that opened normally would move an
old chronicle up to `db.SCHEMA_VERSION` on the way to examining it — the diagnostic changing the thing it is
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

from src.engine import claims                                        # noqa: E402  (the lore debt)
from src.engine import integrity                                     # noqa: E402


def open_readonly(path):
    """A connection that cannot write and cannot migrate."""
    uri = "file:%s?mode=ro" % os.path.abspath(path).replace("\\", "/")
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    return con


def _lore_debt(con):
    """Every run in this database with sayings the fence cannot see yet -> a list of
    `claims.unextracted` results (one per run, count > 0 only), each carrying its own `run_id`.

    A SEPARATE pass from `integrity.sweep`, deliberately: this file's FILES do not include
    `src/engine/integrity.py`, and `sweep`'s findings carry a `kind` that `render` looks up in its
    own module-level `TIERS` — a kind this function invented would KeyError there. `_per_run`-shaped
    (one query per run_id) without touching the module it is shaped after.
    """
    have_runs = con.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='runs'").fetchone()[0]
    if not have_runs:
        return []
    out = []
    for row in con.execute("SELECT run_id FROM runs ORDER BY run_id"):
        debt = claims.unextracted(con, row[0])
        if debt["count"]:
            out.append(dict(debt, run_id=row[0]))
    return out


def _corrections(con):
    """Every run in this database with `correction` events -> [{run_id, count}], count > 0 only.

    DETECTOR #6 (`docs/measurement.md` s3): "correction RATE is detector #6 — a rising rate = the
    recorder degrading". This is the count half; the rate is a count against a run's turns, which
    the reader does here rather than the doctor inventing a threshold it has never calibrated.

    `_lore_debt`-shaped, and for the same reason: this file's gate does not touch
    `src/engine/integrity.py`, and a `kind` invented here would KeyError in `integrity.render`'s
    own TIERS table. Guarded on the table's existence like `_lore_debt` is on `runs`, so an old or
    partial chronicle reports nothing instead of raising."""
    have = con.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('runs','events')").fetchone()[0]
    if have < 2:
        return []
    return [{"run_id": r["run_id"], "count": r["n"]} for r in con.execute(
        "SELECT run_id, COUNT(*) AS n FROM events WHERE type='correction' "
        "GROUP BY run_id ORDER BY run_id")]


def examine(path, fold=False):
    """-> (findings, summary, lore, corrections). `fold` trades read-only for the cache-divergence
    check; the lore debt (`_lore_debt`) and the correction count (`_corrections`) are read the same
    way regardless — both are counts over rows, not migration-coverage questions."""
    if fold:
        from src.engine.ledger import Ledger           # migrates on open — the documented trade
        led = Ledger(path)
        try:
            return (integrity.sweep(led.con, fold_check=lambda r: led.divergence(r)[:2]),
                    integrity.schema_summary(led.con), _lore_debt(led.con), _corrections(led.con))
        finally:
            led.con.close()
    con = open_readonly(path)
    try:
        return (integrity.sweep(con), integrity.schema_summary(con),
                _lore_debt(con), _corrections(con))
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
        findings, summary, lore, corrections = examine(path, fold=args.fold)
        print(integrity.render(findings, brief=args.brief,
                               label=os.path.basename(path), summary=summary))
        if corrections and not args.brief:
            # NOT A FAULT — a MEASUREMENT (measurement.md detector #6). A correction is the record
            # repenting in the open, which is the protocol working; what the reader watches is the
            # rate rising across runs. Printed only when there are some, like every other line here.
            for row in corrections:
                print("     %-28s %d correction(s) — the fold treats the events they name as "
                      "superseded" % (row["run_id"], row["count"]))
        if lore and not args.brief:
            # SAME GRAMMAR integrity.render uses for its own amber tier (a kind+count line, then a
            # subject+detail line per finding) — printed here rather than folded into `findings`
            # because this file's gate does not touch integrity.py (see _lore_debt).
            print("  %-30s %d" % ("LORE-UNEXTRACTED", len(lore)))
            for row in lore:
                print("     %-28s %d utterance(s) unextracted (turns %s-%s) — the fence cannot "
                      "see them" % (row["run_id"], row["count"], row["first_turn"], row["last_turn"]))
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
