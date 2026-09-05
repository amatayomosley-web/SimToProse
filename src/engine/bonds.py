"""bonds.py — the relationship tier: how one person's read of another MOVES.

Third tier beside `state.py` (affect, per beat) and `arc.py` (the durable self, per actor-turn).
This one runs **per WITNESS per turn**, and that cadence is the whole point.

`docs/relationships.md:5` — an edge is *A's belief about A↔B*, held by A. Before this module the only
edge writer was `arc.assess`, which runs on the SPEAKER (`scripts/direct.py:303`,
`scripts/scene.py:306`) and wrote `diff["relationships"][subject]` into the speaker's own dict. So
when A betrayed B, **A's** trust in B fell and B's edge never moved. Measured: 0.80 -> 0.7828 on the
betrayer, nothing on the victim. Edges were a passenger on an actor-scoped engine; relationships are
witness-scoped. Fixing the formula in place could not fix that — it needed a different loop.

THE UPDATE RULE, all four ingredients from `docs/relationships.md:26-29`:

  1. PREDICTION ERROR (:26). `Δ ∝ (observed − expected)`, and **the current edge IS the
     expectation**. That single choice buys the doc's own worked example for free: a betrayal by a
     trusted friend (expect 0.9, observe 0.0) moves nine times as far as the same act from a known
     schemer (expect 0.2, observe 0.0). It also self-limits — edges converge instead of running away.
  2. NEGATIVITY BIAS (:27). `_ALPHA_NEG > _ALPHA_POS` — trust arrives on foot and leaves on
     horseback. The old path had this exactly inverted (a resilient character's betrayal moved trust
     6× LESS than an equal kindness) because `arc.py`'s resilience buffer, which belongs on
     temperament scars, was being applied to the edge. Resilience does not appear in this module.
     Plus CLIFFS: some acts are a discontinuity, not a slope.
  3. SCORED BY THE PERCEIVER'S VALUES (:28). Magnitude scales by `state._relevance` — the same
     worth-menu machinery affect already uses. A loyalty-valuer is destroyed by a betrayal that a
     loyalty-indifferent witness barely registers, *including whether it is a cliff at all*.
  4. ATTRIBUTION (:29). A updates on why A thinks B did it. Accident and coercion damp; malice is
     full. Unknown reads as full — the naive attribution is intent, which is both the human default
     and the conservative choice (an untagged act behaves as it did before).

WHO SAYS WHAT. `docs/relationships.md:11` is three layers: events (objective) → perception
(per-character) → relationship-belief. The ACTOR's committed tags are layer one — `prompt.py:89`
already demands "what OBJECTIVELY happened". Each witness then computes their OWN delta from their
own values, their own expectation, their own attribution. No actor ever declares what someone else
should feel about them.

DEBT IS NOT A BELIEF, so it does not use the delta rule. Trust/affinity/respect are reads of a
person and converge on evidence; debt (`:18` "who owes whom") is a running account that accumulates.
Modelling it as convergence would mean a large favour to someone you already owe registers as
*nothing*, which is backwards.

Pure, deterministic, stdlib. No LLM (CLAUDE.md rule 3), no randomness (rule 4), no numbers to the
prompt (rule 5 — `direction.direct_edge` renders these).
"""
from .gate import PERCEPTION_DC_IDENTITY, PERCEPTION_DC_SUBTLE, _passes_check
from .records import RELATIONSHIP_AXES
from .state import _relevance
from .errors import EngineError

# --- Class-B calibration. Directions are prescribed by relationships.md; magnitudes are chosen
# starts, falsifiable by a run that reads as either glacial or hysterical. ---

_ALPHA_POS = 0.12          # learning rate on a POSITIVE surprise
_ALPHA_NEG = 0.30          # ... on a NEGATIVE one. That _ALPHA_NEG > _ALPHA_POS IS the negativity
                           #     bias (relationships.md:27) — the ratio, 2.5x, is the calibration.
