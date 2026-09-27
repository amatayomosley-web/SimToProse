#!/usr/bin/env python3
"""seats.py — the subagent seats' helper: which seat prompts wait for an answer, and the brief that answers one (gate
session-profile).

A session whose profile puts the seats on `subagent:<tier>` runs every seat call through the replay backend
(scripts/provider.py): the run writes each prompt to `<book>/runs/seats/<key>.prompt.json` and waits until
`<key>.reply.txt` appears beside it. The showrunner runs the scene in the background and, until it ends, answers each
waiting prompt with ONE fresh agent (the scene playbook). A fresh agent per prompt is the wall: an agent that has seen
another answer is no longer blind to it. Lifted from the drive loop of 2026-09-19, which answered every seat of the
first generated scenes this way.

    python scripts/seats.py pending DIR [--log SCENE_LOG] [--wait SECONDS]
        PENDING <key> <purpose> turn=<t> per unanswered prompt, oldest first (exit 0); ENDED when the log shows
        the run has stopped (exit 2); TIMEOUT when nothing arrived within --wait (exit 3)
    python scripts/seats.py brief DIR KEY
        the answering agent's whole brief: .claude/agents/seat.md with this prompt's files named
"""
import argparse
import glob
import io
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEAT_AGENT = os.path.join(REPO, ".claude", "agents", "seat.md")
#: what a scene's output shows once the run has stopped - parked, refused, or crashed
ENDED = ("\nparked ", "== scene ended", "Traceback", "SystemExit", "[CONTRACT_RUN_REFUSED]")


def pending(folder):
    """Unanswered prompts in `folder`, oldest first -> [(key, purpose, turn)]."""
    out = []
    for p in sorted(glob.glob(os.path.join(folder, "*.prompt.json")), key=os.path.getmtime):
        key = os.path.basename(p)[:-len(".prompt.json")]
        if os.path.isfile(os.path.join(folder, key + ".reply.txt")):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                row = json.load(fh)
        except (OSError, ValueError):
            continue                                                # still being written: the next look finds it
        out.append((key, row.get("purpose"), (row.get("meta") or {}).get("turn")))
    return out


def ended(log):
    """Whether a scene's output shows the run has stopped."""
    try:
        with io.open(log, encoding="utf-8", errors="replace") as fh:
            tail = fh.read()[-4000:]
    except OSError:
        return False
    return any(mark in tail for mark in ENDED)


def brief(folder, key):
    """The seat agent's brief for one prompt: the agent file's body with the two files it reads and writes named."""
    with io.open(SEAT_AGENT, encoding="utf-8") as fh:
        text = fh.read()
    if text.startswith("---"):
        text = text[text.find("\n---", 3) + 4:]
    folder = os.path.abspath(folder).replace(os.sep, "/")
    return (text.strip() + "\n\n## Your prompt\n\n- read: `%s/%s.prompt.json` (and the system file it names, beside it)"
            "\n- write: `%s/%s.reply.txt`\n" % (folder, key, folder, key))


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="the subagent seats' helper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("pending", help="list the seat prompts waiting for an answer")
    pe.add_argument("folder")
    pe.add_argument("--log", help="the scene's output file - its end stops the wait")
    pe.add_argument("--wait", type=float, default=0.0, help="seconds to wait for a prompt to arrive (0: look once)")
    br = sub.add_parser("brief", help="print the answering agent's brief for one prompt")
    br.add_argument("folder")
    br.add_argument("key")
    a = ap.parse_args(argv)
    if a.cmd == "brief":
        print(brief(a.folder, a.key))
        return 0
    deadline = time.monotonic() + max(0.0, a.wait)
    while True:
        waiting = pending(a.folder)
        if waiting:
            for key, purpose, turn in waiting:
                print("PENDING %s %s turn=%s" % (key, purpose, turn))
            return 0
        if a.log and ended(a.log):
            print("ENDED")
            return 2
        if time.monotonic() >= deadline:
            print("TIMEOUT")
            return 3
        time.sleep(min(3.0, max(0.05, deadline - time.monotonic())))


if __name__ == "__main__":
    sys.exit(main())
