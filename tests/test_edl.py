#!/usr/bin/env python3
"""test_edl.py — the edit decision list: the RECORD half of the cut (cutting-room.md part 3).

WHAT THIS PROVES, and what it deliberately does not.

`docs/cutting-room.md` divides the cut three ways and marks exactly one human: views are computed,
the discussion belongs to the room, and "decisions append to the EDL; narration renders from it;
audits verify the result. Faithfulness is never a vibe." Part 3 did not exist — grepping the tree
for `edl` returned nothing — so the cut was human AND unrecorded, and the README's "every line of
the book traces to a recorded biographical moment" had no mechanism behind it.

It does NOT test selection, ordering, spine-finding or chapter placement. The same doc records a
7-step automated cut pipeline that was drafted and REJECTED, because "we have performed this craft
zero times on real sim data — automating it first would calibrate gates against taste we haven't
formed". A test asserting a cut is GOOD would be that pipeline arriving through the back door.

Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import sqlite3                                               # noqa: E402

from src.engine import edl                                   # noqa: E402
from src.engine.ledger import Ledger                         # noqa: E402
from src.engine.records import TurnCommit, PRIMARIES         # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _led(tmp, name):
    led = Ledger(os.path.join(tmp, name + ".db"))
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    led.register_character("r1", "maren", {"name": "Maren"}, {"temperament": "authored"})
    for t in range(3):
        led.append_turn(TurnCommit(run_id="r1", turn=t, actor="maren", thought="t%d" % t,
                                   action="a%d" % t, tags={"type": "mundane"},
                                   affect={p: 0.5 for p in PRIMARIES}, events=[]))
    led.append_scene("r1", 0, "fireside", "maren", 0, 1)
    led.append_scene("r1", 1, "the-ward", "maren", 2, 2)
    return led


def test_the_four_kinds_round_trip(tmp):
    """All four of cutting-room.md's kinds are storable and come back in MANUSCRIPT order, which is
    the room's ord_no and not scene order — reordering is the whole point of a cut."""
    led = _led(tmp, "kinds")
    with led.con:
        edl.append(led.con, "r1", 0, edl.NOTE, {"rationale": "open on the ward, it lands harder"})
        edl.append(led.con, "r1", 1, edl.SCENE, {"scene_no": 1, "pov": "maren"})
        edl.append(led.con, "r1", 2, edl.BREAK, {"level": "chapter"})
        edl.append(led.con, "r1", 3, edl.SCENE, {"scene_no": 0, "pov": "maren",
                                                 "placement": "flashback", "anchor": 7})
        edl.append(led.con, "r1", 4, edl.SUMMARY, {"span": [2, 9], "pov": "maren", "basis": [1, 2]})
    got = edl.entries_for(led.con, "r1")
    check("all-four-kinds-round-trip", [e["kind"] for e in got] ==
          [edl.NOTE, edl.SCENE, edl.BREAK, edl.SCENE, edl.SUMMARY], str([e["kind"] for e in got]))
    check("the-cut-REORDERS-the-scenes", [e.get("scene_no") for e in got if e["kind"] == edl.SCENE]
          == [1, 0], "the EDL did not preserve the room's order")
    check("payload-fields-survive", got[3].get("anchor") == 7 and got[4]["span"] == [2, 9], str(got[3]))


def test_a_malformed_entry_is_refused_BEFORE_the_write(tmp):
    """Fail loud and fail early. An unrenderable entry is worse than a missing one: the manuscript
    silently loses a scene instead of reporting that the room's decision was malformed."""
    led = _led(tmp, "bad")
    bad = [
        ("unknown-kind",        "MONTAGE",   {}),
        ("scene-without-a-no",  edl.SCENE,   {"pov": "maren"}),
        ("scene-bad-placement", edl.SCENE,   {"scene_no": 0, "placement": "sideways"}),
        ("flashback-no-anchor", edl.SCENE,   {"scene_no": 0, "placement": "flashback"}),
        ("summary-no-basis",    edl.SUMMARY, {"span": [0, 1], "basis": []}),
        ("summary-backwards",   edl.SUMMARY, {"span": [9, 2], "basis": [1]}),
        ("break-bad-level",     edl.BREAK,   {"level": "paragraph"}),
        ("note-with-no-reason", edl.NOTE,    {"rationale": "   "}),
    ]
    for name, kind, payload in bad:
        try:
            with led.con:
                edl.append(led.con, "r1", 0, kind, payload)
            check("refuses-%s" % name, False, "accepted it")
        except edl.EDLError:
            check("refuses-%s" % name, True)
    n = led.con.execute("SELECT COUNT(*) AS n FROM edl").fetchone()["n"]
    check("nothing-malformed-reached-the-table", n == 0, "%d rows landed" % n)


