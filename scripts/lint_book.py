#!/usr/bin/env python3
"""lint_book.py — pre-run validation of a book's world + characters (production-hardening).

Catches the authoring-error class BEFORE a run instead of at runtime: a missing baseline primary
(KeyError mid-run), a relationship key that is not a world-people id (its edge SILENTLY never
surfaces — content-guide), a malformed vault belief. A mechanical CHECK (the project's discipline);
report-only — authoring stays human. Consolidates + extends scripts/direct.py:startup_faults.

Usage:
  python scripts/lint_book.py --vault "<book>"                 # a real book (Obsidian vault)
  python scripts/lint_book.py --book ashford --char maren      # engine test fixtures
"""
import argparse
import json
import re
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURE_SUFFIXES = ("", "-slice", "-healer")   # this repo's fixture stems — they live HERE, not in src/engine (hard rule 1)
sys.path.insert(0, REPO)

from src.engine.records import PATHS, RecordError               # noqa: E402
from src.engine import books
from src.engine import attachments                               # noqa: E402  (gate 5: the block beside relationships)
from src.engine import systems as _systems                       # noqa: E402  (which systems the book runs)
from src.engine import contracts as _contracts                   # noqa: E402  (a file walked against its declarations)
from src.engine import contracts_sheet as _sheet_contract       # noqa: E402  (the character sheet, declared once)
from src.engine import contracts_world as _world_contract       # noqa: E402  (the world note, declared once)
from src.engine.state import _DIM_TO_PATH                        # noqa: E402  (the appraisal vocabulary, DERIVED)

# Never a second hand-written list: `state._DIM_TO_PATH` IS the engine's dimension
# vocabulary, and a copy here would be the eighth row of CLAUDE.md's duplicates table.
_APPRAISAL_DIMS = frozenset(_DIM_TO_PATH)

# DERIVED from the gate's own list, never a second copy — the words a percept drops.
from src.engine.gate import _words_from_attr as _wfa                 # noqa: E402
_STOPWORDS = frozenset(w for w in
                       ("the a an to of and is in at on by for with her his their its"
                        " she he they it who was has have").split())




_DECIMAL_IN_PROSE = re.compile(r"\d+\.\d+")


def _identity_strings(fixed, baseline):
    """Every (path, string) the STABLE IDENTITY PREFIX carries to the actor verbatim.

    Mirrors what `scene._build_stable` selects — persona / genotype / traits / model / drives /
    voice / provenance — and skips the keys `_strip_notes` already removes (`note`, and anything
    leading with an underscore), because those never reach the prompt.
    """
    out = []

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k) == "note" or str(k).startswith("_"):
                    continue
                walk(v, "%s.%s" % (path, k) if path else str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, "%s[%d]" % (path, i))
        elif isinstance(obj, str):
            out.append((path, obj))

    walk({"persona": {k: fixed.get(k) for k in ("id", "name", "people", "position")},
          "genotype": fixed.get("genotype", {})}, "")
    for key in ("traits", "model", "drives", "voice", "provenance"):
        walk(baseline.get(key, {}), key)
    return out



# THE SHEET'S FIELDS ARE DECLARED ONCE, in the engine (gate sheet-contract, 2026-09-25): src/engine/contracts_sheet.py.
# This file held its own lists of which fields are numbers, and walked them without
# the annotation rule the engine applies, so every `_note` in a number table was reported "not a number" - 19 of the
# 57 errors on the owner's four books. The per-character structural checks below are now `contracts.check`; what
# stays here is what one sheet cannot answer alone (the world's ids, the other sheets) and the prose and resting-face
# advisories.
_SEVERITY = {"error": "errors", "retired": "errors", "unread": "warnings", "unknown": "warnings", "advice": "warnings"}


def _grouped(findings, fields):
    """-> [(severity, where, what)]: findings saying the same thing about the same declared field, one line naming
    each key - a sheet still on the old basis reads as nine missing paths in one line, not nine lines."""
    groups = {}
    for f in findings:
        segs = tuple(f["path"].split(".")) if f["path"] else ()
        decl = _contracts.match(segs, fields) if segs else None
        pattern = decl.path if decl and "<" in decl.path else f["path"]
        groups.setdefault((f["severity"], f["code"], pattern, f["message"]), []).append(f["path"])
    out = []
    for (sev, _code, pattern, msg), paths in groups.items():
        if len(paths) == 1:
            out.append((sev, paths[0], msg))
        else:
            out.append((sev, pattern, "%s: %s" % (msg, ", ".join(p.rsplit(".", 1)[-1] for p in paths))))
    return out


