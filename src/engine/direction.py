"""direction.py — numbers to qualitative DIRECTION (gate 5, the backstage guardrail).

design.md: "the engine computes fear 8/10; what enters the prompt is 'gripped by fear' — a
qualitative direction the engine translates from the number. The LLM never sees raw stats;
numbers live in the DB; directions live in the prompt." relevancy-gate.md: "the prose never
says 'spent 3 focus'."

Phrasing is NEUTRAL qualitative description, not prose flourish — narration.md owns voice.
All functions pure, deterministic, stdlib-only, digit-free output (the guardrail test).
"""
from .records import PRIMARIES

# Class-B band edges: four absolute levels per primary. Provenance: design.md direction rule;
# cut points chosen so the probe's resting ranges (0.2-0.6) read as ordinary and the measured
# fever-arc peaks (0.85+) read as gripping. Probe-calibrated start.
_BANDS = (0.25, 0.55, 0.80)   # quiet | present | strong | gripping

# Per-primary phrase tables, one phrase per band (quiet, present, strong, gripping).
# Neutral register: states what the system is doing, never how the scene looks.
# Second person throughout (g6 portability): the prompt addresses the actor as "you", and
# second person carries no gender — no pronoun parameter needed.
_PHRASES = {
    "SEEKING":     ("little pulls at your curiosity", "alert to what comes next",
                    "drawn hard toward what must be done", "consumed by the need to act"),
    "FEAR":        ("settled, unworried", "a watchful edge",
                    "fear pressing close", "gripped by fear, barely holding it"),
    "RAGE":        ("even-tempered", "a thread of irritation",
                    "anger rising and hard to bank", "fury at the edge of control"),
    "LUST":        ("no pull there", "a faint warmth",
                    "desire making itself felt", "want crowding out sense"),
    "CARE":        ("warmth at rest", "care for those near you",
                    "care pulling hard at you", "the need to protect overriding all else"),
    "PANIC_GRIEF": ("steady", "an ache beneath things",
                    "grief dragging at every motion", "hollowed out by loss"),
    "PLAY":        ("no lightness in reach", "room for a small lightness",
                    "an easy playfulness", "giddy, almost unguarded"),
}

_DEV_THRESH = 0.15   # deviation from temperament mean that reads as rising/settling (Class-B, probe-calibrated start)

# Condition bands (energy after allostatic weighting — same read the gate's budget uses).
_COND = ((0.25, "running on nothing, thought coming slow"),
         (0.50, "worn thin"),
         (0.75, "steady enough"),
         (2.00, "rested and clear"))

# Relationship-edge bands per axis (relationships.md axes; same guardrail as affect).
_EDGE_BANDS = (0.25, 0.55, 0.80)
_EDGE_PHRASES = {
    "trust":    ("little trust", "guarded trust", "solid trust", "trust without reservation"),
    "affinity": ("cool toward them", "civil", "fond of them", "deeply attached"),
    "respect":  ("unconvinced by them", "measured regard", "real respect", "looks up to them"),
    "debt":     ("owes them nothing", "a small debt between them", "owes them much", "bound by what is owed"),
}

_SURENESS = ((0.35, "uncertain of it"), (0.65, "fairly sure"), (0.90, "sure"), (2.00, "knows it to the bone"))


def _band(v, edges):
    for i, e in enumerate(edges):
        if v < e:
            return i
    return len(edges)


def _check_num(name, v):
    if not isinstance(v, (int, float)) or not (0.0 <= float(v) <= 1.0):
        raise ValueError("direction: %s must be a number in [0,1], got %r" % (name, v))
    return float(v)


def direct_affect(affect, temperament):
    """Affect vector -> one digit-free, second-person direction line. Surfaces only what is
    NOTABLE: any primary at strong/gripping level, or deviating past _DEV_THRESH from its resting
    mean (with a rising/settling marker) — an anxious baseline must not read as a fresh spike."""
    if not isinstance(affect, dict) or not isinstance(temperament, dict):
        raise ValueError("direction: affect and temperament must be dicts")
    missing = [p for p in PRIMARIES if p not in affect]
    if missing:
        raise ValueError("direction: affect missing primaries: %s" % missing)
    parts = []
    for p in PRIMARIES:
        v = _check_num("affect[%s]" % p, affect[p])
        mean = _check_num("temperament[%s].mean" % p, temperament.get(p, {}).get("mean", 0.5))
        b = _band(v, _BANDS)
        dev = v - mean
        notable = b >= 2 or abs(dev) > _DEV_THRESH
        if not notable:
            continue
        phrase = _PHRASES[p][b]
        if dev > _DEV_THRESH:
            phrase += ", more than is usual for you"
        elif dev < -_DEV_THRESH:
            phrase += ", quieter than your usual"
        parts.append(phrase)
    return "; ".join(parts) if parts else "even-keeled, nothing pressing"


def direct_condition(condition):
    """Condition -> a digit-free line, via the same energy/load read the gate's budget uses."""
    if not isinstance(condition, dict):
        raise ValueError("direction: condition must be a dict")
    energy = _check_num("condition.energy", condition.get("energy", 1.0))
    load = _check_num("condition.allostatic_load", condition.get("allostatic_load", 0.0))
    effective = energy * (1.0 - load * 0.5)   # mirrors gate._energy_budget (one read, two surfaces)
    for edge, phrase in _COND:
        if effective < edge:
            return phrase
    return _COND[-1][1]


def direct_edge(edge):
    """One relationship edge dict -> digit-free standing description (axes per relationships.md)."""
    if not isinstance(edge, dict):
        raise ValueError("direction: edge must be a dict")
    parts = []
    for axis in ("trust", "affinity", "respect", "debt"):
        if axis in edge:
            v = _check_num("edge.%s" % axis, edge[axis])
            parts.append(_EDGE_PHRASES[axis][_band(v, _EDGE_BANDS)])
    return ", ".join(parts) if parts else "no particular standing"


def sureness(confidence):
    """Belief confidence float -> digit-free sureness phrase (recall rendering)."""
    c = _check_num("confidence", confidence)
    for edge, phrase in _SURENESS:
        if c < edge:
            return phrase
    return _SURENESS[-1][1]
