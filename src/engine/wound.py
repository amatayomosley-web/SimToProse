"""wound.py — the wound tier's MOVER: what decides that a scar deepens or eases.

The other four pieces shipped first, deliberately, so this one could be shown to work:

  the store    `wound_deltas` (schema v10) — signed changes, append-only, DB-enforced
  the reader   `ledger.wound_deltas_for`
  the fold     `levers.replay_wound_deltas` — deltas onto the sheet-authored value
  the wire     `levers.scale_to_wounds`     — a catalog row scaled by what remains

This module is the decision. It writes nothing and reads no database; it returns a number.

WHY A SCAR CHANGES, AND THE DOC LINE THIS REVISES
`docs/arc-engine.md` Open Question #2 asks whether durable diffs soften over the arc or change
only via new events, and leans time: "very slow heal toward the pre-event baseline". This answers
event-FIRST, time-second, and the reason is that a character could otherwise sit in the mill for
twenty years and the wall would weigh exactly the same, while a character who walked into the thing
every week would be unchanged by it. Both readings are wrong about people. Time alone is not
nothing, though — natural recovery after a trauma is real and fast for a fresh wound and then
plateaus — so erosion survives as a weak second rule with a floor.

THE LAW: THE INTENSITY IS THE PREDICTION
A wound's intensity is the character's expectation of how bad this class of moment gets. So the
learning signal is the error between what the moment actually delivered and what the wound
predicted — the same law `bonds.observe` runs for a relationship edge, whose docstring puts it as
"the current edge IS the expectation". A wound is that shape of quantity pointed at a class of
moments instead of a person, so it gets the same rule rather than a second one invented for it.

  observed = the event's dimension on the wound's OWN class
  error    = observed - intensity
  error > 0   the moment was worse than feared   -> the wound DEEPENS
  error < 0   the moment was better than feared  -> the wound EASES

This is why walking into the thing and finding it survivable is what heals a scar, and why nothing
heals while the character avoids the cue: with no trial there is no error, and with no error there
is no learning. It also self-limits — as the intensity falls toward what the world actually
delivers, each further trial pays less — so diminishing returns are arithmetic rather than a rule.

TWO GAINS, AND NEITHER IS A THRESHOLD
Resilience scales how much a trial consolidates. It does NOT decide whether a trial counts. Nothing
switches at a boundary here; `arc.assess`'s 0.70 growth fork is a different mechanism in a
different tier and this module never reads it.

  deepening  gain (1 - resilience)   depleted and alone, a bad night marks you harder
  easing     gain resilience          rested and held, a good night consolidates

RETREAT IS NOT A FAILED TRIAL — IT IS NO TRIAL
If the cue appears and the character withdraws, no outcome is observed, so nothing is computed and
nothing is written. That falls out of the arithmetic rather than needing a rule, and it is the
correct reading: avoidance PRESERVES a fear rather than deepening it. Only staying and being
overwhelmed deepens, which is the `observed > intensity` branch.

Deterministic, stdlib only, no LLM, no randomness (CLAUDE.md hard rules 3 and 4). The variance is
the character's own: resilience moves with load and bonds scene to scene, and the error moves with
the wound's current value, so the same circumstance lands differently in chapter 3 and chapter 12.
"""
from __future__ import annotations

from .decay_law import relax          # the one law; see its header
from .facets import _mentions, _normalize   # ONE word-boundary matcher; a second copy is the duplicate defect
from .records import RecordError   # rule 6's bad-input type

# The two learning rates ARE `bonds._ALPHA_NEG` and `_ALPHA_POS`, restated here rather than imported
# because they mean something different in this tier and should be free to diverge under probe.
# Their ORDER is what matters and it carries two independent justifications: the negativity bias
# that pair was calibrated for, and the finding that re-acquiring a fear after extinction is faster
# than the extinction was. A chapter of progress can go in one night, which is how it reads.
_A_DEEPEN = 0.30
_A_EASE   = 0.12

# A wound below this floor renders as "an old scar you rarely feel" (`direction._EDGE_BANDS` puts
# the lowest band edge at 0.25). Healing to exactly zero would delete the character's history;
# healing to here makes it a mark rather than a wound. An author may raise it per wound —
# `permanence: 1.0` is a wound that never eases at all, which is a strong authorial statement the
# engine can express for free.
_DEFAULT_PERMANENCE = 0.15

# Which appraisal dimension a wound is ABOUT. Most wounds are threat-shaped; a bereavement is not.
_DEFAULT_CLASS = "threat"

# Time, with nothing firing. Deliberately ONE regime, not two: every wound on disk is authored
# backstory, which is consolidated by definition, and the fast fresh-wound regime is unreachable
# until something creates a wound at runtime. Per declared elapsed unit — the same caller-declared
# unit `bonds.drift` takes, so a director who says a winter passed moves both tiers by one story.
# Above `bonds._RETENTION["debt"]` (0.99), the most persistent thing the relationship tier holds:
# a scar outlasts a debt.
_RETENTION = 0.995


def _class_of(wound):
    """Which appraisal dimension this wound is about. Authored, defaulted, never guessed from prose."""
    return str((wound or {}).get("class_dim") or _DEFAULT_CLASS)


def _floor_of(wound):
    """The authored minimum this wound can ease to. `permanence: 1.0` never eases."""
    try:
        return max(0.0, min(1.0, float((wound or {}).get("permanence", _DEFAULT_PERMANENCE))))
    except (TypeError, ValueError):
        raise RecordError("WOUND_PERMANENCE_RANGE",
            "wound: permanence must be a number in [0,1], got %r — `lint_book.py` checks this "
            "before a run" % ((wound or {}).get("permanence"),))


