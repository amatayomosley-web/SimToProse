#!/usr/bin/env python3
"""catalog.py — a book's people, places, groups and things, ranked by how much the book uses them.

    python scripts/catalog.py --book <slug|path>            # writes <book>/runs/catalog.md
    python scripts/catalog.py --book <slug|path> --stdout   # prints it, writes nothing

GENERATED and non-authoritative, like the canon digest: the notes are the record, this is a view of them, and it is
regenerated whole, never edited. It is written into the book's `runs/` - the engine's loader reads `world/`,
`characters/` and `people/` and nothing else - so nothing in the engine reads it and it cannot become a second
source of truth (the Fable review, 2026-10-01).

LEVEL is where the book declares someone (BLUEPRINT-world.md §7.1a): `played` - a sheet in `characters/`;
`seeable` - in `world.people` (the world note's list, or a `people/` note typed `person`); `reference` - a `people/`
note of any other type, which the engine never loads. Played and seeable are separate: a sheet with no people entry
is played and seen by no one.

USE is what the book does with them: the scene files whose cast names them, the sheets that hold a relationship to
them, and the notes that link to their note (`staging/`, `runs/` and dot-folders are not read). Places: the scenes
set there and the sheets that hold them (`loc.<id>`). Groups: their members and the sheets that hold them
(`grp.<tag>`). Things: each scene file's props - the engine has no other thing.

Order: people by level (played, seeable, reference), then by use (a scene counts 3, a tie 2, a link 1), then name;
places and groups by use; everything sorted, so the same book always gives the same bytes. Reads the book; writes
one file. Stdlib only.
"""
import argparse
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import books, vault                              # noqa: E402

OUT = "catalog.md"
SKIP = {"runs", "staging"}
LEVELS = ("played", "seeable", "reference")


def _notes(book_dir, sub):
    d = os.path.join(book_dir, sub)
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".md")] if os.path.isdir(d) else []


def _scenes(book_dir):
    out = []
    for p in sorted(_listing(os.path.join(book_dir, "scenes"), ".json")):
        try:
            cfg = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue                                   # not a scene file this script can read; the lint says why
        if isinstance(cfg, dict):
            out.append((str(cfg.get("name") or os.path.splitext(os.path.basename(p))[0]), cfg))
    return out


def _listing(d, ext):
    return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(ext)] if os.path.isdir(d) else []


def _link_targets(book_dir):
    """{note path: set of link targets, lower-cased basenames} for every note the author keeps."""
    out = {}
    for root, dirs, files in os.walk(book_dir):
        dirs[:] = sorted(x for x in dirs if x not in SKIP and not x.startswith("."))
        for f in sorted(files):
            if f.endswith(".md") and f != OUT:
                p = os.path.join(root, f)
                text = io.open(p, encoding="utf-8", errors="replace").read()
                # a link inside a markdown table escapes its alias pipe ("[[Tam\|the miller]]"): drop the backslash
                out[p] = {os.path.basename(t.strip().rstrip("\\")).lower() for t in vault._LINK_RE.findall(text)}
    return out


