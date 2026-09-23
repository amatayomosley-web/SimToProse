"""test_condition.py — energy and stress that move (src/engine/condition.py, gate condition-flow).

WHAT THIS PINS (2026-09-22). Nothing moved a character's condition after creation. The owner ruled that
the engine carries energy scene to scene AND a scene can override it (C3a), and that emotional load and
time drain it (C3b; exertion arrives with gate body-exertion). `condition_flow` is a NEW system and ships
OFF, so every existing book runs as before (tests/test_systems.py holds that, and the frozen golden run).

  [1] the arithmetic: a beat costs its minutes and (the speaker's) impact; stress above the floor builds
      load; an opening costs the owed minutes and rests over the gap; a refused input is refused by code;
  [2] the director's words: priced by the engine, each energy word inside the stage-line band it names;
  [3] the registry: the flow is off by default and cannot run without the condition system;
  [4] a seated two-scene run with the flow ON through scripts/scene.py main: every present character's
      condition moves beat by beat, the speaker's by more than a bystander's; a night between scenes is
      rest; the stage line the actor reads changes; the replay re-derives EVERY cached condition and
      mood exactly, fresh and resumed;
  [5] a scene cfg's `condition` sets how someone arrives, after the rest - with the flow on and off -
      and the replay reads it back from the pinned cfg;
  [6] the drivers refuse, before a beat is paid for, a sheet the flow cannot move and a cfg that states a
      condition for a book with none; the chair's turn moves its condition too;
  [7] the pre-run checks say the same things first.

The book is invented here (two keepers on a rock), per hard rule 1. Script-style; exit 0 = all pass.
"""
import contextlib
import copy
import glob
import io
import json
import math
import os
import shutil
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import bible, condition, direction, mood_fold, rungs, systems   # noqa: E402
from src.engine.records import Reading, RecordError                              # noqa: E402
from test_systems import _book, _chair_seated                                    # noqa: E402  (one fixture, three suites)

FAILS = []
FLOW = {"condition_flow": True}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _code(fn):
    try:
        fn()
    except RecordError as e:
        return e.code
    return None


def test_arithmetic():
    print("\n[1] the arithmetic")
    c0 = {"energy": 0.8, "allostatic_load": 0.2, "health": 0.9}
    calm = {"WARINESS": 0.3, "DISPLEASURE": 0.2, "DEFLATION": 0.1}
    t = condition.spend(c0, 60.0, 0.0, calm)
    check("an-hour-costs-its-minutes", abs(t["energy"] - (0.8 - 60 * condition.TIME_SPEND)) < 1e-12, t)
    check("...and-a-calm-hour-builds-no-load", t["allostatic_load"] == 0.2, t)
    check("...and-the-other-keys-ride-along-untouched", t["health"] == 0.9 and c0["energy"] == 0.8, (t, c0))
    i = condition.spend(c0, 0.0, 0.3, calm)
    check("a-beat-s-impact-costs-energy", abs(i["energy"] - (0.8 - 0.3 * condition.IMPACT_SPEND)) < 1e-12, i)
    afraid = dict(calm, WARINESS=0.9)
    s = condition.spend(c0, 60.0, 0.0, afraid)
    check("fear-above-the-floor-builds-load", abs(s["allostatic_load"] - (0.2 + condition.LOAD_GAIN * 60 * 0.4)) < 1e-12, s)
    check("...and-the-worst-stress-path-is-the-one-read", condition.stress(dict(afraid, DISPLEASURE=0.7)) == 0.4)
    low = condition.spend({"energy": 0.01, "allostatic_load": 0.99}, 960.0, 5.0, {"WARINESS": 1.0})
    check("energy-and-load-stay-in-0-1", low["energy"] == 0.0 and low["allostatic_load"] == 1.0, low)
    o = condition.opening(c0, 480.0, 30.0, calm)
    tired = 0.8 - 30 * condition.TIME_SPEND
    check("an-opening-costs-the-owed-minutes-then-rests-the-gap",
          abs(o["energy"] - (1 - (1 - tired) * math.exp(-480 / condition.REST_TAU))) < 1e-12, o)
    check("...and-the-load-eases-over-days", abs(o["allostatic_load"] - 0.2 * math.exp(-480 / condition.LOAD_TAU)) < 1e-12, o)
    check("no-gap-rests-nothing", condition.opening(c0, 0, 0.0, calm)["energy"] == 0.8)
    for code, fn in (("CONDITION_NOT_A_DICT", lambda: condition.spend(None, 1.0)),
                     ("CONDITION_KEYS_MISSING", lambda: condition.spend({"energy": 0.5}, 1.0)),
                     ("CONDITION_SPAN_NOT_NUMERIC", lambda: condition.spend(c0, -1.0)),
                     ("CONDITION_SPAN_NOT_NUMERIC", lambda: condition.spend(c0, "an hour")),
                     ("CONDITION_SPAN_NOT_NUMERIC", lambda: condition.opening(c0, True))):
        check("refuses-%s" % code, _code(fn) == code, _code(fn))


