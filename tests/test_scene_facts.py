"""test_scene_facts.py — the POV fact ledger: the leak tests first, then shape, render, measurement.

WHAT THIS GUARDS, in order of importance:

  1. THE LEAK. No actor receives a fact from a beat it was not present for. The first version of the
     ledger read every `entity.<id>` percept key as a witness; a person merely SPOKEN OF (a percept
     marked `present: False`) received four facts from a room he never entered, and this suite's own
     recorded-run check could not see it because it derived "who was present" with the very function
     it was checking. So the leak cases here carry their own oracle: in-memory fixtures whose truth is
     written by hand, and on a recorded run the scenes' PINNED CASTS, read from `scene_cfgs` — a source
     the code path under test never consults.
  2. THE SHAPE. `self` resolves to the speaker; a superseded event contributes nothing; the budget is
     per kind and never splits a beat.
  3. THE RENDER. What changed hands is one register, what was said ("as you heard it") another; the
     renderer adds no number; an unknown word refuses.
  4. A RECORDED RUN (optional). With SWE_FACTS_DB pointing at a COPY of a chronicle it ASSERTS the
     cast-oracle leak rule and that the budget drops no passing on that data, and PRINTS coverage.
     SWE_FACTS_ARM (a re-answer file) supplies rows for beats that predate the transfers contract;
     SWE_FACTS_FLAGS (a book-side file of critic flags) drives the coverage print. Both live beside the
     book, never here: hard rule 1 bans a book's cast AND its plot from this repo, and the first version
     of this suite carried a book's flag list inline.

Deterministic, stdlib only, no API.
"""
import io
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import scene_facts                                    # noqa: E402
from src.engine.presence import present_ids                           # noqa: E402
from src.engine.direction import direct_facts                          # noqa: E402
from src.engine.errors import EngineError                              # noqa: E402
from src.engine.records import RecordError                             # noqa: E402

_FAILED = []


def check(name, ok, detail=""):
    print("   %-60s %s%s" % (name, "PASS" if ok else "FAIL", "" if ok else "  <- %s" % (detail,)))
    if not ok:
        _FAILED.append(name)


def _chronicle(beats, manifest_style="present"):
    """An in-memory chronicle. `beats` = [(turn, speaker, payload, present_ids, mentioned_ids)].

    manifest_style "present": the manifest carries the `present` key (a post-fix run).
    manifest_style "old": no `present` key; percepts list everyone MENTIONED (present or not) and
    edges list only the present people — the shape every manifest before the fix had.
    manifest_style "none": no manifests at all.
    """
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE turns (run_id TEXT, turn INT, actor TEXT)")
    con.execute("CREATE TABLE events (event_id INTEGER PRIMARY KEY, run_id TEXT, turn INT, "
                "effective_at INT, type TEXT, payload TEXT)")
    con.execute("CREATE TABLE decision_manifests (run_id TEXT, turn INT, actor TEXT, manifest TEXT)")
    for turn, speaker, payload, here, mentioned in beats:
        con.execute("INSERT INTO turns VALUES (?,?,?)", ("r", turn, speaker))
        con.execute("INSERT INTO events (run_id, turn, effective_at, type, payload) VALUES (?,?,?,?,?)",
                    ("r", turn, turn, "act", json.dumps(payload)))
        if manifest_style == "none":
            continue
        percepts = ["entity.%s" % i for i in sorted(set(here) | set(mentioned))]
        m = {"percepts": percepts, "edges": [i for i in here if i != speaker]}
        if manifest_style == "present":
            m["present"] = sorted(here)
        con.execute("INSERT INTO decision_manifests VALUES (?,?,?,?)", ("r", turn, speaker, json.dumps(m)))
    return con


def _turns(rows):
    return sorted(int(r["turn"]) for r in rows)


_BEATS = [
    # turn, speaker, payload, who is PRESENT, who is only MENTIONED (spoken of, not in the room)
    (0, "ada", {"transfers": [{"what": "the coin", "from": "ada", "to": "bo", "terms": "price"}]},
     ["ada", "bo"], ["dee"]),
    (1, "bo", {"told": [{"what": "the orchard is mine", "to": "ada", "cost": "exposure"}]},
     ["bo"], ["ada"]),                       # ada stepped out: mentioned, not present
    (2, "ada", {"transfers": [{"what": "the token", "from": "ada", "to": "cy", "terms": "loan"}]},
     ["ada", "bo", "cy"], ["dee"]),
]


