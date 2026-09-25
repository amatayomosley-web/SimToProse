"""clock.py — the DECLARED clock. One cause, FIVE consumers, and since 2026-09-10 a UNIT.
The director says WHEN each scene opens; the engine derives how much time passed. `arc.erode`,
`bond_rest.drift`, `wound.erode`, `tensions.effective` and now `state.decay` all age their tier
against this and nothing else, which is what makes "one clock, five tiers" true rather than
aspirational.

THE UNIT IS THE MINUTE (owner, 2026-09-10: "if we lock duration to the minute, and the design
says user must declare date and time and time between scenes, we have a locked design we can set
our decay to"). Until then `elapsed` was "in the director's own unit" and converted nowhere, so
emotion could not be on the clock at all — a half-life in beats is not a half-life. Now:
  * every scene cfg carries `at`: {day: N, time: "HH:MM"} in the book's own calendar — a plain
    day count, 1-based; months, seasons and festivals stay prose and unread (history.md's
    "causes, not dates" governs the PAST; this is the present's arithmetic)
  * `lasts` is optional: how long the scene runs, minutes, with "90m" / "2h" / "1d" sugar
  * elapsed between scenes is DERIVED — at(this) - (at(prev) + lasts(prev)) — and still logged
    through `declare` as the cause, so the four older consumers are unchanged; an authored
    `elapsed` on a cfg is refused as a second source of one fact
  * the scene's own reading is logged in `scene_clock` (schema v25), append-only, so the next
    scene's gap is derived from a typed prior reading and never from prose

WHY IT IS LOGGED AND NOT COMPUTED. Schema v12 exists because drift used to mutate memory at scene
start and reach no table at all: a resumed cast lost every winter that had passed. The declaration
is the CAUSE, logged once; every erosion is DERIVED from it at replay. That is what keeps the
snapshot a pure function of the log (hard rule 2) while still letting a year go by between chapters.

WHY IT IS ITS OWN FILE. `elapsed_since` was written inside `scripts/keeper.py` on 2026-09-02 and
lifted out the same day, because the second reader would have re-implemented it — the two-spellings
shape this repo paid for with `snapshots.drop_from` in the same week. `Ledger` keeps thin delegating
methods, so existing call sites are unchanged.

WHAT THIS FILE DOES NOT OWN, said so the claim above is not read wider than it is true:
`ledger.timeline_for` reads `time_declarations` directly, and correctly — it interleaves per-turn
declarations with edge deltas for `bond_rest.rehydrate`, which is a different reading with no window
logic to disagree with. It belongs to the edge join, not to the clock. What this file owns is the
SUMMED reading, and there is exactly one of those.

TWO RULES THAT LOOK LIKE DETAILS AND ARE NOT:

  * A declaration records time passed BEFORE its turn. So `elapsed_since(t)` counts from the END of beat
    `t` (and, on a log with no scene reading, sums `turn > t`, never `>=`) — a declaration at the same turn
    as the thing being aged PREDATES it and must not age it.

THE STORY DOES NOT STOP WHEN THE PAGE LOOKS AWAY (owner, 2026-09-24: "these are real people, the book is
us peeking into their world. When we look doesn't determine their state, their stat runs with or without
us looking"). Time is story time wherever it passes - between scenes, inside them, in the minutes a scene
that lulled never spent - and a scene or a chapter is only where the clock is read. `beat_end` and
`story_now` place any moment of the log on it; `elapsed_since` measures between them (gate story-clock).
  * `elapsed` must be > 0. Nothing passing is not a declaration; it is the absence of one, and
    accepting it would let a caller quietly reset an erosion clock while looking like bookkeeping.

EACH CHARACTER LIVES ON THEIR OWN TIMELINE (gate own-timelines, 2026-09-25; the owner: "a chapter can be a time
skip or a change pov"). A character ages by the time THEY lived: one item at each opening they attend, their own
time since they were last in a room (`since_presence`), and one per beat they are in the room for - never a beat
they sat out or walked out of, which reaches them at their next opening instead (`time_items`, `presences`). Their
sheet describes them where they first walk on (`first_presence`), not on the run's first page. So two scenes that
share no one may overlap in story time and run in either order; what is refused is one character in two places at
once (`window.admit`); a scene set before their own story's latest point is a WINDOW for them - they play as they were
then and nothing of it reaches their present (gate flashback-windows, `window.py`). Days may be 0 or negative - before
day 1. The world's own state - tensions, the fold of deaths and knowers - still follows the order scenes were run.
"""
import bisect as _bisect
import json as _json

