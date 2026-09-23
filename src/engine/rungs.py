"""rungs.py — a float on an emotion path -> the rung it is at, and the block that states that rung.

THE MISSING LINK. Until now nothing in `src/engine/` turned a number into a rung. `direction.py`
bands a float into a PHRASE (`_BANDS` at :17) and never into a named position, and a repo grep for
the nine path names returns zero hits outside the docs. So the composer — which must select the rung
a character is ALREADY at, never choose one — had nothing to read. This is that function.

WHAT LEAVES THIS MODULE, AND WHAT NEVER DOES. `rung_at` returns an index and a NAME, for the
composer and for logs. `block_for` returns the block TEXT alone. The name is deliberately NOT part of
what reaches an actor: measured 2026-09-07 across nine draws in three label conditions with byte
identical text beneath, the arm labelled `annoyance` over violent text scored HIGHER than the arm
labelled `fury`, and a blind judge's grouping cut clean across the label conditions. The label is
inert; carrying it to the actor buys nothing and risks a future model weighting the word over the
paragraph. It stays an authoring and selection handle.

AN UNBUILT PATH RAISES. Eight of the nine paths in `docs/emotion-paths.md` have no authored blocks.
Returning an empty string for those would be the defect class this repo names as its dominant one —
declared, wired in isolation, never connected. A path nobody has written must fail where it is asked
for, not read as a character with nothing to feel.

THERE IS NO CONVENIENCE WRAPPER HERE ON PURPOSE. A `live()` returning path+rung+name+block in one
call was written and then deleted the same hour: `tests/test_map.py`'s unreached-function guard
caught it, correctly, because the composer that would call it does not exist yet. A function
written for a caller that has not been built is the exact defect class this repo names as its
dominant one. It comes back with its caller, not before.

Pure, deterministic, stdlib. No LLM (hard rule 3), no float ever returned (hard rule 5).
"""
from .errors import EngineError
from .rung_blocks import BANDS, BLOCKS, DESCENT_BLOCKS


class RungError(EngineError):
    """A path with no authored ladder, a value off the unit interval, or a rung that does not exist."""


# PIVOT per path (redesign gate 3, 2026-09-12): the highest rung a character can leave WITHOUT the
# way down being its own state. At or below the pivot the climb block serves both directions; ABOVE
# it, a DESCENT block does (once authored). DISPLEASURE's is docs/rungs/DISPLEASURE.md's own (anger,
# the last rung a control is surrendered not lost); the rest are PROPOSED and await the owner.
# GOODWILL and DISTASTE have NO descent (care cannot fall; revulsion ends when the thing is gone).
PIVOTS = {
    "DISPLEASURE": 7,   # anger            -- confirmed, in-doc
    "WARINESS":    9,   # dread            -- PROPOSED: above it the fear was somatic
    "DEFLATION":   8,   # despair          -- PROPOSED: terminal flatness, numb re-warming down
    "STIRRING":    7,   # craving          -- PROPOSED: the want has taken you
    "SELF-REGARD": 8,   # hubris           -- PROPOSED: the estimate replaced the world
    "RECEPTIVITY": 9,   # elation          -- PROPOSED: the design's contentment/bliss/savouring
    "LEVITY":      7,   # absorption       -- PROPOSED: flow surfaces
    # GOODWILL, DISTASTE: no descent (design)
}


def paths():
    """Every path this engine can actually resolve -> sorted list. The built set, not the designed one."""
    return sorted(BANDS)


