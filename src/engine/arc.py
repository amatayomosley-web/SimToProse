"""arc.py — the Arc Engine: durable baseline change over the story (docs/arc-engine.md).

NOT a new mechanism — appraisal with a DURABLE write. Most events spike current-state and fade
(state-engine.md). An event that is high-impact AND of a reshaping kind crosses a threshold and
writes a sparse DIFF to the BASELINE (temperament means and the bigotry regard) — moving the floor
of who the character is.

RELATIONSHIP EDGES USED TO BE WRITTEN HERE AND ARE NOT ANY MORE (`bonds.py` owns them). The reason is
a cadence mismatch, not a formula: this engine runs once per turn on the ACTOR, and
`relationships.md:5` defines an edge as the PERCEIVER's belief. So when A betrayed B it was **A's**
trust in B that fell — measured 0.80 -> 0.7828 — while B's edge was never computed at all. It also
scaled the damage by resilience, which made a kindness move trust up to 6x further than an equal
betrayal, inverting `relationships.md:27`. Resilience belongs exactly where it still is: on whether a
survival-threat SCARS or STRENGTHENS the person.

`apply` still accepts a `relationships` block. `assess` no longer produces one, but CLAUDE.md hard
rule 2 makes the log append-only and `direct.py` replays stored arc_diffs on resume, so a diff
persisted before this change must rehydrate to the state that run actually had. Backstory and arc are one engine (baseline-generation.md):
generation pre-plays these diffs before page one; the arc runs them during the book.

Same event, damage OR growth — the resilience FORK: low resilience -> a debuff (trauma signature);
high resilience -> a smaller diff or post-traumatic GROWTH. resilience is DERIVED at read time,
never stored (arc-engine.md). Pure, deterministic, stdlib. Diffs persist via ledger.append_arc_diff.
"""
import copy

from .records import PRIMARIES
from .state import _ALLELE

# Class-B, probe-calibrated starts (arc-engine.md: threshold + magnitudes are calibration, not derived).
_ARC_THRESHOLD = 0.18      # durable-magnitude below this -> no baseline diff (most events stay transient)
_DURABLE_DIM   = 0.6       # a dim this severe marks a durable candidate (consolidation calibration: >0.6 = genuinely severe)
_BASE_STEP     = 0.07      # how far a single durable event moves a baseline value (× magnitude, before clamp)
_REGARD_GENERALIZE = 0.4   # a bond with a disregarded-class member erodes the CLASS regard at this fraction of the edge move
_PTG_RESILIENCE = 0.70     # at/above this resilience, a survival-threat writes GROWTH (mastery) not damage (fear)
_ALLELE_MIN, _ALLELE_MAX = 0.75, 1.3


def _clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def _allele(raw):
    return _ALLELE.get(str(raw).split()[0].lower(), 1.0)


def derive_resilience(char, condition):
    """DERIVED, never stored (arc-engine.md): effortful_control × condition × attachment-security.
    (The 4th design field — meaning-frame availability — is a documented TODO; defaulted out here.)
    Returns [0.05, 0.95]."""
    if not isinstance(char, dict) or not isinstance(condition, dict):
        raise ValueError("derive_resilience: char and condition must be dicts")
    geno = char.get("fixed", {}).get("genotype", {})
    ec = _allele(geno.get("effortful_control", "typical"))
    ec_norm = (ec - _ALLELE_MIN) / (_ALLELE_MAX - _ALLELE_MIN)          # effortful control, [0,1]
    load = float(condition.get("allostatic_load", 0.3))                 # high load depletes resilience
    rels = char.get("current", {}).get("relationships", {})
    attachment = max((float(e.get("affinity", 0.0)) for e in rels.values() if isinstance(e, dict)),
                     default=0.3)                                       # a secure bond present?
    r = 0.45 * ec_norm + 0.30 * (1.0 - load) + 0.25 * attachment
    return max(0.05, min(0.95, r))


