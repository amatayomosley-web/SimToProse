#!/usr/bin/env python3
"""direct.py — the director's chair ("we are the directors", 2026-06-11).

The operator surface for human-directed simulation: you place a CIRCUMSTANCE (an event, in plain
text), the character lives it through the full spine (assemble -> one-pass turn -> validate ->
appraise -> decay -> atomic commit), you read the resolved turn and the state direction, and you
place the next one. Steering is circumstance ONLY — this tool has no affordance for writing the
character's state, thoughts, or actions; the discipline is structural (design.md).

Usage:
  python scripts/direct.py --book ashford --char maren --stub            # deterministic, no API
  python scripts/direct.py --book ashford --char maren                   # real LLM (OpenRouter haiku)
  python scripts/direct.py --book ashford --char maren --resume <run_id> # continue a chronicle

Commands at the prompt: any text = the circumstance you place | status | quit (parks the run).
Harness-layer by design: imports the engine, owns the LLM dispatch (the engine never calls models).
"""
import argparse
import json
import os
import re
import sys
import time
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURE_SUFFIXES = ("", "-slice", "-healer")   # this repo's fixture stems — they live HERE, not in src/engine (hard rule 1)
sys.path.insert(0, REPO)

from src.engine.scene import assemble, resolve_subject, subject_groups, referenced_ids  # noqa: E402
from src.engine import books   # module scope: BOTH the --book and --fixture branches use it
from src.engine import decay as _decay   # recall history fold — see run_turn's assemble call
from src.engine import clock as _clock
from src.engine import scene_facts as _scene_facts   # what has happened, POV-filtered (2026-09-22)
from src.engine import concepts as _concepts   # declared story-time elapsed, same call
from src.engine.severity import normalise_dimensions           # noqa: E402
from src.engine.prompt import build_turn_messages                  # noqa: E402
from src.engine.consolidation import (validate_tags, CATALOG, TagError, tag_refusal,
                                       render_flag)        # noqa: E402
from src.engine import integrity                              # noqa: E402
from src.engine import claims                                 # noqa: E402  (the utterance/T2 path)
from src.engine.state import build_profile, appraise, decay, receive   # noqa: E402
from src.engine import rungs                                       # noqa: E402  (a reading's height)
from src.engine.records import RecordError as _SeatRefusal         # noqa: E402
import appraiser                                                  # noqa: E402  (the two seats)
import provider as _provider                                      # noqa: E402  (the frontier-model seam)
from src.engine.targets import retarget                            # noqa: E402  (per-primitive aboutness)
from src.engine import targets as _targets                        # noqa: E402  (its log: binds_from/binds_for/replay)
from src.engine.direction import direct_condition                  # noqa: E402
sys.path.insert(0, os.path.join(REPO, "scripts"))                # composer lives beside this file
import composer as _composer                                      # noqa: E402  (the rung seam)
# keeper is NOT imported here at module scope: keeper.py imports critic.py, and critic.py imports
# THIS module (`from direct import _openrouter`) — a module-level import here closes that triangle
# into a circular import the moment anything imports critic before direct finishes initialising
# (measured: test_critic.py, test_edl.py, test_faithful_turn.py, test_narrate.py all failed this
# way). scene.py imports keeper at module scope safely because nothing imports scene.py from
# inside the critic/keeper chain; direct.py is IN that chain, so its keeper import stays local to
# where --keeper is actually used, below.
from src.engine.ledger import Ledger                               # noqa: E402
from src.engine.records import (Event, TurnCommit, RelationshipDelta, PATHS,
                                WoundDelta, TowardDelta, RecordError)  # noqa: E402
from src.engine import arc                                         # noqa: E402  (the arc engine)
from src.engine import bonds                                       # noqa: E402  (the relationship tier)
from src.engine import bond_rest                                   # noqa: E402  (its rest half: rest rows, the ordered fold)
from src.engine import attachments                                 # noqa: E402  (gate 5: what a person holds that is not a person)
from src.engine import connection as _connection                   # noqa: E402  (held_map: one registry for stake and feeling)
from src.engine import levers                                      # noqa: E402  (the wound refold on resume)
from src.engine import wound                                       # noqa: E402  (the wound tier's mover)
from src.engine import toward                                      # noqa: E402  (the MICRO tier)
from src.engine import acquisition                                 # noqa: E402  (the vault-growth engine)
from src.engine import faithfulness                                # noqa: E402  (name-leak detector)
from src.engine import faults                                      # noqa: E402  (the engine-fault detector)
from src.engine import passage                                     # noqa: E402  (one clock, two drivers)
from src.engine import systems as _systems                        # noqa: E402  (which systems this book runs)
from src.engine import condition as _condition                    # noqa: E402  (energy and stress that move)
from src.engine import body as _body                              # noqa: E402  (strength and exertion)
from src.engine import injuries as _injuries                      # noqa: E402  (a hurt weakens the body while it heals)

DEFAULT_MODEL = "ollama/gemma4:26b-a4b-it-q4_K_M"


def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _env_path():
    """Path to the .env holding OPENROUTER_API_KEY.

    Machine-local and therefore NEVER hardcoded — a committed absolute path
    publishes the operator's directory layout and signposts their credentials.
    Set SWE_ENV_FILE, or fall back to a .env beside the repo.
    """
    p = os.environ.get("SWE_ENV_FILE")
    if p:
        return p
    local = os.path.join(REPO, ".env")
    if os.path.exists(local):
        return local
    raise RuntimeError(
        "no .env found: set SWE_ENV_FILE to the file holding OPENROUTER_API_KEY, "
        "or place a .env at the repo root (it is gitignored)")


# ---- LLM dispatch (harness-layer twin of the probe's; the engine never calls models) ----

def _openrouter(messages, model, max_tokens=750):
    """The actor's OpenRouter call, through THE seam (scripts/provider.py, 2026-09-11). The actor's
    sampling stays the model's default (no temperature pin: the actor performs; the SEATS are the
    ones pinned at 0). `LAST_USAGE` is kept for the two readers that log it after the fact."""
    text = _provider.call(messages, model, "act", max_tokens=max_tokens, temperature=None, cache=True)
    LAST_USAGE.clear()
    LAST_USAGE.update(_provider.LAST_USAGE)
    return text


# TOKEN ACCOUNTING. `Ledger.log_llm_call` existed with exactly one caller — a test — so `llm_calls`
# was empty on every real run and guide-operating.md's documented spend query returned nothing. Both
# dispatchers already RECEIVE the counts in the response body and threw them away. Captured here for
# the caller that holds the ledger; the engine still never calls a model (CLAUDE.md rule 3).
LAST_USAGE = {}

# THE COMPOSER'S OWN CALLS (gate composer-usage, 2026-09-23). `rung_direction` asks the composer model BEFORE the
# actor's call and both dispatchers write the one `LAST_USAGE`, so the actor's call overwrote the composer's and
# only an `act` row was ever logged - every composer call went uncounted. Each call's usage is kept here, one entry
# per paid call (a retry is a second call), for the driver to log as `compose` rows (`log_compose_usage`).
COMPOSE_USAGE = []


def log_compose_usage(led, run_id, turn, scene=None):
    """Log the composer calls this beat made, one `compose` row each, and clear the list -> rows written."""
    n = 0
    for u in COMPOSE_USAGE:
        if u.get("model"):
            led.log_llm_call(run_id, turn, "compose", u["model"], u.get("tokens_in"), u.get("tokens_out"), scene=scene)
            n += 1
    COMPOSE_USAGE.clear()
    return n

_OLLAMA_THINKS = {}


