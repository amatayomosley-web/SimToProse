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
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bonds                                   # noqa: E402
from src.engine.records import PRIMARIES, RELATIONSHIP_AXES     # noqa: E402

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

_BETRAYAL = {"dimensions": {"social_violation": 0.9}, "durability": "durable", "target": "b"}
_KINDNESS = {"dimensions": {"care_relevant": 0.9}, "durability": "durable", "target": "b"}


def _act(tags, actor="a", witness="b"):
    return bonds.act_from_tags(tags, actor, witness)


def test_the_edge_belongs_to_the_perceiver():
    print("\n[1] THE INVERSION — the edge that moves is the WITNESS's")
    check("witness-gets-an-act", _act(_BETRAYAL, "a", "b") is not None)
    check("act-points-at-the-actor", _act(_BETRAYAL, "a", "b")["toward"] == "a")
    check("nobody-holds-an-edge-to-themselves", _act(_BETRAYAL, "a", "a") is None)
    check("no-actor-no-act", _act(_BETRAYAL, "", "b") is None)
    check("no-dimensions-no-act", _act({"durability": "durable", "target": "b"}, "a", "b") is None)
    # the victim is the SUBJECT; a third party in the room is a bystander, and both are witnesses
    check("subject-is-flagged-received", _act(_BETRAYAL, "a", "b")["received"] is True)
    check("bystander-is-not", _act(_BETRAYAL, "a", "c")["received"] is False)
    # and resilience — the thing that inverted the old numbers — is nowhere in this module
    src = open(os.path.join(REPO, "src", "engine", "bonds.py"), encoding="utf-8").read()
    check("resilience-does-not-scale-an-edge", "resilience" not in src.split('"""')[2],
          "resilience appears in bonds.py CODE, not just the docstring")


def test_prediction_error():
    print("\n[2] PREDICTION ERROR — the current edge IS the expectation (relationships.md:26)")
    act = _act(_BETRAYAL)
    trusted = bonds.observe({"trust": 0.90}, act, _LOYAL)
    schemer = bonds.observe({"trust": 0.20}, act, _LOYAL)
    print("       betrayal by a TRUSTED friend : trust %+0.4f" % trusted["trust"])
    print("       the same from a KNOWN schemer: trust %+0.4f" % schemer["trust"])
    check("trusted-friend-moves-further", abs(trusted["trust"]) > abs(schemer["trust"]),
          "%s vs %s" % (trusted, schemer))
    # the doc's claim is not merely 'more' — it is 'catastrophic' vs 'barely registers'
    ratio = abs(trusted["trust"]) / max(abs(schemer["trust"]), 1e-9)
    print("       ratio: %.2fx" % ratio)
    check("and-by-a-lot", ratio >= 3.0, "only %.2fx" % ratio)
    # a kindness from someone you already trust is barely news; from an enemy it is
    kind = _act(_KINDNESS)
    warm = bonds.observe({"trust": 0.90, "affinity": 0.90}, kind, _LOYAL)
    cold = bonds.observe({"trust": 0.20, "affinity": 0.20}, kind, _LOYAL)
    check("kindness-from-an-enemy-moves-more",
          abs(cold.get("affinity", 0)) > abs(warm.get("affinity", 0)), "%s vs %s" % (cold, warm))
    # self-limiting: an edge already AT the observation does not move
    settled = bonds.observe({"trust": 0.5 - 0.5 * 0.9, "affinity": 0.5}, act, _LOYAL)
    check("no-surprise-no-move", "trust" not in settled, settled)


