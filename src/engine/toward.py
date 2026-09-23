"""toward.py — the MICRO tier: what one specific person makes you feel.

`docs/character-model.md` "THE THREE LAYERS" records the author's model and this module is its
micro half:

  > "Either for macro, there over all attitude is effected, negative care vector is applied and
  >  they care less over all. Or a micro change, their joy towards a person is applied so when they
  >  interact with this person it's applied."

The macro half is the arc: what happened to you changes who you are, everywhere. This is the other
half: what happened between you and THIS PERSON changes what you feel in their presence, and
nowhere else. A man can be hostile to the world and still soften when his daughter walks in; a man
can be gentle everywhere and go cold at one particular face. Neither is expressible by a baseline.

WHY THIS IS NOT bonds.py. An edge answers "do I trust them" on four relationship axes — trust,
affinity, respect, debt. This answers "what do they make me FEEL" on the eight primaries. They are
both per-target and they are not redundant: you can trust someone completely and still find no joy
in them, and the four axes have no word for that. `targets.py` is per-primary but stores ABOUTNESS
— which person a feeling points at — and says so explicitly: "a magnitude decays; a target never
decays". Magnitude toward a person is the thing none of the three could hold.

ADDITIVE, NOT A MULTIPLIER. The author's words are "negative care vector is applied" and "additive
so the character can change". An additive term also relaxes toward 0.0 — the identity of its own
operation in `levers.effective` — so a disposition that is spent leaves the vector exactly as it
found it rather than inverting into something else.

ONE PRICING TABLE. `state._DIM_TO_PATH` prices the event, the same table the current tier uses,
because what an event does to a person is a property of the event and the person and not of how
long the effect lasts (law 4).

THIS PARAGRAPH USED TO CLAIM MORE THAN THE TABLE NOW DELIVERS, and the correction matters because it
was the module's stated reason for existing. It read: the table "reaches all eight primaries and
carries seven NEGATIVE pushes — `social_violation -> PLAY -0.15` among them — which is exactly the
direction the arc cannot express." When the paths replaced the Panksepp primitives on 2026-09-08,
PLAY lost its successor (LEVITY is not built) and every push it carried was dropped. Measured
2026-09-09, the table now holds FOUR negative pushes across three dimensions — `loss -> STIRRING`,
`mastery -> WARINESS`, and `relief -> WARINESS`/`DEFLATION` — and `social_violation` has NONE. So a
degrading act still raises DISPLEASURE and DISTASTE toward its author, but it no longer LOWERS
anything, and the micro tier inherits that hole from the table it shares. The original observation
stands as history: a base-happy character through 80 durable diffs ended with fear saturated and the
positives untouched, which is why this tier exists.

SINCE 2026-09-12 (the redesign, gate 1) THIS TIER IS ATTITUDE. The flat float is MOOD — fast, what
everyone in the room meets; `current.toward[who][path]` is what THAT person has EARNED — slow, a
level on the path's own ladder, any rung; and what the actor plays is COMPOSED each beat by
`balance` (a >= m -> a; a < m -> halfway down from the mood, never below rest) and never stored.
The additive `rows` and the 0.25 cap are retired (staging/src/engine/RETIRED-toward-rows-2026-09-12.py).

Deterministic, stdlib only, no LLM, no randomness (CLAUDE.md hard rules 3 and 4).
"""
from __future__ import annotations

import math

from .clock import MINUTES_PER_DAY            # the one clock; the bottom rung converts the old DAY rate
from .decay_law import relax          # the one law; see its header
from . import connection
from .records import PATHS, RecordError
from .rung_blocks import BANDS as _BANDS      # the ladder edges the attitude staircase steps across
from .rungs import rung_at                    # which rung a magnitude sits in
from .state import _DIM_TO_PATH, _rung_half_life   # the pricing table; the MOOD staircase's shape

# How far one event moves a feeling toward one person. Smaller than the arc's `_BASE_STEP` (0.07)
# because this fires on ORDINARY beats, not only on the rare durable ones — a disposition is built
# from many small readings of someone, where a baseline is reshaped by few large events.
# [CALIBRATION] — a probe against a real book should set this; it is the one number here that is
# somebody's judgement rather than derived.
_STEP = 0.02