def lint(world, chars):
    """Validate (world, chars). Returns {"errors": [...], "warnings": [...]}. Errors would break a
    run; warnings flag thin or silently-degrading authoring (the content-guide's live-field rules)."""
    errors, warnings = [], []
    if not isinstance(world, dict):
        return {"errors": ["world is not a dict"], "warnings": []}

    people_ids = {p.get("id") for p in (world.get("people") or []) if isinstance(p, dict) and p.get("id")}
    _registered = attachments.names_for(world)
    location_ids = {l.get("id") for l in (world.get("locations") or []) if isinstance(l, dict) and l.get("id")}
    # WHICH SYSTEMS THE BOOK RUNS (gate systems-registry, 2026-09-22): the systems it switches off stop being demanded
    # of the sheets below. A declaration the engine cannot honour is reported once, by the world's contract.
    try:
        _enabled = _systems.for_book(world)
    except RecordError:
        _enabled = _systems.defaults()
    # THE WORLD'S CONTRACT (src/engine/contracts_world.py, gate world-contract): every field's shape and whether anything
    # reads it; the laws, the tensions and the systems in their own modules' words
    for sev, where, what in _grouped(_contracts.check(world, _world_contract.WORLD, _enabled), _world_contract.WORLD):
        (errors if _SEVERITY[sev] == "errors" else warnings).append("world.%s: %s" % (where or "note", what))
    # LAWS REACHABILITY. src/engine/bible.py:_applies narrows a law by its `act` ONLY when the
    # CALLER supplies one, so a law carrying an act fires only if some scene cfg declares that
    # act (scripts/scene.py pre-flight). A law nothing can key is a rule the world states and
    # never applies -- verdict_for had no caller at all until 2026-08-22.
    _acts = sorted({str(l.get("act")) for l in (world.get("laws") or []) if isinstance(l, dict) and l.get("act")})
    if _acts:
        warnings.append("world.laws: %d law(s) are keyed by an `act`; a scene cfg must declare the "
                        "matching act or the law never fires. Acts: %s%s"
                        % (len(_acts), ", ".join(_acts[:4]), " ..." if len(_acts) > 4 else ""))
    # A TENSION WATCHING WHAT THE BOOK DOES NOT REGISTER - across the world and the cast, so beside the contract. A
    # malformed tension is the contract's to report; this reads only the ones that load.
    try:
        from src.engine.tensions import from_world as _tensions_from_world
        _tensions = _tensions_from_world(world)
    except (RecordError, ValueError):
        _tensions = []
    _people_ids = {p.get("id") for p in (world.get("people") or []) if isinstance(p, dict)}
    for _t in _tensions:
        _w = _t.get("watches") or {}
        for _loc in (_w.get("locations") or []):
            if location_ids and _loc not in location_ids:
                warnings.append("world.tensions[%s] watches location %r, which is not registered — "
                                "no act there can ever be in scope for it (Rule 6)"
                                % (_t.get("id"), _loc))
        for _who in (_w.get("parties") or []):
            if _people_ids and _who not in _people_ids and _who not in (chars or {}):
                warnings.append("world.tensions[%s] watches party %r, which is neither a registered "
                                "person nor a cast member — check the id" % (_t.get("id"), _who))

    # CAST-JOIN checks (character-authoring-rules.md Rule 1c). The packet is built by JOINS on ids;
    # the engine never infers a connection. A character authored only in characters/ is invisible to
    # gate._extract_named_entities ("Identity derives from world.people"), so no entity percept is
    # produced and scene._build_edges emits no edge — the scene partner is simply absent from the
    # packet while every file involved lints clean.
    for cid in sorted(chars or {}):
        if people_ids and cid not in people_ids:
            warnings.append("char %r: not in world.people — no other character can PERCEIVE them. "
                            "A character is not automatically an entity; add {id: %r, what: ...}" % (cid, cid))
    for cid, ch in sorted((chars or {}).items()):
        if not isinstance(ch, dict):
            continue
        for target in ((ch.get("current") or {}).get("relationships") or {}):
            if target in (chars or {}):
                back = ((chars[target].get("current") or {}).get("relationships") or {})
                if cid not in back:
                    warnings.append("char %r -> %r is ONE-WAY: %r has no relationship record back to "
                                    "%r, so %r gets no edge for %r in any scene they share"
                                    % (cid, target, target, cid, target, cid))

    for cid, ch in (chars or {}).items():
        tag = "char %r" % cid
        if not isinstance(ch, dict):
            errors.append("%s: not a dict" % tag)
            continue
        # THE CONTRACT (src/engine/contracts_sheet.py): every field's shape, whether this book must author it, and
        # whether anything reads it - one declaration, the engine's own validators for the blocks they own
        for sev, where, what in _grouped(_contracts.check(ch, _sheet_contract.SHEET, _enabled, {"registered": _registered}),
                                         _sheet_contract.SHEET):
            (errors if _SEVERITY[sev] == "errors" else warnings).append("%s: %s %s" % (tag, where or "the sheet", what))
        fixed, baseline, current = ({} if not isinstance(ch.get(k), dict) else ch[k] for k in ("fixed", "baseline", "current"))
        for _off in _systems.authored_for_off(ch, _enabled):
            warnings.append("%s: a %s block is authored, but this book switches the %s system off - it does "
                            "nothing" % (tag, _off, _off))

        # THE LAW, the half the engine cannot enforce. `direction.direct_identity` bands every
        # engine SCALAR before it reaches the actor, but an authored STRING is the author's prose
        # and the engine must not rewrite it — so a design note like "patience x0.4 ·
        # temper x1.2" written into a value reaches the actor as a raw stat, and only a human
        # can decide whether that is wanted. Found on a real book the first time this ran.
        for path, text in _identity_strings(fixed, baseline):
            hits = sorted(set(_DECIMAL_IN_PROSE.findall(text)))
            if hits:
                warnings.append(
                    "%s: %s carries %s in AUTHORED TEXT — the identity prefix reaches the actor "
                    "verbatim, so these land as raw stats (design.md: 'The LLM never sees raw "
                    "stats'). The engine bands its own numbers and will not rewrite your prose: "
                    "move the calibration into a `note` key (stripped) or say it in words."
                    % (tag, path, ", ".join(hits[:4])))

        # content-guide rule: a relationship key must be a world.people id or the edge never surfaces
        for k in (current.get("relationships") or {}):
            if people_ids and k not in people_ids:
                warnings.append("%s: relationship %r is not a world.people id — its edge will never surface in a scene" % (tag, k))
        # THE RESTING FACE'S RECEIPTS - a rest above the cap is honoured and named, so it is a decision and never an
        # accident; a stored mean a whole rung from its rest word is the old scale, or a rest moved without its mean.
        # Advice computed by heritable, not a field's shape: the contract has checked the words themselves.
        from src.engine import heritable as _her
        temp = baseline.get("temperament") or {}
        for p in (PATHS if isinstance(temp, dict) else ()):
            row = temp.get(p)
            if not isinstance(row, dict):
                continue
            try:
                over, rung = _her.over_cap(p, temp)
                if over:
                    warnings.append("%s: baseline.temperament.%s.rest sits at rung %d (%s) — above the "
                                    "cap of %d for a resting disposition. Deliberate? Then this note "
                                    "is the receipt." % (tag, p, rung, _her.BANDS[p][rung - 1][2], _her.REST_CAP[p]))
                if "mean" in row:
                    have = _her.rung_of_mean(p, float(row["mean"]))
                    want = _her.rest_rung(p, temp) or _her.rung_of_mean(p, _her.rest_mean(p, temp))
                    if have != want:
                        warnings.append("%s: baseline.temperament.%s.mean %.2f sits at rung %d (%s) but "
                                        "rest says %r (rung %d). The mean is seeded from the rest word "
                                        "once and the arc engine moves it after; a whole rung apart "
                                        "is the old scale, or a rest moved without its mean — delete "
                                        "the mean to re-seed it, or move the rest"
                                        % (tag, p, float(row["mean"]), have, _her.BANDS[p][have - 1][2],
                                           _her.word(row.get("rest"), default="quiet"), want))
            except (RecordError, ValueError, TypeError):
                pass
        loc = current.get("location")
        if loc and location_ids and loc not in location_ids:
            warnings.append("%s: current.location %r is not a world.locations id — no location percept "
                            "will be produced there" % (tag, loc))

    return {"errors": errors, "warnings": warnings}


