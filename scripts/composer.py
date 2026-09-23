#!/usr/bin/env python3
"""composer.py — what a character CAN be played at, read off the engine.

WHAT THIS IS, AND WHAT IT IS NOT YET. The composer sits between the deterministic assembler and the
actor: it reads the packet, never edits it, and emits a second file that reaches the actor alongside
the assembler's. Its job is SELECTION — which two or three of a character's live emotions this beat
is played on — and the selecting half needs an LLM and a brief, and is not built.

THIS IS THE DETERMINISTIC HALF, and it is the half whose contract is settled:

    for each BUILT path, what rung is this character at, and what block states that rung?

That is the input the selecting half consumes. It is pure, it needs no brief, and every rule it obeys
was fixed before it was written:

  * THE COMPOSER NEVER CHOOSES THE RUNG. It takes the rung the engine computes. A character mid-story
    at rung 4 can only be played at 4, whatever the scene wants — the owner's ruling, and the reason
    `selectable` returns what IS rather than what would suit.
  * NO FLOAT LEAVES THIS FUNCTION. `affect` goes in; a rung index, a name and a block come out.
    Hard rule 5 keeps numbers out of the prompt, and the composer is a prompt consumer.
  * THE RUNG NAME IS FOR SELECTING, NOT FOR SENDING. It rides in `name` so the selecting half and the
    logs can speak about it. `block` is what reaches an actor, and it carries no name — measured
    2026-09-07: the label is inert, and identical text under a WRONG label scored higher than under
    its own.
  * A DESIGNED-BUT-UNBUILT PATH IS ABSENT, NOT EMPTY. `rungs.paths()` reports what has blocks. Eight
    of the nine in docs/emotion-paths.md do not, and they do not appear here at all rather than
    appearing as a character with nothing to feel.

Run it against a book in $SWE_BOOKS to see a character's selectable set:
    python scripts/composer.py --book <book> --char <character>
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import rungs                                     # noqa: E402
from src.engine.rung_blocks import BLOCKS                        # noqa: E402
from src.engine.vault import load_book, character_or_raise       # noqa: E402


def selectable(affect, descending=None):
    """{primary: 0..1} -> [{path, rung, name, block}], one per BUILT path, path-sorted.

    The composer's whole read of the emotional state. A path whose source primitive is absent from
    the vector is skipped rather than defaulted: a missing primary means the caller handed in a
    partial vector, and inventing 0.0 for it would put the character at the floor of a path they may
    be nowhere near.

    `descending` is `{path: bool}` from `rungs.descending` (the packet's `state.descending`, set by
    `scene.assemble`): a path coming down from above its pivot gets its DESCENT block from
    `rungs.block_for`, when one is authored. Absent or False, the climb block — the one-argument
    form is byte-identical to what it always returned.
    """
    if not isinstance(affect, dict):
        raise TypeError("selectable: affect must be a dict of {primary: value}, got %r"
                        % type(affect).__name__)
    down = descending if isinstance(descending, dict) else {}
    out = []
    for path in rungs.paths():
        # NO LOOKUP. Until 2026-09-08 each path was translated from one of eight stored Panksepp
        # floats through `rung_blocks.PATH_SOURCE`, and two paths could never be reached because
        # their source was not stored -- RECEPTIVITY mapped to JOY, SELF-REGARD to nothing. The
        # paths ARE the state now, so the vector is keyed by path and every built path is readable.
        if path not in affect:
            continue
        index, name = rungs.rung_at(path, affect[path])
        out.append({"path": path, "rung": index, "name": name,
                    "block": rungs.block_for(path, index, descending=bool(down.get(path)))})
    return out


class ComposerError(Exception):
    """A selection that names something the engine did not produce, or direction that says too much."""


def compose_prompt(rows, brief):
    """(selectable rows, brief) -> the two-message prompt for the composer LLM.

    THE COMPOSER NEVER SEES THE BLOCK TEXT. It gets path, rung and name; the blocks are attached
    afterwards by `direction_for`. That makes "reads the packet, never edits it" a property of what
    it was handed rather than an instruction it could disobey — it cannot paraphrase prose it was
    never given.

    NO FLOAT APPEARS. The rows carry an index and a name because that is all `rung_at` returns.
    """
    if not rows:
        raise ComposerError("compose_prompt: nothing is selectable — no built path reads a primitive "
                            "this character carries")
    live = "\n".join("  %-14s rung %2d   %s" % (r["path"], r["rung"], r["name"]) for r in rows)
    sys_p = (
        "You decide which of a character's live emotions this beat is played on. You are given what "
        "the engine has already computed, and a brief describing what the scene needs.\n\n"
        "FOUR RULES, and the first is the one people break:\n"
        "1. YOU DO NOT CHOOSE THE RUNG. Each emotion below sits at the rung the engine computed. If "
        "the scene wants someone furious and the engine says they are chafing, they are chafing. Say "
        "so in `unavailable` and select what is actually there.\n"
        "2. YOU SELECT, YOU DO NOT WRITE THE STATE. Never describe what the character feels — that "
        "text already exists and is attached after you choose.\n"
        "3. NAME ONE PRIMARY when you select more than one. Measured: an actor given competing states "
        "with no primary resolves them IN SEQUENCE — the first drains away and the second replaces "
        "it — which is the single outcome this design exists to prevent.\n"
        "4. NEVER NAME AN ACT. You may say what the beat is ABOUT. You may not say what the character "
        "does about it; that is theirs.\n\n"
        "Select at most three. Fewer is usual. Selecting none is legitimate when the beat is not "
        "about this character's feelings.")
    usr = ("WHAT IS LIVE for this character (the engine's answer, not yours to change):\n%s\n\n"
           "WHAT THE SCENE NEEDS:\n%s\n\n"
           "Reply as ONE JSON object:\n"
           '{"selected": [{"path": "...", "rung": 0, "primary": true}], '
           '"about": "what this beat is about for this character, one line, naming no act", '
           '"unavailable": "any emotion the scene asked for that this character is not at, else empty"}'
           % (live, brief.strip() or "(no brief supplied)"))
    return [{"role": "system", "content": sys_p}, {"role": "user", "content": usr}]


def verify(selection, rows):
    """Refuse a composer selection that the engine cannot back. Returns the selection, or raises.

    THE GATE. An LLM sits in this seam, so what leaves it is checked deterministically rather than
    trusted. Every refusal here is something the composer is structurally able to get wrong.
    """
    if not isinstance(selection, dict):
        raise ComposerError("verify: selection must be a JSON object, got %r" % type(selection).__name__)
    picked = selection.get("selected") or []
    if not isinstance(picked, list):
        raise ComposerError("verify: `selected` must be a list")
    if len(picked) > 3:
        raise ComposerError("verify: %d emotions selected; at most three may play in one beat" % len(picked))
    have = {(r["path"], r["rung"]) for r in rows}
    for row in picked:
        if not isinstance(row, dict) or "path" not in row or "rung" not in row:
            raise ComposerError("verify: each selection needs a path and a rung, got %r" % (row,))
        if (row["path"], row["rung"]) not in have:
            engine_rung = next((r["rung"] for r in rows if r["path"] == row["path"]), None)
            if engine_rung is None:
                raise ComposerError("verify: %r is not a path this character has — the composer may "
                                    "only select from what the engine produced" % (row["path"],))
            raise ComposerError("verify: %s was selected at rung %r and the engine says rung %d. The "
                                "composer selects the emotion, never the rung."
                                % (row["path"], row["rung"], engine_rung))
    primaries = [r for r in picked if r.get("primary")]
    if len(picked) > 1 and len(primaries) != 1:
        raise ComposerError("verify: %d emotions selected and %d marked primary — exactly one must "
                            "be, or the actor resolves them in sequence instead of at once"
                            % (len(picked), len(primaries)))
    _refuse_leaks(selection)
    return selection


def _forbidden_names():
    """Every word that would let a name do the block's work — designed paths, rung names, primitives."""
    from src.engine.rung_blocks import BANDS
    from src.engine.records import PATHS
    designed = {"displeasure", "wariness", "goodwill", "receptivity", "self-regard",
                "distaste", "deflation", "levity", "stirring"}
    rung_names = {nm.lower() for band in BANDS.values() for _, _, nm in band}
    return designed | rung_names | {p.lower() for p in PATHS}


