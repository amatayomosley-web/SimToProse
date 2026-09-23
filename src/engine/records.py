"""records.py — typed record contracts for everything the engine writes (record-contract.md).

Validation lives at the boundary: a record validates completely or the write refuses — fail loud,
no coercion, no partial acceptance. Downstream read-requirements ARE upstream write-requirements,
so each record here names the consumer that needs it.
"""
from dataclasses import dataclass, field
from typing import Optional
from .errors import EngineError

# The basis. Panksepp's seven affective systems plus DISGUST, which is irreducible by the same
# criterion the other seven meet — it is not derivable from any combination of them — and is
# Plutchik's eighth. Settled normative in `docs/emotion-basis.md` on 2026-08-22 and added here on
# the same day; before that `state.py` carried a written-out DISGUST push it deliberately would not
# wire, and `compounds.py` blocked seventeen of forty-two named emotions (contempt, shame, remorse,
# horror) rather than truncate a recipe that named a primitive the basis did not carry.
#
# ORDER IS LOAD-BEARING: `compounds._vector` builds a dense vector by iterating this tuple, so an
# insertion in the middle would silently re-index every stored comparison. DISGUST goes last.
# THE EIGHT BUILT PATHS ARE THE STATE. Until 2026-09-08 this was the Panksepp primitive set
# ("SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY", "DISGUST") and the paths
# were rendered FROM it through a rung_blocks.PATH_SOURCE lookup. The owner ruled the old
# emotions are REPLACED by the paths, not translated into them, so the lookup is gone and a
# character's affect vector is a position on each path.
#
# The mapping that was retired, from docs/emotion-paths.md's "was" column: SEEKING and LUST
# both fold into STIRRING (what differs is the OBJECT, which is the actor's slot, never the
# block's); FEAR -> WARINESS; RAGE -> DISPLEASURE; CARE -> GOODWILL; PANIC_GRIEF -> DEFLATION;
# DISGUST -> DISTASTE. RECEPTIVITY (was JOY) and SELF-REGARD (new) never had a stored float,
# which is why 22 verified rungs were unreachable. PLAY's path is LEVITY and LEVITY is NOT
# BUILT (docs/rungs/LEVITY.md), so PLAY has no successor here and its appraisal pushes are
# dropped rather than ported.
PATHS = ("STIRRING", "WARINESS", "DISPLEASURE", "GOODWILL",
         "DEFLATION", "DISTASTE", "RECEPTIVITY", "SELF-REGARD", "LEVITY")
# LEVITY joined 2026-09-11 by the owner's ruling ("add levity back in; if it fails in production we
# repair"). PLAY's old appraisal pushes are restored under its name in state._DIM_TO_PATH.

# The `kind` of a wound delta names its CAUSE, never its direction — the sign of `delta` already
# carries direction, so a confirmation/disconfirmation vocabulary would say the same thing twice.
# Three causes: an event fired the wound's own triggers, time passed with nothing firing, or the
# log is being corrected (`correction` is the repo's existing house word — consolidation.py's
# SYSTEM_TYPES). Mirrored by a CHECK constraint on the column, so the database refuses a word this
# tuple does not contain; `levers.py` imports it rather than keeping a second copy.
WOUND_DELTA_KINDS = ("event", "erosion", "correction")

