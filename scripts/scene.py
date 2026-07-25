#!/usr/bin/env python3
"""scene.py — the multi-agent scene runner (the director sets the scene; the agents push it).

The chair (direct.py) runs ONE actor against a typed circumstance. This runs a SCENE: the director
sets the situation, the present cast, and each actor's DRIVE — a genuine standing want, blind to how
the scene ends (design.md scene-goals discipline). Then the agents converse with no scripted lines.

v2 (multi-character.md urge model): each beat, the floor passes to the actor with the highest URGE to
speak — urge = salience + addressed_bonus + disruption_stake − recency_penalty − inhibition — not pure
salience. The disruption_stake (the heat of the exchange × the listener's order/standing values) is what
surfaces the decorum-keeper who isn't moved by the topic but won't abide an argument at their table; the
recency penalty breaks a two-person monopoly. An actor may set `exit` to walk out (the scene ends on
cast<2 or the next lull). Each perceived event carries the recent transcript (rolling context), so the
actors see what they have already said and stop repeating themselves.

Reuses the single-actor engine functions (assemble / llm_turn / appraise / decay / resolve_subject)
and now commits each beat to the same ledger the chair uses, so a scene PERSISTS and a later scene
resumes the cast it evolved (gate swe-scene-ledger-persistence). v1 limits still open: no softmax
temperature (recency is the anti-monopoly term); the `_note` stable-prefix leak is inherited (a
separate fix); dialogue_acts/stance_snapshots writers are a follow-on gate.
"""
import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.vault import load_book                              # noqa: E402
from src.engine.scene import assemble, resolve_subject, subject_groups  # noqa: E402
from src.engine import acquisition                                  # noqa: E402  (witness-propagation + name-transmission)
from src.engine.state import build_profile, appraise, decay         # noqa: E402
from src.engine.direction import direct_affect                      # noqa: E402
from src.engine.records import PRIMARIES, Event, TurnCommit         # noqa: E402
from src.engine.consolidation import validate_tags, CATALOG         # noqa: E402  (validate the actor's same-pass self-report)
from src.engine.ledger import Ledger                               # noqa: E402  (the chronicle the scene now persists to)
from src.engine import arc                                         # noqa: E402  (durable baseline evolution across scenes)
from direct import faithful_turn, DEFAULT_MODEL, _ollama            # noqa: E402  (reuse the harness dispatch + active faithfulness guard; _ollama for the pre-warm)

# urge weights — Class-B director-set starts (calibrate against runs)
_FLOOR_THRESHOLD = 0.06   # below this max urge, no one is moved enough to answer -> the scene lulls
_ADDRESSED_BONUS = 0.15   # being spoken to / about pulls you to reply
_RECENCY_PENALTY = 0.20   # you just spoke -> step back (decays over ~3 beats); breaks two-person monopoly
_INHIBITION      = 0.10   # timid (low-extraversion) actors hold back

# ---- BP1.3 scene config: situation + present acting cast + each actor's DRIVE (genuine, blind to outcome) ----
BP13 = {
    "situation": (
        "It is evening at the Wintercrest family dinner table. Present: Orven the father at the head, "
        "Selven the mother, their son Brakk, and their young daughter Wynn. Earlier today in the garden, "
        "the Fenmark house-worker Kestra threw herself under Wynn's bolting palfrey and shielded the child "
        "with her own body; Kestra's arm was shattered and her face cut. She was left lying in the mud where "
        "she fell — and it is now evening, and she is still out there."),
    "subject": ("kestra", "fenmark"),
    "opening_tags": {"type": "loss", "dimensions": {"care_relevant": 0.5, "loss": 0.3, "social_violation": 0.4},
                     "durability": "transient"},
    "cast": [
        {"id": "brakk",    "drive": "know that the worker who shielded Wynn is being looked after"},
        {"id": "orven", "drive": "keep the evening in order and handle the day's losses efficiently"},
        {"id": "selven",    "drive": "a dignified dinner, Wynn composed, the family's standing intact"},
    ],
}

_NAMES = {"brakk": "Brakk", "orven": "Orven", "selven": "Selven"}


