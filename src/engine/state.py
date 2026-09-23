"""state.py — State Engine, Gate 2.

Three-tier emotion model: temperament (resting) / current state (event-driven) / effective (catalog).
This module implements the middle tier: appraisal + decay.

Normative contract: docs/state-engine.md.
Primaries: src/engine/records.py (single source of truth).
Baseline provenance: docs/baseline-generation.md.
Genotype (hit / hold per path) and the authored rest word: src/engine/heritable.py + docs/baseline-generation.md §Genetics.
Relevance weighting: docs/values-and-stakes.md.
"""
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.engine import connection                    # the investment multiplier (docs/character-model.md)
from src.engine import heritable as _her             # THE one reading of the genotype
from src.engine import rungs as _rungs               # rung_at, for the per-rung decay staircase
from src.engine.decay_law import relax   # THE one law; every decay tier obeys it
from src.engine.rung_blocks import BANDS as _BANDS   # per-rung decay reads the ladder edges
from src.engine.records import PATHS, admits_role, RecordError  # rule 6's bad-input type

# ---------------------------------------------------------------------------
# Class-B constants — theory-anchored, probe-calibrated.
# Reference: docs/state-engine.md §"Where the values come from"
# ---------------------------------------------------------------------------

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
_DIM_TO_PATH = {
    # WAS `_DIM_TO_PRIMARY`, keyed by the Panksepp primitives. Rekeyed 2026-09-08 when the paths
    # became the state. Every weight is the ORIGINAL authored number, carried across on
    # docs/emotion-paths.md's "was" mapping -- nothing was re-tuned.
    #
    # TWO THINGS CHANGED SHAPE, both recorded rather than smoothed:
    #   * SEEKING and LUST both became STIRRING, so where a dimension pushed both, the LARGER
    #     magnitude is kept rather than the sum. `attraction` pushed LUST 0.45 and SEEKING 0.18;
    #     summing would give 0.63, a bigger single shove than any weight anyone authored.
    #   * PLAY's pushes were dropped while LEVITY was unbuilt and RESTORED under LEVITY on 2026-09-11
    #     (the owner's ruling), at the ORIGINAL authored numbers: lowered under threat, loss and social
    #     violation; raised on mastery, relief and attraction.
    #
    # RECEPTIVITY and SELF-REGARD have NO row here. Nothing in the event vocabulary means "something
    # good reached you" or "your standing moved", so those two paths are structurally reachable and
    # never move. Authoring that mapping is the owner's, not this conversion's.
    "threat":           [("WARINESS",     0.45), ("STIRRING",     0.12),
                         ("DISPLEASURE",  0.10), ("LEVITY",      -0.22)],
    "loss":             [("DEFLATION",    0.50), ("STIRRING",    -0.18), ("LEVITY", -0.20)],
    "care_relevant":    [("GOODWILL",     0.40), ("STIRRING",     0.10)],
    "mastery":          [("STIRRING",     0.35), ("WARINESS",    -0.10), ("LEVITY",  0.15)],
    "social_violation": [("DISPLEASURE",  0.45), ("DISTASTE",     0.28), ("LEVITY", -0.15)],
    "relief":           [("WARINESS",    -0.40), ("DEFLATION",   -0.35), ("LEVITY",  0.20)],
    "attraction":       [("STIRRING",     0.45), ("LEVITY",       0.10)],
}

_DIM_TO_PATH["threat"].append(("DISTASTE", 0.08))

# Fail at IMPORT, not at the first event that happens to use the dimension. A primitive named here
# that PATHS does not carry would KeyError deep inside appraise on some later turn, which is a
# runtime surprise standing in for an authoring error.
for _dim, _pushes in _DIM_TO_PATH.items():
    for _p, _w in _pushes:
        if _p not in PATHS:
            raise RecordError("STATE_DIM_TO_PRIMARY_UNKNOWN_PRIMITIVE", "_DIM_TO_PATH[%r] pushes %r, which is not a primitive. Add it to "
                             "PATHS or remove the push - it cannot be silently skipped."
                             % (_dim, _p))

