"""concepts.py — the closed vocabulary of things a feeling can be ABOUT that are not people.

THE PROBLEM THIS SOLVES. A wound is conceptual: a mother whose child nearly died of a fever is
marked by SICKNESS, not by the word "fever". "A child with fever" never matches "the boy's forehead
was hot", so a trigger word list cannot link a later beat to the scar, and hard rule 3 keeps an
LLM out of the engine, so the engine cannot read the beat itself. Owner, 2026-09-11: *"wounds are
conceptual ... so how do we link that concept and others like it."*

THE ANSWER. The engine owns a CLOSED, FLAT registry of concepts — generic nouns, never a book's
nouns (hard rule 1) — and the one reader the pipeline already has on every beat picks from it:
the appraiser seat (`scripts/appraiser.py`) names what a feeling points at as a perceived person,
a registry concept, or nothing, and so may the actor's own self-tags (`consolidation.validate_tags`)
until Phase 3 wires the seat in. The engine VALIDATES the name by identity and REFUSES anything
else by code. After that one semantic step — made by a model, committed to the chronicle before
anything computes from it — every link is exact: a wound keyed `(concept, path)` matches a later
reading about the same concept on the same path by string equality. Deterministic given the log,
which is what this engine promises everywhere (hard rule 2).

WHERE THE FIRST ENTRIES COME FROM. Not invented: `data/formative_profiles.json` carried 78 wound
rows with ~300 trigger phrases, clustered here by hand into the concepts they were instances of;
each of those rows now names its concept, and `tests/test_concepts.py` asserts every one resolves.
A handful the library lacks but any story needs (a death, a child lost, an injury, helplessness)
are added beside them. FLAT ON PURPOSE — the owner's call: "start flat from the library's clusters
and let the first book show the gaps." A two-level list (sickness over fever and plague) is the
sizing question a real book answers, not this file.

THE PREFIX. An about that is a concept is written `concept:<id>` everywhere it travels — the
readings row, the target bind, the wound key — so a character named "fire" can never collide with
the concept. `is_concept` and `id_of` are the two readings of that string; nothing else parses it.

Deterministic, stdlib only, no LLM, no randomness. A lookup table with two accessors.
"""
from __future__ import annotations

from .records import RecordError

PREFIX = "concept:"

