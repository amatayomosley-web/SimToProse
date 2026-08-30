#!/usr/bin/env python3
"""test_books.py — several books active at once, resolved by slug.

The engine always supported multiple books (each is a directory with its
chronicle db beside it), but every invocation needed the full path and nothing
could enumerate what existed. This is the gap between *possible* and *usable
with three books open*.

Contracts:
  - a path still resolves (the old --vault behaviour must not break)
  - the literal folder name resolves under $SWE_BOOKS
  - a SLUG resolves under $SWE_BOOKS, for a folder whose name is not already one
    ("The North Reach" -> "the-north-reach"). This is the contract
    the docs always promised and the suite never tested: every case here used to
    pass a raw folder name, so resolve() never had to slug anything and the
    literal-join implementation looked correct for two months.
  - available() returns SLUGS — the strings resolve() accepts, so the error
    message on a failed resolve cannot list names that would themselves fail
  - an unresolvable book FAILS LOUD and names why — never silently picks one,
    including when two folders slug to the same string
  - slug/db_path have ONE definition (direct.py and scene.py each derived their
    own, which is how two scripts quietly disagree about which file is a book's
    chronicle)

Stdlib only, script-style. Exit 0 = all pass.
"""
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import books                                      # noqa: E402


class Skip(Exception):
    """This case cannot run here, and says so instead of returning green.

    A test that bails with a bare `return` reports PASS for a line it never
    executed — the same shape as the defect this file exists to catch. A skip is
    counted and printed separately so an all-green run can still be read for
    what it did NOT cover.
    """


def _make_books(root, names):
    for n in names:
        os.makedirs(os.path.join(root, n, "world"), exist_ok=True)
        os.makedirs(os.path.join(root, n, "characters"), exist_ok=True)


def test_path_still_resolves_without_the_root(tmp):
    """--vault <path> predates slugs and must keep working untouched."""
    _make_books(tmp, ["Book One"])
    os.environ.pop(books.ROOT_ENV, None)
    d = books.resolve(os.path.join(tmp, "Book One"))
    assert os.path.isdir(d) and d.endswith("Book One"), d


def test_literal_folder_name_resolves_under_the_root(tmp):
    """The raw folder name keeps working — this is what the suite always tested,
    under a name that claimed it was testing slugs."""
    _make_books(tmp, ["Book One", "Second Book"])
    os.environ[books.ROOT_ENV] = tmp
    assert books.resolve("Second Book").endswith("Second Book")


def test_slug_roundtrip_resolves_a_spaced_folder(tmp):
    """THE contract the docs promise: a book whose folder has spaces and capitals
    answers to its slug — the same string db_path() names its chronicle with.

    This is the test whose absence hid the defect. Every other test in this file
    passed a raw directory name, so `resolve()` never had to slug anything.
    """
    _make_books(tmp, ["The North Reach"])
    os.environ[books.ROOT_ENV] = tmp
    d = os.path.join(tmp, "The North Reach")

    assert books.slug(d) == "the-north-reach", books.slug(d)
    assert books.resolve("the-north-reach") == os.path.abspath(d)
    assert books.resolve(books.slug(d)) == os.path.abspath(d), "slug->resolve must round-trip"
    assert books.db_path(books.resolve(books.slug(d))).endswith(
        os.path.join("runs", "the-north-reach.db"))


def test_available_returns_slugs_not_folder_names(tmp):
    """available() feeds the failed-resolve error message. When it listed raw
    folder names it printed strings that would themselves fail to resolve."""
    _make_books(tmp, ["The North Reach", "Book One"])
    os.environ[books.ROOT_ENV] = tmp
    # available() is sorted by FOLDER name, so "Book One" precedes "The North Reach"
    assert books.available() == ["book-one", "the-north-reach"], books.available()
    for s in books.available():
        assert os.path.isdir(books.resolve(s)), "everything listed must resolve"


def test_ambiguous_slug_fails_loud_and_names_both(tmp):
    """Two folders can slug to one name. Picking one silently would send a run's
    events into the wrong book's chronicle.

    NOT REACHABLE ON A CASE-INSENSITIVE FILESYSTEM, and it says so out loud
    rather than returning green. Two distinct folder names that slug alike must
    differ by a space<->hyphen swap somewhere, which makes one of them equal to
    the slug modulo case — so Windows/macOS satisfy the literal branch first and
    never reach the ambiguity check. The guard is still correct and still fires
    on Linux; a silent `return` here would be a test reporting a pass for a line
    it never executed.
    """
    _make_books(tmp, ["Book One", "Book-One"])
    os.environ[books.ROOT_ENV] = tmp
    if len(books.available()) < 2 or os.path.isdir(os.path.join(tmp, "book-one")):
        raise Skip("case-insensitive filesystem: the literal branch shadows the ambiguity check")
    try:
        books.resolve("book-one")
    except books.BookError as e:
        assert "ambiguous" in str(e).lower(), str(e)
        assert "Book One" in str(e) and "Book-One" in str(e), str(e)
        return
    raise AssertionError("an ambiguous slug must fail loud, never pick one")


