#!/usr/bin/env python3
"""test_citation.py — proof for the grounding gate's core (docs/grounding.md).

Asserts the contracts the design names:
  orchestrator-design.md §4  — the ENVELOPE / CLAIM shape this validates
  orchestrator-design.md §6  — NO-SIGNAL != REJECTION: `law:` is UNVERIFIABLE,
                               neither resolved nor denied
  orchestrator-design.md §9  — every namespace maps to a schema.sql table; and
                               THE CORRUPT CONTROL must DENY

The corrupt control is the load-bearing test. `coherence_probe.py --corrupt` MUST
print FAIL for the same reason: a guard without a negative control is
indistinguishable from a guard that cannot fire. If test_CORRUPT_CONTROL ever
passes an envelope, the grounding is theatre and this suite must go red.

Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import citation as C                              # noqa: E402
from src.engine import db                                         # noqa: E402

RUN = "run-cite"


def _fixture(tmp):
    """A minimal run carrying exactly one row per citable namespace."""
    con = db.connect(os.path.join(tmp, "cite.db"))
    con.execute("INSERT INTO runs(run_id, created_at, status, config) VALUES(?,?,?,?)",
                (RUN, "2026-07-24T00:00:00Z", "active", json.dumps({"catalog_version": 1})))
    con.execute("INSERT INTO characters(run_id, char_id, fixed, baseline) VALUES(?,?,?,?)",
                (RUN, "nessa", "{}", "{}"))
    con.execute("INSERT INTO turns(run_id, turn, actor, thought, action, tags, validation, committed_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (RUN, 14, "nessa", "she is lying", "says nothing", "{}", "{}", "2026-07-24T00:00:00Z"))
    con.execute("INSERT INTO events(run_id, turn, caused_at, effective_at, type, actor, payload) "
                "VALUES(?,?,?,?,?,?,?)", (RUN, 14, 14, 14, "deceive", "nessa", "{}"))
    con.execute("INSERT INTO scenes(run_id, scene_no, label, pov, start_turn, end_turn) "
                "VALUES(?,?,?,?,?,?)", (RUN, 2, "the mill", "nessa", 10, 20))
    con.execute("INSERT INTO acquisitions(run_id, char_id, turn, belief) VALUES(?,?,?,?)",
                (RUN, "nessa", 14, json.dumps({"claim": "the mill burned"})))
    con.execute("INSERT INTO current_state(run_id, char_id, turn, affect, condition) VALUES(?,?,?,?,?)",
                (RUN, "nessa", 14, json.dumps({"FEAR": 0.5}), "{}"))
    con.execute("INSERT INTO relationship_deltas(run_id, turn, perceiver, target, axis, delta, cause_event) "
                "VALUES(?,?,?,?,?,?,?)", (RUN, 14, "nessa", "corin", "trust", -0.2, 1))
    con.execute("INSERT INTO snapshots(run_id, as_of_turn, kind, key, value) VALUES(?,?,?,?,?)",
                (RUN, 14, "information", "mill", json.dumps({"known_to": ["nessa"]})))
    con.commit()
    return con


# ids are 1 because each table has exactly one autoincrement row in the fixture
REAL = ["turn:14", "event:1", "scene:2", "belief:nessa:1",
        "state:nessa:14", "edge:1", "snapshot:14:information:mill"]
FAKE = ["turn:999", "event:999", "scene:999", "belief:nessa:999",
        "state:nessa:999", "edge:999", "snapshot:999:information:mill"]


def _claim(mode, tokens):
    field = "cite" if mode == "cited" else "from"
    return {"text": "t", "mode": mode, field: tokens, "as_of": 14, "perspective": "world"}


def _env(kind, claims, unknowns=None):
    return {"kind": kind, "head": {}, "claims": claims, "unknowns": unknowns or []}


# --- parsing --------------------------------------------------------------

def test_parse_every_real_namespace(con):
    for tok in REAL:
        c = C.parse(tok)
        assert c.raw == tok, tok


def test_parse_rejects_malformed(con):
    for bad in ["", "   ", "nocolon", "turn", ":14", 17, None]:
        try:
            C.parse(bad)
        except C.CitationError:
            continue
        raise AssertionError("parse accepted malformed token %r" % (bad,))


def test_parse_rejects_unknown_namespace(con):
    try:
        C.parse("wizard:14")
    except C.CitationError:
        return
    raise AssertionError("parse accepted an unknown namespace")


# --- resolution: the three states -----------------------------------------

def test_every_real_citation_resolves(con):
    for tok in REAL:
        state, detail = C.resolve_one(con, RUN, tok)
        assert state == C.RESOLVED, "%s -> %s (%s)" % (tok, state, detail)


def test_every_fabricated_citation_is_unresolved(con):
    for tok in FAKE:
        state, _ = C.resolve_one(con, RUN, tok)
        assert state == C.UNRESOLVED, "%s -> %s (expected UNRESOLVED)" % (tok, state)


def test_law_is_unverifiable_not_resolved_and_not_unresolved(con):
    """NO-SIGNAL != REJECTION. The lore store is unbuilt; `law:` must be neither
    silently allowed nor silently denied. `entity:` and `law:` both LEFT this set
    once the bible store landed — see the tests below."""
    for tok in ["chronicle:sundering"]:
        state, detail = C.resolve_one(con, RUN, tok)
        assert state == C.UNVERIFIABLE, "%s -> %s" % (tok, state)
        assert detail, "unverifiable must explain why"


def test_wrong_arity_raises(con):
    for bad in ["turn:1:2", "belief:nessa", "snapshot:14:information"]:
        try:
            C.resolve_one(con, RUN, bad)
        except C.CitationError:
            continue
        raise AssertionError("resolve accepted wrong arity: %r" % bad)


def test_other_run_ids_do_not_resolve(con):
    state, _ = C.resolve_one(con, "some-other-run", "turn:14")
    assert state == C.UNRESOLVED, "citation leaked across runs"


# --- envelope verdicts ----------------------------------------------------

def test_clean_envelope_is_allowed(con):
    v = C.verify_envelope(_env("ANSWER", [_claim("cited", REAL)]), con, RUN)
    assert v.allowed, v.reason()
    assert v.checked == len(REAL), v.checked


def test_CORRUPT_CONTROL_fabricated_cites_must_DENY(con):
    """THE CONTROL. If this ever passes, the gate is inert and the grounding is
    theatre — exactly the dead-guard class coherence_probe.py --corrupt exists to
    catch. Do not weaken this test; fix the resolver."""
    env = _env("ANSWER", [_claim("cited", FAKE)])
    v = C.verify_envelope(env, con, RUN)
    assert not v.allowed, "CORRUPT CONTROL PASSED — the grounding gate is inert"
    assert len(v.failures) == len(FAKE), v.failures
    assert "no such row" in v.reason(), v.reason()


def test_one_bad_cite_among_good_ones_denies(con):
    env = _env("VERDICT", [_claim("cited", [REAL[0], "turn:999", REAL[1]])])
    v = C.verify_envelope(env, con, RUN)
    assert not v.allowed, "a single fabricated cite must deny the envelope"
    assert len(v.failures) == 1, v.failures


def test_derived_claim_with_unresolvable_from_denies(con):
    v = C.verify_envelope(_env("DIAGNOSIS", [_claim("derived", ["turn:999"])]), con, RUN)
    assert not v.allowed, "derived claims must ground their `from` refs"


def test_derived_claim_with_resolvable_from_is_allowed(con):
    v = C.verify_envelope(_env("DIAGNOSIS", [_claim("derived", ["turn:14"])]), con, RUN)
    assert v.allowed, v.reason()


def test_claim_with_no_support_denies(con):
    """A cited claim carrying no citation is the exact failure this gate is for —
    a verdict, not a crash."""
    v = C.verify_envelope(_env("ANSWER", [_claim("cited", [])]), con, RUN)
    assert not v.allowed, "an uncited 'cited' claim must deny"
    assert "no cite" in v.reason(), v.reason()


def test_unknowns_only_envelope_is_allowed_and_counted(con):
    """`unknown` is a first-class answer — the pressure valve that stops the
    orchestrator inventing. It must never be penalised."""
    env = _env("ANSWER", [], unknowns=["whether the mill has a night watch"])
    v = C.verify_envelope(env, con, RUN)
    assert v.allowed, v.reason()
    assert v.unknowns == 1, v.unknowns
    assert v.checked == 0, v.checked


def test_unverifiable_does_not_deny_but_is_surfaced(con):
    v = C.verify_envelope(_env("VERDICT", [_claim("cited", ["law:L3"])]), con, RUN)
    assert v.allowed, "a missing store must not act as a denial"
    assert len(v.unverifiable) == 1, v.unverifiable


def test_all_six_kinds_accepted(con):
    for kind in C.KINDS:
        v = C.verify_envelope(_env(kind, [_claim("cited", ["turn:14"])]), con, RUN)
        assert v.allowed, "%s: %s" % (kind, v.reason())


def test_malformed_envelope_raises_not_silently_allows(con):
    bad = [
        "not a dict",
        {"kind": "NOPE", "claims": []},
        {"kind": "ANSWER", "claims": "not a list"},
        {"kind": "ANSWER", "claims": [{"mode": "invented", "cite": []}]},
        {"kind": "ANSWER", "claims": [{"mode": "cited", "cite": "not a list"}]},
        {"kind": "ANSWER", "claims": [], "unknowns": "not a list"},
    ]
    for env in bad:
        try:
            C.verify_envelope(env, con, RUN)
        except C.CitationError:
            continue
        raise AssertionError("malformed envelope was accepted: %r" % (env,))


def test_verdict_serialises(con):
    v = C.verify_envelope(_env("ANSWER", [_claim("cited", FAKE[:1])]), con, RUN)
    d = v.as_dict()
    json.dumps(d)
    assert d["allowed"] is False and d["failures"], d


# --- entity: backed by the run's pinned bible (bible.py) ------------------

def test_entity_resolves_against_the_pinned_bible(con):
    """`entity:` used to be UNVERIFIABLE forever. With a bible pinned to the run
    it becomes exact: real ids resolve, fabricated ones do not."""
    from src.engine import bible
    world = {"world": "W", "people": [{"id": "marlo_clerk", "what": "the clerk"}],
             "locations": [{"id": "quay", "what": "the quay"}]}
    chars = {"nessa": {"fixed": {"name": "Nessa"}, "baseline": {}, "current": {}}}
    fp = bible.build(con, world, chars)
    con.execute("UPDATE runs SET config=? WHERE run_id=?",
                (json.dumps({"catalog_version": 1, bible.CONFIG_KEY: fp}), RUN))
    con.commit()
    try:
        for tok in ["entity:marlo_clerk", "entity:quay", "entity:nessa"]:
            state, detail = C.resolve_one(con, RUN, tok)
            assert state == C.RESOLVED, "%s -> %s (%s)" % (tok, state, detail)
        state, _ = C.resolve_one(con, RUN, "entity:marlo_clerkk")
        assert state == C.UNRESOLVED, "a near-miss entity must not resolve"
    finally:
        con.execute("UPDATE runs SET config=? WHERE run_id=?",
                    (json.dumps({"catalog_version": 1}), RUN))
        con.commit()


def test_law_resolves_against_the_pinned_bible(con):
    """`law:` left the unbacked set once bible_laws landed. A denial can now
    cite the rule it rests on."""
    from src.engine import bible
    world = {"world": "W", "laws": [{"id": "curfew", "domain": "legal", "modality": "FORBIDS",
                                     "statement": "No walking after the third bell."}]}
    chars = {"nessa": {"fixed": {"name": "Nessa"}, "baseline": {}, "current": {}}}
    fp = bible.build(con, world, chars)
    con.execute("UPDATE runs SET config=? WHERE run_id=?",
                (json.dumps({"catalog_version": 1, bible.CONFIG_KEY: fp}), RUN))
    con.commit()
    try:
        state, detail = C.resolve_one(con, RUN, "law:curfew")
        assert state == C.RESOLVED and "FORBIDS" in detail, (state, detail)
        state2, _ = C.resolve_one(con, RUN, "law:no-such-law")
        assert state2 == C.UNRESOLVED, state2
    finally:
        con.execute("UPDATE runs SET config=? WHERE run_id=?",
                    (json.dumps({"catalog_version": 1}), RUN))
        con.commit()


def test_entity_without_a_pinned_bible_is_unverifiable_not_unresolved(con):
    """No store is not "no such entity" — the three-state rule, applied to a run
    that predates bible pinning."""
    state, detail = C.resolve_one(con, RUN, "entity:anyone")
    assert state == C.UNVERIFIABLE, "%s (%s)" % (state, detail)


def main():
    tmp = tempfile.mkdtemp(prefix="swe_citation_test_")
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
