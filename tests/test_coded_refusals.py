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

from src.engine import (bonds, bond_rest, books, citation, codes, levers, narration_modes,  # noqa: E402
                        records, toward, vault)
from src.engine.citation import CitationError                     # noqa: E402
from src.engine.records import PATHS, RecordError, RestDeclared, AttachmentDeclared  # noqa: E402
from src.engine import attachments as _attachments                 # noqa: E402  (gate 5)
from src.engine import systems as _systems                         # noqa: E402  (gate systems-registry)
from src.engine import condition as _condition                     # noqa: E402  (gate condition-flow)
from src.engine import body as _body                               # noqa: E402  (gate body-exertion)
from src.engine import injuries as _injuries                       # noqa: E402  (gate injuries)
from src.engine import guards as _guards, records as _records       # noqa: E402  (gate record-guards)

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _row(**over):
    """A VALID catalog row. Every case below breaks exactly one thing about it."""
    r = {"lever": "STIRRING", "op": "x", "magnitude": 1.0}
    r.update(over)
    return r


def _affect():
    return {p: 0.5 for p in PATHS}


LEVER_CASES = {
    "LEVER_ROW_NOT_A_DICT":         lambda: levers.effective(_affect(), ["not a row"]),
    "LEVER_UNKNOWN":                lambda: levers.effective(_affect(), [_row(lever="VIBES")]),
    "LEVER_OP_UNKNOWN":             lambda: levers.effective(_affect(), [_row(op="?")]),
    "LEVER_MAGNITUDE_NOT_NUMERIC":  lambda: levers.effective(_affect(), [_row(magnitude="big")]),
    "LEVER_MULTIPLIER_NEGATIVE":    lambda: levers.effective(_affect(), [_row(op="x", magnitude=-1.0)]),
    "LEVER_CURRENT_NOT_A_DICT":     lambda: levers.effective("not affect", []),
    "LEVER_CURRENT_MISSING_PRIMARIES": lambda: levers.effective({"STIRRING": 0.5}, []),
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
    "BONDS_RELATIONSHIPS_NOT_A_DICT": lambda: bond_rest.rehydrate("not relationships", {}, []),
    "BONDS_LOG_AXIS_UNKNOWN":        lambda: bond_rest.rehydrate({}, {}, [("edge", "a", "vibes", 0.1, "first")]),
    "BONDS_DRIFT_ELAPSED_NOT_NUMERIC": lambda: bond_rest.drift({}, {}, "a while"),
    "BONDS_REST_NOT_A_DICT":         lambda: bond_rest.drift({}, "rest", 1),
    "BONDS_REST_AXIS_MISSING":       lambda: bond_rest.drift({"trust": 0.5}, {}, 1),
    "BONDS_TIMELINE_KIND_UNKNOWN":   lambda: bond_rest.rehydrate({}, {}, [("weather", 1)]),
    "BONDS_HOLD_ROW_UNFOLDED":       lambda: bond_rest.rehydrate({}, {}, [("hold", "loc.mill", 0.85, "+")]),
    "BONDS_STAKE_MISSING":           lambda: bonds.observe({}, {"observations": {"respect": 0.78}, "received": False}, {}),
    "BONDS_RATE_WORD_UNKNOWN":       lambda: bonds.rates_of({"update": {"grant_threshold": "sometimes"}}),
    "BONDS_SHOWED_AXIS_UNKNOWN":     lambda: bonds.observations_from_showed({"loyalty": "loyal"}),
    "BONDS_SHOWED_WORD_UNKNOWN":     lambda: bonds.observations_from_showed({"trust": "very low"}),
}

TOWARD_CASES = {
    "TOWARD_DIMS_NOT_A_DICT":        lambda: toward.observe("not dims", 1.0),
    "TOWARD_CONNECTION_NOT_NUMERIC": lambda: toward.observe({}, "close"),
    "TOWARD_CHAR_NOT_A_DICT":        lambda: toward.replay("not a char", []),
    "TOWARD_ELAPSED_NOT_NUMERIC":    lambda: toward.erode({}, "a while", None),
    "TOWARD_READING_PATH_UNKNOWN":   lambda: toward.observe_readings([type("R", (), {"path": "PLAY", "rung": "x", "about": "cobb"})()], me="ren"),
    "TOWARD_AFFECT_NOT_A_DICT":      lambda: toward.balance("not a mood", {}, {}),
}

