#!/usr/bin/env python3
"""appraiser.py — the two seats that read a beat and say what it was.

WHY TWO AND NOT ONE. A single seat reading the stream and emitting everything downstream needs was
the obvious design and it is wrong, on a ground that is not cost: **the two outputs have
incompatible blindness contracts.**

  * THE EMOTION SEAT must read the character's private `thought`. That is the whole point — a stoic
    whose face stays flat while the state climbs is only visible from inside, and an appraiser that
    saw only the action would report calm and the ladder would never move.
  * THE EVENT SEAT must NOT. Its dimensions are *"perceiver-neutral facts about the event"*
    (`docs/standard-vectors.md` section 1) which `bonds.act_from_tags` turns into what a WITNESS
    made of the act — and `bonds.witnessed` exists precisely because presence is not perception. A
    reader that has been shown the interior cannot rate the act as a bystander would. You cannot
    un-show a model its context.

So the split is not an optimisation. It is the only arrangement where both consumers get an input
their own contract permits. THIS IS A CLAIM AND IT IS TESTABLE, which is why `appraiser_bakeoff.py`
exists: it runs BOTH seats on the same beats and measures what each can actually produce. If the
thought-blind seat turns out to name rungs as well as the thought-reading one, the argument above is
wrong and this module collapses to one seat. The owner's framing, 2026-09-09: *"Build the dual
appraisers, see what jobs each can do."*

WHAT REPLACES WHAT. Today the ACTOR rates its own emotional impact — it performs the beat and then
scores the severity of what it just did (`prompt.py` reply contract, the `dimensions` block).
`severity.py`'s header records the measured consequence: the one word the actor chose decided its
own ceiling. Both seats here are second readers, and neither is the actor.

SHADOW MODE. Nothing in this module is wired into a driver yet. It builds prompts, parses replies,
and can be run by hand. Readings it produces are stored and spent by nothing — `state.appraise`
still reads `tags.dimensions`, and all twelve consumers of that vocabulary keep their feed. Wiring
comes after the bakeoff says which seat can do which job, not before.

    python scripts/appraiser.py --prompt-only --seat emotion --action "..." --thought "..."
    python scripts/appraiser.py --prompt-only --seat event   --action "..."

Hard rules: no LLM call and no randomness inside `src/engine/` (this is `scripts/`, which is the
dispatch layer); no number reaches either prompt; both parsers refuse rather than repair.
"""
import argparse
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import readings as _readings
from src.engine import concepts as _concepts                      # noqa: E402
from src.engine import rungs                                      # noqa: E402
from src.engine.records import RecordError                        # noqa: E402
from src.engine.severity import WORDS as SEVERITY_WORDS      # noqa: E402
from src.engine import severity as _severity                    # noqa: E402  (the act ladders: bond-arithmetic.md s2)
from src.engine import bonds as _bonds                          # noqa: E402  (observations_from_showed: the seam)
from src.engine import body as _body                            # noqa: E402  (the exertion ladder, gate body-exertion)
from src.engine import tells as _tells                          # noqa: E402  (the tells question, gate tells)
from src.engine import injuries as _injuries                    # noqa: E402  (the injuries question, gate injuries)
from src.engine.consolidation import ACTOR_TAG_TYPES           # noqa: E402  (the closed `type` vocabulary, derived beside CATALOG)
from src.engine.state import _DIM_TO_PATH                         # noqa: E402

# The event seat's vocabulary, DERIVED from the engine's own table rather than restated. CLAUDE.md
# tabulates seven instances of a hand-written list that mirrored something the code already knew;
# every one had already gone wrong. A dimension added to `_DIM_TO_PATH` appears here for free.
DIMENSIONS = tuple(sorted(_DIM_TO_PATH))


def ladders():
    """The eight authored ladders, low rung to high, as the emotion seat is shown them.

    RUNG NAMES AND BLOCK TEXT BOTH, and the pairing is the point: the seat is asked to name a rung,
    so it needs the name, and it can only choose honestly if it can read what the name means. This is
    the ONE surface where a rung name is legitimately shown alongside its block -- `composer.py`
    withholds the name from the ACTOR because the label measured inert there and risks out-voting the
    paragraph. The appraiser is not performing; it is classifying, and a classifier needs its labels.
    """
    out = []
    for path in rungs.paths():
        rows = []
        for i, name in enumerate(rungs.names_on(path), 1):
            rows.append("  %s — %s" % (name, rungs.block_for(path, i).strip()))
        out.append("%s\n%s" % (path, "\n".join(rows)))
    return "\n\n".join(out)


