#!/usr/bin/env python3
"""test_driver_main.py — the drivers' `main()`, actually executed.

THE GAP THIS CLOSES, and it went unnoticed for the whole life of the repo. `tests/test_pipeline_e2e.py`
says in its own docstring that it MIRRORS `scene.py:main`'s orchestration rather than calling it, and
nothing else invoked either driver's `main()`. Everything about the CLI path — argument handling, the
run-id mint, the startup sweep, the scene-cfg fallback — was covered by reading source and by nothing
that runs.

I SAID TWICE THAT THIS COULD NOT BE TESTED, on the reasoning that `scene.py` takes `--book` and hard
rule 1 forbids a book in this repo. That was wrong, and `tests/test_vault.py:_mk_vault` had been
building an invented book in a tmpdir the whole time. A book assembled at test time from notes this
repo wrote is a FIXTURE; hard rule 1 forbids a real one living in the tree, which is a different
thing. Reusing that helper rather than writing a second one, so the two cannot drift.

WHAT RUNNING IT ONCE FOUND. `scene.py --book <any book> --stub` with no `--scene` died with a
`KeyError` on the default fixture's first cast id before a single turn: `scene.py` falls back to its
built-in fixture scene (now DEFAULT_SCENE, cast ruth/dev/agnes), and indexed `chars[cid]` for people
the loaded book has never heard of. A built-in scene's cast belongs to this repo's fixture and to no
book, so the crash reached every `--book` run that did not pass its own `--scene`.

SUBPROCESSES, not imports: what is being tested is that the COMMAND a human types produces the
RESULT the docs claim, which is the same reason `tests/test_map.py` shells out to `gen_map.py`.

Script-style, stdlib only, exit 0 = all pass.
"""
import io
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))
from src.engine import db as _db   # the schema version, never a literal (2026-09-19)

from test_vault import _mk_vault                              # noqa: E402  one fixture, two suites

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _run(*args, **kw):
    """-> (returncode, combined output). Never raises on a non-zero exit; that is often the point."""
    # stdin=DEVNULL IS LOAD-BEARING. `direct.py` drops into a REPL after its turn and reads stdin;
    # without this it inherits the parent's, which is fine from a terminal and HANGS under a
    # background runner. Measured 2026-09-02 — the first run of this file wedged and had to be
    # killed. A test that passes interactively and hangs in CI is worse than one that fails.
    r = subprocess.run([sys.executable] + list(args), capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=kw.get("timeout", 120), cwd=REPO)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def test_direct_main_RUNS_a_turn_on_a_fixture_book(tmp):
    """The whole CLI path: resolve the book, mint a run, print the sweep, park."""
    book = _mk_vault(tmp)
    rc, out = _run(os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira",
                   "--stub", "--circumstance", "the lamp gutters and the wind turns")
    check("direct.py-main-exits-clean", rc == 0, "rc=%d%s%s" % (rc, chr(10), out[-600:]))
    check("...and-created-a-chronicle", "new chronicle:" in out, out[-400:])
    check("...and-PRINTED-the-integrity-sweep", "integrity:" in out, out[-400:])
    check("...and-the-sweep-is-CLEAN-on-a-database-it-just-made",
          "0 red" in out and "missing 0" in out,
          "a database this engine created must carry every guard it declares")


def test_scene_main_REFUSES_a_cast_the_book_does_not_have(tmp):
    """THE CRASH, now a refusal. `scene.py` fell back to a built-in fixture scene whose cast is not
    in any other book, and indexed `chars[cid]` for them — `KeyError` before the first turn.

    It refuses rather than substituting the book's own cast: the fixture's situation text names its
    people in prose, so pairing it with a different cast would describe people who are not there."""
    book = _mk_vault(tmp)
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--stub", "--budget", "1")
    check("scene.py-refuses-instead-of-CRASHING", rc != 0 and "Traceback" not in out,
          out[-500:])
    check("...and-NAMES-the-missing-cast", "'ruth'" in out, out[-300:])
    check("...and-names-what-the-book-DOES-have", "mira" in out.lower(), out[-300:])
    check("...and-names-the-flag-that-fixes-it", "--scene" in out, out[-300:])