def test_words():
    print("\n[2] the director's words, priced by the engine")
    bands = [s for _cut, s in direction._COND]
    for word, band in zip(("spent", "tired", "steady", "fresh"), bands):
        line = direction.direct_condition({"energy": condition.ENERGY_WORDS[word], "allostatic_load": 0.0})
        check("energy-%s-is-told-as-%r" % (word, band[:24]), line == band, line)
    loads = [condition.STRESS_WORDS[w] for w in ("calm", "tense", "strained", "frayed")]
    check("stress-words-rise-in-order", loads == sorted(loads) and len(set(loads)) == 4, loads)
    chars = {"mira": {"current": {"condition": {"energy": 0.9, "allostatic_load": 0.1}}}, "ada": {"current": {"condition": {}}}}
    done = condition.apply_declared(chars, [{"char": "mira", "energy": "Spent"}, {"char": "ada", "stress": "tense"}])
    check("a-declaration-sets-only-the-keys-it-names", done == ["ada", "mira"]
          and chars["mira"]["current"]["condition"] == {"energy": 0.15, "allostatic_load": 0.1}
          and chars["ada"]["current"]["condition"] == {"allostatic_load": 0.30}, chars)
    for code, entries in (("CONDITION_WORD_UNKNOWN", [{"char": "mira", "energy": "exhausted"}]),
                          ("CONDITION_DECLARATION_MALFORMED", [{"char": "mira"}]),
                          ("CONDITION_DECLARATION_MALFORMED", [{"char": "tomas", "energy": "spent"}]),
                          ("CONDITION_DECLARATION_MALFORMED", {"char": "mira"})):
        check("refuses-%s-%s" % (code, json.dumps(entries)), _code(lambda: condition.apply_declared(chars, entries)) == code)
    check("no-declaration-sets-nothing", condition.apply_declared(chars, None) == [])


def test_registry():
    print("\n[3] the registry")
    check("the-flow-is-off-by-default", "condition_flow" not in systems.for_book({}))
    check("...and-on-when-the-book-says-so", "condition_flow" in systems.for_book({"systems": FLOW}))
    check("it-cannot-run-without-the-condition-system",
          _code(lambda: systems.for_book({"systems": {"condition_flow": True, "condition": False}})) == "SYSTEMS_NEEDS_UNMET")


