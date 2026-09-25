"""replies.py — a model's reply, read into a frozen record: the actor's first (the seats, keeper and composer follow).

WHY (gate actor-reply, 2026-09-25; G5 of the contracts plan the owner approved, agreed with Symphony on the shared
board). Every place a model's reply entered the engine read it into a plain dict built from named `.get()`s and
dropped the rest unseen; the ACTOR's reply had no record at all, and its hand-supplied twin (the `--turn-json` seam)
was checked by two hand-written copies raising a bare ValueError after the run row was written. One policy now:

  an EXTRA key         kept on the record (`extra`), written to the committed turn's validation and reported, never
                       refused - a model adds keys, nothing reads them, and refusing would cost a paid retry for
                       nothing; dropped unseen, they hid a model drifting from its contract
  a MISSING or         refused by a registered code where the reply came through the `--turn-json` seam (`supplied`),
  WRONG-TYPED key      before the chronicle is opened - a null OPTIONAL field there is absent, as a model's is; a
                       reply the engine drew from its own model keeps its degradation: no JSON object is an empty draw,
                       which the retry loop redraws

The actor's reply: action, thought, exit, addressee, act, tags - the contract `prompt.build_turn_messages` states
(`act` only where the world has laws). Read as it always was, save two things: `exit` is a JSON true or nothing
(`bool("false")` walked a character out), and a null action or thought is empty, not the word "None" (which was
committed as the action).

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

from dataclasses import dataclass, field

from .records import RecordError

ACTOR_KEYS = ("action", "thought", "exit", "addressee", "act", "tags")
SUPPLIED_REQUIRED = ("action", "thought", "tags")
SUPPLIED_CONTRACT = "{action, thought, tags, exit?, addressee?, act?}"


@dataclass(frozen=True)
class ActorReply:
    """One actor's reply, read. `tags` is the actor's own block (on a live run the event seat reads the act, and this
    survives only as the fallback); `extra` the keys the reply carried that nothing reads, sorted."""
    action: str = ""
    thought: str = ""
    exit: bool = False
    addressee: str = ""
    act: str = ""
    tags: dict = field(default_factory=lambda: {"dimensions": {}})
    extra: tuple = ()

    def as_turn(self):
        """-> the turn dict the drivers carry: the shape the actor's reply has always been read into, plus `extra`."""
        return {"action": self.action, "thought": self.thought, "exit": self.exit, "addressee": self.addressee,
                "act": self.act, "tags": self.tags, "extra": self.extra}


def _text(v):
    return v if isinstance(v, str) else ("" if v is None else str(v))


def actor_reply(obj, supplied=False):
    """A reply object -> ActorReply.

    A MODEL's (`supplied` false): a non-object is an empty draw, and each field is read as it always was - text
    carried as text, a non-object `tags` replaced by an empty block - save `exit`, which only a JSON true sets.
    A SUPPLIED turn (`supplied` true) is refused by code: REPLY_NOT_AN_OBJECT; REPLY_FIELD_MISSING (action, thought,
    tags); REPLY_FIELD_TYPE (text that is not text, an exit that is not true/false, tags that are not an object).
    Either way, a key no reader takes is kept in `extra`, never refused."""
    if not isinstance(obj, dict):
        if supplied:
            raise RecordError("REPLY_NOT_AN_OBJECT", "a supplied turn must be a JSON object %s, got %s"
                              % (SUPPLIED_CONTRACT, type(obj).__name__))
        obj = {}
    if supplied:
        missing = [k for k in SUPPLIED_REQUIRED if k not in obj]
        if missing:
            raise RecordError("REPLY_FIELD_MISSING", "a supplied turn is missing %s - the contract is %s"
                              % (", ".join(missing), SUPPLIED_CONTRACT))
        wrong = [k for k in SUPPLIED_REQUIRED[:2] if not isinstance(obj[k], str)]
        wrong += [k for k in ("addressee", "act") if obj.get(k) is not None and not isinstance(obj[k], str)]
        wrong += ["exit"] if obj.get("exit") is not None and not isinstance(obj["exit"], bool) else []
        wrong += ["tags"] if not isinstance(obj["tags"], dict) else []
        if wrong:
            raise RecordError("REPLY_FIELD_TYPE", "a supplied turn's %s: the wrong type (text for action, thought, "
                              "addressee and act; true or false for exit; an object for tags)" % ", ".join(wrong))
    tags = obj.get("tags") if isinstance(obj.get("tags"), dict) else {"dimensions": {}}
    # `act` as it always was, falsy -> "": a model's "act": false is no act, never the word "False", which the law
    # check would weigh against every law that names no act of its own
    return ActorReply(action=_text(obj.get("action")), thought=_text(obj.get("thought")), exit=obj.get("exit") is True,
                      addressee=_text(obj.get("addressee")), act=_text(obj.get("act") or ""), tags=tags,
                      extra=tuple(sorted(str(k) for k in obj if k not in ACTOR_KEYS)))
