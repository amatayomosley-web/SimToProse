"""heritable.py — the genotype (hit, hold per PATH) and the one reading of where a character RESTS.

`docs/baseline-generation.md` founds the genotype on one job: from ONE species prior, make ten
strangers react differently to the same betrayal. Until 2026-09-10 it did that through six axes
named for Panksepp's primitives (threat_reactivity, approach_drive, ...) that were RENAMED IN PLACE
to path names by `92a9942` and never re-derived — three of the eight paths had no axis at all and
sat at the species prior for everyone. The rebuild of 2026-09-10 made it, per path, cells drawn
INDEPENDENTLY (owner's decision 2 of 2026-09-09 — one allele carrying everything WELDS them, and a
character must be able to rest calm and hold fear for weeks). Later the same day the owner moved
the resting cell OUT of the genotype: *"Have temperament be a character design question, along
with their voice and other personality options."* So:

  fixed.genotype[path] = {hit, hold}       — the heritable RATES, drawn for background people
    hit    the ALLELE — the gain `g` in `f <- f + v_k * g` (docs/emotion-arithmetic.md section 3),
           the only per-character term in the accumulation rule. `GAIN`.
    hold   the genotype's term in DECAY — a multiplier on the path's HALF-LIFE, never an absolute
           rate: `state.half_life_minutes(path, value, hold)` = the zone's half-life x hold, and
           retention over m minutes is 0.5 ** (m / that). So "lasting" stretches every path's
           excursion by the same ratio under whatever per-path table is authored, which is what
           lets the person system and the global system be balanced separately (owner: "be sure
           that we can balance the 2 systems"). A `1 - (1 - r)/hold` form on a per-beat rate was
           measured and rejected first — it stretched x1.18 at r=.72 and x1.16 at r=.90, so one
           word meant a different thing on every path. `PERSIST`.

  baseline.temperament[path] = {rest, mean}  — the character DESIGN, authored beside voice/traits
    rest   the STARTING VECTOR — where the float sits when nothing is happening, and what decay
           relaxes toward. A word names a RUNG (`REST_WORDS`, rung 1..4); an authored NUMBER is
           the mean itself. CAPPED PER PATH (`REST_CAP`) at the last rung that reads as a
           disposition rather than an episode — agreed 2026-09-10; the draw never goes above it,
           and an authored rest above it (word or number) is honoured with a `lint_book` WARN
           naming the rung, so a misanthrope resting at *loathing* is a deliberate act with a
           receipt and never a roll.
    mean   DERIVED from `rest` the first time the sheet reaches the engine (`ensure_temperament`):
           the rung's band midpoint read from `rung_blocks.BANDS` at call time, so a re-band moves
           every rest with it. STORED, because the arc engine writes durable diffs into it and
           `arc.erode` relaxes back toward the stamped value; an existing mean is never rewritten.

A WORD draws the preset; a NUMBER is used exactly as authored. Authors annotate words —
`"high (anxious-leaning bond style)"` — and `word()` is THE one parse; four modules once each
carried their own `.split()[0].lower()` and a fifth reader that did not silently made persistence
a no-op on every annotated sheet.

THE PRESET VALUES ARE THE CONSERVATIVE START. `GAIN` and `PERSIST` below are the numbers carried
from the primitive era, adopted 2026-09-10 as the start the owner tunes in real runs ("we just
need a conservative decay rate and we will tune during testing"). `scripts/derive_genotype.py`
is a tool for that tuning loop — it prints what the idle-floor bound admits at a stated sensor
rate — and `tests/test_genotype_balance.py` guards reachability and rank order. Nothing here
claims these values are final; they are the ones the first runs are measured against.

REFUSED BY NAME rather than translated: the OLD six-axis genotype (`GENOTYPE_OLD_AXES`) and a
`rest` key inside a genotype cell (`GENOTYPE_REST_MOVED`) — the shape of the morning of
2026-09-10. Both fixtures were rewritten by hand; a real book migrates once, with its author's
eyes on it. CUT on the owner's "cut what doesn't align": `effortful_control`, `sensitivity`,
`AXIS_FOR`, the HEXACO bumps on gain, and (with this move) `variability` on the derived row — it
was read by nothing (`guide-content.md` lists it inert).
"""
from .records import PATHS, RecordError
from .rung_blocks import BANDS

