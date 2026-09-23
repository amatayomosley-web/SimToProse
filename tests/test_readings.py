"""test_readings.py — the appraiser's unit of output: validated, stored, replayed.

`docs/emotion-arithmetic.md` §1 and §5 step 8. Phase 2 of the emotion-arithmetic migration.

WHAT THIS SUITE IS REALLY FOR. §5 step 8 says that without a readings table *"`f` and `R` are not
re-derivable and hard rule 2 is false for emotion."* That is the claim under test: not that rows go
in, but that what comes back out is enough to rebuild the beat. So the round-trip test asserts the
readings return in the order they landed, and the append-only triggers are exercised rather than
assumed — a table declared append-only whose triggers were never fired is a coverage claim, not a
guarantee (`a-green-guard-is-a-coverage-claim-first`).
"""
import os
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import readings as R                              # noqa: E402
from src.engine import rungs                                      # noqa: E402
from src.engine.db import connect                                 # noqa: E402
from src.engine.records import Reading, RecordError                # noqa: E402

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    (PASS if ok else FAIL).append(name)


def _db():
    """A real schema on a real file. sqlite's :memory: would not exercise the migration."""
    path = os.path.join(tempfile.mkdtemp(prefix="readings_"), "t.db")
    con = connect(path)
    con.execute("INSERT INTO runs (run_id, created_at, config) VALUES (?, ?, ?)",
                ("r1", "2026-09-09T00:00:00Z", "{}"))
    con.commit()
    return con


def test_a_reading_validates_against_the_live_ladder():
    print("\n[1] THE LADDER IS THE AUTHORITY")
    Reading(path="DISPLEASURE", rung="anger", about="edda").validate()
    check("a-real-rung-on-a-real-path-passes", True)
    Reading(path="WARINESS", rung="dread", about="").validate()
    check("an-empty-about-is-not-an-error", True, "'' is UNBOUND per section 5 step 3 rule 4")

    for name, r in (("an-unbuilt-path-is-refused", Reading(path="COURAGE", rung="banter")),
                    ("a-rung-not-on-that-path", Reading(path="DISPLEASURE", rung="dread")),
                    ("a-misspelled-rung", Reading(path="DISPLEASURE", rung="furious")),
                    ("an-empty-path", Reading(path="", rung="anger")),
                    ("an-empty-rung", Reading(path="DISPLEASURE", rung="")),
                    ("a-non-string-about", Reading(path="DISPLEASURE", rung="anger", about=None))):
        try:
            r.validate()
            check(name, False, "did NOT raise")
        except RecordError:
            check(name, True)

    # THE CROSS-PATH CASE, which is the one a hand-written name list would miss: `dread` is a real
    # rung, just not on DISPLEASURE. Validation resolves against BANDS, so it catches this.
    check("a-real-rung-on-the-WRONG-path-is-caught", "dread" in rungs.names_on("WARINESS"),
          "dread is genuinely a WARINESS rung — the refusal above was not a typo check")


def test_a_path_written_in_lower_case_is_the_same_ladder():
    """2026-09-11, Red Badge on Opus: 105 of 221 answers wrote the eight in lower case and every one
    was refused as a rung not on the path. The path key is now matched without regard to case, as
    the rung name already was in rungs.index_of; an invented rung is still refused by name."""
    print("\
[1b] THE PATH KEY IS MATCHED WITHOUT REGARD TO CASE")
    top = rungs.names_on("WARINESS")[-1]
    rs, _l, _c = R.parse({"readings": [{"path": "wariness", "rung": top, "about": ""}], "confidence": "sure"})
    check("a-lower-case-path-parses-to-the-ladders-own-name", len(rs) == 1 and rs[0].path == "WARINESS" and rs[0].rung == top, rs)
    check("canonical-path-leaves-an-unknown-name-alone", R.canonical_path("courage") == "courage" and R.canonical_path(" Self-Regard ") == "SELF-REGARD")
    try:
        R.parse({"readings": [{"path": "wariness", "rung": "courage", "about": ""}], "confidence": "sure"})
        check("an-invented-rung-still-refuses-by-name", False, "did not raise")
    except RecordError as exc:
        check("an-invented-rung-still-refuses-by-name", "READING_RUNG_NOT_ON_PATH" in str(exc), str(exc)[:80])


