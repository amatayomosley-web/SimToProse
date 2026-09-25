#!/usr/bin/env python3
"""test_own_timelines.py — each character lives on their own timeline (gate own-timelines, 2026-09-25).

THE OWNER'S RULE (plan step 3, approved 2026-09-25): a character ages by the time THEY lived - one item at each
opening they attend (their own time since they were last in a room) and one per beat they are in the room for; the
sheet describes them where they first walk on; a day may be 0 or before day 1; and only one character in two
overlapping scenes is refused. Until this gate every character took every stretch of the run, a late first
appearance arrived pre-aged from the run's first page, and any scene opening before the scene run last had ended
was refused, whoever was in it.

  [1] a walk-out stops ageing with the room and takes the rest of the scene at their next opening
  [2] two scenes that share no one, overlapping in story time, run in either order: everyone ends the same
  [3] a late first appearance walks on as the sheet says - bonds, scars, means, and the dating of what it carries
  [4] days before day 1 are read, stored and printed; an older database rebuilds its scene clock
  [5] one character in two places, or before their own latest, is refused - in both drivers; a walk-out is free

Scenes run through scripts/scene.py main IN PROCESS with the seats faked and nothing turn-dependent in the fakes, so
two run orders can be compared. Script-style: check(), main(), exit code. Stdlib only.
"""
import contextlib
import copy
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

from src.engine import bible, clock, heritable, injuries, mood_fold, passage, rungs   # noqa: E402
from src.engine.ledger import Ledger                                             # noqa: E402
from src.engine.records import Reading, RecordError                              # noqa: E402
from test_condition import FLOW, _cfg                                            # noqa: E402  (one fixture, several suites)
from test_story_time import _beats_by_turn, _con, _folded, _openings, _slow     # noqa: E402
from test_systems import _book                                                   # noqa: E402

FAILS = []
MIRA, ADA = {"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}
TOMAS, WREN = {"id": "tomas", "drive": "take the boat out"}, {"id": "wren", "drive": "mend the nets"}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _add(book, cid, name, like, other):
    """One more character: among the world's people, with `like`'s sheet renamed and an edge to `other`."""
    path = os.path.join(book, "world", "The Rock.md")
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"```json\n(.*)\n```", txt, re.S)
    world = json.loads(m.group(1))
    world["people"] = world["people"] + [{"id": cid, "what": "a boat hand"}]
    open(path, "w", encoding="utf-8").write(txt[:m.start(1)] + json.dumps(world, indent=1) + txt[m.end(1):])
    src = open(os.path.join(book, "characters", "%s.md" % like), encoding="utf-8").read()
    data = json.loads(re.search(r"```json\n(.*)\n```", src, re.S).group(1))
    data["fixed"]["name"] = name
    data["current"]["relationships"] = {other: {"trust": 0.6, "affinity": 0.6, "respect": 0.6, "debt": 0.0}}
    open(os.path.join(book, "characters", "%s.md" % name), "w", encoding="utf-8").write(
        "---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(data, indent=1)))


def _four(tmp):
    """The fixture book with four people: the two keepers, and a boat crew of two who know each other."""
    book = _book(tmp, FLOW)
    _add(book, "tomas", "Tomas", "Ada", "wren")
    _add(book, "wren", "Wren", "Mira", "tomas")
    return book


def _run(book, tmp, scenes, walker=None):
    """Scenes through scripts/scene.py main, the second on on a --resume; `passage.age` watched. `walker` {scene: id}
    walks out on their first line there. -> (db, run_id, outs, steps): steps = [(scene, "opening"|"beat", minutes,
    {id: slow state BEFORE the step})]."""
    import scene
    outs, steps, now = [], [], {"scene": None, "opening": False, "replay": False}

    def fake_turn(packet, event_text, temperament, model, stub, **k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        return ({"action": "She trims the wick and says the wind is backing.", "thought": "",
                 "exit": (walker or {}).get(now["scene"]) == k.get("char_id"), "addressee": other, "act": "",
                 "tags": {"type": "threat", "summary": "trims the wick", "dimensions": {"threat": 0.7},
                          "durability": "durable", "subject": other, "object": other,
                          "showed": {"affinity": 0.85, "trust": 0.8}}}, [])

    def refuse(*_a, **_k):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked out of this test")

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=(), **_k):
        other = next(p for p in present if p != me)          # nothing here reads the turn: run orders compare
        return ([Reading(path="WARINESS", rung=rungs.rung_at("WARINESS", 0.7)[1], about=other, confidence="sure")],
                [other], "sure", [])

    real_age, real_open, real_replay = passage.age, passage.apply_opening, mood_fold.replay

    def watched_age(chars, minutes, rest_rows):
        if not now["replay"]:
            steps.append((now["scene"], "opening" if now["opening"] else "beat", float(minutes or 0.0),
                          {i: _slow(c) for i, c in chars.items()}))
        return real_age(chars, minutes, rest_rows)

    def watched_replay(*a, **kw):
        now["replay"] = True
        try:
            return real_replay(*a, **kw)
        finally:
            now["replay"] = False

    def watched_open(*a, **kw):
        now["opening"] = True
        try:
            return real_open(*a, **kw)
        finally:
            now["opening"] = False

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv,
             passage.age, passage.apply_opening, mood_fold.replay)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, refuse, emotion
    passage.age, passage.apply_opening, mood_fold.replay = watched_age, watched_open, watched_replay
    try:
        for i, (name, day, time, lasts, budget, cast) in enumerate(scenes):
            now["scene"] = name
            argv = ["scene.py", "--book", book, "--scene", _cfg(tmp, name, day, time, lasts, {"cast": cast}),
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
        (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv,
         passage.age, passage.apply_opening, mood_fold.replay) = saved
    db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
    return db, sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0], outs, steps


