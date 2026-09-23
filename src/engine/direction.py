"""direction.py — numbers to qualitative DIRECTION (gate 5, the backstage guardrail).

design.md: "the engine computes fear 8/10; what enters the prompt is 'gripped by fear' — a
qualitative direction the engine translates from the number. The LLM never sees raw stats;
numbers live in the DB; directions live in the prompt." relevancy-gate.md: "the prose never
says 'spent 3 focus'."

Phrasing is NEUTRAL qualitative description, not prose flourish — narration.md owns voice.
All functions pure, deterministic, stdlib-only, digit-free output (the guardrail test).
"""
from .records import PATHS, direction_changes
from .condition import body_view, has_reserves, mind_view   # the two sides of a split pool
from .errors import EngineError
from .presence import display_name as _display_name


# Condition bands (energy after allostatic weighting — same read the gate's budget uses).
_COND = ((0.25, "you take the shortest path and you will not do the thorough version of anything"),
         (0.50, "you do what is asked and none of the extra"),
         (0.75, "you can do the thorough version where it matters"),
         (2.00, "you have reserve to spend on more than is asked"))
# THE BODY'S SIDE (gate energy-reserves), said only when it stands in a different band from the mind's - the
# owner: "a person can never use all energy for one type of activity". Same edges as the mind's bands.
_BODY_COND = ((0.25, "your body is spent, and every movement costs you"),
              (0.50, "your body is tired and wants to stop"),
              (0.75, "your body has enough for what the day asks"),
              (2.00, "your body is fresh and has more to give"))

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


# NO COMPOUND NAME IS APPENDED HERE, and the absence is deliberate. `compounds.recognise` scored by
# cosine, which is scale-invariant by construction — so a pure RAGE vector returned `fury` at 0.10 as
# readily as at 0.95, and at 0.10 the band-0 phrase is filtered out below, leaving that name as the
# WHOLE direction: a barely-irritated character told to play a fury. Measured and written down at
# `docs/emotion-dynamics.md` lines 616-621, which retires compounds as a naming basis. Naming a
# magnitude belongs to the path layer, which reads position on an axis rather than the angle of a
# vector. Do not re-wire a cosine matcher into this module.


def direct_condition(condition):
    """Condition -> a digit-free line, via the same energy/load read the gate's budget uses."""
    if not isinstance(condition, dict):
        raise DirectionError(
            "DIRECTION_PACKET_NOT_AN_OBJECT",
            "direction.direct_condition: condition must be a dict, got %s"
            % type(condition).__name__)
    # ABSENT IS SILENCE (gate systems-registry, 2026-09-22; identity_view's own rule): a character whose
    # book does not run the condition system carries no condition, and the 1.0 / 0.0 defaults below used
    # to render the TOP band - "reserve to spend" - a state the engine had no grounds for. "" says nothing.
    if "energy" not in condition and "allostatic_load" not in condition:
        return ""
    energy = _check_num("condition.energy", condition.get("energy", 1.0))
    load = _check_num("condition.allostatic_load", condition.get("allostatic_load", 0.0))
    if has_reserves(condition):          # BOTH SIDES (gate energy-reserves): the mind's band, and the body's when it differs
        mind = _band_of(_COND, mind_view(condition) * (1.0 - load * 0.5))
        body = _band_of(_BODY_COND, body_view(condition) * (1.0 - load * 0.5))
        return _COND[mind][1] if mind == body else "%s; %s" % (_COND[mind][1], _BODY_COND[body][1])
    effective = energy * (1.0 - load * 0.5)   # mirrors gate._energy_budget (one read, two surfaces)
    return _COND[_band_of(_COND, effective)][1]


def _band_of(table, effective):
    """The index of the first band whose edge `effective` falls below (the last band past every edge)."""
    for i, (edge, _phrase) in enumerate(table):
        if effective < edge:
            return i
    return len(table) - 1


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


