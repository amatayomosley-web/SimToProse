"""world_events.py — what makes an event worth recording to the WORLD, and what each type means.

`ledger._project` (:352) moves exactly six snapshot fields, and every world event type owns one of
them. That ownership is the whole answer to "what constitutes a change worthy of updating", and it
makes the question DECIDABLE rather than a matter of taste:

    AN EVENT IS A WORLD EVENT IFF FOLDING IT WOULD CHANGE THE SNAPSHOT.

Fold it and diff. If the world is identical afterwards, it was not a world event — it was a beat,
and the appraisal tier already recorded it. Nothing about that test requires judgement, which is
why it belongs here and not in an agent's prose: `docs/design.md`'s compute/generate split and
CLAUDE.md hard rule 3 put the reading in the LLM and the arithmetic in the engine, and "did the
snapshot move" is arithmetic.

What the reader still owns is NOTICING — that a character is somewhere new, that someone now knows
a thing they did not. The boundary tests below exist for that half: each one separates its type
from the nearest thing it is NOT, phrased so a reader of the beat can run it.

THE SIX FIELDS, and the types that own them:

    agents[actor].location        move
    agents[victim].life_status    harm (terminal only)
    information[fact]             reveal
    holdings[asset]               seize, destroy-asset
    relationships[a|b].standing   betray, bond
    tensions[id]                  tension, threaten

RESOLVED 2026-09-02, and left here because the shape recurs. `consolidation.CATALOG` declared
`threaten` with `world_map: "tensions"` on 2026-06-11 and `_project` had no branch for it, so for
three months it folded to nothing while claiming a world effect. Neither obvious repair was safe —
`world_map` is what `ACTOR_TAG_TYPES` filters on, so blanking it hands `threaten` to actors — and the
note here used to say a branch "needs a tension identity the payload does not carry". That was the
wrong reading: `world-dynamics.md` says an act raises THE RELEVANT tension, "computed, never
guessed", so the identity is priced from standing interests rather than carried. `tests/test_world_events.py`
derives the declared-but-never-folded set from the two tables every run and now expects it EMPTY.
"""
import copy
import json

from .errors import EngineError


class WorldEventError(EngineError):
    """A world event whose payload the fold cannot use."""


# type -> (snapshot field it owns, payload keys `_project` reads, meaning, boundary test)
# The payload keys are read straight off `ledger._project`; a test asserts they stay in step.
_WORLD = {
    "move": (
        "agents[actor].location", ("to",),
        "a character is somewhere the snapshot does not say they are",
        "vs crossing a room: the destination must be a place the world model NAMES. Position "
        "within a named place is staging, not a move"),
    "harm": (
        "agents[victim].life_status", ("terminal",),
        "a character is dead",
        "vs injury: only terminal harm moves the world. A wound that leaves them alive is an "
        "appraisal event and nothing more — the fold reads `terminal` and ignores the rest"),
    "reveal": (
        "information[fact]", ("fact", "to"),
        "someone now knows a fact the snapshot does not list them as knowing",
        "vs saying it again: the fact must be one the world model tracks BY NAME, and the "
        "knower must not already be on its list. Repeating what is known reveals nothing"),
    "seize": (
        "holdings[asset].controller", ("asset",),
        "control of a named asset passed to someone",
        "vs handling it: possession CHANGED HANDS. Touching, using or guarding an asset you "
        "already control is not a seizure"),
    "destroy-asset": (
        "holdings[asset].destroyed", ("asset",),
        "a named asset no longer exists",
        "vs damage: irreversible. If the thing is still usable, its controller is unchanged and "
        "nothing folded"),
    "betray": (
        "relationships[a|b].standing", (),
        "the standing between two people became enmity",
        "vs trusting them less: STANDING is a category, the axes are degree. Trust, affinity, "
        "respect and debt move every beat in `bonds.py` and are not this. Emit only when you "
        "would say 'they are enemies now', not 'that cost him'"),
    "bond": (
        "relationships[a|b].standing", (),
        "the standing between two people became alliance",
        "vs growing closer: the same category/degree line as betray, in the other direction"),
    "threaten": (
        "tensions[*].temperature", ("dimensions",),
        "an act lands on a standing grievance the world already carries",
        "vs a private squabble: heat lands only where a NAMED tension WATCHES one of these people "
        "or this place. It names no tension — the engine prices the act against every live one "
        "(world-dynamics.md: the relevant tension, computed, never guessed). Nothing watching means "
        "it was a beat, and the appraisal tier already recorded it"),
    "tension": (
        "tensions[id]", ("id",),
        "a named tension's temperature or factions changed",
        "vs a private grievance: the tension must be one the world model NAMES. Two people "
        "falling out is a standing change; a faction conflict heating is this"),
}

