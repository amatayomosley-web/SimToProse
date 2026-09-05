"""scene.py — Scene Assembly: deterministic 7-step pipeline producing the decision packet.

Normative contract: docs/scene-assembly.md (two streams, one wall; stable-prefix/volatile-body
split; excluded-by-construction; the 7-step pipeline — all deterministic, no LLM, no prose).

Public API:
    assemble(char, world, scene_slice, affect, condition) -> packet dict

Packet structure (scene-assembly.md §"The packet"):
    stable  : {persona, values, drives, model, voice}   -- byte-stable across turns
    volatile: {state, goals, percepts, recall, edges}   -- recomputed this turn
    manifest: {state_fields_read, beliefs_injected, percepts, edges}
    recall_refs: [str]  -- belief refs for the ledger (record-contract.md)

Raises ValueError on malformed input (fail loud — no coercion).
Stdlib only. Pure functions only.
"""
import json
import os
import sys

# Make sure gate.py is importable as a sibling module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.engine.levers import active_rows, effective   # noqa: E402
from src.engine.records import RELATIONSHIP_AXES      # noqa: E402  (the four axes, DERIVED not re-listed)
from src.engine.gate import (  # noqa: E402
    perception_scope,
    extract_triggers,
    run_gate,
    _display_name,
)
from .errors import EngineError
from . import heritable

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


