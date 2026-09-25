#!/usr/bin/env python3
"""test_one_name.py — a name means one person (gate one-person-per-name, 2026-09-25).

THE OWNER: "The scene calls character, younger versions is a character" - a younger Mira is a character of their own,
with their own sheet and a place among the world's people (an id beginning with the name, `mira_young`, named Mira).
Then, on the plan he approved: a name means one person - whoever of that name is in the room; if no one is, whoever
the story is at (the one who first walked on at or before the scene's time, the latest if several); if neither has
appeared yet, as before. Until this gate "Mira" named BOTH (the engine matches a person on the first part of their
id), so a flashback with the young Mira in the room made the grown one a third party spoken of, and the chair logged
its character by NAME, so the young Mira played there would have written into the grown one's record.

  [1] the rule itself (presence.one_per_name), the edge fallback and the present-unnamed lookup
  [2] present day, the grown Mira in the room: the name, the edge, the prompt's mask, the leak check, an overheard name
  [3] a flashback with the young Mira in the room: the grown Mira is not perceived, referenced, stood with, or moved;
      and the notice's advice names the recipe
  [4] neither in the room: later in the story "Mira" is the grown one, earlier the young one
  [5] the chair plays the young Mira under her own id

Scenes run through scripts/scene.py main IN PROCESS with the seats faked. Script-style: check(), main(), exit code.
"""
import contextlib
import glob
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import faithfulness, gate, presence, rungs          # noqa: E402
from src.engine.records import Reading, RecordError                 # noqa: E402
from test_condition import FLOW, _cfg                                # noqa: E402  (one fixture, several suites)
from test_systems import _book                                       # noqa: E402

FAILS = []
MIRA, ADA = {"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}
YOUNG, TOMAS = {"id": "mira_young", "drive": "climb the lamp stair"}, {"id": "tomas", "drive": "take the boat out"}
SITUATION = "Mira has left the lamp room door open, and the wind comes up the stair."
TOKEN = re.compile(r"(?<![A-Za-z0-9_])mira(?![A-Za-z0-9_])")        # the grown Mira's id; never mira_young, never "Mira"


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _engine(path):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"```json\n(.*)\n```", txt, re.S)
    return txt, m, json.loads(m.group(1))


def _put(path, txt, m, data):
    open(path, "w", encoding="utf-8").write(txt[:m.start(1)] + json.dumps(data, indent=1) + txt[m.end(1):])


