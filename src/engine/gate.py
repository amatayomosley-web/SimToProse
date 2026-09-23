"""gate.py — Relevancy Gate: perception-mode wall + recall-mode trigger-matching.

Normative contract: docs/relevancy-gate.md (counterfactual relevance via trigger-matching,
two-mode machinery, connection energy, deterministic resolution).

Public API consumed by scene.py:
    perception_scope(scene_slice, world, skills, energy) -> [Percept]
    extract_triggers(percepts)                           -> [str]
    run_gate(triggers, vault, skills, goals, energy)     -> [matched belief dicts]

All functions are PURE + deterministic. No I/O, no LLM, no randomness.
"""

import hashlib
from .records import RecordError   # rule 6's bad-input type; codes.py GATE_*
from .condition import mind_view   # the mind's side of a split pool (gate energy-reserves)
from .presence import (match as _present_match,   # named is not seen — see presence.py
                       display_name as _display_name,
                       named_in as _named_in,
                       present_unnamed as _present_unnamed)   # present is seen — see presence.py
# ---- Percept type (scene-assembly.md §"The packet") ----

def _make_percept(ref, channel, fidelity, attributes, recognized_as=None, must_surface=False,
                  present=None):
    """Construct a Percept dict.

    ref          -- stable identifier (e.g. "evt.child_fever")
    channel      -- "visual" | "verbal" | "tactile" | "olfactory" | "event" | "reported"
    fidelity     -- float 0..1 (how clear/complete this percept is)
    attributes   -- list of str (perceivable attributes; the whitelist)
    recognized_as -- str | None (identity label, filled only on a passed identity check)
    must_surface -- bool (hinge: always inject regardless of budget)
    present      -- bool | None. BODILY HERE as distinct from named (presence.py); None omits it.
    """
    p = {
        "ref":          ref,
        "channel":      channel,
        "fidelity":     float(fidelity),
        "attributes":   list(attributes),
        "must_surface": bool(must_surface),
    }
    if recognized_as is not None:
        p["recognized_as"] = recognized_as
    if present is not None:
        p["present"] = bool(present)
    return p

# ---- DC table (relevancy-gate.md §Resolution — deterministic, not director-set; 2026-06-10 audit) ----
# Connection cost = 1.0 - confidence (edge faintness); budget = energy * (1 - allostatic_load * 0.5)
PERCEPTION_DC_PLAIN    = 0.00  # overt, named — automatic pass
PERCEPTION_DC_IDENTITY = 0.55  # recognising an entity not clearly identified
PERCEPTION_DC_SUBTLE   = 0.60  # noticing a subtle cue (faint signs, emotional tells)

ALLOSTATIC_PENALTY = 0.5  # half-penalty at maximum load (relevancy-gate.md §Connection energy)

def _energy_budget(condition):
    """Compute cognitive connection budget from condition dict.

    Formula: budget = energy * (1 - allostatic_load * ALLOSTATIC_PENALTY)
    Provenance: relevancy-gate.md §Connection energy — energy is read off the
    arousal/allostatic state; hyperarousal/collapse (high load) -> low cognitive energy.
    """
    # MEMORY IS THE MIND'S (gate energy-reserves): with the body system's reserves, what the mind has left;
    # without them, the energy itself - read exactly as before.
    energy = float(mind_view(condition))
    load   = float(condition.get("allostatic_load", 0.0))
    return max(0.0, energy * (1.0 - load * ALLOSTATIC_PENALTY))

# A WORN MIND'S EYE (gate tired-eyes, 2026-09-22; the world lexicon's subtle cues joined it at gate tired-lexicon,
# 2026-09-23): the share of perception a mind with nothing left keeps. [START - FALSIFIER: a character who slept a
# full night reads as missing what a rested eye catches.]
WORN_EYE = 0.5


