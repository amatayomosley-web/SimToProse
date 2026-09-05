#!/usr/bin/env python3
"""test_belief_revision.py — Track 1: Belief Contradiction & Revision (The Supersession Operator).

Proves:
  1. detect_contradiction identifies antonym and negation polarities with word boundaries.
  2. assess() handles explicit supersession via tags['supersedes'] without mutating caller's vault.
  3. assess() automatically detects polarity contradictions on the same subject.
  4. gate.run_gate() suppresses superseded beliefs from active recall.
  5. fold_vault() replays supersessions accurately across append-only ledger acquisitions.
Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import acquisition
from src.engine.gate import run_gate, belief_id
from src.engine.ledger import Ledger

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  -- " + detail) if (detail and not cond) else ""))


def test_contradiction_detection():
    print("\n[1] detect_contradiction")
    check("alive-dead", acquisition.detect_contradiction("Corin is alive in the north", "Corin is dead"))
    check("loyal-traitor", acquisition.detect_contradiction("Maren is a traitor to the watch", "Maren is loyal"))
    check("negation-is-not", acquisition.detect_contradiction("The draft slip is not valid", "The draft slip is valid"))
    check("negation-has-no", acquisition.detect_contradiction("The chest has no gold", "The chest has gold"))
    check("unrelated-no-contradiction", not acquisition.detect_contradiction("Corin wears green wool", "Corin carries a sword"))
    # Word boundary checks to prevent substring false positives
    check("non-contradiction-unsafe", not acquisition.detect_contradiction("the road is unsafe", "there is danger ahead"))
    check("non-contradiction-wonderful", not acquisition.detect_contradiction("she is a wonderful cook", "the wager was lost"))


def test_explicit_supersession():
    print("\n[2] assess -- explicit supersession")
    old_b = {"claim": "The northern pass is open to carts", "confidence": 0.9,
             "provenance": "lived", "believed_value": True, "links": ["north_pass"]}
    char = {"fixed": {"name": "Kael"}, "baseline": {}, "current": {"vault": [old_b]}}
    old_bid = belief_id(old_b)

    applied = {"target": "north_pass"}
    tags = {"summary": "The northern pass is blocked by rockfall", "durability": "durable",
            "confidence": 0.95, "supersedes": "The northern pass is open to carts"}

    new_b = acquisition.assess(applied, tags, char)
    check("promotes-new-belief", new_b is not None and new_b["claim"] == tags["summary"])
    check("marks-new-supersedes-list", new_b.get("supersedes") == [old_bid])
    # Purity: assess() does NOT mutate the caller's vault in-place
    check("assess-is-pure-no-mutation", "status" not in old_b)

    # Negative control: loose single-word or substring must NOT supersede
    tags_loose = {"summary": "The northern pass is blocked by rockfall", "durability": "durable",
                  "confidence": 0.95, "supersedes": "pass"}
    new_b_loose = acquisition.assess(applied, tags_loose, char)
    check("loose-substring-supersedes-does-not-retire-belief",
          new_b_loose is not None and not new_b_loose.get("supersedes"))

    # Explicit belief ID supersession
    tags_by_id = {"summary": "The northern pass is blocked by rockfall", "durability": "durable",
                  "confidence": 0.95, "supersedes": old_bid}
    new_b_by_id = acquisition.assess(applied, tags_by_id, char)
    check("explicit-bid-supersedes-retires-belief",
          new_b_by_id is not None and new_b_by_id.get("supersedes") == [old_bid])

    folded = acquisition.fold_vault([old_b, new_b])
    check("fold-marks-old-belief-superseded", folded[0].get("status") == "superseded")
    check("fold-links-old-to-new-bid", folded[0].get("superseded_by") == belief_id(new_b))


def test_automatic_polarity_supersession():
    print("\n[3] assess -- automatic contradiction detection on same subject")
    old_b = {"claim": "Torin is alive and hiding at the mill", "confidence": 0.8,
             "provenance": "lived", "believed_value": True, "links": ["torin"]}
    char = {"fixed": {"name": "Kael"}, "baseline": {}, "current": {"vault": [old_b]}}
    old_bid = belief_id(old_b)

    applied = {"target": "torin"}
    tags = {"summary": "Torin was confirmed dead by the river patrol", "durability": "durable",
            "confidence": 0.9}

    new_b = acquisition.assess(applied, tags, char)
    check("auto-detects-subject-contradiction", new_b is not None)
    check("supersedes-target-recorded", new_b.get("supersedes") == [old_bid])
    check("assess-is-pure", "status" not in old_b)

    folded = acquisition.fold_vault([old_b, new_b])
    check("fold-prior-belief-marked-superseded", folded[0].get("status") == "superseded")


def test_gate_suppression():
    print("\n[4] gate.run_gate -- suppression of superseded beliefs")
    b_old = {"claim": "Torin is alive", "confidence": 0.8, "status": "superseded", "links": ["torin"]}
    b_new = {"claim": "Torin is dead", "confidence": 0.9, "status": "active", "links": ["torin"]}
    vault = [b_old, b_new]
    triggers = ["torin"]
    recalled = run_gate(triggers, vault, {}, [], {"energy": 1.0, "allostatic_load": 0.0})

    check("only-one-recalled", len(recalled) == 1)
    check("active-belief-surfaces", recalled[0]["claim"] == "Torin is dead")
    check("superseded-suppressed", not any(r["claim"] == "Torin is alive" for r in recalled))


def test_fold_vault_and_ledger_replay():
    print("\n[5] fold_vault and Ledger persistence round-trip")
    tmp_db = os.path.join(tempfile.mkdtemp(), "test_rev.db")
    led = Ledger(tmp_db)
    led.create_run("r1", {"catalog_version": "v1"})

    b1 = {"claim": "The vault door is locked", "confidence": 0.9, "provenance": "lived", "links": ["vault"]}
    b1_id = belief_id(b1)
    b2 = {"claim": "The vault door was forced open", "confidence": 0.95, "provenance": "lived",
          "links": ["vault"], "supersedes": [b1_id]}

    led.append_acquisition("r1", "kael", 1, b1)
    led.append_acquisition("r1", "kael", 2, b2)

    replayed = led.acquisitions_for("r1", "kael")
    check("two-rows-persisted-append-only", len(replayed) == 2)

    folded = acquisition.fold_vault(replayed)
    check("b1-status-folded-to-superseded", folded[0].get("status") == "superseded")
    check("b1-superseded-by-b2", folded[0].get("superseded_by") == belief_id(b2))
    check("b2-status-active", folded[1].get("status") == "active")


if __name__ == "__main__":
    test_contradiction_detection()
    test_explicit_supersession()
    test_automatic_polarity_supersession()
    test_gate_suppression()
    test_fold_vault_and_ledger_replay()
    print("\n" + "-" * 50)
    print("%d passed, %d failed" % (len(PASS), len(FAIL)))
    sys.exit(1 if FAIL else 0)
