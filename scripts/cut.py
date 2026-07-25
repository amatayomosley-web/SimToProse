#!/usr/bin/env python3
"""cut.py — the cutting room's DAILIES VIEWER (cutting-room.md, the views half).

cutting-room.md is explicit (William, 2026-06-10): the shape is NOT a pipeline. The engine owns the
VIEWS and the CHECKS; the DISCUSSION (director + editor) owns the choices, recorded in an EDL. This
module is the views half only — deterministic queries over the recorded chronicle that make a
discussion of many scenes possible. The engine SHOWS; it never decides. Automated selection is
DELIBERATELY not built (automating taste we haven't formed yet would calibrate gates against nothing).

Guardrail the views inherit: magnitude is consequence, not meaning — the quiet scene that carries
the book may be numerically flat. These surface CANDIDATES for the discussion, never the cut.

Usage:
  python scripts/cut.py --vault "<book>" --run <run_id>          # print the dailies
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.ledger import Ledger                                 # noqa: E402

_DURABLE = ("durable", "marking", "reshaping")


def scene_index(led, run_id):
    """The shot list: each recorded scene with its cast (distinct actors in its turn range) + length.
    The atoms are free — the runtime already segments into scenes (cutting-room.md)."""
    out = []
    for s in led.scenes_for(run_id):
        cast = [r["actor"] for r in led.con.execute(
            "SELECT DISTINCT actor FROM turns WHERE run_id=? AND turn BETWEEN ? AND ? ORDER BY actor",
            (run_id, s["start_turn"], s["end_turn"]))]
        out.append(dict(s, cast=cast, n_turns=s["end_turn"] - s["start_turn"] + 1))
    return out


def _salience(tags):
    """A beat's dramatic-salience CANDIDATE score: the largest appraisal-dimension magnitude this turn,
    plus a bonus if the beat was durable (it marked someone). Consequence, not meaning (the guardrail)."""
    if not isinstance(tags, dict):
        return 0.0
    dims = tags.get("dimensions", {}) or {}
    mag = max([abs(float(v)) for v in dims.values() if isinstance(v, (int, float))] or [0.0])
    return round(mag + (0.3 if str(tags.get("durability", "transient")) in _DURABLE else 0.0), 3)


def biggest_moments(led, run_id, top=8):
    """Beats ranked by salience candidate-score (desc). 'What were the biggest moments?' — the views
    surface candidates; the discussion recognizes meaning."""
    rows = led.con.execute(
        "SELECT turn, actor, action, tags FROM turns WHERE run_id=? ORDER BY turn", (run_id,)).fetchall()
    scored = []
    for r in rows:
        tags = json.loads(r["tags"])
        scored.append({"turn": r["turn"], "actor": r["actor"], "action": str(r["action"]).replace("\n", " ")[:140],
                       "score": _salience(tags), "type": tags.get("type", "?"),
                       "durability": tags.get("durability", "transient")})
    scored.sort(key=lambda x: (x["score"], -x["turn"]), reverse=True)
    return scored[:top]


def what_changed(led, run_id):
    """'What changed this person?' — arc-engine baseline diffs (the trauma/growth hinges of a life,
    by construction), per character in turn order."""
    rows = led.con.execute(
        "SELECT char_id, turn, diff FROM arc_diffs WHERE run_id=? ORDER BY char_id, turn", (run_id,)).fetchall()
    out = {}
    for r in rows:
        meta = json.loads(r["diff"]).get("_meta", {})
        out.setdefault(r["char_id"], []).append(
            {"turn": r["turn"], "dominant": meta.get("dominant"), "impact": meta.get("impact")})
    return out


def acquisitions_view(led, run_id):
    """'What was learned?' — vault acquisitions (secrets learned, names told, lived memories) per
    character in turn order (knowledge-model.md)."""
    rows = led.con.execute(
        "SELECT char_id, turn, belief FROM acquisitions WHERE run_id=? ORDER BY char_id, turn, acquisition_id",
        (run_id,)).fetchall()
    out = {}
    for r in rows:
        b = json.loads(r["belief"])
        out.setdefault(r["char_id"], []).append(
            {"turn": r["turn"], "claim": str(b.get("claim", ""))[:120], "provenance": b.get("provenance")})
    return out


def dailies(led, run_id, top=8):
    """The whole dailies bundle, for the cutting discussion."""
    return {"scenes": scene_index(led, run_id), "biggest_moments": biggest_moments(led, run_id, top),
            "what_changed": what_changed(led, run_id), "acquisitions": acquisitions_view(led, run_id)}


def main():
    ap = argparse.ArgumentParser(description="the cutting room's dailies viewer — deterministic views for the cut discussion")
    ap.add_argument("--vault", required=True, help="the BOOK folder (vault)")
    ap.add_argument("--run", required=True, help="run_id to view")
    ap.add_argument("--db", default=None, help="chronicle db path (default <vault>/runs/<book>.db)")
    ap.add_argument("--top", type=int, default=8, help="how many biggest-moment candidates to show")
    args = ap.parse_args()

    from src.engine.vault import load_book
    _world, _chars = load_book(args.vault)
    book_name = os.path.basename(os.path.normpath(args.vault)).lower().replace(" ", "-")
    led = Ledger(args.db or os.path.join(args.vault, "runs", "%s.db" % book_name))
    d = dailies(led, args.run, args.top)

    print("=== DAILIES: run %s ===\n" % args.run)
    print("SCENES (the shot list):")
    for s in d["scenes"]:
        print("  [%d] %-16s turns %d-%d  cast: %s  pov=%s"
              % (s["scene_no"], s["label"], s["start_turn"], s["end_turn"], ", ".join(s["cast"]), s["pov"]))
    print("\nBIGGEST MOMENTS (candidates — magnitude is consequence, not meaning):")
    for m in d["biggest_moments"]:
        print("  %.3f  [t%d] %-9s %-8s %s" % (m["score"], m["turn"], m["actor"], m["type"], m["action"]))
    print("\nWHAT CHANGED (arc hinges):")
    for char, hinges in d["what_changed"].items():
        print("  %s: %s" % (char, ", ".join("t%d %s(%.2f)" % (h["turn"], h["dominant"], h["impact"] or 0.0) for h in hinges)))
    print("\nWHAT WAS LEARNED (acquisitions):")
    for char, acqs in d["acquisitions"].items():
        for a in acqs:
            print("  %s [t%d, %s]: %s" % (char, a["turn"], a["provenance"], a["claim"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