def _event(**over):
    """A VALID Event. Every case below breaks exactly one thing about it."""
    return records.Event(**dict({"type": "mundane", "payload": {}}, **over))


def _commit(**over):
    """A VALID TurnCommit."""
    base = {"run_id": "r1", "turn": 0, "actor": "maren", "thought": "t", "action": "a",
            "tags": {"type": "mundane"}, "affect": {p: 0.5 for p in PATHS}, "events": []}
    return records.TurnCommit(**dict(base, **over))


def _rel(**over):
    base = {"perceiver": "a", "target": "b", "axis": "trust", "delta": 0.1}
    return records.RelationshipDelta(**dict(base, **over))


def _wound(**over):
    base = {"char_id": "a", "wound_id": "w", "delta": 0.1, "kind": sorted(records.WOUND_DELTA_KINDS)[0]}
    return records.WoundDelta(**dict(base, **over))


def _toward(**over):
    base = {"perceiver": "a", "target": "b", "primary": sorted(PATHS)[0], "delta": 0.1}
    return records.TowardDelta(**dict(base, **over))


# THE SURFACE A MALFORMED COMMIT MEETS. It had no handles at all until 2026-09-02 and the
# conversion audit could not see it — `_require(cond, msg)` looked like an already-coded doorway.
# Several codes are shared across record types deliberately: a code names the CONDITION, and the
# three tiers' `delta` fields fail identically.
RECORD_CASES = {
    "RECORD_REST_RANGE":             lambda: RestDeclared("a", "b", "trust", 1.5).validate(),
    "RECORD_REST_SOURCE_UNKNOWN":    lambda: RestDeclared("a", "b", "trust", 0.5, source="guess").validate(),
    "RECORD_HOLD_RANGE":             lambda: AttachmentDeclared("a", "loc.mill", 1.5).validate(),
    "RECORD_SIGN_UNKNOWN":           lambda: AttachmentDeclared("a", "loc.mill", 0.5, sign="*").validate(),
    "RECORD_ATTACHMENT_SOURCE_UNKNOWN": lambda: AttachmentDeclared("a", "loc.mill", 0.5, source="speech").validate(),
    # gate record-guards: the committed turn's validation, and a guard the builder cannot read
    "RECORD_VALIDATION_SHAPE":       lambda: _records.TurnCommit(run_id="r", turn=0, actor="maren", thought="", action="",
                                                                 tags={}, affect={p: 0.0 for p in PATHS},
                                                                 validation={"ok": "yes"}).validate(),
    "RECORD_GUARD_KIND_UNKNOWN":     lambda: _guards.refused(("mill", "wheel", "spoked", lambda: None, "X", "-")),
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
        affect={p: 0.5 for p in list(PATHS)[:-1]}).validate(),
    "RECORD_AFFECT_UNKNOWN_KEYS":    lambda: _commit(
        affect=dict({p: 0.5 for p in PATHS}, VIBES=0.5)).validate(),
    "RECORD_AFFECT_VALUE_RANGE":     lambda: _commit(
        affect=dict({p: 0.5 for p in PATHS}, **{sorted(PATHS)[0]: 9.0})).validate(),
    "RECORD_LIST_ITEM_TYPE":         lambda: _commit(events=["not an Event"]).validate(),
    "RECORD_BYSTANDER_IS_ACTOR":     lambda: _commit(
        bystanders={"maren": {"affect": {p: 0.5 for p in PATHS}}}).validate(),
}


