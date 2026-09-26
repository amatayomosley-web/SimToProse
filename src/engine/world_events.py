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
from .fold import CORRECTION as _CORRECTION      # the one type whose effect reaches BACKWARD


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


# THE KEYS THE FOLD READS BEYOND THE REQUIRED ONES (gate keeper-replies), per FORM where a type has two: the tension
# chassis reads the seed's structure for a seed and `heat` for a delta (tensions.fold_seed / validate_seed,
# fold_delta / validate_delta; `tensions.is_seed` tells them apart). `required_keys` is what `rubric` renders into
# the keeper's prompt - bytes a recorded run replays by - so it stays as it is, and this table carries the rest.
# tests/test_keeper_replies.py folds every type and form through the real fold in three worlds, recording what it reads;
# and the keeper checks every strip against the fold itself, per report (`projected`), in the world the report is
# judged in - so a table that falls behind refuses loudly wherever its read fires in either.
_ALSO_READ = {"tension": {"seed": ("interests", "temperature", "factions", "watches", "cooling"), "delta": ("heat",)}}


def payload_keys(etype, payload=None):
    """Every payload key the fold reads for this type - for this FORM of it, given the payload - -> tuple: the required
    keys, then the rest.

    A keeper's world change keeps these and nothing else. The log stores a payload whole, and a reader that takes
    every event's payload whatever its type (`scene_facts.payloads`, which `injuries.run_rows` reads through) would
    read any other key as a beat's own - measured 2026-09-25, a keeper move carrying `injuries` was an injury."""
    _known(etype, "payload_keys")
    forms = _ALSO_READ.get(etype)
    if not forms:
        return _WORLD[etype][1]
    from .tensions import is_seed                  # the chassis's own test of its form; lazily, as fold.py does
    return _WORLD[etype][1] + forms["seed" if is_seed(payload if isinstance(payload, dict) else {}) else "delta"]


# THE TYPE EACH KEY THE FOLD READS MUST HOLD, for the fold to write what it means. Measured at HEAD 2026-09-25 (gate
# keeper-replies): a reveal whose `to` was one name as text made each of its letters a knower (set.update walks a
# string); a numeric fact or asset folded to an int key that the persisted snapshot stores as text, so every later
# resume refused with LEDGER_RESUME_DIVERGENCE; a move `to` a list parked a list as a location; a harm with terminal
# "false" killed. A tension's id is text because an identity is (HEAD wrote a number's string form - no brick, a name
# nobody chose). The review found it one level down too: a dimension valued true, NaN or Infinity folded as heat, and
# NaN reached the log as a token JSON does not have. "Text" is text the record can HOLD (`replies.text_ok`): a lone
# surrogate passed `isinstance(v, str)`, then crashed the write or bricked every later park and resume.
_TEXT, _NAMES, _TRUTH, _DIMS, _FINITE = "text", "a list of names", "true or false", "a map of the seven dimensions " \
    "to numbers in [0,1]", "a finite number"
_TYPED = {"move": {"to": _TEXT}, "harm": {"terminal": _TRUTH}, "reveal": {"fact": _TEXT, "to": _NAMES},
          "seize": {"asset": _TEXT}, "destroy-asset": {"asset": _TEXT}, "threaten": {"dimensions": _DIMS},
          "tension": {"id": _TEXT, "heat": _FINITE}}


def _finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and v not in (float("inf"), float("-inf"))


def _dims(v):
    from .world_appraisal import DIMENSIONS
    return isinstance(v, dict) and all(k in DIMENSIONS and _finite(x) and 0.0 <= x <= 1.0 for k, x in v.items())


def _text(v):
    from .replies import text_ok
    return text_ok(v)


_HOLDS = {_TEXT: _text, _TRUTH: lambda v: isinstance(v, bool), _NAMES: lambda v: isinstance(v, list) and all(
    _text(x) for x in v), _DIMS: _dims, _FINITE: _finite}


def _not_finite_anywhere(v):
    """Does a payload hold a NaN or an infinity at any depth? -> bool. The log is JSON, which has neither."""
    if isinstance(v, float):
        return not _finite(v)
    if isinstance(v, dict):
        return any(_not_finite_anywhere(x) for x in v.values())
    if isinstance(v, list):
        return any(_not_finite_anywhere(x) for x in v)
    return False


