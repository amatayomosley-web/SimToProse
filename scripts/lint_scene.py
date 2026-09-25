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
from src.engine import attachments as _attachments               # noqa: E402  (gate 5: the director's declarations)
from src.engine import systems as _systems                       # noqa: E402  (which systems the book runs)
from src.engine import contracts as _contracts                   # noqa: E402  (a file walked against its declarations)
from src.engine import contracts_scene as _scene_contract       # noqa: E402  (the scene file, declared once)
from src.engine.records import RecordError                       # noqa: E402
from scene import load_scene_cfg                                # noqa: E402

# Rule 1 — the situation must establish conditions and pressure, not stage the exchange. These
# markers are the doc's own violation examples generalised; they ADVISE, they do not block.
_SCRIPTING = (r"\bexplains?\b", r"\bexplaining\b", r"\btells\s+\w+\s+about\b",
              r"\bdescribes?\b", r"\brecounts?\b", r"\bteaches?\b", r'"[^"]{20,}"')
# Rule 2 — a drive must answer "what do I want from the person in front of me", not address a reader.
_META_GOAL = (r"\bthe reader\b", r"\bintroduce\b", r"\bestablish\b", r"\bexposit", r"\bworld ?lore\b",
              r"\bset ?up\b", r"\bshowcase\b", r"\bdemonstrate\b")


def _list(v):
    """A world list as the engine walks it - anything else is lint_book's finding, never a crash here."""
    return v if isinstance(v, list) else []


def _people(world):
    return {str(p.get("id")) for p in _list(world.get("people")) if isinstance(p, dict) and p.get("id")}


def _locations(world):
    return {str(l.get("id")) for l in _list(world.get("locations")) if isinstance(l, dict) and l.get("id")}


def _law_acts(world):
    return {str(l.get("act")) for l in _list(world.get("laws")) if isinstance(l, dict) and l.get("act")}


def lint_cfg(cfg, world, chars):
    """-> (errors, warnings, unchecked). Errors are resolvable facts; warnings are heuristics.

    THE FILE'S OWN CONTRACT FIRST (src/engine/contracts_scene.py, gate scene-contract): every key's shape, in its
    engine module's words - best on the file as written, which `main` passes; what stays below is what one file
    cannot answer alone (the book's cast, places, groups and laws) and the craft rules."""
    errors, warnings = [], []
    people, locs, acts = _people(world), _locations(world), _law_acts(world)
    known = people | set(chars or {})
    try:
        _sys = _systems.for_book(world)
    except RecordError:
        _sys = _systems.defaults()                   # lint_book reports a bad declaration; this cfg is not the place
    for f in _contracts.check(cfg, _scene_contract.SCENE, _sys):
        # an ERROR is exactly what refuses the run (contracts.refuses, gate run-start-refusal): a file that lints clean starts
        (errors if _contracts.refuses(f) else warnings).append(" ".join(x for x in (f["path"], f["message"]) if x))

    cast = _list(cfg.get("cast"))
    ids = [str(c.get("id")) for c in cast if isinstance(c, dict)]

    for cid in ids:
        if cid not in set(chars or {}):
            errors.append("cast %r is not a character in this book — the run refuses a cast member with no sheet "
                          "to act from%s" % (cid, " (world.people names them, but a person is not a character)"
                                             if cid in people else ""))
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

    # THE DIRECTOR'S HOLDS against the book (the contract has checked each declaration's shape and relation word): a
    # cast member of this scene, and a place or group the world registers.
    try:
        _names = set(_attachments.names_for(world))
    except (RecordError, TypeError):                 # lint_book names the bad locations or groups
        _names = set()
    for d in _list(cfg.get("attachments")):
        if not isinstance(d, dict):
            continue
        if str(d.get("char")) not in ids:
            errors.append("attachments: %r is not in this scene's cast" % d.get("char"))
        if str(d.get("entity")) not in _names:
            errors.append("attachments: %r is not a place or group the world registers (%s)"
                          % (d.get("entity"), ", ".join(sorted(_names)) or "nothing registered"))

    act = cfg.get("act")                             # the law check reads this one; opening_tags.act reaches nothing
    if act and str(act) not in acts:
        errors.append("act %r is keyed by no law in this world — the pre-flight will find nothing to "
                      "bear on it (world.laws declares: %s)"
                      % (act, ", ".join(sorted(acts)) or "no acts at all"))

    # RULE 5 — now enforceable. It named `props` for months while the engine read no such field;
    # since 2026-08-24 props reach the actor as percepts (gate.perception_scope), so the count is a
    # real constraint rather than advice about a field that went nowhere.
    props = _list(cfg.get("props"))                  # anything else is the contract's finding, above
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
    # THE FILE AS WRITTEN (gate scene-contract): the loader turns words into numbers, refuses `elapsed` and exits on
    # a bad voice, so the contract reads the JSON first; the loader's own refusal is reported after, if it has one
    try:
        with open(args.scene, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except (OSError, ValueError) as e:
        print("SCHEMA: %s" % e)
        return 1
    if not isinstance(cfg, dict):
        print("SCHEMA: the scene file must be a JSON object")
        return 1

    errors, warnings, unchecked = lint_cfg(cfg, world, chars)
    if not errors:
        try:
            load_scene_cfg(args.scene)
        except (ValueError, SystemExit) as e:        # the loader exits on a bad voice; it is still a refusal to report
            errors.append("the loader refuses this file: %s" % e)
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
