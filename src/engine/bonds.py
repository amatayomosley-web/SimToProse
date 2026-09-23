"""bonds.py — the relationship tier: how one person's belief about another MOVES, per witnessed act.

Third tier beside `state.py` (affect, per beat) and `arc.py` (the durable self, per actor-turn).
This one runs **per WITNESS per turn**, and that cadence is the whole point: `docs/relationships.md:5`
— an edge is *A's belief about A↔B*, held by A. Before this module the only edge writer ran on the
SPEAKER, so when A betrayed B, A's trust in B fell and B's never moved. Edges are witness-scoped.

THE LAW (`docs/bond-arithmetic.md` s6, 2026-09-17 — bond gate 4), four lines:

  1. THE ANCHOR. An act's rung is the ceiling of what that act can teach, plus one rung for
     repetition (`_BETA`). On the edge's own side of the stranger, the edge rises (or deepens) toward
     the act's height one rung further out, and stops: twelve `kind` acts carry a friend to .77 and
     no further; forty `selfless` acts reach .95. Nothing runs away, nothing tracks the median act.
  2. THE CROSSING. A read on the OTHER side of the stranger is prediction error — `(o − e)`, the
     doc's surprise, weighted by how much the word says (`2|d|`): a `curt` word barely moves a devoted
     friend, a `treacherous` one moves him most of the way — with `_ALPHA_NEG > _ALPHA_POS`, trust
     arriving on foot and leaving on horseback. The cliff sits on top of this branch.
  3. THE STAKE (the owner's rule, s0). An act moves a witness's belief only through what SHE holds
     that the act touched: herself in full, a person by her affinity to them, a thing she holds by
     her hold (gate 5). Values in the abstract move nothing — except trust keeps a floor (a liar
     seen lying to a stranger still costs him) and respect is stake-free (a stranger's mastery
     earns it). The worth menu (`state._relevance`) stays as a factor inside the gain, not the gate.
  4. THE REST, which lives next door (`bond_rest.py`): an unreinforced edge drifts toward its own
     declared rest, never toward the stranger's — a devoted friend does not become a stranger over
     a winter. The law here never reads the rest; the two clocks are two modules.

What this replaced (2026-08-22 → 2026-09-17): a prediction-error law on EVERY act, expected = the
edge, so a confirming act below the edge cooled a friend (twelve `kind` acts took him .75 → .66,
measured), a stranger could never be distrusted, and drift went to .5. The betrayal numbers of that
law survive unchanged on the crossing branch; only the tracking artefact is gone.

WHO SAYS WHAT. The event seat rates the act ONCE, objectively, in words (`scripts/appraiser.py`:
`object` + `showed` on the act ladders, priced at the parse seam by `observations_from_showed`);
each witness then computes her OWN delta from her own stake, her own values, her own expectation,
her own attribution. No actor ever declares what someone else should feel about them.

DEBT IS NOT A BELIEF: it is an ACCOUNT, moved by the seat's ENTRIES (`gave`, `called in` on the
receiver's edge; `repaid` on the actor's own), priced at `_DEBT_RATE` × the beat's strength × the
gain. `refused` moves no account — the obligation stands, and trust carries it.

Pure, deterministic, stdlib. No LLM (CLAUDE.md rule 3), no randomness (rule 4), no numbers to the
prompt (rule 5 — `direction.direct_edge` renders these).
"""
from .gate import PERCEPTION_DC_IDENTITY, PERCEPTION_DC_SUBTLE, _passes_check
from .records import RELATIONSHIP_AXES, RecordError
from . import severity as _severity
from .state import _relevance

