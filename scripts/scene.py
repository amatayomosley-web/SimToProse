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
from src.engine import tellings as _tellings                        # noqa: E402  (what is told becomes what is known)
from src.engine import integrity                              # noqa: E402
from src.engine import claims                                 # noqa: E402  (the utterance/T2 path)
from src.engine import read_api as _read_api                  # noqa: E402  (what is established: the lore fence)
from src.engine import scene_facts as _scene_facts        # noqa: E402  (what has happened, POV-filtered)
import keeper as _keeper                                       # noqa: E402  (the ruling seat at the canon gate)
from src.engine.state import build_profile, appraise, decay, receive   # noqa: E402
from src.engine import rungs                                        # noqa: E402  (a reading's height)
from src.engine.records import RecordError as _SeatRefusal          # noqa: E402
from src.engine.errors import EngineError as _EngineError           # noqa: E402  (a failing fallback, re-raised naming the seat)
import appraiser                                                   # noqa: E402  (the two seats)
import provider as _provider                                       # noqa: E402  (the frontier-model seam)
# NOT the `decay` above — that one is state.decay, the AFFECT relaxation. This is the
# belief-decay module. The names collide, so both are only ever reached under an alias
# here; importing it bare would silently rebind the affect function.
from src.engine import decay as _belief_decay                       # noqa: E402
from src.engine import clock as _clock                              # noqa: E402
_clockmod = _clock                                                   # the minute clock; operator prints
from src.engine import presence as _presence                        # noqa: E402  (a name means one person)
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
from src.engine import contracts as _contracts                    # noqa: E402  (the author files, refused at run start)
from src.engine import replies as _replies                        # noqa: E402  (a model's reply, read into its record)
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
import scene_window as _scene_window                            # a window's reads and rows (gate window-reads)
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
# the tripwire's one line (conversation design v2 s2), added after the prompt when a move runs past floor.MOVE_WORDS
TRIPWIRE_LINE = ("That ran long. Make it one point, then stop where they would answer. Rewrite your ENTIRE reply "
                 "(same JSON shape).")

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