# THE DECAY GLOBAL, IN MINUTES (2026-09-10). Until today this was `_DECAY_RATE`, a retention
# fraction PER BEAT — and a beat had no duration, so a thirty-exchange argument aged a feeling
# thirty units of nothing in particular and a week between scenes aged it not at all. The owner
# locked the clock to the minute (see clock.py), so the global is now a HALF-LIFE per path, and
# there are TWO per path: the DISPOSITION zone (rung <= heritable.REST_CAP — where a character
# can rest) fades slowly, the EPISODE zone above it fades fast. That is the owner's "bottom half
# decays slower than the top", with the zone boundary reusing the rest cap rather than authoring
# a second line through each ladder. Retention over m minutes on a path in a zone is
#     0.5 ** (m / (half_life * hold))
# with the genotype's HOLD cell multiplying the half-life directly (`half_life_minutes`).
#
# THESE VALUES ARE TEMPORARY, SET FROM THE FIRST TWO LIVE READS (2026-09-11; owner: assign
# temporary numbers, generate a book, adjust on what is produced). The EPISODE zone is the
# thermometer's median half-life per path over Red Badge (run readalong-red-badge-1789158299-9a8063)
# and Holmes (readalong-holmes-1789164611-09007d), rounded; the sampling floor was ~25 minutes, so
# the fastest are floors. The previous START (60 / 120 / 180 / 240 / 1440 / 4320 / 4320 / 14400)
# ran away on both books: beats last 5-10 story-minutes, the seat lands ~2 readings on most of
# them, and half-lives of hours to days drained nothing between receipts, pinning SELF-REGARD,
# DEFLATION and GOODWILL at the ceiling while the text's own standing level sat at the lowest rung
# two samples in three (docs/emotion-arithmetic.md section 5). The measured uplift per reading was
# 0.6-1.7x lambda*height, so the multipliers stood and only this table moved.
# The DISPOSITION zone is UNMEASURED - a five-beat thermometer cannot see a decay over days - so
# it keeps each path's previous ratio to its episode zone (12, 12, 16, 18, 10, 10, -, 9) until a
# read with day-long gaps (Frankenstein, Jane Eyre) measures it - except DEFLATION, held at 1800
# by judgment so a settled loss still outlasts settled unease (the spec's one asymmetry claim).
# The measured fast-to-slow ORDER replaces the spec's guess: WARINESS < DEFLATION < STIRRING <
# DISPLEASURE < SELF-REGARD < RECEPTIVITY < GOODWILL < DISTASTE (RECEPTIVITY now outlasts STIRRING,
# 70 vs 33-54 on both books; DISTASTE from one point). tests/test_clock.py pins that order;
# tests/test_genotype_balance.py guards reachability and rank order (E2-E4).
#
# SINCE 2026-09-12 (redesign gate 2, owner: "proper decay rates per emotion AND per rung") these
# two numbers are the ANCHORS the PER-RUNG staircase is built from, not a two-zone lookup. Decay
# steps DOWN the ladder rung by rung, each rung draining at its own half-life (`decay_over`), so a
# path cools fast at the top and slowly at the bottom -- the blocks' own claim that the top cannot
# be sustained and the bottom is where a person lives. `_rung_half_life(path, k)` derives the 92
# cells from EPISODE (the measured excursion median, anchoring rung `_MID_RUNG`), DISPOSITION (the
# resting anchor, rung 1) and `_TOP_BURN` (the burns-out top). Every cell is a START: replace an
# anchor per path or the burn factor, and the whole ladder re-derives; a measurement (the
# thermometer recording the rung a level fell from) can set a cell directly later.
_HALF_LIFE = {
    #               episode   disposition     (minutes) -- the two anchors; the staircase is derived

    "WARINESS":    (   30.0,      360.0),   # measured 26 / 54; unease at rest lingers hours
    "RECEPTIVITY": (   70.0,      840.0),   # measured 70 / 68
    "STIRRING":    (   45.0,      720.0),   # measured 33 / 54
    "DISPLEASURE": (   50.0,      900.0),   # measured 50 / 54
    "GOODWILL":    (   90.0,      900.0),   # measured 23 / 129 - Watson's warmth carries
    "DISTASTE":    (  120.0,     1200.0),   # one point at 384; the slowest of the short zone
    "DEFLATION":   (   40.0,     1800.0),   # measured 26 / none - three points at the floor; at REST a settled loss halves in thirty hours (JUDGMENT: the spec's claim that a loss does not un-happen lives in this zone, which no read has measured; test_state decay_asymmetry)
    "SELF-REGARD": (   60.0,      540.0),   # measured 82 / 48
    "LEVITY":      (   45.0,      450.0),   # UNMEASURED - a JUDGMENT beside STIRRING, its nearest kin (a joke let through passes within the hour; an absorbed afternoon is the activity's length, not the path's); built 2026-09-11 by ruling, tuned in production
}

