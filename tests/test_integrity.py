#!/usr/bin/env python3
"""test_integrity.py — the sweep goes red on a database built the way the defect actually arises.

THE FIXTURE IS NOT HAND-WRITTEN, and that is the point. A hand-broken schema proves the sweep can
read a schema someone wrote to be broken. This builds the REAL `schema.sql` with its emptiness
CHECKs stripped, stamps a pre-v21 `user_version`, and then MIGRATES IT WITH THE REAL ENGINE — which
is the step that makes it indistinguishable from a real aged chronicle in this repo. After
`Ledger(path)` the file reports `user_version = 22` and the guards are still gone.

Measured on a copy of this repo's oldest chronicle, 2026-09-02: v12 -> v22, all 40 triggers arrive, all 5 missing
tables arrive, and 50 of 68 per-column guards do not. `INSERT INTO runs (run_id,...) VALUES ('')`
then succeeds. This file is that measurement, frozen.

THE CONTROL IS LOAD-BEARING: a fresh database must report ZERO. A sweep that is red on everything is
a sweep nobody reads, and this repo has already retired one guard for that reason.

Script-style, stdlib only, exit 0 = all pass.
"""
import io
import json
import os
import re
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import integrity                              # noqa: E402
from src.engine.ledger import Ledger                          # noqa: E402
from src.engine.records import TurnCommit, PRIMARIES          # noqa: E402

SCHEMA = os.path.join(REPO, "src", "engine", "schema.sql")
FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _fresh(tmp, name="fresh"):
    """A database created by this engine today. The control."""
    led = Ledger(os.path.join(tmp, name + ".db"))
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    for cid in ("maren", "edda"):
        led.register_character("r1", cid, {"name": cid.title()}, {"temperament": "authored"})
    return led


def _premigration(tmp, name="old"):
    """A pre-v21 database, built from the REAL schema with its emptiness CHECKs stripped, then
    migrated by the REAL engine. -> path. This is the shape a real aged chronicle here is in."""
    path = os.path.join(tmp, name + ".db")
    schema = io.open(SCHEMA, encoding="utf-8").read()
    stripped, n = re.subn(r"\s*CHECK\s*\(\s*\w+\s*<>\s*''\s*\)", "", schema)
    assert n >= 50, "the strip removed only %d CHECKs — the fixture is not pre-v21" % n
    con = sqlite3.connect(path)
    con.executescript(stripped)
    con.execute("PRAGMA user_version=20")
    con.commit()
    con.close()
    Ledger(path).con.close()                                  # the real migration, v20 -> current
    return path


def test_a_MIGRATED_database_keeps_its_original_columns(tmp):
    """The measurement this whole unit exists for."""
    path = _premigration(tmp)
    con = sqlite3.connect(path)
    version, declared, missing = integrity.schema_summary(con)
    check("the-migration-stamped-the-CURRENT-version", version == 22, "user_version=%d" % version)
    check("...and-the-walls-did-NOT-arrive", missing >= 50,
          "%d of %d guards missing" % (missing, declared))
    # ...and the consequence, not merely the count.
    try:
        with con:
            con.execute("INSERT INTO runs (run_id, created_at, status, config) "
                        "VALUES ('', 'now', 'active', '{}')")
        check("an-EMPTY-run_id-inserts-clean-on-a-migrated-db", True)
    except sqlite3.IntegrityError as e:
        check("an-EMPTY-run_id-inserts-clean-on-a-migrated-db", False,
              "it was refused, so the fixture is not reproducing the defect: %s" % e)
    con.close()


def test_a_FRESH_database_reports_NOTHING(tmp):
    """THE LOAD-BEARING CONTROL. A sweep that is red on everything is a sweep nobody reads."""
    led = _fresh(tmp)
    findings = integrity.sweep(led.con)
    check("a-fresh-database-is-CLEAN", not findings,
          "%s" % [(f["kind"], f["subject"]) for f in findings][:6])
    _v, declared, missing = integrity.schema_summary(led.con)
    check("...and-carries-every-declared-guard", missing == 0,
          "%d of %d missing on a FRESH db" % (missing, declared))


