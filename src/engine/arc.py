"""arc.py — the Arc Engine: durable baseline change over the story (docs/arc-engine.md).

NOT a new mechanism — appraisal with a DURABLE write. Most events spike current-state and fade
(state-engine.md). An event that is high-impact AND of a reshaping kind crosses a threshold and
writes a sparse DIFF to the BASELINE (temperament means and the bigotry regard) — moving the floor
of who the character is.

RELATIONSHIP EDGES USED TO BE WRITTEN HERE AND ARE NOT ANY MORE (`bonds.py` owns them). The reason is
a cadence mismatch, not a formula: this engine runs once per turn on the ACTOR, and
`relationships.md:5` defines an edge as the PERCEIVER's belief. So when A betrayed B it was **A's**
trust in B that fell — measured 0.80 -> 0.7828 — while B's edge was never computed at all. It also
scaled the damage by resilience, which made a kindness move trust up to 6x further than an equal
betrayal, inverting `relationships.md:27`. Resilience belongs exactly where it still is: on whether a
survival-threat SCARS or STRENGTHENS the person.

`apply` still accepts a `relationships` block. `assess` no longer produces one, but CLAUDE.md hard
rule 2 makes the log append-only and `direct.py` replays stored arc_diffs on resume, so a diff
persisted before this change must rehydrate to the state that run actually had. Backstory and arc are one engine (baseline-generation.md):
generation pre-plays these diffs before page one; the arc runs them during the book.

Same event, damage OR growth — the resilience FORK: low resilience -> a debuff (trauma signature);
high resilience -> a smaller diff or post-traumatic GROWTH. resilience is DERIVED at read time,
never stored (arc-engine.md). Pure, deterministic, stdlib. Diffs persist via ledger.append_arc_diff.
"""
from .decay_law import relax          # the one law; see its header
import copy

from .records import PRIMARIES, RecordError
from . import heritable as _her
from .state import _ALLELE, build_profile, price_for

# Class-B, probe-calibrated starts (arc-engine.md: threshold + magnitudes are calibration, not derived).
_ARC_THRESHOLD = 0.18      # durable-magnitude below this -> no baseline diff (most events stay transient)
_DURABLE_DIM   = 0.6       # a dim this severe marks a durable candidate (consolidation calibration: >0.6 = genuinely severe)
_BASE_STEP     = 0.326     # how far a single durable event moves a baseline value (× magnitude, before clamp).
#                          CALIBRATED 2026-09-01 to TWENTY durable events per rung of the 0.1 ladder
#                          (William's rate). At the previous 0.07 one severe durable affront moved the
#                          RAGE mean +0.00108 on the reference fixture — ninety-three events per rung, so a
#                          three-rung arc needed ~280 durable events and no book contains that. Base
#                          change was architecturally present and perceptually absent. Twenty was chosen
#                          over five: temperament must stay a DISPOSITION, not churn inside a chapter.
#                          The value looks small because it is multiplied by three sub-1.0 terms —
#                          impact (~0.35), the priced delta (~0.14), and (1 - resilience).
_REGARD_GENERALIZE = 0.4   # a bond with a disregarded-class member erodes the CLASS regard at this fraction of the edge move
_PTG_RESILIENCE = 0.70     # at/above this resilience, a survival-threat writes GROWTH (mastery) not damage (fear)
# The dominant dimensions whose SUBJECT is a support being WITHDRAWN — the person died, or the
# person wronged them. For these, and only these, the subject's edge sits out of the attachment
# term in `derive_resilience`. Not a taste call: `threat`, `mastery`, `care_relevant` and `relief`
# all name a subject who is still available to the character, so their bonds must keep buffering.
_SEVERING_DIMS = ("loss", "social_violation")
_ALLELE_MIN, _ALLELE_MAX = 0.75, 1.3


def _clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else float(x))


def _allele(raw):
    """One reading, in `heritable.py` — this was the third independent copy of the same parse."""
    return _ALLELE.get(_her.word(raw), 1.0)


