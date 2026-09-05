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

from src.engine import books                                    # noqa: E402  (the one db-path definition)
from src.engine import narration_modes
from src.engine.ledger import Ledger                                 # noqa: E402
from direct import _openrouter                                      # noqa: E402  (strong-model dispatch)
from critic import scene_turns                                      # noqa: E402  (the committed-turn read)

# Strong-stage model. PRIMARY path is Claude-in-the-loop (--prompt-only — key-free; the script emits
# the prompt, Claude-in-a-session writes the prose). This OpenRouter slug is the key-GATED fallback
# (the sim is local-only and the OpenRouter key is intentionally removed; re-adding it is a the author call).
DEFAULT_NARRATOR_MODEL = "anthropic/claude-sonnet-4.6"


# ---------------------------------------------------------------------------------------------
# TWO AXES, and only one of them touches the wall (narration.md; William's reversal 2026-09-01).
#
#   VOICE     — grammatical person and distance. A rendering INSTRUCTION over the same transcript.
#               Constrained by nothing: the wall does not care which pronoun is used.
#   KNOWLEDGE — whose recorded interiority the narrator is shown. Enforced in `pov_split`, because
#               "the wall is in the input" — a prompt cannot un-see what it was handed.
#
# They were conflated only by a hardcoded string in the prompt. Defaults stay `close-third` + `pov`:
# `narration.md` argues that omniscient prose "tells the reader things the POV character can't know,
# collapsing the dramatic irony the whole vault model exists to create". That argument governs the
# DEFAULT and is preserved; it is not a prohibition. The author chooses.
# THE TWO AXES live in `src/engine/narration_modes.py`, because the schema CHECK, the ledger
# guard and the director-facing cfg all need the same vocabulary, and three of those four
# consumers are engine-side. Copying the tuple here would be the duplicate class CLAUDE.md
# tabulates. Re-exported so this module's existing readers are unchanged.
from src.engine.narration_modes import (VOICES, KNOWLEDGE,               # noqa: E402
                                        DEFAULT_VOICE, DEFAULT_KNOWLEDGE)


def pov_split(turns, pov, knowledge=DEFAULT_KNOWLEDGE):
    """Apply the POV wall (narration.md 'second boundary'): the POV actor's turns keep their
    interiority (thought); every other actor contributes ONLY their observable action — their thought
    is hidden, because the POV cannot see it. The prose-layer twin of the simulator's vault wall.

    `knowledge="omniscient"` is the passthrough branch: every actor keeps their recorded thought.
    It is a deliberate author choice (see KNOWLEDGE above) and never the default. What it trades
    away is dramatic irony; what it does NOT relax is faithfulness — the transcript still contains
    only what the run recorded, which is why `test_narrate` can assert every rendered interiority
    traces to a `thought` on a real turn."""
    if knowledge not in KNOWLEDGE:
        raise ValueError("narrate: knowledge must be one of %s, got %r" % (list(KNOWLEDGE), knowledge))
    out = []
    for t in turns:
        if knowledge == "omniscient" or t["actor"] == pov:
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


def build_narration_prompt(turns, pov, world, pov_name=None, retrospective=False, lens=None,
                           voice=DEFAULT_VOICE, knowledge=DEFAULT_KNOWLEDGE):
    """The narrator messages: the §6 adapter contract + the POV-split scene. Other characters appear
    observable-only, so the model literally cannot render their interiors (the wall is in the input).
    `lens` (from narration_lens) is {spine, author, voice} — the timeline register, the POV's assigned
    author, and the POV's voice block; any field may be None, in which case it is simply omitted."""
    povn = pov_name or pov
    lines = []
    for e in pov_split(turns, pov, knowledge):
        who = e["actor"]
        if "thought" in e:
            lines.append("%s (does/says): %s\n%s (privately thinks): %s" % (who, e["action"], who, e["thought"]))
        else:
            lines.append("%s (observed to do/say): %s" % (who, e["action"]))
    transcript = "\n".join(lines)
    lens = lens or {}
    if voice not in VOICES:
        raise ValueError("narrate: voice must be one of %s, got %r" % (sorted(VOICES), voice))
    parts = [
        "You are a NOVELIST adapting one recorded scene into %s. The POV character is %s."
        % (VOICES[voice], povn),
        "The recorded scene is your SOURCE, not your script — like a film adapted from a true story, you "
        "do not render it one-to-one. You MAY compress, cut, reorder, heighten, and choose what to "
        "dramatize versus summarize. You may NOT change what a character chose or did, who they are, or "
        "what causally happened. Adapt the telling; never the person or the choice.",
    ]
    if knowledge == "omniscient":
        parts.append(
            "You may enter ANY character's mind: the transcript below carries every character's recorded "
            "interiority, because the author chose omniscient narration. What you may NOT do is invent "
            "interiority — render only what a character is recorded as thinking, and read no mind the "
            "transcript leaves silent. Omniscience over this record is not omniscience over the world.")
    else:
        parts.append(
            "Bind strictly to %s's knowledge: render %s's perceptions and interiority AND the OBSERVABLE "
            "actions and words of everyone else — never another character's private thoughts or true motives, "
            "only how %s reads them. This POV wall is the source of the scene's dramatic irony; do NOT "
            "head-hop into anyone else's mind." % (povn, povn, povn))
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
        "Render this scene as a passage of %s from %s's point of view."
        % (str(world.get("world", "")), povn, transcript, when, VOICES[voice], povn))
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]


