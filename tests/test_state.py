#!/usr/bin/env python3
"""test_state.py — gate-2 proof for the State Engine (src/engine/state.py).

Asserts the contracts docs/state-engine.md names:
  - TWO-COURAGEOUS-PEOPLE divergence (same threat, different profiles -> different FEAR deltas)
  - Relevance discrimination (care_relevant moves CARE-weighted character more)
  - Decay asymmetry (FEAR returns faster than PANIC_GRIEF after identical spikes)
  - Boundedness (adversarial stream stays in [0,1], non-NaN)
  - Fail-loud (malformed inputs raise ValueError)
  - Probe pre-flight (25-turn EVENTS stream with maren-healer.json passes detector bounds)

Stdlib only, script-style. Exit 0 = all pass.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.records import PRIMARIES                           # noqa: E402
from src.engine.state import build_profile, appraise, decay       # noqa: E402

# Import the EVENTS list from the probe (read-only: coherence_probe.py is never written).
# Add tests/ to sys.path so the import works whether invoked from repo root or tests/.
sys.path.insert(0, os.path.join(REPO, "tests"))
from coherence_probe import EVENTS, detectors                     # noqa: E402

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def flat_affect(v=0.5):
    return {p: v for p in PRIMARIES}


def load_maren():
    path = os.path.join(REPO, "characters", "maren-healer.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def maren_profile():
    return build_profile(load_maren())


def empty_tags():
    return {"dimensions": {}, "durability": "transient"}


# ---------------------------------------------------------------------------
# 1. TWO-COURAGEOUS-PEOPLE — docs/state-engine.md §"This is the answer"
#    Same threat event, two profiles that differ in trait_sensitivity and value weights
#    must produce different FEAR deltas.  The divergence must be measurable (>0.02).
# ---------------------------------------------------------------------------

def _make_high_reactivity_char():
    """Character with elevated threat_reactivity + high security weight -> big FEAR spike."""
    return {
        "fixed": {
            "genotype": {
                "threat_reactivity": "elevated",   # FEAR gain 1.2
                "approach_drive": "typical",
                "affiliation_attachment": "typical",
                "anger_proneness": "typical",
                "effortful_control": "typical",
                "sensitivity": "typical",
            }
        },
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES},
            "traits": {
                "emotionality":      {"mean": 0.80, "variability": 0.10},  # high -> FEAR boost
                "agreeableness":     {"mean": 0.50, "variability": 0.10},
                "extraversion":      {"mean": 0.50, "variability": 0.10},
                "conscientiousness": {"mean": 0.50, "variability": 0.10},
                "honesty_humility":  {"mean": 0.50, "variability": 0.10},
                "openness":          {"mean": 0.50, "variability": 0.10},
            },
            "model": {
                "schwartz":           {"security": 0.90, "benevolence": 0.50,
                                       "achievement": 0.30, "self_direction": 0.30},
                "moral_foundations":  {"care_harm": 0.50, "fairness": 0.50, "loyalty": 0.50},
                "needs":              {"competence": 0.50, "relatedness": 0.50, "autonomy": 0.50},
            },
        },
    }


def _make_low_reactivity_char():
    """Character with low threat_reactivity + low security weight -> small FEAR spike."""
    return {
        "fixed": {
            "genotype": {
                "threat_reactivity": "low",        # FEAR gain 0.75
                "approach_drive": "high",
                "affiliation_attachment": "typical",
                "anger_proneness": "typical",
                "effortful_control": "typical",
                "sensitivity": "typical",
            }
        },
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES},
            "traits": {
                "emotionality":      {"mean": 0.25, "variability": 0.10},  # low -> no FEAR boost
                "agreeableness":     {"mean": 0.50, "variability": 0.10},
                "extraversion":      {"mean": 0.70, "variability": 0.10},
                "conscientiousness": {"mean": 0.50, "variability": 0.10},
                "honesty_humility":  {"mean": 0.50, "variability": 0.10},
                "openness":          {"mean": 0.50, "variability": 0.10},
            },
            "model": {
                "schwartz":           {"security": 0.20, "benevolence": 0.50,
                                       "achievement": 0.70, "self_direction": 0.80},
                "moral_foundations":  {"care_harm": 0.50, "fairness": 0.50, "loyalty": 0.50},
                "needs":              {"competence": 0.80, "relatedness": 0.40, "autonomy": 0.80},
            },
        },
    }


def test_two_courageous_people():
    """docs/state-engine.md §Answer: same threat -> different FEAR deltas from different profiles."""
    char_a = _make_high_reactivity_char()
    char_b = _make_low_reactivity_char()
    profile_a = build_profile(char_a)
    profile_b = build_profile(char_b)

    affect_start = flat_affect(0.5)
    threat_tags = {"dimensions": {"threat": 0.7}, "durability": "transient"}

    after_a = appraise(affect_start, threat_tags, profile_a)
    after_b = appraise(affect_start, threat_tags, profile_b)

    delta_a = after_a["FEAR"] - affect_start["FEAR"]
    delta_b = after_b["FEAR"] - affect_start["FEAR"]

    assert delta_a > delta_b, (
        "TWO-COURAGEOUS: expected high-reactivity > low-reactivity FEAR delta; "
        "got delta_a=%.4f delta_b=%.4f" % (delta_a, delta_b))
    assert (delta_a - delta_b) > 0.02, (
        "TWO-COURAGEOUS: divergence too small (%.4f); profiles did not differentiate" % (delta_a - delta_b))


# ---------------------------------------------------------------------------
# 2. Relevance discrimination — docs/values-and-stakes.md
#    care_relevant event moves CARE primary more for a high-care-harm weighted character
#    than for a low-care-harm weighted one.
# ---------------------------------------------------------------------------

def test_relevance_discrimination():
    """High care_harm weight -> larger CARE delta on care_relevant event."""
    high_care = {
        "fixed": {"genotype": {k: "typical" for k in
                               ["threat_reactivity","approach_drive","affiliation_attachment",
                                "anger_proneness","effortful_control","sensitivity"]}},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES},
            "traits": {t: {"mean": 0.50, "variability": 0.10} for t in
                       ["emotionality","agreeableness","extraversion",
                        "conscientiousness","honesty_humility","openness"]},
            "model": {
                "schwartz": {"benevolence": 0.90, "security": 0.50},
                "moral_foundations": {"care_harm": 0.95, "fairness": 0.50, "loyalty": 0.50},
                "needs": {"competence": 0.50, "relatedness": 0.80, "autonomy": 0.50},
            },
        },
    }
    low_care = {
        "fixed": {"genotype": {k: "typical" for k in
                               ["threat_reactivity","approach_drive","affiliation_attachment",
                                "anger_proneness","effortful_control","sensitivity"]}},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES},
            "traits": {t: {"mean": 0.50, "variability": 0.10} for t in
                       ["emotionality","agreeableness","extraversion",
                        "conscientiousness","honesty_humility","openness"]},
            "model": {
                "schwartz": {"benevolence": 0.10, "security": 0.50},
                "moral_foundations": {"care_harm": 0.10, "fairness": 0.50, "loyalty": 0.50},
                "needs": {"competence": 0.50, "relatedness": 0.20, "autonomy": 0.50},
            },
        },
    }

    profile_hc = build_profile(high_care)
    profile_lc = build_profile(low_care)
    affect = flat_affect(0.5)
    tags = {"dimensions": {"care_relevant": 0.6}, "durability": "transient"}

    after_hc = appraise(affect, tags, profile_hc)
    after_lc = appraise(affect, tags, profile_lc)

    delta_hc = after_hc["CARE"] - affect["CARE"]
    delta_lc = after_lc["CARE"] - affect["CARE"]

    assert delta_hc > delta_lc, (
        "RELEVANCE: high care_harm should move CARE more; got hc=%.4f lc=%.4f" % (delta_hc, delta_lc))
    assert (delta_hc - delta_lc) > 0.01, (
        "RELEVANCE: discrimination margin too small: %.4f" % (delta_hc - delta_lc))


# ---------------------------------------------------------------------------
# 3. Decay asymmetry — docs/state-engine.md §Decay
#    After identical spikes, FEAR must return toward resting faster than PANIC_GRIEF.
#    Concrete ratio: after 5 beats of pure decay, FEAR residual fraction < 80% of PANIC_GRIEF residual.
# ---------------------------------------------------------------------------

def test_decay_asymmetry():
    """FEAR decays markedly faster than PANIC_GRIEF (docs/state-engine.md: 'startle-FEAR fast; GRIEF slow')."""
    char   = load_maren()
    prof   = maren_profile()
    temp   = char["baseline"]["temperament"]

    # Spike both FEAR and PANIC_GRIEF equally above their resting levels.
    spike  = {p: temp[p]["mean"] for p in PRIMARIES}
    spike["FEAR"]        = min(1.0, temp["FEAR"]["mean"]        + 0.35)
    spike["PANIC_GRIEF"] = min(1.0, temp["PANIC_GRIEF"]["mean"] + 0.35)

    state = dict(spike)
    for _ in range(5):
        state = decay(state, temp, prof)

    fear_residual        = state["FEAR"]        - temp["FEAR"]["mean"]
    panic_residual       = state["PANIC_GRIEF"] - temp["PANIC_GRIEF"]["mean"]

    # FEAR residual must be < 80% of PANIC_GRIEF residual (strong asymmetry, not just "slightly faster").
    assert panic_residual > 0, "PANIC_GRIEF decayed fully in 5 beats — rates too aggressive"
    ratio = fear_residual / panic_residual
    assert ratio < 0.80, (
        "DECAY ASYMMETRY: FEAR residual %.4f is not < 80%% of PANIC_GRIEF residual %.4f (ratio=%.3f)" % (
            fear_residual, panic_residual, ratio))


# ---------------------------------------------------------------------------
# 4. Boundedness — adversarial stream keeps every primary in [0,1], non-NaN.
#    docs/state-engine.md §Appraisal step 4: Ai <- clamp(Ai + ΔAi)
# ---------------------------------------------------------------------------

def test_boundedness():
    """50 turns of all-1.0 dimensions must keep every primary in [0,1] and non-NaN."""
    char = load_maren()
    prof = maren_profile()
    temp = char["baseline"]["temperament"]

    adversarial = {"dimensions": {dim: 1.0 for dim in
                                  ["threat","loss","care_relevant","mastery","social_violation"]},
                   "durability": "durable"}

    state = {p: char["current"]["affect"][p] for p in PRIMARIES}

    for t in range(50):
        state = appraise(state, adversarial, prof)
        state = decay(state, temp, prof)
        for p in PRIMARIES:
            v = state[p]
            assert isinstance(v, float), "BOUNDS: turn %d %s is not float: %r" % (t, p, v)
            assert v == v, "BOUNDS: turn %d %s is NaN" % (t, p)            # NaN check
            assert 0.0 <= v <= 1.0, "BOUNDS: turn %d %s=%.4f out of [0,1]" % (t, p, v)


# ---------------------------------------------------------------------------
# 5. Fail-loud — malformed inputs must raise ValueError.
#    docs/state-engine.md: "Malformed input ... raises ValueError — fail loud, never coerce."
# ---------------------------------------------------------------------------

def _expect_value_error(fn, *args, label=""):
    try:
        fn(*args)
        raise AssertionError("FAIL-LOUD (%s): no ValueError raised" % label)
    except ValueError:
        pass


def test_fail_loud():
    """Malformed affect, tags, or profile must raise ValueError."""
    char = load_maren()
    prof = maren_profile()
    temp = char["baseline"]["temperament"]
    good = flat_affect(0.5)
    good_tags = {"dimensions": {"threat": 0.5}, "durability": "transient"}

    # affect out of range
    bad_affect = dict(good)
    bad_affect["FEAR"] = 1.5
    _expect_value_error(appraise, bad_affect, good_tags, prof, label="affect out-of-range")

    # affect missing a primary
    bad_missing = {p: 0.5 for p in PRIMARIES if p != "RAGE"}
    _expect_value_error(appraise, bad_missing, good_tags, prof, label="affect missing primary")

    # affect with unknown key
    bad_unknown = dict(good)
    bad_unknown["WRATH"] = 0.5
    _expect_value_error(appraise, bad_unknown, good_tags, prof, label="affect unknown key")

    # tags not a dict
    _expect_value_error(appraise, good, "not-a-dict", prof, label="tags not dict")

    # profile missing required key
    bad_prof = {k: v for k, v in prof.items() if k != "gains"}
    _expect_value_error(appraise, good, good_tags, bad_prof, label="profile missing gains")

    # decay: affect out of range
    bad_affect2 = dict(good)
    bad_affect2["CARE"] = -0.1
    _expect_value_error(decay, bad_affect2, temp, prof, label="decay affect negative")

    # decay: temperament missing primary
    bad_temp = {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES if p != "SEEKING"}
    _expect_value_error(decay, good, bad_temp, prof, label="decay temperament missing primary")

    # decay: profile missing decay_rates
    bad_prof2 = {k: v for k, v in prof.items() if k != "decay_rates"}
    _expect_value_error(decay, good, temp, bad_prof2, label="decay profile missing decay_rates")


# ---------------------------------------------------------------------------
# 6. Probe pre-flight — 25-turn EVENTS stream through maren-healer.json must pass
#    the coherence_probe.py detector bounds.
#    docs/state-engine.md §"Class B — rule coefficients": "calibrate, don't guess."
#    Thresholds (coherence_probe.py detectors()):
#      SAT_FRAC = 0.15  (no primary pinned >15% of turns at <=0.03 or >=0.97)
#      OSC      = 0.18  (mean |turn-delta| <= 0.18 per primary)
#      DRIFT    = 0.55  (final value within 0.55 of temperament mean)
# ---------------------------------------------------------------------------

def test_probe_preflicht():
    """25-turn run over EVENTS hints with maren-healer.json must pass all probe detectors."""
    char = load_maren()
    prof = build_profile(char)
    temp = char["baseline"]["temperament"]

    state = {p: char["current"]["affect"][p] for p in PRIMARIES}
    history = []

    for event in EVENTS:
        # The probe's stub path echoes event["hint"] as tags (coherence_probe.py llm_consolidate).
        tags = {"dimensions": dict(event.get("hint", {})), "durability": "transient"}
        state = appraise(state, tags, prof)
        state = decay(state, temp, prof)
        history.append(dict(state))

    flags = detectors({"affect": history, "temperament": temp}, show=False)
    assert not flags, "PROBE PRE-FLIGHT FAILED:\n" + "\n".join("  " + f for f in flags)


def _bigot_profile():
    """A character with high innate CARE gain (affiliation_attachment 'high') AND a class-level
    bigotry: low regard for the 'dorn' group, plus a low-affinity edge to one of them ('nessa')."""
    char = {
        "fixed": {"genotype": dict({k: "typical" for k in
                  ["threat_reactivity","approach_drive","anger_proneness","effortful_control","sensitivity"]},
                  affiliation_attachment="high")},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES},
            "traits": {t: {"mean": 0.50, "variability": 0.10} for t in
                       ["emotionality","agreeableness","extraversion","conscientiousness","openness"]},
            "model": {
                "schwartz": {"benevolence": 0.70, "security": 0.50},
                "moral_foundations": {"care_harm": 0.75, "fairness": 0.50, "loyalty": 0.70},
                "needs": {"competence": 0.50, "relatedness": 0.65, "autonomy": 0.50},
                "regard": {"dorn": 0.2},          # the bigotry — low regard for the class
            },
        },
        "current": {"relationships": {"nessa": {"affinity": 0.25}}},   # the arc lever, starts low
    }
    return build_profile(char)


def _care_delta(profile, tags):
    base = flat_affect(0.3)
    return appraise(base, tags, profile)["CARE"] - base["CARE"]


def test_target_aware_regard():
    """The bigot-who-feels-bad mechanism: regard for an event's SUBJECT scopes empathy DOWN,
    but the innate floor keeps it nonzero; per-entity affinity overrides class regard (the arc)."""
    prof = _bigot_profile()
    dim = {"dimensions": {"care_relevant": 0.8}, "durability": "transient"}

    d_neutral = _care_delta(prof, dim)                                            # no subject -> full
    d_dorn = _care_delta(prof, dict(dim, target_group="dorn"))              # faceless of the class
    d_nessa    = _care_delta(prof, dict(dim, target="nessa", target_group="dorn"))  # a member, affinity 0.25
    d_sister  = _care_delta(prof, dict(dim, target="pell", target_group="kin"))  # not a disregarded class
    d_human   = _care_delta(prof, dict(dim, target="some_lord", target_group="aristocrat"))  # not disregarded

    assert d_neutral > 0, "sanity: a care event should move CARE"
    assert d_dorn < d_neutral, "bigotry must scope empathy DOWN (dorn=%.4f, neutral=%.4f)" % (d_dorn, d_neutral)
    assert d_dorn > 0, "the innate floor must keep it NONZERO — feels bad he can't explain (%.4f)" % d_dorn
    assert d_nessa > d_dorn, "affinity must LIFT a member above the class floor (nessa=%.4f > dorn=%.4f)" % (d_nessa, d_dorn)
    assert d_nessa < d_neutral, "but Nessa is still scoped below full at low affinity (%.4f < %.4f)" % (d_nessa, d_neutral)
    assert abs(d_sister - d_neutral) < 1e-9, "a non-disregarded subject gets FULL empathy (%.4f vs %.4f)" % (d_sister, d_neutral)
    assert abs(d_human - d_neutral) < 1e-9, "an undisregarded group = full empathy (%.4f vs %.4f)" % (d_human, d_neutral)
    # the arc lever: raise affinity to Nessa -> more empathy for her specifically
    prof_warm = _bigot_profile()
    prof_warm["relationships"]["nessa"]["affinity"] = 0.85
    d_nessa_warm = _care_delta(prof_warm, dict(dim, target="nessa", target_group="dorn"))
    assert d_nessa_warm > d_nessa, "rising affinity must raise empathy (warm=%.4f, cold=%.4f)" % (d_nessa_warm, d_nessa)


def test_regard_leaves_targetless_unchanged():
    """No target -> factor 1.0 -> identical to pre-fix behavior (the probe relies on this)."""
    prof = _bigot_profile()
    # ISOLATE THE DIMENSION. Regard scaling is a property of a DIMENSION, not of a primitive, and
    # since dimensions became vectors a primitive can receive from several at once -- SEEKING now
    # takes an unscaled push from `mastery` AND a scaled one from `care_relevant`. Mixing them in
    # one event and asserting on the primitive tests the sum, not the rule.
    self_only = {"dimensions": {"mastery": 0.4, "threat": 0.3}, "durability": "transient"}
    a = appraise(flat_affect(0.4), self_only, prof)
    b = appraise(flat_affect(0.4), dict(self_only, target_group="dorn"), prof)
    for p in ("SEEKING", "FEAR", "RAGE", "PLAY"):
        assert abs(a[p] - b[p]) < 1e-9, "%s: self-directed dims must never be regard-scaled" % p

    other = {"dimensions": {"care_relevant": 0.5}, "durability": "transient"}
    c = appraise(flat_affect(0.4), other, prof)
    d = appraise(flat_affect(0.4), dict(other, target_group="dorn"), prof)
    assert d["CARE"] < c["CARE"], "care_relevant (other-directed) SHOULD be scaled when targeted"
    assert d["SEEKING"] < c["SEEKING"], (
        "a scaled dimension must scale its WHOLE vector: care_relevant->SEEKING is the motivation "
        "to act for them, and disregarding them lowers it too")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def test_decay_is_heritable_PER_PRIMITIVE_not_just_globally():
    """One allele, two effects. The rise was already personal; the fall was one global shape
    scaled by one number, so no character could be quick to anger and slow to forgive.

    Four things must hold, and the fourth is the compatibility contract."""
    from src.engine.state import build_profile, PRIMARIES

    def sheet(**over):
        g = {"threat_reactivity": "typical", "approach_drive": "typical",
             "anger_proneness": "typical", "affiliation_attachment": "typical",
             "sensitivity": "typical", "effortful_control": "typical"}
        g.update(over)
        return {"fixed": {"genotype": g}, "baseline": {"traits": {}, "model": {}}, "current": {}}

    typical = build_profile(sheet())["decay_rates"]
    hot     = build_profile(sheet(anger_proneness="high"))["decay_rates"]
    calm    = build_profile(sheet(threat_reactivity="low"))["decay_rates"]

    # 1. a hot-tempered character HOLDS rage longer than a typical one
    assert hot["RAGE"] > typical["RAGE"], (hot["RAGE"], typical["RAGE"])
    # 2. and a low-threat character SHEDS fear faster
    assert calm["FEAR"] < typical["FEAR"], (calm["FEAR"], typical["FEAR"])
    # 3. an allele reaches ONLY the primitives it feeds — anger_proneness must not move FEAR
    assert hot["FEAR"] == typical["FEAR"], "anger_proneness leaked into FEAR"
    assert calm["RAGE"] == typical["RAGE"], "threat_reactivity leaked into RAGE"
    # LUST, PLAY and DISGUST have no axis, so they take the species prior in BOTH directions
    for p in ("LUST", "PLAY", "DISGUST"):
        assert hot[p] == calm[p] == typical[p], "%s moved without a heritable axis" % p

    # 4. THE COMPATIBILITY CONTRACT. An all-typical genotype must reproduce the pre-change rates
    #    exactly, or every character already authored silently changed when this landed.
    from src.engine.state import _DECAY_RATE, _REG_FLOOR
    for p in PRIMARIES:
        was = max(_REG_FLOOR, min(0.98, 1.0 - (1.0 - _DECAY_RATE[p]) * 1.0))
        assert abs(typical[p] - was) < 1e-12, "%s moved for an all-typical genotype: %r vs %r" % (
            p, typical[p], was)


def test_persistence_and_regulation_COMPOSE_rather_than_cancel():
    """The two terms act on the same expression, so it is worth asserting they do not undo
    each other: a regulated person returns faster OVERALL, and within that, their heritable axes
    decide which feelings they hold longest."""
    from src.engine.state import build_profile

    def sheet(reg, anger):
        return {"fixed": {"genotype": {"threat_reactivity": "typical", "approach_drive": "typical",
                                       "anger_proneness": anger,
                                       "affiliation_attachment": "typical",
                                       "sensitivity": "typical", "effortful_control": reg}},
                "baseline": {"traits": {}, "model": {}}, "current": {}}

    # regulation still dominates the direction: high EC returns FASTER than low EC at equal anger
    hi = build_profile(sheet("high", "typical"))["decay_rates"]["RAGE"]
    lo = build_profile(sheet("low", "typical"))["decay_rates"]["RAGE"]
    assert hi < lo, "regulation stopped speeding the return (%r vs %r)" % (hi, lo)

    # and within one regulation level, anger_proneness still separates the two characters
    hi_hot = build_profile(sheet("high", "high"))["decay_rates"]["RAGE"]
    assert hi < hi_hot, "persistence was cancelled by regulation (%r vs %r)" % (hi, hi_hot)
    # the regulated hothead still returns faster than an unregulated calm one — no inversion
    assert hi_hot < lo, "persistence overwhelmed regulation (%r vs %r)" % (hi_hot, lo)



def test_persistence_reads_an_ANNOTATED_allele_the_same_way_gain_does():
    """The two effects of one allele must read that allele the SAME WAY.

    Sheets annotate an allele with a parenthetical, and `_allele` normalises with
    `.split()[0].lower()` precisely so that still reads as its word. `_persist` looked the raw
    string up directly, missed every key, and fell to the species prior — so on the reference
    fixture the GAIN fired at 1.3 and the PERSISTENCE silently did nothing.

    The suite was green because every persistence test used clean words. This one does not."""
    import json
    import os
    from src.engine.heritable import word_of as _allele_word
    from src.engine.state import _allele, _persist, build_profile

    annotated = {"affiliation_attachment": "high (anxious-leaning bond style)",
                 "anger_proneness": "low  (slow to take offence)",
                 "threat_reactivity": "TYPICAL"}
    check_pairs = [("affiliation_attachment", "CARE", "high"),
                   ("anger_proneness", "RAGE", "low"),
                   ("threat_reactivity", "FEAR", "typical")]
    for axis, primary, word in check_pairs:
        assert _allele_word(axis, annotated) == word, (axis, _allele_word(axis, annotated))
        # the load-bearing assertion: BOTH effects must recognise the annotated allele
        assert _allele(axis, annotated) != 1.0 or word == "typical", axis
        assert _persist(primary, annotated) != 1.0 or word == "typical", (
            "%s persistence fell to the species prior on an annotated %r allele" % (primary, word))

    # and on the REAL fixture, end to end through build_profile
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo, "characters", "maren-healer.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            ch = json.load(fh)
        g = ch.get("fixed", {}).get("genotype", {})
        if "(" in str(g.get("affiliation_attachment", "")):
            assert _persist("CARE", g) != 1.0, (
                "the reference fixture annotates its allele and persistence ignored it")


def test_EVERY_refusal_in_this_module_carries_a_REGISTERED_code():
    """19 prose raises in the module every committed turn passes through TWICE, and an operator
    debugging a malformed affect vector had only a sentence to grep.

    Parsed, never listed — a hand-kept list of raise sites is the duplicate CLAUDE.md tabulates
    seven failures of."""
    import ast, re
    from src.engine import codes
    with open(os.path.join(REPO, "src", "engine", "state.py"), encoding="utf-8") as fh:
        src = fh.read()
    uncoded, raised = [], set()
    for n in ast.walk(ast.parse(src)):
        if not isinstance(n, ast.Raise) or not isinstance(n.exc, ast.Call):
            continue
        a0 = n.exc.args[0] if n.exc.args else None
        if (isinstance(a0, ast.Constant) and isinstance(a0.value, str)
                and re.fullmatch(r"[A-Z][A-Z0-9]*_[A-Z0-9_]+", a0.value or "")):
            raised.add(a0.value)
        else:
            uncoded.append(n.lineno)
    assert not uncoded, "state.py raises without a code at line(s) %s" % uncoded
    assert len(raised) >= 10, "the scan found %d codes — it is not reading the module" % len(raised)
    unregistered = sorted(c for c in raised if not codes.is_registered(c))
    assert not unregistered, "state.py raises unregistered code(s) %s" % unregistered


def test_appraise_and_decay_SHARE_a_code_where_they_share_a_condition():
    """The six checks both functions perform are ONE condition each, not twelve.

    Also the falsification: if a later edit gives them separate codes, the count moves and this
    fails rather than silently doubling the namespace an operator has to know."""
    from src.engine.records import RecordError
    from src.engine.state import appraise, decay
    bad = {p: 0.5 for p in PRIMARIES}
    bad["SEEKING"] = 2.0                                   # out of [0,1], the same fault both sides
    profile = maren_profile()
    seen = set()
    for label, call in (
        ("appraise", lambda: appraise(bad, {"type": "mundane"}, profile)),
        ("decay", lambda: decay(bad, {p: {"mean": 0.5} for p in PRIMARIES}, profile)),
    ):
        try:
            call()
            raise AssertionError("%s accepted an out-of-range primary" % label)
        except RecordError as e:
            seen.add(e.code)
            assert e.code == "STATE_AFFECT_VALUE_RANGE", "%s got %r" % (label, e.code)
    assert len(seen) == 1, (
        "appraise and decay refuse the same condition with different codes %s — the namespace an "
        "operator has to know just doubled for one fault" % sorted(seen))


def main():
    # DISCOVERED, NOT LISTED. A hand-written tuple here is the duplicate CLAUDE.md tabulates, and
    # on 2026-09-01 that shape hid a determinism guard in test_scene.py for a whole run. Ordered by
    # definition line so the printed run reads in file order.
    tests = [(fn.__name__[5:], fn) for fn in
             sorted((v for k, v in globals().items()
                     if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("  PASS  %s" % name)
        except Exception as e:
            failed += 1
            print("  FAIL  %s: %s" % (name, e))
    print("\n%d/%d passed" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