def derive_resilience(char, condition, excluded=None):
    """DERIVED, never stored (arc-engine.md): effortful_control × condition × attachment-security.
    (The 4th design field — meaning-frame availability — is a documented TODO; defaulted out here.)
    Returns [0.05, 0.95].

    `excluded` NAMES A BOND THAT CANNOT BUFFER THIS EVENT, and it exists because the max below
    took every edge on the sheet with nothing about the event reaching it. So a death was softened
    by the character's love for the person who died, and a betrayal by their trust in the betrayer
    — the severed bond buffering the severing, in the same turn. `assess` supplies it for the two
    dominant dimensions whose SUBJECT is a withdrawn support (`loss`, `social_violation`) and for
    no others: a wolf attack must still be buffered by a bond to a friend, which is the finding the
    term is modelled on (post-trauma social support predicts recovery — Ozer 2003, Brewin 2000,
    both measuring support that SURVIVED the event).

    If nothing survives the exclusion the default is unchanged at 0.3. That is deliberate and it
    reverses a sketch of this fix that dropped it lower: a lower floor would assert that betrayal
    by your only friend leaves you worse off than never having had one, which is not a claim this
    engine has grounds for. 0.3 is the documented prior for "no relationship data" and a character
    whose only bond just failed them is, for this beat, a character without relationship data.
    """
    if not isinstance(char, dict) or not isinstance(condition, dict):
        raise RecordError("ARC_RESILIENCE_INPUT_NOT_A_DICT", "derive_resilience: char and condition must be dicts")
    geno = char.get("fixed", {}).get("genotype", {})
    ec = _allele(geno.get("effortful_control", "typical"))
    ec_norm = (ec - _ALLELE_MIN) / (_ALLELE_MAX - _ALLELE_MIN)          # effortful control, [0,1]
    load = float(condition.get("allostatic_load", 0.3))                 # high load depletes resilience
    rels = char.get("current", {}).get("relationships", {})
    drop = str(excluded) if excluded else None
    attachment = max((float(e.get("affinity", 0.0)) for eid, e in rels.items()
                      if isinstance(e, dict) and str(eid) != drop),
                     default=0.3)                                       # a secure bond present?
    r = 0.45 * ec_norm + 0.30 * (1.0 - load) + 0.25 * attachment
    return max(0.05, min(0.95, r))


def _profile_for(char):
    """The character's own pricing profile. Built here rather than threaded through every caller —
    `assess`'s signature is fixed by four call sites and two test suites."""
    return build_profile(char)


