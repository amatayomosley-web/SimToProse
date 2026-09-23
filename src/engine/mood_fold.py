"""mood_fold.py — the mood tier, re-derived from the log.

WHY THIS EXISTS (gate mood-from-readings, 2026-09-22). Hard rule 2 says the log is the truth and every
snapshot a derivable cache. For the mood that was false: each beat's mood lived only in `current_state`,
a mutable cache, and a resume restored it from there (`Ledger.latest_affect`); nothing re-derived it from
what the log holds. docs/emotion-arithmetic.md section 5 step 8 logged the READINGS precisely so the mood
would be re-derivable ("without it f and R are not re-derivable and hard rule 2 is false for emotion"),
and no code ever did the derivation. `replay` does it, and `divergence` measures it against the cache.

WHAT IT REPLAYS: a scene-driven run, scene by scene from the `scenes` rows, as scripts/scene.py ran it.
  resume   each cast member from the sheet the run PINNED (`bible.for_run`), the log folded up to the
           scene's first turn - the arc, the bonds and holds (with the resume's own seed rows), the
           aboutness binds, the wounds - and the mood the replay itself last produced (never the cache).
  profile  built at the scene's start, BEFORE the opening fades anything, and rebuilt after that
           character's own wound refold or arc change: exactly when the drivers build it. Decay and the
           receipt read the profile's held map from that build and its relationships live (a profile
           keeps a reference to the sheet's edges), so each beat reads the bonds as they stood.
  opening  `passage.apply_opening`, the very code `open_scene` runs, over the gap the clock logged.
  beat     decay first over the beat's minutes, then the receipt from the logged readings (or, with no
           readings, `appraise` on the logged tags); every other present character decays when the
           manifest records it (step 4, since gate non-speaker-decay); the binds follow rules 1-5.
Each step calls the engine function the driver called; nothing is re-implemented here.

WHAT IT DOES NOT DO. It does not read or write the cache except to compare (`divergence`), and it does
not replace the resume's restore: the owner ruled (2026-09-22, "Keep the mood") that a resume keeps the
saved mood - a resume is not a story event - and this replay is the per-resume check on it. It stops at
the first turn outside every scene row (a chair turn) and says so. It carries no numbers of its own.

Deterministic, stdlib + engine imports only, no LLM, no randomness.
"""
from __future__ import annotations

__layer__ = "engine"

import copy as _copy
import json as _json

from . import arc
from . import body as _body
from . import bond_rest
from . import clock
from . import concepts as _concepts
from . import condition as _condition
from . import injuries as _injuries
from . import passage
from . import readings as _readings
from . import systems as _systems
from . import targets as _targets
from .consolidation import CATALOG
from .records import PATHS, Reading
from .state import appraise, build_profile, decay, receive

TOLERANCE = 1e-9          # what `divergence` reports as agreement: float noise, never a feeling


def _bonds(con, run_id, cid, ch, before, seeded_at=None):
    """(edges, holds) as they stood: the authored ones folded through the timeline up to `before`."""
    rels = _copy.deepcopy(ch["current"]["_authored_relationships"])
    holds = _copy.deepcopy(ch["current"].get("_authored_attachments") or {})
    items = [it for _t, _k, it in bond_rest.timeline_rows(con, run_id, cid, before=before, seeded_at=seeded_at)]
    bond_rest.rehydrate(rels, (ch.get("baseline") or {}).get("relationship_priors", {}), items, attachments=holds)
    return rels, holds


def _resumed(con, run_id, cid, sheet, start, mood, enabled=None, condition=None):
    """One cast member as the resume at `start` rebuilt them (scripts/scene.py main) -> the char. `mood` and
    `condition` are the ones the replay itself carried out of the last scene (None: the sheet's)."""
    ch = _copy.deepcopy(sheet)
    passage.stamp_authored(ch)
    ch = passage.fold_arc(con, run_id, cid, ch, before_turn=start)
    ch["current"]["relationships"], ch["current"]["attachments"] = _bonds(con, run_id, cid, ch, (start, 2), seeded_at=start)
    ch["current"].setdefault("targets", {})
    _targets.replay(ch, _targets.binds_for(con, run_id, cid, before_turn=start))
    passage.fold_wounds(con, run_id, cid, ch, before_turn=start)
    if mood is not None:
        ch["current"]["affect"] = dict(mood)
    if condition is not None:
        ch["current"]["condition"] = dict(condition)
    ch = _systems.strip(ch, enabled if enabled is not None else _systems.defaults())     # the driver's own point
    if enabled is not None and "body" in enabled:                   # the reserves, where the drivers split them
        ch["current"]["condition"] = _condition.split(ch["current"]["condition"])
    return ch


