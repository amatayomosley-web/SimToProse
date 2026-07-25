#!/usr/bin/env python3
"""test_faults.py — the engine-fault detector (faults.py). Proves the machine-side twin of the
world-fault inbox: a recurring consolidation-flag reason (a dimension no actor-type legitimizes)
is aggregated across a run into a named "missing actor type" engine-fault, while a one-off flag
stays below the threshold; the escalation rate is computed and a hot rate is flagged; unused
vocabulary surfaces over a long-enough run. Script-style, stdlib, exit 0 = all pass.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import faults                                   # noqa: E402
from src.engine.ledger import Ledger                            # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


# The exact flag shape consolidation.validate_tags emits for a type/dimension mismatch.
def _dim_mismatch_flag(dim, val, tag_type, legit):
    return "containment: dimension %r (%.2f) not in appraisal_map for type %r (legitimate dims: %s)" % (
        dim, val, tag_type, sorted(legit))


_SOCIAL_FLAG = _dim_mismatch_flag("social_violation", 0.65, "threat", ["care_relevant", "loss", "threat"])


def _gap_turn(dim=_SOCIAL_FLAG):
    return ({"type": "threat", "dimensions": {"social_violation": 0.65, "threat": 0.5}, "durability": "transient"},
            {"ok": True, "flags": [dim], "confidence": 0.37, "escalate": True})


def _clean_turn():
    return ({"type": "mundane", "dimensions": {"mastery": 0.3}, "durability": "transient"},
            {"ok": True, "flags": [], "confidence": 0.55, "escalate": False})


def _put_turn(led, run_id, turn, actor, tags, validation):
    led.con.execute(
        "INSERT INTO turns (run_id, turn, actor, thought, action, tags, validation, committed_at) "
        "VALUES (?, ?, ?, '', '', ?, ?, '')",
        (run_id, turn, actor, json.dumps(tags), json.dumps(validation)))
    led.con.commit()


def _run(turns, actor="selven", run_id="r1"):
    """Build a tmp ledger, create a run, insert the given (tags, validation) turns; return (led, run_id, tmp)."""
    tmp = tempfile.mkdtemp(prefix="swe_faults_")
    led = Ledger(os.path.join(tmp, "f.db"))
    led.create_run(run_id, {"catalog_version": 1})
    for i, (tags, val) in enumerate(turns):
        _put_turn(led, run_id, i, actor, tags, val)
    return led, run_id, tmp


def test_reason_key():
    """Flag strings normalize to a structural (kind, subject) key; the SUBJECT of a dim-mismatch
    is the DIMENSION (the thing without a home), not the chosen type."""
    print("\n[1] REASON_KEY normalization")
    check("dim-unsupported-keys-on-dimension", faults.reason_key(_SOCIAL_FLAG) == ("dim-unsupported", "social_violation"),
          str(faults.reason_key(_SOCIAL_FLAG)))
    check("unknown-dim", faults.reason_key("schema: unknown dimension 'wibble'") == ("unknown-dim", "wibble"))
    check("unknown-type", faults.reason_key("schema: unknown type 'frobnicate'") == ("unknown-type", "frobnicate"))
    check("target-not-perceived", faults.reason_key("containment: target 'ghost' not perceived in PerceptSet") == ("target-not-perceived", None))
    check("capability", faults.reason_key("capability: skill 'combat' = 0.10 < required 0.30 for type 'harm'") == ("capability-miss", "combat"))
    check("schema-other", faults.reason_key("schema: durability None not in {transient, durable}") == ("schema-other", None))
    check("non-string-safe", faults.reason_key(None) == ("other", None))


def test_recurring_gap_becomes_fault():
    """The flagship: the SAME dimension unsupported across turns -> one engine-fault naming it,
    with a fix direction. Counts TURNS, names social_violation, points at the missing type."""
    print("\n[2] RECURRING GAP -> NAMED FAULT (the social_violation hole)")
    led, rid, tmp = _run([_gap_turn(), _clean_turn(), _gap_turn()])
    try:
        res = faults.scan_run(led, rid)
        gap = [f for f in res["faults"] if f["kind"] == "dim-unsupported"]
        check("one-dim-unsupported-fault", len(gap) == 1, str([f["kind"] for f in res["faults"]]))
        if gap:
            check("subject-is-the-dimension", gap[0]["subject"] == "social_violation", gap[0]["subject"])
            check("counts-turns-not-flags", gap[0]["count"] == 2, str(gap[0]["count"]))
            check("names-fix-direction", "actor-taggable type" in gap[0]["message"])
            check("localizes-to-actor", gap[0]["actors"] == ["selven"], str(gap[0]["actors"]))
        check("escalation-rate-2of3", abs(res["stats"]["escalation_rate"] - 0.667) < 0.01, str(res["stats"]["escalation_rate"]))
        check("hot-escalation-flagged", any(f["kind"] == "escalation-rate-hot" for f in res["faults"]))
        rep = faults.render(res)
        check("render-names-the-gap", "social_violation" in rep and "GAP" in rep, rep)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_oneoff_below_threshold():
    """A single mismatch is noise, not a structural gap — no fault, no hot-escalation."""
    print("\n[3] ONE-OFF STAYS BELOW THRESHOLD")
    led, rid, tmp = _run([_gap_turn(), _clean_turn(), _clean_turn()])
    try:
        res = faults.scan_run(led, rid)
        check("no-dim-fault-on-single", not any(f["kind"] == "dim-unsupported" for f in res["faults"]),
              str([f["kind"] for f in res["faults"]]))
        check("no-hot-escalation-1of3", not any(f["kind"] == "escalation-rate-hot" for f in res["faults"]))
        check("clean-render", "(none" in faults.render(res) or "social_violation" not in faults.render(res))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_unused_vocab_over_long_run():
    """Over a run >= 10 turns, an actor-taggable type never chosen surfaces as a low-severity note."""
    print("\n[4] UNUSED VOCABULARY (long run)")
    led, rid, tmp = _run([_clean_turn() for _ in range(12)])   # all 'mundane'
    try:
        res = faults.scan_run(led, rid)
        unused = [f for f in res["faults"] if f["kind"] == "unused-type"]
        check("unused-types-surface", len(unused) >= 1, str([f["subject"] for f in unused]))
        check("care-or-threat-flagged-unused", any(f["subject"] in ("care", "threat", "loss", "aid") for f in unused))
        check("unused-is-low-severity", all(f["severity"] == "low" for f in unused))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_empty_and_fail_loud():
    print("\n[5] EMPTY RUN + FAIL LOUD")
    led, rid, tmp = _run([])
    try:
        res = faults.scan_run(led, rid)
        check("empty-run-no-faults", res["faults"] == [] and res["stats"]["turns"] == 0)
        check("empty-render", "no turns" in faults.render(res))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for bad in (lambda: faults.scan_run("notaledger", "r1"), lambda: faults.render("notadict")):
        try:
            bad(); check("fail-loud", False, "accepted bad input"); return
        except ValueError:
            pass
    check("fail-loud-all", True)


def main():
    print("test_faults.py — the engine-fault detector\n")
    for t in (test_reason_key, test_recurring_gap_becomes_fault, test_oneoff_below_threshold,
              test_unused_vocab_over_long_run, test_empty_and_fail_loud):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
