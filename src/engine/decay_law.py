"""decay_law.py — the one equation every decay in this engine already was.

    value  <-  rest + (value - rest) x retention ^ elapsed

MEASURED IN THIS TREE 2026-09-04, TWO SPELLINGS OF IT:

    state.decay    mean + (affect[p] - mean) * r                  # elapsed is implicitly 1
    bonds.drift    rest[axis] + (edge - rest[axis]) * (_RETENTION[axis] ** elapsed)

They differ only in what they rest at, how fast, and on which clock — which is what the
parameters are for. Neither is wrong; there are simply two of them, so a change to the law has
to be made twice and nothing fails if only one is made. CLAUDE.md's Verify section names that
shape directly ("if you are about to write a list that mirrors something the code already knows,
derive it") and tabulates seven hand-maintained duplicates in this lineage that had each already
gone wrong by the time anyone looked. This is that rule applied to an equation.

The lift also buys two refusals neither spelling had. A negative `elapsed` used to AMPLIFY the
deviation instead of shrinking it — `retention ** -1` is greater than 1 — and non-numeric input
used to raise a bare TypeError from deep inside a fold, naming nothing.

NOTE ON PROVENANCE: the sibling instance's version of this module documents six callers. Four of
them (`wound.erode`, `arc.erode`, `toward.erode`, `world_appraisal.cool`) do not exist in this
template, and neither does the `docs/character-model.md` decay section it quotes. Those lines are
deliberately absent here rather than copied — a template that documents callers it does not have
is the exact defect `tests/test_capability_claims.py` was added to catch.
"""
from __future__ import annotations

from .records import RecordError   # rule 6's bad-input type


def relax(value, rest, retention, elapsed):
    """Relax `value` toward `rest` at `retention` per unit, over `elapsed` units.

    The whole law. Every caller supplies the three things that differ: what it rests at, how
    fast, and how much time has passed on ITS clock. This function has no opinion on any of
    them, which is the point rather than an omission.

    THE TWO IDENTITIES CALLERS RELY ON:
      - `elapsed = 0` returns `value` unchanged, EXACTLY — not approximately. `retention ** 0`
        is 1.0 for every retention, so the arithmetic is `rest + (value - rest) * 1.0`.
      - a value already AT rest never moves, for any retention and any elapsed.
    Both are asserted in `tests/test_decay_law.py`. A decay that drifts on a zero-length tick, or
    that walks a value already at rest, is the kind of defect that only surfaces after a long run.

    NO CLAMPING HERE, deliberately. The two callers in this tree clamp DIFFERENTLY — `bonds.drift`
    clamps per axis with `_clamp01`, `state.decay` clamps with `_clamp` — so a shared clamp would
    silently change one of them. Changing behaviour under cover of a refactor is exactly what a
    lift must not do.
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
                          "a negative exponent AMPLIFIES the deviation instead of shrinking it, "
                          "which reads as a value that decays AWAY from its rest point" % (elapsed,))
    if not (0.0 <= k <= 1.0):
        raise RecordError("DECAY_RETENTION_OUT_OF_RANGE",
                          "relax: retention must be in [0,1], got %r — above 1 the deviation grows "
                          "each tick, below 0 it alternates sign" % (retention,))
    return r + (v - r) * (k ** e)
