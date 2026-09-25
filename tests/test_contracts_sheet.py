#!/usr/bin/env python3
"""test_contracts_sheet.py — the character sheet, declared once (gate sheet-contract, 2026-09-25).

THE CONTRACTS PLAN, G2 (the owner's "Go"; agreed with Symphony on the board, convo #4): every field of a sheet is
declared in src/engine/contracts_sheet.py - its shape, whether a book must author it, and whether anything reads it -
and `contracts.check` walks a sheet against the declarations. Measured on the owner's four books before this gate:
the linter reported every `_note` in a number table as "not a number" (19 of 57 errors), the blueprint marked
drives.orientation required while nothing reads it, an absent baseline.skills was a warning while both drivers crash
on it, and `fixed.position` carried its notes into the prompt.

  [1] the fixtures carry nothing undeclared, and nothing that is not reported as what it is
  [2] an annotation (`_...` or `note`) is ignored everywhere - the 19 false errors
  [3] an undeclared key is reported, with a did-you-mean (under a placeholder parent too)
  [4] a retired key names its successor and its policy
  [5] an unread key is reported as reaching nothing
  [6] a wrong shape, range or word is an error naming the path
  [7] what a book must author, per the systems it runs
  [8] a block an engine module owns is refused in that module's own words
  [9] the declarations are well-formed, and the blueprint's table is generated from them
  [10] `fixed.position` keeps no annotation in the prompt; lint_book's report keeps its shape

Script-style: check(), main(), exit code. Stdlib only. Every sheet here is an invented fixture.
"""
import copy
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import contracts, contracts_sheet, heritable, systems  # noqa: E402
from src.engine.records import PATHS, RETIRED_PRIMITIVES           # noqa: E402

FAILS = []
SHEET = contracts_sheet.SHEET
MAREN = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
REN = json.load(open(os.path.join(REPO, "characters", "ren-traveler.json"), encoding="utf-8"))
WORLD = json.load(open(os.path.join(REPO, "world", "ashford-slice.json"), encoding="utf-8"))


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def run(sheet, on=None, ctx=None):
    from src.engine import attachments
    return contracts.check(sheet, SHEET, systems.defaults() if on is None else on,
                           ctx if ctx is not None else {"registered": attachments.names_for(WORLD)})


def at(findings, path, severity=None):
    return [f for f in findings if f["path"] == path and (severity is None or f["severity"] == severity)]


def fixtures():
    print("[1] the fixtures")
    for name, ch in (("maren", MAREN), ("ren", REN)):
        got = run(ch)
        check("%s-carries-nothing-undeclared" % name, not [f for f in got if f["severity"] == "unknown"],
              [f["path"] for f in got if f["severity"] == "unknown"])
        check("%s-has-no-error" % name, not [f for f in got if f["severity"] in ("error", "retired")],
              [(f["path"], f["message"]) for f in got if f["severity"] in ("error", "retired")])


def annotations():
    print("[2] annotations are ignored everywhere")
    ch = copy.deepcopy(MAREN)
    ch["baseline"]["skills"]["_note"] = "perception is the point of her"
    ch["baseline"]["model"]["schwartz"]["_note"] = "benevolence first"
    ch["baseline"]["traits"]["emotionality"]["note"] = "the house taught her"
    ch["baseline"]["temperament"]["WARINESS"]["_note"] = "she startles"
    ch["current"]["relationships"]["edda_elder"]["_why"] = "the lean years"
    ch["_meta"] = {"author": "a note about the file"}
    got = run(ch)
    hits = [f for f in got if "_note" in f["path"] or "_why" in f["path"] or "_meta" in f["path"] or f["path"].endswith(".note")]
    check("no-finding-touches-an-annotation", not hits, hits)
    check("(the-number-tables-still-check-their-numbers)", at(run(dict(ch, baseline=dict(ch["baseline"], skills=dict(
        ch["baseline"]["skills"], perception="sharp-eyed")))), "baseline.skills.perception", "error"))


def unknown():
    print("[3] an undeclared key is reported, with a did-you-mean")
    ch = copy.deepcopy(MAREN)
    ch["baseline"]["skils"] = {"perception": 0.5}
    ch["current"]["relationships"]["edda_elder"]["trsut"] = 0.4
    got = run(ch)
    f = at(got, "baseline.skils", "unknown")
    check("a-misspelt-section-key", f and "did you mean 'skills'" in f[0]["message"], f)
    f = at(got, "current.relationships.edda_elder.trsut", "unknown")
    check("...under-a-placeholder-parent-too", f and "did you mean 'trust'" in f[0]["message"], f)


