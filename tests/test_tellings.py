#!/usr/bin/env python3
"""test_tellings.py — what a character is TOLD becomes what they know (gate knowledge-tellings, 2026-09-29).

Invented: in a potters' kiln shed, Jory the kiln-master tells his apprentice Linnet, with Sten from the rival kiln
listening, that the new clay bed at Coldridge fires true and that Master Quarles retires at midsummer.
Linnet trusts Jory; Sten does not. What must hold, through scripts/scene.py's own main (the event seat's `told` rows are
the --stub beat's own tags here, the double the seat stands in for):
  - Linnet holds both facts, told by Jory, credited under the told ceiling; Sten holds them as Jory's claims (reported);
  - Jory holds no telling of his own; each telling carries ONE fact identity across its hearers;
  - read_api.knows returns them for Linnet as acquired, and ask.py who names both hearers of a fact about Quarles;
  - in a later scene that touches the clay, Linnet's actor is reminded of it - and, through Jory, of Quarles's news;
  - a reported rumour is priced for recall by its readiness, not its doubt (Fable review 3, 8.3).
Every name here is invented for this test.
"""
import contextlib
import copy
import gc
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import acquisition, read_api, tellings             # noqa: E402
from src.engine.gate import run_gate, _energy_budget               # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

PASS, FAIL = [], []
CLAY = "The new clay bed at Coldridge fires true"
QUARLES = "Master Quarles retires at midsummer"


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


WORLD = dict(copy.deepcopy(WORLD_ENGINE))
WORLD["lexicon"] = {"attribute_classes": {"clay": ["clay", "coldridge"], "kiln": ["kiln", "firing"]}}
WORLD["locations"] = [{"id": "kiln_shed", "what": "the kiln shed of the potters' row"}]
WORLD["people"] = [{"id": "jory", "what": "the kiln-master"}, {"id": "linnet", "what": "his apprentice"},
                   {"id": "sten", "what": "a potter from the rival kiln"},
                   {"id": "quarles", "name": "Quarles", "what": "the old master of the upper kiln"}]


def _sheet(name, relationships):
    eng = copy.deepcopy(CHAR_ENGINE)
    eng["fixed"]["name"] = name
    eng["current"]["relationships"] = relationships
    eng["current"]["location"] = "kiln_shed"
    return "---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(eng, indent=1))


def _edge(trust):
    return {"trust": trust, "affinity": 0.5, "respect": 0.5, "debt": 0.0}