def worn_eye(skill, condition):
    """A perception skill weighed by what the MIND has left - the owner's ruling D3, one rule for a speaker's tells
    (`tells.catches`) and the room's subtle cues (`perception_scope`). Read exactly as the memory budget reads it
    (`_energy_budget`: the mind's side, less the load's penalty); a rested mind keeps its whole eye, one with
    nothing left keeps `WORN_EYE` of it."""
    left = max(0.0, min(1.0, _energy_budget(condition or {})))
    return float(skill) * (WORN_EYE + (1.0 - WORN_EYE) * left)


def _passes_check(skill_value, dc):
    """Deterministic check: passes iff skill_value >= dc.

    relevancy-gate.md §Resolution (2026-06-10): deterministic — stats/knowledge vs DC decide.
    No randomness. A check at DC=0.0 always passes.
    """
    return float(skill_value) >= float(dc)

# ---- Normalisation (accent-tolerant matching — vault claims may carry diacritics) ----

def _normalize(s):
    """Lowercase + strip common diacritics for accent-tolerant matching.
    docs/relevancy-gate.md §"Trigger extraction is fuzzy".
    """
    replacements = [
        ("á","a"),("à","a"),("â","a"),("ä","a"),
        ("é","e"),("è","e"),("ê","e"),("ë","e"),
        ("í","i"),("ì","i"),("î","i"),("ï","i"),
        ("ó","o"),("ò","o"),("ô","o"),("ö","o"),
        ("ú","u"),("ù","u"),("û","u"),("ü","u"),
        ("ý","y"),("ñ","n"),
    ]
    t = s.lower()
    for src, dst in replacements:
        t = t.replace(src, dst)
    return t

# ---- Step 2: Perception scope (perception-mode wall) ----

