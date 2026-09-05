"""direction.py — numbers to qualitative DIRECTION (gate 5, the backstage guardrail).

design.md: "the engine computes fear 8/10; what enters the prompt is 'gripped by fear' — a
qualitative direction the engine translates from the number. The LLM never sees raw stats;
numbers live in the DB; directions live in the prompt." relevancy-gate.md: "the prose never
says 'spent 3 focus'."

Phrasing is NEUTRAL qualitative description, not prose flourish — narration.md owns voice.
All functions pure, deterministic, stdlib-only, digit-free output (the guardrail test).
"""
from .records import PRIMARIES, direction_changes
from .errors import EngineError

# Class-B band edges: four absolute levels per primary. Provenance: design.md direction rule;
# cut points chosen so the probe's resting ranges (0.2-0.6) read as ordinary and the measured
# fever-arc peaks (0.85+) read as gripping. Probe-calibrated start.
_BANDS = (0.25, 0.55, 0.80)   # quiet | present | strong | gripping

# Per-primary STAGE DIRECTIONS, one per band (quiet, present, strong, gripping).
# These are INSTRUCTIONS TO ACT, not reports of feeling. design.md's compute/generate split calls
# for a "direction" the engine translates from the number; a description of interior state is a
# weaker thing -- handed a feeling, an actor narrates the feeling; handed a behaviour, it performs.
# Neutral register: states what the actor DOES, never how the scene looks. narration.md owns voice.
# Second person throughout (g6 portability): carries no gender, so no pronoun parameter is needed.
_PHRASES = {
    "SEEKING":     ("you wait to be handed the next thing",
                    "you ask the next question and reach for the next step",
                    "you drive at it, and each answer is only the way to the next question",
                    "you move before the room is ready and do not wait to be followed"),
    "FEAR":        ("you take the room at face value and do not check the ways out",
                    "you keep the ways out in view and let someone else commit first",
                    "you give ground, you hedge, you commit to nothing you cannot leave",
                    "you protect yourself first and account for it afterwards"),
    "RAGE":        ("you let slights pass without marking them",
                    "you answer sharper than you meant to and do not soften it",
                    "you name the offence out loud and refuse to let it pass",
                    "you square up and end it now, whatever it costs"),
    "LUST":        ("you do not look, and it does not occur to you to",
                    "you notice them, and your eyes keep going back",
                    "you close the distance and give them reason to notice you back",
                    "you make what you want plain to them, and you let the rest of the scene wait"),
    "CARE":        ("no one here has a claim on you, and your own business comes first",
                    "you will do a small thing for someone near you if it costs you little",
                    "you act for them before you have finished deciding to, and you interrupt yourself to do it",
                    "you put yourself between them and it, and what you wanted for yourself does not survive this"),
    "PANIC_GRIEF": ("you carry nothing extra",
                    "you answer late, and you leave part of it unsaid",
                    "you lose the thread of what you were doing, and you leave it where it fell",
                    "you stop, and what the scene wants from you does not reach you"),
    # DISGUST: the withdrawal responses. Where RAGE closes distance to settle a thing, DISGUST
    # opens it and stops treating the other party as someone a settlement is owed to — which is
    # why the gripping band is refusal to be in the same room rather than any kind of blow.
    "DISGUST":     ("you take things as they come and do not find them beneath you",
                    "you keep it at arm's length, and you touch no more of it than you must",
                    "you decline to touch it, and you let them see you decline",
                    "you will not be in the room with it, and you say so on your way out"),
    "PLAY":        ("everything lands at full weight and you lighten nothing",
                    "you let a joke through, and you do not chase it",
                    "you tease, and you take the edge off the room on purpose",
                    "you turn it into a game and pull everyone into playing"),
}