def load_scene_cfg(path):
    """Load a director-authored scene cfg from JSON — the director's interface for a book's scenes
    (the hardcoded BP13 above is just the default fixture). Required: situation (non-empty str) and
    cast (non-empty list of {id, drive}). Optional: name, subject ([id, group] -> tuple), opening_tags.
    Fail loud on a malformed cfg — a scene with no situation or no cast is not runnable."""
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if not isinstance(cfg, dict):
        raise ValueError("scene cfg must be a JSON object")
    if not isinstance(cfg.get("situation"), str) or not cfg["situation"].strip():
        raise ValueError("scene cfg needs a non-empty 'situation'")
    cast = cfg.get("cast")
    if not isinstance(cast, list) or not cast or not all(
            isinstance(c, dict) and c.get("id") and c.get("drive") for c in cast):
        raise ValueError("scene cfg needs a non-empty 'cast' of {id, drive} objects")
    subj = cfg.get("subject")
    cfg["subject"] = tuple(subj) if isinstance(subj, list) and len(subj) == 2 else (None, None)
    cfg.setdefault("opening_tags", {"type": "mundane", "dimensions": {}, "durability": "transient"})
    cfg.setdefault("name", os.path.splitext(os.path.basename(path))[0])
    return cfg


def _compose_event(situation, log, n=4):
    """What the next actor perceives: the standing situation + the recent transcript (rolling context,
    so they can see what they have already said and not repeat it)."""
    if not log:
        return situation + " The table has just been served; the evening is beginning."
    lines = "\n".join("%s: \"%s\"" % (_NAMES.get(b["who"], b["who"]), str(b["action"]).replace("\n", " ")[:300])
                      for b in log[-n:])
    return "%s\n\nThe exchange at the table so far (most recent last):\n%s" % (situation, lines)


def _salience(tags, target, tgroup, listener):
    applied = dict(tags)
    if target:
        applied["target"] = target
    if tgroup:
        applied["target_group"] = tgroup
    appraised = appraise(listener["affect"], applied, listener["profile"])
    return sum(abs(appraised[p] - listener["affect"][p]) for p in PRIMARIES)


def _order_weight(profile):
    """The listener's stake in ORDER/standing — the mean of the standing-cluster values. High for a
    decorum-keeper: a heated exchange at the table is, to them, a violation worth intervening on."""
    s = profile.get("model", {}).get("schwartz", {})
    return sum(float(s.get(k, 0.5)) for k in ("conformity", "security", "power")) / 3.0


def _urge(tags, target, tgroup, listener, addressed, beats_since):
    """How urgently this listener wants the floor. Returns (urge, salience, disruption) for display."""
    sal = _salience(tags, target, tgroup, listener)
    addr = _ADDRESSED_BONUS if addressed else 0.0
    disruption = float((tags.get("dimensions") or {}).get("social_violation", 0.0)) * _order_weight(listener["profile"])
    recency = _RECENCY_PENALTY * max(0.0, 1.0 - beats_since / 3.0)
    inhibition = _INHIBITION * (1.0 - listener["extraversion"])
    return sal + addr + disruption - recency - inhibition, sal, disruption


