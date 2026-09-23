"""test_verify_sheet.py — every command scripts/verify.py would run names a file that exists.

`verify.py` is the operator's Part A sheet, run as subprocesses so what is verified is the COMMAND a
human types. It had no guard of its own. The failure it is exposed to is the one this repo has
measured before: a hand-maintained list of commands that rots to a file nobody has any more (the
CLAUDE.md verify block named 21 suites while three of the unlisted eighteen were red). This does not
run the sheet — that would run the whole suite inside the suite — it proves the sheet CAN run.

Stdlib only. Exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import verify as _v                                             # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def main():
    print("test_verify_sheet.py — the verification sheet's commands resolve")
    rows = list(_v.CHECKS) + [_v.SLOW]
    check("the-sheet-has-rows", len(rows) >= 7, len(rows))
    for cid, what, argv, pred in rows:
        target = next((a for a in argv[1:] if a.endswith(".py")), None)
        path = os.path.join(REPO, target) if target else None
        check("%s-names-a-file-that-exists" % cid, bool(target) and os.path.isfile(path), argv)
        check("%s-has-a-predicate" % cid, callable(pred), pred)
    ids = [r[0] for r in rows]
    check("row-ids-are-unique", len(ids) == len(set(ids)), ids)
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
