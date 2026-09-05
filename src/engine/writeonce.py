"""writeonce.py — the identities the spine writes ONCE, and the refusal when something writes twice.

A SMALL CONCEPT WITH A REAL BOUNDARY. FOUR identities in this engine are minted once and never
rewritten: a `run_id`, a `(run_id, char_id)` cast entry, a `(run_id, turn, actor)` commit, and a
`(run_id, scene_no)` scene boundary. The DATABASE already enforces that with primary keys and,
since schema v9, with append-only triggers. What was missing was the Python half — the writers
leaked the enforcement rather than performing it.

THE COUNT WAS THREE IN THIS FILE'S FIRST DRAFT, and the fourth was found the same day by looking at
the TABLES rather than at the sites already converted. The number is written here because it is the
thing most likely to go stale next: a fifth write-once key added to `schema.sql` will not announce
itself, and nothing mechanically checks this sentence.

WHAT IT REPLACED, measured 2026-09-03 on a live ledger: `create_run` and `register_character` each
raised a bare `sqlite3.IntegrityError: UNIQUE constraint failed: …` with `.code` None, and
`append_turn` raised LEDGER_TURN_COMMIT_ROLLED_BACK — which names the MECHANISM (a transaction
rolled back) rather than the condition (that turn is already in the log). Two writers leaking an
uncoded refusal out of the module CLAUDE.md calls the spine, and the third answering the wrong
question.

WHY IT IS ITS OWN FILE. `ledger.py` sat at 485 lines against hard rule 6's 500, and this is the
SECOND correct change in two days that it could not absorb — `divergence` went to `snapshots.py`
last night for the same reason. Shaving comments to fit is the same file with less explanation in
it, and it crosses again on the next change. `bible.py` gave this signal and was split; this is that
lesson applied one file earlier, while the change is still small.

THE CHECK IS THE FAST PATH; THE DATABASE IS THE ARBITER. A SELECT followed by an INSERT is not
atomic, so two writers can both pass the check and one then hits the constraint. This file used to
say that plainly and stop there — a caveat is a defect that has been written down. `write_once`
closes it by catching what the constraint says and RE-ASKING the check: if the row is there now,
the same registered code is raised.

TWO WAYS TO LOSE A RACE, AND THE FIRST FIX COVERED THE RARER ONE. "Total under contention" was
written here on the strength of the COLLISION — the loser squeezing between check and commit. The
likelier loss is the WAIT: any other writer holding the lock past db.py's busy timeout, on a call
that is not a duplicate of anything. Measured 2026-09-03 at 5.4s on a `create_run` for an
uncontended run id, which left the spine as a raw `sqlite3.OperationalError` with no `.code` — the
defect this module was written to end, arriving through the door it did not watch. `db.refuse_if_busy`
now names it, and `ledger.append_turn` raises the SAME code for the SAME condition, because one
module answering one condition two ways is how it went unnoticed.

RE-ASKING IS THE LOAD-BEARING PART. `sqlite3.IntegrityError` is not proof that THIS identity is the
duplicate — a foreign key, or a different UNIQUE on the same table, raises the same class. Mapping
it to the duplicate code by assumption would put a confident, wrong name on an unrelated fault,
which is the defect this whole conversion exists to remove. The check answers precisely, so ask it.
"""
import sqlite3

from . import db as _db          # for the busy code; `db` imports nothing from here
from .records import RecordError  # the bad-input type db.py already uses


def refuse_duplicate(con, sql, params, code, msg, err):
    """Refuse a second write of a write-once identity. ONE spelling, three callers.

    The SQL and the code come from the caller because the caller knows which identity it is
    protecting; what lives here is the shape — ask, then refuse with a registered code rather than
    letting the constraint answer in its own words.

    `err` IS THE CALLER'S TYPE, which is this repo's existing idiom for exactly this circularity:
    `narration_modes.validate(..., err=NarrationError)` and `clock.declare(..., on_rewrite=...)`
    both take it. `LedgerError` is defined in `ledger.py`, which imports this module, so importing
    it back would be a cycle — and passing the type keeps `ledger.py` raising `LedgerError` without
    this file needing to know what its caller calls that.
    """
    if con.execute(sql, params).fetchone():
        raise err(code, msg)


def write_once(con, check, write):
    """Perform a write-once write, with the same answer whichever half of the race noticed.

    `check()` is the caller's question about the identity, and it has THREE answers, which is why
    it is a callable rather than a SQL string: return False to proceed, return True if the write is
    already done IDENTICALLY (a replay — `--resume` re-walks committed turns by design, so
    `clock.declare` and `ledger.append_arc_diff` must treat that as a no-op, not a refusal), or
    raise the caller's coded error if what is already stored CONFLICTS. A fixed sql+code signature
    could only express the middle case, which is why half this engine's write-once sites could not
    use the first version of this function.

    `write()` performs the inserts inside ONE transaction, so a caller writing two rows (a scene
    and the cfg it pins) commits both or neither.

    THE RE-ASK IS THE LOAD-BEARING PART. `sqlite3.IntegrityError` is raised by every constraint on
    the table — a foreign key, a CHECK, a second UNIQUE — so mapping it to the caller's code by
    assumption would put a confident, wrong name on an unrelated fault. `edl.append` did exactly
    that and reported "generation 0 already holds ord_no 0" for a run that did not exist. Asking
    the check again answers precisely; anything it does not claim propagates as itself.
    """
    if con.in_transaction:
        # THE UNSTATED PRECONDITION, MADE CHECKED. With DML pending on this connection the check
        # below reads inside that uncommitted snapshot, and worse, the `with con:` here would
        # ROLL THE CALLER'S WORK BACK on any failure. No in-tree caller does this (swept 2026-09-03
        # across src/, scripts/ and tests/); a REPL or a hook easily could.
        raise RecordError(
            "DB_TRANSACTION_OPEN",
            "write_once was handed a connection with uncommitted work on it. Commit or roll back "
            "before writing a write-once identity: this function opens its own transaction and "
            "would discard yours.")
    if check():
        return True                       # already written, identically — a replay, not a write
    try:
        with con:
            write()
    except sqlite3.IntegrityError:
        if check():                       # the row is there now: the constraint answered first
            return True
        raise                             # a DIFFERENT constraint — not ours to name
    except sqlite3.OperationalError as exc:
        _db.refuse_if_busy(exc, "write_once")
        raise
    return False
