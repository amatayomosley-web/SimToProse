"""test_body.py — a strength each character carries, and what each act costs the body (src/engine/body.py).

WHAT THIS PINS (gate body-exertion, 2026-09-22). The owner: "Not every event requires the same energy from
each person ... this requires a strength stat for each character." The event reader names how physically
demanding an act was, in a word, the same for anyone; the engine weighs it against the actor's strength.
`body` is a NEW system, OFF by default, and needs `condition_flow`:

  [1] the arithmetic: each exertion word is priced from minutes-to-exhaustion; an hour of `hard` work takes an
      ordinary body from fresh to the edge of the lowest band; strength divides the cost; refusals by code;
  [2] the registry: off by default; cannot run without the flow (which cannot run without condition);
  [3] the event reader: its prompt is byte-identical unless the book runs the body; asked, it must name a
      word from the ladder and quote the action for it; a stray key it was not asked for is dropped;
  [4] a seated two-scene run with the body ON through scripts/scene.py main: the reader is asked every beat,
      its word rides the turn's tags into the log, a frail body pays more than a powerful one for the same
      acts, and the replay re-derives every cached condition; a sheet with no strength is refused first;
  [5] the chair: the same act costs its body; an actor's own stray `exertion` never reaches the log;
  [6] the pre-run check.

The book is invented here (two keepers on a rock), per hard rule 1. Script-style; exit 0 = all pass.
"""
import contextlib
import glob
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import bible, body, condition, mood_fold, rungs, systems   # noqa: E402
from src.engine.records import Reading, RecordError                         # noqa: E402
from test_systems import _book                                              # noqa: E402  (one fixture, four suites)

FAILS = []
BODY = {"condition_flow": True, "body": True}
FLOW = {"condition_flow": True}
ACTION = 'Mira hauls the skiff up the shingle, both hands on the gunwale. "Take the bow," she says.'


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


def _sheet(strength):
    return {"baseline": {"body": {"strength": strength}}}


def test_arithmetic():
    print("\n[1] the arithmetic")
    check("strength-words-order-the-capacity", [body.capacity(_sheet(w)) for w in ("frail", "slight", "ordinary", "strong", "powerful")]
          == sorted(body.STRENGTH_WORDS.values()))
    fresh = {"energy": 1.0, "allostatic_load": 0.2}
    hour = body.exert(condition.spend(fresh, 60.0, 0.0, {}), "hard", 60.0, body.capacity(_sheet("ordinary")))
    check("an-hour-of-HARD-work-takes-an-ordinary-body-from-fresh-to-spent", abs(hour["energy"] - 0.25) < 1e-12, hour)
    check("...and-the-load-is-not-effort-s", hour["allostatic_load"] == 0.2, hour)
    ten = body.exert(condition.spend(fresh, 10.0, 0.0, {}), "extreme", 10.0, 1.0)
    check("ten-minutes-all-out-does-the-same", abs(ten["energy"] - 0.25) < 1e-12, ten)
    frail = 1.0 - body.exert(fresh, "hard", 5.0, body.capacity(_sheet("frail")))["energy"]
    strong = 1.0 - body.exert(fresh, "hard", 5.0, body.capacity(_sheet("powerful")))["energy"]
    check("a-frail-body-pays-more-than-a-powerful-one-for-the-same-act", abs(frail / strong - 1.6 / 0.5) < 1e-9, (frail, strong))
    check("none-and-an-unasked-word-cost-nothing", body.exert(fresh, "none", 30.0, 1.0) == fresh == body.exert(fresh, None, 30.0, 1.0))
    check("an-act-costs-at-least-a-minute", body.exert(fresh, "hard", 0.0, 1.0) == body.exert(fresh, "hard", body.ACT_MINUTES, 1.0))
    check("strength-also-weighs-the-waking-minutes",
          abs((1 - condition.spend(fresh, 60.0, scale=2.0)["energy"]) - 2 * (1 - condition.spend(fresh, 60.0)["energy"])) < 1e-12)
    from src.engine import passage
    from test_vault import CHAR_ENGINE
    import copy

    def owed(on):
        ch = copy.deepcopy(CHAR_ENGINE)
        ch["baseline"]["body"], ch["current"]["condition"] = {"strength": "frail"}, dict(fresh)
        chars = {"mira": ch}
        # her own gap (gate gap-day-and-night): her last scene ended at noon with 30 minutes it never spent; this
        # opening is at that same noon, so only the owed minutes - awake time - move her
        passage.apply_opening(chars, lambda i: [], 720.0, {"mira": {"end": 720.0, "owed": 30.0}}, flow=True, body=on)
        return 1.0 - chars["mira"]["current"]["condition"]["energy"]
    check("an-opening-weighs-the-owed-minutes-against-strength-too",
          owed(False) > 0 and abs(owed(True) - 2 * owed(False)) < 1e-12, (owed(True), owed(False)))
    for code, fn in (("BODY_STRENGTH_MISSING", lambda: body.capacity({"baseline": {}})),
                     ("BODY_STRENGTH_UNKNOWN", lambda: body.capacity(_sheet("mighty"))),
                     ("BODY_EXERTION_UNKNOWN", lambda: body.exert(fresh, "strenuous", 1.0, 1.0))):
        check("refuses-%s" % code, _code(fn) == code, _code(fn))


