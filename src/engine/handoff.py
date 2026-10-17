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
    if "cast" in obj:
        _cast(obj["cast"])
    if "budget" in obj:                         # the scene's ceiling in moves, as the scene file's `moves` (gate budget-in-moves)
        from .contracts_scene import MOVES_MAX
        b = obj["budget"]
        if isinstance(b, bool) or not isinstance(b, int) or not 1 <= b <= MOVES_MAX:
            raise RecordError("HANDOFF_BUDGET_INVALID", "budget %r - a whole number of moves from 1 to %d; leave it out "
                              "and the scene file's moves (else 24) is the ceiling" % (b, MOVES_MAX))
    return obj, playbook


def _members(cast):
    """A direction's cast -> its members as maps; a bare id is {"id": id} (the shorthand docs/CONTRACTS.md shows)."""
    return [{"id": c} if isinstance(c, str) else c for c in cast]


def _cast(cast):
    """A direction's cast is the scene file's cast as far as the author directed it (gate direction-contract): checked
    by contracts_scene's own cast declarations - a key nothing reads, a `to` aimed at no one in it, a character twice -
    with `drive` the one field it may leave to the director. Refused (HANDOFF_CAST_INVALID), every finding named."""
    from . import contracts, contracts_scene
    if not isinstance(cast, list):
        raise RecordError("HANDOFF_CAST_INVALID", "`cast` is a list of ids or {id, drive?, to?, tells?}, not %s"
                          % type(cast).__name__)
    probe = {"cast": [dict({"drive": "-"}, **m) if isinstance(m, dict) else m for m in _members(cast)]}
    fields = tuple(f for f in contracts_scene.SCENE if f.path.split(".")[0] in ("cast", "cast[]"))
    bad = [f for f in contracts.check(probe, fields, systems=("tells",)) if contracts.refuses(f)]   # the book's own
    # switches are the run's to check (contracts.require_at_start); a direction is checked for its shape
    if bad:
        raise RecordError("HANDOFF_CAST_INVALID", "; ".join("%s: %s" % (f["path"], f["message"])
                                                            for f in bad))


def dropped(direction, scene):
    """The scene cfg AS WRITTEN against the author's direction it was written from (gate direction-contract): every
    value the author directed - each cast member, its fields, `at` - must stand in the cfg verbatim; the director may
    add, never drop or change. Raises HANDOFF_DIRECTION_DROPPED naming each one lost; scripts/scene.py calls it before
    the chronicle opens."""
    from .contracts import ignored
    direction, _ = parse_direction(direction)
    scene = scene if isinstance(scene, dict) else {}
    have = {c.get("id"): c for c in scene.get("cast") or [] if isinstance(c, dict)}
    lost = ["at: directed %r, the scene has %r" % (direction["at"], scene.get("at"))
            for _ in [1] if "at" in direction and scene.get("at") != direction["at"]]
    for m in _members(direction.get("cast") or []):
        mine = have.get(m["id"])
        if mine is None:
            lost.append("cast %r: directed, and not in the scene's cast" % m["id"])
            continue
        lost += ["cast %r: %s directed %r, the scene has %r" % (m["id"], k, v, mine.get(k, "nothing"))
                 for k, v in m.items() if k != "id" and not ignored(k) and mine.get(k) != v]
    if lost:
        raise RecordError("HANDOFF_DIRECTION_DROPPED", "the scene file drops or changes what the author directed - %s"
                          % "; ".join(lost))