from .errors import EngineError
from . import writeonce as _once
from .records import RecordError

MINUTES_PER_DAY = 24 * 60          # the older tiers read the clock in days (elapsed_days_since)


class ClockError(EngineError):
    """A time declaration the log cannot accept."""


def declare(con, run_id, turn, elapsed, source="", on_rewrite=None):
    """Record that the director says this much time passed BEFORE this turn.

    Idempotent on a byte-identical re-declaration (that is a replay, not a write) and loud on a
    differing one — the contract `append_arc_diff` holds: a correction is a NEW declaration at a
    NEW turn, never a rewritten one.

    `on_rewrite` is the caller's error type, so the ledger keeps raising `LedgerError` for a rewrite
    and this module does not have to know what its caller calls that.

    TWO ERROR POLICIES IN ONE FUNCTION, and the asymmetry is deliberate rather than sloppy: a bad
    `elapsed` raises a FIXED `RecordError` (every caller's bad-input type already), while a rewrite
    raises the CALLER'S type, because the rewrite refusal is a ledger-contract event that
    `test_ledger` holds by name. Catching and rewrapping would obscure which is which.
    """
    try:
        e = float(elapsed)
    except (TypeError, ValueError):
        raise RecordError("CLOCK_ELAPSED_NOT_NUMERIC",
                          "declare_time: elapsed must be a number, got %r" % (elapsed,))
    if e <= 0:
        raise RecordError("CLOCK_ELAPSED_NOT_POSITIVE",
                          "declare_time: elapsed must be > 0, got %r — nothing passing is not a "
                          "declaration, it is the absence of one" % (elapsed,))
    # ROUTED THROUGH `write_once` 2026-09-03. The check below was a SELECT followed by a plain
    # INSERT — the same non-atomic shape the ledger spine had, so a lost race here surfaced as a
    # raw IntegrityError on `time_declarations`' UNIQUE (run_id, turn) instead of this refusal.
    def _check():
        row = con.execute("SELECT elapsed FROM time_declarations WHERE run_id=? AND turn=?",
                          (run_id, turn)).fetchone()
        if row is None:
            return False
        if abs(float(row["elapsed"]) - e) < 1e-12:
            return True                                 # same turn, same span — a replay
        err = on_rewrite or ClockError
        raise err(
            "LEDGER_TIME_DECL_REWRITE",
            "run %r turn %d already declares elapsed %r; refusing to "
            "replace it with %r. time_declarations is append-only (CLAUDE.md hard rule 2): a "
            "correction is a NEW declaration at a NEW turn, never a rewritten one."
            % (run_id, turn, row["elapsed"], e))

    _once.write_once(con, _check, lambda: con.execute(
        "INSERT INTO time_declarations (run_id, turn, elapsed, source) VALUES (?,?,?,?)",
        (run_id, turn, e, source or "")))


def elapsed_days_since(con, run_id, turn):
    """The story MINUTES since a turn (`elapsed_since`), in DAYS — the unit the four older tiers were calibrated
    in. `bond_rest._RETENTION`, `wound`, `arc._ERODE`, `tensions` and belief decay were all tuned per
    "declared unit" when the unit was the author's own and, on the fixture books, a day; the
    minute lock (2026-09-10) would have made every one of them ~1440x too fast overnight. They keep
    their per-day rates and read the one clock through this; only emotion reads minutes directly,
    because its half-lives were authored in minutes from the start. Re-calibrating the four to
    minutes is recorded in the clock gate's OMISSIONS, not done."""
    return elapsed_since(con, run_id, turn) / float(MINUTES_PER_DAY)


