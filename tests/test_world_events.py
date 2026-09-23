"""test_world_events.py — the world types, checked against the fold that actually consumes them.

The rubric is only worth anything if it describes `ledger._project`. Every assertion here derives
its expectation from the code rather than restating it, because a hand-copied list of world types
is exactly the duplicate-source-of-truth this repo has been burned by seven times (CLAUDE.md).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.world_events import (TYPES, WorldEventError, field_of,  # noqa: E402
                                     required_keys, rubric, validate_payload, _WORLD)


def _project_source():
    """`_project`'s body PLUS every engine module it delegates to, found by reading its own imports.

    A branch may hand its body to a module — `tension` and `threaten` hand theirs to `tensions.py`,
    because the arithmetic is the world-appraisal chassis and does not belong in the ledger. The
    payload keys are then read THERE, and a derivation that stopped at this function would report
    a declared key as unread and be wrong. So the delegation is followed rather than the assertion
    weakened: add a delegate and this finds it, because it reads the `from . import X` lines inside
    the function instead of a list someone maintains.
    """
    # THE FOLD MOVED to `src/engine/fold.py` on 2026-09-03 (ledger.py was at 499 of its 500-line
    # bound and had blocked three correct changes). This derivation reads the branch table out of
    # `_project`'s SOURCE, so it had to move with it — left pointing at ledger.py it found no
    # branches at all and reported every world type as never-folded. It went RED, which is the safe
    # direction; a derivation that goes GREEN against a stale copy is the one that costs.
    src = open("src/engine/fold.py", encoding="utf-8").read()
    i = src.index("def project")
    body = src[i:src.index("def events_between")]
    for mod in sorted(set(re.findall(r"from \.\s+import\s+(\w+)", body))):
        path = os.path.join("src", "engine", "%s.py" % mod)
        if os.path.exists(path):
            body += open(path, encoding="utf-8").read()
    return body


def _folded_types():
    """The types `_project` actually branches on — DERIVED, never listed here."""
    body = _project_source()
    found = set(re.findall(r'etype == "([\w-]+)"', body))
    for m in re.finditer(r'etype in \(([^)]*)\)', body):
        found |= {x.strip().strip('"\'') for x in m.group(1).split(",")}
    return found


def test_every_type_in_the_rubric_is_one_the_fold_actually_handles():
    """A definition for a type that folds to nothing is a lie with a docstring."""
    unhandled = sorted(set(TYPES) - _folded_types())
    assert not unhandled, (
        "the rubric defines %s, which ledger._project never branches on — either the fold gained "
        "a gap or the rubric invented a type" % unhandled)


def test_every_folded_type_has_a_definition():
    missing = sorted(_folded_types() - set(TYPES))
    assert not missing, "ledger._project folds %s and the rubric defines no meaning for it" % missing


def test_declared_world_effects_that_never_fold_are_REPORTED_not_forgotten():
    """DERIVED DEBT. Every type declaring a world_map must have a fold branch, or it claims an
    effect it does not have.

    This carried `threaten` for three months. The note here used to say a branch "needs a tension
    identity the payload does not carry" — that was the wrong reading, and the docs had already
    answered it: `world-dynamics.md` says an act raises THE RELEVANT tension, "computed, never
    guessed", so the identity is not carried, it is computed from standing interests. `threaten`
    folds as of 2026-09-02 and the expected debt is now EMPTY.

    Kept as a guard rather than deleted: the next type that declares a world_map without a branch
    lands here, derived from the two tables, before anyone has to notice by hand."""
    from src.engine.consolidation import CATALOG

    declared = {t for t, r in CATALOG.items() if r.get("world_map") not in (None, "none")}
    debt = sorted(declared - _folded_types())
    for t in debt:
        print("       DEBT  %-12s declares world_map=%r and _project has no branch"
              % (t, CATALOG[t]["world_map"]))
    assert debt == [], (
        "the declared-but-never-folded set changed: %s. If a type was fixed, drop it from this "
        "expectation; if a new one appeared, it is a silent no-op and needs the same scrutiny" % debt)


def test_each_type_names_the_snapshot_field_the_fold_moves():
    body = _project_source()
    for t in TYPES:
        field = field_of(t)
        head = field.split("[")[0]
        assert head in body, (
            "%r claims to move %r but %r never appears in _project" % (t, field, head))


def test_required_keys_are_the_ones_project_actually_reads():
    body = _project_source()
    for t in TYPES:
        for k in required_keys(t):
            assert 'payload.get("%s")' % k in body or '"%s" in payload' % k in body, (
                "%r declares payload key %r but _project never reads it" % (t, k))


def test_a_payload_missing_a_key_the_fold_needs_FAILS_LOUD():
    """The silent shape this guards: _project's branch simply does not fire on a missing key, so
    the event lands in the append-only log claiming a world effect it never had."""
    try:
        validate_payload("move", {})
    except WorldEventError as e:
        assert "to" in str(e) and "location" in str(e), (
            "the error must name the missing key AND the field it would have moved; got %r" % e)
    else:
        raise AssertionError("a move with no destination must not validate")


def test_a_complete_payload_validates():
    assert validate_payload("move", {"to": "the-north-road"}) is True
    assert validate_payload("reveal", {"fact": "the-debt", "to": ["ren"]}) is True
    assert validate_payload("betray", {}) is True, "betray reads actor/target, not payload keys"


def test_an_unknown_type_is_refused_by_name():
    for fn in (field_of, required_keys):
        try:
            fn("gossip")
        except WorldEventError as e:
            assert "gossip" in str(e)
        else:
            raise AssertionError("%s must refuse a non-world type" % fn.__name__)


def test_every_type_carries_a_boundary_against_the_thing_it_is_NOT():
    """The rubric's whole job. 'A move is when someone moves' is not a test a reader can run."""
    for t in TYPES:
        _, _, meaning, boundary = _WORLD[t]
        assert meaning.strip(), "%r has no meaning" % t
        assert boundary.startswith("vs "), (
            "%r must name what it is being told apart FROM; got %r" % (t, boundary))


