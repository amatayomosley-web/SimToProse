"""passage.py — one clock, read the same way by both drivers.

THE CHAIR APPLIED NONE OF IT (cairn 0066; case the-chair-keeps-its-own-time). `scripts/scene.py`
opened every scene by logging the reading, deriving the gap since the last scene ended, and
applying it — drift toward each edge's rest, wound erosion, arc erosion, the toward vectors, and
(since 2026-09-10) emotion decay itself, all on the one declared unit `clock.py`'s header calls
"one cause, five tiers." `scripts/direct.py` sat beside the same chronicle with none of it wired:
its own comment named the asymmetry before any of this moved ("This driver declares no elapsed of
its own") and threaded only a flat `--minutes-per-turn` into emotion decay, so a chair session run
after three scenes advanced no edge, no wound, no arc and no attitude however long it said the gap
was. Two drivers writing the same chronicle held two clocks, and only one of them ticked.

THE FIX IS THE SHAPE THIS REPO ALREADY USES FOR THE FLOOR (`floor.py`, 2026-09-03): the block was a
driver COMPUTING VALUES — the shape CLAUDE.md's Modes section forbids ("a driver never computes a
value; the engine computes, the driver dispatches") — sitting inline in `scripts/scene.py` where
only that one driver could reach it. It is lifted here VERBATIM: same order, same units (minutes
into decay; DAYS into the older tiers, via `clock.MINUTES_PER_DAY` — that conversion is
unchanged, not renegotiated, by this move), same rows written. `scripts/scene.py` calls it where
the block used to live; `scripts/direct.py` calls it wherever the chair is opened with `--at`, and
skips it otherwise (a chair run with no `--at` still says so on stdout, and still declares no clock
of its own — a beat has no duration, per emotion-arithmetic.md section 4, and that omission is
deliberate, recorded in the gate rather than resolved here).

WHAT THIS MODULE DOES NOT DO, so the claim above is not read wider than it is true: it does not
print. The one line `scene.py` printed at the end of the block ("N minutes since the last scene
ended...") is DISPLAY, not computation, and stays with whoever is dispatching — both drivers word
it the same way from this function's own return value, so the wording cannot drift between them the
way the clock itself had. It does not change what a scene or a chair session IS: no per-turn clock
lives here (a beat still has no duration; `--minutes-per-turn` is still the chair's own knob,
unrelated to this), and the older tiers still read DAYS while emotion reads MINUTES, exactly
as clock.py's header describes — this gate moves the CALL, not the law.

UNITS, RE-READ 2026-09-19 (gate `attitude-staircase`). `toward.erode` now takes MINUTES, because
the attitude tier decays on the same per-rung staircase as the mood at its own slower scale
(`toward._attitude_half_life`) and a staircase cannot be stepped on two clocks. THREE tiers still
take the same declaration in days — `bond_rest.drift`, `wound.erode`, `arc.erode` — each with its
own law and its own doc, one tier per gate. The declaration itself is unchanged: minutes, once.

CALLER CONTRACT. `open_scene(led, run_id, start_turn, at_minutes, lasts_minutes, budget, chars,
names=None, flow=False, body=False)` (`flow`: the book runs `condition_flow` - the owed minutes cost energy and
the gap restores it, `condition.opening`; gate condition-flow. `body`: the owed minutes are weighed against
each character's strength, `body.capacity`; gate body-exertion):
  led, run_id      the open chronicle (an `src.engine.ledger.Ledger` and its run id)
  start_turn       the turn this opening is declared AT (a scene's first beat; a chair's next turn
                    number) — declarations record time passed BEFORE this turn (clock.py)
  at_minutes       absolute minutes from the book's day 1 00:00 (`clock.parse_at`'s return)
  lasts_minutes    how long this opening is authored to run, in minutes, or None — undeclared
                    duration means no decay is owed FROM this opening at the next one
  budget           how many beats/turns this opening gets; `lasts_minutes / budget` is the per-beat
                    share `unspent_before` needs to find what a lulled opening owed. The chair has
                    no fixed budget (a REPL, or one beat under --prompt-only/--turn-json), so it
                    passes 1 — per_beat collapses to `lasts_minutes` itself, the same arithmetic a
                    single-beat scene already gets.
  chars            {id: char dict} — every character this opening's clock reaches. Mutated in place
                    exactly as the driver used to: `current.affect`, `current.relationships`
                    (drift), `baseline.wounds` (erosion, `_authored_intensity` stamped once),
                    `baseline.temperament` (arc erosion), `current.toward` (erosion). The caller
                    owns anything ELSE keyed to a character (a driver's own cache of `affect` beside
                    the sheet, for instance) and must refresh it from the sheet afterward — this
                    function does not know such a cache exists.
  names            the opening's own label (a scene's `cfg.get("name")`), reused verbatim as
                    `declare_time`'s provenance string, exactly as `scripts/scene.py` always passed
                    it. Optional because the chair has no scene cfg to draw one from: a chair-
                    declared gap carries no label, same as an unnamed scene always has.
  -> {"elapsed": minutes or None, "owed": minutes, "per_beat": minutes, "relaxed": [ids], "own": {id: minutes}}
     `elapsed` is the signed gap since the scene run last ended (`clock.gap_before`), None for the
     run's first opening - what the operator line prints, and what the log declares when positive;
     `owed` is the previous opening's unspent `lasts` (0.0 when it spent it all, or declared none);
     `own` is how long each character had been out of the room - the minutes their mood and slow
     tiers aged (`own_minutes`; a first appearance is absent from it, and so is everyone at a run's
     first opening); `relaxed` is every id whose slow tiers this call aged (sorted).

Raises `RecordError("CLOCK_TWO_PLACES_AT_ONCE" | ...)` through `window.admit`, before anything is
logged, when the opening puts one of its cast in two places at once (gate own-timelines) — in either
driver. Scenes that share no one may overlap in story time and run in either order. `windows` (the scene
driver): an opening set before a character's own story's latest point is a WINDOW for them (gate
flashback-windows) and the result's `windows` names them {id: window.View}; the chair (no `windows`) is
refused one (CLOCK_RUNS_BACKWARDS).

Deterministic, stdlib + engine imports only, no LLM, no randomness. Fails loud through the modules
it calls.
"""
from __future__ import annotations