# ---------------------------------------------------------------------------------------------------
def _cfg(tmp, name, day, time, lasts, extra=None):
    path = os.path.join(tmp, name + ".json")
    body = {"name": name, "at": {"day": day, "time": time}, "lasts": lasts,
            "situation": "The two keepers wait out the gale in the lamp room.",
            "cast": [{"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}]}
    body.update(extra or {})
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(body, fh)
    return path


def _run(tmp, decl, scenes, sheet_edit=None):
    """Scenes (the second on a --resume) through scripts/scene.py main IN PROCESS, seats faked: every beat
    durable, a reading about the other keeper at a rung that rises with the turn. -> (db, run_id, seen,
    outputs): `seen` is [(turn, speaker, the condition the speaker's packet carried)]."""
    import scene
    book = _book(tmp, decl)
    if sheet_edit:
        sheet_edit(book)
    seen, outs = [], []

    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        me = "mira" if other == "ada" else "ada"          # two keepers: the speaker is the one the edge is not to
        seen.append((me, dict(packet["volatile"]["state"]["condition"])))
        return ({"action": "She trims the wick and says the wind is backing.", "thought": "", "exit": False,
                 "addressee": other, "act": "",
                 "tags": {"type": "threat", "summary": "trims the wick", "dimensions": {"threat": 0.7},
                          "durability": "durable", "subject": other, "object": other,
                          "showed": {"affinity": 0.85, "trust": 0.8}}}, [])

    def refuse(*_a, **_k):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked out of this test")

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=(), **_k):
        other = next(p for p in present if p != me)
        return ([Reading(path="WARINESS", rung=rungs.rung_at("WARINESS", 0.6 + 0.04 * ((turn or 0) % 8))[1], about=other,
                         confidence="sure"),
                 Reading(path="DISPLEASURE", rung=rungs.rung_at("DISPLEASURE", 0.9)[1], about=other, confidence="sure")],
                [other], "sure", [])

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, refuse, emotion
    try:
        for i, (name, day, time, lasts, budget, extra) in enumerate(scenes):
            argv = ["scene.py", "--book", book, "--scene", _cfg(tmp, name, day, time, lasts, extra), "--budget", str(budget),
                    "--model", "fake/model", "--no-keeper"]
            if i:
                db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
                argv += ["--resume", sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0]]
            sys.argv = argv
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                    scene.main()
            except SystemExit as e:
                out.write("\nSYSTEMEXIT %s" % e)
            outs.append(out.getvalue())
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv = saved
    dbs = glob.glob(os.path.join(book, "runs", "*.db"))
    if not dbs:
        return None, None, seen, outs
    con = sqlite3.connect(dbs[0])
    run = con.execute("SELECT run_id FROM runs").fetchone()
    return dbs[0], (run[0] if run else None), seen, outs


def _rows(db, cid):
    return [(int(t), json.loads(c)) for t, c in sqlite3.connect(db).execute(
        "SELECT turn, condition FROM current_state WHERE char_id = ? ORDER BY turn", (cid,))]


def _divergence(db, run_id):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])


TWO_SCENES = (("gale-1", 1, "21:00", "1h", 6, None), ("gale-2", 2, "08:00", "40m", 4, None))


