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

    # 4. THE WOUND'S OWN FIELDS. A missing `intensity` was caught nowhere, and
    # `identity_view._said` supplies 0.5 for an absent weight — so a dead daughter reached the
    # actor as "it catches you sometimes", banded from a number nobody wrote. An invented value
    # shown to the character as true is worse than an absent feature, and this is where it stops.
    def _wounded(*entries):
        c = copy.deepcopy(maren)
        c["baseline"]["drives"]["fears_wounds"] = list(entries)
        return " | ".join(lint_book.lint(world, {"maren": c})["errors"])

    e_missing = _wounded({"id": "w0", "wound": "the fever she could not break", "trigger": ["fever"]})
    check("error-wound-without-intensity",
          "has no `intensity`" in e_missing and "fears_wounds[0]" in e_missing, e_missing)
    check("error-names-the-bands", "it takes you over" in e_missing, e_missing)

    e_nolabel = _wounded({"id": "w0", "intensity": 0.7, "trigger": ["fever"]})
    check("error-wound-without-text",
          "has no `wound` or `fear` text" in e_nolabel, e_nolabel)

    # BOTH keys is an error and normalising them is NOT the fix: `_said` carries every key except
    # `intensity` straight to the prompt, so `wound:` and `fear:` are words the actor reads about
    # themselves. An author calling one a fear and the other a wound is saying something.
    e_both = _wounded({"id": "w0", "wound": "the fever", "fear": "being too late", "intensity": 0.7})
    check("error-wound-with-both-labels", "carries BOTH" in e_both, e_both)

    # `id` is required as of the wound-delta store: it is the key the catalog row names and the
    # key the wound_deltas log records against, so a wound without one can never move.
    check("fear-alone-is-legal",
          not _wounded({"id": "w1", "fear": "being too late", "intensity": 0.5}))
    check("wound-alone-is-legal",
          not _wounded({"id": "w2", "wound": "the fever", "intensity": 0.85}))
    e_noid = _wounded({"wound": "the fever", "intensity": 0.85})
    check("error-wound-without-id", "has no `id`" in e_noid, e_noid)

    # 5. THE PAIRING CHECK STAYS `any`. A build plan for this work proposed tightening it to
    # `every`; checked against the fixtures first, `every` FLAGS A CORRECT CHARACTER. Ren's third
    # trigger is evocative prose for the actor with the operative words in his catalog rows, which
    # his own `_note` documents on purpose. Pinned so the tightening is not re-attempted.
    ren = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    rep3 = lint_book.lint(world, {"ren": ren})
    check("ren-lints-error-free", rep3["errors"] == [], str(rep3["errors"]))
    check("ren-not-flagged-for-prose-triggers",
          not any("NO baseline.catalog row" in w for w in rep3["warnings"]),
          " | ".join(rep3["warnings"]))
    _trigs = ren["baseline"]["drives"]["fears_wounds"][0]["trigger"]
    _words = " ".join(str(w).lower() for r in ren["baseline"]["catalog"]["rows"]
                      for w in ((r.get("when") or {}).get("percept") or []))
    check("the-fixture-actually-has-an-unmatched-trigger",
          not all(t.split()[0].lower() in _words for t in _trigs if t.split()),
          "if every trigger matches, this test proves nothing about `any` vs `every`")

    if FAILS:
        print("\ntest_lint_book: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_lint_book: OK (fixture clean; broken char caught pre-run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
