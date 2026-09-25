#!/usr/bin/env python3
"""test_passage.py — one clock, read the same way by both drivers (src/engine/passage.py).

WHAT THIS PINS. `open_scene` used to be ~40 lines inline in `scripts/scene.py` (gate
driver-clock-parity, 2026-09-19) — the only driver that could reach the clock at all;
`scripts/direct.py` sat beside the same chronicle applying none of it, by its own former
comment's admission. This suite exercises the lifted function directly, on an in-memory Ledger,
with no driver in the loop: the reading is logged, the gap since the previous opening is derived
and applied (decay AND attitude erosion in minutes since gate `attitude-staircase` 2026-09-19, the
three older tiers in days), a lull's unspent remainder is owed forward to whichever opening comes
next, and an opening before the last one ended is refused.

Two characters cloned from the maren fixture (test_pipeline_e2e.py's own `_cast()` pattern, reused
rather than re-derived) — real genotype, temperament, wounds and edges, so decay/drift/wound-erode/
arc-erode/toward-erode all have something real to move, not a fixture built from what the code
merely tolerates.

Script-style like tests/test_floor.py: check(), main(), exit code. Stdlib only.
"""
import copy
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bond_rest                                   # noqa: E402
from src.engine import passage                                     # noqa: E402
from src.engine.ledger import Ledger                                # noqa: E402
from src.engine.records import RecordError                          # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _cast():
    """Two characters cloned from the maren fixture — test_pipeline_e2e.py's own `_cast()`
    pattern: real genotype, temperament, wounds (sickness@WARINESS .85 among them), and an
    authored edge to edda_elder, so every tier open_scene touches has something real to move."""
    base = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    chars = {}
    for cid, name in (("maren", "Maren"), ("edda_elder", "Edda")):
        ch = copy.deepcopy(base)
        ch["fixed"]["id"] = cid
        ch["fixed"]["name"] = name
        chars[cid] = ch
    chars["edda_elder"]["current"]["relationships"]["maren"] = {
        "trust": 0.75, "affinity": 0.6, "respect": 0.7, "debt": 0.0}
    return chars


