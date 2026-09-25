#!/usr/bin/env python3
"""test_windows.py — a scene set in a character's past is a WINDOW for them (gate flashback-windows, 2026-09-25).

THE OWNER'S RULE (plan step 4, approved 2026-09-25): a scene set earlier than the point a character's own story has
reached plays them as they were then, and nothing it produces reaches their present; for a character new to the
story it is where their timeline starts. A notice before the scene says whom it is a window for; a report after it
says what it would have added. The worry it answers: "we've followed X for 43 chapters - why suddenly does he have
these effects?"

  [1] THE DIFFERENTIAL: one story run with a window for mira and once without it - her present, and everyone else's
      who was not in it, ends identical; inside it she plays from her state as of that time; the newcomer carries it;
      a second window does not see the first; the notice, the report, and the mood replay, exact
  [2] a scar minted in a window can be minted again in the present (schema v33), and an older store migrates
  [3] the refusals: two places at once, the chair in a character's past, and a chair with no clock after a window
  [5] a window before a character's first scene plays them from their sheet (gate window-before-first-scene - it was
      refused), their bonds resting where the sheet puts them, and advises a sheet for then when the gap is long

Scenes run through scripts/scene.py main IN PROCESS with the seats faked and nothing turn-dependent in the fakes
(test_own_timelines._run), so the two runs can be compared beat for beat. Script-style: check(), main(), exit code.
"""
import copy
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

from src.engine import bible, clock, passage, window, wound                         # noqa: E402
from src.engine.ledger import Ledger                                                # noqa: E402
from src.engine.records import RecordError                                          # noqa: E402
from test_own_timelines import ADA, MIRA, TOMAS, WREN, _four, _run, _starts         # noqa: E402  (one fixture)
from test_story_time import _con, _folded, _openings, _slow                         # noqa: E402

FAILS = []
S1 = ("lamp-1", 1, "08:00", "2h", 2, [MIRA, ADA])
S2 = ("lamp-2-hard", 3, "08:00", "2h", 2, [MIRA, ADA])      # moves her resting moods
S3 = ("boat-window-hard", 1, "10:30", "2h", 2, [MIRA, ADA, TOMAS])   # half an hour after lamp-1: what she carries in shows   # mira's past and ada's; tomas's first scene
S4 = ("lamp-4", 3, "10:30", "1h", 2, [MIRA, ADA])         # half an hour after lamp-2: a carried mood shows
S5 = ("net-window", 2, "16:00", "1h", 2, [MIRA, WREN])        # mira's past again; wren's first scene


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _replay_ok(db, run_id, label):
    """THIS suite's replay check. A check helper imported from another suite records into THAT suite's failure list,
    so this one failed silently while its own exit code said all was well (found by a mutant, 2026-09-25)."""
    from src.engine import mood_fold
    con = _con(db)
    d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
    check("%s-the-replay-re-derives-every-mood-and-condition" % label,
          d["at"] is None and d["condition_at"] is None and not d["notes"] and not d["missing"], repr(d))


def _moods(con, cid, first, last):
    return [json.loads(r[0]) for r in con.execute(
        "SELECT affect FROM current_state WHERE char_id = ? AND turn BETWEEN ? AND ? ORDER BY turn", (cid, first, last))]


def _claims(led, run_id, cid, view=None):
    return sorted(str(b.get("claim")) for b in led.acquisitions_for(run_id, cid, view))


def _fallbacks():
    """Spy: every read of a window character's history, inside their window, that fell back to their present
    (`window.current`) instead of the view the driver handed them -> (fell_back list, windows seen, restore)."""
    import scene as _scene
    real_current, real_open, real_park = window.current, passage.open_scene, _scene.record_and_park
    inside, fell, seen = {"ids": set()}, [], []

    def spy_current(con, run_id, char_id):
        if char_id in inside["ids"]:
            fell.append(char_id)
        return real_current(con, run_id, char_id)

    def spy_open(*a, **kw):
        out = real_open(*a, **kw)
        inside["ids"] = set(out.get("windows") or {})
        seen.extend(sorted(inside["ids"]))
        return out

    def spy_park(*a, **kw):
        inside["ids"] = set()
        return real_park(*a, **kw)

    window.current, passage.open_scene, _scene.record_and_park = spy_current, spy_open, spy_park

    def restore():
        window.current, passage.open_scene, _scene.record_and_park = real_current, real_open, real_park
    return fell, seen, restore


