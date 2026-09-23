"""test_concepts.py — the closed registry of things a feeling can be about that are not people.

Gate three, 2026-09-11. Owner: *"wounds are conceptual, a mother with a sick kid gets a wound for
sickness. That's not a word but a concept. So how do we link that concept and others like it."*
The answer is `src/engine/concepts.py`: a flat, engine-owned registry the appraiser seat picks
from, validated by identity, refused by code. This suite pins the four things that make that
deterministic:

  1. THE LIST IS CLOSED. `is_concept` knows the registry and nothing else; an unknown id is refused
     with CONCEPT_UNKNOWN at the engine and READING_CONCEPT_UNKNOWN / TAG_CONCEPT_UNKNOWN at the
     two boundaries.
  2. THE LIBRARY RESOLVES. Every wound row in data/formative_profiles.json names a registry
     concept (the registry was seeded from them), so the composition pass can mint every one.
  3. THE PREFIX IS THE ONLY PARSE. `concept:<id>` in, `<id>` out; a bare id is not a concept about.
  4. THE MENU CARRIES NO NUMBER (hard rule 5) and names every concept exactly as the seat must
     return it.

Stdlib only. Exit 0 = all pass.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import concepts as C                          # noqa: E402
from src.engine import readings as _readings                  # noqa: E402
from src.engine import consolidation as _cons                 # noqa: E402
from src.engine.records import RecordError                    # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _refuses(fn, code):
    try:
        fn()
        return False
    except RecordError as exc:
        return code in str(exc)


def test_the_list_is_closed():
    print("\n[1] THE LIST IS CLOSED")
    check("registry-is-flat-and-non-empty", len(C.REGISTRY) >= 40 and all(isinstance(v, str) for v in C.REGISTRY.values()))
    check("a-known-concept-is-a-concept", C.is_concept("concept:sickness"))
    check("a-bare-id-is-not-an-about", not C.is_concept("sickness"))
    check("an-unknown-id-is-not-a-concept-and-raises-by-name",
          not C.is_concept("concept:zebra") and _refuses(lambda: C.id_of("concept:zebra"), "CONCEPT_UNKNOWN"))
    check("a-prefixless-string-is-refused-by-id_of", _refuses(lambda: C.id_of("sickness"), "CONCEPT_NOT_A_CONCEPT"))
    check("about-round-trips", C.id_of(C.about("fire")) == "fire" and _refuses(lambda: C.about("zebra"), "CONCEPT_UNKNOWN"))
    # the two boundaries
    check("the-reading-boundary-refuses-an-unknown-concept",
          _refuses(lambda: _readings.parse({"readings": [{"path": "WARINESS", "rung": "dread", "about": "concept:zebra"}],
                                            "confidence": "sure"}, percepts=[], present=[]), "READING_CONCEPT_UNKNOWN"))
    rs, _l, _c = _readings.parse({"readings": [{"path": "WARINESS", "rung": "dread", "about": "concept:sickness"}],
                                  "confidence": "sure"}, percepts=[], present=[])
    check("the-reading-boundary-passes-a-known-concept-without-a-percept", rs and rs[0].about == "concept:sickness")
    v = _cons.validate_tags({"type": "mundane", "dimensions": {"threat": 0.5}, "durability": "transient",
                             "subject": "concept:zebra"}, [], {})
    codes = [f.get("code") for f in (v.get("flags") or []) if isinstance(f, dict)]
    check("the-self-tag-boundary-flags-an-unknown-concept", "TAG_CONCEPT_UNKNOWN" in codes, v)
    v2 = _cons.validate_tags({"type": "mundane", "dimensions": {"threat": 0.5}, "durability": "transient",
                              "subject": "concept:sickness"}, [], {})
    codes2 = [f.get("code") for f in (v2.get("flags") or []) if isinstance(f, dict)]
    check("...and-passes-a-known-one-without-a-percept",
          "TAG_CONCEPT_UNKNOWN" not in codes2 and "TAG_TARGET_NOT_PERCEIVED" not in codes2, v2)


def test_the_library_resolves():
    print("\n[2] EVERY LIBRARY WOUND ROW NAMES A REGISTRY CONCEPT")
    lib = json.loads(io.open(os.path.join(REPO, "data", "formative_profiles.json"), encoding="utf-8").read())
    rows = [(p["id"], r) for p in lib for r in p.get("catalog_rows", [])
            if str(r.get("source", "")).split(":")[0] in ("wound", "trauma")]
    check("the-library-has-wound-rows", len(rows) >= 70, len(rows))
    bad = [(pid, r.get("source")) for pid, r in rows if r.get("concept") not in C.REGISTRY]
    check("every-wound-row-names-a-registry-concept", not bad, bad[:4])
    used = {r.get("concept") for _p, r in rows}
    check("the-registry-is-seeded-from-them-not-beside-them", len(used) >= 30, len(used))


def test_the_menu():
    print("\n[3] THE MENU THE SEAT IS SHOWN")
    m = C.menu()
    check("every-concept-is-on-it-in-its-returnable-form", all(("concept:%s " % cid) in m for cid in C.REGISTRY))
    check("no-digit-reaches-the-seat", not any(ch.isdigit() for ch in m))
    check("gloss-reads-either-form", C.gloss("concept:sickness") == C.gloss("sickness") == C.REGISTRY["sickness"])


def main():
    print("test_concepts.py — the closed concept registry")
    for t in (test_the_list_is_closed, test_the_library_resolves, test_the_menu):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
