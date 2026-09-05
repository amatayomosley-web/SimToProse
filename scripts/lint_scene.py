"""lint_scene.py — check a scene cfg against the BOOK, not just against the schema.

THE GAP THIS CLOSES. `docs/scene-authoring-rules.md` states six normative rules in 913 tokens and
nothing checked any of them. World notes and character notes have `scripts/lint_book.py`; scene
configs — the third authoring surface — had no validator at all.

`load_scene_cfg` in `scripts/scene.py` checks that `situation` is a non-empty string and `cast` is a
non-empty list of `{id, drive}`. It cannot do more, because it never sees the world: a cfg naming a
cast member who does not exist, a subject nobody can perceive, or an act no law keys parses cleanly
and then fails at runtime — or worse, runs, and produces a scene where the intended mechanism never
fires and nobody can tell why.

WHAT IS AND IS NOT CHECKED, stated in the output itself so a clean run never reads as "all six rules
verified":

  ERRORS   — resolvable facts. An id that names nobody is not a matter of taste.
  WARNINGS — lexical heuristics for rules 1 and 2. A phrase list cannot decide whether a situation
             scripts a beat, so these never block. A guard that blocks correct work gets switched
             off, which is worse than one that advises.
  UNCHECKED — rules 4 and 6 (wound collision, epistemic containment) are semantic and are NOT
             mechanized here. Rule 4's honest surface is behavioural: the engine already prints a
             lull when drives align, which is the real detector.

RULE 5 IS NOW CHECKED, and the sequence matters. When this linter was first written, Rule 5 required
"3-5 concrete props" and `props` was a field the engine read NOWHERE. The check was deliberately NOT
written then: implementing it would have meant inventing the field to satisfy a linter, which
manufactures the specified-but-reaching-nothing defect this repo has found nine times. The rule was
annotated UNBACKED in the doc instead. Props were then wired to the actor as percepts
(`gate.perception_scope`), and only after they reached something did the count become enforceable.
"""
import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.vault import load_book                          # noqa: E402
from scene import load_scene_cfg                                # noqa: E402

# Rule 1 — the situation must establish conditions and pressure, not stage the exchange. These
# markers are the doc's own violation examples generalised; they ADVISE, they do not block.
_SCRIPTING = (r"\bexplains?\b", r"\bexplaining\b", r"\btells\s+\w+\s+about\b",
              r"\bdescribes?\b", r"\brecounts?\b", r"\bteaches?\b", r'"[^"]{20,}"')
# Rule 2 — a drive must answer "what do I want from the person in front of me", not address a reader.
_META_GOAL = (r"\bthe reader\b", r"\bintroduce\b", r"\bestablish\b", r"\bexposit", r"\bworld ?lore\b",
              r"\bset ?up\b", r"\bshowcase\b", r"\bdemonstrate\b")


def _people(world):
    return {str(p.get("id")) for p in (world.get("people") or []) if isinstance(p, dict) and p.get("id")}


def _locations(world):
    return {str(l.get("id")) for l in (world.get("locations") or []) if isinstance(l, dict) and l.get("id")}


def _law_acts(world):
    return {str(l.get("act")) for l in (world.get("laws") or []) if isinstance(l, dict) and l.get("act")}


