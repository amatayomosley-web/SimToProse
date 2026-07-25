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
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.records import PRIMARIES                            # noqa: E402

_OPTIONAL_BASELINE = ("traits", "model", "skills", "voice", "drives")


def lint(world, chars):
    """Validate (world, chars). Returns {"errors": [...], "warnings": [...]}. Errors would break a
    run; warnings flag thin or silently-degrading authoring (the content-guide's live-field rules)."""
    errors, warnings = [], []
    if not isinstance(world, dict):
        return {"errors": ["world is not a dict"], "warnings": []}

    people_ids = {p.get("id") for p in (world.get("people") or []) if isinstance(p, dict) and p.get("id")}
    if not world.get("lexicon"):
        warnings.append("world: no lexicon — perception falls back to generic extraction (kind + leading words), thin")
    for i, loc in enumerate(world.get("locations") or []):
        if not (isinstance(loc, dict) and loc.get("id")):
            warnings.append("world.locations[%d]: missing id" % i)
    for i, p in enumerate(world.get("people") or []):
        if not (isinstance(p, dict) and p.get("id")):
            warnings.append("world.people[%d]: missing id" % i)

    for cid, ch in (chars or {}).items():
        tag = "char %r" % cid
        if not isinstance(ch, dict):
            errors.append("%s: not a dict" % tag)
            continue
        for sec in ("fixed", "baseline", "current"):
            if not isinstance(ch.get(sec), dict):
                errors.append("%s: missing/invalid section %r (assemble requires it)" % (tag, sec))
        fixed, baseline, current = ch.get("fixed", {}), ch.get("baseline", {}), ch.get("current", {})

        if not str(fixed.get("name", "")).strip():
            errors.append("%s: fixed.name missing" % tag)
        miss_t = [p for p in PRIMARIES if p not in (baseline.get("temperament") or {})]
        if miss_t:
            errors.append("%s: baseline.temperament missing primaries %s (decay/profile need all 7)" % (tag, miss_t))
        aff = current.get("affect") or {}
        miss_a = [p for p in PRIMARIES if p not in aff]
        if miss_a:
            errors.append("%s: current.affect missing primaries %s (appraise needs all 7)" % (tag, miss_a))
        for p, v in aff.items():
            if p in PRIMARIES and not (isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0):
                errors.append("%s: current.affect[%s]=%r not in [0,1]" % (tag, p, v))
        if not isinstance(current.get("condition"), dict):
            errors.append("%s: current.condition missing or not a dict (assemble requires a dict)" % tag)

        # content-guide rule: a relationship key must be a world.people id or the edge never surfaces
        for k in (current.get("relationships") or {}):
            if people_ids and k not in people_ids:
                warnings.append("%s: relationship %r is not a world.people id — its edge will never surface in a scene" % (tag, k))
        for opt in _OPTIONAL_BASELINE:
            if not baseline.get(opt):
                warnings.append("%s: baseline.%s absent — thin (read where present)" % (tag, opt))
        for j, b in enumerate(current.get("vault") or []):
            if not (isinstance(b, dict) and str(b.get("claim", "")).strip()):
                warnings.append("%s: vault[%d] has no claim" % (tag, j))
            elif "provenance" not in b:
                warnings.append("%s: vault[%d] missing provenance (seed/authored/lived/witnessed/learned)" % (tag, j))

    return {"errors": errors, "warnings": warnings}


def _load_fixture(book, char):
    def find(folder, stem):
        for cand in (stem, stem + "-slice", stem + "-healer"):
            p = os.path.join(REPO, folder, cand + ".json")
            if os.path.exists(p):
                return p
        raise SystemExit("no %s/%s*.json found" % (folder, stem))
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
        from src.engine.vault import load_book
        world, chars = load_book(args.vault)
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
    print("\nlint: %d error(s), %d warning(s)%s" % (n_e, n_w, " — clean" if n_e == 0 else ""))
    return 1 if n_e else 0


if __name__ == "__main__":
    sys.exit(main())
