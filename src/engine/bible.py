"""bible.py — pin the authored bible into the run DB, and make entities exact.

Two problems, one store.

THE REPLAY HOLE. `vault.load_book()` re-parses the markdown on every invocation
and the result was never recorded. `Ledger.create_run` pins catalog_version,
models and prompt_versions — but nothing identifying the bible. So editing a
character sheet at turn 40 silently changed what turns 1-39 were computed from,
and `Ledger.resume` could not see it: it asserts the fold of the event LOG is
deterministic, not that the INPUTS which produced that log are unchanged. A run
that cannot say what it ran against cannot honestly claim to replay.

THE UNBACKED NAMESPACE. `citation.py` returned UNVERIFIABLE for every `entity:`
token because no entity store existed. "Does this person exist" must be exact
set-membership (orchestrator-design.md 7.1) — a gate cannot be built on a
similarity guess, because a near-miss resolves to the WRONG entity while looking
grounded.

Keyed by FINGERPRINT, not run_id: a bible is usually unchanged across many runs
(the live book has 34), so fingerprinting pins and deduplicates in one move.
Two runs sharing a bible share a row; a run whose bible drifted gets a new one,
and the drift is visible by comparison rather than by trust.

Deterministic, no randomness, no LLM. Fails loud.
"""
from __future__ import annotations

__layer__ = "engine"

import hashlib
import json
from datetime import datetime, timezone
from .errors import EngineError

CONFIG_KEY = "bible_fingerprint"   # what a run stores to name its bible

_KINDS = ("character", "person", "location")

# The domains follow the authoring blueprint, not an invented taxonomy.
# universal-law.md's step-1 rubric names five (A-E); present-systems.md's step-4
# rubric names the social ones. A law about whether souls persist, or whether
# the future is fixed, must have somewhere to go — earlier versions of this enum
# dropped three of the five and silently rejected them.
_DOMAINS = (
    # step 1 — universal law (universal-law.md A-E)
    "physical", "supernatural", "persons", "fate", "cosmology",
    # step 4 — present systems (present-systems.md)
    "legal", "custom", "economic",
)
_MODALITIES = ("IMPOSSIBLE", "FORBIDS", "REQUIRES", "PERMITS")

# universal-law.md mandates THREE epistemic values, not two. The third is the
# one that matters: `contested-unknowable` is a world that DELIBERATELY never
# decides whether the gods are real. Treating it as `known-true` invents a fact
# the author refused to fix; treating it as `known-false` does the same in the
# other direction. It makes the verdict UNDECIDABLE — the same no-signal-is-not-
# rejection rule the citation resolver already runs on.
_EPISTEMIC = ("known-true", "known-false", "contested-unknowable")
_EPISTEMIC_ALIASES = {"true": "known-true", "believed": "known-false"}

# Only IMPOSSIBLE denies. This is the rule the whole store exists for: a gate
# that denied every ILLEGAL act would make crime unwritable (orchestrator-design
# 7.1). A character breaking a law is not a gate failure -- it is the story, and
# the gate's job there is to make sure the CONSEQUENCE lands as a real event.
_DENYING = ("IMPOSSIBLE",)

# --- the blueprint's own defaults ------------------------------------------
# universal-law.md meta-rule 2: "Default to mundane / earthlike; the premise
# must JUSTIFY each deviation... the bias is 'no, unless.'" That is not advice,
# it is a law set. An author does not start from a blank world; they start from
# the mundane one and OVERRIDE it. Without these, a book that has answered none
# of step 1 builds green and can refuse nothing.
#
# One default per domain A-E of universal-law.md's rubric, and each is
# ACT-SHAPED because _applies() matches on `act` — a law the gate can never
# reach is decoration. `epistemic` is stated explicitly (never left to the
# omitted-means-known-true path): a mundane world's mundanity is known-true,
# and these rows must not trip the epistemic check they help enforce.
_DEFAULTS_VERSION = 1
_BLUEPRINT_DEFAULTS = (
    {"id": "default-no-flight", "domain": "physical", "modality": "IMPOSSIBLE",
     "act": "fly", "epistemic": "known-true",
     "statement": "People cannot fly.",
     "why": "A — physical law: default earthlike (universal-law.md:26)"},
    {"id": "default-no-magic", "domain": "supernatural", "modality": "IMPOSSIBLE",
     "act": "cast", "epistemic": "known-true",
     "statement": "There is no magic.",
     "why": "B — the supernatural switch: default off (universal-law.md:32)"},
    {"id": "default-death-is-final", "domain": "persons", "modality": "IMPOSSIBLE",
     "act": "resurrect", "epistemic": "known-true",
     "statement": "The dead do not return.",
     "why": "C — death is final; this is the stakes floor (universal-law.md:38)"},
    {"id": "default-future-is-open", "domain": "fate", "modality": "IMPOSSIBLE",
     "act": "foresee", "epistemic": "known-true",
     "statement": "The future is not fixed and cannot be foreseen.",
     "why": "D — causation & fate: default open (universal-law.md:42)"},
    {"id": "default-one-plane", "domain": "cosmology", "modality": "IMPOSSIBLE",
     "act": "planar-travel", "epistemic": "known-true",
     "statement": "The physical world is all there is; there is nowhere else to go.",
     "why": "E — cosmological structure: default one plane (universal-law.md:50)"},
)

