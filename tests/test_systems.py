"""test_systems.py — which engine systems a book runs (src/engine/systems.py, gate systems-registry).

WHAT THIS PINS (2026-09-22). The owner: "not every book needs everything we had ... a plug and play mech
for the book so user can decide what scripts they want the engine to use." A book says so in its world
note, beside `switches`:  "systems": {"wounds": false}. This suite holds the promise that makes the switch
safe to use - OFF is IDENTITY, and saying nothing changes nothing:

  [1] `for_book` reads the declaration and refuses, by code, one it cannot honour;
  [2] `strip` leaves an all-on sheet untouched and empties exactly the off system's block;
  [3] condition OFF: the stage line and the prompt say nothing of energy, and memory runs on the full
      budget - the census's one absence that used to LIE (it rendered the top band);
  [4] seated two-scene runs through the real driver: no key and an explicit all-on list write the same
      rows; each switchable system off alone stops its own mover's rows and no other system's; the
      replay (`mood_fold`) still re-derives every cached mood;
  [5] the pre-run check stops demanding an off system's block and warns on one authored for nothing;
  [6] the chair (scripts/direct.py) strips too, and its operator line says nothing of an off condition;
  [7] the authoring blueprint names every system the registry has.

The book is invented here (two keepers on a rock), per hard rule 1. Script-style; exit 0 = all pass.
"""
import contextlib
import copy
import glob
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import bible, mood_fold, rungs, systems            # noqa: E402
from src.engine.records import Reading, RecordError                # noqa: E402
from test_vault import CHAR_ENGINE, WORLD_ENGINE                   # noqa: E402

FAILS = []
VOLATILE = {"run_id", "committed_at", "created_at", "recorded_at", "built_at", "at", "ts", "timestamp"}
# THE ENGINE AS IT WAS before the switch existed - written out, not derived from the registry, because it is
# a claim about the past: every one of these runs when a book says nothing, and nothing added since does.
LEGACY = frozenset({"emotion", "perception", "memory", "bonds", "attachments", "laws",
                    "condition", "wounds", "attitude", "arc"})


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _code(fn):
    try:
        fn()
    except RecordError as e:
        return e.code
    return None


# ---------------------------------------------------------------------------------------------------
def test_for_book():
    print("\n[1] for_book: the declaration read, and refused by code where it cannot be honoured")
    legacy = systems.defaults()
    check("no-key-runs-every-legacy-system", systems.for_book(dict(WORLD_ENGINE)) == legacy, sorted(legacy))
    check("...and-an-empty-map-too", systems.for_book({"systems": {}}) == legacy)
    check("...and-no-world-at-all", systems.for_book(None) == legacy)
    all_on = {"systems": {k: True for k in LEGACY}}
    check("an-explicit-all-on-list-is-the-same-set", systems.for_book(all_on) == legacy)
    check("...and-is-not-recorded-as-a-declaration", not systems.declared(all_on) and not systems.declared({}))
    off = systems.for_book({"systems": {"wounds": False, "arc": False}})
    check("a-name-set-false-is-off-and-only-it", off == legacy - {"wounds", "arc"}, sorted(off))
    check("...and-that-book-is-declared", systems.declared({"systems": {"wounds": False}}))
    check("the-defaults-are-EXACTLY-the-legacy-systems", legacy == LEGACY, sorted(legacy ^ LEGACY))
    check("...and-every-NEW-system-ships-off", not (set(systems.REGISTRY) - LEGACY) & legacy,
          sorted(set(systems.REGISTRY) - LEGACY))
    for code, decl in (("SYSTEMS_NOT_A_MAP", ["wounds"]),
                       ("SYSTEMS_UNKNOWN", {"magic": False}),                 # a law switch, not a system
                       ("SYSTEMS_VALUE_NOT_BOOL", {"wounds": "no"}),
                       ("SYSTEMS_VALUE_NOT_BOOL", {"wounds": 0}),
                       ("SYSTEMS_NOT_SWITCHABLE", {"emotion": False})):
        got = _code(lambda: systems.for_book({"systems": decl}))
        check("refuses-%s-%s" % (code, json.dumps(decl)), got == code, got)
    check("a-core-system-may-be-SAID-on", systems.for_book({"systems": {"emotion": True}}) == legacy)


