"""edl.py — the edit decision list: what the room decided, recorded so the prose can be traced.

WHY THIS EXISTS. `docs/cutting-room.md` divides the cut three ways and marks exactly one of them
human:

  1. VIEWS (computed, deterministic) — the engine SHOWS; it never decides. `scripts/cut.py`.
  2. THE DISCUSSION (director + editor) — every shaping choice, made by people.
  3. THE RECORD + THE CHECKS (mechanical) — "decisions append to the EDL; narration renders from it;
     audits verify the result. Faithfulness is never a vibe."

Parts 1 and 2 shipped. Part 3 did not exist: grepping the tree for `edl` returned nothing, so the
state was not "the cut is human by design" but "the cut is human AND unrecorded" — and the README's
"every line of the book traces to a recorded biographical moment" had no mechanism behind it.

WHAT THIS IS NOT. The same doc records a 7-step automated cut pipeline (index -> spine -> select ->
shape -> gate -> render -> audit) that was drafted and REJECTED the same day: "this one handed
machinery a judgment that belongs in the room. We have performed this craft zero times on real sim
data — automating it first would calibrate gates against taste we haven't formed." That rejection
stands. Nothing here selects, orders, finds a throughline or fits a chapter break. This file is a
typed record with a validating writer, and the entries come from people.

The guardrail the doc asks any addition to preserve, restated because it is easy to lose: MAGNITUDE
IS CONSEQUENCE, NOT MEANING. The quiet scene that carries the book may be numerically flat. Views
surface candidates; the room recognises meaning. The moment anything here gates on a number, the
rejection above has been reversed by accident.

The four kinds are `cutting-room.md`'s, built as written:

    SCENE   {scene_no, pov, trim: [event_id...] | FULL, placement: chrono | flashback(anchor)}
    SUMMARY {span: [tick_a, tick_b], pov, basis: [event_id...]}   -- compression, never invention
    BREAK   {level: chapter | act}
    NOTE    {rationale}                                           -- why we cut it this way
"""
import json
import sqlite3

from . import writeonce as _once
from .errors import EngineError

SCENE, SUMMARY, BREAK, NOTE = "SCENE", "SUMMARY", "BREAK", "NOTE"
KINDS = (SCENE, SUMMARY, BREAK, NOTE)

FULL = "FULL"                                   # a SCENE trimmed to nothing is rendered whole
PLACEMENTS = ("chrono", "flashback")
BREAK_LEVELS = ("chapter", "act")


class EDLError(EngineError):
    """An EDL entry failed boundary validation. The write that carried it must not happen."""


def _require(cond, code, msg):
    """Refuse with a REGISTERED code — `EngineError` refuses to construct an unknown one."""
    if not cond:
        raise EDLError(code, msg)


def validate(kind, payload):
    """Check one entry against its kind's contract. Raises EDLError naming the field.

    Fails LOUD and BEFORE the write (CLAUDE.md hard rule 6's fail-loud half): an EDL entry that
    cannot be rendered is worse than a missing one, because the manuscript silently loses a scene
    instead of reporting that the room's decision was malformed.
    """
    _require(kind in KINDS, "EDL_KIND_UNKNOWN",
             "edl: kind must be one of %s, got %r" % (list(KINDS), kind))
    _require(isinstance(payload, dict), "EDL_PAYLOAD_TYPE",
             "edl: payload must be a dict, got %s" % type(payload).__name__)

    if kind == SCENE:
        _require("scene_no" in payload, "EDL_SCENE_NO_MISSING",
                 "edl SCENE: scene_no is required")
        _require(isinstance(payload["scene_no"], int) and not isinstance(payload["scene_no"], bool),
                 "EDL_SCENE_NO_TYPE",
                 "edl SCENE: scene_no must be an int, got %r" % (payload["scene_no"],))
        trim = payload.get("trim", FULL)
        _require(trim == FULL or isinstance(trim, list), "EDL_TRIM_TYPE",
                 "edl SCENE: trim must be %r or a list of event ids, got %r" % (FULL, trim))
        place = payload.get("placement", "chrono")
        _require(place in PLACEMENTS, "EDL_PLACEMENT_UNKNOWN",
                 "edl SCENE: placement must be one of %s, got %r" % (list(PLACEMENTS), place))
        if place == "flashback":
            _require(payload.get("anchor") is not None, "EDL_FLASHBACK_NO_ANCHOR",
                     "edl SCENE: a flashback must name the recall_event_id it anchors to")
    elif kind == SUMMARY:
        span = payload.get("span")
        _require(isinstance(span, (list, tuple)) and len(span) == 2,
                 "EDL_SUMMARY_SPAN_SHAPE",
                 "edl SUMMARY: span must be [tick_a, tick_b], got %r" % (span,))
        _require(span[0] <= span[1], "EDL_SUMMARY_SPAN_BACKWARDS",
                 "edl SUMMARY: span runs backwards: %r" % (span,))
        # basis is what makes compression checkable rather than inventive — cutting-room.md calls a
        # SUMMARY "compression, never invention", and an empty basis is an unsourced paragraph.
        basis = payload.get("basis")
        _require(isinstance(basis, list) and basis, "EDL_SUMMARY_BASIS_EMPTY",
                 "edl SUMMARY: basis must be a non-empty list of event ids — a summary with no "
                 "basis is invention, which is the one thing a summary may not be")
    elif kind == BREAK:
        _require(payload.get("level") in BREAK_LEVELS, "EDL_BREAK_LEVEL_UNKNOWN",
                 "edl BREAK: level must be one of %s, got %r" % (list(BREAK_LEVELS),
                                                                 payload.get("level")))
    else:                                        # NOTE
        _require(str(payload.get("rationale") or "").strip(), "EDL_NOTE_NO_RATIONALE",
                 "edl NOTE: rationale is required — a note with no reason is not the room's memory")
    return True


