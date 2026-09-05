#!/usr/bin/env python3
"""test_place.py — lore accretes, and a place is queryable.

WHAT WAS WRONG, in two halves that turned out to be one shape.

`src/engine/claims.py` was a finished-looking detector with NO TABLE AND NO WRITER, so nothing could
accumulate what characters say. `bible_entities.what` is one authored line, written when the bible is
pinned and never growing. A character could describe their home town for ten chapters and the world
learned nothing.

And `src/engine/read_api.py` had six functions of which five were person-shaped — `said`, `state`,
`knows`, `edges`, `scene_of`. You could ask what someone knew at turn 40; you could not ask what was
known about a town. The engine modelled people through time and modelled places as a static string.

THE ONE THAT MATTERS MOST is tier folding. `docs/keeper-of-truth.md` derives tier from resolutions
and never stores it, and hard rule 2 makes that mandatory rather than stylistic: a tier column that
flips superposed -> fiction is an UPDATE, which schema v9's triggers refuse. So the test asserts both
that folding works AND that the database would stop the alternative.

Script-style, stdlib only, exit 0 = all pass.
"""
import io
import json
import os
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import claims, read_api                     # noqa: E402
from src.engine.ledger import Ledger                        # noqa: E402
from src.engine.records import TurnCommit, PRIMARIES        # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _led(tmp, name):
    led = Ledger(os.path.join(tmp, name + ".db"))
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    led.register_character("r1", "maren", {"name": "Maren"}, {"temperament": "authored"})
    for t in range(3):
        led.append_turn(TurnCommit(run_id="r1", turn=t, actor="maren", thought="t%d" % t,
                                   action="a%d" % t, tags={"type": "mundane"},
                                   affect={p: 0.5 for p in PRIMARIES}, events=[]))
    return led


def test_an_utterance_and_its_facts_persist(tmp):
    """One utterance carries as many facts as it carries — an earlier draft of claims.py stored a
    single triple per claim and silently dropped the rest."""
    led = _led(tmp, "record")
    uid = claims.record(led.con, "r1", 1, "maren", "We held the festival at midwinter, and my "
                                                   "mother led the procession.",
                        extracts=[{"subject": "clifford", "predicate": "holds festival",
                                   "object": "at midwinter"},
                                  {"subject": "clifford", "predicate": "procession led by",
                                   "object": "marens mother"}])
    got = claims.for_run(led.con, "r1")
    check("the-utterance-persists", len(got) == 1 and got[0]["id"] == uid, str(got))
    check("BOTH-facts-were-indexed", len(got[0]["extracts"]) == 2, str(got[0]["extracts"]))
    check("the-VERBATIM-text-is-kept", "when" not in got[0]["text"] and "midwinter" in got[0]["text"],
          got[0]["text"])
    check("an-unresolved-claim-is-SUPERPOSED", claims.tier_of(got[0]) == claims.SUPERPOSED)


def test_the_tier_FOLDS_from_resolutions_and_is_never_written_back(tmp):
    """keeper-of-truth.md derives tier; hard rule 2 makes that mandatory. A keeper that changes its
    mind appends a second verdict and the fold takes the last one."""
    led = _led(tmp, "fold")
    uid = claims.record(led.con, "r1", 0, "maren", "Clifford was founded by shipwrights.",
                        extracts=[{"subject": "clifford", "predicate": "founded by",
                                   "object": "shipwrights"}])
    claims.resolve(led.con, "r1", uid, 1, claims.ESTABLISHED, "corroborated by the ledger")
    u = claims.for_run(led.con, "r1")[0]
    check("a-verdict-moves-the-tier",
          claims.tier_of(u, claims.resolutions_for(led.con, "r1")) == claims.ESTABLISHED)

    claims.resolve(led.con, "r1", uid, 2, claims.FICTION, "the speaker was boasting")
    check("the-LAST-verdict-wins",
          claims.tier_of(u, claims.resolutions_for(led.con, "r1")) == claims.FICTION)
    check("and-a-declined-claim-stops-contesting",
          claims.live(claims.for_run(led.con, "r1"), claims.resolutions_for(led.con, "r1")) == [])

    # AS OF bounds by turn, so chapter 2 does not see chapter 5's ruling
    check("as-of-does-not-leak-a-later-verdict",
          claims.tier_of(u, claims.resolutions_for(led.con, "r1", as_of=1)) == claims.ESTABLISHED)