def elapsed_since(con, run_id, turn):
    """The story MINUTES since a beat ended -> float (gate story-clock): from the end of beat `turn` to how far
    the story has reached (`story_now`). The rest of that scene, a lulled scene's unspent minutes, every gap and
    every later scene's beats all count - the story does not stop when no scene is looking at someone, and a
    declaration at `turn` itself predates that beat's end, the header's rule. Until this gate it summed only the
    DECLARED time after the turn, which is the gaps between scenes and nothing else.

    A run with no scene reading (a log from before schema v25, or a hand-built one) holds only its declared gaps,
    and they are summed exactly as before."""
    now, end = story_now(con, run_id), beat_end(con, run_id, turn)
    if now is not None and end is not None:
        return max(0.0, now - end)
    row = con.execute(
        "SELECT COALESCE(SUM(elapsed), 0) AS total FROM time_declarations "
        "WHERE run_id = ? AND turn > ?", (run_id, int(turn))).fetchone()
    return float(row["total"] or 0.0)


# ---------------------------------------------------------------------------
# THE UNIT, and the readings that carry it (2026-09-10)
# ---------------------------------------------------------------------------
UNIT = "minutes"

_SPAN_UNITS = {"m": 1, "min": 1, "h": 60, "hr": 60, "d": MINUTES_PER_DAY}


