"""compounds.py — the named emotions, as coordinates over the primitives.

`docs/emotion-basis.md` is normative: a PRIMITIVE is an emotion that cannot be derived from a
combination of other emotions; a COMPOUND is a coordinate over the primitives, each primitive
carrying its own TARGET.

This table is ENGINE-owned vocabulary, not character data. "Contempt" must mean the same shape for
every character or the word carries no information. What varies per character is which catalog rows
FIRE (`levers.py`), never what a name means.

Two directions, and the second is the point:

  compose(name, ...)   NAME  -> coordinate.   How an author says "give me contempt."
  recognise(vector)    COORD -> ranked names. What IS this state the engine just computed?

`recognise` is how the basis becomes checkable. Until an engine can name the vector it produced,
there is no way to ask whether the vector was right.

TARGETS ARE ROLES HERE, NOT VALUES. A definition says contempt aims RAGE and DISGUST at the same
object; WHICH object is per-instance and supplied at compose time. The roles:

  self          the character themselves            (shame, pride)
  self.act      a specific thing they did           (guilt, regret)
  object        who or what the state is about      (contempt, fear)
  beneficiary   on whose behalf it is felt          (indignation, jealousy)

THE HARD LINE (decision-engine.md:85) holds here too: naming a state is strictly a READ. This module
never chooses an action and must never gain the ability to.

A recipe may cite a primitive the basis does not have. That is an ERROR reported by validate(), not
a silent drop — the dominant defect in this repo is authored content that reaches nothing, and a
recipe quietly losing an ingredient would be that defect in a new place. DISGUST is deliberately
cited below while absent from PRIMARIES, so the case for the eighth primitive is made by
measurement rather than by argument.
"""
import math

from .records import PRIMARIES, admits_role
from .errors import EngineError

_ROLES = ("self", "self.act", "object", "beneficiary")

