"""books.py — resolve a book by slug, so several can be active at once.

A BOOK is a self-contained directory outside the repo: its vault notes, and its
chronicle db beside them. The engine already worked this way (`--vault <path>`),
which means multiple books were always *possible* — but every invocation needed
the full path, and nothing could enumerate what books existed. That is the whole
gap between "possible" and "usable with three books open".

Resolution, in order:
  1. an existing directory  -> itself (the old `--vault <path>` behaviour, intact)
  2. a slug                 -> <SWE_BOOKS>/<slug>

`SWE_BOOKS` is the root holding book directories. Machine-local, so it is an
environment variable and never a committed constant (CLAUDE.md hard rule 1).

Nothing here reads or writes book content — it resolves paths and fails loud.
"""
from __future__ import annotations

__layer__ = "engine"

import os
from .errors import EngineError

ROOT_ENV = "SWE_BOOKS"


class BookError(EngineError):
    """A book could not be resolved — named loudly, never guessed at."""


def slug(book_dir):
    """The stable short name for a book dir. Also names its chronicle db.

    One definition, used everywhere: `direct.py` and `scene.py` each derived
    this independently, which is how two scripts quietly disagree about which
    file is a book's chronicle.
    """
    return os.path.basename(os.path.normpath(book_dir)).lower().replace(" ", "-")


def root():
    """The books root, or None. Never guesses at a location on disk."""
    r = os.environ.get(ROOT_ENV)
    return r if r else None


def resolve(spec):
    """A path or slug -> an absolute book directory. Raises if it is neither.

    Two ways to name a book under the root, tried in this order:

      1. the LITERAL folder name  -> <root>/<spec>
      2. the SLUG of a folder     -> the entry whose slug() equals spec

    Step 2 is the one that makes `--book the-north-reach` work for a book
    whose folder is `The North Reach`. It was documented and never built:
    resolve() joined the raw spec and stopped, so the only books addressable by
    "slug" were the ones already spelled like one. The db was named by slug() the
    whole time, so a book's chronicle could carry a name its own book did not
    answer to.

    Literal wins on a tie so nothing that resolves today changes meaning.
    """
    if not spec or not str(spec).strip():
        raise BookError("no book given")
    spec = str(spec).strip()

    if os.path.isdir(spec):
        return os.path.abspath(spec)

    r = root()
    if r:
        cand = os.path.join(r, spec)
        if os.path.isdir(cand):
            return os.path.abspath(cand)

        hits = [d for d in _book_dirs(r) if slug(d) == slug(spec)]
        if len(hits) == 1:
            return os.path.abspath(hits[0])
        if len(hits) > 1:
            raise BookError(
                "ambiguous book %r: %d folders under %s=%s share that slug (%s). "
                "Rename one, or pass the full path."
                % (spec, len(hits), ROOT_ENV, r,
                   ", ".join(os.path.basename(h) for h in hits)))

        raise BookError(
            "no book %r: not a directory, and not found under %s=%s (available: %s)"
            % (spec, ROOT_ENV, r, ", ".join(available()) or "none"))
    raise BookError(
        "no book %r: not a directory on disk, and %s is unset so a slug cannot be "
        "resolved. Pass a path, or set %s to the folder holding your books."
        % (spec, ROOT_ENV, ROOT_ENV))


def _book_dirs(r):
    """Absolute paths of the book directories under root `r`, sorted.

    A directory counts as a book only if it holds `world/` — the one structural
    marker every book must have (vault.py's contract). Shared by available() and
    resolve() so the two can never disagree about what exists.
    """
    if not r or not os.path.isdir(r):
        return []
    out = []
    for name in sorted(os.listdir(r)):
        d = os.path.join(r, name)
        if os.path.isdir(d) and os.path.isdir(os.path.join(d, "world")):
            out.append(d)
    return out


def available():
    """Slugs under the books root. Empty when unset — never invents a location.

    SLUGS, not folder names: what this returns is what `resolve()` accepts and
    what `db_path()` names the chronicle. It used to return the raw folder name
    while promising slugs, which made the error message on a failed resolve list
    strings that would themselves have failed to resolve.
    """
    return [slug(d) for d in _book_dirs(root())]


def db_path(book_dir):
    """A book's chronicle db: `<book>/runs/<slug>.db` — it lives WITH the book,
    never in the engine repo."""
    return os.path.join(book_dir, "runs", "%s.db" % slug(book_dir))


class CrossBookDbError(BookError):
    """A db was named that does not belong to the book being run."""


def assert_db_for_book(book_dir, db):
    """Refuse a chronicle that belongs to a DIFFERENT book. No-op when `db` is None.

    CLAUDE.md hard rule 1 says several books can be active at once, each with its own
    db, sharing nothing. db_path() made that the DEFAULT; nothing made it TRUE. Both
    runner scripts read `args.db or default_db`, so an explicit --db pointing at
    another book's chronicle was accepted in silence — and the log is append-only, so
    the mistaken turns cannot be withdrawn afterwards. Convention became enforcement
    here, once, rather than in each script (the same reasoning slug() records).

    Raises CrossBookDbError naming both paths; returns the resolved db otherwise.
    """
    if not db:
        return db_path(book_dir)
    book_real = os.path.realpath(book_dir)
    db_real = os.path.realpath(db)
    if os.path.commonpath([book_real, db_real]) != book_real:
        raise CrossBookDbError(
            "db does not belong to this book — refusing to write across books.\n"
            "  book: %s\n  db:   %s\n"
            "A book's chronicle lives at <book>/runs/<slug>.db. Drop --db to use it, "
            "or run the book that owns that db." % (book_real, db_real))
    return db_real