_EMOTION_SYSTEM = """You read one beat of a story and report WHAT AROSE IN THE PERSON WHO PRODUCED IT.

You are not playing anyone. You are not judging anyone. You report what happened inside them, in
their own beat, using only the ladders below.

THE LADDERS. Eight paths. Each is one axis, running from its quietest rung to its most extreme. The
name of a rung is a handle; the paragraph after it is what that rung IS. Read the paragraph.

%s

WHAT YOU RETURN — JSON, nothing else:

{"readings": [{"path": "<one of the nine, written in capitals exactly as it is headed above>", "rung": "<a rung name from THAT path, exactly as written>", "about": "<who or what it is about, or empty>", "about_missing": "<ONLY when the feeling is about a category the list below lacks: name it in two or three words; otherwise omit this key>"}],
 "lands_on": ["<who in the room this beat reached>"],
 "confidence": "sure" | "likely" | "unsure"}

THE RULES, and each one exists because of a way this goes wrong:

1. REPORT WHAT AROSE OR INTENSIFIED IN THIS BEAT. Not what the person is carrying. A man who walked
   in furious and merely stayed furious while saying something mild has no DISPLEASURE reading — the
   fury is already in the engine's books. You are a sensor for events, not a thermometer.

2. A BEAT IN WHICH NOTHING AROSE RETURNS AN EMPTY LIST. This is the most important rule here and the
   most tempting to break. Most beats are quiet. Reporting a faint something on every beat because
   the form has a slot for it is the single failure that breaks the whole system downstream. Silence
   is a legitimate and common answer.

3. READ THE THOUGHT, NOT ONLY THE ACTION. A person who says nothing and thinks something scalding
   felt it. That is why you are given the thought at all.

4. SEVERAL THINGS CAN ARISE AT ONCE, and two on the same path in one beat are two readings, not one
   averaged. Do not merge them.

5. `about` IS WHO OR WHAT THE FEELING POINTS AT. It is ONE of three things and nothing else:
   a person present, named exactly as the beat names them (it may be the person themselves); or a
   CONCEPT from the list below, returned as the exact `concept:...` string shown (a fear of the
   child's fever is about `concept:sickness`; grief for a dead child is about
   `concept:loss_of_a_child`); or empty. Leave it empty rather than guess — an unbound feeling is a
   real state, a wrongly-bound one is a lie about a relationship, and a concept not on the list
   will be refused. If the feeling is plainly about a category the list does not have, leave
   `about` EMPTY and name the category in `about_missing` — that is measured, never applied.

THE CONCEPTS — the only categories a feeling may be about that are not a person:

%s

6. NEVER INVENT A RUNG NAME. Use the ladders verbatim. If nothing on a ladder fits what you saw, the
   honest answer is to leave that path out.

7. NO NUMBERS ANYWHERE IN YOUR REPLY."""


_EVENT_SYSTEM = """You read what OBJECTIVELY HAPPENED in one beat and rate it.

You are given the act and nothing about anyone's interior. That is deliberate and it is the whole
value of this seat: you rate the EVENT, and how hard it lands on any particular person is arithmetic
that happens after you, using things you cannot see — their temperament, their history, what they
care about. If you could see those, you would apply them, and then they would be applied twice.

You rate the event ONCE, not once per person watching. Severity is a property of what happened.

THE DIMENSIONS. Use only these, and only the ones that genuinely fired:

%s

THE SEVERITY WORDS, from faintest to most extreme:

%s

WHAT YOU RETURN — JSON, nothing else:

{"type": "<exactly ONE word from: %s>",
 "dimensions": {"<dimension>": "<severity word>"},
 "durability": "transient" | "durable",
 "object": "<who or what the act was ABOUT — from THE PEOPLE and THE ATTACHMENTS below, or self, or empty>",
 "showed": {"affinity": {"word": "<an act word from the affinity ladder>",
                         "quote": "<the words of the action that show it, copied exactly>"}},
 "transfers": [{"what": "<the thing, copied from the action>", "from": "<who had it>", "to": "<who has it now>",
                "terms": "none" | "price" | "loan" | "repayment"}],
 "told": [{"what": "<the words, copied from the action>", "to": "<who was told>",
           "cost": "fault" | "exposure" | "none"}],
 "attribution": {"word": "<intent|negligence|coerced|accident>",
                 "quote": "<the words of the action that show it>"},
 "confidence": "sure" | "likely" | "unsure"}

`transfers` is usually an EMPTY list. A transfer is a THING — coin, goods, a tool, a paper, labour
done — that ended THIS beat in the other's keeping: a hand, a pocket, a bag, taken up on their side.
A thing only offered, and not yet taken up, is not a transfer; words, advice, an order, a promise,
a permission are never one. `from` and `to` are names from THE PEOPLE below, or `self`; a thing
handed to someone not on the list is not a transfer you can record. `terms` is what was SAID it was,
in this beat or the one before: `price` — pay for work, a purchase, an exchange in kind, square by its own
words; `loan` — to be returned or worked off; `repayment` — given against something this person
already owed the other; `none` — nothing was said. Quote the thing from the action, as you quote the
words for `showed`. The engine decides what the account does; you report what changed hands.

`told` is usually an EMPTY list. Record only what carried a COST to the teller in the words
themselves: `fault` — they owned an error or a wrong of their own; `exposure` — they named a loss, a
weakness or a liability of their own that the other could use against them. Plain speech, an answer,
an order, a warning, a promise cost nothing: leave the list empty (`cost: none` is the same as
leaving it out). `to` is a name from THE PEOPLE below. Quote the words from the action. The trust
ladder below has no word for this — the engine derives it from `told`; you report what was said.

`attribution` is OPTIONAL, and OMITTING IT IS THE USUAL ANSWER: leave it out whenever the act reads
as simply intended, which is most acts. Write it only when the action itself shows the act was not a
plain, willing choice — ONE word below, with a quote copied from the action exactly, checked the same
way `showed` is. Leaving the key out prices as fully intended; it is not a softer reading than naming
a word, it is the reading a witness makes when nothing says otherwise. Malice is not one of the four:
it prices exactly as intent does, and you were shown no interior to tell them apart, so write intent
and let it stand.

attribution — why the act happened, not what it was:
%s

THE ACT LADDERS — what THIS ACT showed, per axis. Each is eight words, cold to warm, with NO middle
word: an axis the act said nothing about is left out of `showed`, and leaving it out is the usual
answer. The skeleton above names one axis on purpose; most acts speak to one or none.

trust — did the act show them keeping or breaking faith?
%s

affinity — did the act show warmth or its withholding?
%s

respect — did the act show competence or its lack?
%s

debt — not a ladder, and not yours to rate: the account moves on `transfers` (above), never on a word.
Do not write a `debt` key anywhere; it is refused.

THE RULES:

1. RATE WHAT AN ONLOOKER COULD SEE. Not what anyone meant, unless they said it. Not what it will
   cost later. What happened.

2. MOST BEATS ARE MUNDANE AND MOST DIMENSIONS DO NOT FIRE. An empty `dimensions` is a legitimate
   answer for a beat where nothing of consequence occurred.

3. `durable` IS RARE. It means the event would change how someone thinks of themselves or of another
   person for a long time — not merely that it was unpleasant.

4. `showed` IS ABOUT THE ACT, NOT THE PERSON. A loyal man being slack today is `slack`. Name an axis
   only when the act itself showed something on it; a reserved act shows nothing and is left out.
   The floor word on each ladder means BETRAYAL-GRADE — `treacherous` is breaking faith with someone
   who relied on them, never mere unreliability; `cruel` is hurting for its own sake; `disgraceful`
   is conduct, not a failure of skill.

4a. EVERY WORD IN `showed` QUOTES ITS EVIDENCE. `quote` is a span copied from the action — the words
   an onlooker would point to and say "there". Copy them; do not paraphrase. A word with no quote, or
   a quote the action does not contain, is refused and the beat is rated by someone else. If you
   cannot point to the words, the act did not show it: leave the axis out.

4b. `object` IS WHO OR WHAT THE ACT WAS ABOUT, and it comes from the lists you are shown and nowhere
   else: a name from THE PEOPLE (present or spoken of), a name from THE ATTACHMENTS, or `self` when
   the actor acted on themselves. Leave it empty when the act was about nothing in particular. A
   `showed` with no `object` is refused: an act cannot show something about no one. Never invent an
   object; a place or group not on the list is not yet part of the world. A place that is merely
   WHERE the act happened is not its object: name a place or a group only when the act was done TO
   it or FOR it — repaired it, wrecked it, left it, took it, gave to it — and name the person when
   the act was done to a person in that place.

5. NO NUMBERS ANYWHERE IN YOUR REPLY. Use the words.

6. `type` IS THE EVENT'S DOMINANT OBJECTIVE CLASS, and it is ONE word from the list in the skeleton
   above, copied exactly — never a phrase, never a description. If real danger is present the type
   is threat, even during care work; a slight, insult, dismissal or status conflict is affront; help
   given is aid; tending or comfort is care; something taken or gone is loss; nothing of consequence
   is mundane. A type outside the list is refused and the beat is rated by someone else."""


