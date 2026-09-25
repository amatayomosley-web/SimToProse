"""scene.py — Scene Assembly: deterministic 7-step pipeline producing the decision packet.

Normative contract: docs/scene-assembly.md (two streams, one wall; stable-prefix/volatile-body
split; excluded-by-construction; the 7-step pipeline — all deterministic, no LLM, no prose).

Public API:
    assemble(char, world, scene_slice, affect, condition, prev_affect=None) -> packet dict

Packet structure (scene-assembly.md §"The packet"):
    stable  : {persona, values, drives, model, voice}   -- byte-stable across turns
    volatile: {state, goals, percepts, recall, edges}   -- recomputed this turn
    manifest: {state_fields_read, beliefs_injected, percepts, edges}
    recall_refs: [str]  -- POSITIONAL belief refs, vault[N] (record-contract.md)
    recall_ids:  [str]  -- the same beliefs by CONTENT-derived id, parallel to recall_refs

Raises ValueError on malformed input (fail loud — no coercion).
Stdlib only. Pure functions only.
"""
import json
from .records import RecordError   # rule 6's bad-input type
import os
import sys

# Make sure gate.py is importable as a sibling module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.engine.levers import active_rows, effective, scale_to_wounds   # noqa: E402
from src.engine.toward import balance                                   # noqa: E402  (mood + attitude -> what is played)
from src.engine import rungs as _rungs                                   # noqa: E402  (the direction of travel)
from src.engine.records import PATHS                                    # noqa: E402
from src.engine.records import RELATIONSHIP_AXES      # noqa: E402  (the four axes, DERIVED not re-listed)
from src.engine.presence import (referenced_ids,      # noqa: E402  (re-exported: presence.py owns
                                 build_edges as _build_edges,      # who you are standing with)
                                 edge_from_rel as _edge_from_rel,
                                 present_ids as _witnesses_of,     # the one presence rule, for the manifest
                                 world_meant as _world_meant,      # a name means one person
                                 rels_meant as _rels_meant)
from src.engine.scene_slice import of as _slice_of     # noqa: E402  (the assembler's request, closed and typed)

from src.engine.gate import (  # noqa: E402
    perception_scope,
    extract_triggers,
    perceived_surfaces,
    run_gate,
    _display_name,
)
from src.engine import attachments as _attachments             # noqa: E402  (bond gate 5's price table — holds_of, word_of, LOC, GRP)

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

class _Reads(dict):
    """A dict that remembers which top-level keys were asked for. The decision-input manifest is
    derived from this, so it reports the packet's REAL inputs rather than a list someone kept in
    their head. Behaves as a plain dict everywhere else (json, dict(), ** — all unaffected)."""

    def __init__(self, src):
        super(_Reads, self).__init__(src or {})
        self.reads = set()

    def __getitem__(self, key):
        self.reads.add(key)
        return super(_Reads, self).__getitem__(key)

    def get(self, key, default=None):
        self.reads.add(key)
        return super(_Reads, self).get(key, default)