def _as_written(path):
    """The scene file exactly as its author wrote it - what its contract reads (`load_scene_cfg` rewrites it)."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        raise SystemExit("scene file %s cannot be read as JSON: %s" % (path, e))


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
        print(_replies.shown(["   [!] LAW CHECK FAILED for %r: %s" % (act, exc)]))   # ASCII: an act is model text, pre-commit
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
    # WHAT THE SHEETS AUTHORED, before anything below moves them (idempotent: `main` stamped them at load). The folds
    # rebuild from it after every beat, and since gate slow-tiers-run every beat with minutes is a stretch of time they
    # fold across, so a caller that hands this loop an unstamped sheet would be refused mid-scene.
    for c in cfg["cast"]:
        _passage.stamp_authored(chars[c["id"]])
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
    # state ... affinity fades faster than trust"). It was applied here at scene START only, "because a
    # beat has no duration"; beats carry minutes since 2026-09-10, and since gate slow-tiers-run
    # (2026-09-24) the opening ages the four older tiers too, and every beat below ages them again by
    # its own minutes - since gate own-timelines (2026-09-25) each character by their OWN time at the
    # opening (since they were last in a room; a first appearance, nothing) and the room at each beat.
    # ONE CLOCK, IN MINUTES (clock.py, 2026-09-10). Log this scene's reading, derive the gap since
    # the previous scene ENDED, and hand it to the four older tiers — plus emotion, the fifth. A
    # scene that lulled early last time owes its unspent `lasts` here.
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
                                        injuries="injuries" in _sys, windows=True)
    # EACH ACTOR'S VIEW OF THEIR OWN LOG (gate flashback-windows): every read of their history this scene goes
    # through it - for whom the scene is a window, their past before its time and the scene itself.
    for i in ids:
        actors[i]["view"] = _clock_result["views"][i]
    # THE NOTICE, BEFORE A BEAT IS PAID FOR: whom this scene is a window for - and, set before someone's first scene,
    # that they play from their sheet, with advice to write them a sheet for then when the gap is long (gate
    # window-before-first-scene; the owner: "Play the character sheet, if there is a large gap in time advise
    # generating a character sheet").
    from src.engine import window as _win
    for i, _v in sorted(_clock_result["windows"].items()):
        _gap = _win.sheet_gap(led.con, run_id, i, _v.at)
        print("   WINDOW : %s plays as of %s, %s - nothing this scene does reaches their present (a report follows the "
              "scene)%s" % (names.get(i, i), _clockmod.format_at(_v.at), "from their own story then" if _gap is None
                            else "from their sheet, which describes them %s later" % _win.span_words(_gap),
                            "" if _gap is None or _gap <= _win.SHEET_ADVICE_DAYS * _clockmod.MINUTES_PER_DAY else
                            "\n            that is a long way back: consider a younger %s - a character of their own, "
                            "with their own sheet and a place among the world's people (an id beginning with their "
                            "name, e.g. %s_young, named %s) - called into the scene in their place (gate "
                            "one-person-per-name: \"%s\" then means whichever is in the room)"
                            % (names.get(i, i), i.split("_")[0], names.get(i, i), names.get(i, i))))
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
    if (_clock_result["elapsed"] or 0) > 0:
        print("\n  %s minutes since the last scene ended%s — edges relaxed toward each character's"
              " resting disposition, feelings toward their rest" % (
                  int(_clock_result["elapsed"]),
                  " (+%d owed by the last scene)" % int(_clock_result["owed"]) if _clock_result["owed"] else ""))
    elif (_clock_result["elapsed"] or 0) < 0:          # gates own-timelines, flashback-windows: earlier in the story
        print("\n  set %d minutes before the last scene run ended - earlier in the story%s" % (
            int(-_clock_result["elapsed"]), "; a window for %s" % ", ".join(sorted(_clock_result["windows"]))
            if _clock_result["windows"] else "; it shares no one with it"))
    # EACH CHARACTER AGED BY THEIR OWN TIME AWAY (gates absent-age, own-timelines): name whoever was out of the room
    # longer than the scene gap, and anyone appearing for the first time, so the operator can see why one cooled more.
    if _clock_result["elapsed"] is not None:
        _gap = _clock_result["elapsed"] + _clock_result["owed"]
        _away = ["%s %d min" % (i, int(m)) for i, m in sorted(_clock_result["own"].items()) if abs(m - _gap) > 1e-9]
        _away += ["%s first appears (as the sheet describes them)" % i for i in ids if i not in _clock_result["own"]]
        if _away:
            print("  own time away: %s" % "; ".join(_away))
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
    # THE ROUND (conversation design v2 s3, gate round-loop): every call is one actor in one stance - the speaker,
    # who makes a move and says whether they keep the floor or yield it, or a listener asked after a move, who takes
    # it, puts in a word, or holds. `budget` counts committed rows; a call that commits nothing (a listener's empty
    # hold) is free, so the calls are bounded separately, at one per present person per row.
    rnd = _floor.Round(speaker)
    committed = 0
    # WHOM THE DIRECTION AIMS EACH CHARACTER AT (gate directed-addressee): the scene file's `cast[].to`, checked against
    # the cast by its contract before the run began. Absent, the actor chooses, as before.
    _directed = {str(c["id"]): str(c["to"]) for c in cfg["cast"] if c.get("to")}
    # THE WINDOW IN HAND (gate window-reads): its rows, buffered until it closes, and what closing it needs
    window, _wspk, _wstate = [], None, {"target": scene_target}
    _wctx = {"led": led, "run_id": run_id, "cfg": cfg, "world": world, "names": names, "actors": actors, "gi": gi,
             "stub": stub, "sys": _sys, "per_beat": per_beat, "state": _wstate,
             "law_events": lambda reply, who, t: _law_events(led, run_id, world, chars, reply, who,
                                                             location=cfg.get("location"), tick=t)}
    for beat in range(budget * (len(ids) + 1)):
        if committed >= budget:
            break
        stance, speaker, _flags = rnd.call
        scene_target = _wstate["target"]              # the subject the last window's reads resolved
        a = actors[speaker]
        # what this actor was thinking last, its own mind only (design v1 s4: the deliberation is carried, not restarted)
        _floor_kw = dict(_flags, stance=stance,
                         last_thought=next((b["thought"] for b in reversed(log) if b["who"] == speaker), None))
        if _directed.get(speaker) in present:         # a directed target who has left directs nothing
            _floor_kw["to"] = (_directed[speaker], names.get(_directed[speaker], _directed[speaker]))
        # THE MOMENT AS THIS SPEAKER READS IT (gate tells; only when the book runs `tells`): the signs other actors
        # let slip, marked by the event reader, are cut for a speaker who does not catch them and named for one who
        # does. Without the system every speaker reads the log whole, as before.
        _seen, _tells_hidden, _tells_noticed = ((_tells.for_listener(log, speaker,
                                                    _tells.catches(a["char"], tired="condition_flow" in _sys)))
                                                if "tells" in _sys else (log, [], []))
        event_text = _compose_event(cfg["situation"], _seen, names, me=speaker)
        # A NAME MEANS ONE PERSON (gate one-person-per-name): whoever of it is in the room, else whoever the story is
        # at, from the room as it stands and the log so far - a young Mira who walks out has walked on by then
        # (a row still in the open window is a walk-on too, before it commits: gate window-reads)
        _elsewhere = _presence.one_per_name(world.get("people"), present, chars, cfg["at_minutes"],
                                            lambda c: next((x for x in (_clockmod.first_presence(led.con, run_id, c),)
                                                            if x is not None), cfg["at_minutes"]
                                                           if any(r["who"] == c for r in window) else None))
        _world_b = _presence.world_meant(world, _elsewhere)   # what this beat's names, and the memories it writes, read
        scene_slice = {"event": {"text": event_text, "kind": "mundane"},
                       "target": scene_target,
                       # WHO THE SPEAKER IS ENGAGING (the redesign's gate 1): the last speaker, when
                       # someone else spoke last — the person this beat answers. assemble composes
                       # the played vector toward them; absent, it falls back to the subject.
                       "engaged": (log[-1]["who"] if log and log[-1]["who"] != speaker else ""),
                       # WHOM THE SPEAKER'S MOOD CAME FROM, per path, off the log (ledger.raised_by): the
                       # balance meets that person at the mood in full; `current.targets` clears at rest.
                       "raised_by": led.raised_by(run_id, speaker, a["view"]),
                       # WHEN EACH PATH WAS LAST READ and the speaker's last committed beat, off the
                       # log: the descent signal's fuel (rungs.descending, the redesign's gate 3).
                       "last_read_turn": led.last_read_turn(run_id, speaker, a["view"]),
                       "last_turn": led.last_turn(run_id, speaker, a["view"]),
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
        if _elsewhere:                            # only a book two people share a name in carries the key
            scene_slice["elsewhere"] = _elsewhere
        # THE FENCE (2026-09-11): what is established about who and what is here, read from the
        # chronicle as of this turn, so the actor may invent beyond it and not against it.
        _subjects = sorted({x for x in list(present) + [scene_slice.get("location") or "", scene_target or ""] if x})
        _established = _read_api.established(led.con, run_id, _subjects, as_of=turn_no).rows if _subjects else []
        # Same four decay arguments as direct.py's run_turn — see the comment there.
        # Without them every recall in a cast scene ran at turn 0 with no history.
        packet = assemble(a["char"], world, scene_slice, a["affect"],
                          a["char"]["current"]["condition"],
                          prev_affect=led.previous_affect(run_id, speaker, turn_no, a["view"]),
                          current_turn=turn_no,
                          established=_established,
                          # WHAT HAS HAPPENED HERE (2026-09-22): this speaker's own witnessed facts
                          # of the run so far. `before_turn=turn_no` excludes the beat being
                          # composed, which does not exist yet.
                          facts=_scene_facts.facts_for(led.con, run_id, speaker, before_turn=turn_no, view=a["view"]),
                          # WHO IS HURT, as this speaker knows it (gate injuries; only when the book runs it):
                          # what they saw happen and their own sheet's, each aged on the clock.
                          injuries=(_injuries.for_actor(led.con, run_id, speaker, a["char"], turn_no, a["view"])
                                    if "injuries" in _sys else None),
                          relationships=a["char"]["current"].get("relationships", {}),
                          recall_history=_belief_decay.fold_recall_history(
                              led.con, run_id, speaker, a["view"]),
                          # EACH MEMORY ITS OWN STORY TIME (gate memory-fades): since the beat that formed or last
                          # recalled it, to this beat's start - the time after the current beat, handed here before,
                          # is zero at the head of the log, so no memory faded in a live run. A sheet memory's, since
                          # this speaker's own story began (gate own-timelines: where they first walked on)
                          elapsed=lambda t, _now=turn_no, _me=speaker: _clock.days_since(led.con, run_id, _me, t, _now),
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
        # the names the prompt masks and the leak check reads: only the people this scene's names mean
        rels = _presence.rels_meant(a["char"]["current"].get("relationships", {}), _elsewhere)
        # THE ACT SEAM (docs/orchestration.md seam 1). Outbound: emit exactly the messages the
        # engine would have sent, for the actor SALIENCE chose, and stop — the caller acts the beat
        # elsewhere and returns it via --turn-json. scene.py had neither half, which is the stated
        # reason character-simulator could not act in a multi-actor scene (direct.py:run_turn).
        direct.COMPOSE_USAGE.clear()                 # this beat's composer calls only (gate composer-usage)
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
                                                     model=model, stub=stub), **_floor_kw),
                             indent=2))
            direct.log_compose_usage(led, run_id, turn_no, scene=cfg.get("name"))
            return turn_no
        _tripwire = None
        if supplied is not None:
            # A SUPPLIED TURN PASSES THE SAME WALLS. Shape first, then the name-leak check, then the
            # identical validate/appraise/commit path below. A re-entry that skips the wall is a
            # hole in it, and the risk does not fall because the model was a stranger's. The shape is
            # `replies.actor_reply`'s (gate actor-reply): `main` checked the file before the chronicle opened.
            turn = _replies.actor_reply(supplied, supplied=True).as_turn()
            leaks = faithfulness.check_name_leaks("%s %s" % (turn["action"], turn["thought"]), rels)
            print("  [supplied turn accepted for validation — %d char action]" % len(turn["action"]))
            supplied = None          # one supplied beat per invocation; the rest act normally
        else:
            # `information` is the snapshot's fact -> knowers map. Passing it turns the
            # faithfulness guard from name-shaped to fact-shaped: an actor stating something
            # nobody told them is regenerated, the same as a name it does not hold.
            _act_kw = dict(think=think, brief=a.get("drive", ""), seed=seed_base * 1000 + beat, acts=_law_acts,
                           relationships=rels,
                           information=(led.fold(run_id, max(turn_no - 1, 0)) or {}).get("information"),
                           char_id=speaker, vault=a["char"]["current"].get("vault"), world=world, floor=_floor_kw)
            turn, leaks = faithful_turn(packet, event_text, a["temperament"], model, stub, **_act_kw)
            # THE TRIPWIRE (design v2 s2): a move over MOVE_WORDS is drawn once more with the line; the second draw is
            # kept whatever its length, and the validation record says so. A word count flags, it never defines a move.
            _words = len(str(turn.get("action", "")).split())
            if not leaks and _words > _floor.MOVE_WORDS:
                turn, leaks = faithful_turn(packet, event_text, a["temperament"], model, stub, steer=TRIPWIRE_LINE,
                                            **_act_kw)
                _tripwire = {"words": _words, "redrawn_words": len(str(turn.get("action", "")).split())}
        direct.log_compose_usage(led, run_id, turn_no, scene=cfg.get("name"))   # paid for, committed or not
        _acted = bool(str(turn.get("action", "")).strip())
        word, _overridden = _floor.floor_word(stance, turn.get("floor"), _acted)
        # A DIRECTED MOVE IS RECORDED AS AIMED: the direction's id, whatever the actor wrote, and what it wrote is kept
        # on the validation record below when it differs. A silence is aimed at no one.
        _aimed = None
        if _floor_kw.get("to") and _acted:
            _aimed = {"directed": _floor_kw["to"][0], "said": str(turn.get("addressee") or "")}
            turn["addressee"] = _aimed["directed"]
        # A LISTENER WHO HOLDS WITH NOTHING IN IT is the cheap no: no row, no read, the round goes on (design v2 s2).
        # One who holds with a thought and no act is a silence worth recording, and is committed below unread.
        _silent = not leaks and not _acted and stance == "listener" and word == "hold"
        if _silent and not str(turn.get("thought", "")).strip():
            print("-- beat %d (turn %d) -- %s [holds — nothing to commit]" % (beat + 1, turn_no, names.get(speaker, speaker)))
            _next = rnd.after_listener("hold", present)
            if isinstance(_next, str):
                ended = _next
                break
            continue
        if leaks or not (_acted or _silent):            # a leak or an empty draw survived retries -> never committed
            _why = ("faithfulness: %s" % ", ".join(n for n, k in leaks)) if leaks else "empty turn (no action after retries)"
            led.record_turn_skipped(run_id, turn_no, speaker, _why)
            print("-- beat %d (turn %d) -- %s [%s — skipped, not committed]" % (
                beat + 1, turn_no, names.get(speaker, speaker), _why))
            _next = rnd.skipped(present)
            if isinstance(_next, str):
                ended = _next
                break
            continue
        # THE ROW JOINS ITS WINDOW (design v2 s5, gate window-reads). The seats read a window once, at its end - when
        # someone else makes a move, or the scene ends - and its rows commit then, in order (scripts/scene_window.py:
        # the reads, the decay-only rows before the last, every participant's receipt on the last). A move by the
        # window's speaker, and a listener's hold or interjection, add to it.
        _is_move = stance == "speaker" or word == "take" or bool(_flags.get("forced") and word == "interject")
        if window and _is_move and speaker != _wspk:
            _scene_window.close(_wctx, window)
            window = []
        if not window:
            _wspk = speaker
        # TOKEN ACCOUNTING, per call: `log_llm_call` had one caller repo-wide and it was a test, so `llm_calls`
        # stayed empty on every real run and there was no cost visibility at all.
        if not stub and direct.LAST_USAGE.get("model"):
            led.log_llm_call(run_id, turn_no, "act", direct.LAST_USAGE["model"],
                             direct.LAST_USAGE.get("tokens_in"), direct.LAST_USAGE.get("tokens_out"),
                             scene=cfg.get("name"))
        # WHAT THE CALL ITSELF SHOWED, for the row's validation record: a key the reply carried that nothing reads
        # (gate actor-reply), a floor word that is not one (floor-in-record) or of the other stance (round-loop), the
        # tripwire's second draw (round-loop), an aim the direction overrode (directed-addressee)
        _checks = {}
        if turn.get("extra"):
            _checks["reply_extra"] = list(turn["extra"])
            print("   [the reply carries key(s) nothing reads: %s]" % _replies.shown(turn["extra"]))
        if turn.get("floor_said"):
            _checks["reply_floor_said"] = str(turn["floor_said"])
        if _overridden:
            _checks["reply_floor_read_as"] = {"said": _overridden, "read": word}
        if _tripwire:
            _checks["tripwire"] = _tripwire
        if _aimed and _aimed["said"] != _aimed["directed"]:
            _checks["addressee_directed"] = _aimed
        window.append({"turn": turn_no, "who": speaker, "stance": stance, "word": word, "reply": turn, "silent": _silent,
                       "move": _is_move, "packet": packet, "event_text": event_text, "present": list(present),
                       "world": _world_b, "beat": beat, "checks": _checks})
        # WHO IS ASKED NEXT reads the speaker's own tags for the move (design v2 s5: the stub double, bounded to that
        # job, never reaching state): the seats have not read yet. Unpruned by lands_on, which only a seat names.
        try:
            applied = normalise_dimensions(turn["tags"] if isinstance(turn.get("tags"), dict) else {"dimensions": {}})
        except _EngineError:
            applied = {"dimensions": {}}
        target, tgroup = resolve_subject(packet["volatile"]["edges"], gi, applied.get("object") or applied.get("subject"),
                                         referenced_ids(packet["volatile"]["percepts"]))
        if target:
            applied = dict(applied, target=target)
        _lands = None
        addressee = turn.get("addressee", "")          # WHO was spoken to (distinct from the subject)
        if _acted and word != "hold":                 # an act held in silence is not a turn at speaking (recency)
            a["last_spoke"] = committed
        # A MOVE - the speaker's, a listener's take, or a word on the forced floor - offers the floor; `move` and `cut`
        # (a cut-in the round licensed) are what the settled stop counts (gate settled-stop).
        log.append({"who": speaker, "action": turn["action"], "thought": turn["thought"], "tags": applied,
                    "floor": word, "addressee": str(turn.get("addressee") or ""),
                    "move": _is_move, "cut": bool(_flags.get("interrupt"))})
        window[-1]["log"] = log[-1]                   # the window's reads mark it when it closes (tells)
        if "tells" in _sys and not stub and not _silent:   # a sign is cut before the next listener sees the move
            _scene_window.read_move(_wctx, window[-1])
        turn_no += 1                                    # this row is numbered; it commits when its window closes
        committed += 1

        if turn.get("exit"):
            present = [i for i in present if i != speaker]
            print("\n   >> %s leaves the scene. <<" % names.get(speaker, speaker))
            # under two, the scene is over - unless the one left holds the floor and said keep (alone on stage)
            if len(present) < 2 and not (stance == "listener" and present == [rnd.holder] and rnd.kept):
                ended = "exit"
                break

        # THE DECISION IS THE ENGINE'S; THE REPORTING IS THIS FILE'S. Every input to the
        # floor economy moved to src/engine/floor.py on 2026-09-03 and the choice combining
        # them was the one piece left behind, so the module named for the economy did not
        # hold the decision and the decision could not be tested without running a scene.
        # THE ROUND DECIDES NOW (gate round-loop): a move - the speaker's, a listener's take, or a word on the forced
        # floor - offers the floor to the listeners by urge; an interjection or a hold lets the round go on. In a
        # two-hander every move is to the other person (design v1 s3), so the urge reads them as addressed.
        _others = [i for i in present if i != speaker]
        _addr_floor = _others[0] if len(_others) == 1 else addressee
        nxt, urges, ended_because = None, {}, None
        if _is_move:
            nxt, urges, ended_because = _floor.next_speaker(
                actors, present, speaker, applied, target, tgroup, _addr_floor, committed, lands_on=_lands)
            _next = rnd.after_move(speaker, word if stance == "speaker" else "yield", urges, present)
        else:
            _next = rnd.after_listener(word, present)
        ended_because = _next if isinstance(_next, str) else None
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
        if ended_because == "settled":
            print("\n== settled — asked again with the floor theirs, %s held. ==" % names.get(speaker, speaker))
            ended = "settled"
            break
        if _is_move and _floor.settled(log, urges):     # after the forced hold, before the ceiling (design v2 s3)
            print("\n== settled — %d moves in a row said nothing new, and nobody is moved to cut in. =="
                  % _floor.SETTLED_MOVES)
            ended = "settled"
            break
        _st, _who, _fl = _next
        _asks = "%s %s%s" % (names.get(_who, _who), "goes on" if _st == "speaker" else "is asked",
                             "".join(" (%s)" % f for f in sorted(_fl)))
        if urges:
            print("   urges  : %s  -> %s\n" % (
                "  ".join("%s=%.2f[sal%.2f dis%.2f]%s" % (
                    k, v[0], v[1], v[2], " ~unreached" if _lands_norm is not None and norm_id(k) not in _lands_norm else "")
                          for k, v in urges.items()), _asks))
        else:
            print("   -> %s\n" % _asks)

    _scene_window.close(_wctx, window)                # the last window, read and committed (gate window-reads)
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
    ap.add_argument("--profile", default=None,
                    help="the session profile (scripts/profile.py): the actor's model and the seats' backend")
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
                    help="a file holding {action, thought, tags, exit?, addressee?, act?} (or '-' "
                         "for stdin) — the inbound half. Used INSTEAD of the local model for the "
                         "first beat of this invocation; its shape checked before anything is opened "
                         "(REPLY_*), then validated, appraised and committed through the SAME path a locally-"
                         "generated turn takes, faithfulness wall included. Pair with --resume and "
                         "--budget 1 to act one beat at a time")
    args = ap.parse_args()

    # THE ACT SEAM'S INBOUND FILE, checked before anything is opened (gate actor-reply): a malformed turn was refused
    # inside the scene loop, after the run row was written, by a bare ValueError
    supplied = None
    if args.turn_json:
        try:
            raw = sys.stdin.read() if args.turn_json == "-" else open(args.turn_json, encoding="utf-8").read()
            supplied = json.loads(raw)
            _replies.actor_reply(supplied, supplied=True)
        except RecordError as e:
            raise SystemExit(str(e))
        except ValueError as e:
            raise SystemExit("--turn-json is not valid JSON: %s" % e)
        except OSError as e:
            raise SystemExit("--turn-json cannot be read: %s" % e)

    # THE SESSION PROFILE (gate session-profile): the author's choices for the whole session - the actor's model (unless
    # --model names another) and the seats' backend. Applied before the pre-warm, so a local actor is the one warmed.
    _profile = None
    if args.profile:
        from src.engine import roles as _roles
        try:
            _profile, _warns = _roles.load(args.profile)
        except RecordError as e:
            raise SystemExit(str(e))
        for _w in _warns:
            print("profile: %s" % _w)
        if args.model == DEFAULT_MODEL:
            args.model = _roles.model_id(_profile["actor"])

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
    if _profile:                          # subagent seats write their prompts beside the book, never into this repo
        _provider.configure_seats(_roles.model_id(_profile["seats"]), replies=os.path.join(book_dir, "runs", "seats"))
        if args.model.startswith("subagent:"):    # a subagent actor answers through the same folder (gate act-replay)
            _provider.configure_actor(args.model, replies=os.path.join(book_dir, "runs", "seats"))
    world, chars = load_book(book_dir)
    # THE CONTRACTS, AT RUN START (gate run-start-refusal, G4): the world, the scene's cast and the scene file AS
    # WRITTEN - `load_scene_cfg` rewrites it - each against its contract, before a sheet is stamped and before the
    # chronicle is opened (opening it migrates the schema, one way). What the engine would misread or silently drop
    # stops the run here, named; what reaches nothing and loses nothing is counted in one line. A draft still loads
    # and lints: refusing is the run's job, not the loader's.
    _raw = _as_written(args.scene) if args.scene else DEFAULT_SCENE
    _cast = _raw.get("cast") if isinstance(_raw, dict) and isinstance(_raw.get("cast"), list) else []
    _plays = {c["id"] for c in _cast if isinstance(c, dict) and isinstance(c.get("id"), str) and c["id"] in chars}
    try:
        _note = _contracts.require_at_start(world, {c: chars[c] for c in _plays}, _raw,
                                            os.path.basename(args.scene) if args.scene else "the built-in scene")
    except RecordError as e:
        raise SystemExit(str(e))
    if _note:
        print(_note)
    # THE LOADER, AND WHAT SPANS FILES, BEFORE THE CHRONICLE TOO (gate run-start-refusal): the loader's own refusal, a
    # cast id that is not a character of this book, a director's hold for someone who is not in it. Each was refused
    # after the chronicle was opened - the hold after the run row was written, leaving an empty run behind.
    try:
        scene_cfg = load_scene_cfg(args.scene) if args.scene else DEFAULT_SCENE    # director-authored, or the fixture
    except ValueError as e:
        raise SystemExit("scene file %s: %s" % (args.scene, e))
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
    _strangers = sorted({str(d.get("char")) for d in scene_cfg.get("attachments") or [] if d.get("char") not in chars})
    if _strangers:
        raise SystemExit("scene %r declares a hold for %s, who is not in this book"
                         % (scene_cfg.get("name"), ", ".join(repr(c) for c in _strangers)))
    # WHAT THE SHEETS AUTHORED, stamped before anything moves it: the fade folds rebuild from it
    # (gate erosion-derived-at-replay, 2026-09-22).
    for _ch in chars.values():
        _passage.stamp_authored(_ch)
    book_name = books.slug(book_dir)
    try:                                          # the chronicle lives WITH the book — enforced,
        default_db = books.assert_db_for_book(book_dir, args.db)   # not merely defaulted
    except books.BookError as e:
        raise SystemExit(str(e))
    # AN ADOPTED BOOK'S RECORD IS NEVER WRITTEN, and a scene's model calls come before its first write: refused here,
    # before any spend, naming the command that opens a draft (gate draft-flow)
    from src.engine import drafts as _drafts
    from src.engine.records import RecordError as _RecordError
    try:
        default_db, _create = _drafts.writer_db(default_db, "scene.py", book_dir)
    except _RecordError as e:
        raise SystemExit(str(e))
    led = Ledger(default_db, create=_create)     # a draft is opened, never re-created empty

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
        _ladders = rungs.ladders_drifted(led.run_config(run_id))      # LADDER DRIFT (gate ladder-pin), same rule
        if _ladders:
            print("  [!] %s" % _ladders)
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
        # THE LOG BEFORE THIS SCENE'S OPENING, and no further (gate slow-tiers-run): the opening's own stretch is applied
        # by `open_scene` below, so a reading an aborted launch left at this turn must not age anyone here too.
        _open = state["turn"] + 1
        # EACH CAST MEMBER IN THEIR VIEW OF THIS OPENING (gate flashback-windows): set in someone's past, the scene is a
        # window for them, and they are rebuilt as they were then - nothing of their later story, nothing of another
        # window; everyone else as they are now. `open_scene` refuses what cannot be (two places at once) by name.
        from src.engine import window as _window
        _at = scene_cfg["at_minutes"] if "at_minutes" in scene_cfg else _clockmod.parse_at(scene_cfg["at"])
        _views = {cid: _window.view(led.con, run_id, cid, at=_at, start=_open) for cid in cast_ids}
        for cid in cast_ids:                                       # rehydrate each cast member the prior scene evolved
            ch = chars[cid]
            ch = _passage.fold_arc(led.con, run_id, cid, ch, before_turn=_open, view=_views[cid])   # diffs AND each fade
            acq = led.acquisitions_for(run_id, cid, _views[cid])
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
                                led.timeline_for(run_id, cid, before=(_open, 2), view=_views[cid]),
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
            _tbinds = _targets.binds_for(led.con, run_id, cid, view=_views[cid])
            _targets.replay(ch, _tbinds)
            if _tbinds:
                print("   %s: refolded %d aboutness bind(s) on %s"
                      % (cid, len(_tbinds), ", ".join(sorted(ch["current"].get("targets") or {})) or "nothing"))
            _tmoves = led.toward_deltas_for(run_id, cid)
            _passage.fold_toward(led.con, run_id, cid, ch, before_turn=_open, view=_views[cid])
            if _tmoves:
                print("   %s: refolded %d micro movement(s) toward %d person(s)"
                      % (cid, len(_tmoves), len({m[0] for m in _tmoves})))
            _wmoves = led.wound_deltas_for(run_id, cid)
            _passage.fold_wounds(led.con, run_id, cid, ch, before_turn=_open, view=_views[cid])   # mints, deltas, fade
            if _wmoves:                      # OPERATOR output, not the prompt — rule 5 is the prompt
                print("   %s: refolded %d wound movement(s) on %s"
                      % (cid, len(_wmoves), ", ".join(sorted({m[0] for m in _wmoves}))))
            # mood AND condition, one restore shared with the chair (gate resume-and-parity)
            _passage.restore_latest(ch, led.latest_affect(run_id, cid, _views[cid]))
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
                   "prompt_versions": {"turn": 1, "ladders": rungs.fingerprint()}}   # the ladders it is directed from
        if _profile:                      # the session's choices travel with the run they shaped
            run_cfg["models"]["seats"] = _provider.seat_model()
            run_cfg["profile"] = _profile
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
    # THE REPORT, AFTER THE SCENE (gate flashback-windows): what a window would have added to each character it was
    # one for - the rows of theirs their present will never read. The actors decided what happened, so it can only
    # be told once they have.
    from src.engine import window as _window
    for cid in cast_ids:
        _v = _window.view(led.con, run_id, cid, reading=start_turn)
        if next_turn > start_turn and _window.is_window(_v):
            _added = _window.report(led.con, run_id, cid, start_turn, next_turn - 1)
            print("   WINDOW : %s - had this been their story, they would carry: %s" % (
                cid, "; ".join(_added) if _added else "nothing lasting"))
    _report_lore(led, run_id, keeper_ran, args.stub)
    _db_arg = "" if os.path.normcase(os.path.abspath(default_db)) == os.path.normcase(os.path.abspath(
        books.db_path(book_dir))) else ' --db "%s"' % default_db       # a draft's run resumes on the draft
    print("\nparked %s at turn %d — continue with: python scripts/scene.py --vault \"%s\"%s%s --resume %s" % (
        run_id, last, book_dir, _db_arg, " --stub" if args.stub else "", run_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
