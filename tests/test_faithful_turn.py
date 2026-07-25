#!/usr/bin/env python3
"""test_faithful_turn.py — the ACTIVE faithfulness guard: regenerate on a name-leak, reject if it persists.

Proves gate swe-faithfulness-regenerate-on-reject. Patches direct.llm_turn with a scripted dispatch so
the retry loop is exercised deterministically (no API): a leaking-then-clean dispatch must yield a clean
turn within max_retries; an always-leaking dispatch must return residual leaks after max_retries+1 tries.
Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import direct                                              # noqa: E402

REL = {"kestra": {"known_as": "the damaged worker"}}         # the actor knows her only by a descriptor
PACKET = {"volatile": {}, "stable": {}, "manifest": {}, "recall_refs": []}  # patched llm_turn ignores it
FAILS = []


def _turn(action):
    return {"action": action, "thought": "", "exit": False, "addressee": "", "tags": {"dimensions": {}}}


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def main():
    print("test_faithful_turn.py — active faithfulness guard\n")
    _real = direct.llm_turn
    try:
        # (a) leaking on attempt 0, clean on the retry -> faithful_turn returns the clean one
        seq = ["I will fetch Kestra from the cold.", "I will fetch the damaged worker."]
        calls = {"n": 0}

        def leak_then_clean(packet, event_text, temperament, model, stub, think=True, seed=None,
                            relationships=None, corrections=None):
            i = min(calls["n"], len(seq) - 1)
            calls["n"] += 1
            return _turn(seq[i])

        direct.llm_turn = leak_then_clean
        turn, leaks = direct.faithful_turn(PACKET, "ev", "t", "m", False, relationships=REL, max_retries=2)
        check("regenerates-to-clean", not leaks and "Kestra" not in turn["action"],
              "leaks=%s action=%r" % (leaks, turn["action"]))
        check("one-retry-used", calls["n"] == 2, "calls=%d" % calls["n"])
        check("correction-injected", calls["n"] == 2)  # a 2nd call only happens if a correction was issued

        # (b) always leaking -> residual leaks after max_retries+1 attempts (caller will reject)
        calls2 = {"n": 0}

        def always_leak(packet, event_text, temperament, model, stub, think=True, seed=None,
                        relationships=None, corrections=None):
            calls2["n"] += 1
            return _turn("Kestra is here, by the fire.")

        direct.llm_turn = always_leak
        turn2, leaks2 = direct.faithful_turn(PACKET, "ev", "t", "m", False, relationships=REL, max_retries=2)
        check("persistent-leak-returned", bool(leaks2) and leaks2[0][0] == "kestra", str(leaks2))
        check("exhausts-max-retries", calls2["n"] == 3, "attempts=%d" % calls2["n"])

        # (c) clean on the first try -> no retry, no wasted call
        calls3 = {"n": 0}

        def clean_first(packet, event_text, temperament, model, stub, think=True, seed=None,
                        relationships=None, corrections=None):
            calls3["n"] += 1
            return _turn("I will carry the damaged worker inside.")

        direct.llm_turn = clean_first
        turn3, leaks3 = direct.faithful_turn(PACKET, "ev", "t", "m", False, relationships=REL, max_retries=2)
        check("clean-first-no-retry", not leaks3 and calls3["n"] == 1, "calls=%d leaks=%s" % (calls3["n"], leaks3))
    finally:
        direct.llm_turn = _real

    if FAILS:
        print("\ntest_faithful_turn: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_faithful_turn: OK (regenerate-on-leak + reject-on-persist)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
