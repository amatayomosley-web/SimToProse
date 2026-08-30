"""test_declared_is_read.py — the guard for this repo's named dominant defect class.

"Declared, wired in isolation, never connected." A documented key with no reader is a lie with a
citation. The class has cost this project repeatedly and each instance was found by hand, months
late:

  * `CATALOG.durability_class` — self-described "default durability", zero readers, while three
    modules carried three DIFFERENT durability vocabularies and two docs taught the rejected one.
  * `cfg["location"]` — documented "consumed", read only inside an `if _act:` guard most scenes
    never set, so a scene staged at the fold handed its cast the mill's description.
  * `events.target` — read by the fold to decide who died, written by nothing, so a terminal harm
    marked the ACTOR dead across 223 events in five books.
  * `Ledger.run_config` — called behind `hasattr`, which was always false, so the pinned-bible
    divergence check never ran once.
  * `compounds.recognise` — implemented and tested, called by nothing.
  * `escalate` — computed, stored, printed, counted, and branched on by no code at all.

Every one of those is a key that LOOKED wired. This suite makes the class fail a run instead of a
reader's attention.

WHAT THIS GUARD CAN AND CANNOT SEE. It greps for a textual reference to each declared key outside
the module that declares it. That means:
  - it CANNOT prove a reader does anything useful with what it reads;
  - it CANNOT see a key reached only through a dynamic lookup;
  - it CAN see a key that nothing anywhere so much as names, which is the measured shape of every
    instance above.
A green result here is a claim about REFERENCE, not about correctness. Read it that way.

THE RULE IS TWO-WAY, like the code registry in test_errors.py. A newly-dead key fails. And a key on
the exemption list that GAINS a reader also fails, so wiring one forces the exemption to be
retired rather than left behind as stale documentation of a problem that no longer exists.

Run: python tests/test_declared_is_read.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from src.engine.consolidation import CATALOG                          # noqa: E402

_FAILS = []


def check(name, cond, detail=""):
    if not cond:
        _FAILS.append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  - " + detail) if (detail and not cond) else ""))


# Keys that are DECLARED and genuinely have no reader, each with the decision that left it so.
# An entry here is a debt with a name and an owner, not an excuse. Retire it by wiring the key.
# RETIRED 2026-08-30: `durability_class`. It carried a per-type default durability on all 17
# CATALOG rows and was read by nothing since the day it was written. Wiring it was the alternative
# and it was rejected: for the six durable-class types it would turn an omitted field into an
# ENGINE-ASSERTED permanent baseline change plus a vault belief, from a claim the actor never made
# — the same reasoning that made TAG_DURABILITY_MISSING a refusal rather than a silent default,
# one layer up. consolidation-loop.md Principle 1: the doer labels the deed. The design that
# described it is in git history and in the corrected docs/arc-engine.md note.
#
# NOTE, because this list was wrong once already: `world_map` was on it, on the strength of a grep
# that excluded consolidation.py. It is READ, at consolidation.py:377, to derive ACTOR_TAG_TYPES.
# The guard caught that the moment it stopped excluding the declaring module. An exemption asserted
# from a partial sweep is the same defect as the one being exempted.
_KNOWN_UNREAD = {
    "visibility":
        "CATALOG carries a per-type visibility (including 'private-to-actor' on correction) that is "
        "never copied onto a produced Event — every producer takes records.py's 'public' default, "
        "and the column is INSERTed and never SELECTed. Wiring it changes who can see what, which "
        "is a knowledge-model decision, not a plumbing one.",
}


def _sources():
    """Every .py under src/ and scripts/, as (path, text)."""
    out = []
    for sub in ("src", "scripts"):
        for root, _dirs, files in os.walk(os.path.join(REPO, sub)):
            if "__pycache__" in root:
                continue
            for fn in files:
                if fn.endswith(".py"):
                    p = os.path.join(root, fn)
                    with open(p, encoding="utf-8") as fh:
                        out.append((os.path.relpath(p, REPO).replace("\\", "/"), fh.read()))
    return out


def _readers(key, declaring=None):
    """Every file that READS `key` off a mapping.

    THE DECLARING MODULE COUNTS. A first version excluded it, and that was the wrong rule: the
    defect class is "no reader ANYWHERE", not "no reader elsewhere". `capability_req` is consumed
    by validate_tags inside consolidation.py itself and is perfectly well wired; excluding its own
    module reported it dead. The CATALOG literal's own `"key": value` lines cannot match the
    subscript forms below, so the declaration never counts as its own reader.

    PRECISION MATTERS MORE THAN RECALL HERE. A first draft matched the bare word and reported
    `visibility` as read by three modules — but those were `ev.visibility`, an ATTRIBUTE on the
    Event dataclass, which is a different thing that merely shares a name with the CATALOG column.
    A guard that accepts a same-named unrelated symbol as proof of wiring would let a genuinely
    dead column pass, which is the exact failure it exists to catch.

    So a reader must SUBSCRIPT or GET the key — `row["visibility"]`, `.get("visibility")` — the
    only shapes by which a dict column is actually consumed. Attribute access, a dataclass field
    declaration, and a mention in a comment or docstring all correctly fail to count.
    """
    forms = ('["%s"]' % key, "['%s']" % key, '.get("%s"' % key, ".get('%s'" % key)
    hits = []
    for path, text in _sources():
        if declaring is not None and path == declaring:
            continue
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue          # a mention in a comment is documentation, not a reader
            if any(f in stripped for f in forms):
                hits.append(path)
                break
    return sorted(set(hits))


def test_every_catalog_column_has_a_reader():
    """The CATALOG row is the event vocabulary's schema. A column nothing reads is a promise the
    engine does not keep — and `durability_class` sat unread while the value it was supposed to
    default was killing whole scenes."""
    print("\n[1] CATALOG columns")
    columns = sorted(next(iter(CATALOG.values())).keys())
    check("catalog-has-columns", bool(columns), str(columns))
    for col in columns:
        readers = _readers(col)
        expected_dead = col in _KNOWN_UNREAD
        if expected_dead:
            # TWO-WAY: a known-dead key that GAINS a reader must retire its exemption.
            check("known-unread-still-unread:%s" % col, not readers,
                  "now read by %s — wire it and DELETE its entry from _KNOWN_UNREAD" % readers)
        else:
            check("has-a-reader:%s" % col, bool(readers),
                  "declared in CATALOG and named by no code outside consolidation.py")


def test_the_exemption_list_is_documented_and_current():
    """An exemption without a stated reason is just a silenced failure."""
    print("\n[2] the exemption list")
    columns = set(next(iter(CATALOG.values())).keys())
    for key, why in sorted(_KNOWN_UNREAD.items()):
        check("exemption-names-a-real-column:%s" % key, key in columns,
              "_KNOWN_UNREAD names %r, which is not a CATALOG column — stale entry" % key)
        check("exemption-has-a-reason:%s" % key, len(why) > 80,
              "an exemption needs the decision that left it unread, not a label")


def test_the_guard_can_actually_fail():
    """THE CONTROL. A guard that has never been seen to fail is a coverage claim, not a check —
    `test_negative_control` in the private-content sweep passed for three days while 42 tracked
    files were never walked."""
    print("\n[3] CONTROL — the guard catches a key nothing reads")
    invented = _readers("a_column_no_module_will_ever_name_xyzzy")
    check("invented-key-has-no-readers", invented == [], str(invented))
    # ...and finds one that is genuinely read
    real = _readers("appraisal_map")
    check("real-key-is-found", bool(real), "appraisal_map should be read by the drivers: %s" % real)
    # ...and a same-named ATTRIBUTE elsewhere does NOT count as a reader. `Event.visibility` is a
    # dataclass field that shares its name with the CATALOG column and has nothing to do with it;
    # the first draft of this guard counted it and reported the dead column as wired.
    check("same-named-attribute-is-not-a-reader",
          _readers("visibility") == [],
          "ev.visibility must not count as reading CATALOG[t]['visibility']: %s"
          % _readers("visibility"))
    # ...and a docstring mention does not count either
    check("docstring-mention-is-not-a-reader",
          "src/engine/ledger.py" not in _readers("world_map"),
          "ledger.py names world_map only in prose; it must not count")


def main():
    print("test_declared_is_read.py - declared, wired in isolation, never connected")
    for t in (test_every_catalog_column_has_a_reader,
              test_the_exemption_list_is_documented_and_current,
              test_the_guard_can_actually_fail):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
