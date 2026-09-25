"""test_absent_age.py — each character's mood ages by their own time out of the room (gate absent-age).

WHAT THIS PINS (2026-09-24). An opening decayed the NEW scene's cast over the run's gap since the LAST scene ended,
plus that scene's unspent minutes - so someone who sat scenes out, or walked out early, came back feeling exactly
as they did when they left. The owner ruled that they age with story time. Each character's mood now ages over
their own time away (`clock.presence_end` -> `passage.own_minutes`), a first appearance keeps the sheet's mood,
and the rest of a scene someone walked out of is theirs - their mood's and, in a `condition_flow` book, their
energy's. The slow tiers (bonds, wounds, arc, attitude) are not touched: the log already replays every gap
between scenes onto every character, present or not.

  [1] a POV cut: A (mira, ada) 10:00-10:30, B (ada, tomas) 10:32-10:42, A2 (mira, ada) at 10:45. Mira sat B out:
      her mood at A2 ages over her own fifteen minutes, not the run's three; Ada, there to B's end, gets exactly the
      run's gap plus B's unspent minutes - the old number; Tomas's first appearance keeps his sheet's mood; the
      operator is told; the replay re-derives every mood and condition.
  [2] a walk-out: A (all three, 10:00-10:30) - tomas walks out on his first line; B at 11:00. His mood and his
      energy take the rest of A as well as the gap, where the old rule gave him the gap alone.
  [3] a log from before 2026-09-22 records no room: its scene's cast counts as present - and no one else.
  [4] an opening after the run's first refuses to run without presence (PASSAGE_GAPS_MISSING).

The book is invented here (two keepers and a boatman on a rock), per hard rule 1. Script-style; exit 0 = all pass.
"""
import contextlib
import copy
import glob
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import bible, clock, condition, mood_fold, passage, rungs      # noqa: E402
from src.engine.records import Reading, RecordError                             # noqa: E402
from src.engine.state import build_profile, decay                               # noqa: E402
from test_condition import FLOW, _add_tomas, _cfg                               # noqa: E402  (one fixture, three suites)
from test_systems import _book                                                  # noqa: E402

