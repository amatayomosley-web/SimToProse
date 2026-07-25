#!/usr/bin/env python3
"""test_arc.py — the Arc Engine (durable baseline change). Proves arc-engine.md's core:
the slow-burn arc (a bond raising affinity + eroding class-disregard), the durable threshold
(most events stay transient), the resilience FORK (same threat -> damage or growth), and bounded
apply. Script-style, stdlib, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import arc                                    # noqa: E402
from src.engine.records import PRIMARIES                       # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


def _char(ec="typical", aff_to_kestra=0.25, regard_fenmark=0.2, load=0.3):
    return {
        "fixed": {"genotype": {"effortful_control": ec, "affiliation_attachment": "high"}},
        "baseline": {
            "temperament": {p: {"mean": 0.4, "variability": 0.1} for p in PRIMARIES},
            "model": {"regard": {"fenmark": regard_fenmark}},
        },
        "current": {
            "relationships": {"kestra": {"trust": 0.3, "affinity": aff_to_kestra, "respect": 0.2, "debt": 0.3}},
            "condition": {"allostatic_load": load},
        },
    }


def _connection(mag=0.7):
    return {"dimensions": {"care_relevant": mag, "relief": 0.3}, "durability": "durable",
            "target": "kestra", "target_group": "fenmark"}


def test_slow_burn_arc():
    """A durable CONNECTION with Kestra raises affinity to her AND erodes regard['fenmark'] toward 1.0."""
    print("\n[1] SLOW-BURN ARC (the bond teaches the class)")
    ch = _char()
    diff = arc.assess(_connection(), impact=0.6, char=ch, condition=ch["current"]["condition"])
    check("connection-writes-durable", diff is not None)
    if diff:
        check("affinity-up", diff["relationships"]["kestra"]["affinity"] > 0)
        check("regard-erodes-up", diff["regard"]["fenmark"] > 0, str(diff["regard"]))
        new = arc.apply(ch, diff)
        check("affinity-actually-rose",
              new["current"]["relationships"]["kestra"]["affinity"] > ch["current"]["relationships"]["kestra"]["affinity"])
        check("regard-actually-rose",
              new["baseline"]["model"]["regard"]["fenmark"] > ch["baseline"]["model"]["regard"]["fenmark"])

    # accumulation across many beats: affinity climbs monotonically toward 1.0
    ch2 = _char()
    affinities = [ch2["current"]["relationships"]["kestra"]["affinity"]]
    for _ in range(12):
        d = arc.assess(_connection(), impact=0.6, char=ch2, condition=ch2["current"]["condition"])
        if d:
            ch2 = arc.apply(ch2, d)
        affinities.append(ch2["current"]["relationships"]["kestra"]["affinity"])
    check("affinity-climbs-monotonically", all(b >= a for a, b in zip(affinities, affinities[1:])))
    check("affinity-rose-substantially", affinities[-1] - affinities[0] > 0.15,
          "start %.2f -> end %.2f" % (affinities[0], affinities[-1]))
    check("regard-also-eroded", ch2["baseline"]["model"]["regard"]["fenmark"] > 0.2 + 0.05)


def test_threshold_keeps_most_transient():
    """A low-impact / non-severe event writes NO durable diff — the floor doesn't move on small things."""
    print("\n[2] DURABLE THRESHOLD")
    ch = _char()
    mundane = {"dimensions": {"mastery": 0.2}, "durability": "transient"}
    check("mundane-no-diff", arc.assess(mundane, impact=0.1, char=ch, condition=ch["current"]["condition"]) is None)
    # even a durable-flagged event with near-zero impact stays under the magnitude threshold
    weak = {"dimensions": {"care_relevant": 0.6}, "durability": "durable", "target": "kestra", "target_group": "fenmark"}
    check("tiny-impact-no-diff", arc.assess(weak, impact=0.05, char=ch, condition=ch["current"]["condition"]) is None)