def test_strip():
    print("\n[2] strip: identity when all on; exactly the off block emptied")
    sheet = copy.deepcopy(CHAR_ENGINE)
    sheet["baseline"]["wounds"] = [{"id": "w1", "concept": "the sea", "path": "WARINESS", "intensity": 0.6}]
    sheet["current"]["toward"] = {"ada": {"WARINESS": 0.2}}
    before = json.dumps(sheet, sort_keys=True)
    check("all-on-leaves-the-sheet-byte-identical",
          json.dumps(systems.strip(copy.deepcopy(sheet), systems.defaults()), sort_keys=True) == before)
    for name, (tier, key, empty) in (("condition", ("current", "condition", {})), ("wounds", ("baseline", "wounds", [])),
                                     ("attitude", ("current", "toward", {}))):
        got = systems.strip(copy.deepcopy(sheet), systems.defaults() - {name})
        want = copy.deepcopy(sheet)
        want[tier][key] = empty
        check("%s-off-empties-%s.%s-and-nothing-else" % (name, tier, key),
              json.dumps(got, sort_keys=True) == json.dumps(want, sort_keys=True))
    check("arc-off-owns-no-block-so-the-sheet-is-untouched",
          json.dumps(systems.strip(copy.deepcopy(sheet), systems.defaults() - {"arc"}), sort_keys=True) == before)
    off = systems.defaults() - {"wounds", "attitude", "condition"}
    check("authored_for_off-names-each-authored-block-the-book-switched-off",
          sorted(systems.authored_for_off(sheet, off)) == ["attitude", "condition", "wounds"],
          systems.authored_for_off(sheet, off))
    check("...and-nothing-when-all-on", systems.authored_for_off(sheet, systems.defaults()) == [])


def test_condition_off_is_silence():
    print("\n[3] condition OFF: nothing said of energy, and memory on the full budget")
    from src.engine.scene import assemble
    from src.engine.prompt import build_turn_messages
    from src.engine.direction import direct_condition
    import direct
    maren = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    world = json.load(open(os.path.join(REPO, "world", "ashford-slice.json"), encoding="utf-8"))
    ev = "Edda comes up the path carrying a feverish child, and the healer's lamp gutters in the wind."
    sl = {"event": {"text": ev, "kind": "threat"}, "recent": [], "location": "healers_house"}

    def packet(ch):
        return assemble(ch, world, sl, dict(ch["current"]["affect"]), ch["current"]["condition"])

    def prompt(pk, ch):
        return "\n".join(m["content"] for m in build_turn_messages(
            pk, ev, ch["baseline"]["temperament"], ch["current"].get("relationships") or {},
            rung_direction=direct.rung_direction(pk)))

    on = copy.deepcopy(maren)
    off = systems.strip(copy.deepcopy(maren), systems.defaults() - {"condition"})
    line = direct_condition(on["current"]["condition"])
    check("control-the-authored-condition-has-a-stage-line", bool(line), line)
    check("an-absent-condition-says-NOTHING-not-the-top-band", direct_condition({}) == "", direct_condition({}))
    p_on, p_off = prompt(packet(on), on), prompt(packet(off), off)
    check("control-the-on-prompt-carries-it", line[1:] in p_on, line)
    check("the-off-prompt-does-not", line[1:] not in p_off and direct_condition({"energy": 1.0, "allostatic_load": 0.0})[1:] not in p_off)
    check("...and-leaves-no-empty-sentence-where-it-was", not any(ln.strip() == "." for ln in p_off.splitlines()),
          [ln for ln in p_off.splitlines() if ln.strip() == "."])
    full = copy.deepcopy(maren)
    full["current"]["condition"] = {"energy": 1.0, "allostatic_load": 0.0}
    low = copy.deepcopy(maren)
    low["current"]["condition"] = {"energy": 0.1, "allostatic_load": 0.9}
    n_off, n_full, n_low = (len(packet(c)["volatile"]["recall"]) for c in (off, full, low))
    check("control-a-low-budget-recalls-less", n_low < n_full, (n_low, n_full))
    check("the-off-sheet-recalls-what-a-FULL-budget-recalls", n_off == n_full, (n_off, n_full))
    from src.engine import arc
    check("the-arc-reads-an-absent-load-as-the-gate-does-0",
          arc.derive_resilience(off, {}) == arc.derive_resilience(off, {"allostatic_load": 0.0}))


