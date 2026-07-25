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
    bigotry: low regard for the 'fenmark' group, plus a low-affinity edge to one of them ('kestra')."""
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
                "regard": {"fenmark": 0.2},          # the bigotry — low regard for the class
            },
        },
        "current": {"relationships": {"kestra": {"affinity": 0.25}}},   # the arc lever, starts low
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
    d_fenmark = _care_delta(prof, dict(dim, target_group="fenmark"))              # faceless of the class
    d_kestra    = _care_delta(prof, dict(dim, target="kestra", target_group="fenmark"))  # a member, affinity 0.25
    d_sister  = _care_delta(prof, dict(dim, target="wynn", target_group="kin"))  # not a disregarded class
    d_human   = _care_delta(prof, dict(dim, target="some_lord", target_group="aristocrat"))  # not disregarded

    assert d_neutral > 0, "sanity: a care event should move CARE"
    assert d_fenmark < d_neutral, "bigotry must scope empathy DOWN (fenmark=%.4f, neutral=%.4f)" % (d_fenmark, d_neutral)
    assert d_fenmark > 0, "the innate floor must keep it NONZERO — feels bad he can't explain (%.4f)" % d_fenmark
    assert d_kestra > d_fenmark, "affinity must LIFT a member above the class floor (kestra=%.4f > fenmark=%.4f)" % (d_kestra, d_fenmark)
    assert d_kestra < d_neutral, "but Kestra is still scoped below full at low affinity (%.4f < %.4f)" % (d_kestra, d_neutral)
    assert abs(d_sister - d_neutral) < 1e-9, "a non-disregarded subject gets FULL empathy (%.4f vs %.4f)" % (d_sister, d_neutral)
    assert abs(d_human - d_neutral) < 1e-9, "an undisregarded group = full empathy (%.4f vs %.4f)" % (d_human, d_neutral)
    # the arc lever: raise affinity to Kestra -> more empathy for her specifically
    prof_warm = _bigot_profile()
    prof_warm["relationships"]["kestra"]["affinity"] = 0.85
    d_kestra_warm = _care_delta(prof_warm, dict(dim, target="kestra", target_group="fenmark"))
    assert d_kestra_warm > d_kestra, "rising affinity must raise empathy (warm=%.4f, cold=%.4f)" % (d_kestra_warm, d_kestra)


def test_regard_leaves_targetless_unchanged():
    """No target -> factor 1.0 -> identical to pre-fix behavior (the probe relies on this)."""
    prof = _bigot_profile()
    dim = {"dimensions": {"care_relevant": 0.5, "mastery": 0.4, "threat": 0.3}, "durability": "transient"}
    a = appraise(flat_affect(0.4), dim, prof)
    # mastery/threat are self-directed — never regard-scaled even when a target IS present
    b = appraise(flat_affect(0.4), dict(dim, target_group="fenmark"), prof)
    assert abs(a["SEEKING"] - b["SEEKING"]) < 1e-9, "mastery (self-directed) must not be regard-scaled"
    assert abs(a["FEAR"] - b["FEAR"]) < 1e-9, "threat (self-directed) must not be regard-scaled"
    assert b["CARE"] < a["CARE"], "care_relevant (other-directed) SHOULD be scaled when targeted"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    tests = [
        ("two_courageous_people",    test_two_courageous_people),
        ("relevance_discrimination", test_relevance_discrimination),
        ("decay_asymmetry",          test_decay_asymmetry),
        ("boundedness",              test_boundedness),
        ("target_aware_regard",      test_target_aware_regard),
        ("regard_targetless_unchanged", test_regard_leaves_targetless_unchanged),
        ("fail_loud",                test_fail_loud),
        ("probe_preflight",          test_probe_preflicht),
    ]
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
