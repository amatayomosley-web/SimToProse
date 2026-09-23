"""swe_wake.py — SessionStart hook. What this repo contains, before you need it.

THE FAILURE THIS EXISTS TO PREVENT, measured 2026-07-25 in one session:
four of forty-eight design docs read; `docs/design.md` never opened despite
CLAUDE.md naming it normative; "vectors" coined for what `decision-engine.md`
already calls LEVERS, and a worse version of its buff/debuff registry rebuilt
from scratch — guardrails and falsification test included; and the showrunner
skill never loaded, so its THREE enforcement hooks were inactive for the whole
session. None of that was a knowledge failure. Every item was one grep away.
It was not knowing what was there.

WHY A HOOK AND NOT A DOC. `docs/MAP.md` holds the same routing table and is
pointed at from CLAUDE.md — and a pointer has to be chosen to be followed. The
session that wrote MAP.md then failed to load the showrunner skill listed in it.
Awareness has to ARRIVE, not be available.

WHY SESSIONSTART SPECIFICALLY (docs/MAP.md, hook-placement rule):
  SessionStart      once, sees nothing yet  -> INVENTORY: what exists
  UserPromptSubmit  before thinking         -> context needed while reasoning
  PreToolUse        before an act lands     -> gating a specific action
  Stop              after drafting, sees output -> catching what was done
Awareness goes early; verification goes late. An error-check at SessionStart
asks for a promise about a mistake not yet made — which is how guards become
wallpaper (measured: cairn's per-turn block fires full on 34% of turns and
caught none of the four failures above, because it guards sycophancy and these
were confident under-research).

BUDGET. Under 60 lines of output. This is paid at every session start in this
repo, so it stays an INDEX — never content. Every line either names something
that exists or gives a path. No craft, no facts about any book, no advice.

Stdlib only. Silent-failure discipline: a broken wake must never break a
session, so every read is guarded and the hook returns 0 on any error.
"""
from __future__ import annotations

__layer__ = "harness"

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
BOOKS_ENV = "SWE_BOOKS"


def _count(pattern: str, root: Path) -> int:
    try:
        return len(list(root.glob(pattern)))
    except Exception:
        return 0


def _names(d: Path) -> list[str]:
    try:
        return sorted(p.name for p in d.iterdir() if p.is_dir())
    except Exception:
        return []


def _books() -> list[str]:
    """Books on disk + whether each has a chronicle. Never guesses a location:
    an unset SWE_BOOKS is reported as unset, exactly as books.py does."""
    root = os.environ.get(BOOKS_ENV)
    if not root:
        return []
    out = []
    try:
        for d in sorted(Path(root).iterdir()):
            if not (d / "world").is_dir():
                continue
            runs = d / "runs"
            n = len(list(runs.glob("*.db"))) if runs.is_dir() else 0
            slug = d.name.lower().replace(" ", "-")
            out.append("%s%s" % (slug, "  (has chronicle)" if n else "  (never run)"))
    except Exception:
        pass
    return out


def _active_ledger() -> str:
    """The cairn ledger for THIS session, if the id is in the environment.
    Pointer only -- never the contents (0022: pointer, not payload)."""
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if not sid:
        return ""
    p = Path.home() / "cairn" / "ledgers" / ("%s.md" % sid)
    return str(p) if p.exists() else ""


def main() -> int:
    try:
        docs = _count("*.md", REPO / "docs")
        engine = _count("*.py", REPO / "src" / "engine")
        tests = _count("test_*.py", REPO / "tests")
        agents = _count("*.md", REPO / ".claude" / "agents")
        skills = _names(REPO / ".claude" / "skills")

        L = [
            "=== simulated-world-evolve -- Wake ===",
            "",
            "An INSTANCE of SimToProse, not the template. It is SUPPOSED to diverge:",
            "real books, real runs, machine-local config. Books NEVER live in this repo.",
            "",
            "READ docs/MAP.md BEFORE REASONING ABOUT THE ENGINE. It carries the ROUTING",
            "table (which of the %d docs owns your question) and the VOCABULARY table." % docs,
            "Skipping it cost a full session on 2026-07-25: a parallel vocabulary invented",
            "for terms the project already had, and a mechanism rebuilt that was already",
            "specified in docs/decision-engine.md.",
            "",
            "-- VOCABULARY (say these, not synonyms) ------------------------------",
            "  lever          a bounded authorable quantity. NOT 'vector', NOT 'axis'.",
            "  buff/debuff    {trigger, lever, op, magnitude, source} -- the modifier schema",
            "  model          a bias-pack over the lever catalogue (bias, never set)",
            "  direction      numbers translated to prose; the ONLY form state enters a prompt",
            "  the cut        the selected biography. Selection, never invention.",
            "  faithful refusal   a character declining a beat -> the BEAT is wrong",
            "",
            "-- WHAT EXISTS -------------------------------------------------------",
            "  docs/           %2d design docs   (normative for what SHOULD BE)" % docs,
            "  src/engine/     %2d modules        (normative for what IS)" % engine,
            "  tests/          %2d suites         (each PROVES the gate it names)" % tests,
            "  .claude/agents/ %2d agents" % agents,
            "  .claude/skills/ %2d skills: %s" % (len(skills), ", ".join(skills[:6])),
            "                     %s" % ", ".join(skills[6:]) if len(skills) > 6 else "",
            "",
            "  ** If the work is on a BOOK, load the `showrunner` skill FIRST. **",
            "     Its value is not the prose -- it declares THREE HOOKS in its frontmatter",
            "     that exist only while it is loaded: ground_from_book (injects the book's",
            "     laws + story position each turn), citation_gate (blocks an uncitable claim",
            "     from becoming a written record), beat_blind_guard (keeps a spawned",
            "     simulator from learning the intended beat).",
            "",
        ]

        books = _books()
        if books:
            L.append("-- BOOKS ON DISK ($%s) ---------------------------------" % BOOKS_ENV)
            L += ["  %s" % b for b in books]
        else:
            L.append("-- BOOKS: $%s is UNSET. Slug resolution is dead until it is set." % BOOKS_ENV)
        L.append("")

        led = _active_ledger()
        if led:
            L += ["-- PRIOR DECISIONS are banked, not remembered ------------------------",
                  "  %s" % led,
                  "  Re-read it before re-deciding anything. Most of what would be",
                  "  reinvented is already written down.", ""]

        L += ["-- HARD RULES (CLAUDE.md has the full text) --------------------------",
              "  1 no book content in src/engine/ | REAL BOOKS NEVER IN THIS REPO",
              "  2 the log is append-only -- corrections are new events",
              "  3 no LLM calls inside src/engine/   4 no randomness in the engine",
              "  5 numbers never reach the prompt    7 code writes need a depth gate",
              "",
              "  Verify after ANY change: the 10-suite block in CLAUDE.md, then",
              "  coherence_probe.py --stub (must PASS) and --corrupt (must FAIL).",
              "  tests/test_no_private_content.py is EXPECTED TO FAIL here -- this is",
              "  the instance, not the template. Never 'fix' it by scrubbing a book.",
              "=== end wake ==="]

        print("\n".join(x for x in L if x is not None))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
