"""decay_law.py — the one equation every decay in this engine already was.

`docs/character-model.md` opens its NORMATIVE decay section with a sentence this module exists to
make true of the CODE and not only of the prose:

    "Every decay in this engine is already the same equation. Nothing new needs inventing; the
     tiers differ only in what they rest at, how fast, and on which clock."

    value  <-  rest + (value - rest) x retention ^ elapsed

MEASURED 2026-09-03, THE ENGINE HELD SIX SPELLINGS OF IT:

    bonds.drift          rest[axis] + (edge - rest[axis]) * (_RETENTION[axis] ** elapsed)
    wound.erode          floor + (now - floor) * (_RETENTION ** e)
    arc.erode            base + (now - base) * (_ERODE ** e)
    toward.erode         val * (r ** e)                   # "rest point is ZERO, so this is the
                                                          #  whole fold" — its own comment
    world_appraisal.cool raw * (COOLING[rate] ** units)   # the same zero-rest case
    state.decay          the same fold, per primary

A SEVENTH ARRIVED THE SAME DAY, in a new module, which is how this was found at all: no guard in
the repo reports a duplicated equation, and CLAUDE.md's table of seven hand-maintained duplicates —
every one of which had already gone wrong — was assembled the same way, by someone noticing.

WHY THIS IS ITS OWN MODULE. `world_appraisal.cool` carries a NOT YET GENERAL note reserving exactly
the parameter the lift needs ("DECAY ASSUMES A ZERO REST POINT... cool(..., rest=...)"), so it was
the obvious host — but a law that six modules obey should not live inside the one that happened to
reserve the parameter first. `cool` becomes a caller like the others. `decay.py` is named for this
and would be the natural home; it is a peer's live work this session, and not editing it is a
boundary I set with her rather than a technical constraint.

WHAT THIS MODULE DELIBERATELY DOES NOT DECIDE: what a tier rests at, how fast it fades, or which
clock it ticks on. Those are the three columns of the doc's table and they belong to the callers —
a wound's permanence floor is wound.py's business, and putting it here would replace six honest
copies of an equation with one dishonest copy of six policies.

Deterministic, stdlib only, no LLM. Rule 4 holds: nothing here is random.
"""
from __future__ import annotations

__layer__ = "engine"

from .records import RecordError   # rule 6's bad-input type


def relax(value, rest, retention, elapsed):
    """Relax `value` toward `rest` at `retention` per unit, over `elapsed` units.

    The whole law, and every caller supplies the three things the doc says differ: what it rests
    at, how fast, and how much time has passed on ITS clock. This function has no opinion on any
    of them — see the module header for why that is the point rather than an omission.

    THE TWO IDENTITIES WORTH KNOWING, because callers rely on them:
      - `elapsed = 0` returns `value` unchanged, exactly. Not approximately: retention ** 0 is 1.0
        for every retention, so the arithmetic is `rest + (value - rest) * 1.0`.
      - a value already AT rest never moves, for any retention and any elapsed.
    Both are asserted in `tests/test_decay_law.py`, because a decay that drifts on a zero-length
    tick or that walks a resting value is the kind of defect that only shows up after a long run.

    NO CLAMPING HERE. Four of the six callers clamp to [0,1] and two do not, and the ones that do
    disagree about whether to clamp before or after — `bonds.drift` clamps per axis, `arc.erode`
    clamps the mean, `wound.erode` returns a DELTA and lets its caller apply the floor. Clamping
    here would silently change two of them, which is exactly what a lift must not do.
    """
    try:
        v, r, k = float(value), float(rest), float(retention)
        e = float(elapsed)
    except (TypeError, ValueError):
        raise RecordError("DECAY_INPUT_NOT_NUMERIC",
                          "relax: value, rest, retention and elapsed must all be numbers, got "
                          "%r, %r, %r, %r" % (value, rest, retention, elapsed))
    if e < 0:
        raise RecordError("DECAY_ELAPSED_NEGATIVE",
                          "relax: elapsed must be >= 0, got %r — time does not run backwards, and "
                          "a negative exponent would AMPLIFY the deviation instead of shrinking it,"
                          " which reads as a memory getting sharper with age" % (elapsed,))
    if not 0.0 <= k <= 1.0:
        raise RecordError("DECAY_RETENTION_OUT_OF_RANGE",
                          "relax: retention must be in [0,1], got %r. Above 1 the value diverges "
                          "away from rest; below 0 it oscillates across it." % (retention,))
    return r + (v - r) * (k ** e)
