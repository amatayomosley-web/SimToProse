"""test_errors.py — the coded refusal channel, and the registry's two-way rule.

WHY THIS SUITE EXISTS. A repo-wide sweep on 2026-08-30 found 214 sites where a failure, an absence,
or an invalid value produced no loud error. The motivating incident: an actor omitted one enum
field, `scripts/scene.py:403` answered `ok=False` with `applied = {"dimensions": {}}`, the entire
self-report was discarded, and the scene lulled with no error anywhere — while the operator line
printed the raw tags, so the beat read as healthy. Three runs burned.

`src/engine/errors.py` is the channel that ends that. This suite guards the four things about it
that, if they broke, would break silently:

  1. The base is a ValueError. 24 measured test sites catch bare `ValueError` for engine raises.
     Re-rooting the base would make all of them stop catching — and a test that stops catching an
     exception it expected does not fail loudly, it passes for the wrong reason.
  2. The detail survives verbatim. 13 measured tests assert on message substrings; the tightest,
     tests/test_no_digits.py:255, asserts the offending PATH appears in `str()`.
  3. The legacy one-argument form renders byte-identically to how these classes rendered before
     errors.py existed, so a module can be migrated on its own gate without a flag day.
  4. THE REGISTRY IS TWO-WAY. A code raised must be registered; a code registered must be raised.
     The second half is the one that matters: this repo's named dominant defect class is
     "declared, wired in isolation, never connected", and a registry accumulating codes nothing
     raises would be that class reproduced inside the mechanism built to end it.

Run: python tests/test_errors.py      (run_all.py invokes it as a subprocess and reads the exit code)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from src.engine import codes                                          # noqa: E402
from src.engine.errors import EngineError, UnknownErrorCode           # noqa: E402
from src.engine.bible import BibleError                               # noqa: E402
from src.engine.books import BookError, CrossBookDbError              # noqa: E402
from src.engine.citation import CitationError                         # noqa: E402
from src.engine.compounds import CompoundError                        # noqa: E402
from src.engine.ledger import LedgerError                             # noqa: E402
from src.engine.read_api import ReadError                             # noqa: E402
from src.engine.records import RecordError                            # noqa: E402
from src.engine.vault import VaultError                               # noqa: E402

_FAILS = []


def check(name, cond, detail=""):
    if not cond:
        _FAILS.append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  - " + detail) if (detail and not cond) else ""))


_ALL = (BibleError, BookError, CrossBookDbError, CitationError, CompoundError,
        LedgerError, ReadError, RecordError, VaultError)


def test_every_class_is_one_family():
    """One `except EngineError` must catch every engine refusal. Before this, LedgerError rooted on
    RuntimeError and the other eight on ValueError, so no single clause could."""
    for cls in _ALL:
        check("family-%s" % cls.__name__, issubclass(cls, EngineError))
    # The re-root that had no observer: nothing in src/, scripts/ or tests/ catches bare
    # RuntimeError, so LedgerError's old base was untested in BOTH directions.
    check("ledger-error-re-rooted",
          issubclass(LedgerError, EngineError) and not issubclass(LedgerError, RuntimeError),
          "LedgerError must no longer be a RuntimeError")


def test_the_base_is_a_valueerror():
    """INVARIANT 1. 24 test sites catch bare ValueError for engine raises. If this breaks, they all
    stop catching — and stopping-to-catch is a silent pass, not a failure."""
    check("base-is-valueerror", issubclass(EngineError, ValueError))
    for cls in _ALL:
        check("valueerror-%s" % cls.__name__, issubclass(cls, ValueError))


def test_the_coded_form_renders_and_exposes_its_code():
    code = sorted(codes.CODES)[0]
    e = EngineError(code, "the detail")
    check("coded-str", str(e) == "[%s] the detail" % code, str(e))
    check("coded-code", e.code == code)
    check("coded-detail", e.detail == "the detail")


def test_the_detail_survives_verbatim():
    """INVARIANT 2. The prefix is added; the message is never restructured. tests/test_no_digits.py:255
    asserts an offending path appears in str() — a detail moved into an unrendered attribute breaks
    it, and so would rewording."""
    msg = "characters/Tam.md: belief confidence 1.4 out of [0,1]"
    e = VaultError("VAULT_BELIEF_CONFIDENCE_RANGE", msg)
    check("detail-verbatim", msg in str(e), str(e))
    check("detail-is-suffix", str(e).endswith(msg), str(e))


def test_the_legacy_form_is_unchanged():
    """INVARIANT 3. An unmigrated module keeps its exact pre-errors.py rendering, so migration is
    per-module and not a flag day."""
    e = BibleError("world has not answered step 1")
    check("legacy-str", str(e) == "world has not answered step 1", str(e))
    check("legacy-code-is-none", e.code is None)
    check("legacy-still-catchable", isinstance(e, ValueError))


def test_an_unregistered_code_refuses_at_construction():
    """A mistyped code must not silently produce a valid-looking error. That would be this repo's
    own dominant defect class, reappearing inside the mechanism built to end it."""
    try:
        EngineError("NOT_A_REAL_CODE_XYZ", "detail")
        check("unregistered-refused", False, "construction was allowed")
    except UnknownErrorCode:
        check("unregistered-refused", True)
    except Exception as exc:                                   # noqa: BLE001 - the type IS the assertion
        check("unregistered-refused", False, "wrong type: %r" % type(exc).__name__)
    check("unknown-code-error-is-not-engine-error",
          not issubclass(UnknownErrorCode, EngineError),
          "would recurse: constructing an EngineError needs a registered code")


def _used_codes():
    """Every code literal that enters the system, across src/ and scripts/.

    TWO doorways, not one — and the guard originally knew only about the first, which is exactly
    the coverage gap it exists to catch:
      * `raise SomeError("CODE", ...)`  — a refusal
      * `_flag("CODE", ...)`            — a validation finding, which a driver may then raise on
    A code reaching the system through either doorway counts as used.
    """
    found = set()
    pats = (re.compile(r'raise\s+\w*Error\(\s*"([A-Z][A-Z0-9_]+)"'),
            re.compile(r'_flag\(\s*"([A-Z][A-Z0-9_]+)"'))
    for sub in ("src", "scripts"):
        for root, _dirs, files in os.walk(os.path.join(REPO, sub)):
            if "__pycache__" in root:
                continue
            for fn in files:
                if fn.endswith(".py"):
                    with open(os.path.join(root, fn), encoding="utf-8") as fh:
                        text = fh.read()
                    for pat in pats:
                        found.update(pat.findall(text))
    return found


def test_the_registry_is_two_way():
    """THE RULE. Registered-but-never-raised is the failure this repo keeps shipping; it gets the
    same weight here as raised-but-unregistered."""
    used = _used_codes()
    registered = set(codes.CODES)
    unregistered = sorted(used - registered)
    unused = sorted(registered - used)
    check("every-used-code-is-registered", not unregistered,
          "used but absent from codes.py: %s" % unregistered)
    check("every-registered-code-is-used", not unused,
          "registered but used nowhere - a declared key with no reader: %s" % unused)
    check("registry-is-not-empty", len(registered) > 0)
    check("every-code-has-a-description",
          all(codes.describe(c) for c in registered),
          "missing: %s" % sorted(c for c in registered if not codes.describe(c)))


def test_the_vault_codes_reach_a_real_book():
    """END TO END, on the loader every book hits first: a real authoring mistake produces its code."""
    import tempfile
    from src.engine import vault
    with tempfile.TemporaryDirectory() as tmp:
        missing = os.path.join(tmp, "no-such-book")
        try:
            vault.load_book(missing)
            check("book-folder-missing-raises", False, "no raise")
        except VaultError as e:
            check("book-folder-missing-raises", e.code == "VAULT_BOOK_FOLDER_MISSING", str(e))

        # a world note, no characters -> the refusal a world-only author actually meets
        os.makedirs(os.path.join(tmp, "book", "world"))
        os.makedirs(os.path.join(tmp, "book", "characters"))
        with open(os.path.join(tmp, "book", "world", "W.md"), "w", encoding="utf-8") as fh:
            fh.write('---\ntype: world\nid: W\n---\n\n# W\n\n```json\n{"world": "W"}\n```\n')
        try:
            vault.load_book(os.path.join(tmp, "book"))
            check("no-characters-raises", False, "no raise")
        except VaultError as e:
            check("no-characters-raises", e.code == "VAULT_NO_CHARACTERS", str(e))
            check("no-characters-str-is-prefixed", str(e).startswith("[VAULT_NO_CHARACTERS] "), str(e))


def test_the_real_suite_runner_is_the_baseline():
    """The instrument check. 30 of 44 suites use a non-raising `check()` accumulator, so pytest
    calls the test function, gets None, and prints PASS no matter what the assertions found. Proven
    2026-08-30 with a minimal file: a deliberately-false condition gave `pytest: 1 passed` and
    `python file.py: FAIL, exit=1`. Any gate phrased against pytest cannot observe a regression in
    those 30 suites. This test makes the repo say so out loud."""
    probe = os.path.join(REPO, "tests", "test_errors.py")
    r = subprocess.run([sys.executable, probe], capture_output=True, cwd=REPO,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8", SWE_ERRORS_SELFTEST="1"))
    check("suite-is-runnable-as-a-script", r.returncode in (0, 1),
          "exit=%s" % r.returncode)
    check("run_all-is-the-documented-runner",
          os.path.isfile(os.path.join(REPO, "tests", "run_all.py")),
          "python tests/run_all.py is the only invocation that observes all 44 suites")


def main():
    print("test_errors.py - the coded refusal channel and the two-way registry")
    for t in (test_every_class_is_one_family,
              test_the_base_is_a_valueerror,
              test_the_coded_form_renders_and_exposes_its_code,
              test_the_detail_survives_verbatim,
              test_the_legacy_form_is_unchanged,
              test_an_unregistered_code_refuses_at_construction,
              test_the_registry_is_two_way,
              test_the_vault_codes_reach_a_real_book):
        t()
    if not os.environ.get("SWE_ERRORS_SELFTEST"):
        test_the_real_suite_runner_is_the_baseline()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
