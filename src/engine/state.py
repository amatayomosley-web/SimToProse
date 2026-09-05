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

from src.engine import connection                    # the investment multiplier (docs/character-model.md)
from src.engine import heritable as _her             # THE one reading of the genotype
from src.engine.records import PRIMARIES, admits_role, RecordError  # rule 6's bad-input type

# ---------------------------------------------------------------------------
# Class-B constants — theory-anchored, probe-calibrated.
# Reference: docs/state-engine.md §"Where the values come from"
# ---------------------------------------------------------------------------

# ALLELE table: genotype allele string -> numeric gain multiplier.
# Source: coherence_probe.py ALLELE dict (same vocabulary; we inherit, don't invent).
# Theory: docs/baseline-generation.md §Genetics, HEXACO threat-reactivity → FEAR gain.
# Probe-calibrated start.
_ALLELE = _her.GAIN                # re-exported: arc.py and lint_book.py import it from here

# DIM_TO_PRIMARY: appraisal dimension -> [(primary, base_push)].
# Theory: docs/state-engine.md §Appraisal module step 2; OCC/Scherer compression.
# Vocabulary kept identical to coherence_probe.py DIM_TO_PRIMARY so the probe swap is clean.
# relief pushes FEAR and PANIC_GRIEF negative (toward resting) and PLAY positive.
# EVERY DIMENSION IS A VECTOR, not a single push. An event class does several things at once and
# saying it does one is the same flattening that makes a trait word a tag: "threat" that only
# raises fear cannot express a man who goes quiet and watchful, because nothing but fear moved.
# `relief` was already authored this way and was the only one -- the shape was present and
# unapplied.
#
# THE PRIMARY PUSH IS UNCHANGED FROM THE SINGLE-PUSH VERSION in every case. Only secondaries were
# added, so whatever calibration the primaries carry survives and any behavioural difference is
# attributable to the secondaries alone.
#
# The secondaries are theory, not taste, from the same Panksepp/OCC sources as the primaries:
#   PLAY collapses under threat and loss   -- play requires safety and is the first behaviour to go
#   SEEKING rises under threat             -- vigilance and orienting; the BIS sharpens attention
#   SEEKING falls under loss               -- the anhedonic signature of grief: nothing to pursue
#   RAGE rises slightly under threat       -- fight is a branch of the defensive repertoire
#   FEAR falls under mastery               -- competence lowers the threat appraisal itself
_DIM_TO_PRIMARY = {
    "threat":           [("FEAR",         0.45), ("SEEKING",      0.12),
                         ("RAGE",         0.10), ("PLAY",        -0.22)],
    "loss":             [("PANIC_GRIEF",  0.50), ("SEEKING",     -0.18),
                         ("PLAY",        -0.20)],
    "care_relevant":    [("CARE",         0.40), ("SEEKING",      0.10)],
    "mastery":          [("SEEKING",      0.35), ("PLAY",         0.15),
                         ("FEAR",        -0.10)],
    # DISGUST, wired 2026-08-22 when it joined PRIMARIES. It is reached from the dimensions that
    # already exist rather than from a new one:
    #   social_violation -> CONTEMPT, which is the social-violation response that is not anger.
    #     Weighted below RAGE: most violations make people angry first. What separates the two is
    #     that rage wants redress and contempt has stopped asking for any, so a character whose
    #     DISGUST outruns their RAGE is the one who writes the other person off.
    #   threat -> the physical recoil. Small: revulsion is a minor note in ordinary danger and the
    #     catalog is where a character's particular foulness lives (a percept row multiplying
    #     DISGUST is how "he cannot stand the smell of the tannery" becomes arithmetic).
    # No new appraisal DIMENSION was added. That is a separable decision needing its own CATALOG
    # entry, relevance mapping and actor-facing name.
    "social_violation": [("RAGE",         0.45), ("DISGUST",      0.28), ("PLAY", -0.15)],
    "relief":           [("FEAR",        -0.40), ("PANIC_GRIEF", -0.35), ("PLAY", 0.20)],
    # ATTRACTION — the seventh dimension, added 2026-08-22 so that LUST is reachable at all.
    # Before it, LUST had a temperament mean, a decay rate, a genotype default and four direction
    # phrases, and NOTHING that could move it: a character sheet setting a high LUST mean produced
    # a primitive that could only ever sit at rest. `emotion-basis.md` flags that as BLOCKING and
    # holds the whole basis to the rule — fix reachability before changing basis size.
    #
    # It needed its OWN dimension. The other six are threat / loss / care_relevant / mastery /
    # social_violation / relief, and none of them is about desire; reaching LUST from care_relevant
    # would make every act of tenderness push attraction, which is the exact conflation a separate
    # primitive exists to prevent.
    #
    # SEEKING rides along because desire is an approach system before it is anything else, and PLAY
    # lightly because being drawn to someone loosens a room. FEAR is untouched: whether desire is
    # frightening is a CATALOG question about this person, not a species-level push.
    "attraction":       [("LUST",         0.45), ("SEEKING",      0.18), ("PLAY", 0.10)],
}
_DIM_TO_PRIMARY["threat"].append(("DISGUST", 0.08))

