#!/usr/bin/env python3
"""test_scene_config.py — director-authored scene configs (gate swe-scene-config-externalization).

A scene cfg loads from JSON, validates (fail loud on missing situation/cast), and drives run_scene
exactly like the built-in BP13 — so a director can author varied scenes for a multi-scene book.
Deterministic (--stub), a 2-actor cast cloned from the Maren fixture. Script-style, exit 0 = all pass.
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


def _write(tmp, obj):
    p = os.path.join(tmp, "scene.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    return p


def _cast():
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    base = json.load(open(os.path.join(REPO, "characters/maren-healer.json"), encoding="utf-8"))
    chars = {}
    for cid, name in (("maren", "Maren"), ("edda", "Edda")):
        ch = copy.deepcopy(base)
        ch["fixed"]["id"] = cid
        ch["fixed"]["name"] = name
        chars[cid] = ch
    return world, chars


def main():
    print("test_scene_config.py — director-authored scene configs\n")
    tmp = tempfile.mkdtemp(prefix="scene_cfg_")

    # 1. a valid cfg loads + normalizes
    good = {"situation": "Two healers rest by the fire.",
            "subject": [None, None],
            "cast": [{"id": "maren", "drive": "rest"}, {"id": "edda", "drive": "talk"}]}
    cfg = scene.load_scene_cfg(_write(tmp, good))
    check("loads-situation", cfg["situation"].startswith("Two healers"))
    check("subject-is-tuple", isinstance(cfg["subject"], tuple) and cfg["subject"] == (None, None))
    check("name-defaulted", cfg["name"] == "scene")
    check("opening-tags-defaulted", isinstance(cfg.get("opening_tags"), dict))

    # 2. malformed cfgs fail loud
    for bad, label in (({"cast": [{"id": "x", "drive": "y"}]}, "no-situation"),
                       ({"situation": "x"}, "no-cast"),
                       ({"situation": "x", "cast": [{"id": "x"}]}, "cast-missing-drive")):
        try:
            scene.load_scene_cfg(_write(tmp, bad))
            check("raises-%s" % label, False, "no error raised")
        except ValueError:
            check("raises-%s" % label, True)

    # 3. the loaded cfg drives run_scene under --stub
    world, chars = _cast()
    led = Ledger(os.path.join(tmp, "chronicle.db"))
    led.create_run("cfg-run", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    for cid in ("maren", "edda"):
        led.register_character("cfg-run", cid, chars[cid]["fixed"], chars[cid]["baseline"])
    next_turn = scene.run_scene(world, chars, cfg, led, "cfg-run", 0, "stub-model", True, 3, think=False)
    n = led.con.execute("SELECT COUNT(*) c FROM turns WHERE run_id=?", ("cfg-run",)).fetchone()["c"]
    check("cfg-drives-run-scene", n >= 1 and n == next_turn, "n=%d next=%d" % (n, next_turn))

    if FAILS:
        print("\ntest_scene_config: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_scene_config: OK (cfg loads, validates, drives the runner)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
