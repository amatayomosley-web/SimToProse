"""guards.py — the record's second wall on every database the engine opens: insert guards built from the vocabularies
and ranges the record layer checks.

WHY (gate record-guards, 2026-09-26; G6 of the contracts plan the owner approved). schema.sql held eleven columns only
to "not empty" where the record layer refuses anything outside a closed vocabulary - relationship_deltas.axis and .ord,
rest_declared.axis, toward_deltas.primary_, target_binds.primary_, wound_minted.path and .concept, readings.path, .rung
and .confidence, utterances.tier - three deltas and a scar's intensity to no range at all, and a law's statement to
NOT NULL only. And a database migrated from before a table's CHECK carries none of it: SQLite cannot ALTER a CHECK in,
and every book database is a migrated one. A rebuild would put a CHECK in, but it copies the history through it, and
three of the 79 book databases measured on 2026-09-26 hold rows written under the emotion names retired on 2026-09-08
or an older spelling of a relationship order - they would refuse to migrate; and the vocabularies move (records.PATHS
was rekeyed that day, the concept registry grows), which a CHECK can follow only by another rebuild.

So: one BEFORE INSERT trigger per guarded table, `<table>_record_guard`, its SQL built here from the constant the record
layer checks - never a copy of it - and installed by db.connect on every open where it is missing or differs from what
the constants give (a write only then). Every guarded table is append-only (its UPDATE and DELETE triggers refuse), so
INSERT is its only way in.

ONE WALL PER SCHEMA VERSION, held at run time (the gate's reviews: whichever engine opened a book last owned its guard,
so two checkouts with different words replaced each other's wall on open and refused each other's validated beats; a
pin in the suite alone was defeated by editing it; and a check of our own guards' words missed a guard retired, or one
added on another table). Each guard carries a stamp - the schema version that installed it, the fingerprint of its
table's words and bounds, and the WALL's, `vocabulary()` of every guard (no message text, no row order). An engine
meeting any trigger stamped at its own version, or a later one, with another wall REFUSES the book
(DB_GUARD_VOCABULARY_SKEW) instead of replacing it: the first engine's wall stands until the version steps. A guard from
an older version is replaced, as any migration replaces what it supersedes; the suite pins `vocabulary()` to
db.SCHEMA_VERSION so the step is not forgotten. What is left: an engine that steps a book while an OLDER one is
mid-scene in it upgrades the wall under the running one; a beat the new wall refuses is named DB_GUARD_REFUSED, not a
bare rollback.

A GUARD NEVER REFUSES WHAT THE RECORD LAYER ACCEPTS. Each mirrors a check made on every writer path of its column
(the record classes' validate, readings.write, wound.write_mints, law._normalise_law via bible.build; utterances are
written by claims.write with the default tier, or by claims.record, which checks it), so it fires only for a writer that
is not the engine - a script, an sqlite3 shell, a future writer that skipped the record layer - and says so with the
record layer's own code. Where SQLite reads a value more loosely than Python (a text number into a REAL column, a tab
in a law's statement), the guard is the weaker, never the stricter. A guard reads only the row being written: history
written under another vocabulary stays as it was, and `legacy_counts` counts what today's guard would refuse
(integrity reports it as LEGACY-ROWS, never as red).

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

import hashlib
import json
import re

from . import claims, concepts, readings, records, rungs

SUFFIX = "_record_guard"
#: every refusal a guard raises carries this, so the ledger can tell a guard's refusal from any other constraint's
MARK = "(gate record-guards)"
#: tables an older version guarded and this one no longer does - their guards are dropped on open. Only these and the
#: tables in GUARDS are ever touched: a trigger of someone else's that merely ends in SUFFIX is theirs.
RETIRED = ()
_STAMP = re.compile(r"-- record-guards v(\d+) vocabulary ([0-9a-f]{16}) wall ([0-9a-f]{16})")
_MARKER = re.compile(r"-- record-guards v(\d+)")          # any stamp's version, whatever its format


def _ladder():
    """{path: its rung names} for every path a reading may name - the ladders `rungs.index_of` resolves against."""
    return {p: tuple(rungs.names_on(p)) for p in sorted(rungs.BANDS)}


#: (table, column(s), kind, what the column must be, the record layer's own code, where the rule lives). kind "one-of":
#: `allowed()` returns the words; "range": the bounds; "rung": a (path, rung) pair on a ladder; "not-blank": text with
#: something in it. `allowed` reads the module attribute on every build, so the guard follows the constant.
GUARDS = (
    ("relationship_deltas", "axis", "one-of", lambda: records.RELATIONSHIP_AXES, "RECORD_AXIS_UNKNOWN",
     "records.RELATIONSHIP_AXES"),
    ("relationship_deltas", "ord", "one-of", lambda: records.RELATIONSHIP_ORDERS, "RECORD_ORDER_UNKNOWN",
     "records.RELATIONSHIP_ORDERS"),
    ("relationship_deltas", "delta", "range", lambda: records.DELTA_RANGE, "RECORD_DELTA_RANGE",
     "records.DELTA_RANGE"),
    ("rest_declared", "axis", "one-of", lambda: records.RELATIONSHIP_AXES, "RECORD_AXIS_UNKNOWN",
     "records.RELATIONSHIP_AXES"),
    ("toward_deltas", "primary_", "one-of", lambda: records.PATHS, "RECORD_PRIMARY_UNKNOWN", "records.PATHS"),
    ("toward_deltas", "delta", "range", lambda: records.DELTA_RANGE, "RECORD_DELTA_RANGE", "records.DELTA_RANGE"),
    ("target_binds", "primary_", "one-of", lambda: records.PATHS, "RECORD_LIST_ITEM_TYPE", "records.PATHS"),
    ("wound_deltas", "delta", "range", lambda: records.DELTA_RANGE, "RECORD_DELTA_RANGE", "records.DELTA_RANGE"),
    ("wound_minted", "path", "one-of", lambda: records.PATHS, "WOUND_PATH_UNKNOWN", "records.PATHS"),
    ("wound_minted", "concept", "one-of", lambda: tuple(concepts.REGISTRY), "WOUND_CONCEPT_UNKNOWN",
     "concepts.REGISTRY"),
    ("wound_minted", "intensity", "range", lambda: records.INTENSITY_RANGE, "WOUND_INTENSITY_RANGE",
     "records.INTENSITY_RANGE"),
    ("readings", ("path", "rung"), "rung", _ladder, "READING_RUNG_NOT_ON_PATH", "the ladders (rungs.names_on)"),
    ("readings", "confidence", "one-of", lambda: readings.CONFIDENCE_WORDS, "READING_CONFIDENCE_UNKNOWN",
     "readings.CONFIDENCE_WORDS"),
    ("utterances", "tier", "one-of", lambda: claims.TIERS, "CLAIM_TIER_UNKNOWN", "claims.TIERS"),
    ("bible_laws", "statement", "not-blank", lambda: None, "BIBLE_LAW_STATEMENT_MISSING", "law._normalise_law"),
)


def _q(s):
    """An SQL string literal."""
    return "'%s'" % str(s).replace("'", "''")


def _ident(name):
    """An SQL identifier, quoted."""
    return '"%s"' % str(name).replace('"', '""')


def _words(values):
    return "(%s)" % ", ".join(_q(v) for v in values)


def _column(col):
    return "+".join(col) if isinstance(col, tuple) else col


def _version(version):
    if version is None:
        from . import db                               # at call time: db imports this module
        version = db.SCHEMA_VERSION
    return int(version)


def refused(guard, row="NEW."):
    """The SQL condition under which `guard` refuses a row -> str. `row` is "NEW." inside the trigger and "" when the
    same condition counts rows already written (`legacy_counts`): one predicate, read both ways. A NULL is refused by
    the guard's own code, before NOT NULL's generic message."""
    _table, col, kind, allowed, _code, _where = guard
    if kind == "one-of":
        c = row + col
        return "%s IS NULL OR %s NOT IN %s" % (c, c, _words(allowed()))
    if kind == "range":
        lo, hi = allowed()
        c = row + col
        return "typeof(%s) NOT IN ('integer', 'real') OR %s < %r OR %s > %r" % (c, c, lo, c, hi)
    if kind == "rung":
        path, rung = row + col[0], row + col[1]
        ok = " OR ".join("(%s = %s AND %s IN %s)" % (path, _q(p), rung, _words(names))
                         for p, names in allowed().items())
        return "%s IS NULL OR %s IS NULL OR NOT (%s)" % (path, rung, ok)
    if kind == "not-blank":
        c = row + col
        return "%s IS NULL OR trim(%s) = ''" % (c, c)
    raise records.RecordError("RECORD_GUARD_KIND_UNKNOWN", "guards: %s.%s names kind %r, which no builder here reads"
                              % (guard[0], _column(col), kind))


def _canonical(guard):
    """`guard` holding its constant in one canonical form - words sorted, bounds as floats, ladders by path - so its
    predicate can be fingerprinted free of the constant's order."""
    kind, allowed = guard[2], guard[3]()
    if kind == "one-of":
        allowed = tuple(sorted(str(v) for v in allowed))
    elif kind == "range":
        allowed = (float(allowed[0]), float(allowed[1]))
    elif kind == "rung":
        allowed = {p: tuple(sorted(str(n) for n in names)) for p, names in sorted(allowed.items())}
    return guard[:3] + ((lambda: allowed),) + guard[4:]


