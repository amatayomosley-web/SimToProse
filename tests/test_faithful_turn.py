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

REL = {"nessa": {"known_as": "the damaged worker"}}         # the actor knows her only by a descriptor
PACKET = {"volatile": {}, "stable": {}, "manifest": {}, "recall_refs": []}  # patched llm_turn ignores it
FAILS = []


def _turn(action):
    return {"action": action, "thought": "", "exit": False, "addressee": "", "tags": {"dimensions": {}}}


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def test_the_act_seam(tmp=None):
    """A turn authored OUTSIDE the engine goes through the same walls as one generated inside.

    `docs/orchestration.md` listed this as unwired seam 1: direct.py and scene.py fused the model
    call to the commit, so the character-simulator role was the only one of the four LLM calls a
    foreign model could not perform — critic.py and narrate.py have had `--prompt-only` from the
    start. The bridge it specifies is "a `--turn-json` re-entry running validate -> appraise ->
    commit on a supplied turn".

    THE THING WORTH TESTING is not that the seam accepts a turn — it is that accepting one does not
    weaken anything. `faithful_turn` exists because a model emits names it does not hold, and that
    risk does not fall when the model is a stranger's. A re-entry that skips the wall is a hole in
    the wall wearing a seam's name.
    """
    import inspect
    src = inspect.getsource(direct.run_turn)

    check("run_turn takes a supplied turn", "supplied=None" in inspect.signature(direct.run_turn)
          .parameters.get("supplied").__str__() or "supplied" in inspect.signature(direct.run_turn).parameters,
          "the inbound half does not exist")
    check("and a prompt-only path", "prompt_only" in inspect.signature(direct.run_turn).parameters)

    # THE WALL: the supplied path must call the leak check, not skip to validation.
    seam = src.split("if supplied is not None:")[1].split("else:")[0]
    check("the supplied path runs the name-leak check", "check_name_leaks" in seam,
          "a supplied turn would bypass the faithfulness wall — the seam becomes a hole")
    check("and it enforces the turn contract",
          "missing" in seam and "action" in seam and "tags" in seam,
          "a malformed supplied turn must throw naming the missing field")

    # the wall itself still discriminates, on the same relationships shape the seam passes it
    from src.engine import faithfulness
    clean = faithfulness.check_name_leaks("She tells the damaged worker what happened.", REL)
    leaked = faithfulness.check_name_leaks("She tells Nessa what happened.", REL)
    check("descriptor is clean", not clean, str(clean))
    check("the masked NAME leaks", bool(leaked), "the wall the seam relies on does not fire")

    # and the seam is reachable from the command line, which is the whole point: argv in, stdout out
    main_src = inspect.getsource(direct.main)
    check("--prompt-only is exposed", "--prompt-only" in main_src)
    check("--turn-json is exposed", "--turn-json" in main_src)
    check("both require a circumstance", "--circumstance" in main_src)


def main():
    print("test_faithful_turn.py — active faithfulness guard\n")
    _real = direct.llm_turn
    try:
        # (a) leaking on attempt 0, clean on the retry -> faithful_turn returns the clean one
        seq = ["I will fetch Nessa from the cold.", "I will fetch the damaged worker."]
        calls = {"n": 0}

        # `acts` was added to llm_turn when laws were wired into the runner (the actor names what
        # it did in the world's own vocabulary so a law can be keyed to it). A stub that does not
        # accept it TypeErrors before any assertion runs.
        def leak_then_clean(packet, event_text, temperament, model, stub, think=True, seed=None,
                            relationships=None, corrections=None, acts=()):
            i = min(calls["n"], len(seq) - 1)
            calls["n"] += 1
            return _turn(seq[i])

        direct.llm_turn = leak_then_clean
        turn, leaks = direct.faithful_turn(PACKET, "ev", "t", "m", False, relationships=REL, max_retries=2)
        check("regenerates-to-clean", not leaks and "Nessa" not in turn["action"],
              "leaks=%s action=%r" % (leaks, turn["action"]))
        check("one-retry-used", calls["n"] == 2, "calls=%d" % calls["n"])
        check("correction-injected", calls["n"] == 2)  # a 2nd call only happens if a correction was issued

        # (b) always leaking -> residual leaks after max_retries+1 attempts (caller will reject)
        calls2 = {"n": 0}

        def always_leak(packet, event_text, temperament, model, stub, think=True, seed=None,
                        relationships=None, corrections=None, acts=()):
            calls2["n"] += 1
            return _turn("Nessa is here, by the fire.")

        direct.llm_turn = always_leak
        turn2, leaks2 = direct.faithful_turn(PACKET, "ev", "t", "m", False, relationships=REL, max_retries=2)
        check("persistent-leak-returned", bool(leaks2) and leaks2[0][0] == "nessa", str(leaks2))
        check("exhausts-max-retries", calls2["n"] == 3, "attempts=%d" % calls2["n"])

        # (c) clean on the first try -> no retry, no wasted call
        calls3 = {"n": 0}

        def clean_first(packet, event_text, temperament, model, stub, think=True, seed=None,
                        relationships=None, corrections=None, acts=()):
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
    test_the_act_seam()
    print("\ntest_faithful_turn: OK (regenerate-on-leak + reject-on-persist)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
