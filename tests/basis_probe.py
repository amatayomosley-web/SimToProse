#!/usr/bin/env python3
"""basis_probe.py — the blind-judge confusion matrix. Pre-registered in docs/basis-verification.md.

Step 4 of `emotion-basis.md` §"How the basis gets verified", which that doc says to run BEFORE
adding to the basis — and which did not happen: DISGUST, `attraction` and per-primitive targets all
landed first. Run late is better than not run.

THE QUESTION is one row of that doc's failure table:

    coordinates differ, rendered words do not  ->  the direction layer is the bottleneck, not the basis

The engine can compute coordinates that differ — shame and contempt carry identical magnitudes and
different targets, measured. Whether the WORDS carry that to a reader is unverified.

TWO ARMS, because one cannot attribute. Arm A renders without targets (the pre-session engine); arm
B renders with them. **The deliverable is B minus A.** An improvement present in both was never
about targets.

Judges see ONE rendered direction line and a closed candidate list. No character sheet, no numbers,
no target names, no intended label. Three judges from three model FAMILIES so one idiom cannot carry
the result. Order randomised per judge, deterministically.

    python tests/basis_probe.py            # both arms, all judges (~130 local calls)
    python tests/basis_probe.py --dry      # build stimuli and print them, no model calls
    python tests/basis_probe.py --judges qwen2.5:32b

Local Ollama only — no key, no cost. Results append to tests/basis_probe_results.jsonl.
"""
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.compounds import COMPOUNDS, blend                    # noqa: E402
from src.engine.direction import direct_affect                       # noqa: E402
from src.engine.records import PRIMARIES                             # noqa: E402

ME = "ren"                     # the fixture's own id — what makes a bind reflexive
OTHER = "the other"            # every object bind points here; never a book name (hard rule 1)
JUDGES = ("qwen2.5:32b", "gemma4:31b-it-q4_K_M", "mistral-small:latest")

# Group S — confusion INSIDE this family is a PASS. decision-engine.md wants contempt / disdain /
# scorn as neighbouring coordinates on purpose, so scoring them as errors would penalise the design
# for doing what it was designed to do.
SHADE_FAMILY = {"contempt", "disdain", "scorn"}

# Group R — pairs that differ by target ROLE. DERIVED, not hand-listed, because the hand-listed
# version went stale by this project's own hand and was not noticed until after a run:
# gate `compound-drift-repair` re-authored `passive_aggressive` and `spite` to all-object binds,
# and the list still named them. Verified after the fact — `mocking`, `passive_aggressive`, `spite`
# and `excited` all carry roles={object} — so two of the four "role-only pairs" carried NO target
# content when the probe ran, and any result scored under "role pairs separated" was measuring
# nothing. A derived list cannot drift from the table it describes.
#
# A pair qualifies when the two recipes share their primitives and magnitudes closely but assign
# DIFFERENT roles, and at least one of them binds reflexively on a primitive whose registry row
# says the direction changes — otherwise the arms render identically and the cell is dead before
# a judge sees it.
def _role_pairs(mag_tol=0.15):
    import itertools
    out = []
    for a, b in itertools.combinations(sorted(COMPOUNDS), 2):
        ra, rb = COMPOUNDS[a], COMPOUNDS[b]
        if set(ra) != set(rb):
            continue
        if max(abs(ra[p][0] - rb[p][0]) for p in ra) > mag_tol:
            continue
        if {(p, ra[p][1]) for p in ra} == {(p, rb[p][1]) for p in rb}:
            continue                                   # same roles: not a role pair
        live = any(r[1] == "self" and p in ("SEEKING", "DISGUST")
                   for rec in (ra, rb) for p, r in rec.items())
        if live:
            out.append((a, b))
    return tuple(out)


ROLE_PAIRS = _role_pairs()

# Group M — emotion-basis.md's own motivating case.
MOTIVATING = ("shame", "grief", "contempt")

# Group V — every compound that binds SEEKING or DISGUST REFLEXIVELY, which per
# `records.DIRECTEDNESS` are the only two primitives whose direction changes. These are the ONLY
# stimuli on which arm B can differ from arm A at all, so without them the B-minus-A comparison
# rests on `shame` and `pride` alone and the falsification in §7 would be decided by two states.
# Found by asking the table rather than by listing from memory.
REFLEXIVE_BEARING = tuple(sorted(
    n for n, r in COMPOUNDS.items()
    if any(role == "self" and p in ("SEEKING", "DISGUST") for p, (_w, role) in r.items())))

# Filled by run(): the stimuli whose two renders are not byte-identical.
DIFFERING_IDS = set()


def _fixture():
    with open(os.path.join(REPO, "characters", "ren-traveler.json"), encoding="utf-8") as fh:
        ch = json.load(fh)
    temp = ch["baseline"]["temperament"]
    base = {p: temp[p]["mean"] for p in PRIMARIES}
    return base, temp


