#!/usr/bin/env python3
"""test_arc.py — the Arc Engine (durable baseline change). Proves arc-engine.md's core:
the slow-burn arc (a bond raising affinity + eroding class-disregard), the durable threshold
(most events stay transient), the resilience FORK (same threat -> damage or growth), and bounded
apply. Script-style, stdlib, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import arc                                    # noqa: E402
from src.engine.records import PRIMARIES                       # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


def _char(ec="typical", aff_to_nessa=0.25, regard_dorn=0.2, load=0.3):
    return {
        "fixed": {"genotype": {"effortful_control": ec, "affiliation_attachment": "high"}},
        "baseline": {
            "temperament": {p: {"mean": 0.4, "variability": 0.1} for p in PRIMARIES},
            "model": {"regard": {"dorn": regard_dorn}},
        },
        "current": {
            "relationships": {"nessa": {"trust": 0.3, "affinity": aff_to_nessa, "respect": 0.2, "debt": 0.3}},
            "condition": {"allostatic_load": load},
        },
    }


def _connection(mag=0.7):
    return {"dimensions": {"care_relevant": mag, "relief": 0.3}, "durability": "durable",
            "target": "nessa", "target_group": "dorn"}


def test_slow_burn_arc():
    """A durable CONNECTION with Nessa raises affinity to her AND erodes regard['dorn'] toward 1.0."""
    print("\n[1] SLOW-BURN ARC (the bond teaches the class)")
    ch = _char()
    diff = arc.assess(_connection(), impact=0.6, char=ch, condition=ch["current"]["condition"])
    check("connection-writes-durable", diff is not None)
    if diff:
        # The arc STOPPED writing relationship edges on 2026-08-23 (gate bonds-inversion):
        # it runs on the ACTOR and an edge belongs to the PERCEIVER, so a betrayal used to drop
        # the BETRAYER's trust in their victim. `bonds.py` owns edges now; the arc owns
        # temperament and the bigotry regard. `tests/test_bonds.py` [9] pins the handover, and
        # `arc.apply` still REPLAYS a stored relationships block (append-only log, hard rule 2).
        check("no-longer-writes-edges", "relationships" not in diff, sorted(diff))
        check("CARE-rises-instead", diff["temperament"]["CARE"] > 0, str(diff["temperament"]))
        check("regard-erodes-up", diff["regard"]["dorn"] > 0, str(diff["regard"]))
        new = arc.apply(ch, diff)
        check("CARE-actually-rose",
              new["baseline"]["temperament"]["CARE"]["mean"] > ch["baseline"]["temperament"]["CARE"]["mean"])
        check("regard-actually-rose",
              new["baseline"]["model"]["regard"]["dorn"] > ch["baseline"]["model"]["regard"]["dorn"])

    # accumulation across many beats: affinity climbs monotonically toward 1.0
    ch2 = _char()
    affinities = [ch2["current"]["relationships"]["nessa"]["affinity"]]
    for _ in range(12):
        d = arc.assess(_connection(), impact=0.6, char=ch2, condition=ch2["current"]["condition"])
        if d:
            ch2 = arc.apply(ch2, d)
        affinities.append(ch2["baseline"]["temperament"]["CARE"]["mean"])
    # tracks CARE rather than the edge: edges moved to bonds.py, the arc moves temperament
    check("CARE-climbs-monotonically", all(b >= a for a, b in zip(affinities, affinities[1:])))
    check("CARE-rose-substantially", affinities[-1] - affinities[0] > 0.05,
          "start %.2f -> end %.2f" % (affinities[0], affinities[-1]))
    check("regard-also-eroded", ch2["baseline"]["model"]["regard"]["dorn"] > 0.2 + 0.05)


def test_threshold_keeps_most_transient():
    """A low-impact / non-severe event writes NO durable diff — the floor doesn't move on small things."""
    print("\n[2] DURABLE THRESHOLD")
    ch = _char()
    mundane = {"dimensions": {"mastery": 0.2}, "durability": "transient"}
    check("mundane-no-diff", arc.assess(mundane, impact=0.1, char=ch, condition=ch["current"]["condition"]) is None)
    # even a durable-flagged event with near-zero impact stays under the magnitude threshold
    weak = {"dimensions": {"care_relevant": 0.6}, "durability": "durable", "target": "nessa", "target_group": "dorn"}
    check("tiny-impact-no-diff", arc.assess(weak, impact=0.05, char=ch, condition=ch["current"]["condition"]) is None)


