"""The recall pass must actually decay — through assemble(), not through decay's own unit tests.

Why this suite exists. On 2026-09-04 `src/engine/scene.py` called
`run_gate(triggers, vault, skills, goals, condition)` — five of nine parameters. Every hop
BELOW that call threaded `current_turn` correctly (gate -> find_associative_candidates ->
build_vault_graph -> calculate_effective_confidence), and `tests/test_memory_decay.py`
proved the formula. All 74 suites were green. Decay was still inert in every real run,
because nothing asserted the one argument list that joins the two halves.

That is the seam this file guards: "the function works" and "the engine uses it" are two
claims, and a unit test only ever makes the first.

The observable effect is stronger than a smaller number. A belief last recalled 40 turns
ago decays until its cost exceeds the energy budget, so it leaves the packet altogether —
the character stops bringing it up. Asserting on PRESENCE is also what makes this test
honest about where the bid lives: recall entries carry ref/claim/confidence/provenance,
and the belief id is in `packet["recall_ids"]`. An earlier draft looked for the bid inside
the recall entry, found nothing, and reported "never recalled" while the engine was
working correctly.

    python tests/test_recall_decay_is_wired.py
"""
import copy
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.scene import assemble          # noqa: E402
from src.engine.gate import belief_id          # noqa: E402

FAILS = []
STALE_TURN = 40


def _check(name, cond, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, "" if cond else "  -- " + detail))
    if not cond:
        FAILS.append(name)


def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _flat_affect(v=0.5):
    return {k: v for k in ("SEEKING", "FEAR", "RAGE", "LUST", "CARE",
                           "PANIC_GRIEF", "PLAY", "DISGUST")}


def _decaying_char():
    """A character whose vault holds exactly one OLD, non-core belief the scene triggers.

    Two traps, both hit while writing this:
      - `durability`/`provenance` must not be "core" — decay.py returns base confidence
        unchanged for those, so the test would pass while measuring nothing.
      - triggers come from PERCEPT ATTRIBUTES, not the event prose. `extract_triggers`
        on this slice yields ['night'], so a belief keyed on words from the event text
        never enters recall at all.
    """
    ch = copy.deepcopy(_load("characters/maren-healer.json"))
    belief = {
        "claim": "the night air carries fever",
        "believed_value": "a fact about night",
        "provenance": "lived",
        "durability": "transient",
        "confidence": 0.9,
        "created_turn": 0,
        "last_recalled_turn": 0,
        "recall_count": 1,
        "links": ["night"],
        "about": ["night"],
    }
    belief["bid"] = belief_id(belief)
    ch["current"]["vault"] = [belief]
    return ch, belief["bid"]


def _packet(ch, world, turn):
    ss = {"event": {"text": "Rain has been falling on the mill road all morning.",
                    "kind": "mundane"},
          "recent": [], "location": None}
    return assemble(ch, world, ss, _flat_affect(), ch["current"]["condition"],
                    current_turn=turn)


def main():
    world = _load("world/ashford-slice.json")
    ch, bid = _decaying_char()

    fresh = _packet(ch, world, 0)
    stale = _packet(ch, world, STALE_TURN)
    in_fresh = bid in (fresh.get("recall_ids") or [])
    in_stale = bid in (stale.get("recall_ids") or [])

    print("[1] the belief is recalled when it is fresh — or the rest proves nothing")
    _check("fresh-belief-is-recalled", in_fresh,
           "the fixture never entered recall at turn 0; triggers were %r"
           % (fresh.get("volatile", {}).get("percepts"),))

    print("[2] THE SEAM — the same belief must NOT survive %d turns of decay" % STALE_TURN)
    _check("stale-belief-leaves-the-packet", in_fresh and not in_stale,
           "recalled at turn 0: %s, at turn %d: %s. Identical means assemble() is not "
           "passing current_turn to run_gate — the 2026-09-04 defect returning, where "
           "decay was built, tested, threaded end to end, and inert in production."
           % (in_fresh, STALE_TURN, in_stale))

    print("[3] CONTROL — the difference must come from the TURN, not the fixture")
    same_turn_twice = (bid in (_packet(ch, world, 0).get("recall_ids") or []))
    _check("turn-0-is-stable-across-calls", same_turn_twice == in_fresh,
           "two identical calls disagreed, so the comparison in [2] is not measuring the turn")

    print("\nVERDICT: %s%s" % ("FAIL -> " if FAILS else "PASS", FAILS or ""))
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