def span_minutes(value):
    """An authored span -> minutes. A bare number is minutes; "90m", "2h", "1.5d" are sugar.
    None -> None (the field was absent). Refuses zero, negatives and anything else."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise RecordError("CLOCK_SPAN_NOT_A_SPAN", "a span cannot be a boolean")
    if isinstance(value, (int, float)):
        m = float(value)
    else:
        txt = str(value).strip().lower()
        unit = 1.0
        for suffix in sorted(_SPAN_UNITS, key=len, reverse=True):
            if txt.endswith(suffix):
                unit = float(_SPAN_UNITS[suffix])
                txt = txt[: -len(suffix)].strip()
                break
        try:
            m = float(txt) * unit
        except ValueError:
            raise RecordError("CLOCK_SPAN_NOT_A_SPAN",
                              "span %r is not minutes, nor <n>m / <n>h / <n>d" % (value,))
    if m <= 0:
        raise RecordError("CLOCK_SPAN_NOT_POSITIVE", "a span must be > 0 minutes, got %r" % (value,))
    return m


def parse_at(at):
    """A cfg's `at` -> absolute minutes from the book's day 1, 00:00.
    Shape: {"day": N (an integer; 0 and below are the days before day 1 - gate own-timelines), "time": "HH:MM"}.
    Refuses anything else by name."""
    if not isinstance(at, dict):
        raise RecordError("CLOCK_AT_NOT_AN_OBJECT",
                          "`at` must be {day: N, time: HH:MM}, got %r" % (at,))
    day = at.get("day")
    if isinstance(day, bool) or not isinstance(day, int):
        raise RecordError("CLOCK_AT_DAY_INVALID", "`at.day` must be an integer (0 and below come before day 1), "
                                                  "got %r" % (day,))
    t = at.get("time")
    try:
        hh, mm = str(t).strip().split(":")
        hh, mm = int(hh), int(mm)
        if not (0 <= hh < 24 and 0 <= mm < 60):
            raise ValueError
    except (ValueError, AttributeError):
        raise RecordError("CLOCK_AT_TIME_INVALID", "`at.time` must be HH:MM (00:00..23:59), got %r" % (t,))
    return float((day - 1) * MINUTES_PER_DAY + hh * 60 + mm)


def format_at(minutes):
    """Absolute minutes -> "day N HH:MM", for operator prints; never reaches an actor. A minute before day 1 prints
    as day 0, day -1 and so on (divmod floors), the numbering `parse_at` reads."""
    m = int(round(float(minutes)))
    day, rem = divmod(m, MINUTES_PER_DAY)
    return "day %d %02d:%02d" % (day + 1, rem // 60, rem % 60)


def record_scene_clock(con, run_id, turn, at_minutes, lasts_minutes, beat_minutes=0.0, on_rewrite=None):
    """Log a scene's reading: when it opened, how long it ran if authored, and the minutes each
    beat was given (lasts / budget, or 0). Append-only, idempotent on a byte-identical replay,
    loud on a differing one — `declare`'s contract. `beat_minutes` is what lets the NEXT scene
    derive the unspent remainder of this one (a scene that lulls early spends less than `lasts`)
    from the log alone, since resume rehydrates affect from the last committed turn and an
    end-of-scene decay outside a turn would be lost."""
    a = float(at_minutes)
    l = None if lasts_minutes is None else float(lasts_minutes)
    bm = float(beat_minutes or 0.0)

    def _check():
        row = con.execute("SELECT at_minutes, lasts_minutes FROM scene_clock WHERE run_id=? AND turn=?",
                          (run_id, int(turn))).fetchone()
        if row is None:
            return False
        same_at = abs(float(row["at_minutes"]) - a) < 1e-9
        same_l = (row["lasts_minutes"] is None and l is None) or (
            row["lasts_minutes"] is not None and l is not None and abs(float(row["lasts_minutes"]) - l) < 1e-9)
        if same_at and same_l:
            return True
        err = on_rewrite or ClockError
        raise err("LEDGER_SCENE_CLOCK_REWRITE",
                  "run %r turn %d already opens at %s; refusing to replace it. scene_clock is "
                  "append-only (CLAUDE.md hard rule 2)." % (run_id, int(turn), format_at(row["at_minutes"])))

    _once.write_once(con, _check, lambda: con.execute(
        "INSERT INTO scene_clock (run_id, turn, at_minutes, lasts_minutes, beat_minutes) VALUES (?,?,?,?,?)",
        (run_id, int(turn), a, l, bm)))


def last_scene_clock(con, run_id, before_turn=None):
    """The most recent scene reading in this run (optionally strictly before a turn), or None."""
    if before_turn is None:
        row = con.execute("SELECT turn, at_minutes, lasts_minutes, beat_minutes FROM scene_clock WHERE run_id=? "
                          "ORDER BY turn DESC LIMIT 1", (run_id,)).fetchone()
    else:
        row = con.execute("SELECT turn, at_minutes, lasts_minutes, beat_minutes FROM scene_clock WHERE run_id=? AND turn<? "
                          "ORDER BY turn DESC LIMIT 1", (run_id, int(before_turn))).fetchone()
    if row is None:
        return None
    return {"turn": int(row["turn"]), "at": float(row["at_minutes"]),
            "lasts": None if row["lasts_minutes"] is None else float(row["lasts_minutes"]),
            "beat_minutes": float(row["beat_minutes"] or 0.0)}


def at_turn(con, run_id, turn):
    """The story time one beat ran at, in minutes -> float, or None when no scene reading covers it (gate injuries).

    The reading the beat ran under plus the minutes its scene's earlier beats were given - `presence_end`'s
    arithmetic, for one beat. A scene with no `lasts` gives its beats no minutes, so all of them read its opening."""
    seg = last_scene_clock(con, run_id, int(turn) + 1)
    if seg is None:
        return None
    return seg["at"] + (int(turn) - seg["turn"]) * seg["beat_minutes"]


def _span_beats(seg):
    """How many beats a reading's declared span holds -> int, or None when it declares no `lasts` (or no minutes)."""
    if seg["lasts"] is None or not seg["beat_minutes"]:
        return None
    return int(round(seg["lasts"] / seg["beat_minutes"]))


def _beat_share(seg, turn):
    """A beat's own minutes under the reading `seg`: its per-beat share while the declared span holds the beat."""
    if not seg["beat_minutes"]:
        return 0.0
    held = _span_beats(seg)
    return 0.0 if held is not None and int(turn) - seg["turn"] >= held else seg["beat_minutes"]


def _beat_end_at(seg, turn):
    """The minute a beat under the reading `seg` ended, never past the span the reading declared."""
    beats, held = int(turn) - seg["turn"] + 1, _span_beats(seg)
    return seg["at"] + (min(beats, held) if held is not None else beats) * seg["beat_minutes"]


