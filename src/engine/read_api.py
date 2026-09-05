"""read_api.py — the orchestrator's typed read surface over the run DB.

The orchestrator cannot be grounded if it cannot fetch. Before this module the
only read paths were `Ledger.resume`/`latest_affect`/`fold` and the raw SQL
recipes in guide-operating.md — nothing an agent could query by question.

Deliberately BORING (docs/orchestrator-design.md §6A). Exact relational lookup:
no thresholds, no ranking, no centroids, no calibration. Vela needs that
apparatus because relevance there is a fuzzy score distribution; "what did she
say at turn 14" is a primary-key hit. If this module ever grows a cutoff, the
problem has been mis-modelled.

Every read returns a ReadResult carrying a `trace` — which step ran and what it
filtered — so an EMPTY result is attributable (fact absent vs wrong query vs
perspective filter). Vela's stage-attribution lesson: an unattributable "I don't
know" is the worst failure a grounding system can have.

Every read is AS-OF a turn. A fact true at turn 40 asserted at turn 90 is
confidently wrong while sounding perfectly grounded, so `as_of` is required, not
optional, on every state-bearing call.
"""
from __future__ import annotations

__layer__ = "engine"

import json
from .errors import EngineError


class ReadError(EngineError):
    """Malformed read request — fails loud rather than returning empty."""


class ReadResult:
    """Rows plus the trace that explains them (or explains their absence)."""

    __slots__ = ("rows", "trace", "as_of", "perspective")

    def __init__(self, rows, trace, as_of=None, perspective="world"):
        self.rows = rows
        self.trace = trace          # [str] — ordered steps, each naming what it did
        self.as_of = as_of
        self.perspective = perspective

    @property
    def found(self):
        return bool(self.rows)

    def step(self, msg):
        self.trace.append(msg)
        return self

    def as_dict(self):
        return {
            "found": self.found,
            "rows": self.rows,
            "trace": self.trace,
            "as_of": self.as_of,
            "perspective": self.perspective,
        }


def _require(cond, code, msg):
    """Refuse a malformed REQUEST with a registered code.

    RENAMED BACK from `_require_arg` on 2026-09-02, and the reason is the whole point: the trap was
    never the shared NAME, it was two helpers with two CONTRACTS answering to one. `tensions.py`
    and `edl.py` take (cond, code, msg); this took (cond, msg); and `tests/test_errors.py` scans
    for the name. Now that this tier is coded, all three have the same signature and the same
    meaning, so the shared name is accurate rather than a half-match waiting to happen — and the
    scanner sees this tier without being taught anything.

    WHAT THIS TIER DOES NOT REFUSE: a miss. `snapshot_at` on a turn with no persisted snapshot
    reports it in the trace and returns no rows, because "nothing is recorded there" is a true
    answer to a well-formed question. Only the QUESTION can be malformed."""
    if not cond:
        raise ReadError(code, msg)


def _int_as_of(as_of):
    _require(isinstance(as_of, int) and not isinstance(as_of, bool),
             "READ_AS_OF_NOT_AN_INT",
             "as_of must be an int turn index, got %r" % (as_of,))
    _require(as_of >= 0, "READ_AS_OF_NEGATIVE", "as_of must be >= 0, got %d" % as_of)
    return as_of


def _known_run(con, run_id):
    """THE ONE ABSENCE THAT IS A MALFORMED QUESTION, and the exception that proves the rule above.

    Every other miss on this surface is a true answer: a turn that recorded nothing, a character
    who learned nothing, a place nobody has spoken about. The RUN is different, because it is the
    aggregate every read is scoped BY — an unknown one has no world for a fact to be absent from,
    so a typo returned rows [] and a trace that read exactly like a real, empty history. That is
    the failure `read_api`'s own header calls the worst a grounding system can have: an
    unattributable "I don't know".

    `Ledger.load_run` already draws this line on the write side. This is the same line, read-side.
    """
    _require(isinstance(run_id, str) and run_id.strip(), "READ_RUN_UNKNOWN",
             "run_id must be a non-empty string, got %r" % (run_id,))
    if con.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone() is None:
        known = [r[0] for r in con.execute("SELECT run_id FROM runs ORDER BY run_id LIMIT 8")]
        _require(False, "READ_RUN_UNKNOWN",
                 "no run %r in this database. This is the one absence this tier refuses rather "
                 "than reports: every other miss is a true answer about a world that exists, and "
                 "an unknown run has no world to be absent from — an empty result here would read "
                 "as a real, empty history. Known runs: %s"
                 % (run_id, ", ".join(known) or "none"))
    return run_id