def test_a_flowing_run(tmp):
    print("\n[4] the flow ON through scripts/scene.py main: two scenes, a night between them")
    db, run_id, seen, outs = _run(tmp, FLOW, TWO_SCENES)
    speakers = [int(t) for t, in sqlite3.connect(db).execute("SELECT turn FROM turns ORDER BY turn")]
    mira = _rows(db, "mira")
    e = [c["energy"] for _t, c in mira]
    first2 = sqlite3.connect(db).execute("SELECT MIN(start_turn) FROM scenes WHERE start_turn > 0").fetchone()[0]
    s1 = [c["energy"] for t, c in mira if t < first2]
    check("both-scenes-ran", len(speakers) == 10 and first2 == 6, (speakers, first2, outs[-1][-300:]))
    check("mira-s-energy-falls-at-every-row-of-the-first-scene", all(b < a for a, b in zip(s1, s1[1:])) and s1[0] < 0.8, s1)
    con = sqlite3.connect(db)
    act, sit = [], []
    for t, cid, c in con.execute("SELECT s.turn, s.char_id, s.condition FROM current_state s ORDER BY s.turn"):
        prev = [json.loads(x) for (x,) in con.execute("SELECT condition FROM current_state WHERE char_id=? AND turn<? "
                                                       "ORDER BY turn DESC LIMIT 1", (cid, t))]
        if prev and t < first2:
            spoke = con.execute("SELECT actor FROM turns WHERE turn=?", (t,)).fetchone()[0] == cid
            (act if spoke else sit).append(prev[0]["energy"] - json.loads(c)["energy"])
    check("a-speaker-pays-more-than-a-bystander", act and sit and min(act) > max(sit) > 0, (act, sit))
    last1 = [c for t, c in mira if t < first2][-1]
    after = [c for t, c in mira if t >= first2][0]
    check("a-night-between-scenes-is-REST", after["energy"] > last1["energy"], (last1, after))
    check("the-load-built-while-anger-ran-high", mira[len(s1) - 1][1]["allostatic_load"] > 0.2, mira[len(s1) - 1])
    lines = {direction.direct_condition(c) for _who, c in seen}
    check("the-stage-line-the-actor-reads-moved", len(lines) >= 2, lines)
    check("the-resume-reports-the-condition-replay", "conditions: largest difference none" in outs[1], outs[1][-400:])
    d = _divergence(db, run_id)
    check("the-replay-re-derives-every-cached-condition", d["condition_at"] is None and d["condition_largest"] <= 1e-12, d)
    check("...and-every-cached-mood", d["at"] is None and not d["missing"] and not d["notes"], d)
    # THE CONTROL (a mutation survived without it, 2026-09-22): a check that reports "no difference" must be
    # shown to SEE one. A cached condition moved on a complete copy is named at its turn, character and key.
    tampered = os.path.join(tmp, "tampered.db")
    a, b = sqlite3.connect(db), sqlite3.connect(tampered)
    with b:
        a.backup(b)
    a.close()
    t0, c0 = b.execute("SELECT turn, condition FROM current_state WHERE char_id = 'ada' ORDER BY turn LIMIT 1").fetchone()
    moved = dict(json.loads(c0), energy=json.loads(c0)["energy"] - 0.1)
    with b:
        b.execute("UPDATE current_state SET condition = ? WHERE char_id = 'ada' AND turn = ?", (json.dumps(moved), t0))
    b.close()
    d = _divergence(tampered, run_id)
    check("control-a-tampered-cached-condition-is-NAMED", d["condition_at"] == (t0, "ada", "energy")
          and abs(d["condition_largest"] - 0.1) < 1e-9, d)
    return db, run_id


def test_a_declared_arrival(tmp):
    print("\n[5] a scene cfg states how someone arrives - the flow on, and off")
    arrive = (TWO_SCENES[0], ("gale-2", 2, "08:00", "40m", 4, {"condition": [{"char": "mira", "energy": "spent", "stress": "frayed"}]}))
    for label, decl in (("flow-on", FLOW), ("flow-off", None)):
        db, run_id, seen, outs = _run(os.path.join(tmp, label), decl, arrive)
        first2 = sqlite3.connect(db).execute("SELECT MIN(start_turn) FROM scenes WHERE start_turn > 0").fetchone()[0]
        n1 = sum(1 for (t,) in sqlite3.connect(db).execute("SELECT turn FROM turns WHERE turn < ?", (first2,)))
        mine = [c for who, c in seen[n1:] if who.lower() == "mira"]
        check("%s-mira-s-first-packet-of-the-scene-carries-the-declared-state" % label,
              mine and abs(mine[0]["energy"] - 0.15) < 1e-12 and abs(mine[0]["allostatic_load"] - 0.80) < 1e-12, mine[:1])
        check("%s-the-driver-says-so" % label, "CONDITION: mira arrives energy spent, stress frayed" in outs[1], outs[1][-300:])
        d = _divergence(db, run_id)
        check("%s-the-replay-reads-it-back-from-the-pinned-cfg" % label,
              d["condition_at"] is None and d["at"] is None and not d["notes"], d)
    rows = _rows(db, "mira")
    check("flow-off-the-declared-state-then-HOLDS", rows[-1][1]["energy"] == 0.15, rows[-1])