# THE PER-RUNG STAIRCASE (gate 2, 2026-09-12). Three anchors per path, all START:
#   rung `_MID_RUNG`  = the EPISODE anchor (the measured excursion median mostly sat at rungs 2-4)
#   rung 1            = the DISPOSITION anchor (the resting hum, the slow end)
#   the top rung      = EPISODE x `_TOP_BURN` (the block says the top burns out)
# Geometric interpolation in rung-index space between the anchors -> monotone decreasing, since
# DISPOSITION > EPISODE > EPISODE*_TOP_BURN on every path. One judgment (`_TOP_BURN`) governs the
# whole top half; the two anchors are per-path and measurable.
_MID_RUNG = 3
_TOP_BURN = 0.33


def _rung_half_life(path, index):
    """(path, 1-based rung index) -> that rung's half-life in minutes, before hold. Derived from the
    path's two anchors and the burn factor; a top rung is short, a bottom rung is long."""
    episode, disposition = _HALF_LIFE[path]
    n = len(_BANDS[path])
    k = 1 if index < 1 else (n if index > n else int(index))
    mid = _MID_RUNG if _MID_RUNG <= n else n
    top = episode * _TOP_BURN
    if k <= 1:
        return float(disposition)
    if k <= mid:
        frac = (k - 1) / float(mid - 1) if mid > 1 else 1.0
        return float(disposition) * (episode / float(disposition)) ** frac
    if n == mid:
        return float(episode)
    frac = (k - mid) / float(n - mid)
    return float(episode) * (top / float(episode)) ** frac


def half_life_minutes(path, value, hold=1.0):
    """The half-life in force for `value` on `path`, bent by the character's hold. PER RUNG since
    2026-09-12: the rate of the rung the value sits in, not the zone."""
    h = float(hold)
    if h <= 0:
        raise RecordError("GENOTYPE_HOLD_NOT_POSITIVE", "hold must be > 0, got %r" % (hold,))
    return _rung_half_life(path, _rungs.rung_at(path, float(value))[0]) * h


def decay_over(path, value, mean, hold, minutes):
    """`value` decayed toward `mean` over `minutes`, STEPPING through the rungs it passes -- each
    rung drains at its own half-life (`_rung_half_life` x hold). At most one segment per rung, so a
    multi-hour gap from the top of a ladder cools fast through the hot rungs and slowly through the
    cool ones, instead of the whole gap running at the start rung's rate. Pure; returns the new
    value. `relax`'s identities hold: minutes 0 or value at mean -> value unchanged."""
    v, m, rem = float(value), float(mean), float(minutes)
    h = float(hold)
    if rem <= 0 or h <= 0 or abs(v - m) < 1e-12:
        return v
    bands = _BANDS[path]
    down = v > m
    for _ in range(len(bands) + 1):                       # bounded: one segment per rung, + safety
        if rem <= 0 or abs(v - m) < 1e-12:
            break
        hl = _rung_half_life(path, _rungs.rung_at(path, v)[0]) * h
        if hl <= 0:
            break
        lo, hi, _n = bands[_rungs.rung_at(path, v)[0] - 1]
        # the edge of THIS rung on the way to `mean`; never past `mean`
        edge = max(lo, m) if down else min(hi, m)
        per_min = 0.5 ** (1.0 / hl)                       # this rung's retention per minute
        if abs(edge - m) < 1e-12:                         # the rung that contains rest: finish here
            v = relax(v, m, per_min, rem)                 # THE ONE LAW (decay_law.relax), not re-spelled
            break
        t = hl * math.log2(abs(v - m) / abs(edge - m))    # time to fall/rise to this rung's edge
        if t <= 0 or t >= rem:                            # not enough time to leave the rung
            v = relax(v, m, per_min, rem)
            break
        v = edge + (-1e-9 if down else 1e-9)              # step just into the next rung's band
        rem -= t
    return v


