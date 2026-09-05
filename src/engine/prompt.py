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
from .identity_view import direct_goals, direct_identity, direct_percepts
from .state import _DIM_TO_PRIMARY
from .gate import scope_names

# Types the ACTOR may self-tag: pure-appraisal catalog rows (no world fold) that are not
# system-emitted. System types are the engine's own records, never an actor's claim.
from .consolidation import ACTOR_TAG_TYPES, SYSTEM_TYPES        # noqa: E402,F401  (derived once, beside CATALOG)
from .errors import EngineError

_DIMS = tuple(sorted(_DIM_TO_PRIMARY))


def build_turn_messages(packet, event_text, temperament, relationships=None, acts=()):
    """packet + the moment -> the one-pass turn messages (system = cacheable identity prefix;
    user = volatile body as directions + structured content + the same-pass tag instruction).

    The never-invent line is scoped to WORLD facts; the actor's interior is licensed (the
    blind-judge finding: clamping invention must not clamp legitimate interiority)."""
    if not isinstance(packet, dict) or "stable" not in packet or "volatile" not in packet:
        raise EngineError("PROMPT_BUILD_TURN_MESSAGES_PACKET_CARRY_INVALID", "build_turn_messages: packet must carry stable and volatile halves")
    if not isinstance(event_text, str) or not event_text.strip():
        raise EngineError("PROMPT_BUILD_TURN_MESSAGES_EVENT_TEXT_EMPTY_NOT_A_STRING", "build_turn_messages: event_text must be a non-empty string")
    # THE ACT: the actor names what it did in the WORLD's vocabulary, so a law can be keyed to it
    # after the fact. Closed list, drawn from the authored laws; empty is always allowed and is
    # the right answer for most beats. Injected ONLY when the world declares laws.
    _acts = [a for a in (acts or []) if a]
    _act_slot = (", \"act\": \"\"" if _acts else "")
    _act_rule = (("act = the ONE token from this list that names what you just did, or empty if "
                  "none fits - most beats are none. Copy it exactly, do not invent one: "
                  + ", ".join(_acts) + "\n") if _acts else "")
    vol = packet["volatile"]
    # Both halves are now STAGE DIRECTIONS (second-person instructions to act), not reports of
    # interior state, so neither may be wrapped in "You are". The old frame produced
    # "You are you can do the thorough version where it matters."
    # TIER 3: the direction is staged from the EFFECTIVE levers, not the raw current state --
    # state-engine.md:12, "what the decision actually sees, after context". The .get falls back
    # to the current tier so a packet built before this tier existed still renders.
    _st = vol["state"]
    staging = "%s. %s." % (direct_affect(_st.get("effective") or _st["affect"], temperament,
                                        targets=_st.get("targets"),
                                        me=(packet.get("stable", {}).get("persona") or {}).get("id")),
                           direct_condition(_st["condition"]))
    recall = "; ".join("%s (%s — %s)" % (r["claim"], r.get("provenance", ""), sureness(r.get("confidence", 0.5)))
                       for r in vol["recall"]) or "nothing in particular"
    edges = "; ".join("%s: %s" % (e.get("label") or e.get("target", "?"), direct_edge(e)) for e in vol["edges"]) or "no one in mind"
    sys_p = ("You ARE the person defined below. Be them, faithfully — including hesitating, "
             "over-controlling, or refusing when that is true to them. Do not perform a story; "
             "do not resolve drama; just be them.\n"
             "IDENTITY (stable):\n%s" % json.dumps(direct_identity(packet["stable"]), sort_keys=True))
    usr = ("How to play this moment - stage directions, drawn from your state. Act on them; "
           "they are what you DO, not a mood to describe: %s\nActive goals: %s\n"
           "What you perceive THIS moment (your whole knowledge of the scene — act ONLY on what is here; "
           "do not invent people, outcomes, or WORLD facts beyond it. Your own interior is yours: memories, "
           "feelings, the texture of what you carry may surface freely):\n%s\n"
           "What it brings to mind: %s\n"
           "Those present, as you stand with them: %s\n"
           "The moment: %s\n"
           "Reply as ONE JSON object: {\"action\": \"...\", \"thought\": \"...\", \"exit\": false, \"addressee\": \"\", \"tags\": {\"type\": "
           "\"...\", \"summary\": \"...\", \"subject\": \"\", \"dimensions\": {%s}, "
           "\"durability\": \"transient|durable\", \"confidence\": 0..1, \"attribution\": \"\", "
           "\"social\": {}}%s}.\n"
           "action = what you do or say; thought = your private inner line.\n"
           "%s"
           "If the stage directions above pull you in different ways, your thought MUST name "
           "the pulls it is resolving and which one wins -- the weighing is the point, not a "
           "tidy answer. If they agree, say what you are doing and no more.\n"
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
           "event that would change a person for years. confidence = how sure you are the tags fit (0..1).\n"
           "tags.attribution (OPTIONAL — leave \"\" unless it applies) = ONE word, accident or coerced "
           "or negligence, when what you did was NOT deliberate: a hand slipped, you were made to, you "
           "simply did not think. Left empty the act reads as intended, which is usually right. Report "
           "the truth of it; whether anyone believes you is not yours to say.\n"
           "tags.social (OPTIONAL — leave {} unless it applies) = how the act would read to someone "
           "watching, on any of trust / affinity / respect / debt, each 0..1 where 0.5 is neutral, 1.0 "
           "the strongest possible showing and 0.0 the strongest possible failing. Use it when your act "
           "speaks to one of these and the dimensions above do not carry it — deferring to someone "
           "shows what you make of their judgement; calling in a favour settles what is owed. Report "
           "what the ACT shows, never what you want anyone to conclude." % (
               # ORDER IS LOAD-BEARING and was wrong until 2026-08-29: `_act_slot` and `_act_rule`
               # sat here at positions 2 and 3 but appear at template positions 8 and 9, shifting
               # six sections by two. Every prompt the engine had built told the actor its goals
               # were empty, filed its percepts under "Those present", put the recall string under
               # "The moment:", rendered the edges inside the reply skeleton's `"dimensions": {}`,
               # and buried the event text after `"social": {}}`. Guarded now by
               # tests/test_prompt_sections.py, which reads the RENDER, not this tuple.
               staging,                                             # 1  stage directions
               json.dumps(direct_goals(vol["goals"])),              # 2  Active goals:
               json.dumps(direct_percepts(vol["percepts"])),        # 3  What you perceive
               recall,                                              # 4  What it brings to mind:
               edges,                                               # 5  Those present
               event_text,                                          # 6  The moment:
               ", ".join('"%s": 0..1' % d for d in _DIMS),           # 7  reply "dimensions": {...}
               _act_slot,                                           # 8  reply skeleton act field
               _act_rule,                                           # 9  the act instruction
               ", ".join(ACTOR_TAG_TYPES)))                          # 10 tags.type vocabulary
    # final name-hygiene wall: mask, across the WHOLE prompt (identity/voice, recall, moment, edges),
    # the name of anyone this actor knows only by a descriptor — a name never acquired never reaches
    # the model. relationships carry `known_as`; the canonical id stays engine-side (the seam law).
    rels = relationships or {}
    return [{"role": "system", "content": scope_names(sys_p, rels)},
            {"role": "user", "content": scope_names(usr, rels)}]