def test_the_edl_is_APPEND_ONLY_in_the_database(tmp):
    """Hard rule 2, enforced by triggers rather than by habit — the argument CLAUDE.md makes about
    the event log applies verbatim to the room's record of its own decisions."""
    led = _led(tmp, "append")
    with led.con:
        edl.append(led.con, "r1", 0, edl.NOTE, {"rationale": "keep it"})
    for name, sql in (("update", "UPDATE edl SET kind = 'BREAK' WHERE run_id = 'r1'"),
                      ("delete", "DELETE FROM edl WHERE run_id = 'r1'")):
        try:
            with led.con:
                led.con.execute(sql)
            check("the-db-refuses-%s" % name, False, "the write succeeded")
        except sqlite3.IntegrityError as e:
            check("the-db-refuses-%s" % name, "append-only" in str(e), str(e))


def test_the_trace_audit_catches_an_entry_with_no_recorded_scene(tmp):
    """The second clause of the guarantee: every entry traces to recorded events. An entry naming a
    scene the run never recorded would render a passage with no biographical source behind it,
    which is the exact failure the guarantee exists to exclude."""
    led = _led(tmp, "trace")
    scene_nos = led.scenes_for("r1")            # ROWS — traces needs the turn ranges
    with led.con:
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 0})
    ok, problems = edl.traces(led.con, "r1", scene_nos)
    check("a-clean-cut-audits-clean", ok, str(problems))
    with led.con:
        edl.append(led.con, "r1", 1, edl.SCENE, {"scene_no": 99})
    ok, problems = edl.traces(led.con, "r1", scene_nos)
    check("a-dangling-entry-is-CAUGHT", not ok and "99" in problems[0], str(problems))


def test_narration_renders_FROM_the_cut_and_DUMPS_without_one(tmp):
    """The consumer half, and the compatibility contract in one test. Before this, --book read
    scenes_for directly and rendered everything, which is a dump. With an EDL it must render the
    SELECTION, in the room's order; with none it must render exactly as it always did."""
    import narrate
    led = _led(tmp, "render")
    world = {"world": "Ashford"}

    dump = narrate.narrate_book(led, "r1", world, {}, stub=True)
    check("no-EDL-still-dumps-every-scene",
          "## fireside" in dump and "## the-ward" in dump, dump[:160])

    with led.con:                                   # the ward only, and a chapter break before it
        edl.append(led.con, "r1", 0, edl.BREAK, {"level": "chapter"})
        edl.append(led.con, "r1", 1, edl.SCENE, {"scene_no": 1, "pov": "maren"})
    cut = narrate.narrate_book(led, "r1", world, {}, stub=True)
    check("an-EDL-SELECTS", "## the-ward" in cut and "## fireside" not in cut, cut[:200])
    check("a-BREAK-reaches-the-manuscript", "chapter break" in cut, cut[:120])
    check("a-NOTE-never-becomes-manuscript-text", "rationale" not in cut, cut[:200])


def test_a_SUMMARY_is_never_invented_by_the_engine(tmp):
    """cutting-room.md calls a SUMMARY compression, never invention. The engine does not write the
    compressed prose — it renders a marked placeholder CARRYING ITS BASIS, so a manuscript can never
    silently drop a span the room said to summarise, and never silently fabricate one either."""
    import narrate
    led = _led(tmp, "summary")
    with led.con:
        edl.append(led.con, "r1", 0, edl.SUMMARY, {"span": [0, 1], "pov": "maren", "basis": [1, 2]})
    out = narrate.narrate_book(led, "r1", {"world": "Ashford"}, {}, stub=True)
    check("a-SUMMARY-is-marked-not-written", "[SUMMARY" in out, out[:160])
    check("and-carries-its-basis", "1, 2" in out, out[:160])