def _systems_at(con, run_id, start):
    """The systems a scene ran: its first beat's manifest records them when the book declared any
    (gate systems-registry); a book that declared none ran the defaults."""
    row = con.execute("SELECT manifest FROM decision_manifests WHERE run_id = ? AND turn = ?", (run_id, start)).fetchone()
    listed = (_json.loads(row[0]) if row else {}).get("systems")
    return frozenset(listed) if isinstance(listed, list) else _systems.defaults()


def _applied(tags, validation, target, tgroup):
    """The tags `appraise` read: flagged dimensions dropped to the type's legitimate ones, the subject on."""
    if (validation or {}).get("flags"):
        legit = CATALOG.get(tags.get("type", ""), {}).get("appraisal_map", [])
        tags = dict(tags, dimensions={d: v for d, v in (tags.get("dimensions") or {}).items() if d in legit})
    if target:
        tags = dict(tags, target=target)
        if tgroup:
            tags["target_group"] = tgroup
    return tags


def replay(con, run_id, sheets, notes=None, conditions=None):
    """-> {(turn, char_id): mood} for every beat of every scene, the speaker's and each decayed bystander's.

    `sheets` {id: character sheet} - the run's pinned bible characters. `notes`, a list, collects what
    the replay met and could not mirror (a chair turn, a bind the log disagrees with). `conditions`, a dict,
    collects {(turn, char_id): condition} beside the moods - moved by `condition.spend` / `condition.opening`
    when the scene ran `condition_flow`, set by the scene cfg's pinned `condition` list (gate condition-flow)."""
    notes = notes if notes is not None else []
    outc = conditions if conditions is not None else {}
    out, mood, cond, chs, prof, temp, binds = {}, {}, {}, {}, {}, {}, {}
    scenes = con.execute("SELECT start_turn, end_turn, cfg_fingerprint FROM scenes WHERE run_id = ? "
                         "ORDER BY start_turn", (run_id,)).fetchall()
    covered = {t for s in scenes for t in range(int(s[0]), int(s[1]) + 1)}
    stray = [int(r[0]) for r in con.execute("SELECT turn FROM turns WHERE run_id = ?", (run_id,)) if int(r[0]) not in covered]
    for s_start, s_end, fp in scenes:
        start, end = int(s_start), int(s_end)
        if any(t < start for t in stray):
            notes.append("stopped at turn %d: turn %d sits outside every scene (a chair turn)" % (start, min(stray)))
            break
        body = _json.loads(con.execute("SELECT body FROM scene_cfgs WHERE fingerprint = ?", (fp,)).fetchone()[0])
        cast = [c["id"] for c in body["cast"]]
        at_m, lasts, per_beat = con.execute("SELECT at_minutes, lasts_minutes, beat_minutes FROM scene_clock "
                                            "WHERE run_id = ? AND turn = ?", (run_id, start)).fetchone()
        enabled = _systems_at(con, run_id, start)
        flow, body_on, inj_on = "condition_flow" in enabled, "body" in enabled, "injuries" in enabled
        for c in cast:
            chs[c] = _resumed(con, run_id, c, sheets[c], start, mood.get(c), enabled, cond.get(c))
            prof[c], temp[c] = build_profile(chs[c]), chs[c]["baseline"]["temperament"]
            binds[c] = dict(chs[c]["current"].get("targets") or {})
        rests = {c: [r for r in bond_rest.rows_for(con, run_id, c) if r[0] < start or (r[0] == start and r[4] == "authored")]
                 for c in cast}
        passage.apply_opening({c: chs[c] for c in cast}, clock.gap_before(con, run_id, float(at_m), before_turn=start),
                              clock.unspent_before(con, run_id, start) or 0.0, rests.get, flow=flow, body=body_on,
                              at=float(at_m), stated=_condition.stated_gaps(body.get("condition")),
                              gaps={c: clock.presence_end(con, run_id, c, start) for c in cast} if flow else None,
                              weakened=({c: _injuries.weakening(con, run_id, c, chs[c], start) for c in cast}
                                        if (inj_on and body_on) else None))
        _condition.apply_declared({c: chs[c] for c in cast}, body.get("condition"))     # the director's words, as run
        for c in cast:
            mood[c] = dict(chs[c]["current"]["affect"])
            cond[c] = dict(chs[c]["current"].get("condition") or {})
        for t in range(start, end + 1):
            _beat(con, run_id, t, cast, float(per_beat or 0.0), mood, chs, prof, temp, binds, out, notes,
                  cond=cond, outc=outc, flow=flow, body=body_on, injuries=inj_on)
    return out


