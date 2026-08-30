"""consolidation.py — Gate 4: Consolidation Validation.

Mechanical guard on the keystone: the actor's self-reported event-tags.

Contracts:
  consolidation-loop.md   — Principle 3 (typed schema), pipeline (schema-conformance /
                            containment / capability), open-q 2 RESOLVED (composite conf).
  record-contract.md      — event_type catalog shape {appraisal_map, world_map,
                            visibility}.
  state.py _DIM_TO_PRIMARY — the known appraisal dimension vocabulary.
  ledger.py _project       — fold types that need catalog rows.
  gate.py / scene.py       — Percept shape {ref, channel, fidelity, attributes,
                            recognized_as?, must_surface}.

Public API (wired by the integrator onto coherence_probe.py):
    validate_tags(tags, percepts, skills) -> result dict
    CATALOG   — dict[str, row-dict]
    THETA_CONF — float escalation threshold
"""

# ---- Known appraisal dimensions (state.py _DIM_TO_PRIMARY vocabulary) ----
# DERIVED from state._DIM_TO_PRIMARY, which is the single source of truth for what an appraisal
# dimension IS. It was a hand-written list of six and went out of sync the moment `attraction` was
# added as the seventh (2026-08-23) — with a consequence far worse than a warning:
# `validate_tags` returns ok=False on an unknown dimension, and scripts/scene.py answers that by
# setting `applied = {"dimensions": {}}`, so THE ENTIRE APPRAISAL IS DISCARDED. A live turn tagged
# `attraction` and moved no affect at all; the next speaker had no salience to act on and the scene
# lulled after one beat. A second copy of a list is a defect waiting for the list to change.
from .state import _DIM_TO_PRIMARY as _DIMS_SOURCE            # noqa: E402
from .errors import EngineError

_KNOWN_DIMS = frozenset(_DIMS_SOURCE)

_VALID_DURABILITY = frozenset(["transient", "durable"])

# The ONE durability predicate. Before 2026-08-30 there were three vocabularies: this frozenset
# (2 values), and a hand-copied `_DURABLE = ("durable", "marking", "reshaping")` in BOTH
# acquisition.py and cut.py — so the module whose writes are PERMANENT accepted two values the
# validator rejects, while docs/driving-the-engine.md and docs/arc-engine.md taught authors to
# write exactly those two rejected values. Every consumer reads durability as a BOOLEAN
# (acquisition gates a vault belief on it, cut adds a flat salience bonus, arc tests `== "durable"`),
# so there was never a gradation to preserve. docs/standard-vectors.md:144 fixes the vocabulary at
# two values and line 480 lists following the older docs as a known trap.
def is_durable(tags):
    """True when this turn's self-report marks it as leaving a lasting trace.

    The single definition. `acquisition.assess`, `acquisition.witness_belief` and `cut._salience`
    all call this; none of them may re-spell the vocabulary.
    """
    if not isinstance(tags, dict):
        return False
    return str(tags.get("durability", "transient")) == "durable"


# The codes that set ok=False. A driver refusing a beat names one of THESE, never a soft flag —
# a beat carrying only soft flags is narrowed and still moves state.
_HARD_TAG_CODES = frozenset([
    "TAG_TYPE_UNKNOWN",
    "TAG_DIMENSIONS_TYPE",
    "TAG_DIMENSION_VALUE_NOT_NUMERIC",
    "TAG_DIMENSION_VALUE_RANGE",
    "TAG_DURABILITY_MISSING",
    "TAG_DURABILITY_INVALID",
    "TAG_CONFIDENCE_NOT_NUMERIC",
    "TAG_CONFIDENCE_RANGE",
])


def _flag(code, detail):
    """One validation finding, as STRUCTURE rather than prose.

    Flags used to be sentences, which forced `faults.reason_key` to recover their meaning with four
    regexes and drop everything they missed into a bucket `_ACTIONABLE` excluded — so the
    fault-miner counted the recurring reason and threw it away, printing "(none — the vocabulary fit
    this run)" while every beat of a live scene was being discarded. The code IS the structure now.

    Serialised into `turns.validation` as JSON and read back by `faults.scan_run`, so it must stay a
    plain dict: a class would need an encoder on both sides of sqlite.
    """
    return {"code": code, "detail": detail}


