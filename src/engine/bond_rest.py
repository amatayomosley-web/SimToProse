"""bond_rest.py — the REST half of the relationship tier: where an edge relaxes to, and the fold that
walks rests, declarations and movements in the order they happened.

TWO CLOCKS, TWO MODULES. `bonds.py` is the LAW: what one witnessed act does to one edge, per beat.
This is the slow clock: what an unreinforced edge drifts toward across the days between scenes, and
how a resumed cast is rebuilt from the log so that drift and movement land in the order the run
held them. They were one module until 2026-09-17 (bond gate 4), when the law grew and bonds.py met
the 500-line pin; the split follows the seam the two clocks already had. Import graph: this module
imports `bonds` (for `_NEUTRAL` and `_clamp01`); `ledger` imports this (the rest table's rows are
written and read here, the seam `claims` / `targets` / `readings` / `wound` already use); `floor` imports `bonds`.
No cycle, no re-export — the four callers of `drift` / `rehydrate` changed by one token each.

WHY REST IS LOG-DERIVED AND NEVER STORED (bond-arithmetic.md s6). Until this gate every edge relaxed
toward `_NEUTRAL` (0.5), with only `relationship_priors.default_trust` authored: a devoted
.90/.90/.90 edge read .54/.52/.59 after thirty days and no row said why. A rest that sat on the
edge dict and moved on a cliff would be a mutable value with no log row — the v12 defect. So the
rest is a ROW: `rest_declared` (schema v28), `authored` when seeded from the sheet at run creation
or at a pre-v28 run's first resume, `cliff` when a trust cliff lowers it on the causing turn. The
fold reads the rows; nothing holds the value. A rest moves DOWN, never up: a grown, unauthored edge
rests where a stranger does (`stranger_rest`) — `default_trust` on trust, the sheet's "what they
assume about a stranger", and `_NEUTRAL` elsewhere — which is exactly the pre-v28 behaviour, so a
log written before this table replays to the numbers it held.
"""
from . import attachments as _attachments
from .bonds import _NEUTRAL, _clamp01
from .decay_law import relax
from . import clock as _clock          # MINUTES_PER_DAY: the timeline's time item is in days
from .records import RELATIONSHIP_AXES, RecordError, RestDeclared

_INSERT = ("INSERT INTO rest_declared (run_id, turn, perceiver, target, axis, rest, source) "
           "VALUES (?, ?, ?, ?, ?, ?, ?)")


def write(con, run_id, turn, rows):
    """The turn's rest rows into `rest_declared`, on the CALLER's transaction (ledger.append_turn's,
    so a rolled-back beat leaves no orphan rest). No transaction of its own, like claims.write."""
    for rr in rows or ():
        rr.validate()
        con.execute(_INSERT, (run_id, int(turn), rr.perceiver, rr.target, rr.axis, float(rr.rest), rr.source))


def rows_for(con, run_id, perceiver):
    """[(turn, target, axis, rest, source)] for one perceiver, in log order."""
    return [(int(r[0]), r[1], r[2], float(r[3]), r[4]) for r in con.execute(
        "SELECT turn, target, axis, rest, source FROM rest_declared WHERE run_id = ? AND perceiver = ? "
        "ORDER BY turn, rest_id", (run_id, perceiver))]


