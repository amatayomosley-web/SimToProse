#!/usr/bin/env python3
"""exp.py — the lever-eval harness for docs/driving-the-engine.md.

Config-driven: each experiment freezes all but ONE lever, K-samples at temperature>0 with seeds
0..K-1 (reproducible), extracts grep-able outcomes (exit flag, tag type/dims, naming, leave-verbs,
empties), and appends a rates record per experiment to docs/exp-results.jsonl (crash-safe).

EXP-0 runs first and ABORTS the battery if the empty-turn rate is too high (a broken instrument
caught in ~10 min, not 2 hours). Per-sample and per-experiment try/except: one failure never kills
the battery. Engine + stdlib only.

Run:  python scripts/exp.py            # full battery
      python scripts/exp.py --smoke    # K=1, one experiment, fast sanity
"""
import sys, os, json, time, subprocess, shutil, argparse
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.vault import load_book                 # noqa: E402
from src.engine.scene import assemble                  # noqa: E402
from src.engine.prompt import build_turn_messages      # noqa: E402
from src.engine.state import build_profile, appraise   # noqa: E402
from direct import _ollama, _parse_reply, DEFAULT_MODEL  # noqa: E402
from scene import BP13                                  # noqa: E402

BOOK = os.environ.get("SWE_BOOK") or os.environ.get("SWE_BOOKS")
MODEL = DEFAULT_MODEL.split("/", 1)[1]   # locked to direct.DEFAULT_MODEL (bare name; strip the ollama/ prefix)
RESULTS = os.path.join(REPO, "docs", "exp-results.jsonl")
W = shutil.which("ollama")


def _stop():
    if W:
        subprocess.run([W, "stop", MODEL], capture_output=True, text=True)


# ---- moments (what the speaker perceives) ----
SIT = BP13["situation"]
STONEWALL = {
    "soft":    "Send two as far as the ford, then. I will decide the rest after we have eaten. Sit down.",
    "hard":    "Sit down, Ilsa. We will not discuss this further tonight; the matter keeps until morning.",
    "dehuman": "She is a child who dawdles. A dawdling child can wait in the cold an hour. Sit, and let us eat.",
}
def moment_stonewall(line):
    t = ('The exchange in the kitchen so far (most recent last):\n'
         'Ilsa: "Arden - the upland road. Pell has been gone since midday. Has anyone walked past the ford?"\n'
         'Arden: "%s"' % line)
    return SIT + "\n\n" + t
def moment_opener(situation=SIT):
    return situation + " The plates have just been set down; the evening is beginning."

FRAMING = {
    "clinical": "It is night at the Holloway steading. A child was sent up the road at midday and has not returned.",
    "sensory":  ("It is night at the Holloway steading. Out past the yard the frost is settling over the upland road the child walked at midday "
                 "and has not walked back, four hours overdue in the dark, while the family sits down to eat."),
}

# ---- extractors: turn -> value ----
LEAVE = ("i rise", "i stand", "push back", "i leave", "i go ", "i will go", "excuse myself", "i get up",
         "leave the table", "leaving the table", "to the garden", "from the table")
def _act(t): return str(t.get("action", "") or "")
def _dim(t, k): return float(((t.get("tags") or {}).get("dimensions") or {}).get(k, 0.0) or 0.0)
EXTRACTORS = {
    "exit":             lambda t: bool(t.get("exit")),
    "leave_verb":       lambda t: any(v in _act(t).lower() for v in LEAVE),
    "names_pell":       lambda t: "pell" in _act(t).lower(),
    "type":             lambda t: (t.get("tags") or {}).get("type"),
    "care_relevant":    lambda t: _dim(t, "care_relevant"),
    "social_violation": lambda t: _dim(t, "social_violation"),
    "loss":             lambda t: _dim(t, "loss"),
    "empty":            lambda t: not _act(t).strip(),
}

