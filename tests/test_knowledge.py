#!/usr/bin/env python3
"""test_knowledge.py — what a group knows, linked to each member (gate knowledge-links, 2026-09-28).

The owner's confirmed example, invented: Aren, a guild hunter living in the city, raised in the village of Millbrook
and gone from it ten years. A stranger asks about the city's festival, about registering with the guild, says he is
from Millbrook and asks after Sheriff Ambrose. What the owner confirmed must hold:
  - the guild's procedure is everyday to Aren, the city's festival familiar, Millbrook's facts faded and dated;
  - Ambrose's death, which Millbrook learned after Aren left, is a fact his links never reached;
  - the stranger who SAYS he is from Millbrook holds no Millbrook link (the liar test);
  - shared knowledge cannot crowd a character's own memory out of recall (Fable review 3, B1).
The prompts are captured through scripts/scene.py's own main (the --prompt-only seam's call), never a hand-built
packet. Every name here is invented for this test.
"""
import contextlib
import copy
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

from src.engine import knowledge, vault                            # noqa: E402
from src.engine.gate import run_gate                               # noqa: E402
from src.engine.records import RecordError                         # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


FESTIVAL = "The city keeps its Thaw Festival on the first day the river ice breaks."
REGISTER = "To join the hunters' guild you sign the roll at the guildhall, bring a sponsor and pay the fee."
SHERIFF = "Ambrose keeps the peace in Millbrook as its sheriff."
PELLINGS = "The Pellings farm the east bank below the Millbrook mill."
DEATH = "Sheriff Ambrose died last winter."
OWN = "I learned to swim in the Millbrook millpond."

WORLD = dict(copy.deepcopy(WORLD_ENGINE))
WORLD["lexicon"] = {"attribute_classes": {"festival": ["festival", "holiday", "feast"],
                                          "guild": ["guild", "register", "registers", "roll", "sponsor"],
                                          "beasts": ["beast", "beasts", "wyrm", "hunt", "hunter"],
                                          "millbrook": ["millbrook"],
                                          "law": ["sheriff", "law", "peace"]}}
WORLD["locations"] = [{"id": "the_city", "name": "the city", "what": "a river city of stone quays"},
                      {"id": "millbrook", "name": "Millbrook", "what": "a mill village two days upriver"},
                      {"id": "tavern", "what": "the long room of the Quay Tavern"}]
WORLD["people"] = [{"id": "aren", "what": "a guild hunter", "groups": ["hunters-guild"]},
                   {"id": "quentin", "what": "a traveller at the tavern"},
                   {"id": "ambrose", "what": "the sheriff of Millbrook", "groups": ["millbrook-folk"]},
                   {"id": "vey", "what": "the guildmaster", "groups": ["hunters-guild"]}]
WORLD["knowledge"] = [
    {"claim": FESTIVAL, "held_by": ["loc.the_city"], "topic": "festival"},
    {"claim": REGISTER, "held_by": ["grp.hunters-guild"], "topic": "guild"},
    {"claim": SHERIFF, "held_by": ["loc.millbrook"], "about": ["ambrose"], "topic": "law"},
    {"claim": PELLINGS, "held_by": ["loc.millbrook"]},
    {"claim": DEATH, "held_by": ["loc.millbrook"], "about": ["ambrose"], "since": "180d"},
]


def _sheet(name, memberships, beliefs=(), relationships=None):
    eng = copy.deepcopy(CHAR_ENGINE)
    eng["fixed"]["name"] = name
    eng["fixed"]["position"] = "a hunter of beasts for the guild" if name == "Aren" else "a traveller"
    eng["current"]["memberships"] = memberships
    eng["current"]["relationships"] = relationships or {}
    eng["current"]["location"] = "tavern"
    note = "---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(eng, indent=1))
    if beliefs:
        note += "\n## Beliefs\n" + "".join("- (%s, %s) %s\n" % b for b in beliefs)
    return note


