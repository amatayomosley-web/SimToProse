"""identity_view.py — the STABLE identity prefix, said in words.

Split out of `direction.py` (2026-08-22) because the two halves have different LIFETIMES, which is
the same seam this project uses everywhere else: `direction.py` renders the VOLATILE tiers — affect,
condition, edges, sureness, recomputed every beat — while this renders the STABLE prefix, built once
per character from fixed + baseline. Keeping them in one module also pushed it past the 500-line
rule, but the lifetime split is the reason, not the line count.

Everything here obeys the same law: `design.md` — "The LLM never sees raw stats." The guard is
`tests/test_no_digits.py`, and `_say_scalars` makes it true by construction rather than by a test
that has to anticipate every field.
"""
from .direction import _EDGE_BANDS, _band, _check_num
from .errors import EngineError

# ---------------------------------------------------------------------------
# THE IDENTITY SURFACES — the other half of the law
#
# `design.md` says "The LLM never sees raw stats", and CLAUDE.md makes it hard rule 5. It held for
# the four surfaces above and nowhere else: `prompt.py` json.dumps'd the stable prefix, the goals
# and the percepts, so trait means, every worth-menu weight, the regard map, goal urgency, wound
# intensity and percept fidelity all reached the actor as decimals. Measured on one fixture:
# thirteen distinct floats in the prompt. `scene.py:_strip_notes` stated the old position outright —
# "The substrate (numbers, structure) stays".
#
# These renderers keep the STRUCTURE (the model already parses that shape reliably across every run
# in the repo) and replace only the values; changing the container at the same time would confound a
# quality regression with a format one. INTEGERS are untouched — a year, an age, a count of days are
# prose, not engine stats.
# ---------------------------------------------------------------------------

# Per-facet HEXACO characterisation. Not "markedly high" — that is a stat wearing a word. Four bands
# per facet, on the same 0.25/0.55/0.80 edges the rest of this module uses.
_TRAIT_PHRASES = {
    "emotionality":      ("things land on you lightly and pass",
                          "you feel things and set them down again",
                          "you feel things hard and they stay a while",
                          "you feel everything hard and it stays with you"),
    "agreeableness":     ("you hold a grudge and see no reason not to",
                          "you forgive slowly and remember anyway",
                          "you give people the benefit of the doubt",
                          "you forgive before you have decided to"),
    "extraversion":      ("you say less than you think and prefer it that way",
                          "you speak when spoken to",
                          "you take up room in a conversation",
                          "you fill a room and do not notice doing it"),
    "conscientiousness": ("you start things and drift off them",
                          "you finish what matters and let the rest go",
                          "you finish what you start",
                          "you cannot leave a thing half-done"),
    "openness":          ("you want what you already know",
                          "you try a new thing when it is put in front of you",
                          "you go looking for what you have not seen",
                          "the unfamiliar pulls you before the familiar does"),
    "honesty_humility":  ("you take what you can get and call it fair",
                          "you bend a rule when it costs no one you know",
                          "you keep to your word when it costs you",
                          "you would not take an advantage you had not earned"),
}
_TRAIT_FALLBACK = ("very little of this", "some of this",
                   "a good deal of this", "this above most things")

# Intensity for anything authored as a weight-with-a-name: goals, wounds, the regard map.
_URGENCY = ("in the back of your mind", "something you mean to get to",
            "pressing on you", "the thing you would drop everything for")
_WOUND = ("an old scar you rarely feel", "it catches you sometimes",
          "it takes hold of you when it comes", "it takes you over")
_REGARD = ("you do not count them as people",
           "you hold them cheap and it shows",
           "you take them as they come",
           "you would answer for them as you would for your own")

# Percept clarity — replaces the raw `fidelity` float.
_FIDELITY = ("you half-caught it", "you caught the shape of it",
             "you saw it clearly", "you saw it plainly, no doubt in it")

# NAMED SCALARS an author may put on a sheet. The four below were found on real books the first
# time this renderer met one; `_SCALAR_FALLBACK` covers anything else so a novel authored field
# degrades to a banded phrase instead of taking the book down.
_SCALARS = {
    "priority":      ("you would drop this before anything else",
                      "it matters, and it yields to the rest",
                      "it outranks most of what you want",
                      "nothing you want outranks this"),
    "satisfaction":  ("nothing about this is settled",
                      "you have made a start and it is not enough",
                      "this is mostly where you want it",
                      "this one is handled and you can leave it alone"),
    "assertiveness": ("you leave the space for someone else to fill",
                      "you say your piece once and let it stand",
                      "you press a point until it is answered",
                      "you take the room and hold it"),
    "agency":        ("things happen to you and you work out where that leaves you",
                      "you can move some of it and not the rest",
                      "you expect the outcome to answer to what you do",
                      "you treat every outcome as yours to have caused"),
}
_SCALAR_FALLBACK = ("very little of this", "some of this",
                    "a good deal of this", "this above most things")

