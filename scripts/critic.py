#!/usr/bin/env python3
"""critic.py — the continuity + voice critic (design.md layer 6, the non-author check).

Reviews a CANONIZED scene against the world's canon + the scene's own transcript, flagging
CONTINUITY problems (a statement or action that contradicts an established world-fact or an earlier
line) and VOICE problems (two characters who read alike — a reader couldn't tell who is speaking).
A strong-model judgment: the hybrid architecture's editing tier (the author, 2026-06-13) — the cheap
local model does the acting, the strong model (Claude via OpenRouter) does the judging, per the
model-tiering rule. Harness-layer — the engine never calls models. Stub-testable (no API).

DETECT, AND SINCE 2026-09-19 REPENT. `--correct` appends one `correction` event per continuity
flag (`correct_run`, below) — consolidation-loop.md open-q 3's protocol, built: append-only,
never an edit. The REWRITE half stays the author's; the critic still writes no prose. Until this
flag existed the first live pass over real prose found fourteen continuity contradictions and the
record had no row that could carry one, so they lived only in a log file.

ONE REVIEW PER RECORDED SCENE (2026-09-18). Until then main() reviewed the whole run as one
transcript under caps sized when a beat was 121 chars (the haiku probe). The first model run over
a live book — three recorded scenes, ~2,900 chars a beat — reached the model with a tenth of its
beats and short of its full cast and place list, and said so on stderr; the warnings worked and the
critic did not. The unit design.md layer 6 names is a SCENE, which is the unit `scenes` records
and `narrate_book` renders by, so the loop below reviews each recorded scene with its own turns
(a run with no scene rows — the stub probes — is reviewed whole, as before).

Usage:
  python scripts/critic.py --vault "<book>" --run <run_id>            # strong-model review, per scene
  python scripts/critic.py --vault "<book>" --run <run_id> --stub     # clean review, no API
  python scripts/critic.py --vault "<book>" --run <run_id> --correct  # ...and append the corrections
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
from src.engine import world_events                                  # noqa: E402  (THE writer for a non-turn row)
from src.engine.consolidation import CATALOG, SYSTEM_TYPES           # noqa: E402  (the type vocabulary, derived)
from src.engine.ledger import Ledger                                 # noqa: E402
from src.engine.records import Event                                 # noqa: E402
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


# The budgets, named so each is a decision rather than a magic number in a slice. Raising one
# costs strong-model tokens per scene; lowering it blinds the critic sooner. SIZED 2026-09-18 to
# what the live book measured: a 14-beat scene ran 40,700 transcript chars (2,900 per beat), the
# cast line 1,309 and the places line 1,476 — against the old 6,000 / 1,200 / 1,200, which had been
# set on the 121-chars-per-beat probe and bit at beat 3. The warnings below stay: a 40-beat scene
# is the next measurement, and it will say so rather than judge what it did not read.
_TRANSCRIPT_CAP = 60000
_CANON_CAP = 4000          # the who / where lines
_FACTS_CAP = 6000          # the standing facts


def _warn_cap(label, text, cap, unit, sep="; ", scene=""):
    """Say what a cap dropped, on stderr, in the shape the transcript cap already uses.

    A cap is a real budget decision; a SILENT cap is a detector reporting on evidence it never
    read. This makes the coverage claim visible without changing the budget.
    """
    if len(text) <= cap:
        return
    # Count only entries WHOLLY before the cut. The first draft of this counted separators in the
    # kept slice and added one, which counts a half-delivered final entry as delivered: on the
    # active book it printed "N of N people reached the model" in the same sentence as "the rest
    # were NOT checked", while the last was severed mid-clause. A coverage warning that overstates
    # coverage is worse than no warning, because it reads as a clean bill.
    entries = text.split(sep)
    kept_entries = text[:cap].split(sep)[:-1]        # the last is cut mid-entry (len > cap here)
    first_dropped = entries[len(kept_entries)] if len(kept_entries) < len(entries) else ""
    sys.stderr.write(
        "  [critic]%s %s TRUNCATED: %d of %d %s reached the model (%d of %d chars). "
        "Contradictions involving the rest were NOT checked. First dropped: %s\n"
        % (scene, label, len(kept_entries), len(entries), unit, cap, len(text),
           first_dropped.strip()[:70] or "(unknown)"))


def build_critic_prompt(turns, world, label=None):
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
        % (facts_txt[:_FACTS_CAP], who[:_CANON_CAP], where[:_CANON_CAP], transcript[:_TRANSCRIPT_CAP]))
    tag = " [%s]" % label if label else ""
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
    _warn_cap("CAST", who, _CANON_CAP, "people", scene=tag)
    _warn_cap("PLACES", where, _CANON_CAP, "locations", scene=tag)
    _warn_cap("WORLD FACTS", facts_txt, _FACTS_CAP, "facts", sep="\n", scene=tag)   # facts join on newline (above)

    if len(transcript) > _TRANSCRIPT_CAP:
        kept = transcript[:_TRANSCRIPT_CAP].count(chr(10)) + 1
        total = transcript.count(chr(10)) + 1
        sys.stderr.write(
            "  [critic]%s TRANSCRIPT TRUNCATED: %d of %d beats reached the model (%d of %d chars). "
            "Beats %d+ were NOT judged — a clean verdict does not cover them.\n"
            % (tag, kept, total, _TRANSCRIPT_CAP, len(transcript), kept + 1))
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]


def review_scene(turns, world, model=DEFAULT_CRITIC_MODEL, stub=False, label=None):
    """Strong-model continuity+voice review of a canonized scene. Returns {"continuity": [...],
    "voice": [...]}. Stub (or an empty scene): a clean review — deterministic, no API. The strong
    model's reply is parsed leniently (first JSON object); a malformed reply yields empty lists
    (fail-soft on the PARSE only — a non-answer is not a false flag; the run itself fails loud)."""
    if stub or not turns:
        return {"continuity": [], "voice": []}
    messages = build_critic_prompt(turns, world, label=label)
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


def _segments(led, run_id):
    """The run's recorded scenes, each with its own turns -> [(scene row or None, turns)]. A run
    with no scene rows is one segment: the whole run, as the critic always read it."""
    turns = scene_turns(led, run_id)
    scenes = led.scenes_for(run_id)
    if not scenes:
        return [(None, turns)]
    return [(sc, [t for t in turns if sc["start_turn"] <= t["turn"] <= sc["end_turn"]]) for sc in scenes]


def _label(sc):
    return "scene %s %s" % (sc["scene_no"], sc.get("label") or "") if sc else None


def prompts_for_run(led, run_id, world):
    """--prompt-only: one critic prompt per recorded scene (Claude-in-the-loop answers each)."""
    return [build_critic_prompt(seg, world, label=_label(sc)) for sc, seg in _segments(led, run_id)]


def review_run(led, run_id, world, model=DEFAULT_CRITIC_MODEL, stub=False):
    """One review per recorded scene -> {"scenes": [{scene_no, label, turns: [a, b], continuity,
    voice, (parse_error)}]}. A run with no scene rows returns review_scene's flat shape over the
    whole run. An empty scene (no turns in its range) is reviewed clean, not skipped: the entry
    says which turns it covers, so a scene the log never filled is visible in the report."""
    segs = _segments(led, run_id)
    if len(segs) == 1 and segs[0][0] is None:
        return review_scene(segs[0][1], world, model, stub)
    out = []
    for sc, seg in segs:
        rep = review_scene(seg, world, model, stub, label=_label(sc))
        entry = {"scene_no": sc["scene_no"], "label": sc.get("label"),
                 "turns": [sc["start_turn"], sc["end_turn"]]}
        entry.update(rep)
        out.append(entry)
    return {"scenes": out}


# ---------------------------------------------------------------------------------------------
# THE CORRECTION HALF (2026-09-19) — consolidation-loop.md open-q 3, measurement.md s3.
#
# "The critic never edits. It appends a `correction` event referencing the bad event-id; the fold
# applies the inverse delta; consumers treat the referenced event as superseded. Append-only
# repentance — the record keeps both the error and its correction, which is itself diagnostic data
# (correction RATE is detector #6)." That is the whole design, and this is the emitter half of it.
# The DETECTING half above is unchanged, and so is this script's default behaviour: the write
# happens only under `--correct`.
# ---------------------------------------------------------------------------------------------

def world_moving_types():
    """The catalog types whose fold MOVES THE WORLD -> set of names. Derived, never listed.

    A correction's `supersedes` list must name the ids worth un-applying, and "worth un-applying"
    is decidable rather than a matter of taste: a type whose `world_map` is "none" folded to
    nothing, so skipping it on replay changes nothing and naming it would be noise. The engine's
    own system rows (`turn-skipped`, `correction`) are excluded by the same table that declares
    them — a hand-written list here would be the eighth duplicate-of-a-source-of-truth CLAUDE.md
    tabulates, and `consolidation.ACTOR_TAG_TYPES` is already derived from exactly this pair of
    conditions in the other direction."""
    return {name for name, row in CATALOG.items()
            if row.get("world_map") not in (None, "none") and name not in SYSTEM_TYPES}


def continuity_flags(review):
    """Every continuity flag in a review, whatever shape it came back in -> [{turn, issue}, ...].

    `review_run` returns `{"scenes": [{..., "continuity": [...]}]}` for a run with scene rows and
    `review_scene`'s flat `{"continuity": [...]}` for one without (the stub probes), so a caller
    that knew only one of the two would silently correct nothing on half the runs."""
    scenes = review.get("scenes") if isinstance(review, dict) else None
    if isinstance(scenes, list):
        out = []
        for sc in scenes:
            out.extend(f for f in (sc.get("continuity") or []) if isinstance(f, dict))
        return out
    return [f for f in ((review or {}).get("continuity") or []) if isinstance(f, dict)]


def _turn_actors(led, run_id):
    return {r["turn"]: r["actor"] for r in led.con.execute(
        "SELECT turn, actor FROM turns WHERE run_id=?", (run_id,))}


def _world_moving_ids(led, run_id, turn, moving):
    """The event ids appended BY that turn whose type moves the world -> [int] in log order."""
    return [r["event_id"] for r in led.con.execute(
        "SELECT event_id, type FROM events WHERE run_id=? AND turn=? ORDER BY event_id",
        (run_id, turn)) if r["type"] in moving]


def correct_run(led, run_id, review, source="critic"):
    """Append ONE `correction` event per continuity flag -> the Events appended (possibly []).

    THE TICK. Every correction from one review lands at the run's NEXT tick — `latest_turn + 1` —
    passed to `world_events.append` as the turn, with `caused_at`/`effective_at` left to the
    writer's own defaults, which is the convention `scripts/keeper.py` `apply_proposals` already uses for a row
    appended outside a turn commit. Two consequences, both wanted: a fold `as_of` any turn already
    recorded does NOT yet see the correction (the record is not rewritten behind the reader's
    back), and the cache drop `append` performs at that tick invalidates nothing that was right.

    IDEMPOTENT ON (turn, issue). The critic is a strong model read twice on the same scene and
    `--correct` is a hand-run flag, so re-running it must not double the log — and the log cannot
    be de-duplicated afterwards (hard rule 2). The key is the pair the flag itself carries; a
    genuinely new finding on the same turn has different words and appends.

    A FLAG ON A TURN THAT MOVED NOTHING STILL APPENDS, with an empty `supersedes`. Nothing is
    un-applied and that is the point: the flag is real, the RATE is measurement.md detector #6,
    and a correction the emitter dropped is a finding that exists only in a log file — which is
    the RED_STATE this gate was opened on."""
    flags = continuity_flags(review)
    if not flags:
        return []
    moving, actors = world_moving_types(), _turn_actors(led, run_id)
    at = led.latest_turn(run_id) + 1
    seen = {(json.loads(r["payload"]).get("turn"), json.loads(r["payload"]).get("issue"))
            for r in led.corrections_for(run_id)}
    appended = []
    for flag in flags:
        turn, issue = flag.get("turn"), str(flag.get("issue") or "")
        turn = int(turn) if isinstance(turn, (int, float)) and not isinstance(turn, bool) else turn
        if (turn, issue) in seen:
            continue
        ev = Event(type="correction", actor=actors.get(turn), target=None,
                   visibility=CATALOG["correction"]["visibility"],
                   payload={"supersedes": _world_moving_ids(led, run_id, turn, moving) if turn in actors else [],
                            "turn": turn, "issue": issue, "source": source})
        world_events.append(led, run_id, at, [ev])
        seen.add((turn, issue))
        appended.append(ev)
    return appended


def main():
    ap = argparse.ArgumentParser(description="the continuity + voice critic — review a canonized scene")
    ap.add_argument("--vault", required=True, help="the BOOK folder (vault)")
    ap.add_argument("--run", required=True, help="run_id to review")
    ap.add_argument("--db", default=None, help="chronicle db path (default <vault>/runs/<book>.db)")
    ap.add_argument("--model", default=DEFAULT_CRITIC_MODEL)
    ap.add_argument("--stub", action="store_true", help="clean review, no API (deterministic)")
    ap.add_argument("--prompt-only", action="store_true", dest="prompt_only",
                    help="print the strong-model prompt (JSON) instead of calling an API — hand it to Claude-in-the-loop (key-free)")
    ap.add_argument("--correct", action="store_true",
                    help="after the review, APPEND one `correction` event per continuity flag "
                         "(append-only; the fold then treats the flagged turn's world events as "
                         "superseded). Off by default — the flags are a model's reading and the "
                         "owner decides. Nothing is ever edited or deleted")
    args = ap.parse_args()

    from src.engine.vault import load_book
    world, _chars = load_book(args.vault)
    led = Ledger(args.db or books.db_path(args.vault))
    if args.prompt_only:                               # Claude-in-the-loop: emit the prompts, Claude produces the reviews
        # REFUSED RATHER THAN IGNORED. `--prompt-only` returns before any review exists, so there
        # are no flags to correct from; accepting the flag here would append nothing and print
        # nothing, which is the silent no-op this repo keeps paying for.
        if args.correct:
            raise SystemExit("--correct needs a REVIEW to correct from, and --prompt-only produces "
                             "a prompt instead of one. Run the review (--stub or a model), then "
                             "re-run with --correct.")
        print(json.dumps(prompts_for_run(led, args.run, world), indent=2))
        return 0
    report = review_run(led, args.run, world, args.model, args.stub)
    print(json.dumps(report, indent=2))
    entries = report["scenes"] if "scenes" in report else [dict(report, turns=None)]
    total = 0
    for e in entries:
        n = len(e["continuity"]) + len(e["voice"])
        total += n
        span = ("turns %d-%d" % tuple(e["turns"])) if e.get("turns") else "%d turn(s)" % len(scene_turns(led, args.run))
        where = ("scene %s %s, " % (e["scene_no"], e.get("label") or "")) if "scene_no" in e else ""
        print("\ncritic: %s%s — %d flag(s)%s%s" % (where, span, n, " — clean" if n == 0 else "",
                                                 " — NOT JUDGED (%s)" % e["parse_error"] if e.get("parse_error") else ""))
    print("critic: %d flag(s) over %d scene(s)" % (total, len(entries)))
    if args.correct:
        appended = correct_run(led, args.run, report)
        print("critic: %d correction(s) appended (%d supersede a world event)"
              % (len(appended), sum(1 for ev in appended if ev.payload["supersedes"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