# ---------------------------------------------------------------------------------------------------
def _book(tmp, decl=None):
    """Two keepers on a rock, each with an edge to the other, WARINESS raised and a scar they came in with
    (drowning, on DEFLATION - built by the engine's own `wound.make`); `decl` -> world.systems.

    THE SCAR THEY CAME IN WITH is what lets this suite see the replay's own switch: a book with wounds off
    strips it before the first beat, and a replay that did not strip it too would multiply every reading
    about drowning by its investment and disagree with the cache (measured by mutation, 2026-09-22)."""
    from src.engine import wound
    book = os.path.join(tmp, "The Rock and the Rose")
    for sub in ("world", "characters", "people"):
        os.makedirs(os.path.join(book, sub), exist_ok=True)
    world = dict(WORLD_ENGINE, people=[{"id": "mira", "what": "the keeper"}, {"id": "ada", "what": "the relief keeper"}])
    if decl is not None:
        world["systems"] = decl
    with open(os.path.join(book, "world", "The Rock.md"), "w", encoding="utf-8") as fh:
        fh.write("---\ntype: world\nid: The Rock\n---\n# The Rock\n\n```json\n%s\n```\n" % json.dumps(world, indent=1))
    for name, other in (("Mira", "ada"), ("Ada", "mira")):
        eng = copy.deepcopy(CHAR_ENGINE)
        eng["fixed"]["name"] = name
        eng["current"]["relationships"] = {other: {"trust": 0.7, "affinity": 0.65, "respect": 0.6, "debt": 0.0}}
        eng["current"]["affect"]["WARINESS"] = 0.75
        eng["baseline"]["wounds"] = [wound.make("drowning", "DEFLATION", 0.7, "profile:fixture-drowning", text="the boat that went down",
                                                triggers=["the sea"])]
        with open(os.path.join(book, "characters", "%s.md" % name), "w", encoding="utf-8") as fh:
            fh.write("---\ntype: character\nid: %s\n---\n# %s\n\n```json\n%s\n```\n" % (name, name, json.dumps(eng, indent=1)))
    return book


def _cfg(tmp, name, time, lasts):
    path = os.path.join(tmp, name + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"name": name, "at": {"day": 1, "time": time}, "lasts": lasts,
                   "situation": "The two keepers wait out the gale in the lamp room.",
                   "cast": [{"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}]}, fh)
    return path


def _seated(tmp, decl):
    """Two scenes (the second a --resume) through scripts/scene.py main IN PROCESS, the actor and both seats
    faked at their seams and tuned so every mover gets its chance: every beat lasting (the arc and the
    mint), a reading about the other keeper (attitude, bonds) and, on odd turns, a high one about a concept
    (the scar). -> (db, run_id, [the condition each speaker's packet carried])."""
    import scene
    book = _book(tmp, decl)
    seen = []

    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        seen.append(dict(packet["volatile"]["state"]["condition"]))
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        return ({"action": "She trims the wick and says the wind is backing.", "thought": "", "exit": False,
                 "addressee": other, "act": "",
                 "tags": {"type": "threat", "summary": "trims the wick", "dimensions": {"threat": 0.7},
                          "durability": "durable", "subject": other,
                          "object": other, "showed": {"affinity": 0.85, "trust": 0.8}}}, [])

    def refuse(*_a, **_k):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked out of this test")

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=(), **_k):
        other = next(p for p in present if p != me)
        high = (turn or 0) % 2 == 1
        rs = [Reading(path="WARINESS", rung=rungs.rung_at("WARINESS", 0.92 if high else 0.4)[1],
                      about="concept:sickness" if high else other, confidence="sure"),
              Reading(path="GOODWILL", rung=rungs.rung_at("GOODWILL", 0.5)[1], about=other, confidence="likely")]
        if high:                                              # the scar they came in with is read about
            rs.append(Reading(path="DEFLATION", rung=rungs.rung_at("DEFLATION", 0.5)[1], about="concept:drowning", confidence="sure"))
        else:
            # A BEAT THAT LANDS HARD ON ITS OWN. Measured building this suite: the arc's only diffs came on the
            # beats the scar fired (its investment lifts the impact past arc._ARC_THRESHOLD), so switching
            # wounds off silenced the arc too - a true interaction, not a leak. This reading moves the arc
            # with no scar at all, so each system's own switch is tested on its own.
            rs.append(Reading(path="DISPLEASURE", rung=rungs.rung_at("DISPLEASURE", 0.95)[1], about=other, confidence="sure"))
        return rs, [other], "sure", []

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, refuse, emotion
    try:
        for i, (name, time, lasts, budget) in enumerate((("gale-1", "21:00", "1h", 6), ("gale-2", "22:30", "30m", 4))):
            argv = ["scene.py", "--book", book, "--scene", _cfg(tmp, name, time, lasts), "--budget", str(budget),
                    "--model", "fake/model", "--no-keeper"]
            if i:
                db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
                argv += ["--resume", sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0]]
            sys.argv = argv
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                scene.main()
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv = saved
    db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
    return db, sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0], seen


