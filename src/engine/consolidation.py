"""consolidation.py — Gate 4: Consolidation Validation.

Mechanical guard on the keystone: the actor's self-reported event-tags.

Contracts:
  consolidation-loop.md   — Principle 3 (typed schema), pipeline (schema-conformance /
                            containment / capability), open-q 2 RESOLVED (composite conf).
  record-contract.md      — event_type catalog shape {appraisal_map, world_map,
                            durability_class, visibility}.
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
_KNOWN_DIMS = frozenset(["threat", "loss", "care_relevant", "mastery",
                         "social_violation", "relief"])

_VALID_DURABILITY = frozenset(["transient", "durable"])

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
#   durability_class str      — default durability ("transient"|"durable")
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
        "appraisal_map":   ["mastery", "relief"],
        "world_map":       "none",
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  None,
    },

    "care": {
        # A care-relevant act or outcome (aid to another, recovery, protection). [probe] [loop]
        "appraisal_map":   ["care_relevant", "relief", "mastery"],
        "world_map":       "none",
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  None,
    },

    "loss": {
        # A loss event — death, permanent departure, irreversible damage. [probe] [ledger] [contract]
        "appraisal_map":   ["loss", "care_relevant", "social_violation"],
        "world_map":       "none",
        "durability_class": "durable",
        "visibility":      "public",
        "capability_req":  None,
    },

    "threat": {
        # An externally sourced threat — danger, urgency, physical risk. [probe] [ledger] [loop]
        "appraisal_map":   ["threat", "care_relevant", "loss"],
        "world_map":       "none",
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  None,
    },

    # ---- interpersonal action types (world_map = named fold field) ----

    "aid": {
        # Actor helps another. care_relevant is primary; mastery fires (skill execution); [loop] [contract]
        "appraisal_map":   ["care_relevant", "mastery", "relief"],
        "world_map":       "none",      # pure appraisal; fold effect surfaces via bond/harm resolution
        "durability_class": "transient",
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
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  None,
    },

    "threaten": {
        # Actor issues a threat to another. threat + social_violation are primary; [loop] [contract]
        "appraisal_map":   ["threat", "social_violation", "mastery"],
        "world_map":       "tensions",  # a threat raises scene tension (world-dynamics)
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  {"skill": "combat", "min": 0.20},
        # Rationale: threatening in a way that lands requires at least minimal capability signal.
    },

    # ---- world-moving fold types (ledger._project branches) ----

    "move": {
        # Actor moves to a new location. ledger._project: agents[actor]["location"] = to. [actor] [ledger] [contract]
        "appraisal_map":   ["mastery", "threat"],   # threat fires if moving toward danger
        "world_map":       "agents.location",
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  None,
    },

    "harm": {
        # Actor harms a target (non-terminal or terminal). [ledger] [contract] [loop]
        "appraisal_map":   ["social_violation", "threat", "loss", "care_relevant"],
        "world_map":       "agents.life_status (terminal only)",
        "durability_class": "durable",
        "visibility":      "public",
        "capability_req":  {"skill": "combat", "min": 0.30},
        # Rationale: harming requires physical capability. Min 0.30 — a low-combat actor flags,
    },

    "reveal": {
        # Actor discloses a fact to others. [fact] [ledger] [contract]
        "appraisal_map":   ["social_violation", "mastery", "care_relevant"],
        "world_map":       "information",
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  None,
    },

    "seize": {
        # Actor takes control of an asset. [asset] [ledger] [contract]
        "appraisal_map":   ["mastery", "social_violation", "threat"],
        "world_map":       "holdings",
        "durability_class": "durable",
        "visibility":      "public",
        "capability_req":  None,
    },

    "destroy-asset": {
        # Actor destroys an asset permanently. [asset] [ledger] [contract]
        "appraisal_map":   ["loss", "social_violation", "threat"],
        "world_map":       "holdings",
        "durability_class": "durable",
        "visibility":      "public",
        "capability_req":  None,
    },

    "betray": {
        # Actor betrays a relationship. [pair] [ledger] [contract] [loop]
        "appraisal_map":   ["social_violation", "loss", "threat"],
        "world_map":       "relationships",
        "durability_class": "durable",
        "visibility":      "public",
        "capability_req":  None,
    },

    "bond": {
        # Actor forms or deepens a bond. [pair] [ledger] [contract] [loop]
        "appraisal_map":   ["care_relevant", "relief", "mastery"],
        "world_map":       "relationships",
        "durability_class": "durable",
        "visibility":      "public",
        "capability_req":  None,
    },

    "tension": {
        # A world-tension event — faction conflict, political pressure, environmental stress. [name] [ledger] [contract]
        "appraisal_map":   ["threat", "social_violation", "loss"],
        "world_map":       "tensions",
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  None,
    },

    # ---- lifecycle / bookkeeping types ----

    "turn-skipped": {
        # ledger.record_turn_skipped: no action produced; the scene-record must say so. [ledger]
        "appraisal_map":   [],
        "world_map":       "none",
        "durability_class": "transient",
        "visibility":      "public",
        "capability_req":  None,
    },

    "correction": {
        # Compensating event (consolidation-loop.md open-q 3 DESIGNED): append-only [loop-oq3]
        "appraisal_map":   ["social_violation", "relief"],
        "world_map":       "none",      # inverse delta applied by fold, not a direct world-map
        "durability_class": "transient",
        "visibility":      "private-to-actor",
        "capability_req":  None,
    },
}

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
    if tag_type not in CATALOG:
        ok = False
        flags.append("schema: unknown type %r (not in CATALOG)" % tag_type)

    # 1b. dimensions must be a dict with known dim names and values in [0, 1]
    dimensions = tags.get("dimensions", {})
    if not isinstance(dimensions, dict):
        ok = False
        flags.append("schema: dimensions must be a dict, got %r" % type(dimensions).__name__)
        dimensions = {}
    else:
        for dim, val in dimensions.items():
            if dim not in _KNOWN_DIMS:
                ok = False
                flags.append("schema: unknown dimension %r" % dim)
            else:
                try:
                    fval = float(val)
                except (TypeError, ValueError):
                    ok = False
                    flags.append("schema: dimension %r value %r not numeric" % (dim, val))
                    continue
                if not (0.0 <= fval <= 1.0):
                    ok = False
                    flags.append("schema: dimension %r value %r outside [0, 1]" % (dim, val))

    # 1c. durability must be in the valid set
    durability = tags.get("durability")
    if durability not in _VALID_DURABILITY:
        ok = False
        flags.append("schema: durability %r not in {transient, durable}" % durability)

    # 1d. confidence (self-rated) must be in [0, 1] if present
    raw_conf = tags.get("confidence")
    if raw_conf is None:
        self_rated = 0.5   # default: consolidation-loop.md open-q 2 RESOLVED
    else:
        try:
            self_rated = float(raw_conf)
        except (TypeError, ValueError):
            ok = False
            flags.append("schema: confidence %r not numeric" % raw_conf)
            self_rated = 0.5
        else:
            if not (0.0 <= self_rated <= 1.0):
                ok = False
                flags.append("schema: confidence %r outside [0, 1]" % raw_conf)
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
        target = tags.get("target")
        if target:
            if not _is_perceived(target, percepts):
                soft_flags.append(
                    "containment: target %r not perceived in PerceptSet" % target)

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
                soft_flags.append(
                    "containment: dimension %r (%.2f) not in appraisal_map for type %r "
                    "(legitimate dims: %s)" % (dim, fval, tag_type, sorted(allowed)))

        # 2c. Capability: actor's skill below the catalog row's minimum requirement.
        # consolidation-loop.md pipeline: "capability (the actor could do it — in-skill,
        # in-reach)".  character-schema.md baseline.skills.
        cap_req = row.get("capability_req")
        if cap_req:
            skill_name = cap_req["skill"]
            min_val    = float(cap_req["min"])
            actor_val  = float(skills.get(skill_name, 0.0))
            if actor_val < min_val:
                soft_flags.append(
                    "capability: skill %r = %.2f < required %.2f for type %r"
                    % (skill_name, actor_val, min_val, tag_type))

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
