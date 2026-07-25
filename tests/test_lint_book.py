#!/usr/bin/env python3
"""test_lint_book.py — pre-run book validation (gate swe-book-linter).

The maren/ashford fixture lints error-free; a deliberately-broken character yields the specific
run-breaking errors (missing temperament primary, affect out of range, missing condition) and the
content-guide warning (a relationship key that is not a world-people id). Script-style, exit 0 = pass.
"""
import copy
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import lint_book                                              # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def main():
    print("test_lint_book.py — pre-run book validation\n")
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    maren = json.load(open(os.path.join(REPO, "characters/maren-healer.json"), encoding="utf-8"))

    # 1. the real fixture lints error-free (warnings allowed)
    clean = lint_book.lint(world, {"maren": maren})
    check("fixture-no-errors", clean["errors"] == [], str(clean["errors"]))

    # 2. a broken character yields the specific errors
    bad = copy.deepcopy(maren)
    del bad["baseline"]["temperament"]["CARE"]                # drop a primary -> error
    bad["current"]["affect"]["FEAR"] = 1.7                    # out of [0,1] -> error
    bad["current"]["condition"] = "not a dict"                # wrong type -> error
    bad["current"]["relationships"]["nobody_here"] = {"trust": 0.2}   # not a people id -> warning
    rep = lint_book.lint(world, {"maren": bad})
    errs = " | ".join(rep["errors"])
    warns = " | ".join(rep["warnings"])
    check("error-temperament-primary", "temperament missing primaries" in errs and "CARE" in errs, errs)
    check("error-affect-range", "current.affect[FEAR]" in errs, errs)
    check("error-condition-type", "current.condition missing or not a dict" in errs, errs)
    check("warn-bad-relationship-key", "nobody_here" in warns and "never surface" in warns, warns)

    # 3. a missing section is a hard error
    rep2 = lint_book.lint(world, {"x": {"fixed": {"name": "X"}, "baseline": {}}})  # no current
    check("error-missing-section", any("missing/invalid section 'current'" in e for e in rep2["errors"]), str(rep2["errors"]))

    if FAILS:
        print("\ntest_lint_book: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_lint_book: OK (fixture clean; broken char caught pre-run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