def test_registry():
    print("\n[2] the registry")
    check("the-body-is-off-by-default", "body" not in systems.for_book({}))
    check("it-cannot-run-without-the-flow", _code(lambda: systems.for_book({"systems": {"body": True}})) == "SYSTEMS_NEEDS_UNMET")
    check("...and-with-it-it-runs", {"body", "condition_flow"} <= systems.for_book({"systems": BODY}))


def test_the_reader():
    print("\n[3] the event reader - asked only when the book runs the body")
    import appraiser
    kw = dict(moment="The gale has dropped.", present=["mira", "ada"], actor="Mira", attachments=None)
    plain, asked = appraiser.build_event_messages(ACTION, **kw), appraiser.build_event_messages(ACTION, exertion=True, **kw)
    check("not-asked-the-prompt-is-byte-identical", plain == appraiser.build_event_messages(ACTION, exertion=False, **kw))
    check("...and-says-nothing-of-exertion", "exertion" not in plain[0]["content"].lower(), plain[0]["content"][-200:])
    check("asked-it-shows-the-engine-s-own-ladder", body.rubric() in asked[0]["content"] and asked[1] == plain[1])
    base = {"type": "mundane", "dimensions": {}, "durability": "transient"}

    def parse(ex, asked=True, drop=False):
        reply = dict(base) if drop else dict(base, exertion=ex)
        return appraiser.parse_event_reply(json.dumps(reply), objects=["ada"], action=ACTION, exertion=asked)
    check("a-word-and-its-quote-ride-the-tags", parse({"word": "Hard", "quote": "hauls the skiff up the shingle"})["exertion"] == "hard")
    check("omitted-is-none", parse(None, drop=True)["exertion"] == "none")
    check("none-needs-no-quote", parse({"word": "none"})["exertion"] == "none")
    check("not-asked-a-stray-key-is-dropped", "exertion" not in parse({"word": "hard", "quote": "hauls"}, asked=False))
    for code, ex in (("APPRAISER_EXERTION_UNKNOWN", {"word": "strenuous", "quote": "hauls"}),
                     ("APPRAISER_QUOTE_MISSING", {"word": "hard"}),
                     ("APPRAISER_QUOTE_MISSING", "hard"),
                     ("APPRAISER_FACT_NOT_IN_ACTION", {"word": "hard", "quote": "rows across the bay"})):
        check("refuses-%s-%s" % (code, json.dumps(ex)), _code(lambda: parse(ex)) == code, _code(lambda: parse(ex)))


