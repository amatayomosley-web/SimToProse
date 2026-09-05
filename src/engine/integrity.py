"""integrity.py — what is WRONG with a database that a fresh one could not be wrong about.

THE MEASUREMENT THAT MADE THIS NECESSARY, on this repo's own chronicle files, 2026-09-02. The older
of the two sits at `PRAGMA user_version = 12` with five real runs, one still active. Open it with
`db.connect` — as every script does — and it migrates cleanly to v22: all forty append-only triggers
arrive, all five missing tables arrive, and **fifty of the sixty-eight per-column guards `schema.sql`
declares do not**. `INSERT INTO runs (run_id, ...) VALUES ('')` then succeeds. The second file, at
v1, is missing thirty-two. A database created fresh today is missing none.

The cause is one line of SQLite semantics: `_migrate` runs the whole of `schema.sql` through
`executescript`, and every CREATE is `CREATE TABLE IF NOT EXISTS`, so an EXISTING table keeps its
ORIGINAL definition. New tables arrive. New triggers arrive. New CONSTRAINTS on existing tables do
not, and SQLite offers no `ALTER` that adds a CHECK. The v21 version note said so. Nothing read it.

That is CLAUDE.md hard rule 2's shape exactly — *"a rule stated absolutely and enforced by habit is
a rule that has never been tested"* — one layer out: a wall declared in DDL and absent from the file
it was declared for.

TWO TIERS, and the split is what keeps this from becoming wallpaper.

  RED   — rows and state that are ACTUALLY wrong. Zero on both real databases; every one of them
          goes red on a fixture. This is the headline.
  AMBER — walls this database does not carry. Fifty on the older one, and permanent until a table
          rebuild. Reported as a COVERAGE line under the red count, never as the verdict, because a
          number that can only stay red is a number everyone learns to skip.

THE EXPECTATION IS DERIVED, never listed: a reference database is built in memory by executing
`schema.sql`, and the same predicate reads both sides. That symmetry is the load-bearing property —
a bug in the predicate mis-reads the reference and the live file IDENTICALLY and cancels, so this
check can under-report and cannot fabricate. `tests/test_integrity.py` pins it with a deliberately
broken predicate that must still report zero on a fresh database.

IT RAISES NOTHING, and that is a decision rather than an omission. `scripts/direct.py` and
`scripts/scene.py` construct their `Ledger` unguarded at top level, so a raise there aborts before a
single turn — and worse, `keeper.py`, `cut.py`, `critic.py` and `narrate.py` construct one the same
way, so the tools that would REPAIR what was found could not open the database to do it. The
findings carry a stable `kind` string in `faults.py`'s style and are NOT registered in `codes.py`:
that registry's second rule is that a listed code must be RAISED somewhere, and nothing here raises.
"""
import io
import os
import re
import sqlite3

_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

#: kind -> tier. RED is state that is wrong; AMBER is a wall this file does not carry.
TIERS = {
    "BREACH":                      "red",
    "ORPHAN-ROWS":                 "red",
    "CACHE-DIVERGED":              "red",
    "PHANTOM-TURN-ACTOR":          "red",
    "TURN-GAP":                    "red",
    "SCHEMA-TABLE-MISSING":        "amber",
    "APPEND-ONLY-TRIGGER-MISSING": "amber",
    "SCHEMA-GUARD-MISSING":        "amber",
}

#: printed by `render` on EVERY run, green included. A guard reports on what it READS, so a clean
#: result is a claim about coverage before it is a claim about content.
NOT_COVERED = (
    "this sweep does NOT cover:",
    "  * whether a PYTHON writer stands behind a missing wall — `ledger.append_scene` guards",
    "    `scenes.voice` and this cannot see that, so an ALTER-migrated column reports as a hole",
    "    forever even though nothing can write through it",
    "  * repair. Every missing guard needs a table REBUILD; SQLite cannot ALTER a CHECK in",
    "  * a write that left no trace. `PRAGMA recursive_triggers=ON` is set only in `db.connect`,",
    "    so any other opener has hard rule 2 disabled. The three that existed now open `mode=ro`",
    "    and `tests/test_integrity.py` refuses a new one, but a write that ALREADY happened leaves",
    "    nothing behind to find: the delta tables carry no timestamp or version column",
    "  * the CONTENT of a well-formed row. Nothing here reads a book",
)