def test_resilience_fork():
    """Same survival-threat: low resilience -> FEAR-baseline UP (trauma); high -> SEEKING UP (growth)."""
    print("\n[3] RESILIENCE FORK (damage OR growth)")
    threat = {"dimensions": {"threat": 0.85}, "durability": "durable"}
    # low resilience: low effortful_control + high allostatic load + no secure bond
    low = {"fixed": {"genotype": {"effortful_control": "low"}},
           "baseline": {"temperament": {p: {"mean": 0.4, "variability": 0.1} for p in PRIMARIES}},
           "current": {"relationships": {}, "condition": {"allostatic_load": 0.8}}}
    # high resilience: high effortful_control + low load + a secure bond
    high = {"fixed": {"genotype": {"effortful_control": "high"}},
            "baseline": {"temperament": {p: {"mean": 0.4, "variability": 0.1} for p in PRIMARIES}},
            "current": {"relationships": {"ally": {"affinity": 0.9}}, "condition": {"allostatic_load": 0.1}}}
    d_low = arc.assess(threat, impact=0.8, char=low, condition=low["current"]["condition"])
    d_high = arc.assess(threat, impact=0.8, char=high, condition=high["current"]["condition"])
    check("low-resilience-fear-up", d_low and d_low["temperament"].get("FEAR", 0) > 0, str(d_low))
    check("high-resilience-growth", d_high and d_high["temperament"].get("SEEKING", 0) > 0, str(d_high))
    # THE GRADIENT, not the presence of a key. This assertion used to read
    # `"SEEKING" not in d_low["temperament"]`, which passed only because the old branches wrote one
    # primary per event. Under `state._DIM_TO_PRIMARY` a threat ALSO pushes SEEKING at low
    # resilience, and correctly: that push is hypervigilance (state.py's threat row), the scanning
    # of a man who cannot stop checking the door. Growth and vigilance are not distinguished by
    # WHICH key moves. They are distinguished by the COMPANY it keeps.
    sl, sh = d_low["temperament"].get("SEEKING", 0), d_high["temperament"].get("SEEKING", 0)
    check("growth-outruns-vigilance", sh > sl, "resilient %+.4f vs broken %+.4f" % (sh, sl))
    # and the sign of FEAR is what tells the two apart — the resilient man comes out of the same
    # threat LESS afraid, which no scalar buffering of a single FEAR write could ever produce.
    check("the-same-threat-inverts-fear",
          d_low["temperament"].get("FEAR", 0) > 0 > d_high["temperament"].get("FEAR", 0),
          "broken %+.4f, resilient %+.4f" % (d_low["temperament"].get("FEAR", 0),
                                             d_high["temperament"].get("FEAR", 0)))
    # THE FLATTENING, which is why the arc was rewritten at all: eighty durable diffs of beatings
    # used to leave PLAY, CARE, RAGE and DISGUST at exactly their authored values because the
    # branches never wrote them. A threat must now cost the broken man his PLAY.
    check("a-threat-costs-play", d_low["temperament"].get("PLAY", 0) < 0, str(d_low["temperament"]))
    check("a-threat-reaches-more-than-one-primary", len(d_low["temperament"]) >= 4,
          str(d_low["temperament"]))
    check("resilience-derives-ordered",
          arc.derive_resilience(low, low["current"]["condition"]) < arc.derive_resilience(high, high["current"]["condition"]))


