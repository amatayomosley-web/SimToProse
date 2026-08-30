#!/usr/bin/env python3
"""test_pipeline_e2e.py — the whole pipeline COMPOSES on a multi-scene chronicle.

The unit suites prove each stage in isolation; this proves they fit together end-to-end:
  lint -> run scene 1 -> run scene 2 (resume) -> scene boundaries -> cut dailies -> critic (stub)
  -> book narration.
Deterministic (--stub, no API), a 2-actor cast cloned from the Maren fixture. Script-style, exit 0 = pass.
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
import cut                                                           # noqa: E402
import critic                                                        # noqa: E402
import narrate                                                       # noqa: E402
import lint_book                                                     # noqa: E402

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
    return world, chars


def _run_scene(led, run_id, world, chars, cfg, start_turn):
    """Mirror scene.py:main's run + boundary-record (the orchestration the CLI does)."""
    nt = scene.run_scene(world, chars, cfg, led, run_id, start_turn, "stub", True, 3, think=False)
    if nt > start_turn:
        led.append_scene(run_id, led.next_scene_no(run_id), cfg["name"],
                         cfg.get("pov") or cfg["cast"][0]["id"], start_turn, nt - 1)
    return nt


def main():
    print("test_pipeline_e2e.py — the pipeline composes\n")
    world, chars = _cast()

    # 0. lint gate before running
    check("lint-clean-before-run", lint_book.lint(world, {"maren": chars["maren"]})["errors"] == [])

    db = os.path.join(tempfile.mkdtemp(prefix="e2e_"), "chronicle.db")
    led = Ledger(db)
    run_id = "e2e"
    led.create_run(run_id, {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    for cid in ("maren", "edda"):
        led.register_character(run_id, cid, chars[cid]["fixed"], chars[cid]["baseline"])

    # 1. two scenes into one chronicle (scene 2 resumes)
    cfg1 = {"name": "fireside", "pov": "maren", "situation": "Two healers rest by the fire.",
            "subject": (None, None), "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
            "cast": [{"id": "maren", "drive": "rest"}, {"id": "edda", "drive": "talk"}]}
    nt1 = _run_scene(led, run_id, world, chars, cfg1, 0)
    w2, c2 = _cast()
    cfg2 = dict(cfg1, name="the-ward", situation="Later, in the sickroom.")
    nt2 = _run_scene(led, run_id, w2, c2, cfg2, nt1)
    check("two-scenes-committed", nt2 > nt1 >= 1, "nt1=%d nt2=%d" % (nt1, nt2))
    check("two-scene-boundaries", [s["scene_no"] for s in led.scenes_for(run_id)] == [0, 1])

    # 2. cutting-room dailies see the chronicle
    d = cut.dailies(led, run_id)
    check("dailies-scenes", len(d["scenes"]) == 2 and d["scenes"][0]["label"] == "fireside")
    check("dailies-biggest-moments", len(d["biggest_moments"]) == nt2)  # every committed beat surfaced as a candidate

    # 3. critic reviews a scene (stub -> clean)
    s0_turns = critic.scene_turns(led, run_id)[:nt1]
    check("critic-clean-stub", critic.review_scene(s0_turns, world, stub=True) == {"continuity": [], "voice": []})

    # 4. book narration renders both scenes
    book = narrate.narrate_book(led, run_id, world, chars, stub=True)
    check("manuscript-both-scenes", "## fireside" in book and "## the-ward" in book, book[:160])

    if FAILS:
        print("\ntest_pipeline_e2e: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_pipeline_e2e: OK (lint -> scenes -> boundaries -> dailies -> critic -> manuscript)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