TYPES = tuple(sorted(_WORLD))


def _known(etype, where):
    """One refusal for the one question every function here opens with."""
    if etype not in _WORLD:
        raise WorldEventError(
            "WORLD_EVENT_TYPE_UNKNOWN",
            "world_events.%s: %r moves no snapshot field; the world types are: %s"
            % (where, etype, ", ".join(TYPES)))


def field_of(etype):
    """The one snapshot field this type owns. Raises on a type that folds to nothing."""
    _known(etype, "field_of")
    return _WORLD[etype][0]


def required_keys(etype):
    """The payload keys `ledger._project` reads for this type."""
    _known(etype, "required_keys")
    return _WORLD[etype][1]


def _empty_strings(value):
    """Does this payload value carry an empty string anywhere the fold will read one? -> bool.

    A required key holds an identity (`fact`, `asset`, `id`), a destination (`to` on a move), a list
    of knowers (`to` on a reveal), or a structure the fold walks itself (`dimensions`, `terminal`).
    Only the first three can BE a blank string, and this reports on exactly those shapes rather than
    asking each type what it carries — a per-type table here would be the eighth hand-maintained
    duplicate CLAUDE.md tabulates.
    """
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple)):
        return any(isinstance(v, str) and not v.strip() for v in value)
    # A DICT REPORTS CLEAN, and that is a pinned assumption rather than an oversight: the only
    # dict-valued required key is `dimensions`, whose keys never become a snapshot key and are
    # refused outside the seven appraisal dimensions by `world_appraisal.validate_interests`
    # anyway. If a type is ever added whose dict KEYS the fold writes, this is the line to widen.
    return False


def validate_payload(etype, payload):
    """Fail loud on a payload the fold cannot use. Hard rule 6.

    TWO HALVES OF ONE RULE, and the second was missing for as long as the first existed.

    PRESENCE. A missing key does not raise in `_project` — the branch simply does not fire, and the
    event lands in the log claiming a world effect it never had. That is the silent-corruption shape
    this repo keeps paying for, so it is caught at the boundary instead.

    VALUE. An EMPTY key is worse, because the branch DOES fire. `_project` guards its actor-keyed
    branches (`if ev["actor"]`, `if victim:`, `if actor and target`) and its payload-keyed ones were
    never guarded at all, so `fact: ""` and `asset: ""` wrote a blank snapshot key. Checking that a
    key is present and never what it carries is the same defect one level down, and it is the level
    where the log — which cannot be edited — is what holds the damage.
    """
    _known(etype, "validate_payload")
    payload = payload if isinstance(payload, dict) else {}
    missing = [k for k in _WORLD[etype][1] if k not in payload]
    if missing:
        raise WorldEventError(
            "WORLD_EVENT_PAYLOAD_KEY_MISSING",
            "world_events.validate_payload: %r needs payload key(s) %s to move %s; got keys %s"
            % (etype, ", ".join(missing), _WORLD[etype][0], sorted(payload) or "none"))
    blank = [k for k in _WORLD[etype][1] if _empty_strings(payload[k])]
    if blank:
        raise WorldEventError(
            "WORLD_EVENT_PAYLOAD_VALUE_EMPTY",
            "world_events.validate_payload: %r carries an EMPTY %s. %s is what the fold writes, and "
            "an empty one is an identity nothing can name, cite or resolve — measured 2026-09-02, a "
            "reveal with an empty fact folded to information[''], entered the append-only log, and "
            "from that turn on every persist_snapshot and every resume raised on the schema's "
            "`key <> ''`. There is no correction event that removes it. Name the thing or emit "
            "nothing: an act on nothing was a beat, and the appraisal tier already recorded it."
            % (etype, " and an empty ".join(blank), _WORLD[etype][0]))
    return True


