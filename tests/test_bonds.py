"""test_bonds.py — the relationship tier (src/engine/bonds.py).

THE DEFECT THIS TIER EXISTS TO FIX, measured before it was written: `arc.assess` ran on the SPEAKER
and wrote `diff["relationships"][subject]` into the speaker's own dict, so when A betrayed B it was
**A's** trust in B that fell — 0.80 -> 0.7828 — and B's edge never moved at all. `docs/relationships.md:5`
defines an edge as the PERCEIVER's belief. Edges were a passenger on an actor-scoped engine.

And the numbers were pointed the wrong way too. `arc.py:73-74` buffers damage by resilience, so at
resilience 0.90 a kindness moved trust 6.0x further than an equal-impact betrayal — the exact
inverse of `relationships.md:27`. Resilience belongs on temperament scars; it does not appear in
bonds.py at all.

So this suite asks whether the four ingredients the doc prescribes are actually present and pointed
the right way, plus the two axes that had no writer anywhere in the repo before now.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bonds                                   # noqa: E402
from src.engine.records import PATHS, RELATIONSHIP_AXES     # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


# A worth menu that CARES about loyalty/fairness, and one that does not. relationships.md:28 —
# "a loyalty-valuer is destroyed by betrayal" — so the same act must not land the same way.
_LOYAL = {"moral_foundations": {"fairness": 0.95, "loyalty": 0.95, "care_harm": 0.8},
          "schwartz": {"benevolence": 0.8, "security": 0.6}, "needs": {"relatedness": 0.8}}
_INDIFFERENT = {"moral_foundations": {"fairness": 0.05, "loyalty": 0.05, "care_harm": 0.2},
                "schwartz": {"benevolence": 0.2, "security": 0.3}, "needs": {"relatedness": 0.2}}

# THE FIXTURES ARE SEAT-SHAPED (bond gate 4, 2026-09-17): an act is a WORD on an act ladder with an
# OBJECT (bond-arithmetic.md s2/s5). The old `target: "b"` stays as the fallback the stub uses.
# `_KINDNESS` carries the `gave` entry inside `showed`, where parse_event_reply folds it.
_BETRAYAL = {"dimensions": {"social_violation": 0.9}, "durability": "durable", "target": "b",
             "object": "b", "showed": {"trust": "treacherous"}}
_KINDNESS = {"dimensions": {"care_relevant": 0.9}, "durability": "durable", "target": "b",
             "object": "b", "showed": {"affinity": "generous"},
             "transfers": [{"what": "a jar of honey", "from": "a", "to": "b", "terms": "none"}]}
_DISHONEST = dict(_BETRAYAL, showed={"trust": "dishonest"})          # one rung above the floor
_KIND = dict(_KINDNESS, showed={"affinity": "kind"})                   # no entry: a kindness, not a gift
# every value at 1.0: relevance 1 on every dimension — how the tests reach the g = 1 law through observe
_UNIT = {"moral_foundations": {k: 1.0 for k in ("fairness", "loyalty", "care_harm", "authority", "sanctity", "liberty")},
         "schwartz": {k: 1.0 for k in ("benevolence", "security", "achievement", "power", "self_direction",
                                       "universalism", "conformity", "tradition", "hedonism", "stimulation")},
         "needs": {k: 1.0 for k in ("relatedness", "competence", "autonomy")}}


def _act(tags, actor="a", witness="b"):
    return bonds.act_from_tags(tags, actor, witness)


def _after(edge, tags, model, **kw):
    """edge -> the edge once one act is observed and applied (a stranger's stake where the act is
    not received and no stake is given — the bystander shape the tests reach for)."""
    act = _act(tags, "a", kw.pop("witness", "b"))
    if not act["received"] and "stake" not in kw:
        kw["stake"] = 0.0
    return bonds.apply_deltas(edge, bonds.observe(edge, act, model, **kw))


def test_the_edge_belongs_to_the_perceiver():
    print("\n[1] THE INVERSION — the edge that moves is the WITNESS's")
    check("witness-gets-an-act", _act(_BETRAYAL, "a", "b") is not None)
    check("act-points-at-the-actor", _act(_BETRAYAL, "a", "b")["toward"] == "a")
    check("nobody-holds-an-edge-to-themselves", _act(_BETRAYAL, "a", "a") is None)
    check("no-actor-no-act", _act(_BETRAYAL, "", "b") is None)
    # the dimension route is RETIRED (s6 OMITTED: nothing) — strength alone is not an act
    check("no-showed-no-act", _act({"dimensions": {"social_violation": 0.9}, "durability": "durable", "target": "b"}, "a", "b") is None)
    check("the-act-carries-its-object", _act(_BETRAYAL)["object"] == "b")
    # the victim is the OBJECT; a third party in the room is a bystander, and both are witnesses
    check("subject-is-flagged-received", _act(_BETRAYAL, "a", "b")["received"] is True)
    check("bystander-is-not", _act(_BETRAYAL, "a", "c")["received"] is False)
    # and resilience — the thing that inverted the old numbers — is nowhere in this module
    src = open(os.path.join(REPO, "src", "engine", "bonds.py"), encoding="utf-8").read()
    check("resilience-does-not-scale-an-edge", "resilience" not in src.split('"""')[2],
          "resilience appears in bonds.py CODE, not just the docstring")


def test_prediction_error():
    print("\n[2] THE LAW — level-anchored on the same wing, prediction error where the act crosses (s6)")
    act = _act(_BETRAYAL)
    trusted = bonds.observe({"trust": 0.90}, act, _LOYAL, cliffs=False)
    schemer = bonds.observe({"trust": 0.20}, act, _LOYAL, cliffs=False)
    print("       treachery by a TRUSTED friend (cliff off): trust %+0.4f" % trusted["trust"])
    print("       the same from a KNOWN schemer            : trust %+0.4f" % schemer["trust"])
    check("the-trusted-fall-furthest", abs(trusted["trust"]) > abs(schemer["trust"]), "%s vs %s" % (trusted, schemer))
    ratio = abs(trusted["trust"]) / max(abs(schemer["trust"]), 1e-9)
    print("       ratio: %.2fx" % ratio)
    check("and-by-a-lot", ratio >= 3.0, "only %.2fx" % ratio)
    check("the-numbers-are-the-plan's", abs(trusted["trust"] + 0.1824) < 1e-4 and abs(schemer["trust"] + 0.04275) < 1e-4, "%s %s" % (trusted, schemer))
    # ...and then the cliff levels them: the floor word at full relevance is a stance, not a slope
    on = bonds.apply_deltas({"trust": 0.90}, bonds.observe({"trust": 0.90}, act, _LOYAL))["trust"]
    on2 = bonds.apply_deltas({"trust": 0.20}, bonds.observe({"trust": 0.20}, act, _LOYAL))["trust"]
    check("and-then-the-cliff-levels-them", abs(on - bonds._CLIFF_FLOOR) < 1e-6 and abs(on2 - bonds._CLIFF_FLOOR) < 1e-6, "%s %s" % (on, on2))
    # a kindness from an enemy moves; from a friend it confirms (same wing, past the reach)
    kind = _act(_KINDNESS)
    cold = bonds.observe({"trust": 0.20, "affinity": 0.20}, kind, _LOYAL)
    warm = bonds.observe({"trust": 0.90, "affinity": 0.90}, kind, _LOYAL)
    print("       `generous` from an enemy .20: %s   from a friend .90: %s" % (cold, warm))
    check("a-kindness-from-an-enemy-moves", abs(cold.get("affinity", 0) - 0.0312) < 1e-3, cold)
    check("from-a-friend-it-confirms", warm == {}, warm)
    # THE ANCHOR: an edge already holding what the act shows, one rung of grace included, does not move
    check("kind-at-the-reach-does-not-move", bonds.observe({"affinity": 0.78}, _act(_KIND), _LOYAL) == {})
    check("kind-past-the-reach-does-not-move", bonds.observe({"affinity": 0.90}, _act(_KIND), _LOYAL) == {})
    e = {"affinity": 0.75}
    for _ in range(12):
        e = bonds.apply_deltas(e, bonds.observe(e, _act(_KIND), _UNIT))
    twelve = e["affinity"]
    for _ in range(48):
        e = bonds.apply_deltas(e, bonds.observe(e, _act(_KIND), _UNIT))
    print("       twelve `kind` acts on .75 -> %.4f ; sixty -> %.4f (the anchor, not the count)" % (twelve, e["affinity"]))
    check("twelve-kind-acts-carry-.75-to-.7735", abs(twelve - 0.7735) < 1e-3, twelve)
    check("sixty-stop-at-.78", abs(e["affinity"] - 0.78) < 1e-3, e["affinity"])


def test_negativity_bias():
    print("\n[3] NEGATIVITY BIAS — per witness now (relationships.md:27; the s6 alpha table)")
    st = {"trust": 0.5}
    down = bonds.observe(st, _act(_DISHONEST), _UNIT)["trust"]
    up = bonds.observe(st, _act(dict(_BETRAYAL, showed={"trust": "loyal"})), _UNIT)["trust"]
    # `dishonest` (.22) crosses nothing from a stranger: reach .40 below; `loyal` (.78) reach .40 above
    rate_down, rate_up = abs(down) / 0.40, abs(up) / 0.40
    print("       dishonest: trust %+0.4f  (rate %.4f per unit reach)" % (down, rate_down))
    print("       loyal    : trust %+0.4f  (rate %.4f per unit reach)" % (up, rate_up))
    check("losses-outrun-gains", rate_down > rate_up, "%.4f vs %.4f" % (rate_down, rate_up))
    check("the-rates-are-alpha", abs(rate_down - bonds._ALPHA_NEG) < 1e-6 and abs(rate_up - bonds._ALPHA_POS) < 1e-6, "%s %s" % (rate_down, rate_up))
    check("and-the-old-inversion-is-gone", rate_down / rate_up > 1.5)
    # the bias is PER WITNESS: relationship_priors.update sets each person's pair
    slow = bonds.rates_of({"update": {"grant_threshold": "moderate", "withdraw_speed": "slow"}})
    fast = bonds.rates_of({"update": {"grant_threshold": "high", "withdraw_speed": "fast"}})
    print("       moderate/slow -> %s (%.2fx)   high/fast -> %s (%.2fx)" % (slow, slow[1] / slow[0], fast, fast[1] / fast[0]))
    check("a-slow-withdrawer-barely-leans", abs(slow[1] / slow[0] - 1.67) < 0.01, slow)
    check("a-fast-one-leans-hard", abs(fast[1] / fast[0] - 7.5) < 0.01, fast)
    d_slow = bonds.observe(st, _act(_DISHONEST), _UNIT, rates=slow)["trust"]
    d_fast = bonds.observe(st, _act(_DISHONEST), _UNIT, rates=fast)["trust"]
    check("the-same-act-costs-each-witness-their-own-rate", abs(d_slow + 0.08) < 1e-6 and abs(d_fast + 0.18) < 1e-6, "%s %s" % (d_slow, d_fast))


