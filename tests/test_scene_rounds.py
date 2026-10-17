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


def _book(tmp, who, to=None, scene=None):
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
        json.dump(dict({"name": "gale", "at": {"day": 1, "time": "21:00"}, "lasts": "1h",
                   "situation": "The keepers wait out the gale in the lamp room.",
                   "cast": [dict({"id": i, "drive": d}, **({"to": (to or {})[i]} if i in (to or {}) else {}))
                            for _n, i, d in cast]}, **(scene or {})), fh)
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


THOUGHTS = []      # (who, the last_thought this call was given) - gate thought-unsteered
KEPT = []          # (who, the id of the composer keep the driver handed this call) - gate composer-reuse


def _actor(script, calls):
    """The actor, scripted: `script(who, stance, flags, n)` -> (action, thought, floor, addressee) for this person's
    n-th call; every call is recorded as (who, stance, flags, event_text, steer)."""
    seen = {}

    def fake(packet, event_text, temperament, model, stub, **kw):
        who = kw["char_id"]
        floor = dict(kw.get("floor") or {})
        stance = floor.pop("stance", None)
        THOUGHTS.append((who, floor.pop("last_thought", None)))
        n = seen[who] = seen.get(who, -1) + 1
        KEPT.append((who, id(kw.get("kept")) if isinstance(kw.get("kept"), dict) else None))
        calls.append((who, stance, floor, event_text, kw.get("steer")))
        action, thought, word, to = script(who, stance, floor, n, kw.get("steer"))
        return ({"action": action, "thought": thought, "exit": False, "addressee": to, "act": "", "floor": word,
                 "tags": {"type": "mundane", "summary": action or "-", "dimensions": {}, "durability": "transient",
                          "subject": to}}, [])
    return fake


