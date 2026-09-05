#!/usr/bin/env python3
"""test_bible.py — the run pins the bible it ran against, and entities are exact.

Two contracts:
  1. REPLAY HONESTY. Before this, a run recorded nothing identifying its bible,
     so editing a character sheet mid-book silently changed what earlier turns
     were computed from. `Ledger.resume` could not see it — it asserts the fold
     of the event LOG is deterministic, not that the INPUTS are unchanged.
  2. EXACT ENTITY EXISTENCE (orchestrator-design.md §7.1). "Does this person
     exist" must be set-membership, never similarity: a near-miss would resolve
     a fabricated entity to a real one that merely looks like it.

Stdlib only, script-style. Exit 0 = all pass.
"""
import io
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bible, db                                  # noqa: E402

RUN = "run-bible"
OLD_RUN = "run-legacy"

WORLD = {
    "world": "Carrowport",
    "people": [{"id": "marlo_clerk", "what": "the countinghouse clerk"},
               {"id": "sella", "what": "the harbourmaster"}],
    "locations": [{"id": "countinghouse", "what": "on the quay"}],
}
CHARS = {"vesk": {"fixed": {"name": "Vesk"}, "baseline": {}, "current": {}}}


def _fresh(tmp, name="b.db"):
    con = db.connect(os.path.join(tmp, name))
    con.execute("INSERT INTO runs(run_id, created_at, status, config) VALUES(?,?,?,?)",
                (OLD_RUN, "2026-01-01T00:00:00Z", "active",
                 json.dumps({"catalog_version": 1})))          # predates pinning
    con.commit()
    return con


def _pin(con, run_id, fp):
    con.execute("INSERT INTO runs(run_id, created_at, status, config) VALUES(?,?,?,?)",
                (run_id, "2026-07-24T00:00:00Z", "active",
                 json.dumps({"catalog_version": 1, bible.CONFIG_KEY: fp})))
    con.commit()


# --- fingerprint determinism ---------------------------------------------

def test_fingerprint_is_deterministic(con):
    assert bible.fingerprint(WORLD, CHARS) == bible.fingerprint(WORLD, CHARS)


def test_key_order_does_not_change_the_fingerprint(con):
    reordered = {k: WORLD[k] for k in reversed(list(WORLD))}
    assert bible.fingerprint(reordered, CHARS) == bible.fingerprint(WORLD, CHARS), \
        "fingerprint must be order-independent or every reload reads as drift"


def test_any_content_change_changes_the_fingerprint(con):
    base = bible.fingerprint(WORLD, CHARS)
    w2 = json.loads(json.dumps(WORLD)); w2["season"] = "storm"
    assert bible.fingerprint(w2, CHARS) != base, "world edit went undetected"
    c2 = json.loads(json.dumps(CHARS)); c2["vesk"]["baseline"]["skills"] = {"guile": 3}
    assert bible.fingerprint(WORLD, c2) != base, "character edit went undetected"


def test_non_serialisable_fails_loud(con):
    try:
        bible.fingerprint({"x": {1, 2}}, CHARS)
    except bible.BibleError:
        return
    raise AssertionError("a non-JSON bible should fail loud, not hash silently")


# --- build ----------------------------------------------------------------

def test_build_projects_all_three_entity_kinds(con):
    fp = bible.build(con, WORLD, CHARS)
    rows = con.execute("SELECT kind, entity_id FROM bible_entities WHERE fingerprint=? "
                       "ORDER BY kind, entity_id", (fp,)).fetchall()
    got = [(r["kind"], r["entity_id"]) for r in rows]
    assert ("character", "vesk") in got, got
    assert ("person", "marlo_clerk") in got and ("person", "sella") in got, got
    assert ("location", "countinghouse") in got, got
    assert len(got) == 4, got


def test_rebuild_is_idempotent(con):
    fp = bible.build(con, WORLD, CHARS)
    before = con.execute("SELECT COUNT(*) c FROM bible_entities WHERE fingerprint=?", (fp,)).fetchone()["c"]
    again = bible.build(con, WORLD, CHARS)
    after = con.execute("SELECT COUNT(*) c FROM bible_entities WHERE fingerprint=?", (fp,)).fetchone()["c"]
    n_bibles = con.execute("SELECT COUNT(*) c FROM bibles WHERE fingerprint=?", (fp,)).fetchone()["c"]
    assert again == fp and before == after and n_bibles == 1, (before, after, n_bibles)