def test_scored_by_values():
    print("\n[4] SCORED BY THE PERCEIVER'S VALUES — including whether it is a CLIFF at all")
    edge = {"trust": 0.85}
    after_loyal = _after(edge, _BETRAYAL, _LOYAL)["trust"]
    after_indiff = _after(edge, _BETRAYAL, _INDIFFERENT)["trust"]
    print("       loyalty-valuer      : trust 0.85 -> %.4f" % after_loyal)
    print("       loyalty-indifferent : trust 0.85 -> %.4f" % after_indiff)
    check("the-loyalty-valuer-falls-to-the-cliff", abs(after_loyal - bonds._CLIFF_FLOOR) < 1e-6, after_loyal)
    check("the-indifferent-one-only-slopes", abs(after_indiff - 0.841) < 1e-3, after_indiff)
    check("same-act-different-people", abs(after_loyal - after_indiff) > 0.3)
    # a cliff is a DISCONTINUITY on the WORD, never on the strength: the rung above the floor slopes
    # at any strength, and the floor word cliffs at `slight`
    above = _after(edge, _DISHONEST, _LOYAL)["trust"]
    slight = _after(edge, dict(_BETRAYAL, dimensions={"social_violation": 0.15}), _LOYAL)["trust"]
    print("       `dishonest` at .9 -> %.4f (a slope)   `treacherous` at slight .15 -> %.4f (the cliff)" % (above, slight))
    check("the-rung-above-the-floor-is-a-slope", abs(above - 0.7495) < 1e-3, above)
    check("the-word-cliffs-strength-is-not-the-trigger", abs(slight - bonds._CLIFF_FLOOR) < 1e-6, slight)
    check("cliff_axes-names-it", bonds.cliff_axes(edge, _act(_BETRAYAL), _LOYAL) == ("trust",)
          and bonds.cliff_axes(edge, _act(_DISHONEST), _LOYAL) == () and bonds.cliff_axes(edge, _act(_BETRAYAL), _INDIFFERENT) == ())


def test_attribution():
    print("\n[5] ATTRIBUTION — why they think it happened (relationships.md:29)")
    edge = {"trust": 0.80}
    out = {}
    for att in ("malice", "negligence", "coerced", "accident"):
        out[att] = bonds.observe(edge, _act(dict(_DISHONEST, attribution=att)), _LOYAL).get("trust", 0.0)
        print("       %-11s trust %+0.4f" % (att, out[att]))
    check("malice-hurts-most", abs(out["malice"]) > abs(out["negligence"]) > abs(out["coerced"]) > abs(out["accident"]), out)
    # the charity formula's own number: attrib = 1 − (1 − stated)·(floor + (1 − floor)·trust)
    formula = 1.0 - (1.0 - bonds._ATTRIBUTION["accident"]) * (bonds._CHARITY_FLOOR + (1.0 - bonds._CHARITY_FLOOR) * 0.80)
    check("an-accident-barely-registers", abs(abs(out["accident"]) / abs(out["malice"]) - formula) < 1e-3, "%s vs formula %.4f" % (out, formula))
    untagged = bonds.observe(edge, _act(_DISHONEST), _LOYAL).get("trust", 0.0)
    check("untagged-reads-as-intent", abs(untagged - out["malice"]) < 1e-9,
          "an untagged act must behave exactly as a malicious one — no silent damping")
    # ...and whether the excuse is BELIEVED depends on the witness. relationships.md:29 requires
    # misattribution to be possible ("tragic misunderstandings are first-class") but gives no rule
    # for it; charity-scaled-by-trust is this engine's answer, and it is marked as an extension.
    acc = dict(_DISHONEST, attribution="accident")

    def _rate(trust, tags):
        """|delta| per unit of the crossing (.22 to the edge) — isolates CHARITY from the law's own
        weighting, which also varies with the edge."""
        d = bonds.observe({"trust": trust}, _act(tags), _LOYAL).get("trust", 0.0)
        return abs(d) / abs(0.22 - trust)

    believed, disbelieved = _rate(0.95, acc), _rate(0.35, acc)
    print("       the SAME accident, read by a TRUSTING witness  : rate %.4f" % believed)
    print("       ...and by one who trusts them much less        : rate %.4f" % disbelieved)
    check("the-excuse-needs-a-believer", disbelieved > believed * 1.5, "%.4f vs %.4f" % (disbelieved, believed))
    check("charity-never-reaches-zero", disbelieved < _rate(0.35, dict(_DISHONEST, attribution="malice")),
          "an accident must never cost as much as open malice")
    # on the FLOOR word the cliff's target follows attribution too: unforgivability is a judgement of intent
    cliff = {att: bonds.observe(edge, _act(dict(_BETRAYAL, attribution=att)), _LOYAL)["trust"] for att in out}
    print("       `treacherous`: %s" % {k: round(v, 4) for k, v in cliff.items()})
    check("the-cliff-target-follows-attribution", abs(cliff["malice"] + 0.65) < 1e-4 and abs(cliff["accident"] + 0.1914) < 1e-3
          and cliff["malice"] < cliff["negligence"] < cliff["coerced"] < cliff["accident"], cliff)
    check("cliff_axes-reports-the-word-not-the-drop", all(bonds.cliff_axes(edge, _act(dict(_BETRAYAL, attribution=att)), _LOYAL) == ("trust",) for att in out))


def test_the_seat_writes_attribution_and_observe_prices_it():
    print("\n[5b] THE SEAT WRITES IT — act_from_tags carries a seat-written attribution to observe's gain")
    # A seat-shaped reply (parse_event_reply's own out-shape): object + showed{trust: dependable}.
    # `_UNIT` gives relevance 1 on any dimension, so `mastery` here is an arbitrary nonzero severity —
    # only its PRESENCE (a dominant dimension) matters, not its value.
    dependable = {"dimensions": {"mastery": 0.30}, "durability": "transient", "object": "b",
                  "showed": {"trust": "dependable"}}
    edge = {"trust": 0.5}                        # a stranger: real room for a .56 word to move her
    act_intent = _act(dict(dependable, attribution="intent"))
    act_accident = _act(dict(dependable, attribution="accident"))
    check("act_from_tags-stamps-the-seats-own-word-onto-the-act",
          (act_intent["attribution"], act_accident["attribution"]) == ("intent", "accident"),
          (act_intent["attribution"], act_accident["attribution"]))
    gain_intent = bonds.observe(edge, act_intent, _UNIT).get("trust", 0.0)
    gain_accident = bonds.observe(edge, act_accident, _UNIT).get("trust", 0.0)
    check("the-act-has-room-to-move-so-the-comparison-is-not-vacuous", gain_intent != 0.0, gain_intent)
    # THE BARE TABLE RATIO ONLY HOLDS AT FULL TRUST. `_terms` damps `bonds._ATTRIBUTION`'s raw weight
    # by CHARITY (bond-arithmetic.md s6; relationships.md:29): attrib = 1 − (1 − stated)·charity, and
    # charity = floor + (1 − floor)·edge.trust reaches 1.0 only when trust does — where `dependable`
    # (height .56) has no room left to move an edge already at 1.0 (law_delta == 0 there: the ceiling
    # one rung past .56 sits BEHIND a fully-trusting edge). So — as the gate anticipated — this is
    # asserted against `_terms`'s own formula rather than the bare table weight; at edge trust .5 the
    # two disagree by .0078, not noise (printed below). `_terms`'s formula is the same one
    # `test_attribution` above independently checks against the doc for a cold act; this is its
    # warm-branch, seat-shaped twin.
    charity = bonds._CHARITY_FLOOR + (1.0 - bonds._CHARITY_FLOOR) * edge["trust"]
    formula_attrib = 1.0 - (1.0 - bonds._ATTRIBUTION["accident"]) * charity
    _, terms_attrib = bonds._terms(edge, act_accident, _UNIT, None)
    check("_terms-computes-the-documented-charity-formula", abs(terms_attrib - formula_attrib) < 1e-9,
          (terms_attrib, formula_attrib))
    predicted_accident = gain_intent * formula_attrib
    bare_ratio_off_by = abs(gain_accident - gain_intent * bonds._ATTRIBUTION["accident"])
    print("       gain(intent) %.6f   gain(accident) %.6f   predicted (via _terms) %.6f   bare-table-ratio would miss by %.4f"
          % (gain_intent, gain_accident, predicted_accident, bare_ratio_off_by))
    check("observes-trust-gain-on-a-dependable-act-scales-by-exactly-terms-attribution-weight",
          abs(gain_accident - predicted_accident) < 1e-6,
          "%.6f vs predicted %.6f" % (gain_accident, predicted_accident))