__layer__ = "engine"

from . import arc
from . import bond_rest
from . import body as _body
from . import clock
from . import condition as _condition
from . import injuries as _injuries
from . import connection
from . import toward
from . import window as _window
from . import wound
from .state import build_profile, decay
from .records import PATHS, RecordError
import copy as _copy
import json as _json


def open_scene(led, run_id, start_turn, at_minutes, lasts_minutes, budget, chars, names=None, flow=False, body=False,
               stated=None, injuries=False, windows=False):
    # NO ONE IN TWO PLACES (gate own-timelines) - refused before the reading is logged, so a refused opening leaves no
    # reading behind to block the corrected one at the same turn. Set in someone's past, it is a WINDOW for them
    # (gate flashback-windows): the drivers built them as they were then, and nothing it does reaches their present.
    wins = _window.admit(led.con, run_id, list(chars), at_minutes, lasts_minutes, start_turn, windows=windows)
    per_beat = (float(lasts_minutes) / float(budget)) if lasts_minutes and budget else 0.0
    led.record_scene_clock(run_id, start_turn, at_minutes, lasts_minutes, per_beat)
    elapsed = led.gap_before(run_id, at_minutes, before_turn=start_turn)
    owed = led.unspent_before(run_id, start_turn) or 0.0
    if elapsed and elapsed > 0:
        # DECLARED, THEN APPLIED. The declaration is the CAUSE and it is what gets logged; every
        # fade is DERIVED from it at replay - the drift by `bond_rest.rehydrate`, the wound, arc and
        # attitude fades by the folds at the foot of this module, the mood's by `mood_fold`. Until
        # 2026-09-22 only the drift was (gate erosion-derived-at-replay): the other three were applied
        # here in memory, lost on resume, and erased at a scene's first beat by the drivers' refold.
        # Before this line moved here, drift ran inline in the driver, mutated memory, and reached no
        # table — so a resumed cast lost every winter that passed. The declaration is MINUTES; the
        # three older tiers read it in DAYS (clock.elapsed_days_since), `toward.erode` as declared.
        # Since gate own-timelines no one ages by it (each character by their own time), and a scene set earlier
        # than the one run last - a negative gap, legal when they share no one - declares nothing.
        led.declare_time(run_id, start_turn, elapsed, str(names or ""))
    # EACH CHARACTER'S VIEW OF THEIR OWN LOG (gate flashback-windows): the window's for whom this is one - their past
    # before its time, and itself - and their present for everyone else. `views` goes back to the driver, which
    # hands each actor theirs for every read of their history until the scene ends.
    views = {i: wins.get(i) or _window.current(led.con, run_id, i) for i in chars}
    # EACH CHARACTER'S OWN TIME, from the last beat they were in the room: the mood's (gate absent-age), the slow
    # tiers' (gate own-timelines) and, in a book running `condition_flow`, the condition's (gate gap-day-and-night).
    gaps = {i: clock.presence_end(led.con, run_id, i, start_turn, views[i]) for i in chars}
    # AN INJURY WEAKENS THE BODY WHILE IT HEALS (gate injury-weakens): read at the opening, for the gap before it.
    weak = ({i: _injuries.weakening(led.con, run_id, i, chars[i], start_turn, views[i]) for i in chars}
            if (injuries and body) else None)
    relaxed = apply_opening(chars, lambda i: bond_rest.rows_for(led.con, run_id, i, views[i]), at_minutes, gaps,
                            flow=flow, body=body, stated=stated, weakened=weak)
    # keyword form, not a literal {"elapsed": ...} — this is the DERIVED result of gap_before, the
    # thing that retired an AUTHORED cfg `elapsed` field (2026-09-10, clock.py), not a reappearance
    # of it; tests/test_retired_vocabulary.py greps source text and cannot tell the two apart.
    return dict(elapsed=elapsed, owed=owed, per_beat=per_beat, relaxed=relaxed, own=own_minutes(chars, at_minutes, gaps),
                windows=wins, views=views)