_DEBT_RATE = 0.35          # debt accumulates at this fraction of severity (accountant, not believer)

# CLIFFS (relationships.md:27) — trust only. A cliff is an act so far past what the perceiver can
# absorb that the slope stops applying: one unforgivable thing, one discontinuous drop. Gated on
# RELEVANCE as well as severity, so the same act is a cliff for the loyalty-valuer and a slope for
# someone who does not weight loyalty — which is the point of scoring by values at all.
_CLIFF_SEVERITY = 0.80
_CLIFF_RELEVANCE = 0.60
_CLIFF_FLOOR = 0.15
_CLIFF_AXES = ("trust",)

# ATTRIBUTION damping (relationships.md:29). 'unknown' is FULL, not damped: absent an explanation
# people attribute to intent, and it also means an untagged act behaves exactly as before.
_ATTRIBUTION = {"malice": 1.0, "intent": 1.0, "unknown": 1.0,
                "negligence": 0.70, "coerced": 0.35, "accident": 0.15}

# CHARITY — how far a witness is willing to believe the actor's account of WHY.
#
# relationships.md:29 requires the perceiver's attribution to be able to diverge from the truth
# ("Tragic misunderstandings are first-class") but names no rule for HOW it diverges. This is the
# engine's answer, and it is an EXTENSION of the doc rather than a reading of it: a witness extends
# charity in proportion to how much they trust the actor. relationships.md:15 already defines trust
# as "do I rely on their word", and whether you believe someone's account of their own intent is
# that same question. At trust 1.0 the damping lands in full; at trust 0.0 none of it does and the
# act reads as fully intended whatever the actor says.
#
# The consequence is a feedback loop, and it is the point: low trust reads an accident as malice,
# which lowers trust further. That is how relationships actually fail, and it is falsifiable — a
# cast that spirals into mutual contempt from nothing means this curve is too steep.
_CHARITY_FLOOR = 0.15      # even a hated stranger gets this much benefit of the doubt

# Per-axis neutral point — what an edge means when nobody has authored one.
_NEUTRAL = {"trust": 0.5, "affinity": 0.5, "respect": 0.5, "debt": 0.0}

# DRIFT (relationships.md:30): retention per unit of elapsed time, toward the resting prior.
# "affinity fades faster than trust" is the doc's ordering; debt barely fades at all — a favour
# owed is not forgotten by the passage of a week.
_RETENTION = {"trust": 0.97, "affinity": 0.90, "respect": 0.95, "debt": 0.99}

# FALLBACK MAP — dimension -> [(axis, sign, weight)] — used when the actor's tags carry no explicit
# `social` block. Deliberately conservative:
#   * `threat` and `loss` move NOTHING. A turn tagged threat-with-subject-B is ambiguous between
#     "A menaced B" and "A and B are both in danger", and guessing wrong poisons the edge. Only an
#     explicit `social` block can say "I threatened them".
#   * `mastery` moves RESPECT — watching someone be good at a thing is how respect is earned, and
#     this is the first writer `respect` has ever had.
_DIM_AXES = {
    "social_violation": [("trust", -1.0, 1.0), ("respect", -1.0, 0.5)],
    "care_relevant":    [("affinity", +1.0, 1.0), ("trust", +1.0, 0.6)],
    "relief":           [("affinity", +1.0, 0.7), ("trust", +1.0, 0.3)],
    "mastery":          [("respect", +1.0, 1.0)],
}

# Axes that move only for the party the act was ABOUT, never for a bystander. You owe someone who
# helped YOU; watching them help a stranger raises your regard, not your debt.
_RECEIVED_ONLY = ("debt",)

# Which dimensions create debt when received (a kindness lands as an obligation).
_DEBT_DIMS = ("care_relevant", "relief")


