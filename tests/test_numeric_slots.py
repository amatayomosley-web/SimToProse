"""test_numeric_slots.py — a book that lints clean must be a book that runs.

WHY. On 2026-08-30 a controlled trial handed three writers nothing but the three authoring
blueprints and asked each to build a book. All three linted with ZERO ERRORS. One of them could not
run: its author had written a sentence where a number belongs —

    "intensity": "it takes me over"

— because the form told them to circle a phrase. `scripts/lint_book.py` reported clean. It even
printed the offending sentence INSIDE an unrelated warning ("intensity it takes hold of me when it
comes reaches no arithmetic") and still called the book good. The run then died on its first beat,
deep in `src/engine/identity_view.py`, with a bare `ValueError` naming neither the character nor the
field:

    ValueError: direction: value must be a number in [0,1], got 'it takes me over'

A pre-flight that passes a book which cannot run is not a pre-flight. That is the same shape as the
incident this whole effort began with: a check that fires, reports clean, and lets the failure land
somewhere it cannot be traced from.

THE ROT GUARD. The numeric fields are declared once, in the sheet's contract
(src/engine/contracts_sheet.py, gate sheet-contract 2026-09-25) - they were a hand-written list in
lint_book, which walked `_note` annotations as numbers. A declaration that mirrors something the code
already knows is this repo's most expensive failure class — it has cost it seven times (the verify
block's 21 suites, coherence_probe's PATHS, basis_probe's ROLE_PAIRS, consolidation's _KNOWN_DIMS,
test_bonds' _P, scene.py's state_fields_read, SPEC-LEDGER's citations). So it does not stand alone:
`test_the_key_list_covers_what_the_engine_checks` derives every name the engine actually hands to
`_check_num` from source, and fails when the contract stops declaring them as numbers.

Run: python tests/test_numeric_slots.py
"""
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import contracts, contracts_sheet, systems            # noqa: E402
from src.engine.direction import _check_num, DirectionError           # noqa: E402
from src.engine.records import PATHS                              # noqa: E402

_FAILS = []


def check(name, cond, detail=""):
    if not cond:
        _FAILS.append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  - " + detail) if (detail and not cond) else ""))


def _errors(tag, ch):
    """The contract's errors for one sheet, one line each: `<path> <why>`."""
    return ["%s: %s %s" % (tag, f["path"], f["message"])
            for f in contracts.check(ch, contracts_sheet.SHEET, systems.defaults()) if f["severity"] == "error"]


def _sheet(**overrides):
    """A minimal character engine block that lints clean, so a test can break exactly one field."""
    ch = {
        "fixed": {"id": "x", "name": "X", "people": "human",
                  "position": {"place": "p", "class": "c", "era": "e", "niche": "n"},
                  "genotype": {"WARINESS": {"hit": "typical"}}},
        "baseline": {
            "temperament": {p: {"mean": 0.5} for p in PATHS},
            "traits": {"emotionality": {"mean": 0.5}},
            "drives": {"goals": [{"goal": "g", "priority": 0.5}]},
            "skills": {"perception": 0.5},
            "wounds": [{"id": "fire@WARINESS", "concept": "fire", "path": "WARINESS", "intensity": 0.5,
                        "source": "profile:t", "text": "t", "trigger": ["smoke"]}],
        },
        "current": {
            "affect": {p: 0.5 for p in PATHS},
            "condition": {"energy": 0.5, "allostatic_load": 0.3},
            "relationships": {"y": {"trust": 0.5, "affinity": 0.5}},
        },
    }
    for path, val in overrides.items():
        node = ch
        parts = path.split(".")
        for k in parts[:-1]:
            node = node[int(k)] if k.isdigit() else node[k]
        last = parts[-1]
        node[int(last) if last.isdigit() else last] = val
    return ch


def test_prose_in_a_numeric_slot_is_an_ERROR_not_a_warning():
    """THE MEASURED CASE. Every one of these linted clean before 2026-08-30."""
    print("\n[1] prose in a numeric slot")
    # (a wound's intensity is the measured case: it moved from drives.fears_wounds, now retired, to
    # baseline.wounds, which the wound module checks; goals[].satisfaction left the list - nothing reads it,
    # so the contract reports it as reaching nothing rather than as a run that will break)
    cases = [
        ("baseline.wounds.0.intensity", "it takes me over"),
        ("baseline.drives.goals.0.priority", "it comes before everything"),
        ("current.condition.energy", "worn thin"),
        ("current.relationships.y.trust", "I would not turn my back"),
        ("baseline.skills.perception", "sharp-eyed"),
        ("baseline.temperament.WARINESS.mean", "jumpy"),
    ]
    for path, prose in cases:
        errs = _errors("char 'x'", _sheet(**{path: prose}))
        hit = [e for e in errs if path.rsplit(".", 1)[-1] in e]
        check("prose-caught:%s" % path, bool(hit), "no error for %r; got %s" % (prose, errs))


