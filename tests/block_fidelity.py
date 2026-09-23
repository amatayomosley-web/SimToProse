#!/usr/bin/env python3
"""block_fidelity.py — does the block the engine hands an actor produce the state that block names?

THE QUESTION, and it is the production one. A run resolves a float to a rung and hands ONE block to
an actor (`rungs.rung_at` -> `rungs.block_for`). Nothing else reaches them: no ladder, no rung
number, no name, no frame. So the only thing that matters downstream is whether THAT block, alone,
produces a performance recognisable as the state it describes.

WHY THE EXISTING INSTRUMENTS DO NOT ANSWER IT. tests/blind_sort.py ranks BLOCKS against each other.
tests/perform_sort.py ranks PASSAGES against each other. Both are ORDINAL and both are comparative:
"DISPLEASURE recovered 9 of 9 exact on rungs 5,6,7" means passages written from those three blocks
come back ordered 5 < 6 < 7. It does NOT establish that the rung-7 passage reads as rung 7 rather
than as somewhere between 6 and 8. A ladder can be perfectly ordered and every block can be off by
two, and every ordinal test in this repo would pass.

THE TEST. An actor writes a passage from one block, seeing nothing else. A judge then sees that
passage and ALL of the path's blocks, and picks which one it was written from. Correct = the block
transmitted its state. Chance = 1/n.

MATCHING BLOCKS, NOT NAMES, is deliberate. The rung NAME is measured inert and is never delivered
(gen_rungs.py refuses a block carrying its [State:] label; identical violent text scored HIGHER
labelled `annoyance` than labelled `fury`). Asking "which of these names is it" would test the
naming, which is an authoring handle. Asking "which of these BLOCKS is it" tests the artifact the
engine actually ships.

WHAT A FAILURE MEANS, stated before any number exists so it cannot be fitted afterwards:
  high accuracy   the block transmits. The prompt gets the expected response.
  chance          the blocks are interchangeable to a reader — the ladder may still ORDER correctly
                  while no individual rung is recoverable, which is exactly the gap the ordinal
                  instruments cannot see.
  systematic bias confusions cluster (e.g. every passage matched one or two rungs low) — the ladder
                  transmits a state but not the one it is indexed at, and the bands are then wrong
                  rather than the prose.

    python tests/block_fidelity.py --path DISPLEASURE
    python tests/block_fidelity.py --path DISPLEASURE --dry     # stimuli only, no model calls

Local Ollama only. Results append to staging/block_fidelity_results.jsonl.
NOT named test_*.py: run_all.py discovers suites and this makes model calls.
"""
import argparse
import json
import os
import random
import re
import sys
import urllib.request
import uuid

RUN_ID = uuid.uuid4().hex[:8]   # stamped on every row: two runs must never merge silently

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

JUDGES = ["qwen2.5:14b", "gemma4:e4b"]
ACTOR = "qwen2.5:14b"
RESULTS = os.path.join(REPO, "staging", "block_fidelity_results.jsonl")

# One scene, held constant across every rung, so a confusion is about the BLOCK and never about the
# situation. Chosen to meet the four-case universality test's hardest corner: immobile, alone, with
# a cause that is not a person.
SCENES = {
    # A SCENE MUST BE ABLE TO HOST EVERY RUNG OF THE PATH IT TESTS. Learned the hard way on
    # 2026-09-07: DISPLEASURE rung 12 is TERMINAL MOTOR DISCHARGE, and the first run used a woman
    # who cannot get out of bed. The actor wrote the closest a paralysed body manages and both
    # judges scored it mid-ladder -- the SCENE failing, reported by me as the BLOCK failing.
    # Universality (can every rung be WRITTEN for this person) and hostability (can this person
    # PERFORM the peak) are different requirements. This dict is the second one.
    "alone":    ("a man alone in his own kitchen in the middle of the afternoon. He is on his feet, "
                 "nothing is stopping him moving, and there is nobody in the house"),
    "window":   ("a woman who has been confined to her bed for months and cannot get up. Through "
                 "the window beside the bed she can see the garden. Something is happening out "
                 "there that she can see and cannot reach"),
    # Other-directed paths need a second person IN THE ROOM or their peak cannot be performed at
    # all: there is no sacrifice, no protectiveness and no tenderness with nobody to spend them on.
    "other":    ("a woman sitting with her younger brother at his kitchen table. He came in twenty "
                 "minutes ago badly shaken by something he has not explained, and he is still here"),
    # DISGUST needs something GENUINELY REPELLENT that the person is free to expel. Assigning
    # DISTASTE the `other` scene was the third scene-error of this class in one day and it cost two
    # rungs. That scene is a woman with her distressed brother -- there is nothing foul in it, and
    # its pull is toward sympathy. Measured: rung 1 ("turn from it, without weight") produced an
    # actor who named the urge and then wrote "instead, I remain rooted to my chair, offering
    # silent support" -- a GOODWILL behaviour, because the scene asked for one. Rung 5 ("drive it
    # out, and everything it touched with it") produced the contamination SENSATION and BELIEF
    # correctly and then called the urge "futile", because you cannot expel your own brother from
    # his kitchen. Both judges scored what was written and were right both times.
    "foul":     ("a man alone in a room he has just moved into. He has pulled something out from "
                 "under the bed that has been there a long time, and it is on his hands. Nobody "
                 "else is in the building and nothing stops him doing whatever he likes with it"),
    # Wanting and wariness need an OBJECT and a THREAT respectively, present and unresolved.
    "object":   ("a man in a quiet gallery after closing. One object on the far wall has held him "
                 "there for an hour. Nobody is watching and nothing is stopping him approaching it"),
    "threat":   ("a woman alone in an unfamiliar house at night. Something moved downstairs a "
                 "moment ago. She is on her feet and the door is behind her"),
}