def test_the_leak():
    print("\n[1] THE LEAK — present, not merely mentioned; the oracle is written by hand")
    con = _chronicle(_BEATS, "present")
    check("ada-gets-her-own-and-witnessed-beats", _turns(scene_facts.facts_for(con, "r", "ada")) == [0, 2])
    check("ada-mentioned-at-t1-but-absent-gets-nothing-from-it",
          1 not in _turns(scene_facts.facts_for(con, "r", "ada")))
    check("bo-gets-all-three", _turns(scene_facts.facts_for(con, "r", "bo")) == [0, 1, 2])
    check("cy-gets-only-the-beat-he-was-in", _turns(scene_facts.facts_for(con, "r", "cy")) == [2])
    check("dee-MENTIONED-EVERYWHERE-PRESENT-NOWHERE-gets-nothing",
          scene_facts.facts_for(con, "r", "dee") == [],
          "the exact shape of the shipped defect: a percept key with present False")

    print("   -- a manifest written BEFORE the present key (read through its edges)")
    old = _chronicle(_BEATS, "old")
    check("old-manifest-mentioned-person-gets-nothing", scene_facts.facts_for(old, "r", "dee") == [])
    check("old-manifest-absent-at-t1-gets-nothing-from-it",
          1 not in _turns(scene_facts.facts_for(old, "r", "ada")))
    check("old-manifest-present-person-still-witnesses", _turns(scene_facts.facts_for(old, "r", "cy")) == [2])

    print("   -- presence recorded as UNTRACKED (a null present key: the chair)")
    untracked = _chronicle(_BEATS, "present")
    untracked.execute("UPDATE decision_manifests SET manifest = json_set(manifest, '$.present', json('null'))")
    check("untracked-presence-gives-the-speaker-alone", _turns(scene_facts.facts_for(untracked, "r", "bo")) == [1])
    check("untracked-presence-leaks-nothing-to-the-named", scene_facts.facts_for(untracked, "r", "dee") == [])
    print("   -- no manifests at all")
    bare = _chronicle(_BEATS, "none")
    check("no-manifest-leaves-only-the-speakers-own", _turns(scene_facts.facts_for(bare, "r", "bo")) == [1])
    check("no-manifest-leaks-nothing-to-a-bystander", scene_facts.facts_for(bare, "r", "cy") == [])

    print("   -- the one presence rule")
    ids = present_ids([{"ref": "entity.ada", "present": True}, {"ref": "entity.dee", "present": False},
                       {"ref": "entity.eve"}, {"ref": "prop.lamp"}, {"ref": "entity."}])
    check("present-ids-skips-present-false-and-keeps-untracked", ids == ["ada", "eve"], ids)


def test_the_shape():
    print("\n[2] THE SHAPE — self, corrections, a per-kind budget that never splits a beat")
    con = _chronicle(_BEATS, "present")
    bo = scene_facts.facts_for(con, "r", "bo")
    check("most-recent-first", [r["turn"] for r in bo] == [2, 1, 0], [r["turn"] for r in bo])
    check("before_turn-excludes-the-beat-being-composed",
          _turns(scene_facts.facts_for(con, "r", "bo", before_turn=2)) == [0, 1])

    selfish = _chronicle([(0, "ada", {"transfers": [{"what": "the coin", "from": "self", "to": "bo",
                                                     "terms": "price"}],
                                      "told": [{"what": "hush", "to": "self", "cost": "none"}]},
                           ["ada", "bo"], [])], "present")
    rows = scene_facts.facts_for(selfish, "r", "bo")
    passed = [r for r in rows if r["kind"] == "passed"][0]
    told = [r for r in rows if r["kind"] == "told"][0]
    check("self-in-a-transfer-resolves-to-the-speaker", passed["from"] == "ada", passed)
    check("self-as-hearer-resolves-to-the-speaker", told["to"] == "ada", told)

    corrected = _chronicle(_BEATS, "present")
    victim = corrected.execute("SELECT event_id FROM events WHERE turn=0").fetchone()[0]
    corrected.execute("INSERT INTO events (run_id, turn, effective_at, type, payload) VALUES (?,?,?,?,?)",
                      ("r", 3, 3, "correction", json.dumps({"supersedes": [victim], "turn": 0})))
    check("a-superseded-event-contributes-no-row",
          0 not in _turns(scene_facts.facts_for(corrected, "r", "bo")))
    check("a-correction-not-yet-in-effect-does-not-apply",
          0 in _turns(scene_facts.facts_for(corrected, "r", "bo", before_turn=3)))

    many = [(t, "ada", {"told": [{"what": "line %s a" % chr(97 + t), "to": "bo", "cost": "none"},
                                 {"what": "line %s b" % chr(97 + t), "to": "bo", "cost": "none"}],
                        "transfers": ([{"what": "the token", "from": "ada", "to": "bo", "terms": "loan"}]
                                      if t == 0 else [])},
             ["ada", "bo"], []) for t in range(4)]
    heavy = _chronicle(many, "present")
    capped = scene_facts.facts_for(heavy, "r", "bo", budgets={"passed": 24, "told": 3})
    told_turns = [r["turn"] for r in capped if r["kind"] == "told"]
    check("told-budget-keeps-whole-beats-only", told_turns == [3, 3], told_turns)
    check("a-run-of-tellings-cannot-push-a-loan-off",
          any(r["kind"] == "passed" and r["turn"] == 0 for r in capped), capped)
    try:
        scene_facts.for_actor({}, "bo", {})
        check("for_actor-refuses-a-non-list", False, "accepted a dict")
    except RecordError:
        check("for_actor-refuses-a-non-list", True)
    try:
        scene_facts.witnessed({"speaker": "bo", "turn": 0}, "", {})
        check("witnessed-refuses-an-empty-actor", False, "accepted no actor")
    except RecordError:
        check("witnessed-refuses-an-empty-actor", True)