def build_stimuli():
    """Every stimulus, with its intended label and its target map. Deterministic."""
    base, temp = _fixture()
    names = sorted(set(MOTIVATING) | SHADE_FAMILY | set(REFLEXIVE_BEARING)
                   | {n for pair in ROLE_PAIRS for n in pair})
    out = []
    for name in names:
        recipe = COMPOUNDS[name]
        targets = {p: (ME if r == "self" else OTHER) for p, (_w, r) in recipe.items()}
        out.append({"id": "cmp:%s" % name, "label": name, "kind": "compound",
                    "vector": blend(name, base), "targets": targets})

    # Group P — each primitive alone at the STRONG band, so "is DISGUST visible as itself?" is
    # answerable separately from "is contempt visible?".
    for p in PRIMARIES:
        v = dict(base)
        v[p] = 0.70
        out.append({"id": "one:%s" % p, "label": "ONLY_%s" % p, "kind": "primitive",
                    "vector": v, "targets": {p: OTHER}})

    # Group C — the controls that bound every other number.
    # AT TEMPERAMENT — and NOT the same thing as "nothing happening", which the first run of this
    # probe discovered the hard way. `direct_affect` surfaces any primary whose ABSOLUTE band is >=1,
    # so a character whose resting CARE is 0.60 is told "you act for them before you have finished
    # deciding to" on every beat, as if it were news. This fixture renders FOUR active clauses while
    # sitting exactly at its own means, so all three judges named a state and measure 5 "failed" on a
    # control that was mis-specified rather than on judges confabulating.
    out.append({"id": "ctl:at_temperament", "label": "NOTHING", "kind": "control",
                "vector": dict(base), "targets": {}})
    # GENUINELY FLAT — every primitive in the quiet band AND at its mean, so nothing is notable by
    # either test. This is the real confabulation control.
    flat = {p: 0.10 for p in PRIMARIES}
    out.append({"id": "ctl:flat", "label": "NOTHING", "kind": "control",
                "vector": flat, "targets": {}, "temperament_override":
                {p: {"mean": 0.10, "variability": 0.1} for p in PRIMARIES}})
    out.append({"id": "ctl:lust_unbound", "label": "ONLY_LUST", "kind": "control",
                "vector": dict(base, LUST=0.70), "targets": {}})   # no bind -> the unbound phrase
    dup = [s for s in out if s["id"] == "cmp:shame"][0]
    out.append(dict(dup, id="ctl:duplicate"))                      # planted reliability check
    return out, temp


def candidates():
    """The closed list a judge picks from. Includes every intended label plus 'none of these'."""
    names = sorted(set(MOTIVATING) | SHADE_FAMILY | set(REFLEXIVE_BEARING)
                   | {n for pair in ROLE_PAIRS for n in pair})
    return names + ["just %s and nothing else" % p.lower() for p in PRIMARIES] + ["nothing in particular"]


_LABEL_TO_CHOICE = {}


def _choice_for(label):
    if label == "NOTHING":
        return "nothing in particular"
    if label.startswith("ONLY_"):
        return "just %s and nothing else" % label[5:].lower()
    return label


def _ollama(model, prompt, seed):
    # think=False and a larger num_predict: gemma4 is a THINKING model, and its hidden trace
    # otherwise consumes the budget and returns an EMPTY string. Measured in the first run of this
    # probe — 55 of 162 replies were empty, almost all gemma4 — and already documented in
    # scripts/direct.py:_ollama ("the hidden trace otherwise consumes the token budget and empties
    # the reply"). The repo knew; this probe did not ask.
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False,
                       "options": {"temperature": 0.0, "seed": seed, "num_predict": 200}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r).get("response", "")


def judge_prompt(line, options):
    return (
        "Below is a set of stage directions given to an actor — instructions for how to behave in a "
        "scene. They were generated from one underlying emotional state.\n\n"
        "STAGE DIRECTIONS:\n%s\n\n"
        "Which ONE of these is the state they were generated from?\n%s\n\n"
        "Answer with the option text alone, exactly as written above, and nothing else. If none of "
        "them fits, answer: nothing in particular"
        % (line, "\n".join("- %s" % o for o in options)))


def _parse(reply, options):
    """A number first; the option text as a fallback so a wordy judge is still counted."""
    m = re.search(r"\b(\d{1,2})\b", reply or "")
    if m:
        i = int(m.group(1)) - 1
        if 0 <= i < len(options):
            return options[i]
    r = " ".join((reply or "").strip().lower().split())
    for o in sorted(options, key=len, reverse=True):      # longest first: "just rage..." before "rage"
        if o.lower() in r:
            return o
    return None


