"""wound.py — the wound tier: engine-owned scars keyed (concept, path), minted, moved, folded.

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

GATE THREE, 2026-09-11 — WOUNDS LEFT THE CHARACTER SHEET. Owner: *"wounds are a multiplier, so
move it out of character sheet and make it an engine script"* and *"link wounds to the emotion
paths, the wound multiplies that linked emotion."* A wound is now ENGINE STATE at
`baseline.wounds`: one entry per (concept, path) per character, holding the live intensity that
`connection.for_about` reads as the character's investment in that concept on that path. It is
never authored as prose. It comes into being two ways, and both are recorded:

  at creation   `from_profile_row` — the formative library's wound rows
                (`data/formative_profiles.json`, each naming a registry concept) become wounds
                when `scripts/composition_pass.py` composes the character, source `profile:<id>`
  mid-story     `mint` — a DURABLE beat the seat READ at one of a path's top two rungs, that
                path bound to a concept, mints the wound (intensity = the reading's height) for that (concept, path), source `run:<turn>`,
                written as an append-only `wound_minted` row (schema v26) and folded on resume.

THE LINK IS IDENTITY. A later beat about the same concept on the same path finds the wound by
string equality on `concept:<id>` (`fires`); nothing in the engine reads prose to decide. The one
semantic step — this beat is about SICKNESS — is the appraiser seat's or the actor's self-tag's,
validated against the closed registry (`concepts.py`) and committed to the chronicle before
anything computes from it. Deterministic given the log, which is hard rule 2's promise everywhere.

The four older pieces still stand under the new shape:
  the store    `wound_deltas` (schema v10) — signed changes, append-only, DB-enforced
  the reader   `ledger.wound_deltas_for`
  the fold     `fold` here (was `levers.replay_wound_deltas`) — mints, then deltas, onto the sheet
  the wire     `connection.for_about` — the receipt is scaled by what remains
The decision below (`trial`, `erode`) writes nothing and reads no database; it returns a number.
"""
from __future__ import annotations

from .decay_law import relax          # the one law; see its header
from .facets import _mentions, _normalize   # ONE word-boundary matcher; a second copy is the duplicate defect
from .records import RecordError, PATHS   # rule 6's bad-input type
from .state import _DIM_TO_PATH       # the one table _PATH_CLASS is derived from (2026-09-19)
from . import concepts as _concepts

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

# Time, with nothing firing. Deliberately ONE regime, not two. A wound can now be created at
# runtime (`mint`, 2026-09-11) so the fast fresh-wound regime IS reachable — and it is still NOT
# built: its rate would be a design number with no measurement behind it, and the owner's rule of
# 2026-09-10 is a conservative start tuned in runs. A minted wound erodes at the same slow rate as
# a library one; if real runs show fresh scars fading too slowly, that is the knob. Per declared
# elapsed unit — the same caller-declared unit `bond_rest.drift` takes. Above `bond_rest._RETENTION["debt"]`
# (0.99), the most persistent thing the relationship tier holds: a scar outlasts a debt.
_RETENTION = 0.995

# MINTING — a START. A path bound to a concept that the seat READ at one of this many top rungs,
# on a durable beat, scars (intensity = the reading's height). Two rungs: the top band alone is
# rarely named, and a scar that only the amok can earn is decoration.
_MINT_RUNGS_FROM_TOP = 2
def _class_from_dims():
    """`_PATH_CLASS`, DERIVED from `state._DIM_TO_PATH` instead of hand-written (2026-09-19, gate
    heights-price-arc). For each path, the dimension with the LARGEST POSITIVE push onto it is the
    class a wound on that path predicts against (`trial` compares the beat's dimension to the
    intensity) — CLAUDE.md's "if you are about to write a list that mirrors something the code
    already knows, derive it," applied to the dict this replaces.

    A path with no positive push anywhere maps to None, honestly, rather than to an invented
    dimension name: RECEPTIVITY and SELF-REGARD are in `PATHS` but in no dimension's push list at
    all — `state._DIM_TO_PATH`'s own comment says why ("those two paths are structurally reachable
    and never move"). `trial`'s dims fallback reads `(dims or {}).get(_class_of(wound))`, and
    `.get(None)` is already None, so a None class falls through to that function's honest 0.0
    rather than being guessed at.

    Computed ONCE at import into the same module constant `_PATH_CLASS`, so `_class_of` and every
    other reader below are unchanged.
    """
    best = {}                                          # path -> (dim, push), the largest so far
    for dim, pushes in _DIM_TO_PATH.items():
        for path, push in pushes:
            if push > best.get(path, (None, 0.0))[1]:
                best[path] = (dim, push)
    return {path: best.get(path, (None, 0.0))[0] for path in PATHS}


