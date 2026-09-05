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
# The families live in `code_families.py` — data that grows, split from the
# contract in this file. Same split as the sibling instance, same reason.
from .code_families import (  # noqa: E402
    _VAULT,
    _TAG,
    _SPINE,
    _DIRECTION,
    _MIGRATED,
    _DECAY,
)

# One dict per module as its gate lands. Merged into CODES below.
_REGISTRY = {}
_REGISTRY.update(_VAULT)
_REGISTRY.update(_TAG)
_REGISTRY.update(_SPINE)
_REGISTRY.update(_DIRECTION)
_REGISTRY.update(_MIGRATED)
_REGISTRY.update(_DECAY)

CODES = frozenset(_REGISTRY)

#: code -> one-line description. Used by tests and by the operator-facing code index.
DESCRIPTIONS = dict(_REGISTRY)


def is_registered(code):
    """True when `code` may be constructed into an EngineError."""
    return code in CODES


def describe(code):
    """One-line description for a registered code, or None."""
    return DESCRIPTIONS.get(code)