def _run(tmp, who, script, budget, stub=True, to=None, extra=(), keys=None):
    import scene
    book, cfg = _book(tmp, who, to, keys)
    calls, saved = [], scene.faithful_turn
    scene.faithful_turn = _actor(script, calls)
    try:
        if stub:
            out, exited = _drive("scene", book, ["--scene", cfg, "--stub"] + ([] if budget is None else ["--budget", str(budget)])
                                 + list(extra))
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
    speaker's; the speaker is re-called with `resumed`; after the yield and the listener's hold, the speaker is offered
    the silence with the unanswered line (gate forced-ask-order, critique E5: not the listener who just held), holds,
    and the scene has settled."""
    def script(who, stance, flags, n, steer):
        if who == "mira" and stance == "listener":
            return ("", "", "hold", "")
        if who == "mira":
            return ("Mira's paragraph %d." % n, "-", ("keep", "keep", "yield")[min(n, 2)], "ada")
        return ("", "", "hold", "")
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 10)
    check("keep-keep-yield:-three-rows-by-the-speaker", [(r["actor"], r["floor"]) for r in rows]
          == [("mira", "keep"), ("mira", "keep"), ("mira", "yield")], ([(r["actor"], r["floor"]) for r in rows], out[-600:]))
    mira = [c for c in calls if c[0] == "mira"]
    check("...re-called-to-go-on-from-where-they-stopped", [c[2] for c in mira][:3] == [{}, {"resumed": True}, {"resumed": True}],
          [c[2] for c in mira])
    ada = [c[2] for c in calls if c[0] == "ada"]
    check("...the-listener-asked-after-every-move,-and-not-asked-again", ada == [{}, {}, {}], ada)
    check("...then-the-speaker-is-offered-the-silence", [c[1:3] for c in mira][-1:] == [("listener", {"unanswered": True})],
          [c[1:3] for c in calls])
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
    check("...and-the-event-seat-read-the-speaker's-moves-once,-the-silence-never", seats.count("appraise-event") == 1,
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
            return ('"%s"' % " ".join(["word"] * 100), "-", "yield", "ada")
        return ('"A short line."', "-", "yield" if stance == "speaker" else "take", _other(who))
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 2)
    steered = [c for c in calls if c[4]]
    check("a-100-spoken-word-move-is-redrawn-with-the-tripwire-line", len(steered) == 1
          and "pushing for and why" in steered[0][4] and "one point" not in steered[0][4], [c[4] for c in calls])
    check("...the-second-draw-commits-and-the-record-counts-spoken-words", rows[0]["action"] == '"A short line."'
          and rows[0]["validation"].get("tripwire") == {"words": 100, "redrawn_words": 3, "counted": "spoken"}, rows[0])


def test_stage_business_does_not_trip_the_wire(tmp):
    """Gate tripwire-spoken (replay critique E1): the wire counts what was SAID. Most of the drafts it cut in a replay ran
    past 80 words on stage business, under it in speech."""
    business = " ".join(["He sets the cup down on the bench and looks at it."] * 9)

    def script(who, stance, flags, n, steer):
        if who == "mira" and n == 0:
            return ('%s "Sit down, because the tea is hot."' % business, "-", "yield", "ada")
        return ('"A short line."', "-", "yield" if stance == "speaker" else "take", _other(who))
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 2)
    check("100-words-of-action-with-7-spoken-commits-as-drawn,-unsteered",
          exited is None and not any(c[4] for c in calls) and rows[0]["action"].startswith(business)
          and "tripwire" not in rows[0]["validation"], ([c[4] for c in calls], rows[:1]))


def test_every_redraw_is_on_the_record(tmp):
    """Gate tripwire-spoken (replay critique E7): a row was drawn three times - long, then a hold that spoke, then a
    take - and its record named only the first redraw. Each redraw is recorded, the last describing what committed."""
    import scene

    def script(who, stance, flags, n, steer):
        if stance == "speaker":
            return ('"%s says a thing %d."' % (who.title(), n), "-", "yield", _other(who))
        if not steer:
            return ('"%s"' % " ".join(["no"] * 90), "-", "take", _other(who))
        if steer == scene.TRIPWIRE_LINE:
            return ('"The boats are not out."', "-", "hold", _other(who))
        return ('"The boats are not out until the tide turns again."', "-", "take", _other(who))
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 2)
    v = rows[1]["validation"] if len(rows) > 1 else {}
    check("drawn-three-times:-long,-then-a-hold-that-spoke,-then-a-take",
          [c[4] for c in calls if c[1] == "listener"][:3] == [None, scene.TRIPWIRE_LINE, scene.HOLD_SPOKE_LINE],
          [c[:2] + (c[4],) for c in calls])
    check("...the-record-names-both-redraws,-the-last-describing-the-committed-draft",
          rows[1:2] and rows[1]["action"] == '"The boats are not out until the tide turns again."'
          and v.get("tripwire") == {"words": 90, "redrawn_words": 5, "counted": "spoken"}
          and v.get("hold_spoke") == {"said": "hold", "redrawn": "take", "redrawn_words": 10}
          and "floor_corrected" not in v, rows[1:2])


def test_a_steer_never_comes_back_as_the_characters_own_thought(tmp):
    """Gate thought-unsteered (replay critique E2): a row drawn under the tripwire's line is committed as drawn, but
    the next "What you were thinking last" carries the first draw's thought - the character's mind before the
    correction - never the redraw's echo of the steer."""
    def script(who, stance, flags, n, steer):
        if who == "mira" and n == 0:
            return ('"%s"' % " ".join(["go"] * 90), "The boat has to go; Ada must hear why.", "yield", "ada")
        if who == "mira" and steer:
            return ('"Go."', "Watch the door.", "yield", "ada")
        return ('"A short line."', "%s thinks %d." % (who, n), "yield" if stance == "speaker" else "take", _other(who))
    del THOUGHTS[:]
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 4)
    given = [t for w, t in THOUGHTS if w == "mira"]
    check("the-steered-row-commits-its-own-thought", rows and rows[0]["thought"] == "Watch the door.", rows[:1])
    check("...but-mira's-next-call-carries-the-unsteered-thought", len(given) > 2
          and given[2] == "The boat has to go; Ada must hear why.", given)
    check("...and-an-unsteered-row-carries-its-own-thought-as-before",
          [t for w, t in THOUGHTS if w == "ada"][1:2] == ["ada thinks 0."], [t for w, t in THOUGHTS if w == "ada"])


