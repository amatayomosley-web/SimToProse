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

BOOK = os.environ.get("SWE_BOOK")   # path to a book vault; machine-local, never hardcoded
if not BOOK:
    raise SystemExit("set SWE_BOOK to a book vault directory (see docs/guide-operating.md)")
MODEL = DEFAULT_MODEL.split("/", 1)[1]   # locked to direct.DEFAULT_MODEL (bare name; strip the ollama/ prefix)
RESULTS = os.path.join(REPO, "docs", "exp-results.jsonl")
W = shutil.which("ollama")


def _stop():
    if W:
        subprocess.run([W, "stop", MODEL], capture_output=True, text=True)


# ---- moments (what the speaker perceives) ----
SIT = BP13["situation"]
STONEWALL = {
    "soft":    "Have two retrieve the damaged worker. I will assess it after dinner. We will finish the meal first.",
    "hard":    "Sit down, Brakk. We will not discuss this further tonight; the matter is closed until the meal is done.",
    "dehuman": "It is a tool, Brakk. A tool can wait in the cold. Sit, and let us eat.",
}
def moment_stonewall(line):
    t = ('The exchange at the table so far (most recent last):\n'
         'Brakk: "Father - the worker who shielded Wynn. Has she been seen to?"\n'
         'Orven: "%s"' % line)
    return SIT + "\n\n" + t
def moment_opener(situation=SIT):
    return situation + " The table has just been served; the evening is beginning."

FRAMING = {
    "clinical": "It is evening at the Wintercrest dinner. A house-worker was injured in the garden earlier today and has not yet been brought inside.",
    "sensory":  ("It is evening at the Wintercrest dinner. Out in the dark garden the frost is settling over the worker who still lies in the mud where she "
                 "fell this afternoon, her arm broken and her face cut, while the family sits down to eat."),
}

# ---- extractors: turn -> value ----
LEAVE = ("i rise", "i stand", "push back", "i leave", "i go ", "i will go", "excuse myself", "i get up",
         "leave the table", "leaving the table", "to the garden", "from the table")
def _act(t): return str(t.get("action", "") or "")
def _dim(t, k): return float(((t.get("tags") or {}).get("dimensions") or {}).get(k, 0.0) or 0.0)
EXTRACTORS = {
    "exit":             lambda t: bool(t.get("exit")),
    "leave_verb":       lambda t: any(v in _act(t).lower() for v in LEAVE),
    "names_kestra":       lambda t: "kestra" in _act(t).lower(),
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

def brakk_drive(drive):
    def f(chars, world):
        chars["brakk"]["current"]["active_goals"] = [{"goal": drive, "urgency": 0.8}]
        return "brakk", moment_stonewall(STONEWALL["soft"])
    return f
def brakk_wall(line):
    def f(chars, world):
        chars["brakk"]["current"]["active_goals"] = [{"goal": BASE_DRIVE, "urgency": 0.8}]
        return "brakk", moment_stonewall(line)
    return f
def brakk_rage(r):
    def f(chars, world):
        chars["brakk"]["current"]["active_goals"] = [{"goal": BASE_DRIVE, "urgency": 0.8}]
        chars["brakk"]["current"]["affect"]["RAGE"] = r
        return "brakk", moment_stonewall(STONEWALL["soft"])
    return f
def brakk_debt(d):
    def f(chars, world):
        chars["brakk"]["current"]["active_goals"] = [{"goal": BASE_DRIVE, "urgency": 0.8}]
        rel = chars["brakk"]["current"].setdefault("relationships", {}).setdefault("kestra", {})
        rel["debt"] = d
        return "brakk", moment_stonewall(STONEWALL["soft"])
    return f
def brakk_framing(sit):
    def f(chars, world):
        chars["brakk"]["current"]["active_goals"] = [{"goal": BASE_DRIVE, "urgency": 0.8}]
        return "brakk", moment_opener(sit)
    return f


# ---- LLM-sampled experiments ----
EXPERIMENTS = [
    {"id": "EXP-0-calib", "note": "noise floor (empty + valid rate)", "K": 12, "conditions": [
        ("baseline", brakk_drive(BP13["cast"][0]["drive"]))]},
    {"id": "EXP-2-wall", "note": "stonewall severity -> exit?", "conditions": [
        ("soft", brakk_wall(STONEWALL["soft"])),
        ("hard", brakk_wall(STONEWALL["hard"])),
        ("dehuman", brakk_wall(STONEWALL["dehuman"]))]},
    {"id": "EXP-4-affect", "note": "starting RAGE dose-response", "conditions": [
        ("rage_0.35", brakk_rage(0.35)),
        ("rage_0.60", brakk_rage(0.60)),
        ("rage_0.85", brakk_rage(0.85))]},
    {"id": "EXP-6-relationship", "note": "Brakk->Kestra debt", "conditions": [
        ("debt_0.0", brakk_debt(0.0)),
        ("debt_0.3", brakk_debt(0.3)),
        ("debt_0.8", brakk_debt(0.8))]},
    {"id": "EXP-7-framing", "note": "director prose: clinical vs sensory", "conditions": [
        ("clinical", brakk_framing(FRAMING["clinical"])),
        ("sensory", brakk_framing(FRAMING["sensory"]))]},
    {"id": "EXP-9-thinking", "note": "thinking on vs off (same moment)", "conditions": [
        ("think_on", brakk_drive(BP13["cast"][0]["drive"])),
        ("think_off", brakk_drive(BP13["cast"][0]["drive"]))]},
]
THINK_OFF = {("EXP-9-thinking", "think_off")}


# ---- free math experiment: regard -> CARE delta (no LLM) ----
def exp_regard_math():
    world, chars = load_book(BOOK)
    ch = chars["brakk"]
    base = dict(ch["current"]["affect"])
    rows = []
    for r in (0.05, 0.2, 0.6, 1.0):
        ch["baseline"]["model"]["regard"] = {"fenmark": r}
        prof = build_profile(ch)
        tags = {"dimensions": {"care_relevant": 0.6}, "target_group": "fenmark"}   # group only -> pure regard, no affinity lift
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
    args = ap.parse_args()
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