def run_scene(world, chars, cfg, led, run_id, start_turn, model, stub, budget, think=True):
    """Run the scene, committing each beat to the ledger. Returns the next free turn number
    (start_turn + beats committed). The cast is built from `chars` (already loaded + rehydrated by
    the caller on resume); `led`/`run_id` are the open chronicle. Each beat is a turn-commit keyed
    (run_id, turn, actor) — one actor per beat — so a later scene resumes the cast this one evolved."""
    gi = subject_groups(world)
    actors = {}
    for c in cfg["cast"]:
        ch = chars[c["id"]]
        ch["current"]["active_goals"] = [{"goal": c["drive"], "urgency": 0.8}]   # the scene DRIVE overrides sheet goals
        actors[c["id"]] = {
            "id": c["id"], "char": ch, "profile": build_profile(ch), "affect": dict(ch["current"]["affect"]),
            "temperament": ch["baseline"]["temperament"], "drive": c["drive"], "last_spoke": -99,
            "extraversion": float(ch["baseline"].get("traits", {}).get("extraversion", {}).get("mean", 0.5))}
    ids = [c["id"] for c in cfg["cast"]]
    present = list(ids)

    print("=== SCENE: %s — emergent; urge floor, no scripted lines (run %s, from turn %d) ===\n" % (
        cfg.get("name", "scene"), run_id, start_turn))
    for i in ids:
        print("  drive[%-9s] %s" % (i, actors[i]["drive"]))

    osubj, ogrp = cfg["subject"]
    open_sal = {i: _salience(cfg["opening_tags"], osubj, ogrp, actors[i]) for i in ids}
    speaker = max(open_sal, key=open_sal.get)
    print("\n  opener by salience: %s  (%s)\n" % (
        _NAMES.get(speaker, speaker), "  ".join("%s=%.3f" % (k, v) for k, v in open_sal.items())))

    log, ended = [], "budget"
    turn_no = start_turn
    for beat in range(budget):
        a = actors[speaker]
        event_text = _compose_event(cfg["situation"], log)
        scene_slice = {"event": {"text": event_text, "kind": "mundane"},
                       "recent": [l["action"] for l in log[-2:]],
                       "location": a["char"]["current"].get("location")}
        packet = assemble(a["char"], world, scene_slice, a["affect"], a["char"]["current"]["condition"])
        # name hygiene rides in build_turn_messages — mask every name this speaker never acquired;
        # faithful_turn REGENERATES on any latent name-leak the mask couldn't stop, before we commit.
        turn, leaks = faithful_turn(packet, event_text, a["temperament"], model, stub, think=think, seed=beat,
                                    relationships=a["char"]["current"].get("relationships", {}))
        if leaks:                                       # a name-leak survived retries -> skip this beat; never commit a leak
            led.record_turn_skipped(run_id, turn_no, speaker, "faithfulness: %s" % ", ".join(n for n, k in leaks))
            print("-- beat %d (turn %d) -- %s [faithfulness reject: %s — skipped]" % (
                beat + 1, turn_no, _NAMES.get(speaker, speaker), ", ".join(n for n, k in leaks)))
            others = [i for i in present if i != speaker]
            if not others:
                ended = "empty"
                break
            speaker = others[0]
            continue
        if not str(turn.get("action", "")).strip():     # empty draw survived faithful_turn's resamples ->
            led.record_turn_skipped(run_id, turn_no, speaker, "empty turn (no action after retries)")
            print("-- beat %d (turn %d) -- %s [empty draw — skipped, not committed]" % (
                beat + 1, turn_no, _NAMES.get(speaker, speaker)))
            others = [i for i in present if i != speaker]
            if not others:
                ended = "empty"
                break
            speaker = others[0]
            continue
        tags = turn["tags"] if isinstance(turn.get("tags"), dict) else {"dimensions": {}}
        target, tgroup = resolve_subject(packet["volatile"]["edges"], gi, tags.get("subject"))
        addressee = turn.get("addressee", "")          # WHO was spoken to (distinct from the subject)

        # validate the actor's same-pass self-report, mirror the chair: schema-invalid never moves state
        validation = validate_tags(tags, packet["volatile"]["percepts"], a["char"]["baseline"]["skills"])
        if not validation["ok"]:
            applied = {"dimensions": {}}
        elif validation["flags"]:
            legit = CATALOG.get(tags.get("type", ""), {}).get("appraisal_map", [])
            applied = dict(tags, dimensions={d: v for d, v in tags.get("dimensions", {}).items() if d in legit})
        else:
            applied = tags
        if target:
            applied = dict(applied, target=target)
            if tgroup:
                applied["target_group"] = tgroup
        appraised = appraise(a["affect"], applied, a["profile"])         # raw impact (pre-decay)
        impact = sum(abs(appraised[p] - a["affect"][p]) for p in PRIMARIES)
        a["affect"] = decay(appraised, a["temperament"], a["profile"])
        a["last_spoke"] = beat
        log.append({"who": speaker, "action": turn["action"], "thought": turn["thought"], "tags": tags})

        # ---- persist the beat: the scene now writes to the same chronicle the chair does ----
        led.append_turn(TurnCommit(
            run_id=run_id, turn=turn_no, actor=speaker,
            thought=str(turn["thought"]), action=str(turn["action"]),
            tags=tags if isinstance(tags, dict) else {}, affect=dict(a["affect"]),
            condition=dict(a["char"]["current"].get("condition", {})), validation=validation,
            events=[Event(type=str(tags.get("type", "mundane")),
                          payload={"text": event_text, "dimensions": tags.get("dimensions", {}),
                                   "durability": tags.get("durability", "transient"),
                                   "subject": target, "subject_group": tgroup},
                          actor=speaker)],
            manifest=packet["manifest"], recall=packet["recall_refs"]))
        # arc: a durable beat moves the speaker's baseline; persist + evolve them for the next beat
        diff = arc.assess(applied, impact, a["char"], a["char"]["current"]["condition"])
        if diff:
            a["char"] = arc.apply(a["char"], diff)
            led.append_arc_diff(run_id, speaker, turn_no, diff)
            a["profile"] = build_profile(a["char"])
            a["temperament"] = a["char"]["baseline"]["temperament"]
        # acquisition: a durable, subject-bearing beat becomes the speaker's lived belief
        acquired = acquisition.assess(applied, tags, a["char"])
        if acquired:
            a["char"]["current"].setdefault("vault", []).append(acquired)
            led.append_acquisition(run_id, speaker, turn_no, acquired)

        print("-- beat %d (turn %d) -- %s" % (beat + 1, turn_no, _NAMES.get(speaker, speaker)))
        print("   ACTION : %s" % str(turn["action"]).replace("\n", " ")[:500])
        print("   THOUGHT: %s" % str(turn["thought"]).replace("\n", " ")[:300])
        print("   TAGS   : %s %s  subj=%s" % (tags.get("type", "?"), tags.get("dimensions", {}), target or "-"))
        print("   now    : %s" % direct_affect(a["affect"], a["temperament"]))
        # (faithfulness is enforced pre-commit by faithful_turn above — committed beats are leak-free)

        # witness-propagation: present bystanders remember + PERSIST the durable act they watched
        # (knowledge-model.md transmission: B's vault gains what B saw) — now folded to the ledger too,
        # so a witnessed belief survives the scene and resumes with the bystander.
        wb = acquisition.witness_belief(_NAMES.get(speaker, speaker), tags, speaker)
        if wb:
            for wid in present:
                if wid == speaker:
                    continue
                wvault = actors[wid]["char"]["current"].setdefault("vault", [])
                if not any(isinstance(x, dict) and x.get("claim") == wb["claim"] for x in wvault):
                    wvault.append(dict(wb))
                    led.append_acquisition(run_id, wid, turn_no, dict(wb))

        # name-transmission (auto name-reveal): a bystander who hears a name spoken aloud — one they
        # knew only by a descriptor — learns it now, forward (reveal_name is monotonic: old
        # descriptor-memories stay; the name is added going forward). Rides on the same present-set.
        for wid in present:
            if wid == speaker:
                continue
            wchar = actors[wid]["char"]
            for eid, nm in acquisition.overheard_names(str(turn.get("action", "")),
                                                       wchar["current"].get("relationships", {}),
                                                       world.get("people", [])):
                belief = acquisition.reveal_name(wchar, eid, nm)
                if belief:
                    led.append_acquisition(run_id, wid, turn_no, belief)
                    print("   >> %s overhears the name %r (learned)" % (wid, nm))

        turn_no += 1                                    # this beat is committed; the next beat is a new turn

        if turn.get("exit"):
            present = [i for i in present if i != speaker]
            print("\n   >> %s pushes back from the table and leaves the scene. <<" % _NAMES.get(speaker, speaker))
            if len(present) < 2:
                ended = "exit"
                break

        others = [i for i in present if i != speaker]
        if not others:
            ended = "empty"
            break
        urges = {}
        for o in others:
            addressed = bool(addressee) and str(addressee).startswith(o)
            urges[o] = _urge(applied, target, tgroup, actors[o], addressed, beat - actors[o]["last_spoke"])
        nxt = max(urges, key=lambda k: urges[k][0])
        if urges[nxt][0] < _FLOOR_THRESHOLD:
            print("\n== lull — no one is moved enough to answer (max urge %.3f). The scene settles. ==" % urges[nxt][0])
            ended = "lull"
            break
        print("   urges  : %s  -> floor: %s\n" % (
            "  ".join("%s=%.2f[sal%.2f dis%.2f]" % (k, v[0], v[1], v[2]) for k, v in urges.items()),
            _NAMES.get(nxt, nxt)))
        speaker = nxt

    print("\n== scene ended: %s — %d beats ==" % (ended, len(log)))
    return turn_no