# Genotype alleles are already words, but they are ENGINE words (the gain on a primitive's
# sensitivity), and the law is about raw stats, not digits alone. Rendered as reactivity rather than
# configuration. 'typical' has no phrase on purpose: an unremarkable allele is not self-knowledge.
_ALLELE_PHRASES = {
    "threat_reactivity":      {"low": "danger has to be close before you feel it",
                               "elevated": "you feel a threat before others name it",
                               "high": "you are afraid before you know why"},
    "approach_drive":         {"low": "you wait to be moved",
                               "elevated": "you reach for the next thing",
                               "high": "stillness costs you more than doing"},
    "affiliation_attachment": {"low": "you hold people at arm's length without meaning to",
                               "elevated": "you attach to people quickly",
                               "high": "you cannot hold someone loosely"},
    "anger_proneness":        {"low": "it takes a great deal to make you angry",
                               "elevated": "your temper is close to the surface",
                               "high": "anger arrives before judgement does"},
    "effortful_control":      {"low": "what you feel, you feel for a long time",
                               "elevated": "you put a feeling down when you decide to",
                               "high": "you can set anything aside and mean it"},
    "sensitivity":            {"low": "most things wash over you",
                               "elevated": "you register more than others do",
                               "high": "nothing is small to you"},
}


def _phrase(table, v, fallback=None):
    return (table or fallback)[_band(_check_num("value", v), _EDGE_BANDS)]


_WORTH_FAMILIES = ("schwartz", "moral_foundations", "needs")
_NEUTRAL_WEIGHT = 0.5        # state._relevance reads a missing key as this; so does an authored 0.5


def _rank(model, top=4, bottom=3):
    """The worth menu -> (what they will not trade away, what they weigh little).

    Ranked, not banded, and pooled ACROSS the three families rather than ranked within each.
    `reference-species-prior.md` is explicit that for these scales "the ORDER is the replicated
    finding; the spacing is fitted to this scale" — so the rank IS the information. Pooling matters:
    ranked per-family, a character who authored only three Schwartz values had all three returned as
    things they would not trade away, including `power` at 0.15. One menu, one ranking.

    Only weights that DEPART from neutral are ranked at all. An authored 0.5 says "average", and
    `state._relevance` treats a missing key the same way, so listing it as held or slighted would
    invent a conviction the sheet does not claim.
    """
    if not isinstance(model, dict):
        return [], []
    items = []
    for family in _WORTH_FAMILIES:
        for k, v in (model.get(family) or {}).items():
            if isinstance(v, (int, float)) and abs(float(v) - _NEUTRAL_WEIGHT) > 1e-9:
                items.append((k.replace("_", " "), float(v)))
    if not items:
        return [], []
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    held = [k for k, v in items if v > _NEUTRAL_WEIGHT][:top]
    slight = [k for k, v in reversed(items) if v < _NEUTRAL_WEIGHT][:bottom]
    return held, slight


def _is_scalar(v):
    return isinstance(v, float) and not isinstance(v, bool)


