"""severity.py — the event-strength vocabulary: seven engine-owned words on the existing 0..1 scale.

`docs/state-engine.md`:32-34 defines the appraisal magnitude as
`severity(e) x relevance(e, V, D) x trait_sensitivity(T, i)`, and :66-68 requires that these
magnitudes be ENGINE-owned, apply to everyone, and be "tuned by falsification, never guessed".

The SCALE was already engine-owned. The ANCHORS were not. Until this module the actor emitted a
bare float per dimension — `state.appraise`'s own docstring calls it "the raw dimension magnitude
emitted by the consolidation LLM (0..1)" — with nothing in the system fixing 0.2 against 0.3. Two
beats, two characters, two runs could not be compared, because severity was authored fresh by a
model each time. That is the same defect hard rule 5 fixes in the outbound direction (numbers never
reach the prompt); this is its inbound twin.

THE SCALE IS UNCHANGED, AND THAT IS THE POINT. Every threshold already calibrated against it keeps
its exact meaning:

    marked   0.60  meets  arc._DURABLE_DIM (0.60) and bonds._OVERT_SEVERITY (0.55)
    marked   0.60  meets  bonds._OVERT_SEVERITY (0.55) too — the cliff itself reads the ACT ladder's floor word, not a strength word (bond gate 4, 2026-09-17)
    marked+  0.60  is where consolidation._MISMATCH_THRESHOLD (0.5) starts checking

An earlier draft of this change rescaled the field instead — mapping the words onto a much smaller
"steady-state dose" range so that repeated small events accumulated. It was rejected on review, and
the reason is worth keeping: `dimensions` is read by SIX other tiers that key thresholds off the
0..1 severity meaning — `wound.trial` (:167, where a rescaled value inverts the sign of the
prediction error and makes every wound heal), `bonds` (:61, :180), `scene._salience`
(`scripts/scene.py`:55), `state._AT_REST` (:143), `direction._DEV_THRESH` (:125) and
`toward._LIMIT` (:54). Redefining what the field MEANS without changing its type is invisible to
every validator in the repo — the trust-boundary failure that "corrupts silently with nothing
logged". Words on the existing scale cost nothing downstream; a new scale costs all six.
"""
from .errors import EngineError


class SeverityError(EngineError):
    """An event-strength word that is not on the ladder."""


# The seven anchors. Ordered floor to ceiling; the gaps widen toward the top because the
# distinctions a writer can actually make are finer at the quiet end — the difference between
# `faint` and `slight` is a real one, the difference between two flavours of catastrophe is not.
_MAGNITUDE = {
    "faint":    0.05,
    "slight":   0.15,
    "mild":     0.30,
    "moderate": 0.45,
    "marked":   0.60,
    "severe":   0.78,
    "extreme":  0.95,
}

# Public, ordered floor to ceiling. `prompt.py` renders this into the reply contract, which
# CLAUDE.md hard rule 5 exempts from the no-numbers law precisely because the contract "defines
# the scale the actor writes ON, not them".
WORDS = tuple(sorted(_MAGNITUDE, key=_MAGNITUDE.get))


def value_of(word):
    """One word -> its float on the 0..1 severity scale. Raises SeverityError if off-ladder."""
    key = str(word).strip().lower()
    if key not in _MAGNITUDE:
        raise SeverityError("SEVERITY_WORD_UNKNOWN",
            "severity.value_of: %r is not an event-strength word; expected one of: %s"
            % (word, ", ".join(WORDS)))
    return _MAGNITUDE[key]


def normalise_dimensions(tags):
    """Resolve severity WORDS in `tags["dimensions"]` to floats. Pure — returns a new dict.

    THE TRUST BOUNDARY, and it is deliberately shallow. This runs on the parsed reply before
    anything reads `dimensions`, so `validate_tags`, `state.appraise`, `wound.trial`,
    `bonds.act_from_tags`, `arc.assess` and `scene._salience` all receive exactly the float they
    have always received. Nothing downstream learns that words exist.

    A float passes through UNTOUCHED. That is what keeps every existing fixture, test and recorded
    run byte-identical, and it is why this change needs no migration: the two forms coexist and the
    engine cannot tell them apart after this call.

    Raises SeverityError on an off-ladder word rather than flagging it — hard rule 6, modules fail
    loud. A word the engine cannot price is not a degraded reading, it is an unpriceable event, and
    the drivers already treat an unusable self-report as a refusal (`consolidation.tag_refusal`).
    """
    if not isinstance(tags, dict):
        return tags
    dims = tags.get("dimensions")
    if not isinstance(dims, dict):
        return tags
    resolved = {}
    for dim, val in dims.items():
        resolved[dim] = value_of(val) if isinstance(val, str) else val
    return dict(tags, dimensions=resolved)