def render_flag(flag):
    """A flag -> one operator-readable line. Accepts the legacy string shape so a stored
    validation blob written before 2026-08-30 still renders."""
    if isinstance(flag, dict):
        return "[%s] %s" % (flag.get("code", "?"), flag.get("detail", ""))
    return str(flag)


def flag_code(flag):
    """A flag -> its code, or None for a legacy string flag."""
    return flag.get("code") if isinstance(flag, dict) else None


def tag_refusal(validation, who, turn):
    """A failed verdict -> the (code, detail) pair a driver raises with.

    ONE builder for all three drivers (scripts/scene.py, scripts/direct.py,
    tests/coherence_probe.py). Those three used to hold byte-identical copies of
    `applied = {"dimensions": {}}`, and the third lives in the file CLAUDE.md designates the
    permanent real-model regression — so the silent discard would have survived precisely in the
    tool used to verify it was gone.

    Names a HARD code where one exists: a soft flag never refuses a beat.
    """
    flags = validation.get("flags") or []
    hard = [f for f in flags if flag_code(f) in _HARD_TAG_CODES]
    first = hard[0] if hard else (flags[0] if flags else None)
    code = flag_code(first) or "TAG_TYPE_UNKNOWN"
    detail = first.get("detail", "") if isinstance(first, dict) else str(first or "no flag recorded")
    lines = [
        "%s at turn %s: %s" % (who, turn, detail),
        "  every finding: %s" % "; ".join(render_flag(f) for f in flags),
        "  The beat is refused and nothing is committed. Before 2026-08-30 this silently set",
        "  applied = {'dimensions': {}}: no affect moved, no arc row was written, no bond moved,",
        "  every listener's salience was 0.0 and the scene lulled - while the operator line",
        "  printed the RAW tags, so the beat read as healthy. Three runs burned that way.",
    ]
    return code, "\n".join(lines)


class TagError(EngineError):
    """An actor's self-reported tags failed the hard schema contract.

    Raised by the CONSUMERS (scripts/scene.py, scripts/direct.py, tests/coherence_probe.py), never
    by `validate_tags` itself — ~25 tests assert on the verdict dict and two non-scene callers
    consume it rather than an exception, so the validator stays pure and the drivers refuse.
    """



# ---- Class-B constants — documented provenance, probe-calibrated. ----

# Mismatch threshold: only flag a dim-type mismatch when the claimed dim value
# is >= this threshold.  Below it = "background presence" (the scene carries the
# ambient dimension even though the actor's ACT type doesn't drive it).
# Rationale: the probe's mundane stubs carry hint dims like {care_relevant: 0.2,
# loss: 0.3} — these reflect objective scene context, not the actor's TYPE claim.
# The type ("mundane") is the actor's classification of their own ACT; a background
# dim at < 0.5 is not a mismatch, just scene colour.  At >= 0.5 the dim is a primary
# driver and the actor should have picked a different type -> mismatch.
# Pre-flight requirement: 25 EVENTS stubs pass clean (no escalation at default 0.5).
# Highest background dim in the stubs: {care_relevant: 0.5} on event 21 (threat kind —
# care_relevant IS in threat's appraisal_map so no mismatch).  On mundane events the
# highest background is {mastery: 0.3, threat: 0.2, loss: 0.3} — all < 0.5. Correct.
# Source: probe-calibrated (consolidation-loop.md open-q 2, pre-flight clause).
_MISMATCH_THRESHOLD = 0.5   # Class-B, probe-calibrated start.

# Cap multiplier applied to self-rated confidence per soft-fail.
# Rule: each soft-fail multiplies the running confidence by SOFT_FAIL_CAP_FACTOR.
# Rationale: one containment or capability miss is a partial invalidation; 0.65 maps
# a 0.9 self-rating down to ~0.585 after one miss, well below THETA_CONF (0.70),
# triggering escalation — the behaviour the pre-flight test requires.
# Two misses: 0.9 * 0.65^2 = 0.38 — clearly escalated.
# Zero misses: confidence unchanged — clean-tag stub runs at their self-rated value.
# Source: consolidation-loop.md open-q 2 RESOLVED + probe-plan calibration session.
SOFT_FAIL_CAP_FACTOR = 0.65   # Class-B, probe-calibrated start.

