#!/usr/bin/env python3
"""push_guard.py — the publish gate: nothing leaves this checkout unless it is clean and reviewed.

Called by `.githooks/pre-push` (enable per checkout: `git config core.hooksPath .githooks`). Git passes
the remote's name and URL as arguments and one line per ref on stdin:
`<local ref> <local sha> <remote ref> <remote sha>`. For every ref being pushed this REFUSES:

  1. any TAG. A tag carries its own history past every branch check; on 2026-09-23 the public remote
     was found holding a tag whose snapshot named a private book's cast in 24 of its 157 files, while
     every branch sweep had passed.
  2. any outgoing commit whose message or added lines carry a private term or a machine path — the
     patterns `tests/test_no_private_content.py` sweeps the tree with, imported here and never copied,
     so the tree sweep and the push gate cannot disagree about what counts.
  3. any push whose tip commit has no REVIEW RECORD: `<sha>.md`, naming that sha, in the publish-reviews
     folder beside the books ($SWE_PUBLISH_REVIEWS, default `<parent of $SWE_BOOKS>/publish-reviews`).
     A renamed scene is invisible to every pattern — measured the same day, phrase fingerprints of the
     books missed the renamed scenes and flagged clean files — so the only check for plot is a reading,
     and this makes the reading a condition of the push instead of a habit. It proves a review was
     recorded for exactly this commit; it cannot prove the review was good.

A remote DECLARED private (2026-09-26, gate clone-role) is not a publish: the owner's personal clone holds
his books and pushes them to his own private remote. When the url git is pushing to - its second argument,
after any pushurl or pushInsteadOf - is on the machine-local private-remotes list beside the books
(`scripts/checkout_role.py`, the one definition; a list inside this checkout does not count), every ref but
a tag goes, and the verdict names the declaration so a wrongly listed url is visible. Every OTHER remote
gets the full gate above PLUS:

  4. any outgoing commit that ADDS or CHANGES a path under the personal namespace `books/`, and any pushed
     tip whose TREE holds anything there but an empty placeholder - whatever it contains. A clone's books
     never go to a public remote. The tree check holds even when commit traversal is fooled (a stale
     remote-tracking ref, a remote re-pointed from private to public); a new ref is swept over its whole
     history for the same reason. A pure deletion under books/ is allowed, so a leak can be cleaned up.

Deleting a remote ref is always allowed. With no private-terms list or no review folder the gate
REFUSES a public push: a publish gate that cannot see what it guards must not pass. `git push
--no-verify` skips every hook, visibly; there is deliberately no quieter switch.

Stdlib only. Exit 0 = the push may go ahead.
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tests"))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import test_no_private_content as G                                    # noqa: E402  the ONE pattern definition
import checkout_role as R                                              # noqa: E402  the ONE role definition

_REVIEWS_ENV = "SWE_PUBLISH_REVIEWS"
_ZERO = re.compile(r"^0+$")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def reviews_dir():
    """Where review records live: beside the books, never in the repo (a record names what was read)."""
    path = os.environ.get(_REVIEWS_ENV)
    if not path:
        root = os.environ.get("SWE_BOOKS")
        path = os.path.join(os.path.dirname(root), "publish-reviews") if root else None
    return path


def _git(cwd, *args):
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    if out.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), out.stderr.strip()[:200]))
    return out.stdout


def outgoing(cwd, local_sha, remote_sha, remote):
    """The commits this ref would add to the remote: reachable from the new tip and not from the remote's old
    tip. For a NEW ref, the whole history reachable from the tip: this checkout's remote-tracking refs are only a
    local belief about the remote - stale, or left from a url the remote name used to point at, they hid every
    commit ("0 outgoing") while git sent them all (the clone-role review, finding C)."""
    if _ZERO.match(remote_sha):
        return _git(cwd, "rev-list", local_sha).split()
    return _git(cwd, "rev-list", local_sha, "--not", remote_sha).split()


def _combined(pats):
    return re.compile("|".join("(?:%s)" % rx.pattern for _tok, rx in pats))


def leaks_in(cwd, sha, pats):
    """(where, token) for every private hit in one commit's message and ADDED lines. Removed lines are
    history the remote already holds or that another outgoing commit carries, and is swept there."""
    anyhit, hits = _combined(pats), []

    def scan(where, text):
        low = G._normalise(text)
        if anyhit.search(low):
            hits.extend((where, tok) for tok, rx in pats if rx.search(low))

    for n, line in enumerate(_git(cwd, "log", "-1", "--format=%B", sha).splitlines(), 1):
        scan("message:%d" % n, line)
    path, lineno = "?", 0
    for line in _git(cwd, "show", "--format=", "--unified=0", "--no-color", "--no-ext-diff", sha).splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("@@"):
            m = _HUNK.match(line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith("+"):
            scan("%s:%d" % (path, lineno), line[1:])
            lineno += 1
    return hits


def personal_paths(cwd, sha):
    """Paths under the personal namespace that one commit ADDS or CHANGES - against every parent of a merge, and
    against nothing for a root commit - the placeholder excepted. Read NUL-separated: git C-quotes a non-ASCII name in
    its newline output ("books/Caf\\303\\251 ..."), which matched no namespace, so an accented book path went out
    reviewed and term-free (the clone-role review, MAJOR-1). A pure deletion is not listed: it adds nothing."""
    names = _git(cwd, "diff-tree", "-z", "--no-commit-id", "--name-only", "-r", "-m", "--root",
                 "--diff-filter=d", sha).split("\0")
    bad = {n for n in names if n and R.is_personal(n)}
    if R.NAMESPACE_KEEP in names and _git(cwd, "cat-file", "-s", "%s:%s" % (sha, R.NAMESPACE_KEEP)).strip() != "0":
        bad.add("%s (filled in this commit; the placeholder must be empty)" % R.NAMESPACE_KEEP)   # review 2, nit c
    return sorted(bad)


def tip_problems(cwd, sha):
    """What the pushed TREE holds under the personal namespace: every path but the placeholder, and a placeholder
    that is not empty (it is exempt by name, so its size is held at 0). Commit traversal can be fooled; a tree
    cannot."""
    names = [n for n in _git(cwd, "ls-tree", "-r", "-z", "--name-only", sha, "--", R.PERSONAL_NAMESPACE).split("\0")
             if n]
    bad = [n for n in names if R.is_personal(n)]
    if R.NAMESPACE_KEEP in names:
        size = _git(cwd, "cat-file", "-s", "%s:%s" % (sha, R.NAMESPACE_KEEP)).strip()
        if size != "0":
            bad.append("%s (%s bytes; the placeholder must be empty)" % (R.NAMESPACE_KEEP, size))
    return bad


def remote_location(cwd, remote, url=None):
    """The url git is pushing to - its second argument, with pushurl and pushInsteadOf already applied - else the
    one it has for `remote`, else `remote` itself."""
    return url or R.remote_url(cwd, remote) or remote


def check(cwd, remote, lines, url=None):
    """-> list of (remote_ref, verdict, detail). verdict is OK or REFUSED."""
    out = []
    pats = G._patterns()
    rdir = reviews_dir()
    where = remote_location(cwd, remote, url)
    private, why = R.is_private_url(where, repo=cwd)
    shown_where = R.redact(where)
    for raw in lines:
        parts = raw.split()
        if len(parts) != 4:
            continue
        _lref, lsha, rref, rsha = parts
        if _ZERO.match(lsha):
            out.append((rref, "OK", "deletion"))
            continue
        if rref.startswith("refs/tags/"):
            out.append((rref, "REFUSED", "tags are never pushed: a tag carries history past every branch check"))
            continue
        if private:
            out.append((rref, "OK", "private remote %s (%s) - not a publish; no review needed" % (shown_where, why)))
            continue
        if not G._PRIVATE:
            out.append((rref, "REFUSED", "no private-terms list on this machine (%s)" % G._PRIVATE_SOURCE))
            continue
        if not rdir or not os.path.isdir(rdir):
            out.append((rref, "REFUSED", "no review folder (%s unset and none beside $SWE_BOOKS)" % _REVIEWS_ENV))
            continue
        commits = outgoing(cwd, lsha, rsha, remote)
        mine = [("tip", p) for p in tip_problems(cwd, lsha)]
        mine += [(c[:7], p) for c in commits for p in personal_paths(cwd, c)]
        if mine:
            shown = "; ".join("%s %s" % m for m in mine[:10])
            out.append((rref, "REFUSED", "the personal namespace %s never goes to a public remote: %d path(s) in "
                        "the pushed tree or outgoing commits: %s" % (R.PERSONAL_NAMESPACE, len(mine), shown)))
            continue
        hits = [(c[:7], at, tok) for c in commits for at, tok in leaks_in(cwd, c, pats)]
        if hits:
            shown = "; ".join("%s %s %s" % h for h in hits[:10])
            out.append((rref, "REFUSED", "%d private hit(s) in %d outgoing commit(s): %s" % (len(hits), len(commits), shown)))
            continue
        record = os.path.join(rdir, "%s.md" % lsha)
        try:
            ok = lsha in open(record, encoding="utf-8").read()
        except OSError:
            ok = False
        if not ok:
            out.append((rref, "REFUSED", "no review record for %s (expected %s, naming the sha)" % (lsha[:12], record)))
            continue
        out.append((rref, "OK", "%d outgoing commit(s) swept clean; reviewed (%s)" % (len(commits), record)))
    return out


def main(argv=None, stdin=None):
    argv = sys.argv[1:] if argv is None else argv
    remote = argv[0] if argv else "origin"
    url = argv[1] if len(argv) > 1 else None                    # git passes the remote's location second
    lines = (stdin if stdin is not None else sys.stdin).read().splitlines()
    try:
        verdicts = check(os.getcwd(), remote, lines, url)
    except RuntimeError as exc:
        print(("push_guard: REFUSED - %s" % exc).encode("ascii", "backslashreplace").decode("ascii"))
        return 1
    for rref, verdict, detail in verdicts:
        # ASCII-safe: a refused books/ name outside the console's code page raised in print, so the reason arrived
        # as a traceback at the very moment a book was being stopped (clone-role review 2, NEW-2)
        line = "push_guard: %s %s - %s" % (verdict, rref, detail)
        print(line.encode("ascii", "backslashreplace").decode("ascii"))
    return 1 if any(v == "REFUSED" for _r, v, _d in verdicts) else 0


if __name__ == "__main__":
    sys.exit(main())
