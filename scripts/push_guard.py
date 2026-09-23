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

Deleting a remote ref is always allowed. With no private-terms list or no review folder the gate
REFUSES: a publish gate that cannot see what it guards must not pass. `git push --no-verify` skips
every hook, visibly; there is deliberately no quieter switch.

Stdlib only. Exit 0 = the push may go ahead.
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tests"))
import test_no_private_content as G                                    # noqa: E402  the ONE definition

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
    """The commits this ref would add to the remote: reachable from the new tip and not from what the
    remote already holds (its old tip, or for a new ref every remote-tracking ref of that remote)."""
    stop = [remote_sha] if not _ZERO.match(remote_sha) else ["--remotes=%s" % remote]
    return _git(cwd, "rev-list", local_sha, "--not", *stop).split()


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


def check(cwd, remote, lines):
    """-> list of (remote_ref, verdict, detail). verdict is OK or REFUSED."""
    out = []
    pats = G._patterns()
    rdir = reviews_dir()
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
        if not G._PRIVATE:
            out.append((rref, "REFUSED", "no private-terms list on this machine (%s)" % G._PRIVATE_SOURCE))
            continue
        if not rdir or not os.path.isdir(rdir):
            out.append((rref, "REFUSED", "no review folder (%s unset and none beside $SWE_BOOKS)" % _REVIEWS_ENV))
            continue
        commits = outgoing(cwd, lsha, rsha, remote)
        hits = [(c[:7], where, tok) for c in commits for where, tok in leaks_in(cwd, c, pats)]
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
    lines = (stdin if stdin is not None else sys.stdin).read().splitlines()
    try:
        verdicts = check(os.getcwd(), remote, lines)
    except RuntimeError as exc:
        print("push_guard: REFUSED — %s" % exc)
        return 1
    for rref, verdict, detail in verdicts:
        print("push_guard: %s %s — %s" % (verdict, rref, detail))
    return 1 if any(v == "REFUSED" for _r, v, _d in verdicts) else 0


if __name__ == "__main__":
    sys.exit(main())
