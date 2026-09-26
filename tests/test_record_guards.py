#!/usr/bin/env python3
"""test_record_guards.py — the record's second wall, on every database the engine opens (gate record-guards, 2026-09-26).

THE CONTRACTS PLAN, G6 (the owner's "Go"): "`validation` and `wound_mints` are unchecked, and the database CHECKs are
weaker than the Python vocabularies". schema.sql held eleven columns only to "not empty" where the record layer
refuses anything outside a closed vocabulary, and four numbers to no range; a migrated database carried none of it;
and TurnCommit.validate never read `validation` or `wound_mints`. Checked:

  [1] every guard is built from the constant the record layer checks - the SQL's words are the constant's, and a
      changed constant replaces the trigger on the next open (and an unchanged open writes nothing); each guard is
      stamped with its version, its table's vocabulary and the whole wall's, and a same-version engine with another
      guard set - other words, a bound, a rung, a guard retired, a table added, the same words read by another
      predicate, another RAISE kind or trigger timing, a stamp it cannot read, a guard under any name - is refused the
      book, both ways (one wall per version,
      held at run time: the reviews' first majors); only our trigger names are touched; an install that fails part-way
      leaves every guard as it was
  [2] a fresh database: each guarded column refuses a value outside its vocabulary or range, and a NULL, by the record
      layer's own code, and takes one inside it
  [3] NEVER STRICTER THAN PYTHON: every value the record layer accepts passes - every path, every rung on every ladder,
      every concept, word and tier, the ends of every range - and each refused value is one the record layer refuses;
      [3b] past the exact words: every near miss (each case; a space, tab or no-break space at either end; the
      separators swapped; trailing punctuation; the full-width form; the `concept:` prefix; quotes) through the engine's
      own writer is written or refused by the record layer, never by the database
  [4] a database migrated from v33 holding rows under a retired vocabulary: it opens at v34 with its guards, the rows
      are exactly as they were, a new row like them is refused, and integrity counts them as LEGACY-ROWS (amber)
  [5] integrity: a database lacking a guard, or carrying a different one, reports INSERT-GUARD-MISSING (amber); [5b] a
      stale open waits out another writer and a current one takes no lock; two opens of a stale book at once both
      open, or the second is refused under the lock when the first was another engine; a sweep of an aged chronicle
      raises nothing, and an empty text is left to BREACH; [5c] a book the engine refuses to open - another engine's
      guard set (any name, any table, a stamp it cannot read), a taken name, a newer book - is red BOOK-REFUSED
      naming the code the open raises, and a refused open writes nothing; an older engine's guard it does not own is
      amber; `doctor --fold` on a refused book reports it
  [6] the record layer: TurnCommit.validate refuses a malformed mint - any field write_mints keeps - by its WOUND_*
      code before any INSERT is attempted, a validation or lands_on entry of the wrong type by a registered code;
      Reading refuses an unknown confidence; readings.write stores the ladder's own spelling of a rung; a guard of
      another vocabulary refusing a beat is named DB_GUARD_REFUSED
  [7] schema.sql's own IN-list CHECKs - copies older than this gate, which no guard builds - hold exactly the constants
      they copy, so a changed constant fails here until its CHECK and a rebuild step move with it

Script-style: check(), main(), exit code. Stdlib only. Invented fixtures (maren, edda, a millhouse).
"""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bond_rest, claims, concepts, db, guards, integrity, law, readings, records, rungs, wound  # noqa: E402
from src.engine.errors import EngineError                              # noqa: E402
from src.engine.ledger import Ledger                                   # noqa: E402
from src.engine.records import PATHS, Reading, RecordError, TurnCommit  # noqa: E402

FAILS = []
TMP = tempfile.TemporaryDirectory(prefix="swe_guards_", ignore_cleanup_errors=True)
#: db.SCHEMA_VERSION -> guards.vocabulary() at that version (the words, bounds and the whole trigger but its message).
#: Append a row when a guarded word, bound or test changes, and step the version with it; never edit one once a book
#: carries it. The engine holds the rule at run time (a guard stamped at this version with another wall refuses the
#: book); this row is the suite's reminder. (34 was re-pinned in the gate's round 5, when the fingerprint gained the
#: whole message-free trigger - before any book carried a v34 stamp: every run over the owner's books opened backup
#: copies. The one database that did, the suite's own runs/ashford.db from an earlier build, was refused by the new
#: build as the rule says, and released with docs/guide-operating.md's line - what stepping the version avoids.)
GUARD_HASHES = {34: "43066b2019d9d202"}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %r" % (detail,)))
    if not ok:
        FAILS.append("%s: %r" % (name, detail))


def _path(name):
    return os.path.join(TMP.name, name)


def _fresh(name):
    """A database the engine created, holding one run and one bible."""
    con = db.connect(_path(name))
    con.execute("INSERT INTO runs (run_id, created_at, config) VALUES ('r1', 'now', '{}')")
    con.execute("INSERT INTO bibles (fingerprint, built_at, world, characters) VALUES ('fp', 'now', '{}', '{}')")
    con.commit()
    return con


LADDER = {p: rungs.names_on(p) for p in sorted(rungs.BANDS)}
W, WR = "WARINESS", LADDER["WARINESS"][0]

#: table -> a row every guard accepts (column: value). The good row is what the engine itself writes.
GOOD = {
    "relationship_deltas": {"run_id": "r1", "turn": 1, "perceiver": "maren", "target": "edda", "axis": "trust",
                            "delta": 0.1, "ord": "first"},
    "rest_declared": {"run_id": "r1", "turn": 1, "perceiver": "maren", "target": "edda", "axis": "trust", "rest": 0.5,
                      "source": "authored"},
    "toward_deltas": {"run_id": "r1", "turn": 1, "perceiver": "maren", "target": "edda", "primary_": W, "delta": 0.1},
    "target_binds": {"run_id": "r1", "turn": 1, "char_id": "maren", "primary_": W, "target": "edda"},
    "wound_deltas": {"run_id": "r1", "char_id": "maren", "turn": 1, "wound_id": "fire@WARINESS", "delta": -0.1,
                     "kind": "event"},
    "wound_minted": {"run_id": "r1", "turn": 1, "char_id": "maren", "wound_id": "fire@WARINESS", "concept": "fire",
                     "path": W, "intensity": 0.9},
    "readings": {"run_id": "r1", "turn": 1, "actor": "maren", "path": W, "rung": WR, "about": "edda",
                 "confidence": "sure"},
    "utterances": {"run_id": "r1", "turn": 1, "speaker": "maren", "said": "the millhouse wheel is cracked",
                   "tier": "superposed"},
    "bible_laws": {"fingerprint": "fp", "law_id": "l1", "domain": sorted(law._DOMAINS)[0], "modality": "FORBIDS",
                   "statement": "no one crosses the weir at night"},
}

#: (table, {column: a bad value}, the code the database must name, the record layer's own refusal of the same value)
BAD = [
    ("relationship_deltas", {"axis": "love"}, "RECORD_AXIS_UNKNOWN",
     lambda: records.RelationshipDelta("maren", "edda", "love", 0.1).validate()),
    ("relationship_deltas", {"axis": None}, "RECORD_AXIS_UNKNOWN",
     lambda: records.RelationshipDelta("maren", "edda", None, 0.1).validate()),
    ("relationship_deltas", {"ord": "1"}, "RECORD_ORDER_UNKNOWN",
     lambda: records.RelationshipDelta("maren", "edda", "trust", 0.1, order="1").validate()),
    ("relationship_deltas", {"delta": 1.5}, "RECORD_DELTA_RANGE",
     lambda: records.RelationshipDelta("maren", "edda", "trust", 1.5).validate()),
    ("relationship_deltas", {"delta": -1.01}, "RECORD_DELTA_RANGE",
     lambda: records.RelationshipDelta("maren", "edda", "trust", -1.01).validate()),
    ("relationship_deltas", {"delta": "a lot"}, "RECORD_DELTA_RANGE",
     lambda: records.RelationshipDelta("maren", "edda", "trust", "a lot").validate()),
    # a NULL is refused by the guard's own code, before NOT NULL's generic one (SQLite orders text above every number,
    # so `> 1` alone refuses "a lot"; only the typeof clause names the rule for a missing number)
    ("relationship_deltas", {"delta": None}, "RECORD_DELTA_RANGE",
     lambda: records.RelationshipDelta("maren", "edda", "trust", None).validate()),
    ("rest_declared", {"axis": "love"}, "RECORD_AXIS_UNKNOWN",
     lambda: records.RestDeclared("maren", "edda", "love", 0.5).validate()),
    ("toward_deltas", {"primary_": "RAGE"}, "RECORD_PRIMARY_UNKNOWN",
     lambda: records.TowardDelta("maren", "edda", "RAGE", 0.1).validate()),
    ("toward_deltas", {"delta": 2}, "RECORD_DELTA_RANGE",
     lambda: records.TowardDelta("maren", "edda", W, 2).validate()),
    ("target_binds", {"primary_": "RAGE"}, "RECORD_LIST_ITEM_TYPE",
     lambda: _commit(target_binds=[("RAGE", "edda")]).validate()),
    ("wound_deltas", {"delta": 2}, "RECORD_DELTA_RANGE",
     lambda: records.WoundDelta("maren", "fire@WARINESS", 2, "event").validate()),
    ("wound_minted", {"path": "RAGE"}, "WOUND_PATH_UNKNOWN",
     lambda: wound._check({"concept": "fire", "path": "RAGE", "intensity": 0.9})),
    ("wound_minted", {"concept": "the millhouse ghost"}, "WOUND_CONCEPT_UNKNOWN",
     lambda: wound._check({"concept": "the millhouse ghost", "path": W, "intensity": 0.9})),
    ("wound_minted", {"intensity": 1.2}, "WOUND_INTENSITY_RANGE",
     lambda: wound._check({"concept": "fire", "path": W, "intensity": 1.2})),
    ("readings", {"rung": LADDER["DISPLEASURE"][-1]}, "READING_RUNG_NOT_ON_PATH",
     lambda: Reading(path=W, rung=LADDER["DISPLEASURE"][-1]).validate()),
    ("readings", {"path": "COURAGE"}, "READING_RUNG_NOT_ON_PATH",
     lambda: Reading(path="COURAGE", rung=WR).validate()),
    ("readings", {"confidence": "certain"}, "READING_CONFIDENCE_UNKNOWN",
     lambda: Reading(path=W, rung=WR, confidence="certain").validate()),
    # stricter than Reading.validate, which reads a rung name case-blind - but no engine writer can write it:
    # readings.write stores the ladder's own spelling (checked in [6]), so only a stranger's row meets this
    ("readings", {"rung": WR.upper()}, "READING_RUNG_NOT_ON_PATH", None),
    ("utterances", {"tier": "rumour"}, "CLAIM_TIER_UNKNOWN", None),
    ("bible_laws", {"statement": "   "}, "BIBLE_LAW_STATEMENT_MISSING", None),
]


