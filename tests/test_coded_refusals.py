#!/usr/bin/env python3
"""test_coded_refusals.py — every code in these families, EXECUTED, with its table checked against
the registry.

WHY THIS EXISTS ALONGSIDE THE SCANS. `tests/test_errors.py` proves by PARSING that no engine module
is half-converted and that every registered code is raised somewhere. Neither runs a line of the
modules. A code can be registered, spelled correctly at the raise, and wired to a condition that
never fires — or that fires for a DIFFERENT input than the one it names — and both scans stay green.
Executing one case per code is the only thing that catches that.

THE TABLES ARE CHECKED AGAINST THE REGISTRY, not the other way round. A new code in one of these
families with no executing case here FAILS. That is the direction a hand-kept table gets wrong, and
it is the direction that fails SILENT if nobody looks — the shape CLAUDE.md tabulates seven prior
instances of.

CO-LOCATED ON PURPOSE. One file holds the convention for four modules, so the next family is written
by copying a pattern that is visible in one place rather than reconstructed from four.

Script-style, stdlib only, exit 0 = all pass.
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import (bonds, books, citation, codes, levers, narration_modes,  # noqa: E402
                        records, toward, vault)
from src.engine.citation import CitationError                     # noqa: E402
from src.engine.records import PRIMARIES, RecordError             # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _row(**over):
    """A VALID catalog row. Every case below breaks exactly one thing about it."""
    r = {"lever": "SEEKING", "op": "x", "magnitude": 1.0}
    r.update(over)
    return r


def _affect():
    return {p: 0.5 for p in PRIMARIES}


LEVER_CASES = {
    "LEVER_ROW_NOT_A_DICT":         lambda: levers.effective(_affect(), ["not a row"]),
    "LEVER_UNKNOWN":                lambda: levers.effective(_affect(), [_row(lever="VIBES")]),
    "LEVER_OP_UNKNOWN":             lambda: levers.effective(_affect(), [_row(op="?")]),
    "LEVER_MAGNITUDE_NOT_NUMERIC":  lambda: levers.effective(_affect(), [_row(magnitude="big")]),
    "LEVER_MULTIPLIER_NEGATIVE":    lambda: levers.effective(_affect(), [_row(op="x", magnitude=-1.0)]),
    "LEVER_CURRENT_NOT_A_DICT":     lambda: levers.effective("not affect", []),
    "LEVER_CURRENT_MISSING_PRIMARIES": lambda: levers.effective({"SEEKING": 0.5}, []),
    "LEVER_CATALOG_NOT_A_LIST":     lambda: levers.active_rows("not a catalog", {}),
    "LEVER_WHEN_NOT_A_DICT":        lambda: levers.active_rows([_row(when="nope")], {}),
    # the clause NAMES are read off levers.py itself: `percept`, `present_edge`, `target_edge`.
    # A first draft guessed `percept_any` and `edge`, which are silently ignored — the case passed
    # nothing to the guard and reported "ACCEPTED" for a guard that was never reached.
    "LEVER_WHEN_PERCEPT_NOT_A_LIST": lambda: levers.active_rows(
        [_row(when={"percept": "not a list"})], {}),
    "LEVER_WHEN_EDGE_REQ_NOT_A_DICT": lambda: levers.active_rows(
        [_row(when={"present_edge": "not a dict"})], {}),
    "LEVER_EDGE_CLAUSE_UNKNOWN":    lambda: levers.active_rows(
        [_row(when={"present_edge": {"id": "t", "vibes": 0.5}})],
        {"edges": {"t": {"trust": 0.5}}}),
    "LEVER_WOUNDS_NOT_A_LIST":      lambda: levers.replay_wound_deltas("not a list", []),
    "LEVER_WOUND_INTENSITY_NOT_NUMERIC": lambda: levers.scale_to_wounds(
        [_row(wound="w")], [{"id": "w", "intensity": "a lot"}]),
    "LEVER_WOUND_AUTHORED_INTENSITY_ZERO": lambda: levers.scale_to_wounds(
        [_row(wound="w")], [{"id": "w", "intensity": 0.0}]),
}

CITATION_CASES = {
    "CITATION_TOKEN_EMPTY":          lambda: citation.parse("   "),
    "CITATION_TOKEN_SHAPE":          lambda: citation.parse("no-colon-here"),
    "CITATION_NAMESPACE_UNKNOWN":    lambda: citation.parse("vibes:1"),
    "CITATION_ENVELOPE_NOT_A_DICT":  lambda: citation.verify_envelope("not an envelope", None, "r1"),
    "CITATION_ENVELOPE_KIND_UNKNOWN": lambda: citation.verify_envelope({"kind": "vibes"}, None, "r1"),
    # EVERY envelope case must carry a VALID kind, because the kind check fires first. A first
    # draft omitted it and five cases all reported CITATION_ENVELOPE_KIND_UNKNOWN — five tests
    # green on the wrong guard is exactly what an executing table is supposed to catch.
    "CITATION_ENVELOPE_CLAIMS_TYPE": lambda: citation.verify_envelope(
        {"kind": "ANSWER", "claims": "not a list"}, None, "r1"),
    "CITATION_ENVELOPE_UNKNOWNS_TYPE": lambda: citation.verify_envelope(
        {"kind": "ANSWER", "claims": [], "unknowns": "not a list"}, None, "r1"),
    "CITATION_CLAIM_NOT_A_DICT":     lambda: citation.verify_envelope(
        {"kind": "ANSWER", "claims": ["not a claim"]}, None, "r1"),
    "CITATION_CLAIM_MODE_UNKNOWN":   lambda: citation.verify_envelope(
        {"kind": "ANSWER", "claims": [{"mode": "vibes"}]}, None, "r1"),
    "CITATION_CLAIM_TOKENS_TYPE":    lambda: citation.verify_envelope(
        # the field is `cite` for mode="cited" and `from` for "derived" — read off citation.py,
        # not guessed. A `tokens` key is simply ignored, so the guard was never reached.
        {"kind": "ANSWER", "claims": [{"mode": "cited", "cite": "not a list"}]}, None, "r1"),
    "CITATION_ARG_NOT_INT":          lambda: citation.resolve_one(None, "r1", "turn:not-a-number"),
    "CITATION_ARITY_MISMATCH":       lambda: citation.resolve_one(None, "r1", "entity:a:b"),
}

BONDS_CASES = {
    "BONDS_ACT_NOT_A_DICT":          lambda: bonds.witnessed("not an act", {}, {}),
    "BONDS_SKILLS_INVALID":          lambda: bonds.witnessed({}, "not skills", {}),
    "BONDS_MODEL_NOT_A_DICT":        lambda: bonds.observe({}, {}, "not a model", None, None, None),
    "BONDS_DELTAS_NOT_A_DICT":       lambda: bonds.apply_deltas({}, "not deltas"),
    "BONDS_EDGE_AXIS_UNKNOWN":       lambda: bonds.apply_deltas({}, {"vibes": 0.1}),
    "BONDS_RELATIONSHIPS_NOT_A_DICT": lambda: bonds.replay("not relationships", []),
    "BONDS_LOG_AXIS_UNKNOWN":        lambda: bonds.replay({}, [{"perceiver": "a", "target": "b",
                                                                "axis": "vibes", "delta": 0.1}]),
    "BONDS_DRIFT_ELAPSED_NOT_NUMERIC": lambda: bonds.drift({}, {}, "a while"),
}

TOWARD_CASES = {
    "TOWARD_DIMS_NOT_A_DICT":        lambda: toward.observe("not dims", 1.0),
    "TOWARD_CONNECTION_NOT_NUMERIC": lambda: toward.observe({}, "close"),
    "TOWARD_CHAR_NOT_A_DICT":        lambda: toward.replay("not a char", []),
    "TOWARD_ELAPSED_NOT_NUMERIC":    lambda: toward.erode({}, "a while", None),
}

def _event(**over):
    """A VALID Event. Every case below breaks exactly one thing about it."""
    return records.Event(**dict({"type": "mundane", "payload": {}}, **over))


def _commit(**over):
    """A VALID TurnCommit."""
    base = {"run_id": "r1", "turn": 0, "actor": "maren", "thought": "t", "action": "a",
            "tags": {"type": "mundane"}, "affect": {p: 0.5 for p in PRIMARIES}, "events": []}
    return records.TurnCommit(**dict(base, **over))


def _rel(**over):
    base = {"perceiver": "a", "target": "b", "axis": "trust", "delta": 0.1}
    return records.RelationshipDelta(**dict(base, **over))


def _wound(**over):
    base = {"char_id": "a", "wound_id": "w", "delta": 0.1, "kind": sorted(records.WOUND_DELTA_KINDS)[0]}
    return records.WoundDelta(**dict(base, **over))


def _toward(**over):
    base = {"perceiver": "a", "target": "b", "primary": sorted(PRIMARIES)[0], "delta": 0.1}
    return records.TowardDelta(**dict(base, **over))


# THE SURFACE A MALFORMED COMMIT MEETS. It had no handles at all until 2026-09-02 and the
# conversion audit could not see it — `_require(cond, msg)` looked like an already-coded doorway.
# Several codes are shared across record types deliberately: a code names the CONDITION, and the
# three tiers' `delta` fields fail identically.
RECORD_CASES = {
    "RECORD_EVENT_TYPE_EMPTY":       lambda: _event(type="").validate(),
    "RECORD_EVENT_PAYLOAD_TYPE":     lambda: _event(payload="nope").validate(),
    "RECORD_EVENT_VISIBILITY_UNKNOWN": lambda: _event(visibility="secret").validate(),
    "RECORD_EVENT_CAUSED_AT_INVALID": lambda: _event(caused_at=-1).validate(),
    "RECORD_EVENT_EFFECTIVE_AT_INVALID": lambda: _event(caused_at=0, effective_at="soon").validate(),
    "RECORD_EVENT_EFFECTIVE_AT_UNANCHORED": lambda: _event(effective_at=2).validate(),
    "RECORD_EVENT_EFFECT_BEFORE_CAUSE": lambda: _event(caused_at=5, effective_at=1).validate(),
    "RECORD_PERCEIVER_EMPTY":        lambda: _rel(perceiver="").validate(),
    "RECORD_TARGET_EMPTY":           lambda: _rel(target="").validate(),
    "RECORD_AXIS_UNKNOWN":           lambda: _rel(axis="vibes").validate(),
    "RECORD_DELTA_RANGE":            lambda: _rel(delta=9.0).validate(),
    "RECORD_ORDER_UNKNOWN":          lambda: _rel(order="third").validate(),
    "RECORD_CHAR_ID_EMPTY":          lambda: _wound(char_id="").validate(),
    "RECORD_WOUND_ID_EMPTY":         lambda: _wound(wound_id="").validate(),
    "RECORD_WOUND_KIND_UNKNOWN":     lambda: _wound(kind="vibes").validate(),
    "RECORD_PRIMARY_UNKNOWN":        lambda: _toward(primary="VIBES").validate(),
    "RECORD_SOURCE_TYPE":            lambda: _toward(source=7).validate(),
    "RECORD_RUN_ID_EMPTY":           lambda: _commit(run_id="").validate(),
    "RECORD_TURN_INVALID":           lambda: _commit(turn=-1).validate(),
    "RECORD_ACTOR_EMPTY":            lambda: _commit(actor="").validate(),
    "RECORD_FIELD_TYPE":             lambda: _commit(thought=7).validate(),
    "RECORD_AFFECT_MISSING_PRIMARIES": lambda: _commit(
        affect={p: 0.5 for p in list(PRIMARIES)[:-1]}).validate(),
    "RECORD_AFFECT_UNKNOWN_KEYS":    lambda: _commit(
        affect=dict({p: 0.5 for p in PRIMARIES}, VIBES=0.5)).validate(),
    "RECORD_AFFECT_VALUE_RANGE":     lambda: _commit(
        affect=dict({p: 0.5 for p in PRIMARIES}, **{sorted(PRIMARIES)[0]: 9.0})).validate(),
    "RECORD_LIST_ITEM_TYPE":         lambda: _commit(events=["not an Event"]).validate(),
}


# THE FOUR RULES THAT GAINED AN OWNER. Each was enforced inside a script, in the script's own
# words, for a condition an engine module decides — a second spelling that can drift from the first,
# and one already had: `scene.py` read its narration vocabulary from `narrate.py`, a sibling SCRIPT,
# while `narration_modes` sat unused with its two registered codes never raised.
OWNED_CASES = {
    "NARRATION_POV_NOT_PRESENT": lambda: narration_modes.require_witness("nobody", ["maren"]),
    "VAULT_CHARACTER_UNKNOWN":   lambda: vault.character_or_raise({"maren": {}}, "nobody"),
    "BOOK_FIXTURE_NOT_FOUND":    lambda: books.fixture_path(REPO, "world", "no-such-fixture",
                                                            ("", "-slice")),
    "BOOK_DB_MISSING":           lambda: books.db_or_raise(os.path.join(REPO, "no-such.db")),
}


#: family prefix -> (case table, the exception class its module raises)
FAMILIES = {
    "LEVER_":    (LEVER_CASES, RecordError),
    "CITATION_": (CITATION_CASES, CitationError),
    "BONDS_":    (BONDS_CASES, RecordError),
    "TOWARD_":   (TOWARD_CASES, RecordError),
    "RECORD_":   (RECORD_CASES, RecordError),
}

#: codes that live in an EXISTING family but are raised by a helper a script delegates to.
#: Checked by execution only — their family's registry check belongs to that family.
OWNED_CLASSES = {"NARRATION_POV_NOT_PRESENT": narration_modes.NarrationError,
                 "VAULT_CHARACTER_UNKNOWN": vault.VaultError,
                 "BOOK_FIXTURE_NOT_FOUND": books.BookError,
                 "BOOK_DB_MISSING": books.BookError}


def test_every_case_refuses_with_its_OWN_code():
    for prefix, (cases, cls) in sorted(FAMILIES.items()):
        for code, call in sorted(cases.items()):
            try:
                call()
                check("%s refuses" % code, False, "the malformed input was ACCEPTED")
            except cls as e:
                check("%s refuses" % code, e.code == code, "got %r" % e.code)
            except Exception as e:                                # noqa: BLE001
                check("%s refuses" % code, False,
                      "raised %s, not a coded %s: %s" % (type(e).__name__, cls.__name__,
                                                         str(e)[:70]))


def test_the_DELEGATED_rules_fire_from_their_OWNER():
    """A script that restates an engine rule is a duplicate before it is a refusal.

    Each of these was enforced inside a script; each now has one owner that raises a registered
    code, and the script passes `str(e)` through. Executed here so the owner is proven to refuse —
    `tests/test_driver_main.py` proves the script still surfaces it."""
    for code, call in sorted(OWNED_CASES.items()):
        cls = OWNED_CLASSES[code]
        try:
            call()
            check("%s fires" % code, False, "the malformed input was ACCEPTED")
        except cls as e:
            check("%s fires" % code, e.code == code, "got %r" % e.code)
        except Exception as e:                                # noqa: BLE001
            check("%s fires" % code, False,
                  "raised %s, not a coded %s: %s" % (type(e).__name__, cls.__name__, str(e)[:60]))
    for code in OWNED_CASES:
        check("%s is registered" % code, codes.is_registered(code))


def test_each_TABLE_is_checked_against_the_REGISTRY():
    """The direction that fails silent: a new code with no executing case.

    Derived from `codes.CODES`, so adding a refusal to one of these modules without exercising it
    here is red — a hand-kept table is only safe when something else decides what belongs in it."""
    for prefix, (cases, _cls) in sorted(FAMILIES.items()):
        registered = {c for c in codes.CODES if c.startswith(prefix)}
        check("%s* every registered code has a case" % prefix,
              not (registered - set(cases)), str(sorted(registered - set(cases))))
        check("%s* no case names an unregistered code" % prefix,
              not (set(cases) - registered), str(sorted(set(cases) - registered)))


def test_the_families_are_NOT_merged_where_the_condition_rhymes():
    """A code's prefix names the module that OWNS the refusal, not one that shares its shape.

    Four separate `*_ELAPSED_NOT_NUMERIC` codes exist across CLOCK, WOUND, ARC, BONDS and TOWARD and
    that is deliberate: the tiers age against different units and an operator debugging a bad drift
    span needs to know WHICH tier refused. Asserted so a later tidy-up cannot quietly merge them."""
    elapsed = sorted(c for c in codes.CODES if c.endswith("_ELAPSED_NOT_NUMERIC"))
    check("the-per-tier-elapsed-codes-stay-separate", len(elapsed) >= 3,
          "only %s — the tiers were merged into one handle" % elapsed)


def main():
    print("test_coded_refusals.py — every code in four families, executed\n")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        try:
            fn()
        except Exception as e:                                    # noqa: BLE001
            FAILS.append("%s RAISED %s: %s" % (fn.__name__, type(e).__name__, e))
            print("  FAIL  %s RAISED %s: %s" % (fn.__name__, type(e).__name__, str(e)[:110]))
    print("\n%s" % ("test_coded_refusals: OK (every code fires, and every table is registry-checked)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
