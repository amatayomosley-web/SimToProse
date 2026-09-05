"""narration_modes.py — the two axes a narrator is set on, and only one touches the wall.

    VOICE     grammatical person and distance. A rendering INSTRUCTION over the same transcript.
              Constrained by nothing: the wall does not care which pronoun is used.
    KNOWLEDGE whose recorded interiority the narrator is SHOWN. Enforced by `narrate.pov_split`,
              because "the wall is in the input" — a prompt cannot un-see what it was handed.

They were conflated by one hardcoded string until 2026-09-01. `docs/narration.md` argues close-third
+ pov as the DEFAULT and concedes omniscient is a legitimate mode; the default stands, the
prohibition does not.

WHY THIS IS IN THE ENGINE and not beside the narrator that uses it. Four places need the same
vocabulary: the narrator (to render), `scripts/scene.py` (to accept a director's cfg), the schema
(a CHECK on `scenes.voice`), and `Ledger.append_scene` (because SQLite cannot add a CHECK by ALTER,
so a migrated database has no constraint and the guard must live where BOTH paths pass). Three of
those four are engine-side. A vocabulary copied into a CHECK constraint and a Python tuple and a
CLI's `choices=` is the duplicate class CLAUDE.md tabulates seven instances of — so it lives here,
once, and `tests/test_narrate.py` asserts the schema's CHECK still matches this tuple.
"""
from .errors import EngineError

VOICES = {
    "close-third": "close-third-person prose, bound to a single POV character",
    "first":       "first-person prose in the POV character's own voice",
    "distant-third": "third-person prose at a reserved distance — the camera outside, not inside",
    "second":      "second-person prose addressing the POV character as 'you'",
}
DEFAULT_VOICE = "close-third"

# What omniscient IS here, stated so it cannot drift into something larger. The sim records every
# character's thought and `pov_split` hides the non-POV ones at render time, so:
#
#     pov         the narrator's knowledge = the POV character's vault, for this scene
#     omniscient  the narrator's knowledge = the UNION of recorded interiority, for this scene
#
# Both bounded, both faithful by construction — nothing is invented, the narrator is simply not
# blindfolded. Omniscience over the RECORD is not omniscience over the world.
KNOWLEDGE = ("pov", "omniscient")
DEFAULT_KNOWLEDGE = "pov"


class NarrationError(EngineError):
    """A narration axis set to something that does not exist."""


def validate(voice, knowledge, err=NarrationError):
    """Both axes or raise `err`. The guard lives WITH the vocabulary, not beside each caller.

    `err` DEFAULTS TO A CODED TYPE. It was plain `ValueError`, which meant a caller taking the
    default got a raise that skipped `EngineError`'s registration check entirely — no `.code`, tuple
    rendering, and a typo'd code constructing without complaint. Latent, because every caller passes
    its own type; shipped anyway, inside the gate that converted this surface. A default that
    bypasses the mechanism is the mechanism's own hole.

    SQLite cannot add a CHECK constraint by ALTER, so a database migrated into v13 has no
    constraint on these columns while a fresh one does. The Python guard is therefore not a
    belt-and-braces duplicate of the CHECK — it is the ONLY guard on the migrated path, and it has
    to run wherever a scene is written.
    """
    if str(knowledge) not in KNOWLEDGE:
        raise err("NARRATION_KNOWLEDGE_UNKNOWN",
                  "knowledge %r is not one of %s" % (knowledge, list(KNOWLEDGE)))
    if str(voice) not in VOICES:
        raise err("NARRATION_VOICE_UNKNOWN",
                  "voice %r is not one of %s" % (voice, sorted(VOICES)))
    return True


def require_witness(pov, actors, err=NarrationError):
    """A POV-bound narrator must have been IN the scene. Raises `err`, returns the pov.

    `scripts/narrate.py` enforced this itself, which made it a rule with no owner: the one place
    that knows what a POV means is the module that defines the knowledge axis, and a rule enforced
    only at a call site is a rule the next call site will not enforce.
    """
    known = sorted(actors or [])
    if pov not in known:
        raise err("NARRATION_POV_NOT_PRESENT",
                  "POV %r is not present in this run (actors: %s) — a POV-bound narrator can only "
                  "render what its POV witnessed, so a POV who was never in the scene has nothing "
                  "to narrate from." % (pov, ", ".join(known) or "none"))
    return pov