# ---------------------------------------------------------------------------
# DIRECTEDNESS — what each primitive can be ABOUT.
#
# `emotion-basis.md` (normative): "So the model is {primitive -> (magnitude, target)}. Each
# primitive in a compound carries its own target." Before this table there was no statement
# anywhere in the engine of how a primitive is directed — `compounds.py` annotated roles per
# RECIPE, and `state._REGARD_SCALED_DIMS` said which DIMENSIONS were outward-directed, but the
# basis itself said nothing. So the aboutness of eight primitives would otherwise have been decided
# by whichever call site happened to bind first.
#
# ROLE IS DERIVED, NOT AUTHORED. A reflexive state is the object role where the bound id is the
# character's own. Nothing upstream declares reflexivity; this table decides only whether a
# primitive ADMITS that bind. `beneficiary` is not a role — it is the name of CARE's object seen
# from inside a multi-party recipe, and the one-slot model cannot express a beneficiary distinct
# from an object on the same primitive anyway (multi-party states use several primitives, one
# target each — the doc's own jealousy example). `self.act` is not a role either: it is the object
# role with an event-typed target, which is where `emotion-basis.md` already puts tense-like
# structure ("grief targeting a recall entry IS past").
#
# THE LAW BEHIND `direction_changes`, so a future primitive does not re-litigate it:
# **a primitive needs its own reflexive stage directions exactly when its action tendency becomes
# incoherent aimed at the self.** Attack survives — you can go at yourself. Shutdown survives — it
# never pointed at anything. Pursuit inverts: you cannot pursue what you already are, so it becomes
# display. Expulsion inverts: you cannot expel yourself from yourself, so it becomes concealment.
#
# Each row is argued from what the Panksepp system makes a BODY DO, never from how often the
# compound vocabulary happens to use a role. Reasoned by Fable 2026-08-22 under the standing rule
# that downstream aligns to SWE; following that rule caught two places `compounds.py` has already
# drifted FROM this basis (jealousy binds FEAR reflexively where the basis says FEAR of *the loss*;
# four recipes bind PLAY reflexively where covertness is a delivery register, not aboutness).
#
# reflexive       -- may the bound target be the character themselves?
# kinds           -- what sorts of thing this primitive can point at
# direction_changes -- must the actor be told to do something DIFFERENT when the bind is reflexive?
DIRECTEDNESS = {
    # REKEYED TO THE PATHS 2026-09-09, and the rekey is the whole repair. The table sat keyed to the
    # eight Panksepp primitives from 2026-09-08, when `PATHS` replaced them, until this line. Because
    # `admits_role` fails closed on an unknown key, EVERY path silently refused a reflexive bind for
    # a day -- including DISTASTE, DEFLATION and STIRRING, whose predecessors DISGUST, PANIC_GRIEF
    # and SEEKING all admitted one. Nothing raised, no test went red, and a character simply stopped
    # being able to feel anything about himself. A lookup miss, not a decision, and the same shape as
    # the rename sweep this project already recorded: valid code, no error, a capability gone.
    #
    # EVERY PATH ADMITS SELF, and that is a ruling rather than a derivation. William, 2026-09-09:
    #
    #     "The prompts are already designed, just allow for the self target, the actor has to
    #      figure out application."
    #
    # The eighty-three rung blocks were authored to be universal -- that is what the whole
    # behavioural-review programme was measuring -- so a block read inward is the ACTOR APPLYING
    # PROSE THAT ALREADY WORKS, not a state needing a second block. The per-primitive arguments this
    # table used to carry (fear-of-self is fear of a prospect; care is definitionally other-directed;
    # anger at your own fumble targets the act) are preserved verbatim in
    # `staging/src/engine/RETIRED-DIRECTEDNESS-PRIMITIVES.py`. They are not wrong; they are answers
    # to a question this design no longer asks the TABLE, because it asks the actor.
    #
    # `direction_changes` IS FALSE EVERYWHERE, by the same ruling, and the column is kept rather than
    # dropped because it is the thing that would change if a blind sim ever shows a self-bound block
    # failing. THE FALSIFIER, named rather than assumed: run the rung blocks with `about` = the
    # character on DISTASTE and DEFLATION. The retired DISGUST row argues the action tendency BREAKS
    # reflexively -- expulsion and distance-opening are incoherent aimed at yourself, and the
    # measured defect was "you will not be in the room with it" as a shame direction. If that
    # reappears under the path blocks, this column is where the repair goes.
    #
    # `kinds` CARRIES ACROSS from each path's predecessor, since nothing in the ruling touched what
    # a path may point AT -- only whether the pointer may be the character themselves. RECEPTIVITY
    # and SELF-REGARD have no predecessor; both take the widest set their ladders need.
    #
    # reflexive         -- may the bound target be the character themselves?
    # kinds             -- what sorts of thing this path can point at
    # direction_changes -- must the actor be told to do something DIFFERENT when the bind is
    #                      reflexive? False everywhere by ruling; see the falsifier above.

    # forward pull toward what might be found. Was SEEKING (reflexive) merged with LUST (not).
    "STIRRING":    {"reflexive": True, "kinds": ("entity", "task", "prospect"),
                    "direction_changes": False},
    # withdrawal from anticipated harm. Was FEAR, which refused self: "afraid of myself" read as
    # WARINESS(the prospect of what I might do), a belief-typed object. The belief kind is retained,
    # so that reading is still available to an appraiser that prefers it.
    "WARINESS":    {"reflexive": True, "kinds": ("entity", "prospect", "belief"),
                    "direction_changes": False},
    # approach to remove an obstacle or redress a wrong. Was RAGE, which refused self and routed
    # "I hate myself" through DISGUST plus PANIC_GRIEF. The act kind still carries the narrower
    # reading -- anger at your own fumble is DISPLEASURE(the fumble).
    "DISPLEASURE": {"reflexive": True, "kinds": ("entity", "act"),
                    "direction_changes": False},
    # act on another's behalf at cost to yourself. Was CARE, refused as definitionally other-
    # directed; under the ruling the actor decides what goodwill toward oneself looks like.
    "GOODWILL":    {"reflexive": True, "kinds": ("entity",),
                    "direction_changes": False},
    # separation distress. Was PANIC_GRIEF, which already admitted self -- the self as the thing
    # severed from the group, which is shame's ingredient -- and needed no new words for it, because
    # the despair phase is autonomic and its phrases are pure posture.
    "DEFLATION":   {"reflexive": True, "kinds": ("entity", "recall", "belief"),
                    "direction_changes": False},
    # expel; *this would contaminate me*. Was DISGUST, which already admitted self (shame,
    # self-loathing). The one row where the retired table also set direction_changes True; see the
    # falsifier above for what would bring that back.
    "DISTASTE":    {"reflexive": True, "kinds": ("entity", "act", "percept"),
                    "direction_changes": False},
    # openness to what is arriving. NO PREDECESSOR -- new with the path basis. Takes the widest
    # kinds because its ladder runs from noticing a thing to being undone by it.
    "RECEPTIVITY": {"reflexive": True, "kinds": ("entity", "act", "percept", "prospect"),
                    "direction_changes": False},
    # where you stand in your own estimation. NO PREDECESSOR. Its object is arguably ALWAYS the
    # self, which this two-state column cannot say -- `reflexive: True` reads as "may also point
    # inward" where the truth may be "cannot point anywhere else". Left as True deliberately rather
    # than silently: a reflexive-only state is a shape change and wants its own decision.
    "SELF-REGARD": {"reflexive": True, "kinds": ("entity", "act"),
                    "direction_changes": False},
    # how much of your choosing you have handed to what is available. NO PREDECESSOR in the stored
    # state (PLAY was never a float). The design says it is the one path with NO OBJECT — it is a
    # mode, not a feeling about anything — so `kinds` is empty. That column is documentation, not a
    # gate: `admits_role` reads only `reflexive`, so a seat that binds a reading here to the other
    # party of a shared frame is not refused. Recorded rather than enforced (2026-09-11).
    # `reflexive` is True because the owner's ruling (tests/test_directedness.py [2]) is that EVERY
    # path may be about the one who has it; the design's no-object claim lives in `kinds`.
    "LEVITY":      {"reflexive": True, "kinds": (),
                    "direction_changes": False},
}

