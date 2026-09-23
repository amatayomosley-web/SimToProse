#!/usr/bin/env python3
"""test_attachments.py — bond gate 5: what a person holds that is not a person (bond-arithmetic.md s3).

The price table, the sheet block, the append-only rows, the fold, the registry with its two floors,
the stake, `received` by hold, the three-hander through floor.bond_moves, the debt deferral pinned,
the second order by hold, and the v29 -> v30 migration. Invented ids throughout (ash, bel, cato;
mill, chapel; guild) — nothing from any book (hard rule 1).
"""
import json
import os
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import attachments as A                              # noqa: E402
from src.engine import bonds, bond_rest, connection, floor           # noqa: E402
from src.engine.records import RecordError, PATHS                    # noqa: E402

FAILS = []
WORLD = {"locations": [{"id": "mill", "what": "the water-mill at the ford"}, {"id": "chapel", "what": "the chapel on the hill"}],
         "people": [{"id": "ash", "what": "the miller", "groups": ["guild"]}, {"id": "bel", "what": "the reeve"}, {"id": "cato", "what": "a carter"}]}
BLOCK = {"loc.mill": {"hold": 0.85, "sign": "+", "note": "life: she has run it since her father died"},
         "grp.guild": {"hold": 0.40, "sign": "+", "note": "member: attends when it sits"},
         "loc.chapel": {"hold": 0.15, "sign": "+", "note": "acquainted: buries her own there"}}


def check(name, ok, detail=""):
    print("  %s  %s" % ("PASS" if ok else "FAIL", name))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _raises(code, fn):
    try:
        fn()
        return False
    except RecordError as e:
        return e.code == code


def test_the_table():
    print("\n[1] THE TABLE — a word prices; a self-sourced word prices one rung below; the rubric carries no digit")
    check("the five words price", [A.hold_of(w) for w in ("life", "post", "member", "acquainted", "none")] == [.85, .60, .40, .15, .0])
    check("an off-table word is refused", _raises("ATTACH_WORD_UNKNOWN", lambda: A.hold_of("fond")))
    check("word_below walks life -> post -> member -> acquainted -> acquainted",
          [A.word_below(w) for w in A.RELATION_WORDS] == ["post", "member", "acquainted", "acquainted"])
    check("a keeper's self-sourced life prices as post", abs(A.declared_row("ash", "loc.mill", "life", "keeper", self_sourced=True).hold - .60) < 1e-9)
    check("...and that IS word_below('life') == 'post', not a coincidence of the .60/.85 numbers",
          A.word_below("life") == "post"
          and abs(A.declared_row("ash", "loc.mill", "life", "keeper", self_sourced=True).hold
                  - A.hold_of(A.word_below("life"))) < 1e-9)
    check("the rubric names the four words and no digit", all(w in A.rubric() for w in A.RELATION_WORDS) and not any(ch.isdigit() for ch in A.rubric()))


def test_names_for():
    print("\n[2] NAMES — what the world registers: its locations and the group tags its people carry")
    check("sorted, prefixed", A.names_for(WORLD) == ["grp.guild", "loc.chapel", "loc.mill"], A.names_for(WORLD))
    check("a non-dict world is refused", _raises("ATTACH_WORLD_NOT_A_DICT", lambda: A.names_for(["mill"])))


def test_validate_block():
    print("\n[3] THE BLOCK — registered keys pass; the six refusals; an absent sign reads +")
    names = A.names_for(WORLD)
    check("a registered block passes", A.validate_block(BLOCK, registered=names) is BLOCK)
    check("an unregistered place is refused", _raises("ATTACH_ENTITY_UNREGISTERED", lambda: A.validate_block({"loc.tower": {"hold": .5}}, registered=names)))
    check("a person key is refused", _raises("ATTACH_KEY_UNPREFIXED", lambda: A.validate_block({"bel": {"hold": .5}})))
    check("a hold outside [0, 1] is refused", _raises("ATTACH_HOLD_RANGE", lambda: A.validate_block({"loc.mill": {"hold": 1.2}})))
    check("a sign off the pair is refused", _raises("ATTACH_SIGN_UNKNOWN", lambda: A.validate_block({"loc.mill": {"hold": .5, "sign": "*"}})))
    check("three life holds are refused", _raises("ATTACH_LIFE_CAP", lambda: A.validate_block({"loc.a": {"hold": .85}, "loc.b": {"hold": .85}, "loc.c": {"hold": .9}})))
    check("two life holds pass", A.validate_block({"loc.a": {"hold": .85}, "loc.b": {"hold": .9}}) is not None)
    check("an absent sign reads +", A.holds_of({"loc.mill": {"hold": .5}}) == {"loc.mill": .5})