_PATH_CLASS = _class_from_dims()


def class_for_path(path):
    """The appraisal dimension a wound on `path` predicts against."""
    return _PATH_CLASS.get(str(path), _DEFAULT_CLASS)


def _class_of(wound):
    """Which appraisal dimension this wound is about: from its PATH (engine wounds), else authored,
    else the default. Never guessed from prose."""
    w = wound or {}
    if w.get("class_dim"):
        return str(w["class_dim"])
    if w.get("path"):
        return class_for_path(w["path"])
    return _DEFAULT_CLASS


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
    # IDENTITY FIRST (gate three): a beat ABOUT this wound's concept fires it, by string equality
    # on the about the driver resolved — the link the owner asked for, with no fuzzy step. The
    # phrase match below stays for the cue-in-the-room case (the child is here; nobody names
    # sickness) and for library wounds carrying their trigger phrases.
    if isinstance(triggers, dict):
        about = triggers.get("about")
        surfaces_in = triggers.get("surfaces") or ()
        if about and (wound or {}).get("concept") and str(about) == _concepts.PREFIX + str(wound["concept"]):
            return True
        triggers = surfaces_in
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


def about_for(wound, readings):
    """The `about` this wound's identity route should see on this beat -> "concept:<id>" or None.

    A wound is keyed CONCEPT@PATH. It is reached, by `fires`' identity route, when a reading on the
    wound's OWN path is about the wound's OWN concept — the link the owner asked for, with no fuzzy
    step. Both halves matter: a DEFLATION reading about eviction is not the WARINESS scar about
    eviction, and a WARINESS reading about a person is not a WARINESS reading about eviction.

    WHY THIS EXISTS (gate `wounds-and-memory-inputs`, 2026-09-22). Both drivers handed `fires` the
    beat's resolved SUBJECT as `about` — always a person — so the identity route could never match on
    a live beat, while the emotion seat was naming the wound's concept all along: measured, 12 readings
    on a live run carried a wound's concept, two of them on the wound's own path. The concept lives
    in the readings, so the cue is built from the readings, here, once, for both drivers.
    """
    concept = str((wound or {}).get("concept") or "").strip()
    path = str((wound or {}).get("path") or "").strip().upper()
    if not concept or not path:
        return None
    ref = _concepts.PREFIX + concept
    for r in readings or ():
        if str(getattr(r, "about", "") or "") == ref and str(getattr(r, "path", "") or "").upper() == path:
            return ref
    return None


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
    # THE OBSERVATION (Phase 3, spec section 5 step 7): when the seat READ this wound's path this
    # beat, the reading's height IS what the moment delivered on that path — the cue dict carries
    # `heights` {path: height}. Otherwise the event seat's dimension on the wound's class, as before.
    observed = None
    if isinstance(triggers, dict) and isinstance(triggers.get("heights"), dict) and (wound or {}).get("path"):
        observed = triggers["heights"].get(str(wound["path"]))
    if observed is None:
        # A wound on a path no dimension prices (RECEPTIVITY, SELF-REGARD) has `_class_of(wound)
        # is None` (see `_class_from_dims`). `.get(None)` on the dims dict is always None, so this
        # falls straight through to the `return 0.0` below instead of raising or matching some
        # other dimension by accident — the observation is honestly absent, not guessed at.
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

    `elapsed` is the DIRECTOR'S declared unit, the same one `bond_rest.drift` takes, so one line in a
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


