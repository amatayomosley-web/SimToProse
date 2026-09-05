"""profiles.py ? the formative profiles library and composition gate.

`docs/composition-pass.md` is normative:
  - Phase A: classify backstory -> profile picks (LLM, generation-time, 1x/char)
  - Phase B: compose prior + sum(weight * diffs) -> baseline (Deterministic script)

This module holds the ENGINE-owned canonical formative profiles library, the admission
gate for proposed profiles (cosine separability < 0.95, active schema check, bounded diffs),
and the composition arithmetic enforcing the +-0.35 stacked movement cap.

Stdlib only. Under 500 lines per CLAUDE.md Rule 6.
"""
import json
import math
import os
from .records import PRIMARIES
from .errors import EngineError

# Active engine baseline fields that formative diffs are permitted to touch.
# Prevents authored-but-inert dead fields (docs/composition-pass.md:59-61).
VALID_BASELINE_FIELDS = {
    # HEXACO traits (state.py:270)
    "honesty_humility", "emotionality", "extraversion",
    "agreeableness", "conscientiousness", "openness",
    # Panksepp resting primaries (records.py:PRIMARIES)
    "SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY", "DISGUST",
    # SDT needs (character-anatomy.md:8)
    "relatedness", "competence", "autonomy",
    # Schwartz values (reference-species-prior.md:77-88)
    "benevolence", "self_direction", "universalism", "security", "conformity",
    "achievement", "hedonism", "tradition", "stimulation", "power",
    # Moral foundations (reference-species-prior.md:96-103)
    "care_harm", "fairness", "liberty", "loyalty", "authority", "sanctity",
    # Skills & relationship priors (reference-species-prior.md:118-121)
    "default_trust", "perception", "insight", "combat"
}

# Caps (docs/composition-pass.md:62-64, docs/decision-engine.md:107-111)
MAX_DIFF_MAGNITUDE = 0.35
MAX_LEVER_MULTIPLIER = 2.5
MAX_LEVER_ADDITIVE = 0.35
MAX_COSINE_SIMILARITY = 0.95


def _load_library():
    """Load canonical profile definitions from data/formative_profiles.json."""
    pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(pkg_dir, "data", "formative_profiles.json")
    if not os.path.exists(data_path):
        return {}
    with open(data_path, "r", encoding="utf-8") as f:
        profiles_list = json.load(f)
    return {p["id"]: p for p in profiles_list}


LIBRARY = _load_library()


def available(library=None):
    """Sorted list of available profile IDs in the library."""
    lib = library if library is not None else LIBRARY
    return sorted(lib.keys())


def get(profile_id, library=None):
    """Retrieve a profile by ID. Fails loud if unknown."""
    lib = library if library is not None else LIBRARY
    if profile_id not in lib:
        raise EngineError("PROFILES_AVAILABLE_UNKNOWN", "Unknown profile ID: %r (available: %s)" % (profile_id, sorted(lib.keys())))
    return dict(lib[profile_id])


def categories(library=None):
    """Map of category -> list of profile IDs."""
    lib = library if library is not None else LIBRARY
    cats = {}
    for pid, p in sorted(lib.items()):
        c = p.get("category", "uncategorized")
        cats.setdefault(c, []).append(pid)
    return cats