def _rows(db):
    """Every row of every table, the volatile columns masked and the bible's own fingerprint and world text
    normalised - they differ by the `systems` key itself, which is the point of the comparison."""
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    fps = [r[0] for r in con.execute("SELECT fingerprint FROM bibles")]
    out = {}
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        rows = []
        for r in con.execute("SELECT * FROM %s" % t):
            d = {k: ("<V>" if k in VOLATILE else r[k]) for k in r.keys()}
            if t == "bibles":
                d["world"] = json.dumps({k: v for k, v in json.loads(d["world"]).items() if k != "systems"}, sort_keys=True)
            s = json.dumps(d, sort_keys=True, default=str)
            for fp in fps:
                s = s.replace(fp, "<FP>")
            rows.append(s)
        out[t] = sorted(rows)
    con.close()
    return out


def _count(db, table):
    return sqlite3.connect(db).execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]


def test_seated_runs(tmp):
    print("\n[4] seated two-scene runs through the real driver")
    runs = {}
    for label, decl in (("no-key", None), ("all-on", {k: True for k in systems.SWITCHABLE if k in LEGACY}),
                        ("wounds-off", {"wounds": False}), ("attitude-off", {"attitude": False}),
                        ("arc-off", {"arc": False}), ("condition-off", {"condition": False})):
        runs[label] = _seated(os.path.join(tmp, label), decl)
    base, same = _rows(runs["no-key"][0]), _rows(runs["all-on"][0])
    differ = sorted(t for t in set(base) | set(same) if base.get(t) != same.get(t))
    check("no-key-and-an-explicit-all-on-list-write-IDENTICAL-rows", differ == [], differ)
    movers = {"wounds": ("wound_minted", "wound_deltas"), "attitude": ("toward_deltas",), "arc": ("arc_diffs",)}
    n = {label: {t: _count(runs[label][0], t) for ts in movers.values() for t in ts} for label in runs}
    check("control-with-every-system-on-every-mover-writes", all(v > 0 for v in n["no-key"].values()), n["no-key"])
    for sysname, tables in movers.items():
        mine = n["%s-off" % sysname]
        check("%s-off-its-mover-writes-NOTHING" % sysname, all(mine[t] == 0 for t in tables), mine)
        others = {t: mine[t] for s, ts in movers.items() if s != sysname for t in ts}
        check("...while-the-others-still-write-theirs", all(v > 0 for v in others.values()), others)
    check("condition-off-every-mover-still-writes", all(v > 0 for v in n["condition-off"].values()),
          n["condition-off"])
    check("condition-off-every-packet-carried-NO-condition", runs["condition-off"][2] and not any(runs["condition-off"][2]),
          runs["condition-off"][2][:2])
    check("control-condition-on-every-packet-carried-it", all(runs["no-key"][2]), runs["no-key"][2][:2])
    for label in ("no-key", "wounds-off", "condition-off"):
        man = [json.loads(r[0]).get("systems") for r in sqlite3.connect(runs[label][0]).execute(
            "SELECT manifest FROM decision_manifests")]
        want = None if label == "no-key" else sorted(systems.for_book({"systems": {label.split("-")[0]: False}}))
        check("%s-each-beat-records-%s" % (label, "no-set" if want is None else "the-set-it-ran"),
              man and all(m == want for m in man), man[:1])
    for label, (db, run_id, _seen) in sorted(runs.items()):
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row                     # bible.for_run reads its row by column name
        d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
        check("%s-the-replay-re-derives-every-cached-mood" % label,
              d["at"] is None and not d["missing"] and d["rows"] == d["cached"] and not d["notes"], d)


