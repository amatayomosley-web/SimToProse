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

from . import law as _law
from . import writeonce as _once

# RE-EXPORTED so the 130-odd `bible.X` call sites are untouched by the split — the same move
# `ledger.py` makes for `SNAPSHOT_KINDS`. The law half lives in `law.py`; this is its front door.
completeness      = _law.completeness
law_exists        = _law.law_exists
laws_bearing_on   = _law.laws_bearing_on
verdict_for       = _law.verdict_for
require_allowed   = _law.require_allowed
_project_laws     = _law._project_laws          # tests/test_bible.py reaches for it by name
_normalise_law    = _law._normalise_law
_authored_laws    = _law._authored_laws
_DOMAINS          = _law._DOMAINS
_MODALITIES       = _law._MODALITIES

# ONE CLASS, DEFINED WHERE NOTHING IMPORTS UPWARD. The split briefly gave `bible` and `law` each
# their own `BibleError`, so a refusal raised in `law.py` was a DIFFERENT class from the one every
# test and caller catches as `bible.BibleError` — eleven tests went red at once, which is the
# duplicate-spelling defect appearing inside the fix for a duplicate. It lives in `law.py` because
# `bible` imports `law` and never the reverse.
BibleError = _law.BibleError

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
        raise BibleError("BIBLE_NOT_JSON_SERIALIZABLE", "bible is not JSON-serialisable: %s" % e)

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
            raise BibleError("BIBLE_WORLD_STEP1_INCOMPLETE", "world has not answered step 1 (universal-law.md): %s"
                             % "; ".join("[%s] %s" % (p["code"], p["detail"])
                                         for p in report["problems"]))
    fp = fingerprint(world, characters)
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # PROJECT BEFORE WRITING, AND WRITE IN ONE TRANSACTION. Both restructurings, 2026-09-03, forced
    # by routing this through `write_once`: its DB_TRANSACTION_OPEN precondition fired on
    # `tests/test_laws.py`, which was the guard reporting a defect that had always been here.
    #
    # `_project_laws` VALIDATES, and it ran AFTER the bibles row and the entity rows were written,
    # with the executemany calls outside any transaction context — so a malformed law raised with a
    # partial bible sitting uncommitted on the connection, and the next `build` there read its own
    # uncommitted write.
    #
    # OF THE TWO CHANGES, ONLY `_write` IS LOAD-BEARING, and saying so is the point: breakage-tested
    # 2026-09-03, putting `_project_laws` back after the inserts leaves `in_transaction` False and
    # zero rows behind, because `write_once`'s single transaction now rolls them back. Hoisting the
    # two pure projections above the write is DEFENSIVE — it costs nothing to reject a bad law
    # before touching the database — and it is not what closed the leak. A comment that credited
    # the reordering would send the next reader to protect the wrong line.
    rows = _project_entities(world, characters)
    laws = _project_laws(world)          # authored + surviving blueprint defaults; RAISES if bad

    def _check():
        return con.execute("SELECT 1 FROM bibles WHERE fingerprint=?", (fp,)).fetchone() is not None

    def _write():
        con.execute("INSERT INTO bibles(fingerprint, built_at, world, characters) VALUES(?,?,?,?)",
                    (fp, stamp, json.dumps(world, sort_keys=True, ensure_ascii=False),
                     json.dumps(characters, sort_keys=True, ensure_ascii=False)))
        con.executemany(
            "INSERT OR IGNORE INTO bible_entities(fingerprint, kind, entity_id, what) VALUES(?,?,?,?)",
            [(fp, k, eid, what) for k, eid, what in rows])
        con.executemany(
            "INSERT OR IGNORE INTO bible_laws(fingerprint, law_id, domain, modality, statement, act, "
            "actor_class, target_class, location_scope, time_from, time_to, teeth, epistemic, "
            "source_note, excepts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(fp, l["law_id"], l["domain"], l["modality"], l["statement"], l["act"], l["actor_class"],
              l["target_class"], l["location_scope"], l["time_from"], l["time_to"], l["teeth"],
              l["epistemic"], l["source_note"], l["excepts"]) for l in laws])

    # A bible is keyed by CONTENT, so a second build of the same one is a replay by definition and
    # the check returns True. What routing adds is the re-ask: two runs opening the same book at
    # once both passed this SELECT, and one then hit `bibles.fingerprint`'s PRIMARY KEY, raising a
    # bare IntegrityError out of the module that pins hard rule 1.
    _once.write_once(con, _check, _write)
    return fp

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
            raise BibleError("BIBLE_ENTITY_KIND_UNKNOWN", "unknown entity kind %r (known: %s)" % (kind, ", ".join(_KINDS)))
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
