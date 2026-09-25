#!/usr/bin/env python3
"""test_scene_slice.py — the assembler's request is a closed, typed record (gate slice-contract, 2026-09-25).

THE CONTRACTS PLAN, G1 (agreed with Symphony on the board, convo #4; the owner's "Go"): what a driver hands
`scene.assemble` each beat was documented as three keys while the scene driver sent twelve, and nothing refused a
key nobody declared - a misspelt one was accepted and read as its default. `src/engine/scene_slice.py` declares
every key; `of` is the one door both `scene.assemble` and `gate.perception_scope` pass through.

  [1] every declared key is accepted, and made the record's shape
  [2] an undeclared key - at the top, or inside the event - is refused naming it
  [3] a declared key of the wrong shape is refused naming the field
  [4] absent is not empty: `present` (untracked vs nobody) and `raised_by` (no run vs no readings)
  [5] both doors refuse alike, and the engine reads the slice only through the record
  [6] the record is frozen, and the door is idempotent

Script-style: check(), main(), exit code. Stdlib only.
"""
import ast
import copy
import dataclasses
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import scene_slice                                  # noqa: E402
from src.engine.gate import perception_scope                        # noqa: E402
from src.engine.records import RecordError                          # noqa: E402
from src.engine.scene import assemble                               # noqa: E402

FAILS = []
FULL = {"event": {"text": "Mira trims the wick.", "kind": "mundane", "target": "mira"},
        "recent": ["Ada: the wind is backing."], "location": "loc.lamp_room", "present": ["ada", "mira"],
        "props": ["the wick trimmer"], "target": "mira", "engaged": "ada", "raised_by": {"WARINESS": "ada"},
        "last_read_turn": {"WARINESS": 3}, "last_turn": 3, "tells_noticed": ["her hands shake"],
        "elsewhere": ["mira_young"]}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def refusal(raw, door=scene_slice.of):
    """-> (code, message) of the refusal, or (None, None) when the door accepts."""
    try:
        door(raw)
    except RecordError as e:
        return e.code, str(e)
    return None, None


def accepts():
    print("[1] every declared key is accepted")
    s = scene_slice.of(copy.deepcopy(FULL))
    check("the-full-slice-is-a-record", isinstance(s, scene_slice.SceneSlice))
    check("every-key-a-driver-sends-is-declared", set(FULL) == set(scene_slice.DECLARED), sorted(set(FULL) ^ set(scene_slice.DECLARED)))
    check("the-values-survive", (s.event, s.location, s.target, s.engaged, s.raised_by, s.last_read_turn, s.last_turn)
          == (FULL["event"], "loc.lamp_room", "mira", "ada", {"WARINESS": "ada"}, {"WARINESS": 3}, 3), s)
    check("lists-become-tuples", (s.recent, s.present, s.props, s.tells_noticed, s.elsewhere)
          == (("Ada: the wind is backing.",), ("ada", "mira"), ("the wick trimmer",), ("her hands shake",), ("mira_young",)))
    bare = scene_slice.of({"event": {"text": "x"}})
    check("only-the-event-text-is-required", (bare.event, bare.recent, bare.location, bare.present, bare.props, bare.target,
          bare.engaged, bare.raised_by, bare.last_read_turn, bare.last_turn, bare.tells_noticed, bare.elsewhere)
          == ({"text": "x", "kind": "mundane"}, (), None, None, (), None, "", None, {}, None, (), ()), bare)
    check("a-set-of-names-is-ordered", scene_slice.of({"event": {"text": "x"}, "present": {"mira", "ada"}}).present == ("ada", "mira"))


