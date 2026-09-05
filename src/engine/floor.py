"""floor.py — who wants the floor next.

THE TURN-TAKING ECONOMY, MOVED OUT OF THE DRIVER. `compose_event` came here in the same move and
went straight back out: it was the only one of the five returning TEXT rather than a number or a
set of moves, because it decides WHAT THE SPEAKER PERCEIVES while the rest decide WHO SPEAKS NEXT.
That is scene assembly, and `scene.py:assemble` already owns it. The first draft of this very
docstring gave the seam away — "who wants the floor next, AND what they perceive when they get it"
— and a module whose name promises one thing while holding two is a lie the next reader pays for. These five functions computed VALUES —
a salience, a weight, an urge, a set of relationship moves, the text a listener perceives — inside
`scripts/scene.py`, and CLAUDE.md's Modes section says the thing a driver never does is compute a
value. The engine computes; the driver dispatches. That is the same split hard rule 5 draws for
numbers reaching a prompt, one layer out.

WHY IT MATTERED PRACTICALLY, not just architecturally: `tests/run_all.py` discovers suites under
`tests/`, and nothing under `tests/` could import these — the only coverage any of them had was
`tests/test_bonds.py` reaching into `scripts/scene.py` through `spec_from_file_location`, which is
a test loading a 1052-line CLI script to exercise a nine-line function. Here they are importable,
and `tests/test_floor.py` exercises them directly.

THE PUBLIC NAMES LOST THEIR UNDERSCORES. They were private to a script; they are now this module's
interface. `scripts/scene.py` re-exports them under the OLD private names, because nine tests load
that file by path and one calls `sc._bond_moves` — the same move `ledger.py` makes for the fold.

Deterministic, stdlib only, no LLM, no randomness. Fails loud through the modules it calls.
"""
from __future__ import annotations

__layer__ = "engine"

from .records import PRIMARIES
from .state import appraise
from . import bonds
from .scene import norm_id

# THE FLOOR CONSTANTS. Tuned against the probe; `scripts/scene.py` still reads ADDRESSED_BONUS to
# explain a chosen speaker in its own output, which is why it is re-exported rather than hidden.
# FLOOR_THRESHOLD LIVES HERE TOO, and did not in the first draft: it stayed in the driver while the
# other three moved, so the number `urge` is COMPARED AGAINST sat in a different file from the
# function producing the value. Splitting a threshold from its metric is how the two drift.
FLOOR_THRESHOLD = 0.06   # below this max urge, no one is moved enough to answer -> the scene lulls
ADDRESSED_BONUS = 0.15   # being spoken to / about pulls you to reply
RECENCY_PENALTY = 0.20   # you just spoke -> step back (decays over ~3 beats); breaks two-person monopoly
INHIBITION      = 0.10   # timid (low-extraversion) actors hold back


def salience(tags, target, tgroup, listener):
    applied = dict(tags)
    if target:
        applied["target"] = target
    if tgroup:
        applied["target_group"] = tgroup
    appraised = appraise(listener["affect"], applied, listener["profile"])
    return sum(abs(appraised[p] - listener["affect"][p]) for p in PRIMARIES)


def bond_moves(actors, present, speaker, applied):
    """Every OTHER person in the room re-reads the speaker -> [(witness_id, deltas, their_view_deltas)].

    The loop the engine did not have: `arc.assess` runs on the SPEAKER but an edge is the
    PERCEIVER's belief (`bonds.py` docstring has the measurement). READS the edges and returns the
    moves without applying them, so the caller can commit them before touching a character sheet.
    """
    moves = []
    # BELT AND BRACES, and labelled as such: `bonds.act_from_tags` already returns None when actor
    # and witness are the same person, so removing this filter changes no behaviour (breakage-
    # tested 2026-09-03). It stays because the loop reads correctly with it and a reader should not
    # have to open `bonds.py` to learn that the speaker is excluded.
    for wid in [i for i in present if i != speaker]:
        w = actors[wid]
        act = bonds.act_from_tags(applied, speaker, wid)
        if not act:
            continue
        edge = (w["char"]["current"].get("relationships") or {}).get(speaker, {})
        # presence is not perception: a subtle act needs noticing, and pinning one on a STRANGER
        # needs recognising them (bonds.witnessed, on gate.py's own DCs)
        if not bonds.witnessed(act, w["char"]["baseline"].get("skills", {}), edge):
            continue
        model = w["char"]["baseline"].get("model", {})
        deltas = bonds.observe(edge, act, model)
        # ...and if the act was aimed AT them, it also revises what they think the speaker makes of
        # THEM (relationships.md's second order). Same evidence, a different belief.
        view = bonds.reflect(edge, act, model)
        if deltas or view:
            moves.append((wid, deltas, view))
    return moves