# The binding labels a COMPOUND recipe may use. They are authoring ergonomics — which party fills
# which primitive's single slot — and they map onto the derived roles above: `beneficiary` fills
# CARE's object, `self.act` fills an event-typed object. Live state never stores them.
RECIPE_ROLES = ("object", "self", "beneficiary", "self.act")

_ROLE_FOR_LABEL = {"object": "object", "self": "self",
                   "beneficiary": "object", "self.act": "object"}


def admits_role(primitive, role):
    """Does the basis let this primitive carry this role? Unknown primitive -> False (fail closed).

    `role` is a DERIVED role (`object` / `self`) or a recipe binding label, which is normalised
    first. This is the single check every trust boundary uses, so the table cannot be interpreted
    two ways in two places.
    """
    row = DIRECTEDNESS.get(primitive)
    if row is None:
        return False
    derived = _ROLE_FOR_LABEL.get(role, role)
    if derived == "self":
        return bool(row["reflexive"])
    return derived == "object"


def direction_changes(primitive):
    """Does this primitive need DIFFERENT stage directions when its bind is reflexive?

    The second column of the law above, and NOT the same question as `admits_role(p, "self")`.
    `reflexive` asks whether the bind is legal; this asks whether the action tendency BREAKS under
    it. PANIC_GRIEF is the case that separates them — bound to the self all the time, and its
    despair phase is undirected posture, so it needs no new words.

    Read this, never the `reflexive` column, when choosing a reflexive phrase. Before 2026-09-01
    `direction.py:_phrase_for` gated on `admits_role` while its own docstring cited this field;
    PANIC_GRIEF passed that gate and was saved only by having no entry in the phrase table. A law
    enforced by an absent row is enforced by luck.

    Unknown primitive -> False, matching `admits_role`'s fail-closed contract.
    """
    row = DIRECTEDNESS.get(primitive)
    return bool(row["direction_changes"]) if row else False