def test_respect_and_debt_have_a_writer():
    print("\n[6] RESPECT AND DEBT — competence is object-free; the account is the seat's entry")
    mastery = {"dimensions": {"mastery": 0.85}, "durability": "durable", "object": "b", "showed": {"respect": "masterly"}}
    d = bonds.observe({"respect": 0.4}, _act(mastery, "a", "c"), _LOYAL, stake=0.0)
    print("       watched mastery, by a bystander at stake 0 -> %s" % d)
    check("respect-moves-for-a-bystander-who-holds-nothing", abs(d.get("respect", 0) - 0.0128) < 1e-3, d)
    try:
        bonds.observe({"respect": 0.4}, _act(mastery, "a", "c"), _LOYAL)
        check("a-bystander-call-without-stake-is-refused", False, "accepted — stake silently 1")
    except bonds.RecordError as e:
        check("a-bystander-call-without-stake-is-refused", e.code == "BONDS_STAKE_MISSING", e.code)
    # DEBT MOVES ON A TRANSFER (2026-09-18) — a fact the seat reports, priced once per pair by
    # debt_postings from the words (`terms`) and the accounts; never on a witness's read of a word
    got = bonds.observe({}, _act(_KINDNESS, "a", "b"), _LOYAL)                                # b IS the object
    hold = bonds.observe({}, _act(_KINDNESS, "a", "c"), _LOYAL, stake=bonds.stake_of("c", "b", {"b": {"affinity": 0.8}}))
    cold = bonds.observe({}, _act(_KINDNESS, "a", "c"), _LOYAL, stake=bonds.stake_of("c", "b", {"b": {"affinity": 0.5}}))
    print("       `generous` RECEIVED -> %s" % got)
    print("       watched by c who holds b at .8 -> %s ; by c neutral to b -> %s" % (hold, cold))
    check("observe-never-moves-the-account", "debt" not in got and "debt" not in hold and "debt" not in cold, "%s %s %s" % (got, hold, cold))
    posts = bonds.debt_postings(_KINDNESS, "a", {"b": {"a": 0.0}}, present=["a", "b", "c"])
    print("       the transfer posts -> %s" % posts)
    check("receiving-a-thing-creates-debt", posts == [("b", "a", "gave", 0.045, "a jar of honey")], posts)
    check("a-bystander-never-owes", all(p[0] != "c" for p in posts), posts)
    # THE OWNER'S RULE AS A NUMBER: values in the abstract move nothing; what is hers moves her
    check("what-is-hers-moves-her", abs(hold.get("affinity", 0) - 0.0230) < 1e-3, hold)
    check("values-in-the-abstract-move-nothing", cold == {}, cold)
    both = dict(_KINDNESS, showed={"trust": "dependable", "affinity": "generous"})
    rec = bonds.observe({}, _act(both, "a", "b"), _LOYAL)["trust"]
    byst = bonds.observe({}, _act(both, "a", "c"), _LOYAL, stake=0.0)["trust"]
    check("trust-keeps-its-floor-for-a-bystander", abs(byst / rec - bonds._TRUST_STAKE_FLOOR) < 1e-6, "%s %s" % (rec, byst))
    # debt ACCUMULATES — an account, not a belief: the same gift posts the same on 0.0 and on 0.9
    first = bonds.debt_postings(_KINDNESS, "a", {"b": {"a": 0.0}}, present=["a", "b"])[0][3]
    later = bonds.debt_postings(_KINDNESS, "a", {"b": {"a": 0.9}}, present=["a", "b"])[0][3]
    check("debt-does-not-converge", abs(first - later) < 1e-9, "%s vs %s" % (first, later))
    # the entry comes from the TERMS, never from the account: a price is square; a repayment posts on the
    # giver's own account and only when something is owed (the things: a climbing wall's hire desk, invented)
    bought = dict(_KINDNESS, transfers=[{"what": "a day pass", "from": "a", "to": "b", "terms": "price"}])
    back = dict(_KINDNESS, transfers=[{"what": "the belay device", "from": "b", "to": "a", "terms": "repayment"}])
    check("a-price-is-square-by-its-words", bonds.debt_postings(bought, "a", {"b": {"a": 0.9}}, present=["a", "b"]) == [])
    check("a-repayment-lowers-what-the-giver-owes", bonds.debt_postings(back, "b", {"b": {"a": 0.6}}, present=["a", "b"]) == [("b", "a", "repaid", -0.045, "the belay device")])
    check("...and-a-repayment-of-nothing-owed-posts-nothing", bonds.debt_postings(back, "b", {"b": {"a": 0.0}}, present=["a", "b"]) == [])
    check("the-direction-is-the-transfer's-not-the-speaker's",
          bonds.debt_postings(dict(_KINDNESS, transfers=[{"what": "the spare rope", "from": "a", "to": "self", "terms": "none"}]), "b", {}, present=["a", "b"]) == [("b", "a", "gave", 0.045, "the spare rope")])
    check("every-axis-now-has-a-writer", set(RELATIONSHIP_AXES) <= {"trust", "affinity", "respect", "debt"})


def test_drift():
    print("\n[7] DRIFT — unreinforced edges settle back toward their REST (relationships.md:30; s6)")
    from src.engine import bond_rest
    edge = {"trust": 0.90, "affinity": 0.90, "respect": 0.90, "debt": 0.50}
    out = bond_rest.drift(edge, bond_rest.stranger_rest({"default_trust": 0.30}), elapsed=5.0)
    print("       toward a stranger's rest, 5 days: %s" % {k: round(v, 4) for k, v in out.items()})
    check("everything-moves-toward-rest", all(out[a] < edge[a] for a in edge), out)
    moved = {a: edge[a] - out[a] for a in edge}
    check("affinity-fades-faster-than-trust", moved["affinity"] > moved["trust"], moved)
    check("debt-barely-fades", moved["debt"] < moved["affinity"], moved)
    check("a-stranger's-rest-reads-default_trust", bond_rest.stranger_rest({"default_trust": 0.30})["trust"] == 0.30
          and bond_rest.stranger_rest({})["trust"] == bonds._NEUTRAL["trust"])
    # THE POINT OF THE GATE: toward a declared rest equal to the edge, nothing moves
    held = bond_rest.drift(edge, dict(edge), elapsed=30.0)
    check("an-edge-at-its-own-rest-holds", held == edge, held)
    check("zero-elapsed-is-a-no-op", bond_rest.drift(edge, bond_rest.stranger_rest({}), 0.0) == edge)
    check("an-absent-axis-stays-absent", "respect" not in bond_rest.drift({"trust": 0.7}, {"trust": 0.5}, 3.0))


def test_purity():
    print("\n[8] PURE — engine rules 3, 4, 6")
    from src.engine import bond_rest
    edge = {"trust": 0.8, "affinity": 0.6}
    before = dict(edge)
    bonds.apply_deltas(edge, bonds.observe(edge, _act(_BETRAYAL), _LOYAL))
    check("apply_deltas-does-not-mutate", edge == before, edge)
    check("clamped-to-0-1", all(0.0 <= v <= 1.0 for v in
          bonds.apply_deltas({"trust": 0.02}, {"trust": -9.0}).values()))
    for bad, fn in ((("observe", lambda: bonds.observe({}, "nope", _LOYAL))),
                    (("observe", lambda: bonds.observe({}, _act(_BETRAYAL), "nope"))),
                    (("apply_deltas", lambda: bonds.apply_deltas({}, "nope"))),
                    (("drift", lambda: bond_rest.drift({}, {}, "soon")))):
        try:
            fn()
            check("%s-fails-loud" % bad, False, "accepted bad input silently")
        except ValueError:
            check("%s-fails-loud" % bad, True)
    try:
        bonds.apply_deltas({}, {"loyalty": 0.1})
        check("unknown-axis-rejected", False, "accepted an axis outside RELATIONSHIP_AXES")
    except ValueError:
        check("unknown-axis-rejected", True)
    for name in ("bonds.py", "bond_rest.py"):
        src = open(os.path.join(REPO, "src", "engine", name), encoding="utf-8").read()
        check("%s-no-randomness" % name, "import random" not in src)
        check("%s-no-llm" % name, "openai" not in src and "requests" not in src)
        check("%s-under-500-lines" % name, len(src.splitlines()) < 500, len(src.splitlines()))


_P = PATHS          # DERIVED, never re-listed — a hand-copy of this went stale
                        # in test_vault and broke a green suite the day DISGUST landed.


def _person(cid, name, rels):
    """An invented two-character fixture. CLAUDE.md hard rule 1 — engine fixtures, never a book."""
    return {"fixed": {"id": cid, "name": name, "genotype": {}},
            "baseline": {"temperament": {p: {"mean": 0.4, "variability": 0.1} for p in _P},
                         "traits": {"extraversion": {"mean": 0.5}},
                         "model": {"moral_foundations": {"fairness": 0.9, "loyalty": 0.9, "care_harm": 0.8},
                                   "schwartz": {"benevolence": 0.7, "security": 0.5},
                                   "needs": {"relatedness": 0.8}, "regard": {}},
                         "skills": {"perception": 0.5, "insight": 0.5},
                         "relationship_priors": {"default_trust": 0.5}},
            "current": {"affect": {p: 0.4 for p in _P},
                        "condition": {"energy": 0.7, "allostatic_load": 0.3},
                        "location": "yard", "vault": [], "relationships": rels}}


def test_arc_no_longer_writes_edges():
    print("\n[9] THE ARC LET GO OF THE EDGES — but still replays the ones it stored")
    from src.engine import arc
    ch = _person("a", "Ayla", {"b": {"trust": 0.80, "affinity": 0.7, "respect": 0.5, "debt": 0.0}})
    for name, dims in (("betrayal", {"social_violation": 0.9}), ("connection", {"care_relevant": 0.9}),
                       ("threat", {"threat": 0.9}), ("loss", {"loss": 0.9}), ("mastery", {"mastery": 0.9})):
        d = arc.assess({"dimensions": dims, "durability": "durable", "target": "b"}, 0.6,
                       ch, ch["current"]["condition"])
        check("no-relationships-key-on-%s" % name, not (d or {}).get("relationships"), d)
    # CLAUDE.md rule 2: a diff persisted BEFORE this change must still rehydrate its run's real state
    hist = {"temperament": {"WARINESS": 0.01}, "relationships": {"b": {"trust": -0.02}}, "regard": {}}
    check("apply-still-replays-a-stored-edge",
          abs(arc.apply(ch, hist)["current"]["relationships"]["b"]["trust"] - 0.78) < 1e-9,
          "an append-only log means old diffs replay to the state that run ACTUALLY had")


