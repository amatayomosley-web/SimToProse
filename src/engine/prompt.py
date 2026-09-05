"""prompt.py — the reasoning-contract layer as MACHINERY (gate 6, machine/content separation).

scene-assembly.md names prompt structure as the faithfulness lever and the reasoning-contract
layer; it ships with the engine, book-agnostic. Content arrives only through the packet (built
from the book's character/world data). Tag types and dimensions derive from the engine's own
contracts (consolidation CATALOG, state DIM_TO_PRIMARY) — machinery deriving from machinery,
never a hardcoded list. The one-pass tag instruction carries the measured anti-over-tagging
calibration (consolidation-loop.md Principle 1; calibrated against haiku this arc).
"""
import json
from .records import RecordError   # rule 6's bad-input type

from .consolidation import CATALOG
from .severity import gloss as severity_gloss
from .direction import direct_affect, direct_condition, direct_edge, sureness
from .identity_view import direct_goals, direct_identity, direct_percepts
from .state import _DIM_TO_PRIMARY
from .gate import scope_names

# Types the ACTOR may self-tag: pure-appraisal catalog rows (no world fold) that are not
# system-emitted. System types are the engine's own records, never an actor's claim.
from .consolidation import ACTOR_TAG_TYPES, SYSTEM_TYPES        # noqa: E402,F401  (derived once, beside CATALOG)

_DIMS = tuple(sorted(_DIM_TO_PRIMARY))


def build_turn_messages(packet, event_text, temperament, relationships=None, acts=()):
    """packet + the moment -> the one-pass turn messages (system = cacheable identity prefix;
    user = volatile body as directions + structured content + the same-pass tag instruction).

    The never-invent line is scoped to WORLD facts; the actor's interior is licensed (the
    blind-judge finding: clamping invention must not clamp legitimate interiority)."""
    if not isinstance(packet, dict) or "stable" not in packet or "volatile" not in packet:
        raise RecordError("PROMPT_PACKET_INCOMPLETE", "build_turn_messages: packet must carry stable and volatile halves")
    if not isinstance(event_text, str) or not event_text.strip():
        raise RecordError("PROMPT_EVENT_TEXT_EMPTY", "build_turn_messages: event_text must be a non-empty string")
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
    # `previous` is the last committed turn's affect, when the driver put one on the packet. It
    # adds the MOVEMENT clause — how fast this came on — which is a different fact from the
    # deviation marker's "elevated versus your resting state". Absent, the line is unchanged.
    staging = "%s. %s." % (direct_affect(_st.get("effective") or _st["affect"], temperament,
                                        targets=_st.get("targets"),
                                        me=(packet.get("stable", {}).get("persona") or {}).get("id"),
                                        prev=_st.get("previous")),
                           direct_condition(_st["condition"]))
    first_order = []
    second_order = []
    for r in vol["recall"]:
        tgt = r.get("target_actor")
        stance = r.get("epistemic_stance")
        sure = sureness(r.get("confidence", 0.5))
        if tgt and stance:
            if stance == "ignorant_of":
                phrase = "you believe %s is unaware that: %s" % (tgt, r["claim"])
            elif stance == "deceived_about":
                phrase = "you believe %s is deceived into thinking: %s" % (tgt, r["claim"])
            else:
                phrase = "you believe %s knows: %s" % (tgt, r["claim"])
            second_order.append("%s (%s)" % (phrase, sure))
        else:
            first_order.append("%s (%s — %s)" % (r["claim"], r.get("provenance", ""), sure))
    parts = []
    if first_order: parts.append("; ".join(first_order))
    if second_order: parts.append("What others believe: " + "; ".join(second_order))
    recall = " | ".join(parts) or "nothing in particular"
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
           "you feel about it (temperament amplifies downstream; do not pre-amplify). Each severity is ONE "
           "word: %s. CALIBRATION: most moments are ordinary — emit faint or mild, or omit the dimension "
           "entirely. Reserve marked and above for an event that would genuinely change someone (a child "
           "dying, a betrayal, a rescue from real danger). 'durable' is RARE: only an "
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
               ", ".join('"%s": "<severity>"' % d for d in _DIMS),  # 7  reply "dimensions": {...}
               _act_slot,                                           # 8  reply skeleton act field
               _act_rule,                                           # 9  the act instruction
               ", ".join(ACTOR_TAG_TYPES),                           # 10 tags.type vocabulary
               severity_gloss()))                                    # 11 the severity ladder, defined
    # final name-hygiene wall: mask, across the WHOLE prompt (identity/voice, recall, moment, edges),
    # the name of anyone this actor knows only by a descriptor — a name never acquired never reaches
    # the model. relationships carry `known_as`; the canonical id stays engine-side (the seam law).
    rels = relationships or {}
    return [{"role": "system", "content": scope_names(sys_p, rels)},
            {"role": "user", "content": scope_names(usr, rels)}]


# ---- what the next actor PERCEIVES ------------------------------------------------------------
# This lived in `scripts/scene.py`, moved to `floor.py` with the turn-taking economy on 2026-09-03,
# and landed here the same day. It was the odd one out in `floor.py`: four of those functions decide
# WHO SPEAKS NEXT and return numbers, this one decides WHAT THE SPEAKER IS SHOWN and returns text.
#
# NOT scene.py, which was the first correction and would have pushed that module to 521 lines
# against hard rule 6's bound — the right home is the module whose stated job is already prompt text
# built engine-side, book-agnostic, with content arriving only through the packet. Engine-side
# prompt text is not a layering violation: rule 5 bans NUMBERS reaching the prompt, and this carries
# none.

def compose_event(situation, log, names=None, n=4):
    """What the next actor perceives: the standing situation + the recent transcript (rolling context,
    so they can see what they have already said and not repeat it).

    Three things this used to get wrong, all of them reaching the actor:
    1. On an EMPTY log it appended "The table has just been served; the evening is beginning." —
       BP13 dinner-fixture text, unconditional, so the FIRST BEAT OF EVERY SCENE IN EVERY BOOK was
       told it was evening at a table. Measured on a dawn dock scene 2026-08-29.
    2. It truncated each action to 300 characters, so a long beat reached the next actor cut off
       mid-sentence and they answered a fragment.
    3. "The exchange at the table" assumed the fixture's furniture in every scene.
    The situation is the director's, and it is returned untouched.
    """
    names = names or {}
    if not log:
        return situation
    lines = "\n".join("%s: \"%s\"" % (names.get(b["who"], b["who"]), str(b["action"]).replace("\n", " "))
                      for b in log[-n:])
    return "%s\n\nThe exchange so far (most recent last):\n%s" % (situation, lines)