def _readings(con, run_id, before_turn=None):
    """Every scene reading of a run (optionally before a turn), by turn -> [{turn, at, lasts, beat_minutes}]."""
    bound = "" if before_turn is None else " AND turn < %d" % int(before_turn)
    return [{"turn": int(r[0]), "at": float(r[1]), "lasts": None if r[2] is None else float(r[2]),
             "beat_minutes": float(r[3] or 0.0)} for r in con.execute(
        "SELECT turn, at_minutes, lasts_minutes, beat_minutes FROM scene_clock WHERE run_id = ?" + bound
        + " ORDER BY turn", (run_id,))]


def beat_minutes(con, run_id, turn):
    """The story minutes a beat itself took -> float (gate slow-tiers-run): its reading's per-beat share while the
    reading's declared span holds it, and nothing past that or with no reading. A scene's beats never outrun their
    budget; a chair session opens with a budget of one, so a second turn under the same `--at` adds no time."""
    seg = last_scene_clock(con, run_id, int(turn) + 1)
    return 0.0 if seg is None else _beat_share(seg, turn)


def beat_end(con, run_id, turn):
    """The story minute a beat ENDED at -> float, or None when no scene reading covers it (gate story-clock):
    `at_turn`'s arithmetic, one beat on - the reading it ran under plus its minutes for every beat up to this one,
    never past the span the reading declared (gate slow-tiers-run)."""
    seg = last_scene_clock(con, run_id, int(turn) + 1)
    return None if seg is None else _beat_end_at(seg, turn)


def time_items(con, run_id, char_id, before_turn=None, view=None):
    """Every stretch of story time ONE CHARACTER lived -> [(turn, slot, minutes)], ascending (gate own-timelines).

    At each opening they are in the room for, after an earlier presence: their own time since (`since_presence` - the
    arithmetic the live opening applies, so the two cannot drift), at the reading's turn, slot 2. At every beat they
    were in the room for (`presences`): the beat's own minutes, slot 3 (`beat_minutes`). Nothing before their first
    appearance - the sheet is who they are then - and nothing for a beat they sat out or had walked out of: that time
    reaches them at their next opening, in one item. A gap declared at a turn with no reading (a log from before
    schema v25) is that turn's opening for everyone, as it always was. `before_turn` keeps earlier turns only. Until
    this gate every character took every stretch of the run (gate slow-tiers-run), in the scene or not. `view`: which
    of their scenes count (gate flashback-windows - `window.view`; None is their present (`window.current`)):
    their present leaves their windows out, and a window sees their main line before its time and itself."""
    reads = _readings(con, run_id, before_turn)
    v, win = _view(con, run_id, char_id, view)
    starts, out, prev = [r["turn"] for r in reads], [], None
    for t in presences(con, run_id, char_id, before_turn):
        if not win.keeps(v, t):
            continue
        k = _bisect.bisect_right(starts, t) - 1
        if k >= 0:
            if t == reads[k]["turn"] and prev is not None:          # they are in this opening, and were somewhere before
                own = since_presence(_ended(con, run_id, prev), reads[k]["at"])
                if own > 0:
                    out.append((t, 2, own))
            m = _beat_share(reads[k], t)
            if m:
                out.append((t, 3, m))
        prev = t
    opened = set(starts)
    bound = "" if before_turn is None else " AND turn < %d" % int(before_turn)
    out += [(int(t), 2, float(e)) for t, e in con.execute(
        "SELECT turn, elapsed FROM time_declarations WHERE run_id = ?" + bound, (run_id,)) if int(t) not in opened]
    return sorted(out)


def story_now(con, run_id):
    """How far the story has reached -> minutes, or None for a run with no scene reading (gate story-clock): the
    furthest point any scene or chair session reached - a reading's opening, or the end of the last beat committed
    under it. Since gate own-timelines scenes that share no one may run out of story order, so the scene run last is
    not always the furthest; until then this read the last committed beat and the latest reading only."""
    reads = _readings(con, run_id)
    if not reads:
        return None
    starts, last = [r["turn"] for r in reads], {}
    for (t,) in con.execute("SELECT DISTINCT turn FROM turns WHERE run_id = ?", (run_id,)):
        k = _bisect.bisect_right(starts, int(t)) - 1
        if k >= 0:
            last[k] = max(last.get(k, int(t)), int(t))
    return max([r["at"] for r in reads] + [_beat_end_at(reads[k], t) for k, t in last.items()])