def test_refusals(tmp):
    print("\n[6] the drivers refuse before a beat is paid for; the chair's turn moves too")
    def half(book):
        p = os.path.join(book, "characters", "Mira.md")
        txt = open(p, encoding="utf-8").read().replace('"allostatic_load": 0.2', '"allostatic_load_x": 0.2')
        open(p, "w", encoding="utf-8").write(txt)
    db, _r, seen, outs = _run(os.path.join(tmp, "half"), FLOW, TWO_SCENES[:1], sheet_edit=half)
    turns = sqlite3.connect(db).execute("SELECT COUNT(*) FROM turns").fetchone()[0] if db else 0
    check("a-sheet-the-flow-cannot-move-is-refused-before-any-beat",
          "SYSTEMEXIT condition flow" in outs[0] and "CONDITION_KEYS_MISSING" in outs[0] and turns == 0 and not seen,
          (turns, len(seen), outs[0][-300:]))
    off = (("gale-1", 1, "21:00", "1h", 2, {"condition": [{"char": "mira", "energy": "spent"}]}),)
    db, _r, seen, outs = _run(os.path.join(tmp, "nocond"), {"condition": False}, off)
    turns = sqlite3.connect(db).execute("SELECT COUNT(*) FROM turns").fetchone()[0] if db else 0
    check("a-cfg-stating-a-condition-for-a-book-with-none-is-refused",
          "runs no condition system" in outs[0] and turns == 0 and not seen, (turns, len(seen), outs[0][-300:]))
    chair = _chair_seated(os.path.join(tmp, "chair"), FLOW)
    row = [json.loads(c) for (c,) in sqlite3.connect(chair).execute("SELECT condition FROM current_state WHERE char_id='mira'")]
    check("the-chair-s-turn-costs-energy-too", row and row[-1]["energy"] < 0.8, row)
    # THE CHAIR'S OPENINGS KEEP THE STANDARD DAY (gate gap-day-and-night): two sessions of one run, each opened with
    # --at - evening to the next morning is a night's rest; morning to afternoon is hours awake.
    import subprocess

    def sessions(name, first, second):
        book = _book(os.path.join(tmp, name), FLOW)

        def chair(*extra, said="by:ada Ada brought new wicks for the lamp [durable]"):
            r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira",
                                "--stub", "--lasts", "10m"] + list(extra), input=said + "\nquit\n", capture_output=True,
                               text=True, cwd=REPO, timeout=300)
            return (r.stdout or "") + (r.stderr or "")
        out1 = chair("--at", first)
        run_id = next((ln.split("new chronicle:")[1].strip() for ln in out1.splitlines() if "new chronicle:" in ln), "")
        chair("--resume", run_id, "--at", second)
        db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
        return [json.loads(c)["energy"] for (c,) in sqlite3.connect(db).execute(
            "SELECT condition FROM current_state WHERE char_id='mira' ORDER BY turn")], out1
    rows, out1 = sessions("chair-night", "day 1 21:00", "day 2 07:00")
    check("the-chair-s-evening-to-morning-gap-is-a-night-s-REST", len(rows) == 2 and rows[1] > rows[0], (rows, out1[-300:]))
    rows, out1 = sessions("chair-day", "day 1 09:00", "day 1 15:00")
    check("...and-its-morning-to-afternoon-gap-is-hours-AWAKE", len(rows) == 2 and rows[1] < rows[0] - 0.2, (rows, out1[-300:]))