def test_the_scene_wires_it():
    print("\n[10] END TO END — the room re-reads the speaker (scripts/scene.py)")
    import importlib.util as _u
    from src.engine.ledger import Ledger
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    _sp = _u.spec_from_file_location("_sc_bonds", os.path.join(REPO, "scripts", "scene.py"))
    sc = _u.module_from_spec(_sp)
    _sp.loader.exec_module(sc)

    chars = {"a": _person("a", "Ayla", {"b": {"trust": 0.85, "affinity": 0.70, "respect": 0.5, "debt": 0.0}}),
             "b": _person("b", "Beatrix", {"a": {"trust": 0.85, "affinity": 0.70, "respect": 0.5, "debt": 0.0}})}
    world = {"world": "w", "switches": {"magic": False, "divine": False, "beings": False},
             "locations": [{"id": "yard", "what": "the yard"}],
             "people": [{"id": "a", "name": "Ayla"}, {"id": "b", "name": "Beatrix"}]}
    cfg = {"at": {"day": 1, "time": "09:00"}, "situation": "Two people stand in the yard.", "subject": ("b", None),
           "opening_tags": {"type": "mundane", "dimensions": {"social_violation": 0.5},
                            "durability": "transient"},
           "cast": [{"id": "a", "drive": "press the point"}, {"id": "b", "drive": "hold ground"}],
           "name": "bondprobe"}
    sc._NAMES = {"a": "Ayla", "b": "Beatrix"}
    # A betrays B. `type` must be a CATALOG key or validate_tags zeroes the dimensions and nothing
    # moves — the failure mode that made the first run of this probe read as "the loop never fired".
    sc.faithful_turn = lambda packet, event_text, temperament, model, stub, **kw: (
        {"action": "Ayla tells the others what Beatrix said in confidence.",
         "thought": "it had to come out", "exit": False, "addressee": "",
         "tags": {"type": "betray", "summary": "Ayla broke Beatrix's confidence in front of the others",
                  "subject": "b", "object": "b", "showed": {"trust": "treacherous"},
                  "dimensions": {"social_violation": 0.9},
                  "durability": "durable", "confidence": 0.9}}, [])

    from src.engine import bible
    led = Ledger(":memory:")
    led.create_run("r1", {"catalog_version": 1, "models": {"turn": "stub"},
                          "prompt_versions": {"turn": 1},
                          bible.CONFIG_KEY: bible.build(led.con, world, chars)})
    for cid in ("a", "b"):
        led.register_character("r1", cid, chars[cid]["fixed"], chars[cid]["baseline"])
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        sc.run_scene(world, chars, cfg, led, "r1", 0, "stub", True, 1, think=False, seed_base=0)

    speaker_edge = chars["a"]["current"]["relationships"]["b"]["trust"]
    victim_edge = chars["b"]["current"]["relationships"]["a"]["trust"]
    print("       A (speaker / betrayer) trust in B : 0.8500 -> %.4f" % speaker_edge)
    print("       B (witness / victim)   trust in A : 0.8500 -> %.4f" % victim_edge)
    print("       (before this tier: the BETRAYER fell 0.80 -> 0.7828 and the victim never moved)")
    check("the-victim-loses-trust", victim_edge < 0.85 - 0.2, victim_edge)
    check("the-betrayer-does-not", abs(speaker_edge - 0.85) < 1e-9, speaker_edge)
    check("and-it-is-the-cliff", abs(victim_edge - bonds._CLIFF_FLOOR) < 1e-6, victim_edge)
    check("the-run-narrates-it", "BOND" in buf.getvalue())

    # --- and the movement is now CITABLE. `RelationshipDelta` shipped with records.py and had no
    # producer outside tests, so read_api's edges query answered the social-throughline question
    # with an empty result for every run ever made.
    rows = led.con.execute(
        "SELECT perceiver, target, axis, delta FROM relationship_deltas WHERE run_id='r1'").fetchall()
    print("       relationship_deltas rows: %s" % [tuple(r) for r in rows])
    check("the-ledger-has-rows", bool(rows), "RelationshipDelta still has no producer")
    trust = [r for r in rows if r[2] == "trust"]
    check("perceiver-is-the-victim", trust and trust[0][0] == "b", trust)
    check("target-is-the-speaker", trust and trust[0][1] == "a", trust)
    check("delta-is-negative", trust and float(trust[0][3]) < 0, trust)
    from src.engine import read_api
    res = read_api.edges(led.con, "r1", "b", "a", as_of=99)
    check("read_api-edges-returns-them", bool(res.rows), res.trace)
    # atomicity: the deltas rode the turn's own commit, so a turn and its edges cannot disagree
    turns = led.con.execute("SELECT COUNT(*) FROM turns WHERE run_id='r1'").fetchone()[0]
    check("no-orphan-edge-rows", turns >= 1 and bool(rows),
          "deltas must ride the TurnCommit, not a separate write")
    # A CLIFF MOVES THE REST (gate 4): one `cliff` row rides the causing turn, and the fold reads it
    from src.engine import bond_rest
    rest = led.con.execute("SELECT turn, perceiver, target, axis, rest, source FROM rest_declared WHERE run_id='r1' AND source='cliff'").fetchall()
    print("       rest_declared cliff rows: %s" % [tuple(r) for r in rest])
    check("the-cliff-writes-one-rest-row-on-the-causing-turn",
          len(rest) == 1 and tuple(rest[0])[:4] == (0, "b", "a", "trust") and abs(rest[0][4] - bonds._CLIFF_FLOOR) < 1e-6, [tuple(r) for r in rest])
    resolved = bond_rest.resolve(bond_rest.rows_for(led.con, "r1", "b"), chars["b"]["baseline"].get("relationship_priors", {}), "a")
    check("and-resolve-reads-it-back", abs(resolved["trust"] - bonds._CLIFF_FLOOR) < 1e-6, resolved)
    check("the-run-names-the-cliff", "CLIFF" in buf.getvalue())


def test_trust_gates_transmission():
    print("\n[11] TRUST IS THE GAIN ON INFORMATION FLOW (relationships.md, 'Trust is load-bearing')")
    from src.engine import acquisition
    from src.engine.direction import sureness
    tags = {"type": "betray", "durability": "durable",
            "summary": "I took the ledger from the strongbox and burned the top three pages"}
    believed = acquisition.witness_belief("Ayla", tags, "a", trust=0.95)
    doubted = acquisition.witness_belief("Ayla", tags, "a", trust=0.10)
    base = acquisition.witness_belief("Ayla", tags, "a")
    for label, b in (("trusts her", believed), ("does not", doubted), ("no edge", base)):
        print("       %-11s conf %.3f  prov %-10s | %s" % (label, b["confidence"], b["provenance"],
                                                           b["claim"][:58]))
    check("trust-raises-confidence", believed["confidence"] > doubted["confidence"],
          "%s vs %s" % (believed["confidence"], doubted["confidence"]))
    check("distrust-reframes-it-as-a-claim", doubted["provenance"] == "reported"
          and "claims" in doubted["claim"], doubted)
    check("trust-keeps-it-as-witnessed", believed["provenance"] == "witnessed", believed)
    check("no-edge-reproduces-the-old-numbers",
          base["confidence"] == acquisition._WITNESS_BASE and base["provenance"] == "witnessed", base)
    # the difference has to SURVIVE to the actor — a number that changes and a rendering that does
    # not is the failure this project keeps finding.
    print("       rendered: trusting -> %r   doubting -> %r"
          % (sureness(believed["confidence"]), sureness(doubted["confidence"])))
    check("and-the-actor-can-tell", sureness(believed["confidence"]) != sureness(doubted["confidence"]),
          "both render to the same sureness word — the change stayed inside a band")
    check("bad-trust-fails-loud", _raises(lambda: acquisition.witness_belief("A", tags, "a", trust="high")))
    check("still-none-for-a-transient-turn",
          acquisition.witness_belief("A", dict(tags, durability="transient"), "a", trust=0.9) is None)