# Escalation threshold.
# Chosen so:
#   (a) a clean-tag (confidence default 0.5, zero soft-fails) does NOT escalate:  0.5 >= 0.45 ✓
#   (b) a single containment flag on default 0.5: 0.5 * 0.65 = 0.325 < 0.45 → escalates ✓
#   (c) self-rated 0.9, zero flags: 0.9 >= 0.45 → no escalate ✓
#   (d) self-rated 0.9, one flag: 0.9 * 0.65 = 0.585 >= 0.45 — still not escalated.
#       Therefore escalation only fires when confidence is low OR misses stack.
#       A 0.9-rated tag needs two soft-fails to cross the line:
#       0.9 * 0.65^2 = 0.38 < 0.45 → escalate.
#       This is the correct calibration: a single miss on a high-confidence tag is
#       flagged in the flags list but does not escalate; two misses do.
# Source: consolidation-loop.md open-q 2 + probe EVENTS stub distribution.
THETA_CONF = 0.45   # Class-B, probe-calibrated start.

# ---------------------------------------------------------------------------
# The Event Catalog — one artifact, four jobs (record-contract.md §event catalog).
#
# Keys: event-type name string.
# Rows:
#   appraisal_map  list[str]  — dims that legitimately fire for this type
#                               (other dims soft-flag as type-mismatch)
#   world_map      str        — snapshot fields moved by fold (ledger._project),
#                               or "none" for appraisal-only types
#   visibility     str        — "public" | "private-to-actor"
#   capability_req dict|None  — {skill: str, min: float} optional; None = no req
#
# Provenance tags (per row):
#   [probe] = coherence_probe.py EVENTS kind / calibration prompt type vocabulary
#   [ledger] = ledger.py _project etype branch
#   [loop] = consolidation-loop.md pipeline vocabulary
#   [contract] = record-contract.md event catalog name list
#   [loop-oq3] = consolidation-loop.md open-q 3 (compensating-event path)
# ---------------------------------------------------------------------------
CATALOG = {

    # ---- probe appraisal-only types (world_map = "none") ---- [probe] [ledger]

    "mundane": {
        # Routine event — low-stakes action, world not changed. [probe] [ledger]
        # `attraction` here: desire most often surfaces in an ORDINARY moment, not a dramatic one.
        "appraisal_map":   ["mastery", "relief", "attraction"],
        "world_map":       "none",
        "visibility":      "public",
        "capability_req":  None,
    },

    "care": {
        # A care-relevant act or outcome (aid to another, recovery, protection). [probe] [loop]
        "appraisal_map":   ["care_relevant", "relief", "mastery"],
        "world_map":       "none",
        "visibility":      "public",
        "capability_req":  None,
    },

    "loss": {
        # A loss event — death, permanent departure, irreversible damage. [probe] [ledger] [contract]
        "appraisal_map":   ["loss", "care_relevant", "social_violation"],
        "world_map":       "none",
        "visibility":      "public",
        "capability_req":  None,
    },

    "threat": {
        # An externally sourced threat — danger, urgency, physical risk. [probe] [ledger] [loop]
        "appraisal_map":   ["threat", "care_relevant", "loss"],
        "world_map":       "none",
        "visibility":      "public",
        "capability_req":  None,
    },

    # ---- interpersonal action types (world_map = named fold field) ----

    "aid": {
        # Actor helps another. care_relevant is primary; mastery fires (skill execution); [loop] [contract]
        "appraisal_map":   ["care_relevant", "mastery", "relief"],
        "world_map":       "none",      # pure appraisal; fold effect surfaces via bond/harm resolution
        "visibility":      "public",
        "capability_req":  None,        # kept minimal — any character can attempt aid
    },

    "affront": {
        # A social/interpersonal VIOLATION — a slight, an insult, a status move, witnessed disrespect.
        # The actor-taggable home for the social_violation dimension the aristocratic scenes are built on
        # (gate: the engine-fault detector flagged social_violation as having no type to live in). [social]
        # social_violation -> RAGE (the breach), threat -> FEAR (to standing), mastery -> SEEKING
        # (navigating a slight with composure is itself a mastery act, the cutting-but-composed reply).
        "appraisal_map":   ["social_violation", "threat", "mastery"],
        "world_map":       "none",      # pure appraisal -> actor-taggable; erosion rides appraisal/arc, not a fold
        "visibility":      "public",
        "capability_req":  None,
    },

    "threaten": {
        # Actor issues a threat to another. threat + social_violation are primary; [loop] [contract]
        "appraisal_map":   ["threat", "social_violation", "mastery"],
        "world_map":       "tensions",  # a threat raises scene tension (world-dynamics)
        "visibility":      "public",
        "capability_req":  {"skill": "combat", "min": 0.20},
        # Rationale: threatening in a way that lands requires at least minimal capability signal.
    },

    # ---- world-moving fold types (ledger._project branches) ----

    "move": {
        # Actor moves to a new location. ledger._project: agents[actor]["location"] = to. [actor] [ledger] [contract]
        "appraisal_map":   ["mastery", "threat"],   # threat fires if moving toward danger
        "world_map":       "agents.location",
        "visibility":      "public",
        "capability_req":  None,
    },

    "harm": {
        # Actor harms a target (non-terminal or terminal). [ledger] [contract] [loop]
        "appraisal_map":   ["social_violation", "threat", "loss", "care_relevant"],
        "world_map":       "agents.life_status (terminal only)",
        "visibility":      "public",
        "capability_req":  {"skill": "combat", "min": 0.30},
        # Rationale: harming requires physical capability. Min 0.30 — a low-combat actor flags,
    },

    "reveal": {
        # Actor discloses a fact to others. [fact] [ledger] [contract]
        "appraisal_map":   ["social_violation", "mastery", "care_relevant"],
        "world_map":       "information",
        "visibility":      "public",
        "capability_req":  None,
    },

    "seize": {
        # Actor takes control of an asset. [asset] [ledger] [contract]
        "appraisal_map":   ["mastery", "social_violation", "threat"],
        "world_map":       "holdings",
        "visibility":      "public",
        "capability_req":  None,
    },

    "destroy-asset": {
        # Actor destroys an asset permanently. [asset] [ledger] [contract]
        "appraisal_map":   ["loss", "social_violation", "threat"],
        "world_map":       "holdings",
        "visibility":      "public",
        "capability_req":  None,
    },

    "betray": {
        # Actor betrays a relationship. [pair] [ledger] [contract] [loop]
        "appraisal_map":   ["social_violation", "loss", "threat"],
        "world_map":       "relationships",
        "visibility":      "public",
        "capability_req":  None,
    },

    "bond": {
        # Actor forms or deepens a bond. [pair] [ledger] [contract] [loop]
        # `attraction` here (the affiliative event) and DELIBERATELY NOT on threat / harm / seize /
        # threaten: coercion must be AUTHORED as the violation it is, never reached through a
        # dimension the engine hands out on threat events.
        "appraisal_map":   ["care_relevant", "relief", "mastery", "attraction"],
        "world_map":       "relationships",
        "visibility":      "public",
        "capability_req":  None,
    },

    "tension": {
        # A world-tension event — faction conflict, political pressure, environmental stress. [name] [ledger] [contract]
        "appraisal_map":   ["threat", "social_violation", "loss"],
        "world_map":       "tensions",
        "visibility":      "public",
        "capability_req":  None,
    },

    # ---- lifecycle / bookkeeping types ----

    "turn-skipped": {
        # ledger.record_turn_skipped: no action produced; the scene-record must say so. [ledger]
        "appraisal_map":   [],
        "world_map":       "none",
        "visibility":      "public",
        "capability_req":  None,
    },

    "correction": {
        # Compensating event (consolidation-loop.md open-q 3 DESIGNED): append-only [loop-oq3]
        "appraisal_map":   ["social_violation", "relief"],
        "world_map":       "none",      # inverse delta applied by fold, not a direct world-map
        "visibility":      "private-to-actor",
        "capability_req":  None,
    },
}