def own_minutes(ids, at, gaps):
    """{id: minutes} - how long each character has been out of the room at an opening (gate absent-age): from the
    scene reading they were last in (`gaps`, {id: clock.presence_end(...)}) to `at`, plus what they owe of it (the
    rest of a scene they walked out of, or one that lulled) - `clock.since_presence`, the arithmetic the folds' own
    opening item uses (gate own-timelines). An id with no earlier presence is left out: a first appearance arrives
    as the sheet describes them. For someone in the last scene to its end this is exactly the run's gap plus that
    scene's unspent minutes - the old rule, which aged whoever was in the NEW scene by the time since the LAST one
    ended, so a character who sat scenes out came back feeling as they did when they left."""
    return {i: clock.since_presence(g, at) for i in ids for g in [(gaps or {}).get(i)] if g is not None}


def apply_opening(chars, rest_rows, at, gaps, flow=False, body=False, stated=None, weakened=None):
    """An opening's effects on every character, in memory -> the ids whose slow tiers it aged (sorted).

    THE APPLICATION HALF OF `open_scene`, split out verbatim (gate mood-from-readings, 2026-09-22) so the
    mood replay applies an opening with the very code the drivers ran, rather than a second copy of it.
    EVERY CHARACTER BY THEIR OWN TIME (`own_minutes`, from `gaps` {id: clock.presence_end(...) or None} and `at`,
    this opening): the mood decays over it (gate absent-age), and the slow tiers age over it (`age`, gate
    own-timelines) - each edge drifts toward its rest, the wounds erode, the temperament returns toward what was
    authored and the attitude fades - exactly the opening item `clock.time_items` gives the folds. Someone who sat
    scenes out or walked out comes back aged by all of it; someone in the last scene to its end, by the gap plus
    that scene's unspent minutes, as before; a FIRST APPEARANCE is left as the sheet describes them - their story
    begins here. Until gate own-timelines the slow tiers took the run's gap for everyone, first appearances too,
    and the folds had already aged a late arrival from the run's first opening. `gaps` is required
    (PASSAGE_GAPS_MISSING); at the run's first opening every entry is None and nothing moves. `rest_rows(id)` ->
    that character's rest rows as the opening reads them (`bond_rest.rows_for` at the time).

    `flow` (the book runs `condition_flow`, gate condition-flow): the owed minutes cost energy and the
    gap restores it (`condition.opening`) - first, while the mood is still the one the last scene ended
    on, which is the one the owed minutes were lived in. `body` (the book runs `body`, gate body-exertion): the
    owed minutes are weighed against each character's strength, as a beat's are. The condition's gap is each
    character's OWN (gate gap-day-and-night): walked by `condition.between` - night rests, day is awake, `stated`
    {id: rested | awake} supersedes; an id with no earlier presence keeps the sheet's condition. `weakened` {id:
    strength words down} (gate injury-weakens): an injury not yet healed makes the gap cost that body more.
    """
    if gaps is None:
        raise RecordError("PASSAGE_GAPS_MISSING",
                          "passage: an opening needs each character's presence (gaps {id: clock.presence_end(...) or "
                          "None}) to age them by their own time away")
    ids = list(chars)
    if flow:
        for i in ids:
            g = gaps.get(i)
            if g is None:                  # first presence in this run: the sheet is their state
                continue
            chars[i]["current"]["condition"] = _condition.between(
                chars[i]["current"]["condition"], g["end"], at, g["owed"], chars[i]["current"].get("affect"),
                1.0 / _body.capacity(chars[i], (weakened or {}).get(i, 0)) if body else 1.0, (stated or {}).get(i))
    own = own_minutes(ids, at, gaps)
    for i, minutes in own.items():
        if minutes > 0:
            ch = chars[i]
            aged = decay(dict(ch["current"]["affect"]), ch["baseline"]["temperament"], build_profile(ch),
                         elapsed=minutes)
            ch["current"]["affect"] = dict(aged)
    # THE SLOW TIERS, EACH BY THEIR OWN TIME, after the mood (the order the drivers always kept).
    aged = []
    for i, minutes in own.items():
        if minutes > 0:
            age({i: chars[i]}, minutes, rest_rows)
            aged.append(i)
    return sorted(aged)


