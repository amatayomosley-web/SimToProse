#!/usr/bin/env python3
"""test_read_api.py — proof for the orchestrator's typed read surface.

Asserts the contracts orchestrator-design.md §6A names:
  - reads are AS-OF a turn (a fact true at 40 asserted at 90 is confidently wrong)
  - `knows` is bounded to the character's own vault, never world-truth
  - every result carries a TRACE, so an EMPTY result is attributable — Vela's
    stage-attribution lesson: an unattributable "I don't know" is the worst
    failure a grounding system can have
  - malformed requests fail loud rather than returning empty (an empty result
    must always mean "nothing there", never "you asked wrong")

Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import db                                        # noqa: E402
from src.engine import read_api as R                             # noqa: E402

RUN = "run-read"


def _fixture(tmp):
    con = db.connect(os.path.join(tmp, "read.db"))
    con.execute("INSERT INTO runs(run_id, created_at, status, config) VALUES(?,?,?,?)",
                (RUN, "2026-07-24T00:00:00Z", "active", json.dumps({"catalog_version": 1})))
    for c in ("nessa", "corin"):
        con.execute("INSERT INTO characters(run_id, char_id, fixed, baseline) VALUES(?,?,?,?)",
                    (RUN, c, "{}", "{}"))
    con.execute("INSERT INTO turns(run_id, turn, actor, thought, action, tags, validation, committed_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (RUN, 10, "nessa", "he is lying", "says nothing",
                 json.dumps({"act": "conceal"}), json.dumps({"ok": 1}), "2026-07-24T00:00:00Z"))
    # state at 10 and 20 only — nothing at 15, so 15 must carry forward from 10
    for t, fear in ((10, 0.2), (20, 0.8)):
        con.execute("INSERT INTO current_state(run_id, char_id, turn, affect, condition) VALUES(?,?,?,?,?)",
                    (RUN, "nessa", t, json.dumps({"FEAR": fear}), json.dumps({"energy": 1.0})))
    con.execute("INSERT INTO acquisitions(run_id, char_id, turn, belief) VALUES(?,?,?,?)",
                (RUN, "nessa", 10, json.dumps({"claim": "the mill burned", "provenance": "lived"})))
    con.execute("INSERT INTO acquisitions(run_id, char_id, turn, belief) VALUES(?,?,?,?)",
                (RUN, "nessa", 30, json.dumps({"claim": "corin was there", "provenance": "told"})))
    con.execute("INSERT INTO acquisitions(run_id, char_id, turn, belief) VALUES(?,?,?,?)",
                (RUN, "corin", 10, json.dumps({"claim": "nothing happened"})))
    # A SECOND-ORDER ROW IS IN THE FIXTURE ON PURPOSE. Before 2026-08-24 this fixture had none —
    # the word "second" appeared nowhere in this file — and `edges` folded every row into one net,
    # so it summed "what nessa holds about corin" with "what nessa believes corin holds about her".
    # The suite stayed green straight through it: a guard with no fixture for the thing it guards.
    for t, axis, d, o in ((10, "trust", -0.2, "first"), (20, "trust", -0.3, "first"),
                          (20, "respect", 0.1, "first"), (20, "trust", 0.4, "second")):
        con.execute("INSERT INTO relationship_deltas(run_id, turn, perceiver, target, axis, delta, ord, cause_event) "
                    "VALUES(?,?,?,?,?,?,?,?)", (RUN, t, "nessa", "corin", axis, d, o, None))
    con.execute("INSERT INTO snapshots(run_id, as_of_turn, kind, key, value) VALUES(?,?,?,?,?)",
                (RUN, 20, "information", "mill", json.dumps({"known_to": ["nessa"]})))
    con.execute("INSERT INTO scenes(run_id, scene_no, label, pov, start_turn, end_turn) "
                "VALUES(?,?,?,?,?,?)", (RUN, 1, "the mill", "nessa", 5, 25))
    con.commit()
    return con


# --- said -----------------------------------------------------------------

def test_said_returns_the_turn_with_parsed_json(con):
    r = R.said(con, RUN, 10)
    assert r.found and len(r.rows) == 1, r.as_dict()
    assert r.rows[0]["thought"] == "he is lying", r.rows[0]
    assert r.rows[0]["tags"]["act"] == "conceal", "tags must arrive parsed, not as a string"


def test_said_miss_is_attributable(con):
    r = R.said(con, RUN, 999)
    assert not r.found
    assert any("latest committed turn" in s for s in r.trace), r.trace


# --- state: the as-of contract -------------------------------------------

def test_state_is_as_of_not_latest(con):
    """The trap this exists to prevent: reporting turn 20's fear when asked
    about turn 10."""
    r = R.state(con, RUN, "nessa", 10)
    assert r.rows[0]["affect"]["FEAR"] == 0.2, r.rows[0]
    r20 = R.state(con, RUN, "nessa", 20)
    assert r20.rows[0]["affect"]["FEAR"] == 0.8, r20.rows[0]


def test_state_carries_forward_and_says_so(con):
    r = R.state(con, RUN, "nessa", 15)
    assert r.rows[0]["turn"] == 10, r.rows[0]
    assert any("carried forward" in s for s in r.trace), r.trace


def test_state_before_any_row_is_empty_and_explains(con):
    r = R.state(con, RUN, "nessa", 0)
    assert not r.found
    assert any("no state row at or before" in s for s in r.trace), r.trace


def test_state_unregistered_character_says_so(con):
    r = R.state(con, RUN, "nobody", 10)
    assert not r.found
    assert any("not registered" in s for s in r.trace), r.trace


def test_state_carries_perspective(con):
    assert R.state(con, RUN, "nessa", 10).perspective == "char:nessa"


# --- knows: the perspective wall -----------------------------------------

def test_knows_is_bounded_to_that_character(con):
    r = R.knows(con, RUN, "nessa", 40)
    claims = [row["belief"]["claim"] for row in r.rows]
    assert "nothing happened" not in claims, "knows() leaked another character's vault"
    assert len(r.rows) == 2, claims


def test_knows_respects_as_of(con):
    r = R.knows(con, RUN, "nessa", 10)
    assert len(r.rows) == 1, [x["belief"] for x in r.rows]
    assert r.rows[0]["belief"]["claim"] == "the mill burned"


def test_knows_contains_filter_is_traced(con):
    r = R.knows(con, RUN, "nessa", 40, contains="corin")
    assert len(r.rows) == 1, r.rows
    assert any("filtered by contains" in s for s in r.trace), r.trace


def test_knows_miss_reports_total_held(con):
    r = R.knows(con, RUN, "nessa", 40, contains="dragons")
    assert not r.found
    assert any("belief(s) overall" in s for s in r.trace), r.trace


# --- edges ----------------------------------------------------------------

def test_edges_fold_net_by_axis_as_of(con):
    r = R.edges(con, RUN, "nessa", "corin", 20)
    assert len(r.rows) == 4, r.rows
    net = [s for s in r.trace if s.startswith("net by axis")][0]
    assert "-0.5" in net, net          # trust: -0.2 + -0.3, FIRST order only
    assert "0.1" in net, net           # respect


def test_edges_do_not_sum_the_two_orders(con):
    """The first-order net must not absorb a second-order delta.

    The fixture carries a +0.4 second-order trust row against -0.5 of first-order trust. Summed —
    which is what `edges` did until 2026-08-24 — the answer to "what has nessa's trust in corin
    done" comes out -0.1 instead of -0.5, an eighty-percent error built out of a real number about
    a different question.
    """
    r = R.edges(con, RUN, "nessa", "corin", 20)
    net = [s for s in r.trace if s.startswith("net by axis")][0]
    second = [s for s in r.trace if s.startswith("second order")][0]
    assert "-0.5" in net and "-0.1" not in net, net
    assert "0.4" in second, second
    assert all("ord" in row for row in r.rows), r.rows[0]


def test_edges_report_no_second_order_when_there_is_none(con):
    """A pair with only first-order movement must say so, not print an empty dict as a finding."""
    r = R.edges(con, RUN, "nessa", "corin", 10)
    second = [s for s in r.trace if s.startswith("second order")][0]
    assert "(none)" in second, second


def test_edges_as_of_excludes_later_deltas(con):
    r = R.edges(con, RUN, "nessa", "corin", 10)
    assert len(r.rows) == 1, r.rows


def test_edges_miss_is_attributable(con):
    r = R.edges(con, RUN, "corin", "nessa", 20)
    assert not r.found
    assert any("no recorded deltas" in s for s in r.trace), r.trace


# --- snapshot / scene -----------------------------------------------------

def test_snapshot_at_returns_parsed_value(con):
    r = R.snapshot_at(con, RUN, 20, kind="information")
    assert r.found and r.rows[0]["value"]["known_to"] == ["nessa"], r.rows


def test_snapshot_miss_lists_available_turns(con):
    r = R.snapshot_at(con, RUN, 11)
    assert not r.found
    assert any("persisted turns" in s and "20" in s for s in r.trace), r.trace


def test_scene_of_finds_containing_scene(con):
    r = R.scene_of(con, RUN, 10)
    assert r.found and r.rows[0]["scene_no"] == 1, r.rows


def test_scene_of_outside_boundaries_is_attributable(con):
    r = R.scene_of(con, RUN, 99)
    assert not r.found
    assert any("outside every recorded scene" in s for s in r.trace), r.trace


# --- fail loud ------------------------------------------------------------

def test_bad_as_of_raises_rather_than_returning_empty(con):
    """An empty result must always mean 'nothing there', never 'you asked wrong'."""
    for bad in ("14", 1.5, None, True, -1):
        try:
            R.state(con, RUN, "nessa", bad)
        except R.ReadError:
            continue
        raise AssertionError("state() accepted a bad as_of: %r" % (bad,))


def test_bad_turn_type_raises(con):
    for bad in ("10", None, 1.5):
        try:
            R.said(con, RUN, bad)
        except R.ReadError:
            continue
        raise AssertionError("said() accepted a bad turn: %r" % (bad,))


def test_every_result_serialises(con):
    for r in (R.said(con, RUN, 10), R.state(con, RUN, "nessa", 15),
              R.knows(con, RUN, "nessa", 40), R.edges(con, RUN, "nessa", "corin", 20),
              R.snapshot_at(con, RUN, 20), R.scene_of(con, RUN, 10)):
        d = r.as_dict()
        json.dumps(d)
        assert d["trace"], "every result must carry a trace"


def test_every_refusal_carries_a_REGISTERED_code(con):
    """The read tier joins the coded channel (2026-09-02).

    Small on purpose. This tier refuses only a malformed REQUEST — the argument contracts, plus the
    ONE scope question (`READ_RUN_UNKNOWN`) that the next test's principle itself calls malformed."""
    from src.engine import codes
    cases = [
        ("READ_RUN_UNKNOWN",      lambda: R.state(con, "no-such-run", "maren", 0)),
        ("READ_RUN_UNKNOWN",      lambda: R.said(con, "", 0)),
        ("READ_AS_OF_NOT_AN_INT", lambda: R.snapshot_at(con, RUN, "three")),
        ("READ_AS_OF_NEGATIVE",   lambda: R.snapshot_at(con, RUN, -1)),
        ("READ_TURN_NOT_AN_INT",  lambda: R.said(con, RUN, "x")),
        ("READ_PLACE_ID_EMPTY",   lambda: R.place(con, RUN, "   ", 0)),
    ]
    for want, call in cases:
        try:
            call()
            raise AssertionError("%s: the malformed request was ACCEPTED" % want)
        except R.ReadError as e:
            assert e.code == want, "expected %s, got %r" % (want, e.code)
            assert codes.is_registered(e.code), "%s is raised but not registered" % e.code

    # a bool is not an int here, and the check that lets one through is the classic
    try:
        R.said(con, RUN, True)
        raise AssertionError("a bool passed as a turn index")
    except R.ReadError as e:
        assert e.code == "READ_TURN_NOT_AN_INT", e.code


