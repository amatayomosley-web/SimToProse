#!/usr/bin/env python3
"""test_subject.py — runtime SUBJECT resolution (make target-aware appraisal + the arc fire in live
runs). Proves the gate-8 plumbing: the entity->group index from the book's people registry
(subject_groups), the resolution policy (resolve_subject: actor-named-present wins, sole-present
falls back, hallucination drops, ambiguity abstains), and — end to end — that an index->resolve->
inject->appraise chain actually scopes a bigot's empathy DOWN for a disregarded-class subject while
leaving a non-regarded subject at full empathy. Script-style, stdlib, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.scene import subject_groups, resolve_subject       # noqa: E402
from src.engine.state import build_profile, appraise               # noqa: E402
from src.engine.records import PRIMARIES                            # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


_WORLD = {"people": [
    {"id": "kestra", "groups": ["fenmark"]},
    {"id": "fenmark_maid", "groups": ["fenmark"]},
    {"id": "wynn", "groups": ["human"]},
    {"id": "nameless"},                          # no groups -> excluded from the index
    {"id": "", "groups": ["ghost"]},             # no id -> excluded
    "not-a-dict",                                # non-dict -> skipped, never raises
]}


def test_subject_groups():
    """The index is the content/machine seam: group membership authored on person notes,
    folded into world.people, indexed entity->[group]. Malformed entries are skipped, not fatal."""
    print("\n[1] SUBJECT_GROUPS — the entity->class index")
    idx = subject_groups(_WORLD)
    check("kestra-is-fenmark", idx.get("kestra") == ["fenmark"], str(idx.get("kestra")))
    check("wynn-is-human", idx.get("wynn") == ["human"])
    check("groupless-excluded", "nameless" not in idx)
    check("idless-excluded", "" not in idx)
    check("only-real-entities", set(idx) == {"kestra", "fenmark_maid", "wynn"}, str(sorted(idx)))
    try:
        subject_groups("not-a-dict"); check("fail-loud-world", False, "accepted non-dict world")
    except ValueError:
        check("fail-loud-world", True)


def test_resolve_policy():
    """Who is the event about? Named-present wins; sole-present falls back; hallucination drops;
    multi-or-zero present abstains. Group always from the registry, never the name."""
    print("\n[2] RESOLVE_SUBJECT — the resolution policy")
    idx = subject_groups(_WORLD)
    kestra = {"target": "kestra", "affinity": 0.25}
    wynn = {"target": "wynn", "affinity": 0.80}

    # 1. actor named a present party -> that subject + its registry group
    t, g = resolve_subject([kestra, wynn], idx, named="kestra")
    check("named-present-wins", (t, g) == ("kestra", "fenmark"), "%s/%s" % (t, g))

    # 2. no name, exactly one present -> the unambiguous subject
    t, g = resolve_subject([kestra], idx, named=None)
    check("sole-present-fallback", (t, g) == ("kestra", "fenmark"), "%s/%s" % (t, g))

    # 3. named someone NOT present, but exactly one IS present -> drop the name, take the sole party
    t, g = resolve_subject([kestra], idx, named="ghost")
    check("hallucinated-name-drops-to-sole", (t, g) == ("kestra", "fenmark"), "%s/%s" % (t, g))

    # 4. multiple present, no valid name -> abstain (no single subject)
    t, g = resolve_subject([kestra, wynn], idx, named=None)
    check("ambiguous-abstains", (t, g) == (None, None), "%s/%s" % (t, g))
    t, g = resolve_subject([kestra, wynn], idx, named="ghost")
    check("multi-with-bad-name-abstains", (t, g) == (None, None), "%s/%s" % (t, g))

    # 5. zero present -> abstain
    check("none-present-abstains", resolve_subject([], idx, named="kestra") == (None, None))

    # 6. present but not in the group index -> subject resolved, group None (unregarded)
    t, g = resolve_subject([{"target": "stranger"}], idx, named="stranger")
    check("present-no-group", (t, g) == ("stranger", None), "%s/%s" % (t, g))

    for bad in (lambda: resolve_subject("x", idx), lambda: resolve_subject([], "x")):
        try:
            bad(); check("fail-loud-resolve", False, "accepted bad input"); return
        except ValueError:
            pass
    check("fail-loud-resolve", True)


def _bigot():
    """A Brakk-shaped profile: high innate CARE (affiliation_attachment high) + the bigotry
    regard['fenmark']=0.2, with a faint affinity to kestra (0.25)."""
    return build_profile({
        "fixed": {"name": "Brakk", "genotype": {"affiliation_attachment": "high"}},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES},
            "traits": {"emotionality": {"mean": 0.6}},
            "model": {"regard": {"fenmark": 0.2}},
        },
        "current": {
            "relationships": {"kestra": {"trust": 0.2, "affinity": 0.25, "respect": 0.15, "debt": 0.3}},
            "condition": {"allostatic_load": 0.3},
        },
    })


def _care_delta(prof, tag, affect):
    return appraise(affect, tag, prof)["CARE"] - affect["CARE"]


def test_end_to_end_scoping():
    """The whole point: index -> resolve -> inject -> appraise. The SAME care event scopes the
    bigot's CARE DOWN when its subject resolves to a Fenmark, but stays at full empathy for a human
    (group not in his regard map). This is the dead mechanism (state._regard) finally getting its
    runtime inputs — the 'bigot who feels bad' as a live behaviour, not a hand-written test tag."""
    print("\n[3] END-TO-END SCOPING (index -> resolve -> inject -> appraise)")
    prof = _bigot()
    idx = subject_groups(_WORLD)
    affect = {p: 0.4 for p in PRIMARIES}
    care = {"type": "care", "dimensions": {"care_relevant": 0.7}, "durability": "transient"}

    d_neutral = _care_delta(prof, care, affect)                       # no subject -> factor 1.0

    t, g = resolve_subject([{"target": "kestra", "affinity": 0.25}], idx, named="kestra")
    d_fenmark = _care_delta(prof, dict(care, target=t, target_group=g), affect)

    t2, g2 = resolve_subject([{"target": "wynn", "affinity": 0.5}], idx, named="wynn")
    d_human = _care_delta(prof, dict(care, target=t2, target_group=g2), affect)

    check("care-fires-at-all", d_neutral > 0, "%.4f" % d_neutral)
    check("fenmark-subject-scopes-care-down", d_fenmark < d_neutral - 1e-9,
          "fenmark %.4f vs neutral %.4f" % (d_fenmark, d_neutral))
    check("fenmark-care-stays-nonzero", d_fenmark > 0, "%.4f (the CARE_FLOOR — he still feels it)" % d_fenmark)
    check("human-subject-full-empathy", abs(d_human - d_neutral) < 1e-9,
          "human %.4f vs neutral %.4f" % (d_human, d_neutral))


def main():
    print("test_subject.py — runtime SUBJECT resolution\n")
    for t in (test_subject_groups, test_resolve_policy, test_end_to_end_scoping):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
