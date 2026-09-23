#!/usr/bin/env python3
"""bond_replay.py — what the bond tier WOULD have done with a run's stored event tags. Measurement only.

NOT a `test_*.py`; `run_all.py` does not discover it. It writes nothing: no db, no sheet, no log.

WHY THIS EXISTS (2026-09-16). `relationship_deltas` has 0 rows on every live performance of the
first generated scene (v1 5 beats, v2 7, v5 6, v6 14) while the stub probe writes them. The
event seat puts severity WORDS in its `social` block, `bonds.act_from_tags` cannot float a word and
skips the axis, and because the block is non-empty the dimension route is never entered — so the
tier has been dormant on seat output since the seats went live, and nobody could see it because
nothing printed. Fable's review (cairn/projects/reviews/2026-09-16-simtoprose-seat-review-fable.md)
named it and named the measurement to make BEFORE wiring anything: replay the stored blocks through
the arithmetic and look at the trajectory, so the unipolar-word / bipolar-axis question is answered
by a picture and not a guess. The owner's instruction: build, do not wire — "right now we don't have
the metrics to guide the bonds numbers". This script is those metrics.

WHAT IT DOES. For each committed beat of a run: the speaker's stored tags (`turns.tags`, already
severity-normalised in `dimensions`; `social` still words) plus the beat's subject (`events.payload`)
are handed to `bonds.observations_from_social` under one MAPPING, then to `act_from_tags(observations=)`,
then — exactly as `floor.bond_moves` does — `witnessed` and `observe`/`reflect` for every OTHER
person present, from the AUTHORED edges in the book's character sheets. The edges are advanced in
memory beat by beat and printed both ways. Three mappings:

  act        the seat's `showed` + `object` under the 2026-09-17 contract, from a re-answer file
             (`tests/reanswer_event_seat.py --report` -> reanswered.json, passed as --answers);
             the arm the design is measured on
  severity   the stored replies' strength words taken AS observations (the control arm — shows
             what wiring the old `social` block as-is would have done)
  dims       the block ignored; every axis synthesised from the dimensions through `_DIMS_CONTROL`
             (the retired fallback route, kept here as the labelled control arm: the trajectory the
             design produced before the seat named the act)

THE LAW UNDER REPLAY is whatever `bonds.observe` is today — since gate 4 (2026-09-17) the signed,
level-anchored form of bond-arithmetic.md s6, with STAKE and RATES read off each witness's sheet
exactly as `floor.bond_moves` reads them, the second-order mirror on the speaker's own edge, and a
count of the beats that were a CLIFF for someone (the driver would write a rest row; this writes none).

Usage:
  python tests/bond_replay.py --db "<book>/runs/live-run.db" --mapping severity
  python tests/bond_replay.py --db "<book>/runs/live-run.db" --mapping act --answers <dir>/reanswered.json
  python tests/bond_replay.py --db "<book>/runs/live-run.db" --all --answers <...>   # side by side
The book folder is the db's grandparent (`<book>/runs/<x>.db`) unless `--book` says otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bonds                                       # noqa: E402
from src.engine import bond_rest                                   # noqa: E402  (whole: born at the stranger's rest)
from src.engine import attachments                                 # noqa: E402  (gate 5: holds per witness)
from src.engine.records import RELATIONSHIP_AXES, RecordError      # noqa: E402
from src.engine.vault import load_book                             # noqa: E402
from src.engine import severity as S                               # noqa: E402

# THE RETIRED FALLBACK, kept as the labelled control arm (it was `bonds._DIM_AXES` until gate 4;
# the law no longer derives an observation from a dimension — s6 OMITTED: nothing). Each row is
# (axis, sign, weight): observed = .5 + sign·.5·severity·weight; the most extreme read per axis wins.
_DIMS_CONTROL = {
    "social_violation": [("trust", -1.0, 1.0), ("respect", -1.0, 0.5)],
    "care_relevant":    [("affinity", +1.0, 1.0), ("trust", +1.0, 0.6)],
    "relief":           [("affinity", +1.0, 0.7), ("trust", +1.0, 0.3)],
    "mastery":          [("respect", +1.0, 1.0)],
}

AXES = [a for a in RELATIONSHIP_AXES]


def _rows(con, sql, args=()):
    con.row_factory = sqlite3.Row
    return con.execute(sql, args).fetchall()


def load_run(db, run_id=None, scene=None):
    """-> (run_id, [beat dicts], {char_id: {fixed, baseline}}). Read-only.

    scene=N (the scenes table's scene_no) narrows beats to that scene's [start_turn, end_turn]
    (src/engine/ledger.py Ledger.scenes_for / append_scene), before the caller derives ITS
    cast from whatever beats that leaves — the same reason reanswer_event_seat.py grew a
    --scene filter (a run holds several scenes, each with its own cfg). Refuses (SystemExit) a
    scene_no this run does not have, naming the ones it does."""
    con = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    runs = [r["run_id"] for r in _rows(con, "SELECT run_id FROM runs ORDER BY rowid")]
    if not runs:
        raise SystemExit("no runs in %s" % db)
    if run_id is None:
        run_id = runs[-1]
    if run_id not in runs:
        raise SystemExit("run %r not in %s; runs: %s" % (run_id, db, runs))
    turn_lo, turn_hi = None, None
    if scene is not None:
        scene_rows = _rows(con, "SELECT scene_no, start_turn, end_turn FROM scenes WHERE run_id = ? "
                                 "ORDER BY scene_no", (run_id,))
        by_no = {int(r["scene_no"]): (int(r["start_turn"]), int(r["end_turn"])) for r in scene_rows}
        if int(scene) not in by_no:
            raise SystemExit("scene %r not in run %r; scenes: %s" % (scene, run_id, sorted(by_no)))
        turn_lo, turn_hi = by_no[int(scene)]
    subj = {}
    for r in _rows(con, "SELECT turn, actor, payload FROM events WHERE run_id = ? ORDER BY turn, event_id", (run_id,)):
        p = json.loads(r["payload"] or "{}")
        subj.setdefault((int(r["turn"]), r["actor"]), p.get("subject") or p.get("target") or "")
    beats = []
    for r in _rows(con, "SELECT turn, actor, tags, action FROM turns WHERE run_id = ? ORDER BY turn", (run_id,)):
        turn = int(r["turn"])
        if turn_lo is not None and not (turn_lo <= turn <= turn_hi):
            continue
        tags = json.loads(r["tags"] or "{}")
        beats.append({"turn": turn, "actor": r["actor"], "tags": tags,
                      "subject": subj.get((turn, r["actor"]), ""), "action": r["action"] or ""})
    sheets = {r["char_id"]: {"fixed": json.loads(r["fixed"]), "baseline": json.loads(r["baseline"])}
              for r in _rows(con, "SELECT char_id, fixed, baseline FROM characters WHERE run_id = ?", (run_id,))}
    con.close()
    return run_id, beats, sheets


def authored_edges(book_dir, cast, with_holds=False):
    """{perceiver: {target: edge}} from the book's character sheets — the tier's starting point.
    with_holds=True -> (edges, holds) where holds = {cid: attachments.holds_of(current.attachments)}
    (gate 5: what each witness holds that is not a person, as floor.bond_moves reads it)."""
    _world, chars = load_book(book_dir)
    by_id = {}
    for key, ch in chars.items():
        cid = str((ch.get("fixed") or {}).get("id") or (ch.get("fixed") or {}).get("name") or key).lower()
        by_id[cid] = ch
    edges, holds = {}, {}
    for cid in cast:
        ch = by_id.get(cid)
        rels = ((ch or {}).get("current") or {}).get("relationships") or {}
        edges[cid] = {str(t).lower(): {a: float(e.get(a, bonds._NEUTRAL.get(a, 0.5))) for a in AXES if a in e or a in bonds._NEUTRAL}
                      for t, e in rels.items() if isinstance(e, dict)}
        holds[cid] = attachments.holds_of(((ch or {}).get("current") or {}).get("attachments"))
    return (edges, holds) if with_holds else edges


def shape(tags, mapping, answer):
    """The stored tags -> the tags the fold sees under one MAPPING. Pure.

    act       the re-answered tags (showed already priced by parse_event_reply; object named by the
              seat) — the seat's object becomes `target` when it names a cast member, so `received`
              and the second order read it (gate 3 does this in the driver).
    severity  the stored `social` strength words priced through the STRENGTH ladder and handed in as
              `showed` floats — the control arm; act_from_tags would refuse the words themselves.
    dims      neither block: `showed` synthesised from the dimensions through `_DIMS_CONTROL`, the
              route the fold itself took before gate 4.
    """
    t = {k: v for k, v in tags.items() if k not in ("social", "showed")}
    if mapping == "act":
        if not answer:
            return None
        t["type"] = answer.get("type", t.get("type"))
        t["dimensions"] = answer.get("dimensions", {})
        t["durability"] = answer.get("durability", "transient")
        t = S.normalise_dimensions(t)                  # the re-answer's dimensions are words
        if answer.get("showed"):
            # a reply cached before 2026-09-18 carries the retired `debt` verdict inside `showed`; its act
            # words replay, the verdict is dead (bonds.observations_from_showed refuses it as an axis)
            t["showed"] = {a: v for a, v in answer["showed"].items() if a != "debt"}
        if answer.get("object"):
            t["object"] = answer["object"]
            t["target"] = str(answer["object"]).lower()
        t["transfers"] = list(answer.get("transfers") or [])   # the facts the account moves on (2026-09-18)
        return t
    if mapping == "severity":
        social = tags.get("social") or {}
        if social:
            t["showed"] = {a: S.value_of(w) for a, w in social.items() if a in S.ACT_AXES and isinstance(w, str)}
        return t
    obs = {}
    for dim, rows in _DIMS_CONTROL.items():
        try:
            sev = min(1.0, max(0.0, float((tags.get("dimensions") or {}).get(dim, 0.0))))
        except (TypeError, ValueError):
            continue
        if sev <= 0.0:
            continue
        for axis, sign, weight in rows:
            o = 0.5 + sign * 0.5 * sev * weight
            if axis not in obs or abs(o - 0.5) > abs(obs[axis] - 0.5):
                obs[axis] = min(1.0, max(0.0, o))
    if obs:
        t["showed"] = obs
    return t


def replay(beats, sheets, edges, mapping, cast, answers=None, holds=None, no_held=False):
    """-> (per-beat report rows, final edges, counts). Pure over its inputs; edges are copied.
    `holds` = {witness: {entity: hold}} (gate 5) is passed to act_from_tags / stake_of and the second
    order reads the same stake; `no_held=True` passes None everywhere (the pre-gate-5 arm, for an A/B)."""
    edges = {p: {t: dict(e) for t, e in d.items()} for p, d in edges.items()}
    rows, counts = [], {"beats": 0, "no_act": 0, "refused": 0, "unwitnessed": 0, "moved": 0, "cliffs": 0, "postings": 0}
    for b in beats:
        counts["beats"] += 1
        speaker = b["actor"]
        tags = dict(b["tags"], target=b["subject"]) if b["subject"] else dict(b["tags"])
        try:
            tags = shape(tags, mapping, answers.get(str(b["turn"])) if answers else None)
        except RecordError as e:
            counts["refused"] += 1
            rows.append((b["turn"], speaker, "REFUSED %s" % e.code, {}))
            continue
        if tags is None:
            counts["refused"] += 1
            rows.append((b["turn"], speaker, "NO RE-ANSWER for this beat", {}))
            continue
        line = {}
        for wid in [c for c in cast if c != speaker]:
            held = None if no_held else (holds or {}).get(wid) or {}
            act = bonds.act_from_tags(tags, speaker, wid, held=held)
            if not act:
                counts["no_act"] += 1
                line[wid] = "no act"
                continue
            stored = edges.setdefault(wid, {}).get(speaker, {})
            skills = (sheets.get(wid) or {}).get("baseline", {}).get("skills", {})
            if not bonds.witnessed(act, skills, stored):              # recognition on the STORED edge, as floor.bond_moves
                counts["unwitnessed"] += 1
                line[wid] = "not witnessed (sev %.2f)" % act["severity"]
                continue
            model = (sheets.get(wid) or {}).get("baseline", {}).get("model", {})
            # exactly floor.bond_moves: stake and rates off the WITNESS's sheet (s5/s6, gate 4); the
            # law reads the edge WHOLE — born at the stranger's rest when the sheet never authored it
            priors = (sheets.get(wid) or {}).get("baseline", {}).get("relationship_priors", {})
            edge = bond_rest.whole(stored, priors)
            stake = bonds.stake_of(wid, act["object"], edges[wid], held=held)
            rates = bonds.rates_of(priors)
            deltas = bonds.observe(edge, act, model, stake=stake, rates=rates)
            view = bonds.reflect(edge, act, model, rates=rates, stake=stake)
            cliffs = bonds.cliff_axes(edge, act, model) if deltas else ()
            if deltas:
                counts["moved"] += 1
                edges[wid][speaker] = bonds.apply_deltas(edge, deltas)
            if view:
                edges[wid][speaker] = bonds.apply_reflection(edges[wid].get(speaker, edge), view)
            counts["cliffs"] += len(cliffs)
            line[wid] = {"sev": round(act["severity"], 2), "dom": act["dominant"], "obj": tags.get("object"),
                         "stake": round(stake, 2), "cliff": list(cliffs),
                         "held": bool(str(tags.get("object") or "").startswith((attachments.LOC, attachments.GRP))),
                         "obs": {a: round(v, 2) for a, v in act["observations"].items() if v is not None},
                         "d": {a: round(v, 4) for a, v in deltas.items()}}
        # THE ACCOUNT MOVES ON A TRANSFER (2026-09-18): the seat's facts, priced once per pair, as the drivers do
        _accounts = {c: {t: float((e or {}).get("debt", 0.0) or 0.0) for t, e in edges.get(c, {}).items() if isinstance(e, dict)} for c in cast}
        for _p, _t, _entry, _d, _cause in bonds.debt_postings(tags, speaker, _accounts, present=list(cast)):
            _prels = edges.setdefault(_p, {})
            _prels[_t] = bonds.apply_deltas(bond_rest.whole(_prels.get(_t), (sheets.get(_p) or {}).get("baseline", {}).get("relationship_priors", {})), {"debt": _d})
            counts["postings"] += 1
            line.setdefault("postings", []).append("%s %s %s %+0.4f (%s)" % (_p, _entry, _t, _d, _cause[:40]))
        rows.append((b["turn"], speaker, tags.get("type", "?"), line))
    return rows, edges, counts


def fmt_edge(e):
    parts = []
    for a in AXES:
        v = float(e.get(a, bonds._NEUTRAL.get(a, 0.5)))
        word = (" %s" % S.standing_of(a, v)) if a in S.STANDING_WORDS else ""
        parts.append("%s=%.3f%s" % (a[:3], v, word))
    return "  ".join(parts)


def report(mapping, rows, start, final, counts, cast):
    print("\n=== mapping: %s ===" % mapping)
    print("  beats %(beats)d  no-act %(no_act)d  refused %(refused)d  unwitnessed %(unwitnessed)d  moved %(moved)d  cliffs %(cliffs)d  postings %(postings)d" % counts)
    for turn, speaker, etype, line in rows:
        if isinstance(line, dict) and line:
            for wid, what in line.items():
                if isinstance(what, dict):
                    print("  t%02d %-6s %-8s -> %-6s sev %.2f %-14s obj %-6s stake %.2f obs %s  d %s%s" % (
                        turn, speaker, etype, wid, what["sev"], what["dom"], what.get("obj") or "-", what["stake"],
                        what["obs"], what["d"] or "-", ("  CLIFF %s" % what["cliff"]) if what.get("cliff") else ""))
                else:
                    print("  t%02d %-6s %-8s -> %-6s %s" % (turn, speaker, etype, wid, what))
        else:
            print("  t%02d %-6s %s" % (turn, speaker, etype))
    print("  --- edges, authored -> after the run")
    for p in cast:
        for t in cast:
            if p == t:
                continue
            s = start.get(p, {}).get(t, {}); f = final.get(p, {}).get(t, {})
            print("  %s->%s  %s   =>   %s" % (p, t, fmt_edge(s) if s else "(no authored edge)", fmt_edge(f) if f else "(none)"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--run", default=None)
    ap.add_argument("--book", default=None, help="book folder (default: the db's grandparent)")
    ap.add_argument("--mapping", default="severity", choices=("act", "severity", "dims"))
    ap.add_argument("--answers", default=None, help="reanswered.json from tests/reanswer_event_seat.py --report (for --mapping act)")
    ap.add_argument("--all", action="store_true", help="run all three mappings")
    ap.add_argument("--no-held", action="store_true", help="pass no held map (the pre-gate-5 arm) — the A/B against the default")
    ap.add_argument("--scene", type=int, default=None,
                     help="scene_no (scenes table) to narrow to — cast and turns sliced to its "
                          "[start_turn, end_turn] (default: the whole run)")
    a = ap.parse_args(argv)
    db = os.path.abspath(a.db)
    book = a.book or os.path.dirname(os.path.dirname(db))
    run_id, beats, sheets = load_run(db, a.run, scene=a.scene)
    cast = sorted({b["actor"] for b in beats})
    start, holds = authored_edges(book, cast, with_holds=True)
    for p in cast:
        if holds.get(p):
            print("  holds    %s  %s" % (p, "  ".join("%s %.2f" % (k, v) for k, v in sorted(holds[p].items()))))
    print("run %s  beats %d  cast %s  book %s" % (run_id, len(beats), cast, book))
    for p in cast:
        for t in cast:
            if p != t:
                print("  authored %s->%s  %s" % (p, t, fmt_edge(start[p][t]) if start.get(p, {}).get(t) else "(none)"))
    answers = json.load(open(a.answers, encoding="utf-8")) if a.answers else None
    for mapping in (("act", "severity", "dims") if a.all else (a.mapping,)):
        if mapping == "act" and not answers:
            print("\n=== mapping: act === (skipped: no --answers)")
            continue
        rows, final, counts = replay(beats, sheets, start, mapping, cast, answers=answers, holds=holds, no_held=a.no_held)
        report(mapping, rows, start, final, counts, cast)
    return 0


if __name__ == "__main__":
    sys.exit(main())
