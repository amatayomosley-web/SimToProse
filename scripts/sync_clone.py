#!/usr/bin/env python3
"""sync_clone.py - bring a personal clone up to date with the template: one way, by the template's own file list.

The owner, 2026-09-26: people clone the template and make it personal. A clone that shares the template's history
updates with `git pull`; a clone with its own history (the owner's predates the template) cannot, and until this
script it was synced file by file, by hand. The manifest is `git ls-files` of the SOURCE checkout - never a hand
list (CLAUDE.md's seven hand-kept duplicates, every one of which went wrong).

    python scripts/sync_clone.py --to <clone> [--from <template>] [--check]

--check reports, over the source's tracked files: MISSING in the clone, or DIFFERING beyond line endings; the files
the clone tracks that the template's history DELETED; and the files only the clone tracks (CLONE-ONLY). Nothing is
ever deleted. Exit 0 only when nothing is missing, differing or deleted-in-template.

Without --check it copies every missing or differing file, the source's bytes. PRECONDITIONS, each refused before a
byte is copied (scripts/checkout_role.py is the one role definition):
  - the source is the template role and the target is a DECLARED personal clone - so a run in the wrong direction,
    or into a clone nobody declared, is refused rather than guessed (the clone-role review, finding A);
  - each path is the top of its own work tree, and the two are different repositories (not one repository's two
    worktrees, not a folder inside a checkout such as <clone>/books);
  - the source has no uncommitted changes to tracked files, so what travels is what the template committed;
  - the source's personal namespace holds nothing but an empty placeholder;
  - no path it would overwrite has local changes in the clone - staged, unstaged, untracked or ignored.
books/ is never read from the source nor written in the clone, its placeholder excepted. A copy that fails part way
(disk, permissions) is refused with the list of what was already copied. It does not commit: the caller commits,
naming the template commit.

Stdlib only. Exit 0 = in sync (or synced); 1 = --check found work; 2 = refused.
"""
import argparse
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import checkout_role as R                                              # noqa: E402  the ONE role definition


class SyncRefused(Exception):
    """A precondition failed (nothing copied), or a copy failed part way (the message lists what was copied)."""


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if r.returncode != 0:
        raise SyncRefused("git %s failed in %s: %s" % (" ".join(args), cwd,
                                                       r.stderr.decode("utf-8", "replace").strip()[:200]))
    return r.stdout.decode("utf-8")


def _same(a, b):
    """Equal bytes once CRLF line endings are read as LF - the parity the ship process has always used."""
    with open(a, "rb") as fa, open(b, "rb") as fb:
        return fa.read().replace(b"\r\n", b"\n") == fb.read().replace(b"\r\n", b"\n")


def _tracked(repo):
    return [p for p in _git(repo, "ls-files", "-z").split("\0") if p and not R.is_personal(p)]


def _status_paths(repo, *flags):
    """Paths `git status` reports with the given flags (renames count both names), NUL-separated."""
    out, paths, i = _git(repo, "status", "--porcelain=v1", "-z", *flags).split("\0"), set(), 0
    while i < len(out):
        ent = out[i]
        i += 1
        if len(ent) < 4:
            continue
        paths.add(ent[3:])
        if ent[0] in "RC" and i < len(out):
            paths.add(out[i])
            i += 1
    return paths


def _deleted_in_history(repo):
    # -m: a deletion made inside a merge counts too (clone-role review 2, nit b)
    return {p for p in _git(repo, "log", "-m", "--diff-filter=D", "--name-only", "--format=", "-z").split("\0") if p}


def plan(src, dst):
    """-> {"missing", "differ", "deleted_in_template", "clone_only": [...], "same": n} over the source's files."""
    tracked = _tracked(src)
    missing, differ, same = [], [], 0
    for rel in tracked:
        s, d = os.path.join(src, rel), os.path.join(dst, rel)
        if not os.path.isfile(d):
            missing.append(rel)
        elif _same(s, d):
            same += 1
        else:
            differ.append(rel)
    theirs = sorted(set(_tracked(dst)) - set(tracked))
    gone = _deleted_in_history(src)
    return {"missing": missing, "differ": differ, "same": same,
            "deleted_in_template": [p for p in theirs if p in gone],
            "clone_only": [p for p in theirs if p not in gone]}


def _toplevel(path):
    top = _git(path, "rev-parse", "--show-toplevel").strip()
    if os.path.normcase(os.path.realpath(top)) != os.path.normcase(os.path.realpath(path)):
        raise SyncRefused("%s is inside the work tree %s, not its top - give the checkout itself" % (path, top))
    common = _git(path, "rev-parse", "--git-common-dir").strip()
    return os.path.normcase(os.path.realpath(os.path.join(path, common)))