# The switches that must be answered even if shallow (universal-law.md:12) —
# the exception to "settle only what's levered", because everything downstream
# forks on them. All three live in domain B, so a `true` switch with no
# supernatural law is the hollow-probe case universal-law.md:18 names.
_SWITCHES = ("magic", "divine", "beings")
_SWITCH_DOMAIN = "supernatural"

# Where the known-vs-believed check is mandatory (universal-law.md:19). Not
# `physical` — earthlike physics is not a matter of in-world belief — and not
# the step-4 social domains, whose truth-status is never in question.
_EPISTEMIC_REQUIRED_IN = ("supernatural", "persons", "fate", "cosmology")


class BibleError(EngineError):
    """A bible could not be projected — named loudly, never coerced."""


def _canonical(world, characters):
    """A stable byte form of the authored bible.

    Hashes the PARSED structures, not the raw markdown: a whitespace or prose
    edit that leaves the engine payload untouched must NOT read as drift. A
    guard that cries wolf is a guard that gets switched off.
    """
    if not isinstance(world, dict):
        raise BibleError("BIBLE_WORLD_NOT_A_DICT", "world must be a dict, got %s" % type(world).__name__)
    if not isinstance(characters, dict):
        raise BibleError("BIBLE_CHARACTERS_NOT_A_DICT", "characters must be a dict, got %s" % type(characters).__name__)
    try:
        return json.dumps({"world": world, "characters": characters},
                          sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise BibleError("BIBLE_INVALID", "bible is not JSON-serialisable: %s" % e)


def fingerprint(world, characters):
    """The bible's identity. Same content -> same fingerprint, always."""
    return hashlib.sha256(_canonical(world, characters)).hexdigest()


def _project_entities(world, characters):
    """-> [(kind, entity_id, what)] — everything the bible says exists.

    Three sources, because a citation may name any of them: the cast
    (characters), the world's people, and its locations.
    """
    out = []
    for cid in sorted(characters):
        sheet = characters[cid] or {}
        fixed = sheet.get("fixed") or {}
        out.append(("character", str(cid), str(fixed.get("name") or cid)))
    for p in (world.get("people") or []):
        if not isinstance(p, dict) or not p.get("id"):
            continue
        out.append(("person", str(p["id"]), str(p.get("what") or "")))
    for loc in (world.get("locations") or []):
        if not isinstance(loc, dict) or not loc.get("id"):
            continue
        out.append(("location", str(loc["id"]), str(loc.get("what") or "")))
    return out


def _normalise_law(law, where):
    """One raw law dict -> one projected row. Fails LOUD, never coerces.

    A rule the gate will cite must be exactly what the author wrote; a
    silently-repaired law is a denial nobody can explain.
    """
    if not isinstance(law, dict):
        raise BibleError("BIBLE_NOT_A_DICT", "%s must be a dict" % where)
    lid = str(law.get("id") or "").strip()
    if not lid:
        raise BibleError("BIBLE_ID_LAW_INVALID", "%s has no id — a law must be citable" % where)
    statement = str(law.get("statement") or "").strip()
    if not statement:
        raise BibleError("BIBLE_LAW_STATEMENT_INVALID", "law %r has no statement — a denial must be able to quote the rule" % lid)
    domain = str(law.get("domain") or "").strip()
    if domain not in _DOMAINS:
        raise BibleError("BIBLE_LAW_DOMAIN_NOT_IN_SET", "law %r domain %r not in %s" % (lid, domain, ", ".join(_DOMAINS)))
    modality = str(law.get("modality") or "").strip().upper()
    if modality not in _MODALITIES:
        raise BibleError("BIBLE_LAW_MODALITY_NOT_IN_SET", "law %r modality %r not in %s" % (lid, modality, ", ".join(_MODALITIES)))
    epistemic = str(law.get("epistemic") or "known-true").strip().lower()
    epistemic = _EPISTEMIC_ALIASES.get(epistemic, epistemic)
    if epistemic not in _EPISTEMIC:
        raise BibleError("BIBLE_LAW_EPISTEMIC_NOT_IN_SET", "law %r epistemic %r not in %s" % (lid, epistemic, ", ".join(_EPISTEMIC)))
    # excepts: the NARROW form of PERMITS — disarm only the named law ids.
    # Absent = the documented general allowance (orchestrator-design.md
    # modality table). PERMITS-only; anywhere else it fails loud.
    excepts = law.get("excepts")
    if excepts is not None and modality != "PERMITS":
        raise BibleError("BIBLE_EXCEPTS_ONLY_INVALID", "law %r: excepts is only meaningful on a PERMITS row" % lid)
    if isinstance(excepts, str):
        excepts = excepts.replace(",", " ").split()
    if excepts is not None:
        if (not isinstance(excepts, list) or not excepts
                or not all(isinstance(e, str) and e.strip() for e in excepts)):
            raise BibleError("BIBLE_EXCEPTS_NAME_INVALID", "law %r: excepts must name at least one law id" % lid)
        excepts = [e.strip() for e in excepts]
    return {
        "law_id": lid, "domain": domain, "modality": modality, "statement": statement,
        "act": str(law.get("act") or ""), "actor_class": str(law.get("actor_class") or ""),
        "target_class": str(law.get("target_class") or ""),
        "location_scope": str(law.get("location_scope") or ""),
        "time_from": law.get("time_from"), "time_to": law.get("time_to"),
        "teeth": str(law.get("teeth") or ""), "epistemic": epistemic,
        "source_note": str(law.get("source_note") or ""),
        "excepts": " ".join(excepts or []),
    }


def _authored_laws(world):
    """-> [row] for what the author actually wrote. No defaults."""
    raw = world.get("laws") or []
    if not isinstance(raw, list):
        raise BibleError("BIBLE_WORLD_LAWS_NOT_A_LIST", "world 'laws' must be a list, got %s" % type(raw).__name__)
    out, seen = [], set()
    for i, law in enumerate(raw):
        row = _normalise_law(law, "laws[%d]" % i)
        if row["law_id"] in seen:
            raise BibleError("BIBLE_DUPLICATE_LAW_DUPLICATE", "duplicate law id %r" % row["law_id"])
        seen.add(row["law_id"])
        out.append(row)
    return out


def _blueprint_defaults(authored, world):
    """-> [row] the mundane laws the author inherits without writing a line.

    SUPPRESSION IS ACT-KEYED AND DUMB, deliberately. A default drops out only
    when the author declared a law with the same `act` (or the same id) —
    never by inferring "they wrote something supernatural, so they must mean
    magic exists." Inference would silently remove a default, which is exactly
    the invisible behaviour this whole mechanism exists to end. What the author
    wrote always wins; what they did not write is visible as `default-*` in
    every refusal that cites it.

    Opt out entirely with `world["blueprint_defaults"] = False` — for a world
    whose step 1 is fully authored and wants no phantom rules.
    """
    if world.get("blueprint_defaults") is False:
        return []
    taken_acts = {r["act"] for r in authored if r["act"]}
    taken_ids = {r["law_id"] for r in authored}
    out = []
    for d in _BLUEPRINT_DEFAULTS:
        if d["act"] in taken_acts or d["id"] in taken_ids:
            continue
        row = dict(d)
        why = row.pop("why")
        row["source_note"] = "blueprint-default v%d — universal-law.md %s" % (_DEFAULTS_VERSION, why)
        out.append(_normalise_law(row, "blueprint default %r" % d["id"]))
    return out


def _project_laws(world):
    """-> [row] authored laws first, then whichever defaults survive.

    Cross-validates excepts here, against the FINAL row set, because a permit
    may legitimately except a blueprint default (e.g. default-no-flight)."""
    authored = _authored_laws(world)
    rows = authored + _blueprint_defaults(authored, world)
    ids = {r["law_id"] for r in rows}
    for r in rows:
        missing = [e for e in r["excepts"].split() if e not in ids]
        if missing:
            raise BibleError("BIBLE_EXCEPTS_CITE_UNKNOWN", "law %r: excepts cite unknown law ids %s"
                             % (r["law_id"], ", ".join(missing)))
    return rows


def completeness(world):
    """Has step 1 been ANSWERED? -> {"complete": bool, "problems": [...]}.

    Three checks, each traced to the line of universal-law.md that demands it.
    The guide is a rubric of questions, and most may be left "undetermined until
    levered" — these are the ones that may not.

      switch-unanswered   :12  the switches (magic / divine / beings) must be
                               answered even if shallow; everything forks on them
      unbounded-switch    :18  "a power with no stated limit is the director's
                               get-out-of-jail card and makes the probe hollow"
      epistemic-unstated  :19  every supernatural element carries known-true /
                               known-false / contested-unknowable — omitting it
                               silently fixes the ground truth as known-true,
                               which may be a fact the author never chose

    REPORTS, does not enforce. Whether an incomplete world may run is the
    orchestrator's policy call (orchestrator-design.md §7); a checker that
    aborted here would block every book that adopts the store incrementally.
    """
    problems = []
    switches = world.get("switches")
    if not isinstance(switches, dict):
        switches = {}
    answered = {}
    for name in _SWITCHES:
        val = switches.get(name)
        if not isinstance(val, bool):
            problems.append({
                "code": "switch-unanswered", "switch": name,
                "detail": "the %r switch is unanswered — universal-law.md:12 makes the three "
                          "switches the exception to 'settle only what's levered', because "
                          "planet, history and present all fork on them" % name,
            })
        else:
            answered[name] = val

    authored = _authored_laws(world)
    if any(answered.get(n) for n in _SWITCHES):
        if not [r for r in authored if r["domain"] == _SWITCH_DOMAIN]:
            on = sorted(n for n in _SWITCHES if answered.get(n))
            problems.append({
                "code": "unbounded-switch", "switch": ", ".join(on),
                "detail": "%s declared to exist, and no %s law bounds it — universal-law.md:18: "
                          "a power with no stated limit is the director's get-out-of-jail card "
                          "and makes the probe hollow. State what it CANNOT do."
                          % (", ".join(on), _SWITCH_DOMAIN),
            })

    for i, law in enumerate(world.get("laws") or []):
        if not isinstance(law, dict):
            continue
        row = _normalise_law(law, "laws[%d]" % i)
        if row["domain"] in _EPISTEMIC_REQUIRED_IN and not law.get("epistemic"):
            problems.append({
                "code": "epistemic-unstated", "law": row["law_id"],
                "detail": "law %r is in domain %r and states no `epistemic` — it will bind as "
                          "known-true. universal-law.md:19 makes the known-vs-believed call "
                          "mandatory here; say so, or say contested-unknowable."
                          % (row["law_id"], row["domain"]),
            })

    return {"complete": not problems, "problems": problems}


def build(con, world, characters, now=None, strict=False):
    """Store the bible and its entities; return the fingerprint.

    IDEMPOTENT: rebuilding an identical bible is a no-op, not a duplicate. The
    same book rebuilt across many runs must not grow the table.

    `strict=True` refuses to build a world that has not answered step 1 (see
    completeness). OFF by default — the live book has zero laws, and a store
    that cannot be adopted incrementally does not get adopted.
    """
    if strict:
        report = completeness(world)
        if not report["complete"]:
            raise BibleError("BIBLE_WORLD_ANSWERED_INVALID", "world has not answered step 1 (universal-law.md): %s"
                             % "; ".join("[%s] %s" % (p["code"], p["detail"])
                                         for p in report["problems"]))
    fp = fingerprint(world, characters)
    existing = con.execute("SELECT 1 FROM bibles WHERE fingerprint=?", (fp,)).fetchone()
    if existing is not None:
        return fp
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    con.execute("INSERT INTO bibles(fingerprint, built_at, world, characters) VALUES(?,?,?,?)",
                (fp, stamp, json.dumps(world, sort_keys=True, ensure_ascii=False),
                 json.dumps(characters, sort_keys=True, ensure_ascii=False)))
    rows = _project_entities(world, characters)
    con.executemany(
        "INSERT OR IGNORE INTO bible_entities(fingerprint, kind, entity_id, what) VALUES(?,?,?,?)",
        [(fp, k, eid, what) for k, eid, what in rows])
    laws = _project_laws(world)          # authored + surviving blueprint defaults
    con.executemany(
        "INSERT OR IGNORE INTO bible_laws(fingerprint, law_id, domain, modality, statement, act, "
        "actor_class, target_class, location_scope, time_from, time_to, teeth, epistemic, source_note, "
        "excepts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(fp, l["law_id"], l["domain"], l["modality"], l["statement"], l["act"], l["actor_class"],
          l["target_class"], l["location_scope"], l["time_from"], l["time_to"], l["teeth"],
          l["epistemic"], l["source_note"], l["excepts"]) for l in laws])
    con.commit()
    return fp


