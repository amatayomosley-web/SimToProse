"""test_reserves.py — one shared pool, with a reserve for the mind and one for the body (gate energy-reserves).

WHAT THIS PINS (2026-09-22). The owner: "mental energy and physical are separate but also come from the same
source. Something like a shared pool but with reserves for each. A person can never use all energy for one type
of activity." He confirmed the shape: a shared pool plus a mind reserve and a body reserve (a fifth of a full
tank each); thinking and feeling draw the shared pool then the mind's reserve, never the body's; physical effort
the shared pool then the body's reserve, never the mind's; waking time the shared pool; rest refills all three;
memory reads the mind's side; the actor's line reads both and says so when they differ; only books running the
body system have the reserves.

  [1] the split: the reserves are the last energy to go, and `energy` stays the sum;
  [2] the draws: no kind of activity ever touches the other's reserve - the porter and the clerk;
  [3] rest: every store refills, and the TOTAL rests exactly as the single pool did;
  [4] the readers: memory reads the mind's side; the actor's line is unchanged when the sides agree and says
      both when they differ; a condition without reserves reads exactly as before;
  [5] a scene's stated arrival re-splits the reserves;
  [6] through scripts/scene.py main with the body on: every committed condition carries the reserves, the
      hauling empties the body's side before the mind's, the replay re-derives every row; with the body off
      no reserve ever appears.

Script-style; exit 0 = all pass.
"""
import json
import math
import os
import shutil
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import bible, condition as C, direction as D, gate as G, mood_fold   # noqa: E402
import test_body as TB                                                                 # noqa: E402  (its seated run)

FAILS = []
R = C.RESERVE


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def near(a, b):
    return abs(a - b) < 1e-12


def fresh(load=0.0):
    return C.split({"energy": 1.0, "allostatic_load": load})


def test_split():
    print("\n[1] the split")
    f = fresh()
    check("a-fresh-character-has-both-reserves-full", f["mind_reserve"] == R == f["body_reserve"] and f["energy"] == 1.0, f)
    low = C.split({"energy": 0.3, "allostatic_load": 0.1})
    check("a-worn-one-has-half-of-what-is-left-in-each", near(low["mind_reserve"], 0.15) and near(low["body_reserve"], 0.15)
          and low["energy"] == 0.3, low)
    check("splitting-twice-changes-nothing", C.split(f) == f)
    check("...and-a-condition-without-reserves-is-not-split-by-anything-else", not C.has_reserves({"energy": 0.5, "allostatic_load": 0.1}))


def test_draws():
    print("\n[2] the draws - no kind of activity touches the other's reserve")
    porter = C.draw(C.draw(fresh(), 0.6, "awake"), 5.0, "body")          # a long day, then hauling past the limit
    check("the-porter-hauls-his-body-side-empty", porter["body_reserve"] == 0.0 and C.body_view(porter) == 0.0, porter)
    check("...and-his-mind-keeps-its-reserve", near(porter["mind_reserve"], R) and near(C.mind_view(porter), R / (1 - R)), porter)
    clerk = C.draw(fresh(), 5.0, "mind")
    check("the-clerk-argues-her-mind-side-empty", clerk["mind_reserve"] == 0.0 and C.mind_view(clerk) == 0.0, clerk)
    check("...and-her-body-keeps-its-reserve", near(clerk["body_reserve"], R), clerk)
    part = C.draw(fresh(), 0.3, "body")
    check("the-shared-pool-pays-first", near(part["mind_reserve"], R) and near(part["body_reserve"], R) and near(part["energy"], 0.7), part)
    awake = C.draw(fresh(), 1.0 - 2 * R + 0.1, "awake")
    check("waking-time-past-the-shared-pool-draws-both-reserves-evenly",
          near(awake["mind_reserve"], R - 0.05) and near(awake["body_reserve"], R - 0.05), awake)
    lopsided = C.draw(dict(clerk), 0.3, "awake")                         # her mind reserve is gone: the body's pays it all
    check("...each-giving-what-it-has", lopsided["mind_reserve"] == 0.0 and lopsided["body_reserve"] == 0.0 and lopsided["energy"] == 0.0,
          lopsided)
    for c in (porter, clerk, part, awake, lopsided):
        s = c["energy"] - c["mind_reserve"] - c["body_reserve"]
        if s < -1e-12 or c["mind_reserve"] < 0 or c["body_reserve"] < 0:
            check("no-store-ever-goes-below-empty", False, c)
            break
    else:
        check("no-store-ever-goes-below-empty", True)


def test_rest():
    print("\n[3] rest")
    worn = C.draw(C.draw(fresh(0.3), 0.7, "body"), 0.2, "mind")
    rested = C.opening(worn, 480.0, 0.0, {})
    k = math.exp(-480.0 / C.REST_TAU)
    check("the-total-rests-exactly-as-the-single-pool-did", near(rested["energy"], 1 - (1 - worn["energy"]) * k), (rested, worn))
    check("...and-each-reserve-refills-toward-full", near(rested["body_reserve"], R - (R - worn["body_reserve"]) * k)
          and near(rested["mind_reserve"], R - (R - worn["mind_reserve"]) * k), rested)
    check("a-long-rest-refills-everything", all(near(v, t) for v, t in ((C.opening(worn, 1e6, 0.0, {})["energy"], 1.0),)))