VISIBILITIES = ("public", "private-to-actor")
RELATIONSHIP_AXES = ("trust", "affinity", "respect", "debt")


class RecordError(EngineError):
    """A record failed boundary validation. The write that carried it must not happen."""


def _check_affect(affect, label):
    """A committed mood: exactly the nine paths, each in [0, 1] - the actor's and every bystander's."""
    _require(isinstance(affect, dict), "RECORD_FIELD_TYPE", "%s must be dict" % label)
    missing = [p for p in PATHS if p not in affect]
    _require(not missing, "RECORD_AFFECT_MISSING_PRIMARIES", "%s missing primaries: %s" % (label, missing))
    extra = [k for k in affect if k not in PATHS]
    _require(not extra, "RECORD_AFFECT_UNKNOWN_KEYS", "%s has unknown keys: %s" % (label, extra))
    for p, v in affect.items():
        _require(isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0,
                 "RECORD_AFFECT_VALUE_RANGE", "%s[%s] must be in [0, 1], got %r" % (label, p, v))


def _require(cond, code, msg):
    """Refuse with a REGISTERED code. `errors.EngineError` refuses to construct an unknown one, so
    the registry cannot drift from the raises.

    THE SIGNATURE GAINED `code` ON 2026-09-02, and the reason is worth keeping: as `(cond, msg)`
    this helper raised `RecordError(msg)` — a parameter as the sole argument — and the conversion
    audit's doorway rule read any parameter-first raise as ALREADY coded. So the module carrying
    the record contract's forty-four refusals reported as raising nothing at all, and the whole
    engine reported converted while the surface a malformed commit meets had no handles. The rule
    now requires a doorway to pass a code AND a message; this signature is what makes that true.
    """
    if not cond:
        raise RecordError(code, msg)


@dataclass
class Event:
    """One log entry: {what · who · where · consequence · caused_at · effective_at} (world-state-ledger.md).
    Two clocks: caused_at = when it entered the log; effective_at = when it folds (>= caused_at)."""
    type: str
    payload: dict
    actor: Optional[str] = None
    target: Optional[str] = None
    location: Optional[str] = None
    visibility: str = "public"
    caused_at: Optional[int] = None      # default: the committing turn (filled by the ledger)
    effective_at: Optional[int] = None   # default: caused_at

    def validate(self):
        _require(isinstance(self.type, str) and self.type.strip(), "RECORD_EVENT_TYPE_EMPTY", "Event.type must be a non-empty string")
        _require(isinstance(self.payload, dict), "RECORD_EVENT_PAYLOAD_TYPE", "Event.payload must be a dict")
        _require(self.visibility in VISIBILITIES, "RECORD_EVENT_VISIBILITY_UNKNOWN", "Event.visibility %r not in %s" % (self.visibility, list(VISIBILITIES)))
        if self.caused_at is not None:
            _require(isinstance(self.caused_at, int) and self.caused_at >= 0, "RECORD_EVENT_CAUSED_AT_INVALID", "Event.caused_at must be int >= 0")
        if self.effective_at is not None:
            _require(isinstance(self.effective_at, int), "RECORD_EVENT_EFFECTIVE_AT_INVALID", "Event.effective_at must be int")
            _require(self.caused_at is not None, "RECORD_EVENT_EFFECTIVE_AT_UNANCHORED", "Event.effective_at set without caused_at")
            _require(self.effective_at >= self.caused_at, "RECORD_EVENT_EFFECT_BEFORE_CAUSE", "Event.effective_at %s < caused_at %s" % (self.effective_at, self.caused_at))


REST_SOURCES = ("authored", "cliff")


