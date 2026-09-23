#!/usr/bin/env python3
"""test_bond_law.py — THE LAW's table (bond-arithmetic.md s6) pinned number by number, and the rest.

Bond gate 4 of 6 (2026-09-17). `tests/test_bonds.py` tells the tier's stories; this file is the
ledger of the law's NUMBERS — the fourteen worked cases of s6 through `law_delta` alone, the alpha
table, stake, the gains, overtness, the cliff, the debt entries, the rest row's round trip, the
ordered fold, and the replay path (`tests/bond_replay.py`) driven over invented beats. It is
its own suite (not [20] of test_bonds) because test_bonds passed 900 lines and the law deserves a
file a reader can hold whole. Every number is the one Fable's simulation reproduced against the
doc (cairn/projects/reviews/2026-09-17-simtoprose-bond-gate4-plan-fable.md, part 3) — a test that
pins the doc's table is how the doc and the code are kept from drifting apart.

Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bonds, bond_rest                              # noqa: E402
from src.engine.records import RecordError, RestDeclared, PATHS      # noqa: E402

FAILS = []
_UNIT = {"moral_foundations": {k: 1.0 for k in ("fairness", "loyalty", "care_harm", "authority", "sanctity", "liberty")},
         "schwartz": {k: 1.0 for k in ("benevolence", "security", "achievement", "power", "self_direction",
                                       "universalism", "conformity", "tradition", "hedonism", "stimulation")},
         "needs": {k: 1.0 for k in ("relatedness", "competence", "autonomy")}}
_LOYAL = {"moral_foundations": {"fairness": 0.95, "loyalty": 0.95, "care_harm": 0.8},
          "schwartz": {"benevolence": 0.8, "security": 0.6}, "needs": {"relatedness": 0.8}}
_INDIFFERENT = {"moral_foundations": {"fairness": 0.05, "loyalty": 0.05, "care_harm": 0.2},
                "schwartz": {"benevolence": 0.2, "security": 0.3}, "needs": {"relatedness": 0.2}}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % detail))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _walk(o, e, n, rates=None):
    """e -> the edge after n acts of word-height o through the ungained law."""
    x = float(e)
    for _ in range(n):
        x += bonds.law_delta(o, x, *(rates or ()))
    return x


def _tags(showed, dims=None, obj="b", **kw):
    t = {"dimensions": dims or {"care_relevant": 0.6}, "durability": "durable", "object": obj, "showed": dict(showed)}
    t.update(kw)
    return t


# --- [1] the s6 table through law_delta alone ------------------------------------------------

def test_the_table():
    print("\n[1] THE TABLE — the fourteen s6 numbers through law_delta (g = 1)")
    from src.engine import severity as S
    h = lambda ax, w: S.act_value_of(ax, w)                                   # the ladder heights
    rows = (
        ("Watson .75, twelve kind",              _walk(h("affinity", "kind"), .75, 12),        .774),
        ("Watson .75, three curt",               _walk(h("affinity", "curt"), .75, 3),         .718),
        ("distrusted .30 + dishonest",           _walk(h("trust", "dishonest"), .30, 1),       .240),
        ("stranger .50 + dishonest",             _walk(h("trust", "dishonest"), .50, 1),       .380),
        ("stranger .50 + dependable",            _walk(h("trust", "dependable"), .50, 1),      .522),
        ("generous from enemy .20",              _walk(h("affinity", "generous"), .20, 1),     .239),
        ("generous from friend .90",             _walk(h("affinity", "generous"), .90, 1),     .900),
        ("treacherous by trusted .90 (slope)",   _walk(h("trust", "treacherous"), .90, 1),     .708),
        ("treacherous by schemer .20 (slope)",   _walk(h("trust", "treacherous"), .20, 1),     .155),
        ("Jane: six steadfast",                  _walk(h("trust", "steadfast"), .50, 6),       .741),
        ("stranger, forty kind",                 _walk(h("affinity", "kind"), .50, 40),        .778),
        ("stranger, forty selfless",             _walk(h("affinity", "selfless"), .50, 40),    .947),
    )
    for name, got, doc in rows:
        check("%s -> %.3f" % (name, doc), abs(got - doc) < 1e-3, "%.4f" % got)
    jane = _walk(h("trust", "steadfast"), .50, 6)
    jane = _walk(h("trust", "treacherous"), jane, 1)
    check("Jane: then one treacherous (slope) -> .587", abs(jane - .587) < 1e-3, "%.4f" % jane)
    jane = _walk(h("trust", "straight"), jane, 8)
    check("Jane: then eight straight -> .711", abs(jane - .711) < 1e-3, "%.4f" % jane)
    # the anchor holds: sixty and three hundred kind acts stop at the same place
    sixty, many = _walk(h("affinity", "kind"), .75, 60), _walk(h("affinity", "kind"), .75, 300)
    check("sixty kind on .75 -> .78", abs(sixty - .78) < 1e-3, "%.4f" % sixty)
    check("three hundred == sixty (the anchor, not the count)", abs(many - sixty) < 1e-4 and abs(many - .78) < 1e-4, "%.5f vs %.5f" % (many, sixty))
    check("generous on .90 moves nothing", bonds.law_delta(h("affinity", "generous"), .90) == 0.0)
    check("devoted .90 + one kind moves nothing", bonds.law_delta(h("affinity", "kind"), .90) == 0.0)
    # the reach clamps: the outermost word's target is .95 / .05, one rung of grace past .90 / .10
    check("steadfast on .50 targets .95", abs(bonds.law_delta(h("trust", "steadfast"), .50) - bonds._ALPHA_POS * bonds._REACH) < 1e-9)
    check("treacherous on .50 targets .05", abs(bonds.law_delta(h("trust", "treacherous"), .50) + bonds._ALPHA_NEG * bonds._REACH) < 1e-9)
    # per witness: the same dishonest act from a stranger at each pair
    check("stranger + dishonest at a fast withdrawer's rates -> .32", abs(_walk(h("trust", "dishonest"), .5, 1, (.06, .45)) - .32) < 1e-6)
    check("...and at a slow one's -> .42", abs(_walk(h("trust", "dishonest"), .5, 1, (.12, .20)) - .42) < 1e-6)


# --- [2] through observe, at unit relevance ----------------------------------------------------

def test_through_observe():
    print("\n[2] THROUGH OBSERVE — with every value at 1.0 and stake 1, the gain is the identity")
    e = {"affinity": .75}
    for _ in range(12):
        e = bonds.apply_deltas(e, bonds.observe(e, bonds.act_from_tags(_tags({"affinity": "kind"}), "a", "b"), _UNIT))
    check("Watson's twelve kind acts land at .7735", abs(e["affinity"] - .7735) < 1e-4, "%.4f" % e["affinity"])


# --- [3] the alpha table -----------------------------------------------------------------------

def test_the_alpha_table():
    print("\n[3] THE ALPHA TABLE — relationship_priors.update, per witness")
    for g, pos in bonds._RATE_POS.items():
        for w, neg in bonds._RATE_NEG.items():
            got = bonds.rates_of({"update": {"grant_threshold": g, "withdraw_speed": w}})
            check("%s/%s -> (%.2f, %.2f)" % (g, w, pos, neg), got == (pos, neg), got)
    check("no update -> the constants", bonds.rates_of({}) == (bonds._ALPHA_POS, bonds._ALPHA_NEG))
    check("grant_threshold alone -> (.06, .30) for high", bonds.rates_of({"update": {"grant_threshold": "high"}}) == (.06, bonds._ALPHA_NEG))
    try:
        bonds.rates_of({"update": {"grant_threshold": "sometimes"}})
        check("an off-table word refuses", False, "accepted")
    except RecordError as ex:
        check("an off-table word refuses", ex.code == "BONDS_RATE_WORD_UNKNOWN", ex.code)


# --- [4] stake ---------------------------------------------------------------------------------

def test_stake():
    print("\n[4] STAKE — how much the witness holds the object (s5)")
    check("herself -> 1", bonds.stake_of("b", "b", {}) == 1.0)
    check("a person she holds at .8 -> .6", abs(bonds.stake_of("c", "b", {"b": {"affinity": .8}}) - .6) < 1e-9)
    check("a person she holds at .3 -> 0 (no negative stake)", bonds.stake_of("c", "b", {"b": {"affinity": .3}}) == 0.0)
    check("a thing she holds -> the hold (gate 5's hook)", bonds.stake_of("c", "loc.orphanage", {}, held={"loc.orphanage": .85}) == .85)
    check("no object -> 0", bonds.stake_of("c", "", {}) == 0.0)
    check("an unknown id -> 0", bonds.stake_of("c", "x", {"b": {"affinity": .9}}) == 0.0)
    # `self` is the actor as a person: resolved by act_from_tags, priced by the witness's hold on him
    own = bonds.act_from_tags(_tags({"respect": "sharp", "affinity": "kind"}, obj="self"), "a", "c")
    check("self resolves to the actor's id", own["object"] == "a" and own["received"] is False, own)
    check("...and a witness who holds him prices it by her affinity", abs(bonds.stake_of("c", own["object"], {"a": {"affinity": .75}}) - .5) < 1e-9)
    check("...a stranger prices it at 0", bonds.stake_of("c", own["object"], {}) == 0.0)
    check("...and the actor holds no edge to himself", bonds.act_from_tags(_tags({"respect": "sharp"}, obj="self"), "a", "a") is None)


# --- [5] the gains -----------------------------------------------------------------------------

def test_the_gains():
    print("\n[5] THE GAINS — respect in full, trust at its floor, affinity and debt by the hold")
    both = _tags({"trust": "dependable", "affinity": "generous", "respect": "masterly"})
    rec = bonds.observe({}, bonds.act_from_tags(both, "a", "b"), _LOYAL)
    byst = bonds.observe({}, bonds.act_from_tags(both, "a", "c"), _LOYAL, stake=0.0)
    print("       received %s\n       bystander at stake 0 %s" % (rec, byst))
    check("respect moves the bystander in full", abs(byst["respect"] - rec["respect"]) < 1e-9, "%s vs %s" % (byst.get("respect"), rec.get("respect")))
    check("trust at .30 of the received move", abs(byst["trust"] / rec["trust"] - bonds._TRUST_STAKE_FLOOR) < 1e-6, "%s vs %s" % (byst.get("trust"), rec.get("trust")))
    check("affinity not at all", "affinity" not in byst, byst)
    check("debt never through observe", "debt" not in rec and "debt" not in byst, "%s %s" % (rec, byst))
    half = bonds.observe({}, bonds.act_from_tags(both, "a", "c"), _LOYAL, stake=0.5)
    check("at stake .5 affinity is half the received move", abs(half["affinity"] * 2 - rec["affinity"]) < 1e-6, "%s vs %s" % (half.get("affinity"), rec.get("affinity")))


# --- [6] overtness -----------------------------------------------------------------------------

def test_overtness():
    print("\n[6] OVERTNESS — you do not miss what is done to you")
    subtle = _tags({"affinity": "curt"}, dims={"social_violation": .25})
    dull, sharp = {"perception": .2, "insight": .9}, {"perception": .9, "insight": .9}
    check("a received subtle act is witnessed by the dullest", bonds.witnessed(bonds.act_from_tags(subtle, "a", "b"), dull, {}))
    check("the same act, not received, is missed by the dull", not bonds.witnessed(bonds.act_from_tags(subtle, "a", "c"), dull, {}))
    check("...and caught by the sharp", bonds.witnessed(bonds.act_from_tags(subtle, "a", "c"), sharp, {}))


# --- [7] the cliff -----------------------------------------------------------------------------

def test_the_cliff():
    print("\n[7] THE CLIFF — the floor word at relevance, whatever the strength")
    e = {"trust": .85}
    slight = bonds.act_from_tags(_tags({"trust": "treacherous"}, dims={"social_violation": .15}), "a", "b")
    above = bonds.act_from_tags(_tags({"trust": "dishonest"}, dims={"social_violation": .9}), "a", "b")
    check("the word at `slight` cliffs", abs(bonds.apply_deltas(e, bonds.observe(e, slight, _LOYAL))["trust"] - bonds._CLIFF_FLOOR) < 1e-6)
    check("the rung above at .9 slopes", abs(bonds.apply_deltas(e, bonds.observe(e, above, _LOYAL))["trust"] - .7495) < 1e-3)
    check("cliff_axes names the word", bonds.cliff_axes(e, slight, _LOYAL) == ("trust",) and bonds.cliff_axes(e, above, _LOYAL) == ())
    check("no cliff below the relevance bar", bonds.cliff_axes(e, slight, _INDIFFERENT) == ())
    got = {att: bonds.observe({"trust": .80}, bonds.act_from_tags(_tags({"trust": "treacherous"}, dims={"social_violation": .9}, attribution=att), "a", "b"), _LOYAL)["trust"]
           for att in ("malice", "negligence", "coerced", "accident")}
    check("the target follows attribution", abs(got["malice"] + .65) < 1e-4 and abs(got["negligence"] + .4881) < 1e-3
          and abs(got["coerced"] + .2993) < 1e-3 and abs(got["accident"] + .1914) < 1e-3, got)


# --- [8] debt ----------------------------------------------------------------------------------

def test_debt():
    print("\n[8] DEBT — the seat's TRANSFERS, priced once per pair at _DEBT_RATE x severity; the entry from the words")
    r = bonds._DEBT_RATE
    T = lambda rows, dims=None, **kw: dict(_tags({}, dims=dims, **kw), transfers=rows)
    row = lambda what, f, t, terms: {"what": what, "from": f, "to": t, "terms": terms}
    # the things are invented, from a village tool library's Saturday counter (hard rule 1)
    for sev, want in ((.30, .015), (.78, .039), (.60, .030)):
        got = bonds.debt_postings(T([row("the spare hinges", "a", "b", "none")], dims={"care_relevant": sev}), "a", {}, present=["a", "b"])
        check("a gift at %.2f -> +%.3f on the receiver" % (sev, want), got == [("b", "a", "gave", round(want, 6), "the spare hinges")], got)
    check("a loan posts as a gift too (the account is what is owed)", bonds.debt_postings(T([row("the hedge trimmer", "a", "b", "loan")]), "a", {}, present=["a", "b"])[0][2:4] == ("gave", .03))
    check("a price is square", bonds.debt_postings(T([row("a box of screws", "a", "b", "price")]), "a", {}, present=["a", "b"]) == [])
    check("a repayment lowers the giver's own account", bonds.debt_postings(T([row("the sander", "b", "a", "repayment")]), "b", {"b": {"a": .2}}, present=["a", "b"]) == [("b", "a", "repaid", -.03, "the sander")])
    check("...and posts nothing when nothing is owed", bonds.debt_postings(T([row("the sander", "b", "a", "repayment")]), "b", {"b": {"a": 0.0}}, present=["a", "b"]) == [])
    # THE DIRECTION IS THE TRANSFER'S, NOT THE SPEAKER'S — three invented cases on the same table
    took = bonds.debt_postings(T([row("the pressure washer", "a", "self", "loan"), row("the extension lead", "a", "self", "loan")], dims={"care_relevant": .35}), "b", {"b": {"a": .06}}, present=["a", "b"])
    check("things taken on one's own beat post on the ACTOR's account, once for two things", took == [("b", "a", "gave", .0175, "the pressure washer; the extension lead")], took)
    bought = bonds.debt_postings(T([row("a box of screws", "a", "b", "price"), row("the sanding pads", "a", "b", "price"), row("a roll of tape", "a", "b", "price")], dims={"care_relevant": .45}), "b", {"b": {"a": .06}}, present=["a", "b"])
    check("things bought while owing are a price, not a repayment", bought == [], bought)
    paid = bonds.debt_postings(T([row("the hire fee", "b", "a", "price")], dims={"care_relevant": .4}), "b", {"b": {"a": .12}}, present=["a", "b"])
    check("a price paid while owing is a price, not a repayment", paid == [], paid)
    check("a transfer to someone not present posts nothing", bonds.debt_postings(T([row("x", "a", "z", "none")]), "a", {}, present=["a", "b"]) == [])
    check("no transfers, no posting", bonds.debt_postings(_tags({"affinity": "kind"}), "a", {}, present=["a", "b"]) == [])
    check("a watched gift creates no debt for the watcher", all(p[0] != "c" for p in bonds.debt_postings(T([row("the spare hinges", "a", "b", "none")]), "a", {}, present=["a", "b", "c"])))
    check("observe posts no debt at all", "debt" not in bonds.observe({}, bonds.act_from_tags(_tags({"affinity": "generous"}), "a", "b"), _LOYAL))


# --- [9] the rest row's round trip -------------------------------------------------------------

def test_the_rest_row():
    print("\n[9] THE REST ROW — validates, seeds once, rides the turn, resolves latest-per-axis")
    from src.engine.ledger import Ledger
    from src.engine.records import Event, TurnCommit
    for kw, code in (({"rest": 1.5}, "RECORD_REST_RANGE"), ({"source": "guess"}, "RECORD_REST_SOURCE_UNKNOWN"),
                     ({"axis": "loyalty"}, "RECORD_AXIS_UNKNOWN"), ({"perceiver": ""}, "RECORD_PERCEIVER_EMPTY")):
        row = dict(perceiver="a", target="b", axis="trust", rest=.5, source="authored"); row.update(kw)
        try:
            RestDeclared(**row).validate(); check("refuses %s" % code, False, "accepted")
        except RecordError as ex:
            check("refuses %s" % code, ex.code == code, ex.code)
    led = Ledger(":memory:")
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    led.register_character("r", "a", {"id": "a", "name": "A"}, {"relationship_priors": {"default_trust": .4}})
    rels = {"b": {"trust": .9, "affinity": .8, "respect": .7, "debt": .0}, "c": {"trust": .6}, "x": "not an edge"}
    n1 = bond_rest.seed(led.con, "r", 0, "a", rels)
    n2 = bond_rest.seed(led.con, "r", 3, "a", rels)
    check("seed writes one row per authored axis", n1 == 5, n1)
    check("and is idempotent", n2 == 0, n2)
    led.append_turn(TurnCommit(run_id="r", turn=1, actor="a", thought="-", action="-", tags={}, validation={"ok": True},
                               affect={p: .2 for p in PATHS}, condition={"energy": .7},
                               events=[Event(type="betray", payload={"text": "x"}, actor="a")],
                               rest_rows=[RestDeclared(perceiver="a", target="b", axis="trust", rest=.15, source="cliff")]))
    rows = bond_rest.rows_for(led.con, "r", "a")
    check("rows_for returns them in log order", [r[:3] for r in rows] == [(0, "b", "trust"), (0, "b", "affinity"), (0, "b", "respect"), (0, "b", "debt"), (0, "c", "trust"), (1, "b", "trust")], rows)
    check("the cliff row rode append_turn", rows[-1][3:] == (.15, "cliff"), rows[-1])
    res = bond_rest.resolve(rows, {"default_trust": .4}, "b")
    check("resolve takes the latest row per axis", res == {"trust": .15, "affinity": .8, "respect": .7, "debt": .0}, res)
    check("...and the stranger's value where none", bond_rest.resolve(rows, {"default_trust": .4}, "c") == {"trust": .6, "affinity": .5, "respect": .5, "debt": .0})
    check("...on every axis for a stranger", bond_rest.resolve(rows, {"default_trust": .4}, "z") == {"trust": .4, "affinity": .5, "respect": .5, "debt": .0})
    tl = led.timeline_for("r", "a")
    check("timeline_for yields rest items first within a turn", tl[0][0] == "rest" and [t for t in tl if t[0] == "rest"][-1] == ("rest", "b", "trust", .15), tl)
    check("cliff_rows writes only where the edge fell below the rest",
          [r.axis for r in bond_rest.cliff_rows("a", "b", {"trust": .15, "affinity": .8}, ("trust", "affinity"), {"trust": .9, "affinity": .8})] == ["trust"])
    check("...and never up", bond_rest.cliff_rows("a", "b", {"trust": .5}, ("trust",), {"trust": .15}) == [])


# --- [10] the fold -----------------------------------------------------------------------------

def test_the_fold():
    print("\n[10] THE FOLD — rests, time and movements in the order they happened")
    tl = [("rest", "b", "trust", .90), ("rest", "b", "affinity", .90), ("time", 5.0),
          ("edge", "b", "trust", -.75, "first"), ("rest", "b", "trust", .15), ("time", 5.0)]
    got = bond_rest.rehydrate({"b": {"trust": .9, "affinity": .9}}, {"default_trust": .3}, tl)["b"]
    check("[rest, rest, time, edge, rest, time] walks to trust .15 held, affinity .90", abs(got["trust"] - .15) < 1e-9 and abs(got["affinity"] - .9) < 1e-9, got)
    old = bond_rest.rehydrate({"b": {"trust": .9, "affinity": .9}}, {"default_trust": .3}, [t for t in tl if t[0] != "rest"])["b"]
    # the pre-v28 numbers exactly: .9 -> .8152 (5 days toward .3) -> .0652 (the edge) -> .0984 (5 more); affinity .7362 -> .6395
    check("the same log without rest items replays to the pre-v28 numbers (toward the stranger's rest)",
          abs(old["trust"] - .0984) < 1e-3 and abs(old["affinity"] - .6395) < 1e-3, {k: round(v, 4) for k, v in old.items()})
    try:
        bond_rest.rehydrate({}, {}, [("weather", 1)]); check("an unknown item kind refuses", False, "accepted")
    except RecordError as ex:
        check("an unknown item kind refuses", ex.code == "BONDS_TIMELINE_KIND_UNKNOWN", ex.code)


# --- [11] drift ---------------------------------------------------------------------------------

def test_drift():
    print("\n[11] DRIFT — toward the seeded rest holds; toward the stranger's relaxes")
    e = {"trust": .9, "affinity": .9, "respect": .9, "debt": .5}
    check("toward its own rest, thirty days move nothing", bond_rest.drift(e, dict(e), 30.0) == e)
    s = bond_rest.drift(e, bond_rest.stranger_rest({"default_trust": .3}), 30.0)
    check("toward the stranger's rest -> .541/.517/.586/.370", all(abs(s[k] - v) < 1e-3 for k, v in
          (("trust", .541), ("affinity", .517), ("respect", .586), ("debt", .370))), {k: round(v, 3) for k, v in s.items()})
    for bad, code in ((lambda: bond_rest.drift({"trust": .5}, {}, 1), "BONDS_REST_AXIS_MISSING"),
                      (lambda: bond_rest.drift({}, "rest", 1), "BONDS_REST_NOT_A_DICT"),
                      (lambda: bond_rest.drift({}, {}, "soon"), "BONDS_DRIFT_ELAPSED_NOT_NUMERIC")):
        try:
            bad(); check("refuses %s" % code, False, "accepted")
        except RecordError as ex:
            check("refuses %s" % code, ex.code == code, ex.code)


# --- [12] the replay path — bond_replay.replay over invented beats, no book needed ------------------

def test_the_replay_path():
    print("\n[12] THE REPLAY PATH — tests/bond_replay.py's replay, the same law floor.bond_moves runs, on invented beats")
    # A darts match, invented for this test (hard rule 1): Tavi, new to the team, lends Pia his spare
    # flights before her throw; Pia, who has captained him all season, thanks him warmly; Dagny, chalking
    # the scores, has no eye for a quiet act. The re-answered tags are written here, in the shape `shape("act")` reads.
    sys.path.insert(0, os.path.join(REPO, "tests"))
    import bond_replay as R
    cast = ["dagny", "pia", "tavi"]
    sheet = lambda perception: {"fixed": {}, "baseline": {"skills": {"perception": perception, "insight": .9}, "model": _UNIT,
                                                          "relationship_priors": {"default_trust": .5}}}
    sheets = {"dagny": sheet(.1), "pia": sheet(.5), "tavi": sheet(.5)}
    plain = {"trust": .5, "affinity": .5, "respect": .5, "debt": .0}
    start = {"pia": {"tavi": {"trust": .85, "affinity": .80, "respect": .60, "debt": .0}},
             "tavi": {"pia": {"trust": .33, "affinity": .38, "respect": .52, "debt": .0}},
             "dagny": {"pia": dict(plain), "tavi": dict(plain)}}
    beats = [{"turn": 1, "actor": "tavi", "tags": {"type": "aid"}, "subject": "pia", "action": "-"},
             {"turn": 2, "actor": "pia", "tags": {"type": "aid"}, "subject": "tavi", "action": "-"}]
    answers = {"1": {"type": "aid", "dimensions": {"care_relevant": "mild"}, "durability": "transient",
                     "object": "pia", "showed": {"trust": .56},
                     "transfers": [{"what": "his spare flights", "from": "self", "to": "pia", "terms": "loan"}]},
               "2": {"type": "aid", "dimensions": {"care_relevant": "mild"}, "durability": "transient",
                     "object": "tavi", "showed": {"trust": .56, "affinity": .66}}}
    rows, final, counts = R.replay(beats, sheets, start, "act", cast, answers=answers)
    print("       counts %s" % counts)
    check("a bystander with no eye for a quiet act misses both beats", counts["unwitnessed"] == 2, counts)
    seen = {(t, w) for t, _s, _e, line in rows for w, what in line.items() if isinstance(what, dict)}
    check("...while the one each act was done to registers it (received is overt)", seen == {(1, "pia"), (2, "tavi")}, rows)
    check("an edge below the words it saw rises on trust", final["tavi"]["pia"]["trust"] > start["tavi"]["pia"]["trust"], final["tavi"]["pia"])
    check("...and on affinity", final["tavi"]["pia"]["affinity"] > start["tavi"]["pia"]["affinity"], final["tavi"]["pia"])
    check("an edge already above the word holds at its anchor", abs(final["pia"]["tavi"]["trust"] - start["pia"]["tavi"]["trust"]) < 1e-9, final["pia"]["tavi"])
    check("the loan posts once, on the receiver's account", counts["postings"] == 1 and abs(final["pia"]["tavi"]["debt"] - bonds._DEBT_RATE * .30) < 1e-9, (counts, final["pia"]["tavi"]))
    check("the bystander's edges never moved", final["dagny"] == start["dagny"], final["dagny"])


# --- [13] birth — an undeclared edge is born whole at the stranger's rest ------------------------

def _witness(cid, insight, default_trust, relationships=None):
    """A sheet the floor can read: skills (perception high so a subtle act is noticed — the check
    under test is RECOGNITION), the worth menu, the priors, and whatever edges it holds."""
    return {"id": cid,
            "char": {"fixed": {"id": cid, "name": cid.upper()},
                     "baseline": {"skills": {"perception": .9, "insight": insight}, "model": _UNIT,
                                  "relationship_priors": {"default_trust": default_trust},
                                  "traits": {"extraversion": {"mean": .5, "variability": .1}}},
                     "current": {"relationships": dict(relationships or {})}}}


def test_birth():
    print("\n[13] BIRTH — an undeclared edge is born whole where a stranger rests (2026-09-19, the first live stranger case's finding)")
    from src.engine import floor
    priors = {"default_trust": .3}                                          # a wary sheet's assumption about a stranger
    born = bond_rest.whole(None, priors)
    check("whole(None) is the stranger's rest on every axis", born == {"trust": .3, "affinity": .5, "respect": .5, "debt": .0}, born)
    check("whole({}) the same", bond_rest.whole({}, priors) == born)
    check("...and without priors, _NEUTRAL", bond_rest.whole(None, {}) == dict(bonds._NEUTRAL))
    kept = bond_rest.whole({"affinity": .42, "their_view": {"affinity": .46}, "note": "x"}, priors)
    check("a partial edge keeps what it carries and fills the rest", kept == {"trust": .3, "affinity": .42, "respect": .5, "debt": .0,
                                                                           "their_view": {"affinity": .46}, "note": "x"}, kept)
    src = {"affinity": .42}
    bond_rest.whole(src, priors)
    check("whole never mutates its input", src == {"affinity": .42}, src)
    # THE FOLD births at the first movement — the value the law priced the delta from
    z = bond_rest.rehydrate({}, priors, [("edge", "z", "affinity", -.07, "first")])["z"]
    check("rehydrate: a first-order delta on an unknown target lands on a whole edge",
          abs(z["trust"] - .3) < 1e-9 and abs(z["affinity"] - .43) < 1e-9 and z["respect"] == .5 and z["debt"] == .0, z)
    z2 = bond_rest.rehydrate({}, priors, [("edge", "z", "affinity", -.07, "first"), ("time", 30.0)])["z"]
    check("...and thirty days move it toward its OWN rest only (trust stays where it was born)",
          abs(z2["trust"] - .3) < 1e-9 and z2["affinity"] > .43, z2)
    v = bond_rest.rehydrate({}, priors, [("edge", "z", "affinity", .05, "second")])["z"]
    check("a second-order delta births the edge whole and lands the view on neutral",
          abs(v["trust"] - .3) < 1e-9 and v["affinity"] == .5 and abs(v["their_view"]["affinity"] - .55) < 1e-9, v)
    # THE LAW prices a stranger's first trust read from the sheet's default_trust, not .50
    tags = _tags({"trust": "dependable"}, obj="w")                          # done TO the witness: received, overt
    seer = {"a": _witness("a", .9, .3), "w": _witness("w", .9, .3)}
    moves = {wid: d for wid, d, _v, _c in floor.bond_moves(seer, ["a", "w"], "a", tags)}
    act = bonds.act_from_tags(tags, "a", "w", held={})
    rates = bonds.rates_of(priors)
    from_rest = bonds.observe(bond_rest.whole({}, priors), act, _UNIT, stake=1.0, rates=rates)
    from_neutral = bonds.observe({}, act, _UNIT, stake=1.0, rates=rates)
    check("bond_moves prices the stranger's trust from the whole edge", "w" in moves and moves["w"] == from_rest, (moves.get("w"), from_rest))
    check("...which is NOT the neutral price", from_rest["trust"] != from_neutral["trust"], (from_rest, from_neutral))
    # and SMALLER, by the law's own shape: from .30 a `dependable` (.56) is a CROSSING, weighed by what the
    # word says (α·2|d|·(o−e) = .12·.12·.26 = .003744); from .50 it is the same wing, one rung further out
    # (α·(t−x) = .12·.18 = .0216). A wary sheet is moved less by a near-neutral warm word — the
    # wariness working, not a defect; the first draft of this check guessed "larger" and the law said no.
    check("...and smaller — the crossing branch weighs the word: .003744 from .30 vs .0216 from .50",
          abs(from_rest["trust"] - .003744) < 1e-6 and abs(from_neutral["trust"] - .0216) < 1e-6, (from_rest, from_neutral))
    # BIRTH IS NOT ACQUAINTANCE: a witness without insight still cannot pin an act on a stranger
    blind = {"a": _witness("a", .9, .3), "w": _witness("w", .1, .3)}
    check("a witness without insight and no edge makes no move (recognition reads the stored edge)",
          floor.bond_moves(blind, ["a", "w"], "a", _tags({"trust": "dependable"}, obj="a", dimensions={"care_relevant": .3})) == [])
    known = {"a": _witness("a", .9, .3), "w": _witness("w", .1, .3, {"a": {"affinity": .6}})}
    got = {wid: d for wid, d, _v, _c in floor.bond_moves(known, ["a", "w"], "a", tags)}
    check("...while a stored edge, even partial, IS acquaintance and the missing trust is filled at .30",
          "w" in got and got["w"] == bonds.observe(bond_rest.whole({"affinity": .6}, priors), act, _UNIT, stake=1.0, rates=rates), got)


# --- [14] BOND wording -- the empty-showed line reads live, names the stub only under --stub --

def test_bond_wording_names_no_act_generically():
    """gate actor-contract-cleanup (2026-09-19): scripts/scene.py's BOND line printed "the
    stub double names no act" on ANY empty `showed`, not only a stubbed one — wrong on a
    live seat's beat (seen in a live scene's own log). This suite carries
    no fixture run to print a live BOND line from, so the guard is at the source, the same way
    this file already pins bond-arithmetic's numbers against drift: read scene.py's own text
    and check which literal is in it."""
    scene_py = os.path.join(REPO, "scripts", "scene.py")
    with open(scene_py, encoding="utf-8") as f:
        src = f.read()
    check("the new wording is in scripts/scene.py", "the seat named no showed" in src)
    check("the old stub-only wording is gone", "the stub double names no act" not in src)


def main():
    print("test_bond_law.py - the s6 table, pinned\n")
    for fn in sorted((v for k, v in globals().items() if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print("\n%s" % ("test_bond_law: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
