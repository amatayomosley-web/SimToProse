#!/usr/bin/env python3
"""test_opening_profile.py — a scene's first beat feels the opening's fade (gate opening-before-profile).

`scripts/scene.py` built each actor's profile when it assembled the cast, BEFORE `passage.open_scene` faded
wounds, arcs and attitude across the gap since the last scene. The profile carries the investment a reading
about a wound is multiplied by (`connection.held_map`), so for a scene's first beats a scar that had faded
over a month was still felt at its old depth, until a wound or an arc next changed. `mood_fold.replay`
mirrored the same order, so the resume check agreed with the defect. `connection.held_map`'s docstring said
the profile was rebuilt per beat; it was not.

Two scenes a month apart through `scripts/scene.py` main IN PROCESS, the actor and both seats faked (the
emotion seat reads every beat as about the scar), and two spies: one on `build_profile`, one on
`passage.open_scene`. The profile built after the second opening must carry the faded scar, and the replay
must re-derive every cached mood of both scenes.

Script-style, stdlib only, exit 0 = all pass.
"""
import contextlib
import glob
import io
import os
import sqlite3
import sys
import tempfile
import json
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import bible, mood_fold, passage, rungs            # noqa: E402
from src.engine.records import Reading, RecordError                # noqa: E402
from test_systems import _book                                     # noqa: E402  (one fixture: two keepers, a scar)

FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % str(detail)[:400]))
    if not ok:
        FAILS.append(name)


def _cfg(tmp, name, day, lasts):
    path = os.path.join(tmp, name + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"name": name, "at": {"day": day, "time": "21:00"}, "lasts": lasts,
                   "situation": "The two keepers wait out the gale in the lamp room.",
                   "cast": [{"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}]}, fh)
    return path


def _scar(ch):
    w = next((x for x in ((ch.get("baseline") or {}).get("wounds") or [])
              if isinstance(x, dict) and x.get("concept") == "drowning"), None)
    return None if w is None else float(w["intensity"])


def _two_scenes(tmp):
    """-> (db, run_id, [("open",) | ("beat",) | ("profile", who, scar intensity)] in call order)."""
    import scene
    book = _book(tmp)
    calls = []

    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        calls.append(("beat", None, None))
        return ({"action": "She watches the swell and says nothing about the boat.", "thought": "", "exit": False,
                 "addressee": other, "act": "",
                 "tags": {"type": "mundane", "summary": "watches the swell", "dimensions": {}, "durability": "transient",
                          "subject": other}}, [])

    def refuse(*_a, **_k):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked out of this test")

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=(), **_k):
        other = next(p for p in present if p != me)
        # EVERY BEAT IS ABOUT THE SCAR, so its investment - read off the profile - prices every reading
        return ([Reading(path="DEFLATION", rung=rungs.rung_at("DEFLATION", 0.5)[1], about="concept:drowning",
                         confidence="sure")], [other], "sure", [])

    real_bp, real_open = scene.build_profile, passage.open_scene

    def spy_profile(ch):
        calls.append(("profile", str(ch["fixed"]["name"]).lower(), _scar(ch)))
        return real_bp(ch)

    def spy_open(*a, **k):
        calls.append(("open", None, None))
        return real_open(*a, **k)

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, refuse, emotion
    scene.build_profile, passage.open_scene = spy_profile, spy_open
    try:
        for i, (name, day, lasts, budget) in enumerate((("gale-1", 1, "1h", 4), ("gale-2", 30, "30m", 2))):
            argv = ["scene.py", "--book", book, "--scene", _cfg(tmp, name, day, lasts), "--budget", str(budget),
                    "--model", "fake/model", "--no-keeper"]
            if i:
                db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
                argv += ["--resume", sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0]]
            sys.argv = argv
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                scene.main()
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv = saved
        scene.build_profile, passage.open_scene = real_bp, real_open
    db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
    return db, sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0], calls


def main():
    print("test_opening_profile.py — a scene's first beat feels the opening's fade\n")
    tmp = tempfile.mkdtemp(prefix="swe_openprof_")
    try:
        db, run_id, calls = _two_scenes(tmp)
        opens = [i for i, c in enumerate(calls) if c[0] == "open"]
        check("both-scenes-opened-through-open_scene", len(opens) == 2, calls[:6])
        second = opens[-1] if opens else len(calls)
        first_beat = next((i for i in range(second, len(calls)) if calls[i][0] == "beat"), len(calls))
        for who in ("mira", "ada"):
            before = [c[2] for c in calls[:second] if c[0] == "profile" and c[1] == who]
            # BETWEEN the opening and the scene's first beat - a rebuild a wound's trial triggers later does not count
            after = [c[2] for c in calls[second:first_beat] if c[0] == "profile" and c[1] == who]
            check("%s-a-profile-is-built-after-the-opening-and-BEFORE-the-first-beat" % who, bool(after),
                  calls[second:first_beat + 1])
            check("...and-it-carries-the-FADED-scar" % (), bool(before and after) and after[0] < before[-1],
                  (before[-1:] if before else None, after[:1]))
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
        check("the-replay-re-derives-every-cached-mood-of-both-scenes", d["at"] is None and not d["notes"], d)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nVERDICT: %s" % ("PASS" if not FAILS else "FAIL -> %s" % FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
