#!/usr/bin/env python3
"""test_memory_decay.py — Track 3: Memory Decay & Temporal Forgetting Curves.

Proves:
  1. Core identity beliefs never decay over time (Law 1).
  2. Transient beliefs decay toward floor (0.05) as delta_t increases.
  3. Durable beliefs decay slowly toward a high permanence floor (0.35).
  4. Decayed transient beliefs naturally slip from active recall as retrieval cost rises.
  5. Recalling a belief resets delta_t and restores accessibility; spaced repetition flattens decay.
  6. Live relationship connection scales retention (Finding 4).
  7. Decayed memories pass confidence_eff to prompt sureness in words (Finding 6).
  8. Recall history is derived pure from chronicle decision_manifests (Finding 1).
Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import decay
from src.engine.gate import run_gate
from src.engine.direction import sureness
from src.engine.scene import _recall_for_packet

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name + (("  -- " + detail) if (detail and not cond) else ""))


def test_core_belief_invariance():
    print("\n[1] Core Identity Invariance (Zero Decay)")
    b_core = {
        "claim": "I am Kael, sworn tracker of the western border",
        "confidence": 0.95,
        "provenance": "core",
        "durability": "core",
        "created_turn": 1,
    }
    c_0 = decay.calculate_effective_confidence(b_core, current_turn=1)
    c_50 = decay.calculate_effective_confidence(b_core, current_turn=50)
    c_500 = decay.calculate_effective_confidence(b_core, current_turn=500)

    check("turn-0-confidence-exact", c_0 == 0.95)
    check("turn-50-confidence-preserved", c_50 == 0.95)
    check("turn-500-confidence-preserved", c_500 == 0.95)


def test_transient_vs_durable_decay():
    print("\n[2] Transient vs Durable Forgetting Curves")
    b_transient = {
        "claim": "Saw a stray gray mule near the stables this morning",
        "confidence": 0.85,
        "durability": "transient",
        "created_turn": 10,
        "last_recalled_turn": 10,
    }
    b_durable = {
        "claim": "I lost the county spelling bee on the word rhythm",
        "confidence": 0.95,
        "durability": "durable",
        "created_turn": 10,
        "last_recalled_turn": 10,
    }

    # At turn 10 (delta_t = 0)
    check("transient-initial-full", decay.calculate_effective_confidence(b_transient, 10) == 0.85)
    check("durable-initial-full", decay.calculate_effective_confidence(b_durable, 10) == 0.95)

    # At turn 25 (delta_t = 15)
    t_15 = decay.calculate_effective_confidence(b_transient, 25)
    d_15 = decay.calculate_effective_confidence(b_durable, 25)
    check("transient-fades-substantially", t_15 < 0.20, f"actual: {t_15}")
    check("durable-remains-strong", d_15 > 0.60, f"actual: {d_15}")

    # At turn 80 (delta_t = 70)
    t_70 = decay.calculate_effective_confidence(b_transient, 80)
    check("transient-hits-floor", abs(t_70 - decay.FLOOR_TRANSIENT) < 0.01, f"actual: {t_70}")
    d_160 = decay.calculate_effective_confidence(b_durable, 160)
    check("durable-levels-at-permanence-floor", abs(d_160 - decay.FLOOR_DURABLE) < 0.01, f"actual: {d_160}")


def test_gate_retrieval_under_decay():
    print("\n[3] Gate Coupling: Decayed memory slips from normal recall")
    b_clue = {
        "claim": "Saw a beggar wearing blue ribbon near the west gate",
        "confidence": 0.85,
        "durability": "transient",
        "created_turn": 1,
        "last_recalled_turn": 1,
        "links": ["blue_ribbon"],
    }
    vault = [b_clue]
    triggers = ["blue_ribbon"]

    # At turn 1: fresh memory (cost = 1.0 - 0.85 = 0.15 <= 0.50 budget)
    condition_normal = {"energy": 0.5, "allostatic_load": 0.0}  # budget = 0.50
    recalled_fresh = run_gate(triggers, vault, {}, [], condition_normal, current_turn=1)
    check("fresh-memory-recalled", len(recalled_fresh) == 1)

    # At turn 30: decayed memory (eff_conf ~0.05 -> cost ~0.95 > 0.50 budget)
    recalled_decayed = run_gate(triggers, vault, {}, [], condition_normal, current_turn=30)
    check("decayed-memory-suppressed-under-normal-energy", len(recalled_decayed) == 0)

    # At turn 30 under hyper-focus / full rest: budget = 1.0 -> cost 0.95 <= 1.0 -> retrieved!
    condition_hyper = {"energy": 1.0, "allostatic_load": 0.0}  # budget = 1.0
    recalled_hyper = run_gate(triggers, vault, {}, [], condition_hyper, current_turn=30)
    check("decayed-memory-retrievable-under-high-energy", len(recalled_hyper) == 1)


def test_memory_refresh_and_spaced_repetition():
    print("\n[4] Reinforcement & Spaced Repetition")
    b = {
        "claim": "The watchword for the guard post is Falcon",
        "confidence": 0.80,
        "durability": "transient",
        "created_turn": 1,
        "last_recalled_turn": 1,
        "recall_count": 0,
    }

    c_decayed = decay.calculate_effective_confidence(b, current_turn=16)
    check("unreinforced-fades", c_decayed < 0.20)

    # a recall is DERIVED from the decision_manifests log (fold_recall_history); the imperative
    # record_belief_recall was retired 2026-09-10. This is what the fold yields for one recall now.
    refreshed = dict(b, last_recalled_turn=16, recall_count=1)
    c_refreshed = decay.calculate_effective_confidence(refreshed, current_turn=16)
    check("refreshed-memory-sharp-again", c_refreshed == 0.80)
    check("recall-count-incremented", refreshed["recall_count"] == 1)

    practiced = dict(refreshed)
    practiced["recall_count"] = 4
    practiced["last_recalled_turn"] = 20
    c_practiced_10 = decay.calculate_effective_confidence(practiced, current_turn=30)
    raw_transient_10 = decay.calculate_effective_confidence(b, current_turn=11)
    check("spaced-repetition-slows-decay", c_practiced_10 > raw_transient_10, f"{c_practiced_10} vs {raw_transient_10}")


def test_live_connection_slows_decay():
    print("\n[5] Live Connection Scaling (Finding 4)")
    b_friend = {"claim": "Maren loves winter pears", "confidence": 0.85, "links": ["maren"], "durability": "transient"}
    b_stranger = {"claim": "Joss loves winter pears", "confidence": 0.85, "links": ["joss"], "durability": "transient"}

    relationships = {
        "maren": {"affinity": 0.9, "trust": 0.9, "respect": 0.8},
        "joss": {"affinity": 0.5, "trust": 0.5, "respect": 0.5},
    }

    c_friend = decay.calculate_effective_confidence(b_friend, elapsed=12, relationships=relationships)
    c_stranger = decay.calculate_effective_confidence(b_stranger, elapsed=12, relationships=relationships)

    check("friend-memory-decays-slower", c_friend > c_stranger, f"{c_friend} vs {c_stranger}")
    check("stranger-memory-faded", c_stranger < 0.20)
    check("friend-memory-still-accessible", c_friend > 0.28, f"actual: {c_friend}")


def test_faintness_reaches_prompt_sureness():
    print("\n[6] Decayed Memory Portrayed with Uncertainty in Words (Finding 6)")
    b_fresh = {"claim": "The swallows came back early this year", "confidence": 0.95, "confidence_eff": 0.95, "provenance": "lived"}
    b_faded = {"claim": "The swallows came back early this year", "confidence": 0.95, "confidence_eff": 0.18, "provenance": "lived"}

    p_fresh = _recall_for_packet(b_fresh)
    p_faded = _recall_for_packet(b_faded)

    check("packet-uses-confidence-eff", p_faded["confidence"] == 0.18)
    check("fresh-narrates-certainty", sureness(p_fresh["confidence"]) == "you do not entertain the alternative")
    check("faded-narrates-uncertainty", sureness(p_faded["confidence"]) == "you would not stake anything on it")


def test_chronicle_fold_recall_history():
    print("\n[7] Replay Derivation from Chronicle (Finding 1)")
    import sqlite3
    tmp = os.path.join(tempfile.mkdtemp(), "test_chronicle.db")
    con = sqlite3.connect(tmp)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE decision_manifests (run_id TEXT, turn INTEGER, actor TEXT, manifest TEXT)")

    con.execute("INSERT INTO decision_manifests VALUES (?, ?, ?, ?)",
                ("r1", 5, "kael", json.dumps({"recall_ids": ["b:sigil", "b:watchword"]})))
    con.execute("INSERT INTO decision_manifests VALUES (?, ?, ?, ?)",
                ("r1", 12, "kael", json.dumps({"recall_ids": ["b:sigil"]})))

    history = decay.fold_recall_history(con, "r1", "kael")
    check("sigil-found-in-history", "b:sigil" in history)
    check("sigil-last-turn-is-12", history["b:sigil"]["last_turn"] == 12)
    check("sigil-count-is-2", history["b:sigil"]["count"] == 2)
    check("watchword-last-turn-is-5", history["b:watchword"]["last_turn"] == 5)
    check("watchword-count-is-1", history["b:watchword"]["count"] == 1)


def test_each_memory_its_own_story_time():
    """gate memory-fades (2026-09-24). Both drivers handed the gate the story time AFTER the current beat - zero at
    the head of the log - so no memory faded in a live run. Each memory now has its own: since the beat that formed
    or last recalled it, or, carried on the sheet, since page one; and with no clock, none."""
    print("\n[9] Each memory its own story time (gate memory-fades)")
    from src.engine import clock
    from src.engine.decay_law import relax
    from src.engine.ledger import Ledger
    from src.engine.records import PATHS, TurnCommit
    led = Ledger(":memory:")
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    led.register_character("r", "m", {"id": "m", "name": "M"}, {})
    led.record_scene_clock("r", 0, 480.0, 60.0, 20.0)                 # 08:00, an hour, twenty minutes a beat
    for t in (0, 1, 2):
        led.append_turn(TurnCommit(run_id="r", turn=t, actor="m", thought="-", action="-", tags={},
                                   validation={"ok": True}, affect={p: 0.2 for p in PATHS}))
    led.record_scene_clock("r", 3, 1920.0, 30.0, 10.0)               # next morning at 08:00
    led.append_turn(TurnCommit(run_id="r", turn=3, actor="m", thought="-", action="-", tags={},
                               validation={"ok": True}, affect={p: 0.2 for p in PATHS}))
    since = lambda t: clock.days_since(led.con, "r", t, 4)           # asked at the start of beat 4: 08:10, day 2
    sheet = {"claim": "the relief boat was due at dawn", "confidence": 0.8, "durability": "transient", "bid": "b:boat"}
    learned = dict(sheet, bid="b:learned", created_turn=1)
    got = decay.calculate_effective_confidence(sheet, elapsed=since)
    want = relax(0.8, decay.FLOOR_TRANSIENT, decay.RETENTION_TRANSIENT, (1930.0 - 480.0) / 1440.0)
    check("a-sheet's-memory-fades-from-page-one", abs(got - round(want, 4)) < 1e-12 and got < 0.8, repr((got, want)))
    got = decay.calculate_effective_confidence(learned, elapsed=since)
    want = relax(0.8, decay.FLOOR_TRANSIENT, decay.RETENTION_TRANSIENT, (1930.0 - 520.0) / 1440.0)
    check("a-learned-one-from-the-end-of-the-beat-that-taught-it", abs(got - round(want, 4)) < 1e-12, repr((got, want)))
    got = decay.calculate_effective_confidence(sheet, elapsed=since, recall_history={"b:boat": {"last_turn": 3, "count": 1}})
    check("a-recalled-one-from-its-last-recall-(here-no-time-at-all)", got == 0.8, repr(got))
    check("a-core-one-never", decay.calculate_effective_confidence(dict(sheet, durability="core"), elapsed=since) == 0.8)
    bare = Ledger(":memory:")
    bare.create_run("q", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    check("no-clock-no-time", decay.calculate_effective_confidence(
        sheet, elapsed=lambda t: clock.days_since(bare.con, "q", t, 4)) == 0.8)
    with led.con:                                                    # a memory logged before this gate: no turn in it
        led.con.execute("INSERT INTO acquisitions (run_id, char_id, turn, belief) VALUES ('r', 'm', 2, ?)",
                        (json.dumps({"claim": "the lamp oil was low"}),))
    kept = led.acquisitions_for("r", "m")
    check("an-old-logged-memory-takes-its-turn-from-its-row", kept and kept[-1].get("created_turn") == 2, repr(kept))
    fresh = {"claim": "the wind backed at noon"}
    led.append_acquisition("r", "m", 3, fresh)
    check("a-new-one-is-stamped-in-place-and-in-the-log", fresh.get("created_turn") == 3
          and led.acquisitions_for("r", "m")[-1].get("created_turn") == 3, repr(fresh))


def test_a_live_run_forgets():
    """The same through scripts/scene.py main: a memory the sheet carries and one a witness learns, across two
    scenes a day apart, as the recall gate actually receives them."""
    print("\n[10] A live run forgets (gate memory-fades)")
    import contextlib
    import glob
    import io
    import re
    import shutil
    import sqlite3
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    sys.path.insert(0, os.path.join(REPO, "tests"))
    import scene
    from src.engine import associative, clock, rungs
    from src.engine.decay_law import relax
    from src.engine.records import Reading, RecordError
    from test_condition import FLOW, _cfg
    from test_systems import _book
    tmp = tempfile.mkdtemp(prefix="swe_forget_")
    book = _book(tmp, FLOW)
    path = os.path.join(book, "characters", "Mira.md")
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"```json\n(.*)\n```", txt, re.S)
    data = json.loads(m.group(1))
    data["current"]["vault"] = [{"claim": "the relief boat was due at dawn", "confidence": 0.8, "durability": "transient",
                                 "bid": "b:boat", "provenance": "seed"}]
    open(path, "w", encoding="utf-8").write(txt[:m.start(1)] + json.dumps(data, indent=1) + txt[m.end(1):])
    seen = []
    real = associative.calculate_effective_confidence

    def spy(belief, current_turn=0, relationships=None, recall_history=None, elapsed=None):
        out = real(belief, current_turn, relationships, recall_history, elapsed)
        seen.append((dict(belief), elapsed, out))
        return out

    def fake_turn(packet, event_text, temperament, model, stub, **k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        return ({"action": "She trims the wick and says the wind is backing.", "thought": "", "exit": False,
                 "addressee": other, "act": "",
                 "tags": {"type": "threat", "summary": "trims the wick", "dimensions": {"threat": 0.7},
                          "durability": "durable", "subject": other, "object": other}}, [])

    def refuse(*_a, **_k):
        raise RecordError("APPRAISER_REPLY_NOT_JSON", "the event seat is faked out of this test")

    def emotion(action, thought, model, led=None, run_id=None, turn=None, me=None, present=(), **_k):
        other = next(p for p in present if p != me)
        return ([Reading(path="WARINESS", rung=rungs.rung_at("WARINESS", 0.6)[1], about=other, confidence="sure")],
                [other], "sure", [])

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv,
             associative.calculate_effective_confidence)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, refuse, emotion
    associative.calculate_effective_confidence = spy
    try:
        for i, (name, day, time) in enumerate((("dusk", 1, "18:00"), ("next-dusk", 2, "18:00"))):
            argv = ["scene.py", "--book", book, "--scene", _cfg(tmp, name, day, time, "1h"), "--budget", "2",
                    "--model", "fake/model", "--no-keeper"]
            if i:
                db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
                argv += ["--resume", sqlite3.connect(db).execute("SELECT run_id FROM runs").fetchone()[0]]
            sys.argv = argv
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                scene.main()
        db = glob.glob(os.path.join(book, "runs", "*.db"))[0]
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        run_id = con.execute("SELECT run_id FROM runs").fetchone()[0]
        check("the-gate-was-handed-a-clock-not-a-zero", seen and all(callable(e) for _b, e, _o in seen),
              repr(sorted({repr(e)[:30] for _b, e, _o in seen})))
        boat = [(e, o) for b, e, o in seen if b.get("bid") == "b:boat"]
        start2 = con.execute("SELECT MAX(start_turn) FROM scenes").fetchone()[0]
        at2 = clock.at_turn(con, run_id, start2)
        want = round(relax(0.8, decay.FLOOR_TRANSIENT, decay.RETENTION_TRANSIENT, (at2 - clock.opening(con, run_id)) / 1440.0), 4)
        check("the-sheet's-memory-is-whole-at-page-one", boat and boat[0][1] == 0.8, repr(boat[:1]))
        check("...and-a-day-weaker-when-the-next-scene-opens", any(abs(o - want) < 1e-12 for _e, o in boat) and want < 0.8,
              repr((want, [o for _e, o in boat])))
        rows = [(int(r["turn"]), json.loads(r["belief"])) for r in con.execute("SELECT turn, belief FROM acquisitions")]
        check("a-witness-learned-something-and-the-log-keeps-when", rows and all(b.get("created_turn") == t for t, b in rows),
              repr(rows[:2]))
        learned = [b for b, _e, _o in seen if b.get("bid") != "b:boat"]      # every memory the sheet did not carry
        check("...and-the-vault's-copy-fades-from-that-beat", learned and all("created_turn" in b for b in learned),
              repr([b for b in learned if "created_turn" not in b][:1]))
    finally:
        (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv,
         associative.calculate_effective_confidence) = saved
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_core_belief_invariance()
    test_transient_vs_durable_decay()
    test_gate_retrieval_under_decay()
    test_memory_refresh_and_spaced_repetition()
    test_live_connection_slows_decay()
    test_faintness_reaches_prompt_sureness()
    test_chronicle_fold_recall_history()
    test_each_memory_its_own_story_time()
    test_a_live_run_forgets()
    print("\n" + "-" * 50)
    print(f"{len(PASS)} passed, {len(FAIL)} failed")
    sys.exit(1 if FAIL else 0)
