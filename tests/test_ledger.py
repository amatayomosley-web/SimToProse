#!/usr/bin/env python3
"""test_ledger.py — gate-1 proof for the engine spine (schema + records + ledger).

Asserts the contracts the design names, not implementation details:
  run-lifecycle.md   — turn-commit atomicity (rollback leaves ZERO partial rows), resume == uninterrupted
                       control, divergent resume aborts loudly.
  world-state-ledger — fold is deterministic and pure; effective_at gates future-dated consequences.
  record-contract.md — recall / manifest / relationship-delta writes land with the commit.
Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.ledger import Ledger, LedgerError              # noqa: E402
from src.engine.records import Event, RecordError, RelationshipDelta, TurnCommit, PRIMARIES  # noqa: E402

CONFIG = {"catalog_version": 1, "models": {"decide": "stub"}, "prompt_versions": {"decide": 1}}


def flat_affect(v=0.5):
    return {p: v for p in PRIMARIES}


def commit(run_id, turn, actor="maren", events=None, **kw):
    return TurnCommit(run_id=run_id, turn=turn, actor=actor, thought="t%d" % turn, action="a%d" % turn,
                      tags={"type": "mundane"}, affect=kw.pop("affect", flat_affect()),
                      events=events or [], **kw)


def fresh(tmp, name):
    led = Ledger(os.path.join(tmp, name + ".db"))
    led.create_run("r1", CONFIG)
    led.register_character("r1", "maren", {"name": "Maren"}, {"temperament": "authored"})
    return led


def test_atomic_rollback(tmp):
    """Duplicate (run, turn, actor) commit fails on the turns PK AFTER its event rows insert —
    the transaction must roll those event rows back. The log either has the turn or it doesn't."""
    led = fresh(tmp, "atomic")
    led.append_turn(commit("r1", 0, events=[Event(type="move", payload={"to": "well"}, actor="maren")]))
    n_before = led.con.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    try:
        led.append_turn(commit("r1", 0, events=[Event(type="move", payload={"to": "barn"}, actor="maren")]))
        raise AssertionError("duplicate turn-commit was accepted")
    except LedgerError:
        pass
    n_after = led.con.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    assert n_after == n_before, "rollback leaked %d partial event row(s)" % (n_after - n_before)
    assert led.con.execute("SELECT COUNT(*) c FROM turns").fetchone()["c"] == 1


def test_validation_refuses_before_write(tmp):
    led = fresh(tmp, "validate")
    bad = flat_affect()
    bad["FEAR"] = 1.5
    for broken in (
        commit("r1", 0, affect=bad),
        commit("r1", 0, events=[Event(type="harm", payload={}, caused_at=5, effective_at=3)]),
        commit("r1", 0, rel_deltas=[RelationshipDelta("maren", "edda", "loyalty", 0.1)]),
    ):
        try:
            led.append_turn(broken)
            raise AssertionError("invalid record accepted: %r" % broken)
        except RecordError:
            pass
    assert led.con.execute("SELECT COUNT(*) c FROM turns").fetchone()["c"] == 0, "refused commit left rows"


def test_fold_deterministic_and_projects(tmp):
    led = fresh(tmp, "fold")
    led.append_turn(commit("r1", 0, events=[Event(type="move", payload={"to": "square"}, actor="maren")]))
    led.append_turn(commit("r1", 1, events=[
        Event(type="reveal", payload={"fact": "bryn_fevered", "to": ["maren", "edda"]}, actor="edda"),
        Event(type="tension", payload={"name": "fever_season", "temperature": 0.6}),
    ]))
    led.append_turn(commit("r1", 2, events=[Event(type="harm", payload={"terminal": True}, actor="fever", target="tobin")]))
    a, b = led.fold("r1", 2), led.fold("r1", 2)
    assert a == b, "fold is not deterministic on the same log"
    assert a["agents"]["maren"]["location"] == "square"
    assert a["information"]["bryn_fevered"] == ["edda", "maren"]
    assert a["tensions"]["fever_season"]["temperature"] == 0.6
    assert a["agents"]["tobin"]["life_status"] == "dead"
    assert a["clock"]["now"] == 2