def vocabulary(table=None):
    """The fingerprint of what the guards refuse - of one table, or of all -> 16 hex: EVERYTHING in the trigger but its
    message - the statement each guard runs (`_raise` with no message, over its canonical constant: the words, bounds
    or ladders, the predicate, the RAISE kind) and the trigger's own shape (`_TRIGGER`: when it fires, on what).
    Review 4: a same-version engine that changed only how a guard compares its words carried stamps identical to this
    one's; a timing, a RAISE(IGNORE) or a WHEN clause would have too. No message text and no row order: a reworded
    refusal is not another vocabulary, and a moved word or a changed test is."""
    rows = sorted([g[0], _column(g[1]), g[2], _raise(_canonical(g), message=False)]
                  for g in GUARDS if table is None or g[0] == table)
    shape = _TRIGGER % ("<name>", "<table>", 0, "<vocabulary>", "<wall>", "<statements>")
    return hashlib.sha256(json.dumps([shape, rows], sort_keys=True).encode("utf-8")).hexdigest()[:16]


def stamp(sql):
    """A guard's stamp -> (the schema version that installed it, its table's vocabulary, the whole wall's), or None when
    it carries none. The WALL is `vocabulary()` of every guard the installing engine had: a guard it retired, or one on
    a table another engine does not guard, changes it as surely as a moved word (review 3). A stamp this engine cannot
    read - another format, another field order, a field missing - keeps its version: (version, None, None), so at this
    version or a later one it is another engine's, never "no stamp" (review 4: one was replaced as unstamped)."""
    m = _STAMP.search(sql or "")
    if m:
        return (int(m.group(1)), m.group(2), m.group(3))
    m = _MARKER.search(sql or "")
    return (int(m.group(1)), None, None) if m else None