def test_the_stub_is_gone_and_parse_took_its_place():
    """RETIRED 2026-09-09. This tested `stub_readings`, which was deleted the day the appraiser
    seats landed -- the condition its own `tests/test_reachable.py` exemption named in advance.

    IT COULD NEVER HAVE BEEN WIRED, and that is worth keeping rather than quietly dropping: it
    reported the rung a character was ALREADY at, so under Phase 3's arithmetic every beat would
    re-add the carried state to itself and the float would climb from a quiet room to the top rung.
    That is the p = 1 case docs/emotion-arithmetic.md section 8 says has no brake.

    `readings.parse` is the replacement and it is a different KIND of thing -- a validating boundary
    between a model and the ledger rather than a producer. What is asserted here is the half
    `Reading.validate` structurally cannot do: it resolves a rung against the live ladder but cannot
    see the scene, so aboutness and `lands_on` are checked where the percepts are in hand.
    """
    print(chr(10) + "[2] THE STUB IS GONE — parse() is the boundary now")
    check("stub_readings-is-deleted", not hasattr(R, "stub_readings"),
          "preserved in staging/src/engine/RETIRED-stub_readings.py")
    check("parse-exists", callable(getattr(R, "parse", None)))

    rows, lands, conf = R.parse(
        {"readings": [{"path": "DISPLEASURE", "rung": "anger", "about": "edda"}],
         "lands_on": ["edda"], "confidence": "likely"},
        percepts=[{"who": "edda"}], present=["edda"], me="ren")
    check("a-good-reply-parses", len(rows) == 1 and lands == ["edda"] and conf == "likely")
    check("the-confidence-word-is-carried-onto-the-reading", rows[0].confidence == "likely",
          "CONFIDENCE_WORDS was declared in Phase 2 and enforced nowhere until parse()")

    # AN IDLE BEAT IS THE COMMON CASE and must not raise — section 8's stability rests on silence
    rows, _l, _c = R.parse({"readings": [], "confidence": "sure"}, percepts=[], present=[])
    check("an-idle-beat-is-valid", rows == [])

    for name, obj in (
            ("a-numeric-rung-is-refused", {"readings": [{"path": "DISPLEASURE", "rung": "7"}]}),
            ("an-unknown-confidence-is-refused", {"readings": [], "confidence": "fairly"}),
            ("an-unperceived-about-is-refused",
             {"readings": [{"path": "GOODWILL", "rung": "warmth", "about": "joss"}]}),
            ("an-absent-lands_on-is-refused", {"readings": [], "lands_on": ["joss"]})):
        try:
            R.parse(obj, percepts=[{"who": "edda"}], present=["edda"], me="ren")
            check(name, False, "did NOT raise")
        except RecordError:
            check(name, True)


