"""condition.py — energy and stress that MOVE (the `condition_flow` system).

WHY THIS EXISTS (gate condition-flow, 2026-09-22). A character's `current.condition` - `energy` and
`allostatic_load` - sets the memory budget (`gate._energy_budget`) and the actor's line about how much
they have left (`direction.direct_condition`), and nothing ever moved it: the authoring blueprint said so
("Nothing anywhere writes condition.energy"). The owner ruled how it should move:

  C3a  the ENGINE carries energy from scene to scene, AND a scene can override it;
  C3b  what drains it is emotional load, time passing and physical exertion (exertion arrives with
       gate body-exertion, weighed against each character's strength - `body.py`).

The system is OFF by default (`systems.REGISTRY`): a book switches it on in its world note. With it off,
the sheet's condition stays where the author (or the last scene's director) put it, exactly as before.

THE ARITHMETIC, one step per cause, each read from something the log already holds - so the condition
fold (`mood_fold.replay`) re-derives every cached condition from the same causes (hard rule 2):

  a beat     energy -= TIME_SPEND x its minutes + IMPACT_SPEND x its impact (the receipt's own total,
             `state.receive`; the speaker only - a bystander's beat costs only its minutes);
             load   += LOAD_GAIN x its minutes x how far the character's worst stress path stands above
             STRESS_FLOOR at the beat's end (the mood the turn committed).
  an opening (`between`) what the character's last scene left unspent (`owed`) is awake time, costed as a beat
             with no impact; then their own gap follows the standard day - `opening` rests each night hour (the
             energy deficit closes as 1 - exp(-minutes / REST_TAU), the load eases as exp(-minutes / LOAD_TAU))
             and each day hour is awake time; see THE GAP BETWEEN below (the owner's ruling D2 replaced the
             first version, which rested the whole gap).
  a scene    may state how worn someone ARRIVES, in words, after the opening's rest - the director
             states the state AT the opening (`apply_declared`; the cfg's `condition` list, pinned whole
             in scene_cfgs, which is where the replay reads it back).

THE NUMBERS - START values, each with where it came from and what would prove it wrong:
  IMPACT_SPEND 0.2    [DERIVED] measured on the recorded chronicle (33 beats, scratchpad impact census,
                      2026-09-22): per-beat impact median 0.046, p90 0.096; the hardest scene's hardest-hit
                      character summed 1.24 in 15 story-minutes. At 0.2 that scene costs about one stage-line
                      band (0.25) and a typical scene (~0.35) about a third of one. FALSIFIER: a live scene in
                      which a character starting fresh falls two bands on less than 1.0 of summed impact.
  TIME_SPEND   0.6 / 960 per minute [START] an ordinary waking day (16 hours) with nothing hard in it takes
                      a fresh character from the top band to the second-lowest. FALSIFIER: a character
                      resting in the chair all afternoon reading as worn thin.
  LOAD_GAIN    0.3 / (960 x 0.5) [START] a full waking day spent at the TOP of a stress path adds 0.3 of
                      load; an hour of it adds under 0.02 - load is the slow wear of chronic stress
                      (relevancy-gate.md), not a beat's spike. FALSIFIER: load that moves visibly within
                      one scene.
  STRESS_FLOOR 0.5    [START] the ladder's middle: below it a stress path is a feeling, above it the body's
                      stress response. The stress paths are WARINESS, DISPLEASURE and DEFLATION (fear,
                      anger, grief - the three the stress literature ties to wear).
  REST_TAU     360 min [START] a night (8 hours) closes three quarters of the deficit; a day, all of it;
                      a two-hour break, a quarter. FALSIFIER: a character who slept reading as worn.
  LOAD_TAU     3 days [START] wear eases over days of rest, not hours.

THE RESERVES (gate energy-reserves, the owner's ruling D1, 2026-09-22): "mental energy and physical are
separate but also come from the same source. Something like a shared pool but with reserves for each. A person
can never use all energy for one type of activity." For a book that runs `body` - the only one with two kinds of
drain - `split` gives each sheet a MIND reserve and a BODY reserve beside the shared pool (a fifth of a full tank
each, the same for everyone; the owner confirmed). Thinking and feeling (a beat's impact) draw the shared pool,
then the mind's reserve, never the body's; physical effort (`body.exert`) the shared pool, then the body's
reserve, never the mind's; waking time the shared pool, then both reserves evenly. Rest refills each store
toward full on the same curve, so the TOTAL rests exactly as the single pool did. `energy` stays the sheet's one
number and the sum of the three; memory reads `mind_view`, and the actor's line reads both (`direction`). A
condition without the reserve keys is the single pool, byte for byte as before.

THE GAP BETWEEN (gate gap-day-and-night, the owner's ruling D2, 2026-09-22): "we have standard logic, anything
written can supersede but no mention is standard. So if a character was resting that must be stated otherwise if
its day they were awake." `between` measures each character's OWN gap - from the end of the last scene they were
in (`clock.presence_end`) to this opening - and walks it in order: every NIGHT hour (22:00 to 06:00) is rest, every
day hour awake; a scene's `condition` entry {char, gap: rested | awake} supersedes. A POV cut of minutes is minutes
awake, and time off the page in someone else's scene is lived. Off-page waking builds no stress: the mood off the
page is not known. A character's first appearance in a run applies nothing - their sheet is their state.

Deterministic, stdlib + engine imports only, no LLM, no randomness.
"""
from __future__ import annotations

