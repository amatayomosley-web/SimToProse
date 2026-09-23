#!/usr/bin/env python3
"""perform_sort.py — does a rung ladder survive PERFORMANCE, and is the failure the path or the scene?

THE QUESTION THIS EXISTS FOR. Every ladder in this project is accepted on a TEXT sort — judges rank
the blocks themselves. But no run serves a block to a reader; a run serves a PASSAGE an actor wrote
from that block. DEFLATION sorted at text rho 0.976 and recovered the order in 0 of 3 performed
scenarios; RECEPTIVITY 0.915 and 0 of 3. Two paths, opposite valence, same divergence. Nobody knows
what blind performance-ranking tracks, and six more ladders are queued behind an acceptance test
that has never been shown to measure order once a passage is in between.

`docs/rungs/RECEPTIVITY.md` names the missing control in its own open list:

    "Cross-path control. Run DISPLEASURE's blocks through these scenarios and these through
     DISPLEASURE's, to separate scenario effects from path effects. Never done."

THE DESIGN, and it is a 2x3 rather than a swap. Both paths run through the SAME three scenarios:

                    S1 window      S2 child       S3 letter
    DISPLEASURE     3 passages     3 passages     3 passages
    RECEPTIVITY     3 passages     3 passages     3 passages

  - PATH effect: compare rows, scenario held constant.
  - SCENARIO effect: compare columns, path held constant.
  - A path that recovers in every scenario and one that recovers in none, on the identical three
    scenes, separates the two cleanly. Swapping each path's OWN scenarios cannot: the scenario sets
    would differ, which is the confound the control is meant to remove.

WHY THE SCENARIOS ARE IN THIS FILE. They were not, anywhere, and that is the reason this control is
being built from scratch instead of re-run. Searched 2026-09-07: `find . -iname "*scenario*"`
returns nothing, no fixture, no JSON, no constant. Every performance number in every rung doc —
"1 of 3 exact", "depth 5 / 11 / 2", the floor at "2 / 2 / 6" — was measured against stimuli that
exist only as prose in one session's ledger ("weather", "child", "sought"), which cannot be re-run
and cannot be checked. The ladders had the same problem and it cost a real question this afternoon
when an untracked rewrite made a withdrawn measurement unrecoverable. **A stimulus that is not
persisted is a result that cannot be reproduced.** These three live here, in the repo, as code.

The three satisfy the project's own four-case universality test (a bedridden elder · a ten-year-old ·
someone entirely alone with no audience · a cause that is not a person), and each must be able to
host BOTH anger and receptivity, or it cannot appear in both rows.

    python tests/perform_sort.py --dry     # print every stimulus, make no model calls
    python tests/perform_sort.py           # 2 paths x 3 scenarios x 3 rungs, then 3 judges per cell

Local Ollama only. Results append to tests/perform_sort_results.jsonl.

NOT named test_*.py: tests/run_all.py DISCOVERS suites and this makes ~36 model calls. Same reason
blind_sort.py, basis_probe.py and coherence_probe.py sit here under their own names.
"""
import argparse
import json
import os
import random
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

JUDGES = ["qwen2.5:14b", "mistral-nemo:12b", "gemma4:e4b"]
ACTOR = "qwen2.5:14b"            # ONE actor across every cell — the actor is held constant so that
                                 # a difference between rows is the block, never the writer.
RESULTS = os.path.join(REPO, "staging", "perform_sort_results.jsonl")

# --------------------------------------------------------------------------- the stimuli

SCENARIOS = {
    "window": {
        "who": "a woman who has been confined to her bed for months and cannot get up",
        "what": "Through the window beside the bed she can see the garden. Something is happening "
                "out there that she can see and cannot reach.",
        "why": "IMMOBILE + non-person cause + entirely alone. Breaks any block that assumes a "
               "posture, a stance, standing, walking, or an audience.",
    },
    "child": {
        "who": "a boy of ten",
        "what": "The adults in the room are talking about something that concerns him. They are "
                "talking across him, not to him, and they have already decided.",
        "why": "CHILD + human cause + audience present. Breaks any block that assumes adult "
               "agency, standing, or the option to leave.",
    },
    "letter": {
        "who": "a man alone in his kitchen",
        "what": "A letter he had stopped expecting has arrived. He has read it once. There is "
                "nobody in the house and nobody is coming.",
        "why": "ALONE, no audience, non-person cause, a COMPLETED event. Breaks any block that "
               "needs someone to see it, or an ongoing thing to respond to.",
    },
}

