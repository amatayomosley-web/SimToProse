#!/usr/bin/env python3
"""appraiser_bakeoff.py — what job can each seat actually do?

NOT a `test_*.py`, so `run_all.py` does not discover it. It needs a local model and it MEASURES
rather than asserts, mirroring `tests/perform_sort.py` and `tests/blind_sort.py`.

THE QUESTION, in the owner's words (2026-09-09): *"Build the dual appraisers, see what jobs each can
do."* Two seats were built on an ARGUMENT — that the emotion seat must read the character's private
thought and the event seat must not, because dimensions are what a bystander made of the act. That
argument is a priori. This is the measurement that can refute it.

THE COMPARISON, and it is the honest one because both routes end in the same place. The engine needs
one thing from a beat: **which rung is this character at on which path.** There are two roads to it:

    TODAY   passage -> event seat -> dimensions -> state._DIM_TO_PATH -> a float -> rung_at -> RUNG
    NEW     passage -> emotion seat -> a reading -------------------------------------------> RUNG

Same passages, same ground truth, same scoring. A route that cannot land on the right rung is not
doing the job, whatever else it produces.

THE CORPUS IS ALREADY ON DISK and was not built for this, which is what makes it a fair test:
`staging/block_fidelity_results_impulse.jsonl`, 542 valid rows across all eight paths, each a
first-person passage written FROM a known rung by an actor that was never told this measurement
would happen. Ground truth is the rung the passage was generated from.

THE THIRD ARM IS THE ONE THAT MATTERS MOST AND IS EASIEST TO SKIP. `--idle` measures `p`, the rate
at which a seat reports something on a beat where nothing arose. `docs/emotion-arithmetic.md` §8
REQUIRES p <= 0.2 and it has never been measured for any model. It is not an accuracy statistic: at
retention 0.95 a sensor with p above ~0.27 drives every character to saturation on its own, with no
event in the world. A seat that is accurate and chatty is worse than one that is vague and quiet.

    python tests/appraiser_bakeoff.py --n 40 --model gemma4:31b-it-q4_K_M
    python tests/appraiser_bakeoff.py --idle --n 30
"""
import argparse
import collections
import io
import json
import os
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import appraiser                                                   # noqa: E402
from src.engine import rungs                                       # noqa: E402
from src.engine.severity import normalise_dimensions               # noqa: E402
from src.engine.state import _DIM_TO_PATH                          # noqa: E402

CORPUS = os.path.join(REPO, "staging", "block_fidelity_results_impulse.jsonl")
OUT = os.path.join(REPO, "staging", "appraiser_bakeoff_results.jsonl")
DEFAULT_MODEL = "anthropic/claude-opus-5"   # the seats' model (scripts/provider.py); pass a bare gemma name for the local baseline

# Beats where NOTHING AROSE. Hand-written rather than drawn from the corpus, because every corpus
# passage was generated FROM a rung and therefore has something in it by construction. A false-
# positive rate measured on passages that all contain a real signal is not a false-positive rate.
IDLE_BEATS = [
    ("I check the hinge on the shed door and it holds. The wind has dropped since morning.",
     "It will need oiling before the season turns."),
    ("I count the chairs against the booking form and the numbers agree. I tick the form and set it down.",
     "Forty-one. The same as last week."),
    ("I walk the length of the yard and back, because my legs were stiff from sitting.",
     "The stones are uneven near the back step. They always were."),
    ("I pour the water off and set the pot on the ledge to cool.",
     "It will keep until evening."),
    ("She says the cart comes Thursday. I say that I heard the same.",
     "Thursday, then."),
    ("I put my coat on the hook where it goes and push the door shut behind me.",
     "Colder than it looked from inside."),
    ("I read the timetable twice to be sure I had the right bus, and I had.",
     "The twenty past. Fine."),
    ("He asks whether the shop is still open and I tell him it is.",
     "It was open when I passed, and she never shuts early."),
    ("I sharpen the kitchen knife until it catches the light evenly along the edge.",
     "That will do for the week."),
    ("I sit down where I always sit and wait for the others to arrive.",
     "Early, as usual."),
    # twenty more (2026-09-11), so `--n 30` is thirty DISTINCT prompts: the replay backend keys an
    # answer on the prompt, and one agent per prompt is the measurement.
    ("I fold the cloth in four and lay it on the shelf with the others.",
     "That is the last of them."),
    ("I ask the woman at the bus stop the time and she tells me, and I thank her.",
     "Later than I thought, but not by much."),
    ("I lead the horse to the trough and it drinks, and I wait for it.",
     "It drinks slowly in the cold."),
    ("I sweep the step and the dust goes off the edge into the yard.",
     "It will want doing again by Sunday."),
    ("We walk to the end of the lane together and part where the road forks.",
     "She goes left, as she always does."),
    ("I turn the page and the next one is another recipe, in the same hand.",
     "My grandmother had a steady hand."),
    ("I hang the tea towel over the rail by the stove to dry.",
     "It will be dry by morning."),
    ("I wind the clock on the mantel and set it by the wireless.",
     "Two minutes slow, as it always is."),
    ("I stack the plates and carry them through and set them by the basin.",
     "Six. One is chipped, the old one."),
    ("I wait at the counter while the woman weighs the flour.",
     "Two pounds, near enough."),
    ("I draw the curtains on the south side because the sun is on them now.",
     "The room is cooler already."),
    ("I walk the fence line to the corner post and it stands as it did.",
     "No need to bring the mallet."),
    ("She asks if I want tea and I say I do, and she puts the kettle on.",
     "The good cups today."),
    ("I stack the clean jars upside down on the drainer to dry.",
     "Eight, and the chutney will need ten."),
    ("I sit on the bench outside until the bell goes, then I go in.",
     "On time, then."),
    ("I put the letters on the shelf in the order they came and square the pile.",
     "Nothing that needs an answer today."),
    ("The girl brings the pail and I tip it into the barrel and give it back.",
     "Half full. One more will do."),
    ("I check the knots on the tarpaulin and pull one tighter.",
     "It held through the last wind. It will hold."),
    ("I read the next page of the almanac while the bread proves.",
     "Frost expected on the twentieth, it says."),
    ("We stand at the window and watch the cart go by, then go back to the table.",
     "The baker's cart. Thursday, as he said."),
]