def _refuse_leaks(selection):
    """Composer-authored prose may not carry an emotion name or a named act.

    THE NAME. Measured 2026-09-07: the label is inert as direction — identical text under a WRONG
    label scored higher than under its own — so a name in the delivered text buys nothing and risks a
    reader weighting the word over the paragraph.

    THE ACT. The composer says what the beat is about; what the character DOES is the actor's, which
    holds who is present and what it would cost.
    """
    # `about` ONLY, and the omission of `unavailable` is the point. This scanned both until
    # 2026-09-08, which made the two halves of this module contradict each other: `compose_prompt`
    # ASKS for "any emotion the scene asked for that this character is not at" in `unavailable`, and
    # a composer that answered honestly was then refused for naming one. Measured on the first live
    # dispatch - every selection fell back to the deterministic floor.
    #
    # The rule is about DELIVERED text. `direction_for` reads `about` and nothing else, so
    # `unavailable` never reaches an actor; it is a diagnostic for the operator and the logs, and
    # naming an emotion is the only way it can do its job.
    text = str(selection.get("about") or "").lower()
    named = sorted(n for n in _forbidden_names() if re.search(r"\b%s\b" % re.escape(n), text))
    if named:
        raise ComposerError("verify: composer text names %s. The direction says what the beat is "
                            "about; the state text says what is felt, and it is attached after."
                            % ", ".join(named))
    acts = [v for v in ("he strikes", "she strikes", " hits ", " shouts ", "walks out", "refuses to",
                        "should say", "must tell", "will confront") if v in text]
    if acts:
        raise ComposerError("verify: composer text names an act (%s). What the character does is "
                            "theirs to decide." % ", ".join(a.strip() for a in acts))


