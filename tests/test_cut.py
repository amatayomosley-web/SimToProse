#!/usr/bin/env python3
"""test_cut.py — the cutting room's dailies viewer (gate swe-cutting-room-views).

Deterministic views over a synthetic chronicle: biggest_moments ranks a durable high-magnitude beat
above flat ones, what_changed surfaces arc hinges, acquisitions_view lists what was learned, and
scene_index gives the shot list with cast. No LLM, no API. Script-style, exit 0 = all pass.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.ledger import Ledger                                 # noqa: E402
from src.engine.records import TurnCommit                            # noqa: E402
import cut                                                           # noqa: E402

AFF = {p: 0.5 for p in ("SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY", "DISGUST")}
FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _commit(led, run_id, turn, actor, action, tags):
    led.append_turn(TurnCommit(run_id=run_id, turn=turn, actor=actor, thought="", action=action,
                               tags=tags, affect=dict(AFF), condition={}, events=[], validation={}))


def main():
    print("test_cut.py — cutting room dailies viewer\n")
    led = Ledger(os.path.join(tempfile.mkdtemp(prefix="cut_"), "chronicle.db"))
    led.create_run("r", {"catalog_version": 1})
    led.register_character("r", "corin", {"name": "Corin"}, {})
    led.register_character("r", "arden", {"name": "Arden"}, {})

    _commit(led, "r", 0, "corin", "passes the bread", {"type": "mundane", "dimensions": {"mastery": 0.1}, "durability": "transient"})
    _commit(led, "r", 1, "corin", "refuses, his voice gone hard", {"type": "affront", "dimensions": {"social_violation": 0.8}, "durability": "durable"})
    _commit(led, "r", 2, "arden", "a quiet remark over the soup", {"type": "care", "dimensions": {"care_relevant": 0.3}, "durability": "transient"})
    led.append_arc_diff("r", "corin", 1, {"temperament": {"RAGE": 0.05}, "_meta": {"dominant": "RAGE", "impact": 0.42}})
    led.append_acquisition("r", "corin", 1, {"claim": "Father will not bend on the worker", "provenance": "lived"})
    led.append_scene("r", 0, "dinner", "corin", 0, 2)

    # biggest_moments: the durable social_violation 0.8 (+0.3 durable = 1.1) ranks first; flat mundane last
    bm = cut.biggest_moments(led, "r")
    check("biggest-ranks-durable-first", bm[0]["turn"] == 1 and abs(bm[0]["score"] - 1.1) < 1e-9, str(bm[0]))
    check("flat-mundane-ranks-low", bm[-1]["turn"] == 0 and bm[-1]["score"] < 0.5, str(bm[-1]))
    check("guardrail-not-a-cut", len(bm) == 3)  # all beats surfaced as candidates, none discarded

    # what_changed: the arc hinge
    wc = cut.what_changed(led, "r")
    check("arc-hinge-corin", "corin" in wc and wc["corin"][0]["dominant"] == "RAGE" and wc["corin"][0]["turn"] == 1, str(wc))

    # acquisitions: what was learned
    av = cut.acquisitions_view(led, "r")
    check("acquisition-listed", "corin" in av and av["corin"][0]["claim"].startswith("Father will not bend"), str(av))

    # scene_index: the shot list with cast
    si = cut.scene_index(led, "r")
    # cast comes back ORDER BY actor (cut.py:36) — alphabetical, not cast-declaration order
    check("scene-cast-and-length", si[0]["cast"] == ["arden", "corin"] and si[0]["n_turns"] == 3, str(si[0]))
    check("scene-pov", si[0]["pov"] == "corin")

    if FAILS:
        print("\ntest_cut: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_cut: OK (views rank/surface candidates; the engine shows, the discussion decides)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