_SAYS = {"one-of": "is not one of %s", "range": "is not a number in %s",
         "rung": "is not a rung on that path's ladder (%s)", "not-blank": "is blank, which %s refuses"}


#: the one trigger every guarded table gets, and the one statement per guard in it - read by `expected` to build the
#: triggers and by `vocabulary` to fingerprint them, so the shape cannot move without the wall moving
_TRIGGER = "CREATE TRIGGER %s BEFORE INSERT ON %s\nBEGIN\n  -- record-guards v%d vocabulary %s wall %s\n%s\nEND"
_STATEMENT = "  SELECT RAISE(ABORT, %s) WHERE %s;"


def _raise(guard, message=True):
    """A guard's statement in its trigger; with `message` False, the same statement with a fixed placeholder for its
    message - what `vocabulary` fingerprints."""
    table, col, kind, _allowed, code, where = guard
    cond = refused(guard)                              # first: an unknown kind is refused by its code, not a KeyError
    msg = ("%s: %s.%s %s - the database refuses what the record layer refuses %s"
           % (code, table, _column(col), _SAYS[kind] % where, MARK)) if message else "<message>"
    return _STATEMENT % (_q(msg), cond)


def expected(tables=None, version=None):
    """{trigger name: its CREATE statement} for every guarded table (of `tables`, when given), built from the constants
    as they are now and stamped with `version` (the engine's own by default). Deterministic: the same constants and
    version give the same text, byte for byte."""
    version, wall = _version(version), vocabulary()
    out = {}
    for table in sorted({g[0] for g in GUARDS}):
        if tables is not None and table not in tables:
            continue
        body = "\n".join(_raise(g) for g in GUARDS if g[0] == table)
        name = table + SUFFIX
        out[name] = _TRIGGER % (name, table, version, vocabulary(table), wall, body)
    return out


