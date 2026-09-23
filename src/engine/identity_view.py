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
from .records import RecordError   # rule 6's bad-input type
from . import heritable as _her
from . import concepts as _concepts    # THE one parse of a genotype word


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
    # SYNTAX, NOT PRESSURE. `voice.md:12` defines this axis as "hedges <-> declaratives" — a fact
    # about sentence form. It was written as conduct ("you press a point until it is answered",
    # "you take the room and hold it"), which states a position on DISPLEASURE's supervision axis;
    # the top phrase sat around phrases-rage 0.70. A voice phrase must hold at every one of the 92
    # rungs, because voice is the instrument and the path is the pressure on it. A man who does not
    # qualify what he says is still that man when he is furious and when he is bored.
    "assertiveness": ("you hedge what you say, and leave yourself a way out of it",
                      "you say it plainly, and let it stand where it falls",
                      "you do not qualify anything you say",
                      "you speak in flat declaratives, and do not offer them for agreement"),
    "agency":        ("things happen to you and you work out where that leaves you",
                      "you can move some of it and not the rest",
                      "you expect the outcome to answer to what you do",
                      "you treat every outcome as yours to have caused"),
}
_SCALAR_FALLBACK = ("very little of this", "some of this",
                    "a good deal of this", "this above most things")

# WHERE THEY REST — the authored rest word per path (`baseline.temperament[path].rest`, a
# character-design choice beside the voice since 2026-09-10). Rendered under `disposition`
# beside the trait sentences, because that is what it is: who they are on an ordinary day. The
# two lowest rests ('quiet', 'low') have no phrase on purpose — an unremarkable resting point is
# not self-knowledge. Keyed [path][word]. Split out of the allele table when the rest cell left
# the genotype; the phrases are the same writing, unmeasured.
_REST_PHRASES = {
    "WARINESS": {"raised": "some part of you is always listening for trouble",
              "high":   "you live braced, and have for as long as you remember"},
    "STIRRING": {"raised": "there is always something you are half reaching for",
              "high":   "you are never quite at rest; something always has your attention"},
    "DISPLEASURE": {"raised": "there is a low irritation in you most days",
              "high":   "you are easily put on edge and rarely fully off it"},
    "GOODWILL": {"raised": "you are warm to people before they have earned it",
              "high":   "caring for someone is your resting state, not a decision"},
    "DEFLATION": {"raised": "there is a sadness under you that ordinary days do not lift",
              "high":   "you carry a weight most people never notice you carrying"},
    "DISTASTE": {"raised": "much of what people do sits badly with you",
              "high":   "you are hard to please and quick to turn from what fails you"},
    "RECEPTIVITY": {"raised": "you are open to being pleased by ordinary things",
              "high":   "you walk into most rooms already glad"},
    "SELF-REGARD": {"raised": "you think well of yourself without needing to be told",
              "high":   "you carry yourself as someone who matters, and expect it to be noticed"},
    "LEVITY": {"raised": "you are quick to take an opening when one comes, and the room is lighter for it",
              "high":   "you are rarely wholly in earnest; the frame is where you live"},
}

