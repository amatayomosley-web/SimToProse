"""replies.py — a model's reply, read into a record: the actor's, and the keys each seat's reply may carry.

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

THE SEATS (gate seat-replies, the same day). Each seat's parser reads its fields by name, so every other key - an
entry's too - was dropped unseen, and a declared key whose value the parser could not use was skipped (a `showed`
that is not a map) or stringified: where a PerceptSet or a present list checks the value that refused the reply,
and still does; where nothing checks it, it went into the record (a reading's non-text `about` bound as a target
by the read-along, a non-text `about_missing` reported as a concept gap "None", a non-text `lands_on` entry written
by the chair into the append-only lands_on table). THE PARSERS REFUSE WHAT THEY REFUSED BEFORE (bar the accidental
matches noted in readings.parse) and nothing more; what they stringified unchecked they now leave out, and the
record names it, as it names a `showed` they skip.
`event_extra` / `emotion_extra` / `thermometer_extra` name what an ACCEPTED reply carried that nothing read; the
drivers record that on the committed turn as `seat_extra`, and a seat that did not answer as `seat_refused` or
`seat_unanswered` (`seat_failure`). The prompts that state these shapes live in `scripts/appraiser.py`;
tests/test_seat_replies.py holds the two together, since the engine cannot import a script. `confidence` is asked of
the event seat and the thermometer and read by nothing (`UNREAD`): removing the question would change the prompt bytes
recorded runs replay by, so it is declared, not dropped.

THE KEEPER'S THREE (gate keeper-replies, the same day). Its noticing reply is a list of reports, each a world change
or a claim; its ruling reply a list of rulings; and it prices the attachment classifier's reply one kept sentence at a
time. A keeper refusal drops one REPORT and nothing retries it, and no keeper reply had ever been recorded, so here
board #258 holds as written: a key nothing reads is named, never the reason a report is refused (a claim that also
carries a `type` naming no world type is read as the claim it is - unless it carries a change's own fields, when it is
a world change with a wrong type; severity words are resolved only where the fold reads them) - save where a contract
states its own rule about it (the attach reply's shared parser forbids a number anywhere, a `hold`, and a malformed
`gaps`), and save a value the log cannot hold wherever it sits in what is written (a NaN, a value nested too deep to
walk); a known field of the wrong type is refused by code (scripts/keeper.py) where it would reach an append-only
table or the fold as it was, or crash the pass, and left out and named where it is optional. What a world change's
payload carries beyond the keys the fold reads for its type (`world_events.payload_keys`) is left out of the event
written and named, since readers that take every event's payload read it as a beat's own - and the keeper checks
each such strip against the fold itself, in the world the report is judged in. `change_extra` / `claim_extra` /
`ruling_extra` / `attach_extra` name what a report the keeper kept carried beyond what was written;
tests/test_keeper_replies.py holds these tables to the prompts that state them.

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

import json
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


# THE SEATS' CONTRACTS (gate seat-replies): the top-level keys each prompt asks for, then each entry's fields. An
# entry block is one object (attribution) or a list of them (told); a MAP block holds one entry per name the seat
# chooses (showed: one per act ladder), so its names are the seat's answer and only its entries' keys are checked.
EVENT_KEYS = ("type", "dimensions", "durability", "object", "showed", "transfers", "told", "attribution", "confidence")
# Each asked only when its caller asks: the scene driver asks exertion when the book runs `body`, tells and injuries
# when it runs those; the chair asks exertion alone. An unasked block in a reply is extra, whole.
EVENT_ASKED = ("exertion", "tells", "injuries")
EVENT_ENTRIES = {"transfers": ("what", "from", "to", "terms"), "told": ("what", "to", "cost"),
                 "attribution": ("word", "quote"), "exertion": ("word", "quote"), "tells": ("quote",),
                 "injuries": ("who", "quote", "severity")}
EVENT_MAPS = {"showed": ("word", "quote")}
LISTS = ("transfers", "told", "tells", "injuries", "readings")     # the entry blocks asked as a LIST; the rest, one object
EMOTION_KEYS = ("readings", "lands_on", "confidence")
EMOTION_ENTRIES = {"readings": ("path", "rung", "about", "about_missing")}
THERMOMETER_KEYS = ("levels", "confidence")
# Asked, and read by nothing: tests/test_seat_replies.py drives its invariance check from this table, so a key
# listed here that some reader starts to use fails there
UNREAD = {"event": ("confidence",), "thermometer": ("confidence",)}


def _name(k):
    """A key as a path segment: quoted when it holds a character paths use, so `told[].why` written as ONE top-level
    key cannot read as the nested one. (What a name looks like on a CONSOLE line - an empty one, one holding the ", "
    names are joined with - is `listed`'s concern, not the record's: these names are written on committed turns.)"""
    k = str(k)
    return json.dumps(k) if any(c in k for c in '.[]"') else k


def extra_keys(obj, known, entries=None, maps=None):
    """A reply object -> the keys its contract does not name, sorted: a top-level key by name, an entry's by path
    (`told[].why`, `attribution.note`, `showed.affinity.note`). Total - anything that is not an object carries no
    keys, and a malformed block is its parser's to refuse (only an accepted reply is asked)."""
    if not isinstance(obj, dict):
        return ()
    out = {_name(k) for k in obj if k not in known}
    blocks = [(b, f, False) for b, f in (entries or {}).items()] + [(b, f, True) for b, f in (maps or {}).items()]
    for blk, fields, is_map in blocks:
        if blk not in known:
            continue                                   # a block not asked is extra whole, above
        v = obj.get(blk)
        if is_map:
            rows = [("%s.%s" % (blk, _name(n)), r) for n, r in v.items()] if isinstance(v, dict) else []
        else:
            rows = [(blk, v)] if isinstance(v, dict) else [("%s[]" % blk, r) for r in v] if isinstance(v, list) else []
        out |= {"%s.%s" % (where, _name(k)) for where, r in rows if isinstance(r, dict) for k in r if k not in fields}
    return tuple(sorted(out))


