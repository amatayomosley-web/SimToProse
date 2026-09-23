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