def test_a_talk_that_has_run_out_settles(tmp):
    """gate settled-stop: a two-hander never lulls, so a talk going round in circles ends when four moves in a row
    say nothing their speaker had not said; one saying something new each move runs to its budget."""
    lines = {"mira": ('"The boat stays tied tonight."', '"Tonight. The boat stays tied."'),
             "ada": ('"The boat goes out at dawn."', '"At dawn the boat goes out."')}

    def circling(who, stance, flags, n, steer):
        return ("%s says, %s" % (who.title(), lines[who][min(n, 1)]), "-",
                "yield" if stance == "speaker" else "take", _other(who))
    out, exited, calls, rows = _run(os.path.join(tmp, "circling"), ("mira", "ada"), circling, 12)
    check("a-two-hander-going-round-in-circles-ends-settled-after-four-repeated-moves",
          exited is None and "said nothing new" in out and "scene ended: settled" in out and len(rows) == 6,
          (exited, len(rows), out[-400:]))

    def fresh(who, stance, flags, n, steer):
        return ('%s says, "Point number %s."' % (who.title(), "abcdefghijkl"[n] * 3), "-",
                "yield" if stance == "speaker" else "take", _other(who))
    out, exited, calls, rows = _run(os.path.join(tmp, "fresh"), ("mira", "ada"), fresh, 6)
    check("...and-one-saying-something-new-each-move-runs-to-its-budget",
          exited is None and len(rows) == 6 and "said nothing new" not in out, (exited, len(rows), out[-400:]))


def test_a_directed_move_is_aimed_where_the_direction_says(tmp):
    """gate directed-addressee: the scene file's `cast[].to` names whom a character's moves are aimed at. Her prompt is
    told; her rows record that id even when the actor wrote another, which goes on the validation record; the
    directed person is asked first. A `to` naming no one in the cast, herself, or blank refuses the run."""
    def script(who, stance, flags, n, steer):
        if who == "mira":
            return ("Mira speaks, %d." % n, "-", "yield" if stance == "speaker" else "take", "ada")
        return ("%s answers." % who.title(), "-", "take" if stance == "listener" else "yield", "mira")
    out, exited, calls, rows = _run(os.path.join(tmp, "aimed"), ("mira", "ada", "tomas"), script, 3, to={"mira": "tomas"})
    mira_calls = [c for c in calls if c[0] == "mira"]
    check("the-directed-character's-call-carries-whom-she-speaks-to",
          exited is None and mira_calls and all(c[2].get("to") == ("tomas", "Tomas") for c in mira_calls),
          (exited, [c[:3] for c in calls], out[-400:]))
    mira = [r for r in rows if r["actor"] == "mira"]
    check("...her-rows-record-the-directed-addressee", mira and all(r["addressee"] == "tomas" for r in mira),
          [(r["actor"], r["addressee"]) for r in rows])
    check("...and-the-actor's-own-choice-is-on-the-validation-record",
          mira and all(r["validation"].get("addressee_directed") == {"directed": "tomas", "said": "ada"} for r in mira),
          [r["validation"] for r in mira])
    check("...the-directed-person-is-asked-first", len(calls) > 1 and calls[1][0] == "tomas", [c[:2] for c in calls])
    others = [c for c in calls if c[0] != "mira"]
    check("...and-nobody-else-is-directed", all("to" not in c[2] for c in others), [c[:3] for c in others])
    for label, bad in (("not-in-the-cast", "nobody"), ("herself", "mira"), ("blank", "")):
        out, exited, calls, rows = _run(os.path.join(tmp, label), ("mira", "ada"), script, 2, to={"mira": bad})
        check("a-to-naming-%s-refuses-the-run-by-name-before-any-row" % label,
              "SCENE_DIRECTED_TO_UNKNOWN" in "%s%s" % (exited, out) and not rows and not calls,
              (exited, len(rows), out[-300:]))


