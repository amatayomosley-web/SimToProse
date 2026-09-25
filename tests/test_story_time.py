"""test_story_time.py — bonds, scars, attitudes and resting means run on story time (gate slow-tiers-run).

WHAT THIS PINS (2026-09-24). The owner: "these are real people, the book is us peeking into their world. When we
look doesn't determine their state, their stat runs with or without us looking" (docs/design.md). The slow tiers
aged only across the declared gaps between scenes: a scene that lasted half a day moved no bond, eased no scar,
faded no attitude, for anyone. Now every stretch of story time does - each opening's gap plus what the last scene
left unspent, and every beat's own minutes - for the whole cast, in the room or out of it, live and in the folds.

  [1] a long scene ages the slow tiers beat by beat, and at every beat the state the drivers held is exactly
      what the folds rebuild from the log (every cast member, speaker or not);
  [2] a character who sat a scene out comes back aged through it, exactly as the log's stretches say;
  [3] a scene that ended early owes its unspent minutes to the slow tiers at the next opening;
  [4] a reading an aborted launch left behind ages no one twice when the scene is launched again;
  [5] a chair session under one `--at` counts its declared span once;
  and on every run the mood replay re-derives every mood and condition exactly.

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

from src.engine import bible, bond_rest, clock, heritable, mood_fold, passage, rungs, wound   # noqa: E402
from src.engine.ledger import Ledger                                              # noqa: E402
from src.engine.records import PATHS, Reading, RecordError, TurnCommit            # noqa: E402
from test_condition import FLOW, _add_tomas, _cfg                                 # noqa: E402  (one fixture, three suites)
from test_systems import _book                                                    # noqa: E402

FAILS = []
KEEPERS = [{"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}]
TOMAS = {"id": "tomas", "drive": "take the boat out"}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _slow(ch):
    """The slow tiers of one sheet, as comparable data."""
    cur, base = ch.get("current") or {}, ch.get("baseline") or {}
    edges = {}
    for t, e in (cur.get("relationships") or {}).items():
        if isinstance(e, dict):
            edges[t] = {k: (dict(v) if isinstance(v, dict) else v) for k, v in e.items()
                        if k in ("trust", "affinity", "respect", "debt", "their_view")}
    return {"edges": edges,
            "wounds": {w["id"]: w["intensity"] for w in (base.get("wounds") or []) if isinstance(w, dict) and "intensity" in w},
            "means": {p: r["mean"] for p, r in (base.get("temperament") or {}).items() if isinstance(r, dict) and "mean" in r},
            "toward": {w: dict(v) for w, v in (cur.get("toward") or {}).items() if v}}


def _run(tmp, scenes, walker=None, orphan_before=None):
    """Scenes through scripts/scene.py main IN PROCESS, seats faked, `passage.age` watched. `walker` {scene: id}
    walks out on their first line there; `orphan_before` (a scene name) logs that scene's reading first, as a launch
    that died at its opening would have. -> (db, run_id, outs, steps): steps = [(scene, "opening"|"beat", minutes,
    {id: slow state BEFORE the step})] in call order."""
    import scene
    book = _book(tmp, FLOW)
    _add_tomas(book)
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
        other = next(p for p in present if p != me)
        return ([Reading(path="WARINESS", rung=rungs.rung_at("WARINESS", 0.6 + 0.04 * ((turn or 0) % 8))[1], about=other,
                         confidence="sure"),
                 Reading(path="DISPLEASURE", rung=rungs.rung_at("DISPLEASURE", 0.9)[1], about=other, confidence="sure")],
                [other], "sure", [])

    real_age, real_open = passage.age, passage.apply_opening

    real_replay = mood_fold.replay

    def watched_age(chars, minutes, rest_rows):
        if not now["replay"]:                          # the resume's own replay check ages its copies too
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
        for i, (name, day, time, lasts, budget, extra) in enumerate(scenes):
            now["scene"] = name
            path = _cfg(tmp, name, day, time, lasts, extra)
            argv = ["scene.py", "--book", book, "--scene", path, "--budget", str(budget), "--model", "fake/model", "--no-keeper"]
            if i:
                db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
                con = sqlite3.connect(db)
                run_id = con.execute("SELECT run_id FROM runs").fetchone()[0]
                if orphan_before == name:                # the reading a launch that died at its opening left behind
                    start = con.execute("SELECT MAX(turn) FROM turns").fetchone()[0] + 1
                    at, span = clock.parse_at({"day": day, "time": time}), clock.span_minutes(lasts)
                    con.execute("INSERT INTO scene_clock (run_id, turn, at_minutes, lasts_minutes, beat_minutes) VALUES (?,?,?,?,?)",
                                (run_id, start, at, span, span / float(budget)))
                    con.commit()
                argv += ["--resume", run_id]
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


def _con(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con


def _folded(con, run_id, cid, before_turn):
    """One sheet as the folds rebuild it from the log before a turn: the pinned sheet, the arc, the bonds and holds,
    the attitude and the wounds - what a resume at that turn starts from."""
    ch = copy.deepcopy(bible.for_run(con, run_id)[2][cid])
    heritable.ensure_temperament(ch)                       # as the drivers' first profile does, before anything ages
    passage.stamp_authored(ch)
    ch = passage.fold_arc(con, run_id, cid, ch, before_turn=before_turn)
    bond_rest.rehydrate(ch["current"].setdefault("relationships", {}), ch["baseline"].get("relationship_priors", {}),
                        [it for _t, _s, it in bond_rest.timeline_rows(con, run_id, cid, before=(before_turn, 0))],
                        attachments=ch["current"].setdefault("attachments", {}))
    passage.fold_toward(con, run_id, cid, ch, before_turn=before_turn)
    passage.fold_wounds(con, run_id, cid, ch, before_turn=before_turn)
    return _slow(ch)


def _replay_ok(db, run_id, label):
    con = _con(db)
    d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
    check("%s-the-replay-re-derives-every-mood-and-condition" % label,
          d["at"] is None and d["condition_at"] is None and not d["notes"] and not d["missing"], d)


def _beats_by_turn(con, steps, name):
    """The driver's per-beat steps of one scene, keyed by the turn each ran at."""
    row = con.execute("SELECT start_turn, end_turn FROM scenes s JOIN scene_cfgs c ON c.fingerprint = s.cfg_fingerprint "
                      "WHERE s.label = ?", (name,)).fetchone()
    beats = [s for s in steps if s[0] == name and s[1] == "beat"]
    return {int(row[0]) + k: s for k, s in enumerate(beats)}, int(row[0]), int(row[1])


