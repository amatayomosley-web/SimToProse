"""tensions.py — the first register on the world-appraisal chassis.

`world-state-ledger.md` gives the snapshot a `tensions` field — *"each live tension's temperature +
faction status"* — and `history.md` says where they come from: *"History's output is the present's
UNRESOLVED tensions (the old grievance, the contested border, the suppressed faction) — the FUEL for
the director's circumstances."* A tension is authored world canon, not a runtime discovery.

WHAT WAS WRONG FOR THREE MONTHS. `consolidation.CATALOG` declared `threaten` with
`world_map: "tensions"` on 2026-06-11, the same day the fold branch for `tension` landed, and no
`threaten` branch was ever written. The register was inert in every direction at once: not
authorable (`vault.py` and `lint_book.py` did not know the word), not seeded, never emitted, no
delta path (the one branch SET temperature absolutely), and no decay. `threaten` claimed a world
effect it had never once had.

THE PIECE THAT WAS ACTUALLY MISSING was the word "relevant". `world-dynamics.md` says a public
killing raises *the relevant* tension temperature, and nothing decided which one was relevant. The
answer is not a lookup — it is the doc's own formula, and it lives in `world_appraisal.py`: an event
is priced against EVERY live tension's standing interests, and lands on the ones that watch it.

THREE FENCES keep this from minting a tension per squabble (`world-state-ledger.md`: *"only the
levered is written ... the sim doesn't log every peasant"*):

  1. MINTING IS THE DIRECTOR'S. `world-dynamics.md`: *"the world is DIRECTED (the room acts it) ...
     its will is the director."* The keeper may propose HEAT against a tension that exists; it may
     never name a new one. Naming new world structure is a willful act and the room holds will.
  2. SCOPE AND INTERESTS are arithmetic. A threat between two unwatched people in an unwatched place
     matches nothing.
  3. THE WARRANT GATE finishes it. A `threaten` that heats nothing fails `world_events.would_change`
     at its own turn and is refused with the reason printed — it was a beat, and the appraisal tier
     already recorded it.

TWO EVENT FORMS, one type, told apart by the fields present:

    SEED / MINT   the whole authored row      -> creates or restates the tension
    DELTA         {id, heat}                  -> adds heat, clamps, stamps `last_heated_at`

THE SEMANTICS CHANGED, and saying so plainly: the pre-existing branch took `{name, temperature}`
and SET the value absolutely. This keys on `id` (as world notes key locations and people) and splits
create from accumulate, because a register that can only be set cannot accumulate heat from acts.
Nothing breaks — no run has ever logged a tension event, so there is no history to reinterpret — but
an early draft of this docstring claimed the form was byte-identical, and it is not.
"""
import json

from . import world_appraisal as _wa
from .errors import EngineError

# How far a fully-relevant event moves a tension. Class-B, probe-calibrated start, in the shape
# `arc._BASE_STEP` uses: pick the target, derive the constant, write the derivation down.
#
# TARGET: a SEVERE act (0.78) landing on a tension that cares about exactly that dimension moves it
# about one band of the severity ladder — roughly 0.15. relevance(0.78 on a single matched interest)
# is 0.78, so step = 0.15 / 0.78 ~= 0.19. Rounded to 0.20 because the ladder's own rungs are coarser
# than three decimals and a spurious precision here would invite tuning it by feel.
#
# The consequence, stated so it is checkable: it takes roughly five severe, fully-relevant public
# acts to carry a tension from cold to boiling, and a partly-relevant one contributes proportionally
# less. A book that boils a tension in two beats is telling you this constant is wrong.
_HEAT_STEP = 0.20


class TensionError(EngineError):
    """A tension the fold cannot use. Raised BEFORE the write."""


def _require(cond, code, msg):
    """Refuse with a REGISTERED code. `errors.EngineError` refuses to construct an unknown one, so
    the registry cannot drift from the raises — that is the half of `codes.py`'s contract this
    module was built without and converted into on the same day."""
    if not cond:
        raise TensionError(code, msg)


def _severity_words():
    """The ladder, imported at call time to keep the module import graph shallow."""
    from .severity import WORDS
    return WORDS