# ---------------------------------------------------------------------------
# CONSTANTS — every row is in docs/constant-register.md with its basis; bond-arithmetic.md s8 says
# what pins each and how well. None is fitted yet (gate 6, the thermometer).
# ---------------------------------------------------------------------------
_ALPHA_POS = 0.12          # rate moving UP the scale (warming, trusting more)      [LITERATURE-ordered; unfitted]
_ALPHA_NEG = 0.30          # rate moving DOWN it. NEG > POS IS the negativity bias  [LITERATURE-ordered; unfitted]
_BETA = 0.12               # one rung of the act ladder: an act's reach is one rung past its height  [DERIVED: the ladder's rung gap]
_REACH = 0.45              # the same-wing target clamp, as a deviation: .95 / .05 on the axis      [DOC: s6]
_TRUST_STAKE_FLOOR = 0.30  # trust's stake floor: a liar seen lying to a stranger still costs him  [JUDGMENT, Fable settled review 11]
_DEBT_RATE = 0.05          # per entry, × the beat's dimension severity × gain — five `marked` gifts cross "a favour" [JUDGMENT]

# THE CLIFF — a discontinuity, not a slope (relationships.md:27 "some acts are cliffs"). Fires on the
# ACT LADDER'S FLOOR WORD (`treacherous`, height .10 ≤ _CLIFF_FLOOR) when the witness's values make
# the act relevant enough; it lands trust ON the floor. `_CLIFF_SEVERITY` (a strength-word test)
# retired 2026-09-17: strength gates overtness and sizes debt, never a belief's magnitude.
_CLIFF_RELEVANCE = 0.60
_CLIFF_FLOOR = 0.15
_CLIFF_AXES = ("trust",)

# ATTRIBUTION damping (relationships.md:29). 'unknown' is FULL, not damped: absent an explanation
# people attribute to intent, and it also means an untagged act behaves exactly as before.
_ATTRIBUTION = {"malice": 1.0, "intent": 1.0, "unknown": 1.0,
                "negligence": 0.70, "coerced": 0.35, "accident": 0.15}

# CHARITY — how far a witness is willing to believe the actor's account of WHY. An extension of the
# doc: charity scales with trust, so low trust reads an accident as malice, which lowers trust
# further — how relationships actually fail, and falsifiable (a cast spiralling into contempt from
# nothing means this curve is too steep).
_CHARITY_FLOOR = 0.15      # even a hated stranger gets this much benefit of the doubt

# Per-axis neutral point — a STRANGER: what an edge means when nobody has authored one.
_NEUTRAL = {"trust": 0.5, "affinity": 0.5, "respect": 0.5, "debt": 0.0}

# Axes that move only for the party the act was ABOUT, never for a bystander. You owe someone who
# helped YOU; watching them help a stranger raises your regard, not your debt.
_RECEIVED_ONLY = ("debt",)

# PER-WITNESS RATES from `relationship_priors.update` (authored on a few sheets, read by nothing until
# 2026-09-17). grant_threshold: how readily she lets someone in; withdraw_speed: how fast she lets
# them go. The bands are the constants ±50% / ×2/3 and ×1.5 [JUDGMENT — unfitted, like the constants].
_RATE_POS = {"low": 0.18, "moderate": 0.12, "high": 0.06}
_RATE_NEG = {"slow": 0.20, "typical": 0.30, "fast": 0.45}

# OVERTNESS — below this strength an act is subtle and needs noticing (`witnessed`). Strength is
# the beat's dimension severity, never the read: a read is a quality, and reading it as strength
# blinded a witness to every act done in front of her (measured on a live scene).
_OVERT_SEVERITY = 0.55


def _clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def observations_from_showed(showed):
    """The seat's `showed` block -> {axis: observed 0..1}. Pure. THE SEAM (bond-arithmetic.md s4).

    The event seat answers per act on the ACT ladders (`severity.ACT_WORDS`: a quality THIS ACT
    showed, four rungs a side, no middle word), only for the axes the act spoke to. This turns
    each word into its height so `act_from_tags` receives floats and never a word.
      OMITTED IS NOTHING — not neutral, not derived from the dimensions (s6; the dimension route
      survives only as `tests/bond_replay.py`'s control arm): a derived read on an omitted axis is
      the "every beat moves every axis" failure the retired `social` block had.
      REFUSE, NEVER SKIP — a value neither a float nor a word on that axis's ladder raises by code;
      the old branch dropped it silently, and that skip kept the tier dormant for four performances.
    Debt is not here at all since 2026-09-18: the account moves on a TRANSFER the seat reports as a
    fact (`debt_postings`), never on a word — `debt` inside showed is an unknown axis.
    """
    obs = {}
    for axis, v in (showed.items() if isinstance(showed, dict) else ()):
        if axis not in _severity.ACT_AXES:
            raise RecordError("BONDS_SHOWED_AXIS_UNKNOWN",
                              "observations_from_showed: %r is not an act-ladder axis %s" % (axis, list(_severity.ACT_AXES)))
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            obs[axis] = _clamp01(float(v))
            continue
        try:
            obs[axis] = _severity.act_value_of(axis, str(v))
        except _severity.SeverityError:
            raise RecordError("BONDS_SHOWED_WORD_UNKNOWN",
                              "observations_from_showed: %r on %r is not an act word (%s); refused, not skipped"
                              % (v, axis, ", ".join(_severity.ACT_WORDS[axis])))
    return obs


