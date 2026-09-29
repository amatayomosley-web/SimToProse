#!/usr/bin/env python3
"""test_facts.py — facts proposed from a world note, kept only by the author's words (gate knowledge-proposals).

Invented: a weaving town's ways, written as a world note with one fenced passage of author-only truth. Through
scripts/facts.py as a subprocess (the command the partner runs), what must hold:
  - `propose` gives the proposer the note's visible prose and the world's registry - never the fenced truth;
  - `check` keeps a fact whose evidence is the note's own sentence, and refuses, by name, one quoting the fenced truth,
    one quoting words the note does not hold, two facts in one claim, an unregistered holder and an unknown field, and
    flags one the world already knows;
  - `approve` refuses without the author's words, refuses a refused number, and with them writes the kept facts to
    <book>/knowledge/<note>.md; a second approval adds no duplicate; a note changed since its check is refused;
  - the book then loads them: a member's vault holds the kept custom, with the words it came from; a stranger's does not.
Every name here is invented for this test.
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
ROW = "A weaver finishes every row she starts, and to leave a row half-woven is to shame the loom."
FLOODS = "The sheds close for the whole of the shearing month."
TIDE = "The dye vats are emptied at each new season and the stream runs blue for a week."
TRUTH = "The first shed was raised on a bet between two brothers, and no one living remembers which of them won."
CHANNELS = "Children learn to card wool before they learn their letters."
NOTE = ("---\ntype: culture\n---\n# The Ways of Ashcombe\n\nThe weaving sheds of Ashcombe stand along the hillside. %s %s %s\n\n"
        "%%%% truth %%%%\n%s\n%%%% /truth %%%%\n\n%s\n" % (ROW, FLOODS, TIDE, TRUTH, CHANNELS))


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


WORLD = dict(copy.deepcopy(WORLD_ENGINE))
WORLD["lexicon"] = {"attribute_classes": {"loom": ["loom", "shuttle", "row", "woven"]}}
WORLD["locations"] = [{"id": "ashcombe", "name": "Ashcombe", "what": "a weaving town in the hills"}]
WORLD["people"] = [{"id": "ottilie", "what": "a baker", "groups": ["ashcombe-folk"]},
                   {"id": "florian", "what": "a wool buyer from the lowlands"}]
WORLD["knowledge"] = [{"claim": CHANNELS, "held_by": ["grp.ashcombe-folk"]}]
REPLY = {"facts": [
    {"claim": "A weaver finishes every row she starts.", "held_by": ["grp.ashcombe-folk"], "norm": True,
     "sanction": "To leave a row half-woven shames the loom.", "topic": "loom", "evidence": ROW},             # 1 kept
    {"claim": "The first shed was raised on a bet.", "held_by": ["grp.ashcombe-folk"], "evidence": TRUTH},  # 2 truth
    {"claim": "Ashcombe folk love their looms.", "held_by": ["grp.ashcombe-folk"], "evidence": "Ashcombe folk love their looms."},  # 3
    {"claim": "The dye vats are emptied each season. The stream runs blue for a week.", "held_by": ["grp.ashcombe-folk"], "evidence": TIDE},  # 4
    {"claim": FLOODS, "held_by": ["grp.river-folk"], "evidence": FLOODS},                                      # 5 holder
    {"claim": CHANNELS, "held_by": ["grp.ashcombe-folk"], "evidence": CHANNELS},                                  # 6 known
    {"claim": FLOODS, "held_by": ["grp.ashcombe-folk"], "evidence": FLOODS},                                        # 7 kept
    {"claim": FLOODS, "held_by": ["grp.ashcombe-folk"], "evidence": FLOODS, "mood": "wry"},                         # 8 field
]}


def _sheet(name, memberships):
    eng = copy.deepcopy(CHAR_ENGINE)
    eng["fixed"]["name"] = name
    eng["current"]["memberships"] = memberships
    eng["current"]["relationships"] = {}
    return "---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(eng, indent=1))


def _book(tmp):
    book = os.path.join(tmp, "Ashcombe Fixture")
    for sub in ("world", "characters", "scenes", "runs"):
        os.makedirs(os.path.join(book, sub))
    with open(os.path.join(book, "world", "Ashcombe.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\nid: Ashcombe\n---\n# Ashcombe\n\n```json\n%s\n```\n" % json.dumps(WORLD, indent=1))
    with open(os.path.join(book, "world", "Ashcombe Ways.md"), "w", encoding="utf-8") as fh:
        fh.write(NOTE)
    for name, ms in (("Ottilie", [{"of": "grp.ashcombe-folk"}]), ("Florian", [])):
        with open(os.path.join(book, "characters", name + ".md"), "w", encoding="utf-8") as fh:
            fh.write(_sheet(name, ms))
    return book


def facts(*args):
    p = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "facts.py")] + list(args), capture_output=True,
                       text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return p.returncode, p.stdout, p.stderr


def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        book = _book(tmp)
        print("\n[1] propose: the visible prose and the registry, never the author's truth")
        rc, out, err = facts("propose", "--book", book, "--note", "Ashcombe Ways")
        check("propose runs", rc == 0, err)
        check("...and shows the note's prose", ROW in out and CHANNELS in out, out[-600:])
        check("...never its fenced author-only truth", "two brothers" not in out and "which of them won" not in out)
        check("...with the world's holders, people and topics", "grp.ashcombe-folk" in out and "ottilie" in out and "loom" in out)

        print("\n[2] check: kept or refused, each by name")
        reply = os.path.join(tmp, "reply.json")
        with open(reply, "w", encoding="utf-8") as fh:
            json.dump(REPLY, fh)
        rc, out, err = facts("check", "--book", book, "--note", "Ashcombe Ways", "--reply", reply)
        check("check runs", rc == 0, err)
        v = {x["n"]: x for x in (json.loads(out).get("verdicts") if rc == 0 else [])}
        check("1 (the custom, copied evidence) is kept", v.get(1, {}).get("ok") is True, v.get(1))
        for n, code in ((2, "FACTS_EVIDENCE_IS_AUTHOR_TRUTH"), (3, "FACTS_EVIDENCE_NOT_IN_NOTE"), (4, "FACTS_TWO_FACTS"),
                        (5, "KNOWLEDGE_HOLDER_UNREGISTERED"), (6, "FACTS_ALREADY_KNOWN"), (8, "FACTS_FIELD_UNKNOWN")):
            check("%d is refused: %s" % (n, code), v.get(n, {}).get("ok") is False and code in v.get(n, {}).get("why", ""),
                  v.get(n))
        check("7 (a plain fact, copied evidence) is kept", v.get(7, {}).get("ok") is True, v.get(7))
        check("the verdicts are saved for approve",
              os.path.isfile(os.path.join(book, "staging", "facts", "Ashcombe Ways.proposals.json")))

        print("\n[3] approve: only the author's words keep a fact")
        rc, out, err = facts("approve", "--book", book, "--note", "Ashcombe Ways", "--keep", "1,7", "--words", "  ")
        check("without words: refused (FACTS_WORDS_MISSING)", rc == 1 and "FACTS_WORDS_MISSING" in err, err)
        rc, out, err = facts("approve", "--book", book, "--note", "Ashcombe Ways", "--keep", "1,2", "--words", "keep them")
        check("a refused number: refused (FACTS_KEEP_REFUSED)", rc == 1 and "FACTS_KEEP_REFUSED" in err, err)
        target = os.path.join(book, "knowledge", "Ashcombe Ways.md")
        check("...and nothing was written", not os.path.exists(target))
        words = "Yes, keep the row custom and the shearing month."
        rc, out, err = facts("approve", "--book", book, "--note", "Ashcombe Ways", "--keep", "1,7", "--words", words)
        check("with words: kept", rc == 0 and json.loads(out).get("added") == [1, 7], out + err)
        note = vault.parse_note(target) if os.path.isfile(target) else {"engine": None, "body": ""}
        kept = (note["engine"] or {}).get("knowledge") or []
        check("the knowledge note holds the two facts, with their evidence and source",
              len(kept) == 2 and all(f.get("evidence") and f.get("source") == "Ashcombe Ways" for f in kept), kept)
        check("...and the author's words", words in note["body"], note["body"][-400:])
        rc, out, err = facts("approve", "--book", book, "--note", "Ashcombe Ways", "--keep", "1", "--words", "again")
        check("a second approval adds no duplicate", rc == 0 and json.loads(out).get("added") == []
              and json.loads(out).get("facts") == 2, out + err)
        rc, out, err = facts("list", "--book", book)
        check("list shows the knowledge note", rc == 0 and json.loads(out)["knowledge_notes"][0]["facts"] == 2, out + err)

        print("\n[4] the book loads what was kept")
        world, chars = vault.load_book(book)
        mine = [b for b in chars["ottilie"]["current"].get("vault") or [] if b.get("norm")]
        check("Ottilie holds the kept custom as the way of the ashcombe folk, with the words it came from",
              len(mine) == 1 and "finishes every row" in mine[0]["claim"] and mine[0].get("evidence") == ROW, mine)
        check("Florian, a stranger, holds nothing of it",
              not [b for b in chars["florian"]["current"].get("vault") or [] if b.get("shared")])

        print("\n[5] a note changed after its check is checked again")
        with open(os.path.join(book, "world", "Ashcombe Ways.md"), "a", encoding="utf-8") as fh:
            fh.write("\nSwallows nest under the shed eaves.\n")
        rc, out, err = facts("approve", "--book", book, "--note", "Ashcombe Ways", "--keep", "7", "--words", "keep it")
        check("approve refuses a stale check (FACTS_NO_PROPOSALS)", rc == 1 and "FACTS_NO_PROPOSALS" in err, err)

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
