#!/usr/bin/env python3
"""test_canonical_members.py — a guarded field is stored in its vocabulary's own spelling (gate canonical-members, 2026-09-26).

G6 (gate record-guards) left one declared residual: the database's insert guards hold each vocabulary exactly, so a
check loosened later - case, spacing, an alias; "tolerate the model's spelling" is this codebase's habit
(rungs.index_of, readings.canonical_path) - would accept a word the guard then refuses, rolling a validated beat back
mid-scene with ONE engine (DB_GUARD_REFUSED). The fix is one match, `records.member`, whose result each check keeps
and the unchanged writers store. Checked:

  [1] records.member returns the vocabulary's own element - the same object - for a matching value, text only, and
      refuses anything else by the code and words its caller gives; [1b] exact today AT EVERY CHECK, not only inside
      `member` (review 1): a case or space variant of each field is refused by that field's own code - `wound._check`
      called directly as well (review 2: every mint re-matches through `check_mint`, which hid a tidy inside `_check`) -
      toward.coalesce keeps a variant as its own row, and a path with no ladder is refused in the ladder's own words
      (the drivers commit a seat's refusal text to `turns.validation`)
  [2] each of the eight guarded one-of fields, validated, holds the vocabulary's own element (RelationshipDelta axis and
      order, RestDeclared axis, TowardDelta primary, a target bind's primary, Reading path and confidence, a minted
      wound's concept and path) - including for text whose str() is not its value, which the two coercing checks split:
      targets.write_binds stored str() of an exactly-checked primary, wound._check tested str() of a value stored raw
  [3] THE PROPERTY THIS GATE EXISTS FOR: with records.member loosened to a case- and space-blind match, as a later change
      might loosen it, a variant of every field is accepted and written through its real writer into a fresh database,
      stored in the vocabulary's spelling - and no guard refuses it; two spellings of one path in one beat, which
      would become one UNIQUE key, are merged (toward deltas, by toward.coalesce) or refused by name (a bind primary
      spelled two ways, whatever its targets). The mint rows carry the canonical id; a producer's id carries its own spelling (wound.make), so under a
      loosening such a mint is refused by the record layer (WOUND_MINT_ID_MISMATCH) - never by the database

Script-style: check(), main(), exit code. Stdlib only. Invented fixtures (maren, edda).
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import concepts, records, rungs, toward, wound          # noqa: E402
from src.engine.errors import EngineError                              # noqa: E402
from src.engine.ledger import Ledger                                   # noqa: E402
from src.engine.records import PATHS, Reading, RecordError, TurnCommit  # noqa: E402

FAILS = []
TMP = tempfile.TemporaryDirectory(prefix="swe_members_", ignore_cleanup_errors=True)
W = rungs.paths()[0]                           # a built path, and a rung on its ladder
WR = rungs.names_on(W)[0]


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %r" % (detail,)))
    if not ok:
        FAILS.append("%s: %r" % (name, detail))


def _code_of(call):
    try:
        call()
        return None
    except EngineError as e:
        return e.code
    except Exception as e:                                            # noqa: BLE001 - which way it fails is the check
        return type(e).__name__


class Lying(str):
    """Text whose str() is not its value: equal to a vocabulary word, printing as another."""

    def __str__(self):
        return "not-" + str.__str__(self)


class Masked(str):
    """Text whose value is not a vocabulary word but whose str() is one."""

    def __init__(self, value, shown=""):
        super().__init__()
        self.shown = shown

    def __new__(cls, value, shown=""):
        return super().__new__(cls, value)

    def __str__(self):
        return self.shown


def _commit(**kw):
    base = dict(run_id="r1", turn=1, actor="maren", thought="", action="", tags={}, affect={p: 0.0 for p in PATHS})
    base.update(kw)
    return TurnCommit(**base)


def _mint(concept="fire", path=None, wid=None):
    path = W if path is None else path
    return dict(wound.make("fire", W, 0.9, "run:1"), concept=concept, path=path,
                id=wid or wound.wound_id("fire", W))


# ---- [1] ---------------------------------------------------------------------------------------------------------

def the_match():
    print("[1] records.member returns the vocabulary's own element")
    axes = records.RELATIONSHIP_AXES
    got = records.member(Lying(axes[1]), axes, "RECORD_AXIS_UNKNOWN", "axis")
    check("a-matching-value-comes-back-as-the-vocabulary's-own-object", got is axes[1] and type(got) is str,
          (type(got).__name__, got))
    check("...from-a-dict's-keys-too-(the-concept-registry)",
          records.member(Lying("fire"), concepts.REGISTRY, "WOUND_CONCEPT_UNKNOWN", "c") is next(
              k for k in concepts.REGISTRY if k == "fire"))
    for name, value in (("another-word", "loyalty"), ("another-case", axes[0].upper()), ("a-space", " " + axes[0]),
                        ("a-number", 1), ("nothing", None), ("bytes", axes[0].encode())):
        try:
            records.member(value, axes, "RECORD_AXIS_UNKNOWN", "the caller's words %r" % (value,))
            said = None
        except RecordError as e:
            said = (e.code, e.detail)
        check("%s-is-refused-by-the-caller's-code-and-words" % name,
              said == ("RECORD_AXIS_UNKNOWN", "the caller's words %r" % (value,)), said)


def exact_today():
    print("[1b] exact today, at every check: a case or space variant is refused by its field's own code")
    axes, orders = records.RELATIONSHIP_AXES, records.RELATIONSHIP_ORDERS
    words = __import__("src.engine.readings", fromlist=["CONFIDENCE_WORDS"]).CONFIDENCE_WORDS
    cases = (
        ("RelationshipDelta.axis", "RECORD_AXIS_UNKNOWN",
         lambda v: records.RelationshipDelta("maren", "edda", v, 0.1).validate(), axes[0]),
        ("RelationshipDelta.order", "RECORD_ORDER_UNKNOWN",
         lambda v: records.RelationshipDelta("maren", "edda", axes[0], 0.1, order=v).validate(), orders[0]),
        ("RestDeclared.axis", "RECORD_AXIS_UNKNOWN", lambda v: records.RestDeclared("maren", "edda", v, 0.5).validate(),
         axes[1]),
        ("TowardDelta.primary", "RECORD_PRIMARY_UNKNOWN",
         lambda v: records.TowardDelta("maren", "edda", v, 0.1).validate(), PATHS[0]),
        ("a-bind's-primary", "RECORD_LIST_ITEM_TYPE", lambda v: _commit(target_binds=[(v, "edda")]).validate(),
         PATHS[1]),
        ("Reading.confidence", "READING_CONFIDENCE_UNKNOWN",
         lambda v: Reading(path=W, rung=WR, about="edda", confidence=v).validate(), words[0]),
        ("Reading.path", "READING_RUNG_NOT_ON_PATH", lambda v: Reading(path=v, rung=WR, about="edda").validate(), W),
        ("a-mint's-concept", "WOUND_CONCEPT_UNKNOWN", lambda v: wound.check_mint(_mint(concept=v)), "fire"),
        ("a-mint's-path", "WOUND_PATH_UNKNOWN", lambda v: wound.check_mint(_mint(path=v)), W),
    )
    # `wound._check` directly too (review 2): it also reads a sheet's authored wounds at run start, and every mint path
    # re-matches through `check_mint`, which would hide a tidy inside `_check`
    cases += (("wound._check's-path", "WOUND_PATH_UNKNOWN", lambda v: wound._check(dict(_mint(), path=v)), W),
              ("wound._check's-concept", "WOUND_CONCEPT_UNKNOWN", lambda v: wound._check(dict(_mint(), concept=v)),
               "fire"))
    for name, code, call, word in cases:
        got = [_code_of(lambda v=v: call(v)) for v in (word.swapcase(), " " + word)]
        check("%s:-%r-and-%r-refused-by-%s" % (name, word.swapcase(), " " + word, code), got == [code, code], got)
    # toward.coalesce merges on the vocabulary's element, never on a tidied spelling: a variant keeps its own row, and
    # TowardDelta.validate refuses it by name
    merged = toward.coalesce([records.TowardDelta("maren", "edda", PATHS[0], 0.1),
                              records.TowardDelta("maren", "edda", " " + PATHS[0].lower(), 0.2)])
    check("toward.coalesce-keeps-a-variant-as-its-own-row,-for-the-record-layer-to-refuse",
          len(merged) == 2 and _code_of(lambda: _commit(toward_deltas=merged).validate()) == "RECORD_PRIMARY_UNKNOWN",
          [(td.primary, td.delta) for td in merged])
    # A PATH WITH NO LADDER keeps the ladder's own words (review 1: the drivers commit a seat's refusal text to
    # `turns.validation`, and the match's shorter text had replaced them)
    try:
        Reading(path="SELF_REGARD", rung=WR, about="edda").validate()
        said = ""
    except RecordError as e:
        said = str(e)
    check("a-path-with-no-ladder-is-refused-in-the-ladder's-own-words,-its-built-paths-named",
          said.startswith("[READING_RUNG_NOT_ON_PATH] Reading names rung %r on 'SELF_REGARD', which does not resolve: "
                          "[RUNG_PATH_NOT_BUILT]" % WR) and "Built paths: " in said, said[:160])


# ---- [2] ---------------------------------------------------------------------------------------------------------

def each_field_keeps_the_element():
    print("[2] each guarded field, validated, holds the vocabulary's own element")
    axes, orders = records.RELATIONSHIP_AXES, records.RELATIONSHIP_ORDERS
    rd = records.RelationshipDelta("maren", "edda", Lying(axes[0]), 0.1, order=Lying(orders[1]))
    rd.validate()
    check("RelationshipDelta-axis-and-order", rd.axis is axes[0] and rd.order is orders[1], (rd.axis, rd.order))
    rr = records.RestDeclared("maren", "edda", Lying(axes[2]), 0.5)
    rr.validate()
    check("RestDeclared-axis", rr.axis is axes[2], rr.axis)
    td = records.TowardDelta("maren", "edda", Lying(PATHS[0]), 0.1)
    td.validate()
    check("TowardDelta-primary", td.primary is PATHS[0], td.primary)
    tc = _commit(target_binds=[(Lying(PATHS[1]), "edda"), [Lying(PATHS[2]), ""]])
    tc.validate()
    check("a-target-bind's-primary-(each-pair-keeps-its-type)", [type(b) for b in tc.target_binds] == [tuple, list]
          and tc.target_binds[0][0] is PATHS[1] and tc.target_binds[1][0] is PATHS[2], tc.target_binds)
    words = __import__("src.engine.readings", fromlist=["CONFIDENCE_WORDS"]).CONFIDENCE_WORDS
    r = Reading(path=Lying(W), rung=WR, about="edda", confidence=Lying(words[0]))
    r.validate()
    check("Reading-path-and-confidence", r.path is next(p for p in rungs.BANDS if p == W) and r.confidence is words[0],
          (r.path, r.confidence))
    try:                                           # a refusal here is a named FAIL, never a crash hiding the checks below
        m = wound.check_mint(_mint(concept=Lying("fire"), path=Lying(W)))
        ok, got = (m["concept"] is next(k for k in concepts.REGISTRY if k == "fire")
                   and m["path"] is next(p for p in PATHS if p == W)), (m["concept"], m["path"])
    except EngineError as e:
        ok, got = False, e.code
    check("a-minted-wound's-concept-and-path", ok, got)
    try:                                           # ...and a validated commit carries those strings, not the caller's
        tc = _commit(wound_mints=[_mint(concept=Lying("fire"), path=Lying(W))])
        tc.validate()
        ok, got = type(tc.wound_mints[0]["concept"]) is str and type(tc.wound_mints[0]["path"]) is str, tc.wound_mints
    except EngineError as e:
        ok, got = False, e.code
    check("...and-a-validated-commit's-mints-hold-them", ok, got)
    # the two splits, end to end: text equal to a word but printing as another reached targets.write_binds' str();
    # text printing as a word but equal to none passed wound._check's str() and was bound as itself
    led = Ledger(os.path.join(TMP.name, "split.db"))
    led.create_run("r1", {"catalog_version": "1"})
    wrote = _code_of(lambda: led.append_turn(_commit(turn=1, target_binds=[(Lying(PATHS[0]), "edda")])))
    got = led.con.execute("SELECT primary_ FROM target_binds WHERE turn = 1").fetchone()
    check("a-bind's-primary-whose-str()-lies-is-written-in-the-vocabulary's-spelling", wrote is None and got is not None
          and got[0] == PATHS[0], (wrote, got))
    masked = Masked("fire at the mill", shown="fire")
    code = _code_of(lambda: led.append_turn(_commit(turn=2, wound_mints=[_mint(concept=masked, wid=wound.wound_id(
        "fire", W))])))
    check("a-mint-concept-that-only-prints-as-a-word-is-refused-by-the-record-layer,-never-by-the-database",
          code == "WOUND_CONCEPT_UNKNOWN", code)
    led.con.close()


# ---- [3] ---------------------------------------------------------------------------------------------------------

def _loose(value, members, code, msg):
    """What a later change might make of the match: case- and space-blind. Still returns the vocabulary's element."""
    if isinstance(value, str):
        key = " ".join(value.split()).lower()
        for m in members:
            if m.lower() == key:
                return m
    raise RecordError(code, msg)