def test_the_database_REFUSES_a_rewritten_tier(tmp):
    """The reason tier is derived rather than stored, made concrete: the stored version would have
    to be UPDATEd, and the triggers exist precisely to stop that."""
    led = _led(tmp, "append")
    uid = claims.record(led.con, "r1", 0, "maren", "x", extracts=[{"subject": "clifford",
                                                                   "predicate": "is", "object": "old"}])
    for name, sql in (("update", "UPDATE utterances SET tier='fiction' WHERE utterance_id=%d" % uid),
                      ("delete", "DELETE FROM utterances WHERE utterance_id=%d" % uid)):
        try:
            with led.con:
                led.con.execute(sql)
            check("the-db-refuses-a-tier-%s" % name, False, "the write succeeded")
        except sqlite3.IntegrityError as e:
            check("the-db-refuses-a-tier-%s" % name, "append-only" in str(e), str(e))


def test_contradiction_is_found_between_two_speakers(tmp):
    """The detector over the stored form. Same subject, same predicate, different object — the
    floor claims.py describes, not the ceiling."""
    led = _led(tmp, "contra")
    claims.record(led.con, "r1", 0, "maren", "Clifford was founded by shipwrights.",
                  extracts=[{"subject": "clifford", "predicate": "founded by", "object": "shipwrights"}])
    claims.record(led.con, "r1", 1, "edda", "Clifford was founded by miners.",
                  extracts=[{"subject": "clifford", "predicate": "founded by", "object": "miners"}])
    found = claims.contradictions(claims.for_run(led.con, "r1"),
                                  claims.resolutions_for(led.con, "r1"))
    check("the-contradiction-is-FOUND", len(found) == 1, str(found))
    # normalised, not verbatim: claims.normalise hyphenates, which is what makes the stored index
    # agree with the comparator. Asserting the raw phrase here would be asserting the wrong contract.
    check("and-it-names-the-subject-and-predicate",
          found and found[0][2] == (claims.normalise("Clifford"), claims.normalise("founded by")),
          str(found[0][2]) if found else "nothing found")


def test_place_answers_what_is_known_about_a_town(tmp):
    """THE READ THAT DID NOT EXIST. Three sources, each tagged, and every miss traced."""
    led = _led(tmp, "place")
    claims.record(led.con, "r1", 0, "maren", "Clifford keeps the drowned-boat rite every spring.",
                  extracts=[{"subject": "clifford", "predicate": "keeps rite",
                             "object": "the drowned boat"}])
    claims.record(led.con, "r1", 1, "maren", "Nobody in Clifford will name the old mayor.",
                  extracts=[{"subject": "clifford", "predicate": "will not name",
                             "object": "the old mayor"}])
    claims.record(led.con, "r1", 2, "maren", "The ridge is bare above the treeline.",
                  extracts=[{"subject": "the ridge", "predicate": "is", "object": "bare"}])

    res = read_api.place(led.con, "r1", "clifford", 2)
    said = [r for r in res.rows if r["source"] == "said"]
    check("place-returns-what-was-SAID", len(said) == 2, str(said))
    check("and-NOT-what-was-said-about-elsewhere",
          all("ridge" not in r["text"] for r in said), str(said))
    check("each-carries-its-folded-tier",
          all(r["tier"] == claims.SUPERPOSED for r in said), str(said))
    check("the-trace-explains-the-misses",
          any("MISS" in t for t in res.trace), str(res.trace))

    # a resolution CHANGES what the place reports — the point of the whole tier model
    uid = [u["id"] for u in claims.for_run(led.con, "r1") if "rite" in u["text"]][0]
    claims.resolve(led.con, "r1", uid, 2, claims.FICTION, "she was needling him")
    after = [r for r in read_api.place(led.con, "r1", "clifford", 2).rows if r["source"] == "said"]
    check("a-DECLINED-claim-drops-out-of-the-place", len(after) == 1, str(after))

    # AS OF bounds it: at turn 0 only the first thing had been said
    early = [r for r in read_api.place(led.con, "r1", "clifford", 0).rows if r["source"] == "said"]
    check("as-of-bounds-the-lore", len(early) == 1, str(early))


