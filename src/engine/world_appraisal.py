"""world_appraisal.py — the world-side mirror of `state-engine.md`. ONE mechanism, three registers.

`docs/world-dynamics.md` names this file's job in a single sentence, and names it as one rule aimed
at three places:

    "events carry typed consequences that map BY RULE onto snapshot fields — a public killing raises
     the relevant tension temperature; a granary fire moves scarce-resource levels; an insult to the
     guild shifts its disposition toward the insulter. Same shape as character appraisal:
     (typed event x standing interests) -> state delta, COMPUTED, NEVER GUESSED."

That is the whole design. A character has a worth menu and an event has typed dimensions; relevance
is their product. A world REGISTER ENTRY has standing interests and a watch scope, and relevance is
the same product. `state.py` does it for people; this does it for the world.

WHY THIS IS THE CHASSIS AND NOT `tensions.py`. Tensions are the first of the doc's three registers
to be built. Written register-shaped, the next two arrive as COPIES of this arithmetic — which is
the duplicate class CLAUDE.md tabulates seven instances of, and the reason four modules each grew
their own copy of one allele parse. Written mechanism-shaped, faction disposition and scarce-resource
levels arrive as CALLERS. The doc gave the mechanism a name — "world-appraisal" — before it gave any
register one, and the file takes that name deliberately.

WHAT LIVES HERE: arithmetic only. No register knows itself here; the caller supplies the entry.
No LLM (hard rule 3), no randomness (hard rule 4), no persistence, stdlib only.

THE ONE THING THIS FILE REFUSES TO DO is choose WHICH entry an event is about. Nothing looks up an
identity, because the doc forbids guessing one: relevance is computed against EVERY live entry, and
several may move from one event. A public killing heating both the levy dispute and the old
blood-feud is correct, not a collision.

DECAY IS DERIVED, NEVER STORED — the same split `state.py` draws between the current tier and the
effective one, and the reason hard rule 2 survives this feature: the fold stays a pure function of
the LOG, and time is applied at read. `world-dynamics.md` asks for exactly that: "the engine advances
time-dependent state AT READ TIME ... decays what decays (tension temperatures cool absent fuel — the
world-side analog of state-engine.md decay-toward-temperament)."

PAYLOAD AUTHORS, BEFORE YOU WRITE THE NEXT REGISTER'S EVENTS: THE LOG STORES FLOATS. A severity
word is an authoring convenience and dies at the boundary that reads it — the seat resolves a
proposal's words before the write (`scripts/keeper.py`) and `from_world` resolves an authored note's
on load. A word that survives INTO the log is a hostage to `severity._MAGNITUDE`: recalibrate that
table and every historical run refolds into a different world, which is hard rule 2's "pure function
of the log" true in form and false in substance. `tensions.py` carries the full statement and the
measurement that produced it; this pointer is here because you are reading THIS file.

NOT YET GENERAL — the four places this is still tension-shaped, named so the next register finds
them here rather than discovering them. The claim that faction disposition and scarce-resource
levels "arrive as callers" is TRUE for resource magnitude and OVERSTATED for disposition, which
reuses `relevance` and about half of `in_scope` and must add all four of these:

  1. NO VALENCE. `heat` returns a non-negative magnitude, but the doc's own disposition example is
     signed — "an insult to the guild SHIFTS its disposition TOWARD the insulter" (downward). The
     signed half of the character mirror (`state._DIM_TO_PRIMARY` carries it) is not here.
  2. NO DIRECTION. Disposition is per-pair — the guild's view OF the insulter. This returns one
     scalar per entry with no "toward whom" slot.
  3. DECAY ASSUMES A ZERO REST POINT. `cool` decays toward 0 within [0,1]. Dispositions rest at a
     PRIOR (the shape `bonds.drift` uses), and resource levels recover toward a capacity.
  4. SCOPE KNOWS PARTIES AND PLACES, NOT ASSETS. A granary fire scopes by the grain.

Each is additive when the time comes — a per-register valence map, `cool(..., rest=...)`, a
`watches.assets` key — and none of them is here now, because the doc reserves the faction-specific
questions until the first faction is authored (`world-dynamics.md` open-Q #4) and building against
an unauthored register is how a chassis acquires the wrong joints.
"""
from .decay_law import relax          # the one law; see its header
from .errors import EngineError
from .state import _DIM_TO_PRIMARY as _DIMS_SOURCE

# The appraisal vocabulary, DERIVED from the one table that defines it. `consolidation.py` imports
# the same source with the same comment: a second copy of this list is a defect waiting for the list
# to change, and it already cost this repo a silently-discarded appraisal in a live run.
DIMENSIONS = frozenset(_DIMS_SOURCE)