def latest_generation(con, run_id):
    """The generation the run's live cut is in. 0 when nothing has been recorded."""
    row = con.execute("SELECT MAX(generation) AS g FROM edl WHERE run_id = ?", (run_id,)).fetchone()
    return 0 if row is None or row["g"] is None else row["g"]


def next_generation(con, run_id):
    """The generation a REVISION should be written into.

    The triggers on this table say "revise by appending" and until schema v17 there was nowhere to
    append TO: the primary key made a second pass collide, and writing at fresh ord_nos made
    narration render the UNION of both cuts. A run got exactly one cut, forever.
    """
    return latest_generation(con, run_id) + 1


def append(con, run_id, ord_no, kind, payload, generation=None):
    """Record one decision. Append-only; the EDL is the room's memory and is never rewritten.

    `ord_no` is the position in the manuscript, chosen by the room — NOT derived from scene order,
    because reordering is the whole point of a cut.

    `generation` defaults to the LIVE one, so recording a cut entry by entry works unchanged. Pass
    `next_generation(con, run_id)` to start a revision; the old cut stays in the log and stops
    rendering, which is what "revise by appending" was always supposed to mean.
    """
    validate(kind, payload)
    # THE RUN, BEFORE THE SLOT. Routing this module made the foreign key propagate as itself, which
    # is honest and still uncoded — and an uncoded exception leaving the engine is what this whole
    # conversion exists to end. The outer scope is checked first, the same order `append_turn` uses.
    if con.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone() is None:
        raise EDLError("EDL_RUN_UNKNOWN",
                       "edl: no run %r in this database — a cut belongs to a run" % run_id)
    gen = latest_generation(con, run_id) if generation is None else int(generation)
    # ROUTED THROUGH `write_once` 2026-09-03, replacing a bare `except sqlite3.IntegrityError` that
    # relabelled EVERY constraint on this table as a slot collision. Reproduced: appending for a run
    # that does not exist violates the FOREIGN KEY and reported "generation 0 already holds ord_no 0
    # for run 'no-such-run'" — a confident, wrong name for an unrelated rule, and the exact defect
    # `writeonce.py`'s own docstring cites as the reason it re-asks instead of assuming. This site
    # had no pre-check at all, which is why a census of pre-check-shaped sites could not see it.
    def _check():
        return _once.refuse_duplicate(
            con, "SELECT 1 FROM edl WHERE run_id=? AND generation=? AND ord_no=?",
            (run_id, gen, int(ord_no)), "EDL_ORD_COLLISION",
            "edl: generation %d already holds ord_no %d for run %r — a cut is not edited in place. "
            "Append a REVISION with generation=next_generation(con, run_id), which supersedes the "
            "whole list and leaves it in the log." % (gen, int(ord_no), run_id), EDLError)

    _once.write_once(con, _check, lambda: con.execute(
        "INSERT INTO edl (run_id, generation, ord_no, kind, payload) VALUES (?, ?, ?, ?, ?)",
        (run_id, gen, int(ord_no), kind,
         json.dumps(payload, sort_keys=True, ensure_ascii=False))))
    return True


def entries_for(con, run_id):
    """Every EDL entry for the run, in manuscript order -> [{ord_no, kind, ...payload}].

    EMPTY means no cut has been made, which is not an error: `narrate --book` falls back to
    rendering every scene, so a run made before the EDL existed reads exactly as it did.
    """
    # THE LIVE GENERATION ONLY. Earlier ones are superseded decisions: still in the log, because
    # the room's memory of what it tried is worth keeping, and no longer rendered.
    gen = latest_generation(con, run_id)
    rows = con.execute("SELECT ord_no, kind, payload FROM edl WHERE run_id = ? AND generation = ? "
                       "ORDER BY ord_no", (run_id, gen)).fetchall()
    out = []
    for r in rows:
        entry = {"ord_no": r["ord_no"], "kind": r["kind"]}
        entry.update(json.loads(r["payload"]))
        out.append(entry)
    return out