# REFLEXIVE STAGE DIRECTIONS — the same primitive, pointed at the self.
#
# `records.DIRECTEDNESS` decides WHICH primitives need these, by one law: a primitive needs its own
# reflexive directions exactly when its action tendency becomes INCOHERENT aimed at the self.
# Attack survives (you can go at yourself). Shutdown survives — it never pointed at anything, which
# is why PANIC_GRIEF, the most self-directed primitive in the vocabulary, needs none of these.
# Pursuit inverts: you cannot pursue what you already are, so it becomes display. Expulsion
# inverts: you cannot expel yourself from yourself, so it becomes concealment.
#
# Only the quiet band is shared with the object phrases. Every quiet phrase in this module is an
# ABSENCE description ("you let slights pass", "you carry nothing extra"), which is role-free by
# construction — there is no aboutness in a feeling that is not doing anything.
_REFLEXIVE_PHRASES = {
    # pursuit -> display. The basis licenses this as SEEKING-satisfied(self): the deed done, owned,
    # shown. Not hunger aimed inward — that is SEEKING at a prospect, an object bind.
    "SEEKING": (None,
                "you put your name to what you did and let that stand",
                "you bring what you did into the conversation and wait for it to be weighed",
                "you carry it like the answer to every question, and you cannot be told anything"),
    # expulsion -> concealment. The gripping cell is the exact inversion of the defect that
    # motivated this work: the object phrase leaves the room to escape the contaminant; here the
    # contaminant is you, so leaving is what you do FOR the others.
    "DISGUST": (None,
                "you offer less of yourself than the moment asks for",
                "you keep yourself out of what is offered to you, and you give no reason",
                "you take yourself out of the room, and it is the others you are sparing"),
}

# An UNBOUND primitive normally renders its ordinary phrase: restlessness, snappishness and
# fastidiousness with no object are displacement and mood, which is behaviourally honest.
#
# LUST is the exception, and the reason is specific. Its object phrases carry a deictic — "you
# notice THEM", "give THEM reason to notice you back" — so an actor handed one with nothing bound
# will attach it to whoever is in the room and INVENT A DESIRE THE NUMBERS NEVER AIMED, and with it
# a relationship the ledger never earned. That is canon created by a rendering accident. One phrase
# across all live bands on purpose: a mood without an object does not need three grades of
# instruction, and the rising/settling marker still carries the movement.
# A VALUE IS EITHER ONE PHRASE FOR EVERY LIVE BAND, OR A PER-BAND TUPLE WITH None WHERE THE
# ORDINARY OBJECT PHRASE IS ALREADY FINE. LUST needs the first: every one of its live bands points
# at somebody, so a single mood phrase loses nothing. CARE and DISGUST need the second — CARE band 1
# ("a small thing for someone near you") and DISGUST bands 1 and 3 are already objectless and carry
# real information, and blanking them to fix their neighbours would throw away three good bands to
# repair three bad ones.
#
# The criterion above was written for LUST on the day targets landed and then never applied to the
# other seven primitives. Scanned 2026-08-24: CARE bands 2-3 and DISGUST band 2 hand the actor a
# person-deictic with nothing bound. RAGE does NOT — its only "them" is band 0's, where the referent
# is SLIGHTS — so the RAGE entry this pass was scoped to add is not written. `tests/test_direction.py`
# now runs the scan, because a rule that lived in a comment for two days is not a rule.
_UNBOUND_PHRASES = {
    "LUST": "you are restless with wanting, and no one in the room is why",
    # CARE with no one to spend it on: the impulse is real and the beneficiary is not. Bands 0-1
    # keep their object phrases (neither names a person).
    "CARE": (None, None,
             "you set right whatever is nearest, and you are doing it before you decide to",
             "you would spend yourself down to nothing on this, and no one here is who it is for"),
    # DISGUST band 2's object phrase is a refusal made VISIBLE — "you let them see you decline" —
    # which invents a witness when there is none. The visibility is the content; the witness is not.
    "DISGUST": (None, None,
                "you decline to touch it, and you do not disguise the declining", None),
}

_DEV_THRESH = 0.15   # deviation from temperament mean that reads as rising/settling (Class-B, probe-calibrated start)

# ---------------------------------------------------------------------------------------------
# SLOPE — how fast it moved, which is a DIFFERENT question from how far it sits from rest.
#
# `_DEV_THRESH` above compares a value to the character's TEMPERAMENT MEAN: "elevated versus your
# resting state". Nothing compared turn N to turn N-1, so a character who leapt from the quiet band
# to the top in one beat received the identical phrase to one who climbed there over ten. *He had
# been getting angrier all evening* and *he snapped* were the same state to the renderer, and for a
# novel the slope is frequently the story.
#
# The two markers COMPOSE and do not overlap: a character can be steadily elevated and not moving
# (dev high, slope flat), or moving hard through their own normal range (dev low, slope steep).
#
# Class-B, probe-calibrated start, and set ABOVE `_DEV_THRESH` deliberately: a beat that moves a
# primary further than its whole distance-from-rest threshold is a lurch, and marking anything less
# would put a movement clause on almost every line. The clause is worth having because it is rare.
_SLOPE_THRESH = 0.20