def timeline_rows(con, run_id, perceiver, before=None, seeded_at=None):
    """The whole bond timeline WITH its turns -> [(turn, slot, item)], ascending; within a turn rest (0),
    hold (1), time (2), edge (3). `Ledger.timeline_for` strips the turns for `rehydrate`; the attitude
    fold (`passage.fold_toward`) keeps them, because it needs the bonds AS OF each scene opening.

    THE TIME ITEM IS IN DAYS (gate erosion-derived-at-replay, 2026-09-22). `time_declarations` stores
    MINUTES (passage.open_scene declares the gap it derived in minutes), and `drift` reads DAYS - the
    live opening hands it `elapsed / MINUTES_PER_DAY`. This reader handed the replay the raw minutes,
    so a resumed run drifted every edge 1,440 times too hard: a one-day gap between scenes replayed as
    about four years, enough to walk a friendship back to a stranger's rest. The live run's only gap
    was a few minutes, which is why no recorded number moved.

    BOUNDS, for a replay that needs the bonds as they stood (gate mood-from-readings, 2026-09-22):
    `before` = (turn, slot) keeps the rows strictly before it - (t, 3) is the bonds a beat at t read,
    its opening's drift in, its own edge movements out; `seeded_at` is `declared_rows`'. Both None is
    the whole timeline, exactly as before.
    """
    rows = declared_rows(con, run_id, perceiver, seeded_at=seeded_at)
    rows += [(int(t), 2, ("time", float(e) / _clock.MINUTES_PER_DAY))
             for t, e in con.execute("SELECT turn, elapsed FROM time_declarations WHERE run_id = ?", (run_id,))]
    # BOTH ORDERS. Filtering to 'first' would silently drop the second-order tier (what the perceiver
    # believes the OTHER holds), which schema v8 exists to hold.
    rows += [(int(t), 3, ("edge", tgt, axis, float(d), o)) for t, tgt, axis, d, o in con.execute(
        "SELECT turn, target, axis, delta, ord FROM relationship_deltas WHERE run_id = ? AND perceiver = ?",
        (run_id, perceiver))]
    if before is not None:
        rows = [r for r in rows if (r[0], r[1]) < tuple(before)]
    return sorted(rows, key=lambda r: (r[0], r[1]))


def declared_rows(con, run_id, perceiver, seeded_at=None):
    """The DECLARATIONS half of the timeline: rest rows at slot 0, hold rows at slot 1 ->
    [(turn, slot, item)]. Lives beside the fold that reads them; ledger.timeline_for adds the turn's
    time (slot 2) and edge (slot 3) items and sorts. Moved here 2026-09-18 (gate 5) because ledger.py
    sits at the 300-code-line bound and the rows are this module's to read.

    `seeded_at` (a turn): keep that turn's rows only when written BEFORE its opening - a resume's
    `authored` seeds and the scene's `director` holds - and drop a cliff or keeper row the turn's own
    beat wrote after it. That is the log as the scene's characters were built from it (gate
    mood-from-readings; the director's holds added by gate systems-registry, 2026-09-22)."""
    keep = (lambda t, src: t != seeded_at or src in ("authored", "director")) if seeded_at is not None else (lambda t, src: True)
    rows = [(t, 0, ("rest", tg, ax, v)) for t, tg, ax, v, _s in rows_for(con, run_id, perceiver) if keep(t, _s)]
    rows += [(t, 1, ("hold", e, h, s)) for t, e, h, s, _src in _attachments.rows_for(con, run_id, perceiver)
             if keep(t, _src)]
    return rows


def seed(con, run_id, turn, perceiver, relationships):
    """An `authored` rest row for every (target, axis) on this perceiver's sheet that has none yet
    -> rows written. Idempotent, so run creation, a late join and a pre-v28 resume all call it; the
    rows land at `turn`, so the fold applies them before that turn's declaration. Its own
    transaction: the callers are drivers between beats, not inside append_turn."""
    rows = seed_rows(perceiver, relationships, existing=rows_for(con, run_id, perceiver))
    if rows:
        with con:
            write(con, run_id, turn, rows)
    return len(rows)

# DRIFT (relationships.md:30): retention per elapsed DAY, toward the edge's rest. "affinity fades
# faster than trust" is the doc's ordering; debt barely fades at all — a favour owed is not forgotten
# by the passage of a week. [CALIBRATION — bond-arithmetic.md s8: the Moor House gap pins it weakly]
_RETENTION = {"trust": 0.97, "affinity": 0.90, "respect": 0.95, "debt": 0.99}


def stranger_rest(priors):
    """Where an edge with NO declared rest relaxes to: `default_trust` on trust, `_NEUTRAL` elsewhere.

    `default_trust`'s one remaining job (bond-arithmetic.md s6, drift): the sheet's disposition
    toward people it has no history with. This is the pre-v28 behaviour, kept for undeclared edges.
    """
    rest = dict(_NEUTRAL)
    priors = priors if isinstance(priors, dict) else {}
    if "default_trust" in priors:
        try:
            rest["trust"] = _clamp01(float(priors["default_trust"]))
        except (TypeError, ValueError):
            pass
    return rest