# What each word MEANS. Three parts per rung, because a grader needs all three:
#   meaning  — what the word asserts about the event
#   boundary — the test that separates it from the rung BELOW it, phrased so a reader of the
#              scene can actually run it. An ordering without boundaries is not calibration:
#              every model knows `severe` outranks `mild` and none knows which one a given
#              insult earns.
# The anchors are consequence-shaped because the engine's own thresholds are — `marked` is
# exactly `arc._DURABLE_DIM`, the line past which a repeated event starts reshaping a person,
# and `extreme` is the worst of its kind (the relationship cliff reads the act ladder's floor word, not a strength word, since bond gate 4). So a
# grader is never asked to judge an adjective; it is asked what the event WOULD DO, which is a
# question about the scene in front of it.
#
# `docs/design.md`'s compute/generate split and CLAUDE.md hard rule 3 put this here rather than
# in an agent file: the engine owns the scale and the vocabulary; the LLM reads the beat and
# picks the word; the engine turns the word back into arithmetic. Nothing about the number is
# the grader's business, and nothing about the reading is the engine's.
_GLOSS = (
    ("faint",
     "registered, and did not persist",
     "the floor — below this the dimension is simply omitted"),
    ("slight",
     "noticed, and gone by the next thing that happened",
     "vs faint: they could tell you it happened without being asked"),
    ("mild",
     "carried into the next few minutes; it colours the immediate reply, then lets go",
     "vs slight: it touches the very next thing they do"),
    ("moderate",
     "carried for the rest of the day; it returns unbidden when the day goes quiet",
     "vs mild: it survives a change of subject"),
    ("marked",
     "would begin to change them if it kept happening; one instance does not reshape them, "
     "a pattern of it would",
     "vs moderate: repetition would leave a different person"),
    ("severe",
     "reshapes them on its own; they are measurably different afterwards with no repetition",
     "vs marked: ONE instance is enough"),
    ("extreme",
     "the worst of its kind a life contains",
     "vs severe: there is no version of this event that could be worse"),
)


def gloss():
    """The ladder as one short contract line: `word (meaning)`, floor to ceiling.

    The compact form, for a prompt that must also carry a scene. `rubric()` is the full one.
    """
    return ", ".join("%s (%s)" % (w, meaning) for w, meaning, _ in _GLOSS)


def rubric():
    """The full grading definition — meaning AND the boundary against the rung below.

    For the seat that grades a beat from the recorded stream. Contract text only; no engine
    module reads it. The engine holds the arithmetic, the reader holds the reading — the same
    division `.claude/agents/recorder.md` already states for belief erosion ("say what has faded
    and by how much in words, never a number").
    """
    return chr(10).join("%s — %s. [%s]" % (w, meaning, boundary) for w, meaning, boundary in _GLOSS)

