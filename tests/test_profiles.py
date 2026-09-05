#!/usr/bin/env python3
"""test_profiles.py — every PROFILE_ refusal, executed.

WHY EXECUTED AND NOT SCANNED. `tests/test_errors.py` already proves, by parsing the tree, that this
module carries no prose raise and that every registered code is raised somewhere. Neither of those
runs a line of it. A code can be registered, spelled right at the raise, and attached to a condition
that never fires — or fires for something else — and both scans stay green.

THE CASE TABLE IS CHECKED AGAINST THE REGISTRY, not the other way round: a new PROFILE_ code with no
executing case here FAILS. That is the half a hand-kept table normally gets wrong, and it is the
direction that fails silent if left alone.

These refusals are AUTHOR-FACING. Every one rejects something a person wrote by hand — a profile id
that resolves to nothing, a diff field outside the schema, a magnitude past its cap — which is the
same job the VAULT_ family does for the .md notes.

Script-style, stdlib only, exit 0 = all pass.
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import codes, profiles                            # noqa: E402
from src.engine.records import RecordError                        # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _profile(**over):
    """A VALID profile. Every case below breaks exactly one thing about it."""
    row = {"id": "p", "name": "P", "category": "c", "baseline_diffs": {}}
    row.update(over)
    return row


def _row(**over):
    r = {"lever": "SEEKING", "op": "x", "magnitude": 1.0}
    r.update(over)
    return r


#: code -> a call that must refuse with exactly that code.
CASES = {
    "PROFILE_NOT_A_DICT":            lambda: profiles.validate_profile("not a profile"),
    "PROFILE_MISSING_REQUIRED_KEY":  lambda: profiles.validate_profile({"id": "p"}),
    "PROFILE_BASELINE_DIFFS_NOT_A_DICT": lambda: profiles.validate_profile(_profile(baseline_diffs=[])),
    "PROFILE_DIFF_FIELD_UNKNOWN":    lambda: profiles.validate_profile(_profile(baseline_diffs={"nonsense": 0.1})),
    "PROFILE_DIFF_VALUE_NOT_NUMERIC": lambda: profiles.validate_profile(
        _profile(baseline_diffs={"default_trust": "a lot"})),
    "PROFILE_DIFF_MAGNITUDE_EXCEEDED": lambda: profiles.validate_profile(
        _profile(baseline_diffs={"default_trust": 9.0})),
    "PROFILE_CATALOG_ROW_NOT_A_DICT": lambda: profiles.validate_profile(_profile(catalog_rows=["nope"])),
    "PROFILE_CATALOG_ROW_LEVER_UNKNOWN": lambda: profiles.validate_profile(
        _profile(catalog_rows=[_row(lever="VIBES")])),
    "PROFILE_CATALOG_ROW_OP_UNKNOWN": lambda: profiles.validate_profile(
        _profile(catalog_rows=[_row(op="?")])),
    "PROFILE_CATALOG_ROW_MAGNITUDE_NOT_NUMERIC": lambda: profiles.validate_profile(
        _profile(catalog_rows=[_row(magnitude="big")])),
    "PROFILE_CATALOG_ROW_MULTIPLIER_EXCEEDED": lambda: profiles.validate_profile(
        _profile(catalog_rows=[_row(op="x", magnitude=99.0)])),
    "PROFILE_CATALOG_ROW_ADDITIVE_EXCEEDED": lambda: profiles.validate_profile(
        _profile(catalog_rows=[_row(op="+", magnitude=99.0)])),
    "PROFILE_ID_UNKNOWN":            lambda: profiles.get("no-such-profile", {}),
    "PROFILE_PRIOR_NOT_A_DICT":      lambda: profiles.compose("not a prior", []),
    "PROFILE_PICKS_NOT_A_LIST":      lambda: profiles.compose({}, "not a list"),
    "PROFILE_PICK_MALFORMED":        lambda: profiles.compose({}, [{"weight": 1.0}]),
    "PROFILE_PICK_WEIGHT_RANGE":     lambda: profiles.compose({}, [{"profile": "p", "weight": 4.0}]),
    "PROFILE_FIELD_PATH_UNKNOWN":    lambda: profiles.path_for("a-field-nothing-reads"),
    "PROFILE_PLACE_ARGS_NOT_DICTS":  lambda: profiles.place("not a char", {}),
}


def test_every_case_refuses_with_its_OWN_code():
    for code, call in sorted(CASES.items()):
        try:
            call()
            check("refuses-with-%s" % code, False, "the malformed input was ACCEPTED")
        except RecordError as e:
            check("refuses-with-%s" % code, e.code == code, "got %r" % e.code)
        except Exception as e:                                    # noqa: BLE001
            check("refuses-with-%s" % code, False,
                  "raised %s, not a coded RecordError: %s" % (type(e).__name__, str(e)[:70]))


def test_the_case_table_is_CHECKED_AGAINST_the_registry():
    """The direction that fails silent if nobody looks: a new code with no case.

    Derived from `codes.CODES`, so adding a PROFILE_ refusal without exercising it here is red."""
    registered = {c for c in codes.CODES if c.startswith("PROFILE_")}
    check("every-REGISTERED-PROFILE-code-has-an-executing-case",
          not (registered - set(CASES)), str(sorted(registered - set(CASES))))
    check("no-case-names-an-UNREGISTERED-code",
          not (set(CASES) - registered), str(sorted(set(CASES) - registered)))


def test_a_VALID_profile_still_passes():
    """The control. A validator that refused everything would pass every case above."""
    check("a-valid-profile-validates", profiles.validate_profile(_profile()) is True)
    check("...with-a-real-catalog-row",
          profiles.validate_profile(_profile(catalog_rows=[_row()])) is True)
    check("...and-a-legal-diff",
          profiles.validate_profile(_profile(baseline_diffs={"default_trust": 0.1})) is True)


def main():
    print("test_profiles.py — every PROFILE_ refusal, executed\n")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        try:
            fn()
        except Exception as e:                                    # noqa: BLE001
            FAILS.append("%s RAISED %s: %s" % (fn.__name__, type(e).__name__, e))
            print("  FAIL  %s RAISED %s: %s" % (fn.__name__, type(e).__name__, str(e)[:110]))
    print("\n%s" % ("test_profiles: OK (every author-facing refusal fires with its own code)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