def assemble(char, world, scene_slice, affect, condition):
    """Run the 7-step assembly pipeline for one character, one turn.

    scene-assembly.md §"The assembly pipeline (per acting character, per turn)"

    Parameters
    ----------
    char        : dict  full character dict (fixed + baseline + current)
    world       : dict  the book's world slice (locations, people, lexicon;
                        standing_facts is ALSO present but INERT in assembly —
                        read only by the out-of-loop critic; see guide-content.md
                        "Currently INERT")
    scene_slice : dict  {event: {text, kind}, recent: [...], location: str|None}
                        caller-constructed ground truth; the pipeline perceives FROM it
    affect      : dict  {primary: float} current affect (7 primaries)
    condition   : dict  {energy, allostatic_load, ...}

    Returns dict with keys: stable, volatile, manifest, recall_refs.
    Raises ValueError on any malformed input.
    """
    # ---- input validation (fail loud) ----
    if not isinstance(char, dict):
        raise EngineError("SCENE_ASSEMBLE_CHAR_NOT_A_DICT", "assemble: char must be a dict")
    for section in ("fixed", "baseline", "current"):
        if section not in char:
            raise EngineError("SCENE_ASSEMBLE_CHAR_MISSING_SECTION", "assemble: char missing section %r" % section)
    if not isinstance(world, dict):
        raise EngineError("SCENE_ASSEMBLE_WORLD_NOT_A_DICT", "assemble: world must be a dict")
    if not isinstance(scene_slice, dict):
        raise EngineError("SCENE_ASSEMBLE_SCENE_SLICE_NOT_A_DICT", "assemble: scene_slice must be a dict")
    if "event" not in scene_slice or not isinstance(scene_slice["event"], dict):
        raise EngineError("SCENE_ASSEMBLE_SCENE_SLICE_NO_EVENT", "assemble: scene_slice must have 'event' dict")
    if "text" not in scene_slice["event"]:
        raise EngineError("SCENE_ASSEMBLE_EVENT_NO_TEXT", "assemble: scene_slice.event must have 'text'")
    if not isinstance(affect, dict):
        raise EngineError("SCENE_ASSEMBLE_AFFECT_NOT_A_DICT", "assemble: affect must be a dict")
    if not isinstance(condition, dict):
        raise EngineError("SCENE_ASSEMBLE_CONDITION_NOT_A_DICT", "assemble: condition must be a dict")

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
    percepts = perception_scope(scene_slice, world, skills, condition, current.get("relationships", {}))

    # ---- Step 3: Trigger extraction (from PerceptSet ONLY — never from ground truth) ----
    # scene-assembly.md: "You cannot be triggered by what you didn't perceive."
    triggers = extract_triggers(percepts)

    # ---- Step 4: Recall pass ----
    # Run the gate: trigger-match -> vault -> goal-salience -> energy budget.
    recall_entries = run_gate(triggers, vault, skills, goals, condition)

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
            # so `direct_affect` can pick the reflexive variant without a signature change; empty
            # for a character no run has targeted yet, which renders exactly as it did before.
            "targets":          dict(current.get("targets") or {}),
        },
        "goals":   list(goals),
        "percepts": [_percept_for_packet(p) for p in percepts],
        "recall":   [_recall_for_packet(r) for r in recall_entries],
        "edges":    _build_edges(current, percepts, world),
    }

    # -- 5b-ii: TIER 3, the effective levers (state-engine.md:11-12, decision-engine.md:66-85).
    # The catalog applies on the STANDING FACT where appraise() fires on the CHANGE. Rows match
    # only what this character can actually perceive this turn -- the event surface, and edges to
    # parties PRESENT -- so a condition can never fire on someone who is not in the room.
    # With no authored catalog this is the IDENTITY: effective == affect, and every run predating
    # the tier reproduces byte-identically.
    _ctx = {
        "text":      scene_slice["event"].get("text", ""),
        "edges":     {e.get("target"): e for e in volatile["edges"] if e.get("target")},
        "affect":    dict(affect),
        "condition": dict(condition),
        # WHO this event is ABOUT, distinct from who is merely present -- a `target_edge` row
        # fires on the disposition toward the subject, not toward the room.
        "target":    scene_slice["event"].get("target") or scene_slice.get("target"),
    }
    _fired = active_rows(baseline.get("catalog"), _ctx)
    volatile["state"]["effective"] = effective(affect, _fired)
    # Auditable like every other decision input: the ROWS are the trace, so the effective vector
    # stays re-derivable from the committed current tier without ever being committed itself.
    volatile["levers"] = [dict(r) for r in _fired]

    # -- 5c: Manifest (record-contract.md: decision-input manifest with REAL refs)
    percept_refs = [p.get("ref", "") for p in percepts]
    recall_refs  = [r.get("ref", "") for r in recall_entries]
    edge_refs    = [e.get("target", "") for e in volatile["edges"]]

    manifest = {
        # affect/condition arrive as ARGUMENTS, not reads, so they are named explicitly; everything
        # else is whatever the code actually asked `current`/`baseline` for.
        "state_fields_read":  sorted(
            {"current.affect", "current.condition"}
            | {"current.%s" % k for k in current.reads}
            | {"baseline.%s" % k for k in baseline.reads}),
        "beliefs_injected": len(recall_entries),
        "levers_fired":      [r.get("source", "") for r in volatile["levers"]],
        "percepts":          percept_refs,
        "edges":             edge_refs,
    }

    # ---- Steps 6 + 7 deferred to the integrator ----
    # Step 6: Hand to decision engine — the integrator builds the LLM prompt from this packet.
    # Step 7: Couple back (acquisition events logged by the integrator's ledger commit).

    return {
        "stable":      stable,
        "volatile":    volatile,
        "manifest":    manifest,
        "recall_refs": recall_refs,
    }


# ---------------------------------------------------------------------------
# Stable prefix builder
# ---------------------------------------------------------------------------

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
        "genotype":   _sort_nested({k: _allele_word(v) for k, v in fixed.get("genotype", {}).items()}),
        "traits":     _sort_nested(_strip_notes(baseline.get("traits", {}))),
        "model":      _sort_nested(_strip_notes(baseline.get("model", {}))),
        "drives":     _sort_nested(_strip_notes(drives_raw)),
        "voice":      _sort_nested(baseline.get("voice", {})),
        "provenance": _sort_nested(baseline.get("provenance", {})),
    }
    return _sort_nested(stable)


