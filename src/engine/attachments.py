"""attachments.py — what a person holds that is not a person: the price table, the sheet block, the
append-only rows, and the names the world registers (docs/bond-arithmetic.md s3, bond gate 5).

THE OWNER'S RULE (bond-arithmetic.md s0): nothing but a person or a held thing moves a bond, and a
value in the abstract moves nothing. Until this module every caller of `bonds.stake_of` passed
`held=None`, so an act on a place or a group priced stake 0 for every witness, was never `received`,
and below the overtness bar was not witnessed at all — the bowls club a woman had founded was, to
the arithmetic, nobody's.

WRITTEN BY THREE, NEVER BY SPEECH. The author (the sheet block, linted beside `relationships`); the
composition pass (a classifier names a RELATION WORD per registered entity with the backstory
sentence that shows it, and `block_from_words` prices it); the director (the scene cfg's typed
declarations at scene start) — and the keeper, on a claim the canon gate ESTABLISHED, priced one rung
below until an act corroborates it (`declared_row(self_sourced=True)`; called from
`scripts/keeper.py:attach_scene`, at the canon gate after `rule_scene`, 2026-09-19). THE TABLE IS THE
ENGINE'S: no classifier, director or seat is ever shown a number — a number from a model would make
its misreading indistinguishable from a miscalibration.

TWO KEY SPACES, NOT FOUR. `loc.<world.locations id>` and `grp.<people[].groups tag>`. A registry
concept already reaches `connection.held_map` through a WOUND (keyed per path), and a value already
IS the worth-menu weight — letting this block carry either would give one key two writers with two
shapes, the duplicate class CLAUDE.md tabulates. A cause is held through its place or its people.

ONE REGISTRY, TWO READERS, TWO FLOORS. `connection.held_map` folds the block in beside wounds, goals
and values; `connection.for_about` reads it under the feeling floor (.20 — an `acquainted` .15
amplifies no feeling) while `bonds.stake_of` reads the same number unfloored (a gate is not a
multiplier: it gates belief at .15). The number is one; the readers differ on purpose.

IMPORT DISCIPLINE. `connection` imports this; `bonds` imports `state`, which imports `connection`;
so this module imports `.records` only and carries its own clamp.
"""
from .records import RecordError, AttachmentDeclared

# THE RELATION-WORD TABLE (bond-arithmetic.md s3) — an authoring rubric, not fitted: "so a read is
# arguable and a number is not". `none` is the director's word for a hold that ENDED (dismissed, the
# ship sank) and is never offered to a classifier. [DOC s3]
RELATION_HOLDS = {"life": 0.85, "post": 0.60, "member": 0.40, "acquainted": 0.15, "none": 0.0}
RELATION_WORDS = ("life", "post", "member", "acquainted")     # the rubric's four, warm to cool
SIGNS = ("+", "-")                                            # `-` reserved; v1 arithmetic folds `+` only [DOC s3]
LOC, GRP = "loc.", "grp."                                     # the two registered id spaces; loc. is gate.py's own percept namespace
# per-character budget of `life`-tier holds, any source — the settled review's guard against "my ship,
# my crew, my port, my guild, all family". Counts `+` entries at or above the life hold, so an authored
# .90 counts. [JUDGMENT — settled review s4 guard (b); falsifier: an authored sheet the owner wants with three]
_LIFE_CAP = 2
# the boundary tests, digit-free — each names what separates the word from the one BELOW it
_GLOSS = {
    "life":       "losing it would change her days: her livelihood, her home, her child's home, her life's work — the backstory must SHOW the dependence (she built it, lives by it, was ruined for it), never merely call it dear",
    "post":       "her position, crew, parish, ship: hers while she keeps it, and it could be taken — below life because she would go on without it",
    "member":     "she belongs, attends, is native of it: one of several such things she is part of, none of which she keeps",
    "acquainted": "she knows it, passes through, has dealings there — below member because nothing of hers is in it",
}
_INSERT = ("INSERT INTO attachment_declared (run_id, turn, char_id, entity, hold, sign, source) "
           "VALUES (?, ?, ?, ?, ?, ?, ?)")


def _clamp01(x):
    return max(0.0, min(1.0, float(x)))


def _prefixed(key):
    k = str(key)
    return k.startswith(LOC) and len(k) > len(LOC) or k.startswith(GRP) and len(k) > len(GRP)


def hold_of(word):
    """A relation word -> its hold. Refuses an off-table word (ATTACH_WORD_UNKNOWN); never repairs."""
    w = str(word or "").strip().lower()
    if w not in RELATION_HOLDS:
        raise RecordError("ATTACH_WORD_UNKNOWN", "attachments.hold_of: %r is not a relation word; expected one of %s"
                          % (word, ", ".join(RELATION_WORDS) + ", none"))
    return RELATION_HOLDS[w]


