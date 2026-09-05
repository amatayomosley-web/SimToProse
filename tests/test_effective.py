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
import copy
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


def test_a_wound_scales_the_row_it_names():
    """THE WIRE. Before this, a wound's `intensity` and its row's `magnitude` were two authored
    numbers with nothing between them: `grep intensity src/engine/levers.py` returned nothing, so
    fading Ren's phobia from 0.95 to 0.10 changed which of four phrases the actor read and left his
    FEAR multiplier at 3.4. The field was prose with a number on it."""
    print("\n[9] a wound scales the row it names")
    from src.engine.levers import scale_to_wounds
    ren = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    wounds = ren["baseline"]["drives"]["fears_wounds"]
    rows = [r for r in ren["baseline"]["catalog"]["rows"] if r.get("wound")]
    check("the-fixture-actually-links-rows", len(rows) >= 2 and wounds[0].get("id"),
          "no linked rows -> this test would prove nothing")

    full = {r["lever"]: r["magnitude"] for r in scale_to_wounds(rows, wounds)}
    check("at-authored-intensity-nothing-moves",
          full["FEAR"] == 3.4 and full["SEEKING"] == 0.5, str(full))

    healed = copy.deepcopy(wounds)
    healed[0]["_authored_intensity"], healed[0]["intensity"] = 0.95, 0.15
    part = {r["lever"]: r["magnitude"] for r in scale_to_wounds(rows, healed)}
    check("a-healed-wound-hits-softer", 1.0 < part["FEAR"] < 3.4, str(part))
    # a DEBUFF multiplier (0.5) must decay UPWARD to 1.0, not downward — both directions relax
    # toward the operation's own identity, or a fading wound would invert into a buff.
    check("a-debuff-decays-upward", 0.5 < part["SEEKING"] < 1.0, str(part))

    gone = copy.deepcopy(wounds)
    gone[0]["_authored_intensity"], gone[0]["intensity"] = 0.95, 0.0
    zero = {r["lever"]: r["magnitude"] for r in scale_to_wounds(rows, gone)}
    check("a-spent-wound-is-the-identity", zero["FEAR"] == 1.0 and zero["SEEKING"] == 1.0, str(zero))

    # and it must reach the VECTOR, not just the row
    base = {p: 0.3 for p in PRIMARIES}
    check("the-scaling-reaches-effective",
          effective(base, scale_to_wounds(rows, healed))["FEAR"]
          < effective(base, scale_to_wounds(rows, wounds))["FEAR"])


def test_an_unlinked_row_is_untouched():
    """THE MIGRATION GUARANTEE, and the reason this shipped opt-in. Every row in every book
    authored before the wire exists carries no `wound` key."""
    print("\n[10] an unlinked row is byte-identical")
    from src.engine.levers import scale_to_wounds
    rows = [{"lever": "FEAR", "op": "x", "magnitude": 3.4, "source": "s"},
            {"lever": "CARE", "op": "+", "magnitude": 0.22, "source": "s"}]
    wounds = [{"id": "w", "wound": "x", "intensity": 0.1, "_authored_intensity": 0.9}]
    out = scale_to_wounds(rows, wounds)
    check("unlinked-rows-pass-through", out == rows, str(out))
    check("no-wounds-at-all-is-a-no-op", scale_to_wounds(rows, []) == rows)


def test_the_authored_magnitude_survives_for_the_trace():
    """`scene.assemble` publishes the fired rows as the audit trace. A trace showing only the
    scaled number could not be checked against the sheet it came from."""
    print("\n[11] the authored magnitude rides along")
    from src.engine.levers import scale_to_wounds
    rows = [{"wound": "w", "lever": "FEAR", "op": "x", "magnitude": 3.4, "source": "s"}]
    wounds = [{"id": "w", "wound": "x", "intensity": 0.2, "_authored_intensity": 0.8}]
    out = scale_to_wounds(rows, wounds)[0]
    check("authored-kept", out["_authored_magnitude"] == 3.4, str(out))
    check("effective-differs", out["magnitude"] != 3.4, str(out))


