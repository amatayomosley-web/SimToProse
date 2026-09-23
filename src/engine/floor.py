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

from .records import PATHS
from .state import appraise
from . import bonds
from . import bond_rest                                    # whole: an undeclared edge is born at the stranger's rest
from . import connection                                   # gate 5: held_map per witness
from .scene import norm_id

# THE FLOOR CONSTANTS. Tuned against the probe; `scripts/scene.py` still reads ADDRESSED_BONUS to
# explain a chosen speaker in its own output, which is why it is re-exported rather than hidden.
# FLOOR_THRESHOLD LIVES HERE TOO, and did not in the first draft: it stayed in the driver while the
# other three moved, so the number `urge` is COMPARED AGAINST sat in a different file from the
# function producing the value. Splitting a threshold from its metric is how the two drift.
FLOOR_THRESHOLD = 0.06   # below this max urge, no one is moved enough to answer -> the scene lulls
ADDRESSED_BONUS = 0.15   # being spoken to / about pulls you to reply
RECENCY_PENALTY = 0.20   # you just spoke -> step back (decays over ~3 beats); breaks two-person monopoly IN A CROWD — not applied in a two-hander (urge: `contested`)
INHIBITION      = 0.10   # timid (low-extraversion) actors hold back


def salience(tags, target, tgroup, listener):
    applied = dict(tags)
    if target:
        applied["target"] = target
    if tgroup:
        applied["target_group"] = tgroup
    appraised = appraise(listener["affect"], applied, listener["profile"])
    return sum(abs(appraised[p] - listener["affect"][p]) for p in PATHS)


def bond_moves(actors, present, speaker, applied):
    """Every OTHER person in the room re-reads the speaker
    -> [(witness_id, deltas, their_view_deltas, cliffed_axes)].

    The loop the engine did not have: `arc.assess` runs on the SPEAKER but an edge is the
    PERCEIVER's belief (`bonds.py` docstring has the measurement). READS the edges and returns the
    moves without applying them, so the caller can commit them before touching a character sheet.
    STAKE and RATES are read off the WITNESS's own sheet here (bond-arithmetic.md s5/s6, gate 4),
    because this is the one place that holds it whole: how much she holds the act's object, and how
    readily she lets someone in or lets them go. A cliffed axis comes back so the driver can write
    the rest row that rides the turn (bond_rest.cliff_rows).
    """
    moves = []
    # BELT AND BRACES, and labelled as such: `bonds.act_from_tags` already returns None when actor
    # and witness are the same person, so removing this filter changes no behaviour (breakage-
    # tested 2026-09-03). It stays because the loop reads correctly with it and a reader should not
    # have to open `bonds.py` to learn that the speaker is excluded.
    for wid in [i for i in present if i != speaker]:
        ch = actors[wid]["char"]
        # GATE 5: what she holds that is not a person — attachments beside wounds, goals and values,
        # one map (connection.held_map; the same function state.build_profile calls for the emotion
        # tier). An act on her held place is done TO her (received) at her hold (stake), and the
        # second order reads the same hold.
        held = connection.held_map(ch)
        act = bonds.act_from_tags(applied, speaker, wid, held=held)
        if not act:
            continue
        rels = ch["current"].get("relationships") or {}
        stored = rels.get(speaker, {})
        # presence is not perception: a subtle act needs noticing, and pinning one on a STRANGER
        # needs recognising them (bonds.witnessed, on gate.py's own DCs); an act done TO her is overt.
        # Recognition reads the STORED edge — an edge she does not yet hold is a stranger, whatever
        # `whole` fills in below for the law.
        if not bonds.witnessed(act, ch["baseline"].get("skills", {}), stored):
            continue
        model = ch["baseline"].get("model", {})
        priors = ch["baseline"].get("relationship_priors", {})
        # THE LAW READS THE EDGE WHOLE (bond_rest.whole, 2026-09-19): an undeclared edge is born
        # where a stranger rests — `default_trust` on trust — so the first act a stranger does is
        # priced from the sheet's assumption about strangers, not from the neutral .50. The driver
        # applies the deltas to the same whole edge (scripts/scene.py), and the fold births it the
        # same way (bond_rest.rehydrate), so live and replay agree.
        edge = bond_rest.whole(stored, priors)
        stake = bonds.stake_of(wid, act["object"], rels, held=held)
        rates = bonds.rates_of(priors)
        deltas = bonds.observe(edge, act, model, stake=stake, rates=rates)
        # ...and if the act was aimed AT them, it also revises what they think the speaker makes of
        # THEM (relationships.md's second order). Same evidence, a different belief — at the same
        # stake: 1.0 when the object is the witness, her hold when it is her thing (gate 5).
        view = bonds.reflect(edge, act, model, rates=rates, stake=stake)
        cliffs = bonds.cliff_axes(edge, act, model) if deltas else ()
        if deltas or view:
            moves.append((wid, deltas, view, cliffs))
    return moves


