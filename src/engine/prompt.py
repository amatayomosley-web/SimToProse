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
from .direction import (direct_condition, direct_edge, direct_facts, direct_holds, direct_injuries,
                        direct_stirs, sureness)
from .identity_view import direct_goals, direct_identity, direct_percepts
from .state import _DIM_TO_PATH
from .gate import scope_names

# Types the ACTOR may self-tag: pure-appraisal catalog rows (no world fold) that are not
# system-emitted. System types are the engine's own records, never an actor's claim.
from .consolidation import ACTOR_TAG_TYPES, SYSTEM_TYPES        # noqa: E402,F401  (derived once, beside CATALOG)

_DIMS = tuple(sorted(_DIM_TO_PATH))


def direct_established(rows):
    """`volatile.established` -> the fence, as prose. Facts as the world states them, the kept
    sayings verbatim, and the subjects with nothing established named as OPEN — because "nothing
    is known" is the licence, and an actor who is not told it will assume the wall is everywhere."""
    closed, opened = [], []
    for r in rows or []:
        if not isinstance(r, dict) or not str(r.get("subject", "")).strip():
            continue
        subject = str(r["subject"]).strip()
        authored = str(r.get("authored") or "").strip()
        kept = [str(k).strip() for k in (r.get("kept") or []) if str(k).strip()]
        if not authored and not kept:
            opened.append(subject)
            continue
        parts = []
        if authored:
            parts.append(authored)
        if kept:
            parts.append("kept as true: " + " / ".join('"%s"' % k for k in kept))
        closed.append("%s — %s" % (subject, "; ".join(parts)))
    out = "; ".join(closed) if closed else "nothing about anyone or anything here"
    if opened:
        out += ". Nothing is yet established about %s — that ground is yours" % ", ".join(opened)
    return out