def days_since(con, run_id, char_id, turn, now_turn):
    """Story DAYS from the end of beat `turn` to the start of beat `now_turn` -> float (gate memory-fades): a
    memory's own time since the beat that formed or last recalled it; `turn` None is where `char_id`'s own story
    began (`first_presence`, gate own-timelines - it was the run's first page), for a memory their sheet carries.
    0.0 when either end has no reading - no clock, no time - and for a sheet memory in their first beat."""
    now = at_turn(con, run_id, now_turn)
    then = first_presence(con, run_id, char_id) if turn is None else beat_end(con, run_id, turn)
    return 0.0 if now is None or then is None else max(0.0, now - then) / float(MINUTES_PER_DAY)


def first_presence(con, run_id, char_id, view=None):
    """Where one character's own story began -> minutes, or None before their first beat (gate own-timelines): the
    opening of the reading their first beat in the room ran under - the moment their sheet describes them. It was
    page one, the run's first opening, for everyone; a character who walks on in a later scene is met as their
    sheet says, then, and their sheet's memories and injuries are dated from there. Their first scene of the view -
    their main line's first, a window never coming before it (gate flashback-windows)."""
    v, win = _view(con, run_id, char_id, view)
    here = [t for t in presences(con, run_id, char_id) if win.keeps(v, t)]
    seg = last_scene_clock(con, run_id, here[0] + 1) if here else None
    return None if seg is None else seg["at"]


def unspent_before(con, run_id, start_turn):
    """Minutes the PREVIOUS scene declared it lasted but did not spend beat by beat (it lulled or
    emptied before its budget). Derived from the log: beats committed = this start turn minus the
    previous scene's start turn; spent = beats * beat_minutes. Emotion decay owes this at the next
    scene's opening so a scene's decay totals exactly what the author said it lasted. 0 when the
    previous scene had no `lasts` or spent it all; None for the first scene."""
    prev = last_scene_clock(con, run_id, start_turn)
    if prev is None or prev["lasts"] is None:
        return None if prev is None else 0.0
    beats = max(0, int(start_turn) - prev["turn"])
    return max(0.0, prev["lasts"] - beats * prev["beat_minutes"])


def _scene_casts(con, run_id):
    """[(start_turn, end_turn, {cast ids})] for each recorded scene of a run, from its pinned cfg - what a beat
    that records no room falls back on (`last_present`). A scene whose cfg the log does not hold is left out."""
    out = []
    for s, e, fp in con.execute("SELECT start_turn, end_turn, cfg_fingerprint FROM scenes WHERE run_id = ?", (run_id,)):
        row = con.execute("SELECT body FROM scene_cfgs WHERE fingerprint = ?", (fp,)).fetchone() if fp else None
        if row is not None:
            cast = _json.loads(row[0]).get("cast") or []
            out.append((int(s), int(e), {str(c.get("id")) for c in cast if isinstance(c, dict)}))
    return out


def presences(con, run_id, char_id, before_turn=None):
    """Every turn this character was bodily in the room, ascending -> [int] (gate own-timelines; the rule gate
    absent-age wrote for `last_present`, over the whole log). ONE SOURCE for who was there, live and in every fold.

    The speaker (`turns.actor`), or one of the room a scene beat's manifest records under `decay.here` - written
    every beat since gate non-speaker-decay (2026-09-22). A beat logged before that records no room: the log
    cannot tell who listened from who had walked out, so its scene's whole cast counts, which is what every
    opening before gate absent-age assumed, and what keeps those runs replaying as they ran. A chair turn sits in
    no scene, so only its speaker was there."""
    bound = "" if before_turn is None else " AND t.turn < %d" % int(before_turn)
    casts, out = None, []
    for t, actor, man in con.execute(
            "SELECT t.turn, t.actor, m.manifest FROM turns t LEFT JOIN decision_manifests m ON m.run_id = t.run_id "
            "AND m.turn = t.turn WHERE t.run_id = ?" + bound + " ORDER BY t.turn", (run_id,)):
        t = int(t)
        if out and out[-1] == t:
            continue
        room = ((_json.loads(man) if man else {}).get("decay") or {}).get("here")
        if actor != char_id and room is None:
            if casts is None:
                casts = _scene_casts(con, run_id)
            room = [char_id] if any(s <= t <= e and char_id in cast for s, e, cast in casts) else []
        if actor == char_id or char_id in room:
            out.append(t)
    return out


