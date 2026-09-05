"""levers.py — the effective-levers tier (the buff/debuff catalog).

`state.py` owns the BASELINE and CURRENT tiers; this module owns the third.
docs/state-engine.md:11-12 defines all three:

  baseline          temperament, slow                    (character sheet)
  current state     appraisal up + decay down, per beat   (state.py)
  effective levers  what the decision actually SEES,      <- HERE
                    after context, INSTANTANEOUS          (decision-engine.md:66-85)

Separate module rather than more of state.py because it is a separate concern and because
state.py is at its 500-line ceiling (CLAUDE.md hard rule 6).
"""
import re

from .records import PRIMARIES
from .errors import EngineError


def _clamp(x):
    """Clamp to [0, 1]. Local copy so this module stands alone; twin of state._clamp."""
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


# state-engine.md defines THREE tiers, not two. Baseline (temperament, slow), CURRENT STATE
# (this module's appraise + decay, per beat), and EFFECTIVE LEVERS — "what the decision actually
# sees, after context", timescale *instantaneous*, computed by the buff/debuff catalog.
#
# Only the first two shipped. The consequence was measured 2026-08-22 and is the reason this
# exists: because the decision read the CURRENT tier directly, a character's fear ceiling was
# `mean + (1 - mean) * r` — identical across all four threat_reactivity alleles at maximum
# severity, because appraise saturates at 1.0 and decay then pulls back to a equilibrium the
# gain never touches. A brave character (resting FEAR 0.10) capped at 0.748, permanently under
# the 0.80 band: bravery became an IMMUNITY rather than a disposition. That bound is CORRECT for
# a resting level and wrong for "how afraid am I of this, right now" — two different questions
# that were being answered by one number.
#
# Effective is INSTANTANEOUS: computed fresh per decision, never carried across beats, never
# committed. The ledger keeps the current tier (CLAUDE.md hard rule 2 — the log is world-truth;
# effective depends on who is in the room, so it is a view, not canon). It is re-derivable from
# the committed current tier plus the active rows, the same cache-not-truth discipline the
# snapshot follows.
#
# THE HARD LINE (decision-engine.md:85, normative): the catalog computes STATE, it does not pick
# the ACTION. There is no argmax here and there must never be one — "that argmax-on-the-sum is
# the gamey resolver rejected at the top of this doc". The LLM resolves the competing pulls; this
# function only computes what it resolves over.

_OPS = ("x", "+")          # multiply, or add (magnitude may be negative to debuff)


def _check_row(row, i):
    """One registry row -> (lever, op, magnitude). Fails loud; never coerces."""
    if not isinstance(row, dict):
        raise EngineError("LEVERS_EFFECTIVE_ROW_NOT_A_DICT", "effective: row %d must be a dict, got %r" % (i, type(row).__name__))
    lever = row.get("lever")
    if lever not in PRIMARIES:
        raise EngineError("LEVERS_EFFECTIVE_ROW_LEVER_INVALID", "effective: row %d lever %r is not one of the bounded levers %s "
                         "(the catalog is a BOUNDED set, authored once — decision-engine.md)"
                         % (i, lever, list(PRIMARIES)))
    op = row.get("op")
    if op not in _OPS:
        raise EngineError("LEVERS_EFFECTIVE_ROW_OP_INVALID", "effective: row %d op %r must be one of %s" % (i, op, list(_OPS)))
    mag = row.get("magnitude")
    if not isinstance(mag, (int, float)):
        raise EngineError("LEVERS_EFFECTIVE_ROW_MAGNITUDE_NOT_NUMERIC", "effective: row %d magnitude must be numeric, got %r" % (i, mag))
    if op == "x" and float(mag) < 0.0:
        raise EngineError("LEVERS_EFFECTIVE_ROW_MULTIPLIER_NEGATIVE", "effective: row %d multiplier %r is negative; use op '+' to subtract"
                         % (i, mag))
    return lever, op, float(mag)


