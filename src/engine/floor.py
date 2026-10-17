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

import re

from .claims import spoken                                 # the settled stop reads what a move SAID, quoted spans only
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


# ---- THE ROUND (conversation design v2 section 3, gate round-loop) ---------------------------------------------
# One move, then the floor is offered: the engine decides who is asked and in what order (urge, deterministic);
# each asked listener decides what to do with it (take, interject, hold); a speaker nobody interrupted decides
# whether to go on (keep, yield). The model is asked to be the person; who is asked is never the model's call.
INTERRUPT_THRESHOLD = 0.45   # a listener moved this far is told it may cut in (design v2 s3; a recorded scene's 0.22-0.41 must not)
MOVE_WORDS = 80              # a move longer than this is regenerated once with the tripwire line (design v2 s2)
SPEAKER_WORDS = ("keep", "yield")
LISTENER_WORDS = ("take", "interject", "hold")


def ask_order(urges):
    """-> the listeners to ask after a move, highest urge first (`leader`'s tie-break). A two-hander asks the one
    other always: there the urge decides nothing, since the only alternative to asking is a silence nobody chose.
    A crowd asks those at or above FLOOR_THRESHOLD; nobody there is the lull."""
    order = sorted(urges, key=lambda k: (-urges[k][0], str(k)))
    return order if len(order) == 1 else [k for k in order if urges[k][0] >= FLOOR_THRESHOLD]


def floor_word(stance, said, acted):
    """A reply's floor word, read in the stance it was asked in -> (word, overridden). A word from the other
    stance's list, or none, is read the safe way: a speaker's as yield (the floor goes out to be offered), a
    listener's as take when it said or did something and hold when it did neither. `overridden` is the word as
    the reply wrote it when it was not taken at its word, else ''."""
    own = SPEAKER_WORDS if stance == "speaker" else LISTENER_WORDS
    if said in own:
        return said, ""
    return ("yield" if stance == "speaker" else ("take" if acted else "hold")), str(said or "")


class Round:
    """Who is called next, and in what stance. A call is (stance, who, flags) for `prompt.build_turn_messages`;
    an ending is a reason string: "empty" (nobody else here and the speaker yielded), "lull" (a crowd in which
    nobody cleared the floor and the speaker yielded), "settled" (the forced floor held twice).

    `after_move` takes the urges of every other present listener for the move just made (`next_speaker`'s map);
    `after_listener` takes an asked listener's interject or hold. A take is a move: the caller reports it through
    `after_move`, as a yield (the line was the move; whether the taker has more is asked when nobody takes it back).
    Deterministic, holds no model."""

    def __init__(self, opener):
        self.holder, self.kept, self.queue, self.urges, self.forced = opener, False, [], {}, None
        self.call = ("speaker", opener, {})

    def _go(self, call):
        self.call = call
        return call

    def _resume(self):
        return self._go(("speaker", self.holder, {"resumed": True}))

    def _ask(self):
        who = self.queue.pop(0)
        cut = self.kept and self.urges[who][0] >= INTERRUPT_THRESHOLD   # licensed only while they mean to go on
        return self._go(("listener", who, {"interrupt": True} if cut else {}))

    def after_move(self, who, word, urges, present):
        self.holder, self.kept, self.forced = who, word == "keep", None
        self.urges = {k: v for k, v in urges.items() if k in present and k != who}
        self.queue = ask_order(self.urges)
        if self.queue:
            return self._ask()
        if self.kept and who in present:        # nobody to ask, or nobody moved enough: alone on stage goes on
            return self._resume()
        return "lull" if self.urges else "empty"

    def skipped(self, present):
        """The call committed nothing (a leak or an empty draw survived the retries). A listener's counts as a hold;
        a speaker's passes the floor to the next person present, as the beat loop did before the round."""
        stance, who, _ = self.call
        if stance == "listener":
            return self.after_listener("hold", present)
        others = [i for i in present if i != who]
        if not others:
            return "empty"
        self.holder, self.kept, self.queue, self.forced = others[0], False, [], None
        return self._go(("speaker", others[0], {}))

    def after_listener(self, word, present):
        if self.forced is not None:               # the forced floor held a second time: the scene has settled
            return "settled"
        self.queue = [q for q in self.queue if q in present]
        if self.queue:
            return self._ask()
        if self.kept and self.holder in present:  # interjections in view, the speaker goes on
            return self._resume()
        here = {k: v for k, v in self.urges.items() if k in present}
        if not here:
            return "empty"
        self.forced = leader(here)                # every asked listener held after a yield: one more ask
        return self._go(("listener", self.forced, {"forced": True}))


# ---- THE SETTLED STOP (design v1 s3 rule 3, v2 s3; gate settled-stop) -----------------------------------------
# A two-hander never lulls (every move asks the other), so a talk that has run out must be noticed another way: the
# moves stop carrying anything their speaker had not already said. Heat overrides it - an argument repeats itself.
SETTLED_MOVES = 4
STOP_WORDS = frozenset(("the", "and", "you", "your", "but", "not", "for", "with", "that", "this", "are", "was", "were",
                        "have", "has", "had", "its", "it's", "his", "her", "him", "she", "they", "them", "then", "there",
                        "what", "all", "can", "will", "just", "now", "too", "out", "our", "from", "into", "don't"))


def _said(action):
    """-> (content words, asked, spoke) of what a move SAID: its quoted spans, words of three letters or more off the stop
    list, and whether any span asks a question. Narration is not speech (`claims.spoken`)."""
    spans = spoken(str(action or ""))
    words = {w for w in re.findall(r"[a-z']+", " ".join(spans).lower()) if len(w.strip("'")) >= 3 and w not in STOP_WORDS}
    return words, any("?" in s for s in spans), bool(spans)


def settled(log, urges):
    """True when the last SETTLED_MOVES moves in `log` each said nothing new and no listener's urge for the move just
    made is above INTERRUPT_THRESHOLD. A row is a move when its `move` is true. A move is nothing new when every
    content word of its quoted speech was said by the same speaker on an earlier row this scene, and it is not a
    question and not a cut-in (`cut`); a move with no content words is nothing new (a bare "No." ends a thread). A
    move that SAID nothing - no quoted speech, a body at work - is not talk running out, and breaks the run."""
    if any(v[0] > INTERRUPT_THRESHOLD for v in (urges or {}).values()):
        return False
    said, run = {}, 0
    for row in log:
        words, asked, spoke = _said(row.get("action"))
        if row.get("move"):
            run = run + 1 if (spoke and not asked and not row.get("cut") and words <= said.get(row.get("who"), set())) else 0
        said.setdefault(row.get("who"), set()).update(words)
    return run >= SETTLED_MOVES
