"""test_multipliers.py — gate three: connection over every held thing, repetition, presence, and
the wound as engine state that a scene can mint and a resume can find.

The receipt is  v_k · g · connection(about) · q  and the half-life is  base · hold · (1 +
connection(about)) · presence  (docs/emotion-arithmetic.md section 3; owner's rulings of
2026-09-10 and 2026-09-11). Five claims, each with its falsifier:

  1. AN IDEA HITS LIKE A PERSON. A reading about a concept the character holds at investment c
     lands exactly as one about a person whose edge composes to c. Falsifier: the two receipts
     differ by more than float noise.
  2. REPETITION. The same reading again about the same absent thing lands softer each time; about
     a present thing, harder; capped. Falsifier: the sequence is not monotone, or n=4 != n=9.
  3. PRESENCE AND INVESTMENT SLOW THE FADE. A bound path fades slower than an unbound one; a bound
     AND present path slower still; a full investment doubles the half-life exactly. Falsifier:
     any of the three orderings fails.
  4. A SCENE CAN SCAR, AND THE SCAR SURVIVES RESUME. A durable beat that leaves a path bound to a
     concept in its top rungs mints a wound; the row is append-only; a fresh sheet folded from the
     log carries the same wound at the same intensity. Falsifier: the fold differs, or the DB lets
     the row be rewritten.
  5. THE COUNT IS THE LOG'S. `repeat_count` reads consecutive turns about the same subject from
     the chronicle and stops at the first that is not.

Stdlib only. Exit 0 = all pass.
"""
import copy
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import connection as K                        # noqa: E402
from src.engine import heritable as H                         # noqa: E402
from src.engine import state as S                             # noqa: E402
from src.engine import targets as T                           # noqa: E402
from src.engine import wound as W                             # noqa: E402
from src.engine.ledger import Ledger                          # noqa: E402
from src.engine.records import PATHS, TurnCommit, Event       # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _char(c=0.85):
    """A character who holds a person and a concept at the SAME investment c (0.2 <= c <= 1)."""
    aff = 0.5 + c / 2.0                     # compose() = 2 * 0.6*(a-.5) + 2*0.25*(t-.5) + 2*0.15*(r-.5) = c when all three are equal
    ch = {"fixed": {"genotype": H.typical()},
          "baseline": {"temperament": H.resting(),
                       "wounds": [W.make("loss_of_a_child", "DEFLATION", c, "profile:t", text="the child")]},
          "current": {"relationships": {"kid": {"affinity": aff, "trust": aff, "respect": aff, "debt": 0.0}}}}
    S.build_profile(ch)
    return ch


def test_an_idea_hits_like_a_person():
    print("\n[1] AN IDEA HITS LIKE A PERSON")
    ch = _char(0.85)
    prof = S.build_profile(ch)
    rest = {p: ch["baseline"]["temperament"][p]["mean"] for p in PATHS}
    check("the-edge-and-the-wound-compose-to-the-same-investment",
          abs(K.for_about(prof["relationships"], prof["held"], "kid") - 0.85) < 1e-9
          and abs(K.for_about(prof["relationships"], prof["held"], "concept:loss_of_a_child", "DEFLATION") - 0.85) < 1e-9,
          (K.for_about(prof["relationships"], prof["held"], "kid"), prof["held"]))
    person = S.appraise(rest, {"dimensions": {"loss": 0.8}, "target": "kid"}, prof, targets={"DEFLATION": "kid"})
    idea = S.appraise(rest, {"dimensions": {"loss": 0.8}, "target": "concept:loss_of_a_child"}, prof,
                      targets={"DEFLATION": "concept:loss_of_a_child"})
    stranger = S.appraise(rest, {"dimensions": {"loss": 0.8}, "target": "nobody"}, prof, targets={"DEFLATION": "nobody"})
    check("the-idea-and-the-person-land-identically", abs(person["DEFLATION"] - idea["DEFLATION"]) < 1e-12,
          (person["DEFLATION"], idea["DEFLATION"]))
    check("and-both-land-harder-than-a-stranger", idea["DEFLATION"] > stranger["DEFLATION"] + 1e-6,
          (idea["DEFLATION"], stranger["DEFLATION"]))
    # a concept scales EVERY dimension (it is the thing feared); a person scales the empathy dims only
    fear_idea = S.appraise(rest, {"dimensions": {"threat": 0.8}, "target": "concept:loss_of_a_child"}, prof,
                           targets={"WARINESS": "concept:loss_of_a_child"})
    fear_none = S.appraise(rest, {"dimensions": {"threat": 0.8}}, prof)
    check("a-concept-scales-a-threat-a-person-would-not",
          fear_idea["WARINESS"] == fear_none["WARINESS"],       # no wound on WARINESS about this concept -> no scaling
          (fear_idea["WARINESS"], fear_none["WARINESS"]))
    ch["baseline"]["wounds"].append(W.make("sickness", "WARINESS", 0.85, "profile:t"))
    prof2 = S.build_profile(ch)
    fear_wound = S.appraise(rest, {"dimensions": {"threat": 0.8}, "target": "concept:sickness"}, prof2,
                            targets={"WARINESS": "concept:sickness"})
    check("...and-a-wound-on-that-path-does", fear_wound["WARINESS"] > fear_none["WARINESS"] + 1e-6)
    check("below-the-floor-is-exactly-nothing", K.for_about({}, {"concept:fire": {"WARINESS": 0.15}}, "concept:fire", "WARINESS") == 0.0)