def law_exists(con, fp, law_id):
    """Exact. -> (bool, detail). What a `law:` citation resolves against."""
    if not fp:
        return False, "no bible pinned for this run"
    row = con.execute("SELECT modality, statement FROM bible_laws WHERE fingerprint=? AND law_id=?",
                      (fp, str(law_id))).fetchone()
    if row is None:
        return False, "no such law in the pinned bible"
    return True, "%s: %s" % (row["modality"], row["statement"])


def _applies(row, act, location, actor_class=None, target_class=None, tick=None):
    """A law bears on a proposed move when its scopes are empty (bears on all) or match.
    Never fuzzy — a near-match would deny the wrong thing.

    SIX SCOPES, NOT TWO (wired 2026-08-30). `actor_class`, `target_class`, `time_from` and
    `time_to` are declared in schema.sql, validated by `_normalise_law`, and stored — and until
    this change NOTHING READ THEM. A law authored to bind one class of person bound everyone; a
    law authored to bind between two ticks bound forever. That is not an unused column: this
    predicate decides IMPOSSIBLE denial, so an unhonoured scope denies acts the author never
    wrote the law to reach.

    Every scope is optional on BOTH sides. An empty column bears on all, and an argument left None
    means the caller cannot supply that facet — which must not silently narrow the law, so it
    bears. That asymmetry is deliberate: a gate that misses a law is a false PASS
    (orchestrator-design 7), and a caller who does not know the actor's class should not be handed
    a quieter world than the author wrote.
    """
    if row["act"] and act is not None and row["act"] != act:
        return False
    if row["location_scope"] and location is not None and row["location_scope"] != location:
        return False
    if row["actor_class"] and actor_class is not None and row["actor_class"] != actor_class:
        return False
    if row["target_class"] and target_class is not None and row["target_class"] != target_class:
        return False
    if tick is not None:
        if row["time_from"] is not None and tick < row["time_from"]:
            return False
        if row["time_to"] is not None and tick > row["time_to"]:
            return False
    return True


