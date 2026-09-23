"""test_self_contained.py — the engine STANDS ALONE.

The twin of `test_no_private_content.py`, guarding the other direction.

That suite stops book content leaking INTO the repo. Nothing stopped the repo pointing OUT — and
it does: seven design docs reach into a private sibling project, one of them naming an external
file as "the definitive record" of the character model. A design whose rationale lives in a
directory that is not in this repo is not a design this repo owns; clone SWE alone and the
reasoning is unreadable.

**The rule (the author, 2026-08-22):** "SWE is corpus agnostic, it needs to stand on its own without
any other prose or books. We can test and refine with info but it shouldn't require any outside
source to define it."

So: nothing in this repo may DEPEND on a path outside it. The distinction that matters is
dependency vs credit —

  DEPENDENCY (banned): "reuse its STATE fields", "X is the definitive record", "borrowed from
      <path>" where the borrowed content is not restated here. The reader must go elsewhere.
  CREDIT (fine, once inlined): "the idea came from X" where everything needed is on this page.

Mechanically we cannot read intent, so the test bans the PATH SHAPES that only ever appear in
dependencies: sibling-project names, machine-absolute paths, and home-relative paths. Credit that
names a project without a path survives. Env var NAMES (SWE_BOOKS, SWE_ENV_FILE) are the correct
indirection and are always allowed — they are how a machine-local path is referenced without
hardcoding one.

Extend _OUTWARD when a new sibling project appears. Never add an exception: an exception list is
how the other guard rotted (see test_no_private_content.py).
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

# Path shapes that can only be a dependency on something outside this repo.
_OUTWARD = [
    (r"the-writers-desk|writer.s\s+desk",  "private sibling project"),
    (r"Claude\s+Flow",                    "the author's machine-local workspace"),
    (r"[A-Za-z]:[\\/]Users[\\/]",         "machine-absolute path"),
    (r"(?<![\w-])/Users/",                "machine-absolute path (posix)"),
    # `~/.claude/` is EXEMPT and this is a carve-out, stated plainly rather than hidden. The test
    # applied is portability, not secrecy: every user of the agent tooling has `~/.claude/`, so a
    # doc citing it stays true on a fresh clone. `~/anything-else/` is one person's machine.
    (r"(?<![\w.])~/(?!\.claude(?:[/\s]|$))",  "home-relative path"),
    (r"Scribe\s+Lang|IDE\.code-workspace", "external sibling project"),
    (r"vault[\\/]books[\\/](?!<)",        "a concrete book vault (use $SWE_BOOKS)"),
]

# Directories that ARE the repo's own definition. runs/ and .depth/ are scratch; .git is not ours.
_ROOTS = ("docs", "src", "scripts", "tests", ".claude")
_SKIP_DIRS = {".git", "__pycache__", "runs", ".depth", "staging", ".pytest_cache", ".memsearch"}
_TEXT = (".md", ".py", ".json", ".txt", ".yaml", ".yml", ".toml", ".cfg")

# This file necessarily quotes the shapes it bans.
_SELF = os.path.basename(__file__)

# A guard's own forbidden-vocabulary list must CONTAIN the literals it forbids — that is the
# semantic opposite of depending on them. Skipped by STRUCTURE, not by filename: only lines inside
# a list/tuple literal assigned to a _BANNED/_OUTWARD/_PRIVATE-shaped name. Prose can never qualify,
# so this cannot grow into the exception list that rots a guard.
_VOCAB_OPEN = re.compile(r"^\s*_(?:BANNED|OUTWARD|PRIVATE)\w*\s*=\s*[\[(]")


def _vocab_lines(lines):
    """-> set of 1-based line numbers inside a guard's forbidden-vocabulary literal."""
    inside, depth, out = False, 0, set()
    for n, line in enumerate(lines, 1):
        if not inside and _VOCAB_OPEN.match(line):
            inside, depth = True, 0
        if inside:
            out.add(n)
            depth += line.count("[") + line.count("(") - line.count("]") - line.count(")")
            if depth <= 0 and n > 1 or (depth <= 0 and not _VOCAB_OPEN.match(line)):
                inside = False
    return out


def _files():
    out = []
    for root in _ROOTS:
        d = os.path.join(REPO, root)
        if not os.path.isdir(d):
            continue
        for dirpath, dirnames, filenames in os.walk(d):
            dirnames[:] = [x for x in dirnames if x not in _SKIP_DIRS]
            for fn in filenames:
                if fn.endswith(_TEXT) and fn != _SELF:
                    out.append(os.path.join(dirpath, fn))
    for fn in os.listdir(REPO):                      # root-level .md (README, CLAUDE.md)
        if fn.endswith(".md"):
            out.append(os.path.join(REPO, fn))
    return sorted(out)


def sweep():
    """-> [(relpath, lineno, why, line)] — every outward dependency, in file order."""
    hits = []
    pats = [(re.compile(p, re.IGNORECASE), why) for p, why in _OUTWARD]
    for path in _files():
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = os.path.relpath(path, REPO).replace("\\", "/")
        skip = _vocab_lines(lines) if path.endswith(".py") else set()
        for n, line in enumerate(lines, 1):
            if n in skip:
                continue
            for rx, why in pats:
                if rx.search(line):
                    hits.append((rel, n, why, line.strip()[:120]))
                    break
    return hits


def main():
    print("[1] THE ENGINE STANDS ALONE — no path-dependency outside this repo")
    hits = sweep()
    n_files = len(_files())
    if hits:
        by_file = {}
        for rel, n, why, line in hits:
            by_file.setdefault(rel, []).append((n, why, line))
        for rel in sorted(by_file):
            print("\n  %s" % rel)
            for n, why, line in by_file[rel]:
                print("    :%-4d %-42s %s" % (n, why, line))
        print("\n  FAIL  %d outward dependenc(ies) across %d file(s), %d scanned"
              % (len(hits), len(by_file), n_files))
        print("  Each must be INLINED (restate what is needed here) or DEMOTED to credit that")
        print("  names no path. Never add an exception — that is how the other guard rotted.")
        return 1
    print("  PASS  %d files scanned, zero outward dependencies" % n_files)
    print("\nVERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