# THE ACTOR'S TAG VOCABULARY — one derivation, three consumers.
# The pure-appraisal rows (no world fold) that are not the engine's own system records. This lived
# in `prompt.py` and was hand-duplicated in `faults.py`; `validate_tags` meanwhile checked the whole
# CATALOG, so eleven types the actor is never shown were accepted anyway. CLAUDE.md's own list of
# seven hand-maintained duplicates-of-a-source-of-truth says what happens next, so it is derived
# here — beside CATALOG, which is what it derives FROM — and imported by the other two.
SYSTEM_TYPES = ("turn-skipped", "correction")
ACTOR_TAG_TYPES = tuple(sorted(
    name for name, row in CATALOG.items()
    if row.get("world_map") in (None, "none") and name not in SYSTEM_TYPES))

# ---- Internal helpers ----

def _normalize(s):
    """Lowercase, strip common diacritics — same logic as gate.py._normalize.
    gate.py §normalisation: accent-tolerant matching for containment checks."""
    replacements = [
        ("á","a"),("aà","a"),("aâ","a"),("aä","a"),
        ("á","a"),("à","a"),("â","a"),("ä","a"),
        ("é","e"),("è","e"),("ê","e"),("ë","e"),
        ("í","i"),("ì","i"),("î","i"),("ï","i"),
        ("ó","o"),("ò","o"),("ô","o"),("ö","o"),
        ("ú","u"),("ù","u"),("û","u"),("ü","u"),
        ("ý","y"),("ñ","n"),
    ]
    t = str(s).lower()
    for src, dst in replacements:
        t = t.replace(src, dst)
    return t