def _beat(con, run_id, t, cast, per_beat, mood, chs, prof, temp, binds, out, notes, cond=None, outc=None, flow=False,
          body=False, injuries=False):
    """One committed beat, as scripts/scene.py run_scene computed its moods - and, beside them, the
    conditions it committed: moved by the beat's minutes and the speaker's impact when `flow`."""
    cond, outc = (cond if cond is not None else {}), (outc if outc is not None else {})
    cap = ((lambda c: _body.capacity(chs[c], _injuries.weakening(con, run_id, c, chs[c], t) if injuries else 0))
           if body else (lambda c: 1.0))                             # gates body-exertion, injury-weakens
    row = con.execute("SELECT actor, tags, validation FROM turns WHERE run_id = ? AND turn = ?", (run_id, t)).fetchone()
    if row is None:
        return
    spk, tags, val = row[0], _json.loads(row[1] or "{}"), _json.loads(row[2] or "{}")
    man = con.execute("SELECT manifest FROM decision_manifests WHERE run_id = ? AND turn = ?", (run_id, t)).fetchone()
    step4 = (_json.loads(man[0]) if man else {}).get("decay") or {}
    ev = con.execute("SELECT target, payload FROM events WHERE run_id = ? AND turn = ? ORDER BY event_id DESC LIMIT 1",
                     (run_id, t)).fetchone()                         # the beat's own event is appended last
    target = ev[0] if ev else None
    applied = _applied(tags, val, target, (_json.loads(ev[1]).get("subject_group") if ev else None))
    rs = [Reading(path=r[2], rung=r[3], about=r[4] or "", confidence=r[5])
          for r in _readings.readings_for(con, run_id, spk) if int(r[0]) == t]
    room = set(step4.get("here") or ()) or (set(cast) | ({str(target)} if _concepts.looks_like_concept(target) else set()))
    before = dict(binds[spk])
    mid = _targets.bind_readings(before, rs, me=spk) if rs else _targets.retarget(before, applied, me=spk)
    for c in cast:                                                   # the profile reads the edges live
        prof[c]["relationships"] = _bonds(con, run_id, c, chs[c], (t, 3))[0]
    rested = decay(mood[spk], temp[spk], prof[spk], elapsed=per_beat, targets=before, present=room)
    for b in (step4.get("bystanders") or ()):                        # step 4, where the beat recorded it
        mood[b] = decay(mood[b], temp[b], prof[b], elapsed=per_beat, targets=dict(binds[b]), present=room)
        out[(t, b)] = dict(mood[b])
        if flow:                                                     # a bystander's beat costs its minutes
            cond[b] = _condition.spend(cond[b], per_beat, 0.0, mood[b], 1.0 / cap(b))
        outc[(t, b)] = dict(cond.get(b) or {})
    reps = {ab: _targets.repeat_count(con, run_id, spk, ab, before_turn=t) for ab in {str(v) for v in mid.values() if v}}
    if rs:
        mood[spk], impact = receive(rested, rs, prof[spk], targets=mid, repeats=reps, present=room)
    else:
        mood[spk] = appraise(rested, applied, prof[spk], targets=mid, repeats=reps, present=room)
        impact = sum(abs(mood[spk][p] - rested[p]) for p in PATHS)
    if flow:                                                         # the speaker's beat costs minutes AND impact
        cond[spk] = _condition.spend(cond[spk], per_beat, impact, mood[spk], 1.0 / cap(spk))
        if body:                                                     # the act, from the reader's logged word
            cond[spk] = _body.exert(cond[spk], tags.get("exertion"), per_beat, cap(spk))
    outc[(t, spk)] = dict(cond.get(spk) or {})
    binds[spk] = _targets.bind_readings(mid, [], temperament=temp[spk], affect=mood[spk])    # rule 5 last
    logged = dict(_targets.replay({"current": {"targets": {}}}, _targets.binds_for(con, run_id, spk, before_turn=t + 1)))
    if {k: v for k, v in binds[spk].items() if v} != {k: v for k, v in logged.items() if v}:
        notes.append("turn %d %s: the replayed binds %r differ from the log's %r" % (t, spk, binds[spk], logged))
    out[(t, spk)] = dict(mood[spk])
    moved = con.execute("SELECT 1 FROM wound_deltas WHERE run_id = ? AND char_id = ? AND turn = ? UNION ALL "
                        "SELECT 1 FROM wound_minted WHERE run_id = ? AND char_id = ? AND turn = ?",
                        (run_id, spk, t, run_id, spk, t)).fetchone()
    if moved:                                                        # after the commit, as the driver
        passage.fold_wounds(con, run_id, spk, chs[spk], before_turn=t + 1)
        prof[spk] = build_profile(chs[spk])
    diff = con.execute("SELECT diff FROM arc_diffs WHERE run_id = ? AND char_id = ? AND turn = ?", (run_id, spk, t)).fetchone()
    if diff:
        chs[spk] = arc.apply(chs[spk], _json.loads(diff[0]))
        prof[spk], temp[spk] = build_profile(chs[spk]), chs[spk]["baseline"]["temperament"]