# The two cells every path's genotype carries.
AXES = ("hit", "hold")

# rest: a word names a RUNG, 1-based. `quiet` is the path's own name, the neutral floor.
REST_WORDS = ("quiet", "low", "raised", "high")

# The last rung that reads as a DISPOSITION — who the character is on an ordinary day — rather
# than an episode. Read off each ladder's words 2026-09-10 (last rung used as a trait in plain
# English: "a worrier", "a squeamish man"); a numeric cross-check (band top <= 0.45, leaving more
# than half the float for what happens to them) agreed on six of eight and the stricter word
# reading was taken on the other two. Owner agreed. A cap also keeps the cells independent: the
# spec's idle-floor bound tightens as rest approaches the top of its band, so a high rest would
# silently cost the hit cell. (`state.zone_of` used to reuse this as the decay tier's
# disposition/episode boundary; retired 2026-09-19, gate emotion-tier-tidy, when the per-rung
# staircase's own reading replaced it — decay does not consult REST_CAP at all now.)
REST_CAP = {
    "STIRRING":    3,   # noticing      | attraction needs an object
    "WARINESS":    5,   # worry         | nervousness is an episode
    "DISPLEASURE": 4,   # bristling     | riled is an episode
    "GOODWILL":    5,   # tenderness    | compassion arguable, could be 6
    "DEFLATION":   4,   # sorrow        | misery is an episode
    "DISTASTE":    2,   # squeamishness | revulsion is an episode
    "RECEPTIVITY": 5,   # gladness      | wonder is an episode
    "SELF-REGARD": 4,   # self-importance | vanity arguable, could be 5
    "LEVITY":      3,   # playfulness   | banter needs a second mind, so it is an episode (2026-09-11, by the design's own reading; unmeasured)
}

# hit — the START (tuned in runs). Carried from the primitive era, probe-calibrated then.
GAIN = {
    "low":      0.75,
    "typical":  1.0,
    "elevated": 1.2,
    "high":     1.3,
}

# hold — the START (tuned in runs). Carried. The spread is NARROW on purpose: retention enters the settling
# point as 1/(1-r), the hyperbolic channel, and `state.py`'s 2026-09-09 argument that this is the
# wrong place for a per-character knob stands recorded; the owner put hold in the genotype anyway
# and this spread is the concession to that argument.
PERSIST = {
    "brief":    0.85,
    "typical":  1.0,
    "long":     1.10,
    "lasting":  1.15,
}

# The retired vocabulary. Present on a sheet, it is refused by name so a book cannot run on a
# genotype the engine no longer reads (which is exactly what `92a9942` let happen to three paths).
OLD_AXES = ("threat_reactivity", "approach_drive", "affiliation_attachment",     # retired 2026-09-10
            "anger_proneness", "effortful_control", "sensitivity")                    # retired 2026-09-10

_DEFAULT_WORD = {"hit": "typical", "hold": "typical"}
_DEFAULT_REST = "quiet"


def word(value, default="typical"):
    """An authored allele value -> its bare allele word.

    `"high (anxious-leaning bond style)"` -> `"high"`. THE one reading; call this rather than
    writing `.split()[0].lower()` again.
    """
    tok = str(default if value is None else value).split()
    return tok[0].lower().rstrip("(") if tok else str(default).lower()


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ---------------------------------------------------------------------------------------------
# THE GENOTYPE — hit and hold
# ---------------------------------------------------------------------------------------------