# WHAT ONE PERSON STIRS (gate toward-from-readings, 2026-09-11; re-based on the BALANCE 2026-09-12).
# The vector is what a present person moves the PLAYED state by, relative to the mood — the
# composed value toward them minus the mood (toward.balance) — in words. Plain words, never a rung
# name (the composer withholds rung names from the actor by measurement) and never a number (hard
# rule 5). Signed: a person whose attitude runs above the mood raises a path; a cooler person is
# met halfway down and lowers it. Two bands on the path's own scale — a faint stir under
# _STIRS_PLAIN, a plain one above; below _STIRS_FAINT nothing is said.
_STIRS_FAINT = 0.02          # below this the vector is noise and says nothing
_STIRS_PLAIN = 0.10          # at or above this the phrase drops "a little"
_STIRS_PHRASES = {
    #  path            raises the path                                       lowers it
    "STIRRING":    ("they pull your attention",                              "they dull you"),
    "WARINESS":    ("you keep half an eye on them",                          "you let your guard down near them"),
    "DISPLEASURE": ("they get under your skin",                              "they take the heat out of you"),
    "GOODWILL":    ("you go soft near them",                                 "they leave you cold"),
    "DEFLATION":   ("the sight of them sits on your chest",                  "they lift the weight off you"),
    "DISTASTE":    ("something in them turns your stomach",                  "nothing in them offends you"),
    "RECEPTIVITY": ("you open up around them",                               "they close you up"),
    "SELF-REGARD": ("in front of them you stand taller",                     "in front of them you feel small"),
    "LEVITY":      ("you cannot keep a straight face near them",             "they take the play out of you"),
}


def direct_stirs(vec, at_most=2):
    """{path: signed delta} -> a digit-free phrase for what a present person stirs, or "".

    The one or two LARGEST entries by size, joined; anything under _STIRS_FAINT is silence. Returns
    "" for a missing, empty or all-faint vector so the caller can append nothing at all.
    """
    if not isinstance(vec, dict) or not vec:
        return ""
    picked = []
    for path, v in vec.items():
        if path not in _STIRS_PHRASES:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            raise DirectionError("DIRECTION_VALUE_NOT_IN_UNIT_INTERVAL",
                                 "direction.direct_stirs: %s must be a number, got %r" % (path, v))
        if abs(f) >= _STIRS_FAINT:
            picked.append((abs(f), path, f))
    picked.sort(reverse=True)
    parts = []
    for size, path, f in picked[:max(1, int(at_most))]:
        phrase = _STIRS_PHRASES[path][0 if f > 0 else 1]
        parts.append(phrase if size >= _STIRS_PLAIN else "a little, %s" % phrase)
    return "; ".join(parts)


# WHAT IS YOURS HERE (bond-arithmetic.md s7; attachments.py's four relation words, bond gate
# `attachments-to-actor`). A hold prices a place or group the character keeps something IN, not a
# person — `attachments.py` owns the table and derives the word from the hold (`word_of`); this
# module owns only the phrase each word reads as, same register as `_EDGE_PHRASES` and
# `_STIRS_PHRASES`: second person, present tense, never a number. `scene.assemble` decides WHICH
# holds are in scope this turn (present, or the beat's own subject) and hands rows of
# {entity, name, word}; this renders them and nothing else.
_HOLDS_PHRASES = {
    "life":       "your life's work; losing it would change your days",
    "post":       "yours while you keep it, and it could be taken",
    "member":     "one of the things you belong to",
    "acquainted": "a place you know and pass through",
}