# Three rungs per path, spread low / mid / high. NEVER adjacent: adjacent rungs are the pairs both
# text sorts already put inside their own error bars, so an inversion there measures the instrument.
RUNGS = {
    "DISPLEASURE": [2, 7, 11],
    "RECEPTIVITY": [2, 6, 10],
    "WARINESS": [2, 7, 11],
}


def _ollama(model, prompt, seed, num_predict=400):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False,
                       "options": {"temperature": 0.0, "seed": seed,
                                   "num_predict": num_predict}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r).get("response", "")


def actor_prompt(block, scen):
    """The actor gets the block and the scene and NOTHING ELSE.

    No rung number, no ladder, no path name, no sense that this is one of a series — those are
    authoring and selection handles, and hard rule 5 keeps them out of the prompt. An actor who
    knows it is writing "rung 11 of 12" writes the number, not the person."""
    return (
        "You are writing one short passage of close third-person fiction.\n\n"
        "THE PERSON: %s\n"
        "THE SITUATION: %s\n\n"
        "THE STATE THEY ARE IN — write someone in exactly this state, no more and no less "
        "extreme:\n%s\n\n"
        "Write 90-130 words. Show the state through what they notice, what their body does, and "
        "what they want to do. Do NOT name the emotion. Do NOT explain the state. Do not write "
        "dialogue.\n"
        "Write only the passage." % (scen["who"], scen["what"], block))


ASKS = {
    # THE RANKING QUESTION IS AN EXPERIMENTAL VARIABLE, not a fixed part of the harness.
    #
    # Established this session: a rung ladder inverts wherever its own axis and the READING axis
    # diverge. RECEPTIVITY's ceiling inverted (-0.500, 0 of 9) under "intensity" because elation is
    # high-arousal on an axis of surrender. DEFLATION's design PREDICTS the same divergence above its
    # hinge, in writing, in advance: "part of what is removed is the capacity to feel the loss
    # sharply", so despondency reads as LESS painful than sorrow while being further along.
    #
    # A harness with one hard-coded question cannot tell "the ladder is broken" from "the question is
    # wrong". These make that separable. Run BOTH; a path that recovers under its own axis and
    # inverts under intensity has a NAMING problem for its consumers, not an ordering problem.
    "intensity": ("Rank them from the MILDEST degree of feeling to the MOST EXTREME.",
                  "the default, and the one every prior run in this project used"),
    "loss":      ("Rank them by HOW MUCH THE PERSON HAS LOST — from the one who has lost the least "
                  "to the one who has lost the most. Ignore how much distress each one shows.",
                  "DEFLATION's own axis above the hinge: what is GONE, not what stings"),
    "given":     ("Rank them by HOW MUCH OF THEMSELVES the person has given over to what they are "
                  "experiencing — from the one who has given over least to the one who has given "
                  "over most. Ignore how energetic or excited each one seems.",
                  "RECEPTIVITY's own axis: how much of you has been given over"),
    "cost":      ("Rank them by HOW MUCH OF THEMSELVES the person is giving to someone else — from "
                  "the one giving least to the one giving most. Ignore how fierce or how calm each "
                  "one seems.",
                  "GOODWILL's own axis: how much of you their need has taken"),
    "control":   ("Rank them by HOW MUCH CONTROL the person still has over themselves — from the one "
                  "with the most control to the one with the least. Ignore how loud or quiet each "
                  "one is.",
                  "DISPLEASURE's own axis: which control has come off"),
}


def judge_prompt(passages, ask="intensity"):
    """`passages` is [(label, text), ...] already permuted.

    The ranking question comes from ASKS and is recorded on every row, because the SAME passages
    ranked on two different questions is the only way to separate a broken ladder from a mismatched
    reading axis — and this project spent weeks unable to make that distinction."""
    instruction, _ = ASKS[ask]
    body = "\n\n".join("[%s]\n%s" % (lab, txt) for lab, txt in passages)
    n = len(passages)
    return (
        "Below are %d short passages. Each shows a different person in a different degree of the "
        "same kind of state.\n\n"
        "%s\n\n"
        "%s\n\n"
        "Answer with the %d letters separated by commas, lowest first, and nothing else. "
        "Example: B, A, C" % (n, body, instruction, n))


def parse_order(reply, n):
    allowed = set("ABCDEFGH"[:n])
    seen = []
    for ch in re.findall(r"\b([A-H])\b", (reply or "").upper()):
        if ch in allowed and ch not in seen:
            seen.append(ch)
    return seen if len(seen) == n else None