def build_emotion_messages(action, thought, moment="", present=None, me=""):
    """The EMOTION seat's prompt. Sees {action, thought}, the moment, who is present, the ladders.

    WHAT IT IS DELIBERATELY NOT GIVEN, and each omission is a defect it would otherwise cause:

      * THE CHARACTER'S STORED STATE — current floats, current rungs, baseline. `emotion-arithmetic`
        section 7: "blind to stored rungs and to the baseline". A sensor that can see where the
        character already is reports what is CARRIED rather than what AROSE, and the engine then adds
        the carried state to itself every beat.
      * THE DIRECTION TEXT THE ACTOR WAS HANDED. The actor was given a rung block to play from; show
        the same block to the appraiser and it tags the block back, which is a loop, not a reading.
      * THE ACTOR'S OWN `tags`. Anchoring on the severity word the actor picked reproduces exactly
        the self-tagging this seat replaces.
      * THE SHEET. Temperament, wounds, values, gains all apply downstream. Seeing them here applies
        them twice.
    """
    who = ", ".join(present or []) or "no one else"
    lines = []
    if moment:
        lines.append("THE MOMENT:\n%s" % moment.strip())
    lines.append("PRESENT: %s" % who)
    if me:
        lines.append("THE PERSON WHOSE BEAT THIS IS: %s" % me)
    lines.append("WHAT THEY DID:\n%s" % (action or "").strip())
    lines.append("WHAT THEY THOUGHT:\n%s" % (thought or "").strip())
    return [{"role": "system", "content": _EMOTION_SYSTEM % (ladders(), _concepts.menu())},
            {"role": "user", "content": "\n\n".join(lines)}]


# THE EXERTION QUESTION (gate body-exertion), appended to the event seat's system prompt only for a book that
# runs `body`. The ladder is DERIVED from the table the engine prices (`body.rubric`).
_EXERTION_BLOCK = """

EXERTION. This book also asks how much PHYSICAL effort the act took for the one named under WHO ACTED.
Add to the JSON:

 "exertion": {"word": "<one word from the ladder below>", "quote": "<the words of the action that show the effort>"}

Rate the act, not the person: a load is as heavy whoever carries it - the engine weighs it against each
body afterwards. Rate the KIND of effort, not how long it lasted - the engine's own clock supplies the
duration. Speech, looking, listening, thinking, feeling and deciding are `none`, which is the usual answer;
emotional strain is not exertion, and danger is not effort. Only what that body does in this beat, now,
counts - not what it remembers, recounts, used to do, plans, or watches others do. When the beat holds
several acts, rate the effort that fills most of it. `none` needs no quote; every other word quotes the
action exactly.

exertion - from none to the most:
%s
"""


