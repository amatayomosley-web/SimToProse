# -*- coding: utf-8 -*-
"""Every driver that builds actor messages must deliver the rung block.

WHY THIS IS DERIVED AND NOT A LIST. The rung seam shipped on 2026-09-08 with `direct.py`'s
`llm_turn` wired and its `--prompt-only` branch NOT wired; the unit suite passed on a synthetic
packet while a real run emitted no block. The same defect was then found in `scene.py`'s act seam
and `exp.py`. Three instances of one bug, each found by hand, each after the fact.

So this walks the AST of every driver in `scripts/` and finds `build_turn_messages(...)` calls
itself, rather than checking a list someone has to remember to extend. A new driver is covered the
moment it is written. That is the rule CLAUDE.md states after finding seven hand-maintained
duplicates of a source of truth in one session: if you are about to write a list that mirrors
something the code already knows, derive it.

WHAT A FAILURE MEANS. A call site without `rung_direction` hands its actor a strictly SMALLER
prompt than the live dispatch builds — the emotion ladder silently absent for that path only.
`docs/orchestration.md` requires the act seam to emit exactly the messages the engine would have
sent, so an unwired `--prompt-only` branch breaks a stated contract rather than merely differing.
"""
import ast
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "scripts")

# A call site may opt OUT only with a reason recorded here. Empty on purpose: every driver that
# builds actor messages should deliver the block. If a future site legitimately must not, add it
# with the reason, and the entry is then visible in review rather than invisible in an omission.
EXEMPT = {}


def _call_sites():
    """-> [(relpath, lineno, passes_rung_direction)] for every build_turn_messages call in scripts/."""
    found = []
    for name in sorted(os.listdir(SCRIPTS)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(SCRIPTS, name)
        try:
            tree = ast.parse(io.open(path, encoding="utf-8").read())
        except SyntaxError as exc:                       # a broken driver is its own failure
            found.append((name, getattr(exc, "lineno", 0), None))
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            fname = getattr(fn, "id", None) or getattr(fn, "attr", None)
            if fname != "build_turn_messages":
                continue
            kws = {k.arg for k in node.keywords if k.arg}
            found.append((name, node.lineno, "rung_direction" in kws))
    return found


def test_every_driver_delivers_the_rung_block():
    sites = _call_sites()
    assert sites, "found no build_turn_messages call in scripts/ — the walker is broken, not the tree"
    bad = [(f, ln) for f, ln, ok in sites
           if ok is not True and "%s:%d" % (f, ln) not in EXEMPT]
    assert not bad, (
        "these driver call sites build actor messages WITHOUT rung_direction, so the emotion "
        "ladder is silently absent on those paths only: "
        + ", ".join("%s:%d" % b for b in bad)
        + ". Wire them, or record an exemption with its reason in EXEMPT.")
    return len(sites)


def test_the_walker_can_see_an_unwired_site():
    """The control. test_every_driver... is a claim about what the walker READS before it is a claim
    about the tree, so prove the walker actually reports an unwired call rather than passing because
    it found nothing to look at (CLAUDE.md: a green guard is a coverage claim first)."""
    tree = ast.parse("build_turn_messages(packet, ev, temp)\n"
                     "build_turn_messages(packet, ev, temp, rung_direction=d)\n")
    seen = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "build_turn_messages":
            seen.append("rung_direction" in {k.arg for k in node.keywords if k.arg})
    assert seen == [False, True], (
        "the AST walk cannot distinguish a wired call from an unwired one; got %r" % (seen,))


if __name__ == "__main__":
    n = test_every_driver_delivers_the_rung_block()
    test_the_walker_can_see_an_unwired_site()
    print("PASS  rung_seam_coverage — %d driver call site(s), all deliver the block" % n)
    sys.exit(0)