def assemble(char, world, scene_slice, affect, condition, prev_affect=None,
             current_turn=0, relationships=None, recall_history=None, elapsed=None,
             established=None, facts=None, injuries=None, tired=False):
    """Run the 7-step assembly pipeline for one character, one turn.

    scene-assembly.md §"The assembly pipeline (per acting character, per turn)"

    SEEDS every resting MEAN in `baseline.temperament` from its authored `rest` word (2026-09-10;
    the rest is a character-design choice beside the voice, not a genotype cell), and this is the
    one entry every driver passes through before it reads them. Idempotent; a row that carries a
    mean keeps it.

    Parameters
    ----------
    char        : dict  full character dict (fixed + baseline + current)
    world       : dict  the book's world slice (locations, people, lexicon;
                        standing_facts is ALSO present but INERT in assembly —
                        read only by the out-of-loop critic; see guide-content.md
                        "Currently INERT")
    scene_slice : the assembler's request - a `scene_slice.SceneSlice`, or a dict the door (`scene_slice.of`)
                  makes one of: every key a caller may pass is declared there, and an undeclared one is
                  refused (gate slice-contract). Caller-constructed ground truth; the pipeline perceives FROM it
    affect      : dict  {path: float} current affect, the paths of `records.PATHS`
    condition   : dict  {energy, allostatic_load, ...}
    established : list  what is ESTABLISHED about the beat's subjects (`read_api.established`
                        rows: {subject, authored, kept, open}) — the fence the actor is handed
                        with the lore licence (2026-09-11). The driver reads it from the
                        chronicle; the packet only carries it. Absent -> nothing is established
                        and the prompt says so.

    Returns dict with keys: stable, volatile, manifest, recall_refs, recall_ids.
    Raises ValueError on any malformed input.
    """
    # ---- input validation (fail loud) ----
    if not isinstance(char, dict):
        raise RecordError("SCENE_CHAR_NOT_AN_OBJECT", "assemble: char must be a dict")
    for section in ("fixed", "baseline", "current"):
        if section not in char:
            raise RecordError("SCENE_CHAR_SECTION_MISSING",
                              "assemble: char missing section %r" % section)
    _her.ensure_temperament(char)           # rest words -> resting means, once, idempotent
    if not isinstance(world, dict):
        raise RecordError("SCENE_WORLD_NOT_AN_OBJECT", "assemble: world must be a dict")
    s = _slice_of(scene_slice)               # THE ONE DOOR (gate slice-contract): a closed, typed record, or a refusal
    if not isinstance(affect, dict):
        raise RecordError("SCENE_AFFECT_NOT_AN_OBJECT", "assemble: affect must be a dict")
    if not isinstance(condition, dict):
        raise RecordError("SCENE_CONDITION_NOT_AN_OBJECT", "assemble: condition must be a dict")

    fixed    = char["fixed"]
    # RECORDED, not hand-listed. `state_fields_read` below used to be a literal list of six field
    # names maintained by whoever last added a read — and it had already rotted: the per-primitive
    # `current.targets` tier landed with no manifest row, so the audit trail said the packet was
    # built from something it was not. That is the same defect class as `_KNOWN_DIMS` and the
    # by-hand verify block. The wrapper records what assemble ACTUALLY touches, including reads
    # inside the helpers it hands these dicts to, so the manifest cannot disagree with the code.
    baseline = _Reads(char["baseline"])
    current  = _Reads(char["current"])
    skills   = baseline.get("skills", {})
    vault    = current.get("vault", [])
    goals    = current.get("active_goals", [])

    # ---- Step 1: Scene slice (caller-provided ground truth; not yet injected) ----
    # Nothing to do here — scene_slice is the ground truth from the caller.
    # We NEVER inject raw scene_slice into the packet; the perception wall does the scoping.

    # ---- Step 2: Perception scope (perception-mode wall) ----
    # Filter scene_slice to what this character apprehends.
    # Gated by perception/insight skill checks. Failed check = absent from PerceptSet.
    # A NAME MEANS ONE PERSON (gate one-person-per-name): the people this scene's names do not mean, as the driver
    # resolved them (presence.one_per_name), are not among the people it perceives by name or stands with. Absent: all.
    elsewhere = s.elsewhere
    world = _world_meant(world, elsewhere)
    percepts = perception_scope(s, world, skills, condition, _rels_meant(current.get("relationships"), elsewhere),
                                me=str(fixed.get("id") or fixed.get("name") or "").lower(),
                                tired=tired)          # a worn mind's eye dims the room's subtle cues (gate tired-lexicon)

    # ---- Step 3: Trigger extraction (from PerceptSet ONLY — never from ground truth) ----
    # scene-assembly.md: "You cannot be triggered by what you didn't perceive."
    triggers = extract_triggers(percepts)

    # ---- Step 4: Recall pass ----
    # Run the gate: trigger-match -> vault -> goal-salience -> energy budget.
    # All four decay args, or decay is inert: this passed five of nine until 2026-09-04.
    recall_entries = run_gate(triggers, vault, skills, goals, condition, elapsed=elapsed,
                              current_turn=current_turn, recall_history=recall_history,
                              relationships=relationships or current.get("relationships", {}))

    # ---- Step 5: Assemble the packet ----
    # scene-assembly.md §"The packet": stable prefix + volatile body + manifest.

    # -- 5a: Stable prefix (identity — changes rarely; cacheable across turns)
    # Built ONLY from fixed + baseline. No volatile/current data allowed here.
    # Byte-stable: same char dict -> identical json.dumps output.
    # Sort all nested dicts for determinism (scene-assembly.md §"stable-prefix stability").
    stable = _build_stable(fixed, baseline)

    # -- 5b: Volatile body (recomputed this turn)
    volatile = {
        "state":    {
            "affect":           dict(affect),     # Layer-7 state (scene-assembly.md audit B8)
            "condition":        dict(condition),
            # what each primitive is ABOUT (emotion-basis.md per-primary targets). Rides the packet
            # so the renderer could pick the reflexive variant without a signature change (retired); empty
            # for a character no run has targeted yet, which renders exactly as it did before.
            "targets":          dict(current.get("targets") or {}),
        },
        "goals":   list(goals),
        "percepts": [_percept_for_packet(p) for p in percepts],
        "recall":   [_recall_for_packet(r) for r in recall_entries],
        "edges":    _build_edges(current, percepts, world, elsewhere),
        # WHAT IS YOURS HERE (bond gate `attachments-to-actor`, bond-arithmetic.md s7): the held
        # entities THIS TURN puts in scope — present as a percept or named as the beat's own
        # subject — priced to a relation word by attachments.word_of. Empty for a character with
        # no attachments, or none of them in scope this turn; direction.direct_holds renders it.
        "holds":    _build_holds(current, percepts, world, s),
        # THE FENCE (2026-09-11): binding facts about who and what is here, so the actor may invent
        # beyond them and not against them. Rows pass through unchanged; the prompt renders them.
        "established": [dict(r) for r in (established or []) if isinstance(r, dict)],
        # WHAT HAS HAPPENED HERE (gate `scene-facts-to-actor`, 2026-09-22): the facts of this run
        # that THIS character witnessed, most recent first. The POV filtering is `scene_facts`'
        # job and is done before the rows arrive — assembly passes them through unchanged, the way
        # it does the fence, because a filter applied twice in two places is a filter that will
        # disagree with itself. `direction.direct_facts` renders them.
        "facts": [dict(r) for r in (facts or []) if isinstance(r, dict)],
    }
    # WHO IS HURT (gate injuries): rows `injuries.for_actor` already filtered and aged, passed through the way the
    # facts are. The key exists only for a book that runs the system, so every other packet is unchanged.
    if injuries is not None:
        volatile["injuries"] = [dict(r) for r in injuries if isinstance(r, dict)]

    # -- 5b-ii: TIER 3, the effective levers (state-engine.md:11-12, decision-engine.md:66-85).
    # The catalog applies on the STANDING FACT where appraise() fires on the CHANGE. Rows match
    # only what this character can actually perceive this turn -- the event surface, and edges to
    # parties PRESENT -- so a condition can never fire on someone who is not in the room.
    # With no authored catalog this is the IDENTITY: effective == affect, and every run predating
    # the tier reproduces byte-identically.
    _edges  = {e.get("target"): e for e in volatile["edges"] if e.get("target")}
    _target = s.event.get("target") or s.target
    _ctx = {
        "text":      s.event["text"],
        "edges":     _edges,
        "affect":    dict(affect),
        "condition": dict(condition),
        # WHO this event is ABOUT, distinct from who is merely present -- a `target_edge` row
        # fires on the disposition toward the subject, not toward the room.
        "target":    _target,
    }
    # THE SUBJECT MAY NOT BE IN THE ROOM. `edges` is present-only, so a subject merely spoken of
    # carries no edge and every `target_edge` row keyed to them would silently stop firing. Build
    # one from their sheet row, separately, so aboutness and presence stay different questions.
    if _target and _target not in _edges:
        _rel = (current.get("relationships") or {}).get(_target)
        if isinstance(_rel, dict):
            _ctx["subject_edge"] = _edge_from_rel(_target, _rel)
    _fired = active_rows(baseline.get("catalog"), _ctx)
    # A ROW THAT NAMES A WOUND IS SCALED BY WHAT REMAINS OF IT. Until this call the two authored
    # numbers -- the wound's `intensity` and the row's `magnitude` -- were unconnected, so a
    # character's phobia could fade in the prose the actor reads while hitting the arithmetic
    # exactly as hard as the day it was authored. Rows that name no wound pass through untouched,
    # which is every row in every book authored before this line existed.
    _fired = scale_to_wounds(_fired, baseline.get("wounds") or [])   # engine wounds (gate three)
    # THE BALANCE (2026-09-12, the redesign's gate 1). The stored float is the MOOD; `current.toward`
    # is ATTITUDE, what each person has earned; what the actor plays is COMPOSED here each beat and
    # never stored: toward the ENGAGED person, their attitude if it is above the mood, else halfway
    # down from the mood and never below rest; others present may lift a path, damped. Until this
    # line the person's vector was ADDED onto the mood as lever rows, which counted a bound reading
    # twice while that person was in the room — measured on a generated scene, the composer two
    # rungs above the stored state. WHO IS ENGAGED: the driver's say (`scene_slice["engaged"]`, the
    # last speaker), else the moment's subject when it is another person, else the sole other
    # person present, else nobody — and then effective == mood, the identity.
    _me = str(fixed.get("id") or fixed.get("name") or "").lower()
    _present_ids = [str(k) for k in _edges]
    _engaged = s.engaged
    if not _engaged or _engaged == _me:
        _engaged = _target if (_target and str(_target) != _me
                               and not str(_target).startswith("concept:")) else ""
    if not _engaged and len([w for w in _present_ids if w != _me]) == 1:
        _engaged = [w for w in _present_ids if w != _me][0]
    _rest = {p: float(baseline["temperament"][p]["mean"]) for p in PATHS}
    _composed, _stirs, _origin = balance(affect, current.get("toward") or {}, _rest,
                                engaged=_engaged, present=_present_ids, me=_me,
                                # WHOM THE MOOD CAME FROM meets it in full. The driver reads it off the
                                # log (`ledger.raised_by`: the last reading per path); `current.targets`
                                # is the fallback for a slice with no run behind it, and it clears at rest.
                                targets=(s.raised_by if s.raised_by is not None
                                         else current.get("targets") or {}))
    for _e in volatile["edges"]:
        _sv = _stirs.get(str(_e.get("target")))
        if _sv:
            _e["stirs"] = dict(_sv)                 # rendered by direction.direct_stirs, in words
    volatile["state"]["effective"] = effective(_composed, _fired)
    volatile["state"]["engaged"] = _engaged
    # THE DIRECTION OF TRAVEL (the redesign's gate 3). Per built path, is the MOOD coming down from
    # above its pivot? Decided here, once, from three things the drivers hand in beside `raised_by`:
    # which branch set the value (`_origin`, from the balance), when each path was last read
    # (`last_read_turn`) and the actor's last committed beat (`last_turn`) — both off the log.
    # `rungs.block_for` swaps to the descent block only when this is True AND the composed rung is
    # above the pivot. A slice with no run behind it (tests, --fixture) carries neither key and
    # reads "no fuel", which changes nothing while every mood sits below its pivot.
    volatile["state"]["descending"] = _rungs.descending(
        affect, _origin, s.last_read_turn, s.last_turn)
    # SLOPE — last turn's affect, so the direction can say how fast this came on. An ARGUMENT like
    # affect/condition: injecting it post-assembly put an input the manifest could not name.
    if prev_affect:
        volatile["state"]["previous"] = dict(prev_affect)
    # Auditable like every other decision input: the ROWS are the trace, so the effective vector
    # stays re-derivable from the committed current tier without ever being committed itself.
    volatile["levers"] = [dict(r) for r in _fired]

    # -- 5c: Manifest (record-contract.md: decision-input manifest with REAL refs)
    percept_refs = [p.get("ref", "") for p in percepts]
    recall_refs  = [r.get("ref", "") for r in recall_entries]
    # A SECOND, PARALLEL list — never folded into recall_refs, whose contract is that it matches the
    # volatile recall entries' refs exactly (tests/test_scene.py "recall-refs-key-matches-volatile";
    # a first attempt at this change overloaded that field and the guard caught it).
    #
    # `vault[N]` is POSITIONAL: it names a belief only within the note revision that produced it.
    # `recall_events` is append-only and trigger-protected, so a row written with the positional
    # form alone can never be corrected once an author adds a bullet above the entry — and the Beck
    # Hollow chronicle already spans two bible fingerprints, so its stored vault[N] strings are
    # ALREADY ambiguous. The content-derived id stops that accruing from here. See gate.belief_id.
    recall_ids   = [r.get("bid", "") for r in recall_entries]
    edge_refs    = [e.get("target", "") for e in volatile["edges"]]
    # THE HELD ENTITIES THIS TURN KEPT IN SCOPE, beside edges for the same reason: the manifest
    # names every real input the packet rendered, and `volatile["holds"]` is one now.
    holds_refs   = [h.get("entity", "") for h in volatile["holds"]]

    manifest = {
        # affect/condition arrive as ARGUMENTS, not reads, so they are named explicitly; everything
        # else is whatever the code actually asked `current`/`baseline` for.
        "state_fields_read":  sorted(
            {"current.affect", "current.condition"}
            | ({"current.previous_affect"} if prev_affect else set())
            | {"current.%s" % k for k in current.reads}
            | {"baseline.%s" % k for k in baseline.reads}),
        "beliefs_injected": len(recall_entries),
        # THE PERCEIVED TRIGGER SET, published because a consumer outside this module now needs it.
        # `wound.trial` matches against THIS, never the ground-truth event text: the gate's own rule
        # is "you cannot be triggered by what you didn't perceive", and a wound that moved on
        # something withheld from its owner would be the sharpest version of that failure.
        # It was already computed here for the recall gate and thrown away.
        "triggers":          list(triggers),
        # THE UNSHREDDED VIEW, for matching AUTHORED phrases. `triggers` above is the word bag the
        # recall gate wants; a wound's trigger is a phrase an author wrote, and the two need
        # different readings of the same percepts. Both walk the identical PerceptSet, so the
        # perception wall holds for each.
        "surfaces":          list(perceived_surfaces(percepts)),
        "levers_fired":      [r.get("source", "") for r in volatile["levers"]],
        "percepts":          percept_refs,
        "edges":             edge_refs,
        "holds":             holds_refs,
        "established":       [str(r.get("subject", "")) for r in volatile["established"]],
        # The manifest RECORDS its reads (`_Reads`), so a fact that reached the actor is auditable
        # by kind and turn without reproducing the quote in a second place.
        "facts":             ["%s@%s" % (r.get("kind"), r.get("turn")) for r in volatile["facts"]],
        # WHO WAS HERE FOR THIS BEAT (gate `scene-facts-fix`, 2026-09-22). `percepts` above records
        # refs and drops each percept's `present` flag, so someone merely SPOKEN OF is
        # indistinguishable there from someone in the room — and the fact ledger read it that way
        # and handed a man four facts from a room he never entered. This is the same rule
        # `build_edges` applies, from the same function, recorded so a later reader need not guess.
        # NULL when the caller tracks no presence (a slice with no `present` key: the chair). Under the
        # one presence rule an untracked percept counts as present, which is right for who you stand
        # with and wrong for who WITNESSED a beat: recorded as a list it made anyone merely named in
        # the chair a witness to its facts. Null is read as "the speaker alone" (gate resume-and-parity).
        "present":           _witnesses_of(percepts) if s.present is not None else None,
    }

    # ---- Steps 6 + 7 deferred to the integrator ----
    # Step 6: Hand to decision engine — the integrator builds the LLM prompt from this packet.
    # Step 7: Couple back (acquisition events logged by the integrator's ledger commit).

    return {
        "stable":      stable,
        "volatile":    volatile,
        "manifest":    manifest,
        "recall_refs": recall_refs,
        "recall_ids":  recall_ids,
    }


