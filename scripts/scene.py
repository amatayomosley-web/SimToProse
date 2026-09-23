#!/usr/bin/env python3
"""scene.py — the multi-agent scene runner (the director sets the scene; the agents push it).

The chair (direct.py) runs ONE actor against a typed circumstance. This runs a SCENE: the director
sets the situation, the present cast, and each actor's DRIVE — a genuine standing want, blind to how
the scene ends (design.md scene-goals discipline). Then the agents converse with no scripted lines.

v2 (multi-character.md urge model): each beat, the floor passes to the actor with the highest URGE to
speak — urge = salience + addressed_bonus + disruption_stake − recency_penalty − inhibition — not pure
salience. The disruption_stake (the heat of the exchange × the listener's order/standing values) is what
surfaces the decorum-keeper who isn't moved by the topic but won't abide a quarrel in front of them; the
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
from src.engine.scene import (assemble, resolve_subject, subject_groups, norm_id,  # noqa: E402
                              referenced_ids)
from src.engine import acquisition                                  # noqa: E402  (witness-propagation + name-transmission)
from src.engine import integrity                              # noqa: E402
from src.engine import claims                                 # noqa: E402  (the utterance/T2 path)
from src.engine import read_api as _read_api                  # noqa: E402  (what is established: the lore fence)
from src.engine import scene_facts as _scene_facts        # noqa: E402  (what has happened, POV-filtered)
import keeper as _keeper                                       # noqa: E402  (the ruling seat at the canon gate)
from src.engine.state import build_profile, appraise, decay, receive   # noqa: E402
from src.engine import rungs                                        # noqa: E402  (a reading's height)
from src.engine.records import RecordError as _SeatRefusal          # noqa: E402
import appraiser                                                   # noqa: E402  (the two seats)
import provider as _provider                                       # noqa: E402  (the frontier-model seam)
# NOT the `decay` above — that one is state.decay, the AFFECT relaxation. This is the
# belief-decay module. The names collide, so both are only ever reached under an alias
# here; importing it bare would silently rebind the affect function.
from src.engine import decay as _belief_decay                       # noqa: E402
from src.engine import clock as _clock                              # noqa: E402
_clockmod = _clock                                                   # the minute clock; operator prints
from src.engine.targets import retarget                             # noqa: E402  (per-primitive aboutness)
from src.engine import targets as _targets
from src.engine import concepts as _concepts                         # noqa: E402  (its log: binds_from/binds_for/replay)
from src.engine.records import (PATHS, Event, TurnCommit, RelationshipDelta, WoundDelta,
                                TowardDelta, RecordError)  # noqa: E402
from src.engine.consolidation import (validate_tags, CATALOG, TagError, tag_refusal,
                                       render_flag)         # noqa: E402  (validate the actor's same-pass self-report)
from src.engine.ledger import Ledger                               # noqa: E402  (the chronicle the scene now persists to)
from src.engine import arc                                         # noqa: E402  (durable baseline evolution across scenes)
from src.engine import bonds                                       # noqa: E402  (the relationship tier — per WITNESS, not per actor)
from src.engine import attachments                                 # noqa: E402  (gate 5: what a person holds that is not a person)
from src.engine import bond_rest                                   # noqa: E402  (the rest half: drift toward a declared rest, the ordered fold)
from src.engine import systems as _systems                        # noqa: E402  (which systems this book runs)
from src.engine import condition as _condition                    # noqa: E402  (energy and stress that move)
from src.engine import body as _body                              # noqa: E402  (strength and exertion)
from src.engine import tells as _tells                            # noqa: E402  (the signs a sharp eye catches)
from src.engine import injuries as _injuries                      # noqa: E402  (bodily injuries, healing over time)
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
from src.engine import passage as _passage                      # one clock, two drivers (2026-09-19)
_salience        = _floor.salience
_bond_moves      = _floor.bond_moves


def _act_word_near(axis, height):
    """Operator print only: a priced act height -> the act word nearest it, so the log shows words."""
    from src.engine import severity as _sev
    try:
        return min(_sev.ACT_WORDS[axis], key=lambda w: abs(_sev.act_value_of(axis, w) - float(height)))
    except Exception:                          # noqa: BLE001 - a print helper never breaks a beat
        return "?"
_order_weight    = _floor.order_weight
_urge            = _floor.urge
_ADDRESSED_BONUS = _floor.ADDRESSED_BONUS
_RECENCY_PENALTY = _floor.RECENCY_PENALTY
_INHIBITION      = _floor.INHIBITION
_FLOOR_THRESHOLD = _floor.FLOOR_THRESHOLD

# ---- the default scene config: situation + present acting cast + each actor's DRIVE (genuine, blind to outcome) ----
DEFAULT_SCENE = {
    # INVENTED FIXTURE — no book. CLAUDE.md hard rule 1: real books never live in this repo, and that
    # includes their PLOT. This default was once a scene lifted from a private novel, and later that same
    # scene under new names, so every `scene.py` run without --scene played someone's book. It must exercise:
    # a SUBJECT who is absent but salient (Ruth's nephew), three drives that genuinely collide rather than
    # agree (a lull is the failure mode — scene-authoring-rules.md Rule 4), and a care-versus-standing axis
    # (Dev argues from need, Ruth from seniority) for the appraisal to separate on.
    "situation": (
        "The allotment committee meets in the tool shed after last night's flood took the lower beds. "
        "Ruth, who chairs it, wants the upper beds shared out by seniority; Dev, who lost his whole plot, "
        "wants them shared out by need; and Agnes knows the flood gate was left open by Ruth's nephew, "
        "who is not here."),
    "subject": ("nephew", None),
    "at": {"day": 1, "time": "20:00"},           # evening; the clock is required of every scene (clock.py)
    "at_minutes": 20.0 * 60.0,                    # what load_scene_cfg would derive; DEFAULT_SCENE bypasses the loader
    "lasts_minutes": None,
    "opening_tags": {"type": "loss", "dimensions": {"care_relevant": 0.4, "loss": 0.6, "social_violation": 0.3},
                     "durability": "transient"},
    "cast": [
        {"id": "ruth",  "drive": "have the upper beds shared out by seniority tonight, and keep the flood gate out of it"},
        {"id": "dev",   "drive": "get a bed for everyone the flood left with nothing, starting with his own"},
        {"id": "agnes", "drive": "have it said who left the flood gate open before a single bed is shared out"},
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
    a real book, act=None makes every law bear and nearly all of them deny, so a blanket call would
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
    (the hardcoded DEFAULT_SCENE above is just the default fixture). Required: situation (non-empty str) and
    cast (non-empty list of {id, drive}). Optional: name, subject ([id, group] -> tuple),
    opening_tags. REQUIRED since 2026-09-10: `at` — when the scene opens; optional `lasts` — how
    long it runs (minutes, or "2h"); `elapsed` is derived and refused if present (clock.py).
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
    # THE CLOCK (2026-09-10, clock.py). `at` is REQUIRED — when this scene opens, {day, time} —
    # and `lasts` is optional. `elapsed` is REFUSED: it is derived from the previous scene's
    # reading now, and a cfg that also states it is two sources for one fact. A real book
    # written before today carries no `at`; this names the field rather than guessing a time.
    from src.engine import clock as _clock
    if "at" not in cfg:
        raise ValueError("scene cfg %r needs `at`: {\"day\": N, \"time\": \"HH:MM\"} — when the scene opens "
                         "(BLUEPRINT-scene.md section 11)" % (cfg.get("name") or path,))
    if "elapsed" in cfg:
        raise ValueError("scene cfg %r carries `elapsed`, which is DERIVED from `at` now; delete it "
                         "(BLUEPRINT-scene.md section 11)" % (cfg.get("name") or path,))
    try:
        cfg["at_minutes"] = _clock.parse_at(cfg["at"])
        cfg["lasts_minutes"] = _clock.span_minutes(cfg.get("lasts"))
    except Exception as e:                       # noqa: BLE001 — the CLI reports the field, never a traceback
        raise ValueError("scene cfg %r: %s" % (cfg.get("name") or path, e))
    # PROPS — scene-authoring-rules.md Rule 5. Optional on the cfg (every cfg written before
    # 2026-08-24 has none and must keep running byte-identically), but once declared they reach the
    # actor as percepts via gate.perception_scope. Normalised to a list of non-empty strings here so
    # the engine never has to defend against a stray dict.
    props = cfg.get("props")
    cfg["props"] = [str(x).strip() for x in props if str(x).strip()] if isinstance(props, list) else []
    # THE DIRECTOR'S HOLDS (bond-arithmetic.md s3, gate 5): typed declarations with a RELATION WORD —
    # never a float — priced by the engine's table at the scene's first turn. Optional; absent -> [].
    decl = cfg.get("attachments")
    if decl is None:
        cfg["attachments"] = []
    elif not (isinstance(decl, list) and all(isinstance(d, dict) and d.get("char") and d.get("entity") and d.get("relation") for d in decl)):
        raise ValueError("scene cfg %r: `attachments` must be a list of {char, entity, relation} declarations" % (cfg.get("name") or path))
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
    # laziness: measured on a real book, act=None makes every law bear and nearly all of them deny,
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
    # THE DIRECTOR DECLARES A HOLD (bond-arithmetic.md s3, gate 5): a typed row with a RELATION WORD,
    # priced by the engine's table — never a float — written at the scene's first turn on its own
    # transaction (like seed and declare_time) and applied to the sheet BEFORE the profiles are built.
    _decl = []
    for d in cfg.get("attachments") or []:
        if d["char"] not in chars:
            raise SystemExit("scene %r declares a hold for %r, who is not in this book" % (cfg.get("name"), d["char"]))
        _decl.append(attachments.declared_row(d["char"], d["entity"], d["relation"], "director"))
        chars[d["char"]]["current"].setdefault("attachments", {})[d["entity"]] = {
            "hold": attachments.hold_of(d["relation"]), "sign": "+", "note": "director: %s" % (d.get("note") or d["relation"])}
        print("   HOLD   : %s %s %s (director)" % (d["char"], d["relation"], d["entity"]))
    attachments.declare(led.con, run_id, start_turn, _decl)
    # WHICH SYSTEMS THIS BOOK RUNS (gate systems-registry, 2026-09-22): an off system's block is
    # emptied here - after any resume has folded the log back on, before a profile is built - so every
    # reader sees it absent, and its mover is skipped below. No `systems` key = every system on.
    _sys = _systems.for_book(world)
    for c in cfg["cast"]:
        _systems.strip(chars[c["id"]], _sys)
    # THE CONDITION FLOW (gate condition-flow): refuse a sheet it cannot move, and a scene that states a
    # condition for a book with none, before a single beat is paid for.
    try:
        if "condition_flow" in _sys:
            for c in cfg["cast"]:
                _condition.require(chars[c["id"]])
        if "body" in _sys:                          # every act is weighed against a strength
            for c in cfg["cast"]:
                _body.require(chars[c["id"]])
                # the mind's and the body's reserves beside the shared pool (gate energy-reserves)
                chars[c["id"]]["current"]["condition"] = _condition.split(chars[c["id"]]["current"]["condition"])
        if "injuries" in _sys:                      # a sheet's page-one injuries must be readable (gate injuries)
            for c in cfg["cast"]:
                _injuries.require(chars[c["id"]])
        if cfg.get("condition") and "condition" not in _sys:
            raise SystemExit("scene %r states a condition, but this book runs no condition system" % cfg.get("name"))
        _cond_errs = _condition.declaration_errors(cfg.get("condition"), [c["id"] for c in cfg["cast"]])
        if _cond_errs:
            raise SystemExit("scene %r: %s" % (cfg.get("name"), "; ".join(m for _c, m in _cond_errs)))
    except RecordError as e:
        raise SystemExit("condition flow: %s" % e)
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
    # PRESENCE IS MATCHED AGAINST THE PEOPLE REGISTRY, and the two id spaces are not the same one:
    # `gate._extract_named_entities` yields the FULL world.people id while matching on its first
    # part, and a cast is written in the short sheet ids. `gate._present_match` joins them on the
    # extractor's own key. What it CANNOT repair is a cast id that names no world person at all —
    # such a character is never extracted as an entity, so they take no percept and no edge, and
    # presence never applies to them. That is pre-existing and harmless to the presence work, but it
    # is worth saying out loud once, because it is invisible in the prose and looks like a bug later.
    _known = set()
    for _p in (world.get("people") or []):
        if isinstance(_p, dict) and _p.get("id"):
            _known.add(_p["id"])
            _known.add(str(_p["id"]).split("_")[0])   # the extractor's own join key
    _unregistered = [i for i in ids if i not in _known]
    if _unregistered:
        print("   note: cast not in world.people: %s — never perceived as entities, so no percept "
              "and no edge for them (unchanged by presence)" % ", ".join(sorted(_unregistered)))
    present = list(ids)

    # DRIFT (relationships.md: "without reinforcement, relationships slowly decay toward a resting
    # state ... affinity fades faster than trust"). Applied at scene START, once, because a gap in
    # the story is between scenes — a beat has no duration, and drifting per beat would cool a
    # friendship over the course of one conversation. The unit of `elapsed` is the DIRECTOR'S: this
    # engine holds no world clock, so nothing here converts days into anything.
    # ONE CLOCK, IN MINUTES (clock.py, 2026-09-10). Log this scene's reading, derive the gap since
    # the previous scene ENDED, and hand the gap to the four older tiers exactly as before —
    # plus emotion, the fifth. A scene that lulled early last time owes its unspent `lasts` here.
    if "at_minutes" not in cfg:                       # a dict cfg that bypassed load_scene_cfg
        if "at" not in cfg:
            raise SystemExit("scene %r needs `at`: {day: N, time: HH:MM} — when it opens (clock.py)"
                             % (cfg.get("name") or "scene",))
        cfg["at_minutes"] = _clock.parse_at(cfg["at"])
        cfg["lasts_minutes"] = _clock.span_minutes(cfg.get("lasts"))
    # ONE CLOCK, READ THE SAME WAY BY BOTH DRIVERS (src/engine/passage.py, gate driver-clock-
    # parity, 2026-09-19). This used to be ~40 lines inline here — record_scene_clock, gap_before,
    # unspent_before, the affect decay, declare_time, then per-character drift/wound/arc/toward —
    # and `scripts/direct.py` could not reach a line of it. It still runs exactly that, in the same
    # order and the same units; only the CALL moved, so a chair opened with `--at` gets the same
    # clock a scene does.
    _clock_result = _passage.open_scene(led, run_id, start_turn, cfg["at_minutes"], cfg.get("lasts_minutes"),
                                        budget, {i: actors[i]["char"] for i in ids}, names=cfg.get("name"),
                                        flow="condition_flow" in _sys, body="body" in _sys,
                                        stated=_condition.stated_gaps(cfg.get("condition")),
                                        injuries="injuries" in _sys)
    # THE DIRECTOR STATES HOW THEY ARRIVE (owner ruling C3a): words, priced by the engine, applied AFTER the
    # opening's rest - the state AT the opening. The cfg is pinned whole, so the replay reads it back.
    for _c in _condition.apply_declared({i: actors[i]["char"] for i in ids}, cfg.get("condition")):
        print("   CONDITION: %s arrives %s" % (_c, ", ".join("%s %s" % (k, d[k]) for d in cfg["condition"]
                                                          if str(d["char"]) == _c for k in ("energy", "stress") if k in d)))
    # `actors[i]["affect"]` is THIS driver's own cache beside the sheet (built once at actor
    # construction, above) — `open_scene` mutates `char["current"]["affect"]` and knows nothing of
    # the cache, so it is refreshed here or every beat after this one reads the pre-decay value.
    # THE PROFILE IS BUILT AFTER THE OPENING (gate opening-before-profile, 2026-09-23). It was built only at actor
    # construction, above, before `open_scene` faded wounds, arcs and attitude across the gap, so a scene's first
    # beats ran on the pre-fade profile until a wound or an arc next changed. `mood_fold.replay` builds it here too.
    for i in ids:
        actors[i]["affect"] = dict(actors[i]["char"]["current"]["affect"])
        actors[i]["profile"] = build_profile(actors[i]["char"])
        actors[i]["temperament"] = actors[i]["char"]["baseline"]["temperament"]
    per_beat = _clock_result["per_beat"]
    if _clock_result["elapsed"]:
        print("\n  %s minutes since the last scene ended%s — edges relaxed toward each character's"
              " resting disposition, feelings toward their rest" % (
                  int(_clock_result["elapsed"]),
                  " (+%d owed by the last scene)" % int(_clock_result["owed"]) if _clock_result["owed"] else ""))
    print("  opens %s%s" % (_clockmod.format_at(cfg["at_minutes"]),
                            ", lasts %d min (%.1f per beat)" % (int(cfg["lasts_minutes"]), per_beat)
                            if cfg.get("lasts_minutes") else ", no duration authored — no decay inside the scene"))

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
        # THE MOMENT AS THIS SPEAKER READS IT (gate tells; only when the book runs `tells`): the signs other actors
        # let slip, marked by the event reader, are cut for a speaker who does not catch them and named for one who
        # does. Without the system every speaker reads the log whole, as before.
        _seen, _tells_hidden, _tells_noticed = ((_tells.for_listener(log, speaker,
                                                    _tells.catches(a["char"], tired="condition_flow" in _sys)))
                                                if "tells" in _sys else (log, [], []))
        event_text = _compose_event(cfg["situation"], _seen, names)
        scene_slice = {"event": {"text": event_text, "kind": "mundane"},
                       "target": scene_target,
                       # WHO THE SPEAKER IS ENGAGING (the redesign's gate 1): the last speaker, when
                       # someone else spoke last — the person this beat answers. assemble composes
                       # the played vector toward them; absent, it falls back to the subject.
                       "engaged": (log[-1]["who"] if log and log[-1]["who"] != speaker else ""),
                       # WHOM THE SPEAKER'S MOOD CAME FROM, per path, off the log (ledger.raised_by): the
                       # balance meets that person at the mood in full; `current.targets` clears at rest.
                       "raised_by": led.raised_by(run_id, speaker),
                       # WHEN EACH PATH WAS LAST READ and the speaker's last committed beat, off the
                       # log: the descent signal's fuel (rungs.descending, the redesign's gate 3).
                       "last_read_turn": led.last_read_turn(run_id, speaker),
                       "last_turn": led.last_turn(run_id, speaker),
                       "recent": [l["action"] for l in _seen[-2:]],
                       "props": cfg.get("props") or [],
                       # WHO IS BODILY HERE. Shrinks on exit, so it is always "right now". Supplying
                       # it is what turns on the referenced/present distinction: anyone the event
                       # text names who is NOT on this list was spoken of, not seen. Omit the key
                       # (scripts/direct.py does) and every named entity reads present, as before.
                       "present": list(present),
                       # THE DIRECTOR STAGES THE SCENE. This read the acting character's own
                       # sheet, so a cfg staged at one place handed its cast the description
                       # of another — measured 2026-08-29: a scene declared at the fold
                       # delivered loc.mill to both actors while the prose described a
                       # hillside at dusk. The cfg value reached only the pre-flight law
                       # check, itself behind an `if _act:` guard most scenes never set.
                       # Falls back to the sheet, so a cfg with no location is unchanged.
                       "location": cfg.get("location") or a["char"]["current"].get("location")}
        if "tells" in _sys:                       # the signs this speaker caught become percepts (gate tells)
            scene_slice["tells_noticed"] = [t["quote"] for t in _tells_noticed]
        # THE FENCE (2026-09-11): what is established about who and what is here, read from the
        # chronicle as of this turn, so the actor may invent beyond it and not against it.
        _subjects = sorted({x for x in list(present) + [scene_slice.get("location") or "", scene_target or ""] if x})
        _established = _read_api.established(led.con, run_id, _subjects, as_of=turn_no).rows if _subjects else []
        # Same four decay arguments as direct.py's run_turn — see the comment there.
        # Without them every recall in a cast scene ran at turn 0 with no history.
        packet = assemble(a["char"], world, scene_slice, a["affect"],
                          a["char"]["current"]["condition"],
                          prev_affect=led.previous_affect(run_id, speaker, turn_no),
                          current_turn=turn_no,
                          established=_established,
                          # WHAT HAS HAPPENED HERE (2026-09-22): this speaker's own witnessed facts
                          # of the run so far. `before_turn=turn_no` excludes the beat being
                          # composed, which does not exist yet.
                          facts=_scene_facts.facts_for(led.con, run_id, speaker, before_turn=turn_no),
                          # WHO IS HURT, as this speaker knows it (gate injuries; only when the book runs it):
                          # what they saw happen and their own sheet's, each aged on the clock.
                          injuries=(_injuries.for_actor(led.con, run_id, speaker, a["char"], turn_no)
                                    if "injuries" in _sys else None),
                          relationships=a["char"]["current"].get("relationships", {}),
                          recall_history=_belief_decay.fold_recall_history(
                              led.con, run_id, speaker),
                          elapsed=_clock.elapsed_days_since(led.con, run_id, turn_no),
                          # the room's subtle cues dim with the mind, as a speaker's tells do (gate tired-lexicon)
                          tired="condition_flow" in _sys)
        # name hygiene rides in build_turn_messages — mask every name this speaker never acquired;
        # faithful_turn REGENERATES on any latent name-leak the mask couldn't stop, before we commit.
        # seed = seed_base*1000 + beat. It used to be the bare beat index, which made the seed a pure
        # function of the beat: two runs of one cfg drew the identical sequence and came back identical
        # (measured — runs …1787380588 / …1787385137 match on every turn; …1787381033 / …1787381616
        # share a 7-turn prefix). K "replicates" were K=1 repeated K times. Base 0 reproduces the old
        # sequence exactly, so every committed run stays comparable.
        if "tells" in _sys:                    # what this speaker was not shown, and what they caught (gate tells)
            packet["manifest"]["tells"] = {"hidden": _tells_hidden, "noticed": _tells_noticed}
        if "injuries" in _sys:                 # who this speaker was told is hurt, and how it reads (gate injuries)
            packet["manifest"]["injuries"] = ["%s:%s" % (r["who"], r["stage"]) for r in packet["volatile"]["injuries"]]
        if _systems.declared(world):          # the set this beat ran, for the replay; absent = the defaults
            packet["manifest"]["systems"] = sorted(_sys)
        rels = a["char"]["current"].get("relationships", {})
        # THE ACT SEAM (docs/orchestration.md seam 1). Outbound: emit exactly the messages the
        # engine would have sent, for the actor SALIENCE chose, and stop — the caller acts the beat
        # elsewhere and returns it via --turn-json. scene.py had neither half, which is the stated
        # reason character-simulator could not act in a multi-actor scene (direct.py:run_turn).
        if prompt_only:
            # THE RUNG BLOCK RIDES THE ACT SEAM TOO. The live path below reaches
            # direct.faithful_turn -> llm_turn -> build_turn_messages, which passes
            # rung_direction; a prompt_only branch that omitted it would emit a strictly
            # SMALLER prompt than the engine would have sent, which is the one thing this
            # seam promises not to do. Same two-call-site bug the seam shipped with on
            # 2026-09-08, one file over.
            print(json.dumps(build_turn_messages(packet, event_text, a["temperament"], rels,
                                                 acts=_law_acts,
                                                 rung_direction=direct.rung_direction(
                                                     packet, brief=a.get("drive", ""),
                                                     model=model, stub=stub)),
                             indent=2))
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
                                        brief=a.get("drive", ""),
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
        # THE SEATS (Phase 3, wired 2026-09-11 — docs/emotion-arithmetic.md section 5 steps 1-2).
        # Live: the EVENT seat rates the act (dimensions, durability, subject, social) and the
        # EMOTION seat reads the interior (readings, lands_on); the actor's own self-tags are the
        # --stub double and the fallback when a seat refuses (recorded on the turn's validation).
        # Both run on the frontier model through scripts/provider.py — owner: no local models here.
        # `_lands` is None until the emotion seat ANSWERS: None means no seat (--stub, or a refusal)
        # and keeps the floor's counterfactual salience whole; a real list -- even [] -- is the seat's
        # judgment and prunes whoever it left out (gate lands-on-to-floor, 2026-09-19).
        _readings, _lands, _seat_notes = [], None, []
        _seat_answered = False
        if not stub:
            try:
                # ATTRIBUTION PRECEDENCE (2026-09-19, gate seat-attribution): the seat's word, when it
                # answers, wins; the actor's own tags.attribution self-tag is the stub double / the
                # refusal fallback below, never a second vote.
                tags = normalise_dimensions(appraiser.read_event(
                    str(turn.get("action", "")), _provider.seat_model(), led=led, run_id=run_id, turn=turn_no,
                    scene=cfg.get("name"), moment=event_text, present=list(present),
                    actor=names.get(speaker, speaker), target=str(turn.get("addressee", "") or ""),
                    attachments=attachments.names_for(world), exertion="body" in _sys,
                    tells="tells" in _sys, injuries="injuries" in _sys))
                _seat_answered = True
                # THE SUMMARY IS THE ACTOR'S (gate wounds-and-memory-inputs, 2026-09-22): the seat rates
                # and never writes one, and lived memory is built from it.
                tags = acquisition.with_actor_summary(tags, turn.get("tags"))
            except _SeatRefusal as _e:
                _seat_notes.append("event seat refused: %s" % str(_e)[:120])
                tags = normalise_dimensions(turn["tags"] if isinstance(turn.get("tags"), dict) else {"dimensions": {}})
            try:
                _readings, _lands, _conf, _missing = appraiser.read_emotion(
                    str(turn.get("action", "")), str(turn.get("thought", "")), _provider.seat_model(),
                    led=led, run_id=run_id, turn=turn_no, scene=cfg.get("name"), moment=event_text,
                    present=list(present), me=speaker, percepts=packet["volatile"]["percepts"])
                if _missing:
                    _seat_notes.append("concepts the registry lacks: %s" % ", ".join(_missing))
            except _SeatRefusal as _e:
                _seat_notes.append("emotion seat refused: %s" % str(_e)[:120])
                _readings = []
        else:
            tags = normalise_dimensions(
                turn["tags"] if isinstance(turn.get("tags"), dict) else {"dimensions": {}})
        # THE READER'S WORD ONLY (owner ruling C3b2, gate body-exertion): the event seat rates exertion; an
        # actor's own tags - the stub double, the refusal fallback - never carry it into the log.
        if "body" in _sys and not _seat_answered:
            tags = {k: v for k, v in tags.items() if k != "exertion"}
        # THE SEAT'S OBJECT IS THE EVENT'S SUBJECT when it names a person (bond-arithmetic.md s5). On a
        # seat-rated beat the tags carry no `subject` (that key is the actor's own self-report), so
        # until 2026-09-17 resolve_subject fell to rule 3 — "the one other party present" — on every
        # two-hander and to None on every three-hander, and received / the second order / debt went
        # dark. The actor's `subject` stays as the fallback for the stub and for self-tagged beats.
        target, tgroup = resolve_subject(packet["volatile"]["edges"], gi,
                                         tags.get("object") or tags.get("subject"),
                                         referenced_ids(packet["volatile"]["percepts"]))
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
        _before_targets = dict(a.get("targets") or {})
        # RULES 1/3/4 HERE; RULE 5 (a path back at rest clears its bind) AFTER THE RECEIPT, on the
        # float that ENDED the beat — clearing on the pre-receipt float dropped every fresh bind on
        # a resting path (found 2026-09-11 by the read-along stub).
        if _readings:                                        # Phase 3: aboutness from the readings
            a["targets"] = _targets.bind_readings(_before_targets, _readings, me=speaker)
        else:
            a["targets"] = retarget(_before_targets, applied, me=speaker)
        a["char"]["current"]["targets"] = dict(a["targets"])
        # THE CHANGE, NOT THE MAP — see the twin comment in scripts/direct.py. A dropped bind rides
        # as a release row or un-binding is not replayable.
        target_binds = _targets.binds_from(_before_targets, a["targets"])
        # DECAY FIRST, THEN THE RECEIPT — the spec's beat order (docs/emotion-arithmetic.md
        # section 8; the twin comment in scripts/direct.py has the measurement). The beat's
        # minutes pass, then the reading lands on what is left.
        # GATE THREE (2026-09-11). Presence for the receipt: the people on the roster, plus the
        # concept this beat names (a concept is "here" when the beat is about it). Decay ran on
        # what the paths were about DURING the minutes that passed (the binds before this beat);
        # the receipt uses the binds this beat made. Repetition counts consecutive prior beats
        # about the same thing from the log — nothing is stored for it.
        _here = set(present) | ({str(applied.get("target"))} if _concepts.looks_like_concept(applied.get("target")) else set())
        rested = decay(a["affect"], a["temperament"], a["profile"], elapsed=per_beat,
                       targets=_before_targets, present=_here)
        # STEP 4, THE ROOM'S MINUTES (gate non-speaker-decay, 2026-09-22; emotion-arithmetic.md s5):
        # every OTHER present character decays over the same minutes, on their own binds, decay only.
        # Computed here, committed with the turn, and applied to the room once the commit holds -
        # before the floor reads the room. The manifest records the cause so the mood is re-derivable.
        _bystanders = _passage.bystanders({i: actors[i] for i in present}, speaker, per_beat, _here)
        packet["manifest"]["decay"] = {"minutes": per_beat, "here": sorted(_here), "bystanders": sorted(_bystanders)}
        _abouts = {str(t) for t in a["targets"].values() if t}
        _repeats = {ab: _targets.repeat_count(led.con, run_id, speaker, ab, before_turn=turn_no) for ab in _abouts}
        if _readings:                                        # Phase 3: the receipt from readings
            a["affect"], impact = receive(rested, _readings, a["profile"], targets=a["targets"],
                                          repeats=_repeats, present=_here)
        else:
            a["affect"] = appraise(rested, applied, a["profile"], targets=a["targets"],
                                   repeats=_repeats, present=_here)
            impact = sum(abs(a["affect"][p] - rested[p]) for p in PATHS)
        _heights = {}
        for _r in _readings:                                 # what the seat saw, per path, for arc + wounds
            _heights[_r.path] = max(_heights.get(_r.path, 0.0), rungs.height_of(_r.path, rungs.index_of(_r.path, _r.rung)))
        # THE CONDITION MOVES (gate condition-flow; only when the book runs `condition_flow`): the beat's
        # minutes cost every present character and its impact costs the speaker; the load reads the mood each
        # one ends the beat on. Computed here, committed with the turn, applied once the arc has read the
        # condition the beat MET.
        _cond_next = {}
        if "condition_flow" in _sys:
            # THE BODY (gate body-exertion): each spender's waking minutes weighed against their own strength,
            # and the speaker's act priced from the reader's exertion word
            # AN INJURY WEAKENS THE BODY WHILE IT HEALS (gate injury-weakens): the worst of each one's own, before now
            _cap = {c: (_body.capacity(actors[c]["char"], _injuries.weakening(led.con, run_id, c, actors[c]["char"], turn_no)
                                       if "injuries" in _sys else 0) if "body" in _sys else 1.0)
                    for c in [speaker] + list(_bystanders)}
            _cond_next[speaker] = _condition.spend(a["char"]["current"]["condition"], per_beat, impact, a["affect"],
                                                   1.0 / _cap[speaker])
            if "body" in _sys:
                _cond_next[speaker] = _body.exert(_cond_next[speaker], tags.get("exertion"), per_beat, _cap[speaker])
            for _b, _aff in _bystanders.items():
                _cond_next[_b] = _condition.spend(actors[_b]["char"]["current"]["condition"], per_beat, 0.0, _aff,
                                                  1.0 / _cap[_b])
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
            [RelationshipDelta(perceiver=wid, target=speaker, axis=ax, delta=d, order="first",
                               object=str(applied.get("object") or ""))
             for wid, deltas, _v, _c in bond_moves for ax, d in sorted(deltas.items())]
            + [RelationshipDelta(perceiver=wid, target=speaker, axis=ax, delta=d, order="second",
                                 object=str(applied.get("object") or ""))
               for wid, _d, view, _c in bond_moves for ax, d in sorted((view or {}).items())])
        # A CLIFF MOVES THE REST (bond-arithmetic.md s6, gate 4): an append-only row riding this
        # turn, so drift never heals what was unforgivable. Computed here, applied at the commit.
        rest_rows = []
        for wid, deltas, _v, cliffs in bond_moves:
            if cliffs:
                _after = bonds.apply_deltas(actors[wid]["char"]["current"].get("relationships", {}).get(speaker, {}), deltas)
                _cur = bond_rest.resolve(bond_rest.rows_for(led.con, run_id, wid), actors[wid]["char"]["baseline"].get("relationship_priors", {}), speaker)
                rest_rows += bond_rest.cliff_rows(wid, speaker, _after, cliffs, _cur)
        # THE ACCOUNT MOVES ON A TRANSFER (s6, 2026-09-18): the seat reports what changed hands and on
        # what terms; `bonds.debt_postings` prices it once per pair from the words and the accounts —
        # never from a verdict. One row per posting, `cause` = the thing, applied after the commit.
        _accounts = {i: {t: float((e or {}).get("debt", 0.0) or 0.0)
                         for t, e in (actors[i]["char"]["current"].get("relationships") or {}).items() if isinstance(e, dict)}
                     for i in present}
        _posts = bonds.debt_postings(applied, speaker, _accounts, present=list(present))
        for _p, _t, _entry, _d, _cause in _posts:
            rel_deltas.append(RelationshipDelta(perceiver=_p, target=_t, axis="debt", delta=_d, order="first",
                                                object=str(applied.get("object") or ""), cause=_cause))

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
        if _subj and "attitude" in _sys:
            for _prim, _d in toward.observe(applied.get("dimensions") or {}).items():
                toward_deltas.append(TowardDelta(perceiver=speaker, target=str(_subj),
                                                 primary=_prim, delta=_d, source=event_text[:200]))
        # THE SECOND FEED (gate toward-from-readings, 2026-09-11): the emotion seat's PERSON-bound
        # readings go to the person they are about, at the reading's own vector. Before this line
        # "anger, about cobb" made the character short with everyone and moved nothing toward Cobb.
        # ATTITUDE (the redesign's gate 1, 2026-09-12): the reading's vector x the connection
        # multiplier x the durability gate — a durable beat in full, a passing one at a fraction.
        _durable = str(applied.get("durability") or "").lower() == "durable"
        for _who, _path, _d in (toward.observe_readings(_readings, me=speaker, profile=a["profile"],
                                                        durable=_durable) if "attitude" in _sys else ()):
            toward_deltas.append(TowardDelta(perceiver=speaker, target=str(_who), primary=_path,
                                             delta=_d, source=str(turn.get("action", ""))[:200]))
        # ONE ROW PER (perceiver, target, path) PER TURN — the table's UNIQUE contract. The two feeds
        # can price the same person on the same path in one beat; summed here, never side by side
        # (the first beat with both feeds live rolled back on exactly that, 2026-09-11).
        toward_deltas = toward.coalesce(toward_deltas)
        _res = arc.derive_resilience(a["char"], a["char"]["current"].get("condition", {}))
        _wounds = a["char"]["baseline"].get("wounds") or []           # engine wounds (gate three)
        wound_deltas = []
        _cue = {"about": applied.get("target"), "surfaces": packet["manifest"].get("surfaces") or [],
                "heights": _heights}
        for _w in _wounds:
            if not isinstance(_w, dict) or not str(_w.get("id", "")).strip():
                continue
            # the identity route sees the wound's OWN concept when a reading on its path named it
            _cue_w = dict(_cue, about=wound.about_for(_w, _readings) or _cue["about"])
            _d = wound.trial(_w, applied.get("dimensions") or {}, _res, _cue_w)
            if _d:
                wound_deltas.append(WoundDelta(char_id=speaker, wound_id=str(_w["id"]),
                                               delta=_d, kind="event", source=event_text[:200]))
        # THE MINT (gate three): a durable beat the seat read at one of a path's top rungs, that
        # path bound to a concept, scars at the reading's height. Computed here so the rows ride the turn's own transaction; folded after.
        _durable = (applied.get("durability") == "durable"
                    or any(float(v) >= arc._DURABLE_DIM for v in (applied.get("dimensions") or {}).values()))
        wound_mints = wound.mint(a["char"], _heights, a["targets"], _durable,
                                 surfaces=packet["manifest"].get("surfaces") or [],
                                 text=event_text, turn=turn_no) if "wounds" in _sys else []
        # RULE 5 LAST — see scripts/readalong.py: it decides what carries forward, after the mint.
        a["targets"] = _targets.bind_readings(a["targets"], [], temperament=a["temperament"], affect=a["affect"])
        a["char"]["current"]["targets"] = dict(a["targets"])
        target_binds = _targets.binds_from(_before_targets, a["targets"])
        led.append_turn(TurnCommit(
            run_id=run_id, turn=turn_no, actor=speaker,
            thought=str(turn["thought"]), action=str(turn["action"]),
            tags=tags if isinstance(tags, dict) else {}, affect=dict(a["affect"]),
            condition=dict(_cond_next.get(speaker) or a["char"]["current"].get("condition", {})), validation=validation,
            events=_law_events(led, run_id, world, chars, turn, speaker,
                               location=cfg.get("location"), tick=turn_no) + [
                    Event(type=str(tags.get("type", "mundane")),
                          payload={"text": event_text, "dimensions": tags.get("dimensions", {}),
                                   "durability": tags.get("durability", "transient"),
                                   "subject": target, "subject_group": tgroup,
                                   # v27: what the seat said the act was ABOUT and SHOWED, so the
                                   # log carries the bond tier's cause beside the emotion tier's
                                   "object": str(applied.get("object") or ""),
                                   "showed": dict(applied.get("showed") or {}),
                                   "quotes": dict(applied.get("quotes") or {}),
                                   "transfers": list(applied.get("transfers") or []),
                                   "told": list(applied.get("told") or []),
                                   # WHO WAS HURT (gate injuries): the reader's marks only - never an actor's own
                                   # tags - and the key only for a book that runs the system.
                                   **({"injuries": list(applied.get("injuries") or []) if _seat_answered else []}
                                      if "injuries" in _sys else {})},
                          target=target,          # THE SUBJECT. Omitted at every Event site until 2026-08-30, so
                                                  # ledger._project's `victim = ev['target'] or ev['actor']` always
                                                  # fell through and a terminal harm marked the ACTOR dead, never the
                                                  # person harmed; the betray/bond branch was unreachable entirely.
                          actor=speaker)],
            manifest=packet["manifest"], recall=packet["recall_refs"], rel_deltas=rel_deltas,
            wound_deltas=wound_deltas, toward_deltas=toward_deltas, wound_mints=wound_mints,
            utterances=claims.spoken(str(turn["action"])), target_binds=target_binds,
            readings=list(_readings), lands_on=list(_lands or []), rest_rows=rest_rows,
            bystanders={_b: {"affect": dict(_aff), "condition": dict(_cond_next.get(_b) or actors[_b]["char"]["current"].get("condition", {}))}
                        for _b, _aff in _bystanders.items()}))
        if _seat_notes:
            print("   SEATS  : " + " | ".join(_seat_notes))
        # the commit held, so the in-memory sheets may now follow the log
        for _b, _aff in _bystanders.items():          # step 4 lands: the room aged with the speaker
            actors[_b]["affect"] = dict(_aff)
        if toward_deltas:
            # THE FOLD, NOT THE AUTHORED-PLUS-DELTAS REPLAY: that one erased this scene's opening fade at
            # its first beat (gate erosion-derived-at-replay).
            _passage.fold_toward(led.con, run_id, speaker, a["char"])
            _seen = sorted({t.target for t in toward_deltas})
            print("   TOWARD : %s  %s" % (names.get(speaker, speaker), ", ".join(
                "%s %s" % (names.get(w, w), " ".join("%s%+0.3f" % (k, v) for k, v in
                                                     sorted((a["char"]["current"]["toward"].get(w) or {}).items())))
                for w in _seen)))
        if wound_mints:
            for _m in wound_mints:
                print("   SCAR   : %s  %s on %s at %.2f — %s" % (names.get(speaker, speaker), _m["concept"],
                                                              _m["path"], _m["intensity"], _m["text"][:60]))
        if wound_deltas or wound_mints:
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
            _passage.fold_wounds(led.con, run_id, speaker, a["char"])   # mints, deltas AND the fade, in log order
            _wounds = a["char"]["baseline"].get("wounds") or []
            a["profile"] = build_profile(a["char"])          # the held registry moved
            for _wd in wound_deltas:
                _now = next((float(_w["intensity"]) for _w in _wounds
                             if str(_w.get("id", "")) == _wd.wound_id), None)
                print("   WOUND  : %s  %s %+0.4f -> %.3f"
                      % (names.get(speaker, speaker), _wd.wound_id, _wd.delta, _now))

        # THE BOND TIER IS LIVE ON SEAT OUTPUT since 2026-09-17 (bond-arithmetic.md s4: the seat's
        # `showed` is priced at the parse seam) and THE LAW IS bond-arithmetic.md s6 since gate 4 (the
        # signed, level-anchored form; the ledger rule on live scenes lifted when that gate archived).
        # A read that moved nothing is still printed, so the silence of a witness who did not notice,
        # or a two-hander with no third party, is visible in the log; a beat with no read says so too.
        if not bond_moves and isinstance(applied.get("showed"), dict) and applied.get("showed"):
            print("   BOND   : no move — object %s, showed %s (below the overtness gate, or nobody else present)"
                  % (applied.get("object") or "-",
                     ", ".join("%s %s" % (k, v if isinstance(v, str) else _act_word_near(k, v))
                               for k, v in sorted(applied["showed"].items()))))
        elif not bond_moves and not applied.get("showed"):
            print("   BOND   : no act — the seat named no showed%s" % (" (stub)" if stub else ""))
        for wid, deltas, view, cliffs in bond_moves:
            rels = actors[wid]["char"]["current"].setdefault("relationships", {})
            # born whole at the stranger's rest (bond_rest.whole) — the same edge the law priced
            # the deltas from in floor.bond_moves, so what is stored is what the fold rebuilds
            edge = bond_rest.whole(rels.get(speaker), actors[wid]["char"]["baseline"].get("relationship_priors", {}))
            if deltas:
                edge = bonds.apply_deltas(edge, deltas)
            if view:
                edge = bonds.apply_reflection(edge, view)
            rels[speaker] = edge
            _obj_key = str(applied.get("object") or "")
            print("   BOND   : %s -> %s  %s%s%s" % (
                names.get(wid, wid), names.get(speaker, speaker),
                "  ".join("%s %+0.3f" % (ax, d) for ax, d in sorted(deltas.items())),
                ("   | reads them as: " + "  ".join("%s %+0.3f" % (ax, d)
                                                    for ax, d in sorted(view.items()))) if view else "",
                ("  (stake %.2f: %s)" % (bonds.stake_of(wid, _obj_key, rels, held=connection.held_map(actors[wid]["char"])), _obj_key))
                if _obj_key.startswith(attachments.LOC) or _obj_key.startswith(attachments.GRP) else ""))
            for ax in cliffs:
                print("   CLIFF  : %s -> %s  %s rests at %.3f from here" % (names.get(wid, wid), names.get(speaker, speaker), ax, edge.get(ax, 0.0)))
        for _p, _t, _entry, _d, _cause in _posts:
            _prels = actors[_p]["char"]["current"].setdefault("relationships", {})
            # a posting on an edge she does not yet hold births it whole at the stranger's rest
            _prels[_t] = bonds.apply_deltas(bond_rest.whole(_prels.get(_t), actors[_p]["char"]["baseline"].get("relationship_priors", {})), {"debt": _d})
            print("   BOND   : %s %s %s  debt %+0.3f  — %s" % (
                names.get(_p, _p), "owes" if _entry == "gave" else "repaid", names.get(_t, _t), _d, _cause or "(unnamed)"))
        # arc: a durable beat moves the speaker's baseline; persist + evolve them for the next beat
        diff = (arc.assess(applied, impact, a["char"], a["char"]["current"]["condition"], heights=_heights)
                if "arc" in _sys else None)
        if diff:
            a["char"] = arc.apply(a["char"], diff)
            led.append_arc_diff(run_id, speaker, turn_no, diff)
            a["profile"] = build_profile(a["char"])
            a["temperament"] = a["char"]["baseline"]["temperament"]
        for _c, _cd in _cond_next.items():                  # the beat's cost lands (condition flow)
            actors[_c]["char"]["current"]["condition"] = _cd
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
        # DURABILITY IS PRINTED (2026-09-16). It gates attitude accrual, wound minting and the arc
        # tier, and until this line it reached the log only through the database — a seat marking
        # half a scene durable was invisible for four performances. direct.py has printed it since
        # its TAGS line existed; this one did not.
        print("   TAGS   : %s %s [%s]  subj=%s  addressed=%s  conf=%.2f%s%s" % (
            tags.get("type", "?"), _shown, applied.get("durability", "?"), target or "-", addressee or "-",
            validation["confidence"],
            ("  DROPPED %s" % _dropped) if _dropped else "",
            ("  flags: %s" % "; ".join(render_flag(f) for f in validation["flags"]))
            if validation["flags"] else ""))
        print("   now    : %s" % direct.rung_summary(a["affect"]))
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
            actors, present, speaker, applied, target, tgroup, addressee, beat, lands_on=_lands)
        # THE SAME MEMBERSHIP TEST next_speaker JUST RAN (gate lands-on-to-floor, 2026-09-19),
        # mirrored here for the trace only: next_speaker does not hand back a per-listener
        # `landed` flag, so the print recomputes it from the same `_lands`/`norm_id` it was
        # actually called with -- never from a truthiness check on `_lands`, since `[]` (a seat
        # reply naming nobody) prunes everyone exactly as a real list would.
        _lands_norm = None if _lands is None else {norm_id(x) for x in _lands}
        if ended_because == "empty":
            ended = "empty"
            break
        if ended_because == "lull":
            print("\n== lull — no one is moved enough to answer (max urge %.3f, floor %.3f). "
                  "The scene settles. ==" % (urges[_floor.leader(urges)][0], _FLOOR_THRESHOLD))
            print("   urges  : %s   [spoken to: %s]" % (
                "  ".join("%s=%.3f%s%s" % (
                    k, v[0], "+addr" if bool(addressee) and norm_id(addressee) == norm_id(k) else "",
                    " ~unreached" if _lands_norm is not None and norm_id(k) not in _lands_norm else "")
                          for k, v in urges.items()),
                addressee or "no one — the addressed bonus (+%.2f) applied to nobody" % _ADDRESSED_BONUS))
            ended = "lull"
            break
        print("   urges  : %s  -> floor: %s\n" % (
            "  ".join("%s=%.2f[sal%.2f dis%.2f]%s" % (
                k, v[0], v[1], v[2], " ~unreached" if _lands_norm is not None and norm_id(k) not in _lands_norm else "")
                      for k, v in urges.items()),
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


def _keeper_runs(stub, keeper, keeper_off):
    """Should THIS invocation call the canon gate, from the three flags alone — whether any turns
    were actually committed is checked separately at the call site, the same way it always was.

    DEFAULT ON for a live run since 2026-09-19 (owner decision D1, gate lore-licence-visible):
    `--no-keeper` is the only opt-out. `--keeper` is kept as an ACCEPTED flag rather than removed —
    on a live run it is now a no-op (the default already covers it), and under `--stub` it still
    forces the gate to run exactly as it always did, so an operator who explicitly asks for it under
    `--stub` still gets the stub keeper's own report ("noticing pass skipped") rather than silence.
    Bare `--stub` (nobody asked) still runs nothing, unchanged. A free function rather than an
    inline expression so `tests/test_driver_main.py` can pin the truth table without a real model.
    """
    return not keeper_off and (keeper or not stub)


def _report_lore(led, run_id, keeper_ran, stub):
    """Print the lore licence's debt after the run: sayings `claims.unextracted` says the fence
    still cannot see. The trap, in `scripts/keeper.py`'s own words: an utterance lands at commit
    WITHOUT extracts and stays that way until the keeper's noticing pass reads it — a run that never
    calls the gate (or calls it under `--stub`, which asks nothing) accumulates sayings invisible to
    `claims.about` with nothing saying so out loud. This is that line, unconditionally, every run —
    the debt was there before this gate; only the reporting is new."""
    debt = claims.unextracted(led.con, run_id)
    if not debt["count"]:
        print("lore: every saying has been noticed")
    elif not keeper_ran:
        print("lore: %d saying(s) since turn %d await the keeper — run without --no-keeper, or "
              "scripts/keeper.py --prompt-only" % (debt["count"], debt["first_turn"]))
    elif stub:
        print("lore: %d saying(s) still unextracted (the keeper asked nothing under --stub)"
              % debt["count"])
    else:
        print("lore: %d saying(s) still unextracted after the keeper's pass" % debt["count"])


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
    ap.add_argument("--keeper", action="store_true",
                    help="the keeper of truth rules on what was claimed at the canon gate — this is "
                         "the DEFAULT for a non-stub run since 2026-09-19 (owner decision D1), so "
                         "the flag is accepted for compatibility rather than required; under --stub "
                         "it still forces the gate to run (it rules nothing and prints the "
                         "contested claims, as always). See --no-keeper to opt out")
    ap.add_argument("--no-keeper", action="store_true", dest="keeper_off",
                    help="skip the canon gate even on a non-stub run. The lore licence's debt — "
                         "sayings the fence cannot see until the keeper notices them — is left "
                         "unresolved; the run's closing 'lore:' line says how much")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--budget", type=int, default=14, help="max beats")
    ap.add_argument("--seed-base", type=int, default=0, dest="seed_base",
                    help="sampling seed base; per-beat seed = base*1000 + beat. Vary it (0..K-1) to draw a "
                         "REAL K-sample: at a fixed base two runs of one cfg reproduce byte-identically. "
                         "Default 0 reproduces every run committed before this flag existed")
    ap.add_argument("--db", default=None, help="chronicle db path (default <vault>/runs/<book>.db)")
    ap.add_argument("--resume", default=None, help="run_id to continue — a later scene in the same chronicle")
    ap.add_argument("--scene", default=None, help="a director-authored scene cfg JSON (default: the built-in DEFAULT_SCENE fixture)")
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
    # WHAT THE SHEETS AUTHORED, stamped before anything moves it: the fade folds rebuild from it
    # (gate erosion-derived-at-replay, 2026-09-22).
    for _ch in chars.values():
        _passage.stamp_authored(_ch)
    book_name = books.slug(book_dir)
    try:                                          # the chronicle lives WITH the book — enforced,
        default_db = books.assert_db_for_book(book_dir, args.db)   # not merely defaulted
    except books.BookError as e:
        raise SystemExit(str(e))
    led = Ledger(default_db)
    scene_cfg = load_scene_cfg(args.scene) if args.scene else DEFAULT_SCENE    # director-authored scene, or the default fixture
    cast_ids = [c["id"] for c in scene_cfg["cast"]]

    # THE CAST MUST BE IN THE BOOK, and this refuses instead of dying nine lines later on a KeyError.
    #
    # CLAUDE.md records that an entire scene from a private novel once served as this file's DEFAULT
    # fixture, so every no-argument run played someone's book. The content was scrubbed; the SHAPE
    # survived — the default is still a hardcoded scene (DEFAULT_SCENE, cast ruth/dev/agnes), and `--book
    # <any other book>` with no `--scene` indexed `chars[cid]` for people that book has never heard of.
    # Measured 2026-09-02, the first time either driver's main() was ever run by a test: a `KeyError`
    # on the default fixture's first cast id before a single turn.
    #
    # It REFUSES rather than substituting the book's own cast: DEFAULT_SCENE's situation text names Ruth,
    # Dev, Agnes and Ruth's nephew in prose, so pairing it with a different cast would produce a
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
            ch = _passage.fold_arc(led.con, run_id, cid, ch)            # diffs AND each opening's fade, in order
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
            # A pre-v28 run gets its authored rest rows at the resume turn (idempotent: a v28 run
            # writes nothing); its winters before this replay toward the stranger's rest, which is
            # what they were computed against (bond_rest.py docstring).
            bond_rest.seed(led.con, run_id, state["turn"] + 1, cid, ch["current"].get("relationships") or {})
            attachments.seed(led.con, run_id, state["turn"] + 1, cid, ch["current"].get("attachments") or {})
            # ORDERED REHYDRATE: rests, holds, declarations and movements interleaved in the order they
            # happened, because drift and deltas do not commute.
            bond_rest.rehydrate(ch["current"].setdefault("relationships", {}),
                                ch["baseline"].get("relationship_priors", {}),
                                led.timeline_for(run_id, cid),
                                attachments=ch["current"].setdefault("attachments", {}))
            if _moves:                       # OPERATOR output, not the prompt — rule 5 is the prompt
                print("   %s: refolded %d edge movement(s) toward %s"
                      % (cid, len(_moves), ", ".join(sorted({m[0] for m in _moves}))))
            # THE WOUND TIER. Same shape as the edge refold above, and the same failure if it is
            # omitted: a resumed cast's wounds silently return to SHEET strength, so a phobia the
            # character spent a whole book walking into hits exactly as hard on the next page.
            # `replay_wound_deltas` stamps `_authored_intensity` BEFORE applying anything — that
            # ordering is what keeps `levers.scale_to_wounds` scaling against the AUTHORED value
            # rather than the already-healed one.
            # ABOUTNESS — the tier this block did not replay until 2026-09-06. Wiring one driver
            # and not the other is indistinguishable from working until someone runs the other path.
            _tbinds = _targets.binds_for(led.con, run_id, cid)
            _targets.replay(ch, _tbinds)
            if _tbinds:
                print("   %s: refolded %d aboutness bind(s) on %s"
                      % (cid, len(_tbinds), ", ".join(sorted(ch["current"].get("targets") or {})) or "nothing"))
            _tmoves = led.toward_deltas_for(run_id, cid)
            _passage.fold_toward(led.con, run_id, cid, ch)
            if _tmoves:
                print("   %s: refolded %d micro movement(s) toward %d person(s)"
                      % (cid, len(_tmoves), len({m[0] for m in _tmoves})))
            _wmoves = led.wound_deltas_for(run_id, cid)
            _passage.fold_wounds(led.con, run_id, cid, ch)   # mints, deltas and the fade, in log order
            if _wmoves:                      # OPERATOR output, not the prompt — rule 5 is the prompt
                print("   %s: refolded %d wound movement(s) on %s"
                      % (cid, len(_wmoves), ", ".join(sorted({m[0] for m in _wmoves}))))
            # mood AND condition, one restore shared with the chair (gate resume-and-parity)
            _passage.restore_latest(ch, led.latest_affect(run_id, cid))
            chars[cid] = ch
        start_turn = state["turn"] + 1
        print("resumed %s at turn %d (determinism OK)" % (run_id, state["turn"]))
        # THE MOOD, RE-DERIVED (gate mood-from-readings, 2026-09-22): the cache this resume just restored
        # from, measured against the log it should derive from. REPORTED, never repaired - the restore
        # above keeps the SAVED mood by the owner's ruling (2026-09-22, "Keep the mood": a resume is not a
        # story event, so it must not change how anyone feels); this line is the per-resume check on it.
        from src.engine import bible as _bible, mood_fold as _mood_fold
        _pinned = _bible.for_run(led.con, run_id)
        if _pinned is None:          # the replay starts from the sheets the run pinned; a run before pinning has none
            print("   mood replay: skipped - this run pinned no bible to replay from\n")
        else:
            _md = _mood_fold.divergence(led.con, run_id, _pinned[2])
            print("   mood replay: %d of %d cached moods re-derived from the log; largest difference %s; "
                  "conditions: largest difference %s%s\n" % (
                _md["cached"] - len(_md["missing"]), _md["cached"],
                "none" if not _md["at"] or _md["largest"] <= _mood_fold.TOLERANCE else "%.1e (turn %d, %s, %s)" % (
                    (_md["largest"],) + tuple(_md["at"])),
                "none" if not _md["condition_at"] or _md["condition_largest"] <= _mood_fold.TOLERANCE
                else "%.1e (turn %d, %s, %s)" % ((_md["condition_largest"],) + tuple(_md["condition_at"])),
                "".join("\n     - %s" % n for n in _md["notes"])))
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
            # where each authored edge RESTS, as rows the fold can read back (schema v28, gate 4)
            bond_rest.seed(led.con, run_id, 0, cid, chars[cid]["current"].get("relationships") or {})
            attachments.seed(led.con, run_id, 0, cid, chars[cid]["current"].get("attachments") or {})   # what they hold (v30, gate 5)
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
            bond_rest.seed(led.con, run_id, start_turn, cid, chars[cid]["current"].get("relationships") or {})
            attachments.seed(led.con, run_id, start_turn, cid, chars[cid]["current"].get("attachments") or {})
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
    keeper_ran = _keeper_runs(args.stub, args.keeper, args.keeper_off) and next_turn > start_turn
    if keeper_ran:
        # THE CANON GATE (2026-09-11): the scene's claims are ruled on before the scene is parked.
        # `world=world` (2026-09-19, gate keeper-attachment-rubric): the third writer of a hold
        # needs the bible to check a claim's object against — see attachments.names_for.
        _keeper.canon_gate(led, run_id, start_turn, next_turn - 1, _provider.seat_model(), args.stub, world=world)
    last = record_and_park(led, run_id, scene_cfg, start_turn, next_turn, cast_ids)
    _report_lore(led, run_id, keeper_ran, args.stub)
    print("\nparked %s at turn %d — continue with: python scripts/scene.py --vault \"%s\"%s --resume %s" % (
        run_id, last, book_dir, " --stub" if args.stub else "", run_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