def test_the_FIXTURE_path_runs_and_refuses(_tmp):
    """`--fixture` is a documented path (CLAUDE.md hard rule 1) and nothing ran it.

    It crashed on the first attempt with `NameError: cannot access free variable 'books'` — the
    import sat inside the `--book` branch, making it a local of `main()`, so the `--fixture` branch
    referenced an unbound free variable from a nested function. A pure import-placement bug that
    no scan could see and no test reached."""
    rc, out = _run(os.path.join("scripts", "direct.py"), "--fixture", "no-such-fixture",
                   "--char", "x", "--stub")
    check("a-bogus-fixture-refuses-with-its-CODE", "[BOOK_FIXTURE_NOT_FOUND]" in out, out[-300:])
    check("...and-does-not-NameError", "NameError" not in out, out[-300:])

    rc, out = _run(os.path.join("scripts", "direct.py"), "--fixture", "ashford", "--char", "maren",
                   "--stub", "--circumstance", "the wind turns")
    check("a-REAL-fixture-still-runs-a-turn", rc == 0, "rc=%d%s%s" % (rc, chr(10), out[-400:]))
    # THE REST ROWS RIDE RUN CREATION (bond gate 4, schema v28): every authored axis on the sheet
    # gets an `authored` row before the first beat — maren's three edges carry four axes each
    import sqlite3, json as _json
    db = os.path.join(REPO, "runs", "ashford.db")
    if os.path.exists(db):
        con = sqlite3.connect("file:%s?mode=ro" % db.replace(chr(92), "/"), uri=True)
        run = con.execute("SELECT run_id FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()[0]
        n = con.execute("SELECT COUNT(*) FROM rest_declared WHERE run_id=? AND perceiver='maren' AND source='authored'", (run,)).fetchone()[0]
        n_hold = con.execute("SELECT COUNT(*) FROM attachment_declared WHERE run_id=? AND char_id='maren' AND source='authored'", (run,)).fetchone()[0]
        ver = con.execute("PRAGMA user_version").fetchone()[0]
        con.close()
        sheet = _json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))["current"]["relationships"]
        want = sum(1 for e in sheet.values() for a in ("trust", "affinity", "respect", "debt")
                   if isinstance(e, dict) and isinstance(e.get(a), (int, float)))
        check("the-fixture-run-seeded-one-authored-rest-row-per-axis", n == want, "%d rows vs %d authored axes" % (n, want))
        check("...on-a-current-schema-chronicle", ver == _db.SCHEMA_VERSION, "user_version %s" % ver)
        # GATE 5: the sheet's held things seed one authored attachment row each (bond-arithmetic.md s3)
        block = _json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))["current"].get("attachments") or {}
        check("the-fixture-run-seeded-one-authored-attachment-row-per-held-thing", n_hold == len(block), "%d rows vs %d held" % (n_hold, len(block)))
    else:
        check("the-fixture-run-left-a-db-to-read", False, db)


def test_an_ENGINE_code_REACHES_the_terminal(tmp):
    """The property the whole taxonomy's operator value rests on, and nothing asserted it.

    A code is defined in `codes.py` as "the grep handle an operator and a book author both use" —
    which is only true if the handle survives to the surface the operator is looking at. Six sites
    in `scripts/` do `raise SystemExit(str(e))`; `EngineError.__str__` renders `[CODE] detail`, so
    it does. Changing ONE of them to `str(e.detail)` would strip every engine code from every CLI
    surface, and before this test nothing would have noticed."""
    env = dict(os.environ)
    env["SWE_BOOKS"] = tmp                                    # an empty root: no book resolves
    for script, args in (("direct.py", ["--book", "no-such-book", "--char", "x", "--stub"]),
                         ("scene.py", ["--book", "no-such-book", "--stub"]),
                         ("canon_digest.py", ["--book", "no-such-book"])):
        r = subprocess.run([sys.executable, os.path.join("scripts", script)] + args,
                           capture_output=True, text=True, stdin=subprocess.DEVNULL,
                           timeout=120, cwd=REPO, env=env)
        out = (r.stdout or "") + (r.stderr or "")
        check("%s-surfaces-the-CODE" % script, "[BOOK_NOT_FOUND]" in out, out.strip()[-200:])
        check("%s-does-not-TRACEBACK" % script, "Traceback" not in out, out.strip()[-200:])


def test_no_wrapper_STRIPS_the_code_on_its_way_out(_tmp):
    """The structural half. `SystemExit(str(e))` keeps the code; `SystemExit(e.detail)` throws it
    away, and both read fine to someone skimming the diff.

    Parsed, so a wrapper added tomorrow is checked without anyone remembering this file exists."""
    import ast
    offenders = []
    for name in sorted(os.listdir(os.path.join(REPO, "scripts"))):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(REPO, "scripts", name), encoding="utf-8") as fh:
            src = fh.read()
        for n in ast.walk(ast.parse(src)):
            if not (isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call)
                    and getattr(n.exc.func, "id", "") == "SystemExit"):
                continue
            rendered = ast.unparse(n)
            if ".detail" in rendered or ".args[" in rendered:
                offenders.append("%s:%d  %s" % (name, n.lineno, rendered[:70]))
    check("no-SystemExit-reaches-past-the-code-into-.detail", not offenders, "; ".join(offenders))


