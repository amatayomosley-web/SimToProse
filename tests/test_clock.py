"""test_clock.py — the minute clock: the reading, the derived gap, and emotion on it.

Owner, 2026-09-10: "if we lock duration to the minute, and the design says user must declare date
and time and time between scenes, we have a locked design we can set our decay to." This suite
pins the three halves of that lock:

  1. THE READING. `at` parses to absolute minutes from day 1 00:00 and refuses every wrong shape by
     name; `lasts` takes minutes or "2h" sugar and refuses zero.
  2. THE DERIVATION. The gap before a scene is the previous scene's END to this one's opening,
     logged through `declare` unchanged; a scene that opens before the last one ended is refused;
     a scene that lulled early owes its unspent `lasts` to the next opening — derived from the
     log alone, because resume rehydrates affect from the last committed turn.
  3. EMOTION ON THE CLOCK. `state.decay` takes MINUTES and refuses to be called without them; a
     half-life halves the excursion; the disposition zone fades slower than the episode zone; hold
     stretches by one ratio; zero minutes moves nothing.

Stdlib only. Exit 0 = all pass.
"""
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import clock                                  # noqa: E402
from src.engine import heritable as _her                      # noqa: E402
from src.engine import state as _st                           # noqa: E402
from src.engine.ledger import Ledger, LedgerError             # noqa: E402
from src.engine import rungs as _rungs
from src.engine.records import PATHS, RecordError             # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _refuses(fn, code):
    try:
        fn()
        return False
    except (RecordError, LedgerError) as exc:
        return code in str(exc)


def test_the_reading():
    print("\n[1] THE READING — `at` and `lasts` in minutes, refused by name otherwise")
    check("day-1-midnight-is-zero", clock.parse_at({"day": 1, "time": "00:00"}) == 0.0)
    check("day-2-09-00", clock.parse_at({"day": 2, "time": "09:00"}) == 24 * 60 + 9 * 60)
    check("format-round-trips", clock.format_at(clock.parse_at({"day": 3, "time": "17:45"})) == "day 3 17:45")
    check("at-not-an-object", _refuses(lambda: clock.parse_at("tuesday"), "CLOCK_AT_NOT_AN_OBJECT"))
    check("day-zero-refused", _refuses(lambda: clock.parse_at({"day": 0, "time": "09:00"}), "CLOCK_AT_DAY_INVALID"))
    check("time-25-00-refused", _refuses(lambda: clock.parse_at({"day": 1, "time": "25:00"}), "CLOCK_AT_TIME_INVALID"))
    check("span-minutes", clock.span_minutes(45) == 45.0 and clock.span_minutes("90m") == 90.0)
    check("span-hours-days", clock.span_minutes("2h") == 120.0 and clock.span_minutes("1.5d") == 2160.0)
    check("span-absent-is-none", clock.span_minutes(None) is None)
    check("span-zero-refused", _refuses(lambda: clock.span_minutes(0), "CLOCK_SPAN_NOT_POSITIVE"))
    check("span-nonsense-refused", _refuses(lambda: clock.span_minutes("a while"), "CLOCK_SPAN_NOT_A_SPAN"))


def test_the_derivation(tmp):
    print("\n[2] THE DERIVATION — the gap is from the last scene's END, and it is logged")
    led = Ledger(os.path.join(tmp, "clock.db"))
    led.create_run("r1", {"catalog_version": 1, "models": {"decide": "stub"}, "prompt_versions": {"decide": 1}})
    a1 = clock.parse_at({"day": 1, "time": "20:00"})
    check("first-scene-has-no-gap", led.gap_before("r1", a1, before_turn=0) is None)
    led.record_scene_clock("r1", 0, a1, 60.0, beat_minutes=6.0)       # lasts an hour, budget 10
    a2 = clock.parse_at({"day": 2, "time": "09:00"})
    gap = led.gap_before("r1", a2, before_turn=7)
    check("gap-is-end-to-opening", gap == 12 * 60.0, gap)               # 21:00 -> 09:00
    # the scene lulled after 7 beats of a 10-beat budget: 3 beats x 6 min unspent
    owed = led.unspent_before("r1", 7)
    check("unspent-lasts-is-owed", owed == 18.0, owed)
    led.declare_time("r1", 7, gap, "derived")
    check("declaration-is-in-minutes",
          led.con.execute("SELECT elapsed FROM time_declarations WHERE turn = 7").fetchone()[0] == 12 * 60.0)
    led.record_scene_clock("r1", 7, a2, None, 0.0)                    # the next scene's reading, as open_scene logs it
    check("story-time-since-beat-0-is-the-rest-of-the-scene-and-the-gap",   # gate story-clock: 20:06 -> 09:00
          led.elapsed_since("r1", 0) == 54.0 + 12 * 60.0, led.elapsed_since("r1", 0))
    check("opening-before-the-last-end-is-refused",
          _refuses(lambda: led.gap_before("r1", clock.parse_at({"day": 1, "time": "20:30"}), before_turn=7),
                   "CLOCK_RUNS_BACKWARDS"))
    # a replay of the same reading is idempotent; a different one is refused (append-only)
    led.record_scene_clock("r1", 0, a1, 60.0, beat_minutes=6.0)
    check("same-reading-replays-silently", clock.last_scene_clock(led.con, "r1", 1)["at"] == a1)
    check("different-reading-is-refused",
          _refuses(lambda: led.record_scene_clock("r1", 0, a1 + 5, 60.0, 6.0), "LEDGER_SCENE_CLOCK_REWRITE"))
    check("no-lasts-owes-nothing", (led.record_scene_clock("r1", 7, a2, None, 0.0) or True)
          and led.unspent_before("r1", 9) == 0.0)