@dataclass
class RestDeclared:
    """Where one edge axis RESTS from this turn on (bond-arithmetic.md s6). Append-only; a moved rest
    is a NEW row. `authored` = seeded from the sheet at run creation or at a pre-v28 run's first
    resume; `cliff` = a trust cliff lowered it on the causing turn (rides the TurnCommit,
    bonds.cliff_axes). An edge with no row rests where a stranger does (bond_rest.stranger_rest)."""
    perceiver: str
    target: str
    axis: str
    rest: float
    source: str = "authored"

    def validate(self):
        _require(isinstance(self.perceiver, str) and self.perceiver.strip(), "RECORD_PERCEIVER_EMPTY", "RestDeclared.perceiver must be non-empty")
        _require(isinstance(self.target, str) and self.target.strip(), "RECORD_TARGET_EMPTY", "RestDeclared.target must be non-empty")
        _require(self.axis in RELATIONSHIP_AXES, "RECORD_AXIS_UNKNOWN", "RestDeclared.axis must be one of %s" % (RELATIONSHIP_AXES,))
        _require(isinstance(self.rest, (int, float)) and not isinstance(self.rest, bool) and 0.0 <= float(self.rest) <= 1.0,
                 "RECORD_REST_RANGE", "RestDeclared.rest must be a float in [0, 1], got %r" % (self.rest,))
        _require(self.source in REST_SOURCES, "RECORD_REST_SOURCE_UNKNOWN", "RestDeclared.source must be one of %s, got %r" % (REST_SOURCES, self.source))


ATTACHMENT_SOURCES = ("authored", "director", "keeper")
# `composition` is NOT a row source: the composition pass writes the SHEET before a run exists, and
# the sheet seeds `authored` rows at run creation. The note it writes carries the provenance.


@dataclass
class AttachmentDeclared:
    """What one character HOLDS from this turn on (bond-arithmetic.md s3). Append-only; a moved hold is
    a NEW row, a dropped hold is a row at 0 (relation `none`). `authored` = seeded from the sheet at
    run creation / late join / a pre-v30 run's first resume; `director` = the scene cfg's declarations
    at scene start; `keeper` = the canon gate's rubric on a newly-kept entity (deferred, gate 5)."""
    char_id: str
    entity: str            # loc.<world.locations id> | grp.<people[].groups tag>
    hold: float            # 0..1
    sign: str = "+"        # "+" | "-"; reserved — v1 arithmetic folds "+" only
    source: str = "authored"

    def validate(self):
        _require(isinstance(self.char_id, str) and self.char_id.strip(), "RECORD_PERCEIVER_EMPTY", "AttachmentDeclared.char_id must be non-empty")
        _require(isinstance(self.entity, str) and self.entity.strip(), "RECORD_TARGET_EMPTY", "AttachmentDeclared.entity must be non-empty")
        _require(isinstance(self.hold, (int, float)) and not isinstance(self.hold, bool) and 0.0 <= float(self.hold) <= 1.0,
                 "RECORD_HOLD_RANGE", "AttachmentDeclared.hold must be a float in [0, 1], got %r" % (self.hold,))
        _require(self.sign in ("+", "-"), "RECORD_SIGN_UNKNOWN", "AttachmentDeclared.sign must be '+' or '-', got %r" % (self.sign,))
        _require(self.source in ATTACHMENT_SOURCES, "RECORD_ATTACHMENT_SOURCE_UNKNOWN", "AttachmentDeclared.source must be one of %s, got %r" % (ATTACHMENT_SOURCES, self.source))


@dataclass
class RelationshipDelta:
    """One appraisal-driven edge movement (consumers: biggest-moments view, social throughline)."""
    perceiver: str
    target: str
    axis: str
    delta: float
    # 'first' = what the perceiver makes of the target; 'second' = what the perceiver believes the
    # TARGET makes of THEM (bonds.reflect). Defaulted so every existing construction and every row
    # written before schema v8 means exactly what it always meant.
    order: str = "first"
    cause_event: Optional[int] = None    # events.event_id once the cause row exists
    object: str = ""                     # v27: what the act was ABOUT (the seat's object); '' = unnamed
    cause: str = ""                      # v29: for a debt row, WHAT changed hands (the transfer's `what`); '' otherwise

    def validate(self):
        _require(isinstance(self.perceiver, str) and self.perceiver.strip(), "RECORD_PERCEIVER_EMPTY", "RelationshipDelta.perceiver must be non-empty")
        _require(isinstance(self.target, str) and self.target.strip(), "RECORD_TARGET_EMPTY", "RelationshipDelta.target must be non-empty")
        _require(self.axis in RELATIONSHIP_AXES, "RECORD_AXIS_UNKNOWN", "RelationshipDelta.axis %r not in %s" % (self.axis, list(RELATIONSHIP_AXES)))
        _require(isinstance(self.delta, (int, float)) and -1.0 <= float(self.delta) <= 1.0,
                 "RECORD_DELTA_RANGE",
                 "RelationshipDelta.delta must be a number in [-1, 1], got %r" % (self.delta,))
        _require(self.order in ("first", "second"),
                 "RECORD_ORDER_UNKNOWN",
                 "RelationshipDelta.order must be 'first' or 'second', got %r" % (self.order,))