# ---------------------------------------------------------------------------
# THE BOND LADDERS — what an act SHOWED (inbound) and where an edge STANDS (outbound)
# ---------------------------------------------------------------------------
# `docs/bond-arithmetic.md` section 2. Two vocabularies per relationship axis, both on the 0..1 axis
# scale the edges already use (`bonds._NEUTRAL` 0.5 = a stranger). They replace the 2026-09-16 read
# ladder (`_READ`, seven words with a named `neutral`), retired the next day for one reason: a seat
# that must name a rung for an axis it has little to say about names the middle one, and a level
# named on every beat is exactly the "every beat moves every axis" failure the old `social` block
# had. So the ACT ladder has NO neutral word — an axis the act says nothing about is OMITTED — and
# the seat's skeleton shows one axis filled and the rest absent.
#
# THE ACT LADDER is what the event seat answers in: a quality THIS ACT showed, never a standing (a
# loyal man being slack today is `slack`). Four rungs a side, heights symmetric about the stranger.
# The floor word on each axis is the only read that reaches the trust cliff (`bonds._CLIFF_FLOOR`
# 0.15), and the contract text says it means betrayal, not unreliability. Each rung carries a
# gloss and a boundary against the rung nearer the middle, as `_GLOSS` does for strength, so a read
# is arguable and a number is not. Debt is not on a ladder: it is an ACCOUNT, and the seat writes
# signed entries (`DEBT_ENTRIES`) whose magnitude is the beat's dimension severity.
#
# THE STANDING LADDER is where an edge sits, derived from the float by band — `rungs.rung_at`'s
# twin — for the calibration thermometer and the log. The live beat seat never answers in these:
# it rates what an onlooker could see (its rule 1) and a standing is an interior it cannot see. The
# actor keeps `direction._EDGE_PHRASES`' four decision-shaped blocks (nine words, four blocks —
# nine authored blocks only once `block_fidelity` shows an actor plays `faith` unlike `assurance`).
# Words checked against the 92 emotion rung names, the nine path names and the engine's own tokens.
_ACT = {
    "trust":    (("treacherous", 0.10), ("dishonest", 0.22), ("unreliable", 0.34), ("slack", 0.44),
                 ("dependable", 0.56), ("straight", 0.66), ("loyal", 0.78), ("steadfast", 0.90)),
    "affinity": (("cruel", 0.10), ("harsh", 0.22), ("cold", 0.34), ("curt", 0.44),
                 ("civil", 0.56), ("kind", 0.66), ("generous", 0.78), ("selfless", 0.90)),
    "respect":  (("disgraceful", 0.10), ("inept", 0.22), ("careless", 0.34), ("middling", 0.44),
                 ("capable", 0.56), ("sharp", 0.66), ("masterly", 0.78), ("commanding", 0.90)),
}
ACT_AXES = tuple(_ACT)                                  # the three ladder axes; debt is an account
ACT_WORDS = {axis: tuple(w for w, _ in rows) for axis, rows in _ACT.items()}
_ACT_VALUE = {axis: dict(rows) for axis, rows in _ACT.items()}
ACT_FLOOR = {axis: rows[0][0] for axis, rows in _ACT.items()}   # the betrayal-grade word per axis

# what the act showed, per rung: gloss, and the boundary against the rung nearer the stranger
_ACT_GLOSS = {
    "trust": {
        "treacherous": ("betrayed a trust: broke faith with someone who relied on them", "vs dishonest: someone was relying on them, and they knew it"),
        "dishonest":   ("lied, cheated or concealed to their own advantage", "vs unreliable: the failure was chosen, not slipped"),
        "unreliable":  ("failed to do what they said or what was theirs to do", "vs slack: it fell to someone else to make good"),
        "slack":       ("did the thing late, short or carelessly", "vs omit: something visibly went undone"),
        "dependable":  ("did what was theirs to do, as said", "vs omit: someone was counting on it"),
        "straight":    ("told an unwelcome truth or owned a fault plainly", "vs dependable: it cost them something to say"),
        "loyal":       ("stood by someone when it would have been easier not to", "vs straight: a side was taken"),
        "steadfast":   ("held to someone through real cost or danger", "vs loyal: they could have lost something and stayed"),
    },
    "affinity": {
        "cruel":    ("hurt someone for its own sake, or enjoyed it", "vs harsh: the hurt was the point"),
        "harsh":    ("dealt a hurt the situation did not require", "vs cold: something was done, not withheld"),
        "cold":     ("withheld warmth or help that was plainly wanted", "vs curt: the withholding was seen and meant"),
        "curt":     ("gave the least the moment allowed, with an edge", "vs omit: the edge was visible; reserve alone is omit"),
        "civil":    ("gave ordinary courtesy where it was not owed", "vs omit: something was extended, not just not withheld"),
        "kind":     ("gave help or ease at some small cost to themselves", "vs civil: it cost them"),
        "generous": ("gave more than was asked or fair, at real cost", "vs kind: the cost was plain to anyone"),
        "selfless": ("put the other before themselves at serious cost", "vs generous: they lost something that mattered"),
    },
    "respect": {
        "disgraceful": ("acted beneath any standing: shameful in front of others", "vs inept: not a failure of skill but of conduct"),
        "inept":       ("failed at a thing they claimed or were expected to do", "vs careless: they could not, not would not"),
        "careless":    ("did a thing they can do, badly, from not attending", "vs middling: the failure was avoidable"),
        "middling":    ("did the thing adequately and no more", "vs omit: competence was on display and was ordinary"),
        "capable":     ("did a hard thing competently", "vs omit: the difficulty was visible"),
        "sharp":       ("saw or solved what others present did not", "vs capable: the insight, not the execution, stood out"),
        "masterly":    ("did a hard thing with a skill that others would study", "vs sharp: the execution was the point"),
        "commanding":  ("carried the room or the moment by competence alone", "vs masterly: others deferred without being asked"),
    },
}