# Fail at IMPORT, not at the first event that happens to use the dimension. A primitive named here
# that PRIMARIES does not carry would KeyError deep inside appraise on some later turn, which is a
# runtime surprise standing in for an authoring error.
for _dim, _pushes in _DIM_TO_PRIMARY.items():
    for _p, _w in _pushes:
        if _p not in PRIMARIES:
            raise RecordError("STATE_DIM_TO_PRIMARY_UNKNOWN_PRIMITIVE", "_DIM_TO_PRIMARY[%r] pushes %r, which is not a primitive. Add it to "
                             "PRIMARIES or remove the push - it cannot be silently skipped."
                             % (_dim, _p))

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
    # DISGUST: slow. Revulsion outlasts the thing that caused it — you do not want the food again
    # once it has made you ill, and contempt for a person is the most durable of the social
    # responses. Set just below PANIC_GRIEF, which is the slowest of the seven incumbents.
    "DISGUST":     0.88,
}

# A primitive is BACK AT REST when it sits within this of ITS OWN temperament mean. Kept in step
# with direction._DEV_THRESH, which is the same "not asking for attention" judgement.
#
# NOT also gated on the quiet band, which was the first version and was wrong: a character whose
# resting FEAR is 0.62 is never inside the 0.25 quiet band, so her binds would have persisted
# forever while a calm character's cleared normally. Absolute level is disposition; DEVIATION from
# your own mean is the response. Only a response can be about something — which is rule 5's own
# reasoning ("temperament never binds; dispositions do not point") applied consistently.
_AT_REST = 0.15

# Regulation (effortful_control) scaling exponent for decay speed.
# Theory: Conscientiousness / effortful control modulates how quickly affect returns to baseline
# (Gross emotion-regulation literature; docs/baseline-generation.md §Genetics effortful_control axis).
# regulation_gain = allele_value; we speed decay by multiplying (1-rate) by regulation_gain:
#   effective_rate = 1 - (1 - base_rate) * regulation_gain
# Probe-calibrated start — keeps affect within the OSC bound under a high-EC allele (1.3).
# Clipped at effective_rate >= 0.50 to prevent over-rapid collapse to baseline.
_REG_FLOOR = 0.50   # minimum effective retention rate regardless of regulation allele

# PERSISTENCE and the allele vocabulary now live in `heritable.py` — one reading of the genotype
# for every consumer. Four places parsed it independently and a fifth was added that did not,
# which made persistence a silent no-op on any annotated sheet. See that file for the why.


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
    # attraction -> hedonism + relatedness, damped by a sanctity weight. The moral foundation is
    # what makes an ascetic and a libertine appraise the identical moment differently, which is the
    # whole reason relevance is per-character; it enters NEGATIVELY nowhere, because _relevance
    # averages weights rather than summing signed terms — a high-sanctity character simply gets a
    # low hedonism weight authored alongside it, and the row stays honest about what it reads.
    "attraction":       [("schwartz", "hedonism", 0.6), ("needs", "relatedness", 0.3),
                         ("schwartz", "stimulation", 0.1)],
}

# Neutral relevance fallback when a dimension has no value-key mapping.
# Class-B: 0.5 = "average relevance, not tuned for this character."
_RELEVANCE_FALLBACK = 0.5

