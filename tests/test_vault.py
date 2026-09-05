#!/usr/bin/env python3
"""test_vault.py — the Obsidian book-vault loader (gate: swe-engine-vault-loader).

Proves: parse_note (engine block + [[links]] + Beliefs bullets), load_book (world + characters
validated by the engine), and the links-are-live-machinery property: a belief whose claim text
does NOT contain a trigger fires anyway through its [[linked note name]].
Script-style, stdlib only, exit 0 = all pass.
"""
import json
import io
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.vault import load_book, parse_note, VaultError     # noqa: E402
from src.engine.scene import assemble                              # noqa: E402
from src.engine.state import build_profile                         # noqa: E402
from src.engine.records import PRIMARIES                           # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


CHAR_ENGINE = {
    "fixed": {"name": "Mira", "genotype": {
        "threat_reactivity": "typical", "approach_drive": "elevated", "affiliation_attachment": "typical",
        "anger_proneness": "low", "effortful_control": "typical", "sensitivity": "elevated"}},
    "baseline": {
        "temperament": {p: {"mean": m, "variability": 0.1} for p, m in
                        zip(PRIMARIES, (0.6, 0.4, 0.2, 0.2, 0.5, 0.3, 0.35, 0.2))},
        "traits": {"emotionality": {"mean": 0.5}, "agreeableness": {"mean": 0.6}, "extraversion": {"mean": 0.4}},
        "model": {"schwartz": {"security": 0.6, "benevolence": 0.7}, "moral_foundations": {"care_harm": 0.7},
                  "needs": {"relatedness": 0.6, "competence": 0.5}},
        "drives": {"goals": [{"goal": "tend the lighthouse lamp", "urgency": 0.7}],
                   "fears_wounds": [{"wound": "the wreck she watched from the gallery"}],
                   "orientation": "the lamp must never go dark"},
        "skills": {"perception": 0.8, "insight": 0.7, "lamp_craft": 0.9, "combat": 0.1},
        "voice": {"register": "spare, weather-worn", "tic": "names the wind before speaking"},
    },
    "current": {
        # DERIVED over PRIMARIES with per-primitive overrides. A zip against a fixed tuple
        # TRUNCATES SILENTLY when the basis grows — which is how this fixture lost DISGUST
        # when it became the eighth primitive, and the failure surfaced deep inside
        # levers.effective rather than here.
        "affect": dict({p: 0.30 for p in PRIMARIES},
                       SEEKING=0.6, FEAR=0.4, RAGE=0.2, LUST=0.2, CARE=0.5, PLAY=0.35),
        "condition": {"energy": 0.8, "allostatic_load": 0.2},
        "active_goals": [{"goal": "tend the lighthouse lamp", "urgency": 0.7}],
        "relationships": {"tomas_keeper": {"trust": 0.6, "affinity": 0.5, "respect": 0.6, "debt": 0.1}},
        "vault": [], "zone": "the rock", "location": "lamp_room",
    },
}

WORLD_ENGINE = {
    "season": "storm season on the rock",
    "lexicon": {
        "attribute_classes": {"lamp": ["lamp", "light", "wick", "oil"],
                              "storm": ["storm", "gale", "swell"],
                              "wreck": ["wreck", "shipwreck", "hull", "drowned"]},
        "subtle_cues": {"failing-wick": ["guttering", "sputters"]},
        "subtle_cue_classes": ["lamp"],
    },
    "locations": [{"id": "lamp_room", "what": "the lamp room at the tower top"}],
    "people": [],
}

CHAR_NOTE = """---\ntype: character
id: Mira
---
# Mira
The keeper of the rock. Canon prose lives here, linking [[Tomas Keeper]] and [[The Lamp]].

```json
%s
```

## Beliefs
- (1.0, lived) the night the hull broke on the reef, I watched from the gallery [[The Wreck of the Salt Rose]]
- (0.6, told) Tomas swears the southern channel is safe in a north wind [[Tomas Keeper]]
""" % json.dumps(CHAR_ENGINE, indent=1)

WORLD_NOTE = """---
type: world
id: The Rock
---
# The Rock
A lighthouse on a bare reef. [[Mira]] keeps it.

```json
%s
""" % (json.dumps(WORLD_ENGINE, indent=1) + "\n```")

PERSON_NOTE = """---
type: person
id: tomas_keeper
---
The relief keeper who rows out monthly; swears by the southern channel.
"""


def _mk_vault(tmp):
    book = os.path.join(tmp, "The Rock and the Rose")
    for sub in ("world", "characters", "people"):
        os.makedirs(os.path.join(book, sub), exist_ok=True)
    open(os.path.join(book, "world", "The Rock.md"), "w", encoding="utf-8").write(WORLD_NOTE)
    open(os.path.join(book, "characters", "Mira.md"), "w", encoding="utf-8").write(CHAR_NOTE)
    open(os.path.join(book, "people", "Tomas Keeper.md"), "w", encoding="utf-8").write(PERSON_NOTE)
    return book


def test_parse_note(tmp):
    print("\n[1] PARSE NOTE")
    book = _mk_vault(tmp)
    n = parse_note(os.path.join(book, "characters", "Mira.md"))
    check("type-and-id", n["type"] == "character" and n["id"] == "Mira")
    check("engine-block-loads", isinstance(n["engine"], dict) and n["engine"]["fixed"]["name"] == "Mira")
    check("links-extracted", "Tomas Keeper" in n["links"] and "The Wreck of the Salt Rose" in n["links"])
    check("beliefs-parsed", len(n["beliefs"]) == 2 and n["beliefs"][0]["confidence"] == 1.0
          and n["beliefs"][1]["provenance"] == "told")
    check("belief-links-attached", n["beliefs"][0]["links"] == ["The Wreck of the Salt Rose"])
    check("belief-claim-unwrapped", "[[" not in n["beliefs"][0]["claim"])


