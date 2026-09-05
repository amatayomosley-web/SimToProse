#!/usr/bin/env python3
"""test_memory_decay.py — Track 3: Memory Decay & Temporal Forgetting Curves.

Proves:
  1. Core identity beliefs never decay over time (Law 1).
  2. Transient beliefs decay toward floor (0.05) as delta_t increases.
  3. Durable beliefs decay slowly toward a high permanence floor (0.35).
  4. Decayed transient beliefs naturally slip from active recall as retrieval cost rises.
  5. Recalling a belief resets delta_t and restores accessibility; spaced repetition flattens decay.
  6. Live relationship connection scales retention (Finding 4).
  7. Decayed memories pass confidence_eff to prompt sureness in words (Finding 6).
  8. Recall history is derived pure from chronicle decision_manifests (Finding 1).
Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import decay
from src.engine.gate import run_gate
from src.engine.direction import sureness
from src.engine.scene import _recall_for_packet

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  -- " + detail) if (detail and not cond) else ""))


def test_core_belief_invariance():
    print("\n[1] Core Identity Invariance (Zero Decay)")
    b_core = {
        "claim": "I am Kael, sworn tracker of the western border",
        "confidence": 0.95,
        "provenance": "core",
        "durability": "core",
        "created_turn": 1,
    }
    c_0 = decay.calculate_effective_confidence(b_core, current_turn=1)
    c_50 = decay.calculate_effective_confidence(b_core, current_turn=50)
    c_500 = decay.calculate_effective_confidence(b_core, current_turn=500)

    check("turn-0-confidence-exact", c_0 == 0.95)
    check("turn-50-confidence-preserved", c_50 == 0.95)
    check("turn-500-confidence-preserved", c_500 == 0.95)


def test_transient_vs_durable_decay():
    print("\n[2] Transient vs Durable Forgetting Curves")
    b_transient = {
        "claim": "Saw a stray gray mule near the stables this morning",
        "confidence": 0.85,
        "durability": "transient",
        "created_turn": 10,
        "last_recalled_turn": 10,
    }
    b_durable = {
        "claim": "My brother died in the crossing at Oakhaven",
        "confidence": 0.95,
        "durability": "durable",
        "created_turn": 10,
        "last_recalled_turn": 10,
    }

    # At turn 10 (delta_t = 0)
    check("transient-initial-full", decay.calculate_effective_confidence(b_transient, 10) == 0.85)
    check("durable-initial-full", decay.calculate_effective_confidence(b_durable, 10) == 0.95)

    # At turn 25 (delta_t = 15)
    t_15 = decay.calculate_effective_confidence(b_transient, 25)
    d_15 = decay.calculate_effective_confidence(b_durable, 25)
    check("transient-fades-substantially", t_15 < 0.20, f"actual: {t_15}")
    check("durable-remains-strong", d_15 > 0.60, f"actual: {d_15}")

    # At turn 80 (delta_t = 70)
    t_70 = decay.calculate_effective_confidence(b_transient, 80)
    check("transient-hits-floor", abs(t_70 - decay.FLOOR_TRANSIENT) < 0.01, f"actual: {t_70}")
    d_160 = decay.calculate_effective_confidence(b_durable, 160)
    check("durable-levels-at-permanence-floor", abs(d_160 - decay.FLOOR_DURABLE) < 0.01, f"actual: {d_160}")


def test_gate_retrieval_under_decay():
    print("\n[3] Gate Coupling: Decayed memory slips from normal recall")
    b_clue = {
        "claim": "Saw a beggar wearing blue ribbon near the west gate",
        "confidence": 0.85,
        "durability": "transient",
        "created_turn": 1,
        "last_recalled_turn": 1,
        "links": ["blue_ribbon"],
    }
    vault = [b_clue]
    triggers = ["blue_ribbon"]

    # At turn 1: fresh memory (cost = 1.0 - 0.85 = 0.15 <= 0.50 budget)
    condition_normal = {"energy": 0.5, "allostatic_load": 0.0}  # budget = 0.50
    recalled_fresh = run_gate(triggers, vault, {}, [], condition_normal, current_turn=1)
    check("fresh-memory-recalled", len(recalled_fresh) == 1)

    # At turn 30: decayed memory (eff_conf ~0.05 -> cost ~0.95 > 0.50 budget)
    recalled_decayed = run_gate(triggers, vault, {}, [], condition_normal, current_turn=30)
    check("decayed-memory-suppressed-under-normal-energy", len(recalled_decayed) == 0)

    # At turn 30 under hyper-focus / full rest: budget = 1.0 -> cost 0.95 <= 1.0 -> retrieved!
    condition_hyper = {"energy": 1.0, "allostatic_load": 0.0}  # budget = 1.0
    recalled_hyper = run_gate(triggers, vault, {}, [], condition_hyper, current_turn=30)
    check("decayed-memory-retrievable-under-high-energy", len(recalled_hyper) == 1)


def test_memory_refresh_and_spaced_repetition():
    print("\n[4] Reinforcement & Spaced Repetition")
    b = {
        "claim": "The watchword for the guard post is Falcon",
        "confidence": 0.80,
        "durability": "transient",
        "created_turn": 1,
        "last_recalled_turn": 1,
        "recall_count": 0,
    }

    c_decayed = decay.calculate_effective_confidence(b, current_turn=16)
    check("unreinforced-fades", c_decayed < 0.20)

    refreshed = decay.record_belief_recall(b, current_turn=16)
    c_refreshed = decay.calculate_effective_confidence(refreshed, current_turn=16)
    check("refreshed-memory-sharp-again", c_refreshed == 0.80)
    check("recall-count-incremented", refreshed["recall_count"] == 1)

    practiced = dict(refreshed)
    practiced["recall_count"] = 4
    practiced["last_recalled_turn"] = 20
    c_practiced_10 = decay.calculate_effective_confidence(practiced, current_turn=30)
    raw_transient_10 = decay.calculate_effective_confidence(b, current_turn=11)
    check("spaced-repetition-slows-decay", c_practiced_10 > raw_transient_10, f"{c_practiced_10} vs {raw_transient_10}")


def test_live_connection_slows_decay():
    print("\n[5] Live Connection Scaling (Finding 4)")
    b_friend = {"claim": "Maren loves winter pears", "confidence": 0.85, "links": ["maren"], "durability": "transient"}
    b_stranger = {"claim": "Joss loves winter pears", "confidence": 0.85, "links": ["joss"], "durability": "transient"}

    relationships = {
        "maren": {"affinity": 0.9, "trust": 0.9, "respect": 0.8},
        "joss": {"affinity": 0.5, "trust": 0.5, "respect": 0.5},
    }

    c_friend = decay.calculate_effective_confidence(b_friend, elapsed=12, relationships=relationships)
    c_stranger = decay.calculate_effective_confidence(b_stranger, elapsed=12, relationships=relationships)

    check("friend-memory-decays-slower", c_friend > c_stranger, f"{c_friend} vs {c_stranger}")
    check("stranger-memory-faded", c_stranger < 0.20)
    check("friend-memory-still-accessible", c_friend > 0.28, f"actual: {c_friend}")


def test_faintness_reaches_prompt_sureness():
    print("\n[6] Decayed Memory Portrayed with Uncertainty in Words (Finding 6)")
    b_fresh = {"claim": "The pass is blocked", "confidence": 0.95, "confidence_eff": 0.95, "provenance": "lived"}
    b_faded = {"claim": "The pass is blocked", "confidence": 0.95, "confidence_eff": 0.18, "provenance": "lived"}

    p_fresh = _recall_for_packet(b_fresh)
    p_faded = _recall_for_packet(b_faded)

    check("packet-uses-confidence-eff", p_faded["confidence"] == 0.18)
    check("fresh-narrates-certainty", sureness(p_fresh["confidence"]) == "you do not entertain the alternative")
    check("faded-narrates-uncertainty", sureness(p_faded["confidence"]) == "you would not stake anything on it")


def test_chronicle_fold_recall_history():
    print("\n[7] Replay Derivation from Chronicle (Finding 1)")
    import sqlite3
    tmp = os.path.join(tempfile.mkdtemp(), "test_chronicle.db")
    con = sqlite3.connect(tmp)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE decision_manifests (run_id TEXT, turn INTEGER, actor TEXT, manifest TEXT)")

    con.execute("INSERT INTO decision_manifests VALUES (?, ?, ?, ?)",
                ("r1", 5, "kael", json.dumps({"recall_ids": ["b:sigil", "b:crates"]})))
    con.execute("INSERT INTO decision_manifests VALUES (?, ?, ?, ?)",
                ("r1", 12, "kael", json.dumps({"recall_ids": ["b:sigil"]})))

    history = decay.fold_recall_history(con, "r1", "kael")
    check("sigil-found-in-history", "b:sigil" in history)
    check("sigil-last-turn-is-12", history["b:sigil"]["last_turn"] == 12)
    check("sigil-count-is-2", history["b:sigil"]["count"] == 2)
    check("crates-last-turn-is-5", history["b:crates"]["last_turn"] == 5)
    check("crates-count-is-1", history["b:crates"]["count"] == 1)


if __name__ == "__main__":
    test_core_belief_invariance()
    test_transient_vs_durable_decay()
    test_gate_retrieval_under_decay()
    test_memory_refresh_and_spaced_repetition()
    test_live_connection_slows_decay()
    test_faintness_reaches_prompt_sureness()
    test_chronicle_fold_recall_history()
    print("\n" + "-" * 50)
    print(f"{len(PASS)} passed, {len(FAIL)} failed")
    sys.exit(1 if FAIL else 0)