def test_a_MISS_is_still_not_an_ERROR(con):
    """THE LINE THIS TIER DRAWS, and the reason there is no READ_NOT_FOUND.

    A well-formed question about a turn that recorded nothing has a true answer: nothing. Coding
    that as a refusal would turn every honest absence into an error and push callers into
    try/except around normal reads — so a miss reports itself in the TRACE and returns no rows.

    Guarded because the conversion is exactly when someone would "finish the job" by adding a
    not-found code.

    THIS TEST WAS ITSELF WRONG until 2026-09-02: it passed `"r1"`, which is not this fixture's run,
    so the "honest miss" it certified was a miss on a run that DID NOT EXIST — the one absence that
    is not a true answer. It proved the opposite of its own point and stayed green, because nothing
    checked the run either. Reading `RUN` is the fix and `_known_run` is why it can no longer
    happen quietly."""
    res = R.snapshot_at(con, RUN, 999)
    assert not res.found, "a turn with nothing recorded returned rows"
    assert any("MISS" in t for t in res.trace), (
        "a miss must SAY so in the trace, not merely return empty: %r" % res.trace)

    # AN ALLOWLIST, NOT A SUBSTRING FILTER. Forbidding NOT_FOUND and MISSING was evadable by
    # synonym — READ_NO_SUCH_TURN, READ_EMPTY_RESULT and READ_ABSENT all walk straight past it, and
    # the whole point of this assertion is that it stands where someone would add exactly such a
    # code. So the family is CLOSED: a new READ_ code has to be argued for here, in this list, in
    # front of the paragraph saying why absences are not refusals.
    from src.engine import codes
    ALLOWED = {
        "READ_AS_OF_NOT_AN_INT", "READ_AS_OF_NEGATIVE",       # argument contracts
        "READ_TURN_NOT_AN_INT", "READ_PLACE_ID_EMPTY",
        "READ_RUN_UNKNOWN",     # the ONE scope question: an unknown run has no world to be absent from
    }
    read_codes = {c for c in codes.CODES if c.startswith("READ_")}
    assert read_codes, "the READ_ family vanished"
    assert read_codes == ALLOWED, (
        "the READ_ family changed: added %s, removed %s. Every code here refuses a malformed "
        "QUESTION; a code for an ABSENCE (however it is spelled — NOT_FOUND, NO_SUCH_X, EMPTY_X) "
        "would turn every honest miss into a refusal and put a try/except around every normal read."
        % (sorted(read_codes - ALLOWED) or "nothing", sorted(ALLOWED - read_codes) or "nothing"))

def main():
    tmp = tempfile.mkdtemp(prefix="swe_readapi_test_")
    con = None
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    try:
        con = _fixture(tmp)
        for t in tests:
            try:
                t(con)
                print("  PASS  %s" % t.__name__)
            except Exception as e:
                failed += 1
                print("  FAIL  %s: %s" % (t.__name__, e))
    finally:
        if con is not None:
            con.close()
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d/%d passed" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