def assess(tags, impact, char, condition):
    """If this turn's event is DURABLE, return a sparse baseline diff; else None.

    tags:   the actor's event-tags {dimensions, durability, target?, target_group?}.
    impact: scalar appraised impact this turn (sum of |Δaffect| from appraise) — how much it moved them.
    Returns {temperament:{primary:Δ}, regard:{group:Δ}, _meta:{...}} | None. Relationship edges are
    NOT written here — see the module docstring; `bonds.observe` computes them per WITNESS.
    """
    if not isinstance(tags, dict):
        raise ValueError("assess: tags must be a dict")
    dims = tags.get("dimensions", {})
    if not isinstance(dims, dict) or not dims:
        return None
    # durable CANDIDATE: the actor self-reported 'durable', or a dimension is genuinely severe.
    candidate = tags.get("durability") == "durable" or any(float(v) >= _DURABLE_DIM for v in dims.values())
    if not candidate:
        return None
    # Gate on the RAW impact (resilience-independent): a reshaping event is durable whether or not
    # the character is resilient — resilience decides if it SCARS or STRENGTHENS, not if it lands.
    if float(impact) < _ARC_THRESHOLD:
        return None
    resilience = derive_resilience(char, condition)
    grw = _BASE_STEP * float(impact)                      # GROWTH step (full)
    dmg = grw * (1.0 - resilience)                        # DAMAGE step — resilience BUFFERS the scar
    dominant = max(dims, key=lambda k: float(dims[k]))
    group = tags.get("target_group")   # the SUBJECT is bonds.py's input now, not the arc's
    diff = {"temperament": {}, "regard": {}}

    if dominant in ("care_relevant", "relief"):           # CONNECTION (eudaimonic growth)
        diff["temperament"]["CARE"] = +grw
        if group:                                          # the bond generalizes: class disregard erodes toward 1.0
            diff["regard"][group] = +grw * _REGARD_GENERALIZE
    elif dominant == "threat":                             # SURVIVAL-THREAT — the resilience FORK
        if resilience >= _PTG_RESILIENCE:
            diff["temperament"]["SEEKING"] = +grw          # post-traumatic GROWTH: agency/mastery
            diff["temperament"]["FEAR"] = +grw * 0.3
        else:
            diff["temperament"]["FEAR"] = +dmg             # the PTSD signature: FEAR-baseline rises (buffered)
    elif dominant == "loss":                               # LOSS — grief baseline, a wound (resilience softens)
        diff["temperament"]["PANIC_GRIEF"] = +dmg
    elif dominant == "social_violation":                   # BETRAYAL — trust down, vigilance up
        diff["temperament"]["FEAR"] = +dmg * 0.5
    elif dominant == "mastery":                            # MASTERY — competence, seeking
        diff["temperament"]["SEEKING"] = +grw
    else:
        return None

    diff["_meta"] = {"dominant": dominant, "impact": round(float(impact), 3),
                     "resilience": round(resilience, 3), "grw": round(grw, 4), "dmg": round(dmg, 4)}
    return diff


def apply(char, diff):
    """Apply a sparse baseline diff -> a NEW char dict (moves the floor; every value clamped [0,1]).
    Mutates baseline.temperament means and baseline.model.regard.

    The `relationships` branch below is REPLAY-ONLY: `assess` has not emitted one since bonds.py took
    the edges, but a diff persisted before that must still rehydrate to the state its run had."""
    if not isinstance(char, dict) or not isinstance(diff, dict):
        raise ValueError("apply: char and diff must be dicts")
    new = copy.deepcopy(char)
    temp = new.setdefault("baseline", {}).setdefault("temperament", {})
    for p, d in diff.get("temperament", {}).items():
        if p in PRIMARIES and isinstance(temp.get(p), dict):
            temp[p]["mean"] = _clamp01(temp[p].get("mean", 0.5) + d)
    rels = new.setdefault("current", {}).setdefault("relationships", {})
    for tgt, axes in diff.get("relationships", {}).items():        # replay-only; see the docstring
        edge = rels.setdefault(tgt, {"trust": 0.5, "affinity": 0.5, "respect": 0.5, "debt": 0.0})
        for axis, d in axes.items():
            edge[axis] = _clamp01(edge.get(axis, 0.5) + d)
    reg = new.setdefault("baseline", {}).setdefault("model", {}).setdefault("regard", {})
    for grp, d in diff.get("regard", {}).items():
        reg[grp] = _clamp01(reg.get(grp, 1.0) + d)         # erodes toward 1.0 (or down for new disregard)
    return new
