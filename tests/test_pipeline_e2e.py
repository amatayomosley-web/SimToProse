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
    for cid, name in (("maren", "Maren"), ("edda_elder", "Edda")):
        ch = copy.deepcopy(base)
        ch["fixed"]["id"] = cid
        ch["fixed"]["name"] = name
        chars[cid] = ch
    # THE CAST MUST BE PEOPLE THE WORLD KNOWS. `scene._build_edges` emits an edge only for someone
    # who appears in the PerceptSet AND has a relationship record — the repo's own "a character is
    # not automatically an entity" rule. This fixture used the id `edda`, which is in neither
    # `world.people` nor the reference sheet's relationships, so the two clones were strangers: no
    # edge, no addressee, `_ADDRESSED_BONUS` (0.15) never applied, and the scene lulled after ONE
    # beat while the suite reported OK. `edda_elder` is the id the world and the sheet already
    # carry. The engine was right; the cast was not.
    chars["edda_elder"]["current"]["relationships"]["maren"] = {
        "trust": 0.75, "affinity": 0.6, "respect": 0.7, "debt": 0.0,
        "history": "village elder; long mutual reliance"}
    return world, chars


def _run_scene(led, run_id, world, chars, cfg, start_turn):
    """Run a scene and close it THROUGH THE DRIVER'S OWN FUNCTION, not a copy of it.

    This used to reimplement the orchestration, with a docstring that said so ("Mirror
    scene.py:main's ..."). The copy had drifted in four ways — no cfg pin, no voice, no knowledge,
    no snapshot-or-park — so this suite, the one named end-to-end, was asserting against a pipeline
    the CLI does not run. `scene.record_and_park` is now the single implementation and both call it.
    """
    nt = scene.run_scene(world, chars, cfg, led, run_id, start_turn, "stub", True, 3, think=False)
    # RECORD per scene; the PARK is what an invocation does on its way out, and this suite runs
    # several scenes in one process. Calling the combined function here parked the run and then
    # failed the next scene with LEDGER_RUN_NOT_ACTIVE — a seam the old hand-written copy hid by
    # implementing neither half.
    scene.record_boundary(led, run_id, cfg, start_turn, nt,
                          cast_ids=[c["id"] for c in cfg.get("cast", [])], announce=False)
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
    for cid in ("maren", "edda_elder"):
        led.register_character(run_id, cid, chars[cid]["fixed"], chars[cid]["baseline"])

    # 1. two scenes into one chronicle (scene 2 resumes)
    cfg1 = {"name": "fireside", "pov": "maren", "situation": "Maren and Edda rest by the fire.",
            "subject": (None, None), "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
            "cast": [{"id": "maren", "drive": "rest"}, {"id": "edda_elder", "drive": "talk"}]}
    nt1 = _run_scene(led, run_id, world, chars, cfg1, 0)
    w2, c2 = _cast()
    cfg2 = dict(cfg1, name="the-ward", situation="Later, Maren and Edda work in the sickroom.")
    nt2 = _run_scene(led, run_id, w2, c2, cfg2, nt1)
    check("two-scenes-committed", nt2 > nt1 >= 1, "nt1=%d nt2=%d" % (nt1, nt2))
    check("two-scene-boundaries", [s["scene_no"] for s in led.scenes_for(run_id)] == [0, 1])

    # WHAT THE MIRROR NEVER REACHED. The hand-written copy called append_scene with six positional
    # arguments, so it passed no cfg, no voice and no knowledge — every scene row it wrote carried
    # an EMPTY fingerprint, and the schema v14 pin (a resumed run being able to say what location,
    # cast and props produced the turns it replays) was uncovered by the suite named end-to-end.
    # Asserted here because a coverage claim nobody checks is how the copy drifted unnoticed.
    rows = led.scenes_for(run_id)
    # DETAIL MUST BE A STRING — this suite's check() concatenates it, so a list here turns a clean
    # FAIL into a TypeError and the finding is lost behind a traceback. Caught by breakage-testing
    # this very assertion: it fired correctly and then crashed on its way to reporting.
    check("every-scene-PINS-its-cfg", all(r["cfg_fingerprint"] for r in rows),
          "fingerprints: %r" % ([r["cfg_fingerprint"] for r in rows],))
    check("and-records-the-narration-choice",
          all(r["voice"] and r["knowledge"] for r in rows),
          "voice/knowledge: %r" % ([(r["voice"], r["knowledge"]) for r in rows],))

    # ...and the PARK, the other half the copy omitted. It is per-invocation, not per-scene, so it
    # runs once here at the end of the pipeline the way the driver runs it once on its way out.
    scene.park(led, run_id, max(r["end_turn"] for r in rows))
    check("the-run-parks", led.load_run(run_id)["status"] == "parked",
          led.load_run(run_id)["status"])
    check("and-the-snapshot-cache-was-written",
          led.con.execute("SELECT COUNT(*) c FROM snapshots WHERE run_id=?",
                          (run_id,)).fetchone()["c"] > 0)
    # A PIPELINE THAT COMPOSES IS NOT A PIPELINE THAT PRODUCES A SCENE. Until 2026-09-01 this suite
    # reported OK on a scene that lulled after ONE beat (max urge 0.018 against a 0.060 floor) —
    # six PASS lines above an outcome no user would accept. The cause was the stub setting no
    # addressee, so `_ADDRESSED_BONUS` never applied; the engine was correct and the fixture was not.
    spans = [(s["scene_no"], s["end_turn"] - s["start_turn"] + 1) for s in led.scenes_for(run_id)]
    check("a-scene-SUSTAINED-past-one-beat", any(n > 1 for _no, n in spans),
          "beats per scene: %s — a two-hander where nobody answers is a lull, not a scene" % spans)

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
