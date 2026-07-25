#!/usr/bin/env python3
"""test_no_private_content.py — the repo carries no private content.

CLAUDE.md hard rule 1 already says it: "REAL BOOKS NEVER LIVE IN THIS REPO —
they live as linked Obsidian notes in the author's vault." That rule was stated
and then violated, twice: once before a scrub commit titled "keep the engine
repo corpus-agnostic — no book IP", and again after it. It regrew because
nothing enforced it — `test_portability.py`'s sweep covers only `src/engine/`,
leaving docs/, scripts/ and tests/ unguarded.

This is the enforcement. A rule without a guard is a rule that comes back.

SCOPE: every git-tracked file. Untracked and gitignored paths (runs/*.db,
staging/, .env) never reach a remote, so they are not the disclosure surface.

WORD-BOUNDARY matching, not substring. "declaration" contains "clara"; a
substring sweep would flag legitimate prose forever and be switched off inside
a week. The negative control below asserts both directions.

DISTINCT from test_portability.py on purpose: that test proves an ARCHITECTURAL
property (the machine carries no content, scoped to src/engine). This proves an
IP property (the repo carries no private content, scoped to the whole tree).
One red test should mean exactly one thing.

Stdlib only, script-style. Exit 0 = clean.
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Private-book cast, the book's identity, and machine-local paths.
# Extend this list; never add an exception to it. An enforcement sweep with
# hand-waved exceptions rots, and the exception list becomes the leak.
_BANNED = (
    # the private cast — FIRST NAMES AND SURNAMES SEPARATELY.
    # Full names alone are a false-negative hole: the leak this guard was written
    # after referred to the cast as "Kieth, Brian, Ryker, Valeria, Ben", which a
    # full-name list would have sailed straight past.
    "anya", "soren", "alistair", "elara", "clara", "uterkin",
    "aris", "squeen", "ryker", "valeria", "kieth", "thrawn",
    "pueg", "haze", "vance", "brian",
    # Bare "ward" was tried and REMOVED on evidence: it produced 8 hits, all of
    # them the ordinary English word ("the-ward" sickroom in the healer fixture,
    # "mentor-and-ward"), and 0 real ones. A token that fires only on correct
    # content is how a guard gets switched off — the same alert-fatigue failure
    # that kills any check nobody trusts. Coverage is kept by the full name below.
    # Bare "ben" is omitted for the same reason. This is a MEASURED exclusion, not
    # a convenience exception; re-add either only with a true positive to justify it.
    "ben ward",
    # the book's identity
    "a small act of malice",
    # machine-local paths / operator identity
    "claude flow/vault", "c:/users/willi", "claude-suite/.env",
)

# This file necessarily names the tokens it bans. It is the ONLY exemption, and
# it exists because the guard cannot be written without naming what it guards.
# Do not add a second one: an enforcement sweep with exceptions rots, and the
# exception list becomes the leak. (`.depth/` was briefly exempted here; it is
# now gitignored instead — untracking beats exempting.)
_SELF = os.path.basename(__file__)

_TEXT_EXT = (".py", ".md", ".sql", ".json", ".jsonl", ".txt", ".yaml", ".yml",
             ".toml", ".cfg", ".ini", ".sh", ".bat", ".gitignore")


def _patterns():
    return [(tok, re.compile(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(tok))) for tok in _BANNED]


def _tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise RuntimeError("git ls-files failed — cannot determine the disclosure surface")
    files = []
    for rel in out.stdout.splitlines():
        rel = rel.strip()
        if not rel or os.path.basename(rel) == _SELF:
            continue
        if rel.endswith(_TEXT_EXT) or "." not in os.path.basename(rel):
            files.append(rel)
    return files


def _scan(files, pats):
    hits = []
    for rel in files:
        path = os.path.join(REPO, rel)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for n, line in enumerate(fh, 1):
                    low = line.lower()
                    for tok, rx in pats:
                        if rx.search(low):
                            hits.append((rel, n, tok))
        except (OSError, UnicodeDecodeError):
            continue
    return hits


def test_negative_control():
    """The guard must be provably able to fire — and provably not fire on a
    lookalike. Without this the sweep is indistinguishable from an inert one."""
    pats = _patterns()
    fired = [tok for tok, rx in pats if rx.search("the messenger found anya at dusk")]
    assert "anya" in fired, "NEGATIVE CONTROL FAILED: the sweep did not detect a banned token"
    false = [tok for tok, rx in pats if rx.search("see the declaration in section 3")]
    assert not false, "FALSE POSITIVE: 'declaration' matched %s — substring bleed" % false
    quiet = [tok for tok, rx in pats if rx.search("maren tended bryn through the fever")]
    assert not quiet, "FALSE POSITIVE: the public fixture cast matched %s" % quiet
    return "negative control: fires on a banned token, silent on 'declaration' and the fixture cast"


def test_no_private_content_in_tracked_files():
    files = _tracked_files()
    hits = _scan(files, _patterns())
    if hits:
        shown = "\n".join("    %s:%d  %s" % h for h in hits[:25])
        more = "\n    ... and %d more" % (len(hits) - 25) if len(hits) > 25 else ""
        raise AssertionError(
            "%d private-content hit(s) across %d file(s):\n%s%s"
            % (len(hits), len({h[0] for h in hits}), shown, more))
    return "scanned %d tracked files, zero private-content hits" % len(files)


def main():
    print("test_no_private_content.py — the repo carries no private content\n")
    failed = 0
    for t in (test_negative_control, test_no_private_content_in_tracked_files):
        try:
            detail = t()
            print("  PASS  %s\n          %s" % (t.__name__, detail))
        except Exception as e:
            failed += 1
            print("  FAIL  %s\n          %s" % (t.__name__, e))
    print("\nVERDICT: %s" % ("PASS" if not failed else "FAIL"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