def _walked(etype, walk, value):
    """`walk(value)`, a value NESTED TOO DEEP TO WALK refused by code wherever the depth sits - a key nothing reads
    inside a kept map included: the log stores a kept map whole and every later fold parses it, and a value HEAD wrote
    about 950 levels deep bricked every fold after it (gate keeper-replies, third review: it was refused, uncoded). The
    walk's own limit is the bound - a few hundred levels, moving with the caller's stack - and values 400-800 deep
    that HEAD wrote were survived by later folds: the margin is a declared choice (fourth review)."""
    try:
        return walk(value)
    except RecursionError:
        raise WorldEventError(
            "WORLD_EVENT_PAYLOAD_VALUE_TYPE",
            "world_events.validate_payload: %r carries a value nested too deep to walk - the log stores it whole, and "
            "every later fold would parse it" % (etype,)) from None


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

    TYPE, the same defect one level further (gate keeper-replies): a present, non-blank key of the wrong type folds
    into a world nobody meant - see `_TYPED`. Checked AFTER the blanks, so every payload refused before is refused by
    the same code (a blank `terminal` is still an empty one, as tests/test_world_events.py derives for every key).
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
    wrong = ["%r as %s" % (k, kind) for k, kind in _TYPED.get(etype, {}).items()
             if k in payload and not _HOLDS[kind](payload[k])]           # a required key is present by now
    if wrong or _walked(etype, _not_finite_anywhere, payload):
        raise WorldEventError(
            "WORLD_EVENT_PAYLOAD_VALUE_TYPE",
            "world_events.validate_payload: %r needs payload key %s - the fold writes what the value is, and the log "
            "that holds it cannot be edited" % (etype, ", ".join(wrong) or "values that are finite numbers (the log "
                                                "is JSON, which has no NaN or Infinity)"))
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
    return would_move(snap, projected(led, snap, event, at))


def projected(led, snap, event, turn):
    """`snap` with this event projected onto a COPY, as committing it at `turn` would -> dict. WRITES NOTHING.

    The warrant test's arithmetic, and - since gate keeper-replies' second review - the keeper's check on its own strip:
    the event it writes (keys and ids it judged unread left out) must project exactly as the event it was given, or
    what it left out was read after all. Per report, so a read the fold makes only for some values (`target or actor`)
    is decided for the values in hand, not by a table - and in the world `snap` is, which is the log as it stands when
    the report is judged, not the one a later backdated append or correction replays it into (third review)."""
    after = copy.deepcopy(snap)
    led._project(after, _candidate_row(event, turn))
    return after


def _reaches_back_to(led, run_id, event, eff):
    """The EARLIEST turn this event makes the snapshot cache wrong at -> int.

    For every type but one that is the event's own `effective_at`: folding it changes the world
    from its own tick forward and nothing before it. A `correction` is the exception, and it is the
    exception that this function exists for. Its effect is that `fold` SKIPS the ids it supersedes,
    and those ids sit BELOW it — at the flagged turn — so the folds it changes start there, not at
    its own tick.

    MEASURED, not anticipated (2026-09-19, while building the emitter). Without this the sequence
    park at turn N -> `critic.py --correct` -> run one more turn -> resume raised
    LEDGER_RESUME_DIVERGENCE every time: `snapshots.divergence` replays the tail onto a cached
    snapshot that had ALREADY folded the bad event, and a tail replay cannot un-apply it, while the
    from-zero fold beside it now skips it. The two disagreed, which is the divergence check doing
    exactly its job and reporting a cache this writer failed to invalidate. Dropping the cache back
    to the superseded event is the repair, because from there the fold is from-zero again.

    Reads the superseded rows rather than trusting the payload's own turn field: `supersedes` names
    ids, and an id's `effective_at` is a fact of the log. An id this run does not have contributes
    nothing (MIN over an empty match is NULL) instead of raising — a correction naming a stale id
    is a bad correction, not a reason to refuse the write that records it."""
    if event.type != _CORRECTION:
        return eff
    ids = [int(i) for i in (event.payload.get("supersedes") or [])]
    if not ids:
        return eff
    row = led.con.execute(
        "SELECT MIN(effective_at) AS m FROM events WHERE run_id = ? AND event_id IN (%s)"
        % ",".join("?" * len(ids)), [run_id] + ids).fetchone()
    return eff if row["m"] is None else min(eff, int(row["m"]))


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

    ...AND THAT LAST SENTENCE NOW HAS A SECOND CALLER (2026-09-19). `scripts/critic.py:correct_run`
    appends the `correction` row itself through here, so the sentence describes a path rather than
    an intention. Nothing needed widening for it and the type table above is NOT consulted on the
    way in: this function validates a `records.Event` (type non-empty, payload a dict, visibility in
    `records.VISIBILITIES`) and inserts — `_known`/`validate_payload` guard the NOTICING seat in
    `keeper.py`, not the log. Three properties of this writer are what the correction protocol
    needed and why it does not get its own: the insert is the only INSERT on `events` outside a turn
    commit, the row lands with the two clocks filled by one rule, and the snapshot cache is dropped
    inside the same transaction — from the earliest turn each event makes the cache wrong at, which
    for a correction is BELOW its own tick (`_reaches_back_to`, and the divergence it was measured
    against).
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
            earliest = min(earliest, _reaches_back_to(led, run_id, ev, eff))
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