def last_present(con, run_id, char_id, before_turn, view=None):
    """The last turn before `before_turn` this character was bodily in the room -> int, or None (gate absent-age):
    the last of their `presences` the view keeps (gate flashback-windows: a window is not where they last were)."""
    v, win = _view(con, run_id, char_id, view)
    here = [t for t in presences(con, run_id, char_id, before_turn) if win.keeps(v, t)]
    return here[-1] if here else None


def _view(con, run_id, char_id, view):
    """(the view a reader uses, the window module): `window` reads this module, so it is imported here, late."""
    from . import window as _window
    return _window.of(con, run_id, char_id, view), _window


def _ended(con, run_id, turn):
    """{"end", "owed"} for a character whose last beat in the room was `turn`, or None when no reading covers it:
    the declared end of the reading it ran under (opening + lasts), and the minutes of it they did not spend in the
    room - `lasts` less the beats up to and including theirs."""
    seg = last_scene_clock(con, run_id, int(turn) + 1)
    if seg is None:
        return None
    beats = int(turn) + 1 - seg["turn"]
    owed = max(0.0, seg["lasts"] - beats * seg["beat_minutes"]) if seg["lasts"] is not None else 0.0
    return {"end": seg["at"] + (seg["lasts"] or 0.0), "owed": owed}


def presence_end(con, run_id, char_id, before_turn, view=None):
    """Where one character's OWN time last stood before a turn -> {"end", "owed"} or None (gate gap-day-and-night).

    Their last beat in the room (`last_present`) and the scene reading that beat ran under: `end` is its declared
    end (opening + lasts), `owed` the minutes it declared that they did not spend in the room - `lasts` less the
    beats up to and including their last one. Until gate absent-age `owed` counted every beat of the scene, so
    the minutes after a walk-out were no one's; now they are the walk-out's, as the rest of their absence is.
    None: never present before this turn, or no reading to measure from - the sheet is their state. `view`: gate
    flashback-windows (`last_present`)."""
    last = last_present(con, run_id, char_id, before_turn, view)
    return None if last is None else _ended(con, run_id, last)


def since_presence(ended, at):
    """A character's own time between their last beat in a room and an opening at `at`, in minutes (gate
    own-timelines): `ended` is `presence_end`'s {"end", "owed"}. THE ONE ARITHMETIC for the live opening
    (`passage.own_minutes`) and the fold's opening item (`time_items`), so the two cannot drift."""
    return (float(at) - ended["end"]) + ended["owed"]


def own_time(con, run_id, char_id, start_turn, at_minutes):
    """One character's own time before an opening at `start_turn` -> minutes, or None at their first appearance."""
    ended = presence_end(con, run_id, char_id, start_turn)
    return None if ended is None else since_presence(ended, at_minutes)


def gap_before(con, run_id, at_minutes, before_turn=None):
    """Minutes between the END of the scene run last and this opening -> float, or None for the run's first. SIGNED
    since gate own-timelines: negative when this scene is set earlier, which is legal when it shares no one with
    that scene (`window.admit` refuses one character in two places; one set in a character's past is a window for
    them, gate flashback-windows). It is what the
    operator line prints and, when positive, what the log declares; no one ages by it - each character ages by
    their own time (`since_presence`). Until that gate it refused any opening before the last scene's end."""
    prev = last_scene_clock(con, run_id, before_turn)
    if prev is None:
        return None
    return float(at_minutes) - (prev["at"] + (prev["lasts"] or 0.0))