# Genotype cells are already words, but they are ENGINE words (a gain, a half-life factor), and
# the law is about raw stats, not digits alone. Rendered as reactivity rather than configuration,
# one line per path and cell. 'typical' has no phrase on purpose: an unremarkable cell is not
# self-knowledge. Keyed [path][cell][word]. Rebuilt 2026-09-10 with the per-path genotype; the
# primitive-era phrases that still fit were carried, the rest are new writing in the same
# register and unmeasured.
_ALLELE_PHRASES = {
    "WARINESS": {
        "hit":  {"low": "danger has to be close before you feel it",
                 "elevated": "you feel a threat before others name it",
                 "high": "you are afraid before you know why"},
        "hold": {"brief": "once the danger passes, it is gone from you",
                 "long": "a fright stays in your hands after your head has let it go",
                 "lasting": "you do not stop watching the door for days"},
    },
    "STIRRING": {
        "hit":  {"low": "you wait to be moved",
                 "elevated": "you reach for the next thing",
                 "high": "stillness costs you more than doing"},
        "hold": {"brief": "a want, unanswered, lets go of you quickly",
                 "long": "what you have set your mind on, you keep circling",
                 "lasting": "you do not stop wanting a thing because it is out of reach"},
    },
    "DISPLEASURE": {
        "hit":  {"low": "it takes a great deal to make you angry",
                 "elevated": "your temper is close to the surface",
                 "high": "anger arrives before judgement does"},
        "hold": {"brief": "your anger is gone as fast as it came",
                 "long": "you cool slowly, and everyone near you knows it",
                 "lasting": "you keep a grievance the way other people keep a tool"},
    },
    "GOODWILL": {
        "hit":  {"low": "you hold people at arm's length without meaning to",
                 "elevated": "you attach to people quickly",
                 "high": "you cannot hold someone loosely"},
        "hold": {"brief": "your fondness needs feeding or it thins",
                 "long": "once you have taken to someone, it takes a great deal to undo",
                 "lasting": "you do not stop caring for people who have stopped deserving it"},
    },
    "DEFLATION": {
        "hit":  {"low": "a loss lands on you softly",
                 "elevated": "a loss goes deeper in you than it looks",
                 "high": "loss goes all the way down"},
        "hold": {"brief": "you grieve quickly and come back",
                 "long": "sorrow stays with you past the point others expect",
                 "lasting": "you do not recover from losses; you learn to walk with them"},
    },
    "DISTASTE": {
        "hit":  {"low": "little disgusts you",
                 "elevated": "you feel a wrongness in things before you can say what it is",
                 "high": "what revolts you, revolts you completely"},
        "hold": {"brief": "your distaste does not outlast the thing that caused it",
                 "long": "once a thing has sickened you, it stays spoiled",
                 "lasting": "you do not come back from contempt"},
    },
    "RECEPTIVITY": {
        "hit":  {"low": "it takes a great deal to delight you",
                 "elevated": "small good things reach you",
                 "high": "joy takes you over when it comes"},
        "hold": {"brief": "a pleasure passes through you and is gone",
                 "long": "a good thing stays with you into the next day",
                 "lasting": "you can live for weeks on one bright hour"},
    },
    "SELF-REGARD": {
        "hit":  {"low": "praise and slight both slide off you",
                 "elevated": "how you are seen reaches you more than you let on",
                 "high": "a slight to your standing lands like a blow"},
        "hold": {"brief": "your pride heals fast",
                 "long": "a wound to your standing closes slowly",
                 "lasting": "you never quite forget who saw you brought low"},
    },
    "LEVITY": {
        "hit":  {"low": "an opening has to be pointed out to you",
                 "elevated": "a joke reaches you before the point does",
                 "high": "give you a frame and you are inside it at once"},
        "hold": {"brief": "the game ends the moment the room needs you",
                 "long": "a good bit stays with you into the evening",
                 "lasting": "once you are in, it takes a great deal to bring you back out"},
    },
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
            raise RecordError("DIRECTION_VALUE_NOT_IN_UNIT_INTERVAL",
                "direction: %s is %r — outside [0,1], so it is not a weight this layer can band. "
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
        raise RecordError("DIRECTION_PACKET_NOT_AN_OBJECT", "direction: stable must be a dict")
    out = dict(stable)

    traits = stable.get("traits")
    if isinstance(traits, dict):
        out["disposition"] = {
            k: _phrase(_TRAIT_PHRASES.get(k), (v or {}).get("mean", 0.5), _TRAIT_FALLBACK)
            for k, v in traits.items() if isinstance(v, dict) and "mean" in v}
        out.pop("traits", None)      # variability is a sampling parameter, not self-knowledge

    temper = stable.get("temperament")
    if isinstance(temper, dict):
        # The rest WORD per path, said as a disposition beside the trait sentences (owner,
        # 2026-09-10: temperament is a character design question). `scene._rest_words` sends
        # only words, never the seeded mean; a word with no phrase (quiet, low) renders nothing.
        disp = out.get("disposition")
        if not isinstance(disp, dict):
            disp = out["disposition"] = {}
        for path, row in temper.items():
            if path.startswith("_") or not isinstance(row, dict):
                continue
            phrase = _REST_PHRASES.get(path, {}).get(_her.word(row.get("rest"), default="quiet"))
            if phrase:
                disp["%s at rest" % path.lower()] = phrase
        out.pop("temperament", None)

    geno = stable.get("genotype")
    if isinstance(geno, dict):
        # THE one parse (`heritable.word`); this line was the fifth independent copy of it.
        # An authored NUMBER in a cell has no phrase, so it renders nothing — a number is not
        # self-knowledge either, and hard rule 5 forbids it reaching the prompt.
        said = {}
        for path, cell in geno.items():
            if path.startswith("_") or not isinstance(cell, dict):
                continue
            for axis, v in cell.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    continue
                phrase = _ALLELE_PHRASES.get(path, {}).get(axis, {}).get(_her.word(v))
                if phrase:
                    said["%s %s" % (path.lower(), axis)] = phrase
        out["how you are built"] = said
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
        out["drives"] = d

    wounds = stable.get("wounds")
    if isinstance(wounds, list):
        # WHAT HAS MARKED YOU (gate three, 2026-09-11): engine wounds, said as a person knows a
        # scar — what it is about (the concept's gloss, never its id), how it takes them (the
        # intensity banded through `_WOUND`), what happened, what sets it off. The PATH is the
        # engine's key and is not self-knowledge; it is dropped here.
        marks = []
        for w in wounds:
            if not isinstance(w, dict) or not w.get("concept"):
                continue
            row = {"about": _concepts.gloss(str(w["concept"]))}
            if w.get("what happened"):
                row["what happened"] = w["what happened"]
            row["how it takes you"] = _phrase(_WOUND, w.get("intensity", 0.0))
            if w.get("what sets it off"):
                row["what sets it off"] = list(w["what sets it off"])
            marks.append(row)
        if marks:
            out["what has marked you"] = marks
        out.pop("wounds", None)

    # Anything the specific renderers above did not reach — an authored field the engine never
    # specified — is banded by name rather than dropped or refused. See `_say_scalars`.
    return _say_scalars(out)


def _said(item, num_key, said_key, table):
    """One authored {name, <weight>} dict -> the same dict with the weight said as a phrase.
    Every OTHER key is carried through: an authored field with no renderer must not vanish."""
    if not isinstance(item, dict):
        return item
    out = {k: v for k, v in item.items() if k != num_key}
    # AN ABSENT WEIGHT IS SILENCE, NOT A MIDDLE ONE. This defaulted a missing key to 0.5 and banded
    # it into a sentence, so a field nobody authored came back as a conviction the character then
    # acted on — "it catches you sometimes" for a wound with no intensity. Fabricating is worse than
    # either leaking or dropping: a leak is visible and a drop is absent, but an invented middle
    # reads exactly like an authored one. Found 2026-09-06 when the prefix stopped shipping the
    # rate fields and the renderer filled them back in.
    if num_key in item:
        out[said_key] = _phrase(table, item[num_key])
    return out


def direct_goals(goals):
    """volatile.goals -> the same list with `urgency` said as a phrase."""
    if not isinstance(goals, list):
        raise RecordError("DIRECTION_LIST_PACKET_NOT_A_LIST", "direction: goals must be a list")
    # AN ABSENT URGENCY IS SILENCE, NOT A MIDDLE ONE — the same rule as `_said` above, and this
    # site was missed when that one was fixed on 2026-09-06. Defaulting to 0.5 banded a weight
    # nobody authored into "something you mean to get to", which reads to the actor exactly like a
    # weight someone did author. Every goal on the four real books carries an urgency, so this was
    # latent rather than firing — but the prefix stopped shipping the standing goals' weights that
    # same day, which is precisely how a latent fabricator becomes a live one.
    out = []
    for g in goals:
        if not isinstance(g, dict):
            out.append(g)
            continue
        said = {"goal": g.get("goal")}
        if "urgency" in g:
            said["how much"] = _phrase(_URGENCY, g["urgency"])
        out.append(said)
    return out


def direct_percepts(percepts):
    """volatile.percepts -> the same list with `fidelity` said as a phrase.

    How WELL you caught a thing is exactly the sort of state an actor should feel rather than read.
    """
    if not isinstance(percepts, list):
        raise RecordError("DIRECTION_LIST_PACKET_NOT_A_LIST", "direction: percepts must be a list")
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