# --- entity existence: exact ---------------------------------------------

def test_real_entity_resolves_fabricated_does_not(con):
    fp = bible.build(con, WORLD, CHARS)
    ok, detail = bible.entity_exists(con, fp, "marlo_clerk")
    assert ok and "clerk" in detail, detail
    ok2, _ = bible.entity_exists(con, fp, "marlo_clerkk")
    assert not ok2, "a near-miss must NOT resolve — that is the whole point of exactness"


def test_kind_filter_is_honoured(con):
    fp = bible.build(con, WORLD, CHARS)
    assert bible.entity_exists(con, fp, "vesk", kind="character")[0]
    assert not bible.entity_exists(con, fp, "vesk", kind="location")[0]


def test_unknown_kind_fails_loud(con):
    fp = bible.build(con, WORLD, CHARS)
    try:
        bible.entity_exists(con, fp, "vesk", kind="wizard")
    except bible.BibleError:
        return
    raise AssertionError("an unknown entity kind should fail loud")


def test_entities_do_not_leak_across_bibles(con):
    fp1 = bible.build(con, WORLD, CHARS)
    w2 = json.loads(json.dumps(WORLD))
    w2["people"] = [{"id": "someone_else", "what": "a stranger"}]
    fp2 = bible.build(con, w2, CHARS)
    assert fp1 != fp2
    assert bible.entity_exists(con, fp1, "marlo_clerk")[0]
    assert not bible.entity_exists(con, fp2, "marlo_clerk")[0], "entity leaked across bibles"


def test_no_bible_is_not_no_entity(con):
    ok, detail = bible.entity_exists(con, None, "marlo_clerk")
    assert not ok and "no bible" in detail, detail


# --- run pinning ----------------------------------------------------------

def test_for_run_returns_the_pinned_bible(con):
    fp = bible.build(con, WORLD, CHARS)
    _pin(con, RUN, fp)
    got = bible.for_run(con, RUN)
    assert got is not None and got[0] == fp, got
    assert got[1]["world"] == "Carrowport" and "vesk" in got[2]


def test_legacy_run_returns_none_not_an_error(con):
    """The book's 34 existing runs predate pinning and must stay readable."""
    assert bible.for_run(con, OLD_RUN) is None
    assert bible.for_run(con, "no-such-run") is None


# --- drift detection ------------------------------------------------------

def test_drift_detected_when_the_bible_changes(con):
    fp = bible.build(con, WORLD, CHARS)
    _pin(con, RUN, fp)
    d, detail = bible.drifted(con, RUN, WORLD, CHARS)
    assert not d, detail
    edited = json.loads(json.dumps(CHARS))
    edited["vesk"]["baseline"]["skills"] = {"guile": 3}
    d2, detail2 = bible.drifted(con, RUN, WORLD, edited)
    assert d2 and "drifted" in detail2, detail2


def test_both_resume_paths_actually_call_it(con):
    """DETECTION WITH NO CALLER IS NOT DETECTION.

    Until 2026-08-24 `bible.drifted` was invoked from this file and nowhere else — CLAUDE.md hard
    rule 1 advertised it ("`bible.drifted()` detects; it does not abort"), both scripts PINNED a
    fingerprint on every run, and neither ever COMPARED one. The failure the mechanism exists for,
    a mid-book edit silently changing what later turns are computed from, stayed invisible in
    practice. Same shape as `verdict_for`, which `scripts/scene.py` memorializes in its own comment.

    The other half this pins is the false positive found the first time it ran: `scripts/direct.py`
    pins `bible.build(con, world, chars)` — the whole book's cast — so comparing `{char_id: char}`
    reported drift on every resume of an untouched book. A warning that always fires is noise.
    """
    import re
    for script in ("scene.py", "direct.py"):
        src = io.open(os.path.join(REPO, "scripts", script), encoding="utf-8").read()
        assert "bible.drifted(" in src, "%s never calls bible.drifted" % script
        call = re.search(r"bible\.drifted\(([^)]*)\)", src)
        assert call, "%s: no parseable drifted() call" % script
        args = call.group(1)
        assert "{" not in args, (
            "%s compares a hand-built dict %r, not the cast it pinned — this is the "
            "always-fires false positive" % (script, args))
        # the call must sit on the resume branch, not somewhere it can never run
        assert src.index("if args.resume:") < src.index("bible.drifted("),             "%s calls drifted() outside the resume branch" % script