def _percept_strings(percept):
    """Extract all matchable strings from one Percept dict.

    gate.py _make_percept: {ref, channel, fidelity, attributes, recognized_as?, must_surface}.
    For containment: we search ref + every attribute + recognized_as.
    consolidation-loop.md pipeline: "every referent in the scene's PerceptSet —
    no hallucinated entity/act."
    """
    parts = []
    ref = percept.get("ref", "")
    if ref:
        parts.append(ref)
    for attr in percept.get("attributes", []):
        parts.append(str(attr))
    rec = percept.get("recognized_as")
    if rec:
        parts.append(str(rec))
    return parts


def _is_perceived(target, percepts):
    """Return True if target name appears (substring, accent-tolerant) in the PerceptSet.

    consolidation-loop.md: containment check — tag referent must be in PerceptSet.
    gate.py _normalize: accent/case-insensitive substring ok.
    """
    needle = _normalize(str(target))
    for p in percepts:
        if not isinstance(p, dict):
            continue
        for s in _percept_strings(p):
            if needle in _normalize(s):
                return True
    return False


def compose_confidence(self_rated, flags):
    """Compose self-rated confidence with validation soft-fails.

    Rule (Class-B, probe-calibrated — consolidation-loop.md open-q 2 RESOLVED):
      Each soft-fail multiplies the running confidence by SOFT_FAIL_CAP_FACTOR.
      composite = self_rated * (SOFT_FAIL_CAP_FACTOR ** len(flags))

    Rationale: every flag is independent evidence of a validation gap; they compound
    multiplicatively (not additively) so a high self-rating can still survive one miss
    but not two.  SOFT_FAIL_CAP_FACTOR = 0.65 (documented above).

    Returns float in [0, 1].
    """
    n = len(flags)
    if n == 0:
        return float(self_rated)
    composite = float(self_rated) * (SOFT_FAIL_CAP_FACTOR ** n)
    # clamp — should already be in [0,1] given valid self_rated, but be explicit
    return max(0.0, min(1.0, composite))


# ---- Public API ----

