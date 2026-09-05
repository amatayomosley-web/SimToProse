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
import io
import ast
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


def test_an_engine_error_SURVIVES_copy_and_pickle():
    """INVARIANT 3. An exception must be reconstructible FROM ITS OWN ARGS.

    Python rebuilds an exception as `cls(*self.args)` — that is how `copy.copy`, `copy.deepcopy`,
    `pickle`, `multiprocessing` and `concurrent.futures` all do it. `__init__` used to pass the
    RENDERED message to `super().__init__`, so `args` held one element, and once the uncoded branch
    was retired every one of those became a refused one-argument construction. Measured 2026-09-03:
    all three mechanisms raised UnknownErrorCode on a coded VaultError.

    The caller here is the INTERPRETER, which is why no sweep of raise sites could find it and why
    it is pinned by a round trip rather than by a scan. It was latent — nothing in the tree copies
    or pickles an engine error — and a latent contract break is still a break."""
    import copy as _copy
    import pickle as _pickle
    e = BibleError("BIBLE_LAW_ID_MISSING", "laws[0] has no id")
    check("args-are-the-CONSTRUCTOR-arguments", e.args == ("BIBLE_LAW_ID_MISSING",
                                                           "laws[0] has no id"), str(e.args))
    for label, rebuilt in (("copy", _copy.copy(e)),
                           ("deepcopy", _copy.deepcopy(e)),
                           ("pickle", _pickle.loads(_pickle.dumps(e)))):
        check("survives-%s" % label,
              type(rebuilt) is type(e) and rebuilt.code == e.code
              and rebuilt.detail == e.detail and str(rebuilt) == str(e),
              "%r vs %r" % (str(rebuilt), str(e)))

    # ...and the rendering the args change could have silently broken: invariant 2 says the detail
    # is the VERBATIM suffix, which 13 tests assert with `in str(e)`. `__str__` is explicit now
    # precisely because `args` no longer carries the rendered string.
    check("str-still-renders-[CODE]-detail", str(e) == "[BIBLE_LAW_ID_MISSING] laws[0] has no id",
          str(e))
    check("...and-the-detail-is-still-the-verbatim-suffix", str(e).endswith("laws[0] has no id"))


def test_the_legacy_UNCODED_form_is_REFUSED():
    """INVARIANT 3, INVERTED ON 2026-09-02 — and the inversion is this goal's finish line.

    This used to assert that an uncoded refusal still CONSTRUCTED, so a module could migrate on its
    own gate without a flag day. That reason expired when the last module converted: measured the
    same day, zero one-arg constructions of any of the 21 engine error classes remained in `src/`,
    `scripts/` or `.claude/`.

    While the branch stood, `codes.py`'s first rule was enforced by a SCAN. The scan is not enough,
    and that is measured rather than argued: the AST audit certified the engine fully converted
    while 44 prose refusals sat in `records.py` — the surface every committed turn passes through —
    because it read `_require(cond, msg)` as an already-coded doorway. A constructor cannot be
    missed by anything that runs."""
    for label, ctor in (("a module error", lambda: BibleError("world has not answered step 1")),
                        ("the base class", lambda: EngineError("plain prose")),
                        ("no arguments at all", lambda: EngineError())):
        try:
            ctor()
            check("an-uncoded-refusal-is-refused:%s" % label, False, "it CONSTRUCTED")
        except UnknownErrorCode as e:
            check("an-uncoded-refusal-is-refused:%s" % label, "Pass the code FIRST" in str(e),
                  str(e)[:80])

    # THE ONE EXEMPTION, asserted by name: `UnknownErrorCode` is deliberately a plain ValueError
    # (errors.py:52) and NOT an EngineError, because it is raised from inside the constructor that
    # validates codes — a coded form would recurse. If someone re-roots it, this fails.
    check("UnknownErrorCode-is-NOT-an-EngineError", not issubclass(UnknownErrorCode, EngineError))
    check("...and-still-takes-one-argument", str(UnknownErrorCode("a bare message")))


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


def _is_env_lookup(call):
    """`os.environ.get(...)` or `os.getenv(...)` — an environment variable, not an error code.

    They share a spelling convention and nothing else. Excluded by NAME rather than by a list of
    the three that exist today, so a fourth needs no edit here.
    """
    f = call.func
    if isinstance(f, ast.Attribute) and f.attr in ("get", "getenv"):
        v = f.value
        if isinstance(v, ast.Attribute) and v.attr == "environ":
            return True
        if isinstance(v, ast.Name) and v.id == "os":
            return True
    return False