def test_emotion_on_the_clock():
    print("\n[3] EMOTION ON THE CLOCK — minutes in, a half-life halves, zones differ, hold stretches")
    ch = {"fixed": {"genotype": _her.typical(**{"SELF-REGARD": {"hold": "lasting"}})}, "baseline": {}, "current": {}}
    prof = _st.build_profile(ch)
    temp = ch["baseline"]["temperament"]
    check("profile-carries-hold-not-rates", "hold" in prof and "decay_rates" not in prof, sorted(prof))   # decay_rates is retired
    aff = {p: temp[p]["mean"] for p in PATHS}
    aff["WARINESS"] = 0.60                                    # an excursion into the episode zone
    check("elapsed-is-required", _refuses(lambda: _st.decay(dict(aff), temp, prof), "STATE_ELAPSED_MISSING"))
    zero = _st.decay(dict(aff), temp, prof, elapsed=0.0)
    check("zero-minutes-moves-nothing", abs(zero["WARINESS"] - 0.60) < 1e-12)
    # PER-RUNG (gate 2, 2026-09-12): a small excursion that stays inside one rung halves over THAT
    # rung's own half-life. A tiny +0.02 on WARINESS stays in its band across one half-life.
    wmean = temp["WARINESS"]["mean"]; wv = wmean + 0.02
    hl = _st.half_life_minutes("WARINESS", wv, 1.0)
    half = _st.decay({**{p: temp[p]["mean"] for p in PATHS}, "WARINESS": wv}, temp, prof, elapsed=hl)
    check("one-half-life-halves-a-small-excursion",
          abs((half["WARINESS"] - wmean) - 0.02 / 2.0) < 1e-3, half["WARINESS"])
    # the low rungs are slower than the high ones: the SAME minutes take less off a low-rung
    # excursion than off a top-rung one (the staircase, short at the top and long at the bottom).
    topv = _rungs.height_of("WARINESS", len(_rungs.names_on("WARINESS")))     # panic, top rung
    lowv = wmean + 0.02
    drop_top = topv - _st.decay_over("WARINESS", topv, wmean, 1.0, 30.0)
    drop_low = lowv - _st.decay_over("WARINESS", lowv, wmean, 1.0, 30.0)
    check("the-top-drains-faster-than-the-bottom", (drop_top / (topv - wmean)) > (drop_low / (lowv - wmean)) + 1e-6,
          (drop_top, drop_low))
    # hold stretches the half-life by one ratio: a lasting SELF-REGARD needs 1.15x the minutes to halve
    # HOLD stretches every rung's half-life uniformly, so a lasting hold over 1.15x the minutes
    # lands exactly where a typical hold lands over the minutes — true segment by segment (gate 2).
    srmean = temp["SELF-REGARD"]["mean"]; srv = 0.70
    base = _st.decay_over("SELF-REGARD", srv, srmean, 1.0, 120.0)
    stretched = _st.decay_over("SELF-REGARD", srv, srmean, _her.PERSIST["lasting"], 120.0 * _her.PERSIST["lasting"])
    check("hold-lasting-stretches-every-rung-alike", abs(base - stretched) < 1e-9, (base, stretched))
    check("retention-is-0.5-at-one-half-life",
          abs(_st.retention_for("DEFLATION", 0.9, 1.0, _st.half_life_minutes("DEFLATION", 0.9, 1.0)) - 0.5) < 1e-12)
    # THE MEASURED ORDER (2026-09-11, Red Badge + Holmes on the thermometer): RECEPTIVITY outlasts
    # STIRRING on both books, which the spec's guess had the other way round.
    check("half-life-order-is-the-measured-one", all(
        _st._HALF_LIFE[a][0] < _st._HALF_LIFE[b][0] for a, b in
        (("WARINESS", "STIRRING"), ("STIRRING", "DISPLEASURE"), ("DISPLEASURE", "RECEPTIVITY"),
         ("RECEPTIVITY", "GOODWILL"), ("GOODWILL", "DISTASTE"), ("DEFLATION", "SELF-REGARD"))))
    check("every-path-fades-slower-at-rest-than-in-an-episode",
          all(_st._HALF_LIFE[p][1] > _st._HALF_LIFE[p][0] for p in PATHS))