# ---------------------------------------------------------------------------------------------------
def _with_strength(book, strengths):
    """Write `baseline.body.strength` into the invented sheets."""
    for name, word in strengths.items():
        p = os.path.join(book, "characters", "%s.md" % name)
        txt = open(p, encoding="utf-8").read()
        m = re.search(r"```json\n(.*)\n```", txt, re.S)
        eng = json.loads(m.group(1))
        eng["baseline"]["body"] = {"strength": word}
        open(p, "w", encoding="utf-8").write(txt[:m.start(1)] + json.dumps(eng, indent=1) + txt[m.end(1):])


def _cfg(tmp, name, day, time, lasts):
    path = os.path.join(tmp, name + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"name": name, "at": {"day": day, "time": time}, "lasts": lasts,
                   "situation": "The two keepers bring the boat up before the tide turns.",
                   "cast": [{"id": "mira", "drive": "get the boat up"}, {"id": "ada", "drive": "get the boat up"}]}, fh)
    return path


def _run(tmp, decl, strengths=None, refuse=False, stray=None):
    """Two scenes (the second a --resume) through scripts/scene.py main IN PROCESS: the actor hauls every beat,
    the EVENT seat answers (faked) with `hard` when it is asked and records whether it was, the emotion seat
    reads the other keeper. -> (db, run_id, [asked?], output)."""
    import scene
    book = _book(tmp, decl)
    if strengths:
        _with_strength(book, strengths)
    asked, outs = [], []

    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        mine = {"type": "mundane", "summary": "hauls the skiff", "dimensions": {}, "durability": "transient", "subject": other}
        if stray:                                   # an exertion word in the ACTOR's own tags - never the reader's
            mine["exertion"] = stray
        return ({"action": ACTION, "thought": "", "exit": False, "addressee": other, "act": "", "tags": mine}, [])

    def event(action, model, present=(), exertion=False, **_k):
        asked.append(bool(exertion))
        if refuse:
            raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked to refuse")
        other = next((p for p in present if p != "mira"), "mira") if "Mira" in action else "ada"
        tags = {"type": "mundane", "dimensions": {"mastery": 0.3}, "durability": "transient", "object": other}
        return dict(tags, exertion="hard") if exertion else tags

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=(), **_k):
        other = next(p for p in present if p != me)
        return [Reading(path="GOODWILL", rung=rungs.rung_at("GOODWILL", 0.5)[1], about=other, confidence="likely")], [other], "sure", []

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, event, emotion
    try:
        for i, (name, day, time, lasts, budget) in enumerate((("tide-1", 1, "06:00", "1h", 6), ("tide-2", 1, "09:00", "40m", 4))):
            argv = ["scene.py", "--book", book, "--scene", _cfg(tmp, name, day, time, lasts), "--budget", str(budget),
                    "--model", "fake/model", "--no-keeper"]
            if i:
                found = glob.glob(os.path.join(book, "runs", "*.db"))
                if not found:               # the first scene was refused before its chronicle was opened
                    break                   # (gate run-start-refusal): there is nothing to resume
                argv += ["--resume", sqlite3.connect(found[0]).execute("SELECT run_id FROM runs").fetchone()[0]]
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
        return None, None, asked, outs
    run = sqlite3.connect(dbs[0]).execute("SELECT run_id FROM runs").fetchone()
    return dbs[0], (run[0] if run else None), asked, outs


def _last(db, cid):
    return json.loads(sqlite3.connect(db).execute(
        "SELECT condition FROM current_state WHERE char_id = ? ORDER BY turn DESC LIMIT 1", (cid,)).fetchone()[0])