# Condition bands (energy after allostatic weighting — same read the gate's budget uses).
_COND = ((0.25, "you take the shortest path and you will not do the thorough version of anything"),
         (0.50, "you do what is asked and none of the extra"),
         (0.75, "you can do the thorough version where it matters"),
         (2.00, "you have reserve to spend on more than is asked"))

# Relationship-edge bands per axis (relationships.md axes; same guardrail as affect).
_EDGE_BANDS = (0.25, 0.55, 0.80)
_EDGE_PHRASES = {
    "trust":    ("you check what they tell you against something else before you act on it",
                 "you act on their word for small things and verify the large ones",
                 "you act on their word without checking it",
                 "you would act on their word against your own read of the room"),
    "affinity": ("you keep it to the business and leave when the business is done",
                 "you are civil, and you do not seek them out",
                 "you make time for them and take their side by default",
                 "you would put yourself out for them before they thought to ask"),
    "respect":  ("you do not weight their opinion when you decide",
                 "you hear them out and then decide for yourself",
                 "you weigh their judgment against your own and sometimes it wins",
                 "where you are unsure, you do what they would do"),
    "debt":     ("you owe them nothing, and you act like it",
                 "you would do them a small favour unasked",
                 "you say yes when they ask and do not count it",
                 "what they ask of you, you do"),
}

_SURENESS = ((0.35, "you would not stake anything on it"),
             (0.65, "you act on it, but you would hear an argument"),
             (0.90, "you act on it without re-examining it"),
             (2.00, "you do not entertain the alternative"))


def _band(v, edges):
    for i, e in enumerate(edges):
        if v < e:
            return i
    return len(edges)


class DirectionError(EngineError):
    """A value reached the direction layer that it cannot turn into words."""


def _check_num(name, v):
    """A value bound for arithmetic, or a coded refusal naming it.

    This raised a bare ValueError carrying no code and, worse, no route back to the field. A book
    that put a sentence in a numeric slot died here on its first beat with
    `direction: value must be a number in [0,1], got 'it takes me over'` — which names neither the
    character nor the path, and `name` is literally "value" at the busiest call site
    (identity_view._phrase). The pre-flight now catches this class before a run
    (scripts/lint_book.py _numeric_slot_errors), so reaching HERE means the pre-flight was skipped.
    Say so, since that is the actionable part.
    """
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0.0 <= float(v) <= 1.0):
        raise DirectionError(
            "DIRECTION_VALUE_NOT_IN_UNIT_INTERVAL",
            "direction: %s must be a number in [0,1], got %r. A prose value in a numeric slot is "
            "the usual cause; `python scripts/lint_book.py --vault <book>` names the character and "
            "the exact field path before a run." % (name, v))
    return float(v)


def _phrase_for(primary, band, targets, me):
    """The stage direction for this primitive at this band, given what it is pointed at.

    Three cases, in the order the registry decides them:
      * bound to the CHARACTER and the registry says the direction changes -> the reflexive variant
        (`records.direction_changes`). PANIC_GRIEF is bound-to-self all the time and deliberately
        does NOT take this branch: its shutdown never pointed at anything. Until 2026-09-01 this
        line described the intent and the code below gated on `admits_role(p, "self")` — the
        `reflexive` column, which PANIC_GRIEF passes. Nothing rendered wrongly, because the phrase
        table happened to hold exactly the two direction-changing primitives; the law was enforced
        by an absent row rather than by the column that states it. Both halves are now checked:
        the branch reads the column, and `test_direction` asserts the table's keys EQUAL the
        direction_changes-True set.
      * bound to NOBODY and the primitive would otherwise hand the actor a dangling deictic -> the
        unbound phrase. LUST only; see `_UNBOUND_PHRASES`.
      * everything else -> the ordinary object phrase, which is what every caller got before targets
        existed, so a run with no target map is unchanged character for character.
    """
    bound = (targets or {}).get(primary)
    if bound is not None and me is not None and str(bound).lower() == str(me).lower():
        if direction_changes(primary):
            variant = _REFLEXIVE_PHRASES.get(primary)
            if variant and variant[band] is not None:
                return variant[band]
    elif bound is None and targets is not None and band >= 1:
        unbound = _UNBOUND_PHRASES.get(primary)
        if isinstance(unbound, tuple):
            if unbound[band] is not None:            # None = the object phrase is already objectless
                return unbound[band]
        elif unbound is not None:
            return unbound
    return _PHRASES[primary][band]


