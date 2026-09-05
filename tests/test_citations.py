"""test_citations.py — the docs' `file.py:NN` references must point at what they claim.

WHY THIS EXISTS. `docs/SPEC-LEDGER.md` is the normative answer to "is this built?", and it answers
with roughly two hundred hand-typed `module.py:NN` citations. Hand-typed references to moving code
are the same defect this repo keeps finding in other clothes — `coherence_probe.py`'s copy of
PRIMARIES, `basis_probe.py`'s ROLE_PAIRS, `consolidation.py`'s `_KNOWN_DIMS`, the verify block's
list of 21 suites, `scene.py`'s `state_fields_read`. Every one was a list that mirrored something
the code already knew, and every one had gone quietly wrong.

Measured 2026-08-23, the first time anyone checked: TWELVE citations in SPEC-LEDGER pointed at the
wrong line, including four in a single row — `compounds.py:45-124 (42 recipes), compose :165,
recognise :195, separability :224` where the truth was 41 recipes at :186 / :216 / :245. A citation
that silently drifts is worse than none: it reads as provenance and is a guess.

WHAT IS CHECKED (mechanical only — this suite cannot read intent):
  1. Every `name.py:NN` / `name.py:NN-MM` names a file that exists and a line in range.
  2. Every `` `symbol` :NN `` in a row that also cites .py files is DEFINED at that line in one of
     them — `def`, `class`, or a module-level assignment.
A row citing several files is satisfied if ANY of them defines the symbol there; the first draft of
this checker took the last-named file and invented four stale refs of its own.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

SEARCH = ("src/engine", "scripts", "tests")
DOC_DIRS = ("docs",)
ROOT_DOCS = ("CLAUDE.md",)

_FAILS = []
_CACHE = {}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "\n        %s" % detail))
    if not ok:
        _FAILS.append(name)


def _find(name):
    """Resolve a cited path. A name carrying a DIRECTORY is taken at its word; a bare basename
    falls back to SEARCH order, which is a guess and is why the qualified form must win."""
    if name in _CACHE:
        return _CACHE[name]
    if "/" in name:
        p = os.path.join(REPO, name)
        _CACHE[name] = p if os.path.isfile(p) else None
        return _CACHE[name]
    hit = None
    for d in SEARCH:
        p = os.path.join(REPO, d, name)
        if os.path.isfile(p):
            hit = p
            break
    _CACHE[name] = hit
    return hit


def _lines(path):
    key = ("L", path)
    if key not in _CACHE:
        _CACHE[key] = io.open(path, encoding="utf-8").read().splitlines()
    return _CACHE[key]


def _docs():
    """Every .md under DOC_DIRS, RECURSIVELY, plus the root docs.

    This used `os.listdir`, which does not descend — so `docs/authoring/` was never walked, and the
    three BLUEPRINT files (the primary authoring guides, ~1800 lines each) plus START-HERE.md had
    their file:line citations checked by nothing, ever. A guard reports on what it READS: the
    checker was green the whole time and the count it printed was the count of what it happened to
    reach. Same shape as `test_self_contained._ROOTS` omitting `.claude` and missing 42 tracked
    files with a leak in one of them."""
    out = []
    for d in DOC_DIRS:
        full = os.path.join(REPO, d)
        for root, _dirs, files in os.walk(full):
            rel = os.path.relpath(root, REPO).replace("\\", "/")
            out += ["%s/%s" % (rel, f) for f in sorted(files) if f.endswith(".md")]
    return sorted(out) + [f for f in ROOT_DOCS if os.path.isfile(os.path.join(REPO, f))]


def _is_binding(line, sym):
    """Is this `sym = other.sym` — a RE-EXPORT, which POINTS AT a definition rather than being one?

    `_decl`'s assignment clause was written for `_ALLELE = {`, a constant whose VALUE is on that
    line. A re-export is a pointer, and the difference is not pedantic: after `bible.py` was split,
    three citations were "corrected" onto its re-export lines and went green while the mechanism
    they describe had moved to `law.py`. SPEC-LEDGER's column answers WHERE THIS IS BUILT, so a
    binding is the wrong answer to it."""
    m = re.match(r"\s*%s\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\.%s\s*(?:#.*)?$" % (sym, sym), line)
    return m.group(1) if m else None


def _decl(sym):
    """def / class / module-level assignment. `_ALLELE = {` is as much a definition as a def, and a
    checker that only knows `def` reports every constant table as missing."""
    s = re.escape(sym)
    return re.compile(r"\s*(?:def|class)\s+%s\b|\s*%s\s*(?::[^=]+)?=" % (s, s))


def test_file_line_citations():
    """`module.py:NN` — the file exists and the line is in range."""
    print("\n[1] FILE:LINE — every cited file exists and is long enough")
    bad, seen, unresolvable, bindings = [], 0, 0, 0
    for doc in _docs():
        text = io.open(os.path.join(REPO, doc), encoding="utf-8").read()
        # THE DIRECTORY THE AUTHOR WROTE IS PART OF THE CITATION. This captured only the BASENAME,
        # so `scripts/scene.py:683` was resolved through SEARCH order to `src/engine/scene.py` — a
        # DIFFERENT 494-line file — and reported nine correct citations as out of range. Discarding
        # the qualifier made the precise form less checkable than the bare one, the same inversion
        # the dotted `module.symbol` citations had. Nearly rewrote nine right citations to satisfy
        # it before checking what the docs actually said.
        for m in re.finditer(r"((?:[A-Za-z_][A-Za-z0-9_]*/)*[A-Za-z_][A-Za-z0-9_]*\.(?:py|sql)):(\d+)(?:-(\d+))?", text):
            fn, lo, hi = m.group(1), int(m.group(2)), int(m.group(3) or 0)
            f = _find(fn)
            seen += 1
            if f is None:
                bad.append("%s: %s -> no such file under %s" % (doc, m.group(0), "/".join(SEARCH)))
            elif lo > len(_lines(f)) or (hi and hi > len(_lines(f))):
                bad.append("%s: %s -> %s has %d lines" % (doc, m.group(0), fn, len(_lines(f))))
    print("       %d citation(s) across %d doc(s)" % (seen, len(_docs())))
    print("       NOTE: this proves only that the line EXISTS. Whether it is the RIGHT line is")
    print("       checked for the symbol-anchored subset in [2] and nowhere else — read the count")
    print("       there before treating a PASS here as 'the citations are correct'.")
    check("every-cited-line-is-in-range", not bad, "\n        ".join(bad))


def test_symbol_citations():
    """`` `symbol` :NN `` — the symbol is DEFINED at that line in one of the row's cited files."""
    print("\n[2] SYMBOL:LINE — the definition is where the doc says it is")
    bad, seen, unresolvable, bindings = [], 0, 0, 0
    for doc in _docs():
        text = io.open(os.path.join(REPO, doc), encoding="utf-8").read()
        # BACKTICKS OPTIONAL, BUT A BARE SYMBOL MUST BE IN CITATION-LIST POSITION. This required
        # backticks until 2026-09-03, and SPEC-LEDGER writes both forms in the SAME ROW: "`_project`
        # :425" was checked while "append_turn :96, fold :431, resume :486" were not — all four
        # stale, one reported.
        #
        # THE FIRST WIDENING MATCHED THE LAST WORD OF A PHRASE and called it a symbol. Of the 23
        # bare `word :NN` citations in SPEC-LEDGER, SIXTEEN are prose anchors — "at :94", "and :24",
        # "of :34", "which :38" — a legitimate convention pointing a sentence at a line in the row's
        # file. That draft compensated with a skip ("absent everywhere means prose"), which is a
        # heuristic pretending to be a rule: it swallowed FIVE real dead citations (bands, phrases,
        # fork, defaults, resolvers), including one in the row being edited at the time.
        #
        # The two conventions are separable EXACTLY, without guessing: a symbol citation is written
        # in a list — after "(" or ", " — and a prose anchor never is. Measured against the doc,
        # that captures every intended symbol and none of the sixteen anchors. So the skip is gone
        # and ABSENT IS A FAILURE AGAIN, for bare and backticked alike.
        for m in re.finditer(r"`([A-Za-z_][A-Za-z0-9_.]*)`\s*:(\d+)"
                             r"|(?:\(|,\s)([A-Za-z_][A-Za-z0-9_]*) +:(\d+)", text):
            raw = m.group(1) or m.group(3)
            sym = raw.split(".")[-1]     # 1,2 = backticked · 3,4 = bare
            ln = int(m.group(2) or m.group(4))
            row = text[text.rfind("\n", 0, m.start()) + 1:m.start()]
            fns = list(dict.fromkeys(re.findall(r"([A-Za-z_][A-Za-z0-9_]*\.py)", row)))
            cands = [(fn, _lines(_find(fn))) for fn in fns if _find(fn)]
            if not cands:
                unresolvable += 1
                continue
            # A DOTTED CITATION NAMES ITS OWN MODULE, and that half was thrown away — so
            # `bible.completeness :218` was satisfied by law.py merely because law.py was also on
            # the row. The qualifier is the author being MORE specific; discarding it made the
            # dotted form LESS checked than the bare one.
            if "." in raw:
                want = raw.rsplit(".", 2)[-2] + ".py"
                if want not in [fn for fn, _ls in cands]:
                    seen += 1
                    bad.append("%s: `%s` :%d -> names module %s, which this row does not cite (%s)"
                               % (doc, raw, ln, want, ", ".join(fn for fn, _ls in cands)))
                    continue
                cands = [(fn, ls) for fn, ls in cands if fn == want]
            seen += 1
            pat = _decl(sym)
            hit = [(fn, ls) for fn, ls in cands if ln <= len(ls) and pat.match(ls[ln - 1])]
            if hit:
                src = next((b for b in (_is_binding(ls[ln - 1], sym) for _fn, ls in hit) if b), None)
                if src:
                    bindings += 1
                    bad.append("%s: `%s` :%d -> %s:%d is a re-export binding (`%s = %s.%s`), not a "
                               "definition — cite where it is BUILT"
                               % (doc, sym, ln, hit[0][0], ln, sym, src, sym))
                continue
            where = ["%s: %s" % (fn, [i + 1 for i, l in enumerate(ls) if pat.match(l)] or "absent")
                     for fn, ls in cands]
            bad.append("%s: `%s` :%d -> %s" % (doc, sym, ln, "; ".join(where)))
    # WHAT IT DID NOT READ, PRINTED BESIDE WHAT IT DID. A green result is a claim about COVERAGE
    # before it is a claim about content. Prose anchors ("... at :61") name no symbol and are
    # excluded by construction; a citation on a row naming no .py file cannot be resolved at all.
    # Neither is a defect, both are invisible unless counted, and an uncounted exclusion is exactly
    # how this check's first bare-symbol branch hid five dead citations behind a passing run.
    print("       %d symbol citation(s) checked · %d unresolvable (row names no .py file)"
          % (seen, unresolvable))
    check("every-symbol-is-at-its-cited-line", not bad, "\n        ".join(bad))


def test_the_checker_can_fail():
    """The control. A checker that has only ever passed has not been shown to be able to fail —
    `a-fired-check-that-reports-clean` is a standing sticky here for a reason."""
    print("\n[3] CONTROL — the checker catches a citation it should")
    ls = _lines(_find("bonds.py"))
    pat = _decl("observe")
    real = [i + 1 for i, l in enumerate(ls) if pat.match(l)]
    check("bonds.observe-is-found-somewhere", bool(real), real)
    check("and-not-at-a-line-it-is-not-at", not pat.match(ls[0]), ls[0][:60])


def main():
    print("test_citations.py — the docs' references, checked against the tree")
    for t in (test_file_line_citations, test_symbol_citations, test_the_checker_can_fail):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
