#!/usr/bin/env python3
"""test_floor.py — the turn-taking economy: who wants the floor next.

THESE FIVE FUNCTIONS HAD NO DISCOVERABLE SUITE. They lived in `scripts/scene.py`, and
`tests/run_all.py` walks `tests/` — so the only coverage any of them had was `tests/test_bonds.py`
loading a 1052-line CLI through `spec_from_file_location` to exercise a nine-line function. Moving
them to `src/engine/floor.py` (CLAUDE.md's Modes law: a driver never computes a value) is what
makes this file possible, and this file is the reason the move was worth making.

Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import floor                                       # noqa: E402
from src.engine import prompt                                      # noqa: E402
from src.engine.records import PATHS                           # noqa: E402
from src.engine.state import build_profile                         # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % detail))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


# THE SHAPE COMES FROM A REAL SHEET, not from what the functions happened to accept. Checked
# against characters/maren-healer.json 2026-09-03, and the first draft was wrong three ways:
#   - it gave the witnesses `empathy`, which `bonds.witnessed` never reads, and OMITTED `perception`,
#     which is the skill its overtness check actually needs;
#   - traits were `{"mean": x}` where a real sheet writes `{mean, variability}`;
#   - edges carried trust+affinity where a real edge carries trust, affinity, respect and debt,
#     so two of the four axes `bonds.observe` can move were never present to move.
# A fixture built from what the code tolerates tests the code against itself.
_SKILLS = {"perception": 0.9, "insight": 0.9}
_EDGE = {"trust": 0.5, "affinity": 0.5, "respect": 0.5, "debt": 0.0}


def _person(cid, name, extraversion=0.5, standing=0.5, spread=0.3):
    """THE THREE STANDING VALUES MUST DIFFER. They were identical in the first draft, which made
    `max` and `mean` return the same number — so the breakage that turned order_weight into a max
    did not move a single assertion. A fixture whose values are all equal cannot tell an average
    from any other symmetric summary."""
    lo, hi = max(0.0, standing - spread), min(1.0, standing + spread)
    return {"fixed": {"id": cid, "name": name},
            "baseline": {"traits": {"extraversion": {"mean": extraversion,
                                                     "variability": 0.1}},
                         "model": {"schwartz": {"conformity": lo, "security": standing,
                                                "power": hi}},
                         "skills": {}},
            "current": {"relationships": {}}}


def _listener(cid="b", extraversion=0.5, standing=0.5, affect=None):
    """`affect=None` reproduces every existing call site (uniform 0.5) unchanged; a caller that
    needs a listener whose counterfactual appraise moves BY MORE (gate lands-on-to-floor, checking
    that pruning actually zeroes a nonzero salience rather than a term already near 0) passes its
    own starting affect."""
    ch = _person(cid, cid.upper(), extraversion, standing)
    return {"id": cid, "char": ch, "affect": affect or {p: 0.5 for p in PATHS},
            "profile": build_profile(ch), "extraversion": extraversion}


def test_order_weight_is_the_MEAN_of_the_standing_cluster():
    """A decorum-keeper's stake in ORDER. Asserted as the arithmetic it claims to be, because a
    weight that silently became a max or a sum would still look plausible in every trace."""
    p = build_profile(_person("d", "D", standing=0.5, spread=0.3))     # 0.2 / 0.5 / 0.8
    check("mean-of-conformity-security-power", abs(floor.order_weight(p) - 0.5) < 1e-9,
          floor.order_weight(p))
    check("and-it-is-not-the-MAX-of-them", abs(floor.order_weight(p) - 0.8) > 1e-9,
          "returns the largest value, not the average")
    p2 = build_profile(_person("e", "E", standing=0.2, spread=0.1))
    check("a-lower-cluster-weighs-less", floor.order_weight(p2) < floor.order_weight(p),
          "%r vs %r" % (floor.order_weight(p2), floor.order_weight(p)))


def test_urge_moves_the_way_each_TERM_says_it_does():
    """Four terms push the urge, and each is asserted ALONE against an otherwise identical listener.
    A composite that only ever gets checked as a total can have two terms wrong in opposite
    directions and still look right."""
    tags = {"dimensions": {"social_violation": 0.0}, "durability": "transient"}
    base, _s, _d = floor.urge(tags, None, None, _listener(), False, 99)

    addressed, _s, _d = floor.urge(tags, None, None, _listener(), True, 99)
    check("being-addressed-adds-the-bonus",
          abs((addressed - base) - floor.ADDRESSED_BONUS) < 1e-9, addressed - base)

    just_spoke, _s, _d = floor.urge(tags, None, None, _listener(), False, 0)
    check("having-just-spoken-costs-recency",
          abs((base - just_spoke) - floor.RECENCY_PENALTY) < 1e-9, base - just_spoke)

    timid, _s, _d = floor.urge(tags, None, None, _listener(extraversion=0.0), False, 99)
    bold, _s, _d = floor.urge(tags, None, None, _listener(extraversion=1.0), False, 99)
    check("inhibition-scales-with-1-minus-extraversion",
          abs((bold - timid) - floor.INHIBITION) < 1e-9, bold - timid)

    loud = {"dimensions": {"social_violation": 1.0}, "durability": "transient"}
    keeper, _s, disruption = floor.urge(loud, None, None, _listener(standing=1.0), False, 99)
    easy, _s, _d2 = floor.urge(loud, None, None, _listener(standing=0.0), False, 99)
    check("a-decorum-keeper-is-pulled-in-by-a-violation", keeper > easy,
          "%r vs %r" % (keeper, easy))
    check("disruption-is-reported-for-the-trace", disruption > 0, disruption)


def test_bond_moves_never_includes_the_SPEAKER():
    """An edge is the PERCEIVER's belief — the loop exists because `arc.assess` runs on the speaker
    and that is the wrong subject.

    THE PROPERTY IS REAL AND THE GUARD IS DOUBLED, which this docstring says because breakage-
    testing found it: removing `bond_moves`' own `i != speaker` filter changes NOTHING, since
    `bonds.act_from_tags` (src/engine/bonds.py:128) already returns None when actor and witness are
    the same person — "nobody holds an edge to themselves". So this test pins the INVARIANT, not
    that line, and a reader must not treat it as cover for the filter. If the redundant filter is
    ever removed as dead code, this stays green and stays correct."""
    # EVERY actor, the speaker INCLUDED, is given the skills and the edge that make an act
    # witnessable. The first draft equipped only b and c, so the speaker was filtered by
    # `bonds.witnessed` returning False — and removing the `i != speaker` exclusion changed
    # nothing. The test passed because of a fixture gap, not because of the line it names.
    actors = {cid: {"id": cid, "char": _person(cid, cid.upper())} for cid in ("a", "b", "c")}
    for cid in ("a", "b", "c"):
        actors[cid]["char"]["baseline"]["skills"] = dict(_SKILLS)
        actors[cid]["char"]["current"]["relationships"] = {"a": dict(_EDGE), "b": dict(_EDGE)}
    # seat-shaped (bond gate 4): an act is a word on a ladder with an object; b is the object and
    # c a bystander — who re-reads the speaker only because c HOLDS b (the owner's rule, s5: at a
    # stranger's affinity .5 the stake is 0 and a `curt` act on b would move c by nothing)
    actors["c"]["char"]["current"]["relationships"]["b"]["affinity"] = 0.8
    tags = {"dimensions": {"social_violation": 0.25}, "durability": "transient", "target": "b",
            "object": "b", "showed": {"affinity": "curt"}}
    movers = {w for w, _d, _v, _c in floor.bond_moves(actors, ["a", "b", "c"], "a", tags)}
    check("the-speaker-does-not-re-read-themselves", "a" not in movers, sorted(movers))
    check("only-people-present-are-considered",
          movers <= {"b", "c"}, sorted(movers))
    check("b-and-c-consider-it", movers == {"b", "c"}, sorted(movers))


def test_scene_py_DEFINES_none_of_the_names_it_re_exports():
    """The re-export shim can be silently SHADOWED, and nothing would report it.

    `scripts/scene.py` re-exports nine names so the tests that load it by file path keep resolving
    them. A later edit that DEFINES `_urge` there would simply override the re-export line — same
    name, same call sites, a second implementation, and a green suite. That is the duplicate-of-a-
    source-of-truth class CLAUDE.md tabulates seven instances of, every one of which had already
    gone wrong.

    ASSERTED FROM THE AST, not a regex: the first draft used
    `name\s*=\s*(?!_floor\.)`, and a greedy `\s*` backtracks to zero width so the lookahead
    never sees `_floor.` at all — it reported every re-export as a redefinition. A pattern that
    cannot see what it is looking at is the defect this suite exists to catch, arriving in the
    check itself."""
    import ast
    src = io.open(os.path.join(REPO, "scripts", "scene.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    names = {"_salience", "_order_weight", "_urge", "_bond_moves", "_compose_event",
             "_ADDRESSED_BONUS", "_RECENCY_PENALTY", "_INHIBITION", "_FLOOR_THRESHOLD"}
    defined, reexported = set(), set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            defined.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            reexported |= {a.asname or a.name for a in node.names} & names
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in names:
                    # a re-export reads an attribute off the module it came from; anything else
                    # is a second implementation wearing the same name
                    if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
                        reexported.add(t.id)
                    else:
                        defined.add(t.id)
    check("scene.py-defines-none-of-them", not defined, "redefined: %s" % sorted(defined))
    check("and-all-nine-are-actually-re-exported", reexported == names,
          "missing: %s" % sorted(names - reexported))


def test_the_driver_compares_against_the_CONSTANT_not_a_literal():
    """FLOOR_THRESHOLD is calibration, and its VALUE is not asserted anywhere — deliberately.
    Breakage-tested 2026-09-03: changing it from 0.06 to 0.99 fails no test, and it should not,
    because pinning a probe-calibrated number turns every retune into a red suite.

    What IS guarded is the drift Fable named: the threshold lived in `scripts/scene.py` while the
    metric it bounds (`floor.urge`) lived here, and a constant separated from its metric is how the
    two stop meaning the same thing. They are now in one module, and this asserts the driver READS
    it rather than carrying its own copy — the copy being the failure, not the number."""
    src = io.open(os.path.join(REPO, "scripts", "scene.py"), encoding="utf-8").read()
    uses = [l.strip() for l in src.splitlines() if "_FLOOR_THRESHOLD" in l]
    check("the-driver-still-uses-it", len(uses) >= 2, uses)
    literal = [l for l in uses if "0.06" in l and "_floor." not in l]
    check("and-never-against-a-hardcoded-copy", not literal, literal)


def test_next_speaker_returns_a_REASON_not_a_bare_None():
    """Three outcomes, and a None that meant two of them would send the driver back to re-derive
    what this function already knew: nobody else present, versus a field that is present and
    unmoved. The driver reports those differently ("empty" vs "lull")."""
    a, b = _listener("a"), _listener("b")
    actors = {"a": a, "b": b}
    for x in actors.values():
        x["last_spoke"] = 0
    tags = {"dimensions": {"social_violation": 0.9}, "durability": "transient"}

    _n, _u, reason = floor.next_speaker(actors, ["a"], "a", tags, None, None, None, 5)
    check("alone-in-the-room-is-EMPTY", reason == "empty", reason)

    nxt, urges, reason = floor.next_speaker(actors, ["a", "b"], "a", tags, None, None, None, 5)
    check("a-moved-listener-TAKES-the-floor", reason is None and nxt == "b",
          "%r / %r" % (nxt, reason))
    check("and-the-urges-are-returned-for-the-trace", set(urges) == {"b"}, sorted(urges))

    flat = {"dimensions": {"social_violation": 0.0}, "durability": "transient"}
    for x in actors.values():
        x["last_spoke"] = 5                      # just spoke: recency penalty sinks the urge
    _n, _u, reason = floor.next_speaker(actors, ["a", "b"], "a", flat, None, None, None, 5)
    check("an-unmoved-field-is-a-LULL", reason == "lull", reason)

    # A TWO-HANDER DOES NOT LULL ON A DIRECT ADDRESS (2026-09-12). The recency penalty breaks a
    # two-person monopoly in a crowd; in a room of two the other person ALWAYS spoke one beat ago,
    # so on a quiet beat the penalty outweighed being addressed and a generated scene ended on a
    # direct request left unanswered, with the listener at 0.055 against a floor of 0.060.
    nxt, urges, reason = floor.next_speaker(actors, ["a", "b"], "a", flat, None, None, "b", 5)
    check("addressed-in-a-two-hander-answers", reason is None and nxt == "b", "%r / %r" % (nxt, reason))
    c = _listener("c"); c["last_spoke"] = 0; actors3 = dict(actors, c=c)
    nxt3, urges3, _r3 = floor.next_speaker(actors3, ["a", "b", "c"], "a", flat, None, None, "b", 5)
    check("in-a-crowd-the-penalty-still-applies-to-the-one-who-just-spoke",
          urges3["b"][0] < urges["b"][0], "%s vs %s" % (urges3["b"][0], urges["b"][0]))
    both, _s, _d = floor.urge(flat, None, None, _listener(), True, 1, contested=False)
    crowd, _s, _d = floor.urge(flat, None, None, _listener(), True, 1, contested=True)
    check("uncontested-drops-recency-exactly", abs((both - crowd) - floor.RECENCY_PENALTY * (1.0 - 1.0 / 3.0)) < 1e-9, both - crowd)


def test_a_TIE_resolves_to_a_STABLE_winner_not_to_insertion_order():
    """The tie-break was incidental until 2026-09-03: `max(urges, key=...)` returns the FIRST
    maximum in dict-insertion order, which followed the `present` list, so two actors with an
    identical urge resolved by cast order and nothing said so.

    Hard rule 4 makes determinism a contract, and a contract kept by dict ordering is one refactor
    from being false. This asserts the winner is a property of the VALUES — same actors, opposite
    presentation order, same answer — which `max` would not have given."""
    actors = {cid: _listener(cid) for cid in ("zeta", "alpha")}
    for x in actors.values():
        x["last_spoke"] = 0
    tags = {"dimensions": {"social_violation": 0.9}, "durability": "transient"}

    fwd, uf, _r = floor.next_speaker(actors, ["s", "zeta", "alpha"], "s", tags, None, None, None, 5)
    rev, ur, _r = floor.next_speaker(actors, ["s", "alpha", "zeta"], "s", tags, None, None, None, 5)
    check("the-two-are-genuinely-TIED", abs(uf["zeta"][0] - uf["alpha"][0]) < 1e-12,
          "%r vs %r" % (uf["zeta"][0], uf["alpha"][0]))
    check("same-winner-either-way", fwd == rev, "%r vs %r" % (fwd, rev))
    check("and-it-is-the-lexically-first", fwd == "alpha", fwd)
    check("leader-agrees-with-next_speaker", floor.leader(uf) == fwd,
          "%r vs %r" % (floor.leader(uf), fwd))



def test_landed_prunes_only_the_salience_term():
    """gate lands-on-to-floor (2026-09-19): `landed` PRUNES `urge`'s salience term rather than
    adding a flat bonus -- `False` zeroes it (both in the returned urge and in the salience
    returned for display), `True` and `None` leave today's arithmetic untouched."""
    tags = {"dimensions": {"social_violation": 1.0}, "durability": "transient"}
    lis = _listener("b")
    full = floor.urge(tags, None, None, lis, False, 99)
    pruned = floor.urge(tags, None, None, lis, False, 99, landed=False)
    check("landed-False-drops-only-the-salience-term",
          abs(pruned[0] - (full[0] - full[1])) < 1e-9 and pruned[1] == 0.0 and pruned[2] == full[2],
          "full=%r pruned=%r" % (full, pruned))

    true_case = floor.urge(tags, None, None, lis, False, 99, landed=True)
    none_case = floor.urge(tags, None, None, lis, False, 99, landed=None)
    check("landed-True-and-None-keep-todays-value",
          true_case == full and none_case == full,
          "full=%r true=%r none=%r" % (full, true_case, none_case))


