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

ONE PRICING TABLE. `state._DIM_TO_PRIMARY` prices the event, the same table the current tier uses,
because what an event does to a person is a property of the event and the person and not of how
long the effect lasts (law 4). That table reaches all eight primaries and carries seven NEGATIVE
pushes — `social_violation -> PLAY -0.15` among them — which is exactly the direction the arc
cannot express. Measured this session: a base-happy character through 80 durable diffs of beatings
and degradation ended with FEAR saturated and PLAY, CARE, RAGE and DISGUST all UNCHANGED.

Deterministic, stdlib only, no LLM, no randomness (CLAUDE.md hard rules 3 and 4).
"""
from __future__ import annotations

from .decay_law import relax          # the one law; see its header
from . import connection
from .records import PRIMARIES, RecordError
from .state import _DIM_TO_PRIMARY

# How far one event moves a feeling toward one person. Smaller than the arc's `_BASE_STEP` (0.07)
# because this fires on ORDINARY beats, not only on the rare durable ones — a disposition is built
# from many small readings of someone, where a baseline is reshaped by few large events.
# [CALIBRATION] — a probe against a real book should set this; it is the one number here that is
# somebody's judgement rather than derived.
_STEP = 0.02

# How far one person may move you, per primary. ONE DIRECTION BAND (`direction._EDGE_BANDS` steps
# at 0.25) and equal to `state._CARE_FLOOR`: a single person can shift your read of a moment by as
# much as innate empathy itself, and never more than the authored person. Not a decay substitute —
# decay is under design; this is the bound that keeps a long book bounded regardless.
# [CALIBRATION] — anchored to the band width rather than derived.
_LIMIT = 0.25


def _clamp(x):
    return -_LIMIT if x < -_LIMIT else (_LIMIT if x > _LIMIT else float(x))


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
        for prim, push in _DIM_TO_PRIMARY.get(dim, ()):
            out[prim] = out.get(prim, 0.0) + _STEP * m * push * gain
    return {p: v for p, v in out.items() if v}


def apply_deltas(vector, deltas):
    """Accumulate {primary: delta} onto one person's vector. Returns a NEW dict; clamped once.

    STAMPS NOTHING — the authored base lives on the character under `_authored_toward` and is
    stamped by `replay`, which is the one place a vector is rebuilt from the log.
    """
    out = dict(vector or {})
    for p, d in (deltas or {}).items():
        if p in PRIMARIES:
            out[p] = _clamp(out.get(p, 0.0) + float(d))
    return {p: v for p, v in out.items() if v}


def rows(toward, ctx):
    """The micro vectors -> additive lever rows for whoever this moment actually involves.

    PRESENT **or** SUBJECT, which is the distinction `levers` already draws for catalog rows
    (`present_edge` vs `target_edge`) and `scene.assemble` already builds into its ctx. A feeling
    toward someone applies when they are in the room, and it also applies when the moment is ABOUT
    them — you can be moved by a person who is not there.

    Returns rows in `levers.effective`'s own shape, so nothing new has to learn to read them.
    """
    if not isinstance(toward, dict):
        return []
    present = set((ctx or {}).get("edges") or {})
    subject = (ctx or {}).get("target")
    if subject:
        present.add(str(subject))
    out = []
    for who in sorted(present):
        vec = toward.get(who)
        if not isinstance(vec, dict):
            continue
        for prim in PRIMARIES:                      # PRIMARIES order, so the trace is stable
            d = vec.get(prim)
            if not d:
                continue
            out.append({"lever": prim, "op": "+", "magnitude": float(d),
                        "source": "what %s makes them feel" % who, "toward": who})
    return out


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
        if prim in PRIMARIES:
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

# How fast a feeling toward one person fades when nothing renews it, per DECLARED unit. The
# ORDERING is `state._DECAY_RATE`'s, because fast-versus-slow is a property of the emotion system
# and not of which tier is asking; the values are compressed onto the slow clock. CALIBRATION.
#
# Read what it encodes: the positives sit at the fast end and the negatives at the slow end, which
# is the same negativity bias `bonds._ALPHA_NEG > _ALPHA_POS` and `wound._A_DEEPEN > _A_EASE`
# already carry. Someone wrongs you and you do not see them for a season: the fear goes first, the
# anger cools, the warmth you had drains away — and what is left standing is the contempt. You have
# stopped being angry at them and started simply not respecting them. That is estrangement,
# produced by arithmetic with no further events.
_RETENTION = {
    "FEAR":        0.93,   # fear of a person, unreinforced, updates fastest
    "PLAY":        0.94,   # joy toward someone needs re-supply
    "SEEKING":     0.95,
    "RAGE":        0.95,   # anger outlasts the liking (affinity drifts at 0.90)
    "LUST":        0.96,
    "CARE":        0.97,
    "DISGUST":     0.98,   # contempt is the durable social residue
    "PANIC_GRIEF": 0.99,   # grief toward a person spans a saga
}


def erode(char, elapsed, connections=None):
    """Time passing -> every micro vector relaxes toward ZERO. Mutates `current.toward`, returns it.

    RESTS AT ZERO, not at itself, and that is the author's law made arithmetic: the experience layer
    decays back to the authored character. Since the vector is signed, an effective value may sit
    BELOW the base while the base itself never moves — "we don't change the base does not mean we
    can't go below the base".

    CONNECTION SLOWS IT. `connections` maps entity -> connection in [0,1]; a feeling toward someone
    you are invested in fades slower, bounded so it can never become permanent. Same term that
    amplifies the impact, doing its second job — and it needs no decay of its own, because it is
    read live off an edge that is already drifting. Omit it and every retention is unmodified.

    Per DECLARED unit, the director's own, the same one `bonds.drift` and `wound.erode` take. Two
    clocks in this engine and no third.
    """
    if not isinstance(char, dict):
        raise RecordError("TOWARD_CHAR_NOT_A_DICT", "toward.erode: char must be a dict, got %r" % type(char).__name__)
    try:
        e = max(0.0, float(elapsed))
    except (TypeError, ValueError):
        raise RecordError("TOWARD_ELAPSED_NOT_NUMERIC", "toward.erode: elapsed must be a number, got %r" % (elapsed,))
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
            if prim not in PRIMARIES:
                continue
            r = connection.retention_scale(_RETENTION.get(prim, 0.95), c)
            v = relax(float(val), 0.0, r, e)        # rest point is ZERO; the law, one caller of six
            if abs(v) > 1e-9:
                kept[prim] = v
        vecs[who] = kept
    return vecs
