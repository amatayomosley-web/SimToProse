"""test_disgust.py — the eighth primitive, and what it unlocked.

`docs/emotion-basis.md` settled DISGUST as normative on 2026-08-22: irreducible by the project
owner's own criterion — not derivable from any combination of the other seven — and Plutchik's
eighth. The basis carried seven anyway, and the cost was recorded in three places:

  * `state.py` held a written-out DISGUST push it deliberately would NOT wire, with a comment
    saying why: "appraise does `out[primary] + delta` and would KeyError. Adding a silent skip
    would make an unknown primitive vanish quietly, which is the defect class this repo keeps
    finding."
  * `compounds.py` BLOCKED every recipe naming it — seventeen of forty-two, the whole
    contempt/shame/revulsion family — rather than truncate a recipe silently.
  * `goal-alignment-review.md` put it plainly: "**cold contempt is unrepresentable as state**",
    because `social_violation` pushed RAGE alone and all four RAGE directions are hot confrontation.

What this suite pins:
  1. The basis is eight, and the ORDER did not change (compounds._vector indexes by position).
  2. EVERY primitive is REACHABLE — some appraisal dimension can actually move it. LUST failed
    this until `attraction` was added the same day; a basis element with phrases and no input
    looks authored and does nothing, which `emotion-basis.md` calls BLOCKING.
  3. Cold contempt now stages. RAGE and DISGUST separate: one closes distance, the other opens it.
  4. The seventeen are live — sixteen of them, because unblocking exposed one genuine duplicate.
  5. The seven incumbents were not disturbed.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.consolidation import CATALOG                                  # noqa: E402
from src.engine.rung_blocks import BLOCKS                                      # noqa: E402
from src.engine.records import PATHS                                      # noqa: E402
from src.engine.state import _HALF_LIFE, _DIM_TO_PATH, appraise, build_profile, decay  # noqa: E402
_TEST_BEAT_MINUTES = 30.0  # a TEST beat, minutes: the engine has no beat duration. 30 = the pre-clock WARINESS per-beat retention (0.72) against the 60-min episode half-life, so the fast-path tests keep their meaning


_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _maren():
    ch = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    return ch, build_profile(ch), ch["baseline"]["temperament"]


def test_the_basis_is_eight():
    print("\n[1] THE BASIS — eight, and the order is unchanged")
    check("nine-paths", len(PATHS) == 9, PATHS)      # eight until LEVITY joined (2026-09-11)
    check("disgust-is-in-it", "DISTASTE" in PATHS)
    # TWO POSITION CHECKS RETIRED 2026-09-08 ("disgust-is-LAST", "the-seven-kept-their-order").
    # Both existed because compounds._vector indexed the basis BY POSITION, so an insertion in
    # the middle silently re-indexed every stored comparison. compounds.py is retired to staging
    # with the primitive set, nothing indexes PATHS positionally now, and DISTASTE is no longer
    # last in any case -- RECEPTIVITY and SELF-REGARD follow it.
    check("it-has-a-half-life", "DISTASTE" in _HALF_LIFE, sorted(_HALF_LIFE))
    check("revulsion-outlasts-its-cause", _HALF_LIFE["DISTASTE"][0] > _HALF_LIFE["DISPLEASURE"][0],
          "%.2f vs RAGE %.2f — you do not want the food again once it made you ill"
          % (_HALF_LIFE["DISTASTE"][0], _HALF_LIFE["DISPLEASURE"][0]))
    # was: four band phrases. The band table is retired; DISGUST now walks a ladder.
    # WAS `PATH_SOURCE.get("DISTASTE") == "DISTASTE"`. PATH_SOURCE was the lookup translating a
    # path from a primitive; it is gone because a path no longer needs translating from anything.
    check("it-has-a-path", len(BLOCKS["DISTASTE"]) == 5, len(BLOCKS["DISTASTE"]))


def test_it_is_reachable():
    print("\n[2] REACHABLE — an appraisal dimension actually moves it")
    pushes = {d: [p for p, _w in rows] for d, rows in _DIM_TO_PATH.items()}
    reaching = sorted(d for d, ps in pushes.items() if "DISTASTE" in ps)
    print("       dimensions that push DISGUST: %s" % reaching)
    check("some-dimension-pushes-it", bool(reaching))
    check("social_violation-does", "social_violation" in reaching,
          "contempt is the social-violation response that is not anger")
    ch, prof, temp = _maren()
    a = dict(ch["current"]["affect"])
    start = a["DISTASTE"]
    for _ in range(3):
        a = decay(appraise(a, {"dimensions": {"social_violation": 0.85},
                               "durability": "durable"}, prof), temp, prof, elapsed=_TEST_BEAT_MINUTES)
    print("       DISGUST %.3f -> %.3f over three violations" % (start, a["DISTASTE"]))
    check("a-violation-moves-it", a["DISTASTE"] > start + 0.2, a["DISTASTE"])
    # EVERY primitive must be reachable, not just this one. LUST used to fail here — a mean, a
    # decay rate, four direction phrases, and nothing that could move it — and `emotion-basis.md`
    # calls that BLOCKING. `attraction` was added as a seventh dimension on the same day.
    # TWO PATHS ARE KNOWN-DARK, and this guard names them rather than hiding them. Nothing in
    # the event vocabulary means "something good reached you" (RECEPTIVITY) or "your standing
    # moved" (SELF-REGARD), so 22 authored and behaviourally verified rungs cannot be reached.
    # Authoring those dimensions is the owner's emotional model, not something to invent here
    # -- inventing it is the LEVITY failure of 2026-09-08. The guard still has teeth for the
    # SIX that do have inputs: if any of them loses its dimension, this fails.
    _KNOWN_DARK = ("RECEPTIVITY", "SELF-REGARD")
    unreachable = sorted(p for p in PATHS
                         if p not in _KNOWN_DARK
                         and not any(p in ps for ps in pushes.values()))
    print("       paths no dimension can reach: %s   (known-dark: %s)"
          % (unreachable or "NONE", ", ".join(_KNOWN_DARK)))
    check("every-fed-path-is-reachable", not unreachable,
          "a basis element with phrases and no input is worse than no element: it looks authored "
          "and does nothing")
    ch2, prof2, temp2 = _maren()
    b = dict(ch2["current"]["affect"])
    lust0 = b["STIRRING"]
    for _ in range(3):
        # a continuous build of attraction within one scene: elapsed 0 between beats (owner's rule
        # that a beat carries no authored duration unless declared), so per-rung decay does not eat
        # the climb — the check is that the `attraction` dimension FEEDS STIRRING.
        b = decay(appraise(b, {"dimensions": {"attraction": 0.7},
                               "durability": "transient"}, prof2), temp2, prof2, elapsed=0.0)
    print("       STIRRING %.3f -> %.3f over three attraction beats" % (lust0, b["STIRRING"]))
    check("attraction-moves-STIRRING", b["STIRRING"] > lust0 + 0.1, b["STIRRING"])
    check("attraction-is-not-admitted-on-threat-events",
          "attraction" not in (CATALOG["threat"].get("appraisal_map") or []),
          "coercion must be AUTHORED as the violation it is, never reached through a dimension "
          "the engine hands out on threat events")
    check("nor-on-harm-seize-or-threaten",
          not any("attraction" in (CATALOG[t].get("appraisal_map") or [])
                  for t in ("harm", "seize", "threaten")))


def test_cold_contempt_stages():
    print("\n[3] COLD CONTEMPT — recorded as 'unrepresentable as state' before this")
    ch, prof, temp = _maren()
    a = dict(ch["current"]["affect"])
    for _ in range(3):
        a = decay(appraise(a, {"dimensions": {"social_violation": 0.85},
                               "durability": "durable"}, prof), temp, prof, elapsed=_TEST_BEAT_MINUTES)
    # THE RENDERER CHANGED, THE CLAIM DID NOT. `direct_affect` and its band tables were retired on
    # 2026-09-08; DISGUST now reaches the actor as a DISTASTE rung block, selected by the composer.
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(REPO, "scripts"))
    import composer as _c
    rows = _c.selectable(a)
    staged = _c.direction_for(rows, _c.select_deterministic(rows)) if rows else ""
    print("       %s" % staged[-120:].replace(chr(10), " "))
    check("disgust-reaches-the-actor",
          any(r["path"] == "DISTASTE" for r in rows)
          and BLOCKS["DISTASTE"][next(r["rung"] for r in rows if r["path"] == "DISTASTE")] in staged,
          staged[-160:])
    # RAGE and DISGUST must not read as the same instruction: one closes distance, one opens it.
    # Compared at the TOP of each ladder, which is where the two are furthest apart.
    hot = BLOCKS["DISPLEASURE"][len(BLOCKS["DISPLEASURE"])]
    cold = BLOCKS["DISTASTE"][len(BLOCKS["DISTASTE"])]
    check("they-are-different-acts", hot != cold)
    check("no-digits-in-either", not any(c.isdigit() for c in hot + cold))


# SECTION [4] RETIRED 2026-09-08 ("the seventeen are live"). It measured the 41 compound
# recipes -- liveness, family coverage, and pairwise separability under a shade ceiling --
# and every recipe is a weighted vector over the OLD eight primitives, so not one of its keys
# names anything the engine stores now. compounds.py is at staging/src/engine/compounds.py
# with its recipes intact; docs/emotion-dynamics.md keeps its future open as a way to name
# CO-OCCURRENCE ACROSS PATHS. This section returns when that is built, against positions
# rather than the angle of a vector.

def test_the_incumbents_are_undisturbed():
    print("\n[5] THE SEVEN — unchanged, which is what makes this an ADDITION")
    check("rage-still-owns-social_violation",
          _DIM_TO_PATH["social_violation"][0][0] == "DISPLEASURE",
          "most violations make people angry FIRST; contempt is what is left when rage stops "
          "asking for redress")
    check("rage-outweighs-disgust-there",
          dict((p, w) for p, w in _DIM_TO_PATH["social_violation"])["DISPLEASURE"]
          > dict((p, w) for p, w in _DIM_TO_PATH["social_violation"])["DISTASTE"])
    for p in ("WARINESS", "DEFLATION", "DISPLEASURE", "GOODWILL", "STIRRING", "STIRRING", "STIRRING"):
        check("%s-kept-its-decay-rate" % p, p in _HALF_LIFE)
    ch, prof, temp = _maren()
    check("every-primitive-has-a-gain", set(prof["gains"]) == set(PATHS),
          set(prof["gains"]) ^ set(PATHS))
    check("every-primitive-has-a-hold", set(prof["hold"]) == set(PATHS))
    check("the-fixture-carries-nine", len(ch["current"]["affect"]) == 9)


def main():
    print("test_disgust.py — the eighth primitive, and what it unlocked")
    for t in (test_the_basis_is_eight, test_it_is_reachable, test_cold_contempt_stages,
              test_the_incumbents_are_undisturbed):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
