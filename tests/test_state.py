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
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.records import PATHS
from src.engine.heritable import typical as _typical
                           # noqa: E402
from src.engine.state import build_profile, appraise, decay       # noqa: E402
_TEST_BEAT_MINUTES = 30.0  # a TEST beat, minutes: the engine has no beat duration. 30 = the pre-clock WARINESS per-beat retention (0.72) against the 60-min episode half-life, so the fast-path tests keep their meaning


# Import the EVENTS list from the probe (read-only: coherence_probe.py is never written).
# Add tests/ to sys.path so the import works whether invoked from repo root or tests/.
sys.path.insert(0, os.path.join(REPO, "tests"))
from coherence_probe import EVENTS, detectors                     # noqa: E402

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def flat_affect(v=0.5):
    return {p: v for p in PATHS}


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
            "genotype": _typical(WARINESS={"hit": "elevated"})   # WARINESS gain 1.2
        },
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PATHS},
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
            "genotype": _typical(WARINESS={"hit": "low"}, STIRRING={"hit": "high"})   # WARINESS gain 0.75
        },
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PATHS},
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

    delta_a = after_a["WARINESS"] - affect_start["WARINESS"]
    delta_b = after_b["WARINESS"] - affect_start["WARINESS"]

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
        "fixed": {"genotype": _typical()},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PATHS},
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
        "fixed": {"genotype": _typical()},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PATHS},
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

    delta_hc = after_hc["GOODWILL"] - affect["GOODWILL"]
    delta_lc = after_lc["GOODWILL"] - affect["GOODWILL"]

    assert delta_hc > delta_lc, (
        "RELEVANCE: high care_harm should move CARE more; got hc=%.4f lc=%.4f" % (delta_hc, delta_lc))
    assert (delta_hc - delta_lc) > 0.01, (
        "RELEVANCE: discrimination margin too small: %.4f" % (delta_hc - delta_lc))


# ---------------------------------------------------------------------------
# 3. Decay asymmetry — docs/state-engine.md §Decay
#    After identical spikes, FEAR must return toward resting faster than PANIC_GRIEF.
#    Concrete ratio: after 10 beats of pure decay inside the disposition zone, FEAR residual fraction < 80% of PANIC_GRIEF residual.
# ---------------------------------------------------------------------------

def test_decay_asymmetry():
    """WARINESS decays markedly faster than DEFLATION (docs/state-engine.md: 'startle-FEAR fast;
    GRIEF slow'). Re-based 2026-09-19 to the redesign's form (gate emotion-tier-tidy): decay no
    longer reads a shared disposition/episode zone, so the asymmetry is now a comparison of the two
    ladders' BOTTOM RUNGS, read straight off `_rung_half_life`, not derived from a spike's zone."""
    from src.engine.state import _rung_half_life
    from src.engine import rungs as _rungs
    from src.engine.rung_blocks import BANDS as _BANDS

    # THE LADDERS THEMSELVES. Rung 1 is the DISPOSITION anchor on both paths (state.py:
    # `_rung_half_life`, k<=1 -> the disposition anchor unmultiplied) — WARINESS's is 360 minutes,
    # DEFLATION's 1800 (state._HALF_LIFE). The claim is about the anchors, before any spike.
    assert _rung_half_life("WARINESS", 1) < _rung_half_life("DEFLATION", 1), (
        "WARINESS's bottom rung must have the shorter half-life: %.1f vs %.1f minutes"
        % (_rung_half_life("WARINESS", 1), _rung_half_life("DEFLATION", 1)))

    # THE SAME SMALL SPIKE, placed inside rung 1 on EACH ladder (rungs.rung_at / the bands, never
    # zone_of — the zone apparatus is gone). A flat delta small enough to sit under the NARROWER of
    # the two rung-1 ceilings keeps the whole ten-beat run on the bottom rung's own rate for both
    # paths — exactly the trap the old zone form hit ("a 0.35 spike used to cross each path's rest
    # cap at a different height, which made the ratio a fact about the caps rather than about decay").
    ceiling = min(_BANDS["WARINESS"][0][1], _BANDS["DEFLATION"][0][1])
    spike_delta = ceiling * 0.4
    rest = {"WARINESS": 0.0, "DEFLATION": 0.0}
    spiked = {"WARINESS": spike_delta, "DEFLATION": spike_delta}
    for p in ("WARINESS", "DEFLATION"):
        assert _rungs.rung_at(p, rest[p])[0] == 1 and _rungs.rung_at(p, spiked[p])[0] == 1, (
            "the rest value and the spike must both sit on %s's bottom rung" % p)

    temp  = {p: {"mean": rest.get(p, 0.0)} for p in PATHS}
    state = {p: spiked.get(p, 0.0) for p in PATHS}
    prof  = {"hold": {p: 1.0 for p in PATHS}}      # the ladders' own rates, undamped by genotype

    for _ in range(10):                       # a settled state is judged over a longer span
        state = decay(state, temp, prof, elapsed=_TEST_BEAT_MINUTES)

    wariness_residual  = state["WARINESS"]  - temp["WARINESS"]["mean"]
    deflation_residual = state["DEFLATION"] - temp["DEFLATION"]["mean"]

    assert deflation_residual > 0, "DEFLATION decayed fully in ten beats — rates too aggressive"
    assert wariness_residual < deflation_residual, (
        "DECAY ASYMMETRY: WARINESS residual %.4f is not smaller than DEFLATION residual %.4f" % (
            wariness_residual, deflation_residual))


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

    state = {p: char["current"]["affect"][p] for p in PATHS}

    for t in range(50):
        state = appraise(state, adversarial, prof)
        state = decay(state, temp, prof, elapsed=_TEST_BEAT_MINUTES)
        for p in PATHS:
            v = state[p]
            assert isinstance(v, float), "BOUNDS: turn %d %s is not float: %r" % (t, p, v)
            assert v == v, "BOUNDS: turn %d %s is NaN" % (t, p)            # NaN check
            assert 0.0 <= v <= 1.0, "BOUNDS: turn %d %s=%.4f out of [0,1]" % (t, p, v)