def effective(current, rows=()):
    """Current-state vector + ACTIVE registry rows -> the effective levers the decision sees.

    decision-engine.md:80 — `effective = base x PI(multipliers) + SUM(buffs/debuffs)`, clamped.
    Multipliers apply first, then additive terms, so a row's meaning does not depend on authoring
    order within its own kind.

    current: {primary: 0..1} — the CURRENT tier (post-appraise, post-decay).
    rows:    iterable of ACTIVE rows `{lever, op, magnitude, source, ...}`. Which rows are active
             is decided upstream (scene.assemble); this function trusts that and only computes.

    Returns a NEW dict; `current` is never mutated. With no rows it returns the current values
    unchanged — the identity that makes this tier provably non-breaking for existing runs.

    Raises ValueError on a malformed row (unknown lever, bad op, non-numeric magnitude).
    """
    if not isinstance(current, dict):
        raise EngineError("LEVERS_EFFECTIVE_CURRENT_NOT_A_DICT", "effective: current must be a dict, got %r" % type(current).__name__)
    missing = [p for p in PRIMARIES if p not in current]
    if missing:
        raise EngineError("LEVERS_EFFECTIVE_CURRENT_MISSING_PRIMARIES", "effective: current missing primaries: %s" % missing)

    mult = {p: 1.0 for p in PRIMARIES}
    add  = {p: 0.0 for p in PRIMARIES}
    for i, row in enumerate(rows):
        lever, op, mag = _check_row(row, i)
        if op == "x":
            mult[lever] *= mag
        else:
            add[lever] += mag

    out = {}
    for p in PRIMARIES:
        v = current[p]
        if p.startswith("_"):
            out[p] = v
            continue
        out[p] = _clamp(float(v) * mult[p] + add[p])
    for k, v in current.items():                 # author comment keys ride through verbatim
        if k.startswith("_"):
            out[k] = v
    return out


# ---------------------------------------------------------------------------
# Which rows are ACTIVE — the trigger half of `{trigger condition, lever, op, magnitude, source}`
# ---------------------------------------------------------------------------
# decision-engine.md's four worked entries define the bounded condition vocabulary; there are
# exactly four kinds and this implements all four:
#
#   {trusted ally present -> fear x0.7}          -> present_edge
#   {believes the threat is lethal -> fear x1.5} -> percept (fired off the event surface)
#   {his child is the one at risk -> +5}         -> present_edge (a named target)
#   {anger high -> fear x0.6}                    -> affect          (emotion modulating emotion)
#   {exhausted -> fear +3}                       -> condition       (state)
#
# Conditions within one row AND together. A row with no `when` is always active (a standing trait
# expressed as a lever, which is legitimate — it is how "chronically wary of authority" is said).
#
# APPRAISAL vs CATALOG (state-engine.md:49-54): appraisal fires on the CHANGE, the catalog applies
# on the STANDING FACT. A spider appearing is an event and raises fear through appraise(); a
# spider being *present* is a standing fact and multiplies fear through a row. Both, not either.

_AXES = ("trust", "affinity", "respect", "debt")


def _norm(s):
    return " ".join(str(s).lower().split())


def _edge_matches(edges, who, req):
    """Any edge in `edges` (optionally only `who`) satisfying every axis clause in `req`."""
    for eid, edge in edges.items():
        if who is not None and eid != who:
            continue
        ok = True
        for ax, v in req.items():
            if ax in _AXES:
                if float(edge.get(ax, 0.0)) < float(v):
                    ok = False
                    break
            elif ax.endswith("_at_most") and ax[:-len("_at_most")] in _AXES:
                if float(edge.get(ax[:-len("_at_most")], 0.0)) > float(v):
                    ok = False
                    break
            elif ax != "id":
                raise EngineError("LEVERS_UNKNOWN_EDGE_UNKNOWN", "levers: unknown edge clause %r (axes: %s, or <axis>_at_most)"
                                 % (ax, list(_AXES)))
        if ok:
            return True
    return False