def _rows(cur):
    return [dict(r) for r in cur.fetchall()]


def _loads(val, default=None):
    try:
        return json.loads(val)
    except (TypeError, ValueError):
        return default


# --- the surface ----------------------------------------------------------

def said(con, run_id, turn):
    """The recorded turn: thought, action, tags, validation. Exact lookup."""
    _known_run(con, run_id)
    _require(isinstance(turn, int) and not isinstance(turn, bool),
             "READ_TURN_NOT_AN_INT",
             "turn must be an int, got %r" % (turn,))
    res = ReadResult([], ["said: turns WHERE run_id=%s AND turn=%d" % (run_id, turn)], as_of=turn)
    rows = _rows(con.execute(
        "SELECT turn, actor, thought, action, tags, validation, committed_at "
        "FROM turns WHERE run_id=? AND turn=? ORDER BY actor", (run_id, turn)))
    for r in rows:
        r["tags"] = _loads(r.get("tags"), {})
        r["validation"] = _loads(r.get("validation"), {})
    res.rows = rows
    if not rows:
        latest = con.execute(
            "SELECT MAX(turn) AS m FROM turns WHERE run_id=?", (run_id,)).fetchone()["m"]
        res.step("MISS: no turn %d; latest committed turn is %s" % (turn, latest))
    return res


def state(con, run_id, char_id, as_of):
    """Affect + condition for a character AS OF a turn — the latest row at or
    before `as_of`, never the newest row overall."""
    _known_run(con, run_id)
    as_of = _int_as_of(as_of)
    res = ReadResult([], ["state: current_state WHERE char=%s AND turn<=%d" % (char_id, as_of)],
                     as_of=as_of, perspective="char:%s" % char_id)
    row = con.execute(
        "SELECT turn, affect, condition FROM current_state "
        "WHERE run_id=? AND char_id=? AND turn<=? ORDER BY turn DESC LIMIT 1",
        (run_id, char_id, as_of)).fetchone()
    if row is None:
        known = con.execute(
            "SELECT COUNT(*) AS c FROM characters WHERE run_id=? AND char_id=?",
            (run_id, char_id)).fetchone()["c"]
        res.step("MISS: %s" % ("character not registered in this run"
                               if not known else "registered, but no state row at or before turn %d" % as_of))
        return res
    d = dict(row)
    d["affect"] = _loads(d.get("affect"), {})
    d["condition"] = _loads(d.get("condition"), {})
    res.rows = [d]
    if d["turn"] != as_of:
        res.step("carried forward from turn %d (no row at %d)" % (d["turn"], as_of))
    return res


def knows(con, run_id, char_id, as_of, contains=None):
    """What this character BELIEVES as of a turn — their vault slice, never
    world-truth. The perspective wall: a false belief here is correct data."""
    _known_run(con, run_id)
    as_of = _int_as_of(as_of)
    res = ReadResult([], ["knows: acquisitions WHERE char=%s AND turn<=%d" % (char_id, as_of)],
                     as_of=as_of, perspective="char:%s" % char_id)
    rows = _rows(con.execute(
        "SELECT acquisition_id, turn, belief FROM acquisitions "
        "WHERE run_id=? AND char_id=? AND turn<=? ORDER BY turn, acquisition_id",
        (run_id, char_id, as_of)))
    for r in rows:
        r["belief"] = _loads(r.get("belief"), {})
    if contains:
        needle = str(contains).lower()
        before = len(rows)
        rows = [r for r in rows
                if needle in json.dumps(r["belief"]).lower()]
        res.step("filtered by contains=%r: %d -> %d" % (contains, before, len(rows)))
    res.rows = rows
    if not rows:
        total = con.execute(
            "SELECT COUNT(*) AS c FROM acquisitions WHERE run_id=? AND char_id=?",
            (run_id, char_id)).fetchone()["c"]
        res.step("MISS: character holds %d acquired belief(s) overall in this run" % total)
    return res