# id -> what it is, in the words the appraiser seat is shown. ORDER is the menu order.
REGISTRY = {
    # ---- the body in danger ----
    "fire":           "fire, smoke, burning, being trapped by flame",
    "drowning":       "deep water, sinking, a storm at sea, going under",
    "predator":       "a beast, a hunting animal, fangs and claws, being stalked",
    "cold":           "freezing, exposure, a blizzard, the body shutting down",
    "confinement":    "a locked cell, chains, a cage, a space too small to leave",
    "collapse":       "a roof or a tunnel coming down, crushing weight, being buried",
    "poison":         "something in the food or the cup; a taste that should not be there",
    "contamination":  "a substance that sickens by touch or air; a place that is unclean",
    "sickness":       "illness in a body — fever, plague, a sore that will not heal",
    "injury":         "a wound to the body, blood, a limb that will not work",
    "bombardment":    "a blast, artillery, a noise that shakes the ground",
    # ---- want and lack ----
    "hunger":         "no food, an empty larder, rations cut, watching others eat",
    "thirst":         "no water, a dry throat, a cracked land",
    "debt":           "money owed, a ledger against you, the bailiff, eviction",
    "siege":          "gates closed, supply cut, waiting inside walls for the end",
    "exile":          "being cast out — a border, a camp, a home you cannot return to",
    "servitude":      "forced labour, the whip, the bench, a life that is not yours",
    # ---- the social world ----
    "crowds":         "a press of people, noise, a mob, too many voices at once",
    "arrest":         "the watch, irons, being taken, the law laying hands on you",
    "authority":      "officials, edicts, protocol, being made to bend to a rule",
    "isolation":      "being alone too long, silence, no one coming",
    "shame":          "public disgrace, a mark others can see, being made small before people",
    "outsiders":      "strangers, the corrupt city, people not of your kind",
    # ---- what people do to each other ----
    "betrayal":       "trust given and turned against you by someone who had it",
    "disownment":     "cast out by your own family or clan",
    "infidelity":     "a lover or spouse who lied about love",
    "broken_oath":    "a sworn promise broken; a pact abandoned",
    "abandonment":    "left behind — by allies, by those who should have come",
    "helplessness":   "watching harm come to someone and being unable to stop it",
    "loss_of_a_child": "a child dead or dying; the one loss that does not un-happen",
    "death":          "a death witnessed or learned of; a body; the fact of it",
    # ---- violence ----
    "war":            "a raid, a sacking, a town put to the sword",
    "combat":         "steel drawn, being cornered, a fight to the end",
    "conscription":   "the levy, the muster, drums and drill, being taken to fight",
    "pursuit":        "being hunted — patrols, searchlights, an informant's whisper",
    "execution":      "a sentence of death; the scaffold; the firing line",
    "interrogation":  "questioning under duress; a tribunal; being made to confess",
    "assassination":  "an attempt on a life — the bolt from the gallery, the sudden stop",
    # ---- vocation and station ----
    "shoddy_work":    "bad craft, a flawed joint, waste of good material",
    "accounts":       "a ledger that does not balance; a coin missing; an audit",
    "sacrilege":      "a holy thing defiled — scripture burned, a shrine desecrated",
    "heresy":         "false belief, blasphemy, the apostate",
    "indulgence":     "luxury, gluttony, comfort of the flesh",
    "court_intrigue": "flattery with a hook in it; the gift, the private audience",
    "forced_marriage": "a betrothal made for alliance; a dowry; a contract on a body",
    "usurpation":     "a birthright taken; an estate confiscated; a rival on your seat",
    "omens":          "a comet, an eclipse, a prophecy demanded or feared",
    "excommunication": "cast out of the faith; the seal broken; the decree read",
    "possession":     "a demonic accusation; the rite; the bindings",
}


def is_concept(about):
    """Is this about-string a registry concept (`concept:<id>` with a known id)? Never raises."""
    if not isinstance(about, str) or not about.startswith(PREFIX):
        return False
    return about[len(PREFIX):] in REGISTRY


def looks_like_concept(about):
    """Does this about-string CLAIM to be a concept (carries the prefix), known or not?"""
    return isinstance(about, str) and about.startswith(PREFIX)


def id_of(about):
    """`concept:<id>` -> `<id>`. Raises by name on an unknown concept; a prefix with no known id is
    the seat inventing a category, which is exactly what a closed registry refuses."""
    if not looks_like_concept(about):
        raise RecordError("CONCEPT_NOT_A_CONCEPT", "concepts: %r does not carry the %r prefix" % (about, PREFIX))
    cid = about[len(PREFIX):]
    if cid not in REGISTRY:
        raise RecordError("CONCEPT_UNKNOWN",
                          "concepts: %r is not in the registry. The list is closed on purpose — a "
                          "feeling about a category the engine has no name for stays UNBOUND, and a "
                          "new category is an edit to src/engine/concepts.py, never a runtime guess."
                          % (cid,))
    return cid


def about(cid):
    """`<id>` -> `concept:<id>`, refusing an unknown id."""
    if cid not in REGISTRY:
        raise RecordError("CONCEPT_UNKNOWN", "concepts: %r is not in the registry" % (cid,))
    return PREFIX + cid


def gloss(about_or_id):
    """The one-line description shown to a model or a reader. Accepts either form."""
    cid = id_of(about_or_id) if looks_like_concept(about_or_id) else about_or_id
    if cid not in REGISTRY:
        raise RecordError("CONCEPT_UNKNOWN", "concepts: %r is not in the registry" % (cid,))
    return REGISTRY[cid]


def menu():
    """The registry as the appraiser seat is shown it: one line per concept, the exact string the
    seat must return (`concept:<id>`) beside what it means. No numbers."""
    return "\n".join("  %s%s — %s" % (PREFIX, cid, g) for cid, g in REGISTRY.items())