def run(judges, arms=("A", "B"), dry=False, out_path=None):
    stimuli, temp = build_stimuli()
    opts = candidates()
    print("stimuli: %d | candidates: %d | judges: %s" % (len(stimuli), len(opts), ", ".join(judges)))

    rendered = {}
    for s in stimuli:
        tt = s.get("temperament_override") or temp
        rendered[("A", s["id"])] = direct_affect(s["vector"], tt)
        rendered[("B", s["id"])] = direct_affect(s["vector"], tt,
                                                 targets=s["targets"], me=ME)
    DIFFERING_IDS.clear()
    DIFFERING_IDS.update(s["id"] for s in stimuli
                         if rendered[("A", s["id"])] != rendered[("B", s["id"])])
    diff = len(DIFFERING_IDS)

    # DEAD-CELL GUARD. A pair can be a role pair by RECIPE and render identically anyway — measured:
    # `embarrassment` carries DISGUST (0.20, "self") which blends to 0.2375, under the 0.25 band
    # floor with deviation 0.0875 against a 0.15 threshold, so its reflexive ingredient produces no
    # clause at all. Scoring such a cell under "role pairs separated" measures nothing, and that is
    # exactly what happened before anyone checked. Recipe liveness is not render liveness.
    for a, b in ROLE_PAIRS:
        if not ({"cmp:%s" % a, "cmp:%s" % b} & DIFFERING_IDS):
            print("  ! DEAD CELL: %s~%s renders IDENTICALLY in both arms — its reflexive ingredient"
                  % (a, b))
            print("    never clears the band floor. Any score for this pair measures nothing.")
    print("arms differ on %d of %d stimuli (the rest have no reflexive bind, so B == A by design)\n"
          % (diff, len(stimuli)))

    if dry:
        for s in stimuli:
            tag = "  <-- arms differ" if rendered[("A", s["id"])] != rendered[("B", s["id"])] else ""
            print("== %-22s %s%s" % (s["id"], _choice_for(s["label"]), tag))
            print("   %s\n" % rendered[("B", s["id"])][:300])
        return 0

    rows = []
    for judge in judges:
        for arm in arms:
            order = list(stimuli)
            random.Random("%s|%s" % (judge, arm)).shuffle(order)
            for i, s in enumerate(order):
                line = rendered[(arm, s["id"])]
                shuffled = list(opts)
                random.Random("%s|%s|%s" % (judge, arm, s["id"])).shuffle(shuffled)
                t0 = time.time()
                try:
                    reply = _ollama(judge, judge_prompt(line, shuffled), seed=1000 + i)
                except Exception as exc:                      # a dead model must not void the run
                    print("  ! %s %s %s -> %s" % (judge, arm, s["id"], str(exc)[:60]))
                    continue
                got = _parse(reply, shuffled)
                want = _choice_for(s["label"])
                rows.append({"judge": judge, "arm": arm, "id": s["id"], "kind": s["kind"],
                             "intended": want, "answered": got, "raw": reply.strip()[:120],
                             "secs": round(time.time() - t0, 1)})
                print("  %-22s %-4s %-24s -> %-28s %s"
                      % (judge.split(":")[0], arm, s["id"], (got or "(unparsed)")[:28],
                         "OK" if got == want else ""))
    if out_path:
        with open(out_path, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print("\n%d judgements -> %s" % (len(rows), out_path))
    score(rows)
    return 0


def score(rows):
    """The six measures, exactly as pre-registered in docs/basis-verification.md §5."""
    if not rows:
        print("no judgements")
        return
    shade = {c.lower() for c in SHADE_FAMILY}

    def hit(r, collapse_shade=False):
        a, i = (r["answered"] or "").lower(), r["intended"].lower()
        if collapse_shade and a in shade and i in shade:
            return True
        return a == i

    print("\n" + "=" * 74)
    print("MEASURES (pre-registered thresholds in docs/basis-verification.md §5)")
    print("=" * 74)

    for arm in sorted({r["arm"] for r in rows}):
        A = [r for r in rows if r["arm"] == arm]
        # Pre-registered as "2 of 3", i.e. a MAJORITY of judges. Scaled to the judge count so a
        # pilot with fewer judges is not reported as a structural FAIL it could never have passed.
        njudges = len({r["judge"] for r in A})
        need = njudges // 2 + 1
        core = [r for r in A if r["kind"] != "control" and r["intended"].lower() not in shade]
        sh = [r for r in A if r["intended"].lower() in shade]
        m1 = sum(hit(r) for r in core) / len(core) if core else 0
        m2 = sum(hit(r, True) for r in sh) / len(sh) if sh else 0
        print("\nARM %s   (n=%d)" % (arm, len(A)))
        print("  1 exact match, non-shade          %5.1f%%   (threshold 40%%)  %s"
              % (m1 * 100, "PASS" if m1 >= 0.40 else "FAIL"))
        print("  2 shade-family match              %5.1f%%   (threshold 65%%)  %s"
              % (m2 * 100, "PASS" if m2 >= 0.65 else "FAIL"))
        sg = [r for r in A if r["id"] == "cmp:shame"]
        not_grief = sum(1 for r in sg if (r["answered"] or "").lower() != "grief")
        print("  3 shame NOT called grief          %d of %d judges   (threshold %d)  %s"
              % (not_grief, len(sg), need, "PASS" if not_grief >= need else "FAIL"))
        for a, b in ROLE_PAIRS:
            ra = [r for r in A if r["id"] == "cmp:%s" % a]
            rb = [r for r in A if r["id"] == "cmp:%s" % b]
            sep = sum(1 for x, y in zip(ra, rb) if (x["answered"] or "") != (y["answered"] or ""))
            print("  4 %-12s vs %-18s %d of %d judges separated   (threshold %d)  %s"
                  % (a, b, sep, min(len(ra), len(rb)), need, "PASS" if sep >= need else "FAIL"))
        rest = [r for r in A if r["id"] == "ctl:flat"]
        named = sum(1 for r in rest if (r["answered"] or "") != "nothing in particular")
        allowed = njudges // 3          # pre-registered "<=1 of 3"
        print("  5 FLAT control names a state      %d of %d judges   (threshold <=%d)  %s"
              % (named, len(rest), allowed, "PASS" if named <= allowed else "FAIL"))
        atv = [r for r in A if r["id"] == "ctl:at_temperament"]
        atn = sum(1 for r in atv if (r["answered"] or "") != "nothing in particular")
        print("  5b at-temperament names a state   %d of %d judges   (not a threshold — a FINDING:"
              % (atn, len(atv)))
        print("                                       resting renders 4 active clauses)")
        agree = 0
        for j in {r["judge"] for r in A}:
            x = [r["answered"] for r in A if r["judge"] == j and r["id"] == "cmp:shame"]
            y = [r["answered"] for r in A if r["judge"] == j and r["id"] == "ctl:duplicate"]
            if x and y and x[0] == y[0]:
                agree += 1
        print("  6 planted duplicate self-agree    %d of %d judges   (threshold %d)  %s   %s"
              % (agree, njudges, need,
                 "PASS" if agree >= need else "FAIL",
                 "" if agree >= need else "<-- 1-4 UNINTERPRETABLE, RUN VOID"))

    if len({r["arm"] for r in rows}) == 2:
        def rate(arm, ids=None):
            c = [r for r in rows if r["arm"] == arm and r["kind"] != "control"
                 and r["intended"].lower() not in shade and (ids is None or r["id"] in ids)]
            return (sum(hit(r) for r in c) / len(c), len(c)) if c else (0.0, 0)

        # THE SUBSET THAT MATTERS. Only a stimulus carrying a reflexive bind on a primitive whose
        # registry row says direction_changes renders differently between arms; for every other
        # stimulus B IS A, character for character. Averaging across all of them dilutes a real
        # effect with identical renders, so both are reported and §7's falsification is decided on
        # the differing subset.
        differ = {i for i in DIFFERING_IDS if not i.startswith("ctl:")}
        print("\n" + "-" * 74)
        for label, ids in (("ALL core stimuli", None), ("stimuli where the arms DIFFER", differ)):
            b, nb = rate("B", ids)
            a, na = rate("A", ids)
            print("B MINUS A, %-30s %+6.1f pts   [A %5.1f%%  B %5.1f%%  n=%d]"
                  % (label, (b - a) * 100, a * 100, b * 100, min(na, nb)))
        print("docs/basis-verification.md §7: the targets build is FALSIFIED if B is not better")
        print("-" * 74)
        return

# --------------------------------------------------------------------------------------------
# PAIRWISE (2AFC) — the redesign, after 25-way recognition proved unmeasurable.
#
# The first two runs asked a judge to pick one state from 25. Measured: 4.5-18.2% accuracy against
# ~4% chance, and five of six judge-arm pairs gave a DIFFERENT answer to the identical rendered
# line when only the option order changed. A near-chance judge disagrees with itself, so measures
# 1-4 were uninterpretable by the pre-registration's own rule.
#
# That is a finding about the TASK, not yet about the direction layer: 25-way recognition from
# behaviour alone is too hard for these models. Forced choice between TWO named states puts chance
# at 50%, and asks only the discriminations the design actually claims to make.
#
# Same blinding: the judge sees one render and two names, never which was intended, never a number.
# Both orderings of every pair are run, so an order-preferring judge scores 50% rather than 100%.
# --------------------------------------------------------------------------------------------

PAIRS_2AFC = (
    ("shame", "grief"),        # emotion-basis.md's own motivating case
    ("shame", "contempt"),     # identical magnitudes, opposite aim — what targets were built for
    ("excited", "pride"),
    ("cold", "embarrassment"),
    ("mocking", "passive_aggressive"),
    ("mocking", "spite"),
)


def pair_prompt(line, a, b):
    return ("Below are stage directions given to an actor — instructions for how to behave in a "
            "scene. They were generated from ONE of two emotional states.\n\n"
            "STAGE DIRECTIONS:\n%s\n\n"
            "Was this generated from %s, or from %s?\n\n"
            "Reply with one word: either \"%s\" or \"%s\". Nothing else."
            % (line, a, b, a, b))


def run_pairwise(judges, out_path=None):
    stimuli, temp = build_stimuli()
    by_id = {s["id"]: s for s in stimuli}
    rows = []
    for judge in judges:
        for arm in ("A", "B"):
            for a, b in PAIRS_2AFC:
                for intended in (a, b):
                    s = by_id["cmp:%s" % intended]
                    tt = s.get("temperament_override") or temp
                    line = (direct_affect(s["vector"], tt) if arm == "A"
                            else direct_affect(s["vector"], tt, targets=s["targets"], me=ME))
                    for first, second in ((a, b), (b, a)):      # both orders, always
                        reply = _ollama(judge, pair_prompt(line, first, second), seed=7)
                        r = (reply or "").strip().lower()
                        got = a if (a in r and b not in r) else (b if b in r else None)
                        rows.append({"judge": judge, "arm": arm, "pair": "%s|%s" % (a, b),
                                     "intended": intended, "order": "%s,%s" % (first, second),
                                     "answered": got, "raw": (reply or "").strip()[:60]})
    if out_path:
        with open(out_path, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    score_pairwise(rows)
    return rows


def score_pairwise(rows):
    print("\n" + "=" * 74)
    print("PAIRWISE (2AFC) — chance is 50%%.  n=%d judgements" % len(rows))
    print("=" * 74)
    unp = sum(1 for r in rows if r["answered"] is None)
    print("unparsed: %d (%.1f%%)\n" % (unp, 100 * unp / max(len(rows), 1)))
    print("%-30s %8s %8s %8s" % ("pair", "arm A", "arm B", "B - A"))
    print("-" * 58)
    for pair in [p for p in ("%s|%s" % p for p in PAIRS_2AFC)]:
        cells = {}
        for arm in ("A", "B"):
            c = [r for r in rows if r["pair"] == pair and r["arm"] == arm and r["answered"]]
            cells[arm] = (sum(1 for r in c if r["answered"] == r["intended"]) / len(c)) if c else None
        a, b = cells["A"], cells["B"]
        print("%-30s %7s%% %7s%% %+7s" % (
            pair.replace("|", " vs "),
            "%.0f" % (a * 100) if a is not None else "--",
            "%.0f" % (b * 100) if b is not None else "--",
            "%.0f" % ((b - a) * 100) if (a is not None and b is not None) else "--"))
    for arm in ("A", "B"):
        c = [r for r in rows if r["arm"] == arm and r["answered"]]
        if c:
            print("\nARM %s overall: %.1f%%  (chance 50%%)"
                  % (arm, 100 * sum(1 for r in c if r["answered"] == r["intended"]) / len(c)))

# ==============================================================================================
# COMPARATIVE (--compare) — the instrument that can actually reach the targets question.
#
# Runs 1-3 could not. Recounted after the fact: of run 3's twelve pair-member stimuli the arms
# differed on THREE, for three stacked reasons — `ROLE_PAIRS` had gone stale when
# `compound-drift-repair` re-authored two pairs to all-object binds; `cold`~`embarrassment` is a
# role pair by recipe that renders identically because embarrassment's DISGUST (0.20, "self")
# blends to 0.2375, under the 0.25 band floor; and the one cell where arm B genuinely widened the
# gap was answered "pride" 24/24 regardless of stimulus.
#
# TWO FIXES, both forced by that data:
#
#   1. ISOLATE. One vector, rendered twice with ONLY the target flipped. Not `blend(compound)`,
#      where paired states differ in magnitude AND aboutness and a judge can score well by reading
#      intensity alone — which is how shame|contempt hit 92% in BOTH arms.
#   2. COMPARE, do not classify. Run 3's judges were near-perfectly self-consistent (3 order-flips
#      in 72; gemma4 and qwen2.5 zero in 48 each) and still answered one constant name per pair.
#      That is a stable naming policy, not noise, so more n in a classify format would never move
#      it. Showing BOTH renders and asking which is which removes the prior's purchase.
#
# THE FIXTURE AXIS answers the noise-floor question in the same run, at no extra design cost:
# each pair renders on the ordinary fixture (four standing at-rest clauses present — SEEKING 0.50,
# CARE 0.55, PANIC_GRIEF 0.25, PLAY 0.35 all clear band 1 at their own means) AND on a flat
# fixture where the differing clause is most of the text. Flat passing while ordinary fails
# indicts the standing clauses specifically, and the repair is salience grouping rather than
# phrases.
#
# PRE-REGISTERED, fixed before any call:
#   PRIMARY  flat cells pooled over both pairs, n=24: PASS >= 18/24 (75%; binomial p ~ 0.011).
#            <= 17/24 is FAIL-to-carry. No gray zone.
#   FLOOR    flat >=18 and ordinary >=18 -> floor harmless at this legibility level.
#            flat >=18 and ordinary <=14 -> the standing clauses ARE the binding constraint.
#            flat <=17 -> the phrases fail regardless of floor.
#   VOID     positive control (the full-blend shame|contempt pair, comparative) < 10/12, or the
#            identical-render bias floor rejecting p=0.5 by a two-sided exact binomial test at
#            alpha<=0.05, or fewer than 4 of the floor's 12 asks answered at all.
#
#            THE FLOOR BAND WAS "outside 2-10 of 12" AND THE FLOOR EMITTED 6 ROWS. `first` could
#            never exceed 6, so the excess-ONE arm was unreachable from the day it shipped — half
#            a control, and the surviving half was an ABSOLUTE count over a denominator that
#            SHRINKS when judges behave correctly (refusing to separate two identical renders is
#            the right answer, and each refusal made the void more likely). The first replacement
#            written for it, a [0.2,0.8] proportion band, was no better: at n=6 fair judges void
#            21.9% of the time. A control that fair coins fail one run in five is a dice roll.
#            The exact test scales with however many answer, which is the property both earlier
#            forms lacked; at n=12 it rejects on counts <=2 or >=10, a 3.9% false-void rate.
#            Pre-registered 2026-08-24 BEFORE the next run was drawn (docs/basis-verification.md
#            §11), which is the only thing that makes it legal to change at all.
# ==============================================================================================

# The isolated pairs. Each is ONE vector rendered under two target maps — magnitudes identical by
# construction, so anything a judge recovers is aboutness and nothing else.
COMPARE_PAIRS = (
    # DISGUST: the measured end-state of tests/test_targets.py — three social violations, one by
    # another party and one by the character themselves. RAGE is unbound in the reflexive case
    # because retarget rule 3 drops a bind the registry does not admit.
    {"key": "disgust", "names": ("contempt", "shame"),
     "vector": {"DISGUST": 0.556, "RAGE": 0.572},
     "targets": ({"DISGUST": OTHER, "RAGE": OTHER}, {"DISGUST": ME})},
    # SEEKING: pursuit vs display, the other cell where the registry says direction_changes.
    {"key": "seeking", "names": ("excited", "pride"),
     "vector": {"SEEKING": 0.60},
     "targets": ({"SEEKING": OTHER}, {"SEEKING": ME})},
)


def _compare_render(spec, which, flat):
    """One side of a pair. `flat` strips the standing clauses by flattening the temperament."""
    base, temp = _fixture()
    if flat:
        base = {p: 0.10 for p in PRIMARIES}
        temp = {p: {"mean": 0.10, "variability": 0.1} for p in PRIMARIES}
    v = dict(base)
    v.update(spec["vector"])
    return direct_affect(v, temp, targets=spec["targets"][which], me=ME)


def compare_prompt(one, two, asked):
    return ("Two actors were each given stage directions — instructions for how to behave in a "
            "scene. One was in a state of %s. The other was in a state of %s.\n\n"
            "ACTOR ONE:\n%s\n\nACTOR TWO:\n%s\n\n"
            "Which actor was in a state of %s? Reply with one word: ONE or TWO."
            % (one[1], two[1], one[0], two[0], asked))


def _choice(reply):
    """The judge's answer: the FIRST of ONE/TWO that appears as a WORD.

    The rule this replaces was `"ONE" if ("ONE" in r and "TWO" not in r) else ("TWO" if "TWO" in
    r else None)` — a substring test over the whole reply, and it was wrong in two directions at
    once. It scored REFUSALS as answers, because ONE is a substring of NONE, DONE, ALONE and
    SOMEONE: "none of them" registered as the answer ONE. And it INVERTED any reply that named
    its choice and then discussed the alternative, because "ONE. Actor two is calmer" contains
    TWO and fell to the second branch — a directional bias against ONE, in a control whose whole
    job is to detect directional bias.

    Caught 2026-08-23: the bias-floor control voided on a rerun where mistral-small returned the
    SAME refusal it had returned before and it parsed differently — the stored `raw` was clipped
    at 40 characters, so the log could not explain its own numbers. Judges answer first and
    explain after, so first-word-wins is the rule that matches how they actually reply.
    """
    r = (reply or "").strip().upper()
    # "NO ONE" and "NEITHER ONE" are REFUSALS whose second word is the answer token. Word
    # boundaries alone do not save you — \bONE\b matches inside "no one seems different", which is
    # how the first repair of this parser still scored a refusal as an answer. Found 2026-08-24 by
    # tests/test_basis_parser.py, one day after that repair shipped, which is the argument for the
    # harness rather than for the fix.
    r = re.sub(r"\b(?:NO|NEITHER|NOT)\s+(?:ONE|TWO)\b", " ", r)
    m = re.search(r"\b(ONE|TWO)\b", r)
    return m.group(1) if m else None


def test__choice():
    """The control for the control. Every case below is a real reply shape from a probe run."""
    cases = [("ONE", "ONE"), ("TWO", "TWO"), ("one", "ONE"),
             ("ONE. Actor two is calmer.", "ONE"),        # was TWO — the inversion
             ("TWO, because one of them is louder", "TWO"),
             ("none of them", None), ("I am not done", None), ("alone", None),
             ("someone", None),                            # all were ONE — refusals as answers
             ("I don't have enough information to determine", None),
             ("Impossible", None), ("Neither", None), ("", None), (None, None),
             ("no one seems different", None), ("neither one stands out", None),
             ("not one of them", None),
             ("no one? TWO, if forced", "TWO")]        # a refusal that then answers still answers
    bad = [(r, want, _choice(r)) for r, want in cases if _choice(r) != want]
    if bad:
        raise AssertionError("_choice mis-parsed: %r" % (bad,))
    return len(cases)


def run_compare(judges, out_path=None):
    rows = []

    def ask(judge, label, fixture, texts, names, asked_idx, seed):
        """`texts` and `names` are permuted TOGETHER, so texts[i] IS the render for names[i]. The
        correct answer to "which actor was in state names[k]?" is therefore always slot k.

        The first version of this carried an extra `intended_idx` term and scored roughly half the
        correct answers as wrong, which manufactures exactly chance — and did: the positive control,
        a pair read at 92% in the classify format, came back 6/12. A scorer that can only produce
        chance is indistinguishable from a null result, which is the most expensive kind of bug an
        experiment can have."""
        reply = _ollama(judge, compare_prompt((texts[0], names[0]), (texts[1], names[1]),
                                              names[asked_idx]), seed=seed)
        got = _choice(reply)
        want = ("ONE", "TWO")[asked_idx]
        rows.append({"judge": judge, "cell": label, "fixture": fixture, "asked": names[asked_idx],
                     "answered": got, "correct": (got == want) if got else None,
                     "raw": (reply or "").strip()[:400]})

    for judge in judges:
        for spec in COMPARE_PAIRS:
            for flat in (True, False):
                fixture = "flat" if flat else "ordinary"
                a, b = _compare_render(spec, 0, flat), _compare_render(spec, 1, flat)
                na, nb = spec["names"]
                # both assignments x both question forms: an order- or question-preferring judge
                # scores exactly 50% rather than 100%
                for swap in (0, 1):
                    texts = (b, a) if swap else (a, b)
                    names = (nb, na) if swap else (na, nb)
                    for asked_idx in (0, 1):
                        ask(judge, spec["key"], fixture, texts, names, asked_idx, seed=11)

        # positive control: the full-blend pair run 3 read at 92%, in comparative form
        stim, temp = build_stimuli()
        by = {s["id"]: s for s in stim}
        sa, sb = by["cmp:shame"], by["cmp:contempt"]
        ta = direct_affect(sa["vector"], temp, targets=sa["targets"], me=ME)
        tb = direct_affect(sb["vector"], temp, targets=sb["targets"], me=ME)
        for swap in (0, 1):
            texts = (tb, ta) if swap else (ta, tb)
            names = ("contempt", "shame") if swap else ("shame", "contempt")
            for asked_idx in (0, 1):
                ask(judge, "POSITIVE", "ordinary", texts, names, asked_idx, seed=11)

        # bias floor: two IDENTICAL renders, so no signal exists. TWELVE asks, not six — one
        # spec's two asks could never reach the pre-registered band's upper arm, and six is too
        # few for any band to distinguish bias from noise once refusals thin it further.
        for spec in COMPARE_PAIRS:
            same = _compare_render(spec, 0, False)
            for asked_idx in (0, 1):
                ask(judge, "BIASFLOOR", "ordinary", (same, same), spec["names"], asked_idx, seed=11)

    if out_path:
        with open(out_path, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    score_compare(rows)
    return rows


_FLOOR_MIN_ANSWERS = 4          # below this the control has not run, however the counts fall


def _binomial_rejects(k, n, alpha=0.05):
    """Two-sided exact binomial test of p=0.5 — does `k` of `n` reject chance?

    An ABSOLUTE band cannot be right here, because the denominator is however many judges chose to
    answer, and refusing to separate two identical renders is the CORRECT response. Every earlier
    form of this control punished good behaviour: "outside 2-10 of 12" over 6 emitted rows had an
    unreachable upper arm, and a [0.2,0.8] proportion band voids on 21.9% of fair-coin runs at n=6.
    The exact test scales with n, which is the property both lacked.
    """
    if not n:
        return False
    from math import comb
    tail = sum(comb(n, i) for i in range(0, min(k, n - k) + 1))
    return (2.0 * tail / (2 ** n)) <= alpha


def score_compare(rows):
    def cell(key, fixture=None):
        c = [r for r in rows if r["cell"] == key and (fixture is None or r["fixture"] == fixture)
             and r["correct"] is not None]
        return sum(1 for r in c if r["correct"]), len(c)

    print("\n" + "=" * 74)
    print("COMPARATIVE (isolated stimuli, both renders shown).  n=%d" % len(rows))
    print("=" * 74)
    unp = sum(1 for r in rows if r["answered"] is None)
    print("unparsed: %d\n" % unp)

    pc, pn = cell("POSITIVE")
    bf, bn = cell("BIASFLOOR")
    first = sum(1 for r in rows if r["cell"] == "BIASFLOOR" and r["answered"] == "ONE")
    floor_n = sum(1 for r in rows if r["cell"] == "BIASFLOOR" and r["answered"])
    thin = floor_n < _FLOOR_MIN_ANSWERS
    biased = floor_n and _binomial_rejects(first, floor_n)
    print("CONTROLS")
    print("  positive (shame|contempt, full blend)  %d/%d   (void if < 10/12)  %s"
          % (pc, pn, "OK" if pn and pc >= 10 else "VOID"))
    print("  bias floor (identical renders)         answered ONE %d of %d answered, %d asked  %s"
          % (first, floor_n, sum(1 for r in rows if r["cell"] == "BIASFLOOR"),
             "VOID: too few answered" if thin else ("VOID: directional" if biased else "OK")))
    if thin:
        print("           -> the judges would not play the control; that is its own finding, and")
        print("              it is NOT evidence that bias is absent.")

    print("\nCELLS")
    print("  %-12s %-12s %-12s" % ("", "flat", "ordinary"))
    for spec in COMPARE_PAIRS:
        f = cell(spec["key"], "flat")
        o = cell(spec["key"], "ordinary")
        print("  %-12s %-12s %-12s   (%s vs %s)"
              % (spec["key"], "%d/%d" % f, "%d/%d" % o, spec["names"][0], spec["names"][1]))

    fc = sum(cell(s["key"], "flat")[0] for s in COMPARE_PAIRS)
    fn = sum(cell(s["key"], "flat")[1] for s in COMPARE_PAIRS)
    oc = sum(cell(s["key"], "ordinary")[0] for s in COMPARE_PAIRS)
    on = sum(cell(s["key"], "ordinary")[1] for s in COMPARE_PAIRS)
    print("\n" + "-" * 74)
    print("PRIMARY  flat pooled  %d/%d   (threshold >=18/24)   %s"
          % (fc, fn, "PASS — the phrases carry aboutness" if fc >= 18 else "FAIL-to-carry"))
    print("FLOOR    ordinary     %d/%d" % (oc, on))
    if fc >= 18 and oc >= 18:
        print("         -> noise floor HARMLESS at this legibility level")
    elif fc >= 18 and oc <= 14:
        print("         -> the STANDING CLAUSES are the binding constraint; repair is salience")
        print("            grouping, not phrases (SPEC-LEDGER: 'Direction reads a salience order')")
    elif fc <= 17:
        print("         -> the phrases fail REGARDLESS of floor; repair is the phrases themselves")
    else:
        print("         -> between the pre-registered cases; report as inconclusive, do not reinterpret")
    print("-" * 74)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judges", default=",".join(JUDGES))
    ap.add_argument("--arms", default="A,B")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--compare", action="store_true",
                    help="isolated stimuli, both renders shown; also rules on the noise floor")
    ap.add_argument("--pairwise", action="store_true",
                    help="forced 2-alternative choice; chance 50%% instead of 4%%")
    ap.add_argument("--out", default=os.path.join(REPO, "tests", "basis_probe_results.jsonl"))
    args = ap.parse_args()
    if args.compare:
        run_compare([j for j in args.judges.split(",") if j],
                    out_path=args.out.replace(".jsonl", "_compare.jsonl"))
        return 0
    if args.pairwise:
        run_pairwise([j for j in args.judges.split(",") if j],
                     out_path=args.out.replace(".jsonl", "_2afc.jsonl"))
        return 0
    return run([j for j in args.judges.split(",") if j],
               tuple(a for a in args.arms.split(",") if a), dry=args.dry, out_path=args.out)


if __name__ == "__main__":
    sys.exit(main())