def validate_seed(row, where="tension"):
    """An authored tension, whole. Raises naming the field and what it costs to omit it."""
    _require(isinstance(row, dict), "TENSION_NOT_AN_OBJECT",
             "%s must be an object, got %s" % (where, type(row).__name__))
    name = str(row.get("id") or "").strip()
    _require(name, "TENSION_ID_MISSING",
             "%s has no id — the id IS the identity, and a tension with no id cannot be "
                   "heated, cited, or resolved. World notes key locations and people by `id`; "
                   "tensions use the same key, in both the seed and the delta form." % where)
    _wa.validate_interests(row.get("interests"), "%s[%s].interests" % (where, name))
    _wa.validate_watches(row.get("watches"), "%s[%s].watches" % (where, name))
    rate = row.get("cooling", _wa.DEFAULT_COOLING)
    _require(rate in _wa.COOLING, "TENSION_COOLING_UNKNOWN",
             "%s[%s].cooling is %r; expected one of: %s"
             % (where, name, rate, ", ".join(sorted(_wa.COOLING))))
    temp = row.get("temperature", 0.0)
    if isinstance(temp, str):
        # THE AUTHORING SEAM — and this is TOLERANCE, not the contract.
        #
        # THE CONVENTION, stated for whoever writes the next register's payloads: THE LOG STORES
        # FLOATS. A severity word is an authoring convenience and dies at the boundary that reads
        # it — `scripts/keeper.py` resolves a proposal's words before the write, and `from_world`
        # resolves an authored note's on load. A word that survives INTO the log is a hostage to
        # `severity._MAGNITUDE`: recalibrate that table and every historical run refolds into a
        # different world, which is hard rule 2's "pure function of the log" true in form and false
        # in substance.
        #
        # This branch stays because word-carrying tension events were writable for a few hours on
        # 2026-09-02 and a fold must remain total over anything already in a log. It is not a
        # licence to write more of them.
        from .severity import WORDS, value_of, SeverityError
        word = temp.strip().lower()
        _require(word in WORDS, "TENSION_TEMPERATURE_WORD_UNKNOWN",
                 "%s[%s].temperature = %r is not a severity word; expected one of: %s"
                 % (where, name, temp, ", ".join(WORDS)))
        temp = value_of(word)
        row["temperature"] = temp
    _require(isinstance(temp, (int, float)) and not isinstance(temp, bool) and 0.0 <= temp <= 1.0,
             "TENSION_TEMPERATURE_RANGE",
             "%s[%s].temperature = %r is neither a severity word (%s) nor a number in [0,1]"
             % (where, name, row.get("temperature"), ", ".join(_severity_words())))
    factions = row.get("factions", [])
    _require(isinstance(factions, list), "TENSION_FACTIONS_TYPE",
             "%s[%s].factions must be a list" % (where, name))
    for i, f in enumerate(factions):
        _require(isinstance(f, str) and f.strip(), "TENSION_FACTION_EMPTY",
                 "%s[%s].factions[%d] is %r — a faction is named or it is not a party to anything, "
                 "and the snapshot carries this list verbatim for the room to read"
                 % (where, name, i, f))
    return name


def validate_delta(payload, where="tension delta"):
    """A heat delta: {id, heat}."""
    _require(isinstance(payload, dict), "TENSION_NOT_AN_OBJECT", "%s must be an object" % where)
    name = str(payload.get("id") or "").strip()
    _require(name, "TENSION_ID_MISSING",
             "%s names no tension — a delta is {id, heat}, keyed the same way the seed is" % where)
    heat = payload.get("heat")
    _require(isinstance(heat, (int, float)) and not isinstance(heat, bool),
             "TENSION_DELTA_HEAT_TYPE",
             "%s.heat = %r is not a number" % (where, heat))
    return name


def is_seed(payload):
    """Seed form or delta form? The seed carries the authored structure; the delta carries heat."""
    return isinstance(payload, dict) and "interests" in payload