# THE CAP IS GONE (2026-09-12, the redesign's gate 1). `_LIMIT = 0.25` bounded what one person could
# earn to one direction band, which made the cold husband who is tender with his daughter
# unbuildable: from a `quiet` rest (0.045) the cap topped out at concern, two rungs short of
# tenderness. ATTITUDE is a level on the path's own ladder and may reach any rung; the only bound is
# the ladder's. Replay clamps to the unit interval, as every path float is.
_UNIT = 1.0

# A PASSING beat charges attitude at this fraction of the reading's vector; a DURABLE beat charges it
# in full. [JUDGMENT, 2026-09-12, the redesign's gate 4] measured on the live Holmes read
# (readalong-holmes-1789164611-09007d, 421 beats): Watson's 111 readings about Holmes are 106
# PASSING / 5 durable, so this knob is ~95% of a recurring relationship's accrual. Replaying those
# readings as pure accrual (cap 1.0, no erosion, stranger investment): 0.25 leaves a central
# relationship at the floor over twelve chapters (STIRRING curiosity 0.12, RECEPTIVITY liking 0.16);
# 1.0 reaches urge/wonder 0.47 in ~7 beats (the fondness->devotion runaway the accrual cut ended);
# 0.5 gives noticing/pleasure 0.24/0.27 over a case, about one rung per 14 beats. One verified
# origin, no ground-truth target — a judgment from the trajectory, and erosion would push it higher.
_ATTITUDE_PASSING = 0.5

# Others present, damped: a person in the room who is NOT the one engaged lifts a path only to this
# fraction of their attitude, and never lowers one — "a loved daughter in the room softens without
# cancelling the anger at B". [START] — the brief names the mechanism, not the number.
_OTHERS_DAMP = 0.5


def _clamp(x):
    return -_UNIT if x < -_UNIT else (_UNIT if x > _UNIT else float(x))


def observe(dims, connection=1.0):
    """One event -> {primary: delta} for how it moves the witness's feeling toward its SUBJECT.

    Returns {} when nothing applies, so a caller can test the result directly.

    `connection` is the seam for the multiplier under design ("the greater the connection, the
    larger the impact"). It defaults to 1.0 and is NOT yet supplied by any caller — deliberately,
    because what composes connection and what its ceiling should be are open questions, and a
    parameter with an honest default is better than a magic number baked into the arithmetic.
    """
    if not isinstance(dims, dict):
        raise RecordError("TOWARD_DIMS_NOT_A_DICT", "toward.observe: dims must be a dict, got %r" % type(dims).__name__)
    try:
        gain = float(connection)
    except (TypeError, ValueError):
        raise RecordError("TOWARD_CONNECTION_NOT_NUMERIC", "toward.observe: connection must be a number, got %r" % (connection,))
    out = {}
    for dim, mag in dims.items():
        try:
            m = float(mag)
        except (TypeError, ValueError):
            raise RecordError("TAG_DIMENSION_VALUE_NOT_NUMERIC", "toward.observe: dimension %r is %r, not a number — validate_tags "
                             "should have refused this upstream" % (dim, mag))
        for prim, push in _DIM_TO_PATH.get(dim, ()):
            out[prim] = out.get(prim, 0.0) + _STEP * m * push * gain
    return {p: v for p, v in out.items() if v}