def _clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def act_from_tags(tags, actor_id, witness_id):
    """One actor's committed tags -> the OBJECTIVE act, as it bears on ONE witness. None if nothing
    interpersonal happened, or if the witness IS the actor (nobody holds an edge to themselves).

    Returns {toward, observations {axis: observed 0..1}, severity, dominant, received, attribution}.
    `observations` come from the actor's explicit `social` block when present — which is the only way
    `respect` and `debt` can be addressed directly — and otherwise from `_DIM_AXES`.
    """
    if not isinstance(tags, dict) or not actor_id or not witness_id or actor_id == witness_id:
        return None
    dims = tags.get("dimensions") or {}
    if not isinstance(dims, dict):
        dims = {}
    received = bool(tags.get("target")) and str(tags.get("target")) == str(witness_id)
    attribution = str(tags.get("attribution", "unknown") or "unknown").lower()

    social = tags.get("social")
    obs = {}
    if isinstance(social, dict) and social:
        for axis, v in social.items():
            if axis in RELATIONSHIP_AXES:
                try:
                    obs[axis] = _clamp01(float(v))
                except (TypeError, ValueError):
                    continue
        severity = max((abs(v - 0.5) * 2.0 for v in obs.values()), default=0.0)
        dominant = max(dims, key=lambda k: float(dims[k])) if dims else "social_violation"
    else:
        for dim, rows in _DIM_AXES.items():
            try:
                s = _clamp01(float(dims.get(dim, 0.0)))
            except (TypeError, ValueError):
                continue
            if s <= 0.0:
                continue
            for axis, sign, weight in rows:
                # observed sits at 0.5 (neutral) and is pushed to the axis extreme by severity
                o = 0.5 + sign * 0.5 * s * weight
                # several dimensions can speak to one axis; the most extreme read wins
                if axis not in obs or abs(o - 0.5) > abs(obs[axis] - 0.5):
                    obs[axis] = _clamp01(o)
        if not dims:
            return None
        dominant = max(dims, key=lambda k: float(dims[k]))
        severity = _clamp01(float(dims.get(dominant, 0.0)))

    # debt: only for the party the act was about, only for the giving dimensions
    if received and dominant in _DEBT_DIMS and severity > 0.0:
        obs["debt"] = None                      # marker: accumulator, not a delta-rule target

    if not obs:
        return None
    return {"toward": str(actor_id), "observations": obs, "severity": severity,
            "dominant": dominant, "received": received, "attribution": attribution}


# OVERTNESS — above this severity an act is public and nobody in the room can miss it; below it,
# the act is a slight, a look, a withheld word, and registering it takes noticing. gate.py already
# splits percepts this way (an always-surfaced core event, subtle cues behind PERCEPTION_DC_SUBTLE);
# this maps that same split onto social acts rather than inventing a second axis.
_OVERT_SEVERITY = 0.55


def witnessed(act, skills, edge=None):
    """Did this bystander actually REGISTER the act, and can they pin it on the speaker?

    relationships.md's update rule, point 4: "A updates on what A BELIEVES B did". Presence is not
    perception — a distracted or unobservant character standing right there can miss the slight that
    everyone else caught, and a stranger can watch a thing happen without being able to attribute it
    to anyone in particular.

    Two deterministic checks, both reusing gate.py's DCs so bonds cannot drift from the perception
    rules the rest of the engine uses (relevancy-gate.md Resolution: skill vs DC, no randomness):

      1. OVERTNESS. Below `_OVERT_SEVERITY` the act is subtle and needs `perception`.
      2. RECOGNITION. You can pin an act on someone you KNOW at any insight (a standing edge);
         pinning it on a stranger needs `insight` — gate.py's own rule for entity recognition.

    `skills` of None admits everything, so a caller without a character sheet is unchanged.
    Returns bool. A failed check yields NO belief about the act, not a wrong one — misperception as
    content is the false-belief layer, which is unbuilt.
    """
    if skills is None:
        return True
    if not isinstance(act, dict):
        raise EngineError("BONDS_WITNESSED_ACT_NOT_A_DICT", "witnessed: act must be a dict, got %r" % type(act).__name__)
    if not isinstance(skills, dict):
        raise EngineError("BONDS_WITNESSED_SKILLS_NOT_A_DICT", "witnessed: skills must be a dict or None, got %r" % type(skills).__name__)
    if float(act.get("severity", 0.0)) < _OVERT_SEVERITY:
        if not _passes_check(skills.get("perception", 0.5), PERCEPTION_DC_SUBTLE):
            return False
    known = isinstance(edge, dict) and bool(edge)          # a standing edge IS acquaintance
    return known or _passes_check(skills.get("insight", 0.5), PERCEPTION_DC_IDENTITY)