def validate_profile(profile):
    """Assert that a profile meets all normative structural and bounding contracts."""
    if not isinstance(profile, dict):
        raise EngineError("PROFILES_PROFILE_NOT_A_DICT", "Profile must be a dict, got %r" % type(profile).__name__)
    for key in ("id", "name", "category", "baseline_diffs"):
        if key not in profile:
            raise EngineError("PROFILES_MISSING", "Profile missing required key: %r" % key)

    diffs = profile.get("baseline_diffs", {})
    if not isinstance(diffs, dict):
        raise EngineError("PROFILES_BASELINE_DIFFS_NOT_A_DICT", "baseline_diffs must be a dict")
    for field, delta in diffs.items():
        if field not in VALID_BASELINE_FIELDS:
            raise EngineError("PROFILES_BASELINE_DIFFS_CONTAINS_INVALID", "baseline_diffs contains unconsumed/invalid field: %r" % field)
        if not isinstance(delta, (int, float)):
            raise EngineError("PROFILES_DIFF_NUMERIC_NOT_NUMERIC", "diff for %r must be numeric, got %r" % (field, delta))
        if abs(delta) > MAX_DIFF_MAGNITUDE + 1e-6:
            raise EngineError("PROFILES_DIFF_F_INVALID", "diff for %r (%f) exceeds max magnitude +-0.35" % (field, delta))

    for r in profile.get("catalog_rows", []):
        if not isinstance(r, dict):
            raise EngineError("PROFILES_CATALOG_ROW_NOT_A_DICT", "catalog_row must be a dict")
        if "lever" not in r or r["lever"] not in PRIMARIES:
            raise EngineError("PROFILES_CATALOG_ROW_LEVER_INVALID", "catalog_row lever must be one of %s, got %r" % (PRIMARIES, r.get("lever")))
        op = r.get("op", "x")
        if op not in ("x", "+"):
            raise EngineError("PROFILES_CATALOG_ROW_OP_INVALID", "catalog_row op must be 'x' or '+', got %r" % op)
        mag = r.get("magnitude")
        if not isinstance(mag, (int, float)):
            raise EngineError("PROFILES_CATALOG_ROW_MAGNITUDE_NOT_NUMERIC", "catalog_row magnitude must be numeric")
        if op == "x" and mag > MAX_LEVER_MULTIPLIER:
            raise EngineError("PROFILES_CATALOG_ROW_MULTIPLIER_INVALID", "catalog_row multiplier (%f) exceeds max 2.5" % mag)
        if op == "+" and mag > MAX_LEVER_ADDITIVE:
            raise EngineError("PROFILES_CATALOG_ROW_ADDITIVE_INVALID", "catalog_row additive (%f) exceeds max 0.35" % mag)

    return True


def _vectorize(profile):
    """Sparse baseline_diffs dict -> fixed dense vector over sorted VALID_BASELINE_FIELDS."""
    fields = sorted(VALID_BASELINE_FIELDS)
    diffs = profile.get("baseline_diffs", {})
    return [float(diffs.get(f, 0.0)) for f in fields]


def similarity(p1, p2):
    """Cosine similarity between two profiles over their baseline_diffs vector space."""
    v1 = _vectorize(p1)
    v2 = _vectorize(p2)
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def separability(proposal, library=None):
    """Max cosine similarity of proposal against any existing profile in library."""
    lib = library if library is not None else LIBRARY
    if not lib:
        return 0.0
    return max(similarity(proposal, p) for p in lib.values())


def admit(proposal, library=None):
    """Admission gate (docs/composition-pass.md:52-66).

    Returns (admitted: bool, reason: str).
    """
    lib = library if library is not None else LIBRARY
    try:
        validate_profile(proposal)
    except ValueError as e:
        return False, "Schema rejection: %s" % e

    # Gate 1: Separability / Deduplication
    max_sim = separability(proposal, lib)
    if max_sim >= MAX_COSINE_SIMILARITY:
        return False, "Duplicate rejection: cosine similarity %0.3f >= %0.2f to existing profile" % (max_sim, MAX_COSINE_SIMILARITY)

    return True, "Admitted (max similarity %0.3f)" % max_sim


def compose(prior, picks, library=None):
    """Evaluate baseline[field] = clamp(prior[field] + sum(w * profile.diffs[field])).

    Strictly enforces the +-0.35 stacked movement cap across all picks from species prior.
    docs/composition-pass.md:62-64, 79-85.
    """
    lib = library if library is not None else LIBRARY
    if not isinstance(prior, dict):
        raise EngineError("PROFILES_PRIOR_NOT_A_DICT", "prior must be a dict")
    if not isinstance(picks, (list, tuple)):
        raise EngineError("PROFILES_PICKS_NOT_A_LIST", "picks must be a list or tuple")

    # Accumulate raw weighted diffs per field
    deltas = {}
    for pick in picks:
        if not isinstance(pick, dict) or "profile" not in pick:
            raise EngineError("PROFILES_INVALID", "Malformed pick: %r" % pick)
        pid = pick["profile"]
        weight = float(pick.get("weight", 1.0))
        if weight < 0.0 or weight > 1.0:
            raise EngineError("PROFILES_PICK_WEIGHT_INVALID", "Pick weight must be in [0.0, 1.0], got %f" % weight)
        p = get(pid, lib)
        for f, d in p.get("baseline_diffs", {}).items():
            deltas[f] = deltas.get(f, 0.0) + weight * float(d)

    # Compose, clamp to +-0.35 from prior, then clamp to [0.0, 1.0]
    out = dict(prior)
    for field, delta in deltas.items():
        base = float(prior.get(field, 0.50))
        # Cap total movement at +-0.35 from prior
        capped_delta = max(-MAX_DIFF_MAGNITUDE, min(MAX_DIFF_MAGNITUDE, delta))
        out[field] = round(max(0.0, min(1.0, base + capped_delta)), 4)

    return out