def test_the_BREACH_tier_finds_rows_a_fresh_db_would_have_refused(tmp):
    """RED. Three values walked through three missing walls; a fresh database refuses all three."""
    path = _premigration(tmp, "breach")
    con = sqlite3.connect(path)
    with con:
        con.execute("INSERT INTO runs (run_id, created_at, status, config) "
                    "VALUES ('', 'now', 'active', '{}')")
        con.execute("INSERT INTO runs (run_id, created_at, status, config) "
                    "VALUES ('r1', 'now', 'active', '{}')")
        con.execute("INSERT INTO events (run_id, turn, caused_at, effective_at, type, actor, "
                    "visibility, payload) VALUES ('r1', 2, 2, 2, '', 'maren', 'public', '{}')")
    breaches = {f["subject"] for f in integrity.sweep(con) if f["kind"] == "BREACH"}
    check("BREACH-names-the-empty-run_id", "runs.run_id" in breaches, str(breaches))
    check("BREACH-names-the-empty-event-type", "events.type" in breaches, str(breaches))
    con.close()

    # the other half: a fresh database refuses the same inserts outright, which is what makes the
    # finding a MIGRATION fact rather than a claim about the engine's writers.
    led = _fresh(tmp, "control")
    try:
        with led.con:
            led.con.execute("INSERT INTO runs (run_id, created_at, status, config) "
                            "VALUES ('', 'now', 'active', '{}')")
        check("a-fresh-db-REFUSES-the-same-insert", False, "it was accepted")
    except sqlite3.IntegrityError:
        check("a-fresh-db-REFUSES-the-same-insert", True)


def test_an_ORPHAN_row_is_found_where_the_FK_pragma_is_blind(tmp):
    """RED, and NOT a migration fact — a brand-new database accepts the same orphan.

    `schema.sql` declares `REFERENCES runs(run_id)` on seven tables and omits it on fourteen, so
    `PRAGMA foreign_key_check` cannot see an orphan in `current_state`. That is why the sweep runs
    an anti-join ALONGSIDE the pragma rather than trusting it."""
    led = _fresh(tmp, "orphan")
    with led.con:
        led.con.execute("INSERT INTO current_state (run_id, char_id, turn, affect, condition) "
                        "VALUES ('ghost-run', 'nobody', 0, '{}', '{}')")
    findings = integrity.sweep(led.con)
    orphans = [f for f in findings if f["kind"] == "ORPHAN-ROWS"]
    check("ORPHAN-ROWS-found-it", any(f["subject"] == "current_state" for f in orphans),
          str([f["subject"] for f in orphans]))
    check("...on-a-FRESH-database", True)                     # stated: this is a schema gap, not drift
    check("...and-the-FK-pragma-is-blind-to-it",
          not led.con.execute("PRAGMA foreign_key_check").fetchall(),
          "the pragma saw it after all — then the anti-join is redundant and should be dropped")


def test_a_PHANTOM_actor_is_found_where_RESUME_returns_OK(tmp):
    """RED, and the point is the second half: `resume` is blind to this.

    `Ledger._seed` reads `characters` to seed the fold's agents, but `_project` setdefaults ANY
    string an event names, so a phantom folds identically both ways."""
    led = _fresh(tmp, "phantom")
    led.append_turn(TurnCommit(run_id="r1", turn=0, actor="nobody-registered",
                               thought="t", action="a", tags={"type": "mundane"},
                               affect={p: 0.5 for p in PRIMARIES}, events=[]))
    findings = integrity.sweep(led.con)
    phantom = [f for f in findings if f["kind"] == "PHANTOM-TURN-ACTOR"]
    check("PHANTOM-TURN-ACTOR-found-it", bool(phantom), str(findings))
    check("...and-names-the-actor", phantom and "nobody-registered" in phantom[0]["detail"],
          phantom[0]["detail"] if phantom else "")
    try:
        led.resume("r1")
        check("...while-RESUME-returns-OK-which-is-WHY-this-check-exists", True)
    except Exception as e:                                    # noqa: BLE001
        check("...while-RESUME-returns-OK-which-is-WHY-this-check-exists", False,
              "resume already catches it: %s" % e)