def retired():
    print("[4] a retired key names its successor and its policy")
    ch = copy.deepcopy(MAREN)
    ch["current"]["affect"]["CARE"] = 0.4
    ch["baseline"]["temperament"]["RAGE"] = {"mean": 0.2, "variability": 0.1}
    old_axis = heritable.OLD_AXES[0]                       # named from the engine, never spelt here
    ch["fixed"]["genotype"][old_axis] = "high"
    ch["fixed"]["genotype"]["WARINESS"]["rest"] = "raised"
    ch["baseline"]["drives"]["fears_wounds"] = [{"wound": "w"}]
    got = run(ch)
    f = at(got, "current.affect.CARE", "retired")
    check("an-old-primitive-names-its-path", f and "GOODWILL" in f[0]["message"] and "refuse" in f[0]["message"], f)
    f = at(got, "baseline.temperament.RAGE", "retired")
    check("...in-the-temperament-too", f and "DISPLEASURE" in f[0]["message"], f)
    check("(every-successor-is-a-built-path)", set(RETIRED_PRIMITIVES.values()) <= set(PATHS))
    check("an-old-genotype-axis", at(got, "fixed.genotype." + old_axis, "retired"))
    f = at(got, "fixed.genotype.WARINESS.rest", "retired")
    check("a-rest-in-the-genotype-names-where-it-goes", f and "baseline.temperament.WARINESS.rest" in f[0]["message"]
          and "move" in f[0]["message"], f)
    f = at(got, "baseline.drives.fears_wounds", "retired")
    check("fears_wounds-moves-to-the-wounds", f and "baseline.wounds" in f[0]["message"] and "move" in f[0]["message"], f)
    check("nothing-inside-a-retired-field-is-reported", not [x for x in got if x["path"].startswith("baseline.temperament.RAGE.")
                                                             or x["path"].startswith("baseline.drives.fears_wounds[")])


def unread():
    print("[5] an unread key reaches nothing")
    ch = copy.deepcopy(MAREN)
    got = run(ch)
    for path in ("baseline.drives.orientation", "fixed.role_tier", "current.zone"):
        check("%s-is-unread" % path, at(got, path, "unread"), [f["path"] for f in got if f["severity"] == "unread"])
    check("(unread-is-a-warning-not-an-error)", not [f for f in got if f["severity"] == "unread" and f["code"] != "CONTRACT_FIELD_UNREAD"])


def shapes():
    print("[6] a wrong shape, range or word is an error naming the path")
    cases = (("current.affect", "WARINESS", 1.7, "must be a number in [0,1]"),
             ("current.condition", "energy", True, "must be a number in [0,1]"),
             ("fixed.genotype.WARINESS", "hit", "very high", "must lead with one of low|typical|elevated|high"),
             ("baseline.temperament.WARINESS", "rest", "very high", "must lead with one of quiet|low|raised|high"),
             ("fixed.position", "place", 7, "reaches the actor verbatim"),
             ("current.relationships.edda_elder", "trust", "I would not turn my back", "must be a number in [0,1]"))
    for parent, key, value, want in cases:
        ch = copy.deepcopy(MAREN)
        node = ch
        for k in parent.split("."):
            node = node.setdefault(k, {})
        node[key] = value
        f = at(run(ch), parent + "." + key, "error")
        check("%s.%s=%r" % (parent, key, value), f and want in f[0]["message"], f or run(ch)[:3])
    ch = copy.deepcopy(MAREN)
    ch["fixed"]["genotype"]["WARINESS"] = {"hit": 1.8, "hold": "long (she keeps it)"}
    check("a-number-in-a-genotype-cell-is-honoured-and-a-word-leads", not [f for f in run(ch)
                                                                          if f["path"].startswith("fixed.genotype.WARINESS")])


def required():
    print("[7] what a book must author, per the systems it runs")
    ch = copy.deepcopy(MAREN)
    del ch["baseline"]["skills"]
    check("skills-always-(the-drivers-index-it)", at(run(ch), "baseline.skills", "error"))
    ch = copy.deepcopy(MAREN)
    del ch["current"]["affect"]["LEVITY"]
    check("every-path-in-the-mood", at(run(ch), "current.affect.LEVITY", "error"))
    ch = copy.deepcopy(MAREN)
    del ch["current"]["condition"]
    check("condition-while-the-book-runs-it", at(run(ch), "current.condition", "error"))
    check("...not-when-it-does-not", not at(run(ch, on=systems.for_book({"systems": {"condition": False}})), "current.condition"))
    ch = copy.deepcopy(MAREN)
    del ch["current"]["condition"]["allostatic_load"]
    flow = systems.for_book({"systems": {"condition_flow": True}})
    check("both-keys-when-the-flow-runs", at(run(ch, on=flow), "current.condition.allostatic_load", "error"))
    f = at(run(ch), "current.condition", "advice")
    check("...one-of-them-otherwise-is-advice", f and "only one of energy / allostatic_load" in f[0]["message"], f)
    body = systems.for_book({"systems": {"condition_flow": True, "body": True}})
    f = at(run(copy.deepcopy(MAREN), on=body), "baseline.body", "error")
    check("strength-when-the-book-runs-the-body,-in-the-body-module's-words",
          f and "BODY_STRENGTH_MISSING" in f[0]["message"] and "body system" in f[0]["message"], f)


