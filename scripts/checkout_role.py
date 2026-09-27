#!/usr/bin/env python3
"""checkout_role.py - a checkout's declared ROLE (template | personal clone) and its one personal namespace.

The owner, 2026-09-26: "The logic is people clone the repo and make it personal, similar to swe, so for swe we will
have my book info and everything else that's not apart of the public version." The TEMPLATE - the public repo, and
any checkout whose origin is not declared private - sweeps every path, and its books/ holds nothing but an empty
placeholder. A PERSONAL CLONE - a checkout whose origin is on the machine-local private-remotes list beside the books
($SWE_PRIVATE_REMOTES, default <parent of $SWE_BOOKS>/private-remotes.txt) - keeps its owner's books under ONE
namespace, books/, which the private-content sweep leaves and counts. That is not an exception list: nothing is
named, one namespace is declared, and the role a public remote sees is unchanged.

Declared, never guessed, and fail closed: no list, an empty or relative setting, a list that sits INSIDE the checkout
being judged (a commit could then change the role - found by the clone-role review), no origin, or an unlisted origin
is the template role; an unreadable list raises. This module is the one definition: the sweep
(tests/test_no_private_content.py), the publish gate (scripts/push_guard.py), the clone sync (scripts/sync_clone.py)
and the SessionStart wake hook under .claude/hooks read it here, never a copy.

Stdlib only.
"""
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTES_ENV = "SWE_PRIVATE_REMOTES"
PERSONAL_CLONE, TEMPLATE = "personal clone", "template"
PERSONAL_NAMESPACE = "books/"
NAMESPACE_KEEP = "books/.gitkeep"


def norm_url(url):
    """A remote's url or path -> one comparable spelling: `host/owner/repo` for https, ssh and scp-style urls, a
    forward-slashed path for a local remote; lower-cased, a trailing `/` and `.git` dropped. Scheme, port and
    user are dropped too, so the same host and path over two protocols compare equal - one repository."""
    u = str(url or "").strip().replace("\\", "/").lower()
    m = re.match(r"^[a-z][a-z0-9+.-]*://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.*)$", u)
    if not m:
        m = re.match(r"^[^@/\s]+@([^:/\s]+):(.*)$", u)
    if m:
        u = "%s/%s" % (m.group(1), m.group(2))
    u = u.rstrip("/")
    return (u[:-4] if u.endswith(".git") else u).rstrip("/")


def redact(url):
    """The url with any `user:secret@` removed: a credential in a remote url must never reach a log, a push's
    output or a session's wake (the clone-role review, finding F)."""
    return re.sub(r"(?<=://)[^@/\s]+@", "", str(url or ""))


def _inside(path, root):
    try:
        root = os.path.realpath(root)
        return os.path.commonpath([os.path.realpath(path), root]) == root
    except ValueError:                                  # another drive on Windows: not inside
        return False


def private_remotes(repo=None):
    """-> (set of declared-private remotes, normalised - or None when there is no usable list; where it is, or why
    not). Read on every call, never cached. With `repo`, a list inside that checkout does not count."""
    if REMOTES_ENV in os.environ:
        path = os.environ[REMOTES_ENV].strip()
        if not path:
            return None, "%s is set but empty" % REMOTES_ENV
    else:
        root = os.environ.get("SWE_BOOKS", "").strip().rstrip("/\\")
        path = os.path.join(os.path.dirname(root), "private-remotes.txt") if root else ""
        if not path:
            return None, "no private-remotes list (%s and $SWE_BOOKS both unset)" % REMOTES_ENV
    if not os.path.isabs(path):
        return None, "the private-remotes path %r is relative - it must be absolute" % path
    if not os.path.isfile(path):
        return None, "no private-remotes list at %s" % path
    if repo and _inside(path, repo):
        return None, ("the private-remotes list %s sits inside the checkout - a commit could change it; keep it "
                      "outside the work tree" % path)
    urls = set()
    with open(path, encoding="utf-8-sig") as fh:         # -sig: PowerShell 5.1 writes a BOM
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                line = re.split(r"\s+#", line, maxsplit=1)[0].strip()     # a trailing comment needs a space
                if line:
                    urls.add(norm_url(line))
    return urls, path


def is_private_url(url, repo=None):
    """-> (True only when `url` is on the declared private-remotes list, why)."""
    urls, source = private_remotes(repo)
    if urls is None:
        return False, source
    if url and norm_url(url) in urls:
        return True, "declared private in %s" % source
    return False, "not on the private-remotes list %s" % source


def remote_url(repo, name="origin"):
    """The fetch url git has for `name` in `repo`, or "" when there is none."""
    r = subprocess.run(["git", "remote", "get-url", name], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


def checkout_role(repo=REPO):
    """-> (PERSONAL_CLONE | TEMPLATE, why). A personal clone ONLY when this checkout's origin is declared private;
    anything else is the template role - the one that sweeps everything."""
    url = remote_url(repo)
    if not url:
        return TEMPLATE, "no origin remote"
    private, why = is_private_url(url, repo)
    return (PERSONAL_CLONE if private else TEMPLATE), "origin %s: %s" % (redact(url), why)


def is_personal(rel):
    """True for a path inside the personal namespace; the namespace's own placeholder is not personal content."""
    p = rel.replace("\\", "/")
    return p.startswith(PERSONAL_NAMESPACE) and p != NAMESPACE_KEEP


def listed(repo=REPO):
    """Every path git would offer to commit - tracked, plus untracked and not ignored - read NUL-separated, so a name
    with an accent or a curly quote arrives as itself. Until 2026-09-26 the sweep read git's newline output, where
    such a name is C-quoted ("books/Caf\\303\\251 ...") and matched no namespace and no extension: the tree sweep had
    never read a non-ASCII-named file (the clone-role review, MAJOR-1). Strict UTF-8: a name git cannot give as
    UTF-8 fails loud rather than being skipped."""
    out = []
    for args in (["git", "ls-files", "-z"], ["git", "ls-files", "-z", "--others", "--exclude-standard"]):
        r = subprocess.run(args, cwd=repo, capture_output=True)
        if r.returncode != 0:
            raise RuntimeError("%s failed - cannot determine the disclosure surface" % " ".join(args))
        out.extend(p for p in r.stdout.decode("utf-8").split("\0") if p)
    return out


def namespace_intruders(repo=REPO):
    """Every path git would offer to commit inside the personal namespace, the placeholder excepted - any file, text
    or not. In the template this must be empty."""
    return [rel for rel in listed(repo) if is_personal(rel)]


def placeholder_problem(repo=REPO):
    """-> why the namespace placeholder is not an empty file, or "" when it is empty or absent. The placeholder is
    exempt by NAME, so anything written into it would pass every namespace check unless its size is held at 0."""
    p = os.path.join(repo, NAMESPACE_KEEP)
    if os.path.isfile(p) and os.path.getsize(p):
        return "%s is not empty (%d bytes) - the placeholder carries nothing" % (NAMESPACE_KEEP, os.path.getsize(p))
    return ""