def test_negativity_bias():
    print("\n[3] NEGATIVITY BIAS — the right way round this time (relationships.md:27)")
    neutral = {"trust": 0.5, "affinity": 0.5, "respect": 0.5}
    down = bonds.observe(neutral, _act(_BETRAYAL), _LOYAL)["trust"]
    up = bonds.observe(neutral, _act(_KINDNESS), _LOYAL)["trust"]
    # equal-size surprises: betrayal observes trust at 0.05, kindness at 0.5+0.5*0.9*0.6 = 0.77
    # so normalise by the surprise each one carries before comparing the RATES
    rate_down = abs(down) / abs(0.05 - 0.5)
    rate_up = abs(up) / abs(0.77 - 0.5)
    print("       betrayal: trust %+0.4f  (rate %.4f per unit surprise)" % (down, rate_down))
    print("       kindness: trust %+0.4f  (rate %.4f per unit surprise)" % (up, rate_up))
    check("losses-outrun-gains", rate_down > rate_up, "%.4f vs %.4f" % (rate_down, rate_up))
    print("       ratio: %.2fx — the OLD path gave 0.50x here (kindness 2x betrayal at resilience 0.70)"
          % (rate_down / rate_up))
    check("and-the-old-inversion-is-gone", rate_down / rate_up > 1.5)


def test_scored_by_values():
    print("\n[4] SCORED BY THE PERCEIVER'S VALUES — including whether it is a CLIFF at all")
    edge = {"trust": 0.85}
    loyal = bonds.observe(edge, _act(_BETRAYAL), _LOYAL)
    indiff = bonds.observe(edge, _act(_BETRAYAL), _INDIFFERENT)
    after_loyal = bonds.apply_deltas(edge, loyal)["trust"]
    after_indiff = bonds.apply_deltas(edge, indiff)["trust"]
    print("       loyalty-valuer      : trust 0.85 -> %.4f" % after_loyal)
    print("       loyalty-indifferent : trust 0.85 -> %.4f" % after_indiff)
    check("the-loyalty-valuer-falls-to-the-cliff", abs(after_loyal - bonds._CLIFF_FLOOR) < 1e-6,
          after_loyal)
    check("the-indifferent-one-only-slopes", after_indiff > bonds._CLIFF_FLOOR + 0.3, after_indiff)
    check("same-act-different-people", abs(after_loyal - after_indiff) > 0.3)
    # a cliff is a DISCONTINUITY: it must not scale smoothly with severity
    mild = dict(_BETRAYAL, dimensions={"social_violation": 0.75})   # just under _CLIFF_SEVERITY
    after_mild = bonds.apply_deltas(edge, bonds.observe(edge, _act(mild), _LOYAL))["trust"]
    print("       severity 0.75 (sub-cliff) -> %.4f   severity 0.90 (cliff) -> %.4f"
          % (after_mild, after_loyal))
    check("sub-cliff-stays-a-slope", after_mild > bonds._CLIFF_FLOOR + 0.3, after_mild)


def test_attribution():
    print("\n[5] ATTRIBUTION — why they think it happened (relationships.md:29)")
    edge = {"trust": 0.80}
    out = {}
    for att in ("malice", "negligence", "coerced", "accident"):
        tags = dict(_BETRAYAL, attribution=att)
        out[att] = bonds.observe(edge, _act(tags), _LOYAL).get("trust", 0.0)
        print("       %-11s trust %+0.4f" % (att, out[att]))
    check("malice-hurts-most", abs(out["malice"]) > abs(out["negligence"]) > abs(out["coerced"]) > abs(out["accident"]),
          out)
    check("an-accident-barely-registers", abs(out["accident"]) < abs(out["malice"]) * 0.3, out)
    untagged = bonds.observe(edge, _act(_BETRAYAL), _LOYAL).get("trust", 0.0)
    check("untagged-reads-as-intent", abs(untagged - out["malice"]) < 1e-9,
          "an untagged act must behave exactly as a malicious one — no silent damping")
    # ...and whether the excuse is BELIEVED depends on the witness. relationships.md:29 requires
    # misattribution to be possible ("tragic misunderstandings are first-class") but gives no rule
    # for it; charity-scaled-by-trust is this engine's answer, and it is marked as an extension.
    acc = dict(_BETRAYAL, attribution="accident")

    def _rate(trust, tags):
        """|delta| per unit of surprise — isolates CHARITY from prediction error, which also
        varies with trust. (Comparing raw deltas here would measure both at once, and at trust 0.05
        the surprise is exactly zero — the observation IS 0.05 — so nothing moves at all.)"""
        d = bonds.observe({"trust": trust}, _act(tags), _LOYAL).get("trust", 0.0)
        return abs(d) / abs(0.05 - trust)

    believed, disbelieved = _rate(0.95, acc), _rate(0.35, acc)
    print("       the SAME accident, read by a TRUSTING witness  : rate %.4f" % believed)
    print("       ...and by one who trusts them much less        : rate %.4f" % disbelieved)
    check("the-excuse-needs-a-believer", disbelieved > believed * 1.5,
          "%.4f vs %.4f" % (disbelieved, believed))
    # ...but nobody is beyond all doubt: an accident still hurts less than open malice, even read
    # by the witness least inclined to believe it.
    check("charity-never-reaches-zero",
          disbelieved < _rate(0.35, dict(_BETRAYAL, attribution="malice")),
          "an accident must never cost as much as open malice")