def _book_with_a_law(tmp, law):
    """The invented fixture book, plus one authored law in its world note's engine block."""
    import json
    from test_vault import WORLD_ENGINE
    book = _mk_vault(tmp)
    wp = os.path.join(book, "world", "The Rock.md")
    with open(wp, encoding="utf-8") as fh:
        head = fh.read().split("```json")[0]
    engine = dict(WORLD_ENGINE)
    engine["laws"] = [law]
    with open(wp, "w", encoding="utf-8") as fh:
        fh.write(head + "```json" + chr(10) + json.dumps(engine, indent=1) + chr(10) + "```" + chr(10))
    return book


def _scene_cfg(tmp, **over):
    import json
    cfg = {"at": {"day": 1, "time": "09:00"}, "situation": "Mira considers the gulls.",
           "cast": [{"id": "mira", "drive": "reach the mainland tonight"}]}
    cfg.update(over)
    path = os.path.join(tmp, "scene-%d.json" % len(over))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh)
    return path


def test_the_LAW_DENIAL_path_runs_end_to_end(tmp):
    """The delegation the bible/law split existed to unblock, driven through the CLI.

    `tests/test_bible.py` executes `require_allowed` directly; nothing drove it through
    `scene.py`, so the refusal an operator actually meets was covered by reading source. Every
    other never-executed path this session has crashed on its first run — the scene-cfg fallback
    with a `KeyError` on its fixture cast, `--fixture` with an unbound `books`. This one did not,
    and that is worth recording as a measurement rather than an assumption."""
    book = _book_with_a_law(tmp, {"id": "no-flight", "statement": "people do not fly",
                                  "domain": "physical", "modality": "IMPOSSIBLE", "act": "fly"})
    cfg = _scene_cfg(tmp, act="fly")
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", cfg,
                   "--stub", "--budget", "1")
    check("a-denied-act-REFUSES-the-scene", rc != 0 and "Traceback" not in out, out[-400:])
    check("...with-the-CODE", "[BIBLE_ACT_IMPOSSIBLE]" in out, out[-300:])
    check("...naming-the-LAW-that-denied-it", "no-flight" in out, out[-300:])
    check("...and-quoting-the-rule", "people do not fly" in out, out[-300:])


def test_a_PERMITTED_act_still_runs(tmp):
    """The control. A law bearing on a DIFFERENT act must not refuse this one — without this, a
    check that denied everything would pass the test above."""
    book = _book_with_a_law(tmp, {"id": "no-flight", "statement": "people do not fly",
                                  "domain": "physical", "modality": "IMPOSSIBLE", "act": "fly"})
    cfg = _scene_cfg(tmp, act="wait")
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", cfg,
                   "--stub", "--budget", "1")
    check("an-unrelated-act-is-NOT-refused", "[BIBLE_ACT_IMPOSSIBLE]" not in out, out[-400:])
    check("...and-the-scene-actually-started", "new chronicle:" in out, out[-400:])


def test_a_REFUSED_scene_LEAVES_NO_RUN(tmp):
    """A row that should not exist must never be WRITTEN — the log is append-only, so there is no
    second chance to remove it.

    THIS TEST USED TO ASSERT THE OPPOSITE. `main` created the run and `run_scene` checked the law
    after it, so a refused scene left an `active` run with zero turns. I pinned that as a known
    wart and declined to fix it, on the ground that the check needs the pinned bible and so could
    not move. TRUE ON RESUME, FALSE ON A NEW RUN: `bible.build` hands back the fingerprint one line
    BEFORE `create_run`. A blocker asserted for both branches that binds one.

    And the residue was not inert, which is the part that made it worth fixing rather than
    recording: `canon_digest._latest_run` picks the newest row (`canon_digest.py:45`), so the
    digest's default selection landed on the EMPTY run and digested nothing while the real one sat
    a row back — an operator-facing wrong answer, not clutter."""
    import sqlite3
    book = _book_with_a_law(tmp, {"id": "no-flight", "statement": "people do not fly",
                                  "domain": "physical", "modality": "IMPOSSIBLE", "act": "fly"})
    cfg = _scene_cfg(tmp, act="fly")
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", cfg,
                   "--stub", "--budget", "1")
    check("the-scene-was-refused", "[BIBLE_ACT_IMPOSSIBLE]" in out, out[-300:])
    check("...and-no-chronicle-was-announced", "new chronicle:" not in out, out[-300:])
    db = os.path.join(book, "runs", "the-rock-and-the-rose.db")
    runs = 0
    if os.path.isfile(db):
        con = sqlite3.connect("file:%s?mode=ro" % db.replace(chr(92), "/"), uri=True)
        try:
            runs = con.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        finally:
            con.close()
    check("...and-the-refusal-cost-NO-run", runs == 0, "%d run(s) left behind" % runs)