def debt_postings(tags, actor_id, accounts, present=None):
    """The seat's TRANSFERS -> the debt postings they warrant -> [(perceiver, target, entry, delta, cause)].

    THE ACCOUNT MOVES ON A FACT, NOT A VERDICT (2026-09-18; bond-arithmetic.md s6). The seat used to
    answer `gave | repaid | refused | called in` and the law priced the word: measured on the first
    live scene it fired on 10 of 14 beats, and on one beat it was signed backwards — the word was
    read from the speaker's side while the account belongs to the pair, so the posting landed on
    the wrong party. Now the seat reports what changed hands
    (`transfers`: what, from, to, terms as SAID — none | price | loan | repayment) and this function
    decides the entry from the words and the account:

        m = _DEBT_RATE × the beat's dimension severity × attribution × hold(to)   hold = 1 for a person
        per ordered pair (from, to) with a transfer row:
            any row with terms none | loan   -> (to,   from, "gave",   +m)   the receiver owes more
            any row with terms repayment     -> (from, to,   "repaid", -m)   iff accounts[from][to] > 0;
                                                                             a repayment of nothing owed posts nothing
            rows with terms price            -> nothing                      square by their own words
        ONE gave and ONE repaid per pair per beat, however many things: the beat is the unit the law prices
        (five small things must not outrank one purse). A `to` that is not a person present posts nothing
        (a transfer to a thing someone holds is gate 5's, once `held_map` says whose account it is).
        `refused` and `called in` are words, not transfers: the account moves when the owed thing is
        DELIVERED (a later transfer with terms repayment).

    The engine never reads the account to CHOOSE the entry — a priced thing is a price whichever way
    it passes, even between two who owe, never a repayment — only to refuse a repayment of nothing. `self` in from/to
    resolves to the actor. `accounts` is {perceiver: {target: debt}} for the people present.
    """
    if not isinstance(tags, dict):
        return []
    rows = tags.get("transfers") or []
    if not isinstance(rows, list) or not rows:
        return []
    me = str(actor_id).strip().lower()
    dims = tags.get("dimensions") or {}
    sev = max((_clamp01(float(v)) for v in dims.values() if isinstance(v, (int, float))), default=0.0) if isinstance(dims, dict) else 0.0
    if sev <= 0.0:
        return []
    attrib = _ATTRIBUTION.get(str(tags.get("attribution", "unknown") or "unknown").lower(), 1.0)
    people = {str(x).strip().lower() for x in (present or ())} if present is not None else None
    pairs = {}                                            # (from, to) -> {"terms": set, "what": [..]}
    for r in rows:
        if not isinstance(r, dict):
            continue
        f = str(r.get("from") or "").strip().lower(); t = str(r.get("to") or "").strip().lower()
        f = me if f == "self" else f; t = me if t == "self" else t
        terms = str(r.get("terms") or "none").strip().lower()
        if not f or not t or f == t:
            continue
        if people is not None and t not in people:
            continue                                      # a transfer to a THING posts nothing (deferred 2026-09-18, gate 5: the seat's contract restricts from/to to THE PEOPLE; the candidate rule is in the gate-5 plan)
        pr = pairs.setdefault((f, t), {"terms": set(), "what": [], "hold": 1.0})
        pr["terms"].add(terms); pr["what"].append((terms, str(r.get("what") or "").strip()))
    out = []
    for (f, t), pr in pairs.items():
        m = round(_DEBT_RATE * sev * attrib * pr["hold"], 6)
        # the row's `cause` names only the things that MOVED the account: a priced thing on the same beat
        # as a loan is square by its own words and does not belong on the gave row (found 2026-09-18:
        # a priced thing and a loaned one named on one row, where only the loan was owed)
        cause_of = lambda kinds: "; ".join(w for k, w in pr["what"] if w and k in kinds)
        if pr["terms"] & {"none", "loan"}:
            out.append((t, f, "gave", m, cause_of({"none", "loan"})))
        if "repayment" in pr["terms"]:
            owed = float(((accounts or {}).get(f) or {}).get(t, 0.0) or 0.0)
            if owed > 0.0:
                out.append((f, t, "repaid", -m, cause_of({"repayment"})))
    return out


