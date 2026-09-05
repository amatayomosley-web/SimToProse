"""connection.py — how much of the character is INVESTED in the person a moment is about.

`docs/character-model.md` "DECAY AND CONNECTION" is normative and records the author's rule:
**the greater the connection, the larger the impact — and the longer it lasts.** One quantity doing
two jobs, and this module is that quantity.

WHAT IT FIXES. Before it, a beloved's death and a stranger's produced the SAME magnitude. The only
subject-shaped term was `state._regard`, which returns 1.0 by default, is clamped to [0,1], and
carries the comment "affinity lifts, never lowers" — so a bond could recover impact lost to a
bigotry and could never amplify past baseline. Nothing in the engine made closeness matter.

A READ, NEVER A STORE, and that is the load-bearing choice. Connection is computed fresh from the
live relationship edge, which `bonds.observe` moves and `bonds.drift` relaxes. Three things follow
for free rather than needing machinery:

  * it INCREASES when the bond does (`bonds.observe`, `_ALPHA_POS`)
  * it DECREASES three ways — `_ALPHA_NEG` at 2.5x the rise, `drift` toward the resting prior, and
    the trust CLIFF, which collapses a bond rather than eroding it
  * it needs NO DECAY OF ITS OWN. When a friendship cools, both the amplification and the slowed
    forgetting cool with it, and there is no fifth store to fall out of sync.

DEBT IS EXCLUDED FROM THE BLEND, on the relationship tier's own reasoning: debt "is not a belief, it
is a running account". An account is not investment, and including it would mean that repaying
someone reduces how much their death hurts.

DEVIATION ABOVE NEUTRAL, NOT RAW LEVEL. `bonds._NEUTRAL` puts every belief axis at 0.5, so a
stranger with no edge composes to exactly 0 and every multiplier to exactly 1.0 — which is the same
identity-preservation `_regard` defends ("keeps target-less events unchanged"). Every existing run,
fixture and target-less event computes byte-identically.

A DISLIKED PERSON IS NOT AMPLIFIED. Below-neutral clamps to zero rather than going negative:
dampening is the regard machinery's job, and two factors that both scale the same term must not
restate each other.

Deterministic, stdlib only, no LLM, no randomness.
"""
from __future__ import annotations
from .records import RecordError   # rule 6's bad-input type

# The blend. ORDERING is the defensible part — affinity above trust above respect — and the engine
# already leans on affinity twice for exactly this idea: `arc.derive_resilience` takes max affinity
# as its secure-base term, and `_regard`'s lift reads affinity alone. The VALUES are calibration and
# want a probe; nothing here pretends otherwise.
_W = (("affinity", 0.60), ("trust", 0.25), ("respect", 0.15))

# THE RELEVANCY FLOOR — the author's third requirement: "low connections shouldn't get any
# modifiers". A HARD dead zone, not a soft ramp, and the difference is the whole point. Without it
# every passing acquaintance at affinity 0.52 earns a sliver of amplification and a sliver of slowed
# forgetting: every number in the run shifts for no dramatic reason, the audit trail fills with rows
# that move nothing a reader could notice, and a probe of the real effect drowns in that noise. The
# floor buys SILENCE. The precedent is `arc._ARC_THRESHOLD`, below which no durable diff is written
# at all because "most events stay transient" — here, most people are not close enough to change how
# anything lands. At 0.20, affinity alone must clear roughly 0.67 to register: more than an
# acquaintance. CALIBRATION; the dead-zone FORM is the normative part.
_FLOOR = 0.20

# How far connection may amplify. Bounded because the repo has already paid once for an unbounded
# chain against a saturating clamp: a brave character's fear capped identically across all four
# threat_reactivity alleles, and "bravery became an IMMUNITY rather than a disposition". 0.75 keeps
# all four affiliation alleles separated at a typical-severe event with a maximal bond; at 1.0 the
# flattening returns. CALIBRATION, with a named falsifier.
_GAIN = 0.75

# How far connection may slow forgetting: a fraction of the remaining headroom toward 1.0, so no
# feeling can ever become permanent by this route. At 0.5 and full connection a feeling lasts about
# twice as long. CALIBRATION.
_RETENTION_K = 0.5

# Which dimensions connection scales. WIDER than `state._REGARD_SCALED_DIMS` by exactly
# `social_violation`, and the asymmetry is principled: regard scopes EMPATHY, and a bigotry dampens
# compassion but never dampened outrage; connection scales INVESTMENT, and investment amplifies
# betrayal — the beloved's knife cuts deeper than the stranger's.
#
# `threat` stays OUT, and the objection "a threat to someone you love is not self-directed" is
# answered rather than dismissed: a threat's SUBJECT is the source of danger (`arc.py` says so where
# it excludes severing dims), so connection-to-the-subject would be connection to the wolf. Fear FOR
# someone rides the `care_relevant` half that a threat-to-a-cared-for also emits, and that half IS
# scaled. The fear OF the thing rides the unscaled half. `relief` stays out because its pushes are
# negative and a negative push binds no party to compose a connection from.
SCALED_DIMS = ("care_relevant", "loss", "social_violation")


def compose(edge):
    """One relationship edge -> connection in [0, 1]. A stranger, or no edge at all, is 0.0."""
    if not isinstance(edge, dict):
        return 0.0
    dev = 0.0
    for axis, w in _W:
        try:
            dev += w * (float(edge.get(axis, 0.5)) - 0.5)
        except (TypeError, ValueError):
            raise RecordError("CONNECTION_EDGE_AXIS_NOT_NUMERIC", "connection: edge axis %r is %r, not a number" % (axis, edge.get(axis)))
    c = max(0.0, min(1.0, 2.0 * dev))
    return 0.0 if c < _FLOOR else c          # the dead zone: below the floor, nothing at all


def magnitude_scale(c):
    """Connection -> the multiplier on an event's magnitude. 1.0 at no connection, never above 1.75."""
    return 1.0 + _GAIN * max(0.0, min(1.0, float(c)))


def retention_scale(retention, c):
    """Connection -> a slower forgetting. Takes a bounded fraction of the headroom toward 1.0.

    Never reaches 1.0, so no feeling becomes permanent by this route however close the bond.
    """
    r = max(0.0, min(1.0, float(retention)))
    return r + (1.0 - r) * _RETENTION_K * max(0.0, min(1.0, float(c)))


def for_target(relationships, target):
    """The connection a character has to one named person. 0.0 for a stranger or an absent target."""
    if not target or not isinstance(relationships, dict):
        return 0.0
    return compose(relationships.get(str(target)))