def _row_active(when, ctx):
    """One row's `when` clause against the turn context. All clauses must hold."""
    if not when:
        return True
    if not isinstance(when, dict):
        raise EngineError("LEVERS_WHEN_NOT_A_DICT", "levers: `when` must be a dict, got %r" % type(when).__name__)

    words = when.get("percept")
    if words is not None:
        if not isinstance(words, (list, tuple)):
            raise EngineError("LEVERS_WHEN_PERCEPT_NOT_A_LIST", "levers: when.percept must be a list of words")
        # WORD BOUNDARIES, not substring containment. Raw `in` fired a row keyed on a short word
        # against two unrelated words that merely contained it — measured twice in one sentence of
        # a live book, both false, and both masked because a legitimate word in the same sentence
        # also matched. A trigger that fires on a coincidence inside a longer word is a wound
        # going off at random.
        # Multi-word phrases keep substring semantics: they cannot collide by accident.
        surface = _norm(ctx.get("text", ""))
        def _hit(w):
            n = _norm(w)
            if not n:
                return False
            if " " in n:                      # a phrase — substring is safe and is what authors mean
                return n in surface
            return re.search(r"(?<![0-9a-z])%s(?![0-9a-z])" % re.escape(n), surface) is not None
        if not any(_hit(w) for w in words):
            return False

    # PRESENT_EDGE -- someone in the room. TARGET_EDGE -- the party this event is ABOUT. They are
    # different facts: "the man I hate is here" and "this is about the man I hate" pull differently,
    # and the same aboutness distinction the shame measurement forced onto states applies to
    # triggers. Both accept `<axis>` (at least) and `<axis>_at_most` (at most), because an axis that
    # can only be tested on its favourable side expresses allies and never enemies -- and
    # relationships.md says the axes gate help/betray, believe/DOUBT, defer/OVERRIDE, comply/REFUSE.
    for key in ("present_edge", "target_edge"):
        edge_req = when.get(key)
        if edge_req is None:
            continue
        if not isinstance(edge_req, dict):
            raise EngineError("LEVERS_WHEN_ENTRY_NOT_A_DICT", "levers: when.%s must be a dict" % key)
        edges = ctx.get("edges") or {}
        if key == "target_edge":
            subject = ctx.get("target")
            edges = {subject: edges[subject]} if subject in edges else {}
        who = edge_req.get("id")
        if not _edge_matches(edges, who, edge_req):
            return False

    aff_req = when.get("affect_at_least")
    if aff_req is not None:
        aff = ctx.get("affect") or {}
        if not all(float(aff.get(p, 0.0)) >= float(v) for p, v in aff_req.items()):
            return False

    cond_req = when.get("condition_at_most")
    if cond_req is not None:
        cond = ctx.get("condition") or {}
        if not all(float(cond.get(k, 1.0)) <= float(v) for k, v in cond_req.items()):
            return False
    return True


def active_rows(catalog, ctx):
    """Full catalog + turn context -> the rows that fire this turn, in authoring order.

    catalog: list of rows `{when?, lever, op, magnitude, source}` (`baseline.catalog`).
    ctx:     {"text": event text, "edges": {id: edge}, "affect": {...}, "condition": {...}}

    Pure and deterministic. Validates every row it returns, so a malformed row fails loud at
    assembly rather than silently never firing — the failure mode this whole tier exists to end.
    """
    if catalog is None:
        return []
    if isinstance(catalog, dict):
        # `{"_note": ..., "rows": [...]}` — every other block in the schema carries an author
        # `_note`, so the catalog may too. A bare list is equally valid.
        catalog = catalog.get("rows") or []
    if not isinstance(catalog, (list, tuple)):
        raise EngineError("LEVERS_CATALOG_NOT_A_LIST", "levers: catalog must be a list of rows or {'rows': [...]}, got %r"
                         % type(catalog).__name__)
    out = []
    for i, row in enumerate(catalog):
        _check_row(row, i)                       # validate ALL rows, active or not
        if _row_active(row.get("when"), ctx or {}):
            out.append(row)
    return out
