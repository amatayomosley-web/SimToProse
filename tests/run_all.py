#!/usr/bin/env python3
"""run_all.py — every suite in tests/, DISCOVERED not listed.

Written 2026-08-23 after the fourth stale hand-list of one session, and the worst of them: the
verify procedure itself. CLAUDE.md's verify block names 21 suites by hand; `tests/` holds 39 files.
Three of the eighteen never run were RED, each broken by that same session's own changes —
`test_arc` still asserted the edge-writing that moved to bonds.py, `test_faithful_turn`'s stub
predated the `acts` kwarg, `test_vault`'s affect fixture predated DISGUST. Every one of them was
reported as "21 suites green" while failing.

The other three stale lists that session found and fixed — coherence_probe's PRIMARIES,
basis_probe's ROLE_PAIRS, consolidation's _KNOWN_DIMS — were all the same shape: a hand-maintained
copy that rotted when its source changed. A hand-listed verify block is that shape applied to the
thing that is supposed to CATCH the shape.

    python tests/run_all.py            # every suite
    python tests/run_all.py --slow     # include the ones that make model calls

Probes are excluded by default: coherence_probe has its own --stub/--corrupt contract (the corrupt
arm MUST fail), and basis_probe makes local model calls.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# Not plain pass/fail suites — each has its own contract, run separately by the verify block.
_PROBES = {"coherence_probe.py", "basis_probe.py"}
# Make live model calls; opt in with --slow.
# EMPTY since 2026-09-04, and that is a measurement. test_pipeline_e2e.py sat here on the
# assumption that an end-to-end suite must be slow; timed, it runs in 601ms, exits 0, and
# greps 0 hits for openrouter/api_key/requests.post — it is stub-only. Excluding it meant
# every documented verify run skipped the ONE suite that exercises the whole pipeline, and
# the summary line said so ("1 slow skipped") in a way that read as deliberate. The sibling
# template inherited the same exclusion by copy. Put a suite here only after TIMING it.
_SLOW = set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slow", action="store_true", help="include suites that make model calls")
    args = ap.parse_args()

    names = sorted(f for f in os.listdir(HERE)
                   if f.startswith("test_") and f.endswith(".py") and f not in _PROBES)
    skipped = [] if args.slow else [f for f in names if f in _SLOW]
    names = [f for f in names if args.slow or f not in _SLOW]

    failed = []
    for f in names:
        r = subprocess.run([sys.executable, os.path.join(HERE, f)],
                           capture_output=True, cwd=REPO,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        ok = r.returncode == 0
        print("  %s  %s" % ("PASS" if ok else "FAIL", f[5:-3]))
        if not ok:
            failed.append((f, (r.stdout + r.stderr).decode("utf-8", "replace").strip()))

    print("\n%d suites: %d passed, %d failed%s"
          % (len(names), len(names) - len(failed), len(failed),
             (" (%d slow skipped: %s)" % (len(skipped), ", ".join(skipped))) if skipped else ""))
    for f, out in failed:
        print("\n--- %s ---\n%s" % (f, out[-700:]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