# THE FOUR RULES THAT GAINED AN OWNER. Each was enforced inside a script, in the script's own
# words, for a condition an engine module decides — a second spelling that can drift from the first,
# and one already had: `scene.py` read its narration vocabulary from `narrate.py`, a sibling SCRIPT,
# while `narration_modes` sat unused with its two registered codes never raised.
_W = {"locations": [{"id": "mill"}], "people": [{"id": "ash", "groups": ["guild"]}]}
ATTACH_CASES = {
    "ATTACH_WORD_UNKNOWN":        lambda: _attachments.hold_of("fond"),
    "ATTACH_WORLD_NOT_A_DICT":    lambda: _attachments.names_for(["mill"]),
    "ATTACH_BLOCK_NOT_A_DICT":    lambda: _attachments.validate_block(["loc.mill"]),
    "ATTACH_ENTRY_NOT_A_DICT":    lambda: _attachments.validate_block({"loc.mill": 0.85}),
    "ATTACH_KEY_UNPREFIXED":      lambda: _attachments.validate_block({"bel": {"hold": 0.5}}),
    "ATTACH_ENTITY_UNREGISTERED": lambda: _attachments.validate_block({"loc.tower": {"hold": 0.5}}, registered=_attachments.names_for(_W)),
    "ATTACH_HOLD_RANGE":          lambda: _attachments.validate_block({"loc.mill": {"hold": 1.2}}),
    "ATTACH_SIGN_UNKNOWN":        lambda: _attachments.validate_block({"loc.mill": {"hold": 0.5, "sign": "*"}}),
    "ATTACH_LIFE_CAP":            lambda: _attachments.validate_block({"loc.a": {"hold": 0.85}, "loc.b": {"hold": 0.85}, "loc.c": {"hold": 0.9}}),
    "ATTACH_HOLD_UNWORDED":       lambda: _attachments.word_of(0.0),
}
# WHICH SYSTEMS A BOOK RUNS (gate systems-registry, 2026-09-22): a declaration the engine cannot honour
# refuses before the first beat - a typo must not switch nothing off and say nothing.
SYSTEMS_CASES = {
    "SYSTEMS_NOT_A_MAP":      lambda: _systems.for_book({"systems": ["wounds"]}),
    "SYSTEMS_UNKNOWN":        lambda: _systems.for_book({"systems": {"magic": False}}),
    "SYSTEMS_VALUE_NOT_BOOL": lambda: _systems.for_book({"systems": {"wounds": "off"}}),
    "SYSTEMS_NOT_SWITCHABLE": lambda: _systems.for_book({"systems": {"memory": False}}),
    "SYSTEMS_NEEDS_UNMET":    lambda: _systems.for_book({"systems": {"condition_flow": True, "condition": False}}),
}
# ENERGY AND STRESS THAT MOVE (gate condition-flow): the flow refuses what it cannot move, and the director's
# words refuse what the engine does not price.
CONDITION_CASES = {
    "CONDITION_NOT_A_DICT":            lambda: _condition.spend(["energy"], 1.0),
    "CONDITION_KEYS_MISSING":          lambda: _condition.spend({"energy": 0.5}, 1.0),
    "CONDITION_SPAN_NOT_NUMERIC":      lambda: _condition.spend({"energy": 0.5, "allostatic_load": 0.1}, "an hour"),
    "CONDITION_DECLARATION_MALFORMED": lambda: _condition.apply_declared({"maren": {}}, [{"char": "maren"}]),
    "CONDITION_WORD_UNKNOWN":          lambda: _condition.apply_declared({"maren": {}}, [{"char": "maren", "energy": "exhausted"}]),
}
# STRENGTH AND EXERTION (gate body-exertion): a sheet the body cannot weigh, and a word it does not price.
BODY_CASES = {
    "BODY_STRENGTH_MISSING":  lambda: _body.capacity({"baseline": {"body": {}}}),
    "BODY_STRENGTH_UNKNOWN":  lambda: _body.capacity({"baseline": {"body": {"strength": "mighty"}}}),
    "BODY_EXERTION_UNKNOWN":  lambda: _body.exert({"energy": 0.5, "allostatic_load": 0.1}, "strenuous", 1.0, 1.0),
}
# BODILY INJURIES (gate injuries): a sheet's page-one list the system cannot read, and a severity it does not heal by.
INJURY_CASES = {
    "INJURY_SHAPE":            lambda: _injuries.require({"current": {"condition": {"injuries": [{"severity": "minor"}]}}}),
    "INJURY_SEVERITY_UNKNOWN": lambda: _injuries.stage("mortal", 0),
    "INJURY_AGO_NOT_A_SPAN":   lambda: _injuries.require({"current": {"condition": {"injuries": [
        {"what": "a cut", "severity": "minor", "ago": "a while"}]}}}),
}

# the composition pass's parser lives in scripts/ (like appraiser's); its cases are in
# tests/test_composition_phase_a.py, execution-checked there, and registry-checked here.

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
    "ATTACH_":   (ATTACH_CASES, RecordError),
    "SYSTEMS_":  (SYSTEMS_CASES, RecordError),
    "CONDITION_": (CONDITION_CASES, RecordError),
    "BODY_":     (BODY_CASES, RecordError),
    "INJURY_":   (INJURY_CASES, RecordError),
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