def test_a_CROSS_DRIVER_resume_is_not_reported_as_a_PHANTOM(tmp):
    """THE FALSE POSITIVE, and it fired on the flow CLAUDE.md documents as first-class.

    Registration used to run only inside each driver's create-run branch, so a run started by
    `direct.py` (one character) and continued by `scene.py` (a cast) committed turns for people the
    chronicle never recorded as existing. `resume` returns OK on it — `_seed` reads `characters`
    while `_project` setdefaults ANY string an event names, so the phantom folds identically both
    ways — and the sweep called a supported flow corruption.

    The fix was DRIVER-SIDE, not a narrowing of the check: the finding was true. An unregistered
    actor's agent row exists only by setdefault, so their life_status and location come from a
    default rather than a sheet. Both drivers now register a late-joining cast member on every
    path, which is a legal append (schema v20 refuses UPDATE and DELETE on `characters`, not
    INSERT). The check keeps its teeth — the second half of this test proves it."""
    led = _fresh(tmp, "crossdriver")
    for turn, who in ((0, "maren"), (1, "edda")):
        led.append_turn(TurnCommit(run_id="r1", turn=turn, actor=who, thought="t", action="a",
                                   tags={"type": "mundane"},
                                   affect={p: 0.5 for p in PRIMARIES}, events=[]))
    check("a-REGISTERED-second-actor-is-not-a-phantom",
          not [f for f in integrity.sweep(led.con) if f["kind"] == "PHANTOM-TURN-ACTOR"],
          "the fixture registers both, so this must be silent")

    # ...and the teeth: somebody genuinely absent from the cast STILL reports.
    led.append_turn(TurnCommit(run_id="r1", turn=2, actor="nobody-registered", thought="t",
                               action="a", tags={"type": "mundane"},
                               affect={p: 0.5 for p in PRIMARIES}, events=[]))
    check("...but-a-REAL-phantom-still-reports",
          bool([f for f in integrity.sweep(led.con) if f["kind"] == "PHANTOM-TURN-ACTOR"]),
          "narrowing the check to silence the false positive would have removed its teeth")


def test_both_DRIVERS_register_a_late_joining_cast_member(_tmp):
    """ANTI-ROT for the fix above. Both drivers must register OUTSIDE their create-run branch.

    Asserted structurally rather than by grepping for a call: the call existed before this fix —
    it was simply in the wrong place, inside `if <new run>:`. What changed is WHERE, so that is
    what the test reads."""
    import ast
    for name in ("direct.py", "scene.py"):
        src = io.open(os.path.join(REPO, "scripts", name), encoding="utf-8").read()
        tree = ast.parse(src)
        main = next((n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name == "main"), None)

        def reg_lines(node):
            return [n.lineno for n in ast.walk(node)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "register_character"]

        # THE PROPERTY IS "REGISTERS AFTER CONSULTING THE EXISTING CAST", not "calls it somewhere"
        # and not "calls it unconditionally". The call ALREADY existed before this fix — it was in
        # the wrong PLACE, inside the create-run branch — and registration legitimately sits behind
        # `if cid not in _known`, so an unconditional-call assertion would be wrong. A first draft
        # asserted "a top-level statement contains the call" and passed with the body replaced by
        # `if False:`, because an `if` at top level is still a top-level statement.
        known_line = next((n.lineno for n in ast.walk(tree)
                           if isinstance(n, ast.Assign)
                           and any(getattr(t, "id", "") == "_known" for t in n.targets)), None)
        check("%s-queries-the-EXISTING-cast" % name, known_line is not None,
              "no `_known` set — re-registering an existing member would raise on the primary key")
        after = [ln for ln in reg_lines(main) if known_line and ln > known_line]
        check("%s-registers-AFTER-consulting-it" % name, bool(after),
              "every register_character call precedes the _known query, so it is still create-only")
        body = ast.get_source_segment(src, main) or ""
        check("%s-the-registration-is-REACHABLE" % name,
              "if False" not in body and "if 0:" not in body,
              "the registration is disabled by a constant condition")

