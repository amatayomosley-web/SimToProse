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
import io
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.ledger import Ledger, LedgerError              # noqa: E402
from src.engine.records import (Event, RecordError, RelationshipDelta, TowardDelta,
                                TurnCommit, PRIMARIES)  # noqa: E402

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
    """A commit that fails PART WAY THROUGH must leave no event rows. The log either has the turn
    or it doesn't.

    THE TRIGGER CHANGED ON 2026-09-03 AND THE TEST HAD TO, or it would have gone vacuous. It used a
    DUPLICATE (run, turn, actor) commit, which failed on the turns primary key AFTER the event rows
    inserted — a real mid-transaction failure. Then `append_turn` gained a duplicate PRE-check
    (LEDGER_TURN_EXISTS), so the duplicate now never reaches the transaction: no event rows insert,
    `n_after == n_before` is trivially true, and this test kept PASSING while proving nothing. It
    still caught `LedgerError`, so nothing went red — a guard passing for the wrong reason, which is
    the shape CLAUDE.md tabulates seven instances of.

    The trigger is now two IDENTICAL toward-deltas in one commit: `TowardDelta.validate` accepts
    each, the events insert, and the pair then collides on
    `UNIQUE (run_id, turn, perceiver, target, primary_)` — mid-transaction, by construction.
    Verified 2026-09-03 to raise LEDGER_TURN_COMMIT_ROLLED_BACK with the event count unmoved."""
    led = fresh(tmp, "atomic")
    _p0 = sorted(PRIMARIES)[0]
    _td = TowardDelta(perceiver="maren", target="edda", primary=_p0, delta=0.1)
    n_before = led.con.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    try:
        led.append_turn(commit("r1", 0,
                               events=[Event(type="move", payload={"to": "well"}, actor="maren")],
                               toward_deltas=[_td, _td]))
        raise AssertionError("a commit that collides mid-transaction was accepted")
    except LedgerError as e:
        assert e.code == "LEDGER_TURN_COMMIT_ROLLED_BACK", (
            "the rollback must report the ROLLBACK, not something else: %r" % e.code)
    n_after = led.con.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    assert n_after == n_before, "rollback leaked %d partial event row(s)" % (n_after - n_before)
    assert led.con.execute("SELECT COUNT(*) c FROM turns").fetchone()["c"] == 0, (
        "a failed commit must leave no turn row either")


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
        # The SEED form (schema of 2026-09-02): keyed by `id` like every other authored world
        # entity, and carrying the standing interests an act is priced against. The old
        # {name, temperature} shape set the value absolutely and could not accumulate.
        Event(type="tension", payload={"id": "fever_season", "temperature": 0.6,
                                       "watches": {"locations": ["the-ward"]},
                                       "interests": {"threat": 0.5}}),
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
    con.execute("INSERT INTO wound_deltas(run_id,char_id,turn,wound_id,delta,kind,source) "
                "VALUES('ao','a',0,'w',-0.1,'erosion','')")
    con.commit()

    frozen = ("events", "turns", "recall_events", "acquisitions", "arc_diffs",
              "relationship_deltas", "wound_deltas")
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


def test_scene_cfg_is_PINNED_and_drift_is_detected(tmp):
    """The bible defect, one table over. Until schema v14 a scene row recorded its BOUNDARY and
    nothing about what produced the turns inside it, so a resumed run folded a snapshot it could
    not explain. Four things must hold, and the last two are the ones with teeth."""
    from src.engine import scene_cfg
    led = fresh(tmp, "cfgpin")
    led.append_turn(commit("r1", 0))

    cfg = {"name": "fireside", "location": "the-hall", "props": ["a cup", "the fire"],
           "cast": [{"id": "maren"}], "opening_tags": {"dimensions": {"threat": "mild"}}}
    led.append_scene("r1", 0, "fireside", "maren", 0, 0, cfg=cfg)

    # 1. the body comes back, so a replay can name its inputs
    got = scene_cfg.for_scene(led.con, "r1", 0)
    assert got == cfg, "the pinned cfg did not round-trip: %r" % (got,)

    # 2. an unchanged cfg is NOT drift — a guard that cries wolf gets switched off
    drift, detail = scene_cfg.drifted(led.con, "r1", 0, cfg)
    assert not drift, detail

    # 3. reordering keys or reformatting is NOT drift: the PARSED payload is what is hashed
    reordered = {k: cfg[k] for k in reversed(list(cfg))}
    assert scene_cfg.fingerprint(reordered) == scene_cfg.fingerprint(cfg)

    # 4. a REAL edit IS drift, and both fingerprints are named so the author can see which is which
    edited = dict(cfg, location="the-ward")
    drift, detail = scene_cfg.drifted(led.con, "r1", 0, edited)
    assert drift, "editing the location was not detected"
    assert "pinned" in detail and "on disk" in detail, detail