def test_readers():
    print("\n[4] the readers")
    porter = C.draw(C.draw(fresh(), 0.6, "awake"), 5.0, "body")
    clerk = C.draw(fresh(), 5.0, "mind")
    check("memory-reads-the-mind-side-the-porter-still-recalls", near(G._energy_budget(porter), R / (1 - R)), G._energy_budget(porter))
    check("...and-the-clerk-does-not", G._energy_budget(clerk) == 0.0)
    bands = [p for _e, p in D._COND]
    body_bands = [p for _e, p in D._BODY_COND]
    line = D.direct_condition(porter)
    check("sides-that-differ-are-both-said", line.startswith(bands[1]) and line.endswith(body_bands[0]), line)
    same = fresh()
    check("sides-that-agree-say-the-one-sentence-as-before", D.direct_condition(same) == bands[3], D.direct_condition(same))
    plain = {"energy": 0.8, "allostatic_load": 0.2}
    check("a-condition-without-reserves-reads-exactly-as-before",
          D.direct_condition(plain) == bands[2] and near(G._energy_budget(plain), 0.8 * (1 - 0.2 * 0.5)))
    check("the-actor-is-never-given-a-number", not any(ch.isdigit() for ch in D.direct_condition(porter) + D.direct_condition(clerk)))


def test_arrival():
    print("\n[5] a scene's stated arrival re-splits the reserves")
    chars = {"mira": {"current": {"condition": fresh()}}}
    C.apply_declared(chars, [{"char": "mira", "energy": "spent"}])
    c = chars["mira"]["current"]["condition"]
    check("spent-whole-with-the-reserves-last-to-go", c["energy"] == C.ENERGY_WORDS["spent"]
          and near(c["mind_reserve"], C.ENERGY_WORDS["spent"] / 2) and near(c["body_reserve"], C.ENERGY_WORDS["spent"] / 2), c)


def test_through_the_driver(tmp):
    print("\n[6] through scripts/scene.py main")
    db, run_id, _asked, outs = TB._run(os.path.join(tmp, "body"), TB.BODY, {"Mira": "powerful", "Ada": "frail"})
    rows = [(int(t), cid, json.loads(c)) for t, cid, c in sqlite3.connect(db).execute(
        "SELECT turn, char_id, condition FROM current_state ORDER BY turn")]
    check("every-committed-condition-carries-both-reserves", rows and all(C.has_reserves(c) for _t, _c, c in rows), rows[:1])
    # THE FIRST SCENE ONLY: its hauling is the claim. The daytime gap after it is hours awake (gate gap-day-and-night),
    # which, once the shared pool is gone, wears BOTH reserves - a different rule, tested in test_condition.
    second = sqlite3.connect(db).execute("SELECT MIN(start_turn) FROM scenes WHERE start_turn > 0").fetchone()[0]
    ada = [c for t, cid, c in rows if cid == "ada" and t < second]
    check("the-frail-hauler-s-body-side-empties-before-her-mind-side",
          ada and ada[-1]["body_reserve"] < ada[-1]["mind_reserve"] and C.body_view(ada[-1]) < C.mind_view(ada[-1]), ada[-1:])
    check("...and-in-that-scene-the-hauling-never-emptied-her-mind-reserve",
          all(c["mind_reserve"] > 0 for c in ada), [c["mind_reserve"] for c in ada])
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    d = mood_fold.divergence(con, run_id, bible.for_run(con, run_id)[2])
    check("the-replay-re-derives-every-store-of-every-row", d["condition_at"] is None and d["at"] is None and not d["notes"], d)
    ref, _r, _a, _o = TB._run(os.path.join(tmp, "flow"), TB.FLOW, {"Mira": "powerful", "Ada": "frail"})
    flow_rows = [json.loads(c) for (c,) in sqlite3.connect(ref).execute("SELECT condition FROM current_state")]
    check("with-the-body-off-no-reserve-ever-appears", flow_rows and not any(C.has_reserves(c) for c in flow_rows), flow_rows[:1])
    chair = TB._chair(os.path.join(tmp, "chair"), TB.BODY, True)
    row = json.loads(sqlite3.connect(chair).execute("SELECT condition FROM current_state WHERE char_id = 'mira'").fetchone()[0])
    # one beat's hauling is paid from the shared pool, so both reserves are still full - this checks the SPLIT
    check("the-chair-splits-too", C.has_reserves(row) and near(row["mind_reserve"], R) and near(row["body_reserve"], R), row)


def main():
    print("test_reserves.py — one shared pool, with a reserve for the mind and one for the body\n")
    tmp = tempfile.mkdtemp(prefix="swe_reserves_")
    try:
        test_split()
        test_draws()
        test_rest()
        test_readers()
        test_arrival()
        test_through_the_driver(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_reserves: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
