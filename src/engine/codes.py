"""codes.py — the frozen registry of engine error codes.

THE RULE THAT MAKES THIS WORTH HAVING, in both directions:

  * A code raised anywhere must appear here, or `EngineError.__init__` refuses to construct.
  * A code listed here must be raised somewhere, or `tests/test_errors.py` fails.

The second half is the point. This repo's named dominant defect class is "declared, wired in
isolation, never connected" — a documented key with no reader is a lie with a citation. A registry
that accumulated codes nothing raises would be that exact class, reproduced inside the mechanism
built to end it. So the registry grows one module at a time, on the same gate that converts that
module's raises, and never ahead of them.

A repo-wide sweep (2026-08-30, 214 sites) sized the full namespace at ~148 codes. They are NOT
pre-registered here. Each arrives with its raise.

NAMING. `<MODULE>_<WHAT_WENT_WRONG>`, SCREAMING_SNAKE. The prefix names the module that owns the
refusal, not the module that happened to detect it. Keep the code stable once shipped: it is the
grep handle an operator and a book author both use, and renaming one is a breaking change to
every runbook and blueprint that cites it.
"""
from __future__ import annotations

# ---- VAULT_* — the authoring contract for a book's .md notes (src/engine/vault.py) ----
# These are the first refusals any book author meets: the loader reads their files before anything
# else runs. Every one of them names a field a human wrote by hand, which is why they are also the
# codes the authoring blueprints cite in their "what happens if you leave this blank" column.
_VAULT = {
    "VAULT_ENGINE_BLOCK_INVALID_JSON":  "a note's ```json engine block is not parseable json",
    "VAULT_BELIEF_CONFIDENCE_RANGE":    "a Beliefs bullet's confidence is outside [0,1]",
    "VAULT_BELIEFS_SECTION_UNPARSED":   "'## Beliefs' has bullets and none match the authoring contract",
    "VAULT_BOOK_FOLDER_MISSING":        "the book folder does not exist",
    "VAULT_WORLD_NOTE_COUNT":           "a book needs exactly one type:world note",
    "VAULT_WORLD_NO_ENGINE_BLOCK":      "the world note carries no ```json engine block",
    "VAULT_CHARACTER_NO_ENGINE_BLOCK":  "a character note carries no ```json engine block",
    "VAULT_CHARACTER_BLOCK_INCOMPLETE": "a character engine block is missing a required top-level key",
    "VAULT_NO_CHARACTERS":              "a book has no character notes at all",
}

# ---- TAG_* — the actor's self-reported event tags (src/engine/consolidation.py) ----
# The hard half (ok=False) is what the drivers raise on. The soft half only flags: it narrows or
# reports, and a beat carrying only soft flags still moves state.
_TAG = {
    # hard — the beat is refused
    "TAG_TYPE_UNKNOWN":                  "tags.type is not a CATALOG key",
    "TAG_DIMENSIONS_TYPE":               "tags.dimensions is present but is not a dict",
    "TAG_DIMENSION_VALUE_NOT_NUMERIC":   "a dimension's magnitude is not a number",
    "TAG_DIMENSION_VALUE_RANGE":         "a dimension's magnitude is outside [0,1]",
    "TAG_DURABILITY_MISSING":            "tags.durability is absent",
    "TAG_DURABILITY_INVALID":            "tags.durability is not one of {transient, durable}",
    "TAG_CONFIDENCE_NOT_NUMERIC":        "tags.confidence is present but is not a number",
    "TAG_CONFIDENCE_RANGE":              "tags.confidence is outside [0,1]",
    # soft — reported and narrowed, never fatal
    "TAG_TYPE_NOT_ACTOR_OFFERED":        "a CATALOG type an actor is never offered was self-reported",
    "TAG_DIMENSION_UNKNOWN":             "a dimension key outside the known vocabulary (dropped)",
    "TAG_TARGET_NOT_PERCEIVED":          "the tag names a subject absent from the PerceptSet",
    "TAG_DIMENSION_NOT_IN_APPRAISAL_MAP": "a primary-driver dimension the chosen type does not legitimize",
    "TAG_CAPABILITY_BELOW_REQ":          "the actor's skill is below the type's capability_req",
}

# ---- LEDGER_* / RECORD_* / DB_* — the append-only spine (ledger.py, records.py, db.py) ----
_SPINE = {
    "LEDGER_ARC_DIFF_REWRITE": "a second, DIFFERENT arc diff arrived for a (run, char, turn) that already has one",
}

# ---- DIRECTION_* — turning stored numbers into words (src/engine/direction.py) ----
_DIRECTION = {
    "DIRECTION_VALUE_NOT_IN_UNIT_INTERVAL":
        "a value bound for a stage direction is not a number in [0,1] - usually prose in a numeric slot",
}

# One dict per module as its gate lands. Merged into CODES below.
_REGISTRY = {}
_REGISTRY.update(_VAULT)
_REGISTRY.update(_TAG)
_REGISTRY.update(_SPINE)
_REGISTRY.update(_DIRECTION)

CODES = frozenset(_REGISTRY)

#: code -> one-line description. Used by tests and by the operator-facing code index.
DESCRIPTIONS = dict(_REGISTRY)


def is_registered(code):
    """True when `code` may be constructed into an EngineError."""
    return code in CODES


def describe(code):
    """One-line description for a registered code, or None."""
    return DESCRIPTIONS.get(code)
