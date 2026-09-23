"""test_prompt_sections.py — every labelled section of the actor prompt holds ITS OWN content.

The gap this closes. `build_turn_messages` assembles the user message from a template with ten
`%s` placeholders and a ten-item argument tuple. Nothing asserted that the two agreed, and on
2026-08-29 they did not: `_act_slot` and `_act_rule` sat at argument positions 2 and 3 but at
template positions 8 and 9, shifting six sections by two. Every prompt this engine had ever built
told the actor its goals were empty, filed its percepts under "Those present", put the recall
string under "The moment:", rendered the relationship edges inside the reply skeleton's
`"dimensions": {...}`, and buried the actual event text after `"social": {}}`.

Why the existing suites could not catch it. `test_no_digits.py` scans the rendered prompt for
digits — a structural scramble carries none. Everything else tests the packet, not the render. A
guard reports on what it READS, and nothing read the layout.

So this suite reads the layout: for each label, the text that FOLLOWS it must be the argument that
label names. It is deliberately written against the rendered string rather than the format tuple,
because asserting the tuple order against itself would restate the bug rather than detect it.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.prompt import build_turn_messages, _DIMS   # noqa: E402
from src.engine.records import PATHS                                 # noqa: E402

_MARK_EVENT = "ZZ_EVENT_MARKER_ZZ"
_MARK_GOAL = "ZZ_GOAL_MARKER_ZZ"
_MARK_PERCEPT = "ZZ_PERCEPT_MARKER_ZZ"
_MARK_CLAIM = "ZZ_RECALL_MARKER_ZZ"
_MARK_EDGE = "ZZ_EDGE_MARKER_ZZ"
_MARK_HOLDS = "ZZ_HOLDS_MARKER_ZZ"
_MARK_FACTS = "ZZ_FACTS_MARKER_ZZ"


def _packet():
    """A packet whose every volatile slot carries a DISTINCT marker, so a section holding the
    wrong argument is identifiable by which marker turned up in it."""
    return {
        "stable": {"persona": {"id": "a", "name": "A"}},
        "volatile": {
            "state": {"affect": {p: 0.3 for p in PATHS},
                      "condition": {"energy": 0.5, "allostatic_load": 0.2}},
            "goals": [{"goal": _MARK_GOAL, "urgency": 0.5}],
            "percepts": [{"ref": "p.1", "channel": "visual",
                          "attributes": [_MARK_PERCEPT], "fidelity": 0.9}],
            "recall": [{"claim": _MARK_CLAIM, "confidence": 0.8, "provenance": "seen"}],
            "edges": [{"label": _MARK_EDGE, "target": "b", "trust": 0.5,
                       "affinity": 0.5, "respect": 0.5, "debt": 0.5}],
            "holds": [{"entity": "loc.x", "name": _MARK_HOLDS, "word": "life"}],
            # 2026-09-22: the fixture carried no facts, so the section rendered its empty
            # phrase and no check ever looked at what it holds.
            "facts": [{"kind": "passed", "turn": 1, "speaker": "b", "what": _MARK_FACTS,
                       "from": "b", "to": "a", "terms": "loan"}],
        },
    }


def _usr(acts=()):
    temperament = {p: {"mean": 0.3, "variability": 0.1} for p in PATHS}
    return build_turn_messages(_packet(), _MARK_EVENT, temperament, acts=acts)[1]["content"]


_LABELS = ("Active goals:", "What you perceive THIS moment", "What it brings to mind:",
           "What is established about who and what is here",
           "What is yours here:",
           # 2026-09-22, gate scene-facts-to-actor. A new section MUST be registered here or
           # `_after`'s window spills across it and reads the next section's content as this one's,
           # which is the exact confusion this suite exists to detect.
           "What has happened here, as you saw it",
           "Those present, as you stand with them:", "The moment:", "Reply as ONE JSON object")


def _after(text, label, n=400):
    """The window of text following a label, BOUNDED BY THE NEXT LABEL.

    A fixed-width window would spill into the following section and read its content as this
    one's — which is precisely the confusion this suite exists to detect, so the window has to
    respect the same boundaries the actor reads by.
    """
    i = text.index(label) + len(label)
    end = i + n
    for other in _LABELS:
        j = text.find(other, i)
        if j != -1:
            end = min(end, j)
    return text[i:end]


def _check(text, label, must_hold, must_not_hold):
    seg = _after(text, label)
    assert must_hold in seg, (
        "section %r does not hold its own content (%r missing). Got: %r"
        % (label, must_hold, seg[:200]))
    for wrong in must_not_hold:
        assert wrong not in seg, (
            "section %r holds ANOTHER section's argument (%r). Got: %r"
            % (label, wrong, seg[:200]))


def test_each_section_holds_its_own_argument():
    """The whole point: label and content agree, with no acts injected (the default path)."""
    u = _usr()
    _check(u, "Active goals:", _MARK_GOAL, [_MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE, _MARK_HOLDS, _MARK_EVENT])
    _check(u, "What you perceive THIS moment", _MARK_PERCEPT, [_MARK_GOAL, _MARK_CLAIM, _MARK_EDGE, _MARK_HOLDS])
    _check(u, "What it brings to mind:", _MARK_CLAIM, [_MARK_GOAL, _MARK_PERCEPT, _MARK_EDGE, _MARK_HOLDS])
    _check(u, "What is yours here:", _MARK_HOLDS, [_MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE])
    _check(u, "What has happened here, as you saw it", _MARK_FACTS,
           [_MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE, _MARK_HOLDS, _MARK_EVENT])
    _check(u, "Those present, as you stand with them:", _MARK_EDGE,
           [_MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM, _MARK_HOLDS, _MARK_FACTS])
    _check(u, "The moment:", _MARK_EVENT, [_MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE, _MARK_HOLDS])


def test_sections_hold_when_acts_are_injected():
    """The act slot and rule are conditional; injecting them must not shift anything else."""
    u = _usr(acts=("move", "rest"))
    _check(u, "Active goals:", _MARK_GOAL, [_MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE, _MARK_HOLDS, _MARK_EVENT])
    _check(u, "What you perceive THIS moment", _MARK_PERCEPT, [_MARK_GOAL, _MARK_CLAIM, _MARK_EDGE, _MARK_HOLDS])
    _check(u, "What is yours here:", _MARK_HOLDS, [_MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE])
    _check(u, "The moment:", _MARK_EVENT, [_MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE, _MARK_HOLDS])
    assert 'act = the ONE token from this list' in u
    assert '"act": ""' in u, "the act SLOT belongs in the reply skeleton when acts are declared"


def test_holds_section_renders_the_empty_phrase_when_there_are_none():
    """No holds in scope renders the fixed phrase rather than an omitted section -- the label
    count must stay constant whether or not this character holds anything (gate
    attachments-to-actor's MIGRATION note)."""
    temperament = {p: {"mean": 0.3, "variability": 0.1} for p in PATHS}

    packet_empty = _packet()
    packet_empty["volatile"]["holds"] = []
    u_empty = build_turn_messages(packet_empty, _MARK_EVENT, temperament)[1]["content"]
    _check(u_empty, "What is yours here:", "nothing here is yours",
           [_MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE])

    packet_absent = _packet()
    del packet_absent["volatile"]["holds"]
    u_absent = build_turn_messages(packet_absent, _MARK_EVENT, temperament)[1]["content"]
    _check(u_absent, "What is yours here:", "nothing here is yours",
           [_MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM, _MARK_EDGE])


def test_facts_section_renders_the_fact_and_the_empty_phrase():
    """The fact reaches the section in the register the reader is addressed in, and an empty ledger
    renders the fixed phrase rather than an omitted section (the label count stays constant)."""
    u = _usr()
    seg = _after(u, "What has happened here, as you saw it", n=700)
    assert "What changed hands: B lent %s to you." % _MARK_FACTS in seg, seg
    temperament = {p: {"mean": 0.3, "variability": 0.1} for p in PATHS}
    packet_empty = _packet()
    packet_empty["volatile"]["facts"] = []
    u_empty = build_turn_messages(packet_empty, _MARK_EVENT, temperament)[1]["content"]
    _check(u_empty, "What has happened here, as you saw it",
           "nothing has happened here yet that you saw", [_MARK_FACTS, _MARK_EDGE, _MARK_HOLDS])


def test_reply_skeleton_dimensions_are_the_dimension_names():
    """`"dimensions": {...}` defines the scale the actor writes ON. It held the EDGES string."""
    seg = _after(_usr(), '"dimensions": {', 260)
    for dim in _DIMS:
        assert '"%s": "<severity>"' % dim in seg, (
            "dimension %r missing from the reply skeleton; got: %r" % (dim, seg[:200]))
    for dim in _DIMS:
        assert '"%s": 0..1' % dim not in seg, (
            "dimension %r still offers a bare float — severity is an engine-owned vocabulary "
            "now (src/engine/severity.py), not a number the actor invents" % dim)
    for wrong in (_MARK_EDGE, _MARK_GOAL, _MARK_PERCEPT, _MARK_CLAIM):
        assert wrong not in seg, "reply skeleton dimensions hold %r" % wrong


def test_event_text_is_not_inside_the_reply_skeleton():
    """The regression's loudest symptom: the event landed after `"social": {}}`."""
    u = _usr()
    assert u.index(_MARK_EVENT) < u.index("Reply as ONE JSON object"), (
        "the event text falls INSIDE the reply skeleton — the actor is asked to respond to a "
        "moment that appears as part of its own output format")


def test_reply_skeleton_retired_the_social_key():
    """gate actor-contract-cleanup (2026-09-19): the social block was retired by
    bond-arithmetic.md s2 (APPRAISER_SOCIAL_RETIRED, 2026-09-17) and nothing live ever read
    tags.social off the actor's own contract — three vocabularies for one tier, two of
    them dead. attribution is the seat's one still-live self-report tag, and stays (gate 9
    gives the event seat the live one; this is the stub double's own)."""
    u = _usr()
    skeleton = u[u.index("Reply as ONE JSON object"):u.index("action = what you do or say")]
    assert '"attribution"' in skeleton, (
        "reply skeleton lost \"attribution\" — the stub double's own tag; got: %r" % skeleton[:300])
    assert '"social"' not in skeleton, (
        "reply skeleton still offers \"social\" — retired 2026-09-17, removed 2026-09-19, "
        "nothing reads it; got: %r" % skeleton[:300])


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("  PASS  %s" % name)
    print("prompt sections: all checks passed")
