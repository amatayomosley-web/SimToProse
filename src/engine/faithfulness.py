"""faithfulness.py — the deterministic half of the faithfulness guard: catch NAME leaks in a turn.

knowledge-model.md "omniscience leak at decision time": the masking wall (gate.scope_names) keeps a
name a character hasn't acquired OUT of the prompt — but the model can still emit it from its WEIGHTS
(latent knowledge the engine can't see). This catches that, deterministically: if a character's turn
USES the name of an entity they know only by a descriptor (`known_as` != the name), that name was
never in their context — it leaked from the substrate. Detect-and-surface; the model-critic (a Sonnet
subagent, when the book is Claude-orchestrated) is the rewrite/reject half, layered on top of this flag.
Pure; no LLM.
"""
import re

from .gate import _normalize


def check_name_leaks(text, relationships):
    """Return [(name, known_as)] for every entity whose NAME appears in `text` but whom this character
    knows only by a DESCRIPTOR (their edge's `known_as` is not the name) — a latent leak the masking
    wall could not prevent. Empty list = clean. Pure, deterministic; mirrors gate.scope_names but
    DETECTS in the OUTPUT instead of masking the INPUT."""
    if not isinstance(text, str) or not isinstance(relationships, dict):
        return []
    leaks = []
    for pid, rel in relationships.items():
        if not isinstance(rel, dict):
            continue
        known_as = rel.get("known_as")
        if not known_as:
            continue                                      # they know the canonical name -> using it is fine
        name = str(pid).split("_")[0]
        if len(name) < 2 or _normalize(name) == _normalize(str(known_as)):
            continue                                      # known_as IS the name -> not a leak
        if re.search(r"\b%s\b" % re.escape(name), text, re.IGNORECASE):
            leaks.append((name, str(known_as)))
    return leaks


# The stop-list exists because a fact key is a PHRASE and phrases share words. Matching a fact by
# its rarest content word would fire on "the" or "fever" alone; matching the whole phrase would miss
# ordinary variation. So the rule below is deliberately the strict one — the WHOLE phrase, on word
# boundaries — and what it misses is stated rather than papered over.
_FACT_MIN_WORDS = 2


def check_fact_leaks(text, char_id, information):
    """Return [(fact, knowers)] for every TRACKED fact this character states without knowing it.

    THE WALL WAS NAME-SHAPED. `check_name_leaks` masks "Aldric" when the character knows him only as
    "the man from the docks". It does not catch "the man from the docks is here" when the character
    should not know he is from the docks at all. Not every secret is a name: a relationship, an
    intention, a location, a debt, a parentage — none were caught, and all of them leak.

    The registry to check against already existed and was built for something else.
    `snapshot["information"]` is a `fact -> [knowers]` map, folded from `reveal` events
    (`ledger._project`). An actor stating a fact it is not a knower of is the fact-shaped twin of a
    name it does not hold, and it is detected the same way: in the OUTPUT, because the leak can come
    from the model's weights or from an omniscient director's prose, and neither is visible to the
    input wall.

    WHAT THIS MISSES, said plainly because a guard reports on what it READS. It matches the fact's
    PHRASE, so a paraphrase escapes — "she is lying about the fever" will not match a fact keyed as
    "the fever will not break". That is a floor, not a ceiling, the same limit `claims.py` states
    for structural contradiction. Deliberately not softened with a similarity score: hard rule 4
    forbids nondeterminism here, and a tuned threshold that silently mislabels is worse than a
    strict rule that says what it does not cover.

    An empty or absent registry returns [] — a run before anything was revealed has no facts to
    leak, and that must not read as a clean bill of health for facts nobody tracked.
    """
    if not isinstance(text, str) or not isinstance(information, dict):
        return []
    leaks = []
    for fact, knowers in information.items():
        fact = str(fact or "").strip()
        if len(fact.split()) < _FACT_MIN_WORDS:
            continue                                  # too short to match without firing on prose
        known = [str(k) for k in (knowers or [])]
        if char_id is not None and str(char_id) in known:
            continue                                  # they know it — stating it is theirs to state
        if re.search(r"\b%s\b" % re.escape(fact), text, re.IGNORECASE):
            leaks.append((fact, sorted(known)))
    return leaks
