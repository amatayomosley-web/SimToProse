"""acquisition.py — the vault grows: a durable, subject-bearing turn becomes a recallable belief.

knowledge-model.md §"Acquisition during play": experience the ledger records is PROMOTED into the
actor's vault as a belief, so a later turn's recall gate (gate.run_gate) can surface it. The model
never curates its own memory — it sees only the salient slice (the gate's energy budget), so it cannot
know what is new. The ENGINE reads the committed turn + the full vault and decides, DETERMINISTICALLY.
The claim is the actor's own `summary` tag (concise, model-written, already recorded) — never
re-interpreted; provenance "lived" distinguishes a simulated acquisition from an authored .md seed.
Pure; the harness (direct.py:run_turn) persists it (Ledger.append_acquisition) and folds it forward.
"""
import re

from .gate import _normalize, belief_id
from .records import RecordError   # rule 6's bad-input type

from .consolidation import is_durable
from .facets import stamp as _stamp_facets

# The durability predicate is imported, never re-spelled. This module used to carry
# `_DURABLE = ("durable", "marking", "reshaping")` — a THIRD vocabulary, accepting two values
# `consolidation._VALID_DURABILITY` rejects, in the module whose writes are PERMANENT.


def assess(applied, tags, char, world=None):
    """A committed turn -> a belief to acquire, or None. DETERMINISTIC over the recorded turn + vault.

    Promote iff the event is DURABLE (it would mark the actor) AND names a SUBJECT (a memory is ABOUT
    someone). The claim is the actor's own `summary` tag; dedup by exact claim against the existing
    vault so the same lived fact is not stored twice. Returns a belief dict (the caller appends +
    persists) or None. No LLM, no world read — only the committed turn and the actor's own vault.
    """
    if not isinstance(applied, dict) or not isinstance(tags, dict) or not isinstance(char, dict):
        return None
    # NOTE FOR CALLERS: this reads the actor's RAW tags by design — the claim is their own summary.
    # It therefore has no idea whether the tag passed validation, so a caller must NOT invoke it on
    # a turn the engine refused. Both callers were ungated until 2026-08-29, and because they merge
    # the resolved `target` onto `applied` even on ok=False, a schema-invalid turn still had a
    # subject and wrote a PERMANENT vault belief. The gate lives at the call sites now.
    if not is_durable(tags):
        return None                                       # a transient turn leaves no memory
    subject = applied.get("target")
    if not subject:
        return None                                       # a memory is ABOUT someone — no subject, no belief
    summary = str(tags.get("summary", "") or "").strip()
    if not summary:
        return None                                       # nothing concrete to remember
    vault = char.get("current", {}).get("vault", []) or []
    norm = summary.lower()
    for b in vault:                                       # structural dedup: the same lived fact, once
        if isinstance(b, dict) and str(b.get("claim", "")).strip().lower() == norm:
            if not tags.get("supersedes") and b.get("target_actor") == tags.get("target_actor") and b.get("epistemic_stance") == tags.get("epistemic_stance"):
                return None
    try:
        conf = float(tags.get("confidence", 0.8))
    except (TypeError, ValueError):
        conf = 0.8
    return _build_belief(
        summary,
        conf,
        subject,
        tags,
        vault,
        world)


def reveal_name(char, entity_id, name, world=None):
    """The name-reveal as a MONOTONIC acquisition: the character learns an entity's NAME.

    Flips the relationship edge's `known_as` to the name so FUTURE rendering uses it (the masking wall
    stops hiding it: known_as == the name), and appends a belief recording that they learned it. Past
    memories are NOT touched — they keep the framing the character had at the time. You do not rewrite
    "the stranger who helped me" when you learn the name; you ADD the name going forward. The vault is
    monotonic-add (knowledge-model.md). Returns the name-belief to persist, or None if the character has
    no edge to the entity. The caller decides WHEN (a staged reveal moment) — steering is circumstance.
    """
    if not isinstance(char, dict) or not entity_id or not name:
        return None
    rels = char.get("current", {}).get("relationships", {})
    edge = rels.get(str(entity_id))
    if not isinstance(edge, dict):
        return None                                       # no relationship to this entity — nothing to reveal
    old = str(edge.get("known_as", "") or "").strip()
    edge["known_as"] = str(name)                          # FORWARD: future prompts + edge labels render the name
    knew_as = ("the one I knew as '%s'" % old) if old else "the one I had not named"
    belief = _stamp_facets({
        "claim": "%s is named %s" % (knew_as, name),
        "confidence": 1.0,
        "provenance": "learned",
        "believed_value": True,
        "links": [str(entity_id)],
    }, world, subject=entity_id)
    char["current"].setdefault("vault", []).append(belief)  # ADD — prior beliefs are left exactly as they were
    return belief