def _used_codes():
    """Every code literal that ENTERS the system, across src/ and scripts/.

    PARSED, NOT MATCHED — and that is the repair, not a preference. This walked the raw TEXT with a
    regex per doorway, and had to learn a new pattern every time a module invented one: `raise
    X("CODE", …)`, then `_flag("CODE", …)`, then `_require(cond, "CODE", …)` (which needed a
    paren-balancer, because the condition contains commas), then `raise err("CODE", …)` where the
    type is a parameter. Four patterns, three of them added AFTER the guard went red on codes that
    were being raised through a doorway it had not been taught.

    Reading CALL ARGUMENTS instead needs no doorway list at all: every one of those spellings is a
    call with the code as an argument, and a fifth invented tomorrow will be too.

    IT ALSO CLOSES THE ONE WEAKNESS HERE THAT FAILED **GREEN**. The regex read comments and
    docstrings, so a commented-out raise could keep a dead code "used" — the registry's
    listed-but-never-raised rule would report clean on a code nothing raises. A docstring is never a
    call argument, so the parse cannot see one. Every other weakness in this file fails red; this
    was the exception, deferred across four gates, and it is closed rather than accepted.

    Measured on the swap (2026-09-02): the parse finds every code the four patterns found, plus 34
    more they missed — multi-line `_require` calls the balancer still could not span. Strict
    superset, so the guard cannot have got weaker.

    ENVIRONMENT LOOKUPS ARE EXCLUDED, and finding out why is the whole reason this note exists. A
    first draft said the extras were harmless because "the only consumer is a subset test" — that
    was WRONG. `test_every_used_code_is_registered` runs the check in the other direction too, and
    `os.environ.get("SWE_BOOKS")` reads as a used-but-unregistered code. Three of them,
    immediately. So `os.environ.get` and `os.getenv` arguments are skipped by name: an environment
    variable and an error code share a spelling convention and nothing else.
    """
    found = set()
    for sub in ("src", "scripts"):
        for root, _dirs, files in os.walk(os.path.join(REPO, sub)):
            if "__pycache__" in root:
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                with open(os.path.join(root, fn), encoding="utf-8") as fh:
                    text = fh.read()
                try:
                    tree = ast.parse(text)
                except SyntaxError:                    # a file that cannot parse is a louder failure
                    continue                           # elsewhere; this guard is not the place
                for n in ast.walk(tree):
                    if not isinstance(n, ast.Call):
                        continue
                    if _is_env_lookup(n):              # SCREAMING_SNAKE, and not a code
                        continue
                    for a in n.args:
                        if (isinstance(a, ast.Constant) and isinstance(a.value, str)
                                and re.fullmatch(r"[A-Z][A-Z0-9]*_[A-Z0-9_]+", a.value or "")):
                            found.add(a.value)
    return found


def test_the_code_scan_CANNOT_SEE_a_comment_or_a_docstring():
    """THE WEAKNESS THAT FAILED GREEN, closed and pinned.

    A commented-out raise used to keep a dead code alive in `_used_codes`, so the registry's
    "a listed code must be raised somewhere" rule would report clean on a code nothing raises.
    Proven against a file that mentions a code three ways the old regex would have counted."""
    import tempfile
    bait = (
        '"""A docstring mentioning raise X("BAIT_IN_DOCSTRING", "x").' + chr(10) + '"""' + chr(10) +
        '# raise X("BAIT_IN_COMMENT", "x")' + chr(10) +
        'MENTIONED = "BAIT_AS_A_BARE_STRING"' + chr(10) +
        'def f():' + chr(10) +
        '    raise ValueError("BAIT_REALLY_RAISED", "x")' + chr(10))
    tmp = tempfile.mkdtemp()
    sub = os.path.join(tmp, "src")
    os.makedirs(sub)
    with open(os.path.join(sub, "bait.py"), "w", encoding="utf-8") as fh:
        fh.write(bait)
    global REPO
    real, REPO = REPO, tmp
    try:
        seen = _used_codes()
    finally:
        REPO = real
    check("a-code-in-a-DOCSTRING-is-not-used", "BAIT_IN_DOCSTRING" not in seen, str(sorted(seen)))
    check("a-code-in-a-COMMENT-is-not-used", "BAIT_IN_COMMENT" not in seen, str(sorted(seen)))
    check("a-code-as-a-BARE-assignment-is-not-used", "BAIT_AS_A_BARE_STRING" not in seen,
          str(sorted(seen)))
    check("...but-a-code-REALLY-raised-IS-used", "BAIT_REALLY_RAISED" in seen, str(sorted(seen)))