def test_a_seated_run(tmp):
    print("\n[4] the body ON through scripts/scene.py main")
    strengths = {"Mira": "powerful", "Ada": "frail"}
    db, run_id, asked, outs = _run(os.path.join(tmp, "body"), BODY, strengths)
    ref, _r2, asked_ref, _o = _run(os.path.join(tmp, "flow"), FLOW, strengths)
    check("both-runs-ran", db and ref and sqlite3.connect(db).execute("SELECT COUNT(*) FROM turns").fetchone()[0] == 10, outs[-1][-300:])
    check("the-reader-was-asked-every-beat-with-the-body-on", asked and all(asked) and len(asked) == 10, asked)
    check("...and-never-with-it-off", asked_ref and not any(asked_ref), asked_ref)
    tags = [json.loads(t) for (t,) in sqlite3.connect(db).execute("SELECT tags FROM turns ORDER BY turn")]
    check("the-reader-s-word-rides-the-turn-into-the-log", all(t.get("exertion") == "hard" for t in tags), tags[:1])
    check("...and-no-word-is-logged-with-the-body-off",
          not any("exertion" in json.loads(t) for (t,) in sqlite3.connect(ref).execute("SELECT tags FROM turns")))
    cost = {c: _last(ref, c)["energy"] - _last(db, c)["energy"] for c in ("mira", "ada")}
    check("the-same-hauling-costs-the-frail-keeper-more", cost["ada"] > cost["mira"] > 0, cost)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
    check("the-replay-re-derives-every-cached-condition-from-the-logged-word",
          d["condition_at"] is None and d["at"] is None and not d["notes"], d)
    db3, _r3, asked3, outs3 = _run(os.path.join(tmp, "nostrength"), BODY, {"Mira": "strong"})
    turns = sqlite3.connect(db3).execute("SELECT COUNT(*) FROM turns").fetchone()[0] if db3 else 0
    check("a-sheet-with-no-strength-is-refused-before-any-beat", "BODY_STRENGTH_MISSING" in outs3[0] and turns == 0 and not asked3,
          (turns, outs3[0][-300:]))
    db4, run4, _a4, _o4 = _run(os.path.join(tmp, "stray"), BODY, strengths, refuse=True, stray="extreme")
    logged = [json.loads(t) for (t,) in sqlite3.connect(db4).execute("SELECT tags FROM turns")]
    check("the-seat-refused-an-actor-s-own-exertion-never-reaches-the-log", logged and not any("exertion" in t for t in logged),
          logged[:1])


def _chair(tmp, decl, seat_answers, stray=None, strength="frail"):
    """One seated chair beat through scripts/direct.py main's REPL, IN PROCESS, at 10 minutes a turn -> the db.
    The actor is faked at `faithful_turn`; `seat_answers` False makes the event seat refuse; `stray` puts an
    exertion word in the ACTOR's own tags. (The REPL, not --turn-json: the one-shot seam does not pass
    --minutes-per-turn to the turn at all - a pre-existing asymmetry, flagged to the owner, not changed here.)"""
    import direct
    book = _book(tmp, decl)
    if strength:
        _with_strength(book, {"Mira": strength, "Ada": "ordinary"})
    tags = {"type": "mundane", "summary": "hauls the skiff", "dimensions": {}, "durability": "transient", "subject": "ada"}
    if stray:
        tags["exertion"] = stray
    said = io.StringIO("by:ada Ada comes down to the slip; the tide is turning\nquit\n")   # the REPL reads sys.stdin

    def actor(*_a, **_k):
        return {"action": ACTION, "thought": "", "exit": False, "addressee": "ada", "act": "", "tags": dict(tags)}, []

    def event(action, model, exertion=False, **_k):
        if not seat_answers:
            raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked to refuse")
        t = {"type": "mundane", "dimensions": {"mastery": 0.3}, "durability": "transient", "object": "ada"}
        return dict(t, exertion="hard") if exertion else t

    def emotion(*_a, **_k):
        return [Reading(path="GOODWILL", rung=rungs.rung_at("GOODWILL", 0.5)[1], about="ada", confidence="likely")], ["ada"], "sure", []

    saved = (direct.faithful_turn, direct.appraiser.read_event, direct.appraiser.read_emotion, sys.argv, sys.stdin)
    direct.faithful_turn, direct.appraiser.read_event, direct.appraiser.read_emotion, sys.stdin = actor, event, emotion, said
    sys.argv = ["direct.py", "--book", book, "--char", "Mira", "--model", "fake/model", "--no-keeper", "--minutes-per-turn", "10"]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            direct.main()
    finally:
        direct.faithful_turn, direct.appraiser.read_event, direct.appraiser.read_emotion, sys.argv, sys.stdin = saved
    return glob.glob(os.path.join(book, "runs", "*.db"))[0]