def act_from_tags(tags, actor_id, witness_id, held=None):
    """One actor's committed tags -> the OBJECTIVE act, as it bears on ONE witness. None if the act
    showed nothing on any axis, or if the witness IS the actor (nobody holds an edge to themselves).

    -> {toward, observations {axis: height}, severity, dominant, received, attribution, object}

    Observations come ONLY from `showed` (bond-arithmetic.md s6 OMITTED: nothing — not derived from
    the dimensions; the stub double emits no `showed`, so a --stub run moves no edge and says so).
    `severity` is the max of the dimensions: it gates overtness and sizes debt, never a belief.
    `received` := the act's OBJECT resolves to this witness (s5): the seat's object first, the
    driver's `target` as the fallback for tags with no object; `held` ({entity: hold} for this
    witness, gate 5) makes an act on a thing she holds an act done to her. `object` is the resolved
    id the act is about, for `stake_of`.
    """
    if not isinstance(tags, dict) or not actor_id or not witness_id or actor_id == witness_id:
        return None
    dims = tags.get("dimensions") or {}
    if not isinstance(dims, dict):
        dims = {}
    showed = tags.get("showed")
    obs = observations_from_showed(showed) if isinstance(showed, dict) and showed else {}
    if not obs:
        return None
    _obj = str(tags.get("object") or "").strip().lower() or str(tags.get("target") or "").strip().lower()
    # THE SEAT'S `self` IS THE ACTOR AS A PERSON (s6, stake): resolved here, once, for every caller —
    # unresolved it reached stake_of as a name nobody holds an edge to and priced at 0 (found 2026-09-18).
    if _obj == "self":
        _obj = str(actor_id).strip().lower()
    _me = str(witness_id).strip().lower()
    received = bool(_obj) and _obj == _me
    if not received and _obj and isinstance(held, dict):
        _hv = held.get(_obj)                              # gate 5: an act on a thing she holds is done TO her
        received = isinstance(_hv, (int, float)) and not isinstance(_hv, bool) and float(_hv) > 0.0
    severity = max((_clamp01(float(v)) for v in dims.values() if isinstance(v, (int, float))), default=0.0)
    dominant = max(dims, key=lambda k: float(dims[k])) if dims else "social_violation"
    return {"toward": str(actor_id), "observations": obs, "severity": severity, "dominant": dominant,
            "received": received, "attribution": str(tags.get("attribution", "unknown") or "unknown").lower(),
            "object": _obj}


