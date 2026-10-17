"""test_scene_rounds.py — the round (conversation design v2 section 3, gate round-loop), through scripts/scene.py main.

After every move the engine offers the floor: it asks the listeners in urge order (in a two-hander, the other one
always), each answers under the listener contract (take, interject, hold), and a speaker nobody interrupted is
called again under the speaker contract (keep, yield). This suite scripts the ACTOR - who it is, the stance it was
asked in, what it answers - and reads what the driver did with it: the calls it made and the rows it committed.

The fixture is invented: three keepers on a rock (the test_systems sheets, a third added).
"""
import copy
import json
import os
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from test_seat_replies import EMOTION, EVENT, _drive, _seats    # noqa: E402
from test_systems import CHAR_ENGINE, WORLD_ENGINE              # noqa: E402

FAILS = []
CAST = (("Mira", "mira", "keep the lamp lit"), ("Ada", "ada", "get the boat ready"), ("Tomas", "tomas", "mend the net"))


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "\n        %s" % (detail,)))
    if not ok:
        FAILS.append(name)


def _book(tmp, who):
    book = os.path.join(tmp, "The Rock")
    for sub in ("world", "characters", "people"):
        os.makedirs(os.path.join(book, sub), exist_ok=True)
    cast = [c for c in CAST if c[1] in who]
    world = dict(WORLD_ENGINE, people=[{"id": i, "what": "a keeper"} for _n, i, _d in cast])
    with open(os.path.join(book, "world", "The Rock.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\nid: The Rock\n---\n# The Rock\n\n```json\n%s\n```\n" % json.dumps(world, indent=1))
    for name, i, _d in cast:
        eng = copy.deepcopy(CHAR_ENGINE)
        eng["fixed"]["name"] = name
        eng["current"]["relationships"] = {o: {"trust": 0.7, "affinity": 0.65, "respect": 0.6, "debt": 0.0}
                                           for _n, o, _x in cast if o != i}
        with open(os.path.join(book, "characters", "%s.md" % name), "w", encoding="utf-8") as fh:
            fh.write("---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(eng, indent=1)))
    cfg = os.path.join(tmp, "gale.json")
    with open(cfg, "w", encoding="utf-8") as fh:
        json.dump({"name": "gale", "at": {"day": 1, "time": "21:00"}, "lasts": "1h",
                   "situation": "The keepers wait out the gale in the lamp room.",
                   "cast": [{"id": i, "drive": d} for _n, i, d in cast]}, fh)
    return book, cfg


def _rows(book):
    import glob
    dbs = glob.glob(os.path.join(book, "runs", "*.db"))
    if not dbs:
        return []
    con = sqlite3.connect(dbs[0])
    try:
        return [{"actor": a, "action": x, "thought": t, "floor": f, "addressee": d, "validation": json.loads(v)}
                for a, x, t, f, d, v in con.execute(
                    "SELECT actor, action, thought, floor, addressee, validation FROM turns ORDER BY turn")]
    finally:
        con.close()


def _actor(script, calls):
    """The actor, scripted: `script(who, stance, flags, n)` -> (action, thought, floor, addressee) for this person's
    n-th call; every call is recorded as (who, stance, flags, event_text, steer)."""
    seen = {}

    def fake(packet, event_text, temperament, model, stub, **kw):
        who = kw["char_id"]
        floor = dict(kw.get("floor") or {})
        stance = floor.pop("stance", None)
        floor.pop("last_thought", None)
        n = seen[who] = seen.get(who, -1) + 1
        calls.append((who, stance, floor, event_text, kw.get("steer")))
        action, thought, word, to = script(who, stance, floor, n, kw.get("steer"))
        return ({"action": action, "thought": thought, "exit": False, "addressee": to, "act": "", "floor": word,
                 "tags": {"type": "mundane", "summary": action or "-", "dimensions": {}, "durability": "transient",
                          "subject": to}}, [])
    return fake


def _run(tmp, who, script, budget, stub=True):
    import scene
    book, cfg = _book(tmp, who)
    calls, saved = [], scene.faithful_turn
    scene.faithful_turn = _actor(script, calls)
    try:
        if stub:
            out, exited = _drive("scene", book, ["--scene", cfg, "--budget", str(budget), "--stub"])
        else:
            seat_calls = []
            with _seats({"appraise-event": [EVENT], "appraise-emotion": [EMOTION]}, seat_calls):
                out, exited = _drive("scene", book, ["--scene", cfg, "--budget", str(budget)])
            calls.append(("seats", seat_calls))
    finally:
        scene.faithful_turn = saved
    return out, exited, calls, _rows(book)


def _other(who):
    return "ada" if who == "mira" else "mira"


def test_a_two_hander_asks_the_other_after_every_move(tmp):
    def script(who, stance, flags, n, steer):
        return ("%s says a thing %d." % (who, n), "-", "yield" if stance == "speaker" else "take", _other(who))
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 4)
    check("two-hander:-four-rows,-alternating", exited is None and [r["actor"] for r in rows] == ["mira", "ada", "mira", "ada"],
          (exited, [r["actor"] for r in rows], out[-600:]))
    check("...the-first-call-a-speaker,-every-later-call-a-listener-asked",
          [c[1] for c in calls[:4]] == ["speaker", "listener", "listener", "listener"], [c[:2] for c in calls])
    check("...each-row-carries-its-floor-word", [r["floor"] for r in rows] == ["yield", "take", "take", "take"],
          [r["floor"] for r in rows])


def test_a_speaker_who_keeps_goes_on_and_an_empty_hold_commits_nothing(tmp):
    """keep, keep, yield from the speaker; the listener holds with nothing every time: three rows, all the
    speaker's; the speaker is re-called with `resumed`; after the yield the listener is asked once more with the
    forced line, holds again, and the scene has settled."""
    def script(who, stance, flags, n, steer):
        if who == "mira":
            return ("Mira's paragraph %d." % n, "-", ("keep", "keep", "yield")[min(n, 2)], "ada")
        return ("", "", "hold", "")
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 10)
    check("keep-keep-yield:-three-rows-by-the-speaker", [(r["actor"], r["floor"]) for r in rows]
          == [("mira", "keep"), ("mira", "keep"), ("mira", "yield")], ([(r["actor"], r["floor"]) for r in rows], out[-600:]))
    mira = [c for c in calls if c[0] == "mira"]
    check("...re-called-to-go-on-from-where-they-stopped", [c[2] for c in mira] == [{}, {"resumed": True}, {"resumed": True}],
          [c[2] for c in mira])
    ada = [c[2] for c in calls if c[0] == "ada"]
    check("...the-listener-asked-after-every-move,-then-once-with-the-floor-forced",
          ada == [{}, {}, {}, {"forced": True}], ada)
    check("...and-a-second-hold-settles-the-scene", "scene ended: settled" in out, out[-300:])