def _load_fixture(book, char):
    def find(folder, stem):
        try:                           # ONE copy of this search — direct.py carried the other
            return books.fixture_path(REPO, folder, stem, _FIXTURE_SUFFIXES)
        except books.BookError as e:
            raise SystemExit(str(e))
    with open(find("world", book), encoding="utf-8") as fh:
        world = json.load(fh)
    with open(find("characters", char), encoding="utf-8") as fh:
        ch = json.load(fh)
    return world, {ch.get("fixed", {}).get("name", char).lower(): ch}


def main():
    ap = argparse.ArgumentParser(description="lint a book's world + characters before a run")
    ap.add_argument("--vault", default=None, help="BOOK folder (Obsidian vault)")
    ap.add_argument("--book", default=None, help="engine test-fixture world stem (use with --char)")
    ap.add_argument("--char", default=None, help="fixture character stem (with --book)")
    args = ap.parse_args()

    if args.vault:
        from src.engine.vault import load_book, VaultError
        try:
            world, chars = load_book(args.vault)
        except VaultError as e:            # a contract breach IS a lint error, not a traceback
            print("  ERROR %s" % e)
            print("\nlint: 1 error(s), 0 warning(s)")
            return 1
    elif args.book and args.char:
        world, chars = _load_fixture(args.book, args.char)
    else:
        raise SystemExit("pass --vault <book>, or --book <stem> --char <stem>")

    report = lint(world, chars)
    for w in report["warnings"]:
        print("  WARN  %s" % w)
    for e in report["errors"]:
        print("  ERROR %s" % e)
    n_e, n_w = len(report["errors"]), len(report["warnings"])
    # "clean" means nothing fired. A run with warnings is NOT clean - saying so is how 8
    # warnings naming an empty vault got read as a pass.
    print("\nlint: %d error(s), %d warning(s)%s" % (n_e, n_w, " — clean" if not (n_e or n_w) else ""))
    return 1 if n_e else 0


if __name__ == "__main__":
    sys.exit(main())