# ---------------------------------------------------------------------------
# Stable prefix builder
# ---------------------------------------------------------------------------

def _wounds_for_prefix(wounds):
    """baseline.wounds -> the part of each the actor may be told. Pure; a new list."""
    out = []
    for w in wounds if isinstance(wounds, list) else []:
        if not isinstance(w, dict) or not w.get("concept"):
            continue
        row = {"concept": str(w["concept"]), "path": str(w.get("path", "")), "intensity": w.get("intensity", 0.0)}
        if w.get("text"):
            row["what happened"] = str(w["text"])
        if w.get("trigger"):
            row["what sets it off"] = [str(t) for t in w["trigger"]]
        out.append(row)
    return sorted(out, key=lambda r: (r["concept"], r["path"]))


def _rest_words(temperament):
    """{path: {"rest": word}} for every path whose authored rest is a WORD; numbers stay home."""
    out = {}
    if not isinstance(temperament, dict):
        return out
    for p, row in temperament.items():
        if isinstance(row, dict) and isinstance(row.get("rest"), str):
            out[p] = {"rest": row["rest"]}
    return out


def _build_stable(fixed, baseline):
    """Build the stable identity prefix from fixed + baseline only.

    scene-assembly.md §"Stable prefix": persona / disposition / values / drives /
    the Model / voice. Built from fixed+baseline; NO volatile data ever goes here.
    Sort keys so json.dumps is byte-identical for the same inputs.
    """
    drives_raw = baseline.get("drives", {})
    # Exclude wounds/fears from the stable prefix? No — they are baseline-level character
    # identity (authored at character creation). Include them in full.
    # The stable prefix is the Layer 1·3·5 operands:
    #   Layer 1: Persona (who they are — fixed)
    #   Layer 3: Values/Model (schwartz, moral_foundations, needs, resolution_priority)
    #   Layer 5: Drives/goals/orientation (baseline level — not current active_goals which are volatile)

    stable = {
        "persona": {
            "id":       fixed.get("id"),
            "name":     fixed.get("name"),
            "people":   fixed.get("people"),
            "position": _sort_nested(fixed.get("position", {})),
        },
        "drives":     _sort_nested(_strip_notes(_manner_drives(drives_raw))),
        "voice":      _sort_nested(_strip_notes(baseline.get("voice", {}))),
        # THE WOUNDS (gate three, 2026-09-11): engine state, keyed concept + path, rendered by
        # `direct_identity` into "what has marked you" — what happened (the beat or the profile),
        # what it is about (the concept's gloss), how it takes them (the intensity banded), what
        # sets it off (the perceived words). The intensity NUMBER travels here and is banded by
        # the renderer, exactly as a goal's priority is; the concept id is turned into its gloss.
        "wounds":     _wounds_for_prefix(baseline.get("wounds") or []),
        # RESTORED 2026-09-09, by owner ruling: the character sheet is what defines who the
        # character IS, so the assembler does not get to decide which parts of them reach a scene.
        #
        # Removed 2026-09-06 with genotype/model/provenance under one argument -- see the comment
        # below -- and that removal silently falsified a DOCUMENTED PROMISE. BLUEPRINT-character.md
        # section 7.3 has an author circle one of four sentences per facet and says in bold they are
        # "word for word, the sentences the actor will be shown", citing identity_view by line. The
        # suite stayed green throughout, because nothing asserts what the identity prefix CONTAINS.
        #
        # `direct_identity` renders this into `disposition` and pops the raw block, so no number
        # reaches the prompt (tests/test_no_digits.py is the guard). It reads `mean` only -- an
        # authored `note` beside a facet is dropped HERE, by the renderer, and still does not reach
        # the actor. Recorded in the gate; not fixed by this change.
        "traits":     _sort_nested(baseline.get("traits", {})),
        # THE REST WORDS (2026-09-10, owner: temperament is a character design question, beside
        # the voice). Only the authored WORD per path travels — never the seeded mean, which is a
        # number the sweep in `direct_identity` would refuse — and `direct_identity` renders each
        # into a sentence under `disposition`, beside the trait sentences, then pops the block.
        # A rest authored as a NUMBER has no phrase and does not travel at all.
        "temperament": _sort_nested(_rest_words(baseline.get("temperament", {}))),
        # RESTORED 2026-09-09, same owner ruling, same day, one step further: a person knows
        # their own constitution. `direct_identity` renders this as "how you are built" from
        # `_ALLELE_PHRASES` and pops the raw alleles, so no allele word reaches the prompt.
        #
        # THIS IS THE SHARPEST FORM OF THE 2026-09-06 ARGUMENT AND IT IS NOT ANSWERED HERE.
        # An allele maps onto ONE named primary's gain -- anger_proneness sets DISPLEASURE
        # gain -- so "it takes a great deal to make you angry" is a claim about DISPLEASURE,
        # and the DISPLEASURE rung block is also a claim about DISPLEASURE. Those are nearer
        # to the same claim than any trait phrase was. Whether an actor holding both plays a
        # rung SOFTER than the rung says is empirical; the falsifier is blind actors on one
        # rung block with and without this prefix. Owner ruled the sheet defines the
        # character; the risk is recorded, not waved off.
        "genotype":   _sort_nested(fixed.get("genotype", {})),
    }
    return _sort_nested(stable)