def test_a_silence_is_committed_and_not_read(tmp):
    """A hold with a thought and no act is a row - the POV's silence - and the event seat is not asked about it."""
    def script(who, stance, flags, n, steer):
        if stance == "listener":
            return ("", "He says nothing; he will not give her that.", "hold", "")
        return ("Mira's line %d." % n, "-", "keep" if n < 1 else "yield", "ada")
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 3, stub=False)
    seats = dict(c for c in calls if c[0] == "seats")["seats"]
    silent = [r for r in rows if r["actor"] == "ada"]
    check("a-silent-hold-is-a-row-with-its-thought", exited is None and silent and silent[0]["floor"] == "hold"
          and silent[0]["action"] == "" and "will not give her that" in silent[0]["thought"], (exited, rows, out[-500:]))
    check("...and-the-event-seat-read-only-the-acts", seats.count("appraise-event") == len(rows) - len(silent),
          (seats, len(rows), len(silent)))


def test_alone_on_stage_a_keep_goes_on(tmp):
    def script(who, stance, flags, n, steer):
        return ("Mira thinks aloud, %d." % n, "-", ("keep", "keep", "yield")[min(n, 2)], "")
    out, exited, calls, rows = _run(tmp, ("mira",), script, 10)
    check("a-one-person-scene-keeps-going-past-one-beat", [r["floor"] for r in rows] == ["keep", "keep", "yield"],
          ([r["floor"] for r in rows], out[-400:]))
    check("...and-a-yield-with-nobody-to-ask-ends-it-empty", "scene ended: empty" in out, out[-200:])


def test_a_crowd_asks_the_addressed_first_and_a_take_ends_the_round(tmp):
    def script(who, stance, flags, n, steer):
        if stance == "speaker":
            return ("%s asks Ada about the boat." % who, "-", "yield", "ada")
        return ("%s answers." % who, "-", "take", "mira")
    out, exited, calls, rows = _run(tmp, ("mira", "ada", "tomas"), script, 3)
    check("crowd:-the-addressed-listener-is-asked-first", calls[1][:2] == ("ada", "listener"), [c[:2] for c in calls])
    check("...and-her-take-is-the-next-row:-the-one-below-the-floor-is-never-asked",
          [r["actor"] for r in rows][:2] == ["mira", "ada"] and "tomas" not in [c[0] for c in calls],
          ([r["actor"] for r in rows], [c[:2] for c in calls]))


def test_a_long_move_is_drawn_again_once_and_flagged(tmp):
    def script(who, stance, flags, n, steer):
        if who == "mira" and not steer and n == 0:
            return (" ".join(["word"] * 100), "-", "yield", "ada")
        return ("A short line.", "-", "yield" if stance == "speaker" else "take", _other(who))
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 2)
    steered = [c for c in calls if c[4]]
    check("a-100-word-move-is-redrawn-with-the-tripwire-line", len(steered) == 1 and "one point" in steered[0][4]
          and "stop where they would answer" in steered[0][4], [c[4] for c in calls])
    check("...the-second-draw-commits-and-the-record-says-why", rows[0]["action"] == "A short line."
          and rows[0]["validation"].get("tripwire") == {"words": 100, "redrawn_words": 3}, rows[0])


def test_the_exchange_shows_the_thread_and_your_own_lines(tmp):
    def script(who, stance, flags, n, steer):
        return ("%s line %d." % (who.title(), n), "-", "yield" if stance == "speaker" else "take", _other(who))
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 3)
    third = calls[2]
    check("the-moment-marks-the-reader's-own-line-and-whom-it-was-to",
          third[0] == "mira" and 'You, to Ada: "Mira line 0."' in third[3]
          and 'Ada, to you: "Ada line 0."' in third[3], third[3][-300:])


def main():
    print("test_scene_rounds.py - the round, through scripts/scene.py main\n")
    for name, fn in sorted(((k, v) for k, v in globals().items() if k.startswith("test_") and callable(v)),
                           key=lambda kv: kv[1].__code__.co_firstlineno):
        print("[%s]" % name)
        fn(tempfile.mkdtemp(prefix="rounds_"))
    print("\n%s" % ("test_scene_rounds: OK" if not FAILS else "FAILED: %d" % len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