def validate_tags(tags, percepts, skills):
    """Mechanical validation of actor self-reported event-tags (the keystone guard).

    consolidation-loop.md pipeline:
      schema-conformance (hard) -> containment (soft) -> capability (soft)
      -> compose_confidence -> escalate if composite < THETA_CONF

    Parameters
    ----------
    tags     : dict  {type, summary?, dimensions: {dim: 0..1}, durability,
                      target?, confidence?}
               confidence: self-rated 0..1; default 0.5 when absent
               (consolidation-loop.md: "the actor knows when its act was ambiguous")
    percepts : list  PerceptSet — list of Percept dicts from scene.assemble
                     (gate.py _make_percept: {ref, channel, fidelity, attributes,
                     recognized_as?, must_surface})
    skills   : dict  baseline.skills {skill_name: float 0..1}
               (character-schema.md baseline.skills)

    Returns
    -------
    {
      "ok"        : bool   — hard schema conformance (all fields valid)
      "flags"     : [str]  — soft-fail messages; empty on a clean tag
      "confidence": float  — composite: self-rated capped by validation
      "escalate"  : bool   — composite < THETA_CONF (critic flag)
    }

    Raises ValueError on malformed inputs (non-dict tags, non-list percepts,
    non-dict skills). A well-formed tag that fails validation returns ok=False /
    flags — does NOT raise (a rejected tag is data, not an exception).
    """
    # ---- fail-loud on malformed inputs (not tag-content failures) ----
    if not isinstance(tags, dict):
        raise ValueError("validate_tags: tags must be a dict, got %r" % type(tags).__name__)
    if not isinstance(percepts, list):
        raise ValueError("validate_tags: percepts must be a list, got %r" % type(percepts).__name__)
    if not isinstance(skills, dict):
        raise ValueError("validate_tags: skills must be a dict, got %r" % type(skills).__name__)

    ok    = True
    flags = []

    # ---- 1. Schema-conformance (hard — ok=False on any failure) ----
    # consolidation-loop.md: "tags in event vocabulary" (Principle 3: typed schema).

    # 1a. type must be in CATALOG
    tag_type = tags.get("type")
    # OPEN, NOT CLOSED (2026-08-29). CATALOG holds 17 types; the prompt offers an actor 6. The
    # other 11 are accepted here, and a plausible free-text `move` — never offered, natural for
    # "stepped toward the door" — reaches ledger._project's move branch, which needs only a truthy
    # actor, and nulls the character's location. Narrowing this to ACTOR_TAG_TYPES was tried and
    # REVERTED: `betray` carries a world_map and so falls outside the actor set, but the bond tier
    # (bonds.act_from_tags, tests/test_bonds.py) fires on precisely that type — so the narrow check
    # breaks a documented mechanism. Where a `betray` tag legitimately ORIGINATES (actor self-report
    # vs. the recorder role) is a design question, and the observed harm so far is a constructed
    # case rather than a production event. A soft flag naming the gap is the honest interim.
    if tag_type not in CATALOG:
        ok = False
        flags.append(_flag("TAG_TYPE_UNKNOWN",
                          "unknown type %r (not in CATALOG)" % tag_type))
    elif tag_type not in ACTOR_TAG_TYPES:
        flags.append(_flag("TAG_TYPE_NOT_ACTOR_OFFERED",
                          "type %r is in CATALOG but is never offered to an actor (offered: %s) — "
                          "it folds to the world unchecked (not invalidating)"
                          % (tag_type, ", ".join(ACTOR_TAG_TYPES))))

    # 1b. dimensions must be a dict with known dim names and values in [0, 1]
    dimensions = tags.get("dimensions", {})
    if not isinstance(dimensions, dict):
        ok = False
        flags.append(_flag("TAG_DIMENSIONS_TYPE",
                          "dimensions must be a dict, got %r" % type(dimensions).__name__))
        dimensions = {}
    else:
        for dim, val in dimensions.items():
            if dim not in _KNOWN_DIMS:
                # FLAG, do not invalidate. An unknown KEY is a reporting error; the rest of the
                # block is still usable, and `state.appraise` already ignores a dimension it does
                # not recognise ("future-proof; new consolidation dims won't crash"). The validator
                # was the only half of the engine treating this as fatal.
                #
                # Why it mattered, measured on a live run 2026-08-23: ok=False makes
                # scripts/scene.py set `applied = {"dimensions": {}}`, discarding the WHOLE
                # appraisal including every valid dimension present. It happened on both beats of
                # one scene for two different reasons — `attraction` (valid, missing from this
                # module's then-hand-copied dimension list) and `{"debt", "respect"}` (the
                # `tags.social` EDGE axes put in the dimensions slot). Neither turn moved any
                # affect, so the listener had no salience and the scene lulled at urge -0.183
                # where a plausible reply computes +0.474.
                #
                # Flagging routes it into scripts/scene.py's `elif validation["flags"]` branch,
                # which narrows dimensions to the event TYPE's appraisal_map — so the unknown key
                # is dropped, the valid ones survive, and the drop is recorded in the validation
                # blob committed to the ledger rather than happening silently.
                flags.append(_flag("TAG_DIMENSION_UNKNOWN",
                                  "unknown dimension %r (dropped; not invalidating)" % dim))
            else:
                try:
                    fval = float(val)
                except (TypeError, ValueError):
                    ok = False
                    flags.append(_flag("TAG_DIMENSION_VALUE_NOT_NUMERIC",
                                      "dimension %r value %r not numeric" % (dim, val)))
                    continue
                if not (0.0 <= fval <= 1.0):
                    ok = False
                    flags.append(_flag("TAG_DIMENSION_VALUE_RANGE",
                                      "dimension %r value %r outside [0, 1]" % (dim, val)))

    # 1c. durability must be in the valid set
    durability = tags.get("durability")
    if durability is None:
        ok = False
        flags.append(_flag("TAG_DURABILITY_MISSING",
                           "durability is absent; it must be one of {transient, durable}. "
                           "NOTE: older docs suggested 'marking'/'reshaping' — those were never a "
                           "third and fourth grade, every consumer reads durability as a boolean "
                           "(standard-vectors.md:144)."))
    elif durability not in _VALID_DURABILITY:
        ok = False
        flags.append(_flag("TAG_DURABILITY_INVALID",
                           "durability %r not in {transient, durable}" % durability))

    # 1d. confidence (self-rated) must be in [0, 1] if present
    raw_conf = tags.get("confidence")
    if raw_conf is None:
        self_rated = 0.5   # default: consolidation-loop.md open-q 2 RESOLVED
    else:
        try:
            self_rated = float(raw_conf)
        except (TypeError, ValueError):
            ok = False
            flags.append(_flag("TAG_CONFIDENCE_NOT_NUMERIC",
                               "confidence %r not numeric" % raw_conf))
            self_rated = 0.5
        else:
            if not (0.0 <= self_rated <= 1.0):
                ok = False
                flags.append(_flag("TAG_CONFIDENCE_RANGE",
                                   "confidence %r outside [0, 1]" % raw_conf))
                self_rated = max(0.0, min(1.0, self_rated))

    # ---- 2. Soft checks (flags only — do not set ok=False) ----
    # consolidation-loop.md: "fail -> reject/flag; low-confidence -> escalate"

    # Short-circuit soft checks if the type is unknown (no catalog row to read)
    row = CATALOG.get(tag_type)
    soft_flags = []

    if row is not None:
        # 2a. Containment: tag target (if any) must appear in the PerceptSet.
        # consolidation-loop.md pipeline: "every referent in the scene's PerceptSet —
        # no hallucinated entity/act".  gate.py: accent/case-insensitive substring ok.
        # The actor is asked for `tags.subject` (prompt.py) — never `tags.target`. `target` is a
        # RESOLVED id the callers merge onto `applied`, a SEPARATE dict, after this function has
        # already run. So `tags.get("target")` was always absent and this containment check never
        # once ran on real data; its tests passed because the fixture sets `target` by hand.
        target = tags.get("subject") or tags.get("target")
        if target:
            if not _is_perceived(target, percepts):
                soft_flags.append(_flag("TAG_TARGET_NOT_PERCEIVED",
                                        "target %r not perceived in PerceptSet" % target))

        # 2b. Dimension-type mismatch: dims claimed but NOT in catalog's appraisal_map
        # AND value >= _MISMATCH_THRESHOLD (a primary driver, not background scene colour).
        # consolidation-loop.md Principle 3: typed schema — each type maps to specific dims.
        # Soft-flag only when the dim is a primary driver (>= 0.5).  Background dims
        # (< 0.5) reflect objective scene context; the TYPE names the actor's ACT,
        # not the ambient scene.  Pre-flight requires the 25 EVENTS stubs pass cleanly.
        allowed = set(row["appraisal_map"])
        for dim, val in dimensions.items():
            if dim not in _KNOWN_DIMS:
                continue   # already flagged in schema check; skip
            try:
                fval = float(val)
            except (TypeError, ValueError):
                continue   # already flagged in schema check
            if allowed and dim not in allowed and fval >= _MISMATCH_THRESHOLD:
                soft_flags.append(_flag("TAG_DIMENSION_NOT_IN_APPRAISAL_MAP",
                                        "dimension %r (%.2f) not in appraisal_map for type %r "
                                        "(legitimate dims: %s)"
                                        % (dim, fval, tag_type, sorted(allowed))))

        # 2c. Capability: actor's skill below the catalog row's minimum requirement.
        # consolidation-loop.md pipeline: "capability (the actor could do it — in-skill,
        # in-reach)".  character-schema.md baseline.skills.
        cap_req = row.get("capability_req")
        if cap_req:
            skill_name = cap_req["skill"]
            min_val    = float(cap_req["min"])
            actor_val  = float(skills.get(skill_name, 0.0))
            if actor_val < min_val:
                soft_flags.append(_flag("TAG_CAPABILITY_BELOW_REQ",
                                        "skill %r = %.2f < required %.2f for type %r"
                                        % (skill_name, actor_val, min_val, tag_type)))

    flags.extend(soft_flags)

    # ---- 3. Compose confidence ----
    composite = compose_confidence(self_rated, soft_flags)

    # ---- 4. Escalate ----
    escalate = composite < THETA_CONF

    return {
        "ok":         ok,
        "flags":      flags,
        "confidence": composite,
        "escalate":   escalate,
    }
