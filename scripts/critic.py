#!/usr/bin/env python3
"""critic.py — the continuity + voice critic (design.md layer 6, the non-author check).

Reviews a CANONIZED scene against the world's canon + the scene's own transcript, flagging
CONTINUITY problems (a statement or action that contradicts an established world-fact or an earlier
line) and VOICE problems (two characters who read alike — a reader couldn't tell who is speaking).
A strong-model judgment: the hybrid architecture's editing tier (the author, 2026-06-13) — the cheap
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

from src.engine import books                                    # noqa: E402  (the one db-path definition)
from src.engine.ledger import Ledger                                 # noqa: E402
from direct import _openrouter                                      # noqa: E402  (reuse the harness's strong-model dispatch)

# Strong-stage model. PRIMARY path is Claude-in-the-loop (--prompt-only — key-free; the script emits
# the prompt, Claude-in-a-session produces the review). This OpenRouter slug is the key-GATED fallback
# (the sim is local-only and the OpenRouter key is intentionally removed; re-adding it is a the author call).
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


# The transcript budget, named so it is a decision rather than a magic number in a slice.
# Raising it costs strong-model tokens per scene; lowering it blinds the critic sooner.
_TRANSCRIPT_CAP = 6000


def _warn_cap(label, text, cap, unit, sep="; "):
    """Say what a cap dropped, on stderr, in the shape the transcript cap already uses.

    A cap is a real budget decision; a SILENT cap is a detector reporting on evidence it never
    read. This makes the coverage claim visible without changing the budget.
    """
    if len(text) <= cap:
        return
    # Count only entries WHOLLY before the cut. The first draft of this counted separators in the
    # kept slice and added one, which counts a half-delivered final entry as delivered: on the
    # active book it printed "9 of 9 people reached the model" in the same sentence as "the rest
    # were NOT checked", while the ninth was severed mid-clause. A coverage warning that overstates
    # coverage is worse than no warning, because it reads as a clean bill.
    entries = text.split(sep)
    kept_entries = text[:cap].split(sep)[:-1]        # the last is cut mid-entry (len > cap here)
    first_dropped = entries[len(kept_entries)] if len(kept_entries) < len(entries) else ""
    sys.stderr.write(
        "  [critic] %s TRUNCATED: %d of %d %s reached the model (%d of %d chars). "
        "Contradictions involving the rest were NOT checked. First dropped: %s\n"
        % (label, len(kept_entries), len(entries), unit, cap, len(text),
           first_dropped.strip()[:70] or "(unknown)"))


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
        % (facts_txt[:2500], who[:1200], where[:1200], transcript[:_TRANSCRIPT_CAP]))
    # EVERY CAP HERE IS SILENT, AND THAT IS THE DEFECT. The transcript slice is the one that
    # matters: past the cap the critic judges a scene it cannot see the end of, and reports a
    # clean bill on evidence it never read — the same shape as a sweep certifying a directory it
    # never walked. The cap itself is a real budget decision (these prompts go to a strong model,
    # priced per token) and is NOT changed here; what changes is that dropping evidence now says so.
    #
    # The bite point is model-dependent and has never been measured per-run: at 121 chars/beat
    # (measured on runs/probe.db, the committed haiku probe) the cap lands near beat 50; a model
    # writing longer actions reaches it far sooner. The warning is what makes that measurable
    # instead of estimated.
    # The transcript cap warns (below); `who` and `where` did not, and both bite on a real book —
    # measured 2026-08-29: who 1309 chars, where 1476, against a 1200 cap. What fell off `where`
    # was an entire location and the law that governs it. A critic that never received a place
    # cannot flag a contradiction against it, and returned a clean verdict without saying so.
    # Same defect the comment below names; it was only ever fixed for one of the three caps.
    _warn_cap("CAST", who, 1200, "people")
    _warn_cap("PLACES", where, 1200, "locations")
    _warn_cap("WORLD FACTS", facts_txt, 2500, "facts", sep="\n")   # facts join on newline (above)

    if len(transcript) > _TRANSCRIPT_CAP:
        kept = transcript[:_TRANSCRIPT_CAP].count(chr(10)) + 1
        total = transcript.count(chr(10)) + 1
        sys.stderr.write(
            "  [critic] TRANSCRIPT TRUNCATED: %d of %d beats reached the model (%d of %d chars). "
            "Beats %d+ were NOT judged — a clean verdict does not cover them.\n"
            % (kept, total, _TRANSCRIPT_CAP, len(transcript), kept + 1))
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
    # A PARSE FAILURE MUST NOT READ AS A CLEAN SCENE. Until 2026-08-29 every failure here — a
    # refusal, an empty reply, a mid-JSON cutoff, or a real finding followed by a stray brace that
    # made the greedy `\{.*\}` overshoot — returned {"continuity": [], "voice": []}: byte-identical
    # to "I read this scene and found nothing wrong". The critic is the no-contradiction floor
    # (acceptance-criteria.md), so that is the one verdict it must never produce by accident. The
    # docstring above claimed "the run itself fails loud"; it does not — `_openrouter` raises only
    # on transport failure, and a 200-OK unparseable body raised and logged nothing.
    err = None
    try:
        d = json.loads(m.group(0)) if m else {}
        if not m:
            err = "no JSON object found in reply"
    except Exception as exc:
        d, err = {}, "json: %s" % exc
    cont = d.get("continuity") if isinstance(d.get("continuity"), list) else []
    voice = d.get("voice") if isinstance(d.get("voice"), list) else []
    if err is None and d and not isinstance(d.get("continuity"), list) and "continuity" in d:
        err = "continuity was %s, not a list" % type(d.get("continuity")).__name__
    if err:
        sys.stderr.write(
            "  [critic] REPLY UNPARSEABLE (%s) — this is NOT a clean verdict; the scene was not "
            "judged. Raw reply began: %r\n" % (err, (raw or "")[:120]))
        return {"continuity": cont, "voice": voice, "parse_error": err}
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
    led = Ledger(args.db or books.db_path(args.vault))
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