def test_an_UNPINNED_scene_reads_as_unknown_not_as_unchanged(tmp):
    """The compatibility contract, and the one that decides whether this guard can lie in the
    reassuring direction. A scene recorded before v14 has no body; saying "unchanged" about it
    would assert something nobody recorded. `bible.for_run` makes the same choice."""
    from src.engine import scene_cfg
    led = fresh(tmp, "cfgunpinned")
    led.append_turn(commit("r1", 0))
    led.append_scene("r1", 0, "fireside", "maren", 0, 0)          # no cfg= : the pre-v14 shape

    assert scene_cfg.for_scene(led.con, "r1", 0) is None
    drift, detail = scene_cfg.drifted(led.con, "r1", 0, {"name": "anything at all"})
    assert not drift and "predates" in detail, detail
    # and a scene that does not exist is distinguishable from one that is merely unpinned
    _d, nodetail = scene_cfg.drifted(led.con, "r1", 99, {})
    assert "no such scene" in nodetail, nodetail


def test_one_cfg_run_twice_is_ONE_row(tmp):
    """Content-addressing pins and DEDUPLICATES in one move (bibles makes the same argument):
    two scenes run from one cfg share a row, which is the evidence they had IDENTICAL inputs
    rather than merely similar ones."""
    from src.engine import scene_cfg
    led = fresh(tmp, "cfgdedupe")
    led.append_turn(commit("r1", 0))
    led.append_turn(commit("r1", 1))
    cfg = {"name": "fireside", "location": "the-hall"}
    led.append_scene("r1", 0, "fireside", "maren", 0, 0, cfg=cfg)
    led.append_scene("r1", 1, "fireside", "maren", 1, 1, cfg=dict(cfg))

    n = led.con.execute("SELECT COUNT(*) AS n FROM scene_cfgs").fetchone()["n"]
    assert n == 1, "the same cfg was stored %d times" % n
    rows = led.scenes_for("r1")
    assert rows[0]["cfg_fingerprint"] == rows[1]["cfg_fingerprint"] != ""
    # a DIFFERENT cfg gets its own row, or dedupe would be collapsing real distinctions
    led.append_turn(commit("r1", 2))
    led.append_scene("r1", 2, "the-ward", "maren", 2, 2, cfg={"name": "the-ward"})
    assert led.con.execute("SELECT COUNT(*) AS n FROM scene_cfgs").fetchone()["n"] == 2