def test_a_TURN_GAP_is_found_and_a_SKIPPED_turn_is_NOT(tmp):
    """RED, plus the control that keeps it honest.

    Stated plainly: no CURRENT driver can produce a gap — `turn_no` is recomputed from
    `latest_turn()` at every process start. This is a standing guard against a future driver, and
    the skipped-turn control is why a cruder run-status proxy was rejected: it goes red on a
    legitimately parked run."""
    led = _fresh(tmp, "gap")
    for turn in (0, 2):
        led.append_turn(TurnCommit(run_id="r1", turn=turn, actor="maren", thought="t", action="a",
                                   tags={"type": "mundane"},
                                   affect={p: 0.5 for p in PRIMARIES}, events=[]))
    gaps = [f for f in integrity.sweep(led.con) if f["kind"] == "TURN-GAP"]
    check("TURN-GAP-found-the-missing-beat", bool(gaps) and "[1]" in gaps[0]["detail"],
          gaps[0]["detail"] if gaps else "nothing found")

    led2 = _fresh(tmp, "skip")
    led2.append_turn(TurnCommit(run_id="r1", turn=0, actor="maren", thought="t", action="a",
                                tags={"type": "mundane"},
                                affect={p: 0.5 for p in PRIMARIES}, events=[]))
    led2.append_turn(TurnCommit(run_id="r1", turn=2, actor="maren", thought="t", action="a",
                                tags={"type": "mundane"},
                                affect={p: 0.5 for p in PRIMARIES}, events=[]))
    with led2.con:
        led2.con.execute("INSERT INTO events (run_id, turn, caused_at, effective_at, type, "
                         "visibility, payload) VALUES ('r1', 1, 1, 1, 'turn-skipped', "
                         "'public', '{}')")
    check("a-DECLARED-skip-is-not-a-gap",
          not [f for f in integrity.sweep(led2.con) if f["kind"] == "TURN-GAP"],
          "a legitimately skipped turn was reported as a gap")


def test_a_STALE_CACHE_is_found_before_resume_hits_it(tmp):
    """RED. This is `resume`'s own comparison, asked for every run instead of one."""
    led = _fresh(tmp, "stale")
    for turn in range(3):
        led.append_turn(TurnCommit(run_id="r1", turn=turn, actor="maren", thought="t", action="a",
                                   tags={"type": "mundane"},
                                   affect={p: 0.5 for p in PRIMARIES}, events=[]))
    led.persist_snapshot("r1", 2, led.fold("r1", 2))
    # a backdated world event written WITHOUT invalidating the cache — the 2026-09-01 brick
    with led.con:
        led.con.execute("INSERT INTO events (run_id, turn, caused_at, effective_at, type, actor, "
                        "visibility, payload) VALUES ('r1', 1, 1, 1, 'move', 'maren', 'public', ?)",
                        (json.dumps({"to": "the ridge"}),))
    findings = integrity.sweep(led.con, fold_check=lambda r: led.divergence(r)[:2])
    check("CACHE-DIVERGED-found-it",
          any(f["kind"] == "CACHE-DIVERGED" for f in findings), str(findings)[:200])
    check("...and-it-is-SILENT-without-the-fold-check",
          not any(f["kind"] == "CACHE-DIVERGED" for f in integrity.sweep(led.con)),
          "the read-only sweep reported a check it could not have run")


def test_a_BROKEN_predicate_still_reports_ZERO_on_a_fresh_database(tmp):
    """THE SYMMETRY PROPERTY, pinned.

    The one thing here that cannot be derived is the CHECK-text predicate — SQLite exposes no pragma
    for CHECK constraints. What makes that safe is that the SAME predicate reads the reference
    schema and the live database, so a bug in it mis-reads both sides identically and cancels. This
    check can therefore UNDER-report and cannot fabricate.

    Proven by deliberately breaking the predicate and asserting a fresh database is still clean."""
    led = _fresh(tmp, "symmetry")
    real = integrity._guard
    try:
        integrity._guard = lambda col, ddl: ("non-empty", None) if "<>" in ddl else None
        findings = integrity.sweep(led.con)
        check("a-BROKEN-predicate-still-reports-zero-on-a-fresh-db", not findings,
              "%d finding(s) fabricated: %s" % (len(findings),
                                                [f["kind"] for f in findings][:5]))
    finally:
        integrity._guard = real
    check("...and-the-real-predicate-was-restored", integrity._guard is real)