def _db(book):
    import glob
    con = sqlite3.connect(glob.glob(os.path.join(book, "runs", "*.db"))[0])
    con.row_factory = sqlite3.Row
    return con


def test_a_window_is_read_once_at_its_last_row(tmp):
    """gate window-reads (design v2 s5): keep, keep, yield is one window - one act Event, on its last row, and the two
    rows before it commit with a manifest naming the window they belong to."""
    def script(who, stance, flags, n, steer):
        if who == "mira":
            return ("Mira's paragraph %d." % n, "-", ("keep", "keep", "yield")[min(n, 2)], "ada")
        return ("", "", "hold", "")
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 3)
    con = _db(os.path.join(tmp, "The Rock"))
    turns = [r[0] for r in con.execute("SELECT turn FROM turns ORDER BY turn")]
    acts = [r[0] for r in con.execute("SELECT turn FROM events WHERE actor = 'mira' AND type NOT IN ('turn-skipped') "
                                      "AND type NOT LIKE 'law%' ORDER BY turn")]
    check("three-rows,-one-act-event,-on-the-last-row", exited is None and len(turns) == 3 and acts == [turns[-1]],
          (exited, turns, acts, out[-500:]))
    wins = [json.loads(r[0]).get("window") for r in con.execute("SELECT manifest FROM decision_manifests ORDER BY turn")]
    check("...every-row's-manifest-names-the-window", wins == [{"from": turns[0], "close": turns[-1]}] * 2
          + [dict(wins[-1] or {}, **{"from": turns[0], "close": turns[-1]})] and "reads" in (wins[-1] or {}), wins)


def test_an_interjection_is_its_own_read_and_the_listeners_feeling_lands_at_the_windows_end(tmp):
    """Under the seats: Mira keeps, Ada interjects, Mira yields, Ada takes. The first window (three rows) is read once
    for Mira's act, once for Ada's interjection, and once each for their feelings, Ada's written at Mira's last row;
    Ada's take is the second window. The fold re-derives every cached mood, the listener's included."""
    from src.engine import bible, mood_fold

    def script(who, stance, flags, n, steer):
        if who == "mira":
            return ('"The boat stays tied, %d."' % n, "-", ("keep", "yield")[min(n, 1)], "ada")
        if n == 0:
            return ('"Nonsense!"', "She thinks it is nonsense.", "interject", "mira")
        return ('"Then we wait."', "-", "take", "mira")
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 4, stub=False)
    seats = dict(c for c in calls if c[0] == "seats")["seats"]
    check("four-rows:-keep,-interject,-yield,-take", [(r["actor"], r["floor"]) for r in rows]
          == [("mira", "keep"), ("ada", "interject"), ("mira", "yield"), ("ada", "take")], ([(r["actor"], r["floor"])
                                                                                             for r in rows], out[-500:]))
    check("...two-windows:-three-event-reads-and-four-emotion-reads-(mira-takes-in-ada's-take:-listener-read)",
          seats.count("appraise-event") == 3 and seats.count("appraise-emotion") == 4, seats)
    con = _db(os.path.join(tmp, "The Rock"))
    t = [r[0] for r in con.execute("SELECT turn FROM turns ORDER BY turn")]
    read_at = {(r[0], r[1]) for r in con.execute("SELECT turn, actor FROM readings")}
    check("...the-listener's-feeling-is-written-at-the-window's-last-row-under-her-own-name",
          read_at == {(t[2], "mira"), (t[2], "ada"), (t[3], "ada"), (t[3], "mira")}, sorted(read_at))
    got = mood_fold.replay(con, con.execute("SELECT run_id FROM runs").fetchone()[0],
                           bible.for_run(con, con.execute("SELECT run_id FROM runs").fetchone()[0])[2])
    cache = {(r[0], r[1]): json.loads(r[2]) for r in con.execute("SELECT turn, char_id, affect FROM current_state")}
    worst = max((abs(got[k][p] - v) for k in cache if k in got for p, v in cache[k].items()), default=float("inf"))
    check("...and-the-fold-re-derives-every-cached-mood-to-1e-12", set(cache) <= set(got) and worst <= 1e-12,
          (worst, sorted(set(cache) - set(got))))


