#!/usr/bin/env python3
"""test_bands.py — a band exists before anyone belongs to it (gate band-register, 2026-10-13).

The owner, 2026-10-13: "the world is so big it will be easy to forget what the world contains" - a tale saved for one
town, then a character from that town written as never having heard it. A fact needs a holder when it is saved, and
the holder was a group only once a cast member carried its tag (Fable review 3, M1). The owner's "Yes" reverses that:
a band is registered in the world on its own, and a fact can be held by it before anyone is placed in it.

Invented fixture: the river town of Saltmarsh, its folk, and the Lantern Guild nobody in the cast belongs to yet.
"""
import copy
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import attachments, knowledge, vault              # noqa: E402
from src.engine.records import RecordError                         # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[:600]) if (detail and not cond) else ""))


TALE = "The Saltmarsh folk say the drowned bell rings before a flood."
WICKS = "The Lantern Guild trims its wicks at dusk and not before."

WORLD = dict(copy.deepcopy(WORLD_ENGINE))
WORLD["locations"] = [{"id": "saltmarsh", "name": "Saltmarsh", "what": "a river town on stilts"},
                      {"id": "ferry", "what": "the ferry landing"}]
WORLD["people"] = [{"id": "odo", "what": "a ferryman"}]
WORLD["bands"] = [{"id": "lowland-folk", "kind": "people", "rule": "everyone raised in the lowlands",
                   "requires": {"nation": "the Lowlands"}}]
BAND_NOTE = {"bands": [
    {"id": "saltmarsh-folk", "kind": "place-folk", "parent": "lowland-folk", "nation": "the Lowlands",
     "rule": "everyone who grew up in Saltmarsh", "requires": {"place": "saltmarsh"}, "defines": ["Saltmarsh"]},
    {"id": "lantern-guild", "kind": "guild", "parent": "lowland-folk", "rule": "the sworn wick-trimmers of the guild"}]}


def _bad(band):
    """A world whose register holds one band -> the RecordError code bands.validate raises, or None."""
    w = dict(copy.deepcopy(WORLD), bands=WORLD["bands"] + [band])
    try:
        from src.engine import bands
        bands.validate_bands(w)
    except RecordError as e:
        return e.code
    except ImportError as e:
        return "IMPORT: %s" % e
    return None


def _book(tmp):
    book = os.path.join(tmp, "Saltmarsh Fixture")
    for sub in ("world", "characters", "bands", "knowledge"):
        os.makedirs(os.path.join(book, sub))
    world = dict(WORLD, knowledge=[{"claim": TALE, "held_by": ["grp.saltmarsh-folk"]}])
    with open(os.path.join(book, "world", "Saltmarsh.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\n---\n# Saltmarsh\n\n```json\n%s\n```\n" % json.dumps(world, indent=1))
    with open(os.path.join(book, "bands", "Lowland bands.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: bands\n---\n# Lowland bands\n\n```json\n%s\n```\n" % json.dumps(BAND_NOTE, indent=1))
    with open(os.path.join(book, "knowledge", "Guild.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: knowledge\n---\n```json\n%s\n```\n"
                 % json.dumps({"knowledge": [{"claim": WICKS, "held_by": ["grp.lantern-guild"]}]}))
    eng = copy.deepcopy(CHAR_ENGINE)
    eng["fixed"]["name"] = "Odo"
    eng["current"]["memberships"] = [{"of": "grp.saltmarsh-folk"}]
    with open(os.path.join(book, "characters", "Odo.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: character\n---\n# Odo\n\n```json\n%s\n```\n" % json.dumps(eng, indent=1))
    return book


def test_register():
    print("register")
    try:
        names = attachments.names_for(WORLD)
    except Exception as e:                              # noqa: BLE001 - a red test reports, never crashes
        names = [repr(e)]
    check("a band with no member is a registered name", "grp.lowland-folk" in names, names)
    w = dict(WORLD, knowledge=[{"claim": TALE, "held_by": ["grp.lowland-folk"]}])
    try:
        knowledge.validate_world(w)
        ok = True
    except RecordError as e:
        ok = e
    check("a fact held by a band nobody belongs to validates", ok is True, ok)
    check("the fixture register is clean", _bad({"id": "ferry-crews", "kind": "guild", "rule": "the crews"}) is None)
    for band, code in (({"id": "x", "kind": "tribe", "rule": "r"}, "BANDS_KIND_UNKNOWN"),
                       ({"id": "x", "kind": "guild", "rule": "  "}, "BANDS_RULE_EMPTY"),
                       ({"id": "x", "kind": "guild", "rule": "r", "parent": "nobody"}, "BANDS_PARENT_UNKNOWN"),
                       ({"id": "lowland-folk", "kind": "people", "rule": "r"}, "BANDS_ID_DUPLICATE"),
                       ({"id": "grp.x", "kind": "guild", "rule": "r"}, "BANDS_ID_INVALID"),
                       ({"id": "x", "kind": "guild", "rule": "r", "requires": {"trade": "smith"}}, "BANDS_REQUIRES_INVALID"),
                       ({"id": "x", "kind": "guild", "rule": "r", "requires": {"place": "nowhere"}}, "BANDS_REQUIRES_INVALID"),
                       ({"id": "x", "kind": "guild", "rule": "r", "defines": "Saltmarsh"}, "BANDS_DEFINES_INVALID"),
                       ("not a band", "BANDS_ENTRY_NOT_A_DICT")):
        got = _bad(band)
        check("refused by name: %s" % code, got == code, got)
    try:
        from src.engine import bands
        bands.validate_bands(dict(WORLD, bands={"a": 1}))
        got = None
    except RecordError as e:
        got = e.code
    except ImportError as e:
        got = repr(e)
    check("refused by name: BANDS_NOT_A_LIST", got == "BANDS_NOT_A_LIST", got)


def test_book():
    print("book")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        try:
            world, chars = vault.load_book(_book(tmp))
        except Exception as e:                          # noqa: BLE001
            check("the book loads its bands/ note", False, repr(e))
            return
        ids = [b.get("id") for b in world.get("bands") or []]
        check("the bands/ note merges after the world note's own", ids == ["lowland-folk", "saltmarsh-folk", "lantern-guild"], ids)
        try:
            knowledge.validate_world(world)
            ok = True
        except RecordError as e:
            ok = e
        check("the guild's fact, held by a band with no member, validates in the loaded book", ok is True, ok)
        vault_claims = [b.get("claim") for b in chars["odo"]["current"].get("vault") or []]
        check("a member placed in a band is linked to its fact", TALE in vault_claims, vault_claims)
        check("and not to a band he is not in", WICKS not in vault_claims, vault_claims)
        sys.path.insert(0, os.path.join(REPO, "scripts"))
        import lint_book
        findings = json.dumps(lint_book.lint(world, chars), default=str)
        check("lint reads every band field as declared", "bands" not in findings.lower()
              and "not declared" not in findings.lower(), findings[:600])


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    print("test_bands")
    test_register()
    test_book()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("  FAIL:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