def test_the_WRITE_ONCE_identities_refuse_a_SECOND_write(tmp):
    """Four identities are minted once: a run, a cast entry, a commit, a scene. Three leaked.

    Measured 2026-09-03 before the fix: `create_run` and `register_character` each raised a bare
    `sqlite3.IntegrityError: UNIQUE constraint failed: …` with `.code` None — true, and the
    programmer's view of something the operator experienced as "that already exists". `append_turn`
    raised LEDGER_TURN_COMMIT_ROLLED_BACK, which names the MECHANISM rather than the condition.

    `append_scene` is the FOURTH, found 2026-09-03 AFTER the other three were called the complete
    set — it raised a bare IntegrityError carrying no `.code` attribute at all. The count had been
    taken from the sites already converted rather than from the tables with a write-once key, which
    is the census reading its own output back as its input.

    All four go through `writeonce`, one spelling. The constraint is no longer merely a backstop:
    see `test_a_LOST_RACE_refuses_with_the_SAME_code`."""
    from src.engine.ledger import LedgerError
    led = fresh(tmp, "writeonce")
    cfg = CONFIG
    dup = TurnCommit(run_id="r1", turn=0, actor="maren", thought="t", action="a",
                        tags={"type": "mundane"}, affect={p: 0.5 for p in PRIMARIES}, events=[])
    led.append_turn(dup)
    cases = (("LEDGER_RUN_EXISTS", lambda: led.create_run("r1", cfg)),
             ("LEDGER_CHARACTER_EXISTS", lambda: led.register_character("r1", "maren", {}, {})),
             ("LEDGER_TURN_EXISTS", lambda: led.append_turn(dup)),
             ("LEDGER_SCENE_EXISTS", lambda: led.append_scene("r1", 7, "again", "maren", 0, 0)))
    led.append_scene("r1", 7, "first", "maren", 0, 0)
    for code, call in cases:
        try:
            call()
            raise AssertionError("%s: the duplicate was ACCEPTED" % code)
        except LedgerError as e:
            assert e.code == code, "expected %s, got %r" % (code, e.code)

    # THE DISTINCTION MUST SURVIVE: a rollback from any OTHER cause still reports the rollback,
    # or coding the duplicate would have cost the code that was already right.
    from src.engine import codes
    assert codes.is_registered("LEDGER_TURN_COMMIT_ROLLED_BACK"), "the rollback code was retired"
    with open(os.path.join(REPO, "src", "engine", "ledger.py"), encoding="utf-8") as fh:
        assert "LEDGER_TURN_COMMIT_ROLLED_BACK" in fh.read(), (
            "coding the duplicate cost the rollback code that was already right")


def test_the_REFUSALS_are_ordered_OUTSIDE_IN(tmp):
    """When several refusals apply at once, which one does the operator hear?

    Nothing asserted the ORDER, and precedence is exactly what a later edit reshuffles without
    noticing — moving the duplicate pre-check above `commit.validate()` would be a one-line change
    that makes a malformed commit report its slot instead of its defect.

    The order is OUTSIDE-IN, measured 2026-09-03: the commit's own SHAPE, then whether the run
    exists, then whether it is active, then whether the slot is taken. That is the order in which
    the operator can act — a malformed commit is malformed whether or not its turn index is free,
    and the fix for each is different."""
    from src.engine.ledger import LedgerError
    led = fresh(tmp, "precedence")
    good = commit("r1", 0)
    led.append_turn(good)

    bad_affect = flat_affect()
    bad_affect["FEAR"] = 9.0
    cases = (
        # malformed AND duplicate -> the SHAPE wins, because that is the defect
        ("RECORD_AFFECT_VALUE_RANGE", commit("r1", 0, affect=bad_affect)),
        # duplicate on a run that does not exist -> the RUN wins; it is the outer scope
        ("LEDGER_RUN_UNKNOWN", commit("no-such-run", 0)),
        # well-formed duplicate on a live run -> the slot
        ("LEDGER_TURN_EXISTS", commit("r1", 0)),
    )
    for expected, tc in cases:
        try:
            led.append_turn(tc)
            raise AssertionError("%s: the commit was ACCEPTED" % expected)
        except (LedgerError, RecordError) as e:
            assert e.code == expected, (
                "refusal precedence changed: expected %s, got %r — an operator now hears about a "
                "different problem than the one they should fix first" % (expected, e.code))


