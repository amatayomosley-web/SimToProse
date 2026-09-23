"""systems.py — which engine systems a book runs, declared in its world note.

WHY (gate systems-registry, 2026-09-22). The owner: "not every book needs everything we had ... we need
a plug and play mech for the book so user can decide what scripts they want the engine to use." A
review of the engine the same day found the right unit is not a script but a SYSTEM — the sheet block
that feeds it, the per-beat mover that changes it, the rows it writes and the line it renders — and
that most of the switch already existed as ABSENCE: measured, one block deleted at a time on the
fixture, nothing raises, a character with no vault recalls nothing, one with no edges stands with no
one. What was missing: a book's way to SAY which systems it runs; the movers honouring it (they create
state from nothing — a sheet with no wounds still mints scars); the pre-run check not demanding an off
system's blocks; and the one block whose absence LIED (a missing condition rendered the top energy
band, `direction.direct_condition`).

THE DECLARATION lives in the world note beside `switches` (the laws' per-book precedent):

    "systems": {"wounds": false, "attitude": false}

A name left out runs its default. A world with no `systems` key runs every legacy system — the engine
exactly as it was before this gate (proved against a frozen run of the previous head). A NEW system
(`condition_flow`, gate condition-flow) defaults OFF, so no existing book changes until it says so.

OFF MEANS IDENTITY, IN TWO HALVES. `strip` empties the system's block on a sheet right before a
scene's characters are built (after any resume has folded the log back on), so every reader sees it
absent — the census's identity. The drivers skip the system's MOVER. The mood replay strips its pinned
sheets at the same point, so a replayed run still equals its cache. OFF stops what a system does from
here on; what it already did stays in the story (a resting level an earlier scene moved stays moved).

Deterministic, stdlib + engine imports only, no LLM.
"""
from __future__ import annotations

__layer__ = "engine"

from .records import RecordError

# id -> (on by default, switchable, what it is, what OFF means). Core systems are listed so the book's
# author can see the whole engine; they are not switchable until each has its own proof of identity.
REGISTRY = {
    "emotion":     (True, False, "moods: decay, the receipt from readings, the directions the actor plays", ""),
    "perception":  (True, False, "what a character perceives in each beat", ""),
    "memory":      (True, False, "what a character knows, and what the moment brings to mind", ""),
    "bonds":       (True, False, "relationship edges: trust, affinity, respect, debt", ""),
    "attachments": (True, False, "what a character holds that is not a person", ""),
    "laws":        (True, False, "what the world permits (it keeps its own switches)", ""),
    "condition":   (True, True, "energy and stress: the memory budget, and how much they have left",
                    "no condition block is needed; the stage directions say nothing of energy; memory runs on a full budget"),
    "wounds":      (True, True, "scars: minted by lasting beats, tested by later ones, shown under what has marked you",
                    "no scar is minted, tested or shown"),
    "attitude":    (True, True, "what each person makes this character feel",
                    "no attitude accrues, fades or is shown"),
    "arc":         (True, True, "lasting beats move a character's resting levels",
                    "resting levels move no further"),
    # NEW SYSTEMS SHIP OFF (gate condition-flow): an existing book runs exactly as it did until it says so.
    "condition_flow": (False, True, "energy and stress move: spent by what a beat costs and by time, "
                       "restored across a declared gap, set by a scene when it says so",
                       "energy and stress stay where the sheet or a scene put them"),
    "body":        (False, True, "a strength each character carries, and the physical effort each act takes - read by "
                   "the event reader and weighed against that strength",
                   "no act costs physical effort; the event reader is not asked; no strength is needed"),
    "tells":       (False, True, "subtle signs: the event reader marks the parts of an act only a sharp eye would "
                   "catch, and a listener who does not catch them never reads them",
                   "every listener reads every act whole, as before; the event reader is not asked"),
    "injuries":    (False, True, "bodily injuries: the event reader marks harm done to a body, each heals over story "
                   "time by its severity, and whoever was hurt or saw it is told",
                   "no injury is marked, kept or shown; the event reader is not asked"),
}
SWITCHABLE = tuple(k for k, v in REGISTRY.items() if v[1])
# A system that moves or reads another's block needs that system on: the flow moves the condition block, and
# a sheet's injuries are written inside it (`current.condition.injuries`).
NEEDS = {"condition_flow": ("condition",), "body": ("condition_flow",), "injuries": ("condition",)}

# The block each switchable system owns on a sheet, and its empty value. `arc` owns none: its OFF is
# only its mover, because what it already moved lives in the temperament, which stays.
_BLOCKS = {"condition": ("current", "condition", dict),
           "wounds":    ("baseline", "wounds", list),
           "attitude":  ("current", "toward", dict),
           "body":      ("baseline", "body", dict)}
# The drivers index `current.condition` directly, so an off condition is emptied even where the sheet never
# wrote one; every other off block is emptied only where it exists - a system that ships OFF must not add a
# block to the sheets of a book that never mentioned it (gate body-exertion).
_ALWAYS = ("condition",)


def defaults():
    """The systems a book runs when it declares nothing -> frozenset."""
    return frozenset(k for k, v in REGISTRY.items() if v[0])


def for_book(world):
    """The systems this book runs -> frozenset of ids. Refuses a declaration it cannot honour, by code."""
    decl = (world or {}).get("systems") if isinstance(world, dict) else None
    if decl is None:
        return defaults()
    if not isinstance(decl, dict):
        raise RecordError("SYSTEMS_NOT_A_MAP",
                          "world.systems must be a map of system name -> true/false, got %r" % type(decl).__name__)
    on = set(defaults())
    for name, val in decl.items():
        if name not in REGISTRY:
            raise RecordError("SYSTEMS_UNKNOWN", "world.systems names %r, which is not an engine system; the systems "
                              "are %s" % (name, ", ".join(sorted(REGISTRY))))
        if not isinstance(val, bool):
            raise RecordError("SYSTEMS_VALUE_NOT_BOOL", "world.systems.%s must be true or false, got %r" % (name, val))
        if not REGISTRY[name][1] and val is False:
            raise RecordError("SYSTEMS_NOT_SWITCHABLE", "world.systems.%s cannot be switched off yet; the switchable "
                              "systems are %s" % (name, ", ".join(SWITCHABLE)))
        (on.add if val else on.discard)(name)
    for name in sorted(on):
        unmet = [n for n in NEEDS.get(name, ()) if n not in on]
        if unmet:
            raise RecordError("SYSTEMS_NEEDS_UNMET", "world.systems runs %s but switches off %s, which it needs"
                              % (name, ", ".join(unmet)))
    return frozenset(on)


def declared(world):
    """True when the book runs a set that DIFFERS from the defaults; then each beat records the set it ran,
    so a replay knows. A book that says nothing - or lists every default as it is - records nothing, and
    writes exactly the rows it wrote before this gate."""
    return for_book(world) != defaults()


def strip(char, enabled):
    """Empty the block of every switched-off system on this sheet -> the char (mutated). Identity when
    every system that owns a block is on."""
    for name, (tier, key, kind) in _BLOCKS.items():
        if name not in enabled and (name in _ALWAYS or key in (char.get(tier) or {})):
            char.setdefault(tier, {})[key] = kind()
    return char


def authored_for_off(char, enabled):
    """-> [system names] whose block this sheet authors although the book switched them off (the pre-run
    check warns: it will do nothing)."""
    return [name for name, (tier, key, _kind) in _BLOCKS.items()
            if name not in enabled and ((char.get(tier) or {}).get(key))]