__layer__ = "engine"

import math

from .records import RecordError

WAKING_DAY_MINUTES = 960.0
TIME_SPEND = 0.6 / WAKING_DAY_MINUTES
IMPACT_SPEND = 0.2
STRESS_PATHS = ("WARINESS", "DISPLEASURE", "DEFLATION")
STRESS_FLOOR = 0.5
LOAD_GAIN = 0.3 / (WAKING_DAY_MINUTES * 0.5)
REST_TAU = 360.0
LOAD_TAU = 3 * 1440.0

# THE DIRECTOR'S WORDS -> the engine's numbers (never a float from the author; attachments.hold_of's shape).
# Energy words sit inside the four stage-line bands (direction._COND) so the word the director writes is
# the band the actor is told, with no load: spent < .25 <= tired < .50 <= steady < .75 <= fresh.
ENERGY_WORDS = {"spent": 0.15, "tired": 0.40, "steady": 0.65, "fresh": 0.95}
GAP_WORDS = ("rested", "awake")        # what a scene may say a character did with the gap before it
NIGHT_FROM, NIGHT_UNTIL = 22 * 60, 6 * 60  # the standard night, minutes of the day [START - the owner's standard]
STRESS_WORDS = {"calm": 0.05, "tense": 0.30, "strained": 0.55, "frayed": 0.80}


