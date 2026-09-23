#!/usr/bin/env python3
"""reanswer_event_seat.py — rebuild a run's EVENT-seat prompts under the CURRENT contract, for an
out-of-process re-answer, then parse the answers and report what the seat did with the contract.

NOT a `test_*.py`; `run_all.py` does not discover it. It writes prompt files and a report; it never
touches the run's db or its cached seats.

WHY THIS EXISTS (2026-09-17, bond gate 1 of 6, `docs/bond-arithmetic.md` s9). The event seat's
contract changed — `object` + `showed` on the act ladders replaced the `social` block of strength
words — and a changed contract cannot be measured on cached replies: the prompt key changes and
the old replies are refused at parse (APPRAISER_SOCIAL_RETIRED). The measurement the gate needs is
the SAME beats re-read under the NEW contract: per-axis firing rate (the old skeleton had all three
axes filled on 22 of 22 cached replies; the target is <= 1.5 named axes per beat), the object-naming
rate, and the refusal rate. Those numbers decide whether the contract works before the law is
written on top of it.

HOW. The user turn of every event prompt is rebuilt from the run's log exactly as `scene.py` builds
it live (situation from `scene_cfgs`, the rolling transcript via `prompt.compose_event`, the cast's
display names), and the system turn is the contract as it stands now. `--emit` writes them through
`provider.emit` (same files, same keys) into a directory of your choosing; something out of process
answers them as `<key>.reply.txt` (an agent per prompt, no key on this machine); `--report` parses
every answer with `appraiser.parse_event_reply` under the object lists the prompt showed, prints the
rates, and writes `<dir>/reanswered.json` — {turn: tags} — which `tests/bond_replay.py --answers`
replays through the bond arithmetic.

PER SCENE (2026-09-18, the quote-check gate). A run holds several scenes; each has its own cfg (the
`scenes` row's `cfg_fingerprint` -> the `scene_cfgs` body) and its own transcript — `scene.run_scene`
starts `log = []` per invocation, so scene 2's first prompt carries THE MOMENT and no prior exchange.
The first draft of this script kept the LAST cfg for every turn and rolled one log across the run,
which on the two-scene live run would have rebuilt S1's prompts under S2's situation and S2's
first prompt with S1's last beats in it. Now: per scene, its cfg, its cast as `present`, the log
reset at `start_turn`. `--verify <dir>[,<dir>]` asserts every rebuilt USER turn is byte-identical
to the stored prompt for that turn (the system turn is the part that changes with the contract);
`--emit` refuses on a mismatch, so nothing is ever re-answered against a prompt the run never asked.

Usage:
  python tests/reanswer_event_seat.py --db "<book>/runs/live-run.db" --verify "<book>/runs/seats-s1,<book>/runs/seats-s2"
  python tests/reanswer_event_seat.py --db "<book>/runs/live-run.db" --out <dir> --emit --verify <dirs> [--scene N]
  python tests/reanswer_event_seat.py --db "<book>/runs/live-run.db" --out <dir> --report
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import appraiser as A                                              # noqa: E402
import provider as P                                               # noqa: E402
from src.engine.prompt import compose_event                        # noqa: E402
from src.engine.records import RecordError                         # noqa: E402
from src.engine import severity as S                               # noqa: E402


def load(db, run_id=None):
    """-> (run_id, names, scenes) where scenes = [{scene_no, label, start_turn, end_turn, cfg, turns}],
    each scene with ITS cfg (by the scenes row's fingerprint) and ITS turns only. Read-only."""
    con = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    con.row_factory = sqlite3.Row
    runs = [r["run_id"] for r in con.execute("SELECT run_id FROM runs ORDER BY rowid")]
    run_id = run_id or runs[-1]
    names = {}
    for r in con.execute("SELECT char_id, fixed FROM characters WHERE run_id = ?", (run_id,)):
        f = json.loads(r["fixed"]); names[r["char_id"]] = f.get("name") or r["char_id"]
    bodies = {r["fingerprint"]: r["body"] for r in con.execute("SELECT fingerprint, body FROM scene_cfgs")}
    scenes = []
    for sc in con.execute("SELECT scene_no, label, cfg_fingerprint, start_turn, end_turn FROM scenes WHERE run_id = ? ORDER BY scene_no", (run_id,)):
        body = bodies.get(sc["cfg_fingerprint"])
        if not body:
            raise SystemExit("scene %d (%s) pins cfg %s, which scene_cfgs does not hold" % (sc["scene_no"], sc["label"], sc["cfg_fingerprint"][:12]))
        cfg = json.loads(body)
        if not cfg.get("situation"):
            raise SystemExit("scene %d's cfg carries no situation" % sc["scene_no"])
        turns = [dict(r) for r in con.execute(
            "SELECT turn, actor, action FROM turns WHERE run_id = ? AND turn BETWEEN ? AND ? ORDER BY turn",
            (run_id, sc["start_turn"], sc["end_turn"]))]
        scenes.append({"scene_no": sc["scene_no"], "label": sc["label"], "start_turn": sc["start_turn"],
                       "end_turn": sc["end_turn"], "cfg": cfg, "turns": turns})
    con.close()
    if not scenes:
        raise SystemExit("run %s has no scenes rows in %s" % (run_id, db))
    return run_id, names, scenes


def build(scene, names, attachments=None):
    """-> [(turn, actor_id, messages, objects, action)] — the prompt per beat of ONE scene as scene.py
    builds it live: its cfg's situation, its cast as present, the log reset at start_turn.
    `attachments` (gate 5): the world's attachable names shown on THE ATTACHMENTS line; the parser
    admits them as objects the way scene.py does."""
    out, log = [], []
    cfg = scene["cfg"]
    cast = [c["id"] if isinstance(c, dict) else str(c) for c in (cfg.get("cast") or [])] or list(names)
    for t in scene["turns"]:
        moment = compose_event(cfg["situation"], log, names)
        present = list(cast)                                       # ids, as scene.py passes them live
        msgs = A.build_event_messages(t["action"], moment=moment, present=present,
                                      actor=names.get(t["actor"], t["actor"]), referenced=None, attachments=attachments)
        out.append((t["turn"], t["actor"], msgs, list(present) + list(attachments or []), t["action"]))
        log.append({"who": t["actor"], "action": t["action"]})
    return out


_ATTACH_LINE = "THE ATTACHMENTS the act may be about"


def _sans_attachments(text):
    """The user turn with THE ATTACHMENTS line removed — the one line a gate-5 re-answer changes."""
    return "\n".join(l for l in str(text).split("\n") if not l.startswith(_ATTACH_LINE))


def verify(prompts, stored_dirs, modulo_attachments=False):
    """Every rebuilt USER turn against the stored `appraise-event` prompt for the same turn under any of
    `stored_dirs` -> (matched, mismatched, unmatched). The system turn is excluded on purpose: it is
    the contract, the one thing a re-answer changes. `modulo_attachments` compares with THE
    ATTACHMENTS line removed from both sides (gate 5: the list is what that re-answer changes)."""
    stored = {}
    for d in stored_dirs:
        for fn in os.listdir(d):
            if not fn.endswith(".prompt.json"):
                continue
            row = json.load(io.open(os.path.join(d, fn), encoding="utf-8"))
            if row.get("purpose") != "appraise-event":
                continue
            turn = (row.get("meta") or {}).get("turn")
            if turn is not None:
                stored[int(turn)] = [m for m in row["messages"] if m.get("role") == "user"]
    matched, mismatched, unmatched = [], [], []
    for turn, _actor, msgs, _objects, _action in prompts:
        mine = [m["content"] for m in msgs if m.get("role") == "user"]
        theirs = [m["content"] for m in stored.get(turn, [])]
        if modulo_attachments:
            mine, theirs = [_sans_attachments(x) for x in mine], [_sans_attachments(x) for x in theirs]
        if not theirs:
            unmatched.append(turn)
        elif mine == theirs:
            matched.append(turn)
        else:
            mismatched.append(turn)
    return matched, mismatched, unmatched


def emit(prompts, out_dir, model):
    os.makedirs(out_dir, exist_ok=True)
    index = []
    for turn, actor, msgs, objects, action in prompts:
        key = P.emit(msgs, model, "appraise-event", out_dir, meta={"turn": turn, "actor": actor, "objects": objects})
        index.append({"turn": turn, "actor": actor, "key": key, "objects": objects, "action": action})
    io.open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8").write(json.dumps(index, indent=1))
    print("emitted %d prompt(s) to %s (index.json beside them); answer each as <key>.reply.txt" % (len(index), out_dir))


def report(out_dir):
    index = json.load(io.open(os.path.join(out_dir, "index.json"), encoding="utf-8"))
    parsed, refused, missing = {}, [], []
    axes = {a: 0 for a in S.ACT_AXES}; debt = 0; told_costly = 0; objects_named = 0; empty_dims = 0; showed_beats = 0; held_obj = []
    for row in index:
        p = os.path.join(out_dir, "%s.reply.txt" % row["key"])
        if not os.path.isfile(p):
            missing.append(row["turn"]); continue
        raw = io.open(p, encoding="utf-8").read()
        try:
            tags = A.parse_event_reply(raw, objects=row["objects"], action=row.get("action"))
        except RecordError as e:
            refused.append((row["turn"], e.code, str(e)[:100])); continue
        parsed[row["turn"]] = dict(tags, actor=row["actor"])
        sh = tags.get("showed") or {}
        if sh:
            showed_beats += 1
        for a in S.ACT_AXES:
            if a in sh:
                axes[a] += 1
        if tags.get("transfers"):
            debt += 1                                              # beats with at least one transfer row
        if str(tags.get("object") or "").startswith(("loc.", "grp.")):
            held_obj.append((row["turn"], tags.get("object"), bool(tags.get("transfers"))))   # gate 5: a held thing as the object
        if any(r.get("cost") != "none" for r in (tags.get("told") or [])):
            told_costly += 1                                       # beats with a told row at a cost (derives the trust rung)
        if tags.get("object"):
            objects_named += 1
        if not tags.get("dimensions"):
            empty_dims += 1
    n = len(index)
    print("beats %d  parsed %d  refused %d  missing %d" % (n, len(parsed), len(refused), len(missing)))
    for t, code, msg in refused:
        print("   t%02d REFUSED %s: %s" % (t, code, msg))
    if parsed:
        named = sum(axes.values()) + debt
        print("named axes per beat: %.2f  (target <= 1.5)   beats with any read: %d/%d" % (named / len(parsed), showed_beats, len(parsed)))
        print("per axis: " + "  ".join("%s %d" % (a, c) for a, c in axes.items()) + "  beats with transfers %d  rows %d" % (debt, sum(len(v.get("transfers") or []) for v in parsed.values()))
              + "  told rows %d  beats told at a cost %d" % (sum(len(v.get("told") or []) for v in parsed.values()), told_costly))
        print("object named on %d/%d beats; empty dimensions on %d" % (objects_named, len(parsed), empty_dims))
        for t in sorted(parsed):
            tg = parsed[t]
            print("   t%02d %-6s %-8s %-9s obj=%-8s showed=%s%s" % (t, tg["actor"], tg["type"], tg["durability"], tg.get("object") or "-",
                  {k: (v if isinstance(v, str) else round(v, 2)) for k, v in (tg.get("showed") or {}).items()} or "-",
                  ("  transfers=" + "; ".join("%s %s->%s [%s]" % (r["what"][:28], r["from"], r["to"], r["terms"]) for r in tg["transfers"])) if tg.get("transfers") else ""),
                  end="")
            print(("  told=" + "; ".join("%s ->%s [%s]" % (r["what"][:28], r["to"], r["cost"]) for r in tg["told"])) if tg.get("told") else "")
    if held_obj:
        print("held-thing objects on %d beat(s): %s  (with a transfer row: %d)" % (
            len(held_obj), " ".join("t%02d=%s" % (t, o) for t, o, _tr in held_obj), sum(1 for _t, _o, tr in held_obj if tr)))
    else:
        print("held-thing objects on 0 beats")
    io.open(os.path.join(out_dir, "reanswered.json"), "w", encoding="utf-8").write(json.dumps({str(t): v for t, v in parsed.items()}, indent=1))
    print("wrote %s" % os.path.join(out_dir, "reanswered.json"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--run", default=None)
    ap.add_argument("--out", default=None, help="directory for the prompt files and answers")
    ap.add_argument("--model", default="anthropic/claude-opus-5", help="recorded on the prompt file; the answering agent chooses its own")
    ap.add_argument("--scene", type=int, default=None, help="one scene_no only (default: every scene of the run)")
    ap.add_argument("--verify", default=None, help="comma-separated dirs of the run's stored prompts; every rebuilt user turn must match byte for byte")
    ap.add_argument("--attachments", default=None, help="gate 5: `world` (the book's attachable names) or a comma list of loc./grp. names to show the seat; --verify then compares modulo THE ATTACHMENTS line")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", action="store_true")
    g.add_argument("--report", action="store_true")
    g.add_argument("--check", action="store_true", help="verify only; emit nothing")
    a = ap.parse_args(argv)
    if a.report:
        if not a.out:
            raise SystemExit("--report needs --out")
        report(os.path.abspath(a.out))
        return 0
    run_id, names, scenes = load(os.path.abspath(a.db), a.run)
    attach = None
    if a.attachments:
        if a.attachments.strip().lower() == "world":
            from src.engine.vault import load_book
            from src.engine import attachments as _attachments
            book = os.path.dirname(os.path.dirname(os.path.abspath(a.db)))
            attach = _attachments.names_for(load_book(book)[0])
        else:
            attach = [x.strip() for x in a.attachments.split(",") if x.strip()]
        print("attachments shown to the seat: %s" % (", ".join(attach) or "none"))
    prompts = []
    for sc in scenes:
        if a.scene is not None and sc["scene_no"] != a.scene:
            continue
        built = build(sc, names, attachments=attach)
        print("scene %d %s: turns %d-%d, %d beats, cast %s" % (sc["scene_no"], sc["label"], sc["start_turn"], sc["end_turn"], len(built), [names.get(c, c) for c in names]))
        prompts += built
    if a.verify:
        dirs = [os.path.abspath(d.strip()) for d in a.verify.split(",") if d.strip()]
        matched, mismatched, unmatched = verify(prompts, dirs, modulo_attachments=attach is not None)
        print("verify: %d/%d user turns byte-identical to the stored prompts%s; mismatched %s; no stored prompt for %s"
              % (len(matched), len(prompts), " (modulo the attachments line)" if attach is not None else "", mismatched or "none", unmatched or "none"))
        if mismatched or unmatched:
            raise SystemExit("REFUSED: the rebuilt prompts are not the run's — fix the builder before answering anything")
    if a.check:
        return 0
    if not a.out:
        raise SystemExit("--emit needs --out")
    emit(prompts, os.path.abspath(a.out), a.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