def _guard(col, ddl):
    """The per-column emptiness guard in a CREATE TABLE text -> (kind, values) or None.

    This is `tests/test_place.py`'s `_guarded` predicate, extended to RETURN the enum members so the
    same parse that finds the wall also states what would walk through its absence. It is the ONE
    thing in this module that cannot be derived — SQLite exposes no pragma for CHECK constraints, so
    the DDL text must be read. What makes that safe is that it reads BOTH sides: see the module
    docstring's symmetry argument, and the broken-predicate control in `tests/test_integrity.py`.
    """
    if "%s <> ''" % col in ddl:
        return ("non-empty", None)
    e = re.search(r"CHECK\s*\(\s*%s\s+IN\s*\((.*?)\)" % re.escape(col), ddl, re.S)
    if e and "''" not in e.group(1):
        return ("enum", tuple(v.strip().strip("'") for v in e.group(1).split(",")))
    return None


def _tables(con):
    return {r[0]: (r[1] or "") for r in con.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def _triggers(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}


def _cols(con, table):
    return [r[1] for r in con.execute("PRAGMA table_info(%s)" % table)]


def reference(schema_path=None):
    """A database built by EXECUTING schema.sql, in memory. The expectation, never a list."""
    con = sqlite3.connect(":memory:")
    con.executescript(io.open(schema_path or _SCHEMA_PATH, encoding="utf-8").read())
    return con


def declared_guards(ref):
    """(table, column) -> (kind, values) for every guard schema.sql declares. Derived by walking
    the reference database's own columns, so a new table's column cannot slip past a name list."""
    out = {}
    for table, ddl in _tables(ref).items():
        for col in _cols(ref, table):
            g = _guard(col, ddl)
            if g:
                out[(table, col)] = g
    return out


def _finding(kind, subject, detail, count=None):
    return {"kind": kind, "tier": TIERS[kind], "subject": subject, "detail": detail, "count": count}


def _schema_tier(con, ref, findings):
    """AMBER, plus the RED that hides under it. Returns (declared, missing) for the coverage line."""
    live, expect = _tables(con), _tables(ref)
    for table in sorted(set(expect) - set(live)):
        findings.append(_finding("SCHEMA-TABLE-MISSING", table,
                                 "schema.sql declares this table; the database has no such table"))
    for name in sorted(_triggers(ref) - _triggers(con)):
        # a trigger for a table this database does not have is already reported above; naming it
        # again would double-count one fact.
        if name.rsplit("_no_", 1)[0] in live:
            findings.append(_finding("APPEND-ONLY-TRIGGER-MISSING", name,
                                     "schema.sql defines it; this database does not carry it"))

    declared = declared_guards(ref)
    missing = 0
    for (table, col), (kind, values) in sorted(declared.items()):
        if table not in live or col not in _cols(con, table):
            continue                                  # the missing TABLE is the finding, not this
        if _guard(col, live[table]):
            continue                                  # the wall is here
        missing += 1
        # THE RED THAT HIDES UNDER THE AMBER. The same derivation, pointed at ROWS: a wall this file
        # lacks is a coverage fact, but a row that holds what the wall forbids is a corruption fact,
        # and only the second one is worth waking someone for.
        if kind == "non-empty":
            sql = "SELECT COUNT(*) FROM %s WHERE %s = ''" % (table, col)
        else:
            sql = "SELECT COUNT(*) FROM %s WHERE %s NOT IN (%s)" % (
                table, col, ", ".join("'%s'" % v.replace("'", "''") for v in values))
        n = con.execute(sql).fetchone()[0]
        if n:
            findings.append(_finding(
                "BREACH", "%s.%s" % (table, col),
                "%d row(s) hold a value the current schema forbids (%s guard)" % (n, kind), n))
        findings.append(_finding(
            "SCHEMA-GUARD-MISSING", "%s.%s" % (table, col),
            "schema.sql guards this column (%s); this database's table does not" % kind))
    return len(declared), missing


def _orphans(con, findings):
    """A row scoped to a run that does not exist is invisible to every scoped query in the engine.

    NOT redundant with `PRAGMA foreign_key_check`, and this is measured rather than assumed:
    `schema.sql` declares `REFERENCES runs(run_id)` on seven tables and omits it on fourteen, so an
    orphan in `current_state` passes the pragma and is caught only by this anti-join. Both belong in
    the report; neither replaces the other.

    This is ALSO not a migration divergence — a brand-new v22 database accepts the same orphan. It
    is a standing schema gap, and saying so is the difference between a finding and a scare.
    """
    live = _tables(con)
    for table in sorted(live):
        if table == "runs" or "run_id" not in _cols(con, table):
            continue
        rows = [r[0] for r in con.execute(
            "SELECT DISTINCT run_id FROM %s WHERE run_id NOT IN (SELECT run_id FROM runs)" % table)]
        if rows:
            findings.append(_finding("ORPHAN-ROWS", table,
                                     "run_id(s) with no row in runs: %s%s"
                                     % (rows[:4], " ..." if len(rows) > 4 else ""), len(rows)))


def _per_run(con, findings, fold_check=None, known_cast=None):
    """The three checks that need a RUN rather than a schema.

    `fold_check` is `Ledger.divergence` when the caller has a writable ledger, and None when the
    database is open read-only — the sweep says which it did rather than reporting a silent pass.
    """
    if "runs" not in _tables(con):
        return
    for row in con.execute("SELECT run_id FROM runs ORDER BY run_id"):
        run_id = row[0]

        # D3 — the stale cache, found BEFORE resume hits it. `Ledger.resume` is the only other
        # place this comparison exists, and it runs for one run_id and only when --resume is
        # passed; `read_api.snapshot_at` reads the cache with no comparison at all.
        if fold_check is not None:
            diverged, detail = fold_check(run_id)
            if diverged:
                findings.append(_finding("CACHE-DIVERGED", run_id, detail))

        # D4a — an actor no one registered. `Ledger._seed` reads `characters` to seed the fold's
        # agents, but `_project` setdefaults ANY string an event names, so a phantom folds
        # identically both ways and `resume` returns OK on it. Measured: it does.
        #
        # The broader form — every folded `agents` key vs `characters` — is deliberately NOT here:
        # `bible_entities.kind` includes 'person', the walk-on cast, and a played character killing
        # a walk-on legitimately puts a non-`characters` id into `agents`. `turns.actor` has no
        # such case: every driver sources it from the registered cast.
        cast = {r[0] for r in con.execute(
            "SELECT char_id FROM characters WHERE run_id=?", (run_id,))} | set(known_cast or ())
        phantom = sorted({r[0] for r in con.execute(
            "SELECT DISTINCT actor FROM turns WHERE run_id=?", (run_id,))} - cast - {None})
        if phantom:
            findings.append(_finding("PHANTOM-TURN-ACTOR", run_id,
                                     "turn(s) committed by unregistered actor(s): %s" % phantom,
                                     len(phantom)))

        # D5 — a beat that vanished. Stated honestly: NO current driver can produce a gap, because
        # `turn_no` is recomputed from `latest_turn()` at every process start and only advances
        # after a successful `append_turn`. This is a standing guard against a future driver, and
        # the report says so rather than implying it caught something today.
        turns = {r[0] for r in con.execute("SELECT DISTINCT turn FROM turns WHERE run_id=?",
                                           (run_id,))}
        if turns:
            skipped = {r[0] for r in con.execute(
                "SELECT DISTINCT turn FROM events WHERE run_id=? AND type='turn-skipped'",
                (run_id,))}
            gaps = sorted(set(range(max(turns) + 1)) - turns - skipped)
            if gaps:
                findings.append(_finding("TURN-GAP", run_id,
                                         "no commit and no skip at turn(s) %s" % gaps[:8],
                                         len(gaps)))


def sweep(con, schema_path=None, fold_check=None, known_cast=None):
    """Everything wrong with this database -> [finding]. Reads only. Raises nothing.

    `con` may be a read-only connection: `scripts/doctor.py` opens with `mode=ro` deliberately,
    because `db.connect` MIGRATES on open and a doctor that opened normally would move
    `an aged chronicle db` from v12 to v22 — the diagnostic changing the thing it is diagnosing.
    """
    findings = []
    ref = reference(schema_path)
    try:
        declared, missing = _schema_tier(con, ref, findings)
        _orphans(con, findings)
        _per_run(con, findings, fold_check=fold_check, known_cast=known_cast)
    finally:
        ref.close()
    version = con.execute("PRAGMA user_version").fetchone()[0]
    for f in findings:
        f["user_version"] = version
        f["declared"] = declared
        f["missing"] = missing
    return findings


def schema_summary(con, schema_path=None):
    """(user_version, guards declared, guards this database is missing).

    Separate from `sweep` because the coverage numbers are the one thing worth printing when the
    finding list is EMPTY — a clean sweep still has to say how many walls it checked for, or the
    green reads as wider than it is.
    """
    ref = reference(schema_path)
    try:
        declared = declared_guards(ref)
        live = _tables(con)
        missing = sum(1 for (t, c) in declared
                      if t in live and c in _cols(con, t) and not _guard(c, live[t]))
    finally:
        ref.close()
    return con.execute("PRAGMA user_version").fetchone()[0], len(declared), missing


def counts(findings):
    """kind -> how many. Used by `render` and asserted directly by the tests."""
    out = {}
    for f in findings:
        out[f["kind"]] = out.get(f["kind"], 0) + 1
    return out


def render(findings, brief=False, label="", summary=None):
    """The report. RED first and by name; amber as one coverage line; the caveats every time.

    `brief=True` is what the drivers print at startup: the red tier in full, the amber as a single
    line. A driver that printed fifty missing-guard lines before every run would be muted inside a
    week, and a muted report is the reporter-nobody-reads this repo has named as its dominant
    defect class.
    """
    by_kind = counts(findings)
    red = [f for f in findings if f["tier"] == "red"]
    head = dict(findings[0]) if findings else {}
    if summary is not None:                            # the clean case still reports its coverage
        head["user_version"], head["declared"], head["missing"] = summary
    out = []
    version = head.get("user_version")
    out.append("integrity%s: %d red, %d amber%s"
               % (" [%s]" % label if label else "", len(red), len(findings) - len(red),
                  "" if version is None else "  (user_version=%d)" % version))
    for f in red:
        out.append("  !! %-20s %-28s %s" % (f["kind"], f["subject"], f["detail"]))
    if head.get("declared"):
        out.append("  -- schema.sql declares %d per-column guards; this database is missing %d"
                   % (head["declared"], head["missing"]))
        if head["missing"]:
            out.append("     (SQLite cannot ALTER a CHECK in, so a MIGRATED database keeps its "
                       "original columns — the Python writers are its only wall)")
    if not brief:
        for kind in sorted(k for k in by_kind if TIERS[k] == "amber"):
            out.append("  %-30s %d" % (kind, by_kind[kind]))
        for f in findings:
            if f["tier"] == "amber" and f["kind"] != "SCHEMA-GUARD-MISSING":
                out.append("     %-28s %s" % (f["subject"], f["detail"]))
        out.extend("  " + line for line in NOT_COVERED)
    return chr(10).join(out)


def startup_line(con, label=""):
    """The one line a DRIVER prints after opening its ledger -> str.

    A NAMED FUNCTION rather than an expression composed at each call site, and the reason is a
    coverage fact rather than tidiness: `tests/test_pipeline_e2e.py` MIRRORS `scene.py:main`'s
    orchestration instead of calling it, and nothing else invokes either driver's `main()`. So the
    call sites in `direct.py` and `scene.py` were checked by parsing their source and by nothing
    that RUNS — a TypeError in the expression would have shipped green. Behind one name, the thing
    the driver evaluates is the thing a test can execute.

    Brief by construction. A driver that printed fifty missing-guard lines before every run would be
    muted inside a week, and a muted report is the reporter-nobody-reads this repo has named as its
    dominant defect class.
    """
    return render(sweep(con), brief=True, label=label, summary=schema_summary(con))