def age(chars, minutes, rest_rows):
    """Story time passing for the slow tiers of every character given -> the ids it aged, sorted (gate
    slow-tiers-run; docs/design.md, "State runs whether or not the page is looking").

    THE ONE STEP every stretch of story time takes, live and in the folds: at an opening (`apply_opening`: each
    character's own time since they were last in a room), at every beat for everyone in the room (both drivers and
    `mood_fold._beat`, before the beat's own movements; gate own-timelines - it was the whole cast, walk-outs too),
    and item by item in `fold_toward` / `fold_wounds` / `fold_arc` and `bond_rest.rehydrate` over each character's
    own `clock.time_items`. Each edge drifts toward its own rest, each untouched
    scar eases toward its floor, the resting means return toward what was authored, and the attitudes fade toward
    zero on the bonds as they have just drifted - the order the folds keep. Until this gate only the gap between
    scenes did any of it. `rest_rows(id)` -> that character's rest rows as this moment reads them; `minutes` of 0
    or less ages nothing: []."""
    if not minutes or float(minutes) <= 0.0:
        return []
    minutes = float(minutes)
    days = minutes / float(clock.MINUTES_PER_DAY)
    ids = list(chars)
    for i in ids:
        ch = chars[i]
        priors = ch["baseline"].get("relationship_priors", {})
        rels = ch["current"].get("relationships") or {}
        # TOWARD EACH EDGE'S OWN REST (bond-arithmetic.md s6, gate 4): the declared rows, else a
        # stranger's — never `_NEUTRAL` for an authored friendship.
        _rows = rest_rows(i)
        for tgt, edge in rels.items():
            if isinstance(edge, dict):
                rels[tgt] = dict(edge, **bond_rest.drift(edge, bond_rest.resolve(_rows, priors, tgt), days))
        # the SAME stretch erodes an untouched wound — one clock, two tiers
        # (docs/character-model.md "DECAY AND CONNECTION": two clocks and no third).
        for _w in (ch["baseline"].get("wounds") or []):          # engine wounds (gate three)
            if isinstance(_w, dict) and "intensity" in _w:
                _e = wound.erode(_w, days)
                if _e:
                    _w.setdefault("_authored_intensity", float(_w["intensity"]))
                    _w["intensity"] = max(0.0, min(1.0, float(_w["intensity"]) + _e))
        # THE SAME STRETCH, three tiers. Edges drift toward their priors, wounds erode
        # toward their floor, temperament returns toward what the author wrote, and feelings
        # toward a person fade toward ZERO — slower for people this character is invested in,
        # because connection does its second job here (docs/character-model.md). The last of
        # those reads the stretch in MINUTES (the staircase's clock), the first three in days.
        arc.erode(ch, days)
        _conns = {who: connection.for_target(rels, who)
                  for who in ((ch["current"].get("toward") or {}))}
        toward.erode(ch, minutes, _conns)
    return sorted(ids)


