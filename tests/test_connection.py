#!/usr/bin/env python3
"""test_connection.py — the investment multiplier (src/engine/connection.py).

`docs/character-model.md` "DECAY AND CONNECTION" is normative and records the author's rule: the
greater the connection, the larger the impact, and the longer it lasts. One quantity, two jobs.

What this pins:
  1. THE GAP IT CLOSES. A beloved's death and a stranger's produced the SAME magnitude, because the
     only subject-shaped term (`state._regard`) is clamped to [0,1] and "affinity lifts, never
     lowers". Nothing in the engine made closeness matter.
  2. THE RELEVANCY FLOOR — the author's third requirement. Below it, NOTHING: not a small value, a
     dead zone. Without it every acquaintance earns a sliver and the audit trail fills with noise.
  3. THE IDENTITY. A stranger, a target-less event, and an unlinked fixture all compute exactly as
     they did before, or the change is not safe to ship.
  4. INCREASE, DECREASE, and no decay of its own — because it is a READ off the live edge.

Stdlib only, script-style, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import connection as C                         # noqa: E402
from src.engine import bonds                                   # noqa: E402
from src.engine.records import PRIMARIES                       # noqa: E402
from src.engine.state import build_profile, appraise           # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _edge(v):
    return {"trust": v, "affinity": v, "respect": v, "debt": 0.0}


def _char(rels):
    return {"fixed": {"genotype": {"affiliation_attachment": "elevated"}},
            "baseline": {"temperament": {p: {"mean": 0.30, "variability": 0.1} for p in PRIMARIES},
                         "traits": {}, "model": {"schwartz": {}, "needs": {},
                                                 "moral_foundations": {}}, "skills": {}},
            "current": {"relationships": rels,
                        "condition": {"energy": 1.0, "allostatic_load": 0.0}}}


def test_the_beloved_and_the_stranger_now_differ():
    """THE GAP THE AUTHOR NAMED. Measured identical before this module existed."""
    print("\n[1] a beloved's death is not a stranger's")
    prof = build_profile(_char({"sister": _edge(0.92)}))
    aff = {p: 0.30 for p in PRIMARIES}
    L = lambda t: {"type": "loss", "dimensions": {"loss": 0.85}, "target": t}
    beloved = appraise(aff, L("sister"), prof)["PANIC_GRIEF"]
    stranger = appraise(aff, L("a_stranger"), prof)["PANIC_GRIEF"]
    check("the-beloved-lands-harder", beloved > stranger, "%.4f vs %.4f" % (beloved, stranger))
    check("and-by-a-visible-margin", beloved - stranger > 0.05, "%.4f" % (beloved - stranger))


def test_the_relevancy_floor_is_a_dead_zone():
    """The author's third requirement, and the reason it is HARD rather than a ramp: the floor buys
    SILENCE. A ramp gives every passing acquaintance a sliver of amplification, which is noise in
    the arithmetic and in the audit trail."""
    print("\n[2] low connections get NOTHING")
    for v in (0.50, 0.55, 0.60):
        check("affinity-%.2f-is-silent" % v, C.compose(_edge(v)) == 0.0, str(C.compose(_edge(v))))
        check("and-its-multiplier-is-exactly-1", C.magnitude_scale(C.compose(_edge(v))) == 1.0)
    check("above-the-floor-it-engages", C.compose(_edge(0.70)) > 0.0, str(C.compose(_edge(0.70))))
    # a DEAD ZONE, not a ramp: there is a jump at the floor, and that is deliberate
    below, above = C.compose(_edge(0.60)), C.compose(_edge(0.65))
    check("there-is-a-real-discontinuity", below == 0.0 and above >= C._FLOOR,
          "%.3f then %.3f" % (below, above))


def test_the_identity_holds():
    """Every target-less event and every stranger computes byte-identically, or this is not safe."""
    print("\n[3] the identity — nothing else moves")
    check("no-edge-is-zero", C.for_target({}, "nobody") == 0.0)
    check("no-target-is-zero", C.for_target({"a": _edge(0.95)}, None) == 0.0)
    check("neutral-composes-to-zero", C.compose(bonds._NEUTRAL) == 0.0, str(bonds._NEUTRAL))
    check("stranger-multiplier-is-exactly-1", C.magnitude_scale(0.0) == 1.0)
    check("stranger-retention-is-unchanged", C.retention_scale(0.95, 0.0) == 0.95)
    # a DISLIKED person is not amplified — dampening belongs to regard, and two factors scaling one
    # term must not restate each other
    check("dislike-is-not-amplification", C.compose(_edge(0.10)) == 0.0, str(C.compose(_edge(0.10))))


def test_it_slows_forgetting_without_making_anything_permanent():
    print("\n[4] connection slows decay, bounded")
    r = 0.95
    check("full-connection-slows-it", C.retention_scale(r, 1.0) > r)
    check("but-never-reaches-1", C.retention_scale(r, 1.0) < 1.0,
          "%.6f" % C.retention_scale(r, 1.0))
    check("even-at-a-fast-rate", C.retention_scale(0.72, 1.0) < 1.0)
    check("monotone-in-connection",
          C.retention_scale(r, 0.3) < C.retention_scale(r, 0.9))


def test_the_ceiling_keeps_the_alleles_apart():
    """The bound exists because the repo has already paid once: a brave character's fear capped
    IDENTICALLY across all four threat_reactivity alleles, and bravery became an immunity rather
    than a disposition. An unbounded multiplier against a saturating clamp reproduces that."""
    print("\n[5] the ceiling")
    check("ceiling-is-1.75", abs(C.magnitude_scale(1.0) - 1.75) < 1e-9,
          "%.4f" % C.magnitude_scale(1.0))
    aff = {p: 0.30 for p in PRIMARIES}
    L = {"type": "loss", "dimensions": {"loss": 0.70}, "target": "kin"}
    landed = []
    for allele in ("low", "typical", "elevated", "high"):
        ch = _char({"kin": _edge(0.95)})
        ch["fixed"]["genotype"]["affiliation_attachment"] = allele
        landed.append(appraise(aff, L, build_profile(ch))["PANIC_GRIEF"])
    check("all-four-alleles-stay-separated",
          all(b > a for a, b in zip(landed, landed[1:])),
          " ".join("%.4f" % v for v in landed))
    check("and-none-has-saturated", max(landed) < 1.0, "%.4f" % max(landed))


def test_debt_is_excluded():
    """The relationship tier's own reasoning: debt "is not a belief, it is a running account". An
    account is not investment — including it would mean repaying someone reduces how much their
    death hurts."""
    print("\n[6] debt is not investment")
    a = C.compose({"trust": 0.9, "affinity": 0.9, "respect": 0.9, "debt": 0.0})
    b = C.compose({"trust": 0.9, "affinity": 0.9, "respect": 0.9, "debt": 0.9})
    check("paying-a-debt-changes-nothing", a == b, "%.4f vs %.4f" % (a, b))


def test_fail_loud():
    print("\n[7] fail loud")
    try:
        C.compose({"affinity": "a lot"})
        check("raises-on-prose-axis", False, "returned instead of raising")
    except ValueError as e:
        check("raises-on-prose-axis", "not a number" in str(e), str(e)[:60])
    check("a-non-dict-edge-is-zero-not-a-crash", C.compose(None) == 0.0)


def test_connection_slows_a_real_decay():
    """The retention half, WIRED. A seam nothing calls is the declared-but-unconnected defect this
    repo keeps paying for, so the gate that adds the multiplier adds the decay it multiplies."""
    print('\n[8] it slows a decay that actually runs')
    import copy
    from src.engine import toward
    start = {"current": {"toward": {"j": {"PLAY": 0.12, "RAGE": 0.11, "DISGUST": 0.07}}}}
    far = copy.deepcopy(start); toward.erode(far, 10)                       # an acquaintance
    near = copy.deepcopy(start); toward.erode(near, 10, {"j": 0.9})         # someone close
    for prim in ("PLAY", "RAGE", "DISGUST"):
        check("%s-lasts-longer-with-a-bond" % prim,
              near["current"]["toward"]["j"][prim] > far["current"]["toward"]["j"][prim],
              "%.4f vs %.4f" % (near["current"]["toward"]["j"][prim],
                                far["current"]["toward"]["j"][prim]))
    # ESTRANGEMENT BY ARITHMETIC: warmth outruns contempt downward, with no further events
    long = copy.deepcopy(start); toward.erode(long, 60)
    v = long["current"]["toward"]["j"]
    check("contempt-outlasts-the-warmth", v["DISGUST"] > v["PLAY"],
          "PLAY %.5f vs DISGUST %.5f" % (v["PLAY"], v["DISGUST"]))
    check("and-it-rests-at-zero-not-at-itself", all(x < 0.12 for x in v.values()), str(v))


def test_temperament_returns_toward_the_authored_self():
    print('\n[9] identity is the asymptote')
    from src.engine import arc
    ch = {"baseline": {"temperament": {
        "CARE": {"mean": 0.85, "_authored_mean": 0.40, "variability": 0.1},
        "RAGE": {"mean": 0.20, "_authored_mean": 0.55, "variability": 0.1},
        "FEAR": {"mean": 0.30, "variability": 0.1}}}}          # never moved: no stamp
    arc.erode(ch, 50)
    t = ch["baseline"]["temperament"]
    check("a-raised-mean-comes-down", t["CARE"]["mean"] < 0.85, "%.4f" % t["CARE"]["mean"])
    check("but-not-below-the-authored-value", t["CARE"]["mean"] > 0.40, "%.4f" % t["CARE"]["mean"])
    check("a-LOWERED-mean-comes-back-UP", t["RAGE"]["mean"] > 0.20, "%.4f" % t["RAGE"]["mean"])
    check("and-not-above-its-authored-value", t["RAGE"]["mean"] < 0.55, "%.4f" % t["RAGE"]["mean"])
    check("an-unmoved-primary-is-left-alone", t["FEAR"]["mean"] == 0.30, str(t["FEAR"]))
    check("the-authored-value-is-never-touched",
          t["CARE"]["_authored_mean"] == 0.40 and t["RAGE"]["_authored_mean"] == 0.55)
    # slower than every other tier: identity is the least cue-specific thing the engine holds
    check("slower-than-a-wound", arc._ERODE > 0.995)


def main():
    print("test_connection.py - the investment multiplier")
    for t in sorted((v for k, v in globals().items() if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