# How fast an entry sheds heat per DECLARED unit of elapsed time — the `toward.py` retention idiom,
# authored as a word rather than a number so a world note never carries a tuned float.
#
# Class-B, probe-calibrated start. Anchored on the arc/bond precedent: `bonds` drifts at 0.90 and
# `toward` retains 0.93-0.99 per unit. A grievance is the slowest social residue in this repo's
# model (`toward.py`: "contempt is the durable social residue" at 0.98; "grief toward a person spans
# a saga" at 0.99), and a contested border outlasts a contempt, so `slow` sits at the top of that
# band rather than beyond it.
COOLING = {
    "fast":    0.90,   # a flare: a market panic, a rumour — gone within the season absent fuel
    "typical": 0.96,
    "slow":    0.99,   # a grievance: the contested border, the suppressed faction
}
DEFAULT_COOLING = "typical"


class WorldAppraisalError(EngineError):
    """A world-appraisal input the arithmetic cannot use. Raised BEFORE anything is written."""


def validate_interests(interests, where="interests"):
    """Standing interests: {dimension: weight in [0,1]}. Raises naming the field.

    Fails loud on an unknown dimension rather than ignoring it, because ignoring one is how
    `consolidation._KNOWN_DIMS` silently discarded every appraisal in a live run — the same table,
    the same failure, one register over.
    """
    if not isinstance(interests, dict) or not interests:
        raise WorldAppraisalError(
            "WORLD_INTERESTS_EMPTY",
            "%s must be a non-empty {dimension: weight} map — an entry with no interests can never "
            "be moved by anything, which makes it scenery rather than a register entry" % where)
    for dim, weight in sorted(interests.items()):
        if dim not in DIMENSIONS:
            raise WorldAppraisalError(
                "WORLD_INTEREST_DIM_UNKNOWN",
                "%s[%r] is not one of the seven appraisal dimensions (%s) — it would be silently "
                "ignored, and an interest nothing can match is worse than none"
                % (where, dim, ", ".join(sorted(DIMENSIONS))))
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or not 0.0 <= weight <= 1.0:
            raise WorldAppraisalError("WORLD_INTEREST_WEIGHT_RANGE",
                                      "%s[%r] = %r is not a weight in [0,1]" % (where, dim, weight))
    return True


def validate_watches(watches, where="watches"):
    """Scope: {parties: [id...], locations: [id...]}. At least one, or the entry watches nothing."""
    if not isinstance(watches, dict):
        raise WorldAppraisalError("WORLD_WATCHES_TYPE",
                                  "%s must be a dict of parties/locations, got %s"
                                  % (where, type(watches).__name__))
    parties = watches.get("parties") or []
    places = watches.get("locations") or []
    for name, seq in (("parties", parties), ("locations", places)):
        if not isinstance(seq, list):
            raise WorldAppraisalError("WORLD_WATCHES_FIELD_TYPE",
                                      "%s.%s must be a list, got %s"
                                      % (where, name, type(seq).__name__))
        # COUNTING ENTRIES IS NOT LOOKING AT THEM. The check below refuses a watch list that names
        # nothing; a list of BLANKS passed it and produced the identical condition — `in_scope`
        # compares each member against actor, target and location, and no event carries an empty
        # one, so a blank can never match. The refusal that already exists was being satisfied by
        # a value it was written to catch.
        for i, member in enumerate(seq):
            if not isinstance(member, str) or not member.strip():
                raise WorldAppraisalError(
                    "WORLD_WATCHES_MEMBER_EMPTY",
                    "%s.%s[%d] is %r. Every member is matched by NAME against an event's actor, "
                    "target or location, so a blank one can never be in scope — the entry would "
                    "sit inert while looking live, which is what the next check refuses and this "
                    "value walked straight past." % (where, name, i, member))
    if not parties and not places:
        raise WorldAppraisalError(
            "WORLD_WATCHES_EMPTY",
            "%s names neither a party nor a location — nothing could ever be in scope, so the entry "
            "would sit inert while looking live" % where)
    return True


def in_scope(watches, actor=None, target=None, location=None):
    """Is this event within the entry's watch? -> bool.

    The cheap fence, and the one that keeps "only the levered is written" true
    (`world-state-ledger.md`: "the sim doesn't log every peasant"). A threat between two unwatched
    farmhands in an unwatched place intersects nothing and contributes nothing — and the emitting
    seat's warrant test then refuses the event as a beat, without anyone having to remember to.
    """
    parties = set(watches.get("parties") or [])
    places = set(watches.get("locations") or [])
    who = {x for x in (actor, target) if x}
    return bool(who & parties) or bool(location and location in places)