# THE FIELDS BELOW ARE RATES, AND A RATE IS SPENT ONCE. `state.build_profile` reads `genotype`,
# the trait means and the worth menu and turns them into gains, relevance and regard — they are how
# hard an event moves this person. Until 2026-09-06 the SAME fields were also written into the
# prefix and rendered to the actor as sentences, from tables `identity_view` itself calls
# "reactivity rather than configuration". So a character was damped once in the arithmetic and
# again in the prose, and a rung stopped meaning the same thing for two people — which is the one
# property the shared scale cannot lose.
#
# WHAT STAYS is manner and biography: who he is, how he sounds, what he is trying to do, what was
# done to him. None of those make a claim the state layer also makes; a laconic man is laconic at
# every rung. `direct_identity` keeps its renderers for the cut blocks on purpose — its docstring
# records that silently dropping a field is worse than leaking one, and the sweep that refuses an
# unphrased number lives with them.
_CUT_FROM_PREFIX = ("genotype", "traits", "model", "provenance")

# Inside `drives`, the same line: the goal and the wound are what happened, and the rest is the
# resolver's weights said out loud. `priority` and `satisfaction` are the resolver; `trigger`,
# `avoidance` and `defense` pre-decide conduct the rung owns; `orientation` is a routing bias.
# `fears_wounds` LEFT THIS TABLE 2026-09-11: a wound is engine state at `baseline.wounds` (gate
# three) and reaches the actor through `_build_stable`'s `wounds` block, never as sheet prose.
_DRIVE_KEEP = {"goals": ("goal",)}