def aggregate(turns):
    out = {}
    for name, fn in EXTRACTORS.items():
        vals = [fn(t) for t in turns]
        if all(isinstance(v, bool) for v in vals):
            out[name] = "%d/%d" % (sum(vals), len(vals))
        elif all(isinstance(v, (int, float)) for v in vals):
            out[name] = round(sum(vals) / len(vals), 2)
        else:
            out[name] = dict(Counter("" if v is None else str(v) for v in vals))
    return out


# ---- the sampler: one condition -> K turns ----
def sample_condition(setup, K=6, think=True, temp=0.7):
    world, chars = load_book(BOOK)        # fresh state per condition (no cross-contamination)
    cid, event_text = setup(chars, world)
    ch = chars[cid]
    ss = {"event": {"text": event_text, "kind": "mundane"}, "recent": [], "location": ch["current"].get("location")}
    packet = assemble(ch, world, ss, dict(ch["current"]["affect"]), ch["current"]["condition"])
    messages = build_turn_messages(packet, event_text, ch["baseline"]["temperament"])
    turns = []
    for s in range(K):
        try:
            turns.append(_parse_reply(_ollama(messages, MODEL, think=think, temperature=temp, seed=s)))
        except Exception as e:
            turns.append({"action": "", "thought": "", "exit": False, "tags": {}, "_err": repr(e)[:120]})
    return turns


# ---- setup builders: (chars, world) -> (char_id, event_text) ----
BASE_DRIVE = BP13["cast"][0]["drive"]   # passive baseline; held constant so only the tested lever moves

def ilsa_drive(drive):
    def f(chars, world):
        chars["ilsa"]["current"]["active_goals"] = [{"goal": drive, "urgency": 0.8}]
        return "ilsa", moment_stonewall(STONEWALL["soft"])
    return f
def ilsa_wall(line):
    def f(chars, world):
        chars["ilsa"]["current"]["active_goals"] = [{"goal": BASE_DRIVE, "urgency": 0.8}]
        return "ilsa", moment_stonewall(line)
    return f
def ilsa_rage(r):
    def f(chars, world):
        chars["ilsa"]["current"]["active_goals"] = [{"goal": BASE_DRIVE, "urgency": 0.8}]
        chars["ilsa"]["current"]["affect"]["RAGE"] = r
        return "ilsa", moment_stonewall(STONEWALL["soft"])
    return f
def ilsa_debt(d):
    def f(chars, world):
        chars["ilsa"]["current"]["active_goals"] = [{"goal": BASE_DRIVE, "urgency": 0.8}]
        rel = chars["ilsa"]["current"].setdefault("relationships", {}).setdefault("pell", {})
        rel["debt"] = d
        return "ilsa", moment_stonewall(STONEWALL["soft"])
    return f
def ilsa_framing(sit):
    def f(chars, world):
        chars["ilsa"]["current"]["active_goals"] = [{"goal": BASE_DRIVE, "urgency": 0.8}]
        return "ilsa", moment_opener(sit)
    return f


# ---- LLM-sampled experiments ----
EXPERIMENTS = [
    {"id": "EXP-0-calib", "note": "noise floor (empty + valid rate)", "K": 12, "conditions": [
        ("baseline", ilsa_drive(BP13["cast"][0]["drive"]))]},
    {"id": "EXP-2-wall", "note": "stonewall severity -> exit?", "conditions": [
        ("soft", ilsa_wall(STONEWALL["soft"])),
        ("hard", ilsa_wall(STONEWALL["hard"])),
        ("dehuman", ilsa_wall(STONEWALL["dehuman"]))]},
    {"id": "EXP-4-affect", "note": "starting RAGE dose-response", "conditions": [
        ("rage_0.35", ilsa_rage(0.35)),
        ("rage_0.60", ilsa_rage(0.60)),
        ("rage_0.85", ilsa_rage(0.85))]},
    {"id": "EXP-6-relationship", "note": "Ilsa->Pell debt", "conditions": [
        ("debt_0.0", ilsa_debt(0.0)),
        ("debt_0.3", ilsa_debt(0.3)),
        ("debt_0.8", ilsa_debt(0.8))]},
    {"id": "EXP-7-framing", "note": "director prose: clinical vs sensory", "conditions": [
        ("clinical", ilsa_framing(FRAMING["clinical"])),
        ("sensory", ilsa_framing(FRAMING["sensory"]))]},
    {"id": "EXP-9-thinking", "note": "thinking on vs off (same moment)", "conditions": [
        ("think_on", ilsa_drive(BP13["cast"][0]["drive"])),
        ("think_off", ilsa_drive(BP13["cast"][0]["drive"]))]},
]
THINK_OFF = {("EXP-9-thinking", "think_off")}


