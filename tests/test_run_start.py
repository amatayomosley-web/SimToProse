#!/usr/bin/env python3
"""test_run_start.py — a run refuses to start from files the engine would misread (gate run-start-refusal, 2026-09-25).

THE CONTRACTS PLAN, G4 (the owner's "Go"; agreed with Symphony on the board, convo #4: "RUN START refuses against the
required set given the book's systems, naming the field, before any spend"; "UNKNOWN KEYS ... An ERROR at run start").
Both drivers started a run from any file the loaders accepted: an undeclared key dropped silently, a retired field's
content ignored, a malformed scene subject turned into no one, a scene with no situation a traceback. Now
`contracts.require_at_start` reads the world, the characters who play and the scene file as written, and what
`contracts.refuses` stops the run before its chronicle is opened.

  [1] what refuses: an error, an undeclared key, a retired field to move or refused - never a pruned, unread or
      advised one
  [2] require_at_start: each refusal names its file and path; what does not refuse is counted in one line
  [3] scripts/scene.py: refused before the chronicle exists; a sheet nobody plays is not read; a resume re-checks
  [4] scripts/direct.py: the chair's one character, the same way
  [5] the operating guide says so

Script-style: check(), main(), exit code. Stdlib only. Every book here is invented (two keepers on a rock).
"""
import copy
import glob
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import contracts, contracts_sheet, heritable, systems   # noqa: E402
from src.engine.records import RecordError                                # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                          # noqa: E402

