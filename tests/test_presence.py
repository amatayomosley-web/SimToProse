#!/usr/bin/env python3
"""test_presence.py — pinning src/engine/presence.py: being NAMED is not being IN THE ROOM.

No suite existed for this module before gate `attachments-to-actor` (scene.py already called
presence.build_edges/edge_from_rel; nothing had ever pinned what they do). This suite does not
touch presence.py — it PINS what match, referenced_ids, display_name, named_in, present_unnamed,
build_edges and edge_from_rel do TODAY, so the module's own defect-history (a cast list keyed in
the wrong id space, a referenced-not-present party wrongly seated, an absent axis silently written
as None) stays caught by something.

Script-style (like tests/test_scene.py, tests/test_attachments.py): plain check(), main(), exit
code 0 = all pass. Stdlib only. No pytest. Invented ids throughout (edda, joss, ren, mill/chapel
analogues) — nothing from any book (hard rule 1).
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import presence as P                              # noqa: E402
from src.engine.records import RecordError                        # noqa: E402

PASS = []
FAIL = []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print("  PASS  %s" % name)
    else:
        FAIL.append(name)
        msg = "  FAIL  %s" % name
        if detail:
            msg += "  - " + str(detail)       # a list or tuple as detail used to crash the run at the first failure
        print(msg)


def _raises(code, fn):
    try:
        fn()
        return False
    except RecordError as e:
        return e.code == code


def test_match():
    print("\n[1] MATCH - the full id or its first underscore-part, never raw-string containment")
    check("full id present", P.match("edda_elder", {"edda_elder"}))
    check("head-of-id present (cast lists use the short id)", P.match("edda_elder", {"edda"}))
    check("neither present", not P.match("edda_elder", {"joss"}))
    check("an id with no underscore still matches on itself", P.match("solo", {"solo"}))
    check("empty present_set never matches", not P.match("edda_elder", set()))


def test_referenced_ids():
    print("\n[2] REFERENCED_IDS - named this turn, NOT standing with you")
    percepts = [
        {"ref": "entity.ren_traveler", "present": False},
        {"ref": "entity.edda_elder", "present": True},
        {"ref": "loc.cottage", "present": False},
        {"ref": "entity.ren_traveler", "present": False},   # duplicate, deduped
    ]
    check("only present:false entity. refs, deduped and sorted",
          P.referenced_ids(percepts) == ["ren_traveler"], P.referenced_ids(percepts))
    check("empty for no percepts", P.referenced_ids([]) == [])
    check("a non-list refuses", _raises("GATE_PERCEPTS_NOT_A_LIST", lambda: P.referenced_ids("bad")))


def test_display_name():
    print("\n[3] DISPLAY_NAME - the id, capitalised words, never the engine form")
    check("first_last -> First Last", P.display_name("edda_elder") == "Edda Elder")
    check("solo -> Solo", P.display_name("solo") == "Solo")
    check("empty id -> empty", P.display_name("") == "")


def test_named_in():
    print("\n[4] NAMED_IN - who the TEXT names, from world.people, identity only")
    world = {"people": [{"id": "edda_elder", "what": "the village elder"},
                        {"id": "ren_traveler", "what": "an outsider"}]}
    normalize = lambda s: s.lower()
    hits = P.named_in("Edda spoke to no one in particular.", world, normalize)
    check("edda is named with her observable role",
          hits == [("edda_elder", "Edda", ["the village elder"])], hits)
    check("a name absent from the text is not returned",
          P.named_in("Nothing happens.", world, normalize) == [])
    check("a person with no `what` falls back to the (lowercase) first name as the observable",
          P.named_in("Ren left.", {"people": [{"id": "ren_traveler"}]}, normalize) ==
          [("ren_traveler", "Ren", ["ren"])])


def test_present_unnamed():
    print("\n[5] PRESENT_UNNAMED - bodily here, the text just never said so")
    world = {"people": [{"id": "edda_elder", "what": "the village elder"},
                        {"id": "joss_apprentice", "what": "the apprentice"}]}
    out = P.present_unnamed({"edda_elder", "joss_apprentice"}, ["joss_apprentice"], world, me="maren_healer")
    check("the unnamed present person is returned, the named one is not",
          out == [("edda_elder", "Edda", ["the village elder"])], out)
    check("empty present_set -> []", P.present_unnamed(set(), [], world) == [])
    check("the perceiver is never a percept of themself",
          P.present_unnamed({"maren_healer"}, [], world, me="maren_healer") == [])


def test_build_edges():
    print("\n[6] BUILD_EDGES - a present entity WITH a relationship gets an edge; referenced-not-present does not")
    current = {"relationships": {
        "edda_elder":   {"trust": 0.6, "affinity": 0.5, "respect": 0.7, "debt": 0.0},
        "ren_traveler": {"trust": 0.3, "affinity": 0.4, "respect": 0.4, "debt": 0.0},
    }}
    percepts = [
        {"ref": "entity.edda_elder", "present": True},
        {"ref": "entity.ren_traveler", "present": False},   # referenced, not present
    ]
    edges = P.build_edges(current, percepts, {})
    check("exactly the present party gets an edge",
          [e["target"] for e in edges] == ["edda_elder"], edges)
    check("the referenced-not-present party gets none",
          all(e["target"] != "ren_traveler" for e in edges))
    check("a party with no relationship row gets no edge",
          P.build_edges({"relationships": {}}, [{"ref": "entity.nobody", "present": True}], {}) == [])
    check("order is sorted, not hash order (hard rule 4)",
          [e["target"] for e in P.build_edges(
              {"relationships": {k: {"trust": .5} for k in ("zeta", "alpha", "mid")}},
              [{"ref": "entity." + k, "present": True} for k in ("zeta", "alpha", "mid")], {})]
          == ["alpha", "mid", "zeta"])


def test_edge_from_rel():
    print("\n[7] EDGE_FROM_REL - one relationship row -> one edge; an absent axis is OMITTED, never None")
    edge = P.edge_from_rel("edda_elder", {"trust": 0.6, "affinity": 0.5, "history": "old friends"})
    check("target/label/history carry through",
          edge["target"] == "edda_elder" and edge["history"] == "old friends", edge)
    check("no known_as falls back to display_name", edge["label"] == "Edda Elder", edge["label"])
    check("known_as overrides the display name",
          P.edge_from_rel("edda_elder", {"known_as": "the elder"})["label"] == "the elder")
    check("a present axis carries its value", edge["trust"] == 0.6 and edge["affinity"] == 0.5)
    check("an absent axis is OMITTED, never set to None",
          "respect" not in edge and "debt" not in edge, edge)
    check("their_view carries through when present",
          P.edge_from_rel("x", {"their_view": {"affinity": 0.8}})["their_view"] == {"affinity": 0.8})


def test_names_one_rule():
    print("\n[8] NAMES_OF + MENTIONS - one list of names, matched as whole words, read by every name path")
    from src.engine import acquisition, contracts, contracts_world, facets
    from src.engine.gate import _normalize
    ned = {"id": "ned", "what": "the carter"}
    tobit = {"id": "tobit_wendle", "name": "Tobit Wendle", "what": "the reeve"}
    corby = {"id": "corby_bisset", "name": "Corby Bisset", "what": "the tallyman", "aliases": ["Corbs", "Big Corby"]}
    fran = {"id": "fran", "name": "Fran", "what": "the weaver"}
    world = {"people": [ned, tobit, corby, fran]}
    named = lambda text: [h[0] for h in P.named_in(text, world, _normalize)]
    # a name inside a longer word names no one: measured on a live run, 2026-10-01, a short id inside an ordinary word
    # put a person who was not in the scene into four beats' percepts
    check("a name inside a longer word is not a mention ('turned' does not name ned)", named("She turned away.") == [])
    check("nor 'Tobitha' tobit", named("Tobitha came in.") == [])
    check("nor a phrase that runs into a longer word ('a big corbyn')", named("A big corbyn sat.") == [])
    check("nor a name before a letter outside a-z ('François')", named("François came in.") == [])
    check("the possessive still names ('Ned's')", named("Ned's cart was empty.") == ["ned"])
    check("a whole name names, across any run of spaces", named("Corby   Bisset came late.") == ["corby_bisset"])
    check("an alias names", named("Corbs counted coins.") == ["corby_bisset"])
    check("a word of `name` alone names no one unless it is an alias (a shared surname would name a family)",
          named("Wendle signed the tally.") == [])
    check("a post nobody declared names no one", named("The reeve's clerk counted coins.") == [])
    check("names_of: the id's first word, the id as words, the whole name, then the aliases, deduped, in order",
          P.names_of({"id": "tam_rill", "name": "Tam Rill", "aliases": ["Rill", "Tam", "Tammy"]})
          == ["tam", "tam rill", "Rill", "Tammy"],
          P.names_of({"id": "tam_rill", "name": "Tam Rill", "aliases": ["Rill", "Tam", "Tammy"]}))
    check("names_of reads only a LIST of aliases (a string is the contract's to refuse, not letters to match)",
          P.names_of({"id": "ned", "aliases": "Neddy"}) == ["ned"])
    check("belief-stamping reads the same list (an alias stamps)",
          facets.entities_in("Corbs counted coins.", world) == ["corby_bisset"])
    check("belief-stamping: a name inside a longer word stamps no one",
          facets.entities_in("She turned away.", world) == [])
    rels = {"tobit_wendle": {"known_as": "the reeve"}, "corby_bisset": {"known_as": "the tallyman"},
            "ned": {"known_as": "the carter"}}
    quill = {"id": "odile_quill", "name": "Odile Quill", "what": "x", "aliases": ["Quill", "Old"]}
    people = [dict(ned, name="Ned"), tobit, corby, quill, {"id": "tansy_old", "name": "Tansy", "what": "x", "aliases": ["the tallyman"]}]
    check("hearing the whole name teaches the spoken word",
          acquisition.overheard_names("Tobit Wendle signed it.", rels, people) == [("tobit_wendle", "Tobit")],
          acquisition.overheard_names("Tobit Wendle signed it.", rels, people))
    check("a surname that is no alias is not heard", acquisition.overheard_names("Wendle signed it.", rels, people) == [])
    check("an alias holding the id's first word teaches the spoken word",
          acquisition.overheard_names("Big Corby counted.", rels, people) == [("corby_bisset", "Corby")])
    check("any other alias teaches itself, never a name nobody said",
          acquisition.overheard_names("Quill came in.", {"odile_quill": {"known_as": "the dyer"}}, people)
          == [("odile_quill", "Quill")])
    check("an alias whose words all sit inside the witness's descriptor teaches nothing",
          acquisition.overheard_names("The old man sat.", {"odile_quill": {"known_as": "the old woman"}}, people) == []
          and acquisition.overheard_names("The tallyman sat.", {"tansy_old": {"known_as": "tallyman"}}, people) == [])
    check("a name inside a longer word is not heard",
          acquisition.overheard_names("She turned away.", rels, people) == [])
    check("a name beside an underscore still names (markdown italics, an id label)",
          named("_Ned_ left.") == ["ned"] and named("ned_carter: Yes.") == ["ned"])
    check("hearing the id's first word, when `name` lacks it, teaches what was heard, not a name nobody said",
          acquisition.overheard_names("Uncle Osric came.", {"osric_uncle": {"known_as": "the old man"}},
                                      [{"id": "osric_uncle", "name": "Agnes Bright", "what": "x"}])
          == [("osric_uncle", "Osric")])
    check("a cue PHRASE (wounds, topics) still reads by containment - only names are bounded",
          facets._mentions("the mill", _normalize("down by the millpond")) is True)
    findings = contracts.check({"people": [corby]}, contracts_world.WORLD)
    check("the world contract declares people[].aliases (an undeclared key would refuse the run)",
          not [f for f in findings if "aliases" in str(f.get("path"))], findings)


def main():
    print("test_presence.py - pinning presence.py: named is not present\n")
    for t in sorted((v for k, v in globals().items()
                     if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        t()
    print("\n%s" % ("test_presence: OK" if not FAIL else "FAILED:"))
    for f in FAIL:
        print("  - %s" % f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
