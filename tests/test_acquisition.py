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
    return {"fixed": {"name": "Nora"}, "baseline": {}, "current": {"vault": list(vault or [])}}


def test_assess_promotes_durable_subject_turn():
    print("\n[A] assess — durable + subject -> belief")
    applied = {"target": "delphine", "dimensions": {"care_relevant": 0.4}}
    tags = {"type": "aid", "summary": "I read the whole chapter out for Delphine when she forgot her glasses",
            "durability": "durable", "confidence": 0.85}
    b = acquisition.assess(applied, tags, _char())
    check("durable-subject-promotes", b is not None and b["claim"] == tags["summary"], repr(b))
    check("provenance-lived", bool(b) and b.get("provenance") == "lived", repr(b))
    check("links-to-subject", bool(b) and b.get("links") == ["delphine"], repr(b))
    check("confidence-carried", bool(b) and abs(b.get("confidence", 0) - 0.85) < 1e-9, repr(b))


def test_assess_rejects():
    print("\n[B] assess — rejections")
    base = {"target": "delphine"}
    check("transient-none", acquisition.assess(base, {"summary": "I pour the tea", "durability": "transient"}, _char()) is None)
    check("no-subject-none", acquisition.assess({}, {"summary": "I brood", "durability": "durable"}, _char()) is None)
    check("no-summary-none", acquisition.assess(base, {"summary": "", "durability": "durable"}, _char()) is None)


def test_assess_dedups():
    print("\n[C] assess — dedup vs existing vault")
    applied = {"target": "delphine"}
    tags = {"summary": "I read the chapter out for Delphine", "durability": "durable", "confidence": 0.75}
    ch = _char(vault=[{"claim": "I read the chapter out for Delphine", "provenance": "lived"}])
    check("duplicate-claim-none", acquisition.assess(applied, tags, ch) is None)
    check("novel-claim-promotes", acquisition.assess(applied, tags, _char(vault=[{"claim": "something else"}])) is not None)


def test_ledger_roundtrip():
    print("\n[D] Ledger.append_acquisition / acquisitions_for")
    led = Ledger(os.path.join(tempfile.mkdtemp(), "acq.db"))
    led.create_run("r1", {"catalog_version": 1})
    led.append_acquisition("r1", "nora", 3, {"claim": "first", "provenance": "lived", "links": ["delphine"]})
    led.append_acquisition("r1", "nora", 5, {"claim": "second", "provenance": "lived", "links": []})
    led.append_acquisition("r1", "wendell", 4, {"claim": "wendell-only", "provenance": "lived", "links": []})
    got = led.acquisitions_for("r1", "nora")
    check("nora-gets-two", len(got) == 2, str(got))
    check("ordered-by-turn", [b["claim"] for b in got] == ["first", "second"], str(got))
    check("scoped-by-char", [b["claim"] for b in led.acquisitions_for("r1", "wendell")] == ["wendell-only"])


def test_reveal_name_monotonic():
    print("\n[E] reveal_name — monotonic name acquisition (old info preserved)")
    from src.engine.gate import scope_names
    ch = _char(vault=[{"claim": "I read the chapter out for the woman with the lemon cake", "provenance": "lived"}])
    ch["current"]["relationships"] = {"delphine": {"trust": 0.55, "known_as": "the woman with the lemon cake"}}
    before = len(ch["current"]["vault"])
    b = acquisition.reveal_name(ch, "delphine", "Delphine")
    check("flips-known-as", ch["current"]["relationships"]["delphine"]["known_as"] == "Delphine")
    check("returns-learned-belief", bool(b) and b.get("provenance") == "learned" and "Delphine" in b.get("claim", ""), repr(b))
    check("old-belief-preserved", ch["current"]["vault"][0]["claim"] == "I read the chapter out for the woman with the lemon cake")
    check("monotonic-append", len(ch["current"]["vault"]) == before + 1)
    rels = ch["current"]["relationships"]
    check("name-now-visible-to-knower", scope_names("Delphine enters", rels) == "Delphine enters",
          scope_names("Delphine enters", rels))
    check("others-still-masked", "Delphine" not in scope_names("Delphine enters", {"delphine": {"known_as": "the woman with the lemon cake"}}))
    check("no-edge-returns-none", acquisition.reveal_name(_char(), "ghost", "Boo") is None)