def test_effective_at_gates_the_fold(tmp):
    led = fresh(tmp, "twoclock")
    led.append_turn(commit("r1", 0, events=[
        Event(type="move", payload={"to": "hills"}, actor="maren", caused_at=0, effective_at=4)]))
    assert led.fold("r1", 2)["agents"]["maren"]["location"] is None, "future-dated event folded early"
    assert led.fold("r1", 4)["agents"]["maren"]["location"] == "hills", "due event did not fold"


def test_resume_equals_uninterrupted_control(tmp):
    interrupted, control = fresh(tmp, "resume_a"), fresh(tmp, "resume_b")
    script = [commit("r1", i, events=[Event(type="move", payload={"to": "loc%d" % i}, actor="maren")]
                     if i % 3 == 0 else []) for i in range(12)]
    for i, c in enumerate(script):
        interrupted.append_turn(c)
        if i == 5:  # mid-run checkpoint, then "crash" (nothing held in memory matters after this)
            interrupted.persist_snapshot("r1", 5, interrupted.fold("r1", 5))
    for c in [commit("r1", i, events=[Event(type="move", payload={"to": "loc%d" % i}, actor="maren")]
                     if i % 3 == 0 else []) for i in range(12)]:
        control.append_turn(c)
    resumed = interrupted.resume("r1")
    assert resumed["turn"] == 11
    assert resumed["snapshot"] == control.fold("r1", 11), "resume diverged from the uninterrupted control"


def test_divergent_resume_aborts_loudly(tmp):
    led = fresh(tmp, "diverge")
    for i in range(6):
        led.append_turn(commit("r1", i, events=[Event(type="move", payload={"to": "loc%d" % i}, actor="maren")]))
    led.persist_snapshot("r1", 3, led.fold("r1", 3))
    with led.con:  # corrupt a field the tail replay does NOT rewrite (moves only touch location) —
        # a corrupted location would be legitimately healed by the later absolute move projection
        led.con.execute("UPDATE snapshots SET value = ? WHERE kind = 'agents'",
                        (json.dumps({"location": "loc3", "life_status": "alive", "possessions": ["phantom"]}),))
    try:
        led.resume("r1")
        raise AssertionError("divergent resume did not abort")
    except LedgerError as e:
        assert "DIVERGENCE" in str(e)


def test_record_contract_rows_land(tmp):
    led = fresh(tmp, "contract")
    led.append_turn(commit("r1", 0,
                           recall=["belief:suil_death", "belief:third_night_rule"],
                           manifest={"state_fields_read": ["affect"], "beliefs_injected": 2, "percepts": ["bryn"], "edges": []},
                           rel_deltas=[RelationshipDelta("maren", "joss", "trust", -0.1)]))
    assert json.loads(led.con.execute("SELECT belief_refs FROM recall_events").fetchone()["belief_refs"])[0] == "belief:suil_death"
    assert json.loads(led.con.execute("SELECT manifest FROM decision_manifests").fetchone()["manifest"])["beliefs_injected"] == 2
    rd = led.con.execute("SELECT * FROM relationship_deltas").fetchone()
    assert (rd["perceiver"], rd["target"], rd["axis"]) == ("maren", "joss", "trust") and abs(rd["delta"] + 0.1) < 1e-9


def test_llm_token_ledger(tmp):
    led = fresh(tmp, "tokens")
    led.log_llm_call("r1", 0, "decide", "anthropic/claude-haiku-4.5", 551, 120, scene="fever")
    row = led.con.execute("SELECT * FROM llm_calls").fetchone()
    assert row["purpose"] == "decide" and row["tokens_in"] == 551


def test_fk_enforcement_survives_migration(tmp):
    """Reviewer finding 3 claimed executescript turns foreign_keys off — refuted empirically; this
    test pins the property so a future migration change can't silently regress it."""
    import sqlite3
    led = fresh(tmp, "fk")
    assert led.con.execute("PRAGMA foreign_keys").fetchone()[0] == 1, "foreign_keys is OFF after migrate"
    try:
        with led.con:
            led.con.execute("INSERT INTO events (run_id, turn, caused_at, effective_at, type, payload) "
                            "VALUES ('GHOST_RUN', 0, 0, 0, 'move', '{}')")
        raise AssertionError("FK violation was accepted")
    except sqlite3.IntegrityError:
        pass