def ask(messages, model, max_tokens=700):
    """ONE dispatcher (2026-09-11). A local name (`ollama/...` or a bare `gemma4:...`) goes to
    Ollama for the comparison baseline; anything with a provider prefix goes through THE seam,
    scripts/provider.py, on the frontier model — the owner's ruling for the seats. `--idle` on
    the frontier model is the p measurement that has never been made for any model."""
    if model.startswith("ollama/"):
        return ollama(messages, model[len("ollama/"):], max_tokens)
    if "/" not in model and not model.startswith("subagent:"):
        return ollama(messages, model, max_tokens)
    import provider as _provider
    return _provider.call(messages, model, "bakeoff", max_tokens=max_tokens)


def ollama(messages, model, max_tokens=700):
    """One call. `think=False` and a bounded reply, per basis_probe's finding: gemma4 spent its
    budget thinking and returned empty 55 of 162 times before the flag was set."""
    body = json.dumps({
        "model": model, "messages": messages, "stream": False, "think": False,
        "options": {"num_predict": max_tokens, "temperature": 0.3},
    }).encode("utf-8")
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode("utf-8"))["message"]["content"]


def dimensions_to_rung(tags, path):
    """The route the engine uses TODAY: dimensions -> pushes -> a float -> a rung.

    Scored from a FLOOR of 0.0 rather than from a character's current state, because the corpus
    passage is the whole of the evidence and there is no character behind it. That is generous to
    this arm -- it is the cleanest possible reading of the dimension route -- and it is the right
    generosity, because the question is what the route CAN do, not what it does on a bad day.
    """
    dims = normalise_dimensions(dict(tags)).get("dimensions", {})
    total = 0.0
    for dim, mag in dims.items():
        for p, w in _DIM_TO_PATH.get(dim, []):
            if p == path and w > 0:
                total += w * float(mag)
    total = max(0.0, min(1.0, total))
    return rungs.rung_at(path, total)[0]