# WHICH SCENE EACH PATH IS TESTED IN. Chosen so the path's PEAK is physically performable.
PATH_SCENE = {
    "DISPLEASURE": "alone",    # peak is undirected discharge -- needs a body that can move
    "DEFLATION":   "alone",    # peak is hollowness -- needs nothing but a person and time
    "RECEPTIVITY": "object",   # needs something to be open TO; the peak is being taken over by it
    "GOODWILL":    "other",    # peak is sacrifice -- impossible with nobody to spend it on
    "SELF-REGARD": "other",    # needs someone to be regarded against
    "STIRRING":    "object",   # peak is fixation -- needs an object to fixate on
    "DISTASTE":    "foul",     # peak is contamination-and-expulsion -- needs something
                               # genuinely repellent that the person is FREE to drive out
    "WARINESS":    "threat",   # peak needs a threat that has not resolved
}

def _ollama(model, prompt, seed, num_predict=400):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False,
                       "options": {"temperature": 0.0, "seed": seed,
                                   "num_predict": num_predict}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r).get("response", "")


def actor_prompt(block, scene, delivery="isolated", second=None):
    """Build the actor's prompt.

    `isolated` was the first version and it is NOT how the engine delivers a block. It asks
    for third-person fiction and says "no more and no less extreme", which invites the writer
    to calibrate intensity — something the real prompt never asks for.

    `production` reproduces scripts/composer.py -> direction_for verbatim: second person, the
    block introduced as "Your state as you come into this moment", and the load-bearing
    disclaimer "it is not a list of actions and it does not tell you what to do. Act from it."
    A second block is attached under "Also true of you right now" exactly as direction_for
    does — the multi-state beat the composer's own rule 3 calls the single outcome the design
    exists to prevent, and which nothing had tested.
    """
    if delivery == "isolated":
        return (
            "You are writing one short passage of close third-person fiction.\n\n"
            "THE PERSON AND SITUATION: %s.\n\n"
            "THE STATE THEY ARE IN — write someone in exactly this state, no more and no "
            "less extreme:\n%s\n\n"
            "Write 90-130 words. Show the state through what they notice, what their body "
            "does, and what they want to do. Do NOT name the emotion. No dialogue.\n"
            "Write only the passage." % (scene, block))

    lead = ("Your state as you come into this moment. This is what is true inside you; it is "
            "not a list of actions and it does not tell you what to do. Act from it.\n\n%s"
            % block)
    also = ""
    if second:
        also = ("\n\nAlso true of you right now. This is what is true inside you; it is not "
                "a list of actions and it does not tell you what to do. Act from it.\n\n%s"
                % second)
    return (
        "You ARE this person. Be them, faithfully.\n\n"
        "WHO AND WHERE YOU ARE: %s.\n\n"
        "%s%s\n\n"
        "Write what you do and notice in this moment, 90-130 words, in your own voice. "
        "Do not name the emotion. No dialogue." % (scene, lead, also))


def impulse_of(block):
    """The block's stated Impulse — the PULL it is supposed to produce in the actor.

    This is the behavioural contract. Everything else in a block describes the state; the
    Impulse says what the person is moved to do. If the emotional path has one job, it is
    that the actor comes out of the prompt pulled THIS way."""
    m = re.search(r"\*\*The Impulse\.\*\*\s*(.+?)(?:\n\n|\Z)", block, re.S)
    return " ".join(m.group(1).split()) if m else None