# Subject-regard scaling (docs/state-engine.md: relevance includes WHO the event is about).
# A character's regard for an event's SUBJECT scopes their EMPATHY response — but cannot zero it.
# _CARE_FLOOR is the innate-empathy floor: you can train someone to believe a being doesn't count,
# not to feel nothing when it bleeds. (This floor IS the "feels bad he can't explain" response — an
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
    """Numeric allele GAIN for one heritable axis. One reading, in `heritable.py`."""
    return _her.gain(axis, genotype)


def _persist(primary, genotype):
    """How long this character holds this primitive — the same allele, its other effect."""
    return _her.persist(primary, genotype)


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
    #
    # PER-PRIMITIVE PERSISTENCE divides the regulation term: an allele that makes a primitive
    # linger shrinks how much regulation sheds each beat, so the two compose rather than compete.
    # A regulated person returns faster overall, and WITHIN that, their heritable axes decide which
    # feelings they hold longest. An all-typical genotype leaves persist at 1.0 and reproduces the
    # pre-2026-09-01 rates exactly, so nothing already authored moves.
    decay_rates = {}
    for p in PRIMARIES:
        base_r = _DECAY_RATE[p]
        eff_r  = 1.0 - (1.0 - base_r) * regulation / _persist(p, genotype)
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


def appraise(affect, tags, profile, targets=None):
    """Apply one structured event to the current affect vector.

    docs/state-engine.md §Appraisal module:
      magnitude = severity(tag_dim_value) x relevance(dim, character) x trait_sensitivity(primary)
      Ai <- clamp(Ai + direction * magnitude)

    Gate-2 scope: severity factoring for wielded threats (damage-potential x hit-probability x context)
    is explicitly deferred to a later gate (state-engine.md §Appraisal step 3 note).  Here severity =
    the raw dimension magnitude emitted by the consolidation LLM (0..1).

    affect:  dict {primary: float 0..1} — current affect state (all PRIMARIES required)
    tags:    dict {"dimensions": {dim: 0..1}, "durability": str, "target"?: str, "target_group"?: str}
    profile: dict returned by build_profile()
    targets: dict {primary: target_id} | None — what each primitive is currently ABOUT. Supplied,
             regard is evaluated PER PRIMITIVE against its own bound party rather than once for the
             whole event. Omitted, behaviour is exactly the one-target-per-event model.
             Produced by `retarget`, which the caller runs BEFORE this so the fear an event raises
             is fear OF the thing the event was about.

    Subject regard: when the event names a SUBJECT (tags["target"]/["target_group"]), the empathy
    dims (care_relevant, loss) are scaled by the character's regard for that subject, floored by
    _CARE_FLOOR (state-engine.md — relevance includes who the event is about). No target -> factor 1.0.

    Returns: new affect dict (pure — no mutation).
    Raises ValueError on malformed input.
    """
    # --- input validation (docs/state-engine.md: fail loud, never coerce) ---
    if not isinstance(affect, dict):
        raise RecordError("STATE_AFFECT_NOT_A_DICT", "appraise: affect must be a dict, got %r" % type(affect).__name__)
    missing = [p for p in PRIMARIES if p not in affect]
    if missing:
        raise RecordError("STATE_AFFECT_MISSING_PRIMARIES", "appraise: affect missing primaries: %s" % missing)
    # `_`-prefixed keys are author comments (`_note`), same tolerance
    # baseline.temperament already extends — before this, a comment key legal
    # in one block was fatal in its sibling while lint_book.py passed clean.
    unknown = [k for k in affect if k not in PRIMARIES and not k.startswith("_")]
    if unknown:
        raise RecordError("STATE_AFFECT_UNKNOWN_KEYS", "appraise: affect has unknown keys: %s" % unknown)
    for p, v in affect.items():
        if p.startswith("_"):
            continue
        if not isinstance(v, (int, float)):
            raise RecordError("STATE_AFFECT_VALUE_NOT_NUMERIC", "appraise: affect[%s] must be numeric, got %r" % (p, v))
        if not (0.0 <= float(v) <= 1.0):
            raise RecordError("STATE_AFFECT_VALUE_RANGE", "appraise: affect[%s]=%r out of [0,1]" % (p, v))

    if not isinstance(tags, dict):
        raise RecordError("STATE_TAGS_NOT_A_DICT", "appraise: tags must be a dict, got %r" % type(tags).__name__)

    required_profile_keys = ("gains", "decay_rates", "relevance_weights", "sensitivity")
    for k in required_profile_keys:
        if k not in profile:
            raise RecordError("STATE_PROFILE_MISSING_KEY", "appraise: profile missing key %r" % k)

    dimensions = tags.get("dimensions", {})
    if not isinstance(dimensions, dict):
        raise RecordError("STATE_TAGS_DIMENSIONS_TYPE", "appraise: tags['dimensions'] must be a dict")

    gains             = profile["gains"]
    relevance_weights = profile["relevance_weights"]
    sensitivity       = profile["sensitivity"]

    # subject regard -> empathy-scaling factor (1.0 when no subject, so target-less events unchanged)
    #
    # PER-PRIMITIVE when a target map is supplied. `emotion-basis.md`: "Per-primary targets move
    # the target from the event onto the state, and `_regard` becomes a per-primitive evaluation."
    # Without `targets` this is byte-identical to the one-target-per-event model it replaces, so
    # every caller that has not been taught about targets is unaffected.
    event_regard  = _regard(profile, tags.get("target"), tags.get("target_group"))
    regard_factor = _CARE_FLOOR + (1.0 - _CARE_FLOOR) * event_regard
    groups        = tags.get("_target_groups") if isinstance(tags.get("_target_groups"), dict) else {}

    def _conn_for(primary):
        """How INVESTED this character is in the party THIS primitive is pointed at.

        The twin of `_factor_for`, resolving the same bound target from the same map, and it needs
        no new inputs: `build_profile` already carries `relationships`. An unbound primitive gets
        1.0 — there is nobody to be invested in. Negative pushes never bind a party, so a
        suppression (PLAY collapsing under threat) is never amplified.
        """
        if not targets:
            return connection.magnitude_scale(
                connection.for_target(profile.get("relationships", {}), tags.get("target")))
        bound = targets.get(primary)
        if bound is None:
            return 1.0
        return connection.magnitude_scale(
            connection.for_target(profile.get("relationships", {}), bound))

    def _factor_for(primary):
        """The empathy scale for THIS primitive, from the party THIS primitive is pointed at."""
        if not targets:
            return regard_factor
        bound = targets.get(primary)
        if bound is None:                       # unbound primitive: no subject to scope empathy by
            return 1.0
        r = _regard(profile, bound, groups.get(bound))
        return _CARE_FLOOR + (1.0 - _CARE_FLOOR) * r

    # comment keys ride through verbatim; numerics are floated
    out = {p: (v if p.startswith("_") else float(v)) for p, v in affect.items()}

    for primary, delta in _price(dimensions, gains, relevance_weights, sensitivity,
                                 _factor_for, _conn_for).items():
        out[primary] = _clamp(out[primary] + delta)

    return out


