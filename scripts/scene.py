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
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.vault import load_book                              # noqa: E402
from src.engine.scene import assemble, resolve_subject, subject_groups, norm_id  # noqa: E402
from src.engine import acquisition                                  # noqa: E402  (witness-propagation + name-transmission)
from src.engine import integrity                              # noqa: E402
from src.engine.state import build_profile, appraise, decay         # noqa: E402
# NOT the `decay` above — that one is state.decay, the AFFECT relaxation. This is the
# belief-decay module. The names collide, so both are only ever reached under an alias
# here; importing it bare would silently rebind the affect function.
from src.engine import decay as _belief_decay                       # noqa: E402
from src.engine import clock as _clock                              # noqa: E402
from src.engine.targets import retarget                             # noqa: E402  (per-primitive aboutness)
from src.engine.direction import direct_affect                      # noqa: E402
from src.engine.records import (PRIMARIES, Event, TurnCommit, RelationshipDelta, WoundDelta,
                                TowardDelta)  # noqa: E402
from src.engine.consolidation import (validate_tags, CATALOG, TagError, tag_refusal,
                                       render_flag)         # noqa: E402  (validate the actor's same-pass self-report)
from src.engine.ledger import Ledger                               # noqa: E402  (the chronicle the scene now persists to)
from src.engine import arc                                         # noqa: E402  (durable baseline evolution across scenes)
from src.engine import bonds                                       # noqa: E402  (the relationship tier — per WITNESS, not per actor)
from src.engine import levers                                      # noqa: E402  (the wound refold on resume)
from src.engine import wound                                       # noqa: E402  (the wound tier's mover)
from src.engine import toward                                      # noqa: E402  (the MICRO tier)
from src.engine import connection                                  # noqa: E402  (the investment multiplier)
from src.engine import faithfulness                                # noqa: E402  (the name-leak wall a SUPPLIED turn must pass too)
from src.engine.severity import normalise_dimensions               # noqa: E402
from src.engine.prompt import build_turn_messages                  # noqa: E402  (the act seam's outbound half)
import direct                                                       # noqa: E402  (LAST_USAGE — token accounting)
from direct import faithful_turn, DEFAULT_MODEL, _ollama            # noqa: E402  (reuse the harness dispatch + active faithfulness guard; _ollama for the pre-warm)

# urge weights — Class-B director-set starts (calibrate against runs)
# ---- the floor economy: MOVED to src/engine/floor.py -----------------------------------------
# Five value-computing functions and these three constants lived here until 2026-09-03. CLAUDE.md's
# Modes section says a driver never computes a value, and `tests/run_all.py` discovers suites under
# tests/ — so nothing under tests/ could import them, and `tests/test_bonds.py` was loading this
# entire 1052-line CLI through `spec_from_file_location` to exercise a nine-line function.
#
# THE OLD PRIVATE NAMES ARE KEPT because nine tests load THIS FILE by path and one calls
# `sc._bond_moves`. Same move `ledger.py` makes for the fold: the seam is real, the call sites are
# untouched, and a test that reaches for a name still finds it.
from src.engine import floor as _floor
from src.engine.prompt import compose_event as _compose_event   # perception assembly, not floor
_salience        = _floor.salience
_bond_moves      = _floor.bond_moves
_order_weight    = _floor.order_weight
_urge            = _floor.urge
_ADDRESSED_BONUS = _floor.ADDRESSED_BONUS
_RECENCY_PENALTY = _floor.RECENCY_PENALTY
_INHIBITION      = _floor.INHIBITION
_FLOOR_THRESHOLD = _floor.FLOOR_THRESHOLD

# ---- BP1.3 scene config: situation + present acting cast + each actor's DRIVE (genuine, blind to outcome) ----
BP13 = {
    # INVENTED FIXTURE — no book. CLAUDE.md hard rule 1: real books never live in this repo, and that
    # includes their PLOT. This default was once a scene lifted from a private novel, which meant every
    # `scene.py` run without --scene played someone's book. What the fixture must exercise, and does:
    # a SUBJECT who is absent but salient (nobody can look at Pell), three drives that genuinely
    # collide rather than agree (a lull is the failure mode — scene-authoring-rules.md Rule 4), and a
    # care-versus-standing axis so the appraisal dimensions have something to separate on.
    "situation": (
        "It is full dark at the Holloway steading and the child Pell has not come back from the upland "
        "road. She was sent at midday to carry a message to the next farm, a walk of two hours there and "
        "two back. Present in the kitchen: Arden the father, Ilsa the mother, and Corin the hired man, "
        "who walked part of that road himself this afternoon and has said nothing about it."),
    "subject": ("pell", "holloway"),
    "opening_tags": {"type": "loss", "dimensions": {"care_relevant": 0.5, "loss": 0.3, "social_violation": 0.4},
                     "durability": "transient"},
    "cast": [
        {"id": "ilsa",  "drive": "get lanterns and bodies onto the upland road tonight, now, whoever it costs"},
        {"id": "arden", "drive": "not raise the valley over a girl who is probably sheltering somewhere dry"},
        {"id": "corin", "drive": "keep what he saw on that road to himself a little longer"},
    ],
}

def _display_names(world):
    """entity id -> the name a person in the room would use.

    Was a hardcoded 3-entry dict of the INVENTED FIXTURE's cast, so every real book fell through to
    the raw lowercase id — and not only in prints: `acquisition.witness_belief` is handed this
    name, so a witness recorded a database id where a person would have said a name.
    Resolved from the book's own `world.people` now, which is the same source `load_book` builds
    the cast from. Falls back to a title-cased id so a person with no note still reads as a name.
    """
    out = {}
    for p in (world or {}).get("people", []) or []:
        pid = (p or {}).get("id")
        if not pid:
            continue
        out[pid] = (p.get("name") or str(pid).replace("_", " ").title())
    return out


def law_preflight(led, cfg, world, chars, run_id=None, fp=None):
    """Does the world permit this circumstance at all? Refuses before anything is written.

    CALLED TWICE, and the placement is the point. `main` calls it on the NEW-RUN branch BEFORE
    `create_run`, so a scene the world refuses never mints a chronicle row; `run_scene` calls it on
    the resume path, where the pinned fingerprint genuinely does come from the run.

    THAT SPLIT WAS THE CORRECTION. I named the empty run a known wart and declined to fix it,
    asserting that the check could not move because it needs the pinned bible — true on RESUME,
    false on a new run, where `bible.build` hands back the fingerprint one line earlier. A blocker
    asserted for both branches that binds one. And the residue was not inert: `canon_digest`
    selects the newest row (`canon_digest.py:45`), so the digest's default landed on the EMPTY run
    and digested nothing while the real one sat a row back.

    `guide-content.md:146` — IMPOSSIBLE denies the circumstance; FORBIDS allows it and attaches
    teeth. The act is AUTHORED in the scene cfg and the check is skipped without one: measured on
    the active book, act=None makes all 27 laws bear and 24 of them deny, so a blanket call would
    refuse every scene. Inferring the act from prose is a classifier problem, not a call site.
    """
    from src.engine import bible
    act = cfg.get("act")
    if not act:
        return None
    if fp is None:
        # The hasattr guard here was ALWAYS FALSE — `run_config` existed nowhere on Ledger — so the
        # pinned-bible lookup never ran and this always rebuilt from the current notes, which is
        # exactly the mid-book drift hard rule 1 pins the bible to catch.
        fp = (led.run_config(run_id) or {}).get(bible.CONFIG_KEY) if run_id else None
        fp = fp or bible.build(led.con, world, chars)
    verdict = bible.verdict_for(led.con, fp, act=act, location=cfg.get("location"))
    try:
        bible.require_allowed(verdict, act)          # the ruling and the refusal are one thing
    except bible.BibleError as e:
        raise SystemExit("scene refused: %s" % e)
    if verdict["violations"]:
        print("  LAW: %r is FORBIDDEN but possible - it runs, and it costs." % act)
        for law_id, teeth in zip(verdict["violations"],
                                 verdict["teeth"] or [""] * len(verdict["violations"])):
            print("       %s -> %s" % (law_id, teeth))
    if verdict.get("undecidable"):
        print("  LAW: %r is contested-unknowable; the world declines to rule." % act)
    return verdict


