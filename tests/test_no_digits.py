"""test_no_digits.py — THE LAW: no number describing a character reaches them.

`docs/design.md`: *"The LLM never sees raw stats; numbers live in the DB; directions live in the
prompt."* CLAUDE.md makes it hard rule 5 and calls it THE LAW. It was true of `direction.py`'s four
surfaces — affect, condition, edges, sureness — and false everywhere else, because `prompt.py`
json.dumps'd the stable identity prefix, the goals and the percepts straight into the message.

MEASURED before the fix, on one fixture:

    FLOATS IN THE WHOLE PROMPT: ['0.0','0.1','0.3','0.31','0.5','0.6','0.66',
                                 '0.72','0.77','0.8','0.85','0.9','1.0']

Trait means and variability, every worth-menu weight, the regard map, goal urgency, wound intensity
and percept fidelity. `scene.py:_strip_notes` stated the old position in its own docstring: "The
substrate (numbers, structure) stays — only the commentary ABOUT it is removed."

A law with no guard is a comment. This suite is the guard.

WHAT IT BANS, EXACTLY. Decimals, and only in what the actor is TOLD.

  * INTEGERS are fine. A year, an age, "three days", a `role_tier` — those are content an author
    wrote, not engine scalars. Every engine scalar in this repo is a float in [0,1]; banning
    integers would forbid legitimate prose and make the guard unusable, so it would get switched off.
  * THE REPLY CONTRACT is exempt, and the split is at "Reply as ONE JSON object:". After that point
    the prompt describes the SCHEMA OF THE ACTOR'S REPORT — "emit 0.1-0.3", "each 0..1 where 0.5 is
    neutral". Those digits describe the scale the actor must WRITE ON, not the character. The law is
    about what the model is told about the person it is playing.

    That exemption is a real one and worth naming rather than burying: the cleaner end state is a
    contract that asks for WORDS and lets the engine map them to numbers, which would delete the
    exemption entirely. It is not done here because `consolidation.validate_tags` expects floats and
    the whole appraisal calibration is fitted to them.
  * AUTHORED PROSE is the engine's business only to REPORT, never to rewrite. A real book was found
    carrying design notes inside string values — "tool_reach x0.35 · act_latency x0.3" — and those
    reach the actor verbatim because the identity prefix carries an author's words as written.
    `direct_identity` bands the engine's own scalars and leaves prose alone; `scripts/lint_book.py`
    WARNS on a decimal in authored identity text so a human decides. A renderer that edited an
    author's sentences to satisfy a guard would be a worse failure than the leak.

WHAT IT DOES NOT DO: a renderer with no phrase table for a field is NOT a reason to refuse a book.
The first version of `direct_identity` raised on any number it had no table for, and that took down
two of three real books on first contact — `goals[].priority`, `goals[].satisfaction`,
`voice.assertiveness`, `orientation.agency` are all fields an author invented and the engine never
specified. Named scalars now fall back to a banded generic. The law is "no digits", not "every field
must be hand-phrased", and enforcing the second at the cost of the first is how a guard gets
switched off. A number OUTSIDE [0,1] still refuses: that is not a weight, and guessing at it would
be the silent-drop failure in a new place.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.identity_view import direct_goals, direct_identity, direct_percepts  # noqa: E402
from src.engine.prompt import build_turn_messages                                # noqa: E402
from src.engine.records import PRIMARIES                                         # noqa: E402
from src.engine.scene import assemble                                            # noqa: E402

_FAILS = []
_DECIMAL = re.compile(r"\d+\.\d+")
_CONTRACT = "Reply as ONE JSON object:"


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _fixture():
    """An invented character with a NUMBER IN EVERY LEAKING FIELD — the point is to give the guard
    something to find. Engine fixture, never a book (CLAUDE.md hard rule 1)."""
    char = {
        "fixed": {"id": "wren", "name": "Wren", "role_tier": 2,
                  "genotype": {"threat_reactivity": "high", "effortful_control": "low",
                               "anger_proneness": "typical"}},
        "baseline": {
            "temperament": {p: {"mean": 0.4, "variability": 0.12} for p in PRIMARIES},
            "traits": {"emotionality": {"mean": 0.78, "variability": 0.1},
                       "extraversion": {"mean": 0.22}, "agreeableness": {"mean": 0.66},
                       "conscientiousness": {"mean": 0.91}, "openness": {"mean": 0.34},
                       "honesty_humility": {"mean": 0.55}},
            "model": {"schwartz": {"benevolence": 0.85, "power": 0.15, "security": 0.62,
                                   "tradition": 0.28},
                      "moral_foundations": {"care_harm": 0.77, "authority": 0.19},
                      "needs": {"relatedness": 0.71, "autonomy": 0.33},
                      "regard": {"outsiders": 0.24, "kin": 0.95}},
            "skills": {"perception": 0.63, "insight": 0.58, "combat": 0.41},
            "drives": {"goals": [{"goal": "get the boy off the road", "urgency": 0.93},
                                 {"goal": "keep the shop open", "urgency": 0.35}],
                       "fears_wounds": [{"wound": "the dark water", "intensity": 0.88,
                                         "trigger": ["water", "dark"]},
                                        {"wound": "being laughed at", "intensity": 0.21}],
                       "orientation": "she takes the practical option and regrets it later"},
            "voice": {"register": "plain, short sentences"},
            "relationship_priors": {"default_trust": 0.45},
            "provenance": {"temperament.FEAR": "the flood, age nine"}},
        "current": {"affect": {p: 0.45 for p in PRIMARIES},
                    "condition": {"energy": 0.7, "allostatic_load": 0.3},
                    "location": "yard", "zone": "outer",
                    "vault": [{"claim": "the yard is where the water took her brother",
                               "confidence": 0.82, "provenance": "lived", "believed_value": True,
                               "links": ["dark"]}],
                    "relationships": {"joss": {"trust": 0.8, "affinity": 0.62, "respect": 0.5,
                                               "debt": 0.0, "known_as": "the apprentice"}},
                    "active_goals": [{"goal": "get the boy off the road", "urgency": 0.93}]}}
    world = {"world": "w", "switches": {"magic": False, "divine": False, "beings": False},
             "locations": [{"id": "yard", "what": "the yard behind the shop"}],
             "people": [{"id": "joss", "name": "Joss", "what": "the apprentice"}]}
    return char, world


def _prompt():
    char, world = _fixture()
    packet = assemble(char, world,
                      {"event": {"text": "A door bangs somewhere out in the dark.", "kind": "threat"},
                       "recent": [], "location": "yard"},
                      dict(char["current"]["affect"]), char["current"]["condition"])
    msgs = build_turn_messages(packet, "A door bangs somewhere out in the dark.",
                               char["baseline"]["temperament"], char["current"]["relationships"])
    return packet, "\n".join(m["content"] for m in msgs)


def test_the_law():
    print("\n[1] THE LAW — no decimal describing the character reaches the actor")
    _, whole = _prompt()
    told = whole.split(_CONTRACT)[0]                  # what the actor is TOLD
    asked = whole[len(told):]                         # what the actor is ASKED TO WRITE
    leaks = sorted(set(_DECIMAL.findall(told)))
    if leaks:
        for line in told.split("\n"):
            if _DECIMAL.search(line):
                print("       LEAK: %s" % line.strip()[:160])
    print("       decimals in what the actor is told : %s" % (leaks or "NONE"))
    print("       decimals in the reply contract     : %s (exempt — the scale they report ON)"
          % (sorted(set(_DECIMAL.findall(asked))) or "none"))
    check("no-decimals-reach-the-actor", not leaks, leaks)
    check("the-contract-boundary-exists", _CONTRACT in whole,
          "the exemption is only sound if the split point is real")


def test_the_information_survives():
    print("\n[2] AND NOTHING WAS LOST — the digits went, the characterisation stayed")
    packet, whole = _prompt()
    told = whole.split(_CONTRACT)[0]
    for name, needle in (("the-goal-is-still-named", "get the boy off the road"),
                         ("the-wound-is-still-named", "the dark water"),
                         ("the-trigger-survives", "water"),
                         ("the-belief-is-still-recalled", "took her brother"),   # recall fires on PERCEPT
                                                              # attributes (yard/shop/threat),
                                                              # never on raw event text
                         ("the-voice-survives", "plain, short sentences"),
                         ("the-orientation-survives", "regrets it later"),
                         ("the-provenance-survives", "the flood, age nine"),
                         ("the-percept-is-still-there", "yard")):
        check(name, needle in told, needle)
    # the values are RANKED rather than dropped, and the ranking is right
    ident = direct_identity(packet["stable"])
    worth = ident["what you weigh"]
    print("       holds : %s" % worth.get("you will not trade these away"))
    print("       slights: %s" % worth.get("these weigh little with you"))
    check("the-highest-value-is-held", "benevolence" in worth["you will not trade these away"])
    check("the-lowest-is-not", "power" not in worth["you will not trade these away"],
          "ranked per-family, a 3-value sheet listed power at 0.15 as a thing she would not trade away")
    check("the-lowest-is-slighted", "power" in worth["these weigh little with you"])
    check("a-neutral-weight-is-neither", "honesty humility" not in str(worth),
          "an authored 0.5 says 'average'; claiming it as a conviction invents one")
    check("the-regard-map-is-banded", "kin" in str(worth.get("how you hold each people")))


def test_the_surfaces_are_pure():
    print("\n[3] THE RENDERERS THEMSELVES — pure, total, and fail-loud")
    packet, _ = _prompt()
    stable = packet["stable"]
    before = json.dumps(stable, sort_keys=True)
    direct_identity(stable)
    check("direct_identity-does-not-mutate", json.dumps(stable, sort_keys=True) == before)
    out = direct_identity(stable)
    check("identity-is-digit-free", not _DECIMAL.findall(json.dumps(out)), json.dumps(out)[:200])
    check("unknown-keys-pass-through", direct_identity({"future_field": "kept"})["future_field"] == "kept",
          "a field added later must not be silently dropped")
    check("variability-is-not-self-knowledge", "variability" not in json.dumps(out),
          "it is a sampling parameter, not something a person knows about themselves")
    check("goals-are-digit-free",
          not _DECIMAL.findall(json.dumps(direct_goals(packet["volatile"]["goals"]))))
    check("percepts-are-digit-free",
          not _DECIMAL.findall(json.dumps(direct_percepts(packet["volatile"]["percepts"]))))
    for label, fn in (("identity", lambda: direct_identity("nope")),
                      ("goals", lambda: direct_goals("nope")),
                      ("percepts", lambda: direct_percepts("nope"))):
        try:
            fn()
            check("%s-fails-loud" % label, False, "accepted a non-collection silently")
        except ValueError:
            check("%s-fails-loud" % label, True)
    # an empty sheet must not crash, and must not invent
    check("an-empty-sheet-renders", isinstance(direct_identity({}), dict))
    check("empty-goals-render", direct_goals([]) == [])


def test_no_new_leak_creeps_back():
    print("\n[4] AN UNHANDLED FIELD IS BANDED, NOT DROPPED AND NOT LEAKED")
    char, world = _fixture()
    # Fields with no phrase table. The first three are real dead schema fields (SPEC-LEDGER lists
    # `model.resolution_priority` and `goals[].satisfaction` as stored with zero consumers); the
    # rest are the shapes found on REAL books the first time this renderer met one.
    char["baseline"]["model"]["resolution_priority"] = {"loyalty_over_truth": 0.87}
    char["baseline"]["drives"]["goals"].append({"goal": "invented later", "urgency": 0.71,
                                                "satisfaction": 0.44, "priority": 0.9})
    char["baseline"]["voice"]["assertiveness"] = 0.65
    char["baseline"]["drives"]["orientation"] = {"agency": 0.8, "locus": "internal"}
    char["baseline"]["model"]["a_field_nobody_has_written_yet"] = 0.42

    packet = assemble(char, world,
                      {"event": {"text": "A door bangs.", "kind": "mundane"},
                       "recent": [], "location": "yard"},
                      dict(char["current"]["affect"]), char["current"]["condition"])
    msgs = build_turn_messages(packet, "A door bangs.", char["baseline"]["temperament"],
                               char["current"]["relationships"])
    told = "\n".join(m["content"] for m in msgs).split(_CONTRACT)[0]
    check("still-no-decimals", not _DECIMAL.findall(told), sorted(set(_DECIMAL.findall(told))))

    out = direct_identity(packet["stable"])
    blob = json.dumps(out)
    # NOT DROPPED: every one of them is still present, said in words
    for name, needle in (("priority-is-said", "nothing you want outranks this"),
                         ("satisfaction-is-said", "you have made a start"),
                         ("assertiveness-is-said", "you press a point until it is answered"),
                         # 0.8 sits exactly ON the 0.80 band edge, so it lands in the TOP band
                         ("agency-is-said", "you treat every outcome as yours to have caused")):
        check(name, needle in blob, needle)
    check("a-field-with-no-table-still-lands", "a_field_nobody_has_written_yet" in blob)
    check("...and-lands-as-words", "some of this" in blob or "a good deal of this" in blob,
          "an unknown scalar must get a banded generic, not vanish")
    check("authored-prose-is-untouched", "internal" in blob,
          "the renderer bands NUMBERS; an author's words are theirs")
    print("       every unhandled field survived, in words, with no digit")

    # ...but a number that is not a WEIGHT still refuses. Guessing at it would be the silent-drop
    # failure in a new place.
    char["baseline"]["model"]["some_count"] = 12.5
    packet = assemble(char, world,
                      {"event": {"text": "A door bangs.", "kind": "mundane"},
                       "recent": [], "location": "yard"},
                      dict(char["current"]["affect"]), char["current"]["condition"])
    try:
        direct_identity(packet["stable"])
        check("out-of-range-still-refuses", False, "12.5 was banded as if it were a weight")
    except ValueError as exc:
        print("       %s" % str(exc)[:130])
        check("out-of-range-still-refuses", True)
        check("and-names-the-path", "some_count" in str(exc), str(exc)[:100])


def main():
    print("test_no_digits.py — THE LAW: no number describing a character reaches them")
    for t in (test_the_law, test_the_information_survives, test_the_surfaces_are_pure,
              test_no_new_leak_creeps_back):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