@dataclass
class WoundDelta:
    """One movement of a wound's intensity — the wound tier's write-record.

    SIGNED, and the sign carries the direction: negative heals, positive deepens. `kind` therefore
    names the CAUSE and never repeats the direction — an event fired the wound's own triggers, time
    passed with nothing firing, or the log is being corrected (the repo's existing house word).

    Rides INSIDE `TurnCommit`, not as a separate post-commit append. `append_arc_diff` is called
    after `append_turn`, so a crash between them leaves the turn permanently committed with the
    diff lost and `turns`' PRIMARY KEY refusing a re-append. Not a gap worth copying.
    """
    char_id: str
    wound_id: str
    delta: float
    kind: str
    source: str = ""

    def validate(self):
        _require(isinstance(self.char_id, str) and self.char_id.strip(), "RECORD_CHAR_ID_EMPTY", "WoundDelta.char_id must be non-empty")
        _require(isinstance(self.wound_id, str) and self.wound_id.strip(),
                 "RECORD_WOUND_ID_EMPTY",
                 "WoundDelta.wound_id must be non-empty — a wound with no id can never be folded back")
        _require(isinstance(self.delta, (int, float)) and -1.0 <= float(self.delta) <= 1.0,
                 "RECORD_DELTA_RANGE",
                 "WoundDelta.delta must be a number in [-1, 1], got %r" % (self.delta,))
        _require(self.kind in WOUND_DELTA_KINDS,
                 "RECORD_WOUND_KIND_UNKNOWN",
                 "WoundDelta.kind %r not in %s — the kind names the CAUSE; the sign of `delta` "
                 "already carries the direction" % (self.kind, list(WOUND_DELTA_KINDS)))
        _require(isinstance(self.source, str), "RECORD_SOURCE_TYPE", "WoundDelta.source must be str")


@dataclass
class TowardDelta:
    """One movement of what a specific person makes the perceiver FEEL — the MICRO tier.

    Distinct from RelationshipDelta: that carries an `axis` in trust|affinity|respect|debt and
    answers "do I trust them"; this carries a `primary` from the eight affective primitives and
    answers "what do they make me feel". Both are per-target and neither is redundant.
    """
    perceiver: str
    target: str
    primary: str
    delta: float
    source: str = ""

    def validate(self):
        _require(isinstance(self.perceiver, str) and self.perceiver.strip(), "RECORD_PERCEIVER_EMPTY", "TowardDelta.perceiver must be non-empty")
        _require(isinstance(self.target, str) and self.target.strip(), "RECORD_TARGET_EMPTY", "TowardDelta.target must be non-empty")
        _require(self.primary in PATHS,
                 "RECORD_PRIMARY_UNKNOWN",
                 "TowardDelta.primary %r not in %s — the MICRO tier is priced on the affective "
                 "primitives, not the relationship axes" % (self.primary, list(PATHS)))
        _require(isinstance(self.delta, (int, float)) and -1.0 <= float(self.delta) <= 1.0,
                 "RECORD_DELTA_RANGE",
                 "TowardDelta.delta must be a number in [-1, 1], got %r" % (self.delta,))
        _require(isinstance(self.source, str), "RECORD_SOURCE_TYPE", "TowardDelta.source must be str")