FAILS = []
KEEPERS = [{"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}]
ALL3 = KEEPERS + [{"id": "tomas", "drive": "take the boat out"}]


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _run(tmp, decl, scenes, walker=None):
    """Scenes through scripts/scene.py main IN PROCESS (each after the first on a --resume), seats faked, with
    `passage.open_scene` watched. `walker` {scene name: id}: that character walks out on their first line there.
    -> (db, run_id, outputs, openings): openings[i] = {"before", "after", "result"} for scene i's opening."""
    import scene
    book = _book(tmp, decl)
    _add_tomas(book)
    outs, openings, now = [], [], {"scene": None}

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
        other = next(p for p in present if p != me)
        return ([Reading(path="WARINESS", rung=rungs.rung_at("WARINESS", 0.6 + 0.04 * ((turn or 0) % 8))[1], about=other,
                         confidence="sure"),
                 Reading(path="DISPLEASURE", rung=rungs.rung_at("DISPLEASURE", 0.9)[1], about=other, confidence="sure")],
                [other], "sure", [])

    real_open = passage.open_scene

    def watched(led, run_id, start_turn, at_minutes, lasts_minutes, budget, chars, **kw):
        before = {i: copy.deepcopy(c) for i, c in chars.items()}
        result = real_open(led, run_id, start_turn, at_minutes, lasts_minutes, budget, chars, **kw)
        openings.append({"before": before, "after": {i: copy.deepcopy(c) for i, c in chars.items()}, "result": result})
        return result

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv, passage.open_scene)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, refuse, emotion
    passage.open_scene = watched
    try:
        for i, (name, day, time, lasts, budget, extra) in enumerate(scenes):
            now["scene"] = name
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
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv, passage.open_scene = saved
    dbs = glob.glob(os.path.join(book, "runs", "*.db"))
    con = sqlite3.connect(dbs[0]) if dbs else None
    run = con.execute("SELECT run_id FROM runs").fetchone() if con else None
    return (dbs[0] if dbs else None), (run[0] if run else None), outs, openings


def _aged(ch, minutes):
    """The mood this sheet would carry after `minutes` out of the room: state.decay, as the opening calls it."""
    return decay(dict(ch["current"]["affect"]), ch["baseline"]["temperament"], build_profile(ch), elapsed=minutes)


def _replay_ok(db, run_id, label):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
    check("%s-the-replay-re-derives-every-mood-and-condition" % label,
          d["at"] is None and d["condition_at"] is None and not d["notes"] and not d["missing"], d)


def test_a_pov_cut(tmp):
    print("\n[1] a POV cut: whoever sat the middle scene out ages by their own time; a first appearance keeps the sheet")
    pov = (("keep-A", 1, "10:00", "30m", 2, None),
           ("boat-B", 1, "10:32", "10m", 1, {"cast": [KEEPERS[1], ALL3[2]]}),
           ("keep-A2", 1, "10:45", "20m", 2, None))
    db, run_id, outs, opened = _run(tmp, FLOW, pov)
    check("three-scenes-ran", len(opened) == 3 and all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    if len(opened) != 3:
        return
    b, a2 = opened[1], opened[2]
    check("the-run's-gap-at-A2-is-three-minutes", a2["result"]["elapsed"] == 3.0 and a2["result"]["owed"] == 0.0, a2["result"])
    check("mira's-own-time-away-is-fifteen", a2["result"]["own"].get("mira") == 15.0, a2["result"]["own"])
    mira_before = a2["before"]["mira"]
    got, want, old = a2["after"]["mira"]["current"]["affect"], _aged(mira_before, 15.0), _aged(mira_before, 3.0)
    check("her-mood-aged-over-her-own-fifteen-minutes", got == want, (got, want))
    check("...which-is-not-the-run's-three-(the-old-number)", want != old, (want, old))
    ada_before = a2["before"]["ada"]
    check("ada-there-to-B's-end-gets-exactly-the-old-number",
          a2["result"]["own"].get("ada") == 3.0 and a2["after"]["ada"]["current"]["affect"] == _aged(ada_before, 3.0),
          (a2["result"]["own"], a2["after"]["ada"]["current"]["affect"]))
    tomas_before = b["before"]["tomas"]
    check("tomas-first-appears-at-B-and-keeps-the-sheet's-mood",
          "tomas" not in b["result"]["own"] and b["after"]["tomas"]["current"]["affect"] == tomas_before["current"]["affect"],
          (b["result"]["own"], b["after"]["tomas"]["current"]["affect"]))
    check("...where-the-old-rule-would-have-faded-it", _aged(tomas_before, 2.0) != tomas_before["current"]["affect"])
    check("the-operator-is-told-who-was-away", "own time away: mira 15 min" in outs[2], outs[2][:1500])
    check("...and-who-first-appears", "tomas first appears" in outs[1], outs[1][:1500])
    check("...and-nothing-when-everyone-was-there-to-the-end", "own time away" not in outs[0])
    _replay_ok(db, run_id, "pov")


def test_a_walk_out(tmp):
    print("\n[2] a walk-out: the rest of the scene he left is his - mood and energy")
    first = [ALL3[2]] + KEEPERS                              # first in the cast, so he has the opening line
    walk = (("walk-A", 1, "10:00", "30m", 3, {"cast": first}),
            ("walk-B", 1, "11:00", "20m", 2, {"cast": ALL3}))
    db, run_id, outs, opened = _run(tmp, FLOW, walk, walker={"walk-A": "tomas"})
    check("two-scenes-ran", len(opened) == 2 and all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    if len(opened) != 2:
        return
    con = sqlite3.connect(db)
    left = con.execute("SELECT MIN(turn) FROM turns WHERE actor = 'tomas'").fetchone()[0]
    a_end = con.execute("SELECT end_turn FROM scenes ORDER BY start_turn").fetchone()[0]
    check("tomas-walked-out-before-A-ended", left is not None and left < a_end, (left, a_end))
    if left is None or left >= a_end:
        return
    rooms = [json.loads(m)["decay"]["here"] for (m,) in con.execute(
        "SELECT manifest FROM decision_manifests WHERE turn > ? AND turn <= ? ORDER BY turn", (left, a_end))]
    check("...and-the-room-after-him-did-not-hold-him", rooms and all("tomas" not in r for r in rooms), rooms)
    walked = 30.0 - (left + 1) * 10.0                    # A: thirty minutes, ten a beat; his beats end at his exit
    own = 30.0 + walked                                  # the half hour to 11:00, and the rest of A
    wb = opened[1]
    check("his-own-time-away-includes-the-rest-of-A", abs(wb["result"]["own"].get("tomas", -1) - own) < 1e-9,
          (wb["result"]["own"], own))
    check("...while-the-two-who-stayed-get-the-old-number",
          wb["result"]["own"].get("mira") == 30.0 and wb["result"]["own"].get("ada") == 30.0, wb["result"]["own"])
    t_before = wb["before"]["tomas"]
    got, want, old = wb["after"]["tomas"]["current"]["affect"], _aged(t_before, own), _aged(t_before, 30.0)
    check("his-mood-aged-over-all-of-it", got == want, (got, want))
    check("...which-is-not-the-gap-alone", want != old)
    c0 = t_before["current"]["condition"]
    e_new = condition.between(c0, 630.0, 660.0, walked, t_before["current"]["affect"])["energy"]
    e_old = condition.between(c0, 630.0, 660.0, 0.0, t_before["current"]["affect"])["energy"]
    e_got = wb["after"]["tomas"]["current"]["condition"]["energy"]
    check("his-energy-paid-for-the-rest-of-A-awake", abs(e_got - e_new) < 1e-12, (e_got, e_new))
    check("...where-the-old-count-charged-him-the-gap-alone", abs(e_new - e_old) > 1e-6, (e_new, e_old))
    _replay_ok(db, run_id, "walk-out")


def test_a_log_that_records_no_room(tmp):
    print("\n[3] a log from before 2026-09-22 records no room: its scene's cast counts as present, and no one else")
    pov = (("keep-A", 1, "10:00", "30m", 2, None),
           ("boat-B", 1, "10:32", "10m", 1, {"cast": [KEEPERS[1], ALL3[2]]}),
           ("keep-A2", 1, "10:45", "20m", 2, None))
    db, run_id, outs, opened = _run(tmp, None, pov)
    check("three-scenes-ran-in-a-book-without-the-energy-flow", len(opened) == 3 and all("SYSTEMEXIT" not in o for o in outs),
          [o[-300:] for o in outs])
    if len(opened) != 3:
        return
    check("...where-mira's-mood-still-ages-by-her-own-fifteen", opened[2]["result"]["own"].get("mira") == 15.0
          and opened[2]["after"]["mira"]["current"]["affect"] == _aged(opened[2]["before"]["mira"], 15.0), opened[2]["result"])
    _replay_ok(db, run_id, "flow-off")
    old = os.path.join(tmp, "roomless.db")
    src, dst = sqlite3.connect(db), sqlite3.connect(old)
    src.backup(dst)
    src.close()
    starts = [int(r[0]) for r in dst.execute("SELECT start_turn FROM scenes ORDER BY start_turn")]
    spoke = dst.execute("SELECT actor FROM turns WHERE turn = ?", (starts[1],)).fetchone()[0]
    silent = ({"ada", "tomas"} - {spoke}).pop()
    dst.execute("DROP TRIGGER decision_manifests_no_update")          # this copy plays a log written before the room was
    for turn, man in list(dst.execute("SELECT turn, manifest FROM decision_manifests")):
        m = json.loads(man)
        m.pop("decay", None)
        dst.execute("UPDATE decision_manifests SET manifest = ? WHERE turn = ?", (json.dumps(m), turn))
    dst.commit()
    dst.row_factory = sqlite3.Row
    check("the-copy-records-no-room", all("decay" not in json.loads(r[0]) for r in dst.execute("SELECT manifest FROM decision_manifests")))
    check("the-one-who-only-listened-in-B-(%s)-was-there-to-its-end" % silent,
          clock.presence_end(dst, run_id, silent, starts[2]) == {"end": 642.0, "owed": 0.0},
          clock.presence_end(dst, run_id, silent, starts[2]))
    check("...and-mira-who-was-not-in-B-is-not-counted-there",
          clock.presence_end(dst, run_id, "mira", starts[2]) == {"end": 630.0, "owed": 0.0},
          clock.presence_end(dst, run_id, "mira", starts[2]))
    check("...and-no-one-was-in-the-room-before-the-first-beat",
          clock.presence_end(dst, run_id, "tomas", starts[1]) is None, clock.presence_end(dst, run_id, "tomas", starts[1]))


def test_no_presence_is_refused():
    print("\n[4] an opening needs each character's presence")
    ch = {"current": {"affect": {"WARINESS": 0.6}}, "baseline": {"temperament": {}}}
    try:
        passage.apply_opening({"t": ch}, lambda i: [], 100.0, None)
        check("no-presence-is-refused", False, "did not raise")
    except RecordError as e:
        check("no-presence-is-refused", e.code == "PASSAGE_GAPS_MISSING", e.code)
    first = {"t": copy.deepcopy(ch)}
    passage.apply_opening(first, lambda i: [], 100.0, {"t": None})
    check("...while-a-first-appearance-ages-nothing", first["t"] == ch, first)


def main():
    print("test_absent_age.py — each character's mood ages by their own time out of the room\n")
    tmp = tempfile.mkdtemp(prefix="swe_absent_")
    try:
        test_a_pov_cut(os.path.join(tmp, "pov"))
        test_a_walk_out(os.path.join(tmp, "walk"))
        test_a_log_that_records_no_room(os.path.join(tmp, "roomless"))
        test_no_presence_is_refused()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_absent_age: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