def test_lint():
    print("\n[7] the pre-run checks")
    import lint_book
    import lint_scene
    world = json.load(open(os.path.join(REPO, "world", "ashford-slice.json"), encoding="utf-8"))
    maren = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    half = copy.deepcopy(maren)
    del half["current"]["condition"]["allostatic_load"]
    got = lint_book.lint(dict(world, systems=FLOW), {"maren": half})
    check("flow-on-a-half-authored-condition-is-an-ERROR", any("condition_flow" in e for e in got["errors"]), got["errors"])
    got = lint_book.lint(world, {"maren": half})
    check("...while-with-the-flow-off-it-stays-a-warning", not any("condition_flow" in e for e in got["errors"]))
    cfg = {"cast": [{"id": "maren", "drive": "save the child"}, {"id": "edda", "drive": "get help"}], "situation": "x",
           "condition": [{"char": "maren", "energy": "exhausted"}]}
    errs, _w, _u = lint_scene.lint_cfg(cfg, world, {"maren": maren})
    check("lint_scene-refuses-an-unpriced-word", any("exhausted" in e for e in errs), errs)
    cfg["condition"] = [{"char": "maren", "energy": "spent"}]
    errs, _w, _u = lint_scene.lint_cfg(cfg, dict(world, systems={"condition": False}), {"maren": maren})
    check("lint_scene-refuses-a-condition-for-a-book-with-none", any("switches the condition system off" in e for e in errs), errs)
    errs, _w, _u = lint_scene.lint_cfg(cfg, world, {"maren": maren})
    check("...and-passes-a-good-one", not any(e.startswith("condition") for e in errs), errs)


def _add_tomas(book):
    """A third keeper, for a POV cut: in the world's people and with a sheet of his own (Ada's, renamed)."""
    import re
    for path, edit in ((os.path.join(book, "world", "The Rock.md"),
                        lambda w: dict(w, people=w["people"] + [{"id": "tomas", "what": "the boatman"}])),
                       (os.path.join(book, "characters", "Ada.md"), None)):
        txt = open(path, encoding="utf-8").read()
        m = re.search(r"```json\n(.*)\n```", txt, re.S)
        data = json.loads(m.group(1))
        if edit:
            open(path, "w", encoding="utf-8").write(txt[:m.start(1)] + json.dumps(edit(data), indent=1) + txt[m.end(1):])
        else:
            data["fixed"]["name"] = "Tomas"
            data["current"]["relationships"] = {"ada": {"trust": 0.6, "affinity": 0.6, "respect": 0.6, "debt": 0.0}}
            open(os.path.join(book, "characters", "Tomas.md"), "w", encoding="utf-8").write(
                "---\ntype: character\nid: Tomas\n---\n# Tomas\n\n```json\n%s\n```\n" % json.dumps(data, indent=1))