def test_the_differential(tmp):
    print("\n[1] one story with windows for mira (and one for ada) and once without - their present ends identical")
    a_book, b_book = _four(os.path.join(tmp, "with")), _four(os.path.join(tmp, "without"))
    def lamp_2_moves_her(db):
        """What a hard scene does to a resting mood, written as lamp-2's own row: her resting wariness rises. A window
        set before lamp-2 must play her without it; her present after lamp-2 carries it. (The fake scenes move no
        resting mood by themselves, and a replay that resumed a window in her present could not be told apart.)"""
        con = sqlite3.connect(db)
        last2 = con.execute("SELECT end_turn FROM scenes WHERE label = 'lamp-2-hard'").fetchone()[0]
        with con:
            con.execute("INSERT INTO arc_diffs (run_id, char_id, turn, diff) SELECT run_id, 'mira', ?, ? FROM runs",
                        (last2, json.dumps({"temperament": {"WARINESS": 0.15}})))
        con.close()
    fell, seen, restore = _fallbacks()
    try:
        a_db, a_run, a_outs, a_steps = _run(a_book, os.path.join(tmp, "with"), (S1, S2))
        lamp_2_moves_her(a_db)
        _d, _r, more_outs, more_steps = _run(a_book, os.path.join(tmp, "with"), (S3, S4, S5), resume=True)
        a_outs, a_steps = a_outs + more_outs, a_steps + more_steps
    finally:
        restore()
    check("inside-a-window-no-read-of-their-history-fell-back-to-their-present", seen == ["ada", "mira", "mira"]
          and not fell, (seen, fell[:6]))
    b_db, b_run, b_outs, _b_steps = _run(b_book, os.path.join(tmp, "without"), (S1, S2))
    lamp_2_moves_her(b_db)
    _d, _r, more_outs, _more = _run(b_book, os.path.join(tmp, "without"), (S4,), resume=True)
    b_outs = b_outs + more_outs
    check("all-scenes-ran", all("SYSTEMEXIT" not in o for o in a_outs + b_outs), [o[-300:] for o in a_outs + b_outs])
    a, b = _con(a_db), _con(b_db)
    sa, sb = _starts(a), _starts(b)
    check("five-scenes-with-the-windows,-three-without", len(sa) == 5 and len(sb) == 3, (sa, sb))
    notice, report = a_outs[2].find("WINDOW : Mira plays as of day 1 10:30"), a_outs[2].find("WINDOW : mira - had this")
    first_beat = a_outs[2].find("=== SCENE")
    check("the-notice-names-her-before-the-scene's-first-beat", 0 <= notice < first_beat, a_outs[2][:1200])
    check("...and-ada,-and-no-one-else-(it-is-tomas's-first-scene)", "WINDOW : Tomas" not in a_outs[2]
          and "WINDOW : Ada plays as of day 1 10:30" in a_outs[2] and "a window for ada, mira" in a_outs[2], a_outs[2][:1200])
    check("the-report-follows-the-scene", report > first_beat and ("toward tomas" in a_outs[2][report:]
                                                                  or "a memory:" in a_outs[2][report:]),
          a_outs[2][report:report + 600])
    check("no-notice-where-no-one-is-in-their-past", all("WINDOW :" not in a_outs[i] for i in (0, 1, 3)))
    # INSIDE THE WINDOW: she plays from her state as of day 1 10:30 - after lamp-1, before lamp-2
    (s1, _e1), (s2, _e2), (s3, e3), (s4, e4), (s5, _e5) = sa
    minutes, held = _openings(a_steps, "boat-window-hard")["mira"]
    check("she-opens-the-window-aged-by-her-own-time-since-lamp-1-(half-an-hour)", minutes == 30.0, minutes)
    check("...as-she-stood-after-lamp-1,-nothing-of-lamp-2", held == _folded(a, a_run, "mira", s2), held)
    led = Ledger(a_db)
    v3 = window.view(led.con, a_run, "mira", reading=s3)
    check("her-view-there-is-a-window", window.is_window(v3) and v3.cut == s2 and v3.since == s3, v3)
    asof = v3._replace(since=10 ** 9)             # the window's view before its own first beat: her past alone
    s1_last = led.con.execute("SELECT affect, condition FROM current_state WHERE char_id='mira' AND turn < ? ORDER BY turn DESC",
                              (s2,)).fetchone()
    check("...her-mood-and-condition-there-are-lamp-1's-last", led.latest_affect(a_run, "mira", asof)
          == {"affect": json.loads(s1_last[0]), "condition": json.loads(s1_last[1])})
    learned = lambda view: sorted(int(b["created_turn"]) for b in led.acquisitions_for(a_run, "mira", view))
    check("...and-no-memory-she-made-in-lamp-2-reaches-it", learned(asof) and max(learned(asof)) < s2
          and any(s2 <= t < s3 for t in learned(window.current(a, a_run, "mira"))), (learned(asof), s2))
    # THE NEWCOMER CARRIES IT: the scene is tomas's first, his own story
    sheet = copy.deepcopy(bible.for_run(a, a_run)[2]["tomas"])
    check("tomas-carries-his-first-scene-into-his-present", _folded(a, a_run, "tomas", 10 ** 6) != _folded(a, a_run, "tomas", s3)
          or _claims(led, a_run, "tomas"), (_folded(a, a_run, "tomas", 10 ** 6), sheet["current"].get("relationships")))
    # AFTER IT: her present, and ada's, exactly as a run without the window
    head_a, head_b = s5, b.execute("SELECT MAX(turn) FROM turns").fetchone()[0] + 1
    for cid in ("mira", "ada"):
        check("%s's-moods-in-lamp-4-are-the-run-without-the-window's" % cid,
              _moods(a, cid, s4, e4) == _moods(b, cid, sb[2][0], sb[2][1]) and _moods(a, cid, s4, e4))
        fa, fb = _folded(a, a_run, cid, head_a), _folded(b, b_run, cid, head_b)
        check("%s's-bonds-scars-and-means-after-it-are-too" % cid, fa == fb, {k: (fa[k], fb[k]) for k in fa if fa[k] != fb[k]})
        check("%s's-memories-too" % cid, _claims(led, a_run, cid, window.current(a, a_run, cid)) == _claims(Ledger(b_db), b_run, cid))
    check("her-latest-mood-in-her-present-is-lamp-4's-last", led.latest_affect(a_run, "mira")["affect"] == _moods(a, "mira", s4, e4)[-1])
    # A SECOND WINDOW DOES NOT SEE THE FIRST: net-window rebuilds her as boat-window did, from lamp-1
    _m5, held5 = _openings(a_steps, "net-window")["mira"]
    check("the-second-window-rebuilds-her-as-the-first-did-(windows-do-not-chain)", held5 == held, (held5, held))
    _replay_ok(a_db, a_run, "with-two-windows")
    led.con.close()
    return a_db, a_run, sa