def test_two_scenes_in_one_SECOND_do_not_collide(tmp):
    """`scene.py` minted its run id from epoch SECONDS with no uniqueness suffix, while
    `direct.py:688` has carried a uuid one all along.

    The refusal above is the trigger that makes this reachable: refuse, fix the cfg, rerun — inside
    the same second `create_run` hits the primary key and raises a RAW `sqlite3.IntegrityError`,
    uncoded, because `create_run` has no RUN_EXISTS. Two permitted scenes back to back is the same
    shape without the refusal."""
    book = _book_with_a_law(tmp, {"id": "no-flight", "statement": "people do not fly",
                                  "domain": "physical", "modality": "IMPOSSIBLE", "act": "fly"})
    cfg = _scene_cfg(tmp, act="wait")                 # permitted, so both runs are created
    first = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", cfg,
                 "--stub", "--budget", "1")[1]
    second = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", cfg,
                  "--stub", "--budget", "1")[1]
    check("neither-run-hit-a-CONSTRAINT", "IntegrityError" not in (first + second),
          (first + second)[-300:])
    ids = [ln.split("new chronicle:")[1].strip() for ln in (first + second).splitlines()
           if "new chronicle:" in ln]
    check("...and-the-two-run-ids-DIFFER", len(ids) == 2 and ids[0] != ids[1], str(ids))
    # THE SCENE DRIVER SEEDS TOO (bond gate 4): mira's one authored edge, four axes, per run
    import sqlite3
    db = os.path.join(book, "runs", "the-rock-and-the-rose.db")
    con = sqlite3.connect("file:%s?mode=ro" % db.replace(chr(92), "/"), uri=True)
    rows = con.execute("SELECT run_id, COUNT(*) FROM rest_declared WHERE perceiver='mira' AND target='tomas_keeper' "
                       "AND source='authored' GROUP BY run_id").fetchall()
    con.close()
    check("scene.py-seeded-four-authored-rest-rows-per-run", len(rows) == 2 and all(r[1] == 4 for r in rows), str(rows))


def test_the_e2e_suite_CALLS_the_driver_rather_than_MIRRORING_it(_tmp):
    """This test used to assert the opposite, and the note it carried said to revisit it if that
    changed. It changed on 2026-09-03, so here is the revisit rather than a deletion.

    WHAT IT USED TO PIN: `tests/test_pipeline_e2e.py` reimplemented the orchestration in a
    `_run_scene` whose docstring read "Mirror scene.py:main's run + boundary-record". That was
    called a legitimate design — the two suites covering different things — and the standing note
    asserted the word "Mirror" was still present, which pinned the DEBT rather than any behaviour.

    WHY IT WAS NOT LEGITIMATE: the copy had already drifted four ways. It passed no `cfg`, so the
    schema v14 scene pin was never exercised by the suite named end-to-end; no `voice` and no
    `knowledge`, so the per-scene narration choice defaulted silently; and it never persisted a
    snapshot or parked the run. Nobody chose those four. They are what a copy does when the
    original moves, which is the argument for deriving rather than mirroring, one layer out from
    the seven duplicates CLAUDE.md tabulates.

    Both now call `scripts/scene.py:record_boundary`, and the split of `park` out of it was forced
    by the e2e running several scenes in one process where the driver runs one and exits — a seam
    the copy had hidden by implementing neither half."""
    with open(os.path.join(REPO, "tests", "test_pipeline_e2e.py"), encoding="utf-8") as fh:
        src = fh.read()
    check("the-mirror-is-gone", "Mirror scene.py:main" not in src,
          "the e2e suite is reimplementing the driver again")
    check("it-calls-the-driver-s-own-function", "scene.record_boundary(" in src,
          "e2e no longer calls record_boundary; it may have grown a second copy")
    check("and-exercises-the-cfg-pin-the-copy-missed", "cfg_fingerprint" in src,
          "the assertion that scene rows are PINNED went away with the mirror")


