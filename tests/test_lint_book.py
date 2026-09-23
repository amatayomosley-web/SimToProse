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
    del bad["baseline"]["temperament"]["GOODWILL"]                # absent rest = quiet, seeded: NOT an error (2026-09-10)
    bad["fixed"]["genotype"]["DEFLATION"]["rest"] = "raised"      # rest inside the genotype -> error (moved to design)
    bad["baseline"]["temperament"]["DISTASTE"]["rest"] = "raised" # above DISTASTE's cap of 2 -> warning with the rung
    bad["baseline"]["temperament"]["STIRRING"]["mean"] = 0.62     # a mean a whole rung off its rest word -> warning
    bad["current"]["affect"]["WARINESS"] = 1.7                    # out of [0,1] -> error
    bad["current"]["condition"] = "not a dict"                # wrong type -> error
    bad["current"]["relationships"]["nobody_here"] = {"trust": 0.2}   # not a people id -> warning
    rep = lint_book.lint(world, {"maren": bad})
    errs = " | ".join(rep["errors"])
    warns = " | ".join(rep["warnings"])
    check("no-error-for-an-absent-rest-row", "temperament missing" not in errs and "GOODWILL" not in errs, errs)
    check("error-rest-inside-the-genotype", "genotype.DEFLATION.rest" in errs and "baseline.temperament.DEFLATION.rest" in errs, errs)
    check("warn-rest-above-the-cap-names-the-rung", "baseline.temperament.DISTASTE.rest sits at rung 3" in warns, warns)
    check("warn-mean-a-rung-off-its-rest-word", "baseline.temperament.STIRRING.mean 0.62" in warns and "rest says 'low'" in warns, warns)
    check("error-affect-range", "current.affect[WARINESS]" in errs, errs)
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

    # WOUNDS LEFT THE SHEET (gate three, 2026-09-11): the prose block is refused by name
    e_missing = _wounded({"id": "w0", "wound": "the fever she could not break", "trigger": ["fever"]})
    check("error-fears-wounds-is-refused",
          "fears_wounds is not read since 2026-09-11" in e_missing and "baseline.wounds" in e_missing, e_missing)
    bad = copy.deepcopy(maren)
    bad["baseline"]["wounds"] = [{"id": "zebra@WARINESS", "concept": "zebra", "path": "WARINESS", "intensity": 0.5, "source": "profile:t"}]
    e_concept = " | ".join(lint_book.lint(world, {"maren": bad})["errors"])
    check("error-wound-with-an-unknown-concept", "WOUND_CONCEPT_UNKNOWN" in e_concept, e_concept)
    bad["baseline"]["wounds"] = [{"id": "fire@WARINESS", "concept": "fire", "path": "WARINESS", "intensity": 0.5, "source": "hand-written"}]
    e_src = " | ".join(lint_book.lint(world, {"maren": bad})["errors"])
    check("error-wound-not-minted", "minted, never hand-written" in e_src, e_src)
    # THE OLD CHECKS ON THE PROSE BLOCK (labels, id, the pairing warning) LEFT WITH IT 2026-09-11:
    # a wound is minted, keyed, and matched by concept identity, so there is no label to get
    # wrong, no id to forget and no catalog twin to pair. Ren still lints error-free with his
    # scar as engine state, and a row that names a wound the sheet does not carry is an error.
    ren = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    rep3 = lint_book.lint(world, {"ren": ren})
    check("ren-lints-error-free", rep3["errors"] == [], str(rep3["errors"]))
    check("ren-carries-his-scar-as-engine-state",
          any(w.get("id") == "predator@WARINESS" for w in ren["baseline"]["wounds"] if isinstance(w, dict)))
    orphan = copy.deepcopy(ren)
    orphan["baseline"]["catalog"]["rows"].append({"wound": "ghost@WARINESS", "when": {"percept": ["x"]},
                                                  "lever": "WARINESS", "op": "x", "magnitude": 2.0, "source": "t"})
    e_orphan = " | ".join(lint_book.lint(world, {"ren": orphan})["errors"])
    check("error-row-names-a-wound-the-sheet-does-not-carry", "baseline.wounds does not carry" in e_orphan, e_orphan)

    # GATE 5 (bond-arithmetic.md s3): the block beside relationships; in_group retired; a prose rate word
    # is named here instead of refusing at the character's first witnessed beat.
    check("the-migrated-fixtures-carry-a-registered-block", bool(maren["current"].get("attachments")) and bool(ren["current"].get("attachments")))
    ig = copy.deepcopy(maren); ig["baseline"]["relationship_priors"]["in_group"] = ["edda_elder"]
    check("error-in_group-is-retired", "in_group is RETIRED" in " | ".join(lint_book.lint(world, {"maren": ig})["errors"]))
    unreg = copy.deepcopy(maren); unreg["current"]["attachments"]["loc.tower"] = {"hold": .5, "sign": "+", "note": "x"}
    check("error-an-unregistered-attachment-key", "ATTACH_ENTITY_UNREGISTERED" in " | ".join(lint_book.lint(world, {"maren": unreg})["errors"]))
    prose = copy.deepcopy(ren); prose["baseline"]["relationship_priors"]["update"]["withdraw_speed"] = "slowly, over a season of small proofs"
    check("error-a-prose-rate-word", "relationship_priors.update" in " | ".join(lint_book.lint(world, {"ren": prose})["errors"]))

    if FAILS:
        print("\ntest_lint_book: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_lint_book: OK (fixture clean; broken char caught pre-run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