# A compound is named only when it CLEARLY leads. `compounds.recognise` returns a RANKED list on
# purpose: its docstring says ambiguity between two names is information — it means the basis cannot
# separate them — and collapsing that to one name would hide exactly what `separability()` exists to
# surface. So two gates, both Class-B calibration starts:
#   _NAME_FLOOR  — below this the vector is not really any named compound, it is just affect.
#   _NAME_MARGIN — the top must beat the runner-up by this much, or the honest answer is silence.
_NAME_FLOOR = 0.90
_NAME_MARGIN = 0.05


def name_compound(vector):
    """A live affect vector -> the name of the compound emotion it clearly is, or None.

    THE WIRING THAT DID NOT EXIST. `compounds.recognise` was implemented, tested, and called by
    nothing in src/ or scripts/ — a whole vocabulary the actor could never be handed. This is its
    first consumer.

    Returns a WORD, never a score: CLAUDE.md hard rule 5 keeps numbers out of the prompt, and
    tests/test_no_digits.py enforces it. Silence on an ambiguous vector is a real answer, not a
    failure to decide.
    """
    from .compounds import recognise                      # local: compounds imports records, keep the cycle short
    ranked = recognise(vector, top=2, floor=_NAME_FLOOR)
    if not ranked:
        return None
    if len(ranked) > 1 and (ranked[0][1] - ranked[1][1]) < _NAME_MARGIN:
        return None                                        # the basis cannot separate these two — say nothing
    return ranked[0][0]


def _slope_marker(primary, v, prev):
    """The movement clause for one primary since the previous COMMITTED turn, or "".

    `prev` is the previous affect vector, or None for a first turn / a caller that does not pass
    one — in which case there is no movement to describe and the line is what it always was.
    Returns a clause with no "; " in it, because that is this module's clause separator and a
    consumer splitting on it would mis-count (pinned by test_direction).
    """
    if not prev or primary not in prev:
        return ""
    try:
        delta = float(v) - float(prev[primary])
    except (TypeError, ValueError):
        return ""
    if delta >= _SLOPE_THRESH:
        return " and it came on you fast, this last moment"
    if delta <= -_SLOPE_THRESH:
        return " and it has just dropped away from you"
    return ""


def direct_affect(affect, temperament, targets=None, me=None, prev=None):
    """Affect vector -> one digit-free, second-person line of STAGE DIRECTIONS — what the actor
    DOES, not what it feels. Surfaces any primary at present level or above, or one deviating past
    _DEV_THRESH from its resting mean (with a rising/settling marker) — an anxious baseline must
    not read as a fresh spike, and a primary in the quiet band is genuinely not asking for
    attention.

    `prev` (the previous committed turn's affect vector) adds a MOVEMENT clause: how fast this got
    here, which is not the same question as how far it sits from rest. Omitted, no line changes.

    `targets` ({primary: target_id}) and `me` (this character's id) select the REFLEXIVE variant for
    a primitive bound to the character themselves, where the registry says its direction changes.
    Omitted, every phrase is the object phrase and output is identical to the pre-targets engine.

    The gate was `b >= 2` and that was NON-MONOTONIC: measured at temperament mean 0.65,
    CARE 0.30 and 0.45 both surfaced while 0.54 fell silent, telling the actor LESS was happening
    at higher care. Anything that has surfaced must keep surfacing as the value rises."""
    if not isinstance(affect, dict) or not isinstance(temperament, dict):
        raise DirectionError(
            "DIRECTION_PACKET_NOT_AN_OBJECT",
            "direction.direct_affect: affect and temperament must both be dicts, got %s and %s. "
            "This layer is the only thing standing between a stored number and the prompt "
            "(CLAUDE.md hard rule 5), so it refuses a packet it cannot read rather than "
            "translating part of one." % (type(affect).__name__, type(temperament).__name__))
    missing = [p for p in PRIMARIES if p not in affect]
    if missing:
        raise DirectionError(
            "DIRECTION_AFFECT_MISSING_PRIMARY",
            "direction.direct_affect: affect is missing %s. Every primary is described or the "
            "actor is told less is happening than the state says — a silent omission here reads "
            "to the actor as a feeling that is absent rather than one that went unrendered."
            % ", ".join(missing))
    parts = []
    for p in PRIMARIES:
        v = _check_num("affect[%s]" % p, affect[p])
        mean = _check_num("temperament[%s].mean" % p, temperament.get(p, {}).get("mean", 0.5))
        b = _band(v, _BANDS)
        dev = v - mean
        notable = b >= 1 or abs(dev) > _DEV_THRESH   # >=1, not >=2 — see the docstring
        if not notable:
            continue
        phrase = _phrase_for(p, b, targets, me)
        # Band 0 takes DIFFERENT markers. Its phrases are absence descriptions (the reflexive
        # tables depend on that), and an absence cannot be intensified: "you let slights pass
        # without marking them, more than is usual for you" asserted a stronger absence while the
        # value was RISING, and "you carry nothing extra, quieter than your usual" is a quieter
        # nothing. An absence SLIPS, or it is out of character; those are the two things it can do.
        if dev > _DEV_THRESH:
            phrase += ", though that is beginning to slip" if b == 0 else ", more than is usual for you"
        elif dev < -_DEV_THRESH:
            phrase += ", which is not like you" if b == 0 else ", quieter than your usual"
        # SLOPE last, because it qualifies the whole clause: where the deviation marker says how
        # this compares to your resting state, this says how fast you got here.
        phrase += _slope_marker(p, v, prev)
        parts.append(phrase)
    named = name_compound(affect)
    if named:
        parts.append("and what is on you has a name, and the name is %s" % named)
    # "; " is the CLAUSE SEPARATOR: no phrase above may contain it, or a consumer
    # splitting the line mis-counts. Pinned by test_direction:separator-not-in-phrases.
    return "; ".join(parts) if parts else "nothing here pulls at you, so act as you ordinarily would"


