#!/usr/bin/env python3
"""calibrate_accrual.py — how much should one reading accrue? Measured against the thermometer.

THE QUESTION (owner, 2026-09-11, after the first generated scene on a real book): a character's
GOODWILL ran fondness -> devotion in three beats on real readings. "We shouldn't see dramatic increases
without cause ... I have no issue with counting legitimate repetition, but this has shown we need
to lower the amount that accrues." The accrual has one global knob, `rungs.LAMBDA` (0.15 on every
path, a Class-B start that was never measured), and one open design question: whether a reading
at or below the level the character already carries should add its full vector (a repeat) or a
smaller one (sustaining), with the full vector reserved for a reading that names a HIGHER level
than is carried (arising). This script measures both, on the data we have.

THE DATA: the two live read-alongs (Red Badge, Holmes) carry an Opus reading per beat AND an Opus
thermometer sample every five beats — the standing level the text actually shows. Every seat
answer is cached under $SWE_BOOKS/readalong/<slug>/seats/, so the whole run can be re-run
in-process, deterministically, with the engine's constants changed and NOTHING else.

THE METHOD (measurement only; no engine change; this file is a test-tree tool):
  1. VALIDATE: re-run at scale 1.0 and compare every committed affect against the ORIGINAL run's
     current_state. If they differ the replay is not the run and nothing below counts.
  2. SWEEP: for each variant x scale, re-run and score `state vs thermometer` with the harness's
     own scorer (readalong._state_vs_levels): mean |state - level| in height, per-path bias
     median, against the rest-only baseline that any prediction must beat.
  3. Every run this makes is moved to <book>/staging/calibration/ so the book's runs/ stays the
     record of real runs.

VARIANTS
  additive   the shipped receipt: f += v(rung)·g·c·q            (rungs.vector_for scaled by s)
  anchored   two multiplier sets keyed on the CARRIED level:
               rung above carried: f += ALPHA·g·c·(level(rung) - f)   (arising: the gap, not the vector)
               rung at/below:      f += RHO·g·c·v(rung)·q             (sustaining: counts, small)

Usage:
  python tests/calibrate_accrual.py --book red-badge --scales 1,0.7,0.5,0.35,0.25,0.15
  python tests/calibrate_accrual.py --book holmes --variant anchored --alpha 0.5 --rho 0.25
  python tests/calibrate_accrual.py --book red-badge --original readalong-red-badge-1789158299-9a8063   (validate only)
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import readalong as RA                                             # noqa: E402
from src.engine import rungs as _rungs                             # noqa: E402
from src.engine import connection as _conn                         # noqa: E402
from src.engine import state as _state                             # noqa: E402
from src.engine.ledger import Ledger                               # noqa: E402
from src.engine.records import PATHS                               # noqa: E402

_ORIG_LAMBDA = dict(_rungs.LAMBDA)
_ORIG_RECEIVE = RA.receive
_ORIG_LOAD_BOOK = RA.load_book


def load_book_with_all_paths(book_dir):
    """The read-along sheets were authored on eight paths; LEVITY joined the engine afterwards
    (2026-09-11). Default the missing path IN MEMORY (rest quiet -> its band midpoint, genotype
    typical) so the sheets on disk stay the other session's to migrate. The original runs never
    carried LEVITY, so the validation compares the eight paths they did carry."""
    text, chapters, sheet, cast = _ORIG_LOAD_BOOK(book_dir)
    from src.engine import heritable as _H
    temp = sheet["baseline"].setdefault("temperament", {})
    for p in PATHS:
        if p not in temp:
            temp[p] = {"rest": "quiet"}
        if p not in sheet["current"].setdefault("affect", {}):
            sheet["current"]["affect"][p] = _H.rest_mean(p, temp)
        sheet["fixed"].setdefault("genotype", {}).setdefault(p, {"hit": "typical", "hold": "typical"})
    return text, chapters, sheet, cast


RA.load_book = load_book_with_all_paths


def anchored_receive(alpha, rho):
    """A receipt with two multiplier sets keyed on the carried level. Same signature as state.receive."""
    def receive(affect, readings, profile, targets=None, repeats=None, present=None):
        gains = profile["gains"]
        rels = profile.get("relationships", {}) if isinstance(profile.get("relationships"), dict) else {}
        held = profile.get("held") or {}
        here = {str(x) for x in (present or ())}
        out = {p: (v if p.startswith("_") else float(v)) for p, v in affect.items()}
        impact = 0.0
        for r in (readings or []):
            path, rung, about = r.path, r.rung, (r.about or "")
            k = _rungs.index_of(path, rung)
            level = _rungs.height_of(path, k)
            v = _rungs.vector_for(path, k)
            g = float(gains.get(path, 1.0))
            about = about or (targets or {}).get(path) or ""
            cs = _conn.magnitude_scale(_conn.for_about(rels, held, about, path)) if about else 1.0
            n = (repeats or {}).get(str(about), 0) if about else 0
            q = _conn.repetition(n, str(about) in here) if about else 1.0
            gap = level - out[path]
            add = alpha * g * cs * gap if gap > 0 else rho * g * cs * v * q
            impact += add
            out[path] = max(0.0, min(1.0, out[path] + add))
        return out, impact
    return receive


def set_scale(s):
    for p in _ORIG_LAMBDA:
        _rungs.LAMBDA[p] = _ORIG_LAMBDA[p] * float(s)


def readings_seat(book_dir, original, pid):
    """A seat that answers from the ORIGINAL run's stored readings, turn by turn. The cached seat
    replies cannot be replayed by key any more (the ladders gained LEVITY after those runs, so every
    prompt's key changed), but the READINGS the seat produced are in the run's log, and the
    readings — not the prompts — are what the arithmetic consumes."""
    from src.engine.records import Reading
    led = Ledger(os.path.join(book_dir, "runs", "%s.db" % original))
    rows = led.con.execute("SELECT turn, path, rung, about, confidence FROM readings WHERE run_id = ? AND actor = ? "
                           "ORDER BY turn, reading_id", (original, pid)).fetchall()
    led.con.close()
    by_turn = {}
    for r in rows:
        by_turn.setdefault(int(r["turn"]), []).append(
            Reading(path=r["path"], rung=r["rung"], about=r["about"] or "", confidence=r["confidence"] or "likely"))

    def seat(passage, model, led, run_id, turn):
        rs = by_turn.get(int(turn), [])
        return rs, [], "likely", []
    return seat


def rerun(book_dir, seat):
    """One in-process re-run from the original run's readings -> run_id. Quiet. No thermometer call
    (the original's levels file is compared against instead)."""
    return RA.run(book_dir, seat=seat, model="replay", thermometer=0, log=lambda *_a, **_k: None)


def states_of(book_dir, run_id, pid):
    led = Ledger(os.path.join(book_dir, "runs", "%s.db" % run_id))
    rows = led.con.execute("SELECT turn, affect FROM current_state WHERE run_id = ? AND char_id = ? ORDER BY turn",
                           (run_id, pid)).fetchall()
    out = {int(r["turn"]): json.loads(r["affect"]) for r in rows}
    led.con.close()
    return out


def levels_of(book_dir, run_id):
    p = os.path.join(book_dir, "runs", "%s.levels.jsonl" % run_id)
    if not os.path.isfile(p):
        return []
    return [json.loads(l) for l in io.open(p, encoding="utf-8") if l.strip()]


def score_vs_thermometer(book_dir, run_id, levels):
    _text, _chapters, sheet, _cast = RA.load_book(book_dir)
    pid = sheet["fixed"]["id"]
    led = Ledger(os.path.join(book_dir, "runs", "%s.db" % run_id))
    temp = sheet["baseline"]["temperament"]
    res = RA._state_vs_levels(led, run_id, pid, temp, levels)
    # the ceiling count: how often the state sits at the top rung of a path
    st = states_of(book_dir, run_id, pid)
    pinned = {p: 0 for p in PATHS}
    for a in st.values():
        for p in PATHS:
            if float(a.get(p, 0.0)) >= 0.95:
                pinned[p] += 1
    res["pinned_turns"] = {p: n for p, n in pinned.items() if n}
    res["turns"] = len(st)
    led.con.close()
    return res


def park(book_dir, run_id):
    """Move a calibration run out of runs/ (it is not a real run). The driver leaves its sqlite
    handle to the garbage collector, and Windows refuses to move an open file, so collect first
    and leave a note rather than fail when a handle survives."""
    import gc
    gc.collect()
    dst = os.path.join(book_dir, "staging", "calibration")
    os.makedirs(dst, exist_ok=True)
    for f in glob.glob(os.path.join(book_dir, "runs", run_id + "*")):
        try:
            shutil.move(f, os.path.join(dst, os.path.basename(f)))
        except OSError:
            print("   (could not move %s yet — still open; move it by hand)" % os.path.basename(f))


def readings_of(book_dir, run_id, pid):
    led = Ledger(os.path.join(book_dir, "runs", "%s.db" % run_id))
    rows = [(int(r["turn"]), r["path"], r["rung"], r["about"] or "") for r in led.con.execute(
        "SELECT turn, path, rung, about FROM readings WHERE run_id = ? AND actor = ? ORDER BY turn, reading_id", (run_id, pid))]
    led.con.close()
    return rows


def validate(book_dir, seat, original, pid):
    """The replay must consume EXACTLY the original run's readings (the input is the run); the
    committed affect is then the CURRENT engine's arithmetic on them, which legitimately differs
    from the original where the engine's constants moved since (the half-lives were re-set on
    2026-09-11 after the original ran under the START table). Returns (readings_identical,
    worst affect diff, turns)."""
    set_scale(1.0)
    RA.receive = _ORIG_RECEIVE
    rid = rerun(book_dir, seat)
    same = readings_of(book_dir, original, pid) == readings_of(book_dir, rid, pid)
    a, b = states_of(book_dir, original, pid), states_of(book_dir, rid, pid)
    worst = 0.0
    for t in sorted(a):
        if t not in b:
            continue
        for p in PATHS:
            if p in a[t] and p in b[t]:
                worst = max(worst, abs(float(a[t][p]) - float(b[t][p])))
    park(book_dir, rid)
    return same, worst, len(b)


def main(argv=None):
    ap = argparse.ArgumentParser(description="measure how much a reading should accrue, against the thermometer")
    ap.add_argument("--book", required=True, help="read-along slug under $SWE_BOOKS/readalong/")
    ap.add_argument("--original", default=None, help="the live run id to validate the replay against (default: newest with a levels file and Opus readings)")
    ap.add_argument("--scales", default="1,0.7,0.5,0.35,0.25,0.15,0.1")
    ap.add_argument("--variant", default="both", choices=("additive", "anchored", "both"))
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--rho", type=float, default=0.25)
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--lambdas", default=None, help="a JSON object {PATH: lambda} to score instead of the scale sweep")
    args = ap.parse_args(argv)

    book_dir = os.path.join(RA.books_root(), args.book)
    seats = os.path.join(book_dir, "seats")
    _text, _chapters, sheet, _cast = RA.load_book(book_dir)
    pid = sheet["fixed"]["id"]
    original = args.original
    if not original:
        cands = sorted(glob.glob(os.path.join(book_dir, "runs", "readalong-*.levels.jsonl")), key=os.path.getmtime)
        original = os.path.basename(cands[-1])[:-len(".levels.jsonl")] if cands else None
    print("book %s  protagonist %s  cached replies %d  original run %s" % (
        args.book, pid, len(glob.glob(os.path.join(seats, "*.reply.txt"))), original))

    if not original:
        raise SystemExit("no original run with a levels file under %s/runs" % book_dir)
    seat = readings_seat(book_dir, original, pid)
    levels = levels_of(book_dir, original)
    if original:
        same, worst, nb = validate(book_dir, seat, original, pid)
        print("VALIDATE readings replayed identically: %s (%d turns); worst affect diff vs the original's stored state %.3f "
              "(engine drift since that run — the half-lives were re-set after it; 0 would mean nothing changed)"
              % ("YES" if same else "NO — the input is not the run", nb, worst))
        if not same or args.validate_only:
            return 0 if same else 2
        base = score_vs_thermometer(book_dir, original, levels)
        print("ORIGINAL (as it ran, START half-lives)  state err %.3f  rest err %.3f  pinned %s" % (
            base["mean_abs_error_state"], base["mean_abs_error_rest"], base.get("pinned_turns")))

    if args.lambdas:
        table = json.loads(args.lambdas)
        RA.receive = _ORIG_RECEIVE
        for p, v in table.items():
            _rungs.LAMBDA[p] = float(v)
        rid = rerun(book_dir, seat)
        r = score_vs_thermometer(book_dir, rid, levels)
        bias = " ".join("%s %+.2f" % (p[:4], v["bias_median"]) for p, v in sorted(r["per_path"].items()))
        print("per-path lambdas %s\n  state err %.3f  rest err %.3f  %s | pinned %s" % (
            table, r["mean_abs_error_state"], r["mean_abs_error_rest"], bias, r.get("pinned_turns") or "-"))
        park(book_dir, rid)
        set_scale(1.0)
        return 0
    variants = ["additive", "anchored"] if args.variant == "both" else [args.variant]
    scales = [float(x) for x in args.scales.split(",") if x.strip()]
    print("\n%-9s %-6s %-9s %-9s  %s" % ("variant", "scale", "state", "rest", "per-path bias median (state - thermometer, height) / pinned turns"))
    for variant in variants:
        RA.receive = _ORIG_RECEIVE if variant == "additive" else anchored_receive(args.alpha, args.rho)
        for s in scales:
            set_scale(s)
            rid = rerun(book_dir, seat)
            r = score_vs_thermometer(book_dir, rid, levels)
            bias = " ".join("%s %+.2f" % (p[:4], v["bias_median"]) for p, v in sorted(r["per_path"].items()))
            print("%-9s %-6.2f %-9.3f %-9.3f  %s | pinned %s" % (
                variant, s, r["mean_abs_error_state"], r["mean_abs_error_rest"], bias, r.get("pinned_turns") or "-"))
            park(book_dir, rid)
    set_scale(1.0)
    RA.receive = _ORIG_RECEIVE
    return 0


if __name__ == "__main__":
    sys.exit(main())
