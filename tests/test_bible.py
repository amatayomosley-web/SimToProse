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
