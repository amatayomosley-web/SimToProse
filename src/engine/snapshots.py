"""snapshots.py — the folded world, cached. NOT the source of truth, and the file says so.

CLAUDE.md hard rule 2: *"The snapshot is a derivable CACHE, never the source of truth."* That seam
lived inside `ledger.py` beside the log itself, which made it easy to forget which half was which.
It is its own file now, and the whole contract is the module docstring:

  * WRITE is `persist` — a memo, safe to lose.
  * READ is `load` — the newest memo, or None. `Ledger.fold` needs no memo at all.
  * INVALIDATE is `drop_from` — **the obligation of any writer that appends below the head.**

That last one is the reason this file exists rather than staying three methods. `Ledger.resume`
replays only the events AFTER the cached turn, so an event appended at or below it is invisible to
the incremental fold and present in the from-zero fold. The two differ and `resume` refuses — which
is correct, because the cache really is stale.

Measured 2026-09-01: `scene.py` parks a run by persisting a snapshot; `world_events.append` then
wrote events at that same turn; the run became permanently unresumable and the only repair was
deleting snapshot rows by hand. Nothing was wrong with the log, the fold, or the divergence check.
The cache had simply not been told.

Deleting here is legal and deliberate: schema v9's append-only triggers cover `events`, `turns`,
`recall_events`, `acquisitions`, `arc_diffs` and `relationship_deltas`, and deliberately EXCLUDE
`snapshots` and `current_state` — CLAUDE.md's own words, *"a cache that cannot be rewritten is not
a cache."*

`Ledger` keeps thin methods delegating here, so the thirteen existing call sites are unchanged.
"""
import json

KINDS = ("agents", "holdings", "information", "relationships", "tensions", "clock")


def persist(con, run_id, as_of_turn, snap):
    """Cache the folded snapshot at a turn, replacing any memo already there."""
    with con:
        con.execute("DELETE FROM snapshots WHERE run_id = ? AND as_of_turn = ?",
                    (run_id, as_of_turn))
        for kind in KINDS:
            pairs = snap[kind].items() if kind != "clock" else [("now", snap["clock"]["now"])]
            for key, value in pairs:
                con.execute(
                    "INSERT INTO snapshots (run_id, as_of_turn, kind, key, value) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (run_id, as_of_turn, kind, str(key), json.dumps(value)))


def load(con, run_id):
    """The newest cached snapshot -> (as_of_turn, snap), or None if nothing is cached."""
    row = con.execute("SELECT MAX(as_of_turn) AS t FROM snapshots WHERE run_id = ?",
                      (run_id,)).fetchone()
    if row["t"] is None:
        return None
    as_of = row["t"]
    snap = {kind: {} for kind in KINDS}
    for r in con.execute("SELECT kind, key, value FROM snapshots WHERE run_id = ? AND as_of_turn = ?",
                         (run_id, as_of)):
        if r["kind"] == "clock":
            snap["clock"] = {"now": json.loads(r["value"])}
        else:
            snap[r["kind"]][r["key"]] = json.loads(r["value"])
    return as_of, snap


def drop_from(con, run_id, turn, own_transaction=True):
    """Invalidate cached snapshots at or after `turn` -> rows dropped.

    Snapshots strictly BELOW `turn` are untouched, and that is not an optimisation: `fold` replays
    by `effective_at`, so an event effective at turn N cannot change the fold at any earlier turn.
    Dropping them too would make the next resume replay the whole log for nothing.

    `own_transaction=False` for a caller that is ALREADY inside one — `world_events.append` must
    invalidate in the same transaction as its inserts, or a crash between the two commits leaves
    the run unresumable. It matters that this is a flag rather than a second copy of the SQL: the
    first version of that fix inlined the DELETE, which left this function with no production
    caller while its own docstring called itself "the obligation of any writer". Two spellings of
    one rule drift the moment the boundary changes (`>=` vs `>`), and that is the hand-copied
    duplicate CLAUDE.md tabulates seven instances of.

    A nested `with con:` on the same connection COMMITS the outer transaction at the inner exit,
    which is exactly why the flag exists rather than an unconditional `with`.
    """
    sql = "DELETE FROM snapshots WHERE run_id = ? AND as_of_turn >= ?"
    if not own_transaction:
        return con.execute(sql, (run_id, int(turn))).rowcount
    with con:
        cur = con.execute(sql, (run_id, int(turn)))
    return cur.rowcount


def divergence(led, run_id):
    """Snapshot+tail replay vs the from-zero fold -> (diverged, detail, turn, fold).

    THE CACHE-VALIDITY QUESTION, and it belongs to the cache. It lived inside `Ledger.resume`, which
    asks it for the ONE run_id passed to `--resume` — so a parked run whose cache went stale was
    silent until someone reopened exactly that run, and `read_api.snapshot_at` reads the cache
    without asking at all. `integrity.sweep` needs the same question for every run.

    It moved HERE rather than being re-spelled there, and rather than staying on `Ledger`: the same
    two reasons `world_events.would_change` took a `Ledger` instead of living on one. Two spellings
    of one rule drift the moment the boundary changes (this module's own `drop_from` docstring), and
    putting it on `Ledger` pushed that file past hard rule 6's 500 lines. This module already owns
    the CONCEPT — the snapshot is a cache, and whether a cache is stale is the cache's question.

    DETECTION ONLY: writes nothing, raises nothing. `Ledger.resume` turns a True into the coded
    refusal an operator reads; `integrity.sweep` turns it into a finding.
    """
    t = led.latest_turn(run_id)
    cached = led.load_snapshot(run_id)
    if cached is None:
        incremental = led.fold(run_id, t)
    else:
        as_of, snap = cached
        snap = json.loads(json.dumps(snap))            # deep copy; JSON-shaped by construction
        for ev in led._events_between(run_id, as_of, t):
            led._project(snap, ev)
        snap["clock"] = {"now": t}
        incremental = snap
    full = led.fold(run_id, t)
    if incremental == full:
        return False, "", t, full
    return True, "snapshot+tail replay != from-zero fold at turn %d" % t, t, full