def test_resume_replay_data():
    print("\n[F] resume-replay — arc_diffs_for + vault rehydrate")
    led = Ledger(os.path.join(tempfile.mkdtemp(), "resume.db"))
    led.create_run("r2", {"catalog_version": 1})
    led.append_arc_diff("r2", "nora", 2, {"temperament": {"DISPLEASURE": 0.05}, "_meta": {"dominant": "DISPLEASURE"}})
    led.append_arc_diff("r2", "nora", 4, {"relationships": {"delphine": {"affinity": 0.15}}})
    led.append_acquisition("r2", "nora", 3, {"claim": "learned A", "provenance": "lived"})
    led.append_acquisition("r2", "nora", 5, {"claim": "learned B", "provenance": "lived"})
    diffs = led.arc_diffs_for("r2", "nora")
    check("arc-diffs-two-in-order", len(diffs) == 2 and "DISPLEASURE" in diffs[0].get("temperament", {}), str(diffs))
    # the resume replay: a seed char's vault gets the acquisitions appended in order
    seed = _char(vault=[{"claim": "seed belief"}])
    seed["current"]["vault"].extend(led.acquisitions_for("r2", "nora"))
    claims = [b["claim"] for b in seed["current"]["vault"]]
    check("vault-rehydrated-seed-plus-acquired", claims == ["seed belief", "learned A", "learned B"], str(claims))


def test_witness_belief():
    print("\n[G] witness_belief — bystander remembers a durable act")
    b = acquisition.witness_belief("Nora", {"summary": "I read the chapter out for Delphine", "durability": "durable"}, "nora")
    check("witnessed-deperson", bool(b) and b["claim"].startswith("Nora read the chapter out"), repr(b))
    check("witnessed-provenance-links", bool(b) and b.get("provenance") == "witnessed" and b.get("links") == ["nora"], repr(b))
    check("witness-transient-none", acquisition.witness_belief("Nora", {"summary": "x", "durability": "transient"}, "nora") is None)
    nonfirst = acquisition.witness_belief("Nora", {"summary": "The cup fell", "durability": "durable"}, "nora")
    check("witness-nonfirst-person", bool(nonfirst) and nonfirst["claim"].startswith("Nora — as I saw it"), repr(nonfirst))


def test_faithfulness_name_leak():
    print("\n[H] faithfulness — catch a name the character does not hold")
    from src.engine import faithfulness
    rels = {"delphine": {"known_as": "the woman with the lemon cake"}}
    check("leak-detected", faithfulness.check_name_leaks("I will save Delphine a seat next month.", rels) == [("delphine", "the woman with the lemon cake")],
          str(faithfulness.check_name_leaks("I will save Delphine a seat next month.", rels)))
    check("descriptor-is-clean", faithfulness.check_name_leaks("I will save the woman with the lemon cake a seat next month.", rels) == [])
    check("known-name-is-clean", faithfulness.check_name_leaks("Delphine is here", {"delphine": {"known_as": "Delphine"}}) == [])
    check("no-known_as-is-clean", faithfulness.check_name_leaks("Delphine is here", {"delphine": {"trust": 0.55}}) == [])


def test_overheard_names():
    print("\n[I] overheard_names — transmission: a bystander hears a name and learns it")
    people = [{"id": "delphine", "name": "Delphine Okafor"}, {"id": "nora", "name": "Nora Whitlock"}]
    masked = {"delphine": {"known_as": "the woman with the lemon cake"}}
    check("masked-name-overheard",
          acquisition.overheard_names("Pass the milk to Delphine, would you.", masked, people) == [("delphine", "Delphine")],
          str(acquisition.overheard_names("Pass the milk to Delphine, would you.", masked, people)))
    check("descriptor-only-no-transmission",
          acquisition.overheard_names("Pass the milk to the woman with the lemon cake.", masked, people) == [])
    check("already-known-skipped",
          acquisition.overheard_names("Delphine is here", {"delphine": {"known_as": "Delphine"}}, people) == [])
    check("no-edge-skipped", acquisition.overheard_names("Delphine is here", {}, people) == [])
    check("name-not-in-registry-skipped",
          acquisition.overheard_names("Delphine is here", masked, []) == [])
    # end-to-end: overheard -> reveal_name flips known_as forward, monotonically
    ch = _char(vault=[{"claim": "I read the chapter out for the woman with the lemon cake"}])
    ch["current"]["relationships"] = {"delphine": {"known_as": "the woman with the lemon cake"}}
    for eid, nm in acquisition.overheard_names("Delphine, take the armchair.", ch["current"]["relationships"], people):
        acquisition.reveal_name(ch, eid, nm)
    check("overheard-then-revealed", ch["current"]["relationships"]["delphine"]["known_as"] == "Delphine")
    check("old-descriptor-memory-kept", ch["current"]["vault"][0]["claim"] == "I read the chapter out for the woman with the lemon cake")


