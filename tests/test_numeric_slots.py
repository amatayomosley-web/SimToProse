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

THE ROT GUARD. `lint_book._NUMERIC_KEYS` is a hand-written list, and a hand-written list that
mirrors something the code already knows is this repo's most expensive failure class — it has cost
it seven times (the verify block's 21 suites, coherence_probe's PRIMARIES, basis_probe's ROLE_PAIRS,
consolidation's _KNOWN_DIMS, test_bonds' _P, scene.py's state_fields_read, SPEC-LEDGER's citations).
So the list does not stand alone: `test_the_key_list_covers_what_the_engine_checks` derives every
name the engine actually hands to `_check_num` from source, and fails when the list stops covering
them.

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

import lint_book                                                      # noqa: E402
from src.engine.direction import _check_num, DirectionError           # noqa: E402
from src.engine.records import PRIMARIES                              # noqa: E402

_FAILS = []


def check(name, cond, detail=""):
    if not cond:
        _FAILS.append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  - " + detail) if (detail and not cond) else ""))


def _sheet(**overrides):
    """A minimal character engine block that lints clean, so a test can break exactly one field."""
    ch = {
        "fixed": {"id": "x", "name": "X", "people": "human",
                  "position": {"place": "p", "class": "c", "era": "e", "niche": "n"},
                  "genotype": {"threat_reactivity": "typical"}},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES},
            "traits": {"emotionality": {"mean": 0.5}},
            "drives": {"goals": [{"goal": "g", "priority": 0.5, "satisfaction": 0.5}],
                       "fears_wounds": [{"wound": "w", "intensity": 0.5, "trigger": ["t"]}]},
            "skills": {"perception": 0.5},
        },
        "current": {
            "affect": {p: 0.5 for p in PRIMARIES},
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
    cases = [
        ("baseline.drives.fears_wounds.0.intensity", "it takes me over"),
        ("baseline.drives.goals.0.priority", "it comes before everything"),
        ("baseline.drives.goals.0.satisfaction", "nothing about this is settled"),
        ("current.condition.energy", "worn thin"),
        ("current.relationships.y.trust", "I would not turn my back"),
        ("baseline.skills.perception", "sharp-eyed"),
        ("baseline.temperament.FEAR.mean", "jumpy"),
    ]
    for path, prose in cases:
        errs = lint_book._numeric_slot_errors("char 'x'", _sheet(**{path: prose}))
        hit = [e for e in errs if path.rsplit(".", 1)[-1] in e and "not a number" in e]
        check("prose-caught:%s" % path, bool(hit), "no error for %r; got %s" % (prose, errs))


def test_a_valid_sheet_reports_nothing():
    """The other half. A guard that fires on everything is not a guard."""
    print("\n[2] a valid sheet is silent")
    errs = lint_book._numeric_slot_errors("char 'x'", _sheet())
    check("clean-sheet-is-clean", errs == [], str(errs))


def test_a_multiplier_is_numeric_but_unbounded():
    """`catalog[].magnitude` is a MULTIPLIER when its op is "x" — standard-vectors sizes rows at
    x0.6-1.5 and the reference book carries 1.45 — and an additive delta when the op is "+", where
    a negative value is a legitimate debuff.

    The first version of this sweep bounded it to [0,1] and reported FIVE errors against the
    reference book, every one of them correct authoring. Caught by running the guard on a real book
    before trusting it. Prose there must still fail; a 1.45 must not."""
    print("\n[3b] a multiplier is numeric, not bounded")
    ch = _sheet()
    ch["baseline"]["catalog"] = [{"when": {"percept": ["x"]}, "lever": "FEAR",
                                  "op": "x", "magnitude": 1.45, "source": "s"}]
    errs = lint_book._numeric_slot_errors("t", ch)
    check("multiplier-above-one-is-fine", errs == [], str(errs))
    ch["baseline"]["catalog"][0]["magnitude"] = "hits him hard"
    errs = lint_book._numeric_slot_errors("t", ch)
    check("prose-in-a-multiplier-still-fails", bool(errs), str(errs))


def test_out_of_range_and_bool_are_caught():
    print("\n[3] range, and the bool trap")
    check("above-one", bool(lint_book._numeric_slot_errors("t", _sheet(**{"current.condition.energy": 1.4}))))
    check("below-zero", bool(lint_book._numeric_slot_errors("t", _sheet(**{"current.condition.energy": -0.2}))))
    # True is an int in Python and would sail through a naive isinstance check while meaning nothing.
    errs = lint_book._numeric_slot_errors("t", _sheet(**{"current.condition.energy": True}))
    check("bool-is-not-a-number", bool(errs), "True passed as a number: %s" % errs)


def test_the_key_list_covers_what_the_engine_checks():
    """THE ROT GUARD. Derive from source every name the engine hands to `_check_num`, and assert the
    linter's list covers it. A hand-maintained mirror of something the code knows is the failure
    class that has cost this repo seven separate times."""
    print("\n[4] the list cannot silently rot")
    names = set()
    for mod in ("direction.py", "identity_view.py"):
        with open(os.path.join(REPO, "src", "engine", mod), encoding="utf-8") as fh:
            for m in re.finditer(r'_check_num\(\s*"([^"]+)"', fh.read()):
                names.add(m.group(1))
    check("found-check_num-callers", bool(names), "no _check_num call sites found — the derivation broke")
    covered = lint_book._NUMERIC_KEYS | lint_book._NUMERIC_MAPS
    missing = []
    for n in sorted(names):
        # names look like "condition.energy", "temperament[%s].mean", "edge.%s", "value"
        leaf = re.split(r"[.\[]", n)[-1].strip("]%s ")
        if not leaf or "%" in leaf or leaf == "value":
            continue          # a generic placeholder names no field; the walk covers it by key
        if leaf not in covered:
            missing.append("%s (leaf %r)" % (n, leaf))
    check("every-checked-field-is-in-the-list", not missing,
          "the engine checks these and lint_book does not sweep them: %s" % missing)


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