def restore_latest(char, latest):
    """Put the chronicle's latest mood AND condition onto a resumed character's sheet -> the char.

    ONE RESTORE, for both drivers (gate resume-and-parity, 2026-09-22). Each driver hand-copied it and
    each dropped something: both kept only `affect` from `ledger.latest_affect`, though it returns
    `condition` too, so a resumed character's condition came back as authored; and the chair set only
    its LOCAL mood, so `open_scene` then decayed the sheet's authored mood and the chair copied that
    over what it had restored. It must run BEFORE `open_scene`, which reads the sheet. `latest` None
    (a character with no committed beat) leaves the sheet as authored.
    """
    if latest:
        cur = char.setdefault("current", {})
        if isinstance(latest.get("affect"), dict):
            cur["affect"] = dict(latest["affect"])
        if isinstance(latest.get("condition"), dict) and latest["condition"]:
            cur["condition"] = dict(latest["condition"])
    return char


def bystanders(room, speaker, minutes, here):
    """Step 4 of the beat: every OTHER present character, decay only -> {id: decayed affect}.

    THE MINUTES PASS FOR THE WHOLE ROOM (gate non-speaker-decay, 2026-09-22; docs/emotion-arithmetic.md
    section 5, step 4). Until this, only the speaker decayed, so a character who listened for five beats
    aged one beat's minutes when they next spoke. Each bystander decays on THEIR OWN binds - what their
    feelings are about - against the same room the speaker's decay reads, because `state.decay`
    slows a feeling whose object is present and a feeling the character is invested in.

    room: {id: {"affect", "temperament", "profile", "targets"}} - the present characters, the speaker
    among them (the driver's actor dicts carry exactly these keys). Pure: returns new dicts.
    """
    return {i: decay(dict(r["affect"]), r["temperament"], r["profile"], elapsed=float(minutes or 0.0),
                     targets=dict(r.get("targets") or {}), present=set(here or ()))
            for i, r in room.items() if i != speaker}