# ---------------------------------------------------------------------------------------------
# GATE THREE: the wound as ENGINE STATE — its shape, its two births, its fold, its identity
# ---------------------------------------------------------------------------------------------

def wound_id(concept, path):
    """The one id a (concept, path) wound has, for every store that keys on it."""
    return "%s@%s" % (str(concept), str(path))


def _check(w):
    """Refuse a malformed engine wound by name. Returns the dict."""
    if not isinstance(w, dict):
        raise RecordError("WOUND_NOT_A_DICT", "wound: expected a wound dict, got %r" % type(w).__name__)
    if str(w.get("concept", "")) not in _concepts.REGISTRY:
        raise RecordError("WOUND_CONCEPT_UNKNOWN", "wound %r names concept %r, not in the registry" % (w.get("id"), w.get("concept")))
    if str(w.get("path", "")) not in PATHS:
        raise RecordError("WOUND_PATH_UNKNOWN", "wound %r names path %r" % (w.get("id"), w.get("path")))
    v = w.get("intensity")
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0.0 <= float(v) <= 1.0):
        raise RecordError("WOUND_INTENSITY_RANGE", "wound %r intensity %r is not a number in [0,1]" % (w.get("id"), v))
    return w


def make(concept, path, intensity, source, text="", triggers=(), permanence=None):
    """A wound dict in the one shape every reader takes. `id` is derived, never authored."""
    w = {"id": wound_id(concept, path), "concept": str(concept), "path": str(path),
         "intensity": round(float(intensity), 4), "source": str(source),
         "text": str(text or ""), "trigger": [str(t) for t in (triggers or ()) if str(t).strip()]}
    if permanence is not None:
        w["permanence"] = float(permanence)
    return _check(w)


def from_profile_row(row, profile_id):
    """A formative-library catalog row that names a concept -> the wound it stands for, or None
    for a row that is not a wound (the library's vocation/passion/conditioning rows stay levers).

    The row's magnitude was a multiplier on the float (x1.4 .. x2.5); the wound's intensity is an
    investment in [0,1]. Mapped linearly from the library's own range so its ORDER survives:
    x1.4 -> 0.40, x2.5 -> 0.95. A START, like every number in the library.
    """
    if not isinstance(row, dict) or not row.get("concept"):
        return None
    try:
        mag = float(row.get("magnitude", 1.0))
    except (TypeError, ValueError):
        return None
    lo, hi = 1.4, 2.5
    frac = max(0.0, min(1.0, (mag - lo) / (hi - lo)))
    intensity = round(0.40 + 0.55 * frac, 3)
    return make(row["concept"], row.get("lever"), intensity, "profile:%s" % profile_id,
                text=str(row.get("source", "")), triggers=(row.get("when") or {}).get("percept") or ())