def divergence(con, run_id, sheets):
    """The replay against the cache -> {"rows", "cached", "largest", "at", "missing", "notes"}.

    `largest` is the biggest |replay - cache| on any path of any row both hold; `at` names it as
    (turn, char, path), None when every row agrees exactly; `missing` lists cached rows the replay did
    not rebuild. Reported, never repaired: the cache is not rewritten."""
    notes, gotc = [], {}
    got = replay(con, run_id, sheets, notes, conditions=gotc)
    cached = {(int(r[0]), r[1]): _json.loads(r[2]) for r in con.execute(
        "SELECT turn, char_id, affect FROM current_state WHERE run_id = ?", (run_id,))}
    largest, at = 0.0, None
    for key in sorted(set(got) & set(cached)):
        for p, v in cached[key].items():
            d = abs(float(got[key].get(p, 0.0)) - float(v))
            if d > largest:
                largest, at = d, (key[0], key[1], p)
    c_largest, c_at = 0.0, None                                      # the condition column (gate condition-flow)
    for (turn, cid), cached_c in _cached_conditions(con, run_id).items():
        mine = gotc.get((turn, cid))
        if mine is None:
            continue
        for k in sorted(set(cached_c) | set(mine)):
            a, b = cached_c.get(k), mine.get(k)
            d = (abs(float(a) - float(b)) if isinstance(a, (int, float)) and isinstance(b, (int, float))
                 and not isinstance(a, bool) else (0.0 if a == b else 1.0))
            if d > c_largest:
                c_largest, c_at = d, (turn, cid, k)
    return {"rows": len(got), "cached": len(cached), "largest": largest, "at": at,
            "missing": sorted(set(cached) - set(got)), "notes": notes,
            "condition_largest": c_largest, "condition_at": c_at}


def _cached_conditions(con, run_id):
    return {(int(r[0]), r[1]): _json.loads(r[2] or "{}") for r in con.execute(
        "SELECT turn, char_id, condition FROM current_state WHERE run_id = ?", (run_id,))}
