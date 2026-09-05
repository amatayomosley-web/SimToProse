"""faults.py — the engine-fault detector: the machine-side twin of the chair's world-fault inbox.

`detect_world_faults` (scripts/direct.py) catches *"the sim reached for world CONTENT that doesn't
exist"* and queues it to the operator's `world-faults.md`. This catches *"the sim reached for a
REPRESENTATION the engine can't express"* — it aggregates the per-turn consolidation flags already
persisted in the ledger (`turns.validation`, schema.sql) across a run and surfaces any failure-reason
that RECURS past a threshold as a named engine-fault.

The realization behind it: the escalation critic already fires per-turn; nobody was watching the
*pattern*. One escalation is noise. The same reason recurring across turns is a structural gap — a
missing tag type, a dead dimension, a mis-cast character. The flagship case: a dimension
(`social_violation`) that NO actor-taggable type legitimizes, so every social scene flags — the
vocabulary lacks a home for it.

Pure read-side: reads the ledger, applies the consolidation CATALOG vocabulary, returns structured
faults. Never writes the book (the seam — engine-faults are a developer signal, not world content).
Stdlib only.

LIMIT (documented): this only catches gaps that TRIP an existing check. A *silent* gap — the LLM
picks a type that is dimension-legal but semantically wrong (tagging a slight `loss` to dodge the
flag) — throws no flag and is invisible here. Catching those needs the actor to self-report "none of
these fit" (a prompt signal) — a clean v2.
"""
import json
from .records import RecordError   # rule 6's bad-input type
import re

from .consolidation import CATALOG

# Class-B calibration: a reason recurring at/above BOTH of these is a structural gap, not noise.
_MIN_COUNT = 2
_MIN_FRACTION = 0.10
_ESCALATION_HOT = 0.40        # escalation rate at/above this on a run flags the run itself
_UNUSED_TYPE_MIN_TURNS = 10   # only call a type "unused" over a run long enough to mean it
_PRIMARY_DIM = 0.5            # a dimension at/above this is a primary driver (matches consolidation _MISMATCH_THRESHOLD)

_SYSTEM_TYPES = ("turn-skipped", "correction")

# code -> the structural reason kind the fault-miner aggregates on. Before 2026-08-30 flags were
# PROSE and this was four regexes plus a catch-all that mapped every "schema:" flag to
# ("schema-other", None) — which _ACTIONABLE then excluded. So the miner counted the recurring
# reason and dropped it, printing "(none — the vocabulary fit this run)" while every beat of a live
# scene was being discarded for a missing enum. The code IS the key now; nothing is recovered.
_CODE_TO_KIND = {
    "TAG_DIMENSION_NOT_IN_APPRAISAL_MAP": "dim-unsupported",
    "TAG_DIMENSION_UNKNOWN":              "unknown-dim",
    "TAG_TYPE_UNKNOWN":                   "unknown-type",
    "TAG_TARGET_NOT_PERCEIVED":           "target-not-perceived",
    "TAG_CAPABILITY_BELOW_REQ":           "capability-miss",
    "TAG_DURABILITY_MISSING":             "durability-missing",
    "TAG_DURABILITY_INVALID":             "durability-invalid",
    "TAG_DIMENSION_VALUE_NOT_NUMERIC":    "dim-value-invalid",
    "TAG_DIMENSION_VALUE_RANGE":          "dim-value-invalid",
    "TAG_CONFIDENCE_NOT_NUMERIC":         "confidence-invalid",
    "TAG_CONFIDENCE_RANGE":               "confidence-invalid",
    "TAG_DIMENSIONS_TYPE":                "dimensions-not-a-dict",
    "TAG_TYPE_NOT_ACTOR_OFFERED":         "type-not-actor-offered",
}

# The SUBJECT is what to fix, extracted from the flag's detail where one exists. SEARCH, not match:
# the details read "unknown dimension 'wibble'" and "unknown type 'frobnicate'", so anchoring at ^
# found neither. Left-to-right order does the right thing for the compound cases — a dim-unsupported
# detail names the dimension before the type, and the DIMENSION is the thing without a home.
_SUBJECT_RE = re.compile(r"(?:dimension|type|skill) '([^']+)'")