def test_a_wound_that_cannot_scale_fails_loud():
    """A non-numeric intensity reaches no arithmetic, and a zero authored intensity makes the ratio
    undefined. Both are refused by name rather than silently treated as 'no change'."""
    print("\n[12] fail loud, never a silent full-strength row")
    from src.engine.levers import scale_to_wounds
    rows = [{"wound": "w", "lever": "FEAR", "op": "x", "magnitude": 3.4, "source": "s"}]
    for bad, why in (([{"id": "w", "intensity": "it takes me over"}], "prose intensity"),
                     ([{"id": "w", "intensity": 0.0, "_authored_intensity": 0.0}], "zero denominator")):
        try:
            scale_to_wounds(rows, bad)
            check("raises-on-%s" % why, False, "returned instead of raising")
        except ValueError as e:
            check("raises-on-%s" % why, "w" in str(e), str(e))


def test_the_fold_stamps_the_authored_value_before_it_moves_anything():
    """THE ACCEPTANCE TEST FOR THE WHOLE TIER, and the order is the entire point.

    `scale_to_wounds` divides by `_authored_intensity` and falls back to the CURRENT value when the
    key is absent. Stamp AFTER folding and that fallback reads the already-healed number, the ratio
    becomes 1.0, and a wound faded to nothing goes on hitting the arithmetic at full authored
    strength forever — silently. A review of the store called this the one decision most likely to
    be quietly wrong, because the sibling fold (`arc.apply`) does not stamp anything and a
    copy-the-neighbour implementation would reintroduce it.
    """
    print("\n[13] the fold stamps before it moves")
    from src.engine.levers import replay_wound_deltas, scale_to_wounds
    sheet = [{"id": "w", "wound": "the bite", "intensity": 0.95}]
    check("sheet-starts-unstamped", "_authored_intensity" not in sheet[0], str(sheet[0]))
    replay_wound_deltas(sheet, [("w", -0.4, "event"), ("w", -0.2, "event")])
    check("authored-is-the-ORIGINAL", abs(sheet[0]["_authored_intensity"] - 0.95) < 1e-9, str(sheet[0]))
    check("intensity-is-the-FOLDED", abs(sheet[0]["intensity"] - 0.35) < 1e-9, str(sheet[0]))
    rows = [{"wound": "w", "lever": "FEAR", "op": "x", "magnitude": 3.4, "source": "s"}]
    scaled = scale_to_wounds(rows, sheet)[0]["magnitude"]
    check("the-ratio-actually-bit", 1.0 < scaled < 3.4, "%.4f" % scaled)

    # ORDER-INDEPENDENT: summed then clamped once. arc.apply and bonds.replay clamp per step, which
    # diverges the moment a running total leaves [0,1] — so this is a deliberate difference, pinned.
    a = replay_wound_deltas([dict(id="w", wound="x", intensity=0.5)],
                            [("w", 0.8, "event"), ("w", -0.7, "event")])[0]["intensity"]
    b = replay_wound_deltas([dict(id="w", wound="x", intensity=0.5)],
                            [("w", -0.7, "event"), ("w", 0.8, "event")])[0]["intensity"]
    check("fold-is-order-independent", abs(a - b) < 1e-12, "%.6f vs %.6f" % (a, b))

    # a re-fold must not re-stamp from the moved value
    replay_wound_deltas(sheet, [("w", -0.1, "erosion")])
    check("refold-keeps-the-original-authored", abs(sheet[0]["_authored_intensity"] - 0.95) < 1e-9,
          str(sheet[0]))


