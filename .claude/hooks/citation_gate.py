#!/usr/bin/env python3
"""citation_gate.py — PreToolUse. No ungrounded fact becomes an artifact.

THE LAYER THIS BELONGS TO. Three hooks guard the orchestrator and they are not
interchangeable:

    inject   UserPromptSubmit  guards ANSWERS   (ground_from_book.py)
    block    PreToolUse        guards ARTIFACTS (this file)
    correct  Stop              guards OMISSIONS (not built yet)

No hook can un-say a sentence, so chat prose is grounded by INJECTION, not by
this. What this stops is an unresolvable claim becoming a written record — the
thing a future turn would then read back as canon.

It does not reimplement resolution. `citation.verify_envelope` already denies on
UNRESOLVED and — the rule a fresh implementation would get wrong — does NOT deny
on UNVERIFIABLE, because a namespace with no store behind it is a missing
checker, not a negative verdict.

FAILS CLOSED, deliberately. If this gate cannot run, it DENIES and says why.
The failure mode this whole repo keeps rediscovering is the guard that reports
success while guarding nothing; a gate that allows on error is invisible when
broken. Failing closed is safe here precisely because the gate is
lifecycle-scoped to a skill — unloading the skill removes it, so a broken gate
never strands anyone.
"""
import json
import os
import re
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_WRITE_TOOLS = ("Write", "Edit", "MultiEdit")
_ENVELOPE_RE = re.compile(r"```json\s*\n(\{.*?\})\n```", re.DOTALL)

# Notes that ARE world-fact records. A claim written here without an envelope is
# a fact with no provenance, so absence is itself a failure. Everything else
# under runs/ is process-truth (what the orchestrator DID, not what happened),
# where an envelope is verified if present and not demanded if absent.
_CANON_BEARING = ("canon-ledger.md", "continuity-register.md")


def _allow():
    return 0


def _deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    return 0


def _written_text(tool_input):
    """Every shape the write tools use, concatenated. A claim smuggled through
    any one of them is still a claim."""
    parts = [tool_input.get("content") or "", tool_input.get("new_string") or ""]
    for e in (tool_input.get("edits") or []):
        if isinstance(e, dict):
            parts.append(e.get("new_string") or "")
    return "\n".join(p for p in parts if p)


def _book_dir(path):
    """<book>/runs/<file> -> <book>. None when the path is not under a runs/."""
    parts = os.path.normpath(path).replace("\\", "/").split("/")
    if "runs" not in parts:
        return None
    return "/".join(parts[:parts.index("runs")]) or None


def _latest_run(con):
    row = con.execute("SELECT run_id FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()
    return row["run_id"] if row else None


def _open_readonly(db):
    """The chronicle, opened so it CANNOT be written.

    A bare `sqlite3.connect` here carried none of `db.connect`'s protections — most sharply
    `PRAGMA recursive_triggers=ON`, which exists because INSERT OR REPLACE performs its delete
    WITHOUT firing the delete trigger unless it is set. So an accidental write from this reader
    would bypass hard rule 2's append-only triggers, and `wound_deltas`/`toward_deltas`/
    `relationship_deltas` carry no timestamp or version column — nothing in the row afterward
    would say it had been rewritten.

    Routing through `db.connect` is NOT the fix: it MIGRATES on open, so a read would silently
    move a v12 chronicle to v22. `mode=ro` reads a live WAL database correctly and refuses writes,
    which is the same trade `scripts/doctor.py` makes for the same reason.
    """
    import os as _os
    return sqlite3.connect("file:%s?mode=ro" % _os.path.abspath(db).replace(chr(92), "/"),
                           uri=True)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return _allow()                       # not our payload; the harness owns this
    if not isinstance(payload, dict):
        return _allow()                       # a list/scalar is not an event we own

    if payload.get("tool_name") not in _WRITE_TOOLS:
        return _allow()
    tool_input = payload.get("tool_input") or {}
    path = str(tool_input.get("file_path") or "")
    if not path:
        return _allow()

    book = _book_dir(path)
    if book is None:
        return _allow()                       # not a process note — out of scope, by design

    text = _written_text(tool_input)
    match = _ENVELOPE_RE.search(text)
    is_canon = os.path.basename(path) in _CANON_BEARING

    if match is None:
        if is_canon:
            return _deny(
                "citation gate: %s is a canon-bearing note and carries no ```json envelope. "
                "A world-fact written here has no provenance a later turn could check. "
                "Attach an envelope {kind, claims:[{mode, cite|from}]} or write it to a "
                "process note instead." % os.path.basename(path))
        return _allow()                       # process note, no claims made

    # --- from here an envelope EXISTS, so it gets resolved or nothing ships ---
    try:
        envelope = json.loads(match.group(1))
    except Exception as e:
        return _deny("citation gate: the envelope in %s is not valid json (%s). An "
                     "unparseable envelope cannot be checked, so it is refused rather "
                     "than assumed good." % (os.path.basename(path), e))

    try:
        sys.path.insert(0, REPO)
        from src.engine import citation, books        # noqa: E402
    except Exception as e:
        return _deny("citation gate CANNOT RUN (import failed: %s). Denying rather than "
                     "allowing: a gate that passes when broken is worse than no gate. "
                     "Fix the gate, or unload the showrunner skill to remove it." % e)

    try:
        db = books.db_path(book)
        if not os.path.exists(db):
            return _deny("citation gate CANNOT RUN: no chronicle db at %s, so no citation "
                         "can be resolved. Run the book once before writing canon." % db)
        con = _open_readonly(db)
        con.row_factory = sqlite3.Row
        run_id = _latest_run(con)
        if not run_id:
            return _deny("citation gate CANNOT RUN: the db at %s has no runs, so there is "
                         "nothing to resolve citations against." % db)
        verdict = citation.verify_envelope(envelope, con, run_id)
    except citation.CitationError as e:
        return _deny("citation gate: malformed envelope in %s — %s"
                     % (os.path.basename(path), e))
    except Exception as e:
        return _deny("citation gate CANNOT RUN (%s: %s). Denying rather than allowing."
                     % (type(e).__name__, e))
    finally:
        try:
            con.close()
        except Exception:
            pass

    if not verdict.allowed:
        return _deny("citation gate: DENIED writing %s — %s. Every world-fact in a note must "
                     "resolve against the pinned bible or the run log. Cite what exists, or "
                     "move the claim to `unknowns`."
                     % (os.path.basename(path), verdict.reason() or "unresolved citations"))

    # UNVERIFIABLE tokens do NOT deny — a namespace with no store is a missing checker,
    # not a negative verdict. They are surfaced so the gap stays visible instead of
    # being silently read back as if it had been checked.
    if verdict.unverifiable:
        sys.stderr.write("citation gate: allowed %s with %d unverifiable citation(s): %s\n"
                         % (os.path.basename(path), len(verdict.unverifiable),
                            "; ".join("%s (%s)" % (t, d) for _, t, d in verdict.unverifiable)))
    return _allow()


if __name__ == "__main__":
    sys.exit(main())