def build_event_messages(action, moment="", present=None, actor="", target="", referenced=None, attachments=None,
                         exertion=False, tells=False, injuries=False):
    """The EVENT seat's prompt. Sees the observable act ONLY — never the thought.

    THE OMISSION IS THE CONTRACT. `bonds.act_from_tags` turns these dimensions into what a WITNESS
    made of the act, and `bonds.witnessed` is in the engine because presence is not perception. A
    rating made with the interior in view is not a bystander's rating, whatever it claims to be.
    """
    who = ", ".join(present or []) or "no one else"
    lines = []
    if moment:
        lines.append("THE MOMENT:\n%s" % moment.strip())
    lines.append("PRESENT: %s" % who)
    if actor:
        lines.append("WHO ACTED: %s" % actor)
    # THE OBJECT IS THE SEAT'S TO NAME (bond-arithmetic.md s5). Until 2026-09-17 this line told the
    # seat WHO IT WAS AIMED AT (the addressee) and the driver guessed the bond tier's object as "the
    # one other party present" — stake 1 both ways in a two-hander, None in a three-hander. `target`
    # stays in the signature so the drivers' calls are unchanged; the prompt no longer carries it.
    people = list(present or [])
    if referenced:
        people += [r for r in referenced if r not in people]
    lines.append("THE PEOPLE the act may be about: %s" % (", ".join(people) or "no one"))
    lines.append("THE ATTACHMENTS the act may be about (places, groups, things people hold): %s"
                 % (", ".join(attachments or []) or "none registered"))
    lines.append("WHAT HAPPENED:\n%s" % (action or "").strip())
    # EXERTION IS ASKED ONLY WHEN THE BOOK RUNS `body` (gate body-exertion): appended, so the prompt of every
    # other book - and the sha256 key of every recorded seat reply - is byte-identical.
    _ask = (((_EXERTION_BLOCK % _body.rubric()) if exertion else "") + (_tells.RUBRIC if tells else "")
            + ((_injuries.RUBRIC % _injuries.rubric()) if injuries else ""))
    return [{"role": "system",
             "content": _EVENT_SYSTEM % ("\n".join("  %s" % d for d in DIMENSIONS),
                                         ", ".join(SEVERITY_WORDS),
                                         ", ".join(ACTOR_TAG_TYPES),
                                         _severity.attribution_rubric(),
                                         _severity.act_rubric("trust"),
                                         _severity.act_rubric("affinity"),
                                         _severity.act_rubric("respect")) + _ask},
            {"role": "user", "content": "\n\n".join(lines)}]


def _json_object(raw):
    """The first JSON object in a reply, or None. Shared by both parsers.

    NOT `direct._parse_reply` -- that one is shaped for the ACTOR's reply and coerces every result
    into {action, thought, exit, addressee, act, tags}, which silently dropped the composer's
    `selected` for a day (measured 2026-09-08). A second reply shape needs its own reader.
    """
    if not raw:
        return None
    depth, start = 0, -1
    for i, ch in enumerate(raw):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(raw[start:i + 1])
                except ValueError:
                    start = -1
    return None


_THERMOMETER_SYSTEM = """You read ONE passage of a novel and say where its viewpoint character STANDS on each of
eight emotional ladders at the END of the passage — the standing level, not what arose in it.

This is the opposite of the sensor's job. The sensor reports what rose in a beat; you report the
level the character is carrying when the beat ends, whether or not anything rose. A man who
walked in furious and is still furious stands at his fury; a man whose fright passed an hour ago
stands wherever it has fallen to.

THE LADDERS. Each runs from its quietest rung to its most extreme. The name of a rung is a
handle; the paragraph after it is what that rung IS. Read the paragraph.

%s

WHAT YOU RETURN — JSON, nothing else:

{"levels": {"<path, in capitals exactly as headed above>": "<a rung name from THAT path, exactly as written>", ...}, "confidence": "sure" | "likely" | "unsure"}

THE RULES:
1. EVERY PATH GETS A RUNG, including the quiet ones — the lowest rung is a legitimate and common
   answer; most paths on most passages sit there.
2. THE LEVEL AT THE END of the passage, as the text shows it or plainly implies it. Do not
   forecast. Do not average the passage.
3. NEVER INVENT A RUNG NAME. Use the ladders verbatim.
4. NO NUMBERS ANYWHERE IN YOUR REPLY."""


def build_thermometer_messages(passage, me=""):
    """The THERMOMETER seat's prompt — a MEASUREMENT instrument for the read-along, never wired into
    a driver. `docs/emotion-arithmetic.md` section 7 makes the sensor blind to the standing level
    on purpose; fitting a half-life needs that level over story time, so this seat reads it and
    the harness logs it beside the readings, applying nothing."""
    lines = []
    if me:
        lines.append("THE VIEWPOINT CHARACTER: %s" % me)
    lines.append("THE PASSAGE:\n%s" % (passage or "").strip())
    return [{"role": "system", "content": _THERMOMETER_SYSTEM % ladders()},
            {"role": "user", "content": "\n\n".join(lines)}]


def parse_thermometer_reply(raw):
    """A raw thermometer reply -> {path: rung NAME} for every path it named, each validated against
    the live ladder (an invented rung raises by name). Missing paths are missing, not defaulted."""
    obj = _json_object(raw)
    if not isinstance(obj, dict) or not isinstance(obj.get("levels"), dict):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the thermometer's reply carried no `levels` object")
    out = {}
    for path, rung in obj["levels"].items():
        rung = str(rung or "").strip()
        if any(ch.isdigit() for ch in rung):
            raise RecordError("READING_RUNG_IS_NUMERIC", "thermometer: %r is a number, not a rung name" % rung)
        path = _readings.canonical_path(path)           # the ladder's own name; case is not a ladder
        try:
            rungs.index_of(path, rung)                  # raises on an unbuilt path or an invented rung
        except rungs.RungError as exc:
            raise RecordError("READING_RUNG_NOT_ON_PATH", "thermometer: %s" % exc)
        out[path] = rung
    return out