def test_load_book_validates(tmp):
    print("\n[2] LOAD BOOK -> ENGINE-VALID")
    book = _mk_vault(tmp)
    world, chars = load_book(book)
    check("one-character", list(chars) == ["mira"])
    char = chars["mira"]
    check("beliefs-became-vault", len(char["current"]["vault"]) == 2)
    check("person-note-joined-world", any(p["id"] == "tomas_keeper" for p in world.get("people", []))
          and "relief keeper" in [p for p in world["people"] if p["id"] == "tomas_keeper"][0]["what"])
    build_profile(char)                                            # raises if schema-invalid
    packet = assemble(char, world, {"event": {"text": "The lamp gutters in the gale.", "kind": "threat"},
                                    "recent": [], "location": "lamp_room"},
                      char["current"]["affect"], char["current"]["condition"])
    check("assemble-runs-on-vault-book", len(packet["volatile"]["percepts"]) >= 1)


def test_links_are_live_triggers(tmp):
    print("\n[3] LINKS ARE LIVE MACHINERY")
    book = _mk_vault(tmp)
    world, chars = load_book(book)
    char = chars["mira"]
    # The event mentions Tomas — the belief's CLAIM contains "Tomas" too, so strip it to isolate
    # the link path: a belief whose claim text shares NO word with the trigger fires via its link.
    char["current"]["vault"][1]["claim"] = "the southern channel is safe in a north wind, he swears"
    packet = assemble(char, world, {"event": {"text": "Tomas Keeper rows out through the swell, waving.",
                                              "kind": "mundane"}, "recent": [], "location": None},
                      char["current"]["affect"], char["current"]["condition"])
    fired = [r["claim"] for r in packet["volatile"]["recall"]]
    check("link-fired-the-belief", any("southern channel" in c for c in fired),
          "recall=%s" % fired)


def test_fail_loud(tmp):
    print("\n[4] FAIL LOUD")
    book = _mk_vault(tmp)
    bad = os.path.join(book, "characters", "Broken.md")
    open(bad, "w", encoding="utf-8").write("---\ntype: character\n---\n# Broken\nno engine block\n")
    try:
        load_book(book)
        check("missing-engine-block-raises", False, "loaded a character with no engine block")
    except VaultError:
        check("missing-engine-block-raises", True)
    os.remove(bad)
    try:
        load_book(os.path.join(book, "nope"))
        check("missing-folder-raises", False)
    except VaultError:
        check("missing-folder-raises", True)


def test_frontmatter_is_carried_not_dropped(tmp):
    """An authored frontmatter key must not vanish without a word.

    `parse_note` kept `type` and `id` and silently discarded every other key — matched by the
    regex, checked against a whitelist, thrown away. Measured across the three real books on
    2026-08-24: type 36, id 32, source 3, pulled 3, note 1. Seven authored values reaching nothing.

    Third instance of this shape in one repo: `consolidation._KNOWN_DIMS` went stale and discarded
    EVERY appraisal in a live run, and THE LAW's first draft dropped unknown identity keys and came
    back green. This module's own beliefs guard exists for the same reason and records its cost at
    41 of 77 beliefs. Dropping is worse than failing.
    """
    print(chr(10) + "[5] FRONTMATTER IS CARRIED — no key is thrown away in silence")
    path = os.path.join(tmp, "extra.md")
    note = ["---", "type: character", "id: wren", "source: field notes",
            "pulled: 2026-03-04", "note: verify before use", "---", "", "body", ""]
    io.open(path, "w", encoding="utf-8").write(chr(10).join(note))
    n = parse_note(path)
    check("type-and-id-still-land-in-their-own-slots", n["type"] == "character" and n["id"] == "wren")
    check("and-are-also-in-frontmatter",
          n["frontmatter"]["type"] == "character" and n["frontmatter"]["id"] == "wren")
    check("the-keys-that-used-to-vanish-are-here",
          n["frontmatter"].get("source") == "field notes"
          and n["frontmatter"].get("pulled") == "2026-03-04"
          and n["frontmatter"].get("note") == "verify before use", n["frontmatter"])
    check("nothing-is-coerced", isinstance(n["frontmatter"]["pulled"], str),
          "a guessed date format yields a confident wrong value; the raw string is honest")

    bare = os.path.join(tmp, "bare.md")
    io.open(bare, "w", encoding="utf-8").write("no frontmatter at all" + chr(10))
    b = parse_note(bare)
    check("a-note-with-no-frontmatter-parses-as-before",
          b["frontmatter"] == {} and b["id"] == "bare" and b["type"] is None)

    src = io.open(os.path.join(REPO, "src", "engine", "vault.py"), encoding="utf-8").read()
    check("the-whitelist-cannot-quietly-return",
          'note["frontmatter"][key] = value' in src,
          "the drop-everything-else filter is back")


def main():
    print("test_vault.py — the Obsidian book-vault loader\n")
    tmp = tempfile.mkdtemp(prefix="swe_vault_")
    try:
        for t in (test_parse_note, test_load_book_validates, test_links_are_live_triggers,
                  test_frontmatter_is_carried_not_dropped, test_fail_loud):
            t(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