def test_each_reader_holds_to_the_view(a_db, a_run, sa):
    """Every reader of one character's history, on the story with two windows for mira: her present leaves the
    windows' rows out, every row keeps them. Some of what the fake scenes cannot produce - a cliff, a hurt - is
    written into a window here, so a reader that stopped filtering would show it."""
    print("\n[4] each reader of her history holds to her view")
    from src.engine import bond_rest, decay, injuries, scene_facts, targets
    from src.engine.records import RestDeclared
    (_s1, _e1), (_s2, _e2), (s3, e3), (s4, e4), (s5, e5) = sa
    led = Ledger(a_db)
    con, now, allv = led.con, window.current(led.con, a_run, "mira"), window.ALL
    in_windows = lambda t: s3 <= int(t) <= e3 or s5 <= int(t) <= e5
    check("her-present-leaves-both-windows-out", now.excluded == ((s3, e3), (s5, e5)) and not window.is_window(now), now)
    with con:                                    # a cliff, a hurt, a thing she was told and a bind, in her first window
        bond_rest.write(con, a_run, s3, [RestDeclared("mira", "tomas", "trust", 0.1, "cliff")])
        con.execute("INSERT INTO events (run_id, turn, caused_at, effective_at, type, actor, payload) VALUES "
                    "(?, ?, 0, 0, 'harm', 'mira', ?)", (a_run, s3, json.dumps(
                        {"injuries": [{"who": "self", "quote": "a rope burn", "severity": "minor"}],
                         "told": [{"what": "the boat leaks at the stern", "to": "mira"}]})))
        con.execute("INSERT INTO target_binds (run_id, turn, char_id, primary_, target) VALUES (?, ?, 'mira', 'WARINESS', "
                    "'tomas')", (a_run, s3))
        wound.write_mints(con, a_run, s3, "mira", [wound.make("exile", "DEFLATION", 0.5, "run:%d" % s3, text="a beat")])
        free = [t for t in range(s3, e3 + 1) if not con.execute("SELECT 1 FROM arc_diffs WHERE char_id='mira' AND turn=?",
                                                                (t,)).fetchone()]
        con.execute("INSERT INTO arc_diffs (run_id, char_id, turn, diff) VALUES (?, 'mira', ?, ?)",
                    (a_run, free[0], json.dumps({"temperament": {"WARINESS": 0.2}})))
        quiet = [t for t in range(s3, e3 + 1) if not con.execute("SELECT 1 FROM decision_manifests WHERE actor='mira' "
                                                                 "AND turn=?", (t,)).fetchone()]
        con.execute("INSERT INTO decision_manifests (run_id, turn, actor, manifest) VALUES (?, ?, 'mira', ?)",
                    (a_run, quiet[0], json.dumps({"recall_ids": ["b:a-window-recall"]})))
    sheet = copy.deepcopy(bible.for_run(con, a_run)[2]["mira"])
    passage.stamp_authored(sheet)
    head = e5 + 1
    pairs = (
        ("rest-rows", lambda v: [r[0] for r in bond_rest.rows_for(con, a_run, "mira", v)]),
        ("time-items", lambda v: [t for t, _s, _m in clock.time_items(con, a_run, "mira", view=v)]),
        ("last-presence", lambda v: [clock.last_present(con, a_run, "mira", head, v)]),
        ("memories", lambda v: [b["created_turn"] for b in led.acquisitions_for(a_run, "mira", v)]),
        ("last-turn", lambda v: [led.last_turn(a_run, "mira", v)]),
        ("last-readings", lambda v: list(led.last_read_turn(a_run, "mira", v).values())),
        ("previous-mood", lambda v: [t for (t, aff) in con.execute(
            "SELECT turn, affect FROM current_state WHERE char_id='mira' AND turn < ?", (s4,))
            if json.loads(aff) == led.previous_affect(a_run, "mira", s4, v)]),
        ("binds", lambda v: [s3] if ("WARINESS", "tomas") in targets.binds_for(con, a_run, "mira", view=v) else []),
        ("facts", lambda v: [r["turn"] for r in scene_facts.facts_for(con, a_run, "mira", view=v, budgets=None)]),
        ("hurts", lambda v: [r["what"] for r in injuries.for_actor(con, a_run, "mira", {}, head, v)]),
        ("recalls", lambda v: [h["last_turn"] for h in decay.fold_recall_history(con, a_run, "mira", v).values()]),
        ("bond-timeline-rests", lambda v: [t for t, _s, it in bond_rest.timeline_rows(con, a_run, "mira", view=v)
                                           if it[0] == "rest"]),
        ("scars", lambda v: [w["id"] for w in passage.fold_wounds(con, a_run, "mira", copy.deepcopy(sheet), view=v)
                             if isinstance(w, dict)]),
        ("resting-means", lambda v: [passage.fold_arc(con, a_run, "mira", copy.deepcopy(sheet), view=v)
                                     ["baseline"]["temperament"]["WARINESS"]["mean"]]),
    )
    for name, read in pairs:
        mine, every = read(now), read(allv)
        if name == "hurts":
            ok = "a rope burn" in every and "a rope burn" not in mine
        elif name == "scars":
            ok = "exile@DEFLATION" in every and "exile@DEFLATION" not in mine
        elif name == "resting-means":
            ok = every[0] > mine[0]
        else:
            ok = not any(in_windows(t) for t in mine if t is not None) and any(in_windows(t) for t in every if t is not None)
        check("%s:-her-present-reads-none-of-the-windows',-every-row-does" % name, ok, (mine, every))
    led.con.close()


