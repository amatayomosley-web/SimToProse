#!/usr/bin/env python3
"""narrate.py — the narrator (design.md layer 7, narration.md): a canonized scene -> POV-bound prose.

Renders a scene's committed chronicle into close-third novel prose bounded by ONE POV character's
knowledge (narration.md): the POV's perceptions + interiority (their thoughts) + every other
character's OBSERVABLE actions and words — NEVER another character's private thoughts or true
motives, only how the POV reads them. That boundary is the prose-layer twin of the simulator's vault
wall, and it is what produces dramatic irony automatically ("he smiled, and she took it for warmth").
A strong-model render done ONCE at output (hybrid editing tier — the cheap model acts, the strong
model writes the prose). Harness-layer; the engine never calls models. Stub-testable (no API).

The narrator is an ADAPTER, not a transcriber (Writing Conventions §6): the chronicle is SOURCE, the
way a true story is source for the film of it. It MAY compress / heighten / reorder the telling; it may
NOT change what a character chose, who they are, or what causally happened. Per-render VOICE comes from
the book's `book.json` (the timeline spine + the per-character author) plus the POV character's own
`voice` block — assembled by narration_lens() and woven into the prompt.

Usage:
  python scripts/narrate.py --vault "<book>" --run <run_id> --pov <char_id>
  python scripts/narrate.py --vault "<book>" --run <run_id> --pov <char_id> --stub
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.ledger import Ledger                                 # noqa: E402
from direct import _openrouter                                      # noqa: E402  (strong-model dispatch)
from critic import scene_turns                                      # noqa: E402  (the committed-turn read)

# Strong-stage model. PRIMARY path is Claude-in-the-loop (--prompt-only — key-free; the script emits
# the prompt, Claude-in-a-session writes the prose). This OpenRouter slug is the key-GATED fallback
# (the sim is local-only and the OpenRouter key is intentionally removed; re-adding it is a William call).
DEFAULT_NARRATOR_MODEL = "anthropic/claude-sonnet-4.6"


def pov_split(turns, pov):
    """Apply the POV wall (narration.md 'second boundary'): the POV actor's turns keep their
    interiority (thought); every other actor contributes ONLY their observable action — their thought
    is hidden, because the POV cannot see it. The prose-layer twin of the simulator's vault wall."""
    out = []
    for t in turns:
        if t["actor"] == pov:
            out.append({"actor": t["actor"], "action": t["action"], "thought": t["thought"]})
        else:
            out.append({"actor": t["actor"], "action": t["action"]})       # observable only — no thought
    return out


