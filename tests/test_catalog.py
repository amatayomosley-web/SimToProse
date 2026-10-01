"""test_catalog.py — a book's people, places, groups and things, by level and by use (scripts/catalog.py).

Builds a small invented book in a temp folder (nothing from any book: hard rule 1) and pins what the catalog says
about it: the three levels and their order, the use counts, what is left out of the counts (a backup under
staging/, the catalog itself), where it is written, that a second run writes the same bytes, and that the
engine's loader sees the same book before and after. Script-style: check(), main(), exit 0 = all pass. Stdlib only.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import catalog                                                    # noqa: E402
from src.engine import vault                                      # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  - %s" % (detail,)))
    if not ok:
        FAIL.append(name)


def _note(path, front, body="", engine=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = "---\n%s\n---\n%s\n" % (front, body)
    if engine is not None:
        text += "\n```json\n%s\n```\n" % json.dumps(engine)
    io.open(path, "w", encoding="utf-8").write(text)


def _book():
    d = tempfile.mkdtemp(prefix="catalog_")
    _note(os.path.join(d, "world", "Shore.md"), "type: world\nid: shore", "# Shore", {
        "people": [{"id": "tam", "name": "Tam", "what": "the miller", "groups": ["millers"]},
                   {"id": "orla", "name": "Orla", "what": "the dyer"}],
        "locations": [{"id": "mill", "what": "the mill"}, {"id": "fold", "what": "the fold | up the fell"}]})
    _note(os.path.join(d, "characters", "Tam.md"), "type: character\nid: tam", "# Tam", {
        "fixed": {"id": "tam", "name": "Tam"}, "baseline": {},
        "current": {"relationships": {"orla": {"trust": 0.5}},
                    "attachments": {"loc.mill": {"hold": 0.8, "sign": "+"}, "grp.millers": {"hold": 0.5, "sign": "+"}}}})
    _note(os.path.join(d, "characters", "Nell.md"), "type: character\nid: nell", "# Nell", {
        "fixed": {"id": "nell", "name": "Nell"}, "baseline": {},
        "current": {"relationships": {"tam": {"trust": 0.6}}}})
    _note(os.path.join(d, "people", "Bryony.md"), "type: reference\nid: bryony\naliases: [Old Bryony]",
          "# Bryony Teal — the shepherd\n\n[[Bryony]] keeps the fold.")       # a note naming itself is not a link in
    _note(os.path.join(d, "chapters", "Ch1.md"), "type: outline", "[[Bryony]] and [[Tam|the miller]] talk.")
    for n in range(2, 5):                       # Bryony is the most-linked person, so only her LEVEL keeps her last
        _note(os.path.join(d, "chapters", "Ch%d.md" % n), "type: outline", "[[Bryony]] walks the fell.")
    _note(os.path.join(d, "chapters", "Ch5.md"), "type: outline",          # a link in a table escapes its pipe
          "| who | where |\n|---|---|\n| [[Bryony" + chr(92) + "|Old Bryony]] | the fell |")
    _note(os.path.join(d, "staging", "old", "Ch1.md"), "type: outline", "[[Bryony]] again.")
    os.makedirs(os.path.join(d, "scenes"))
    io.open(os.path.join(d, "scenes", "scene_01_cfg.json"), "w", encoding="utf-8").write(json.dumps(
        {"name": "scene_01", "cast": [{"id": "tam"}, {"id": "nell"}], "location": "mill",
         "props": ["a sack of grain"]}))
    return d


def test_levels_and_order(d):
    print("\n[1] LEVELS AND ORDER - played, then seeable, then reference; then by use")
    cat = catalog.build(d)
    rows = {r["id"]: r for r in cat["people"]}
    check("tam is played and seeable", rows["tam"]["levels"] == ["played", "seeable"], rows["tam"]["levels"])
    check("nell is played and NOT seeable (a sheet is not an entity)", rows["nell"]["levels"] == ["played"],
          rows["nell"]["levels"])
    check("orla is seeable only", rows["orla"]["levels"] == ["seeable"], rows["orla"]["levels"])
    check("bryony's reference note is listed, at the reference level",
          rows.get("bryony", {}).get("levels") == ["reference"], rows.get("bryony"))
    check("order: played (by use), then seeable, then reference",
          [r["id"] for r in cat["people"]] == ["tam", "nell", "orla", "bryony"], [r["id"] for r in cat["people"]])
    check("the reference note's title is its name", rows["bryony"]["name"] == "Bryony Teal", rows["bryony"]["name"])


def test_use(d):
    print("\n[2] USE - scenes cast, sheets tied, notes linking; staging/ and the catalog itself never count")
    rows = {r["id"]: r for r in catalog.build(d)["people"]}
    check("tam: cast in one scene", rows["tam"]["scenes"] == ["scene_01"], rows["tam"]["scenes"])
    check("tam: one sheet tied to him (nell)", rows["tam"]["ties"] == ["nell"], rows["tam"]["ties"])
    check("orla: tied from tam's sheet", rows["orla"]["ties"] == ["tam"], rows["orla"]["ties"])
    check("bryony: five notes link to her - the backup under staging/ does not count", rows["bryony"]["links"] == 5,
          rows["bryony"]["links"])
    check("tam: an aliased link [[Tam|the miller]] still counts", rows["tam"]["links"] == 1, rows["tam"]["links"])
    catalog.main(["--book", d])
    check("after a catalog is written, the counts do not include it",
          {r["id"]: r["links"] for r in catalog.build(d)["people"]}["bryony"] == 5)


def test_places_groups_things(d):
    print("\n[3] PLACES, GROUPS, THINGS")
    cat = catalog.build(d)
    places = {p["id"]: p for p in cat["places"]}
    check("the mill: one scene set there, held by tam", places["mill"]["scenes"] == ["scene_01"]
          and places["mill"]["holders"] == ["tam"], places["mill"])
    check("places ranked by use (mill before fold)", [p["id"] for p in cat["places"]] == ["mill", "fold"])
    check("the millers: tam a member and a holder", cat["groups"] == [
        {"tag": "millers", "members": ["tam"], "holders": ["tam"]}], cat["groups"])
    check("things are the scene's props", cat["things"] == [("scene_01", ["a sack of grain"])], cat["things"])
    text = catalog.render(cat, "shore")
    check("a pipe inside a table cell is escaped", "the fold \\| up the fell" in text, text[-600:])
    check("the table links each person to their note", "[[Bryony]]" in text and "[[Tam]]" in text)


def test_writing(d):
    print("\n[4] WRITING - into runs/, the same bytes twice, nothing the loader reads changes")
    before = vault.load_book(d)
    for f in ("catalog.md",):
        p = os.path.join(d, "runs", f)
        if os.path.exists(p):
            os.remove(p)                          # the temp book's own output from [2]; nothing else is touched
    catalog.main(["--book", d])
    p = os.path.join(d, "runs", "catalog.md")
    first = io.open(p, encoding="utf-8").read() if os.path.isfile(p) else None
    check("written to <book>/runs/catalog.md", first is not None)
    catalog.main(["--book", d])
    check("a second run writes the same bytes", io.open(p, encoding="utf-8").read() == first)
    check("the loader sees the same book before and after", vault.load_book(d) == before)
    out = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "catalog.py"), "--book", d, "--stdout"],
                         capture_output=True, text=True, encoding="utf-8")
    check("--stdout prints the catalog", out.returncode == 0 and out.stdout.startswith("# Catalog"), out.stderr[-300:])
    check("it never writes into world/, characters/ or people/",
          not any(f == "catalog.md" for sub in ("world", "characters", "people")
                  for f in os.listdir(os.path.join(d, sub))))


def main():
    print("test_catalog.py - a book's people, places, groups and things, by level and by use\n")
    d = _book()
    try:
        for t in (test_levels_and_order, test_use, test_places_groups_things, test_writing):
            t(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("\n%s" % ("test_catalog: OK" if not FAIL else "FAILED: %s" % FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
