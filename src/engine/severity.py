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
    extreme  0.95  is the only word that reaches bonds._CLIFF_SEVERITY (0.80)
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
# and `extreme` is the only rung reaching `bonds._CLIFF_SEVERITY`, the unforgivable act. So a
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
