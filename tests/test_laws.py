#!/usr/bin/env python3
"""test_laws.py — computable denial: what the world makes impossible vs forbids.

THE LOAD-BEARING RULE (orchestrator-design.md §7.1): a gate that denied every
ILLEGAL act would make crime unwritable. The world says no in two different ways
and they must resolve differently:

  IMPOSSIBLE  physical/supernatural — it cannot occur   -> DENY the circumstance
  FORBIDS     legal/custom — it may not, but it can     -> ALLOW, attach the teeth

A character breaking a law is not a gate failure. It is the story. The gate's
job there is to make sure the CONSEQUENCE lands, not to prevent the act.

Second rule, from universal-law.md's known-vs-believed check: an `epistemic:
believed` law binds BEHAVIOUR, never POSSIBILITY. A world where people believe
the dead walk is not a world where they do, and the gate must never deny a
circumstance because a character holds a false belief.

Stdlib only, script-style. Exit 0 = all pass.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bible, db                                  # noqa: E402

CHARS = {"vesk": {"fixed": {"name": "Vesk"}, "baseline": {}, "current": {}}}


def _world(laws=None, **extra):
    w = {"world": "Carrowport", "locations": [{"id": "quay", "what": "the quay"},
                                              {"id": "hall", "what": "the hall"}]}
    if laws is not None:
        w["laws"] = laws
    w.update(extra)
    return w


def _law(lid, modality, **kw):
    base = {"id": lid, "domain": kw.pop("domain", "legal"), "modality": modality,
            "statement": kw.pop("statement", "a rule about %s" % lid)}
    base.update(kw)
    return base


def _con(tmp):
    return db.connect(os.path.join(tmp, "laws.db"))


def _rows(con, fp):
    return [dict(r) for r in con.execute(
        "SELECT * FROM bible_laws WHERE fingerprint=? ORDER BY law_id", (fp,))]


def _authored(con, fp):
    """Only what the author wrote — the blueprint defaults filtered out. Tests
    about authored content assert through this; tests about the defaults assert
    on them by name."""
    return [r for r in _rows(con, fp) if not r["law_id"].startswith("default-")]


def _defaults(con, fp):
    return [r for r in _rows(con, fp) if r["law_id"].startswith("default-")]


# --- projection -----------------------------------------------------------

def test_laws_project_into_the_store(con):
    fp = bible.build(con, _world([_law("curfew", "FORBIDS", act="move", teeth="the watch detains you")]), CHARS)
    rows = _authored(con, fp)
    assert len(rows) == 1 and rows[0]["law_id"] == "curfew", rows
    assert rows[0]["teeth"] == "the watch detains you", rows[0]


def test_a_book_with_no_laws_is_not_an_error(con):
    """Every existing book, including the live one, has none. A store that
    refuses to build without content cannot be adopted incrementally.

    It is no longer EMPTY, though: an unauthored world inherits the blueprint's
    mundane defaults (universal-law.md:10, 'the bias is no, unless'). Nothing
    downstream is denied that was allowed before — only the acts the mundane
    world never permitted in the first place."""
    fp = bible.build(con, _world(), CHARS)
    assert _authored(con, fp) == [], "an unauthored world invented an authored law"
    assert bible.verdict_for(con, fp, act="move")["allowed"] is True


def test_malformed_laws_fail_loud(con):
    bad = [
        [_law("x", "MAYBE")],                                   # unknown modality
        [dict(_law("x", "FORBIDS"), domain="vibes")],            # unknown domain
        [dict(_law("x", "FORBIDS"), epistemic="perhaps")],       # unknown epistemic
        [dict(_law("x", "FORBIDS"), domain="physics")],          # near-miss domain
        [{"modality": "FORBIDS", "domain": "legal", "statement": "s"}],   # no id
        [{"id": "x", "modality": "FORBIDS", "domain": "legal"}],          # no statement
        [_law("dup", "FORBIDS"), _law("dup", "PERMITS")],        # duplicate id
        "not-a-list",
    ]
    for laws in bad:
        try:
            bible.build(con, _world(laws), CHARS)
        except bible.BibleError:
            continue
        raise AssertionError("malformed law accepted: %r" % (laws,))


# --- THE MODALITY RULE ----------------------------------------------------

def test_IMPOSSIBLE_denies(con):
    fp = bible.build(con, _world([
        _law("no-flight", "IMPOSSIBLE", domain="physical", act="fly",
             statement="People cannot fly.")]), CHARS)
    v = bible.verdict_for(con, fp, act="fly")
    assert v["allowed"] is False, v
    assert v["denied_by"] == ["no-flight"] and "cannot fly" in v["reason"], v


def test_FORBIDS_ALLOWS_and_attaches_teeth(con):
    """THE CONTROL for this design. If a FORBIDS law ever denies, crime becomes
    unwritable and the engine has stopped being a story engine."""
    fp = bible.build(con, _world([
        _law("curfew", "FORBIDS", act="move", teeth="the watch detains you",
             statement="No one may walk after the third bell.")]), CHARS)
    v = bible.verdict_for(con, fp, act="move")
    assert v["allowed"] is True, "A FORBIDS law DENIED — crime is now unwritable: %s" % v
    assert v["violations"] == ["curfew"], v
    assert v["teeth"] == ["the watch detains you"], v


def test_REQUIRES_allows_but_records_the_violation(con):
    fp = bible.build(con, _world([_law("tithe", "REQUIRES", act="trade", teeth="the guild fines you")]), CHARS)
    v = bible.verdict_for(con, fp, act="trade")
    assert v["allowed"] is True and v["violations"] == ["tithe"], v


def test_PERMITS_overrides_a_forbid(con):
    fp = bible.build(con, _world([
        _law("curfew", "FORBIDS", act="move", teeth="detained"),
        _law("writ", "PERMITS", act="move", statement="A physician's writ permits night travel.")]), CHARS)
    v = bible.verdict_for(con, fp, act="move")
    assert v["allowed"] is True and v["permitted_by"] == ["writ"], v
    assert v["violations"] == [], "a permit must clear the violation, not merely coexist: %s" % v


def test_PERMITS_also_clears_an_impossible(con):
    fp = bible.build(con, _world([
        _law("no-flight", "IMPOSSIBLE", domain="physical", act="fly"),
        _law("winged", "PERMITS", domain="supernatural", act="fly",
             statement="The wing-born fly.")]), CHARS)
    assert bible.verdict_for(con, fp, act="fly")["allowed"] is True


def test_PERMITS_excepts_scopes_the_disarm(con):
    """A scoped permit disarms ONLY the law it names — the rite that excepts the
    curfew must not also cancel the weapons ban on the same act."""
    fp = bible.build(con, _world([
        _law("curfew", "FORBIDS", act="move", teeth="detained"),
        _law("no-arms", "FORBIDS", act="move", teeth="disarmed at the gate"),
        _law("writ", "PERMITS", act="move", excepts=["curfew"],
             statement="A physician's writ permits night travel.")]), CHARS)
    v = bible.verdict_for(con, fp, act="move")
    assert v["allowed"] is True
    assert v["violations"] == ["no-arms"], "unnamed law must keep its teeth: %s" % v
    assert v["teeth"] == ["disarmed at the gate"], v
    assert v["permitted_by"] == ["writ"], v


def test_PERMITS_excepts_must_name_known_ids(con):
    try:
        bible.build(con, _world([
            _law("writ", "PERMITS", act="move", excepts=["no-such-law"])]), CHARS)
    except bible.BibleError as e:
        assert "no-such-law" in str(e)
    else:
        raise AssertionError("excepts citing an unknown law id must fail loud")


def test_excepts_on_a_non_permit_fails_loud(con):
    try:
        bible.build(con, _world([
            _law("curfew", "FORBIDS", act="move", excepts=["anything"])]), CHARS)
    except bible.BibleError as e:
        assert "PERMITS" in str(e)
    else:
        raise AssertionError("excepts on a FORBIDS row must fail loud")


# --- the epistemic wall ---------------------------------------------------

def test_a_believed_law_never_denies(con):
    """People BELIEVE the dead walk. They do not. The gate must not deny a
    circumstance because a character holds a false belief."""
    fp = bible.build(con, _world([
        _law("dead-walk", "IMPOSSIBLE", domain="supernatural", act="rest",
             epistemic="known-false", statement="The dead walk on the third night.")]), CHARS)
    v = bible.verdict_for(con, fp, act="rest")
    assert v["allowed"] is True, "a merely BELIEVED law constrained possibility: %s" % v
    assert v["denied_by"] == [] and v["violations"] == [], v
    assert v["considered"] == ["dead-walk"], "it must still be VISIBLE, just not binding"


# --- scope ----------------------------------------------------------------

def test_location_scope_is_honoured(con):
    fp = bible.build(con, _world([
        _law("quay-curfew", "IMPOSSIBLE", domain="physical", act="move", location_scope="quay")]), CHARS)
    assert bible.verdict_for(con, fp, act="move", location="quay")["allowed"] is False
    assert bible.verdict_for(con, fp, act="move", location="hall")["allowed"] is True


def test_unscoped_law_bears_everywhere(con):
    fp = bible.build(con, _world([_law("gravity", "IMPOSSIBLE", domain="physical", act="fly")]), CHARS)
    for loc in ("quay", "hall", None):
        assert bible.verdict_for(con, fp, act="fly", location=loc)["allowed"] is False, loc


def test_a_law_on_another_act_does_not_bear(con):
    fp = bible.build(con, _world([_law("no-flight", "IMPOSSIBLE", domain="physical", act="fly")]), CHARS)
    v = bible.verdict_for(con, fp, act="speak")
    assert v["allowed"] is True and v["considered"] == [], v


# --- isolation + citation -------------------------------------------------

def test_laws_do_not_leak_across_bibles(con):
    fp1 = bible.build(con, _world([_law("curfew", "FORBIDS", act="move")]), CHARS)
    fp2 = bible.build(con, _world([_law("other", "FORBIDS", act="move")]), CHARS)
    assert fp1 != fp2
    assert bible.law_exists(con, fp1, "curfew")[0]
    assert not bible.law_exists(con, fp2, "curfew")[0], "law leaked across bibles"


def test_law_exists_is_exact(con):
    fp = bible.build(con, _world([_law("curfew", "FORBIDS", act="move")]), CHARS)
    ok, detail = bible.law_exists(con, fp, "curfew")
    assert ok and "FORBIDS" in detail, detail
    assert not bible.law_exists(con, fp, "curfewe")[0], "a near-miss law must not resolve"


def test_no_bible_is_not_no_law(con):
    ok, detail = bible.law_exists(con, None, "curfew")
    assert not ok and "no bible" in detail, detail


# --- blueprint alignment (universal-law.md) -------------------------------

def test_all_five_universal_law_domains_are_accepted(con):
    """universal-law.md names five step-1 domains (A-E). An earlier enum held
    only two of them and silently rejected laws about souls, fate or cosmology."""
    laws = [_law("l-%s" % d, "IMPOSSIBLE", domain=d, act="a-%s" % d)
            for d in ("physical", "supernatural", "persons", "fate", "cosmology")]
    fp = bible.build(con, _world(laws), CHARS)
    assert len(_authored(con, fp)) == 5, _authored(con, fp)
    for d in ("legal", "custom", "economic"):      # step-4 domains still accepted
        assert bible.build(con, _world([_law("s-%s" % d, "FORBIDS", domain=d)]), CHARS)


def test_contested_unknowable_is_undecidable_not_allowed(con):
    """THE THIRD EPISTEMIC VALUE. The author DELIBERATELY refused to fix whether
    this is true. Treating it as allowed invents a fact they withheld — the same
    no-signal-is-not-a-verdict rule the citation resolver runs on."""
    fp = bible.build(con, _world([
        _law("divine-justice", "IMPOSSIBLE", domain="fate", act="escape",
             epistemic="contested-unknowable",
             statement="The unjust never escape the god's eye.")]), CHARS)
    v = bible.verdict_for(con, fp, act="escape")
    assert v["undecidable"] is True, "a contested law was silently resolved: %s" % v
    assert v["denied_by"] == [], v
    assert v["undecided_by"] == ["divine-justice"], v


def test_known_true_still_binds_alongside_a_contested_one(con):
    fp = bible.build(con, _world([
        _law("gravity", "IMPOSSIBLE", domain="physical", act="fly"),
        _law("omens", "IMPOSSIBLE", domain="fate", act="fly", epistemic="contested-unknowable")]), CHARS)
    v = bible.verdict_for(con, fp, act="fly")
    assert v["allowed"] is False and v["denied_by"] == ["gravity"], v
    assert v["undecidable"] is False, "a real denial outranks an undecided one: %s" % v


def test_legacy_epistemic_spellings_still_load(con):
    """`true`/`believed` were the first spelling. They alias rather than break
    any book already authored against them."""
    fp = bible.build(con, _world([
        _law("a", "IMPOSSIBLE", domain="physical", act="fly", epistemic="true"),
        _law("b", "IMPOSSIBLE", domain="supernatural", act="rest", epistemic="believed")]), CHARS)
    rows = {r["law_id"]: r["epistemic"] for r in _authored(con, fp)}
    assert rows == {"a": "known-true", "b": "known-false"}, rows
    assert bible.verdict_for(con, fp, act="fly")["allowed"] is False
    assert bible.verdict_for(con, fp, act="rest")["allowed"] is True


# --- the blueprint's defaults (universal-law.md:10, "the bias is no, unless") --

def test_an_unauthored_world_inherits_the_mundane_defaults(con):
    """The guide does not hand the author a blank world. It hands them the
    mundane one and asks which deviations the premise justifies."""
    fp = bible.build(con, _world(), CHARS)
    rows = _defaults(con, fp)
    assert len(rows) == 5, [r["law_id"] for r in rows]
    for r in rows:
        assert "universal-law.md" in r["source_note"], r
        assert r["epistemic"] == "known-true", r
        assert r["act"], "a default with no act can never be reached by _applies()"


def test_every_step_one_domain_has_exactly_one_default(con):
    """THE ENUMERATION CHECK the previous gate lacked. universal-law.md names
    five step-1 domains (A-E); citing the doc is not conformance to it, so this
    walks the doc's vocabulary and demands the store cover all of it."""
    fp = bible.build(con, _world(), CHARS)
    got = sorted(r["domain"] for r in _defaults(con, fp))
    assert got == ["cosmology", "fate", "persons", "physical", "supernatural"], got