def test_drift_is_silent_for_legacy_runs(con):
    d, detail = bible.drifted(con, OLD_RUN, WORLD, CHARS)
    assert not d and "predates" in detail, detail


# --- the pin governs the PER-TURN law check, not just the pre-flight -------

# scripts/scene.py's `_law_events` ran `bible.build(led.con, world, chars)` — fingerprinting
# whatever world was in memory — while `run_scene`'s pre-flight forty lines below read the run's
# PINNED bible. On a resumed run whose notes were edited between sessions the two disagree, so one
# scene adjudicated its pre-flight against the pin and its per-turn acts against the edited world.
# Contract 1 of this file, applied one layer down: a run is answerable to the bible it pinned.

_LAW_WORLD = dict(WORLD, laws=[{"id": "no-smuggling", "domain": "legal", "modality": "FORBIDS",
                                "statement": "Goods pass the counting-house or they do not pass.",
                                "act": "smuggle", "teeth": "the harbourmaster takes the cargo"}])
_EDITED_WORLD = dict(WORLD, laws=[])          # the author deleted the law between sessions


def _ledger_over(con):
    """A real Ledger on the same file the harness opened — not a shim.

    `_law_events` touches `led.con` and `led.run_config` only, but the point of the test is the
    contract between scene.py and the REAL accessor, so a stand-in would assert nothing.
    """
    from src.engine.ledger import Ledger
    path = con.execute("PRAGMA database_list").fetchall()[0][2]
    return Ledger(path)