def _manner_drives(drives):
    """baseline.drives -> the part of it that is biography rather than rate. Pure.

    Returns a NEW dict; the caller's is never touched. An unknown top-level key is DROPPED rather
    than carried, and that is the opposite of `direct_identity`'s rule for a reason: this function
    decides what a character may be told about itself, so an unrecognised field must not reach the
    actor by default. A new drives block is a deliberate decision, not an accident of merging.
    """
    if not isinstance(drives, dict):
        return {}
    out = {}
    for block, keep in _DRIVE_KEEP.items():
        rows = drives.get(block)
        if not isinstance(rows, list):
            continue
        kept = [{k: r[k] for k in keep if isinstance(r, dict) and k in r} for r in rows]
        kept = [r for r in kept if r]
        if kept:
            out[block] = kept
    return out


def _strip_notes(obj):
    """Remove authoring metadata from the identity prefix: any key named 'note' or starting with
    '_' (design rationale, notes naming the engine module that reads a field, arc foreshadowing about
    where a value is headed). Recursive; pure. The substrate (numbers, structure) stays — only the
    commentary ABOUT it is removed, so none of it reaches the prompt. (gate swe-prompt-hygiene-strip-notes)
    """
    if isinstance(obj, dict):
        return {k: _strip_notes(v) for k, v in obj.items()
                if not (str(k) == "note" or str(k).startswith("_"))}
    if isinstance(obj, list):
        return [_strip_notes(x) for x in obj]
    return obj