def rubric():
    """The emit definition for the seat that reads the stream — meaning AND boundary per type.

    Contract text only; no engine module reads it. Opens with the decidable rule, because that is
    the part that removes the judgement: the reader notices, the engine decides whether it counted.
    """
    head = ("A world event is warranted IFF folding it would change the world snapshot. "
            "If the world reads identically afterwards, it was a beat, not a world change — "
            "the appraisal tier has already recorded it.")
    # THE PAYLOAD CONTRACT, rendered from `required_keys` — the same table the fold reads.
    #
    # The rubric taught meaning and boundary and left the SHAPE unsaid, so a seat instructed to
    # grade "in the severity words" had to guess both the slot and the legal keys. Measured
    # 2026-09-02 on the assembled keeper prompt: one of seven dimension names present, no payload
    # shape at all — and `social_violation` is not a guessable spelling. Generated here rather than
    # written into one seat, so every future type carries its own contract to every seat that
    # renders this.
    rows = []
    for t in TYPES:
        keys = required_keys(t)
        shape = ("payload {%s}" % ", ".join('"%s": …' % k for k in keys)) if keys else "no payload keys"
        rows.append("%s — %s. Moves %s. %s. [%s]"
                    % (t, _WORLD[t][2], _WORLD[t][0], shape, _WORLD[t][3]))
    # ...and the one key whose VALUE vocabulary is not obvious from its name.
    from .world_appraisal import DIMENSIONS
    # The VALUE vocabulary too, not only the key vocabulary. Without this clause the seat had to
    # join three separate blocks — the ladder, "grade in the severity words", and this key list — to
    # work out that a dimension takes `"marked"` rather than a number. One inferential hop is one
    # too many in a contract.
    tail = ("A `dimensions` map is keyed by the seven appraisal dimensions and by nothing else: %s. "
            "Each is VALUED with a severity word from the ladder above — {\"threat\": \"marked\"}, "
            "never a number."
            % ", ".join(sorted(DIMENSIONS)))
    return head + chr(10) + chr(10).join(rows) + chr(10) + chr(10) + tail


def would_move(before, after):
    """THE WARRANT TEST, as arithmetic: did folding this event change the world?

    `AN EVENT IS A WORLD EVENT IFF FOLDING IT WOULD CHANGE THE SNAPSHOT` — the rule stated at the
    top of this file, here as the function that decides it. Fold the log, fold it again with the
    candidate appended, and compare the fields the world owns. Identical -> it was a beat, and the
    appraisal tier already recorded it.

    Compares the WORLD fields only, never the clock: `fold` stamps `clock.now` on every snapshot, so
    comparing whole dicts would call every candidate a world event. That is the one way this test
    can silently pass for the wrong reason, so it is excluded by name rather than by luck.

    No judgement, no whitelist, no per-type special case — which is why it lives in the engine
    while the NOTICING that produced the candidate lives in the harness (hard rule 3).
    """
    keys = set(before) | set(after)
    keys.discard("clock")
    return any(before.get(k) != after.get(k) for k in keys)


# ---------------------------------------------------------------------------------------------
# THE WRITER AND THE WARRANT. These take a `Ledger` rather than living on it, for a measured
# reason: putting them there pushed `ledger.py` to 519 lines and `test_map` went red on hard rule
# 6. This module already owns the CONCEPT — what makes an event worth recording to the world — so
# it is the honest home for the two functions that decide and perform it, and `bible.py` /
# `scene_cfg.py` are the same shape.