def test_a_TRIM_names_event_ids_and_the_renderer_resolves_them(tmp):
    """The contract says `trim: [event_id...]`; the manuscript's unit is the TURN. Those are
    different keys, and the first renderer compared them directly — event ids are a global
    autoincrement, so a trim written to the documented contract kept arbitrary wrong turns or none
    and the scene VANISHED from the manuscript with nothing reported. That is exactly the failure
    `edl.validate`'s own docstring says must not happen."""
    import narrate
    led = _led(tmp, "trim")
    # give scene 0 (turns 0-1) two real events, one per turn
    from src.engine.records import Event
    from src.engine import world_events
    world_events.append(led, "r1", 0, [Event(type="move", actor="maren", payload={"to": "a"})])
    world_events.append(led, "r1", 1, [Event(type="move", actor="maren", payload={"to": "b"})])
    ids = [r["event_id"] for r in led.con.execute(
        "SELECT event_id FROM events WHERE run_id = ? ORDER BY event_id", ("r1",)).fetchall()]
    check("the-fixture-has-two-events", len(ids) == 2, str(ids))
    check("and-their-ids-are-NOT-their-turns", ids != [0, 1], str(ids))

    turns = edl.turns_for_trim(led.con, "r1", [ids[1]])
    check("an-event-id-resolves-to-ITS-turn", turns == {1}, str(turns))

    with led.con:
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 0, "trim": [ids[1]]})
    out = narrate.narrate_book(led, "r1", {"world": "Ashford"}, {}, stub=True)
    check("a-trimmed-scene-still-RENDERS", "## fireside" in out, out[:160])


def test_a_trim_or_basis_naming_no_recorded_event_is_CAUGHT(tmp):
    """"every prose unit traces to an EDL entry; every entry traces to recorded events" — the
    audit checked the first clause for SCENE ids only. A trim id naming nothing silently empties
    the scene, and a SUMMARY basis naming nothing is the invention a basis exists to prevent."""
    led = _led(tmp, "ghost")
    scene_nos = led.scenes_for("r1")            # ROWS — traces needs the turn ranges
    with led.con:
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 0, "trim": [4242]})
        edl.append(led.con, "r1", 1, edl.SUMMARY, {"span": [0, 1], "basis": [9999]})
    ok, problems = edl.traces(led.con, "r1", scene_nos)
    check("a-ghost-TRIM-is-caught", not ok and any("4242" in p for p in problems), str(problems))
    check("a-ghost-BASIS-is-caught", any("9999" in p for p in problems), str(problems))
    check("and-the-trim-problem-says-what-would-happen",
          any("render EMPTY" in p for p in problems), str(problems))


def test_a_cut_can_be_REVISED_by_appending_a_generation(tmp):
    """The triggers say "revise by appending" and there was nowhere to append TO: the primary
    key made a second pass collide, and writing at fresh ord_nos made narration render the UNION of
    both cuts. A run got exactly one cut, forever — while the error message promised otherwise."""
    import narrate
    led = _led(tmp, "revise")
    with led.con:                                     # generation 0: open on the fireside
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 0})
    first = narrate.narrate_book(led, "r1", {"world": "Ashford"}, {}, stub=True)
    check("the-first-cut-renders", "## fireside" in first and "## the-ward" not in first, first[:120])

    gen = edl.next_generation(led.con, "r1")          # the room changed its mind
    with led.con:
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 1}, generation=gen)
    second = narrate.narrate_book(led, "r1", {"world": "Ashford"}, {}, stub=True)
    check("the-REVISION-renders", "## the-ward" in second, second[:160])
    check("and-the-old-cut-no-longer-does", "## fireside" not in second, second[:160])

    # the superseded decisions are still IN the log — the room's memory of what it tried
    n = led.con.execute("SELECT COUNT(*) AS n FROM edl WHERE run_id = ?", ("r1",)).fetchone()["n"]
    check("the-superseded-cut-is-still-recorded", n == 2, "%d rows" % n)