def order_weight(profile):
    """The listener's stake in ORDER/standing — the mean of the standing-cluster values. High for a
    decorum-keeper: a heated exchange in their presence is, to them, a violation worth intervening on."""
    s = profile.get("model", {}).get("schwartz", {})
    return sum(float(s.get(k, 0.5)) for k in ("conformity", "security", "power")) / 3.0


def urge(tags, target, tgroup, listener, addressed, beats_since, contested=True, landed=None):
    """How urgently this listener wants the floor. Returns (urge, salience, disruption) for display.

    `contested`: is there anyone ELSE who could take the floor? The recency penalty exists to break
    a two-person monopoly in a crowded room; in a room of two there is no monopoly to break and the
    only alternative to the other person answering is silence. Measured 2026-09-12 on a generated
    two-hander: after a short, direct demand typed `mundane` by the event seat,
    the listener's urge was 0.055 against a floor of 0.060 — addressed +0.15, recency -0.133 (spoke
    one beat ago, as the other person in a two-hander always has), inhibition -0.05 — and the scene
    ended by lull. With `contested=False` the penalty is 0.

    `landed` (gate lands-on-to-floor, 2026-09-19): whether the emotion seat's `lands_on` named this
    listener as someone the beat reached (docs/emotion-arithmetic.md section 5 step 5). `False`
    PRUNES the salience term to 0.0 — both in the returned urge and in the salience returned for
    display, so a listener the seat did not list is not pulled to the floor by a counterfactual
    appraise the seat never endorsed, and the trace shows why. `True` or `None` computes salience
    exactly as today. `None` is not "the seat said no one" — it is NO SEAT (--stub, or a refusal):
    the counterfactual appraise is the only judgment available, so today's behaviour is kept whole
    rather than guessed at from an absence.

    THE FLAT LANDS_ON_BONUS FORM IS DELIBERATELY NOT BUILT. The doc's literal §5 step 5 spec reads
    `urge += LANDS_ON_BONUS·[listener in lands_on]` — a bonus added to whoever the seat lists, not a
    prune of whoever it leaves out. Measured 2026-09-19 (scratchpad/replay_lands_on.py) over the 31
    recorded beats that carry a seat reply: the seat listed EVERY present listener on all 34 of 34
    listener-beats — it never once left someone out — so on this corpus a flat bonus is a constant
    added to every listener in the room, which is arithmetically a lowering of FLOOR_THRESHOLD by
    the bonus and would retire the lull by the back door of a seam that looks unrelated to it —
    exactly the owner's open drive-term question (D5), not this gate's to decide. Pruning is the
    conservative reading: identical to today wherever the seat lists everyone (0 of 30 decided
    beats changed on the corpus), and it still puts the seat's judgment to use exactly where the two
    forms could ever disagree — a listener the seat left out.
    """
    sal = 0.0 if landed is False else salience(tags, target, tgroup, listener)
    addr = ADDRESSED_BONUS if addressed else 0.0
    disruption = float((tags.get("dimensions") or {}).get("social_violation", 0.0)) * order_weight(listener["profile"])
    recency = RECENCY_PENALTY * max(0.0, 1.0 - beats_since / 3.0) if contested else 0.0
    inhibition = INHIBITION * (1.0 - listener["extraversion"])
    return sal + addr + disruption - recency - inhibition, sal, disruption


def leader(urges):
    """The highest urge, tie-broken STABLY. One spelling, so the driver's lull message names the
    same actor this function would have chosen — two orderings would disagree exactly when it
    mattered, on a tie."""
    return sorted(urges, key=lambda k: (-urges[k][0], str(k)))[0]


def next_speaker(actors, present, speaker, applied, target, tgroup, addressee, beat, lands_on=None):
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

    `lands_on` (gate lands-on-to-floor, 2026-09-19): the emotion seat's list for THIS beat, or
    `None` when there is no seat (--stub, or a refusal) — propagated to `urge`'s `landed` per
    listener, unchanged otherwise. `None` skips pruning entirely (every listener's `landed` is
    `None`, `urge` computes salience exactly as today); otherwise a listener's `landed` is whether
    their `norm_id` is in `{norm_id(x) for x in lands_on}` — the same normalisation `addressed`
    already applies two lines below, since the seat writes ids in whatever spelling it was shown,
    same as the addressee.
    """
    others = [i for i in present if i != speaker]
    if not others:
        return None, {}, "empty"
    landed_ids = None if lands_on is None else {norm_id(x) for x in lands_on}
    urges = {}
    for o in others:
        # `startswith` on a bare id could never match what the actor is actually shown — the
        # capitalised display name, or the `entity.<id>` percept ref. norm_id accepts every
        # spelling the prompt displays.
        addressed = bool(addressee) and norm_id(addressee) == norm_id(o)
        landed = None if landed_ids is None else (norm_id(o) in landed_ids)
        urges[o] = urge(applied, target, tgroup, actors[o], addressed,
                        beat - actors[o]["last_spoke"], contested=len(others) > 1, landed=landed)
    nxt = leader(urges)
    if urges[nxt][0] < FLOOR_THRESHOLD:
        return None, urges, "lull"
    return nxt, urges, None