def _ollama_can_think(model):
    """Whether an Ollama model supports thinking, from /api/show capabilities (cached per model).
    The rule: if a model CAN think it always should; a model that CAN'T must not be sent `think`
    (Ollama 400s on the param). This gate keeps thinking on wherever possible, off only where impossible."""
    if model in _OLLAMA_THINKS:
        return _OLLAMA_THINKS[model]
    import urllib.request
    req = urllib.request.Request("http://localhost:11434/api/show",
                                 data=json.dumps({"model": model}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        caps = json.load(r).get("capabilities", []) or []
    _OLLAMA_THINKS[model] = "thinking" in caps
    return _OLLAMA_THINKS[model]


def _ollama(messages, model, max_tokens=4096, think=True, temperature=1.0, seed=None):
    """Local dispatch — Ollama's NATIVE /api/chat endpoint on localhost (free, on-disk, pinned).
    think=False: the engine wants the character's immediate turn, not a reasoning trace — and for
    thinking models (Gemma 4) the hidden trace otherwise consumes the token budget and empties the
    reply (measured: gemma4:26b-a4b 138s/empty via /v1 -> 17.8s/valid here). Thinking is gated by _ollama_can_think so non-thinking models (which 400 on
    the param) never receive it. num_ctx 32768 (raised from 8192 on 2026-08-23, measured — see below)
    keeps the KV cache modest while leaving the thinking trace real room — the KV is a fixed,
    num_ctx-sized buffer Ollama allocates ONCE at load (server.log device.go:251), NOT a
    per-beat-growing thing; each beat is a fresh stateless /api/chat that refills it (scene memory is
    the ledger/vault, not the model KV).

    WHY 32768 AND NOT 8192, measured 2026-08-23. A scene prompt is BOUNDED, not growing: two principals of an
    active book measured 2,646 and 3,013 tokens (prompt_eval_count, gemma4:31b). Cast named by
    role only — hard rule 1. It does not grow with
    scene length — _compose_event keeps only the last 4 beats at 300 chars each (scene.py:106), recall
    is capped by the energy budget, and percepts/edges scale with cast and world rather than time. So
    ~3K is typical and ~5K a fat upper bound.
    But num_ctx covers PROMPT PLUS GENERATION, and max_tokens above is 4096: 3,000 + 4,096 = 7,096 of
    8,192, leaving ~1.1K for the thinking trace. That is the empty-reply failure described at the top
    of this docstring, hit again on 2026-08-23 by tests/basis_probe.py (55 of 162 replies empty,
    almost all gemma4). 8192 was not generous; it was about one bad turn from zero.
    COST, measured on this host via /api/ps: 8K -> 26.2 GB total / 21.9 VRAM, 32K -> 28.4 / 22.0,
    128K -> 37.7 / 21.4. VRAM saturates at ~22 of 24 GB regardless, so the delta lands in system RAM:
    +2.2 GB for 32K, +11.5 GB for 128K. 128K buys nothing a bounded ~3K prompt can use.

    THE OOM RATIONALE BELOW IS STALE AND KEPT FOR PROVENANCE. It cites a 16 GB host; this machine has
    64 GB (41 free, measured 2026-08-23), so the constraint that set 8192 no longer holds here. The
    pre-warm fix it describes is still in scene.py and still correct. keep_alive is left at Ollama's default so the model stays warm
    between beats. The OOM that dogged the early scene runs (ggml.c:1558 mem_buffer NULL -> runner crash -> HTTP 500;
    server.log 2026-06-14) was NOT KV or VRAM: it was the COLD-LOAD HOST-RAM spike — cold-loading the 17 GB
    model (UseMmap:false) while scene.py is resident exhausts the 16 GB host. The fix lives in the harness
    (scene.py pre-warms the model before load_book, so the cold load lands while host RAM is free); freeing
    2.2 GB of GPU VRAM via OLLAMA_GPU_OVERHEAD did NOT help (host-bound, not VRAM-bound — measured 2026-06-14). Sampling is Gemma 4's tuned profile — temperature 1.0, top_p 0.95, top_k 64 (the
    model's shipped defaults; measured 2026-06-12, temp 0/0.7 are off-spec and induce a greedy
    repetition tic + inflated empty turns). The engine's determinism is fold-forward over the committed
    event log (ledger.resume folds stored turns; it never re-generates), so correctness does NOT depend
    on sampling reproducibility — and at temp 1.0 on GPU, generation is NOT bit-reproducible anyway (FP
    reduction order; confirmed same seed -> different draw). The per-turn seed (run_turn -> seed=turn_no)
    only decorrelates turns from Ollama's single default seed. No auth, no fallback: a down daemon raises."""
    import urllib.request
    payload = {"model": model, "messages": messages, "stream": False,
               "options": {"temperature": temperature, "top_p": 0.95, "top_k": 64,
                           "num_ctx": 32768, "num_predict": max_tokens}}
    if seed is not None:                  # Ollama uses a FIXED seed by default (deterministic even at temp>0); vary the seed to sample
        payload["options"]["seed"] = seed
    if _ollama_can_think(model):          # capable -> always think (honor the flag); incapable -> omit (Ollama 400s)
        payload["think"] = bool(think)
    body = json.dumps(payload).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        body = json.load(r)
    LAST_USAGE.clear()
    LAST_USAGE.update({"model": model,
                       "tokens_in": body.get("prompt_eval_count"),
                       "tokens_out": body.get("eval_count")})
    return body["message"]["content"]


def _parse_reply(text):
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    try:
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        d = {}
    tags = d.get("tags") if isinstance(d.get("tags"), dict) else {"dimensions": {}}
    # `act` was dropped here, so `scene.py:_law_events` — which returns [] on a falsy act — could
    # never fire, and no authored law has ever bound to a real model reply. The prompt asks for it
    # whenever the world declares laws; the parser simply never carried it through. Its own tests
    # passed by calling `_law_events` directly with a hand-built {"act": ...} dict.
    return {"action": d.get("action", ""), "thought": d.get("thought", ""),
            "exit": bool(d.get("exit", False)), "addressee": d.get("addressee", ""),
            "act": str(d.get("act", "") or ""), "tags": tags}


def rung_summary(affect):
    """affect -> a short operator-facing line naming each built path and the rung it is at.

    OPERATOR PRINT ONLY. The rung NAME never reaches an actor (composer.py: the label is inert, and
    measured 2026-09-07 identical text under a WRONG label scored higher than under its own), but a
    human watching a run needs to see where the character sits, and this replaces the band-phrase
    line the band-phrase affect renderer used to print before it was retired on 2026-09-08.
    """
    try:
        rows = _composer.selectable(affect)
    except Exception as exc:
        return "(rung summary unavailable: %s)" % type(exc).__name__
    if not rows:
        return "no built path covers this character's affect"
    return "; ".join("%s %s" % (r["path"].lower(), r["name"]) for r in rows)


def rung_direction(packet, brief="", model=None, stub=False):
    """packet -> the rung-block direction the actor receives, or None.

    THE RUNG SEAM. Until 2026-09-08 the emotion ladders reached no actor at all: `composer.selectable`
    computed rows carrying the block text and `composer.direction_for` assembled the actor-facing
    wording, and NOTHING CALLED EITHER. The ladder and the prompt were two parallel renderings of the
    same affect vector with only the thin one (the band-phrase renderer, since retired) connected.

    IT IS NOW THE WHOLE EMOTION LANGUAGE. It used to ride alongside a per-primary clause list that covered
    every primitive and only eight paths have built ladders, so replacing it would silently mute the
    rest — and scripts/composer.py:1-30 specifies "a second file that reaches the actor ALONGSIDE the
    assembler's". A packet whose affect touches no built path returns None and the prompt is byte-
    identical to the pre-rung engine.

    THIS IS A FUNCTION AND NOT AN INLINE BLOCK because `build_turn_messages` has TWO call sites in
    this file — llm_turn, and the `--prompt-only` branch of run_turn. Wiring one and not the other is
    exactly the bug this seam shipped with for its first ten minutes: the unit suite passed on a
    synthetic packet while a real `--prompt-only` run emitted no block at all.

    IT REPORTS ITS OWN FAILURE. The run degrades rather than crashing, per the engine's boundary, but
    a silent None is what hid the two-call-site bug, so a skip is announced on stderr.

    IT RECORDS WHAT IT SENT (gate composer-direction-recorded, 2026-09-22): `packet["manifest"]
    ["direction"]` is set on every call - `composer.record` when a direction was built, else
    {"by": "none", "why": ...}. Both drivers commit that manifest with the turn, and a retry calls this
    again, so the committed record is the direction of the attempt that was kept. A supplied turn commits the
    direction its `--prompt-only` step kept (`via: prompt-only`), or `by: none` with the reason (gate
    chair-parity). No key at all means this beat built no prompt (a stub actor, or a beat committed
    before gate composer-direction-recorded).
    """
    rec = {"by": "none", "why": ""}
    try:
        vs = (packet.get("volatile") or {}).get("state") or {}
        affect = vs.get("effective") or vs.get("affect")
        if not isinstance(affect, dict):
            rec["why"] = "the packet carries no affect"
            return None
        # the COMPOSED rung picks the block; `state.descending` (scene.assemble, off the MOOD and
        # the log) says whether that block is the descent one above the pivot
        rows = _composer.selectable(affect, descending=vs.get("descending"))
        if not rows:
            rec["why"] = "no built path covers this affect"
            return None
        sel, by, fell_back = _compose_selection(rows, brief, model, stub)
        text = _composer.direction_for(rows, sel)
        rec = _composer.record(rows, sel, text, by, fell_back=fell_back, descending=vs.get("descending"))
        return text
    except Exception as exc:
        print("  [rung-direction skipped] %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        rec = {"by": "none", "why": "%s: %s" % (type(exc).__name__, exc)}
        return None
    finally:
        _manifest = packet.get("manifest") if isinstance(packet, dict) else None
        if isinstance(_manifest, dict):
            _manifest["direction"] = rec


def _compose_selection(rows, brief, model, stub):
    """(rows, brief, model, stub) -> (a VERIFIED selection, who selected it, why the composer fell back).
    The scene-aware half, with a floor under it. `by` is "composer" or "floor"; `fell_back` is "" unless
    the composer was asked and failed, when it names the error (it used to reach stderr only).

    THE HALF THAT WAS BUILT AND NEVER DISPATCHED. `composer.compose_prompt` and `composer.verify`
    have existed since the composer was written; no driver called either, so every live run selected
    through `select_deterministic`, which ranks by relative ladder height and takes no brief.
    Measured 2026-09-08: the repo fixture was played on its three TALLEST ladders whatever the beat
    was, and `selection["about"]` came back empty every time. That is a ranker, not a composer.

    IT FALLS BACK RATHER THAN GUESSING. No brief, no model, or --stub takes the deterministic floor
    unchanged -- the engine runs key-free by default and must keep doing so. So does any failure:
    a transport error, an unparseable reply, or a `verify` REFUSAL. A refusal is not repaired,
    because every refusal names something the composer is structurally able to get wrong (selecting
    a path the engine never produced, moving a rung, more than three, no single primary, or prose
    carrying an emotion name or a named act). Repairing one would make the gate advisory.

    THE FLOOR FILTER DOES NOT APPLY HERE, and that asymmetry is deliberate. `select_deterministic`
    drops floor rungs because a height ranker is blind to the beat and pads its cap with states the
    character is not in. A composer holding the brief may legitimately decide a quiet emotion is
    what this beat is about, and `verify` already bounds what it may pick.
    """
    if not brief or not model or stub:
        return _composer.select_deterministic(rows), "floor", ""
    try:
        msgs = _composer.compose_prompt(rows, brief)
        if model.startswith("ollama/"):
            raw = _ollama(msgs, model[len("ollama/"):], max_tokens=700, think=False)
        else:
            raw = _openrouter(msgs, model, max_tokens=700)
        COMPOSE_USAGE.append(dict(LAST_USAGE))          # before the actor's call overwrites it (gate composer-usage)
        # NOT `_parse_reply` -- that one is shaped for the ACTOR's reply and coerces every result
        # into {action, thought, exit, addressee, act, tags}, so a composer selection came back
        # with `selected` silently dropped and every call fell back. Measured 2026-09-08.
        m = re.search(r"\{.*\}", raw or "", re.DOTALL)
        sel = json.loads(m.group(0)) if m else None
        if not isinstance(sel, dict) or "selected" not in sel:
            raise ValueError("composer reply carried no `selected`")
        return _composer.verify(sel, rows), "composer", ""
    except Exception as exc:
        print("  [composer fell back to the deterministic floor] %s: %s"
              % (type(exc).__name__, exc), file=sys.stderr)
        return _composer.select_deterministic(rows), "floor", "%s: %s" % (type(exc).__name__, exc)


def llm_turn(packet, event_text, temperament, model, stub, think=True, seed=None, relationships=None, corrections=None, acts=(), brief=""):
    if stub:
        # THE STUB ADDRESSES SOMEONE. Measured 2026-09-01: without an addressee a two-hander lulls
        # after ONE beat — urge 0.018 against a 0.060 floor — because `_ADDRESSED_BONUS` (0.15,
        # scripts/scene.py) never applies and inhibition alone (0.066 on the reference sheet) exceeds
        # the floor. The engine was right and the fixture was unrepresentative: a person spoken to in
        # a room answers. `tests/test_pipeline_e2e.py` reported OK on that dead scene for months.
        # `volatile["edges"]` is a LIST of {target, trust, ...}, not a dict (src/engine/scene.py).
        present = [e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or [])
                   if e.get("target")]
        dur = "durable" if "durable" in event_text.lower() else "transient"
        subj = present[0] if present else (packet.get("stable", {}).get("persona", {}).get("id") or "")
        tags = {"type": "mundane", "summary": event_text, "dimensions": {"mastery": "mild"},
                "durability": dur}
        if subj:
            tags["subject"] = subj
        return {"action": "(stub) the character meets the moment — %s" % event_text.lower(),
                "thought": "(stub) steady; do what it needs",
                "addressee": present[0] if present else "",
                "tags": tags}
    messages = build_turn_messages(packet, event_text, temperament, relationships, acts=acts,
                                   rung_direction=rung_direction(packet, brief=brief, model=model, stub=stub))
    if corrections:                                                  # faithful_turn appends corrective turns on a name-leak retry
        messages = list(messages) + list(corrections)
    if model.startswith("ollama/"):                                  # local on-disk dispatch (free, pinned)
        return _parse_reply(_ollama(messages, model[len("ollama/"):], think=think, seed=seed))
    return _parse_reply(_openrouter(messages, model))


def faithful_turn(packet, event_text, temperament, model, stub, think=True, seed=None, relationships=None, max_retries=2, acts=(), information=None, char_id=None, brief=""):
    """llm_turn + the ACTIVE faithfulness guard. If the actor emits a name it does not hold (a latent
    weights-leak the masking wall can't prevent — faithfulness.check_name_leaks), re-call with an
    explicit correction, up to max_retries. An empty/unparseable draw (no action — a stochastic
    thinking-spiral or non-JSON reply at temp 1.0) is LIKEWISE re-sampled, with no correction: just a
    fresh draw of the same prompt (the caller still records turn-skipped if it stays empty past
    retries, so an empty beat never false-lulls a scene). Returns (turn, leaks); leaks == [] means clean. Never
    EDITS a turn — a leaking attempt is discarded and regenerated; the caller records turn-skipped if
    leaks persist (design.md 'recorded as-is, never edited'). The Sonnet/Claude semantic critic is the
    layer ABOVE this mechanical floor (driving-the-engine.md 'the layer above')."""
    rels = relationships or {}
    corrections = []
    turn = None
    for attempt in range(max_retries + 1):
        s = seed if (seed is None or attempt == 0) else seed + 100 * attempt   # resample on retry
        turn = llm_turn(packet, event_text, temperament, model, stub, think=think, seed=s, acts=acts, brief=brief,
                        relationships=relationships, corrections=(corrections or None))
        if not str(turn.get("action", "")).strip() and attempt < max_retries:
            continue                          # empty/unparseable draw (no action) — resample. At temp 1.0
                                              # generation is non-reproducible, so a fresh draw of the SAME
                                              # prompt usually parses (measured 2026-06-14: in-scene empty,
                                              # standalone resample full). Nothing to correct — just redraw.
        emitted = "%s %s" % (turn.get("action", ""), turn.get("thought", ""))
        leaks = faithfulness.check_name_leaks(emitted, rels)
        # THE WALL USED TO BE NAME-SHAPED. Not every secret is a name — a relationship, an
        # intention, a location, a debt, a parentage. `information` is the snapshot's
        # fact -> knowers map, folded from `reveal`, and an actor stating a fact it is not a
        # knower of is the same offence one level out. `information=None` (every pre-2026-09-01
        # caller) makes this a no-op, so nothing already running changes.
        fact_leaks = faithfulness.check_fact_leaks(emitted, char_id, information or {})
        if not leaks and not fact_leaks:
            return turn, []
        if leaks:
            corrections.append({"role": "user", "content": (
                "You used a name your character does not know: %s. They know this person only as %s. "
                "Rewrite your ENTIRE reply (same JSON shape) using only that descriptor — never the name."
                % (", ".join(n for n, k in leaks), "; ".join("%r" % k for n, k in leaks)))})
        if fact_leaks:
            corrections.append({"role": "user", "content": (
                "Your character stated something they do not know: %s. Nobody told them. Rewrite "
                "your ENTIRE reply (same JSON shape) without it — they may act on what they can "
                "see and what they were told, and on nothing else."
                % "; ".join("%r" % f for f, _k in fact_leaks))})
        leaks = list(leaks) + [(f, "not a knower") for f, _k in fact_leaks]
    return turn, leaks


# ---- world faults: the hinge trigger of the world-building workflow, made mechanical ----
# "The bible grows from the sim": when the sim reaches for world that doesn't exist, the chair
# queues it as an Obsidian checkbox in the BOOK's world-faults.md (the operator's inbox). The
# ENGINE never writes the vault; the chair is the operator's surface. Authoring stays human.

def detect_world_faults(packet, scene_slice, event_text, world, turn_no):
    faults = []
    if scene_slice.get("location") and not any(
            p.get("ref", "").startswith("loc.") for p in packet["volatile"]["percepts"]):
        faults.append("turn %d: location %r has no world note (no loc percept resolved)"
                      % (turn_no, scene_slice["location"]))
    core = next((p for p in packet["volatile"]["percepts"] if p.get("ref", "").startswith("evt.")), None)
    classes = set(world.get("lexicon", {}).get("attribute_classes", {}))
    if core and not (set(core.get("attributes", [])) & classes):
        faults.append("turn %d: the lexicon has no vocabulary for this event — %r"
                      % (turn_no, event_text[:80]))
    return faults


def startup_faults(char, world):
    people = {p.get("id") for p in world.get("people", [])}
    return ["relationship %r points at no person note" % k
            for k in char["current"].get("relationships", {}) if k not in people]


def record_faults(faults, book_dir):
    for f in faults:
        print("  [world-fault] %s" % f)
    if book_dir and faults:
        path = os.path.join(book_dir, "world-faults.md")
        new = not os.path.exists(path)
        # A CHECKLIST, NOT A LOG. The header below says each box is a world-building pass to
        # run, and the same hole is reached for on every turn that needs it - appending blind
        # wrote one fault per turn and buried the rest. Read back what is already listed and
        # add only what is not. A TICKED box counts as listed: a fault the operator has
        # already worked through must not come back looking fresh.
        listed = set()
        if not new:
            with open(path, encoding="utf-8") as fh:
                listed = {ln.split("]", 1)[-1].strip() for ln in fh if ln.startswith("- [")}
        fresh = [f for f in faults if str(f).strip() not in listed]
        if not fresh:
            return
        with open(path, "a", encoding="utf-8") as fh:
            if new:
                fh.write("# World Faults\n\nThe sim reached for world that does not exist yet. Each box = a\n"
                         "world-building pass to run (docs/guide-content.md §world-building pass).\n\n")
            for f in fresh:
                fh.write("- [ ] %s\n" % f)


# ---- the chair ----

def _direction_file(led, run_id, actor):
    """Where a `--prompt-only` step leaves the direction its prompt carried, for the `--turn-json` step that
    answers it: beside the chronicle, one file per (run, actor). None for an in-memory ledger.

    ON DISK BECAUSE THE TWO STEPS ARE TWO PROCESSES (gate chair-parity, 2026-09-23). A supplied turn used to
    commit no `direction` at all, and it cannot recompute one: with a brief and a model the composer's pick
    is a fresh model call. Keyed by run and actor, not turn, because a brand-new run's two steps can see
    different turn numbers (the prompt step mints it at 0; the answering step resumes at the last turn + 1)."""
    try:
        path = next((r[2] for r in led.con.execute("PRAGMA database_list") if r[1] == "main"), "")
    except Exception:
        return None
    if not path:
        return None
    return os.path.join(path + ".directions", "%s.%s.json" % (run_id, actor))


def _keep_direction(led, run_id, actor, turn_no, event_text, direction):
    """The `--prompt-only` half: record what direction the emitted prompt carried."""
    path = _direction_file(led, run_id, actor)
    if not path or not isinstance(direction, dict):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"run_id": run_id, "actor": actor, "turn": turn_no, "circumstance": event_text,
                   "direction": direction}, fh)