def assess(tags, impact, char, condition):
    """If this turn's event is DURABLE, return a sparse baseline diff; else None.

    tags:   the actor's event-tags {dimensions, durability, target?, target_group?}.
    impact: scalar appraised impact this turn (sum of |Δaffect| from appraise) — how much it moved them.
    Returns {temperament:{primary:Δ}, regard:{group:Δ}, _meta:{...}} | None. Relationship edges are
    NOT written here — see the module docstring; `bonds.observe` computes them per WITNESS.
    """
    if not isinstance(tags, dict):
        raise RecordError("ARC_ASSESS_TAGS_NOT_A_DICT", "assess: tags must be a dict")
    dims = tags.get("dimensions", {})
    if not isinstance(dims, dict) or not dims:
        return None
    # durable CANDIDATE: the actor self-reported 'durable', or a dimension is genuinely severe.
    candidate = tags.get("durability") == "durable" or any(float(v) >= _DURABLE_DIM for v in dims.values())
    if not candidate:
        return None
    # Gate on the RAW impact (resilience-independent): a reshaping event is durable whether or not
    # the character is resilient — resilience decides if it SCARS or STRENGTHENS, not if it lands.
    if float(impact) < _ARC_THRESHOLD:
        return None
    dominant = max(dims, key=lambda k: float(dims[k]))
    # THE SEVERED BOND CANNOT BUFFER ITS OWN SEVERING. `loss` and `social_violation` are the two
    # branches below whose SUBJECT is a support being withdrawn — the person died, or the person
    # wronged them. `target` names who the event is ABOUT (docs/standard-vectors.md, TARGET/SUBJECT;
    # `validate_tags` resolves it as `tags.get("subject") or tags.get("target")`), which is exactly
    # the edge that must sit out. Every other dimension keeps the full attachment term: a threat's
    # subject is the source of danger, not a lost friend, so a bond must still soften it.
    _severed = (tags.get("subject") or tags.get("target")) if dominant in _SEVERING_DIMS else None
    resilience = derive_resilience(char, condition, excluded=_severed)
    grw = _BASE_STEP * float(impact)                      # GROWTH step (full)
    dmg = grw * (1.0 - resilience)                        # DAMAGE step — resilience BUFFERS the scar
    group = tags.get("target_group")   # the SUBJECT is bonds.py's input now, not the arc's
    diff = {"temperament": {}, "regard": {}}

    # ONE PRICING TABLE, at both timescales (docs/character-model.md law 4). The seven hand-written
    # branches this replaces reached FOUR of eight primaries and every one of their writes was
    # POSITIVE, so a base-happy character through eighty durable diffs of beatings and degradation
    # ended with FEAR saturated and PLAY, CARE, RAGE and DISGUST at exactly their authored values.
    # `state.price_for` runs the identical chain `appraise` runs — severity x relevance x GENOTYPE
    # GAIN x sensitivity x push x regard x connection — so law 3 holds here too: an anger-prone man
    # now accumulates RAGE faster than a placid one from the same beating, which the old branches
    # could not express because they never read the gains at all.
    priced = price_for(dims, _profile_for(char), tags)
    for p, d in priced.items():
        v = d * grw * (1.0 - resilience)          # the damage step, generalised to eight primaries
        if v:
            diff["temperament"][p] = diff["temperament"].get(p, 0.0) + v

    # THE FORK SURVIVES, as ROW SELECTION over the same table rather than as a second formula.
    # Dissolving it into the gain looked right and is not: uniform scaling preserves ratios, and the
    # threat row is FEAR +0.45 against SEEKING +0.12 at every resilience, so no scalar can ever make
    # growth dominate — a resilient character would come out of every trial more fearful and less
    # playful, merely slower. Worse, under a (1-resilience) scale the BROKEN man accumulates more
    # SEEKING than the resilient one, which inverts the claim entirely. And the table's own
    # threat->SEEKING push is vigilance, not mastery: it prices damage richly and does not contain
    # growth, because growth is a property of the person meeting the event, not of the event.
    # So a survival threat met with resources ALSO reads the MASTERY row of the same table —
    # SEEKING up, PLAY up, FEAR down — which is what `arc-engine.md` has always specified for
    # mastery, at zero new constants.
    if dominant == "threat" and resilience >= _PTG_RESILIENCE:
        for p, d in price_for({"mastery": float(dims.get("threat", 0.0))},
                              _profile_for(char), tags).items():
            if d:
                diff["temperament"][p] = diff["temperament"].get(p, 0.0) + d * grw

    if dominant in ("care_relevant", "relief") and group:
        # the bond generalizes: class disregard erodes toward 1.0
        diff["regard"][group] = +grw * _REGARD_GENERALIZE

    if not diff["temperament"] and not diff["regard"]:
        return None

    diff["_meta"] = {"dominant": dominant, "impact": round(float(impact), 3),
                     "resilience": round(resilience, 3), "grw": round(grw, 4), "dmg": round(dmg, 4)}
    return diff