def build_turn_messages(packet, event_text, temperament, relationships=None, acts=(), rung_direction=None):
    """packet + the moment -> the one-pass turn messages (system = cacheable identity prefix;
    user = volatile body as directions + structured content + the same-pass tag instruction).

    THE LORE LICENCE (2026-09-11; owner: "I legitimately want them to make up lore in their turns,
    but only when that specific info isn't established"). The packet carries what is ESTABLISHED
    about who and what is here (`volatile.established`, from `read_api.established`) and the
    actor is told: do not contradict it; beyond it, speak as someone who knows their world. What
    they say binds nothing until the keeper keeps it (`claims.py` — every spoken line enters the
    log SUPERPOSED). The old line forbade inventing "people, outcomes, or WORLD facts"; the first
    two fences stand (no one new in the room, nothing decided for others or for what happens
    next) and the third is now the fence the facts draw. The actor's interior stays licensed (the
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
    # THE RUNG BLOCKS ARE THE EMOTION LANGUAGE. Until 2026-09-08 this slot ALSO carried
    # the band-phrase affect renderer - an exhaustive per-primary clause list - and the two were
    # in CONFLICT rather than merely redundant. direct_affect's own contract was "every primary
    # is described or the actor is told less is happening than the state says"; the composer's is
    # "SELECTION - which two or three of a character's live emotions this beat is played on"
    # (scripts/composer.py header). Exhaustive description and two-or-three selection cannot both
    # govern one slot: the list re-supplied precisely what the selection had chosen to leave out.
    # The owner ruled the engine moves to the path form, so that renderer and its phrase tables
    # are gone. What remains is the selected blocks plus the CONDITION line, which renders energy
    # and allostatic load and is not emotion.
    #
    # A character carrying only primitives with no built ladder gets the condition line alone.
    # That is composer.py's doctrine - "a designed-but-unbuilt path is ABSENT, NOT EMPTY" - and
    # not a silent omission: LUST and PLAY have no ladder, so they are unplayable rather than
    # quietly described by a retired renderer.
    #
    # WHAT WENT WITH IT, recorded so it is not rediscovered as a bug: deviation from the
    # character's own temperament mean ("more than is usual for you"), slope since the previous
    # turn, and target-sensitivity (the reflexive variant, the unbound-LUST phrase). No rung
    # block encodes any of the three - measured, 0 of 83.
    # The condition phrases were authored to FOLLOW a "you ..." affect clause, so they open
    # lowercase. Standing alone now, the first letter is lifted; nothing else is touched.
    _cond = direct_condition(_st["condition"])
    staging = ("%s%s." % (_cond[:1].upper(), _cond[1:])) if _cond else ""   # "" = the condition system is off
    if rung_direction:
        staging = "\n\n".join(x for x in (rung_direction, staging) if x)
    # A FIXED PHRASE for the empty slot, never an empty label (the holds/facts rule below): reachable only
    # when the book runs no condition system and the affect touches no built path.
    staging = staging or "nothing in particular"
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
    # WHAT EACH PRESENT PERSON STIRS rides the edge line (gate toward-from-readings): the micro
    # tier's words, after the standing — "<name>: <standing>, and you go soft near them". Empty vector,
    # nothing appended, so a sheet with no such history renders exactly as before.
    def _edge_line(e):
        text = direct_edge(e)
        stirs = direct_stirs(e.get("stirs"))
        return "%s, and %s" % (text, stirs) if stirs else text
    edges = "; ".join("%s: %s" % (e.get("label") or e.get("target", "?"), _edge_line(e)) for e in vol["edges"]) or "no one in mind"
    # WHAT IS YOURS HERE (bond gate attachments-to-actor, bond-arithmetic.md s7). `scene.assemble`
    # already scoped `volatile.holds` to this turn (present, or the beat's own subject); this
    # renders the same "<name> — <phrase>" register as the edges line above. A FIXED PHRASE for
    # the empty case, never an omitted section — the section-boundary tests bound on the label,
    # and an omitted section would make the label count depend on what this character owns.
    holds = direct_holds(vol.get("holds") or []) or "nothing here is yours"
    # WHAT HAS HAPPENED HERE (gate scene-facts-to-actor, 2026-09-22). The facts of this run that
    # THIS actor witnessed, most recent first — `scene_facts` does the POV filtering, this renders.
    # A FIXED PHRASE for the empty case, never an omitted section, for the same reason `holds` has
    # one: the section-boundary tests bound on the label, and an omitted section would make the
    # label count depend on how much has happened.
    facts = (direct_facts(vol.get("facts") or [],
                          (packet["stable"].get("persona") or {}).get("id"), vol.get("names"))
             or "nothing has happened here yet that you saw")
    # WHO IS HURT (gate injuries): appended to what has happened, only for a book that runs `injuries` and only when
    # this actor knows someone is hurt - every other prompt reads exactly as it did.
    hurt = direct_injuries(vol.get("injuries") or [], (packet["stable"].get("persona") or {}).get("id"),
                           vol.get("names"))
    if hurt:
        facts = "%s%s %s" % (facts, "" if facts.endswith(".") else ".", hurt)
    sys_p = ("You ARE the person defined below. Be them, faithfully — including hesitating, "
             "over-controlling, or refusing when that is true to them. Do not perform a story; "
             "do not resolve drama; just be them.\n"
             "IDENTITY (stable):\n%s" % json.dumps(direct_identity(packet["stable"]), sort_keys=True))
    usr = ("How to play this moment - stage directions, drawn from your state. Act on them; "
           "they are what you DO, not a mood to describe: %s\nActive goals: %s\n"
           "What you perceive THIS moment (your whole knowledge of the scene — act ONLY on what is here; "
           "put no one new in the room, and decide nothing for anyone else or for what happens next. "
           "Your own interior is yours: memories, feelings, the texture of what you carry may surface "
           "freely):\n%s\n"
           "What it brings to mind: %s\n"
           "What is established about who and what is here — the world's facts; do not contradict them. "
           "Beyond them, speak as someone who knows their world: name things, recall customs, fill in what "
           "a person of your station would know. What you say binds nothing until it is kept: %s\n"
           "What is yours here: %s\n"
           "What has happened here, as you saw it (most recent first, from beats you were in the room "
           "for. What changed hands you saw happen: act consistently with it. What was said is only "
           "what you heard said, not proof that it is true): %s\n"
           "Those present, as you stand with them: %s\n"
           "The moment: %s\n"
           "Reply as ONE JSON object: {\"action\": \"...\", \"thought\": \"...\", \"exit\": false, \"addressee\": \"\", \"tags\": {\"type\": "
           "\"...\", \"summary\": \"...\", \"subject\": \"\", \"dimensions\": {%s}, "
           "\"durability\": \"transient|durable\", \"confidence\": 0..1, \"attribution\": \"\"}%s}.\n"
           "action = what you do or say; thought = your private inner line.\n"
           "%s"
           "If the stage directions above pull you in different ways, your thought MUST name "
           "the pulls it is resolving and which one wins -- the weighing is the point, not a "
           "tidy answer. If they agree, say what you are doing and no more.\n"
           "exit = true ONLY if your action is to physically leave this scene now — to walk out, push back "
           "your chair and go; false otherwise.\n"
           "addressee = the id of the ONE present party you are speaking TO (from 'Those present, as you "
           "stand with them') — copy its id exactly; leave \"\" if you address the room or only yourself. "
           "This is WHO you speak to, distinct from tags.subject (who the moment is about). "
           "Only someone here can be addressed — never a person merely spoken of.\n"
           "tags.type = exactly ONE word from: %s (the event's dominant objective class — if real "
           "danger is present, the type is threat, even during care work; if the event is a social "
           "slight, insult, dismissal, or status conflict, the type is affront; never combine types).\n"
           "tags.subject = the id of the ONE person the moment most concerns — copy its id exactly. "
           "They may be someone here (from 'Those present, as you stand with them' above), or someone "
           "only spoken of: anyone in what you perceive marked \"present\": false has been named to you "
           "and is NOT in the room, and may still be who this is about. What you perceive writes a "
           "person as entity.<their id>; either spelling is accepted. Name no one who appears in "
           "neither place. Leave \"\" if the moment concerns no one in particular, or only you. "
           "(Report WHO; never how you regard them — not yours to weigh.)\n"
           "tags = what OBJECTIVELY happened, for the event log — report the event's own severity, NOT how "
           "you feel about it (temperament amplifies downstream; do not pre-amplify). Each severity is ONE "
           "word: %s. CALIBRATION: most moments are ordinary — emit faint or mild, or omit the dimension "
           "entirely. Reserve marked and above for an event that would genuinely change someone (a child "
           "dying, a betrayal, a rescue from real danger). 'durable' is RARE: only an "
           "event that would change a person for years. confidence = how sure you are the tags fit (0..1).\n"
           "tags.attribution (OPTIONAL — leave \"\" unless it applies) = ONE word, accident or coerced "
           "or negligence, when what you did was NOT deliberate: a hand slipped, you were made to, you "
           "simply did not think. Left empty the act reads as intended, which is usually right. Report "
           "the truth of it; whether anyone believes you is not yours to say.\n" % (
               # ORDER IS LOAD-BEARING and was wrong until 2026-08-29: `_act_slot` and `_act_rule`
               # sat here at positions 2 and 3 but appear at template positions 8 and 9, shifting
               # six sections by two. Every prompt the engine had built told the actor its goals
               # were empty, filed its percepts under "Those present", put the recall string under
               # "The moment:", rendered the edges inside the reply skeleton's `"dimensions": {}`,
               # and buried the event text after the skeleton's closing `"attribution": ""}`.
               # Guarded now by tests/test_prompt_sections.py, which reads the RENDER, not this tuple.
               staging,                                             # 1  stage directions
               json.dumps(direct_goals(vol["goals"])),              # 2  Active goals:
               json.dumps(direct_percepts(vol["percepts"])),        # 3  What you perceive
               recall,                                              # 4  What it brings to mind:
               direct_established(vol.get("established") or []),    # 5  What is established (2026-09-11)
               holds,                                                # 6  What is yours here (2026-09-19)
               facts,                                               # 7  What has happened here (2026-09-22)
               edges,                                               # 8  Those present
               event_text,                                          # 9  The moment:
               ", ".join('"%s": "<severity>"' % d for d in _DIMS),  # 10 reply "dimensions": {...}
               _act_slot,                                           # 11 reply skeleton act field
               _act_rule,                                           # 12 the act instruction
               ", ".join(ACTOR_TAG_TYPES),                           # 13 tags.type vocabulary
               severity_gloss()))                                    # 14 the severity ladder, defined
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

# How many recent beats a moment shows (gate tells reads the same window for what it hides and names).
MOMENT_BEATS = 4


def compose_event(situation, log, names=None, n=MOMENT_BEATS):
    """What the next actor perceives: the standing situation + the recent transcript (rolling context,
    so they can see what they have already said and not repeat it).

    Three things this used to get wrong, all of them reaching the actor:
    1. On an EMPTY log it appended a fixed line of the old default fixture's scene-setting (its hour
       and its table), unconditional, so the FIRST BEAT OF EVERY SCENE IN EVERY BOOK was told that
       one fixture's time of day and furniture. Measured on a real book's opening scene 2026-08-29.
    2. It truncated each action to 300 characters, so a long beat reached the next actor cut off
       mid-sentence and they answered a fragment.
    3. Its transcript header named the old fixture's furniture in every scene.
    The situation is the director's, and it is returned untouched.
    """
    names = names or {}
    if not log:
        return situation
    lines = "\n".join("%s: \"%s\"" % (names.get(b["who"], b["who"]), str(b["action"]).replace("\n", " "))
                      for b in log[-n:])
    return "%s\n\nThe exchange so far (most recent last):\n%s" % (situation, lines)
