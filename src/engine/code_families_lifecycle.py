"""code_families_lifecycle.py — the code DATA for a book's life after adoption: drafts, the lineage log, the lease.

A SECOND DATA FILE, split, not sanded (`code_families.py`'s own rule): that file reached 791 of CLAUDE.md hard rule 6's
800 total lines with the record-role codes, and the draft flow (gate draft-flow, 2026-09-27) is the first of several
gates that add families about what happens to a book once it has a record - drafts and approval here, the author's
declarations and a struck beat after it. `codes.py` imports these and merges them with the rest: still ONE registry,
read through `codes.CODES` / `codes.DESCRIPTIONS`. NAMING and the two-way rule live in `codes.py`.
"""

# ---- DRAFT_* — the approval flow (src/engine/drafts.py, scripts/draft.py) ----
_DRAFT_F = {
    "DRAFT_BOOK_NOT_ADOPTED": "a draft flow met a book whose database is not its record (never adopted, or missing), so there is no approved state to copy a draft from or land one on - `draft.py adopt` first",
    "DRAFT_NOT_FOUND":       "no open draft there - never opened, already promoted, set aside or left stale (the refusal names which), or, once a book is adopted, a writer's database that is not a draft in its runs/drafts at all",
    "DRAFT_NOT_OURS":        "a file in runs/drafts is not the draft the lineage opened under that id - no open entry, a role row with another id or parent, or no database at all - so it could be a forged file, which must not be written or promoted (gate record-role review 3); `draft.py reject` sets it aside",
    "DRAFT_IN_USE":          "a database is still open somewhere - an SQLite connection whose -wal or -shm outlives a close of our own, or another program's handle that refuses a move - so promoting, adopting or moving it would lose what that run writes next",
    "DRAFT_NOT_EXTENDING":   "a draft does not hold every run and turn of the record it names as its parent, which a real draft always does (it began as a copy, and the log is append-only) - another book's draft copied in, most likely",
    "DRAFT_RECORD_MISSING":  "the record the lineage adopted is not where the lineage names it, or is no longer a record - or a book to adopt has no database yet (adopt --new starts one empty); adopting again would abandon every approved state",
    "DRAFT_BOOK_ADOPTED":    "adopt was asked of a book the lineage already adopted; a book is adopted once",
    "DRAFT_NOT_A_BOOK":      "a draft flow was given a folder with no world/ in it (books._book_dirs' marker of a book), and writes nothing into one - not even its lease",
    "DRAFT_APPROVAL_MISSING": "a promote or restore was asked for without the owner's words - none, no letter or digit in them, or a <placeholder>; the record changes only on a yes, recorded exactly as given",
    "DRAFT_APPROVER_UNKNOWN": "who gave the yes was not `owner` or `partner-relayed`; a relayed yes is recorded as relayed, never as the owner's own",
    "DRAFT_HEAD_UNKNOWN":    "a restore named a state the lineage never kept a history copy of",
    "DRAFT_HEAD_CURRENT":    "a restore named the state the record is already in",
    "DRAFT_HISTORY_CHANGED": "the history copy of a state is missing, carries another state, or its bytes no longer match the digest the lineage logged when it was kept - something wrote it since",
}

# ---- LINEAGE_* — the book's lineage log and lease (src/engine/lineage.py) ----
_LINEAGE_F = {
    "LINEAGE_UNREADABLE":  "a line of the book's runs/lineage.jsonl is not a lineage entry (not JSON, not an object, an unknown op, or a field its op needs is missing); it is refused, never skipped, since a skipped line is a promote or restore the checks would miss",
    "LINEAGE_OP_UNKNOWN":  "an entry was appended under an op the lineage does not know",
    "LINEAGE_LEASE_HELD":  "another process holds the book's lease - another flow is running on this book; the operating system frees it when that process ends",
}