def test_an_authored_law_suppresses_its_default(con):
    """The sharp case: a world where people CAN fly but MAY NOT. If the default
    survived, its IMPOSSIBLE would deny the act outright and the author's
    FORBIDS — the whole story — would be silently unreachable."""
    fp = bible.build(con, _world([
        _law("skyfolk", "FORBIDS", domain="physical", act="fly",
             statement="None may take the air above the quay.",
             teeth="the wardens put an arrow in you")]), CHARS)
    assert [r["law_id"] for r in _defaults(con, fp) if r["act"] == "fly"] == [], \
        "a blueprint default overrode the author"
    v = bible.verdict_for(con, fp, act="fly")
    assert v["allowed"] is True, v
    assert v["teeth"] == ["the wardens put an arrow in you"], v


def test_defaults_can_be_switched_off(con):
    """A world whose step 1 is fully authored wants no phantom rules."""
    fp = bible.build(con, _world(None, blueprint_defaults=False), CHARS)
    assert _defaults(con, fp) == []
    assert bible.verdict_for(con, fp, act="fly")["allowed"] is True


def test_a_default_denial_names_itself_as_a_default(con):
    """Silent seeding would be inventing facts the author withheld. A refusal
    must be traceable to the blueprint, so the author knows where to look."""
    fp = bible.build(con, _world(), CHARS)
    v = bible.verdict_for(con, fp, act="resurrect")
    assert v["allowed"] is False and v["denied_by"] == ["default-death-is-final"], v
    ok, detail = bible.law_exists(con, fp, "default-death-is-final")
    assert ok and "IMPOSSIBLE" in detail, detail