def test_the_clock_call_lives_in_ONE_place():
    print("\n[4] ONE CLOCK, ONE CALLER — the inline block moved to src/engine/passage.py")
    # gate driver-clock-parity (2026-09-19): `led.unspent_before(` — along with record_scene_clock,
    # gap_before and declare_time — lived inline in scripts/scene.py, which is why direct.py could
    # not reach it. If this substring drifts back into a driver, the two drivers hold two clocks
    # again (scripts/direct.py's own former comment: "This driver declares no elapsed of its own").
    # Source-level guard, same style as test_bonds.py's "replays-through-bond_rest".
    passage_src = open(os.path.join(REPO, "src", "engine", "passage.py"), encoding="utf-8").read()
    check("passage.py-HOLDS-the-call", "led.unspent_before(" in passage_src)
    for script in ("scene.py", "direct.py"):
        src = open(os.path.join(REPO, "scripts", script), encoding="utf-8").read()
        check("%s-no-longer-calls-it-INLINE" % script[:-3],
              "led.unspent_before(" not in src,
              "the block is back in a driver instead of src/engine/passage.py")
        check("...and-%s-dispatches-through-passage.open_scene" % script[:-3],
              "passage.open_scene(" in src, "the driver no longer calls the shared helper")


def test_the_story_clock(tmp):
    """gate story-clock (2026-09-24). The owner: "their stat runs with or without us looking." `elapsed_since`
    summed the DECLARED time after a turn - the gaps between scenes - so a scene's own minutes and a lulled scene's
    unspent ones passed for nothing that read it. It now measures story time from the end of a beat."""
    print("\n[5] THE STORY CLOCK — every minute counts: a scene's own, the unspent ones, the gaps")
    from src.engine.records import TurnCommit
    led = Ledger(os.path.join(tmp, "story.db"))
    led.create_run("r1", {"catalog_version": 1, "models": {"decide": "stub"}, "prompt_versions": {"decide": 1}})
    led.register_character("r1", "m", {"id": "m", "name": "M"}, {})

    def beat(t):
        led.append_turn(TurnCommit(run_id="r1", turn=t, actor="m", thought="-", action="-", tags={},
                                   validation={"ok": True}, affect={p: 0.2 for p in PATHS}))
    led.record_scene_clock("r1", 0, 600.0, 30.0, 10.0)               # A: 10:00, thirty minutes, ten a beat
    beat(0), beat(1)                                                 # ...lulled after two: ten minutes unspent
    led.record_scene_clock("r1", 2, 660.0, 20.0, 10.0)               # B: 11:00
    led.declare_time("r1", 2, 30.0, "derived")                       # 10:30 -> 11:00
    beat(2), beat(3)
    check("a-beat-ends-its-minutes-after-its-reading", [clock.beat_end(led.con, "r1", t) for t in range(4)]
          == [610.0, 620.0, 670.0, 680.0], [clock.beat_end(led.con, "r1", t) for t in range(4)])
    check("the-story-has-reached-the-last-beat's-end", clock.story_now(led.con, "r1") == 680.0)
    check("since-beat-0-counts-A's-next-beat-its-unspent-ten-the-gap-and-B",
          led.elapsed_since("r1", 0) == 10.0 + 10.0 + 30.0 + 20.0, led.elapsed_since("r1", 0))
    old = led.con.execute("SELECT SUM(elapsed) FROM time_declarations WHERE turn > 0").fetchone()[0]
    check("...where-the-declared-sum-saw-only-the-gap", old == 30.0, old)
    check("a-declaration-at-the-aged-turn-still-predates-its-end", led.elapsed_since("r1", 2) == 10.0)
    check("the-last-beat-has-nothing-since-it", led.elapsed_since("r1", 3) == 0.0)
    check("...nor-a-beat-not-yet-played", led.elapsed_since("r1", 4) == 0.0, led.elapsed_since("r1", 4))
    led.record_scene_clock("r1", 4, 720.0, None, 0.0)                # C opens at noon; no beat yet
    check("an-opening-moves-the-story-on-before-its-first-beat", clock.story_now(led.con, "r1") == 720.0
          and led.elapsed_since("r1", 3) == 40.0, (clock.story_now(led.con, "r1"), led.elapsed_since("r1", 3)))
    check("in-days-for-the-tiers-that-read-days", abs(led.elapsed_days_since("r1", 0) - 110.0 / 1440.0) < 1e-15,
          led.elapsed_days_since("r1", 0) * 1440.0)
    bare = Ledger(os.path.join(tmp, "bare.db"))                       # a log with no scene reading at all
    bare.create_run("r2", {"catalog_version": 1, "models": {"decide": "stub"}, "prompt_versions": {"decide": 1}})
    bare.declare_time("r2", 1, 5.0, "d"), bare.declare_time("r2", 2, 7.0, "d")
    check("a-log-with-no-reading-sums-its-declared-gaps-as-before",
          bare.elapsed_since("r2", 0) == 12.0 and bare.elapsed_since("r2", 2) == 0.0 and clock.story_now(bare.con, "r2") is None)


def main():
    print("test_clock.py — the minute clock")
    tmp = tempfile.mkdtemp(prefix="stp-clock-")
    try:
        test_the_reading()
        test_the_derivation(tmp)
        test_emotion_on_the_clock()
        test_the_clock_call_lives_in_ONE_place()
        test_the_story_clock(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