def _esc(c):
    o = ord(c)
    return c if 32 <= o < 127 else "\\x%02x" % o if o < 256 else "\\u%04x" % o if o < 0x10000 else "\\U%08x" % o


def shown(keys):
    """Key names - or any model text - for a console line: printable ASCII whatever they hold. A model's text is any
    text, and a piped Windows stdout is cp1252 - one arrow in a key crashed the beat before its commit (gate
    seat-replies review); a raw newline or ESC let a model forge a report line or reset the terminal (gate
    keeper-replies review), so control characters are escaped too."""
    return ", ".join("".join(_esc(c) for c in str(k)) for k in keys)


def listed(names):
    """A list of key names for a console line: `shown`, with a name that is empty, holds the ", " they are joined with,
    or begins or ends with whitespace quoted - "a, b" and "" printed as three names (gate keeper-replies review), and
    "actor " never read as the id `actor` (fourth review). Display only: the record keeps each name as it is, in a
    list, where nothing is ambiguous."""
    return shown(json.dumps(str(n)) if not str(n) or ", " in str(n) or str(n) != str(n).strip() else n for n in names)


def text_ok(v):
    """Text the record can hold -> bool: a str that encodes as UTF-8. JSON can carry a lone surrogate ("\\ud800") that
    Python reads as a str and sqlite cannot bind - an id holding one crashed the keeper's pass at the write, and a
    fact or asset holding one bricked every later park and resume (gate keeper-replies review)."""
    if not isinstance(v, str):
        return False
    try:
        v.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def seat_failure(exc):
    """A seat's RecordError -> (the validation key, what it records). A reply its parser refused is `seat_refused`,
    "[CODE] detail"; a reply that never came - the provider's own failures, PROVIDER_* (no key, HTTP, a replay with
    no answer) - is `seat_unanswered`, the code alone: its detail names machine paths, and the log is append-only."""
    code = str(getattr(exc, "code", "") or "")
    return ("seat_unanswered", code) if code.startswith("PROVIDER_") else ("seat_refused", str(exc)[:200])


SEAT_VERB = {"seat_refused": "refused", "seat_unanswered": "was never answered"}
_BECAUSE = {"event": "\n  the actor's own tags were read because the event seat %s: %s",
            "emotion": "\n  the emotion seat %s, so the beat carries no readings: %s"}


def failure_note(failed):
    """{seat_refused|seat_unanswered: {seat: what}} -> the lines a refused beat's error carries, the event seat first.
    Only the EVENT seat's silence is why the actor's own tags were read; the emotion seat's leaves no readings - two
    different fallbacks, named as such (the second review caught the first draft blaming the emotion seat for the tags).
    Without these lines the operator is told only that the actor's tag is bad."""
    by_seat = {seat: (key, what) for key, by in failed.items() for seat, what in by.items()}
    return "".join(_BECAUSE[s] % (SEAT_VERB.get(by_seat[s][0], by_seat[s][0]), by_seat[s][1])
                   for s in ("event", "emotion") if s in by_seat)


def _not_text(v):
    return bool(v) and not isinstance(v, str)


def event_extra(obj, exertion=False, tells=False, injuries=False):
    """The event seat's reply -> what it carried beyond the questions it was asked (an unasked block included), and
    a declared key whose value the parser cannot read and leaves out: a `showed` that is not a map."""
    asked = tuple(k for k, on in zip(EVENT_ASKED, (exertion, tells, injuries)) if on)
    unread = {"showed"} if isinstance(obj, dict) and obj.get("showed") and not isinstance(obj["showed"], dict) else set()
    return tuple(sorted(set(extra_keys(obj, EVENT_KEYS + asked, EVENT_ENTRIES, EVENT_MAPS)) | unread))


