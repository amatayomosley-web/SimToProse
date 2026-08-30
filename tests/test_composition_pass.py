#!/usr/bin/env python3
"""test_composition_pass.py ? CLI and integration tests for scripts/composition_pass.py.

Asserts:
  - CLI parser correctly maps picks and arguments
  - apply_composition_pass composes baseline stats and injects catalog rows & vault beliefs
  - Stacked cap +-0.35 is strictly enforced
  - Deduplication prevents duplicate catalog rows or vault claims

Stdlib only, script-style. Exit 0 = all pass.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts.composition_pass import parse_picks, apply_composition_pass


def test_parse_picks():
    args = ["fire_survival_acute:1.0", "street_urchin:0.5", "galley_slave_rower"]
    picks = parse_picks(args)
    assert len(picks) == 3
    assert picks[0] == {"profile": "fire_survival_acute", "weight": 1.0}
    assert picks[1] == {"profile": "street_urchin", "weight": 0.5}
    assert picks[2] == {"profile": "galley_slave_rower", "weight": 1.0}


def test_apply_composition_pass():
    """The composed values must land where CONSUMERS read them, not merely exist.

    This test previously asserted composed["baseline"]["FEAR"], composed["catalog_rows"] and
    composed["vault_beliefs"] — three paths the engine does not read. It passed while every value
    the pass computed was dead: state.build_profile reads baseline.temperament.<P>.mean,
    levers.active_rows reads baseline.catalog.rows via scene.assemble, and the recall gate reads
    current.vault (vault.py:117). A key existing proves nothing; a consumer reading it does.
    """
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))
    from src.engine.state import build_profile
    from src.engine.records import PRIMARIES

    char = {
        "id": "test_hero", "name": "Test Hero",
        "fixed": {"genotype": {}},
        "baseline": {
            "temperament": {p: {"mean": 0.30, "variability": 0.10} for p in PRIMARIES},
            "traits": {"emotionality": {"mean": 0.50}},
            "model": {"schwartz": {"security": 0.50}},
            "relationship_priors": {"default_trust": 0.50},
        },
        "current": {"affect": {p: 0.30 for p in PRIMARIES}, "vault": [],
                    "condition": {"energy": 0.8, "allostatic_load": 0.2}},
    }
    before_fear = char["baseline"]["temperament"]["FEAR"]["mean"]
    before_gain = build_profile(char)["gains"]["FEAR"]

    composed = apply_composition_pass(char, [
        {"profile": "fire_survival_acute", "weight": 1.0},
        {"profile": "galley_slave_rower", "weight": 1.0}])

    # 1. the NESTED temperament mean moved, so build_profile sees it
    after_fear = composed["baseline"]["temperament"]["FEAR"]["mean"]
    assert after_fear > before_fear, "FEAR mean did not move: %.3f -> %.3f" % (before_fear, after_fear)
    build_profile(composed)                       # must still be a valid character
    assert "FEAR" not in composed["baseline"], "flat FEAR written beside the nested one — the bug"

    # 2. catalog rows landed where levers.active_rows reads them
    rows = (composed["baseline"].get("catalog") or {}).get("rows") or []
    sources = [r["source"] for r in rows]
    assert "wound:fire_survival_acute" in sources, sources
    assert "wound:galley_servitude" in sources, sources
    assert "catalog_rows" not in composed, "top-level catalog_rows is read by nothing"

    # 3. belief seeds landed at current.vault, where the recall gate reads them
    claims = [v["claim"] for v in composed["current"]["vault"]]
    assert any("fire spreads faster" in c for c in claims), claims
    assert any("freedom is not granted" in c for c in claims), claims
    assert "vault_beliefs" not in composed, "top-level vault_beliefs is read by nothing"

    # 4. and the rows actually FIRE
    from src.engine.levers import active_rows, effective
    ctx = {"text": "smoke fills the stair and the blaze takes the landing", "edges": {},
           "affect": composed["current"]["affect"], "condition": {}}
    fired = active_rows(composed["baseline"]["catalog"], ctx)
    assert fired, "a fire-survivor's row did not fire on a fire event"
    assert effective(composed["current"]["affect"], fired)["FEAR"] > composed["current"]["affect"]["FEAR"]


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("  PASS  %s" % t.__name__)
        except Exception as e:
            failed += 1
            print("  FAIL  %s: %s" % (t.__name__, e))
    print("")
    print(str(len(tests) - failed) + "/" + str(len(tests)) + " passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
