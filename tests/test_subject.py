#!/usr/bin/env python3
"""test_subject.py — runtime SUBJECT resolution (make target-aware appraisal + the arc fire in live
runs). Proves the gate-8 plumbing: the entity->group index from the book's people registry
(subject_groups), the resolution policy (resolve_subject: actor-named-present wins, sole-present
falls back, hallucination drops, ambiguity abstains), and — end to end — that an index->resolve->
inject->appraise chain actually scopes empathy DOWN for a subject from a group the character holds
low while leaving a non-regarded subject at full empathy. Script-style, stdlib, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.scene import subject_groups, resolve_subject       # noqa: E402
from src.engine.presence import referenced_ids                     # noqa: E402
from src.engine.state import build_profile, appraise               # noqa: E402
from src.engine.records import PATHS                            # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


_WORLD = {"people": [
    {"id": "thaddeus", "groups": ["imagers"]},
    {"id": "barnaby", "groups": ["imagers"]},
    {"id": "philomena", "groups": ["visual"]},
    {"id": "nameless"},                          # no groups -> excluded from the index
    {"id": "", "groups": ["ghost"]},             # no id -> excluded
    "not-a-dict",                                # non-dict -> skipped, never raises
]}


def test_subject_groups():
    """The index is the content/machine seam: group membership authored on person notes,
    folded into world.people, indexed entity->[group]. Malformed entries are skipped, not fatal."""
    print("\n[1] SUBJECT_GROUPS — the entity->class index")
    idx = subject_groups(_WORLD)
    check("thaddeus-is-imager", idx.get("thaddeus") == ["imagers"], str(idx.get("thaddeus")))
    check("philomena-is-visual", idx.get("philomena") == ["visual"])
    check("groupless-excluded", "nameless" not in idx)
    check("idless-excluded", "" not in idx)
    check("only-real-entities", set(idx) == {"thaddeus", "barnaby", "philomena"}, str(sorted(idx)))
    try:
        subject_groups("not-a-dict"); check("fail-loud-world", False, "accepted non-dict world")
    except ValueError:
        check("fail-loud-world", True)


def test_resolve_policy():
    """Who is the event about? Named-present wins; sole-present falls back; hallucination drops;
    multi-or-zero present abstains. Group always from the registry, never the name."""
    print("\n[2] RESOLVE_SUBJECT — the resolution policy")
    idx = subject_groups(_WORLD)
    thaddeus = {"target": "thaddeus", "affinity": 0.45}
    philomena = {"target": "philomena", "affinity": 0.65}

    # 1. actor named a present party -> that subject + its registry group
    t, g = resolve_subject([thaddeus, philomena], idx, named="thaddeus")
    check("named-present-wins", (t, g) == ("thaddeus", "imagers"), "%s/%s" % (t, g))

    # 2. no name, exactly one present -> the unambiguous subject
    t, g = resolve_subject([thaddeus], idx, named=None)
    check("sole-present-fallback", (t, g) == ("thaddeus", "imagers"), "%s/%s" % (t, g))

    # 3. named someone NOT present, but exactly one IS present -> drop the name, take the sole party
    t, g = resolve_subject([thaddeus], idx, named="ghost")
    check("hallucinated-name-drops-to-sole", (t, g) == ("thaddeus", "imagers"), "%s/%s" % (t, g))

    # 4. multiple present, no valid name -> abstain (no single subject)
    t, g = resolve_subject([thaddeus, philomena], idx, named=None)
    check("ambiguous-abstains", (t, g) == (None, None), "%s/%s" % (t, g))
    t, g = resolve_subject([thaddeus, philomena], idx, named="ghost")
    check("multi-with-bad-name-abstains", (t, g) == (None, None), "%s/%s" % (t, g))

    # 5. zero present -> abstain
    check("none-present-abstains", resolve_subject([], idx, named="thaddeus") == (None, None))

    # 6. present but not in the group index -> subject resolved, group None (unregarded)
    t, g = resolve_subject([{"target": "stranger"}], idx, named="stranger")
    check("present-no-group", (t, g) == ("stranger", None), "%s/%s" % (t, g))

    for bad in (lambda: resolve_subject("x", idx), lambda: resolve_subject([], "x")):
        try:
            bad(); check("fail-loud-resolve", False, "accepted bad input"); return
        except ValueError:
            pass
    check("fail-loud-resolve", True)


def _honora():
    """Honora, a visual observer at a star party: high innate CARE (GOODWILL hit high) + a low regard
    for the imagers whose screens spoil the dark, regard['imagers']=0.3, and a mild affinity to thaddeus (0.45)."""
    return build_profile({
        "fixed": {"name": "Honora", "genotype": {"GOODWILL": {"hit": "high"}, "WARINESS": {"hit": "elevated"}}},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PATHS},
            "traits": {"emotionality": {"mean": 0.6}},
            "model": {"regard": {"imagers": 0.3}},
        },
        "current": {
            "relationships": {"thaddeus": {"trust": 0.4, "affinity": 0.45, "respect": 0.45, "debt": 0.0}},
            "condition": {"allostatic_load": 0.1},
        },
    })


def _care_delta(prof, tag, affect):
    return appraise(affect, tag, prof)["GOODWILL"] - affect["GOODWILL"]


def test_end_to_end_scoping():
    """The whole point: index -> resolve -> inject -> appraise. The SAME care event scopes Honora's
    CARE DOWN when its subject resolves to an imager, but stays at full empathy for a visual observer
    (group not in her regard map). This is the dead mechanism (state._regard) finally getting its
    runtime inputs — care that survives a low regard as a live behaviour, not a hand-written tag."""
    print("\n[3] END-TO-END SCOPING (index -> resolve -> inject -> appraise)")
    prof = _honora()
    idx = subject_groups(_WORLD)
    affect = {p: 0.4 for p in PATHS}
    care = {"type": "care", "dimensions": {"care_relevant": 0.7}, "durability": "transient"}

    d_neutral = _care_delta(prof, care, affect)                       # no subject -> factor 1.0

    t, g = resolve_subject([{"target": "thaddeus", "affinity": 0.45}], idx, named="thaddeus")
    d_imager = _care_delta(prof, dict(care, target=t, target_group=g), affect)

    t2, g2 = resolve_subject([{"target": "philomena", "affinity": 0.5}], idx, named="philomena")
    d_visual = _care_delta(prof, dict(care, target=t2, target_group=g2), affect)

    check("care-fires-at-all", d_neutral > 0, "%.4f" % d_neutral)
    check("imager-subject-scopes-care-down", d_imager < d_neutral - 1e-9,
          "imager %.4f vs neutral %.4f" % (d_imager, d_neutral))
    check("imager-care-stays-nonzero", d_imager > 0, "%.4f (the CARE_FLOOR — scoped, never zeroed)" % d_imager)
    check("visual-subject-full-empathy", abs(d_visual - d_neutral) < 1e-9,
          "visual %.4f vs neutral %.4f" % (d_visual, d_neutral))


def test_referenced_subject():
    """AN ABSENT PERSON CAN STILL BE WHAT THE MOMENT IS ABOUT.

    `resolve_subject` derived its whole nameable set from `edges`, and `edges` holds only parties
    PRESENT — so news that a third party elsewhere had ruined you could only be ABOUT the messenger
    who brought it. Measured on a twelve-rung walk: every passage exempted the man in the room and
    the anger had nowhere to go but out the door.
    """
    print("")
    print("test_referenced_subject")
    idx = subject_groups(_WORLD)
    thaddeus_edge = {"target": "thaddeus", "trust": 0.5}

    # the defect, asserted directly: named, spoken of, not in the room -> still the subject
    check("named-referenced-wins",
          resolve_subject([], idx, named="thaddeus", referenced=["thaddeus"]) == ("thaddeus", "imagers"),
          str(resolve_subject([], idx, named="thaddeus", referenced=["thaddeus"])))

    # REFERENCED IS NAMEABLE, NEVER THE DEFAULT. A character alone with one other person still
    # means that person unless the actor says otherwise.
    check("referenced-never-sole-fallback",
          resolve_subject([], idx, named=None, referenced=["thaddeus"]) == (None, None))
    check("present-still-wins-the-fallback",
          resolve_subject([thaddeus_edge], idx, named=None, referenced=["philomena"]) == ("thaddeus", "imagers"))

    # NEGATIVE CONTROL — widening what is nameable must not disable the invention guard.
    check("hallucination-still-drops-with-nothing-present",
          resolve_subject([], idx, named="ghost", referenced=["philomena"]) == (None, None))
    check("hallucination-still-drops-to-sole-present",
          resolve_subject([thaddeus_edge], idx, named="ghost", referenced=["philomena"]) == ("thaddeus", "imagers"))

    # the default keeps every existing caller byte-identical
    check("referenced-defaults-empty",
          resolve_subject([thaddeus_edge], idx, named="thaddeus") == ("thaddeus", "imagers"))


def test_referenced_ids_reads_percepts():
    """Only `present is False` is referenced. A missing key means the caller does not track
    presence, and `.get` returning None is not False — that asymmetry is what keeps the
    single-character driver, which supplies no roster, on exactly its old behaviour."""
    print("")
    print("test_referenced_ids_reads_percepts")
    check("absent-entity-is-referenced",
          referenced_ids([{"ref": "entity.thaddeus", "present": False}]) == ["thaddeus"])
    check("present-entity-is-not",
          referenced_ids([{"ref": "entity.thaddeus", "present": True}]) == [])
    check("no-present-key-is-not",            # the legacy path — NEGATIVE CONTROL
          referenced_ids([{"ref": "entity.thaddeus"}]) == [])
    check("non-entity-refs-ignored",
          referenced_ids([{"ref": "loc.dark_field", "present": False}]) == [])
    check("deduped-and-sorted",               # hard rule 4
          referenced_ids([{"ref": "entity.thaddeus", "present": False},
                          {"ref": "entity.philomena", "present": False},
                          {"ref": "entity.thaddeus", "present": False}]) == ["philomena", "thaddeus"])


def main():
    print("test_subject.py — runtime SUBJECT resolution\n")
    for t in (test_subject_groups, test_resolve_policy, test_end_to_end_scoping,
              test_referenced_subject, test_referenced_ids_reads_percepts):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
