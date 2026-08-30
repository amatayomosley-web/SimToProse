"""verify.py — run Part A of docs/verification-sheet.md and print a pass/fail sheet.

WHY A SCRIPT AND NOT JUST THE DOC. The sheet's Part A is seven commands with seven pass conditions.
Left as prose, it is a checklist — and this repo's measured record with checklists is poor: the
verify block in CLAUDE.md named 21 suites by hand while `tests/` held 39, and three of the eighteen
that were never run were RED while the block reported green. `tests/run_all.py` exists because of
that. This is the same move one level up.

It runs the real commands as subprocesses rather than importing and calling — the same reason
`test_map.py` shells out to `gen_map.py --check`: what is being verified is that the COMMAND a human
would type produces the RESULT the sheet claims, not that a function returns something.

`--slow` includes the end-to-end pipeline test (two stub scenes, ~1 minute); without it that row is
reported SKIPPED rather than silently omitted, because a sheet that quietly drops its most
end-to-end row is the checklist problem again.

Part B (mechanism) and Part C (human) are NOT run here. B needs a book on disk; C needs a person.
The sheet says so and this prints the reminder, so a green run is never mistaken for a whole system.
"""
import argparse
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

# (id, what it proves, argv, predicate over (returncode, stdout+stderr))
CHECKS = [
    ("A1", "every suite green",
     [PY, "tests/run_all.py"],
     lambda rc, out: rc == 0 and "0 failed" in out),
    ("A2", "the detectors detect",
     [PY, "tests/coherence_probe.py", "--stub"],
     lambda rc, out: "VERDICT: PASS" in out),
    ("A3", "AND CAN FAIL — the control",
     [PY, "tests/coherence_probe.py", "--corrupt"],
     lambda rc, out: "VERDICT: FAIL" in out),
    ("A4", "the routing table matches the tree",
     [PY, "scripts/gen_map.py", "--check"],
     lambda rc, out: rc == 0 and "matches the tree" in out),
    ("A5", "no private content anywhere tracked",
     [PY, "tests/test_no_private_content.py"],
     lambda rc, out: rc == 0 and "VERDICT: PASS" in out),
    ("A6", "no path outside this repo",
     [PY, "tests/test_self_contained.py"],
     lambda rc, out: rc == 0 and "VERDICT: PASS" in out),
]
SLOW = ("A7", "THE WHOLE PIPELINE end to end",
        [PY, "tests/test_pipeline_e2e.py"],
        lambda rc, out: rc == 0 and "test_pipeline_e2e: OK" in out)


def _run(argv):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
                       errors="replace", env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slow", action="store_true",
                    help="include A7, the end-to-end pipeline test (~1 min, two stub scenes)")
    args = ap.parse_args()

    print("verification-sheet Part A — the machinery, not the book")
    print("=" * 70)
    checks = list(CHECKS) + ([SLOW] if args.slow else [])
    failed = []
    for cid, what, argv, ok in checks:
        rc, out = _run(argv)
        good = False
        try:
            good = bool(ok(rc, out))
        except Exception:
            good = False
        print("  %s  %-4s %s" % ("PASS" if good else "FAIL", cid, what))
        if not good:
            failed.append(cid)
            tail = [l for l in out.strip().split("\n") if l.strip()][-3:]
            for l in tail:
                print("            | %s" % l[:100])
    if not args.slow:
        print("  SKIP  A7   THE WHOLE PIPELINE end to end   (re-run with --slow)")

    print("=" * 70)
    print("Part A: %d of %d passed" % (len(checks) - len(failed), len(checks)))
    print()
    print("NOT covered by a green run above — docs/verification-sheet.md Parts B, C, D:")
    print("  · Part B (mechanism: props, linter, digest, append-only, act seam) needs a book on disk")
    print("  · Part C (does it read as a story, can you tell two characters apart) needs a person")
    print("  · Part D: NO BOOK HAS EVER BEEN PRODUCED. A7 is two stub scenes on a fixture.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