# ---------------------------------------------------------------------------------------------------
# THE FADE, DERIVED AT REPLAY (gate erosion-derived-at-replay, 2026-09-22)
#
# `open_scene` applies a declared gap's fade to attitude, wounds and resting mood IN MEMORY and logs
# only the cause, the time declaration - and nothing read the cause back. So on resume every fade was
# lost, and worse, both drivers re-folded attitude and wounds after EVERY committed beat from the
# authored base plus the logged deltas, erasing that scene's own opening fade at its first beat. The
# docs said the fade is "DERIVED at replay"; these three folds make it so. Logging the fade as rows
# was not an option: each of the three tables allows one row per turn per item, and an opening shares
# its turn with the scene's first beat.
#
# ORDER. A fade multiplies whatever value it finds; a delta adds. They do not commute. Between two
# stretches of story time the deltas stay ORDER-FREE - summed, then clamped once, exactly as
# `toward.replay` and `levers.replay_wound_deltas` have always done - and each stretch's fade applies at
# its place in the log: after every delta of the turns before it, before the deltas of its own turn. Since
# gate slow-tiers-run (2026-09-24) the stretches are `clock.time_items`: each opening and each committed beat's
# own minutes, the opening's first - so a scene that lasts a day fades every tier across that day, not only
# across the gaps between scenes. Since gate own-timelines (2026-09-25) they are each CHARACTER'S own: their
# time since they were last in a room at each opening they attend, and the beats they were in the room for.
# With no stretch in the log each fold equals the old restorer exactly; tests/test_passage.py pins that.
# ---------------------------------------------------------------------------------------------------

def stamp_authored(char):
    """Record what the sheet authored, BEFORE anything moves it -> the char. Idempotent (setdefault).

    The folds rebuild from these, never from the live values, so they must be taken at load: a
    scene opening fades attitude and wounds before the first refold runs, and a stamp taken then
    would record the faded value as the authored one. `_authored_relationships` and
    `_authored_attachments` let the attitude fold rebuild the bonds as they stood at each opening.
    Underscored `current` keys never reach a prompt: assembly selects its volatile keys explicitly.
    """
    cur = char.setdefault("current", {})
    cur.setdefault("_authored_relationships", _copy.deepcopy(cur.get("relationships") or {}))
    cur.setdefault("_authored_attachments", _copy.deepcopy(cur.get("attachments") or {}))
    cur.setdefault("_authored_toward", {w: dict(v) for w, v in (cur.get("toward") or {}).items()
                                        if isinstance(v, dict)})
    for w in ((char.get("baseline") or {}).get("wounds") or []):
        if isinstance(w, dict) and "intensity" in w:
            w.setdefault("_authored_intensity", float(w["intensity"]))
    return char


def _bound(before_turn):
    """The SQL clause for a fold read AS OF a turn (the replay's resume) - "" for the whole log."""
    return "" if before_turn is None else " AND turn < %d" % int(before_turn)


def _stretches(con, run_id, char_id, before_turn=None, view=None):
    """{turn: [minutes, ...]} - every stretch of story time one character lived, a turn's opening before its beat's
    own (`clock.time_items`: gate slow-tiers-run, per character since gate own-timelines, in their view since gate
    flashback-windows). Until gate slow-tiers-run the only stretch was a declared gap between scenes."""
    out = {}
    for t, _slot, m in clock.time_items(con, run_id, char_id, before_turn, view):
        out.setdefault(int(t), []).append(float(m))
    return out


