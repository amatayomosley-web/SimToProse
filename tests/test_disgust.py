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

from src.engine.compounds import COMPOUNDS, separability                      # noqa: E402
from src.engine.consolidation import CATALOG                                  # noqa: E402
from src.engine.direction import _PHRASES, direct_affect                      # noqa: E402
from src.engine.records import PRIMARIES                                      # noqa: E402
from src.engine.state import _DECAY_RATE, _DIM_TO_PRIMARY, appraise, build_profile, decay  # noqa: E402

_FAILS = []
_SHADE_CEILING = 0.99      # tests/test_compounds.py: 0.95-0.99 are SHADES, on purpose


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _maren():
    ch = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    return ch, build_profile(ch), ch["baseline"]["temperament"]


def test_the_basis_is_eight():
    print("\n[1] THE BASIS — eight, and the order is unchanged")
    check("eight-primitives", len(PRIMARIES) == 8, PRIMARIES)
    check("disgust-is-in-it", "DISGUST" in PRIMARIES)
    check("disgust-is-LAST", PRIMARIES[-1] == "DISGUST",
          "compounds._vector indexes by POSITION — an insertion in the middle silently re-indexes "
          "every stored comparison")
    check("the-seven-kept-their-order",
          list(PRIMARIES[:7]) == ["SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY"],
          list(PRIMARIES[:7]))
    check("it-has-a-decay-rate", "DISGUST" in _DECAY_RATE, sorted(_DECAY_RATE))
    check("revulsion-outlasts-its-cause", _DECAY_RATE["DISGUST"] > _DECAY_RATE["RAGE"],
          "%.2f vs RAGE %.2f — you do not want the food again once it made you ill"
          % (_DECAY_RATE["DISGUST"], _DECAY_RATE["RAGE"]))
    check("it-has-four-directions", len(_PHRASES.get("DISGUST", ())) == 4)


def test_it_is_reachable():
    print("\n[2] REACHABLE — an appraisal dimension actually moves it")
    pushes = {d: [p for p, _w in rows] for d, rows in _DIM_TO_PRIMARY.items()}
    reaching = sorted(d for d, ps in pushes.items() if "DISGUST" in ps)
    print("       dimensions that push DISGUST: %s" % reaching)
    check("some-dimension-pushes-it", bool(reaching))
    check("social_violation-does", "social_violation" in reaching,
          "contempt is the social-violation response that is not anger")
    ch, prof, temp = _maren()
    a = dict(ch["current"]["affect"])
    start = a["DISGUST"]
    for _ in range(3):
        a = decay(appraise(a, {"dimensions": {"social_violation": 0.85},
                               "durability": "durable"}, prof), temp, prof)
    print("       DISGUST %.3f -> %.3f over three violations" % (start, a["DISGUST"]))
    check("a-violation-moves-it", a["DISGUST"] > start + 0.2, a["DISGUST"])
    # EVERY primitive must be reachable, not just this one. LUST used to fail here — a mean, a
    # decay rate, four direction phrases, and nothing that could move it — and `emotion-basis.md`
    # calls that BLOCKING. `attraction` was added as a seventh dimension on the same day.
    unreachable = sorted(p for p in PRIMARIES
                         if not any(p in ps for ps in pushes.values()))
    print("       primitives no dimension can reach: %s" % (unreachable or "NONE"))
    check("every-primitive-is-reachable", not unreachable,
          "a basis element with phrases and no input is worse than no element: it looks authored "
          "and does nothing")
    ch2, prof2, temp2 = _maren()
    b = dict(ch2["current"]["affect"])
    lust0 = b["LUST"]
    for _ in range(3):
        b = decay(appraise(b, {"dimensions": {"attraction": 0.7},
                               "durability": "transient"}, prof2), temp2, prof2)
    print("       LUST %.3f -> %.3f over three attraction beats" % (lust0, b["LUST"]))
    check("attraction-moves-LUST", b["LUST"] > lust0 + 0.1, b["LUST"])
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
                               "durability": "durable"}, prof), temp, prof)
    staged = direct_affect(a, temp)
    print("       %s" % staged[-120:])
    check("disgust-reaches-the-actor", any(p in staged for p in _PHRASES["DISGUST"]), staged[-160:])
    # RAGE and DISGUST must not read as the same instruction: one closes distance, one opens it
    hot = _PHRASES["RAGE"][3]
    cold = _PHRASES["DISGUST"][3]
    print("       RAGE   gripping: %s" % hot)
    print("       DISGUST gripping: %s" % cold)
    check("they-are-different-acts", hot != cold and "distance" not in hot)
    check("no-digits-in-either", not any(c.isdigit() for c in hot + cold))