def test_respect_and_debt_have_a_writer():
    print("\n[6] RESPECT AND DEBT — no writer existed anywhere in the repo before this")
    # respect, from the fallback map: watching someone be good at a thing
    mastery = {"dimensions": {"mastery": 0.85}, "durability": "durable", "target": "b"}
    d = bonds.observe({"respect": 0.4}, _act(mastery), _LOYAL)
    print("       witnessed mastery -> %s" % d)
    check("respect-moves", d.get("respect", 0) > 0, d)
    # debt: only for the party the act was ABOUT
    got = bonds.observe({}, _act(_KINDNESS, "a", "b"), _LOYAL)      # b IS the subject
    saw = bonds.observe({}, _act(_KINDNESS, "a", "c"), _LOYAL)      # c merely watched
    print("       kindness RECEIVED -> %s" % got)
    print("       kindness WITNESSED -> %s" % saw)
    check("receiving-a-kindness-creates-debt", got.get("debt", 0) > 0, got)
    check("watching-one-does-not", "debt" not in saw, saw)
    check("but-watching-still-warms-you", saw.get("affinity", 0) > 0, saw)
    # debt ACCUMULATES — it is an account, not a belief, so a second favour still registers
    first = bonds.observe({"debt": 0.0}, _act(_KINDNESS), _LOYAL)["debt"]
    later = bonds.observe({"debt": 0.9}, _act(_KINDNESS), _LOYAL)["debt"]
    check("debt-does-not-converge", abs(first - later) < 1e-9,
          "a favour to someone you already owe must still count: %s vs %s" % (first, later))
    check("every-axis-now-has-a-writer",
          set(RELATIONSHIP_AXES) <= {"trust", "affinity"} | {"respect"} | {"debt"})

    # --- the `social` block: acts the dimension fallback CANNOT express ---
    print("       -- the optional `social` block --")
    # deferring to someone's judgement. No mastery dimension, so the fallback map says nothing.
    defer = {"type": "mundane", "dimensions": {"mastery": 0.0}, "durability": "transient",
             "target": "b", "social": {"respect": 0.9}}
    fallback_only = bonds.observe({"respect": 0.4}, _act(dict(defer, social={})) or
                                  {"observations": {}, "severity": 0.0, "dominant": ""}, _LOYAL)
    with_block = bonds.observe({"respect": 0.4}, _act(defer), _LOYAL)
    print("       deferral, dimensions alone -> %s" % fallback_only)
    print("       deferral, with `social`    -> %s" % with_block)
    check("the-fallback-cannot-say-it", not fallback_only, fallback_only)
    check("the-social-block-can", with_block.get("respect", 0) > 0, with_block)
    # a debt DISCHARGED — the fallback only ever adds debt; nothing could subtract it
    settle = {"type": "mundane", "dimensions": {"mastery": 0.1}, "durability": "transient",
              "target": "b", "social": {"debt": 0.05}}
    d = bonds.observe({"debt": 0.6}, _act(settle), _LOYAL)
    print("       calling in a favour        -> %s" % d)
    check("a-debt-can-now-be-settled", d.get("debt", 0) < 0, d)
    # the block is authoritative where it speaks: an explicit reading overrides the dimension map
    contra = {"type": "betray", "dimensions": {"social_violation": 0.9}, "durability": "durable",
              "target": "b", "social": {"trust": 0.95}}
    check("an-explicit-reading-wins", bonds.observe({"trust": 0.5}, _act(contra), _LOYAL)["trust"] > 0,
          "the social block must override the dimension fallback, not merge with it")
    # and a malformed block is ignored rather than crashing the beat
    junk = dict(_BETRAYAL, social={"loyalty": 0.2, "trust": "very low"})
    check("junk-keys-ignored", "loyalty" not in (_act(junk) or {}).get("observations", {}))