def whole(edge, priors):
    """The edge with EVERY axis present -> a NEW dict: what the edge carries is kept (authored or
    moved values, `their_view`, anything else on it); an axis it lacks is the stranger's
    (`stranger_rest`). An edge the sheet never authored is BORN here, whole, where s6 says it rests.

    Until 2026-09-19 an undeclared edge was created EMPTY at every birth site (the fold's first
    movement, the law's read in floor.bond_moves, both drivers' apply, the replay tool) and every
    reader defaulted the axis it lacked to `_NEUTRAL` — so the sheet's `default_trust` (low on a wary
    sheet) reached the edge only as a drift target across the DAYS between scenes, and the first act
    a stranger did was priced from trust .50. Measured on the first live stranger case of a book run:
    three beats of a stranger's acts left the witness with affinity and respect and NO trust axis,
    and `drift` skips an axis the edge lacks, so no number of days would have moved it. Born whole,
    the sheet's assumption about a stranger applies at the first meeting.

    NOT acquaintance: `bonds.witnessed` keys recognition on the STORED edge being non-empty, and the
    callers hand it the stored edge before calling this — a born edge does not let a witness without
    insight pin an act on a stranger.
    """
    out = stranger_rest(priors)
    if isinstance(edge, dict):
        out.update(edge)
    return out


def seed_rows(perceiver, relationships, existing=()):
    """`authored` rest rows for every numeric axis on every edge of the sheet that `existing` does not
    already cover -> [RestDeclared]. Pure. `existing` is `rows_for`'s [(turn, target, axis,
    rest, source)]. Where the author put a relationship is where it rests until a cliff moves it."""
    have = {(str(t), str(a)) for (_turn, t, a, _r, _s) in (existing or ())}
    out = []
    for target, edge in (relationships or {}).items():
        if not isinstance(edge, dict):
            continue
        for axis in RELATIONSHIP_AXES:
            v = edge.get(axis)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and (str(target), axis) not in have:
                out.append(RestDeclared(perceiver=str(perceiver), target=str(target), axis=axis,
                                        rest=_clamp01(float(v)), source="authored"))
    return out


def resolve(rows, priors, target):
    """{axis: rest} for one target: the LATEST row per axis in `rows` (in log order), else the
    stranger's value. Always all four axes. `rows` is `rows_for`'s shape."""
    rest = stranger_rest(priors)
    for (_turn, t, axis, value, _source) in (rows or ()):
        if str(t) == str(target) and axis in rest:
            rest[axis] = _clamp01(float(value))
    return rest


def cliff_rows(perceiver, target, edge_after, cliffs, current_rest, source="cliff"):
    """One `cliff` row per cliffed axis whose post-cliff value sits BELOW the current rest -> [RestDeclared].
    The rest moves down, never up, and never twice to the same place. `cliffs` is bonds.cliff_axes'
    list of axes; `edge_after` the edge once the cliff's delta is applied; `current_rest` from resolve."""
    out = []
    for axis in (cliffs or ()):
        if axis not in RELATIONSHIP_AXES or axis not in (edge_after or {}):
            continue
        after = _clamp01(float(edge_after[axis]))
        if after < float((current_rest or {}).get(axis, _NEUTRAL.get(axis, 0.5))) - 1e-9:
            out.append(RestDeclared(perceiver=str(perceiver), target=str(target), axis=axis, rest=after, source=source))
    return out


def drift(edge, rest, elapsed=1.0):
    """Unreinforced edges settle back toward their REST (relationships.md:30; bond-arithmetic.md s6).

    `elapsed` is in DAYS and NOT beats: a single conversation must not erode a friendship, which is
    why this is not wired into the beat loop. `rest` is the edge's own {axis: value} from `resolve`
    — never `_NEUTRAL` handed in as a shortcut: drift to neutral turns a devoted friend into a
    stranger over a winter, and that is the defect this module's docstring records.
    """
    edge = edge if isinstance(edge, dict) else {}
    if not isinstance(rest, dict):
        raise RecordError("BONDS_REST_NOT_A_DICT", "drift: rest must be a dict {axis: value}, got %r" % type(rest).__name__)
    try:
        elapsed = max(0.0, float(elapsed))
    except (TypeError, ValueError):
        raise RecordError("BONDS_DRIFT_ELAPSED_NOT_NUMERIC", "drift: elapsed must be a number, got %r" % (elapsed,))
    out = dict(edge)
    for axis in RELATIONSHIP_AXES:
        if axis not in edge:
            continue
        if axis not in rest:
            raise RecordError("BONDS_REST_AXIS_MISSING", "drift: the rest carries no %r, which the edge does" % axis)
        out[axis] = _clamp01(relax(float(edge[axis]), float(rest[axis]), _RETENTION[axis], elapsed))
    return out