def witnessed(act, skills, edge=None):
    """Did this bystander actually REGISTER the act, and can they pin it on the speaker?

    relationships.md's update rule, point 4: "A updates on what A BELIEVES B did". Presence is not
    perception. Two deterministic checks on gate.py's own DCs (no randomness):
      1. OVERTNESS. Below `_OVERT_SEVERITY` the act is subtle and needs `perception` — EXCEPT an act
         done TO the witness (`received`, s6): you do not miss what is done to you.
      2. RECOGNITION. You can pin an act on someone you KNOW (a standing edge); pinning it on a
         stranger needs `insight` — gate.py's own rule for entity recognition.
    `skills` of None admits everything. A failed check yields NO belief, not a wrong one.
    """
    if skills is None:
        return True
    if not isinstance(act, dict):
        raise RecordError("BONDS_ACT_NOT_A_DICT", "witnessed: act must be a dict, got %r" % type(act).__name__)
    if not isinstance(skills, dict):
        raise RecordError("BONDS_SKILLS_INVALID", "witnessed: skills must be a dict or None, got %r" % type(skills).__name__)
    if not act.get("received") and float(act.get("severity", 0.0)) < _OVERT_SEVERITY:
        if not _passes_check(skills.get("perception", 0.5), PERCEPTION_DC_SUBTLE):
            return False
    known = isinstance(edge, dict) and bool(edge)          # a standing edge IS acquaintance
    return known or _passes_check(skills.get("insight", 0.5), PERCEPTION_DC_IDENTITY)


def stake_of(witness_id, obj, relationships, held=None):
    """How much this witness HOLDS the act's object -> 0..1 (bond-arithmetic.md s5).

    Herself -> 1. A person she holds an edge to -> her affinity above the stranger, doubled
    (`max(0, 2·(affinity − .5))`) — NO dead zone: a gate is not a multiplier. A thing she holds ->
    `held[obj]` (gate 5: `connection.held_map`, passed by `floor.bond_moves` and `direct.run_turn`;
    a scalar `loc.` / `grp.` entry is her hold). Anything else — an unregistered name, an
    unknown id, '' — -> 0: the owner's rule, values in the abstract move nothing. `self` (the actor
    acting on himself) resolves per witness to the actor as a person — a stranger's act on himself
    moves her affinity by nothing, her trust by the floor, her respect in full.
    """
    o = str(obj or "").strip().lower()
    if not o:
        return 0.0
    if o == str(witness_id).strip().lower():
        return 1.0
    if isinstance(held, dict) and o in held:
        v = held.get(o)                                   # a dict-valued concept entry is the emotion registry's wound map, not a hold
        return _clamp01(float(v)) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0
    rels = relationships if isinstance(relationships, dict) else {}
    edge = rels.get(o) or rels.get(obj) or {}
    if isinstance(edge, dict) and "affinity" in edge:
        return _clamp01(2.0 * (float(edge["affinity"]) - 0.5))
    return 0.0


def rates_of(priors):
    """`relationship_priors.update` -> (alpha_pos, alpha_neg). No `update` -> the constants. A word
    off `_RATE_POS` / `_RATE_NEG` is REFUSED, never defaulted. Reads nothing else on the block."""
    upd = (priors or {}).get("update") if isinstance(priors, dict) else None
    if not isinstance(upd, dict):
        return _ALPHA_POS, _ALPHA_NEG
    pos, neg = _ALPHA_POS, _ALPHA_NEG
    if "grant_threshold" in upd:
        w = str(upd["grant_threshold"]).strip().lower()
        if w not in _RATE_POS:
            raise RecordError("BONDS_RATE_WORD_UNKNOWN", "rates_of: grant_threshold %r is not one of %s" % (upd["grant_threshold"], list(_RATE_POS)))
        pos = _RATE_POS[w]
    if "withdraw_speed" in upd:
        w = str(upd["withdraw_speed"]).strip().lower()
        if w not in _RATE_NEG:
            raise RecordError("BONDS_RATE_WORD_UNKNOWN", "rates_of: withdraw_speed %r is not one of %s" % (upd["withdraw_speed"], list(_RATE_NEG)))
        neg = _RATE_NEG[w]
    return pos, neg


def law_delta(o, e, alpha_pos=_ALPHA_POS, alpha_neg=_ALPHA_NEG):
    """THE LAW, ungained (bond-arithmetic.md s6). o = the act word's height, e = the edge.

        d = o − .5, x = e − .5                       deviations from the stranger
        SAME WING (d·x > 0, or x == 0):
            t = clamp(d ± _BETA, ±_REACH)            the act's rung, one rung further out
            0 if |x| ≥ |t| else α·(t − x)            α_pos moving up the scale, α_neg moving down
        CROSSING (d·x < 0):
            α·2|d|·(o − e)                            prediction error, weighted by what the word says
    Pure floats. The nine worked cases are tests/test_bonds.py [20].
    """
    d, x = float(o) - 0.5, float(e) - 0.5
    if d == 0.0:
        return 0.0
    if x == 0.0 or d * x > 0.0:
        t = max(-_REACH, min(_REACH, d + (_BETA if d > 0 else -_BETA)))
        if abs(x) >= abs(t):
            return 0.0
        return (alpha_pos if t > x else alpha_neg) * (t - x)
    return (alpha_pos if o > e else alpha_neg) * 2.0 * abs(d) * (float(o) - float(e))