# DEBT is an account. Its two POSTINGS (2026-09-18): `gave` on the receiver's account, `repaid` on the
# giver's own — derived by `bonds.debt_postings` from the seat's TRANSFERS (what changed hands, on what
# terms), never answered by the seat as a word. `refused` and `called in` were entries until this date;
# neither posts (the account moves when the owed thing is DELIVERED), so they are gone from the list.
DEBT_ENTRIES = ("gave", "repaid")
# TERMS: what a transfer was SAID to be — the one judgment the seat keeps on the account, and it is a
# fact about the words of the beat: a wage or a purchase is `price` (square), `loan` is to be returned
# or worked off, `repayment` is given against something already owed, `none` is nothing said.
TRANSFER_TERMS = ("none", "price", "loan", "repayment")
# THE DERIVED WORD (2026-09-18, gate seat-told): one rung per axis the seat is NOT offered. Measured
# three times on the same 28 beats (bare words, the quote check, the transfers contract) the seat named
# `straight` on 11, 9 and 9 of 14 against a 4-8 band — the span it quoted was in the text and did not
# show the word. The rung stays on the engine's ladder (act_value_of prices it; the fold and the log
# are unchanged); the seat reports the FACT under it instead — a `told` row: what was said, to whom,
# at what COST to the teller (`fault` — owned an error or a wrong of their own; `exposure` — named a
# loss, a weakness or a liability of their own the other could use; `none` — plain speech, an answer,
# an order, a warning) — and `appraiser.parse_event_reply` derives the rung at the seam when the cost
# is not `none` and the seat named no trust word. A seat that writes the word is refused.
ACT_DERIVED = {"trust": "straight"}
TOLD_COSTS = ("fault", "exposure", "none")


def act_value_of(axis, word):
    """(axis, act word) -> its height on the bipolar 0..1 axis scale. Raises SeverityError off-ladder.

    A strength word, a standing word or a debt entry handed here is refused, not reinterpreted: the
    three vocabularies share no token, so nothing is ambiguous, and a wrong-ladder word is the seat
    answering a question it was not asked.
    """
    key = str(word).strip().lower()
    if axis not in _ACT_VALUE:
        raise SeverityError("SEVERITY_ACT_AXIS_UNKNOWN",
            "severity.act_value_of: %r is not an act-ladder axis; expected one of: %s" % (axis, ", ".join(ACT_AXES)))
    if key not in _ACT_VALUE[axis]:
        raise SeverityError("SEVERITY_ACT_WORD_UNKNOWN",
            "severity.act_value_of: %r is not an act word on %s; expected one of: %s"
            % (word, axis, ", ".join(ACT_WORDS[axis])))
    return _ACT_VALUE[axis][key]


def act_rubric(axis):
    """The act ladder for one axis as contract text: `word — meaning [boundary]`, floor to ceiling,
    with the omission rule stated where the middle would be. For the event seat's prompt."""
    rows = []
    derived = ACT_DERIVED.get(axis)
    for w, _ in _ACT[axis]:
        if w == derived:
            rows.append("(%s is not yours to name: it is derived from `told` — see below)" % w)
            continue
        meaning, boundary = _ACT_GLOSS[axis][w]
        rows.append("%s — %s. [%s]" % (w, meaning, boundary))
    rows.insert(4, "(no middle word: an act that showed nothing on this axis is OMITTED, and that is the usual answer)")
    return chr(10).join(rows)