def _book(tmp):
    book = os.path.join(tmp, "Kiln Fixture")
    for sub in ("world", "characters", "scenes", "runs"):
        os.makedirs(os.path.join(book, sub))
    with open(os.path.join(book, "world", "Potters Row.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\nid: Potters Row\n---\n# Potters Row\n\n```json\n%s\n```\n" % json.dumps(WORLD, indent=1))
    for name, rels in (("Jory", {"linnet": _edge(0.6), "sten": _edge(0.5)}),
                       ("Linnet", {"jory": _edge(0.8), "sten": _edge(0.5)}),
                       ("Sten", {"jory": _edge(0.2), "linnet": _edge(0.5)})):
        with open(os.path.join(book, "characters", name + ".md"), "w", encoding="utf-8") as fh:
            fh.write(_sheet(name, rels))
    return book


class _Captured(Exception):
    def __init__(self, messages):
        super().__init__("captured")
        self.messages = messages


def _run(book, name, situation, cast, db, budget, resume=None, capture=None):
    """One scene through scripts/scene.py main. Jory's first beat carries the two tellings; `capture` stops at that
    character's first beat and returns their user message."""
    import scene
    import direct
    cfg = os.path.join(book, "scenes", name + "_cfg.json")
    with open(cfg, "w", encoding="utf-8") as fh:
        json.dump({"name": name, "at": {"day": 1, "time": "18:00" if not resume else "19:00"}, "situation": situation,
                   "cast": [{"id": c, "drive": "finish the day's work"} for c in cast]}, fh)
    real = scene.faithful_turn
    state = {"told": False}

    def fake(packet, event_text, temperament, model, stub, **kw):
        if capture and kw.get("char_id") == capture:
            raise _Captured(scene.build_turn_messages(
                packet, event_text, temperament, kw.get("relationships"), acts=kw.get("acts", ()),
                rung_direction=direct.rung_direction(packet, brief=kw.get("brief", ""), model=model, stub=stub)))
        turn, leaks = real(packet, event_text, temperament, model, stub, **kw)
        if kw.get("char_id") == "jory" and not state["told"]:
            state["told"] = True
            turn = dict(turn, action='Jory taps the cooling jar. "%s. %s."' % (CLAY, QUARLES), addressee="linnet")
            turn["tags"] = dict(turn.get("tags") or {}, told=[{"what": CLAY, "to": "linnet", "cost": "none"},
                                                              {"what": QUARLES, "to": "linnet", "cost": "none"}])
        return turn, leaks
    argv = sys.argv
    sys.argv = (["scene.py", "--book", book, "--scene", cfg, "--stub", "--no-keeper", "--budget", str(budget), "--db", db]
                + (["--resume", resume] if resume else []))
    scene.faithful_turn = fake
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            scene.main()
    except _Captured as cap:
        return "\n".join(m["content"] for m in cap.messages if m.get("role") == "user"), state
    except SystemExit as e:
        if e.code not in (None, 0):
            raise AssertionError("scene %s exited %r:\n%s" % (name, e.code, log.getvalue()[-2000:]))
    finally:
        scene.faithful_turn, sys.argv = real, argv
    if capture:
        raise AssertionError("scene %s ended before %s's beat:\n%s" % (name, capture, log.getvalue()[-1500:]))
    return log.getvalue(), state


def _acquired(db, char):
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    try:
        return [json.loads(r[0]) for r in con.execute("SELECT belief FROM acquisitions WHERE char_id=? ORDER BY acquisition_id", (char,))]
    finally:
        con.close()


def test_the_telling_is_known(book, db):
    print("\n[1] a telling becomes what its hearers know")
    log, state = _run(book, "news", "Evening in the kiln shed; the last firing is cooling.", ["jory", "linnet", "sten"],
                      db, 4)
    check("Jory spoke and told (the fixture reached its beat)", state["told"], log[-800:])
    linnet = [b for b in _acquired(db, "linnet") if b.get("told")]
    sten = [b for b in _acquired(db, "sten") if b.get("told")]
    jory = [b for b in _acquired(db, "jory") if b.get("told")]
    l_claims = {b["claim"]: b for b in linnet}
    trusting, _ = acquisition.credit(0.8)
    check("Linnet holds both facts, told by Jory", set(l_claims) == {CLAY, QUARLES}
          and all(b["provenance"] == "told by Jory" for b in linnet), [(b["claim"], b["provenance"]) for b in linnet])
    check("...credited by her trust, under the told ceiling", all(b["confidence"] == trusting < 0.9 for b in linnet),
          [b["confidence"] for b in linnet])
    check("...and as ready as any telling", all(b.get("readiness") == tellings.READINESS for b in linnet), linnet)
    doubt, reported = acquisition.credit(0.2)
    s_claims = {b["claim"] for b in sten}
    check("Sten, who does not trust Jory, holds them as Jory's claims", reported and s_claims ==
          {"Jory claims: %s" % CLAY, "Jory claims: %s" % QUARLES} and all(b["provenance"] == "reported" for b in sten),
          sorted(s_claims))
    check("...credited low", all(b["confidence"] == doubt for b in sten), [b["confidence"] for b in sten])
    check("Jory holds no telling of his own", jory == [], jory)
    clay_ids = {b["fact"] for b in linnet + sten if CLAY in b["claim"]}
    check("one telling, one fact identity across its hearers", len(clay_ids) == 1 and next(iter(clay_ids)).endswith(".jory.0"),
          clay_ids)
    check("the kiln news is about Quarles (named, so registered)", "quarles" in l_claims.get(QUARLES, {}).get("about", []),
          l_claims.get(QUARLES))
    return state


def test_asking(book, db):
    print("\n[2] the engine answers who knows it")
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    con.row_factory = sqlite3.Row                      # read_api reads rows by name, as every engine reader does
    try:
        run_id = con.execute("SELECT run_id FROM runs").fetchone()[0]
        got = read_api.knows(con, run_id, "linnet", 10 ** 6)
    finally:
        con.close()
    rows = [r for r in got.rows if CLAY == str(r["belief"].get("claim"))]
    check("read_api.knows returns the clay bed for Linnet, as acquired", len(rows) == 1 and rows[0].get("source") == "acquired",
          got.rows)
    p = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "ask.py"), "who", "--book", book, "--db", db,
                        "--run", run_id, "--about", "quarles"], capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    try:
        out = json.loads(p.stdout)
    except ValueError:
        out = {"raw": p.stdout[-400:], "err": p.stderr[-400:]}
    holders = sorted(h.get("char") for h in (out.get("holders") or []))
    check("ask.py who --about quarles names both hearers, not the teller", holders == ["linnet", "sten"]
          and "jory" in (out.get("hold_nothing") or []), out)
    return run_id