def test_a_long_scene(tmp):
    print("\n[1] a long scene: every beat's minutes age the slow tiers, and the folds rebuild what the drivers held")
    scenes = (("vigil-A", 1, "08:00", "12h", 3, {"cast": KEEPERS}), ("vigil-B", 2, "08:00", "6h", 2, {"cast": KEEPERS}))
    db, run_id, outs, steps = _run(tmp, scenes)
    check("two-scenes-ran", all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    con = _con(db)
    beats, start, end = _beats_by_turn(con, steps, "vigil-A")
    check("every-beat-took-its-four-hours", sorted(beats) == list(range(start, end + 1))
          and all(s[2] == 240.0 for s in beats.values()), [(t, s[2]) for t, s in sorted(beats.items())])
    scar0 = beats[start][3]["mira"]["wounds"]
    scar_n = _folded(con, run_id, "mira", end + 1)["wounds"]
    check("the-scar-eased-inside-the-scene", all(scar_n[w] < scar0[w] for w in scar0), (scar0, scar_n))
    want = dict(scar0)
    for _k in range(end - start + 1):
        want = {w: v + wound.erode({"intensity": v, "id": w}, 240.0 / 1440.0) for w, v in want.items()}
    untouched = [w for w in scar0 if not con.execute("SELECT 1 FROM wound_deltas WHERE char_id = 'mira' AND wound_id = ?",
                                                        (w,)).fetchone()]
    check("...an-untouched-scar-by-exactly-its-beats'-minutes", untouched and all(abs(scar_n[w] - want[w]) < 1e-15 for w in untouched),
          (untouched, scar_n, want))
    mismatches = []
    for name in ("vigil-A", "vigil-B"):
        per_turn, s0, _e = _beats_by_turn(con, steps, name)
        for t, (_n, _k, _m, held) in sorted(per_turn.items()):
            if t == s0:
                continue                                   # the scene's first beat also carries its opening's stretch
            for cid, state in held.items():
                got = _folded(con, run_id, cid, t)
                if state != got:
                    mismatches.append((name, t, cid, {k: (state[k], got[k]) for k in state if state[k] != got[k]}))
    check("at-every-beat-every-cast-member's-state-is-what-the-folds-rebuild", not mismatches and len(steps) > 4, mismatches)
    _replay_ok(db, run_id, "long")


def test_an_absent_character(tmp):
    print("\n[2] a character who sat a scene out comes back aged through it")
    scenes = (("keep-A", 1, "08:00", "6h", 2, {"cast": KEEPERS}),
              ("boat-B", 1, "15:00", "8h", 2, {"cast": [KEEPERS[1], TOMAS]}),
              ("keep-A2", 2, "01:00", "4h", 2, {"cast": KEEPERS}))
    db, run_id, outs, steps = _run(tmp, scenes)
    check("three-scenes-ran", all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    con = _con(db)
    starts = [int(r[0]) for r in con.execute("SELECT start_turn FROM scenes ORDER BY start_turn")]
    at_b = _folded(con, run_id, "mira", starts[1])            # the end of A: what she carried out of the room
    opening = next(s for s in steps if s[0] == "keep-A2" and s[1] == "opening")
    held = opening[3]["mira"]                                 # what her resume rebuilt, before A2's own opening
    want = dict(at_b["wounds"])
    for t, _slot, m in clock.time_items(con, run_id, starts[2]):
        if t >= starts[1]:                                    # B's opening and B's beats: time she was not in the room
            want = {w: v + wound.erode({"intensity": v, "id": w}, m / 1440.0) for w, v in want.items()}
    check("she-had-no-movement-of-her-own-in-B", not con.execute(
        "SELECT 1 FROM wound_deltas WHERE char_id = 'mira' AND turn >= ? AND turn < ?", (starts[1], starts[2])).fetchone())
    check("her-scar-eased-over-every-minute-of-B", all(abs(held["wounds"][w] - want[w]) < 1e-15 for w in want)
          and all(held["wounds"][w] < at_b["wounds"][w] for w in want), (held["wounds"], want, at_b["wounds"]))
    check("...and-her-bond-drifted-through-it-too", held["edges"] != at_b["edges"], (held["edges"], at_b["edges"]))
    _replay_ok(db, run_id, "absent")


def test_owed_minutes(tmp):
    print("\n[3] a scene that ended early owes its unspent minutes to the slow tiers at the next opening")
    scenes = (("short-A", 1, "08:00", "6h", 3, {"cast": KEEPERS}), ("short-B", 1, "16:00", "2h", 2, {"cast": KEEPERS}))
    db, run_id, outs, steps = _run(tmp, scenes, walker={"short-A": "ada"})
    con = _con(db)
    starts = [int(r[0]) for r in con.execute("SELECT start_turn FROM scenes ORDER BY start_turn")]
    check("A-ended-early-on-a-walk-out", starts[1] - starts[0] < 3, starts)
    opening = next(s for s in steps if s[0] == "short-B" and s[1] == "opening")
    unspent = 360.0 - (starts[1] - starts[0]) * 120.0
    check("B's-opening-aged-the-slow-tiers-by-the-gap-AND-A's-unspent-minutes",
          abs(opening[2] - ((960.0 - 840.0) + unspent)) < 1e-9 and unspent > 0, (opening[2], unspent))
    _replay_ok(db, run_id, "owed")


def test_an_aborted_launch(tmp):
    print("\n[4] a reading an aborted launch left behind ages no one twice")
    scenes = (("try-A", 1, "08:00", "6h", 6, {"cast": KEEPERS}), ("try-B", 1, "20:00", "4h", 2, {"cast": KEEPERS}))
    db, run_id, outs, steps = _run(tmp, scenes, orphan_before="try-B")
    check("the-relaunch-ran", all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    con = _con(db)
    starts = [int(r[0]) for r in con.execute("SELECT start_turn FROM scenes ORDER BY start_turn")]
    check("...after-A-moved-a-resting-mean-BEFORE-the-relaunch-(so-a-second-fade-would-show)",   # arc.erode moves
          con.execute("SELECT COUNT(*) FROM arc_diffs WHERE turn < ?", (starts[1],)).fetchone()[0] > 0)   # only a moved mean
    opening = next(s for s in steps if s[0] == "try-B" and s[1] == "opening")
    for cid in ("mira", "ada"):
        got = _folded(con, run_id, cid, starts[1])
        check("%s-resumed-from-the-log-before-the-opening-and-no-further" % cid, opening[3][cid] == got,
              {k: (opening[3][cid][k], got[k]) for k in got if opening[3][cid][k] != got[k]})
    _replay_ok(db, run_id, "relaunch")


def test_a_chair_session():
    print("\n[5] a chair session under one `--at` counts its declared span once")
    led = Ledger(":memory:")
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    led.register_character("r", "m", {"id": "m", "name": "M"}, {})
    led.record_scene_clock("r", 5, 600.0, 30.0, 30.0)        # the chair's opening: budget one, thirty minutes
    for t in (5, 6):
        led.append_turn(TurnCommit(run_id="r", turn=t, actor="m", thought="-", action="-", tags={},
                                   validation={"ok": True}, affect={p: 0.2 for p in PATHS}))
    check("the-first-turn-takes-the-span", clock.beat_minutes(led.con, "r", 5) == 30.0)
    check("...the-second-takes-none", clock.beat_minutes(led.con, "r", 6) == 0.0)
    check("...and-the-story-stops-at-the-span's-end", clock.beat_end(led.con, "r", 6) == 630.0
          and clock.story_now(led.con, "r") == 630.0, (clock.beat_end(led.con, "r", 6), clock.story_now(led.con, "r")))
    check("the-folds-see-one-stretch", clock.time_items(led.con, "r") == [(5, 3, 30.0)], clock.time_items(led.con, "r"))
    # A BEAT'S OWN ROWS COME AFTER ITS MINUTES: a cliff the beat made must not be the rest its own drift ran toward
    from src.engine.records import RestDeclared
    led.register_character("r", "e", {"id": "e", "name": "E"}, {})
    with led.con:
        bond_rest.write(led.con, "r", 5, [RestDeclared("m", "e", "trust", 0.1, "cliff")])
        led.con.execute("INSERT INTO relationship_deltas(run_id, turn, perceiver, target, axis, delta, ord) "
                        "VALUES ('r', 5, 'm', 'e', 'trust', -0.3, 'first')")
    order = [it[0] for t, _s, it in bond_rest.timeline_rows(led.con, "r", "m") if t == 5]
    check("within-a-beat-its-minutes-then-its-cliff-then-its-movement", order == ["time", "rest", "edge"], order)


def main():
    print("test_story_time.py — bonds, scars, attitudes and resting means run on story time\n")
    tmp = tempfile.mkdtemp(prefix="swe_story_")
    try:
        test_a_long_scene(os.path.join(tmp, "long"))
        test_an_absent_character(os.path.join(tmp, "absent"))
        test_owed_minutes(os.path.join(tmp, "owed"))
        test_an_aborted_launch(os.path.join(tmp, "relaunch"))
        test_a_chair_session()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_story_time: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