def test_the_SWEEP_IS_ACTUALLY_CALLED_by_both_drivers(_tmp):
    """ANTI-ROT. A reporter nobody calls is this repo's named dominant defect class, and it would
    pass every test above.

    Also asserts the call is NOT resume-gated: unlike `bible.drifted`, which has nothing pinned to
    compare on a new run, the dangerous case here IS the new run — a fresh run_id written into a
    database with no walls.

    THIS TEST PROVES THE CALL SITE EXISTS, AND NOTHING MORE. No test invokes either driver's
    `main()` — `tests/test_pipeline_e2e.py:58` says in its own docstring that it MIRRORS
    `scene.py:main` rather than calling it. That is why the driver's expression was moved behind
    `integrity.startup_line`: the test below EXECUTES the same thing the driver evaluates, so the
    surface proven only by parsing is now one function call rather than a composed expression."""
    import ast
    for name in ("direct.py", "scene.py"):
        src = io.open(os.path.join(REPO, "scripts", name), encoding="utf-8").read()
        check("%s-CALLS-integrity.startup_line" % name, "integrity.startup_line(" in src)
        # WALK THE TREE, not the indentation. The first version of this test measured leading
        # spaces, and `if False: print(integrity.sweep(...))` on one line has leading indent 4 —
        # so the guard passed while the call was disabled. Measured 2026-09-02 by doing exactly
        # that. The question is structural, so the check has to be.
        tree = ast.parse(src)
        main = next((n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
        check("%s-has-a-main" % name, main is not None)
        def calls_sweep(node):
            # `ast.dump` renders the call as Attribute(attr='sweep', value=Name(id='integrity')),
            # so searching a dump for the SOURCE spelling "integrity.sweep(" finds nothing — my
            # first structural draft did exactly that and reported 0 both ways, which is the
            # instrument agreeing with itself rather than reading the tree.
            return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and n.func.attr == "startup_line"
                       and isinstance(n.func.value, ast.Name) and n.func.value.id == "integrity"
                       for n in ast.walk(node))

        top = [st for st in (main.body if main else []) if calls_sweep(st)]
        nested = [n for n in ast.walk(main) if main and isinstance(n, (ast.If, ast.Try, ast.While))
                  and calls_sweep(n)]
        check("%s-calls-it-UNCONDITIONALLY" % name, bool(top) and not nested,
              "top-level statements: %d, wrapped in a branch: %d" % (len(top), len(nested)))


def test_NO_WRITABLE_chronicle_connection_lives_outside_db_py(_tmp):
    """The hole `integrity.NOT_COVERED` names, closed rather than documented.

    `db.connect` sets `PRAGMA recursive_triggers=ON` for a measured reason: INSERT OR REPLACE
    performs its delete WITHOUT firing the delete trigger unless it is on, so a connection opened
    anywhere else has hard rule 2's append-only enforcement silently disabled. Three readers —
    `canon_digest.py` and two `.claude` hooks — opened the chronicle with a bare `sqlite3.connect`.
    All three were read-only by BEHAVIOUR, and nothing made them read-only by CONSTRUCTION.

    PROTECTED-OR-EXPLAINED, the same shape as the schema check: every `sqlite3.connect` call outside
    `db.py` must be in-memory, carry `mode=ro`, or appear below with a written reason. A new one
    defaults to FAILING.

    Routing them through `db.connect` would be worse, not better: it MIGRATES on open, so a hook
    resolving a citation would silently move a v12 chronicle to v22."""
    import ast
    EXEMPT = {
        "scripts/doctor.py": "builds the mode=ro URI itself; it IS the read-only opener",
        "src/engine/integrity.py": "opens ':memory:' for the reference schema, never a chronicle",
        "src/engine/db.py": "the one place a chronicle is opened writable, on purpose",
    }
    offenders = []
    for rel_dir in ("src/engine", "scripts", ".claude/hooks"):
        base = os.path.join(REPO, *rel_dir.split("/"))
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if not name.endswith(".py"):
                continue
            rel = "%s/%s" % (rel_dir, name)
            src = io.open(os.path.join(base, name), encoding="utf-8").read()
            for n in ast.walk(ast.parse(src)):
                if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "connect"
                        and isinstance(n.func.value, ast.Name) and n.func.value.id == "sqlite3"):
                    continue
                if rel in EXEMPT:
                    continue
                # in-memory or read-only is fine wherever it appears
                arg = ast.unparse(n.args[0]) if n.args else ""
                whole = ast.unparse(n)
                if ":memory:" in arg or "mode=ro" in whole:
                    continue
                offenders.append("%s:%d  %s" % (rel, n.lineno, whole[:60]))
    check("no-WRITABLE-chronicle-open-outside-db.py", not offenders, "; ".join(offenders))
    check("every-exemption-names-a-file-that-EXISTS",
          all(os.path.exists(os.path.join(REPO, *f.split("/"))) for f in EXEMPT), str(sorted(EXEMPT)))
    check("no-exemption-is-a-BARE-membership", all(EXEMPT.values()))


