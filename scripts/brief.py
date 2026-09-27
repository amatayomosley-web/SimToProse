#!/usr/bin/env python3
"""brief.py — what a spawn is handed: the showrunner's core plus the one playbook its direction names, or a
specialist's brief (gate partner-contracts).

The partner (docs/CONTRACTS.md) runs it and passes the whole output as a general-purpose subagent's prompt, so the
right playbook is in hand from the first line - nothing is left for the spawn to choose to read (cairn's lesson: skills
a model had to choose to load were never loaded). The showrunner builds its specialists' briefs the same way, which
works from a session opened in any folder (a subagent type is found only from the session's own folder).

    python scripts/brief.py <direction.json>                        the showrunner's brief, or a coded refusal
    python scripts/brief.py --specialist narrator [--input FILE]    that agent's brief (.claude/agents/<name>.md)
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import handoff                                        # noqa: E402
from src.engine.errors import EngineError                            # noqa: E402
from src.engine.records import RecordError                           # noqa: E402

AGENTS = os.path.join(REPO, ".claude", "agents")
PLAYBOOKS = os.path.join(REPO, ".claude", "showrunner", "playbooks")


def _body(path):
    """A markdown file without its YAML front matter."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        text = text[end + 4:] if end >= 0 else text
    return text.strip()


def _where():
    return ("\n\n---\nEngine folder: run every command from `%s` (e.g. `cd \"%s\"` first).\n" % (REPO, REPO))


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="the brief a showrunner or specialist spawn is handed")
    ap.add_argument("direction", nargs="?", help="the partner's direction (a JSON file)")
    ap.add_argument("--specialist", help="a specialist agent's name (a file in .claude/agents)")
    ap.add_argument("--input", help="the specialist's scoped input (a file), appended to its brief")
    a = ap.parse_args(argv)
    if a.specialist:
        path = os.path.join(AGENTS, "%s.md" % a.specialist)
        if not os.path.isfile(path) or a.specialist == "showrunner":
            names = sorted(f[:-3] for f in os.listdir(AGENTS) if f.endswith(".md") and f != "showrunner.md")
            print("brief.py: no specialist %r - one of %s" % (a.specialist, ", ".join(names)), file=sys.stderr)
            return 1
        extra = ""
        if a.input:
            with open(a.input, encoding="utf-8-sig") as fh:
                extra = "\n\n## Your input\n\n" + fh.read()
        print(_body(path) + extra + _where())
        return 0
    try:
        try:
            with open(a.direction or "", encoding="utf-8-sig") as fh:
                obj = json.load(fh)
        except (OSError, ValueError) as exc:
            raise RecordError("HANDOFF_DIRECTION_UNREADABLE", "%s: %s" % (a.direction, exc))
        direction, playbook = handoff.parse_direction(obj)
    except EngineError as exc:
        print("brief.py: %s" % exc, file=sys.stderr)
        return 1
    print(_body(os.path.join(AGENTS, "showrunner.md")))
    print("\n\n" + _body(os.path.join(PLAYBOOKS, "%s.md" % playbook)))
    print("\n\n## The direction\n\n```json\n%s\n```" % json.dumps(direction, indent=2, ensure_ascii=False) + _where())
    return 0


if __name__ == "__main__":
    sys.exit(main())