def _gain(axis, stake, attrib, relevance):
    """The witness's terms, per axis (s6): affinity stake·attrib·rel | trust (floor + (1−floor)·stake)·attrib·rel
    | respect attrib·rel (stake-free) | debt stake·attrib."""
    if axis == "affinity":
        return stake * attrib * relevance
    if axis == "trust":
        return (_TRUST_STAKE_FLOOR + (1.0 - _TRUST_STAKE_FLOOR) * stake) * attrib * relevance
    if axis == "respect":
        return attrib * relevance
    return stake * attrib


def _terms(edge, act, model, attribution):
    """(relevance, attrib) — the two witness-side factors the law and the cliff share."""
    relevance = _relevance(act.get("dominant", ""), model)
    stated = _ATTRIBUTION.get(str(attribution or act.get("attribution") or "unknown").lower(), 1.0)
    charity = _CHARITY_FLOOR + (1.0 - _CHARITY_FLOOR) * float(edge.get("trust", _NEUTRAL["trust"]))
    return relevance, 1.0 - (1.0 - stated) * charity


def cliff_axes(edge, act, model, attribution=None):
    """The axes on which this act IS a cliff for this witness: the act word at the floor
    (observed ≤ _CLIFF_FLOOR), relevance ≥ _CLIFF_RELEVANCE, on a cliff axis -> tuple. The driver
    turns these into rest rows (bond_rest.cliff_rows). Fires for any witness whose values clear the
    bar, bystander included: a cliff is unforgivability, a stance about the man."""
    if not isinstance(act, dict) or not isinstance(model, dict):
        return ()
    edge = edge if isinstance(edge, dict) else {}
    relevance, _attrib = _terms(edge, act, model, attribution)
    obs = act.get("observations") or {}
    return tuple(a for a in _CLIFF_AXES if a in obs and obs[a] is not None
                 and float(obs[a]) <= _CLIFF_FLOOR and relevance >= _CLIFF_RELEVANCE)


def observe(edge, act, model, attribution=None, expect=None, cliffs=True, stake=None, rates=None):
    """ONE witness's per-axis edge deltas from ONE act. Pure; returns {} when nothing moves.

    edge   -- the witness's CURRENT edge toward the actor ({axis: value}); {} for a stranger.
    act    -- from act_from_tags (the objective layer).
    model  -- the witness's worth menu (baseline.model) — what makes the update THEIRS.
    expect -- where to read the EXPECTATION from, if not the edge (`reflect` passes their_view).
    cliffs -- off for the second order.
    stake  -- bonds.stake_of for this witness and the act's object. None is 1.0 for a RECEIVED act;
              a bystander call without it is REFUSED (BONDS_STAKE_MISSING) — never silently 1.
    rates  -- (alpha_pos, alpha_neg) from rates_of; None is the constants.
    """
    if not isinstance(act, dict):
        raise RecordError("BONDS_ACT_NOT_A_DICT", "observe: act must be a dict, got %r" % type(act).__name__)
    if not isinstance(model, dict):
        raise RecordError("BONDS_MODEL_NOT_A_DICT", "observe: model must be a dict, got %r" % type(model).__name__)
    edge = edge if isinstance(edge, dict) else {}
    exp = expect if isinstance(expect, dict) else edge
    if stake is None:
        if not act.get("received"):
            raise RecordError("BONDS_STAKE_MISSING", "observe: a bystander's call must carry stake= (bonds.stake_of); a received act may omit it")
        stake = 1.0
    stake = _clamp01(float(stake))
    a_pos, a_neg = rates if rates else (_ALPHA_POS, _ALPHA_NEG)
    relevance, attrib = _terms(edge, act, model, attribution)
    obs = act.get("observations") or {}
    deltas = {}
    for axis, observed in obs.items():
        if axis not in RELATIONSHIP_AXES or observed is None:
            continue
        if axis in _RECEIVED_ONLY and not act.get("received"):
            continue
        g = _gain(axis, stake, attrib, relevance)
        if g <= 0.0:
            continue
        expected = float(exp.get(axis, _NEUTRAL.get(axis, 0.5)))
        d = g * law_delta(float(observed), expected, a_pos, a_neg)
        if cliffs and axis in cliff_axes(edge, act, model, attribution):
            # UNFORGIVABILITY is a judgement about intent, so attribution gates the drop: at full
            # attribution the edge lands on the floor; an accident never cliffs.
            target = _CLIFF_FLOOR + (expected - _CLIFF_FLOOR) * (1.0 - attrib)
            d = min(d, target - expected)                      # discontinuity, not a slope
        deltas[axis] = round(d, 6)
    # THE ACCOUNT does not move here since 2026-09-18: a transfer is a fact about two people, priced
    # once by `debt_postings` from the seat's `transfers`, not a witness's read of a word.
    return {a: d for a, d in deltas.items() if abs(d) > 1e-6}


