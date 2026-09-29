#!/usr/bin/env python3
"""test_recall_about.py — recall meets a belief by its WORDS or by what it is ABOUT (gate knowledge-about-index).

The recall matcher (`associative.find_associative_candidates`, step 1) used to match a trigger by raw substring over
a belief's claim and links, and never read `about`. So 'low' qualified a belief about the Hollow and 'out' one that
says "about" - the accidents `facets.py` closed at the WRITE on 2026-08-30 and the MATCH kept making - while a belief
stamped as about a person the character recognizes, but saying "he", was no direct candidate. And the graph anchored
a namespaced or multi-word referent ("loc.millbrook", "old_man") under a spelling no trigger ever has.

Proves, through `gate.run_gate` (the one caller, from `scene.assemble`):
  [1] the substring accidents are closed, and the real word still matches (the control);
  [2] a single word meets its plural either way;
  [3] a belief is reached through what it is ABOUT - the knower's referent - when the prose never names them;
  [4] a namespaced or multi-word referent meets its trigger, directly and as a stepping stone;
  [5] two identities are two ids and stay apart (a beekeeper and the basket-seller she also is are joined by a
      fact that someone holds - tests/test_identity.py - never by the matcher).
Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.gate import run_gate  # noqa: E402

PASS, FAIL = [], []
RESTED = {"energy": 1.0, "allostatic_load": 0.0}


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  -- " + str(detail)) if (detail and not cond) else ""))


def recall(triggers, vault):
    return run_gate(list(triggers), vault, {}, [], RESTED)


def claims(got):
    return [r["claim"] for r in got]


def test_the_accidents_are_closed():
    print("\n[1] a trigger meets a WORD, never the inside of one")
    hollow = {"claim": "The Hollow goes short every winter.", "confidence": 0.8, "provenance": "lived"}
    mill = {"claim": "She talked about the mill all night.", "confidence": 0.8, "provenance": "lived"}
    check("'low' does not qualify a belief about the Hollow", recall(["low"], [hollow]) == [], claims(recall(["low"], [hollow])))
    check("'out' does not qualify a belief that says 'about'", recall(["out"], [mill]) == [], claims(recall(["out"], [mill])))
    check("control: 'hollow' still reaches it", claims(recall(["hollow"], [hollow])) == [hollow["claim"]])
    check("control: 'mill' still reaches it", claims(recall(["mill"], [mill])) == [mill["claim"]])


def test_plurals_meet():
    print("\n[2] a single word meets its plural either way")
    many = {"claim": "The hunters came down at dusk.", "confidence": 0.8, "provenance": "lived"}
    one = {"claim": "A hunter sleeps by the gate.", "confidence": 0.8, "provenance": "lived"}
    check("'hunter' reaches 'hunters'", claims(recall(["hunter"], [many])) == [many["claim"]])
    check("'hunters' reaches 'hunter'", claims(recall(["hunters"], [one])) == [one["claim"]])


def test_about_reaches_what_the_prose_does_not_name():
    print("\n[3] what a belief is ABOUT reaches it (the knower's referent), exactly as naming them does")
    hill = {"claim": "He will come up that hill one day.", "confidence": 0.8, "provenance": "lived", "about": ["tam"]}
    got = recall(["tam"], [hill])
    check("recognizing tam reaches the belief that says 'he'", claims(got) == [hill["claim"]], claims(got))
    check("someone else recognized does not reach it", recall(["nell"], [hill]) == [])
    # Rested, the graph already reached it (its `about` is an anchor). Exhausted, the traversal does not run, and only
    # direct candidates can fire - so a certain belief that NAMES tam surfaced and the same belief saying "he" did not.
    spent = {"energy": 0.0, "allostatic_load": 1.0}
    named = {"claim": "Tam will come up that hill one day.", "confidence": 1.0, "provenance": "lived", "about": ["tam"]}
    said_he = dict(hill, confidence=1.0)
    check("control: exhausted, the certain belief that names tam surfaces",
          claims(run_gate(["tam"], [named], {}, [], spent)) == [named["claim"]])
    got = run_gate(["tam"], [said_he], {}, [], spent)
    check("exhausted, the same belief saying 'he' surfaces too (it is about him)", claims(got) == [said_he["claim"]],
          claims(got))


def test_namespaced_and_multiword_referents_meet_their_triggers():
    print("\n[4] 'loc.millbrook' meets 'millbrook'; 'old_man' meets 'old man'")
    sheriff = {"claim": "The sheriff keeps the peace.", "confidence": 0.8, "provenance": "known in Millbrook",
               "about": ["loc.millbrook", "ambrose"]}
    check("a fact about loc.millbrook is reached by 'millbrook'", claims(recall(["millbrook"], [sheriff])) == [sheriff["claim"]])
    fixed = {"claim": "He fixed the wheel for us once.", "confidence": 0.8, "provenance": "lived",
             "about": ["old_man"], "links": ["wheel"]}
    oak = {"claim": "The wheel was cut from the black oak.", "confidence": 0.8, "provenance": "lived",
           "links": ["wheel", "black_oak"]}
    got = recall(["old man"], [fixed, oak])
    check("the recognized old man reaches what is about him", fixed["claim"] in claims(got), claims(got))
    step = [r for r in got if r["claim"] == oak["claim"]]
    check("...and, through it, the wheel's other belief as a leap", bool(step) and step[0].get("hops", 1) >= 2, got)


def test_two_identities_stay_apart():
    print("\n[5] two identities are two ids (the equivalence is a fact of its own, not a join here)")
    seller = {"claim": "Brisk weaves the tightest baskets in the valley.", "confidence": 0.8,
              "provenance": "seen at the market", "about": ["brisk"]}
    keeper = {"claim": "Maudie keeps twelve hives on the south slope.", "confidence": 0.8, "provenance": "lived",
              "about": ["maudie"]}
    got = recall(["maudie"], [seller, keeper])
    check("the beekeeper reaches only what is about the beekeeper", claims(got) == [keeper["claim"]], claims(got))


if __name__ == "__main__":
    print("test_recall_about.py - recall meets a belief by its words or by what it is about")
    for t in (test_the_accidents_are_closed, test_plurals_meet, test_about_reaches_what_the_prose_does_not_name,
              test_namespaced_and_multiword_referents_meet_their_triggers, test_two_identities_stay_apart):
        t()
    print("\n" + "-" * 50)
    print("%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)