# name -> {primitive: (weight, role)}. Weights are SHAPES, not magnitudes: contempt at 0.4 and at
# 0.9 are the same state at different strengths, which is why similarity is cosine (below).
# NOTHING HERE IS CALIBRATED. These are authored shapes; separability() is what will falsify them.
COMPOUNDS = {
    # --- outward, at another party -------------------------------------------------
    "contempt":     {"RAGE": (0.35, "object"), "DISGUST": (0.55, "object")},
    "disdain":      {"RAGE": (0.20, "object"), "DISGUST": (0.45, "object"),
                     "PANIC_GRIEF": (0.15, "object")},
    "scorn":        {"RAGE": (0.45, "object"), "DISGUST": (0.50, "object")},
    "indignation":  {"RAGE": (0.50, "object"), "CARE": (0.40, "beneficiary")},
    "spite":        {"RAGE": (0.35, "object"), "DISGUST": (0.40, "object"),
                     "PLAY": (0.20, "object")},
    # FEAR is of THE LOSS — a prospect, an object. `emotion-basis.md`'s own recipe reads
    # "CARE(beloved) + RAGE(rival) + FEAR(the loss)"; the reflexive bind here was drift FROM that,
    # caught 2026-08-22 when `records.DIRECTEDNESS` gave the basis a way to say so.
    "jealousy":     {"CARE": (0.40, "beneficiary"), "RAGE": (0.35, "object"),
                     "FEAR": (0.35, "object")},
    "wariness":     {"FEAR": (0.35, "object"), "SEEKING": (0.25, "object")},

    # --- inward, at the self -------------------------------------------------------
    "shame":        {"PANIC_GRIEF": (0.50, "self"), "DISGUST": (0.45, "self")},
    "guilt":        {"PANIC_GRIEF": (0.40, "self.act"), "CARE": (0.45, "beneficiary")},
    "embarrassment": {"PANIC_GRIEF": (0.30, "self"), "DISGUST": (0.20, "self"),
                      "FEAR": (0.25, "object")},
    # SEEKING is reflexive (the basis licenses SEEKING-satisfied(self)); PLAY is not. The pleasure
    # is IN the deed, an object. That it is savoured rather than offered is COVERTNESS — a delivery
    # register, which this project removes from the basis rather than accommodating (`sarcastic`).
    "pride":        {"SEEKING": (0.45, "self"), "PLAY": (0.30, "object")},
    "self_loathing": {"DISGUST": (0.65, "self"), "PANIC_GRIEF": (0.30, "self")},

    # --- toward a bond -------------------------------------------------------------
    "love":         {"CARE": (0.50, "object"), "LUST": (0.25, "object"),
                     "PANIC_GRIEF": (0.20, "object")},
    "tenderness":   {"CARE": (0.55, "object"), "PLAY": (0.20, "object")},
    "devotion":     {"CARE": (0.60, "object"), "SEEKING": (0.25, "object")},
    "longing":      {"PANIC_GRIEF": (0.45, "object"), "LUST": (0.25, "object"),
                     "SEEKING": (0.25, "object")},

    # --- the plain states, for completeness of the read-back -----------------------
    "dread":        {"FEAR": (0.70, "object"), "SEEKING": (0.15, "object")},
    "grief":        {"PANIC_GRIEF": (0.75, "object")},
    "fury":         {"RAGE": (0.80, "object")},
    "resolve":      {"SEEKING": (0.60, "object"), "FEAR": (0.20, "object")},
    "delight":      {"PLAY": (0.60, "object"), "SEEKING": (0.30, "object")},
    "revulsion":    {"DISGUST": (0.80, "object")},

    # --- borrowed texture range -----------------------------------------------------
    # Mapped from a 58-state vocabulary authored independently for VOICE (measured 2026-08-22):
    # 15 of those were delivery qualities with no motivational content, 7 were that basis's own
    # primitives, 5 were intensity variants of another row. What remains is texture this basis had
    # no way to name. Semantic duplicates of rows above are deliberately NOT carried -- a second
    # name for one shape is the redundancy separability() exists to catch.
    "anxious":      {"FEAR": (0.40, "object"), "SEEKING": (0.30, "object"),
                     "PANIC_GRIEF": (0.20, "self")},
    "stressed":     {"FEAR": (0.30, "object"), "RAGE": (0.25, "object"),
                     "PANIC_GRIEF": (0.25, "self")},
    "broken":       {"PANIC_GRIEF": (0.60, "self"), "FEAR": (0.25, "object")},
    "bitter":       {"RAGE": (0.25, "object"), "PANIC_GRIEF": (0.35, "self"),
                     "DISGUST": (0.35, "object")},
    "cold":         {"PANIC_GRIEF": (0.30, "self"), "FEAR": (0.20, "object"),
                     "DISGUST": (0.25, "object")},
    "fierce":       {"RAGE": (0.60, "object"), "FEAR": (0.25, "object")},

    "excited":      {"SEEKING": (0.55, "object"), "PLAY": (0.35, "object")},
    "charming":     {"PLAY": (0.40, "object"), "SEEKING": (0.25, "object"),
                     "CARE": (0.25, "object")},
    "welcoming":    {"CARE": (0.35, "object"), "PLAY": (0.35, "object"),
                     "SEEKING": (0.20, "object")},
    "comforting":   {"CARE": (0.50, "object"), "PANIC_GRIEF": (0.20, "object")},
    "fond":         {"CARE": (0.40, "object"), "PLAY": (0.30, "object"),
                     "PANIC_GRIEF": (0.15, "object")},
    "warm":         {"CARE": (0.40, "object"), "PLAY": (0.20, "object"),
                     "PANIC_GRIEF": (0.25, "object")},
    "nostalgic":    {"PANIC_GRIEF": (0.35, "object"), "PLAY": (0.25, "object"),
                     "CARE": (0.25, "object")},

    # the condescension range -- the family this basis cannot express without DISGUST
    "mocking":      {"DISGUST": (0.40, "object"), "RAGE": (0.20, "object"),
                     "PLAY": (0.30, "object")},
    # `sarcastic` WAS here and is removed (2026-08-22, when DISGUST joined PRIMARIES and both
    # recipes went live for the first time). It scored cosine 0.996 to `mocking` — the same three
    # primitives, the same roles, magnitudes within 0.05 — which is inside the duplicate band, not
    # the 0.95-0.99 SHADE band `decision-engine.md` deliberately populates with contempt / disdain /
    # scorn. It is not a shade: sarcasm is a DELIVERY REGISTER, saying the opposite of what you
    # mean, and a person can be sarcastic while amused, furious, or fond. The feeling underneath is
    # mocking; how it is performed is the actor's job and the direction layer's, not the basis's.
    # The collision was invisible while DISGUST was missing, because both recipes were BLOCKED.
    "condescending": {"DISGUST": (0.45, "object"), "PLAY": (0.20, "object"),
                      "SEEKING": (0.15, "self")},
    "smug":         {"SEEKING": (0.35, "self"), "DISGUST": (0.30, "object"),
                     "PLAY": (0.25, "object")},
    "haughty":      {"SEEKING": (0.40, "self"), "DISGUST": (0.25, "object")},
    "passive_aggressive": {"RAGE": (0.30, "object"), "DISGUST": (0.30, "object"),
                           "PLAY": (0.25, "object")},
    "bored_contempt": {"DISGUST": (0.45, "object"), "PANIC_GRIEF": (0.20, "self")},
}


