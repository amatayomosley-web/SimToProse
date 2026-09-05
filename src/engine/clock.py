"""clock.py — the DECLARED clock. One cause, four consumers.

The director says how much time passed; nothing else knows. `arc.erode`, `bonds.drift`,
`wound.erode` and now `tensions.effective` all age their tier against this and nothing else, which
is what makes "one clock, four tiers" true rather than aspirational.

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
declarations with edge deltas for `bonds.rehydrate`, which is a different reading with no window
logic to disagree with. It belongs to the edge join, not to the clock. What this file owns is the
SUMMED reading, and there is exactly one of those.

TWO RULES THAT LOOK LIKE DETAILS AND ARE NOT:

  * A declaration records time passed BEFORE its turn. So `elapsed_since(t)` sums `turn > t`, never
    `>=` — a declaration at the same turn as the thing being aged PREDATES it and must not age it.
  * `elapsed` must be > 0. Nothing passing is not a declaration; it is the absence of one, and
    accepting it would let a caller quietly reset an erosion clock while looking like bookkeeping.
"""
from .errors import EngineError
from . import writeonce as _once
from .records import RecordError


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


def elapsed_since(con, run_id, turn):
    """Declared units between a turn and the head -> float. `turn >`, for the reason in the header."""
    row = con.execute(
        "SELECT COALESCE(SUM(elapsed), 0) AS total FROM time_declarations "
        "WHERE run_id = ? AND turn > ?", (run_id, int(turn))).fetchone()
    return float(row["total"] or 0.0)
