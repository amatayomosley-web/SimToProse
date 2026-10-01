"""facets.py — what a belief is ABOUT, stamped when the belief is written.

THE PROBLEM THIS SOLVES, measured 2026-08-30. A belief carried its claim as prose and nothing
structural. Recall then matched that prose against a bag of words pulled out of the scene's props,
by raw substring. Two consequences, both observed on a live book:

  * Beliefs qualified on accidents. In one scene the winning belief matched on 'out' (inside
    "about") and 'low' (inside "Hollow"); `levers.py` had already fixed exactly this defect for
    lever rows, calling it "a wound going off at random", and the fix was never ported here.
  * The beliefs a scene was ABOUT could not say so. Nell's "Tam Rill is not a coward about work"
    matched seven of the scene's triggers and stayed silent; her "They are animals" matched one and
    fired. Across two characters and twelve beliefs, ELEVEN carried an empty `links` list — the
    entity axis existed in the schema and was empty in practice, because it depended on an author
    remembering to bracket a name.

THE FIX IS AT THE WRITE, NOT THE MATCH. A matcher can never recover a referent the prose expressed
as a pronoun — "He will come up that hill one day" is about Tam and says "He". But whoever WRITES
the belief knows: the three runtime writers hold the resolved subject already, and the author knows
who they meant. So the structure is stamped at creation and rides ALONGSIDE the claim, which stays
prose because the claim is what reaches the page through the narrator.

  about  : [entity_id]     who or what this belief concerns
  topics : [lexicon class]  which of the world's own attribute classes it touches

Both are derived from vocabularies the engine already owns — `world.people` and
`world.lexicon.attribute_classes` — so there is no second typing list to rot out of sync with the
first. That is the defect this repo has paid for seven times over.

Deterministic, stdlib only, no LLM, no randomness.
"""
from __future__ import annotations

import re

from .gate import _lexicon, _normalize
from .presence import mentions, names_of


def _mentions(word, text):
    """Word-boundary containment for a cue word, never raw substring - `presence.mentions` with gate's normaliser.

    `levers.py` learned this the expensive way: raw `in` fired a row keyed on a short word against
    two unrelated words that merely contained it. The rule itself lives in presence.py since 2026-10-01; a cue
    PHRASE here keeps containment (`bounded_phrases=False`), as wounds and topics always read it.
    """
    return mentions(word, text, _normalize, bounded_phrases=False)


def entities_in(text, world):
    """-> [entity_id] for every person the world knows who is NAMED in this text.

    Matches every form `presence.names_of` gives (the id's first word, the id, the whole name, the aliases), each
    as bounded words - the list and the rule perception reads too. Absence is a real answer: a belief that refers
    to someone only as "he" resolves to nothing here, and that is precisely the case only the writer can settle.
    """
    t = _normalize(str(text or ""))
    found = []
    for person in (world or {}).get("people", []) or []:
        if not isinstance(person, dict):
            continue
        pid = str(person.get("id", "") or "")
        if pid and any(mentions(c, t, _normalize) for c in names_of(person)):
            found.append(pid)
    return sorted(set(found))


def topics_in(text, world):
    """-> [attribute class] for every lexicon class this text touches.

    The SAME classes the event percept already gets (`gate._extract_event_attributes`), and
    deliberately WITHOUT that function's generic floor — it appends the text's own leading words
    when nothing matches, which is a sensible fallback for describing an event and useless as a
    topic: it produced "They are animals. They are hungry" as a belief's topic in testing. A belief
    that touches no declared class has no topics, and says so.
    """
    t = _normalize(str(text or ""))
    classes, _cues, _cc = _lexicon(world or {})
    return sorted(cls for cls, words in (classes or {}).items()
                  if any(_mentions(kw, t) for kw in words))


def belief_facets(claim, world, subject=None, place=None):
    """claim (+ what the writer already knows) -> {"about": [...], "topics": [...]}.

    `subject` is the authoritative answer and always wins: the three runtime writers hold the
    RESOLVED subject of the turn, which is right even when the prose says "he". Names found in the
    claim are added to it, never instead of it — a belief may be about someone it never names, and
    may name someone it is not about.
    """
    about = []
    for s in (subject if isinstance(subject, (list, tuple)) else [subject]):
        if s:
            about.append(str(s))
    about.extend(entities_in(claim, world))
    facets = {"about": sorted(set(about)), "topics": topics_in(claim, world)}
    if place:
        facets["place"] = str(place)
    return facets


def stamp(belief, world, subject=None, place=None):
    """Add facets to a belief dict IN PLACE and return it.

    Additive by contract: `about` merges with any links the author bracketed rather than replacing
    them. Never overwrites a non-empty value a caller set deliberately.
    """
    if not isinstance(belief, dict):
        return belief
    f = belief_facets(belief.get("claim", ""), world, subject=subject, place=place)
    merged = set(f["about"]) | {str(l) for l in (belief.get("links") or []) if l}
    belief["about"] = sorted(merged)
    belief["topics"] = f["topics"]
    if "place" in f:
        belief.setdefault("place", f["place"])
    return belief