def test_the_render():
    print("\n[3] THE RENDER — seen and heard are two registers")
    rows = [{"kind": "passed", "turn": 2, "speaker": "ada", "what": "the token",
             "from": "ada", "to": "cy", "terms": "loan"},
            {"kind": "told", "turn": 1, "speaker": "bo", "what": "the orchard is mine",
             "to": "ada", "cost": "exposure"},
            {"kind": "told", "turn": 0, "speaker": "ada", "what": "hush", "to": "ada", "cost": "none"},
            {"kind": "passed", "turn": 0, "speaker": "ada", "what": "the coin",
             "from": "ada", "to": "bo", "terms": "price"}]
    out = direct_facts(rows, "ada")
    print("       ada reads: %s" % out)
    check("seen-first-in-its-own-register",
          out.startswith("What changed hands: you lent the token to Cy; you paid the coin to Bo."), out)
    check("heard-is-rendered-as-heard", "What was said, as you heard it: Bo told you, at their own "
                                        "exposure: the orchard is mine" in out, out)
    check("a-telling-to-oneself-is-said-aloud", "you said aloud: hush" in out, out)
    # The RENDERER adds no number. It cannot claim the content carries none: the `what` is the
    # seat's own quote of the action, and a quantity in it is story content the law permits.
    check("the-renderer-adds-no-number", not any(ch.isdigit() for ch in out), out)
    check("empty-rows-render-empty", direct_facts([], "ada") == "")
    check("only-heard-renders-only-heard",
          direct_facts(rows[1:2], "ada").startswith("What was said, as you heard it:"))
    for bad, why in (({"kind": "passed", "what": "x", "from": "a", "to": "b", "terms": "gifted"},
                      "unknown terms"),
                     ({"kind": "told", "what": "x", "to": "b", "cost": "shame"}, "unknown cost"),
                     ({"kind": "moved", "what": "x"}, "unknown kind"),
                     ({"kind": "passed", "what": "", "from": "a", "to": "b", "terms": "price"},
                      "empty what")):
        try:
            direct_facts([bad], "ada")
            check("refuses-%s" % why.replace(" ", "-"), False, "rendered %r" % (bad,))
        except EngineError:
            check("refuses-%s" % why.replace(" ", "-"), True)


def _cast_by_turn(con, run):
    """{turn: set(cast ids)} from the scenes' PINNED cfgs — the oracle. Independent of the code path,
    which reads manifests and never consults scene_cfgs."""
    out = {}
    for start, end, fp in con.execute("SELECT start_turn, end_turn, cfg_fingerprint FROM scenes "
                                      "WHERE run_id=?", (run,)):
        body = con.execute("SELECT body FROM scene_cfgs WHERE fingerprint=?", (fp,)).fetchone()
        cast = {c.get("id") for c in (json.loads(body[0]).get("cast") or []) if isinstance(c, dict)} if body else set()
        for t in range(int(start), int(end) + 1):
            out[t] = cast
    return out