def price_for(dimensions, profile, tags=None):
    """PUBLIC. One event's dimensions -> {primary: raw delta}, priced by the character's own
    genotype gains, worth-menu relevance, sensitivity, regard and connection.

    The durable tier calls THIS rather than carrying its own branches. Two things it deliberately
    does NOT take: `affect`, because a durable write is about who someone is and not where their
    mood happens to sit; and `impact`, because impact is the SUM of |delta-affect| that appraise
    already produced — pricing from it would apply the genotype gains a second time (quadratic in
    gain for the dominant primary) and inherit appraise's per-primary clamp shadow, where a
    saturated primary silently shrinks the measured impact.
    """
    tags = tags or {}
    gains = profile["gains"]
    rels = profile.get("relationships", {})
    groups = tags.get("_target_groups") if isinstance(tags.get("_target_groups"), dict) else {}
    ev_regard = _regard(profile, tags.get("target"), tags.get("target_group"))
    reg = _CARE_FLOOR + (1.0 - _CARE_FLOOR) * ev_regard
    cs = connection.magnitude_scale(connection.for_target(rels, tags.get("target")))
    return _price(dimensions, gains, profile["relevance_weights"], profile["sensitivity"],
                  lambda _p: reg, lambda _p: cs)


def _price(dimensions, gains, relevance_weights, sensitivity, factor_for, conn_for):
    """One event's dimensions -> {primary: raw delta}. THE ONE PRICING CHAIN.

    Extracted so the DURABLE tier can price with the identical arithmetic instead of carrying a
    second, thinner table of its own — `docs/character-model.md` law 4, "one pricing table, applied
    at every timescale", and the eighth entry in CLAUDE.md's duplicates table if it were copied.

    Returns RAW deltas and clamps nothing: `appraise` clamps into [0,1] against current affect, and
    the arc scales by its own step before clamping against a baseline. Two callers, two clamps, one
    chain.
    """
    out = {}
    for dim, mag in (dimensions or {}).items():
        if not isinstance(mag, (int, float)):
            raise RecordError("STATE_DIMENSION_MAGNITUDE_NOT_NUMERIC", "appraise: dimension %r magnitude must be numeric, got %r" % (dim, mag))
        mag = float(mag)
        # Unknown dimensions are silently ignored (future-proof; new consolidation dims won't crash).
        for primary, base_push in _DIM_TO_PRIMARY.get(dim, []):
            # empathy dims only, and scoped by the party THIS primitive is pointed at
            rscale = factor_for(primary) if dim in _REGARD_SCALED_DIMS else 1.0
            # CONNECTION: the greater the bond, the larger the impact. Separate from `rscale` and
            # deliberately not folded into it — regard asks "do they count to me at all" and is
            # clamped [0,1] with an innate-empathy floor; connection asks "how much of me is
            # invested" and is >= 1.0 with a ceiling. One factor holding both would make the floor
            # and the ceiling fight. A stranger composes to exactly 1.0, so every target-less event
            # and every existing fixture is byte-identical.
            cscale = conn_for(primary) if dim in connection.SCALED_DIMS else 1.0
            # relevance: Class-A per-character weighting over the worth menu.
            rel = float(relevance_weights.get(dim, _RELEVANCE_FALLBACK))
            # trait_sensitivity: Class-A genotype gain for this primary.
            g = float(gains.get(primary, 1.0))
            # delta = severity x relevance x trait_sensitivity x base_push x subject-regard
            out[primary] = out.get(primary, 0.0) + (
                mag * rel * g * sensitivity * base_push * rscale * cscale)
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
        raise RecordError("STATE_AFFECT_NOT_A_DICT", "decay: affect must be a dict, got %r" % type(affect).__name__)
    missing = [p for p in PRIMARIES if p not in affect]
    if missing:
        raise RecordError("STATE_AFFECT_MISSING_PRIMARIES", "decay: affect missing primaries: %s" % missing)
    # `_`-prefixed keys: author comments, tolerated and passed through — see
    # the twin exemption in appraise.
    unknown = [k for k in affect if k not in PRIMARIES and not k.startswith("_")]
    if unknown:
        raise RecordError("STATE_AFFECT_UNKNOWN_KEYS", "decay: affect has unknown keys: %s" % unknown)
    for p, v in affect.items():
        if p.startswith("_"):
            continue
        if not isinstance(v, (int, float)):
            raise RecordError("STATE_AFFECT_VALUE_NOT_NUMERIC", "decay: affect[%s] must be numeric" % p)
        if not (0.0 <= float(v) <= 1.0):
            raise RecordError("STATE_AFFECT_VALUE_RANGE", "decay: affect[%s]=%r out of [0,1]" % (p, v))

    if not isinstance(temperament, dict):
        raise RecordError("STATE_TEMPERAMENT_NOT_A_DICT", "decay: temperament must be a dict")
    for p in PRIMARIES:
        if p not in temperament:
            raise RecordError("STATE_TEMPERAMENT_MISSING_PRIMARY", "decay: temperament missing primary %r" % p)
        t = temperament[p]
        if not isinstance(t, dict) or "mean" not in t:
            raise RecordError("STATE_TEMPERAMENT_ENTRY_INVALID", "decay: temperament[%r] must be a dict with 'mean'" % p)

    if not isinstance(profile, dict) or "decay_rates" not in profile:
        raise RecordError("STATE_PROFILE_MISSING_DECAY_RATES", "decay: profile must be a dict with 'decay_rates'")

    decay_rates = profile["decay_rates"]

    out = {k: v for k, v in affect.items() if k.startswith("_")}  # comments survive decay
    for p in PRIMARIES:
        mean = float(temperament[p]["mean"])
        r    = float(decay_rates.get(p, _DECAY_RATE[p]))
        # Ai <- mean + (Ai - mean) * r
        out[p] = _clamp(mean + (float(affect[p]) - mean) * r)

    return out