def load_corpus(n, seed_paths=None):
    """Unique passages with known (path, rung). Deduped: the corpus repeats each passage per judge."""
    seen, rows = set(), []
    for line in io.open(CORPUS, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("INVALID") or r.get("kind") != "true":
            continue
        key = (r["path"], r["rung"], r["passage"][:80])
        if key in seen:
            continue
        seen.add(key)
        if seed_paths and r["path"] not in seed_paths:
            continue
        rows.append(r)
    # spread across paths rather than taking the head, which is all DISPLEASURE
    by_path = collections.defaultdict(list)
    for r in rows:
        by_path[r["path"]].append(r)
    out, i = [], 0
    while len(out) < n and any(by_path.values()):
        for p in sorted(by_path):
            if by_path[p] and len(out) < n:
                out.append(by_path[p].pop(i % max(1, len(by_path[p]))))
        i += 1
    return out


def run_accuracy(rows, model, log):
    print("\n=== ACCURACY — same passages, same ground truth, two routes to a rung ===")
    tally = {"emotion": [0, 0, 0], "event": [0, 0, 0]}      # exact, within-1, scored
    named_wrong_path = 0
    for i, r in enumerate(rows, 1):
        path, truth = r["path"], int(r["rung"])
        passage = r["passage"]
        row = {"path": path, "truth": truth, "model": model}

        # ARM 1 — the emotion seat. The passage is first person, so it is action and interior at
        # once; that is the condition this seat is designed for.
        try:
            raw = ask(appraiser.build_emotion_messages(passage, passage), model)
            reads, _lands, conf = appraiser.parse_emotion_reply(raw)
            hit = [x for x in reads if x.path == path]
            if hit:
                got = rungs.index_of(path, hit[0].rung)
                tally["emotion"][2] += 1
                tally["emotion"][0] += (got == truth)
                tally["emotion"][1] += (abs(got - truth) <= 1)
                row["emotion"] = {"rung": hit[0].rung, "index": got, "confidence": conf}
            else:
                named_wrong_path += 1
                row["emotion"] = {"rung": None, "paths_named": [x.path for x in reads]}
        except Exception as exc:
            row["emotion"] = {"error": "%s: %s" % (type(exc).__name__, str(exc)[:120])}

        # ARM 2 — the event seat, then the engine's own dimension route to a rung.
        try:
            raw = ask(appraiser.build_event_messages(passage), model)
            tags = appraiser.parse_event_reply(raw, action=passage)
            got = dimensions_to_rung(tags, path)
            tally["event"][2] += 1
            tally["event"][0] += (got == truth)
            tally["event"][1] += (abs(got - truth) <= 1)
            row["event"] = {"dimensions": tags["dimensions"], "index": got}
        except Exception as exc:
            row["event"] = {"error": "%s: %s" % (type(exc).__name__, str(exc)[:120])}

        log.write(json.dumps(row) + "\n")
        log.flush()
        print("  %3d/%d  %-12s truth %2d | emotion %-22s | event %s"
              % (i, len(rows), path, truth,
                 row["emotion"].get("rung") or row["emotion"].get("error", "-")[:22],
                 row["event"].get("index", row["event"].get("error", "-"))))

    print("\n  %-10s %7s %8s %8s" % ("arm", "scored", "exact", "within-1"))
    for arm in ("emotion", "event"):
        ex, w1, n = tally[arm]
        if n:
            print("  %-10s %7d %7.0f%% %7.0f%%" % (arm, n, 100.0 * ex / n, 100.0 * w1 / n))
        else:
            print("  %-10s %7d %8s %8s" % (arm, 0, "-", "-"))
    print("  emotion seat named the path at all: %d of %d"
          % (tally["emotion"][2], tally["emotion"][2] + named_wrong_path))
    print("\n  BAR (docs/emotion-arithmetic.md section 8): within-1 >= 80%, exact >= 50%")


def run_idle(model, n, log):
    print("\n=== IDLE — p, the false-positive rate. The number the whole design rests on. ===")
    beats = (IDLE_BEATS * ((n // len(IDLE_BEATS)) + 1))[:n]
    fired = 0
    for i, (action, thought) in enumerate(beats, 1):
        try:
            raw = ask(appraiser.build_emotion_messages(action, thought), model)
            reads, _l, _c = appraiser.parse_emotion_reply(raw)
        except Exception as exc:
            print("  %3d  REFUSED  %s" % (i, str(exc)[:70]))
            log.write(json.dumps({"idle": True, "error": str(exc)[:200]}) + "\n")
            continue
        fired += bool(reads)
        log.write(json.dumps({"idle": True, "action": action,
                              "readings": [(r.path, r.rung) for r in reads]}) + "\n")
        log.flush()
        print("  %3d  %-6s %s" % (i, "FIRED" if reads else "quiet",
                                  ", ".join("%s/%s" % (r.path, r.rung) for r in reads)[:60]))
    p = fired / float(len(beats))
    print("\n  p = %d/%d = %.2f     (section 8 requires p <= 0.20)" % (fired, len(beats), p))
    print("  runaway threshold: at retention 0.95 a sensor above p = 0.27 saturates every")
    print("  character on its own, with nothing happening in the world.")
    print("  VERDICT: %s" % ("USABLE" if p <= 0.20 else "TOO CHATTY — the prompt or the model, never the arithmetic"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="what job can each appraiser seat do?")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--idle", action="store_true", help="measure p instead of accuracy")
    ap.add_argument("--paths", default="", help="comma-separated subset")
    ap.add_argument("--emit", default=None, help="--idle: write the idle prompts to this directory and stop (one agent per prompt answers)")
    ap.add_argument("--replies", default=None, help="--idle: replay the answers written for the emitted prompts")
    a = ap.parse_args(argv)

    print("model: %s" % a.model)
    if a.idle and a.emit:
        import provider as _provider
        beats = (IDLE_BEATS * ((a.n // len(IDLE_BEATS)) + 1))[:a.n]
        keys = [_provider.emit(appraiser.build_emotion_messages(act, th), a.model, "appraise-emotion", a.emit, meta={"idle": i})
                for i, (act, th) in enumerate(beats, 1)]
        print("emitted %d idle prompts (%d distinct) -> %s" % (len(keys), len(set(keys)), a.emit))
        return 0
    if a.replies:
        import provider as _provider
        _provider.use_replies(a.replies)
    with io.open(OUT, "a", encoding="utf-8") as log:
        if a.idle:
            run_idle(a.model, a.n, log)
        else:
            paths = [p.strip() for p in a.paths.split(",") if p.strip()] or None
            rows = load_corpus(a.n, paths)
            print("corpus: %d passages, %d paths"
                  % (len(rows), len({r["path"] for r in rows})))
            run_accuracy(rows, a.model, log)
    print("\nrows -> %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