def test_holds_of():
    print("\n[4] HOLDS — the numbers held_map folds: + entries, floats only")
    check("a - entry is skipped", A.holds_of({"loc.mill": {"hold": .5, "sign": "-"}, "grp.guild": {"hold": .4}}) == {"grp.guild": .4})
    check("None -> {}", A.holds_of(None) == {})
    check("a string hold is refused", _raises("ATTACH_HOLD_RANGE", lambda: A.holds_of({"loc.mill": {"hold": "much"}})))


def _ledger():
    from src.engine.ledger import Ledger
    led = Ledger(":memory:")
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    led.register_character("r", "ash", {"id": "ash", "name": "Ash"}, {"relationship_priors": {"default_trust": .4}})
    return led


def test_the_rows():
    print("\n[5] THE ROWS — seed once, declare once, log order, append-only by trigger")
    led = _ledger()
    n1 = A.seed(led.con, "r", 0, "ash", BLOCK)
    n2 = A.seed(led.con, "r", 2, "ash", BLOCK)
    check("seed writes one authored row per held thing", n1 == 3, n1)
    check("and is idempotent", n2 == 0, n2)
    row = A.declared_row("ash", "loc.mill", "none", "director")
    d1 = A.declare(led.con, "r", 4, [row])
    d2 = A.declare(led.con, "r", 4, [row])
    check("declare writes the director's row at hold 0 for none", d1 == 1 and abs(row.hold) < 1e-9, (d1, row.hold))
    check("and does not double-declare", d2 == 0, d2)
    rows = A.rows_for(led.con, "r", "ash")
    check("rows_for returns them in log order", [(r[0], r[1]) for r in rows] == [(0, "loc.mill"), (0, "grp.guild"), (0, "loc.chapel"), (4, "loc.mill")], rows)
    check("the director's row carries its source", rows[-1][4] == "director", rows[-1])
    for stmt, name in (("UPDATE attachment_declared SET hold = 0.1", "UPDATE"), ("DELETE FROM attachment_declared", "DELETE")):
        try:
            led.con.execute(stmt); check("%s is refused by the trigger" % name, False, "accepted")
        except sqlite3.IntegrityError as e:
            check("%s is refused by the trigger" % name, "append-only" in str(e), str(e)[:60])
    return led


def test_the_fold():
    print("\n[6] THE FOLD — rest, hold, time, edge within a turn; the block folds in place; no block refuses")
    from src.engine.records import Event, TurnCommit, RestDeclared, RelationshipDelta
    led = _ledger()
    A.seed(led.con, "r", 0, "ash", BLOCK)
    bond_rest.seed(led.con, "r", 0, "ash", {"bel": {"trust": .6, "affinity": .5, "respect": .5, "debt": .0}})
    led.append_turn(TurnCommit(run_id="r", turn=4, actor="ash", thought="-", action="-", tags={}, validation={"ok": True},
                               affect={p: .2 for p in PATHS}, condition={"energy": .7},
                               events=[Event(type="mundane", payload={"text": "x"}, actor="ash")],
                               rel_deltas=[RelationshipDelta(perceiver="ash", target="bel", axis="trust", delta=.02, order="first")],
                               rest_rows=[RestDeclared(perceiver="ash", target="bel", axis="trust", rest=.15, source="cliff")]))
    A.declare(led.con, "r", 4, [A.declared_row("ash", "loc.mill", "none", "director")])
    led.declare_time("r", 4, 1.0, source="test")
    tl = led.timeline_for("r", "ash")
    at4 = [t[0] for t in tl if True][-4:]
    check("kinds within turn 4 run rest, hold, time, edge", [t[0] for t in tl][-4:] == ["rest", "hold", "time", "edge"], [t[0] for t in tl])
    check("the hold item is ('hold', entity, hold, sign)", ("hold", "loc.mill", 0.0, "+") in tl, tl)
    block = json.loads(json.dumps(BLOCK))
    rels = {"bel": {"trust": .6, "affinity": .5, "respect": .5, "debt": .0}}
    bond_rest.rehydrate(rels, {"default_trust": .4}, tl, attachments=block)
    check("the director's row wins on the block", abs(block["loc.mill"]["hold"]) < 1e-9 and block["loc.mill"]["note"].startswith("life:"), block["loc.mill"])
    check("the other holds stand", abs(block["grp.guild"]["hold"] - .4) < 1e-9)
    check("a hold row with no block is refused", _raises("BONDS_HOLD_ROW_UNFOLDED", lambda: bond_rest.rehydrate({}, {}, [("hold", "loc.mill", .85, "+")])))
    check("a timeline with no hold item needs no block", bond_rest.rehydrate({"bel": {"trust": .6}}, {}, [("rest", "bel", "trust", .5), ("time", 1.0)]) is not None)


