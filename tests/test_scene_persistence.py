#!/usr/bin/env python3
"""test_scene_persistence.py — the multi-agent scene runner persists its chronicle to the ledger.

Proves gate swe-scene-ledger-persistence:
  1. PER-BEAT COMMIT   — run_scene writes one `turns` row per beat (actor = that beat's speaker)
  2. RESUME HOLDS      — Ledger.resume() returns without RESUME DIVERGENCE after a scene
  3. CROSS-SCENE       — a second run_scene resuming the same run_id accumulates further turns

Deterministic: --stub (no API). A 2-actor cast cloned from the Maren fixture so the test needs no
external book vault. Script-style like the other suites: plain asserts, main(), exit 0 = all pass.
"""
import copy
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.ledger import Ledger                                # noqa: E402
from scene import run_scene                                         # noqa: E402  (the runner under test)


def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _cast():
    """A 2-actor cast cloned from the single Maren fixture (distinct ids/names) + the Ashford slice +
    a minimal mundane cfg — enough to drive the runner deterministically under --stub."""
    world = _load("world/ashford-slice.json")
    base = _load("characters/maren-healer.json")
    chars = {}
    for cid, name in (("maren", "Maren"), ("edda", "Edda")):
        ch = copy.deepcopy(base)
        ch["fixed"]["id"] = cid
        ch["fixed"]["name"] = name
        chars[cid] = ch
    cfg = {
        "name": "fireside",
        "situation": "Two healers sit by the fire after a long day in the ward.",
        "subject": (None, None),
        "opening_tags": {"type": "mundane", "dimensions": {"care_relevant": 0.3}, "durability": "transient"},
        "cast": [
            {"id": "maren", "drive": "rest, and know the ward is quiet for the night"},
            {"id": "edda", "drive": "share the weight of the day with someone who understands"},
        ],
    }
    return world, chars, cfg


def _count(led, run_id):
    return led.con.execute("SELECT COUNT(*) c FROM turns WHERE run_id=?", (run_id,)).fetchone()["c"]


def main():
    world, chars, cfg = _cast()
    db = os.path.join(tempfile.mkdtemp(prefix="scene_persist_"), "chronicle.db")
    led = Ledger(db)
    run_id = "scene-test-1"
    led.create_run(run_id, {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    for cid in ("maren", "edda"):
        led.register_character(run_id, cid, chars[cid]["fixed"], chars[cid]["baseline"])

    # ---- 1. PER-BEAT COMMIT ----
    next_turn = run_scene(world, chars, cfg, led, run_id, 0, "stub-model", True, 4, think=False)
    n1 = _count(led, run_id)
    assert n1 >= 1, "scene 1 committed no turns"
    assert n1 == next_turn, "turn counter (%d) != committed turns (%d)" % (next_turn, n1)
    actors = {r["actor"] for r in led.con.execute("SELECT DISTINCT actor FROM turns WHERE run_id=?", (run_id,))}
    assert actors <= {"maren", "edda"}, "unexpected actor(s): %s" % (actors - {"maren", "edda"})
    print("  [1] per-beat commit: %d turns, actors=%s — OK" % (n1, sorted(actors)))

    # ---- 2. RESUME HOLDS (no fold divergence) ----
    last = max(next_turn - 1, 0)
    led.persist_snapshot(run_id, last, led.fold(run_id, last))
    led.set_status(run_id, "parked")
    led.set_status(run_id, "active")
    state = led.resume(run_id)
    assert state["turn"] == last, "resume turn %d != last committed %d" % (state["turn"], last)
    print("  [2] resume holds: turn=%d, no fold divergence — OK" % state["turn"])

    # ---- 3. CROSS-SCENE accumulation (a later scene continues the same chronicle) ----
    world2, chars2, cfg2 = _cast()
    next_turn2 = run_scene(world2, chars2, cfg2, led, run_id, next_turn, "stub-model", True, 3, think=False)
    n2 = _count(led, run_id)
    assert n2 > n1, "scene 2 did not accumulate (n1=%d, n2=%d)" % (n1, n2)
    assert next_turn2 == n2, "cross-scene turn counter (%d) != total committed (%d)" % (next_turn2, n2)
    print("  [3] cross-scene: scene2 grew %d -> %d turns — OK" % (n1, n2))

    print("test_scene_persistence: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