def edges(con, run_id, perceiver, target, as_of):
    """Relationship trajectory perceiver -> target as of a turn: every delta, plus TWO folded nets.

    THE TWO ORDERS ARE DIFFERENT QUANTITIES ABOUT DIFFERENT PARTIES and this used to add them
    together. `net` was one dict folded over every row, so once schema v8 (2026-08-23) began
    persisting `bonds.reflect`'s output as `ord='second'`, the answer to "what has A's trust in B
    done" silently included "what A believes B's trust in A has done". A category error, not a
    rounding one — and `tests/test_read_api.py` had no second-order fixture, so the suite stayed
    green straight through it.

    Both nets are returned rather than one filtered by a parameter: a caller that does not know the
    second order exists still gets the right first-order number, and sees the other sitting beside
    it. An `ord=` argument would have let the same caller keep asking the ambiguous question.

    `cause_event` is still NULL on every row — `append_turn` has never had an event id to attach —
    so the old docstring's "every delta with the event that caused it" was already half a promise.
    Stated rather than repeated.
    """
    _known_run(con, run_id)
    as_of = _int_as_of(as_of)
    res = ReadResult([], ["edges: relationship_deltas %s->%s WHERE turn<=%d"
                          % (perceiver, target, as_of)],
                     as_of=as_of, perspective="char:%s" % perceiver)
    rows = _rows(con.execute(
        "SELECT delta_id, turn, axis, delta, ord, cause_event FROM relationship_deltas "
        "WHERE run_id=? AND perceiver=? AND target=? AND turn<=? ORDER BY turn, delta_id",
        (run_id, perceiver, target, as_of)))
    net, their_view = {}, {}
    for r in rows:
        # a pre-v8 row has ord defaulted to 'first' by the schema, which is what it is
        into = their_view if r["ord"] == "second" else net
        into[r["axis"]] = round(into.get(r["axis"], 0.0) + (r["delta"] or 0.0), 6)
    res.rows = rows
    res.step("net by axis (what %s holds about %s): %s" % (perceiver, target, net if net else "(none)"))
    res.step("second order (what %s believes %s holds about them): %s"
             % (perceiver, target, their_view if their_view else "(none)"))
    if not rows:
        res.step("MISS: no recorded deltas on this pair at or before turn %d" % as_of)
    return res


def snapshot_at(con, run_id, as_of, kind=None):
    """The folded world snapshot at a turn. `kind` narrows to one projection
    family (agents/holdings/information/relationships/tensions/clock)."""
    _known_run(con, run_id)
    as_of = _int_as_of(as_of)
    where = "run_id=? AND as_of_turn=?"
    params = [run_id, as_of]
    if kind is not None:
        where += " AND kind=?"
        params.append(kind)
    res = ReadResult([], ["snapshot_at: snapshots WHERE %s" % where], as_of=as_of)
    rows = _rows(con.execute(
        "SELECT as_of_turn, kind, key, value FROM snapshots WHERE %s ORDER BY kind, key" % where,
        tuple(params)))
    for r in rows:
        r["value"] = _loads(r.get("value"), r.get("value"))
    res.rows = rows
    if not rows:
        avail = [r["as_of_turn"] for r in _rows(con.execute(
            "SELECT DISTINCT as_of_turn FROM snapshots WHERE run_id=? ORDER BY as_of_turn",
            (run_id,)))]
        res.step("MISS: no persisted snapshot at turn %d; persisted turns: %s"
                 % (as_of, avail if avail else "(none)"))
    return res