def test_a_deepened_wound_does_not_kill_the_beat():
    """THE CRASH. A wound can DEEPEN past what its author wrote, so the ratio is not bounded by 1 —
    and for a SUPPRESSING multiplier the scaled value goes negative, at which point `_check_row`
    raises from inside `effective`, the one function every decision depends on, blaming the author
    for a number they never wrote.

    Found by review, not by this suite: every prior test here used ratio <= 1. Reachable by ordinary
    authoring — any suppressing row on a wound authored at or below `1 - magnitude`, i.e. a mild
    dread the book then deepens, which is the arc the tier exists to produce."""
    print('\n[15] a deepened wound must not crash the decision')
    from src.engine.levers import scale_to_wounds
    # ren-traveler's REAL suppressing row, on a wound authored mild and deepened by the book
    deepened = [{"id": "w", "wound": "x", "intensity": 0.90, "_authored_intensity": 0.40}]
    rows = [{"wound": "w", "lever": "SEEKING", "op": "x", "magnitude": 0.5, "source": "s"}]
    out = scale_to_wounds(rows, deepened)
    check("ratio-above-one-is-reachable", 0.90 / 0.40 > 1.0)
    check("suppressor-floors-at-zero-not-negative", out[0]["magnitude"] == 0.0,
          str(out[0]["magnitude"]))
    try:
        effective({p: 0.3 for p in PRIMARIES}, out)
        check("effective-does-not-raise", True)
    except ValueError as e:
        check("effective-does-not-raise", False, str(e))
    # a BOOSTING row deepens past its authored value, which is the point of deepening
    boost = scale_to_wounds([{"wound": "w", "lever": "FEAR", "op": "x", "magnitude": 3.4,
                              "source": "s"}], deepened)[0]["magnitude"]
    check("a-booster-grows-past-its-authored-value", boost > 3.4, "%.4f" % boost)
    # and an unmoved wound is still exact
    same = [{"id": "w", "wound": "x", "intensity": 0.95, "_authored_intensity": 0.95}]
    check("unmoved-is-still-byte-exact",
          scale_to_wounds([{"wound": "w", "lever": "FEAR", "op": "x", "magnitude": 3.4,
                            "source": "s"}], same)[0]["magnitude"] == 3.4)


def test_the_bookkeeping_key_never_reaches_the_actor():
    """REGRESSION GUARD for a leak `tests/test_no_digits.py` cannot catch. Before the rename, a
    wound carrying both keys rendered `authored_intensity: this above most things` beside
    `how it takes you: it catches you sometimes` — two contradictory statements about one wound,
    one of them the engine's own arithmetic. No digit appeared, because `_say_scalars` bands the
    float into a phrase, so the digit guard passed it."""
    print("\n[14] the bookkeeping key is stripped before the prompt")
    from src.engine.identity_view import direct_identity
    from src.engine.levers import replay_wound_deltas
    from src.engine.scene import _strip_notes           # the identity-prefix filter itself
    wounds = replay_wound_deltas([{"id": "w", "wound": "the spider", "intensity": 0.95}],
                                 [("w", -0.55, "event")])
    rendered = json.dumps(direct_identity({"drives": _strip_notes({"fears_wounds": wounds})}))
    check("no-authored-key-in-the-prompt", "authored" not in rendered, rendered)
    check("the-wound-itself-still-renders", "the spider" in rendered, rendered)
    check("and-it-says-how-it-takes-you", "how it takes you" in rendered, rendered)
    # prove the guard would FAIL without the underscore — or it proves nothing
    leaky = json.dumps(direct_identity({"drives": _strip_notes(
        {"fears_wounds": [{"wound": "the spider", "intensity": 0.4, "authored_intensity": 0.95}]})}))
    check("the-control-leaks", "authored_intensity" in leaky, leaky)


def main():
    print("test_effective.py — the effective-levers tier + the spider test")
    # DISCOVERED, NOT LISTED — the same hand-maintained tuple that let four new tests sit unrun in
    # tests/test_arc.py while the suite printed PASS. Ordered by definition line so the [N]
    # headings stay in reading order.
    for t in sorted((v for k, v in globals().items() if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