def test_a_valid_sheet_reports_nothing():
    """The other half. A guard that fires on everything is not a guard."""
    print("\n[2] a valid sheet is silent")
    errs = _errors("char 'x'", _sheet())
    check("clean-sheet-is-clean", errs == [], str(errs))
    ann = _sheet()
    ann["baseline"]["skills"]["_note"] = "perception is the point of her"      # an annotation, not a number
    ann["baseline"]["traits"]["emotionality"]["_note"] = "the house taught her"
    check("an-annotation-in-a-number-table-is-no-error", _errors("char 'x'", ann) == [], str(_errors("char 'x'", ann)))


def test_a_multiplier_is_numeric_but_unbounded():
    """`catalog[].magnitude` is a MULTIPLIER when its op is "x" — standard-vectors sizes rows at
    x0.6-1.5 and the reference book carries 1.45 — and an additive delta when the op is "+", where
    a negative value is a legitimate debuff.

    The first version of this sweep bounded it to [0,1] and reported FIVE errors against the
    reference book, every one of them correct authoring. Caught by running the guard on a real book
    before trusting it. Prose there must still fail; a 1.45 must not."""
    print("\n[3b] a multiplier is numeric, not bounded")
    ch = _sheet()
    ch["baseline"]["catalog"] = [{"when": {"percept": ["x"]}, "lever": "WARINESS",
                                  "op": "x", "magnitude": 1.45, "source": "s"}]
    errs = _errors("t", ch)
    check("multiplier-above-one-is-fine", errs == [], str(errs))
    ch["baseline"]["catalog"][0]["magnitude"] = "hits him hard"
    errs = _errors("t", ch)
    check("prose-in-a-multiplier-still-fails", bool(errs), str(errs))


def test_out_of_range_and_bool_are_caught():
    print("\n[3] range, and the bool trap")
    check("above-one", bool(_errors("t", _sheet(**{"current.condition.energy": 1.4}))))
    check("below-zero", bool(_errors("t", _sheet(**{"current.condition.energy": -0.2}))))
    # True is an int in Python and would sail through a naive isinstance check while meaning nothing.
    errs = _errors("t", _sheet(**{"current.condition.energy": True}))
    check("bool-is-not-a-number", bool(errs), "True passed as a number: %s" % errs)


def test_the_key_list_covers_what_the_engine_checks():
    """THE ROT GUARD. Derive from source every name the engine hands to `_check_num`, and assert the
    sheet's contract declares it a number. A hand-maintained mirror of something the code knows is the
    failure class that has cost this repo seven separate times."""
    print("\n[4] the list cannot silently rot")
    names = set()
    for mod in ("direction.py", "identity_view.py"):
        with open(os.path.join(REPO, "src", "engine", mod), encoding="utf-8") as fh:
            for m in re.finditer(r'_check_num\(\s*"([^"]+)"', fh.read()):
                names.add(m.group(1))
    check("found-check_num-callers", bool(names), "no _check_num call sites found — the derivation broke")
    numeric = [f.path.split(".") for f in contracts_sheet.SHEET if f.kind in ("unit", "number", "signed")]
    covered = {segs[-1] for segs in numeric} | {segs[-2] for segs in numeric if segs[-1] in ("<name>", "<id>", "<PATH>")}
    missing = []
    for n in sorted(names):
        # names look like "condition.energy", "temperament[%s].mean", "edge.%s", "value"
        leaf = re.split(r"[.\[]", n)[-1].strip("]%s ")
        if not leaf or "%" in leaf or leaf == "value":
            continue          # a generic placeholder names no field; the walk covers it by key
        if leaf not in covered:
            missing.append("%s (leaf %r)" % (n, leaf))
    check("every-checked-field-is-in-the-list", not missing,
          "the engine checks these and the sheet's contract does not declare them numbers: %s" % missing)


def test_the_runtime_raise_is_coded_and_actionable():
    print("\n[5] the runtime raise names the way back")
    try:
        _check_num("value", "it takes me over")
        check("raises", False, "no raise")
    except DirectionError as e:
        check("raises", True)
        check("has-a-code", e.code == "DIRECTION_VALUE_NOT_IN_UNIT_INTERVAL", str(e.code))
        check("keeps-the-original-message", "must be a number in [0,1]" in str(e), str(e))
        check("names-the-preflight", "lint_book.py" in str(e),
              "a raise this deep must say how to find the field: %s" % e)


def main():
    print("test_numeric_slots.py - a book that lints clean must be a book that runs")
    for t in (test_prose_in_a_numeric_slot_is_an_ERROR_not_a_warning,
              test_a_valid_sheet_reports_nothing,
              test_a_multiplier_is_numeric_but_unbounded,
              test_out_of_range_and_bool_are_caught,
              test_the_key_list_covers_what_the_engine_checks,
              test_the_runtime_raise_is_coded_and_actionable):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
