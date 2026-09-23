"""test_mood_fold.py — the mood tier, re-derived from the log (src/engine/mood_fold.py).

WHAT THIS PINS (gate mood-from-readings, 2026-09-22). The mood of record lived only in current_state, a
mutable cache; nothing re-derived it. `mood_fold.replay` rebuilds every cached mood - each speaker's and
each decayed bystander's - from the log and the sheets the run pinned, and this suite holds it to the
cache the drivers wrote, to 1e-12, over runs the real driver produced:

  [1] a stub run through the CLI - a fresh scene, then --resume after a declared gap - where every beat
      takes the no-readings path (`appraise`), and the resume prints the replay line;
  [2] a SEATED run, in process, with the model and both seats faked at their seams, so the receipt
      from readings (`receive`), the binds they make and the repetition count all run;
  [3] a cache row tampered with is named at its turn, character and path;
  [4] a turn outside every scene (the chair) stops the replay and says so.

The book is invented here (two keepers on a rock), per hard rule 1. Script-style; exit 0 = all pass.
"""
import contextlib
import copy
import glob
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import bible, mood_fold, rungs                     # noqa: E402
from src.engine.records import Reading, RecordError                # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _book(tmp):
    """Two keepers on a rock, each with an edge to the other, WARINESS raised so decay has work to do."""
    book = os.path.join(tmp, "The Rock and the Rose")
    for sub in ("world", "characters", "people"):
        os.makedirs(os.path.join(book, sub), exist_ok=True)
    world = dict(WORLD_ENGINE, people=[{"id": "mira", "what": "the keeper"}, {"id": "ada", "what": "the relief keeper"}])
    with open(os.path.join(book, "world", "The Rock.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\nid: The Rock\n---\n# The Rock\n\n```json\n%s\n```\n" % json.dumps(world, indent=1))
    for name, other in (("Mira", "ada"), ("Ada", "mira")):
        eng = copy.deepcopy(CHAR_ENGINE)
        eng["fixed"]["name"] = name
        eng["current"]["relationships"] = {other: {"trust": 0.7, "affinity": 0.65, "respect": 0.6, "debt": 0.0}}
        eng["current"]["affect"]["WARINESS"] = 0.75
        with open(os.path.join(book, "characters", "%s.md" % name), "w", encoding="utf-8") as fh:
            fh.write("---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(eng, indent=1)))
    return book


def _cfg(tmp, name, time, lasts):
    path = os.path.join(tmp, name + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"name": name, "at": {"day": 1, "time": time}, "lasts": lasts,
                   "situation": "The two keepers wait out the gale in the lamp room.",
                   "cast": [{"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}]}, fh)
    return path


def _cli(*args):
    r = subprocess.run([sys.executable, os.path.join("scripts", "scene.py")] + list(args), capture_output=True,
                       text=True, stdin=subprocess.DEVNULL, cwd=REPO, timeout=300)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _open(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con


def _copy_db(src, dst):
    """A COMPLETE copy: the chronicle runs in WAL mode, so a file copy can miss whatever the log has not
    checkpointed yet - measured here: a file copy taken while this suite held a connection lost the
    whole second scene. The backup API copies what a reader sees."""
    a, b = sqlite3.connect(src), sqlite3.connect(dst)
    with b:
        a.backup(b)
    a.close()
    b.close()
    return dst


def _agreement(con, run_id):
    """-> (largest |replay - cache| over every cached row, rows replayed, rows cached, bystander rows)."""
    got = mood_fold.replay(con, run_id, bible.for_run(con, run_id)[2])
    cache = {(r[0], r[1]): json.loads(r[2]) for r in con.execute(
        "SELECT turn, char_id, affect FROM current_state WHERE run_id = ?", (run_id,))}
    worst = max((abs(got[k][p] - v) for k in cache if k in got for p, v in cache[k].items()), default=float("inf"))
    speakers = {(r[0], r[1]) for r in con.execute("SELECT turn, actor FROM turns WHERE run_id = ?", (run_id,))}
    return worst, len(set(got) & set(cache)), len(cache), len(set(cache) - speakers)


def test_a_stub_run_is_rederived_exactly(tmp):
    print("\n[1] A STUB RUN (fresh, then --resume after 90 minutes): every cached mood re-derived")
    book = _book(tmp)
    rc1, _o1 = _cli("--book", book, "--scene", _cfg(tmp, "gale-1", "21:00", "1h"), "--stub", "--budget", "6")
    db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
    run_id = _open(db).execute("SELECT run_id FROM runs").fetchone()[0]
    rc2, out2 = _cli("--book", book, "--scene", _cfg(tmp, "gale-2", "23:30", "40m"), "--stub", "--budget", "4",
                     "--resume", run_id)
    check("both-scenes-ran", rc1 == 0 and rc2 == 0, out2[-600:])
    line = next((ln for ln in out2.splitlines() if "mood replay:" in ln), "")
    check("the-resume-prints-the-replay", "12 of 12 cached moods re-derived" in line and "largest difference none" in line, line)
    worst, both, cached, bystanders = _agreement(_open(db), run_id)
    check("every-row-replayed", both == cached and cached == 20, (both, cached))
    check("...including-the-bystanders-step-4-decayed", bystanders == 10, bystanders)
    check("...equal-to-the-cache-to-1e-12", worst <= 1e-12, worst)
    return db, run_id


def _seated(book, tmp, name, time, lasts, budget, resume=None):
    """scripts/scene.py main IN PROCESS, not stubbed: the actor answers through a faked `faithful_turn`
    (the driver's own import) addressing the other keeper, the event seat refuses (so the beat keeps the
    actor's own tags), and the emotion seat returns one WARINESS reading about the other keeper at a
    rung that cycles with the turn."""
    import scene
    calls = {"n": 0}

    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        calls["n"] += 1
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        return ({"action": "She trims the wick and says the wind is backing.", "thought": "", "exit": False,
                 "addressee": other, "act": "",
                 "tags": {"type": "mundane", "summary": "trims the wick", "dimensions": {"mastery": "mild"},
                          "durability": "transient", "subject": other,
                          # WHAT THE ACT SHOWED - so the listener's edge to the speaker MOVES every beat,
                          # and the replay must read each beat's bonds as they stood (bond-arithmetic s4)
                          "object": other, "showed": {"affinity": 0.85, "trust": 0.8}}}, [])

    def refuse(*_a, **_k):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked out of this test")

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=(), **_k):
        other = next(p for p in present if p != me)
        rung = rungs.rung_at("WARINESS", 0.35 + 0.1 * ((turn or 0) % 3))[1]
        return [Reading(path="WARINESS", rung=rung, about=other, confidence="sure")], [other], "sure", []

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, refuse, emotion
    sys.argv = ["scene.py", "--book", book, "--scene", _cfg(tmp, name, time, lasts), "--budget", str(budget),
                "--model", "fake/model", "--no-keeper"] + (["--resume", resume] if resume else [])
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            scene.main()
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv = saved
    return out.getvalue(), calls["n"]


def test_a_seated_run_is_rederived_exactly(tmp):
    print("\n[2] A SEATED RUN (readings -> the receipt, their binds, the repetition count), fresh then resumed")
    book = _book(tmp)
    out1, n1 = _seated(book, tmp, "gale-1", "21:00", "1h", 5)
    db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
    run_id = _open(db).execute("SELECT run_id FROM runs").fetchone()[0]
    out2, n2 = _seated(book, tmp, "gale-2", "22:30", "30m", 3, resume=run_id)
    con = _open(db)
    n_read = con.execute("SELECT COUNT(*) FROM readings WHERE run_id = ?", (run_id,)).fetchone()[0]
    n_bind = con.execute("SELECT COUNT(*) FROM target_binds WHERE run_id = ?", (run_id,)).fetchone()[0]
    n_edge = con.execute("SELECT COUNT(*) FROM relationship_deltas WHERE run_id = ?", (run_id,)).fetchone()[0]
    check("the-actor-and-the-emotion-seat-answered", n1 >= 2 and n2 >= 1 and n_read >= 3 and n_bind >= 1, (n1, n2, n_read, n_bind))
    check("...and-the-bonds-moved-mid-scene", n_edge >= 2, n_edge)
    line = next((ln for ln in out2.splitlines() if "mood replay:" in ln), "")
    check("the-resume-prints-the-replay-with-no-difference", "largest difference none" in line, line)
    worst, both, cached, _b = _agreement(con, run_id)
    check("every-row-replayed", both == cached and cached >= 6, (both, cached))
    check("...equal-to-the-cache-to-1e-12", worst <= 1e-12, worst)
    return db, run_id


def test_a_tampered_row_is_named(tmp, db, run_id):
    print("\n[3] A TAMPERED CACHE ROW is named at its turn, character and path")
    copy_db = _copy_db(db, os.path.join(tmp, "tampered.db"))
    con = _open(copy_db)
    # THE LAST ROW OF THE FIRST SCENE - the very row the second scene's resume restored from. A replay that
    # read the cache would carry the tampered value into every later beat; this one must not.
    end1 = con.execute("SELECT end_turn FROM scenes WHERE run_id = ? ORDER BY start_turn LIMIT 1", (run_id,)).fetchone()[0]
    cid, affect = con.execute("SELECT char_id, affect FROM current_state WHERE run_id = ? AND turn = ? "
                              "ORDER BY char_id LIMIT 1", (run_id, end1)).fetchone()
    moved = dict(json.loads(affect), WARINESS=0.5 if json.loads(affect)["WARINESS"] < 0.45 else 0.3)
    with con:
        con.execute("UPDATE current_state SET affect = ? WHERE run_id = ? AND turn = ? AND char_id = ?",
                    (json.dumps(moved), run_id, end1, cid))
    d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
    check("the-divergence-names-the-row", d["at"] == (end1, cid, "WARINESS") and d["largest"] > 0.05, d)
    got = mood_fold.replay(con, run_id, bible.for_run(con, run_id)[2])
    off = [k for k, v in ((k, json.loads(a)) for k, a in (((r[0], r[1]), r[2]) for r in con.execute(
        "SELECT turn, char_id, affect FROM current_state WHERE run_id = ?", (run_id,))))
           if max(abs(got[k][p] - x) for p, x in v.items()) > 1e-12]
    check("...and-no-other-row-moves-the-replay-never-reads-the-cache", off == [(end1, cid)], off)


def test_a_chair_turn_stops_the_replay(tmp, db, run_id):
    print("\n[4] A TURN OUTSIDE EVERY SCENE (the chair) stops the replay, and it says so")
    copy_db = _copy_db(db, os.path.join(tmp, "chair.db"))
    con = _open(copy_db)
    first = con.execute("SELECT MIN(start_turn) FROM scenes WHERE run_id = ?", (run_id,)).fetchone()[0]
    second = con.execute("SELECT MAX(start_turn) FROM scenes WHERE run_id = ?", (run_id,)).fetchone()[0]
    with con:                     # the second scene now starts one turn later: its first turn is nobody's
        con.execute("DROP TRIGGER IF EXISTS scenes_no_update")       # a scratch copy; the live log refuses this
        con.execute("UPDATE scenes SET start_turn = ? WHERE run_id = ? AND start_turn = ?", (second + 1, run_id, second))
    notes = []
    got = mood_fold.replay(con, run_id, bible.for_run(con, run_id)[2], notes)
    check("the-replay-stops-before-the-stray-turn", got and max(t for t, _c in got) < second and first == 0, sorted(got)[-2:])
    check("...and-names-it", any("outside every scene" in n for n in notes), notes)


def main():
    print("test_mood_fold.py — the mood tier, re-derived from the log\n")
    tmp = tempfile.mkdtemp(prefix="swe_mood_fold_")
    try:
        db, run_id = test_a_stub_run_is_rederived_exactly(os.path.join(tmp, "stub"))
        test_a_seated_run_is_rederived_exactly(os.path.join(tmp, "seated"))
        test_a_tampered_row_is_named(tmp, db, run_id)
        test_a_chair_turn_stops_the_replay(tmp, db, run_id)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_mood_fold: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