def fold_seed(register, payload, at_turn):
    """Create or restate a tension. Mutates `register` in place, the way `_project` branches do."""
    name = validate_seed(payload)
    register[name] = {
        "temperature": float(payload.get("temperature", 0.0)),
        "factions":    list(payload.get("factions", [])),
        "interests":   dict(payload["interests"]),
        "watches":     {"parties":   list((payload.get("watches") or {}).get("parties") or []),
                        "locations": list((payload.get("watches") or {}).get("locations") or [])},
        "cooling":     payload.get("cooling", _wa.DEFAULT_COOLING),
        "last_heated_at": int(at_turn),
    }
    return register


def fold_delta(register, payload, at_turn):
    """Add heat to a named tension. A delta naming no live tension is a NO-OP, deliberately.

    Not an error: the fold must stay a total function over the log (`world-state-ledger.md`: "a pure
    function of the log"), and a run resumed against an edited world note could legitimately replay a
    delta whose tension the author has since removed. The emitting seat refuses it up front instead —
    that is where a live mistake is catchable and where the operator is standing, and it now says
    "names no live tension" rather than reporting a reference error as a warrant failure.

    A `heat` of 0 is legal and is NOT a no-op: it restamps `last_heated_at`, which delays cooling.
    That is the grievance re-aired without anything new happening, and it is a real move the room
    may want — but it means a zero-heat delta passes the warrant gate on the timestamp alone, so it
    is written down here rather than discovered later.
    """
    name = validate_delta(payload)
    row = register.get(name)
    if row is None:
        return register
    row["temperature"] = max(0.0, min(1.0, float(row.get("temperature", 0.0))
                                      + float(payload["heat"])))
    row["last_heated_at"] = int(at_turn)
    return register


def fold_act(register, dimensions, at_turn, actor=None, target=None, location=None):
    """A typed ACT prices itself against every live tension. The doc's formula, applied.

    Returns the names heated, so a caller can report which — several may move from one event, and
    that is correct: a public killing heating both the levy dispute and the old blood-feud is two
    true facts, not a collision.
    """
    heated = []
    for name in sorted(register):
        row = register[name]
        interests = row.get("interests") or {}
        if not interests or not _wa.in_scope(row.get("watches") or {}, actor, target, location):
            continue
        delta = _wa.heat(dimensions or {}, interests, _HEAT_STEP)
        if delta <= 0.0:
            continue
        row["temperature"] = max(0.0, min(1.0, float(row.get("temperature", 0.0)) + delta))
        row["last_heated_at"] = int(at_turn)
        heated.append(name)
    return heated


def effective(row, elapsed):
    """The tension's temperature NOW, after cooling — derived, never stored.

    The raw value in the snapshot is what the log folded to. Time is applied here, at read, so the
    fold stays a pure function of events and hard rule 2 stays literally true.
    """
    return _wa.cool(row.get("temperature", 0.0), elapsed, row.get("cooling", _wa.DEFAULT_COOLING))


def from_world(world):
    """The authored tensions of a world note -> [row], validated. Absent field -> []."""
    rows = (world or {}).get("tensions") or []
    _require(isinstance(rows, list), "TENSION_WORLD_FIELD_TYPE",
             "world.tensions must be a list of tensions")
    for row in rows:
        validate_seed(row)
    return list(rows)


def seed_events(world):
    """Authored tensions -> the `tension` events that put them in the log.

    THE DIRECTOR SEEDS AS EVENTS, NEVER AS A DECREE. `world-state-ledger.md` write-path #3 is
    explicit that the director "may seed ledger state ... but always as an event". That is what makes
    creation and a mid-run mint the SAME mechanism placed at different turns, rather than two.
    """
    return [{"type": "tension", "payload": dict(row)} for row in from_world(world)]


def rubric():
    """What a keeper needs to grade a threat, generated from this module rather than restated."""
    return ("A TENSION is an authored, standing thing — a grievance, a contested border, a "
            "suppressed faction. You never name a new one: only the room does that. What you report "
            "is that an act happened and how hard it landed, in the severity words; the engine "
            "prices it against every tension that watches those people or that place, and a threat "
            "that no tension watches was simply a beat.")