def select_deterministic(rows, cap=3):
    """(selectable rows) -> a selection of the same shape the LLM half returns, without an LLM.

    THIS IS A FLOOR, NOT A REPLACEMENT FOR `compose_prompt`. The selecting half is supposed to read
    a brief and decide which two or three of a character's live emotions THIS BEAT is played on;
    that needs an LLM and is not built. Until it is, the chain cannot run end to end at all, so this
    picks by the only thing the rows carry and says plainly what it is not doing.

    RANKED BY RELATIVE POSITION ON ITS OWN LADDER, not by rung index. The index is not comparable
    across paths -- rung 8 of a twelve-rung ladder and rung 8 of a ten-rung one are different
    heights -- so the key is index/len(ladder), derived from BLOCKS rather than from a table that
    could rot. Ties break on path name so the same packet always composes the same prompt
    (CLAUDE.md hard rule 4: the engine is deterministic).

    NO FLOAT LEAVES. The ratio is selection-internal; what comes back is the path, the rung index
    and a primary flag, which is what `direction_for` consumes.

    `about` is deliberately EMPTY. It is the one field that needs the brief, and inventing one here
    would put words in the actor's mouth that no engine computed.
    """
    if not isinstance(rows, list):
        raise ComposerError("select_deterministic: rows must be the list from selectable(), got %r"
                            % type(rows).__name__)
    if not rows:
        return {"selected": [], "about": "", "unavailable": ""}
    # A FLOOR RUNG IS A TRUE READING AND A WRONG STAGE DIRECTION. `selectable` answers "what rung is
    # this character at" and returns a row for every built path, including the ones sitting at 0.0 --
    # that read is correct and stays. This half answers a different question, "which two or three of
    # a character's live emotions is this beat played on", and the slot it fills is framed by
    # src/engine/prompt.py as "stage directions ... they are what you DO, not a mood to describe".
    # Six of the eight ladders state no impulse at all at rung 1: DEFLATION "None. It is noted.",
    # GOODWILL / RECEPTIVITY / STIRRING "None yet.", SELF-REGARD "None."
    #
    # MEASURED 2026-09-08, and this is why the filter exists: an all-zero affect vector and one with
    # LUST at 0.95 both delivered DISTASTE 1, DEFLATION 1 and GOODWILL 1 -- byte-identical direction
    # for two entirely different characters, describing mild distaste, deflation and fondness to
    # someone in none of those states. Padding the cap with floor rows is not neutral; it is
    # misdescription.
    #
    # NOT a notability gate. `direction.direct_affect` had one (band >= 1, or deviating past a
    # threshold from the character's temperament mean) and it was retired with that renderer. This
    # is the conservative edge of what the evidence supports: the floor only. A character at rung 2
    # of everything still receives three near-floor blocks, and porting a real gate needs either
    # temperament in this module or an authored thought/action line in the data.
    ranked = sorted(
        [r for r in rows if r["rung"] > 1],
        key=lambda r: (-(float(r["rung"]) / len(BLOCKS[r["path"]])), r["path"]))
    if not ranked:
        return {"selected": [], "about": "", "unavailable": ""}
    picked = ranked[:max(1, int(cap))]
    return {"selected": [{"path": r["path"], "rung": r["rung"], "primary": (i == 0)}
                         for i, r in enumerate(picked)],
            "about": "",
            "unavailable": ""}


