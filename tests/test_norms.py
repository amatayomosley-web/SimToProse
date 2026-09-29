#!/usr/bin/env python3
"""test_norms.py — a group's norms: what is proper, and what breaking it costs (gate knowledge-norms, 2026-09-29).

A norm is a knowledge entry marked `norm: true` with a `sanction`: held by a group, linked to each member like the
group's facts, but told as the way of that group, everyday to every member whatever their trade, and never fading - a
custom is replaced when you move, not forgotten. Invented here: in the weaving town of Ashcombe a weaver finishes every
row she starts, and to leave a row half-woven shames the loom. Ottilie, a baker, lives there; Florian, a wool buyer
from the lowlands, does not; Hester grew up there and left twenty years ago. What must hold:
  - Ottilie holds the custom, with its cost, as the way of the ashcombe folk - everyday, core, never fading;
  - a plain fact of the same group, beside it, fades as memories do (the control);
  - Hester holds it faded and dated; Florian holds nothing;
  - validate_world refuses a norm that is not true/false and a sanction that is not words or stands on a plain fact;
  - through scripts/scene.py main, when a stranger leaves a row half-woven, Ottilie's actor is reminded of the
    custom and its cost, and Florian's is not.
Every name and custom here is invented for this test.
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
from src.engine.decay import calculate_effective_confidence        # noqa: E402
from src.engine.records import RecordError                         # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

PASS, FAIL = [], []
RULE = "A weaver finishes every row she starts."
COST = "To leave a row half-woven shames the loom."
FLOOD = "The sheds close for the whole of the shearing month."


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


WORLD = dict(copy.deepcopy(WORLD_ENGINE))
WORLD["lexicon"] = {"attribute_classes": {"loom": ["loom", "shuttle", "row", "woven"]}}
WORLD["locations"] = [{"id": "ashcombe", "name": "Ashcombe", "what": "a weaving town in the hills"}]
WORLD["people"] = [{"id": "ottilie", "what": "a baker", "groups": ["ashcombe-folk"]},
                   {"id": "florian", "what": "a wool buyer from the lowlands"},
                   {"id": "hester", "what": "a dyer who grew up in Ashcombe", "groups": ["ashcombe-folk"]}]
WORLD["knowledge"] = [
    {"claim": RULE, "held_by": ["grp.ashcombe-folk"], "norm": True, "sanction": COST, "topic": "loom"},
    {"claim": FLOOD, "held_by": ["grp.ashcombe-folk"]},
]


def _link(char, text):
    return [b for b in knowledge.links_for(char, WORLD) if text in b["claim"]]


def test_units():
    print("\n[1] a custom is held as the way of the group, and does not fade")
    check("the fixture world validates", knowledge.validate_world(copy.deepcopy(WORLD)) is None)
    ottilie = {"fixed": {"position": "a baker"}, "current": {"memberships": [{"of": "grp.ashcombe-folk"}]}}
    norm = _link(ottilie, RULE)
    check("Ottilie holds the custom with its cost", len(norm) == 1 and norm[0]["claim"] == "%s %s" % (RULE, COST), norm)
    n = norm[0] if norm else {}
    check("...as the way of the ashcombe folk", n.get("provenance") == "the way of the ashcombe folk" and n.get("norm") == "grp.ashcombe-folk", n)
    check("...everyday, though baking has nothing to do with looms", n.get("familiarity") == "everyday", n)
    check("...and core", n.get("durability") == "core", n)
    fact = (_link(ottilie, FLOOD) or [{}])[0]
    check("control: a plain fact of the same group is known in it, familiar, durable",
          fact.get("provenance") == "known in the ashcombe folk" and fact.get("familiarity") == "familiar"
          and fact.get("durability") == "durable", fact)
    ten_years = 3650.0
    check("after ten years the custom holds as it was authored", calculate_effective_confidence(n, elapsed=ten_years)
          == n.get("confidence"), calculate_effective_confidence(n, elapsed=ten_years))
    check("...while the plain fact has faded", calculate_effective_confidence(fact, elapsed=ten_years) < fact.get("confidence", 0),
          calculate_effective_confidence(fact, elapsed=ten_years))
    hester = {"current": {"memberships": [{"of": "grp.ashcombe-folk", "left": "20y"}]}}
    w = (_link(hester, RULE) or [{}])[0]
    check("Hester, gone twenty years, holds it faded and dated", w.get("familiarity") == "faded"
          and w.get("learned_days") == 7300.0, w)
    check("Florian, a stranger to the town, holds nothing", knowledge.links_for({"current": {"memberships": []}}, WORLD) == [])
    for entry, why in (({"norm": "yes"}, "a norm that is not true/false"),
                       ({"sanction": COST}, "a sanction on a plain fact"),
                       ({"norm": True, "sanction": ""}, "an empty sanction"),
                       ({"norm": True, "sanction": 3}, "a sanction that is not words")):
        bad = copy.deepcopy(WORLD)
        bad["knowledge"] = [dict({"claim": RULE, "held_by": ["grp.ashcombe-folk"]}, **entry)]
        try:
            knowledge.validate_world(bad)
            check("the world refuses %s" % why, False)
        except RecordError as e:
            check("the world refuses %s (KNOWLEDGE_NORM_INVALID)" % why,
                  "KNOWLEDGE_NORM_INVALID" in str(e) or getattr(e, "code", "") == "KNOWLEDGE_NORM_INVALID", e)


def _sheet(name, memberships):
    eng = copy.deepcopy(CHAR_ENGINE)
    eng["fixed"]["name"] = name
    eng["fixed"]["position"] = "a baker" if name == "Ottilie" else "a wool buyer"
    eng["current"]["memberships"] = memberships
    eng["current"]["relationships"] = {}
    eng["current"]["location"] = "ashcombe"
    return "---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(eng, indent=1))


class _Captured(Exception):
    def __init__(self, messages):
        super().__init__("captured")
        self.messages = messages


def _mind(book, who):
    import scene
    import direct
    cfg = os.path.join(book, "scenes", "guest_%s_cfg.json" % who)
    with open(cfg, "w", encoding="utf-8") as fh:
        json.dump({"name": "guest_" + who, "at": {"day": 1, "time": "18:00"},
                   "situation": "The newcomer drops the shuttle mid-row and walks off to haggle over wool.",
                   "cast": [{"id": who, "drive": "see the evening through"}]}, fh)
    real = scene.faithful_turn

    def fake(packet, event_text, temperament, model, stub, **kw):
        raise _Captured(scene.build_turn_messages(
            packet, event_text, temperament, kw.get("relationships"), acts=kw.get("acts", ()),
            rung_direction=direct.rung_direction(packet, brief=kw.get("brief", ""), model=model, stub=stub)))
    argv = sys.argv
    sys.argv = ["scene.py", "--book", book, "--scene", cfg, "--stub", "--no-keeper", "--budget", "1",
                "--db", os.path.join(book, "runs", "guest_%s.db" % who)]
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
    print("\n[2] through scripts/scene.py: the member is reminded of the custom and its cost; the stranger is not")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        book = os.path.join(tmp, "Ashcombe Fixture")
        for sub in ("world", "characters", "scenes", "runs"):
            os.makedirs(os.path.join(book, sub))
        with open(os.path.join(book, "world", "Ashcombe.md"), "w", encoding="utf-8") as fh:
            fh.write("---\ntype: world\nid: Ashcombe\n---\n# Ashcombe\n\n```json\n%s\n```\n" % json.dumps(WORLD, indent=1))
        for name, ms in (("Ottilie", [{"of": "grp.ashcombe-folk"}]), ("Florian", [])):
            with open(os.path.join(book, "characters", name + ".md"), "w", encoding="utf-8") as fh:
                fh.write(_sheet(name, ms))
        ottilie, florian = _mind(book, "ottilie"), _mind(book, "florian")
        check("Ottilie's actor is reminded of the custom and what breaking it costs",
              RULE in ottilie and COST in ottilie and "the way of the ashcombe folk" in ottilie, ottilie)
        check("Florian's actor, a stranger to it, is not", RULE not in florian, florian)
        gc.collect()


if __name__ == "__main__":
    print("test_norms.py - a group's norms")
    test_units()
    test_through_the_driver()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)