def rung_at(path, value):
    """(path, 0.0..1.0) -> (rung_index, rung_name). 1-based, because rungs are counted from one.

    The bands tile the interval with no gap and no overlap, half-open [lo, hi), and the top band's
    upper edge sits above 1.0 so a saturated vector lands on the peak instead of falling through.
    """
    if path not in BANDS:
        raise RungError("RUNG_PATH_NOT_BUILT",
                        "rung_at: %r has no authored ladder. Built paths: %s. A path in "
                        "docs/emotion-paths.md is DESIGNED, not built, until its blocks are written."
                        % (path, ", ".join(paths()) or "none"))
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise RungError("RUNG_VALUE_NOT_A_NUMBER",
                        "rung_at: %r is not a number; a rung is a position on a 0..1 path" % (value,))
    if not (0.0 <= v <= 1.0):
        raise RungError("RUNG_VALUE_OUT_OF_RANGE",
                        "rung_at: %r is outside [0, 1]. Affect is a unit interval everywhere in this "
                        "engine; a value beyond it means the caller clamped nothing." % (v,))
    for i, (lo, hi, name) in enumerate(BANDS[path], start=1):
        if lo <= v < hi:
            return i, name
    # Unreachable while the bands tile the interval; tests/test_rungs.py asserts they do.
    raise RungError("RUNG_BANDS_DO_NOT_TILE",
                    "rung_at: %.4f on %r fell through every band — the band table has a gap" % (v, path))


def block_for(path, index, descending=False):
    """(path, rung_index) -> the block TEXT for that rung. No name, no number, no label.

    This is what the actor receives. It carries no rung name by design (see the module docstring) and
    no numeral, so nothing in it can be read as a level to perform.
    """
    if path not in BLOCKS:
        raise RungError("RUNG_PATH_NOT_BUILT",
                        "block_for: %r has no authored ladder. Built paths: %s"
                        % (path, ", ".join(paths()) or "none"))
    if index not in BLOCKS[path]:
        raise RungError("RUNG_INDEX_UNKNOWN",
                        "block_for: %r has no rung %r; it has %d rungs"
                        % (path, index, len(BLOCKS[path])))
    # DESCENT (gate 3): above the pivot, a falling value plays the descent block if one is authored;
    # everywhere else, and until the blocks exist, the climb block. The caller passes `descending`
    # from `descending()` below — the last-receipt signal off the log, NOT a hysteresis resolver:
    # none exists (grep finds only a comment), nothing stores a prior rung, and the resolver names
    # the rung fresh from the float each beat (verified 2026-09-12).
    if descending and index > PIVOTS.get(path, len(BLOCKS[path]) + 1):
        d = DESCENT_BLOCKS.get(path, {}).get(index)
        if d:
            return d
    return BLOCKS[path][index]


def descending(mood, origin, last_read_turn, last_turn):
    """({path: mood float}, {path: origin}, {path: turn}, turn|None) -> {path: bool}, one per BUILT path.

    THE DIRECTION OF TRAVEL, off the log and the balance — the one place the rule lives, so neither
    driver re-derives it (2026-09-12, resolved with the peer session). A path is coming down when ALL
    of:

      origin == "mood"     the felt value was set by the MOOD, not by a person's earned attitude
                           (`a >= m`) and not by a present other's damped lift. Only the mood drains
                           on the fast clock; a value held up by an attitude is a plateau toward that
                           person, not a come-down, and keeps the climb block. `toward.balance`
                           reports which branch set each path because it is the function that knows.
      no fuel              the path was NOT read at the actor's most recent completed beat
                           (`last_read_turn[path] != last_turn`). Any reading is fuel — every reading
                           adds a positive vector. Block selection runs BEFORE the act and the seat
                           reads AFTER it, so the previous beat's reading is the freshest there is.
      above the pivot      `rung_at(mood) > PIVOTS[path]`, on the MOOD's own rung, not the composed
                           one. `block_for` still receives the COMPOSED index and applies its own
                           above-pivot check; both are required.

    THE +1-OWN-BEAT LAG is a property, not a bug: the beat where fuel stops still renders the climb
    (its predecessor carried the reading); descent first appears on the actor's SECOND own beat with
    no reading on the path, and only if the mood is still above the pivot by then — a crest before
    the ebb. Beat 1 (no turns, no readings) reads "no fuel" on every path, and every mood is at rest,
    so nothing above a pivot exists to swap. A path with no pivot (GOODWILL, DISTASTE) is never
    descending. No peak is stored and no prior rung: the flaw that sank the retired recovery tier.
    """
    if not isinstance(mood, dict):
        raise RungError("RUNG_MOOD_NOT_A_DICT",
                        "descending: mood must be a dict of {path: float}, got %r" % type(mood).__name__)
    origin = origin if isinstance(origin, dict) else {}
    fuel = last_read_turn if isinstance(last_read_turn, dict) else {}
    out = {}
    for path in paths():
        if path not in mood or path not in PIVOTS:
            out[path] = False
            continue
        index, _name = rung_at(path, mood[path])
        fed = last_turn is not None and fuel.get(path) == last_turn
        out[path] = (str(origin.get(path, "mood")) == "mood") and not fed and index > PIVOTS[path]
    return out


