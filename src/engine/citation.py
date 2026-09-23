"""citation.py — the grounding contract's enforcement core.

Every assertion the orchestrator makes about the world must resolve to a row.
This module parses citation tokens, resolves them against the run DB, and returns
a verdict over a whole ENVELOPE (docs/orchestrator-design.md §4).

Three resolution states, not two (docs/orchestrator-design.md §6, from Vela's
degenerate-signal guard): a token can RESOLVE, fail to resolve (UNRESOLVED), or be
UNVERIFIABLE — the namespace is real but no store backs it yet. Conflating the
third with either of the others is the bug this design exists to avoid: treating
"no checker" as "checker says no" makes the orchestrator useless, and treating it
as "checker says yes" makes it a liar. UNVERIFIABLE is surfaced, never silently
resolved either way.

The check lives OUTSIDE the model on purpose (grounding.md forcing layer 3) — an
LLM cannot police its own grounding; a deterministic resolver can.

No LLM calls here. No randomness. Fails loud on malformed input.
"""
from __future__ import annotations

__layer__ = "engine"

import re

from . import bible
from .errors import EngineError

# --- resolution states ----------------------------------------------------
RESOLVED = "resolved"
UNRESOLVED = "unresolved"
UNVERIFIABLE = "unverifiable"

# --- envelope vocabulary (docs/orchestrator-design.md §4) -----------------
KINDS = ("ANSWER", "VERDICT", "DIAGNOSIS", "PROPOSAL", "REPORT", "NOTICE")
MODES = ("cited", "derived")

_TOKEN = re.compile(r"^([a-z_]+):(.+)$")


class CitationError(EngineError):
    """Malformed citation token or envelope — a contract breach, never a verdict."""


class Citation:
    """A parsed token. `kind` names the namespace; `args` its parts."""

    __slots__ = ("raw", "kind", "args")

    def __init__(self, raw, kind, args):
        self.raw = raw
        self.kind = kind
        self.args = args

    def __repr__(self):  # pragma: no cover - debug aid
        return "Citation(%r)" % self.raw


def parse(token):
    """'turn:14' -> Citation. Raises CitationError on anything malformed."""
    if not isinstance(token, str) or not token.strip():
        raise CitationError("CITATION_TOKEN_EMPTY", "citation must be a non-empty string, got %r" % (token,))
    m = _TOKEN.match(token.strip())
    if not m:
        raise CitationError("CITATION_TOKEN_SHAPE", "citation %r is not '<kind>:<args>'" % token)
    kind, rest = m.group(1), m.group(2)
    if kind not in _known():
        raise CitationError("CITATION_NAMESPACE_UNKNOWN",
            "unknown citation namespace %r (known: %s)"
            % (kind, ", ".join(sorted(_known())))
        )
    return Citation(token.strip(), kind, rest.split(":"))


def _known():
    """Every namespace `parse` accepts. `entity` and `law` are neither table
    resolvers nor unbacked — they resolve against the run's pinned bible, so they
    must be named here explicitly or parse would reject them as unknown."""
    return set(_RESOLVERS) | set(_UNBACKED) | {"entity", "law"}


# --- per-namespace resolvers ---------------------------------------------
# Each returns True when the cited row exists. Signature: (con, run_id, args).
# Arity is checked before dispatch, so a resolver never sees the wrong shape.

def _one(con, sql, params):
    return con.execute(sql, params).fetchone() is not None


def _r_turn(con, run_id, a):
    return _one(con, "SELECT 1 FROM turns WHERE run_id=? AND turn=? LIMIT 1", (run_id, _int(a[0])))


def _r_event(con, run_id, a):
    return _one(con, "SELECT 1 FROM events WHERE run_id=? AND event_id=? LIMIT 1", (run_id, _int(a[0])))


def _r_scene(con, run_id, a):
    return _one(con, "SELECT 1 FROM scenes WHERE run_id=? AND scene_no=? LIMIT 1", (run_id, _int(a[0])))


def _r_belief(con, run_id, a):
    return _one(
        con,
        "SELECT 1 FROM acquisitions WHERE run_id=? AND char_id=? AND acquisition_id=? LIMIT 1",
        (run_id, a[0], _int(a[1])),
    )


def _r_state(con, run_id, a):
    return _one(
        con,
        "SELECT 1 FROM current_state WHERE run_id=? AND char_id=? AND turn=? LIMIT 1",
        (run_id, a[0], _int(a[1])),
    )


def _r_edge(con, run_id, a):
    return _one(
        con,
        "SELECT 1 FROM relationship_deltas WHERE run_id=? AND delta_id=? LIMIT 1",
        (run_id, _int(a[0])),
    )


def _r_snapshot(con, run_id, a):
    return _one(
        con,
        "SELECT 1 FROM snapshots WHERE run_id=? AND as_of_turn=? AND kind=? AND key=? LIMIT 1",
        (run_id, _int(a[0]), a[1], a[2]),
    )


# namespace -> (resolver, expected arg count)
_RESOLVERS = {
    "turn": (_r_turn, 1),
    "event": (_r_event, 1),
    "scene": (_r_scene, 1),
    "belief": (_r_belief, 2),
    "state": (_r_state, 2),
    "edge": (_r_edge, 1),
    "snapshot": (_r_snapshot, 3),
}

