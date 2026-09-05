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
from src.engine.records import PRIMARIES                           # noqa: E402
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


def _listener(cid="b", extraversion=0.5, standing=0.5):
    ch = _person(cid, cid.upper(), extraversion, standing)
    return {"id": cid, "char": ch, "affect": {p: 0.5 for p in PRIMARIES},
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
    tags = {"dimensions": {"social_violation": 0.25}, "durability": "transient", "target": "b"}
    movers = {w for w, _d, _v in floor.bond_moves(actors, ["a", "b", "c"], "a", tags)}
    check("the-speaker-does-not-re-read-themselves", "a" not in movers, sorted(movers))
    check("only-people-present-are-considered",
          movers <= {"b", "c"}, sorted(movers))


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