def _embedded_code_sites(text):
    """Raises carrying a code INSIDE the message: `raise X("CODE: prose…")`.

    THE SHAPE THAT HID A BUG FROM ITS OWN MEASUREMENT. Every doorway pattern here requires a closing
    quote immediately after the code token, so an embedded code is invisible to all of them — and on
    2026-09-02 a gate certified "0 bare-prose raises remaining" using exactly those patterns, while
    `clock.py` still raised `"LEDGER_TIME_DECL_REWRITE: run %r …"` through the legacy one-arg path
    with the code unregistered. The instrument could not see the thing it was asked to measure, and
    reported clean.

    So this looks for the shape ON PURPOSE and the suite FAILS on it. A code embedded in prose is
    not a coded raise: it carries no `.code`, skips the registry check, and cannot be grepped by an
    operator who has only the code.

    THE UNDERSCORE IS REQUIRED. Every registered code has one; `raise SystemExit("USAGE: …")` and
    `raise RuntimeError("ERROR: …")` never will, and both would otherwise fail this suite with the
    misleading diagnosis "a code buried in a message".

    AND THIS IS THE CHEAPER LAYER, NOT THE ONLY ONE. An f-string, a %-built message or a variable
    detail is invisible to any textual scan — those are caught at the runtime choke point in
    `errors.EngineError.__init__`, where every finished string must pass.
    """
    return re.findall(r'raise\s+\w+\(\s*"([A-Z][A-Z0-9]*_[A-Z0-9_]{2,}):', text)


def _require_codes(text):
    """Codes passed to a module's own `_require(cond, CODE, msg)` helper.

    Scanned by BALANCING PARENS rather than by regex, because the condition is an expression and
    routinely contains commas and nested calls — `_require(isinstance(t, (int, float)) and ...,`
    defeats any `[^,]+` pattern, and a regex that half-works here reports a raised code as unraised,
    which is the guard lying in the direction that costs a real conversion.
    """
    # ONLY the three-arg helper. `read_api._require(cond, msg)` shares the NAME and takes two args,
    # so a scanner keyed on the name alone half-matches across a boundary the moment anyone
    # harmonises the two helpers or pastes a call between them. Guarded by requiring the code to be
    # the SECOND argument — a two-arg helper whose message happens to start SCREAMING would still
    # be caught, and that is the safe direction (it fails red, not green).
    out = set()
    for m in re.finditer(r'_require\(', text):
        i, depth = m.end(), 1
        while i < len(text) and depth:
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
            i += 1
        # FIRST match only: the code is the argument after the condition, so it precedes anything
        # quoted in the message. Taking all of them collected a `fromlist=["WORDS"]` out of a
        # message string and reported it as an unregistered code.
        found_here = re.findall(r'"([A-Z][A-Z0-9_]{4,})"', text[m.end():i])
        if found_here:
            out.add(found_here[0])
    return out


def test_no_raise_hides_its_code_INSIDE_the_message():
    """The counter-instrument. Every other check here reads codes as a first string argument, so
    none of them can see `raise X("CODE: prose")` — and one existed while a gate said none did."""
    hits = []
    for sub in ("src", "scripts"):
        for root, _dirs, files in os.walk(os.path.join(REPO, sub)):
            if "__pycache__" in root:
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                with open(path, encoding="utf-8") as fh:
                    for code in _embedded_code_sites(fh.read()):
                        hits.append("%s: %s" % (os.path.relpath(path, REPO), code))
    check("no-code-is-buried-in-a-message", not hits,
          "a code inside the message carries no .code, skips the registry check, and cannot be "
          "grepped by an operator who has only the code: %s" % hits)



def test_the_RUNTIME_choke_point_catches_what_no_scan_can():
    """The layer under the static check, and the reason it exists.

    Every textual scan here needs the code as a literal opening a string. An f-string, a %-built
    message or a variable detail defeats all of them — and each one arrives at
    `EngineError.__init__` as a finished string, so that is where they are caught.

    Built 2026-09-02 after a static scan certified "0 bare-prose raises" while one existed, and
    then found unguarded by its own control run: the choke point could be deleted and every test
    still passed. This is that control, kept."""
    code = "TENSION_ID_MISSING"
    dynamic = [
        ("f-string", "%s: built at runtime" % code),          # what an f-string produces
        ("percent-built", "%s: %s" % (code, "detail")),
        ("variable detail", code + ": assembled from parts"),
    ]
    for label, msg in dynamic:
        try:
            EngineError(msg)
            check("the-choke-point-refuses-a-%s" % label.replace(" ", "-"), False,
                  "a code-shaped one-arg message was accepted: %r" % msg)
        except UnknownErrorCode as e:
            check("the-choke-point-refuses-a-%s" % label.replace(" ", "-"),
                  "Pass the code FIRST" in str(e), str(e)[:80])

    # CONVENTIONAL PROSE IS NOW REFUSED TOO, and that is the point rather than collateral. The
    # narrow check above existed to catch a code HIDING inside a message while leaving ordinary
    # prose alone; retiring the uncoded branch makes that case a SUBSET of a general refusal, so
    # the special case no longer has to be right about which shouts are codes.
    for label, msg in (("usage", "USAGE: pass --book <slug>"),
                       ("error-shout", "ERROR: could not open the db"),
                       ("plain prose", "a tension carries no id")):
        try:
            EngineError(msg)
            check("uncoded-prose-is-refused:%s" % label, False, "it CONSTRUCTED: %r" % msg)
        except UnknownErrorCode:
            check("uncoded-prose-is-refused:%s" % label, True)

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


