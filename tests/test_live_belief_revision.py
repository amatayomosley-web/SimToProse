#!/usr/bin/env python3
"""test_live_belief_revision.py — Proves Track 1 belief revision functions during live runs.

Verifies:
  1. Live acquisition in-session:
     - Actor starts with active belief: "Torin is alive and hiding at the mill"
     - Next turn reports: "Torin is dead by the river"
     - When appended using the live per-turn driver path, fold_vault is executed forward.
     - The old belief status transitions to 'superseded' IN-SESSION.
     - Live recall pass surfaces ONLY the new belief, NEVER both contradictory beliefs.
  2. Decay sorting:
     - Phase 2 candidate salience sorts by decay-adjusted confidence (confidence_eff),
       not raw base confidence.
  3. 1-hop zero step cost:
     - Directly triggered 1.0 confidence belief costs 0.0, recalling even under 0.0 energy.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import acquisition
from src.engine.gate import run_gate, belief_id

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  -- " + detail) if (detail and not cond) else ""))


def test_live_turn_fold_vault():
    print("\n[1] Live Turn In-Session Vault Folding")
    # Character initial state
    old_b = {
        "claim": "Torin is alive and hiding at the mill",
        "confidence": 0.8,
        "provenance": "lived",
        "believed_value": True,
        "links": ["torin"],
        "status": "active",
    }
    char = {
        "fixed": {"name": "Kael"},
        "baseline": {},
        "current": {"vault": [old_b]},
    }

    # Turn reports contradictory event
    applied = {"target": "torin"}
    tags = {
        "summary": "Torin was confirmed dead by the river patrol",
        "confidence": 0.9,
        "durability": "durable",
    }

    # Assess returns new belief
    acquired = acquisition.assess(applied, tags, char)
    check("turn-assessed", acquired is not None)

    # Driver live path: append + fold_vault
    vault = char["current"]["vault"]
    vault.append(acquired)
    acquisition.fold_vault(vault)

    # In-session verification: old belief MUST be marked superseded immediately
    check("old-belief-marked-superseded-live", old_b.get("status") == "superseded")
    check("new-belief-marked-active-live", acquired.get("status") == "active")

    # Run recall gate immediately on live vault
    cond = {"energy": 1.0, "allostatic_load": 0.0}
    recalled = run_gate(["torin"], vault, {}, [], cond)

    check("only-one-belief-recalled", len(recalled) == 1)
    check("recalled-is-new-death-report", recalled[0]["claim"] == tags["summary"])
    check("stale-alive-belief-suppressed", not any("alive" in r["claim"] for r in recalled))


def test_salience_sorts_by_effective_confidence():
    print("\n[2] Salience Sorts by Effective Confidence")
    # b1 was created at turn 0, transient -> by turn 50 it has decayed to floor (0.05)
    b1 = {
        "claim": "The old wagon had red wheels",
        "confidence": 0.9,
        "created_turn": 0,
        "links": ["wagon"],
        "status": "active",
        "durability": "transient",
    }
    # b2 was created recently at turn 49, durable -> at turn 50 it is fresh (eff_conf ~ 0.7)
    b2 = {
        "claim": "The wagon axle is broken",
        "confidence": 0.7,
        "created_turn": 49,
        "links": ["wagon"],
        "status": "active",
        "durability": "durable",
    }
    vault = [b1, b2]

    # Under raw base confidence, b1 (0.9) would beat b2 (0.7).
    # Under decay-adjusted salience at turn 50, b2 (~0.7) beats decayed b1 (~0.05).
    cond = {"energy": 0.35, "allostatic_load": 0.0}
    recalled = run_gate(["wagon"], vault, {}, [], cond, current_turn=50)

    check("single-memory-selected", len(recalled) == 1)
    check("fresh-memory-preferred-over-decayed", recalled[0]["claim"] == b2["claim"])


def test_1hop_direct_cost_at_zero_energy():
    print("\n[3] 1-Hop Direct Match Zero Cost")
    b = {
        "claim": "The campfire is burning brightly",
        "confidence": 1.0,
        "confidence_eff": 1.0,
        "links": ["fire"],
        "status": "active",
    }
    # Energy is near zero: budget is minimal
    cond = {"energy": 0.01, "allostatic_load": 0.0}
    recalled = run_gate(["fire"], [b], {}, [], cond)
    check("certain-direct-memory-surfaces", len(recalled) == 1)


if __name__ == "__main__":
    test_live_turn_fold_vault()
    test_salience_sorts_by_effective_confidence()
    test_1hop_direct_cost_at_zero_energy()
    print("\n" + "-" * 50)
    print(f"{len(PASS)} passed, {len(FAIL)} failed")
    sys.exit(1 if FAIL else 0)