def test_a_LOST_RACE_refuses_with_the_SAME_code(tmp):
    """The pre-check is not atomic. Does the refusal survive losing the race, or degrade?

    `writeonce.py` used to STATE this gap: two writers both pass the SELECT, one hits the
    constraint, and the operator gets back the raw `sqlite3.IntegrityError` the module exists to
    replace. A caveat is a defect that has been written down — the code was total only when
    uncontended, which is the condition under which nobody needed it.

    Simulated by making the FAST PATH blind for exactly one call while the row is already there, so
    the write reaches the constraint the way a lost race does. Both halves must name the identity
    with the same registered code."""
    import sqlite3
    from src.engine import writeonce as _once
    from src.engine.ledger import LedgerError
    led = fresh(tmp, "race")
    led.append_scene("r1", 3, "winner", "maren", 0, 0)
    led.register_character("r1", "kell", {}, {})
    led.append_turn(commit("r1", 4))

    real, seen = _once.refuse_duplicate, {"n": 0}

    def blind_once(con, sql, params, code, msg, err):
        seen["n"] += 1
        if seen["n"] == 1:
            return                       # the fast path sees nothing — the other writer is mid-flight
        return real(con, sql, params, code, msg, err)   # the re-ask sees the winner's row

    for expected, call in (("LEDGER_SCENE_EXISTS",
                            lambda: led.append_scene("r1", 3, "loser", "maren", 0, 0)),
                           ("LEDGER_CHARACTER_EXISTS",
                            lambda: led.register_character("r1", "kell", {}, {})),
                           ("LEDGER_RUN_EXISTS", lambda: led.create_run("r1", CONFIG)),
                           # the fourth reaches the re-ask through append_turn's OWN except branch,
                           # not through write_once — it writes many rows, so it cannot use that
                           # shape. Without the re-ask a lost race here reports ROLLED_BACK: the
                           # mechanism, for a condition that has a code of its own.
                           ("LEDGER_TURN_EXISTS", lambda: led.append_turn(commit("r1", 4)))):
        seen["n"] = 0
        _once.refuse_duplicate = blind_once
        try:
            call()
            raise AssertionError("%s: the duplicate was ACCEPTED under contention" % expected)
        except LedgerError as e:
            assert e.code == expected, (
                "a lost race degraded the refusal: expected %s, got %r" % (expected, e.code))
        except sqlite3.IntegrityError as e:
            raise AssertionError(
                "%s: a lost race leaked the raw constraint error — %s" % (expected, e))
        finally:
            _once.refuse_duplicate = real
        assert seen["n"] == 2, (
            "%s: the re-ask did not run (%d calls) — the code passed for some other reason"
            % (expected, seen["n"]))


def test_a_DIFFERENT_constraint_is_not_relabelled_as_a_duplicate(tmp):
    """Guards against RELABELLING, which is a narrower claim than this test first made.

    ITS FIRST DOCSTRING SAID "this is the case that needs the re-ask", and that was false, proven
    by removing the re-ask: what is left is a bare `raise`, so the IntegrityError still propagates
    and this test still passes. It fails only against the SHORTCUT — catching IntegrityError and
    raising the duplicate code unconditionally. The absence of the re-ask is caught by
    `test_a_LOST_RACE_refuses_with_the_SAME_code` and by nothing here.

    Both breakages were run the day this was written and BOTH went red, which is why the suite was
    sound and the sentence was not: two tests failing together was read as each test failing for
    its own reason.

    `sqlite3.IntegrityError` is raised by every constraint on the table, not only the write-once
    key: a foreign key, a NOT NULL, a second UNIQUE. Catching it and raising the duplicate code
    unconditionally would be four lines shorter and would put a confident, WRONG name on an
    unrelated fault — a refusal that says "already exists" about a row that does not. That is the
    same substitution (the mechanism reported in place of the condition) this whole conversion set
    out to remove, so it must not be reintroduced by the fix for it.

    Asserted on the helper directly, with two constraints on one table, because no ledger table
    currently offers both — and a guard that can only be written where the defect happens to be
    reachable today stops covering the contract the moment a column is added."""
    import sqlite3
    from src.engine import writeonce as _once
    from src.engine.ledger import LedgerError
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE t (a TEXT PRIMARY KEY, b TEXT UNIQUE)")
    con.execute("INSERT INTO t VALUES ('x', 'shared')")
    con.commit()

    # the write-once key is `a`. 'y' is FREE, so the check passes both times; the insert violates
    # the UNIQUE on `b`, which is a different rule and not this helper's to name.
    try:
        _once.write_once(con,
                         lambda: _once.refuse_duplicate(con, "SELECT 1 FROM t WHERE a=?", ("y",),
                                                        "LEDGER_RUN_EXISTS", "nope", LedgerError),
                         lambda: con.execute("INSERT INTO t VALUES ('y', 'shared')"))
        raise AssertionError("the second UNIQUE was not enforced — the fixture proves nothing")
    except LedgerError as e:
        raise AssertionError(
            "an unrelated constraint was relabelled %s: the helper claims a row exists that does "
            "not, and the real rule that was broken is now unnameable" % e.code)
    except sqlite3.IntegrityError:
        pass                              # correct: propagated as itself

    # ...and the control, so the test cannot pass by the helper simply never coding anything.
    try:
        _once.write_once(con,
                         lambda: _once.refuse_duplicate(con, "SELECT 1 FROM t WHERE a=?", ("x",),
                                                        "LEDGER_RUN_EXISTS", "dup", LedgerError),
                         lambda: con.execute("INSERT INTO t VALUES ('x', 'other')"))
        raise AssertionError("the write-once key itself was not refused")
    except LedgerError as e:
        assert e.code == "LEDGER_RUN_EXISTS", e.code