def _raise_audit(path):
    """One module -> (codes it names, line numbers of prose refusals). PARSED, never grepped.

    TWO THINGS A REGEX GETS WRONG HERE, both measured on 2026-09-02:

      1. IT CANNOT SEE THE DOORWAY. `_require(cond, code, msg)` in tensions.py, edl.py and
         read_api.py ends in `raise X(code, msg)` where the code is a VARIABLE. A grep counts that
         as prose: it reported 188 uncoded sites where the parse reports 180, and called edl.py
         half-converted when edl.py is clean. So a bare first argument that is a PARAMETER of the
         enclosing function is recognised as the doorway.
      2. IT CANNOT SEE THROUGH THE DOORWAY EITHER. The codes those modules raise are literals at
         the `_require(...)` CALL, not at the raise — so a first draft of this audit reported
         twenty-three TENSION_/EDL_/TAG_ codes as registered-and-never-raised when every one of
         them fires. Codes are therefore collected from every CALL ARGUMENT, which reaches both
         spellings and reaches no docstring (a docstring is never a call argument, so a code cannot
         hide behind a mention of itself).
    """
    import ast
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    spans = [(n.lineno, getattr(n, "end_lineno", n.lineno),
              {a.arg for a in n.args.args + n.args.kwonlyargs})
             for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    def params_at(line):
        best, width = set(), None
        for a, b, names in spans:
            if a <= line <= b and (width is None or b - a < width):
                width, best = b - a, names
        return best

    def is_code(node):
        return (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and re.fullmatch(r"[A-Z][A-Z0-9]*_[A-Z0-9_]+", node.value))

    codes_named = {a.value for n in ast.walk(tree) if isinstance(n, ast.Call)
                   for a in n.args if is_code(a)}
    uncoded = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Raise) or not isinstance(n.exc, ast.Call):
            continue
        a0 = n.exc.args[0] if n.exc.args else None
        if is_code(a0):
            continue
        # A DOORWAY NEEDS A CODE **AND** A MESSAGE. The first version of this rule said "a bare
        # first argument that is a parameter of the enclosing function is the coded doorway", and
        # `records.py:172` is `_require(cond, msg)` raising `RecordError(msg)` — one argument, a
        # parameter, and pure prose. The rule read it as coded, so the module carrying the record
        # contract's 44 refusals landed in the raises-nothing bucket and the whole tree reported
        # converted. Measured 2026-09-02: records.py:174 is the only parameter-first raise in the
        # engine, so this is one module — but it is the one that validates every commit.
        if (isinstance(a0, ast.Name) and a0.id in params_at(n.lineno)
                and len(n.exc.args) >= 2):
            continue                                  # the coded doorway, not a prose refusal
        uncoded.append(n.lineno)
    return codes_named, uncoded