def direct_condition(condition):
    """Condition -> a digit-free line, via the same energy/load read the gate's budget uses."""
    if not isinstance(condition, dict):
        raise DirectionError(
            "DIRECTION_PACKET_NOT_AN_OBJECT",
            "direction.direct_condition: condition must be a dict, got %s"
            % type(condition).__name__)
    energy = _check_num("condition.energy", condition.get("energy", 1.0))
    load = _check_num("condition.allostatic_load", condition.get("allostatic_load", 0.0))
    effective = energy * (1.0 - load * 0.5)   # mirrors gate._energy_budget (one read, two surfaces)
    for edge, phrase in _COND:
        if effective < edge:
            return phrase
    return _COND[-1][1]


# SECOND ORDER (relationships.md rich layer: "what A thinks B feels about A"). Rendered as what the
# character EXPECTS FROM them, because that is what a second-order belief actually changes about
# behaviour — you do not act on someone's regard, you act on your reading of it. Same bands.
_THEIR_VIEW_PHRASES = {
    "trust":    ("they do not take your word for anything",
                 "they hear you out and check it after",
                 "they take you at your word",
                 "they would back your word against their own eyes"),
    "affinity": ("they would not notice if you stopped coming",
                 "they are civil with you and no more",
                 "they are glad of you and it shows",
                 "they would put themselves out for you before you asked"),
    "respect":  ("nothing you say changes what they do",
                 "they hear you out and then do as they intended",
                 "your read carries weight with them",
                 "where they are unsure, they do what you would do"),
    "debt":     ("they owe you nothing and act like it",
                 "they would do you a small favour unasked",
                 "they say yes when you ask",
                 "what you ask of them, they do"),
}


def direct_edge(edge):
    """One relationship edge dict -> digit-free standing description (axes per relationships.md).

    Renders both orders when both are present: what this character makes of them, and — from
    `edge["their_view"]` — what this character believes THEY make of this character. The gap between
    the two is the whole reason the second order exists: someone who adores a person they know to be
    indifferent has to be stageable differently from someone who believes it is returned.
    """
    if not isinstance(edge, dict):
        raise DirectionError(
            "DIRECTION_PACKET_NOT_AN_OBJECT",
            "direction.direct_edge: edge must be a dict, got %s" % type(edge).__name__)
    parts = []
    for axis in ("trust", "affinity", "respect", "debt"):
        if axis in edge:
            v = _check_num("edge.%s" % axis, edge[axis])
            parts.append(_EDGE_PHRASES[axis][_band(v, _EDGE_BANDS)])
    view = edge.get("their_view")
    if isinstance(view, dict):
        theirs = [_THEIR_VIEW_PHRASES[axis][_band(_check_num("their_view.%s" % axis, view[axis]),
                                                  _EDGE_BANDS)]
                  for axis in ("trust", "affinity", "respect", "debt") if axis in view]
        if theirs:
            parts.append("and as you read them, %s" % ", ".join(theirs))
    return ", ".join(parts) if parts else "no particular standing"


def sureness(confidence):
    """Belief confidence float -> digit-free sureness phrase (recall rendering)."""
    c = _check_num("confidence", confidence)
    for edge, phrase in _SURENESS:
        if c < edge:
            return phrase
    return _SURENESS[-1][1]