def test_repetition():
    print("\n[2] REPETITION — softer when absent, harder when present, capped")
    ch = _char(0.85)
    prof = S.build_profile(ch)
    rest = {p: ch["baseline"]["temperament"][p]["mean"] for p in PATHS}
    tags = {"dimensions": {"loss": 0.8}, "target": "concept:loss_of_a_child"}
    tg = {"DEFLATION": "concept:loss_of_a_child"}
    absent = [S.appraise(rest, tags, prof, targets=tg, repeats={"concept:loss_of_a_child": n}, present=[])["DEFLATION"] for n in range(5)]
    here = [S.appraise(rest, tags, prof, targets=tg, repeats={"concept:loss_of_a_child": n},
                       present=["concept:loss_of_a_child"])["DEFLATION"] for n in range(5)]
    check("absent-habituates", all(a > b for a, b in zip(absent, absent[1:])), [round(x, 4) for x in absent])
    check("present-grinds", all(a < b for a, b in zip(here, here[1:])), [round(x, 4) for x in here])
    check("first-time-is-the-plain-receipt", absent[0] == here[0])
    check("capped", K.repetition(4, True) == K.repetition(9, True) and K.repetition(4, False) == K.repetition(40, False))
    check("no-count-is-1", K.repetition(0, False) == 1.0 == K.repetition(0, True))


def test_presence_and_investment_slow_the_fade():
    print("\n[3] PRESENCE AND INVESTMENT SLOW THE FADE")
    ch = _char(1.0)
    prof = S.build_profile(ch)
    temp = ch["baseline"]["temperament"]
    aff = {p: temp[p]["mean"] for p in PATHS}
    aff["DEFLATION"] = 0.70
    hl = S._HALF_LIFE["DEFLATION"][0]        # the episode anchor (`_HALF_LIFE[path]` is (episode,
                                              # disposition)); `_ZONE_EPISODE` retired 2026-09-19,
                                              # gate emotion-tier-tidy — this reader used it only as
                                              # a named index 0, never for zone semantics
    unbound = S.decay(dict(aff), temp, prof, elapsed=hl)["DEFLATION"]
    bound = S.decay(dict(aff), temp, prof, elapsed=hl, targets={"DEFLATION": "concept:loss_of_a_child"})["DEFLATION"]
    here = S.decay(dict(aff), temp, prof, elapsed=hl, targets={"DEFLATION": "concept:loss_of_a_child"},
                   present=["concept:loss_of_a_child"])["DEFLATION"]
    check("bound-fades-slower-than-unbound", bound > unbound + 1e-9, (unbound, bound))
    check("bound-and-present-slower-still", here > bound + 1e-9, (bound, here))
    check("a-full-investment-doubles-the-half-life", K.half_life_scale(1.0) == 2.0)
    # PER-RUNG (gate 2): stretch doubles whatever the rung's half-life is, so decaying bound over
    # `hl` lands where UNBOUND lands over `hl/2` -- the doubling on the float, no anchor-as-rate
    # assumption. (`half_life_scale(1.0) == 2.0` above is the multiplier; this is it on the float.)
    unbound_half = S.decay(dict(aff), temp, prof, elapsed=hl / 2.0)["DEFLATION"]
    check("the-doubling-shows-on-the-float", abs(bound - unbound_half) < 1e-9, (bound, unbound_half))
    check("nothing-bound-is-exactly-the-old-decay",
          S.decay(dict(aff), temp, prof, elapsed=hl) == S.decay(dict(aff), temp, prof, elapsed=hl, targets={}, present=[]))


def _commit(led, run_id, turn, actor, affect, subject=None, mints=()):
    tags = {"type": "mundane", "dimensions": {"threat": 0.9}, "durability": "durable"}
    if subject:
        tags["subject"] = subject
    led.append_turn(TurnCommit(run_id=run_id, turn=turn, actor=actor, thought="t", action="a",
                               tags=tags, affect=dict(affect), condition={}, validation={"ok": True, "flags": []},
                               events=[Event(type="mundane", payload={"text": "x"}, actor=actor)],
                               wound_mints=list(mints)))