def scene_of(con, run_id, turn):
    """Which scene a turn belongs to — the unit the cut and narration iterate."""
    _known_run(con, run_id)
    _require(isinstance(turn, int) and not isinstance(turn, bool),
             "READ_TURN_NOT_AN_INT",
             "turn must be an int, got %r" % (turn,))
    res = ReadResult([], ["scene_of: scenes WHERE start_turn<=%d<=end_turn" % turn], as_of=turn)
    rows = _rows(con.execute(
        "SELECT scene_no, label, pov, start_turn, end_turn FROM scenes "
        "WHERE run_id=? AND start_turn<=? AND end_turn>=? ORDER BY scene_no",
        (run_id, turn, turn)))
    res.rows = rows
    if not rows:
        res.step("MISS: turn %d falls outside every recorded scene boundary" % turn)
    return res


def place(con, run_id, place_id, as_of):
    """What is KNOWN about a location as of a turn — the first read here that is not person-shaped.

    This surface had six functions and five of them asked about people: `said`, `state`, `knows`,
    `edges`, `scene_of`. You could ask what someone knew at turn 40 and you could not ask what was
    known about a town, which is what "the engine models people through time and models places as a
    static authored string" looked like from the read side.

    Three sources, in the order a reader needs them:

      1. THE AUTHORED LINE — `bible_entities.what` for this location, pinned with the run's bible.
         One sentence, written once. It is the floor, not the answer.
      2. WHO IS THERE — from the folded snapshot's `agents`, so it moves when the keeper emits a
         `move`. Before the emitting seat existed this was permanently the seed.
      3. WHAT HAS BEEN SAID — every LIVE utterance whose subject is this place, as of this turn,
         with its FOLDED tier. Uncapped and unranked, because `claims.about` is: a keeper that
         misses one contradicting claim adopts a false fact, so completeness beats brevity.

    Rows are tagged by `source` so a caller can tell an authored fact from a thing a character said
    once and nobody has ruled on. The trace names every step, including the misses — a place with no
    lore must read as "nobody has said anything", never as an empty result that looks like an error.
    """
    _known_run(con, run_id)
    _require(isinstance(place_id, str) and place_id.strip(),
             "READ_PLACE_ID_EMPTY",
             "place_id must be a non-empty string, got %r" % (place_id,))
    as_of = _int_as_of(as_of)
    res = ReadResult([], ["place: %r as of turn %d" % (place_id, as_of)], as_of=as_of)

    row = con.execute(
        "SELECT be.what AS what FROM bible_entities be JOIN runs r ON 1=1 "
        "WHERE be.kind='location' AND be.entity_id=? AND be.fingerprint = "
        "json_extract(r.config, '$.bible_fingerprint') AND r.run_id=?",
        (place_id, run_id)).fetchone()
    if row and row["what"]:
        res.rows.append({"source": "authored", "what": row["what"]})
        res.step("authored: bible_entities.what")
    else:
        res.step("MISS: no authored line for %r — either the bible names no such location, or "
                 "the run predates bible pinning" % place_id)

    agents = _rows(con.execute(
        "SELECT key, value FROM snapshots WHERE run_id=? AND as_of_turn=? AND kind='agents'",
        (run_id, as_of)))
    here = []
    for a in agents:
        val = _loads(a.get("value"), {}) or {}
        if isinstance(val, dict) and val.get("location") == place_id:
            here.append(a["key"])
    if here:
        res.rows.append({"source": "present", "who": sorted(here)})
        res.step("present: %d from the folded snapshot" % len(here))
    else:
        res.step("MISS: nobody is recorded at %r in the snapshot at turn %d — note that "
                 "agents.location only moves when the keeper emits a `move`" % (place_id, as_of))

    from . import claims
    said = claims.about(claims.for_run(con, run_id, as_of), place_id,
                        claims.resolutions_for(con, run_id, as_of))
    for u in said:
        res.rows.append({"source": "said", "turn": u["turn"], "speaker": u["speaker"],
                         "tier": claims.tier_of(u, claims.resolutions_for(con, run_id, as_of)),
                         "text": u["text"], "extracts": u["extracts"]})
    res.step("said: %d live utterance(s) about %r" % (len(said), place_id)
             if said else "MISS: nobody has said anything about %r by turn %d" % (place_id, as_of))
    return res