def perception_scope(scene_slice, world, skills, condition, relationships=None, me=None, tired=False):
    """Filter scene_slice to what THIS character apprehends this turn.

    scene-assembly.md step 2; relevancy-gate.md §"Two input domains, one machinery —
    perception-mode": source set = the scene slice; passed check admits an attribute into
    the PerceptSet or fills recognized_as; failed check = absent.

    Parameters
    ----------
    scene_slice : dict  {event: {text, kind}, recent: [...], location: str|None}
    world       : dict  the book's world slice (locations, people, lexicon;
                        standing_facts is ALSO present but INERT here — read only
                        by the out-of-loop critic, never by perception. A fact
                        that must reach the actor goes in event text or a vault
                        belief; guide-content.md "Currently INERT")
    skills      : dict  {skill_name: float 0..1} from baseline.skills
    condition   : dict  {energy, allostatic_load, ...}
    tired       : bool  the book runs `condition_flow`: the subtle-cue check weighs the eye by what the mind has
                        left (`worn_eye`), as `tells.catches` does (gate tired-lexicon)

    Returns list of Percept dicts (the PerceptSet).

    Raises ValueError on malformed input.
    """
    if not isinstance(scene_slice, dict):
        raise RecordError("GATE_SCENE_SLICE_NOT_AN_OBJECT", "perception_scope: scene_slice must be a dict")
    if not isinstance(world, dict):
        raise RecordError("GATE_WORLD_NOT_AN_OBJECT", "perception_scope: world must be a dict")
    if not isinstance(skills, dict):
        raise RecordError("GATE_SKILLS_NOT_AN_OBJECT", "perception_scope: skills must be a dict")
    if not isinstance(condition, dict):
        raise RecordError("GATE_CONDITION_NOT_AN_OBJECT", "perception_scope: condition must be a dict")

    event = scene_slice.get("event")
    if not isinstance(event, dict) or "text" not in event:
        raise RecordError("GATE_EVENT_MISSING_TEXT", "perception_scope: scene_slice.event must be a dict with 'text'")

    event_text = str(event.get("text", ""))
    event_kind = str(event.get("kind", "mundane"))
    location   = scene_slice.get("location")
    recent     = scene_slice.get("recent", [])
    # WHO IS BODILY HERE (presence.py). None = untracked -> every named entity reads present.
    present_ids = scene_slice.get("present")
    present_set = None if present_ids is None else {str(i) for i in present_ids}

    perception_skill = float(skills.get("perception", 0.5))
    insight_skill    = float(skills.get("insight", 0.5))

    percepts = []

    # -- Percept 1: the core event (always present — overt, plain-stated)
    # DC = 0.0 (PLAIN): the event text names what happened openly.
    event_attrs = _extract_event_attributes(event_text, event_kind, world)
    core_ref = "evt.%s" % _safe_ref(event_text[:30])
    percepts.append(_make_percept(
        ref         = core_ref,
        channel     = "event",
        fidelity    = 1.0,
        attributes  = event_attrs,
        must_surface= True,   # the event is the anchor; always surface
    ))

    # -- Percept 2: subtle cues in the event text (DC = PERCEPTION_DC_SUBTLE)
    # Gated on perception skill. A character with low perception misses fine detail.
    # Examples: severity of fever, physical distress signs, environmental details.
    if _has_subtle_cues(event_text, event_kind, world):
        if _passes_check(worn_eye(perception_skill, condition) if tired else perception_skill, PERCEPTION_DC_SUBTLE):
            subtle_attrs = _extract_subtle_attributes(event_text, event_kind, world)
            if subtle_attrs:
                percepts.append(_make_percept(
                    ref        = "evt.subtle.%s" % _safe_ref(event_text[:20]),
                    channel    = "visual",
                    fidelity   = perception_skill,
                    attributes = subtle_attrs,
                ))

    # -- Percept 2b: PROPS — the room's physical affordances (no DC; plainly present)
    # scene-authoring-rules.md Rule 5 requires 3-5 concrete objects per scene "that can be held,
    # counted, slid" because "the simulation engine requires physical affordances to anchor body
    # language, eye contact, and pacing". Until 2026-08-24 that rule named a field the engine read
    # NOWHERE — the ninth specified-but-reaching-nothing defect found in this repo. A prop that is
    # not a percept is not in the scene: scene-assembly.md makes the PerceptSet the only channel by
    # which a world fact reaches an actor.
    #
    # NOT perception-gated, deliberately. The rule's own argument is that these are the plainly
    # present objects of the room, not fine detail a low-perception character misses — and gating
    # them would withdraw the affordances exactly when a character most needs something to do with
    # their hands. A prop that SHOULD be hidden is a subtle cue and belongs in the event text, where
    # PERCEPTION_DC_SUBTLE already applies.
    for prop in (scene_slice.get("props") or []):
        text = str(prop).strip()
        if not text:
            continue
        percepts.append(_make_percept(
            ref         = "prop.%s" % _safe_ref(text[:30]),
            channel     = "visual",
            fidelity    = 1.0,
            attributes  = [text],
            must_surface= True,     # an affordance withheld is an affordance that does not exist
        ))

    # -- Percept 2c: TELLS this listener caught (gate tells; the `tells` system) - a sign another actor let slip,
    # marked by the event reader and passed on by `tells.for_listener` only to a listener sharp enough for it.
    # Absent the system the key is never set and nothing is added.
    for tell in (scene_slice.get("tells_noticed") or []):
        text = str(tell).strip()
        if text:
            percepts.append(_make_percept(ref="tell.%s" % _safe_ref(text[:30]), channel="visual", fidelity=1.0,
                                          attributes=[text], must_surface=True))

    # -- Percept 3: entity recognition (DC = PERCEPTION_DC_IDENTITY)
    # For each person mentioned in the scene, check if this character recognises them.
    # Identity label (recognized_as) filled only on a passed insight check.
    #
    # CRITICAL: on a FAILED check, use only minimal physical presence markers ("person present"),
    # NOT the full world description (which contains identity-bearing words like "gifted").
    # The world description is the IDENTITY record; it is withheld behind the check, same as the
    # label. Only a passed check unlocks both the recognized_as label AND the role description.
    # scene-assembly.md: "the disguised assassin → [a hooded figure, cloaked, ~6ft, →door];
    # the label 'assassin' withheld behind a check" — the granular description is ALSO gated.
    # NAMED IS NOT SEEN (presence.py). The extractor is unchanged; the distinction is drawn HERE,
    # where the scene slice — and so the presence list — is already in scope.
    named_entities = _named_in(event_text, world, _normalize)
    for entity_id, entity_label, entity_attrs in named_entities:
        entity_ref = "entity.%s" % entity_id
        here = None if present_set is None else _present_match(entity_id, present_set)
        channel = "reported" if here is False else "visual"
        # you recognize who you KNOW (a standing relationship) even at low insight; a STRANGER still
        # needs the insight check. Acquaintance keys recognition, not perceptual sharpness alone.
        if (relationships and entity_id in relationships) or _passes_check(insight_skill, PERCEPTION_DC_IDENTITY):
            # Passed: full role description + recognized_as label
            percepts.append(_make_percept(
                ref          = entity_ref,
                channel      = channel,
                fidelity     = insight_skill,
                attributes   = entity_attrs,
                recognized_as= entity_label,
                present      = here,
            ))
        else:
            # Failed: only minimal observable presence — no role description, no label.
            # "person present" is all a failed check perceives; merely named, not even that.
            percepts.append(_make_percept(
                ref        = entity_ref,
                channel    = channel,
                fidelity   = 0.4,
                attributes = ["person spoken of" if here is False else "person present"],
                # recognized_as intentionally absent
                present    = here,
            ))

    # -- Percept 3b: PRESENT IS SEEN (presence.present_unnamed, 2026-09-18). The people the driver says
    # are bodily here whom the text did not name: perceived as here without a DC (being in the room
    # is plain), WHO they are behind the same recognition check as the named path. Only when the
    # slice carries a presence list — an untracked scene (present None) is unchanged.
    if present_set is not None:
        for entity_id, entity_label, entity_attrs in _present_unnamed(present_set, [e[0] for e in named_entities], world, me):
            entity_ref = "entity.%s" % entity_id
            if (relationships and entity_id in relationships) or _passes_check(insight_skill, PERCEPTION_DC_IDENTITY):
                percepts.append(_make_percept(
                    ref          = entity_ref,
                    channel      = "visual",
                    fidelity     = insight_skill,
                    attributes   = entity_attrs or ["person present"],
                    recognized_as= entity_label,
                    present      = True,
                ))
            else:
                percepts.append(_make_percept(
                    ref        = entity_ref,
                    channel    = "visual",
                    fidelity   = 0.4,
                    attributes = ["person present"],
                    present    = True,
                ))

    # -- Percept 4: location context (if location is set and resolvable)
    if location:
        loc_entry = _lookup_location(location, world)
        if loc_entry:
            percepts.append(_make_percept(
                ref        = "loc.%s" % loc_entry["id"],
                channel    = "visual",
                fidelity   = 1.0,
                attributes = [loc_entry["what"]],
            ))

    return percepts