def test_place_reports_who_is_there_from_the_MOVED_snapshot(tmp):
    """The link to the emitting seat. Before it existed, agents.location was permanently the seed,
    so this row could only ever repeat what was authored."""
    from src.engine import world_events
    from src.engine.records import Event
    led = _led(tmp, "who")
    world_events.append(led, "r1", 2, [Event(type="move", actor="maren", payload={"to": "clifford"})])
    led.persist_snapshot("r1", 2, led.fold("r1", 2))

    rows = read_api.place(led.con, "r1", "clifford", 2).rows
    present = [r for r in rows if r["source"] == "present"]
    check("place-says-WHO-is-there", present and present[0]["who"] == ["maren"], str(rows))

    empty = read_api.place(led.con, "r1", "the ridge", 2)
    check("and-an-empty-place-TRACES-rather-than-erroring",
          not [r for r in empty.rows if r["source"] == "present"]
          and any("nobody is recorded" in t for t in empty.trace), str(empty.trace))


def test_the_DERIVED_half_is_append_only_too(tmp):
    """An append-only pair whose derived half is mutable is not append-only.

    `claim_extracts` is the index that drives contradiction detection and `read_api.place()`, and
    it shipped with no triggers: an extract could be edited so two utterances stopped contradicting
    each other, with the verbatim text untouched and nothing recording that anything changed. Same
    for `scene_cfgs.body` — a mutable body under a fixed fingerprint can be rewritten to lie about
    what a scene was pinned to, which is the whole point of pinning."""
    led = _led(tmp, "derived")
    uid = claims.record(led.con, "r1", 0, "maren", "Clifford was founded by shipwrights.",
                        extracts=[{"subject": "clifford", "predicate": "founded by",
                                   "object": "shipwrights"}])
    led.append_scene("r1", 0, "fireside", "maren", 0, 1, cfg={"name": "fireside"})

    for label, sql in (
        ("extract-update", "UPDATE claim_extracts SET object='miners' WHERE utterance_id=%d" % uid),
        ("extract-delete", "DELETE FROM claim_extracts WHERE utterance_id=%d" % uid),
        ("cfg-body-update", "UPDATE scene_cfgs SET body='{}'"),
        ("cfg-body-delete", "DELETE FROM scene_cfgs"),
    ):
        try:
            with led.con:
                led.con.execute(sql)
            check("the-db-refuses-%s" % label, False, "the write succeeded")
        except sqlite3.IntegrityError as e:
            check("the-db-refuses-%s" % label, "append-only" in str(e), str(e)[:90])

