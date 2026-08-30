"""test_lint_scene.py — each scene-cfg check must fire on exactly what it claims to catch.

`docs/scene-authoring-rules.md` states six normative rules and, until 2026-08-24, nothing checked
any of them — the last authoring surface in the repo with no validator. `load_scene_cfg` validates
the SCHEMA (situation is a string, cast is a list of {id, drive}); it never sees the world, so a cfg
naming a character who does not exist parses cleanly and fails later, or worse runs and produces a
scene where the intended mechanism silently never fires.

The discipline this suite enforces on itself: every check gets a cfg that violates EXACTLY that
check and nothing else, so a passing test proves the check fires rather than proving the linter
runs. A guard verified only against a wholly-broken fixture is verified against nothing in
particular.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import lint_scene                                               # noqa: E402

_FAILS = []

# An invented two-person world — CLAUDE.md hard rule 1: fixtures are invented or they are not fixtures.
WORLD = {"world": "w",
         "people": [{"id": "wren", "what": "the ferrier"}, {"id": "coll", "what": "the boy"}],
         "locations": [{"id": "the-slip", "what": "the slipway"}],
         "laws": [{"act": "refuse_passage", "modality": "forbidden"}]}
CHARS = {"wren": {}, "coll": {}}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _cfg(**over):
    # A CLEAN cfg now carries props: rule 5 became enforceable when props started reaching the
    # actor, so a fixture without them is no longer "valid" — it is a scene with nothing in it to
    # pick up. This fixture was written before that and the control caught it, which is the control
    # doing its job.
    base = {"name": "t", "situation": "The tide is turning and the last boat is on the slip.",
            "subject": (None, None),
            "props": ["a coil of wet rope", "the tide-board", "a bailing tin"],
            "cast": [{"id": "wren", "drive": "get the boy off the slip before the water comes"},
                     {"id": "coll", "drive": "stay aboard and not be sent back up the road"}]}
    base.update(over)
    return base


def _fires(cfg, needle, where="errors"):
    e, w, _u = lint_scene.lint_cfg(cfg, WORLD, CHARS)
    pool = e if where == "errors" else w
    return any(needle in x for x in pool), (e, w)


def test_a_clean_cfg_is_clean():
    """The control. A linter that flags a correct cfg gets switched off."""
    print("\n[1] A VALID CFG PASSES — or the guard is noise")
    e, w, u = lint_scene.lint_cfg(_cfg(), WORLD, CHARS)
    check("no-errors", not e, "; ".join(e))
    check("no-warnings", not w, "; ".join(w))
    # TWO now, not three: rule 5 left this set when it gained an enforcer.
    check("but-it-still-declares-what-it-did-not-check", len(u) >= 2, u)


def test_each_error_fires_on_its_own_violation():
    print("\n[2] EACH CHECK FIRES ON EXACTLY ITS OWN DEFECT")

    ok, ctx = _fires(_cfg(cast=[{"id": "ghost", "drive": "a"}, {"id": "coll", "drive": "b"}]),
                     "not a character in this book")
    check("unknown-cast-id", ok, ctx)

    ok, ctx = _fires(_cfg(cast=[{"id": "wren", "drive": "a"}, {"id": "wren", "drive": "b"}]),
                     "more than once")
    check("duplicate-cast-seat", ok, ctx)

    ok, ctx = _fires(_cfg(subject=("nobody", "kin")), "resolves to nobody")
    check("unresolvable-subject", ok, ctx)

    ok, ctx = _fires(_cfg(location="elsewhere"), "not in world.locations")
    check("unknown-location", ok, ctx)

    ok, ctx = _fires(_cfg(act="not_a_law"), "keyed by no law")
    check("unkeyed-act", ok, ctx)

    sit = "The tide is turning and the last boat is on the slip."
    ok, ctx = _fires(_cfg(cast=[{"id": "wren", "drive": sit}, {"id": "coll", "drive": "b"}]),
                     "copy of the situation")
    check("drive-copied-from-situation", ok, ctx)


def test_heuristics_warn_and_never_block():
    """Rules 1 and 2 get lexical proxies. They must never be errors.

    A phrase list cannot decide whether a situation scripts a beat. A guard that BLOCKS correct
    work gets disabled, which is the failure mode the private-content sweep's negative control
    exists to prevent — so these advise.
    """
    print("\n[3] HEURISTICS ADVISE, THEY DO NOT BLOCK")
    scripted = _cfg(situation="The ferrier explains the toll to the boy at length.")
    e, w, _u = lint_scene.lint_cfg(scripted, WORLD, CHARS)
    check("scripting-marker-warns", any("rule 1" in x for x in w), w)
    check("and-is-NOT-an-error", not e, e)

    meta = _cfg(cast=[{"id": "wren", "drive": "introduce the world lore to the reader"},
                      {"id": "coll", "drive": "stay aboard"}])
    e2, w2, _u = lint_scene.lint_cfg(meta, WORLD, CHARS)
    check("meta-goal-warns", any("rule 2" in x for x in w2), w2)
    check("and-is-NOT-an-error", not e2, e2)

    aligned = _cfg(cast=[{"id": "wren", "drive": "same want"}, {"id": "coll", "drive": "same want"}])
    _e, w3, _u = lint_scene.lint_cfg(aligned, WORLD, CHARS)
    check("aligned-drives-warn-about-the-lull", any("lull" in x for x in w3), w3)


def test_it_says_what_it_cannot_check():
    """A clean run must not read as 'all six rules verified'."""
    print("\n[4] THE UNCHECKED SET IS DECLARED")
    _e, _w, u = lint_scene.lint_cfg(_cfg(), WORLD, CHARS)
    blob = " ".join(u)
    check("rule-4-declared-unchecked", "rule 4" in blob)
    check("rule-6-declared-unchecked", "rule 6" in blob)
    check("rule-5-is-no-longer-in-the-unchecked-set", "props" not in blob,
          "props now reach the actor as percepts, so rule 5 is enforced rather than declared")


def test_rule_5_is_enforced_now_that_props_reach_something():
    """The count is only a real constraint because the field is now read.

    Written in this order on purpose: the check did not exist while `props` was a field the engine
    ignored, because a linter enforcing a field nothing reads manufactures the very defect class
    this repo keeps finding. Props became percepts first; the check came second.
    """
    print("\n[5] RULE 5 — enforceable because props now reach the actor")
    # the base fixture now HAS props (rule 5 is enforced), so strip them to test the absence
    bare = _cfg()
    bare.pop("props", None)
    _e, w, _u = lint_scene.lint_cfg(bare, WORLD, CHARS)
    check("absent-props-warn", any("rule 5" in x for x in w), w)
    e2, _w, _u = lint_scene.lint_cfg(_cfg(props=["a rope", "a tin"]), WORLD, CHARS)
    check("two-props-is-an-error", any("3-5" in x for x in e2), e2)
    e3, _w, _u = lint_scene.lint_cfg(_cfg(props=["a"] * 6), WORLD, CHARS)
    check("six-props-is-an-error", any("3-5" in x for x in e3), e3)
    e4, w4, _u = lint_scene.lint_cfg(
        _cfg(props=["a coil of wet rope", "the salve tin", "a cracked lantern"]), WORLD, CHARS)
    check("three-good-props-is-clean", not e4 and not any("rule 5" in x for x in w4), (e4, w4))

    # the field must actually be read by the engine, or this check is decoration again
    from src.engine import gate
    slice_ = {"event": {"text": "x", "kind": "mundane"}, "props": ["a coil of wet rope"]}
    ps = gate.perception_scope(slice_, {"people": [], "locations": []}, {"perception": 0.5},
                               {"energy": 0.7}, {})
    check("and-the-engine-emits-a-prop-percept",
          any(str(p.get("ref", "")).startswith("prop.") for p in ps),
          "lint_scene would be enforcing a field nothing reads — the defect it refused to create")


def main():
    print("test_lint_scene.py — the scene-cfg validator")
    for t in (test_a_clean_cfg_is_clean, test_each_error_fires_on_its_own_violation,
              test_heuristics_warn_and_never_block, test_it_says_what_it_cannot_check,
              test_rule_5_is_enforced_now_that_props_reach_something):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