def test_the_rubric_leads_with_the_DECIDABLE_rule():
    """The reader notices; the engine decides whether it counted. If the rule goes missing the
    rubric becomes seven judgement calls again."""
    text = rubric()
    assert "IFF folding it would change the world snapshot" in text
    for t in TYPES:
        assert t in text, "%r missing from the rendered rubric" % t


def test_folding_one_well_formed_event_of_each_type_CHANGES_the_snapshot():
    """THE DECIDABILITY GUARD, run against the real fold. If a type cannot move the snapshot with
    a payload built from its own declared keys, the rubric is promising something the fold does
    not deliver — which is precisely the threaten defect, caught mechanically."""
    import json
    from src.engine.ledger import Ledger

    sample = {
        "move":          ({"to": "the-north-road"}, "a", None),
        "harm":          ({"terminal": True}, "a", "b"),
        "reveal":        ({"fact": "the-debt", "to": ["b"]}, "a", None),
        "seize":         ({"asset": "the-mill"}, "a", None),
        "destroy-asset": ({"asset": "the-mill"}, "a", None),
        "betray":        ({}, "a", "b"),
        "bond":          ({}, "a", "b"),
        "tension":       ({"id": "the-border", "temperature": 0.7, "factions": ["x"],
                           "watches": {"parties": ["a"]}, "interests": {"threat": 0.5}}, "a", None),
        # THE FIRST CONDITIONAL TYPE. `threaten` names no tension — it prices itself against every
        # live one — so on an EMPTY register it correctly changes nothing, and that is the scope
        # fence working, not a defect. The invariant therefore restates: a type must move the
        # snapshot when folded onto a world prepared with ITS OWN declared preconditions. For
        # `threaten` that precondition is a tension that watches the act.
        "threaten":      ({"dimensions": {"threat": 0.78}}, "a", "b"),
    }
    preconditions = {
        "threaten": {"tensions": {"the-border": {
            "temperature": 0.1, "factions": [], "cooling": "typical", "last_heated_at": 0,
            "watches": {"parties": ["a", "b"]}, "interests": {"threat": 0.5}}}},
    }
    assert set(sample) == set(TYPES), "sample set drifted from TYPES: %s" % sorted(set(TYPES) ^ set(sample))

    for t in TYPES:
        payload, actor, target = sample[t]
        validate_payload(t, payload)
        before = {"agents": {}, "information": {}, "holdings": {}, "relationships": {}, "tensions": {}}
        before.update(json.loads(json.dumps(preconditions.get(t, {}))))
        ev = {"type": t, "payload": json.dumps(payload), "actor": actor, "target": target,
              "location": None, "effective_at": 1}
        after = Ledger._project(json.loads(json.dumps(before)), ev)
        assert after != before, (
            "%r folded to NO CHANGE with a payload built from its own required_keys — the rubric "
            "promises it moves %s and the fold disagrees" % (t, field_of(t)))

    # ...and the OTHER half of a conditional type: with no precondition, it must fold to nothing
    # rather than inventing somewhere to land.
    bare = {"agents": {}, "information": {}, "holdings": {}, "relationships": {}, "tensions": {}}
    after = Ledger._project(json.loads(json.dumps(bare)),
                            {"type": "threaten", "payload": json.dumps({"dimensions": {"threat": 0.78}}),
                             "actor": "a", "target": "b", "location": None, "effective_at": 1})
    assert after == bare, (
        "threaten moved a world with no tension watching it — the scope fence is what keeps "
        "'only the levered is written' true, and it just failed open")