def test_the_registry():
    print("\n[7] THE REGISTRY — one map, two readers, two floors")
    char = {"baseline": {"wounds": [], "drives": {"goals": [{"priority": .7}]}, "model": {"schwartz": {"security": .6}}},
            "current": {"attachments": BLOCK}}
    held = connection.held_map(char)
    check("attachments sit beside goals and values", held.get("loc.mill") == .85 and held.get("grp.guild") == .4 and "goal:0" in held and "value:security" in held, sorted(held))
    check("a - entry is not in the map", "loc.mill" not in connection.held_map({"current": {"attachments": {"loc.mill": {"hold": .85, "sign": "-"}}}}))
    check("for_about reads a held place", abs(connection.for_about({}, held, "loc.mill", "DEFLATION") - .85) < 1e-9)
    check("for_about floors an acquainted place at .20", connection.for_about({}, {"loc.chapel": .15}, "loc.chapel") == 0.0)
    check("stake_of reads the same .15 unfloored", abs(bonds.stake_of("bel", "loc.chapel", {}, held={"loc.chapel": .15}) - .15) < 1e-9)
    check("a held place scales every dimension", connection.scales("threat", "loc.mill") is True)


def test_stake():
    print("\n[8] STAKE — the s5 numbers with a held thing")
    held = A.holds_of(BLOCK)
    check("herself 1", bonds.stake_of("bel", "bel", {}, held=held) == 1.0)
    check("a person at affinity .70 -> .40", abs(bonds.stake_of("bel", "cato", {"cato": {"affinity": .70}}, held=held) - .40) < 1e-9)
    check("her mill .85", abs(bonds.stake_of("bel", "loc.mill", {}, held=held) - .85) < 1e-9)
    check("her guild .40", abs(bonds.stake_of("bel", "grp.guild", {}, held=held) - .40) < 1e-9)
    check("an unheld place 0", bonds.stake_of("bel", "loc.tower", {}, held=held) == 0.0)
    check("a T2 name 0", bonds.stake_of("bel", "the ford", {}, held=held) == 0.0)
    check("a dict-valued concept entry 0", bonds.stake_of("bel", "concept:grief", {}, held={"concept:grief": {"DEFLATION": .9}}) == 0.0)


def _tags(obj, sev="marked"):
    from src.engine.severity import normalise_dimensions
    return normalise_dimensions({"type": "aid", "dimensions": {"care_relevant": sev}, "durability": "transient",
                                 "object": obj, "showed": {"affinity": .78, "trust": .56}})


def test_received_and_overt():
    print("\n[9] RECEIVED — an act on her held place is done to her, and so is overt")
    held = A.holds_of(BLOCK)
    act = bonds.act_from_tags(_tags("loc.mill", "moderate"), "ash", "bel", held=held)
    check("received by hold", act and act["received"] is True, act)
    check("witnessed at sev .30 with no perception skill (received is overt; the edge is acquaintance)",
          bonds.witnessed(act, {"perception": 0.1}, {"trust": .55}))
    act0 = bonds.act_from_tags(_tags("loc.mill", "moderate"), "ash", "bel", held={})
    check("without the hold: not received", act0 and act0["received"] is False, act0)
    check("...and not witnessed, same skills, same edge", not bonds.witnessed(act0, {"perception": 0.1}, {"trust": .55}))


def _actors():
    def sheet(cid, block):
        return {"char": {"fixed": {"id": cid, "name": cid.title()},
                         "baseline": {"skills": {"perception": .1}, "model": {}, "relationship_priors": {"default_trust": .5},
                                      "wounds": [], "drives": {"goals": []}},
                         "current": {"relationships": {"ash": {"trust": .55, "affinity": .55, "respect": .50, "debt": .0}},
                                     "attachments": block}}}
    return {"ash": sheet("ash", {}), "bel": sheet("bel", {"loc.mill": {"hold": .85, "sign": "+", "note": "life"}}), "cato": sheet("cato", {})}


def test_the_three_hander():
    print("\n[10] THE THREE-HANDER — ash acts on the mill; bel holds it, cato does not")
    actors = _actors()
    moves = {w: (d, v) for w, d, v, _c in floor.bond_moves(actors, ["ash", "bel", "cato"], "ash", _tags("loc.mill", "marked"))}
    check("bel: affinity, trust and a their_view delta", "bel" in moves and "affinity" in moves["bel"][0] and "trust" in moves["bel"][0] and moves["bel"][1], moves.get("bel"))
    check("cato: a trust delta only (the .30 stake floor), no affinity, no their_view",
          "cato" in moves and "trust" in moves["cato"][0] and "affinity" not in moves["cato"][0] and not moves["cato"][1], moves.get("cato"))
    check("cato's trust gain is smaller than bel's", "cato" in moves and "bel" in moves and moves["cato"][0]["trust"] < moves["bel"][0]["trust"], (moves.get("cato"), moves.get("bel")))
    check("respect is absent (the act named none)", all("respect" not in d for d, _v in moves.values()))
    moves2 = {w: (d, v) for w, d, v, _c in floor.bond_moves(actors, ["ash", "bel", "cato"], "ash", _tags("loc.mill", "moderate"))}
    check("at moderate: cato is not witnessed at all, bel still moves (received only for her)", "cato" not in moves2 and "bel" in moves2, sorted(moves2))


