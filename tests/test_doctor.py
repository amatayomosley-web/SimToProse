#!/usr/bin/env python3
"""test_doctor.py — the lore debt, on the doctor's report (gate lore-licence-visible, 2026-09-19).

NO EARLIER SUITE CALLED `scripts/doctor.py`. `tests/test_integrity.py` names it once, in a comment
about how it builds its own read-only connection, and never imports or runs it — `examine()` and
`main()` had no discoverable coverage before this file. New, not an extension: grepped first.

WHAT THIS CHECKS, and only this: that `examine()`'s new `lore` return (`claims.unextracted` per
run, via `_lore_debt`) reaches the OPERATOR'S TERMINAL as the amber line the gate asks for — "N
utterance(s) unextracted (turns X-Y) — the fence cannot see them" — on a database that has the debt,
and is silent on one that does not. `tests/test_lore.py` already pins `claims.unextracted` itself
(count/first_turn/last_turn/speakers); this file does not re-derive that, only that `doctor.py`
actually prints what it returns, run as the command an operator types.

Script-style like tests/test_floor.py: check(), main(), exit code. Stdlib only.
"""
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import claims                                      # noqa: E402
from src.engine.ledger import Ledger                                # noqa: E402
from src.engine.records import PATHS, TurnCommit                    # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _doctor(*args, timeout=60):
    """-> (returncode, combined output) of `python scripts/doctor.py <args>`. Never raises."""
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "doctor.py")] + list(args),
                       capture_output=True, text=True, timeout=timeout, cwd=REPO)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _a_bare_saying_db(tmp, name):
    """A fresh chronicle carrying ONE utterance committed the ORDINARY way — through
    `TurnCommit.utterances=claims.spoken(action)`, exactly as `scripts/scene.py` and
    `scripts/direct.py` build it — so it lands with NO `claim_extracts` row, same fixture shape as
    `tests/test_lore.py:test_unextracted`'s "bare" case. -> path, closed."""
    path = os.path.join(tmp, name + ".db")
    led = Ledger(path)
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    led.register_character("r1", "maren", {"name": "Maren"}, {"temperament": "authored"})
    said = '"The mill burned the winter my mother died."'
    led.append_turn(TurnCommit(run_id="r1", turn=0, actor="maren", thought="t0", action=said,
                               tags={"type": "mundane"}, affect={p: 0.3 for p in PATHS}, events=[],
                               utterances=claims.spoken(said)))
    led.con.close()
    return path


def _a_clean_db(tmp, name):
    """A fresh chronicle with a run and no utterances at all — the honest majority case (most turns
    say nothing quotable) — closed before the doctor reads it read-only."""
    path = os.path.join(tmp, name + ".db")
    led = Ledger(path)
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    led.register_character("r1", "maren", {"name": "Maren"}, {"temperament": "authored"})
    led.con.close()
    return path


def test_a_db_with_the_debt_prints_the_amber_line(tmp):
    print("\n[1] THE DEBT IS AMBER — a saying the fence cannot see is reported, not silent")
    path = _a_bare_saying_db(tmp, "dirty")
    rc, out = _doctor(path)
    check("doctor-exits-clean-amber-never-fails-it", rc == 0, out[-500:])
    check("the-LORE-UNEXTRACTED-kind-line-is-printed", "LORE-UNEXTRACTED" in out, out)
    # Split on either side of the em-dash rather than asserting one literal span across it — this
    # file's own subprocess round-trips it correctly (checked directly), but no OTHER check in
    # tests/test_driver_main.py spans one across a subprocess capture either, and there is no
    # reason for this file to be the first to need it.
    check("the-exact-debt-sentence-is-printed",
          "1 utterance(s) unextracted (turns 0-0)" in out and "the fence cannot see them" in out, out)
    check("the-run-that-carries-it-is-named", "r1" in out, out)


def test_a_clean_db_prints_no_lore_line(tmp):
    print("\n[2] THE CONTROL — nothing to notice, nothing printed")
    path = _a_clean_db(tmp, "clean")
    rc, out = _doctor(path)
    check("doctor-exits-clean", rc == 0, out[-500:])
    check("no-LORE-UNEXTRACTED-line-on-a-run-with-no-utterances",
          "LORE-UNEXTRACTED" not in out, out)
    check("...and-no-bare-sentence-either", "unextracted" not in out, out)


