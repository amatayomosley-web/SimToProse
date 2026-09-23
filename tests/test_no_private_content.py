#!/usr/bin/env python3
"""test_no_private_content.py — the repo carries no private content.

CLAUDE.md hard rule 1 already says it: "REAL BOOKS NEVER LIVE IN THIS REPO —
they live as linked Obsidian notes in the author's vault." That rule was stated
and then violated, twice: once before a scrub commit titled "keep the engine
repo corpus-agnostic — no book IP", and again after it. It regrew because
nothing enforced it — `test_portability.py`'s sweep covers only `src/engine/`,
leaving docs/, scripts/ and tests/ unguarded.

This is the enforcement. A rule without a guard is a rule that comes back.

SCOPE NOTE — THIS GUARD BINDS THE INSTANCE TOO (changed 2026-08-21). It used to
say a working instance was EXPECTED TO FAIL, because the author's cast and title
"legitimately live there", so it ran only as a pre-upstream check. That exemption
is retired: the author, 2026-08-21 — "No real cast, hard separation."

The old reasoning failed in a way worth recording, because it is the reason this
file exists at all. A guard that is expected to fail is a guard nobody reads, and
under it the leak grew to 336 occurrences across 20 files — including a private
surname inside src/engine/ (which test_portability.py missed, because it swept
only FIXTURE tokens), and an entire scene from a private novel serving as
scene.py's DEFAULT, so every no-argument run played someone's book.

This suite is now in CLAUDE.md's verify block and must stay green. Fix a failure
by scrubbing the ENGINE, never by loosening the list. Books live in the vault.

SCOPE: everything git would offer to commit -- tracked files PLUS untracked
files that are not gitignored. GITIGNORED paths (runs/*.db, staging/, .env)
are excluded and that is correct: they never reach a remote.

The tracked-only scope was a HOLE, found 2026-08-22. A newly written doc is
untracked until it is staged, so it was invisible to this sweep while sitting
in the working tree -- and one did: a review written that day named a book
character 24 times and this suite reported PASS over 177 files. Untracked-and-
not-ignored is a different set from ignored; the first is on its way to a
commit, the second never is.

WORD-BOUNDARY matching, not substring. Ordinary English words contain short
names as substrings, so a substring sweep would flag legitimate prose forever
and be switched off inside a week. The negative control below asserts both
directions, burying a banned token inside a longer word to prove it stays quiet.

DISTINCT from test_portability.py on purpose: that test proves an ARCHITECTURAL
property (the machine carries no content, scoped to src/engine). This proves an
IP property (the repo carries no private content, scoped to the whole tree).
One red test should mean exactly one thing.

Stdlib only, script-style. Exit 0 = clean.
"""
import collections
import os
import re
import subprocess
import shutil
import tempfile
import io
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Private-book cast, the book's identity, and machine-local paths.
# Extend this list; never add an exception to it. An enforcement sweep with
# hand-waved exceptions rots, and the exception list becomes the leak.
# THE PRIVATE HALF OF THIS LIST NO LONGER LIVES IN THIS REPO.
#
# It used to be a tuple of literal strings which were, by construction, the cast names,
# surnames, place names and book titles of the owner's books — sitting in a tracked file that is
# exempt from the sweep it feeds. CLAUDE.md hard rule 1 says nothing about a book "cast,
# surnames, titles, place names, or PLOT — appears in this repo". This list was exactly that,
# and the rule had never been turned on the guard that enumerates it.
#
# Measured 2026-08-24, rewriting all 126 commits to purge private terms: after the scrub, ONE
# file in the working tree had changed — this one. Everything else was already clean. Cleaning
# the history around a file that names them at HEAD does not clean the repo.
#
# The terms now live beside the BOOKS, which is where book-derived data belongs.
_TERMS_ENV = "SWE_PRIVATE_TERMS"


def _private_terms():
    """Machine-local private terms -> (tokens, source-description).

    Returns an EMPTY list and says so when the file is absent. It does not fall back silently:
    the defect this whole guard exists around was a sweep reporting clean over ground it never
    covered, and a quiet fallback would rebuild that exact failure one level up.
    """
    path = os.environ.get(_TERMS_ENV)
    if not path:
        root = os.environ.get("SWE_BOOKS")
        path = os.path.join(os.path.dirname(root), "private-terms.txt") if root else None
    if not path or not os.path.isfile(path):
        return [], ("NO private-terms file (%s unset and none beside $SWE_BOOKS) — this run "
                    "checked MACHINE PATHS ONLY and proves nothing about cast or titles" % _TERMS_ENV)
    toks = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#")[0].strip().lower()
            if line:
                toks.append(line)
    return toks, "%d private term(s) from %s" % (len(toks), path)


