#!/usr/bin/env python3
"""test_identity.py — one person under two identities, joined by a fact for whoever holds it (gate knowledge-identity).

Fable review 3, M3: a person a story shows under two names is two people[] entries, and what joins them is a FACT -
held by whoever knows it, and by nobody else. Invented here: the hill folk know Maudie, who keeps bees on the south
slope; the market knows Brisk, who sells baskets on Tuesdays - two people[] entries, one woman. Petra, who buys from
both, holds that they are the same (`same_as`); Dell does not. What must hold:
  - through gate.run_gate: for Petra, recognizing Maudie brings what she knows of Brisk to mind; for Dell it does not;
  - the identity itself comes to mind under either name; knows_about(Petra, "maudie") answers with Brisk's baskets;
  - a group can hold an identity (world knowledge `same_as`), joined for its members only; a bad one is refused, in the
    world and on a sheet at the run's start;
  - through scripts/scene.py main, Petra's actor, in a scene where Maudie sells honey, is reminded of the baskets;
    Dell's is not.
Every name and situation here is invented for this test.
"""
import contextlib
import copy
import gc
import io
import json
import os
import re
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import knowledge                                   # noqa: E402
from src.engine.gate import run_gate                               # noqa: E402
from src.engine.records import RecordError                         # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

PASS, FAIL = [], []
BASKETS = "Brisk weaves the tightest baskets in the valley."
SAME = "Maudie the beekeeper and Brisk the basket-seller are one woman."
RESTED = {"energy": 1.0, "allostatic_load": 0.0}


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


WORLD = dict(copy.deepcopy(WORLD_ENGINE))
WORLD["locations"] = [{"id": "market", "what": "the Tuesday market below the hill"}]
WORLD["people"] = [{"id": "petra", "what": "a weaver"}, {"id": "dell", "what": "a drover"},
                   {"id": "maudie", "name": "Maudie", "what": "a beekeeper on the south slope"},
                   {"id": "brisk", "name": "Brisk", "what": "a basket-seller at the Tuesday market"}]
BASKETS_B = {"claim": BASKETS, "confidence": 0.8, "provenance": "seen at the market", "durability": "durable",
             "about": ["brisk"]}
SAME_B = {"claim": SAME, "confidence": 0.8, "provenance": "seen", "durability": "durable",
          "about": ["maudie", "brisk"], "same_as": ["maudie", "brisk"]}
# The same conclusion in the words it is often reached in - naming neither. Its `about` holds nothing, so it is no bridge
# in the graph: only the identity itself can join the two ids. (Written with both names, the belief IS a bridge, and the
# walk from it already drags the other name's memories along - Fable review 3, M3 (ii) - so the checks that prove the
# join use this one.)
HER = "The basket-seller and the beekeeper are the same woman."
HER_B = {"claim": HER, "confidence": 0.8, "provenance": "seen", "durability": "durable", "same_as": ["maudie", "brisk"]}
HIVES = "Maudie keeps twelve hives on the south slope."
HIVES_B = {"claim": HIVES, "confidence": 0.8, "provenance": "lived", "durability": "durable", "about": ["maudie"]}


def claims(got):
    return [r["claim"] for r in got]