def test_drift():
    print("\n[7] DRIFT — unreinforced edges settle back (relationships.md:30)")
    edge = {"trust": 0.90, "affinity": 0.90, "respect": 0.90, "debt": 0.50}
    out = bonds.drift(edge, {"default_trust": 0.30}, elapsed=5.0)
    print("       %s" % {k: round(v, 4) for k, v in out.items()})
    check("everything-moves-toward-rest", all(out[a] < edge[a] for a in edge), out)
    moved = {a: edge[a] - out[a] for a in edge}
    check("affinity-fades-faster-than-trust", moved["affinity"] > moved["trust"], moved)
    check("debt-barely-fades", moved["debt"] < moved["affinity"], moved)
    check("drift-uses-relationship_priors", bonds.drift(edge, {"default_trust": 0.30}, 50)["trust"]
          < bonds.drift(edge, {"default_trust": 0.80}, 50)["trust"],
          "default_trust must set where trust RESTS — it had no runtime reader before this")
    check("zero-elapsed-is-a-no-op", bonds.drift(edge, {}, 0.0) == edge)
    check("an-absent-axis-stays-absent", "respect" not in bonds.drift({"trust": 0.7}, {}, 3.0))


def test_purity():
    print("\n[8] PURE — engine rules 3, 4, 6")
    edge = {"trust": 0.8, "affinity": 0.6}
    before = dict(edge)
    bonds.apply_deltas(edge, bonds.observe(edge, _act(_BETRAYAL), _LOYAL))
    check("apply_deltas-does-not-mutate", edge == before, edge)
    check("clamped-to-0-1", all(0.0 <= v <= 1.0 for v in
          bonds.apply_deltas({"trust": 0.02}, {"trust": -9.0}).values()))
    for bad, fn in ((("observe", lambda: bonds.observe({}, "nope", _LOYAL))),
                    (("observe", lambda: bonds.observe({}, _act(_BETRAYAL), "nope"))),
                    (("apply_deltas", lambda: bonds.apply_deltas({}, "nope"))),
                    (("drift", lambda: bonds.drift({}, {}, "soon")))):
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
    src = open(os.path.join(REPO, "src", "engine", "bonds.py"), encoding="utf-8").read()
    check("no-randomness", "import random" not in src)
    check("no-llm", "openai" not in src and "requests" not in src)
    check("under-500-lines", len(src.splitlines()) < 500, len(src.splitlines()))