def observe_readings(readings, me="", profile=None, durable=False):
    """The emotion seat's PERSON-bound readings -> [(who, path, delta)]: what this beat adds to ATTITUDE.

    THE SECOND FEED (2026-09-11), RE-SCALED (2026-09-12, the redesign's gate 1). A reading
    "DISPLEASURE / anger, about cobb" charges the MOOD through `state.receive` (everyone in the room
    meets it) and, through this function, what Cobb has EARNED: the reading's own vector
    (`rungs.vector_for`, λ_p · height) x the connection multiplier x the durability gate.

      connection  `connection.magnitude_scale(connection.for_about(...))` — 1.0 for a stranger, up
                  to 1.75 for the closest bond; the SAME multiplier form the flat receipt uses, so
                  the two feeds scale alike. (Raw investment would be 0.0 below the connection floor
                  and a stranger could never become someone.) `profile` is `state.build_profile`'s
                  dict; absent, the multiplier is 1.0.
      durability  a DURABLE beat charges in full; a PASSING beat at `_ATTITUDE_PASSING`.

    What is skipped, and why: an empty `about` (an unbound feeling is a real state with no person in
    it), a `concept:` about (a wound or an idea is not a person; the concept registry's business),
    and a reading about the character themself (`about == me` — what you make yourself feel IS the
    mood). Readings are positive magnitudes, so this feed only RAISES an attitude; a person who calms
    you still arrives by the event route. Deterministic; pure over its inputs.
    """
    from . import rungs as _rungs
    rel = (profile or {}).get("relationships") if isinstance(profile, dict) else None
    held = (profile or {}).get("held") if isinstance(profile, dict) else None
    gate = 1.0 if durable else _ATTITUDE_PASSING
    out = []
    for r in (readings or []):
        about = str(getattr(r, "about", "") or "")
        if not about or about.startswith("concept:") or (me and about == str(me)):
            continue
        path, rung = getattr(r, "path", None), getattr(r, "rung", None)
        if path not in PATHS:
            raise RecordError("TOWARD_READING_PATH_UNKNOWN",
                              "toward.observe_readings: %r is not a path" % (path,))
        k = _rungs.index_of(path, rung)                       # raises on a rung the ladder lacks
        c = connection.for_about(rel if isinstance(rel, dict) else {}, held, about, path)
        out.append((about, path, float(_rungs.vector_for(path, k)) * connection.magnitude_scale(c) * gate))
    return out


def compose(mood, attitude, rest):
    """One path: what the actor plays toward ONE engaged person, from mood, their attitude, the rest.

    THE OWNER'S BALANCE (2026-09-12):  a >= m -> a (they have earned more than the mood; play it);
    a < m -> midpoint(m, max(a, rest)) — a cooler person is met halfway down from the mood, and never
    below the speaker's own resting level. Owner's example: engaged with A at rung 6, turn to B whose
    attitude is rung 1 — B is met at the midpoint. Floats on the path's own scale, never rung
    indices: the ladders are not evenly spaced and a half-rung has no block; the resolver names the
    rung from the float.
    """
    m, a, r = float(mood), float(attitude), float(rest)
    return a if a >= m else (m + max(a, r)) / 2.0