def unknown():
    print("[2] an undeclared key is refused naming it")
    code, msg = refusal(dict(FULL, presnt=["ada"]))
    check("a-misspelt-key-is-refused", code == "SCENE_SLICE_UNKNOWN_KEY" and "presnt" in msg, (code, msg))
    code, msg = refusal(dict(FULL, event=dict(FULL["event"], subject="mira")))
    check("...inside-the-event-too", code == "SCENE_SLICE_UNKNOWN_KEY" and "event.subject" in msg, (code, msg))
    check("the-refusal-names-what-is-declared", "tells_noticed" in (msg or "") or "target" in (msg or ""), msg)


def shapes():
    print("[3] a declared key of the wrong shape is refused naming the field")
    bad = {"recent": "one line", "location": 7, "present": "ada", "props": [3], "target": ["mira"], "engaged": None,
           "raised_by": {"WARINESS": 2}, "last_read_turn": {"WARINESS": "3"}, "last_turn": True,
           "tells_noticed": "a sign", "elsewhere": [None]}
    check("(every-declared-field-but-the-event-has-a-bad-value-here)",
          set(bad) == set(scene_slice.DECLARED) - {"event"}, sorted(set(scene_slice.DECLARED) - {"event"} - set(bad)))
    for key, value in sorted(bad.items()):
        code, msg = refusal(dict(FULL, **{key: value}))
        check("%s-of-the-wrong-shape" % key, code == "SCENE_SLICE_FIELD_TYPE" and key in (msg or ""), (code, msg))
    for label, raw, want in (("not-an-object", "a moment", "SCENE_SLICE_NOT_AN_OBJECT"),
                             ("no-event", {"recent": []}, "SCENE_SLICE_EVENT_MISSING"),
                             ("an-event-with-no-text", {"event": {"kind": "mundane"}}, "SCENE_SLICE_EVENT_TEXT_MISSING"),
                             ("event-text-not-a-string", {"event": {"text": 5}}, "SCENE_SLICE_FIELD_TYPE"),
                             ("event-target-not-a-string", {"event": {"text": "x", "target": 5}}, "SCENE_SLICE_FIELD_TYPE")):
        code, msg = refusal(raw)
        check(label, code == want, (code, msg))


def absent_is_not_empty():
    print("[4] absent is not empty")
    check("present-absent-is-untracked", scene_slice.of({"event": {"text": "x"}}).present is None)
    check("present-empty-is-nobody-here", scene_slice.of({"event": {"text": "x"}, "present": []}).present == ())
    check("raised_by-absent-is-no-run-behind-it", scene_slice.of({"event": {"text": "x"}}).raised_by is None)
    check("raised_by-empty-is-a-run-with-no-readings", scene_slice.of({"event": {"text": "x"}, "raised_by": {}}).raised_by == {})
    # and assembly keeps the difference: untracked presence records no witnesses, tracked presence records the room
    from test_scene import _char, _flat_affect, _world
    ch, w = _char(), _world()
    af, cond = _flat_affect(), dict(ch["current"]["condition"])
    un = assemble(copy.deepcopy(ch), w, {"event": {"text": "Joss is here", "kind": "mundane"}}, af, cond)
    tr = assemble(copy.deepcopy(ch), w, {"event": {"text": "Joss is here", "kind": "mundane"}, "present": []}, af, cond)
    check("untracked-presence-records-no-witnesses", un["manifest"].get("present") is None, un["manifest"].get("present"))
    check("tracked-presence-records-the-room", tr["manifest"].get("present") == [], tr["manifest"].get("present"))
    # ...and whom the mood came from: with no run behind the slice the sheet's targets stand in; a run whose log holds
    # no reading says no one raised it, and the sheet does not get to say otherwise (the fixture test_toward uses)
    from src.engine import heritable, toward
    from src.engine.records import PATHS
    rc = json.load(open(os.path.join(REPO, "characters", "ren-traveler.json"), encoding="utf-8"))
    rw = json.load(open(os.path.join(REPO, "world", "ashford-slice.json"), encoding="utf-8"))
    heritable.ensure_temperament(rc)
    rest = float(rc["baseline"]["temperament"]["GOODWILL"]["mean"])
    mood = {p: float(rc["baseline"]["temperament"][p]["mean"]) for p in PATHS}
    mood["GOODWILL"] = rest + 0.08
    toward.replay(rc, [("joss_apprentice", "GOODWILL", 0.02)])
    rc["current"]["targets"] = {"GOODWILL": "joss_apprentice"}      # the sheet says Joss raised it
    rc["baseline"].pop("catalog", None)
    base = {"event": {"text": "Joss is here", "kind": "mundane"}, "target": "joss_apprentice", "engaged": "joss_apprentice"}
    felt = lambda sl: assemble(copy.deepcopy(rc), rw, sl, dict(mood), rc["current"]["condition"])["volatile"]["state"]["effective"]["GOODWILL"]
    check("no-run-behind-it:-the-sheet's-targets-meet-the-mood-in-full", abs(felt(base) - mood["GOODWILL"]) < 1e-12, felt(base))
    check("a-run-with-no-readings:-no-one-raised-it,-met-halfway",
          abs(felt(dict(base, raised_by={})) - (mood["GOODWILL"] + rest) / 2.0) < 1e-12, felt(dict(base, raised_by={})))