def test_a_scene_can_scar_and_the_scar_survives_resume(tmp):
    print("\n[4] A DURABLE TOP-RUNG BEAT ABOUT A CONCEPT SCARS, AND THE SCAR SURVIVES RESUME")
    led = Ledger(os.path.join(tmp, "scar.db"))
    led.create_run("r1", {"catalog_version": 1, "models": {"decide": "stub"}, "prompt_versions": {"decide": 1}})
    ch = {"fixed": {"genotype": H.typical()}, "baseline": {"temperament": H.resting()}, "current": {}}
    S.build_profile(ch)
    aff = {p: ch["baseline"]["temperament"][p]["mean"] for p in PATHS}
    heights = {"WARINESS": 0.95}                                      # the seat read the top of the ladder
    targets = {"WARINESS": "concept:sickness"}
    check("a-transient-beat-mints-nothing", W.mint(ch, heights, targets, False, turn=1) == [])
    check("a-low-reading-mints-nothing", W.mint(ch, {"WARINESS": 0.30}, targets, True, turn=1) == [])
    check("a-person-bound-path-mints-nothing", W.mint(ch, heights, {"WARINESS": "kid"}, True, turn=1) == [])
    check("an-unread-path-mints-nothing", W.mint(ch, {}, targets, True, turn=1) == [])
    mints = W.mint(ch, heights, targets, True, surfaces=["the boy's forehead was hot"], text="the fever took hold", turn=1)
    check("a-durable-top-rung-beat-about-a-concept-mints-one-wound",
          len(mints) == 1 and mints[0]["id"] == "sickness@WARINESS" and mints[0]["intensity"] == 0.95
          and mints[0]["source"] == "run:1" and mints[0]["trigger"] == ["the boy's forehead was hot"], mints)
    _commit(led, "r1", 1, "maren", aff, subject="concept:sickness", mints=mints)
    W.fold(ch, W.mints_for(led.con, "r1", "maren"), led.wound_deltas_for("r1", "maren"))
    check("the-live-sheet-carries-it", [w["id"] for w in ch["baseline"]["wounds"]] == ["sickness@WARINESS"])
    check("the-same-pair-is-not-minted-twice", W.mint(ch, heights, targets, True, turn=2) == [])
    # RESUME: a fresh sheet, folded from the log alone
    fresh = {"fixed": {"genotype": H.typical()}, "baseline": {"temperament": H.resting()}, "current": {}}
    W.fold(fresh, W.mints_for(led.con, "r1", "maren"), led.wound_deltas_for("r1", "maren"))
    got = fresh["baseline"]["wounds"]
    check("a-resumed-sheet-carries-the-same-scar", len(got) == 1 and got[0]["id"] == "sickness@WARINESS"
          and got[0]["intensity"] == 0.95 and got[0]["text"] == "the fever took hold", got)
    # it is felt: the held registry now carries it and the receipt is amplified
    prof = S.build_profile(fresh)
    check("and-it-is-felt", prof["held"].get("concept:sickness", {}).get("WARINESS") == 0.95, prof["held"])
    # the row is APPEND-ONLY
    import sqlite3
    try:
        led.con.execute("UPDATE wound_minted SET intensity = 0.1")
        check("the-birth-cannot-be-rewritten", False, "UPDATE succeeded")
    except sqlite3.IntegrityError as exc:
        check("the-birth-cannot-be-rewritten", "append-only" in str(exc))
    try:
        led.con.execute("DELETE FROM wound_minted")
        check("nor-erased", False, "DELETE succeeded")
    except sqlite3.IntegrityError as exc:
        check("nor-erased", "append-only" in str(exc))


def test_the_count_is_the_logs(tmp):
    print("\n[5] THE REPETITION COUNT IS READ FROM THE CHRONICLE")
    led = Ledger(os.path.join(tmp, "count.db"))
    led.create_run("r2", {"catalog_version": 1, "models": {"decide": "stub"}, "prompt_versions": {"decide": 1}})
    aff = {p: 0.2 for p in PATHS}
    check("no-turns-is-zero", T.repeat_count(led.con, "r2", "ren", "concept:sickness") == 0)
    _commit(led, "r2", 0, "ren", aff, subject="concept:sickness")
    _commit(led, "r2", 1, "ren", aff, subject="concept:sickness")
    check("two-consecutive-turns-about-it-count-two", T.repeat_count(led.con, "r2", "ren", "concept:sickness") == 2)
    check("counted-before-a-turn-excludes-it", T.repeat_count(led.con, "r2", "ren", "concept:sickness", before_turn=1) == 1)
    _commit(led, "r2", 2, "ren", aff, subject="kid")
    check("a-different-subject-breaks-the-streak", T.repeat_count(led.con, "r2", "ren", "concept:sickness") == 0)
    _commit(led, "r2", 3, "ren", aff, subject="concept:sickness")
    check("and-it-starts-again", T.repeat_count(led.con, "r2", "ren", "concept:sickness") == 1)
    check("another-character-has-their-own-count", T.repeat_count(led.con, "r2", "maren", "concept:sickness") == 0)


def main():
    print("test_multipliers.py — gate three: connection, repetition, presence, and the minted wound")
    tmp = tempfile.mkdtemp(prefix="stp-g3-")
    try:
        test_an_idea_hits_like_a_person()
        test_repetition()
        test_presence_and_investment_slow_the_fade()
        test_a_scene_can_scar_and_the_scar_survives_resume(tmp)
        test_the_count_is_the_logs(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