def test_the_exchange_shows_the_thread_and_your_own_lines(tmp):
    def script(who, stance, flags, n, steer):
        return ("%s line %d." % (who.title(), n), "-", "yield" if stance == "speaker" else "take", _other(who))
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 3)
    third = calls[2]
    check("the-moment-marks-the-reader's-own-line-and-whom-it-was-to",
          third[0] == "mira" and 'You, to Ada: "Mira line 0."' in third[3]
          and 'Ada, to you: "Ada line 0."' in third[3], third[3][-300:])


def test_the_authors_direction_is_kept_or_the_run_is_refused(tmp):
    """The partner's direction aims Mira at Ada (gate direction-contract); a cfg the director wrote without that `to`
    is refused before the chronicle opens, and one that keeps it runs."""
    def script(who, stance, flags, n, steer):
        return ("%s says a thing %d." % (who, n), "-", "yield" if stance == "speaker" else "take", _other(who))
    direction = os.path.join(tmp, "direction.json")
    with open(direction, "w", encoding="utf-8") as fh:
        json.dump({"book": "The Rock", "kind": "scene", "intent": "the keepers wait out the gale",
                   "cast": [{"id": "mira", "to": "ada"}, "ada"]}, fh)
    out, exited, calls, rows = _run(os.path.join(tmp, "dropped"), ("mira", "ada"), script, 2,
                                    extra=["--direction", direction])
    check("a-cfg-that-drops-the-directed-to-is-refused,-named,-before-a-turn",
          "HANDOFF_DIRECTION_DROPPED" in str(exited) and "mira" in str(exited) and not rows and not calls,
          (exited, len(rows), out[-300:]))
    out, exited, calls, rows = _run(os.path.join(tmp, "kept"), ("mira", "ada"), script, 2, to={"mira": "ada"},
                                    extra=["--direction", direction])
    check("...and-one-that-keeps-it-runs", exited is None and len(rows) == 2, (exited, out[-300:]))
    import hashlib
    with open(direction, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    marks = [json.loads(m[0]).get("direction") for m in _db(os.path.join(tmp, "kept", "The Rock")).execute(
        "SELECT manifest FROM decision_manifests ORDER BY turn")]
    check("...every-turn's-manifest-names-the-direction-it-was-checked-against", marks == [sha, sha], marks)


def test_a_run_says_whether_a_direction_was_checked(tmp):
    """Neither --direction nor --no-direction is refused by name before a turn (gate direction-required); a run by
    hand says --no-direction, and its record says so."""
    import scene
    def script(who, stance, flags, n, steer):
        return ("%s says a thing %d." % (who, n), "-", "yield" if stance == "speaker" else "take", _other(who))
    book, cfg = _book(os.path.join(tmp, "bare"), ("mira", "ada"))
    saved, sys.argv = sys.argv, ["scene.py", "--book", book, "--model", "fake/model", "--no-keeper", "--scene", cfg,
                                 "--budget", "2", "--stub"]
    exited = None
    try:
        scene.main()
    except SystemExit as e:
        exited = str(e)
    finally:
        sys.argv = saved
    check("neither-flag-is-HANDOFF_DIRECTION_REQUIRED-before-a-turn",
          "HANDOFF_DIRECTION_REQUIRED" in str(exited) and not _rows(book), exited)
    out, exited, calls, rows = _run(os.path.join(tmp, "byhand"), ("mira", "ada"), script, 2)
    marks = [json.loads(m[0]).get("direction") for m in _db(os.path.join(tmp, "byhand", "The Rock")).execute(
        "SELECT manifest FROM decision_manifests ORDER BY turn")]
    check("...--no-direction-runs,-and-every-turn's-manifest-says-none", exited is None and marks == ["none", "none"],
          (exited, marks))


def test_each_actor_keeps_their_own_composer_selection(tmp):
    """Gate composer-reuse: the driver hands each actor's every call that actor's own keep, one per actor for the run,
    so identical rows on their next call reuse the selection and another's never does."""
    def script(who, stance, flags, n, steer):
        return ("%s says a thing %d." % (who, n), "-", "yield" if stance == "speaker" else "take", _other(who))
    del KEPT[:]
    out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 4)
    ids = {w: {k for x, k in KEPT if x == w} for w in ("mira", "ada")}
    check("each-actor's-calls-carry-one-keep-of-their-own", exited is None and all(
        len(v) == 1 and None not in v for v in ids.values()) and ids["mira"] != ids["ada"], (exited, KEPT))


