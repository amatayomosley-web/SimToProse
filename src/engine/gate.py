"""gate.py — Relevancy Gate: perception-mode wall + recall-mode trigger-matching.

Normative contract: docs/relevancy-gate.md (counterfactual relevance via trigger-matching,
two-mode machinery, connection energy, deterministic resolution).

Public API consumed by scene.py:
    perception_scope(scene_slice, world, skills, energy) -> [Percept]
    extract_triggers(percepts)                           -> [str]
    run_gate(triggers, vault, skills, goals, energy)     -> [matched belief dicts]

All functions are PURE + deterministic. No I/O, no LLM, no randomness.
"""

# ---- Percept type (scene-assembly.md §"The packet") ----

def _make_percept(ref, channel, fidelity, attributes, recognized_as=None, must_surface=False):
    """Construct a Percept dict.

    ref          -- stable identifier (e.g. "evt.child_fever")
    channel      -- "visual" | "verbal" | "tactile" | "olfactory" | "event"
    fidelity     -- float 0..1 (how clear/complete this percept is)
    attributes   -- list of str (perceivable attributes; the whitelist)
    recognized_as -- str | None (identity label, filled only on a passed identity check)
    must_surface -- bool (hinge: always inject regardless of budget)
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
    energy = float(condition.get("energy", 1.0))
    load   = float(condition.get("allostatic_load", 0.0))
    return max(0.0, energy * (1.0 - load * ALLOSTATIC_PENALTY))


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

def perception_scope(scene_slice, world, skills, condition, relationships=None):
    """Filter scene_slice to what THIS character apprehends this turn.

    scene-assembly.md step 2; relevancy-gate.md §"Two input domains, one machinery —
    perception-mode": source set = the scene slice; passed check admits an attribute into
    the PerceptSet or fills recognized_as; failed check = absent.

    Parameters
    ----------
    scene_slice : dict  {event: {text, kind}, recent: [...], location: str|None}
    world       : dict  the book's world slice (locations, people, standing_facts, lexicon)
    skills      : dict  {skill_name: float 0..1} from baseline.skills
    condition   : dict  {energy, allostatic_load, ...}

    Returns list of Percept dicts (the PerceptSet).

    Raises ValueError on malformed input.
    """
    if not isinstance(scene_slice, dict):
        raise ValueError("perception_scope: scene_slice must be a dict")
    if not isinstance(world, dict):
        raise ValueError("perception_scope: world must be a dict")
    if not isinstance(skills, dict):
        raise ValueError("perception_scope: skills must be a dict")
    if not isinstance(condition, dict):
        raise ValueError("perception_scope: condition must be a dict")

    event = scene_slice.get("event")
    if not isinstance(event, dict) or "text" not in event:
        raise ValueError("perception_scope: scene_slice.event must be a dict with 'text'")

    event_text = str(event.get("text", ""))
    event_kind = str(event.get("kind", "mundane"))
    location   = scene_slice.get("location")
    recent     = scene_slice.get("recent", [])

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
        if _passes_check(perception_skill, PERCEPTION_DC_SUBTLE):
            subtle_attrs = _extract_subtle_attributes(event_text, event_kind, world)
            if subtle_attrs:
                percepts.append(_make_percept(
                    ref        = "evt.subtle.%s" % _safe_ref(event_text[:20]),
                    channel    = "visual",
                    fidelity   = perception_skill,
                    attributes = subtle_attrs,
                ))

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
    named_entities = _extract_named_entities(event_text, world)
    for entity_id, entity_label, entity_attrs in named_entities:
        entity_ref = "entity.%s" % entity_id
        # you recognize who you KNOW (a standing relationship) even at low insight; a STRANGER still
        # needs the insight check. Acquaintance keys recognition, not perceptual sharpness alone.
        if (relationships and entity_id in relationships) or _passes_check(insight_skill, PERCEPTION_DC_IDENTITY):
            # Passed: full role description + recognized_as label
            percepts.append(_make_percept(
                ref          = entity_ref,
                channel      = "visual",
                fidelity     = insight_skill,
                attributes   = entity_attrs,
                recognized_as= entity_label,
            ))
        else:
            # Failed: only minimal observable presence — no role description, no label.
            # "person present" is all a character who failed the check perceives.
            percepts.append(_make_percept(
                ref        = entity_ref,
                channel    = "visual",
                fidelity   = 0.4,
                attributes = ["person present"],
                # recognized_as intentionally absent
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

def extract_triggers(percepts):
    """Extract trigger strings from the PerceptSet.

    scene-assembly.md step 3: triggers derived from PerceptSet ONLY —
    "you cannot be triggered by what you didn't perceive."

    Triggers = entities, names, keywords from percept attributes and recognized_as.
    Returns list of lowercase normalised trigger strings.
    """
    if not isinstance(percepts, list):
        raise ValueError("extract_triggers: percepts must be a list")

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

def run_gate(triggers, vault, skills, goals, condition):
    """Match triggers against the vault and return active recall.

    relevancy-gate.md: trigger-match -> vault -> skill -> goal-salience -> energy budget.
    Energy budget: spend descending salience (goal-bearing first); stop when budget runs out.

    Parameters
    ----------
    triggers  : [str]  normalised trigger strings (from extract_triggers)
    vault     : [dict] list of belief dicts {claim, believed_value, provenance, confidence, ...}
    skills    : dict   {skill_name: float}
    goals     : [dict] active_goals list [{goal: str, urgency: float}]
    condition : dict   {energy, allostatic_load}

    Returns list of matched belief dicts augmented with:
        ref       -- "vault[N]" stable reference
        cost      -- float (connection cost = 1 - confidence)
        triggered -- the trigger word(s) that matched
    """
    if not isinstance(triggers, list):
        raise ValueError("run_gate: triggers must be a list")
    if not isinstance(vault, list):
        raise ValueError("run_gate: vault must be a list")
    if not isinstance(skills, dict):
        raise ValueError("run_gate: skills must be a dict")
    if not isinstance(goals, list):
        raise ValueError("run_gate: goals must be a list")
    if not isinstance(condition, dict):
        raise ValueError("run_gate: condition must be a dict")

    budget = _energy_budget(condition)
    goal_texts = [_normalize(g.get("goal", "")) for g in goals]

    # Phase 1: find all vault entries that match any trigger
    candidates = []
    for idx, belief in enumerate(vault):
        if not isinstance(belief, dict):
            continue
        claim = str(belief.get("claim", ""))
        confidence = float(belief.get("confidence", 0.5))
        cost = 1.0 - confidence   # relevancy-gate.md: edge cost = edge faintness = 1-confidence
        # [[links]] are live machinery (vault.py): a belief's linked note names join its matchable
        # surface — author-controlled trigger anchors, not substring luck.
        surface = _normalize(claim) + " " + " ".join(_normalize(str(l)) for l in belief.get("links", []))

        matched_triggers = []
        for trig in triggers:
            if _normalize(trig) in surface:
                matched_triggers.append(trig)

        if not matched_triggers:
            continue

        # goal salience: does this belief touch an active goal?
        # relevancy-gate.md §Goal salience: beliefs bearing on active goals rank first
        is_goal_bearing = False
        for gt in goal_texts:
            if gt and _keyword_overlap(_normalize(claim), gt):
                is_goal_bearing = True
                break
        # also check claim keywords against goal texts (bidirectional)
        if not is_goal_bearing:
            claim_words = set(_normalize(claim).split())
            for g in goals:
                goal_words = set(_normalize(g.get("goal", "")).split())
                if claim_words & goal_words - {"the", "a", "an", "to", "of", "and", "is", "in"}:
                    is_goal_bearing = True
                    break

        candidates.append({
            "idx":            idx,
            "ref":            "vault[%d]" % idx,
            "claim":          claim,
            "believed_value": belief.get("believed_value"),
            "provenance":     belief.get("provenance", ""),
            "confidence":     confidence,
            "cost":           cost,
            "triggered":      matched_triggers,
            "is_goal_bearing": is_goal_bearing,
        })

    # Phase 2: sort by salience descending (goal-bearing first, then by confidence)
    # relevancy-gate.md: "Explore from triggers by ascending cost / descending salience"
    candidates.sort(key=lambda c: (0 if c["is_goal_bearing"] else 1, -c["confidence"]))

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


def _extract_named_entities(text, world):
    """Return [(entity_id, entity_label, [observable_attrs])] for known entities mentioned.

    Identity derives from world.people — we only surface entities whose presence is
    evidenced by the scene text. No invention.
    """
    t = _normalize(text)
    results = []

    for person in world.get("people", []):
        pid   = person.get("id", "")
        what  = person.get("what", "")
        # Check if this person's name appears in the event text
        name_parts = pid.replace("_", " ").split()
        first_name = name_parts[0] if name_parts else ""
        if first_name and _normalize(first_name) in t:
            # Observable attributes: role/description from world (not secret)
            # We expose only the role description, not inner motivations
            observable = [what] if what else [first_name]
            results.append((pid, first_name.capitalize(), observable))

    return results


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
# acquired. The canonical entity id ("kestra") is engine wiring (regard/subject) and stays engine-side,
# exactly like the regard NUMBER. The DEFAULT is common knowledge — a character knows the names of
# those they stand with; IGNORANCE is the marked case (knowledge is stratified by station). An edge
# sets `known_as` to the term THIS character uses: a descriptor ("the damaged worker") when they do
# NOT know the name, or a nickname. Absent known_as -> they know the canonical name. Opt-in masking:
# you author ignorance, never blanket-hide. So family stays named; only the disregarded worker is masked.

def _display_name(entity_id):
    """Canonical display name from an entity id: 'wynn_wintercrest' -> 'Wynn Wintercrest',
    'kestra' -> 'Kestra'. What an actor sees for someone they know. Never an engine id form."""
    return " ".join(w.capitalize() for w in str(entity_id).split("_") if w) or str(entity_id)


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
