"""contracts_world.py — the world note, declared once: every field of the book's world, its shape, and where it stands.

The declarations `contracts.check` walks a world against (gate world-contract, 2026-09-25), and the rows
BLUEPRINT-world carries between its GENERATED markers. Built from an inventory of every path the engine and its
drivers read from the world dict (file:line per path) and the paths the owner's world notes and the fixture carry.
The world is the world note's engine block plus one `people` entry per person note (vault.load_book). A block an
engine module already validates is handed to it: the laws to law.py, the tensions to tensions.py, the systems to
systems.py - one rule per thing.

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

from .contracts import Field as F


def _person(p, world, ctx):
    if isinstance(p, dict) and not p.get("id"):
        return "has no id - no one can perceive, join or cite this person"
    return None


def _place(loc, world, ctx):
    if isinstance(loc, dict) and not loc.get("id"):
        return "has no id - no scene can stand there or name it"
    if isinstance(loc, dict) and not loc.get("what"):
        return "has no `what` - a scene staged there has nothing to perceive of it (gate reads it on a match)"
    return None


def _law(row, world, ctx):
    from .law import _normalise_law
    _normalise_law(row, "a law")


def _laws(rows, world, ctx):
    """The list as a whole: ids unique, `excepts` naming laws that exist (law.py's own projection). A law that fails
    on its own is reported once, as that entry - the projection would only refuse it again."""
    from .law import _normalise_law, _project_laws
    try:
        for i, row in enumerate(rows or []):
            _normalise_law(row, "laws[%d]" % i)
    except (ValueError, TypeError):
        return None
    _project_laws(world)


def _cue_classes(names, world, ctx):
    have = set(((world.get("lexicon") or {}).get("attribute_classes") or {}) if isinstance(world.get("lexicon"), dict) else ())
    unknown = [n for n in (names or []) if isinstance(n, str) and n not in have]
    if unknown:
        return ("names %s, which lexicon.attribute_classes does not define - it matches nothing, silently"
                % ", ".join(repr(n) for n in unknown))
    return None


def _systems(block, world, ctx):
    from . import systems
    systems.for_book(world)


def _tensions(rows, world, ctx):
    from . import tensions
    tensions.from_world(world)


WORLD = (
    F("world", "text", status="runtime", reader="narrate", doc="the world's title; the note's id when absent"),
    F("timeline", "text", reader="narrate", doc="which spine in book.json the narrator reads"),
    F("season", "any", status="unread", doc="nothing reads it; a season that must reach a character goes in the scene"),
    # ---- who can be perceived ------------------------------------------------------------------------------------
    F("people", "list", reader="presence; bible; attachments; acquisition", doc="everyone a character can perceive or name",
      absent="EMPTY - entity recognition has nothing to recognize, and every relationship edge is disabled with it; "
             "people/*.md notes load only when their frontmatter says type: person"),
    F("people[]", "map", check=_person, reader="presence.named_in"),
    F("people[].id", "text", reader="presence.named_in; bible; scene.subject_groups",
      doc="the join: its first word is the name the text is searched for"),
    F("people[].what", "text", reader="presence (shown on a passed insight check); bible; critic"),
    F("people[].name", "text", reader="facets; scene._display_names; acquisition.overheard_names",
      doc="the name said aloud; the id, title-cased, when absent"),
    F("people[].groups", "list", reader="attachments.names_for; scene.subject_groups",
      doc="group tags - grp.<tag> attachments and regard; a LIST (a string is read letter by letter)"),
    F("people[].groups[]", "text", reader="attachments.names_for"),
    # ---- where a scene can stand --------------------------------------------------------------------------------
    F("locations", "list", reader="gate._lookup_location; attachments; bible; critic",
      absent="EMPTY - no scene can produce a location percept"),
    F("locations[]", "map", check=_place, reader="gate._lookup_location"),
    F("locations[].id", "text", reader="gate._lookup_location; attachments; bible"),
    F("locations[].what", "text", reader="gate._lookup_location; bible; critic", doc="what a character perceives of the place"),
    F("locations[].name", "text", reader="scene._holds_display_name", doc="the name a hold is shown by; `what`, then the id"),
    # ---- what perception looks for --------------------------------------------------------------------------------
    F("lexicon", "map", reader="gate._lexicon; facets", doc="the world's perception vocabulary",
      absent="absent - perception falls back to generic extraction (the event's kind and leading words), thin"),
    F("lexicon.attribute_classes", "map", reader="gate._extract_event_attributes; facets.topics_in"),
    F("lexicon.attribute_classes.<name>", "list", reader="gate._extract_event_attributes",
      doc="the words that mark the class - a LIST (a string is scanned letter by letter, so almost anything matches)"),
    F("lexicon.attribute_classes.<name>[]", "text", reader="gate._extract_event_attributes"),
    F("lexicon.subtle_cues", "map", reader="gate._extract_subtle_attributes"),
    F("lexicon.subtle_cues.<name>", "list", reader="gate._extract_subtle_attributes", doc="the fine signs a sharp eye catches"),
    F("lexicon.subtle_cues.<name>[]", "text", reader="gate._extract_subtle_attributes"),
    F("lexicon.subtle_cue_classes", "list", check=_cue_classes, reader="gate._has_subtle_cues",
      doc="which attribute classes count as subtle; each must be an attribute_classes key"),
    F("lexicon.subtle_cue_classes[]", "text", reader="gate._has_subtle_cues"),
    # ---- what the world refuses ------------------------------------------------------------------------------------
    F("laws", "list", check=_laws, reader="law._project_laws; scene (the pre-flight, _law_events)",
      doc="the blueprint's default laws apply too, unless blueprint_defaults is false",
      absent="EMPTY - only the blueprint's default laws apply; this world adds none of its own"),
    F("laws[]", "map", check=_law, reader="law._normalise_law"),
    F("laws[].id", "text", reader="law._normalise_law"),
    F("laws[].statement", "text", reader="law._normalise_law"),
    F("laws[].domain", "text", reader="law._normalise_law"),
    F("laws[].modality", "text", reader="law._normalise_law", doc="IMPOSSIBLE | FORBIDS | REQUIRES | PERMITS"),
    F("laws[].epistemic", "text", reader="law._normalise_law"),
    F("laws[].act", "text", reader="law._applies; scene (the act vocabulary shown to the actor)"),
    F("laws[].location_scope", "text", reader="law._applies"),
    F("laws[].actor_class", "text", reader="scene._law_events"),
    F("laws[].target_class", "text", reader="bible (stored; nothing supplies a target class yet)"),
    F("laws[].time_from", "number", reader="law._applies", doc="a tick - a text value raises mid-run"),
    F("laws[].time_to", "number", reader="law._applies", doc="a tick - a text value raises mid-run"),
    F("laws[].teeth", "any", reader="law.verdict_for; scene (printed)"),
    F("laws[].excepts", "any", reader="law._normalise_law; law._project_laws",
      doc="PERMITS only: the law ids this one excepts, a list or a comma-separated line"),
    F("laws[].source_note", "any", status="unread", doc="stored with the law; nothing reads it back"),
    F("blueprint_defaults", "bool", reader="law._blueprint_defaults",
      doc="false turns the five default laws off - only a literal false does"),
    F("switches", "map", reader="law.completeness (strict bible builds only)", doc="magic / divine / beings, answered"),
    F("switches.<name>", "any", reader="law.completeness"),
    # ---- which systems run, and what the world watches ----------------------------------------------------------------
    F("systems", "delegated", check=_systems, reader="systems.for_book", doc="switch a system on or off for this book"),
    F("tensions", "delegated", check=_tensions, reader="tensions.from_world; keeper", doc="standing tensions the world keeps"),
    F("standing_facts", "any", reader="critic (out of the loop; never perception)", doc="facts only the critic reads"),
)
