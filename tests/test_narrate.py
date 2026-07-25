#!/usr/bin/env python3
"""test_narrate.py — the POV-bound narrator (design.md layer 7, narration.md).

Proves gate swe-narrator-pov: the POV wall (pov_split keeps the POV's thought, drops others'), the
prompt boundary (POV's thought present, a non-POV thought ABSENT), the stub path, and the strong-
model dispatch parse. critic._openrouter is reused by narrate; monkeypatched here so no API runs.
Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import copy                                                  # noqa: E402
import json                                                  # noqa: E402
import tempfile                                              # noqa: E402

import narrate                                                # noqa: E402
import scene                                                  # noqa: E402
from src.engine.ledger import Ledger                          # noqa: E402

WORLD = {"world": "Ashford — a small upland village"}
TURNS = [
    {"turn": 0, "actor": "maren", "action": "She set the cup down and said the fever would break by dawn.",
     "thought": "It will not break by dawn. I am lying to keep them calm."},
    {"turn": 1, "actor": "edda", "action": "Edda nodded and thanked her, easier now.",
     "thought": "SECRET-EDDA-DOUBT: I do not believe her, but I will not say so."},
]
FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def main():
    print("test_narrate.py — POV-bound narrator\n")

    # 1. the POV wall: POV keeps thought; the other actor loses it
    split = narrate.pov_split(TURNS, "maren")
    maren = next(e for e in split if e["actor"] == "maren")
    edda = next(e for e in split if e["actor"] == "edda")
    check("pov-keeps-thought", "thought" in maren and "lying" in maren["thought"])
    check("nonpov-drops-thought", "thought" not in edda, str(edda))

    # 2. the prompt boundary: POV's interiority is in, the non-POV SECRET is OUT
    blob = " ".join(m["content"] for m in narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren"))
    check("prompt-names-pov", "Maren" in blob)
    check("prompt-has-pov-thought", "lying to keep them calm" in blob)
    check("prompt-hides-nonpov-secret", "SECRET-EDDA-DOUBT" not in blob, "non-POV thought leaked into the prompt")
    check("prompt-has-nonpov-action", "thanked her" in blob)  # observable action still rendered
    msgs = narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren")
    check("prompt-json-serializable", len(json.loads(json.dumps(msgs))) == 2)  # --prompt-only must round-trip for Claude-in-the-loop

    # 3. stub path: POV's actions strung deterministically (no API)
    s = narrate.narrate(TURNS, "maren", WORLD, stub=True)
    check("stub-pov-actions", "fever would break by dawn" in s and "thanked her" not in s,
          "stub should render only the POV's actions")
    check("stub-empty-scene", narrate.narrate([], "maren", WORLD, stub=True) == "")

    # 4. strong-model dispatch returns the rendered prose (monkeypatched)
    _real = narrate._openrouter
    try:
        narrate._openrouter = lambda messages, model, max_tokens=2000: "The cup met the table without a sound."
        out = narrate.narrate(TURNS, "maren", WORLD, stub=False)
        check("dispatch-returns-prose", out == "The cup met the table without a sound.", out)
    finally:
        narrate._openrouter = _real

    # 5. book-scale: narrate a whole multi-scene chronicle, POV per recorded scene
    _book_narration()

    if FAILS:
        print("\ntest_narrate: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_narrate: OK (POV wall holds; the non-POV secret never reaches the prose; book narrates per-scene POV)")
    return 0


def _book_chars():
    base = json.load(open(os.path.join(REPO, "characters/maren-healer.json"), encoding="utf-8"))
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    chars = {}
    for cid, name in (("maren", "Maren"), ("edda", "Edda")):
        ch = copy.deepcopy(base)
        ch["fixed"]["id"] = cid
        ch["fixed"]["name"] = name
        chars[cid] = ch
    return world, chars


def _book_narration():
    print("\n[book] narrate_book — whole chronicle, POV per scene")
    world, chars = _book_chars()
    led = Ledger(os.path.join(tempfile.mkdtemp(prefix="narrate_book_"), "chronicle.db"))
    led.create_run("bk", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    for cid in ("maren", "edda"):
        led.register_character("bk", cid, chars[cid]["fixed"], chars[cid]["baseline"])
    cfg = {"name": "fireside", "situation": "Two healers by the fire.", "subject": (None, None),
           "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
           "cast": [{"id": "maren", "drive": "rest"}, {"id": "edda", "drive": "talk"}]}
    nt0 = scene.run_scene(world, chars, cfg, led, "bk", 0, "stub", True, 2, think=False)
    led.append_scene("bk", 0, "fireside", "maren", 0, nt0 - 1)           # scene 0 POV = maren (the actor)
    cfg2 = dict(cfg, name="the-ward", situation="Later, in the sickroom.")
    w2, c2 = _book_chars()
    nt1 = scene.run_scene(w2, c2, cfg2, led, "bk", nt0, "stub", True, 2, think=False)
    led.append_scene("bk", 1, "the-ward", "edda", nt0, nt1 - 1)          # scene 1 POV = edda (who did NOT act -> proves POV is per-scene)

    book = narrate.narrate_book(led, "bk", world, chars, stub=True)
    check("book-has-scene0-header", "## fireside" in book, book[:120])
    check("book-has-scene1-header", "## the-ward" in book, book[:200])
    check("scene0-renders-maren-pov", "two healers by the fire" in book.lower())
    # scene 1's recorded actor is maren, but its POV is edda -> edda has no actions in range -> quiet
    check("scene1-uses-edda-pov", "the scene passes quietly" in book.lower(),
          "scene1 should be quiet (POV edda did not act) — proves per-scene POV: %s" % book[-160:])


if __name__ == "__main__":
    sys.exit(main())
