#!/usr/bin/env python3
"""test_checkout_role.py - a checkout's role is DECLARED, fails closed, and the personal namespace is read as itself.

`scripts/checkout_role.py` decides whether a checkout is the TEMPLATE (swept whole) or a declared PERSONAL CLONE
(swept whole except books/), and lists what git would offer to commit. Everything here drives those functions and the
sweep's own `sweep_set` / `_scan` on scratch git repositories - never a re-implementation - with a synthetic bait token
and synthetic urls, so it needs no book and names none. The non-ASCII cases are the clone-role review's MAJOR-1: git
C-quotes such a name in its newline output, and until the listing read NUL-separated a `books/Café ...` path matched
no namespace and no extension, and no non-ASCII-named file anywhere had ever been swept.

Stdlib only, script-style. Exit 0 = all pass.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))
import checkout_role as R                                              # noqa: E402
import test_no_private_content as G                                    # noqa: E402

BAIT = "zzqclone"
ACUTE = "Café Society"                                             # an accented title, as book folders are


def _git_init(path, origin=None):
    subprocess.run(["git", "init", "-q", path], check=True, capture_output=True)
    if origin:
        subprocess.run(["git", "remote", "add", "origin", origin], cwd=path, check=True, capture_output=True)


def _with_env(overrides, fn):
    saved = {k: os.environ.get(k) for k in overrides}
    try:
        for k, v in overrides.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return fn()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _put(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8").write(text)


def test_role_is_declared_never_guessed():
    """Personal clone ONLY when the origin is on the declared list; no list, an empty or relative setting, a list
    inside the checkout, an unlisted origin or no origin is the template role. A BOM does not hide the first entry,
    and a credential in the origin url never reaches the reason text."""
    tmp = tempfile.mkdtemp(prefix="swe_rolectl_")
    try:
        repo, bare = os.path.join(tmp, "clone"), os.path.join(tmp, "bare")
        _git_init(repo, "https://Example.invalid/Someone/Private-Book.git/")
        _git_init(bare)
        lst = os.path.join(tmp, "private-remotes.txt")
        role = lambda r, path: _with_env({R.REMOTES_ENV: path}, lambda: R.checkout_role(r))

        assert role(repo, os.path.join(tmp, "absent.txt"))[0] == R.TEMPLATE, "no list must mean the template role"
        io.open(lst, "w", encoding="utf-8").write("# declared private\ngit@example.invalid:someone/private-book  # mine\n")
        assert role(repo, lst)[0] == R.PERSONAL_CLONE, ("an https origin did not match its listed scp spelling "
                                                        "(case, trailing / and .git, a trailing comment)")
        io.open(lst, "w", encoding="utf-8-sig").write("https://example.invalid/someone/private-book\n")
        assert role(repo, lst)[0] == R.PERSONAL_CLONE, "a BOM at the head of the list hid its first entry"
        got, why = role(repo, "")
        assert got == R.TEMPLATE and "empty" in why, "an explicitly EMPTY setting must mean no list, and say so: %s" % why
        got, why = role(repo, "private-remotes.txt")
        assert got == R.TEMPLATE and "relative" in why, "a relative list path must not count, and say so: %s" % why
        hashed = os.path.join(tmp, "my#repos", "private.git")                  # a '#' inside a path is not a comment
        hrepo = os.path.join(tmp, "hashed")
        _git_init(hrepo, hashed)
        io.open(lst, "w", encoding="utf-8").write("%s   # the hashed one\n" % hashed.replace("\\", "/"))
        assert role(hrepo, lst)[0] == R.PERSONAL_CLONE, "a '#' inside a listed path truncated the entry"
        inside = os.path.join(repo, "private-remotes.txt")
        io.open(inside, "w", encoding="utf-8").write("https://example.invalid/someone/private-book\n")
        got, why = role(repo, inside)
        assert got == R.TEMPLATE and "inside the checkout" in why, "a list inside the checkout counted: %s" % why
        io.open(lst, "w", encoding="utf-8").write("https://example.invalid/someone/another-book\n")
        assert role(repo, lst)[0] == R.TEMPLATE, "an unlisted origin must mean the template role"
        io.open(lst, "w", encoding="utf-8").write("https://example.invalid/someone/private-book\n")
        assert role(bare, lst)[0] == R.TEMPLATE, "a checkout with no origin must mean the template role"

        subprocess.run(["git", "remote", "set-url", "origin", "https://user:s3cr3t-tok@example.invalid/someone/"
                        "private-book.git"], cwd=repo, check=True, capture_output=True)
        got, why = role(repo, lst)
        assert got == R.PERSONAL_CLONE, "userinfo in the url must not change what repository it names"
        assert "s3cr3t" not in why and "user:" not in why, "a credential reached the reason text: %s" % why
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return ("declared, never guessed: listed -> personal clone; no list, empty, relative, inside the checkout, "
            "unlisted or no origin -> template; a BOM hides nothing; credentials never printed")


def test_personal_clone_skips_only_its_namespace():
    """Through `sweep_set` and `_scan`, the functions the sweep runs: a personal clone leaves books/ (every file
    counted, accented names included) and still sweeps the rest, an accented name included; the template sweeps all."""
    tmp = tempfile.mkdtemp(prefix="swe_clonectl_")
    try:
        repo = os.path.join(tmp, "clone")
        _git_init(repo, "https://example.invalid/someone/private-book.git")
        _put(repo, "books/Novel/notes.md", "the %s marker\n" % BAIT)
        _put(repo, "books/%s/notes.md" % ACUTE, "the %s marker\n" % BAIT)
        _put(repo, "books/Novel/cover.bin", "binary-ish\n")
        _put(repo, "scripts/tool.py", "the %s marker\n" % BAIT)
        _put(repo, "scripts/café tool.py", "the %s marker\n" % BAIT)
        _put(repo, "books/.gitkeep", "")
        lst = os.path.join(tmp, "private-remotes.txt")
        io.open(lst, "w", encoding="utf-8").write("https://example.invalid/someone/private-book\n")
        pats = [(BAIT, G._token_rx(BAIT))]

        def sweep(path):
            files, mine, role, _why = _with_env({R.REMOTES_ENV: path}, lambda: G.sweep_set(repo))
            return role, {h[0].replace("\\", "/") for h in G._scan(files, pats, repo=repo)}, \
                {m.replace("\\", "/") for m in mine}

        role, hit, left = sweep(lst)
        assert role == R.PERSONAL_CLONE, role
        assert hit == {"scripts/tool.py", "scripts/café tool.py"}, "a clone must still sweep outside books/: %s" % hit
        assert left == {"books/Novel/notes.md", "books/%s/notes.md" % ACUTE, "books/Novel/cover.bin"}, (
            "every unswept file - text or not, accented or not - must be handed back for the report: %s" % left)
        role, hit, left = sweep(os.path.join(tmp, "absent.txt"))
        assert role == R.TEMPLATE and not left, (role, left)
        assert hit == {"scripts/tool.py", "scripts/café tool.py", "books/Novel/notes.md",
                       "books/%s/notes.md" % ACUTE}, "the template role must sweep books/ too: %s" % hit
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return ("a personal clone leaves books/ (every file counted) and sweeps the rest; the template sweeps books/ "
            "too; accented names are read as themselves")


def test_template_books_namespace_is_empty():
    """In the TEMPLATE the personal namespace holds only an EMPTY placeholder: the template is what a public remote
    receives. With negative controls: a binary intruder, an accented one, and a placeholder with content."""
    tmp = tempfile.mkdtemp(prefix="swe_nsctl_")
    try:
        _git_init(tmp)
        _put(tmp, "books/.gitkeep", "")
        io.open(os.path.join(tmp, "books", "cover.bin"), "wb").write(b"\x00\x01")
        _put(tmp, "books/%s/notes.md" % ACUTE, "plain\n")
        caught = sorted(p.replace("\\", "/") for p in R.namespace_intruders(tmp))
        assert caught == ["books/%s/notes.md" % ACUTE, "books/cover.bin"], "the namespace check missed: %s" % caught
        assert R.placeholder_problem(tmp) == "", "an empty placeholder was flagged"
        _put(tmp, "books/.gitkeep", "something smuggled\n")
        assert R.placeholder_problem(tmp), "a placeholder with content passed"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    role, why = R.checkout_role()
    if role == R.PERSONAL_CLONE:
        return "personal clone (%s): books/ is its own - checked in the template only; the controls fire" % why
    inside = R.namespace_intruders()
    assert not inside, "the template's books/ holds %d file(s) besides its placeholder: %s" % (len(inside), inside[:10])
    problem = R.placeholder_problem()
    assert not problem, problem
    return "the template's books/ holds only an empty placeholder (%s); the controls fire" % why


def test_chronicles_are_ignored_at_every_depth():
    """A chronicle database is a save-file: under ANY runs/ git must ignore it, while a book's notes stay
    committable - and the files that live beside the books, if they ever land at a clone's root, are ignored too.
    Asked of git itself, through a COPY of this repo's .gitignore in a bare scratch repository with no global
    excludes, so a machine's own ignore files can neither pass nor fail it (clone-role review 2, nit g)."""
    ignored = ["runs/live.db", "books/Some Book/runs/live.db", "books/Some Book/runs/live.db-wal",
               "books/Some Book/runs/drafts/d1.db", "books/Some Book/runs/history/h1.db-shm",
               "books/Some Book/runs/live.db.directions/r.a.json",
               "private-remotes.txt", "private-terms.txt", "name-review.txt", "publish-reviews/abc.md"]
    kept = ["books/Some Book/world/world.md", "runs/_TEMPLATE/story-map.md", "books/Some Book/runs/story-map.md"]
    tmp = tempfile.mkdtemp(prefix="swe_ignorectl_")
    try:
        _git_init(tmp)
        shutil.copyfile(os.path.join(REPO, ".gitignore"), os.path.join(tmp, ".gitignore"))
        empty = os.path.join(tmp, "no-global-excludes")
        io.open(empty, "w").close()

        def ig(p):
            return subprocess.run(["git", "-c", "core.excludesFile=%s" % empty.replace("\\", "/"), "check-ignore",
                                   "-q", "--no-index", p], cwd=tmp).returncode == 0

        missed = [p for p in ignored if not ig(p)]
        over = [p for p in kept if ig(p)]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert not missed, "files git would commit: %s" % missed
    assert not over, "book notes git would ignore: %s" % over
    return "%d chronicle and beside-the-books paths ignored; %d note paths still committable" % (len(ignored), len(kept))


