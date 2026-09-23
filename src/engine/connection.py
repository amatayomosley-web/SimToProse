"""connection.py — how much of the character is INVESTED in the thing a moment is about.

`docs/character-model.md` "DECAY AND CONNECTION" is normative and records the author's rule:
**the greater the connection, the larger the impact — and the longer it lasts.** One quantity doing
two jobs, and this module is that quantity.

WHAT IT FIXES. Before it, a beloved's death and a stranger's produced the SAME magnitude. The only
subject-shaped term was `state._regard`, which returns 1.0 by default, is clamped to [0,1], and
carries the comment "affinity lifts, never lowers" — so a bond could recover impact lost to a
bigotry and could never amplify past baseline. Nothing in the engine made closeness matter.

A READ, NEVER A STORE, and that is the load-bearing choice. Connection is computed fresh from the
live relationship edge, which `bonds.observe` moves and `bond_rest.drift` relaxes. Three things follow
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

WIDENED 2026-09-11 (gate three) FROM PEOPLE TO EVERY HELD THING. Owner, 2026-09-10: *"the closer
people are the harder the emotions should hit, but I also want the ability for abstract ideas to
also carry the same harder hit as relationships."* So ONE registry, `for_about`, reads investment
in whatever a feeling points at, on one scale with one floor and one ceiling:

    a person       the relationship edge, as before (`compose`)
    a concept      the WOUND on that concept and path — its live intensity IS the investment
                   (`docs/concepts.py` names the concept; `wound.py` owns the intensity)
    a goal         the goal's priority (`baseline.drives.goals[n].priority`, about `goal:<n>`)
    a value        the worth-menu weight (`baseline.model.<family>.<key>`, about `value:<key>`)

An idea a character holds at 0.8 hits exactly as a person held at 0.8, by construction. And the
same investment stretches the half-life (`half_life_scale`): a full bond, or a full wound, doubles
how long the excursion lasts — the "and the longer it lasts" half of the rule, which until this
gate only the memory tier honoured.

REPETITION (`repetition`) rides here too, because it is the other multiplier on the same receipt
(owner: "Q is good"): the same thing landing again on the same path habituates when the thing is
absent and grinds when it is in the room. Its inputs are a count read from the log
(`targets.repeat_count`) and presence; it stores nothing.
"""
from __future__ import annotations
from .records import RecordError   # rule 6's bad-input type
from . import concepts as _concepts
from . import attachments as _attachments   # gate 5: what she holds that is not a person (same scale)

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

# ---- gate three (2026-09-11): the held registry, the half-life, repetition — all STARTS ----
# How far a full investment stretches the half-life: 1 + _HOLD_K * c. At 1.0 a full bond doubles
# it, which is what this module's own `_RETENTION_K` comment promised in per-beat units ("about
# twice as long"). A START, tuned in runs.
_HOLD_K = 1.0
# Repetition: per repeat of the same about on the same path, the receipt shrinks when the thing is
# absent (habituation — the fifth telling of the same news lands softer) and grows when it is
# present (grinding — the fifth slight from the man still in the room lands harder). Capped so
# neither can run away. STARTS.
_Q_HABITUATE = 0.80
_Q_GRIND = 1.15
_Q_CAP = 4
# While the thing a feeling is about is HERE, the feeling does not fade: the half-life stretches by
# this. Presence is ONE factor by the owner's ruling (the here/open split was withdrawn). A START.
PRESENCE_HOLD = 3.0


def _prefixed(about, prefix):
    return isinstance(about, str) and about.startswith(prefix)