def _deep(n):
    v = []
    for _ in range(n):
        v = [v]
    return v


def _commit(**kw):
    base = dict(run_id="r1", turn=1, actor="maren", thought="", action="", tags={}, affect={p: 0.0 for p in PATHS})
    base.update(kw)
    return TurnCommit(**base)


def _insert(con, table, row):
    cols = sorted(row)
    con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(cols), ", ".join("?" * len(cols))),
                [row[c] for c in cols])


def _refusal(con, table, row):
    """-> None when the database took the row (then rolled back), else the refusal's text."""
    try:
        _insert(con, table, row)
        con.rollback()
        return None
    except sqlite3.IntegrityError as e:
        con.rollback()
        return str(e)


def _code_of(call):
    try:
        call()
        return None
    except EngineError as e:
        return e.code
    except Exception as e:                                            # noqa: BLE001 - which way it fails is the check
        return type(e).__name__


# ---- [1] ---------------------------------------------------------------------------------------------------------

def built_from_the_constants():
    print("[1] every guard is built from the constant the record layer checks")
    sql = guards.expected()
    check("one-guard-per-guarded-table", set(sql) == {g[0] + guards.SUFFIX for g in guards.GUARDS}, sorted(sql))
    for g in guards.GUARDS:
        table, col, kind, allowed = g[:4]
        if kind == "one-of":
            m = re.search(r"NEW\.%s NOT IN \((.*?)\);" % col, sql[table + guards.SUFFIX])  # unparsed = a named FAIL
            got = [w.strip()[1:-1].replace("''", "'") for w in m.group(1).split(", ")] if m else None
            check("%s.%s-is-exactly-its-constant" % (table, col), got == list(allowed()), got and got[:5])
    ladder = {p: tuple(rungs.names_on(p)) for p in rungs.BANDS}
    body = sql["readings" + guards.SUFFIX]
    pairs = set(re.findall(r"NEW\.path = '([^']+)' AND NEW\.rung IN \(([^)]*)\)", body))
    check("readings.path+rung-is-exactly-the-ladders", {p: tuple(n.strip()[1:-1] for n in names.split(", "))
                                                         for p, names in pairs} == ladder, sorted(ladder))
    # WHAT IS EMITTED IS WHAT IS FINGERPRINTED (review 5): the wall hashes `_TRIGGER` and each `_raise`, so an edit to how
    # `expected` assembles them would change what the database refuses and move no stamp - held here, by the suite
    built = {t + guards.SUFFIX: guards._TRIGGER % (t + guards.SUFFIX, t, db.SCHEMA_VERSION, guards.vocabulary(t),
                                                   guards.vocabulary(), "\n".join(guards._raise(g) for g in guards.GUARDS
                                                                                  if g[0] == t))
             for t in {g[0] for g in guards.GUARDS}}
    check("each-emitted-trigger-is-exactly-the-fingerprinted-templates", sql == built,
          sorted(n for n in built if sql.get(n) != built[n]))
    con = _fresh("derive.db")
    con.close()
    con = db.connect(_path("derive.db"))
    check("an-unchanged-open-writes-no-guard", guards.install(con) == [], guards.install(con))
    guard = "relationship_deltas" + guards.SUFFIX
    check("each-guard-is-stamped-with-its-version,-its-table's-vocabulary-and-the-wall's",
          guards.stamp(guards.installed(con).get(guard)) == (db.SCHEMA_VERSION, guards.vocabulary("relationship_deltas"),
                                                             guards.vocabulary()), guards.stamp(guards.installed(con).get(guard)))
    cookie = con.execute("PRAGMA schema_version").fetchone()[0]
    con.close()
    con = db.connect(_path("derive.db"))
    check("...and-a-current-open-rewrites-nothing-(its-schema-cookie-stands)",
          con.execute("PRAGMA schema_version").fetchone()[0] == cookie, cookie)
    con.close()
    # ONE VOCABULARY PER SCHEMA VERSION, AT RUN TIME (review 2's major: the suite's pin alone was defeated by editing
    # it). Another engine at this version with other words is refused the book and the first engine's guard stands; a
    # newer version's engine replaces it, as a migration step does; an older engine then meets a newer guard and is
    # refused - it never downgrades the wall.
    real = records.RELATIONSHIP_AXES
    records.RELATIONSHIP_AXES = real + ("loyalty",)
    try:
        code = _code_of(lambda: db.connect(_path("derive.db")))
        raw = sqlite3.connect(_path("derive.db"))
        check("a-same-version-engine-with-other-words-is-refused-the-book-and-the-guard-stands",
              code == "DB_GUARD_VOCABULARY_SKEW" and guard in guards.installed(raw)
              and "'loyalty'" not in guards.installed(raw)[guard], code)
        try:
            written = guards.install(raw, version=db.SCHEMA_VERSION + 1)
        except EngineError as e:                                     # refused: reported by name, never a section crash
            written = e.code
        check("...a-newer-version's-engine-replaces-it-(a-migration-step)", isinstance(written, list)
              and guard in written and "'loyalty'" in guards.installed(raw).get(guard, ""), written)
        raw.close()
    finally:
        records.RELATIONSHIP_AXES = real
    code = _code_of(lambda: db.connect(_path("derive.db")))
    check("...and-an-older-engine-meeting-the-newer-guard-is-refused,-never-downgrading-it",
          code == "DB_GUARD_VOCABULARY_SKEW", code)
    raw = sqlite3.connect(_path("derive.db"))
    body = guards.installed(raw).get("readings" + guards.SUFFIX)
    check("...(the-newer-version's-install-restamped-every-guard-of-the-book)",
          (guards.stamp(body) or (None,))[0] == db.SCHEMA_VERSION + 1, guards.stamp(body))
    raw.close()
    # ONE WALL PER VERSION, whatever moved (review 3's major: a guard retired, or one added on another table, left every
    # stamp of the other engine's guards "the same words", so neither engine refused the other; review 3: a bound or a
    # rung was held only by the pin). Each case is another engine at THIS version opening a book this engine made.
    _fresh("wall.db").close()
    raw = sqlite3.connect(_path("wall.db"))
    before = guards.installed(raw).get(guard)
    raw.close()
    tables = len({g[0] for g in guards.GUARDS})
    real_range, real_band = records.DELTA_RANGE, rungs.BANDS[W]
    real_guards, real_retired, real_refused = guards.GUARDS, guards.RETIRED, guards.refused
    real_statement, real_trigger = guards._STATEMENT, guards._TRIGGER
    extra = ("llm_calls", "purpose", "one-of", lambda: ("act", "compose"), "RECORD_FIELD_TYPE", "a purpose vocabulary")

    def nocase(g, row="NEW."):                                       # the same words, read another way (review 4)
        sql = real_refused(g, row)
        return sql.replace("NOT IN", "COLLATE NOCASE NOT IN") if g[:2] == ("relationship_deltas", "axis") else sql
    others = (("a-widened-bound", lambda: setattr(records, "DELTA_RANGE", (-2.0, 2.0))),
              ("a-renamed-rung", lambda: rungs.BANDS.__setitem__(W, [real_band[0][:2] + (real_band[0][2] + "-x",)]
                                                                 + list(real_band[1:]))),
              ("a-retired-guard", lambda: (setattr(guards, "GUARDS", tuple(g for g in real_guards
                                                                             if g[0] != "utterances")),
                                           setattr(guards, "RETIRED", ("utterances",)))),
              ("a-guard-on-another-table", lambda: setattr(guards, "GUARDS", real_guards + (extra,))),
              ("the-same-words-read-by-another-predicate", lambda: setattr(guards, "refused", nocase)),
              ("another-RAISE-kind", lambda: setattr(guards, "_STATEMENT", real_statement.replace("ABORT", "FAIL"))),
              ("another-trigger-timing", lambda: setattr(guards, "_TRIGGER", real_trigger.replace("BEFORE", "AFTER"))))
    for i, (what, become) in enumerate(others):
        book = "wall_%d.db" % i                                      # its own book: no case sees another's
        _fresh(book).close()
        try:
            become()
            code = _code_of(lambda: db.connect(_path(book)))
        finally:
            records.DELTA_RANGE, rungs.BANDS[W] = real_range, real_band
            guards.GUARDS, guards.RETIRED, guards.refused = real_guards, real_retired, real_refused
            guards._STATEMENT, guards._TRIGGER = real_statement, real_trigger
        raw = sqlite3.connect(_path(book))
        stands = guards.installed(raw)
        raw.close()
        check("a-same-version-engine-with-%s-is-refused-the-book,-and-every-guard-stands" % what,
              code == "DB_GUARD_VOCABULARY_SKEW" and stands.get(guard) == before and len(stands) == tables,
              (code, sorted(stands)))
    # ...and the other way round: a book another engine made with a guard on a table this one does not guard
    try:
        guards.GUARDS = real_guards + (extra,)
        _fresh("wall_x.db").close()
    finally:
        guards.GUARDS = real_guards
    code = _code_of(lambda: db.connect(_path("wall_x.db")))
    raw = sqlite3.connect(_path("wall_x.db"))
    theirs = raw.execute("SELECT COUNT(*) FROM sqlite_master WHERE name = 'llm_calls_record_guard'").fetchone()[0]
    raw.close()
    check("...and-an-engine-without-a-guarded-table-is-refused-a-book-that-guards-it,-which-stands",
          code == "DB_GUARD_VOCABULARY_SKEW" and theirs == 1, (code, theirs))
    # ...and EVERY stamped trigger is read, whatever its name or table - not only the guards this engine calls its own:
    # this engine's current guards beside one other engine's guard on a table this one does not guard
    try:
        guards.GUARDS = real_guards + (extra,)
        theirs = guards.expected()["llm_calls" + guards.SUFFIX]
    finally:
        guards.GUARDS = real_guards
    _fresh("wall_y.db").close()
    raw = sqlite3.connect(_path("wall_y.db"))
    raw.execute(theirs)
    raw.commit()
    raw.close()
    code = _code_of(lambda: db.connect(_path("wall_y.db")))
    check("...and-another-engine's-stamped-guard-on-a-table-this-one-does-not-guard-is-read,-and-refused",
          code == "DB_GUARD_VOCABULARY_SKEW", code)
    # ...WHATEVER ITS NAME (review 4: a survey narrowed to names ending in the suffix passed every suite)
    _fresh("wall_z.db").close()
    raw = sqlite3.connect(_path("wall_z.db"))
    raw.execute(theirs.replace("CREATE TRIGGER llm_calls" + guards.SUFFIX, "CREATE TRIGGER purpose_guard", 1))
    raw.commit()
    raw.close()
    code = _code_of(lambda: db.connect(_path("wall_z.db")))
    check("...whatever-its-name-(one-not-ending-in-the-guard-suffix)", code == "DB_GUARD_VOCABULARY_SKEW", code)
    # A STAMP THIS ENGINE CANNOT READ keeps its version (review 4: one in another field order, or an earlier round's
    # format, parsed as no stamp and was replaced as unstamped): at this version it is another engine's, refused; from
    # an older version it is replaced, as any older guard is
    ours = guards.expected()[guard]
    line = next(ln for ln in ours.splitlines() if "-- record-guards" in ln)
    _v, voc, wall = guards.stamp(ours)
    for what, version, text in (("in-another-field-order", db.SCHEMA_VERSION, "wall %s vocabulary %s" % (wall, voc)),
                                ("of-an-earlier-format", db.SCHEMA_VERSION, "vocabulary %s" % voc),
                                ("from-an-older-version", db.SCHEMA_VERSION - 1, "wall %s vocabulary %s" % (wall, voc))):
        book = "unreadable_%s.db" % what
        _fresh(book).close()
        raw = sqlite3.connect(_path(book))
        raw.execute("DROP TRIGGER IF EXISTS %s" % guard)
        raw.execute(ours.replace(line, "  -- record-guards v%d %s" % (version, text)))
        raw.commit()
        raw.close()
        code = _code_of(lambda: db.connect(_path(book)).close())
        raw = sqlite3.connect(_path(book))
        now = guards.installed(raw).get(guard)
        raw.close()
        if version < db.SCHEMA_VERSION:
            check("an-unreadable-stamp-%s-is-replaced" % what, code is None and now == ours, (code, now == ours))
        else:
            check("an-unreadable-stamp-%s-is-another-engine's:-refused,-and-it-stands" % what,
                  code == "DB_GUARD_VOCABULARY_SKEW" and now == ours.replace(line, "  -- record-guards v%d %s"
                                                                              % (version, text)), code)
    # the rest of [1] on a book of this version
    con = _fresh("names.db")
    name = "readings" + guards.SUFFIX
    con.execute("DROP TRIGGER IF EXISTS %s" % name)
    con.execute(guards.expected()[name].replace("'sure'", "'certain'"))      # same stamp, a different body
    con.commit()
    written = guards.install(con)
    check("...(a-body-edited-under-this-version's-own-stamp-is-replaced-on-open)", written == [name]
          and guards.installed(con).get(name) == guards.expected()[name], (written, name in guards.installed(con)))
    # ONLY OUR NAMES (review 1: every trigger ending in the suffix was treated as ours - a user's was dropped, and one
    # whose name needs quoting stopped every tool opening the book; review 2: SQLite compares trigger names case-blind)
    con.execute("CREATE TRIGGER audit_record_guard BEFORE INSERT ON llm_calls BEGIN SELECT 1; END")
    con.execute('CREATE TRIGGER "audit-llm_record_guard" BEFORE INSERT ON llm_calls BEGIN SELECT 1; END')
    con.commit()
    con.close()
    con = db.connect(_path("names.db"))
    left = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")}
    check("someone-else's-trigger-that-ends-in-the-suffix-is-left-alone,-and-the-book-still-opens",
          {"audit_record_guard", "audit-llm_record_guard"} <= left, sorted(left))
    # ...even one named for the unguarded table it sits on (the suffix and the table agree; only the name list says
    # it is not ours - round 3's mutants: the table check alone let a suffix rule through)
    con.execute("CREATE TRIGGER llm_calls_record_guard BEFORE INSERT ON llm_calls BEGIN SELECT 1; END")
    con.commit()
    con.close()
    con = db.connect(_path("names.db"))
    check("...even-one-named-<its-own-unguarded-table>_record_guard", "llm_calls_record_guard" in {
        r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")})
    con.execute("DROP TRIGGER IF EXISTS llm_calls_record_guard")
    # OUR GUARD UNDER ANOTHER CASE, on its own table, is ours (SQLite reads the name case-blind): replaced, not refused
    con.execute("DROP TRIGGER IF EXISTS %s" % name)
    con.execute(guards.expected()[name].replace("CREATE TRIGGER " + name, "CREATE TRIGGER " + name.upper(), 1))
    con.commit()
    con.close()
    code = _code_of(lambda: db.connect(_path("names.db")).close())
    raw = sqlite3.connect(_path("names.db"))
    names_now = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")}
    raw.close()
    check("...and-our-guard-under-another-case-on-its-own-table-is-ours:-replaced,-not-refused", code is None
          and name in names_now and name.upper() not in names_now, (code, sorted(names_now)))
    con = db.connect(_path("names.db"))
    con.execute("DROP TRIGGER IF EXISTS %s" % name)
    con.execute("CREATE TRIGGER Readings_Record_Guard BEFORE INSERT ON llm_calls BEGIN SELECT 1; END")
    con.commit()
    con.close()
    code = _code_of(lambda: db.connect(_path("names.db")))
    raw = sqlite3.connect(_path("names.db"))
    theirs = raw.execute("SELECT tbl_name FROM sqlite_master WHERE name = 'Readings_Record_Guard'").fetchone()
    check("...a-trigger-of-someone-else's-holding-our-name-case-blind-is-refused,-never-dropped",
          code == "DB_GUARD_NAME_TAKEN" and theirs == ("llm_calls",), (code, theirs))
    raw.execute("DROP TRIGGER IF EXISTS Readings_Record_Guard")
    raw.commit()
    raw.close()
    real_retired = guards.RETIRED
    guards.RETIRED = ("llm_calls",)
    try:
        con = db.connect(_path("names.db"))
        con.execute("CREATE TRIGGER llm_calls_record_guard BEFORE INSERT ON llm_calls BEGIN SELECT 1; END")
        con.commit()
        con.close()
        con = db.connect(_path("names.db"))
        left = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")}
        check("a-guard-of-a-RETIRED-table-is-dropped-on-open", "llm_calls_record_guard" not in left
              and "audit_record_guard" in left, sorted(left))
        con.close()
    finally:
        guards.RETIRED = real_retired
    # THE SUITE'S REMINDER of the run-time rule: a change to any guarded word or bound moves this fingerprint - step
    # db.SCHEMA_VERSION and add its row (never edit one: the stamps in every book carry the old row's fingerprint)
    check("the-vocabulary-is-pinned-to-the-schema-version-(a-vocabulary-change-steps-the-version)",
          GUARD_HASHES.get(db.SCHEMA_VERSION) == guards.vocabulary(), (db.SCHEMA_VERSION, guards.vocabulary()))
    # ...OF WORDS AND BOUNDS ONLY (review 2: a reworded message, or two rows of one table swapped, moved the hash - and a
    # moved hash is a version step, which locks every older checkout out of every book)
    real_guards, real_says, was = guards.GUARDS, dict(guards._SAYS), guards.vocabulary()
    real_axes, real_refused = records.RELATIONSHIP_AXES, guards.refused
    try:
        guards.GUARDS = tuple(reversed(real_guards))
        reordered = guards.vocabulary()
        guards.GUARDS = tuple(g[:4] + ("ANOTHER_CODE", "another rule") for g in real_guards)
        recoded = guards.vocabulary()
        guards.GUARDS = real_guards
        guards._SAYS.update({k: "differs from %s" for k in real_says})
        reworded = guards.vocabulary()
        records.RELATIONSHIP_AXES = tuple(reversed(real_axes))
        resorted = guards.vocabulary()
        records.RELATIONSHIP_AXES = real_axes
        guards.refused = lambda g, row="NEW.": real_refused(g, row).replace("NOT IN", "COLLATE NOCASE NOT IN")
        retested = guards.vocabulary()
    finally:
        guards.GUARDS, records.RELATIONSHIP_AXES, guards.refused = real_guards, real_axes, real_refused
        guards._SAYS.update(real_says)
    check("...a-fingerprint-free-of-row-order,-a-constant's-word-order,-codes-and-message-text,-and-moved-by-a-test",
          was == reordered == recoded == reworded == resorted and retested != was,
          (was, reordered, recoded, reworded, resorted, retested))
    # ONE TRANSACTION: a failure between a drop and its re-creation leaves the old guard (review 1: untested)
    con = db.connect(_path("names.db"))
    before = guards.installed(con).get(name)
    real_expected = guards.expected
    guards.expected = lambda tables=None, version=None: dict(real_expected(tables, version),
                                                             **{name: "CREATE TRIGGER broken ("})
    try:
        guards.install(con)
        failed = None
    except sqlite3.Error as e:
        failed = type(e).__name__
    finally:
        guards.expected = real_expected
    check("an-install-that-fails-part-way-leaves-every-guard-as-it-was", failed == "OperationalError"
          and guards.installed(con).get(name) == before and not con.in_transaction, failed)
    con.execute("INSERT INTO runs (run_id, created_at, config) VALUES ('r2', 'now', '{}')")
    check("...and-install-refuses-a-connection-with-a-transaction-open-(it-would-commit-it)",
          _code_of(lambda: guards.install(con)) == "DB_TRANSACTION_OPEN", _code_of(lambda: guards.install(con)))
    con.rollback()
    con.close()
    real_words = readings.CONFIDENCE_WORDS
    readings.CONFIDENCE_WORDS = real_words + ("probable",)
    try:
        check("the-confidence-guard-reads-the-constant-when-built,-not-at-import",
              "'probable'" in guards.expected()["readings" + guards.SUFFIX])
    finally:
        readings.CONFIDENCE_WORDS = real_words


# ---- [2] + [3] ---------------------------------------------------------------------------------------------------

def a_fresh_database():
    print("[2] a fresh database: each guarded column refuses what the record layer refuses, by its code")
    con = _fresh("fresh.db")
    for table, row in sorted(GOOD.items()):
        check("the-engine's-own-row-is-taken:-%s" % table, _refusal(con, table, row) is None,
              _refusal(con, table, row))
    for table, bad, code, python in BAD:
        said = _refusal(con, table, dict(GOOD[table], **bad))
        check("%s-refuses-%s-by-%s" % (table, bad, code), (said or "").startswith(code + ": "), said)
        if python is not None:
            check("...and-the-record-layer-refuses-it-too-(%s)" % code, _code_of(python) == code, _code_of(python))
    # A NULL IN EVERY GUARDED COLUMN is refused by its guard's code, before NOT NULL's generic one (review 2: the suite
    # held two of the sixteen, and the NULL half of the rung and not-blank guards could go unseen)
    cols = [(g[0], c, g[4]) for g in guards.GUARDS for c in (g[1] if isinstance(g[1], tuple) else (g[1],))]
    wrong = [(t, c, _refusal(con, t, dict(GOOD[t], **{c: None}))) for t, c, code in cols
             if not (_refusal(con, t, dict(GOOD[t], **{c: None})) or "").startswith(code + ": ")]
    check("a-NULL-in-each-of-the-%d-guarded-columns-is-refused-by-its-guard's-code" % len(cols), bool(cols)
          and not wrong, wrong)
    print("[3] never stricter than Python: every value the record layer accepts passes")
    def takes(table, **kw):
        return _refusal(con, table, dict(GOOD[table], **kw)) is None
    check("every-path-as-a-primary", all(takes("toward_deltas", primary_=p) and takes("target_binds", primary_=p)
                                         and takes("wound_minted", path=p) for p in PATHS))
    check("every-axis-and-order", all(takes("relationship_deltas", axis=a, ord=o) and takes("rest_declared", axis=a)
                                      for a in records.RELATIONSHIP_AXES for o in records.RELATIONSHIP_ORDERS))
    check("every-rung-on-every-ladder", all(takes("readings", path=p, rung=n) for p, ns in LADDER.items() for n in ns),
          [(p, n) for p, ns in LADDER.items() for n in ns if not takes("readings", path=p, rung=n)][:3])
    check("every-confidence-word", all(takes("readings", confidence=c) for c in readings.CONFIDENCE_WORDS))
    check("every-concept", all(takes("wound_minted", concept=c) for c in concepts.REGISTRY))
    check("every-tier", all(takes("utterances", tier=t) for t in claims.TIERS))
    check("the-ends-of-every-range", all(takes("relationship_deltas", delta=d) and takes("toward_deltas", delta=d)
                                         and takes("wound_deltas", delta=d) for d in (-1, -1.0, 0, 1, 1.0, True))
          and all(takes("wound_minted", intensity=i) for i in (0, 0.0, 1, 1.0)))
    # EVERY RANGE, BOTH SIDES: the validator and the database agree at each bound and just past it (review 1: the
    # guards held copies of the bounds, and each could widen on its untested side, or the validator alone, unseen)
    eps = 1e-9
    for table, col, validate, (lo, hi) in (
            ("relationship_deltas", "delta", lambda v: records.RelationshipDelta("maren", "edda", "trust", v).validate(),
             records.DELTA_RANGE),
            ("toward_deltas", "delta", lambda v: records.TowardDelta("maren", "edda", W, v).validate(),
             records.DELTA_RANGE),
            ("wound_deltas", "delta", lambda v: records.WoundDelta("maren", "fire@WARINESS", v, "event").validate(),
             records.DELTA_RANGE),
            ("wound_minted", "intensity", lambda v: wound._check({"concept": "fire", "path": W, "intensity": v}),
             records.INTENSITY_RANGE)):
        disagree = [v for v in (lo, hi, lo - eps, hi + eps, lo + eps, hi - eps)
                    if (_code_of(lambda: validate(v)) is None) != takes(table, **{col: v})]
        check("%s.%s:-the-validator-and-the-database-agree-at-both-bounds" % (table, col), not disagree, disagree)
    # AN INTEGER PAST A FLOAT'S RANGE is out of range, by the range's own code (review 3: float() raised a bare
    # OverflowError in in_range and in the validation's confidence rule)
    huge = 10 ** 400
    got = [_code_of(lambda: records.RelationshipDelta("maren", "edda", "trust", huge).validate()),
           _code_of(lambda: records.TowardDelta("maren", "edda", W, huge).validate()),
           _code_of(lambda: records.WoundDelta("maren", "fire@WARINESS", huge, "event").validate()),
           _code_of(lambda: wound._check({"concept": "fire", "path": W, "intensity": huge})),
           _code_of(lambda: _commit(validation={"confidence": huge}).validate())]
    check("an-integer-past-a-float's-range-is-refused-by-the-range's-code,-never-an-OverflowError",
          got == ["RECORD_DELTA_RANGE"] * 3 + ["WOUND_INTENSITY_RANGE", "RECORD_VALIDATION_SHAPE"], got)
    con.close()


def _near(word):
    """The spellings a validator loosened to tolerate a model's spelling would take: each case; a space, a tab or a
    no-break space at either end; the separators swapped; trailing punctuation; the full-width form (what NFKC folds);
    the `concept:` prefix a concept carries everywhere it travels (review 3: a loosening outside case and edge
    whitespace passed every suite); quotes around it (review 4: gate.py strips quotes from a model's words). An
    enumeration, so a tripwire, not a proof - declared in the gate."""
    full = "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in word)
    return sorted({word.upper(), word.lower(), word.title(), " " + word, word + " ", "\t" + word, word + "\t",
                   " " + word, word + " ", word.replace(" ", "_"), word.replace("_", " "),
                   word.replace(" ", "-"), word.replace("-", " "), word + ".", word + ",", full, "concept:" + word,
                   '"%s"' % word, "'%s'" % word}
                  - {word})


def near_misses():
    print("[3b] past the exact words: a near miss is written or refused by the record layer, never by the database")
    # Review 2: each one-of guard was held to its words one exact value at a time, so a validator loosened to read a
    # word case- or space-blind - this codebase's own pattern (rungs.index_of, readings.canonical_path) - passed every
    # suite while the database refused the engine's own validated beats. Through the engine's own writer, a near miss
    # is either written or refused by the record layer's code; when the record layer refuses it, the database does too.
    led = Ledger(_path("nearmiss.db"))
    led.create_run("r1", {"catalog_version": "1"})
    turn = [0]

    def beat(**kw):
        turn[0] += 1
        return _code_of(lambda: led.append_turn(_commit(turn=turn[0], **kw)))

    def mint(concept="fire", path=W):
        return dict(wound.make("fire", W, 0.9, "run:1"), concept=concept, path=path, id=wound.wound_id(concept, path))

    #: (table, column, the words, the engine's writer of one value -> the code that refused it, or None when written)
    writers = (
        ("relationship_deltas", "axis", records.RELATIONSHIP_AXES,
         lambda v: beat(rel_deltas=[records.RelationshipDelta("maren", "edda", v, 0.1)])),
        ("relationship_deltas", "ord", records.RELATIONSHIP_ORDERS,
         lambda v: beat(rel_deltas=[records.RelationshipDelta("maren", "edda", "trust", 0.1, order=v)])),
        ("rest_declared", "axis", records.RELATIONSHIP_AXES,
         lambda v: beat(rest_rows=[records.RestDeclared("maren", "edda", v, 0.5)])),
        ("toward_deltas", "primary_", PATHS,
         lambda v: beat(toward_deltas=[records.TowardDelta("maren", "edda", v, 0.1)])),
        ("target_binds", "primary_", PATHS, lambda v: beat(target_binds=[(v, "edda")])),
        ("wound_minted", "path", PATHS, lambda v: beat(wound_mints=[mint(path=v)])),
        ("wound_minted", "concept", tuple(concepts.REGISTRY), lambda v: beat(wound_mints=[mint(concept=v)])),
        ("readings", "confidence", readings.CONFIDENCE_WORDS,
         lambda v: beat(readings=[Reading(path=W, rung=WR, about="edda", confidence=v)])),
        ("utterances", "tier", claims.TIERS,
         lambda v: _code_of(lambda: claims.record(led.con, "r1", 1, "maren", "the millhouse wheel is cracked", tier=v))),
    )
    for table, col, words, write in writers:
        code = next(g[4] for g in guards.GUARDS if g[:2] == (table, col))
        wrong = []
        for v in [n for w in words for n in _near(w)]:
            got = write(v)
            if got not in (None, code) or (got == code and not (_refusal(led.con, table, dict(
                    GOOD[table], **{col: v})) or "").startswith(code + ": ")):
                wrong.append((v, got))
        check("%s.%s:-each-near-miss-is-written-or-refused-by-%s,-never-by-the-database" % (table, col, code),
              not wrong, wrong[:4])
    # THE RUNG AND ITS PATH: the validator reads a rung case- and space-blind and the writer stores the ladder's own
    # spelling, so each near miss of a rung is written; a path is read exactly, so its near miss is refused by the code
    wrong = []
    for p, names in LADDER.items():
        for v in [n for name in names for n in _near(name)]:
            got = beat(readings=[Reading(path=p, rung=v, about="edda")])
            if got not in (None, "READING_RUNG_NOT_ON_PATH"):
                wrong.append((p, v, got))
        for v in _near(p):
            got = beat(readings=[Reading(path=v, rung=names[0], about="edda")])
            if got not in (None, "READING_RUNG_NOT_ON_PATH") or (got and not (_refusal(led.con, "readings", dict(
                    GOOD["readings"], path=v, rung=names[0])) or "").startswith("READING_RUNG_NOT_ON_PATH: ")):
                wrong.append((v, names[0], got))
    check("readings.path+rung:-each-near-miss-of-a-rung-or-a-path-is-written-or-refused-by-the-record-layer",
          not wrong, wrong[:4])
    led.con.close()


# ---- [4] + [5] ---------------------------------------------------------------------------------------------------

def a_migrated_database():
    print("[4] a database migrated from v33 holding rows under a retired vocabulary")
    con = _fresh("old.db")
    con.close()
    raw = sqlite3.connect(_path("old.db"))
    for name in guards.installed(raw):
        raw.execute("DROP TRIGGER IF EXISTS %s" % name)
    _insert(raw, "toward_deltas", dict(GOOD["toward_deltas"], primary_="RAGE"))
    _insert(raw, "relationship_deltas", dict(GOOD["relationship_deltas"], ord="1"))
    raw.execute("PRAGMA user_version = 33")
    raw.commit()
    before = raw.execute("SELECT * FROM toward_deltas").fetchall() + raw.execute(
        "SELECT * FROM relationship_deltas").fetchall()
    check("the-v33-file-carries-no-guard-(the-state-every-book-database-is-in)", guards.installed(raw) == {})
    lacking = [f for f in integrity.sweep(raw) if f["kind"] == "INSERT-GUARD-MISSING"]
    check("[5]-integrity-reports-each-missing-guard-amber", len(lacking) == len(guards.expected())
          and all(f["tier"] == "amber" for f in lacking), [f["subject"] for f in lacking])
    raw.close()
    con = db.connect(_path("old.db"))
    check("it-opens-at-v34-with-every-guard", con.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION == 34
          and set(guards.installed(con)) == set(guards.expected()), con.execute("PRAGMA user_version").fetchone())
    after = con.execute("SELECT * FROM toward_deltas").fetchall() + con.execute(
        "SELECT * FROM relationship_deltas").fetchall()
    check("the-legacy-rows-are-exactly-as-they-were", [tuple(r) for r in after] == [tuple(r) for r in before], after)
    check("a-new-row-like-them-is-refused", (_refusal(con, "toward_deltas", dict(
        GOOD["toward_deltas"], primary_="RAGE")) or "").startswith("RECORD_PRIMARY_UNKNOWN: "))
    found = integrity.sweep(con)
    legacy = {f["subject"]: f for f in found if f["kind"] == "LEGACY-ROWS"}
    check("integrity-counts-them-as-LEGACY-ROWS,-amber", set(legacy) == {"toward_deltas.primary_",
                                                                         "relationship_deltas.ord"}
          and all(f["tier"] == "amber" and f["count"] == 1 for f in legacy.values()), sorted(legacy))
    check("...and-reports-no-red-and-no-missing-guard-once-the-engine-opened-it", not [
        f for f in found if f["tier"] == "red" or f["kind"] == "INSERT-GUARD-MISSING"],
        [(f["kind"], f["subject"]) for f in found if f["tier"] == "red" or f["kind"] == "INSERT-GUARD-MISSING"])
    check("guards.legacy_counts-reads-the-guard's-own-predicate", guards.legacy_counts(con)
          == {"toward_deltas.primary_": 1, "relationship_deltas.ord": 1}, guards.legacy_counts(con))
    con.close()
    raw = sqlite3.connect(_path("old.db"))
    name = "readings" + guards.SUFFIX
    raw.execute("DROP TRIGGER IF EXISTS %s" % name)
    raw.execute(guards.expected()[name].replace("'certain'", "'x'").replace("'sure'", "'certain'"))
    raw.commit()
    stale = [f for f in integrity.sweep(raw) if f["kind"] == "INSERT-GUARD-MISSING"]
    check("[5]-a-guard-that-differs-is-reported-with-the-stamp-it-carries", [(f["subject"], "stamped v%d" %
                                                                               db.SCHEMA_VERSION in f["detail"])
                                                                              for f in stale] == [(name, True)], stale)
    raw.execute("DROP TRIGGER IF EXISTS %s" % name)
    raw.execute(guards.expected()[name].replace("  -- record-guards", "  -- no stamp"))
    raw.commit()
    unstamped = [f["detail"] for f in integrity.sweep(raw) if f["kind"] == "INSERT-GUARD-MISSING"]
    check("...and-an-unstamped-one-as-unstamped", len(unstamped) == 1 and "unstamped" in unstamped[0], unstamped)
    raw.close()
    con = db.connect(_path("old.db"))
    check("...and-the-engine-replaces-it-on-open", guards.installed(con).get(name) == guards.expected()[name])
    con.close()


def _race(book, name, first_sql):
    """Two tools open one stale book together: the second reads its plan (guard `name` missing) and waits on the lock
    while the first installs `first_sql` under its own -> (the second's plan readings, what its open returned or raised,
    the guard that stands). A spy on guards.installed proves the interleaving was set up."""
    db.connect(_path(book)).close()
    raw = sqlite3.connect(_path(book))
    raw.execute("DROP TRIGGER IF EXISTS %s" % name)
    raw.commit()
    raw.close()
    seen, result, real_installed = [], {}, guards.installed
    guards.installed = lambda c: (lambda got: (seen.append(name in got), got)[1])(real_installed(c))
    holder = sqlite3.connect(_path(book), timeout=5, check_same_thread=False)
    holder.execute("BEGIN IMMEDIATE")

    def second():
        try:
            c = db.connect(_path(book))
            result["guard"] = name in real_installed(c)
            c.close()
        except Exception as e:                                       # noqa: BLE001 - what it raised is the finding
            result["error"] = getattr(e, "code", type(e).__name__)
    try:
        t = threading.Thread(target=second)
        t.start()
        deadline = time.time() + 5
        while not seen and time.time() < deadline:
            time.sleep(0.01)
        time.sleep(0.3)                                              # the second open now waits on the lock
        holder.execute(first_sql)                                    # the first tool's install, under its lock
        holder.commit()
        t.join(15)
    finally:
        guards.installed = real_installed
        holder.close()
    raw = sqlite3.connect(_path(book))
    stands = real_installed(raw).get(name)
    raw.close()
    return seen, result, stands


def the_lock_and_an_aged_chronicle():
    print("[5b] a stale open under another writer; a sweep of an aged chronicle")
    con = db.connect(_path("busy.db"))
    con.close()
    raw = sqlite3.connect(_path("busy.db"))
    raw.execute("DROP TRIGGER IF EXISTS readings" + guards.SUFFIX)
    raw.commit()
    raw.close()
    holder = sqlite3.connect(_path("busy.db"), timeout=5, check_same_thread=False)
    holder.execute("BEGIN IMMEDIATE")
    release = threading.Timer(0.8, lambda: (holder.commit(), holder.close()))
    release.start()
    start = time.time()
    try:
        c2 = db.connect(_path("busy.db"))
        got = "readings" + guards.SUFFIX in guards.installed(c2)
        c2.close()
    except Exception as e:                                           # noqa: BLE001 - what it raised is the finding
        got = "%s: %s" % (type(e).__name__, e)
    release.join()
    waited = time.time() - start
    check("a-stale-open-waits-out-another-writer-and-installs-(IMMEDIATE,-not-a-deferred-upgrade)",
          got is True and waited >= 0.5, (got, round(waited, 2)))
    raw = sqlite3.connect(_path("aged.db"))
    raw.executescript(open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read())
    raw.execute("DROP TABLE readings")
    raw.execute("ALTER TABLE relationship_deltas DROP COLUMN ord")
    raw.commit()
    try:
        found, err = integrity.sweep(raw), None
    except Exception as e:                                           # noqa: BLE001 - a sweep raises nothing, by design
        found, err = [], "%s: %s" % (type(e).__name__, e)
    missing = {f["subject"] for f in found if f["kind"] == "INSERT-GUARD-MISSING"}
    check("an-aged-chronicle's-sweep-raises-nothing-and-names-no-guard-for-a-table-it-lacks", err is None
          and "readings" + guards.SUFFIX not in missing and "relationship_deltas" + guards.SUFFIX in missing,
          (err, sorted(missing)))
    check("...and-counts-no-legacy-row-for-a-column-it-lacks", "relationship_deltas.ord" not in guards.legacy_counts(raw),
          guards.legacy_counts(raw))
    raw.close()
    # AN EMPTY TEXT IS BREACH'S, NOT LEGACY'S (review 1: one corrupt row was reported red and amber both; review 2:
    # the rung half went untested)
    raw = sqlite3.connect(_path("prewall.db"))
    raw.execute("CREATE TABLE relationship_deltas (delta_id INTEGER PRIMARY KEY, run_id TEXT, turn INTEGER, "
                "perceiver TEXT, target TEXT, axis TEXT, delta REAL, ord TEXT)")
    raw.execute("INSERT INTO relationship_deltas (run_id, turn, perceiver, target, axis, delta, ord) VALUES "
                "('r1', 1, 'maren', 'edda', '', 0.1, 'first'), ('r1', 2, 'maren', 'edda', 'love', 0.1, 'first')")
    raw.execute("CREATE TABLE readings (reading_id INTEGER PRIMARY KEY, run_id TEXT, turn INTEGER, actor TEXT, "
                "path TEXT, rung TEXT, about TEXT, confidence TEXT)")
    raw.executemany("INSERT INTO readings (run_id, turn, actor, path, rung, about, confidence) VALUES "
                    "(?, ?, ?, ?, ?, ?, ?)", [("r1", 1, "maren", W, "", "edda", ""),
                                              ("r1", 2, "maren", "", WR, "edda", "sure"),
                                              ("r1", 3, "maren", W, "no such rung", "edda", "certain")])
    raw.commit()
    check("legacy_counts-leaves-an-empty-text-to-BREACH-and-counts-the-retired-word,-for-a-word-and-a-rung",
          guards.legacy_counts(raw) == {"relationship_deltas.axis": 1, "readings.path+rung": 1,
                                        "readings.confidence": 1}, guards.legacy_counts(raw))
    raw.close()
    # A CURRENT OPEN TAKES NO LOCK (review 2: an install that always began its transaction passed every suite - every
    # tool's open, the cutter's and the narrator's included, then queued behind any writer and failed behind a long one)
    db.connect(_path("current.db")).close()
    holder = sqlite3.connect(_path("current.db"), timeout=5, check_same_thread=False)
    holder.execute("BEGIN IMMEDIATE")
    real_timeout = db.BUSY_TIMEOUT_SECONDS
    db.BUSY_TIMEOUT_SECONDS = 2.0
    start = time.time()
    try:
        code = _code_of(lambda: db.connect(_path("current.db")).close())
    finally:
        db.BUSY_TIMEOUT_SECONDS = real_timeout
        holder.rollback()
        holder.close()
    took = time.time() - start
    check("a-current-open-takes-no-lock:-it-opens-at-once-beside-another-writer", code is None and took < 1.0,
          (code, round(took, 2)))
    # TWO TOOLS OPEN A STALE BOOK TOGETHER (round 3's own probe: the second read "missing", waited on the lock while the
    # first installed the guard, then met "trigger ... already exists" - a raw error on open). The plan is read again
    # under the lock. The spy proves the race was set up: the second open's first plan saw the guard missing.
    name = "readings" + guards.SUFFIX
    seen, result, _stands = _race("race.db", name, guards.expected()[name])
    check("two-opens-of-a-stale-book-at-once:-the-second-re-reads-its-plan-under-the-lock-and-opens",
          seen[:1] == [False] and result == {"guard": True}, (seen, result))
    # ...AND WHEN THE FIRST IS ANOTHER ENGINE at this version (review 3: the skew check under the lock was held by
    # nothing - without it the second open replaced the other engine's guard, and every suite passed)
    rd = "relationship_deltas" + guards.SUFFIX
    real = records.RELATIONSHIP_AXES
    records.RELATIONSHIP_AXES = real + ("loyalty",)
    try:
        theirs = guards.expected()[rd]
    finally:
        records.RELATIONSHIP_AXES = real
    seen, result, stands = _race("race2.db", rd, theirs)
    check("...and-when-the-first-is-another-engine's-install,-the-second-is-refused-under-the-lock-and-theirs-stands",
          seen[:1] == [False] and result == {"error": "DB_GUARD_VOCABULARY_SKEW"} and stands == theirs,
          (seen, result, stands == theirs))
    # PAST THE BUSY TIMEOUT, the stale open is DB_BUSY_TIMEOUT - as every other writer names the lock - not a raw error
    raw = sqlite3.connect(_path("busy.db"))
    raw.execute("DROP TRIGGER IF EXISTS readings" + guards.SUFFIX)
    raw.commit()
    raw.close()
    holder = sqlite3.connect(_path("busy.db"), timeout=5, check_same_thread=False)
    holder.execute("BEGIN IMMEDIATE")
    real_timeout = db.BUSY_TIMEOUT_SECONDS
    db.BUSY_TIMEOUT_SECONDS = 0.3
    try:
        code = _code_of(lambda: db.connect(_path("busy.db")))
    finally:
        db.BUSY_TIMEOUT_SECONDS = real_timeout
        holder.commit()
        holder.close()
    check("...and-a-lock-held-past-the-timeout-is-DB_BUSY_TIMEOUT", code == "DB_BUSY_TIMEOUT", code)


def the_doctor_and_the_engine_agree():
    print("[5c] integrity reads the guards as the open does: a book the engine refuses is red, naming the code")
    # Review 3: the read-only doctor reported every book the engine refuses to open as amber "the engine installs it
    # on open" and exited clean. integrity now reads guards.survey, the reading install acts on.
    def read_only(name):
        return sqlite3.connect("file:%s?mode=ro" % _path(name).replace(os.sep, "/"), uri=True)
    real = records.RELATIONSHIP_AXES
    records.RELATIONSHIP_AXES = real + ("loyalty",)                 # another engine's guard set, at this version
    try:
        _fresh("skewed.db").close()
    finally:
        records.RELATIONSHIP_AXES = real
    con = _fresh("taken.db")                                         # a trigger not ours holding a guard's name
    con.execute("DROP TRIGGER IF EXISTS readings" + guards.SUFFIX)
    con.execute("CREATE TRIGGER Readings_Record_Guard BEFORE INSERT ON llm_calls BEGIN SELECT 1; END")
    con.commit()
    con.close()
    real_guards = guards.GUARDS                                      # another engine's guard, under two names
    extra = ("llm_calls", "purpose", "one-of", lambda: ("act", "compose"), "RECORD_FIELD_TYPE", "a purpose vocabulary")
    try:
        guards.GUARDS = real_guards + (extra,)
        theirs = guards.expected()["llm_calls" + guards.SUFFIX]
    finally:
        guards.GUARDS = real_guards
    for book, sql in (("foreign.db", theirs), ("foreign_named.db", theirs.replace(
            "CREATE TRIGGER llm_calls" + guards.SUFFIX, "CREATE TRIGGER purpose_guard", 1))):
        _fresh(book).close()
        raw = sqlite3.connect(_path(book))
        raw.execute(sql)
        raw.commit()
        raw.close()
    rd = "relationship_deltas" + guards.SUFFIX                      # a same-version stamp this engine cannot read
    ours = guards.expected()[rd]
    line = next(ln for ln in ours.splitlines() if "-- record-guards" in ln)
    _fresh("unreadable.db").close()
    raw = sqlite3.connect(_path("unreadable.db"))
    raw.execute("DROP TRIGGER IF EXISTS %s" % rd)
    raw.execute(ours.replace(line, "  -- record-guards v%d wall %s" % (db.SCHEMA_VERSION, guards.vocabulary())))
    raw.commit()
    raw.close()
    _fresh("newer.db").close()                                       # a book a newer engine stepped
    raw = sqlite3.connect(_path("newer.db"))
    raw.execute("PRAGMA user_version = %d" % (db.SCHEMA_VERSION + 1))
    raw.commit()
    raw.close()
    for book, code in (("skewed.db", "DB_GUARD_VOCABULARY_SKEW"), ("taken.db", "DB_GUARD_NAME_TAKEN"),
                       ("newer.db", "DB_SCHEMA_TOO_NEW"), ("foreign.db", "DB_GUARD_VOCABULARY_SKEW"),
                       ("foreign_named.db", "DB_GUARD_VOCABULARY_SKEW"),
                       ("unreadable.db", "DB_GUARD_VOCABULARY_SKEW")):
        ro = read_only(book)
        found = integrity.sweep(ro)
        ro.close()
        refused = [f for f in found if f["kind"] == "BOOK-REFUSED"]
        opened = _code_of(lambda: db.connect(_path(book)).close())
        check("%s:-integrity-reports-it-red,-naming-%s,-the-code-the-open-raises" % (book, code), opened == code
              and bool(refused) and all(f["tier"] == "red" and "(%s)" % code in f["detail"] for f in refused)
              and not [f for f in found if f["kind"] == "INSERT-GUARD-MISSING"],
              (opened, [(f["kind"], f["subject"], f["detail"][:90]) for f in found
                        if f["kind"] in ("BOOK-REFUSED", "INSERT-GUARD-MISSING")]))
    # THE WAY OUT IN ONE HOP (review 5): the refusal and the doctor both name the command, with this book's own file
    try:
        db.connect(_path("skewed.db")).close()
        said = ""
    except EngineError as e:
        said = str(e)
    ro = read_only("skewed.db")
    told = [f["detail"] for f in integrity.sweep(ro) if f["kind"] == "BOOK-REFUSED"]
    ro.close()
    check("...and-the-refusal-and-the-doctor-both-name-release_guards-with-this-book's-file",
          all("python scripts/release_guards.py" in t and "skewed.db\"" in t for t in [said] + told) and told,
          (said[-150:], [t[-150:] for t in told]))
    # A REFUSED OPEN WRITES NOTHING, and the doctor reading the book before any migration agrees with the open after
    # it (review 4: the open migrated the book, then refused it; a table the migration creates hid a taken name)
    raw = sqlite3.connect(_path("aged_taken.db"))
    raw.executescript(open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read())
    raw.execute("DROP TABLE readings")
    raw.execute("CREATE TRIGGER Readings_Record_Guard BEFORE INSERT ON llm_calls BEGIN SELECT 1; END")
    raw.execute("PRAGMA user_version = 23")
    raw.commit()
    raw.close()
    ro = read_only("aged_taken.db")
    found = [f for f in integrity.sweep(ro) if f["kind"] in ("BOOK-REFUSED", "INSERT-GUARD-MISSING")]
    ro.close()
    opened = _code_of(lambda: db.connect(_path("aged_taken.db")).close())
    raw = sqlite3.connect(_path("aged_taken.db"))
    left = (raw.execute("PRAGMA user_version").fetchone()[0],
            raw.execute("SELECT COUNT(*) FROM sqlite_master WHERE name = 'readings'").fetchone()[0])
    raw.close()
    check("an-aged-book-with-a-taken-guard-name:-refused-before-its-migration,-which-writes-nothing,-and-the-doctor-"
          "agrees", opened == "DB_GUARD_NAME_TAKEN" and left == (23, 0) and [f["kind"] for f in found]
          == ["BOOK-REFUSED"] and "(DB_GUARD_NAME_TAKEN)" in found[0]["detail"], (opened, left, [(f["kind"], f["subject"])
                                                                                          for f in found]))
    # AN OLDER ENGINE'S GUARD THIS ONE DOES NOT OWN (a table no longer guarded, not in RETIRED): reported, left alone
    _fresh("unowned.db").close()
    raw = sqlite3.connect(_path("unowned.db"))
    raw.execute(theirs.replace("-- record-guards v%d " % db.SCHEMA_VERSION, "-- record-guards v%d "
                               % (db.SCHEMA_VERSION - 1), 1))
    raw.commit()
    raw.close()
    ro = read_only("unowned.db")
    found = [(f["kind"], f["tier"], f["subject"]) for f in integrity.sweep(ro) if f["kind"] == "INSERT-GUARD-UNOWNED"]
    ro.close()
    opened = _code_of(lambda: db.connect(_path("unowned.db")).close())
    check("an-older-engine's-guard-this-one-does-not-own-is-reported-amber-and-left", opened is None and found
          == [("INSERT-GUARD-UNOWNED", "amber", "llm_calls" + guards.SUFFIX)], (opened, found))
    # THE DOCTOR'S --fold on a refused book reports it, never a traceback (review 4)
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "doctor.py"), "--fold", _path("skewed.db")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=REPO,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8"))
    check("doctor---fold-on-a-refused-book-reports-it-red,-never-a-traceback", r.returncode == 1
          and "--fold skipped" in r.stdout and "BOOK-REFUSED" in r.stdout and "Traceback" not in r.stderr,
          (r.returncode, r.stderr[-160:]))
    # THE WAY OUT, one command in any shell (Fable's read: the documented one-liner ran in Git Bash, not PowerShell):
    # every stamped trigger goes - this engine's, another engine's, under any name - a trigger with no stamp stays,
    # and the next open installs this engine's own
    def release(path):
        return subprocess.run([sys.executable, os.path.join(REPO, "scripts", "release_guards.py"), path],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=REPO,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8"))

    def rows(c):
        return {t: sorted(repr(tuple(x)) for x in c.execute('SELECT * FROM "%s"' % t))
                for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}

    raw = sqlite3.connect(_path("foreign_named.db"))
    raw.execute("CREATE TRIGGER audit_llm BEFORE INSERT ON llm_calls BEGIN SELECT 1; END")
    raw.commit()
    before = rows(raw)
    raw.close()
    r = release(_path("foreign_named.db"))
    raw = sqlite3.connect(_path("foreign_named.db"))
    left = sorted(n for (n,) in raw.execute("SELECT name FROM sqlite_master WHERE type = 'trigger' AND (sql LIKE "
                                            "'%-- record-guards v%' OR name = 'audit_llm')"))
    untouched = rows(raw) == before and any(before.values())
    raw.close()
    opened = _code_of(lambda: db.connect(_path("foreign_named.db")).close())
    check("release_guards-drops-every-stamped-trigger,-keeps-an-unstamped-one,-touches-no-row,-and-the-book-then-opens",
          r.returncode == 0 and left == ["audit_llm"] and untouched and opened is None and "purpose_guard" in r.stdout,
          (r.returncode, left, untouched, opened, r.stdout[-120:]))
    # THE WRITABLE OPEN LIVES IN db.py (tests/test_integrity.py's rule) - and it opens a book, never makes one
    gone = _path("no_book.db")
    r = release(gone)
    check("...and-a-path-with-no-file-refuses-DB_PATH_INVALID-(the-script-exits-2)-and-creates-none",
          _code_of(lambda: db.release_guards(gone)) == "DB_PATH_INVALID" and r.returncode == 2
          and not os.path.exists(gone), (r.returncode, os.path.exists(gone), r.stderr[-120:]))
    with open(_path("maren_notes.db"), "w", encoding="utf-8") as f:
        f.write("maren's notes on the millhouse, not a chronicle\n")
    r = release(_path("maren_notes.db"))
    with open(_path("maren_notes.db"), encoding="utf-8") as f:
        same = f.read() == "maren's notes on the millhouse, not a chronicle\n"
    check("...and-a-file-that-is-not-a-database-exits-1,-left-as-it-was", r.returncode == 1 and same,
          (r.returncode, same, r.stderr[-120:]))
    db.connect(_path("held.db")).close()
    holder = sqlite3.connect(_path("held.db"), timeout=5)
    holder.execute("BEGIN IMMEDIATE")
    real = db.BUSY_TIMEOUT_SECONDS
    db.BUSY_TIMEOUT_SECONDS = 0.3
    try:
        code = _code_of(lambda: db.release_guards(_path("held.db")))
    finally:
        db.BUSY_TIMEOUT_SECONDS = real
        holder.rollback()
        holder.close()
    raw = sqlite3.connect(_path("held.db"))
    stamped = sum(1 for (s,) in raw.execute("SELECT sql FROM sqlite_master WHERE type = 'trigger'") if guards.stamp(s))
    raw.close()
    check("...and-under-another-writer-past-the-busy-timeout-refuses-DB_BUSY_TIMEOUT-and-drops-nothing",
          code == "DB_BUSY_TIMEOUT" and stamped == len(guards.expected()), (code, stamped, len(guards.expected())))
    con = db.connect(_path("foreign_named.db"))
    con.execute("INSERT INTO runs (run_id, created_at, config) VALUES ('r9', 'now', '{}')")
    check("...and-release-refuses-a-connection-with-a-transaction-open", _code_of(lambda: guards.release(con))
          == "DB_TRANSACTION_OPEN", _code_of(lambda: guards.release(con)))
    con.rollback()
    con.close()
    _fresh("current2.db").close()
    ro = read_only("current2.db")
    found = [(f["kind"], f["subject"]) for f in integrity.sweep(ro) if f["kind"] in ("BOOK-REFUSED",
                                                                                      "INSERT-GUARD-MISSING")]
    ro.close()
    check("...and-a-current-book-reports-neither", not found, found)


# ---- [6] ---------------------------------------------------------------------------------------------------------

def the_record_layer():
    print("[6] the record layer: the fields nothing checked")
    mint = wound.make("fire", W, 0.9, "run:1")
    check("a-well-formed-mint-passes", _code_of(lambda: _commit(wound_mints=[mint]).validate()) is None)
    for name, mints, code in (("a-mint-naming-no-registered-concept", [dict(mint, concept="the millhouse ghost")],
                               "WOUND_CONCEPT_UNKNOWN"),
                              ("a-mint-on-a-retired-path", [dict(mint, path="RAGE")], "WOUND_PATH_UNKNOWN"),
                              ("a-mint-past-full-strength", [dict(mint, intensity=1.5)], "WOUND_INTENSITY_RANGE"),
                              ("a-mint-that-is-not-a-map", ["fire"], "WOUND_NOT_A_DICT"),
                              ("mints-that-are-not-a-list", mint, "RECORD_FIELD_TYPE"),
                              # every field write_mints keeps (review 1: only concept, path and intensity were read)
                              ("a-mint-whose-id-is-not-its-(concept,-path)'s", [dict(mint, id="cold@DEFLATION")],
                               "WOUND_MINT_ID_MISMATCH"),
                              ("a-mint-with-no-id", [{k: v for k, v in mint.items() if k != "id"}],
                               "WOUND_MINT_ID_MISMATCH"),
                              ("a-mint-whose-source-is-a-list", [dict(mint, source=["run:1"])], "WOUND_MINT_FIELD_TYPE"),
                              ("a-mint-whose-text-is-a-number", [dict(mint, text=5)], "WOUND_MINT_FIELD_TYPE"),
                              # a None is not an absent field: it reached wound_minted's NOT NULL inside the beat
                              ("a-mint-whose-source-is-None", [dict(mint, source=None)], "WOUND_MINT_FIELD_TYPE"),
                              ("a-mint-whose-text-is-None", [dict(mint, text=None)], "WOUND_MINT_FIELD_TYPE"),
                              ("a-mint-whose-triggers-are-a-set", [dict(mint, trigger={"smoke"})],
                               "WOUND_MINT_FIELD_TYPE")):
        check("TurnCommit-refuses-%s:-%s" % (name, code), _code_of(lambda: _commit(wound_mints=mints).validate())
              == code, _code_of(lambda: _commit(wound_mints=mints).validate()))
    led = Ledger(_path("ledger.db"))
    led.create_run("r1", {"catalog_version": "1"})
    check("write_mints-runs-the-same-whole-mint-check-(the-write's-own-wall)", _code_of(
        lambda: wound.write_mints(led.con, "r1", 9, "maren", [dict(mint, id="cold@DEFLATION")]))
          == "WOUND_MINT_ID_MISMATCH")
    led.con.rollback()
    bad = _commit(wound_mints=[dict(mint, concept="the millhouse ghost")])
    # OBSERVED AT THE WRITE (review 2: "0 turns and the code" held on the old path too, where write_mints refused the
    # mint from inside the beat's transaction and the beat rolled back): no INSERT is attempted at all
    seen = []
    led.con.set_trace_callback(seen.append)
    try:
        code = _code_of(lambda: led.append_turn(bad))
    finally:
        led.con.set_trace_callback(None)
    wrote = [s for s in seen if s.lstrip().split(" ", 1)[0].upper() in ("BEGIN", "INSERT")]
    check("...before-any-INSERT-is-attempted-(not-a-rolled-back-beat)", code == "WOUND_CONCEPT_UNKNOWN" and not wrote
          and led.con.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == 0, (code, wrote[:2]))
    tagged = {"ok": True, "flags": [{"code": "TAG_X", "detail": "d"}], "confidence": 0.65, "escalate": False,
              "reply_extra": ["note"]}
    for name, v in (("empty", {}), ("the-drivers'-shape", tagged), ("the-read-along's", {"ok": True, "flags": []}),
                    ("ok-alone", {"ok": True}),
                    # the check mirrors the ledger's own serialiser, which writes a NaN (review 1: a stricter
                    # allow_nan=False went unseen)
                    ("holding-a-NaN-the-ledger's-serialiser-writes", {"ok": True, "flags": [], "x": float("nan")})):
        check("validation-%s-passes" % name, _code_of(lambda: _commit(validation=v).validate()) is None,
              _code_of(lambda: _commit(validation=v).validate()))
    for name, v, code in (("ok-as-text", {"ok": "yes"}, "RECORD_VALIDATION_SHAPE"),
                          ("flags-as-text", {"flags": "none"}, "RECORD_VALIDATION_SHAPE"),
                          ("confidence-past-one", {"confidence": 1.5}, "RECORD_VALIDATION_SHAPE"),
                          ("confidence-as-true", {"confidence": True}, "RECORD_VALIDATION_SHAPE"),
                          ("escalate-as-text", {"escalate": "no"}, "RECORD_VALIDATION_SHAPE"),
                          ("a-value-json-cannot-write", {"ok": True, "flags": [], "why": object()},
                           "RECORD_VALIDATION_SHAPE"),
                          ("a-value-nested-too-deep-to-write", {"ok": True, "flags": [], "why": _deep(5000)},
                           "RECORD_VALIDATION_SHAPE"),
                          ("not-a-map", ["ok"], "RECORD_FIELD_TYPE")):
        check("validation-%s-is-refused:-%s" % (name, code), _code_of(lambda: _commit(validation=v).validate())
              == code, _code_of(lambda: _commit(validation=v).validate()))
    for name, lands, code in (("an-empty-id", [""], "RECORD_LIST_ITEM_TYPE"), ("a-blank-id", ["  "],
                              "RECORD_LIST_ITEM_TYPE"), ("a-number", [5], "RECORD_LIST_ITEM_TYPE"),
                              ("a-name", ["edda"], None)):
        check("lands_on-%s:-%s" % (name, code), _code_of(lambda: _commit(lands_on=lands).validate()) == code,
              _code_of(lambda: _commit(lands_on=lands).validate()))
    check("Reading-refuses-a-confidence-outside-the-three-words", _code_of(
        lambda: Reading(path=W, rung=WR, confidence="certain").validate()) == "READING_CONFIDENCE_UNKNOWN")
    wrote = _code_of(lambda: led.append_turn(_commit(turn=2, readings=[Reading(path=W, rung="  " + WR.upper() + " ",
                                                                                about="edda")])))
    stored = led.con.execute("SELECT rung FROM readings WHERE turn = 2").fetchone()
    check("readings.write-stores-the-ladder's-own-spelling", wrote is None and stored is not None and stored[0] == WR,
          (wrote, stored and stored[0]))
    # ANOTHER VOCABULARY'S GUARD: this ledger's guard was built before the registry grew, as one installed by an older
    # engine would be; the record layer accepts the new concept and the database refuses it - by its own name
    new = "the millhouse flood"
    concepts.REGISTRY[new] = concepts.REGISTRY["fire"]
    try:
        skew = _code_of(lambda: led.append_turn(_commit(turn=3, wound_mints=[wound.make(new, W, 0.9, "run:3")])))
    finally:
        del concepts.REGISTRY[new]
    check("a-beat-refused-by-a-guard-of-another-vocabulary-is-named-DB_GUARD_REFUSED", skew == "DB_GUARD_REFUSED",
          skew)
    # ...AND BY THE SAME ENGINE'S OTHER WRITERS into a guarded table, each in its own transaction (review 2: the seed of
    # an edge's rests and the keeper's utterances let the same refusal out as a bare IntegrityError)
    real_axes, real_tiers = records.RELATIONSHIP_AXES, claims.TIERS
    records.RELATIONSHIP_AXES = bond_rest.RELATIONSHIP_AXES = real_axes + ("loyalty",)
    claims.TIERS = real_tiers + ("rumoured",)
    try:
        seeded = _code_of(lambda: bond_rest.seed(led.con, "r1", 4, "maren", {"edda": {"loyalty": 0.5}}))
        said = _code_of(lambda: claims.record(led.con, "r1", 4, "maren", "the millhouse wheel is cracked",
                                              tier="rumoured"))
    finally:
        records.RELATIONSHIP_AXES = bond_rest.RELATIONSHIP_AXES = real_axes
        claims.TIERS = real_tiers
    check("...and-by-bond_rest.seed-and-claims.record-too", seeded == said == "DB_GUARD_REFUSED", (seeded, said))
    led.con.close()


# ---- [7] ---------------------------------------------------------------------------------------------------------

def the_schema_copies():
    print("[7] schema.sql's own IN-list CHECKs hold exactly the constants they copy")
    # Review 2: these predate the gate and no guard builds them - they are copies, the class CLAUDE.md tabulates. A
    # CHECK moves only by a table rebuild (SQLite cannot ALTER one), so a constant that grows a word leaves its copy
    # refusing that word, on a fresh database too. Pinned here: a changed constant fails this section until its CHECK
    # in schema.sql, and a rebuild step in db._migrate for the books that already hold the table, move with it.
    from src.engine import attachments, bible, edl, narration_modes, snapshots
    ref = sqlite3.connect(":memory:")
    ref.executescript(open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read())
    ddl = {t: re.sub(r"--[^\n]*", "", s) for t, s in ref.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'")}
    ref.close()
    items = {(t, m.group(1)): [w.strip() for w in m.group(2).split(",")]
             for t, s in ddl.items() for m in re.finditer(r"CHECK\s*\(\s*(\w+)\s+IN\s*\((.*?)\)\s*\)", s, re.S)}
    lists = {k: sorted(w[1:-1] for w in v) for k, v in items.items()}
    copies = {("wound_deltas", "kind"): records.WOUND_DELTA_KINDS, ("rest_declared", "source"): records.REST_SOURCES,
              ("attachment_declared", "source"): records.ATTACHMENT_SOURCES,
              ("attachment_declared", "sign"): attachments.SIGNS, ("events", "visibility"): records.VISIBILITIES,
              ("bible_laws", "domain"): law._DOMAINS, ("bible_laws", "modality"): law._MODALITIES,
              ("bible_laws", "epistemic"): law._EPISTEMIC, ("claim_resolutions", "verdict"): claims.TIERS,
              ("snapshots", "kind"): snapshots.KINDS, ("edl", "kind"): edl.KINDS, ("bible_entities", "kind"): bible._KINDS,
              ("scenes", "voice"): narration_modes.VOICES, ("scenes", "knowledge"): narration_modes.KNOWLEDGE}
    own = {("runs", "status")}                         # no constant names these words: the list is its own authority
    check("every-IN-list-CHECK-in-schema.sql-is-pinned-here-or-named-as-its-own", set(lists) == set(copies) | own,
          sorted(set(lists) ^ (set(copies) | own)))
    # the parser is an instrument: every `IN (` in a table's DDL is one it read, and every item it read is one quoted
    # literal (review 3: a misparse counted as a read, so a CHECK it could not read was reported as a moved word)
    ins = sum(len(re.findall(r"\bIN\s*\(", s, re.I)) for s in ddl.values())
    misread = sorted((k, w) for k, v in items.items() for w in v if not re.fullmatch(r"'[^']*'", w))
    check("...and-the-parser-read-every-IN-list-the-DDL-holds,-each-item-one-quoted-literal", ins == len(lists)
          and not misread, (ins, len(lists), misread[:3]))
    for (table, col), const in sorted(copies.items()):
        check("schema.sql-%s.%s-holds-exactly-its-constant" % (table, col), lists.get((table, col)) == sorted(const),
              (lists.get((table, col)), sorted(const)))


def main():
    print("test_record_guards.py - the record's second wall, on every database the engine opens (gate record-guards)\n")
    for section in (built_from_the_constants, a_fresh_database, near_misses, a_migrated_database,
                    the_lock_and_an_aged_chronicle, the_doctor_and_the_engine_agree, the_record_layer, the_schema_copies):
        try:
            section()
        except Exception as e:                                       # noqa: BLE001 - a harness reports
            check("%s RAISED %s" % (section.__name__, type(e).__name__), False, str(e)[:200])
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