def _tables(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def _ours():
    """Every trigger name this module may own: the guarded tables' and the retired ones'."""
    return {t + SUFFIX for t in {g[0] for g in GUARDS} | set(RETIRED)}


def installed(con):
    """{trigger name: its SQL} for every guard of ours this database carries - a trigger whose name is ours, compared
    case-blind as SQLite compares it, and which sits on our table."""
    ours = {n.lower(): n for n in _ours()}
    out = {}
    for name, table, sql in con.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type = 'trigger'"):
        mine = ours.get(str(name).lower())
        if mine and str(table).lower() == mine[:-len(SUFFIX)].lower():
            out[mine] = sql
    return out


def refused_by_guard(exc):
    """Did a record guard raise this sqlite error? -> bool."""
    return MARK in str(exc)


def survey(con, version=None):
    """What `install` would do to this database, read-only -> {"version", "wall", "want", "have", "stale", "changed",
    "skew", "taken"}. `skew` is every trigger - any name, any table - stamped at this version or a later one with
    another WALL: another engine's guard set (review 3: a guard it retired, or one on a table this engine does not
    guard, was invisible to a check of our own names). `taken` is each guard to install whose name a trigger that is
    not ours holds. install refuses both; integrity reports both from this one reading, so the doctor and the engine
    cannot disagree about a book."""
    version, wall = _version(version), vocabulary()
    want, have = expected(_tables(con), version), installed(con)
    triggers = [(str(r[0]), r[1]) for r in con.execute("SELECT name, sql FROM sqlite_master WHERE type = 'trigger'")]
    stamped = [(name, stamp(sql)) for name, sql in triggers]
    skew = sorted((name, got) for name, got in stamped if got and got[0] >= version and got[2] != wall)
    stale = sorted(n for n in have if n not in want)
    changed = sorted(n for n, sql in want.items() if have.get(n) != sql)
    held, mine = {name.lower(): name for name, _sql in triggers}, {n.lower() for n in have}
    # every guard name, not only those this database's tables want now: a migration creates a table, and a name taken
    # before it is taken after (review 4: the doctor read the book before migration and the open after)
    taken = sorted((n, held[n.lower()]) for n in (t + SUFFIX for t in {g[0] for g in GUARDS})
                   if n not in have and n.lower() in held)
    # an older engine's guard this one does not own - a table no longer guarded and not listed in RETIRED: left on open
    unowned = sorted((name, got) for name, got in stamped if got and got[0] < version and name.lower() not in mine)
    return {"version": version, "wall": wall, "want": want, "have": have, "stale": stale, "changed": changed,
            "skew": skew, "taken": taken, "unowned": unowned}


def release_hint(con):
    """The way out of a book refused for another engine's guards, named with this book's own file -> text; the refusal
    and the doctor print the same words (review 5: both sent the owner to a doc, and the doc to the command)."""
    path = next((str(r[2]) for r in con.execute("PRAGMA database_list") if r[1] == "main"), "") or "<book.db>"
    return ("from the engine's folder: python scripts/release_guards.py \"%s\" (docs/guide-operating.md, Failure "
            "playbook)" % path)


def check(con, version=None):
    """Refuse this book as `install` would - another engine's wall, a taken name - before anything is written:
    db.connect calls it before a migration commits its version step, so a refused open leaves the book as it was
    (review 4)."""
    _plan(con, _version(version))


def _plan(con, version):
    """-> (want, have, stale, changed) for this database, refusing a skewed book or a taken name (see `install`)."""
    s = survey(con, version)
    if s["skew"]:
        name, got = s["skew"][0]
        raise records.RecordError(
            "DB_GUARD_VOCABULARY_SKEW",
            "%s: this book's record guards were installed at schema v%d by an engine with another guard set (wall %s; "
            "this engine's is %s at v%d). Two engines at one version disagree on what the database refuses - step "
            "db.SCHEMA_VERSION where the words, bounds, tests or guarded tables moved; replacing the guards would "
            "refuse the other engine's running beats. If that engine is gone, release the book %s"
            % (name, got[0], got[2] or "unreadable", s["wall"], version, release_hint(con)))
    if s["taken"]:
        name, holder = s["taken"][0]
        raise records.RecordError(
            "DB_GUARD_NAME_TAKEN", "%s: a trigger named %r, not the engine's, holds this guard's name (SQLite "
            "compares trigger names case-blind) - drop it, and re-create it under another name if it is still "
            "needed, so the guard can be installed" % (name, holder))
    return s["want"], s["have"], s["stale"], s["changed"]


def install(con, version=None):
    """Create each missing guard, replace each whose SQL differs from what the constants give today, drop a retired
    one -> the names written (empty when the database is current, and then nothing is written and no lock is taken).
    REFUSES a book holding any guard stamped at this version, or a later one, with another wall
    (DB_GUARD_VOCABULARY_SKEW): another checkout's guard set, which replacing would turn against its running beats; the
    reading is `survey`, which integrity reports from too. REFUSES a trigger of someone else's holding
    one of our names (DB_GUARD_NAME_TAKEN): dropping it would destroy their work. One IMMEDIATE transaction: it waits out
    another writer for the connection's busy timeout, and a guard is never absent between its drop and re-creation.
    THE PLAN IS READ AGAIN UNDER THE LOCK: two tools opening a stale book together both read "missing", and the second,
    once the first had installed it, met "trigger ... already exists" (round 3's own probe). Refuses a connection with
    a transaction already open: its own BEGIN would commit the caller's."""
    version = _version(version)
    if con.in_transaction:
        raise records.RecordError("DB_TRANSACTION_OPEN", "guards.install: the connection has uncommitted work on it, "
                                  "and installing would commit it - commit or roll back first")
    if not any(_plan(con, version)[2:]):
        return []
    con.execute("BEGIN IMMEDIATE")
    try:
        want, have, stale, changed = _plan(con, version)
        for n in stale + changed:
            if n in have:
                con.execute("DROP TRIGGER IF EXISTS %s" % _ident(n))
        for n in changed:
            con.execute(want[n])
        con.commit()
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    return stale + changed


def release(con):
    """Drop every trigger carrying a record-guards stamp - this engine's and another engine's, whatever its name - so the
    next open installs this engine's own -> the names dropped. The owner's way out of DB_GUARD_VOCABULARY_SKEW once the
    engine that stamped the book is gone (scripts/release_guards.py; docs/guide-operating.md). The guards hold no data,
    so no row is touched; a trigger with no stamp is someone else's and stays. One IMMEDIATE transaction; refuses a
    connection with a transaction open, as install does."""
    if con.in_transaction:
        raise records.RecordError("DB_TRANSACTION_OPEN", "guards.release: the connection has uncommitted work on it, "
                                  "and releasing would commit it - commit or roll back first")
    con.execute("BEGIN IMMEDIATE")
    try:
        names = sorted(str(r[0]) for r in con.execute("SELECT name, sql FROM sqlite_master WHERE type = 'trigger'")
                       if stamp(r[1]))
        for n in names:
            con.execute("DROP TRIGGER IF EXISTS %s" % _ident(n))
        con.commit()
    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    return names


def legacy_counts(con):
    """{"table.column": rows} for each guard, counting the rows already written that it would refuse today - history
    written under another vocabulary or spelling, readable as it was and never rewritten (hard rule 2). Only guards
    whose table and columns this database has; zero counts left out; an empty text left out, since the not-empty wall's
    own check (integrity's BREACH) reports it."""
    tables = _tables(con)
    out = {}
    for g in GUARDS:
        table, col, kind = g[0], g[1], g[2]
        cols = col if isinstance(col, tuple) else (col,)
        if table not in tables:
            continue
        have = {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}
        if not set(cols) <= have:
            continue
        blank = " AND ".join("%s <> ''" % c for c in cols) if kind in ("one-of", "rung") else "1"
        n = con.execute("SELECT COUNT(*) FROM %s WHERE (%s) AND %s" % (table, refused(g, row=""), blank)).fetchone()[0]
        if n:
            out["%s.%s" % (table, _column(col))] = n
    return out
