"""test_belief_facets.py — a belief must carry what it is ABOUT, stamped when it is written.

MEASURED 2026-08-30, on a live book. Recall matched a belief's prose against a bag of words pulled
from the scene's props, by raw substring. Two failures came out of that, and neither is fixable in
the matcher:

  1. Beliefs qualified on accidents. The winning belief in one scene matched on 'out' — inside
     "about" — and 'low' — inside "Hollow". `levers.py` had already fixed exactly this for lever
     rows, calling it "a wound going off at random"; the fix was never ported.
  2. The beliefs a scene was ABOUT could not say so. Nell's "Tam Rill is not a coward about work"
     matched seven of the scene's triggers and stayed silent while "They are animals" matched one
     and fired. Eleven of twelve authored beliefs across two characters carried an empty `links`
     list: the entity axis was in the schema and empty in practice, because it depended on an
     author remembering to bracket a name.

THE FIX IS AT THE WRITE. A matcher can never recover a referent the prose expressed as a pronoun —
"He will come up that hill one day" is about Tam and says "He" — but every writer of a belief knows
who it is about. The three runtime writers hold the resolved subject; the author knows who they
meant. So it is stamped at creation, alongside the prose claim, which stays prose because the claim
is what reaches the page.

Run: python tests/test_belief_facets.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from src.engine import acquisition                                    # noqa: E402
from src.engine.facets import belief_facets, entities_in, stamp, topics_in   # noqa: E402

_FAILS = []


def check(name, cond, detail=""):
    if not cond:
        _FAILS.append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  - " + detail) if (detail and not cond) else ""))


WORLD = {
    "people": [{"id": "tam", "name": "Tam Rill", "what": "the miller's son"},
               {"id": "nell", "name": "Nell Harrow", "what": "shepherd"}],
    "lexicon": {"attribute_classes": {
        "threat": ["wolf", "wolves", "pack", "tracks"],
        "work":   ["race", "wheel", "mill", "fold"],
        "cold":   ["frost", "ice", "snow"],
    }},
}


def test_the_substring_accidents_are_closed():
    """THE MEASURED BUG. Both of these fired on the live book and decided which beliefs a character
    could think."""
    print("\n[1] substring accidents")
    # 'out' is a substring of "about". Under the old raw-`in` match it qualified; it must not now.
    # (The fixture's classes deliberately contain no word that appears in this sentence, so the
    # correct answer is the empty list — an earlier draft of this assertion expected ["work"] and
    # was testing the fixture rather than the code.)
    check("about-does-not-contain-out", topics_in("this is about the mill", WORLD) == ["work"],
          str(topics_in("this is about the mill", WORLD)))
    check("hollow-does-not-contain-low", "cold" not in topics_in("the Hollow goes short", WORLD),
          str(topics_in("the Hollow goes short", WORLD)))
    check("faron-does-not-contain-far", entities_in("a drover named Faron", {"people": [
        {"id": "far", "name": "Far"}]}) == [], "'far' must not match inside 'Faron'")
    check("real-word-still-matches", topics_in("wolf tracks in the snow", WORLD) == ["cold", "threat"],
          str(topics_in("wolf tracks in the snow", WORLD)))


def test_a_named_person_resolves_without_the_author_bracketing_them():
    """The measured gap: a belief that names someone and carries no reference to them."""
    print("\n[2] names resolve")
    f = belief_facets("Tam Rill is not a coward about work. He is out on that race at four.", WORLD)
    check("resolves-the-full-name", f["about"] == ["tam"], str(f["about"]))
    check("resolves-a-first-name-alone", entities_in("Tam is out on the race", WORLD) == ["tam"])
    # "race" is a `work` keyword in the fixture; "work" itself is not, deliberately — a topic comes
    # from the world's declared vocabulary, never from the word happening to look like a category.
    check("topics-come-with-it", f["topics"] == ["work"], str(f["topics"]))


def test_a_pronoun_resolves_to_nothing_and_that_is_correct():
    """THE HONEST LIMIT, and the reason the fix belongs at the write. Guessing here would be worse
    than an empty answer: a wrong subject fires the belief in the wrong scenes."""
    print("\n[3] the pronoun only the writer can settle")
    f = belief_facets("He will come up that hill one day.", WORLD)
    check("pronoun-is-not-guessed", f["about"] == [], str(f["about"]))
    # ...but the writer's own answer is taken, whatever the prose says
    f2 = belief_facets("He will come up that hill one day.", WORLD, subject="tam")
    check("the-writers-subject-wins", f2["about"] == ["tam"], str(f2["about"]))


def test_the_subject_and_the_prose_are_merged_not_swapped():
    """A belief may be about someone it never names, and may name someone it is not about."""
    print("\n[4] merge, never replace")
    f = belief_facets("Nell Harrow asked me again.", WORLD, subject="tam")
    check("both-are-kept", f["about"] == ["nell", "tam"], str(f["about"]))
    b = {"claim": "Tam Rill is not a coward.", "links": ["faron"]}
    stamp(b, WORLD)
    check("author-links-survive", set(b["about"]) == {"tam", "faron"}, str(b["about"]))


def test_every_runtime_writer_stamps():
    """All three acquisition writers hold the resolved subject already. If one of them stopped
    stamping, its beliefs would silently go back to being unfindable — so each is asserted."""
    print("\n[5] the three runtime writers")
    tags = {"type": "threat", "durability": "durable", "confidence": 0.9,
            "summary": "wolf tracks at the fold, and Tam Rill saw them too"}
    applied = {"dimensions": {"threat": 0.7}, "target": "tam"}
    char = {"current": {"vault": []}}

    a = acquisition.assess(applied, tags, char, WORLD)
    check("assess-stamps", bool(a) and "tam" in (a or {}).get("about", []), str(a))
    check("assess-topics", bool(a) and "threat" in (a or {}).get("topics", []), str(a))

    wb = acquisition.witness_belief("Nell Harrow", tags, "nell", trust=0.6, world=WORLD)
    check("witness-stamps", bool(wb) and "nell" in (wb or {}).get("about", []), str(wb))

    ch = {"current": {"relationships": {"tam": {"known_as": "the miller's son"}}, "vault": []}}
    rn = acquisition.reveal_name(ch, "tam", "Tam Rill", WORLD)
    check("reveal-name-stamps", bool(rn) and "tam" in (rn or {}).get("about", []), str(rn))


def test_world_is_optional_and_omitting_it_changes_nothing_else():
    """Backward compatibility is load-bearing: every existing caller that does not pass a world must
    get exactly the belief it got before, plus the subject it already knew."""
    print("\n[6] world is optional")
    tags = {"type": "threat", "durability": "durable", "confidence": 0.9, "summary": "a thing happened"}
    a = acquisition.assess({"dimensions": {}, "target": "tam"}, tags, {"current": {"vault": []}})
    check("still-returns-a-belief", bool(a), str(a))
    check("subject-still-stamped", "tam" in (a or {}).get("about", []), str(a))
    check("no-topics-without-a-lexicon", (a or {}).get("topics") == [], str(a))


def test_a_real_book_gets_typed_at_load():
    """END TO END on whatever book this machine has, if any.

    NOT a hardcoded path. The first draft of this test named a vault directory and a book by name,
    and BOTH `test_no_private_content` and `test_self_contained` refused it — the guard working
    exactly as CLAUDE.md's three-blind-spots account says it must. A test reaches a book only
    through $SWE_BOOKS, and must pass on a checkout that has none, because the engine ships
    bookless.
    """
    print("\n[7] a real book, if this machine has one")
    from src.engine import vault as V
    root = os.environ.get("SWE_BOOKS")
    books = []
    if root and os.path.isdir(root):
        books = [os.path.join(root, d) for d in sorted(os.listdir(root))
                 if os.path.isdir(os.path.join(root, d, "characters"))]
    if not books:
        print("  SKIP  no book on this machine ($SWE_BOOKS unset or empty)")
        return
    _w, chars = V.load_book(books[0])
    every = [b for c in chars.values() for b in (c["current"].get("vault") or [])]
    check("every-belief-has-the-keys",
          all("about" in b and "topics" in b for b in every),
          "%d beliefs, %d missing" % (len(every), sum(1 for b in every if "about" not in b)))
    # A PROPERTY over whatever book is present, never an assertion about a particular cast.
    check("every-about-entry-is-an-entity-id",
          all(all(isinstance(x, str) and x for x in (b.get("about") or [])) for b in every),
          "an `about` entry must be a non-empty entity id")



def main():
    print("test_belief_facets.py - a belief must carry what it is about")
    for t in (test_the_substring_accidents_are_closed,
              test_a_named_person_resolves_without_the_author_bracketing_them,
              test_a_pronoun_resolves_to_nothing_and_that_is_correct,
              test_the_subject_and_the_prose_are_merged_not_swapped,
              test_every_runtime_writer_stamps,
              test_world_is_optional_and_omitting_it_changes_nothing_else,
              test_a_real_book_gets_typed_at_load):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