def test_the_scene_wires_drift():
    print("\n[12] DRIFT IS WIRED — and only where the director says time passed")
    import importlib.util as _u
    from src.engine.ledger import Ledger
    from src.engine import bible
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    _sp = _u.spec_from_file_location("_sc_drift", os.path.join(REPO, "scripts", "scene.py"))
    sc = _u.module_from_spec(_sp)
    _sp.loader.exec_module(sc)
    sc._NAMES = {"a": "Ayla", "b": "Beatrix"}
    sc.faithful_turn = lambda *a, **k: ({"action": "Ayla says nothing much.", "thought": "-",
                                         "exit": False, "addressee": "",
                                         "tags": {"type": "mundane", "summary": "", "subject": "",
                                                  "dimensions": {}, "durability": "transient",
                                                  "confidence": 0.5}}, [])

    def _run(elapsed, trust_prior=0.30, seed=False):
        """One scene, zero meaningful beats — so any edge movement is drift and nothing else.
        `seed` writes the authored rest rows first, as the drivers' create path does (gate 4)."""
        start = {"trust": 0.90, "affinity": 0.90, "respect": 0.90, "debt": 0.50}
        chars = {"a": _person("a", "Ayla", {"b": dict(start)}),
                 "b": _person("b", "Beatrix", {"a": dict(start)})}
        for c in chars.values():
            c["baseline"]["relationship_priors"] = {"default_trust": trust_prior}
        world = {"world": "w", "switches": {"magic": False, "divine": False, "beings": False},
                 "locations": [{"id": "yard", "what": "the yard"}],
                 "people": [{"id": "a", "name": "Ayla"}, {"id": "b", "name": "Beatrix"}]}
        cfg = {"at": {"day": 1, "time": "09:00"}, "situation": "Two people stand in the yard.", "subject": (None, None),
               "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
               "cast": [{"id": "a", "drive": "wait"}, {"id": "b", "drive": "wait"}], "name": "drift"}
        if elapsed:
            # 2026-09-10: elapsed is DERIVED from `at` (clock.py), in MINUTES. A first scene is
            # put on the ledger at 09:00 (below); this one opens `elapsed` minutes after it ended.
            _m = 9 * 60 + int(elapsed)
            cfg["at"] = {"day": 1 + _m // (24 * 60), "time": "%02d:%02d" % (_m % (24 * 60) // 60, _m % 60)}
        led = Ledger(":memory:")
        led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"},
                             "prompt_versions": {"turn": 1},
                             bible.CONFIG_KEY: bible.build(led.con, world, chars)})
        for cid in ("a", "b"):
            led.register_character("r", cid, chars[cid]["fixed"], chars[cid]["baseline"])
            if seed:
                from src.engine import bond_rest
                bond_rest.seed(led.con, "r", 0, cid, chars[cid]["current"]["relationships"])
        import io
        from contextlib import redirect_stdout
        start_turn = 0
        if elapsed:
            from src.engine import clock as _ck
            from src.engine.records import PATHS, TurnCommit
            led.record_scene_clock("r", 0, _ck.parse_at({"day": 1, "time": "09:00"}), None, 0.0)
            # ...with both of them in its room: since gate own-timelines a character ages by their OWN time since they
            # were last in a room, and with no beat before this one both would first appear here, as their sheets say
            led.append_turn(TurnCommit(run_id="r", turn=0, actor="a", thought="-", action="-", tags={},
                                       validation={"ok": True}, affect={p: 0.2 for p in PATHS},
                                       manifest={"decay": {"minutes": 0.0, "here": ["a", "b"], "bystanders": []}}))
            start_turn = 1                     # the drifting scene follows a prior reading
        with redirect_stdout(io.StringIO()):
            sc.run_scene(world, chars, cfg, led, "r", start_turn, "stub", True, 1, think=False, seed_base=0)
        return start, chars["a"]["current"]["relationships"]["b"]

    start, none = _run(None)
    check("no-elapsed-no-drift", none == start, none)
    _, after = _run(5.0 * 24 * 60)              # five DAYS, in minutes — the unit is the clock's now
    print("       before        %s" % {k: round(v, 3) for k, v in start.items()})
    print("       after 5 days  %s" % {k: round(v, 3) for k, v in after.items()})
    check("edges-relaxed", all(after[k] < start[k] for k in start), after)
    check("affinity-outpaces-trust", (start["affinity"] - after["affinity"])
          > (start["trust"] - after["trust"]), after)
    # the resting point is the CHARACTER's, not a constant — relationship_priors finally reads
    _, low = _run(30.0 * 24 * 60, trust_prior=0.20)
    _, high = _run(30.0 * 24 * 60, trust_prior=0.80)
    print("       default_trust 0.20 -> trust %.3f   default_trust 0.80 -> trust %.3f"
          % (low["trust"], high["trust"]))
    check("different-priors-different-resting-points", low["trust"] < high["trust"] - 0.2,
          "relationship_priors had no runtime reader before this")
    # ARM 2 (gate 4): an AUTHORED edge rests where it was authored — thirty days move nothing
    _, seeded = _run(30.0 * 24 * 60, seed=True)
    print("       seeded rest, 30 days: %s" % {k: round(v, 3) for k, v in seeded.items()})
    check("an-authored-edge-rests-where-it-was-authored", all(abs(seeded[k] - start[k]) < 1e-9 for k in start), seeded)
    # ARM 3 (gate 4): a cliff in a first scene, then thirty days — trust stays on the floor
    from src.engine import bond_rest
    chars = {"a": _person("a", "Ayla", {"b": {"trust": 0.90, "affinity": 0.90, "respect": 0.90, "debt": 0.50}}),
             "b": _person("b", "Beatrix", {"a": {"trust": 0.90, "affinity": 0.90, "respect": 0.90, "debt": 0.50}})}
    world = {"world": "w", "switches": {"magic": False, "divine": False, "beings": False},
             "locations": [{"id": "yard", "what": "the yard"}],
             "people": [{"id": "a", "name": "Ayla"}, {"id": "b", "name": "Beatrix"}]}
    led = Ledger(":memory:")
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1},
                         bible.CONFIG_KEY: bible.build(led.con, world, chars)})
    for cid in ("a", "b"):
        led.register_character("r", cid, chars[cid]["fixed"], chars[cid]["baseline"])
        bond_rest.seed(led.con, "r", 0, cid, chars[cid]["current"]["relationships"])
    _mundane = sc.faithful_turn
    sc.faithful_turn = lambda *a, **k: ({"action": "Ayla tells the others what Beatrix said in confidence.", "thought": "-",
                                         "exit": False, "addressee": "",
                                         "tags": {"type": "betray", "summary": "", "subject": "b", "object": "b",
                                                  "showed": {"trust": "treacherous"}, "dimensions": {"social_violation": 0.9},
                                                  "durability": "durable", "confidence": 0.9}}, [])
    _cfg = lambda day, name: {"at": {"day": day, "time": "09:00"}, "situation": "Two people stand in the yard.", "subject": ("b", None),
                              "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
                              "cast": [{"id": "a", "drive": "wait"}, {"id": "b", "drive": "wait"}], "name": name}
    import io
    from contextlib import redirect_stdout
    with redirect_stdout(io.StringIO()):
        nxt = sc.run_scene(world, chars, _cfg(1, "cliff"), led, "r", 0, "stub", True, 1, think=False, seed_base=0)
    cliffed = dict(chars["b"]["current"]["relationships"]["a"])
    sc.faithful_turn = _mundane
    with redirect_stdout(io.StringIO()):
        sc.run_scene(world, chars, _cfg(31, "later"), led, "r", nxt, "stub", True, 1, think=False, seed_base=0)
    healed = chars["b"]["current"]["relationships"]["a"]
    print("       after the cliff: trust %.3f ; thirty days later: %.3f (affinity %.3f, at its authored rest)"
          % (cliffed["trust"], healed["trust"], healed["affinity"]))
    check("a-cliff-does-not-heal-over-a-winter", abs(healed["trust"] - bonds._CLIFF_FLOOR) < 1e-6, healed)
    check("the-other-axes-rest-where-they-were-authored", abs(healed["affinity"] - 0.90) < 1e-9, healed)


def test_presence_is_not_perception():
    print("\n[13] PERCEPTION GATES THE UPDATE — presence is not perception")
    sharp = {"perception": 0.90, "insight": 0.90}
    dull = {"perception": 0.20, "insight": 0.20}
    known = {"trust": 0.5}
    # a SLIGHT — low severity, so registering it takes noticing
    subtle = {"dimensions": {"social_violation": 0.25}, "durability": "transient", "object": "b", "showed": {"affinity": "curt"}}
    slight = _act(subtle, "a", "c")                                   # c watches it done to b
    print("       a slight (severity %.2f):  sharp=%s  dull=%s"
          % (slight["severity"], bonds.witnessed(slight, sharp, known),
             bonds.witnessed(slight, dull, known)))
    check("the-observant-catch-it", bonds.witnessed(slight, sharp, known))
    check("the-distracted-miss-it", not bonds.witnessed(slight, dull, known))
    # ...but you do not miss what is done to YOU (s6, overtness): the object registers it regardless
    check("the-object-witnesses-it-anyway", bonds.witnessed(_act(subtle, "a", "b"), dull, known))
    # a public betrayal — nobody in the room misses it
    overt = _act(_BETRAYAL)
    print("       a betrayal (severity %.2f): sharp=%s  dull=%s"
          % (overt["severity"], bonds.witnessed(overt, sharp, known),
             bonds.witnessed(overt, dull, known)))
    check("an-overt-act-is-not-missable", bonds.witnessed(overt, dull, known))
    # RECOGNITION: you can pin an act on someone you know; on a stranger you need insight
    check("a-stranger-needs-insight", not bonds.witnessed(overt, dull, {}))
    check("but-an-acquaintance-does-not", bonds.witnessed(overt, dull, known))
    check("a-perceptive-stranger-manages", bonds.witnessed(overt, sharp, {}))
    check("no-skills-admits-everything", bonds.witnessed(slight, None, {}))
    check("bad-skills-fails-loud", _raises(lambda: bonds.witnessed(overt, "sharp", {})))

    # ...and it reaches the scene loop: the same beat, two witnesses, one opinion
    import importlib.util as _u
    _sp = _u.spec_from_file_location("_sc_perc", os.path.join(REPO, "scripts", "scene.py"))
    sc = _u.module_from_spec(_sp)
    _sp.loader.exec_module(sc)
    actors = {}
    for wid, sk in (("b", sharp), ("c", dull)):
        ch = _person(wid, wid.upper(), {"a": {"trust": 0.5, "affinity": 0.5}})
        ch["baseline"]["skills"] = dict(sk)
        actors[wid] = {"id": wid, "char": ch}
    actors["a"] = {"id": "a", "char": _person("a", "A", {})}
    # object `a` (the speaker's own business), a respect word (stake-free): both are bystanders,
    # and only the sharp one registers it
    tags = {"dimensions": {"social_violation": 0.25}, "durability": "transient", "object": "a", "showed": {"respect": "careless"}}
    moved = {w: d for w, d, _v, _c in sc._bond_moves(actors, ["a", "b", "c"], "a", tags)}
    print("       scene loop -> %s" % {k: sorted(v) for k, v in moved.items()})
    check("only-the-observant-witness-moved", set(moved) == {"b"}, sorted(moved))


def test_second_order():
    print("\n[14] SECOND ORDER — what you think THEY make of YOU (relationships.md rich layer)")
    from src.engine.direction import direct_edge
    # someone who adores a person and is starting to suspect it is not returned
    edge = {"trust": 0.70, "affinity": 0.90, "respect": 0.70,
            "their_view": {"trust": 0.70, "affinity": 0.70, "respect": 0.70}}
    cold = _act({"dimensions": {"social_violation": 0.85}, "durability": "durable", "object": "b",
                 "showed": {"affinity": "harsh", "trust": "unreliable"}})
    mine = bonds.observe(edge, cold, _LOYAL)
    theirs = bonds.reflect(edge, cold, _LOYAL)
    print("       my read of THEM  : %s" % {k: round(v, 3) for k, v in mine.items()})
    print("       my read of THEIR read of ME: %s" % {k: round(v, 3) for k, v in theirs.items()})
    check("both-orders-move", bool(mine) and bool(theirs), "%s %s" % (mine, theirs))
    check("the-numbers-are-the-plan's", abs(mine["affinity"] + 0.1085) < 1e-3 and abs(mine["trust"] + 0.0328) < 1e-3
          and abs(theirs["affinity"] + 0.0766) < 1e-3, "%s %s" % (mine, theirs))
    check("trust-never-feeds-their_view", "trust" not in theirs, theirs)
    # a kindness confirms what I think of him (past the reach) while it still moves what I think he thinks of me
    kind_mine, kind_theirs = bonds.observe(edge, _act(_KIND), _LOYAL), bonds.reflect(edge, _act(_KIND), _LOYAL)
    check("the-orders-diverge-because-their-expectations-differ", kind_mine == {} and abs(kind_theirs.get("affinity", 0) - 0.0077) < 1e-3,
          "%s %s" % (kind_mine, kind_theirs))
    after = bonds.apply_reflection(bonds.apply_deltas(edge, mine), theirs)
    print("       affinity — mine %.3f -> %.3f | what I think theirs is %.3f -> %.3f"
          % (edge["affinity"], after["affinity"],
             edge["their_view"]["affinity"], after["their_view"]["affinity"]))
    check("the-two-can-diverge",
          abs(after["affinity"] - after["their_view"]["affinity"]) > 0.05, after)
    check("i-can-still-like-someone-i-think-does-not-like-me",
          after["affinity"] > after["their_view"]["affinity"], after)
    # a BYSTANDER learns about the actor, but nothing observed about how the actor regards THEM
    seen = _act({"dimensions": {"social_violation": 0.85}, "durability": "durable", "object": "b",
                 "showed": {"affinity": "harsh"}}, "a", "c")
    check("a-bystander-reflects-nothing", bonds.reflect({}, seen, _LOYAL) == {},
          "watching cruelty to someone else is inference about you, not observation")
    # no cliff on the second order — a cliff is a stance toward a person, not a reading of them
    steep = bonds.reflect({"their_view": {"affinity": 0.95}},
                          _act(dict(_BETRAYAL, showed={"affinity": "cruel", "trust": "treacherous"})), _LOYAL)
    check("no-cliff-on-the-second-order",
          0.95 + steep["affinity"] > bonds._CLIFF_FLOOR + 0.3, steep)
    check("bad-act-fails-loud", _raises(lambda: bonds.reflect({}, "nope", _LOYAL)))
    check("bad-deltas-fail-loud", _raises(lambda: bonds.apply_reflection({}, "nope")))

    # AND IT REACHES THE ACTOR — otherwise it is the authored-but-inert defect in a new place
    print("       rendered:")
    warm = direct_edge({"affinity": 0.90, "their_view": {"affinity": 0.90}})
    lonely = direct_edge({"affinity": 0.90, "their_view": {"affinity": 0.10}})
    print("         returned    -> %s" % warm)
    print("         unrequited  -> %s" % lonely)
    check("the-renderer-shows-the-gap", warm != lonely)
    check("an-edge-without-a-view-is-unchanged",
          direct_edge({"affinity": 0.9}) == direct_edge({"affinity": 0.9, "their_view": {}}))
    check("their-view-is-phrased-as-expectation", "they" in lonely.split("and as you read them,")[1])


