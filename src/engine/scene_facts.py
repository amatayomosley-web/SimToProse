"""scene_facts.py — what has happened in this run, as FACTS, filtered to one actor's point of view.

WHY THIS EXISTS (2026-09-22). The actor is told who it is and how it feels, in detail: identity,
stage directions from its affect, the rungs it is on, its edges to everyone present, what it holds.
It was told NOTHING about what has happened. The one section whose label promises memory — "What it
brings to mind" (`prompt.py`) — is the long-term recall tier, and on the live run its belief set does
not follow the beat. So the actor's only record of the scene so far was
`prompt.compose_event`'s rolling transcript, whose documented job is anti-repetition and whose window
is FOUR beats.

The cost, measured over the two recorded scenes and re-checked by an independent review: of the 13
continuity flags a model critic raised on real prose, TEN contradict a beat that was outside that
window at the moment the actor wrote. The other three were in view, and in all three the actor
contradicted its OWN immediately preceding beat — so the transcript is not consumed as state at any
window width, which is why the answer is facts rather than more transcript.

WHAT THIS IS, AND THE ONE DECISION BEHIND IT. A ledger of DATED FACTS, never an object-state
snapshot. The predecessor design (`docs/props-ledger.md`, superseded) kept a current holder per thing,
which needs one object's identity resolved across beats, and the producer cannot supply that: the
event seat's `what` must be a span of THAT beat's action (`scripts/appraiser.py`,
APPRAISER_FACT_NOT_IN_ACTION). A dated fact is a claim about one moment, quoted from that moment.
It does NOT fully escape identity: when the seat quotes one act at two beats, the ledger shows it
twice (see OPEN, below).

THE ROWS COME FROM PRODUCERS THAT ALREADY RUN, and were read only by `bonds`, which priced them into
trust/debt floats and dropped the fact:

    passed   <- events.payload["transfers"] = [{what, from, to, terms}]   (since 2026-09-18)
    told     <- events.payload["told"]      = [{what, to, cost}]          (since 2026-09-18)

POINT OF VIEW IS THE CONTRACT. An actor receives a fact only from a beat it SPOKE or was PRESENT for.
Presence is the engine's own rule, from one function (`presence.present_ids`: a percept marked
`present: False` is someone spoken of, not someone in the room) and it is RECORDED per beat in the
manifest's `present` key. The first version of this module read every `entity.<id>` percept key as a
witness, because the manifest recorded refs and dropped that flag. A person in no scene's cast,
matched by first-name substring inside an ordinary word in someone's line, received four facts
from a room he never entered, and I had cited his appearance as proof the filter discriminated. A manifest written before the `present` key existed is
read through its `edges`, which `build_edges` filters by the same rule: lossy for a present person
with no relationship record, never a leak.

SCOPED TO THE RUN, NOT THE SCENE, with a budget PER KIND that never splits a beat (see BUDGETS).
A corrected event (`critic --correct`) contributes no row: its supersession is read through
`fold.superseded_ids`, the same function the world fold uses.

OPEN, recorded rather than guessed: (1) the seat's double-post — one act quoted at two beats reads as
two acts, and the section asks the actor to act consistently with it; pre-registered as a FAIL
condition of the controlled re-answer. (2) Object STATE (a door left open, a lamp put out) has no producer.
(3) Compaction: a settled loan is not collapsed against its repayment, because matching them is the
identity problem again.

Deterministic, stdlib only, no LLM (hard rule 3). No writes: every row is derived from the log on
demand, so there is no new table and nothing to migrate.
"""
from __future__ import annotations

import json

from . import fold as _fold
from .records import RecordError

# The two row kinds this module folds. A third — `changed`, for object STATE — is DESIGNED and NOT
# BUILT: no producer emits it, and adding one is a seat-contract change that needs a live re-answer.
PASSED = "passed"
TOLD = "told"
KINDS = (PASSED, TOLD)