def held_map(char):
    """The character's HELD THINGS -> investment in [0,1], on one scale. Pure; a fresh dict.

    People are NOT here — a person's investment is read live off the relationship edge by
    `for_about`, because `bonds.observe` moves edges every beat and a copy would go stale. What is
    here is the slow half: wounds (engine state at `baseline.wounds`), goals, and worth-menu
    values. Rebuilt by the drivers when a scene opens (after the opening's fade), after a wound moves
    and after an arc moves the baseline - so a wound that deepened this scene is felt from the next beat.
    """
    out = {}
    if not isinstance(char, dict):
        return out
    base = char.get("baseline") or {}
    for w in (base.get("wounds") or []):
        if not isinstance(w, dict):
            continue
        cid, path = w.get("concept"), w.get("path")
        if not cid or not path:
            continue
        try:
            c = max(0.0, min(1.0, float(w.get("intensity", 0.0))))
        except (TypeError, ValueError):
            raise RecordError("CONNECTION_HELD_NOT_NUMERIC",
                              "connection: wound %r has a non-numeric intensity %r" % (w.get("id"), w.get("intensity")))
        key = _concepts.about(str(cid))            # refuses an unknown concept by name
        # keyed by concept for the receipt; the PATH is the wound's own and is enforced in
        # `wound.fires` — a wound on WARINESS about sickness does not amplify GOODWILL about it.
        out.setdefault(key, {})[str(path)] = max(c, out.get(key, {}).get(str(path), 0.0))
    for i, g in enumerate((base.get("drives") or {}).get("goals") or []):
        if isinstance(g, dict) and isinstance(g.get("priority"), (int, float)):
            out["goal:%d" % i] = max(0.0, min(1.0, float(g["priority"])))
    model = base.get("model") or {}
    for fam in ("schwartz", "moral_foundations", "needs"):
        for k, v in (model.get(fam) or {}).items():
            if isinstance(v, (int, float)) and not str(k).startswith("_"):
                out["value:%s" % k] = max(0.0, min(1.0, float(v)))
    # GATE 5 (2026-09-18): ATTACHMENTS — what she holds that is not a person, on the same scale
    # (bond-arithmetic.md s3), read off `current.attachments` (the sheet block, folded from
    # attachment_declared rows on rehydrate). `+` entries only: `sign` is reserved. ONE REGISTRY, TWO
    # READERS, TWO FLOORS (settled review 1k): `for_about` applies _FLOOR here — an `acquainted` .15
    # amplifies no feeling — while bonds.stake_of reads the same number unfloored, because a gate is
    # not a multiplier. People are still not here; a person's investment is the live edge.
    for key, hold in _attachments.holds_of((char.get("current") or {}).get("attachments")).items():
        out[key] = hold
    return out


def for_about(relationships, held, about, path=None):
    """Investment in whatever `about` names, in [0,1], through the one floor. 0.0 for nothing.

    relationships: `current.relationships` (a person's edge is read live)
    held:          `held_map(char)` (wounds, goals, values)
    about:         a person id, `concept:<id>`, `goal:<n>`, `value:<key>`, or None
    path:          the path asking — a concept's investment is the wound ON THAT PATH
    """
    if not about:
        return 0.0
    if _prefixed(about, "concept:"):
        by_path = (held or {}).get(about) or {}
        c = float(by_path.get(str(path), 0.0)) if path is not None else max([0.0] + [float(v) for v in by_path.values()])
        return 0.0 if c < _FLOOR else min(1.0, c)
    if _prefixed(about, "goal:") or _prefixed(about, "value:"):
        c = float((held or {}).get(about, 0.0))
        return 0.0 if c < _FLOOR else min(1.0, c)
    # WIDENED 2026-09-18 (gate 5) to attachments: a held place or group, under the feeling floor.
    # No READING can name a loc./grp. key yet (the emotion seat's contract): this branch is reached
    # by the bond tier's stake today and by feeling when that seat gate lands.
    if _prefixed(about, _attachments.LOC) or _prefixed(about, _attachments.GRP):
        c = float((held or {}).get(about, 0.0) or 0.0)
        return 0.0 if c < _FLOOR else min(1.0, c)
    return for_target(relationships, about)


def scales(dim, about):
    """Does connection scale THIS dimension for THIS about? A person's investment scales only the
    empathy/betrayal dims (`SCALED_DIMS` — a threat's subject is the wolf). A concept, goal or value
    IS the thing feared, lost or wronged, so every dimension scales."""
    if _prefixed(about, "concept:") or _prefixed(about, "goal:") or _prefixed(about, "value:"):
        return True
    if _prefixed(about, _attachments.LOC) or _prefixed(about, _attachments.GRP):
        return True                                   # a held place or group IS the thing lost or wronged (gate 5)
    return dim in SCALED_DIMS


def half_life_scale(c):
    """Investment -> the multiplier on the half-life. 1.0 at none; 1 + _HOLD_K at full."""
    return 1.0 + _HOLD_K * max(0.0, min(1.0, float(c)))


def repetition(n, present):
    """The q multiplier for the (n+1)th consecutive reading about the same thing on a path.

    n = 0 (first time) -> 1.0. Absent: habituates by _Q_HABITUATE per repeat; present: grinds by
    _Q_GRIND per repeat; capped at _Q_CAP repeats. Unknown presence counts as absent.
    """
    try:
        k = max(0, min(_Q_CAP, int(n)))
    except (TypeError, ValueError):
        raise RecordError("CONNECTION_REPEAT_NOT_INTEGER", "connection: repeat count must be an int, got %r" % (n,))
    return (_Q_GRIND if present else _Q_HABITUATE) ** k


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