def lint_cfg(cfg, world, chars):
    """-> (errors, warnings, unchecked). Errors are resolvable facts; warnings are heuristics."""
    errors, warnings = [], []
    people, locs, acts = _people(world), _locations(world), _law_acts(world)
    known = people | set(chars or {})

    cast = cfg.get("cast") or []
    ids = [str(c.get("id")) for c in cast if isinstance(c, dict)]

    for cid in ids:
        if cid not in known:
            errors.append("cast %r is not a character in this book and not in world.people — no one "
                          "can perceive them and the engine has no sheet to act from" % cid)
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append("cast lists %s more than once — one seat per character per scene"
                      % ", ".join(sorted(dupes)))
    if len(ids) < 2:
        warnings.append("cast has %d member(s): a scene with no second party cannot produce the "
                        "wound collision rule 4 calls the dynamic engine" % len(ids))

    situation = str(cfg.get("situation") or "")
    for c in cast:
        if not isinstance(c, dict):
            continue
        drive = str(c.get("drive") or "").strip()
        cid = c.get("id")
        if drive and drive.lower() == situation.strip().lower():
            errors.append("cast %r: drive is a copy of the situation — a drive is what THIS person "
                          "wants from the other, not a restatement of the moment (rule 2)" % cid)
        for pat in _META_GOAL:
            if re.search(pat, drive, re.I):
                warnings.append("cast %r: drive contains %r — rule 2 wants an in-room want, not a "
                                "goal aimed at the reader or the exposition" % (cid, pat.strip("\\b")))
                break

    drives = [str(c.get("drive") or "").strip().lower() for c in cast if isinstance(c, dict)]
    if len(drives) > 1 and len(set(drives)) == 1:
        warnings.append("every cast member has the SAME drive — aligned goals produce zero urge and "
                        "the scene lulls immediately (rule 4)")

    for pat in _SCRIPTING:
        if re.search(pat, situation, re.I):
            warnings.append("situation matches %r — rule 1 wants physical conditions and pressure, "
                            "not the exchange staged in advance" % pat)
            break

    subj = cfg.get("subject")
    subj_id = subj[0] if isinstance(subj, (list, tuple)) and len(subj) == 2 else None
    if subj_id and str(subj_id) not in known:
        errors.append("subject %r resolves to nobody in this book — the regard scoping it exists for "
                      "will never fire" % subj_id)

    loc = cfg.get("location")
    if loc and str(loc) not in locs:
        errors.append("location %r is not in world.locations — no scene can produce a location "
                      "percept for it" % loc)

    # DIMENSION LEGALITY — docs/template-scene-blueprint.md's pre-flight says items 1-4 are
    # mechanically covered; item 4 (legal dimension keys) was not checked anywhere. An unknown key
    # is not rejected downstream either: state.appraise silently no-ops on it (_DIM_TO_PRIMARY.get),
    # so a typo'd dimension is authored, shown to nobody, and computes nothing.
    from src.engine.state import _DIM_TO_PRIMARY as _LEGAL_DIMS
    dims = (cfg.get("opening_tags") or {}).get("dimensions")
    if isinstance(dims, dict):
        for k, v in dims.items():
            if k not in _LEGAL_DIMS:
                errors.append("opening_tags.dimensions key %r is not one of the legal seven (%s) — "
                              "appraise() silently ignores it" % (k, ", ".join(sorted(_LEGAL_DIMS))))
            elif isinstance(v, str):
                # A WORD is the authored form (standard-vectors.md §3); scene.py resolves it at the
                # cfg parse seam. Only an unknown word is an error, and the message names the ladder.
                from src.engine.severity import WORDS
                if v.strip().lower() not in WORDS:
                    errors.append("opening_tags.dimensions[%r] = %r is not a severity word — use one "
                                  "of: %s" % (k, v, ", ".join(WORDS)))
            elif not isinstance(v, (int, float)) or not (0.0 <= float(v) <= 1.0):
                errors.append("opening_tags.dimensions[%r] = %r is neither a severity word (%s) nor "
                              "a number in [0,1]" % (k, v, ", ".join(__import__(
                                  "src.engine.severity", fromlist=["WORDS"]).WORDS)))

    act = (cfg.get("opening_tags") or {}).get("act") or cfg.get("act")
    if act and str(act) not in acts:
        errors.append("act %r is keyed by no law in this world — the pre-flight will find nothing to "
                      "bear on it (world.laws declares: %s)"
                      % (act, ", ".join(sorted(acts)) or "no acts at all"))

    # RULE 5 — now enforceable. It named `props` for months while the engine read no such field;
    # since 2026-08-24 props reach the actor as percepts (gate.perception_scope), so the count is a
    # real constraint rather than advice about a field that went nowhere.
    props = cfg.get("props") or []
    if not props:
        warnings.append("no props declared — rule 5 wants 3-5 concrete objects that can be held, "
                        "counted or slid; without affordances the actors have nothing to do with "
                        "their hands and the scene drifts to talking heads")
    elif not (3 <= len(props) <= 5):
        errors.append("props: %d declared, rule 5 wants 3-5 — %s"
                      % (len(props), "too few to furnish the room" if len(props) < 3
                         else "too many to stay in the actor's attention"))
    for pr in props:
        if len(str(pr).strip()) < 3:
            errors.append("prop %r is not a graspable object" % pr)

    unchecked = [
        "rule 4 (wound collision) — semantic; the engine's own lull print is the real detector",
        "rule 6 (epistemic containment) — semantic; class and institutional boundaries need a reader",
    ]
    return errors, warnings, unchecked


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--book", required=True, help="book slug under $SWE_BOOKS, or a path")
    ap.add_argument("--scene", required=True, help="path to the scene cfg JSON")
    args = ap.parse_args()

    from src.engine import books
    try:
        book_dir = books.resolve(args.book)
        world, chars = load_book(book_dir)
    except Exception as e:
        raise SystemExit("could not load book: %s" % e)
    try:
        cfg = load_scene_cfg(args.scene)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print("SCHEMA: %s" % e)
        return 1

    errors, warnings, unchecked = lint_cfg(cfg, world, chars)
    print("lint_scene: %s against %s" % (os.path.basename(args.scene), os.path.basename(book_dir)))
    for e in errors:
        print("  ERROR    %s" % e)
    for w in warnings:
        print("  warning  %s" % w)
    print("  -- NOT CHECKED (a clean run above does not mean these hold) --")
    for u in unchecked:
        print("     %s" % u)
    print("\n%d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
