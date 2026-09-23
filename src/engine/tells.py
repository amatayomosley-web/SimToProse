"""tells.py — the small signs a sharp eye catches, and a listener who misses them never reads (the `tells` system).

WHY THIS EXISTS (gate tells, 2026-09-22). The design says perception FILTERS what a character apprehends: "A
failed check removes a detail (they didn't notice)" (docs/scene-assembly.md:46; relevancy-gate.md:31). As built it
removed nothing. Each actor reads the others' acts word for word in "The moment" (`prompt.compose_event`), so a
tremor another actor wrote reached a dull listener exactly as it reached a sharp one; the subtle-cue check only
decided whether the lexicon's cue NAME was also given. The owner asked where the tells could even come from,
since the actors play the scenes and no one writes them - and answered "Yes" to this: the EVENT READER, which
already reads every beat and quotes the words behind what it reports, marks the parts of an act only a sharp eye
would catch; a listener who does not catch them never reads those words.

WHO CATCHES A TELL: the same check the lexicon's subtle cues use - `baseline.skills.perception` against
`gate.PERCEPTION_DC_SUBTLE`. A listener who catches it reads the act whole and is TOLD it, as a percept (what
the design calls admitting the attribute into the PerceptSet). One who does not reads the act with the quoted
words cut. A character's own acts are never cut: they did them.

The system is OFF by default: with it off the reader is not asked, every moment is composed exactly as before.
Energy does not yet change who catches a tell - the owner's question, asked after this.

Deterministic, stdlib + engine imports only, no LLM, no randomness.
"""
from __future__ import annotations

__layer__ = "engine"

import re

from .gate import PERCEPTION_DC_SUBTLE, _energy_budget
from .prompt import MOMENT_BEATS

MAX_PER_BEAT = 3
# A worn mind's eye (gate tired-eyes): the share of perception a mind with nothing left keeps. [START - FALSIFIER:
# a character who slept a full night reads as missing what a rested eye catches.]
WORN_EYE = 0.5

# The reader's question, appended to the event seat's prompt only for a book that runs `tells`.
RUBRIC = """

TELLS. This book also asks for the act's TELLS: the small signs in it that only a sharp eye would catch - a
tremor, a glance away, a hesitation, a word caught back - shown by the one named under WHO ACTED without meaning
to. Add to the JSON:

 "tells": [{"quote": "<the words of the action that show the sign, copied exactly>"}]

Most beats have NONE: leave the list empty. At most three. An open act, a spoken word or a deliberate gesture is
not a tell - everyone sees and hears it. A listener who is not sharp will not be shown the words you quote, so
quote only the sign itself, never what anyone needs in order to follow the scene.
"""


def catches(char, tired=False):
    """Does this listener catch the small signs? -> bool (the lexicon's subtle-cue line).

    `tired` (the book also runs `condition_flow`; the owner's ruling D3, 2026-09-22): a worn mind catches less -
    the skill is weighed by what the MIND has left, read exactly as the memory budget reads it
    (`gate._energy_budget`: the mind's side, less the load's penalty). A rested mind keeps its whole eye; one with
    nothing left keeps `WORN_EYE` of it."""
    skills = (char.get("baseline") or {}).get("skills") or {}
    eye = float(skills.get("perception", 0.5))
    if tired:
        left = max(0.0, min(1.0, _energy_budget((char.get("current") or {}).get("condition") or {})))
        eye *= WORN_EYE + (1.0 - WORN_EYE) * left
    return eye >= PERCEPTION_DC_SUBTLE


def cut(action, quotes):
    """The act with each quoted sign removed, the text tidied where it closed up -> str."""
    out = str(action)
    for q in quotes or ():
        words = str(q).split()
        if words:
            out = re.sub(r"\s*" + r"\s+".join(re.escape(w) for w in words), "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    out = re.sub(r"([,;:])(\s*[,;:.])+", r"\2", out)
    return out.strip()


def for_listener(log, me, sharp):
    """The log as THIS listener reads it -> (log, hidden, noticed). Each other actor's beat whose tags carry
    `tells`: cut from its action when `sharp` is False, kept when True. `hidden` / `noticed` are [{"who", "quote"}]
    for the beats the moment SHOWS (the last `prompt.MOMENT_BEATS`) - the beat's manifest, and the percepts a
    sharp listener is told."""
    out, hidden, noticed = [], [], []
    shown = len(log or ()) - MOMENT_BEATS
    for i, b in enumerate(log or ()):
        quotes = [str(t) for t in ((b.get("tags") or {}).get("tells") or ()) if str(t).strip()]
        if not quotes or b.get("who") == me:
            out.append(b)
            continue
        if i >= shown:
            (noticed if sharp else hidden).extend({"who": b.get("who"), "quote": q} for q in quotes)
        out.append(b if sharp else dict(b, action=cut(b.get("action", ""), quotes)))
    return out, hidden, noticed