def narrate(turns, pov, world, model=DEFAULT_NARRATOR_MODEL, stub=False, pov_name=None,
            retrospective=False, lens=None, voice=DEFAULT_VOICE, knowledge=DEFAULT_KNOWLEDGE):
    """Render the scene to POV-bound prose. Stub: the POV's own actions strung as plain sentences
    (deterministic, no API) — enough to prove the wiring. Empty scene -> empty string."""
    if not turns:
        return ""
    if stub:
        acts = [str(t["action"]).strip() for t in turns if t["actor"] == pov]
        return " ".join(a for a in acts if a) or "(the scene passes quietly)"
    messages = build_narration_prompt(turns, pov, world, pov_name, retrospective, lens,
                                      voice, knowledge)
    return _openrouter(messages, model, max_tokens=2000)


def narrate_book(led, run_id, world, chars, model=DEFAULT_NARRATOR_MODEL, stub=False,
                 retrospective=False, cfg=None, voice=None, knowledge=None):
    """Render an entire chronicle as a manuscript: each recorded scene narrated in order, POV-bounded
    by that scene's recorded pov (the director's per-scene choice; narration.md multi-POV = switch the
    boundary, never violate it). A scene with no pov falls back to its first actor. Returns the
    concatenated manuscript with a header per scene. Empty (no scenes) -> empty string.

    MIXED VOICE. Each scene renders in its OWN `voice`/`knowledge` (schema v13), which is how a book
    alternates first- and third-person sections without the narrator being told once for the whole
    manuscript. `voice=` / `knowledge=` here OVERRIDE every scene — the whole-book choice — and are
    None by default so the per-scene columns win unless the caller says otherwise."""
    scenes = led.scenes_for(run_id)
    if not scenes:
        return ""
    all_turns = scene_turns(led, run_id)
    chars = chars or {}
    passages = []

    # RENDER FROM THE CUT when there is one. `cutting-room.md`: "decisions append to the EDL;
    # narration renders from it". Without an EDL this function rendered every recorded scene in
    # scene order, which is a DUMP, not a cut — and the README's "a novel is a CUT of those
    # biographies, selected, ordered and narrated" had nothing behind it.
    #
    # An EMPTY EDL is not an error and never becomes one: every run made before the EDL existed has
    # none, so the fallback below renders exactly as it always did. Requiring a cut would turn the
    # common case into the error case.
    from src.engine import edl as edl_mod
    cut = edl_mod.entries_for(led.con, run_id)
    if cut:
        by_no = {sc["scene_no"]: sc for sc in scenes}
        for e in cut:
            if e["kind"] == edl_mod.BREAK:
                passages.append("# %s break" % e["level"])
                continue
            if e["kind"] == edl_mod.NOTE:
                continue                              # the room's memory, not manuscript text
            if e["kind"] == edl_mod.SUMMARY:
                # Compression is the room's to write, and the engine does not invent it. The entry
                # is rendered as a marked placeholder carrying its basis, so a manuscript never
                # silently drops a span the cut said to summarise.
                passages.append("[SUMMARY ticks %s-%s, pov %s, basis %s]"
                                % (e["span"][0], e["span"][1], e.get("pov") or "-",
                                   ", ".join(str(b) for b in e["basis"])))
                continue
            sc = by_no.get(e["scene_no"])
            if sc is None:
                continue                              # edl.traces reports this; rendering skips it
            seg = [t for t in all_turns if sc["start_turn"] <= t["turn"] <= sc["end_turn"]]
            if e.get("trim") and e["trim"] != edl_mod.FULL:
                # RESOLVE event ids to turns. `cutting-room.md` writes a trim as [event_id...] and
                # the manuscript's unit is the turn; filtering the turn list by the trim values
                # directly compared a global autoincrement against turn numbers, so a conforming
                # trim kept arbitrary wrong turns or none and the scene vanished, silently.
                keep = edl_mod.turns_for_trim(led.con, run_id, e["trim"])
                seg = [t for t in seg if t["turn"] in keep]
            if not seg:
                # SAY SO. `continue` here dropped the scene from the manuscript with nothing
                # reported — the exact failure `edl.validate`'s docstring says must not happen
                # ("the manuscript silently loses a scene"). A cut that selects nothing is a cut
                # the room got wrong, and the reader of the output is the person who can fix it.
                passages.append("[EMPTY: EDL entry %d selected scene %s and its trim kept no "
                                "recorded turn — run `cut.py --show-edl` for the trace audit]"
                                % (e["ord_no"], e.get("scene_no")))
                continue
            pov = e.get("pov") or sc["pov"] or seg[0]["actor"]
            pov_name = chars.get(pov, {}).get("fixed", {}).get("name", pov)
            lens = narration_lens(pov, world, chars, cfg)
            s_voice = voice or sc.get("voice") or DEFAULT_VOICE
            s_know  = knowledge or sc.get("knowledge") or DEFAULT_KNOWLEDGE
            prose = narrate(seg, pov, world, model, stub, pov_name, retrospective, lens,
                            s_voice, s_know)
            title = sc["label"] or ("Scene %d" % sc["scene_no"])
            if e.get("placement") == "flashback":
                title = "%s (flashback)" % title
            passages.append("## " + title + '\n\n' + prose)
        return '\n\n'.join(passages)

    for s in scenes:
        seg = [t for t in all_turns if s["start_turn"] <= t["turn"] <= s["end_turn"]]
        if not seg:
            continue
        pov = s["pov"] or seg[0]["actor"]                 # the scene's POV, or its first actor as a fallback
        pov_name = chars.get(pov, {}).get("fixed", {}).get("name", pov)
        lens = narration_lens(pov, world, chars, cfg)
        # per-scene by default; the argument overrides the whole manuscript when the caller passes one
        s_voice = voice or s.get("voice") or DEFAULT_VOICE
        s_know  = knowledge or s.get("knowledge") or DEFAULT_KNOWLEDGE
        prose = narrate(seg, pov, world, model, stub, pov_name, retrospective, lens, s_voice, s_know)
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
    # THE TWO AXES (see VOICES / KNOWLEDGE above). Separate flags because they are separate
    # questions: first-person-omniscient and close-third-POV are both real books.
    ap.add_argument("--voice", default=None, choices=sorted(VOICES),
                    help="grammatical person and distance (default close-third; with --book, "
                         "omitting this uses each scene's own recorded voice)")
    ap.add_argument("--knowledge", default=None, choices=list(KNOWLEDGE),
                    help="whose recorded interiority the narrator is shown: pov (default, the wall "
                         "stands) or omniscient (every character's recorded thought). Omniscient "
                         "trades dramatic irony for reach; it never licenses inventing interiority.")
    ap.add_argument("--prompt-only", action="store_true", dest="prompt_only",
                    help="print the narration prompt(s) (JSON) instead of calling an API — hand to Claude-in-the-loop (key-free)")
    args = ap.parse_args()

    from src.engine.vault import load_book
    world, chars = load_book(args.vault)
    cfg = load_narration_config(args.vault)               # book.json: timeline spines + per-character casting (§6)
    led = Ledger(args.db or books.db_path(args.vault))

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
                            "prompt": build_narration_prompt(
                                seg, pov, world, pov_name, args.retrospective, lens,
                                args.voice or s.get("voice") or DEFAULT_VOICE,
                                args.knowledge or s.get("knowledge") or DEFAULT_KNOWLEDGE)})
            print(json.dumps(out, indent=2))
            return 0
        manuscript = narrate_book(led, args.run, world, chars, args.model, args.stub,
                                  args.retrospective, cfg, args.voice, args.knowledge)
        print(manuscript or "(no recorded scenes to narrate)")
        return 0

    if not args.pov:
        raise SystemExit("--pov is required for single-scene narration (or pass --book to narrate the whole chronicle)")
    turns = scene_turns(led, args.run)
    present = {t["actor"] for t in turns}
    try:                # the rule belongs to the module that defines the knowledge axis
        narration_modes.require_witness(args.pov, present)
    except narration_modes.NarrationError as e:
        raise SystemExit("%s (run %r)" % (e, args.run))
    pov_name = chars.get(args.pov, {}).get("fixed", {}).get("name", args.pov)
    lens = narration_lens(args.pov, world, chars, cfg)
    if args.prompt_only:                              # Claude-in-the-loop: emit the prompt, Claude writes the prose
        print(json.dumps(build_narration_prompt(
            turns, args.pov, world, pov_name, args.retrospective, lens,
            args.voice or DEFAULT_VOICE, args.knowledge or DEFAULT_KNOWLEDGE), indent=2))
        return 0
    prose = narrate(turns, args.pov, world, args.model, args.stub, pov_name, args.retrospective, lens,
                    args.voice or DEFAULT_VOICE, args.knowledge or DEFAULT_KNOWLEDGE)
    print(prose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