# ---------------------------------------------------------------------------
# WHAT A RUNG IS WORTH — the hard vector table
# ---------------------------------------------------------------------------
# `docs/emotion-arithmetic.md` section 2. A rung's vector is the same for EVERY character and
# EVERY target; the character enters the arithmetic once, as the gain in the receipt step
# (section 3 step 2: `f <- f + v_k * g`). The owner's rule, 2026-09-07:
#
#     "The goal is to set hard numbers for the vector, rung 3 gets the same value across all
#      instances regardless of who is the target of the tag. The character has the multipliers."
#
# DERIVED FROM `BANDS`, NEVER AUTHORED. Ninety-two hand-written vectors would be a duplicate of
# the band table, which is the defect class CLAUDE.md tabulates seven instances of -- and
# `gen_rungs.py` already overwrites `rung_blocks.py` wholesale with drift nobody has measured. A
# derived table cannot rot: move a band and the vector moves with it.
#
# THE FORMULA, and it was CHECKED against the doc's published table before it was written here:
#
#     v_k = LAMBDA[path] * height_k        height_k = the band midpoint, clamped to 1.0
#
# 91 of the 92 published heights are the plain midpoint. The one disagreement is DISPLEASURE's top
# rung `amok`: band (0.98, 1.01) has midpoint 0.995 and the doc prints 1.0. It is a rounding in the
# doc, not a rule -- every OTHER path's top rung is published as its own raw midpoint (DISTASTE
# `abomination` .915, WARINESS `terror` .975, SELF-REGARD `apotheosis` .985), so no clamp-to-one is
# in force anywhere else. A rule that fires exactly once is not a rule. The clamp below is a real
# guard for a different reason: the top band's upper edge sits ABOVE 1.0 on purpose (see `rung_at`),
# so a wide enough top band could produce a midpoint over 1.0, and a vector must not exceed lambda.
#
# LAMBDA IS PER-PATH AND UNIFORM. Section 9 decision 1 -- global 0.15, or per path from the start --
# is the owner's and is unanswered. A dict initialised to the same value everywhere means answering
# it later is a DATA change, not a code change, and the shape already says the answer may differ
# per path. "Control the numbers" is then eight numbers, not ninety-two.
# MEASURED 2026-09-11 (tests/calibrate_accrual.py + tests/test_genotype_balance.py E2). 0.15 was
# the Class-B start and it ran away on real readings: on the first generated scene of a real book a
# character's GOODWILL climbed six rungs in three of his beats on ordinary readings, and on the two
# live read-alongs the state sat above the thermometer's standing level on every path (Red Badge
# error 0.290 vs rest-only 0.140, Holmes 0.192 vs 0.051) with paths pinned at the ceiling.
# Replayed with lambda scaled, the error fell monotonically and the bias crossed ~0 on six of eight
# paths at 0.15-0.25x. The FLOOR per path is the design's own reachability guarantee (E2: the
# strongest person under sustained top-rung readings every ten minutes, with no bond multiplier,
# must reach the top rung) — it is set by each path's half-life, shortest half-life highest
# floor. The table below IS that floor (at 0.002 resolution), which scores like the 0.25x global
# on both thermometers (Red Badge 0.213, Holmes 0.110) while keeping the top reachable. Owner:
# "lower the amount that accrues"; the additive receipt stays (legitimate repetition counts).
LAMBDA = {                               # measured (docs/emotion-arithmetic.md section 2)
    "STIRRING":    0.070,
    "WARINESS":    0.100,                # the shortest half-life needs the largest vector to reach terror
    "DISPLEASURE": 0.054,
    "GOODWILL":    0.030,
    "DEFLATION":   0.066,
    "DISTASTE":    0.026,
    "RECEPTIVITY": 0.042,
    "SELF-REGARD": 0.042,
    "LEVITY":      0.066,
}
assert set(LAMBDA) == set(BANDS), "every built ladder needs its lambda: %s" % sorted(set(BANDS) ^ set(LAMBDA))