def apply(char, diff):
    """Apply a sparse baseline diff -> a NEW char dict (moves the floor; every value clamped [0,1]).
    Mutates baseline.temperament means and baseline.model.regard, and PRESERVES what the author
    wrote alongside each — `_authored_mean` per primary, `_authored_regard` per group. Moving the
    floor is the arc's job; erasing where the floor started was never asked for by any doc, and
    without the authored value no code can tell what a character was written as from what the story
    did to them.

    The `relationships` branch below is REPLAY-ONLY: `assess` has not emitted one since bonds.py took
    the edges, but a diff persisted before that must still rehydrate to the state its run had."""
    if not isinstance(char, dict) or not isinstance(diff, dict):
        raise RecordError("ARC_APPLY_INPUT_NOT_A_DICT", "apply: char and diff must be dicts")
    new = copy.deepcopy(char)
    temp = new.setdefault("baseline", {}).setdefault("temperament", {})
    for p, d in diff.get("temperament", {}).items():
        if p in PRIMARIES and isinstance(temp.get(p), dict):
            # STAMP THE AUTHORED VALUE BEFORE THE FIRST MOVE, and the order is the point. This line
            # used to write the sum straight over `mean`, so the number the author chose was gone
            # after a character's first durable event — and there was nowhere else it survived:
            # `grep '["mean"] ='` finds exactly one writer repo-wide, this one. Measured across the
            # books on disk, one character's CARE has accumulated +0.840 and saturated against
            # the clamp; what they were written as is unrecoverable. (No cast name here — hard
            # rule 1, and test_portability's token sweep caught the first draft of this comment.)
            # `mean` KEEPS holding the effective value so every reader — build_profile's decay
            # target, direct_affect's rising/settling language — is untouched. The authored copy
            # rides alongside, underscore-prefixed so `scene._strip_notes` keeps it out of the
            # actor's prompt (the same mechanism `_authored_intensity` uses for a wound, and the
            # same trap: a non-underscore spelling of that key rendered into the IDENTITY block).
            # setdefault, never assignment: re-applying a diff to an already-stamped character must
            # not re-baseline from the moved value.
            temp[p].setdefault("_authored_mean", _clamp01(temp[p].get("mean", 0.5)))
            temp[p]["mean"] = _clamp01(temp[p].get("mean", 0.5) + d)
    rels = new.setdefault("current", {}).setdefault("relationships", {})
    for tgt, axes in diff.get("relationships", {}).items():        # replay-only; see the docstring
        edge = rels.setdefault(tgt, {"trust": 0.5, "affinity": 0.5, "respect": 0.5, "debt": 0.0})
        for axis, d in axes.items():
            edge[axis] = _clamp01(edge.get(axis, 0.5) + d)
    model = new.setdefault("baseline", {}).setdefault("model", {})
    reg = model.setdefault("regard", {})
    # The same preservation for the bigotry regard, which had the same one-line erasure. A flat
    # {group: value} map has no per-entry dict to stamp into, so the authored copy is a sibling map.
    authored_reg = model.setdefault("_authored_regard", {})
    for grp, d in diff.get("regard", {}).items():
        authored_reg.setdefault(grp, _clamp01(reg.get(grp, 1.0)))
        reg[grp] = _clamp01(reg.get(grp, 1.0) + d)         # erodes toward 1.0 (or down for new disregard)
    return new

# How fast a temperament mean returns toward what the author wrote, per DECLARED unit. The SLOWEST
# thing in the engine, and the ordering is principled rather than a taste: the more cue-specific a
# quantity, the faster it fades — a wound outlasts a debt (0.995 vs 0.99) because it is more
# specific, and tonic identity is the LEAST specific thing held here, so it fades slowest of all.
# Without any erosion a fifty-year saga ends with every diff a character ever took still intact,
# which reads as machinery rather than a person. CALIBRATION.
_ERODE = 0.998


def erode(char, elapsed):
    """Time passing -> temperament means relax toward `_authored_mean`. Mutates, returns the char.

    THE WEAK SECOND RULE. Durable change is event-first: a counter-valenced event is what should
    move a baseline back, and the calendar alone should barely do anything. This is the barely.

    SYMMETRIC, so a mean pushed BELOW its authored value erodes back UP. That matters under the
    author's law: experience may take the effective value below the base, and the base is what it
    returns toward — the authored character is the asymptote, which is the whole reason
    `_authored_mean` is stamped before the first move.

    A primary with no stamp has never been moved by an arc diff, so there is nothing to return
    toward and it is left exactly alone.
    """
    if not isinstance(char, dict):
        raise RecordError("ARC_ERODE_CHAR_NOT_A_DICT", "arc.erode: char must be a dict, got %r" % type(char).__name__)
    try:
        e = max(0.0, float(elapsed))
    except (TypeError, ValueError):
        raise RecordError("ARC_ELAPSED_NOT_NUMERIC", "arc.erode: elapsed must be a number, got %r" % (elapsed,))
    if e == 0.0:
        return char
    temp = (char.get("baseline") or {}).get("temperament") or {}
    for p, row in temp.items():
        if not isinstance(row, dict) or "_authored_mean" not in row:
            continue                      # never moved, so nothing to return toward
        base = float(row["_authored_mean"])
        now = float(row.get("mean", base))
        row["mean"] = _clamp01(relax(now, base, _ERODE, e))
    return char
