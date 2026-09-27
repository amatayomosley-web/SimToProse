#!/usr/bin/env python3
"""test_push_guard.py — the publish gate refuses tags, private terms and unreviewed commits, through real git.

`scripts/push_guard.py` runs as a pre-push hook. A hook that is never invoked is an inert file, so this
suite does not call the checker directly for its main claims: it builds a scratch repository and a bare
"remote", points `core.hooksPath` at THIS repo's `.githooks`, and runs `git push` — the path a real publish
takes. A synthetic private term and a synthetic review folder are passed through the environment, so the
suite needs no book and names none.

Stdlib only, script-style. Exit 0 = all pass.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERM = "zqvorth"                                  # synthetic: belongs to no book
_FAILS = []


def check(name, ok, detail=""):
    # ASCII-safe: git's output reaches here decoded with replacement characters, and a failure report that
    # crashes the console encoder proves the check ran, not what it refused (found by the clone-role mutants).
    detail = str(detail)[:400].encode("ascii", "backslashreplace").decode("ascii")
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _run(cwd, env, *args):
    r = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.returncode, (r.stdout + r.stderr)


def _commit(work, env, path, text, msg):
    io.open(os.path.join(work, path), "w", encoding="utf-8", newline="\n").write(text)
    _run(work, env, "add", path)
    _run(work, env, "commit", "-q", "-m", msg)
    return _run(work, env, "rev-parse", "HEAD")[1].strip()


def _review(reviews, sha):
    io.open(os.path.join(reviews, sha + ".md"), "w", encoding="utf-8").write("REVIEWED %s\nRESULT: clean\n" % sha)


def main():
    print("test_push_guard.py — the publish gate, through a real `git push`")
    tmp = tempfile.mkdtemp(prefix="swe_pushguard_")
    try:
        remote, work, reviews = (os.path.join(tmp, d) for d in ("remote.git", "work", "reviews"))
        os.makedirs(reviews)
        terms = os.path.join(tmp, "terms.txt")
        io.open(terms, "w", encoding="utf-8").write("# synthetic\n%s\n" % TERM)
        env = dict(os.environ, SWE_PRIVATE_TERMS=terms, SWE_PUBLISH_REVIEWS=reviews,
                   GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
        _run(tmp, env, "init", "-q", "--bare", remote)
        _run(tmp, env, "init", "-q", "-b", "main", work)
        _run(work, env, "config", "core.autocrlf", "false")
        _run(work, env, "config", "core.hooksPath", os.path.join(REPO, ".githooks").replace(os.sep, "/"))
        _run(work, env, "remote", "add", "origin", remote)

        print("\n[1] a clean commit is refused until a review record names it, then goes")
        a = _commit(work, env, "notes.md", "an engine note\n", "first")
        rc, out = _run(work, env, "push", "-q", "origin", "main")
        check("unreviewed-commit-refused", rc != 0 and "no review record" in out, out)
        check("the-hook-actually-ran", "push_guard:" in out, out)
        _review(reviews, a)
        rc, out = _run(work, env, "push", "-q", "origin", "main")
        check("reviewed-clean-commit-goes", rc == 0, out)
        check("the-remote-holds-it", _run(remote, env, "rev-parse", "main")[1].strip() == a)

        print("\n[2] a private term in an added line is refused even with a review record")
        b = _commit(work, env, "notes.md", "an engine note\nthe %s example\n" % TERM, "second")
        _review(reviews, b)
        rc, out = _run(work, env, "push", "-q", "origin", "main")
        check("term-in-added-line-refused", rc != 0 and TERM in out and "notes.md:2" in out, out)
        check("the-remote-did-not-move", _run(remote, env, "rev-parse", "main")[1].strip() == a)

        print("\n[2b] ...and fused into an identifier (the fourth read's find, 2026-09-23)")
        _run(work, env, "reset", "-q", "--hard", a)
        b2 = _commit(work, env, "notes.md", "an engine note\nsee %sIndex.md\n" % TERM.capitalize(), "second-b")
        _review(reviews, b2)
        rc, out = _run(work, env, "push", "-q", "origin", "main")
        check("term-fused-into-an-identifier-refused", rc != 0 and TERM in out, out)

        print("\n[3] ...and in a commit message")
        _run(work, env, "reset", "-q", "--hard", a)
        c = _commit(work, env, "other.md", "plain\n", "mention %s here" % TERM)
        _review(reviews, c)
        rc, out = _run(work, env, "push", "-q", "origin", "main")
        check("term-in-message-refused", rc != 0 and "message:1" in out, out)

        print("\n[4] an EXISTING ref sweeps only its outgoing commits: a term the remote already holds is not re-judged"
              "\n    (a NEW ref sweeps its whole history - [10f])")
        _run(work, env, "reset", "-q", "--hard", a)
        _commit(work, env, "held.md", "the %s the remote already has\n" % TERM, "planted")
        rc, out = _run(work, env, "push", "-q", "--no-verify", "origin", "main")   # plant it past the gate
        check("a-term-commit-planted-on-the-remote", rc == 0, out)
        d = _commit(work, env, "clean.md", "plain\n", "third")
        _review(reviews, d)
        rc, out = _run(work, env, "push", "-q", "origin", "main")
        check("fast-forward-of-one-clean-commit-goes", rc == 0 and "1 outgoing commit" in out, out)

        print("\n[5] tags are never pushed; deleting a remote ref always is")
        _run(work, env, "tag", "v1", d)
        rc, out = _run(work, env, "push", "-q", "origin", "v1")
        check("tag-push-refused", rc != 0 and "tags are never pushed" in out, out)
        rc, out = _run(work, env, "push", "-q", "--no-verify", "origin", "v1")    # plant one past the gate
        rc, out = _run(work, env, "push", "-q", "origin", ":refs/tags/v1")
        check("deleting-a-remote-tag-goes", rc == 0, out)

        print("\n[6] an orphan root pushed over the remote is swept WHOLE (the publish shape)")
        _run(work, env, "checkout", "-q", "--orphan", "fresh")
        _run(work, env, "rm", "-rqf", "--cached", ".")            # an EMPTY index: only what is added below
        io.open(os.path.join(work, "clean.md"), "w", encoding="utf-8").write("plain\nold %s line\n" % TERM)
        _run(work, env, "add", "clean.md")
        _run(work, env, "commit", "-q", "-m", "fresh root")
        e = _run(work, env, "rev-parse", "HEAD")[1].strip()
        _review(reviews, e)
        rc, out = _run(work, env, "push", "-q", "--force", "origin", "fresh:main")
        check("orphan-with-a-term-refused", rc != 0 and TERM in out, out)
        io.open(os.path.join(work, "clean.md"), "w", encoding="utf-8").write("plain\n")
        _run(work, env, "add", "clean.md")
        _run(work, env, "commit", "-q", "--amend", "-m", "fresh root")
        f = _run(work, env, "rev-parse", "HEAD")[1].strip()
        _review(reviews, f)
        rc, out = _run(work, env, "push", "-q", "--force", "origin", "fresh:main")
        check("clean-reviewed-orphan-overwrites", rc == 0 and _run(remote, env, "rev-parse", "main")[1].strip() == f, out)

        print("\n[7] it fails CLOSED: no terms list or no review folder refuses the push")
        g = _commit(work, env, "clean.md", "plain\nmore\n", "fourth")
        _review(reviews, g)
        bare = dict(env, SWE_PRIVATE_TERMS=os.path.join(tmp, "absent.txt"), SWE_BOOKS="")
        rc, out = _run(work, bare, "push", "-q", "origin", "fresh:main")
        check("no-terms-list-refuses", rc != 0 and "no private-terms list" in out, out)
        rc, out = _run(work, dict(env, SWE_PUBLISH_REVIEWS=os.path.join(tmp, "absent")), "push", "-q", "origin", "fresh:main")
        check("no-review-folder-refuses", rc != 0 and "no review folder" in out, out)
        rc, out = _run(work, env, "push", "-q", "origin", "fresh:main")
        check("and-with-both-it-goes", rc == 0, out)

        print("\n[9] a DECLARED private remote is not a publish: no review, books/ and terms go; a tag still does not")
        private = os.path.join(tmp, "private.git")
        _run(tmp, env, "init", "-q", "--bare", private)
        _run(work, env, "remote", "add", "mine", private)
        remotes = os.path.join(tmp, "private-remotes.txt")
        io.open(remotes, "w", encoding="utf-8").write("# declared private\n%s\n" % private.replace(os.sep, "/"))
        penv = dict(env, SWE_PRIVATE_REMOTES=remotes)
        _run(work, penv, "checkout", "-q", "-b", "clonework", g)
        os.makedirs(os.path.join(work, "books", "Novel"), exist_ok=True)
        h = _commit(work, penv, "books/Novel/notes.md", "the %s chapter plan\n" % TERM, "a book note")
        rc, out = _run(work, penv, "push", "-q", "mine", "clonework")
        check("private-remote-push-goes-unreviewed", rc == 0 and "private remote" in out, out)
        check("the-private-remote-holds-the-book",
              _run(private, penv, "rev-parse", "clonework")[1].strip() == h)
        inlist = os.path.join(work, "private-remotes.txt")                   # a list INSIDE the pushing checkout
        io.open(inlist, "w", encoding="utf-8").write("%s\n" % private.replace(os.sep, "/"))
        rc, out = _run(work, dict(penv, SWE_PRIVATE_REMOTES=inlist), "push", "-q", "mine", "clonework:inside")
        check("list-inside-the-checkout-ignored", rc != 0 and "private remote" not in out, out)
        os.remove(inlist)
        _run(work, penv, "tag", "v2", h)
        rc, out = _run(work, penv, "push", "-q", "mine", "v2")
        check("tag-to-a-private-remote-still-refused", rc != 0 and "tags are never pushed" in out, out)

        print("\n[10] any OTHER remote refuses the personal namespace, even reviewed and term-free")
        _run(work, penv, "checkout", "-q", "-b", "cleanbook", g)
        os.makedirs(os.path.join(work, "books", "Novel"), exist_ok=True)     # the checkout removed the folder
        k = _commit(work, penv, "books/Novel/outline.md", "a plain outline\n", "a clean book note")
        _review(reviews, k)
        rc, out = _run(work, penv, "push", "-q", "origin", "cleanbook:main")
        check("books-path-to-public-refused", rc != 0 and "personal namespace" in out
              and "books/Novel/outline.md" in out, out)
        check("the-public-remote-did-not-move", _run(remote, penv, "rev-parse", "main")[1].strip() == g)
        _run(work, penv, "checkout", "-q", "-b", "placeholder", g)
        os.makedirs(os.path.join(work, "books"), exist_ok=True)
        m = _commit(work, penv, "books/.gitkeep", "", "the namespace placeholder")
        _review(reviews, m)
        rc, out = _run(work, penv, "push", "-q", "origin", "placeholder:main")
        check("the-placeholder-alone-goes", rc == 0, out)
        base = _run(remote, penv, "rev-parse", "main")[1].strip()

        print("\n[10b] ...including a ROOT commit (the orphan publish shape) and a merge that adds books/ itself")
        _run(work, penv, "checkout", "-q", "--orphan", "rootbooks")
        _run(work, penv, "rm", "-rqf", "--cached", ".")
        os.makedirs(os.path.join(work, "books", "Novel"), exist_ok=True)
        r0 = _commit(work, penv, "books/Novel/root.md", "a plain note\n", "a root carrying a book")
        _review(reviews, r0)
        rc, out = _run(work, penv, "push", "-q", "--force", "origin", "rootbooks:main")
        check("orphan-root-with-books-refused", rc != 0 and "books/Novel/root.md" in out, out)
        _run(work, penv, "checkout", "-q", "-f", "-b", "side", base)
        _commit(work, penv, "side.md", "plain\n", "side work")
        _run(work, penv, "checkout", "-q", "-b", "mainline", base)
        _commit(work, penv, "line.md", "plain\n", "main work")
        _run(work, penv, "merge", "-q", "--no-commit", "--no-ff", "side")
        os.makedirs(os.path.join(work, "books", "Novel"), exist_ok=True)
        io.open(os.path.join(work, "books", "Novel", "merged.md"), "w", encoding="utf-8").write("plain\n")
        _run(work, penv, "add", "books/Novel/merged.md")
        _run(work, penv, "commit", "-q", "-m", "a merge that adds a book file itself")
        mm = _run(work, penv, "rev-parse", "HEAD")[1].strip()
        _review(reviews, mm)
        rc, out = _run(work, penv, "push", "-q", "origin", "mainline:main")
        check("merge-only-books-change-refused", rc != 0 and "books/Novel/merged.md" in out, out)
        check("the-public-remote-still-did-not-move", _run(remote, penv, "rev-parse", "main")[1].strip() == base)

        print("\n[10c] an accented book path, a public pushurl, a re-pointed remote, a filled placeholder: refused")
        _run(work, penv, "checkout", "-q", "-f", "-b", "accent", base)
        os.makedirs(os.path.join(work, "books", "Café Society"), exist_ok=True)
        ac = _commit(work, penv, "books/Café Society/chapter one.md", "a plain note\n", "an accented book path")
        _review(reviews, ac)
        rc, out = _run(work, penv, "push", "-q", "origin", "accent:main")
        check("non-ascii-books-path-refused", rc != 0 and "personal namespace" in out, out)
        pub2, pub3 = os.path.join(tmp, "public2.git"), os.path.join(tmp, "public3.git")
        _run(tmp, penv, "init", "-q", "--bare", pub2)
        _run(tmp, penv, "init", "-q", "--bare", pub3)
        _run(work, penv, "remote", "add", "sneaky", private)                 # fetches from the listed private...
        _run(work, penv, "remote", "set-url", "--push", "sneaky", pub2)      # ...but pushes to a public one
        _review(reviews, h)
        rc, out = _run(work, penv, "push", "-q", "sneaky", "clonework")
        check("private-fetch-public-pushurl-refused", rc != 0 and "personal namespace" in out, out)
        _run(work, penv, "remote", "set-url", "mine", pub3)                  # "mine" re-pointed: stale tracking refs
        rc, out = _run(work, penv, "push", "-q", "mine", "clonework")
        check("repointed-remote-new-branch-refused", rc != 0 and "personal namespace" in out, out)
        check("the-repointed-remote-holds-nothing", _run(pub3, penv, "rev-parse", "clonework")[0] != 0)
        _run(work, penv, "checkout", "-q", "-f", "-b", "fillkeep", base)
        fk = _commit(work, penv, "books/.gitkeep", "smuggled\n", "a filled placeholder")
        _review(reviews, fk)
        rc, out = _run(work, penv, "push", "-q", "origin", "fillkeep:main")
        check("non-empty-placeholder-refused", rc != 0 and "placeholder must be empty" in out, out)

        print("\n[10d] a pure deletion under books/ goes: a leak can be cleaned up")
        _run(work, penv, "checkout", "-q", "-f", "-b", "leak", base)
        os.makedirs(os.path.join(work, "books", "Novel"), exist_ok=True)
        _commit(work, penv, "books/Novel/leaked.md", "plain\n", "a leak")
        rc, out = _run(work, penv, "push", "-q", "--no-verify", "origin", "leak:main")    # planted past the gate
        check("a-leak-planted-on-the-public-remote", rc == 0, out)
        _run(work, penv, "rm", "-q", "books/Novel/leaked.md")
        _run(work, penv, "commit", "-q", "-m", "clean up the leak")
        cl = _run(work, penv, "rev-parse", "HEAD")[1].strip()
        _review(reviews, cl)
        rc, out = _run(work, penv, "push", "-q", "origin", "leak:main")
        check("books-deletion-to-public-goes", rc == 0, out)
        tipnow = _run(remote, penv, "rev-parse", "main")[1].strip()

        print("\n[10e] history that ADDED then removed a book file is refused, though the pushed tree is clean")

        def add_then_drop(branch, start, rel, how="plain"):
            if how == "root":
                _run(work, penv, "checkout", "-q", "-f", "--orphan", branch)
                _run(work, penv, "rm", "-rqf", "--cached", ".")
            else:
                _run(work, penv, "checkout", "-q", "-f", "-b", branch, start)
            os.makedirs(os.path.dirname(os.path.join(work, rel)), exist_ok=True)
            if how == "merge":
                _run(work, penv, "checkout", "-q", "-b", branch + "-side", start)
                _commit(work, penv, branch + "-side.md", "plain\n", "side")
                _run(work, penv, "checkout", "-q", branch)
                _commit(work, penv, branch + "-line.md", "plain\n", "line")
                _run(work, penv, "merge", "-q", "--no-commit", "--no-ff", branch + "-side")
                os.makedirs(os.path.dirname(os.path.join(work, rel)), exist_ok=True)
                io.open(os.path.join(work, rel), "w", encoding="utf-8").write("plain\n")
                _run(work, penv, "add", rel)
                _run(work, penv, "commit", "-q", "-m", "a merge adding a book file")
            else:
                _commit(work, penv, rel, "plain\n", "add a book file")
            _run(work, penv, "rm", "-q", rel)
            _run(work, penv, "commit", "-q", "-m", "drop it again")
            tip = _run(work, penv, "rev-parse", "HEAD")[1].strip()
            _review(reviews, tip)
            return tip

        add_then_drop("gone-plain", tipnow, "books/Novel/brief.md")
        rc, out = _run(work, penv, "push", "-q", "origin", "gone-plain:main")
        check("added-then-dropped-books-refused", rc != 0 and "books/Novel/brief.md" in out, out)
        add_then_drop("gone-root", None, "books/Novel/rooted.md", how="root")
        rc, out = _run(work, penv, "push", "-q", "--force", "origin", "gone-root:main")
        check("root-added-then-dropped-books-refused", rc != 0 and "books/Novel/rooted.md" in out, out)
        add_then_drop("gone-merge", tipnow, "books/Novel/merged2.md", how="merge")
        rc, out = _run(work, penv, "push", "-q", "origin", "gone-merge:main")
        check("merge-added-then-dropped-books-refused", rc != 0 and "books/Novel/merged2.md" in out, out)
        add_then_drop("gone-accent", tipnow, "books/Café Society/draft.md")
        rc, out = _run(work, penv, "push", "-q", "origin", "gone-accent:main")
        check("accented-added-then-dropped-books-refused", rc != 0 and "personal namespace" in out, out)

        print("\n[10f] a new branch to a re-pointed remote is swept over its WHOLE history, not the stale tracking refs")
        pub4 = os.path.join(tmp, "public4.git")
        _run(tmp, penv, "init", "-q", "--bare", pub4)
        _run(work, penv, "remote", "set-url", "mine", private)
        _run(work, penv, "checkout", "-q", "-f", "-b", "termhist", base)     # before [10d]'s planted leak
        _commit(work, penv, "hist.md", "the %s aside\n" % TERM, "a term in history")
        rc, out = _run(work, penv, "push", "-q", "mine", "termhist")              # fine: mine is private
        check("the-term-history-went-to-the-private-remote", rc == 0, out)
        th = _commit(work, penv, "hist.md", "plain\n", "the term removed at the tip")
        _review(reviews, th)
        _run(work, penv, "remote", "set-url", "mine", pub4)                      # re-pointed to a public remote
        rc, out = _run(work, penv, "push", "-q", "mine", "termhist:fresh")
        check("stale-tracking-refs-do-not-hide-history", rc != 0 and TERM in out, out)

        print("\n[10g] a books/ name outside the console's code page is refused with its REASON, not a traceback")
        _run(work, penv, "checkout", "-q", "-f", "-b", "omega", tipnow)      # a fast-forward of the remote's main
        os.makedirs(os.path.join(work, "books", "Ωmega"), exist_ok=True)
        om = _commit(work, penv, "books/Ωmega/notes.md", "plain\n", "a book path outside cp1252")
        _review(reviews, om)
        rc, out = _run(work, penv, "push", "-q", "origin", "omega:main")
        check("unprintable-books-name-refused-readably", rc != 0 and "personal namespace" in out
              and "Traceback" not in out, out)

        print("\n[10h] a placeholder filled and emptied again inside the outgoing commits is refused")
        _run(work, penv, "checkout", "-q", "-f", "-b", "fillempty", tipnow)
        _commit(work, penv, "books/.gitkeep", "smuggled\n", "fill the placeholder")
        fe = _commit(work, penv, "books/.gitkeep", "", "empty it again")
        _review(reviews, fe)
        rc, out = _run(work, penv, "push", "-q", "origin", "fillempty:main")
        check("fill-then-empty-placeholder-refused", rc != 0 and "filled in this commit" in out, out)

        print("\n[11] a credential in the pushed-to url never reaches the verdict (push_guard.check itself)")
        sys.path.insert(0, os.path.join(REPO, "scripts"))
        import push_guard as PG                                              # noqa: E402
        cred = os.path.join(tmp, "cred-remotes.txt")
        io.open(cred, "w", encoding="utf-8").write("https://example.invalid/someone/privrepo\n")
        saved_env = os.environ.get("SWE_PRIVATE_REMOTES")
        os.environ["SWE_PRIVATE_REMOTES"] = cred
        try:
            got = PG.check(work, "x", ["refs/heads/a %s refs/heads/a %s" % (h, "0" * 40)],
                           url="https://user:s3cr3t-tok@example.invalid/someone/privrepo.git")
        finally:
            if saved_env is None:
                os.environ.pop("SWE_PRIVATE_REMOTES", None)
            else:
                os.environ["SWE_PRIVATE_REMOTES"] = saved_env
        check("credential-redacted-in-the-verdict", got and got[0][1] == "OK" and "s3cr3t" not in got[0][2]
              and "user:" not in got[0][2], got)

        print("\n[8] the hook file is the one this repo ships")
        hook = os.path.join(REPO, ".githooks", "pre-push")
        text = io.open(hook, encoding="utf-8").read() if os.path.isfile(hook) else ""
        check("pre-push-calls-push_guard", "scripts/push_guard.py" in text, hook)
        check("pre-push-has-lf-endings", "\r" not in text, "CRLF breaks sh on some hosts")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
