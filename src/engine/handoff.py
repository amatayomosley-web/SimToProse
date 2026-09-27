"""handoff.py — the partner route's contract: the DIRECTION a partner writes and the showrunner executes.

The owner, 2026-09-27: "a user can talk with their partner about the next part of the book or scene then the partner
can write the directions using the contract to hand to the showrunner. This keeps the context window for both
smaller". A direction is one JSON object. `parse_direction` refuses a malformed one before anything is spawned, and
names the one playbook its kind loads (.claude/showrunner/playbooks/<playbook>.md), so the spawned showrunner starts
with the right instructions in hand and never has to choose what to read (scripts/brief.py builds that brief). Info
requests need no showrunner: scripts/ask.py answers them from src/engine/read_api.py. docs/CONTRACTS.md is the page a
partner reads (gate partner-contracts).
"""
from .records import RecordError

#: kind -> (the playbook it loads, the fields it needs beside `book` and `kind`)
KINDS = {"scene": ("scene", ("intent",)),
         "render": ("render", ("run",)),
         "declare": ("declare", ("run", "file", "words")),
         "adopt": ("record", ("words",)),
         "approve": ("record", ("draft", "words")),
         "reject": ("record", ("draft",)),
         "rewind": ("record", ("to", "words")),
         "release": ("record", ("words",))}
#: every other field a direction may carry; anything else is refused, never dropped
MAY = ("run", "draft", "words", "cast", "where", "at", "budget", "stub", "note", "in_advance")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def parse_direction(obj):
    """A direction -> (the direction, the playbook its kind loads); refused (HANDOFF_*) before the showrunner spawns.
    The author's words, where a kind needs them, are kept exactly as given - the showrunner passes them to draft.py."""
    if not isinstance(obj, dict):
        raise RecordError("HANDOFF_DIRECTION_UNREADABLE", "a direction is one JSON object, not %s" % type(obj).__name__)
    kind = obj.get("kind")
    if kind not in KINDS:
        raise RecordError("HANDOFF_KIND_UNKNOWN", "kind %r - one of %s" % (kind, ", ".join(KINDS)))
    playbook, need = KINDS[kind]
    missing = [f for f in ("book",) + need if not _text(obj.get(f))]
    if missing:
        raise RecordError("HANDOFF_FIELD_MISSING", "a %s direction needs %s" % (kind, ", ".join(missing)))
    words = obj.get("words")
    if words is not None and (not _text(words) or not any(ch.isalnum() for ch in words)
                              or (words.strip().startswith("<") and words.strip().endswith(">"))):
        raise RecordError("HANDOFF_WORDS_MISSING", "`words` are the author's own words, verbatim - not a placeholder")
    unknown = sorted(set(obj) - {"book", "kind"} - set(need) - set(MAY))
    if unknown:
        raise RecordError("HANDOFF_FIELD_UNKNOWN", "%s - nothing reads it, so the showrunner would never see it"
                          % ", ".join(unknown))
    return obj, playbook
