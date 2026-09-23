#!/usr/bin/env python3
"""gen_rungs.py — docs/rungs/<PATH>.md -> src/engine/rung_blocks.py (generated, never hand-edited).

WHY A GENERATOR AND NOT A RUNTIME PARSE. The blocks are authored prose and the doc is where they are
edited; the engine must not depend on markdown formatting at import time. The repo already uses this
shape (scripts/gen_map.py, and the parked scripts/gen_emotion_names.py), and a generated module can
be diffed, so a change to the prose shows up as a change to the artefact.

WHAT IT REFUSES. A block that still carries its `[State: name]` label, because the label is measured
INERT and is deliberately not delivered — 2026-09-07, nine draws across three label conditions with
identical text: the arm labelled `annoyance` over violent text scored HIGHER than the arm labelled
`fury`, and a blind judge's grouping cut straight across the label conditions. The name is an
authoring and selection handle; it never reaches the actor.

Run: python scripts/gen_rungs.py
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)                          # for src.engine.rungs.PIVOTS
DOCS = os.path.join(REPO, "docs", "rungs")
OUT = os.path.join(REPO, "src", "engine", "rung_blocks.py")

# THE BANDS ARE CALIBRATION, NOT DERIVED — the same status arc.py:32 declares for its own constants.
# Width is set by how much RUNWAY a state needs before it should promote: a lived-in state absorbs
# event pressure without reclassifying, a rare state escalates on a small increment. Verified against
# the authored characters across the owner's books, who occupy rungs 2/3/4/6 only at rest, and against
# the appraisal asymptotes measured on a real run: a character resting at rung 3 climbs to 5 under a
# severe affront and to 7 under an extreme one, and one resting at 6 reaches 10 at his ceiling. So an
# ordinary temperament stops short of wanting someone hurt from a single wrong, which is right, and a
# hot one reaches the destructive band without reaching the two that need more than appraisal.
# No measurement fixes any individual edge. Move them by editing here and regenerating.
BANDS = {
    "DISPLEASURE": [
        (0.00, 0.07, "displeasure"),   # the null state; the first real wrong should promote out of it
        (0.07, 0.18, "annoyance"),
        (0.18, 0.31, "chafing"),       # widest pair: where a working adult actually lives
        (0.31, 0.44, "bristling"),
        (0.44, 0.56, "riled"),
        (0.56, 0.67, "seething"),
        (0.67, 0.77, "anger"),
        (0.77, 0.85, "outrage"),
        (0.85, 0.91, "fury"),
        (0.91, 0.95, "rage"),
        (0.95, 0.98, "berserk"),
        (0.98, 1.01, "amok"),          # top edge above 1.0 so a saturated vector lands, not falls through
    ],
    # RECEPTIVITY's bands are the ones docs/emotion-paths.md §3 assigned when the path passed its first
    # blind sort (rho 0.900), copied here rather than re-derived. Not yet verified against a cast at
    # rest the way DISPLEASURE's were — that measurement is owed and is listed in docs/rungs/RECEPTIVITY.md.
    "RECEPTIVITY": [
        (0.00, 0.08, "receptivity"),   # permission and nothing beyond it; the null state
        (0.08, 0.17, "liking"),
        (0.17, 0.26, "appreciation"),
        (0.26, 0.35, "pleasure"),
        (0.35, 0.45, "gladness"),
        (0.45, 0.55, "wonder"),
        (0.55, 0.64, "awe"),
        (0.64, 0.75, "delight"),       # thought becomes thought + action from here
        (0.75, 0.84, "elation"),       # three performed runs read this rung unstable; see the doc
        (0.84, 0.93, "rapture"),
        (0.93, 1.01, "ecstasy"),       # top edge above 1.0, same reason as amok
    ],
    # DISTASTE's bands are docs/emotion-paths.md 7's, copied not re-derived. The axis is REACH, not
    # consumption -- the one path of nine that is not "how much of you X has taken" -- and the
    # thought/action line sits at 0.15, the lowest of any path, because disgust is body-level.
    "DISTASTE": [
        (0.00, 0.15, "distaste"),      # declines it; nobody notices; reason still wins here (measured)
        (0.15, 0.35, "squeamishness"), # contact, not intake -- the action line
        (0.35, 0.60, "revulsion"),     # the body answers on its own; knowing better does not reach it
        (0.60, 0.82, "loathing"),
        (0.82, 1.01, "abomination"),   # contaminates by contact -- the rung that produces shunning
    ],
    # GOODWILL's bands are docs/emotion-paths.md 5's, copied not re-derived. The first OTHER-DIRECTED
    # path: "them" is the empty slot, never filled. The ACTION LINE is at rung 6 -- measured: rung 6
    # acted in every performed scenario, rung 2 in none. devotion is wide (0.70-0.85) on the design's
    # own finding that English has no rung between devotion and sacrifice.
    "GOODWILL": [
        (0.00, 0.09, "goodwill"),      # it has begun to register; noticing is the whole of it
        (0.09, 0.18, "warmth"),
        (0.18, 0.27, "fondness"),
        (0.27, 0.36, "concern"),
        (0.36, 0.45, "tenderness"),
        (0.45, 0.54, "compassion"),    # ACTION LINE -- enough of you to move you
        (0.54, 0.62, "solicitude"),
        (0.62, 0.70, "protectiveness"),
        (0.70, 0.85, "devotion"),      # widened to absorb the hole the design found at 0.79-0.90
        (0.85, 1.01, "sacrifice"),     # the engine's own 1.00 anchor; names an act -- objection recorded
    ],
    # STIRRING's bands are docs/emotion-paths.md 1's, copied not re-derived. WANT / SEEKING / LUST fold
    # into one path; the OBJECT is the actor's slot. Action line at rung 4. The HOLD: the object does not
    # get better or nearer up the ladder -- proximity is not magnitude.
    "STIRRING": [
        (0.00, 0.08, "stirring"),      # registered as more than the things around it; that is all
        (0.08, 0.18, "curiosity"),     # to KNOW it, not to have it
        (0.18, 0.30, "noticing"),      # oriented; costless to keep or drop
        (0.30, 0.40, "attraction"),    # ACTION LINE -- approach. Also an appraisal TAG name (prompt.py:148); different channel
        (0.40, 0.48, "urge"),          # a spike; passes if waited out
        (0.48, 0.58, "wanting"),       # continuous; starts itself
        (0.58, 0.66, "craving"),       # does not pass
        (0.66, 0.74, "zeal"),          # the day arranges around it
        (0.74, 0.85, "longing"),       # the absence is the sensation
        (0.85, 0.94, "fixation"),      # the world is recoverable, but it costs
        (0.94, 1.01, "obsession"),     # refusal is not on offer
    ],
    # SELF-REGARD's bands are MINE, not the design's -- docs/emotion-paths.md 6 gives none and marks the
    # primitive "(new)". Calibrated on the same logic as DISPLEASURE: lived-in rungs wide (dignity,
    # pride -- where adults rest), rare rungs narrow (9-11). Not yet verified against a resting cast.
    # NOTE: no primitive ever fed this path (the retired lookup had no row for it) -- the engine has no self-regard primary
    # (emotion-basis.md:71: pride = SEEKING-satisfied(self), a reflexive read the composer does not
    # perform). The ladder compiles; the composer cannot select it until that read exists.
    "SELF-REGARD": [
        (0.00, 0.10, "self-regard"),     # you count, to yourself; at rest
        (0.10, 0.22, "dignity"),         # a standing you would notice being touched
        (0.22, 0.35, "pride"),           # attached to a deed; widest pair with dignity
        (0.35, 0.46, "self-importance"), # design predicts 4/5 dissociate
        (0.46, 0.56, "vanity"),
        (0.56, 0.66, "conceit"),         # the estimate stops checking itself
        (0.66, 0.75, "arrogance"),       # others = audience or obstacle; still have FORCE
        (0.75, 0.83, "hubris"),          # exempt; absorbs grandiosity because it PRODUCES ACTION
        (0.83, 0.90, "narcissism"),      # others have no inside (clinical-usage flag; name never delivered)
        (0.90, 0.96, "megalomania"),     # the estimate replaced the world
        (0.96, 1.01, "apotheosis"),      # the estimate replaced YOU
    ],
    # DEFLATION's bands align with docs/emotion-paths.md §8 (hinge at ~0.60, ceiling at 0.90).
    # The axis is how much of you the lowness has taken: below 0.60 the currency is SCOPE (how much of
    # experience is coloured by grief/sorrow), above 0.60 the currency is FACULTIES (which capacities --
    # will, comfort, initiative, self -- have shut down). Hinge sits between inconsolability (6) and despondency (7).
    # LEVITY's bands are docs/emotion-paths.md §9's, copied not re-derived (built 2026-09-11 by the
    # owner's ruling; the 2026-09-07 finding that its axis and its low rungs disagree stands, and
    # production is the test). The thought/action line is at 0.10, second lowest after DISTASTE:
    # letting a joke through is already an act. Nine rungs; unmeasured.
    "LEVITY": [
        (0.00, 0.10, "amusement"),       # an opening registers and pleases you; nothing handed over
        (0.10, 0.22, "levity"),          # you let one through, and go back to it
        (0.22, 0.36, "playfulness"),     # disposed toward openings; you would take the next
        (0.36, 0.50, "banter"),          # inside the frame; you say what you would not
        (0.50, 0.62, "mischief"),        # you HUNT openings and push to see the frame hold
        (0.62, 0.74, "immersion"),       # you stop checking outside
        (0.74, 0.85, "absorption"),      # the activity sets the pace, not you
        (0.85, 0.94, "raptness"),        # the activity chooses; you follow
        (0.94, 1.01, "flow"),            # no gap between opening and act; no chooser
    ],
    "DEFLATION": [
        (0.00, 0.08, "deflation"),       # something has gone out of you; the rest works
        (0.08, 0.18, "dejection"),       # not lifted by what would usually lift you
        (0.18, 0.30, "sadness"),         # attention keeps returning; nothing comes of it
        (0.30, 0.42, "sorrow"),          # the returning has become staying
        (0.42, 0.60, "misery"),          # wanting closed to one point; widest -- where the grieving sit
        (0.60, 0.70, "inconsolability"), # HINGE: the one want cannot be met; you want it anyway
        (0.70, 0.80, "despondency"),     # stopped reaching, though reaching is possible
        (0.80, 0.90, "despair"),         # nothing ahead registers as yours
        (0.90, 0.96, "devastation"),     # CEILING at 0.90: nothing stays in place long enough to be wanted
        (0.96, 1.01, "hollowness"),      # no one in you to want
    ],
    # WARINESS's bands are docs/emotion-paths.md §4's, copied not re-derived.
    # The axis is how much of you a possible harm has taken over, following the sequence currency:
    # attention -> tone -> thought -> body -> the future -> conduct -> choice.
    "WARINESS": [
        (0.00, 0.07, "wariness"),
        (0.07, 0.14, "unease"),
        (0.14, 0.21, "misgiving"),
        (0.21, 0.29, "apprehension"),
        (0.29, 0.37, "worry"),
        (0.37, 0.45, "nervousness"),
        (0.45, 0.54, "anxiety"),
        (0.54, 0.62, "foreboding"),
        (0.62, 0.72, "dread"),
        (0.72, 0.80, "alarm"),
        (0.80, 0.87, "fright"),
        (0.87, 0.94, "panic"),
        (0.94, 1.01, "terror"),
    ],
}

# PATH_SOURCE — the path -> primitive lookup — LEFT THIS FILE 2026-09-10. The engine deleted it on
# 2026-09-08 when the paths became the stored state (92a9942); this generator kept a copy and kept
# emitting it, so a regeneration reverted that migration. The "was" column in docs/emotion-paths.md
# is the record; nothing reads it. tests/test_retired_vocabulary.py is the guard.

_HDR = re.compile(r"^(\d+)\s+—\s+(.+?)\s*$")
_LABEL = re.compile(r"\*\*\[State:[^\]]*\]\*\*\s*")


CLIMB_END = ("## The descent blocks", "## What must still be measured")
DESCENT_END = ("## What must still be measured",)


def _section(src, start, ends):
    """The doc text after `start` up to the FIRST of `ends`, or None when `start` is absent."""
    if start not in src:
        return None
    body = src.split(start, 1)[1]
    cut = min([body.index(e) for e in ends if e in body] or [len(body)])
    return body[:cut]


def _parse(path_name, body, what):
    """A section's "### N — name" chunks -> {rung_index: block_text}, each checked against BANDS.

    Shared by the climb and the descent parsers so one grammar serves both: the header is the rung's
    index and NAME (the name must be the band's — a renamed rung is caught here, not at runtime), the
    [State:] label is refused as text (it is inert as direction, measured 2026-09-07), a duplicate
    index is refused (the climb parser used to let a later chunk silently overwrite an earlier one).
    """
    out = {}
    for chunk in re.split(r"\n### ", body)[1:]:
        head, rest = chunk.split("\n", 1)
        m = _HDR.match(head.strip())
        if not m:
            continue
        idx, name = int(m.group(1)), m.group(2).strip()
        if not 1 <= idx <= len(BANDS[path_name]):
            raise SystemExit("%s %s rung %d does not exist; the ladder has %d rungs"
                             % (path_name, what, idx, len(BANDS[path_name])))
        text = _LABEL.sub("", rest.strip()).strip()
        expected = BANDS[path_name][idx - 1][2]
        if name != expected:
            raise SystemExit("%s %s rung %d is named %r in the doc and %r in BANDS — one of them is wrong"
                             % (path_name, what, idx, name, expected))
        if not text:
            raise SystemExit("%s %s rung %d has no block text" % (path_name, what, idx))
        if idx in out:
            raise SystemExit("%s %s rung %d appears twice in the doc" % (path_name, what, idx))
        out[idx] = text
    return out


def blocks_from(path_name):
    """docs/rungs/<PATH>.md -> {rung_index: block_text}. Raises if the doc disagrees with BANDS."""
    src_path = os.path.join(DOCS, "%s.md" % path_name)
    if not os.path.isfile(src_path):
        raise SystemExit("no authored blocks for %s: %s" % (path_name, src_path))
    src = io.open(src_path, encoding="utf-8").read()
    body = _section(src, "## The blocks", CLIMB_END)
    if body is None:
        raise SystemExit("%s has no '## The blocks' section" % path_name)
    out = _parse(path_name, body, "climb")
    missing = [i for i in range(1, len(BANDS[path_name]) + 1) if i not in out]
    if missing:
        raise SystemExit("%s is missing blocks for rungs %s" % (path_name, missing))
    return out


def descent_blocks_from(path_name):
    """docs/rungs/<PATH>.md "## The descent blocks" -> {rung_index: block_text}, or {} when absent.

    THE WAY DOWN IS NOT THE CLIMB REVERSED (docs/emotion-dynamics.md, the descent list; the redesign's
    gate 3). Above a path's PIVOT — the last rung a character can walk back from — a falling mood
    plays its own block; at and below it, the climb block serves both directions. So the section may
    only name rungs ABOVE the pivot, a path with no pivot (GOODWILL, DISTASTE: care cannot fall,
    revulsion ends when the thing is gone) may not carry one, and the section is ALL OR NOTHING: a
    half-authored descent would flip an actor between registers on the way down, which is the
    retired recovery tier's "drops onto fury" defect in a new coat. The pivots live in one place,
    `src/engine/rungs.PIVOTS`; this generator reads them, never copies them.
    """
    src_path = os.path.join(DOCS, "%s.md" % path_name)
    src = io.open(src_path, encoding="utf-8").read()
    body = _section(src, "## The descent blocks", DESCENT_END)
    if body is None:
        return {}
    from src.engine.rungs import PIVOTS
    if path_name not in PIVOTS:
        raise SystemExit("%s carries a descent section but has no pivot (rungs.PIVOTS): the design says "
                         "this path has no way down of its own" % path_name)
    out = _parse(path_name, body, "descent")
    pivot = PIVOTS[path_name]
    low = sorted(i for i in out if i <= pivot)
    if low:
        raise SystemExit("%s descent rungs %s are at or below the pivot (%d): below the pivot one block "
                         "serves both directions" % (path_name, low, pivot))
    wanted = list(range(pivot + 1, len(BANDS[path_name]) + 1))
    missing = [i for i in wanted if i not in out]
    if out and missing:
        raise SystemExit("%s descent section covers only some rungs above the pivot; missing %s — all "
                         "or nothing, so the way down stays one register" % (path_name, missing))
    return out


def main():
    parts = [
        '"""rung_blocks.py — GENERATED by scripts/gen_rungs.py. Do not hand-edit.\n',
        "",
        "Band edges are CALIBRATION (see the generator's note): width is how much runway a state needs",
        "before it should promote. Block text is authored in docs/rungs/<PATH>.md.",
        "",
        "The rung NAME is here for the composer to select by and for authoring. It is never delivered to",
        "the actor: measured 2026-09-07, the label is inert — identical text under a wrong label scored",
        "HIGHER than under its own. `rungs.block_for` returns the text alone.",
        '"""',
        "",
        "BANDS = {",
    ]
    blocks_out = ["", "BLOCKS = {"]
    descent_out = ["",
                   "# DESCENT_BLOCKS — the way down, above each path's pivot (src/engine/rungs.PIVOTS). Authored",
                   "# under '## The descent blocks' in docs/rungs/<PATH>.md; an empty dict is a path whose descent",
                   "# is not yet written (or, for GOODWILL and DISTASTE, has none by design). `rungs.block_for`",
                   "# serves one only when the caller says the mood is descending AND the rung is above the pivot.",
                   "DESCENT_BLOCKS = {"]
    for path_name in sorted(BANDS):
        blk = blocks_from(path_name)
        dsc = descent_blocks_from(path_name)
        parts.append("    %r: [" % path_name)
        for lo, hi, nm in BANDS[path_name]:
            parts.append("        (%.2f, %.2f, %r)," % (lo, hi, nm))
        parts.append("    ],")
        blocks_out.append("    %r: {" % path_name)
        for i in sorted(blk):
            blocks_out.append("        %d: %r," % (i, blk[i]))
        blocks_out.append("    },")
        if dsc:
            descent_out.append("    %r: {" % path_name)
            for i in sorted(dsc):
                descent_out.append("        %d: %r," % (i, dsc[i]))
            descent_out.append("    },")
        else:
            descent_out.append("    %r: {}," % path_name)
    parts.append("}")
    # THE TOMBSTONE the live module carries (hand-written by 92a9942, now emitted so a regeneration
    # keeps it): what PATH_SOURCE was and why it is gone.
    parts += [
        "# `PATH_SOURCE` LIVED HERE and is gone (2026-09-08). It mapped each path to one of the eight",
        "# Panksepp primitives so a path could be RENDERED from a stored float. The owner ruled the old",
        "# emotions are REPLACED by the paths, so there is nothing to translate from: a path IS the",
        "# state, `records.PATHS` names the set, and a character carries a position on each. The lookup",
        "# was also why RECEPTIVITY (mapped to JOY, never stored) and SELF-REGARD (no entry at all)",
        "# were unreachable, which cost 22 authored and verified rungs.",
    ]
    blocks_out.append("}")
    descent_out.append("}")
    io.open(OUT, "w", encoding="utf-8").write("\n".join(parts + blocks_out + descent_out) + "\n")
    total = sum(len(blocks_from(p)) for p in BANDS)
    down = sum(len(descent_blocks_from(p)) for p in BANDS)
    print("wrote %s — %d path(s), %d blocks, %d descent blocks"
          % (os.path.relpath(OUT, REPO), len(BANDS), total, down))


if __name__ == "__main__":
    sys.exit(main())
