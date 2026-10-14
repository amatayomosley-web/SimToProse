#!/usr/bin/env python3
"""test_placement.py — place a person in the bands whose rules they meet, and list what they then know (gate place-a-person).

The owner, 2026-10-13: a folktale saved for town X, forgotten, then a character from town X written as never having
heard of it - "What guards against this?" This does: placing a person reads their sheet (where they live and have lived,
their people), lists the bands whose TYPED rule they meet, lists the bands only the author can judge with the reason,
and writes the confirmed ones - on the author's words - to <book>/memberships/<person>.md, which the book loads into
current.memberships. A band whose rule needs a ROLE is always the author's to judge: fixed.position is prose told to
the actor word for word, and a match is never claimed from prose. `knows` then lists what the person holds, by band.

Invented fixture: Saltmarsh, a Lowland river town, and Odo, a ferryman raised there. Through scripts/place.py.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import vault                                       # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


BELL = "The drowned bell rings before a flood."
RIVER = "The river is owed a coin at every crossing."
HIGH = "The hill forts light beacons at midwinter."

WORLD = dict(copy.deepcopy(WORLD_ENGINE))
WORLD["locations"] = [{"id": "saltmarsh", "name": "Saltmarsh", "what": "a river town on stilts"},
                      {"id": "ferry", "what": "the ferry landing"},
                      {"id": "highfold", "name": "Highfold", "what": "a hill fort"}]
WORLD["people"] = [{"id": "odo", "what": "a ferryman"}]
WORLD["bands"] = [
    {"id": "lowland-folk", "kind": "people", "rule": "everyone raised in the Lowlands", "requires": {"nation": "Lowlander"}},
    {"id": "saltmarsh-folk", "kind": "place-folk", "rule": "everyone who grew up in Saltmarsh", "requires": {"place": "saltmarsh"}},
    {"id": "highfold-folk", "kind": "place-folk", "rule": "everyone of Highfold", "requires": {"place": "highfold"}},
    {"id": "ferry-crews", "kind": "guild", "rule": "who works a ferry", "requires": {"place": "saltmarsh", "role": "ferryman"}},
    {"id": "bell-ringers", "kind": "order", "rule": "the old women who keep the drowned-bell tale"}]
WORLD["knowledge"] = [{"claim": BELL, "held_by": ["grp.saltmarsh-folk"]},
                      {"claim": RIVER, "held_by": ["grp.lowland-folk"]},
                      {"claim": HIGH, "held_by": ["grp.highfold-folk"]}]


def _book(tmp):
    book = os.path.join(tmp, "Saltmarsh Fixture")
    for sub in ("world", "characters"):
        os.makedirs(os.path.join(book, sub))
    with open(os.path.join(book, "world", "World.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\n---\n```json\n%s\n```\n" % json.dumps(WORLD, indent=1))
    eng = copy.deepcopy(CHAR_ENGINE)
    eng["fixed"]["name"] = "Odo"
    eng["fixed"]["people"] = "Lowlander"
    eng["fixed"]["position"] = "a ferryman of Saltmarsh"
    eng["current"]["location"] = "ferry"
    eng["current"]["memberships"] = [{"of": "loc.saltmarsh", "left": "2y"}]
    with open(os.path.join(book, "characters", "Odo.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: character\n---\n# Odo\n\n```json\n%s\n```\n" % json.dumps(eng, indent=1))
    return book


def place(*args):
    p = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "place.py")] + list(args), capture_output=True,
                       text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    try:
        out = json.loads(p.stdout)
    except ValueError:
        out = {"raw": p.stdout}
    return p.returncode, out, p.stderr


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    print("test_placement")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        book = _book(tmp)
        print("candidates")
        rc, out, err = place("candidates", "--book", book, "--person", "odo")
        check("candidates runs", rc == 0, err or out)
        matched = {m.get("band"): m for m in out.get("matched") or []}
        by_hand = {m.get("band"): m for m in out.get("check_by_hand") or []}
        check("his people match the Lowland band", "grp.lowland-folk" in matched, out)
        check("a place he lived (a loc. membership, even one he left) matches the town's folk", "grp.saltmarsh-folk" in matched, out)
        check("a town he never lived in is not listed", "grp.highfold-folk" not in matched and "grp.highfold-folk" not in by_hand, out)
        check("a band needing a role is the author's to judge, never matched from prose",
              "grp.ferry-crews" in by_hand and "grp.ferry-crews" not in matched
              and "fixed.position" in str(by_hand["grp.ferry-crews"].get("why")), by_hand.get("grp.ferry-crews"))
        check("a band with a plain-words rule only is the author's to judge, its rule shown",
              by_hand.get("grp.bell-ringers", {}).get("rule") == "the old women who keep the drowned-bell tale", by_hand)
        check("each match says why", "saltmarsh" in str(matched.get("grp.saltmarsh-folk", {}).get("why")), matched)
        print("confirm")
        rc, out, err = place("confirm", "--book", book, "--person", "odo", "--keep", "grp.saltmarsh-folk,grp.lowland-folk")
        check("confirm refuses without the author's words", rc != 0 and "PLACE_WORDS_MISSING" in err, err)
        rc, out, err = place("confirm", "--book", book, "--person", "odo", "--keep", "grp.nobody", "--words", "yes")
        check("confirm refuses a band the world does not register", rc != 0 and "PLACE_BAND_UNREGISTERED" in err, err)
        rc, out, err = place("confirm", "--book", book, "--person", "odo", "--keep", "grp.saltmarsh-folk,grp.lowland-folk",
                             "--words", "Odo grew up in Saltmarsh")
        check("confirm writes the memberships note", rc == 0 and os.path.isfile(os.path.join(book, "memberships", "odo.md")),
              err or out)
        with open(os.path.join(book, "characters", "Odo.md"), encoding="utf-8") as fh:
            sheet = fh.read()
        check("the author's own sheet is not written", "saltmarsh-folk" not in sheet)
        world, chars = vault.load_book(book)
        ms = [m.get("of") for m in chars["odo"]["current"].get("memberships") or []]
        check("the book loads them into current.memberships, after the sheet's own",
              ms == ["loc.saltmarsh", "grp.saltmarsh-folk", "grp.lowland-folk"], ms)
        claims = [b.get("claim") for b in chars["odo"]["current"].get("vault") or []]
        check("he now holds the town's tale and his people's custom, not the hill fort's",
              BELL in claims and RIVER in claims and HIGH not in claims, claims)
        rc, out, err = place("confirm", "--book", book, "--person", "odo", "--keep", "grp.saltmarsh-folk", "--words", "again")
        world, chars = vault.load_book(book)
        ms = [m.get("of") for m in chars["odo"]["current"].get("memberships") or []]
        check("a second confirm adds no duplicate", rc == 0 and ms.count("grp.saltmarsh-folk") == 1, ms)
        rc, out, err = place("candidates", "--book", book, "--person", "odo")
        check("a band he is placed in is listed as already held, not again", "grp.saltmarsh-folk" in (out.get("already") or [])
              and "grp.saltmarsh-folk" not in {m.get("band") for m in out.get("matched") or []}, out)
        print("knows")
        rc, out, err = place("knows", "--book", book, "--person", "odo")
        held = out.get("by_holder") or {}
        check("knows lists what he holds, by band", rc == 0 and BELL in held.get("grp.saltmarsh-folk", [])
              and RIVER in held.get("grp.lowland-folk", []), out)
        check("knows never lists what he does not hold", HIGH not in json.dumps(out), out)
        rc, out, err = place("knows", "--book", book, "--person", "nobody")
        check("an unknown person is refused by name", rc != 0 and "VAULT_CHARACTER_UNKNOWN" in err, err)
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