def _book(tmp):
    book = os.path.join(tmp, "Aren Fixture")
    for sub in ("world", "characters", "scenes", "runs"):
        os.makedirs(os.path.join(book, sub))
    with open(os.path.join(book, "world", "The City.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\nid: The City\n---\n# The City\n\n```json\n%s\n```\n" % json.dumps(WORLD, indent=1))
    with open(os.path.join(book, "characters", "Aren.md"), "w", encoding="utf-8") as fh:
        fh.write(_sheet("Aren", [{"of": "loc.the_city"}, {"of": "grp.hunters-guild"}, {"of": "loc.millbrook", "left": "10y"}],
                        beliefs=[("0.7", "lived", OWN + " [[millbrook]]")],
                        relationships={"ambrose": {"trust": 0.7, "affinity": 0.6, "respect": 0.7, "debt": 0.0}}))
    with open(os.path.join(book, "characters", "Quentin.md"), "w", encoding="utf-8") as fh:
        fh.write(_sheet("Quentin", [{"of": "loc.the_city"}]))
    return book


class _Captured(Exception):
    def __init__(self, messages):
        super().__init__("captured")
        self.messages = messages


def _prompt(book, name, situation):
    """Aren's first-beat messages for one scene, through scripts/scene.py main (the --prompt-only seam's call)."""
    import scene
    import direct
    cfg = os.path.join(book, "scenes", name + "_cfg.json")
    with open(cfg, "w", encoding="utf-8") as fh:
        json.dump({"name": name, "at": {"day": 1, "time": "20:00"}, "situation": situation,
                   "cast": [{"id": "aren", "drive": "finish his supper and get to bed"}]}, fh)
    real = scene.faithful_turn

    def fake(packet, event_text, temperament, model, stub, think=True, brief="", seed=None, acts=(),
             relationships=None, information=None, char_id=None, max_retries=2):
        raise _Captured(scene.build_turn_messages(packet, event_text, temperament, relationships, acts=acts,
                                                  rung_direction=direct.rung_direction(packet, brief=brief, model=model,
                                                                                       stub=stub)))
    argv = sys.argv
    sys.argv = ["scene.py", "--book", book, "--scene", cfg, "--stub", "--no-keeper", "--budget", "1",
                "--db", os.path.join(book, "runs", name + ".db")]
    scene.faithful_turn = fake
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            scene.main()
    except _Captured as cap:
        return "\n".join(m["content"] for m in cap.messages if m.get("role") == "user")
    finally:
        scene.faithful_turn, sys.argv = real, argv
    raise AssertionError("scene %s ended before Aren's beat:\n%s" % (name, log.getvalue()[-1500:]))


def _mind(user_text):
    """The 'What it brings to mind' section of the actor's user message."""
    m = re.search(r"What it brings to mind:[ \t]*([^\n]*)", user_text)
    return m.group(1) if m else ""


def test_units():
    check("age: <n>y is years of days", knowledge.days("10y") == 3650.0)
    check("age: <n>d and bare numbers are days", knowledge.days("180d") == 180.0 and knowledge.days(3) == 3.0)
    for bad in ("soon", "0d", "-2y", True):
        try:
            knowledge.days(bad)
            check("age refuses %r" % (bad,), False)
        except RecordError as e:
            check("age refuses %r" % (bad,), "KNOWLEDGE_AGE_NOT_A_SPAN" in str(e) or getattr(e, "code", "") == "KNOWLEDGE_AGE_NOT_A_SPAN", e)
    words = [knowledge.age_words(d) for d in (0, 10, 200, 1000, 3650, 20000)]
    check("age words: none for no age, then the bands", words == ["", "lately", "within the past year", "some years back",
                                                                     "years ago", "long ago"], words)
    check("age words carry no digit", not any(re.search(r"\d", w) for w in words))
    world = copy.deepcopy(WORLD)
    check("the fixture world validates", knowledge.validate_world(world) is None)
    for field, value, code in (("held_by", ["loc.nowhere"], "KNOWLEDGE_HOLDER_UNREGISTERED"),
                               ("held_by", [], "KNOWLEDGE_HELD_BY_EMPTY"),
                               ("topic", "weather", "KNOWLEDGE_TOPIC_UNKNOWN"),
                               ("about", ["ghost"], "KNOWLEDGE_ABOUT_UNREGISTERED"),
                               ("since", "someday", "KNOWLEDGE_AGE_NOT_A_SPAN"),
                               ("confidence", 1.5, "KNOWLEDGE_CONFIDENCE_RANGE"),
                               ("claim", "  ", "KNOWLEDGE_CLAIM_EMPTY")):
        bad = copy.deepcopy(WORLD)
        bad["knowledge"][0][field] = value
        try:
            knowledge.validate_world(bad)
            check("world refuses %s=%r" % (field, value), False)
        except RecordError as e:
            check("world refuses %s=%r with %s" % (field, value, code), code in str(e) or getattr(e, "code", "") == code, e)
    from src.engine.attachments import names_for
    reg = names_for(WORLD)
    for rows, code in (([{"of": "grp.nobody"}], "KNOWLEDGE_MEMBERSHIP_UNREGISTERED"),
                       ([{"of": "loc.millbrook", "left": "a while"}], "KNOWLEDGE_AGE_NOT_A_SPAN"),
                       ([{"of": "loc.millbrook", "familiarity": "vivid"}], "KNOWLEDGE_FAMILIARITY_UNKNOWN"),
                       (["loc.millbrook"], "KNOWLEDGE_MEMBERSHIP_NOT_A_DICT"),
                       ({"of": "loc.millbrook"}, "KNOWLEDGE_MEMBERSHIPS_NOT_A_LIST")):
        try:
            knowledge.validate_memberships(rows, reg)
            check("memberships refuse %r" % (rows,), False)
        except RecordError as e:
            check("memberships refuse %r with %s" % (rows, code), code in str(e) or getattr(e, "code", "") == code, e)
    for rows in (None, [{"of": "loc.millbrook", "left": "10y", "familiarity": "faded"}]):
        check("memberships accept %r" % (rows,), knowledge.validate_memberships(rows, reg) is None)


def test_links(book):
    world, chars = vault.load_book(book)
    aren, quentin = chars["aren"], chars["quentin"]
    links = {b["claim"]: b for b in aren["current"]["vault"] if b.get("shared")}
    check("Aren is linked to the city's festival, familiar", links.get(FESTIVAL, {}).get("familiarity") == "familiar", links.get(FESTIVAL))
    check("Aren is linked to the guild's procedure, everyday (his position names the guild)",
          links.get(REGISTER, {}).get("familiarity") == "everyday", links.get(REGISTER))
    check("Aren holds Millbrook's sheriff, faded and dated ten years",
          links.get(SHERIFF, {}).get("familiarity") == "faded" and links.get(SHERIFF, {}).get("learned_days") == 3650.0,
          links.get(SHERIFF))
    check("Aren holds the Pellings, faded", links.get(PELLINGS, {}).get("familiarity") == "faded")
    check("Ambrose's death, learned after Aren left, is not linked", DEATH not in links)
    check("a link says where it came from", links.get(SHERIFF, {}).get("provenance") == "known in Millbrook", links.get(SHERIFF))
    check("his own memory is still there", any(b.get("claim", "").startswith(OWN[:20]) and not b.get("shared")
                                               for b in aren["current"]["vault"]))
    check("links are stamped like any belief (about carries the village)", "millbrook" in (links.get(PELLINGS) or {}).get("about", []),
          links.get(PELLINGS))
    check("the liar test: Quentin, who only SAYS he is from Millbrook, holds no Millbrook link",
          knowledge.knows_about(quentin, "millbrook") == [] and knowledge.knows_about(quentin, "loc.millbrook") == [])
    check("Aren does hold Millbrook links", len(knowledge.knows_about(aren, "millbrook")) >= 2)
    check("Quentin holds the city's festival", any(b.get("claim") == FESTIVAL for b in quentin["current"]["vault"]))
    check("a sheet with no memberships gets nothing", knowledge.links_for({"current": {}}, world) == [])
    import lint_book
    findings = json.dumps(lint_book.lint(world, chars), default=str)
    check("lint reads the new fields as declared (no finding names knowledge or memberships)",
          "knowledge" not in findings.lower() and "memberships" not in findings.lower(), findings[:600])


def test_prompts(book):
    fest = _mind(_prompt(book, "festival", "A stranger at the table asks Aren when the city's holiday falls this year."))
    check("the festival question brings up the city's festival", FESTIVAL in fest, fest)
    reg = _mind(_prompt(book, "register", "The stranger asks how a newcomer registers with the guild."))
    check("the registration question brings up the guild's procedure", REGISTER in reg, reg)
    home = _mind(_prompt(book, "millbrook", "The stranger says he is from Millbrook too, and asks how old Sheriff Ambrose is keeping."))
    check("Millbrook brings up the sheriff, told as old", SHERIFF in home and "you last knew it years ago" in home, home)
    check("his own Millbrook memory comes up beside the village's", OWN in home, home)
    check("Ambrose's death never comes up", "died" not in home, home)
    check("no digit in what comes to mind", not re.search(r"\d", home), home)


def test_crowding():
    """Fable review 3 B1: shared knowledge written confident cannot take a character's own memory's place."""
    shared = [{"claim": "harvest custom number %s of the valley is kept by every household" % w, "confidence": 0.9,
               "provenance": "known in the valley", "durability": "durable", "links": ["harvest"],
               "shared": "loc.valley", "familiarity": "familiar"} for w in ("one two three four five six seven eight nine ten".split() * 15)]
    own = {"claim": "i helped bring the harvest in from the lower field", "confidence": 0.7, "provenance": "lived"}
    for energy in (0.51, 1.0):
        got = run_gate(["harvest"], shared + [own], {}, [], {"energy": energy, "allostatic_load": 0.0})
        n_shared = sum(1 for c in got if c.get("claim", "").startswith("harvest custom"))
        check("energy %.2f: the own memory is recalled beside 150 shared facts" % energy,
              any(c.get("claim") == own["claim"] for c in got), [c.get("claim") for c in got])
        check("energy %.2f: no more than %d shared facts recalled" % (energy, knowledge.SHARED_SLOTS),
              n_shared <= knowledge.SHARED_SLOTS, n_shared)
    # everyday adds no price, so only the floor keeps a certain, everyday shared fact from costing nothing
    certain = [dict(s, confidence=1.0, familiarity="everyday") for s in shared]
    got = run_gate(["harvest"], certain, {}, [], {"energy": 0.025, "allostatic_load": 0.0})
    check("a certain shared fact still costs something: an empty mind recalls none", got == [], len(got))
    plain = [{"claim": "the harvest %s" % i, "confidence": c, "provenance": "lived"} for i, c in enumerate((0.9, 0.6, 0.3))]
    got = [c["claim"] for c in run_gate(["harvest"], plain, {}, [], {"energy": 0.5, "allostatic_load": 0.0})]
    check("a vault with no shared link recalls as before (confidence order within the budget)",
          got == ["the harvest 0", "the harvest 1"], got)


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    print("test_knowledge")
    test_units()
    test_crowding()
    # a captured beat leaves its chronicle open until collected; on Windows an open file cannot be removed
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        book = _book(tmp)
        test_links(book)
        test_prompts(book)
        import gc
        gc.collect()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
