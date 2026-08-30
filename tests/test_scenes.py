#!/usr/bin/env python3
"""test_scenes.py — scene boundaries become first-class (gate swe-scene-boundaries).

Covers Ledger.append_scene / scenes_for / next_scene_no and the main()-style recording: two
sequential scenes get scene_no 0 then 1 with contiguous turn ranges (the book's structure for the
cutting room + book-scale narration). Stub-driven, no API. Script-style, exit 0 = all pass.
"""
import copy
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.ledger import Ledger                                 # noqa: E402
import scene                                                         # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _cast():
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    base = json.load(open(os.path.join(REPO, "characters/maren-healer.json"), encoding="utf-8"))
    chars = {}
    for cid, name in (("maren", "Maren"), ("edda", "Edda")):
        ch = copy.deepcopy(base)
        ch["fixed"]["id"] = cid
        ch["fixed"]["name"] = name
        chars[cid] = ch
    cfg = {"name": "fireside", "pov": "maren", "situation": "Two healers by the fire.",
           "subject": (None, None), "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
           "cast": [{"id": "maren", "drive": "rest"}, {"id": "edda", "drive": "talk"}]}
    return world, chars, cfg


def _record_scene(led, run_id, cfg, cast_ids, start_turn, next_turn):
    """Mirror scene.py:main's boundary-recording logic (the part under test)."""
    last = max(next_turn - 1, 0)
    if next_turn > start_turn:
        scene_no = led.next_scene_no(run_id)
        pov = cfg.get("pov") or (cast_ids[0] if cast_ids else None)
        led.append_scene(run_id, scene_no, cfg.get("name", "scene"), pov, start_turn, last)
        return scene_no
    return None


def main():
    print("test_scenes.py — scene boundaries\n")
    tmp = tempfile.mkdtemp(prefix="scenes_")
    led = Ledger(os.path.join(tmp, "chronicle.db"))
    led.create_run("bk", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    world, chars, cfg = _cast()
    for cid in ("maren", "edda"):
        led.register_character("bk", cid, chars[cid]["fixed"], chars[cid]["baseline"])

    check("next-scene-no-empty-is-0", led.next_scene_no("bk") == 0)

    # scene 0
    nt0 = scene.run_scene(world, chars, cfg, led, "bk", 0, "stub", True, 3, think=False)
    s0 = _record_scene(led, "bk", cfg, ["maren", "edda"], 0, nt0)
    check("scene-0-recorded", s0 == 0)

    # scene 1 (continues the chronicle)
    world2, chars2, cfg2 = _cast()
    nt1 = scene.run_scene(world2, chars2, cfg2, led, "bk", nt0, "stub", True, 3, think=False)
    s1 = _record_scene(led, "bk", cfg2, ["maren", "edda"], nt0, nt1)
    check("scene-1-recorded", s1 == 1)

    scenes = led.scenes_for("bk")
    check("two-scenes-in-order", [s["scene_no"] for s in scenes] == [0, 1], str(scenes))
    check("pov-stored", all(s["pov"] == "maren" for s in scenes))
    check("scene0-range", scenes[0]["start_turn"] == 0 and scenes[0]["end_turn"] == nt0 - 1, str(scenes[0]))
    check("contiguous-ranges", scenes[1]["start_turn"] == nt0, "scene1 start %d != %d" % (scenes[1]["start_turn"], nt0))
    check("label-stored", scenes[0]["label"] == "fireside")

    if FAILS:
        print("\ntest_scenes: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_scenes: OK (scenes first-class; contiguous ranges; pov + label persisted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