def test_the_scar_table(tmp):
    print("\n[2] a scar minted in a window can be minted again in the present; an older store migrates")
    led = Ledger(os.path.join(tmp, "scars.db"))
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    m = wound.make("drowning", "DEFLATION", 0.5, "run:3", text="a beat")
    with led.con:
        wound.write_mints(led.con, "r", 3, "mira", [m])
    try:
        with led.con:
            wound.write_mints(led.con, "r", 9, "mira", [m])
        check("the-same-scar-at-another-turn-commits", len(wound.mints_for(led.con, "r", "mira")) == 2)
    except sqlite3.IntegrityError as e:
        check("the-same-scar-at-another-turn-commits", False, str(e))
    try:
        with led.con:
            wound.write_mints(led.con, "r", 9, "mira", [m])
        check("...but-not-twice-in-one-turn", False, "committed")
    except sqlite3.IntegrityError:
        check("...but-not-twice-in-one-turn", True)
    led.con.close()
    schema = open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read()
    old = schema.replace("UNIQUE (run_id, char_id, wound_id, turn)", "UNIQUE (run_id, char_id, wound_id)")
    check("the-v32-table-can-be-made-for-the-test", old != schema)
    path = os.path.join(tmp, "v32.db")
    raw = sqlite3.connect(path)
    raw.executescript(old)
    raw.execute("INSERT INTO wound_minted (run_id, turn, char_id, wound_id, concept, path, intensity) "
                "VALUES ('r', 3, 'mira', 'drowning@DEFLATION', 'drowning', 'DEFLATION', 0.5)")
    raw.execute("PRAGMA user_version = 32")
    raw.commit()
    raw.close()
    led = Ledger(path)
    kept = [tuple(r) for r in led.con.execute("SELECT turn, char_id, wound_id FROM wound_minted")]
    with led.con:
        wound.write_mints(led.con, "r", 9, "mira", [m])
    check("a-v32-store-migrates-with-its-scars-and-takes-the-second",
          kept == [(3, "mira", "drowning@DEFLATION")] and len(wound.mints_for(led.con, "r", "mira")) == 2, kept)
    try:
        led.con.execute("DELETE FROM wound_minted")
        check("...and-is-still-append-only", False, "deleted")
    except sqlite3.DatabaseError as e:
        check("...and-is-still-append-only", "append-only" in str(e), str(e))
    led.con.close()