class CompoundError(EngineError):
    """A recipe broke the contract — named loudly, never coerced."""


def _vec(recipe):
    """recipe -> a dense weight vector over PRIMARIES, ignoring absent primitives."""
    return [float(recipe.get(p, (0.0, None))[0]) for p in PRIMARIES]


def _cosine(a, b):
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def validate():
    """-> {"ok", "blocked", "bad_role", "drift"} — the last being roles the BASIS disallows.

    A recipe citing a primitive PRIMARIES does not carry is BLOCKED, not silently truncated. This
    is the measurement that decides whether the basis needs an eighth element: if the blocked list
    is empty the seven suffice for this vocabulary; if a whole family is blocked on one missing
    primitive, that primitive is a requirement rather than an opinion.
    """
    ok, blocked, bad_role, drift = [], {}, {}, {}
    for name, recipe in sorted(COMPOUNDS.items()):
        missing = sorted({p for p in recipe if p not in PRIMARIES})
        roles = sorted({r for _w, r in recipe.values() if r not in _ROLES})
        if roles:
            bad_role[name] = roles
        # DRIFT — a role this recipe uses that the BASIS does not admit for that primitive
        # (records.DIRECTEDNESS). Reported, never auto-corrected: the recipes are authored and the
        # repair is an authoring decision, but the basis is upstream and gets to say a recipe is
        # wrong. This check is why the registry is enforceable rather than advisory.
        off = sorted("%s(%s)" % (p, r) for p, (_w, r) in recipe.items()
                     if p in PRIMARIES and not admits_role(p, r))
        if off:
            drift[name] = off
        if missing:
            blocked[name] = missing
        else:
            ok.append(name)
    return {"ok": ok, "blocked": blocked, "bad_role": bad_role, "drift": drift}


def compose(name, intensity=1.0, targets=None):
    """NAME -> a coordinate `{primitive: {"magnitude", "target", "role"}}`.

    intensity scales every weight (the shape is preserved — that is what makes it the same state
    at a different strength). `targets` maps a ROLE to a concrete id, e.g.
    {"object": "<an entity id>", "self": "<this character id>"}; an unsupplied role leaves target None, which is
    legitimate for a state whose object is not a party (dread of the dark).

    Raises CompoundError on an unknown name or a recipe citing a primitive the basis lacks.
    """
    if name not in COMPOUNDS:
        raise CompoundError("COMPOUND_NAME_UNKNOWN", "compose: unknown compound %r (known: %s)"
                            % (name, ", ".join(sorted(COMPOUNDS))))
    if not isinstance(intensity, (int, float)) or not (0.0 <= float(intensity) <= 1.0):
        raise CompoundError("COMPOUND_INTENSITY_RANGE", "compose: intensity must be a number in [0,1], got %r" % (intensity,))
    recipe = COMPOUNDS[name]
    missing = sorted({p for p in recipe if p not in PRIMARIES})
    if missing:
        raise CompoundError("COMPOUND_RECIPE_BLOCKED",
            "compose: %r requires primitive(s) %s which the basis does not carry. "
            "Either the recipe is wrong or the basis is incomplete — see docs/emotion-basis.md; "
            "this is reported rather than silently dropped." % (name, missing))
    targets = targets or {}
    out = {}
    for p, (w, role) in recipe.items():
        out[p] = {"magnitude": max(0.0, min(1.0, float(w) * float(intensity))),
                  "target": targets.get(role), "role": role}
    return out


def recognise(vector, top=3, floor=0.0):
    """A live affect (or effective) vector -> the table entries ranked by cosine similarity.

    Returns [(name, similarity)], longest-match-first, at most `top`, dropping anything below
    `floor`. Compounds the basis cannot express are skipped — they can never match.

    A RANKED list, never a single winner: ambiguity between two names is information (it says the
    basis cannot separate them) and collapsing it to one name would hide exactly what
    separability() exists to surface.
    """
    if not isinstance(vector, dict):
        raise CompoundError("COMPOUND_VECTOR_NOT_AN_OBJECT", "recognise: vector must be a dict, got %r" % type(vector).__name__)
    v = [float(vector.get(p, 0.0)) for p in PRIMARIES]
    scored = []
    for name, recipe in COMPOUNDS.items():
        if any(p not in PRIMARIES for p in recipe):
            continue
        s = _cosine(v, _vec(recipe))
        if s >= floor:
            scored.append((name, s))
    scored.sort(key=lambda t: (-t[1], t[0]))
    return scored[:top]