def test_next_speaker_prunes_via_lands_on():
    """gate lands-on-to-floor (2026-09-19): `next_speaker`'s `lands_on` propagates `landed` per
    listener -- a listener the seat did not list loses its salience term and, where salience was
    the thing keeping it ahead, loses the floor."""
    tags = {"dimensions": {"social_violation": 1.0}, "durability": "transient"}
    a, b, c = _listener("a"), _listener("b"), _listener("c")
    for x in (a, b, c):
        x["last_spoke"] = 0
    actors = {"a": a, "b": b, "c": c}

    # TWO OTHERWISE-IDENTICAL LISTENERS: b and c share one profile and one starting affect, so
    # without lands_on they would be a genuine tie (broken lexically, "b" before "c" -- the SAME
    # winner this scenario produces, which is why the second scenario below is the one that
    # actually falsifies "next_speaker ignores lands_on"). What lands_on=["b"] changes here, and
    # what this checks, is that c's OWN salience is pruned to 0 rather than merely losing a tie.
    nxt, urges, reason = floor.next_speaker(actors, ["a", "b", "c"], "a", tags, None, None, None, 5,
                                            lands_on=["b"])
    check("next_speaker-prunes-the-unreached-listener",
          reason is None and nxt == "b" and urges["c"][1] == 0.0 and urges["b"][1] > 0.0,
          "nxt=%r urges=%r" % (nxt, urges))

    # C WOULD HAVE WON ON SALIENCE: b starts at every path's ceiling (little room for the
    # counterfactual appraise to move it -> low salience), c starts at the neutral 0.5 the other
    # fixtures use (a lot of room -> high salience) -- real numbers, not asserted ones: sal(c)=0.44
    # vs sal(b)=0.075, measured directly below. Everything else about b and c is identical, so
    # without lands_on the higher-salience listener (c) wins; pruning c's salience with
    # lands_on=["b"] flips the floor to b, which is the property this gate exists to add.
    b2 = _listener("b", affect={p: 1.0 for p in PATHS})
    c2 = _listener("c", affect={p: 0.5 for p in PATHS})
    b2["last_spoke"] = c2["last_spoke"] = 0
    actors2 = {"a": a, "b": b2, "c": c2}
    unpruned, uu, _r = floor.next_speaker(actors2, ["a", "b", "c"], "a", tags, None, None, None, 5,
                                          lands_on=None)
    check("c-would-have-won-on-salience-before-pruning", unpruned == "c" and uu["c"][1] > uu["b"][1],
          "nxt=%r urges=%r" % (unpruned, uu))
    pruned_nxt, up, _r = floor.next_speaker(actors2, ["a", "b", "c"], "a", tags, None, None, None, 5,
                                            lands_on=["b"])
    check("next_speaker-prunes-the-unreached-listener",
          pruned_nxt == "b" and up["c"][1] == 0.0,
          "nxt=%r urges=%r (unpruned was %r)" % (pruned_nxt, up, uu))

    # THE PERCEPT SPELLING: the seat writes ids the way the prompt showed them, not the bare id --
    # `norm_id` is what already lets `addressed` match "entity.b"/"B"/"b" alike, and lands_on gets
    # the same treatment. b's salience-for-display must stay UNPRUNED (equal across all three
    # spellings) to prove each one resolved to the same listener.
    sal_by_spelling = {}
    for spelling in (["b"], ["entity.b"], ["B"]):
        _n, u, _r = floor.next_speaker(actors2, ["a", "b", "c"], "a", tags, None, None, None, 5,
                                       lands_on=spelling)
        sal_by_spelling[spelling[0]] = u["b"][1]
    check("lands_on-matches-the-percept-spelling",
          len(set(sal_by_spelling.values())) == 1 and sal_by_spelling["b"] > 0.0,
          sal_by_spelling)

    # NONE REPRODUCES TODAY'S CHOICE, on the tie fixture `test_a_TIE_resolves...` already uses --
    # lands_on=None must be indistinguishable from not passing it at all.
    za = {cid: _listener(cid) for cid in ("zeta", "alpha")}
    for x in za.values():
        x["last_spoke"] = 0
    tags2 = {"dimensions": {"social_violation": 0.9}, "durability": "transient"}
    with_none = floor.next_speaker(za, ["s", "zeta", "alpha"], "s", tags2, None, None, None, 5,
                                   lands_on=None)
    without_kwarg = floor.next_speaker(za, ["s", "zeta", "alpha"], "s", tags2, None, None, None, 5)
    check("lands_on-None-reproduces-todays-choice", with_none == without_kwarg,
          "%r vs %r" % (with_none, without_kwarg))

def main():
    print("test_floor.py — the turn-taking economy\n")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print("\n%s" % ("test_floor: OK (the floor economy computes what it says it computes)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
