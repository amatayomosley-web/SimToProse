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