def _role_key(recipe):
    """The aboutness signature: which primitive points at which ROLE."""
    return tuple(sorted((p, r) for p, (_w, r) in recipe.items()))


def separability(threshold=0.95):
    """-> [(a, b, cosine)] for every expressible pair whose shapes are too close to tell apart.

    This is the confusion matrix from docs/emotion-basis.md's verification procedure, run
    deterministically with no model in the loop. A pair above `threshold` means the basis cannot
    distinguish two states the vocabulary treats as different — which is either a missing dimension
    or a redundant name, and the doc's failure table says which repair each implies.
    """
    names = [n for n, r in sorted(COMPOUNDS.items()) if all(p in PRIMARIES for p in r)]
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            # Two compounds with the same magnitudes but DIFFERENT role signatures are
            # different states -- pride is SEEKING+PLAY at the SELF, excitement is the same
            # shape at an OBJECT. Cosine alone scored those 1.000 and was wrong to.
            if _role_key(COMPOUNDS[a]) != _role_key(COMPOUNDS[b]):
                continue
            s = _cosine(_vec(COMPOUNDS[a]), _vec(COMPOUNDS[b]))
            if s >= threshold:
                out.append((a, b, s))
    out.sort(key=lambda t: -t[2])
    return out


def recipe_sum(name, intensity=1.0):
    """The compound's total weight — the IDENTITY DIAL.

    docs/emotion-basis.md, borrowed verbatim: how hard a state steers and how much of the person's
    resting self survives it are THE SAME NUMBER. A sum of 0.35 leaves 65% of who they ordinarily
    are; a sum of 1.0 erases it. Nothing else in this engine answers "how much of me survives this
    moment" — the decay rate answers a different question (how fast do I return) with a constant.
    """
    if name not in COMPOUNDS:
        raise CompoundError("COMPOUND_NAME_UNKNOWN", "recipe_sum: unknown compound %r" % (name,))
    return sum(w for w, _r in COMPOUNDS[name].values()) * float(intensity)


def blend(name, baseline, intensity=1.0, targets=None):
    """A compound ON A PERSON -> a FULL vector over every primitive.

        vector = recipe_magnitudes + (1 - sum) * baseline        [clamped to [0,1]]

    A recipe alone is a partial thing: it says what contempt IS and nothing about the rest of the
    person. This fills the remainder with their own resting level, so the result is always a whole
    character rather than an emotion floating free.

    Two consequences worth naming, both of which fall out rather than being coded:

      1. THE SAME RECIPE GIVES DIFFERENT VECTORS ON DIFFERENT PEOPLE. Contempt on a warm character
         and contempt on a cold one are not the same state, because 30% of each is still them.
         That is what lets one shared vocabulary carry any cast.
      2. INTENSITY AND IDENTITY-PRESERVATION ARE ONE DIAL. Halving intensity halves the sum, which
         raises the bleed — a faint contempt is mostly the person, a total one is mostly the
         emotion. No separate parameter, because they were never two things.

    baseline: {primitive: float} — the character's TEMPERAMENT MEANS (their resting level), not
    their current affect. Current affect is already a departure from rest; blending toward it would
    compound a deviation with itself.

    At sum >= 1.0 the bleed is zero: pure steering, the person erased. That is the source formula's
    own behaviour and it is right — a total emotion does erase you.
    """
    coord = compose(name, intensity, targets)
    if not isinstance(baseline, dict):
        raise CompoundError("COMPOUND_BASELINE_NOT_AN_OBJECT", "blend: baseline must be a dict, got %r" % type(baseline).__name__)
    total = sum(v["magnitude"] for v in coord.values())
    bleed = max(0.0, 1.0 - total)
    out = {}
    for p in PRIMARIES:
        mag = coord[p]["magnitude"] if p in coord else 0.0
        b = float(baseline.get(p, 0.0))
        out[p] = max(0.0, min(1.0, mag + bleed * b))
    return out