def order_weight(profile):
    """The listener's stake in ORDER/standing — the mean of the standing-cluster values. High for a
    decorum-keeper: a heated exchange at the table is, to them, a violation worth intervening on."""
    s = profile.get("model", {}).get("schwartz", {})
    return sum(float(s.get(k, 0.5)) for k in ("conformity", "security", "power")) / 3.0


def urge(tags, target, tgroup, listener, addressed, beats_since):
    """How urgently this listener wants the floor. Returns (urge, salience, disruption) for display."""
    sal = salience(tags, target, tgroup, listener)
    addr = ADDRESSED_BONUS if addressed else 0.0
    disruption = float((tags.get("dimensions") or {}).get("social_violation", 0.0)) * order_weight(listener["profile"])
    recency = RECENCY_PENALTY * max(0.0, 1.0 - beats_since / 3.0)
    inhibition = INHIBITION * (1.0 - listener["extraversion"])
    return sal + addr + disruption - recency - inhibition, sal, disruption


def leader(urges):
    """The highest urge, tie-broken STABLY. One spelling, so the driver's lull message names the
    same actor this function would have chosen — two orderings would disagree exactly when it
    mattered, on a tie."""
    return sorted(urges, key=lambda k: (-urges[k][0], str(k)))[0]


def next_speaker(actors, present, speaker, applied, target, tgroup, addressee, beat):
    """Who takes the floor after this beat -> (chosen_id, urges, reason).

    `reason` is None when someone takes it, "empty" when nobody else is present, and "lull" when
    the field is present but nobody cleared FLOOR_THRESHOLD. Three outcomes rather than a bare
    Optional, because the caller reports them differently and a None that means two things is the
    kind of ambiguity a driver resolves by re-deriving what this function already knew.

    THE DECISION LIVED IN THE DRIVER while every input to it lived here. `scripts/scene.py`'s beat
    loop built the urges map, took the maximum and compared it to the threshold, with three print
    statements interleaved through the decision — so the module named for the turn-taking economy
    held the economy and not the choice, and the choice could not be tested without running a scene.
    The prints stay in the driver: this decides, the driver reports.

    THE TIE-BREAK IS EXPLICIT, and it was not before. `max(urges, key=...)` returns the FIRST
    maximum in dict-insertion order, which followed `present`, so two actors with an identical urge
    resolved by cast order and nothing said so. Hard rule 4 makes determinism a contract, and a
    contract kept by dict ordering is one refactor from being false — sorting on (-urge, id) makes
    the winner a property of the values rather than of how they were inserted. Named here because
    the same defect, undocumented tie-breaking in a priority walk, is live in `associative.py`.
    """
    others = [i for i in present if i != speaker]
    if not others:
        return None, {}, "empty"
    urges = {}
    for o in others:
        # `startswith` on a bare id could never match what the actor is actually shown — the
        # capitalised display name, or the `entity.<id>` percept ref. norm_id accepts every
        # spelling the prompt displays.
        addressed = bool(addressee) and norm_id(addressee) == norm_id(o)
        urges[o] = urge(applied, target, tgroup, actors[o], addressed,
                        beat - actors[o]["last_spoke"])
    nxt = leader(urges)
    if urges[nxt][0] < FLOOR_THRESHOLD:
        return None, urges, "lull"
    return nxt, urges, None