def observe(edge, act, model, attribution=None, expect=None, cliffs=True):
    """ONE witness's per-axis edge deltas from ONE act. Pure; returns {} when nothing moves.

    edge   -- the witness's CURRENT edge toward the actor ({axis: value}); {} for a stranger.
    act    -- from act_from_tags (the objective layer).
    model  -- the witness's worth menu (baseline.model) — this is what makes the update THEIRS.
    expect -- where to read the EXPECTATION from, if not the edge itself. `reflect` passes the
              second-order block; charity still reads first-order trust off `edge`, because whether
              you believe someone's excuse depends on what you make of THEM, not on what you think
              they make of you.
    cliffs -- off for the second order: a cliff is a judgement about unforgivability, which is a
              stance you take toward a person, not a reading of how they feel.
    """
    if not isinstance(act, dict):
        raise EngineError("BONDS_OBSERVE_ACT_NOT_A_DICT", "observe: act must be a dict, got %r" % type(act).__name__)
    if not isinstance(model, dict):
        raise EngineError("BONDS_OBSERVE_MODEL_NOT_A_DICT", "observe: model must be a dict, got %r" % type(model).__name__)
    edge = edge if isinstance(edge, dict) else {}
    exp = expect if isinstance(expect, dict) else edge
    obs = act.get("observations") or {}
    severity = float(act.get("severity", 0.0))
    if severity <= 0.0 or not obs:
        return {}

    relevance = _relevance(act.get("dominant", ""), model)
    # The act's OBJECTIVE attribution, then the witness's reading of it. A witness who does not
    # trust this person does not believe the excuse — see _CHARITY_FLOOR above.
    stated = _ATTRIBUTION.get(str(attribution or act.get("attribution") or "unknown").lower(), 1.0)
    charity = _CHARITY_FLOOR + (1.0 - _CHARITY_FLOOR) * float(edge.get("trust", _NEUTRAL["trust"]))
    attrib = 1.0 - (1.0 - stated) * charity                # full damping only from a trusting witness
    gain = relevance * attrib
    if gain <= 0.0:
        return {}

    deltas = {}
    for axis, observed in obs.items():
        if axis not in RELATIONSHIP_AXES:
            continue
        if axis in _RECEIVED_ONLY and not act.get("received"):
            continue
        if observed is None:                                  # debt: an ACCOUNT, not a belief
            # Only the IMPLICIT path lands here (a kindness received, marked by act_from_tags), and
            # it can only add: you cannot accidentally repay someone. An EXPLICIT social.debt reading
            # skips this branch and takes the delta rule below, where a low observation against a
            # high standing balance comes out negative — which is how a favour gets called in.
            deltas[axis] = round(severity * _DEBT_RATE * gain, 6)
            continue
        expected = float(exp.get(axis, _NEUTRAL.get(axis, 0.5)))
        surprise = observed - expected
        if abs(surprise) < 1e-9:
            continue                                          # exactly what they expected: no news
        alpha = _ALPHA_NEG if surprise < 0 else _ALPHA_POS     # <- the negativity bias
        d = surprise * alpha * gain
        if (cliffs and axis in _CLIFF_AXES and observed <= _CLIFF_FLOOR
                and severity >= _CLIFF_SEVERITY and relevance >= _CLIFF_RELEVANCE):
            # A cliff is UNFORGIVABILITY, and that is a judgement about intent — so attribution
            # gates the drop rather than being overridden by it. At full attribution the edge lands
            # on the floor; as the act reads more accidental the target rises back toward where the
            # edge already was, and the ordinary slope (min) takes over. An accident never cliffs.
            target = _CLIFF_FLOOR + (expected - _CLIFF_FLOOR) * (1.0 - attrib)
            d = min(d, target - expected)                      # discontinuity, not a slope
        deltas[axis] = round(d, 6)
    return {a: d for a, d in deltas.items() if abs(d) > 1e-6}