# ---- free math experiment: regard -> CARE delta (no LLM) ----
def exp_regard_math():
    world, chars = load_book(BOOK)
    ch = chars["ilsa"]
    base = dict(ch["current"]["affect"])
    rows = []
    for r in (0.05, 0.2, 0.6, 1.0):
        ch["baseline"]["model"]["regard"] = {"holloway": r}
        prof = build_profile(ch)
        tags = {"dimensions": {"care_relevant": 0.6}, "target_group": "holloway"}   # group only -> pure regard, no affinity lift
        after = appraise(base, tags, prof)
        rows.append({"regard": r, "CARE_delta": round(after["CARE"] - base["CARE"], 3)})
    prof = build_profile(ch)
    after = appraise(base, {"dimensions": {"care_relevant": 0.6}}, prof)            # no subject -> factor 1.0 control
    rows.append({"regard": "no-subject", "CARE_delta": round(after["CARE"] - base["CARE"], 3)})
    return rows


# ---- runner ----
def _write(rec):
    rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(RESULTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(">>", rec.get("exp"), json.dumps(rec.get("summary", rec.get("error", "")), ensure_ascii=False)[:400], flush=True)

def run_experiment(spec):
    K = spec.get("K", 6)
    conds = {}
    for label, setup in spec["conditions"]:
        think = (spec["id"], label) not in THINK_OFF
        _stop()
        t0 = time.time()
        turns = sample_condition(setup, K=K, think=think)
        conds[label] = {
            "rates": aggregate(turns),
            "secs": round(time.time() - t0),
            "samples": [{"exit": bool(x.get("exit")), "type": (x.get("tags") or {}).get("type"),
                         "action": _act(x).replace("\n", " ")[:170]} for x in turns],
        }
    return {"exp": spec["id"], "note": spec.get("note"), "K": K,
            "summary": {lbl: c["rates"] for lbl, c in conds.items()}, "conditions": conds}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="K=1 sanity on one experiment")
    ap.add_argument("--book", default=None, help="path to a book vault directory (or slug)")
    args = ap.parse_args()
    book_path = args.book or BOOK
    if not book_path:
        raise SystemExit("set SWE_BOOKS or pass --book (see docs/guide-operating.md)")
    if args.smoke:
        turns = sample_condition(EXPERIMENTS[1]["conditions"][0][1], K=1)
        print("SMOKE:", json.dumps({"rates": aggregate(turns), "action": _act(turns[0])[:170],
              "exit": turns[0].get("exit"), "tags": turns[0].get("tags")}, ensure_ascii=False, indent=2))
        _stop(); return 0
    print("=== LEVER EVAL BATTERY (model=%s) ===" % MODEL, flush=True)
    e0 = run_experiment(EXPERIMENTS[0]); _write(e0)
    empty = e0["conditions"]["baseline"]["rates"].get("empty", "0/12")
    if int(str(empty).split("/")[0]) > 2:
        _write({"exp": "ABORT", "error": "empty-turn rate %s too high; fix dispatch before trusting rates" % empty})
        print("ABORTED.", flush=True); _stop(); return 1
    for spec in EXPERIMENTS[1:]:
        try:
            _write(run_experiment(spec))
        except Exception as e:
            _write({"exp": spec["id"], "error": repr(e)[:200]})
        _stop()
    _write({"exp": "EXP-5-regard-math", "summary": exp_regard_math()})
    print("=== BATTERY DONE ===", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