def test_the_refusals(tmp):
    print("\n[3] the refusals")
    book = _four(os.path.join(tmp, "refuse"))
    db, run_id, outs, _steps = _run(book, os.path.join(tmp, "refuse"), (S1, S2, S3))
    check("three-scenes-ran", all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    led = Ledger(db)
    sheets = bible.for_run(led.con, run_id)[2]
    head = led.con.execute("SELECT MAX(turn) FROM turns").fetchone()[0] + 1
    for label, at, who, code in (("mira-inside-lamp-1", clock.parse_at({"day": 1, "time": "09:00"}), "mira", "CLOCK_TWO_PLACES_AT_ONCE"),
                                 ("mira-inside-her-own-window", clock.parse_at({"day": 1, "time": "11:00"}), "mira", "CLOCK_TWO_PLACES_AT_ONCE")):
        try:
            passage.open_scene(led, run_id, head, at, 30.0, 1, {who: copy.deepcopy(sheets[who])}, windows=True)
            check("%s-is-refused-%s" % (label, code), False, "opened")
        except RecordError as e:
            check("%s-is-refused-%s" % (label, code), e.code == code, e.code)
    check("a-refused-opening-logs-nothing", not led.con.execute("SELECT 1 FROM scene_clock WHERE turn >= ?", (head,)).fetchone())

    def chair(*extra):
        r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira",
                            "--stub", "--resume", run_id] + list(extra), input="quit\n", capture_output=True, text=True,
                           cwd=REPO, timeout=300)
        return r.stdout + r.stderr
    out = chair("--at", "day 2 12:00", "--lasts", "10m")
    check("the-chair-in-her-past-is-refused-(it-stays-in-the-present)", "CLOCK_RUNS_BACKWARDS" in out, out[-400:])
    out = chair()
    check("a-clockless-chair-right-after-a-window-for-her-is-refused", "CLOCK_CHAIR_IN_A_WINDOW" in out, out[-400:])
    check("...and-neither-logged-anything", not led.con.execute("SELECT 1 FROM scene_clock WHERE turn >= ?", (head,)).fetchone()
          and not led.con.execute("SELECT 1 FROM turns WHERE turn >= ?", (head,)).fetchone())
    led.con.close()