def _say_scalars(obj, key="", path=""):
    """Recursively replace every remaining [0,1] scalar with a phrase, keyed by its FIELD NAME.

    The catch-all after the specific renderers have run. It exists because the first version of
    this module REFUSED any number it had no phrase for, and that refusal — correct for the engine's
    own fields — took down two real books on their FIRST contact with it: `goals[].priority`,
    `goals[].satisfaction`, `voice.assertiveness` and `orientation.agency` are all authored fields
    the engine never specified, and no author should have their book stop running because the
    direction layer lacks artisanal prose for a weight they invented.

    THE LAW IS "NO DIGITS", not "every field must be hand-phrased". A named scalar with no table
    gets a banded generic; the digit still never reaches the actor. What still REFUSES is a number
    outside [0,1] — that is not a weight, it is something else wearing a float, and guessing at it
    would be the silent-drop failure in a new place.
    """
    if isinstance(obj, dict):
        return {k: _say_scalars(v, k, "%s.%s" % (path, k) if path else str(k))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [_say_scalars(v, key, "%s[%d]" % (path, i)) for i, v in enumerate(obj)]
    if _is_scalar(obj):
        if not (0.0 <= obj <= 1.0):
            raise EngineError(
                "IDENTITY_VIEW_DIRECTION_OUTSIDE_WEIGHT_INVALID", "direction: %s is %r — outside [0,1], so it is not a weight this layer can band. "
                "It would reach the actor as a raw stat (design.md: 'The LLM never sees raw "
                "stats'). Give it a renderer, or keep it out of the identity prefix." % (path, obj))
        return _phrase(_SCALARS.get(key), obj, _SCALAR_FALLBACK)
    return obj


def direct_identity(stable):
    """The stable identity prefix -> the same SHAPE with every raw stat replaced by a phrase.

    Pure. Unknown keys pass through untouched, so persona, voice and provenance (all strings) are
    unchanged and a future field is not silently dropped.

    FAILS LOUD on any number it does not know how to say. That is the difference between a law and a
    comment: an earlier draft of this function REPLACED the blocks it understood and dropped
    everything else, so a field nobody had written a renderer for — `model.resolution_priority`,
    `goals[].satisfaction`, both real dead schema fields — vanished silently instead of leaking.
    Silent dropping is worse than leaking: the guard comes back green and the next authored field
    disappears with it. So unknown keys are CARRIED, and then the sweep below refuses the packet and
    names the path. A new numeric field is a five-minute phrase table, not a silent loss.
    """
    if not isinstance(stable, dict):
        raise EngineError("IDENTITY_VIEW_DIRECTION_STABLE_NOT_A_DICT", "direction: stable must be a dict")
    out = dict(stable)

    traits = stable.get("traits")
    if isinstance(traits, dict):
        out["disposition"] = {
            k: _phrase(_TRAIT_PHRASES.get(k), (v or {}).get("mean", 0.5), _TRAIT_FALLBACK)
            for k, v in traits.items() if isinstance(v, dict) and "mean" in v}
        out.pop("traits", None)      # variability is a sampling parameter, not self-knowledge

    geno = stable.get("genotype")
    if isinstance(geno, dict):
        said = {k: _ALLELE_PHRASES.get(k, {}).get(str(v).split()[0].lower()) for k, v in geno.items()}
        out["how you are built"] = {k: v for k, v in said.items() if v}
        out.pop("genotype", None)

    model = stable.get("model")
    if isinstance(model, dict):
        held, slight = _rank(model)
        worth = {}
        if held:
            worth["you will not trade these away"] = held
        if slight:
            worth["these weigh little with you"] = slight
        regard = model.get("regard")
        if isinstance(regard, dict) and regard:
            worth["how you hold each people"] = {
                g: _phrase(_REGARD, v) for g, v in regard.items() if isinstance(v, (int, float))}
        for k, v in model.items():           # anything with no renderer is CARRIED, not dropped —
            if k not in _WORTH_FAMILIES and k != "regard":     # the sweep below then refuses it
                worth[k] = v
        out["what you weigh"] = worth
        out.pop("model", None)

    drives = stable.get("drives")
    if isinstance(drives, dict):
        d = dict(drives)
        if isinstance(drives.get("goals"), list):
            d["goals"] = [_said(g, "urgency", "how much", _URGENCY) for g in drives["goals"]]
        if isinstance(drives.get("fears_wounds"), list):
            d["fears_wounds"] = [_said(w, "intensity", "how it takes you", _WOUND)
                                 for w in drives["fears_wounds"]]
        out["drives"] = d

    # Anything the specific renderers above did not reach — an authored field the engine never
    # specified — is banded by name rather than dropped or refused. See `_say_scalars`.
    return _say_scalars(out)


def _said(item, num_key, said_key, table):
    """One authored {name, <weight>} dict -> the same dict with the weight said as a phrase.
    Every OTHER key is carried through: an authored field with no renderer must not vanish."""
    if not isinstance(item, dict):
        return item
    out = {k: v for k, v in item.items() if k != num_key}
    out[said_key] = _phrase(table, item.get(num_key, 0.5))
    return out


def direct_goals(goals):
    """volatile.goals -> the same list with `urgency` said as a phrase."""
    if not isinstance(goals, list):
        raise EngineError("IDENTITY_VIEW_DIRECTION_GOALS_NOT_A_LIST", "direction: goals must be a list")
    return [{"goal": g.get("goal"), "how much": _phrase(_URGENCY, g.get("urgency", 0.5))}
            if isinstance(g, dict) else g for g in goals]


def direct_percepts(percepts):
    """volatile.percepts -> the same list with `fidelity` said as a phrase.

    How WELL you caught a thing is exactly the sort of state an actor should feel rather than read.
    """
    if not isinstance(percepts, list):
        raise EngineError("IDENTITY_VIEW_DIRECTION_PERCEPTS_NOT_A_LIST", "direction: percepts must be a list")
    out = []
    for p in percepts:
        if not isinstance(p, dict):
            out.append(p)
            continue
        q = {k: v for k, v in p.items() if k != "fidelity"}
        if "fidelity" in p:
            q["how well you caught it"] = _phrase(_FIDELITY, p["fidelity"])
        out.append(q)
    return out
