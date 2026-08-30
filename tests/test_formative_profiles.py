#!/usr/bin/env python3
"""test_formative_profiles.py ? formative profile library, admission gate, and composition.

Asserts:
  - 94 canonical profiles load, validate, and have valid active schema fields
  - Cosine separability distinguishes profiles (no duplicate >= 0.95 in library)
  - Admission gate rejects duplicates (sim >= 0.95), unconsumed fields, and out-of-bounds diffs
  - Composition sums weighted diffs over prior and strictly enforces the +-0.35 stacked cap
  - Deterministic: same inputs -> exact same output

Stdlib only, script-style. Exit 0 = all pass.
"""
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import profiles as P
from src.engine.records import PRIMARIES


def test_library_integrity():
    avail = P.available()
    assert len(avail) == 94, "Expected 94 profiles, got %d" % len(avail)
    for pid in avail:
        p = P.get(pid)
        assert p["id"] == pid
        assert P.validate_profile(p), "Profile %s failed validation" % pid


def test_library_categories():
    cats = P.categories()
    expected = {
        "physical_trauma", "scarcity_deprivation", "social_isolation",
        "relational_betrayal", "violence_conflict", "vocation_discipline",
        "privilege_intrigue", "spiritual_institutional"
    }
    assert set(cats.keys()) == expected, "Categories mismatch: %s" % set(cats.keys())
    for c, pids in cats.items():
        assert len(pids) >= 10, "Category %s expected >= 10 profiles, got %d" % (c, len(pids))


def test_pairwise_separability():
    avail = P.available()
    for i, pid1 in enumerate(avail):
        p1 = P.get(pid1)
        for j, pid2 in enumerate(avail):
            if i >= j:
                continue
            p2 = P.get(pid2)
            sim = P.similarity(p1, p2)
            assert sim < P.MAX_COSINE_SIMILARITY, (
                "Profiles %s and %s too similar (%0.3f >= %0.2f)" % (pid1, pid2, sim, P.MAX_COSINE_SIMILARITY)
            )


def test_admit_rejects_duplicate():
    clone = dict(P.get("fire_survival_acute"))
    clone["id"] = "fire_survival_clone"
    clone["name"] = "Fire Survival Duplicate"
    admitted, reason = P.admit(clone)
    assert not admitted, "Duplicate should be rejected"
    assert "Duplicate rejection" in reason, reason


def test_admit_rejects_unconsumed_field():
    bad = {
        "id": "bad_field",
        "category": "physical_trauma",
        "name": "Bad Field Proposal",
        "baseline_diffs": {"some_random_untracked_field": 0.15}
    }
    admitted, reason = P.admit(bad)
    assert not admitted, "Unconsumed field should be rejected"
    assert "unconsumed/invalid field" in reason, reason


def test_admit_rejects_out_of_bounds_diff():
    bad = {
        "id": "bad_magnitude",
        "category": "physical_trauma",
        "name": "Oversized Diff",
        "baseline_diffs": {"FEAR": 0.50}
    }
    admitted, reason = P.admit(bad)
    assert not admitted, "Diff > 0.35 should be rejected"
    assert "exceeds max magnitude" in reason, reason


def test_admit_rejects_out_of_bounds_lever_multiplier():
    bad = {
        "id": "bad_multiplier",
        "category": "physical_trauma",
        "name": "Oversized Multiplier",
        "baseline_diffs": {"FEAR": 0.10},
        "catalog_rows": [{"when": {"percept": ["fire"]}, "lever": "FEAR", "op": "x", "magnitude": 4.0}]
    }
    admitted, reason = P.admit(bad)
    assert not admitted, "Multiplier > 2.5 should be rejected"
    assert "exceeds max 2.5" in reason, reason


def test_admit_accepts_valid_orthogonal_profile():
    valid = {
        "id": "arctic_tundra_nomad",
        "category": "physical_trauma",
        "name": "Arctic Tundra Nomad",
        "description": "Raised in permafrost waste, surviving extreme blizzards",
        "baseline_diffs": {"competence": 0.20, "stimulation": -0.20, "tradition": 0.15},
        "catalog_rows": [
            {"when": {"percept": ["blizzard", "whiteout", "frostbite"]}, "lever": "FEAR", "op": "x", "magnitude": 1.7, "source": "wound:blizzard"}
        ],
        "vault_belief_seeds": [
            {"claim": "the whiteout shows no landmarks; stop moving and you freeze", "confidence": 0.95, "provenance": "formative:arctic"}
        ]
    }
    admitted, reason = P.admit(valid)
    assert admitted, "Valid profile should be admitted: %s" % reason


def test_compose_single_profile():
    prior = {"FEAR": 0.25, "security": 0.55, "emotionality": 0.50}
    picks = [{"profile": "fire_survival_acute", "weight": 1.0}]
    composed = P.compose(prior, picks)
    assert abs(composed["FEAR"] - 0.35) < 1e-4
    assert abs(composed["security"] - 0.70) < 1e-4
    assert abs(composed["emotionality"] - 0.58) < 1e-4


def test_compose_enforces_max_stacked_cap():
    prior = {"FEAR": 0.25, "security": 0.55}
    picks = [
        {"profile": "fire_survival_acute", "weight": 1.0},
        {"profile": "predator_mauling", "weight": 1.0},
        {"profile": "sacked_settlement", "weight": 1.0}
    ]
    composed = P.compose(prior, picks)
    assert abs(composed["FEAR"] - 0.60) < 1e-4
    assert abs(composed["security"] - 0.90) < 1e-4


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
