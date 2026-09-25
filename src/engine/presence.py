"""presence.py — being NAMED to someone is not being IN THE ROOM with them.

Two questions the engine asked as one until this module existed:

    who does this beat's text NAME?     -> gate._extract_named_entities
    who is BODILY HERE?                 -> the caller's cast list

Conflating them had two costs, opposite in direction and both silent. A person merely spoken of
was rendered to the actor at channel "visual" — seen, in a room they are not in — and, wherever a
relationship row existed, took an EDGE and appeared under "Those present". Meanwhile the true
object of a feeling, when they were elsewhere, could not be named as the event's subject at all,
so news that a third party had ruined you could only be ABOUT the messenger who carried it.

Measured on a live twelve-rung walk: every passage exempted the person in the room, and the anger
had nowhere to go but out the door.

The distinction is OPT-IN per caller, by sentinel: a scene slice with no `present` key means
presence is UNKNOWN and every named entity reads as present, exactly as before. Only a driver that
actually knows its cast supplies the list. That is what keeps this change a no-op for the
single-character driver, which has no roster to build one from.

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

from .records import PATHS, RecordError, RELATIONSHIP_AXES


def match(entity_id, present_set):
    """Is this extracted entity id one of the ids the caller says is bodily here?

    THE TWO SIDES ARE NOT THE SAME ID SPACE, and assuming they were is the defect this function
    exists to prevent. The extractor yields the FULL people-registry id — often `<name>_<role>` —
    while matching on its first part alone; a cast list is written in the short ids the character
    sheets use. Compared raw, `<name>_<role>` is not in `{<name>}`, EVERY present cast member is
    classified ABSENT, and the scene loses all its edges with nothing raised. Measured on this
    repo's own test fixture the day the presence list was introduced.

    So the join uses the extractor's OWN key: the full id, or its first underscore-part.
    """
    if entity_id in present_set:
        return True
    head = str(entity_id).split("_")[0]
    return bool(head) and head in present_set


def referenced_ids(percepts):
    """Entity ids this character heard NAMED this turn and is NOT standing with.

    The companion to `edges` for `resolve_subject`: what you can be angry AT, over and above who
    you are in the room with. Empty for every caller that does not track presence, which is what
    keeps this a no-op for the single-character driver.
    """
    if not isinstance(percepts, list):
        raise RecordError("GATE_PERCEPTS_NOT_A_LIST", "referenced_ids: percepts must be a list")
    out = [str(p.get("ref", ""))[len("entity."):] for p in percepts
           if isinstance(p, dict) and p.get("present") is False
           and str(p.get("ref", "")).startswith("entity.")]
    return sorted(dict.fromkeys(out))          # SORTED = hard rule 4, same reason as _build_edges


def display_name(entity_id):
    """Canonical display name from an entity id: 'first_last' -> 'First Last',
    'solo' -> 'Solo'. What an actor sees for someone they know. Never an engine id form."""
    return " ".join(w.capitalize() for w in str(entity_id).split("_") if w) or str(entity_id)


def named_in(text, world, normalize):
    """Return [(entity_id, entity_label, [observable_attrs])] for known entities mentioned.

    Identity derives from world.people. NAMING is all this establishes — whether they are HERE is
    `match`'s question, and conflating the two is the defect this module exists to prevent.
    `normalize` is passed in rather than duplicated, so there is one spelling of it (gate.py's).
    """
    t = normalize(text)
    results = []

    for person in world.get("people", []):
        pid   = person.get("id", "")
        what  = person.get("what", "")
        # Check if this person's name appears in the event text
        name_parts = pid.replace("_", " ").split()
        first_name = name_parts[0] if name_parts else ""
        if first_name and normalize(first_name) in t:
            # Observable attributes: role/description from world (not secret)
            # We expose only the role description, not inner motivations
            observable = [what] if what else [first_name]
            results.append((pid, first_name.capitalize(), observable))

    return results


def _character(pid, own):
    """The book's character a person among the world's people IS -> their id, or None: their own id when it is one,
    else the first part of it (a cast is written in the short ids, the world's people as `<name>_<role>`)."""
    head = pid.split("_")[0]
    return pid if pid in own else (head if head in own else None)


def one_per_name(people, here, own, at, walked_on):
    """A NAME MEANS ONE PERSON (gate one-person-per-name, the owner 2026-09-25) -> the ids of the people this scene's
    names do NOT mean, sorted: their ids among the world's people and their characters' ids, so both spaces can drop them.

    Two people can share a name: a younger version of a character is a character of their own ("the scene calls
    character, younger versions is a character"), whose place among the world's people carries an id beginning with
    the name. `named_in` matches on the name, so "Mira" named both, and in a flashback with the young one in the room
    the grown one became a third party spoken of. For each name several people share, it means: whoever of that name
    is here; if no one is, whoever the story is at - the one who first walked on at or before `at`, the latest if
    several; if neither, all of them, as before. A person who is a character of their own is here by their own id
    only: `match("mira_young", {"mira"})` is True, so the grown one in the room would have brought the young one too.

    `here` the character ids in the room; `own` the book's character ids; `at` this scene's time in minutes, or None
    (no clock: the room decides alone); `walked_on(character id)` -> the minutes their own story began, or None.
    """
    own, here, groups = set(own or ()), set(here or ()), {}
    for p in people or ():
        pid = str((p or {}).get("id") or "") if isinstance(p, dict) else ""
        if pid:
            groups.setdefault(pid.split("_")[0].lower(), []).append(pid)
    out = set()
    for ids in groups.values():
        if len(ids) < 2:
            continue
        meant = [i for i in ids if i in here or _character(i, own) in here]
        if not meant and at is not None:
            began = {i: walked_on(_character(i, own)) for i in ids if _character(i, own)}
            began = {i: m for i, m in began.items() if m is not None and m <= at}
            meant = [i for i, m in began.items() if m == max(began.values())] if began else []
        for i in ([] if not meant else ids):
            if i not in meant:
                out.add(i)
                if _character(i, own) not in {_character(m, own) for m in meant}:
                    out.add(_character(i, own))
    return sorted(x for x in out if x)


def world_meant(world, elsewhere):
    """The world as this scene's names read it: without the people `one_per_name` says they do not mean. The one
    copy every name reader takes - perception, and the beliefs a scene writes, whose `about` is stamped by name
    (`facets.stamp`): a memory of the grown Mira made in the present was also "about" the young one."""
    drop = set(elsewhere or ())
    if not drop:
        return world
    return dict(world, people=[p for p in (world.get("people") or []) if not (isinstance(p, dict) and p.get("id") in drop)])


def rels_meant(relationships, elsewhere):
    """A character's relationships as this scene's names read them - what the prompt masks by, the leak check reads
    and an overheard name teaches: an edge to the Mira the name does not mean is not in it."""
    drop = set(elsewhere or ())
    return {k: v for k, v in (relationships or {}).items() if k not in drop}


def present_unnamed(present_set, named_ids, world, me=None):
    """[(entity_id, label, [observable_attrs])] for the people BODILY HERE whom the text did not name.

    PRESENT IS SEEN (2026-09-18). `named_in` yields only the people the event text names, and on a
    scene's opener the text is the authored opening prose, which need not name the cast. On the
    first live scene the emotion seat's `about: <the other man in the room>` was refused as not
    perceived while the event seat — shown THE PEOPLE from the cast list — accepted him as the act's
    object: the two seats saw different rooms. A person the driver says is here is perceived as
    here whether or not the prose names them; WHO they are still passes the recognition check in
    gate.perception_scope, exactly as a named person does. The perceiver is never a percept of
    themself. `named_ids` are the registry ids `named_in` already yielded; joined on `match`'s key.
    """
    if not present_set:
        return []
    me_key = str(me or "").strip().lower()
    named = {str(n) for n in (named_ids or ())} | {str(n).split("_")[0] for n in (named_ids or ())}
    people = {str(p.get("id", "")): p for p in (world.get("people", []) or []) if isinstance(p, dict) and p.get("id")}
    out = []
    for pid in sorted(str(x) for x in present_set):
        key = pid.strip().lower()
        if not key or key == me_key or key.split("_")[0] == me_key.split("_")[0]:
            continue
        if pid in named or pid.split("_")[0] in named:
            continue
        # the registry's own id when the cast id is its first part; else the cast id as given. Its own id first: a
        # younger version's `mira_young` answers to `mira` too (gate one-person-per-name)
        full = pid if pid in people else next((rid for rid in people if match(rid, {pid})), pid)
        what = str((people.get(full) or {}).get("what") or "")
        out.append((full, display_name(full.split("_")[0]), [what] if what else []))
    return out


def present_ids(percepts):
    """The ids of the entities a PerceptSet holds as PRESENT -> sorted list.

    THE ONE PRESENCE RULE, used by `build_edges` (who you stand with) and by the manifest's
    `present` key (who witnessed this beat, read by `scene_facts`). REFERENCED IS NOT PRESENT: a
    percept marked `present: False` is someone spoken of, and is skipped. An ABSENT flag (a caller
    that does not track presence) counts as present, which is `build_edges`' long-standing reading.

    WHY IT IS A FUNCTION NOW (2026-09-22). The fact ledger's first version read every `entity.<id>`
    percept key as a witness, because the manifest recorded the refs and dropped this flag. A person
    matched by first-name substring inside an ordinary word was a present:False percept, took no edge here,
    and still received four facts from a room he never entered. Two consumers with two copies of the
    rule is how that happened; one function is how it stops.
    """
    out = set()
    for p in percepts or ():
        if p.get("present") is False:
            continue
        ref = p.get("ref", "")
        if ref.startswith("entity.") and len(ref) > len("entity."):
            out.add(ref[len("entity."):])
    return sorted(out)


def build_edges(current, percepts, world, elsewhere=()):
    """Build in-scene relationship edges to present entities.

    scene-assembly.md §"Volatile body": relationship edges to present entities.
    Only emit edges for entities that actually appear in the PerceptSet (recognized_as
    or entity refs) AND have a relationship record. `elsewhere`: the people this scene's names do not mean
    (`one_per_name`) - the name fallback below would otherwise hand the grown Mira an edge in the young one's scene.

    Returns list of {target, trust, affinity, respect, debt, history}.
    """
    elsewhere = set(elsewhere or ())
    relationships = current.get("relationships", {})
    edges = []
    seen  = set()

    # Collect entity ids from percepts — the presence rule lives in `present_ids`, once.
    present_entity_ids = set(present_ids(percepts))
    for p in percepts:
        # REFERENCED IS NOT PRESENT: the recognized_as fallback below must not re-admit by name
        # someone `present_ids` already refused. `.get` returning None is not False, so callers that
        # do not track presence are untouched.
        if p.get("present") is False:
            continue
        # also check recognized_as for partial name matches
        rec = p.get("recognized_as", "")
        if rec:
            for rel_id in relationships:
                if rel_id.startswith(rec.lower()) and rel_id not in elsewhere:
                    present_entity_ids.add(rel_id)

    # SORTED = hard rule 4. Walking the SET gave hash order, which varies per PROCESS: the e2e
    # exited 0 then 1 on identical --stub runs (2026-09-01, tests/test_scene.py holds the guard).
    for entity_id in sorted(present_entity_ids):
        if entity_id in seen:
            continue
        rel = relationships.get(entity_id)
        if rel and isinstance(rel, dict):
            edge = edge_from_rel(entity_id, rel)
            # WHAT THIS PERSON STIRS is set by scene.assemble from the BALANCE (2026-09-12) — what
            # they move the played vector by relative to the mood — under the key `stirs`, never
            # `toward`: tests/test_toward.py [6] holds that word out of the prompt as the guard that
            # the NUMBER never reaches the actor; the words may, the key name must not.
            edges.append(edge)
            seen.add(entity_id)

    return edges


def edge_from_rel(entity_id, rel):
    """One relationship row -> one edge. ONE definition, because there are now two callers:
    `_build_edges` for the parties PRESENT, and `assemble`'s subject-edge branch for the party this
    beat is ABOUT when they are elsewhere. Two copies is how those would quietly diverge.
    """
    edge = {
        "target":  entity_id,
        # the actor's OWN term for this entity: known_as (a descriptor when they don't know
        # the name) else the canonical display name. NEVER the raw id (the seam law).
        "label":   rel.get("known_as") or display_name(entity_id),
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
    return edge


