"""body.py — a strength each character carries, and what each act costs the body (the `body` system).

WHY THIS EXISTS (gate body-exertion, 2026-09-22). The owner ruled that physical exertion drains energy
(C3b) and that "not every event requires the same energy from each person ... this requires a strength stat
for each character" (C3b2): the EVENT READER rates how physically demanding an act is IN ITSELF - the same
word whoever does it - and the ENGINE weighs that against the character's own strength. Emotion already works
this way (the reading is shared; the person's own gain multiplies it, `state.receive`).

The system is OFF by default and needs `condition_flow` (it moves energy). With it off, the reader is never
asked (its prompt is byte-identical, so every recorded seat reply stands) and no sheet needs a strength.

STRENGTH is a WORD on the sheet (`baseline.body.strength`), priced here as CAPACITY - how long this body keeps
going, relative to an ordinary one. It scales what an act costs AND the ordinary drain of waking time (the
working assumption the owner was told: strength stands for physical capacity in general; he may split out
endurance later). Nothing moves it yet (injury, age and training are his open question, C3b4).

EXERTION is a word the reader gives per beat from a closed ladder (`EXERTION_WORDS`), for the body that acted.
Its cost is priced from TIME TO EXHAUSTION: how many minutes of doing only that would take an ordinary body
from fresh to spent (energy 1.0 -> 0.25, the edge of the lowest stage-line band). The engine's one clock
supplies the duration - the beat's minutes, at least `ACT_MINUTES` (an act that took effort took at least a
minute) - and the reader rates only the KIND of effort. Above the ordinary waking drain an act costs

    (SPENT_SPAN / EXHAUSTS_IN[word] - condition.TIME_SPEND) x max(minutes, ACT_MINUTES) / capacity

THE NUMBERS - START values from the exercise literature's shape (time to exhaustion falls steeply with
intensity: a day at an easy pace, an hour at a hard one, minutes all-out), each with a falsifier:
  light 960 min     walking about all day ends the day spent. FALSIFIER: an afternoon's errands reading as worn.
  moderate 240 min  four hours of steady carrying or rowing ends spent. FALSIFIER: an hour's rowing reading spent.
  hard 60 min       an hour of hauling or running ends spent. FALSIFIER: a ten-minute run reading as spent.
  extreme 10 min    ten minutes of all-out struggle ends spent. FALSIFIER: a one-minute scuffle reading as spent.
  capacity          frail 0.5, slight 0.75, ordinary 1.0, strong 1.3, powerful 1.6 [START] - a powerful body
                    keeps going about three times as long as a frail one.
The ladder's definitions were probed on real prose before building (scratchpad S4 on the recorded chronicle,
S4b on public-domain labour and battle passages with two independent raters); see gate body-exertion.

Deterministic, stdlib + engine imports only, no LLM, no randomness.
"""
from __future__ import annotations

__layer__ = "engine"

from . import condition as _condition
from .records import RecordError

STRENGTH_WORDS = {"frail": 0.5, "slight": 0.75, "ordinary": 1.0, "strong": 1.3, "powerful": 1.6}
SPENT_SPAN = 0.75                       # fresh (1.0) to spent (0.25, the lowest band's edge)
ACT_MINUTES = 1.0
# word -> (minutes to exhaustion for an ordinary body doing only this, None = no effort; the reader's line)
# THE LINES, as revised by the probes: no line says how LONG (the clock does), walking of any length is `light`, and
# `extreme` names the effort, not the stakes - two independent raters on 36 public-domain passages agreed on 35 with
# the first draft, split only on its "a step or two" boundary, and each proposed these same changes (S4b).
EXERTION_WORDS = {
    "none":     (None, "talk, look, sit, stand, a gesture, shifting in place; handwork done in place (writing, sewing, "
                       "shelling peas, peeling an apple)"),
    "light":    (960.0, "walking, however far; fetching and carrying small things"),
    "moderate": (240.0, "carrying or holding a real load, climbing, rowing or paddling at an easy pace, steady work with "
                        "hands and back, firing a weapon"),
    "hard":     (60.0, "hauling, running, rowing or pulling at full strength, lifting what takes the whole body, a scuffle"),
    "extreme":  (10.0, "grappling hand-to-hand at full strength, struggling not to drown, carrying a person, hauling past "
                       "the point of breath"),
}


def capacity(char, weakened=0):
    """How long this body keeps going, relative to an ordinary one -> float. Refuses a sheet the body system
    cannot weigh: no strength, or a word the engine does not price.

    `weakened` (gate injury-weakens, the owner's ruling D6): how many strength words lower the body counts while
    an injury heals (`injuries.weakening`) - never below the lowest word. 0, the default, is the sheet's word."""
    body = (char.get("baseline") or {}).get("body")
    word = body.get("strength") if isinstance(body, dict) else None
    if word is None:
        raise RecordError("BODY_STRENGTH_MISSING", "the body system weighs every act against baseline.body.strength, "
                          "and this sheet has none (one of %s)" % ", ".join(STRENGTH_WORDS))
    if str(word).lower() not in STRENGTH_WORDS:
        raise RecordError("BODY_STRENGTH_UNKNOWN", "baseline.body.strength %r is not one of %s" % (word, ", ".join(STRENGTH_WORDS)))
    words = list(STRENGTH_WORDS)
    return STRENGTH_WORDS[words[max(0, words.index(str(word).lower()) - max(0, int(weakened or 0)))]]


def require(char):
    """Refuse, before the first beat, a sheet the body system cannot weigh -> the char."""
    capacity(char)
    return char


def exert(condition, word, minutes, cap):
    """What the act cost this body -> a NEW condition (energy only; the load is stress's, not effort's).
    `word` None (the reader was not asked, refused, or a stub beat) costs nothing, as `none` does."""
    if word is None:
        return dict(condition)
    key = str(word).lower()
    if key not in EXERTION_WORDS:
        raise RecordError("BODY_EXERTION_UNKNOWN", "exertion %r is not one of %s" % (word, ", ".join(EXERTION_WORDS)))
    span = EXERTION_WORDS[key][0]
    if span is None:
        return dict(condition)
    minutes = _condition._span(minutes, "minutes")
    _condition._pair(condition)
    rate = max(0.0, SPENT_SPAN / span - _condition.TIME_SPEND)
    # the BODY's side: the shared pool, then the body's reserve - never the mind's (gate energy-reserves)
    return _condition.draw(condition, rate * max(minutes, ACT_MINUTES) / float(cap), "body")


def rubric():
    """The ladder as the event reader is shown it, derived from the table the engine prices."""
    return "\n".join("  %-9s - %s" % (w, line) for w, (_span, line) in EXERTION_WORDS.items())
