#!/usr/bin/env python3
"""test_acquisition.py — the vault grows: a durable, subject-bearing turn becomes a recallable belief.

Covers acquisition.assess (the deterministic promotion rule) + Ledger.append_acquisition /
acquisitions_for (the persistence round-trip). Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import acquisition          # noqa: E402
from src.engine.ledger import Ledger        # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  — " + detail) if (detail and not cond) else ""))


def _char(vault=None):
    return {"fixed": {"name": "Brakk"}, "baseline": {}, "current": {"vault": list(vault or [])}}


def test_assess_promotes_durable_subject_turn():
    print("\n[A] assess — durable + subject -> belief")
    applied = {"target": "kestra", "dimensions": {"care_relevant": 0.8}}
    tags = {"type": "aid", "summary": "I forced Father to send help for the worker",
            "durability": "durable", "confidence": 0.9}
    b = acquisition.assess(applied, tags, _char())
    check("durable-subject-promotes", b is not None and b["claim"] == tags["summary"], repr(b))
    check("provenance-lived", bool(b) and b.get("provenance") == "lived", repr(b))
    check("links-to-subject", bool(b) and b.get("links") == ["kestra"], repr(b))
    check("confidence-carried", bool(b) and abs(b.get("confidence", 0) - 0.9) < 1e-9, repr(b))


def test_assess_rejects():
    print("\n[B] assess — rejections")
    base = {"target": "kestra"}
    check("transient-none", acquisition.assess(base, {"summary": "I pass the salt", "durability": "transient"}, _char()) is None)
    check("no-subject-none", acquisition.assess({}, {"summary": "I brood", "durability": "durable"}, _char()) is None)
    check("no-summary-none", acquisition.assess(base, {"summary": "", "durability": "durable"}, _char()) is None)


def test_assess_dedups():
    print("\n[C] assess — dedup vs existing vault")
    applied = {"target": "kestra"}
    tags = {"summary": "I forced Father to send help", "durability": "durable", "confidence": 0.8}
    ch = _char(vault=[{"claim": "I forced Father to send help", "provenance": "lived"}])
    check("duplicate-claim-none", acquisition.assess(applied, tags, ch) is None)
    check("novel-claim-promotes", acquisition.assess(applied, tags, _char(vault=[{"claim": "something else"}])) is not None)


def test_ledger_roundtrip():
    print("\n[D] Ledger.append_acquisition / acquisitions_for")
    led = Ledger(os.path.join(tempfile.mkdtemp(), "acq.db"))
    led.create_run("r1", {"catalog_version": 1})
    led.append_acquisition("r1", "brakk", 3, {"claim": "first", "provenance": "lived", "links": ["kestra"]})
    led.append_acquisition("r1", "brakk", 5, {"claim": "second", "provenance": "lived", "links": []})
    led.append_acquisition("r1", "selven", 4, {"claim": "selven-only", "provenance": "lived", "links": []})
    got = led.acquisitions_for("r1", "brakk")
    check("brakk-gets-two", len(got) == 2, str(got))
    check("ordered-by-turn", [b["claim"] for b in got] == ["first", "second"], str(got))
    check("scoped-by-char", [b["claim"] for b in led.acquisitions_for("r1", "selven")] == ["selven-only"])


def test_reveal_name_monotonic():
    print("\n[E] reveal_name — monotonic name acquisition (old info preserved)")
    from src.engine.gate import scope_names
    ch = _char(vault=[{"claim": "I tended the damaged worker", "provenance": "lived"}])
    ch["current"]["relationships"] = {"kestra": {"trust": 0.2, "known_as": "the damaged worker"}}
    before = len(ch["current"]["vault"])
    b = acquisition.reveal_name(ch, "kestra", "Kestra")
    check("flips-known-as", ch["current"]["relationships"]["kestra"]["known_as"] == "Kestra")
    check("returns-learned-belief", bool(b) and b.get("provenance") == "learned" and "Kestra" in b.get("claim", ""), repr(b))
    check("old-belief-preserved", ch["current"]["vault"][0]["claim"] == "I tended the damaged worker")
    check("monotonic-append", len(ch["current"]["vault"]) == before + 1)
    rels = ch["current"]["relationships"]
    check("name-now-visible-to-knower", scope_names("Kestra enters", rels) == "Kestra enters",
          scope_names("Kestra enters", rels))
    check("others-still-masked", "Kestra" not in scope_names("Kestra enters", {"kestra": {"known_as": "the damaged worker"}}))
    check("no-edge-returns-none", acquisition.reveal_name(_char(), "ghost", "Boo") is None)


def test_resume_replay_data():
    print("\n[F] resume-replay — arc_diffs_for + vault rehydrate")
    led = Ledger(os.path.join(tempfile.mkdtemp(), "resume.db"))
    led.create_run("r2", {"catalog_version": 1})
    led.append_arc_diff("r2", "brakk", 2, {"temperament": {"RAGE": 0.05}, "_meta": {"dominant": "RAGE"}})
    led.append_arc_diff("r2", "brakk", 4, {"relationships": {"kestra": {"affinity": 0.1}}})
    led.append_acquisition("r2", "brakk", 3, {"claim": "learned A", "provenance": "lived"})
    led.append_acquisition("r2", "brakk", 5, {"claim": "learned B", "provenance": "lived"})
    diffs = led.arc_diffs_for("r2", "brakk")
    check("arc-diffs-two-in-order", len(diffs) == 2 and "RAGE" in diffs[0].get("temperament", {}), str(diffs))
    # the resume replay: a seed char's vault gets the acquisitions appended in order
    seed = _char(vault=[{"claim": "seed belief"}])
    seed["current"]["vault"].extend(led.acquisitions_for("r2", "brakk"))
    claims = [b["claim"] for b in seed["current"]["vault"]]
    check("vault-rehydrated-seed-plus-acquired", claims == ["seed belief", "learned A", "learned B"], str(claims))


def test_witness_belief():
    print("\n[G] witness_belief — bystander remembers a durable act")
    b = acquisition.witness_belief("Kestra", {"summary": "I covered the child with my body", "durability": "durable"}, "kestra")
    check("witnessed-deperson", bool(b) and b["claim"].startswith("Kestra covered the child"), repr(b))
    check("witnessed-provenance-links", bool(b) and b.get("provenance") == "witnessed" and b.get("links") == ["kestra"], repr(b))
    check("witness-transient-none", acquisition.witness_belief("Kestra", {"summary": "x", "durability": "transient"}, "kestra") is None)
    nonfirst = acquisition.witness_belief("Kestra", {"summary": "The cup fell", "durability": "durable"}, "kestra")
    check("witness-nonfirst-person", bool(nonfirst) and nonfirst["claim"].startswith("Kestra — as I saw it"), repr(nonfirst))


def test_faithfulness_name_leak():
    print("\n[H] faithfulness — catch a name the character does not hold")
    from src.engine import faithfulness
    rels = {"kestra": {"known_as": "the damaged worker"}}
    check("leak-detected", faithfulness.check_name_leaks("I will fetch Kestra from the cold.", rels) == [("kestra", "the damaged worker")],
          str(faithfulness.check_name_leaks("I will fetch Kestra from the cold.", rels)))
    check("descriptor-is-clean", faithfulness.check_name_leaks("I will fetch the damaged worker.", rels) == [])
    check("known-name-is-clean", faithfulness.check_name_leaks("Kestra is here", {"kestra": {"known_as": "Kestra"}}) == [])
    check("no-known_as-is-clean", faithfulness.check_name_leaks("Kestra is here", {"kestra": {"trust": 0.2}}) == [])


def test_overheard_names():
    print("\n[I] overheard_names — transmission: a bystander hears a name and learns it")
    people = [{"id": "kestra", "name": "Kestra Fenmark"}, {"id": "brakk", "name": "Brakk Wintercrest"}]
    masked = {"kestra": {"known_as": "the damaged worker"}}
    check("masked-name-overheard",
          acquisition.overheard_names("Send help for Kestra at once.", masked, people) == [("kestra", "Kestra")],
          str(acquisition.overheard_names("Send help for Kestra at once.", masked, people)))
    check("descriptor-only-no-transmission",
          acquisition.overheard_names("Send help for the worker.", masked, people) == [])
    check("already-known-skipped",
          acquisition.overheard_names("Kestra is here", {"kestra": {"known_as": "Kestra"}}, people) == [])
    check("no-edge-skipped", acquisition.overheard_names("Kestra is here", {}, people) == [])
    check("name-not-in-registry-skipped",
          acquisition.overheard_names("Kestra is here", masked, []) == [])
    # end-to-end: overheard -> reveal_name flips known_as forward, monotonically
    ch = _char(vault=[{"claim": "I tended the damaged worker"}])
    ch["current"]["relationships"] = {"kestra": {"known_as": "the damaged worker"}}
    for eid, nm in acquisition.overheard_names("Kestra, come inside.", ch["current"]["relationships"], people):
        acquisition.reveal_name(ch, eid, nm)
    check("overheard-then-revealed", ch["current"]["relationships"]["kestra"]["known_as"] == "Kestra")
    check("old-descriptor-memory-kept", ch["current"]["vault"][0]["claim"] == "I tended the damaged worker")


def main():
    print("test_acquisition.py — the vault grows (knowledge-model.md acquisition)\n")
    test_assess_promotes_durable_subject_turn()
    test_assess_rejects()
    test_assess_dedups()
    test_ledger_roundtrip()
    test_reveal_name_monotonic()
    test_resume_replay_data()
    test_witness_belief()
    test_faithfulness_name_leak()
    test_overheard_names()
    total = len(PASS) + len(FAIL)
    print("\n--- summary ---\n  %d / %d passed" % (len(PASS), total))
    if FAIL:
        print("  FAILED:")
        for f in FAIL:
            print("    " + f)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