def balance(affect, toward, rest, engaged=None, present=(), me="", targets=None):
    """The composed vector for this beat -> (effective {path: float}, stirs {who: {path: delta}},
    origin {path: "mood" | "attitude" | "lift"}).

    NEVER STORED — computed each beat from three stored things: the MOOD (`affect`, fast), the
    ATTITUDES (`toward`, per person, slow) and the REST (the temperament means). This replaced the
    additive `rows` on 2026-09-12: adding a person's vector onto the mood counted a bound reading
    twice while that person was in the room (measured on a generated scene: the composer two rungs
    above the stored state), and the cap it needed then made a tender-with-one-person character
    unbuildable.

      engaged   the ONE person this beat is played toward: composed in full, every path.
      present   others in the room: each may LIFT a path to `_OTHERS_DAMP` x their attitude, never
                lower one — a floor, not a sum, so no double count re-enters here.
      me        the character's own id; an entry for oneself is ignored (composing against oneself
                is undefined — what you make yourself feel IS the mood).
      targets   `current.targets`, what each path's mood is ABOUT ({path: about}). THE MOOD IS MET
                IN FULL BY THE PERSON IT IS ABOUT: the brief's formula alone would meet the very
                person who raised the mood halfway down from it until their attitude caught up
                (measured on a generated scene: the one who had raised the speaker's warmth to
                compassion would have been met at tenderness), while the brief's own example plays
                the mood in full with A and halves it for B. The path's existing aboutness is the
                record of who raised it; no second store.

    `stirs` carries, for the engaged person and each present other, what they move the played
    vector by RELATIVE TO THE MOOD (effective-if-engaged minus mood), for `direction.direct_stirs`
    to say in words on the "Those present" line. Zero entries are dropped so a person at the mood
    adds no words. Nobody engaged and nobody present -> effective == mood exactly (the identity).

    `origin` names WHICH BRANCH SET each path's value, because this is the function that knows and
    the driver must never re-derive it from the number (2026-09-12, resolved with the peer session):
    a value can sit on a plateau three ways — the engaged person's earned attitude (`a >= m`, under
    either rule), a present other's damped lift, or the mood itself — and only
    the mood drains on the fast clock. `rungs.descending` reads it: a come-down is right ONLY when
    the mood set the value. The midpoint branch (`a < m`) is "mood": `(m + max(a, rest)) / 2` moves
    with m. Reported for every built path, "mood" when nobody is engaged or present.
    """
    if not isinstance(affect, dict):
        raise RecordError("TOWARD_AFFECT_NOT_A_DICT", "toward.balance: affect must be a dict, got %r" % type(affect).__name__)
    att = toward if isinstance(toward, dict) else {}
    rest = rest if isinstance(rest, dict) else {}
    me = str(me or "")
    eng = str(engaged or "")
    if not eng or eng == me or eng.startswith("concept:"):
        eng = ""
    others = [str(w) for w in (present or ()) if str(w) and str(w) != me and str(w) != eng
              and not str(w).startswith("concept:")]

    about = targets if isinstance(targets, dict) else {}

    def _vec(who):
        v = att.get(who)
        return v if isinstance(v, dict) else {}

    def _toward(who, p, m, r):
        """What `who` is met at on path p -> (value, origin): the mood in full when it is about them,
        else composed. "attitude" when THEIR earned attitude is what set the value (a >= m, either
        rule — at equality the attitude is what holds it when the mood drains), "mood" otherwise:
        the midpoint moves with m."""
        a = float(_vec(who).get(p, 0.0))
        if str(about.get(p) or "") == who:
            return max(m, a), ("attitude" if a >= m else "mood")
        return compose(m, a, r), ("attitude" if a >= m else "mood")

    eff, stirs, origin = {}, {}, {}
    for p in PATHS:
        m = float(affect.get(p, 0.0))
        r = float(rest.get(p, 0.0))
        e, src = m, "mood"
        if eng:
            e, src = _toward(eng, p, m, r)
            d = e - m
            if d:
                stirs.setdefault(eng, {})[p] = d
        for who in sorted(set(others)):
            a = float(_vec(who).get(p, 0.0))
            lift = _OTHERS_DAMP * a
            if lift > e:
                e, src = lift, "lift"
            d = _toward(who, p, m, r)[0] - m        # what they WOULD stir if turned to
            if d:
                stirs.setdefault(who, {})[p] = d
        eff[p] = max(-_UNIT, min(_UNIT, e))
        origin[p] = src
    for k, v in affect.items():                      # author comments ride through, as in decay
        if k not in PATHS and str(k).startswith("_"):
            eff[k] = v
    return eff, stirs, origin


def coalesce(deltas):
    """[TowardDelta] -> [TowardDelta], ONE row per (perceiver, target, path), deltas summed.

    Two feeds, one quantity (2026-09-11). The first beat with both feeds live priced GOODWILL toward
    the same person twice in one turn — the event route (care_relevant, subject = that person) and
    the reading route (a protectiveness reading about them) — and `toward_deltas` is UNIQUE on (run, turn,
    perceiver, target, path), so `append_turn` rolled the whole beat back and the scene died. The
    constraint is right: one row per key per turn keeps the log readable, and the fold sums every
    row for a key before it clamps (`replay`), so one summed row IS what two rows would have meant.
    Order of first appearance is kept; distinct sources are joined so the row still says what moved
    it. Called by both drivers on the same line, immediately before the commit.
    """
    merged = {}
    for td in (deltas or []):
        key = (td.perceiver, td.target, td.primary)
        if key in merged:
            prev = merged[key]
            src = prev.source if td.source in ("", prev.source) else (
                td.source if not prev.source else "%s | %s" % (prev.source, td.source))
            merged[key] = type(prev)(perceiver=prev.perceiver, target=prev.target, primary=prev.primary,
                                     delta=float(prev.delta) + float(td.delta), source=src)
        else:
            merged[key] = td
    return list(merged.values())