def _law_event_payloads(led, run_id, world):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "swe_scene_under_test", os.path.join(REPO, "scripts", "scene.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    evs = mod._law_events(led, run_id, world, CHARS, {"act": "smuggle"}, "vesk")
    return [e.payload for e in evs]


def test_law_check_reads_the_pin_not_the_edited_world(con):
    """THE DEFECT. Pinned to a bible that forbids the act; the in-memory world no longer does."""
    fp_pinned = bible.build(con, _LAW_WORLD, CHARS)
    _pin(con, RUN, fp_pinned)
    assert bible.fingerprint(_EDITED_WORLD, CHARS) != fp_pinned,         "fixture is inert: the edit must actually change the fingerprint"
    led = _ledger_over(con)
    try:
        payloads = _law_event_payloads(led, RUN, _EDITED_WORLD)
    finally:
        led.con.close()
    assert any("no-smuggling" in (p.get("laws") or []) for p in payloads),         "the pinned law did not fire — the check used the edited world: %r" % (payloads,)


def test_an_unpinned_run_still_falls_back_to_the_loaded_world(con):
    """THE CONTROL, and the reason the fallback stays. OLD_RUN's config predates pinning."""
    bible.build(con, _LAW_WORLD, CHARS)         # present in the DB, but NOT pinned to this run
    led = _ledger_over(con)
    try:
        payloads = _law_event_payloads(led, OLD_RUN, _EDITED_WORLD)
    finally:
        led.con.close()
    assert not any("no-smuggling" in (p.get("laws") or []) for p in payloads),         "an unpinned run must adjudicate the world it loaded, not a stray bible: %r" % (payloads,)


# --- every BIBLE_ refusal, EXECUTED --------------------------------------------------------------
#
# `tests/test_errors.py` proves by PARSING that this module carries no prose raise and that every
# registered code is raised somewhere. Neither of those runs a line of it: a code can be registered,
# spelled right at the raise, and wired to a condition that never fires, and both scans stay green.
#
# The table is checked AGAINST the registry, so a new BIBLE_ code with no executing case is red —
# that is the direction that fails silent if nobody looks.

def _law(**over):
    """A VALID law. Every case below breaks exactly one thing about it."""
    row = {"id": "L1", "statement": "no one flies", "domain": "physical", "modality": "IMPOSSIBLE"}
    row.update(over)
    return row


def _bible_cases(con):
    from src.engine import bible as B
    return {
        "BIBLE_WORLD_NOT_A_DICT":        lambda: B.fingerprint("not a world", {}),
        "BIBLE_CHARACTERS_NOT_A_DICT":   lambda: B.fingerprint({}, "not characters"),
        "BIBLE_NOT_JSON_SERIALIZABLE":   lambda: B.fingerprint({"x": {1, 2}}, {}),
        "BIBLE_LAWS_FIELD_NOT_A_LIST":   lambda: B._authored_laws({"laws": "nope"}),
        "BIBLE_LAW_ENTRY_NOT_A_DICT":    lambda: B._authored_laws({"laws": ["nope"]}),
        "BIBLE_LAW_ID_MISSING":          lambda: B._authored_laws({"laws": [_law(id="")]}),
        "BIBLE_LAW_STATEMENT_MISSING":   lambda: B._authored_laws({"laws": [_law(statement="")]}),
        "BIBLE_LAW_DOMAIN_UNKNOWN":      lambda: B._authored_laws({"laws": [_law(domain="vibes")]}),
        "BIBLE_LAW_MODALITY_UNKNOWN":    lambda: B._authored_laws({"laws": [_law(modality="MAYBE")]}),
        "BIBLE_LAW_EPISTEMIC_UNKNOWN":   lambda: B._authored_laws({"laws": [_law(epistemic="dubious")]}),
        "BIBLE_LAW_EXCEPTS_NOT_PERMITS": lambda: B._authored_laws({"laws": [_law(excepts=["L2"])]}),
        "BIBLE_LAW_EXCEPTS_EMPTY":       lambda: B._authored_laws(
            {"laws": [_law(modality="PERMITS", excepts=[])]}),
        "BIBLE_LAW_ID_DUPLICATE":        lambda: B._authored_laws({"laws": [_law(), _law()]}),
        "BIBLE_LAW_EXCEPTS_UNKNOWN_ID":  lambda: B._project_laws(
            {"laws": [_law(modality="PERMITS", excepts=["no-such-law"])]}),
        "BIBLE_ENTITY_KIND_UNKNOWN":     lambda: B.entity_exists(con, "fp", "e", kind="banana"),
        "BIBLE_WORLD_STEP1_INCOMPLETE":  lambda: B.build(con, {}, {}, strict=True),
        # the refusal that the bible/law split existed to unblock: it lives WITH the ruling now,
        # not restated in scripts/scene.py's own words.
        "BIBLE_ACT_IMPOSSIBLE":          lambda: B.require_allowed(
            {"allowed": False, "denied_by": ["no-flight"], "reason": "people do not fly"}, "fly"),
    }


def test_every_BIBLE_case_refuses_with_its_OWN_code(con):
    from src.engine.bible import BibleError
    wrong = []
    for code, call in sorted(_bible_cases(con).items()):
        try:
            call()
            wrong.append("%s: ACCEPTED" % code)
        except BibleError as e:
            if e.code != code:
                wrong.append("%s: got %r" % (code, e.code))
        except Exception as e:                                    # noqa: BLE001
            wrong.append("%s: raised %s (%s)" % (code, type(e).__name__, str(e)[:60]))
    assert not wrong, "; ".join(wrong)


def test_the_BIBLE_case_table_is_CHECKED_AGAINST_the_registry(con):
    from src.engine import codes
    registered = {c for c in codes.CODES if c.startswith("BIBLE_")}
    cases = set(_bible_cases(con))
    assert not (registered - cases), (
        "registered with no executing case: %s" % sorted(registered - cases))
    assert not (cases - registered), (
        "a case names an unregistered code: %s" % sorted(cases - registered))


def test_a_VALID_law_still_normalises(con):
    """The control. A validator that refused everything would pass every case above."""
    from src.engine import bible as B
    rows = B._authored_laws({"laws": [_law()]})
    assert len(rows) == 1 and rows[0]["law_id"] == "L1", str(rows)
    permits = B._project_laws({"laws": [_law(),
                                        _law(id="L2", modality="PERMITS", excepts=["L1"])]})
    assert len(permits) >= 2, "a PERMITS row excepting a REAL law was refused: %s" % permits


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        tmp = tempfile.mkdtemp(prefix="swe_bible_")
        con = None
        try:
            con = _fresh(tmp)          # a fresh DB per test — no cross-contamination
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