def test_debt_deferral():
    print("\n[11] DEBT — a transfer to a held thing posts nothing (deferred, pinned)")
    from src.engine.severity import normalise_dimensions
    t = normalise_dimensions({"type": "aid", "dimensions": {"care_relevant": "marked"}, "durability": "transient", "object": "bel",
                              "transfers": [{"what": "the purse", "from": "ash", "to": "loc.mill", "terms": "none"}]})
    check("to a place: []", bonds.debt_postings(t, "ash", {"bel": {"ash": 0.0}}, present=["ash", "bel"]) == [])
    t2 = dict(t, transfers=[{"what": "the purse", "from": "ash", "to": "bel", "terms": "none"}])
    posts = bonds.debt_postings(t2, "ash", {"bel": {"ash": 0.0}}, present=["ash", "bel"])
    check("to a person: one gave on her account", len(posts) == 1 and posts[0][:3] == ("bel", "ash", "gave"), posts)


def test_reflect_by_hold():
    print("\n[12] THE SECOND ORDER — scaled by the hold")
    act = bonds.act_from_tags(_tags("loc.mill"), "ash", "bel", held={"loc.mill": .85})
    edge = {"trust": .55, "affinity": .55, "respect": .5, "debt": .0}
    full = bonds.reflect(edge, act, {}, stake=1.0)
    part = bonds.reflect(edge, act, {}, stake=.85)
    check("reflect at .85 == .85 x reflect at 1.0", full and part and abs(part["affinity"] - .85 * full["affinity"]) < 1e-6, (full, part))


def test_the_migration():
    print("\n[13] THE MIGRATION — a v29 db gains the table and both triggers; a newer one is refused")
    from src.engine import db as _db
    schema = open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read()
    d = tempfile.mkdtemp()
    p = os.path.join(d, "v29.db")
    con = sqlite3.connect(p); con.executescript(schema); con.execute("DROP TABLE attachment_declared"); con.execute("PRAGMA user_version = 29"); con.commit(); con.close()
    con = _db.connect(p)
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE name LIKE 'attachment_declared%'")}
    ver = con.execute("PRAGMA user_version").fetchone()[0]
    con.close()
    check("the table and both triggers exist after open", names >= {"attachment_declared", "attachment_declared_no_update", "attachment_declared_no_delete"}, names)
    check("user_version is the engine's SCHEMA_VERSION", ver == _db.SCHEMA_VERSION, ver)
    p2 = os.path.join(d, "v31.db")
    con = sqlite3.connect(p2); con.executescript(schema); con.execute("PRAGMA user_version = %d" % (_db.SCHEMA_VERSION + 1)); con.commit(); con.close()
    try:
        _db.connect(p2); check("a newer db is refused", False, "opened")
    except RecordError as e:
        check("a newer db is refused", e.code == "DB_SCHEMA_TOO_NEW", e.code)


def test_word_of():
    print("\n[14] WORD_OF -- the inverse of the table: the warmest word priced at or below the hold")
    check("life at .85", A.word_of(.85) == "life", A.word_of(.85))
    check("post at .60", A.word_of(.60) == "post", A.word_of(.60))
    check("member at .40", A.word_of(.40) == "member", A.word_of(.40))
    check("acquainted at .15", A.word_of(.15) == "acquainted", A.word_of(.15))
    check("nearest at or below: .70 prices as post", A.word_of(.70) == "post", A.word_of(.70))
    check("the ceiling: 1.0 still reads as life (no word above it)", A.word_of(1.0) == "life")
    check("0 refuses -- a none hold has no word", _raises("ATTACH_HOLD_UNWORDED", lambda: A.word_of(0)))
    check("below the floor but not zero still refuses", _raises("ATTACH_HOLD_UNWORDED", lambda: A.word_of(.10)))
    check("a non-numeric hold is refused as out-of-range, not unworded",
          _raises("ATTACH_HOLD_RANGE", lambda: A.word_of("much")))
    check("word_of and hold_of round-trip on the table's own four prices",
          all(A.word_of(A.hold_of(w)) == w for w in A.RELATION_WORDS), A.RELATION_WORDS)


def main():
    print("test_attachments.py — bond gate 5, pinned\n")
    for fn in sorted((v for k, v in globals().items() if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print("\n%s" % ("test_attachments: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