def test_the_director_holds_the_floor_open(tmp):
    """Gate placements (design v2 s2 rule 4, s3): a scene file's hold_open opens on its speaker, who is called again
    while they keep and nobody is asked; on their yield the room's reaction is shown to the next actor and kept as an
    Event on that row; `moves` is the ceiling when no --budget is given."""
    def script(who, stance, flags, n, steer):
        if stance == "speaker" and flags.get("hold_open"):
            return ("%s goes on, part %d." % (who.title(), n), "-", "keep" if n < 2 else "yield", _other(who))
        return ("%s answers, %d." % (who.title(), n), "-", "take" if stance == "listener" else "yield", _other(who))
    plain = _run(os.path.join(tmp, "plain"), ("mira", "ada"), script, 2)[2]
    held = _other(plain[0][0])                        # whoever salience would NOT open with
    room = "The lamp gutters and the gale drops."
    out, exited, calls, rows = _run(os.path.join(tmp, "held"), ("mira", "ada"), script, None,
                                    keys={"moves": 5, "hold_open": {"speaker": held, "when": "opening", "reaction": room}})
    check("the-held-speaker-opens-and-is-called-three-times-with-nobody-asked",
          exited is None and [c[:2] for c in calls[:3]] == [(held, "speaker")] * 3
          and all(c[2].get("hold_open") for c in calls[:3]), (exited, [c[:3] for c in calls], out[-400:]))
    check("...then-the-listener-is-asked,-and-reads-the-room", len(calls) > 3 and calls[3][:2] == (_other(held), "listener")
          and "The room: %s" % room in calls[3][3], calls[3][3] if len(calls) > 3 else calls)
    check("...the-hold-ends-with-the-speech", not any(c[2].get("hold_open") for c in calls[3:]), [c[:3] for c in calls])
    check("...moves-is-the-ceiling-without---budget", len(rows) == 5, len(rows))
    con = _db(os.path.join(tmp, "held", "The Rock"))
    placed = [(r["turn"], r["actor"], json.loads(r["payload"])) for r in con.execute(
        "SELECT turn, actor, payload FROM events WHERE type = 'placed-reaction'")]
    turns = [r["turn"] for r in con.execute("SELECT turn FROM turns ORDER BY turn")]
    check("...and-the-reaction-is-an-Event-with-no-actor-on-the-yielding-row",
          len(turns) == 5 and placed == [(turns[2], None, {"text": room})], placed)
    # THE NARRATOR SEES THE ROOM (gate narrator-room): under the row it rides, for a POV who did not speak
    import types
    import critic
    import narrate
    from narration_contract import transcript
    got = critic.scene_turns(types.SimpleNamespace(con=con), con.execute("SELECT run_id FROM turns").fetchone()[0])
    entries = narrate.pov_split(got, _other(held))
    legend, lines = transcript(entries, _other(held), "POV", {}, "pov")
    check("...the-narrator's-transcript-shows-the-room-under-the-speech-that-ended",
          [r["room"] for r in got] == ["", "", room, "", ""] and "beat 3 · THE ROOM: %s" % room in lines.splitlines()
          and lines.splitlines().index("beat 3 · THE ROOM: %s" % room) == 3 and "THE ROOM  " in legend, (got, lines))
    plain = transcript(narrate.pov_split([dict(r, room="") for r in got], _other(held)), _other(held), "POV", {}, "pov")
    check("...and-without-one-no-room-text-at-all", "ROOM" not in "".join(plain), plain)
    # THE CRITIC SEES IT TOO (gate critic-room): continuity is judged against the whole record
    crit = critic.build_critic_prompt(got, {})[1]["content"].splitlines()
    at = "[%d] THE ROOM: %s" % (got[2]["turn"], room)
    check("...the-critic's-transcript-shows-the-room-after-that-turn", at in crit
          and crit[crit.index(at) - 1].startswith("[%d] %s:" % (got[2]["turn"], held)), crit)
    check("...and-a-row-without-one-renders-as-before", "ROOM" not in critic.build_critic_prompt(
        [dict(r, room="") for r in got], {})[1]["content"])
    out, exited, calls, rows = _run(os.path.join(tmp, "open"), ("mira", "ada"), script, None)
    check("with-no---budget-and-no-moves-the-ceiling-is-24", exited is None and len(rows) == 24, (exited, len(rows)))
    out, exited, calls, rows = _run(os.path.join(tmp, "bad"), ("mira", "ada"), script, 2,
                                    keys={"hold_open": {"speaker": "tomas"}})
    check("a-hold_open-on-someone-not-in-the-cast-refuses-the-run-by-name",
          "SCENE_HOLD_OPEN_UNKNOWN" in "%s%s" % (exited, out) and not rows and not calls, (exited, out[-300:]))