@dataclass
class Reading:
    """One path moving in one beat, for one character, about one party.

    `docs/emotion-arithmetic.md` section 1. The appraiser's unit of output, and the engine's unit of
    emotional cause. Three fields carry meaning and one carries a caveat:

      path   -- one of the BUILT paths. A designed-but-unbuilt path (LEVITY) has no bands and is
                therefore untaggable; `rungs.index_of` refuses it, which is correct.
      rung   -- a rung NAME from that path's ladder. Never a number: "no number leaves the
                appraiser" is hard rule 5's inbound twin, and a name survives a re-band.
      about  -- an entity id, or "" for unbound. Not an error when empty; section 5 step 3 rule 4
                says an empty `about` leaves an existing bind untouched.
      confidence -- a WORD. It gates escalation to the recorder and NEVER enters arithmetic.

    Validation resolves the rung name against the live ladder rather than a copy of it, so a
    renamed rung fails loudly here instead of resolving to the wrong position downstream.
    """
    path: str
    rung: str
    about: str = ""
    confidence: str = "sure"

    def validate(self):
        _require(isinstance(self.path, str) and self.path.strip(),
                 "READING_PATH_EMPTY", "Reading.path must be a non-empty string")
        _require(isinstance(self.rung, str) and self.rung.strip(),
                 "READING_RUNG_EMPTY", "Reading.rung must be a non-empty rung NAME")
        _require(isinstance(self.about, str),
                 "READING_ABOUT_TYPE",
                 "Reading.about must be a str ('' is UNBOUND, which is not an error), got %r"
                 % type(self.about).__name__)
        _require(isinstance(self.confidence, str) and self.confidence.strip(),
                 "READING_CONFIDENCE_EMPTY", "Reading.confidence must be a non-empty word")
        # THE LADDER IS THE AUTHORITY, not a list kept here. Importing at call time keeps
        # records.py free of an engine import at module scope, and means this can never disagree
        # with rung_blocks.BANDS -- the duplicate class CLAUDE.md tabulates seven instances of.
        from . import rungs as _rungs
        try:
            _rungs.index_of(self.path, self.rung)
        except Exception as exc:
            raise RecordError("READING_RUNG_NOT_ON_PATH",
                              "Reading names rung %r on %r, which does not resolve: %s"
                              % (self.rung, self.path, exc))
        return self


