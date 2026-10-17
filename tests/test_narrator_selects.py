#!/usr/bin/env python3
"""test_narrator_selects.py - gate narrator-compression: the narrator SELECTS (the owner: "the narrators job is to take
what's generated and turn it into the story").

A telling of a replayed two-hander came out in the record's shape: one paragraph per row, every spoken line wrapped in
a gesture, nothing summarized, the same gesture copied from row to row. The contract demanded it - every act fixed and
undroppable, every listener's act placed, every silence shown. The control: a scripted scene whose rows repeat one
gesture builds a prompt that no longer asks for every row, says what may be cut and what may not (with a test for a
dropped line), and carries the never-do list; the role file says the same.
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import narrate                       # noqa: E402

WORLD = {"world": "A hill village with one well."}
GESTURE = "Ash rubs the back of his neck."
TURNS = [
    {"turn": 0, "actor": "wren", "action": '"The well rope is frayed."', "thought": "Say it plainly.", "floor": "yield",
     "addressee": "ash"},
    {"turn": 1, "actor": "ash", "action": GESTURE + ' "It held all summer."', "thought": "x", "floor": "take",
     "addressee": "wren"},
    {"turn": 2, "actor": "wren", "action": '"Summer is over."', "thought": "Press it.", "floor": "yield",
     "addressee": "ash"},
    {"turn": 3, "actor": "ash", "action": GESTURE, "thought": "x", "floor": "hold", "addressee": ""},
    {"turn": 4, "actor": "wren", "action": '"I will splice it tonight."', "thought": "Then do it.", "floor": "yield",
     "addressee": "ash"},
    {"turn": 5, "actor": "ash", "action": GESTURE + ' "Do."', "thought": "x", "floor": "take", "addressee": "wren"},
    {"turn": 6, "actor": "wren", "action": "", "thought": "Done talking.", "floor": "hold", "addressee": ""},
]
SELECTS = ("THE NOVELIST SELECTS", "dramatize in full", "compress into summary", "rendered once or not at all")
CANNOT_CUT = ("what changed hands", "a line the story turns on", "if a later line answers it")
NEVER = ("NEVER DO", "a paragraph that ends on a saying", "explaining the subtext", "fragment runs",
         "the same epithet or gesture")
PER_ROW = ("every act and what changed hands", "put them there and nowhere else", "render what the listener did",
           "show what %s did" % "Wren")


def _prompt():
    msgs = narrate.build_narration_prompt(TURNS, "wren", WORLD, pov_name="Wren", names={"wren": "Wren", "ash": "Ash"})
    return msgs[0]["content"], msgs[1]["content"]


def test_the_prompt_selects_and_carries_the_never_do_list():
    sys_, user = _prompt()
    blob = sys_ + "\n" + user
    missing = [p for p in SELECTS + CANNOT_CUT + NEVER if p not in blob]
    assert not missing, "the prompt lacks %s" % missing
    stale = [p for p in PER_ROW if p in blob]
    assert not stale, "the prompt still asks for every row: %s" % stale
    assert "the record, row by row; the story you write from it is not" in user, user[:600]


def test_the_role_file_says_the_same():
    role = io.open(os.path.join(REPO, ".claude", "agents", "narrator.md"), encoding="utf-8").read()
    missing = [p for p in SELECTS + CANNOT_CUT + NEVER if p not in role]
    assert not missing, "narrator.md lacks %s" % missing
    stale = [p for p in PER_ROW[:3] if p in role]
    assert not stale, "narrator.md still asks for every row: %s" % stale


def test_the_fixed_substance_stands():
    sys_, _ = _prompt()
    for p in ("Nothing is said on the page that the record does not say", "never text for the page", "one speech"):
        assert p in sys_, p


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("  PASS  %s" % name)
    print("narrator selects: all checks passed")