def test_brief_mode_suppresses_the_amber_detail(tmp):
    """`--brief` is documented as "red tier and the coverage line only" (doctor.py's own --brief
    help, and integrity.render's brief=True contract) — the lore line follows the SAME amber-tier
    convention every other finding already does: suppressed under --brief, present in full."""
    print("\n[3] --brief HIDES IT, LIKE EVERY OTHER AMBER DETAIL")
    path = _a_bare_saying_db(tmp, "dirty2")
    rc, out = _doctor(path, "--brief")
    check("brief-mode-exits-clean", rc == 0, out[-500:])
    check("brief-mode-does-not-print-the-lore-line", "LORE-UNEXTRACTED" not in out, out)
    rc2, out2 = _doctor(path)
    check("...but-the-FULL-report-on-the-SAME-db-does", "LORE-UNEXTRACTED" in out2, out2)


def test_examine_returns_the_lore_debt_directly(_tmp):
    """The unit-level half, beside the CLI-level checks above: `examine()` returns a 4-tuple whose
    third element is exactly what `claims.unextracted` says, per run — pinned directly so a
    future refactor of the print formatting cannot quietly stop finding the debt in the first place.

    THE FOURTH ELEMENT ARRIVED 2026-09-19 (gate correction-events): the per-run `correction` count,
    measurement.md detector #6. This unpacking is the only change that gate made to this file."""
    print("\n[4] examine() -> (findings, summary, lore, corrections) — THE DATA BEHIND THE LINES")
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import doctor
    tmp = tempfile.mkdtemp(prefix="swe_doctor_unit_")
    try:
        dirty = _a_bare_saying_db(tmp, "unit-dirty")
        findings, summary, lore, corrections = doctor.examine(dirty)
        check("examine-returns-a-4-tuple-now", isinstance(lore, list) and isinstance(corrections, list),
              (type(lore), type(corrections)))
        check("one-run-carries-the-debt", len(lore) == 1 and lore[0]["run_id"] == "r1", lore)
        check("...with-the-same-shape-claims.unextracted-gives",
              lore[0]["count"] == 1 and lore[0]["first_turn"] == 0 and lore[0]["last_turn"] == 0,
              lore)
        check("a-run-with-no-corrections-reports-none", corrections == [], corrections)
        clean = _a_clean_db(tmp, "unit-clean")
        _f2, _s2, lore2, _c2 = doctor.examine(clean)
        check("a-clean-run-carries-no-lore-finding", lore2 == [], lore2)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_a_db_with_a_correction_names_the_count(_tmp):
    """DETECTOR #6 ON THE REPORT (gate correction-events). A chronicle carrying one `correction`
    event must say so — `examine()`'s fourth element AND the printed report, because a count that
    only exists in a return value is not a report. The control is the clean db above: no line."""
    print("\n[5] N correction(s) — THE COUNT IS NAMED, AND ONLY WHEN THERE IS ONE")
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import doctor
    from src.engine import world_events
    from src.engine.records import Event
    tmp = tempfile.mkdtemp(prefix="swe_doctor_corr_")
    try:
        path = os.path.join(tmp, "corrected.db")
        led = Ledger(path)
        led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
        led.register_character("r1", "maren", {"name": "Maren"}, {"temperament": "authored"})
        world_events.append(led, "r1", 0, [Event(type="move", actor="maren", payload={"to": "ward"})])
        world_events.append(led, "r1", 1, [Event(
            type="correction", actor="maren", visibility="private-to-actor",
            payload={"supersedes": [1], "turn": 0, "issue": "she never left the cottage",
                     "source": "critic"})])
        led.con.close()
        _f, _s, _l, corrections = doctor.examine(path)
        check("examine-names-the-count", corrections == [{"run_id": "r1", "count": 1}], corrections)
        rc, out = _doctor(path)
        check("the-report-prints-it", "1 correction(s)" in out, out)
        check("...and-says-what-it-means", "superseded" in out, out)
        check("corrections-are-not-a-failure", rc == 0, out[-500:])
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("test_doctor.py — the doctor reports the lore licence's debt\n")
    tmp = tempfile.mkdtemp(prefix="swe_doctor_")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn(tempfile.mkdtemp(dir=tmp))
    print("\n%s" % ("test_doctor: OK (a saying nobody noticed is now on the report)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
