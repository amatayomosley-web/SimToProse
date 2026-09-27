#!/usr/bin/env python3
"""profile.py — the session profile: set once when a session opens, passed to every run until it closes (gate
session-profile).

The owner, 2026-09-27: "you open a session prepare how you want it ran and then it continues until close". The partner
asks the author once (docs/CONTRACTS.md section 0) and writes the answer with this script; `scripts/brief.py --profile`
and `scripts/scene.py --profile` read it. Which model each role needs, and why: docs/guide-model-roles.md. The table
and the floors are src/engine/roles.py.

    python scripts/profile.py new --out FILE [--preset standard|local|subagents] [--set ROLE=MODEL ...]
    python scripts/profile.py show FILE

The presets differ only in the seats:
  standard   OpenRouter at the pinned frontier model (a key file is needed: scripts/provider.py)
  local      the actor's own local model - no key, no spend, below the seats' floor (a warning names the trade)
  subagents  no key - one fresh Opus agent answers each seat prompt (Claude tokens: one spawn per prompt)
"""
import argparse
import datetime
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import roles                                          # noqa: E402
from src.engine.errors import EngineError                            # noqa: E402
from src.engine.records import RecordError                           # noqa: E402
import direct                                                        # noqa: E402  (the actor's default model)
import provider                                                      # noqa: E402  (the seats' default model)

PRESETS = ("standard", "local", "subagents")


def build(preset="standard", sets=()):
    """(a preset, ROLE=MODEL overrides) -> (the profile, its warnings); refused (ROLES_*) before anything is written.
    Every role is written out, defaults included, so the author sees exactly what the session runs."""
    chosen = {}
    for item in sets:
        role, _, value = item.partition("=")
        if not role or not value:
            raise RecordError("ROLES_PROFILE_UNREADABLE", "--set takes ROLE=MODEL, not %r" % item)
        chosen[role.strip()] = value.strip()
    out = {"actor": chosen.get("actor", direct.DEFAULT_MODEL)}
    out["seats"] = chosen.get("seats") or {"standard": provider.DEFAULT_SEAT_MODEL, "local": out["actor"],
                                           "subagents": "subagent:opus"}[preset]
    out.update(roles.AGENT_DEFAULTS)
    out.update({r: v for r, v in chosen.items() if r not in ("actor", "seats")})
    profile = {"profile": 1, "preset": preset, "made": datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"), "roles": out}
    _roles, warnings = roles.check(profile)
    return profile, warnings


def summary(profile_roles, warnings):
    """The profile as the author reads it: one line per role, then the warnings."""
    lines = ["  %-20s %-34s %s" % (r, v, roles.class_of(r, v)) for r, v in profile_roles.items()]
    return "\n".join(lines + ["  warning: %s" % w for w in warnings])


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="the session profile - which model fills each role")
    sub = ap.add_subparsers(dest="cmd", required=True)
    new = sub.add_parser("new", help="write this session's profile")
    new.add_argument("--out", required=True, help="the profile file (keep it in the session's own scratch folder)")
    new.add_argument("--preset", choices=PRESETS, default="standard")
    new.add_argument("--set", action="append", default=[], metavar="ROLE=MODEL")
    show = sub.add_parser("show", help="read a profile back, with its warnings")
    show.add_argument("file")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "new":
            profile, warnings = build(a.preset, a.set)
            with open(a.out, "w", encoding="utf-8") as fh:
                json.dump(profile, fh, indent=1)
            print("profile: %s (%s)\n%s" % (a.out, a.preset, summary(profile["roles"], warnings)))
        else:
            profile_roles, warnings = roles.load(a.file)
            print("profile: %s\n%s" % (a.file, summary(profile_roles, warnings)))
    except EngineError as exc:
        print("profile.py: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