def test_the_chair_moves_edges():
    print("\n[15] THE SINGLE-ACTOR CHAIR — one perceiver is still a perceiver")
    import importlib.util as _u
    from src.engine.ledger import Ledger
    from src.engine import bible
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    _sp = _u.spec_from_file_location("_dr_bonds", os.path.join(REPO, "scripts", "direct.py"))
    dr = _u.module_from_spec(_sp)
    _sp.loader.exec_module(dr)

    world = {"world": "w", "switches": {"magic": False, "divine": False, "beings": False},
             "locations": [{"id": "yard", "what": "the yard"}],
             "people": [{"id": "maren", "name": "Maren"}, {"id": "joss", "name": "Joss"}]}

    def _turn(by, dims, target="maren", showed=None, obj=None, etype="betray", transfers=None):
        ch = _person("maren", "Maren", {"joss": {"trust": 0.80, "affinity": 0.75,
                                                 "respect": 0.5, "debt": 0.30}})
        ch["fixed"]["name"] = "Maren"
        before = dict(ch["current"]["relationships"]["joss"])
        _tags = {"type": etype, "summary": "Joss took the purse", "subject": target, "dimensions": dims,
                 "durability": "durable", "confidence": 0.9,
                 "object": obj or target, "showed": showed or {"trust": "treacherous", "affinity": "harsh"},
                 "transfers": list(transfers or [])}
        dr.faithful_turn = lambda *a, **k: (
            {"action": "Maren says nothing and watches him.", "thought": "-", "exit": False,
             "addressee": "", "tags": _tags}, [])
        led = Ledger(":memory:")
        led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"},
                             "prompt_versions": {"turn": 1},
                             bible.CONFIG_KEY: bible.build(led.con, world, {"maren": ch})})
        led.register_character("r", "maren", ch["fixed"], ch["baseline"])
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            # run_turn RETURNS the evolved char — the arc deepcopies, so the passed-in dict can be
            # stale. The REPL rebinds; a caller that does not would silently lose every arc diff too.
            _a, _ok, out, _p = dr.run_turn(
                led, "r", ch, world, dr.subject_groups(world), dr.build_profile(ch),
                ch["baseline"]["temperament"], dict(ch["current"]["affect"]), 0,
                "Joss takes the purse off the table and pockets it.", [], "stub", True, by=by)
        return before, out["current"]["relationships"]["joss"], led

    before, after, led = _turn("joss", {"social_violation": 0.9})
    b0, a0 = dict(before), dict(after)     # the no-actor run below REBINDS before/after
    print("       by:joss  — Maren's trust in Joss %.3f -> %.3f" % (before["trust"], after["trust"]))
    check("a-named-actor-moves-the-edge", after["trust"] < before["trust"] - 0.2, after)
    check("and-the-second-order-follows", isinstance(after.get("their_view"), dict)
          and after["their_view"].get("affinity", 1.0) < 0.5, after.get("their_view"))

    before, after, led_none = _turn(None, {"social_violation": 0.9})
    print("       no by:   — %.3f -> %.3f" % (before["trust"], after["trust"]))
    check("no-actor-no-movement", after == before, after)

    # AND THE MOVEMENT IS PERSISTED. This block used to sit AFTER `led.append_turn`, so the chair
    # computed its deltas for a turn already written and stored NONE of them: the edge moved in
    # memory, printed a BOND line, and was gone at process exit. record-contract.md puts the write
    # on the CAUSING turn's commit, which is why the fix was to move the block above the commit
    # rather than to append the rows afterwards — a rolled-back turn would otherwise leave orphans.
    rows = led.edge_deltas_for("r", "maren")
    print("       persisted: %s" % rows)
    check("the-chair-persists-its-deltas", bool(rows), "the edge moved in memory and nowhere else")
    check("both-orders-reach-the-log", {r[3] for r in rows} == {"first", "second"}, rows)
    check("every-row-points-at-the-party-who-acted", all(r[0] == "joss" for r in rows), rows)
    check("the-signs-match-the-in-memory-edge",
          abs((a0["trust"] - b0["trust"])
              - sum(r[2] for r in rows if r[1] == "trust" and r[3] == "first")) < 1e-9,
          "before %r after %r rows %r" % (b0["trust"], a0["trust"], rows))
    turn_of = led.con.execute(
        "SELECT DISTINCT turn FROM relationship_deltas WHERE run_id='r'").fetchall()
    check("they-ride-the-causing-turn", [r[0] for r in turn_of] == [0], repr([tuple(r) for r in turn_of]))
    check("and-a-turn-with-no-actor-writes-nothing", not led_none.edge_deltas_for("r", "maren"))
    # GATE 4: the cliff's rest row rides turn 0; the actor's own `repaid` posts on her own account
    rest = led.con.execute("SELECT turn, perceiver, target, axis, rest, source FROM rest_declared WHERE run_id='r'").fetchall()
    print("       rest rows: %s" % [tuple(r) for r in rest])
    check("a-cliff-rest-row-rides-the-causing-turn", len(rest) == 1 and tuple(rest[0])[:4] == (0, "maren", "joss", "trust")
          and abs(rest[0][4] - bonds._CLIFF_FLOOR) < 1e-6 and rest[0][5] == "cliff", [tuple(r) for r in rest])
    # a by=None turn whose seat tags carry a TRANSFER from her to Joss as repayment: her own account falls
    b2, a2, led_own = _turn(None, {"care_relevant": 0.6}, target="joss", showed={"trust": "dependable"}, obj="joss", etype="aid",
                            transfers=[{"what": "the purse", "from": "self", "to": "joss", "terms": "repayment"}])
    own = led_own.edge_deltas_for("r", "maren")
    print("       by=None, repays joss with the purse: debt %.3f -> %.3f ; rows %s" % (b2["debt"], a2["debt"], own))
    check("the-actor's-repayment-lowers-what-she-owes", abs((b2["debt"] - a2["debt"]) - 0.03) < 1e-6, "%s -> %s" % (b2["debt"], a2["debt"]))
    check("and-writes-a-first-order-debt-row-under-her-own-name-with-the-cause", len(own) == 1 and own[0][0] == "joss" and own[0][1] == "debt" and abs(own[0][2] + 0.03) < 1e-6 and own[0][3] == "first", own)
    cause = led_own.con.execute("SELECT cause FROM relationship_deltas WHERE run_id='r' AND axis='debt'").fetchone()[0]
    check("the-row-says-what-changed-hands", cause == "the purse", cause)
    check("the-deltas-are-built-before-the-commit",
          open(os.path.join(REPO, "scripts", "direct.py"), encoding="utf-8").read().index("rel_deltas, bond_line, rest_rows, _cliff_lines = [], None, [], []")
          < open(os.path.join(REPO, "scripts", "direct.py"), encoding="utf-8").read().index("led.append_turn(TurnCommit("),
          "the block is back below the commit — the deltas would be orphaned on a rollback")

    # the REPL refuses an id that names nobody, rather than opening an edge to a ghost
    src = open(os.path.join(REPO, "scripts", "direct.py"), encoding="utf-8").read()
    check("repl-parses-the-by-prefix", 'startswith("by:")' in src)
    check("repl-refuses-an-unknown-id", "name an entity that exists" in src)
    check("the-actor-is-authored-not-inferred", "by=by" in src and "by=None" in src)


