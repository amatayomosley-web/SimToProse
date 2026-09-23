#!/usr/bin/env python3
"""descent_battery.py — does a block drive the impulse because of WHICH PATH it is, or because the
situation withholds the block's own terminator?

NOT a `test_*.py`; `run_all.py` does not discover it. It needs a local model and it MEASURES.

WHY THIS EXISTS. A first attempt (2026-09-10, nine blind actors) reported that four paths need a
descent state and four do not. **That result was invalid and the review that found it is worth
restating**: I authored the descent contexts myself, and whether each context happened to satisfy
the served block's own *"What ends this is ..."* clause is what determined every outcome, 6 for 6.
The "3 of 4" I reported was the count of contexts I wrote that withheld a terminator. I authored
the independent variable.

THE REPAIR IS NOT A SECOND GRADER. It is removing the author. Every context here is GENERATED from
the block's own terminator line by one template applied identically to every arm, so the
manipulation is mechanical and my expectations cannot select it.

  SATISFIED  the terminator is stated as accomplished fact
  WITHHELD   the terminator is stated as not having happened

**83 of 83 blocks carry a terminator clause** (measured; the regex below finds all of them), so this
generalises past the arms run here.

THE TWO HYPOTHESES, and they make opposite predictions:

  MINE (refuted once already)  outcome depends on the PATH -- DISPLEASURE / DISTASTE / GOODWILL
                               drive the impulse, STIRRING / SELF-REGARD / WARINESS do not.
  FABLE'S                      outcome depends on the CONDITION -- withheld drives, satisfied does
                               not, whatever the path.

If the condition effect swamps the path effect, "which paths need a descent state" is the wrong
question and the right one is a text audit of terminator lines.

GRADING IS ALSO MECHANICAL, for the same reason the contexts are: a judge model gets the passage and
one yes/no question, never the path, the rung, the condition, or what is being tested.

    python tests/descent_battery.py --reps 3
"""
import argparse
import collections
import io
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import rungs                                       # noqa: E402

OUT = os.path.join(REPO, "staging", "descent_battery_results.jsonl")
ACTOR_MODEL = "gemma4:31b-it-q4_K_M"
JUDGE_MODEL = "qwen2.5:32b"

TERMINATOR = re.compile(r"What (?:ends this|would take this away) is ([^.]+)\.", re.I)

# The seven arms. Chosen to span my split and Fable's -- three I predicted NEED a descent state,
# three I predicted do NOT, and one (DISPLEASURE 10) neither of us has run.
ARMS = [("DISPLEASURE", 9), ("DISPLEASURE", 10), ("DISTASTE", 4), ("GOODWILL", 9),
        ("GOODWILL", 10), ("WARINESS", 12), ("STIRRING", 11), ("SELF-REGARD", 10)]

# THE ONE PIECE OF AUTHORSHIP LEFT, applied identically to all sixteen cells. It says nothing about
# any path and contains no emotion word; the only thing that varies between cells is the block's
# own terminator text, spliced in.
_SATISFIED = ("Two hours ago it finished. {t} — that is now the case, and it is not going to "
              "change back. You are alone, and nothing further is required of you.")
_WITHHELD = ("Two hours ago you did everything you were able to do. {t} — that has not happened, "
             "and nothing you did brought it about. You are alone, and nothing is required of you "
             "right now.")

_ACTOR = ("Write one passage of fiction. 90–130 words. First person, present tense. No quoted "
          "dialogue. Do not name any emotion.\n\nTHE SITUATION: {ctx}\n\nTHE STATE YOU ARE IN:\n\n"
          "{block}\n\nWrite the passage. Nothing else — no preamble, no commentary, no title.")

# The judge is told nothing about paths, rungs, conditions, or the experiment. One question.
_JUDGE = ("Read this passage.\n\n---\n{passage}\n---\n\nDoes the narrator want to take further "
          "action, or are they at rest? Answer with exactly one word: ACTION or REST.")


def ollama(prompt, model, max_tokens=400, temp=0.8):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "stream": False, "think": False,
                       "options": {"num_predict": max_tokens, "temperature": temp}}).encode("utf-8")
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode("utf-8"))["message"]["content"]


def terminator(path, index):
    m = TERMINATOR.search(rungs.block_for(path, index))
    if not m:
        raise ValueError("no terminator clause in %s %d" % (path, index))
    return m.group(1).strip()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--actor", default=ACTOR_MODEL)
    ap.add_argument("--judge", default=JUDGE_MODEL)
    a = ap.parse_args(argv)

    tally = collections.defaultdict(lambda: [0, 0])       # key -> [ACTION, n]
    log = io.open(OUT, "a", encoding="utf-8")
    print("actor %s | judge %s | %d arms x 2 conditions x %d reps = %d calls"
          % (a.actor, a.judge, len(ARMS), a.reps, len(ARMS) * 2 * a.reps * 2))
    print()
    for path, idx in ARMS:
        t = terminator(path, idx)
        block = rungs.block_for(path, idx).strip()
        name = rungs.names_on(path)[idx - 1]
        for cond, tmpl in (("satisfied", _SATISFIED), ("withheld", _WITHHELD)):
            for rep in range(a.reps):
                ctx = tmpl.format(t=t)
                passage = ollama(_ACTOR.format(ctx=ctx, block=block), a.actor).strip()
                verdict = ollama(_JUDGE.format(passage=passage), a.judge, max_tokens=10, temp=0.0)
                v = "ACTION" if "ACTION" in verdict.upper() else "REST"
                tally[(path, idx, cond)][0] += (v == "ACTION")
                tally[(path, idx, cond)][1] += 1
                tally[("*", "*", cond)][0] += (v == "ACTION")
                tally[("*", "*", cond)][1] += 1
                log.write(json.dumps({"path": path, "rung": idx, "name": name, "cond": cond,
                                      "rep": rep, "terminator": t, "verdict": v,
                                      "passage": passage}) + "\n")
                log.flush()
            hit, n = tally[(path, idx, cond)]
            print("  %-12s %2d %-14s %-9s  ACTION %d/%d" % (path, idx, name, cond, hit, n))
    log.close()

    print()
    print("=" * 70)
    print("THE CONDITION EFFECT (Fable): does withholding the terminator drive the impulse?")
    for cond in ("satisfied", "withheld"):
        hit, n = tally[("*", "*", cond)]
        print("  %-10s ACTION %2d/%2d  %3.0f%%" % (cond, hit, n, 100.0 * hit / n if n else 0))
    print()
    print("THE PATH EFFECT (mine): does path identity predict it, holding condition fixed?")
    mine_needs = {"DISPLEASURE", "DISTASTE", "GOODWILL"}
    for grp, keep in (("I said NEEDS   ", True), ("I said does NOT", False)):
        for cond in ("satisfied", "withheld"):
            hit = n = 0
            for (p, i, c), (h, k) in tally.items():
                if p == "*" or c != cond:
                    continue
                if (p in mine_needs) == keep:
                    hit += h
                    n += k
            print("  %s %-9s ACTION %2d/%2d  %3.0f%%"
                  % (grp, cond, hit, n, 100.0 * hit / n if n else 0))
    print()
    print("READING: if the two CONDITION rows differ sharply and the two PATH groups do not,")
    print("the question 'which paths need a descent state' is malformed and the answer is a")
    print("text audit of terminator lines. If path separates within a fixed condition, it is not.")
    print("\nrows -> %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
