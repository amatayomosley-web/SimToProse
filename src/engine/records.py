"""records.py — typed record contracts for everything the engine writes (record-contract.md).

Validation lives at the boundary: a record validates completely or the write refuses — fail loud,
no coercion, no partial acceptance. Downstream read-requirements ARE upstream write-requirements,
so each record here names the consumer that needs it.
"""
from dataclasses import dataclass, field
from typing import Optional

PRIMARIES = ("SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY")
VISIBILITIES = ("public", "private-to-actor")
RELATIONSHIP_AXES = ("trust", "affinity", "respect", "debt")


class RecordError(ValueError):
    """A record failed boundary validation. The write that carried it must not happen."""


def _require(cond, msg):
    if not cond:
        raise RecordError(msg)


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
        _require(isinstance(self.type, str) and self.type.strip(), "Event.type must be a non-empty string")
        _require(isinstance(self.payload, dict), "Event.payload must be a dict")
        _require(self.visibility in VISIBILITIES, "Event.visibility %r not in %s" % (self.visibility, list(VISIBILITIES)))
        if self.caused_at is not None:
            _require(isinstance(self.caused_at, int) and self.caused_at >= 0, "Event.caused_at must be int >= 0")
        if self.effective_at is not None:
            _require(isinstance(self.effective_at, int), "Event.effective_at must be int")
            _require(self.caused_at is not None, "Event.effective_at set without caused_at")
            _require(self.effective_at >= self.caused_at, "Event.effective_at %s < caused_at %s" % (self.effective_at, self.caused_at))


@dataclass
class RelationshipDelta:
    """One appraisal-driven edge movement (consumers: biggest-moments view, social throughline)."""
    perceiver: str
    target: str
    axis: str
    delta: float
    cause_event: Optional[int] = None    # events.event_id once the cause row exists

    def validate(self):
        _require(isinstance(self.perceiver, str) and self.perceiver.strip(), "RelationshipDelta.perceiver must be non-empty")
        _require(isinstance(self.target, str) and self.target.strip(), "RelationshipDelta.target must be non-empty")
        _require(self.axis in RELATIONSHIP_AXES, "RelationshipDelta.axis %r not in %s" % (self.axis, list(RELATIONSHIP_AXES)))
        _require(isinstance(self.delta, (int, float)) and -1.0 <= float(self.delta) <= 1.0,
                 "RelationshipDelta.delta must be a number in [-1, 1], got %r" % (self.delta,))


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
        _require(isinstance(self.run_id, str) and self.run_id.strip(), "TurnCommit.run_id must be non-empty")
        _require(isinstance(self.turn, int) and self.turn >= 0, "TurnCommit.turn must be int >= 0")
        _require(isinstance(self.actor, str) and self.actor.strip(), "TurnCommit.actor must be non-empty")
        _require(isinstance(self.thought, str), "TurnCommit.thought must be str")
        _require(isinstance(self.action, str), "TurnCommit.action must be str")
        _require(isinstance(self.tags, dict), "TurnCommit.tags must be dict")
        _require(isinstance(self.affect, dict), "TurnCommit.affect must be dict")
        missing = [p for p in PRIMARIES if p not in self.affect]
        _require(not missing, "TurnCommit.affect missing primaries: %s" % missing)
        extra = [k for k in self.affect if k not in PRIMARIES]
        _require(not extra, "TurnCommit.affect has unknown keys: %s" % extra)
        for p, v in self.affect.items():
            _require(isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0,
                     "TurnCommit.affect[%s] must be in [0, 1], got %r" % (p, v))
        _require(isinstance(self.condition, dict), "TurnCommit.condition must be dict")
        _require(isinstance(self.events, list), "TurnCommit.events must be a list")
        for ev in self.events:
            _require(isinstance(ev, Event), "TurnCommit.events items must be Event, got %r" % type(ev).__name__)
            ev.validate()
        if self.recall is not None:
            _require(isinstance(self.recall, list), "TurnCommit.recall must be a list of belief refs")
        if self.manifest is not None:
            _require(isinstance(self.manifest, dict), "TurnCommit.manifest must be dict")
        _require(isinstance(self.rel_deltas, list), "TurnCommit.rel_deltas must be a list")
        for rd in self.rel_deltas:
            _require(isinstance(rd, RelationshipDelta), "TurnCommit.rel_deltas items must be RelationshipDelta")
            rd.validate()
        return self