def test_lint():
    print("\n[5] the pre-run check: an off system's block is not demanded; one authored for nothing warns")
    import lint_book
    world = json.load(open(os.path.join(REPO, "world", "ashford-slice.json"), encoding="utf-8"))
    maren = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    bare = copy.deepcopy(maren)
    del bare["current"]["condition"]
    got = lint_book.lint(world, {"maren": bare})
    check("control-with-condition-on-a-missing-block-is-an-error", any("current.condition" in e for e in got["errors"]), got["errors"])
    got = lint_book.lint(dict(world, systems={"condition": False}), {"maren": bare})
    check("condition-off-the-same-sheet-passes", not any("condition" in e for e in got["errors"]), got["errors"])
    got = lint_book.lint(dict(world, systems={"condition": False}), {"maren": maren})
    check("a-block-authored-for-an-off-system-WARNS", any("condition block is authored" in w for w in got["warnings"]),
          [w for w in got["warnings"] if "system" in w])
    half = copy.deepcopy(maren)
    del half["current"]["condition"]["allostatic_load"]
    got = lint_book.lint(world, {"maren": half})
    check("a-half-authored-condition-WARNS", any("only one of energy / allostatic_load" in w for w in got["warnings"]))
    got = lint_book.lint(dict(world, systems={"magic": False}), {"maren": maren})
    check("a-declaration-the-engine-cannot-honour-is-an-ERROR", any(e.startswith("world.systems:") and "SYSTEMS_UNKNOWN" in e
                                                                  for e in got["errors"]), got["errors"])