def retention_for(path, value, hold, minutes):
    """The retention factor over `minutes` for a value on `path` — what decay_law.relax takes as
    `retention` with elapsed 1.0. 0.5 at exactly one (hold-bent) half-life, 1.0 at zero minutes.
    THE RUNG IS READ ONCE, from where the value IS at the start of the interval (`half_life_minutes`
    -> `_rung_half_life`); an excursion that crosses a rung edge mid-interval still takes that one
    rung's rate for the whole interval, which at beat granularity is the approximation this tier
    accepts — `decay_over` is the tier that steps rung by rung instead."""
    try:
        m = float(minutes)
    except (TypeError, ValueError):
        raise RecordError("STATE_ELAPSED_NOT_NUMERIC",
                          "retention_for: minutes must be a number, got %r" % (minutes,))
    if m < 0:
        raise RecordError("STATE_ELAPSED_NOT_NUMERIC", "retention_for: minutes must be >= 0, got %r" % (minutes,))
    if m == 0.0:
        return 1.0
    return 0.5 ** (m / half_life_minutes(path, value, hold))


# A primitive is BACK AT REST when it sits within this of ITS OWN temperament mean. Kept in step
# with direction._DEV_THRESH, which is the same "not asking for attention" judgement.
#
# NOT also gated on the quiet band, which was the first version and was wrong: a character whose
# resting FEAR is 0.62 is never inside the 0.25 quiet band, so her binds would have persisted
# forever while a calm character's cleared normally. Absolute level is disposition; DEVIATION from
# your own mean is the response. Only a response can be about something — which is rule 5's own
# reasoning ("temperament never binds; dispositions do not point") applied consistently.
_AT_REST = 0.15

