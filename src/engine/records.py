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
        _require(self.primary in PRIMARIES,
                 "RECORD_PRIMARY_UNKNOWN",
                 "TowardDelta.primary %r not in %s — the MICRO tier is priced on the affective "
                 "primitives, not the relationship axes" % (self.primary, list(PRIMARIES)))
        _require(isinstance(self.delta, (int, float)) and -1.0 <= float(self.delta) <= 1.0,
                 "RECORD_DELTA_RANGE",
                 "TowardDelta.delta must be a number in [-1, 1], got %r" % (self.delta,))
        _require(isinstance(self.source, str), "RECORD_SOURCE_TYPE", "TowardDelta.source must be str")


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

    def validate(self):
        _require(isinstance(self.run_id, str) and self.run_id.strip(), "RECORD_RUN_ID_EMPTY", "TurnCommit.run_id must be non-empty")
        _require(isinstance(self.turn, int) and self.turn >= 0, "RECORD_TURN_INVALID", "TurnCommit.turn must be int >= 0")
        _require(isinstance(self.actor, str) and self.actor.strip(), "RECORD_ACTOR_EMPTY", "TurnCommit.actor must be non-empty")
        _require(isinstance(self.thought, str), "RECORD_FIELD_TYPE", "TurnCommit.thought must be str")
        _require(isinstance(self.action, str), "RECORD_FIELD_TYPE", "TurnCommit.action must be str")
        _require(isinstance(self.tags, dict), "RECORD_FIELD_TYPE", "TurnCommit.tags must be dict")
        _require(isinstance(self.affect, dict), "RECORD_FIELD_TYPE", "TurnCommit.affect must be dict")
        missing = [p for p in PRIMARIES if p not in self.affect]
        _require(not missing, "RECORD_AFFECT_MISSING_PRIMARIES", "TurnCommit.affect missing primaries: %s" % missing)
        extra = [k for k in self.affect if k not in PRIMARIES]
        _require(not extra, "RECORD_AFFECT_UNKNOWN_KEYS", "TurnCommit.affect has unknown keys: %s" % extra)
        for p, v in self.affect.items():
            _require(isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0,
                     "RECORD_AFFECT_VALUE_RANGE",
                     "TurnCommit.affect[%s] must be in [0, 1], got %r" % (p, v))
        _require(isinstance(self.condition, dict), "RECORD_FIELD_TYPE", "TurnCommit.condition must be dict")
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
        _require(isinstance(self.wound_deltas, list), "RECORD_FIELD_TYPE", "TurnCommit.wound_deltas must be a list")
        for wd in self.wound_deltas:
            _require(isinstance(wd, WoundDelta), "RECORD_LIST_ITEM_TYPE", "TurnCommit.wound_deltas items must be WoundDelta")
            wd.validate()
        _require(isinstance(self.toward_deltas, list), "RECORD_FIELD_TYPE", "TurnCommit.toward_deltas must be a list")
        for td in self.toward_deltas:
            _require(isinstance(td, TowardDelta), "RECORD_LIST_ITEM_TYPE", "TurnCommit.toward_deltas items must be TowardDelta")
            td.validate()
        return self