# ---------------------------------------------------------------------------
# 5. Fail-loud — malformed inputs must raise ValueError.
#    docs/state-engine.md: "Malformed input ... raises ValueError — fail loud, never coerce."
# ---------------------------------------------------------------------------

def _expect_value_error(fn, *args, label="", **kw):
    try:
        fn(*args, **kw)
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
    bad_affect["WARINESS"] = 1.5
    _expect_value_error(appraise, bad_affect, good_tags, prof, label="affect out-of-range")

    # affect missing a primary
    bad_missing = {p: 0.5 for p in PATHS if p != "DISPLEASURE"}
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
    bad_affect2["GOODWILL"] = -0.1
    _expect_value_error(decay, bad_affect2, temp, prof, label="decay affect negative")

    # decay: temperament missing primary
    bad_temp = {p: {"mean": 0.5, "variability": 0.1} for p in PATHS if p != "STIRRING"}
    _expect_value_error(decay, good, bad_temp, prof, label="decay temperament missing primary", elapsed=1.0)

    # decay: profile missing hold
    bad_prof2 = {k: v for k, v in prof.items() if k != "hold"}
    _expect_value_error(decay, good, temp, bad_prof2, label="decay profile missing hold", elapsed=1.0)


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

    state = {p: char["current"]["affect"][p] for p in PATHS}
    history = []

    for event in EVENTS:
        # The probe's stub path echoes event["hint"] as tags (coherence_probe.py llm_consolidate).
        tags = {"dimensions": dict(event.get("hint", {})), "durability": "transient"}
        state = appraise(state, tags, prof)
        state = decay(state, temp, prof, elapsed=1440.0)   # the probe's events are life episodes a DAY apart (coherence_probe.py:390), not exchanges
        history.append(dict(state))

    flags = detectors({"affect": history, "temperament": temp}, show=False)
    assert not flags, "PROBE PRE-FLIGHT FAILED:\n" + "\n".join("  " + f for f in flags)


def _ringer_profile():
    """A tower bell-ringer: high innate CARE gain (GOODWILL hit 'high') AND a low regard for a whole
    group, the handbell ringers ('handbells'), plus a low-affinity edge to one of them ('mungo')."""
    char = {
        "fixed": {"genotype": _typical(GOODWILL={"hit": "high"}, STIRRING={"hit": "elevated"})},
        "baseline": {
            "temperament": {p: {"mean": 0.5, "variability": 0.1} for p in PATHS},
            "traits": {t: {"mean": 0.50, "variability": 0.10} for t in
                       ["emotionality","agreeableness","extraversion","conscientiousness","openness"]},
            "model": {
                "schwartz": {"benevolence": 0.80, "security": 0.35},
                "moral_foundations": {"care_harm": 0.85, "fairness": 0.45, "loyalty": 0.60},
                "needs": {"competence": 0.55, "relatedness": 0.60, "autonomy": 0.75},
                "regard": {"handbells": 0.1},     # she rates the handbell ringers low — "not real ringing"
            },
        },
        "current": {"relationships": {"mungo": {"affinity": 0.4}}},    # one member, a per-entity edge
    }
    return build_profile(char)