def fires(wound, triggers):
    """Does this wound's own trigger list match what the character PERCEIVED?

    `triggers` is the PerceptSet-derived SURFACES from `gate.perceived_surfaces` — the raw phrasings
    the character perceived, not the shredded word bag and not the ground-truth event text. The
    blueprint instructs authors to write triggers as PHRASES ("a child with fever"), and the shredded
    bag drops the connective words, so a phrase could never match it. MEASURED on this repo's own
    fixture: a wound authored exactly as documented never fired. That distinction is the whole guard: the gate's docstring states "you cannot be
    triggered by what you didn't perceive", and `bonds.py` goes further and imports the gate's own
    DCs so it cannot drift from them. `levers._row_active` does NOT — it matches raw `ctx["text"]`,
    so a catalog row can fire on something withheld from the character. This module declines to
    copy that; a wound must never move on an event its owner did not see.

    Word boundaries, via the ONE matcher `facets` already owns: a raw substring test fires a wound
    keyed on a short word against any longer word containing it, which is a scar going off at
    random. A multi-word phrase keeps substring semantics because it cannot collide by accident.
    """
    # EACH SURFACE SEPARATELY, never one joined blob. Joining lets a phrase match across the seam
    # between two unrelated percepts — "a child with fever" matching a room that contains a child
    # and, separately, a fever elsewhere. A trigger must be satisfied by ONE thing the character
    # actually saw.
    surfaces = [str(t) for t in (triggers or ()) if str(t).strip()]
    if not surfaces:
        return False
    joined = " ".join(surfaces)          # single-word triggers may match anywhere in the set
    for t in ((wound or {}).get("trigger") or []):
        t = str(t).strip()
        if not t:
            continue
        if " " in _normalize(t):
            if any(_mentions(t, s) for s in surfaces):
                return True
        elif _mentions(t, joined):
            return True
    return False


def trial(wound, dims, resilience, triggers):
    """One beat -> the signed change in this wound's intensity. Returns 0.0 when nothing applies.

    Returns a NUMBER. The caller decides whether to record it; this module touches no state, so a
    healing trial can never reach a temperament baseline — the double-count rule holds by
    construction rather than by a guard. (Deepening SHOULD write both: a mauling both deepens the
    dog-scar and raises tonic vigilance, and `arc.assess` owns that second write independently.
    Easing must write only the wound, because extinction is specific to its cue and its context.)
    """
    if not isinstance(wound, dict):
        raise RecordError("WOUND_NOT_A_DICT", "wound.trial: wound must be a dict, got %r" % type(wound).__name__)
    if "intensity" not in wound:
        raise RecordError("WOUND_INTENSITY_MISSING",
            "wound.trial: wound %r carries no `intensity` — `lint_book.py` requires one on every "
            "wound, because the intensity IS the prediction this compares against"
            % (wound.get("id") or wound.get("wound") or wound.get("fear")))
    if not fires(wound, triggers):
        return 0.0
    observed = (dims or {}).get(_class_of(wound))
    if observed is None:
        return 0.0            # the cue appeared but the beat says nothing about this wound's class
    try:
        observed = float(observed)
        now = float(wound["intensity"])
        r = max(0.0, min(1.0, float(resilience)))
    except (TypeError, ValueError):
        raise RecordError("WOUND_TRIAL_INPUT_NOT_NUMERIC", "wound.trial: observed/intensity/resilience must be numbers, got %r / %r / %r"
                         % (observed, wound.get("intensity"), resilience))
    error = observed - now
    if error == 0.0:
        return 0.0
    step = (_A_DEEPEN * error * (1.0 - r)) if error > 0 else (_A_EASE * error * r)
    floor = _floor_of(wound)
    dest = now + step
    if step < 0.0:
        # THE FLOOR STOPS AN EASE; IT MUST NOT CAUSE A DEEPENING. A single clamp into [floor, 1.0]
        # looks right and is not: an unhealable wound (`permanence: 1.0`) sitting at 0.95 clamps
        # UP to 1.0 and the reassuring encounter that should have done nothing makes it worse.
        # Found by walking an arc rather than reading the line. An easing trial may move a wound
        # down to the floor and no further, and may never move it up.
        dest = min(now, max(dest, floor))
    else:
        dest = min(1.0, dest)
    return dest - now


def erode(wound, elapsed):
    """Time passing with the wound untouched -> a small negative change, never past the floor.

    The weak second rule. Event-driven change is the first; this exists because a wound nothing ever
    reopens should still fade to a mark over a saga, and because the alternative — a wound frozen
    forever unless walked into — reads as machinery rather than a person.

    `elapsed` is the DIRECTOR'S declared unit, the same one `bonds.drift` takes, so one line in a
    scene cfg moves the relationship tier and this one by the same story-time.
    """
    if not isinstance(wound, dict) or "intensity" not in wound:
        return 0.0
    try:
        e = max(0.0, float(elapsed))
    except (TypeError, ValueError):
        raise RecordError("WOUND_ELAPSED_NOT_NUMERIC", "wound.erode: elapsed must be a number, got %r" % (elapsed,))
    if e == 0.0:
        return 0.0
    now = float(wound["intensity"])
    floor = _floor_of(wound)
    if now <= floor:
        return 0.0
    return relax(now, floor, _RETENTION, e) - now
