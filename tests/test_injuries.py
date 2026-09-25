"""test_injuries.py — bodily injuries kept as state, told to who saw them, healed over story time (gate injuries).

WHAT THIS PINS (2026-09-22). No act could leave anyone hurt: the event seat was never asked about harm, a
sheet's `current.condition.injuries` was read by nothing, and no actor was told that anyone was hurt. The owner
ruled: "Track injuries as state similar to props but for now I'm not interested in health bars", then "Heal over
time". `injuries` is a NEW system, OFF by default.

  [1] `stage`: each severity reads fresh, then healing, then is gone - a grave one leaves its mark;
  [2] `require`: a sheet's page-one injuries are {what, severity, ago?}, anything else refused by code;
  [3] the reader: its prompt is byte-identical unless asked; asked, each injury names someone present (or the one
      who acted), quotes the act, and carries a severity from the ladder - at most three;
  [4] the words the actor reads: who, the quote and the stage, never a number;
  [5] through scripts/scene.py main with the system on: the reader marks the burn, it rides the event into the
      log, the one hurt and the one who watched are told it, fresh, each beat records what it told; the sheet's
      old injuries reach only their owner; time heals it on the clock; with the system off the reader is never
      asked and nothing is kept or told.

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

from src.engine import clock, injuries, systems                 # noqa: E402
from src.engine.direction import DirectionError, direct_injuries  # noqa: E402
from src.engine.prompt import build_turn_messages              # noqa: E402
from src.engine.records import RecordError                     # noqa: E402
from test_systems import _book, _cfg                           # noqa: E402  (one fixture)

FAILS = []
BURN = "catches her palm on the lamp's hot brass"
ACTS = {"mira": "Mira %s and hisses. \"The wind is backing,\" she says." % BURN,
        "ada": "Ada coils the boat line. \"The tide is turning,\" she says."}
DAY = clock.MINUTES_PER_DAY


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _code(fn):
    try:
        fn()
    except (RecordError, DirectionError) as e:
        return e.code
    return None


def test_stage():
    print("\n[1] stage - healing over story time")
    check("a-minor-hurt-is-fresh-the-first-day", injuries.stage("minor", 0) == "fresh" and injuries.stage("minor", 0.9 * DAY) == "fresh")
    check("...healing-after-it", injuries.stage("minor", 1.5 * DAY) == "healing")
    check("...and-gone-after-three-days", injuries.stage("minor", 3 * DAY) is None)
    check("a-serious-one-heals-over-weeks", injuries.stage("serious", 5 * DAY) == "fresh" and injuries.stage("serious", 10 * DAY) == "healing"
          and injuries.stage("serious", 22 * DAY) is None)
    check("a-grave-one-leaves-its-mark-for-good", injuries.stage("grave", 60 * DAY) == "healing" and injuries.stage("grave", 91 * DAY) == "mark"
          and injuries.stage("grave", float("inf")) == "mark")
    check("an-unknown-severity-is-refused", _code(lambda: injuries.stage("mortal", 0)) == "INJURY_SEVERITY_UNKNOWN")
    check("the-system-is-off-by-default-and-needs-condition", "injuries" not in systems.for_book({})
          and "injuries" in systems.for_book({"systems": {"injuries": True}})
          and _code(lambda: systems.for_book({"systems": {"injuries": True, "condition": False}})) == "SYSTEMS_NEEDS_UNMET")


def _sheet(injs):
    return {"current": {"condition": {"energy": 0.8, "allostatic_load": 0.2, "injuries": injs}}}


def test_require():
    print("\n[2] require - a sheet's page-one injuries")
    ok = [{"what": "an old rope burn", "severity": "grave"}, {"what": "a split lip", "severity": "minor", "ago": "12h"}]
    check("a-well-formed-list-passes", injuries.require(_sheet(ok)) is not None and injuries.require(_sheet([])) is not None)
    check("no-list-at-all-passes", injuries.require({"current": {"condition": {}}}) is not None)
    for code, injs in (("INJURY_SHAPE", "a limp"), ("INJURY_SHAPE", [{"severity": "minor"}]),
                       ("INJURY_SHAPE", [{"what": "a cut", "severity": "minor", "hp": 3}]),
                       ("INJURY_SEVERITY_UNKNOWN", [{"what": "a cut", "severity": "nasty"}]),
                       ("INJURY_AGO_NOT_A_SPAN", [{"what": "a cut", "severity": "minor", "ago": "a while"}])):
        check("refuses-%s-%s" % (code, json.dumps(injs)[:34]), _code(lambda: injuries.require(_sheet(injs))) == code,
              _code(lambda: injuries.require(_sheet(injs))))


def test_reader():
    print("\n[3] the reader")
    import appraiser
    kw = dict(moment="The gale has dropped.", present=["mira", "ada"], actor="Mira", attachments=None)
    plain = appraiser.build_event_messages(ACTS["mira"], **kw)
    check("not-asked-the-prompt-is-byte-identical", plain == appraiser.build_event_messages(ACTS["mira"], injuries=False, **kw)
          and "INJURIES" not in plain[0]["content"])
    check("asked-it-carries-the-question-and-the-ladder", all(s in appraiser.build_event_messages(ACTS["mira"], injuries=True, **kw)[0]["content"]
                                                            for s in ("INJURIES", injuries.rubric())))
    base = {"type": "mundane", "dimensions": {}, "durability": "transient"}

    def parse(t, asked=True):
        return appraiser.parse_event_reply(json.dumps(dict(base, injuries=t)), objects=["ada"], action=ACTS["mira"],
                                           injuries=asked, present=["mira", "ada"], actor="Mira")
    one = {"who": "self", "quote": BURN, "severity": "minor"}
    check("a-marked-injury-rides-the-tags", parse([one])["injuries"] == [one], parse([one]))
    check("the-one-who-acted-named-by-name-is-self", parse([dict(one, who="Mira")])["injuries"][0]["who"] == "self")
    check("someone-present-is-named-by-id", parse([dict(one, who="ada")])["injuries"][0]["who"] == "ada")
    check("none-is-an-empty-list", parse([])["injuries"] == [] and parse(None)["injuries"] == [])
    check("not-asked-a-stray-key-is-dropped", "injuries" not in parse([one], asked=False))
    for code, t in (("APPRAISER_INJURY_SHAPE", "a burn"), ("APPRAISER_INJURY_SHAPE", [one] * 4),
                    ("APPRAISER_INJURY_SHAPE", [dict(one, who="the cook")]), ("APPRAISER_QUOTE_MISSING", [dict(one, quote=" ")]),
                    ("APPRAISER_FACT_NOT_IN_ACTION", [dict(one, quote="breaks her arm")]),
                    ("APPRAISER_INJURY_UNKNOWN", [dict(one, severity="nasty")])):
        check("refuses-%s-%s" % (code, json.dumps(t)[:30]), _code(lambda: parse(t)) == code, _code(lambda: parse(t)))


def test_words():
    print("\n[4] the words the actor reads")
    rows = [{"who": "mira", "what": BURN, "severity": "minor", "stage": "fresh"},
            {"who": "ada", "what": "an old rope burn.", "severity": "grave", "stage": "mark"}]
    line = direct_injuries(rows, "mira", {"ada": "Ada"})
    check("who-the-quote-and-the-stage", line == 'Who is hurt, as you know it: you - "%s" (fresh); Ada - "an old rope burn" '
          '(healed, but it left its mark).' % BURN, line)
    check("no-number-reaches-the-actor", not re.search(r"\d", line))
    check("nothing-hurt-is-silence", direct_injuries([], "mira") == "")
    check("an-unknown-stage-is-refused", _code(lambda: direct_injuries([dict(rows[0], stage="3 days")], "mira")) == "DIRECTION_INJURY_STAGE_UNKNOWN")


def _sheets(book, injs):
    """Write each keeper's page-one injuries, and the `fixed.id` BLUEPRINT-character 1.x REQUIRES - the shared
    fixture leaves it out, and without it no actor can be told a hurt is its own ("you")."""
    for name in ("Mira", "Ada"):
        p = os.path.join(book, "characters", "%s.md" % name)
        txt = open(p, encoding="utf-8").read()
        m = re.search(r"```json\n(.*)\n```", txt, re.S)
        eng = json.loads(m.group(1))
        eng["fixed"]["id"] = name.lower()
        eng["current"]["condition"]["injuries"] = injs.get(name, [])
        open(p, "w", encoding="utf-8").write(txt[:m.start(1)] + json.dumps(eng, indent=1) + txt[m.end(1):])


ADA_SHEET = [{"what": "an old rope burn across the palm", "severity": "grave"},
             {"what": "a split lip from the gale", "severity": "minor", "ago": "2d"}]


def _run(tmp, decl, ada=None):
    """One scene of four beats through scripts/scene.py main IN PROCESS: Mira burns her palm on her first act, the
    event seat (faked) marks it when asked. -> (db, [(speaker, volatile injuries or None, the rendered prompt)], [asked?])."""
    import scene
    book = _book(tmp, decl)
    _sheets(book, {"Ada": ADA_SHEET if ada is None else ada})
    seen, asked, marked = [], [], []

    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        me = "mira" if other == "ada" else "ada"
        text = "\n".join(m["content"] for m in build_turn_messages(packet, event_text, temperament, {}))
        seen.append((me, packet["volatile"].get("injuries"), text))
        return ({"action": ACTS[me], "thought": "", "exit": False, "addressee": other, "act": "",
                 "tags": {"type": "mundane", "summary": "tends the lamp", "dimensions": {}, "durability": "transient",
                          "subject": other}}, [])

    def event(action, model, injuries=False, **_k):
        asked.append(bool(injuries))
        out = {"type": "mundane", "dimensions": {}, "durability": "transient"}
        if injuries:
            out["injuries"] = [{"who": "self", "quote": BURN, "severity": "minor"}] if (BURN in action and not marked) else []
            marked.extend(out["injuries"])
        return out

    def emotion(action, thought, model, me=None, present=(), **_k):
        return [], [p for p in present if p != me], "sure", []

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, event, emotion
    sys.argv = ["scene.py", "--book", book, "--scene", _cfg(tmp, "gale", "21:00", "1h"), "--budget", "4",
                "--model", "fake/model", "--no-keeper"]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            scene.main()
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv = saved
    return glob.glob(os.path.join(book, "runs", "*.db"))[0], seen, asked


def _ada(book):
    from src.engine import vault
    return vault.load_book(book)[1]["ada"]


def test_through_the_driver(tmp):
    print("\n[5] through scripts/scene.py main")
    db, seen, asked = _run(os.path.join(tmp, "on"), {"injuries": True})
    check("both-keepers-spoke", {w for w, _i, _t in seen} == {"mira", "ada"}, [w for w, _i, _t in seen])
    check("the-reader-was-asked-every-beat", asked and all(asked), asked)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    hurt_turns = [r["turn"] for r in con.execute("SELECT turn, payload FROM events") if json.loads(r["payload"] or "{}").get("injuries")]
    check("the-burn-rides-its-event-into-the-log-once", len(hurt_turns) == 1, hurt_turns)
    after = [(w, i, t) for w, i, t in seen if i is not None and any(r["what"] == BURN for r in i)]
    check("the-one-hurt-is-told-it-fresh", any(w == "mira" and 'you - "%s" (fresh)' % BURN in t for w, _i, t in after),
          [t[-400:] for w, _i, t in after if w == "mira"][-1:])
    check("...and-the-one-who-watched", any(w == "ada" and '"%s" (fresh)' % BURN in t and 'you - "%s"' % BURN not in t
                                            for w, _i, t in after), [t[-400:] for w, _i, t in after if w == "ada"][-1:])
    ada_own = [i for w, i, _t in seen if w == "ada"]
    check("the-sheet-s-old-injuries-reach-their-owner", ada_own and all(
        {("an old rope burn across the palm", "mark"), ("a split lip from the gale", "healing")} <= {(r["what"], r["stage"]) for r in i}
        for i in ada_own), ada_own[:1])
    check("...and-no-one-else", not any("rope burn" in r["what"] or "split lip" in r["what"]
                                        for w, i, _t in seen if w == "mira" for r in (i or [])))
    mans = {r["turn"]: json.loads(r["manifest"]) for r in con.execute("SELECT turn, manifest FROM decision_manifests")}
    check("each-beat-records-who-it-told-was-hurt", all("injuries" in m for m in mans.values())
          and any("mira:fresh" in m["injuries"] for m in mans.values()), list(mans.values())[-1].get("injuries"))
    run_id = con.execute("SELECT run_id FROM runs").fetchone()[0]
    first = con.execute("SELECT MIN(turn) FROM turns").fetchone()[0]
    opened = clock.last_scene_clock(con, run_id, first + 1)["at"]
    check("a-beat-s-time-is-its-scene-s-opening-plus-its-beats", clock.at_turn(con, run_id, first + 2)
          == opened + 2 * 15.0, (clock.at_turn(con, run_id, first + 2), opened))
    head = con.execute("SELECT MAX(turn) FROM turns").fetchone()[0] + 1
    check("someone-who-was-never-there-is-told-nothing", injuries.for_actor(con, run_id, "gull", {}, head) == [])
    burn_at = clock.at_turn(con, run_id, hurt_turns[0])
    ada = _ada(os.path.dirname(os.path.dirname(db)))
    for days, want, lip in ((1.5, "healing", None), (4.0, None, None)):   # a later scene, days on - the clock heals
        con.execute("INSERT INTO scene_clock (run_id, turn, at_minutes, lasts_minutes, beat_minutes) VALUES (?,?,?,?,?)",
                    (run_id, head, burn_at + days * DAY, None, 0.0))
        rows = injuries.for_actor(con, run_id, "ada", ada, head)
        check("%s-days-on-the-burn-reads-%s" % (days, want or "healed"),
              [r["stage"] for r in rows if r["what"] == BURN] == ([want] if want else []), rows)
        check("...and-the-sheet-s-split-lip-heals-on-the-same-clock",
              [r["stage"] for r in rows if "split lip" in r["what"]] == ([lip] if lip else []), rows)
        head += 1
    try:
        _run(os.path.join(tmp, "bad"), {"injuries": True}, ada=[{"what": "a cut", "severity": "nasty"}])
        check("a-sheet-injury-the-system-cannot-read-is-refused-before-the-first-beat", False, "the scene ran")
    except SystemExit as e:
        check("a-sheet-injury-the-system-cannot-read-is-refused-before-the-first-beat", "INJURY_SEVERITY_UNKNOWN" in str(e), str(e))
    import lint_book
    from src.engine import vault
    book = os.path.join(tmp, "bad", "The Rock and the Rose")
    rep = lint_book.lint(*vault.load_book(book)[:2])
    check("...and-named-by-the-pre-run-check", any("injuries system" in e and "ada" in e.lower() for e in rep["errors"]), rep["errors"])
    db, seen, asked = _run(os.path.join(tmp, "off"), None)
    check("with-it-off-the-reader-is-never-asked", asked and not any(asked), asked)
    con = sqlite3.connect(db)
    check("...nothing-is-kept", not any("injuries" in json.loads(p or "{}") for (p,) in con.execute("SELECT payload FROM events")))
    check("...and-nothing-is-told-or-recorded", all(i is None and "Who is hurt" not in t for _w, i, t in seen)
          and not any("injuries" in json.loads(m) for (m,) in con.execute("SELECT manifest FROM decision_manifests")))


ALL = {"condition_flow": True, "body": True, "injuries": True}
HURT = "the keel crushes her hand against the ways"
HAULS = {"mira": 'Mira hauls the skiff up the shingle and %s. "Take the bow," she says.' % HURT,
         "ada": 'Ada hauls the skiff up the shingle. "Mind the keel," she says.'}


def _hauling(tmp, decl, severity):
    """Two scenes (the second a --resume) through scripts/scene.py main IN PROCESS: both keepers haul every beat (the
    reader says `hard` when asked), and the reader marks Mira's crushed hand once, at her first beat, with `severity`
    (None: no injury). -> (db, run_id, output)."""
    import scene
    from test_body import _cfg as _tide, _with_strength
    book = _book(tmp, decl)
    _sheets(book, {})
    _with_strength(book, {"Mira": "strong", "Ada": "strong"})
    marked, outs = [], []

    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        me = "mira" if other == "ada" else "ada"
        return ({"action": HAULS[me], "thought": "", "exit": False, "addressee": other, "act": "",
                 "tags": {"type": "mundane", "summary": "hauls the skiff", "dimensions": {}, "durability": "transient",
                          "subject": other}}, [])

    def event(action, model, actor="", exertion=False, injuries=False, **_k):
        out = {"type": "mundane", "dimensions": {}, "durability": "transient"}
        if exertion:
            out["exertion"] = "hard"
        if injuries:
            hurt = severity and actor == "Mira" and not marked
            out["injuries"] = [{"who": "self", "quote": HURT, "severity": severity}] if hurt else []
            marked.extend(out["injuries"])
        return out

    def emotion(action, thought, model, me=None, present=(), **_k):
        return [], [p for p in present if p != me], "sure", []

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, event, emotion
    try:
        for i, (name, day, time, lasts, budget) in enumerate((("tide-1", 1, "06:00", "1h", 6), ("tide-2", 1, "09:00", "40m", 4))):
            argv = ["scene.py", "--book", book, "--scene", _tide(tmp, name, day, time, lasts), "--budget", str(budget),
                    "--model", "fake/model", "--no-keeper"]
            if i:
                argv += ["--resume", sqlite3.connect(glob.glob(os.path.join(book, "runs", "*.db"))[0]).execute(
                    "SELECT run_id FROM runs").fetchone()[0]]
            sys.argv = argv
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                scene.main()
            outs.append(out.getvalue())
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv = saved
    db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
    return db, sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0], outs


def _mira(db):
    return json.loads(sqlite3.connect(db).execute(
        "SELECT condition FROM current_state WHERE char_id = 'mira' ORDER BY turn DESC LIMIT 1").fetchone()[0])


def test_weakens(tmp):
    print("\n[6] a hurt weakens the body while it heals (gate injury-weakens; the book runs body AND injuries)")
    from src.engine import body, bible, mood_fold
    ch = {"baseline": {"body": {"strength": "strong"}}}
    check("strength-steps-down-a-word-at-a-time-and-never-below-the-lowest",
          [body.capacity(ch, w) for w in (0, 1, 2, 9)] == [1.3, 1.0, 0.75, 0.5], [body.capacity(ch, w) for w in (0, 1, 2, 9)])
    check("every-severity-says-how-far-it-weakens", set(injuries.WEAKENS) == set(injuries.SEVERITY))
    runs = {sev: _hauling(os.path.join(tmp, sev or "none"), ALL if sev else {"condition_flow": True, "body": True}, sev)
            for sev in (None, "minor", "serious", "grave")}
    e = {sev: _mira(db)["energy"] for sev, (db, _r, _o) in runs.items()}
    check("a-minor-hurt-costs-nothing-more", abs(e["minor"] - e[None]) < 1e-12, e)
    check("a-serious-one-costs-more-and-a-grave-one-more-still", e["grave"] < e["serious"] < e["minor"], e)
    db, run_id, _o = runs["grave"]
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
    check("the-replay-weakens-exactly-as-the-driver-did-across-both-scenes-and-the-gap",
          d["condition_at"] is None and d["at"] is None and not d["notes"], d)
    head = con.execute("SELECT MAX(turn) FROM turns").fetchone()[0] + 1
    hurt_at = clock.at_turn(con, run_id, [r["turn"] for r in injuries.run_rows(con, run_id)][0])
    for days, want in ((10.0, 2), (100.0, 0)):              # still healing, then healed - its mark weakens nothing
        con.execute("INSERT INTO scene_clock (run_id, turn, at_minutes, lasts_minutes, beat_minutes) VALUES (?,?,?,?,?)",
                    (run_id, head, hurt_at + days * DAY, None, 0.0))
        got = injuries.weakening(con, run_id, "mira", {}, head)
        check("%s-days-on-the-crushed-hand-weakens-by-%d" % (days, want), got == want, got)
        head += 1
    rib = {"current": {"condition": {"injuries": [{"what": "a cracked rib", "severity": "serious", "ago": "2d"}]}}}
    check("a-sheet-s-own-unhealed-injury-weakens-too", injuries.weakening(con, run_id, "ada", rib, 1) == 1)
    check("...and-someone-else-s-never-does", injuries.weakening(con, run_id, "ada", {}, 1) == 0)
    import copy
    from src.engine import condition, passage
    from test_vault import CHAR_ENGINE             # a whole sheet: an opening with a presence ages the mood and the
    base = copy.deepcopy(CHAR_ENGINE)              # slow tiers too (gate own-timelines), not the condition alone
    base["current"]["condition"] = condition.split({"energy": 0.9, "allostatic_load": 0.1})
    base["baseline"]["body"] = {"strength": "strong"}
    gap = {}
    for w in (None, {"mira": 2}):                  # two waking hours between scenes, weighed whole and a grave hurt down
        chs = {"mira": copy.deepcopy(base)}
        passage.apply_opening(chs, lambda i: [], 540.0, {"mira": {"end": 420.0, "owed": 0.0}}, flow=True, body=True,
                              weakened=w)
        gap[bool(w)] = chs["mira"]["current"]["condition"]["energy"]
    want = condition.TIME_SPEND * 120 * (1 / 0.75 - 1 / 1.3)
    check("the-gap-between-scenes-costs-the-weakened-body-the-priced-amount", abs((gap[False] - gap[True]) - want) < 1e-12,
          (gap, want))


def _chair(tmp, injs):
    """One chair turn through scripts/direct.py main's REPL at ten minutes, Mira strong and hauling (`hard`), her
    sheet carrying `injs` -> her condition after it."""
    import direct
    from test_body import ACTION, _with_strength
    book = _book(tmp, ALL)
    _sheets(book, {"Mira": injs})
    _with_strength(book, {"Mira": "strong", "Ada": "ordinary"})

    def actor(*_a, **_k):
        return {"action": ACTION, "thought": "", "exit": False, "addressee": "ada", "act": "",
                "tags": {"type": "mundane", "summary": "hauls", "dimensions": {}, "durability": "transient", "subject": "ada"}}, []

    def event(action, model, exertion=False, injuries=False, **_k):
        return dict({"type": "mundane", "dimensions": {}, "durability": "transient"}, **({"exertion": "hard"} if exertion else {}))

    def emotion(*_a, **_k):
        return [], ["ada"], "sure", []

    saved = (direct.faithful_turn, direct.appraiser.read_event, direct.appraiser.read_emotion, sys.argv, sys.stdin)
    direct.faithful_turn, direct.appraiser.read_event, direct.appraiser.read_emotion = actor, event, emotion
    sys.stdin = io.StringIO("by:ada Ada comes down to the slip\nquit\n")
    sys.argv = ["direct.py", "--book", book, "--char", "Mira", "--model", "fake/model", "--no-keeper", "--minutes-per-turn", "10"]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            direct.main()
    finally:
        direct.faithful_turn, direct.appraiser.read_event, direct.appraiser.read_emotion, sys.argv, sys.stdin = saved
    return _mira(glob.glob(os.path.join(book, "runs", "*.db"))[0])


def test_the_chair_weakens(tmp):
    print("\n[7] the chair: a hurt on the sheet weakens the body its turn is weighed against")
    whole = _chair(os.path.join(tmp, "whole"), [])
    hurt = _chair(os.path.join(tmp, "hurt"), [{"what": "a cracked rib", "severity": "serious", "ago": "1d"}])
    want = 0.125 * (1 / 1.0 - 1 / 1.3)       # ten minutes of waking and hauling (0.125 of energy for an ordinary body),
    got = whole["energy"] - hurt["energy"]    # weighed as ordinary (strong, a word down) instead of strong
    check("the-serious-rib-prices-her-turn-as-an-ordinary-body-s", abs(got - want) < 1e-9, (got, want))


def main():
    print("test_injuries.py — hurts kept as state, told to who saw them, healed over time\n")
    tmp = tempfile.mkdtemp(prefix="swe_injuries_")
    try:
        test_stage()
        test_require()
        test_reader()
        test_words()
        test_through_the_driver(tmp)
        test_weakens(os.path.join(tmp, "weak"))
        test_the_chair_weakens(os.path.join(tmp, "chair"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_injuries: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  " + f)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