def _chair(tmp, decl):
    """One durable chair beat through scripts/direct.py's CLI -> (book, returncode, output, operator lines)."""
    book = _book(tmp, decl)
    r = subprocess.run([sys.executable, os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira", "--stub"],
                       input="by:ada Ada brought new wicks for the lamp [durable]\nquit\n",
                       capture_output=True, text=True, cwd=REPO, timeout=300)
    out = (r.stdout or "") + (r.stderr or "")
    return book, r.returncode, out, [ln for ln in out.splitlines() if ln.startswith("  Mira")]


def test_chair(tmp):
    print("\n[6] the chair strips too, and says nothing of an off condition")
    from src.engine import direction
    phrase = direction.direct_condition(CHAR_ENGINE["current"]["condition"])
    _b, rc_on, out_on, tail_on = _chair(os.path.join(tmp, "on"), None)
    check("control-condition-on-the-operator-line-ends-with-the-stage-line",
          rc_on == 0 and tail_on and tail_on[-1].endswith("; %s." % phrase), tail_on[-1:] or out_on[-400:])
    book, rc, out, tail = _chair(os.path.join(tmp, "off"), {"condition": False, "wounds": False})
    check("the-chair-turn-commits", rc == 0, out[-500:])
    db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
    man = [json.loads(m[0]) for m in sqlite3.connect(db).execute("SELECT manifest FROM decision_manifests")]
    check("...and-records-the-set-it-ran", man and man[-1].get("systems") == sorted(systems.defaults() - {"condition", "wounds"}),
          [m.get("systems") for m in man])
    conds = [json.loads(c[0]) for c in sqlite3.connect(db).execute("SELECT condition FROM current_state WHERE char_id = 'mira'")]
    check("...and-the-chair-row-carries-NO-condition", conds and conds[-1] == {}, conds)
    # the mood summary itself joins its paths with "; ", so the test is the four band sentences, not the separator
    check("condition-off-the-operator-line-says-nothing-of-energy",
          tail and tail[-1].endswith(".") and not tail[-1].endswith("; .")
          and not any(s in tail[-1] for _cut, s in direction._COND), tail[-1:])


def _chair_seated(tmp, decl):
    """One SEATED chair beat through scripts/direct.py main IN PROCESS: a supplied durable turn about the
    other keeper, the event seat refused, the emotion seat faked high - a concept reading (the mint) and
    three about the other keeper (the arc's impact, the attitude). -> the db."""
    import builtins
    import direct
    book = _book(tmp, decl)
    tj = os.path.join(tmp, "turn.json")
    with open(tj, "w", encoding="utf-8") as fh:
        json.dump({"action": 'Mira grips the rail. "The oil is gone and the light will fail."', "thought": "not again",
                   "tags": {"type": "threat", "summary": "the lamp oil is gone", "dimensions": {"threat": 0.9},
                            "durability": "durable", "subject": "ada"}}, fh)

    def refuse(*_a, **_k):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked out of this test")

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=None, **_k):
        return ([Reading(path="WARINESS", rung=rungs.rung_at("WARINESS", 0.92)[1], about="concept:sickness", confidence="sure")]
                + [Reading(path=p, rung=rungs.rung_at(p, 0.95)[1], about="ada", confidence="sure")
                   for p in ("DISPLEASURE", "DEFLATION", "STIRRING")], ["ada"], "sure", [])

    def no_repl(*_a):
        raise EOFError()

    saved = (direct.appraiser.read_event, direct.appraiser.read_emotion, sys.argv, builtins.input)
    direct.appraiser.read_event, direct.appraiser.read_emotion, builtins.input = refuse, emotion, no_repl
    sys.argv = ["direct.py", "--book", book, "--char", "Mira", "--model", "fake/model", "--turn-json", tj,
                "--circumstance", "Ada comes up the tower stair and says the lamp oil is gone", "--no-keeper"]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            direct.main()
    finally:
        direct.appraiser.read_event, direct.appraiser.read_emotion, sys.argv, builtins.input = saved
    return glob.glob(os.path.join(book, "runs", "*.db"))[0]


def test_chair_movers(tmp):
    print("\n[6b] the chair's three movers honour the switch")
    tables = ("wound_minted", "toward_deltas", "arc_diffs")
    on = {t: _count(_chair_seated(os.path.join(tmp, "on"), None), t) for t in tables}
    check("control-a-seated-chair-beat-mints-accrues-and-moves-the-arc", all(v > 0 for v in on.values()), on)
    off = {t: _count(_chair_seated(os.path.join(tmp, "off"), {"wounds": False, "attitude": False, "arc": False}), t)
           for t in tables}
    check("with-all-three-off-none-of-them-writes", all(v == 0 for v in off.values()), off)


def test_blueprint_names_every_system():
    print("\n[7] the authoring blueprint names every system the registry has")
    txt = open(os.path.join(REPO, "docs", "authoring", "BLUEPRINT-character.md"), encoding="utf-8").read()
    start = txt.find("# PART ZERO")
    part = txt[start:txt.find("\n# PART ", start + 5)] if start >= 0 else ""
    check("part-zero-exists", bool(part))
    missing = [k for k in systems.REGISTRY if "`%s`" % k not in part]
    check("...and-names-every-registry-system", not missing, missing)
    check("...and-shows-the-world-key", '"systems"' in part)


def main():
    print("test_systems.py — which engine systems a book runs\n")
    tmp = tempfile.mkdtemp(prefix="swe_systems_")
    try:
        test_for_book()
        test_strip()
        test_condition_off_is_silence()
        test_seated_runs(os.path.join(tmp, "seated"))
        test_lint()
        test_chair(os.path.join(tmp, "chair"))
        test_chair_movers(os.path.join(tmp, "chair-seated"))
        test_blueprint_names_every_system()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_systems: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
