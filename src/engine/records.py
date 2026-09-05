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
PRIMARIES = ("SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY", "DISGUST")

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
    # appetitive expectancy — forward pull toward what might be found. Intrinsically transitive.
    # Reflexive is licensed by the basis itself (pride = SEEKING-satisfied(self)): the deed done,
    # owned, displayed. CAVEAT ON THE RECORD: the basis writes "SEEKING-*satisfied*(self)", and
    # "satisfied" does work that magnitude-plus-target cannot carry. The variants assume the
    # satisfied reading because it is the only reflexive SEEKING the basis licenses; hungry seeking
    # aimed at what one might become is SEEKING(a prospect), not reflexive. If blind vocabulary
    # authoring surfaces a state this conflates, the cell splits — a named falsifier, not a silent
    # assumption.
    "SEEKING":     {"reflexive": True,  "kinds": ("entity", "task", "prospect"),
                    "direction_changes": True},
    # withdrawal from anticipated harm. The harm-source is the object — the spider, the loss, the
    # dread of what is coming. Reflexive NOT admitted: "afraid of myself" is FEAR(the prospect of
    # what I might do), a belief-typed object. Its four phrases never name the feared thing, so
    # generalized withdrawal is target-tolerant across every kind it admits.
    "FEAR":        {"reflexive": False, "kinds": ("entity", "prospect", "belief"),
                    "direction_changes": False},
    # approach to remove an obstacle or redress a wrong. The object may be an ACT, including one
    # the character authored — anger at your own fumble is RAGE at the fumble, not a reflexive
    # bind. Reflexive-entity RAGE ("I hate myself") decomposes into DISGUST plus PANIC_GRIEF, where
    # the vocabulary already lives. Phrases survive an own-act target verbatim: "you name the
    # offence out loud and refuse to let it pass" is confession when the offence is yours.
    "RAGE":        {"reflexive": False, "kinds": ("entity", "act"),
                    "direction_changes": False},
    # approach toward union with another. No reflexive reading survives the definition. Its risk is
    # different and is handled in direction.py: an UNBOUND lust misattributed to whoever is present
    # invents a desire the numbers never aimed.
    "LUST":        {"reflexive": False, "kinds": ("entity",),
                    "direction_changes": False},
    # act on another's behalf at cost to yourself — definitionally other-directed, so reflexive is
    # not admitted ("self-care" is welfare management through SEEKING and FEAR, not the nurturance
    # circuit). Its object IS the beneficiary; the phrases were written at the welfare-party
    # ("you act for them", "you put yourself between them and it") before the question was asked.
    "CARE":        {"reflexive": False, "kinds": ("entity",),
                    "direction_changes": False},
    # separation distress. Object: the lost one, the loss-event, the anticipated loss. Reflexive
    # ADMITTED — the self as the thing severed from the group, which is shame's ingredient.
    # And yet direction_changes is False, which is the whole point of separating these two columns:
    # the despair phase is autonomic and UNDIRECTED, which is exactly why all four of its measured
    # phrases are pure posture. The most self-directed primitive in the vocabulary needs no new
    # words.
    "PANIC_GRIEF": {"reflexive": True,  "kinds": ("entity", "recall", "belief"),
                    "direction_changes": False},
    # social engagement without stake. Reflexive NOT admitted, and this is the clearest case where
    # reading the registry off the vocabulary would have imported a category error: the recipes
    # binding PLAY reflexively mean "the pleasure is kept private" (spite) or "savoured, not
    # offered" (smug). That is COVERTNESS — a delivery register, not aboutness — and this project
    # already ruled on register masquerading as state when it removed `sarcastic`.
    "PLAY":        {"reflexive": False, "kinds": ("entity", "act"),
                    "direction_changes": False},
    # expel; *this would contaminate me*. Reflexive admitted (shame, self-loathing) and the action
    # tendency BREAKS under it: expulsion and distance-opening are incoherent aimed at yourself,
    # which is the measured defect — "you will not be in the room with it" as a shame direction.
    # Self-disgust is the mirror: not expel-it-from-me but withhold-me-from-them.
    "DISGUST":     {"reflexive": True,  "kinds": ("entity", "act", "percept"),
                    "direction_changes": True},
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
VISIBILITIES = ("public", "private-to-actor")
RELATIONSHIP_AXES = ("trust", "affinity", "respect", "debt")


class RecordError(EngineError):
    """A record failed boundary validation. The write that carried it must not happen."""


