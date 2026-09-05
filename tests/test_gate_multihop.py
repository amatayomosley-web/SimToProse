#!/usr/bin/env python3
"""test_gate_multihop.py — Track 2: Multi-Hop Associative Graph Traversal.

Proves:
  1. Direct 1-hop matching succeeds as before.
  2. Multi-hop associative chain (the shopkeeper sigil: sigil -> crates -> maren -> veil)
     surfaces when cognitive energy budget is sufficient (rested character: budget 1.0).
  3. Narrowing under stress/fatigue: with budget 0.48, direct 1-hop memory (0.30) surfaces,
     while 2-hop (0.50) and 3-hop (0.80) associative leaps fail to fire.
  4. Hinge override: a marked hinge (must_surface=True) surfaces even under severe exhaustion.
Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import associative           # noqa: E402
from src.engine.gate import run_gate, belief_id  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  -- " + detail) if (detail and not cond) else ""))


def test_shopkeeper_sigil_rested():
    print("\n[1] Shopkeeper Sigil 3-Hop Associative Recall (Rested: energy=1.0, load=0.0)")
    b1 = {
        "claim": "Saw the coiled serpent mark burned on cargo crates 15 years ago",
        "confidence": 0.7,
        "provenance": "lived",
        "links": ["coiled_serpent", "harbor_crates"],
    }
    b2 = {
        "claim": "The harbor crates were part of Maren the dockmaster runs",
        "confidence": 0.8,
        "provenance": "lived",
        "links": ["harbor_crates", "maren"],
    }
    b3 = {
        "claim": "Maren let slip in private that she answered to the Veil",
        "confidence": 0.7,
        "provenance": "lived",
        "links": ["maren", "the_veil"],
    }
    vault = [b1, b2, b3]
    triggers = ["coiled_serpent"]

    # Rested state: budget = 1.0 * (1.0 - 0.0) = 1.0
    condition_rested = {"energy": 1.0, "allostatic_load": 0.0}
    recalled = run_gate(triggers, vault, {}, [], condition_rested)

    claims = [r["claim"] for r in recalled]
    check("b1-recalled", b1["claim"] in claims)
    check("b2-recalled", b2["claim"] in claims)
    check("b3-veil-recalled", b3["claim"] in claims)

    # Verify associative path is traced for b3
    veil_cands = [r for r in recalled if r["claim"] == b3["claim"]]
    check("veil-cand-exists", len(veil_cands) == 1)
    if veil_cands:
        check("veil-is-multihop", veil_cands[0].get("hops", 1) >= 2)
        check("path-contains-stepping-stones", len(veil_cands[0].get("path", [])) >= 3)


def test_shopkeeper_sigil_fatigued():
    print("\n[2] Calibrated Narrowing: Fatigue allows 1-hop (0.30) but severs 3-hop (0.80)")
    b1 = {
        "claim": "Saw the coiled serpent mark burned on cargo crates 15 years ago",
        "confidence": 0.7,
        "provenance": "lived",
        "links": ["coiled_serpent", "harbor_crates"],
    }
    b2 = {
        "claim": "The harbor crates were part of Maren the dockmaster runs",
        "confidence": 0.8,
        "provenance": "lived",
        "links": ["harbor_crates", "maren"],
    }
    b3 = {
        "claim": "Maren let slip in private that she answered to the Veil",
        "confidence": 0.7,
        "provenance": "lived",
        "links": ["maren", "the_veil"],
    }
    vault = [b1, b2, b3]
    triggers = ["coiled_serpent"]

    # Budget = 0.6 * (1.0 - 0.4 * 0.5) = 0.6 * 0.8 = 0.48
    # B1 cost: 0.30 <= 0.48 -> RECALLED
    # B2 cost: 0.50 > 0.48 -> SUPPRESSED
    # B3 cost: 0.80 > 0.48 -> SUPPRESSED
    condition_fatigued = {"energy": 0.6, "allostatic_load": 0.4}
    recalled = run_gate(triggers, vault, {}, [], condition_fatigued)

    claims = [r["claim"] for r in recalled]
    check("1-hop-b1-recalled-under-fatigue", b1["claim"] in claims)
    check("2-hop-b2-suppressed-under-fatigue", b2["claim"] not in claims)
    check("3-hop-b3-veil-suppressed-under-fatigue", b3["claim"] not in claims)


def test_hinge_must_surface_override():
    print("\n[3] Hinge Override: marked consequential target surfaces despite exhaustion")
    b_hinge = {
        "claim": "The code word for the courier is Blackfin",
        "confidence": 0.5,
        "links": ["courier", "blackfin"],
        "must_surface": True,
    }
    vault = [b_hinge]
    triggers = ["courier"]

    # Severe exhaustion: budget = 0.1 * 0.5 = 0.05 (normal cost would be 0.50)
    condition_exhausted = {"energy": 0.1, "allostatic_load": 1.0}
    recalled = run_gate(triggers, vault, {}, [], condition_exhausted)

    claims = [r["claim"] for r in recalled]
    check("hinge-surfaces-despite-exhaustion", b_hinge["claim"] in claims)


if __name__ == "__main__":
    test_shopkeeper_sigil_rested()
    test_shopkeeper_sigil_fatigued()
    test_hinge_must_surface_override()
    print("\n" + "-" * 50)
    print(f"{len(PASS)} passed, {len(FAIL)} failed")
    sys.exit(1 if FAIL else 0)