def rehydrate(relationships, priors, timeline, attachments=None):
    """Rebuild edges from the sheet by walking rests, declarations and movements IN THE ORDER THEY
    HAPPENED (Ledger.timeline_for). Returns the same dict, folded in place.

    ORDER IS LOAD-BEARING: drift is multiplicative toward a rest, a delta is additive, and they do
    not commute — `drift(0.80) then +0.10 != 0.80 + 0.10 then drift`. A fold that applied every
    declaration and then every movement would produce a number the run never held. Within a turn a
    rest takes effect first, then the hold, then the declaration, then the movements (the ledger's
    0/1/2/3 tiebreak: rest, hold, time, edge).

      ("rest", target, axis, value)  remembered: the edge's rest from here on
      ("hold", entity, hold, sign)   gate 5: folded onto `attachments` (the sheet block) in place
      ("time", elapsed)              every edge drifts toward its resolved rest
      ("edge", target, axis, d, ord) added to the edge ("first") or to `their_view` ("second")

    An unknown item kind is REFUSED: the old walk skipped one silently, and a silently skipped rest
    row would be this gate's dormancy.
    """
    if not isinstance(relationships, dict):
        raise RecordError("BONDS_RELATIONSHIPS_NOT_A_DICT", "rehydrate: relationships must be a dict, got %r"
                         % type(relationships).__name__)
    priors = priors or {}
    rests = {}                                       # target -> {axis: rest}, the latest per axis
    for item in (timeline or ()):
        kind = item[0]
        if kind == "rest":
            _, tgt, axis, value = item
            if axis not in RELATIONSHIP_AXES:
                raise RecordError("BONDS_LOG_AXIS_UNKNOWN", "rehydrate: unknown rest axis %r" % (axis,))
            rests.setdefault(str(tgt), {})[axis] = _clamp01(float(value))
        elif kind == "hold":
            # GATE 5: a declared hold takes effect after the turn's rest rows and before its time
            # declaration (slot 1), so the state after turn N carries what N declared. Numerically it
            # commutes with everything here (a hold feeds stake at the time the delta was PRICED, and
            # the delta is what the log holds); the slot is about the resumed sheet, not the edge.
            _, entity, hold, sign = item
            if not isinstance(attachments, dict):
                raise RecordError("BONDS_HOLD_ROW_UNFOLDED", "rehydrate: a hold row for %r arrived with no attachments block to fold into — pass attachments=current.attachments" % (entity,))
            attachments[str(entity)] = dict(attachments.get(str(entity)) or {}, hold=_clamp01(float(hold)), sign=str(sign))
        elif kind == "time":
            for tgt, edge in list(relationships.items()):
                if isinstance(edge, dict):
                    rest = dict(stranger_rest(priors), **rests.get(str(tgt), {}))
                    relationships[tgt] = dict(edge, **drift(edge, rest, item[1]))
        elif kind == "edge":
            _, tgt, axis, d, order = item
            if axis not in RELATIONSHIP_AXES:
                raise RecordError("BONDS_LOG_AXIS_UNKNOWN", "rehydrate: unknown axis %r (log disagrees with "
                                 "RELATIONSHIP_AXES)" % (axis,))
            # BORN WHOLE at its first movement (`whole`): a target the sheet never authored starts
            # where a stranger rests, on every axis — the same value `floor.bond_moves` priced the
            # delta from, so the fold lands where the run did. An authored edge keeps its values;
            # an axis it lacks is filled the same way.
            edge = relationships[tgt] = whole(relationships.get(tgt), priors)
            # SECOND ORDER lands in `their_view`, exactly as `bonds.replay` routes it.
            slot = edge.setdefault("their_view", {}) if order == "second" else edge
            slot[axis] = _clamp01(float(slot.get(axis, _NEUTRAL[axis])) + float(d))
        else:
            raise RecordError("BONDS_TIMELINE_KIND_UNKNOWN", "rehydrate: timeline item kind %r is not rest | hold | time | edge" % (kind,))
    return relationships