def _candidate_row(event, turn):
    """The event as `_project` will see it once committed — EVERY field it reads.

    A partial row is how the first version failed: it supplied type, payload, actor and target, and
    `_project`'s betray/bond branch reads `ev["effective_at"]`, so two of the eight world-moving
    types raised KeyError through the seat instead of being judged. The row is built here, once,
    from the same defaults `append` applies, so the two cannot drift; `test_keeper` DERIVES the
    field set from `_project`'s own source and fails if this ever falls behind again.
    """
    caused = turn if event.caused_at is None else event.caused_at
    eff = caused if event.effective_at is None else event.effective_at
    return {"type": event.type, "payload": json.dumps(event.payload),
            "actor": event.actor, "target": event.target, "location": event.location,
            "visibility": event.visibility, "turn": int(turn),
            "caused_at": int(caused), "effective_at": int(eff)}


def would_change(led, run_id, as_of_turn, event, at_turn=None):
    """Would folding this event change the world? -> bool. WRITES NOTHING.

    It has to be write-free. `events` is append-only at the DATABASE (hard rule 2, triggers since
    schema v9), so the obvious shape — append, fold, diff, roll back — cannot roll back: the trigger
    refuses the DELETE, which is the rule working exactly as intended and the reason this exists.

    So the candidate is projected onto a COPY of the folded snapshot instead, with the same
    `Ledger._project` the real fold uses, so the answer cannot drift from what committing would do.

    `at_turn` is where the event will actually LAND, and it defaults to `as_of_turn` only because
    every existing caller passed one turn for both. They are not the same question: `append` inserts
    at the proposal's own turn, so judging a backdated candidate against the HEAD asked whether it
    would change a world it never enters. Measured 2026-09-01: a backdated move was accepted while
    leaving the head fold identical, violating this module's own stated invariant.
    """
    at = as_of_turn if at_turn is None else at_turn
    snap = led.fold(run_id, at)
    after = copy.deepcopy(snap)
    led._project(after, _candidate_row(event, at))
    return would_move(snap, after)


def append(led, run_id, turn, events):
    """Append WORLD events — the ones with no actor, or whose actor is incidental to the effect.

    THE WRITER THAT DID NOT EXIST. `ledger._project` moves six snapshot fields and every
    world-moving type owns one, but the eight types appeared ONLY inside the fold: seeded, then
    frozen for a whole book. A character could die and `life_status` stayed "alive". So the fold had
    branches no real run could reach, and `guide-operating.md`'s "sparse until move/harm/reveal
    events populate it" understated a case where nothing populates it at all.

    Appended OUTSIDE a turn commit, deliberately: the turn is the ACTOR's atomic unit and a world
    event has no actor. `events.turn` is documented as "the turn whose commit appended it" and
    `events.actor` as "NULL for world events" — this is the writer that column was waiting for.
    Append-only like everything else; a wrong world event is corrected by a new one.
    """
    led.load_run(run_id)
    earliest = None
    with led.con:
        for ev in events:
            ev.validate()
            caused = turn if ev.caused_at is None else ev.caused_at
            eff = caused if ev.effective_at is None else ev.effective_at
            led.con.execute(
                "INSERT INTO events (run_id, turn, caused_at, effective_at, type, actor, "
                "target, location, visibility, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, int(turn), int(caused), int(eff), ev.type, ev.actor, ev.target,
                 ev.location, ev.visibility, json.dumps(ev.payload)))
            earliest = eff if earliest is None else min(earliest, eff)
        # THE CACHE IS NOW STALE AT AND ABOVE THAT TURN, and this DELETE rides the same transaction
        # as the inserts above. `resume` replays only events AFTER the cached turn, so a scene
        # parked at turn N and then moved by the keeper at turn N could never be resumed — the
        # incremental fold would miss what the from-zero fold contains and the divergence check
        # would refuse forever. Invalidating is the writer's obligation, not resume's to tolerate.
        #
        # INSIDE the transaction, deliberately: the first version committed the events and then
        # invalidated separately, so a crash between the two commits re-created the very brick this
        # exists to prevent — a narrow window, and the same failure.
        if earliest is not None:
            from . import snapshots
            snapshots.drop_from(led.con, run_id, earliest, own_transaction=False)
    return len(events)
