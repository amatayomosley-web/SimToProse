#!/usr/bin/env python3
"""test_contracts_world.py — the world note, declared once (gate world-contract, 2026-09-25).

THE CONTRACTS PLAN, G2 for the world (the owner's "Go"; agreed with Symphony on the board, convo #4). Before this gate
nothing checked the lexicon's shape, a person's groups or the laws at the pre-run check, and several silent traps sat
in the readers: a list written as text is scanned letter by letter, `blueprint_defaults: "false"` keeps the defaults
on, a law's `time_from` written as text raises uncaught mid-run, and a subtle-cue class naming no attribute class
matches nothing. src/engine/contracts_world.py declares every field; the laws, tensions and systems are handed to
their own modules.

  [1] the fixture world carries nothing undeclared and no error
  [2] the silent traps are reported, naming the path
  [3] the laws, tensions and systems are refused in their own modules' words - once each
  [4] what reaches nothing, and what a thin world goes without
  [5] the table is generated from the declarations; lint_book keeps its report

Script-style: check(), main(), exit code. Stdlib only. Every world here is the invented fixture.
"""
import copy
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import contracts, contracts_world, systems          # noqa: E402

FAILS = []
WORLD = json.load(open(os.path.join(REPO, "world", "ashford-slice.json"), encoding="utf-8"))
LAW = {"id": "no-theft", "statement": "Taking what is another's is punished.", "domain": "legal",
       "modality": "FORBIDS", "epistemic": "known-true", "act": "steal"}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def run(world):
    try:
        on = systems.for_book(world)
    except Exception:                                   # noqa: BLE001 - the contract reports why
        on = systems.defaults()
    return contracts.check(world, contracts_world.WORLD, on)


def at(findings, path, severity=None):
    return [f for f in findings if f["path"] == path and (severity is None or f["severity"] == severity)]


def clean():
    print("[1] the fixture world")
    got = run(WORLD)
    check("nothing-undeclared", not [f for f in got if f["severity"] == "unknown"], [f["path"] for f in got if f["severity"] == "unknown"])
    check("no-error", not [f for f in got if f["severity"] in ("error", "retired")], got)
    w = copy.deepcopy(WORLD)
    w["laws"] = [dict(LAW)]
    check("a-well-formed-law-passes", not [f for f in run(w) if f["severity"] == "error"], run(w))


def traps():
    print("[2] the silent traps")
    w = copy.deepcopy(WORLD)
    w["people"][0]["groups"] = "villagers"
    f = at(run(w), "people[].groups", "error")
    check("groups-written-as-text-(read-letter-by-letter)", f and "must be a list" in f[0]["message"], f)
    w = copy.deepcopy(WORLD)
    first = sorted(w["lexicon"]["attribute_classes"])[0]
    w["lexicon"]["attribute_classes"][first] = "fever chills sweat"
    f = at(run(w), "lexicon.attribute_classes.%s" % first, "error")
    check("an-attribute-class-written-as-text", f and "must be a list" in f[0]["message"], f)
    w = copy.deepcopy(WORLD)
    w["blueprint_defaults"] = "false"
    f = at(run(w), "blueprint_defaults", "error")
    check("a-text-false-that-keeps-the-defaults-on", f and "must be true or false" in f[0]["message"], f)
    w = copy.deepcopy(WORLD)
    w["laws"] = [dict(LAW, time_from="dawn")]
    f = at(run(w), "laws[].time_from", "error")
    check("a-law's-time-written-as-text-(raised-mid-run)", f and "must be a number" in f[0]["message"], f)
    w = copy.deepcopy(WORLD)
    w["lexicon"]["subtle_cue_classes"] = ["no_such_class"]
    f = at(run(w), "lexicon.subtle_cue_classes", "advice")
    check("a-subtle-cue-class-naming-no-attribute-class", f and "no_such_class" in f[0]["message"], f)
    w = copy.deepcopy(WORLD)
    w["laws"] = [dict(LAW, time_from=None)]
    check("a-null-is-not-authored,-not-a-wrong-type", not at(run(w), "laws[].time_from"), run(w))