# Machine-local paths, as SHAPES rather than as one operator's actual path.
#
# These used to be three literals — a Windows home directory with the operator's username in it,
# a workspace folder name, and a path to an env file. That was the last identifying string left in
# the repo after the private terms moved out, and this repo is intended to go public: "the guard
# names the person it protects" is a poor last line. Generalising also makes the guard STRONGER,
# because it now catches any contributor's home path rather than only the one that already leaked.
#
# Matched as regexes, not as tokens, so `_patterns` does not word-boundary-wrap them.
_GENERIC_PATH_SHAPES = (
    (r"[a-z]:[\/]users[\/][a-z0-9._-]+", "a Windows home directory"),
    (r"(?<![a-z0-9])/home/[a-z0-9._-]+", "a Linux home directory"),
    (r"(?<![a-z0-9])/" + "users" + r"/[a-z0-9._-]+", "a macOS home directory"),
    (r"[a-z0-9._-]*[\/]\." + "env" + r"(?![a-z0-9])", "a path to an env file"),    # assembled: now swept
)
_BANNED_GENERIC = ()

_PRIVATE, _PRIVATE_SOURCE = _private_terms()
_BANNED = _BANNED_GENERIC + tuple(_PRIVATE)


# THIS FILE IS SWEPT LIKE EVERY OTHER (since 2026-09-23). It used to exempt itself because it had to
# spell the names it banned; the names moved out to the vault on 2026-08-24, and the exemption stayed
# behind with nothing left to protect. On 2026-09-23 a fourth read found a private book's note name in
# a docstring example written here that day, inside the one file no sweep read. There is no exemption.
_TEXT_EXT = (".py", ".md", ".sql", ".json", ".jsonl", ".txt", ".yaml", ".yml",
             ".toml", ".cfg", ".ini", ".sh", ".bat", ".gitignore")

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _normalise(text):
    """What every private-content check reads: identifiers split at CamelCase humps, lower-cased, Windows
    separators turned forward. Until 2026-09-23 the checks read `text.lower()`, so a name fused into an
    CamelCase identifier was one word to the matcher and matched nothing — the fourth read found one
    that had passed all three guards."""
    return _CAMEL.sub(" ", text).lower().replace(chr(92), "/")


def _token_rx(tok):
    """One private term, word-bounded, with its separators loosened: a term the list spells with `-` or a
    space also matches `_`, `-` or whitespace in the text, so `x-y` in the list catches `x_y`, `x y` and
    (after `_normalise`) `XY` in an identifier."""
    body = r"[-_\s]+".join(re.escape(p) for p in re.split(r"[-_\s]+", tok) if p)
    return re.compile(r"(?<![a-z0-9])%s(?![a-z0-9])" % body)


def _patterns():
    """Private terms match as WORDS; machine paths match as SHAPES.

    The private half is literal and word-bounded — a name is a name — read against `_normalise`d text.
    The generic half is a set of regexes describing what a machine-local path LOOKS like, so the guard
    names no operator and catches any contributor's home directory rather than only the one that leaked.
    """
    pats = [(tok, _token_rx(tok)) for tok in _BANNED]
    pats += [(label, re.compile(rx)) for rx, label in _GENERIC_PATH_SHAPES]
    return pats