def laws_bearing_on(con, fp, act=None, location=None,
                    actor_class=None, target_class=None, tick=None):
    """Every law that bears on a proposed act -> [row dicts]. Exhaustive by
    construction: the gate needs the COMPLETE set, because a miss is a false
    pass (orchestrator-design 7).

    The four scope arguments beyond `act`/`location` all default to None, so every existing caller
    is byte-identical in behaviour; supplying one NARROWS the bearing set to the laws that actually
    reach this actor, this target, at this tick."""
    if not fp:
        return []
    rows = [dict(r) for r in con.execute(
        "SELECT * FROM bible_laws WHERE fingerprint=? ORDER BY law_id", (fp,))]
    return [r for r in rows
            if _applies(r, act, location, actor_class, target_class, tick)]


def verdict_for(con, fp, act=None, location=None,
                actor_class=None, target_class=None, tick=None):
    """Does the world permit this? -> dict.

      allowed  False only when a TRUE, IMPOSSIBLE law bears on it
      denied_by / permitted_by / violations  the rows that decided it
      teeth    consequences a FORBIDS violation attaches

    Four rules do the work.

    1. Only IMPOSSIBLE denies. FORBIDS means the act is against the rules, not
       that it cannot happen, so it returns ALLOWED with its teeth and the
       consequence lands as an event.
    2. Only `known-true` laws bind. A `known-false` one — a superstition —
       never constrains possibility: a world where people believe the dead walk
       is not a world where they do.
    3. `contested-unknowable` yields UNDECIDABLE, not allowed. The author
       deliberately refused to fix the ground truth, so the gate must not invent
       it in either direction. Same rule as an unbacked citation namespace: no
       signal is not a verdict.
    4. A permit's reach is what it declares: unscoped = general allowance over
       every tooth bearing on the act; with `excepts` = only the named laws.
    """
    bearing = laws_bearing_on(con, fp, act, location, actor_class, target_class, tick)
    permits = [r for r in bearing if r["modality"] == "PERMITS"]
    binding = [r for r in bearing if r["epistemic"] == "known-true"]
    undecided = [r for r in bearing
                 if r["epistemic"] == "contested-unknowable" and r["modality"] in _DENYING]
    general = [p for p in permits if not (p.get("excepts") or "").split()]
    scoped_ids = {e for p in permits for e in (p.get("excepts") or "").split()}

    def _disarmed(row):
        return bool(general) or row["law_id"] in scoped_ids

    denies = [r for r in binding if r["modality"] in _DENYING and not _disarmed(r)]
    violations = [r for r in binding
                  if r["modality"] in ("FORBIDS", "REQUIRES") and not _disarmed(r)]
    return {
        "allowed": not denies,
        "undecidable": bool(undecided) and not denies and not permits,
        "undecided_by": [r["law_id"] for r in undecided],
        "denied_by": [r["law_id"] for r in denies],
        "permitted_by": [r["law_id"] for r in permits],
        "violations": [r["law_id"] for r in violations],
        "teeth": [r["teeth"] for r in violations if r["teeth"]],
        "reason": ("; ".join(r["statement"] for r in denies) if denies
                   else "; ".join("%s (%s)" % (r["statement"], r["teeth"] or "no stated consequence")
                                  for r in violations)),
        "considered": [r["law_id"] for r in bearing],
    }