# The allele token without its authored parenthetical; the rationale must not reach the prompt.
# `heritable.word` is THE reading — this file held the fourth independent copy of that parse.
from .heritable import word as _allele_word                             # noqa: E402
from . import heritable as _her                                         # noqa: E402  (temperament seed)


def _sort_nested(obj):
    """Recursively sort dict keys for byte-stable json.dumps.
    scene-assembly.md §"stable-prefix stability": same char dict -> identical bytes.

    There were TWO definitions of this, the first with a broken comprehension referencing an
    undefined name and unreachable code after it, the second silently shadowing it — with a comment
    saying "Fix: replace the double-comprehension bug above" left in place beside both. Only the
    second ever ran. The dead one is gone; found 2026-09-01 while looking for something to split.
    """
    if isinstance(obj, dict):
        return {k: _sort_nested(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_sort_nested(x) for x in obj]
    return obj


# ---------------------------------------------------------------------------
# Packet formatters
# ---------------------------------------------------------------------------

def _percept_for_packet(p):
    """Format a percept for the volatile.percepts list.
    Include only the structured fields defined in scene-assembly.md.
    """
    out = {
        "ref":        p.get("ref"),
        "channel":    p.get("channel"),
        "fidelity":   p.get("fidelity"),
        "attributes": list(p.get("attributes", [])),
    }
    if p.get("must_surface"):
        out["must_surface"] = True
    if "recognized_as" in p:
        out["recognized_as"] = p["recognized_as"]
    # PRESENT reaches the actor, because the actor is the one who has to decide whether the moment
    # is ABOUT the person who is not here. Absent entirely when the caller does not track presence.
    if "present" in p:
        out["present"] = p["present"]
    return out


def _recall_for_packet(r):
    """Format a recall entry for volatile.recall, preserving epistemic stance."""
    out = {
        "ref":        r.get("ref"),
        "claim":      r.get("claim"),
        "confidence": r.get("confidence_eff", r.get("confidence")),
        "provenance": r.get("provenance"),
    }
    if r.get("target_actor"): out["target_actor"] = r["target_actor"]
    if r.get("epistemic_stance"): out["epistemic_stance"] = r["epistemic_stance"]
    return out


def _holds_display_name(entity, world):
    """One held entity's key -> the world's display line for it. A `loc.` key reads
    `world.locations`: its `name` when authored, else its `what` line, else the id's own tail. A
    `grp.` key has no registry beyond the tag `people[].groups` already carries, so it renders as
    the tag — the same tail a `loc.` key falls back to when the world does not resolve it."""
    if entity.startswith(_attachments.LOC):
        lid = entity[len(_attachments.LOC):]
        for loc in (world.get("locations") or []):
            if isinstance(loc, dict) and str(loc.get("id") or "") == lid:
                return str(loc.get("name") or loc.get("what") or lid)
        return lid
    if entity.startswith(_attachments.GRP):
        return entity[len(_attachments.GRP):]
    return entity


def _build_holds(current, percepts, world, s):
    """`current.attachments`'s `+` entries -> what the actor is shown he holds this turn.

    Kept when the entity is something THIS TURN's PerceptSet actually contains (a `loc.` ref,
    gate.py's own percept namespace) or is the beat's own subject/target (the slice's event's
    own `target`, else the slice's) — held elsewhere, off the page, stays off the page, the same
    rule presence.py already applies to a person who is neither present nor spoken of. No `grp.`
    percept exists (this gate's own OMISSION), so a group only ever qualifies through the second
    branch; the first is structurally closed to it.

    Sorted by entity (hard rule 4 — `_build_edges` paid for the hash-order version of this bug
    once, in this file). Skips an entity whose hold prices below `attachments.word_of`'s floor: a
    hold that faint has nothing to tell the actor, which is a fact about the hold, not a malformed
    row, so ATTACH_HOLD_UNWORDED is swallowed here and nowhere else.
    """
    holds = _attachments.holds_of(current.get("attachments"))
    if not holds:
        return []
    refs = {str(p.get("ref", "")).strip().lower() for p in (percepts or [])}
    subject = str(s.event.get("target") or s.target or "").strip().lower()
    rows = []
    for entity, hold in holds.items():
        key = str(entity).strip().lower()
        if key not in refs and key != subject:
            continue
        try:
            word = _attachments.word_of(hold)
        except RecordError as exc:
            if exc.code != "ATTACH_HOLD_UNWORDED":
                raise
            continue
        rows.append({"entity": str(entity), "name": _holds_display_name(str(entity), world), "word": word})
    return sorted(rows, key=lambda r: r["entity"])


def subject_groups(world):
    """Build the entity-id -> [group] index from the book's people registry.

    Group membership is authored content (person-note `groups`); load_book folds it into
    world["people"]. This index is how an event's SUBJECT acquires a class an appraiser can
    (dis)regard. Pure; rebuilt once per run (world is static). Raises on a non-dict world."""
    if not isinstance(world, dict):
        raise RecordError("SCENE_WORLD_NOT_AN_OBJECT", "subject_groups: world must be a dict")
    index = {}
    for p in world.get("people", []):
        if isinstance(p, dict) and p.get("id"):
            groups = p.get("groups", [])
            if isinstance(groups, list) and groups:
                index[p["id"]] = [str(g) for g in groups]
    return index


def norm_id(value):
    """An actor's spelling of an entity id -> the bare id the engine matches on.

    THE ACTOR IS NEVER SHOWN THE FORM THE ENGINE WANTS. The prompt instructs "copy its id exactly"
    while displaying only the capitalised display name (from the edges line) and the percept ref
    (`entity.<id>`); the bare lowercase id the matchers compare against appears nowhere. Measured
    on a live two-hander: one actor emitted the display name, the other the percept ref, and
    neither matched. Both still resolved — but only because `resolve_subject`'s single-party
    fallback fires when exactly one other person is present, which is always true in a two-hander
    and never guaranteed after. The addressee matcher has no such fallback, so it simply failed
    and the scene lulled.

    Accepting all three spellings is the smaller change than altering what the percept refs look
    like, since those refs are a stable shape other code consumes.
    """
    s = str(value or "").strip()
    if not s:
        return ""
    if "." in s:                      # percept refs are `<kind>.<id>` — entity.x, prop.y, loc.z
        s = s.rsplit(".", 1)[1]
    return s.strip().lower().replace(" ", "_")


def resolve_subject(edges, groups_index, named=None, referenced=()):
    """Who is this turn's event about, and what class are they? -> (target_id|None, target_group|None).

    Policy (deterministic, no LLM in here — the LLM's only input is `named`, its own reading):
      1. a NAMED subject the actor can actually see (in `edges`) wins — handles multi-party scenes;
      2. else a NAMED subject the actor was told about (`referenced`) — someone spoken of, not here;
      3. else, if exactly ONE party is present, it is the unambiguous subject;
      4. else (none present, or several with no name) -> (None, None): no single subject, so
         appraisal's regard factor stays 1.0 and the event is empathy-unscaled.

    RULE 2 IS WHY THIS FUNCTION GREW A PARAMETER. Aboutness and presence are different questions,
    and deriving the first from `edges` alone made them the same one: the news that a man elsewhere
    has ruined you could only be ABOUT the messenger who brought it. Measured on a live walk — every
    passage exempted the man in the room, and the anger had nowhere to go but out the door.

    RULE 3 DELIBERATELY IGNORES `referenced`. Someone absent is NAMEABLE, never the default: a
    character alone with one other person still means that person unless the actor says otherwise.
    A name in neither set still drops to the fallback — the invention guard is unchanged.

    The group is resolved from the registry, never from `named`. Multi-group entities use the
    PRIMARY (first) group (v1 — no lowest-regard arbitration yet). Raises on malformed structure."""
    if not isinstance(edges, list) or not isinstance(groups_index, dict):
        raise RecordError("SCENE_SUBJECT_INPUTS_INVALID", "resolve_subject: edges must be a list and groups_index a dict")
    present = [e.get("target") for e in edges if isinstance(e, dict) and e.get("target")]
    present_set = set(present)
    target = None
    named_id = norm_id(named)
    by_norm = {norm_id(p): p for p in present}
    ref_by_norm = {norm_id(r): str(r) for r in (referenced or ()) if r}
    if named_id and named_id in by_norm:           # the actor named someone it can see -> trust it
        target = by_norm[named_id]
    elif named_id and named_id in ref_by_norm:     # named someone spoken of but not in the room
        target = ref_by_norm[named_id]
    elif len(present_set) == 1:                     # exactly one party present -> unambiguous subject
        target = present[0]
    group = None
    if target is not None:
        groups = groups_index.get(target, [])
        group = groups[0] if groups else None       # primary group; None -> not a regarded class
    return target, group
