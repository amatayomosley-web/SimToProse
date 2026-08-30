#!/usr/bin/env python3
"""ground_from_book.py — UserPromptSubmit. Put the facts in front of the model
BEFORE it answers.

THE HOOK THAT ACTUALLY GROUNDS. It is easy to reach for PreToolUse when asked to
enforce grounding, because a blocker feels like enforcement. But no hook can
un-say a sentence, so blocking cannot make an ANSWER truthful — it can only stop
an artifact. This one fires earlier, and everything it prints to stdout enters
the model's context for the turn.

    a block produces a REFUSAL; an injection produces a CORRECT ANSWER.

It reads the user's prompt, so retrieval is QUERY-AWARE — the laws and entities
it surfaces depend on what was asked, rather than dumping the same block every
turn until it becomes wallpaper.

FAILS OPEN. Unlike the write gates, a failure here must not block the turn: the
cost of a missing injection is an ungrounded answer, and the cost of denying is
a dead conversation. But it says so out loud rather than going quiet, because a
grounding layer that silently stops grounding is the failure this repo keeps
finding.
"""
import json
import os
import re
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BOOK_ENV = "SWE_ACTIVE_BOOK"        # the book this session is running
MAX_LAWS = 12
MAX_TERMS = 8
# Three characters, not four. The words that matter most in this domain are
# short — fly, die, god, war, vow, sin — and a four-character floor silently
# drops every one of them, which is how "query-aware" degrades to "wallpaper"
# without anything looking broken.
_WORD = re.compile(r"[a-z][a-z0-9_'-]{2,}")

# Words that match everything and therefore ground nothing.
_STOP = {
    "the", "and", "but", "for", "you", "her", "him", "his", "she", "they", "was", "are",
    "can", "did", "get", "got", "has", "had", "how", "its", "let", "not", "now", "one",
    "our", "out", "who", "why", "yes", "any", "all", "own", "too", "use", "way",
    "this", "that", "with", "from", "have", "what", "when", "where", "which", "would",
    "could", "should", "there", "their", "them", "then", "than", "been", "being",
    "about", "into", "just", "like", "make", "made", "does", "done", "book", "story",
    "scene", "chapter", "write", "written", "character", "characters", "world", "want",
    "going", "happen", "happens", "allowed", "across", "here", "over",
}


def _say(line=""):
    print(line)


def _terms(prompt):
    """Content words from the prompt — what makes this retrieval query-aware."""
    seen, out = set(), []
    for w in _WORD.findall(prompt.lower()):
        if w in _STOP or w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out[:MAX_TERMS]


def _resolve_book():
    """-> book dir, or None. Never guesses at a location on disk."""
    spec = os.environ.get(BOOK_ENV)
    if not spec:
        return None
    try:
        sys.path.insert(0, REPO)
        from src.engine import books                  # noqa: E402
        return books.resolve(spec)
    except Exception:
        return None


def _laws_and_position(book, terms):
    """The two things the orchestrator must never assert without: what the world
    forbids, and where the story is."""
    try:
        sys.path.insert(0, REPO)
        from src.engine import books                  # noqa: E402
    except Exception as e:
        _say("[grounding UNAVAILABLE: %s] Answer only from what is on screen; do not "
             "assert world-facts this turn." % e)
        return

    db = books.db_path(book)
    if not os.path.exists(db):
        _say("No chronicle yet for this book (%s). Nothing has happened that could be "
             "cited — treat every world-fact as unwritten." % os.path.basename(db))
        return

    con = None
    try:
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT run_id, config FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()
        if row is None:
            _say("The chronicle exists but holds no runs. Nothing is citable yet.")
            return
        run_id = row["run_id"]
        fp = None
        try:
            fp = (json.loads(row["config"]) or {}).get("bible_fingerprint")
        except Exception:
            pass

        turn = con.execute(
            "SELECT COUNT(*) c FROM events WHERE run_id=?", (run_id,)).fetchone()["c"]
        _say("ACTIVE BOOK: %s   run: %s   events: %d"
             % (os.path.basename(book), run_id, turn))

        if not fp:
            _say("This run pinned no bible (it predates bible-in-db). Laws are NOT "
                 "citable for it — say so rather than inventing one.")
            return

        laws = [dict(r) for r in con.execute(
            "SELECT law_id, modality, statement, teeth, epistemic FROM bible_laws "
            "WHERE fingerprint=? ORDER BY law_id", (fp,))]
        if not laws:
            _say("The pinned bible declares NO laws. The world cannot refuse anything yet.")
            return

        # Query-aware: laws whose text touches the prompt come first and in full.
        def touched(law):
            blob = ("%s %s" % (law["law_id"], law["statement"])).lower()
            return any(t in blob for t in terms)

        hits = [l for l in laws if touched(l)]
        rest = [l for l in laws if l not in hits]

        _say()
        _say("LAWS IN FORCE (%d; cite by law_id, never paraphrase as your own knowledge):"
             % len(laws))
        def line(l):
            # teeth ALWAYS, in both branches. A FORBIDS law without its
            # consequence is the half that makes crime writable — drop it and
            # the orchestrator reads the law as a plain prohibition.
            return "  %s [%s/%s] %s%s" % (
                l["law_id"], l["modality"], l["epistemic"], l["statement"],
                "  teeth: %s" % l["teeth"] if l["teeth"] else "")

        if hits:
            _say("  -- bearing on what was just asked --")
            for l in hits[:MAX_LAWS]:
                _say(line(l))
            _say("  -- also in force --")
        for l in rest[:max(0, MAX_LAWS - len(hits[:MAX_LAWS]))]:
            _say(line(l))
        if len(laws) > MAX_LAWS:
            _say("  ... %d more not shown; query the bible rather than guessing."
                 % (len(laws) - MAX_LAWS))
    except Exception as e:
        _say("[grounding FAILED: %s: %s] Do not assert world-facts this turn."
             % (type(e).__name__, e))
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:
                pass


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    prompt = str(payload.get("prompt") or payload.get("user_prompt") or "")

    book = _resolve_book()
    _say("=== SHOWRUNNER GROUNDING (engine-computed; this is the only world-truth "
         "you may assert without checking) ===")
    if book is None:
        _say("No active book. Set %s to a slug under $SWE_BOOKS to ground this session."
             % BOOK_ENV)
        _say("Until then you have NO citable world-facts: say what you do not know "
             "rather than filling it in.")
    else:
        _laws_and_position(book, _terms(prompt))
    _say("=== end grounding ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