def entry(genotype, path):
    """The per-path cell dict for `path`, or {} for a path the sheet does not mention.

    Refuses the retired shapes loudly: silently reading them as "all typical" would be the same
    failure this rebuild exists to remove.
    """
    g = genotype or {}
    if not isinstance(g, dict):
        raise RecordError("GENOTYPE_NOT_A_DICT", "genotype must be a dict, got %r" % type(g).__name__)
    stale = [k for k in g if k in OLD_AXES]
    if stale:
        raise RecordError("GENOTYPE_OLD_AXES",
                          "genotype carries the retired primitive-era axes %s; a genotype is now "
                          "one {hit, hold} cell per PATH (%s). Rewrite the sheet — "
                          "docs/guide-emotional-authoring.md — nothing translates it for you."
                          % (stale, "|".join(PATHS)))
    if path not in PATHS:
        raise RecordError("GENOTYPE_UNKNOWN_PATH", "genotype: %r is not a path" % (path,))
    cell = g.get(path, {})
    if not isinstance(cell, dict):
        raise RecordError("GENOTYPE_CELL_NOT_A_DICT",
                          "genotype[%r] must be a dict of {hit, hold}, got %r" % (path, cell))
    if "rest" in cell:
        raise RecordError("GENOTYPE_REST_MOVED",
                          "genotype[%r] carries a `rest` cell. Where a character rests is a DESIGN "
                          "question since 2026-09-10 and lives at baseline.temperament[%r].rest, "
                          "beside their voice and traits; the genotype is {hit, hold}. Move the word "
                          "— docs/authoring/BLUEPRINT-character.md Part Three." % (path, path))
    return cell


def cell_value(genotype, path, axis):
    """The raw authored value of one cell (word or number), defaulting per axis."""
    if axis not in AXES:
        raise RecordError("GENOTYPE_UNKNOWN_AXIS", "genotype axis %r is not one of %s" % (axis, AXES))
    v = entry(genotype, path).get(axis)
    return _DEFAULT_WORD[axis] if v is None else v


def hit(path, genotype):
    """The gain g on this path. A number is used as authored; an unknown word is the species
    prior (1.0) — `lint_book` reports the word, this does not."""
    v = cell_value(genotype, path, "hit")
    return float(v) if _is_number(v) else GAIN.get(word(v), 1.0)


def hold(path, genotype):
    """The half-life multiplier on this path. Number as authored; unknown word -> 1.0."""
    v = cell_value(genotype, path, "hold")
    return float(v) if _is_number(v) else PERSIST.get(word(v), 1.0)


def typical(**overrides):
    """A full genotype at the species prior, with per-path overrides: typical(WARINESS={"hit": "high"})."""
    g = {p: {"hit": "typical", "hold": "typical"} for p in PATHS}
    for p, cell in overrides.items():
        if p not in PATHS:
            raise RecordError("GENOTYPE_UNKNOWN_PATH", "typical(): %r is not a path" % (p,))
        g[p] = dict(g[p], **cell)
    return g


# ---------------------------------------------------------------------------------------------
# THE TEMPERAMENT — where they rest, authored as a word beside the voice
# ---------------------------------------------------------------------------------------------

def rest_row(temperament, path):
    """The authored `baseline.temperament[path]` row, or {} when the sheet does not carry it."""
    t = temperament or {}
    if not isinstance(t, dict):
        raise RecordError("GENOTYPE_TEMPERAMENT_NOT_A_DICT",
                          "baseline.temperament must be a dict, got %r" % type(t).__name__)
    if path not in PATHS:
        raise RecordError("GENOTYPE_UNKNOWN_PATH", "temperament: %r is not a path" % (path,))
    row = t.get(path, {})
    if not isinstance(row, dict):
        raise RecordError("GENOTYPE_REST_ROW_NOT_A_DICT",
                          "baseline.temperament[%r] must be a dict of {rest, mean}, got %r" % (path, row))
    return row