_P = PRIMARIES          # DERIVED, never re-listed — a hand-copy of this went stale
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
    hist = {"temperament": {"FEAR": 0.01}, "relationships": {"b": {"trust": -0.02}}, "regard": {}}
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
             "b": _person("b", "Bran", {"a": {"trust": 0.85, "affinity": 0.70, "respect": 0.5, "debt": 0.0}})}
    world = {"world": "w", "switches": {"magic": False, "divine": False, "beings": False},
             "locations": [{"id": "yard", "what": "the yard"}],
             "people": [{"id": "a", "name": "Ayla"}, {"id": "b", "name": "Bran"}]}
    cfg = {"situation": "Two people stand in the yard.", "subject": ("b", None),
           "opening_tags": {"type": "mundane", "dimensions": {"social_violation": 0.5},
                            "durability": "transient"},
           "cast": [{"id": "a", "drive": "press the point"}, {"id": "b", "drive": "hold ground"}],
           "name": "bondprobe"}
    sc._NAMES = {"a": "Ayla", "b": "Bran"}
    # A betrays B. `type` must be a CATALOG key or validate_tags zeroes the dimensions and nothing
    # moves — the failure mode that made the first run of this probe read as "the loop never fired".
    sc.faithful_turn = lambda packet, event_text, temperament, model, stub, **kw: (
        {"action": "Ayla tells the others what Bran said in confidence.",
         "thought": "it had to come out", "exit": False, "addressee": "",
         "tags": {"type": "betray", "summary": "Ayla broke Bran's confidence in front of the yard",
                  "subject": "b", "dimensions": {"social_violation": 0.9},
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
    sc._NAMES = {"a": "Ayla", "b": "Bran"}
    sc.faithful_turn = lambda *a, **k: ({"action": "Ayla says nothing much.", "thought": "-",
                                         "exit": False, "addressee": "",
                                         "tags": {"type": "mundane", "summary": "", "subject": "",
                                                  "dimensions": {}, "durability": "transient",
                                                  "confidence": 0.5}}, [])

    def _run(elapsed, trust_prior=0.30):
        """One scene, zero meaningful beats — so any edge movement is drift and nothing else."""
        start = {"trust": 0.90, "affinity": 0.90, "respect": 0.90, "debt": 0.50}
        chars = {"a": _person("a", "Ayla", {"b": dict(start)}),
                 "b": _person("b", "Bran", {"a": dict(start)})}
        for c in chars.values():
            c["baseline"]["relationship_priors"] = {"default_trust": trust_prior}
        world = {"world": "w", "switches": {"magic": False, "divine": False, "beings": False},
                 "locations": [{"id": "yard", "what": "the yard"}],
                 "people": [{"id": "a", "name": "Ayla"}, {"id": "b", "name": "Bran"}]}
        cfg = {"situation": "Two people stand in the yard.", "subject": (None, None),
               "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
               "cast": [{"id": "a", "drive": "wait"}, {"id": "b", "drive": "wait"}], "name": "drift"}
        if elapsed:
            cfg["elapsed"] = elapsed
        led = Ledger(":memory:")
        led.create_run("r", {"catalog_version": 1, "models": {"turn": "stub"},
                             "prompt_versions": {"turn": 1},
                             bible.CONFIG_KEY: bible.build(led.con, world, chars)})
        for cid in ("a", "b"):
            led.register_character("r", cid, chars[cid]["fixed"], chars[cid]["baseline"])
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            sc.run_scene(world, chars, cfg, led, "r", 0, "stub", True, 1, think=False, seed_base=0)
        return start, chars["a"]["current"]["relationships"]["b"]

    start, none = _run(None)
    check("no-elapsed-no-drift", none == start, none)
    _, after = _run(5.0)
    print("       before        %s" % {k: round(v, 3) for k, v in start.items()})
    print("       after 5 units %s" % {k: round(v, 3) for k, v in after.items()})
    check("edges-relaxed", all(after[k] < start[k] for k in start), after)
    check("affinity-outpaces-trust", (start["affinity"] - after["affinity"])
          > (start["trust"] - after["trust"]), after)
    # the resting point is the CHARACTER's, not a constant — relationship_priors finally reads
    _, low = _run(30.0, trust_prior=0.20)
    _, high = _run(30.0, trust_prior=0.80)
    print("       default_trust 0.20 -> trust %.3f   default_trust 0.80 -> trust %.3f"
          % (low["trust"], high["trust"]))
    check("different-priors-different-resting-points", low["trust"] < high["trust"] - 0.2,
          "relationship_priors had no runtime reader before this")


def test_presence_is_not_perception():
    print("\n[13] PERCEPTION GATES THE UPDATE — presence is not perception")
    sharp = {"perception": 0.90, "insight": 0.90}
    dull = {"perception": 0.20, "insight": 0.20}
    known = {"trust": 0.5}
    # a SLIGHT — low severity, so registering it takes noticing
    slight = _act({"dimensions": {"social_violation": 0.25}, "durability": "transient", "target": "b"})
    print("       a slight (severity %.2f):  sharp=%s  dull=%s"
          % (slight["severity"], bonds.witnessed(slight, sharp, known),
             bonds.witnessed(slight, dull, known)))
    check("the-observant-catch-it", bonds.witnessed(slight, sharp, known))
    check("the-distracted-miss-it", not bonds.witnessed(slight, dull, known))
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
    tags = {"dimensions": {"social_violation": 0.25}, "durability": "transient", "target": "b"}
    moved = {w: d for w, d, _v in sc._bond_moves(actors, ["a", "b", "c"], "a", tags)}
    print("       scene loop -> %s" % {k: sorted(v) for k, v in moved.items()})
    check("only-the-observant-witness-moved", set(moved) == {"b"}, sorted(moved))


def test_second_order():
    print("\n[14] SECOND ORDER — what you think THEY make of YOU (relationships.md rich layer)")
    from src.engine.direction import direct_edge
    # someone who adores a person and is starting to suspect it is not returned
    edge = {"trust": 0.70, "affinity": 0.90, "respect": 0.70,
            "their_view": {"trust": 0.70, "affinity": 0.90, "respect": 0.70}}
    cold = _act({"dimensions": {"social_violation": 0.85}, "durability": "durable", "target": "b"})
    mine = bonds.observe(edge, cold, _LOYAL)
    theirs = bonds.reflect(edge, cold, _LOYAL)
    print("       my read of THEM  : %s" % {k: round(v, 3) for k, v in mine.items()})
    print("       my read of THEIR read of ME: %s" % {k: round(v, 3) for k, v in theirs.items()})
    check("both-orders-move", bool(mine) and bool(theirs), (mine, theirs))
    after = bonds.apply_reflection(bonds.apply_deltas(edge, mine), theirs)
    print("       affinity — mine %.3f -> %.3f | what I think theirs is %.3f -> %.3f"
          % (edge["affinity"], after["affinity"],
             edge["their_view"]["affinity"], after["their_view"]["affinity"]))
    check("the-two-can-diverge",
          abs(after["affinity"] - after["their_view"]["affinity"]) > 0.05, after)
    check("i-can-still-like-someone-i-think-does-not-like-me",
          after["affinity"] > after["their_view"]["affinity"], after)
    # a BYSTANDER learns about the actor, but nothing observed about how the actor regards THEM
    seen = _act({"dimensions": {"social_violation": 0.85}, "durability": "durable", "target": "b"},
                "a", "c")
    check("a-bystander-reflects-nothing", bonds.reflect({}, seen, _LOYAL) == {},
          "watching cruelty to someone else is inference about you, not observation")
    # no cliff on the second order — a cliff is a stance toward a person, not a reading of them
    steep = bonds.reflect({"their_view": {"trust": 0.95}}, cold, _LOYAL)
    check("no-cliff-on-the-second-order",
          0.95 + steep["trust"] > bonds._CLIFF_FLOOR + 0.3, steep)
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

    def _turn(by, dims, target="maren"):
        ch = _person("maren", "Maren", {"joss": {"trust": 0.80, "affinity": 0.75,
                                                 "respect": 0.5, "debt": 0.0}})
        ch["fixed"]["name"] = "Maren"
        before = dict(ch["current"]["relationships"]["joss"])
        dr.faithful_turn = lambda *a, **k: (
            {"action": "Maren says nothing and watches him.", "thought": "-", "exit": False,
             "addressee": "", "tags": {"type": "betray", "summary": "Joss took the purse",
                                       "subject": target, "dimensions": dims,
                                       "durability": "durable", "confidence": 0.9}}, [])
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
    check("the-deltas-are-built-before-the-commit",
          open(os.path.join(REPO, "scripts", "direct.py"), encoding="utf-8").read().index("rel_deltas, bond_line = [], None")
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
             "people": [{"id": "a", "name": "Ayla"}, {"id": "b", "name": "Bran"}]}
    chars = {"b": _person("b", "Bran", {"a": {"trust": 0.80, "affinity": 0.70}})}
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

    # THE REAL FOLD, not a copy of it. An earlier draft of this test re-implemented the loop and
    # then grepped scripts/scene.py for the method name — a proxy for the thing, which would have
    # stayed green while the two drifted. bonds.replay is what both resume paths call.
    rels = bonds.replay({"a": {"trust": 0.80, "affinity": 0.70}}, rows)
    print("       replayed: %s" % rels["a"])
    check("first-order-replays", abs(rels["a"]["trust"] - 0.50) < 1e-9, rels["a"]["trust"])
    check("affinity-replays", abs(rels["a"]["affinity"] - 0.60) < 1e-9, rels["a"]["affinity"])
    check("second-order-lands-in-their_view",
          abs(rels["a"]["their_view"]["affinity"] - 0.30) < 1e-9, rels["a"].get("their_view"))
    check("the-orders-do-not-collide",
          rels["a"]["affinity"] != rels["a"]["their_view"]["affinity"])
    for _script in ("scene.py", "direct.py"):                       # BOTH resume paths, one fold
        _src = open(os.path.join(REPO, "scripts", _script), encoding="utf-8").read()
        check("%s-replays-through-bonds" % _script[:-3],
              "bonds.replay" in _src and "edge_deltas_for" in _src,
              "the reader exists but this resume path does not call it")
    check("replay-refuses-an-unknown-axis",
          _raises(lambda: bonds.replay({}, [("a", "loyalty", 0.1, "first")])))
    check("bad-order-fails-loud",
          _raises(lambda: RelationshipDelta("b", "a", "trust", -0.1, order="third").validate()))


def test_a_partial_edge_renders():
    """An edge carrying only the axes that MOVED must still render.

    `bonds.replay` reconstructs an edge toward someone the character's sheet never named, and it
    carries only the axes that actually moved — no respect, no debt, because the character holds no
    belief about those. `scene._build_edges` used to fill the absent ones with None; `direct_edge`
    guards with `if axis in edge`, which is TRUE for a key present with value None, so `_check_num`
    raised "edge.respect must be a number in [0,1], got None" and the BEAT DIED. Latent for as long
    as every sheet-authored edge happened to carry all four axes. Presence is the contract the
    renderers were written against; the packet now honours it.
    """
    print("\n[17] A PARTIAL EDGE RENDERS — absence is omission, never None")
    from src.engine.scene import _build_edges
    from src.engine.direction import direct_edge

    rels = bonds.replay({}, [("ren", "trust", -0.42, "first"),
                             ("ren", "affinity", -0.25, "first"),
                             ("ren", "respect", -0.30, "second")])
    print("       replayed: %s" % rels["ren"])
    check("replay-does-not-invent-unmoved-axes",
          "debt" not in rels["ren"] and "respect" not in rels["ren"], rels["ren"])

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


def main():
    print("test_bonds.py — the relationship tier")
    for t in (test_the_edge_belongs_to_the_perceiver, test_prediction_error, test_negativity_bias,
              test_scored_by_values, test_attribution, test_respect_and_debt_have_a_writer,
              test_drift, test_purity, test_arc_no_longer_writes_edges, test_trust_gates_transmission,
              test_the_scene_wires_it, test_the_scene_wires_drift, test_presence_is_not_perception,
              test_second_order, test_the_chair_moves_edges,
              test_edges_survive_the_scene, test_a_partial_edge_renders):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