def replay(char, deltas):
    """Fold logged micro movements onto a character. Mutates `char["current"]["toward"]`, returns it.

    ONE FUNCTION, called from every resume path — `bonds.py` records what it costs when a replay is
    hand-copied into each driver instead, and `levers.replay_wound_deltas` follows the same rule.

    STAMPS `_authored_toward` BEFORE APPLYING ANYTHING. An author may write a starting disposition
    ("she has always resented her sister"), and law 1 of docs/character-model.md is that the base
    survives: effective = base + experience, both readable. Stamp after and the base is gone.

    THE UNDERSCORE HERE IS A CONVENTION, NOT THE GUARD, and a first draft of this docstring said
    otherwise. `scene._strip_notes` is applied to `baseline.traits`, `baseline.model` and
    `baseline.drives` ONLY — the stable prefix, which is built from fixed+baseline. Nothing strips
    `current`. What keeps this out of the prompt is that `assemble`'s volatile block SELECTS its
    keys explicitly (state / goals / percepts / recall / edges) rather than dumping `current`, so a
    new key under `current` is invisible until someone adds it. The underscore matches
    `_authored_mean` and `_authored_intensity` for readability; those two DO depend on the strip,
    because they live inside prompt-visible baseline blocks. This one does not.

    SUMS THEN CLAMPS, once, so the fold is order-independent — the same discipline
    `levers.replay_wound_deltas` follows and for the same reason.

    deltas: [(target, primary, delta)] in log order.
    """
    if not isinstance(char, dict):
        raise RecordError("TOWARD_CHAR_NOT_A_DICT", "toward.replay: char must be a dict, got %r" % type(char).__name__)
    cur = char.setdefault("current", {})
    base = cur.setdefault("toward", {})
    cur.setdefault("_authored_toward",
                   {who: dict(v) for who, v in base.items() if isinstance(v, dict)})
    totals = {}
    for row in (deltas or ()):
        who, prim, d = str(row[0]), str(row[1]), float(row[2])
        if prim in PATHS:
            # TWO statements, not one. `a[k] = expr` evaluates expr FIRST, so the one-liner form
            # `totals.setdefault(who, {})[prim] = totals[who].get(...)` reads totals[who] before
            # setdefault has created it and raises KeyError on the first delta for each person.
            slot = totals.setdefault(who, {})
            slot[prim] = slot.get(prim, 0.0) + d
    authored = cur["_authored_toward"]
    for who, vec in totals.items():
        start = dict(authored.get(who) or {})
        merged = {}
        for prim in set(start) | set(vec):
            v = _clamp(float(start.get(prim, 0.0)) + float(vec.get(prim, 0.0)))
            if v:
                merged[prim] = v
        base[who] = merged
    return base

# How fast a feeling toward one person fades when nothing renews it, per DAY. Since 2026-09-19
# (gate `attitude-staircase`) this table is no longer the whole law: it is the BOTTOM RUNG of the
# attitude staircase, converted to a half-life in minutes by `_attitude_half_life`, which is why
# the values and the name both stay — a rename would sever the doc trail to the day rates they are.
# The ORDERING is `state._DECAY_RATE`'s, because fast-versus-slow is a property of the emotion system
# and not of which tier is asking; the values are compressed onto the slow clock. CALIBRATION.
#
# Read what it encodes: the positives sit at the fast end and the negatives at the slow end, which
# is the same negativity bias `bonds._ALPHA_NEG > _ALPHA_POS` and `wound._A_DEEPEN > _A_EASE`
# already carry. Someone wrongs you and you do not see them for a season: the fear goes first, the
# anger cools, the warmth you had drains away — and what is left standing is the contempt. You have
# stopped being angry at them and started simply not respecting them. That is estrangement,
# produced by arithmetic with no further events.
_RETENTION = {
    "WARINESS":    0.93,   # fear of a person, unreinforced, updates fastest
    "STIRRING":    0.95,
    "DISPLEASURE": 0.95,   # anger outlasts the liking (affinity drifts at 0.90)
    "GOODWILL":    0.97,
    "DISTASTE":    0.98,   # contempt is the durable social residue
    "DEFLATION":   0.99,   # grief toward a person spans a saga
    # PLACEHOLDERS, and stated rather than defaulted. `erode` used to read this through
    # `.get(prim, 0.95)`, so before 2026-09-09 these two took STIRRING's rate by accident
    # and the table read as though somebody had chosen it. `_attitude_half_life` subscripts it
    # directly now — every path in `records.PATHS` has a row, and a missing one is a loud KeyError
    # beside `state._HALF_LIFE`'s, not a silent default. They have no place in the ordering the
    # paragraph above argues for -- that argument is about how a wrong ages, and neither path is
    # about a wrong. `toward.observe` builds only from `state._DIM_TO_PATH`, which reaches neither,
    # so a non-zero value here can arrive ONLY from an authored sheet. The value is the mean of the
    # six real rates. Calibrate it if an appraisal dimension is ever authored for either path.
    "RECEPTIVITY": 0.96,
    "SELF-REGARD": 0.96,
    "LEVITY":      0.95,   # PLACEHOLDER, stated (2026-09-11): STIRRING's rate; the design gives this path no object, so a value here reaches state only from an authored sheet
}