def turns_for_trim(con, run_id, trim):
    """Event ids -> the set of TURNS they sit on. Empty set for FULL or an empty trim.

    `cutting-room.md` writes a trim as `[event_id...]`, and the manuscript's unit is the TURN — a
    beat, which `pov_split` renders. Those are different keys, and the first renderer filtered the
    turn list by the trim VALUES directly: event ids are a global autoincrement, so a trim written
    to the documented contract kept arbitrary wrong turns, or none, and the scene vanished from the
    manuscript with no warning. The doc's unit stands; this resolves it.
    """
    if not trim or trim == FULL:
        return set()
    marks = ",".join("?" * len(trim))
    rows = con.execute("SELECT DISTINCT turn FROM events WHERE run_id = ? AND event_id IN (%s)"
                       % marks, tuple([run_id] + list(trim))).fetchall()
    return {r["turn"] for r in rows}


def _as_id(value):
    """An event id as the table stores it. A JSON trim may carry "3" for 3."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def traces(con, run_id, scenes):
    """The audit half -> (ok, [problem...]).

    `cutting-room.md`: "every prose unit traces to an EDL entry; every entry traces to recorded
    events". This is the second clause, checked mechanically: a SCENE entry naming a scene the run
    never recorded would render a passage with no biographical source behind it, which is precisely
    the failure the guarantee exists to exclude.

    `scenes` is the ROWS (`Ledger.scenes_for`), not just their numbers. It took numbers once, and
    that was the reason the sharpest case slipped through: a trim naming a REAL event that sits in a
    DIFFERENT scene passed existence checking, rendered nothing, and audited clean — measured
    2026-09-01, `ok=True, problems=[]` against an empty manuscript. Existence is not membership,
    and the turn range is what tells them apart, so the rows are required rather than optional.

    Reports rather than raises — an audit that aborts cannot show you the whole list.
    """
    rows = list(scenes or [])
    if rows and not isinstance(rows[0], dict):
        raise EDLError(
            "EDL_TRACES_NEEDS_ROWS",
            "edl.traces needs the scene ROWS (Ledger.scenes_for), not scene numbers: without "
            "start_turn/end_turn it can only check that a trimmed event EXISTS, not that it sits "
            "in the scene being trimmed — which is the case that renders an empty manuscript and "
            "audits clean.")
    by_no = {r["scene_no"]: r for r in rows}
    known = set(by_no)
    problems = []
    live = {r["event_id"] for r in
            con.execute("SELECT event_id FROM events WHERE run_id = ?", (run_id,)).fetchall()}
    for e in entries_for(con, run_id):
        if e["kind"] == SCENE:
            if e.get("scene_no") not in known:
                problems.append("EDL entry %d names scene %r, which the run did not record"
                                % (e["ord_no"], e.get("scene_no")))
            # THE OTHER HALF OF THE GUARANTEE. "every entry traces to recorded events" — a trim id
            # naming no recorded event silently empties the scene at render time, which is the
            # failure this audit exists to catch and did not.
            trim = e.get("trim")
            if trim and trim != FULL:
                # Coerced: a trim read from JSON may carry "3" where the table holds 3, and SQL's
                # IN would resolve it while a Python membership test would call it a ghost.
                ghosts = [i for i in trim if not _as_id(i) in live]
                if ghosts:
                    problems.append("EDL entry %d trims to event id(s) %s, which this run never "
                                    "recorded — the scene would render EMPTY"
                                    % (e["ord_no"], ", ".join(str(g) for g in ghosts)))
                # MEMBERSHIP, PER ID. A real event id belonging to a DIFFERENT scene keeps no turn
                # of THIS one. The first version reported only when the WHOLE trim landed outside,
                # so a trim mixing one valid id with one cross-scene id audited clean — no content
                # lost, but a decision referencing an event that has no effect, unremarked. An
                # entry that names something inert is a decision the room did not actually make.
                row = by_no.get(e.get("scene_no"))
                if row is not None:
                    strays = []
                    for i in (x for x in trim if x in live):
                        turns = turns_for_trim(con, run_id, [i])
                        if turns and not any(row["start_turn"] <= t <= row["end_turn"]
                                             for t in turns):
                            strays.append((i, sorted(turns)[0]))
                    if strays:
                        kept_any = turns_for_trim(con, run_id, [x for x in trim if x in live])
                        inside_any = any(row["start_turn"] <= t <= row["end_turn"]
                                         for t in kept_any)
                        problems.append(
                            "EDL entry %d trims scene %s to event id(s) %s, on turn(s) %s — outside "
                            "this scene's range %d-%d, so %s"
                            % (e["ord_no"], e.get("scene_no"),
                               ", ".join(str(i) for i, _t in strays),
                               ", ".join(str(t) for _i, t in strays),
                               row["start_turn"], row["end_turn"],
                               "they select nothing" if inside_any
                               else "the scene would render EMPTY"))
        if e["kind"] == SUMMARY:
            ghosts = [i for i in (e.get("basis") or []) if i not in live]
            if ghosts:
                problems.append("EDL entry %d summarises from event id(s) %s, which this run never "
                                "recorded — a summary with no basis is invention"
                                % (e["ord_no"], ", ".join(str(g) for g in ghosts)))
    return (not problems), problems