def entity_exists(con, fp, entity_id, kind=None):
    """Exact set-membership. -> (bool, detail).

    Never fuzzy: the gate this feeds must be able to DENY, and a similarity
    match would resolve a fabricated entity to a real one that merely looks
    like it.
    """
    if not fp:
        return False, "no bible pinned for this run"
    sql = "SELECT kind, what FROM bible_entities WHERE fingerprint=? AND entity_id=?"
    params = [fp, str(entity_id)]
    if kind is not None:
        if kind not in _KINDS:
            raise BibleError("BIBLE_UNKNOWN", "unknown entity kind %r (known: %s)" % (kind, ", ".join(_KINDS)))
        sql += " AND kind=?"
        params.append(kind)
    row = con.execute(sql + " LIMIT 1", tuple(params)).fetchone()
    if row is None:
        return False, "no such entity in the pinned bible"
    return True, "%s: %s" % (row["kind"], row["what"] or entity_id)


def for_run(con, run_id):
    """The bible a run was computed against -> (fingerprint, world, characters),
    or None. Runs predating this feature return None rather than raising — the
    book's existing runs must stay readable."""
    row = con.execute("SELECT config FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if row is None:
        return None
    try:
        fp = (json.loads(row["config"]) or {}).get(CONFIG_KEY)
    except (TypeError, ValueError):
        return None
    if not fp:
        return None
    b = con.execute("SELECT world, characters FROM bibles WHERE fingerprint=?", (fp,)).fetchone()
    if b is None:
        return None
    return fp, json.loads(b["world"]), json.loads(b["characters"])


def drifted(con, run_id, world, characters):
    """Has the authored bible changed since this run was made? -> (bool, detail).

    DETECTION ONLY. Acting on drift is the resume path's policy call — shipping
    an abort here would break every run made before fingerprints existed.
    """
    pinned = for_run(con, run_id)
    if pinned is None:
        return False, "run predates bible pinning — nothing to compare"
    current = fingerprint(world, characters)
    if current == pinned[0]:
        return False, "bible unchanged (%s)" % current[:12]
    return True, "bible drifted: run pinned %s, on disk %s" % (pinned[0][:12], current[:12])
