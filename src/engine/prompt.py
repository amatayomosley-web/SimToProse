"""prompt.py — the reasoning-contract layer as MACHINERY (gate 6, machine/content separation).

scene-assembly.md names prompt structure as the faithfulness lever and the reasoning-contract
layer; it ships with the engine, book-agnostic. Content arrives only through the packet (built
from the book's character/world data). Tag types and dimensions derive from the engine's own
contracts (consolidation CATALOG, state DIM_TO_PRIMARY) — machinery deriving from machinery,
never a hardcoded list. The one-pass tag instruction carries the measured anti-over-tagging
calibration (consolidation-loop.md Principle 1; calibrated against haiku this arc).
"""
import json

from .consolidation import CATALOG
from .direction import direct_affect, direct_condition, direct_edge, sureness
from .state import _DIM_TO_PRIMARY
from .gate import scope_names

# Types the ACTOR may self-tag: pure-appraisal catalog rows (no world fold) that are not
# system-emitted. System types are the engine's own records, never an actor's claim.
SYSTEM_TYPES = ("turn-skipped", "correction")
ACTOR_TAG_TYPES = tuple(sorted(
    name for name, row in CATALOG.items()
    if row.get("world_map") in (None, "none") and name not in SYSTEM_TYPES))

_DIMS = tuple(sorted(_DIM_TO_PRIMARY))


def build_turn_messages(packet, event_text, temperament, relationships=None):
    """packet + the moment -> the one-pass turn messages (system = cacheable identity prefix;
    user = volatile body as directions + structured content + the same-pass tag instruction).

    The never-invent line is scoped to WORLD facts; the actor's interior is licensed (the
    blind-judge finding: clamping invention must not clamp legitimate interiority)."""
    if not isinstance(packet, dict) or "stable" not in packet or "volatile" not in packet:
        raise ValueError("build_turn_messages: packet must carry stable and volatile halves")
    if not isinstance(event_text, str) or not event_text.strip():
        raise ValueError("build_turn_messages: event_text must be a non-empty string")
    vol = packet["volatile"]
    feeling = "%s. You are %s." % (direct_affect(vol["state"]["affect"], temperament),
                                   direct_condition(vol["state"]["condition"]))
    recall = "; ".join("%s (%s — %s)" % (r["claim"], r.get("provenance", ""), sureness(r.get("confidence", 0.5)))
                       for r in vol["recall"]) or "nothing in particular"
    edges = "; ".join("%s: %s" % (e.get("label") or e.get("target", "?"), direct_edge(e)) for e in vol["edges"]) or "no one in mind"
    sys_p = ("You ARE the person defined below. Be them, faithfully — including hesitating, "
             "over-controlling, or refusing when that is true to them. Do not perform a story; "
             "do not resolve drama; just be them.\n"
             "IDENTITY (stable):\n%s" % json.dumps(packet["stable"], sort_keys=True))
    usr = ("How you are, right now: %s\nActive goals: %s\n"
           "What you perceive THIS moment (your whole knowledge of the scene — act ONLY on what is here; "
           "do not invent people, outcomes, or WORLD facts beyond it. Your own interior is yours: memories, "
           "feelings, the texture of what you carry may surface freely):\n%s\n"
           "What it brings to mind: %s\n"
           "Those present, as you stand with them: %s\n"
           "The moment: %s\n"
           "Reply as ONE JSON object: {\"action\": \"...\", \"thought\": \"...\", \"exit\": false, \"addressee\": \"\", \"tags\": {\"type\": "
           "\"...\", \"summary\": \"...\", \"subject\": \"\", \"dimensions\": {%s}, "
           "\"durability\": \"transient|durable\", \"confidence\": 0..1}}.\n"
           "action = what you do or say; thought = your private inner line.\n"
           "exit = true ONLY if your action is to physically leave this scene now — to walk out, push back "
           "your chair and go; false otherwise.\n"
           "addressee = the id of the ONE present party you are speaking TO (from 'Those present, as you "
           "stand with them') — copy its id exactly; leave \"\" if you address the room or only yourself. "
           "This is WHO you speak to, distinct from tags.subject (who the moment is about).\n"
           "tags.type = exactly ONE word from: %s (the event's dominant objective class — if real "
           "danger is present, the type is threat, even during care work; if the event is a social "
           "slight, insult, dismissal, or status conflict, the type is affront; never combine types).\n"
           "tags.subject = the id of the ONE present party (from 'Those present, as you stand with "
           "them' above) the event most concerns — copy its id exactly; leave \"\" if it concerns no "
           "one in particular or only you. (Report WHO; never how you regard them — not yours to weigh.)\n"
           "tags = what OBJECTIVELY happened, for the event log — report the event's own severity, NOT how "
           "you feel about it (temperament amplifies downstream; do not pre-amplify). CALIBRATION: most "
           "moments are ordinary — emit 0.1-0.3, or omit the dimension entirely. Reserve >0.6 for a genuinely "
           "severe event (a child dying, a betrayal, a rescue from real danger). 'durable' is RARE: only an "
           "event that would change a person for years. confidence = how sure you are the tags fit (0..1)." % (
               feeling, json.dumps(vol["goals"]), json.dumps(vol["percepts"]),
               recall, edges, event_text,
               ", ".join('"%s": 0..1' % d for d in _DIMS),
               ", ".join(ACTOR_TAG_TYPES)))
    # final name-hygiene wall: mask, across the WHOLE prompt (identity/voice, recall, moment, edges),
    # the name of anyone this actor knows only by a descriptor — a name never acquired never reaches
    # the model. relationships carry `known_as`; the canonical id stays engine-side (the seam law).
    rels = relationships or {}
    return [{"role": "system", "content": scope_names(sys_p, rels)},
            {"role": "user", "content": scope_names(usr, rels)}]