def test_the_join_is_the_holders():
    print("\n[1] two ids are one person only for whoever holds that they are")
    petra, dell = [dict(BASKETS_B), dict(SAME_B)], [dict(BASKETS_B)]
    got = run_gate(["maudie"], petra, {}, [], RESTED)
    check("Petra, recognizing Maudie, is reminded of Brisk's baskets", BASKETS in claims(got), claims(got))
    check("...and of the identity itself", SAME in claims(got), claims(got))
    check("Dell, who does not hold it, is not", run_gate(["maudie"], dell, {}, [], RESTED) == [])
    check("the identity comes to mind under the other name too", SAME in claims(run_gate(["brisk"], petra, {}, [], RESTED)))
    check("knowledge.same_ids joins them under one id, deterministically",
          knowledge.same_ids(petra) == {"maudie": "brisk", "brisk": "brisk"}, knowledge.same_ids(petra))
    about = [b["claim"] for b in knowledge.knows_about({"current": {"vault": petra}}, "maudie")]
    check("what Petra knows about Maudie includes Brisk's baskets", BASKETS in about and SAME in about, about)
    check("what Dell knows about Maudie does not", knowledge.knows_about({"current": {"vault": dell}}, "maudie") == [])
    rev = [b["claim"] for b in knowledge.knows_about({"current": {"vault": [dict(BASKETS_B), dict(HIVES_B), dict(HER_B)]}},
                                                     "brisk")]
    check("...and what she knows about Brisk includes Maudie's hives (either name, both ways)",
          HIVES in rev and BASKETS in rev, rev)
    refuted = [dict(BASKETS_B), dict(SAME_B, status="refuted")]
    check("an identity she no longer holds joins nothing", run_gate(["maudie"], refuted, {}, [], RESTED) == [])
    # what only the identity can do - the graph has no bridge from Maudie to Brisk here:
    words = [dict(BASKETS_B), dict(HER_B)]
    got = run_gate(["maudie"], words, {}, [], RESTED)
    check("an identity naming neither still joins them (it is the knower's, not the words')", BASKETS in claims(got), claims(got))
    check("...and the baskets are reached directly, not dragged", [r.get("hops") for r in got if r["claim"] == BASKETS] == [1],
          got)
    both = [dict(BASKETS_B), dict(HIVES_B), dict(HER_B)]
    check("...and the basket-seller's name brings the beekeeper's facts, the other way round",
          HIVES in claims(run_gate(["brisk"], both, {}, [], RESTED)), claims(run_gate(["brisk"], both, {}, [], RESTED)))
    got = run_gate(["hives"], both, {}, [], RESTED)
    check("a word about the beekeeper drags the baskets along - one person is one node in her memory",
          BASKETS in claims(got) and HIVES in claims(got), claims(got))
    spent = {"energy": 0.0, "allostatic_load": 1.0}
    sure = [dict(BASKETS_B, confidence=1.0), dict(SAME_B, confidence=1.0)]
    check("exhausted, when no walk runs, a certain memory of Brisk still comes to mind at Maudie's name",
          BASKETS in claims(run_gate(["maudie"], sure, {}, [], spent)), claims(run_gate(["maudie"], sure, {}, [], spent)))
    sure_hives = [dict(HIVES_B, confidence=1.0), dict(HER_B)]
    check("exhausted, the basket-seller's name still brings a certain memory of the beekeeper",
          HIVES in claims(run_gate(["brisk"], sure_hives, {}, [], spent)), claims(run_gate(["brisk"], sure_hives, {}, [], spent)))


def test_a_group_can_hold_it():
    print("\n[2] a group can hold an identity; a bad one is refused")
    world = dict(copy.deepcopy(WORLD), knowledge=[{"claim": HER, "held_by": ["loc.market"], "same_as": ["maudie", "brisk"]}])
    check("the world validates", knowledge.validate_world(world) is None)
    member = {"current": {"memberships": [{"of": "loc.market"}], "vault": [dict(BASKETS_B)]}}
    stranger = {"current": {"vault": [dict(BASKETS_B)]}}
    knowledge.materialise(world, {"member": member, "stranger": stranger})
    got = run_gate(["maudie"], member["current"]["vault"], {}, [], RESTED)
    check("a regular of the market, recognizing Maudie, is reminded of the baskets", BASKETS in claims(got), claims(got))
    check("a stranger to it is not", run_gate(["maudie"], stranger["current"]["vault"], {}, [], RESTED) == [])
    for value, why in ((["maudie"], "one id"), (["maudie", "ghost"], "an unregistered id"), ("maudie", "not a list")):
        bad = dict(world, knowledge=[{"claim": HER, "held_by": ["loc.market"], "same_as": value}])
        try:
            knowledge.validate_world(bad)
            check("same_as with %s is refused" % why, False)
        except RecordError as e:
            check("same_as with %s is refused (KNOWLEDGE_SAME_AS_INVALID)" % why,
                  "KNOWLEDGE_SAME_AS_INVALID" in str(e) or getattr(e, "code", "") == "KNOWLEDGE_SAME_AS_INVALID", e)