def direction_for(rows, selection):
    """(rows, a verified selection) -> the direction text the actor receives, primary first.

    The blocks are attached HERE, from the engine, by path and rung. The composer never held them, so
    nothing it wrote can have altered them.
    """
    by_key = {(r["path"], r["rung"]): r for r in rows}
    picked = sorted(selection.get("selected") or [],
                    key=lambda r: (not r.get("primary"), r["path"]))
    parts = []
    about = (selection.get("about") or "").strip()
    if about:
        parts.append("What this is about for you: %s" % about)
    for i, row in enumerate(picked):
        block = by_key[(row["path"], row["rung"])]["block"]
        lead = "Your state as you come into this moment." if i == 0 else "Also true of you right now."
        parts.append("%s This is what is true inside you; it is not a list of actions and it does "
                     "not tell you what to do. Act from it.\n\n%s" % (lead, block))
    return "\n\n".join(parts)


def _digest(text):
    """A short stable fingerprint of a text (sha256, first 16 hex): pins what was sent without storing it."""
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:16]


def record(rows, selection, text, by, fell_back="", descending=None):
    """What the actor was directed with this beat -> the manifest's `direction` entry.

    WRITTEN BECAUSE NOTHING KEPT IT (gate composer-direction-recorded, 2026-09-22). The direction was
    built on every actor call and thrown away, so no committed beat could say which emotions the actor
    played, at which rungs, whether the LLM composer or the deterministic floor chose them, or that the
    composer had fallen back. docs/record-contract.md: the manifest holds the packet's contents AS REFS.

    REFS, NOT PROSE. Each selected block is named by path, rung and the descent flag it was fetched
    with, and pinned by a hash: the blocks are engine constants, so a reader re-derives the text with
    `rungs.block_for(path, index, descending)` and the hash says whether the blocks have been
    regenerated since. `about` is kept verbatim - it is the composer's own verified prose, which
    nothing can re-derive. `text` pins the whole direction as the actor received it.

    by: "composer" (the verified LLM selection) or "floor" (`select_deterministic`); `fell_back` names
    the error when the composer was asked and the floor answered instead. `offered` is every path the
    engine put in front of the selector, at its rung, so the choice can be read against its options.
    """
    by_key = {(r["path"], r["rung"]): r for r in rows}
    down = descending if isinstance(descending, dict) else {}
    sel = selection or {}
    picked = sorted(sel.get("selected") or [], key=lambda s: (not s.get("primary"), s["path"]))
    return {
        "by": str(by),
        "fell_back": str(fell_back or ""),
        "offered": {r["path"]: r["name"] for r in rows},
        "selected": [{"path": s["path"], "rung": by_key[(s["path"], s["rung"])]["name"], "index": int(s["rung"]),
                      "primary": bool(s.get("primary")), "descending": bool(down.get(s["path"])),
                      "block": _digest(by_key[(s["path"], s["rung"])]["block"])} for s in picked],
        "about": str(sel.get("about") or ""),
        "text": _digest(text) if text else "",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--book", required=True)
    ap.add_argument("--char", required=True)
    ap.add_argument("--vault", default=os.environ.get("SWE_BOOKS"))
    ap.add_argument("--json", action="store_true", help="emit the selectable set as JSON")
    ap.add_argument("--brief", default="", help="what the scene needs from this character")
    ap.add_argument("--prompt-only", action="store_true",
                    help="emit the composer prompt instead of calling a model (no key on this machine)")
    ap.add_argument("--selection", help="path to a composer's JSON reply; verifies it and emits the direction")
    args = ap.parse_args()
    if not args.vault:
        ap.error("no book vault: pass --vault or set SWE_BOOKS")

    folder = None
    for name in sorted(os.listdir(args.vault)):
        if name.lower().replace(" ", "-") == args.book.lower().replace(" ", "-"):
            folder = os.path.join(args.vault, name)
            break
    if folder is None:
        ap.error("book %r not found in %s" % (args.book, args.vault))

    _world, chars = load_book(folder)
    char = character_or_raise(chars, args.char.lower())
    affect = char["current"]["affect"]
    rows = selectable(affect)

    if args.json:
        print(json.dumps(rows, indent=1))
        return 0

    if args.prompt_only:
        print(json.dumps(compose_prompt(rows, args.brief), indent=1))
        return 0

    if args.selection:
        # THE SEAM. There is no model key on this machine, so the composer runs the way every other
        # LLM stage in this repo does: emit the prompt, take the reply back through the gate. The
        # gate is the point — nothing a composer returns reaches an actor unverified.
        selection = json.loads(io.open(args.selection, encoding="utf-8").read())
        print(direction_for(rows, verify(selection, rows)))
        return 0

    print("%s — selectable emotions (built paths only; %d of 9 designed)"
          % (args.char, len(rungs.paths())))
    for r in rows:
        print("  %-14s rung %2d  %s" % (r["path"], r["rung"], r["name"]))
        print("      %s" % " ".join(r["block"].split())[:96] + "...")
    if not rows:
        print("  (nothing — no built path reads a primitive this character carries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