@dataclass
class TurnCommit:
    """run-lifecycle.md's atomic unit: {thought, action, tags} · validation · events · state — together or not at all."""
    run_id: str
    turn: int
    actor: str
    thought: str
    action: str
    tags: dict                            # the actor's same-pass consolidation self-report
    affect: dict                          # CURRENT tier after appraisal+decay: {primary: 0..1}, all 7
    condition: dict = field(default_factory=dict)
    events: list = field(default_factory=list)            # [Event]
    validation: dict = field(default_factory=dict)        # mechanical validation result (gate 4)
    recall: Optional[list] = None                         # belief refs the gate injected (record-contract)
    manifest: Optional[dict] = None                       # decision-input manifest (record-contract)
    rel_deltas: list = field(default_factory=list)        # [RelationshipDelta]
    wound_deltas: list = field(default_factory=list)      # [WoundDelta] — rides the turn, never a post-commit append
    toward_deltas: list = field(default_factory=list)     # [TowardDelta] — the MICRO tier, same discipline
    utterances: list = field(default_factory=list)        # [str] — what the actor SAID; rides the turn (keeper-of-truth.md)
    target_binds: list = field(default_factory=list)      # [(primary, target)] — aboutness; '' RELEASES a bind
    readings: list = field(default_factory=list)          # [Reading] — the emotional CAUSE of this beat
    wound_mints: list = field(default_factory=list)       # [wound dict] — scars this beat MINTED (wound.mint); rides the turn
    rest_rows: list = field(default_factory=list)         # [RestDeclared] — a cliff's rest move rides the causing turn (v28)
    lands_on: list = field(default_factory=list)          # [char_id] — who the beat bears on (floor, Phase 5)
    bystanders: dict = field(default_factory=dict)        # {char_id: {"affect", "condition"}} — every OTHER present
                                                          # character's mood after the beat's minutes (step 4)

    def validate(self):
        _require(isinstance(self.run_id, str) and self.run_id.strip(), "RECORD_RUN_ID_EMPTY", "TurnCommit.run_id must be non-empty")
        _require(isinstance(self.turn, int) and self.turn >= 0, "RECORD_TURN_INVALID", "TurnCommit.turn must be int >= 0")
        _require(isinstance(self.actor, str) and self.actor.strip(), "RECORD_ACTOR_EMPTY", "TurnCommit.actor must be non-empty")
        _require(isinstance(self.thought, str), "RECORD_FIELD_TYPE", "TurnCommit.thought must be str")
        _require(isinstance(self.action, str), "RECORD_FIELD_TYPE", "TurnCommit.action must be str")
        _require(isinstance(self.tags, dict), "RECORD_FIELD_TYPE", "TurnCommit.tags must be dict")
        _check_affect(self.affect, "TurnCommit.affect")
        _require(isinstance(self.condition, dict), "RECORD_FIELD_TYPE", "TurnCommit.condition must be dict")
        _require(isinstance(self.bystanders, dict), "RECORD_FIELD_TYPE", "TurnCommit.bystanders must be a dict")
        for _b, _row in self.bystanders.items():
            _require(isinstance(_b, str) and _b.strip() and _b != self.actor, "RECORD_BYSTANDER_IS_ACTOR",
                     "TurnCommit.bystanders names %r: a bystander is a present character OTHER than the actor" % (_b,))
            _require(isinstance(_row, dict) and isinstance(_row.get("condition", {}), dict), "RECORD_FIELD_TYPE",
                     "TurnCommit.bystanders[%s] must be {affect, condition}" % _b)
            _check_affect(_row.get("affect"), "TurnCommit.bystanders[%s].affect" % _b)
        _require(isinstance(self.events, list), "RECORD_FIELD_TYPE", "TurnCommit.events must be a list")
        for ev in self.events:
            _require(isinstance(ev, Event), "RECORD_LIST_ITEM_TYPE", "TurnCommit.events items must be Event, got %r" % type(ev).__name__)
            ev.validate()
        if self.recall is not None:
            _require(isinstance(self.recall, list), "RECORD_FIELD_TYPE", "TurnCommit.recall must be a list of belief refs")
        if self.manifest is not None:
            _require(isinstance(self.manifest, dict), "RECORD_FIELD_TYPE", "TurnCommit.manifest must be dict")
        _require(isinstance(self.rel_deltas, list), "RECORD_FIELD_TYPE", "TurnCommit.rel_deltas must be a list")
        for rd in self.rel_deltas:
            _require(isinstance(rd, RelationshipDelta), "RECORD_LIST_ITEM_TYPE", "TurnCommit.rel_deltas items must be RelationshipDelta")
            rd.validate()
        _require(isinstance(self.rest_rows, list), "RECORD_FIELD_TYPE", "TurnCommit.rest_rows must be a list")
        for rr in self.rest_rows:
            _require(isinstance(rr, RestDeclared), "RECORD_LIST_ITEM_TYPE", "TurnCommit.rest_rows items must be RestDeclared")
            rr.validate()
        _require(isinstance(self.wound_deltas, list), "RECORD_FIELD_TYPE", "TurnCommit.wound_deltas must be a list")
        for wd in self.wound_deltas:
            _require(isinstance(wd, WoundDelta), "RECORD_LIST_ITEM_TYPE", "TurnCommit.wound_deltas items must be WoundDelta")
            wd.validate()
        _require(isinstance(self.toward_deltas, list), "RECORD_FIELD_TYPE", "TurnCommit.toward_deltas must be a list")
        _require(isinstance(self.utterances, list), "RECORD_FIELD_TYPE", "TurnCommit.utterances must be a list")
        for _u in self.utterances:
            _require(isinstance(_u, str) and _u.strip(), "RECORD_LIST_ITEM_TYPE",
                     "TurnCommit.utterances items must be non-empty strings; `claims.write` refuses the rest")
        # ABOUTNESS, and the empty string is LEGAL here where it is refused above. An utterance that
        # says nothing is a bug; a bind that names nobody is a RELEASE, which `targets.retarget`
        # rules 3 and 5 produce every time a feeling stops being about someone. Refusing it would
        # make un-binding underivable and the replay would diverge from the run it reproduces.
        _require(isinstance(self.target_binds, list), "RECORD_FIELD_TYPE", "TurnCommit.target_binds must be a list")
        _require(isinstance(self.readings, list), "RECORD_FIELD_TYPE", "TurnCommit.readings must be a list")
        for _r in self.readings:
            _require(isinstance(_r, Reading), "RECORD_FIELD_TYPE",
                     "TurnCommit.readings items must be Reading, got %r" % type(_r).__name__)
            _r.validate()
        _require(isinstance(self.lands_on, list), "RECORD_FIELD_TYPE", "TurnCommit.lands_on must be a list")
        for _tb in self.target_binds:
            _require(isinstance(_tb, (list, tuple)) and len(_tb) == 2, "RECORD_LIST_ITEM_TYPE",
                     "TurnCommit.target_binds items must be (primary, target) pairs, got %r" % (_tb,))
            _require(_tb[0] in PATHS, "RECORD_LIST_ITEM_TYPE",
                     "TurnCommit.target_binds names %r, which is not one of the primaries" % (_tb[0],))
            _require(isinstance(_tb[1], str), "RECORD_LIST_ITEM_TYPE",
                     "TurnCommit.target_binds target must be a str ('' is the release), got %r" % type(_tb[1]).__name__)
        for td in self.toward_deltas:
            _require(isinstance(td, TowardDelta), "RECORD_LIST_ITEM_TYPE", "TurnCommit.toward_deltas items must be TowardDelta")
            td.validate()
        return self
