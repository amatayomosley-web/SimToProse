"""test_levity.py — the ninth path, built by the owner's ruling (2026-09-11).

`docs/rungs/LEVITY.md` records the 2026-09-07 finding that kept this path out — its axis and its
low rungs disagreed in performance three times out of three — and the owner's ruling that put it
in regardless: *"Add levity back in, we will see if in production it fails, if so we repair."*
This suite pins what "in" means, so a repair cannot half-remove it:

  1. THE LADDER. Nine rungs compile from docs/emotion-paths.md §9's bands; the vectors climb;
     the seats' ladders list it.
  2. THE TABLES. It is in PATHS with a directedness row; it has a half-life, a rest cap, rest and
     genotype phrases, a residue rate and a wound class; both fixtures carry it.
  3. THE PUSHES. PLAY's original appraisal pushes came back under the new name: a threat lowers
     it, relief raises it (the stub route only — a live reading can only add).
  4. THE NO-OBJECT CLAIM is recorded (kinds empty) and NOT enforced (admits_role reads reflexive).

Stdlib only. Exit 0 = all pass.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import heritable as _her                       # noqa: E402
from src.engine import identity_view as _iv                    # noqa: E402
from src.engine import rungs                                   # noqa: E402
from src.engine import toward as _toward                       # noqa: E402
from src.engine import wound as _wound                         # noqa: E402
from src.engine.records import DIRECTEDNESS, PATHS, admits_role   # noqa: E402
from src.engine.rung_blocks import BANDS                       # noqa: E402
from src.engine.state import _DIM_TO_PATH, _HALF_LIFE, appraise, build_profile   # noqa: E402
import appraiser                                               # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def test_the_ladder():
    print("\n[1] THE LADDER — nine rungs, climbing vectors, listed to the seats")
    names = rungs.names_on("LEVITY")
    check("nine-rungs", names == ["amusement", "levity", "playfulness", "banter", "mischief",
                                  "immersion", "absorption", "raptness", "flow"], names)
    check("the-bands-are-section-nines", [b[:2] for b in BANDS["LEVITY"]] ==
          [(0.0, 0.1), (0.1, 0.22), (0.22, 0.36), (0.36, 0.5), (0.5, 0.62), (0.62, 0.74), (0.74, 0.85), (0.85, 0.94), (0.94, 1.01)],
          BANDS["LEVITY"])
    vs = [rungs.vector_for("LEVITY", i) for i in range(1, 10)]
    check("the-vectors-climb-from-lambda-times-the-midpoints", all(b > a for a, b in zip(vs, vs[1:]))
          and abs(vs[0] - rungs.LAMBDA["LEVITY"] * 0.05) < 1e-9 and vs[-1] <= rungs.LAMBDA["LEVITY"] + 1e-9, [round(v, 4) for v in vs])
    check("every-block-has-text", all(rungs.block_for("LEVITY", i).strip() for i in range(1, 10)))
    check("the-seats-ladders-list-it", "LEVITY" in appraiser.ladders())


def test_the_tables():
    print("\n[2] THE TABLES — everything a path must join")
    check("in-PATHS", "LEVITY" in PATHS and len(PATHS) == 9, PATHS)
    check("a-directedness-row", "LEVITY" in DIRECTEDNESS and DIRECTEDNESS["LEVITY"]["kinds"] == ())
    check("a-half-life-in-both-zones", _HALF_LIFE["LEVITY"][1] > _HALF_LIFE["LEVITY"][0] > 0, _HALF_LIFE.get("LEVITY"))
    check("a-rest-cap-at-playfulness", _her.REST_CAP["LEVITY"] == 3, _her.REST_CAP.get("LEVITY"))
    check("rest-phrases-for-raised-and-high", set(_iv._REST_PHRASES["LEVITY"]) == {"raised", "high"})
    check("a-residue-rate", "LEVITY" in _toward._RETENTION)
    # was "mastery" (hand-written); _PATH_CLASS is now DERIVED (gate heights-price-arc, 2026-09-19)
    # as the LARGEST positive push per path, and relief (.20) outweighs mastery (.15) for LEVITY —
    # see state._DIM_TO_PATH's LEVITY row, pinned two tests below in [3] THE PUSHES.
    check("a-wound-class", _wound.class_for_path("LEVITY") == "relief", _wound.class_for_path("LEVITY"))
    for fn in ("characters/maren-healer.json", "characters/ren-traveler.json"):
        ch = json.load(io.open(os.path.join(REPO, fn), encoding="utf-8"))
        check("%s-carries-it" % os.path.basename(fn),
              "LEVITY" in ch["fixed"]["genotype"] and "LEVITY" in ch["baseline"]["temperament"]
              and "LEVITY" in ch["current"]["affect"])


def test_the_pushes():
    print("\n[3] THE PUSHES — PLAY's numbers under the new name, on the stub route")
    weights = {dim: dict(rows).get("LEVITY") for dim, rows in _DIM_TO_PATH.items()}
    check("lowered-under-threat-loss-and-social-violation",
          weights["threat"] == -0.22 and weights["loss"] == -0.20 and weights["social_violation"] == -0.15, weights)
    check("raised-on-mastery-relief-and-attraction",
          weights["mastery"] == 0.15 and weights["relief"] == 0.20 and weights["attraction"] == 0.10, weights)
    ch = json.load(io.open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    _her.ensure_temperament(ch)
    prof = build_profile(ch)
    start = dict(ch["current"]["affect"])
    start["LEVITY"] = 0.40                                      # inside the frame, then the world intrudes
    down = appraise(dict(start), {"type": "threat", "dimensions": {"threat": 0.8}, "durability": "transient"}, prof)
    up = appraise(dict(start), {"type": "mundane", "dimensions": {"relief": 0.8}, "durability": "transient"}, prof)
    check("a-threat-lowers-it", down["LEVITY"] < start["LEVITY"], (start["LEVITY"], down["LEVITY"]))
    check("relief-raises-it", up["LEVITY"] > start["LEVITY"], (start["LEVITY"], up["LEVITY"]))


def test_the_no_object_claim():
    print("\n[4] NO OBJECT — recorded, not enforced")
    check("kinds-is-empty", DIRECTEDNESS["LEVITY"]["kinds"] == ())
    check("but-self-is-admitted-by-the-ruling", admits_role("LEVITY", "self"))
    check("and-an-object-is-not-refused", admits_role("LEVITY", "object"))


def main():
    print("test_levity.py — the ninth path")
    test_the_ladder()
    test_the_tables()
    test_the_pushes()
    test_the_no_object_claim()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