def _preflight(src, dst):
    for path in (src, dst):
        if not os.path.isdir(path):
            raise SyncRefused("%s is not a folder" % path)
    if _toplevel(src) == _toplevel(dst):
        raise SyncRefused("the target IS the source (%s): the same repository - two paths are not two checkouts" % dst)
    role, why = R.checkout_role(src)
    if role != R.TEMPLATE:
        raise SyncRefused("the source is a personal clone (%s) - a sync runs FROM the template only" % why)
    role, why = R.checkout_role(dst)
    if role != R.PERSONAL_CLONE:
        raise SyncRefused("the target is not a declared personal clone (%s) - declare its origin in the "
                          "private-remotes list beside the books first; the direction is never guessed" % why)
    dirty = sorted(_status_paths(src, "--untracked-files=no"))
    if dirty:
        raise SyncRefused("the source has uncommitted changes to %d tracked file(s) (%s) - commit first, so what "
                          "travels is what the template committed" % (len(dirty), ", ".join(dirty[:5])))
    intruders = R.namespace_intruders(src)
    problem = R.placeholder_problem(src)
    if intruders or problem:
        raise SyncRefused("the source's personal namespace is not empty: %s" % (intruders[:5] or problem))


def _say(msg):
    print(str(msg).encode("ascii", "backslashreplace").decode("ascii"))    # a path must never crash the report


def sync(src, dst, check_only=False, say=None):
    """Report, then (unless check_only) copy. -> the plan dict; raises SyncRefused."""
    say = say or _say
    _preflight(src, dst)
    p = plan(src, dst)
    say("sync_clone: %d same, %d missing, %d differing, %d deleted in the template, %d clone-only "
        "(never deleted)" % (p["same"], len(p["missing"]), len(p["differ"]), len(p["deleted_in_template"]),
                             len(p["clone_only"])))
    for kind in ("missing", "differ", "deleted_in_template", "clone_only"):
        for rel in p[kind]:
            say("  %-20s %s" % (kind, rel))
    if p["deleted_in_template"]:
        say("sync_clone: the template deleted %d file(s) the clone still tracks - review and remove them by hand"
            % len(p["deleted_in_template"]))
    todo = p["missing"] + p["differ"]
    if check_only or not todo:
        return p
    # --ignored=traditional with --untracked-files=all lists every ignored file ONE BY ONE; "matching" reported an
    # ignored directory as "dir/" and hid its files, so a clone's file inside an ignored folder (staging/, where the
    # owner's safe-delete rule parks files at their original paths) was overwritten (clone-role review 2, NEW-1).
    # A directory entry, should one still appear, blocks every path beneath it.
    local = _status_paths(dst, "--untracked-files=all", "--ignored=traditional")
    dirs = tuple(p for p in local if p.endswith("/"))
    blocked = sorted(rel for rel in todo if rel in local or rel.startswith(dirs))
    if blocked:
        raise SyncRefused("the clone has local changes to %d path(s) this sync would overwrite: %s"
                          % (len(blocked), ", ".join(blocked[:10])))
    done = []
    try:
        for rel in todo:
            s, d = os.path.join(src, rel), os.path.join(dst, rel)
            os.makedirs(os.path.dirname(d) or dst, exist_ok=True)
            shutil.copyfile(s, d)
            with open(s, "rb") as fa, open(d, "rb") as fb:
                if fa.read() != fb.read():
                    raise OSError("the copy of %s did not land byte-for-byte" % rel)
            done.append(rel)
    except OSError as exc:
        raise SyncRefused("the copy failed part way (%s) after copying %d of %d file(s): %s"
                          % (exc, len(done), len(todo), ", ".join(done[:10]) or "none"))
    say("sync_clone: copied %d file(s); commit them in the clone, naming the template commit" % len(todo))
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bring a personal clone up to date with the template, one way.")
    ap.add_argument("--to", required=True, help="the clone's working tree (its top folder)")
    ap.add_argument("--from", dest="src", default=REPO, help="the template checkout (default: this one)")
    ap.add_argument("--check", action="store_true", help="report only; exit 1 when there is work to do")
    a = ap.parse_args(argv)
    try:
        p = sync(a.src, a.to, check_only=a.check)
    except Exception as exc:        # any failure is a refusal (2), never "--check found work" (1) - review 2, nit f
        kind = "" if isinstance(exc, SyncRefused) else "%s: " % type(exc).__name__
        print("sync_clone: REFUSED - %s%s" % (kind, str(exc).encode("ascii", "backslashreplace").decode("ascii")))
        return 2
    return 1 if a.check and (p["missing"] or p["differ"] or p["deleted_in_template"]) else 0


if __name__ == "__main__":
    sys.exit(main())
