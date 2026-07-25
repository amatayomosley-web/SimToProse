#!/usr/bin/env python3
"""coherence_probe.py — walking skeleton for the coherence/coupling probe (docs/probe-plan.md).

Runs ONE character (characters/maren-healer.json) through N turns of the minimal REAL loop and
checks tracked state stays sane, bounded, and coupled — the upstream risk that gates the director probe.

  --stub: canned LLM, deterministic smoke test | --corrupt: positive control, detectors MUST fail
  --run: real LLM via OpenRouter — the actual probe | --db: persist through src/engine | --roundtrip

NOT the engine: appraisal + scene-assembly are deliberately THIN (walking-skeleton discipline, probe-plan.md);
consolidation is built for real because it IS the keystone under test. src/ stays empty.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMARIES = ["SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY"]

# The probe runs on the CHEAPEST tier that can participate (override with --model).
# Why cheap, not strong: (1) production runs hundreds of turns x characters — only viable on a cheap model;
# cost-blowup is a named failure mode (prior-art.md), so the probe must test the production-realistic tier.
# (2) A cheap model holding coherent is STRONGER evidence the ARCHITECTURE does the work, not raw model smarts;
# a top model passing is the weakest possible result. Sweep haiku->sonnet to locate the floor — the floor is
# itself the finding (holds-on-haiku = cheap+robust; needs-sonnet = capability floor; needs-top = leaning on the model).
MODEL = "anthropic/claude-haiku-4.5"

CALL_BUDGET = None      # --max-calls N: hard-stop after N real API calls (for budgeted verification)
_CALLS = {"n": 0}
_PARSE_FAILS = {"n": 0}   # turns where the LLM emitted unparseable JSON — a per-model reliability signal
DB_PATH = None          # --db [path]: write the run through src/engine (the strangler-fig hook, gate 1)


class _BudgetHit(Exception):
    """Raised when the API call budget is exhausted — unwinds before any half-applied state write."""


def load_json(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


# Gate-2/3 strangler swaps: the thin profile/appraisal/decay AND the text-stub scene builder that
# lived here are replaced by the real modules (src/engine/state.py, src/engine/scene.py + gate.py —
# deterministic PerceptSet, trigger wall, energy-budgeted recall, stable/volatile packet).
sys.path.insert(0, REPO)
from src.engine.state import build_profile, appraise, decay   # noqa: E402
from src.engine.scene import assemble                          # noqa: E402
from src.engine.consolidation import validate_tags, CATALOG    # noqa: E402
from src.engine.prompt import build_turn_messages               # noqa: E402


def _env_path():
    """Path to the .env holding OPENROUTER_API_KEY.

    Machine-local and therefore NEVER hardcoded — a committed absolute path
    publishes the operator's directory layout and signposts their credentials.
    Set SWE_ENV_FILE, or fall back to a .env beside the repo.
    """
    p = os.environ.get("SWE_ENV_FILE")
    if p:
        return p
    local = os.path.join(REPO, ".env")
    if os.path.exists(local):
        return local
    raise RuntimeError(
        "no .env found: set SWE_ENV_FILE to the file holding OPENROUTER_API_KEY, "
        "or place a .env at the repo root (it is gitignored)")


def clamp(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


# ---- LLM interface: stub (deterministic) | openrouter (real) -------------------------------------

def llm_turn(packet, event, mode, temperament=None):
    """ONE-PASS turn (consolidation-loop.md Principle 1): the actor emits prose action + thought +
    its own event-tags in a single output — they cannot desynchronize. Returns {action, thought, tags}."""
    if mode == "run":
        return _openrouter_turn(packet, event, temperament)
    # stub: plausible event-flavored stand-in; tags echo the ground-truth hint (detectors exercised)
    return {
        "action": "Maren tends to it — %s" % event["text"].lower(),
        "thought": "(stub) she steadies herself and does what the moment needs",
        "tags": {"type": event.get("kind", "mundane"), "summary": event["text"],
                 "dimensions": dict(event.get("hint", {})), "durability": "transient"},
    }


def _openrouter(messages, max_tokens=600):
    import re
    import urllib.request
    key = None
    with open(_env_path(), encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"\s*OPENROUTER_API_KEY\s*=\s*(\S+)", line)
            if m:
                key = m.group(1).strip().strip('"').strip("'")
    if CALL_BUDGET is not None and _CALLS["n"] >= CALL_BUDGET:
        raise _BudgetHit()
    _CALLS["n"] += 1
    body = json.dumps({"model": MODEL, "messages": messages,
                       "max_tokens": max_tokens}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                 headers={"Authorization": "Bearer %s" % key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def _openrouter_turn(packet, event, temperament):
    """ONE call per turn. The prompt itself is ENGINE machinery (src/engine/prompt.py — the
    reasoning-contract layer, g6); this harness only dispatches and coerces the reply shape."""
    messages = build_turn_messages(packet, event["text"], temperament)
    d = _parse_json(_openrouter(messages, max_tokens=750))
    tags = d.get("tags") if isinstance(d.get("tags"), dict) else {"dimensions": {}}
    return {"action": d.get("action", ""), "thought": d.get("thought", ""), "tags": tags}   # always carry the keys


def _parse_json(text):
    import re
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        _PARSE_FAILS["n"] += 1
        return {"dimensions": {}}
    try:
        return json.loads(m.group(0))
    except Exception:
        _PARSE_FAILS["n"] += 1          # degrade, don't crash: a parse miss is DATA (model JSON reliability), not a halt
        return {"dimensions": {}}


# ---- the scripted event stream (mundane + high-impact + a recovery + a loss + the apprentice tension) ----
EVENTS = [
    {"text": "Morning. She walks the upland edge gathering late herbs.", "kind": "mundane", "hint": {"mastery": 0.2}},
    {"text": "A boy's scraped knee at the well — easy, cleaned and bound.", "kind": "mundane", "hint": {"care_relevant": 0.2, "mastery": 0.3}},
    {"text": "Bryn, a child, is carried in with a climbing fever.", "kind": "threat", "hint": {"threat": 0.6, "care_relevant": 0.8}},
    {"text": "She works the remedies through the night, watching the heat.", "kind": "mundane", "hint": {"mastery": 0.3, "threat": 0.2}},
    {"text": "Second night: Bryn's fever climbs higher, not lower.", "kind": "threat", "hint": {"threat": 0.7, "loss": 0.3}},
    {"text": "Edda the elder sits with her a while, says she's doing all anyone could.", "kind": "mundane", "hint": {"relief": 0.3, "care_relevant": 0.2}},
    {"text": "Joss, her apprentice, asks to take the night watch on Bryn alone.", "kind": "threat", "hint": {"threat": 0.55, "care_relevant": 0.4}},
    {"text": "A cup of tea, a few minutes off her feet.", "kind": "mundane", "hint": {"relief": 0.2}},
    {"text": "Third night — the threshold past which fevers here rarely turn.", "kind": "threat", "hint": {"threat": 0.85, "loss": 0.5}},
    {"text": "[scene boundary] Dawn comes.", "kind": "mundane", "hint": {}, "boundary": True},
    {"text": "Bryn's fever breaks with the light. He will live.", "kind": "care", "hint": {"relief": 0.9, "care_relevant": 0.3}},
    {"text": "She finally sleeps a few hours.", "kind": "mundane", "hint": {"relief": 0.25}},
    {"text": "Stores are low; she spends the morning grinding and drying.", "kind": "mundane", "hint": {"mastery": 0.25}},
    {"text": "Ren, the traveler, collapses in the square — an outsider, but ill.", "kind": "threat", "hint": {"threat": 0.5, "care_relevant": 0.5}},
    {"text": "She tends Ren; it's exhaustion and bad water, not danger. He'll mend.", "kind": "mundane", "hint": {"mastery": 0.3, "relief": 0.2}},
    {"text": "Old Tobin is past saving — she can only ease the leaving.", "kind": "loss", "hint": {"loss": 0.6, "care_relevant": 0.6}},
    {"text": "Tobin dies in the night, her hand on his.", "kind": "loss", "hint": {"loss": 0.8}},
    {"text": "She washes the body, the old rite, in silence.", "kind": "mundane", "hint": {"loss": 0.3, "care_relevant": 0.3}},
    {"text": "The village mourns at the square; she stands apart.", "kind": "mundane", "hint": {"loss": 0.2}},
    {"text": "Joss, shaken, asks her if he could have done more for Tobin.", "kind": "threat", "hint": {"care_relevant": 0.4, "threat": 0.3}},
    {"text": "She reorders every jar and tincture on the shelf, twice.", "kind": "mundane", "hint": {"mastery": 0.4}},
    {"text": "Another child sniffles at the well — almost certainly nothing.", "kind": "threat", "hint": {"threat": 0.6, "care_relevant": 0.5}},
    {"text": "It is nothing. She sits up watching the child's house anyway.", "kind": "mundane", "hint": {"threat": 0.2}},
    {"text": "Edda tells her, plainly, to rest.", "kind": "mundane", "hint": {"relief": 0.2, "care_relevant": 0.1}},
    {"text": "Dawn. The first hard frost; the fever season turns.", "kind": "mundane", "hint": {"relief": 0.3}},
]


def detectors(history, show=True):
    """State-sanity (mechanical), per measurement.md: bounds / saturation / oscillation / reversal / drift.
    Thresholds calibrated against the --corrupt control. MEASUREMENT LESSON (stub vs corrupt, this session):
    reversal *rate* does NOT discriminate — coherent affect rises on an event then decays, reversing
    direction often but *gently* (legit reversal 0.73-0.77 > corrupt 0.65). The load-bearing separators are
    oscillation *magnitude* (mean |turn-delta|: legit <=0.12, corrupt 0.22-0.24) and saturation (legit 0.00,
    corrupt 0.32-0.44). So we compute reversal for information but flag on magnitude + saturation + drift."""
    SAT_FRAC, OSC, DRIFT = 0.15, 0.18, 0.55
    temps = history["temperament"]
    series = {p: [snap[p] for snap in history["affect"]] for p in PRIMARIES}
    flags = []
    if show:
        print("  metric      " + "  ".join("%-5s" % p[:5] for p in PRIMARIES))
    rows = {"sat": [], "osc": [], "rev": [], "drift": []}
    for p in PRIMARIES:
        s = series[p]
        if any(v < -1e-9 or v > 1.0 + 1e-9 for v in s):
            flags.append("BOUNDS: %s left [0,1]" % p)
        sat = sum(1 for v in s if v <= 0.03 or v >= 0.97) / len(s)
        deltas = [s[i] - s[i - 1] for i in range(1, len(s))]
        osc = sum(abs(d) for d in deltas) / len(deltas) if deltas else 0.0
        signs = [1 if d > 0.01 else (-1 if d < -0.01 else 0) for d in deltas]
        nz = [x for x in signs if x != 0]
        rev = sum(1 for i in range(1, len(nz)) if nz[i] != nz[i - 1]) / max(1, len(nz) - 1)
        drift = abs(s[-1] - temps[p]["mean"])
        for k, v in (("sat", sat), ("osc", osc), ("rev", rev), ("drift", drift)):
            rows[k].append(v)
        if sat > SAT_FRAC:
            flags.append("SATURATION: %s pinned %.0f%% of turns" % (p, 100 * sat))
        if osc > OSC:
            flags.append("OSCILLATION: %s mean |turn-delta| %.2f" % (p, osc))
        if drift > DRIFT:
            flags.append("DRIFT: %s ended %.2f from resting (decay not holding)" % (p, drift))
    if show:
        for k in ("sat", "osc", "rev", "drift"):
            print("  %-10s  " % k + "  ".join("%.2f " % v for v in rows[k]))
    return flags


# ---- consolidation round-trip (pass-condition #3, probe-plan.md:66) — the keystone-risk detector ----
# The consolidation loop self-reports event-tags; #3 checks they stay FAITHFUL to the event's objective
# ground-truth (the scripted `hint`) AND — the load-bearing part — that the error does NOT COMPOUND across
# the run ("the flat slope is the real pass — this is the one error class that compounds"). Measured on data
# we already have: per-turn TAGS (consolidated dims) vs EVENTS[turn]["hint"]. No API calls.

def _roundtrip_error(dims, hint):
    """Mean absolute per-dimension distance between consolidated tags and ground-truth hint (union of keys)."""
    keys = set(dims) | set(hint)
    if not keys:
        return 0.0
    return sum(abs(float(dims.get(k, 0.0)) - float(hint.get(k, 0.0))) for k in keys) / len(keys)


def _lsq_slope(ys):
    """Least-squares slope of ys vs index 0..n-1 (error-per-turn). Flat ~0; positive = compounding."""
    n = len(ys)
    if n < 2:
        return 0.0
    xm = (n - 1) / 2.0
    ym = sum(ys) / n
    den = sum((i - xm) ** 2 for i in range(n))
    return sum((i - xm) * (ys[i] - ym) for i in range(n)) / den if den else 0.0


def consolidation_roundtrip(records, label="", show=True):
    """Pass-condition #3. records: [{turn, dims, hint}]. Two axes, reported separately:
      COMPOUNDING (slope) — the keystone. Rising error = the design's named highest risk. HARD fail.
      FIDELITY  (mean err) — absolute tag accuracy. Loose = a calibration issue, bounded + non-escalating. SOFT.
    Returns (flags, mean_err, slope)."""
    # SLOPE_THRESH calibrated against the planted compound-control (this session): legit runs measured a flat
    # +0.0003-0.0005/turn (~0.01 total drift over 25 turns = noise); the planted creeping error measured
    # +0.0084/turn. 0.004 sits between (8x the flat floor, half the control) — the control trips, legit passes.
    ERR_THRESH, SLOPE_THRESH = 0.30, 0.004
    errs = [_roundtrip_error(r["dims"], r["hint"]) for r in records]
    mean_err = sum(errs) / len(errs) if errs else 0.0
    slope = _lsq_slope(errs)
    flags = []
    if slope > SLOPE_THRESH:
        flags.append("COMPOUNDING: error slope +%.4f/turn (>%.4f) — consolidation error RISES across the run" % (slope, SLOPE_THRESH))
    if mean_err > ERR_THRESH:
        flags.append("FIDELITY: mean round-trip error %.2f (>%.2f) — tags drift from the objective event (calibration)" % (mean_err, ERR_THRESH))
    if show:
        print("  %-20s mean_err=%.3f  slope=%+.4f/turn  [%s]" % (
            (label + ":"), mean_err, slope, "COMPOUNDING" if slope > SLOPE_THRESH else "non-compounding"))
        print("    per-turn err: %s" % " ".join("%.2f" % e for e in errs))
    return flags, mean_err, slope


def _compound_control(records):
    """Planted POSITIVE control (teeth-check, measurement.md): a creeping false 'threat' tag that grows each
    turn, so error MUST rise. If consolidation_roundtrip does not flag COMPOUNDING here, the detector is hollow."""
    return [{"turn": r["turn"], "hint": r["hint"],
             "dims": dict(r["dims"], threat=clamp(r["dims"].get("threat", 0.0) + 0.04 * i))}
            for i, r in enumerate(records)]


def _roundtrip_records_from_log(log):
    """In-memory path: per-turn consolidated dims (from the run's log) joined to the event ground-truth hint."""
    return [{"turn": e["turn"], "dims": (e.get("tags") or {}).get("dimensions", {}) or {},
             "hint": EVENTS[e["turn"]].get("hint", {})} for e in log]


def _roundtrip_records_from_transcript(rel):
    """No-API path: recover per-turn TAGS from a saved --run transcript, join to EVENTS hints by turn index."""
    import re
    recs, turn = [], None
    for line in open(os.path.join(REPO, rel), encoding="utf-8", errors="replace"):
        m = re.match(r"^\s*(\d+)\s+[\d.]+\s", line)
        if m:
            turn = int(m.group(1))
        elif turn is not None and "TAGS" in line:
            mj = re.search(r"\{.*\}", line)
            dims = {}
            if mj:
                try:
                    dims = json.loads(mj.group(0))
                except Exception:
                    dims = {}
            if turn < len(EVENTS):
                recs.append({"turn": turn, "dims": dims, "hint": EVENTS[turn].get("hint", {})})
            turn = None
    return recs


def roundtrip_report():
    """Pass-condition #3 on data already in hand (no API): both saved runs + the planted compound-control."""
    print("consolidation round-trip — pass-condition #3 (probe-plan.md:66): FAITHFUL + NON-COMPOUNDING\n")
    have, hard_fail = [], []
    for name, rel in [("haiku", "runs/maren_haiku.txt"), ("sonnet", "runs/maren_sonnet.txt")]:
        if not os.path.exists(os.path.join(REPO, rel)):
            print("  (skip %s — %s not found)" % (name, rel))
            continue
        recs = _roundtrip_records_from_transcript(rel)
        if len(recs) < 5:
            print("  (skip %s — only %d turns recovered)" % (name, len(recs)))
            continue
        flags, me, sl = consolidation_roundtrip(recs, label=name)
        have.append((name, recs, flags, me, sl))
        hard_fail += [(name, f) for f in flags if f.startswith("COMPOUNDING")]
    if not have:
        print("\n  NO DATA — run `--run` first to produce runs/maren_*.txt")
        return 1
    # teeth-check: the planted compounding error MUST flag COMPOUNDING, or the detector is hollow.
    cflags, _, _ = consolidation_roundtrip(_compound_control(have[0][1]), label="control(compound)")
    teeth = "PASS" if any(f.startswith("COMPOUNDING") for f in cflags) else "FAIL"
    print("\n  teeth-check (planted compounding error MUST trip COMPOUNDING): %s" % teeth)
    print("\n--- condition #3 verdict ---")
    if teeth != "PASS":
        print("VERDICT: VOID — detector failed its own teeth-check; slope threshold too loose to trust")
        return 3
    if hard_fail:
        for n, f in hard_fail:
            print("  FLAG  [%s] %s" % (n, f))
        print("VERDICT: condition #3 FAIL — consolidation error COMPOUNDS (the keystone risk, caught pre-engine)")
        return 2
    soft = [(n, f) for (n, _r, fl, _m, _s) in have for f in fl if f.startswith("FIDELITY")]
    for n, f in soft:
        print("  note  [%s] %s" % (n, f))
    print("VERDICT: condition #3 PASS on the keystone axis — error is NON-COMPOUNDING (slope flat) on both runs.")
    print("         %s Gate to the director probe: OPEN." % (
        "Absolute fidelity is loose (calibration refinement, not a compounding fault)." if soft else "Fidelity also within threshold."))
    return 0


def _open_ledger(mode):
    """--db: write the run through the engine spine (strangler-fig hook, gate 1). Returns (ledger, run_id)."""
    import time
    sys.path.insert(0, REPO)
    from src.engine.ledger import Ledger
    led = Ledger(os.path.join(REPO, DB_PATH))
    run_id = "probe-%s-%d" % (mode, int(time.time()))
    led.create_run(run_id, {"catalog_version": 1, "models": {"decide": MODEL if mode == "run" else "stub"},
                            "prompt_versions": {"decide": 1, "consolidate": 2}})
    char = load_json("characters/maren-healer.json")
    led.register_character(run_id, "maren", char["fixed"], char["baseline"])
    return led, run_id


def run_probe(mode):
    char = load_json("characters/maren-healer.json")
    world = load_json("world/ashford-slice.json")
    temperament = char["baseline"]["temperament"]
    profile = build_profile(char)
    affect = {p: char["current"]["affect"][p] for p in PRIMARIES}
    condition = dict(char["current"]["condition"])   # static at probe scale; condition dynamics post-spine
    rng = _seeded_rng(1729) if mode == "corrupt" else None
    ledger = run_id = None
    if DB_PATH:
        ledger, run_id = _open_ledger(mode)

    affect_hist, log, recent, stopped = [], [], [], None
    print("turn  " + "  ".join("%-5s" % p[:5] for p in PRIMARIES) + "   event")
    for i, event in enumerate(EVENTS):
        scene_slice = {"event": {"text": event["text"], "kind": event.get("kind", "mundane")},
                       "recent": recent[-2:], "location": None}
        packet = assemble(char, world, scene_slice, affect, condition)
        recent.append(event["text"])
        try:
            turn = llm_turn(packet, event, mode, temperament)   # ONE pass: prose + tags together (Principle 1)
        except _BudgetHit:
            stopped = i
            break
        except Exception as exc:                   # any turn-level failure degrades, never crashes the run
            _PARSE_FAILS["n"] += 1
            print("%4d  [turn-error, degraded: %s]" % (i, str(exc)[:70]))
            if ledger is not None:
                ledger.record_turn_skipped(run_id, i, "maren", str(exc))   # no silent skips
            continue
        decision, tags = {"action": turn["action"], "thought": turn["thought"]}, turn["tags"]
        validation = validate_tags(tags, packet["volatile"]["percepts"], char["baseline"]["skills"])
        if not validation["ok"]:                   # schema-invalid record never moves state (conservative floor);
            tags = {"dimensions": {}}              # the rejection itself is recorded in TurnCommit.validation
        elif validation["flags"]:                  # catalog appraisal_map IS the contract: dims illegitimate for
            legit = CATALOG.get(tags.get("type", ""), {}).get("appraisal_map", [])   # the type never move state
            tags = dict(tags, dimensions={d: v for d, v in tags.get("dimensions", {}).items() if d in legit})
        affect = decay(appraise(affect, tags, profile), temperament, profile)
        if mode == "corrupt":                      # positive control: corrupt the state row
            affect = {p: clamp(affect[p] + rng()) for p in PRIMARIES}
        affect_hist.append(dict(affect))
        log.append({"turn": i, "event": event["text"], "tags": tags, "decision": decision})
        if ledger is not None:                     # the turn-commit: this turn persists atomically, or not at all
            from src.engine.records import Event, TurnCommit
            safe_tags = tags if isinstance(tags, dict) else {}
            ledger.append_turn(TurnCommit(
                run_id=run_id, turn=i, actor="maren",
                thought=str(decision.get("thought", "")), action=str(decision.get("action", "")),
                tags=safe_tags, affect=dict(affect), validation=validation,
                events=[Event(type=str(safe_tags.get("type", "mundane")),
                              payload={"text": event["text"],
                                       "dimensions": safe_tags.get("dimensions", {}),
                                       "durability": safe_tags.get("durability", "transient")},
                              actor="maren")],
                # record-contract.md: the packet's REAL manifest + recall refs (audit-A2 repair complete)
                manifest=packet["manifest"],
                recall=packet["recall_refs"]))
        print("%4d  " % i + "  ".join("%.2f " % affect[p] for p in PRIMARIES) +
              ("  | %s" % event["text"][:48]))
        if mode == "run":                          # surface the model's actual output for inspection
            print("        ACTION : %s" % str(decision.get("action", "")).replace("\n", " ")[:220])
            print("        THOUGHT: %s" % str(decision.get("thought", "")).replace("\n", " ")[:180])
            print("        TAGS   : %s  [%s]  valid=%s conf=%.2f%s" % (
                json.dumps(tags.get("dimensions", {})), tags.get("durability", "?"),
                validation["ok"], validation["confidence"],
                " ESCALATE(%s)" % "; ".join(validation["flags"])[:80] if validation["escalate"] else ""))
    if stopped is not None:
        print("\n[stopped at turn %d — call budget %s reached; %d real calls made]" % (stopped, CALL_BUDGET, _CALLS["n"]))
    if ledger is not None:                         # resume asserts fold determinism (run-lifecycle.md), or raises
        resumed = ledger.resume(run_id)
        n_commits = ledger.con.execute("SELECT COUNT(*) c FROM turns WHERE run_id = ?", (run_id,)).fetchone()["c"]
        print("\n[ledger] run=%s  %d turn-commits persisted  resume@turn=%d determinism OK" % (run_id, n_commits, resumed["turn"]))

    if mode == "run":
        print("\nLLM JSON parse failures: %d / %d turns" % (_PARSE_FAILS["n"], len(affect_hist) or 1))
        print("\n--- consolidation round-trip (pass-condition #3) ---")
        consolidation_roundtrip(_roundtrip_records_from_log(log), label=MODEL.split("/")[-1])
    flags = detectors({"affect": affect_hist, "temperament": temperament})
    print("\n--- state-sanity detectors ---")
    if flags:
        for f in flags:
            print("  FLAG  " + f)
        print("VERDICT: FAIL (%d flag(s))" % len(flags))
        return 2
    print("  all primaries bounded, non-saturating, non-oscillating, returned toward resting")
    print("VERDICT: PASS")
    return 0


def _seeded_rng(seed):
    """Tiny deterministic LCG -> corruption noise in [-0.45, 0.45]. (No stdlib random import needed.)"""
    state = {"s": seed}

    def nxt():
        state["s"] = (1103515245 * state["s"] + 12345) & 0x7FFFFFFF
        return (state["s"] / 0x7FFFFFFF - 0.5) * 0.9
    return nxt


def main(argv):
    global MODEL, CALL_BUDGET, DB_PATH
    if "--roundtrip" in argv:                  # pass-condition #3 over saved transcripts — no API calls
        return roundtrip_report()
    if "--db" in argv:
        nxt = argv[argv.index("--db") + 1] if argv.index("--db") + 1 < len(argv) else ""
        DB_PATH = nxt if nxt and not nxt.startswith("--") else "runs/probe.db"
    mode = "stub"
    if "--run" in argv:
        mode = "run"
    elif "--corrupt" in argv:
        mode = "corrupt"
    if "--model" in argv:
        MODEL = argv[argv.index("--model") + 1]
    if "--max-calls" in argv:
        CALL_BUDGET = int(argv[argv.index("--max-calls") + 1])
    print("coherence_probe: mode=%s  model=%s  N=%d turns\n" % (
        mode, MODEL if mode == "run" else "(no API)", len(EVENTS)))
    return run_probe(mode)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