def modules():
    print("[3] the modules that own a block refuse in their own words, once")
    w = copy.deepcopy(WORLD)
    w["laws"] = [dict(LAW, modality="SOMETIMES")]
    got = run(w)
    f = at(got, "laws[]", "error")
    check("a-law-the-law-module-refuses", f and "BIBLE_LAW_MODALITY" in f[0]["message"], f)
    check("...reported-once-(not-again-by-the-list)", not at(got, "laws", "error"), at(got, "laws"))
    w = copy.deepcopy(WORLD)
    w["laws"] = [dict(LAW), dict(LAW)]
    f = at(run(w), "laws", "error")
    check("two-laws-with-one-id-(the-list-as-a-whole)", f and "BIBLE_LAW_ID_DUPLICATE" in f[0]["message"], f)
    w = copy.deepcopy(WORLD)
    w["systems"] = {"magic": False}
    f = at(run(w), "systems", "error")
    check("a-system-the-registry-does-not-know", f and "SYSTEMS_UNKNOWN" in f[0]["message"], f)
    w = copy.deepcopy(WORLD)
    w["tensions"] = [{"id": "t1"}]
    f = at(run(w), "tensions", "error")
    check("a-tension-the-tension-module-refuses", f and "[" in f[0]["message"], f)


def thin():
    print("[4] what reaches nothing, and what a thin world goes without")
    w = copy.deepcopy(WORLD)
    got = run(w)
    check("season-reaches-nothing", at(got, "season", "unread"), [f for f in got if f["severity"] == "unread"])
    f = at(got, "laws", "advice")
    check("no-laws:-the-defaults-still-apply-(the-old-warning-said-none-did)", f and "default laws apply" in f[0]["message"], f)
    w["people"] = []
    w.pop("lexicon")
    got = run(w)
    check("an-empty-people-list-is-advised", at(got, "people", "advice"))
    check("no-lexicon-is-advised", at(got, "lexicon", "advice"))
    w = copy.deepcopy(WORLD)
    w["people"].append({"what": "a stranger with no id"})
    check("a-person-with-no-id-is-advised", at(run(w), "people[]", "advice"))
    w = copy.deepcopy(WORLD)
    w["lexicn"] = {}
    f = at(run(w), "lexicn", "unknown")
    check("an-undeclared-key-with-a-did-you-mean", f and "did you mean 'lexicon'" in f[0]["message"], f)


def table_and_report():
    print("[5] the table and the report")
    paths = [f.path for f in contracts_world.WORLD]
    check("every-path-declared-once", len(paths) == len(set(paths)))
    check("every-kind-and-status-known", all(f.kind in contracts.KINDS and f.status in contracts.STATUSES
                                             for f in contracts_world.WORLD))
    r = subprocess.run([sys.executable, os.path.join("scripts", "gen_contracts.py"), "--check"], cwd=REPO,
                       capture_output=True, text=True)
    check("the-blueprint's-table-matches-the-declarations", r.returncode == 0, r.stdout + r.stderr)
    import lint_book
    maren = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    rep = lint_book.lint(WORLD, {"maren": maren})
    check("lint_book-keeps-its-shape-and-the-fixture-is-error-free", set(rep) == {"errors", "warnings"} and rep["errors"] == [],
          rep["errors"])
    w = copy.deepcopy(WORLD)
    w["systems"] = {"magic": False}
    rep = lint_book.lint(w, {"maren": maren})
    check("a-world-finding-reads-world.<path>:", any(e.startswith("world.systems:") and "SYSTEMS_UNKNOWN" in e for e in rep["errors"]),
          rep["errors"])


def main():
    clean()
    traps()
    modules()
    thin()
    table_and_report()
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