def test_direct_main_EXECUTES_durable_turn_and_folds_vault(tmp):
    """The live execution gap: direct.py executing a durable beat folds the vault and persists."""
    import sqlite3
    book = _mk_vault(tmp)
    cmd = "by:tomas_keeper Tomas brought new wicks for the lamp [durable]\nquit\n"
    r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"),
                        "--book", book, "--char", "Mira", "--stub"],
                       input=cmd, capture_output=True, text=True, cwd=REPO)
    out = (r.stdout or "") + (r.stderr or "")
    check("direct-durable-turn-exits-0", r.returncode == 0, out[-400:])
    check("direct-prints-LEARNED-lived-belief", "LEARNED: Tomas brought new wicks" in out, out[-400:])
    db = os.path.join(book, "runs", "the-rock-and-the-rose.db")
    con = sqlite3.connect(db)
    try:
        rows = con.execute("SELECT run_id, char_id, turn, belief FROM acquisitions").fetchall()
        check("direct-persisted-acquisition-row", len(rows) == 1)
        check("direct-acquisition-actor-is-mira", rows[0][1] == "mira")
        check("direct-acquisition-provenance-lived", '"provenance": "lived"' in rows[0][3])
    finally:
        con.close()


def test_the_FIXTURE_path_survives_a_SUPPLIED_turn(tmp):
    """--fixture + --turn-json, the branch the fixture test above never reached.

    `book_dir` was assigned only inside the `--book` arm while the `--turn-json` call site read it
    unconditionally, so this combination raised `UnboundLocalError` before a turn was attempted.
    The sibling test above passes `--circumstance` and lands on the REPL path instead, which is
    why a documented flag pair went unrun for the life of the repo.
    """
    tj = os.path.join(tmp, "turn.json")
    with io.open(tj, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "action": 'He looked at the split. "The wright at Fallow is two days off."',
            "thought": "two days I do not have",
            "tags": {"type": "mundane", "summary": "found the cart broken", "dimensions": {},
                     "durability": "transient", "confidence": 0.9, "subject": ""}}))
    rc, out = _run(os.path.join("scripts", "direct.py"), "--fixture", "ashford",
                   "--char", "ren-traveler", "--stub", "--circumstance", "a cart returns broken",
                   "--turn-json", tj)
    check("a-supplied-turn-on-a-FIXTURE-does-not-raise", "UnboundLocalError" not in out, out[-400:])
    check("...and-the-turn-COMMITS", rc == 0 and "committed" in out, "rc=%d%s%s" % (rc, chr(10), out[-400:]))


def test_the_world_faults_file_is_a_CHECKLIST_not_a_log(tmp):
    """A hole is reached for on every turn that needs it; the file must list it once.

    `record_faults` appended blind, so one recurring fault was written once per turn and buried
    everything else. A TICKED box counts as listed too — a fault the operator has worked through
    must not come back looking fresh.
    """
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("_d", os.path.join(REPO, "scripts", "direct.py"))
    d = importlib.util.module_from_spec(spec)
    sys.modules["_d"] = d
    spec.loader.exec_module(d)

    d.record_faults(["no place named Fallow", "no person named Cobb"], tmp)
    d.record_faults(["no place named Fallow"], tmp)
    d.record_faults(["no place named Fallow", "no law about carts"], tmp)
    path = os.path.join(tmp, "world-faults.md")
    txt = io.open(path, encoding="utf-8").read()
    check("a-recurring-fault-is-listed-ONCE", txt.count("no place named Fallow") == 1, txt)
    check("...and-the-others-are-not-lost",
          txt.count("no person named Cobb") == 1 and txt.count("no law about carts") == 1, txt)

    # A TICKED box is still listed. Re-raising a fault the operator has closed would make the
    # checklist unusable — it would grow back every run.
    txt = txt.replace("- [ ] no law about carts", "- [x] no law about carts")
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(txt)
    d.record_faults(["no law about carts"], tmp)
    after = io.open(path, encoding="utf-8").read()
    check("a-TICKED-fault-does-not-come-back", "- [ ] no law about carts" not in after, after)


def test_a_fixture_run_writes_no_faults_FILE(tmp):
    """None is the honest book directory for a fixture, and `record_faults` must take it quietly."""
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("_d2", os.path.join(REPO, "scripts", "direct.py"))
    d = importlib.util.module_from_spec(spec)
    sys.modules["_d2"] = d
    spec.loader.exec_module(d)
    d.record_faults(["no place named Fallow"], None)          # must not raise
    check("a-None-book-dir-writes-nothing", not os.path.exists(os.path.join(tmp, "world-faults.md")))