def test_literal_name_wins_over_a_slug_collision(tmp):
    """Precedence, pinned: an exact folder name is never shadowed by another
    folder that merely slugs to the same string."""
    _make_books(tmp, ["book-one", "Book One"])
    os.environ[books.ROOT_ENV] = tmp
    if len(books.available()) < 2:
        raise Skip("case-insensitive filesystem: the two folders collapsed into one")
    assert books.resolve("book-one") == os.path.abspath(os.path.join(tmp, "book-one"))


def test_three_books_are_independent(tmp):
    """The point of the exercise: three active books, three slugs, three dbs,
    nothing shared."""
    names = ["Book One", "Second Book", "Third Book"]
    _make_books(tmp, names)
    os.environ[books.ROOT_ENV] = tmp
    assert books.available() == ["book-one", "second-book", "third-book"], books.available()
    dbs = [books.db_path(books.resolve(n)) for n in names]
    assert len(set(dbs)) == 3, dbs
    for d in dbs:
        assert d.startswith(tmp), "a book's chronicle must live WITH the book, not in the repo"


def test_a_db_from_another_book_is_refused(tmp):
    """Independence was the DEFAULT (db_path) and nothing made it TRUE: both runner
    scripts read `args.db or default_db`, so --db pointing at another book's chronicle
    was accepted in silence — and the log is append-only, so those turns cannot be
    withdrawn. assert_db_for_book is where convention became enforcement."""
    _make_books(tmp, ["Book One", "Second Book"])
    os.environ[books.ROOT_ENV] = tmp
    one, two = books.resolve("Book One"), books.resolve("Second Book")

    assert books.assert_db_for_book(one, None) == books.db_path(one), "unset --db uses the book's own"
    assert books.assert_db_for_book(one, books.db_path(one)) == os.path.realpath(books.db_path(one))

    try:
        books.assert_db_for_book(one, books.db_path(two))
    except books.CrossBookDbError as e:
        assert "Book One" in str(e) and "Second Book" in str(e), "the error must name BOTH paths"
    else:
        raise AssertionError("a db from another book was accepted")

    try:
        books.assert_db_for_book(one, os.path.join(REPO, "runs", "ashford.db"))
    except books.CrossBookDbError:
        pass
    else:
        raise AssertionError("a db in the engine repo was accepted for a book")


def test_unresolvable_slug_fails_loud_and_lists_what_exists(tmp):
    _make_books(tmp, ["Book One"])
    os.environ[books.ROOT_ENV] = tmp
    try:
        books.resolve("Nope")
    except books.BookError as e:
        assert "Nope" in str(e) and "book-one" in str(e), str(e)
        return
    raise AssertionError("an unknown slug must fail loud, never resolve to something else")


def test_slug_without_a_root_explains_the_fix(tmp):
    os.environ.pop(books.ROOT_ENV, None)
    try:
        books.resolve("malice")
    except books.BookError as e:
        assert books.ROOT_ENV in str(e), str(e)
        return
    raise AssertionError("a slug with no root must fail loud")


def test_empty_spec_fails_loud(tmp):
    for bad in ("", "   ", None):
        try:
            books.resolve(bad)
        except books.BookError:
            continue
        raise AssertionError("empty book spec accepted: %r" % (bad,))


def test_slug_and_db_path_are_one_definition(tmp):
    _make_books(tmp, ["A Small Test Book"])
    d = os.path.join(tmp, "A Small Test Book")
    assert books.slug(d) == "a-small-test-book", books.slug(d)
    assert books.db_path(d).endswith(os.path.join("runs", "a-small-test-book.db")), books.db_path(d)
    assert books.slug(d + os.sep) == books.slug(d), "a trailing separator must not change the slug"


def test_available_is_empty_without_a_root(tmp):
    os.environ.pop(books.ROOT_ENV, None)
    assert books.available() == [], "must never invent a books location"


def test_available_skips_non_books(tmp):
    _make_books(tmp, ["Real Book"])
    os.makedirs(os.path.join(tmp, "not-a-book"), exist_ok=True)   # no world/
    os.environ[books.ROOT_ENV] = tmp
    assert books.available() == ["real-book"], books.available()


def test_a_non_book_folder_does_not_resolve_by_slug(tmp):
    """The world/ marker gates resolution too, not just listing — otherwise a
    stray sibling folder could be adopted as a book by slug."""
    _make_books(tmp, ["Real Book"])
    os.makedirs(os.path.join(tmp, "Not A Book"), exist_ok=True)   # no world/
    os.environ[books.ROOT_ENV] = tmp
    try:
        books.resolve("not-a-book")
    except books.BookError:
        return
    raise AssertionError("a folder without world/ must not resolve as a book")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    saved = os.environ.get(books.ROOT_ENV)
    failed = skipped = 0
    for t in tests:
        tmp = tempfile.mkdtemp(prefix="swe_books_")
        try:
            t(tmp)
            print("  PASS  %s" % t.__name__)
        except Skip as e:
            skipped += 1
            print("  SKIP  %s: %s" % (t.__name__, e))
        except Exception as e:
            failed += 1
            print("  FAIL  %s: %s" % (t.__name__, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if saved is None:
        os.environ.pop(books.ROOT_ENV, None)
    else:
        os.environ[books.ROOT_ENV] = saved
    print("\n%d/%d passed%s" % (len(tests) - failed - skipped, len(tests),
                                ", %d skipped" % skipped if skipped else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