def _mind(user_text):
    m = re.search(r"What it brings to mind:[ \t]*([^\n]*)", user_text)
    return m.group(1) if m else ""


def test_it_comes_back(book, db, run_id):
    print("\n[3] a later scene that touches it brings it back - and what was told with it")
    user, _ = _run(book, "later", "Linnet wedges a lump of clay from Coldridge at the bench.",
                   ["linnet"], db, 1, resume=run_id, capture="linnet")
    mind = _mind(user)
    check("Linnet is reminded that the clay bed fires true, told by Jory", CLAY in mind and "told by Jory" in mind,
          mind or user[-800:])
    check("...and of Quarles's news he told with it (the teller joins them)", QUARLES in mind, mind)


def test_readiness_prices_a_rumour():
    print("\n[4] a doubted rumour is priced by how readily it comes back, not by its doubt")
    doubt, _ = acquisition.credit(0.2)
    rumour = {"claim": "Jory claims: %s" % CLAY, "confidence": doubt, "readiness": tellings.READINESS,
              "provenance": "reported", "durability": "durable", "links": ["jory"]}
    cond = {"energy": 0.4, "allostatic_load": 0.0}
    budget = _energy_budget(cond)
    check("the fixture's budget sits between the two prices", 1 - tellings.READINESS <= budget < 1 - doubt,
          (budget, 1 - tellings.READINESS, 1 - doubt))
    got = run_gate(["clay"], [rumour], {}, [], cond)
    check("the rumour comes to mind on a budget its doubt could not pay", [r["claim"] for r in got] == [rumour["claim"]], got)
    plain = {k: v for k, v in rumour.items() if k != "readiness"}
    check("control: the same belief priced by its doubt does not", run_gate(["clay"], [plain], {}, [], cond) == [])


def test_a_dragged_neighbour_waits_its_turn():
    print("\n[5] what the scene touched ranks ahead of what it dragged along")
    slow = {"claim": "The clay is slow to dry this week.", "confidence": 0.6, "provenance": "lived"}       # costs .4
    bed = {"claim": CLAY, "confidence": 0.7, "provenance": "told by Jory", "links": ["jory"]}                # costs .3
    owes = {"claim": "Jory owes Linnet two days' wages.", "confidence": 0.95, "provenance": "told by Jory",
            "links": ["jory"]}                                                                            # costs .05
    cond = {"energy": 0.72, "allostatic_load": 0.0}
    budget = _energy_budget(cond)
    check("the fixture's budget pays both direct matches and not the neighbour too", 0.7 <= budget < 0.75, budget)
    got = run_gate(["clay"], [slow, bed, owes], {}, [], cond)
    claims = [r["claim"] for r in got]
    check("both beliefs the scene touched come to mind", slow["claim"] in claims and CLAY in claims, claims)
    check("the sure neighbour told with one of them does not take a direct match's place", owes["claim"] not in claims, claims)
    roomy = run_gate(["clay"], [slow, bed, owes], {}, [], {"energy": 1.0, "allostatic_load": 0.0})
    check("control: with room, the neighbour comes along (dragged, a leap)",
          [r.get("hops") for r in roomy if r["claim"] == owes["claim"]] == [2], roomy)


def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        book = _book(tmp)
        db = os.path.join(book, "runs", "kiln.db")
        test_the_telling_is_known(book, db)
        run_id = test_asking(book, db)
        test_it_comes_back(book, db, run_id)
        gc.collect()
    test_readiness_prices_a_rumour()
    test_a_dragged_neighbour_waits_its_turn()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