def load_scene_cfg(path):
    """Load a director-authored scene cfg from JSON — the director's interface for a book's scenes
    (the hardcoded BP13 above is just the default fixture). Required: situation (non-empty str) and
    cast (non-empty list of {id, drive}). Optional: name, subject ([id, group] -> tuple),
    opening_tags, and `elapsed` — how much time the director says has passed since the last
    scene, in the director's own unit, which relaxes every cast edge toward its resting prior.
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
    # PROPS — scene-authoring-rules.md Rule 5. Optional on the cfg (every cfg written before
    # 2026-08-24 has none and must keep running byte-identically), but once declared they reach the
    # actor as percepts via gate.perception_scope. Normalised to a list of non-empty strings here so
    # the engine never has to defend against a stray dict.
    props = cfg.get("props")
    cfg["props"] = [str(x).strip() for x in props if str(x).strip()] if isinstance(props, list) else []
    cfg.setdefault("opening_tags", {"type": "mundane", "dimensions": {}, "durability": "transient"})
    # THE SAME SEAM AS THE ACTOR'S REPLY. `severity.normalise_dimensions` resolves a WORD to its
    # float here, at the parse boundary, so everything downstream — lint, `_salience`, `appraise` —
    # sees the floats it has always seen. Numbers still pass through untouched, so every cfg written
    # before the ladder existed runs byte-identically.
    #
    # This was a real docs-vs-engine break for a day: `template-scene-blueprint.md` was rewritten to
    # say "a WORD, not a number" while `lint_scene.py` rejected words and `appraise` raised on one.
    # The doc was right about the design and the engine had not been told — so the engine was told.
    cfg["opening_tags"] = normalise_dimensions(cfg["opening_tags"])
    cfg.setdefault("name", os.path.splitext(os.path.basename(path))[0])
    # PER-SCENE NARRATION (schema v13). The director already chooses `pov` per scene; voice and
    # knowledge are the same authority through the same column family, and they are what makes a
    # mixed-voice book possible — Bleak House alternates first and third, Gone Girl alternates two
    # first-person narrators. Defaults are what every scene was before the columns existed.
    #
    # Validated HERE rather than trusted: a migrated DB has no CHECK on `knowledge` (SQLite cannot
    # add one by ALTER), so the guard has to live where both the fresh and the migrated path pass.
    # THE VOCABULARY COMES FROM THE MODULE THAT DEFINES IT, and the check from the same place.
    # This read VOICES/KNOWLEDGE out of `narrate.py` — a sibling SCRIPT — and then re-implemented
    # `narration_modes.validate` beside them, so the engine module that owns both axes sat unused
    # with its two registered codes never raised. Two spellings of one contract, already drifting.
    from src.engine.narration_modes import VOICES, KNOWLEDGE, validate as _validate_modes
    from narrate import DEFAULT_VOICE, DEFAULT_KNOWLEDGE
    cfg["voice"] = str(cfg.get("voice") or DEFAULT_VOICE)
    cfg["knowledge"] = str(cfg.get("knowledge") or DEFAULT_KNOWLEDGE)
    try:
        _validate_modes(cfg["voice"], cfg["knowledge"])
    except Exception as e:                       # noqa: BLE001 — the CLI reports, never tracebacks
        raise SystemExit("scene cfg %r: %s" % (cfg.get("name"), e))
    return cfg


def _law_events(led, run_id, world, chars, turn, speaker, location=None, tick=None):
    """A reported act -> [Event] for every law it violates. NEVER retracts the turn.

    docs/guide-content.md's modality table: FORBIDS "allows, and attaches `teeth` as a consequence",
    and REQUIRES records the omission. The verdict_for function in src/engine/bible.py computed those
    teeth from the day it was written and nothing consumed them, so a breakable law cost nothing.

    This runs AFTER the beat and cannot deny: the turn already happened, and CLAUDE.md hard rule 2
    makes the log append-only -- a correction is a new event, never an edit. An IMPOSSIBLE act
    reported here is therefore RECORDED for the critic and the arc to see; refusing it is the
    pre-flight's job, before the beat.

    The teeth are recorded, not APPLIED. Turning a consequence into a lost rank or a wound is the
    director's judgment; a rule check that also punished would be the catalog-picks-the-action error
    one layer up (decision-engine.md).
    """
    act = str((turn or {}).get("act") or "").strip()
    if not act:
        return []
    from src.engine import bible
    # SCOPE, SUPPLIED. This called verdict_for with neither a location nor an actor, so even the
    # one scope the predicate honoured went unsupplied on every reported act — and four more
    # scopes were read by nothing at all until 2026-08-30. The acting character's class comes off
    # their own sheet; a character with no class simply fails to match a class-scoped law.
    _sheet = (chars.get(speaker) or {}).get("fixed") or {}
    _actor_class = ((_sheet.get("position") or {}).get("class") or None)
    try:
        # THE PIN, NOT THE CURRENT NOTES. This read `bible.build(led.con, world, chars)`, which
        # fingerprints whatever world is in memory — while `run_scene`'s pre-flight forty lines
        # below correctly reads the run's pinned bible first. On a RESUMED run whose notes were
        # edited between sessions the two disagree, so the same scene adjudicated its pre-flight
        # against the pin and its per-turn acts against the edited world. CLAUDE.md hard rule 1
        # pins the bible precisely so a mid-book edit cannot silently change what turns were
        # computed from; the drift check reports the divergence and, by that same rule, does not
        # abort. The `or build(...)` fallback keeps an unpinned run working.
        # (That check is named without its parentheses on purpose: tests/test_bible.py's
        # `test_both_resume_paths_actually_call_it` asserts the call is on the resume branch by
        # comparing STRING OFFSETS of the two literals, so a mere comment mentioning it earlier in
        # the file turns that test red. Recorded in this gate's OMISSIONS as a fragile proxy.)
        fp = (led.run_config(run_id) or {}).get(bible.CONFIG_KEY) or bible.build(led.con, world, chars)
        v = bible.verdict_for(led.con, fp, act=act, location=location,
                              actor_class=_actor_class, tick=tick)
    except bible.BibleError as exc:
        # NARROWED, AND NO LONGER SILENT. This was `except Exception: return []` with the comment
        # "a law check must never take a scene down with it" — which meant a malformed law, a
        # corrupt bible or an unenforceable scope all became "the world has no opinion", quietly.
        # A bare except around a safety gate is the same shape as the incident this whole effort
        # exists to end, one layer up. The check still does not abort the run (the beat already
        # happened and the log is append-only), but the failure is now NAMED and RECORDED.
        print("   [!] LAW CHECK FAILED for %r: %s" % (act, exc))
        return [Event(type="law-violation", actor=speaker,
                      payload={"act": act, "modality": "CHECK-FAILED",
                               "laws": [], "teeth": "",
                               "error_code": getattr(exc, "code", None) or "BIBLE_CHECK_FAILED",
                               "reason": str(exc),
                               "note": "the world could not be consulted; this is recorded, not silently dropped"})]
    out = []
    if not v["allowed"]:
        out.append(Event(type="law-violation", actor=speaker,
                         payload={"act": act, "modality": "IMPOSSIBLE",
                                  "laws": v["denied_by"], "reason": v.get("reason", ""),
                                  "note": "reported after the fact; the pre-flight is what refuses"}))
    for law, teeth in zip(v["violations"], (v["teeth"] or []) + [""] * len(v["violations"])):
        out.append(Event(type="law-violation", actor=speaker,
                         payload={"act": act, "modality": "FORBIDS-or-REQUIRES",
                                  "laws": [law], "teeth": teeth}))
    return out


def run_scene(world, chars, cfg, led, run_id, start_turn, model, stub, budget, think=True, seed_base=0,
              prompt_only=False, supplied=None):
    """Run the scene, committing each beat to the ledger. Returns the next free turn number
    (start_turn + beats committed). The cast is built from `chars` (already loaded + rehydrated by
    the caller on resume); `led`/`run_id` are the open chronicle. Each beat is a turn-commit keyed
    (run_id, turn, actor) — one actor per beat — so a later scene resumes the cast this one evolved.

    `prompt_only` emits the messages for the beat's speaker and returns without acting (the act
    seam's outbound half). `supplied` is a {action, thought, tags, exit?, addressee?} dict used
    INSTEAD of the local model for the first beat of this invocation — the inbound half. Between
    them any model anywhere can act a beat and the chronicle cannot tell which one did
    (docs/orchestration.md seam 1; scripts/direct.py:run_turn is the reference)."""
    names = _display_names(world)
    # ---- LAW PRE-FLIGHT: does the world permit this circumstance at all? -------------------
    # guide-content.md:146 - IMPOSSIBLE "denies the circumstance"; FORBIDS allows and attaches
    # teeth. src/engine/bible.py:411 implements it and had NO caller: the world refused nothing,
    # and critic.py checks only continuity and voice, so a breach was caught nowhere.
    #
    # The act is AUTHORED in the scene cfg and the check is skipped without one. That is not
    # laziness: measured on the active book, act=None makes all 27 laws bear and 24 of them deny,
    # so a blanket call would refuse every scene. Inferring the act from prose is a classifier
    # problem, not a call site.
    # ON RESUME the pinned fingerprint genuinely does come from the run, so the check stays here.
    # It re-parks on refusal: `main` flips a parked run to `active` before this point, and a scene
    # the world refuses must not leave the run looking live.
    try:
        law_preflight(led, cfg, world, chars, run_id=run_id)
    except SystemExit:
        led.set_status(run_id, "parked")
        raise

    # The act vocabulary the actor may report from, drawn from the world's own laws. Empty for
    # a lawless world, in which case nothing is injected and the prompt is unchanged.
    _law_acts = sorted({str(l.get("act")) for l in (world.get("laws") or []) if l.get("act")})

    gi = subject_groups(world)
    actors = {}
    for c in cfg["cast"]:
        ch = chars[c["id"]]
        ch["current"]["active_goals"] = [{"goal": c["drive"], "urgency": 0.8}]   # the scene DRIVE overrides sheet goals
        actors[c["id"]] = {
            "id": c["id"], "char": ch, "profile": build_profile(ch), "affect": dict(ch["current"]["affect"]),
            "temperament": ch["baseline"]["temperament"], "drive": c["drive"], "last_spoke": -99,
            "extraversion": float(ch["baseline"].get("traits", {}).get("extraversion", {}).get("mean", 0.5)),
            "targets": dict(ch["current"].get("targets") or {})}
    ids = [c["id"] for c in cfg["cast"]]
    present = list(ids)

    # DRIFT (relationships.md: "without reinforcement, relationships slowly decay toward a resting
    # state ... affinity fades faster than trust"). Applied at scene START, once, because a gap in
    # the story is between scenes — a beat has no duration, and drifting per beat would cool a
    # friendship over the course of one conversation. The unit of `elapsed` is the DIRECTOR'S: this
    # engine holds no world clock, so nothing here converts days into anything.
    elapsed = cfg.get("elapsed")
    if elapsed:
        # DECLARED, THEN APPLIED. The declaration is the CAUSE and it is what gets logged; drift
        # and wound erosion are both DERIVED from it at replay. Before this line, drift ran here,
        # mutated memory, and reached no table — so a resumed cast lost every winter that passed.
        led.declare_time(run_id, start_turn, elapsed, str(cfg.get("name", "") or ""))
        for i in ids:
            ch = actors[i]["char"]
            priors = ch["baseline"].get("relationship_priors", {})
            rels = ch["current"].get("relationships") or {}
            for tgt, edge in rels.items():
                if isinstance(edge, dict):
                    rels[tgt] = dict(edge, **bonds.drift(edge, priors, elapsed))
            # the SAME declared unit erodes an untouched wound — one clock, two tiers
            # (docs/character-model.md "DECAY AND CONNECTION": two clocks and no third).
            for _w in ((ch["baseline"].get("drives") or {}).get("fears_wounds") or []):
                if isinstance(_w, dict) and "intensity" in _w:
                    _e = wound.erode(_w, elapsed)
                    if _e:
                        _w.setdefault("_authored_intensity", float(_w["intensity"]))
                        _w["intensity"] = max(0.0, min(1.0, float(_w["intensity"]) + _e))
            # THE SAME DECLARED UNIT, three tiers. Edges drift toward their priors, wounds erode
            # toward their floor, temperament returns toward what the author wrote, and feelings
            # toward a person fade toward ZERO — slower for people this character is invested in,
            # because connection does its second job here (docs/character-model.md).
            arc.erode(ch, elapsed)
            _conns = {who: connection.for_target(rels, who)
                      for who in ((ch["current"].get("toward") or {}))}
            toward.erode(ch, elapsed, _conns)
        print("\n  elapsed %s since the last scene — edges relaxed toward each character's"
              " resting disposition" % elapsed)

    print("=== SCENE: %s — emergent; urge floor, no scripted lines (run %s, from turn %d) ===\n" % (
        cfg.get("name", "scene"), run_id, start_turn))
    for i in ids:
        print("  drive[%-9s] %s" % (i, actors[i]["drive"]))

    osubj, ogrp = cfg["subject"]
    open_sal = {i: _salience(cfg["opening_tags"], osubj, ogrp, actors[i]) for i in ids}
    speaker = max(open_sal, key=open_sal.get)
    print("\n  opener by salience: %s  (%s)\n" % (
        names.get(speaker, speaker), "  ".join("%s=%.3f" % (k, v) for k, v in open_sal.items())))

    # WHO THE MOMENT IS ABOUT, carried across beats. `levers._edge_matches` reads `ctx["target"]`
    # for a `target_edge` clause — one of the two edge-clause kinds decision-engine.md documents as
    # authorable — and NO caller ever set it, so such a row could never fire in any book. The value
    # already exists: `resolve_subject` computes it every beat and it was discarded when the slice
    # was rebuilt. Seeded from the director's own cfg subject so beat 1 is not blind.
    scene_target = cfg["subject"][0]
    log, ended = [], "budget"
    turn_no = start_turn
    for beat in range(budget):
        a = actors[speaker]
        event_text = _compose_event(cfg["situation"], log, names)
        scene_slice = {"event": {"text": event_text, "kind": "mundane"},
                       "target": scene_target,
                       "recent": [l["action"] for l in log[-2:]],
                       "props": cfg.get("props") or [],
                       # THE DIRECTOR STAGES THE SCENE. This read the acting character's own
                       # sheet, so a cfg staged at one place handed its cast the description
                       # of another — measured 2026-08-29: a scene declared at the fold
                       # delivered loc.mill to both actors while the prose described a
                       # hillside at dusk. The cfg value reached only the pre-flight law
                       # check, itself behind an `if _act:` guard most scenes never set.
                       # Falls back to the sheet, so a cfg with no location is unchanged.
                       "location": cfg.get("location") or a["char"]["current"].get("location")}
        # Same four decay arguments as direct.py's run_turn — see the comment there.
        # Without them every recall in a cast scene ran at turn 0 with no history.
        packet = assemble(a["char"], world, scene_slice, a["affect"],
                          a["char"]["current"]["condition"],
                          prev_affect=led.previous_affect(run_id, speaker, turn_no),
                          current_turn=turn_no,
                          relationships=a["char"]["current"].get("relationships", {}),
                          recall_history=_belief_decay.fold_recall_history(
                              led.con, run_id, speaker),
                          elapsed=_clock.elapsed_since(led.con, run_id, turn_no))
        # name hygiene rides in build_turn_messages — mask every name this speaker never acquired;
        # faithful_turn REGENERATES on any latent name-leak the mask couldn't stop, before we commit.
        # seed = seed_base*1000 + beat. It used to be the bare beat index, which made the seed a pure
        # function of the beat: two runs of one cfg drew the identical sequence and came back identical
        # (measured — runs …1787380588 / …1787385137 match on every turn; …1787381033 / …1787381616
        # share a 7-turn prefix). K "replicates" were K=1 repeated K times. Base 0 reproduces the old
        # sequence exactly, so every committed run stays comparable.
        rels = a["char"]["current"].get("relationships", {})
        # THE ACT SEAM (docs/orchestration.md seam 1). Outbound: emit exactly the messages the
        # engine would have sent, for the actor SALIENCE chose, and stop — the caller acts the beat
        # elsewhere and returns it via --turn-json. scene.py had neither half, which is the stated
        # reason character-simulator could not act in a multi-actor scene (direct.py:run_turn).
        if prompt_only:
            print(json.dumps(build_turn_messages(packet, event_text, a["temperament"], rels,
                                                 acts=_law_acts), indent=2))
            return turn_no
        if supplied is not None:
            # A SUPPLIED TURN PASSES THE SAME WALLS. Shape first, then the name-leak check, then the
            # identical validate/appraise/commit path below. A re-entry that skips the wall is a
            # hole in it, and the risk does not fall because the model was a stranger's.
            missing = [k for k in ("action", "thought", "tags") if k not in supplied]
            if missing:
                raise ValueError("supplied turn is missing %s — the contract is "
                                 "{action, thought, tags, exit?, addressee?}" % ", ".join(missing))
            turn = {"action": str(supplied.get("action", "")), "thought": str(supplied.get("thought", "")),
                    "exit": bool(supplied.get("exit", False)), "addressee": supplied.get("addressee", ""),
                    "act": str(supplied.get("act", "") or ""),
                    "tags": supplied.get("tags") if isinstance(supplied.get("tags"), dict) else {"dimensions": {}}}
            leaks = faithfulness.check_name_leaks("%s %s" % (turn["action"], turn["thought"]), rels)
            print("  [supplied turn accepted for validation — %d char action]" % len(turn["action"]))
            supplied = None          # one supplied beat per invocation; the rest act normally
        else:
            # `information` is the snapshot's fact -> knowers map. Passing it turns the
            # faithfulness guard from name-shaped to fact-shaped: an actor stating something
            # nobody told them is regenerated, the same as a name it does not hold.
            turn, leaks = faithful_turn(packet, event_text, a["temperament"], model, stub, think=think,
                                        seed=seed_base * 1000 + beat, acts=_law_acts,
                                        relationships=rels,
                                        information=(led.fold(run_id, max(turn_no - 1, 0)) or {}).get("information"),
                                        char_id=speaker)
        if leaks:                                       # a leak survived retries -> skip this beat; never commit one
            led.record_turn_skipped(run_id, turn_no, speaker, "faithfulness: %s" % ", ".join(n for n, k in leaks))
            print("-- beat %d (turn %d) -- %s [faithfulness reject: %s — skipped]" % (
                beat + 1, turn_no, names.get(speaker, speaker), ", ".join(n for n, k in leaks)))
            others = [i for i in present if i != speaker]
            if not others:
                ended = "empty"
                break
            speaker = others[0]
            continue
        if not str(turn.get("action", "")).strip():     # empty draw survived faithful_turn's resamples ->
            led.record_turn_skipped(run_id, turn_no, speaker, "empty turn (no action after retries)")
            print("-- beat %d (turn %d) -- %s [empty draw — skipped, not committed]" % (
                beat + 1, turn_no, names.get(speaker, speaker)))
            others = [i for i in present if i != speaker]
            if not others:
                ended = "empty"
                break
            speaker = others[0]
            continue
        # THE SEVERITY SEAM — twin of scripts/direct.py. Words -> floats on the existing
        # 0..1 scale, before validate_tags and every downstream reader.
        tags = normalise_dimensions(
            turn["tags"] if isinstance(turn.get("tags"), dict) else {"dimensions": {}})
        target, tgroup = resolve_subject(packet["volatile"]["edges"], gi, tags.get("subject"))
        if target:
            scene_target = target          # carries into the NEXT beat's ctx (target_edge)
        addressee = turn.get("addressee", "")          # WHO was spoken to (distinct from the subject)

        # validate the actor's same-pass self-report, mirror the chair: schema-invalid never moves state
        validation = validate_tags(tags, packet["volatile"]["percepts"], a["char"]["baseline"]["skills"])
        if not validation["ok"]:
            # FAIL-FAST (2026-08-30). This branch used to read `applied = {"dimensions": {}}`,
            # discarding the WHOLE self-report over one invalid field. See consolidation.tag_refusal.
            raise TagError(*tag_refusal(validation, names.get(speaker, speaker), turn_no))
        elif validation["flags"]:
            legit = CATALOG.get(tags.get("type", ""), {}).get("appraisal_map", [])
            applied = dict(tags, dimensions={d: v for d, v in tags.get("dimensions", {}).items() if d in legit})
        else:
            applied = tags
        if target:
            applied = dict(applied, target=target)
            if tgroup:
                applied["target_group"] = tgroup
        # what each primitive is ABOUT, computed BEFORE the appraisal so the fear this event raises
        # is fear OF the thing the event was about (emotion-basis.md: the target moves onto state)
        a["targets"] = retarget(a.get("targets") or {}, applied,
                                temperament=a["temperament"], affect=a["affect"], me=speaker)
        a["char"]["current"]["targets"] = dict(a["targets"])
        appraised = appraise(a["affect"], applied, a["profile"], targets=a["targets"])
        impact = sum(abs(appraised[p] - a["affect"][p]) for p in PRIMARIES)
        a["affect"] = decay(appraised, a["temperament"], a["profile"])
        a["last_spoke"] = beat
        log.append({"who": speaker, "action": turn["action"], "thought": turn["thought"], "tags": tags})

        # bonds: EVERY OTHER PERSON IN THE ROOM re-reads the speaker. This is the loop the engine
        # did not have — arc runs on the speaker, and relationships.md:5 says an edge is the
        # PERCEIVER's belief, so an actor-scoped engine moved the wrong person's edge (a betrayal
        # dropped the BETRAYER's trust in their victim). Each witness computes their own delta from
        # their own worth menu, their own expectation, and their own read of why it happened.
        # COMPUTED HERE, APPLIED AFTER THE COMMIT: the deltas ride the turn that caused them
        # (record-contract.md, quoted in ledger.py's docstring), so a rolled-back turn leaves no
        # orphan edge rows and the in-memory sheet never runs ahead of the log.
        bond_moves = _bond_moves(actors, present, speaker, applied)
        # BOTH orders persist. The second-order component used to be dropped here (the loop bound
        # it to `_v` and threw it away), so `their_view` rendered and then evaporated at scene end —
        # a mechanism that reaches the actor and not the record is half-built.
        rel_deltas = (
            [RelationshipDelta(perceiver=wid, target=speaker, axis=ax, delta=d, order="first")
             for wid, deltas, _v in bond_moves for ax, d in sorted(deltas.items())]
            + [RelationshipDelta(perceiver=wid, target=speaker, axis=ax, delta=d, order="second")
               for wid, _d, view in bond_moves for ax, d in sorted((view or {}).items())])

        # ---- persist the beat: the scene now writes to the same chronicle the chair does ----
        # TOKEN ACCOUNTING — `log_llm_call` had one caller repo-wide and it was a test, so
        # `llm_calls` stayed empty on every real run and there was no cost visibility at all.
        if not stub and direct.LAST_USAGE.get("model"):
            led.log_llm_call(run_id, turn_no, "act", direct.LAST_USAGE["model"],
                             direct.LAST_USAGE.get("tokens_in"), direct.LAST_USAGE.get("tokens_out"),
                             scene=cfg.get("name"))
        # THE WOUND TIER MOVES HERE, BEFORE THE COMMIT, so the deltas ride the turn's own
        # transaction. `arc.assess` runs AFTER append_turn and calls `append_arc_diff` separately —
        # a crash between the two leaves the turn permanently committed with the diff lost, and
        # `turns`' PRIMARY KEY refuses a re-append. That gap is documented, not copied.
        #
        # Matched against the PERCEIVED trigger set from the manifest, never `event_text`. A wound
        # must not move on something its owner did not see.
        # THE MICRO TIER accrues here, on the same pre-commit line as the wound trial and for the
        # same reason: the deltas ride `append_turn`'s own transaction rather than a separate
        # post-commit call that a crash can lose. What happened between this actor and the event's
        # SUBJECT becomes what that person makes them feel.
        toward_deltas = []
        _subj = applied.get("subject") or applied.get("target")
        if _subj:
            for _prim, _d in toward.observe(applied.get("dimensions") or {}).items():
                toward_deltas.append(TowardDelta(perceiver=speaker, target=str(_subj),
                                                 primary=_prim, delta=_d, source=event_text[:200]))
        _res = arc.derive_resilience(a["char"], a["char"]["current"].get("condition", {}))
        _wounds = (a["char"]["baseline"].get("drives") or {}).get("fears_wounds") or []
        wound_deltas = []
        for _w in _wounds:
            if not isinstance(_w, dict) or not str(_w.get("id", "")).strip():
                continue
            _d = wound.trial(_w, applied.get("dimensions") or {}, _res,
                             packet["manifest"].get("surfaces") or [])
            if _d:
                wound_deltas.append(WoundDelta(char_id=speaker, wound_id=str(_w["id"]),
                                               delta=_d, kind="event", source=event_text[:200]))
        led.append_turn(TurnCommit(
            run_id=run_id, turn=turn_no, actor=speaker,
            thought=str(turn["thought"]), action=str(turn["action"]),
            tags=tags if isinstance(tags, dict) else {}, affect=dict(a["affect"]),
            condition=dict(a["char"]["current"].get("condition", {})), validation=validation,
            events=_law_events(led, run_id, world, chars, turn, speaker,
                               location=cfg.get("location"), tick=turn_no) + [
                    Event(type=str(tags.get("type", "mundane")),
                          payload={"text": event_text, "dimensions": tags.get("dimensions", {}),
                                   "durability": tags.get("durability", "transient"),
                                   "subject": target, "subject_group": tgroup},
                          target=target,          # THE SUBJECT. Omitted at every Event site until 2026-08-30, so
                                                  # ledger._project's `victim = ev['target'] or ev['actor']` always
                                                  # fell through and a terminal harm marked the ACTOR dead, never the
                                                  # person harmed; the betray/bond branch was unreachable entirely.
                          actor=speaker)],
            manifest=packet["manifest"], recall=packet["recall_refs"], rel_deltas=rel_deltas,
            wound_deltas=wound_deltas, toward_deltas=toward_deltas))
        # the commit held, so the in-memory sheets may now follow the log
        if toward_deltas:
            toward.replay(a["char"], led.toward_deltas_for(run_id, speaker))
            _seen = sorted({t.target for t in toward_deltas})
            print("   TOWARD : %s  %s" % (names.get(speaker, speaker), ", ".join(
                "%s %s" % (names.get(w, w), " ".join("%s%+0.3f" % (k, v) for k, v in
                                                     sorted((a["char"]["current"]["toward"].get(w) or {}).items())))
                for w in _seen)))
        if wound_deltas:
            # RE-FOLD FROM THE LOG, never hand-apply. A first version of this incremented the
            # in-memory intensity per beat -- `clamp(intensity + delta)` -- while the resume path
            # computes `clamp(authored + SUM(deltas))`. With two trials on one wound in a scene
            # those DIVERGE the moment an intermediate value clamps, so the same scene played
            # straight and resumed would end at different intensities. Clamp-per-step is
            # order-dependent; `replay_wound_deltas` sums first for exactly that reason and says so
            # in its own docstring, which the hand-copy then ignored.
            # Calling the SAME function on the SAME rows the resume path reads makes divergence
            # impossible rather than unlikely. `bonds.py` records this lesson for edges: a replay
            # hand-copied into each driver drifts, and the copies are the defect.
            levers.replay_wound_deltas(_wounds, led.wound_deltas_for(run_id, speaker))
            for _wd in wound_deltas:
                _now = next((float(_w["intensity"]) for _w in _wounds
                             if str(_w.get("id", "")) == _wd.wound_id), None)
                print("   WOUND  : %s  %s %+0.4f -> %.3f"
                      % (names.get(speaker, speaker), _wd.wound_id, _wd.delta, _now))

        for wid, deltas, view in bond_moves:
            rels = actors[wid]["char"]["current"].setdefault("relationships", {})
            edge = rels.get(speaker, {})
            if deltas:
                edge = bonds.apply_deltas(edge, deltas)
            if view:
                edge = bonds.apply_reflection(edge, view)
            rels[speaker] = edge
            print("   BOND   : %s -> %s  %s%s" % (
                names.get(wid, wid), names.get(speaker, speaker),
                "  ".join("%s %+0.3f" % (ax, d) for ax, d in sorted(deltas.items())),
                ("   | reads them as: " + "  ".join("%s %+0.3f" % (ax, d)
                                                    for ax, d in sorted(view.items()))) if view else ""))
        # arc: a durable beat moves the speaker's baseline; persist + evolve them for the next beat
        diff = arc.assess(applied, impact, a["char"], a["char"]["current"]["condition"])
        if diff:
            a["char"] = arc.apply(a["char"], diff)
            led.append_arc_diff(run_id, speaker, turn_no, diff)
            a["profile"] = build_profile(a["char"])
            a["temperament"] = a["char"]["baseline"]["temperament"]
        # acquisition: a durable, subject-bearing beat becomes the speaker's lived belief
        # GATED: `assess` reads the raw tags by design, so a turn the engine REFUSED must not
        # reach it. Ungated, a schema-invalid tag still carried a merged `target` and wrote a
        # permanent vault belief out of a self-report validate_tags had just rejected.
        acquired = acquisition.assess(applied, tags, a["char"], world) if validation["ok"] else None
        if acquired:
            a["char"]["current"].setdefault("vault", []).append(acquired)
            acquisition.fold_vault(a["char"]["current"]["vault"])
            led.append_acquisition(run_id, speaker, turn_no, acquired)

        print("-- beat %d (turn %d) -- %s" % (beat + 1, turn_no, names.get(speaker, speaker)))
        # NEVER TRUNCATE. `_compose_event` already learned this: a 300-char cut sent the next
        # actor a fragment to answer. The operator log carried the same silent slice, so a line
        # ending mid-word gave no sign it had been cut.
        print("   ACTION : %s" % str(turn["action"]).replace("\n", " "))
        print("   THOUGHT: %s" % str(turn["thought"]).replace("\n", " "))
        # `addressee` is worth _ADDRESSED_BONUS against _FLOOR_THRESHOLD — several times the
        # whole threshold (both are in src/engine/floor.py; this comment deliberately does NOT
        # restate their values, because a number copied into prose is the duplicate-of-a-source-
        # of-truth class and drifts silently) — so it single-handedly decides whether a two-hander continues. It was
        # read by the urge loop and rendered nowhere: on 2026-08-29 a scene ended at max urge 0.022
        # (the addressed branch computes to 0.179) and establishing that the actor had left the
        # field empty took arithmetic rather than reading. A term that decides an outcome and is
        # never printed can only be inferred.
        # SHOW WHAT APPLIED, NOT WHAT WAS CLAIMED. This printed `tags` — the pre-validation input
        # — so a beat whose dimensions were narrowed (or, before the raise above, discarded whole)
        # printed identically to a healthy one. That is why the lull read as model flakiness for
        # three runs before anyone looked at the validator.
        _shown = applied.get("dimensions", {})
        _dropped = {d: v for d, v in (tags.get("dimensions") or {}).items() if d not in _shown}
        print("   TAGS   : %s %s  subj=%s  addressed=%s  conf=%.2f%s%s" % (
            tags.get("type", "?"), _shown, target or "-", addressee or "-",
            validation["confidence"],
            ("  DROPPED %s" % _dropped) if _dropped else "",
            ("  flags: %s" % "; ".join(render_flag(f) for f in validation["flags"]))
            if validation["flags"] else ""))
        print("   now    : %s" % direct_affect(a["affect"], a["temperament"]))
        # (faithfulness is enforced pre-commit by faithful_turn above — committed beats are leak-free)

        # witness-propagation: present bystanders remember + PERSIST the durable act they watched
        # (knowledge-model.md transmission: B's vault gains what B saw) — now folded to the ledger too,
        # so a witnessed belief survives the scene and resumes with the bystander.
        # ...and how far each one CREDITS it scales with their trust in whoever spoke
        # (relationships.md: "relationships are the gain on information flow"). The belief is now
        # computed per witness rather than once and shared, because two people in the same room do
        # not take the same thing from the same account.
        for wid in present:
            if wid == speaker:
                continue
            wchar = actors[wid]["char"]
            wedge = (wchar["current"].get("relationships") or {}).get(speaker) or {}
            wb = acquisition.witness_belief(names.get(speaker, speaker), tags, speaker,
                                            trust=wedge.get("trust"), world=world, witness_id=wid)
            if not wb:
                continue                                # transient / no summary / deceived target — next witness
            wvault = wchar["current"].setdefault("vault", [])
            if not any(isinstance(x, dict) and x.get("claim") == wb["claim"] for x in wvault):
                wvault.append(dict(wb))
                acquisition.fold_vault(wvault)
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
                belief = acquisition.reveal_name(wchar, eid, nm, world)
                if belief:
                    led.append_acquisition(run_id, wid, turn_no, belief)
                    print("   >> %s overhears the name %r (learned)" % (wid, nm))

        turn_no += 1                                    # this beat is committed; the next beat is a new turn

        if turn.get("exit"):
            present = [i for i in present if i != speaker]
            print("\n   >> %s leaves the scene. <<" % names.get(speaker, speaker))
            if len(present) < 2:
                ended = "exit"
                break

        # THE DECISION IS THE ENGINE'S; THE REPORTING IS THIS FILE'S. Every input to the
        # floor economy moved to src/engine/floor.py on 2026-09-03 and the choice combining
        # them was the one piece left behind, so the module named for the economy did not
        # hold the decision and the decision could not be tested without running a scene.
        nxt, urges, ended_because = _floor.next_speaker(
            actors, present, speaker, applied, target, tgroup, addressee, beat)
        if ended_because == "empty":
            ended = "empty"
            break
        if ended_because == "lull":
            print("\n== lull — no one is moved enough to answer (max urge %.3f, floor %.3f). "
                  "The scene settles. ==" % (urges[_floor.leader(urges)][0], _FLOOR_THRESHOLD))
            print("   urges  : %s   [spoken to: %s]" % (
                "  ".join("%s=%.3f%s" % (k, v[0], "+addr" if bool(addressee) and norm_id(addressee) == norm_id(k) else "")
                          for k, v in urges.items()),
                addressee or "no one — the addressed bonus (+%.2f) applied to nobody" % _ADDRESSED_BONUS))
            ended = "lull"
            break
        print("   urges  : %s  -> floor: %s\n" % (
            "  ".join("%s=%.2f[sal%.2f dis%.2f]" % (k, v[0], v[1], v[2]) for k, v in urges.items()),
            names.get(nxt, nxt)))
        speaker = nxt

    print("\n== scene ended: %s — %d beats ==" % (ended, len(log)))
    return turn_no


def record_and_park(led, run_id, scene_cfg, start_turn, next_turn, cast_ids=(), announce=True):
    """Close a scene: record its boundary, persist the snapshot, park the run. -> the last turn index.

    EXTRACTED 2026-09-03 BECAUSE A TEST WAS REIMPLEMENTING IT. `tests/test_pipeline_e2e.py` carried a
    `_run_scene` whose docstring read "Mirror scene.py:main's run + boundary-record (the
    orchestration the CLI does)" — and the copy had already drifted from the original in four ways,
    which is what a copy does when the original moves:

      1. it called `append_scene` with six positional arguments, so it passed no `cfg` — the schema
         v14 PIN, the thing that lets a resumed run say what location, cast, props and opening tags
         produced the turns it replays. The suite named end-to-end never once exercised it, and
         every scene row it wrote carried an empty fingerprint where the driver's carries a hash.
      2. no `voice`, so the per-scene narration choice defaulted silently.
      3. no `knowledge`, likewise.
      4. no `persist_snapshot` and no `set_status(..., "parked")` — neither the snapshot cache nor
         the park transition was covered by the suite that claims the widest coverage in the repo.

    Nobody introduced those four deliberately. That is the argument for the extraction rather than
    for fixing the copy: CLAUDE.md's own rule is that a list mirroring what the code already knows
    should be DERIVED, and a second implementation is that same defect with more lines.

    `announce` exists so the driver keeps printing its line and a test harness stays quiet.

    RECORDING AND PARKING ARE SEPARATE, and the split came out of retiring that copy rather than
    from taste: a boundary is recorded PER SCENE, while parking is what an INVOCATION does on its
    way out. The driver runs one scene and exits, so it does both and the distinction is invisible
    there; `tests/test_pipeline_e2e.py` runs several scenes in one process, and the first thing it
    did with a combined function was park the run and then fail its own second scene with
    LEDGER_RUN_NOT_ACTIVE. The copy had hidden that seam by implementing neither half.
    """
    last = record_boundary(led, run_id, scene_cfg, start_turn, next_turn, cast_ids, announce)
    park(led, run_id, last)
    return last


def record_boundary(led, run_id, scene_cfg, start_turn, next_turn, cast_ids=(), announce=True):
    """Write the scene row for the turns just committed. -> the last turn index. Per SCENE."""
    last = max(next_turn - 1, 0)
    if next_turn > start_turn:                          # at least one beat committed -> record it
        scene_no = led.next_scene_no(run_id)
        pov = scene_cfg.get("pov") or (cast_ids[0] if cast_ids else None)
        led.append_scene(run_id, scene_no, scene_cfg.get("name", "scene"), pov, start_turn, last,
                         voice=scene_cfg.get("voice", "close-third"),
                         knowledge=scene_cfg.get("knowledge", "pov"),
                         cfg=scene_cfg)
        if announce:
            print("recorded scene %d: %r (turns %d-%d, pov=%s)"
                  % (scene_no, scene_cfg.get("name", "scene"), start_turn, last, pov))
    return last


def park(led, run_id, last):
    """Persist the snapshot cache and park the run. Per INVOCATION, not per scene."""
    led.persist_snapshot(run_id, last, led.fold(run_id, last))
    led.set_status(run_id, "parked")


def main():
    ap = argparse.ArgumentParser(
        description="the multi-agent scene runner - set the scene, the agents push it; the chronicle persists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # THE POINT OF USE. This is the only surface a user reaches without first knowing which of
        # the 62 docs to open, and the fact below is the one that costs work when it is not known.
        epilog="""RE-RUNNING A SCENE IS NOT A RETRY.
  The log is append-only. A re-run takes the NEXT scene number, so the scene you rejected stays
  in the chronicle and the cast opens the new one carrying the state it gave them. You get a
  sequel, played by characters that scene already changed.

  There is no fork and no undo. The recovery path is the save-file discipline: copy the run db
  before a scene you might reject, and restore it if you do.
  See docs/guide-user-path.md section 6.""")
    ap.add_argument("--book", default=None, help="a REAL BOOK: slug under $SWE_BOOKS, or a path")
    ap.add_argument("--vault", default=None, help="older spelling of --book (a path)")
    ap.add_argument("--stub", action="store_true", help="deterministic stand-in, no API")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--budget", type=int, default=14, help="max beats")
    ap.add_argument("--seed-base", type=int, default=0, dest="seed_base",
                    help="sampling seed base; per-beat seed = base*1000 + beat. Vary it (0..K-1) to draw a "
                         "REAL K-sample: at a fixed base two runs of one cfg reproduce byte-identically. "
                         "Default 0 reproduces every run committed before this flag existed")
    ap.add_argument("--db", default=None, help="chronicle db path (default <vault>/runs/<book>.db)")
    ap.add_argument("--resume", default=None, help="run_id to continue — a later scene in the same chronicle")
    ap.add_argument("--scene", default=None, help="a director-authored scene cfg JSON (default: the built-in BP13 fixture)")
    ap.add_argument("--no-think", action="store_false", dest="think",
                    help="disable model thinking (Ollama) for fast iteration; thinking is ON by default")
    ap.add_argument("--prompt-only", action="store_true", dest="prompt_only",
                    help="emit the turn prompt for the beat's speaker as JSON and exit — the act "
                         "seam's outbound half. Any model anywhere can consume this "
                         "(docs/orchestration.md seam 1)")
    ap.add_argument("--turn-json", default=None, dest="turn_json",
                    help="a file holding {action, thought, tags, exit?, addressee?} (or '-' for "
                         "stdin) — the inbound half. Used INSTEAD of the local model for the first "
                         "beat of this invocation; the engine validates, appraises and commits it "
                         "through the SAME path a locally-generated turn takes, faithfulness wall "
                         "included. Pair with --resume and --budget 1 to act one beat at a time")
    args = ap.parse_args()

    supplied = None
    if args.turn_json:
        raw = sys.stdin.read() if args.turn_json == "-" else open(args.turn_json, encoding="utf-8").read()
        supplied = json.loads(raw)
        if not isinstance(supplied, dict):
            raise SystemExit("--turn-json must hold a JSON object, got %s" % type(supplied).__name__)

    # pre-warm: cold-load the model NOW, before load_book pulls the engine's recall models into host RAM.
    # On this RAM-constrained host the 17 GB model's cold load (UseMmap:false) OOMs if it lands mid-scene
    # with scene.py resident (ggml mem_buffer NULL -> HTTP 500; server.log 2026-06-14). Warming first puts
    # the cold load where host RAM is free; every beat then hits a warm model. Fail loud — a down daemon
    # should stop us here, not on beat 1. Stub runs and non-ollama models skip.
    if not args.stub and args.model.startswith("ollama/"):
        _ollama([{"role": "user", "content": "ok"}], args.model[len("ollama/"):], max_tokens=4, think=False)
        print("pre-warmed %s\n" % args.model)

    from src.engine import books
    spec = args.book or args.vault
    if not spec:
        raise SystemExit("pass --book (a slug under $SWE_BOOKS, or a path)")
    try:
        book_dir = books.resolve(spec)
    except books.BookError as e:
        raise SystemExit(str(e))
    world, chars = load_book(book_dir)
    book_name = books.slug(book_dir)
    try:                                          # the chronicle lives WITH the book — enforced,
        default_db = books.assert_db_for_book(book_dir, args.db)   # not merely defaulted
    except books.BookError as e:
        raise SystemExit(str(e))
    led = Ledger(default_db)
    scene_cfg = load_scene_cfg(args.scene) if args.scene else BP13             # director-authored scene, or the default fixture
    cast_ids = [c["id"] for c in scene_cfg["cast"]]

    # THE CAST MUST BE IN THE BOOK, and this refuses instead of dying nine lines later on a KeyError.
    #
    # CLAUDE.md records that an entire scene from a private novel once served as this file's DEFAULT
    # fixture, so every no-argument run played someone's book. The content was scrubbed; the SHAPE
    # survived — BP13 is still a hardcoded scene whose cast is ilsa/arden/corin, and `--book <any
    # other book>` with no `--scene` indexed `chars[cid]` for people that book has never heard of.
    # Measured 2026-09-02, the first time either driver's main() was ever run by a test:
    # `KeyError: 'ilsa'` before a single turn.
    #
    # It REFUSES rather than substituting the book's own cast: BP13's situation text names Pell,
    # Holloway, Arden, Ilsa and Corin in prose, so pairing it with a different cast would produce a
    # beat whose words describe people who are not in it — a silent wrong answer instead of a loud
    # refusal.
    _absent = [cid for cid in cast_ids if cid not in chars]
    if _absent:
        raise SystemExit(
            ("scene cast %s is not in this book.%s" + chr(10) +
             "  this book's characters: %s" + chr(10) +
             "  pass --scene <cfg.json> with a cast drawn from them; the built-in scene is a "
             "fixture for this repo's own characters and fits no other book.")
            % (", ".join(repr(c) for c in _absent),
               "" if args.scene else "  (no --scene given, so the built-in fixture scene was used)",
               ", ".join(sorted(chars)) or "none"))

    if args.resume:
        run_id = args.resume
        led.set_status(run_id, "active")
        state = led.resume(run_id)
        # BIBLE DRIFT — the detection half, which until 2026-08-24 had no caller anywhere outside
        # tests. CLAUDE.md hard rule 1 advertises this mechanism ("`bible.drifted()` detects; it
        # does not abort"), and the PINNING ran while the COMPARING never did, so the exact failure
        # it was built for — a mid-book edit silently changing what later turns are computed from —
        # stayed invisible in practice. Same shape as `verdict_for`, memorialized at scene.py:170.
        # Detection only, deliberately: an author legitimately edits a book between scenes, and
        # refusing to resume would make the common case the error case.
        from src.engine import bible                  # local, as everywhere else in this file
        from src.engine import scene_cfg as scene_cfg_mod   # aliased: `scene_cfg` is the loaded dict here
        _drift, _detail = bible.drifted(led.con, run_id, world, chars)
        if _drift:
            print("  [!] %s" % _detail)
            print("      earlier turns were computed from the pinned bible; later ones will not be.")
        # CFG DRIFT — the same detection for the other authored input (schema v14). The bible pin
        # covers the world and the cast; the cfg covers the location, the props and the opening
        # tags, and it shaped every turn in the scene it ran. Detection only, for the reason above.
        #
        # Compared ONLY against scenes recorded under this cfg's own name. Every other scene in the
        # run legitimately ran from a different cfg, so comparing against all of them would report
        # drift on every resume — a guard that cries wolf is a guard that gets switched off
        # (`bible._canonical` states the rule).
        _cfg_name = scene_cfg.get("name", "scene")
        for _s in led.scenes_for(run_id):
            if _s["label"] != _cfg_name:
                continue
            _cd, _cdet = scene_cfg_mod.drifted(led.con, run_id, _s["scene_no"], scene_cfg)
            if _cd:
                print("  [!] scene %d (%s): %s" % (_s["scene_no"], _cfg_name, _cdet))
                print("      that scene's turns were computed from the pinned cfg, not this one.")
        for cid in cast_ids:                                       # rehydrate each cast member the prior scene evolved
            ch = chars[cid]
            for diff in led.arc_diffs_for(run_id, cid):
                ch = arc.apply(ch, diff)
            acq = led.acquisitions_for(run_id, cid)
            if acq:
                ch["current"].setdefault("vault", []).extend(acq)
            from src.engine.acquisition import fold_vault
            ch["current"]["vault"] = fold_vault(ch["current"].get("vault", []))
            # EDGES — replayed from the append-only log, the same way the arc is. Without this a
            # resumed cast reverted to sheet-authored relationships and every trust movement from
            # prior scenes was silently gone (the arc stopped writing edges when bonds.py took
            # them, and nothing replaced the replay).
            _moves = led.edge_deltas_for(run_id, cid)
            # ORDERED REHYDRATE: declarations and movements interleaved in the order they
            # happened, because drift and deltas do not commute.
            bonds.rehydrate(ch["current"].setdefault("relationships", {}),
                            ch["baseline"].get("relationship_priors", {}),
                            led.timeline_for(run_id, cid))
            if _moves:                       # OPERATOR output, not the prompt — rule 5 is the prompt
                print("   %s: refolded %d edge movement(s) toward %s"
                      % (cid, len(_moves), ", ".join(sorted({m[0] for m in _moves}))))
            # THE WOUND TIER. Same shape as the edge refold above, and the same failure if it is
            # omitted: a resumed cast's wounds silently return to SHEET strength, so a phobia the
            # character spent a whole book walking into hits exactly as hard on the next page.
            # `replay_wound_deltas` stamps `_authored_intensity` BEFORE applying anything — that
            # ordering is what keeps `levers.scale_to_wounds` scaling against the AUTHORED value
            # rather than the already-healed one.
            _tmoves = led.toward_deltas_for(run_id, cid)
            toward.replay(ch, _tmoves)
            if _tmoves:
                print("   %s: refolded %d micro movement(s) toward %d person(s)"
                      % (cid, len(_tmoves), len({m[0] for m in _tmoves})))
            _wmoves = led.wound_deltas_for(run_id, cid)
            levers.replay_wound_deltas(
                (ch["baseline"].get("drives") or {}).get("fears_wounds") or [], _wmoves)
            if _wmoves:                      # OPERATOR output, not the prompt — rule 5 is the prompt
                print("   %s: refolded %d wound movement(s) on %s"
                      % (cid, len(_wmoves), ", ".join(sorted({m[0] for m in _wmoves}))))
            latest = led.latest_affect(run_id, cid)
            if latest:
                ch["current"]["affect"] = latest["affect"]
            chars[cid] = ch
        start_turn = state["turn"] + 1
        print("resumed %s at turn %d (determinism OK)\n" % (run_id, state["turn"]))
    else:
        # A UNIQUENESS SUFFIX, as `direct.py:688` has carried all along. Epoch SECONDS alone
        # collide when an operator refuses a scene, fixes the cfg and reruns within the same
        # second — `create_run` then hits the primary key and raises a RAW sqlite3.IntegrityError
        # with no code behind it. Reproduced 2026-09-03.
        run_id = "scene-%s-%d-%s" % (book_name, int(time.time()), uuid.uuid4().hex[:6])
        run_cfg = {"catalog_version": 1,
                   "models": {"turn": "stub" if args.stub else args.model},
                   "prompt_versions": {"turn": 1}}
        from src.engine import bible
        _fp = bible.build(led.con, world, chars)                          # pin the bible
        # REFUSE BEFORE THE RUN EXISTS. The pre-flight used to sit inside `run_scene`, after this
        # line, so a scene the world refuses left an `active` run with zero turns — permanent, the
        # log being append-only, and picked as the newest row by `canon_digest._latest_run`, which
        # made the digest's default selection land on the empty one. The fingerprint is already in
        # hand here, so nothing about the check needs the run.
        law_preflight(led, cfg=scene_cfg, world=world, chars=chars, fp=_fp)
        run_cfg[bible.CONFIG_KEY] = _fp
        led.create_run(run_id, run_cfg)
        for cid in cast_ids:
            led.register_character(run_id, cid, chars[cid]["fixed"], chars[cid]["baseline"])
        # THE DIRECTOR SEEDS AS EVENTS, NEVER AS A DECREE (`world-state-ledger.md` write-path #3:
        # the director "may seed ledger state ... but always as an event"). That is what makes
        # creating a tension and minting one mid-run the SAME mechanism at different turns.
        from src.engine import tensions as _tn
        from src.engine.records import Event as _Ev
        from src.engine import world_events as _we
        _seeds = _tn.seed_events(world)
        if _seeds:
            _we.append(led, run_id, 0, [_Ev(type=s["type"], payload=s["payload"]) for s in _seeds])
            print("seeded %d authored tension(s)" % len(_seeds))
        start_turn = 0
        print("new chronicle: %s\n" % run_id)

    # REGISTER THE CAST ON EVERY PATH, not only on create. `characters` IS the engine's definition
    # of who is real — `Ledger._seed` reads it to seed the fold's agents — and registration used to
    # run only inside the create-run branch. CLAUDE.md makes both drivers first-class writers to the
    # SAME chronicle, so a run started by one and continued by the other committed turns for people
    # the chronicle never recorded as existing: `_project` setdefaults any string an event names, so
    # the phantom folds identically both ways and `resume` returns OK. Their life_status and
    # location then come from a default rather than a sheet.
    #
    # An append, not a rewrite: schema v20's triggers refuse UPDATE and DELETE on `characters` and
    # leave INSERT alone, which is exactly the shape a late-joining cast member needs.
    _known = {r["char_id"] for r in led.con.execute(
        "SELECT char_id FROM characters WHERE run_id=?", (run_id,))}
    for cid in cast_ids:
        if cid not in _known and cid in chars:
            led.register_character(run_id, cid, chars[cid]["fixed"], chars[cid]["baseline"])
            print("registered late-joining cast member: %s" % cid)

    # THE SWEEP IS PRINTED, NOT RAISED, AND NOT RESUME-GATED. Unlike `bible.drifted`, which
    # has nothing pinned to compare on a new run, the DANGEROUS case here IS the new run: a
    # fresh run_id written into a database that lost 50 of its 68 walls on migration and
    # never said so.
    print(integrity.startup_line(led.con))

    next_turn = run_scene(world, chars, scene_cfg, led, run_id, start_turn, args.model, args.stub, args.budget,
                          think=args.think, seed_base=args.seed_base,
                          prompt_only=args.prompt_only, supplied=supplied)
    if args.prompt_only:                                # outbound half emitted; nothing was acted
        return
    last = record_and_park(led, run_id, scene_cfg, start_turn, next_turn, cast_ids)
    print("\nparked %s at turn %d — continue with: python scripts/scene.py --vault \"%s\"%s --resume %s" % (
        run_id, last, book_dir, " --stub" if args.stub else "", run_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