def test_a_hold_that_speaks_is_a_take(tmp):
    """Gate hold-that-spoke (the first live replay, 2026-10-17): a listener's hold whose act is a spoken answer
    is drawn once more with the line that names it; still speaking, it is read as a take - the other party is asked
    next, and the scene does not end settled on it."""
    import scene
    asked = []

    def script(who, stance, flags, n, steer):
        if stance == "speaker":
            return ("%s says a thing %d." % (who.title(), n), "-", "yield", _other(who))
        asked.append(who)
        if len(asked) == 1:
            return ('"Is the tide in?" %s asks.' % who.title(), "-", "take", _other(who))
        return ('"Not yet. Soon," %s says.' % who.title(), "-", "hold", _other(who))
    out, exited, calls, rows = _run(os.path.join(tmp, "spoke"), ("mira", "ada"), script, 4)
    lst = [c for c in calls if c[1] == "listener"]
    check("the-hold-that-spoke-is-drawn-once-more-with-the-line",
          exited is None and len(lst) > 2 and lst[2][4] == scene.HOLD_SPOKE_LINE and lst[2][0] == lst[1][0],
          (exited, [c[:2] + (c[4],) for c in calls]))
    fixed = [r for r in rows if r["validation"].get("floor_corrected")]
    check("...still-speaking,-it-commits-as-a-take-and-the-record-says-so",
          fixed and fixed[0]["floor"] == "take" and fixed[0]["validation"]["floor_corrected"] == {"said": "hold", "kept": "take"},
          [(r["actor"], r["floor"], r["validation"].get("floor_corrected")) for r in rows])
    check("...the-other-party-is-asked-next,-not-forced,-and-it-does-not-settle",
          len(lst) > 3 and lst[3][0] != lst[2][0] and not lst[3][2].get("forced") and "== settled" not in out,
          ([c[:3] for c in calls], out[-300:]))

    def heeds(who, stance, flags, n, steer):
        if stance == "listener" and steer:
            return ('"Soon," %s says.' % who.title(), "-", "take", _other(who))
        return script(who, stance, flags, n, steer)
    del asked[:]
    out, exited, calls, rows = _run(os.path.join(tmp, "heeds"), ("mira", "ada"), heeds, 3)
    check("a-redraw-that-takes-is-kept-as-drawn,-with-no-correction",
          exited is None and [r["floor"] for r in rows][:3] == ["yield", "take", "take"]
          and not any(r["validation"].get("floor_corrected") for r in rows), [(r["actor"], r["floor"]) for r in rows])

    def quiet(who, stance, flags, n, steer):
        if stance == "speaker":
            return ("%s says a thing %d." % (who.title(), n), "-", "yield", _other(who))
        return ("", "%s keeps quiet." % who.title(), "hold", _other(who))
    out, exited, calls, rows = _run(os.path.join(tmp, "quiet"), ("mira", "ada"), quiet, 6)
    check("a-silent-hold-twice-still-settles,-and-the-line-prints-after-the-last-rows",
          "== settled" in out and out.index("== settled") > out.rindex("-- beat"), out[-500:])