def apply_deltas(edge, deltas):
    """Edge + deltas -> a NEW edge dict, every axis clamped [0,1]. Never mutates its input."""
    if not isinstance(deltas, dict):
        raise EngineError("BONDS_APPLY_DELTAS_NOT_A_DICT", "apply_deltas: deltas must be a dict, got %r" % type(deltas).__name__)
    new = dict(edge) if isinstance(edge, dict) else {}
    for axis, d in deltas.items():
        if axis not in RELATIONSHIP_AXES:
            raise EngineError("BONDS_APPLY_DELTAS_NOT_IN_SET", "apply_deltas: %r not in %s" % (axis, list(RELATIONSHIP_AXES)))
        new[axis] = _clamp01(float(new.get(axis, _NEUTRAL.get(axis, 0.5))) + float(d))
    return new


# The two orders read one act DIFFERENTLY, and this map is the difference.
#
# The first pass of this module assumed they did not — that the same observations served both, and
# only the target of the belief changed. A test falsified it: a betrayal aimed at YOU moves trust
# and respect on the first-order map, so the second order came out saying nothing about affinity
# at all. But "they did this to me" is the plainest possible evidence about their warmth toward me,
# and a character who cannot draw it is not modelling a slight, they are auditing a contract.
#
# What the two orders share: a kindness aimed at you already reads affinity-positive on the shared
# map, so only the negative case needed the extension.
_SECOND_ORDER_EXTRA = {
    "social_violation": [("affinity", -1.0, 1.0)],
}


def _second_order_act(act):
    """The same act, re-read as evidence about how the actor regards the person it was aimed at."""
    dominant = act.get("dominant", "")
    rows = _SECOND_ORDER_EXTRA.get(dominant)
    if not rows:
        return act
    sev = float(act.get("severity", 0.0))
    obs = dict(act.get("observations") or {})
    for axis, sign, weight in rows:
        o = _clamp01(0.5 + sign * 0.5 * sev * weight)
        if axis not in obs or obs[axis] is None or abs(o - 0.5) > abs(obs[axis] - 0.5):
            obs[axis] = o
    return dict(act, observations=obs)


def reflect(edge, act, model, attribution=None):
    """What this act tells the person it was AIMED AT about how the actor regards THEM.

    docs/relationships.md's rich layer, last item: "second-order (what A thinks B feels about A)".
    Without it, unrequited attachment is unrepresentable — someone who adores a person they know to
    be indifferent stores exactly what someone who believes it is returned stores. The gap between
    the two IS the drama, and it lived nowhere.

    The evidence is the same act; what differs is which belief it updates and what that belief
    EXPECTED. So this is `observe` pointed at `edge["their_view"]`, with cliffs off.

    Fires only on a RECEIVED act. Watching someone be cruel to a third party is evidence about that
    person — which `observe` already takes — but it is not an observation of how they feel about
    YOU. Concluding that from it is inference, and this engine has no inference layer to put it in.

    Returns {axis: delta} for the second-order block, or {} — including {} for a bystander.
    """
    if not isinstance(act, dict):
        raise EngineError("BONDS_REFLECT_ACT_NOT_A_DICT", "reflect: act must be a dict, got %r" % type(act).__name__)
    if not act.get("received"):
        return {}
    edge = edge if isinstance(edge, dict) else {}
    view = edge.get("their_view")
    return observe(edge, _second_order_act(act), model, attribution=attribution,
                   expect=view if isinstance(view, dict) else {}, cliffs=False)