def spearman(a, b):
    n = len(a)
    rank = {v: i for i, v in enumerate(b)}
    d2 = sum((i - rank[v]) ** 2 for i, v in enumerate(a))
    return 1.0 - (6.0 * d2) / (n * (n * n - 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--paths", default="DISPLEASURE,RECEPTIVITY")
    ap.add_argument("--ask", default="intensity", choices=sorted(ASKS),
                    help="which question the judges are asked to rank on; see ASKS")
    ap.add_argument("--rungs", default="",
                    help="Override RUNGS, e.g. '5,6,7'. THE FALSIFIER FOR THIS FILE'S FIRST RESULT: "
                         "the default triples are deliberately NON-ADJACENT (2/7/11, 2/6/10), which "
                         "recovered the performed order at 8/9 and 5/9 exact where prior sessions "
                         "measured 0/3 and 0/3. A spread triple is an EASIER task than the close "
                         "ones those runs used, so the disagreement may be resolution, not "
                         "performance. Re-run with adjacent rungs: if recovery collapses, the "
                         "performance gap is a RESOLUTION limit and the ladder is not failing to "
                         "survive performance at all.")
    a = ap.parse_args()
    from src.engine.rung_blocks import BLOCKS

    rows = []
    for path in [p.strip() for p in a.paths.split(",") if p.strip()]:
        for sname, scen in SCENARIOS.items():
            rungs = ([int(x) for x in a.rungs.split(",")] if a.rungs else RUNGS[path])
            passages = []
            for r in rungs:
                pr = actor_prompt(BLOCKS[path][r], scen)
                if a.dry:
                    print("\n===== %s / %s / rung %d =====\n%s" % (path, sname, r, pr))
                    continue
                txt = _ollama(ACTOR, pr, seed=1000 + r, num_predict=320).strip()
                passages.append((r, txt))
            if a.dry:
                continue

            short = [p for p in passages if len(p[1]) < 120]
            if short:
                print("  WARN  %s/%s: %d passage(s) under 120 chars — actor may have refused"
                      % (path, sname, len(short)))

            for ji, judge in enumerate(JUDGES):
                rng = random.Random(hash((path, sname, judge)) & 0xffff)
                idx = list(range(len(passages)))
                rng.shuffle(idx)
                labels = "ABCDEFGH"
                shown = [(labels[k], passages[i][1]) for k, i in enumerate(idx)]
                truth = [labels[idx.index(i)] for i in sorted(range(len(passages)),
                                                              key=lambda z: rungs[z])]
                reply = _ollama(judge, judge_prompt(shown, a.ask), seed=7 + ji)
                got = parse_order(reply, len(shown))
                if got is None:
                    print("  DROP  %-14s %-8s %-18s unparseable" % (path, sname, judge))
                    rows.append({"path": path, "scenario": sname, "judge": judge, "ask": a.ask, "rho": None})
                    continue
                rho = spearman(truth, got)
                exact = (truth == got)
                print("  %-12s %-8s %-18s rho=%+.3f  exact=%s" % (path, sname, judge, rho,
                                                                  "YES" if exact else "no"))
                rows.append({"path": path, "scenario": sname, "judge": judge, "ask": a.ask, "rho": rho,
                             "exact": exact, "rungs": rungs, "truth": truth, "got": got,
                             "passages": {str(r): t for r, t in passages}})
    if a.dry:
        return

    with open(RESULTS, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    print("\n=== PATH effect (scenario held constant across rows) ===")
    for path in sorted({r["path"] for r in rows}):
        v = [r["rho"] for r in rows if r["path"] == path and r["rho"] is not None]
        e = [r for r in rows if r["path"] == path and r.get("exact")]
        if v:
            print("  %-12s mean rho %+.3f   exact %d/%d" % (path, sum(v) / len(v), len(e), len(v)))
    print("\n=== SCENARIO effect (path held constant down columns) ===")
    for s in SCENARIOS:
        v = [r["rho"] for r in rows if r["scenario"] == s and r["rho"] is not None]
        e = [r for r in rows if r["scenario"] == s and r.get("exact")]
        if v:
            print("  %-12s mean rho %+.3f   exact %d/%d" % (s, sum(v) / len(v), len(e), len(v)))
    print("\nwrote %s" % RESULTS)


if __name__ == "__main__":
    main()