def _care_delta(profile, tags):
    base = flat_affect(0.3)
    return appraise(base, tags, profile)["GOODWILL"] - base["GOODWILL"]


def test_target_aware_regard():
    """Care that outlives a low regard: regard for an event's SUBJECT's group scopes empathy DOWN,
    but the innate floor keeps it nonzero; per-entity affinity lifts one member above the group."""
    prof = _ringer_profile()
    dim = {"dimensions": {"care_relevant": 0.8}, "durability": "transient"}

    d_neutral = _care_delta(prof, dim)                                            # no subject -> full
    d_hand    = _care_delta(prof, dict(dim, target_group="handbells"))            # faceless of the group
    d_mungo   = _care_delta(prof, dict(dim, target="mungo", target_group="handbells"))  # a member, affinity 0.4
    d_band    = _care_delta(prof, dict(dim, target="lettice", target_group="tower"))  # her own band
    d_other   = _care_delta(prof, dict(dim, target="tour_guide", target_group="visitors"))  # not disregarded

    assert d_neutral > 0, "sanity: a care event should move CARE"
    assert d_hand < d_neutral, "low regard must scope empathy DOWN (handbells=%.4f, neutral=%.4f)" % (d_hand, d_neutral)
    assert d_hand > 0, "the innate floor must keep it NONZERO — a group held low still registers (%.4f)" % d_hand
    assert d_mungo > d_hand, "affinity must LIFT a member above the group floor (mungo=%.4f > handbells=%.4f)" % (d_mungo, d_hand)
    assert d_mungo < d_neutral, "but a member is still scoped below full at low affinity (%.4f < %.4f)" % (d_mungo, d_neutral)
    assert abs(d_band - d_neutral) < 1e-9, "a non-disregarded subject gets FULL empathy (%.4f vs %.4f)" % (d_band, d_neutral)
    assert abs(d_other - d_neutral) < 1e-9, "an undisregarded group = full empathy (%.4f vs %.4f)" % (d_other, d_neutral)
    # affinity is per entity: raise it for one member -> more empathy for that member alone
    prof_warm = _ringer_profile()
    prof_warm["relationships"]["mungo"]["affinity"] = 0.9
    d_mungo_warm = _care_delta(prof_warm, dict(dim, target="mungo", target_group="handbells"))
    assert d_mungo_warm > d_mungo, "rising affinity must raise empathy (warm=%.4f, cold=%.4f)" % (d_mungo_warm, d_mungo)


