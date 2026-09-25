"""window.py — a scene set in a character's past is a WINDOW for them (gate flashback-windows, 2026-09-25).

THE OWNER'S RULE (plan step 4, approved 2026-09-25), from the worry that set it: "we've followed X for 43 chapters -
why suddenly does he have these effects?" A scene set earlier than the point a character's own story has reached
plays them from their state AS OF THEN - bonds, scars, mood, condition, injuries, the memories formed by then, what
their feelings were about - and NOTHING it produces reaches their present. For everyone else in it the scene is
their own story going on: a character new to the story starts their timeline in it, and one whose story has not
reached that time carries it forward. A notice before the scene says whom it is a window for (`admit`), and a report
after it says what it would have added (`report`).

DERIVED, NEVER STORED. A character's scenes are classified in the order they ran (`_groups`): a scene is a window
for them when it opens before the latest point their MAIN LINE - their scenes that were not windows - had reached.
A VIEW of their log (`view`) then says which of their rows a reader may see: in their present, every row but their
windows'; inside a window at time T, their main-line rows from before T and the window's own so far. A window
reaches no other window of theirs, so the same scene plays the same whatever order the author ran them in (review
I3). Every reader of one character's history takes a view - by default their PRESENT (`current`: every row but
their windows'). The scene driver hands each actor the view of the scene they are in (a window's, for whom it is
one), the drivers' resume the view of the scene about to open, and the mood replay the view at each scene's start.
A default cannot be read off the log inside a window: before its first beat commits, nothing in the log says who
is in it.

BEFORE A CHARACTER'S FIRST SCENE (the owner, 2026-09-25: "Play the character sheet, if there is a large gap in time
advise generating a character sheet"): the engine holds nothing of them before the moment their sheet describes, so a
window set earlier plays them from the sheet as it stands, and the notice says how much later the sheet describes
them, advising a sheet for them as they were then past `SHEET_ADVICE_DAYS` (`sheet_gap`). The sheet's own rows - the
rests and holds seeded from it - belong to every view (`bond_rest.rows_for`), or such a window would play their
friendships as a stranger's.

WHAT IT DOES NOT COVER. The world's own state - tensions, the fold of deaths and knowers, the keeper's canon - still
follows the order scenes were run.

Deterministic, stdlib + engine imports only, no LLM, no randomness.
"""
from __future__ import annotations

__layer__ = "engine"

import bisect as _bisect
import json as _json
from collections import namedtuple

from . import clock as _clock
from .records import RecordError

# excluded: ((first_turn, last_turn), ...) - the character's window scenes, other than one they stand in
# cut:      None in their present; in a window, the first turn of their main line after the window's time
# since:    in a window, its own first turn - its rows from there on are its own
# at:       the story minute the view stands at (the opening's), for the notice
View = namedtuple("View", "excluded cut since at")
ALL = View((), None, None, None)       # every row: what a writer checks against, never what a reader sees
# How long before a character's first scene a window may be set before the notice advises a sheet for them as they
# were then [START - the owner named no line; FALSIFIER: an author advised to write a new sheet for a flashback a
# month back finds the old one still describes that person, or one not advised finds it plainly does not].
SHEET_ADVICE_DAYS = 30.0


def _groups(con, run_id, char_id, reads, before_turn):
    """[(k, first_turn, last_turn, main, end)] - each reading of `reads` one character was in the room under, in run
    order, before `before_turn`: its turns, whether it was their main line, and where their time in it ended - its
    declared end if they were in the room at its last beat (a lull ends the talk, not their being there), else the
    end of their last beat in it (they walked out). Main while it opens at or after their main line's latest end."""
    starts, last_of, mine = [r["turn"] for r in reads], {}, {}
    for (t,) in con.execute("SELECT DISTINCT turn FROM turns WHERE run_id = ? AND turn < ?", (run_id, int(before_turn))):
        k = _bisect.bisect_right(starts, int(t)) - 1
        if k >= 0:
            last_of[k] = max(last_of.get(k, int(t)), int(t))
    for t in _clock.presences(con, run_id, char_id, before_turn):
        k = _bisect.bisect_right(starts, t) - 1
        if k >= 0:
            mine[k] = max(mine.get(k, t), t)
    out, reached = [], None
    for k in sorted(mine):
        seg = reads[k]
        end = seg["at"] + (seg["lasts"] or 0.0) if mine[k] == last_of[k] else _clock._beat_end_at(seg, mine[k])
        main = reached is None or seg["at"] >= reached
        if main:
            reached = end if reached is None else max(reached, end)
        out.append((k, seg["turn"], last_of[k], main, end))
    return out