def test_the_seventeen_are_live():
    print("\n[4] THE SEVENTEEN — and no duplicate came in with them")
    live = [n for n, r in COMPOUNDS.items() if all(p in PRIMARIES for p in r)]
    citing = [n for n, r in COMPOUNDS.items() if "DISGUST" in r]
    print("       compounds live: %d of %d   (%d of them name DISGUST)"
          % (len(live), len(COMPOUNDS), len(citing)))
    check("nothing-is-blocked-any-more", len(live) == len(COMPOUNDS),
          sorted(set(COMPOUNDS) - set(live)))
    # 16 live, not the 17 that were blocked: `sarcastic` was removed as a duplicate of
    # `mocking` (0.996) the moment both went live for the first time.
    check("the-family-is-there",
          {"contempt", "disdain", "scorn", "shame", "embarrassment", "self_loathing",
           "revulsion", "bitter", "cold", "spite"} <= set(live),
          sorted({"contempt", "disdain", "scorn", "shame", "embarrassment",
                  "self_loathing", "revulsion", "bitter", "cold", "spite"} - set(live)))
    check("seventeen-were-blocked-sixteen-are-live", len(citing) == 16, len(citing))
    pairs = sorted(separability(), key=lambda t: -t[2])[:3]
    for a, b, s in pairs:
        print("       closest: %-22s %.3f" % ("%s~%s" % (a, b), s))
    check("no-duplicate-above-the-shade-ceiling", pairs[0][2] < _SHADE_CEILING,
          "%s~%s at %.3f" % pairs[0])
    check("shades-are-still-allowed", pairs[0][2] > 0.90,
          "decision-engine.md wants contempt/disdain/scorn as neighbouring COORDINATES; a "
          "vocabulary with no near-neighbours has lost the nuance the basis exists for")
    check("sarcastic-is-gone", "sarcastic" not in COMPOUNDS,
          "it scored 0.996 to `mocking` — a delivery register, not a feeling")


def test_the_incumbents_are_undisturbed():
    print("\n[5] THE SEVEN — unchanged, which is what makes this an ADDITION")
    check("rage-still-owns-social_violation",
          _DIM_TO_PRIMARY["social_violation"][0][0] == "RAGE",
          "most violations make people angry FIRST; contempt is what is left when rage stops "
          "asking for redress")
    check("rage-outweighs-disgust-there",
          dict((p, w) for p, w in _DIM_TO_PRIMARY["social_violation"])["RAGE"]
          > dict((p, w) for p, w in _DIM_TO_PRIMARY["social_violation"])["DISGUST"])
    for p in ("FEAR", "PANIC_GRIEF", "RAGE", "CARE", "SEEKING", "LUST", "PLAY"):
        check("%s-kept-its-decay-rate" % p, p in _DECAY_RATE)
    ch, prof, temp = _maren()
    check("every-primitive-has-a-gain", set(prof["gains"]) == set(PRIMARIES),
          set(prof["gains"]) ^ set(PRIMARIES))
    check("every-primitive-has-a-decay-rate", set(prof["decay_rates"]) == set(PRIMARIES))
    check("the-fixture-carries-eight", len(ch["current"]["affect"]) == 8)


def main():
    print("test_disgust.py — the eighth primitive, and what it unlocked")
    for t in (test_the_basis_is_eight, test_it_is_reachable, test_cold_contempt_stages,
              test_the_seventeen_are_live, test_the_incumbents_are_undisturbed):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
