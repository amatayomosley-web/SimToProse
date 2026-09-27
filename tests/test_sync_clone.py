#!/usr/bin/env python3
"""test_sync_clone.py - a clone is synced from the template by the template's own file list, one way, never books/.

`scripts/sync_clone.py` brings a personal clone up to date when the clone cannot `git pull` (its history predates the
template). This builds a scratch "template" and a scratch "clone" as real git repositories, declares the clone
personal through a scratch private-remotes list, and drives `sync` and `main` - the functions the operator runs -
through every precondition, the one-way copy itself, and the personal namespace books/, which never travels.

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
import sync_clone as S                                                  # noqa: E402

_FAILS = []
_ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
            GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
TPL_URL = "https://example.invalid/someone/template.git"
CLONE_URL = "https://example.invalid/someone/private-clone.git"


def check(name, ok, detail=""):
    detail = str(detail)[:400].encode("ascii", "backslashreplace").decode("ascii")    # never crash the report
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=_ENV, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _write(root, rel, data):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "wb").write(data)


def _repo(path, files, origin):
    _git(os.path.dirname(path), "init", "-q", path)
    _git(path, "config", "core.autocrlf", "false")
    _git(path, "remote", "add", "origin", origin)
    for rel, data in files.items():
        _write(path, rel, data)
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "seed")


def _refused(fn):
    """The refusal's words; any OTHER exception comes back labelled, so a check fails by name instead of the suite
    crashing (a crash proves the check ran, not what it refused)."""
    try:
        fn()
    except S.SyncRefused as exc:
        return str(exc)
    except Exception as exc:
        return "UNEXPECTED %s: %s" % (type(exc).__name__, exc)
    return None


def _main_rc(argv):
    try:
        return S.main(argv)
    except Exception as exc:
        return "crash: %s" % type(exc).__name__


def _read(root, rel):
    return io.open(os.path.join(root, rel), "rb").read()


def main():
    print("test_sync_clone.py - one way, by the template's file list, never books/")
    tmp = tempfile.mkdtemp(prefix="swe_syncclone_")
    saved = os.environ.get("SWE_PRIVATE_REMOTES")
    listed = os.path.join(tmp, "private-remotes.txt")
    io.open(listed, "w", encoding="utf-8").write("# the clone is declared private; the template is not\n%s\n"
                                                 % CLONE_URL)
    os.environ["SWE_PRIVATE_REMOTES"] = listed
    quiet = lambda *_a: None
    try:
        tpl, clone = os.path.join(tmp, "template"), os.path.join(tmp, "clone")
        _repo(tpl, {"src/engine/a.py": b"x = 1\n", "docs/b.md": b"line\n", "books/.gitkeep": b"",
                    "docs/retired.md": b"old\n"}, TPL_URL)
        _git(tpl, "rm", "-q", "docs/retired.md")
        _git(tpl, "commit", "-q", "-m", "retire a doc")
        _repo(clone, {"books/.gitkeep": b"", "books/Mine/notes.md": b"the clone's own book\n",
                      "docs/b.md": b"line\r\n", "old/legacy.md": b"clone-only\n", "docs/retired.md": b"old\n"},
              CLONE_URL)

        print("\n[1] --check reports, and copies nothing")
        p = S.sync(tpl, clone, check_only=True, say=quiet)
        check("missing-reported", p["missing"] == ["src/engine/a.py"], p)
        check("crlf-only-difference-is-same", "docs/b.md" not in p["differ"] + p["missing"], p)
        check("clone-only-reported", p["clone_only"] == ["old/legacy.md"], p)
        check("deleted-in-template-reported", p["deleted_in_template"] == ["docs/retired.md"], p)
        check("check-copied-nothing", not os.path.exists(os.path.join(clone, "src", "engine", "a.py")))
        check("check-exit-1-when-work", S.main(["--to", clone, "--from", tpl, "--check"]) == 1)

        print("\n[2] a sync copies the template's committed bytes; clone-only and books/ stay")
        _write(tpl, "docs/b.md", b"line\nnew line\n")
        _git(tpl, "commit", "-qam", "edit")
        S.sync(tpl, clone, say=quiet)
        check("missing-copied", _read(clone, "src/engine/a.py") == b"x = 1\n")
        check("differing-copied", _read(clone, "docs/b.md") == b"line\nnew line\n", _read(clone, "docs/b.md"))
        check("clone-only-kept", os.path.isfile(os.path.join(clone, "old", "legacy.md")))
        check("deleted-in-template-kept-not-deleted", os.path.isfile(os.path.join(clone, "docs", "retired.md")))
        check("clone-book-kept", _read(clone, "books/Mine/notes.md") == b"the clone's own book\n")
        _git(clone, "add", "-A")
        _git(clone, "commit", "-q", "-m", "sync")
        check("deleted-in-template-keeps-check-at-1", S.main(["--to", clone, "--from", tpl, "--check"]) == 1)
        _git(clone, "rm", "-q", "docs/retired.md")
        _git(clone, "commit", "-q", "-m", "drop what the template retired")
        check("now-in-sync", S.main(["--to", clone, "--from", tpl, "--check"]) == 0)

        print("\n[3] every precondition refuses BEFORE a byte is copied")
        _write(tpl, "docs/b.md", b"line\nnewer\n")
        _git(tpl, "commit", "-qam", "edit2")
        _write(clone, "docs/b.md", b"a local edit\n")
        why = _refused(lambda: S.sync(tpl, clone, say=quiet))
        check("local-edit-blocks", why is not None and "docs/b.md" in why, why)
        check("local-edit-survives", _read(clone, "docs/b.md") == b"a local edit\n")
        _git(clone, "checkout", "--", "docs/b.md")
        io.open(os.path.join(clone, ".git", "info", "exclude"), "a", encoding="utf-8").write("docs/new.md\n")
        _write(clone, "docs/new.md", b"an ignored local file\n")
        _write(tpl, "docs/new.md", b"the template's new doc\n")
        _git(tpl, "add", "docs/new.md")
        _git(tpl, "commit", "-q", "-m", "a new doc")
        why = _refused(lambda: S.sync(tpl, clone, say=quiet))
        check("ignored-local-file-blocks", why is not None and "docs/new.md" in why, why)
        check("ignored-local-file-survives", _read(clone, "docs/new.md") == b"an ignored local file\n")
        why = _refused(lambda: S.sync(tpl, tpl, say=quiet))
        check("target-equal-to-source-refused", why is not None and "same repository" in why, why)
        wt = os.path.join(tmp, "tpl-worktree")
        _git(tpl, "worktree", "add", "-q", wt)
        why = _refused(lambda: S.sync(tpl, wt, say=quiet))
        check("a-worktree-of-the-source-refused", why is not None and "same repository" in why, why)
        why = _refused(lambda: S.sync(tpl, os.path.join(clone, "books"), say=quiet))
        check("a-folder-inside-the-clone-refused", why is not None and "not its top" in why, why)
        plain = os.path.join(tmp, "plain")
        os.makedirs(plain)
        check("non-repo-target-refused", _refused(lambda: S.sync(tpl, plain, say=quiet)) is not None)
        why = _refused(lambda: S.sync(clone, tpl, say=quiet))
        check("reversed-run-refused", why is not None and "the source is a personal clone" in why, why)
        io.open(listed, "w", encoding="utf-8").write("https://example.invalid/someone/another\n")
        why = _refused(lambda: S.sync(tpl, clone, say=quiet))
        check("undeclared-target-refused", why is not None and "not a declared personal clone" in why, why)
        io.open(listed, "w", encoding="utf-8").write("%s\n" % CLONE_URL)
        _write(tpl, "docs/b.md", b"uncommitted template work\n")
        why = _refused(lambda: S.sync(tpl, clone, say=quiet))
        check("dirty-source-refused", why is not None and "uncommitted" in why, why)
        _git(tpl, "checkout", "--", "docs/b.md")
        _write(tpl, "books/Novel/never.md", b"a book file in the template\n")
        why = _refused(lambda: S.sync(tpl, clone, say=quiet))
        check("source-namespace-intruder-refused", why is not None and "namespace" in why, why)
        os.remove(os.path.join(tpl, "books", "Novel", "never.md"))
        _write(tpl, "books/.gitkeep", b"smuggled\n")
        _git(tpl, "commit", "-qam", "a filled placeholder, committed")          # past the dirty-source check
        why = _refused(lambda: S.sync(tpl, clone, say=quiet))
        check("source-placeholder-filled-refused", why is not None and "placeholder" in why, why)
        check("main-exit-2-on-refusal", _main_rc(["--to", tpl, "--from", tpl]) == 2)
        io.open(listed, "w", encoding="utf-16").write("%s\n" % CLONE_URL)          # a list saved as UTF-16
        rc = _main_rc(["--to", clone, "--from", tpl])
        check("main-exit-2-on-an-unreadable-list", rc == 2, rc)
        io.open(listed, "w", encoding="utf-8").write("%s\n" % CLONE_URL)

        print("\n[4] fresh pairs: a file inside an ignored FOLDER, a copy that fails part way, a staged rename")

        def pair(name, tfiles, cfiles):
            t, c = os.path.join(tmp, name + "-t"), os.path.join(tmp, name + "-c")
            _repo(t, dict({"books/.gitkeep": b""}, **tfiles), TPL_URL.replace("template", name + "-t"))
            _repo(c, dict({"books/.gitkeep": b""}, **cfiles), CLONE_URL)
            return t, c

        t, c = pair("ignored", {"staging/docs/p.md": b"the template's copy\n"}, {"docs/x.md": b"x\n"})
        io.open(os.path.join(c, ".git", "info", "exclude"), "a", encoding="utf-8").write("staging/\n")
        _write(c, "staging/docs/p.md", b"a file the owner parked here\n")
        why = _refused(lambda: S.sync(t, c, say=quiet))
        check("file-in-an-ignored-folder-blocks", why is not None and "staging/docs/p.md" in why, why)
        check("file-in-an-ignored-folder-survives", _read(c, "staging/docs/p.md") == b"a file the owner parked here\n")

        t, c = pair("partial", {"docs/a-first.md": b"first\n", "docs/blocker.md": b"second\n"},
                    {"docs/blocker.md/inner.md": b"a folder where the template has a file\n"})
        why = _refused(lambda: S.sync(t, c, say=quiet))
        check("part-way-failure-reported", why is not None and "part way" in why and "docs/a-first.md" in why
              and "1 of 2" in why, why)

        t, c = pair("rename", {"docs/b.md": b"template text\n"}, {"docs/b.md": b"clone text\n"})
        _git(c, "mv", "docs/b.md", "docs/b-renamed.md")
        why = _refused(lambda: S.sync(t, c, say=quiet))
        check("staged-rename-of-a-target-blocks", why is not None and "docs/b.md" in why, why)
    finally:
        if saved is None:
            os.environ.pop("SWE_PRIVATE_REMOTES", None)
        else:
            os.environ["SWE_PRIVATE_REMOTES"] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
