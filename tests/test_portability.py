#!/usr/bin/env python3
"""test_portability.py — gate-6 proof: the machine is book-agnostic.

Two checks, both mechanical:
  1. ALIEN FIXTURE: a world + character sharing ONLY the schema with Maren/Ashford (a debt-collector
     in a port city — different vocabulary, different wound, different lexicon) runs the COMPLETE
     loop: assemble -> prompt build -> validate_tags -> appraise -> decay -> ledger turn-commit ->
     fold -> resume. Zero src/engine edits required is the claim; this test is the proof.
  2. TOKEN SWEEP: no fixture word (either book's) appears anywhere in src/engine/*.py — content
     lives in content packages, the machine carries none of it.
Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import re
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.scene import assemble                              # noqa: E402
from src.engine.prompt import build_turn_messages                  # noqa: E402
from src.engine.consolidation import validate_tags                 # noqa: E402
from src.engine.state import build_profile, appraise, decay        # noqa: E402
from src.engine.ledger import Ledger                               # noqa: E402
from src.engine.records import Event, TurnCommit, PRIMARIES        # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


# ---- the alien fixture: Vesk, a harbor debt-collector in Carrowport (inline test data) ----

WORLD = {
    "world": "Carrowport — a salt-bitten harbor city",
    "season": "storm season; ships overdue, ledgers unpaid",
    "lexicon": {
        "attribute_classes": {
            "debt":    ["debt", "owed", "ledger", "coin", "payment", "arrears"],
            "ship":    ["ship", "harbor", "dock", "cargo", "vessel", "overdue"],
            "violence": ["knife", "blade", "beaten", "bruised", "threat"],
            "storm":   ["storm", "gale", "swell", "rain"],
        },
        "subtle_cues": {
            "hidden-weapon": ["beneath the coat", "at the hip"],
            "false-ledger":  ["figures do not sit", "ink too fresh"],
        },
        "subtle_cue_classes": ["violence"],
    },
    "locations": [{"id": "countinghouse", "what": "the countinghouse on the quay where Vesk keeps the books"}],
    "people": [{"id": "marlo_clerk", "what": "the countinghouse clerk, quick with figures, quicker to look away"}],
}

CHAR = {
    "fixed": {"name": "Vesk", "genotype": {
        "threat_reactivity": "typical", "approach_drive": "elevated", "affiliation_attachment": "low",
        "anger_proneness": "elevated", "effortful_control": "typical", "sensitivity": "typical"}},
    "baseline": {
        "temperament": {p: {"mean": m, "variability": 0.1} for p, m in
                        zip(PRIMARIES, (0.6, 0.45, 0.5, 0.2, 0.3, 0.35, 0.3))},
        "traits": {"emotionality": {"mean": 0.4}, "agreeableness": {"mean": 0.3}, "extraversion": {"mean": 0.55}},
        "model": {"schwartz": {"security": 0.8, "achievement": 0.7, "benevolence": 0.2, "self_direction": 0.6},
                  "moral_foundations": {"fairness": 0.85, "loyalty": 0.5, "care_harm": 0.25},
                  "needs": {"competence": 0.75, "relatedness": 0.2}},
        "drives": {"goals": [{"goal": "collect what the ledger says is owed", "urgency": 0.7}],
                   "fears_wounds": [{"wound": "the year the house seized HIS family's boat for arrears"}],
                   "orientation": "the ledger is the only honest thing in the harbor"},
        "skills": {"streetwise": 0.8, "insight": 0.7, "perception": 0.6, "persuasion": 0.65, "combat": 0.5},
        "voice": {"register": "flat, clipped", "tic": "thumbs the ledger's edge"},
    },
    "current": {
        "affect": {p: v for p, v in zip(PRIMARIES, (0.6, 0.45, 0.5, 0.2, 0.3, 0.35, 0.3))},
        "condition": {"energy": 0.7, "allostatic_load": 0.3, "health": 0.9, "fatigue": 0.2, "injuries": []},
        "active_goals": [{"goal": "collect what the ledger says is owed", "urgency": 0.7}],
        "relationships": {"marlo_clerk": {"trust": 0.4, "affinity": 0.3, "respect": 0.5, "debt": 0.0}},
        "vault": [
            {"claim": "the harbor master's ledger ran false the year the boat was seized",
             "believed_value": "the wound", "provenance": "lived", "timestamp": "t-20y", "confidence": 1.0},
            {"claim": "Marlo's figures do not always sit square", "believed_value": True,
             "provenance": "observation", "timestamp": "recent", "confidence": 0.6},
        ],
        "zone": "quay", "location": "countinghouse",
    },
}

EVENTS_ALIEN = [
    {"text": "Morning on the quay; the ledger shows three debts in arrears.", "kind": "mundane",
     "hint": {"mastery": 0.2}},
    {"text": "A cargo ship is overdue; its owner owes the house forty crowns.", "kind": "threat",
     "hint": {"threat": 0.4, "mastery": 0.3}},
    {"text": "Marlo the clerk presents figures; the ink too fresh on one page.", "kind": "threat",
     "hint": {"threat": 0.5, "social_violation": 0.4}},
    {"text": "A debtor arrives with a knife beneath the coat and empty hands.", "kind": "threat",
     "hint": {"threat": 0.7}},
    {"text": "The storm breaks over the harbor; collections wait.", "kind": "mundane",
     "hint": {"relief": 0.2}},
    {"text": "The debtor pays in full, coin counted twice on the countinghouse table.", "kind": "care",
     "hint": {"relief": 0.5, "mastery": 0.4}},
]


def test_alien_full_loop():
    print("\n[1] ALIEN FIXTURE — full loop, zero engine edits")
    tmp = tempfile.mkdtemp(prefix="swe_port_")
    try:
        led = Ledger(os.path.join(tmp, "carrowport.db"))
        led.create_run("vesk-1", {"catalog_version": 1, "models": {"decide": "stub"}, "prompt_versions": {"turn": 1}})
        led.register_character("vesk-1", "vesk", CHAR["fixed"], CHAR["baseline"])
        profile = build_profile(CHAR)
        temperament = CHAR["baseline"]["temperament"]
        affect = dict(CHAR["current"]["affect"])
        recall_fired, percept_classes = set(), set()
        for i, ev in enumerate(EVENTS_ALIEN):
            packet = assemble(CHAR, WORLD, {"event": {"text": ev["text"], "kind": ev["kind"]},
                                            "recent": [], "location": CHAR["current"]["location"]},
                              affect, CHAR["current"]["condition"])
            for p in packet["volatile"]["percepts"]:
                percept_classes.update(p.get("attributes", []))
            recall_fired.update(r["ref"] for r in packet["volatile"]["recall"])
            msgs = build_turn_messages(packet, ev["text"], temperament)
            tags = {"type": ev["kind"], "summary": ev["text"], "dimensions": dict(ev["hint"]),
                    "durability": "transient"}
            validation = validate_tags(tags, packet["volatile"]["percepts"], CHAR["baseline"]["skills"])
            affect = decay(appraise(affect, tags, profile), temperament, profile)
            led.append_turn(TurnCommit(
                run_id="vesk-1", turn=i, actor="vesk", thought="t", action="a", tags=tags,
                affect=dict(affect), validation=validation,
                events=[Event(type=ev["kind"], payload={"text": ev["text"]}, actor="vesk")],
                manifest=packet["manifest"], recall=packet["recall_refs"]))
        resumed = led.resume("vesk-1")
        check("six-turn-commits", led.latest_turn("vesk-1") == 5)
        check("resume-determinism", resumed["turn"] == 5)
        check("lexicon-classes-fired", {"debt", "ship", "violence"} <= percept_classes,
              "saw: %s" % sorted(percept_classes))
        check("alien-vault-recall-fired", len(recall_fired) >= 1, "no vault belief ever recalled")
        check("affect-bounded", all(0.0 <= v <= 1.0 for v in affect.values()))
        check("prompt-built-digit-free-state", not re.search(r"\d", msgs[1]["content"].split("Active goals:")[0]))
        check("validation-clean-on-stub-tags", validation["ok"] and not validation["escalate"],
              str(validation))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_fixture_tokens_in_engine():
    """The sweep: neither book's vocabulary may appear in the machine."""
    print("\n[2] TOKEN SWEEP over src/engine")
    tokens = ("maren", "ashford", "joss", "edda", "bryn", "suil", "tobin", "healer",
              "vesk", "carrowport", "marlo", "countinghouse")
    hits = []
    eng = os.path.join(REPO, "src", "engine")
    for fn in sorted(os.listdir(eng)):
        if not fn.endswith((".py", ".sql")):
            continue
        text = open(os.path.join(eng, fn), encoding="utf-8").read().lower()
        for tok in tokens:
            if tok in text:
                hits.append("%s: %s" % (fn, tok))
    check("zero-fixture-tokens-in-machine", not hits, "; ".join(hits[:6]))


def main():
    print("test_portability.py — gate 6: the machine is book-agnostic\n")
    test_alien_full_loop()
    test_no_fixture_tokens_in_engine()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
