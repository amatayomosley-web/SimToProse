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

  * A declaration records time passed BEFORE its turn. So `elapsed_since(t)` sums `turn > t`, never
    `>=` — a declaration at the same turn as the thing being aged PREDATES it and must not age it.
  * `elapsed` must be > 0. Nothing passing is not a declaration; it is the absence of one, and
    accepting it would let a caller quietly reset an erosion clock while looking like bookkeeping.
"""
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
    """The declared MINUTES since a turn, in DAYS — the unit the four older tiers were calibrated
    in. `bond_rest._RETENTION`, `wound`, `arc._ERODE`, `tensions` and belief decay were all tuned per
    "declared unit" when the unit was the author's own and, on the fixture books, a day; the
    minute lock (2026-09-10) would have made every one of them ~1440x too fast overnight. They keep
    their per-day rates and read the one clock through this; only emotion reads minutes directly,
    because its half-lives were authored in minutes from the start. Re-calibrating the four to
    minutes is recorded in the clock gate's OMISSIONS, not done."""
    return elapsed_since(con, run_id, turn) / float(MINUTES_PER_DAY)


def elapsed_since(con, run_id, turn):
    """Declared MINUTES between a turn and the head -> float. `turn >`, for the reason in the header."""
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
    Shape: {"day": N (int >= 1), "time": "HH:MM"}. Refuses anything else by name."""
    if not isinstance(at, dict):
        raise RecordError("CLOCK_AT_NOT_AN_OBJECT",
                          "`at` must be {day: N, time: HH:MM}, got %r" % (at,))
    day = at.get("day")
    if isinstance(day, bool) or not isinstance(day, int) or day < 1:
        raise RecordError("CLOCK_AT_DAY_INVALID", "`at.day` must be an integer >= 1, got %r" % (day,))
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
    """Absolute minutes -> "day N HH:MM", for operator prints; never reaches an actor."""
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


def opening(con, run_id):
    """When the run's first scene opened, in minutes -> float, or None: page one, the moment a sheet describes."""
    row = con.execute("SELECT at_minutes FROM scene_clock WHERE run_id=? ORDER BY turn LIMIT 1", (run_id,)).fetchone()
    return None if row is None else float(row["at_minutes"])


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


def presence_end(con, run_id, char_id, before_turn):
    """Where one character's OWN time last stood before a turn -> {"end", "owed"} or None (gate gap-day-and-night).

    Their last beat present in this run - the speaker (`turns.actor`), or one of the room a scene beat's manifest
    records under `decay.here` - and the scene reading that beat ran under: `end` is its declared end (opening +
    lasts), `owed` what it declared and its beats did not spend (`unspent_before`'s arithmetic, for that reading).
    None: never present before this turn, or no reading to measure from - the sheet is their state."""
    last = None
    for t, actor, man in con.execute(
            "SELECT t.turn, t.actor, m.manifest FROM turns t LEFT JOIN decision_manifests m ON m.run_id = t.run_id "
            "AND m.turn = t.turn WHERE t.run_id = ? AND t.turn < ? ORDER BY t.turn DESC", (run_id, int(before_turn))):
        here = ((_json.loads(man) if man else {}).get("decay") or {}).get("here") or ()
        if actor == char_id or char_id in here:
            last = int(t)
            break
    seg = None if last is None else last_scene_clock(con, run_id, last + 1)
    if seg is None:
        return None
    nxt = con.execute("SELECT MIN(turn) FROM scene_clock WHERE run_id = ? AND turn > ? AND turn < ?",
                      (run_id, seg["turn"], int(before_turn))).fetchone()[0]
    beats = (int(nxt) if nxt is not None else int(before_turn)) - seg["turn"]
    owed = max(0.0, seg["lasts"] - beats * seg["beat_minutes"]) if seg["lasts"] is not None else 0.0
    return {"end": seg["at"] + (seg["lasts"] or 0.0), "owed": owed}


def gap_before(con, run_id, at_minutes, before_turn=None):
    """Minutes between the previous scene's END and this scene's opening, or None for the first
    scene of a run. Refuses a scene that opens before the previous one ended — the clock does not
    run backwards, and a cfg that says otherwise is the author's to fix."""
    prev = last_scene_clock(con, run_id, before_turn)
    if prev is None:
        return None
    end = prev["at"] + (prev["lasts"] or 0.0)
    gap = float(at_minutes) - end
    if gap < 0:
        raise RecordError("CLOCK_RUNS_BACKWARDS",
                          "this scene opens at %s but the previous one ended at %s; a scene cannot open "
                          "before the last one ended" % (format_at(at_minutes), format_at(end)))
    return gap