def apply_reflection(edge, deltas):
    """Edge + second-order deltas -> a NEW edge whose `their_view` has moved. Never mutates."""
    if not isinstance(deltas, dict):
        raise EngineError("BONDS_APPLY_REFLECTION_DELTAS_NOT_A_DICT", "apply_reflection: deltas must be a dict, got %r" % type(deltas).__name__)
    new = dict(edge) if isinstance(edge, dict) else {}
    view = new.get("their_view")
    new["their_view"] = apply_deltas(view if isinstance(view, dict) else {}, deltas)
    return new


def drift(edge, priors=None, elapsed=1.0):
    """Unreinforced edges settle back toward a resting state (relationships.md:30).

    `elapsed` is in whatever unit the caller declares — scenes, days, chapters — and NOT beats: a
    single conversation must not erode a friendship, which is why this is not wired into the beat
    loop. `priors` is the character's `baseline.relationship_priors` (default_trust), the field that
    reference-species-prior.md:121 names as the one formative environment moves hardest and that
    nothing has ever read at runtime until now.
    """
    edge = edge if isinstance(edge, dict) else {}
    priors = priors if isinstance(priors, dict) else {}
    try:
        elapsed = max(0.0, float(elapsed))
    except (TypeError, ValueError):
        raise EngineError("BONDS_DRIFT_ELAPSED_NOT_NUMERIC", "drift: elapsed must be a number, got %r" % (elapsed,))
    rest = dict(_NEUTRAL)
    if "default_trust" in priors:
        try:
            rest["trust"] = _clamp01(float(priors["default_trust"]))
        except (TypeError, ValueError):
            pass
    out = dict(edge)
    for axis in RELATIONSHIP_AXES:
        if axis not in edge:
            continue
        r = _RETENTION[axis] ** elapsed
        out[axis] = _clamp01(rest[axis] + (float(edge[axis]) - rest[axis]) * r)
    return out


def replay(relationships, deltas):
    """Fold logged edge movements back onto sheet-authored relationships. Mutates and returns.

    THE ONE PLACE the fold lives, because `arc_diffs_for` taught the lesson: a replay whose logic
    is hand-copied into each resume path drifts, and the copies are the defect. `scripts/scene.py`
    and `scripts/direct.py` both call THIS; the test exercises THIS. There is no second copy to
    disagree with it.

    `deltas` is what `Ledger.edge_deltas_for` returns: [(target, axis, delta, order)] in turn order.
    Second-order rows land in the edge's `their_view` sub-map (what the perceiver believes the OTHER
    holds), first-order on the edge itself. An axis absent from the sheet starts at neutral 0.5 —
    the same floor `_NEUTRAL` uses — because a movement logged against an unauthored axis is still a
    movement, and dropping it would silently lose the only record of it.
    """
    if not isinstance(relationships, dict):
        raise EngineError("BONDS_REPLAY_RELATIONSHIPS_NOT_A_DICT", "replay: relationships must be a dict, got %r" % type(relationships).__name__)
    for target, axis, delta, order in deltas or ():
        if axis not in RELATIONSHIP_AXES:
            raise EngineError("BONDS_REPLAY_UNKNOWN_AXIS_UNKNOWN", "replay: unknown axis %r (log disagrees with RELATIONSHIP_AXES)" % (axis,))
        edge = relationships.setdefault(target, {})
        slot = edge.setdefault("their_view", {}) if order == "second" else edge
        slot[axis] = _clamp01(float(slot.get(axis, _NEUTRAL[axis])) + float(delta))
    return relationships
