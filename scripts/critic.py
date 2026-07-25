#!/usr/bin/env python3
"""critic.py — the continuity + voice critic (design.md layer 6, the non-author check).

Reviews a CANONIZED scene against the world's canon + the scene's own transcript, flagging
CONTINUITY problems (a statement or action that contradicts an established world-fact or an earlier
line) and VOICE problems (two characters who read alike — a reader couldn't tell who is speaking).
A strong-model judgment: the hybrid architecture's editing tier (William, 2026-06-13) — the cheap
local model does the acting, the strong model (Claude via OpenRouter) does the judging, per the
model-tiering rule. Detect-and-report; the rewrite / compensating-event half is the layer above
(a follow-on gate). Harness-layer — the engine never calls models. Stub-testable (no API).

Usage:
  python scripts/critic.py --vault "<book>" --run <run_id>            # strong-model review
  python scripts/critic.py --vault "<book>" --run <run_id> --stub     # clean review, no API
"""
import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.ledger import Ledger                                 # noqa: E402
from direct import _openrouter                                      # noqa: E402  (reuse the harness's strong-model dispatch)

# Strong-stage model. PRIMARY path is Claude-in-the-loop (--prompt-only — key-free; the script emits
# the prompt, Claude-in-a-session produces the review). This OpenRouter slug is the key-GATED fallback
# (the sim is local-only and the OpenRouter key is intentionally removed; re-adding it is a William call).
DEFAULT_CRITIC_MODEL = "anthropic/claude-sonnet-4.6"


def scene_turns(led, run_id):
    """The committed turns of a run, in turn order — the canonized scene the critic reads."""
    rows = led.con.execute(
        "SELECT turn, actor, action, thought FROM turns WHERE run_id=? ORDER BY turn", (run_id,)).fetchall()
    return [{"turn": r["turn"], "actor": r["actor"], "action": r["action"], "thought": r["thought"]} for r in rows]


def _name_of(p):
    if not isinstance(p, dict):
        return str(p)
    return str(p.get("name") or p.get("what") or p.get("id") or "")


def build_critic_prompt(turns, world):
    """Build the critic messages: the world's canon (standing facts + who + where) + the scene
    transcript, asking for continuity contradictions and voice-distinctness issues as strict JSON.
    The critic does NOT rewrite here — it flags. An empty list is the correct answer for a clean scene."""
    facts = world.get("standing_facts", []) or []
    facts_txt = "\n".join("- %s" % f for f in facts) if isinstance(facts, list) else json.dumps(facts)[:1500]
    who = "; ".join("%s = %s" % (p.get("id", "?"), _name_of(p)) for p in world.get("people", []) if isinstance(p, dict))
    where = "; ".join("%s = %s" % (l.get("id", "?"), l.get("what", "")) for l in world.get("locations", []) if isinstance(l, dict))
    transcript = "\n".join(
        "[%d] %s: %s" % (t["turn"], t["actor"], str(t["action"]).replace("\n", " ")) for t in turns)
    sys_msg = (
        "You are a CONTINUITY + VOICE critic for a novel-in-progress. You are NOT the author and you do "
        "not rewrite. You read one scene's transcript against the world's established canon and report "
        "problems as JSON. Two jobs:\n"
        "(1) CONTINUITY — any statement or action that contradicts an established world-fact, the cast/"
        "place facts, or an EARLIER line in this same transcript.\n"
        "(2) VOICE — any two characters whose lines are indistinguishable (a reader could not tell who "
        "is speaking).\n"
        "Report ONLY real problems. An empty list is the correct, expected answer for a clean scene — "
        "do not invent issues to seem useful.")
    user_msg = (
        "WORLD FACTS (canon — must not be contradicted):\n%s\n\n"
        "WHO: %s\nWHERE: %s\n\n"
        "SCENE TRANSCRIPT:\n%s\n\n"
        "Return ONLY this JSON, nothing else:\n"
        '{"continuity": [{"turn": <int>, "issue": "<what contradicts what>"}], '
        '"voice": [{"chars": ["<id>", "<id>"], "issue": "<why indistinguishable>"}]}'
        % (facts_txt[:2500], who[:1200], where[:1200], transcript[:6000]))
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]


def review_scene(turns, world, model=DEFAULT_CRITIC_MODEL, stub=False):
    """Strong-model continuity+voice review of a canonized scene. Returns {"continuity": [...],
    "voice": [...]}. Stub (or an empty scene): a clean review — deterministic, no API. The strong
    model's reply is parsed leniently (first JSON object); a malformed reply yields empty lists
    (fail-soft on the PARSE only — a non-answer is not a false flag; the run itself fails loud)."""
    if stub or not turns:
        return {"continuity": [], "voice": []}
    messages = build_critic_prompt(turns, world)
    raw = _openrouter(messages, model, max_tokens=1200)
    m = re.search(r"\{.*\}", raw or "", re.DOTALL)
    try:
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        d = {}
    cont = d.get("continuity") if isinstance(d.get("continuity"), list) else []
    voice = d.get("voice") if isinstance(d.get("voice"), list) else []
    return {"continuity": cont, "voice": voice}


def main():
    ap = argparse.ArgumentParser(description="the continuity + voice critic — review a canonized scene")
    ap.add_argument("--vault", required=True, help="the BOOK folder (vault)")
    ap.add_argument("--run", required=True, help="run_id to review")
    ap.add_argument("--db", default=None, help="chronicle db path (default <vault>/runs/<book>.db)")
    ap.add_argument("--model", default=DEFAULT_CRITIC_MODEL)
    ap.add_argument("--stub", action="store_true", help="clean review, no API (deterministic)")
    ap.add_argument("--prompt-only", action="store_true", dest="prompt_only",
                    help="print the strong-model prompt (JSON) instead of calling an API — hand it to Claude-in-the-loop (key-free)")
    args = ap.parse_args()

    from src.engine.vault import load_book
    world, _chars = load_book(args.vault)
    book_name = os.path.basename(os.path.normpath(args.vault)).lower().replace(" ", "-")
    led = Ledger(args.db or os.path.join(args.vault, "runs", "%s.db" % book_name))
    turns = scene_turns(led, args.run)
    if args.prompt_only:                               # Claude-in-the-loop: emit the prompt, Claude produces the review
        print(json.dumps(build_critic_prompt(turns, world), indent=2))
        return 0
    report = review_scene(turns, world, args.model, args.stub)
    print(json.dumps(report, indent=2))
    n = len(report["continuity"]) + len(report["voice"])
    print("\ncritic: %d flag(s) over %d turn(s)%s" % (n, len(turns), " — clean" if n == 0 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