# ---------------------------------------------------------------------------
# PLACEMENT — where a composed field actually lands on a character
# ---------------------------------------------------------------------------
# `compose` is a FLAT computation and correct as one: the caps and the similarity metric both
# operate on a flat vector. But a character is NESTED, and the consumers read nested paths:
#   baseline.temperament.<PRIMARY>.mean   -> state.build_profile (decay target, direction marker)
#   baseline.traits.<facet>.mean          -> state.build_profile (HEXACO slopes on the gains)
#   baseline.model.<ns>.<field>           -> state._relevance (which events land hard)
#   baseline.skills.<skill>               -> the deterministic checks
#   baseline.relationship_priors.<field>  -> edge defaults
#
# Writing the flat result straight onto `baseline` left those untouched and added dead siblings:
# measured on a real character, the composed values sat next to the originals and build_profile
# went on reading the originals. That is the authored-but-inert defect, and it was silent.
#
# A field with NO known path RAISES. Writing it somewhere unread is the bug being fixed here.

_SCHWARTZ = ("benevolence", "self_direction", "universalism", "security", "conformity",
             "achievement", "hedonism", "tradition", "stimulation", "power")
_FOUNDATIONS = ("care_harm", "fairness", "liberty", "loyalty", "authority", "sanctity")
_NEEDS = ("relatedness", "competence", "autonomy")
_HEXACO = ("honesty_humility", "emotionality", "extraversion",
           "agreeableness", "conscientiousness", "openness")
_SKILLS = ("perception", "insight", "combat")


def path_for(field):
    """A composed field name -> the nested path a consumer reads. Raises on an unknown field."""
    if field in PRIMARIES:
        # the MEAN, not a starting affect: guide-content.md — "the mean IS the personality's
        # resting face; an anxious character = high FEAR mean, not high starting affect".
        return ("baseline", "temperament", field, "mean")
    if field in _HEXACO:
        return ("baseline", "traits", field, "mean")
    if field in _SCHWARTZ:
        return ("baseline", "model", "schwartz", field)
    if field in _FOUNDATIONS:
        return ("baseline", "model", "moral_foundations", field)
    if field in _NEEDS:
        return ("baseline", "model", "needs", field)
    if field in _SKILLS:
        return ("baseline", "skills", field)
    if field == "default_trust":
        return ("baseline", "relationship_priors", "default_trust")
    raise EngineError("PROFILES_PROFILESPATH_FOR_ENGINE_PATH_INVALID", "profiles.path_for: no engine path for %r - a composed value with nowhere to "
                     "go must fail loud, never be written where nothing reads it" % (field,))


def _read(char, path):
    node = char
    for k in path:
        if not isinstance(node, dict) or k not in node:
            return None
        node = node[k]
    return node


def _write(char, path, value):
    node = char
    for k in path[:-1]:
        nxt = node.get(k)
        if not isinstance(nxt, dict):
            nxt = {}
            node[k] = nxt
        node = nxt
    node[path[-1]] = value


def prior_from(char):
    """The character's CURRENT values as a flat dict, for compose() to diff from.

    A field the sheet does not carry reads 0.50 — guide-content.md's rule that a missing key is
    neutral, not zero.
    """
    out = {}
    for field in sorted(VALID_BASELINE_FIELDS):
        v = _read(char, path_for(field))
        out[field] = float(v) if isinstance(v, (int, float)) else 0.50
    return out


def place(char, composed):
    """Write a composed FLAT result onto the character at the paths the engine reads. Mutates."""
    if not isinstance(char, dict) or not isinstance(composed, dict):
        raise EngineError("PROFILES_PLACE_CHAR_COMPOSED_INVALID", "place: char and composed must both be dicts")
    for field, value in sorted(composed.items()):
        _write(char, path_for(field), round(float(value), 4))
    return char