def _replay_ok(db, run_id, label):
    con = _con(db)
    d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
    check("%s-the-replay-re-derives-every-mood-and-condition" % label,
          d["at"] is None and d["condition_at"] is None and not d["notes"] and not d["missing"], repr(d))


def _starts(con):
    return [(int(r[0]), int(r[1])) for r in con.execute("SELECT start_turn, end_turn FROM scenes ORDER BY start_turn")]


def _live_equals_folds(con, run_id, steps, names):
    """Every beat's watched state, for everyone in the room, against the folds at that turn (a scene's first beat
    also carries its opening, which the folds place at the same turn, so it is left to the opening checks)."""
    bad, n = [], 0
    for name in names:
        per_turn, s0, _e = _beats_by_turn(con, steps, name)
        for t, (_n, _k, _m, held) in sorted(per_turn.items()):
            if t == s0:
                continue
            for cid, state in held.items():
                n += 1
                got = _folded(con, run_id, cid, t)
                if state != got:
                    bad.append((name, t, cid, {k: (state[k], got[k]) for k in state if state[k] != got[k]}))
    return bad, n


def test_a_walk_out(tmp):
    print("\n[1] a walk-out stops ageing with the room, and takes the rest of the scene at their next opening")
    book = _four(tmp)
    scenes = (("pier-A", 1, "06:00", "4h", 4, [MIRA, ADA, TOMAS]), ("pier-B", 1, "12:00", "2h", 2, [MIRA, ADA, TOMAS]))
    db, run_id, outs, steps = _run(book, tmp, scenes, walker={"pier-A": "ada"})
    check("two-scenes-ran", all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    con = _con(db)
    (a0, a1), (b0, _b1) = _starts(con)
    left = con.execute("SELECT MIN(turn) FROM turns WHERE actor = 'ada' AND turn <= ?", (a1,)).fetchone()[0]
    check("ada-walked-out-and-the-scene-went-on-without-her", left is not None and left < a1, (left, a1))
    beats = lambda cid: [t for t, s, _m in clock.time_items(con, run_id, cid, b0) if s == 3]
    check("her-beat-minutes-stop-at-the-beat-she-left-on", beats("ada") == list(range(a0, left + 1)), beats("ada"))
    check("...while-those-who-stayed-took-every-beat", beats("mira") == list(range(a0, a1 + 1)), beats("mira"))
    opened = _openings(steps, "pier-B")
    at_b = clock.last_scene_clock(con, run_id, b0 + 1)["at"]
    want = at_b - clock.beat_end(con, run_id, left)
    check("at-B-she-takes-her-own-time:-from-the-end-of-the-beat-she-left-on",
          abs(opened["ada"][0] - want) < 1e-9 and opened["ada"][0] == clock.own_time(con, run_id, "ada", b0, at_b),
          (opened["ada"][0], want))
    check("...which-is-longer-than-theirs-by-the-rest-of-A", opened["ada"][0] > opened["mira"][0] == opened["tomas"][0],
          {c: m for c, (m, _s) in opened.items()})
    for cid in ("mira", "ada", "tomas"):
        check("%s-resumed-into-B-as-the-folds-have-them" % cid, opened[cid][1] == _folded(con, run_id, cid, b0))
    bad, n = _live_equals_folds(con, run_id, steps, ("pier-A", "pier-B"))
    check("at-every-beat-everyone-in-the-room-is-what-the-folds-rebuild", not bad and n > 6, bad or n)
    _replay_ok(db, run_id, "walk-out")
    return book, db, run_id, left


def test_either_order(tmp):
    print("\n[2] two scenes that share no one, overlapping in story time, run in either order - everyone ends the same")
    lamp = ("lamp-P", 1, "08:00", "2h", 2, [MIRA, ADA])
    boat = ("boat-Q", 1, "09:00", "2h", 2, [TOMAS, WREN])
    ends = {}
    for label, order in (("lamp-first", (lamp, boat)), ("boat-first", (boat, lamp))):
        sub = os.path.join(tmp, label)
        db, run_id, outs, _steps = _run(_four(sub), sub, order)
        check("%s-both-ran-(the-second-opens-inside-the-first's-span)" % label,
              all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
        check("%s-the-operator-is-told-it-is-set-earlier" % label, "set 60 minutes before" in outs[1]
              if label == "lamp-first" else "set 180 minutes before" in outs[1], outs[1][-400:])
        con = _con(db)
        head = con.execute("SELECT MAX(turn) FROM turns").fetchone()[0] + 1
        ends[label] = {cid: (_folded(con, run_id, cid, head), json.loads(con.execute(
            "SELECT affect FROM current_state WHERE char_id = ? ORDER BY turn DESC LIMIT 1", (cid,)).fetchone()[0]))
            for cid in ("mira", "ada", "tomas", "wren")}
        _replay_ok(db, run_id, label)
        n = con.execute("SELECT COUNT(*) FROM time_declarations").fetchone()[0]
        check("%s-a-gap-below-zero-declares-nothing" % label, n == 0, n)
        check("%s-the-story-has-reached-the-later-end,-whichever-scene-ran-last" % label,
              clock.story_now(con, run_id) == 11 * 60.0, clock.story_now(con, run_id))
    for cid in ("mira", "ada", "tomas", "wren"):
        a, b = ends["lamp-first"][cid], ends["boat-first"][cid]
        check("%s-ends-the-same-in-either-order" % cid, a == b, {k: (a[0][k], b[0][k]) for k in a[0] if a[0][k] != b[0][k]}
              or (a[1], b[1]))


def test_a_late_first_appearance(tmp):
    print("\n[3] a late first appearance walks on as the sheet says, and is dated from there")
    book = _four(tmp)
    scenes = (("lamp-A", 1, "08:00", "2h", 2, [MIRA, ADA]), ("lamp-B", 4, "08:00", "2h", 2, [MIRA, ADA, TOMAS]))
    db, run_id, outs, steps = _run(book, tmp, scenes)
    check("two-scenes-ran", all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    check("the-operator-sees-him-first-appear", "tomas first appears (as the sheet describes them)" in outs[1], outs[1][-400:])
    con = _con(db)
    (_a0, _a1), (b0, b1) = _starts(con)
    opened = _openings(steps, "lamp-B")
    at_b, at_a = clock.last_scene_clock(con, run_id, b0 + 1)["at"], clock.last_scene_clock(con, run_id, 1)["at"]
    check("his-opening-ages-him-by-nothing-(the-keepers-by-their-three-days-less-A's-two-hours)",
          "tomas" not in opened and sorted(opened) == ["ada", "mira"]
          and all(m == at_b - (at_a + 120.0) for m, _s in opened.values()), {c: m for c, (m, _s) in opened.items()})
    sheet = copy.deepcopy(bible.for_run(con, run_id)[2]["tomas"])
    heritable.ensure_temperament(sheet)                         # as the drivers' first profile does
    passage.stamp_authored(sheet)
    first, _s, _e = _beats_by_turn(con, steps, "lamp-B")
    check("at-his-first-beat-his-bonds-scars-and-means-are-the-sheet's", first[b0][3]["tomas"] == _slow(sheet),
          {k: (first[b0][3]["tomas"][k], _slow(sheet)[k]) for k in _slow(sheet) if first[b0][3]["tomas"][k] != _slow(sheet)[k]})
    check("...and-the-folds-hold-nothing-for-him-before-it",
          [it for it in clock.time_items(con, run_id, "tomas") if it[0] < b0] == [] and _folded(con, run_id, "tomas", b0) == _slow(sheet))
    check("his-story-begins-at-B,-theirs-at-A", clock.first_presence(con, run_id, "tomas") == at_b
          and clock.first_presence(con, run_id, "mira") == at_a, (clock.first_presence(con, run_id, "tomas"), at_b))
    now = clock.at_turn(con, run_id, b1)
    check("a-sheet-memory-of-his-is-dated-from-B", abs(clock.days_since(con, run_id, "tomas", None, b1) - (now - at_b) / 1440.0) < 1e-15
          and clock.days_since(con, run_id, "mira", None, b1) > 3.0, clock.days_since(con, run_id, "tomas", None, b1))
    hurt = {"current": {"condition": {"injuries": [{"what": "a rope burn", "severity": "minor", "ago": "12h"}]}}}
    his = injuries.for_actor(con, run_id, "tomas", hurt, b1)
    hers = injuries.for_actor(con, run_id, "mira", hurt, b1)
    check("a-sheet-injury-twelve-hours-old-is-fresh-on-him-and-long-healed-on-a-keeper-met-three-days-earlier",
          [r["stage"] for r in his] == ["fresh"] and hers == [], (his, hers))
    _replay_ok(db, run_id, "first-appearance")


def test_days_before_day_one(tmp):
    print("\n[4] days before day 1 - read, stored, printed; an older database rebuilds its scene clock")
    book = _four(tmp)
    scenes = (("before-A", -3, "06:00", "1h", 2, [TOMAS, ADA]), ("lamp-B", 1, "08:00", "1h", 2, [MIRA, ADA]))
    db, run_id, outs, steps = _run(book, tmp, scenes)
    check("a-scene-on-day-minus-3-ran,-then-one-on-day-1", all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    check("...and-the-operator-reads-its-day-as-written", "opens day -3 06:00" in outs[0], outs[0][-600:])
    con = _con(db)
    first = clock.last_scene_clock(con, run_id, 1)
    check("it-is-stored-below-zero-and-read-back", first["at"] == -4 * 1440.0 + 360.0 and clock.format_at(first["at"]) == "day -3 06:00",
          first)
    (_a0, _a1), (b0, _b1) = _starts(con)
    opened = _openings(steps, "lamp-B")
    check("ada's-own-time-to-day-1-runs-across-day-0", abs(opened["ada"][0] - (4 * 1440.0 + 60.0)) < 1e-9 and "mira" not in opened,
          {c: m for c, (m, _s) in opened.items()})
    _replay_ok(db, run_id, "day-minus-3")
    # AN OLDER DATABASE: v31's scene_clock refused a reading below zero (a CHECK SQLite cannot drop) - opening it rebuilds
    # the table, rows kept; an open interrupted after the old table was set aside finishes the copy on the next.
    schema = open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read()
    old = schema.replace("at_minutes    REAL    NOT NULL,", "at_minutes    REAL    NOT NULL CHECK (at_minutes >= 0),")
    check("the-v31-table-can-be-made-for-the-test", old != schema)
    for label, interrupted in (("v31", False), ("v31-interrupted", True)):
        path = os.path.join(tmp, "%s.db" % label)
        raw = sqlite3.connect(path)
        raw.executescript(old)
        raw.execute("INSERT INTO scene_clock (run_id, turn, at_minutes, lasts_minutes, beat_minutes) VALUES ('r', 0, 60.0, 30.0, 15.0)")
        if interrupted:
            raw.executescript("DROP TRIGGER scene_clock_no_update; DROP TRIGGER scene_clock_no_delete; "
                              "ALTER TABLE scene_clock RENAME TO scene_clock_v31;")
        raw.execute("PRAGMA user_version = 31")
        raw.commit()
        raw.close()
        led = Ledger(path)
        sql = led.con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='scene_clock'").fetchone()[0]
        kept = [tuple(r) for r in led.con.execute("SELECT run_id, turn, at_minutes, lasts_minutes, beat_minutes FROM scene_clock")]
        check("%s-migrates-to-v32-with-its-rows" % label, led.con.execute("PRAGMA user_version").fetchone()[0] == 32
              and kept == [("r", 0, 60.0, 30.0, 15.0)] and not re.search(r"\bat_minutes\s*>=", sql), (kept, sql))
        led.record_scene_clock("r", 5, -600.0, None, 0.0)
        check("%s-...takes-a-reading-before-day-1" % label, clock.last_scene_clock(led.con, "r")["at"] == -600.0)
        try:
            led.con.execute("UPDATE scene_clock SET at_minutes = 0 WHERE turn = 5")
            check("%s-...and-is-still-append-only" % label, False, "the update went through")
        except sqlite3.DatabaseError as e:
            check("%s-...and-is-still-append-only" % label, "append-only" in str(e), str(e))
        check("%s-...with-nothing-left-aside" % label, not led.con.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'scene_clock_v31'").fetchone())
        led.con.close()


def test_refusals(tmp, walked):
    print("\n[5] one character in two places, or before their own latest, is refused - in both drivers")
    book, db, run_id, _left = walked
    led = Ledger(db)
    sheets = bible.for_run(led.con, run_id)[2]
    head = led.con.execute("SELECT MAX(turn) FROM turns").fetchone()[0] + 1
    a = clock.last_scene_clock(led.con, run_id, 1)                          # pier-A: day 1 06:00, four hours
    b = clock.last_scene_clock(led.con, run_id)                             # pier-B: day 1 12:00, two hours
    chars = lambda *ids: {i: copy.deepcopy(sheets[i]) for i in ids}
    for label, at, who, code in (("a-keeper-inside-A,-where-she-stayed", a["at"] + 150.0, ("mira",), "CLOCK_TWO_PLACES_AT_ONCE"),
                                 ("...anyone-inside-B", b["at"] + 30.0, ("tomas",), "CLOCK_TWO_PLACES_AT_ONCE"),
                                 ("...a-keeper-before-her-own-latest", a["at"] + 280.0, ("mira",), "CLOCK_RUNS_BACKWARDS")):
        try:
            passage.open_scene(led, run_id, head, at, 20.0, 1, chars(*who))
            check("%s-is-refused-%s" % (label, code), False, "opened")
        except RecordError as e:
            check("%s-is-refused-%s" % (label, code), e.code == code, e.code)
    check("a-refused-opening-logs-nothing", not led.con.execute("SELECT 1 FROM scene_clock WHERE turn >= ?", (head,)).fetchone())
    # THE CHAIR TAKES THE SAME REFUSAL: its only one was the run-wide gap, which is gone (review I5)
    r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira", "--stub",
                        "--resume", run_id, "--at", "day 1 08:00", "--lasts", "10m"], input="quit\n",
                       capture_output=True, text=True, cwd=REPO, timeout=300)
    check("the-chair-at-a-time-its-character-spent-in-A-is-refused", "CLOCK_TWO_PLACES_AT_ONCE" in (r.stdout + r.stderr)
          and not led.con.execute("SELECT 1 FROM scene_clock WHERE turn >= ?", (head,)).fetchone(), (r.stdout + r.stderr)[-500:])
    got = _opens(led, run_id, head, b["at"] + b["lasts"], None, chars("mira"))
    check("a-scene-opening-as-her-last-one-ends-only-touches-it", (got.get("own") or {}).get("mira") == 0.0, got)
    led.con.close()
    # HE WALKED OUT: from the end of the beat he left on, he is free - while the others are still in the scene. A log
    # built by hand: a four-hour scene at 06:00, an hour a beat, tomas in the room for its first beat only.
    from src.engine.records import PATHS, TurnCommit
    mem = Ledger(":memory:")
    mem.create_run("w", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    mem.record_scene_clock("w", 0, 360.0, 240.0, 60.0)
    for t, room in ((0, ["ada", "mira", "tomas"]), (1, ["ada", "mira"]), (2, ["ada", "mira"]), (3, ["ada", "mira"])):
        mem.append_turn(TurnCommit(run_id="w", turn=t, actor=room[t % 2], thought="-", action="-", tags={},
                                   validation={"ok": True}, affect={p: 0.2 for p in PATHS},
                                   manifest={"decay": {"minutes": 60.0, "here": room, "bystanders": []}}))
    try:
        passage.open_scene(mem, "w", 4, 450.0, 20.0, 1, chars("mira"))
        check("she-stayed:-a-scene-at-07:30-is-two-places", False, "opened")
    except RecordError as e:
        check("she-stayed:-a-scene-at-07:30-is-two-places", e.code == "CLOCK_TWO_PLACES_AT_ONCE", e.code)
    got = _opens(mem, "w", 4, 450.0, 20.0, chars("tomas"))
    check("he-left-at-07:00:-his-scene-at-07:30-opens-inside-the-span-he-walked-out-of",
          (got.get("own") or {}).get("tomas") == 30.0 and got.get("elapsed") == 450.0 - 600.0, got)


def _opens(led, run_id, turn, at, lasts, chars):
    """An opening that should be allowed -> its result, or {"refused": code} so a wrong refusal fails by name."""
    try:
        return passage.open_scene(led, run_id, turn, at, lasts, 1, chars)
    except RecordError as e:
        return {"refused": e.code}


def main():
    print("test_own_timelines.py — each character lives on their own timeline (gate own-timelines)\n")
    tmp = tempfile.mkdtemp(prefix="swe_own_")
    try:
        walked = test_a_walk_out(os.path.join(tmp, "walk"))
        test_either_order(os.path.join(tmp, "order"))
        test_a_late_first_appearance(os.path.join(tmp, "late"))
        test_days_before_day_one(os.path.join(tmp, "before"))
        test_refusals(tmp, walked)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_own_timelines: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