def view(con, run_id, char_id, reading=None, at=None, start=None):
    """The view of one character's log at a moment -> View (see the header). The moment is a logged reading - the
    one at turn `reading`, else the story's latest - or an opening not yet logged, `at` (minutes) at turn `start`."""
    reads = _clock._readings(con, run_id)
    if at is None:
        ks = [k for k, r in enumerate(reads) if reading is None or r["turn"] == int(reading)]
        if not ks:
            return View((), None, None, None)
        at, start = reads[ks[-1]]["at"], reads[ks[-1]]["turn"]
    before = [r for r in reads if r["turn"] < int(start)]
    groups = _groups(con, run_id, char_id, before, start)
    excluded = tuple((first, last) for _k, first, last, main, _e in groups if not main)
    reached = max((e for _k, _f, _l, main, e in groups if main), default=None)
    if reached is None or float(at) >= reached:
        return View(excluded, None, None, float(at))
    mains = [(before[k]["at"], first) for k, first, _l, main, _e in groups if main]
    cut = next((first for a, first in mains if a > float(at)), mains[-1][1])
    return View(excluded, cut, int(start), float(at))


def is_window(v):
    """True when the view stands in a window (a scene set in the character's past), not in their present."""
    return v.cut is not None


def current(con, run_id, char_id):
    """A character's PRESENT -> View: every row of theirs but their windows'. What a reader sees handed no view. A
    store with no scene clock at all (a module's own test store) holds no window: every row."""
    if con.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'scene_clock'").fetchone() is None:
        return ALL
    groups = _groups(con, run_id, char_id, _clock._readings(con, run_id), 10 ** 12)
    return View(tuple((first, last) for _k, first, last, main, _e in groups if not main), None, None, None)


def require_present(con, run_id, char_id):
    """Refuse a chair session with no clock of its own while the story's latest scene is a window for its character
    (CLOCK_CHAIR_IN_A_WINDOW) -> None. Its turns would fall under that scene's reading and silently join the window,
    where nothing reaches their present; with an `--at` it opens in their present, or is refused by name."""
    reads = _clock._readings(con, run_id)
    groups = _groups(con, run_id, char_id, reads, 10 ** 12)
    if groups and not groups[-1][3] and groups[-1][0] == len(reads) - 1:
        raise RecordError("CLOCK_CHAIR_IN_A_WINDOW",
                          "the story's latest scene is set in %s's past, a window for them: give the chair an --at "
                          "so it knows when it is" % char_id)


def keeps(v, turn):
    """Does a row at `turn` belong to what this view may see?"""
    t = int(turn)
    if any(lo <= t <= hi for lo, hi in v.excluded):
        return False
    return v.cut is None or t < v.cut or t >= v.since


def clause(v, col="turn"):
    """`keeps` as SQL, to append to a WHERE: '' for a present with no window behind it."""
    parts = ["NOT (%s BETWEEN %d AND %d)" % (col, lo, hi) for lo, hi in v.excluded]
    if v.cut is not None:
        parts.append("(%s < %d OR %s >= %d)" % (col, v.cut, col, v.since))
    return "".join(" AND " + p for p in parts)


def of(con, run_id, char_id, v=None):
    """The view a reader uses: the one handed in, else the character's present (`current`)."""
    return v if v is not None else current(con, run_id, char_id)


def admit(con, run_id, cast, at_minutes, lasts_minutes, start, windows=False):
    """Refuse an opening that cannot be, before anything is logged -> {id: View} the cast members it is a WINDOW for.

    CLOCK_TWO_PLACES_AT_ONCE: its span (at to at + lasts) overlaps one a cast member was in - any scene of theirs,
    windows included; spans that only touch are not two places. Set before the latest point their main line has
    reached, the opening is a window for them (a scene, `windows`), else CLOCK_RUNS_BACKWARDS (the chair, which
    stays in the present). A window before their first scene plays them from their sheet (`sheet_gap`; gate
    window-before-first-scene - it was refused). Until gate flashback-windows the clock's own refusal (gate
    own-timelines) refused every opening in a character's past."""
    a = float(at_minutes)
    b = a + float(lasts_minutes or 0.0)
    reads = [r for r in _clock._readings(con, run_id) if r["turn"] < int(start)]
    out = {}
    for c in cast:
        groups = _groups(con, run_id, c, reads, start)
        for k, _f, _l, _m, e in groups:
            if reads[k]["at"] < b and a < e:
                raise RecordError("CLOCK_TWO_PLACES_AT_ONCE",
                                  "%s is in a scene from %s to %s; this one, %s to %s, would put them in two places "
                                  "at once" % (c, _clock.format_at(reads[k]["at"]), _clock.format_at(e),
                                               _clock.format_at(a), _clock.format_at(b)))
        v = view(con, run_id, c, at=a, start=start)
        if not is_window(v):
            continue
        reached = max(e for _k, _f, _l, main, e in groups if main)
        if not windows:
            raise RecordError("CLOCK_RUNS_BACKWARDS",
                              "%s's own story has reached %s and this opens at %s, before it: the chair stays in the "
                              "present - open it at %s or later (a scene may be set in their past, as a window)"
                              % (c, _clock.format_at(reached), _clock.format_at(a), _clock.format_at(reached)))
        out[c] = v
    return out