def _ledger(chars, run_id="r1"):
    """An in-memory chronicle with both characters registered and their authored edges SEEDED
    (bond gate 4) — without seeding, every edge rests at the stranger's default and "drifts toward
    its rest" would be indistinguishable from drifting toward a stranger."""
    led = Ledger(":memory:")
    led.create_run(run_id, {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    for cid, ch in chars.items():
        led.register_character(run_id, cid, ch["fixed"], ch["baseline"])
        bond_rest.seed(led.con, run_id, 0, cid, ch["current"].get("relationships") or {})
    return led


def _in_the_room(led, turn, actor, here):
    """A committed beat: `actor` spoke and `here` were in the room (the manifest's `decay.here`) - what an opening
    reads for how long each character has been away (gate absent-age). With no beat before it, a character is at
    their first appearance and keeps the sheet's mood."""
    from src.engine.records import PATHS, TurnCommit
    led.append_turn(TurnCommit(run_id="r1", turn=turn, actor=actor, thought="-", action="-", tags={},
                               validation={"ok": True}, affect={p: 0.2 for p in PATHS},
                               manifest={"decay": {"minutes": 0.0, "here": sorted(here), "bystanders": []}}))


def test_a_declared_gap_decays_drifts_and_erodes():
    print("\n[1] A DECLARED GAP (at 420/15, opened at 440) — decay, drift toward the SEEDED rest, "
          "wound and toward erosion")
    chars = _cast()
    led = _ledger(chars)
    # a prior opening at 420, lasting 15 (budget 1: beat_minutes == lasts) — ends at 435; both were in it
    led.record_scene_clock("r1", 0, 420.0, 15.0, 15.0)
    _in_the_room(led, 0, "maren", ("maren", "edda_elder"))

    maren = chars["maren"]
    maren["current"]["affect"]["WARINESS"] = 0.60          # an excursion for decay to relax back
    before_affect = dict(maren["current"]["affect"])
    # DISPLACE the edge away from its SEEDED rest (.75/.6/.7/.0), as an earlier scene might have —
    # otherwise "drift toward the rest" and "the rest IS the current value" are indistinguishable.
    maren["current"]["relationships"]["edda_elder"] = {"trust": 0.50, "affinity": 0.6, "respect": 0.7, "debt": 0.0}
    # wounds[0] on the fixture is a "_note" placeholder (no "intensity") — find the real one by id.
    _sickness = next(w for w in maren["baseline"]["wounds"] if w.get("id") == "sickness@WARINESS")
    before_wound = float(_sickness["intensity"])                            # .85
    maren["current"].setdefault("toward", {})["edda_elder"] = {"GOODWILL": 0.30}

    result = passage.open_scene(led, "r1", 1, 440.0, None, 1, chars)

    check("elapsed-is-the-gap-since-the-priors-END", result["elapsed"] == 5.0, result)
    check("owed-is-zero-the-prior-scene-spent-its-lasts", result["owed"] == 0.0, result)
    check("relaxed-is-every-id-SORTED", result["relaxed"] == ["edda_elder", "maren"], result["relaxed"])

    rows = [tuple(r) for r in led.con.execute(
        "SELECT turn, elapsed, source FROM time_declarations WHERE run_id='r1'")]
    check("one-time_declarations-row-of-5", rows == [(1, 5.0, "")], rows)

    check("affect-decayed-BACK-toward-the-temperament-mean",
          maren["current"]["affect"]["WARINESS"] < before_affect["WARINESS"], maren["current"]["affect"])

    edge = maren["current"]["relationships"]["edda_elder"]
    check("the-displaced-edge-moved-BACK-toward-its-authored-rest", edge["trust"] > 0.50, edge)
    check("...and-has-not-OVERSHOT-the-rest", edge["trust"] <= 0.75 + 1e-9, edge)
    check("an-axis-already-AT-its-rest-does-not-move", edge["affinity"] == 0.6, edge)

    after_wound = float(_sickness["intensity"])
    check("the-untouched-wound-eroded-DOWN", after_wound < before_wound, (before_wound, after_wound))
    check("...and-stamped-_authored_intensity-ONCE",
          _sickness.get("_authored_intensity") == before_wound, _sickness)

    tv = maren["current"]["toward"]["edda_elder"]["GOODWILL"]
    check("the-toward-vector-eroded-toward-ZERO", 0.0 < tv < 0.30, tv)


def test_a_lull_owes_its_unspent_remainder():
    print("\n[2] A LULL — beats*beat_minutes < lasts, the unspent remainder is OWED and APPLIED")
    chars = _cast()
    chars["maren"]["current"]["affect"]["WARINESS"] = 0.60      # an excursion, so fifteen minutes and five differ
    led = _ledger(chars)
    # a 15-minute scene budgeted at 5 min/beat that lulled after ONE beat, with her in it: 10 unspent
    led.record_scene_clock("r1", 0, 420.0, 15.0, 5.0)
    _in_the_room(led, 0, "maren", ("maren", "edda_elder"))
    result = passage.open_scene(led, "r1", 1, 440.0, None, 1, chars)      # gap 440-435=5
    check("elapsed-is-5", result["elapsed"] == 5.0, result)
    check("owed-is-the-unspent-10", result["owed"] == 10.0, result)

    # cross-checked against a DIRECT call at elapsed+owed=15 on a fresh, identically-seeded clone —
    # proves the decay loop used elapsed PLUS owed, not elapsed alone.
    from src.engine.state import build_profile, decay
    fresh = _cast()["maren"]
    fresh["current"]["affect"]["WARINESS"] = 0.60
    profile = build_profile(fresh)
    want = decay(dict(fresh["current"]["affect"]), fresh["baseline"]["temperament"], profile, elapsed=15.0)
    alone = decay(dict(fresh["current"]["affect"]), fresh["baseline"]["temperament"], profile, elapsed=5.0)
    check("decay-used-elapsed-PLUS-owed-not-elapsed-alone",
          chars["maren"]["current"]["affect"] == want and want != alone, (chars["maren"]["current"]["affect"], want))


def test_opening_before_the_prior_end_is_refused():
    print("\n[3] BACKWARDS — an opening cannot precede the last one's END")
    chars = _cast()
    led = _ledger(chars)
    led.record_scene_clock("r1", 0, 420.0, 15.0, 15.0)          # ends at 435
    try:
        passage.open_scene(led, "r1", 1, 430.0, None, 1, chars)   # opens at 430, before 435
        check("opening-before-the-prior-end-RAISES", False, "did not raise")
    except RecordError as exc:
        check("opening-before-the-prior-end-RAISES", exc.code == "CLOCK_RUNS_BACKWARDS", exc.code)


def test_the_first_opening_of_a_run_applies_nothing():
    print("\n[4] THE FIRST OPENING — no prior row, elapsed is None, nothing is applied")
    chars = _cast()
    led = _ledger(chars)
    before = dict(chars["maren"]["current"]["affect"])
    before_edge = dict(chars["maren"]["current"]["relationships"]["edda_elder"])
    result = passage.open_scene(led, "r1", 0, 540.0, None, 1, chars)
    check("elapsed-is-None", result["elapsed"] is None, result)
    check("owed-is-zero", result["owed"] == 0.0, result)
    check("relaxed-is-EMPTY", result["relaxed"] == [], result["relaxed"])
    check("affect-is-UNTOUCHED", chars["maren"]["current"]["affect"] == before, chars["maren"]["current"]["affect"])
    check("the-edge-is-UNTOUCHED",
          chars["maren"]["current"]["relationships"]["edda_elder"] == before_edge)
    n = led.con.execute("SELECT COUNT(*) c FROM time_declarations WHERE run_id='r1'").fetchone()["c"]
    check("no-time_declarations-row", n == 0, n)
    n2 = led.con.execute("SELECT COUNT(*) c FROM scene_clock WHERE run_id='r1'").fetchone()["c"]
    check("but-the-OPENING-itself-is-still-logged", n2 == 1, n2)   # record_scene_clock runs unconditionally


def test_the_attitude_tier_is_handed_MINUTES():
    """THE UNIT, BOTH WAYS (gate `attitude-staircase`, 2026-09-19). `toward.erode` takes MINUTES
    now — it steps the same per-rung staircase the mood tier does, and a staircase cannot be
    stepped on two clocks. The three older tiers still get the day conversion.

    Asserted as a SPY and as an EFFECT, because either alone is weak: the spy proves which number
    crossed the call, and the effect proves the number means what the staircase's bottom rung says
    it means. A 1440-minute gap on a bottom-rung attitude toward a STRANGER (connection 0, so no
    slowing) must land exactly on the old flat one-day result."""
    print("\n[5] THE ATTITUDE TIER READS THE DECLARATION IN MINUTES, the older three in days")
    from src.engine import toward
    from src.engine.decay_law import relax

    chars = _cast()
    led = _ledger(chars)
    led.record_scene_clock("r1", 0, 420.0, 15.0, 15.0)                  # ends at 435
    # a stranger: `connection.for_target` is 0.0 with no edge, so nothing slows the decay
    start = 0.05                                                        # inside GOODWILL's rung 1
    for ch in chars.values():
        ch["current"].setdefault("toward", {})["a_stranger"] = {"GOODWILL": start}

    seen = []
    real = toward.erode
    toward.erode = lambda c, m, conns=None: (seen.append(m), real(c, m, conns))[1]
    try:
        result = passage.open_scene(led, "r1", 1, 435.0 + 1440.0, None, 1, chars)
    finally:
        toward.erode = real

    check("the-gap-is-1440-minutes", result["elapsed"] == 1440.0, result)
    check("erode-was-handed-the-MINUTES-not-the-days", seen == [1440.0, 1440.0], seen)
    got = chars["maren"]["current"]["toward"]["a_stranger"]["GOODWILL"]
    want = relax(start, 0.0, toward._RETENTION["GOODWILL"], 1.0)
    check("...and-a-bottom-rung-attitude-over-that-day-is-the-old-flat-result",
          abs(got - want) < 1e-9, (got, want))


def test_restore_latest_puts_mood_and_condition_on_the_sheet():
    """gate resume-and-parity (2026-09-22): both drivers kept only the mood from latest_affect, and the
    chair kept it only in a local that open_scene then overwrote with the sheet's decayed mood."""
    ch = {"current": {"affect": {"WARINESS": 0.1}, "condition": {"energy": 0.9}}}
    latest = {"affect": {"WARINESS": 0.6}, "condition": {"energy": 0.4, "allostatic_load": 0.3}}
    passage.restore_latest(ch, latest)
    check("mood-restored-onto-the-sheet", ch["current"]["affect"] == {"WARINESS": 0.6}, ch)
    check("condition-restored-onto-the-sheet", ch["current"]["condition"] == {"energy": 0.4, "allostatic_load": 0.3}, ch)
    latest["affect"]["WARINESS"] = 0.99
    check("the-restore-is-a-copy", ch["current"]["affect"]["WARINESS"] == 0.6, ch)
    untouched = {"current": {"affect": {"WARINESS": 0.1}, "condition": {"energy": 0.9}}}
    passage.restore_latest(untouched, None)
    check("no-committed-beat-leaves-the-sheet-as-authored", untouched["current"]["affect"] == {"WARINESS": 0.1})
    passage.restore_latest(untouched, {"affect": {"WARINESS": 0.2}, "condition": {}})
    check("an-empty-stored-condition-does-not-erase-the-sheets", untouched["current"]["condition"] == {"energy": 0.9})


# ---------------------------------------------------------------------------------------------------
# THE FADE, DERIVED AT REPLAY (gate erosion-derived-at-replay, 2026-09-22). `open_scene` fades
# attitude, wounds and resting means in memory and logs only the declaration; the three folds must
# rebuild the same values from the log, and a beat refolded after an opening must keep its fade.
# ---------------------------------------------------------------------------------------------------
_GAP = 3 * 1440.0          # three days: every tier's fade is large enough to see


def _stamped_cast():
    chars = _cast()
    chars["maren"]["current"]["toward"] = {"edda_elder": {"GOODWILL": 0.30}}   # an AUTHORED attitude
    for ch in chars.values():
        passage.stamp_authored(ch)                                          # at load, as both drivers do
    return chars


def _mint_row(led, turn, concept, path, intensity):
    from src.engine import wound
    m = wound.make(concept, path, intensity, "run:%d" % turn, text="a beat")
    led.con.execute("INSERT INTO wound_minted(run_id, turn, char_id, wound_id, concept, path, intensity, source, "
                    "text, triggers) VALUES ('r1', ?, 'maren', ?, ?, ?, ?, ?, ?, ?)",
                    (turn, m["id"], m["concept"], m["path"], m["intensity"], m["source"], m["text"],
                     json.dumps(m["trigger"])))
    led.con.commit()
    return m["id"]


def _log_beat(led, turn, toward_rows, wound_rows, arc_diff=None, trust=None):
    for tgt, prim, d in toward_rows:
        led.con.execute("INSERT INTO toward_deltas(run_id, turn, perceiver, target, primary_, delta) "
                        "VALUES ('r1', ?, 'maren', ?, ?, ?)", (turn, tgt, prim, d))
    for wid, d in wound_rows:
        led.con.execute("INSERT INTO wound_deltas(run_id, char_id, turn, wound_id, delta, kind) "
                        "VALUES ('r1', 'maren', ?, ?, ?, 'event')", (turn, wid, d))
    if arc_diff:
        led.con.execute("INSERT INTO arc_diffs(run_id, char_id, turn, diff) VALUES ('r1', 'maren', ?, ?)",
                        (turn, json.dumps(arc_diff)))
    if trust is not None:
        led.con.execute("INSERT INTO relationship_deltas(run_id, turn, perceiver, target, axis, delta, ord) "
                        "VALUES ('r1', ?, 'maren', 'edda_elder', 'trust', ?, 'first')", (turn, trust))
    led.con.commit()


def _old_restorers(led, ch):
    """What both drivers ran before this gate: the arc loop, toward.replay, wound.fold."""
    from src.engine import arc, toward, wound
    for diff in led.arc_diffs_for("r1", "maren"):
        ch = arc.apply(ch, diff)
    toward.replay(ch, led.toward_deltas_for("r1", "maren"))
    wound.fold(ch, wound.mints_for(led.con, "r1", "maren"), led.wound_deltas_for("r1", "maren"))
    return ch


def _folds(led, ch):
    ch = passage.fold_arc(led.con, "r1", "maren", ch)
    passage.fold_toward(led.con, "r1", "maren", ch)
    passage.fold_wounds(led.con, "r1", "maren", ch)
    return ch


def _turn0(led):
    """One beat at turn 0: attitude, a wound trial, a mint, an arc diff and an edge movement."""
    _log_beat(led, 0, [("edda_elder", "GOODWILL", 0.20), ("edda_elder", "WARINESS", 0.15),
                       ("a_stranger", "DISTASTE", 0.25)],
              [("sickness@WARINESS", 0.05)], arc_diff={"temperament": {"WARINESS": 0.05}}, trust=-0.10)   # still above the connection floor
    return _mint_row(led, 0, "betrayal", "DISPLEASURE", 0.6)


def _gap(a, b):
    """Largest absolute difference between two {who: {path: v}} / {id: v} / {path: v} maps; inf on a key mismatch."""
    if set(a) != set(b):
        return float("inf")
    out = 0.0
    for k in a:
        if isinstance(a[k], dict) or isinstance(b[k], dict):
            out = max(out, _gap(a[k] or {}, b[k] or {}))
        else:
            out = max(out, abs(float(a[k]) - float(b[k])))
    return out


def _intensities(ch):
    return {w["id"]: w["intensity"] for w in ch["baseline"]["wounds"] if isinstance(w, dict) and "intensity" in w}


def _means(ch):
    return {p: r["mean"] for p, r in ch["baseline"]["temperament"].items() if isinstance(r, dict) and "mean" in r}


def test_with_no_declaration_the_folds_are_the_old_restorers():
    print("\n[7] NO DECLARATION - each fold equals the restorer it replaces, EXACTLY")
    chars = _stamped_cast()
    led = _ledger(chars)
    _turn0(led)
    _log_beat(led, 1, [("edda_elder", "GOODWILL", 0.05)], [("sickness@WARINESS", -0.02)],
              arc_diff={"temperament": {"GOODWILL": -0.04}})
    _mint_row(led, 1, "abandonment", "DEFLATION", 0.5)
    old = _old_restorers(led, _stamped_cast()["maren"])
    new = _folds(led, _stamped_cast()["maren"])
    check("attitude-identical", new["current"]["toward"] == old["current"]["toward"],
          (new["current"]["toward"], old["current"]["toward"]))
    check("wounds-identical-including-each-authored-stamp", new["baseline"]["wounds"] == old["baseline"]["wounds"],
          (new["baseline"]["wounds"], old["baseline"]["wounds"]))
    check("temperament-identical", new["baseline"]["temperament"] == old["baseline"]["temperament"])
    check("...and-the-log-moved-something-so-the-equality-is-not-vacuous",
          old["current"]["toward"]["edda_elder"].get("GOODWILL") == 0.55 and "abandonment@DEFLATION" in _intensities(old),
          old["current"]["toward"])


def _opened():
    """A turn-0 beat, then an opening at turn 1 after three days: -> (led, the live maren after it,
    the live maren just before it)."""
    chars = _stamped_cast()
    led = _ledger(chars)
    _turn0(led)
    maren = _old_restorers(led, chars["maren"])       # exact before any declaration (test [7])
    bond_rest.rehydrate(maren["current"]["relationships"], maren["baseline"].get("relationship_priors", {}),
                        led.timeline_for("r1", "maren"), attachments=maren["current"].setdefault("attachments", {}))
    chars["maren"] = maren
    before = copy.deepcopy(maren)
    led.record_scene_clock("r1", 0, 420.0, 15.0, 15.0)                            # ends at 435
    passage.open_scene(led, "r1", 1, 435.0 + _GAP, None, 1, chars)
    return led, chars["maren"], before


def test_the_folds_reproduce_what_the_opening_faded():
    print("\n[8] AN OPENING'S FADE - the folds over the log reproduce the live opening to 1e-12")
    led, live, before = _opened()
    check("the-opening-faded-the-attitude", _gap(live["current"]["toward"], before["current"]["toward"]) > 1e-3)
    check("...the-wounds-incl-the-mint", _intensities(live)["betrayal@DISPLEASURE"] < 0.6
          and _intensities(live)["sickness@WARINESS"] < _intensities(before)["sickness@WARINESS"], _intensities(live))
    check("...and-the-moved-resting-mean", live["baseline"]["temperament"]["WARINESS"]["mean"]
          < before["baseline"]["temperament"]["WARINESS"]["mean"])
    rebuilt = _folds(led, _stamped_cast()["maren"])
    for name, a, b in (("attitude", rebuilt["current"]["toward"], live["current"]["toward"]),
                       ("wound-intensities", _intensities(rebuilt), _intensities(live)),
                       ("resting-means", _means(rebuilt), _means(live))):
        check("the-fold-reproduces-the-%s" % name, _gap(a, b) < 1e-12, (_gap(a, b), a, b))
    old = _old_restorers(led, _stamped_cast()["maren"])
    check("...where-the-old-restorers-lost-the-fade", _gap(old["current"]["toward"], live["current"]["toward"]) > 1e-3
          and _gap(_intensities(old), _intensities(live)) > 1e-6 and _gap(_means(old), _means(live)) > 1e-6)
    unstamped = _cast()["maren"]
    unstamped["current"]["toward"] = {"edda_elder": {"GOODWILL": 0.30}}
    try:
        passage.fold_toward(led.con, "r1", "maren", unstamped)
        check("an-unstamped-sheet-is-refused-at-a-declared-gap", False, "did not raise")
    except RecordError as exc:
        check("an-unstamped-sheet-is-refused-at-a-declared-gap", exc.code == "PASSAGE_FOLD_UNSTAMPED", exc.code)


def test_a_beat_refolded_after_the_opening_keeps_the_fade():
    print("\n[9] THE MID-SCENE REFOLD - the scene's first beat keeps its own opening's fade")
    from src.engine import toward
    led, live, _before = _opened()
    faded = copy.deepcopy(live)
    # the beat also moves the edge: the opening read the bonds BEFORE it, so the refold must too
    _log_beat(led, 1, [("edda_elder", "GOODWILL", 0.05)], [("sickness@WARINESS", -0.02)], trust=0.10)
    new_wid = _mint_row(led, 1, "abandonment", "DEFLATION", 0.5)
    erased = toward.replay(copy.deepcopy(live), led.toward_deltas_for("r1", "maren"))
    passage.fold_toward(led.con, "r1", "maren", live)                 # what the driver runs after the commit
    passage.fold_wounds(led.con, "r1", "maren", live)
    want = faded["current"]["toward"]["edda_elder"]["GOODWILL"] + 0.05
    got = live["current"]["toward"]["edda_elder"]["GOODWILL"]
    check("the-delta-lands-on-the-FADED-value", abs(got - want) < 1e-12, (got, want))
    check("...where-the-old-refold-put-it-back-on-the-authored-value",
          abs(erased["edda_elder"]["GOODWILL"] - 0.55) < 1e-12 and abs(got - 0.55) > 1e-3, (erased, got))
    check("a-person-with-no-new-delta-keeps-the-fade",
          live["current"]["toward"]["a_stranger"] == faded["current"]["toward"]["a_stranger"])
    want_w = _intensities(faded)["sickness@WARINESS"] - 0.02
    check("the-wound-delta-lands-on-the-ERODED-intensity",
          abs(_intensities(live)["sickness@WARINESS"] - want_w) < 1e-12, (_intensities(live), want_w))
    check("a-wound-minted-in-the-opening-turn-joins-AFTER-its-fade",
          _intensities(live)[new_wid] == 0.5 and next(w for w in live["baseline"]["wounds"]
                                                      if w.get("id") == new_wid)["_authored_intensity"] == 0.5)
    again = copy.deepcopy(live)
    passage.fold_toward(led.con, "r1", "maren", again)
    passage.fold_wounds(led.con, "r1", "maren", again)
    check("the-refold-is-idempotent", again["current"]["toward"] == live["current"]["toward"]
          and again["baseline"]["wounds"] == live["baseline"]["wounds"])


def test_a_declared_day_replays_as_one_day_of_bond_drift():
    print("\n[10] THE BOND TIMELINE'S UNIT - a declared 1,440 minutes replays as ONE day of drift")
    chars = _stamped_cast()
    led = _ledger(chars)
    _log_beat(led, 0, [], [], trust=-0.25)                            # displaced from its rest
    maren = chars["maren"]
    rels = maren["current"]["relationships"]
    bond_rest.rehydrate(rels, maren["baseline"].get("relationship_priors", {}), led.timeline_for("r1", "maren"),
                        attachments=maren["current"].setdefault("attachments", {}))
    led.record_scene_clock("r1", 0, 420.0, 15.0, 15.0)
    passage.open_scene(led, "r1", 1, 435.0 + 1440.0, None, 1, chars)
    live = rels["edda_elder"]["trust"]
    replay = copy.deepcopy(maren["current"]["_authored_relationships"])
    items = led.timeline_for("r1", "maren")
    bond_rest.rehydrate(replay, maren["baseline"].get("relationship_priors", {}), items, attachments={})
    check("the-live-opening-drifted-the-displaced-edge", 0.50 < live < 0.75, live)
    check("the-replayed-edge-equals-the-live-drift", abs(replay["edda_elder"]["trust"] - live) < 1e-12,
          (replay["edda_elder"]["trust"], live))
    check("the-timeline's-time-item-is-ONE-day", ("time", 1.0) in items, items)
    as_minutes = [("time", 1440.0) if it[0] == "time" else it for it in items]
    wrong = copy.deepcopy(maren["current"]["_authored_relationships"])
    bond_rest.rehydrate(wrong, maren["baseline"].get("relationship_priors", {}), as_minutes, attachments={})
    check("...where-minutes-read-as-days-overshoot-to-the-rest", abs(wrong["edda_elder"]["trust"] - live) > 1e-2,
          (wrong["edda_elder"]["trust"], live))


def test_the_room_decays_on_each_bystanders_own_binds():
    """gate non-speaker-decay (2026-09-22): step 4 of the beat - every OTHER present character decays over
    the beat's minutes, decay only, on THEIR OWN binds against the room."""
    print("\n[11] STEP 4 - every other present character decays, on their own binds")
    from src.engine.state import build_profile, decay
    chars = _cast()
    third = copy.deepcopy(chars["maren"])
    third["fixed"]["id"] = "joss"
    chars["joss"] = third
    room = {}
    for cid, ch in chars.items():
        aff = dict(ch["current"]["affect"], WARINESS=0.80)
        room[cid] = {"affect": aff, "temperament": ch["baseline"]["temperament"], "profile": build_profile(ch),
                     "targets": {}}
    room["edda_elder"]["targets"] = {"WARINESS": "maren"}            # her fear is ABOUT someone in the room
    here = {"maren", "edda_elder", "joss"}
    before = copy.deepcopy(room)
    got = passage.bystanders(room, "maren", 30.0, here)
    check("the-speaker-is-not-a-bystander", sorted(got) == ["edda_elder", "joss"], sorted(got))
    for cid in got:
        want = decay(dict(before[cid]["affect"]), before[cid]["temperament"], before[cid]["profile"], elapsed=30.0,
                     targets=dict(before[cid]["targets"]), present=set(here))
        check("%s-is-state.decay-on-their-own-binds" % cid, got[cid] == want, (got[cid], want))
    check("a-fear-whose-object-is-present-fades-slower",
          got["edda_elder"]["WARINESS"] > got["joss"]["WARINESS"], (got["edda_elder"]["WARINESS"], got["joss"]["WARINESS"]))
    check("the-room-is-not-mutated", room == before)
    still = passage.bystanders(room, "maren", 0.0, here)
    check("no-minutes-no-change", all(still[c] == room[c]["affect"] for c in still), still)


def test_the_bounds_read_the_log_as_it_stood():
    """gate mood-from-readings (2026-09-22): the mood replay rebuilds each resume from the log AS IT STOOD,
    so the folds, the bond timeline and the binds reader take a bound. Past the log it changes nothing;
    at a turn it equals the unbounded fold over a log that stops there."""
    print("\n[12] BOUNDS - past the log they change nothing; at a turn they read the log as it stood")
    from src.engine.records import RestDeclared
    led, _live, _before = _opened()                                   # a turn-0 beat, then an opening at turn 1
    _log_beat(led, 1, [("edda_elder", "GOODWILL", 0.05)], [("sickness@WARINESS", -0.02)],
              arc_diff={"temperament": {"GOODWILL": -0.04}}, trust=0.10)
    far = 10 ** 6
    for name, fold in (("toward", passage.fold_toward), ("wounds", passage.fold_wounds)):
        a, b = _stamped_cast()["maren"], _stamped_cast()["maren"]
        check("%s-bounded-past-the-log-is-unbounded" % name,
              fold(led.con, "r1", "maren", a) == fold(led.con, "r1", "maren", b, before_turn=far))
    check("arc-bounded-past-the-log-is-unbounded",
          passage.fold_arc(led.con, "r1", "maren", _stamped_cast()["maren"])["baseline"]["temperament"]
          == passage.fold_arc(led.con, "r1", "maren", _stamped_cast()["maren"], before_turn=far)["baseline"]["temperament"])
    check("timeline-bounded-past-the-log-is-unbounded",
          bond_rest.timeline_rows(led.con, "r1", "maren") == bond_rest.timeline_rows(led.con, "r1", "maren", before=(far, 0)))
    chars0 = _stamped_cast()
    led0 = _ledger(chars0)                                            # the same log, stopped before turn 1
    _turn0(led0)
    for name, fold in (("toward", passage.fold_toward), ("wounds", passage.fold_wounds)):
        a, b = _stamped_cast()["maren"], _stamped_cast()["maren"]
        check("%s-bounded-at-turn-1-is-the-log-before-it" % name,
              fold(led.con, "r1", "maren", a, before_turn=1) == fold(led0.con, "r1", "maren", b))
    check("arc-bounded-at-turn-1-is-the-log-before-it",
          passage.fold_arc(led.con, "r1", "maren", _stamped_cast()["maren"], before_turn=1)["baseline"]["temperament"]
          == passage.fold_arc(led0.con, "r1", "maren", _stamped_cast()["maren"])["baseline"]["temperament"])
    bond_rest.write(led.con, "r1", 1, [RestDeclared(perceiver="maren", target="edda_elder", axis="trust", rest=0.4, source="cliff"),
                                        RestDeclared(perceiver="maren", target="edda_elder", axis="affinity", rest=0.5, source="authored")])
    led.con.commit()
    at1 = [it for t, k, it in bond_rest.timeline_rows(led.con, "r1", "maren", seeded_at=1) if t == 1 and k == 0]
    check("seeded_at-keeps-the-resumes-seed-and-drops-the-beats-cliff",
          at1 == [("rest", "edda_elder", "affinity", 0.5)], at1)
    # THE DIRECTOR'S HOLDS are written at the scene's first turn BEFORE its people are built (scripts/scene.py
    # run_scene), so they are part of the log that scene opened on; a keeper's hold at that turn came after
    # its beat. The replay dropped the director's too until gate systems-registry (2026-09-22).
    from src.engine import attachments as _att
    from src.engine.records import AttachmentDeclared
    _att.declare(led.con, "r1", 1, [AttachmentDeclared("maren", "loc.healers_house", 0.6, source="director"),
                                    AttachmentDeclared("maren", "loc.mill", 0.3, source="keeper")])
    holds1 = [it for t, k, it in bond_rest.timeline_rows(led.con, "r1", "maren", seeded_at=1) if t == 1 and k == 1]
    check("seeded_at-keeps-the-directors-hold-and-drops-the-keepers",
          holds1 == [("hold", "loc.healers_house", 0.6, "+")], holds1)


def test_a_first_beat_cliff_replays_after_its_openings_drift():
    """GATE cliff-after-drift (2026-09-23). A scene opens at turn 5 after ten days; its FIRST beat breaks trust
    (-.40) and the cliff lowers the rest to .15 - both rows land at turn 5, beside the opening's time
    declaration. Live, the drift ran at the opening toward the OLD rest (.80: no move), then the beat. The
    timeline sorted every rest row first, so the replay drifted ten days toward .15 before the beat. A rest the
    sheet or the director laid down at the same turn still takes effect before the drift."""
    from src.engine.records import RestDeclared
    print("\n[cliff] a first-beat cliff replays after its scene's drift")
    led = Ledger(":memory:")
    led.create_run("r1", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    authored = {"edda_elder": {"trust": 0.80, "affinity": 0.5, "respect": 0.5, "debt": 0.0}}
    with led.con:
        bond_rest.write(led.con, "r1", 0, bond_rest.seed_rows("maren", authored, existing=[]))
    led.declare_time("r1", 5, 10 * 1440.0, "ten days")                 # the second scene's opening
    with led.con:
        led.con.execute("INSERT INTO relationship_deltas(run_id, turn, perceiver, target, axis, delta, ord) "
                        "VALUES ('r1', 5, 'maren', 'edda_elder', 'trust', -0.40, 'first')")
        bond_rest.write(led.con, "r1", 5, [RestDeclared("maren", "edda_elder", "trust", 0.15, "cliff")])
    rels = copy.deepcopy(authored)
    bond_rest.rehydrate(rels, {}, led.timeline_for("r1", "maren"))
    check("the-edge-drifts-toward-the-rest-it-had-at-the-opening-then-takes-the-beat",
          abs(rels["edda_elder"]["trust"] - 0.40) < 1e-9, rels["edda_elder"])
    order = [(t, s, it[0]) for t, s, it in bond_rest.timeline_rows(led.con, "r1", "maren") if t == 5]
    check("...the-turn-reads-drift-then-the-beat's-own-rows", [k for _t, _s, k in order] == ["time", "rest", "edge"], order)
    # a hold the DIRECTOR declares at scene start is laid down before the opening; one a KEEPER writes comes after
    from src.engine import attachments
    from src.engine.records import AttachmentDeclared
    with led.con:
        attachments.write(led.con, "r1", 5, [AttachmentDeclared("maren", "loc.the-ferry", 0.6, "+", "director"),
                                             AttachmentDeclared("maren", "loc.the-mill", 0.4, "+", "keeper")])
    order = ["%s:%s" % (it[0], it[1] if it[0] == "hold" else "") for t, _s, it in bond_rest.timeline_rows(led.con, "r1", "maren") if t == 5]
    check("...a-director's-hold-comes-before-the-drift-and-a-keeper's-after",
          order.index("hold:loc.the-ferry") < order.index("time:") < order.index("hold:loc.the-mill"), order)
    # THE OPENING'S VIEW: the bonds as they stood at turn 5's opening exclude the beat's cliff (passage.fold_toward)
    before = [it for t, s, it in bond_rest.timeline_rows(led.con, "r1", "maren", before=(5, 3)) if t == 5]
    check("the-bonds-at-the-opening-hold-no-cliff-the-beat-had-not-yet-made",
          not any(it[0] == "rest" and it[2] == "trust" for it in before), before)


def main():
    print("test_passage.py — one clock, read the same way by both drivers\n")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print("\n%s" % ("test_passage: OK (scripts/scene.py and scripts/direct.py now read the same clock)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