def test_the_gap_between(tmp):
    print("\n[8] the gap is each character's own: night rests, day is awake, a stated word supersedes")
    check("an-evening-to-morning-gap-walks-day-night-day", C_hours(21 * 60, 1440 + 8 * 60) == [("day", 60.0), ("night", 480.0), ("day", 120.0)],
          C_hours(21 * 60, 1440 + 8 * 60))
    c = {"energy": 0.7, "allostatic_load": 0.3}
    check("the-night-rests", condition.between(c, 21 * 60 + 10, 1440 + 7 * 60)["energy"] > 0.7)
    check("six-daylight-hours-are-awake", abs(condition.between(c, 9 * 60, 15 * 60)["energy"] - (0.7 - 360 * condition.TIME_SPEND)) < 1e-12)
    check("a-stated-rest-supersedes-the-day", condition.between(c, 9 * 60, 15 * 60, stated="rested")["energy"] > 0.7)
    check("a-stated-waking-supersedes-the-night",
          abs(condition.between(c, 21 * 60, 1440 + 7 * 60, stated="awake")["energy"] - (0.7 - 600 * condition.TIME_SPEND)) < 1e-12)
    check("an-unpriced-gap-word-is-refused", _code(lambda: condition.between(c, 0, 60, stated="napped")) == "CONDITION_WORD_UNKNOWN")
    check("the-scene-file-may-say-it", condition.declaration_errors([{"char": "mira", "gap": "rested"}], ["mira"]) == []
          and condition.declaration_errors([{"char": "mira", "gap": "napped"}], ["mira"])[0][0] == "CONDITION_WORD_UNKNOWN")
    from src.engine import passage
    first_time = {"t": {"current": {"condition": dict(c)}}}
    passage.apply_opening(first_time, 0.0, 0.0, lambda i: [], flow=True, at=600.0, gaps={"t": None})
    check("a-first-appearance-keeps-the-sheet-s-condition", first_time["t"]["current"]["condition"] == c, first_time)
    # B has ONE beat, so one of its two is present and SILENT - presence is the room, not only the speaker
    pov = (("keep-A", 1, "10:00", "30m", 2, None),
           ("boat-B", 1, "10:32", "10m", 1, {"cast": [{"id": "ada", "drive": "get the boat ready"},
                                                     {"id": "tomas", "drive": "take the boat out"}]}),
           ("keep-A2", 1, "10:45", "20m", 2, None))
    for label, extra in (("unstated", None), ("stated", [{"char": "mira", "gap": "rested"}, {"char": "ada", "gap": "rested"}])):
        scenes = pov[:2] + ((pov[2][:5] + ({"condition": extra} if extra else None,)),)
        db, run_id, seen, outs = _run(os.path.join(tmp, label), FLOW, scenes, sheet_edit=_add_tomas)
        starts = [int(r[0]) for r in sqlite3.connect(db).execute("SELECT start_turn FROM scenes ORDER BY start_turn")]
        check("%s-three-scenes-ran" % label, len(starts) == 3, (starts, outs[-1][-300:]))
        if len(starts) != 3:
            continue
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        if label == "unstated":
            from src.engine import clock
            check("mira-s-own-gap-runs-from-the-scene-she-was-in", clock.presence_end(con, run_id, "mira", starts[2])
                  == {"end": 630.0, "owed": 0.0}, clock.presence_end(con, run_id, "mira", starts[2]))
            check("...ada-s-from-the-POV-cut-she-was-in", clock.presence_end(con, run_id, "ada", starts[2])
                  == {"end": 642.0, "owed": 0.0}, clock.presence_end(con, run_id, "ada", starts[2]))
            check("...and-a-first-appearance-has-none", clock.presence_end(con, run_id, "tomas", starts[1]) is None)
            spoke = con.execute("SELECT actor FROM turns WHERE turn = ?", (starts[1],)).fetchone()[0]
            silent = ({"ada", "tomas"} - {spoke}).pop()
            check("the-one-who-only-LISTENED-in-B-was-there-too-(%s)" % silent,
                  clock.presence_end(con, run_id, silent, starts[2]) == {"end": 642.0, "owed": 0.0},
                  clock.presence_end(con, run_id, silent, starts[2]))
        first = next(who for i, (who, _c) in enumerate(seen) if i == starts[2])       # the first speaker of A2
        opening = seen[starts[2]][1]["energy"]
        last = json.loads(con.execute("SELECT condition FROM current_state WHERE char_id = ? AND turn < ? ORDER BY turn DESC LIMIT 1",
                                      (first, starts[2])).fetchone()[0])["energy"]
        gap = {"mira": 15.0, "ada": 3.0}[first]
        if label == "unstated":
            check("the-POV-cut-s-minutes-are-AWAKE-time-for-%s" % first, abs(opening - (last - gap * condition.TIME_SPEND)) < 1e-12,
                  (first, opening, last, gap))
        else:
            check("a-stated-rest-rests-%s-instead" % first, opening > last, (first, opening, last))
        d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
        check("%s-the-replay-re-derives-every-condition" % label, d["condition_at"] is None and d["at"] is None and not d["notes"], d)


def C_hours(a, b):
    return condition.hours(a, b)


def main():
    print("test_condition.py — energy and stress that move\n")
    tmp = tempfile.mkdtemp(prefix="swe_condition_")
    try:
        test_arithmetic()
        test_words()
        test_registry()
        test_a_flowing_run(os.path.join(tmp, "flow"))
        test_a_declared_arrival(os.path.join(tmp, "arrive"))
        test_refusals(os.path.join(tmp, "refuse"))
        test_lint()
        test_the_gap_between(os.path.join(tmp, "gap"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_condition: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