def test_before_a_first_scene(tmp):
    """The owner (2026-09-25): "Play the character sheet, if there is a large gap in time advise generating a
    character sheet". Ada first walks on in lamp-1 (day 1 08:00) and tomas in the boat (day 60); a dawn scene at day 1
    06:00 is a window for both, set two hours before ada's first scene and two months before tomas's; a prologue at
    day -400 is a window for mira, and wren's first scene."""
    print("\n[5] a window before a character's first scene plays them from their sheet")
    boat = ("boat", 60, "08:00", "2h", 2, [TOMAS, ADA])
    dawn = ("dawn-window", 1, "06:00", "1h", 2, [ADA, TOMAS])
    prologue = ("prologue-window", -400, "09:00", "1h", 2, [MIRA, WREN])
    book = _four(os.path.join(tmp, "first"))
    db, run_id, outs, steps = _run(book, os.path.join(tmp, "first"), (S1, boat, dawn, prologue))
    check("all-four-ran-(nothing-refused)", all("SYSTEMEXIT" not in o for o in outs), [o[-300:] for o in outs])
    notice = lambda out, who: next((ln for ln in out.splitlines() if ln.strip().startswith("WINDOW : %s plays" % who)), "")
    advised = lambda out, who: "consider generating a character sheet for %s as they were then" % who in out
    check("ada-plays-from-her-sheet,-two-hours-before-it", "from their sheet, which describes them 2 hours later"
          in notice(outs[2], "Ada") and not advised(outs[2], "Ada"), notice(outs[2], "Ada"))
    check("tomas-plays-from-his-sheet,-two-months-before-it,-and-the-notice-advises-a-sheet-for-then",
          "from their sheet, which describes them 2 months later" in notice(outs[2], "Tomas") and advised(outs[2], "Tomas"),
          outs[2][:1500])
    check("mira-a-year-before:-advised-too", "from their sheet, which describes them 1 year later" in notice(outs[3], "Mira")
          and advised(outs[3], "Mira"), notice(outs[3], "Mira"))
    check("wren's-first-scene-is-no-window-for-him", "WINDOW : Wren" not in outs[3], outs[3][:1200])
    con = _con(db)
    starts = _starts(con)
    d0, d1 = starts[2]
    sheets = bible.for_run(con, run_id)[2]
    from src.engine import bond_rest, heritable
    for cid in ("ada", "tomas"):
        sheet = copy.deepcopy(sheets[cid])
        heritable.ensure_temperament(sheet)
        passage.stamp_authored(sheet)
        per_beat = [s[3][cid] for s in steps if s[0] == "dawn-window" and s[1] == "beat" and cid in s[3]]
        check("%s-opens-as-the-sheet-says-and-no-opening-ages-them" % cid, per_beat and per_beat[0] == _slow(sheet)
              and cid not in _openings(steps, "dawn-window"), (per_beat[:1], _slow(sheet)))
        authored = _slow(sheet)["edges"]                   # a bond born in the window is the window's; these are the sheet's
        check("%s's-authored-bonds-rest-where-the-sheet-puts-them-through-every-beat" % cid, per_beat and authored
              and all(b["edges"].get(t) == e for b in per_beat for t, e in authored.items()), [b["edges"] for b in per_beat])
        v = window.view(con, run_id, cid, reading=d0)
        rests = [r for r in bond_rest.rows_for(con, run_id, cid, v) if r[4] == "authored"]
        timeline = [it for _t, _s, it in bond_rest.timeline_rows(con, run_id, cid, view=v) if it[0] == "rest"]
        check("%s's-window-sees-the-sheet's-own-rests,-seeded-at-their-first-scene-after-it" % cid,
              window.is_window(v) and rests and all(r[0] >= v.cut for r in rests) and len(timeline) == len(rests),
              (v, rests, timeline))
    check("a-short-gap-is-not-long", window.sheet_gap(con, run_id, "ada", clock.parse_at({"day": 1, "time": "06:00"}))
          == 120.0 and window.sheet_gap(con, run_id, "ada", clock.parse_at({"day": 2, "time": "06:00"})) is None)
    _replay_ok(db, run_id, "before-a-first-scene")


def main():
    print("test_windows.py — a scene set in a character's past is a window for them (gate flashback-windows)\n")
    tmp = tempfile.mkdtemp(prefix="swe_win_")
    try:
        test_each_reader_holds_to_the_view(*test_the_differential(tmp))
        test_the_scar_table(tmp)
        test_the_refusals(tmp)
        test_before_a_first_scene(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_windows: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