def test_apply_bounded_and_fail_loud():
    print("\n[4] BOUNDED APPLY + FAIL LOUD")
    ch = _char(regard_dorn=0.95)
    # a big regard erosion clamps at 1.0
    new = arc.apply(ch, {"regard": {"dorn": +0.5}})
    check("regard-clamped-at-1", new["baseline"]["model"]["regard"]["dorn"] == 1.0)
    new2 = arc.apply(ch, {"temperament": {"FEAR": +5.0}})
    check("temperament-clamped-at-1", new2["baseline"]["temperament"]["FEAR"]["mean"] == 1.0)
    for bad in (lambda: arc.assess("notadict", 0.5, ch, {}), lambda: arc.apply("x", {}),
                lambda: arc.derive_resilience("x", {})):
        try:
            bad(); check("fail-loud", False, "accepted bad input"); return
        except ValueError:
            pass
    check("fail-loud-all", True)


def test_persist_roundtrip():
    """append_arc_diff writes a diff that reads back from the arc_diffs table."""
    print("\n[5] PERSISTENCE ROUND-TRIP")
    import json, shutil, tempfile
    from src.engine.ledger import Ledger
    tmp = tempfile.mkdtemp(prefix="swe_arc_")
    try:
        led = Ledger(os.path.join(tmp, "arc.db"))
        led.create_run("r1", {"catalog_version": 1})
        led.register_character("r1", "corin", {"name": "Corin"}, {"temperament": "x"})
        diff = {"relationships": {"nessa": {"affinity": 0.07}}, "regard": {"dorn": 0.03}}
        led.append_arc_diff("r1", "corin", 4, diff)
        row = led.con.execute("SELECT diff FROM arc_diffs WHERE run_id='r1' AND char_id='corin' AND turn=4").fetchone()
        check("arc-diff-persisted", row is not None)
        check("arc-diff-roundtrips", row and json.loads(row["diff"])["relationships"]["nessa"]["affinity"] == 0.07)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _bonded(aff_nessa=0.9, aff_stranger=0.2, ec="typical", load=0.3):
    """One strong bond and one weak one — so excluding the strong one is MEASURABLE."""
    ch = _char(ec=ec, load=load)
    ch["current"]["relationships"] = {
        "nessa":    {"trust": 0.8, "affinity": aff_nessa,    "respect": 0.7, "debt": 0.1},
        "stranger": {"trust": 0.2, "affinity": aff_stranger, "respect": 0.2, "debt": 0.0},
    }
    return ch


def _loss(target, mag=0.8):
    return {"dimensions": {"loss": mag, "threat": 0.2}, "durability": "durable", "target": target}


def test_the_severed_bond_does_not_buffer_its_own_severing():
    """THE DEFECT. `derive_resilience` took the max affinity over EVERY edge with nothing about the
    event reaching it, so grief at losing Nessa was softened by the character's love for Nessa."""
    print("\n[9] the severed bond cannot buffer the severing")
    ch = _bonded()
    cond = ch["current"]["condition"]

    r_all = arc.derive_resilience(ch, cond)
    r_less = arc.derive_resilience(ch, cond, excluded="nessa")
    check("excluding-the-bond-lowers-resilience", r_all - r_less >= 0.15,
          "all=%.4f excluded=%.4f delta=%.4f" % (r_all, r_less, r_all - r_less))

    d_her = arc.assess(_loss("nessa"), impact=0.8, char=ch, condition=cond)
    d_other = arc.assess(_loss("stranger"), impact=0.8, char=ch, condition=cond)
    check("both-events-write-grief", bool(d_her) and bool(d_other), "%r / %r" % (d_her, d_other))
    if d_her and d_other:
        g_her = d_her["temperament"]["PANIC_GRIEF"]
        g_other = d_other["temperament"]["PANIC_GRIEF"]
        check("losing-the-loved-one-hurts-more", g_her > g_other,
              "loss of nessa=%.5f vs loss of stranger=%.5f" % (g_her, g_other))