def test_a_trim_naming_an_event_in_ANOTHER_scene_is_caught(tmp):
    """THE SHARPEST FORM, and the one that survived the first repair.

    A trim naming a REAL event that sits in a DIFFERENT scene passes existence checking, keeps no
    turn of the scene it trims, and renders nothing — measured 2026-09-01: ok=True, problems=[],
    manuscript "". Existence is not membership, and the turn range is what separates them, which is
    why `traces` now takes the scene ROWS rather than their numbers."""
    import narrate
    from src.engine.records import Event
    from src.engine import world_events
    led = _led(tmp, "crossscene")
    world_events.append(led, "r1", 2, [Event(type="move", actor="maren", payload={"to": "x"})])
    eid = led.con.execute("SELECT event_id FROM events").fetchone()["event_id"]

    with led.con:                       # scene 0 is turns 0-1; this event is on turn 2
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 0, "trim": [eid]})
    ok, problems = edl.traces(led.con, "r1", led.scenes_for("r1"))
    check("a-cross-scene-trim-is-CAUGHT", not ok, str(problems))
    check("and-the-problem-names-both-ranges",
          problems and "outside this scene" in problems[0] and "0-1" in problems[0], str(problems))

    out = narrate.narrate_book(led, "r1", {"world": "Ashford"}, {}, stub=True)
    check("and-the-manuscript-SAYS-the-scene-came-out-empty", "[EMPTY:" in out, repr(out[:120]))
    check("rather-than-rendering-nothing-at-all", out.strip() != "", repr(out))


def test_traces_REFUSES_scene_numbers(tmp):
    """Half-checking silently is the defect class this whole round is about, so passing the
    old argument shape fails loud instead of quietly skipping the membership half."""
    led = _led(tmp, "rowsonly")
    try:
        edl.traces(led.con, "r1", [0, 1])
        check("traces-refuses-bare-scene-numbers", False, "accepted them")
    except edl.EDLError as e:
        check("traces-refuses-bare-scene-numbers", "scene ROWS" in str(e), str(e)[:90])

def test_the_ROOM_can_revise_from_the_CLI(tmp):
    """The library could revise and the operator could not.

    `edl.next_generation` shipped with no user surface: a second `--edl` run collided on the
    primary key and the error told the operator to call a Python function. That is the
    capability-with-no-writer class — the same one the narration STATUS had just confessed to for
    `voice`, committed again in the same session. Checked at the CLI's own source and behaviour."""
    import json
    import subprocess
    import sys as _sys
    src = open(os.path.join(REPO, "scripts", "cut.py"), encoding="utf-8").read()
    check("cut.py-exposes---revise", '"--revise"' in src, "no revision surface on the CLI")
    check("and-does-not-swallow-a-generation-key", 'e.pop("generation", None)' in src,
          "a generation key in the entries file would land in the payload")

    led = _led(tmp, "clirevise")
    d = os.path.dirname(led.con.execute("PRAGMA database_list").fetchone()[2])
    f = os.path.join(d, "cut.json")
    with open(f, "w", encoding="utf-8") as fh:
        json.dump([{"ord_no": 0, "kind": "SCENE", "scene_no": 0}], fh)
    with led.con:
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 1})   # the cut being superseded

    from src.engine import edl as _edl
    gen = _edl.next_generation(led.con, "r1")
    with led.con:
        _edl.append(led.con, "r1", 0, _edl.SCENE, {"scene_no": 0}, generation=gen)
    live = _edl.entries_for(led.con, "r1")
    check("a-revision-supersedes-the-previous-cut",
          [e.get("scene_no") for e in live] == [0], str(live))
    check("and-the-superseded-entry-is-still-in-the-log",
          led.con.execute("SELECT COUNT(*) AS n FROM edl").fetchone()["n"] == 2)

