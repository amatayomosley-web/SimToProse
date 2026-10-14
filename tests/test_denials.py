#!/usr/bin/env python3
"""test_denials.py — a line that denies what its speaker knows (gate denial-check, 2026-10-13).

The engine guarded the LEAK direction only: `faithfulness.check_fact_leaks` flags a character stating a fact they do
not hold. The owner's case runs the other way: a tale saved for town X, then a character from town X written as never
having heard of it. `check_fact_denials` flags a sentence that both DENIES (a closed list of denial phrases) and NAMES
the subject of a fact the speaker holds - a person, place or group the fact is about, or a word of its topic.

The limit, asserted here so nobody reads it as more: a vague denial that names nothing ("I know nothing of that") does
not match, and a paraphrased subject escapes. Word matching does not read meaning; placing the person in their bands
(scripts/place.py) is the real guard, and this only catches the plain case. Invented fixture.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import faithfulness                                # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


BELL = "The drowned bell rings before a flood."
WORLD = {"locations": [{"id": "saltmarsh", "name": "Saltmarsh"}],
         "people": [{"id": "maud_tern", "name": "Maud Tern", "what": "the bell-keeper"}],
         "lexicon": {"attribute_classes": {"folklore": ["tale", "tales", "folktale", "folktales", "legend"]}}}
VAULT = [
    {"claim": BELL, "shared": "grp.saltmarsh-folk", "links": ["saltmarsh", "folklore", "saltmarsh-folk"],
     "about": ["saltmarsh"], "topic": "folklore"},
    {"claim": "Maud Tern keeps the bell tower.", "shared": "loc.saltmarsh", "links": ["maud_tern"], "about": ["maud_tern"]},
    {"claim": "I fell in the river as a boy.", "provenance": "lived", "links": ["saltmarsh"]},
]


def test_wiring():
    """In the loop: a denial in the character's own THOUGHT is regenerated - nobody lies to themselves. A denial they
    SPEAK may be a lie, which is theirs to tell (lying is the drama layer, knowledge-model.md), so it is not corrected."""
    import direct
    real = direct.llm_turn
    calls = {"n": 0}
    seq = []

    def scripted(packet, event_text, temperament, model, stub, corrections=None, **_kw):
        i = min(calls["n"], len(seq) - 1)
        calls["n"] += 1
        calls["last"] = corrections
        return {"action": seq[i][0], "thought": seq[i][1], "exit": False, "addressee": "", "tags": {"dimensions": {}}}
    try:
        direct.llm_turn = scripted
        packet = {"volatile": {}, "stable": {}, "manifest": {}, "recall_refs": []}
        seq[:] = [("He shrugs.", "I have never heard of Saltmarsh."), ("He shrugs.", "Saltmarsh, then. Best say nothing.")]
        turn, leaks = direct.faithful_turn(packet, "ev", "t", "m", False, max_retries=2, vault=VAULT, world=WORLD)
        check("a denial in the thought is regenerated", not leaks and calls["n"] == 2, "leaks=%r calls=%r" % (leaks, calls["n"]))
        check("the correction names what he knows", calls.get("last") and any(BELL in c["content"] for c in calls["last"]),
              calls.get("last"))
        calls["n"] = 0
        seq[:] = [("'Saltmarsh? Never heard of it,' he says.", "Better they think I'm a stranger.")]
        turn, leaks = direct.faithful_turn(packet, "ev", "t", "m", False, max_retries=2, vault=VAULT, world=WORLD)
        check("a denial he speaks is his to tell (a lie), not corrected", not leaks and calls["n"] == 1,
              "leaks=%r calls=%r" % (leaks, calls["n"]))
        calls["n"] = 0
        seq[:] = [("He shrugs.", "I have never heard of Saltmarsh.")]
        turn, leaks = direct.faithful_turn(packet, "ev", "t", "m", False, max_retries=1)
        check("no vault passed: the check is a no-op (every caller before this gate)", not leaks and calls["n"] == 1)
    finally:
        direct.llm_turn = real


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    print("test_denials")
    f = getattr(faithfulness, "check_fact_denials", None)
    check("faithfulness.check_fact_denials exists", callable(f))
    if not callable(f):
        print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
        sys.exit(1)
    got = f("I've never heard of any folktales, sir.", VAULT, WORLD)
    check("denying the topic of a held fact is flagged", any(g[1] == BELL for g in got), got)
    got = f("Maud Tern? I don't know her.", VAULT, WORLD)
    check("denying a person a held fact is about is flagged (her name, as the world writes it)",
          any(g[0] == "Maud Tern" for g in got), got)
    got = f("Saltmarsh? Never heard of it.", VAULT, WORLD)
    check("denying a place a held fact is about is flagged", any(g[0] == "Saltmarsh" for g in got), got)
    check("each finding carries the sentence it read", got and "Never heard of it" in got[0][2], got)
    check("naming the subject without denying is clean", f("The folktales say the bell rings.", VAULT, WORLD) == [])
    check("not knowing WHERE someone is denies nothing about knowing them",
          f("I don't know where Maud Tern went.", VAULT, WORLD) == [])
    check("denying something else is clean", f("I don't know the ferryman's name.", VAULT, WORLD) == [])
    check("a denial in one sentence and the subject in the next is clean (the sentence is the unit)",
          f("I don't know. Saltmarsh is upriver.", VAULT, WORLD) == [])
    check("a belief that names no subject (no `about`) makes no finding",
          f("Saltmarsh? Never heard of it.", VAULT[2:], WORLD) == [])
    check("THE LIMIT: a vague denial that names nothing does not match", f("I know nothing of that.", VAULT, WORLD) == [])
    check("THE LIMIT: a paraphrased subject escapes", f("Never heard of the town on stilts.", VAULT, WORLD) == [])
    check("an empty vault or no text is a no-op", f("Never heard of Saltmarsh.", [], WORLD) == [] and f(None, VAULT, WORLD) == [])
    test_wiring()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for x in FAIL:
        print("  FAIL:", x)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
