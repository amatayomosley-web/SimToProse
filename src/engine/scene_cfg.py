"""scene_cfg.py — the scene cfg a scene ran against, pinned so a replay can name its inputs.

WHY THIS EXISTS, and why it is a module rather than three methods on the ledger. `bible.py` was
written because the bible "was re-parsed per invocation and never recorded, so a mid-book edit
silently changed what earlier turns were computed from" (CLAUDE.md hard rule 1). The scene cfg is
the same class of input — location, cast, props, opening tags — and until schema v14 it had no such
pin: `scenes` recorded the BOUNDARY and nothing about what produced the turns inside it. A resumed
run folded a snapshot it could not explain, and hard rule 2's replay guarantee was not actually held
for scene inputs.

So this file is `bible.py`'s sibling and deliberately copies its shape: fingerprint the parsed
payload, store it content-addressed, and DETECT drift without acting on it. The three rules it
inherits, each for a stated reason:

  * Hash the PARSED payload, never the file bytes — a whitespace or key-order edit that leaves the
    engine's inputs untouched must not read as drift. A guard that cries wolf gets switched off.
  * Content-address the body — fingerprinting pins and DEDUPLICATES in one move, so two scenes run
    from one cfg share a row and are provably the same inputs rather than merely similar ones.
  * Detect, never abort — an author legitimately edits between scenes, and refusing to resume would
    make the common case the error case. `bible.drifted` makes the same call and says so.

Unpinned reads as UNKNOWN, never as UNCHANGED. Scenes recorded before v14 carry an empty
fingerprint; `drifted` returns False with a reason for them, exactly as `bible.for_run` returns None
for runs predating fingerprints.
"""
import hashlib
import json

from .errors import EngineError


class SceneCfgError(EngineError):
    """A scene cfg failed boundary validation. The write that carried it must not happen."""


def fingerprint(cfg):
    """The cfg's identity. Same content -> same fingerprint, always."""
    if cfg is not None and not isinstance(cfg, dict):
        raise SceneCfgError("SCENE_CFG_NOT_AN_OBJECT", "scene cfg must be a dict or None, got %s" % type(cfg).__name__)
    try:
        blob = json.dumps(cfg or {}, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise SceneCfgError("SCENE_CFG_NOT_SERIALIZABLE", "scene cfg is not JSON-serialisable: %s" % e)
    return hashlib.sha256(blob).hexdigest()


def record(con, cfg):
    """Store the cfg body under its fingerprint and return it. None -> '' (nothing pinned)."""
    if cfg is None:
        return ""
    fp = fingerprint(cfg)
    from .ledger import _now                             # local: ledger imports nothing from here
    con.execute("INSERT OR IGNORE INTO scene_cfgs (fingerprint, recorded_at, body) VALUES (?, ?, ?)",
                (fp, _now(), json.dumps(cfg, sort_keys=True, ensure_ascii=False)))
    return fp


def _pinned(con, run_id, scene_no):
    row = con.execute("SELECT cfg_fingerprint FROM scenes WHERE run_id = ? AND scene_no = ?",
                      (run_id, int(scene_no))).fetchone()
    return None if row is None else row["cfg_fingerprint"]


def for_scene(con, run_id, scene_no):
    """The cfg a scene ran against -> dict, or None.

    None means UNKNOWN, not empty: a scene recorded before pinning existed has no body to return,
    and saying so is the honest answer. Same contract as `bible.for_run`.
    """
    fp = _pinned(con, run_id, scene_no)
    if not fp:
        return None
    body = con.execute("SELECT body FROM scene_cfgs WHERE fingerprint = ?", (fp,)).fetchone()
    return json.loads(body["body"]) if body else None


def drifted(con, run_id, scene_no, cfg):
    """Has the authored cfg changed since this scene ran? -> (bool, detail).

    DETECTION ONLY, deliberately — see the module docstring. The caller decides policy; the resume
    path in `scripts/scene.py` prints and continues.
    """
    fp = _pinned(con, run_id, scene_no)
    if fp is None:
        return False, "no such scene %s/%s — nothing to compare" % (run_id, scene_no)
    if not fp:
        return False, "scene predates cfg pinning — nothing to compare"
    current = fingerprint(cfg)
    if current == fp:
        return False, "cfg unchanged (%s)" % current[:12]
    return True, "cfg drifted: scene pinned %s, on disk %s" % (fp[:12], current[:12])