def test_the_actors_summary_survives_the_seat():
    print("\n[S] with_actor_summary — the seat rates; the actor's summary still reaches memory")
    seat = {"type": "aid", "durability": "durable", "dimensions": {"care_relevant": 0.4}, "object": "delphine"}
    actor = {"type": "aid", "summary": "I read the chapter out for her", "durability": "transient"}
    merged = acquisition.with_actor_summary(seat, actor)
    check("summary-carried", merged.get("summary") == "I read the chapter out for her", repr(merged))
    check("seat-verdict-untouched", merged["durability"] == "durable" and merged["type"] == "aid", repr(merged))
    check("inputs-not-mutated", "summary" not in seat, repr(seat))
    check("a-seat-summary-is-kept", acquisition.with_actor_summary(dict(seat, summary="seat's"), actor)["summary"] == "seat's")
    check("no-actor-summary-adds-nothing", "summary" not in acquisition.with_actor_summary(seat, {"type": "aid"}))
    check("a-non-dict-actor-reply-is-safe", "summary" not in acquisition.with_actor_summary(seat, None))
    applied = {"target": "delphine", "dimensions": {"care_relevant": 0.4}}
    check("seat-tags-alone-acquire-nothing", acquisition.assess(applied, seat, _char()) is None)
    b = acquisition.assess(applied, merged, _char())
    check("with-the-summary-the-beat-is-remembered", b is not None and b["claim"] == "I read the chapter out for her", repr(b))


def test_learned_memories_are_meaningful():
    """gate learned-memories-durable (2026-09-24): every memory learned in a story came from a durable event (or is a
    name), and carried no durability, so `decay` faded it as an everyday detail - a week on, barely recalled."""
    print("\n[H] learned memories fade as meaningful ones")
    from src.engine import decay
    from src.engine.decay_law import relax
    lived = acquisition.assess({"target": "delphine"}, {"summary": "I read the chapter out for Delphine",
                                                        "durability": "durable", "confidence": 0.85}, _char())
    seen = acquisition.witness_belief("Nora", {"summary": "I read the chapter out for Delphine", "durability": "durable"}, "nora")
    char = _char()
    char["current"]["relationships"] = {"delphine": {"trust": 0.6}}
    named = acquisition.reveal_name(char, "delphine", "Delphine")
    check("lived-witnessed-and-named-are-all-meaningful",
          all(b and b.get("durability") == "durable" for b in (lived, seen, named)), repr((lived, seen, named)))
    week = decay.calculate_effective_confidence(lived, elapsed=7.0)
    want = round(relax(0.85, min(0.85, decay.FLOOR_DURABLE), decay.RETENTION_DURABLE, 7.0), 4)
    check("a-week-on-it-fades-at-the-meaningful-rate", week == want and week > 0.6, repr((week, want)))
    led = Ledger(os.path.join(tempfile.mkdtemp(), "old.db"))
    led.create_run("r1", {"catalog_version": 1})
    with led.con:                                      # a memory logged before this gate: no durability in it
        led.con.execute("INSERT INTO acquisitions (run_id, char_id, turn, belief) VALUES ('r1', 'nora', 2, ?)",
                        ('{"claim": "old", "provenance": "lived", "links": []}',))
    check("a-memory-logged-before-reads-back-meaningful", led.acquisitions_for("r1", "nora")[0].get("durability") == "durable",
          repr(led.acquisitions_for("r1", "nora")))


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
    test_the_actors_summary_survives_the_seat()
    test_learned_memories_are_meaningful()
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