def test_regard_leaves_targetless_unchanged():
    """No target -> factor 1.0 -> identical to pre-fix behavior (the probe relies on this)."""
    prof = _ringer_profile()
    # ISOLATE THE DIMENSION. Regard scaling is a property of a DIMENSION, not of a primitive, and
    # since dimensions became vectors a primitive can receive from several at once -- SEEKING now
    # takes an unscaled push from `mastery` AND a scaled one from `care_relevant`. Mixing them in
    # one event and asserting on the primitive tests the sum, not the rule.
    self_only = {"dimensions": {"mastery": 0.4, "threat": 0.3}, "durability": "transient"}
    a = appraise(flat_affect(0.4), self_only, prof)
    b = appraise(flat_affect(0.4), dict(self_only, target_group="handbells"), prof)
    # WAS a four-name subset. Every path is checked now: if neither dimension is regard-scaled
    # then NO path may differ, which is the stronger form of the same rule.
    for p in PATHS:
        assert abs(a[p] - b[p]) < 1e-9, "%s: self-directed dims must never be regard-scaled" % p

    other = {"dimensions": {"care_relevant": 0.5}, "durability": "transient"}
    c = appraise(flat_affect(0.4), other, prof)
    d = appraise(flat_affect(0.4), dict(other, target_group="handbells"), prof)
    assert d["GOODWILL"] < c["GOODWILL"], "care_relevant (other-directed) SHOULD be scaled when targeted"
    assert d["STIRRING"] < c["STIRRING"], (
        "a scaled dimension must scale its WHOLE vector: care_relevant->SEEKING is the motivation "
        "to act for them, and disregarding them lowers it too")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def test_every_cell_reads_an_ANNOTATED_word_the_same_way():
    """Every cell — the genotype's hit and hold, and the authored rest word — must read an
    annotated word the SAME WAY.

    Sheets annotate a word with a parenthetical — `"high (anxious-leaning bond style)"` — and
    `heritable.word` is THE one parse. On 2026-09-01 a fifth reader that did not use it made the
    persistence half of the genotype a silent no-op on the repo's own reference fixture; this
    test exists so the three-cell rebuild cannot repeat that on any cell."""
    import json
    import os
    from src.engine import heritable as _her

    g = {"GOODWILL":    {"hit": "high (anxious-leaning bond style)", "hold": "long  (does not let go)"},
         "DISPLEASURE": {"hit": "LOW  (slow to take offence)"},
         "WARINESS":    {"hit": "TYPICAL"}}
    t = {"GOODWILL":    {"rest": "raised (warm before it is earned)"}}
    assert _her.rest_rung("GOODWILL", t) == 3, _her.rest_rung("GOODWILL", t)
    assert _her.hit("GOODWILL", g) == _her.GAIN["high"], _her.hit("GOODWILL", g)
    assert _her.hold("GOODWILL", g) == _her.PERSIST["long"], _her.hold("GOODWILL", g)
    assert _her.hit("DISPLEASURE", g) == _her.GAIN["low"]
    assert _her.hit("WARINESS", g) == 1.0 and _her.hold("WARINESS", g) == 1.0
    # a NUMBER is honoured as written, on every cell
    n = {"SELF-REGARD": {"hit": 1.05, "hold": 0.92}}
    assert _her.rest_mean("SELF-REGARD", {"SELF-REGARD": {"rest": 0.31}}) == 0.31 and _her.hit("SELF-REGARD", n) == 1.05
    from src.engine.state import half_life_minutes as _hl
    assert abs(_hl("SELF-REGARD", 0.31, _her.hold("SELF-REGARD", n)) / _hl("SELF-REGARD", 0.31, 1.0) - 0.92) < 1e-12
    # the retired shape is REFUSED, not read as typical
    try:
        _her.hit("WARINESS", {"threat_reactivity": "high"})      # the retired shape, refused
        raise AssertionError("a primitive-era genotype must be refused")
    except Exception as exc:
        assert "GENOTYPE_OLD_AXES" in str(exc) or type(exc).__name__ == "RecordError", exc

    # and on the REAL fixture, end to end through build_profile
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo, "characters", "maren-healer.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            ch = json.load(fh)
        from src.engine.state import build_profile
        prof = build_profile(ch)
        g = ch["fixed"]["genotype"]
        assert "(" in str(g["GOODWILL"]["hit"]), "the reference fixture should annotate a cell"
        assert prof["gains"]["GOODWILL"] == _her.GAIN["high"], prof["gains"]["GOODWILL"]
        assert prof["hold"]["GOODWILL"] == _her.PERSIST["long"], "the annotated hold was ignored"


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
    bad = {p: 0.5 for p in PATHS}
    bad["STIRRING"] = 2.0                                   # out of [0,1], the same fault both sides
    profile = maren_profile()
    seen = set()
    for label, call in (
        ("appraise", lambda: appraise(bad, {"type": "mundane"}, profile)),
        ("decay", lambda: decay(bad, {p: {"mean": 0.5} for p in PATHS}, profile, elapsed=1.0)),
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



def test_decay_is_on_the_one_law_and_has_a_clock():
    """2026-09-09. `decay_law.py` exists because the engine held six hand-written copies of
    `rest + (value - rest) * retention ** elapsed`, and its header LISTS this tier among them --
    while state.py imported nothing from it. Green the whole time, because the arithmetic agreed by
    luck rather than by wiring.

    The clock is the real repair. Every other decay tier takes `elapsed` -- bonds.drift,
    toward.erode, wound.erode, arc.erode, world_appraisal.cool -- and this one did not, so a beat
    spanning a heartbeat and a beat spanning a week aged a feeling identically.
    docs/character-model.md says the tiers differ in "what they rest at, how fast, and ON WHICH
    CLOCK"; emotion had two of the three.
    """
    print(chr(10) + "[N] DECAY: on the one law, and on a clock")
    import inspect
    from src.engine import state as _st

    # per-rung stepping (gate 2) moved the law call into decay_over, which decay calls per path.
    src = inspect.getsource(_st.decay) + inspect.getsource(_st.decay_over)
    assert "relax(" in src, "the decay tier (decay -> decay_over) must CALL the one law, not re-spell it"
    assert "elapsed" in inspect.signature(_st.decay).parameters, "decay must take a clock"

    prof = _ringer_profile()
    temp = {p: {"mean": 0.20, "variability": 0.1} for p in PATHS}
    aff = {p: 0.60 for p in PATHS}

    # SINCE 2026-09-10 THERE IS NO DEFAULT: elapsed is MINUTES on the one clock and a caller that
    # does not know how much time passed says 0, never nothing (tests/test_clock.py owns the rest).
    try:
        _st.decay(dict(aff), temp, prof)
        raise AssertionError("decay without elapsed must be refused")
    except Exception as exc:
        assert "STATE_ELAPSED_MISSING" in str(exc), exc

    # decay_law promises two identities; asserted HERE too because this tier clamps and it does not
    zero = _st.decay(dict(aff), temp, prof, elapsed=0.0)
    assert all(abs(zero[p] - 0.60) < 1e-12 for p in PATHS), (
        "a zero-length tick must not move a feeling: %r" % zero["DISPLEASURE"])
    at_rest = _st.decay({p: 0.20 for p in PATHS}, temp, prof, elapsed=9.0)
    assert all(abs(at_rest[p] - 0.20) < 1e-12 for p in PATHS), (
        "a value already at rest must never walk, however long the tick")

    one, two, five = (_st.decay(dict(aff), temp, prof, elapsed=e) for e in (60.0, 120.0, 300.0))
    assert one["DISPLEASURE"] > two["DISPLEASURE"] > five["DISPLEASURE"] > 0.20, (
        "more declared time must decay further, and never past rest: %.4f %.4f %.4f"
        % (one["DISPLEASURE"], two["DISPLEASURE"], five["DISPLEASURE"]))

    try:
        _st.decay(dict(aff), temp, prof, elapsed="a while")
        raise AssertionError("a non-numeric elapsed must be refused, not coerced")
    except Exception as exc:
        assert type(exc).__name__ == "RecordError", exc
    print("       relax() called; elapsed honoured; default unchanged")


def test_decay_is_the_global_half_life_bent_by_the_HOLD_cell():
    """REVERSES `test_decay_was_heritable_and_is_now_FLAT` (2026-09-09), by owner ruling 2026-09-10:
    the genotype is "the starting vectors, then the allele, then the decay" — three cells per
    path, drawn independently. The 2026-09-09 argument that retention is the wrong place for a
    per-character knob (it enters the settling point hyperbolically) stands recorded in
    `heritable.py`; the owner put hold in the genotype anyway, and PERSIST's narrow spread is the
    concession.

    THE BALANCE RULE, which is what this test actually pins: hold multiplies the path's HALF-LIFE
    (`state._HALF_LIFE`, minutes, per zone), so the same word stretches every path and zone by
    the same ratio and a re-authored half-life table never touches the person term."""
    print(chr(10) + "[N] DECAY = the path's half-life bent by the HOLD cell, in minutes")
    from src.engine.state import build_profile, half_life_minutes, _HALF_LIFE
    from src.engine import heritable as _her

    typ = {"fixed": {"genotype": _typical()}, "baseline": {}, "current": {}}
    assert build_profile(typ)["hold"] == {p: 1.0 for p in PATHS}, "a typical hold must be the identity"

    lasting = {"fixed": {"genotype": _typical(**{p: {"hold": "lasting"} for p in PATHS})}, "baseline": {}, "current": {}}
    hold = build_profile(lasting)["hold"]
    for p in PATHS:
        for v in (0.02, 0.95):                                  # a disposition-zone and an episode-zone value
            ratio = half_life_minutes(p, v, hold[p]) / half_life_minutes(p, v, 1.0)
            assert abs(ratio - _her.PERSIST["lasting"]) < 1e-9, (p, v, ratio)

    # two different genotypes decay differently again, and the resting mean is the authored
    # rest WORD's rung midpoint (design beside the voice), not a genotype cell
    g = []
    for f in ("ren-traveler", "maren-healer"):
        ch = json.load(io.open("characters/%s.json" % f, encoding="utf-8"))
        prof = build_profile(ch)
        temp = ch["baseline"]["temperament"]
        assert "rest" not in ch["fixed"]["genotype"]["WARINESS"], "the fixture still carries rest in the genotype"
        assert temp["WARINESS"]["mean"] == _her.rest_mean("WARINESS", temp), (temp["WARINESS"], _her.rest_mean("WARINESS", temp))
        g.append(prof)
    assert g[0]["hold"]["WARINESS"] != g[1]["hold"]["WARINESS"], "ren holds brief, maren long"
    assert g[0]["gains"]["WARINESS"] != g[1]["gains"]["WARINESS"]
    print("       WARINESS hold %.2f vs %.2f; gain %.2f vs %.2f; episode half-life %d min" % (
        g[0]["hold"]["WARINESS"], g[1]["hold"]["WARINESS"],
        g[0]["gains"]["WARINESS"], g[1]["gains"]["WARINESS"], _HALF_LIFE["WARINESS"][0]))


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
