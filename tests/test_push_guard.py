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
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % str(detail)[:400]))
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

        print("\n[4] only OUTGOING commits are swept: a term the remote already holds is not re-judged")
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