def test_parked_run_refuses_append(tmp):
    """run-lifecycle.md: a parked run is visible + resumable, never appended-to until reactivated."""
    led = fresh(tmp, "parked")
    led.append_turn(commit("r1", 0))
    led.set_status("r1", "parked")
    try:
        led.append_turn(commit("r1", 1))
        raise AssertionError("append to a parked run was accepted")
    except LedgerError:
        pass
    led.set_status("r1", "active")
    led.append_turn(commit("r1", 1))  # reactivation restores the write path


def test_projection_families(tmp):
    """seize/destroy-asset (holdings) and betray/bond (relationships) — the doc-named projections
    the original suite skipped. Snapshot is the current NOW: bond-after-betray shows alliance,
    the betrayal stays queryable in the immutable log."""
    led = fresh(tmp, "families")
    led.append_turn(commit("r1", 0, events=[
        Event(type="seize", payload={"asset": "granary"}, actor="maren"),
        Event(type="betray", payload={}, actor="joss", target="maren"),
    ]))
    led.append_turn(commit("r1", 1, events=[
        Event(type="destroy-asset", payload={"asset": "granary"}, actor="raiders"),
        Event(type="bond", payload={}, actor="joss", target="maren"),
    ]))
    snap = led.fold("r1", 1)
    assert snap["holdings"]["granary"] == {"destroyed": True}
    assert snap["relationships"]["joss|maren"]["standing"] == "alliance"
    assert led.fold("r1", 0)["holdings"]["granary"] == {"controller": "maren"}
    assert led.fold("r1", 0)["relationships"]["joss|maren"]["standing"] == "enmity"
    n_betrays = led.con.execute("SELECT COUNT(*) c FROM events WHERE type='betray'").fetchone()["c"]
    assert n_betrays == 1, "the log must keep the betrayal the snapshot moved past"


def test_multi_run_isolation(tmp):
    """Two runs in one db, same turn numbers: snapshots, folds, and state must never cross-pollute."""
    led = fresh(tmp, "multirun")
    led.create_run("r2", CONFIG)
    led.register_character("r2", "maren", {"name": "Maren"}, {"temperament": "authored"})
    led.append_turn(commit("r1", 0, events=[Event(type="move", payload={"to": "village"}, actor="maren")]))
    led.append_turn(commit("r2", 0, events=[Event(type="move", payload={"to": "mountain"}, actor="maren")]))
    led.persist_snapshot("r1", 0, led.fold("r1", 0))
    led.persist_snapshot("r2", 0, led.fold("r2", 0))
    assert led.resume("r1")["snapshot"]["agents"]["maren"]["location"] == "village"
    assert led.resume("r2")["snapshot"]["agents"]["maren"]["location"] == "mountain"


def test_turn_skipped_is_recorded(tmp):
    led = fresh(tmp, "skipped")
    led.record_turn_skipped("r1", 3, "maren", "decide call exhausted retries")
    ev = led.con.execute("SELECT * FROM events WHERE type='turn-skipped'").fetchone()
    assert ev["turn"] == 3 and "retries" in json.loads(ev["payload"])["reason"]


