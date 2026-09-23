"""test_receive.py — Phase 3: the receipt from READINGS, and what follows from a reading.

docs/emotion-arithmetic.md section 5 step 3 (and 7), wired 2026-09-11 with the seats as the
emotional input. Five claims:

  1. THE RECEIPT IS THE VECTOR TIMES THE MULTIPLIERS. A reading at rung k on a path adds exactly
     vector_for(path, k) · g · connection(about) · q — and nothing on any other path.
  2. IMPACT IS THE BEAT'S TOTAL ADDITION. arc.assess reads it.
  3. ABOUTNESS FROM READINGS. An about binds; an empty about leaves the bind; a path back at rest
     clears it; a reflexive about binds only where the basis admits self.
  4. THE DURABLE CANDIDATE. A reading at or above the durable height makes arc's candidate with
     no dimension at all.
  5. A WOUND READS THE READING. When a reading fires a wound's path, the trial's observation is
     the reading's height, not an event dimension.

Stdlib only. Exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import arc as _arc                            # noqa: E402
from src.engine import connection as K                        # noqa: E402
from src.engine import heritable as H                         # noqa: E402
from src.engine import readings as R                          # noqa: E402
from src.engine import rungs                                  # noqa: E402
from src.engine import state as S                             # noqa: E402
from src.engine import targets as T                           # noqa: E402
from src.engine import wound as W                             # noqa: E402
from src.engine.records import PATHS, admits_role             # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _char(hit="typical"):
    ch = {"fixed": {"genotype": H.typical(WARINESS={"hit": hit})},
          "baseline": {"temperament": H.resting(), "wounds": [W.make("sickness", "WARINESS", 0.85, "profile:t")]},
          "current": {}}
    S.build_profile(ch)
    return ch


def _parse(rows):
    rs, _l, _c = R.parse({"readings": rows, "confidence": "sure"}, percepts=None, present=None, me="maren")
    return rs


def test_the_receipt_is_the_vector_times_the_multipliers():
    print("\n[1] THE RECEIPT IS THE VECTOR TIMES THE MULTIPLIERS")
    ch = _char(hit="high")
    prof = S.build_profile(ch)
    rest = {p: ch["baseline"]["temperament"][p]["mean"] for p in PATHS}
    names = rungs.names_on("WARINESS")
    k = 5
    rs = _parse([{"path": "WARINESS", "rung": names[k - 1], "about": ""}])
    out, impact = S.receive(rest, rs, prof)
    want = rungs.vector_for("WARINESS", k) * H.GAIN["high"]
    check("unbound-reading-adds-vector-times-gain", abs((out["WARINESS"] - rest["WARINESS"]) - want) < 1e-12, (out["WARINESS"] - rest["WARINESS"], want))
    check("no-other-path-moves", all(out[p] == rest[p] for p in PATHS if p != "WARINESS"))
    check("impact-is-the-addition", abs(impact - want) < 1e-12, impact)
    # about a held concept: times connection; repeated and present: times q
    rs2 = _parse([{"path": "WARINESS", "rung": names[k - 1], "about": "concept:sickness"}])
    out2, _ = S.receive(rest, rs2, prof, present=["concept:sickness"], repeats={"concept:sickness": 2})
    want2 = want * K.magnitude_scale(0.85) * K.repetition(2, True)
    check("a-held-concept-scales-by-connection-and-repetition", abs((out2["WARINESS"] - rest["WARINESS"]) - want2) < 1e-12,
          (out2["WARINESS"] - rest["WARINESS"], want2))
    # the standing bind supplies the about when the reading has none
    out3, _ = S.receive(rest, rs, prof, targets={"WARINESS": "concept:sickness"})
    check("an-unbound-reading-takes-the-paths-standing-about", abs((out3["WARINESS"] - rest["WARINESS"]) - want * K.magnitude_scale(0.85)) < 1e-12)
    # two readings on one path are two additions
    out4, imp4 = S.receive(rest, rs + rs, prof)
    check("two-readings-on-one-path-add-twice", abs((out4["WARINESS"] - rest["WARINESS"]) - 2 * want) < 1e-12 and abs(imp4 - 2 * want) < 1e-12)
    # clamped
    hi = dict(rest, WARINESS=0.99)
    out5, _ = S.receive(hi, rs + rs + rs, prof)
    check("clamped-at-one", out5["WARINESS"] == 1.0)


def test_aboutness_from_readings():
    print("\n[3] ABOUTNESS FROM READINGS")
    ch = _char()
    temp = ch["baseline"]["temperament"]
    aff = {p: temp[p]["mean"] for p in PATHS}
    aff["WARINESS"] = 0.6
    aff["DEFLATION"] = 0.6
    names_w, names_d = rungs.names_on("WARINESS"), rungs.names_on("DEFLATION")
    rs = _parse([{"path": "WARINESS", "rung": names_w[3], "about": "concept:sickness"},
                 {"path": "DEFLATION", "rung": names_d[3], "about": ""}])
    t = T.bind_readings({"DEFLATION": "joss", "GOODWILL": "joss"}, rs, temperament=temp, affect=aff, me="maren")
    check("an-about-binds", t.get("WARINESS") == "concept:sickness", t)
    check("an-empty-about-leaves-the-bind", t.get("DEFLATION") == "joss", t)
    check("a-path-at-rest-clears-its-bind", "GOODWILL" not in t, t)
    self_ok = [p for p in PATHS if admits_role(p, "self")]
    self_no = [p for p in PATHS if not admits_role(p, "self")]
    if self_ok and self_no:
        rs2 = _parse([{"path": self_ok[0], "rung": rungs.names_on(self_ok[0])[2], "about": "maren"},
                      {"path": self_no[0], "rung": rungs.names_on(self_no[0])[2], "about": "maren"}])
        t2 = T.bind_readings({self_no[0]: "joss"}, rs2, me="maren")
        check("a-reflexive-about-binds-only-where-the-basis-admits-self",
              t2.get(self_ok[0]) == "maren" and self_no[0] not in t2, t2)


def test_the_durable_candidate_and_the_wound_read_the_reading():
    print("\n[4/5] THE DURABLE CANDIDATE, AND A WOUND READS THE READING")
    ch = _char()
    cond = {"energy": 0.8, "allostatic_load": 0.2}
    none = _arc.assess({"dimensions": {"threat": 0.1}, "durability": "transient"}, 0.5, ch, cond, heights={"WARINESS": 0.2})
    check("a-low-reading-is-no-candidate", none is None)
    some = _arc.assess({"dimensions": {"threat": 0.1}, "durability": "transient"}, 0.5, ch, cond, heights={"WARINESS": 0.9})
    check("a-reading-at-the-durable-height-is-a-candidate", some is not None, some)
    w = ch["baseline"]["wounds"][0]
    res = 0.5
    d_hi = W.trial(w, {}, res, {"about": "concept:sickness", "surfaces": [], "heights": {"WARINESS": 0.99}})
    d_lo = W.trial(w, {}, res, {"about": "concept:sickness", "surfaces": [], "heights": {"WARINESS": 0.10}})
    check("a-reading-above-the-wound-deepens-it", d_hi > 0, d_hi)
    check("a-reading-below-the-wound-eases-it", d_lo < 0, d_lo)
    check("no-reading-no-dimension-no-move", W.trial(w, {}, res, {"about": "concept:sickness", "surfaces": [], "heights": {}}) == 0.0)


def main():
    print("test_receive.py — Phase 3: the receipt from readings")
    for t in (test_the_receipt_is_the_vector_times_the_multipliers, test_aboutness_from_readings,
              test_the_durable_candidate_and_the_wound_read_the_reading):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