def main():
    ap = argparse.ArgumentParser(description="the multi-agent scene runner — set the scene, the agents push it; the chronicle persists")
    ap.add_argument("--vault", required=True, help="the BOOK folder (vault)")
    ap.add_argument("--stub", action="store_true", help="deterministic stand-in, no API")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--budget", type=int, default=14, help="max beats")
    ap.add_argument("--db", default=None, help="chronicle db path (default <vault>/runs/<book>.db)")
    ap.add_argument("--resume", default=None, help="run_id to continue — a later scene in the same chronicle")
    ap.add_argument("--scene", default=None, help="a director-authored scene cfg JSON (default: the built-in BP13 fixture)")
    ap.add_argument("--no-think", action="store_false", dest="think",
                    help="disable model thinking (Ollama) for fast iteration; thinking is ON by default")
    args = ap.parse_args()

    # pre-warm: cold-load the model NOW, before load_book pulls the engine's recall models into host RAM.
    # On this RAM-constrained host the 17 GB model's cold load (UseMmap:false) OOMs if it lands mid-scene
    # with scene.py resident (ggml mem_buffer NULL -> HTTP 500; server.log 2026-06-14). Warming first puts
    # the cold load where host RAM is free; every beat then hits a warm model. Fail loud — a down daemon
    # should stop us here, not on beat 1. Stub runs and non-ollama models skip.
    if not args.stub and args.model.startswith("ollama/"):
        _ollama([{"role": "user", "content": "ok"}], args.model[len("ollama/"):], max_tokens=4, think=False)
        print("pre-warmed %s\n" % args.model)

    world, chars = load_book(args.vault)
    book_name = os.path.basename(os.path.normpath(args.vault)).lower().replace(" ", "-")
    default_db = os.path.join(args.vault, "runs", "%s.db" % book_name)   # the chronicle lives WITH the book
    led = Ledger(args.db or default_db)
    cfg = load_scene_cfg(args.scene) if args.scene else BP13             # director-authored scene, or the default fixture
    cast_ids = [c["id"] for c in cfg["cast"]]

    if args.resume:
        run_id = args.resume
        led.set_status(run_id, "active")
        state = led.resume(run_id)
        for cid in cast_ids:                                       # rehydrate each cast member the prior scene evolved
            ch = chars[cid]
            for diff in led.arc_diffs_for(run_id, cid):
                ch = arc.apply(ch, diff)
            acq = led.acquisitions_for(run_id, cid)
            if acq:
                ch["current"].setdefault("vault", []).extend(acq)
            latest = led.latest_affect(run_id, cid)
            if latest:
                ch["current"]["affect"] = latest["affect"]
            chars[cid] = ch
        start_turn = state["turn"] + 1
        print("resumed %s at turn %d (determinism OK)\n" % (run_id, state["turn"]))
    else:
        run_id = "scene-%s-%d" % (book_name, int(time.time()))
        led.create_run(run_id, {"catalog_version": 1,
                                "models": {"turn": "stub" if args.stub else args.model},
                                "prompt_versions": {"turn": 1}})
        for cid in cast_ids:
            led.register_character(run_id, cid, chars[cid]["fixed"], chars[cid]["baseline"])
        start_turn = 0
        print("new chronicle: %s\n" % run_id)

    next_turn = run_scene(world, chars, cfg, led, run_id, start_turn, args.model, args.stub, args.budget, think=args.think)
    last = max(next_turn - 1, 0)
    if next_turn > start_turn:                          # at least one beat committed -> record the scene boundary
        scene_no = led.next_scene_no(run_id)
        pov = cfg.get("pov") or (cast_ids[0] if cast_ids else None)
        led.append_scene(run_id, scene_no, cfg.get("name", "scene"), pov, start_turn, last)
        print("recorded scene %d: %r (turns %d-%d, pov=%s)" % (scene_no, cfg.get("name", "scene"), start_turn, last, pov))
    led.persist_snapshot(run_id, last, led.fold(run_id, last))
    led.set_status(run_id, "parked")
    print("\nparked %s at turn %d — continue with: python scripts/scene.py --vault \"%s\"%s --resume %s" % (
        run_id, last, args.vault, " --stub" if args.stub else "", run_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