def test_edges_survive_the_scene():
    """An edge that moved must still be moved when the run resumes.

    `relationship_deltas` was written and never replayed — its only consumers were
    `citation._r_edge` and `read_api.edges`, neither of which rebuilds an edge. Once `arc.assess`
    stopped writing edges (gate bonds-inversion) the resume path restored NONE, so a cast came back
    as the people their sheet says they are and every trust movement from prior scenes was gone.
    Hard rule 2 is why replay is the repair rather than a stored snapshot: the log is the source of
    truth and the edge is a derivable cache.
    """
    print("\n[16] EDGES SURVIVE — replayed from the log, both orders")
    from src.engine.ledger import Ledger
    from src.engine.records import Event, RelationshipDelta, TurnCommit
    from src.engine import bible
    led = Ledger(":memory:")
    world = {"world": "w", "switches": {}, "locations": [{"id": "yard", "what": "the yard"}],
             "people": [{"id": "a", "name": "Ayla"}, {"id": "b", "name": "Beatrix"}]}
    chars = {"b": _person("b", "Beatrix", {"a": {"trust": 0.80, "affinity": 0.70}})}
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"},
                         "prompt_versions": {"turn": 1},
                         bible.CONFIG_KEY: bible.build(led.con, world, chars)})
    led.register_character("r", "b", chars["b"]["fixed"], chars["b"]["baseline"])
    led.append_turn(TurnCommit(
        run_id="r", turn=0, actor="a", thought="-", action="-", tags={}, validation={"ok": True},
        affect={p: 0.4 for p in _P}, condition={"energy": 0.7},
        events=[Event(type="betray", payload={"text": "x"}, actor="a")],
        rel_deltas=[RelationshipDelta("b", "a", "trust", -0.30, order="first"),
                    RelationshipDelta("b", "a", "affinity", -0.10, order="first"),
                    RelationshipDelta("b", "a", "affinity", -0.20, order="second")]))

    rows = led.edge_deltas_for("r", "b")
    print("       stored: %s" % rows)
    check("both-orders-stored", len(rows) == 3 and {r[3] for r in rows} == {"first", "second"}, rows)

    # THE REAL FOLD, not a copy of it. `bonds.rehydrate` is what both resume paths call; the
    # delta-only `replay` was retired 2026-09-10 (staging/src/engine/RETIRED-DEAD-FUNCTIONS-2026-09-10.py)
    # because nothing but this test called it.
    from src.engine import bond_rest
    tl = [("edge", t, a, d, o) for t, a, d, o in rows]
    rels = bond_rest.rehydrate({"a": {"trust": 0.80, "affinity": 0.70}}, {}, tl)
    print("       rehydrated: %s" % rels["a"])
    check("first-order-replays", abs(rels["a"]["trust"] - 0.50) < 1e-9, rels["a"]["trust"])
    check("affinity-replays", abs(rels["a"]["affinity"] - 0.60) < 1e-9, rels["a"]["affinity"])
    check("second-order-lands-in-their_view",
          abs(rels["a"]["their_view"]["affinity"] - 0.30) < 1e-9, rels["a"].get("their_view"))
    check("the-orders-do-not-collide",
          rels["a"]["affinity"] != rels["a"]["their_view"]["affinity"])
    # `rehydrate` walks declarations and movements INTERLEAVED by turn — drift is multiplicative
    # toward a prior and a delta is additive, so they do not commute; this asserts the resume
    # paths use the ordered fold.
    check("rehydrate-keeps-the-second-order",
          abs(rels["a"]["their_view"]["affinity"] - 0.30) < 1e-9, rels["a"].get("their_view"))
    # a REST item ahead of a TIME item: the declared rest wins over the stranger's (gate 4)
    walked = bond_rest.rehydrate({"a": {"trust": 0.80, "affinity": 0.70}}, {"default_trust": 0.5},
                                 [("rest", "a", "trust", 0.80), ("rest", "a", "affinity", 0.70), ("time", 30.0)] + tl)
    check("a-declared-rest-wins-over-the-stranger's", abs(walked["a"]["trust"] - 0.50) < 1e-9 and abs(walked["a"]["affinity"] - 0.60) < 1e-9, walked["a"])
    for _script in ("scene.py", "direct.py"):                       # BOTH resume paths, one fold
        _src = open(os.path.join(REPO, "scripts", _script), encoding="utf-8").read()
        check("%s-replays-through-bond_rest" % _script[:-3],
              "bond_rest.rehydrate" in _src and "timeline_for" in _src,
              "the ordered fold exists but this resume path does not call it")
    check("bad-order-fails-loud",
          _raises(lambda: RelationshipDelta("b", "a", "trust", -0.1, order="third").validate()))


def test_a_partial_edge_renders():
    """An edge carrying only SOME axes must still render.

    `scene._build_edges` used to fill the absent ones with None; `direct_edge` guards with
    `if axis in edge`, which is TRUE for a key present with value None, so `_check_num` raised
    "edge.respect must be a number in [0,1], got None" and the BEAT DIED. Latent for as long as
    every sheet-authored edge happened to carry all four axes. Presence is the contract the
    renderers were written against; the packet now honours it.

    RE-BASED 2026-09-19 (gate stranger-edge-birth). This block's first premise was that
    `bond_rest.rehydrate` reconstructs an edge toward someone the sheet never named with ONLY the
    axes that moved — "no respect, no debt, because the character holds no belief about those".
    That premise is retired: the character DOES hold a belief about a stranger on every axis — the
    sheet's `default_trust` on trust and the neutral elsewhere (bond-arithmetic.md s6, "what they
    assume about a stranger") — and the fold now births the edge whole at that rest, as the law
    prices it live (`bond_rest.whole`). The partial edge this block renders is therefore built by
    hand (a sheet may still author two axes); the fold's own shape is pinned first.
    """
    print("\n[17] A PARTIAL EDGE RENDERS — absence is omission, never None")
    from src.engine.scene import _build_edges
    from src.engine.direction import direct_edge

    from src.engine import bond_rest
    folded = bond_rest.rehydrate({}, {"default_trust": 0.3}, [("edge", "ren", "trust", -0.12, "first"),
                                                              ("edge", "ren", "affinity", -0.25, "first"),
                                                              ("edge", "ren", "respect", -0.30, "second")])
    print("       rehydrated: %s" % folded["ren"])
    check("rehydrate-births-a-stranger-edge-WHOLE-at-the-sheet's-rest",
          abs(folded["ren"]["trust"] - 0.18) < 1e-9 and abs(folded["ren"]["affinity"] - 0.25) < 1e-9
          and folded["ren"]["respect"] == 0.5 and folded["ren"]["debt"] == 0.0
          and abs(folded["ren"]["their_view"]["respect"] - 0.20) < 1e-9, folded["ren"])
    rels = {"ren": {"trust": 0.08, "affinity": 0.25, "their_view": {"respect": 0.2}}}   # a sheet that authored two axes

    world = {"world": "w", "people": [{"id": "ren", "what": "Ren, on the near bank"}]}
    edges = _build_edges({"relationships": rels}, [{"ref": "entity.ren"}], world)
    check("the-present-party-gets-an-edge", len(edges) == 1, edges)
    e = edges[0]
    check("an-absent-axis-is-OMITTED-not-None",
          "respect" not in e and "debt" not in e and e.get("trust") is not None, sorted(e))
    prose = direct_edge(e)                        # this RAISED before the fix
    print("       prose: %s" % prose)
    check("it-renders-instead-of-raising", isinstance(prose, str) and prose.strip())
    check("and-the-second-order-survives-the-trip", "as you read them" in prose, prose)

    full = _build_edges({"relationships": {"ren": {"trust": 0.8, "affinity": 0.7,
                                                   "respect": 0.6, "debt": 0.1}}},
                        [{"ref": "entity.ren"}], world)[0]
    check("a-complete-edge-is-unchanged",
          all(k in full for k in ("trust", "affinity", "respect", "debt")), sorted(full))
    check("an-authored-null-still-does-not-reach-the-renderer",
          "respect" not in _build_edges({"relationships": {"ren": {"trust": 0.8, "respect": None}}},
                                        [{"ref": "entity.ren"}], world)[0])
    check("the-frame-word-is-gone-from-the-status-line",
          "They are %s" not in open(os.path.join(REPO, "scripts", "direct.py"), encoding="utf-8").read())


def _raises(fn):
    try:
        fn()
        return False
    except ValueError:
        return True