# ---------------------------------------------------------------------------
# ATTRIBUTION — why an act happened, not what it did (relationships.md:29; bond-arithmetic.md s4/s6,
# gate `seat-attribution`, 2026-09-19). THE LAW'S FIFTH INPUT: `bonds._ATTRIBUTION` has priced this
# since bond gate 4, and nothing live ever wrote it — every beat read `unknown` (full weight). D2:
# the EVENT SEAT is the producer, not the actor (the actor's own self-tag, `prompt.py`, stays as the
# stub double and the seat-refusal fallback only).
#
# A CLOSED FOUR, not the six `bonds._ATTRIBUTION` prices. `malice` is not offered: the seat rates
# what an onlooker could see (its rule 1), an onlooker cannot see a malicious WILL any better than an
# intentional one without the interior, and the two price identically (`bonds._ATTRIBUTION`: malice
# == intent == 1.0), so nothing is lost by folding it into `intent`. `unknown` is not offered either:
# it is the OMISSION itself — the seat leaves the field out — never a word the seat writes.
#
# NO LADDER, NO FLOOR-TO-CEILING CLAIM. These are four qualitatively different accounts of a will,
# not heights on one axis, so `attribution_rubric()` (unlike `act_rubric`) takes no axis and orders
# nothing.
ATTRIBUTION_WORDS = ("intent", "negligence", "coerced", "accident")

# meaning, then the boundary against the account it is most likely mistaken for.
_ATTRIBUTION_GLOSS = (
    ("intent",
     "done knowingly and on purpose",
     "vs negligence: they saw it coming and meant it, not merely should have"),
    ("negligence",
     "should have known, and did not think",
     "vs intent: nothing was meant by it — the failure was not thinking, not choosing"),
    ("coerced",
     "made to do it; they would not have done it otherwise",
     "vs negligence: the will belonged to someone else, not merely absent"),
    ("accident",
     "a hand slipped: no fault in the will at all",
     "vs negligence: there was nothing here to have thought of"),
)


def attribution_rubric():
    """The four accounts of WHY, as contract text: `word — meaning [boundary]`. For the event seat's
    prompt (bond-arithmetic.md s4). Omitting the field entirely means `unknown`, priced at full
    weight by `bonds._ATTRIBUTION` — the same reading an untagged act has always had."""
    return chr(10).join("%s — %s. [%s]" % (w, meaning, boundary) for w, meaning, boundary in _ATTRIBUTION_GLOSS)


# ---- the standing ladder: where an edge sits, by band. Outbound only. ----
_STANDING = {
    "trust":    ("betrayer", "distrust", "suspicion", "caution", "stranger", "reliance", "assurance", "faith", "absolute"),
    "affinity": ("hatred", "dislike", "coolness", "reserve", "stranger", "amity", "affection", "closeness", "devotedness"),
    "respect":  ("contempt", "disdain", "dismissal", "doubt", "stranger", "credit", "esteem", "admiration", "reverence"),
}
STANDING_WORDS = dict(_STANDING)
# the stranger band, then four even bands a side: [0,.1175,.235,.3525,.47 | .53,.6475,.765,.8825,1]
_STRANGER = (0.47, 0.53)
_STANDING_EDGES = tuple([i * (_STRANGER[0] / 4.0) for i in range(1, 5)] +
                        [_STRANGER[1] + i * ((1.0 - _STRANGER[1]) / 4.0) for i in range(0, 4)])
DEBT_STANDING = (("owed to you", -1.0), ("square", 0.0), ("a favour", 0.15), ("an obligation", 0.35),
                 ("a debt", 0.60), ("bound", 0.85))


def standing_of(axis, value):
    """(axis, edge float 0..1) -> the standing word: the band the float sits in. Nine bands tile
    [0, 1]; the stranger band is [.47, .53). Debt is an account and has its own scale (`DEBT_STANDING`)."""
    if axis not in _STANDING:
        raise SeverityError("SEVERITY_STANDING_AXIS_UNKNOWN",
            "severity.standing_of: %r has no standing ladder; expected one of: %s" % (axis, ", ".join(_STANDING)))
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise SeverityError("SEVERITY_STANDING_NOT_A_NUMBER",
            "severity.standing_of: %r is not a number on the 0..1 axis scale" % (value,))
    v = 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)
    for i, edge in enumerate(_STANDING_EDGES):
        if v < edge:
            return _STANDING[axis][i]
    return _STANDING[axis][-1]