def _actor_taggable_types():
    """The pure-appraisal types an actor may self-tag.

    Was a third hand-maintained copy of this derivation (prompt.py had one, validate_tags used the
    whole CATALOG instead). Now imported from the one place that owns it, beside CATALOG itself.
    """
    from .consolidation import ACTOR_TAG_TYPES
    return set(ACTOR_TAG_TYPES)


def reason_key(flag):
    """One validation flag -> a structural (kind, subject) key.

    The SUBJECT is what to fix. For a dim-unsupported flag it is the DIMENSION (which has no home),
    NOT the type that happened to be chosen — the same dimension failing across types IS the gap.

    Accepts the legacy prose shape so a validation blob stored before 2026-08-30 still aggregates;
    a legacy flag has no code and lands in ("other", None), which is honest — its structure was
    never recoverable, it was only guessed at.
    """
    code = flag.get("code") if isinstance(flag, dict) else None
    if code is None:
        return ("other", None)
    kind = _CODE_TO_KIND.get(code)
    if kind is None:
        return ("other", None)
    m = _SUBJECT_RE.search(str(flag.get("detail", "")))
    return (kind, m.group(1) if m else None)


def _message(kind, subject, count, turns):
    if kind == "dim-unsupported":
        return ("dimension %r was loaded as a primary driver but NO chosen actor-type legitimized it "
                "(%d/%d turns) — the actor tag vocabulary likely lacks a class for %r; add an "
                "actor-taggable type whose appraisal_map includes %r." % (subject, count, turns, subject, subject))
    if kind == "unknown-dim":
        return "dimension %r was emitted but is not a known dimension (%d/%d turns) — typo or a missing dimension." % (subject, count, turns)
    if kind == "unknown-type":
        return "type %r was emitted but is not in the CATALOG (%d/%d turns) — the actor reached for a type that does not exist." % (subject, count, turns)
    if kind == "target-not-perceived":
        return "a tag named a target absent from the PerceptSet (%d/%d turns) — perception or subject-resolution mis-fit." % (count, turns)
    if kind == "capability-miss":
        return "skill %r fell below a type's capability_req (%d/%d turns) — the actor is mis-cast, or the requirement is mis-set." % (subject, count, turns)
    if kind == "durability-missing":
        return ("%d/%d turns omitted `durability` entirely — the actor is not being told to emit it, "
                "or the reply contract does not require it. Every one of those beats was refused." % (count, turns))
    if kind == "durability-invalid":
        return ("%d/%d turns sent a durability value outside {transient, durable} — most often the "
                "'marking'/'reshaping' vocabulary that older docs taught and the validator has never "
                "accepted (standard-vectors.md:144)." % (count, turns))
    if kind == "dim-value-invalid":
        return "a dimension magnitude was non-numeric or outside [0,1] (%d/%d turns)." % (count, turns)
    if kind == "confidence-invalid":
        return "the self-rated confidence was non-numeric or outside [0,1] (%d/%d turns)." % (count, turns)
    if kind == "dimensions-not-a-dict":
        return "tags.dimensions arrived as something other than a dict (%d/%d turns)." % (count, turns)
    if kind == "type-not-actor-offered":
        return ("type %r is in the CATALOG but is never offered to an actor (%d/%d turns) — it folds "
                "to the world unchecked." % (subject, count, turns))
    return "reason %r recurred (%d/%d turns)." % (kind, count, turns)


# Reason kinds that are genuine engine-faults when they recur. The schema kinds are IN this list
# now. They were excluded when they were an unstructured "schema-other" bucket, and that exclusion
# is exactly why a run in which every single beat failed on a missing `durability` reported clean.
_ACTIONABLE = ("dim-unsupported", "unknown-dim", "unknown-type", "target-not-perceived",
               "capability-miss", "durability-missing", "durability-invalid",
               "dim-value-invalid", "confidence-invalid", "dimensions-not-a-dict",
               "type-not-actor-offered")


