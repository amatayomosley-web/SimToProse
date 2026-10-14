#!/usr/bin/env python3
"""test_default_holder.py — a fact's holder defaults from where its text is written (gate facts-default-holder, 2026-10-13).

The owner, 2026-10-13: "How do we ask who should know this info so we can assign individuals?" A fact still cannot be
saved without holders; what changes is who names them. The extraction pass proposes the holder from WHERE the note
sits - a note a band `defines`, a town's note, a nation's folder - and the author answers only the exceptions, keeping
the defaulted facts as one batch. When the default comes from a typed thing (a town, a nation) and the band that holds
it has no typed rule for it yet, the check says what `requires` the band should carry, so placing a person from that
town finds the band without anyone remembering it.

Invented fixture: the river town of Saltmarsh in the Lowlands. Through scripts/facts.py as a subprocess.
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

from src.engine import proposals, vault                            # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


BELL = "The drowned bell rings before a flood."
EELS = "Nobody eats eel on a feast day."
FERRY = "The ferry does not cross after dark."
COUNCIL = "The council meets in the bell tower."
TOWN_NOTE = "---\ntype: place\n---\n# Saltmarsh\n\n%s %s %s\n" % (BELL, EELS, FERRY)
GUILD_NOTE = "---\ntype: guild\n---\n# Lantern Guild\n\n%s\n" % COUNCIL

WORLD = dict(copy.deepcopy(WORLD_ENGINE))
WORLD["locations"] = [{"id": "saltmarsh", "name": "Saltmarsh", "what": "a river town on stilts"}]
WORLD["people"] = [{"id": "odo", "what": "a ferryman"}]
WORLD["bands"] = [{"id": "saltmarsh-folk", "kind": "place-folk", "rule": "everyone who grew up in Saltmarsh",
                   "nation": "the Lowlands"},
                  {"id": "lantern-guild", "kind": "guild", "rule": "the sworn wick-trimmers", "defines": ["Lantern Guild"]},
                  {"id": "ferry-crews", "kind": "guild", "rule": "who works the ferry"}]
REPLY = {"facts": [
    {"claim": BELL, "evidence": BELL},                                                     # 1 defaulted
    {"claim": EELS, "held_by": [], "evidence": EELS},                                      # 2 defaulted (empty list)
    {"claim": FERRY, "held_by": ["grp.ferry-crews"], "evidence": FERRY},                   # 3 the author's exception
]}


def _book(tmp):
    book = os.path.join(tmp, "Saltmarsh Fixture")
    for sub in ("world", "characters", os.path.join("places", "the Lowlands"), "guilds", "notes"):
        os.makedirs(os.path.join(book, sub))
    with open(os.path.join(book, "world", "World.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\n---\n```json\n%s\n```\n" % json.dumps(WORLD, indent=1))
    with open(os.path.join(book, "places", "the Lowlands", "Saltmarsh.md"), "w", encoding="utf-8") as fh:
        fh.write(TOWN_NOTE)
    with open(os.path.join(book, "notes", "Weather.md"), "w", encoding="utf-8") as fh:
        fh.write(TOWN_NOTE.replace("# Saltmarsh", "# Weather"))
    with open(os.path.join(book, "guilds", "Lantern Guild.md"), "w", encoding="utf-8") as fh:
        fh.write(GUILD_NOTE)
    eng = copy.deepcopy(CHAR_ENGINE)
    eng["current"]["memberships"] = [{"of": "grp.saltmarsh-folk"}]
    with open(os.path.join(book, "characters", "Odo.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: character\n---\n```json\n%s\n```\n" % json.dumps(eng, indent=1))
    return book


def facts(*args):
    p = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "facts.py")] + list(args), capture_output=True,
                       text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return p.returncode, p.stdout, p.stderr


def test_unit():
    print("default_holder")
    dh = getattr(proposals, "default_holder", None)
    check("proposals.default_holder exists", callable(dh))
    if not callable(dh):
        return
    got = dh("guilds/Lantern Guild.md", WORLD)
    check("a note a band defines -> that band", got.get("holder") == "grp.lantern-guild", got)
    got = dh("places/the Lowlands/Saltmarsh.md", WORLD)
    check("a town's note -> the place-folk band named for that town (<loc id>-...)",
          got.get("holder") == "grp.saltmarsh-folk", got)
    check("...and the band is told the typed rule it lacks: requires.place", got.get("requires") == {"place": "saltmarsh"}, got)
    w = dict(WORLD, bands=[dict(WORLD["bands"][0], requires={"place": "saltmarsh"})])
    got = dh("places/the Lowlands/Saltmarsh.md", w)
    check("a band already typed for the town needs no suggestion", got.get("holder") == "grp.saltmarsh-folk"
          and not got.get("requires"), got)
    got = dh("places/Saltmarsh.md", dict(WORLD, bands=[]))
    check("a town with no band of its own -> the place itself", got.get("holder") == "loc.saltmarsh", got)
    got = dh("notes/Weather.md", WORLD)
    check("a note under nothing the world registers -> no default", got.get("holder") is None, got)


def test_flow():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        book = _book(tmp)
        print("propose")
        rc, out, err = facts("propose", "--book", book, "--note", "Saltmarsh")
        check("propose runs", rc == 0, err)
        check("...and names the note's default holder, asking only for exceptions",
              "DEFAULT HOLDER" in out and "grp.saltmarsh-folk" in out, out[-700:])
        print("check")
        reply = os.path.join(tmp, "reply.json")
        with open(reply, "w", encoding="utf-8") as fh:
            json.dump(REPLY, fh)
        rc, out, err = facts("check", "--book", book, "--note", "Saltmarsh", "--reply", reply)
        check("check runs", rc == 0, err)
        try:
            got = json.loads(out)
        except ValueError:
            got = {}
        v = {x["n"]: x for x in got.get("verdicts") or []}
        check("a proposal with no holder is kept, held by the default",
              v.get(1, {}).get("ok") and v[1]["fact"].get("held_by") == ["grp.saltmarsh-folk"], v.get(1))
        check("...and marked as defaulted", v.get(1, {}).get("defaulted") is True and v.get(2, {}).get("defaulted") is True, v)
        check("an empty holder list defaults the same way", v.get(2, {}).get("fact", {}).get("held_by") == ["grp.saltmarsh-folk"], v.get(2))
        check("the author's exception keeps its own holder, not defaulted",
              v.get(3, {}).get("fact", {}).get("held_by") == ["grp.ferry-crews"] and not v.get(3, {}).get("defaulted"), v.get(3))
        check("the check says what requires the band lacks", got.get("band_requires") ==
              {"band": "grp.saltmarsh-folk", "requires": {"place": "saltmarsh"}}, got.get("band_requires"))
        rc, out, err = facts("check", "--book", book, "--note", "Weather", "--reply", reply)
        try:
            w1 = {x["n"]: x for x in json.loads(out).get("verdicts") or []}.get(1, {})
        except ValueError:
            w1 = {"why": out + err}
        check("a note with no default refuses a holderless fact as before",
              not w1.get("ok") and "KNOWLEDGE_HELD_BY_EMPTY" in str(w1.get("why")), w1)
        print("approve")
        rc, out, err = facts("approve", "--book", book, "--note", "Saltmarsh", "--keep", "defaulted",
                             "--words", "the town's lore, as a batch")
        check("approve --keep defaulted keeps the defaulted batch", rc == 0 and json.loads(out or "{}").get("kept") == [1, 2],
              out + err)
        world, chars = vault.load_book(book)
        claims = [b.get("claim") for b in chars["odo"]["current"].get("vault") or []]
        check("a member of the town's folk holds the batch", BELL in claims and EELS in claims and FERRY not in claims, claims)



def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    print("test_default_holder")
    test_unit()
    test_flow()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
