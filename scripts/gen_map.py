"""gen_map.py — regenerate docs/MAP.md's inventory tables from the tree itself.

WHY THIS IS A SCRIPT AND NOT AN INSTRUCTION. `MAP.md` claimed its inventories "cannot drift from
the code without the code changing" and told the reader to regenerate them with a shell one-liner
pasted into the doc. Nobody runs a one-liner in a doc. Measured 2026-08-24: the module table listed
18 of 24 modules, the docs table 49 of 62, the suites table 29 of 40 — and MAP is the file every
session is instructed to read FIRST, so the routing table that exists to stop people re-deriving
things was itself hiding six modules, thirteen docs and eleven suites.

The claim was also only half true. A RENAMED title line does surface, because the row is built from
it. An ADDED file does not, because nothing re-runs the generator. Additions were the whole failure.

`--check` exits non-zero when the file on disk disagrees with the tree, which is what
`tests/test_map.py` runs, so the inventories are now load-bearing rather than aspirational.
"""
import argparse
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(REPO, "docs", "MAP.md")


def _title(path):
    """A doc's own first heading, minus the '# name — ' prefix it repeats."""
    with io.open(path, encoding="utf-8") as fh:
        first = fh.readline().strip()
    first = re.sub(r"^#+\s*", "", first)
    return first.split(" — ", 1)[1].strip() if " — " in first else first


def _docstring(path):
    """A module's one-line purpose: its docstring's first line, minus the 'name.py — ' prefix."""
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r'^\s*(?:"""|\'\'\')(.*)', text)
    if not m:
        return ""
    line = m.group(1).strip()
    return line.split(" — ", 1)[1].strip() if " — " in line else line


def _lines(path):
    with io.open(path, encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def _rows(paths, describe):
    """No LINE COUNT column. It used to carry one, and it made MAP go stale on every edit to any
    file — so the guard cried wolf on ordinary work and the only way to live with it was to stop
    believing it. The table's job is WHAT OWNS WHAT; the counts belonged to CLAUDE.md's 500-line
    rule, which is now enforced across every module by `tests/test_map.py` instead of noted for
    24 of them here and actually checked for one (`bonds`, in test_bonds.py).

    What remains changes only when a file is ADDED, REMOVED or RETITLED — which is the drift this
    inventory exists to catch."""
    return ["| `%s` | %s |" % (os.path.splitext(os.path.basename(p))[0], describe(p))
            for p in paths]


def _listing(d, pattern, exclude=()):
    return sorted(os.path.join(REPO, d, f) for f in os.listdir(os.path.join(REPO, d))
                  if re.match(pattern, f) and f not in exclude)


def sections():
    """(heading-regex, replacement-heading, rows) per generated table.

    MAP.md is EXCLUDED from its own docs table. Not tidiness — a fixed-point requirement. The table
    carries each doc's line count, so listing MAP inside it means every regeneration changes MAP's
    length, which changes the row describing MAP, which changes its length again. Self-inclusion is
    exactly why this inventory could not be checked mechanically before.
    """
    docs = [p for p in _listing("docs", r".*\.md$") if os.path.basename(p) != "MAP.md"]
    mods = _listing("src/engine", r".*\.py$", exclude=("__init__.py",))
    tests = _listing("tests", r"test_.*\.py$")
    return [
        (r"^## docs/ — \d+ design docs \(normative for what SHOULD BE\)$",
         "## docs/ — %d design docs (normative for what SHOULD BE)" % len(docs),
         _rows(docs, _title)),
        (r"^## src/engine/ — \d+ modules \(normative for what IS\)$",
         "## src/engine/ — %d modules (normative for what IS)" % len(mods),
         _rows(mods, _docstring)),
        (r"^## tests/ — \d+ suites \(each is a PROOF of the gate it names\)$",
         "## tests/ — %d suites (each is a PROOF of the gate it names)" % len(tests),
         _rows(tests, _docstring)),
    ]


def render(current):
    """Rewrite each generated table in place, leaving ROUTING, VOCABULARY and prose untouched."""
    out = current
    for pat, heading, rows in sections():
        m = re.search(pat, out, re.M)
        if not m:
            raise SystemExit("gen_map: no section matching %r — MAP.md's headings changed shape" % pat)
        start = m.start()
        rest = out[m.end():]
        nxt = re.search(r"^## ", rest, re.M)
        end = m.end() + (nxt.start() if nxt else len(rest))
        table = "\n".join([heading, "", "| %s | lines | owns |" % heading.split("/")[0][3:].strip(),
                           "|---|---|---|"] + rows)
        out = out[:start] + table + "\n\n" + out[end:]
    # THE .claude/ COUNTS, which were hand-typed and rotted exactly as the tables had. Found
    # 2026-08-24: the line read "10 skills:" above a list of eleven, in the same file whose
    # generated halves had just been given a drift guard. The hand-maintained half drifted anyway,
    # which is the whole argument for deriving rather than describing.
    for sub, word in (("agents", "agents"), ("skills", "skills")):
        d = os.path.join(REPO, ".claude", sub)
        if os.path.isdir(d):
            n = len([x for x in os.listdir(d)
                     if (x.endswith(".md") if sub == "agents" else os.path.isdir(os.path.join(d, x)))])
            out = re.sub(r"\*\*\d+ %s:\*\*" % word, "**%d %s:**" % (n, word), out, count=1)

    # the header's own counts, which repeat the section counts and rotted alongside them
    counts = {"design docs": len(_listing("docs", r".*\.md$")),
              "modules": len(_listing("src/engine", r".*\.py$", exclude=("__init__.py",))),
              "suites": len(_listing("tests", r"test_.*\.py$"))}
    for word, n in counts.items():
        out = re.sub(r"\d+ %s" % re.escape(word), "%d %s" % (n, word), out, count=1)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if MAP.md disagrees with the tree; write nothing")
    args = ap.parse_args()
    current = io.open(MAP, encoding="utf-8").read()
    fresh = render(current)
    if args.check:
        if fresh != current:
            print("MAP.md is STALE — run: python scripts/gen_map.py")
            return 1
        print("MAP.md matches the tree")
        return 0
    io.open(MAP, "w", encoding="utf-8", newline="").write(fresh)
    print("regenerated docs/MAP.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