def scan_run(ledger, run_id, min_count=_MIN_COUNT, min_fraction=_MIN_FRACTION):
    """Read a run's turns; aggregate validation flags + tag stats; return structured engine-faults.

    Returns {"faults": [fault, ...], "stats": {...}}. A fault is
    {kind, subject, count, turns, fraction, actors, message, severity}.
    Pure read; the ledger raises on an unknown run. Fail loud on a bad ledger handle."""
    if not hasattr(ledger, "con"):
        raise RecordError("FAULT_LEDGER_HANDLE_INVALID", "scan_run: ledger must be a Ledger (got %r)" % type(ledger).__name__)
    rows = ledger.con.execute(
        "SELECT turn, actor, tags, validation FROM turns WHERE run_id = ? ORDER BY turn", (run_id,)).fetchall()
    total = len(rows)
    if total == 0:
        return {"faults": [], "stats": {"turns": 0, "escalations": 0, "escalation_rate": 0.0,
                                        "types_used": [], "dims_used": []}}

    reason_counts = {}      # (kind, subject) -> count of TURNS exhibiting it
    reason_actors = {}      # (kind, subject) -> set(actors)
    escalations = 0
    used_types, used_dims = set(), set()
    for r in rows:
        try:
            val = json.loads(r["validation"] or "{}")
            tags = json.loads(r["tags"] or "{}")
        except (TypeError, ValueError):
            val, tags = {}, {}
        if val.get("escalate"):
            escalations += 1
        if tags.get("type"):
            used_types.add(tags["type"])
        for d, v in (tags.get("dimensions", {}) or {}).items():
            try:
                if float(v) >= _PRIMARY_DIM:
                    used_dims.add(d)
            except (TypeError, ValueError):
                pass
        seen = set()
        for flag in val.get("flags", []):
            key = reason_key(flag)
            if key in seen:
                continue            # count TURNS exhibiting a reason, not raw flags
            seen.add(key)
            reason_counts[key] = reason_counts.get(key, 0) + 1
            reason_actors.setdefault(key, set()).add(r["actor"])

    faults = []
    for (kind, subject), count in sorted(reason_counts.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        if kind not in _ACTIONABLE:
            continue
        frac = count / total
        if count >= min_count and frac >= min_fraction:
            faults.append({
                "kind": kind, "subject": subject, "count": count, "turns": total,
                "fraction": round(frac, 3), "actors": sorted(reason_actors[(kind, subject)]),
                "message": _message(kind, subject, count, total),
                "severity": "high" if frac >= 0.5 else "medium"})

    if total >= _UNUSED_TYPE_MIN_TURNS:      # unused-vocabulary companion (only meaningful over a real run)
        for t in sorted(_actor_taggable_types() - used_types):
            faults.append({"kind": "unused-type", "subject": t, "count": 0, "turns": total,
                           "fraction": 0.0, "actors": [],
                           "message": "actor type %r was never used across %d turns — possibly redundant or mis-named." % (t, total),
                           "severity": "low"})

    esc_frac = escalations / total
    if esc_frac >= _ESCALATION_HOT and total >= 3:
        faults.append({"kind": "escalation-rate-hot", "subject": None, "count": escalations, "turns": total,
                       "fraction": round(esc_frac, 3), "actors": [],
                       "message": "escalation critic fired on %d/%d turns (%.0f%%) — vocabulary or a character is mis-fit; see the recurring reasons above." % (escalations, total, esc_frac * 100),
                       "severity": "high" if esc_frac >= 0.6 else "medium"})

    stats = {"turns": total, "escalations": escalations, "escalation_rate": round(esc_frac, 3),
             "types_used": sorted(used_types), "dims_used": sorted(used_dims)}
    return {"faults": faults, "stats": stats}


def render(result):
    """Render a scan result as the developer-facing engine-fault report (printed at park)."""
    if not isinstance(result, dict):
        raise RecordError("FAULT_SCAN_RESULT_INVALID", "render: result must be the dict scan_run returns")
    faults = result.get("faults", [])
    stats = result.get("stats", {})
    if stats.get("turns", 0) == 0:
        return "  engine-faults: no turns to scan."
    out = ["  engine-faults — %d turn(s), escalation rate %.0f%%"
           % (stats["turns"], stats.get("escalation_rate", 0.0) * 100)]
    if not faults:
        out.append("    (none — the vocabulary fit this run)")
    for f in faults:
        tag = {"high": "GAP ", "medium": "gap ", "low": "note"}.get(f.get("severity", "medium"), "gap ")
        loc = ("  [%s]" % ", ".join(f["actors"])) if f.get("actors") else ""
        out.append("    %s %s%s" % (tag, f["message"], loc))
    return "\n".join(out)
