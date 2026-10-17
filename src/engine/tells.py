"""tells.py — the small signs a sharp eye catches, and a listener who misses them never reads (the `tells` system).

WHY THIS EXISTS (gate tells, 2026-09-22). The design says perception FILTERS what a character apprehends: "A
failed check removes a detail (they didn't notice)" (docs/scene-assembly.md:46). As built it removed nothing: each
actor read the others' acts word for word in "The moment" (`prompt.compose_event`).

WHERE A TELL COMES FROM (gate tells-direction; William's ruling via the showrunner, 2026-10-16 21:44): the SCENE BRIEF.
The author gives a character their tells (`cast[].tells`, contracts_scene); that character's actor is told what they
give away without meaning to (`prompt._tell_line`) and, when it shows, writes it in its reply's `tell` field, in its
own words, never in `action`. The record keeps it apart (turns.tell). No reader marks it and no regex cuts it - gate
tells had the event reader quote the signs in an act and cut them per listener; that is gone. No cast[].tells, no
tells.

WHO CATCHES A TELL: the same check the lexicon's subtle cues use - `baseline.skills.perception` against
`gate.PERCEPTION_DC_SUBTLE`. A listener who catches it reads the act with the tell after it and is TOLD it, as a
percept (what the design calls admitting the attribute into the PerceptSet). One who does not reads the act alone.
A character's own rows read whole: they did them.

The system is OFF by default: with it off a scene that states tells is refused (SCENE_TELLS_INVALID).

Deterministic, stdlib + engine imports only, no LLM, no randomness.
"""
from __future__ import annotations

__layer__ = "engine"

from .gate import PERCEPTION_DC_SUBTLE, WORN_EYE, worn_eye   # noqa: F401  (WORN_EYE: the constant is gate's)
from .prompt import MOMENT_BEATS

# A worn mind's eye: `gate.worn_eye` and `gate.WORN_EYE`, one rule for tells and the lexicon's cues (gate tired-lexicon).


def catches(char, tired=False):
    """Does this listener catch the small signs? -> bool (the lexicon's subtle-cue line).

    `tired` (the book also runs `condition_flow`; the owner's ruling D3, 2026-09-22): a worn mind catches less -
    the skill is weighed by what the MIND has left, read exactly as the memory budget reads it
    (`gate._energy_budget`: the mind's side, less the load's penalty). A rested mind keeps its whole eye; one with
    nothing left keeps `WORN_EYE` of it."""
    skills = (char.get("baseline") or {}).get("skills") or {}
    eye = float(skills.get("perception", 0.5))
    if tired:
        eye = worn_eye(eye, (char.get("current") or {}).get("condition") or {})
    return eye >= PERCEPTION_DC_SUBTLE


def for_listener(log, me, sharp):
    """The log as THIS listener reads it -> (log, hidden, noticed). A row whose actor let a `tell` show: another's
    reads with the tell after the act when `sharp`, the act alone when not; one's own reads whole. `hidden` /
    `noticed` are [{"who", "tell"}] for the rows the moment SHOWS (the last `prompt.MOMENT_BEATS`) - the beat's
    manifest, and the percepts a sharp listener is told."""
    out, hidden, noticed = [], [], []
    shown = len(log or ()) - MOMENT_BEATS
    for i, b in enumerate(log or ()):
        tell = " ".join(str(b.get("tell") or "").split())
        if not tell:
            out.append(b)
            continue
        mine = b.get("who") == me
        if i >= shown and not mine:
            (noticed if sharp else hidden).append({"who": b.get("who"), "tell": tell})
        out.append(dict(b, action=("%s %s" % (b.get("action", ""), tell)).strip()) if (sharp or mine) else b)
    return out, hidden, noticed