def _clamp(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def _span(value, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise RecordError("CONDITION_SPAN_NOT_NUMERIC", "condition: %s must be a number >= 0, got %r" % (what, value))
    return float(value)


def _pair(condition):
    """(energy, load) of a condition the flow may move; refuses one it cannot."""
    if not isinstance(condition, dict):
        raise RecordError("CONDITION_NOT_A_DICT", "condition must be a dict, got %s" % type(condition).__name__)
    missing = [k for k in ("energy", "allostatic_load") if k not in condition]
    if missing:
        raise RecordError("CONDITION_KEYS_MISSING", "the condition flow moves energy AND allostatic_load; this "
                          "condition lacks %s (the readers would each assume a different value)" % ", ".join(missing))
    return float(condition["energy"]), float(condition["allostatic_load"])


def require(char):
    """Refuse, before the first beat, a sheet the flow cannot move -> the char."""
    _pair((char.get("current") or {}).get("condition"))
    return char


def stress(mood):
    """How far the worst stress path stands above the floor -> [0, 1 - STRESS_FLOOR]."""
    mood = mood or {}
    return max(0.0, max(float(mood.get(p, 0.0)) for p in STRESS_PATHS) - STRESS_FLOOR)


RESERVE = 0.2                 # each reserve's full size, a share of a full tank - "a fifth" (owner-confirmed START)
_SHARED_FULL = 1.0 - 2 * RESERVE


def has_reserves(condition):
    return isinstance(condition, dict) and "mind_reserve" in condition and "body_reserve" in condition


def split(condition):
    """Give a condition its two reserves -> a NEW condition. They are the last energy to go: full while the
    total allows, else half of it each. A condition that has them already is returned as it is."""
    if has_reserves(condition):
        return dict(condition)
    energy, _load = _pair(condition)
    r = min(RESERVE, energy / 2.0)
    return dict(condition, mind_reserve=r, body_reserve=r)


def _stores(c):
    m, b = float(c["mind_reserve"]), float(c["body_reserve"])
    return max(0.0, float(c["energy"]) - m - b), m, b


def _take(store, owed):
    t = min(store, owed)
    return store - t, owed - t


def draw(condition, amount, kind):
    """Spend `amount` of one kind - "mind", "body" or "awake" -> a NEW condition. The shared pool pays first,
    then the kind's own reserve; waking time, once the shared pool is gone, draws both reserves evenly. A kind
    never touches the other's reserve. Without reserves the single pool pays, as it always has."""
    if not has_reserves(condition):
        energy, _load = _pair(condition)
        return dict(condition, energy=_clamp(energy - amount))
    s, m, b = _stores(condition)
    s, owed = _take(s, amount)
    if kind == "mind":
        m, _left = _take(m, owed)
    elif kind == "body":
        b, _left = _take(b, owed)
    else:                                  # awake: both reserves evenly, each giving what it has
        m, rest_m = _take(m, owed / 2.0)
        b, rest_b = _take(b, owed / 2.0 + rest_m)
        m, _left = _take(m, rest_b)
    return dict(condition, energy=_clamp(s + m + b), mind_reserve=m, body_reserve=b)


def mind_view(condition):
    """What the mind has left, 0..1 (full is 1): the shared pool and the mind's reserve. Without reserves, the
    energy itself (absent reads full, as the memory budget always has)."""
    if not has_reserves(condition):
        return float(condition.get("energy", 1.0))
    s, m, _b = _stores(condition)
    return _clamp((s + m) / (1.0 - RESERVE))


def body_view(condition):
    """What the body has left, 0..1: the shared pool and the body's reserve. Without reserves, the energy."""
    if not has_reserves(condition):
        return float(condition.get("energy", 1.0))
    s, _m, b = _stores(condition)
    return _clamp((s + b) / (1.0 - RESERVE))


def spend(condition, minutes, impact=0.0, mood=None, scale=1.0):
    """One beat's cost -> a NEW condition dict (the other keys kept). `impact` is the receipt's total
    (the speaker's; 0 for a bystander); `mood` the one the beat committed, for the load. `scale` multiplies
    the waking-time cost: 1 / the body's capacity when the book runs `body` (gate body-exertion), else 1."""
    _energy, load = _pair(condition)
    minutes, impact = _span(minutes, "minutes"), _span(impact, "impact")
    cond = draw(condition, TIME_SPEND * minutes * float(scale), "awake")     # waking time: the shared pool
    cond = draw(cond, IMPACT_SPEND * impact, "mind")                        # what the beat did to them
    return dict(cond, allostatic_load=_clamp(load + LOAD_GAIN * minutes * stress(mood)))


def opening(condition, gap, owed=0.0, mood=None, scale=1.0):
    """An opening -> a NEW condition: the last scene's unspent minutes are awake time (costed at `scale`, as
    `spend`), then the declared gap is rest. `gap` None or 0 rests nothing."""
    cond = spend(condition, _span(owed or 0.0, "owed"), 0.0, mood, scale)
    gap = _span(gap or 0.0, "gap")
    energy, load = _pair(cond)
    k = math.exp(-gap / REST_TAU)
    if has_reserves(cond):                 # each store toward full on one curve: the total rests as before
        s, m, b = _stores(cond)
        s, m, b = _SHARED_FULL - (_SHARED_FULL - s) * k, RESERVE - (RESERVE - m) * k, RESERVE - (RESERVE - b) * k
        return dict(cond, energy=_clamp(s + m + b), mind_reserve=m, body_reserve=b,
                    allostatic_load=_clamp(load * math.exp(-gap / LOAD_TAU)))
    return dict(cond, energy=_clamp(1.0 - (1.0 - energy) * k),
                allostatic_load=_clamp(load * math.exp(-gap / LOAD_TAU)))


def hours(start, end):
    """The minutes from `start` to `end` (absolute, from day 1 00:00), in order -> [("night" | "day", minutes)]."""
    out, t, end = [], float(start), float(end)
    while t < end:
        mod = t % 1440.0
        night = mod >= NIGHT_FROM or mod < NIGHT_UNTIL
        edge = (t - mod) + (NIGHT_FROM if not night else (NIGHT_UNTIL if mod < NIGHT_UNTIL else 1440.0 + NIGHT_UNTIL))
        stop, kind = min(end, edge), ("night" if night else "day")
        if out and out[-1][0] == kind:
            out[-1] = (kind, out[-1][1] + stop - t)
        else:
            out.append((kind, stop - t))
        t = stop
    return out


def between(condition, end, at, owed=0.0, mood=None, scale=1.0, stated=None):
    """A character's own gap -> a NEW condition. What their last scene declared and did not spend is awake time
    (with the mood they left it in); then the gap from that scene's `end` to this opening's `at`: `stated`
    "rested" rests all of it, "awake" keeps them up through all of it, and nothing stated walks it hour by hour -
    night rests, day is awake."""
    if stated is not None and stated not in GAP_WORDS:
        raise RecordError("CONDITION_WORD_UNKNOWN", "a gap is one of %s, got %r" % (", ".join(GAP_WORDS), stated))
    cond = spend(condition, _span(owed or 0.0, "owed"), 0.0, mood, scale)
    gap = _span(float(at) - float(end), "gap")
    if stated == "rested":
        return opening(cond, gap)
    if stated == "awake":
        return spend(cond, gap, 0.0, None, scale)
    for kind, minutes in hours(end, at):
        cond = opening(cond, minutes) if kind == "night" else spend(cond, minutes, 0.0, None, scale)
    return cond


def stated_gaps(entries):
    """A scene cfg's `condition` list -> {char: gap word} for the entries that say what the gap was."""
    return {str(d["char"]): str(d["gap"]).lower() for d in (entries or ()) if isinstance(d, dict) and "gap" in d}


def declaration_errors(entries, cast):
    """-> [(code, message)] for a scene cfg's `condition` list; lint_scene reports every one, and
    `apply_declared` raises the first."""
    if entries is None:
        return []
    if not isinstance(entries, list):
        return [("CONDITION_DECLARATION_MALFORMED", "condition: must be a list of {char, energy?, stress?, gap?} declarations")]
    errs = []
    for d in entries:
        if not isinstance(d, dict) or not d.get("char") or not ({"energy", "stress", "gap"} & set(d)):
            errs.append(("CONDITION_DECLARATION_MALFORMED",
                         "condition: %r is not a {char, energy?, stress?, gap?} declaration naming at least one" % (d,)))
            continue
        if str(d["char"]) not in set(cast):
            errs.append(("CONDITION_DECLARATION_MALFORMED", "condition: %r is not in this scene's cast" % d["char"]))
        for key, table in (("energy", ENERGY_WORDS), ("stress", STRESS_WORDS), ("gap", GAP_WORDS)):
            if key in d and str(d[key]).lower() not in table:
                errs.append(("CONDITION_WORD_UNKNOWN", "condition: %s %r is not one of %s" % (key, d[key], ", ".join(table))))
    return errs


def apply_declared(chars, entries):
    """The director's statement of how each named cast member ARRIVES -> the ids it set (sorted). `chars` is
    the scene's cast {id: sheet}. Applied after the opening's rest. Only the named keys move."""
    errs = declaration_errors(entries, chars)
    if errs:
        msg = "; ".join(m for _c, m in errs)
        if errs[0][0] == "CONDITION_WORD_UNKNOWN":
            raise RecordError("CONDITION_WORD_UNKNOWN", msg)
        raise RecordError("CONDITION_DECLARATION_MALFORMED", msg)
    done = set()
    for d in entries or ():
        cond = chars[str(d["char"])].setdefault("current", {}).setdefault("condition", {})
        if "energy" in d:
            cond["energy"] = ENERGY_WORDS[str(d["energy"]).lower()]
            if has_reserves(cond):             # the stated whole, re-split with the reserves last to go
                cond["mind_reserve"] = cond["body_reserve"] = min(RESERVE, cond["energy"] / 2.0)
        if "stress" in d:
            cond["allostatic_load"] = STRESS_WORDS[str(d["stress"]).lower()]
        done.add(str(d["char"]))
    return sorted(done)