def test_a_sheet_is_checked_at_the_start():
    print("\n[2b] a sheet's identity is checked before a run starts")
    from src.engine import contracts
    for value, why in ((["maudie", "ghost"], "an id the world does not have"), (["maudie"], "one id")):
        eng = copy.deepcopy(CHAR_ENGINE)
        eng["current"]["vault"] = [dict(HER_B, same_as=value)]
        try:
            contracts.require_at_start(copy.deepcopy(WORLD), {"petra": eng})
            check("a sheet whose same_as names %s is refused at the run's start" % why, False)
        except Exception as e:
            check("a sheet whose same_as names %s is refused at the run's start" % why,
                  "same_as" in str(e) and "CONTRACT_RUN_REFUSED" in str(e), e)


def _sheet(name, vault):
    eng = copy.deepcopy(CHAR_ENGINE)
    eng["fixed"]["name"] = name
    eng["current"]["relationships"] = {"maudie": {"trust": 0.6, "affinity": 0.5, "respect": 0.5, "debt": 0.0}}
    eng["current"]["location"] = "market"
    eng["current"]["vault"] = vault
    return "---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(eng, indent=1))


class _Captured(Exception):
    def __init__(self, messages):
        super().__init__("captured")
        self.messages = messages


def _mind(book, who):
    import scene
    import direct
    cfg = os.path.join(book, "scenes", "stall_%s_cfg.json" % who)
    with open(cfg, "w", encoding="utf-8") as fh:
        json.dump({"name": "stall_" + who, "at": {"day": 1, "time": "11:00"},
                   "situation": "Maudie the beekeeper sets a comb of honey on the stall and names her price.",
                   "cast": [{"id": who, "drive": "buy what she came for"}]}, fh)
    real = scene.faithful_turn

    def fake(packet, event_text, temperament, model, stub, **kw):
        raise _Captured(scene.build_turn_messages(
            packet, event_text, temperament, kw.get("relationships"), acts=kw.get("acts", ()),
            rung_direction=direct.rung_direction(packet, brief=kw.get("brief", ""), model=model, stub=stub)))
    argv = sys.argv
    sys.argv = ["scene.py", "--book", book, "--scene", cfg, "--stub", "--no-keeper", "--budget", "1",
                "--db", os.path.join(book, "runs", "stall_%s.db" % who)]
    scene.faithful_turn = fake
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            scene.main()
    except _Captured as cap:
        user = "\n".join(m["content"] for m in cap.messages if m.get("role") == "user")
        m = re.search(r"What it brings to mind:[ \t]*([^\n]*)", user)
        return m.group(1) if m else ""
    finally:
        scene.faithful_turn, sys.argv = real, argv
    raise AssertionError("the scene ended before %s's beat:\n%s" % (who, log.getvalue()[-1500:]))


def test_through_the_driver():
    print("\n[3] through scripts/scene.py: the holder's actor is reminded; the other's is not")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        book = os.path.join(tmp, "Market Fixture")
        for sub in ("world", "characters", "scenes", "runs"):
            os.makedirs(os.path.join(book, sub))
        with open(os.path.join(book, "world", "Market.md"), "w", encoding="utf-8") as fh:
            fh.write("---\ntype: world\nid: Market\n---\n# Market\n\n```json\n%s\n```\n" % json.dumps(WORLD, indent=1))
        for name, vault in (("Petra", [dict(BASKETS_B), dict(HER_B)]), ("Dell", [dict(BASKETS_B)])):
            with open(os.path.join(book, "characters", name + ".md"), "w", encoding="utf-8") as fh:
                fh.write(_sheet(name, vault))
        petra, dell = _mind(book, "petra"), _mind(book, "dell")
        check("Petra's actor is reminded of the baskets when Maudie sells honey", BASKETS in petra, petra)
        check("Dell's actor, who never learned they are one woman, is not", BASKETS not in dell, dell)
        gc.collect()


if __name__ == "__main__":
    print("test_identity.py - one person under two identities")
    test_the_join_is_the_holders()
    test_a_group_can_hold_it()
    test_a_sheet_is_checked_at_the_start()
    test_through_the_driver()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)