def impulse_prompt(passage, impulse):
    """Does the passage show this pull? YES/NO, one impulse at a time.

    Deliberately NOT a ranking and NOT a multiple choice. Both of those measure whether the
    rungs are DISTINGUISHABLE, which is a different question from whether any one of them
    lands. A block can be perfectly distinguishable and still fail to move the actor."""
    return (
        "Read this passage.\n\n%s\n\n"
        "Now consider this description of what a person is pulled to do:\n%s\n\n"
        "Does the person in the passage act on, or clearly want, what that description "
        "says? Answer YES or NO and nothing else." % (passage, impulse))


def match_prompt(passage, blocks_shown):
    """`blocks_shown` is [(label, block_text), ...] — every rung on the path, permuted."""
    listing = "\n\n".join("[%s]\n%s" % (lab, txt) for lab, txt in blocks_shown)
    return (
        "Below is a PASSAGE, then %d STATE DESCRIPTIONS.\n\n"
        "PASSAGE:\n%s\n\n"
        "STATE DESCRIPTIONS:\n%s\n\n"
        "The passage was written to portray exactly ONE of these states. Which one?\n"
        "Answer with the single letter and nothing else." % (len(blocks_shown), passage, listing))


def run_impulse(path, blocks, scene, delivery, wanted, judges=None):
    """THE BEHAVIOURAL TEST. Does the block push the actor to act the way the block says?

    For each rung: the actor writes from the block (production delivery), then each judge is asked
    TWICE about that one passage —

        TRUE  does it show the pull this block actually names?      expect YES
        FOIL  does it show the pull a DISTANT rung's block names?   expect NO

    The foil is the whole point. "Did the actor do what the prompt said" scored alone is unfalsifiable:
    a judge inclined to say yes says yes to everything, and 100% would look like success. The gap
    between hit rate and false-positive rate is the only number here that means anything. A block
    that scores 90% true and 85% foil has not moved the actor at all; it has found an agreeable judge.
    """
    judges = judges or JUDGES
    n = len(blocks)
    rows, hit, hit_n, fp, fp_n = [], 0, 0, 0, 0
    for rung in wanted:
        passage = _ollama(ACTOR, actor_prompt(blocks[rung], scene, delivery),
                          seed=1000 + rung, num_predict=320).strip()
        true_imp = impulse_of(blocks[rung])
        foil_rung = rung + (6 if rung <= n // 2 else -6)
        foil_rung = max(1, min(n, foil_rung))
        foil_imp = impulse_of(blocks[foil_rung])
        for ji, judge in enumerate(judges):
            for kind, imp, want in (("true", true_imp, True), ("foil", foil_imp, False)):
                reply = _ollama(judge, impulse_prompt(passage, imp), seed=7 + ji, num_predict=8)
                said_yes = bool(re.search(r"YES", (reply or "").upper()))
                if kind == "true":
                    hit_n += 1; hit += 1 if said_yes else 0
                else:
                    fp_n += 1; fp += 1 if said_yes else 0
                rows.append({"run_id": RUN_ID, "path": path, "rung": rung, "judge": judge, "kind": kind,
                             "foil_rung": foil_rung if kind == "foil" else None,
                             "said_yes": said_yes, "expected": want, "impulse": imp,
                             "passage": passage})
        t = [r["said_yes"] for r in rows if r["rung"] == rung and r["kind"] == "true"]
        f = [r["said_yes"] for r in rows if r["rung"] == rung and r["kind"] == "foil"]
        print("  rung %2d  true %s   foil(%2d) %s" % (rung, "".join("Y" if x else "." for x in t),
                                                     foil_rung, "".join("Y" if x else "." for x in f)))
    print()
    print("  ACTED ON ITS OWN IMPULSE   %d/%d = %.0f%%" % (hit, hit_n, 100.0 * hit / hit_n))
    print("  ACCEPTED A DISTANT IMPULSE %d/%d = %.0f%%   <- false positives" % (fp, fp_n, 100.0 * fp / fp_n))
    print("  DISCRIMINATION (gap)       %+.0f points" % (100.0 * hit / hit_n - 100.0 * fp / fp_n))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="DISPLEASURE")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--scene", default="", choices=sorted(SCENES) + [""],
                    help="default: the scene PATH_SCENE picks for this path")
    ap.add_argument("--rungs", default="", help="comma list; default every rung")
    ap.add_argument("--delivery", default="isolated", choices=["isolated","production"])
    ap.add_argument("--mode", default="identify", choices=["identify","impulse"])
    ap.add_argument("--judges", default="",
                    help="comma list; widens n on a SHORT ladder. DISTASTE has 5 rungs, so "
                         "2 judges give only 10 judgments and one flip moves the hit rate "
                         "10 points -- too coarse to decide a 90% criterion on.")
    ap.add_argument("--second", type=int, default=0,
                    help="attach a SECOND block at this rung, as direction_for does for a "
                         "multi-state beat. The judge is still asked for the PRIMARY.")
    a = ap.parse_args()
    from src.engine.rung_blocks import BLOCKS
    blocks = BLOCKS[a.path]
    n = len(blocks)
    labels = "ABCDEFGHIJKLMNOP"[:n]

    wanted0 = [int(x) for x in a.rungs.split(',')] if a.rungs else sorted(blocks)
    if a.mode == 'impulse':
        print('=== %s  behavioural (impulse) test, delivery=%s, scene=%s ===' % (a.path, a.delivery, a.scene))
        rws = run_impulse(a.path, blocks, SCENES[a.scene or PATH_SCENE.get(a.path, 'alone')], a.delivery, wanted0,
                          [j.strip() for j in a.judges.split(',') if j.strip()] or None)
        with open(RESULTS.replace('.jsonl','_impulse.jsonl'), 'a', encoding='utf-8') as f:
            for r in rws: f.write(json.dumps(r) + chr(10))
        return
    rows, correct, total = [], 0, 0
    wanted = [int(x) for x in a.rungs.split(",")] if a.rungs else sorted(blocks)
    for rung in wanted:
        passage = None
        if a.dry:
            print("\n===== %s rung %d actor prompt =====\n%s" % (a.path, rung,
                                                                actor_prompt(blocks[rung], SCENES[a.scene or PATH_SCENE.get(a.path, 'alone')], a.delivery,
                                 blocks.get(a.second) if a.second else None)[:700]))
            continue
        passage = _ollama(ACTOR, actor_prompt(blocks[rung], SCENES[a.scene or PATH_SCENE.get(a.path, 'alone')], a.delivery,
                                 blocks.get(a.second) if a.second else None), seed=1000 + rung, num_predict=320).strip()
        if len(passage) < 120:
            print("  WARN  rung %2d: actor returned %d chars" % (rung, len(passage)))

        for ji, judge in enumerate(JUDGES):
            rng = random.Random(hash((a.path, rung, judge)) & 0xffff)
            order = sorted(blocks)
            rng.shuffle(order)
            shown = [(labels[k], blocks[r]) for k, r in enumerate(order)]
            truth_label = labels[order.index(rung)]
            reply = _ollama(judge, match_prompt(passage, shown), seed=7 + ji, num_predict=12)
            m = re.search(r"\b([A-%s])\b" % labels[-1], (reply or "").upper())
            got_label = m.group(1) if m else None
            got_rung = order[labels.index(got_label)] if got_label else None
            ok = (got_rung == rung)
            correct += 1 if ok else 0
            total += 1
            print("  rung %2d  %-14s -> %-2s  %s" % (rung, judge.split(":")[0],
                                                     got_rung if got_rung else "??",
                                                     "OK" if ok else ("off %+d" % (got_rung - rung)
                                                                      if got_rung else "unparsed")))
            rows.append({"path": a.path, "scene": (a.scene or PATH_SCENE.get(a.path, "alone")), "delivery": a.delivery, "second": a.second,
                         "rung": rung, "judge": judge, "got": got_rung,
                         "correct": ok, "passage": passage, "raw": (reply or "").strip()[:80]})
    if a.dry:
        return

    offs = [r["got"] - r["rung"] for r in rows if r["got"] is not None]
    print("\n=== %s ===" % a.path)
    print("  exact match: %d/%d = %.0f%%   (chance = 1/%d = %.0f%%)"
          % (correct, total, 100.0 * correct / total, n, 100.0 / n))
    if offs:
        print("  mean signed offset %+.2f   mean |offset| %.2f   within-1 %d/%d"
              % (sum(offs) / len(offs), sum(abs(o) for o in offs) / len(offs),
                 sum(1 for o in offs if abs(o) <= 1), len(offs)))
    with open(RESULTS, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("  wrote %s" % RESULTS)


if __name__ == "__main__":
    main()
