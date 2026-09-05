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

WHERE THIS ENDS, stated because "the refusal surface is converted" reads wider than it is true.

INSIDE `src/engine/`, THE RULE IS NOW TOTAL BY CONSTRUCTION. `EngineError.__init__` REFUSES a
one-argument construction outright (2026-09-02), so an uncoded refusal cannot be written, not
merely cannot be found. That replaced enforcement by a SCAN, and the scan was not enough: the AST
audit certified the engine fully converted while 44 prose refusals sat in `records.py` — the
surface every committed turn passes through — because it read `_require(cond, msg)` as an
already-coded doorway. `errors.py`'s own two raises are the one exemption, asserted by name:
`UnknownErrorCode` is deliberately a plain ValueError, because it fires from inside the constructor
that validates codes and a coded form would recurse.

`scripts/` — measured, not assumed. An earlier draft here said scripts refuse in prose and stopped,
and half of that was already false:

  * AN ENGINE REFUSAL SURFACED BY A SCRIPT KEEPS ITS CODE. Six sites do `raise SystemExit(str(e))`
    and one formats `"%s" % e`; `EngineError.__str__` renders `[CODE] detail`, so
    `python scripts/direct.py --book no-such-book` prints `[BOOK_NOT_FOUND] …` at the terminal.
    `tests/test_driver_main.py` asserts it, and an AST check refuses a wrapper that reaches past
    the exception into `.detail` — which would strip every code from every CLI surface silently.
  * FIVE SCRIPT-SIDE RESTATEMENTS NOW DELEGATE to the module that owns the rule, so their codes
    live in that module's family rather than a `SCRIPT_` one: the naming rule says a prefix names
    the OWNER, and `SCRIPT_` is detected-here by construction. `scene.py` was re-implementing
    `narration_modes.validate` while importing its vocabulary from a sibling SCRIPT.
  * THE SIXTH LANDED ON 2026-09-03, once the block was removed rather than argued around.
    `scene.py`'s law denial now delegates to `bible.require_allowed`, raising BIBLE_ACT_IMPOSSIBLE.
    It was blocked because `bible.py` sat at 546 lines, over hard rule 6's bound and frozen by the
    ratchet — so `bible.py` was SPLIT into the PIN (what a run ran against) and `law.py` (the
    RULING), and it left the grandfathered debt list at the same time.
  * USAGE ERRORS STAY PROSE, deliberately. "pass exactly one of --book or --fixture" names nothing
    an operator can look up; the fix is to retype the command.
  * 7 script-native CONTENT refusals stay prose, and that is DECIDED rather than pending: they are
    exactly the sites with no owning engine module, which is the same fact as having nothing a
    runbook would look up. "This book holds no runs" reports an empty result rather than refusing
    bad input; `gen_map.py` is repo tooling; the rest are argument-shape, one keystroke from usage.

`.claude/hooks/` — 5 exit sites, prose, and out of scope by the same rule: they are harness, not
engine, and a hook's DENY message is read by an agent rather than looked up in a runbook.

NAMING. `<MODULE>_<WHAT_WENT_WRONG>`, SCREAMING_SNAKE. The prefix names the module that owns the
refusal, not the module that happened to detect it. Keep the code stable once shipped: it is the
grep handle an operator and a book author both use, and renaming one is a breaking change to
every runbook and blueprint that cites it.
"""
from __future__ import annotations

from .code_families import (  # the data half; this file keeps the contract
    _RECORD,
    _VAULT,
    _TAG,
    _SPINE,
    _DIRECTION,
    _WORLD_APPRAISAL,
    _TENSION,
    _CLOCK,
    _EDL,
    _NARRATION,
    _ACQUISITION_F,
    _ARC_F,
    _BOOK_F,
    _COMPOUND_F,
    _CONNECTION_F,
    _DB_F,
    _DECAY_F,
    _DIRECTION_F,
    _FAULT_F,
    _GATE_F,
    _PROMPT_F,
    _SCENE_F,
    _SEVERITY_F,
    _WOUND_F,
    _LEVERS,
    _CITATION,
    _BONDS,
    _TOWARD,
    _PROFILE,
    _BIBLE,
    _STATE,
    _LEDGER,
    _WORLD_EVENT,
    _CLAIM,
    _READ,
)

_FAMILIES = (
    _RECORD,
    _VAULT,
    _TAG,
    _SPINE,
    _DIRECTION,
    _WORLD_APPRAISAL,
    _TENSION,
    _CLOCK,
    _EDL,
    _NARRATION,
    _ACQUISITION_F,
    _ARC_F,
    _BOOK_F,
    _COMPOUND_F,
    _CONNECTION_F,
    _DB_F,
    _DECAY_F,
    _DIRECTION_F,
    _FAULT_F,
    _GATE_F,
    _PROMPT_F,
    _SCENE_F,
    _SEVERITY_F,
    _WOUND_F,
    _LEVERS,
    _CITATION,
    _BONDS,
    _TOWARD,
    _PROFILE,
    _BIBLE,
    _STATE,
    _LEDGER,
    _WORLD_EVENT,
    _CLAIM,
    _READ,
)

# The families live in `code_families.py` — data that grows, split from the contract above.
# Merged here so `codes.CODES` and `codes.DESCRIPTIONS` keep the names every consumer uses.
_REGISTRY = {}
for _fam in _FAMILIES:
    _REGISTRY.update(_fam)

CODES = frozenset(_REGISTRY)

#: code -> one-line description. Used by tests and by the operator-facing code index.
DESCRIPTIONS = dict(_REGISTRY)

def is_registered(code):
    """True when `code` may be constructed into an EngineError."""
    return code in CODES

def describe(code):
    """One-line description for a registered code, or None."""
    return DESCRIPTIONS.get(code)