def test_the_chair(tmp):
    print("\n[5] the chair")
    on = _chair(os.path.join(tmp, "on"), BODY, True)                 # mira is FRAIL: capacity 0.5
    off = _chair(os.path.join(tmp, "off"), FLOW, True)
    e_on, e_off = _last(on, "mira")["energy"], _last(off, "mira")["energy"]
    waking = condition.TIME_SPEND * 10.0 * (1 / 0.5 - 1)               # her ten waking minutes, weighed
    act = (0.75 / 60.0 - condition.TIME_SPEND) * 10.0 / 0.5            # ten minutes' hauling, weighed
    check("the-chair-s-hauling-costs-a-frail-body-the-priced-amount", abs((e_off - e_on) - (waking + act)) < 1e-9,
          (e_off, e_on, waking + act))
    stray = _chair(os.path.join(tmp, "stray"), BODY, False, stray="extreme")
    t = json.loads(sqlite3.connect(stray).execute("SELECT tags FROM turns").fetchone()[0])
    check("an-actor-s-own-exertion-never-reaches-the-log", "exertion" not in t, t)
    check("...and-costs-only-her-weighed-waking-minutes", abs((e_off - _last(stray, "mira")["energy"]) - waking) < 1e-12,
          (_last(stray, "mira"), e_off, waking))
    try:
        none = _chair(os.path.join(tmp, "nostrength"), BODY, True, strength=None)
        refused, n = "", sqlite3.connect(none).execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    except SystemExit as e:
        refused, n = str(e), 0
    check("the-chair-refuses-a-sheet-with-no-strength-before-its-turn", "BODY_STRENGTH_MISSING" in refused and n == 0, (refused, n))


def test_lint():
    print("\n[6] the pre-run check")
    import lint_book
    world = json.load(open(os.path.join(REPO, "world", "ashford-slice.json"), encoding="utf-8"))
    maren = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    got = lint_book.lint(dict(world, systems=BODY), {"maren": maren})
    check("body-on-a-sheet-with-no-strength-is-an-ERROR", any("BODY_STRENGTH_MISSING" in e for e in got["errors"]), got["errors"])
    strong = dict(maren, baseline=dict(maren["baseline"], body={"strength": "mighty"}))
    got = lint_book.lint(dict(world, systems=BODY), {"maren": strong})
    check("...and-an-unpriced-word-too", any("BODY_STRENGTH_UNKNOWN" in e for e in got["errors"]), got["errors"])
    good = dict(maren, baseline=dict(maren["baseline"], body={"strength": "strong"}))
    got = lint_book.lint(dict(world, systems=BODY), {"maren": good})
    check("...and-a-priced-one-passes", not any("body" in e for e in got["errors"]), got["errors"])
    got = lint_book.lint(world, {"maren": good})
    check("body-off-an-authored-strength-WARNS", any("a body block is authored" in w for w in got["warnings"]),
          [w for w in got["warnings"] if "system" in w])


def main():
    print("test_body.py — a strength each character carries, and what each act costs the body\n")
    tmp = tempfile.mkdtemp(prefix="swe_body_")
    try:
        test_arithmetic()
        test_registry()
        test_the_reader()
        test_a_seated_run(os.path.join(tmp, "seated"))
        test_the_chair(os.path.join(tmp, "chair"))
        test_lint()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_body: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