def _person(book, cid, name, like, edges, what):
    """One more character: a place among the world's people and a sheet (`like`'s, renamed) under the note id `cid`."""
    wpath = os.path.join(book, "world", "The Rock.md")
    txt, m, world = _engine(wpath)
    world["people"] = world["people"] + [{"id": cid, "name": name, "what": what}]
    _put(wpath, txt, m, world)
    _t, _m, data = _engine(os.path.join(book, "characters", "%s.md" % like))
    data["fixed"]["name"] = name
    data["current"]["relationships"] = edges
    open(os.path.join(book, "characters", "%s.md" % cid), "w", encoding="utf-8").write(
        "---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (cid, name, json.dumps(data, indent=1)))


def _the_book(tmp):
    """The two keepers; the young Mira (a character of her own, named Mira); Tomas. Ada knows the young Mira only as
    "the girl", Tomas the grown one only as "the keeper" - what makes the prompt's mask, the leak check and an
    overheard name read the wrong Mira."""
    book = _book(tmp, FLOW)
    wpath = os.path.join(book, "world", "The Rock.md")
    txt, m, world = _engine(wpath)
    world["people"] = [dict(p, name=p["id"].title()) for p in world["people"]]   # a name is what gets overheard
    _put(wpath, txt, m, world)
    edge = {"trust": 0.6, "affinity": 0.6, "respect": 0.6, "debt": 0.0}
    _person(book, "mira_young", "Mira", "Mira", {"ada": dict(edge)}, "the keeper's girl")
    _person(book, "tomas", "Tomas", "Ada", {"ada": dict(edge), "mira": dict(edge, known_as="the keeper")}, "a boat hand")
    apath = os.path.join(book, "characters", "Ada.md")
    txt, m, ada = _engine(apath)
    ada["current"]["relationships"]["mira_young"] = dict(edge, known_as="the girl")
    _put(apath, txt, m, ada)
    return book


def _run(book, tmp, scenes, walkers=None):
    """Scenes through scripts/scene.py main, each after the first on a --resume; `walkers` {scene: id} walks out on
    their first line there. -> (db, run_id, outs, seen): seen = [(scene, speaker, packet + the moment it was handed,
    the relationships the prompt masks by)]."""
    import scene
    outs, seen, now = [], [], {"scene": None, "packet": None}
    real_assemble = scene.assemble

    def spy_assemble(*a, **k):
        now["packet"] = real_assemble(*a, **k)
        return now["packet"]

    def fake_turn(packet, event_text, temperament, model, stub, **k):
        seen.append((now["scene"], k.get("char_id"), dict(packet, moment=event_text), dict(k.get("relationships") or {})))
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        return ({"action": "She looks at Mira in the %s and says the wind is backing." % now["scene"], "thought": "",
                 "exit": (walkers or {}).get(now["scene"]) == k.get("char_id"), "addressee": other, "act": "",
                 "tags": {"type": "threat", "summary": "looks at Mira in the %s" % now["scene"], "dimensions": {"threat": 0.7},
                          "durability": "durable", "subject": other, "object": other,
                          "showed": {"affinity": 0.85, "trust": 0.8}}}, [])

    def refuse(*_a, **_k):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked out of this test")

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=(), **_k):
        other = next(p for p in present if p != me)
        return ([Reading(path="WARINESS", rung=rungs.rung_at("WARINESS", 0.7)[1], about=other, confidence="sure")],
                [other], "sure", [])

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, scene.assemble, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, refuse, emotion
    scene.assemble = spy_assemble
    try:
        for i, (name, day, time, lasts, budget, cast) in enumerate(scenes):
            now["scene"] = name
            argv = ["scene.py", "--book", book, "--scene",
                    _cfg(tmp, name, day, time, lasts, {"cast": cast, "situation": SITUATION}),
                    "--budget", str(budget), "--model", "fake/model", "--no-keeper"]
            if i:
                argv += ["--resume", sqlite3.connect(glob.glob(os.path.join(book, "runs", "*.db"))[0]).execute(
                    "SELECT run_id FROM runs").fetchone()[0]]
            sys.argv = argv
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                    scene.main()
            except SystemExit as e:
                out.write("\nSYSTEMEXIT %s" % e)
            outs.append(out.getvalue())
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, scene.assemble, sys.argv = saved
    db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
    return db, sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0], outs, seen


def _refs(packet):
    return {p.get("ref"): p.get("present") for p in packet["volatile"]["percepts"] if str(p.get("ref", "")).startswith("entity.")}


def _span(con, label):
    """[start, end] turns of the scene whose pinned cfg is named `label`."""
    for s, e, fp in con.execute("SELECT start_turn, end_turn, cfg_fingerprint FROM scenes ORDER BY start_turn"):
        body = con.execute("SELECT body FROM scene_cfgs WHERE fingerprint = ?", (fp,)).fetchone()
        if body and json.loads(body[0]).get("name") == label:
            return int(s), int(e)
    return None


WORDS = ("triggers", "surfaces")     # the manifest's word lists: "mira" there is the NAME heard, which recall matches as a
                                     # word (a memory of either Mira may come to mind on it) - never a person's id
PROSE = ("text", "claim", "summary", "source", "action", "thought", "said", "moment", "quote", "rationale")
                                     # what someone said or saw, as written: a stub writes it lower-cased, so the name
                                     # reads as "mira" there - words again, not a person