def test_the_one_refused_feels_it(tmp):
    """Gate listener-read (showrunner ruling 2026-10-17 09:00; a replayed two-hander's refused character got no
    reading on any turn he was refused): Mira asks, Ada refuses, by turns - every window is one row. At each window's
    end the other present participant is read too, from a prompt that says she did not act and shows what she took in
    and what she was thinking last; the reading is written at that row under her own name, and the fold re-derives
    every cached mood."""
    import appraiser
    from src.engine import bible, mood_fold
    prompts, real = [], appraiser.build_emotion_messages

    def spy(*a, **kw):
        out = real(*a, **kw)
        prompts.append((kw.get("me"), out[1]["content"]))
        return out

    def script(who, stance, flags, n, steer):
        if who == "mira":
            return ('"Look at the sky, %d."' % n, "Mira wants her to look.", "yield", "ada")
        return ('"No."', "Ada will not look up.", "take", "mira")
    appraiser.build_emotion_messages = spy
    try:
        out, exited, calls, rows = _run(tmp, ("mira", "ada"), script, 4, stub=False)
    finally:
        appraiser.build_emotion_messages = real
    con = _db(os.path.join(tmp, "The Rock"))
    t = {r[0]: r[1] for r in con.execute("SELECT turn, actor FROM turns ORDER BY turn")}
    read_at = {(r[0], r[1]) for r in con.execute("SELECT turn, actor FROM readings")}
    refused = [k for k, v in t.items() if v == "ada"]
    check("the-one-refused-is-read-at-every-turn-she-is-refused",
          exited is None and refused and all((k, "mira") in read_at for k in refused), (sorted(read_at), t, out[-400:]))
    check("...and-the-one-who-acted-is-read-as-before", all((k, v) in read_at for k, v in t.items()), sorted(read_at))
    heard = [p for me, p in prompts if me == "mira" and "THEY DID NOT ACT" in p]
    check("...from-a-prompt-that-says-she-did-not-act-and-shows-what-she-took-in-and-was-thinking",
          heard and '"No."' in heard[0] and "Mira wants her to look." in heard[0] and "WHAT THEY DID:" not in heard[0],
          heard[:1] or [p[:300] for _m, p in prompts[:2]])
    spoke = [p for me, p in prompts if "THEY DID NOT ACT" not in p]
    check("...each-actor's-own-prompt-is-the-one-it-always-was", len(spoke) == len(t) and all(
        "WHAT THEY DID:" in p for p in spoke), (len(spoke), len(t), spoke[:1]))
    run = con.execute("SELECT run_id FROM runs").fetchone()[0]
    got = mood_fold.replay(con, run, bible.for_run(con, run)[2])
    cache = {(r[0], r[1]): json.loads(r[2]) for r in con.execute("SELECT turn, char_id, affect FROM current_state")}
    worst = max((abs(got[k][p] - v) for k in cache if k in got for p, v in cache[k].items()), default=float("inf"))
    check("...and-the-fold-re-derives-every-cached-mood-to-1e-12", set(cache) <= set(got) and worst <= 1e-12,
          (worst, sorted(set(cache) - set(got))))


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