def test_a_bond_still_buffers_a_threat_it_had_nothing_to_do_with():
    """THE OTHER HALF, and the reason the exclusion is keyed on the dimension rather than applied
    to every event with a target. A wolf's subject is the source of danger, not a withdrawn
    support; the literature the attachment term models is about support that SURVIVED."""
    print("\n[10] a bond still buffers an unrelated threat")
    ch = _bonded()
    cond = ch["current"]["condition"]
    threat = {"dimensions": {"threat": 0.8, "loss": 0.1}, "durability": "durable", "target": "nessa"}
    d = arc.assess(threat, impact=0.8, char=ch, condition=cond)
    check("threat-targeting-the-bond-writes-a-diff", bool(d), str(d))
    # THE EXCLUSION, tested by DIFFERENCE rather than by re-deriving the formula. The old form
    # asserted `abs(got - 0.07 * 0.8 * (1 - r)) < 1e-9`, a hand-copy of the arc's arithmetic living
    # in a test — so it failed the moment the arc was routed through the one pricing table, though
    # nothing it meant to check had changed. A test that restates an implementation measures the
    # implementation. Compare the bonded character against a twin with no bond at all: for a THREAT
    # the bond still counts, so the two must DIFFER.
    stripped = _bonded()
    stripped["current"]["relationships"] = {}
    d_nobond = arc.assess(threat, impact=0.8, char=stripped,
                          condition=stripped["current"]["condition"])
    if d:
        got = d["temperament"].get("FEAR", 0.0)
        expected = d_nobond["temperament"].get("FEAR", 0.0)
        check("bond-was-not-excluded-for-a-threat", abs(got - expected) > 1e-9,
              "bonded FEAR=%.6f vs unbonded FEAR=%.6f — identical means the bond was "
              "wrongly excluded from a threat it had nothing to do with" % (got, expected))


def test_excluding_the_only_edge_falls_to_the_documented_default():
    """A DELIBERATE NON-CHANGE, recorded because an earlier sketch of this fix proposed otherwise.
    Dropping below 0.3 here would assert that betrayal by your only friend leaves you worse off
    than never having had one. The engine has no grounds for that."""
    print("\n[11] no surviving edge -> the no-data prior, not a lower floor")
    lone = _char()
    lone["current"]["relationships"] = {"nessa": {"trust": 0.8, "affinity": 0.9, "respect": 0.7}}
    friendless = _char()
    friendless["current"]["relationships"] = {}
    cond = lone["current"]["condition"]
    check("excluded-only-edge-equals-no-edges",
          abs(arc.derive_resilience(lone, cond, excluded="nessa")
              - arc.derive_resilience(friendless, cond)) < 1e-12,
          "%.6f vs %.6f" % (arc.derive_resilience(lone, cond, excluded="nessa"),
                            arc.derive_resilience(friendless, cond)))


def test_an_unknown_excluded_id_changes_nothing():
    """The exclusion must be a no-op when the subject is not someone the character has an edge to —
    a stranger dying is still a loss, and the character's bonds still buffer it."""
    print("\n[12] excluding a non-edge is a no-op")
    ch = _bonded()
    cond = ch["current"]["condition"]
    check("unknown-id-is-inert",
          arc.derive_resilience(ch, cond, excluded="nobody") == arc.derive_resilience(ch, cond))
    check("none-is-inert",
          arc.derive_resilience(ch, cond, excluded=None) == arc.derive_resilience(ch, cond))