def emotion_extra(obj):
    """The emotion seat's reply -> what it carried beyond its contract (docs/emotion-arithmetic.md section 1), and a
    declared value the parser now leaves out where it used to stringify it into the record: a reading's `about` that
    is not text (a falsy one was unbound before too), an `about_missing` that is not text (a null became a concept
    gap named "None"), a `lands_on` entry that is not text (a null became a row "None"). Asked only of an ACCEPTED
    reply - where a PerceptSet or a present list checks those values, the reply is refused, as it was bar the
    accidental matches readings.parse notes."""
    if not isinstance(obj, dict):
        return ()
    rows = [r for r in (obj.get("readings") if isinstance(obj.get("readings"), list) else []) if isinstance(r, dict)]
    unread = {"readings[].about" for r in rows if _not_text(r.get("about"))}
    unread |= {"readings[].about_missing" for r in rows if "about_missing" in r and not isinstance(r["about_missing"], str)}
    lands = obj.get("lands_on")
    if isinstance(lands, list) and any(not isinstance(x, str) for x in lands):
        unread.add("lands_on[]")
    return tuple(sorted(set(extra_keys(obj, EMOTION_KEYS, EMOTION_ENTRIES)) | unread))


def thermometer_extra(obj):
    """The thermometer's reply -> what it carried beyond `levels` and `confidence`."""
    return extra_keys(obj, THERMOMETER_KEYS)


# THE KEEPER'S CONTRACTS (gate keeper-replies): scripts/keeper.py build_keeper_prompt states a world change and a
# claim, its ruling system prompt a ruling, scripts/composition_pass.py build_attach_classify_prompt the attach reply.
# `location` is read and never asked (a threat's scope, keeper.apply_proposals); an attach reply's `gaps` is asked,
# checked by the shared parser, and used by nothing at the keeper's call.
CHANGE_KEYS = ("turn", "type", "payload", "actor", "target", "location")
CLAIM_KEYS = ("turn", "speaker", "said", "extracts")
CLAIM_ENTRIES = {"extracts": ("subject", "predicate", "object")}
RULING_KEYS = ("utterance_id", "verdict", "rationale")
ATTACH_KEYS = ("holds", "gaps")
ATTACH_ENTRIES = {"holds": ("entity", "relation", "because"), "gaps": ("named", "because")}


def change_extra(obj, left_out=(), ids=()):
    """A world change the keeper kept -> what it carried beyond what was written: a top-level key nothing reads; each
    payload key the fold does not read for its type (`left_out`: a key, or a (key, inner key) pair for a dimension the
    seven do not name), which the keeper leaves out of the event it writes; and each id (`ids`: actor, target,
    location) it wrote as null because the value was not text naming something and the fold did not read it for this
    report (scripts/keeper.py `_strip_check` projects both ways)."""
    paths = {"payload." + ".".join(_name(p) for p in (k if isinstance(k, tuple) else (k,))) for k in left_out}
    return tuple(sorted(set(extra_keys(obj, CHANGE_KEYS)) | paths | set(ids)))


def claim_extra(obj):
    """A claim the keeper recorded -> what it carried beyond its contract (an extract's too, `extracts[].note`), and an
    extract `object` it left out: null or not text (HEAD wrote a null as "none", anything else as its string; an extract
    is stored normalised, so any text is storable there)."""
    rows = obj.get("extracts") if isinstance(obj, dict) and isinstance(obj.get("extracts"), list) else []
    unread = {"extracts[].object" for r in rows if isinstance(r, dict) and "object" in r
              and not isinstance(r["object"], str)}
    return tuple(sorted(set(extra_keys(obj, CLAIM_KEYS, CLAIM_ENTRIES)) | unread))


def ruling_extra(obj):
    """A ruling the keeper applied or left -> what it carried beyond its contract, and a `rationale` that is not
    storable text, written as "" (HEAD wrote its string form; a falsy one was "" then too, so it is not named)."""
    r = obj.get("rationale") if isinstance(obj, dict) else None
    unread = {"rationale"} if r and not text_ok(r) else set()
    return tuple(sorted(set(extra_keys(obj, RULING_KEYS)) | unread))


def attach_extra(obj):
    """An attach reply the keeper accepted -> what it carried beyond {holds, gaps} and their entries' fields. (Not
    every extra key reaches here: that contract forbids a number anywhere and a `hold` - the price the model must never
    write - so the shared parser refuses those, by its own stated rule, before anything is named.)"""
    return extra_keys(obj, ATTACH_KEYS, ATTACH_ENTRIES)