def a_looser_match_stores_the_vocabulary():
    print("[3] with the match loosened, every variant is written in the vocabulary's spelling, and no guard refuses it")
    axes, orders = records.RELATIONSHIP_AXES, records.RELATIONSHIP_ORDERS
    words = __import__("src.engine.readings", fromlist=["CONFIDENCE_WORDS"]).CONFIDENCE_WORDS
    led = Ledger(os.path.join(TMP.name, "loose.db"))
    led.create_run("r1", {"catalog_version": "1"})

    def one(sql):
        row = led.con.execute(sql).fetchone()
        return tuple(row) if row else None

    #: (field, the commit's variant fields, the query reading it back, the vocabulary's spelling)
    cases = (
        ("relationship_deltas.axis+ord", dict(rel_deltas=[records.RelationshipDelta(
            "maren", "edda", "  %s " % axes[0].upper(), 0.1, order=orders[1].title())]),
         "SELECT axis, ord FROM relationship_deltas WHERE turn = %d", (axes[0], orders[1])),
        ("rest_declared.axis", dict(rest_rows=[records.RestDeclared("maren", "edda", axes[1].title(), 0.5)]),
         "SELECT axis FROM rest_declared WHERE turn = %d", (axes[1],)),
        ("toward_deltas.primary_", dict(toward_deltas=[records.TowardDelta("maren", "edda", PATHS[0].lower(), 0.1)]),
         "SELECT primary_ FROM toward_deltas WHERE turn = %d", (PATHS[0],)),
        ("target_binds.primary_", dict(target_binds=[(" %s" % PATHS[1].lower(), "edda")]),
         "SELECT primary_ FROM target_binds WHERE turn = %d", (PATHS[1],)),
        ("readings.path+confidence", dict(readings=[Reading(path=W.lower(), rung=WR, about="edda",
                                                            confidence=words[0].upper())]),
         "SELECT path, confidence FROM readings WHERE turn = %d", (W, words[0])),
        ("wound_minted.concept+path", dict(wound_mints=[_mint(concept="FIRE ", path=W.lower())]),
         "SELECT concept, path FROM wound_minted WHERE turn = %d", ("fire", W)),
    )
    real = records.member
    records.member = _loose
    try:
        for turn, (name, fields, sql, want) in enumerate(cases, start=1):
            wrote = _code_of(lambda: led.append_turn(_commit(turn=turn, **fields)))
            got = one(sql % turn)
            check("%s:-accepted-and-stored-as-%s" % (name, "/".join(want)), wrote is None and got == want, (wrote, got))
        # TWO SPELLINGS OF ONE PATH IN ONE BEAT would become one UNIQUE key (review 1): toward deltas merge into one row
        # on the vocabulary's element; binds naming two targets under one primary are refused by name
        nxt = len(cases) + 1
        merged = toward.coalesce([records.TowardDelta("maren", "edda", PATHS[2], 0.1),
                                  records.TowardDelta("maren", "edda", " %s" % PATHS[2].title(), 0.2)])
        wrote = _code_of(lambda: led.append_turn(_commit(turn=nxt, toward_deltas=merged)))
        rows = led.con.execute("SELECT primary_, delta FROM toward_deltas WHERE turn = %d" % nxt).fetchall()
        check("two-spellings-of-one-toward-path:-merged-into-one-row-in-the-vocabulary's-spelling",
              wrote is None and len(merged) == 1 and [tuple(r) for r in rows] == [(PATHS[2], 0.1 + 0.2)],
              (wrote, len(merged), [tuple(r) for r in rows]))
        code = _code_of(lambda: led.append_turn(_commit(turn=nxt + 1, target_binds=[
            (PATHS[3], "edda"), (PATHS[3].lower(), "ada")])))
        check("two-spellings-of-one-bind-primary:-refused-by-the-record-layer,-never-by-the-database",
              code == "RECORD_LIST_ITEM_TYPE", code)
    finally:
        records.member = real
    led.con.close()


def main():
    print("test_canonical_members.py - a guarded field is stored in its vocabulary's own spelling (gate canonical-members)\n")
    for section in (the_match, exact_today, each_field_keeps_the_element, a_looser_match_stores_the_vocabulary):
        try:
            section()
        except Exception as e:                                       # noqa: BLE001 - a harness reports
            check("%s RAISED %s" % (section.__name__, type(e).__name__), False, str(e)[:200])
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