def rest_value(path, temperament):
    """The raw authored rest (word or number); absent reads as the species prior, `quiet`."""
    v = rest_row(temperament, path).get("rest")
    return _DEFAULT_REST if v is None else v


def rest_rung(path, temperament):
    """The 1-based rung index a rest WORD names, or None when the rest is an authored number."""
    v = rest_value(path, temperament)
    if _is_number(v):
        return None
    w = word(v, default=_DEFAULT_REST)
    return REST_WORDS.index(w) + 1 if w in REST_WORDS else 1


def rung_midpoint(path, rung):
    """The band midpoint of a 1-based rung on `path`, from the live ladder."""
    bands = BANDS[path]
    if not 1 <= rung <= len(bands):
        raise RecordError("GENOTYPE_REST_RUNG_OFF_LADDER",
                          "rest rung %d is off %s's %d-rung ladder" % (rung, path, len(bands)))
    lo, hi, _name = bands[rung - 1]
    return (float(lo) + float(hi)) / 2.0


def rest_mean(path, temperament):
    """The resting mean on this path: a word's rung midpoint, or the authored number."""
    v = rest_value(path, temperament)
    if _is_number(v):
        return max(0.0, min(1.0, float(v)))
    return rung_midpoint(path, rest_rung(path, temperament))


def rung_of_mean(path, mean):
    """Which 1-based rung a mean sits in — for the over-cap receipt on an authored number."""
    m = float(mean)
    bands = BANDS[path]
    for i, (lo, hi, _n) in enumerate(bands):
        if float(lo) <= m < float(hi):
            return i + 1
    return len(bands)


def over_cap(path, temperament):
    """(True, rung) when this path's rest sits above `REST_CAP` — an authored word or number."""
    r = rest_rung(path, temperament)
    if r is None:
        r = rung_of_mean(path, rest_mean(path, temperament))
    return (r > REST_CAP[path], r)


def temperament_of(temperament):
    """The full `baseline.temperament` from an authored one: every path gets {rest, mean}, the
    mean DERIVED from the rest unless the row already carries one (the arc engine writes there).
    Keys the author put beside them (a `_note`, a mean's `_authored_mean`) pass through."""
    t = temperament or {}
    out = {k: v for k, v in t.items() if k not in PATHS}
    for p in PATHS:
        row = dict(rest_row(t, p))
        row.setdefault("rest", _DEFAULT_REST)
        if "mean" not in row:
            row["mean"] = rest_mean(p, t)
        out[p] = row
    return out


def ensure_temperament(char):
    """Seed every path's resting mean from its authored rest word. Mutates; idempotent.

    Temperament is a STORED field because the arc engine writes durable diffs into it and
    `arc.erode` relaxes toward the stamped authored mean; the rest word IS that authored base.
    A row that already carries a mean keeps it — `lint_book` warns when the mean's rung and the
    rest word's rung disagree, which is how an old-scale sheet is caught.
    """
    if not isinstance(char, dict):
        raise RecordError("GENOTYPE_CHAR_NOT_A_DICT", "ensure_temperament: char must be a dict")
    base = char.setdefault("baseline", {})
    t = base.get("temperament")
    if t is None:
        t = base["temperament"] = {}
    for p in PATHS:
        rest_row(t, p)                                  # validates, before anything is written
    for p in PATHS:                                     # IN PLACE: callers hold this dict
        row = t.setdefault(p, {})
        row.setdefault("rest", _DEFAULT_REST)
        if "mean" not in row:
            row["mean"] = rest_mean(p, t)
    return char


def resting(**words):
    """A full temperament at the species prior with per-path rest words: resting(WARINESS="high")."""
    t = {p: {"rest": _DEFAULT_REST} for p in PATHS}
    for p, w in words.items():
        if p not in PATHS:
            raise RecordError("GENOTYPE_UNKNOWN_PATH", "resting(): %r is not a path" % (p,))
        t[p] = {"rest": w}
    return temperament_of(t)
