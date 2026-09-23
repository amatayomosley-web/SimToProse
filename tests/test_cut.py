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

from src.engine import world_events                                  # noqa: E402
from src.engine.ledger import Ledger                                 # noqa: E402
from src.engine.records import Event, TurnCommit, PATHS              # noqa: E402
import cut                                                           # noqa: E402

# DERIVED from records.PATHS, never enumerated. A hand-written list of the set is the
# duplicate CLAUDE.md warns about, and on 2026-09-08 it broke in exactly that way: the
# sweep that rekeyed the old primitives to paths turned both SEEKING and LUST into
# STIRRING, so every literal silently became STIRRING three times with RECEPTIVITY and
# SELF-REGARD missing entirely.
AFF = {p: 0.5 for p in PATHS}
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
    led.register_character("r", "juno", {"name": "Juno"}, {})
    led.register_character("r", "zofia", {"name": "Zofia"}, {})

    _commit(led, "r", 0, "juno", "rolls the mats out along the rink", {"type": "mundane", "dimensions": {"mastery": 0.15}, "durability": "transient"})
    _commit(led, "r", 1, "juno", "tells the umpire, in front of the whole clubhouse, that he measured the last end in the other side's favour on purpose", {"type": "affront", "dimensions": {"social_violation": 0.7}, "durability": "durable"})
    _commit(led, "r", 2, "zofia", "asks quietly whether she wants to sit the next game out", {"type": "care", "dimensions": {"care_relevant": 0.25}, "durability": "transient"})
    led.append_arc_diff("r", "juno", 1, {"temperament": {"DISPLEASURE": 0.05}, "_meta": {"dominant": "DISPLEASURE", "impact": 0.38}})
    led.append_acquisition("r", "juno", 1, {"claim": "The finals are played on the top rink every Saturday in August", "provenance": "lived"})
    led.append_scene("r", 0, "bowling-green", "juno", 0, 2)

    # biggest_moments: the durable social_violation 0.7 (+0.3 durable = 1.0) ranks first; flat mundane last
    bm = cut.biggest_moments(led, "r")
    check("biggest-ranks-durable-first", bm[0]["turn"] == 1 and abs(bm[0]["score"] - 1.0) < 1e-9, str(bm[0]))
    check("flat-mundane-ranks-low", bm[-1]["turn"] == 0 and bm[-1]["score"] < 0.5, str(bm[-1]))
    check("guardrail-not-a-cut", len(bm) == 3)  # all beats surfaced as candidates, none discarded

    # what_changed: the arc hinge
    wc = cut.what_changed(led, "r")
    check("arc-hinge-juno", "juno" in wc and wc["juno"][0]["dominant"] == "DISPLEASURE" and wc["juno"][0]["turn"] == 1, str(wc))

    # acquisitions: what was learned
    av = cut.acquisitions_view(led, "r")
    check("acquisition-listed", "juno" in av and av["juno"][0]["claim"].startswith("The finals are played on the top rink"), str(av))

    # scene_index: the shot list with cast
    si = cut.scene_index(led, "r")
    # cast comes back ORDER BY actor (cut.py:36) — alphabetical, not cast-declaration order
    check("scene-cast-and-length", si[0]["cast"] == ["juno", "zofia"] and si[0]["n_turns"] == 3, str(si[0]))
    check("scene-pov", si[0]["pov"] == "juno")

    # THE CORRECTED MARKER (2026-09-19) — consolidation-loop.md open-q 3's consumer half: "the cut
    # treats corrected events as superseded". The CONTROL first: a run that has never been
    # corrected must carry no marker anywhere, because the dailies gained these fields for every
    # run and a view that always shows a correction line is a view nobody reads.
    check("clean-run-has-no-corrected-turns", cut.corrected_turns(led, "r") == {}, str(cut.corrected_turns(led, "r")))
    check("clean-run-scenes-carry-an-empty-marker-list", si[0]["corrected"] == [], str(si[0]["corrected"]))
    check("clean-run-dailies-carry-an-empty-map", cut.dailies(led, "r")["corrected"] == {})

    world_events.append(led, "r", 2, [Event(type="move", actor="zofia", payload={"to": "the-mower-shed"})])
    moved = led.con.execute("SELECT event_id FROM events WHERE run_id='r' AND type='move'").fetchone()[0]
    world_events.append(led, "r", 3, [Event(
        type="correction", actor="zofia", visibility="private-to-actor",
        payload={"supersedes": [moved], "turn": 2, "issue": "the mower shed stayed locked until the groundsman came",
                 "source": "critic"})])

    marks = cut.corrected_turns(led, "r")
    check("the-flagged-turn-is-marked", list(marks) == [2], str(marks))
    check("...with-the-critic's-words", marks[2] == "the mower shed stayed locked until the groundsman came", str(marks))
    si2 = cut.scene_index(led, "r")
    check("the-scene-carries-the-marker",
          si2[0]["corrected"] == ["t2 corrected: the mower shed stayed locked until the groundsman came"], str(si2[0]["corrected"]))
    check("dailies-carry-the-map", cut.dailies(led, "r")["corrected"] == {2: "the mower shed stayed locked until the groundsman came"},
          str(cut.dailies(led, "r")["corrected"]))
    check("the-beat-itself-is-still-in-the-dailies",     # append-only: the cut still sees the turn
          any(m["turn"] == 2 for m in cut.dailies(led, "r")["biggest_moments"]))

    if FAILS:
        print("\ntest_cut: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_cut: OK (views rank/surface candidates; the engine shows, the discussion decides)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