def test_the_log_refuses_to_be_rewritten(tmp):
    """Hard rule 2, enforced by the DATABASE rather than by ledger.py's habits.

    "The log is append-only. No update, no delete on events — corrections are new `correction`
    events." Until schema v9 that held only because `ledger.py` happens never to emit UPDATE or
    DELETE. Anything else with a connection — a stranger's script, a foreign driver on rails, an
    sqlite3 shell, a future writer added in good faith — could rewrite a committed turn and leave a
    folded snapshot that no longer matches the log it claims to derive from.

    A rule stated absolutely and enforced by habit is a rule that has never been tested. This tests
    it: the assertion is that the write is REFUSED, not that a trigger is present in sqlite_master
    (which would check the mechanism instead of the guarantee).
    """
    import os as _os
    from src.engine.db import connect as _connect
    con = _connect(_os.path.join(tmp, "appendonly.db"))
    con.execute("INSERT INTO runs(run_id,created_at,status,config) VALUES('ao','t','active','{}')")
    con.execute("INSERT INTO events(run_id,turn,caused_at,effective_at,type,actor,target,location,"
                "visibility,payload) VALUES('ao',0,'t','t','betray','a','b','yard','public','{}')")
    con.commit()

    # A ROW PER FROZEN TABLE FIRST. A BEFORE-UPDATE trigger fires PER ROW, so `UPDATE turns SET ...`
    # on an empty table succeeds trivially and proves nothing — the first draft of this test asserted
    # exactly that and passed five tables while genuinely checking one. There is nothing to protect
    # in an empty table; the guarantee is about rows that exist.
    con.execute("INSERT INTO turns(run_id,turn,actor,thought,action,tags,validation,committed_at) "
                "VALUES('ao',0,'a','t','x','{}','{}','t')")
    con.execute("INSERT INTO recall_events(run_id,turn,actor,belief_refs) VALUES('ao',0,'a','[]')")
    con.execute("INSERT INTO acquisitions(run_id,char_id,turn,belief) VALUES('ao','a',0,'{}')")
    con.execute("INSERT INTO arc_diffs(run_id,char_id,turn,diff) VALUES('ao','a',0,'{}')")
    con.execute("INSERT INTO relationship_deltas(run_id,turn,perceiver,target,axis,delta,ord) "
                "VALUES('ao',0,'a','b','trust',-0.1,'first')")
    con.commit()

    frozen = ("events", "turns", "recall_events", "acquisitions", "arc_diffs", "relationship_deltas")
    for table in frozen:
        for verb in ("UPDATE %s SET run_id='x'", "DELETE FROM %s"):
            try:
                con.execute(verb % table)
                raise AssertionError("%s accepted a %s — the log is rewritable"
                                     % (table, verb.split()[0]))
            except AssertionError:
                raise
            except Exception as e:
                assert "append-only" in str(e),                     "%s refused %s but not for the append-only reason: %s" % (table, verb.split()[0], e)

    # the INSERT path is untouched — a frozen log must still GROW
    con.execute("INSERT INTO events(run_id,turn,caused_at,effective_at,type,actor,target,location,"
                "visibility,payload) VALUES('ao',1,'t','t','correction','a','b','yard','public','{}')")
    assert con.execute("SELECT COUNT(*) FROM events WHERE run_id='ao'").fetchone()[0] == 2

    # and the CACHES stay mutable — a snapshot that cannot be rewritten is not a cache
    con.execute("UPDATE runs SET status='parked' WHERE run_id='ao'")
    con.execute("INSERT INTO snapshots(run_id,as_of_turn,kind,key,value) VALUES('ao',1,'agents','a','{}')")
    con.execute("UPDATE snapshots SET value='{\"x\":1}' WHERE run_id='ao'")
    con.commit()


def test_an_older_db_gains_the_protection(tmp):
    """A pre-v9 chronicle must migrate, keep every row, and come out protected."""
    import os as _os, sqlite3 as _sq
    from src.engine.db import connect as _connect
    path = _os.path.join(tmp, "legacy.db")
    raw = _sq.connect(path)
    raw.executescript("CREATE TABLE runs(run_id TEXT PRIMARY KEY, created_at TEXT, status TEXT, config TEXT);"
                      "CREATE TABLE events(event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT,"
                      " turn INTEGER, caused_at TEXT, effective_at TEXT, type TEXT, actor TEXT,"
                      " target TEXT, location TEXT, visibility TEXT, payload TEXT);")
    raw.execute("INSERT INTO runs VALUES('old','t','parked','{}')")
    raw.execute("INSERT INTO events(run_id,turn,caused_at,effective_at,type,actor,target,location,"
                "visibility,payload) VALUES('old',0,'t','t','x','a','b','y','public','{}')")
    raw.commit(); raw.close()

    con = _connect(path)                                    # migrates
    assert con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1, "migration lost a row"
    try:
        con.execute("UPDATE events SET payload='{}'")
        raise AssertionError("an older db migrated WITHOUT gaining the protection")
    except AssertionError:
        raise
    except Exception as e:
        assert "append-only" in str(e), e


def main():
    tmp = tempfile.mkdtemp(prefix="swe_ledger_test_")
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    try:
        for t in tests:
            try:
                t(tmp)
                print("  PASS  %s" % t.__name__)
            except Exception as e:
                failed += 1
                print("  FAIL  %s: %s" % (t.__name__, e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d/%d passed" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
