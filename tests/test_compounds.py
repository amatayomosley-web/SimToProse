"""test_compounds.py — the named emotions as coordinates over the primitives.

`docs/emotion-basis.md` is normative. This suite pins four things:

  1. ROUND TRIP. A composed coordinate must recognise as itself. If `compose` and `recognise`
     disagree, the vocabulary is not a coordinate system, it is a list of names.
  2. SEPARABILITY. No two expressible compounds may share a shape. A pair above the threshold means
     the basis cannot distinguish two states the vocabulary treats as different — per the doc's
     failure table that is a missing dimension or a redundant name, never nothing.
  3. BLOCKED RECIPES ARE REPORTED, NEVER DROPPED. A recipe citing a primitive the basis lacks must
     surface. The dominant defect in this repo all session was authored content that reached
     nothing; a recipe silently losing an ingredient would be that defect in a new place.
  4. NO ACTION SELECTION. decision-engine.md:85 is normative — the catalog computes state, never
     the action. Naming a state is strictly a read, and this suite is what objects if that changes.

MEASURED 2026-08-22, and this is the finding the suite exists to keep visible: 8 of 22 compounds
are blocked, and ALL EIGHT block on the same missing primitive (DISGUST) — contempt, disdain,
scorn, spite, shame, embarrassment, self_loathing, revulsion. One absent element takes out the
entire contempt-and-self-conscious family. That is the difference between an opinion about the
basis and a requirement of it.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.compounds import (                        # noqa: E402
    COMPOUNDS, CompoundError, blend, compose, recipe_sum, recognise, separability,
    validate, _ROLES,
)
from src.engine.records import PRIMARIES                  # noqa: E402

_FAILS = []
_ALL_ROLES = {"object": "someone", "self": "me", "beneficiary": "them", "self.act": "the thing"}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _flat(name, intensity=0.8):
    c = compose(name, intensity, _ALL_ROLES)
    return {p: c[p]["magnitude"] for p in c}


def test_round_trip():
    print("\n[1] ROUND TRIP — a composed coordinate recognises as itself")
    ok = validate()["ok"]
    misses = []
    for name in ok:
        top = recognise(_flat(name), top=2)
        if not top or top[0][0] != name:
            misses.append((name, top[:1]))
    check("every-expressible-compound-recognises-as-itself", not misses, misses[:3])
    # intensity is a SCALE, not a shape: the same state at two strengths must name the same
    drift = [n for n in ok if recognise(_flat(n, 0.3))[0][0] != recognise(_flat(n, 1.0))[0][0]]
    check("intensity-does-not-change-the-name", not drift, drift[:3])
    check("recognise-returns-ranked-not-single",
          all(isinstance(t, tuple) and len(t) == 2 for t in recognise(_flat(ok[0]), top=3)))


def test_separability():
    print("\n[2] SEPARABILITY — no two expressible compounds share a shape")
    # 0.99 is the HARD line: same role signature AND the same shape means one state with two
    # names. 0.95-0.99 are SHADES (contempt/disdain/scorn occupy one region on purpose) and are
    # reported, not failed -- the source vocabulary this borrows from carries exact aliases too.
    hard = separability(0.99)
    check("no-pair-above-0.99", not hard, ["%s~%s %.3f" % p for p in hard[:3]])
    shades = [x for x in separability(0.95) if x not in hard]
    print("       shades (0.95-0.99, reported not failed): %s"
          % (["%s~%s %.3f" % x for x in shades] or "none"))
    near = separability(0.90)
    print("       (nearest pairs at 0.90: %s)"
          % (["%s~%s %.3f" % p for p in near[:3]] or "none"))


def test_blocked_are_reported():
    print("\n[3] BLOCKED RECIPES — reported loudly, never silently truncated")
    v = validate()
    check("validate-partitions-the-table",
          len(v["ok"]) + len(v["blocked"]) == len(COMPOUNDS),
          "%d + %d != %d" % (len(v["ok"]), len(v["blocked"]), len(COMPOUNDS)))
    check("no-malformed-roles", not v["bad_role"], v["bad_role"])
    for name in v["blocked"]:
        try:
            compose(name, 0.5, _ALL_ROLES)
            check("compose-refuses-%s" % name, False, "did NOT raise")
            break
        except CompoundError:
            pass
    else:
        check("compose-refuses-every-blocked-compound", True)
    check("blocked-never-match-in-recognise",
          all(n not in dict(recognise(_flat(v["ok"][0]), top=len(COMPOUNDS))) for n in v["blocked"]))
    # THE FINDING: the blocked set must be a coherent family on ONE missing primitive, or the
    # argument for adding it is weaker than it looks.
    missing = sorted({m for ms in v["blocked"].values() for m in ms})
    if v["blocked"]:
        print("       %d blocked, all on %s -> %s"
              % (len(v["blocked"]), missing, sorted(v["blocked"])))
        check("blocked-set-is-one-missing-primitive", len(missing) == 1, missing)


def test_fail_loud():
    print("\n[4] FAIL LOUD")
    for name, fn in (("unknown-name",      lambda: compose("smugness", 0.5)),
                     ("intensity-range",   lambda: compose("grief", 1.5)),
                     ("intensity-type",    lambda: compose("grief", "a lot")),
                     ("vector-not-a-dict", lambda: recognise(["FEAR", 0.5]))):
        try:
            fn()
            check(name, False, "did NOT raise")
        except CompoundError:
            check(name, True)


def test_contract():
    print("\n[5] CONTRACT — shape, roles, and the hard line")
    c = compose("jealousy", 0.8, _ALL_ROLES)
    check("every-primitive-carries-magnitude-target-role",
          all(set(v) == {"magnitude", "target", "role"} for v in c.values()))
    check("targets-are-per-primitive-not-per-compound",
          len({v["target"] for v in c.values()}) > 1,
          "jealousy must point at more than one object: %s" % {k: v["target"] for k, v in c.items()})
    check("all-roles-are-known", all(v["role"] in _ROLES for v in c.values()))
    check("magnitudes-clamped", all(0.0 <= v["magnitude"] <= 1.0 for v in c.values()))
    check("every-recipe-primitive-is-uppercase-primary-shaped",
          all(p.isupper() for r in COMPOUNDS.values() for p in r))
    # the hard line: this module reads state, it never picks an action
    raw = open(os.path.join(REPO, "src/engine/compounds.py"), encoding="utf-8").read().splitlines()
    Q3, S3 = chr(34) * 3, chr(39) * 3
    code, in_doc = [], False
    for ln in raw:
        st = ln.strip()
        if st.startswith(Q3) or st.startswith(S3):
            in_doc = not in_doc
            continue
        if in_doc or st.startswith("#"):
            continue
        code.append(ln.split("#", 1)[0])
    src = chr(10).join(code)
    banned = [w for w in ("argmax", "def choose", "def decide", "def act") if w in src]
    check("no-action-selection", not banned, banned)


def test_blend():
    print("\n[6] BLEND — a compound ON a person is always a WHOLE vector")
    warm = {"CARE": 0.70, "PLAY": 0.55, "SEEKING": 0.50, "FEAR": 0.25,
            "RAGE": 0.20, "LUST": 0.25, "PANIC_GRIEF": 0.30}
    cold = {"CARE": 0.20, "PLAY": 0.15, "SEEKING": 0.45, "FEAR": 0.45,
            "RAGE": 0.45, "LUST": 0.15, "PANIC_GRIEF": 0.40}
    v = blend("indignation", warm)
    check("covers-every-primitive", set(v) == set(PRIMARIES), sorted(set(PRIMARIES) - set(v)))
    check("all-clamped", all(0.0 <= x <= 1.0 for x in v.values()))
    # THE POINT: one vocabulary, any cast. The same name is a different state on a different person.
    check("same-recipe-differs-by-person", blend("indignation", warm) != blend("indignation", cold))
    check("the-difference-is-the-baseline-showing-through",
          blend("indignation", warm)["PLAY"] > blend("indignation", cold)["PLAY"])
    # intensity and identity-preservation are ONE dial, not two parameters
    faint, total = blend("indignation", warm, 0.25), blend("indignation", warm, 1.0)
    check("lower-intensity-leaves-more-of-the-person",
          faint["PLAY"] > total["PLAY"] and faint["CARE"] > total["CARE"],
          "faint PLAY %.3f vs total %.3f" % (faint["PLAY"], total["PLAY"]))
    check("recipe_sum-scales-with-intensity",
          abs(recipe_sum("indignation", 0.5) - recipe_sum("indignation") * 0.5) < 1e-9)
    # a fully-steered state erases the person — the source formula's own behaviour
    hi = {n: recipe_sum(n) for n in validate()["ok"]}
    top = max(hi, key=hi.get)
    if hi[top] >= 1.0:
        b = blend(top, warm)
        check("sum-at-or-above-one-gives-zero-bleed",
              all(abs(b[p] - (compose(top, 1.0).get(p, {}).get("magnitude", 0.0))) < 1e-9
                  for p in PRIMARIES), top)
    else:
        print("       (no expressible recipe sums >= 1.0; highest is %s at %.2f)" % (top, hi[top]))
    for name, fn in (("baseline-not-a-dict", lambda: blend("grief", [0.3])),
                     ("unknown-name-blend",  lambda: blend("nope", warm))):
        try:
            fn(); check(name, False, "did NOT raise")
        except CompoundError:
            check(name, True)


def main():
    print("test_compounds.py — named emotions as coordinates over the primitives")
    for t in (test_round_trip, test_separability, test_blocked_are_reported,
              test_fail_loud, test_contract, test_blend):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