# TRUST IS THE GAIN ON INFORMATION FLOW (relationships.md, "Trust is load-bearing"): whether a
# bystander records what they heard as a believed fact or a discounted rumour scales with their trust
# in whoever said it. This is the coupling point between the relationship system and the knowledge
# system, and it applies here for a specific reason — `witness_belief` builds the bystander's claim
# out of the ACTOR'S OWN summary, because the engine holds no independent perceptual account of the
# beat. So "witnessing" is, mechanically, taking their word for it.
_WITNESS_BASE = 0.7        # what a witness credits at neutral trust — the old unconditional value
_REPORTED_AT = 0.40        # at or below this trust, the claim is stored as THEIR assertion, not fact
_WITNESS_CEILING = 0.88    # nobody is CERTAIN of another person's account of events. The claim is
                           # built from the actor's own summary, so total conviction in it would be
                           # conviction in THEM. CALIBRATED AGAINST THE BAND, not chosen round:
                           # direction._SURENESS turns over at 0.90 into "you do not entertain the
                           # alternative", so this sits just under it and the most-trusted account
                           # still renders as "you act on it without re-examining it" — believed,
                           # and still a thing someone told you. (0.90 was the first value here and
                           # landed ON the edge, which is the trap guide-emotional-authoring.md
                           # warns about: a number that changed and a rendering that did not.)


def witness_belief(actor_name, tags, actor_id, trust=None, world=None, witness_id=None):
    """What a PRESENT bystander takes from watching `actor` do a durable thing this turn — a belief
    for their own vault. knowledge-model.md transmission: B's vault gains what B saw. Returns the
    belief, or None for a transient turn / no summary. The caller appends it to each present witness's
    vault (with dedup). Deterministic — the actor's own committed summary, lightly de-personed
    ("I forced..." -> "<Actor> forced..."); no LLM.

    `trust` is the WITNESS's trust edge toward the actor. None (the default) keeps the old
    unconditional numbers, so any caller that does not have an edge to hand is unchanged. Supplied,
    it moves three things the actor actually reads — `confidence` (rendered through
    `direction.sureness`), `provenance` (rendered verbatim), and the claim TEXT, which below
    `_REPORTED_AT` is reframed as something this person SAID rather than something that happened.

    It does NOT touch `believed_value`: that field is carried by the gate and dropped at the packet,
    so routing distrust through it would reach nothing — the authored-but-inert defect in a new place.
    """
    if not isinstance(tags, dict):
        return None
    if not is_durable(tags):
        return None
    is_target = bool(witness_id and str(tags.get("target_actor")) == str(witness_id))
    is_epistemic_blind = tags.get("epistemic_stance") in ("ignorant_of", "deceived_about")
    if is_target and is_epistemic_blind:
        if not tags.get("public_summary"):
            return None
        summary = str(tags.get("public_summary")).strip()
    else:
        summary = str(tags.get("public_summary") or tags.get("summary", "") or "").strip()
    if not summary:
        return None
    name = str(actor_name or actor_id or "someone").strip()
    if summary[:2].lower() == "i ":                       # first-person -> third: "I forced..." -> "<Name> forced..."
        claim = "%s %s" % (name, summary[2:].strip())
    else:
        claim = "%s — as I saw it: %s" % (name, summary)

    conf, prov = _WITNESS_BASE, "witnessed"
    if trust is not None:
        try:
            t = max(0.0, min(1.0, float(trust)))
        except (TypeError, ValueError):
            raise RecordError("ACQUISITION_WITNESS_TRUST_INVALID", "witness_belief: trust must be a number in [0,1], got %r" % (trust,))
        conf = round(_WITNESS_BASE * (0.4 + 1.2 * t), 4)   # neutral trust reproduces the base value
        conf = max(0.05, min(_WITNESS_CEILING, conf))
        if t <= _REPORTED_AT:                              # a discounted rumour, kept but attributed
            prov = "reported"
            claim = "%s claims: %s" % (name, summary[2:].strip() if summary[:2].lower() == "i " else summary)
    return _stamp_facets({
        "claim": claim,
        "confidence": conf,
        "provenance": prov,
        "believed_value": True,
        "links": [str(actor_id)],
    }, world, subject=actor_id)


def overheard_names(text, relationships, people):
    """Names spoken aloud in `text` that a present witness (with `relationships`) knows only by a
    DESCRIPTOR — transmission: hearing a name said in the scene is how a bystander learns it
    (knowledge-model.md transmission; rides on witness-propagation). Returns [(entity_id, first_name)]
    for the caller to reveal_name + persist. The canonical name comes from the people registry, never
    guessed; matched on the first name token (what gets spoken). Pure, deterministic. An entity the
    witness already names, or has no edge to, is skipped — new-entity acquisition is a separate path.
    """
    if not isinstance(text, str) or not isinstance(relationships, dict):
        return []
    name_by_id = {p["id"]: str(p.get("name", "")) for p in (people or [])
                  if isinstance(p, dict) and p.get("id")}
    out = []
    for eid, rel in relationships.items():
        if not isinstance(rel, dict) or not rel.get("known_as"):
            continue                                       # no edge data, or they already know the name natively
        first = (name_by_id.get(eid, "") or "").split(" ")[0].strip()
        if len(first) < 2 or _normalize(first) == _normalize(str(rel["known_as"])):
            continue                                       # known_as already IS the name -> nothing to learn
        if re.search(r"\b%s\b" % re.escape(first), text, re.IGNORECASE):
            out.append((eid, first))
    return out