def doors():
    print("[5] both doors refuse alike; the engine reads only the record")
    from test_scene import _char, _flat_affect, _world
    ch, w = _char(), _world()
    af, cond = _flat_affect(), dict(ch["current"]["condition"])
    for label, raw in (("a-misspelt-key", {"event": {"text": "x"}, "presnt": []}),
                       ("a-wrong-shape", {"event": {"text": "x"}, "present": "ada"})):
        a = refusal(raw, lambda r: assemble(copy.deepcopy(ch), w, r, af, cond))[0]
        p = refusal(raw, lambda r: perception_scope(r, w, ch["baseline"]["skills"], cond))[0]
        check("assembly-and-perception-refuse-%s-alike" % label, a == p and a is not None, (a, p))
    same = assemble(copy.deepcopy(ch), w, scene_slice.of({"event": {"text": "Joss is here", "kind": "mundane"}}), af, cond)
    dct = assemble(copy.deepcopy(ch), w, {"event": {"text": "Joss is here", "kind": "mundane"}}, af, cond)
    check("a-record-and-its-dict-assemble-the-same-packet", json.dumps(same, sort_keys=True, default=str)
          == json.dumps(dct, sort_keys=True, default=str))
    # NO DICT-STYLE READ OF THE SLICE LEFT IN THE ENGINE: a read of `scene_slice[...]` or `scene_slice.get(...)` is a
    # key taken around the door. Parsed, not grepped: a docstring naming it is not a read.
    leaks = []
    for path in sorted(glob.glob(os.path.join(REPO, "src", "engine", "*.py"))):
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "scene_slice":
                leaks.append("%s:%d subscript" % (os.path.basename(path), node.lineno))
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "scene_slice" and node.func.attr in ("get", "keys", "items", "values")):
                leaks.append("%s:%d .%s()" % (os.path.basename(path), node.lineno, node.func.attr))
            if (isinstance(node, ast.Compare) and any(isinstance(c, ast.Name) and c.id == "scene_slice" for c in node.comparators)):
                leaks.append("%s:%d `in scene_slice`" % (os.path.basename(path), node.lineno))
    check("no-read-of-the-slice-goes-around-the-door", not leaks, leaks)


def frozen():
    print("[6] frozen, and idempotent")
    s = scene_slice.of(copy.deepcopy(FULL))
    try:
        s.location = "elsewhere"
        check("the-record-cannot-be-reassigned", False, "assigned")
    except dataclasses.FrozenInstanceError:
        check("the-record-cannot-be-reassigned", True)
    check("the-door-passes-a-record-through-unchanged", scene_slice.of(s) is s)


def main():
    accepts()
    unknown()
    shapes()
    absent_is_not_empty()
    doors()
    frozen()
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