def test_a_LOCK_TIMEOUT_is_a_TIMEOUT_and_not_a_REFUSAL(tmp):
    """The likelier way to lose a race, and the one the first fix did not cover.

    `write_once` caught only `sqlite3.IntegrityError` — the COLLISION, where a loser squeezes
    between the check and the commit. The WAIT needs only a slow winner, happens to calls that are
    not duplicates of anything, and left the spine as a raw `sqlite3.OperationalError` with no
    `.code`: measured 2026-09-03 at 5.4s on a `create_run` for an UNCONTENDED run id.

    THE SAME CONDITION, THE SAME CODE, FROM BOTH WRITERS. `append_turn` already coded this as
    LEDGER_TURN_COMMIT_ROLLED_BACK while `write_once` let it out raw — one module answering one
    condition two ways, which is exactly how it went unnoticed. Asserted on all three paths.

    AND IT IS A TIMEOUT, NOT A REFUSAL: the identical call succeeds once the lock clears, so it
    carries its own name rather than joining any _EXISTS or ROLLED_BACK code. That distinction is
    the whole reason it is a separate code, so the test asserts the NAME, not merely that something
    coded came back."""
    from src.engine import db as _db
    from src.engine.records import RecordError as _RE
    old = _db.BUSY_TIMEOUT_SECONDS
    _db.BUSY_TIMEOUT_SECONDS = 0.2                  # the wait is the point; its LENGTH is not
    try:
        led = fresh(tmp, "busy")
        holder = Ledger(os.path.join(tmp, "busy.db"))
        holder.con.execute("BEGIN IMMEDIATE")       # a winner holds the write lock, unrelated row
        holder.con.execute(
            "INSERT INTO scenes (run_id, scene_no, label, pov, cfg_fingerprint, voice, knowledge, "
            "start_turn, end_turn) VALUES ('r1', 99, 'h', 'p', '', 'close-third', 'pov', 0, 0)")
        # AND THE HANDLER MUST NOT GO BACK TO THE DATABASE FOR A FAILURE A CONSTRAINT DID NOT CAUSE.
        # `append_turn`'s re-ask is gated on IntegrityError; ungated it ran a SELECT on a connection
        # whose transaction had just died, for EVERY unrelated fault. A WAL read does not need the
        # write lock, so that SELECT quietly succeeds and the busy code still comes back — the gate
        # is invisible unless the re-ask itself is counted, which is what `asks` does.
        from src.engine import writeonce as _once
        real, asks = _once.refuse_duplicate, [0]
        def counted(*a, **k):
            asks[0] += 1
            return real(*a, **k)
        cases = (("create_run", lambda: led.create_run("brand-new-and-uncontended", CONFIG)),
                 ("append_scene", lambda: led.append_scene("r1", 2, "s", "maren", 0, 0)),
                 ("append_turn", lambda: led.append_turn(commit("r1", 3))))
        for where, call in cases:
            try:
                call()
                raise AssertionError("%s: the blocked write was ACCEPTED" % where)
            except _RE as e:
                assert e.code == "DB_BUSY_TIMEOUT", (
                    "%s: a lock timeout reported %r — it must name the TIMEOUT, because the same "
                    "call succeeds once the lock clears and the operator's action is to RETRY, not "
                    "to fix their input" % (where, e.code))

        _once.refuse_duplicate = counted
        try:
            asks[0] = 0
            try:
                led.append_turn(commit("r1", 4))
            except _RE:
                pass
            assert asks[0] == 1, (
                "append_turn asked the duplicate question %d times on a LOCK failure; the pre-check "
                "is 1 and the re-ask must not run — a busy timeout is not a constraint answering"
                % asks[0])
        finally:
            _once.refuse_duplicate = real
        holder.con.rollback()
    finally:
        _db.BUSY_TIMEOUT_SECONDS = old