def test_the_round_trip():
    print("\n[3] ROUND TRIP — the beat is re-derivable, which is the whole point")
    con = _db()
    with con:
        R.write(con, "r1", 1, "ren", [Reading("DISPLEASURE", "anger", "edda"),
                                      Reading("WARINESS", "unease", "")])
        R.write(con, "r1", 2, "ren", [Reading("DISPLEASURE", "fury", "edda")])
        R.write(con, "r1", 2, "maren", [Reading("GOODWILL", "concern", "ren")])
    rows = R.readings_for(con, "r1")
    check("everything-written-comes-back", len(rows) == 4, len(rows))
    check("in-beat-order", [r[0] for r in rows] == [1, 1, 2, 2], [r[0] for r in rows])
    check("the-rung-name-survives", rows[0][3] == "anger", rows[0])
    check("an-unbound-about-round-trips-as-empty", rows[1][4] == "", repr(rows[1][4]))
    mine = R.readings_for(con, "r1", actor="maren")
    check("filtering-by-actor-works", len(mine) == 1 and mine[0][2] == "GOODWILL", mine)

    # TWO READINGS ON ONE PATH IN ONE BEAT are two additions, not one. A UNIQUE would have eaten one.
    with con:
        R.write(con, "r1", 3, "ren", [Reading("DISPLEASURE", "anger", "edda"),
                                      Reading("DISPLEASURE", "outrage", "joss")])
    turn3 = [r for r in R.readings_for(con, "r1") if r[0] == 3]
    check("two-readings-on-one-path-in-one-beat-both-survive", len(turn3) == 2, turn3)


def test_the_table_is_append_only():
    print("\n[4] APPEND-ONLY — fired, not assumed")
    con = _db()
    with con:
        R.write(con, "r1", 1, "ren", [Reading("DISPLEASURE", "anger", "edda")])
    for name, sql in (("update-is-refused", "UPDATE readings SET rung = 'fury'"),
                      ("delete-is-refused", "DELETE FROM readings")):
        try:
            with con:
                con.execute(sql)
            check(name, False, "the trigger did NOT fire")
        except sqlite3.IntegrityError as exc:
            check(name, "append-only" in str(exc), str(exc)[:60])
    check("...and-the-row-is-still-there", len(R.readings_for(con, "r1")) == 1)


def test_a_committed_turn_carries_its_readings():
    print("\n[5] THE COMMIT PATH — readings ride with the turn")
    import inspect
    from src.engine import ledger
    src = inspect.getsource(ledger.Ledger.append_turn)   # the commit method
    check("record-writes-readings", "_readings.write(" in src,
          "the commit must write them INSIDE the turn's transaction")
    # they must land inside the same `with con:` as the turn, not after it
    body = src[src.index("with self.con"):] if "with self.con" in src else ""
    check("...inside-the-transaction", "_readings.write(" in body,
          "a write after the transaction is a write a crash can lose")


def test_lands_on_round_trip():
    print(chr(10) + "[6] LANDS_ON ROUND TRIP -- write_lands_on / lands_on_for (gate lands-on-to-floor, 2026-09-19)")
    con = _db()
    with con:
        R.write_lands_on(con, "r1", 1, "ren", ["b", "c"])
    check("everything-written-comes-back-in-order", R.lands_on_for(con, "r1", 1) == ["b", "c"],
          R.lands_on_for(con, "r1", 1))
    check("a-turn-with-no-lands_on-reads-back-empty", R.lands_on_for(con, "r1", 2) == [],
          R.lands_on_for(con, "r1", 2))

    with con:
        n = R.write_lands_on(con, "r1", 3, "ren", [])
    check("an-empty-list-writes-no-rows", n == 0 and R.lands_on_for(con, "r1", 3) == [],
          (n, R.lands_on_for(con, "r1", 3)))

    # STORED AS GIVEN AFTER strip() -- parse() is the trust boundary that checked these against the
    # PerceptSet; this write does not re-validate, the same trust `write` places in `r.validate()`.
    with con:
        R.write_lands_on(con, "r1", 4, "ren", [" entity.b ", "B"])
    check("ids-are-stored-as-given-after-strip", R.lands_on_for(con, "r1", 4) == ["entity.b", "B"],
          R.lands_on_for(con, "r1", 4))


def main():
    for t in (test_a_reading_validates_against_the_live_ladder,
              test_a_path_written_in_lower_case_is_the_same_ladder,
              test_the_stub_is_gone_and_parse_took_its_place,
              test_the_round_trip,
              test_the_table_is_append_only,
              test_a_committed_turn_carries_its_readings,
              test_lands_on_round_trip):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("VERDICT: FAIL -> %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