def fold_toward(con, run_id, char_id, char, before_turn=None, view=None):
    """Rebuild `current.toward` from the authored attitude, the logged deltas and every stretch of story time's
    fade, in log order -> the rebuilt dict. Called on resume and after every committed beat. `before_turn`
    folds the log as it stood before that turn (the mood replay's resume); None is the whole log.

    ONE WALK OF THE BOND TIMELINE (gate slow-tiers-run): the attitude fades on the bonds AS THEY STOOD at each
    stretch - its own drift already in, the beat's movements not - so the walk folds the bonds one item at a time
    (`bond_rest.rehydrate`, its rests carried across) and reads the connections at every time item. The fold used
    to rebuild the bonds from the sheet at each opening; with a stretch at every beat that is a rebuild per beat.
    `view`: which of their rows count (gate flashback-windows, `window.view`; None - their present)."""
    view = _window.of(con, run_id, char_id, view)
    cur = char.setdefault("current", {})
    authored = cur.setdefault("_authored_toward", {w: dict(v) for w, v in (cur.get("toward") or {}).items()
                                                   if isinstance(v, dict)})
    cur["toward"] = {w: dict(v) for w, v in authored.items()}
    rows = bond_rest.timeline_rows(con, run_id, char_id, before=None if before_turn is None else (int(before_turn), 0),
                                   view=view)
    if any(it[0] == "time" for _t, _s, it in rows) and "_authored_relationships" not in cur:
        raise RecordError("PASSAGE_FOLD_UNSTAMPED",
                          "passage: the attitude fold needs the authored bonds - call stamp_authored "
                          "when the sheet loads, before anything moves it")
    by_turn = {}
    for t, tgt, prim, d in con.execute("SELECT turn, target, primary_, delta FROM toward_deltas WHERE run_id = ? "
                                       "AND perceiver = ?" + _bound(before_turn) + _window.clause(view)
                                       + " ORDER BY turn, delta_id",
                                       (run_id, char_id)):
        by_turn.setdefault(int(t), []).append((str(tgt), str(prim), float(d)))
    pending = {}

    def flush():
        for who, vec in pending.items():
            start = dict(cur["toward"].get(who) or {})
            merged = {}
            for prim in set(start) | set(vec):
                v = toward._clamp(float(start.get(prim, 0.0)) + float(vec.get(prim, 0.0)))
                if v:
                    merged[prim] = v
            cur["toward"][who] = merged
        pending.clear()

    def pend(turn):
        for who, prim, d in by_turn.get(turn, ()):
            if prim in PATHS:
                slot = pending.setdefault(who, {})
                slot[prim] = slot.get(prim, 0.0) + d

    rels = _copy.deepcopy(cur.get("_authored_relationships") or {})
    atts = _copy.deepcopy(cur.get("_authored_attachments") or {})
    priors, rests, turns, k = (char.get("baseline") or {}).get("relationship_priors", {}), {}, sorted(by_turn), 0
    for t, _slot, item in rows:
        if item[0] == "time":                         # every earlier turn's deltas land before this stretch
            while k < len(turns) and turns[k] < t:
                pend(turns[k])
                k += 1
            flush()
        bond_rest.rehydrate(rels, priors, [item], attachments=atts, rests=rests)
        if item[0] == "time":
            toward.erode(char, item[2], {who: connection.for_target(rels, who) for who in (cur.get("toward") or {})})
    for turn in turns[k:]:
        pend(turn)
    flush()
    return cur["toward"]