def test_the_authored_baseline_survives_the_arc():
    """THE BASE MUST NOT BE EATEN. `apply` wrote the sum straight over `mean`, and `grep '["mean"] ='`
    finds exactly ONE writer repo-wide — this one. So after a character's first durable event the
    number the author chose was gone, with nowhere else it survived. Measured across the books on
    disk, the largest net drift is +0.840 on one primary, enough to have saturated against the
    clamp; what that character was written as is unrecoverable. (No cast name here — hard rule 1,
    and this docstring's first draft carried one until the private-content sweep caught it, the
    SECOND time in this gate after test_portability caught the same slip in arc.py.)

    An additive experience layer cannot be built on a fold that has already eaten the thing it
    should be added to."""
    print('\n[13] the authored baseline survives')
    ch = _char()
    ch["baseline"]["model"]["regard"]["dorn"] = 0.20
    authored = ch["baseline"]["temperament"]["CARE"]["mean"]
    c = ch
    for _ in range(3):
        c = arc.apply(c, {"temperament": {"CARE": 0.15}, "regard": {"dorn": 0.05}})
    t = c["baseline"]["temperament"]["CARE"]
    check("mean-holds-the-EFFECTIVE-value", abs(t["mean"] - (authored + 0.45)) < 1e-9, str(t))
    check("authored-is-preserved", abs(t["_authored_mean"] - authored) < 1e-9, str(t))
    check("regard-authored-is-preserved",
          abs(c["baseline"]["model"]["_authored_regard"]["dorn"] - 0.20) < 1e-9,
          str(c["baseline"]["model"]))
    check("regard-holds-the-effective-value",
          abs(c["baseline"]["model"]["regard"]["dorn"] - 0.35) < 1e-9, str(c["baseline"]["model"]))
    # a primary no diff ever touched gains no stamp — an untouched character stays byte-identical
    check("untouched-primary-is-unstamped",
          "_authored_mean" not in c["baseline"]["temperament"]["RAGE"],
          str(c["baseline"]["temperament"]["RAGE"]))
    # RE-APPLYING must not re-baseline from the moved value
    c2 = arc.apply(c, {"temperament": {"CARE": 0.10}})
    check("refold-keeps-the-ORIGINAL-authored",
          abs(c2["baseline"]["temperament"]["CARE"]["_authored_mean"] - authored) < 1e-9,
          str(c2["baseline"]["temperament"]["CARE"]))


def test_the_preserved_base_never_reaches_the_actor():
    """Tested on the REAL path, not a hand-built dict. A first version of this check handed
    `{"temperament": ...}` straight to `direct_identity` and reported a leak — measuring a path the
    engine does not use, because `_build_stable` does not carry temperament at all. The honest test
    is the prompt the actor is actually sent."""
    print('\n[14] the preserved base is not shown to the character')
    import json as _json
    from src.engine.scene import assemble
    from src.engine.prompt import build_turn_messages
    ch = _json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    world = _json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    ch = arc.apply(ch, {"temperament": {"CARE": 0.15}, "regard": {"dorn": 0.05}})
    check("the-stamp-is-on-the-sheet",
          "_authored_mean" in ch["baseline"]["temperament"]["CARE"])
    packet = assemble(ch, world, {"event": {"text": "a spider drops", "kind": "threat"}},
                      ch["current"]["affect"], ch["current"]["condition"])
    msgs = _json.dumps(build_turn_messages(packet, "a spider drops",
                                           ch["baseline"]["temperament"], {}))
    check("no-authored-key-in-the-real-prompt", "authored" not in msgs)
    check("and-model-IS-in-the-stable-prefix", "model" in packet["stable"],
          "if model were absent this test would prove nothing about _authored_regard")