# Namespaces that are real but have no store yet (docs/orchestrator-design.md §7.1
# designs the tables; they are unbuilt). These resolve UNVERIFIABLE — the gap stays
# loud instead of failing closed and blocking every lore claim.
_UNBACKED = {
    "chronicle": "no chronicle store yet (orchestrator-design.md §7.1)",
}


def _int(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        raise CitationError("CITATION_ARG_NOT_INT", "citation expected an integer, got %r" % (s,))


def resolve_one(con, run_id, token):
    """-> (state, detail). Never raises on a *missing* row; raises only on a
    malformed token, which is a contract breach rather than a verdict."""
    c = token if isinstance(token, Citation) else parse(token)
    if c.kind in _UNBACKED:
        return UNVERIFIABLE, _UNBACKED[c.kind]
    if c.kind in ("entity", "law"):
        # Backed by the bible pinned to THIS run. A run with no pinned bible
        # yields UNVERIFIABLE, not UNRESOLVED: "no store" is not "no such
        # entity", and conflating them is the bug the three-state design exists
        # to prevent.
        if len(c.args) != 1:
            raise CitationError("CITATION_ARITY_MISMATCH", "citation %r takes 1 argument, got %d" % (c.raw, len(c.args)))
        pinned = bible.for_run(con, run_id)
        if pinned is None:
            return UNVERIFIABLE, "this run pinned no bible (predates bible-in-db)"
        lookup = bible.entity_exists if c.kind == "entity" else bible.law_exists
        ok, detail = lookup(con, pinned[0], c.args[0])
        return (RESOLVED, detail) if ok else (UNRESOLVED, detail)
    fn, arity = _RESOLVERS[c.kind]
    if len(c.args) != arity:
        raise CitationError("CITATION_ARITY_MISMATCH",
            "citation %r takes %d argument(s), got %d" % (c.raw, arity, len(c.args))
        )
    if fn(con, run_id, c.args):
        return RESOLVED, ""
    return UNRESOLVED, "no such row"


# --- envelope verification -----------------------------------------------

class Verdict:
    """The gate's answer over one envelope."""

    __slots__ = ("allowed", "failures", "unverifiable", "checked", "unknowns")

    def __init__(self, allowed, failures, unverifiable, checked, unknowns):
        self.allowed = allowed
        self.failures = failures            # [(claim_index, token, detail)]
        self.unverifiable = unverifiable    # [(claim_index, token, detail)]
        self.checked = checked              # total tokens resolved
        self.unknowns = unknowns            # count of declared gaps

    def reason(self):
        if self.allowed:
            return ""
        return "; ".join(
            "claim[%d] cites %s — %s" % (i, t, d) for i, t, d in self.failures
        )

    def as_dict(self):
        return {
            "allowed": self.allowed,
            "failures": [list(f) for f in self.failures],
            "unverifiable": [list(u) for u in self.unverifiable],
            "checked": self.checked,
            "unknowns": self.unknowns,
        }


def verify_envelope(envelope, con, run_id):
    """Resolve every citation in an ENVELOPE. -> Verdict.

    DENIES on any UNRESOLVED token. UNVERIFIABLE tokens do NOT deny — they are
    collected and surfaced, because a missing store is not a negative verdict.
    Raises CitationError on a malformed envelope (a contract breach, not a
    judgement: the caller sent something that isn't an envelope at all).
    """
    if not isinstance(envelope, dict):
        raise CitationError("CITATION_ENVELOPE_NOT_A_DICT", "envelope must be a dict, got %r" % type(envelope).__name__)
    kind = envelope.get("kind")
    if kind not in KINDS:
        raise CitationError("CITATION_ENVELOPE_KIND_UNKNOWN", "envelope kind %r not in %s" % (kind, ", ".join(KINDS)))

    claims = envelope.get("claims", [])
    if not isinstance(claims, list):
        raise CitationError("CITATION_ENVELOPE_CLAIMS_TYPE", "envelope 'claims' must be a list")
    unknowns = envelope.get("unknowns", [])
    if not isinstance(unknowns, list):
        raise CitationError("CITATION_ENVELOPE_UNKNOWNS_TYPE", "envelope 'unknowns' must be a list")

    failures, unverifiable, checked = [], [], 0

    for i, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise CitationError("CITATION_CLAIM_NOT_A_DICT", "claim[%d] must be a dict" % i)
        mode = claim.get("mode")
        if mode not in MODES:
            raise CitationError("CITATION_CLAIM_MODE_UNKNOWN", "claim[%d] mode %r not in %s" % (i, mode, ", ".join(MODES)))
        field = "cite" if mode == "cited" else "from"
        tokens = claim.get(field, [])
        if not isinstance(tokens, list):
            raise CitationError("CITATION_CLAIM_TOKENS_TYPE", "claim[%d] %r must be a list" % (i, field))
        if not tokens:
            # A cited/derived claim with no support is the failure this gate exists
            # for. It is a VERDICT, not a contract breach — deny, don't raise.
            failures.append((i, "(none)", "%s claim carries no %s" % (mode, field)))
            continue
        for tok in tokens:
            state, detail = resolve_one(con, run_id, tok)
            checked += 1
            if state == UNRESOLVED:
                failures.append((i, tok, detail))
            elif state == UNVERIFIABLE:
                unverifiable.append((i, tok, detail))

    return Verdict(not failures, failures, unverifiable, checked, len(unknowns))