# ---- Step 3: Trigger extraction (from PerceptSet only — never ground truth) ----

def belief_id(belief):
    """A belief -> a stable identity derived from its CLAIM TEXT.

    WHY THIS EXISTS. The gate's only handle on a belief was `vault[N]` — its POSITION in the
    character's vault list — and `scene.assemble` wrote that string into `recall_events`, a table
    the schema-v9 triggers refuse to UPDATE or DELETE. The position means nothing outside the exact
    note revision that produced it: add one bullet above an entry and every stored reference below
    it names a different belief, permanently and uncorrectably. The Beck Hollow chronicle already
    spans two bible fingerprints, so its stored `vault[2]` strings are ALREADY ambiguous.

    Derived from the claim, not from `acquisition_id`, because authored seed beliefs have no
    acquisition row and they are the majority of every vault in every book — an id scheme covering
    only acquired beliefs would leave the authored ones exactly as unidentifiable as before.

    A claim whose WORDS changed is a different thing to have believed, so it gets a different id.
    That matches the monotonic-add vault (`knowledge-model.md`) and the append-only log: beliefs are
    added and superseded, never edited in place.

    Stable across processes: hashlib, not Python's salted `hash()`.
    """
    # `_normalize` lowercases and folds diacritics but does NOT collapse whitespace — it is built
    # for trigger matching, where runs of spaces never occur. An author REFLOWING a belief line
    # must not create a new belief, so the collapse happens here rather than by changing a
    # normaliser the matcher also depends on.
    d = belief or {}
    claim = " ".join(_normalize(str(d.get("claim", ""))).split())
    k = "%s|%s|%s" % (claim, str(d.get("target_actor") or "").strip().lower(), str(d.get("epistemic_stance") or "").strip().lower()) if (d.get("target_actor") or d.get("epistemic_stance")) else claim
    return "b:" + hashlib.sha1(k.encode("utf-8")).hexdigest()[:12]

