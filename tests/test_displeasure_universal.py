#!/usr/bin/env python3
"""test_displeasure_universal.py — Automated verification of the 12 DISPLEASURE blocks.

Asserts:
1. Block structure: Opening, The Sensation, The Belief (with italic anchor), The Impulse.
2. Zero smuggled targets / human-only constraints in floor rungs (no 'person now rather than a thing').
3. Zero brawler posturing or strike constraints (no 'balls of feet', no 'cannot strike', no 'with your hands').
4. Zero smuggled speech mandates (no 'in your voice', no 'asking was not enough').
5. Full float coverage and clean retrieval across all 12 rungs.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import rungs
from src.engine.rung_blocks import BANDS

def test_structural_invariants():
    print("[1] VERIFYING 4-PART STRUCTURAL INVARIANTS ACROSS ALL 12 RUNGS")
    for i in range(1, 13):
        block = rungs.block_for('DISPLEASURE', i)
        assert len(block.strip()) > 50, f"Rung {i} block is too short"
        assert "- **The Sensation.**" in block, f"Rung {i} missing Sensation bullet"
        assert "- **The Belief.**" in block, f"Rung {i} missing Belief bullet"
        assert "- **The Impulse.**" in block, f"Rung {i} missing Impulse bullet"
        assert re.search(r"\*[^*]+\*\.?$", block, re.MULTILINE), f"Rung {i} missing italicized Belief anchor"
        print(f"  PASS  Rung {i:02d} structure complete")

def test_zero_smuggled_human_cause_and_dialogue():
    print("\n[2] VERIFYING TARGET-AGNOSTICISM & ZERO SMUGGLED INTERPERSONAL MANDATES")
    forbidden_human = [
        ("person now rather than a thing", "forces human cause on non-human events"),
        ("asking was not enough", "smuggles prior verbal conversation"),
        ("say it plainly to whoever", "forces presence of an interlocutor"),
        ("in your voice and in what you say", "forces verbal dialogue channel"),
        ("defending it counts double", "forces interpersonal debate exchange"),
        ("not letting the exchange go", "forces interpersonal debate exchange"),
        ("them coming off it", "assumes interpersonal human cause")
    ]
    for i in range(1, 13):
        text = rungs.block_for('DISPLEASURE', i).lower()
        for phrase, reason in forbidden_human:
            assert phrase not in text, f'Rung {i} violates target-agnosticism ({reason}): found "{phrase}"'
        print(f"  PASS  Rung {i:02d} free of smuggled human-only staging")

def test_zero_brawler_combat_assumptions():
    print("\n[3] VERIFYING POSTURAL AGNOSTICISM & ZERO BRAWLER ASSUMPTIONS")
    forbidden_brawler = [
        ("balls of your feet", "assumes standing brawler stance"),
        ("cannot strike", "assumes brawler punch is the default impulse"),
        ("with your hands or with whatever", "forces hand-to-hand fist combat"),
        ("strike at them", "forces physical blow action")
    ]
    for i in range(1, 13):
        text = rungs.block_for('DISPLEASURE', i).lower()
        for phrase, reason in forbidden_brawler:
            assert phrase not in text, f'Rung {i} violates postural agnosticism ({reason}): found "{phrase}"'
        print(f"  PASS  Rung {i:02d} free of brawler combat tropes")

def test_monotonic_resolution():
    print("\n[4] VERIFYING FLOAT RESOLUTION COVERS 0.0 TO 1.0")
    seen = []
    step = 0.01
    v = 0.0
    while v <= 1.0:
        idx, name = rungs.rung_at('DISPLEASURE', v)
        if not seen or seen[-1] != idx:
            seen.append(idx)
        v = round(v + step, 4)
    assert seen == list(range(1, 13)), f"Did not resolve every rung in order: {seen}"
    print(f"  PASS  All 12 rungs resolved monotonically across 0.0..1.0")

if __name__ == "__main__":
    test_structural_invariants()
    test_zero_smuggled_human_cause_and_dialogue()
    test_zero_brawler_combat_assumptions()
    test_monotonic_resolution()
    print("\nALL DISPLEASURE UNIVERSAL INVARIANT TESTS PASSED (4/4 test suites clean).")