def direct_holds(rows):
    """[{"entity", "name", "word"}] -> "<name> — <phrase>; ..." joined, or "" for no rows.

    `entity` rides each row for the caller's own bookkeeping (the manifest key `scene.assemble`
    records beside it) and is never rendered — only `name` and `word` reach the actor, and `word`
    only as the phrase it prices, never as itself. An unpriced word refuses rather than rendering
    the raw word or silently dropping the row — the same choice `direct_edge` makes for a
    malformed edge.
    """
    if not isinstance(rows, list):
        raise DirectionError(
            "DIRECTION_LIST_PACKET_NOT_A_LIST",
            "direction.direct_holds: rows must be a list, got %s" % type(rows).__name__)
    parts = []
    for row in rows:
        if not isinstance(row, dict):
            raise DirectionError(
                "DIRECTION_PACKET_NOT_AN_OBJECT",
                "direction.direct_holds: each row must be a dict, got %s" % type(row).__name__)
        word = str(row.get("word") or "").strip().lower()
        if word not in _HOLDS_PHRASES:
            raise DirectionError(
                "DIRECTION_HOLD_WORD_UNKNOWN",
                "direction.direct_holds: %r is not a relation word; expected one of %s"
                % (row.get("word"), ", ".join(sorted(_HOLDS_PHRASES))))
        name = str(row.get("name") or "").strip()
        parts.append("%s — %s" % (name, _HOLDS_PHRASES[word]))
    return "; ".join(parts)


# WHAT HAS HAPPENED HERE (gate scene-facts-to-actor, 2026-09-22). The terms a transfer may carry
# (`severity.TRANSFER_TERMS`) and the cost a telling may carry, as clauses in the actor's own
# register. Unknown word REFUSES rather than rendering itself or dropping the row — `direct_holds`
# and `direct_edge` make the same choice, for the same reason: a silently dropped fact is the defect
# this whole section exists to answer.
_PASSED_CLAUSES = {
    "none":      "%s handed %s to %s",
    "price":     "%s paid %s to %s",
    "loan":      "%s lent %s to %s",
    "repayment": "%s repaid %s to %s",
}
_TOLD_CLAUSES = {
    "none":      "%s told %s: %s",
    "exposure":  "%s told %s, at %s own exposure: %s",
    "fault":     "%s owned a fault to %s: %s",
}
_SAID_ALOUD = "%s said aloud: %s"        # a telling with no hearer, or to the teller themself


def _who(ident, me, names):
    """An id -> "you" for the reader, else a display name, else "someone".

    `display_name` is IMPORTED, not re-implemented: one spelling of id-to-name in the tree is the
    rule this repo has paid for seven times (CLAUDE.md's duplicates table). An explicit `names` map
    still wins, for a caller that knows a better label than the id can carry.
    """
    if ident and ident == me:
        return "you"
    if not ident:
        return "someone"
    return str((names or {}).get(ident) or _display_name(ident))


def _passed_clause(row, me, names):
    terms = str(row.get("terms") or "none").strip().lower()
    if terms not in _PASSED_CLAUSES:
        raise DirectionError(
            "DIRECTION_FACT_TERMS_UNKNOWN",
            "direction.direct_facts: %r is not a transfer term; expected one of %s"
            % (row.get("terms"), ", ".join(sorted(_PASSED_CLAUSES))))
    return _PASSED_CLAUSES[terms] % (_who(row.get("from"), me, names), row["what"],
                                     _who(row.get("to"), me, names))


def _told_clause(row, me, names):
    cost = str(row.get("cost") or "none").strip().lower()
    if cost not in _TOLD_CLAUSES:
        raise DirectionError(
            "DIRECTION_FACT_COST_UNKNOWN",
            "direction.direct_facts: %r is not a telling cost; expected one of %s"
            % (row.get("cost"), ", ".join(sorted(_TOLD_CLAUSES))))
    teller = _who(row.get("speaker"), me, names)
    hearer_id = row.get("to")
    if not hearer_id or hearer_id == row.get("speaker"):
        return _SAID_ALOUD % (teller, row["what"])
    heard = _who(hearer_id, me, names)
    if cost == "exposure":
        return _TOLD_CLAUSES[cost] % (teller, heard, "your" if teller == "you" else "their",
                                      row["what"])
    return _TOLD_CLAUSES[cost] % (teller, heard, row["what"])


