"""state.py — State Engine, Gate 2.

Three-tier emotion model: temperament (resting) / current state (event-driven) / effective (catalog).
This module implements the middle tier: appraisal + decay.

Normative contract: docs/state-engine.md.
Primaries: src/engine/records.py (single source of truth).
Baseline provenance: docs/baseline-generation.md.
Trait→sensitivity: docs/trait-theory.md + docs/baseline-generation.md §Genetics.
Relevance weighting: docs/values-and-stakes.md.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.engine.records import PRIMARIES

# ---------------------------------------------------------------------------
# Class-B constants — theory-anchored, probe-calibrated.
# Reference: docs/state-engine.md §"Where the values come from"
# ---------------------------------------------------------------------------

# ALLELE table: genotype allele string -> numeric gain multiplier.
# Source: coherence_probe.py ALLELE dict (same vocabulary; we inherit, don't invent).
# Theory: docs/baseline-generation.md §Genetics, HEXACO threat-reactivity → FEAR gain.
# Probe-calibrated start.
_ALLELE = {
    "low":      0.75,
    "typical":  1.0,
    "elevated": 1.2,
    "high":     1.3,
}

# DIM_TO_PRIMARY: appraisal dimension -> [(primary, base_push)].
# Theory: docs/state-engine.md §Appraisal module step 2; OCC/Scherer compression.
# Vocabulary kept identical to coherence_probe.py DIM_TO_PRIMARY so the probe swap is clean.
# relief pushes FEAR and PANIC_GRIEF negative (toward resting) and PLAY positive.
_DIM_TO_PRIMARY = {
    "threat":           [("FEAR",        0.45)],
    "loss":             [("PANIC_GRIEF", 0.50)],
    "care_relevant":    [("CARE",        0.40)],
    "mastery":          [("SEEKING",     0.35)],
    "social_violation": [("RAGE",        0.45)],
    "relief":           [("FEAR",       -0.40), ("PANIC_GRIEF", -0.35), ("PLAY", 0.20)],
}

# Per-primary decay retention rates (fraction of deviation from temperament kept per beat).
# Formula: Ai <- baselineI + (Ai - baselineI) * r_i   (docs/state-engine.md §Decay)
# Theory rationale (all from Panksepp + empirical affect-regulation literature):
#   FEAR / startle: fast-decaying fear response; BIS disengages rapidly once threat is resolved.
#       r = 0.72 — returns to resting in ~3 beats after a spike.
#   PANIC_GRIEF: grief lingers; loss representations persist for many beats (Bowlby attachment).
#       r = 0.90 — slow decay; 10% shed per beat.
#   RAGE: moderate; anger dissipates faster than grief but slower than startle.
#       r = 0.80
#   CARE: moderate-slow; protective CARE activation persists while the situation is legible.
#       r = 0.82
#   SEEKING: moderate; approach motivation resets once the goal is resolved or blocked.
#       r = 0.78
#   LUST: moderate; unspecified in the probe stream, set to moderate neutral.
#       r = 0.80
#   PLAY: relatively fast; playfulness is context-contingent, resets quickly.
#       r = 0.75
# All probe-calibrated start (docs/state-engine.md §"Class B — rule coefficients").
_DECAY_RATE = {
    "FEAR":        0.72,
    "PANIC_GRIEF": 0.90,
    "RAGE":        0.80,
    "CARE":        0.82,
    "SEEKING":     0.78,
    "LUST":        0.80,
    "PLAY":        0.75,
}

# Regulation (effortful_control) scaling exponent for decay speed.
# Theory: Conscientiousness / effortful control modulates how quickly affect returns to baseline
# (Gross emotion-regulation literature; docs/baseline-generation.md §Genetics effortful_control axis).
# regulation_gain = allele_value; we speed decay by multiplying (1-rate) by regulation_gain:
#   effective_rate = 1 - (1 - base_rate) * regulation_gain
# Probe-calibrated start — keeps affect within the OSC bound under a high-EC allele (1.3).
# Clipped at effective_rate >= 0.50 to prevent over-rapid collapse to baseline.
_REG_FLOOR = 0.50   # minimum effective retention rate regardless of regulation allele

# Value/drive dimension weights used for relevance computation.
# docs/values-and-stakes.md: relevance = how much the event dimension touches this character's
# weighted values/drives.  We map appraisal dimensions onto the worth menu entries in the character
# sheet (baseline.model.schwartz + baseline.model.moral_foundations + baseline.model.needs +
# baseline.drives.goals[*].priority).
# Mapping (Class-B structural, not per-character):
_DIM_VALUE_KEYS = {
    # threat -> survival need + security value
    "threat":           [("needs", "competence", 0.2), ("schwartz", "security", 0.8)],
    # loss -> relatedness need + benevolence value + care_harm moral foundation
    "loss":             [("needs", "relatedness", 0.5), ("schwartz", "benevolence", 0.3),
                         ("moral_foundations", "care_harm", 0.2)],
    # care_relevant -> care_harm moral foundation + benevolence + relatedness
    "care_relevant":    [("moral_foundations", "care_harm", 0.6),
                         ("schwartz", "benevolence", 0.3),
                         ("needs", "relatedness", 0.1)],
    # mastery -> competence need + achievement value + self-direction
    "mastery":          [("needs", "competence", 0.5), ("schwartz", "achievement", 0.3),
                         ("schwartz", "self_direction", 0.2)],
    # social_violation -> fairness + loyalty moral foundations
    "social_violation": [("moral_foundations", "fairness", 0.5),
                         ("moral_foundations", "loyalty", 0.5)],
    # relief -> security + relatedness
    "relief":           [("schwartz", "security", 0.5), ("needs", "relatedness", 0.3),
                         ("schwartz", "benevolence", 0.2)],
}

# Neutral relevance fallback when a dimension has no value-key mapping.
# Class-B: 0.5 = "average relevance, not tuned for this character."
_RELEVANCE_FALLBACK = 0.5

# Subject-regard scaling (docs/state-engine.md: relevance includes WHO the event is about).
# A character's regard for an event's SUBJECT scopes their EMPATHY response — but cannot zero it.
# _CARE_FLOOR is the innate-empathy floor: you can train someone to believe a being doesn't count,
# not to feel nothing when it bleeds. (This floor IS Brakk's "feels bad he can't explain" — an
# innate response his learned bigotry dampens but cannot delete.) Class-B, probe-calibrated start.
_CARE_FLOOR = 0.25
# Only OTHER-directed welfare dims are subject-scoped. threat/mastery/relief are self-directed
# (the character's own state), not about regard for a subject — left unscaled.
_REGARD_SCALED_DIMS = ("care_relevant", "loss")

# Trait sensitivity: per-primary gain derived from the character's HEXACO facets.
# Theory: docs/trait-theory.md, docs/baseline-generation.md §Genetics.
# Mapping (genotype axis → primary gain) is done in build_profile via _allele().
# Additionally, HEXACO trait means modulate within-person sensitivity beyond the genotype:
#   - emotionality (≈ HEXACO E facet) elevates FEAR and PANIC_GRIEF sensitivity.
#   - agreeableness reduces RAGE baseline sensitivity.
#   - conscientiousness (effortful_control proxy) is handled via _REG_FLOOR in decay.
# These are Class-B: theory-anchored slopes, probe-calibrated magnitude.
# Applied additively to genotype gain: trait_sensitivity = genotype_gain * (1 + trait_mod).
_HEXACO_SENSITIVITY_MAP = {
    # emotionality (mean) -> FEAR and PANIC_GRIEF gain bump.
    # Theory: HEXACO Emotionality = anxiety + fearfulness + sentimentality + dependence.
    # e.g. a 0.70 trait mean -> +0.14 above neutral (0.50 neutral).
    # Slope = 0.7 per unit of emotionality above 0.5.  Probe-calibrated start.
    "emotionality":     {"FEAR": 0.7, "PANIC_GRIEF": 0.6},
    # agreeableness (mean, high) -> slightly reduced RAGE sensitivity.
    # High agreeableness (low anger-prone) lowers RAGE gain.
    # Slope = -0.4 per unit above 0.5.  Probe-calibrated start.
    "agreeableness":    {"RAGE": -0.4},
    # extraversion (mean) -> PLAY and SEEKING sensitivity.
    # Higher extraversion = more responsive to approach/play stimuli.
    # Slope = 0.3 per unit above 0.5.  Probe-calibrated start.
    "extraversion":     {"PLAY": 0.3, "SEEKING": 0.3},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(x):
    """Clamp to [0, 1]. docs/state-engine.md §Appraisal step 4."""
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def _allele(axis, genotype):
    """Return numeric allele gain for one heritable axis.
    docs/baseline-generation.md §Genetics; allele vocabulary = coherence_probe.py ALLELE."""
    raw = str(genotype.get(axis, "typical")).split()[0].lower()
    return _ALLELE.get(raw, 1.0)


def _regard(profile, target, target_group):
    """Regard for an event's SUBJECT, in [0,1] (docs/state-engine.md — relevance includes who the
    event is about). The model: empathy is FULL by default; only an active DISREGARD of the
    subject's class scopes it down (mere dislike does not — you can wince for someone you dislike).
      1. If the subject's group (or entity) is in the character's regard map (the bigotry, model.regard
         {group: 0..1}) -> that class floor applies; a specific member's relationship AFFINITY can
         LIFT them above it (the ARC lever: a class held low, but ONE member come to be valued).
      2. Else -> 1.0 (no disregard for this subject -> full empathy; keeps target-less events unchanged)."""
    grp = profile.get("regard", {})
    group_regard = None
    if target_group is not None and target_group in grp:
        group_regard = float(grp[target_group])
    elif target is not None and target in grp:
        group_regard = float(grp[target])
    if group_regard is None:
        return 1.0
    rel = profile.get("relationships", {})
    if target is not None and isinstance(rel.get(target), dict) and "affinity" in rel[target]:
        group_regard = max(group_regard, float(rel[target]["affinity"]))   # affinity lifts, never lowers
    return max(0.0, min(1.0, group_regard))


def _relevance(dim, model):
    """Compute relevance of an event dimension for this character's weighted values/drives.
    docs/values-and-stakes.md: relevance = how strongly this dim touches the character's weights.
    Returns float in [0, 1].  Class-A weights (per-character model); Class-B structure.
    """
    mappings = _DIM_VALUE_KEYS.get(dim)
    if not mappings:
        return _RELEVANCE_FALLBACK
    total_weight, weighted_sum = 0.0, 0.0
    for (namespace, key, struct_weight) in mappings:
        ns = model.get(namespace, {})
        char_weight = float(ns.get(key, 0.5))   # 0.5 = neutral if missing
        total_weight += struct_weight
        weighted_sum += struct_weight * char_weight
    if total_weight < 1e-9:
        return _RELEVANCE_FALLBACK
    return weighted_sum / total_weight


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_profile(char):
    """Build the profile dict that appraise() and decay() need.

    All values DERIVED from the character sheet (Class A) or named theory constants (Class B).
    No free sliders, no runtime-conjured numbers. (docs/state-engine.md §Provenance)

    char: the full character dict (fixed + baseline + current) per character-schema.md.
    Returns: plain dict with keys:
        gains           {primary: float}  — per-primary appraise gain from genotype
        decay_rates     {primary: float}  — per-primary effective retention rate after regulation
        relevance_weights {dim: float}    — per-dimension relevance for this character
        regulation      float             — effortful_control allele value
        sensitivity     float             — global sensation-level sensitivity allele
        model           dict              — baseline.model reference (schwartz, moral_foundations, needs)
    """
    fixed = char.get("fixed", {})
    baseline = char.get("baseline", {})
    genotype = fixed.get("genotype", {})
    traits = baseline.get("traits", {})
    model = baseline.get("model", {})

    # ---- Class-A: per-character genotype gains (docs/baseline-generation.md §Genetics) ----
    gains = {p: 1.0 for p in PRIMARIES}
    gains["FEAR"]        = _allele("threat_reactivity", genotype)
    gains["SEEKING"]     = _allele("approach_drive", genotype)
    aff                  = _allele("affiliation_attachment", genotype)
    gains["CARE"]        = aff
    gains["PANIC_GRIEF"] = aff
    gains["RAGE"]        = _allele("anger_proneness", genotype)
    # LUST and PLAY not covered by the 6-axis genotype; default to 1.0 (species prior).

    # ---- Class-A: HEXACO trait modulation on top of genotype gain ----
    # Theory: docs/trait-theory.md §Whole-Trait + docs/baseline-generation.md §Genetics.
    # trait_sensitivity = genotype_gain * (1 + slope * (trait_mean - 0.5))
    for trait_name, primary_slopes in _HEXACO_SENSITIVITY_MAP.items():
        trait_mean = float(traits.get(trait_name, {}).get("mean", 0.5))
        deviation  = trait_mean - 0.5          # deviation from population neutral
        for primary, slope in primary_slopes.items():
            gains[primary] = gains[primary] * (1.0 + slope * deviation)

    # Clamp gains to [0.5, 2.5] — prevent degenerate edge values.
    for p in PRIMARIES:
        gains[p] = max(0.5, min(2.5, gains[p]))

    # ---- Class-A: regulation (effortful_control allele) ----
    regulation = _allele("effortful_control", genotype)

    # ---- Class-A: global sensitivity (sensitivity allele) ----
    sensitivity = _allele("sensitivity", genotype)

    # ---- Class-B + Class-A: per-primary effective decay rates ----
    # effective_rate = 1 - (1 - base_rate) * regulation_gain
    # High regulation -> smaller residual deviation each beat -> faster return to temperament.
    # Clipped at _REG_FLOOR to prevent over-rapid decay.
    decay_rates = {}
    for p in PRIMARIES:
        base_r = _DECAY_RATE[p]
        eff_r  = 1.0 - (1.0 - base_r) * regulation
        decay_rates[p] = max(_REG_FLOOR, min(0.98, eff_r))

    # ---- Class-A: per-dimension relevance for this character ----
    relevance_weights = {dim: _relevance(dim, model) for dim in _DIM_VALUE_KEYS}

    # ---- Class-A: subject regard — class-level disposition (the bigotry) + relationship edges ----
    current = char.get("current", {})
    regard = model.get("regard", {}) if isinstance(model.get("regard"), dict) else {}
    relationships = current.get("relationships", {}) if isinstance(current.get("relationships"), dict) else {}

    return {
        "gains":             gains,
        "decay_rates":       decay_rates,
        "relevance_weights": relevance_weights,
        "regulation":        regulation,
        "sensitivity":       sensitivity,
        "model":             model,
        "regard":            regard,
        "relationships":     relationships,
    }


def appraise(affect, tags, profile):
    """Apply one structured event to the current affect vector.

    docs/state-engine.md §Appraisal module:
      magnitude = severity(tag_dim_value) x relevance(dim, character) x trait_sensitivity(primary)
      Ai <- clamp(Ai + direction * magnitude)

    Gate-2 scope: severity factoring for wielded threats (damage-potential x hit-probability x context)
    is explicitly deferred to a later gate (state-engine.md §Appraisal step 3 note).  Here severity =
    the raw dimension magnitude emitted by the consolidation LLM (0..1).

    affect:  dict {primary: float 0..1} — current affect state (all 7 PRIMARIES required)
    tags:    dict {"dimensions": {dim: 0..1}, "durability": str, "target"?: str, "target_group"?: str}
    profile: dict returned by build_profile()

    Subject regard: when the event names a SUBJECT (tags["target"]/["target_group"]), the empathy
    dims (care_relevant, loss) are scaled by the character's regard for that subject, floored by
    _CARE_FLOOR (state-engine.md — relevance includes who the event is about). No target -> factor 1.0.

    Returns: new affect dict (pure — no mutation).
    Raises ValueError on malformed input.
    """
    # --- input validation (docs/state-engine.md: fail loud, never coerce) ---
    if not isinstance(affect, dict):
        raise ValueError("appraise: affect must be a dict, got %r" % type(affect).__name__)
    missing = [p for p in PRIMARIES if p not in affect]
    if missing:
        raise ValueError("appraise: affect missing primaries: %s" % missing)
    unknown = [k for k in affect if k not in PRIMARIES]
    if unknown:
        raise ValueError("appraise: affect has unknown keys: %s" % unknown)
    for p, v in affect.items():
        if not isinstance(v, (int, float)):
            raise ValueError("appraise: affect[%s] must be numeric, got %r" % (p, v))
        if not (0.0 <= float(v) <= 1.0):
            raise ValueError("appraise: affect[%s]=%r out of [0,1]" % (p, v))

    if not isinstance(tags, dict):
        raise ValueError("appraise: tags must be a dict, got %r" % type(tags).__name__)

    required_profile_keys = ("gains", "decay_rates", "relevance_weights", "sensitivity")
    for k in required_profile_keys:
        if k not in profile:
            raise ValueError("appraise: profile missing key %r" % k)

    dimensions = tags.get("dimensions", {})
    if not isinstance(dimensions, dict):
        raise ValueError("appraise: tags['dimensions'] must be a dict")

    gains             = profile["gains"]
    relevance_weights = profile["relevance_weights"]
    sensitivity       = profile["sensitivity"]

    # subject regard -> empathy-scaling factor (1.0 when no subject, so target-less events unchanged)
    subj_regard   = _regard(profile, tags.get("target"), tags.get("target_group"))
    regard_factor = _CARE_FLOOR + (1.0 - _CARE_FLOOR) * subj_regard

    out = {p: float(v) for p, v in affect.items()}

    for dim, mag in dimensions.items():
        if not isinstance(mag, (int, float)):
            raise ValueError("appraise: dimension %r magnitude must be numeric, got %r" % (dim, mag))
        mag = float(mag)
        rscale = regard_factor if dim in _REGARD_SCALED_DIMS else 1.0   # empathy dims only
        # Unknown dimensions are silently ignored (future-proof; new consolidation dims won't crash).
        for primary, base_push in _DIM_TO_PRIMARY.get(dim, []):
            # relevance: Class-A per-character weighting over the worth menu.
            rel = float(relevance_weights.get(dim, _RELEVANCE_FALLBACK))
            # trait_sensitivity: Class-A genotype gain for this primary.
            g = float(gains.get(primary, 1.0))
            # delta = severity x relevance x trait_sensitivity x base_push x subject-regard
            delta = mag * rel * g * sensitivity * base_push * rscale
            out[primary] = _clamp(out[primary] + delta)

    return out


def decay(affect, temperament, profile):
    """Relax each primary toward its temperament mean (resting level).

    docs/state-engine.md §Decay:
      Ai <- baselineI + (Ai - baselineI) * r_i
    where r_i is the per-primary effective retention rate (1 = no decay, 0 = instant return).

    Rates: FEAR fastest (startle); PANIC_GRIEF slowest (grief lingers); others between.
    Regulation (effortful_control) speeds return: higher EC -> lower r_i.
    (Parallel to docs/relationships.md "drift toward baseline.")

    affect:      dict {primary: float 0..1}
    temperament: dict {primary: {"mean": float, "variability": float}}
                 (= baseline.temperament from the character sheet)
    profile:     dict returned by build_profile()

    Returns: new affect dict (pure — no mutation).
    Raises ValueError on malformed input.
    """
    if not isinstance(affect, dict):
        raise ValueError("decay: affect must be a dict, got %r" % type(affect).__name__)
    missing = [p for p in PRIMARIES if p not in affect]
    if missing:
        raise ValueError("decay: affect missing primaries: %s" % missing)
    unknown = [k for k in affect if k not in PRIMARIES]
    if unknown:
        raise ValueError("decay: affect has unknown keys: %s" % unknown)
    for p, v in affect.items():
        if not isinstance(v, (int, float)):
            raise ValueError("decay: affect[%s] must be numeric" % p)
        if not (0.0 <= float(v) <= 1.0):
            raise ValueError("decay: affect[%s]=%r out of [0,1]" % (p, v))

    if not isinstance(temperament, dict):
        raise ValueError("decay: temperament must be a dict")
    for p in PRIMARIES:
        if p not in temperament:
            raise ValueError("decay: temperament missing primary %r" % p)
        t = temperament[p]
        if not isinstance(t, dict) or "mean" not in t:
            raise ValueError("decay: temperament[%r] must be a dict with 'mean'" % p)

    if not isinstance(profile, dict) or "decay_rates" not in profile:
        raise ValueError("decay: profile must be a dict with 'decay_rates'")

    decay_rates = profile["decay_rates"]

    out = {}
    for p in PRIMARIES:
        mean = float(temperament[p]["mean"])
        r    = float(decay_rates.get(p, _DECAY_RATE[p]))
        # Ai <- mean + (Ai - mean) * r
        out[p] = _clamp(mean + (float(affect[p]) - mean) * r)

    return out