def perceived_surfaces(percepts):
    """The PerceptSet's raw phrasings — what the character actually saw, UNSHREDDED.

    The twin of `extract_triggers`, and it exists because those two answer different questions.
    `extract_triggers` shreds each attribute into single words for the RECALL GATE, which matches
    trigger words against belief PROSE: perceive a wolf and "the wolf came down the fell road"
    should surface. Word-level overlap is right for that.

    It is wrong for an AUTHORED trigger. `docs/authoring/BLUEPRINT-character.md`'s wound box
    instructs "2-4 short phrases, in the words a scene would actually use", so authors write
    "a child with fever" — and the shredded bag is ['child','fever','tosses','cot'], with "a" and
    "with" dropped by the stoplist and everything under three characters gone. The phrase can never
    be a substring of that, so a wound authored exactly as documented never fires. MEASURED on this
    repo's own fixture before this function existed.

    SAME PERCEPTS, so the perception wall is untouched: "you cannot be triggered by what you didn't
    perceive" is a property of the PerceptSet, and any view derived from the same list inherits it.
    This is a second READING of what was perceived, never a second SOURCE.
    """
    if not isinstance(percepts, list):
        raise RecordError("GATE_PERCEPTS_NOT_A_LIST", "perceived_surfaces: percepts must be a list")
    out = []
    for p in percepts:
        if not isinstance(p, dict):
            continue
        for attr in p.get("attributes", []) or []:
            if str(attr).strip():
                out.append(_normalize(str(attr)))
        rec = p.get("recognized_as")
        if rec and str(rec).strip():
            out.append(_normalize(str(rec)))
    return out

def extract_triggers(percepts):
    """Extract trigger strings from the PerceptSet.

    scene-assembly.md step 3: triggers derived from PerceptSet ONLY —
    "you cannot be triggered by what you didn't perceive."

    Triggers = entities, names, keywords from percept attributes and recognized_as.
    Returns list of lowercase normalised trigger strings.
    """
    if not isinstance(percepts, list):
        raise RecordError("GATE_PERCEPTS_NOT_A_LIST", "extract_triggers: percepts must be a list")

    triggers = []
    for p in percepts:
        if not isinstance(p, dict):
            continue
        # from attributes
        for attr in p.get("attributes", []):
            triggers.extend(_words_from_attr(attr))
        # from recognized_as (entity identity, if the check passed)
        rec = p.get("recognized_as")
        if rec:
            triggers.extend(_words_from_attr(rec))
        # from ref — entity ids carry the name, but ONLY when the entity was recognized.
        # An unrecognized entity has ref="entity.<id>" but no recognized_as;
        # emitting its name as a trigger would violate the trigger wall:
        # the character can't be triggered by an identity they couldn't establish.
        # scene-assembly.md step 3: triggers from PerceptSet; recognition is a gated fact.
        ref = p.get("ref", "")
        if ref.startswith("entity.") and p.get("recognized_as"):
            triggers.append(ref[len("entity."):].replace("_", " "))

    # deduplicate, normalise, filter short noise
    seen = set()
    out  = []
    for t in triggers:
        t = _normalize(t.strip())
        if len(t) >= 3 and t not in seen:
            seen.add(t)
            out.append(t)
    return out