def delegated():
    print("[8] a block an engine module owns is refused in its own words")
    ch = copy.deepcopy(REN)
    ch["baseline"]["wounds"] = [{"id": "zebra@WARINESS", "concept": "zebra", "path": "WARINESS", "intensity": 0.5, "source": "profile:t"}]
    f = at(run(ch), "baseline.wounds[]", "error")
    check("a-wound-the-wound-module-refuses", f and "WOUND_CONCEPT_UNKNOWN" in f[0]["message"], f)
    scar = next(w for w in REN["baseline"]["wounds"] if isinstance(w, dict) and w.get("id"))
    ch["baseline"]["wounds"] = [dict(scar, source="hand-written")]
    f = at(run(ch), "baseline.wounds[]", "error")
    check("a-wound-not-minted", f and "CONTRACT_WOUND_SOURCE" in f[0]["message"], f)
    ch = copy.deepcopy(REN)
    ch["baseline"]["catalog"]["rows"].append({"wound": "ghost@WARINESS", "when": {"percept": ["x"]}, "lever": "WARINESS",
                                              "op": "x", "magnitude": 2.0, "source": "t"})
    f = at(run(ch), "baseline.catalog", "error")
    check("a-row-naming-a-wound-the-sheet-lacks", f and "CONTRACT_CATALOG_WOUND_UNKNOWN" in f[0]["message"], f)
    ch = copy.deepcopy(MAREN)
    ch["current"]["attachments"]["loc.tower"] = {"hold": .5, "sign": "+"}
    f = at(run(ch), "current.attachments", "error")
    check("an-unregistered-attachment", f and "ATTACH_ENTITY_UNREGISTERED" in f[0]["message"], f)
    ch = copy.deepcopy(REN)
    ch["baseline"]["relationship_priors"]["update"]["withdraw_speed"] = "slowly, over a season"
    check("a-prose-rate-word", at(run(ch), "baseline.relationship_priors.update", "error"))


def declarations():
    print("[9] the declarations are well-formed; the table is generated from them")
    paths = [f.path for f in SHEET]
    check("every-path-declared-once", len(paths) == len(set(paths)), sorted(p for p in paths if paths.count(p) > 1))
    check("every-kind-and-status-known", all(f.kind in contracts.KINDS and f.status in contracts.STATUSES for f in SHEET))
    check("a-retired-field-names-its-successor-and-policy",
          all(f.replaced_by and f.policy in ("prune", "move", "refuse") for f in SHEET if f.status == "retired"))
    check("an-unread-field-names-no-reader", all(not f.reader for f in SHEET if f.status == "unread"))
    words = [f for f in SHEET if f.kind.startswith("word")]
    check("every-vocabulary-resolves", all(len(tuple(contracts._vocab(f.vocab))) > 1 for f in words), [f.vocab for f in words])
    check("every-placeholder-resolves", all(contracts._placeholder(p) for p in contracts.PLACEHOLDERS))
    r = subprocess.run([sys.executable, os.path.join("scripts", "gen_contracts.py"), "--check"], cwd=REPO,
                       capture_output=True, text=True)
    check("the-blueprint's-table-matches-the-declarations", r.returncode == 0, r.stdout + r.stderr)


def prompt_and_report():
    print("[10] the prompt and the report")
    from src.engine.scene import assemble
    ch = copy.deepcopy(MAREN)
    ch["fixed"]["position"]["_note"] = "a design note about her class"
    ch["fixed"]["position"]["note"] = "another"
    pos = assemble(ch, WORLD, {"event": {"text": "A quiet morning."}}, {p: 0.2 for p in PATHS},
                   ch["current"]["condition"])["stable"]["persona"]["position"]
    check("no-annotation-in-the-persona", "_note" not in pos and "note" not in pos and "place" in pos, pos)
    import lint_book
    rep = lint_book.lint(WORLD, {"maren": MAREN})
    check("lint_book-keeps-its-shape", set(rep) == {"errors", "warnings"} and rep["errors"] == [], rep["errors"])
    old = copy.deepcopy(MAREN)
    for p in PATHS[1:]:
        old["current"]["affect"].pop(p, None)
    lines = [e for e in lint_book.lint(WORLD, {"maren": old})["errors"] if "current.affect" in e]
    check("eight-missing-paths-are-one-line", len(lines) == 1 and all(p in lines[0] for p in PATHS[1:]), lines)
    old["current"]["affect"] = {}
    lines = [e for e in lint_book.lint(WORLD, {"maren": old})["errors"] if "current.affect" in e]
    check("an-empty-mood-is-one-finding,-not-ten", len(lines) == 1 and "current.affect is required" in lines[0], lines)


def main():
    fixtures()
    annotations()
    unknown()
    retired()
    unread()
    shapes()
    required()
    delegated()
    declarations()
    prompt_and_report()
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