def relevance(dimensions, interests):
    """(typed event x standing interests) -> a scalar in [0,1]. The doc's formula, literally.

    A dot product over a mass of `max(1, sum of weights)`. Both halves of that are load-bearing:

      * DIVIDING BY THE MASS at all, so an entry caring about six things is not six times easier to
        move by one event than an entry caring about one.
      * THE FLOOR OF 1, so weights that sum to less than one keep their ABSOLUTE meaning. A first
        version divided by the raw mass and was therefore scale-invariant — `{social_violation: 0.1}`
        and `{social_violation: 1.0}` priced identically, so an author's "barely about this" dial did
        nothing while `validate_interests` still bounded weights to [0,1] as though it did. That is
        the worst of both: a knob that looks live and is not. Caught by review, measured, fixed.

    Dimensions the entry does not care about contribute nothing; dimensions the event does not carry
    contribute nothing.
    """
    if not isinstance(dimensions, dict):
        raise WorldAppraisalError("WORLD_DIMENSIONS_TYPE",
                                  "relevance: dimensions must be a dict, got %s"
                                  % type(dimensions).__name__)
    if not interests:
        return 0.0
    mass = max(1.0, sum(float(w) for w in interests.values()))
    total = 0.0
    for dim, weight in interests.items():
        try:
            value = float(dimensions.get(dim, 0.0) or 0.0)
        except (TypeError, ValueError):
            raise WorldAppraisalError(
                "WORLD_DIMENSION_NOT_NUMERIC",
                "relevance: dimensions[%r] = %r is not numeric. Severity WORDS resolve at the parse "
                "seam (severity.normalise_dimensions); by the time the arithmetic sees them they are "
                "floats." % (dim, dimensions.get(dim)))
        total += value * float(weight)
    return max(0.0, min(1.0, total / mass))


def heat(dimensions, interests, step):
    """How much this event moves an entry it is in scope for. Never negative, never > step.

    THE NAME WILL NOT SURVIVE A SIGNED REGISTER. Disposition moves DOWN when the guild is insulted,
    and "negative heat" is a worse phrase than the thing it describes. When that register lands this
    wants a `delta()` sibling carrying a valence map rather than a renamed `heat()` — the magnitude
    reading is right for tensions and resource levels, and it should keep the honest name.

    `step` is the register's own calibration constant — the caller owns it, because a tension and a
    resource level do not move at the same rate and this file has no opinion about either.
    """
    return relevance(dimensions, interests) * float(step)


def cool(value, elapsed, rate=DEFAULT_COOLING, rest=0.0):
    """Shed heat over DECLARED elapsed time -> the effective value. PURE; nothing is stored.

    This is why hard rule 2 survives the feature. `world-state-ledger.md` says "the fold is the ONLY
    way the snapshot changes — it is a pure function of the log", and a decayed-in-place temperature
    would make time a second writer. So the fold keeps the RAW accumulated value and this applies
    time at read, the way `state.py` keeps the current tier and derives the effective one.

    `elapsed` is director-declared units from `time_declarations` — the same clock `arc.erode`,
    `bonds.drift` and `wound.erode` already read. One clock, now four tiers.

    `rest` IS THE PARAMETER THIS FUNCTION'S OWN NOTE RESERVED. It read "DECAY ASSUMES A ZERO REST
    POINT... cool(..., rest=...)", and 2026-09-03 was the moment: the arithmetic moved to
    `decay_law.relax`, which every other decaying tier now calls too, and the zero default keeps
    every existing caller bit-identical (asserted in tests/test_decay_law.py). A tension sheds heat
    toward nothing; a belief's confidence sheds toward its tier floor. Same law, different rest.
    """
    try:
        raw = float(value)
        units = max(0.0, float(elapsed))
    except (TypeError, ValueError):
        raise WorldAppraisalError("WORLD_COOL_INPUT_NOT_NUMERIC",
                                  "cool: value and elapsed must be numbers, got %r and %r"
                                  % (value, elapsed))
    if rate not in COOLING:
        raise WorldAppraisalError("WORLD_COOLING_UNKNOWN",
                                  "cool: %r is not a cooling rate; expected one of: %s"
                                  % (rate, ", ".join(sorted(COOLING))))
    return max(0.0, min(1.0, relax(raw, rest, COOLING[rate], units)))


def band(value):
    """A magnitude -> the severity WORD for its nearest rung. The rendering half of rule 5.

    Every register that ever reaches a prompt needs this, and defining "nearest rung" per-seat is
    how two seats come to disagree about what 0.55 is called. One definition, here, beside the
    arithmetic it renders — the same reason `severity.py` owns the ladder rather than each caller.
    """
    from .severity import WORDS, value_of
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    return min(WORDS, key=lambda w: abs(value_of(w) - v))