# --- completeness: what the blueprint REQUIRES an answer to -----------------

def test_the_switches_must_be_answered(con):
    """universal-law.md:12 — the switches are the exception to 'settle only
    what's levered'. Everything downstream forks on them."""
    rep = bible.completeness(_world())
    assert rep["complete"] is False
    assert sorted(p["switch"] for p in rep["problems"]
                  if p["code"] == "switch-unanswered") == ["beings", "divine", "magic"], rep


def test_a_fully_answered_mundane_world_is_complete(con):
    rep = bible.completeness(_world(
        [_law("curfew", "FORBIDS", act="move", teeth="the watch detains you")],
        switches={"magic": False, "divine": False, "beings": False}))
    assert rep["complete"] is True, rep["problems"]


def test_a_world_that_answers_yes_and_bounds_it_is_complete(con):
    rep = bible.completeness(_world([
        _law("witchcraft", "PERMITS", domain="supernatural", act="cast",
             epistemic="known-true", teeth="it costs a year of your life")],
        switches={"magic": True, "divine": False, "beings": False}))
    assert rep["complete"] is True, rep["problems"]


# --- THE CORRUPT CONTROLS: these MUST come back red ------------------------

def test_corrupt_a_power_that_exists_with_nothing_bounding_it_is_flagged(con):
    """universal-law.md:18 — 'a power with no stated limit is the director's
    get-out-of-jail card and makes the probe hollow.' If this passes, the
    completeness check is decorative."""
    rep = bible.completeness(_world(
        [_law("curfew", "FORBIDS", act="move")],
        switches={"magic": True, "divine": False, "beings": False}))
    assert rep["complete"] is False, "magic exists and nothing bounds it — this must not pass"
    assert [p["code"] for p in rep["problems"]] == ["unbounded-switch"], rep


def test_corrupt_a_supernatural_law_with_no_epistemic_is_flagged(con):
    """universal-law.md:19 — omitting it binds the law as known-true, fixing a
    ground truth the author may never have chosen."""
    rep = bible.completeness(_world(
        [_law("the-drowned-speak", "IMPOSSIBLE", domain="supernatural", act="commune")],
        switches={"magic": False, "divine": False, "beings": True}))
    assert rep["complete"] is False
    codes = [p["code"] for p in rep["problems"]]
    assert "epistemic-unstated" in codes, rep


def test_strict_build_refuses_a_world_that_has_answered_nothing(con):
    try:
        bible.build(con, _world(), CHARS, strict=True)
    except bible.BibleError as e:
        assert "universal-law.md" in str(e), e
    else:
        raise AssertionError("strict build accepted an unanswered world")


def test_strict_build_is_off_by_default_so_the_live_book_still_runs(con):
    """The live book has zero laws. A store that cannot be adopted
    incrementally does not get adopted."""
    assert bible.build(con, _world(), CHARS)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        tmp = tempfile.mkdtemp(prefix="swe_laws_")
        con = None
        try:
            con = _con(tmp)
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