def test_NO_ENGINE_MODULE_IS_HALF_CONVERTED():
    """THE STATE THAT MISLEADS, and the one I keep producing.

    An all-prose module is honest: an operator greps the sentence and finds it. A module with SOME
    coded refusals is not — the first code someone finds tells them the module is coded, so they
    grep for a handle that is not there. Measured 2026-09-02: `claims.record` gained three codes in
    the morning and left five neighbours in prose; `direction.py` coded its range refusal and left
    four shape refusals; and `ledger.py` — the spine — coded one raise out of eleven, leaving the
    resume-divergence message an operator reads when a book will not reopen with no handle at all.

    This asserts only that no module is HALF converted. An all-prose module is NOT a violation:
    24 of them remain, and a permanently-red test is a test everyone learns to ignore."""
    eng = os.path.join(REPO, "src", "engine")
    modules = [f for f in sorted(os.listdir(eng)) if f.endswith(".py")]
    half, converted, prose, silent = [], [], [], []
    for f in modules:
        named, uncoded = _raise_audit(os.path.join(eng, f))
        if named and uncoded:
            half.append("%s (codes %d, prose at %s)" % (f, len(named), uncoded))
        elif named:
            converted.append(f)
        elif uncoded:
            prose.append((f, len(uncoded)))
        else:
            silent.append(f)                          # raises nothing at all — legitimate
    check("no-engine-module-is-HALF-converted", not half, "; ".join(half))
    # THE CONVERSION IS DONE, AND ONE MODULE IS EXEMPT BY NAME. Asserting the exemption rather
    # than tolerating a gap: `errors.py` raises `UnknownErrorCode` from inside
    # `EngineError.__init__`, the constructor that VALIDATES codes, so a coded raise there
    # re-enters the check it is performing. If a future edit codes them anyway, or if some other
    # module quietly joins the prose list, this fails — an all-prose module was legal while the
    # conversion was in flight and is not legal now that it has landed.
    EXEMPT_PROSE = {"errors.py": "raises from inside the constructor that validates codes"}
    unexpected = sorted(f for f, _n in prose if f not in EXEMPT_PROSE)
    check("no-UNEXPECTED-module-is-still-all-prose", not unexpected, str(unexpected))
    check("the-exemption-names-a-module-that-EXISTS",
          all(os.path.exists(os.path.join(eng, f)) for f in EXEMPT_PROSE), str(sorted(EXEMPT_PROSE)))
    check("...and-still-raises-something-uncoded",
          all(f in {x for x, _ in prose} for f in EXEMPT_PROSE),
          "an exemption outlived the raises it excuses: %s" % sorted(EXEMPT_PROSE))
    # COVERAGE BEFORE CONTENT. Every module must land in exactly one bucket, so a parse failure or
    # a widened doorway rule cannot quietly shrink what this test READS while it still reports PASS.
    check("the-audit-classified-EVERY-engine-module",
          len(half) + len(converted) + len(prose) + len(silent) == len(modules),
          "%d modules, %d classified" % (len(modules),
                                         len(half) + len(converted) + len(prose) + len(silent)))
    # THE CENSUS IS PRINTED, NOT ASSERTED. It is the number I have twice stated wrong from memory;
    # printing it every run means the next claim about how much is left is read, not recalled.
    print("        converted: %d | all-prose: %d modules, %d sites | raises nothing: %d"
          % (len(converted), len(prose), sum(n for _, n in prose), len(silent)))


def test_every_registered_code_is_RAISED_somewhere_in_the_engine():
    """The registry's other half, over the whole tree rather than one module. A code listed and
    never raised is the same lie with a citation as a code raised and never listed."""
    raised = set()
    for d in ("src/engine", "scripts"):               # NOT tests/ — asserting a code is not raising it
        base = os.path.join(REPO, *d.split("/"))
        for f in sorted(os.listdir(base)):
            if f.endswith(".py"):
                raised |= _raise_audit(os.path.join(base, f))[0]
    orphan = sorted(c for c in codes.CODES if c not in raised)
    check("every-REGISTERED-code-is-raised-somewhere", not orphan,
          "registered and never raised: %s" % orphan)


def main():
    print("test_errors.py - the coded refusal channel and the two-way registry")
    # DISCOVERED, NOT LISTED. This eight-name tuple is the sixth instance of that shape found in
    # two days, and it swallowed the counter-instrument added on 2026-09-02 — a test written
    # SPECIFICALLY to catch a measurement blind spot, itself never run, in the file about
    # measurement blind spots. Ordered by definition line so the printed run reads in file order.
    for t in sorted((v for k, v in globals().items()
                     if k.startswith("test_") and callable(v)
                     # THE ONLY LEGAL EXCLUSION: the baseline runner is invoked below under an env
                     # guard because it shells out to the whole suite. Any other name added here is
                     # the hand-written list growing back, which is what swallowed the
                     # counter-instrument on 2026-09-02.
                     and k != "test_the_real_suite_runner_is_the_baseline"),
                    key=lambda f: f.__code__.co_firstlineno):
        # PER-TEST ISOLATION. A bare `t()` let the FIRST raiser kill every test after it — which is
        # how this very file reported NOTHING AT ALL when the legacy branch was retired and three of
        # its own tests started raising. Fifth suite given this on 2026-09-02.
        try:
            t()
        except Exception as e:                                # noqa: BLE001 — a harness reports
            check("%s RAISED %s" % (t.__name__, type(e).__name__), False, str(e)[:130])
    if not os.environ.get("SWE_ERRORS_SELFTEST"):
        test_the_real_suite_runner_is_the_baseline()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