def test_the_act_ladders_and_the_seam_are_live():
    """Bond gate 1 of 6 (2026-09-17, bond-arithmetic.md s2/s4). The seat answers on the ACT ladders
    (`severity.ACT_WORDS`: eight words per axis, no middle word) with an `object`; the parse seam
    prices the words (`bonds.observations_from_showed`) so a seat-shaped reply reaches
    `act_from_tags` as floats and MOVES AN EDGE. The retired `social` block is refused, not dormant.
    This test used to pin the dormancy ("LIVE-ROUTE-IS-DORMANT-ON-SEAT-WORDS"); flipped on purpose."""
    print("\n[18] THE ACT LADDERS + THE SEAM — live on seat output")
    from src.engine import severity as S
    # the act ladders: three axes, eight words, symmetric heights, disjoint from every other vocabulary
    check("three-act-axes", S.ACT_AXES == ("trust", "affinity", "respect"))
    for ax in S.ACT_AXES:
        vals = [S.act_value_of(ax, w) for w in S.ACT_WORDS[ax]]
        check("%s-eight-words-symmetric-about-the-stranger" % ax,
              vals == [0.10, 0.22, 0.34, 0.44, 0.56, 0.66, 0.78, 0.90], vals)
        check("%s-floor-word-reaches-the-cliff-and-nothing-else-does" % ax,
              vals[0] <= bonds._CLIFF_FLOOR < vals[1], (vals[0], bonds._CLIFF_FLOOR))
        check("%s-rubric-names-every-word-and-the-omission-rule" % ax,
              all(w in S.act_rubric(ax) for w in S.ACT_WORDS[ax]) and "OMITTED" in S.act_rubric(ax))
    from src.engine.rung_blocks import BANDS
    emo = {nm.lower() for b in BANDS.values() for _, _, nm in b} | {p.lower() for p in BANDS}
    act_all = {w for ax in S.ACT_AXES for w in S.ACT_WORDS[ax]}
    stand_all = {w for ws in S.STANDING_WORDS.values() for w in ws if w != "stranger"}
    check("act-words-collide-with-nothing", not (act_all & (emo | set(S.WORDS) | stand_all)), act_all & (emo | set(S.WORDS) | stand_all))
    check("standing-words-collide-with-nothing", not (stand_all & (emo | set(S.WORDS))), stand_all & (emo | set(S.WORDS)))
    for w in ("marked", "neutral", "reliance", "gave"):
        try:
            S.act_value_of("trust", w); check("act-ladder-refuses-%s" % w, False, "accepted")
        except S.SeverityError as e:
            check("act-ladder-refuses-%s" % w, e.code == "SEVERITY_ACT_WORD_UNKNOWN", e.code)
    # the standing ladder: nine bands tile [0,1], the stranger band is [.47,.53)
    check("stranger-band", S.standing_of("trust", 0.47) == "stranger" == S.standing_of("trust", 0.529) and S.standing_of("trust", 0.469) == "caution" and S.standing_of("trust", 0.53) == "reliance")
    seq = [S.standing_of("affinity", i / 1000.0) for i in range(0, 1001)]
    order = [w for i, w in enumerate(seq) if i == 0 or w != seq[i - 1]]
    check("nine-standing-bands-in-order", order == list(S.STANDING_WORDS["affinity"]), order)

    # the seam: a seat-shaped reply (act words + object) becomes floats, and the live route MOVES AN EDGE
    seat = {"type": "aid", "durability": "transient", "target": "b",
            "dimensions": {"care_relevant": 0.6},
            "showed": {"affinity": "generous", "respect": "masterly"},
            "transfers": [{"what": "a pot of jam", "from": "a", "to": "b", "terms": "none"}]}
    act = bonds.act_from_tags(seat, "a", "b")
    check("a-seat-shaped-reply-becomes-an-act", isinstance(act, dict) and abs(act["observations"]["affinity"] - 0.78) < 1e-9
          and abs(act["observations"]["respect"] - 0.78) < 1e-9, act)
    check("strength-comes-from-the-dimensions-not-the-read", abs(act["severity"] - 0.6) < 1e-9, act["severity"])
    check("the-transfer-posts-through-debt_postings-not-the-act", "debt_entry" not in act
          and bonds.debt_postings(seat, "a", {}, present=["a", "b"]) == [("b", "a", "gave", 0.03, "a pot of jam")])
    d = bonds.observe({"trust": 0.8, "affinity": 0.75, "respect": 0.7}, act, _LOYAL)
    check("...and-the-live-route-moves-an-edge", bool(d) and "affinity" in d, d)
    priced = bonds.observations_from_showed({"trust": 0.9, "affinity": "civil"})
    check("floats-pass-through-words-are-priced", priced == {"trust": 0.9, "affinity": 0.56}, priced)
    check("an-omitted-axis-is-nothing", "respect" not in bonds.act_from_tags(dict(seat, showed={"affinity": "kind"}), "a", "b")["observations"])
    for bad, code in (({"trust": "moderate"}, "BONDS_SHOWED_WORD_UNKNOWN"), ({"loyalty": "loyal"}, "BONDS_SHOWED_AXIS_UNKNOWN")):
        try:
            bonds.observations_from_showed(bad); check("seam-refuses-%s" % code, False, "accepted")
        except bonds.RecordError as e:
            check("seam-refuses-%s" % code, e.code == code, e.code)
    try:
        bonds.observations_from_showed({"debt": "gave"}); check("debt-inside-showed-is-no-axis", False, "accepted")
    except bonds.RecordError as e:
        check("debt-inside-showed-is-no-axis", e.code == "BONDS_SHOWED_AXIS_UNKNOWN", e.code)
    # the retired block: a legacy reply is REFUSED at the parse seam, and the fold no longer reads it
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import appraiser as A
    try:
        A.parse_event_reply('{"type": "aid", "dimensions": {}, "social": {"trust": "moderate"}}')
        check("the-social-block-is-refused-at-parse", False, "accepted")
    except Exception as e:                                                 # noqa: BLE001
        check("the-social-block-is-refused-at-parse", getattr(e, "code", "") == "APPRAISER_SOCIAL_RETIRED", getattr(e, "code", type(e).__name__))
    legacy = dict(seat); legacy.pop("showed"); legacy["social"] = {"trust": "moderate", "affinity": "marked"}
    check("a-legacy-social-block-still-produces-nothing-at-the-fold", bonds.act_from_tags(legacy, "a", "b") is None)
    # the prompt carries the ladders and the lists, and no longer the aimed-at line or the old block
    msgs = A.build_event_messages("x", present=["A", "B"], actor="A", target="B", referenced=["C"], attachments=["the ship"])
    sysm, usr = msgs[0]["content"], msgs[1]["content"]
    check("the-prompt-carries-the-three-act-ladders", all(w in sysm for w in ("treacherous", "steadfast", "cruel", "selfless", "disgraceful", "commanding")))
    check("the-prompt-no-longer-asks-for-social-strength-words", '"social"' not in sysm and "AIMED AT" not in usr)
    check("the-prompt-shows-the-people-and-the-attachments", "THE PEOPLE the act may be about: A, B, C" in usr and "the ship" in usr)
    check("the-prompt-carries-no-height", not re.search(r"0\.\d", sysm), "a ladder height reached the contract")
    # the drivers hand the seat's read to the fold through the existing bond_moves call
    import io as _io
    for name in ("scene.py", "direct.py"):
        src = _io.open(os.path.join(REPO, "scripts", name), encoding="utf-8").read()
        check("%s-still-calls-read_event-and-act_from_tags-or-bond_moves" % name, "read_event(" in src and ("act_from_tags(" in src or "_bond_moves(" in src))

def test_the_object_is_the_seats_and_received_follows_it():
    """Bond gate 3 (2026-09-17, bond-arithmetic.md s5). The seat names the act's OBJECT; the driver
    stops guessing. `received` is "the object resolves to this witness" (gate 5 adds "or she holds
    it", the `held=` hook); the second order fires for the received party only; the delta row and
    the event payload carry the object so a reader can see WHY an edge moved. A three-hander is the
    case the old guess got wrong: no seat `subject`, two others present -> target None -> nothing."""
    print("\n[19] THE OBJECT — named by the seat, received by the one it names")
    from src.engine.scene import resolve_subject
    from src.engine.ledger import Ledger
    from src.engine.records import Event, RelationshipDelta, TurnCommit, PATHS
    from src.engine import bible, db as _db
    import sqlite3
    tags = {"type": "aid", "durability": "transient", "dimensions": {"care_relevant": 0.6},
            "object": "b", "showed": {"affinity": 0.78, "trust": 0.66}}
    # resolve_subject: the object names a present person; a referenced one; none -> None in a three-hander
    edges = [{"target": "b"}, {"target": "c"}]
    check("the-object-resolves-a-present-person", resolve_subject(edges, {}, "b", [])[0] == "b")
    check("the-object-resolves-a-referenced-person", resolve_subject(edges, {}, "cobb", ["cobb"])[0] == "cobb")
    check("no-object-in-a-three-hander-is-nobody", resolve_subject(edges, {}, None, [])[0] is None)
    # received: B receives, C watches
    ab = bonds.act_from_tags(tags, "a", "b"); ac = bonds.act_from_tags(tags, "a", "c")
    check("the-named-party-receives", ab["received"] is True)
    check("a-bystander-does-not", ac["received"] is False)
    check("the-fallback-target-still-works-without-an-object", bonds.act_from_tags({"type": "aid", "dimensions": {"care_relevant": 0.6}, "target": "c", "showed": {"affinity": "kind"}}, "a", "c")["received"] is True)
    check("the-held-hook-makes-an-act-on-her-thing-received", bonds.act_from_tags(dict(tags, object="loc.orphanage"), "a", "c", held={"loc.orphanage": 0.85})["received"] is True)
    check("...and-not-when-she-does-not-hold-it", bonds.act_from_tags(dict(tags, object="loc.orphanage"), "a", "c", held={})["received"] is False)
    vb = bonds.reflect({"trust": 0.5, "affinity": 0.5}, ab, _LOYAL); vc = bonds.reflect({"trust": 0.5, "affinity": 0.5}, ac, _LOYAL)
    check("the-second-order-fires-for-the-received-party-only", bool(vb) and not vc, (vb, vc))
    # the delta row carries the object through a v27 ledger, and a v26 db gains the column
    led = Ledger(":memory:")
    world = {"world": "w", "switches": {}, "locations": [], "people": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]}
    led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1},
                         bible.CONFIG_KEY: bible.build(led.con, world, {})})
    led.append_turn(TurnCommit(run_id="r", turn=0, actor="a", thought="-", action="-", tags={}, validation={"ok": True},
                               affect={p: 0.2 for p in PATHS}, condition={"energy": 0.7},
                               events=[Event(type="aid", payload={"text": "x", "object": "b"}, actor="a")],
                               rel_deltas=[RelationshipDelta(perceiver="b", target="a", axis="affinity", delta=0.01, order="first", object="b")]))
    row = led.con.execute("SELECT object, ord FROM relationship_deltas WHERE run_id='r'").fetchone()
    check("the-delta-row-carries-the-object", row is not None and row["object"] == "b" and row["ord"] == "first", dict(row) if row else None)
    check("a-row-with-no-object-defaults-to-empty", RelationshipDelta(perceiver="b", target="a", axis="trust", delta=0.1).object == "")
    old = sqlite3.connect(":memory:")
    old.executescript("CREATE TABLE runs (run_id TEXT); CREATE TABLE relationship_deltas (delta_id INTEGER PRIMARY KEY, run_id TEXT, turn INTEGER, perceiver TEXT, target TEXT, axis TEXT, delta REAL, ord TEXT DEFAULT 'first', cause_event INTEGER); PRAGMA user_version=26;")
    try:
        _db._migrate(old)
        cols = {r[1] for r in old.execute("PRAGMA table_info(relationship_deltas)")}
        check("a-v26-db-gains-the-object-column-on-open", "object" in cols and old.execute("PRAGMA user_version").fetchone()[0] == _db.SCHEMA_VERSION, sorted(cols))
    except Exception as e:                                                # noqa: BLE001
        check("a-v26-db-gains-the-object-column-on-open", False, "%s: %s" % (type(e).__name__, str(e)[:120]))
    # the drivers write it
    import io as _io
    for name in ("scene.py", "direct.py"):
        src = _io.open(os.path.join(REPO, "scripts", name), encoding="utf-8").read()
        check("%s-writes-the-object-on-its-delta-rows" % name, 'object=str(applied.get("object")' in src)
    src = _io.open(os.path.join(REPO, "scripts", "scene.py"), encoding="utf-8").read()
    check("scene.py-feeds-the-object-to-resolve_subject", 'tags.get("object") or tags.get("subject")' in src)
    check("scene.py-records-the-object-and-showed-on-the-event", '"object": str(applied.get("object")' in src and '"showed": dict(applied.get("showed")' in src)

def main():
    print("test_bonds.py — the relationship tier")
    for t in (test_the_edge_belongs_to_the_perceiver, test_prediction_error, test_negativity_bias,
              test_scored_by_values, test_attribution, test_the_seat_writes_attribution_and_observe_prices_it,
              test_respect_and_debt_have_a_writer,
              test_drift, test_purity, test_arc_no_longer_writes_edges, test_trust_gates_transmission,
              test_the_scene_wires_it, test_the_scene_wires_drift, test_presence_is_not_perception,
              test_second_order, test_the_chair_moves_edges,
              test_edges_survive_the_scene, test_a_partial_edge_renders,
              test_the_act_ladders_and_the_seam_are_live,
              test_the_object_is_the_seats_and_received_follows_it):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
