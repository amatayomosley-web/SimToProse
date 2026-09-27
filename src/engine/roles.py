"""roles.py — the session profile: which model fills each role, and the floor each must meet (gate session-profile).

The owner, 2026-09-27: "we can set it per session. That way you open a session prepare how you want it ran and then it
continues until close" - and "the show runner can't be a qwen 7B". `docs/guide-model-roles.md` is the reasoning; this
is its table. A PROFILE is one JSON object, `{"profile": 1, "roles": {role: value}}`, written once per session by
`scripts/profile.py` and passed to every `scripts/brief.py` and `scripts/scene.py` call.

TWO KINDS OF FLOOR. `check` REFUSES what cannot do the job at all - an agent role on anything but a Claude model (an
agent drives Claude Code's tools; a local chat model cannot), and a showrunner below Mid (it holds a playbook, a fixed
command list and a report shape over many steps). Every other floor is ADVICE: it WARNS, naming the role and the trade,
and the profile stands - the owner made the seats' backend the author's choice, so a draft on local seats is a knowing
trade, never a refusal.

VALUES. An ENGINE role (a single call a script makes) takes `ollama/<model>` (local), an OpenRouter id such as
`anthropic/claude-opus-5`, or `subagent:<tier>` (the replay backend: one fresh agent of that Claude tier answers each
prompt). An OpenRouter id this table cannot place carries its class after an `@` (`qwen/qwen3-235b@mid`), written by
the author, so no model is ranked by a guess - and so does a subagent that is not Claude (`subagent:gemini@top`),
so the record names what actually answered. An AGENT role takes a Claude tier: haiku, sonnet, opus or fable.
"""
import json

from .records import RecordError

#: capability classes, weakest first (docs/guide-model-roles.md "The classes, by capability")
CLASSES = ("local", "small", "mid", "top")
_RANK = {c: i for i, c in enumerate(CLASSES)}

#: the Claude tiers an agent can be spawned at, and their class
TIERS = {"haiku": "small", "sonnet": "mid", "opus": "top", "fable": "top"}

#: OpenRouter id prefixes this table can place
_KNOWN = (("anthropic/claude-opus", "top"), ("anthropic/claude-fable", "top"),
          ("anthropic/claude-sonnet", "mid"), ("anthropic/claude-haiku", "small"))

#: role -> (kind, floor class, hard floor?, what it is) - the agent names are the files in .claude/agents
ROLES = {
    "actor":               ("engine", "local", False, "plays one character's beat; the composer follows it"),
    "seats":               ("engine", "top", False, "the event and emotion seats, the keeper and the thermometer"),
    "showrunner":          ("agent", "mid", True, "runs one scene from its playbook and reports"),
    "director":            ("agent", "top", False, "shapes a scene toward the author's agreed story"),
    "narrator":            ("agent", "top", False, "writes the prose"),
    "recorder":            ("agent", "top", False, "reviews flagged consolidation - the error class that compounds"),
    "cutter":              ("agent", "top", False, "turns recorded lives into the novel's scene list"),
    "world-builder":       ("agent", "top", False, "authors the world"),
    "character-generator": ("agent", "top", False, "authors the characters"),
    "continuity-critic":   ("agent", "mid", False, "checks a recorded scene's continuity and voice"),
    "character-simulator": ("agent", "small", False, "plays a beat when an agent acts instead of the local model"),
    "appraiser":           ("agent", "top", False, "the event seat, answered by an agent"),
}

#: the agent roles' defaults - the guide's floors, at today's tiers; engine defaults come from the scripts themselves
AGENT_DEFAULTS = {"showrunner": "sonnet", "director": "opus", "narrator": "opus", "recorder": "opus", "cutter": "opus",
                  "world-builder": "opus", "character-generator": "opus", "continuity-critic": "sonnet",
                  "character-simulator": "sonnet", "appraiser": "opus"}


def class_of(role, value):
    """A role's value -> its capability class; refused (ROLES_*) when it cannot be placed or cannot fill the role."""
    kind = ROLES[role][0]
    if not isinstance(value, str) or not value.strip():
        raise RecordError("ROLES_MODEL_UNKNOWN", "%s: %r is not a model" % (role, value))
    if kind == "agent":
        if value not in TIERS:
            raise RecordError("ROLES_CLAUDE_ONLY", "%s is an agent role - it drives Claude Code's tools, so it runs on "
                              "a Claude tier (%s), not %r" % (role, ", ".join(TIERS), value))
        return TIERS[value]
    if value.startswith("ollama/"):
        return "local"
    if value.startswith("subagent:") and "@" not in value:      # a Claude tier; any other answerer states its class
        tier = value[len("subagent:"):]
        if tier not in TIERS:
            raise RecordError("ROLES_MODEL_UNKNOWN", "%s: %r - a subagent answers at a Claude tier (%s)"
                              % (role, value, ", ".join(TIERS)))
        return TIERS[tier]
    if "@" in value:
        declared = value.rsplit("@", 1)[1]
        if declared not in _RANK:
            raise RecordError("ROLES_MODEL_UNKNOWN", "%s: %r - the class after @ is one of %s"
                              % (role, value, ", ".join(CLASSES)))
        return declared
    for prefix, cls in _KNOWN:
        if value.startswith(prefix):
            return cls
    raise RecordError("ROLES_MODEL_UNKNOWN", "%s: %r is not a model this table can place - write its class after "
                      "an @ (e.g. %s@mid), or use ollama/<model> or subagent:<tier>" % (role, value, value))


def model_id(value):
    """The value as the provider sees it: an author's `@class` is the profile's note, never part of the model id."""
    return value.rsplit("@", 1)[0] if "@" in value and not value.startswith("subagent:") else value


def check(profile):
    """A profile -> (its roles, the warnings to show the author). Refused (ROLES_*) when it is not a profile, names a
    role this table does not have, or puts a role below a HARD floor; every other floor below its class only warns."""
    if not isinstance(profile, dict) or profile.get("profile") != 1 or not isinstance(profile.get("roles"), dict):
        raise RecordError("ROLES_PROFILE_UNREADABLE", "a profile is {\"profile\": 1, \"roles\": {role: model}} - "
                          "scripts/profile.py writes one")
    roles, warnings = dict(profile["roles"]), []
    unknown = sorted(r for r in roles if r not in ROLES)
    if unknown:
        raise RecordError("ROLES_UNKNOWN", "%s - the roles are %s" % (", ".join(unknown), ", ".join(ROLES)))
    for role, value in roles.items():
        _kind, floor, hard, what = ROLES[role]
        cls = class_of(role, value)
        if _RANK[cls] < _RANK[floor]:
            if hard:
                raise RecordError("ROLES_BELOW_FLOOR", "%s (%s) needs at least %s; %r is %s"
                                  % (role, what, floor, value, cls))
            warnings.append("%s is below its floor: %r is %s, the guide advises %s (%s) - a knowing trade"
                            % (role, value, cls, floor, what))
    return roles, warnings


def load(path):
    """A profile file -> (its roles, its warnings); ROLES_PROFILE_UNREADABLE when it cannot be read as JSON."""
    try:
        with open(path, encoding="utf-8-sig") as fh:
            obj = json.load(fh)
    except (OSError, ValueError) as exc:
        raise RecordError("ROLES_PROFILE_UNREADABLE", "%s: %s" % (path, exc))
    return check(obj)