def load_narration_config(vault):
    """Read the book's narration manifest (book.json at the vault root; Writing Conventions §6):
    {spines: {timeline: register}, casting: {char_id: author}}. Missing or malformed -> {} (the
    narrator then renders neutrally). load_book does not read this file; the narrator does."""
    path = os.path.join(vault, "book.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}
    return cfg if isinstance(cfg, dict) else {}


def narration_lens(pov, world, chars, cfg):
    """Assemble the POV's render lens (Writing Conventions §6): the timeline SPINE
    (cfg.spines[world.timeline]), the POV's assigned AUTHOR (cfg.casting[pov]), and the POV's VOICE
    block from the sheet (reused — register/tic/rule). Any piece may be absent; build_narration_prompt
    omits what is None and degrades to a neutral render. Pure."""
    cfg = cfg or {}
    spine = (cfg.get("spines") or {}).get(world.get("timeline"))
    author = (cfg.get("casting") or {}).get(pov)
    voice = ((chars.get(pov) or {}).get("baseline") or {}).get("voice")
    return {"spine": spine, "author": author, "voice": voice}


def build_narration_prompt(turns, pov, world, pov_name=None, retrospective=False, lens=None):
    """The narrator messages: the §6 adapter contract + the POV-split scene. Other characters appear
    observable-only, so the model literally cannot render their interiors (the wall is in the input).
    `lens` (from narration_lens) is {spine, author, voice} — the timeline register, the POV's assigned
    author, and the POV's voice block; any field may be None, in which case it is simply omitted."""
    povn = pov_name or pov
    lines = []
    for e in pov_split(turns, pov):
        who = e["actor"]
        if "thought" in e:
            lines.append("%s (does/says): %s\n%s (privately thinks): %s" % (who, e["action"], who, e["thought"]))
        else:
            lines.append("%s (observed to do/say): %s" % (who, e["action"]))
    transcript = "\n".join(lines)
    lens = lens or {}
    parts = [
        "You are a NOVELIST adapting one recorded scene into close-third-person prose, bound to a single "
        "POV character: %s." % povn,
        "The recorded scene is your SOURCE, not your script — like a film adapted from a true story, you "
        "do not render it one-to-one. You MAY compress, cut, reorder, heighten, and choose what to "
        "dramatize versus summarize. You may NOT change what a character chose or did, who they are, or "
        "what causally happened. Adapt the telling; never the person or the choice.",
        "Bind strictly to %s's knowledge: render %s's perceptions and interiority AND the OBSERVABLE "
        "actions and words of everyone else — never another character's private thoughts or true motives, "
        "only how %s reads them. This POV wall is the source of the scene's dramatic irony; do NOT "
        "head-hop into anyone else's mind." % (povn, povn, povn),
    ]
    if lens.get("spine"):
        parts.append("VOICE — the section's authorial spine (every passage in this section shares it): %s"
                     % lens["spine"])
    lensbits = []
    if lens.get("author"):
        lensbits.append("render %s's passages in the manner of %s" % (povn, lens["author"]))
    v = lens.get("voice") or {}
    vb = "; ".join("%s: %s" % (k, v[k]) for k in ("register", "tic", "rule") if v.get(k))
    if vb:
        lensbits.append("bent to this character's own voice — %s" % vb)
    if lensbits:
        parts.append("LENS — color the spine toward the POV character (do not replace it): %s."
                     % "; ".join(lensbits))
    parts.append(
        "Anti-slop floor: vary sentence length; concrete nouns over abstractions; no tricolons, no "
        "'not X but Y', no em-dash pileups, no summarizing a paragraph in its last sentence; never use "
        "delve, testament, tapestry, crucial, paramount, leverage, beacon, symphony, underscore, foster, "
        "nuanced, profound, or shattered.")
    sys_msg = " ".join(parts)
    when = ("Tell it retrospectively — the narrator knows how it turned out and may foreshadow."
            if retrospective else
            "Tell it in real time — the narrator knows only up to this moment, no foreshadowing.")
    user_msg = (
        "WORLD: %s\n\nRECORDED SCENE (POV = %s; everyone else is shown observable-only):\n%s\n\n%s\n\n"
        "Render this scene as a passage of close-third prose from %s's point of view."
        % (str(world.get("world", "")), povn, transcript, when, povn))
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]


def narrate(turns, pov, world, model=DEFAULT_NARRATOR_MODEL, stub=False, pov_name=None,
            retrospective=False, lens=None):
    """Render the scene to POV-bound prose. Stub: the POV's own actions strung as plain sentences
    (deterministic, no API) — enough to prove the wiring. Empty scene -> empty string."""
    if not turns:
        return ""
    if stub:
        acts = [str(t["action"]).strip() for t in turns if t["actor"] == pov]
        return " ".join(a for a in acts if a) or "(the scene passes quietly)"
    messages = build_narration_prompt(turns, pov, world, pov_name, retrospective, lens)
    return _openrouter(messages, model, max_tokens=2000)


def narrate_book(led, run_id, world, chars, model=DEFAULT_NARRATOR_MODEL, stub=False,
                 retrospective=False, cfg=None):
    """Render an entire chronicle as a manuscript: each recorded scene narrated in order, POV-bounded
    by that scene's recorded pov (the director's per-scene choice; narration.md multi-POV = switch the
    boundary, never violate it). A scene with no pov falls back to its first actor. Returns the
    concatenated manuscript with a header per scene. Empty (no scenes) -> empty string."""
    scenes = led.scenes_for(run_id)
    if not scenes:
        return ""
    all_turns = scene_turns(led, run_id)
    chars = chars or {}
    passages = []
    for s in scenes:
        seg = [t for t in all_turns if s["start_turn"] <= t["turn"] <= s["end_turn"]]
        if not seg:
            continue
        pov = s["pov"] or seg[0]["actor"]                 # the scene's POV, or its first actor as a fallback
        pov_name = chars.get(pov, {}).get("fixed", {}).get("name", pov)
        lens = narration_lens(pov, world, chars, cfg)
        prose = narrate(seg, pov, world, model, stub, pov_name, retrospective, lens)
        title = s["label"] or ("Scene %d" % s["scene_no"])
        passages.append("## %s\n\n%s" % (title, prose))
    return "\n\n".join(passages)