def _attitude_half_life(path, index):
    """(path, 1-based rung index) -> the ATTITUDE's half-life at that rung, in MINUTES.

    TWO TABLES, ONE SHAPE (the redesign's decay section; gate `attitude-staircase`, 2026-09-19).
    The mood tier already steps per rung (`state._rung_half_life`, gate 2, 6ccf5c9). Attitude steps
    on the SAME staircase at a slower, per-path scale — and that scale invents no third table, it is
    derived from the two the repo already has:

      BOTTOM (rung 1) — today's per-DAY rate, converted. `erode` used to relax the whole vector at
        `_RETENTION[path]` per day, so a bottom-rung attitude must go on decaying exactly as it did:
        `MINUTES_PER_DAY * ln(0.5) / ln(_RETENTION[path])` is the half-life in minutes that
        reproduces that rate over one day, EXACTLY (`0.5 ** (1440/hl) == _RETENTION[path]`, asserted
        in `tests/test_toward.py`). [UNMEASURED, carried over] — `_RETENTION`'s values are the
        pre-redesign day rates, CALIBRATION where they were written; nothing re-measured them here
        and this gate deliberately did not (its OMISSIONS say so).
      SHAPE (every other rung) — the MOOD staircase's own ratio on this path,
        `_rung_half_life(path, k) / _rung_half_life(path, 1)`, so the top burns out in the same
        proportion the mood's does and the two tiers cannot disagree about the shape of forgetting.
        [MEASURED / JUDGMENT, per `state.py`] — the EPISODE anchors are that module's measured
        excursion medians, the DISPOSITION anchors and `_TOP_BURN` its stated judgments. Read there,
        not re-implemented here; replace an anchor and BOTH staircases move together.

    THE ORDERING IS `_RETENTION`'S, and it survives the shaping because the ratio is 1.0 at rung 1
    by construction: at the bottom rung WARINESS fades fastest, then STIRRING and DISPLEASURE,
    GOODWILL, DISTASTE, and DEFLATION slowest — the negativity bias `bonds._ALPHA_NEG > _ALPHA_POS`
    and `wound._A_DEEPEN > _A_EASE` already carry, unchanged by this gate.

    No `hold` term: the genotype bends the MOOD's half-lives (`state.half_life_minutes`); what one
    person has earned is not the character's own regulation, and adding a cell here would be a knob
    nothing asked for.
    """
    bottom = MINUTES_PER_DAY * math.log(0.5) / math.log(_RETENTION[path])
    return bottom * _rung_half_life(path, index) / _rung_half_life(path, 1)