# THE GENOTYPE IS READ IN `heritable.py` AND NOWHERE ELSE — two cells per path (hit, hold).
# `build_profile` asks it for the gain and the hold on every path and builds nothing else about
# the character into the arithmetic; the 2026-09-10 rebuild cut `effortful_control`,
# `sensitivity` and the HEXACO bumps as second per-character terms the spec forbids. Where the
# character RESTS is not genotype: it is authored as a word at `baseline.temperament[path].rest`
# beside their voice (owner, 2026-09-10), and `heritable.ensure_temperament` seeds the mean.


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
# _CARE_FLOOR is the innate-empathy floor: a learned low regard for a subject can dampen the
# response to their harm, never delete it. (The floor is the innate response that regard scales
# down to and no further.) Class-B, probe-calibrated start.
_CARE_FLOOR = 0.25
# Only OTHER-directed welfare dims are subject-scoped. threat/mastery/relief are self-directed
# (the character's own state), not about regard for a subject — left unscaled.
_REGARD_SCALED_DIMS = ("care_relevant", "loss")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(x):
    """Clamp to [0, 1]. docs/state-engine.md §Appraisal step 4."""
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


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

    THE GENOTYPE SUPPLIES EXACTLY TWO THINGS PER PATH (2026-09-10, owner):
      gains        {path: g}      the HIT cell — `f <- f + v_k * g`, the only per-character term
                                  in the accumulation rule (docs/emotion-arithmetic.md section 3)
      hold         {path: factor} the HOLD cell — a multiplier on the path's half-life; decay reads
                                  it against the minute clock (`retention_for`), so the person term
                                  and the global term are balanced separately
    AND THE SHEET SUPPLIES WHERE THEY REST — a design question, not a heritable one (owner, later
    the same day: "have temperament be a character design question, along with their voice"):
      temperament  {path: {rest, mean}} `baseline.temperament`, the rest WORD authored beside the
                                  voice and the mean SEEDED from it once (heritable.ensure_temperament)
                                  — stored, because the arc engine writes durable diffs into it

    WHAT IS GONE, and the reason each time is the same — a second per-character term on `g` or
    on `r` that the spec's one-rule-for-everyone forbids: `sensitivity` (a uniform scale on all
    eight gains), `effortful_control` / `regulation` / `control` (bent decay, then gain, then was
    read by nothing), `_HEXACO_SENSITIVITY_MAP` (a second source of g, from traits). The trait
    means now reach no engine arithmetic; that dead vector is recorded in the gate, not resolved.

    char: the full character dict (fixed + baseline + current) per character-schema.md.
    Returns: plain dict with keys:
        gains             {path: float}
        hold              {path: float}
        temperament       {path: {"rest", "mean"}}   — the same object the sheet holds
        relevance_weights {dim: float}    per-dimension relevance for this character
        model             dict            baseline.model reference
        regard, relationships             subject-regard inputs (unchanged)
    """
    if not isinstance(char, dict):
        raise RecordError("STATE_CHAR_NOT_A_DICT", "build_profile: char must be a dict, got %r" % type(char).__name__)
    _her.ensure_temperament(char)
    fixed = char.get("fixed", {})
    baseline = char.get("baseline", {})
    genotype = fixed.get("genotype", {})
    model = baseline.get("model", {})

    # ---- Class-A: the HIT cell -> gain, per path. Clamped to [0.5, 2.5] against degenerate
    # authored numbers; every preset word is well inside.
    gains = {p: max(0.5, min(2.5, _her.hit(p, genotype))) for p in PATHS}

    # ---- Class-A: the HOLD cell, a multiplier on the path's half-life (the Class-B global).
    hold = {p: _her.hold(p, genotype) for p in PATHS}

    # ---- Class-A: per-dimension relevance for this character ----
    relevance_weights = {dim: _relevance(dim, model) for dim in _DIM_VALUE_KEYS}

    # ---- Class-A: subject regard — class-level disposition (the bigotry) + relationship edges ----
    current = char.get("current", {})
    regard = model.get("regard", {}) if isinstance(model.get("regard"), dict) else {}
    relationships = current.get("relationships", {}) if isinstance(current.get("relationships"), dict) else {}

    return {
        "gains":             gains,
        "hold":              hold,
        # GATE THREE (2026-09-11): what this character HOLDS that is not a person — wounds (engine
        # state at baseline.wounds, keyed concept + path), goals, worth-menu values — each as an
        # investment in [0,1]. People are read live off `relationships` below. The receipt and the
        # half-life both read investment through `connection.for_about`; owner: abstract ideas
        # carry the same hit as relationships.
        "held":              connection.held_map(char),
        "temperament":       baseline["temperament"],
        "relevance_weights": relevance_weights,
        "model":             model,
        "regard":            regard,
        "relationships":     relationships,
    }


def appraise(affect, tags, profile, targets=None, repeats=None, present=None):
    """Apply one structured event to the current affect vector.

    docs/state-engine.md §Appraisal module:
      magnitude = severity(tag_dim_value) x relevance(dim, character) x trait_sensitivity(primary)
      Ai <- clamp(Ai + direction * magnitude)

    Gate-2 scope: severity factoring for wielded threats (damage-potential x hit-probability x context)
    is explicitly deferred to a later gate (state-engine.md §Appraisal step 3 note).  Here severity =
    the raw dimension magnitude emitted by the consolidation LLM (0..1).

    affect:  dict {primary: float 0..1} — current affect state (all PATHS required)
    tags:    dict {"dimensions": {dim: 0..1}, "durability": str, "target"?: str, "target_group"?: str}
    profile: dict returned by build_profile()
    targets: dict {primary: target_id} | None — what each primitive is currently ABOUT. Supplied,
             regard is evaluated PER PRIMITIVE against its own bound party rather than once for the
             whole event. Omitted, behaviour is exactly the one-target-per-event model.
             Produced by `retarget`, which the caller runs BEFORE this so the fear an event raises
             is fear OF the thing the event was about.
    repeats: dict {about: n} | None — how many consecutive prior beats were about each thing
             (`targets.repeat_count`); the repetition term `q` (gate three, 2026-09-11). None = 1.0.
    present: iterable of about-ids that are IN THE ROOM this beat (people on the roster; a concept
             when this beat names it). Decides whether repetition habituates or grinds. None = absent.

    GATE THREE (2026-09-11) — THE RECEIPT IS  v_k · g · connection(about) · q  (docs/emotion-arithmetic.md
    section 3). `connection` reads investment in whatever the primitive is about through ONE
    registry — a person's edge, a wound's intensity, a goal's priority, a value's weight — so an
    idea held at 0.8 lands as a person held at 0.8 (`connection.for_about`); `q` is
    `connection.repetition(n, present)`.

    Subject regard: when the event names a SUBJECT (tags["target"]/["target_group"]), the empathy
    dims (care_relevant, loss) are scaled by the character's regard for that subject, floored by
    _CARE_FLOOR (state-engine.md — relevance includes who the event is about). No target -> factor 1.0.

    Returns: new affect dict (pure — no mutation).
    Raises ValueError on malformed input.
    """
    # --- input validation (docs/state-engine.md: fail loud, never coerce) ---
    if not isinstance(affect, dict):
        raise RecordError("STATE_AFFECT_NOT_A_DICT", "appraise: affect must be a dict, got %r" % type(affect).__name__)
    missing = [p for p in PATHS if p not in affect]
    if missing:
        raise RecordError("STATE_AFFECT_MISSING_PRIMARIES", "appraise: affect missing primaries: %s" % missing)
    # `_`-prefixed keys are author comments (`_note`), same tolerance
    # baseline.temperament already extends — before this, a comment key legal
    # in one block was fatal in its sibling while lint_book.py passed clean.
    unknown = [k for k in affect if k not in PATHS and not k.startswith("_")]
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

    required_profile_keys = ("gains", "hold", "relevance_weights")
    for k in required_profile_keys:
        if k not in profile:
            raise RecordError("STATE_PROFILE_MISSING_KEY", "appraise: profile missing key %r" % k)

    dimensions = tags.get("dimensions", {})
    if not isinstance(dimensions, dict):
        raise RecordError("STATE_TAGS_DIMENSIONS_TYPE", "appraise: tags['dimensions'] must be a dict")

    gains             = profile["gains"]
    relevance_weights = profile["relevance_weights"]

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
        about = tags.get("target") if not targets else targets.get(primary)
        if about is None:
            return 1.0
        return connection.magnitude_scale(
            connection.for_about(profile.get("relationships", {}), profile.get("held"), about, primary))

    def _about_for(primary):
        return tags.get("target") if not targets else targets.get(primary)

    _here = {str(x) for x in (present or ())}

    def _q_for(primary):
        """The repetition multiplier for THIS primitive's about: 1.0 when nothing is known."""
        about = _about_for(primary)
        if not about or not repeats:
            return 1.0
        n = repeats.get(str(about), 0)
        return connection.repetition(n, str(about) in _here)

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

    for primary, delta in _price(dimensions, gains, relevance_weights,
                                 _factor_for, _conn_for, _q_for, _about_for).items():
        out[primary] = _clamp(out[primary] + delta)

    return out