# ---- Step 4: Recall pass (recall-mode gate) ----

def run_gate(triggers, vault, skills, goals, condition, current_turn=0, relationships=None, recall_history=None, elapsed=None):
    """Match triggers against the vault and return active recall.

    relevancy-gate.md: trigger-match -> vault -> skill -> goal-salience -> energy budget.
    Optional decay parameters: current_turn, relationships, recall_history, elapsed.
    """
    if not isinstance(triggers, list):
        raise RecordError("GATE_TRIGGERS_NOT_A_LIST", "run_gate: triggers must be a list")
    if not isinstance(vault, list):
        raise RecordError("GATE_VAULT_NOT_A_LIST", "run_gate: vault must be a list")
    if not isinstance(skills, dict):
        raise RecordError("GATE_SKILLS_NOT_AN_OBJECT", "run_gate: skills must be a dict")
    if not isinstance(goals, list):
        raise RecordError("GATE_GOALS_NOT_A_LIST", "run_gate: goals must be a list")
    if not isinstance(condition, dict):
        raise RecordError("GATE_CONDITION_NOT_AN_OBJECT", "run_gate: condition must be a dict")

    budget = _energy_budget(condition)
    goal_texts = [_normalize(g.get("goal", "")) for g in goals]

    # Phase 1: generate candidates via 1-hop matching and multi-hop associative traversal
    from .associative import find_associative_candidates
    candidates = find_associative_candidates(
        triggers, vault, goals, budget, current_turn=current_turn,
        relationships=relationships, recall_history=recall_history, elapsed=elapsed)

    # Phase 2: sort by salience descending (goal-bearing first, then by confidence)
    # relevancy-gate.md: "Explore from triggers by ascending cost / descending salience"
    candidates.sort(key=lambda c: (0 if c["is_goal_bearing"] else 1, -c.get("confidence_eff", c["confidence"])))

    # Phase 3: spend budget — inject until budget exhausted
    injected = []
    spent    = 0.0
    for c in candidates:
        if spent + c["cost"] <= budget:
            injected.append(c)
            spent += c["cost"]
        # else: budget exhausted for this connection; it does NOT fire
        # (relevancy-gate.md: "when the budget runs out, remaining matches DON'T fire")

    return injected

# ---- Internal helpers — event classification and attribute extraction ----
# MACHINE/CONTENT SEAM (g6): the extraction MECHANISM lives here; the WORDS live in the book's
# world package under world["lexicon"] = {attribute_classes: {class: [keywords]},
# subtle_cues: {cue_name: [markers]}, subtle_cue_classes: [class, ...]}. The world bible owns
# its vocabulary (world-model.md); a world without a lexicon gets generic extraction (kind +
# leading words, no subtle percepts) — a content choice with defined semantics, not a failure.

def _lexicon(world):
    lex = world.get("lexicon", {})
    return (lex.get("attribute_classes", {}), lex.get("subtle_cues", {}), lex.get("subtle_cue_classes", []))

def _has_subtle_cues(text, kind, world):
    """True if this event carries gated fine detail: a subtle-cue class keyword is present,
    or the event kind is inherently cue-bearing (threat/loss — catalog machinery, not content)."""
    t = _normalize(text)
    classes, _cues, cue_classes = _lexicon(world)
    for cls in cue_classes:
        if any(_normalize(kw) in t for kw in classes.get(cls, [])):
            return True
    return kind in ("threat", "loss")

def _extract_event_attributes(text, kind, world):
    """Perceivable attributes from the event text (plain, overt) — lexicon-classed, no invention.
    Each attribute_class whose keyword appears contributes its class name."""
    attrs = []
    t = _normalize(text)
    classes, _cues, _cc = _lexicon(world)
    for cls in sorted(classes):
        if any(_normalize(kw) in t for kw in classes[cls]):
            attrs.append(cls)
    if kind and kind != "mundane":
        attrs.append(kind)
    if not attrs:                                  # generic floor: the event's own leading words
        attrs.append(" ".join(text.split()[:6]))
    return list(dict.fromkeys(attrs))