# How many rows of each kind an actor is shown, most recent first, never splitting a beat.
#
# MEASURED 2026-09-22 on the three re-answer arms of the two recorded scenes (28 beats): at most 14
# `passed` rows and 13 `told` rows over the whole span, and no beat above three rows of either kind.
#
#   passed 24 — [JUDGMENT anchored on that measurement] every passing in the recorded data fits with
#               room for a further scene. It WILL bind over a book, and when it does the oldest
#               passing goes first; compaction is the open answer, not a larger number.
#   told    6 — [JUDGMENT] tellings are long quotes and the recency-relevant kind; six rows is the
#               last few beats of what was said. Kept separate so a run of speeches can never push a
#               loan off the ledger — which is exactly what one shared budget of twelve did.
#
# The first version of this constant was a single `12` annotated "at most 9 observed". Nothing had
# measured 9. It bound before turn 10 and dropped the oldest facts, rebuilding the four-beat window
# one layer up. A number here that says "measured" names the measurement or says JUDGMENT.
BUDGET_PASSED = 24
BUDGET_TOLD = 6
BUDGETS = {PASSED: BUDGET_PASSED, TOLD: BUDGET_TOLD}

_SELF = "self"


def _party(value, speaker):
    """A seat's party field -> an id. `self` is the beat's own actor, as `bonds` resolves it
    (bonds.py, the fix of c9f8728 — the seat's `self` priced every self beat at 0 until it was)."""
    v = str(value or "").strip()
    return speaker if v.lower() == _SELF and speaker else v


def _rows(payload, turn, speaker):
    """One committed beat's payload -> its fact rows. Order within a beat is the seat's order."""
    out = []
    for t in payload.get("transfers") or []:
        if not isinstance(t, dict):
            continue
        what = str(t.get("what") or "").strip()
        frm, to = _party(t.get("from"), speaker), _party(t.get("to"), speaker)
        if not (what and frm and to):
            continue
        out.append({"kind": PASSED, "turn": int(turn), "speaker": speaker, "what": what,
                    "from": frm, "to": to, "terms": str(t.get("terms") or "none").strip().lower()})
    for t in payload.get("told") or []:
        if not isinstance(t, dict):
            continue
        what = str(t.get("what") or "").strip()
        if not what:
            continue
        out.append({"kind": TOLD, "turn": int(turn), "speaker": speaker, "what": what,
                    "to": _party(t.get("to"), speaker),
                    "cost": str(t.get("cost") or "none").strip().lower()})
    return out


def witnessed(row, actor, present_by_turn):
    """Did `actor` witness the beat this row came from? Its speaker did; otherwise the beat's
    recorded presence decides. A beat with no presence on record is witnessed by its speaker alone:
    absent evidence of presence, the safe answer is the one that cannot leak."""
    if not actor:
        raise RecordError("SCENE_FACTS_NO_ACTOR", "scene_facts.witnessed: actor is required")
    if row.get("speaker") == actor:
        return True
    return actor in (present_by_turn.get(int(row["turn"])) or frozenset())


def for_actor(rows, actor, present_by_turn, budgets=BUDGETS):
    """POV-filter `rows` for `actor`; keep the most recent beats of each kind under its budget.

    WHOLE BEATS ONLY. A beat's rows of one kind are kept together or not at all: a cut that split a
    beat kept whichever row the seat happened to list first, and on the recorded data that kept a
    row the critic had flagged as an error and dropped the valid row beside it.
    `budgets=None` keeps everything — for measurement only; no driver passes it.
    """
    if not isinstance(rows, list):
        raise RecordError("SCENE_FACTS_ROWS_NOT_A_LIST",
                          "scene_facts.for_actor: rows must be a list, got %s" % type(rows).__name__)
    mine = [r for r in rows if witnessed(r, actor, present_by_turn)]
    if budgets is None:
        return sorted(mine, key=lambda r: int(r["turn"]), reverse=True)
    kept = []
    for kind in KINDS:
        cap = int(budgets.get(kind, 0))
        by_turn = {}
        for r in mine:
            if r["kind"] == kind:
                by_turn.setdefault(int(r["turn"]), []).append(r)
        n = 0
        for turn in sorted(by_turn, reverse=True):
            beat = by_turn[turn]
            if n + len(beat) > cap:
                break
            kept.extend(beat)
            n += len(beat)
    kept.sort(key=lambda r: int(r["turn"]), reverse=True)   # stable: seat order within a beat
    return kept