FAILS = []
WORLD = dict(WORLD_ENGINE, people=[{"id": "mira", "what": "the keeper"}, {"id": "ada", "what": "the relief keeper"}])
SCENE = {"name": "gale", "at": {"day": 1, "time": "21:00"}, "lasts": "1h",
         "situation": "The two keepers wait out the gale in the lamp room.",
         "cast": [{"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}]}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def sheet(**edits):
    s = copy.deepcopy(CHAR_ENGINE)
    s["current"]["relationships"] = {"ada": {"trust": 0.7, "affinity": 0.65, "respect": 0.6, "debt": 0.0}}
    for dotted, value in edits.items():
        node, *path, last = dotted.split("__")
        target = s[node]
        for k in path:
            target = target.setdefault(k, {})
        target[last] = value
    return s


def refusal(world=WORLD, sheets=None, scene=None, name="gale.json"):
    """-> the refusal's message, or None when the run may start."""
    try:
        contracts.require_at_start(world, {"mira": sheet()} if sheets is None else sheets, scene, name)
    except RecordError as e:
        return str(e) if e.code == "CONTRACT_RUN_REFUSED" else "WRONG CODE %s" % e.code
    return None


# ---------------------------------------------------------------------------------------------------------------------
def what_refuses():
    print("[1] what refuses")
    for sev, policy, want in (("error", "", True), ("unknown", "", True), ("retired", "move", True),
                              ("retired", "refuse", True), ("retired", "prune", False), ("unread", "", False),
                              ("advice", "", False)):
        f = {"severity": sev, "code": "X", "path": "p", "message": "m", "policy": policy}
        check("%s%s-%s" % (sev, "-" + policy if policy else "", "refuses" if want else "does-not"),
              contracts.refuses(f) is want)
    moved = sheet(baseline__drives__fears_wounds=[{"wound": "the wreck"}])
    got = [f for f in contracts.check(moved, contracts_sheet.SHEET, systems.defaults(), {"registered": ()})
           if f["path"] == "baseline.drives.fears_wounds"]
    check("a-retired-finding-carries-its-field's-policy", got and got[0].get("policy") == "move", got)


def at_start():
    print("[2] require_at_start")
    try:
        note = contracts.require_at_start(WORLD, {"mira": sheet(), "ada": sheet()}, copy.deepcopy(SCENE), "gale.json")
        ok = True
    except RecordError as e:
        note, ok = str(e), False
    check("the-fixture-book-starts", ok, note)
    # the fixture carries a pruned field (temperament variability, cut) and fields nothing reads: counted, not refused
    check("...and-what-it-does-not-refuse-is-counted-in-one-line",
          ok and note.startswith("contract: nothing refused;") and "retired" in note and "unread" in note
          and "\n" not in note, note)
    cases = (
        ("an-undeclared-key", {"mira": sheet(fixed__nmae="Mira")}, None, "mira: fixed.nmae is not declared"),
        ("...with-a-did-you-mean", {"mira": sheet(fixed__nmae="Mira")}, None, "did you mean 'name'"),
        ("a-retired-field-to-move", {"mira": sheet(baseline__drives__fears_wounds=[{"wound": "the wreck"}])}, None,
         "mira: baseline.drives.fears_wounds is RETIRED"),
        ("a-retired-field-refused", {"mira": sheet(**{"fixed__genotype__" + heritable.OLD_AXES[0]: 0.5})}, None,
         "mira: fixed.genotype.%s is RETIRED" % heritable.OLD_AXES[0]),
        ("a-required-field-absent", {"mira": _without(sheet(), "baseline", "skills")}, None,
         "mira: baseline.skills is required and absent"),
        ("a-field-of-the-wrong-shape", {"mira": sheet(current__location=7)}, None, "mira: current.location must be text"),
    )
    for label, sheets, _scene, want in cases:
        msg = refusal(sheets=sheets)
        check(label, msg and want in msg, msg)
    msg = refusal(world=dict(WORLD, systems={"bogus": True}))
    check("the-world's-own-error", msg and "world: systems" in msg and "SYSTEMS_UNKNOWN" in msg, msg)
    msg = refusal(world=["not", "a", "world"])
    check("a-world-that-is-not-an-object-is-refused-not-a-crash", msg and "world: the file" in msg, msg)
    for label, edit, want in (("a-subject-of-three", {"subject": ["mira", "ada", "keepers"]}, "gale.json: subject"),
                              ("a-pov-outside-the-cast", {"pov": "wren"}, "gale.json: pov"),
                              ("no-situation", {"situation": None}, "gale.json: situation is required")):
        sc = dict(copy.deepcopy(SCENE), **edit)
        if edit.get("situation", "") is None:
            del sc["situation"]
        msg = refusal(scene=sc)
        check("the-scene-file:-" + label, msg and want in msg, msg)
    two = sheet()
    two["baseline"]["drives"]["goals"] = [{"goal": "tend the lamp", "priorty": 0.4}, {"goal": "row out", "priorty": 0.6}]
    msg = refusal(sheets={"mira": two})
    check("the-same-finding-twice-is-one-line-counted", msg and msg.count("goals[].priorty") == 1 and "(x2)" in msg, msg)
    check("the-chair's-form:-no-scene-file-is-read", refusal(scene=None) is None)
    msg = refusal(sheets={"mira": sheet(fixed__nmae="Mira"), "ada": sheet(fixed__nmae="Ada")})
    check("every-file-that-stops-it-is-named-not-only-the-first",
          msg and "mira: fixed.nmae" in msg and "ada: fixed.nmae" in msg and "2 thing(s)" in msg, msg)


def _without(s, section, key):
    del s[section][key]
    return s


def linters():
    print("[2c] the linters' ERRORS are exactly what refuses the run (the second review)")
    import lint_book
    import lint_scene
    rep = lint_book.lint(WORLD, {"mira": sheet(fixed__nmae="Mira")})
    check("lint_book:-an-undeclared-key-is-an-error,-as-the-run-refuses-it", any("fixed.nmae" in e for e in rep["errors"]),
          rep)
    rep = lint_book.lint(WORLD, {"mira": sheet()})
    check("lint_book:-a-pruned-field-is-a-warning,-as-the-run-starts",
          not any("variability" in e for e in rep["errors"]) and any("variability" in w for w in rep["warnings"]), rep)
    try:
        rep = lint_book.lint(dict(WORLD, locations=True, people=3), {"mira": sheet()})
        ok = any("world.locations: must be a list" in e for e in rep["errors"])
    except Exception as e:                              # noqa: BLE001 - a crash is the failure this names
        ok, rep = False, "CRASH %r" % (e,)
    check("lint_book:-a-world-shape-the-run-refuses-by-name-is-reported,-not-a-crash", ok, rep)
    errs, warns, _u = lint_scene.lint_cfg(dict(copy.deepcopy(SCENE), subjet=["mira", None]), WORLD, {"mira": {}, "ada": {}})
    check("lint_scene:-an-undeclared-key-is-an-error", any("subjet" in x for x in errs), (errs, warns))
    try:
        lint_scene.lint_cfg(copy.deepcopy(SCENE), dict(WORLD, locations=True), {"mira": {}, "ada": {}})
        ok, why = True, ""
    except Exception as e:                              # noqa: BLE001
        ok, why = False, repr(e)
    check("lint_scene:-a-malformed-world-is-no-crash", ok, why)
    # the shapes the third review found still crashing the linters, though the run refuses each by name
    rels = sheet()
    rels["current"]["relationships"] = [{"ada": 0.5}]
    rels["current"]["location"] = ["lamp_room"]
    for label, fn in (
            ("lint_book:-a-person-whose-id-is-a-list", lambda: lint_book.lint(
                dict(WORLD, people=[{"id": ["mira"], "what": "x"}]), {"mira": sheet()})),
            ("lint_book:-a-tension-whose-cooling-is-a-list", lambda: lint_book.lint(
                dict(WORLD, tensions=[{"id": "t", "cooling": ["slow"], "interests": {"threat": 0.5},
                                       "watches": {"parties": ["mira"]}}]), {"mira": sheet()})),
            ("lint_book:-relationships-and-a-location-as-lists", lambda: lint_book.lint(WORLD, {"mira": rels, "ada": sheet()})),
            ("lint_scene:-props-as-a-number", lambda: lint_scene.lint_cfg(dict(copy.deepcopy(SCENE), props=3), WORLD,
                                                                         {"mira": {}, "ada": {}})),
            ("lint_book:-a-baseline-that-is-not-an-object", lambda: lint_book.lint(
                WORLD, {"mira": dict(sheet(), baseline="TODO")}))):
        try:
            fn()
            ok, why = True, ""
        except Exception as e:                          # noqa: BLE001
            ok, why = False, repr(e)
        check(label + "-is-no-crash", ok, why)


def _tension_world():
    """A world keeping one standing tension whose temperature is a severity WORD - the authoring form its module
    turns into a number as it reads it."""
    from src.engine import tensions
    w = copy.deepcopy(WORLD)
    w["tensions"] = [{"id": "the-lamp-oil", "temperature": "marked", "interests": {"threat": 0.6},
                      "watches": {"parties": ["mira", "ada"], "locations": ["lamp_room"]}}]
    tensions.from_world(copy.deepcopy(w))              # a valid seed, or this fixture is wrong, not the check
    return w


def reviewed():
    print("[2b] what the first review found, each held")
    import json as _json
    picks = sheet()
    picks["formative_picks"] = [{"profile": "fire_survival_acute", "weight": 1.0, "why": "the classification's reason"}]
    check("a-sheet-the-composition-pass-wrote-starts", refusal(sheets={"mira": picks}) is None,
          refusal(sheets={"mira": picks}))
    for label, edit in (("baseline.skills", ("baseline", "skills")), ("current.condition", ("current", "condition"))):
        s = sheet()
        s[edit[0]][edit[1]] = {}
        check("an-empty-%s-block-is-said-on-purpose-and-starts" % label, refusal(sheets={"mira": s}) is None,
              refusal(sheets={"mira": s}))
    blank = sheet()
    blank["baseline"]["skills"] = {}
    said = [f for f in contracts.check(blank, contracts_sheet.SHEET, systems.defaults(), {"registered": ()})
            if f["path"] == "baseline.skills"]
    check("...and-the-empty-skills-block-is-told-what-it-costs", said and said[0]["severity"] == "advice"
          and "exactly average" in said[0]["message"], said)
    bare = sheet()
    bare["current"] = {}
    msg = refusal(sheets={"mira": bare})
    check("...while-an-empty-current-still-lacks-what-it-must-carry-(one-finding)",
          msg and "mira: current is required and empty" in msg and "current.affect" not in msg, msg)
    mood = sheet()
    mood["current"]["affect"] = {}
    msg = refusal(sheets={"mira": mood})
    check("...and-an-empty-mood-is-one-finding-for-its-nine-paths",
          msg and "mira: current.affect is required and empty" in msg and "current.affect." not in msg, msg)
    goals = sheet()
    goals["baseline"]["drives"]["goals"][0].update(kind="terminal", view="self", serves="the lamp")
    check("the-goal-keys-the-blueprint-calls-inert-start", refusal(sheets={"mira": goals}) is None,
          refusal(sheets={"mira": goals}))
    w = _tension_world()
    before = _json.dumps(w, sort_keys=True)
    refusal(world=w)
    check("the-check-changes-nothing-it-is-handed-(a-tension's-word-stays-a-word)",
          _json.dumps(w, sort_keys=True) == before and w["tensions"][0]["temperature"] == "marked")
    msg = refusal(scene=dict(copy.deepcopy(SCENE), cast=SCENE["cast"] + [{"id": "mira", "drive": "again"}]))
    check("a-cast-naming-someone-twice-is-refused", msg and "gale.json: cast" in msg and "'mira' more than once" in msg, msg)
    held = sheet()
    held["current"]["attachments"] = {"loc.lamp_room": {"hold": 0.5, "sign": "+"}}
    msg = refusal(world=dict(WORLD, systems={"body": "yes"}), sheets={"mira": held})
    check("a-world-whose-systems-cannot-be-read-refuses-for-that-alone-and-says-what-it-checked-against",
          msg and "SYSTEMS_VALUE_NOT_BOOL" in msg and "ATTACH_ENTITY_UNREGISTERED" not in msg
          and "checked against the default systems" in msg, msg)
    scar = sheet()
    scar["baseline"]["wounds"] = [{"id": "w", "concept": "exile", "path": "DEFLATION", "intensity": 0.5, "source": "old"}]
    off = dict(WORLD, systems={"wounds": False})
    check("a-switched-off-system's-own-rules-are-not-applied-(a-hand-written-wound-source)",
          refusal(world=off, sheets={"mira": scar}) is None)
    msg = refusal(sheets={"mira": scar})
    check("...and-with-the-system-on-the-same-wound-is-refused", msg and "CONTRACT_WOUND_SOURCE" in msg, msg)
    # THE SHAPE STILL IS (the second review): the drivers stamp and fold every block before an off system's is emptied,
    # so what they would crash on is refused by name - a word intensity, a block of the wrong kind
    worded = sheet()
    worded["baseline"]["wounds"] = [{"id": "w", "concept": "exile", "path": "DEFLATION", "intensity": "severe"}]
    msg = refusal(world=off, sheets={"mira": worded})
    check("...but-a-wound-the-stamp-cannot-read-is-refused-even-with-wounds-off",
          msg and "mira: baseline.wounds[]" in msg and "intensity must be a number" in msg, msg)
    unrated = sheet()
    unrated["baseline"]["wounds"] = [{"id": "w", "concept": "exile", "path": "DEFLATION", "source": "old"}]
    check("...while-a-wound-with-no-intensity-is-read-by-nothing-there-and-starts",
          refusal(world=off, sheets={"mira": unrated}) is None, refusal(world=off, sheets={"mira": unrated}))
    stale = sheet()
    stale["current"]["condition"] = "tired"
    check("...and-a-stale-condition-block-in-a-book-without-the-system-starts-(nothing-reads-it-before-it-is-emptied)",
          refusal(world=dict(WORLD, systems={"condition": False}), sheets={"mira": stale}) is None,
          refusal(world=dict(WORLD, systems={"condition": False}), sheets={"mira": stale}))
    toward = sheet()
    toward["current"]["toward"] = {"ada": {"WARINESS": "high"}}
    msg = refusal(world=dict(WORLD, systems={"attitude": False}), sheets={"mira": toward})
    check("...and-an-attitude-the-resume-cannot-fold", msg and "mira: current.toward.ada.WARINESS must be a number" in msg, msg)
    mighty = sheet()
    mighty["baseline"]["body"] = {"strength": "mighty"}               # not one of the body module's words
    check("a-book-that-runs-no-body-does-not-hold-a-body-block-to-the-body-module's-words",
          refusal(sheets={"mira": mighty}) is None, refusal(sheets={"mira": mighty}))
    msg = refusal(world=dict(WORLD, systems={"condition_flow": True, "body": True}), sheets={"mira": mighty})
    check("...and-one-that-does,-does", msg and "mira: baseline.body" in msg and "(this book runs the body system)" in msg, msg)
    cat = sheet()
    cat["baseline"]["catalog"] = {"rows": [{"lever": "WARINESS", "op": "x", "magnitude": 1.4, "wound": "sickness@WARINESS",
                                            "when": {"percept": ["a cough"]}}]}
    check("a-catalog-row-naming-a-wound-is-not-cross-read-in-a-wounds-off-book-(the-run-empties-every-sheet's-alike)",
          refusal(world=off, sheets={"mira": cat}) is None, refusal(world=off, sheets={"mira": cat}))
    msg = refusal(sheets={"mira": cat})
    check("...and-is-with-wounds-on", msg and "CONTRACT_CATALOG_WOUND_UNKNOWN" in msg, msg)
    for label, where, value in (("scene-condition", "scene.condition", ""), ("world-systems", "world.systems", ""),
                                ("opening-dimensions", "scene.opening_tags", {"dimensions": ""}),
                                ("a-skill", "sheet.baseline.skills.perception", ""),
                                ("energy", "sheet.current.condition.energy", ""),
                                ("a-trait-mean", "sheet.baseline.traits.extraversion.mean", ""),
                                ("a-worth", "sheet.baseline.model.schwartz.security", ""),
                                ("a-genotype-cell", "sheet.fixed.genotype.WARINESS", ""),
                                ("a-whitespace-pov", "scene.pov", "   ")):
        world, s, scene = copy.deepcopy(WORLD), sheet(), copy.deepcopy(SCENE)
        target, *path = where.split(".")
        node = {"scene": scene, "world": world, "sheet": s}[target]
        for k in path[:-1]:
            node = node.setdefault(k, {})
        node[path[-1]] = value
        msg = refusal(world=world, sheets={"mira": s}, scene=scene)
        check("a-blank-where-its-reader-takes-no-blank-is-refused:-" + label, msg and "CONTRACT_RUN_REFUSED" in msg
              and ".".join(path) in msg, msg)
    # A RETIRED KEY STOPS THE RUN BY ITS PRESENCE (the third review): the engine refuses some on sight whatever they
    # hold, so "an empty one is only counted" let them through to a crash after the run row was written
    for label, dotted, value in (("fears_wounds-emptied", "baseline.drives.fears_wounds", []),
                                 ("an-old-primitive-in-the-mood-set-to-null", "current.affect.FEAR", None),
                                 ("a-genotype-rest-blanked", "fixed.genotype.WARINESS.rest", "")):
        s = sheet()
        node, *path, last = dotted.split(".")
        target = s[node]
        for k in path:
            target = target.setdefault(k, {})
        target[last] = value
        msg = refusal(sheets={"mira": s})
        check("an-emptied-retired-key-still-stops-the-run:-" + label, msg and dotted in msg and "RETIRED" in msg, msg)
    for label, catalog in (("blank", ""), ("rows-that-are-not-a-list", {"rows": "none"})):
        c = sheet()
        c["baseline"]["catalog"] = catalog
        msg = refusal(sheets={"mira": c})
        check("a-catalog-levers-cannot-read-is-refused:-" + label, msg and "mira: baseline.catalog" in msg, msg)
    for label, where in (("baseline.drives.goals", ("baseline", "drives", "goals")),
                         ("current.active_goals", ("current", "active_goals"))):
        g = sheet()
        node = g
        for k in where[:-1]:
            node = node[k]
        node[where[-1]] = ["tend the lamp"]
        msg = refusal(sheets={"mira": g})
        check("a-goal-written-as-a-bare-string-is-refused-(it-was-dropped-silently):-" + label,
              msg and label + "[] must be an object" in msg, msg)
    for label, edit in (("a-blank-subject", {"subject": ""}), ("blank-props", {"props": ""})):
        check("a-blank-the-loader-reads-as-absent-starts:-" + label,
              refusal(scene=dict(copy.deepcopy(SCENE), **edit)) is None, refusal(scene=dict(copy.deepcopy(SCENE), **edit)))
    spaced = sheet()
    spaced["fixed"]["genotype"]["STIRRING"]["hit"] = "  "
    check("a-blank-word-reads-as-its-default-and-starts", refusal(sheets={"mira": spaced}) is None,
          refusal(sheets={"mira": spaced}))
    cue = copy.deepcopy(WORLD)
    cue["lexicon"]["attribute_classes"]["lamp"].append("")
    msg = refusal(world=cue)
    check("an-empty-cue-word-is-refused-(it-is-found-in-every-event)",
          msg and "world: lexicon.attribute_classes.lamp[]" in msg, msg)
    # THE FOURTH REVIEW: a null ITEM is a bad item, not an absence; a wound's numbers wherever the fold reads them; a
    # blank scene name is kept as the label by the loader; [] is no one
    nulls = sheet()
    nulls["current"]["active_goals"] = [None]
    msg = refusal(sheets={"mira": nulls})
    check("a-null-item-is-a-bad-item-not-an-absence:-an-active-goal", msg and "current.active_goals[] must be an object" in msg, msg)
    nullcue = copy.deepcopy(WORLD)
    nullcue["lexicon"]["attribute_classes"]["lamp"].append(None)
    msg = refusal(world=nullcue)
    check("...a-cue-word", msg and "lexicon.attribute_classes.lamp[] must be text" in msg, msg)
    msg = refusal(scene=dict(copy.deepcopy(SCENE), props=["rope", None, "lamp"]))
    check("...a-prop-(the-loader-would-have-made-it-a-prop-named-None)", msg and "gale.json: props[] must be text" in msg, msg)
    for systems_decl in (None, {"wounds": False}):
        lasting = sheet()
        lasting["baseline"]["wounds"] = [{"id": "exile@DEFLATION", "concept": "exile", "path": "DEFLATION", "intensity": 0.5,
                                          "permanence": "lasting", "source": "profile:fixture-exile"}]
        msg = refusal(world=dict(WORLD, systems=systems_decl) if systems_decl else WORLD, sheets={"mira": lasting})
        check("a-word-permanence-is-refused-(the-fold-reads-it)%s" % ("-with-wounds-off" if systems_decl else ""),
              msg and "permanence must be a number" in msg, msg)
    msg = refusal(scene=dict(copy.deepcopy(SCENE), name=""))
    check("a-blank-scene-name-is-refused-(the-loader-keeps-it-as-the-label)", msg and "gale.json: name" in msg, msg)
    check("an-empty-subject-list-is-no-one-and-starts", refusal(scene=dict(copy.deepcopy(SCENE), subject=[])) is None)
    bare_flow = sheet()
    bare_flow["current"]["condition"] = {}
    msg = refusal(world=dict(WORLD, systems={"condition_flow": True}), sheets={"mira": bare_flow})
    check("an-empty-block-that-must-carry-keys-names-the-system-that-asks-for-them",
          msg and "current.condition is required and empty - it must carry energy, allostatic_load (this book runs the "
          "condition_flow system)" in msg, msg)
    msg = refusal(world=dict(WORLD, locations=True), sheets={"mira": held})
    check("a-world-whose-places-cannot-be-read-checks-no-hold-against-a-register-it-could-not-build",
          msg and "world: locations must be a list" in msg and "ATTACH_ENTITY_UNREGISTERED" not in msg, msg)
    for label, world, scene, want in (
            ("dimensions-given-as-a-list", WORLD, dict(copy.deepcopy(SCENE), opening_tags={"dimensions": ["threat"]}),
             "must be an object of the seven dimensions"),
            ("a-cast-that-is-not-a-list", WORLD, dict(copy.deepcopy(SCENE), cast=2, pov="mira"), "gale.json: cast must be a list"),
            ("locations-that-are-not-a-list", dict(WORLD, locations=True), None, "world: locations must be a list"),
            ("attribute-classes-that-are-not-a-map", dict(WORLD, lexicon={"attribute_classes": 3, "subtle_cue_classes": ["x"]}),
             None, "world: lexicon.attribute_classes must be an object")):
        try:
            msg = refusal(world=world, scene=scene)
        except Exception as e:                          # noqa: BLE001 - a crash is the failure this names
            msg = "CRASH %s: %s" % (type(e).__name__, e)
        check("a-malformed-shape-is-refused-by-name-not-a-crash:-" + label, msg and want in msg
              and "not the shape its reader takes" not in msg, msg)       # its own words, not the catch-all's
    check("a-whitespace-only-situation-is-absent", "gale.json: situation is required" in
          (refusal(scene=dict(copy.deepcopy(SCENE), situation="   ")) or ""))
    check("a-blank-pov-voice-or-knowledge-is-the-default,-not-a-refusal",
          refusal(scene=dict(copy.deepcopy(SCENE), pov="", voice="", knowledge="")) is None)
    check("a-relation-word-with-a-stray-space-reads-as-the-word",
          refusal(scene=dict(copy.deepcopy(SCENE), attachments=[{"char": "mira", "entity": "loc.lamp_room",
                                                                  "relation": "post "}])) is None)
    def walker(value, whole, ctx):                       # a reader that cannot walk what it is handed
        raise TypeError("'int' object is not iterable")
    got = contracts.check({"x": 3}, (contracts.Field("x", "any", check=walker),))
    check("a-hook-that-cannot-walk-its-value-is-a-named-error-never-a-crash",
          len(got) == 1 and got[0]["severity"] == "error" and "not the shape its reader takes (TypeError" in got[0]["message"], got)
    half = sheet()
    half["current"]["condition"] = {"energy": 0.8}
    msg = refusal(world=dict(WORLD, systems={"condition_flow": True}), sheets={"mira": half})
    check("a-field-required-while-a-system-runs-is-demanded-then",
          msg and "mira: current.condition.allostatic_load is required (this book runs the condition_flow system)" in msg, msg)
    check("...and-not-while-it-is-off", refusal(sheets={"mira": half}) is None, refusal(sheets={"mira": half}))
    msg = refusal(world=["not", "a", "world"])
    check("a-file-level-refusal-reads-once", msg and "world: the file's engine block must be an object" in msg
          and "the file the file" not in msg, msg)
    note = contracts.require_at_start(WORLD, {"mira": sheet()}, copy.deepcopy(SCENE), "gale.json")
    check("the-count-line-names-both-linters", "lint_book.py" in note and "lint_scene.py" in note, note)


# ---------------------------------------------------------------------------------------------------------------------
def _note_path(book, name):
    return os.path.join(book, "characters", "%s.md" % name)


def _edit_sheet(book, name, fn):
    """Rewrite one character note's engine block through `fn`."""
    p = _note_path(book, name)
    text = open(p, encoding="utf-8").read()
    head, body = text.split("```json\n", 1)
    block, tail = body.split("\n```", 1)
    eng = json.loads(block)
    fn(eng)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(head + "```json\n" + json.dumps(eng, indent=1) + "\n```" + tail)


def _book(tmp):
    from test_systems import _book as build
    book = build(tmp)
    with open(_note_path(book, "Wren"), "w", encoding="utf-8") as fh:     # a third keeper, in no scene here
        eng = copy.deepcopy(CHAR_ENGINE)
        eng["fixed"]["name"] = "Wren"
        fh.write("---\ntype: character\nid: Wren\n---\n# Wren\n\n```json\n%s\n```\n" % json.dumps(eng, indent=1))
    return book


def _scene_file(tmp, **edit):
    p = os.path.join(tmp, "gale-%d.json" % len(glob.glob(os.path.join(tmp, "gale-*.json"))))
    body = dict(copy.deepcopy(SCENE), **edit)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(body, fh)
    return p


def _scene(book, cfg, *extra):
    r = subprocess.run([sys.executable, os.path.join("scripts", "scene.py"), "--book", book, "--scene", cfg, "--stub",
                        "--budget", "2", "--no-keeper"] + list(extra), cwd=REPO, capture_output=True, text=True, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _dbs(book):
    return glob.glob(os.path.join(book, "runs", "*.db"))


def _counts(db):
    con = sqlite3.connect(db)
    out = {t: con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for (t,) in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    out["_status"] = con.execute("SELECT status FROM runs").fetchall()
    con.close()
    return out


def scene_driver():
    print("[3] scripts/scene.py")
    tmp = tempfile.mkdtemp(prefix="run_start_")
    book = _book(os.path.join(tmp, "clean"))
    def _wren(e):                                                       # a sheet nobody here plays, and malformed
        e["fixed"]["nmae"] = "Wren"
        e["baseline"]["wounds"] = [{"concept": "exile", "path": "DEFLATION", "intensity": "severe"}]
        e["current"]["toward"] = ["ada"]
    _edit_sheet(book, "Wren", _wren)
    with open(_note_path(book, "Oona"), "w", encoding="utf-8") as fh:        # a fourth, in no scene, sections unwritten
        fh.write("---\ntype: character\nid: Oona\n---\n# Oona\n\n```json\n%s\n```\n"
                 % json.dumps({"fixed": "TODO", "baseline": "TODO", "current": "TODO"}))
    rc, out = _scene(book, _scene_file(tmp))
    # the run starts only if Wren's sheet is not checked (an undeclared key) and the stamp every sheet gets reads
    # his malformed blocks without a crash (a word intensity, an attitude that is a list)
    check("control-the-fixture-book-runs-reading-only-its-cast", rc == 0 and bool(_dbs(book)) and "Traceback" not in out,
          out[-600:])
    check("...printing-one-line-for-what-it-did-not-refuse", "contract: nothing refused;" in out, out[:600])
    db = _dbs(book)[0] if _dbs(book) else None

    for label, edit_sheet, scene_edit, want in (
            ("a-cast-sheet-with-an-undeclared-key", lambda e: e["fixed"].update(nmae="Mira"), {}, "mira: fixed.nmae"),
            ("a-cast-sheet-still-carrying-fears_wounds",
             lambda e: e["baseline"]["drives"].update(fears_wounds=[{"wound": "the wreck"}]), {},
             "mira: baseline.drives.fears_wounds is RETIRED"),
            ("a-scene-subject-of-three", None, {"subject": ["mira", "ada", "keepers"]}, "{file}: subject"),
            ("a-scene-with-no-situation", None, {"situation": ""}, "{file}: situation is required"),
            ("a-whitespace-only-situation", None, {"situation": "   "}, "{file}: situation is required"),
            ("a-cast-naming-someone-twice", None, {"cast": SCENE["cast"] + [{"id": "ada", "drive": "again"}]},
             "{file}: cast")):
        b = _book(os.path.join(tmp, label))
        if edit_sheet:
            _edit_sheet(b, "Mira", edit_sheet)
        cfg = _scene_file(tmp, **scene_edit)
        if scene_edit.get("situation") == "":
            body = json.load(open(cfg, encoding="utf-8"))
            del body["situation"]
            json.dump(body, open(cfg, "w", encoding="utf-8"))
        rc, out = _scene(b, cfg)
        want = want.format(file=os.path.basename(cfg))                   # the refusal names the file itself
        check(label + ":-refused-by-name", rc != 0 and "CONTRACT_RUN_REFUSED" in out and want in out, out[-600:])
        check(label + ":-no-chronicle-was-opened", not _dbs(b), _dbs(b))
        check(label + ":-no-traceback", "Traceback" not in out, out[-400:])
    # WHAT SPANS FILES, refused before the chronicle too: a cast id no character carries, a hold for a stranger
    for label, scene_edit, want in (
            ("a-cast-id-that-is-no-character-of-the-book", {"cast": [{"id": "mira", "drive": "x"}, {"id": "tomas", "drive": "y"}]},
             "scene cast 'tomas' is not in this book"),
            ("a-director's-hold-for-someone-not-in-the-book",
             {"attachments": [{"char": "tomas", "entity": "loc.lamp_room", "relation": "post"}]}, "declares a hold for 'tomas'")):
        b = _book(os.path.join(tmp, label))
        rc, out = _scene(b, _scene_file(tmp, **scene_edit))
        check(label + ":-refused-before-the-chronicle-is-opened", rc != 0 and want in out and not _dbs(b)
              and "Traceback" not in out, (_dbs(b), out[-400:]))
    b = _book(os.path.join(tmp, "not-json"))
    broken = os.path.join(tmp, "broken.json")
    with open(broken, "w", encoding="utf-8") as fh:
        fh.write('{"name": "gale", "situation": ')
    rc, out = _scene(b, broken)
    check("a-scene-file-that-is-not-JSON-is-refused-by-name-not-a-traceback",
          rc != 0 and "cannot be read as JSON" in out and "Traceback" not in out and not _dbs(b), out[-400:])

    if db:
        before = _counts(db)
        run_id = sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0]
        _edit_sheet(book, "Ada", lambda e: e["fixed"].update(nmae="Ada"))
        rc, out = _scene(book, _scene_file(tmp, at={"day": 1, "time": "23:00"}), "--resume", run_id)
        check("a-resume-is-checked-again", rc != 0 and "ada: fixed.nmae" in out, out[-600:])
        check("...and-writes-nothing-to-the-chronicle-it-resumes", _counts(db) == before, (before, _counts(db)))


def driver_guards():
    print("[3b] run_scene's own guards stand behind the check, for a caller that hands it a sheet directly")
    import scene
    from src.engine.ledger import Ledger
    from src.engine.vault import load_book
    from test_systems import _book as build
    tmp = tempfile.mkdtemp(prefix="run_start_guard_")
    world, chars = load_book(build(tmp, {"condition_flow": True, "body": True}))
    chars["mira"]["baseline"]["body"] = {"strength": "strong"}          # ada carries none
    led = Ledger(os.path.join(tmp, "guard.db"))
    led.create_run("guard-run", {"catalog_version": 1})
    cfg = dict(copy.deepcopy(SCENE), at_minutes=21 * 60.0, lasts_minutes=60.0, subject=(None, None), props=[],
               attachments=[], opening_tags={"type": "mundane", "dimensions": {}, "durability": "transient"})
    try:
        scene.run_scene(world, chars, cfg, led, "guard-run", 0, "fake/model", True, 1)
        got = None
    except SystemExit as e:
        got = str(e)
    check("run_scene-refuses-a-sheet-with-no-strength-itself-(the-body-guard-is-not-dead-code)",
          got and "BODY_STRENGTH_MISSING" in got, got)


def chair_driver():
    print("[4] scripts/direct.py")
    tmp = tempfile.mkdtemp(prefix="run_start_chair_")

    def chair(book):
        r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira",
                            "--stub"], input="quit\n", cwd=REPO, capture_output=True, text=True, timeout=600)
        return r.returncode, (r.stdout or "") + (r.stderr or "")

    book = _book(os.path.join(tmp, "clean"))
    _edit_sheet(book, "Ada", lambda e: e["fixed"].update(nmae="Ada"))       # not the one the chair plays
    rc, out = chair(book)
    # Ada's sheet carries an undeclared key: the chair starts only if it reads no sheet but the one it plays
    check("control-the-chair-starts-reading-only-its-own-character", rc == 0 and bool(_dbs(book)), out[-600:])
    check("...and-counts-what-it-did-not-refuse", "contract: nothing refused;" in out, out[:600])
    bad = _book(os.path.join(tmp, "bad"))
    _edit_sheet(bad, "Mira", lambda e: e["fixed"].update(nmae="Mira"))
    rc, out = chair(bad)
    check("the-chair's-character-with-an-undeclared-key-is-refused", rc != 0 and "mira: fixed.nmae" in out, out[-600:])
    check("...before-its-chronicle-is-opened", not _dbs(bad), _dbs(bad))
    worded = _book(os.path.join(tmp, "worded"))
    _edit_sheet(worded, "Mira", lambda e: e["baseline"].update(
        wounds=[{"id": "exile@DEFLATION", "concept": "exile", "path": "DEFLATION", "intensity": "severe",
                 "source": "profile:fixture-exile"}]))
    rc, out = chair(worded)
    check("a-wound-the-stamp-cannot-read-is-refused-by-name-in-the-chair-too-(its-stamp-comes-after-the-check)",
          rc != 0 and "CONTRACT_RUN_REFUSED" in out and "Traceback" not in out and not _dbs(worded), out[-600:])


def docs():
    print("[5] the operating guide")
    text = open(os.path.join(REPO, "docs", "guide-operating.md"), encoding="utf-8").read()
    check("guide-operating-says-a-run-refuses-at-its-start", "CONTRACT_RUN_REFUSED" in text)
    # the blueprint's copy-out form and worked example were keyed by the retired eight, so a sheet built from them
    # was refused at its run's start (the first review, finding 4)
    from src.engine.records import RETIRED_PRIMITIVES
    bp = open(os.path.join(REPO, "docs", "authoring", "BLUEPRINT-character.md"), encoding="utf-8").read()
    keyed = [p for p in RETIRED_PRIMITIVES if '"%s":' % p in bp]
    check("the-character-blueprint's-forms-key-the-mood-by-the-nine-paths", not keyed, keyed)


def main():
    what_refuses()
    at_start()
    reviewed()
    linters()
    scene_driver()
    driver_guards()
    chair_driver()
    docs()
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