def _kept_direction(led, run_id, actor, event_text):
    """The `--turn-json` half -> the direction record this supplied turn commits: the prompt step's, when one
    was kept for this run, actor and circumstance; otherwise `by: none` with the reason. It never guesses."""
    path = _direction_file(led, run_id, actor)
    try:
        with open(path, encoding="utf-8") as fh:
            kept = json.load(fh)
    except (TypeError, OSError, ValueError):
        kept = None
    if (isinstance(kept, dict) and kept.get("run_id") == run_id and kept.get("actor") == actor
            and kept.get("circumstance") == event_text and isinstance(kept.get("direction"), dict)):
        return dict(kept["direction"], via="prompt-only", prompt_turn=kept.get("turn"))
    return {"by": "none", "why": "a supplied turn with no --prompt-only direction kept for this run, "
                                 "actor and circumstance"}


def run_turn(led, run_id, char, world, groups_index, profile, temperament, affect, turn_no, event_text, recent, model, stub, book_dir=None, by=None, supplied=None, prompt_only=False, brief="", minutes=0.0):
    """One placed circumstance through the full spine. Returns (new_affect, ok, char, profile) —
    char/profile may be EVOLVED if the event wrote a durable baseline diff (the arc engine).

    `by` is the entity id of WHOEVER PERFORMED the circumstance, when a person performed it. It is
    AUTHORED by the director (`by:<id> <text>` at the REPL), never inferred — the same decision the
    laws' `act` made, for the same reason: a classifier reading "he takes the basket" and guessing
    which entity `he` is fails silently and poisons an edge instead of skipping it. Supplied, the
    character re-reads that person on their own tags; absent, no edge moves and the turn is
    unchanged."""
    scene_slice = {"event": {"text": event_text, "kind": "mundane"}, "recent": recent[-2:],
                   "location": char["current"].get("location"),
                   # whom this mood came from, per path, off the log — the balance meets them in full
                   "raised_by": led.raised_by(run_id, char["fixed"]["name"].lower()),
                   # when each path was last read, and the actor's last committed beat — the descent
                   # signal's fuel (rungs.descending): no reading at the last beat means no fuel
                   "last_read_turn": led.last_read_turn(run_id, char["fixed"]["name"].lower()),
                   "last_turn": led.last_turn(run_id, char["fixed"]["name"].lower())}
    # SLOPE as an assemble ARGUMENT, so the manifest can name it (see scene.assemble).
    _actor = char["fixed"]["name"].lower()
    # Recall decay needs the RUN's turn, not the character's — the ledger owns it. Until
    # 2026-09-04 none of these four reached the gate, so every recall ran at turn 0 with
    # no history and no elapsed time, i.e. no decay at all. fold_recall_history derives
    # {bid: {last_turn, count}} from the append-only decision_manifests table rather than
    # reading it off the belief, keeping "cause is logged once; effect is derived at
    # replay" (decay.py:30).
    # THE FENCE (2026-09-11): what is established about the place and whoever acted, as of now.
    from src.engine import read_api as _read_api
    _subjects = sorted({x for x in [scene_slice.get("location") or "", by or ""] if x})
    _established = _read_api.established(led.con, run_id, _subjects, as_of=turn_no).rows if _subjects else []
    _sys = _systems.for_book(world)                  # which systems this book runs (gate systems-registry)
    packet = assemble(char, world, scene_slice, affect, char["current"]["condition"],
                      prev_affect=led.previous_affect(run_id, _actor, turn_no),
                      current_turn=turn_no,
                      established=_established,
                      # WHAT HAS HAPPENED HERE (2026-09-22) — the chair reads the same facts the
                      # scene driver does, through the same call, so the two drivers cannot drift
                      # (the defect gate `driver-clock-parity` fixed for the clock).
                      facts=_scene_facts.facts_for(led.con, run_id, _actor, before_turn=turn_no),
                      relationships=char["current"].get("relationships", {}),
                      recall_history=_decay.fold_recall_history(led.con, run_id, _actor),
                      elapsed=_clock.elapsed_days_since(led.con, run_id, turn_no),
                      tired="condition_flow" in _sys)     # the room's subtle cues dim with the mind (gate tired-lexicon)
    record_faults(detect_world_faults(packet, scene_slice, event_text, world, turn_no), book_dir)
    if _systems.declared(world):
        packet["manifest"]["systems"] = sorted(_sys)
    actor = char["fixed"]["name"].lower()
    rels = char["current"].get("relationships", {})

    # THE ACT SEAM (docs/orchestration.md, unwired seam 1). `--prompt-only` emits exactly the
    # messages the engine would have sent; `--turn-json` hands a turn back. Between them, ANY model
    # anywhere can act a character and the chronicle cannot tell which one did — argv in, stdout
    # out, the one interface every harness shares. critic.py and narrate.py have had this pair since
    # the beginning; direct.py and scene.py, the two that ACT, had neither, which is why the
    # character-simulator agent could not do its job.
    COMPOSE_USAGE.clear()                            # this beat's composer calls only (gate composer-usage)
    if prompt_only:
        _msgs = build_turn_messages(packet, event_text, temperament, rels,
                                    rung_direction=rung_direction(packet, brief=brief, model=model, stub=stub))
        log_compose_usage(led, run_id, turn_no)
        _keep_direction(led, run_id, actor, turn_no, event_text, packet["manifest"].get("direction"))
        print(json.dumps(_msgs, indent=2))
        return affect, False, char, profile

    if supplied is not None:
        # A SUPPLIED TURN PASSES THE SAME WALLS. `faithful_turn` exists because a model emits names
        # it does not hold, and that risk does not fall when the model is a stranger's — a re-entry
        # that skips the wall is a hole in it. Shape first, then the name-leak check, then the
        # identical validate/appraise/commit path below.
        missing = [k for k in ("action", "thought", "tags") if k not in supplied]
        if missing:
            raise ValueError("supplied turn is missing %s — the contract is "
                             "{action, thought, tags, exit?, addressee?}" % ", ".join(missing))
        turn = {"action": str(supplied.get("action", "")), "thought": str(supplied.get("thought", "")),
                "exit": bool(supplied.get("exit", False)), "addressee": supplied.get("addressee", ""),
                "act": str(supplied.get("act", "") or ""),
                "tags": supplied.get("tags") if isinstance(supplied.get("tags"), dict) else {"dimensions": {}}}
        leaks = faithfulness.check_name_leaks("%s %s" % (turn.get("action", ""), turn.get("thought", "")), rels)
        packet["manifest"]["direction"] = _kept_direction(led, run_id, actor, event_text)
        print("  [supplied turn accepted for validation — %d char action]" % len(turn["action"]))
    else:
      try:
        # name hygiene rides in build_turn_messages: assemble saw RAW text (so a name in it resolves to its entity);
        # the PROMPT masks every name this actor never acquired (passed via relationships). faithful_turn
        # then REGENERATES on any name-leak the masking wall couldn't stop (latent weights leak) —
        # and, since 2026-09-01, on any tracked FACT the actor is not a knower of, because the wall
        # was name-shaped and not every secret is a name.
        turn, leaks = faithful_turn(packet, event_text, temperament, model, stub, seed=turn_no, brief=brief,
                                    relationships=rels,
                                    information=(led.fold(run_id, max(turn_no - 1, 0)) or {}).get("information"),
                                    char_id=actor)
      except Exception as exc:                       # degrade, never crash; no silent skips
        log_compose_usage(led, run_id, turn_no)       # a failed beat's composer calls were still paid for
        led.record_turn_skipped(run_id, turn_no, actor, str(exc))
        print("  [turn failed, recorded as turn-skipped: %s]" % str(exc)[:80])
        return affect, False, char, profile

    log_compose_usage(led, run_id, turn_no)          # every attempt's composer calls, skipped beat or not
    # THE EMPTY DRAW. `scene.py:485` refuses one and records turn-skipped; the chair did not, so an
    # action that stayed empty through every resample committed as a real turn — a beat in the
    # chronicle where nothing happened, indistinguishable later from one where nothing was meant to.
    # Same rule in both drivers or it is not a rule.
    if not str(turn.get("action", "")).strip():
        led.record_turn_skipped(run_id, turn_no, actor, "empty turn (no action after retries)")
        print("  [empty draw after retries — recorded as turn-skipped, not committed]")
        return affect, False, char, profile

    if leaks:                                      # name(s) the actor cannot hold survived retries -> reject; never commit a leak
        led.record_turn_skipped(run_id, turn_no, actor,
                                "faithfulness: used name(s) not theirs after retries: %s" % ", ".join(n for n, k in leaks))
        print("  [faithfulness reject: %s used %s after retries — turn skipped]" % (actor, ", ".join(n for n, k in leaks)))
        return affect, False, char, profile
    # THE SEATS (Phase 3, wired 2026-09-11) — the twin of scripts/scene.py's block. The chair has no
    # cast roster, but the PACKET knows who is in the room: `volatile.edges` carries one edge per
    # entity the PerceptSet recognised (the stub reads the same list). Until 2026-09-18 the event seat
    # here was told nobody else was present, so it could name no object but `self` and every named
    # party was refused (APPRAISER_OBJECT_UNKNOWN) — the same list now feeds the transfers' parties.
    _readings, _lands, _seat_notes = [], [], []
    _seat_answered = False
    _roster = [str(e.get("target")) for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")]
    if by and str(by) not in _roster:
        _roster.append(str(by))
    if not stub:
        try:
            # ATTRIBUTION PRECEDENCE (2026-09-19, gate seat-attribution): the seat's word, when it
            # answers, wins; the actor's own tags.attribution self-tag is the stub double / the
            # refusal fallback below, never a second vote.
            tags = normalise_dimensions(appraiser.read_event(
                str(turn.get("action", "")), _provider.seat_model(), led=led, run_id=run_id, turn=turn_no,
                moment=event_text, present=_roster, actor=char["fixed"]["name"], target=str(by or ""),
                attachments=attachments.names_for(world), exertion="body" in _sys))
            _seat_answered = True
            # THE SUMMARY IS THE ACTOR'S (gate wounds-and-memory-inputs, 2026-09-22) - scene.py does the same
            tags = acquisition.with_actor_summary(tags, turn.get("tags"))
        except _SeatRefusal as _e:
            _seat_notes.append("event seat refused: %s" % str(_e)[:120])
            tags = normalise_dimensions(turn["tags"])
        try:
            _readings, _lands, _conf, _missing = appraiser.read_emotion(
                str(turn.get("action", "")), str(turn.get("thought", "")), _provider.seat_model(),
                led=led, run_id=run_id, turn=turn_no, moment=event_text, present=None, me=actor,
                percepts=packet["volatile"]["percepts"])
            if _missing:
                _seat_notes.append("concepts the registry lacks: %s" % ", ".join(_missing))
        except _SeatRefusal as _e:
            _seat_notes.append("emotion seat refused: %s" % str(_e)[:120])
            _readings = []
    else:
        tags = normalise_dimensions(turn["tags"])
    # THE READER'S WORD ONLY (owner ruling C3b2, gate body-exertion): the event seat rates exertion; an
    # actor's own tags - the stub double, the refusal fallback - never carry it into the log.
    if "body" in _sys and not _seat_answered:
        tags = {k: v for k, v in tags.items() if k != "exertion"}
    validation = validate_tags(tags, packet["volatile"]["percepts"], char["baseline"]["skills"])
    if not validation["ok"]:
        # FAIL-FAST (2026-08-30). This branch used to read `applied = {"dimensions": {}}`,
        # discarding the WHOLE self-report over one invalid field. See consolidation.tag_refusal.
        raise TagError(*tag_refusal(validation, char["fixed"]["name"], turn_no))
    elif validation["flags"]:
        legit = CATALOG.get(tags.get("type", ""), {}).get("appraisal_map", [])
        applied = dict(tags, dimensions={d: v for d, v in tags.get("dimensions", {}).items() if d in legit})
    else:
        applied = tags
    # subject resolution: who is this event about + their class -> the empathy scope (state._regard, arc).
    # The actor may NAME a present party (it reads the scene); the engine validates presence and resolves
    # the group from the registry (never the LLM — the regard number stays off the prompt).
    named = tags.get("subject") if isinstance(tags, dict) else None
    # ALWAYS EMPTY IN THIS DRIVER, deliberately and not by oversight. `run_turn` builds a slice with
    # no `present` key because this chair has no roster to build one from: `current.location` is free
    # text about the acting character, world locations carry no occupants field, and `by` is one
    # optional director assertion that most beats omit — promoting it would make every beat typed
    # without it declare an empty room. So presence stays UNKNOWN here and every named entity reads
    # present, exactly as before. The call is wired anyway so the two drivers cannot drift.
    target, target_group = resolve_subject(packet["volatile"]["edges"], groups_index, named,
                                           referenced_ids(packet["volatile"]["percepts"]))
    if target is None and by:
        target = by
        target_group = (groups_index.get(by) or [None])[0]
    if target is not None:
        applied = dict(applied, target=target)
        if target_group is not None:
            applied["target_group"] = target_group
    # aboutness first, so this event's pushes bind the party the event was about
    _before_targets = dict(char["current"].get("targets") or {})
    # RULES 1/3/4 HERE; RULE 5 AFTER THE RECEIPT — see the twin comment in scripts/scene.py.
    if _readings:                                            # Phase 3: aboutness from the readings
        targets = _targets.bind_readings(_before_targets, _readings, me=actor)
    else:
        targets = retarget(_before_targets, applied, me=actor)
    char["current"]["targets"] = dict(targets)
    # THE CHANGE, NOT THE MAP. Hard rule 2 wants the state derivable FROM the log, so what rides the
    # turn is what moved — including a DROP, which rides as a release row. Logging only the positive
    # binds would leave un-binding underivable and the replay would diverge from this run.
    target_binds = _targets.binds_from(_before_targets, targets)
    # DECAY FIRST, THEN THE RECEIPT (docs/emotion-arithmetic.md section 8 — row 12 rejects
    # vector-before-decay; measured 2026-09-10: under the reverse order the clamp at 1.0 landed
    # before decay pulled back and no ladder's top band was reachable). The minutes since the last
    # turn pass, then this turn's reading lands on what is left. `impact` is the receipt's own
    # move. The REPL has no scene cfg; time is what --minutes-per-turn says, else 0.
    # GATE THREE (2026-09-11): the chair has no roster, so presence is UNKNOWN for people; a
    # concept is "here" when this beat names it. Decay ran on the binds before this beat; the
    # receipt uses the binds it made; repetition counts prior beats from the log.
    _here = {str(applied.get("target"))} if _concepts.looks_like_concept(applied.get("target")) else set()
    rested = decay(affect, temperament, profile, elapsed=minutes, targets=_before_targets, present=_here)
    _abouts = {str(t) for t in targets.values() if t}
    _repeats = {ab: _targets.repeat_count(led.con, run_id, actor, ab, before_turn=turn_no) for ab in _abouts}
    if _readings:                                            # Phase 3: the receipt from readings
        new_affect, impact = receive(rested, _readings, profile, targets=targets, repeats=_repeats, present=_here)
    else:
        new_affect = appraise(rested, applied, profile, targets=targets, repeats=_repeats, present=_here)
        impact = sum(abs(new_affect[p] - rested[p]) for p in PATHS)
    _heights = {}
    for _r in _readings:
        _heights[_r.path] = max(_heights.get(_r.path, 0.0), rungs.height_of(_r.path, rungs.index_of(_r.path, _r.rung)))
    # THE CONDITION MOVES (gate condition-flow) - scripts/scene.py's rule: the turn's minutes and its impact,
    # committed with the turn, applied once the arc has read the condition the turn met.
    _cond_next = None
    if "condition_flow" in _sys:
        _cap = (_body.capacity(char, _injuries.weakening(led.con, run_id, actor, char, turn_no) if "injuries" in _sys
                               else 0) if "body" in _sys else 1.0)   # the body, weakened while hurt (gate injury-weakens)
        _cond_next = _condition.spend(char["current"]["condition"], minutes, impact, new_affect, 1.0 / _cap)
        if "body" in _sys:
            _cond_next = _body.exert(_cond_next, tags.get("exertion"), minutes, _cap)
    # ---- bonds: the chair has exactly ONE perceiver, and if a PERSON did this, they re-read them ----
    # RUNS BEFORE THE COMMIT, and that placement is the whole repair. This block used to sit AFTER
    # `led.append_turn`, so `deltas` and `view` were computed for a turn already written and were
    # persisted NOWHERE: the edge moved in memory, printed a BOND line, and was gone at process
    # exit. record-contract.md puts relationship-delta writes on the CAUSING turn's commit — which
    # is also why appending them afterwards would be wrong rather than merely late: a rolled-back
    # turn would leave orphan edge rows. `scripts/scene.py` has always had this ordering; the chair
    # did not, and was the last half of that repair still open.
    #
    # No perception check here (unlike scene.py): this character demonstrably registered the
    # circumstance — they acted on it, `assemble` already ran the percept gate over the event text,
    # and it is their OWN tags being read. relationships.md wants the update to run on what the
    # perceiver BELIEVES happened, so their reading is the thing the doc asks for, not a substitute.
    rel_deltas, bond_line, rest_rows, _cliff_lines = [], None, [], []
    if by:
        # `applied["target"]` comes from resolve_subject, which validates the named subject against
        # the actor's EDGES — so it can never resolve to the actor THEMSELVES, and "Joss took the
        # basket from ME" would read as a bystander's view of a stranger's business. The raw tag is
        # what carries that, so read it here: an act the character reports as being about them IS
        # aimed at them, which is what makes the second order fire.
        raw_subject = str((tags or {}).get("subject", "") or "").strip().lower()
        # THE SEAT'S OBJECT (bond-arithmetic.md s5): `self` names the actor themselves; a person's
        # name resolves through act_from_tags's own object read; the raw-subject workaround stays
        # for the actor's self-tagged form.
        _obj = str((tags or {}).get("object", "") or "").strip().lower()
        _self = _obj == "self" or raw_subject in (actor, str(char["fixed"].get("id", actor)).lower())
        _held = _connection.held_map(char)                # gate 5: her held things, one map for stake and received
        bact = bonds.act_from_tags(dict(applied, target=actor, object=actor) if _self else applied, by, actor, held=_held)
        if bact:
            bmodel = char["baseline"].get("model", {})
            priors = char["baseline"].get("relationship_priors", {})
            rels = char["current"].setdefault("relationships", {})
            # born whole at the stranger's rest (bond_rest.whole, 2026-09-19): an edge the sheet never
            # authored starts at `default_trust`, not .50 — the same read floor.bond_moves makes
            edge = bond_rest.whole(rels.get(by), priors)
            # STAKE and RATES off the perceiver's own sheet (bond-arithmetic.md s5/s6, gate 4) — the
            # same two reads floor.bond_moves makes for each witness of a scene beat.
            stake = bonds.stake_of(actor, bact["object"], rels, held=_held)
            rates = bonds.rates_of(priors)
            deltas = bonds.observe(edge, bact, bmodel, stake=stake, rates=rates)
            view = bonds.reflect(edge, bact, bmodel, rates=rates, stake=stake)
            cliffs = bonds.cliff_axes(edge, bact, bmodel) if deltas else ()
            if deltas or view:
                if deltas:
                    edge = bonds.apply_deltas(edge, deltas)
                if view:
                    edge = bonds.apply_reflection(edge, view)
                rels[by] = edge
                # A CLIFF MOVES THE REST: an append-only row on this turn's commit (bond_rest.py).
                if cliffs:
                    rest_rows = bond_rest.cliff_rows(actor, by, edge, cliffs,
                                                     bond_rest.resolve(bond_rest.rows_for(led.con, run_id, actor), priors, by))
                    _cliff_lines = ["  CLIFF  : %s -> %s  %s rests at %.3f from here" % (actor, by, ax, edge.get(ax, 0.0))
                                    for ax in cliffs]
                rel_deltas = (
                    [RelationshipDelta(perceiver=actor, target=by, axis=ax, delta=d, order="first",
                                       object=str(applied.get("object") or ""))
                     for ax, d in sorted(deltas.items())]
                    + [RelationshipDelta(perceiver=actor, target=by, axis=ax, delta=d, order="second",
                                         object=str(applied.get("object") or ""))
                       for ax, d in sorted(view.items())])
                bond_line = "  BOND   : %s -> %s  %s%s" % (
                    actor, by, "  ".join("%s %+0.3f" % (a, d) for a, d in sorted(deltas.items())),
                    ("   | reads them as: " + "  ".join("%s %+0.3f" % (a, d)
                                                        for a, d in sorted(view.items()))) if view else "")
    # THE ACCOUNT MOVES ON A TRANSFER (s6, 2026-09-18): the seat's `transfers`, priced once per pair by
    # `bonds.debt_postings` from the words and the accounts. The chair holds ONE sheet: a posting under
    # this character's name lands on their edge; one under `by`'s name is written as a row for a scene
    # with that sheet to fold (the account it reads for `repaid` is this character's own, the only one here).
    _present = [actor] + [x for x in _roster if x != actor]
    _accounts = {actor: {t: float((e or {}).get("debt", 0.0) or 0.0)
                         for t, e in (char["current"].get("relationships") or {}).items() if isinstance(e, dict)}}
    _posts = bonds.debt_postings(applied, str(by or actor), _accounts, present=_present)
    for _p, _t, _entry, _d, _cause in _posts:
        rel_deltas.append(RelationshipDelta(perceiver=_p, target=_t, axis="debt", delta=_d, order="first",
                                            object=str(applied.get("object") or ""), cause=_cause))
        if _p == actor:
            _srels = char["current"].setdefault("relationships", {})
            # a posting on an edge the chair does not yet hold births it whole at the stranger's rest
            _srels[_t] = bonds.apply_deltas(bond_rest.whole(_srels.get(_t), char["baseline"].get("relationship_priors", {})), {"debt": _d})
        _cliff_lines.append("  BOND   : %s %s %s  debt %+0.3f  — %s" % (_p, "owes" if _entry == "gave" else "repaid", _t, _d, _cause or "(unnamed)"))

    if not stub and LAST_USAGE.get("model"):        # token accounting — see LAST_USAGE above
        led.log_llm_call(run_id, turn_no, "act", LAST_USAGE["model"],
                         LAST_USAGE.get("tokens_in"), LAST_USAGE.get("tokens_out"))
    # THE TWO NEW TIERS, MIRRORING scene.py, and computed BEFORE the commit so the deltas ride
    # append_turn's own transaction rather than a separate post-commit call a crash can lose.
    # Both drivers are first-class (CLAUDE.md Modes), write to the same chronicle, and must not
    # produce different durable consequences for the same beat.
    _applied = tags if isinstance(tags, dict) else {}
    _dims = _applied.get("dimensions") or {}
    _res = arc.derive_resilience(char, char["current"].get("condition", {}))
    _wounds = char["baseline"].get("wounds") or []                 # engine wounds (gate three)
    wound_deltas = []
    _cue = {"about": applied.get("target"), "surfaces": packet["manifest"].get("surfaces") or [],
            "heights": _heights}
    for _w in _wounds:
        if not isinstance(_w, dict) or not str(_w.get("id", "")).strip():
            continue
        _cue_w = dict(_cue, about=wound.about_for(_w, _readings) or _cue["about"])
        _d = wound.trial(_w, _dims, _res, _cue_w)
        if _d:
            wound_deltas.append(WoundDelta(char_id=actor, wound_id=str(_w["id"]),
                                           delta=_d, kind="event", source=event_text[:200]))
    _durable = (_applied.get("durability") == "durable"
                or any(float(v) >= arc._DURABLE_DIM for v in _dims.values()))
    wound_mints = wound.mint(char, _heights, targets, _durable,
                             surfaces=packet["manifest"].get("surfaces") or [], text=event_text,
                             turn=turn_no) if "wounds" in _sys else []
    # RULE 5 LAST — see scripts/readalong.py: it decides what carries forward, after the mint.
    targets = _targets.bind_readings(targets, [], temperament=temperament, affect=new_affect)
    char["current"]["targets"] = dict(targets)
    target_binds = _targets.binds_from(_before_targets, targets)
    toward_deltas = []
    _subj = _applied.get("subject") or _applied.get("target")
    if _subj and "attitude" in _sys:
        for _prim, _td in toward.observe(_dims).items():
            toward_deltas.append(TowardDelta(perceiver=actor, target=str(_subj),
                                             primary=_prim, delta=_td, source=event_text[:200]))
    # THE SECOND FEED (gate toward-from-readings, 2026-09-11) — the same line scene.py carries, so
    # a beat produces the same history whichever driver ran it (tests/test_toward.py [8]).
    _durable = str(_applied.get("durability") or "").lower() == "durable"
    for _who, _path, _td in (toward.observe_readings(_readings, me=actor, profile=profile, durable=_durable)
                             if "attitude" in _sys else ()):
        toward_deltas.append(TowardDelta(perceiver=actor, target=str(_who), primary=_path,
                                         delta=_td, source=str(turn.get("action", ""))[:200]))
    # ONE ROW PER (perceiver, target, path) PER TURN — the table's UNIQUE contract. The two feeds
    # can price the same person on the same path in one beat; summed here, never side by side
    # (the first beat with both feeds live rolled back on exactly that, 2026-09-11).
    toward_deltas = toward.coalesce(toward_deltas)
    led.append_turn(TurnCommit(
        run_id=run_id, turn=turn_no, actor=char["fixed"]["name"].lower(),
        thought=str(turn["thought"]), action=str(turn["action"]),
        tags=tags if isinstance(tags, dict) else {}, affect=dict(new_affect),
        condition=dict(_cond_next or char["current"]["condition"]), validation=validation,
        wound_deltas=wound_deltas, toward_deltas=toward_deltas, wound_mints=wound_mints,
        events=[Event(type=str(tags.get("type", "mundane")),
                      payload={"text": event_text, "dimensions": tags.get("dimensions", {}),
                               "durability": tags.get("durability", "transient"),
                               "subject": target, "subject_group": target_group,
                               # the seat's read rides the event as it does in scene.py (gate 3 / quote check)
                               "object": str(tags.get("object") or ""), "showed": dict(tags.get("showed") or {}),
                               "quotes": dict(tags.get("quotes") or {}), "transfers": list(tags.get("transfers") or []),
                               "told": list(tags.get("told") or [])},
                      target=target,          # THE SUBJECT. Omitted at every Event site until 2026-08-30, so
                                              # ledger._project's `victim = ev['target'] or ev['actor']` always
                                              # fell through and a terminal harm marked the ACTOR dead, never the
                                              # person harmed; the betray/bond branch was unreachable entirely.
                      actor=char["fixed"]["name"].lower())],
        manifest=packet["manifest"], recall=packet["recall_refs"], rel_deltas=rel_deltas,
        utterances=claims.spoken(str(turn["action"])), target_binds=target_binds,
        readings=list(_readings), lands_on=list(_lands), rest_rows=rest_rows))
    if toward_deltas:
        # THE ATTITUDE MOVES WITHIN A SESSION (gate chair-parity, 2026-09-23). scripts/scene.py folds after
        # every live commit; this driver folded only on --resume, so a chair session's attitude stayed
        # where the session opened, whatever the character lived through in it.
        passage.fold_toward(led.con, run_id, actor, char)
    if _seat_notes:
        print("  SEATS  : " + " | ".join(_seat_notes))
    # NEVER TRUNCATE - the operator log's silent slice gave no sign a line was cut.
    print("\n  ACTION : %s" % str(turn["action"]).replace("\n", " "))
    print("  THOUGHT: %s" % str(turn["thought"]).replace("\n", " "))
    print("  TAGS   : %s %s [%s]  valid=%s conf=%.2f%s" % (
        tags.get("type", "?"), json.dumps(applied.get("dimensions", {})), tags.get("durability", "?"),
        validation["ok"], validation["confidence"],
        "  ** ESCALATE: %s" % "; ".join(render_flag(f) for f in validation["flags"]) if validation["escalate"] else ""))
    if target is not None:                          # who the event was about + the class regard scoped by
        print("  SUBJECT: %s%s" % (target, ("  [%s]" % target_group) if target_group else "  [unregarded]"))
    if bond_line:                                   # computed above, printed here — the transcript order is unchanged
        print(bond_line)
    for _ln in _cliff_lines:
        print(_ln)
    if toward_deltas:                               # read back from the FOLDED sheet, as scene.py prints it
        _tw = char["current"].get("toward") or {}
        print("  TOWARD : %s" % ", ".join("%s %s" % (w, " ".join("%s%+0.3f" % (k, v) for k, v in sorted((_tw.get(w) or {}).items())))
                                        for w in sorted({t.target for t in toward_deltas})))
    # (faithfulness is enforced pre-commit by faithful_turn above — a committed turn is leak-free by construction)

    # ---- the arc engine: a durable event moves the BASELINE (who they now are), persists, evolves char ----
    if wound_deltas or wound_mints:                       # the commit held: the sheet follows the log
        passage.fold_wounds(led.con, run_id, actor, char)   # the fold keeps each opening's fade (gate erosion-derived-at-replay)
        profile = build_profile(char)
        for _m in wound_mints:
            print("  SCAR   : %s on %s at %.2f" % (_m["concept"], _m["path"], _m["intensity"]))
    diff = arc.assess(applied, impact, char, char["current"]["condition"], heights=_heights) if "arc" in _sys else None
    if diff:
        char = arc.apply(char, diff)
        led.append_arc_diff(run_id, actor, turn_no, diff)
        profile = build_profile(char)              # re-derive from the evolved baseline
        m = diff.get("_meta", {})
        # No `relationships` term: `arc.assess` has not emitted that block since bonds.py took
        # edges (src/engine/arc.py documents the branch in `apply` as replay-only, kept for stored
        # pre-v8 diffs). The clause was always empty and read as though the arc still moved edges.
        moved = (list(diff.get("temperament", {}))
                 + ["regard.%s" % g for g in diff.get("regard", {})])
        print("  ARC    : durable (%s, impact %.2f) -> baseline moved: %s" % (m.get("dominant", "?"), m.get("impact", 0.0), ", ".join(moved)))
    if _cond_next is not None:                     # the turn's cost lands (condition flow)
        char["current"]["condition"] = _cond_next

    # acquisition: a durable, subject-bearing turn becomes a recallable belief in the actor's vault
    # (knowledge-model.md). The ENGINE reads the committed turn — never the model's introspection;
    # provenance 'lived' marks it apart from an authored .md seed. Folds forward now so the next turn's
    # recall gate can surface it; persisted to the ledger for the record.
    # GATED — see scripts/scene.py: a refused self-report must not become a permanent memory.
    acquired = acquisition.assess(applied, tags, char, world) if validation["ok"] else None
    if acquired:
        char["current"].setdefault("vault", []).append(acquired)
        acquisition.fold_vault(char["current"]["vault"])
        led.append_acquisition(run_id, actor, turn_no, acquired)
        print("  LEARNED: %s  (%s)" % (str(acquired["claim"])[:120], acquired["provenance"]))
    return new_affect, True, char, profile


def show_status(led, run_id, char, affect, temperament):
    n = led.con.execute("SELECT COUNT(*) c FROM turns WHERE run_id=?", (run_id,)).fetchone()["c"]
    esc = led.con.execute("SELECT COUNT(*) c FROM turns WHERE run_id=? AND "
                          "json_extract(validation,'$.escalate')=1", (run_id,)).fetchone()["c"]
    skipped = led.con.execute("SELECT COUNT(*) c FROM events WHERE run_id=? AND type='turn-skipped'",
                              (run_id,)).fetchone()["c"]
    print("\n  run=%s  turns=%d  escalations=%d  skipped=%d" % (run_id, n, esc, skipped))
    # BOTH halves are stage directions — second-person instructions to act — so neither takes a
    # "They are" frame. It printed "They are you do what is asked and none of the extra", the same
    # shape `prompt.py` :49 records fixing for the affect halves ("You are you can do the thorough
    # version where it matters") and missed here because this is an operator print, not the prompt.
    _cond = direct_condition(char["current"]["condition"])        # "" when the book runs no condition system
    print("  %s — %s%s." % (char["fixed"]["name"], rung_summary(affect), ("; " + _cond) if _cond else ""))


def _parse_chair_at(raw):
    """`--at`'s CLI text -> `clock.parse_at`'s {day, time} shape. A driver reshaping its own argv
    into the engine's typed input, same as every other flag here — `clock.parse_at` still does
    every actual check (range, shape, by name) and this does not repeat any of it.

    Accepts the JSON object a scene cfg's `at` field already carries ('{"day": 1, "time": "09:30"}'
    — "the same JSON shape scene cfgs use"), or the plain shorthand a human types at a prompt:
    "day N HH:MM" or bare "N HH:MM"."""
    text = raw.strip()
    if text.startswith("{"):
        try:
            at = json.loads(text)
        except ValueError as e:
            raise SystemExit("--at %r is not valid JSON: %s" % (raw, e))
        return _clock.parse_at(at)
    if text[:4].lower() == "day ":
        text = text[4:].strip()
    parts = text.split()
    if len(parts) != 2:
        raise SystemExit(
            "--at %r is not \"day N HH:MM\", \"N HH:MM\", or the JSON {day, time} shape scene "
            "cfgs use" % (raw,))
    day_txt, time_txt = parts
    try:
        day = int(day_txt)
    except ValueError:
        raise SystemExit("--at %r: %r is not a day number" % (raw, day_txt))
    return _clock.parse_at({"day": day, "time": time_txt})


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
    Identical to `scripts/scene.py`'s copy — parity, not a shared import, for the same reason the
    two drivers' `--keeper` help text has always been maintained in both places rather than one.
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
    ap = argparse.ArgumentParser(description="the director's chair — place circumstance, read the life")
    ap.add_argument("--book", default=None, help="a REAL BOOK: a slug under $SWE_BOOKS, or a path to the book folder (world/, characters/, people/ notes). Books live in your vault, never in this repo")
    ap.add_argument("--vault", default=None, help="older spelling of --book (a path)")
    ap.add_argument("--char", required=True, help="character: note name (--vault) or fixture file stem (--book)")
    ap.add_argument("--stub", action="store_true", help="deterministic stand-in, no API")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--resume", default=None, help="run_id to continue")
    ap.add_argument("--fixture", default=None, help="an ENGINE TEST FIXTURE (ashford) — not a real book")
    ap.add_argument("--prompt-only", action="store_true", dest="prompt_only",
                    help="emit the turn prompt as JSON and exit — the act seam's outbound half. "
                         "Any model anywhere can consume this (docs/orchestration.md seam 1)")
    ap.add_argument("--turn-json", default=None, dest="turn_json",
                    help="a file holding {action, thought, tags, exit?, addressee?} (or '-' for "
                         "stdin) — the inbound half. The engine validates, appraises and commits it "
                         "through the SAME path a locally-generated turn takes, faithfulness wall "
                         "included. Requires a circumstance via --circumstance")
    ap.add_argument("--circumstance", default=None,
                    help="the placed circumstance for a --prompt-only / --turn-json turn")
    ap.add_argument("--brief", default=None,
                    help="what the scene needs from this character - the composer selects which of "
                         "their live emotions the beat is played on. Absent, the circumstance text "
                         "stands in; absent that too, selection falls back to the deterministic floor")
    ap.add_argument("--db", default=None, help="db path (default <book>/runs/<slug>.db)")
    ap.add_argument("--minutes-per-turn", type=float, default=0.0, dest="minutes_per_turn",
                    help="story minutes each placed circumstance takes (default 0: no decay between "
                         "turns inside this invocation — a beat has no duration; see --at for the "
                         "clock BETWEEN invocations, which is a separate knob)")
    ap.add_argument("--at", default=None,
                    help="when THIS INVOCATION opens: \"day N HH:MM\", \"N HH:MM\", or the JSON "
                         "{day, time} shape scene cfgs use. Declares the gap since the chair (or a "
                         "scene) last closed, through the SAME clock scene.py uses — drift, wound/"
                         "arc erosion, the toward vectors and emotion decay all age by it before "
                         "the first turn. Absent (default): no clock is declared, same as today —"
                         " --minutes-per-turn is still the only knob between this invocation's own beats")
    ap.add_argument("--lasts", default=None,
                    help="how long this invocation is authored to run: minutes, or \"90m\" / \"2h\" "
                         "/ \"1d\" sugar (clock.span_minutes). Only meaningful with --at; a lulled "
                         "remainder is owed to whichever session opens next")
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
    args = ap.parse_args()

    # BOUND ON BOTH BRANCHES. Only the --book arm assigned this, and the --turn-json call site
    # below reads it unconditionally, so every --fixture run through that path died with
    # UnboundLocalError before a turn was attempted. A fixture has no book directory and None is
    # the honest value: `record_faults` already reads it as "nowhere to write".
    book_dir = None
    book_spec = args.book or args.vault          # --vault is the older spelling of --book
    if bool(book_spec) == bool(args.fixture):
        raise SystemExit("pass exactly one of --book (a real book: slug or path) or --fixture (an engine test fixture)")
    if book_spec:
        from src.engine.vault import load_book
        from src.engine import vault
        try:
            book_dir = books.resolve(book_spec)
        except books.BookError as e:
            raise SystemExit(str(e))
        world, chars = load_book(book_dir)
        # THE BOOK ANSWERS FOR ITS OWN CAST. This restated the dict `load_book` had just returned.
        # The key is NORMALISED first and that is not cosmetic: `--char Mira` has to find `mira`,
        # and a first draft of this delegation passed the raw argument and broke exactly that.
        key = args.char.lower().replace(" ", "_")
        try:
            char = vault.character_or_raise(chars, key)
            passage.stamp_authored(char)             # before anything moves it (gate erosion-derived-at-replay)
        except vault.VaultError as e:
            raise SystemExit(str(e))
        book_name = books.slug(book_dir)
        try:                                          # the chronicle lives WITH the book — enforced,
            default_db = books.assert_db_for_book(book_dir, args.db)   # not merely defaulted
        except books.BookError as e:
            raise SystemExit(str(e))
        args.db = None                                # already resolved above
    else:
        def find(folder, stem):
            try:                       # ONE copy of this search — lint_book.py carried the other
                return books.fixture_path(REPO, folder, stem, _FIXTURE_SUFFIXES, relative=True)
            except books.BookError as e:
                raise SystemExit(str(e))
        world = _load(find("world", args.fixture))
        char = _load(find("characters", args.char))
        passage.stamp_authored(char)             # before anything moves it (gate erosion-derived-at-replay)
        book_name = args.fixture
        default_db = os.path.join(REPO, "runs", "%s.db" % args.fixture)
    char_id = char["fixed"]["name"].lower()
    led = Ledger(args.db or default_db)

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
        # Compare the SAME shape the run pinned: `bible.build(led.con, world, chars)` below takes
        # the whole book's cast, so comparing {char_id: char} reported drift on every single
        # resume — a warning that always fires is noise, and it fired on an untouched book the
        # first time it ran. Guarded on `book_spec` for the same reason the pinning is: a
        # --fixture run has no bible to have drifted from.
        if book_spec:
            from src.engine import bible              # local, as everywhere else in this file
            _drift, _detail = bible.drifted(led.con, run_id, world, chars)
        else:
            _drift, _detail = False, ""
        if _drift:
            print("  [!] %s" % _detail)
            print("      earlier turns were computed from the pinned bible; later ones will not be.")
        char = passage.fold_arc(led.con, run_id, char_id, char)   # the arc AND each opening's fade, in order
        acquired = led.acquisitions_for(run_id, char_id)       # rehydrate the grown vault (lived memory)
        if acquired:
            char["current"].setdefault("vault", []).extend(acquired)
        from src.engine.acquisition import fold_vault
        char["current"]["vault"] = fold_vault(char["current"].get("vault", []))
        # EDGES — the chair writes none of its own (its TurnCommit is built before the tags are
        # read for bonds), but the SAME run may have played scenes, and those movements are this
        # character's. Reading is free correctness even while writing stays open.
        _moves = led.edge_deltas_for(run_id, char_id)
        # A pre-v28 run gets its authored rest rows at the resume turn (idempotent on a v28 run).
        bond_rest.seed(led.con, run_id, state["turn"] + 1, char_id, char["current"].get("relationships") or {})
        attachments.seed(led.con, run_id, state["turn"] + 1, char_id, char["current"].get("attachments") or {})
        # ORDERED REHYDRATE. This driver declares no elapsed of its own, but the SAME run
        # may have played scenes that did, and losing those was the defect.
        bond_rest.rehydrate(char["current"].setdefault("relationships", {}),
                            char["baseline"].get("relationship_priors", {}),
                            led.timeline_for(run_id, char_id),
                            attachments=char["current"].setdefault("attachments", {}))
        if _moves:                           # OPERATOR output, not the prompt — rule 5 is the prompt
            print("refolded %d edge movement(s) toward %s"
                  % (len(_moves), ", ".join(sorted({m[0] for m in _moves}))))
        # THE WOUND TIER — the same refold, on the single-character driver. Wiring only one of the
        # two drivers is indistinguishable from working until someone runs the other path.
        # THE MICRO TIER refolds here too. A test asserting both drivers refold caught this
        # missing, after a gate of mine had CLAIMED it was already wired — the claim was written
        # from intent rather than from the file.
        # ABOUTNESS refolds here too, and it was the one accumulating tier this block did not
        # replay — measured 2026-09-06, arc/vault/edges/toward/wounds all did and targets did not,
        # so a character resumed with whatever the sheet authored (`{}` in every book on disk).
        _tbinds = _targets.binds_for(led.con, run_id, char_id)
        _targets.replay(char, _tbinds)
        if _tbinds:                          # OPERATOR output, not the prompt — rule 5 is the prompt
            print("refolded %d aboutness bind(s) on %s"
                  % (len(_tbinds), ", ".join(sorted(char["current"].get("targets") or {})) or "nothing"))
        _tmoves = led.toward_deltas_for(run_id, char_id)
        passage.fold_toward(led.con, run_id, char_id, char)
        if _tmoves:
            print("refolded %d micro movement(s) toward %d person(s)"
                  % (len(_tmoves), len({m[0] for m in _tmoves})))
        _wmoves = led.wound_deltas_for(run_id, char_id)
        passage.fold_wounds(led.con, run_id, char_id, char)   # mints, deltas and the fade, in log order
        if _wmoves:
            print("refolded %d wound movement(s) on %s"
                  % (len(_wmoves), ", ".join(sorted({m[0] for m in _wmoves}))))

        # ON THE SHEET, not only in the local: open_scene below reads and decays the sheet, and the
        # refresh after it copied the decayed AUTHORED mood over a restore that lived only here
        # (gate resume-and-parity, 2026-09-22). Condition is restored with it.
        passage.restore_latest(char, led.latest_affect(run_id, char_id))
        affect = dict(char["current"]["affect"])
        turn_no = state["turn"] + 1
        print("resumed %s at turn %d (determinism OK)" % (run_id, state["turn"]))
    else:
        # uuid suffix: int(time.time()) alone collides for two runs started in
        # the same second (sqlite3.IntegrityError on runs.run_id — hit 2026-07-24
        # batching --stub turns in a shell loop). The timestamp stays for
        # sortability; the suffix carries uniqueness.
        run_id = "directed-%s-%d-%s" % (book_name, int(time.time()), uuid.uuid4().hex[:6])
        cfg = {"catalog_version": 1,
               "models": {"turn": "stub" if args.stub else args.model},
               "prompt_versions": {"turn": 1}}
        if book_spec:                      # pin WHAT THIS RUN RAN AGAINST (bible.py)
            from src.engine import bible
            cfg[bible.CONFIG_KEY] = bible.build(led.con, world, chars)
        led.create_run(run_id, cfg)
        led.register_character(run_id, char_id, char["fixed"], char["baseline"])
        # where each authored edge RESTS, as rows the fold can read back (schema v28, gate 4)
        bond_rest.seed(led.con, run_id, 0, char_id, char["current"].get("relationships") or {})
        attachments.seed(led.con, run_id, 0, char_id, char["current"].get("attachments") or {})   # what they hold (v30, gate 5)
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
        affect = dict(char["current"]["affect"])
        turn_no = 0
        print("new chronicle: %s" % run_id)

    # ONE CLOCK, TWO DRIVERS (src/engine/passage.py, gate driver-clock-parity, 2026-09-19). Before
    # this, the chair declared no elapsed of its own — a chair session resumed after scenes had
    # played applied no drift, no wound/arc erosion and wrote no clock row however long it was said
    # to be later, while scene.py ran the identical arithmetic every scene. `start_turn` is pinned
    # here, BEFORE the REPL can move `turn_no`, so the keeper hook below can tell what this
    # invocation itself committed.
    start_turn = turn_no
    # WHICH SYSTEMS THIS BOOK RUNS (gate systems-registry): an off system's block emptied after the resume
    # folded the log back on and before the opening reads the sheet - the scene driver's point exactly.
    _systems.strip(char, _systems.for_book(world))
    if "condition_flow" in _systems.for_book(world):      # a sheet the flow cannot move is refused now
        try:
            _condition.require(char)
            if "body" in _systems.for_book(world):
                _body.require(char)
                char["current"]["condition"] = _condition.split(char["current"]["condition"])   # gate energy-reserves
        except RecordError as e:
            raise SystemExit("condition flow: %s" % e)
    if args.at:
        _at_minutes = _parse_chair_at(args.at)
        _lasts_minutes = _clock.span_minutes(args.lasts) if args.lasts else None
        # THE CHAIR HAS NO FIXED BUDGET (a REPL, or one beat under --prompt-only/--turn-json) —
        # budget=1 collapses `per_beat` to `lasts_minutes` itself, the same arithmetic a single-beat
        # scene already gets (passage.open_scene's own contract).
        _clock_result = passage.open_scene(led, run_id, start_turn, _at_minutes, _lasts_minutes, 1,
                                           {char_id: char}, names=None,
                                           flow="condition_flow" in _systems.for_book(world),
                                           body="body" in _systems.for_book(world),
                                           injuries="injuries" in _systems.for_book(world))
        # `affect` is THIS driver's own cache beside the sheet (set above, from either branch) —
        # open_scene mutates `char["current"]["affect"]` and knows nothing of the cache, so it is
        # refreshed here or the first turn below reads the pre-decay value.
        affect = dict(char["current"]["affect"])
        if _clock_result["elapsed"]:
            print("\n  %s minutes since the last scene ended%s — edges relaxed toward each character's"
                  " resting disposition, feelings toward their rest" % (
                      int(_clock_result["elapsed"]),
                      " (+%d owed by the last scene)" % int(_clock_result["owed"]) if _clock_result["owed"] else ""))
    else:
        print("chair: no --at given — running on --minutes-per-turn only (no scene clock declared)")

    profile = build_profile(char)
    temperament = char["baseline"]["temperament"]
    groups_index = subject_groups(world)            # entity -> class, built once (the subject's regard key)
    recent = []
    # THE RESOLVED DIRECTORY, NOT THE CLI SPELLING. `args.vault` is the older alias and is None
    # for every run that said --book, so this wrote world-faults.md for nobody.
    record_faults(startup_faults(char, world), book_dir)
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
    if char_id not in _known:
        led.register_character(run_id, char_id, char["fixed"], char["baseline"])
        bond_rest.seed(led.con, run_id, turn_no, char_id, char["current"].get("relationships") or {})
        attachments.seed(led.con, run_id, turn_no, char_id, char["current"].get("attachments") or {})
        print("registered late-joining cast member: %s" % char_id)

    # THE SWEEP IS PRINTED, NOT RAISED, AND NOT RESUME-GATED. Unlike `bible.drifted`, which
    # has nothing pinned to compare on a new run, the DANGEROUS case here IS the new run: a
    # fresh run_id written into a database that lost 50 of its 68 walls on migration and
    # never said so.
    print(integrity.startup_line(led.con))
    show_status(led, run_id, char, affect, temperament)
    # THE ACT SEAM: one turn, non-interactive, in or out. Placed before the REPL so a harness
    # never has to speak the REPL's language — argv in, stdout out, exit code.
    if args.prompt_only or args.turn_json:
        if not args.circumstance:
            raise SystemExit("--prompt-only and --turn-json need --circumstance '<what happened>'")
        supplied = None
        if args.turn_json:
            raw = (sys.stdin.read() if args.turn_json == '-'
                   else open(args.turn_json, encoding='utf-8').read())
            try:
                supplied = json.loads(raw)
            except ValueError as e:
                raise SystemExit('--turn-json is not valid JSON: %s' % e)
        try:
            # the same minutes and brief the REPL passes (gate chair-parity): the one-shot seam used to
            # decay nothing and hand the composer no brief
            affect, ok, char, profile = run_turn(
                led, run_id, char, world, groups_index, profile, temperament, affect, turn_no,
                args.circumstance, [], args.model, args.stub, book_dir=book_dir,
                supplied=supplied, prompt_only=args.prompt_only,
                minutes=args.minutes_per_turn, brief=(args.brief or args.circumstance or ""))
        except ValueError as e:
            raise SystemExit(str(e))
        if args.turn_json:
            print('committed' if ok else 'REFUSED — recorded as turn-skipped')
            led.set_status(run_id, 'parked')
        return 0 if (ok or args.prompt_only) else 1

    print("\nplace a circumstance (plain text), or: status | quit\n")

    for line in sys.stdin:
        cmd = line.strip()
        if not cmd:
            continue
        if cmd.lower() == "quit":
            break
        if cmd.lower() == "status":
            show_status(led, run_id, char, affect, temperament)
            continue
        if cmd.lower().startswith("reveal "):           # director stages a name-reveal: "reveal <entity_id> <name>"
            parts = cmd.split(None, 2)
            if len(parts) < 3:
                print("  usage: reveal <entity_id> <name>")
                continue
            belief = acquisition.reveal_name(char, parts[1], parts[2], world)
            if belief:
                led.append_acquisition(run_id, char_id, turn_no, belief)
                print("  REVEAL : %s now known to %s as %r — %s" % (parts[1], char_id, parts[2], belief["claim"]))
            else:
                print("  (no %r in %s's relationships — reveal skipped)" % (parts[1], char_id))
            continue
        by = None                                       # "by:<entity_id> <text>" — WHO did this circumstance
        if cmd.lower().startswith("by:"):
            head, _, rest = cmd.partition(" ")
            by = head[3:].strip()
            if by not in (char["current"].get("relationships") or {}) and                     by not in {p.get("id") for p in (world.get("people") or []) if isinstance(p, dict)}:
                print("  (no %r in %s's relationships or world.people — name an entity that exists)" % (by, char_id))
                continue
            cmd = rest.strip()
            if not cmd:
                print("  usage: by:<entity_id> <what they did>")
                continue
        _brief = (args.brief or args.circumstance or "")
        affect, ok, char, profile = run_turn(led, run_id, char, world, groups_index, profile, temperament, affect,
                                             turn_no, cmd, recent, args.model, args.stub, book_dir=book_dir, by=by,
                                             minutes=args.minutes_per_turn, brief=_brief)
        temperament = char["baseline"]["temperament"]   # re-bind: the arc may have moved the baseline
        if ok:
            recent.append(cmd)
            turn_no += 1
        print("\n  now: %s\n" % rung_summary(affect))

    keeper_ran = _keeper_runs(args.stub, args.keeper, args.keeper_off) and turn_no > start_turn
    if keeper_ran:
        # THE CANON GATE (2026-09-11 on scene.py; parity here 2026-09-19): the chair's own claims
        # are ruled on before the run is parked, exactly as scripts/scene.py's site does. DEFAULT ON
        # for a non-stub invocation since 2026-09-19 (owner decision D1, gate lore-licence-visible;
        # see _keeper_runs above) — --no-keeper opts out; --keeper stays accepted and still forces
        # the gate to run under --stub, unchanged from before. Gated on turn_no > start_turn the
        # same way scene.py gates on prompt_only above it — nothing was acted, nothing to rule on.
        # LOCAL IMPORT — see the module-scope comment by the other imports for why (keeper -> critic
        # -> direct is a circular import if this module imports keeper at the top).
        import keeper as _keeper
        # `world=world` (2026-09-19, gate keeper-attachment-rubric): the third writer of a hold
        # needs the bible to check a claim's object against — see attachments.names_for.
        _keeper.canon_gate(led, run_id, start_turn, turn_no - 1, _provider.seat_model(), args.stub, world=world)

    led.persist_snapshot(run_id, max(turn_no - 1, 0), led.fold(run_id, max(turn_no - 1, 0)))
    led.set_status(run_id, "parked")
    print(faults.render(faults.scan_run(led, run_id)))   # engine-faults: recurring vocab/representation gaps (the world-fault twin)
    _report_lore(led, run_id, keeper_ran, args.stub)
    src_arg = ('--vault "%s"' % args.vault) if args.vault else ("--book %s" % args.book)
    print("parked %s at turn %d — resume with: python scripts/direct.py %s --char %s%s --resume %s" % (
        run_id, turn_no - 1, src_arg, args.char, " --stub" if args.stub else "", run_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