def height_of(path, index):
    """(path, 1-based rung index) -> the rung's HEIGHT on [0, 1]: its band midpoint.

    Height is what the rung is, independently of what it is worth. Separated from `vector_for` on
    purpose: the durable tiers compare a reading's HEIGHT against a threshold
    (`docs/emotion-arithmetic.md` section 5 step 7), and they must not have to divide by lambda to
    recover it.
    """
    if path not in BANDS:
        raise RungError("RUNG_PATH_NOT_BUILT",
                        "height_of: %r has no authored ladder. Built paths: %s"
                        % (path, ", ".join(paths()) or "none"))
    rows = BANDS[path]
    if not isinstance(index, int) or isinstance(index, bool) or not (1 <= index <= len(rows)):
        raise RungError("RUNG_INDEX_UNKNOWN",
                        "height_of: rung %r is not on %s, which has %d rungs (1-based)"
                        % (index, path, len(rows)))
    lo, hi, _name = rows[index - 1]
    return min(1.0, (float(lo) + float(hi)) / 2.0)


def vector_for(path, index):
    """(path, 1-based rung index) -> what a tag AT that rung adds, before the character's gain.

    THE SAME NUMBER FOR EVERYONE. This is the whole point of the tier: a `fury` reading is worth
    the same to a placid man and a violent one, and what differs between them is the gain that
    multiplies it. Putting the character in here instead would make two tags at one rung
    incomparable, and the engine could no longer say what a beat was worth.

    On DISPLEASURE this gives `displeasure` 0.0053 through `amok` 0.1493 -- a fury tag is worth
    about twenty-five times a displeasure tag, to everyone.
    """
    return LAMBDA.get(path, 0.15) * height_of(path, index)


def names_on(path):
    """(path) -> the rung NAMES on that ladder, low to high. 1-based positions."""
    if path not in BANDS:
        raise RungError("RUNG_PATH_NOT_BUILT",
                        "names_on: %r has no authored ladder. Built paths: %s"
                        % (path, ", ".join(paths()) or "none"))
    return [name for _lo, _hi, name in BANDS[path]]


def index_of(path, name):
    """(path, rung NAME) -> the 1-based index. The appraiser's half of `rung_at`.

    `docs/emotion-arithmetic.md` section 1: "No number leaves the appraiser." A reading names a
    rung -- `{"path": "DISPLEASURE", "rung": "anger"}` -- so something has to turn that word back
    into the position `vector_for` and `block_for` are keyed by. This is that.

    THE NAME IS THE WIRE FORMAT AND THE INDEX IS NOT, deliberately. An index is a POSITION, and a
    position means nothing once a band is inserted: this repo has already paid for that once, with
    `vault[N]` belief references that became permanently ambiguous the moment a bullet was added
    above them (`gate.py:249` records the cost). A name survives a re-band. If a rung is ever
    RENAMED, stored readings naming the old word fail loudly here rather than resolving to the
    wrong rung silently -- which is the behaviour to want.
    """
    rows = names_on(path)                      # raises on an unbuilt path
    want = str(name).strip().lower()
    for i, rung in enumerate(rows, start=1):
        if rung.lower() == want:
            return i
    raise RungError("RUNG_NAME_UNKNOWN",
                    "index_of: %r is not a rung on %s. Its rungs, low to high: %s"
                    % (name, path, ", ".join(rows)))