def test_a_bom_hides_no_entry():
    """PowerShell 5.1 saves text with a BOM. Read as plain utf-8 it glued itself to the FIRST entry, which then never
    matched: the first private term went unswept, silently (clone-role review 1, pre-existing), and the first
    name-review header went unread. Through the sweep's own readers."""
    tmp = tempfile.mkdtemp(prefix="swe_bomctl_")
    try:
        terms = os.path.join(tmp, "terms.txt")
        io.open(terms, "w", encoding="utf-8-sig").write("zzqbom\nzzqsecond\n")
        toks, _src = _with_env({"SWE_PRIVATE_TERMS": terms}, G._private_terms)
        assert toks[:1] == ["zzqbom"], "a BOM hid the first private term: %r" % toks[:1]
        review = os.path.join(tmp, "review.txt")
        io.open(review, "w", encoding="utf-8-sig").write("[public-books]\nPub Book\n[ordinary]\nword\n")
        public, ordinary, _src = _with_env({"SWE_NAME_REVIEW": review}, G._name_review)
        assert public == {"Pub Book"} and ordinary == {"word"}, "a BOM hid the first review header: %r" % public
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return "a BOM hides neither the first private term nor the first review header"


def main():
    print("test_checkout_role.py - the role is declared, fails closed, and names are read as themselves\n")
    failed = 0
    for t in (test_role_is_declared_never_guessed, test_personal_clone_skips_only_its_namespace,
              test_template_books_namespace_is_empty, test_chronicles_are_ignored_at_every_depth,
              test_a_bom_hides_no_entry):
        try:
            detail = t()
            print("  PASS  %s\n          %s" % (t.__name__, detail))
        except Exception as e:
            failed += 1
            print("  FAIL  %s\n          %s" % (t.__name__, str(e).encode("ascii", "backslashreplace").decode("ascii")))
    print("\nVERDICT: %s" % ("PASS" if not failed else "FAIL"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