def test_direct_at_writes_scene_clock_and_later_declares_time(tmp):
    """gate driver-clock-parity (2026-09-19): the chair reads the SAME clock a scene does, through
    src/engine/passage.py:open_scene. Before this gate `direct.py` declared no elapsed of its own —
    its own former comment named the asymmetry — so a chair session opened after a scene applied no
    drift, no wound/arc erosion and wrote no clock row however long the gap was said to be.

    Two invocations of the SAME run: the first opens the chronicle with --at/--lasts (nothing to
    derive a gap from yet, so no "minutes since" line); the second resumes it later and gets the
    declared gap — one scene_clock row per opening, one time_declarations row for the SECOND."""
    book = _mk_vault(tmp)
    circumstance = "by:tomas_keeper Tomas brought new wicks for the lamp [durable]"
    r1 = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book,
                        "--char", "Mira", "--stub", "--at", "day 1 06:00", "--lasts", "10m"],
                        input=circumstance + "\nquit\n", capture_output=True, text=True,
                        timeout=120, cwd=REPO)
    out1 = (r1.stdout or "") + (r1.stderr or "")
    check("first-opening-exits-clean", r1.returncode == 0, out1[-500:])
    check("a-FIRST-opening-has-no-prior-gap-to-print",
          "minutes since the last scene ended" not in out1, out1[-400:])
    run_ids = [ln.split("new chronicle:")[1].strip() for ln in out1.splitlines() if "new chronicle:" in ln]
    check("a-run-was-minted", len(run_ids) == 1, out1[-400:])
    if not run_ids:
        return
    run_id = run_ids[0]
    db = os.path.join(book, "runs", "the-rock-and-the-rose.db")
    import sqlite3
    con = sqlite3.connect("file:%s?mode=ro" % db.replace(chr(92), "/"), uri=True)
    rows = con.execute("SELECT turn, at_minutes, lasts_minutes FROM scene_clock WHERE run_id=?", (run_id,)).fetchall()
    con.close()
    check("the-first-opening-wrote-ONE-scene_clock-row", len(rows) == 1, rows)
    check("at-day-1-06-00-lasts-10", bool(rows) and abs(rows[0][1] - 360.0) < 1e-6 and abs(rows[0][2] - 10.0) < 1e-6, rows)

    r2 = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book,
                        "--char", "Mira", "--stub", "--resume", run_id,
                        "--at", "day 1 07:00", "--lasts", "10m"],
                        input="quit\n", capture_output=True, text=True, timeout=120, cwd=REPO)
    out2 = (r2.stdout or "") + (r2.stderr or "")
    check("second-opening-exits-clean", r2.returncode == 0, out2[-500:])
    check("the-declared-GAP-is-printed-with-relaxed-edges",
          "50 minutes since the last scene ended" in out2 and "relaxed" in out2, out2[-500:])
    con = sqlite3.connect("file:%s?mode=ro" % db.replace(chr(92), "/"), uri=True)
    n = con.execute("SELECT COUNT(*) FROM time_declarations WHERE run_id=?", (run_id,)).fetchone()[0]
    clocks = con.execute("SELECT COUNT(*) FROM scene_clock WHERE run_id=?", (run_id,)).fetchone()[0]
    con.close()
    check("the-second-opening-declared-exactly-ONE-time-row", n == 1, n)
    check("...and-wrote-a-SECOND-scene_clock-row", clocks == 2, clocks)


def test_direct_without_at_declares_no_clock(tmp):
    """The chair's DEFAULT is unchanged: no --at, no clock row, and it SAYS so on stdout — the
    asymmetry this gate closes is closed only where the operator opted in."""
    book = _mk_vault(tmp)
    r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book,
                       "--char", "Mira", "--stub"], input="quit\n", capture_output=True,
                       text=True, timeout=120, cwd=REPO)
    out = (r.stdout or "") + (r.stderr or "")
    check("no-at-exits-clean", r.returncode == 0, out[-400:])
    check("says-it-is-running-on-minutes-per-turn-only",
          "chair: no --at given" in out and "--minutes-per-turn" in out, out[-400:])
    run_ids = [ln.split("new chronicle:")[1].strip() for ln in out.splitlines() if "new chronicle:" in ln]
    check("a-run-was-minted", len(run_ids) == 1, out[-400:])
    if not run_ids:
        return
    import sqlite3
    db = os.path.join(book, "runs", "the-rock-and-the-rose.db")
    con = sqlite3.connect("file:%s?mode=ro" % db.replace(chr(92), "/"), uri=True)
    n = con.execute("SELECT COUNT(*) FROM scene_clock WHERE run_id=?", (run_ids[0],)).fetchone()[0]
    con.close()
    check("no-at-writes-NO-scene_clock-row", n == 0, n)