def _extract_subtle_attributes(text, kind, world):
    """Check-gated fine-grained attributes — lexicon-driven, no invention."""
    attrs = []
    t = _normalize(text)
    _classes, cues, _cc = _lexicon(world)
    for cue in sorted(cues):
        if any(_normalize(marker) in t for marker in cues[cue]):
            attrs.append(cue)
    return attrs

def _lookup_location(location_str, world):
    """Return the world location entry matching the location string, or None."""
    if not location_str:
        return None
    loc_n = _normalize(str(location_str))
    for loc in world.get("locations", []):
        lid = _normalize(loc.get("id", ""))
        lwhat = _normalize(loc.get("what", ""))
        if lid in loc_n or loc_n in lid or loc_n in lwhat:
            return loc
    return None

def _safe_ref(s):
    """Convert an arbitrary string to a safe identifier fragment."""
    return "".join(c if c.isalnum() else "_" for c in _normalize(s)).strip("_")

def _words_from_attr(attr):
    """Split an attribute string into meaningful word-level triggers."""
    # Split on whitespace and common separators; yield non-trivial words
    import re
    words = re.split(r"[\s\-_/]+", attr)
    stop = {"the", "a", "an", "to", "of", "and", "is", "in", "at", "on", "by", "for", "with",
            "her", "his", "their", "its", "she", "he", "they", "it", "who", "was", "has", "have"}
    out = []
    for w in words:
        w = _normalize(w.strip(".,;:!?\"'()[]"))
        if len(w) >= 3 and w not in stop:
            out.append(w)
    return out

def _keyword_overlap(text, query):
    """Return True if any query word appears in text (word-level overlap)."""
    stop = {"the", "a", "an", "to", "of", "and", "is", "in"}
    qwords = {w for w in _normalize(query).split() if w not in stop and len(w) >= 3}
    twords = set(_normalize(text).split())
    return bool(qwords & twords)

# ---- Name hygiene: render entities by acquaintance, never by the canonical id ----
# knowledge-model.md §"keeping the WRONG facts OUT": a character must not see a name they never
# acquired. The canonical entity id is engine wiring (regard/subject) and stays engine-side,
# exactly like the regard NUMBER. The DEFAULT is common knowledge — a character knows the names of
# those they stand with; IGNORANCE is the marked case (a name is learned, not assumed). An edge
# sets `known_as` to the term THIS character uses: a descriptor ("the man in the red scarf") when they do
# NOT know the name, or a nickname. Absent known_as -> they know the canonical name. Opt-in masking:
# you author ignorance, never blanket-hide. So the regulars stay named; only the newcomer nobody introduced is masked.

def scope_names(text, relationships):
    """Replace a person's first name with the term THIS actor uses for them — but ONLY where the
    actor's edge marks the name unacquired (`known_as` set to something other than the name itself).
    Absent or name-equal `known_as` leaves the name (they know it; default is common knowledge).
    Subtractive epistemic scoping (knowledge-model.md); pure. The canonical id is untouched in the
    engine — only this prompt-facing prose is masked."""
    import re
    if not isinstance(text, str) or not isinstance(relationships, dict):
        return text
    out = text
    for pid, rel in relationships.items():
        if not isinstance(rel, dict):
            continue
        known_as = rel.get("known_as")
        if not known_as:
            continue                                          # absent -> they know the name; no mask
        name = str(pid).split("_")[0]
        if len(name) < 2 or _normalize(name) == _normalize(str(known_as)):
            continue                                          # known_as IS the name -> no mask
        out = re.sub(r"\b%s\b" % re.escape(name), str(known_as), out, flags=re.IGNORECASE)
    return out