def read_level(passage, model, led=None, run_id=None, turn=None, scene=None, me=""):
    """The THERMOMETER seat, live -> {path: rung name}. Raises RecordError on a refused reply."""
    import provider as _provider
    raw = _provider.call(build_thermometer_messages(passage, me=me), model, "thermometer",
                         led=led, run_id=run_id, turn=turn, scene=scene)
    return parse_thermometer_reply(raw)


def missing_concepts(raw):
    """The measurement-only `about_missing` names in a raw emotion-seat reply -> [str]. Never
    applied to state; the read-along collects them as the registry's next edit."""
    try:
        obj = _json_object(raw)
    except Exception:            # noqa: BLE001 — measurement only; a refused reply has no names to collect
        return []
    out = []
    for row in (obj.get("readings") or []) if isinstance(obj, dict) else []:
        if isinstance(row, dict) and str(row.get("about_missing", "")).strip():
            out.append(str(row["about_missing"]).strip())
    return out


def read_emotion(action, thought, model, led=None, run_id=None, turn=None, scene=None,
                 moment="", present=None, me="", percepts=None):
    """The EMOTION seat, live: prompt -> the frontier model (scripts/provider.py) -> parsed.
    -> (readings, lands_on, confidence, missing) ; raises RecordError on a refused reply."""
    import provider as _provider
    raw = _provider.call(build_emotion_messages(action, thought, moment=moment, present=present, me=me),
                         model, "appraise-emotion", led=led, run_id=run_id, turn=turn, scene=scene)
    readings, lands, conf = parse_emotion_reply(raw, percepts=percepts, present=present, me=me)
    return readings, lands, conf, missing_concepts(raw)


def read_event(action, model, led=None, run_id=None, turn=None, scene=None,
               moment="", present=None, actor="", target="", referenced=None, attachments=None, exertion=False,
               tells=False, injuries=False):
    """The EVENT seat, live: prompt -> the frontier model -> the tags dict the twelve dimension
    consumers already read, plus the bond tier's `object` + `showed`. Raises RecordError on a
    refused reply. The object lists are what the prompt showed; the parser refuses anything else."""
    import provider as _provider
    raw = _provider.call(build_event_messages(action, moment=moment, present=present, actor=actor, target=target,
                                              referenced=referenced, attachments=attachments, exertion=exertion,
                                              tells=tells, injuries=injuries),
                         model, "appraise-event", led=led, run_id=run_id, turn=turn, scene=scene)
    objects = list(present or []) + [r for r in (referenced or []) if r not in (present or [])] + list(attachments or [])
    return parse_event_reply(raw, objects=objects, action=action, exertion=exertion, tells=tells,
                             injuries=injuries, present=present, actor=actor)


def parse_emotion_reply(raw, percepts=None, present=None, me=""):
    """A raw emotion-seat reply -> (readings, lands_on, confidence). Raises RecordError on refusal.

    REFUSES RATHER THAN REPAIRS, which is the same rule `_compose_selection` follows and for the same
    reason: every refusal below names something this seat is structurally able to get wrong, and a
    repaired refusal makes the gate advisory. A caller that catches this records an idle beat.
    """
    obj = _json_object(raw)
    if not isinstance(obj, dict):
        raise RecordError("APPRAISER_REPLY_NOT_JSON",
                          "the emotion seat's reply carried no JSON object")
    return _readings.parse(obj, percepts=percepts, present=present, me=me)


def _norm_span(s):
    """Whitespace-collapsed, lower-cased: the only tolerance a copied span is allowed."""
    return " ".join(str(s or "").split()).lower()


