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
    if name in _CACHE:
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
    out = []
    for d in DOC_DIRS:
        full = os.path.join(REPO, d)
        if os.path.isdir(full):
            out += [os.path.join(d, f) for f in sorted(os.listdir(full)) if f.endswith(".md")]
    return out + [f for f in ROOT_DOCS if os.path.isfile(os.path.join(REPO, f))]


def _decl(sym):
    """def / class / module-level assignment. `_ALLELE = {` is as much a definition as a def, and a
    checker that only knows `def` reports every constant table as missing."""
    s = re.escape(sym)
    return re.compile(r"\s*(?:def|class)\s+%s\b|\s*%s\s*(?::[^=]+)?=" % (s, s))


def test_file_line_citations():
    """`module.py:NN` — the file exists and the line is in range."""
    print("\n[1] FILE:LINE — every cited file exists and is long enough")
    bad, seen = [], 0
    for doc in _docs():
        text = io.open(os.path.join(REPO, doc), encoding="utf-8").read()
        for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*\.(?:py|sql)):(\d+)(?:-(\d+))?", text):
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
    bad, seen = [], 0
    for doc in _docs():
        text = io.open(os.path.join(REPO, doc), encoding="utf-8").read()
        for m in re.finditer(r"`([A-Za-z_][A-Za-z0-9_.]*)`\s*:(\d+)", text):
            sym, ln = m.group(1).split(".")[-1], int(m.group(2))
            row = text[text.rfind("\n", 0, m.start()) + 1:m.start()]
            fns = list(dict.fromkeys(re.findall(r"([A-Za-z_][A-Za-z0-9_]*\.py)", row)))
            cands = [(fn, _lines(_find(fn))) for fn in fns if _find(fn)]
            if not cands:
                continue
            seen += 1
            pat = _decl(sym)
            if any(ln <= len(ls) and pat.match(ls[ln - 1]) for _fn, ls in cands):
                continue
            where = ["%s: %s" % (fn, [i + 1 for i, l in enumerate(ls) if pat.match(l)] or "absent")
                     for fn, ls in cands]
            bad.append("%s: `%s` :%d -> %s" % (doc, sym, ln, "; ".join(where)))
    print("       %d symbol citation(s) resolvable to a cited file" % seen)
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