def test_the_slave_case():
    """THE AUTHOR'S OWN CASE, kept as a permanent regression because it is the reason this tier was
    rewritten. `docs/character-model.md` "THE THREE LAYERS" records it verbatim:

      > "A base happy person who was a slave and beaten for years can be a very angry and hostile
      >  person today. Because their circumstances created the conditions for so many negative
      >  vectors to apply."

    Before the arc was routed through `state._DIM_TO_PRIMARY` this run moved exactly ONE primary.
    FEAR climbed to saturation and PLAY, CARE, RAGE and DISGUST sat at precisely their authored
    values after eighty durable diffs of beatings and degradation — not because the character had
    endured it well, but because `assess`'s seven hand-written branches contained no line that
    could write them. A base-happy man came out of years of slavery still base-happy, and the
    engine had no way to say otherwise. That is the defect; this is its guard.
    """
    print("")
    print("[15] the author's case: a base-happy man, beaten for years")
    ch = {"fixed": {"genotype": {"effortful_control": "low", "threat_reactivity": "high"}},
          "baseline": {"temperament": {p: {"mean": m, "variability": 0.1} for p, m in
                       (("PLAY", 0.75), ("CARE", 0.75), ("SEEKING", 0.60), ("LUST", 0.50),
                        ("FEAR", 0.20), ("RAGE", 0.20), ("PANIC_GRIEF", 0.25), ("DISGUST", 0.20))}},
          "current": {"relationships": {}, "condition": {"allostatic_load": 0.85}}}
    start = {p: ch["baseline"]["temperament"][p]["mean"] for p in PRIMARIES}
    ev = {"dimensions": {"threat": 0.75, "social_violation": 0.80, "loss": 0.15},
          "durability": "durable"}
    for _ in range(80):
        d = arc.assess(ev, impact=0.85, char=ch, condition=ch["current"]["condition"])
        if d:
            ch = arc.apply(ch, d)
    end = {p: ch["baseline"]["temperament"][p]["mean"] for p in PRIMARIES}

    check("angry", end["RAGE"] > 0.90, "RAGE %.3f -> %.3f" % (start["RAGE"], end["RAGE"]))
    check("hostile", end["DISGUST"] > 0.70, "DISGUST %.3f -> %.3f" % (start["DISGUST"], end["DISGUST"]))
    check("afraid", end["FEAR"] > 0.90, "FEAR %.3f -> %.3f" % (start["FEAR"], end["FEAR"]))
    # the one that proves it is not just "everything rises": the joy has to GO.
    check("the-joy-is-gone", end["PLAY"] < 0.20, "PLAY %.3f -> %.3f" % (start["PLAY"], end["PLAY"]))
    check("no-longer-flat", sum(1 for p in PRIMARIES if abs(end[p] - start[p]) > 1e-9) >= 6,
          "moved: %s" % {p: round(end[p] - start[p], 3) for p in PRIMARIES
                         if abs(end[p] - start[p]) > 1e-9})
    # LAW 1, at the end of the worst life the engine can price: the sheet still knows who he was.
    check("the-authored-base-survived-all-of-it",
          ch["baseline"]["temperament"]["PLAY"].get("_authored_mean") == 0.75,
          str(ch["baseline"]["temperament"]["PLAY"]))
    # and law 3 — the genotype BIASED it. A calm man with the same eighty nights is not this man.
    calm = {"fixed": {"genotype": {"effortful_control": "high", "threat_reactivity": "low"}},
            "baseline": {"temperament": {p: {"mean": m, "variability": 0.1} for p, m in
                         (("PLAY", 0.75), ("CARE", 0.75), ("SEEKING", 0.60), ("LUST", 0.50),
                          ("FEAR", 0.20), ("RAGE", 0.20), ("PANIC_GRIEF", 0.25), ("DISGUST", 0.20))}},
            "current": {"relationships": {}, "condition": {"allostatic_load": 0.85}}}
    # MEASURE BEFORE THE CEILING. At _BASE_STEP=0.326 (calibrated 2026-09-01) eighty nights
    # saturate FEAR at 1.000 for BOTH men, and a clamp cannot show a bias — the comparison would
    # report "equal" because the instrument ran out of range, not because the genotype did nothing.
    # Twenty-five nights is still a brutal life and leaves headroom for the difference to be seen.
    _BIAS_N = 25
    reactive = {"fixed": {"genotype": {"effortful_control": "low", "threat_reactivity": "high"}},
                "baseline": {"temperament": {p: {"mean": m, "variability": 0.1} for p, m in
                             (("PLAY", 0.75), ("CARE", 0.75), ("SEEKING", 0.60), ("LUST", 0.50),
                              ("FEAR", 0.20), ("RAGE", 0.20), ("PANIC_GRIEF", 0.25), ("DISGUST", 0.20))}},
                "current": {"relationships": {}, "condition": {"allostatic_load": 0.85}}}
    for _ in range(_BIAS_N):
        d = arc.assess(ev, impact=0.85, char=calm, condition=calm["current"]["condition"])
        if d:
            calm = arc.apply(calm, d)
        d = arc.assess(ev, impact=0.85, char=reactive, condition=reactive["current"]["condition"])
        if d:
            reactive = arc.apply(reactive, d)
    end = {p: reactive["baseline"]["temperament"][p]["mean"] for p in PRIMARIES}
    check("the-genotype-biased-the-durable-tier",
          calm["baseline"]["temperament"]["FEAR"]["mean"] < end["FEAR"],
          "calm FEAR %.3f vs reactive FEAR %.3f after %d nights — equal means gains never "
          "reached this tier (or both hit the clamp; see _BIAS_N)"
          % (calm["baseline"]["temperament"]["FEAR"]["mean"], end["FEAR"], _BIAS_N))