def test_resilience_fork():
    """Same survival-threat: low resilience -> FEAR-baseline UP (trauma); high -> SEEKING UP (growth)."""
    print("\n[3] RESILIENCE FORK (damage OR growth)")
    threat = {"dimensions": {"threat": 0.85}, "durability": "durable"}
    # low resilience: low effortful_control + high allostatic load + no secure bond
    low = {"fixed": {"genotype": {"effortful_control": "low"}},
           "baseline": {"temperament": {p: {"mean": 0.4, "variability": 0.1} for p in PRIMARIES}},
           "current": {"relationships": {}, "condition": {"allostatic_load": 0.8}}}
    # high resilience: high effortful_control + low load + a secure bond
    high = {"fixed": {"genotype": {"effortful_control": "high"}},
            "baseline": {"temperament": {p: {"mean": 0.4, "variability": 0.1} for p in PRIMARIES}},
            "current": {"relationships": {"ally": {"affinity": 0.9}}, "condition": {"allostatic_load": 0.1}}}
    d_low = arc.assess(threat, impact=0.8, char=low, condition=low["current"]["condition"])
    d_high = arc.assess(threat, impact=0.8, char=high, condition=high["current"]["condition"])
    check("low-resilience-fear-up", d_low and d_low["temperament"].get("FEAR", 0) > 0, str(d_low))
    check("low-resilience-no-growth", d_low and "SEEKING" not in d_low["temperament"])
    check("high-resilience-growth", d_high and d_high["temperament"].get("SEEKING", 0) > 0, str(d_high))
    check("resilience-derives-ordered",
          arc.derive_resilience(low, low["current"]["condition"]) < arc.derive_resilience(high, high["current"]["condition"]))


def test_apply_bounded_and_fail_loud():
    print("\n[4] BOUNDED APPLY + FAIL LOUD")
    ch = _char(regard_fenmark=0.95)
    # a big regard erosion clamps at 1.0
    new = arc.apply(ch, {"regard": {"fenmark": +0.5}})
    check("regard-clamped-at-1", new["baseline"]["model"]["regard"]["fenmark"] == 1.0)
    new2 = arc.apply(ch, {"temperament": {"FEAR": +5.0}})
    check("temperament-clamped-at-1", new2["baseline"]["temperament"]["FEAR"]["mean"] == 1.0)
    for bad in (lambda: arc.assess("notadict", 0.5, ch, {}), lambda: arc.apply("x", {}),
                lambda: arc.derive_resilience("x", {})):
        try:
            bad(); check("fail-loud", False, "accepted bad input"); return
        except ValueError:
            pass
    check("fail-loud-all", True)


def test_persist_roundtrip():
    """append_arc_diff writes a diff that reads back from the arc_diffs table."""
    print("\n[5] PERSISTENCE ROUND-TRIP")
    import json, shutil, tempfile
    from src.engine.ledger import Ledger
    tmp = tempfile.mkdtemp(prefix="swe_arc_")
    try:
        led = Ledger(os.path.join(tmp, "arc.db"))
        led.create_run("r1", {"catalog_version": 1})
        led.register_character("r1", "brakk", {"name": "Brakk"}, {"temperament": "x"})
        diff = {"relationships": {"kestra": {"affinity": 0.07}}, "regard": {"fenmark": 0.03}}
        led.append_arc_diff("r1", "brakk", 4, diff)
        row = led.con.execute("SELECT diff FROM arc_diffs WHERE run_id='r1' AND char_id='brakk' AND turn=4").fetchone()
        check("arc-diff-persisted", row is not None)
        check("arc-diff-roundtrips", row and json.loads(row["diff"])["relationships"]["kestra"]["affinity"] == 0.07)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("test_arc.py — the Arc Engine (durable baseline change)\n")
    for t in (test_slow_burn_arc, test_threshold_keeps_most_transient, test_resilience_fork,
              test_apply_bounded_and_fail_loud, test_persist_roundtrip):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
