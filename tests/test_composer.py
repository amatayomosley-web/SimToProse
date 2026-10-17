#!/usr/bin/env python3
"""test_composer.py — the gate between a composer and an actor.

WHY A GATE AT ALL. The composer is an LLM sitting between the deterministic assembler and the actor.
Everything upstream of it is checkable; it is not. So what leaves it is verified rather than trusted,
and every refusal asserted here is something the composer is STRUCTURALLY able to get wrong — not a
hypothetical, but a mistake the shape of the task invites.

THE FOUR IT CANNOT BE ALLOWED TO DO:

  1. SELECT A RUNG THE ENGINE DID NOT PRODUCE. The owner's ruling, 2026-09-06: the composer selects
     WHICH emotion, never the rung. A character mid-story at rung 4 can only be played at 4 whatever
     the scene wants. A composer that could raise the rung would be writing state, which is the
     assembler's job and nobody else's.
  2. SELECT A PATH THE CHARACTER HAS NOT.
  3. NAME THE EMOTION IN ITS OWN PROSE. Measured 2026-09-07 across nine draws in three label
     conditions with byte-identical text beneath: the label is INERT as direction — the arm labelled
     `annoyance` over violent text scored HIGHER than the arm labelled `fury`. A name in the
     delivered text buys nothing and risks a reader weighting the word over the paragraph.
  4. NAME AN ACT. The composer says what the beat is about; what the character DOES belongs to the
     actor, which holds who is present and what a discharge would cost.

AND ONE STRUCTURAL GUARANTEE, asserted because it is easy to lose in a refactor: the composer is
never handed the block text. It selects by path, rung and name, and `direction_for` attaches the
blocks afterwards from the engine. "Reads the packet, never edits it" is then a property of what it
was given rather than an instruction it might disobey.

WHAT THIS CANNOT TEST YET, stated so a green run is not read as more than it is: with one path built
there is nothing to choose BETWEEN. The priority ordering that justifies the composer existing —
measured, an actor given competing states with no primary named resolves them in SEQUENCE, the first
draining away as the second replaces it — is exercised here only against synthetic rows.

Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import composer as C                                            # noqa: E402
from src.engine import rungs                                    # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  - " + detail) if (detail and not cond) else ""))


def rows_at(*pairs):
    """[(path, rung)] -> selectable rows, built through the real resolver so the blocks are real."""
    return [{"path": p, "rung": r, "name": rungs.rung_at(p, 0.0)[1] if False else
             [nm for i, (_, _, nm) in enumerate(__import__(
                 "src.engine.rung_blocks", fromlist=["BANDS"]).BANDS[p], start=1) if i == r][0],
             "block": rungs.block_for(p, r)} for p, r in pairs]


def refuses(selection, rows, label, needle=""):
    try:
        C.verify(selection, rows)
        check(label, False, "it was ACCEPTED")
    except C.ComposerError as e:
        check(label, (needle in str(e)) if needle else True, str(e)[:80])


def test_the_composer_never_holds_the_block():
    """The structural guarantee. If the block text ever reaches the composer, it can paraphrase it,
    and 'never edits the packet' stops being a property and becomes a request."""
    print("\n[1] THE COMPOSER IS NOT HANDED THE STATE TEXT")
    rows = rows_at(("DISPLEASURE", 3))
    msgs = C.compose_prompt(rows, "the crew is watching")
    whole = " ".join(m["content"] for m in msgs)
    check("the-block-text-is-absent", rows[0]["block"][:60] not in whole)
    check("the-rung-and-name-are-present", "rung  3" in whole and "chafing" in whole)
    check("no-float-appears", not any(t in whole for t in ("0.18", "0.25", "0.31")))
    check("the-brief-reaches-it", "the crew is watching" in whole)


def test_it_may_not_move_the_rung():
    """The ruling this whole seam rests on: the composer selects the emotion, never its height."""
    print("\n[2] IT MAY NOT SELECT A RUNG THE ENGINE DID NOT PRODUCE")
    rows = rows_at(("DISPLEASURE", 3))
    refuses({"selected": [{"path": "DISPLEASURE", "rung": 9, "primary": True}]}, rows,
            "a-higher-rung-is-refused", "never the rung")
    refuses({"selected": [{"path": "DISPLEASURE", "rung": 1, "primary": True}]}, rows,
            "a-lower-rung-is-refused", "never the rung")
    refuses({"selected": [{"path": "WARINESS", "rung": 3, "primary": True}]}, rows,
            "a-path-the-character-lacks-is-refused", "not a path")


def test_it_may_not_name_the_emotion_or_an_act():
    print("\n[3] ITS OWN PROSE MAY NAME NEITHER THE EMOTION NOR AN ACT")
    rows = rows_at(("DISPLEASURE", 3))
    ok = {"selected": [{"path": "DISPLEASURE", "rung": 3, "primary": True}]}
    for text, label in (("he is chafing at the delay", "a-rung-name-is-refused"),
                        ("this is displeasure over the count", "a-path-name-is-refused"),
                        ("his rage is up", "a-primitive-name-is-refused")):
        refuses(dict(ok, about=text), rows, label, "names")
    refuses(dict(ok, about="the count, and he will confront the foreman"), rows,
            "a-named-act-is-refused", "names an act")
    got = C.verify(dict(ok, about="the count, and who signed for it"), rows)
    check("clean-direction-is-accepted", got is not None)


def test_one_primary_when_more_than_one_plays():
    """Measured: without a named primary the actor resolves competing states IN SEQUENCE — the first
    drains and the second replaces it, which is the one outcome the design exists to prevent."""
    print("\n[4] EXACTLY ONE PRIMARY WHEN MORE THAN ONE IS SELECTED")
    rows = rows_at(("DISPLEASURE", 3))
    synthetic = rows + [{"path": "SECOND", "rung": 2, "name": "second", "block": "SECOND BLOCK"}]
    two = [{"path": "DISPLEASURE", "rung": 3}, {"path": "SECOND", "rung": 2}]
    refuses({"selected": two}, synthetic, "no-primary-is-refused", "primary")
    refuses({"selected": [dict(t, primary=True) for t in two]}, synthetic,
            "two-primaries-are-refused", "primary")
    check("one-primary-is-accepted",
          C.verify({"selected": [dict(two[0], primary=True), two[1]]}, synthetic) is not None)
    check("a-single-selection-needs-no-primary",
          C.verify({"selected": [{"path": "DISPLEASURE", "rung": 3}]}, rows) is not None)
    refuses({"selected": [dict(t, primary=(i == 0)) for i, t in enumerate(two * 2)]}, synthetic,
            "more-than-three-is-refused", "at most three")


def test_the_direction_puts_the_primary_first_and_carries_real_blocks():
    print("\n[5] THE DIRECTION CARRIES ENGINE BLOCKS, PRIMARY FIRST")
    rows = rows_at(("DISPLEASURE", 3))
    synthetic = rows + [{"path": "SECOND", "rung": 2, "name": "second", "block": "SECOND BLOCK"}]
    sel = C.verify({"selected": [{"path": "SECOND", "rung": 2},
                                 {"path": "DISPLEASURE", "rung": 3, "primary": True}],
                    "about": "the count, and who signed for it"}, synthetic)
    text = C.direction_for(synthetic, sel)
    check("the-primary-block-comes-first",
          text.index(rows[0]["block"][:40]) < text.index("SECOND BLOCK"), "order is wrong")
    check("the-block-is-the-engines-verbatim", rows[0]["block"] in text)
    check("the-about-line-survives", "who signed for it" in text)
    check("the-direction-names-no-rung", "chafing" not in text.lower())


def test_nothing_selectable_is_refused_not_silently_empty():
    print("\n[6] AN EMPTY SELECTABLE SET RAISES RATHER THAN BUILDING A PROMPT ABOUT NOTHING")
    try:
        C.compose_prompt([], "a brief")
        check("empty-rows-refused", False, "it built a prompt")
    except C.ComposerError:
        check("empty-rows-refused", True)


def test_the_descent_flag_reaches_block_for():
    """Gate 3 wiring (2026-09-15): `selectable(affect, descending)` hands the per-path flag to
    `rungs.block_for`, which swaps to the descent block only above the pivot. DESCENT_BLOCKS is
    still empty in the tree, so the swap is proven against a planted block and the one-argument form
    is proven byte-identical to before."""
    print("\n[9] THE DESCENT FLAG REACHES block_for")
    from src.engine.rung_blocks import BANDS, BLOCKS
    piv = rungs.PIVOTS["DISPLEASURE"]
    above = {"DISPLEASURE": BANDS["DISPLEASURE"][piv][0] + 1e-6}     # one rung above the pivot
    at = {"DISPLEASURE": BANDS["DISPLEASURE"][piv - 1][0] + 1e-6}    # the pivot rung itself
    planted = "PLANTED DESCENT TEXT — the way down is not the climb reversed"
    saved = rungs.DESCENT_BLOCKS
    rungs.DESCENT_BLOCKS = {"DISPLEASURE": {piv + 1: planted, piv: planted}}
    try:
        climb = C.selectable(above)[0]["block"]
        down = C.selectable(above, descending={"DISPLEASURE": True})[0]["block"]
        check("above-the-pivot-descending-serves-the-descent-block", down == planted, down[:60])
        check("above-the-pivot-not-descending-serves-the-climb", climb != planted and climb == BLOCKS["DISPLEASURE"][piv + 1])
        check("one-argument-form-is-unchanged", C.selectable(above) == C.selectable(above, descending=None))
        check("false-flag-is-the-climb", C.selectable(above, descending={"DISPLEASURE": False})[0]["block"] == climb)
        check("at-the-pivot-never-swaps", C.selectable(at, descending={"DISPLEASURE": True})[0]["block"] == BLOCKS["DISPLEASURE"][piv])
        check("a-flag-for-another-path-does-not-leak", C.selectable(above, descending={"WARINESS": True})[0]["block"] == climb)
    finally:
        rungs.DESCENT_BLOCKS = saved


def test_identical_rows_reuse_the_selection():
    """Gate composer-reuse (conversation design v2 s7 E, v1 s7F): when this actor's rows are identical to the rows of
    their previous call, the kept selection is reused - `by: "kept"`, no dispatch. Rows that moved ask again; a floor
    the composer fell back to is never kept, so the next call asks again."""
    print("\n[10] IDENTICAL ROWS REUSE THE SELECTION (composer-reuse)")
    import json
    import direct
    affect = {p: 0.7 for p in rungs.paths()}
    top = C.selectable(affect)[0]
    good = json.dumps({"selected": [{"path": top["path"], "rung": top["rung"], "primary": True}],
                       "about": "the debt she owes him", "unavailable": ""})
    sent, answers = [], []
    real, err = direct._openrouter, sys.stderr

    def fake(msgs, model, **kw):
        sent.append(msgs)
        return answers.pop(0) if answers else good

    def call(aff, kept):
        packet = {"volatile": {"state": {"affect": aff}}, "manifest": {}}
        out = direct.rung_direction(packet, brief="the wheel has split", model="fake/model", kept=kept)
        return out, packet["manifest"]["direction"]

    import io
    direct._openrouter, sys.stderr = fake, io.StringIO()
    try:
        kept = {}
        first, r1 = call(affect, kept)
        second, r2 = call(dict(affect), kept)
        check("two-calls-on-identical-rows-make-one-dispatch", len(sent) == 1, "%d dispatches" % len(sent))
        check("...the-second-is-recorded-kept-with-the-same-selection", r1["by"] == "composer" and r2["by"] == "kept"
              and r2["selected"] == r1["selected"] and r2["about"] == r1["about"] and second == first, (r1["by"], r2["by"]))
        moved = dict(affect, **{C.selectable(affect)[1]["path"]: 0.05})   # another path's rung; the reply stays valid
        _out, r3 = call(moved, kept)
        check("rows-that-moved-ask-again", len(sent) == 2 and r3["by"] == "composer", (len(sent), r3["by"]))
        other = {}
        _out, r4 = call(moved, other)
        check("another-actor's-keep-is-their-own", len(sent) == 3 and r4["by"] == "composer", (len(sent), r4["by"]))
        answers.append("not json at all")
        fell = {}
        _out, r5 = call(affect, fell)
        _out, r6 = call(affect, fell)
        check("a-floor-the-composer-fell-back-to-is-not-kept", r5["by"] == "floor" and r6["by"] == "composer"
              and len(sent) == 5, (r5["by"], r6["by"], len(sent)))
        nokeep = [call(affect, None)[1]["by"] for _ in range(2)]
        check("without-a-keep-every-call-asks-as-before", nokeep == ["composer", "composer"] and len(sent) == 7,
              (nokeep, len(sent)))
    finally:
        direct._openrouter, sys.stderr = real, err


def test_each_feeling_says_what_it_is_on():
    """Gate composer-on (round 2 ruling 1; a replayed two-hander's state texts carried no object): a selected feeling's
    `on` is rendered "This is about: <on>" under its own block and kept in the record; it is checked as `about` is - not
    text, an emotion name or a named act is refused. A selection without one renders as before."""
    print("\n[11] EACH FEELING SAYS WHAT IT IS ON (composer-on)")
    rows = C.selectable({p: 0.7 for p in rungs.paths()})
    a, b = rows[0], rows[1]
    sel = {"selected": [{"path": a["path"], "rung": a["rung"], "primary": True, "on": "the girl crossing the ford"},
                        {"path": b["path"], "rung": b["rung"], "primary": False, "on": "the lamp she will not light"}],
           "about": "", "unavailable": ""}
    text = " ".join(C.direction_for(rows, C.verify(sel, rows)).split())
    first, second = " ".join(a["block"].split()), " ".join(b["block"].split())
    check("each-block-is-followed-by-its-own-on",
          text.index(first) < text.index("This is about: the girl crossing the ford") < text.index(second)
          < text.index("This is about: the lamp she will not light"), text[:200])
    rec = C.record(rows, sel, "x", "composer")
    check("...and-the-record-keeps-it-per-selection", [s.get("on") for s in rec["selected"]]
          == ["the girl crossing the ford", "the lamp she will not light"], rec["selected"])
    bare = {"selected": [{"path": a["path"], "rung": a["rung"], "primary": True}], "about": "", "unavailable": ""}
    check("a-selection-without-on-renders-as-before", "This is about" not in C.direction_for(rows, bare)
          and "on" not in C.record(rows, bare, "x", "composer")["selected"][0], C.direction_for(rows, bare)[:80])
    for name, on, code in (("an-on-that-names-an-emotion", "his rage at the girl", "COMPOSER_NAMES_EMOTION"),
                           ("an-on-that-names-an-act", "she strikes him", "COMPOSER_NAMES_ACT"),
                           ("an-on-that-is-not-text", 5, "COMPOSER_FIELD_TYPE")):
        bad = {"selected": [{"path": a["path"], "rung": a["rung"], "primary": True, "on": on}], "about": ""}
        try:
            C.verify(bad, rows)
            got = None
        except C.ComposerError as e:
            got = str(e)
        check("%s-is-refused" % name, bool(got) and code in got, got)


def test_the_keep_expires_when_the_other_moved():
    """Gate composer-on (round 2 ruling 2b; a replayed two-hander held one character's direction for eight turns while
    the other refused them): the scene driver marks the keep with how far the other party has moved; the same rows and
    brief are reused only while that mark stands - a redraw within a beat, or the speaker's own keep - and asked again
    once it moves. A keep with no mark compares as before."""
    print("\n[12] THE KEEP EXPIRES WHEN THE OTHER HAS MOVED (composer-on)")
    import io
    import json
    import direct
    import scene
    affect = {p: 0.7 for p in rungs.paths()}
    top = C.selectable(affect)[0]
    good = json.dumps({"selected": [{"path": top["path"], "rung": top["rung"], "primary": True}],
                       "about": "the debt she owes him", "unavailable": ""})
    sent = []
    real, err = direct._openrouter, sys.stderr

    def call(kept, mark):
        kept["moved"] = mark
        packet = {"volatile": {"state": {"affect": affect}}, "manifest": {}}
        direct.rung_direction(packet, brief="the wheel has split", model="fake/model", kept=kept)
        return packet["manifest"]["direction"]["by"]

    direct._openrouter, sys.stderr = (lambda msgs, model, **kw: sent.append(1) or good), io.StringIO()
    try:
        kept = {}
        got = [call(kept, 0), call(kept, 0), call(kept, 1), call(kept, 1)]
        check("same-rows-but-the-other-moved-asks-again", got == ["composer", "kept", "composer", "kept"]
              and len(sent) == 2, (got, len(sent)))
    finally:
        direct._openrouter, sys.stderr = real, err
    log = [{"who": "ash", "move": True, "floor": "yield"}, {"who": "wren", "move": True, "floor": "take"},
           {"who": "", "move": False, "floor": ""}, {"who": "ash", "move": True, "floor": "keep"},
           {"who": "wren", "move": False, "floor": "hold"}, {"who": "wren", "move": False, "floor": "interject"}]
    check("the-mark-counts-the-others'-moves-and-interjections-not-holds-or-the-room",
          (scene._moved(log, "ash"), scene._moved(log, "wren")) == (2, 2),
          (scene._moved(log, "ash"), scene._moved(log, "wren")))


def main():
    print("test_composer.py - the gate between composer and actor\n")
    for t in sorted((v for k, v in globals().items()
                     if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        try:
            t()
        except Exception as e:                       # noqa: BLE001 - a harness reports, never raises
            check("%s RAISED %s" % (t.__name__, type(e).__name__), False, str(e)[:150])
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