def _tracked_files():
    # tracked + untracked-but-not-ignored = the set git would offer to commit. --exclude-standard
    # keeps .gitignore honoured, so runs/*.db and staging/ stay out.
    listed = []
    for args in (["git", "ls-files"],
                 ["git", "ls-files", "--others", "--exclude-standard"]):
        out = subprocess.run(args, cwd=REPO, capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
        if out.returncode != 0:
            raise RuntimeError("%s failed — cannot determine the disclosure surface" % " ".join(args))
        listed.extend(out.stdout.splitlines())
    files = []
    for rel in listed:
        rel = rel.strip()
        if not rel:
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
                    low = _normalise(line)
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
    # A FRESH CLONE HAS NO PRIVATE TERMS, and must still be able to run this suite — the repo is
    # meant to be cloned and run out of the box. So the control fires on whatever list this
    # machine actually has: a private token when one is configured, a machine path otherwise.
    # It never passes vacuously; there is always a token it must detect.
    if _PRIVATE:
        probe, expect = "the messenger found %s at dusk" % _PRIVATE[0], _PRIVATE[0]
    else:
        # ASSEMBLED at runtime, never spelled out: a literal machine path here is the very thing
        # `test_self_contained` bans, and writing one tripped that guard immediately.
        expect = "a Windows home directory"
        probe = "see " + "c:" + "/" + "users" + "/" + "someone" + "/notes.md"
    fired = [tok for tok, rx in pats if rx.search(probe)]
    assert expect in fired, ("NEGATIVE CONTROL FAILED: the sweep did not detect %r, a token that "
                             "IS on this run's list (%s)" % (expect, _PRIVATE_SOURCE))
    # THE LOOKALIKE IS BUILT, never spelled. An English word picked because it hides a banned name
    # points straight at that name, so the substring-bleed probe buries one of THIS run's own
    # tokens inside a longer word instead; on word boundaries it must stay silent.
    host = next((t for t in _PRIVATE if t.isalpha()), None)
    lookalike = "see the re%sment in section 3" % host if host else "see the note in section 3"
    false = [tok for tok, rx in pats if rx.search(lookalike)]
    assert not false, "FALSE POSITIVE: a token buried in a longer word matched %s — substring bleed" % false
    quiet = [tok for tok, rx in pats if rx.search("maren tended bryn through the fever")]
    assert not quiet, "FALSE POSITIVE: the public fixture cast matched %s" % quiet
    return ("negative control: fires on %r, silent on a token buried in a longer word and on the "
            "fixture cast" % expect)


def test_the_sweep_can_see_where_the_leak_was():
    """COVERAGE — the thing `test_negative_control` never tested.

    On 2026-08-24 this sweep was found to have certified a tree that was not clean. A TRACKED file,
    .claude/skills/starting-a-book/SKILL.md, carried an operator machine path written with Windows
    separators, and the sweep reported zero hits for three days, inside the verify block, quoted in
    CLAUDE.md as proof the tree was clean. THREE independent blind spots, each sufficient alone:

      1. `.claude` was not in test_self_contained._ROOTS, so the file was never walked. 42 tracked
         files were invisible to a guard CLAUDE.md calls the rule itself.
      2. `_scan` lower-cased but did not normalise separators, so a token written with forward
         slashes could not match a path written with backslashes.
      3. The book slug involved was not in _BANNED.

    `test_negative_control` passed the whole time. It proves the PATTERNS fire against a string
    literal and says nothing about WHICH FILES are read. The distance between "the regex works" and
    "the regex was pointed at the file" is where this lived.
    """
    # A SYNTHETIC token, not a real one. Any genuine banned string written here as bait is itself
    # flagged by `test_self_contained` as a machine-local reference — two earlier drafts of this
    # control tripped that guard, which is the two sweeps correctly working against each other. A
    # made-up token exercises `_scan`'s normalisation and belongs to nobody.
    bait_token = "zzq-fixture/marker"
    bait_pats = [(bait_token, _token_rx(bait_token))]

    # EXERCISE `_scan`; DO NOT RE-IMPLEMENT IT. The first draft normalised the string itself and
    # asserted the token matched — so deleting the normalisation from `_scan` left it GREEN. A
    # control that performs the work under test instead of calling it proves only that its author
    # can perform the work. Caught by re-breaking the code and watching this stay green.
    tmp = tempfile.mkdtemp(prefix="swe_leakctl_")
    try:
        bait = os.path.join(tmp, "bait.md")
        io.open(bait, "w", encoding="utf-8").write(
            chr(92).join(["zzq-fixture", "marker"]) + chr(10))   # same token, other separator
        fired = _scan([os.path.relpath(bait, REPO)], bait_pats)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert fired, ("NORMALISATION LOST: _scan matched a forward-slash token against a file that "
                   "spells it with backslashes, and no longer does. That is exactly how the "
                   "confirmed exposure hid for three days.")

    import test_self_contained as SC
    assert ".claude" in SC._ROOTS, (
        "COVERAGE LOST: .claude is not scanned. The agent overlay is tracked content, and the one "
        "confirmed private-content exposure in this repo was inside it.")

    tracked = _tracked_files()
    claude = [f for f in tracked if f.replace(chr(92), "/").startswith(".claude/")]
    assert claude, ("no .claude file reached the tracked-file list — the sweep is walking a tree "
                    "that does not contain the overlay")
    assert os.path.basename(__file__) in {os.path.basename(f) for f in tracked}, (
        "COVERAGE LOST: this file is exempt from its own sweep again — a private name sat in it unseen "
        "on 2026-09-23 for exactly that reason")
    return ("coverage: %d .claude file(s) swept; a backslash-spelled token still fires" % len(claude))


def test_no_private_content_in_tracked_files():
    files = _tracked_files()
    hits = _scan(files, _patterns())
    if hits:
        shown = "\n".join("    %s:%d  %s" % h for h in hits[:25])
        more = "\n    ... and %d more" % (len(hits) - 25) if len(hits) > 25 else ""
        raise AssertionError(
            "%d private-content hit(s) across %d file(s):\n%s%s"
            % (len(hits), len({h[0] for h in hits}), shown, more))
    return ("scanned %d tracked files, zero private-content hits\n          [terms] %s"
            % (len(files), _PRIVATE_SOURCE))


# ---- THE LIST MUST KEEP UP WITH THE BOOKS (2026-09-23, gate leak-guards) ----------------------------
#
# Every check above is exactly as good as the private-terms list, and on 2026-09-23 that list was found
# 53 names behind the books: a place name from a private book had sat on the public remote for weeks
# under a sweep that reported PASS, because nobody had written the name down. A hand-kept list lags the
# thing it lists. So this reads the BOOKS: every name a private book defines — its note files' names, the
# ids in its JSON, the capitalised words mid-sentence in its prose — must be either on the private list or
# on the vault's reviewed-ordinary list. A word any PUBLIC book in the vault uses (the public-domain
# novels, the demo) is ordinary English and needs no ruling. A new name in a book fails this suite until
# someone classifies it, and both lists live beside the books, never here.
_REVIEW_ENV = "SWE_NAME_REVIEW"
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_MIDCAP = re.compile(r"(?<=[a-z,;:] )([A-Z][a-z]{2,})")
_ID = re.compile(r'"id"\s*:\s*"([^"]+)"')
_NOTE_DIRS = ("characters", "people", "world", "cast")


def _name_review():
    """-> (public book folders, reviewed-ordinary words, source) from the vault's review file, or
    (None, None, why) when there is none — said plainly, never a silent pass."""
    path = os.environ.get(_REVIEW_ENV)
    if not path:
        root = os.environ.get("SWE_BOOKS")
        path = os.path.join(os.path.dirname(root), "name-review.txt") if root else None
    if not path or not os.path.isfile(path):
        return None, None, "NO name-review file (%s unset and none beside $SWE_BOOKS)" % _REVIEW_ENV
    sections, cur = {"public-books": set(), "ordinary": set()}, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#")[0].strip()
            if line.startswith("[") and line.endswith("]"):
                cur = sections.setdefault(line[1:-1].strip().lower(), set())
            elif line and cur is not None:
                cur.add(line)
    return sections["public-books"], {w.lower() for w in sections["ordinary"]}, path


def _book_texts(book_dir):
    for dirpath, dirs, files in os.walk(book_dir):
        rel = os.path.relpath(dirpath, book_dir).replace(os.sep, "/")
        if rel.split("/")[0] == "runs":               # run records: the engine's output, not the book's names
            dirs[:] = []
            continue
        for f in sorted(files):
            if f.endswith((".md", ".json", ".txt")):
                with open(os.path.join(dirpath, f), encoding="utf-8", errors="replace") as fh:
                    yield rel, f, fh.read()


def _parts(s):
    """'CamelCaseName' / 'snake_case_name' / 'grp.x' -> lower-case word parts."""
    return [w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", s)]


def book_name_candidates(books_root, public_books, known, ordinary):
    """{private book: {name: first file}} for every name a private book uses at least twice that is on
    neither list and in no public book's vocabulary."""
    books = sorted(d for d in os.listdir(books_root) if os.path.isdir(os.path.join(books_root, d)))
    common = set()
    for b in books:
        if b in public_books:
            for _rel, _f, txt in _book_texts(os.path.join(books_root, b)):
                common.update(w.lower() for w in _WORD.findall(txt))
    out = {}
    for b in books:
        if b in public_books:
            continue
        seen, where = collections.Counter(), {}
        for rel, f, txt in _book_texts(os.path.join(books_root, b)):
            found = _parts(os.path.splitext(f)[0]) * 2 if rel.split("/")[0] in _NOTE_DIRS else []
            found += [m.group(1).lower() for m in _MIDCAP.finditer(txt)]
            for m in _ID.finditer(txt):
                found += _parts(m.group(1))
            for w in found:
                seen[w] += 1
                where.setdefault(w, "%s/%s" % (rel, f))
        miss = {w: where[w] for w, c in seen.items() if c >= 2 and len(w) >= 3 and w.isalpha()
                and w not in known and w not in ordinary and w not in common}
        if miss:
            out[b] = miss
    return out


def test_the_name_check_can_fire():
    """Negative control on a synthetic vault: an unlisted invented name fails; either list silences it;
    a word a public book uses never needs a ruling."""
    tmp = tempfile.mkdtemp(prefix="swe_namectl_")
    try:
        os.makedirs(os.path.join(tmp, "Private Book", "characters"))
        os.makedirs(os.path.join(tmp, "Public Book"))
        io.open(os.path.join(tmp, "Private Book", "characters", "Quistrel.md"), "w", encoding="utf-8").write(
            "the ship reached Quelmoor at dawn, and then Quelmoor burned.\n")
        io.open(os.path.join(tmp, "Public Book", "novel.txt"), "w", encoding="utf-8").write(
            "the ship reached the harbour at dawn and then it burned\n")
        got = book_name_candidates(tmp, {"Public Book"}, set(), set()).get("Private Book", {})
        assert "quelmoor" in got and "quistrel" in got, "the check missed an unlisted invented name: %s" % got
        assert "ship" not in got and "burned" not in got, "a public book's word needed a ruling: %s" % got
        assert not book_name_candidates(tmp, {"Public Book"}, {"quelmoor", "quistrel"}, set()), "a listed name fired"
        assert not book_name_candidates(tmp, {"Public Book"}, {"quistrel"}, {"quelmoor"}), "a reviewed word fired"
        # ...and THROUGH the suite's own check, so its failure branch is exercised, not just the extractor
        review = os.path.join(tmp, "review.txt")
        io.open(review, "w", encoding="utf-8").write("[public-books]\nPublic Book\n[ordinary]\n")
        saved = {k: os.environ.get(k) for k in ("SWE_BOOKS", _REVIEW_ENV)}
        os.environ.update(SWE_BOOKS=tmp, **{_REVIEW_ENV: review})
        try:
            test_the_list_keeps_up_with_the_books()
            raise AssertionError("the suite's check passed a vault holding an unlisted invented name")
        except AssertionError as exc:
            assert "quelmoor" in str(exc), "the suite's check failed without naming the name: %s" % exc
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return "fires on an unlisted invented name, through the suite's own check; quiet once it is on either list"


def test_fused_and_respelled_names_are_seen():
    """A name fused into an identifier, or written with `_` where the list has `-`, must still be seen —
    through `_scan`, the function the sweep runs (2026-09-23: the fourth read found a private note name
    fused into a CamelCase identifier that every guard had passed)."""
    pats = [(t, _token_rx(t)) for t in ("zzqword", "zzq-mark")]
    tmp = tempfile.mkdtemp(prefix="swe_fusedctl_")
    try:
        bait = os.path.join(tmp, "bait.md")
        io.open(bait, "w", encoding="utf-8").write(
            "the ZzqwordIndex note\na zzq_mark here\nthe zzqwordish thing\n")
        fired = {(n, tok) for _rel, n, tok in _scan([os.path.relpath(bait, REPO)], pats)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert (1, "zzqword") in fired, "a name fused into a CamelCase identifier went unseen: %s" % fired
    assert (2, "zzq-mark") in fired, "a hyphenated name written with an underscore went unseen: %s" % fired
    assert not any(n == 3 for n, _t in fired), "a name buried in a longer lower-case word fired: %s" % fired
    if _PRIVATE:
        real = next((t for t in _PRIVATE if t.isalpha()), None)
        if real:
            probe = _normalise("see the %sIndex note" % real.capitalize())
            assert any(rx.search(probe) for _t, rx in _patterns()), "a real term fused into an identifier went unseen"
    return "a CamelCase-fused name and an underscore-respelled one are both seen; a buried one is not"


def test_the_list_keeps_up_with_the_books():
    root = os.environ.get("SWE_BOOKS")
    public, ordinary, source = _name_review()
    if not root or not os.path.isdir(root) or public is None:
        return ("NOT CHECKED — no books on this machine or %s; this run proves nothing about whether the "
                "list keeps up with the books" % source)
    missing = book_name_candidates(root, public, set(_PRIVATE), ordinary)
    if missing:
        rows = ["    %s: %s  (%s)" % (b, w, f) for b, m in sorted(missing.items()) for w, f in sorted(m.items())]
        raise AssertionError(
            "%d name(s) the private books use are on neither the private list nor the reviewed-ordinary list "
            "— add each to one (both live beside the books, never in this repo):\n%s%s"
            % (len(rows), "\n".join(rows[:40]), "\n    ..." if len(rows) > 40 else ""))
    return "every name the private books use is classified [%s; review: %s]" % (_PRIVATE_SOURCE, source)


def main():
    print("test_no_private_content.py — the repo carries no private content\n")
    failed = 0
    for t in (test_negative_control, test_the_sweep_can_see_where_the_leak_was,
              test_no_private_content_in_tracked_files, test_fused_and_respelled_names_are_seen,
              test_the_name_check_can_fire,
              test_the_list_keeps_up_with_the_books):
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
