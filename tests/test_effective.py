"""test_effective.py — the effective-levers tier (src/engine/levers.py).

THE SPIDER TEST is the acceptance criterion (the author, 2026-08-22):

  "If a person is brave but has a morbid fear of spiders. They are alone in a cave when they
   encounter a massive spider they would run, but if they are with someone they want to protect
   then depending on the other numbers they may overcome fear and fight. This isn't possible if
   we tag a person as a coward. Because there is no nuance in the tag."

Same character, same stimulus, different context -> different numbers -> different direction, with
the difference falling out of ARITHMETIC and no trait word anywhere. `characters/ren-traveler.json`
is the fixture: threat_reactivity "low" and resting FEAR 0.22 (a genuinely steady man), with the
phobia living entirely in `baseline.catalog` — because a single global gain cannot say
"brave except about spiders", which is the whole point.

What this pins, and why each matters:
  1. IDENTITY with no rows — the migration guarantee. Every run predating the tier reproduces
     byte-identically, which is checkable rather than argued.
  2. The formula — `base x PI(multipliers) + SUM(adds)`, clamped (decision-engine.md:80).
  3. FAIL LOUD on a malformed row. A row that silently never fires is the exact defect this tier
     exists to end; discovering it at authoring time is the whole value.
  4. All four condition kinds from decision-engine.md's worked entries.
  5. THE CEILING IS BROKEN. Before the tier, FEAR was bounded by `mean + (1-mean)*r` — measured
     identical across all four threat_reactivity alleles at maximum severity, so a brave character
     could never reach the flee band and bravery was an IMMUNITY. The tier must lift a resting-0.22
     character above that bound.
  6. NO ACTION SELECTION. decision-engine.md:85 is normative: the catalog computes STATE, never the
     action. If an argmax ever appears in levers.py this suite should be the thing that objects.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.levers import effective, active_rows          # noqa: E402
from src.engine.records import PRIMARIES                       # noqa: E402
from src.engine.scene import assemble                          # noqa: E402
from src.engine.direction import direct_affect                 # noqa: E402

_FAILS = []


Q3 = chr(34) * 3
S3 = chr(39) * 3


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def flat(v=0.30):
    return {p: v for p in PRIMARIES}


def _fixture():
    ch = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    w = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    return ch, w


def test_identity():
    print("\n[1] IDENTITY — no rows changes nothing (the migration guarantee)")
    cur = flat(0.42)
    check("no-rows-is-identity", effective(cur) == cur)
    check("empty-list-is-identity", effective(cur, []) == cur)
    check("none-catalog-yields-no-rows", active_rows(None, {}) == [])
    check("input-not-mutated", cur == flat(0.42))


def test_formula():
    print("\n[2] FORMULA — base x PI(mult) + SUM(add), clamped")
    cur = flat(0.20)
    cur["FEAR"] = 0.40
    e = effective(cur, [{"lever": "FEAR", "op": "x", "magnitude": 2.0, "source": "a"}])
    check("multiplier", abs(e["FEAR"] - 0.80) < 1e-9, e["FEAR"])
    e = effective(cur, [{"lever": "FEAR", "op": "+", "magnitude": 0.25, "source": "a"}])
    check("additive", abs(e["FEAR"] - 0.65) < 1e-9, e["FEAR"])
    e = effective(cur, [{"lever": "FEAR", "op": "+", "magnitude": -0.30, "source": "a"}])
    check("additive-negative-is-a-debuff", abs(e["FEAR"] - 0.10) < 1e-9, e["FEAR"])
    # multipliers before adds, so authoring order within a kind cannot change the result
    rows = [{"lever": "FEAR", "op": "+", "magnitude": 0.10, "source": "a"},
            {"lever": "FEAR", "op": "x", "magnitude": 2.0, "source": "b"}]
    check("mult-applies-before-add",
          abs(effective(cur, rows)["FEAR"] - 0.90) < 1e-9, effective(cur, rows)["FEAR"])
    check("order-within-kind-irrelevant",
          effective(cur, rows) == effective(cur, list(reversed(rows))))
    e = effective(cur, [{"lever": "FEAR", "op": "x", "magnitude": 9.0, "source": "a"}])
    check("clamped-high", e["FEAR"] == 1.0, e["FEAR"])
    e = effective(cur, [{"lever": "FEAR", "op": "+", "magnitude": -9.0, "source": "a"}])
    check("clamped-low", e["FEAR"] == 0.0, e["FEAR"])
    check("other-levers-untouched", e["CARE"] == 0.20)


def test_fail_loud():
    print("\n[3] FAIL LOUD — a silent row is the defect this tier exists to end")
    cur = flat()
    bad = [
        ("unknown-lever",     {"lever": "COURAGE", "op": "x", "magnitude": 2.0}),
        ("bad-op",            {"lever": "FEAR", "op": "^", "magnitude": 2.0}),
        ("non-numeric",       {"lever": "FEAR", "op": "x", "magnitude": "a lot"}),
        ("negative-multiple", {"lever": "FEAR", "op": "x", "magnitude": -2.0}),
        ("row-not-a-dict",    "FEAR x2"),
    ]
    for name, row in bad:
        try:
            effective(cur, [row])
            check(name, False, "did NOT raise")
        except ValueError:
            check(name, True)
    # and rows are validated even when INACTIVE — authoring-time discovery, not runtime surprise
    try:
        active_rows([{"when": {"percept": ["nothing here"]}, "lever": "NOPE",
                      "op": "x", "magnitude": 1.0}], {"text": "an empty room"})
        check("inactive-rows-still-validated", False, "did NOT raise")
    except ValueError:
        check("inactive-rows-still-validated", True)


def test_conditions():
    print("\n[4] CONDITIONS — all four kinds from decision-engine.md's worked entries")
    R = lambda when: [{"when": when, "lever": "FEAR", "op": "x", "magnitude": 2.0, "source": "s"}]
    ctx = {"text": "a spider drops from the dark", "edges": {}, "affect": flat(), "condition": {}}
    check("percept-hit", len(active_rows(R({"percept": ["spider"]}), ctx)) == 1)
    check("percept-miss", len(active_rows(R({"percept": ["wolf"]}), ctx)) == 0)
    ctx_e = dict(ctx, edges={"joss": {"trust": 0.8, "affinity": 0.9}})
    check("edge-hit", len(active_rows(R({"present_edge": {"affinity": 0.7}}), ctx_e)) == 1)
    check("edge-miss-threshold", len(active_rows(R({"present_edge": {"affinity": 0.95}}), ctx_e)) == 0)
    check("edge-miss-nobody-present", len(active_rows(R({"present_edge": {"affinity": 0.7}}), ctx)) == 0)
    check("edge-named-id", len(active_rows(R({"present_edge": {"id": "edda", "affinity": 0.7}}), ctx_e)) == 0)
    ctx_a = dict(ctx, affect=dict(flat(), RAGE=0.80))
    check("affect-hit", len(active_rows(R({"affect_at_least": {"RAGE": 0.7}}), ctx_a)) == 1)
    check("affect-miss", len(active_rows(R({"affect_at_least": {"RAGE": 0.9}}), ctx_a)) == 0)
    ctx_c = dict(ctx, condition={"energy": 0.20})
    check("condition-hit", len(active_rows(R({"condition_at_most": {"energy": 0.35}}), ctx_c)) == 1)
    check("condition-miss", len(active_rows(R({"condition_at_most": {"energy": 0.10}}), ctx_c)) == 0)
    check("clauses-AND-together",
          len(active_rows(R({"percept": ["spider"], "present_edge": {"affinity": 0.7}}), ctx)) == 0)
    check("no-when-is-always-active",
          len(active_rows([{"lever": "FEAR", "op": "x", "magnitude": 2.0, "source": "s"}], ctx)) == 1)


def test_ceiling_is_broken():
    print("\n[5] THE CEILING — a brave character can now exceed mean + (1-mean)*r")
    ch, w = _fixture()
    from src.engine.state import build_profile, appraise, decay
    from src.engine.direction import _band, _BANDS
    prof = build_profile(ch)
    temp = ch["baseline"]["temperament"]
    # TIER 1 ALONE, run to equilibrium under sustained MAXIMUM threat. This is the hard bound
    # the old single-tier path could never exceed -- not with any event, not with any genotype.
    a = dict(ch["current"]["affect"])
    for _ in range(400):
        a = decay(appraise(a, {"dimensions": {"threat": 1.0}}, prof), temp, prof)
    tier1_max = a["FEAR"]
    ev = "A spider the size of a dog drops from the dark above the one narrow ledge out."
    # start FROM that maximum: if tier 3 can still move it, the bound is genuinely broken
    pk = assemble(ch, w, {"event": {"text": ev, "kind": "threat"}, "recent": [],
                          "location": "upland_road"}, dict(a), ch["current"]["condition"])
    eff = pk["volatile"]["state"]["effective"]["FEAR"]
    rawf = pk["volatile"]["state"]["affect"]["FEAR"]
    check("phobia-row-fires", eff > rawf, "%.3f vs %.3f" % (eff, rawf))
    check("tier-3-exceeds-the-tier-1-hard-bound", eff > tier1_max + 1e-9,
          "effective %.3f vs tier-1 sustained maximum %.3f" % (eff, tier1_max))
    # and from REST the phobia alone carries him into a band his own calm never reaches
    pk0 = assemble(ch, w, {"event": {"text": ev, "kind": "threat"}, "recent": [],
                           "location": "upland_road"},
                   dict(ch["current"]["affect"]), ch["current"]["condition"])
    rest_eff = pk0["volatile"]["state"]["effective"]["FEAR"]
    rest_raw = ch["current"]["affect"]["FEAR"]
    check("phobia-lifts-him-two-bands-from-rest",
          _band(rest_eff, _BANDS) >= _band(rest_raw, _BANDS) + 2,
          "%.3f (band %d) from %.3f (band %d)"
          % (rest_eff, _band(rest_eff, _BANDS), rest_raw, _band(rest_raw, _BANDS)))
    check("the-genotype-still-says-brave",
          ch["fixed"]["genotype"]["threat_reactivity"].startswith("low"))


def test_spider_A_vs_B():
    print("\n[6] THE SPIDER TEST — same man, same spider, different company")
    ch, w = _fixture()
    temp = ch["baseline"]["temperament"]
    A = ("A spider the size of a dog drops from the dark above the one narrow ledge out, "
         "fangs working. Ren is alone in the deep gallery.")
    B = A.replace("Ren is alone in the deep gallery.", "Joss is pressed against the wall behind Ren.")
    out = {}
    for name, ev in (("A", A), ("B", B)):
        pk = assemble(ch, w, {"event": {"text": ev, "kind": "threat"}, "recent": [],
                              "location": "upland_road"},
                      dict(ch["current"]["affect"]), ch["current"]["condition"])
        st = pk["volatile"]["state"]
        out[name] = (st["effective"], direct_affect(st["effective"], temp),
                     len(pk["volatile"]["levers"]))
    (eA, dA, nA), (eB, dB, nB) = out["A"], out["B"]
    print("     A: %d rows  FEAR %.3f  CARE %.3f" % (nA, eA["FEAR"], eA["CARE"]))
    print("     B: %d rows  FEAR %.3f  CARE %.3f" % (nB, eB["FEAR"], eB["CARE"]))
    check("company-fires-more-rows", nB > nA, "%d vs %d" % (nB, nA))
    check("fear-lower-with-someone-to-protect", eB["FEAR"] < eA["FEAR"],
          "%.3f vs %.3f" % (eB["FEAR"], eA["FEAR"]))
    check("care-higher-with-someone-to-protect", eB["CARE"] > eA["CARE"],
          "%.3f vs %.3f" % (eB["CARE"], eA["CARE"]))
    check("the-DIRECTION-differs", dA != dB, "identical direction in both scenes")
    # the contest must actually reverse, not merely shift: fear dominates alone, care with company
    check("contest-reverses",
          (eA["FEAR"] > eA["CARE"]) and (eB["CARE"] > eB["FEAR"]),
          "A fear %.3f/care %.3f ; B fear %.3f/care %.3f"
          % (eA["FEAR"], eA["CARE"], eB["FEAR"], eB["CARE"]))
    check("no-digits-reach-the-actor", not any(c.isdigit() for c in dA + dB), dA)


def test_no_action_selection():
    print("\n[7] THE HARD LINE — the catalog computes STATE, never the action")
    # Scan CODE only. levers.py's own comment quotes decision-engine.md FORBIDDING argmax, and
    # a scan that cannot tell a prohibition from a violation is the guard-quoting-what-it-bans
    # trap -- the same shape that made the private-content guard flag its own banned list.
    raw = open(os.path.join(REPO, "src/engine/levers.py"), encoding="utf-8").read().splitlines()
    code, in_doc = [], False
    for ln in raw:
        st = ln.strip()
        if st.startswith(Q3) or st.startswith(S3):
            in_doc = not in_doc
            continue
        if in_doc or st.startswith('#'):
            continue
        code.append(ln.split('#', 1)[0])
    src = chr(10).join(code)
    banned = [w for w in ("argmax", "def choose", "def decide", "def select_action") if w in src]
    check("no-action-selection-in-levers", not banned, "found: %s" % banned)
    ch, _w = _fixture()
    rows = (ch["baseline"]["catalog"] or {}).get("rows") or []
    check("every-lever-is-a-bounded-primary",
          all(r["lever"] in PRIMARIES for r in rows),
          [r["lever"] for r in rows if r["lever"] not in PRIMARIES])


def test_antagonistic_edges():
    """An edge must be testable on BOTH sides, and aboutness must differ from presence.

    relationships.md says the axes gate help/betray, believe/DOUBT, defer/OVERRIDE, comply/REFUSE.
    A gate that can only test the favourable side of an axis reads half of that: it can say "an
    ally is present" and never "an enemy is present", so an antagonistic disposition cannot fire a
    row at all. And "the man I hate is here" is not the same fact as "this is ABOUT the man I hate".

    NOTE the deliberate non-fix: state.py:184 lifts regard by affinity and never lowers it
    ("affinity lifts, never lowers"), and _REGARD_SCALED_DIMS covers only care_relevant and loss.
    That commitment stands -- dislike must not scope empathy down; you can wince for someone you
    hate. Antagonism is routed through RAGE/DISGUST comportment instead, in the catalog, where it
    stays authored per character rather than becoming a universal engine rule.
    """
    print("\n[8] ANTAGONISTIC EDGES - hate as a trigger, and aboutness vs presence")
    from src.engine.levers import active_rows
    edges = {"foe": {"trust": 0.10, "affinity": 0.05},
             "friend": {"trust": 0.85, "affinity": 0.90}}
    cur = flat(0.25)
    hate = [{"when": {"target_edge": {"affinity_at_most": 0.25}},
             "lever": "RAGE", "op": "x", "magnitude": 2.4, "source": "him specifically"}]
    near = [{"when": {"present_edge": {"affinity_at_most": 0.25}},
             "lever": "PLAY", "op": "x", "magnitude": 0.3, "source": "not while he is here"}]
    ctx = lambda t: {"text": "words", "edges": edges, "affect": cur, "condition": {}, "target": t}
    check("at_most-fires-on-a-LOW-axis", len(active_rows(hate, ctx("foe"))) == 1)
    check("at_most-does-not-fire-on-a-high-axis", len(active_rows(hate, ctx("friend"))) == 0)
    check("target_edge-is-not-presence",
          len(active_rows(hate, ctx("friend"))) == 0 and len(active_rows(near, ctx("friend"))) == 1,
          "the foe is PRESENT in both, but only the target row should care who it is about")
    e_foe = effective(cur, active_rows(hate, ctx("foe")))
    e_fr = effective(cur, active_rows(hate, ctx("friend")))
    check("hate-pulls-the-vector-toward-it", e_foe["RAGE"] > e_fr["RAGE"],
          "%.3f vs %.3f" % (e_foe["RAGE"], e_fr["RAGE"]))
    # at-least still means at-least: every row authored before this change is unaffected
    ally = [{"when": {"present_edge": {"affinity": 0.70}},
             "lever": "FEAR", "op": "x", "magnitude": 0.6, "source": "someone at my back"}]
    check("bare-axis-still-means-at-least", len(active_rows(ally, ctx("foe"))) == 1)
    try:
        active_rows([{"when": {"present_edge": {"warmth": 0.5}}, "lever": "RAGE",
                      "op": "x", "magnitude": 1.0}], ctx("foe"))
        check("unknown-edge-clause-fails-loud", False, "did NOT raise")
    except ValueError:
        check("unknown-edge-clause-fails-loud", True)


def main():
    print("test_effective.py — the effective-levers tier + the spider test")
    for t in (test_identity, test_formula, test_fail_loud, test_conditions,
              test_ceiling_is_broken, test_spider_A_vs_B, test_no_action_selection,
              test_antagonistic_edges):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
