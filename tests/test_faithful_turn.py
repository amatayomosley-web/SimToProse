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



def test_the_wall_is_FACT_shaped_too(tmp=None):
    """The wall masked names and nothing else. It would catch "Aldric" where the character
    knows only "the man from the docks", and miss "the man from the docks is here" when the
    character should not know he is from the docks at all. Not every secret is a name.

    Four cases, and the third is the one that keeps the guard from being a nuisance."""
    from src.engine.faithfulness import check_fact_leaks
    info = {"the fever will not break": ["edda"], "the well is poisoned": ["maren", "edda"]}

    # 1. a non-knower stating a tracked fact is a LEAK
    got = check_fact_leaks("She said the fever will not break by dawn.", "maren", info)
    check("a-non-knower-stating-a-tracked-fact-LEAKS", len(got) == 1, str(got))
    check("and-the-report-names-who-DOES-know", got and got[0][1] == ["edda"], str(got))

    # 2. a knower stating the same fact is CLEAN — the guard must not gag people who were told
    check("a-knower-stating-it-is-clean",
          check_fact_leaks("The well is poisoned.", "maren", info) == [], "gagged a knower")

    # 3. an empty or absent registry is a no-op, so every pre-2026-09-01 caller is unchanged
    check("an-empty-registry-is-a-NO-OP", check_fact_leaks("anything at all", "maren", {}) == [])
    check("and-so-is-a-missing-one", check_fact_leaks("anything at all", "maren", None) == [])

    # 4. WHAT IT MISSES, asserted so the limit is documented by the suite and not only by a
    #    docstring: a paraphrase escapes. This is a floor, not a ceiling, and a future reader
    #    should find the gap named rather than discover it in a book.
    check("a-PARAPHRASE-escapes-and-that-is-known",
          check_fact_leaks("She is lying about the fever.", "maren", info) == [],
          "if this now passes, the matcher changed and the docstring must be updated too")


def test_faithful_turn_REGENERATES_on_a_fact_leak(tmp=None):
    """The wiring, not just the detector. A fact leak must drive the same discard-and-retry
    the name case drives — design.md says recorded as-is, never edited."""
    _real = direct.llm_turn
    info = {"the fever will not break": ["edda"]}
    try:
        seq = ["She knows the fever will not break.", "She sets the cup down and says nothing."]
        calls = {"n": 0}

        def leak_then_clean(packet, event_text, temperament, model, stub, think=True, seed=None,
                            relationships=None, corrections=None, acts=()):
            i = min(calls["n"], len(seq) - 1)
            calls["n"] += 1
            calls["last"] = corrections
            return _turn(seq[i])

        direct.llm_turn = leak_then_clean
        turn, leaks = direct.faithful_turn(PACKET, "ev", "t", "m", False, relationships=REL,
                                           information=info, char_id="maren", max_retries=2)
        check("a-fact-leak-is-REGENERATED", not leaks and calls["n"] == 2,
              "leaks=%r calls=%r" % (leaks, calls["n"]))
        check("the-correction-names-the-fact",
              calls.get("last") and any("fever will not break" in c["content"]
                                        for c in calls["last"]), str(calls.get("last")))

        # and a knower saying the same thing is never corrected at all
        calls["n"] = 0
        turn, leaks = direct.faithful_turn(PACKET, "ev", "t", "m", False, relationships=REL,
                                           information=info, char_id="edda", max_retries=2)
        check("a-knower-is-not-corrected", not leaks and calls["n"] == 1,
              "leaks=%r calls=%r" % (leaks, calls["n"]))
    finally:
        direct.llm_turn = _real



def test_BOTH_drivers_refuse_an_empty_draw(tmp=None):
    """Same rule in both drivers or it is not a rule.

    `scene.py` refuses an action that stayed empty through every resample and records turn-skipped.
    `direct.py` did not — so in the chair an empty draw COMMITTED as a real turn: a beat in the
    chronicle where nothing happened, indistinguishable later from one where nothing was meant to.
    Checked against the source of both, because the behaviour is a branch, not a return value."""
    import os
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("scene.py", "direct.py"):
        src = open(os.path.join(repo, "scripts", name), encoding="utf-8").read()
        check("%s-refuses-an-empty-draw" % name,
              "empty turn (no action after retries)" in src,
              "an empty action commits as a real turn in %s" % name)


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

    # EVERY test_ FUNCTION, AND THE CHECK COMES LAST. `test_the_act_seam()` used to be called
    # AFTER the FAILS block returned, so anything it appended to FAILS was printed as a line and
    # never failed the suite — a check whose result is discarded. Discovered now, so a test added
    # to this file cannot be forgotten either: the same defect found in test_scene.py on 2026-09-01.
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()

    if FAILS:
        print("\ntest_faithful_turn: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_faithful_turn: OK (regenerate-on-leak + reject-on-persist + the fact-shaped wall)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