def test_every_LOG_LIKE_table_is_append_only(tmp):
    """DERIVED, not a hand-kept list of table names — the thing that would rot.

    Three groups shipped without triggers and were found by an adversarial sweep: `scenes` (whose
    own header calls itself append-only, and which the v14 cfg pin depends on), `decision_manifests`
    (what a decision READ — rewriting one falsifies provenance), and the bible trio (the hard-rule-1
    pin; `read_api.place` reads `bible_entities.what` by fingerprint).

    The MUTABLE set is the short one and is named here with its reason, so a new table defaults to
    protected-or-explained rather than to silence."""
    led = _led(tmp, "alltables")
    # Each entry states why the table MUST change over a run's life. `characters` was here with the
    # reason "re-registered on resume", which was false — `register_character` runs only on the
    # create-run branch — and the exemption was not free, because `Ledger._seed` reads the table to
    # seed the fold's agents. It is protected now. An exemption resting on a false reason is worse
    # than none: it reads as considered.
    mutable = {
        "runs":           "status and config change over a run's life",
        "current_state":  "a per-turn cache of the folded affect",
        "snapshots":      "the fold cache — a cache that cannot be rewritten is not a cache",
        "scheduler_state": "the scheduler's own bookkeeping",
        "llm_calls":      "token accounting, not canon",
        "dialogue_acts":  "no writer yet",
        "stance_snapshots": "no writer yet",
    }
    tables = {r["name"] for r in led.con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    # BOTH HALVES OF THE PAIR. "Has at least one trigger" counted a table carrying only an UPDATE
    # guard — or some future unrelated trigger — as fully protected, which claims more than the
    # query reads. Append-only means neither write succeeds, so the test asks for both by name.
    trigs = {r["name"] for r in led.con.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'")}
    protected = {t for t in tables
                 if {"%s_no_update" % t, "%s_no_delete" % t} <= trigs}
    half = sorted(t for t in tables - protected - set(mutable)
                  if any(n.startswith(t + "_no_") for n in trigs))
    check("no-table-carries-only-HALF-an-append-only-pair", not half,
          "update-only or delete-only: %s" % half)

    unguarded = sorted(tables - protected - set(mutable))
    check("every-log-like-table-has-append-only-triggers", not unguarded,
          "no triggers and not declared mutable: %s" % unguarded)
    stale = sorted(set(mutable) & protected)
    check("the-mutable-list-is-not-stale", not stale,
          "declared mutable but now protected: %s" % stale)

    # ...and the new triggers actually BITE. They must be fired against a NON-EMPTY table: a DELETE
    # matching no rows fires no BEFORE DELETE trigger, so the first version of this check "passed"
    # against empty tables and proved nothing. That is the guard-that-cannot-fail shape, caught here
    # by the check reporting success on a table it had never populated.
    led.append_scene("r1", 0, "fireside", "maren", 0, 1)
    with led.con:
        led.con.execute("INSERT INTO bibles (fingerprint, built_at, world, characters) "
                        "VALUES ('fp', 'now', '{}', '{}')")
    with led.con:
        led.con.execute("INSERT INTO bible_entities (fingerprint, kind, entity_id, what) "
                        "VALUES ('fp', 'location', 'clifford', 'a river town')")
        led.con.execute("INSERT INTO decision_manifests (run_id, turn, actor, manifest) "
                        "VALUES ('r1', 0, 'maren', '{}')")
    # UPDATE as well as DELETE. An UPDATE matching no rows fires no BEFORE UPDATE trigger, the same
    # way an empty DELETE fires none — the lesson that made the first version of this check pass
    # against empty tables while proving nothing. Every seeded table is bitten BOTH ways.
    seeded = ("scenes", "bibles", "bible_entities", "decision_manifests", "characters")
    for t in seeded:
        n = led.con.execute("SELECT COUNT(*) AS n FROM %s" % t).fetchone()["n"]
        check("the-%s-fixture-has-a-row" % t, n > 0, "empty: no trigger can fire")
        for verb, sql in (("delete", "DELETE FROM %s" % t),
                          ("update", "UPDATE %s SET run_id = run_id" % t if t in
                           ("scenes", "decision_manifests", "characters")
                           else "UPDATE %s SET fingerprint = fingerprint" % t)):
            try:
                with led.con:
                    led.con.execute(sql)
                check("the-db-refuses-an-%s-on-%s" % (verb, t), False, "the write succeeded")
            except sqlite3.IntegrityError as e:
                check("the-db-refuses-an-%s-on-%s" % (verb, t), "append-only" in str(e), str(e)[:70])

def test_NOT_NULL_does_not_mean_PRESENT(tmp):
    """SQLite satisfies NOT NULL with the empty string.

    Measured 2026-09-02, before the fix: a run with an empty run_id, a character with an empty
    char_id, an event with an empty type and a bible with an empty fingerprint ALL inserted clean.
    An empty identity joins to everything or to nothing; an empty type folds to nothing while
    looking like a recorded event. The Python layer refused them — this is the second wall, the
    same argument that grew the v9 append-only triggers: a rule enforced by one writer's habit has
    never been tested against a stranger's script.

    DERIVED from the schema, not a list: every identity/discriminator column is read out of the
    CREATE TABLE text and each one is required to carry the CHECK. A list here would rot the first
    time a table gained a column."""
    import re
    led = _led(tmp, "notnull")
    schema = io.open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read()

    # PROTECTED-OR-EXPLAINED, and the inversion is the whole repair. The first version of this test
    # enumerated columns from the schema but CLASSIFIED them against a hand-written set of names —
    # so a column whose name nobody had thought of was not reported as a hole, it was not considered
    # at all. That failed SILENT, and it hid seven: `stance_snapshots.character` and
    # `toward_deltas.primary_` sit inside a PRIMARY KEY and a UNIQUE, and neither name was in the
    # set. A classification list is the thing CLAUDE.md tabulates seven prior failures of.
    #
    # Now every TEXT NOT NULL / TEXT PRIMARY KEY column must be guarded OR carry a written reason
    # here. A new column defaults to FAILING. The reason is required text, not a bare membership,
    # because "why may this be blank" is the question the exemption is answering.
    EXEMPT = {
        # JSON — an empty document is caught at parse, where the shape is also checked.
        "runs.config": "JSON", "events.payload": "JSON", "turns.tags": "JSON",
        "turns.validation": "JSON", "characters.fixed": "JSON", "characters.baseline": "JSON",
        "current_state.affect": "JSON", "current_state.condition": "JSON",
        "arc_diffs.diff": "JSON", "acquisitions.belief": "JSON", "snapshots.value": "JSON",
        "recall_events.belief_refs": "JSON", "decision_manifests.manifest": "JSON",
        "scene_cfgs.body": "JSON", "edl.payload": "JSON", "scheduler_state.value": "JSON",
        "bibles.world": "JSON", "bibles.characters": "JSON",
        # TIMESTAMPS — written by the engine, never authored; an empty one is a code defect the
        # schema cannot distinguish from a legitimately unset clock.
        "runs.created_at": "timestamp", "turns.committed_at": "timestamp",
        "scene_cfgs.recorded_at": "timestamp", "bibles.built_at": "timestamp",
        # PROSE — the content columns. An empty one is an AUTHORING question, refused by the writer
        # that owns it (`claims.record` for `said`), not an integrity question for the database.
        "utterances.said": "prose", "bible_laws.statement": "prose",
        "stance_snapshots.position": "prose",
    }

    def _guarded(col, body):
        """Bound to THIS column, and read over the whole CREATE TABLE block.

        Both halves are repairs. Searching one LINE for any `<> ''` accepted a neighbour's guard as
        this column's, and reported `bible_laws.domain` as unguarded because its enum CHECK spans
        four lines. An enum counts — verified by insertion, an `IN (...)` list cannot contain the
        empty string — but only when it is this column's enum and does not list '' itself."""
        if "%s <> ''" % col in body:
            return True
        e = re.search(r"CHECK\s*\(\s*%s\s+IN\s*\((.*?)\)" % re.escape(col), body, re.S)
        return bool(e) and "''" not in e.group(1)

    unguarded = []
    # The block regex ends at a `);` that starts its own line — built with chr(10) rather than an
    # escape, because the escape is what a shell heredoc eats on the way in.
    block = r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)" + chr(10) + r"\);"
    for tbl, body in re.findall(block, schema, re.S):
        for line in body.splitlines():
            c = re.match(r"\s+(\w+)\s+TEXT\s+(NOT NULL|PRIMARY KEY)", line)
            if not c:
                continue
            col, name = c.group(1), "%s.%s" % (tbl, c.group(1))
            # DEFAULT '' is the ONE silent exit that stays: it is a positive declaration that empty
            # means "none given" here. A non-empty DEFAULT is not — it covers an OMITTED value and
            # an explicit '' still writes straight through it.
            if re.search(r"DEFAULT\s+''", line) or _guarded(col, body) or name in EXEMPT:
                continue
            unguarded.append(name)
    check("every-column-is-GUARDED-or-EXPLAINED", not unguarded,
          "neither refuses '' nor carries a reason: %s" % unguarded)
    check("no-exemption-is-a-BARE-membership", all(EXEMPT.values()),
          "an exemption with no reason is a hole with a comma")
    # RESOLVED INSIDE ITS OWN TABLE, because the first version tested the bare column WORD against
    # the whole schema text — and "config", "payload", "value" and "position" all occur in comments
    # and in other tables, so a dropped column kept its exemption unless the word left the FILE.
    # An exemption that outlives its column is the list going stale, which is the whole failure the
    # protected-or-explained shape exists to prevent.
    bodies = dict(re.findall(block, schema, re.S))
    stale = sorted(n for n in EXEMPT
                   if n.split(".")[0] not in bodies
                   or not re.search(r"^\s+%s\s+TEXT" % re.escape(n.split(".")[1]),
                                    bodies[n.split(".")[0]], re.M))
    check("no-exemption-names-a-column-that-is-GONE", not stale,
          "these exemptions name a table or column the schema no longer has: %s" % stale)

    # ...and the deliberately-optional ones must KEEP accepting it: for them empty means
    # "none given", and constraining those would refuse a legitimate authored value.
    try:
        with led.con:
            led.con.execute("INSERT INTO scenes (run_id, scene_no, label, start_turn, end_turn) "
                            "VALUES (?, 99, '', 0, 0)", ("r1",))
        check("an-optional-column-still-accepts-empty", True)
    except sqlite3.IntegrityError as e:
        check("an-optional-column-still-accepts-empty", False,
              "a DEFAULT '' column was constrained: %s" % e)

    # and the wall BITES on a real identity
    for label, sql in (("run_id", "INSERT INTO runs (run_id, created_at, status, config) "
                                  "VALUES ('', 'now', 'active', '{}')"),
                       ("event type", "INSERT INTO events (run_id, turn, caused_at, effective_at, "
                                      "type, visibility, payload) VALUES ('r1',0,0,0,'','public','{}')")):
        try:
            with led.con:
                led.con.execute(sql)
            check("the-db-refuses-an-empty-%s" % label.replace(" ", "-"), False, "it was accepted")
        except sqlite3.IntegrityError:
            check("the-db-refuses-an-empty-%s" % label.replace(" ", "-"), True)

def main():
    print("test_place.py — lore accretes, and a place is queryable\n")
    tmp = tempfile.mkdtemp(prefix="swe_place_test_")
    # PER-TEST, so one raiser does not take the file with it — the same fix test_world_appraisal
    # needed, found here the same way: a missing import killed the run and every later test was
    # skipped silently rather than one failure being reported.
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        try:
            fn(tmp)
        except Exception as e:                       # noqa: BLE001 — a harness reports, never raises
            FAILS.append("%s RAISED %s: %s" % (fn.__name__, type(e).__name__, e))
            print("  FAIL  %s RAISED %s: %s" % (fn.__name__, type(e).__name__, str(e)[:90]))
    print("\n%s" % ("test_place: OK (utterances persist, tier folds, a place answers)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