def word_of(hold):
    """A hold -> the relation word it prices AT: the inverse of `hold_of`. The warmest word in
    RELATION_WORDS whose price sits at or below the hold, so a hold a shade above `post`'s .60
    still reads as post rather than rounding up to life. Below `acquainted`'s floor (.15) —
    including a `none` hold's 0.0 — there is no word: refuses ATTACH_HOLD_UNWORDED rather than
    inventing a fifth, colder rung.

    Derived, never stored: the block's only priced value is the hold (bond-arithmetic.md s3), and
    an inverse table is the one source of truth for what it is CALLED — a word written beside the
    number on the sheet would be a second copy of the same fact, free to disagree with the number
    that prices it (the duplicate class CLAUDE.md tabulates).
    """
    if not isinstance(hold, (int, float)) or isinstance(hold, bool) or not 0.0 <= float(hold) <= 1.0:
        raise RecordError("ATTACH_HOLD_RANGE", "attachments.word_of: hold must be a float in [0, 1], got %r" % (hold,))
    h = float(hold)
    for w in RELATION_WORDS:
        if h >= RELATION_HOLDS[w]:
            return w
    raise RecordError("ATTACH_HOLD_UNWORDED",
                      "attachments.word_of: hold %r prices below acquainted (.15) — no word for the actor" % (hold,))


def word_below(word):
    """One rung cooler: life -> post -> member -> acquainted -> acquainted. The self-sourced guard (s3):
    a hold whose only evidence is the holder's own claim prices here until an act corroborates it."""
    w = str(word or "").strip().lower()
    if w not in RELATION_WORDS:
        raise RecordError("ATTACH_WORD_UNKNOWN", "attachments.word_below: %r is not one of %s" % (word, ", ".join(RELATION_WORDS)))
    i = RELATION_WORDS.index(w)
    return RELATION_WORDS[min(i + 1, len(RELATION_WORDS) - 1)]


def rubric():
    """The four words with their boundary tests, warm to cool, digit-free — what a classifier is
    shown. `none` is not here."""
    return "\n".join("%-11s — %s" % (w, _GLOSS[w]) for w in RELATION_WORDS)


def names_for(world):
    """The world's attachable names -> sorted ["grp.<tag>", ..., "loc.<id>", ...]: what the seat is
    shown and what lint registers. A location is registered by existing in `world.locations`; a group
    by appearing as a `groups` tag on at least one `people[]` entry — no new world field."""
    if not isinstance(world, dict):
        raise RecordError("ATTACH_WORLD_NOT_A_DICT", "attachments.names_for: world must be a dict, got %r" % type(world).__name__)
    names = set()
    for loc in world.get("locations") or []:
        lid = str((loc or {}).get("id") or "").strip() if isinstance(loc, dict) else ""
        if lid:
            names.add(LOC + lid)
    for person in world.get("people") or []:
        for tag in ((person or {}).get("groups") or []) if isinstance(person, dict) else []:
            t = str(tag or "").strip()
            if t:
                names.add(GRP + t)
    return sorted(names)


def validate_block(block, registered=None):
    """`current.attachments` -> the same block, checked. Refuses: ATTACH_BLOCK_NOT_A_DICT,
    ATTACH_ENTRY_NOT_A_DICT, ATTACH_KEY_UNPREFIXED, ATTACH_ENTITY_UNREGISTERED (when `registered` is
    given), ATTACH_HOLD_RANGE, ATTACH_SIGN_UNKNOWN (an absent sign reads "+"), ATTACH_LIFE_CAP."""
    if not isinstance(block, dict):
        raise RecordError("ATTACH_BLOCK_NOT_A_DICT", "current.attachments must be {entity: {hold, sign, note}}, got %r" % type(block).__name__)
    reg = {str(x) for x in registered} if registered is not None else None
    life = 0
    for key, entry in block.items():
        if not isinstance(entry, dict):
            raise RecordError("ATTACH_ENTRY_NOT_A_DICT", "current.attachments[%r] must be an object, got %r" % (key, type(entry).__name__))
        if not _prefixed(key):
            raise RecordError("ATTACH_KEY_UNPREFIXED", "current.attachments key %r carries no loc./grp. prefix — a person belongs in relationships (the edge is the hold)" % (key,))
        if reg is not None and str(key) not in reg:
            raise RecordError("ATTACH_ENTITY_UNREGISTERED", "current.attachments names %r, which the world does not register (%s)" % (key, ", ".join(sorted(reg)) or "nothing registered"))
        h = entry.get("hold")
        if not isinstance(h, (int, float)) or isinstance(h, bool) or not 0.0 <= float(h) <= 1.0:
            raise RecordError("ATTACH_HOLD_RANGE", "current.attachments[%r].hold must be a float in [0, 1], got %r" % (key, h))
        sign = entry.get("sign", "+")
        if sign not in SIGNS:
            raise RecordError("ATTACH_SIGN_UNKNOWN", "current.attachments[%r].sign must be '+' or '-', got %r" % (key, sign))
        if sign == "+" and float(h) >= RELATION_HOLDS["life"]:
            life += 1
    if life > _LIFE_CAP:
        raise RecordError("ATTACH_LIFE_CAP", "current.attachments carries %d life-tier holds; the cap is %d (nobody holds everything as their life)" % (life, _LIFE_CAP))
    return block


