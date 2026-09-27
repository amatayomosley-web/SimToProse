#!/usr/bin/env python3
"""brief.py — the partner's hand-over: a spawn's brief, or a mechanical step run straight away (gates
partner-contracts, partner-runs-mechanical).

The partner (docs/CONTRACTS.md) runs it on a direction. A SCENE needs judgment and specialists, so it prints the
showrunner's whole brief - the core plus the scene playbook plus the direction - to pass as a general-purpose
subagent's prompt; nothing is left for the spawn to choose to read. A RECORD step (adopt, approve, reject, rewind,
release) and a DECLARATION are mechanical, and a spawn would pay about 70k tokens of opening context to run one to
three commands (measured, cairn_spawn_overhead.py) - so `--run` checks the direction and runs them itself. The
showrunner builds its specialists' briefs here too, which works from a session opened in any folder.

    python scripts/brief.py <direction.json>                        a spawn's brief, or a coded refusal
    python scripts/brief.py --run <direction.json>                  a record step or declaration, run now
    python scripts/brief.py --specialist narrator [--input FILE]    that agent's brief (.claude/agents/<name>.md)
"""
import argparse
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import books, drafts, handoff                         # noqa: E402
from src.engine.errors import EngineError                            # noqa: E402
from src.engine.records import RecordError                           # noqa: E402

AGENTS = os.path.join(REPO, ".claude", "agents")
PLAYBOOKS = os.path.join(REPO, ".claude", "showrunner", "playbooks")
DRAFT = os.path.join(REPO, "scripts", "draft.py")


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


def _argv(d, book_dir):
    """A record direction -> its one draft.py command as an argument list - the one source for both the spawn's brief
    and --run, and nothing for a shell to mangle. The author's words go through exactly as given, marked relayed."""
    words = d.get("words") or d.get("note") or ""
    kind, book = d["kind"], ["--book", book_dir]
    tail = {"adopt": ["adopt"] + book,
            "approve": ["promote"] + book + ["--draft", d.get("draft", ""), "--approved", words, "--by", "partner-relayed"]
                       + (["--in-advance"] if d.get("in_advance") else []),
            "reject": ["reject"] + book + ["--draft", d.get("draft", ""), "--why", words],
            "rewind": ["restore"] + book + ["--to", d.get("to", ""), "--approved", words, "--by", "partner-relayed"],
            "release": ["release"] + book + ["--approved", words, "--by", "partner-relayed"]}[kind]
    return [sys.executable, DRAFT] + tail


def _sh(text):
    """An argument for a bash line, exactly as given - quoted unless it is plainly safe."""
    text = str(text)
    if text and all(c.isalnum() or c in "-_./:" for c in text):
        return text
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")


def _record_step(d):
    """A record direction -> a spawn's whole brief: the one command and the report shape."""
    argv = _argv(d, books.resolve(d["book"]).replace(os.sep, "/"))
    return ("# Showrunner — one record step\n\nMake exactly ONE Bash call - this command - then answer. No other tool "
            "call, no reads, no checks:\n\n    cd \"%s\" && python scripts/draft.py %s\n\nThen your whole answer is "
            "this JSON:\n\n```json\n{\"status\": \"done | refused\", \"kind\": \"%s\", \"draft\": \"%s\", \"summary\": "
            "\"<the line the command printed>\", \"refusal\": \"<its error line, if it failed>\"}\n```\n"
            % (REPO.replace(os.sep, "/"), " ".join(_sh(a) for a in argv[2:]), d["kind"], d.get("draft", "")))


def _run_direction(d, playbook):
    """Run a record step or a declaration now -> the exit status. A declaration on an adopted book is opened as a
    draft, declared, and promoted in advance on the author's words; a refused declaration's draft is set aside."""
    book_dir = books.resolve(d["book"])
    if playbook == "record":
        return subprocess.call(_argv(d, book_dir), cwd=REPO)
    if d["kind"] != "declare":
        raise RecordError("HANDOFF_NEEDS_SPAWN", "a %s needs judgment and a specialist - pass `brief.py <direction>`'s "
                          "output to the %s instead of --run" % (d["kind"], "showrunner" if d["kind"] == "scene"
                                                                   else "narrator (docs/CONTRACTS.md)"))
    declare = [sys.executable, os.path.join(REPO, "scripts", "declare.py"), "--book", book_dir, "--run", d["run"],
               "--file", d["file"]]
    if not drafts.adopted(book_dir):
        return subprocess.call(declare, cwd=REPO)
    opened = subprocess.run([sys.executable, DRAFT, "open", "--book", book_dir, "--note", "declaration"], cwd=REPO,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    sys.stdout.write(opened.stdout)
    sys.stderr.write(opened.stderr)
    path = next((l[len("draft: "):].strip() for l in opened.stdout.splitlines() if l.startswith("draft: ")), "")
    if opened.returncode or not path:
        return opened.returncode or 1
    did = os.path.basename(path)[:-3]
    rc = subprocess.call(declare + ["--db", path], cwd=REPO)
    if rc:
        subprocess.call([sys.executable, DRAFT, "reject", "--book", book_dir, "--draft", did, "--why",
                         "the declaration was refused"], cwd=REPO)
        return rc
    return subprocess.call([sys.executable, DRAFT, "promote", "--book", book_dir, "--draft", did, "--approved",
                            d["words"], "--by", "partner-relayed", "--in-advance"], cwd=REPO)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="the partner's hand-over: a spawn's brief, or a mechanical step run now")
    ap.add_argument("direction", nargs="?", help="the partner's direction (a JSON file)")
    ap.add_argument("--run", action="store_true", help="run a record step or a declaration now instead of briefing")
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
        if a.run:
            return _run_direction(direction, playbook)
        if playbook == "record":
            print(_record_step(direction))
            return 0
    except EngineError as exc:
        print("brief.py: %s" % exc, file=sys.stderr)
        return 1
    print(_body(os.path.join(AGENTS, "showrunner.md")))
    print("\n\n" + _body(os.path.join(PLAYBOOKS, "%s.md" % playbook)))
    print("\n\n## The direction\n\n```json\n%s\n```" % json.dumps(direction, indent=2, ensure_ascii=False) + _where())
    return 0


if __name__ == "__main__":
    sys.exit(main())