def main():
    print("test_arc.py — the Arc Engine (durable baseline change)\n")
    # DISCOVERED, NOT LISTED. This was a hand-written tuple of five names, and adding a test to the
    # file did not run it — the suite printed VERDICT: PASS with four new assertions never
    # executed. That is CLAUDE.md's seven-duplicates table gaining an eighth row: a list mirroring
    # something the module already knows. Ordered by definition line so the printed [N] headings
    # stay in reading order, which a sorted-by-name discovery would scramble.
    tests = sorted((v for k, v in globals().items()
                    if k.startswith("test_") and callable(v)),
                   key=lambda f: f.__code__.co_firstlineno)
    for t in tests:
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0



def test_base_step_is_calibrated_to_TWENTY_durable_events_per_rung():
    """THE RATE IS THE POINT, and a constant with no test drifts. Calibrated 2026-09-01 (William):
    one rung of the 0.1 ladder costs ~20 durable events. Before this, _BASE_STEP=0.07 gave +0.00108
    per severe durable affront on the maren fixture — 93 events per rung, so a three-rung arc needed
    ~280 durable events and no book contains that. Base change existed and could not be perceived.

    Twenty was chosen over five deliberately: temperament must stay a DISPOSITION rather than churn
    inside a chapter. If the ladder resolution or the pricing chain changes, this number moves and
    this test is where you notice."""
    import json
    from src.engine.state import PRIMARIES, appraise, build_profile

    ch = json.load(open("characters/maren-healer.json", encoding="utf-8"))
    prof = build_profile(ch)
    base = {p: 0.0 for p in PRIMARIES}
    tags = {"type": "affront", "dimensions": {"social_violation": 0.78}, "durability": "durable"}
    out = appraise(base, tags, prof)
    impact = sum(abs(out[p] - base[p]) for p in PRIMARIES)
    diff = arc.assess(tags, impact, ch, ch["current"]["condition"])
    step = diff["temperament"]["RAGE"]
    events = 0.1 / step
    assert 15 <= events <= 27, (
        "one rung should cost ~20 durable events; got %.0f (step %+0.5f). Five would let a "
        "personality churn inside a chapter; ninety-three is invisible across a whole book." % (events, step))


def test_a_transient_event_below_the_durable_line_still_writes_NOTHING():
    """The gate that makes the rate safe to raise. Re-measured 2026-09-01 after an earlier probe at
    exactly _DURABLE_DIM wrongly suggested `durability` was inert — at 0.60 a SECOND route fires
    ("or a dimension is genuinely severe"), which masked the flag. Below that line the flag governs."""
    import json
    from src.engine.state import PRIMARIES, appraise, build_profile

    ch = json.load(open("characters/maren-healer.json", encoding="utf-8"))
    prof = build_profile(ch)
    base = {p: 0.0 for p in PRIMARIES}
    tags = {"type": "affront", "dimensions": {"social_violation": 0.45}, "durability": "transient"}
    out = appraise(base, tags, prof)
    impact = sum(abs(out[p] - base[p]) for p in PRIMARIES)
    assert arc.assess(tags, impact, ch, ch["current"]["condition"]) is None, (
        "a transient event below _DURABLE_DIM must not reshape temperament, or ordinary friction "
        "rewrites a person at the raised step")


if __name__ == "__main__":
    sys.exit(main())