def present_by_turn(con, run_id):
    """{turn: frozenset(ids PRESENT at that beat)} from the decision manifests.

    Reads the manifest's `present` key (written from `presence.present_ids` since gate
    `scene-facts-fix`). A manifest older than that key is read through its `edges`, which
    `presence.build_edges` filters by the same rule: someone merely spoken of never appears there.
    That fallback is lossy — a present person with no relationship record has no edge — and it can
    never leak. A manifest that cannot be parsed contributes nothing.
    """
    out = {}
    for turn, blob in con.execute(
            "SELECT turn, manifest FROM decision_manifests WHERE run_id=? ORDER BY turn", (run_id,)):
        try:
            m = json.loads(blob) if blob else {}
        except (TypeError, ValueError):
            continue
        ids = m["present"] if "present" in m else m.get("edges")
        out[int(turn)] = frozenset(str(i) for i in (ids or []) if i)
    return out


def _superseded(con, run_id, before_turn=None):
    """Event ids a `correction` has superseded, via the world fold's own `superseded_ids`.

    Read as plain mappings so this works on any connection whatever its row factory; the supersession
    RULE is the fold's, not a copy. A correction lands at a later tick than what it names, so for the
    beat being composed only corrections already in effect before it apply.
    """
    q = "SELECT type, payload FROM events WHERE run_id=? AND type=?"
    args = [run_id, _fold.CORRECTION]
    if before_turn is not None:
        q += " AND effective_at < ?"
        args.append(int(before_turn))
    return _fold.superseded_ids([{"type": t, "payload": p} for t, p in con.execute(q, args)])


def payloads(con, run_id, before_turn=None):
    """(turn, payload dict) for every live event of a run, in log order: corrections and what they superseded
    are skipped, an unreadable payload contributes nothing. `before_turn` excludes the beat being composed.
    The one reading of the log's payloads - `run_rows` below and `injuries.run_rows` fold from it."""
    dead = _superseded(con, run_id, before_turn)
    q = "SELECT event_id, turn, type, payload FROM events WHERE run_id=?"
    args = [run_id]
    if before_turn is not None:
        q += " AND turn < ?"
        args.append(int(before_turn))
    for event_id, turn, etype, payload in con.execute(q + " ORDER BY turn, event_id", args):
        if etype == _fold.CORRECTION or int(event_id) in dead:
            continue
        try:
            p = json.loads(payload) if payload else {}
        except (TypeError, ValueError):
            continue
        if isinstance(p, dict):
            yield turn, p


def run_rows(con, run_id, before_turn=None):
    """Every fact row of a run, in log order, minus superseded events. `before_turn` excludes the
    beat being composed."""
    speakers = {int(t): a for t, a in con.execute("SELECT turn, actor FROM turns WHERE run_id=?", (run_id,))}
    rows = []
    for turn, p in payloads(con, run_id, before_turn):
        rows.extend(_rows(p, turn, speakers.get(int(turn))))
    return rows


def facts_for(con, run_id, actor, before_turn=None, budgets=BUDGETS):
    """The one call a driver makes: this actor's witnessed facts, most recent first.

    Takes the LIVE connection both drivers already hold (`led.con`) rather than re-opening the
    file: the drivers' other in-turn reads (`read_api.established`, `previous_affect`) all go through
    the same handle.
    """
    return for_actor(run_rows(con, run_id, before_turn=before_turn),
                     actor, present_by_turn(con, run_id), budgets=budgets)