def test_direct_keeper_under_stub_asks_nothing(tmp):
    """--keeper on the chair (new flag, same help text as scene.py's — CALLERS): under --stub it
    rules nothing and prints that, exactly as scene.py's own --keeper does at its canon-gate site.
    Gated on a turn actually having been committed THIS invocation (turn_no > start_turn), the same
    way scene.py gates its own call on `next_turn > start_turn`."""
    book = _mk_vault(tmp)
    circumstance = "by:tomas_keeper Tomas brought new wicks for the lamp [durable]"
    r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book,
                       "--char", "Mira", "--stub", "--keeper"],
                       input=circumstance + "\nquit\n", capture_output=True, text=True,
                       timeout=120, cwd=REPO)
    out = (r.stdout or "") + (r.stderr or "")
    check("keeper-run-exits-clean", r.returncode == 0, out[-500:])
    check("the-keeper-ASKS-NOTHING-under-stub",
          "KEEPER (stub): noticing pass skipped" in out, out[-500:])


def test_keeper_runs_truth_table(_tmp):
    """`_keeper_runs` pins the DEFAULT (owner decision D1, gate lore-licence-visible, 2026-09-19)
    without a real model: this whole gate is --stub only, and a live (non-stub) invocation needs a
    key this suite must not use, so the default-on behaviour can only be checked by loading the
    function itself — the same reason `test_the_world_faults_file_is_a_CHECKLIST_not_a_log` above
    loads `direct.py` by file location rather than running it. Both drivers carry their own copy
    (parity, the way their `--keeper` help text has always been maintained in both places rather
    than one) and must agree on every row."""
    print("\n[T] _keeper_runs — the default, pinned without a live model")
    import importlib.util
    mods = {}
    for name in ("scene", "direct"):
        spec = importlib.util.spec_from_file_location(
            "_kr_%s" % name, os.path.join(REPO, "scripts", name + ".py"))
        m = importlib.util.module_from_spec(spec)
        sys.modules["_kr_%s" % name] = m
        spec.loader.exec_module(m)
        mods[name] = m
    # (stub, keeper, keeper_off) -> expected. The first row is the flip this gate makes; the rest
    # pin that nothing else moved: --keeper stays a no-op on a live run, bare --stub is silent as
    # before, an explicit --keeper still forces the gate under --stub (the CLI-level test above
    # pins that one end to end), and --no-keeper always wins when both are given.
    table = [((False, False, False), True),
            ((False, True,  False), True),
            ((False, False, True),  False),
            ((False, True,  True),  False),
            ((True,  False, False), False),
            ((True,  True,  False), True),
            ((True,  False, True),  False),
            ((True,  True,  True),  False)]
    for name, m in mods.items():
        for (stub, keeper, keeper_off), want in table:
            got = m._keeper_runs(stub, keeper, keeper_off)
            check("%s._keeper_runs(stub=%s, keeper=%s, keeper_off=%s)" % (name, stub, keeper, keeper_off),
                  got == want, "got %r, want %r" % (got, want))


def test_scene_stub_with_no_quotes_reports_every_saying_noticed(tmp):
    """The 'lore:' line (gate lore-licence-visible), on the existing plain fixture invocation.

    MEASURED, not assumed: `_scene_cfg`'s situation text ("Mira considers the gulls.") carries no
    dialogue and the stub actor's own template ("(stub) the character meets the moment — %s")
    never emits a quote either, so `claims.spoken` finds nothing and the debt is genuinely zero —
    the "every saying has been noticed" form, not the counted one. See the sibling test below for
    the count > 0 form, driven the same way with one quote added to the situation."""
    print("\n[L1] lore: EVERY SAYING HAS BEEN NOTICED — the plain fixture has none to notice")
    book = _mk_vault(tmp)
    cfg = _scene_cfg(tmp)
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", cfg,
                   "--stub", "--budget", "1")
    check("scene-exits-clean", rc == 0, out[-500:])
    check("no-quoted-saying-reports-as-noticed", "lore: every saying has been noticed" in out, out[-400:])