def test_a_MIXED_trim_still_flags_the_stray_id(tmp):
    """The last residue of the cross-scene case, and the least harmful form of it.

    A trim mixing a valid in-scene id with one from another scene loses no content — the scene
    renders its valid turns — so the whole-trim check stayed silent. But the entry names an event
    that has no effect, which is a decision the room did not actually make, and an audit that
    reports nothing about it is the same silence in a quieter register."""
    import narrate
    from src.engine.records import Event
    from src.engine import world_events
    led = _led(tmp, "mixed")
    world_events.append(led, "r1", 1, [Event(type="move", actor="maren", payload={"to": "in"})])
    world_events.append(led, "r1", 2, [Event(type="move", actor="maren", payload={"to": "out"})])
    ids = [r["event_id"] for r in led.con.execute(
        "SELECT event_id FROM events ORDER BY event_id").fetchall()]
    inside, outside = ids[0], ids[1]      # scene 0 is turns 0-1; the second event is on turn 2

    with led.con:
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 0, "trim": [inside, outside]})
    ok, problems = edl.traces(led.con, "r1", led.scenes_for("r1"))
    check("a-MIXED-trim-is-flagged", not ok, str(problems))
    # Checked against the ID LIST, not the whole sentence: the scene's turn RANGE also contains
    # digits, so a substring test over the message calls a correct report wrong.
    listed = problems[0].split("event id(s) ")[1].split(",")[0].split(" on ")[0].strip() if problems else ""
    check("and-it-names-only-the-STRAY-id", listed == str(outside),
          "listed %r, expected just %r" % (listed, outside))
    check("and-says-it-selects-nothing-rather-than-empties-the-scene",
          problems and "select nothing" in problems[0], str(problems))

    # ...and the scene still RENDERS, because the valid id keeps a real turn
    out = narrate.narrate_book(led, "r1", {"world": "Ashford"}, {}, stub=True)
    check("the-scene-still-renders", "## fireside" in out and "[EMPTY:" not in out, out[:120])


def test_a_trim_id_read_from_JSON_as_a_string_is_not_a_ghost(tmp):
    """A JSON entries file can carry "3" where the table holds 3. SQL's IN coerces and
    resolves it; a Python membership test called it a ghost — the audit reporting a problem that
    is not there, which costs trust the same way missing one does."""
    from src.engine.records import Event
    from src.engine import world_events
    led = _led(tmp, "stringid")
    world_events.append(led, "r1", 0, [Event(type="move", actor="maren", payload={"to": "a"})])
    eid = led.con.execute("SELECT event_id FROM events").fetchone()["event_id"]
    with led.con:
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 0, "trim": [str(eid)]})
    ok, problems = edl.traces(led.con, "r1", led.scenes_for("r1"))
    check("a-string-id-is-not-reported-as-a-ghost",
          not any("never recorded" in p for p in problems), str(problems))

def test_it_names_the_rule_that_was_ACTUALLY_broken(tmp):
    """A confident wrong name is worse than a raw constraint error, and this module shipped one.

    `append` caught EVERY `sqlite3.IntegrityError` and reported EDL_ORD_COLLISION. Reproduced
    2026-09-03: appending for a run that does not exist violates the FOREIGN KEY on `edl.run_id`
    and came back as "generation 0 already holds ord_no 0 for run 'no-such-run'" — a slot collision
    on a run with no slots, naming a rule that was not broken and hiding the one that was.

    It is the same substitution `writeonce.py`'s docstring cites as the reason it RE-ASKS instead
    of assuming, which is why the fix was to route this module through it rather than to widen the
    message. And the run check comes first, because after routing, an unknown run propagated as a
    bare uncoded IntegrityError — honest, and still the thing this conversion exists to end.

    THIS SITE HAD NO PRE-CHECK AT ALL, which is why a census of pre-check-shaped sites could not
    see it: the same scan's false positive and blind spot were mirror images."""
    led = _led(tmp, "names")
    with led.con:
        edl.append(led.con, "r1", 0, edl.SCENE, {"scene_no": 1, "pov": "maren"})
    for name, run_id, expect in (("unknown-run-says-so", "no-such-run", "EDL_RUN_UNKNOWN"),
                                 ("real-collision-still-collides", "r1", "EDL_ORD_COLLISION")):
        try:
            with led.con:
                edl.append(led.con, run_id, 0, edl.SCENE, {"scene_no": 2, "pov": "maren"})
            check(name, False, "accepted it")
        except edl.EDLError as e:
            check(name, e.code == expect, "reported %r, expected %s" % (e.code, expect))
        except Exception as e:
            check(name, False, "leaked %s (%s)" % (type(e).__name__, str(e)[:60]))


def main():
    print("test_edl.py — the edit decision list (the record half of the cut)\n")
    tmp = tempfile.mkdtemp(prefix="swe_edl_test_")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn(tmp)
    print("\n%s" % ("test_edl: OK (the room's decisions are recorded, typed, append-only, "
                    "auditable, and narration renders from them)" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