def _strip_notes(obj):
    """Remove authoring metadata from the identity prefix: any key named 'note' or starting with
    '_' (design rationale, engine-internal notes like 'state.py _regard', arc foreshadowing like
    'erodes toward 1.0'). Recursive; pure. The substrate (numbers, structure) stays — only the
    commentary ABOUT it is removed, so none of it reaches the prompt. (gate swe-prompt-hygiene-strip-notes)
    """
    if isinstance(obj, dict):
        return {k: _strip_notes(v) for k, v in obj.items()
                if not (str(k) == "note" or str(k).startswith("_"))}
    if isinstance(obj, list):
        return [_strip_notes(x) for x in obj]
    return obj


def _allele_word(value):
    """Keep the allele token, drop the authored parenthetical rationale:
    'high (the innate empathy ...)' -> 'high'. The gain math reads the token; the rationale is
    authoring commentary that must not reach the prompt."""
    # Was `.split(" (", 1)[0].strip()` — the one reader of three that never lowercased, so a
    # capitalised allele reached the prompt as "High" while the gain math read "high".
    return heritable.word(value)


def _sort_nested(obj):
    """Recursively sort dict keys for byte-stable json.dumps.
    scene-assembly.md §"stable-prefix stability": same char dict -> identical bytes.
    """
    if isinstance(obj, dict):
        return {k: _sort_nested(v) for k in sorted(obj.keys()) for _ in [True] if k == k}
        # equivalent but cleaner:
    if isinstance(obj, dict):
        return {k: _sort_nested(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_sort_nested(x) for x in obj]
    return obj


# Fix: replace the double-comprehension bug above with the clean version
def _sort_nested(obj):
    """Recursively sort dict keys for byte-stable json.dumps."""
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
    return out


def _recall_for_packet(r):
    """Format a recall entry for the volatile.recall list.
    Carries claim/confidence/provenance/ref — NOT the full vault entry.
    """
    return {
        "ref":        r.get("ref"),
        "claim":      r.get("claim"),
        "confidence": r.get("confidence"),
        "provenance": r.get("provenance"),
    }


def _build_edges(current, percepts, world):
    """Build in-scene relationship edges to present entities.

    scene-assembly.md §"Volatile body": relationship edges to present entities.
    Only emit edges for entities that actually appear in the PerceptSet (recognized_as
    or entity refs) AND have a relationship record.

    Returns list of {target, trust, affinity, respect, debt, history}.
    """
    relationships = current.get("relationships", {})
    edges = []
    seen  = set()

    # Collect entity ids from percepts
    present_entity_ids = set()
    for p in percepts:
        ref = p.get("ref", "")
        if ref.startswith("entity."):
            eid = ref[len("entity."):]
            present_entity_ids.add(eid)
        # also check recognized_as for partial name matches
        rec = p.get("recognized_as", "")
        if rec:
            for rel_id in relationships:
                if rel_id.startswith(rec.lower()):
                    present_entity_ids.add(rel_id)

    for entity_id in present_entity_ids:
        if entity_id in seen:
            continue
        rel = relationships.get(entity_id)
        if rel and isinstance(rel, dict):
            edge = {
                "target":  entity_id,
                # the actor's OWN term for this entity: known_as (a descriptor when they don't know
                # the name) else the canonical display name. NEVER the raw id (the seam law).
                "label":   rel.get("known_as") or _display_name(entity_id),
                "history": rel.get("history"),
                # SECOND ORDER — what this character believes the OTHER party makes of THEM
                # (`bonds.reflect`; `emotion-basis.md`'s rich layer). Without this line the whole
                # mechanism was dead at runtime: `bonds.reflect` computed it, `direction.direct_edge`
                # could render it, and the packet never carried it, so the "and as you read them, …"
                # clause fired only in unit tests. That is the verdict_for / RelationshipDelta /
                # formative.* defect class — specified, implemented, reaching nothing — in the very
                # feature family that was supposed to have escaped it.
                "their_view": rel.get("their_view"),
            }
            # AN AXIS THIS EDGE DOES NOT CARRY IS OMITTED, never set to None. `direct_edge` and
            # `citation._r_edge` both test key PRESENCE — "if axis in edge" — so presence is the
            # contract they were written against, and filling an absent axis with None satisfied
            # the test while failing the value: `_check_num` raised
            # "edge.respect must be a number in [0,1], got None" and the beat died. Latent while
            # every sheet-authored edge happened to carry all four axes; `bonds.replay` is the
            # first producer of a partial edge (a resumed character holds only the axes that
            # actually moved toward someone their sheet never named), which is how a bug older
            # than the replay became reachable the day it shipped.
            for _axis in RELATIONSHIP_AXES:
                if rel.get(_axis) is not None:
                    edge[_axis] = rel[_axis]
            edges.append(edge)
            seen.add(entity_id)

    return edges


# ---------------------------------------------------------------------------
# Subject resolution — who is THIS event about, and what class are they?
#
# The target-aware appraisal (state.py _regard) and the arc's regard-generalization
# (arc.py assess) scope a character's EMPATHY by their regard for an event's SUBJECT.
# That machinery is dead until something resolves the subject + its group at runtime.
# This is that something. The split it enforces:
#   - group MEMBERSHIP is CONTENT (authored on person notes' `groups`) — never an LLM guess;
#   - the regard NUMBER stays engine-side and never reaches the prompt (the seam law);
#   - WHO the event is about may need the actor's reading (multi-party scenes) — the LLM may
#     NAME a subject, but only one it can actually see; the engine validates and resolves the rest.
# ---------------------------------------------------------------------------

def subject_groups(world):
    """Build the entity-id -> [group] index from the book's people registry.

    Group membership is authored content (person-note `groups`); load_book folds it into
    world["people"]. This index is how an event's SUBJECT acquires a class an appraiser can
    (dis)regard. Pure; rebuilt once per run (world is static). Raises on a non-dict world."""
    if not isinstance(world, dict):
        raise EngineError("SCENE_SUBJECT_GROUPS_WORLD_NOT_A_DICT", "subject_groups: world must be a dict")
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


def resolve_subject(edges, groups_index, named=None):
    """Who is this turn's event about, and what class are they? -> (target_id|None, target_group|None).

    Policy (deterministic, no LLM in here — the LLM's only input is `named`, its own reading):
      1. a NAMED subject the actor can actually see (in `edges`) wins — handles multi-party scenes;
      2. else, if exactly ONE party is present, it is the unambiguous subject;
      3. else (none present, or several with no name) -> (None, None): no single subject, so
         appraisal's regard factor stays 1.0 and the event is empathy-unscaled.
    The group is resolved from the registry, never from `named`. Multi-group entities use the
    PRIMARY (first) group (v1 — no lowest-regard arbitration yet). Raises on malformed structure."""
    if not isinstance(edges, list) or not isinstance(groups_index, dict):
        raise EngineError("SCENE_RESOLVE_SUBJECT_EDGES_NOT_A_LIST", "resolve_subject: edges must be a list and groups_index a dict")
    present = [e.get("target") for e in edges if isinstance(e, dict) and e.get("target")]
    present_set = set(present)
    target = None
    named_id = norm_id(named)
    by_norm = {norm_id(p): p for p in present}
    if named_id and named_id in by_norm:           # the actor named someone it can see -> trust it
        target = by_norm[named_id]
    elif len(present_set) == 1:                     # exactly one party present -> unambiguous subject
        target = present[0]
    group = None
    if target is not None:
        groups = groups_index.get(target, [])
        group = groups[0] if groups else None       # primary group; None -> not a regarded class
    return target, group