def price_for(dimensions, profile, tags=None):
    """PUBLIC. One event's dimensions -> {primary: raw delta}, priced by the character's own
    genotype gains, worth-menu relevance, regard and connection.

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
    return _price(dimensions, gains, profile["relevance_weights"],
                  lambda _p: reg, lambda _p: cs)


def _price(dimensions, gains, relevance_weights, factor_for, conn_for, q_for=None, about_for=None):
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
        for primary, base_push in _DIM_TO_PATH.get(dim, []):
            # empathy dims only, and scoped by the party THIS primitive is pointed at
            rscale = factor_for(primary) if dim in _REGARD_SCALED_DIMS else 1.0
            # CONNECTION: the greater the bond, the larger the impact. Separate from `rscale` and
            # deliberately not folded into it — regard asks "do they count to me at all" and is
            # clamped [0,1] with an innate-empathy floor; connection asks "how much of me is
            # invested" and is >= 1.0 with a ceiling. One factor holding both would make the floor
            # and the ceiling fight. A stranger composes to exactly 1.0, so every target-less event
            # and every existing fixture is byte-identical.
            # A person's investment scales the empathy/betrayal dims only; a concept, goal or value
            # IS the thing feared or lost, so it scales every dim (`connection.scales`).
            _about = about_for(primary) if about_for else None
            cscale = conn_for(primary) if connection.scales(dim, _about) else 1.0
            # REPETITION (gate three): the same thing landing again on the same path.
            qscale = q_for(primary) if q_for else 1.0
            # relevance: Class-A per-character weighting over the worth menu.
            rel = float(relevance_weights.get(dim, _RELEVANCE_FALLBACK))
            # the HIT cell: Class-A genotype gain for this path.
            g = float(gains.get(primary, 1.0))
            # delta = severity x relevance x genotype hit x base_push x subject-regard x connection x repetition
            out[primary] = out.get(primary, 0.0) + (
                mag * rel * g * base_push * rscale * cscale * qscale)
    return out


def receive(affect, readings, profile, targets=None, repeats=None, present=None):
    """THE RECEIPT STEP FROM READINGS (docs/emotion-arithmetic.md section 3; section 5 step 3).

    Phase 3, wired 2026-09-11. The appraiser seat reports what AROSE this beat as readings —
    {path, rung NAME, about} — and each one adds its rung's vector to its path, scaled by the
    character's multipliers and nothing else:

        f[path] <- f[path] + vector_for(path, rung) · g[path] · connection(about) · q

    `vector_for` is the same number for everyone (rungs.py); `g` is the HIT cell; connection is
    investment in what the reading is about (`connection.for_about`, the about from the reading or
    the path's standing bind); `q` is repetition. Decay ran BEFORE this (the caller's job, spec
    "decay first"); the clamp is at 1.0. Returns (new affect, impact) where impact is the beat's
    total addition Σ v_k·g — the quantity arc.assess reads as "how much it moved them" (step 7).

    This is `appraise` with the seat in place of the actor's self-tags and the rung vector in
    place of _DIM_TO_PATH; appraise stays as the --stub double and the refusal fallback.

    readings: [records.Reading] — validated by readings.parse against the live ladder.
    """
    from . import rungs as _rungs
    if not isinstance(affect, dict):
        raise RecordError("STATE_AFFECT_NOT_A_DICT", "receive: affect must be a dict, got %r" % type(affect).__name__)
    missing = [p for p in PATHS if p not in affect]
    if missing:
        raise RecordError("STATE_AFFECT_MISSING_PRIMARIES", "receive: affect missing primaries: %s" % missing)
    if not isinstance(profile, dict) or "gains" not in profile:
        raise RecordError("STATE_PROFILE_MISSING_KEY", "receive: profile missing key 'gains'")
    gains = profile["gains"]
    rels = profile.get("relationships", {}) if isinstance(profile.get("relationships"), dict) else {}
    held = profile.get("held") or {}
    here = {str(x) for x in (present or ())}
    out = {p: (v if p.startswith("_") else float(v)) for p, v in affect.items()}
    impact = 0.0
    for r in (readings or []):
        path, rung, about = r.path, r.rung, (r.about or "")
        k = _rungs.index_of(path, rung)                      # raises on a rung the ladder lacks
        v = _rungs.vector_for(path, k)
        g = float(gains.get(path, 1.0))
        about = about or (targets or {}).get(path) or ""
        cs = connection.magnitude_scale(connection.for_about(rels, held, about, path)) if about else 1.0
        n = (repeats or {}).get(str(about), 0) if about else 0
        q = connection.repetition(n, str(about) in here) if about else 1.0
        add = v * g * cs * q
        impact += add
        out[path] = _clamp(out[path] + add)
    return out, impact


def decay(affect, temperament, profile, elapsed=None, targets=None, present=None):
    """Relax each path toward its temperament mean (resting level) over `elapsed` MINUTES.

    GATE THREE (2026-09-11) — THE HALF-LIFE IS  base · hold · (1 + connection(about)) · presence.
    `targets` says what each path is ABOUT; investment in that thing (a bond, a wound, a goal, a
    value — `connection.for_about` on `profile["held"]` and the live edges) stretches the half-life
    (`connection.half_life_scale`: a full investment doubles it — the "and the longer it lasts" half
    of character-model.md's rule), and while the thing is IN THE ROOM (`present`) the excursion
    barely fades at all (`connection.PRESENCE_HOLD`, x3). Both None -> exactly the old behaviour.

    ON THE ONE CLOCK SINCE 2026-09-10 — the fifth consumer of clock.py. `elapsed` is REQUIRED and
    in minutes: the gap the scene derived at its opening, or the scene's authored share per beat
    (lasts / budget), or 0.0 for a beat inside a scene with no `lasts` (owner: no beat has a
    duration unless authored). A caller that does not know how much time passed says 0, not
    nothing; the old default of one unit is gone because the unit is no longer the caller's.

    docs/state-engine.md §Decay:
      Ai <- baselineI + (Ai - baselineI) * r_i
    where r_i is the per-primary effective retention rate (1 = no decay, 0 = instant return).

    Rates: `_HALF_LIFE`'s two anchors per path (episode, disposition), in minutes, derive the
    per-rung staircase (`_rung_half_life`); each rung's rate is bent by the character's HOLD cell.
    (Parallel to docs/relationships.md "drift toward baseline.")

    ON THE ONE LAW SINCE 2026-09-09, and it was the SEVENTH spelling of it. `decay_law.py` exists
    because the engine held six hand-written copies of `rest + (value - rest) * retention ** elapsed`
    -- and its header LISTS this function among them, while this module imported nothing from it.
    A documented wiring that was never made, green the whole time, because the arithmetic happened
    to agree. It agrees no longer by luck: `relax` is called.

    `elapsed` IS NEW, AND IT IS THE REAL REPAIR. Every other decay tier in this engine takes a
    clock -- `bond_rest.drift`, `toward.erode`, `wound.erode`, `arc.erode`, `world_appraisal.cool` --
    and this one did not, so a beat spanning a heartbeat and a beat spanning a week aged a feeling
    identically. `docs/character-model.md`'s decay section says the tiers "differ only in what they
    rest at, how fast, and ON WHICH CLOCK"; emotion had two of the three.

    DEFAULTS TO 1.0, so every existing caller gets byte-identical numbers -- `retention ** 1.0` is
    `retention`. NO DRIVER PASSES IT YET: what one unit IS (a beat, or the director's declared unit
    that `time_declarations` already carries for the other tiers) is a design decision about the
    world's time model, and threading a clock before its unit is decided would bake the answer in
    silently. The parameter is here so that decision is a wiring change, not a rewrite.

    affect:      dict {primary: float 0..1}
    temperament: dict {path: {"rest": word|number, "mean": float}}
                 (= baseline.temperament from the character sheet)
    profile:     dict returned by build_profile()

    Returns: new affect dict (pure — no mutation).
    Raises ValueError on malformed input.
    """
    if not isinstance(affect, dict):
        raise RecordError("STATE_AFFECT_NOT_A_DICT", "decay: affect must be a dict, got %r" % type(affect).__name__)
    missing = [p for p in PATHS if p not in affect]
    if missing:
        raise RecordError("STATE_AFFECT_MISSING_PRIMARIES", "decay: affect missing primaries: %s" % missing)
    # `_`-prefixed keys: author comments, tolerated and passed through — see
    # the twin exemption in appraise.
    unknown = [k for k in affect if k not in PATHS and not k.startswith("_")]
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
    for p in PATHS:
        if p not in temperament:
            raise RecordError("STATE_TEMPERAMENT_MISSING_PRIMARY", "decay: temperament missing primary %r" % p)
        t = temperament[p]
        if not isinstance(t, dict) or "mean" not in t:
            raise RecordError("STATE_TEMPERAMENT_ENTRY_INVALID", "decay: temperament[%r] must be a dict with 'mean'" % p)

    if not isinstance(profile, dict) or "hold" not in profile:
        raise RecordError("STATE_PROFILE_MISSING_HOLD", "decay: profile must be a dict with 'hold'")
    if elapsed is None:
        raise RecordError("STATE_ELAPSED_MISSING",
                          "decay: elapsed (minutes) is required — 0.0 for a beat with no authored duration")
    try:
        e = float(elapsed)
    except (TypeError, ValueError):
        raise RecordError("STATE_ELAPSED_NOT_NUMERIC",
                          "decay: elapsed must be a number of minutes, got %r" % (elapsed,))
    if e < 0:
        raise RecordError("STATE_ELAPSED_NOT_NUMERIC", "decay: elapsed must be >= 0 minutes, got %r" % (elapsed,))

    hold = profile["hold"]
    rels = profile.get("relationships", {}) if isinstance(profile.get("relationships"), dict) else {}
    held = profile.get("held") or {}
    here = {str(x) for x in (present or ())}
    out = {k: v for k, v in affect.items() if k.startswith("_")}  # comments survive decay
    for p in PATHS:
        mean = float(temperament[p]["mean"])
        v = float(affect[p])
        stretch = 1.0
        about = (targets or {}).get(p)
        if about:
            stretch *= connection.half_life_scale(connection.for_about(rels, held, about, p))
            if str(about) in here:
                stretch *= connection.PRESENCE_HOLD
        # PER-RUNG STEPPING (gate 2): the interval drains through each rung it crosses at that
        # rung's own rate; `stretch` (investment + presence) lengthens every rung's half-life alike.
        out[p] = _clamp(decay_over(p, v, mean, float(hold.get(p, 1.0)) * stretch, e))

    return out