def test_the_DRIVERS_startup_line_actually_RUNS(tmp):
    """EXECUTED, not parsed. The other half of the test above.

    A TypeError in the driver's one line would have shipped green: the AST check reads source, and
    no test runs `main()`. This calls exactly what the drivers call."""
    led = _fresh(tmp, "startup")
    line = integrity.startup_line(led.con)
    check("startup_line-returns-a-string", isinstance(line, str) and line, repr(line)[:80])
    check("...that-leads-with-the-RED-count", line.startswith("integrity"), line[:60])
    check("...and-is-BRIEF-on-a-clean-db", len(line.splitlines()) <= 4,
          "%d lines — a driver that prints this before every run gets muted" % len(line.splitlines()))
    check("...and-reports-its-COVERAGE-even-when-clean", "per-column guards" in line, line[:200])

    # and on the database that IS wrong, the same call says so rather than staying quiet
    import sqlite3 as _s
    con = _s.connect(_premigration(tmp, "startup_old"))
    with con:
        con.execute("INSERT INTO runs (run_id, created_at, status, config) "
                    "VALUES ('', 'now', 'active', '{}')")
    loud = integrity.startup_line(con, label="aged")
    check("...and-names-the-BREACH-on-an-aged-db", "BREACH" in loud, loud[:200])
    con.close()


def test_the_sweep_RAISES_NOTHING_and_registers_NO_code(_tmp):
    """It reports. Two consequences that are easy to get wrong later.

    `direct.py` and `scene.py` construct their Ledger unguarded at top level, so a raise aborts
    before a single turn — and `keeper.py`, `cut.py`, `critic.py` and `narrate.py` do the same, so a
    raise would block the very tools that repair what was found. And no finding kind may enter
    `codes.py`: that registry's second rule is that a listed code must be RAISED somewhere."""
    from src.engine import codes
    src = io.open(os.path.join(REPO, "src", "engine", "integrity.py"), encoding="utf-8").read()
    import ast
    raises = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Raise)]
    check("integrity.py-raises-NOTHING", not raises,
          "raise at line(s) %s" % [n.lineno for n in raises])
    leaked = sorted(k for k in integrity.TIERS if codes.is_registered(k))
    check("no-finding-kind-is-in-the-CODE-registry", not leaked, str(leaked))


def main():
    tmp = tempfile.mkdtemp(prefix="swe_integrity_")
    print("test_integrity.py — the walls a migrated database lost\n")
    # PER-TEST ISOLATION. Four suites lost their whole tail to one raiser on 2026-09-02.
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        try:
            fn(tmp)
        except Exception as e:                                # noqa: BLE001
            FAILS.append("%s RAISED %s: %s" % (fn.__name__, type(e).__name__, e))
            print("  FAIL  %s RAISED %s: %s" % (fn.__name__, type(e).__name__, str(e)[:110]))
    print("\n%s" % ("test_integrity: OK (a migrated db is missing its walls, and the sweep says so)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