# ---- Track 1: Belief Revision & Contradiction Helpers ----

_POLARITY_PAIRS = (
    ("alive", "dead"),
    ("living", "dead"),
    ("loyal", "traitor"),
    ("innocent", "guilty"),
    ("safe", "danger"),
    ("safe", "threat"),
    ("won", "lost"),
    ("refused", "accepted"),
    ("enemy", "friend"),
    ("enemy", "ally"),
)


def detect_contradiction(new_claim, old_claim):
    """True if new_claim asserts a direct polarity reversal of old_claim."""
    n = _normalize(str(new_claim or ""))
    o = _normalize(str(old_claim or ""))
    if not n or not o:
        return False
    stopwords = {"the", "a", "an", "to", "of", "and", "is", "in", "it", "on", "for", "at", "by", "this", "that", "there"}
    w_n = set(re.findall(r"\b\w+\b", n)) - stopwords
    w_o = set(re.findall(r"\b\w+\b", o)) - stopwords
    if not (w_n & w_o):
        return False
    for pos, neg in _POLARITY_PAIRS:
        n_pos = re.search(r"\b%s\b" % re.escape(pos), n) is not None
        n_neg = re.search(r"\b%s\b" % re.escape(neg), n) is not None
        o_pos = re.search(r"\b%s\b" % re.escape(pos), o) is not None
        o_neg = re.search(r"\b%s\b" % re.escape(neg), o) is not None
        if (n_pos and o_neg) or (n_neg and o_pos):
            return True
    if (re.search(r"\bis not\b", n) and re.search(r"\bis\b", o) and not re.search(r"\bis not\b", o)) or        (re.search(r"\bis not\b", o) and re.search(r"\bis\b", n) and not re.search(r"\bis not\b", n)):
        return True
    if (re.search(r"\bhas no\b", n) and re.search(r"\bhas\b", o) and not re.search(r"\bhas no\b", o)) or        (re.search(r"\bhas no\b", o) and re.search(r"\bhas\b", n) and not re.search(r"\bhas no\b", n)):
        return True
    return False


def fold_vault(vault):
    """Walk vault beliefs in chronological order and mark superseded entries."""
    if not isinstance(vault, list):
        return vault
    by_id = {}
    for b in vault:
        if not isinstance(b, dict):
            continue
        bid = b.get("bid") or belief_id(b)
        b["bid"] = bid
        b.setdefault("status", "active")
        by_id[bid] = b

    for b in vault:
        if not isinstance(b, dict):
            continue
        curr_bid = b.get("bid") or belief_id(b)
        superseded_targets = b.get("supersedes") or []
        for target in superseded_targets:
            if target in by_id and target != curr_bid:
                by_id[target]["status"] = "superseded"
                by_id[target]["superseded_by"] = curr_bid
    return vault


def _build_belief(summary, conf, subject, tags, vault, world):
    superseded_bids = []
    raw_sup = tags.get("supersedes")
    curr_tgt = tags.get("target_actor")
    if raw_sup:
        sup_list = raw_sup if isinstance(raw_sup, (list, tuple)) else [raw_sup]
        for s in sup_list:
            s_str = str(s).strip()
            for b in vault:
                if not isinstance(b, dict):
                    continue
                if b.get("target_actor") != curr_tgt:
                    continue
                bid = b.get("bid") or belief_id(b)
                s_norm = _normalize(s_str)
                c_norm = _normalize(str(b.get("claim", "")))
                if s_str == bid or (s_norm and s_norm == c_norm):
                    superseded_bids.append(bid)

    if subject:
        subj_str = str(subject).lower()
        for b in vault:
            if not isinstance(b, dict) or b.get("status") in ("superseded", "refuted"):
                continue
            if b.get("target_actor") != curr_tgt:
                continue
            b_links = [str(l).lower() for l in (b.get("links") or [])]
            b_about = [str(a).lower() for a in (b.get("about") or [])]
            if subj_str in b_links or subj_str in b_about or subj_str in str(b.get("claim", "")).lower():
                if detect_contradiction(summary, b.get("claim", "")):
                    bid = b.get("bid") or belief_id(b)
                    superseded_bids.append(bid)

    b = {
        "claim": summary,
        "confidence": max(0.0, min(1.0, conf)),
        "provenance": "lived",
        "believed_value": True,
        "links": [str(subject)],
        "status": "active",
    }
    if tags.get("target_actor"):
        b["target_actor"] = str(tags["target_actor"])
        b["epistemic_stance"] = str(tags.get("epistemic_stance", "believes"))
    if superseded_bids:
        b["supersedes"] = sorted(set(superseded_bids))

    return _stamp_facets(b, world, subject=subject)
