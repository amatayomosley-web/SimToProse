#!/usr/bin/env python3
"""test_theory_of_mind.py — Track 4: Second-Order Theory of Mind & Epistemic Asymmetry.

Proves:
  1. Epistemic belief attribution schema: target_actor and epistemic_stance.
  2. The Omniscience Wall (Prompt Boundary):
     - Torin has a non-empty vault.
     - Kael knows the secret ("gold in the cellar") and Torin's ignorance.
     - Torin's assembled prompt contains ZERO occurrences of the secret token ("cellar").
  3. Positive Prompt Rendering:
     - Kael's assembled prompt explicitly renders "you believe torin is unaware that: ...".
  4. Witness Channel Leak Prevention:
     - During deception, Torin witnesses only the public act, never the private secret.
  5. Supersession Partitioned by Depth:
     - First-order reality never supersedes a second-order belief about another person.
     - Second-order updates supersede only matching target_actor beliefs.
  6. Substring Contradiction Hardening:
     - Unrelated claims with polarity words (e.g. "bridge is not far" vs "gold is in the cellar") do not contradict.
Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import acquisition, prompt
from src.engine.gate import run_gate, belief_id
from src.engine.direction import sureness

PASS, FAIL = [], []

_PRIMARIES = ("SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY", "DISGUST")
_TEMPERAMENT = {p: {"mean": 0.3, "variability": 0.1} for p in _PRIMARIES}
_STATE = {
    "affect": {p: 0.0 for p in _PRIMARIES},
    "condition": {"energy": 0.8, "allostatic_load": 0.1}
}


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  -- " + detail) if (detail and not cond) else ""))


def test_epistemic_attribution_schema():
    print("\n[1] Epistemic Attribution Schema")
    applied = {"target": "gold"}
    tags = {
        "summary": "The gold was hidden in the old cellar",
        "confidence": 0.9,
        "durability": "durable",
        "target_actor": "torin",
        "epistemic_stance": "ignorant_of",
    }
    char = {"fixed": {"name": "Kael"}, "baseline": {}, "current": {"vault": []}}
    b = acquisition.assess(applied, tags, char)

    check("belief-created", b is not None)
    check("target-actor-stamped", b.get("target_actor") == "torin")
    check("epistemic-stance-stamped", b.get("epistemic_stance") == "ignorant_of")
    check("links-contain-subject", "gold" in (b.get("links") or []))


def test_omniscience_wall_at_prompt_boundary():
    print("\n[2] The Omniscience Wall (Prompt Boundary)")
    # Kael knows the secret and knows Torin is ignorant of it
    b_kael_secret = {
        "claim": "The gold is hidden in the cellar",
        "confidence": 0.9,
        "provenance": "witnessed",
        "links": ["gold"],
    }
    b_kael_tom = {
        "claim": "The gold is hidden in the cellar",
        "confidence": 0.9,
        "provenance": "witnessed",
        "target_actor": "torin",
        "epistemic_stance": "ignorant_of",
        "links": ["gold", "torin"],
    }

    # Torin has a genuine, non-empty vault with unrelated beliefs
    b_torin_normal = {
        "claim": "Gold is heavy to carry on foot",
        "confidence": 0.85,
        "provenance": "lived",
        "links": ["gold"],
    }
    vault_torin = [b_torin_normal]

    triggers = ["gold"]
    cond = {"energy": 1.0, "allostatic_load": 0.0}

    # Gate retrieval for Torin
    recalled_torin = run_gate(triggers, vault_torin, {}, [], cond)
    check("torin-recalls-his-own-belief", any(r["claim"] == b_torin_normal["claim"] for r in recalled_torin))
    check("torin-does-not-recall-secret", not any("cellar" in r["claim"] for r in recalled_torin))

    # Assemble Torin's prompt
    packet_torin = {
        "stable": {"persona": {"id": "torin", "name": "Torin", "role": "scout", "voice": "quiet", "drives": ["duty"]}},
        "volatile": {
            "goals": [],
            "percepts": [{"ref": "p.1", "channel": "visual", "attributes": ["Torin stands by the fire with gold coins in his hand"], "fidelity": 0.9}],
            "recall": recalled_torin,
            "edges": [],
            "state": _STATE,
        },
        "moment": "Torin inspects his supplies",
    }
    temperament = _TEMPERAMENT
    msgs_torin = prompt.build_turn_messages(packet_torin, "Torin inspects his supplies", temperament)
    prompt_str_torin = str(msgs_torin)

    check("prompt-contains-torin-belief", "Gold is heavy" in prompt_str_torin)
    check("omniscience-wall-zero-secret-in-torin-prompt", "cellar" not in prompt_str_torin)


def test_positive_second_order_prompt_rendering():
    print("\n[3] Positive Second-Order Prompt Rendering")
    b_kael_tom = {
        "claim": "The gold is hidden in the cellar",
        "confidence": 0.9,
        "provenance": "witnessed",
        "target_actor": "torin",
        "epistemic_stance": "ignorant_of",
        "links": ["gold", "torin"],
    }
    recalled_kael = run_gate(["gold", "torin"], [b_kael_tom], {}, [], {"energy": 1.0, "allostatic_load": 0.0})

    packet_kael = {
        "stable": {"persona": {"id": "kael", "name": "Kael", "role": "tracker", "voice": "dry", "drives": ["caution"]}},
        "volatile": {
            "goals": [],
            "percepts": [{"ref": "p.1", "channel": "visual", "attributes": ["Kael watches Torin near the table"], "fidelity": 0.9}],
            "recall": recalled_kael,
            "edges": [],
            "state": _STATE,
        },
        "moment": "Kael decides what to say",
    }
    temperament = _TEMPERAMENT
    msgs_kael = prompt.build_turn_messages(packet_kael, "Kael decides what to say", temperament)
    prompt_str_kael = str(msgs_kael)

    check("kael-prompt-renders-second-order", "What others believe" in prompt_str_kael)
    check("kael-prompt-renders-torin-ignorance", "you believe torin is unaware that: The gold is hidden in the cellar" in prompt_str_kael)


def test_witness_channel_leak_prevention():
    print("\n[4] Witness Channel Leak Prevention")
    tags_deceive = {
        "summary": "The gold is in the cellar; Torin must not know",
        "public_summary": "Told Torin the wagon was ransacked",
        "durability": "durable",
        "target_actor": "torin",
        "epistemic_stance": "ignorant_of",
    }
    wb_torin = acquisition.witness_belief("Kael", tags_deceive, "kael", witness_id="torin")
    check("witness-channel-does-not-leak-secret", "cellar" not in str(wb_torin))
    check("witness-records-public-summary", "wagon was ransacked" in wb_torin["claim"])

    tags_secret = {
        "summary": "Found the secret cache in the cellar",
        "durability": "durable",
        "target_actor": "torin",
        "epistemic_stance": "ignorant_of",
    }
    wb_torin_secret = acquisition.witness_belief("Kael", tags_secret, "kael", witness_id="torin")
    check("secret-action-drops-witness-belief-for-ignorant-actor", wb_torin_secret is None)

    # deceived_about stance: target actor must NEVER receive secret summary
    tags_deceive_with_public = {
        "summary": "The gold is hidden in the cellar",
        "public_summary": "Told Torin the wagon was ransacked",
        "durability": "durable",
        "target_actor": "torin",
        "epistemic_stance": "deceived_about",
    }
    wb_torin_dec = acquisition.witness_belief("Kael", tags_deceive_with_public, "kael", witness_id="torin")
    check("deceived-about-does-not-leak-secret", "cellar" not in str(wb_torin_dec))
    check("deceived-about-records-public-summary", "wagon was ransacked" in wb_torin_dec["claim"])

    tags_deceive_no_public = {
        "summary": "The gold is hidden in the cellar",
        "durability": "durable",
        "target_actor": "torin",
        "epistemic_stance": "deceived_about",
    }
    wb_torin_dec_nopub = acquisition.witness_belief("Kael", tags_deceive_no_public, "kael", witness_id="torin")
    check("deceived-about-without-public-summary-yields-none", wb_torin_dec_nopub is None)

    wb_maren = acquisition.witness_belief("Kael", tags_deceive_no_public, "kael", witness_id="maren")
    check("non-target-bystander-receives-secret-action-belief", wb_maren is not None and "cellar" in wb_maren["claim"])


def test_bystander_propagation_cast_ordering():
    print("\n[5] Bystander Propagation Cast-Ordering Invariance")
    # Tags representing an action that Torin is blind to (no public summary)
    tags = {
        "summary": "Kael hid the sapphire in the chest",
        "durability": "durable",
        "target_actor": "torin",
        "epistemic_stance": "ignorant_of",
    }

    # Simulate bystander loop for two different cast orderings
    for order_name, present in [("torin-first", ["torin", "maren"]), ("maren-first", ["maren", "torin"])]:
        received = {}
        for wid in present:
            wb = acquisition.witness_belief("Kael", tags, "kael", trust=0.8, world={}, witness_id=wid)
            if not wb:
                continue
            received[wid] = wb

        check(f"ordering-{order_name}-torin-gets-nothing", "torin" not in received)
        check(f"ordering-{order_name}-maren-gets-belief", "maren" in received and "sapphire" in received["maren"]["claim"])


def test_supersession_partitioned_by_depth():
    print("\n[6] Supersession Partitioned by Depth")
    b_tom = {
        "claim": "The pass is safe for travel",
        "confidence": 0.8,
        "provenance": "lived",
        "links": ["pass"],
        "target_actor": "torin",
        "epistemic_stance": "believes",
    }
    char = {"fixed": {"name": "Kael"}, "baseline": {}, "current": {"vault": [b_tom]}}

    # Kael discovers first-order reality: the pass is not safe
    b_reality = acquisition.assess(
        {"target": "pass"},
        {"summary": "The pass is not safe for travel", "confidence": 0.9, "durability": "durable"},
        char
    )
    check("first-order-reality-does-not-supersede-second-order", b_reality.get("supersedes") is None)

    # Negative control: single-word substring "pass" must NOT supersede b_tom on a non-contradictory event
    b_loose = acquisition.assess(
        {"target": "pass"},
        {"summary": "The pass has many stones on the trail", "confidence": 0.9, "durability": "durable",
         "target_actor": "torin", "epistemic_stance": "believes", "supersedes": "pass"},
        char
    )
    check("single-word-supersedes-does-not-retire-belief", not b_loose.get("supersedes"))

    # Kael updates his model of Torin with exact claim
    b_tom_update = acquisition.assess(
        {"target": "pass"},
        {"summary": "The pass is not safe for travel", "confidence": 0.9, "durability": "durable",
         "target_actor": "torin", "epistemic_stance": "believes", "supersedes": "The pass is safe for travel"},
        char
    )
    check("second-order-update-supersedes-matching-target", b_tom_update.get("supersedes") == [belief_id(b_tom)])


def test_substring_contradiction_hardening():
    print("\n[7] Substring Contradiction Hardening")
    c1 = "The bridge is not far"
    c2 = "The gold is in the cellar"
    check("unrelated-is-not-does-not-contradict", not acquisition.detect_contradiction(c1, c2))

    c3 = "The bridge is far"
    check("related-is-not-does-contradict", acquisition.detect_contradiction(c1, c3))


if __name__ == "__main__":
    test_epistemic_attribution_schema()
    test_omniscience_wall_at_prompt_boundary()
    test_positive_second_order_prompt_rendering()
    test_witness_channel_leak_prevention()
    test_bystander_propagation_cast_ordering()
    test_supersession_partitioned_by_depth()
    test_substring_contradiction_hardening()
    print("\n" + "-" * 50)
    print(f"{len(PASS)} passed, {len(FAIL)} failed")
    sys.exit(1 if FAIL else 0)