def build(book_dir):
    """-> {"people": [...], "places": [...], "groups": [...], "things": [(scene, [prop])]} for one book."""
    world, chars = vault.load_book(book_dir)
    people = {}

    def row(pid):
        return people.setdefault(pid, {"id": pid, "name": None, "levels": set(), "notes": [], "scenes": [],
                                       "ties": [], "links": 0})

    for p in _notes(book_dir, "characters"):
        n = vault.parse_note(p)
        cid = str(n["id"]).lower().replace(" ", "_")
        if cid in chars:
            r = row(cid)
            r["levels"].add("played")
            r["notes"].append(p)
            r["name"] = r["name"] or (chars[cid].get("fixed") or {}).get("name")
    for p in world.get("people") or []:
        if isinstance(p, dict) and p.get("id"):
            r = row(str(p["id"]))
            r["levels"].add("seeable")
            r["name"] = p.get("name") or r["name"]
    for p in _notes(book_dir, "people"):
        n = vault.parse_note(p)
        eng = n["engine"] if isinstance(n["engine"], dict) else {}
        r = row(str(eng.get("id") or n["id"]).lower().replace(" ", "_"))
        r["notes"].append(p)
        if (n["type"] or "person") != "person":
            r["levels"].add("reference")
        title = re.search(r"^#\s+(.+)$", n["body"], re.M)          # "# Bryony Teal — the shepherd": the name part
        r["name"] = r["name"] or (title.group(1).split(" — ")[0].strip() if title else None)

    scenes = _scenes(book_dir)
    for label, cfg in scenes:
        for c in cfg.get("cast") or []:
            cid = str(c.get("id") if isinstance(c, dict) else c)
            if cid in people:
                people[cid]["scenes"].append(label)
    holds = {}
    for cid in sorted(chars):
        cur = chars[cid].get("current") if isinstance(chars[cid].get("current"), dict) else {}
        for k in sorted((cur.get("relationships") or {}) if isinstance(cur.get("relationships"), dict) else {}):
            if k in people:
                people[k]["ties"].append(cid)
        for k in sorted((cur.get("attachments") or {}) if isinstance(cur.get("attachments"), dict) else {}):
            holds.setdefault(k, []).append(cid)
    targets = _link_targets(book_dir)
    for r in people.values():
        mine = {os.path.normcase(os.path.abspath(p)) for p in r["notes"]}
        keys = {os.path.splitext(os.path.basename(p))[0].lower() for p in r["notes"]} | {r["id"]}
        r["links"] = sum(1 for p, t in targets.items()
                         if os.path.normcase(os.path.abspath(p)) not in mine and t & keys)

    def score(r):
        return 3 * len(r["scenes"]) + 2 * len(r["ties"]) + r["links"]

    ordered = sorted(people.values(), key=lambda r: (
        min(LEVELS.index(lv) for lv in r["levels"]) if r["levels"] else len(LEVELS), -score(r), (r["name"] or r["id"]).lower()))
    for r in ordered:
        r["levels"] = [lv for lv in LEVELS if lv in r["levels"]]
        r["note"] = os.path.splitext(os.path.basename(r["notes"][0]))[0] if r["notes"] else None
        del r["notes"]
    places = []
    for loc in world.get("locations") or []:
        if isinstance(loc, dict) and loc.get("id"):
            lid = str(loc["id"])
            places.append({"id": lid, "what": str(loc.get("what") or ""),
                           "scenes": [s for s, cfg in scenes if str(cfg.get("location") or "") == lid],
                           "holders": holds.get("loc." + lid, [])})
    places.sort(key=lambda p: (-(3 * len(p["scenes"]) + 2 * len(p["holders"])), p["id"]))
    members = {}
    for p in world.get("people") or []:
        for tag in (p.get("groups") or []) if isinstance(p, dict) and isinstance(p.get("groups"), list) else []:
            members.setdefault(str(tag), []).append(str(p.get("id")))
    groups = [{"tag": t, "members": sorted(m), "holders": holds.get("grp." + t, [])} for t, m in members.items()]
    groups.sort(key=lambda g: (-(2 * len(g["holders"]) + len(g["members"])), g["tag"]))
    things = [(s, [str(x) for x in cfg.get("props") or []]) for s, cfg in scenes if cfg.get("props")]
    return {"people": ordered, "places": places, "groups": groups, "things": things}


def _cell(v):
    return " ".join(str(v).split()).replace("|", "\\|")


def _few(items):
    return "%d (%s)" % (len(items), ", ".join(items)) if items else "0"


def render(cat, slug):
    out = ["# Catalog — %s" % slug, "",
           "> GENERATED by `scripts/catalog.py` from the book's notes and scene files. **Non-authoritative**: the notes",
           "> are the record. Regenerate it; never edit it. Nothing in the engine reads this file.", "",
           "## People (%d)" % len(cat["people"]), "",
           "| Who | Level | Note | Scenes cast | Tied from | Linked from |", "|---|---|---|---|---|---|"]
    for r in cat["people"]:
        out.append("| %s | %s | %s | %s | %s | %d |" % (
            _cell(r["name"] or r["id"]), ", ".join(r["levels"]) or "-", "[[%s]]" % r["note"] if r["note"] else "-",
            _cell(_few(r["scenes"])), _cell(_few(r["ties"])), r["links"]))
    out += ["", "## Places (%d)" % len(cat["places"]), "", "| Place | What | Scenes set there | Held by |",
            "|---|---|---|---|"]
    for p in cat["places"]:
        out.append("| %s | %s | %s | %s |" % (_cell(p["id"]), _cell(p["what"]), _cell(_few(p["scenes"])),
                                              _cell(_few(p["holders"]))))
    out += ["", "## Groups (%d)" % len(cat["groups"]), "", "| Group | Members | Held by |", "|---|---|---|"]
    for g in cat["groups"]:
        out.append("| %s | %s | %s |" % (_cell(g["tag"]), _cell(_few(g["members"])), _cell(_few(g["holders"]))))
    out += ["", "## Things (a scene's props)", "", "| Scene | Things |", "|---|---|"]
    for s, props in cat["things"]:
        out.append("| %s | %s |" % (_cell(s), _cell("; ".join(props))))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--book", required=True, help="book slug under $SWE_BOOKS, or a path")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing the file")
    args = ap.parse_args(argv)
    try:
        book_dir = books.resolve(args.book)
    except books.BookError as e:
        raise SystemExit(str(e))
    text = render(build(book_dir), books.slug(book_dir))
    if args.stdout:
        sys.stdout.write(text)
        return 0
    dest_dir = os.path.join(book_dir, "runs")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, OUT)
    io.open(dest, "w", encoding="utf-8", newline="").write(text)
    print("wrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