def mint(char, heights, targets, durable, surfaces=(), text="", turn=None):
    """One beat -> the wounds it mints on this character: NEW (concept, path) pairs as wound dicts.
    Pure; writes nothing; the caller records the rows and folds them.

    THE RULE: on a DURABLE beat (the arc engine's own candidate test), every path the seat READ at
    one of its top `_MINT_RUNGS_FROM_TOP` rungs (`heights` = {path: the reading's height}) AND
    that is bound to a registry concept mints a wound on that (concept, path) if none exists.
    Intensity = the reading's height — what the moment delivered, the same quantity `trial`
    takes as its observation (a START). Triggers = the surfaces the character perceived on this
    beat, kept as the words the actor is told set it off; the LINK is the concept, never these.

    WHY THE READING AND NOT THE FLOAT (2026-09-11, found by the read-along stub): under the
    adopted globals one reading adds at most ~lambda to a path, so "the receipt leaves the path
    in its top rungs" is unreachable from a single beat by construction — the top is a
    sustained-readings property (test_genotype_balance E2). A scar is made by ONE moment.
    """
    from .rung_blocks import BANDS as _BANDS
    if not isinstance(char, dict):
        raise RecordError("WOUND_MINT_CHAR_NOT_A_DICT", "wound.mint: char must be a dict")
    if not durable:
        return []
    have = {str(w.get("id")) for w in ((char.get("baseline") or {}).get("wounds") or []) if isinstance(w, dict)}
    out = []
    for path in PATHS:
        about = (targets or {}).get(path)
        if not about or not _concepts.is_concept(about):
            continue
        h = (heights or {}).get(path)
        if h is None:
            continue
        cid = _concepts.id_of(about)
        wid = wound_id(cid, path)
        if wid in have:
            continue
        top = len(_BANDS[path])
        floor_of_top_rungs = float(_BANDS[path][top - _MINT_RUNGS_FROM_TOP][0])
        if float(h) < floor_of_top_rungs:
            continue
        out.append(make(cid, path, min(1.0, float(h)), "run:%s" % ("" if turn is None else turn),
                        text=str(text or "")[:200], triggers=surfaces))
    return out


def write_mints(con, run_id, turn, char_id, mints):
    """Log one turn's minted wounds -> rows written. NO TRANSACTION OF ITS OWN (see
    targets.write_binds: called inside Ledger.append_turn's transaction)."""
    import json as _json
    n = 0
    for w in (mints or []):
        w = _check(w)
        con.execute("INSERT INTO wound_minted (run_id, turn, char_id, wound_id, concept, path, intensity, "
                    "source, text, triggers) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, int(turn), str(char_id), w["id"], w["concept"], w["path"], float(w["intensity"]),
                     w.get("source", ""), w.get("text", ""), _json.dumps(w.get("trigger") or [])))
        n += 1
    return n


def mints_for(con, run_id, char_id):
    """Every wound this run minted on this character, in turn order -> [wound dict]."""
    import json as _json
    out = []
    for r in con.execute("SELECT wound_id, concept, path, intensity, source, text, triggers FROM wound_minted "
                         "WHERE run_id = ? AND char_id = ? ORDER BY turn, mint_id", (run_id, str(char_id))):
        out.append(make(r[1], r[2], r[3], r[4], text=r[5], triggers=_json.loads(r[6] or "[]")))
    return out


def fold(char, mints, deltas):
    """Fold the log onto the character: minted wounds join `baseline.wounds`, then signed deltas
    move intensities. Mutates and returns the list. ONE FUNCTION, called from every resume path
    (bonds.py records what hand-copied replays cost).

    STAMPS `_authored_intensity` before any delta, as `levers.replay_wound_deltas` did and for the
    same reason: the scale in `levers.scale_to_wounds` is intensity / authored. CLAMPS ONCE AFTER
    SUMMING, so the fold is order-independent.
    """
    if not isinstance(char, dict):
        raise RecordError("WOUND_MINT_CHAR_NOT_A_DICT", "wound.fold: char must be a dict")
    base = char.setdefault("baseline", {})
    wounds = base.setdefault("wounds", [])
    if not isinstance(wounds, list):
        raise RecordError("WOUND_LIST_NOT_A_LIST", "baseline.wounds must be a list, got %r" % type(wounds).__name__)
    have = {str(w.get("id")): w for w in wounds if isinstance(w, dict)}
    for m in (mints or []):
        m = _check(m)
        if m["id"] not in have:
            wounds.append(dict(m))
            have[m["id"]] = wounds[-1]
    from .levers import replay_wound_deltas       # THE one delta fold (sums first, clamps once)
    return replay_wound_deltas(wounds, deltas)