def direct_facts(rows, me, names=None):
    """Fact rows (scene_facts) -> two sentences, most recent first within each, or "".

    TWO REGISTERS, deliberately (gate `scene-facts-fix`, 2026-09-22, on the review's advice).
    What CHANGED HANDS the actor saw happen; the section asks it to stay consistent with that. What
    was SAID is only what was said — a quote of speech, which may be false, misheard, or a lie — so it
    is rendered "as you heard it" and never as settled fact. Rendering both as one list under "do not
    contradict it" would let one mis-read or false line bind every beat after it.

    NO TURN STAMPS: order carries recency, and a turn number means nothing to the person. The quoted
    `what` is the seat's own span of the action, so a quantity inside it is story content, not a
    number describing the character (test_no_digits bans DECIMALS describing the character).
    """
    if not isinstance(rows, list):
        raise DirectionError(
            "DIRECTION_LIST_PACKET_NOT_A_LIST",
            "direction.direct_facts: rows must be a list, got %s" % type(rows).__name__)
    passed, told = [], []
    for row in rows:
        if not isinstance(row, dict):
            raise DirectionError(
                "DIRECTION_PACKET_NOT_AN_OBJECT",
                "direction.direct_facts: each row must be a dict, got %s" % type(row).__name__)
        if not str(row.get("what") or "").strip():
            raise DirectionError("DIRECTION_FACT_EMPTY",
                                 "direction.direct_facts: a fact row carries no `what`")
        row = dict(row, what=str(row["what"]).strip())
        kind = row.get("kind")
        if kind == "passed":
            passed.append(_passed_clause(row, me, names))
        elif kind == "told":
            told.append(_told_clause(row, me, names))
        else:
            raise DirectionError(
                "DIRECTION_FACT_KIND_UNKNOWN",
                "direction.direct_facts: %r is not a fact kind; expected passed or told" % (kind,))
    parts = []
    if passed:
        parts.append("What changed hands: %s." % "; ".join(passed).rstrip(".!?"))
    if told:
        # a quoted line usually ends with its own stop; strip it rather than double it
        parts.append("What was said, as you heard it: %s." % "; ".join(told).rstrip(".!?"))
    return " ".join(parts)


# How an injury reads, in words (gate injuries): `injuries.stage`'s three values, never a number.
_INJURY_STAGES = {"fresh": "fresh", "healing": "healing", "mark": "healed, but it left its mark"}


def direct_injuries(rows, me, names=None):
    """Injury rows (`injuries.for_actor`) -> one sentence, or "": who is hurt, the words that show it, and how
    it reads now. The quote is the reader's span of the act (or the author's own words, for a sheet's injury),
    so what it says is story content; the stage is a word."""
    if not isinstance(rows, list):
        raise DirectionError("DIRECTION_LIST_PACKET_NOT_A_LIST",
                             "direction.direct_injuries: rows must be a list, got %s" % type(rows).__name__)
    parts = []
    for row in rows:
        if not isinstance(row, dict):
            raise DirectionError("DIRECTION_PACKET_NOT_AN_OBJECT",
                                 "direction.direct_injuries: each row must be a dict, got %s" % type(row).__name__)
        what = str(row.get("what") or "").strip().rstrip(".!?")
        if not what:
            raise DirectionError("DIRECTION_FACT_EMPTY", "direction.direct_injuries: an injury row carries no `what`")
        if row.get("stage") not in _INJURY_STAGES:
            raise DirectionError("DIRECTION_INJURY_STAGE_UNKNOWN",
                                 "direction.direct_injuries: %r is not a stage; expected one of %s"
                                 % (row.get("stage"), ", ".join(_INJURY_STAGES)))
        parts.append('%s - "%s" (%s)' % (_who(row.get("who"), me, names), what, _INJURY_STAGES[row["stage"]]))
    return ("Who is hurt, as you know it: %s." % "; ".join(parts)) if parts else ""


def sureness(confidence):
    """Belief confidence float -> digit-free sureness phrase (recall rendering)."""
    c = _check_num("confidence", confidence)
    for edge, phrase in _SURENESS:
        if c < edge:
            return phrase
    return _SURENESS[-1][1]
