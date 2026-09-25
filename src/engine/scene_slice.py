"""scene_slice.py — the assembler's request: what a driver hands `scene.assemble` each beat, as a closed record.

THE CONTRACT WAS THREE KEYS AND THE DRIVERS SENT TWELVE (gate slice-contract, 2026-09-25). `assemble`'s docstring
and guide-content's "complete input contract" both named {event, recent, location} and said the machine read
nothing else, while the scene driver handed it the room, the props, the beat's subject, whom the speaker answers,
where each path's mood came from and when it was last read, the tells a listener caught, and the people this
beat's names do not mean. Nothing refused a key nobody declared, and every reader took what it wanted by `.get()`:
a misspelt key was accepted and read as its default, and nothing anywhere said so.

One record now, `SceneSlice`: every key a caller may pass, typed, and one door, `of`, that both `scene.assemble`
and `gate.perception_scope` go through. An undeclared key is refused naming it (inside the event too), a declared
key of the wrong shape is refused naming the field, and the engine reads the record's attributes, never the dict.
The drivers keep building dicts; the door makes the record. The fields below are the documentation - no other
list of them is kept (the repo has paid seven times for hand-kept copies of what the code already knows).

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

from dataclasses import dataclass, field, fields
from typing import Optional

from .records import RecordError

EVENT_KEYS = ("text", "kind", "target")   # the event: what happened, its kind, and whom it was done to (optional)


@dataclass(frozen=True)
class SceneSlice:
    """One beat's ground truth, before the perception wall scopes it to what this character apprehends."""
    event: dict                               # {text: str, kind: str = "mundane", target: str | None} - the moment
    recent: tuple = ()                        # the last lines said, oldest first - the rolling context
    location: Optional[str] = None            # the place id the director staged the scene at, if any
    present: Optional[tuple] = None           # who is bodily here; None = untracked (the chair): all named read present
    props: tuple = ()                         # the room's objects, plainly present (scene-authoring-rules Rule 5)
    target: Optional[str] = None              # whom the moment is about, carried across beats (the cfg's subject)
    engaged: str = ""                         # whom this speaker answers - the last speaker, if someone else; "" none
    raised_by: Optional[dict] = None          # {path: id} - whom each path's mood came from (ledger.raised_by);
                                              # None = no run behind the slice (tests, --fixture): the sheet's targets stand in
    last_read_turn: dict = field(default_factory=dict)  # {path: turn} - when each path was last read (ledger)
    last_turn: Optional[int] = None           # the speaker's last committed beat, or None before their first
    tells_noticed: tuple = ()                 # signs another actor let slip that this listener caught (gate tells)
    elsewhere: tuple = ()                     # the people this beat's names do not mean (presence.one_per_name)


DECLARED = tuple(f.name for f in fields(SceneSlice))


def _refuse(code, msg):
    raise RecordError(code, msg)


def _text(v, name, none_ok=False):
    if v is None and none_ok:
        return None
    if not isinstance(v, str):
        _refuse("SCENE_SLICE_FIELD_TYPE", "the scene slice's %s must be a string%s, got %r"
                % (name, " or None" if none_ok else "", type(v).__name__))
    return v


def _texts(v, name, sort=False):
    if not isinstance(v, (list, tuple, set, frozenset)) or not all(isinstance(x, str) for x in v):
        _refuse("SCENE_SLICE_FIELD_TYPE", "the scene slice's %s must be a list of strings, got %r" % (name, v))
    return tuple(sorted(v)) if isinstance(v, (set, frozenset)) or sort else tuple(v)


def _int(v, name, none_ok=False):
    if v is None and none_ok:
        return None
    if isinstance(v, bool) or not isinstance(v, int):
        _refuse("SCENE_SLICE_FIELD_TYPE", "the scene slice's %s must be an integer turn%s, got %r"
                % (name, " or None" if none_ok else "", v))
    return v


def _map(v, name, value):
    if not isinstance(v, dict) or not all(isinstance(k, str) for k in v):
        _refuse("SCENE_SLICE_FIELD_TYPE", "the scene slice's %s must be an object keyed by path, got %r" % (name, v))
    return {k: value(x, "%s[%s]" % (name, k)) for k, x in v.items()}


def of(raw):
    """-> SceneSlice. THE ONE DOOR: a record passes through unchanged; a dict is checked against the declaration -
    no undeclared key, at the top or inside the event, and every declared key of its shape - and made into one.
    Raises RecordError naming the key or the field; never coerces a wrong shape into a right one."""
    if isinstance(raw, SceneSlice):
        return raw
    if not isinstance(raw, dict):
        _refuse("SCENE_SLICE_NOT_AN_OBJECT", "the scene slice must be an object, got %r" % type(raw).__name__)
    extra = sorted(str(k) for k in raw if k not in DECLARED)
    if extra:
        _refuse("SCENE_SLICE_UNKNOWN_KEY", "the scene slice carries %s, which the assembler's request does not declare "
                "(it declares: %s)" % (", ".join(extra), ", ".join(DECLARED)))
    event = raw.get("event")
    if not isinstance(event, dict):
        _refuse("SCENE_SLICE_EVENT_MISSING", "the scene slice must carry an `event` object, got %r" % (event,))
    extra = sorted("event.%s" % k for k in event if k not in EVENT_KEYS)
    if extra:
        _refuse("SCENE_SLICE_UNKNOWN_KEY", "the scene slice carries %s, which the event does not declare (it declares: "
                "%s)" % (", ".join(extra), ", ".join(EVENT_KEYS)))
    if "text" not in event:
        _refuse("SCENE_SLICE_EVENT_TEXT_MISSING", "the scene slice's event carries no `text`")
    ev = {"text": _text(event["text"], "event.text"), "kind": _text(event.get("kind", "mundane"), "event.kind")}
    if "target" in event:
        ev["target"] = _text(event["target"], "event.target", none_ok=True)
    return SceneSlice(
        event=ev,
        recent=_texts(raw.get("recent", ()), "recent"),
        location=_text(raw.get("location"), "location", none_ok=True),
        present=None if raw.get("present") is None else _texts(raw["present"], "present"),
        props=_texts(raw.get("props", ()), "props"),
        target=_text(raw.get("target"), "target", none_ok=True),
        engaged=_text(raw.get("engaged", ""), "engaged"),
        raised_by=None if raw.get("raised_by") is None else _map(raw["raised_by"], "raised_by", _text),
        last_read_turn=_map(raw.get("last_read_turn", {}), "last_read_turn", _int),
        last_turn=_int(raw.get("last_turn"), "last_turn", none_ok=True),
        tells_noticed=_texts(raw.get("tells_noticed", ()), "tells_noticed"),
        elsewhere=_texts(raw.get("elsewhere", ()), "elsewhere", sort=True))