def _require(cond, code, msg):
    """Refuse with a registered CODE, not just prose.

    The code parameter is not decoration. This helper is a refusal DOORWAY, and a
    doorway is what an AST raise-scan cannot see through: the sibling instance's audit
    certified its engine fully converted while 44 prose refusals sat behind a helper of
    exactly this shape. Every caller names its own code so the scan in
    tests/test_errors.py sees one refusal per CALL SITE, not one per doorway.
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
        _require(isinstance(self.type, str) and self.type.strip(), "RECORDS_EVENT_TYPE_NOT_A_STRING", "Event.type must be a non-empty string")
        _require(isinstance(self.payload, dict), "RECORDS_EVENT_PAYLOAD_NOT_A_DICT", "Event.payload must be a dict")
        _require(self.visibility in VISIBILITIES, "RECORDS_EVENT_VISIBILITY_NOT_IN_SET", "Event.visibility %r not in %s" % (self.visibility, list(VISIBILITIES)))
        if self.caused_at is not None:
            _require(isinstance(self.caused_at, int) and self.caused_at >= 0, "RECORDS_EVENT_CAUSED_AT_INVALID", "Event.caused_at must be int >= 0")
        if self.effective_at is not None:
            _require(isinstance(self.effective_at, int), "RECORDS_EVENT_EFFECTIVE_AT_NOT_AN_INT", "Event.effective_at must be int")
            _require(self.caused_at is not None, "RECORDS_EVENT_EFFECTIVE_AT_WITHOUT_CAUSED_AT", "Event.effective_at set without caused_at")
            _require(self.effective_at >= self.caused_at, "RECORDS_EVENT_EFFECTIVE_AT_BEFORE_CAUSED_AT", "Event.effective_at %s < caused_at %s" % (self.effective_at, self.caused_at))


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

    def validate(self):
        _require(isinstance(self.perceiver, str) and self.perceiver.strip(), "RECORDS_RELATIONSHIPDELTA_PERCEIVER_EMPTY", "RelationshipDelta.perceiver must be non-empty")
        _require(isinstance(self.target, str) and self.target.strip(), "RECORDS_RELATIONSHIPDELTA_TARGET_EMPTY", "RelationshipDelta.target must be non-empty")
        _require(self.axis in RELATIONSHIP_AXES, "RECORDS_RELATIONSHIPDELTA_AXIS_NOT_IN_SET", "RelationshipDelta.axis %r not in %s" % (self.axis, list(RELATIONSHIP_AXES)))
        _require(isinstance(self.delta, (int, float)) and -1.0 <= float(self.delta) <= 1.0,
                 "RECORDS_RELATIONSHIPDELTA_DELTA_NOT_NUMERIC", "RelationshipDelta.delta must be a number in [-1, 1], got %r" % (self.delta,))
        _require(self.order in ("first", "second"),
                 "RECORDS_RELATIONSHIPDELTA_ORDER_INVALID", "RelationshipDelta.order must be 'first' or 'second', got %r" % (self.order,))


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

    def validate(self):
        _require(isinstance(self.run_id, str) and self.run_id.strip(), "RECORDS_TURNCOMMIT_RUN_ID_EMPTY", "TurnCommit.run_id must be non-empty")
        _require(isinstance(self.turn, int) and self.turn >= 0, "RECORDS_TURNCOMMIT_TURN_INVALID", "TurnCommit.turn must be int >= 0")
        _require(isinstance(self.actor, str) and self.actor.strip(), "RECORDS_TURNCOMMIT_ACTOR_EMPTY", "TurnCommit.actor must be non-empty")
        _require(isinstance(self.thought, str), "RECORDS_TURNCOMMIT_THOUGHT_INVALID", "TurnCommit.thought must be str")
        _require(isinstance(self.action, str), "RECORDS_TURNCOMMIT_ACTION_INVALID", "TurnCommit.action must be str")
        _require(isinstance(self.tags, dict), "RECORDS_TURNCOMMIT_TAGS_INVALID", "TurnCommit.tags must be dict")
        _require(isinstance(self.affect, dict), "RECORDS_TURNCOMMIT_AFFECT_NOT_A_DICT", "TurnCommit.affect must be dict")
        missing = [p for p in PRIMARIES if p not in self.affect]
        _require(not missing, "RECORDS_MISSING_PRIMARIES", "TurnCommit.affect missing primaries: %s" % missing)
        extra = [k for k in self.affect if k not in PRIMARIES]
        _require(not extra, "RECORDS_UNKNOWN_KEYS", "TurnCommit.affect has unknown keys: %s" % extra)
        for p, v in self.affect.items():
            _require(isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0,
                     "RECORDS_TURNCOMMIT_AFFECT_VALUE_OUT_OF_RANGE", "TurnCommit.affect[%s] must be in [0, 1], got %r" % (p, v))
        _require(isinstance(self.condition, dict), "RECORDS_TURNCOMMIT_CONDITION_INVALID", "TurnCommit.condition must be dict")
        _require(isinstance(self.events, list), "RECORDS_TURNCOMMIT_EVENTS_NOT_A_LIST", "TurnCommit.events must be a list")
        for ev in self.events:
            _require(isinstance(ev, Event), "RECORDS_TURNCOMMIT_EVENTS_INVALID", "TurnCommit.events items must be Event, got %r" % type(ev).__name__)
            ev.validate()
        if self.recall is not None:
            _require(isinstance(self.recall, list), "RECORDS_TURNCOMMIT_RECALL_NOT_A_LIST", "TurnCommit.recall must be a list of belief refs")
        if self.manifest is not None:
            _require(isinstance(self.manifest, dict), "RECORDS_TURNCOMMIT_MANIFEST_INVALID", "TurnCommit.manifest must be dict")
        _require(isinstance(self.rel_deltas, list), "RECORDS_TURNCOMMIT_REL_DELTAS_NOT_A_LIST", "TurnCommit.rel_deltas must be a list")
        for rd in self.rel_deltas:
            _require(isinstance(rd, RelationshipDelta), "RECORDS_TURNCOMMIT_REL_DELTAS_INVALID", "TurnCommit.rel_deltas items must be RelationshipDelta")
            rd.validate()
        return self
