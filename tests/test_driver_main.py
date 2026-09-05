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

WHAT RUNNING IT ONCE FOUND. `scene.py --book <any book> --stub` with no `--scene` died with
`KeyError: 'ilsa'` before a single turn: `scene.py` falls back to the built-in BP13 fixture whose
cast is ilsa/arden/corin, and indexes `chars[cid]` for people the loaded book has never heard of.
CLAUDE.md already records the content half of that defect — a scene from a private novel serving as
this file's default fixture — and the scrub removed the content while leaving the SHAPE.

SUBPROCESSES, not imports: what is being tested is that the COMMAND a human types produces the
RESULT the docs claim, which is the same reason `tests/test_map.py` shells out to `gen_map.py`.

Script-style, stdlib only, exit 0 = all pass.
"""
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

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
    check("...and-NAMES-the-missing-cast", "'ilsa'" in out, out[-300:])
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
    cfg = {"situation": "Mira considers the gulls.",
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
    with `KeyError: 'ilsa'`, `--fixture` with an unbound `books`. This one did not, and that is
    worth recording as a measurement rather than an assumption."""
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