def sheet_gap(con, run_id, char_id, at_minutes):
    """How long before a character's first scene a window at `at_minutes` is set -> minutes, or None when it is not
    before it (gate window-before-first-scene): they play from their sheet, which describes them that much later."""
    # EVERY ROW: a character's first scene in run order is always their main line's first (nothing is a window before
    # it), so the question reads no view of their history - asking their present would read one needlessly
    first = _clock.first_presence(con, run_id, char_id, ALL)
    return None if first is None or float(at_minutes) >= first else first - float(at_minutes)


def span_words(minutes):
    """A span for the operator's line -> "3 hours", "2 months", "11 years" (rounded to its largest unit)."""
    m = float(minutes)
    for unit, size in (("year", 365.25 * 1440), ("month", 30.4375 * 1440), ("day", 1440.0), ("hour", 60.0)):
        if m >= size:
            n = int(round(m / size))
            return "%d %s%s" % (n, unit, "" if n == 1 else "s")
    n = int(round(m))
    return "%d minute%s" % (n, "" if n == 1 else "s")


def report(con, run_id, char_id, first, last):
    """What a window would have added to one character, had it been their story -> [phrase], words only (the
    window's own rows, turns `first`..`last`, that their present never reads): new scars, scars that moved, bonds,
    feelings toward people, resting moods, memories, hurts. [] when it left nothing lasting."""
    span = (run_id, char_id, int(first), int(last))
    out = ["a new scar: %s, on %s" % (c, p.lower()) for c, p in con.execute(
        "SELECT concept, path FROM wound_minted WHERE run_id = ? AND char_id = ? AND turn BETWEEN ? AND ? "
        "ORDER BY turn, mint_id", span)]
    out += ["the %s scar %s" % (w.split("@")[0], "deepened" if d > 0 else "eased") for w, d in con.execute(
        "SELECT wound_id, SUM(delta) FROM wound_deltas WHERE run_id = ? AND char_id = ? AND turn BETWEEN ? AND ? "
        "GROUP BY wound_id ORDER BY wound_id", span) if d]
    out += ["%s toward %s %s" % (ax, tg, "rose" if d > 0 else "fell") for tg, ax, d in con.execute(
        "SELECT target, axis, SUM(delta) FROM relationship_deltas WHERE run_id = ? AND perceiver = ? AND turn BETWEEN "
        "? AND ? AND ord = 'first' GROUP BY target, axis ORDER BY target, axis", span) if d]
    out += ["%s toward %s %s" % (p.lower(), tg, "grew" if d > 0 else "faded") for tg, p, d in con.execute(
        "SELECT target, primary_, SUM(delta) FROM toward_deltas WHERE run_id = ? AND perceiver = ? AND turn BETWEEN "
        "? AND ? GROUP BY target, primary_ ORDER BY target, primary_", span) if d]
    moved = {}
    for (diff,) in con.execute("SELECT diff FROM arc_diffs WHERE run_id = ? AND char_id = ? AND turn BETWEEN ? AND ?",
                               span):
        for p, d in ((_json.loads(diff) or {}).get("temperament") or {}).items():
            moved[p] = moved.get(p, 0.0) + float(d if not isinstance(d, dict) else d.get("mean", 0.0))
    out += ["their resting %s %s" % (p.lower(), "rose" if d > 0 else "fell") for p, d in sorted(moved.items()) if d]
    out += ["a memory: %s" % str(_json.loads(b).get("claim") or "").strip()[:80] for (b,) in con.execute(
        "SELECT belief FROM acquisitions WHERE run_id = ? AND char_id = ? AND turn BETWEEN ? AND ? "
        "ORDER BY turn, acquisition_id", span)]
    from . import injuries as _injuries
    out += ["hurt: %s (%s)" % (r["what"], r["severity"]) for r in _injuries.run_rows(con, run_id, int(last) + 1)
            if r["who"] == char_id and int(first) <= r["turn"] <= int(last)]
    return out