def test_scene_stub_with_a_quoted_saying_reports_the_debt(tmp):
    """The count > 0 branch, driven for real rather than hand-computed: a director-authored
    situation with one quoted span becomes the stub actor's own action text verbatim (the stub
    template interpolates the event text), so `claims.spoken` finds exactly one saying nobody has
    extracted.

    Three invocations of the same one-quote scene, differing only in the keeper flags, to pin all
    three 'lore:' forms the gate specifies against a real driver run:
      * neither flag (bare --stub): the keeper does not run -> "await the keeper", naming the fix
      * --keeper (still forces the gate under --stub, unchanged from before this gate — the sibling
        chair test above pins the same thing): the stub keeper asks nothing and the saying is
        STILL unextracted afterwards
      * --keeper together with --no-keeper: the opt-out wins, same as neither flag
    """
    print("\n[L2] lore: N SAYING(S) — a quoted span in the situation becomes a debt")
    book = _mk_vault(tmp)
    said = 'Mira turns and says "the gulls are wrong tonight."'

    def _cfg(name, **over):
        cfg = {"at": {"day": 1, "time": "09:00"}, "situation": said,
              "cast": [{"id": "mira", "drive": "reach the mainland tonight"}]}
        cfg.update(over)
        path = os.path.join(tmp, name + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh)
        return path

    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", _cfg("bare"),
                   "--stub", "--budget", "1")
    check("bare-stub-exits-clean", rc == 0, out[-500:])
    check("bare-stub-names-the-count-and-turn",
          "lore: 1 saying(s) since turn 0 await the keeper" in out, out[-400:])
    check("...and-the-fix-it-names",
          "--no-keeper" in out and "scripts/keeper.py --prompt-only" in out, out[-400:])
    check("the-keeper-did-NOT-run", "KEEPER" not in out, out[-400:])

    rc2, out2 = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene",
                     _cfg("forced", at={"day": 1, "time": "09:01"}), "--stub", "--budget", "1", "--keeper")
    check("stub-plus-keeper-exits-clean", rc2 == 0, out2[-500:])
    check("--keeper-STILL-forces-the-gate-under---stub",
          "KEEPER (stub): noticing pass skipped" in out2, out2[-500:])
    check("...and-the-debt-is-reported-as-LEFT-by-a-stub-keeper",
          "lore: 1 saying(s) still unextracted" in out2 and "the keeper asked nothing under --stub" in out2,
          out2[-400:])

    rc3, out3 = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene",
                     _cfg("overridden", at={"day": 1, "time": "09:02"}), "--stub", "--budget", "1",
                     "--keeper", "--no-keeper")
    check("no-keeper-WINS-over-keeper-even-under-stub", rc3 == 0 and "KEEPER" not in out3, out3[-500:])
    check("...back-to-await-the-keeper",
          "lore: 1 saying(s) since turn 0 await the keeper" in out3, out3[-400:])


def test_direct_stub_with_a_quoted_circumstance_reports_the_debt(tmp):
    """direct.py's OWN `_report_lore`/`_keeper_runs` — a separate copy from scene.py's (parity, not
    a shared import), so a driver run pins it independently. The typed circumstance rides into the
    stub's action the same way scene.py's situation text does (`llm_turn`'s stub branch, shared by
    both drivers): a quote in what the operator types becomes a quote in what the stub 'said'."""
    print("\n[L3] lore: THE CHAIR REPORTS THE SAME DEBT, ITS OWN WAY")
    book = _mk_vault(tmp)
    circumstance = 'Tomas turns and says "the wicks are new, keep them dry"'
    r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book,
                       "--char", "Mira", "--stub", "--no-keeper"],
                       input=circumstance + "\nquit\n", capture_output=True, text=True,
                       timeout=120, cwd=REPO)
    out = (r.stdout or "") + (r.stderr or "")
    check("chair-exits-clean", r.returncode == 0, out[-500:])
    check("...not-with-an-UNRECOGNIZED-flag", "unrecognized arguments" not in out, out[-300:])
    check("the-chair-names-the-same-debt-line",
          "lore: 1 saying(s) since turn 0 await the keeper" in out, out[-400:])
    check("--no-keeper-kept-the-gate-off", "KEEPER" not in out, out[-400:])


def main():
    print("test_driver_main.py — the CLI path, executed rather than mirrored\n")
    tmp = tempfile.mkdtemp(prefix="swe_driver_")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        try:
            fn(tempfile.mkdtemp(dir=tmp))
        except Exception as e:                                    # noqa: BLE001
            FAILS.append("%s RAISED %s: %s" % (fn.__name__, type(e).__name__, e))
            print("  FAIL  %s RAISED %s: %s" % (fn.__name__, type(e).__name__, str(e)[:110]))
    print("\n%s" % ("test_driver_main: OK (both drivers' main() ran, and one of them used to crash)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