def _strings(value, skip=WORDS + PROSE):
    """Every string in a JSON value - keys and leaves - except under the word lists and the prose."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k not in skip:
                yield str(k)
                yield from _strings(v, skip)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v, skip)
    elif isinstance(value, str):
        yield value


def _mentions(con, lo, hi):
    """Every id-bearing cell, in every table a turn keys, between two turns, that carries the grown Mira's id ->
    [(table, column, text)]. Prose columns and prose keys are words, not people, and are left out."""
    hits = []
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall():
        cols = [r[1] for r in con.execute("PRAGMA table_info(%s)" % t)]
        if "turn" not in cols:
            continue
        for row in con.execute("SELECT * FROM %s WHERE turn BETWEEN ? AND ?" % t, (lo, hi)):
            for col, c in zip(cols, row):
                if not isinstance(c, str) or col in PROSE:
                    continue
                try:
                    texts = list(_strings(json.loads(c)))
                except ValueError:
                    texts = [c]
                hits += [(t, col, x[:160]) for x in texts if TOKEN.search(x)]
    return hits


def rule():
    print("[1] the rule")
    people = [{"id": "mira", "name": "Mira"}, {"id": "mira_young", "name": "Mira"}, {"id": "ada"}]
    own = {"mira", "mira_young", "ada"}
    began = {"mira": 1440.0, "mira_young": -5000.0}
    one = lambda here, at: presence.one_per_name(people, here, own, at, began.get)
    check("the-young-one-in-the-room:-the-name-is-hers", one(["mira_young", "ada"], -5000.0) == ["mira"])
    check("the-grown-one-in-the-room:-the-name-is-hers", one(["mira", "ada"], 3000.0) == ["mira_young"])
    check("neither,-later:-the-one-the-story-is-at-(the-latest-to-walk-on)", one(["ada"], 3000.0) == ["mira_young"])
    check("neither,-earlier:-only-the-young-one-had-walked-on", one(["ada"], -4000.0) == ["mira"])
    check("neither,-before-both-walked-on:-both,-as-before", one(["ada"], -9000.0) == [])
    check("no-clock,-no-one-in-the-room:-both,-as-before", one(["ada"], None) == [])
    check("both-in-the-room:-both", one(["mira", "mira_young"], 0.0) == [])
    check("a-name-no-one-shares-is-never-touched", presence.one_per_name(
        [{"id": "mira"}, {"id": "ada"}], ["ada"], own, 0.0, lambda c: 0.0) == [])
    tie = presence.one_per_name(people, ["ada"], own, 3000.0, lambda c: 0.0)
    check("walked-on-at-the-same-moment:-both", tie == [], tie)
    # a world written <name>_<role>, the cast in short ids: the grown one is `ren`, their place `ren_traveler`
    pb, ob = [{"id": "ren_traveler"}, {"id": "ren_young", "name": "Ren"}], {"ren", "ren_young"}
    got = presence.one_per_name(pb, ["ren"], ob, 10.0, lambda c: 0.0)
    check("a-character-of-their-own-is-in-the-room-by-their-own-id-only", got == ["ren_young"], got)
    got = presence.one_per_name(pb, ["ren_young"], ob, 10.0, lambda c: 0.0)
    check("...and-their-grown-self-drops-in-both-id-spaces", got == ["ren", "ren_traveler"], got)
    check("(the-join-that-made-it-necessary)", presence.match("ren_young", {"ren"}))
    # the edge a percept's NAME finds: without `elsewhere`, both Miras
    cur = {"relationships": {"mira": {"trust": 0.5}, "mira_young": {"trust": 0.5}}}
    pct = [{"ref": "entity.mira_young", "recognized_as": "Mira", "present": True}]
    check("(the-name-fallback-found-both)", sorted(e["target"] for e in presence.build_edges(cur, pct, {})) == ["mira", "mira_young"])
    check("the-name-fallback-skips-the-one-the-name-does-not-mean",
          [e["target"] for e in presence.build_edges(cur, pct, {}, ["mira"])] == ["mira_young"])
    got = presence.present_unnamed({"mira"}, [], {"people": [{"id": "mira_young", "what": "the girl"},
                                                             {"id": "mira", "what": "the keeper"}]}, me="ada")
    check("someone-in-the-room-is-read-by-their-own-id-first", got == [("mira", "Mira", ["the keeper"])], got)


def main():
    rule()
    tmp = tempfile.mkdtemp(prefix="one_name_")
    try:
        book = _the_book(tmp)
        scenes = (("lamp-day", 1, "08:00", "2h", 2, [MIRA, ADA]),
                  ("stair-walkout", -450, "08:00", "1h", 4, [YOUNG, ADA, TOMAS]),
                  ("girlhood", -400, "09:00", "1h", 2, [YOUNG, ADA]),
                  ("harbour-later", 3, "08:00", "1h", 2, [ADA, TOMAS]),
                  ("schoolyard-earlier", -300, "08:00", "1h", 2, [TOMAS, ADA]))
        db, run_id, outs, seen = _run(book, tmp, scenes, walkers={"stair-walkout": "mira_young"})
        check("all-five-scenes-ran", all("SYSTEMEXIT" not in o and "Traceback" not in o for o in outs),
              [o[-400:] for o in outs])
        by = lambda scene_name, who: [(p, r) for s, w, p, r in seen if s == scene_name and w == who]
        con = sqlite3.connect(db)

        print("[2] present day, the grown Mira in the room")
        ada = by("lamp-day", "ada")
        check("ada-acts-in-it", bool(ada), [(s, w) for s, w, _p, _r in seen])
        check("(the-moment-she-is-handed-names-Mira)", all("Mira" in p["moment"] for p, _r in ada), [p["moment"][:80] for p, _r in ada])
        check("mira-is-seen,-the-young-one-is-not-there", all(_refs(p).get("entity.mira") is True
              and "entity.mira_young" not in _refs(p) for p, _r in ada), [_refs(p) for p, _r in ada])
        check("ada-stands-with-the-grown-mira-only", all([e["target"] for e in p["volatile"]["edges"]] == ["mira"]
              for p, _r in ada), [[e["target"] for e in p["volatile"]["edges"]] for p, _r in ada])
        check("the-prompt-masks-by-the-mira-the-name-means", all(set(r) == {"mira"} for _p, r in ada), [sorted(r) for _p, r in ada])
        rels = ada[0][1] if ada else {}
        check("so-Mira-stays-Mira-in-ada's-prompt", gate.scope_names("Mira keeps the lamp.", rels) == "Mira keeps the lamp.",
              gate.scope_names("Mira keeps the lamp.", rels))
        check("and-saying-it-is-no-leak", faithfulness.check_name_leaks("I tell Mira the wind is up.", rels) == [])
        full = dict(rels, mira_young={"known_as": "the girl"})
        check("(with-both,-she-would-have-called-her-the-girl)", "the girl" in gate.scope_names("Mira keeps the lamp.", full))
        s1 = _span(con, "lamp-day")
        learned = [json.loads(r[0]) for r in con.execute("SELECT belief FROM acquisitions WHERE turn BETWEEN ? AND ?", s1)]
        check("hearing-the-grown-mira's-name-teaches-ada-nothing-of-the-young-one",
              not any("the girl" in b.get("claim", "") for b in learned), [b.get("claim") for b in learned])
        about = [b.get("about") for b in learned if "Mira" in b.get("claim", "")]
        check("what-the-room-remembers-of-Mira-is-about-the-grown-one", bool(about) and all(
              "mira" in a and "mira_young" not in a for a in about), about)

        print("[3] a flashback with the young Mira in the room")
        ada, young = by("girlhood", "ada"), by("girlhood", "mira_young")
        check("both-act-in-it", bool(ada) and bool(young), [(s, w) for s, w, _p, _r in seen])
        check("ada-sees-the-young-mira,-and-the-grown-one-is-nowhere-in-what-she-perceives",
              all(_refs(p).get("entity.mira_young") is True and "entity.mira" not in _refs(p) for p, _r in ada),
              [_refs(p) for p, _r in ada])
        check("ada-stands-with-the-young-mira-only", all([e["target"] for e in p["volatile"]["edges"]] == ["mira_young"]
              for p, _r in ada), [[e["target"] for e in p["volatile"]["edges"]] for p, _r in ada])
        check("the-prompt-masks-her-as-the-girl", all(set(r) == {"mira_young"} for _p, r in ada), [sorted(r) for _p, r in ada])
        s2 = _span(con, "girlhood")
        check("the-young-mira-is-logged-as-herself", {r[0] for r in con.execute(
            "SELECT actor FROM turns WHERE turn BETWEEN ? AND ?", s2)} == {"ada", "mira_young"})
        hits = _mentions(con, *s2)
        check("the-grown-mira's-record-is-untouched:-no-row-of-the-flashback-names-her", not hits, hits[:6])
        adv = outs[2].split("consider a younger", 1)[-1][:300]
        check("the-notice-advises-a-younger-ada,-with-the-recipe",
              "consider a younger Ada - a character of their own, with their own sheet and a place among the world's "
              "people (an id beginning with their name, e.g. ada_young, named Ada) - called into the scene in their place"
              in re.sub(r"\s+", " ", outs[2]), adv)
        # SHE WALKS OUT OF HER FIRST SCENE: the room no longer holds a Mira, and the time rule finds her - she walked on
        # in this very scene, so her presence is in the log by the next beat
        walk = [(w, p) for sc, w, p, _r in seen if sc == "stair-walkout"]
        out_at = next((n for n, (w, _p) in enumerate(walk) if w == "mira_young"), None)
        after = [p for _w, p in walk[out_at + 1:]] if out_at is not None else []
        check("(she-spoke,-walked-out,-and-the-scene-went-on)", bool(after), [w for w, _p in walk])
        check("after-she-walks-out-of-her-first-scene,-Mira-is-still-her,-spoken-of",
              bool(after) and all(_refs(p).get("entity.mira_young") is False and "entity.mira" not in _refs(p) for p in after),
              [_refs(p) for p in after])

        print("[4] neither Mira in the room")
        for label, meant, other in (("harbour-later", "entity.mira", "entity.mira_young"),
                                    ("schoolyard-earlier", "entity.mira_young", "entity.mira")):
            ps = [p for p, _r in by(label, "ada") + by(label, "tomas")]
            check("%s:-Mira-is-%s,-spoken-of" % (label, meant[7:]),
                  bool(ps) and all(_refs(p).get(meant) is False and other not in _refs(p) for p in ps), [_refs(p) for p in ps])
        # TOMAS KNOWS THE GROWN MIRA ONLY AS "the keeper": said aloud in the present, her name teaches him; said in the
        # past, it is the young one's name, and teaches him nothing of the keeper's
        told = lambda label: [json.loads(b)["claim"] for (b,) in con.execute(
            "SELECT belief FROM acquisitions WHERE char_id = 'tomas' AND turn BETWEEN ? AND ?", _span(con, label))]
        check("(later,-tomas-overhears-the-keeper's-name)", any("the keeper" in c for c in told("harbour-later")),
              told("harbour-later"))
        check("earlier,-the-young-mira's-name-teaches-him-nothing-of-the-keeper",
              not any("the keeper" in c for c in told("schoolyard-earlier")), told("schoolyard-earlier"))
        con.close()

        print("[5] the chair")
        # a SUPPLIED turn, durable: it passes the same walls and commit as an acted one, and leaves a lived memory -
        # whose `about` the chair stamps by the Mira the name means
        turn = {"action": "She tells Ada that Mira will mind the stair.", "thought": "",
                "tags": {"type": "threat", "summary": "Mira will mind the stair", "dimensions": {"threat": 0.7},
                         "durability": "durable"}}
        r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book, "--char", "mira_young",
                            "--stub", "--resume", run_id, "--at", "day -400 11:00", "--lasts", "10m",
                            "--circumstance", "Ada says Mira should mind the stair.", "--turn-json", "-"],
                           input=json.dumps(turn), capture_output=True, text=True, cwd=REPO, timeout=300)
        con = sqlite3.connect(db)
        head = con.execute("SELECT MAX(turn) FROM scene_clock").fetchone()[0]
        actors = [a for (a,) in con.execute("SELECT actor FROM turns WHERE turn >= ?", (head,))]
        check("the-chair-logs-the-young-mira-under-her-own-id", actors == ["mira_young"], (actors, (r.stdout + r.stderr)[-600:]))
        last = con.execute("SELECT MAX(turn) FROM turns").fetchone()[0]
        hits = _mentions(con, head, last)
        check("her-chair-turn,-whose-moment-names-Mira,-names-no-grown-mira", bool(actors) and not hits, hits[:6])
        lived = [json.loads(b) for (b,) in con.execute(
            "SELECT belief FROM acquisitions WHERE char_id = 'mira_young' AND turn >= ?", (head,))]
        check("(her-chair-turn-left-a-lived-memory,-about-herself-and-not-the-grown-mira)", bool(lived) and all(
              "mira_young" in b.get("about", []) and "mira" not in b.get("about", []) for b in lived),
              [b.get("about") for b in lived])
        con.close()
        # ADA IN THE CHAIR, in the present: the prompt the engine would send keeps "Mira" - she knows the grown one's
        # name; masking by the young one's edge would have called her "the girl"
        r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book, "--char", "ada", "--stub",
                            "--resume", run_id, "--at", "day 5 08:00", "--lasts", "10m", "--prompt-only",
                            "--circumstance", "Mira keeps the lamp through the gale."],
                           capture_output=True, text=True, cwd=REPO, timeout=300)
        said = r.stdout + r.stderr
        check("ada's-chair-prompt-says-Mira,-never-the-girl", "Mira keeps the lamp" in said and "the girl" not in said,
              said[-600:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