def test_against_a_recorded_run():
    print("\n[4] A RECORDED RUN — cast-oracle leak rule and the budget (assert); coverage (print)")
    db = os.environ.get("SWE_FACTS_DB")
    if not db or not os.path.isfile(db):
        print("       SKIPPED: set SWE_FACTS_DB to a COPY of a chronicle db (SWE_FACTS_ARM and")
        print("       SWE_FACTS_FLAGS optional). This suite therefore covers the in-memory cases only.")
        return
    con = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    run = con.execute("SELECT run_id FROM runs LIMIT 1").fetchone()[0]
    speakers = {int(t): a for t, a in con.execute("SELECT turn, actor FROM turns WHERE run_id=?", (run,))}
    arm = os.environ.get("SWE_FACTS_ARM")
    if arm and os.path.isfile(arm):
        answers = json.load(io.open(arm, encoding="utf-8"))
        rows = [r for t in sorted(int(k) for k in answers)
                for r in scene_facts._rows(answers[str(t)], t, speakers.get(t))]
        print("       rows from the re-answer file: %d" % len(rows))
    else:
        rows = scene_facts.run_rows(con, run)
        print("       rows from the db payloads: %d" % len(rows))
    seen = scene_facts.present_by_turn(con, run)
    cast = _cast_by_turn(con, run)
    everyone = set()
    for (blob,) in con.execute("SELECT manifest FROM decision_manifests WHERE run_id=?", (run,)):
        everyone |= {p[len("entity."):] for p in (json.loads(blob).get("percepts") or [])
                     if isinstance(p, str) and p.startswith("entity.")}
    in_any_cast = set().union(*cast.values()) if cast else set()
    mentioned_only = sorted(everyone - in_any_cast)
    print("       people only ever mentioned, never cast: %d" % len(mentioned_only))

    leaks = []
    for who in sorted(everyone | in_any_cast):
        for r in scene_facts.for_actor(rows, who, seen, budgets=None):
            if r.get("speaker") != who and who not in cast.get(int(r["turn"]), set()):
                leaks.append((who, r["turn"]))
    check("no-actor-holds-a-fact-from-a-scene-whose-cast-excludes-them", not leaks, leaks[:6])
    check("the-mentioned-only-receive-nothing",
          all(not scene_facts.for_actor(rows, who, seen, budgets=None) for who in mentioned_only),
          mentioned_only)

    dropped = []
    for who in sorted(in_any_cast):
        for t in sorted(speakers):
            upto = [r for r in rows if int(r["turn"]) < t]
            full = [r for r in scene_facts.for_actor(upto, who, seen, budgets=None) if r["kind"] == "passed"]
            kept = [r for r in scene_facts.for_actor(upto, who, seen) if r["kind"] == "passed"]
            if len(kept) != len(full):
                dropped.append((who, t, len(full) - len(kept)))
    check("the-shipped-budget-drops-no-passing-on-this-data", not dropped, dropped[:6])

    flags_file = os.environ.get("SWE_FACTS_FLAGS")
    if not flags_file or not os.path.isfile(flags_file):
        print("       (no SWE_FACTS_FLAGS: coverage not printed)")
        return
    flags = json.load(io.open(flags_file, encoding="utf-8"))["flags"]
    print("       coverage at the SHIPPED budget, by the flag's keyword in a row from its source beat.")
    print("       A keyword match is not a proof the contradicted fact is carried; read the clause.")
    hit = 0
    for f in flags:
        who = speakers.get(int(f["turn"]))
        mine = scene_facts.for_actor([r for r in rows if int(r["turn"]) < int(f["turn"])], who, seen)
        held = [r for r in mine if int(r["turn"]) == int(f["source"]) and f["keyword"].lower() in r["what"].lower()]
        hit += bool(held)
        print("       t%-3s vs t%-3s  %-3s" % (f["turn"], f["source"], "YES" if held else "no"))
    print("       covered %d of %d" % (hit, len(flags)))
    con.close()


def main():
    print("=" * 78)
    print("scene_facts — the POV fact ledger")
    print("=" * 78)
    test_the_leak()
    test_the_shape()
    test_the_render()
    test_against_a_recorded_run()
    print("\n" + "=" * 78)
    if _FAILED:
        print("FAILED: %s" % ", ".join(_FAILED))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