def parse_event_reply(raw, objects=None, action=None, exertion=False, tells=False, injuries=False, present=None,
                      actor=""):
    """A raw event-seat reply -> the tags dict the twelve dimension consumers already read.

    Emits the shape the twelve dimension consumers read ({type, dimensions, durability}) plus, since
    2026-09-17, the bond tier's read: `object` (a name from the lists the seat was shown, or self)
    and `showed` ({axis: height} — words priced HERE through `bonds.observations_from_showed`, plus
    a validated debt entry). `objects` is the allowed object list (people present + referenced +
    attachments); None skips the object check (a caller with no lists, e.g. a unit test).
    `severity.normalise_dimensions` still turns the dimension words into floats -- one resolver.

    THE QUOTE CHECK (2026-09-18). Every `showed` word arrives as {"word", "quote"}; the quote must
    be a span of the beat's `action` (whitespace and case aside). A bare word is refused
    (APPRAISER_QUOTE_MISSING); a span the action does not contain is refused
    (APPRAISER_FACT_NOT_IN_ACTION). `action=None` skips the containment check only — the quote is
    still required. The spans come back as `quotes` {axis: span} beside the priced `showed`, so the
    log can be audited word by word. Why: the boundary tests in the glosses were advice the seat
    could ignore (the .66 trust word on nearly every beat of one live scene, its test in the prompt); a
    span it has to copy is a claim the parser can hold it to.
    """
    obj = _json_object(raw)
    if not isinstance(obj, dict):
        raise RecordError("APPRAISER_REPLY_NOT_JSON",
                          "the event seat's reply carried no JSON object")
    dims = obj.get("dimensions")
    if not isinstance(dims, dict):
        raise RecordError("APPRAISER_DIMENSIONS_TYPE",
                          "the event seat returned %r for dimensions, not an object"
                          % type(dims).__name__)
    unknown = sorted(d for d in dims if d not in DIMENSIONS)
    if unknown:
        raise RecordError("APPRAISER_DIMENSION_UNKNOWN",
                          "the event seat named %s, which are outside the vocabulary %s"
                          % (unknown, list(DIMENSIONS)))
    bad = sorted(str(v) for v in dims.values() if str(v) not in SEVERITY_WORDS)
    if bad:
        raise RecordError("APPRAISER_SEVERITY_WORD_UNKNOWN",
                          "the event seat used %s; the rubric is %s" % (bad, list(SEVERITY_WORDS)))
    dur = str(obj.get("durability", "transient"))
    if dur not in ("transient", "durable"):
        raise RecordError("APPRAISER_DURABILITY_UNKNOWN",
                          "durability must be transient or durable, got %r" % dur)
    # THE TYPE IS A CLOSED WORD, the same six the actor is offered (consolidation.ACTOR_TAG_TYPES).
    # The first live beat on a real book (2026-09-11) answered a phrase here, this parser passed it,
    # and consolidation killed the run with TAG_TYPE_UNKNOWN before anything committed — the seat
    # had never been shown the list. Refused by name now, so the driver's seat-refusal path takes it.
    etype = str(obj.get("type", "mundane")).strip().lower()
    if etype not in ACTOR_TAG_TYPES:
        raise RecordError("APPRAISER_TYPE_UNKNOWN",
                          "the event seat's type %r is not one of %s" % (str(obj.get("type")), list(ACTOR_TAG_TYPES)))
    out = {"type": etype, "dimensions": dict(dims), "durability": dur}
    # THE RETIRED BLOCK IS REFUSED, NOT FILTERED (2026-09-17). `social` carried strength words that
    # `bonds.act_from_tags` could not float and silently skipped — 0 relationship_deltas on every live
    # performance. A cached reply from before the contract changed cannot replay under it.
    if isinstance(obj.get("social"), dict) and obj.get("social"):
        raise RecordError("APPRAISER_SOCIAL_RETIRED",
                          "the event seat answered with `social` (strength words); the contract is `object` + `showed` on the act ladders")
    # THE DEBT VERDICT IS RETIRED (2026-09-18): the seat reports what changed hands (`transfers`) and
    # bonds.debt_postings derives the entry. A cached reply carrying the verdict cannot replay here.
    if obj.get("debt") or (isinstance(obj.get("showed"), dict) and "debt" in obj["showed"]):
        raise RecordError("APPRAISER_DEBT_RETIRED",
                          "the event seat answered with a `debt` verdict; the contract is `transfers` (what changed hands, on what terms)")
    # THE OBJECT: from the lists the seat was shown, or self, or empty. Refused otherwise.
    # bond-arithmetic.md s5: the seat names it; the driver stops guessing.
    object_ = str(obj.get("object") or "").strip()
    if object_:
        allowed = {str(x).strip().lower() for x in (objects or ())} | {"self"}
        if objects is not None and object_.lower() not in allowed:
            raise RecordError("APPRAISER_OBJECT_UNKNOWN",
                              "the event seat named %r as the act's object, which is on none of the lists it was shown (%s)"
                              % (object_, ", ".join(sorted(allowed))))
        out["object"] = object_
    showed = obj.get("showed")
    if isinstance(showed, dict) and showed:
        if not object_:
            raise RecordError("APPRAISER_SHOWED_WITHOUT_OBJECT",
                              "the event seat said what the act showed (%s) but named no object" % list(showed))
        words, quotes = {}, {}
        norm_action = _norm_span(action) if action is not None else None
        for axis, val in showed.items():
            if not isinstance(val, dict) or not str(val.get("word") or "").strip():
                raise RecordError("APPRAISER_QUOTE_MISSING",
                                  "the event seat named %r on %s with no {word, quote} — every read quotes the action" % (val, axis))
            span = str(val.get("quote") or "").strip()
            if not span:
                raise RecordError("APPRAISER_QUOTE_MISSING",
                                  "the event seat's %s read (%r) carries no quote" % (axis, val.get("word")))
            if norm_action is not None and _norm_span(span) not in norm_action:
                raise RecordError("APPRAISER_FACT_NOT_IN_ACTION",
                                  "the event seat quoted %r for %s, and the action does not contain it" % (span, axis))
            if str(val["word"]).strip().lower() == _severity.ACT_DERIVED.get(axis):
                raise RecordError("APPRAISER_WORD_DERIVED",
                                  "the event seat named %r on %s; that rung is derived from `told`, not named" % (val["word"], axis))
            words[axis] = val["word"]
            quotes[axis] = span
        # THE SEAM (bond-arithmetic.md s4): words -> heights here, so nothing downstream sees a word.
        # bonds refuses an off-ladder word or axis by code; the driver's seat-refusal path takes it.
        priced = _bonds.observations_from_showed(words)
        out["showed"] = priced
        if quotes:
            out["quotes"] = quotes
    # THE TOLD LIST (2026-09-18, gate seat-told): what was said at a cost to the teller. Shape-checked
    # here; a row whose cost is not `none` DERIVES the trust rung the seat is not offered
    # (severity.ACT_DERIVED) when the seat named no trust word — the seat's own word stands.
    told_rows = obj.get("told")
    kept_told = []
    if told_rows not in (None, []):
        if not isinstance(told_rows, list):
            raise RecordError("APPRAISER_TOLD_SHAPE", "told must be a list of {what, to, cost}, got %r" % type(told_rows).__name__)
        allowed = ({str(x).strip().lower() for x in (objects or ())} | {"self"}) if objects is not None else None
        norm_action = _norm_span(action) if action is not None else None
        for r in told_rows:
            if not isinstance(r, dict):
                raise RecordError("APPRAISER_TOLD_SHAPE", "a told row is not an object: %r" % (r,))
            what = str(r.get("what") or "").strip()
            to = str(r.get("to") or "").strip().lower()
            cost = str(r.get("cost") or "none").strip().lower()
            if not what or not to:
                raise RecordError("APPRAISER_TOLD_SHAPE", "a told row needs what and to: %r" % (r,))
            if allowed is not None and to not in allowed:
                raise RecordError("APPRAISER_TOLD_SHAPE", "a told row names %r; the lists shown were %s" % (to, ", ".join(sorted(allowed))))
            if cost not in _severity.TOLD_COSTS:
                raise RecordError("APPRAISER_COST_UNKNOWN", "told cost %r is not one of %s" % (r.get("cost"), list(_severity.TOLD_COSTS)))
            if norm_action is not None and _norm_span(what) not in norm_action:
                raise RecordError("APPRAISER_FACT_NOT_IN_ACTION", "the event seat quoted %r as told, and the action does not contain it" % what)
            kept_told.append({"what": what, "to": to, "cost": cost})
        out["told"] = kept_told
    costly = [r for r in kept_told if r["cost"] != "none"]
    if costly:
        if not object_:
            raise RecordError("APPRAISER_SHOWED_WITHOUT_OBJECT",
                              "the event seat recorded a told row at a cost (%r) but named no object" % costly[0]["what"])
        rung = _severity.act_value_of("trust", _severity.ACT_DERIVED["trust"])
        have = (out.get("showed") or {}).get("trust")
        # The rung is derived when the seat named no trust word, and LIFTS a warm word below it (the
        # rung's own boundary — "it cost them something to say" — is the told fact; measured 2026-09-18:
        # the seat wrote `dependable` beside an owned fault on three beats). A higher word stands; a
        # cold word stands (a man plainly owning "I lied" is `dishonest` only if the seat says so).
        if have is None or 0.5 < have < rung:
            out.setdefault("showed", {})["trust"] = rung
            out.setdefault("quotes", {})["trust"] = costly[0]["what"]
    # THE TRANSFERS: facts, shape-checked here, priced by bonds.debt_postings. `what` must be a span of
    # the action (the quote check); from/to from the shown lists or self, and different; terms closed.
    rows = obj.get("transfers")
    if rows not in (None, []):
        if not isinstance(rows, list):
            raise RecordError("APPRAISER_TRANSFER_SHAPE", "transfers must be a list of {what, from, to, terms}, got %r" % type(rows).__name__)
        allowed = ({str(x).strip().lower() for x in (objects or ())} | {"self"}) if objects is not None else None
        norm_action = _norm_span(action) if action is not None else None
        kept = []
        for r in rows:
            if not isinstance(r, dict):
                raise RecordError("APPRAISER_TRANSFER_SHAPE", "a transfer row is not an object: %r" % (r,))
            what = str(r.get("what") or "").strip()
            f = str(r.get("from") or "").strip().lower(); t = str(r.get("to") or "").strip().lower()
            terms = str(r.get("terms") or "").strip().lower()
            if not what or not f or not t:
                raise RecordError("APPRAISER_TRANSFER_SHAPE", "a transfer row needs what, from and to: %r" % (r,))
            if f == t:
                raise RecordError("APPRAISER_TRANSFER_SHAPE", "a transfer from %r to %r changes no hands" % (f, t))
            if allowed is not None and (f not in allowed or t not in allowed):
                raise RecordError("APPRAISER_TRANSFER_SHAPE", "a transfer names %r -> %r; the lists shown were %s" % (f, t, ", ".join(sorted(allowed))))
            if terms not in _severity.TRANSFER_TERMS:
                raise RecordError("APPRAISER_TERMS_UNKNOWN", "transfer terms %r is not one of %s" % (r.get("terms"), list(_severity.TRANSFER_TERMS)))
            if norm_action is not None and _norm_span(what) not in norm_action:
                raise RecordError("APPRAISER_FACT_NOT_IN_ACTION", "the event seat quoted %r as a transfer, and the action does not contain it" % what)
            kept.append({"what": what, "from": f, "to": t, "terms": terms})
        out["transfers"] = kept
    # THE ATTRIBUTION (2026-09-19, gate seat-attribution): why the act happened, not what it did.
    # OPTIONAL, and omission is the usual answer — omitted means `unknown` (bonds._ATTRIBUTION: full
    # weight, the reading an untagged act has always had). The word is the closed four the seat is
    # offered (severity.ATTRIBUTION_WORDS: bonds._ATTRIBUTION minus `malice`, which folds into
    # `intent`, and minus `unknown`, which is never written — only left out). Quote-checked exactly
    # as `showed` is: a missing quote and a quote the action lacks reuse those same two codes, because
    # both failures ARE the same failure — a claim about the act with no evidence in the text.
    attribution = obj.get("attribution")
    if attribution is not None:
        if not isinstance(attribution, dict) or not str(attribution.get("word") or "").strip():
            raise RecordError("APPRAISER_QUOTE_MISSING",
                              "the event seat named an attribution (%r) with no {word, quote} — an attributed act quotes the action, like showed" % (attribution,))
        word = str(attribution["word"]).strip().lower()
        if word not in _severity.ATTRIBUTION_WORDS:
            raise RecordError("APPRAISER_ATTRIBUTION_UNKNOWN",
                              "the event seat's attribution %r is not one of %s"
                              % (attribution.get("word"), list(_severity.ATTRIBUTION_WORDS)))
        span = str(attribution.get("quote") or "").strip()
        if not span:
            raise RecordError("APPRAISER_QUOTE_MISSING",
                              "the event seat's attribution (%r) carries no quote" % word)
        norm_action = _norm_span(action) if action is not None else None
        if norm_action is not None and _norm_span(span) not in norm_action:
            raise RecordError("APPRAISER_FACT_NOT_IN_ACTION",
                              "the event seat quoted %r for attribution, and the action does not contain it" % span)
        out["attribution"] = word
    # EXERTION (gate body-exertion) - read only when it was asked: one word from the body system's ladder
    # and, above `none`, a quote the action contains, checked as `showed` and `attribution` are. Omitted
    # is `none`. When it was NOT asked, a stray key is dropped: the prompt said nothing of it.
    if exertion:
        ex = obj.get("exertion")
        if ex is None:
            out["exertion"] = "none"
        else:
            if not isinstance(ex, dict) or not str(ex.get("word") or "").strip():
                raise RecordError("APPRAISER_QUOTE_MISSING",
                                  "the event seat named an exertion (%r) with no {word, quote}" % (ex,))
            word = str(ex["word"]).strip().lower()
            if word not in _body.EXERTION_WORDS:
                raise RecordError("APPRAISER_EXERTION_UNKNOWN",
                                  "the event seat's exertion %r is not one of %s" % (ex.get("word"), list(_body.EXERTION_WORDS)))
            span = str(ex.get("quote") or "").strip()
            if word != "none" and not span:
                raise RecordError("APPRAISER_QUOTE_MISSING", "the event seat's exertion (%r) carries no quote" % word)
            if span and action is not None and _norm_span(span) not in _norm_span(action):
                raise RecordError("APPRAISER_FACT_NOT_IN_ACTION",
                                  "the event seat quoted %r for exertion, and the action does not contain it" % span)
            out["exertion"] = word
    # TELLS (gate tells) - read only when asked: at most three quotes of signs only a sharp eye catches, each
    # found in the action as `showed` is. Omitted is none. Not asked, a stray key is dropped.
    if tells:
        raw_t = obj.get("tells") or []
        if not isinstance(raw_t, list) or len(raw_t) > _tells.MAX_PER_BEAT or not all(isinstance(t, dict) for t in raw_t):
            raise RecordError("APPRAISER_TELLS_SHAPE", "the event seat's tells %r is not a list of at most %d {quote}"
                              % (raw_t, _tells.MAX_PER_BEAT))
        quotes = []
        for t in raw_t:
            span = str(t.get("quote") or "").strip()
            if not span:
                raise RecordError("APPRAISER_QUOTE_MISSING", "the event seat named a tell with no quote")
            if action is not None and _norm_span(span) not in _norm_span(action):
                raise RecordError("APPRAISER_FACT_NOT_IN_ACTION",
                                  "the event seat quoted %r as a tell, and the action does not contain it" % span)
            quotes.append(span)
        out["tells"] = quotes
    # INJURIES (gate injuries) - read only when asked: at most three {who, quote, severity}, the one hurt present
    # or the one who acted, each quote found in the action as `showed` is. Omitted is none. Not asked, dropped.
    if injuries:
        out["injuries"] = _injuries.parse_seat(obj.get("injuries"), action, present, actor, _norm_span)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="the two appraiser seats — prompts and parsers")
    ap.add_argument("--seat", choices=("emotion", "event", "both"), default="both")
    ap.add_argument("--action", default="")
    ap.add_argument("--thought", default="")
    ap.add_argument("--moment", default="")
    ap.add_argument("--present", default="")
    ap.add_argument("--me", default="")
    ap.add_argument("--target", default="")
    ap.add_argument("--prompt-only", action="store_true",
                    help="emit the prompt(s) and stop — the seam Mode B drives")
    ap.add_argument("--reply", default="",
                    help="a raw reply to parse (path to a file, or the text itself)")
    a = ap.parse_args(argv)

    present = [p.strip() for p in a.present.split(",") if p.strip()]
    seats = ("emotion", "event") if a.seat == "both" else (a.seat,)

    if a.reply:
        raw = io.open(a.reply, encoding="utf-8").read() if os.path.exists(a.reply) else a.reply
        for seat in seats:
            if seat == "emotion":
                rs, lands, conf = parse_emotion_reply(raw, present=present, me=a.me)
                print(json.dumps({"readings": [r.__dict__ for r in rs],
                                  "lands_on": lands, "confidence": conf}, indent=2))
            else:
                print(json.dumps(parse_event_reply(raw), indent=2))
        return 0

    for seat in seats:
        msgs = (build_emotion_messages(a.action, a.thought, a.moment, present, a.me)
                if seat == "emotion" else
                build_event_messages(a.action, a.moment, present, a.me, a.target))
        print("=" * 78)
        print("SEAT: %s   (%d chars)" % (seat.upper(), sum(len(m["content"]) for m in msgs)))
        print("=" * 78)
        for m in msgs:
            print("--- %s ---" % m["role"])
            print(m["content"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