def test_write_once_REFUSES_a_connection_with_WORK_PENDING(tmp):
    """The precondition `write_once` assumed and never checked.

    With uncommitted DML on the connection, its pre-check reads inside that private snapshot AND
    its `with con:` would ROLL THE CALLER'S WORK BACK on any failure — silently discarding writes
    the caller believed were in flight. Swept 2026-09-03: no caller in src/, scripts/ or tests/
    does this, which is why it was invisible rather than why it was safe."""
    from src.engine.records import RecordError as _RE
    led = fresh(tmp, "pending")
    led.con.execute(                                # raw DML, deliberately not committed
        "INSERT INTO scenes (run_id, scene_no, label, pov, cfg_fingerprint, voice, knowledge, "
        "start_turn, end_turn) VALUES ('r1', 5, 'uncommitted', 'p', '', 'close-third', 'pov', 0, 0)")
    assert led.con.in_transaction, "the fixture did not actually leave work pending"
    try:
        led.create_run("another", CONFIG)
        raise AssertionError("a write-once write proceeded on a connection with work pending")
    except _RE as e:
        assert e.code == "DB_TRANSACTION_OPEN", e.code
    led.con.rollback()


def test_the_IDEMPOTENT_REPLAY_writers_still_replay(tmp):
    """`write_once` grew a check CALLABLE so these two could use it, and the reason is this test.

    `clock.declare` and `ledger.append_arc_diff` are not plain write-once: `--resume` re-walks
    committed turns by design, so an IDENTICAL re-write is the documented path and must be a
    no-op. A fixed sql+code signature can only express "refuse any second write", which is why
    half the engine's write-once sites could not use the first version of this function. Three
    answers, all asserted: absent -> writes, identical -> replays, different -> refuses."""
    from src.engine import clock as _clock
    led = fresh(tmp, "replay")
    led.append_arc_diff("r1", "maren", 0, {"warmth": 0.1})
    led.append_arc_diff("r1", "maren", 0, {"warmth": 0.1})        # replay: a no-op, not a refusal
    n = led.con.execute("SELECT COUNT(*) c FROM arc_diffs").fetchone()["c"]
    assert n == 1, "an identical replay wrote a second row (%d)" % n
    try:
        led.append_arc_diff("r1", "maren", 0, {"warmth": 0.9})
        raise AssertionError("a DIFFERING arc diff was accepted for the same (run, char, turn)")
    except LedgerError as e:
        assert e.code == "LEDGER_ARC_DIFF_REWRITE", e.code

    _clock.declare(led.con, "r1", 1, 3.0)
    _clock.declare(led.con, "r1", 1, 3.0)                          # replay
    n = led.con.execute("SELECT COUNT(*) c FROM time_declarations").fetchone()["c"]
    assert n == 1, "an identical time declaration wrote a second row (%d)" % n
    try:
        _clock.declare(led.con, "r1", 1, 9.0, on_rewrite=LedgerError)
        raise AssertionError("a DIFFERING elapsed was accepted for the same turn")
    except LedgerError as e:
        assert e.code == "LEDGER_TIME_DECL_REWRITE", e.code


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