def test_an_EMPTY_required_key_is_refused_for_every_type():
    """PRESENCE IS NOT VALUE, and the gap between them bricked a run.

    Measured 2026-09-02: a `reveal` carrying `fact: ""` passed `validate_payload` (which checked
    only that the key existed), folded to `information[""]`, and entered the APPEND-ONLY log. From
    that turn on, `persist_snapshot` and `resume` both raised on the schema's `key <> ''` and the
    run could never be parked or resumed again — and no correction event removes an information key.

    DERIVED over every type and every required key, so a type added later is covered without
    anyone remembering to come back here."""
    for t in TYPES:
        for k in required_keys(t):
            payload = {key: (["someone"] if key == "to" and t == "reveal" else "x")
                       for key in required_keys(t)}
            payload[k] = [""] if isinstance(payload[k], list) else ""
            try:
                validate_payload(t, payload)
            except WorldEventError as e:
                assert e.code == "WORLD_EVENT_PAYLOAD_VALUE_EMPTY", (
                    "%s/%s refused with %r, not the emptiness code" % (t, k, e.code))
                continue
            raise AssertionError(
                "%r accepted an EMPTY %r. That value becomes %s, and an identity nothing can name "
                "cannot be cited, resolved, or corrected out of an append-only log."
                % (t, k, field_of(t)))


def test_a_present_and_NON_empty_payload_still_passes():
    """The control. A guard that refuses everything would pass the test above and break the book."""
    validate_payload("reveal", {"fact": "the levy was doubled", "to": ["edda"]})
    validate_payload("seize", {"asset": "the mill"})
    validate_payload("harm", {"terminal": False})       # a bool is not an empty string
    validate_payload("threaten", {"dimensions": {}})    # an empty MAP is not an empty identity


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("  PASS  %s" % name)
            except Exception as e:                       # noqa: BLE001 — a harness reports, never raises
                fails += 1
                print("  FAIL  %s: %s" % (name, e))
    print("%s" % ("ALL PASS" if not fails else "%d FAILED" % fails))
    sys.exit(1 if fails else 0)
