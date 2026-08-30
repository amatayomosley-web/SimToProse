#!/usr/bin/env python3
"""beat_blind_guard.py — PreToolUse on Task. The simulator's wall, enforced.

THE RULE (`showrunner.md`): keep the character-simulator BEAT-BLIND — never pass
it the director's intended outcome. It is the load-bearing wall of the whole
design. A character told what is supposed to happen will produce it, and the
probe becomes a machine for confirming the director's guess instead of a test of
whether a real person would move. The refusal that makes the system honest — "no
lever works, revise the beat" — is unreachable once the wall leaks.

Until now the wall was prose in an agent file, which means it held exactly as
well as attention held. This denies the spawn.

SCOPED AND DUMB, on purpose. It fires only on a Task whose target is the
simulator, and it matches directive language about intended outcome. It does not
try to infer intent from tone. A guard that gets clever produces false denials,
and a guard that produces false denials gets switched off.

FAILS CLOSED on its own breakage, like the other write-path gates: a wall that
stops guarding while reporting success is the failure this repo keeps finding.
"""
import json
import re
import sys

# MEASURED, not assumed. The frontmatter MATCHER accepts "Task", but the payload
# the harness actually delivers reports `tool_name: "Agent"`. The first version of
# this guard tested `!= "Task"` and therefore allowed every spawn — a dead wall,
# shipped green, because the test fed it the same invented name the code expected.
# A fixture cannot validate its own shape; only a captured payload can. Both names
# are accepted so the guard survives whichever the harness sends.
_SPAWN_TOOLS = ("Task", "Agent")

_SIMULATOR_HINTS = ("character-simulator", "character_simulator", "simulator")

# Directive language about what the turn is FOR. Each pattern names an outcome
# the character is not allowed to be told about.
_BEAT_LEAKS = (
    (r"\bthe\s+(?:intended|planned|desired|target)\s+(?:beat|outcome|result|ending)\b",
     "names the intended outcome"),
    (r"\b(?:the\s+)?beat\s*(?:is|:)\s*\S", "states the beat"),
    (r"\b(?:should|must|needs?\s+to|has\s+to|is\s+meant\s+to)\s+(?:end\s+up|conclude|"
     r"decide|choose|refuse|agree|leave|stay|die|kill|confess|betray)\b",
     "prescribes the character's choice"),
    (r"\bmake\s+(?:her|him|them|the\s+character)\s+\w+", "instructs the outcome"),
    (r"\bso\s+that\s+(?:she|he|they)\s+(?:will|would|can)\b", "supplies the purpose"),
    (r"\bdirector'?s?\s+(?:intent|intention|plan|goal|beat)\b", "passes director intent"),
    (r"\bwe\s+need\s+(?:her|him|them)\s+to\b", "states the required result"),
)


def _allow():
    return 0


def _deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    return 0


def _targets_simulator(tool_input):
    target = " ".join(str(tool_input.get(k) or "") for k in
                      ("subagent_type", "description")).lower()
    return any(h in target for h in _SIMULATOR_HINTS)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return _allow()
    if not isinstance(payload, dict):
        return _allow()                       # a list/scalar is not an event we own

    if payload.get("tool_name") not in _SPAWN_TOOLS:
        return _allow()

    try:
        tool_input = payload.get("tool_input") or {}
        if not _targets_simulator(tool_input):
            return _allow()               # a different specialist — not this wall

        prompt = str(tool_input.get("prompt") or "")
        hits = [why for pat, why in _BEAT_LEAKS
                if re.search(pat, prompt, re.IGNORECASE)]
    except Exception as e:
        return _deny("beat-blind guard CANNOT RUN (%s: %s). Denying rather than allowing — "
                     "a wall that stops guarding while reporting success is worse than no "
                     "wall." % (type(e).__name__, e))

    if hits:
        return _deny(
            "beat-blind guard: DENIED. This spawn tells the character-simulator what is "
            "supposed to happen (%s). A character handed the intended outcome will produce "
            "it, and the honest refusal — 'no lever works, revise the beat' — becomes "
            "unreachable. Send the CIRCUMSTANCE and the character's own packet; let the "
            "director judge the result afterwards." % "; ".join(sorted(set(hits))))

    return _allow()


if __name__ == "__main__":
    sys.exit(main())