def apply_deltas(edge, deltas):
    """Edge + deltas -> a NEW edge dict, every axis clamped [0,1]. Never mutates its input. The clamp
    is what lets an authored .95 or .05 hold: nothing confirms it, nothing erodes it short of a
    crossing read."""
    if not isinstance(deltas, dict):
        raise RecordError("BONDS_DELTAS_NOT_A_DICT", "apply_deltas: deltas must be a dict, got %r" % type(deltas).__name__)
    new = dict(edge) if isinstance(edge, dict) else {}
    for axis, d in deltas.items():
        if axis not in RELATIONSHIP_AXES:
            raise RecordError("BONDS_EDGE_AXIS_UNKNOWN", "apply_deltas: %r not in %s" % (axis, list(RELATIONSHIP_AXES)))
        new[axis] = _clamp01(float(new.get(axis, _NEUTRAL.get(axis, 0.5))) + float(d))
    return new


def reflect(edge, act, model, attribution=None, stake=None, rates=None):
    """What this act tells the person it was AIMED AT about how the actor regards THEM — the second
    order (relationships.md's rich layer). Without it unrequited attachment is unrepresentable.

    Under the act ladders (2026-09-17): fires only on a RECEIVED act; reads the AFFINITY word only —
    how he holds me — since a `dependable` or `masterly` act says nothing about how he regards me;
    the debt entry is stripped; expectation = `their_view`; cliffs off; stake = the hold (1.0 when the
    object is the witness; gate 5 passes the hold). {} when the act showed no affinity.
    """
    if not isinstance(act, dict):
        raise RecordError("BONDS_ACT_NOT_A_DICT", "reflect: act must be a dict, got %r" % type(act).__name__)
    if not act.get("received"):
        return {}
    obs = act.get("observations") or {}
    if "affinity" not in obs or obs["affinity"] is None:
        return {}
    edge = edge if isinstance(edge, dict) else {}
    view = edge.get("their_view")
    second = dict(act, observations={"affinity": obs["affinity"]})
    return observe(edge, second, model, attribution=attribution, expect=view if isinstance(view, dict) else {},
                   cliffs=False, stake=1.0 if stake is None else stake, rates=rates)


def apply_reflection(edge, deltas):
    """Edge + second-order deltas -> a NEW edge whose `their_view` has moved. Never mutates."""
    if not isinstance(deltas, dict):
        raise RecordError("BONDS_DELTAS_NOT_A_DICT", "apply_reflection: deltas must be a dict, got %r" % type(deltas).__name__)
    new = dict(edge) if isinstance(edge, dict) else {}
    view = new.get("their_view")
    new["their_view"] = apply_deltas(view if isinstance(view, dict) else {}, deltas)
    return new
