# -*- coding: utf-8 -*-
"""direction.py after the band-phrase affect renderer was retired (2026-09-08).

WHAT THIS COVERS NOW. `direct_affect` and its tables (`_PHRASES`, `_REFLEXIVE_PHRASES`,
`_UNBOUND_PHRASES`, `_BANDS`, `_DEV_THRESH`, `_slope_marker`, `_phrase_for`) are gone: the rung
ladders are the emotion language, and `scripts/composer.py` selects two or three of them per beat.
What remains in this module renders things NO ladder describes -- the relationship edge, what you
think another feels about you, physical condition, and recall confidence -- plus the shared band
helper `identity_view` imports.

The retired assertions are preserved at `staging/tests/test_direction_affect_half.py`. They were
not failing on their own terms; their subject was removed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.direction import (  # noqa: E402
    direct_condition, direct_edge, sureness, _band, _check_num,
    _COND, _EDGE_BANDS, _EDGE_PHRASES, _SURENESS, _THEIR_VIEW_PHRASES)

_FAILED = []


def check(name, cond, detail=""):
    print("  %-58s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        _FAILED.append("%s %s" % (name, detail))


def _tables():
    """Every surviving actor-facing phrase table, walked whole."""
    out = []
    for tbl in (_EDGE_PHRASES, _THEIR_VIEW_PHRASES):
        for row in tbl.values():
            out.extend(row)
    out.extend(p for _, p in _COND)
    out.extend(p for _, p in _SURENESS)
    return out


def test_no_digits_ever():
    """Hard rule 5 on what is left. A digit in any surviving phrase reaches the actor."""
    bad = [p for p in _tables() if any(c.isdigit() for c in p)]
    check("no-digit-in-any-surviving-phrase", not bad, str(bad[:3]))


def test_separator_is_not_inside_a_phrase():
    """`direct_affect` joined clauses with "; " and no phrase could contain one. The edge renderer
    still joins, so the contract outlives the function that motivated it."""
    bad = [p for p in _tables() if "; " in p]
    check("clause-separator-not-inside-a-phrase", not bad, str(bad[:3]))


def test_condition_bands():
    lo = direct_condition({"energy": 0.1, "allostatic_load": 0.9})
    hi = direct_condition({"energy": 1.0, "allostatic_load": 0.0})
    check("condition-renders-and-differs", bool(lo) and bool(hi) and lo != hi)
    check("condition-carries-no-digit", not any(c.isdigit() for c in lo + hi))


def test_edges_and_sureness():
    e = direct_edge({"trust": 0.9, "affinity": 0.1, "respect": 0.5, "debt": 0.5})
    check("edge-renders", bool(e) and not any(c.isdigit() for c in e))
    s_lo, s_hi = sureness(0.1), sureness(0.99)
    check("sureness-renders-and-differs", s_lo != s_hi and not any(c.isdigit() for c in s_lo + s_hi))


def test_band_helper_still_serves_identity_view():
    """`identity_view` imports `_band`, `_check_num` and `_EDGE_BANDS` from here. The retirement of
    the affect renderer must not have taken them with it."""
    check("band-helper-monotone",
          _band(0.0, _EDGE_BANDS) <= _band(0.5, _EDGE_BANDS) <= _band(0.99, _EDGE_BANDS))
    check("band-helper-tops-out", _band(0.99, _EDGE_BANDS) == len(_EDGE_BANDS))
    from src.engine import identity_view                       # the real consumer, imported live
    check("identity_view-imports-cleanly", hasattr(identity_view, "direct_identity"))


def test_refusals_still_fire():
    """The shape refusals this module still owns must raise rather than translate a bad packet.
    `direction` is the only thing standing between a stored number and the prompt (hard rule 5), so
    it refuses what it cannot read."""
    raised = []
    for label, bad in (("condition-not-a-dict", lambda: direct_condition("not a dict")),
                       ("value-not-a-number", lambda: _check_num("x", "not a number"))):
        try:
            bad()
            raised.append((label, None))
        except Exception as exc:                               # noqa: BLE001 - the code is the point
            raised.append((label, getattr(exc, "code", None) or type(exc).__name__))
    check("both-shape-refusals-raise", all(c is not None for _, c in raised), str(raised))


def main():
    for fn in (test_no_digits_ever, test_separator_is_not_inside_a_phrase, test_condition_bands,
               test_edges_and_sureness, test_band_helper_still_serves_identity_view,
               test_refusals_still_fire):
        print("\n[%s]" % fn.__name__)
        fn()
    if _FAILED:
        print("\n%d FAILED" % len(_FAILED))
        for f in _FAILED:
            print("   " + f)
        sys.exit(1)
    print("\nPASS  direction (post-retirement surface)")


if __name__ == "__main__":
    main()