def fold_wounds(con, run_id, char_id, char, before_turn=None, view=None):
    """Rebuild `baseline.wounds`: the authored wounds, each minting at its turn, the logged deltas and every
    opening's fade, in log order -> the list (mutated in place). Called on resume and after every beat.
    `before_turn` folds the log as it stood before that turn; None is the whole log. `view`: gate flashback-windows."""
    view = _window.of(con, run_id, char_id, view)
    base = char.setdefault("baseline", {})
    wounds = base.setdefault("wounds", [])
    if not isinstance(wounds, list):
        raise RecordError("WOUND_LIST_NOT_A_LIST", "baseline.wounds must be a list, got %r" % type(wounds).__name__)
    minted = [(int(r[0]), wound.make(r[2], r[3], r[4], r[5], text=r[6], triggers=_json.loads(r[7] or "[]")))
              for r in con.execute("SELECT turn, wound_id, concept, path, intensity, source, text, triggers "
                                   "FROM wound_minted WHERE run_id = ? AND char_id = ?" + _bound(before_turn) +
                                   _window.clause(view) + " ORDER BY turn, mint_id",
                                   (run_id, str(char_id)))]
    minted_ids = {m["id"] for _t, m in minted}
    live = []
    for w in wounds:
        if isinstance(w, dict) and str(w.get("id", "")) not in minted_ids:
            if "intensity" in w:
                w.setdefault("_authored_intensity", float(w["intensity"]))
                w["intensity"] = float(w["_authored_intensity"])
            live.append(w)
    wounds[:] = live
    have = {str(w.get("id", "")) for w in wounds if isinstance(w, dict)}
    stretches = _stretches(con, run_id, char_id, before_turn, view)
    mints_at, deltas_at = {}, {}
    for t, m in minted:
        mints_at.setdefault(t, []).append(m)
    for t, wid, d in con.execute("SELECT turn, wound_id, delta FROM wound_deltas WHERE run_id = ? AND char_id = ?"
                                 + _bound(before_turn) + _window.clause(view) + " ORDER BY turn, delta_id",
                                 (run_id, str(char_id))):
        deltas_at.setdefault(int(t), []).append((str(wid), float(d)))
    pending = {}

    def flush():
        for w in wounds:
            wid = str(w.get("id", ""))
            if isinstance(w, dict) and wid in pending and "intensity" in w:
                w.setdefault("_authored_intensity", float(w["intensity"]))
                w["intensity"] = max(0.0, min(1.0, float(w["intensity"]) + pending[wid]))
        pending.clear()

    for turn in sorted(set(mints_at) | set(deltas_at) | set(stretches)):
        if turn in stretches:
            flush()
            for minutes in stretches[turn]:                   # the opening's stretch, then the beat's own
                days = minutes / float(clock.MINUTES_PER_DAY)
                for w in wounds:                              # exactly what the live step (`age`) does
                    if isinstance(w, dict) and "intensity" in w:
                        e = wound.erode(w, days)
                        if e:
                            w.setdefault("_authored_intensity", float(w["intensity"]))
                            w["intensity"] = max(0.0, min(1.0, float(w["intensity"]) + e))
        for m in mints_at.get(turn, ()):                      # a wound minted in a beat joins after its time
            if m["id"] not in have:
                # its minted strength IS its authored one, stamped as it joins - as `wound.fold` did -
                # so `levers.scale_to_wounds` scales a faded scar against what it was minted at
                wounds.append(dict(m, _authored_intensity=float(m["intensity"])))
                have.add(m["id"])
        for wid, d in deltas_at.get(turn, ()):
            pending[wid] = pending.get(wid, 0.0) + d
    flush()
    return wounds


def fold_arc(con, run_id, char_id, char, before_turn=None, view=None):
    """Replay the arc - each durable diff and every stretch of story time's fade of the resting means - in log
    order -> the char (a new dict when any diff applies, as `arc.apply` returns one). `before_turn` folds the
    log as it stood before that turn; None is the whole log. `view`: gate flashback-windows."""
    view = _window.of(con, run_id, char_id, view)
    stretches = _stretches(con, run_id, char_id, before_turn, view)
    diffs = {int(t): _json.loads(d) for t, d in con.execute(
        "SELECT turn, diff FROM arc_diffs WHERE run_id = ? AND char_id = ?" + _bound(before_turn) + _window.clause(view)
        + " ORDER BY turn",
        (run_id, char_id))}
    for turn in sorted(set(diffs) | set(stretches)):
        for minutes in stretches.get(turn, ()):
            arc.erode(char, minutes / float(clock.MINUTES_PER_DAY))
        if turn in diffs:
            char = arc.apply(char, diffs[turn])
    return char

