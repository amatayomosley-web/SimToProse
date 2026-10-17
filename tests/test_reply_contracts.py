"""test_reply_contracts.py — the speaker and listener reply contracts (conversation design v2 section 7B).

A move is one point, one paragraph, or one act. After it, each asked listener chooses what to do with
the floor (take, interject, hold) and a speaker nobody interrupted chooses whether to go on (keep,
yield). The record has held the floor word since gate floor-in-record; this suite proves the actor is
ASKED for it, in the stance it is in, and that a prompt built with no stance is the prompt as it was.

Read from the render, never from the format tuple, for the reason tests/test_prompt_sections.py gives.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.prompt import build_turn_messages            # noqa: E402
from src.engine.records import PATHS, RecordError            # noqa: E402

_EVENT = "The ferryman sets the rope on the table."


def _packet():
    return {"stable": {"persona": {"id": "a", "name": "A"}},
            "volatile": {"state": {"affect": {p: 0.3 for p in PATHS},
                                   "condition": {"energy": 0.5, "allostatic_load": 0.2}},
                         "goals": [], "percepts": [], "recall": [], "edges": []}}


def _usr(**kw):
    temperament = {p: {"mean": 0.3, "variability": 0.1} for p in PATHS}
    return build_turn_messages(_packet(), _EVENT, temperament, **kw)[1]["content"]


def _skeleton(u):
    return u[u.index("Reply as ONE JSON object"):u.index("action = what you do or say")]


_MEMORY = "What is under your own name you have already said. Do not say it again: press it, drop it, or change tack."


def test_speaker_contract_asks_keep_or_yield():
    u = _usr(stance="speaker")
    assert '"floor": "keep"' in _skeleton(u), _skeleton(u)
    assert "one point, one paragraph, or one act" in u
    assert "then stop where they would answer" in u
    assert "keep if you have more" in u and "yield if that was the last of it" in u
    assert _MEMORY in u
    assert "Take the floor" not in u, "a speaker is not given the listener's choices"


def test_listener_contract_asks_take_interject_or_hold():
    u = _usr(stance="listener")
    assert '"floor": "hold"' in _skeleton(u), _skeleton(u)
    assert "You have just heard the last line." in u
    assert "Take the floor, put in a word and let them go on, hold your tongue, or do something" in u
    assert "hold with nothing to say and nothing to do is allowed and means it" in u
    assert _MEMORY in u
    assert "yield if that was the last of it" not in u, "a listener is not given the speaker's choices"


def test_placed_and_licensed_lines_render_only_when_asked():
    plain_s, plain_l = _usr(stance="speaker"), _usr(stance="listener")
    room = "The room is yours; no one will answer until you finish."
    cut = "You are moved enough to cut in before they finish."
    forced = "the floor is yours; answer, act, or let the silence stand."
    unanswered = "You stopped and no one has answered you: the floor is yours again; go on, act, or let the silence stand."
    resumed = "Go on from where you stopped; do not restate."
    assert room in _usr(stance="speaker", hold_open=True) and room not in plain_s
    assert resumed in _usr(stance="speaker", resumed=True) and resumed not in plain_s
    assert cut in _usr(stance="listener", interrupt=True) and cut not in plain_l
    assert forced in _usr(stance="listener", forced=True) and forced not in plain_l
    assert "or leave" not in _usr(stance="listener", forced=True), "the forced line does not invite the exit (critique E5)"
    assert unanswered in _usr(stance="listener", unanswered=True) and unanswered not in plain_l


def test_no_stance_is_the_prompt_as_it_was():
    """No caller passes a stance until the round loop (gate C); every one of them gets today's prompt."""
    u = _usr()
    assert u == _usr(stance=None)
    assert '"floor"' not in _skeleton(u)
    assert "What you were thinking last" not in u
    assert _MEMORY not in u


def test_a_bad_stance_refuses_by_code():
    for kw, code in (({"stance": "chorus"}, "PROMPT_STANCE_UNKNOWN"),
                     ({"stance": "listener", "hold_open": True}, "PROMPT_STANCE_FLAG"),
                     ({"stance": "listener", "resumed": True}, "PROMPT_STANCE_FLAG"),
                     ({"stance": "speaker", "interrupt": True}, "PROMPT_STANCE_FLAG"),
                     ({"stance": "speaker", "forced": True}, "PROMPT_STANCE_FLAG"),
                     ({"hold_open": True}, "PROMPT_STANCE_FLAG"),
                     ({"last_thought": "x"}, "PROMPT_STANCE_FLAG")):
        try:
            _usr(**kw)
        except RecordError as e:
            assert e.code == code, (kw, e.code)
        else:
            raise AssertionError("%r built a prompt; it must refuse %s" % (kw, code))


def test_a_directed_move_is_told_whom_it_is_to():
    """gate directed-addressee: the scene direction may name whom a character's move is aimed at; the prompt says so
    and asks for that id, in any stance or none; without it, nothing is added; a malformed one refuses by code."""
    line = 'This move is directed: you are speaking to Tomas. Set addressee to "tomas"'
    for kw in ({}, {"stance": "speaker"}, {"stance": "listener"}):
        assert line in _usr(to=("tomas", "Tomas"), **kw), kw
        assert "This move is directed" not in _usr(**kw), kw
    for bad in ("tomas", ("tomas",), ("", "Tomas"), ("tomas", "")):
        try:
            _usr(to=bad)
        except RecordError as e:
            assert e.code == "PROMPT_DIRECTED_TO_MALFORMED", (bad, e.code)
        else:
            raise AssertionError("to=%r built a prompt; it must refuse" % (bad,))


def test_a_sheets_tics_are_habits_not_every_move():
    """gate tic-rate (a replay: a sheet's two tics shown in most moves): the voice's tics reach the actor on
    every call as identity; under the round loop the actor is told they show now and then - at most one a move, never
    the one shown last. A sheet without tics, and the stance-free prompt, are as they were."""
    line = "Your tics are habits: they show now and then, not in every move"
    p = _packet()
    p["stable"]["voice"] = {"tics": ["hums under his breath", "folds his arms"]}
    temperament = {k: {"mean": 0.3, "variability": 0.1} for k in PATHS}
    for stance in ("speaker", "listener"):
        assert line in build_turn_messages(p, _EVENT, temperament, stance=stance)[1]["content"], stance
        assert line not in _usr(stance=stance), stance
    assert line not in build_turn_messages(p, _EVENT, temperament)[1]["content"], "stance-free prompt unchanged"
    p["stable"]["voice"] = {"tics": []}
    assert line not in build_turn_messages(p, _EVENT, temperament, stance="speaker")[1]["content"], "no tics, no line"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("  PASS  %s" % name)
    print("reply contracts: all checks passed")