def holds_of(block):
    """The block -> {entity: hold} for "+" entries, floats only — what held_map folds and what the
    replay hands to stake_of. {} for None."""
    out = {}
    for key, entry in (block or {}).items() if isinstance(block, dict) else ():
        if not isinstance(entry, dict) or entry.get("sign", "+") != "+":
            continue
        h = entry.get("hold")
        if not isinstance(h, (int, float)) or isinstance(h, bool):
            raise RecordError("ATTACH_HOLD_RANGE", "current.attachments[%r].hold is not a number: %r" % (key, h))
        out[str(key)] = _clamp01(h)
    return out


def block_from_words(words):
    """{entity: (relation word, sentence)} -> a sheet block priced from the table, note "<word>: <sentence>",
    sign "+". The composition pass's write; the script never touches a number."""
    block = {}
    for entity, pair in (words or {}).items():
        word, sentence = pair
        block[str(entity)] = {"hold": hold_of(word), "sign": "+", "note": "%s: %s" % (str(word).strip().lower(), str(sentence or "").strip())}
    return validate_block(block)


def declared_row(char_id, entity, word, source, self_sourced=False):
    """A typed declaration -> AttachmentDeclared priced from the table (a director typing a float is the
    same defect as a model emitting one). self_sourced=True prices word_below(word): the keeper guard."""
    w = str(word or "").strip().lower()
    priced = hold_of(word_below(w)) if self_sourced and w in RELATION_WORDS else hold_of(w)
    row = AttachmentDeclared(char_id=str(char_id), entity=str(entity), hold=priced, sign="+", source=str(source))
    row.validate()
    return row


def seed_rows(char_id, block, existing=()):
    """`authored` rows for every entity of the block that `existing` (rows_for's shape) does not
    already carry -> [AttachmentDeclared]. Pure."""
    have = {str(e) for _t, e, _h, _s, _src in (existing or ())}
    rows = []
    for entity, entry in (block or {}).items() if isinstance(block, dict) else ():
        if str(entity) in have or not isinstance(entry, dict):
            continue
        row = AttachmentDeclared(char_id=str(char_id), entity=str(entity), hold=_clamp01(entry.get("hold", 0.0) or 0.0),
                                 sign=str(entry.get("sign", "+")), source="authored")
        row.validate()
        rows.append(row)
    return rows


def write(con, run_id, turn, rows):
    """Rows into attachment_declared on the CALLER's transaction (no transaction of its own)."""
    for r in rows or ():
        r.validate()
        con.execute(_INSERT, (run_id, int(turn), r.char_id, r.entity, float(r.hold), r.sign, r.source))


def rows_for(con, run_id, char_id):
    """[(turn, entity, hold, sign, source)] for one character, in log order (turn, attachment_id)."""
    return [(int(r[0]), r[1], float(r[2]), r[3], r[4]) for r in con.execute(
        "SELECT turn, entity, hold, sign, source FROM attachment_declared WHERE run_id = ? AND char_id = ? "
        "ORDER BY turn, attachment_id", (run_id, char_id))]


def seed(con, run_id, turn, char_id, block):
    """Idempotent: authored rows for the block's entities that have none yet, at `turn`, own
    transaction -> rows written. Run creation, a late join, a pre-v30 resume all call it."""
    rows = seed_rows(char_id, block, existing=rows_for(con, run_id, char_id))
    if rows:
        with con:
            write(con, run_id, turn, rows)
    return len(rows)


def declare(con, run_id, turn, rows):
    """The director's rows at a scene's first turn, own transaction -> rows written. Idempotent on
    (turn, char_id, entity, hold, source): a re-invoked scene does not double-declare."""
    fresh = []
    for r in rows or ():
        have = {(t, e, h, s) for t, e, h, _sg, s in rows_for(con, run_id, r.char_id)}
        if (int(turn), r.entity, float(r.hold), r.source) not in have:
            fresh.append(r)
    if fresh:
        with con:
            write(con, run_id, turn, fresh)
    return len(fresh)