def main():
    ap = argparse.ArgumentParser(description="the narrator — render a canonized scene into POV-bound prose")
    ap.add_argument("--vault", required=True, help="the BOOK folder (vault)")
    ap.add_argument("--run", required=True, help="run_id to narrate")
    ap.add_argument("--pov", default=None, help="POV character id for single-scene mode (required without --book)")
    ap.add_argument("--book", action="store_true", help="narrate the WHOLE chronicle — every recorded scene, POV per scene")
    ap.add_argument("--db", default=None, help="chronicle db path (default <vault>/runs/<book>.db)")
    ap.add_argument("--model", default=DEFAULT_NARRATOR_MODEL)
    ap.add_argument("--stub", action="store_true", help="deterministic stand-in, no API")
    ap.add_argument("--retrospective", action="store_true", help="narrator knows the outcome (may foreshadow)")
    ap.add_argument("--prompt-only", action="store_true", dest="prompt_only",
                    help="print the narration prompt(s) (JSON) instead of calling an API — hand to Claude-in-the-loop (key-free)")
    args = ap.parse_args()

    from src.engine.vault import load_book
    world, chars = load_book(args.vault)
    cfg = load_narration_config(args.vault)               # book.json: timeline spines + per-character casting (§6)
    book_name = os.path.basename(os.path.normpath(args.vault)).lower().replace(" ", "-")
    led = Ledger(args.db or os.path.join(args.vault, "runs", "%s.db" % book_name))

    if args.book:                                     # whole-chronicle manuscript, POV per recorded scene
        if args.prompt_only:                          # Claude-in-the-loop: emit per-scene prompts
            all_turns = scene_turns(led, args.run)
            out = []
            for s in led.scenes_for(args.run):
                seg = [t for t in all_turns if s["start_turn"] <= t["turn"] <= s["end_turn"]]
                if not seg:
                    continue
                pov = s["pov"] or seg[0]["actor"]
                pov_name = chars.get(pov, {}).get("fixed", {}).get("name", pov)
                lens = narration_lens(pov, world, chars, cfg)
                out.append({"scene": s["label"], "pov": pov,
                            "prompt": build_narration_prompt(seg, pov, world, pov_name, args.retrospective, lens)})
            print(json.dumps(out, indent=2))
            return 0
        manuscript = narrate_book(led, args.run, world, chars, args.model, args.stub, args.retrospective, cfg)
        print(manuscript or "(no recorded scenes to narrate)")
        return 0

    if not args.pov:
        raise SystemExit("--pov is required for single-scene narration (or pass --book to narrate the whole chronicle)")
    turns = scene_turns(led, args.run)
    present = {t["actor"] for t in turns}
    if args.pov not in present:                       # narration.md: a POV not in the scene cannot narrate it
        raise SystemExit("POV %r is not present in run %r (actors: %s) — a POV-bound narrator can only "
                         "render a scene it witnessed" % (args.pov, args.run, ", ".join(sorted(present)) or "none"))
    pov_name = chars.get(args.pov, {}).get("fixed", {}).get("name", args.pov)
    lens = narration_lens(args.pov, world, chars, cfg)
    if args.prompt_only:                              # Claude-in-the-loop: emit the prompt, Claude writes the prose
        print(json.dumps(build_narration_prompt(turns, args.pov, world, pov_name, args.retrospective, lens), indent=2))
        return 0
    prose = narrate(turns, args.pov, world, args.model, args.stub, pov_name, args.retrospective, lens)
    print(prose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