def _step_to_zero(path, magnitude, c, minutes):
    """One MAGNITUDE down `path`'s ladder toward ZERO over `minutes` -> the new magnitude. Pure.

    `state.decay_over`'s loop at the attitude scale: at most one segment per rung, each draining at
    its own half-life (`_attitude_half_life` in place of `_rung_half_life`), rest fixed at ZERO
    because this tier's rest is the authored character and never a floor. So a hatred at the top of
    DISPLEASURE's ladder cools fast through the hot rungs and slowly through the cool ones, where
    one flat rate made it fade at the same fraction per day as a flicker of annoyance at the bottom.

    CONNECTION ENTERS PER STEP. `connection.retention_scale` takes a per-UNIT retention, so it is
    applied to the rung's per-MINUTE retention — today's function, at minute granularity. The
    segment length is then read back off the SLOWED rate (`-1 / log2(r)` is that rate's own
    half-life): charge a slowed value the unslowed time to cross a band and a bonded feeling would
    fall through the ladder at the unbonded speed, which is the opposite of what connection does.

    RUNG 1 IS WHERE THIS ANCHORS. Every ladder's first band starts at 0.0, so rest is INSIDE it and
    `decay_over`'s own "the rung that contains rest: finish here" branch spends the WHOLE remaining
    time at rung 1's rate — which is the old per-day rate exactly. The bands are half-open
    [lo, hi), so a magnitude sitting on an edge belongs to the rung above and no edge case reaches
    this branch by accident.
    """
    v, rem = float(magnitude), float(minutes)
    bands = _BANDS[path]
    for _ in range(len(bands) + 1):                   # bounded: one segment per rung, + safety
        if rem <= 0 or v < 1e-12:
            break
        k = rung_at(path, v)[0]
        lo = bands[k - 1][0]                          # this rung's lower edge, on the way to zero
        r = connection.retention_scale(0.5 ** (1.0 / _attitude_half_life(path, k)), c)
        if lo < 1e-12:                                # the rung that contains rest: finish here
            v = relax(v, 0.0, r, rem)                 # THE ONE LAW (decay_law.relax), not re-spelled
            break
        t = math.log2(v / lo) / (-math.log2(r))       # time to fall to this rung's lower edge
        if t <= 0 or t >= rem:                        # not enough time to leave the rung
            v = relax(v, 0.0, r, rem)
            break
        v = lo - 1e-9                                 # step just into the next rung's band
        rem -= t
    return v


def erode(char, minutes, connections=None):
    """Time passing -> every micro vector relaxes toward ZERO. Mutates `current.toward`, returns it.

    RESTS AT ZERO, not at itself, and that is the author's law made arithmetic: the experience layer
    decays back to the authored character. Since the vector is signed, an effective value may sit
    BELOW the base while the base itself never moves — "we don't change the base does not mean we
    can't go below the base". Time takes the MAGNITUDE down; the SIGN is the person's, and is kept.

    CONNECTION SLOWS IT. `connections` maps entity -> connection in [0,1]; a feeling toward someone
    you are invested in fades slower, bounded so it can never become permanent. Same term that
    amplifies the impact, doing its second job — and it needs no decay of its own, because it is
    read live off an edge that is already drifting. Omit it and every retention is unmodified.

    MINUTES, the one declared clock (`clock.py`) — the same unit the mood tier reads, and since
    2026-09-19 the same per-rung STAIRCASE at the attitude's own slower scale (`_attitude_half_life`,
    `_step_to_zero`). `bond_rest.drift`, `wound.erode` and `arc.erode` still take that one
    declaration in DAYS: the minute and the day are the only two units in this engine and there is
    no third.
    """
    if not isinstance(char, dict):
        raise RecordError("TOWARD_CHAR_NOT_A_DICT", "toward.erode: char must be a dict, got %r" % type(char).__name__)
    try:
        e = max(0.0, float(minutes))
    except (TypeError, ValueError):
        raise RecordError("TOWARD_ELAPSED_NOT_NUMERIC", "toward.erode: minutes must be a number, got %r" % (minutes,))
    vecs = (char.get("current") or {}).get("toward")
    if not isinstance(vecs, dict) or e == 0.0:
        return vecs or {}
    conns = connections or {}
    for who, vec in list(vecs.items()):
        if not isinstance(vec, dict):
            continue
        c = float(conns.get(who, 0.0) or 0.0)
        kept = {}
        for prim, val in vec.items():
            if prim not in PATHS:
                continue
            v = _clamp(float(val))                  # `rung_at` refuses a value off the unit interval
            m = _step_to_zero(prim, abs(v), c, e)   # the ladder is a magnitude's; the sign rides back
            if m > 1e-9:
                kept[prim] = m if v >= 0.0 else -m
        vecs[who] = kept
    return vecs
