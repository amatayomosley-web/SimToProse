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

from src.engine.scene import assemble, resolve_subject, subject_groups   # noqa: E402
from src.engine import books   # module scope: BOTH the --book and --fixture branches use it
from src.engine import decay as _decay   # recall history fold — see run_turn's assemble call
from src.engine import clock as _clock   # declared story-time elapsed, same call
from src.engine.severity import normalise_dimensions           # noqa: E402
from src.engine.prompt import build_turn_messages                  # noqa: E402
from src.engine.consolidation import (validate_tags, CATALOG, TagError, tag_refusal,
                                       render_flag)        # noqa: E402
from src.engine import integrity                              # noqa: E402
from src.engine.state import build_profile, appraise, decay        # noqa: E402
from src.engine.targets import retarget                            # noqa: E402  (per-primitive aboutness)
from src.engine.direction import direct_affect, direct_condition   # noqa: E402
from src.engine.ledger import Ledger                               # noqa: E402
from src.engine.records import (Event, TurnCommit, RelationshipDelta, PRIMARIES,
                                WoundDelta, TowardDelta)  # noqa: E402
from src.engine import arc                                         # noqa: E402  (the arc engine)
from src.engine import bonds                                       # noqa: E402  (the relationship tier)
from src.engine import levers                                      # noqa: E402  (the wound refold on resume)
from src.engine import wound                                       # noqa: E402  (the wound tier's mover)
from src.engine import toward                                      # noqa: E402  (the MICRO tier)
from src.engine import acquisition                                 # noqa: E402  (the vault-growth engine)
from src.engine import faithfulness                                # noqa: E402  (name-leak detector)
from src.engine import faults                                      # noqa: E402  (the engine-fault detector)

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
    import urllib.request
    key = None
    with open(_env_path(), encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"\s*OPENROUTER_API_KEY\s*=\s*(\S+)", line)
            if m:
                key = m.group(1).strip().strip('"').strip("'")
    body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                 headers={"Authorization": "Bearer %s" % key, "Content-Type": "application/json"})
    import urllib.error
    with urllib.request.urlopen(req, timeout=120) as r:
        body = json.load(r)
    usage = body.get("usage") or {}
    LAST_USAGE.clear()
    LAST_USAGE.update({"model": model,
                       "tokens_in": usage.get("prompt_tokens"),
                       "tokens_out": usage.get("completion_tokens")})
    return body["choices"][0]["message"]["content"]


# TOKEN ACCOUNTING. `Ledger.log_llm_call` existed with exactly one caller — a test — so `llm_calls`
# was empty on every real run and guide-operating.md's documented spend query returned nothing. Both
# dispatchers already RECEIVE the counts in the response body and threw them away. Captured here for
# the caller that holds the ledger; the engine still never calls a model (CLAUDE.md rule 3).
LAST_USAGE = {}

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
    between beats. The OOM that dogged the dinner (ggml.c:1558 mem_buffer NULL -> runner crash -> HTTP 500;
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


def llm_turn(packet, event_text, temperament, model, stub, think=True, seed=None, relationships=None, corrections=None, acts=()):
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
    messages = build_turn_messages(packet, event_text, temperament, relationships, acts=acts)
    if corrections:                                                  # faithful_turn appends corrective turns on a name-leak retry
        messages = list(messages) + list(corrections)
    if model.startswith("ollama/"):                                  # local on-disk dispatch (free, pinned)
        return _parse_reply(_ollama(messages, model[len("ollama/"):], think=think, seed=seed))
    return _parse_reply(_openrouter(messages, model))


def faithful_turn(packet, event_text, temperament, model, stub, think=True, seed=None, relationships=None, max_retries=2, acts=(), information=None, char_id=None):
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
        turn = llm_turn(packet, event_text, temperament, model, stub, think=think, seed=s, acts=acts,
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
        with open(path, "a", encoding="utf-8") as fh:
            if new:
                fh.write("# World Faults\n\nThe sim reached for world that does not exist yet. Each box = a\n"
                         "world-building pass to run (docs/guide-content.md §world-building pass).\n\n")
            for f in faults:
                fh.write("- [ ] %s\n" % f)


# ---- the chair ----

def run_turn(led, run_id, char, world, groups_index, profile, temperament, affect, turn_no, event_text, recent, model, stub, book_dir=None, by=None, supplied=None, prompt_only=False):
    """One placed circumstance through the full spine. Returns (new_affect, ok, char, profile) —
    char/profile may be EVOLVED if the event wrote a durable baseline diff (the arc engine).

    `by` is the entity id of WHOEVER PERFORMED the circumstance, when a person performed it. It is
    AUTHORED by the director (`by:<id> <text>` at the REPL), never inferred — the same decision the
    laws' `act` made, for the same reason: a classifier reading "he takes the purse" and guessing
    which entity `he` is fails silently and poisons an edge instead of skipping it. Supplied, the
    character re-reads that person on their own tags; absent, no edge moves and the turn is
    unchanged."""
    scene_slice = {"event": {"text": event_text, "kind": "mundane"}, "recent": recent[-2:],
                   "location": char["current"].get("location")}
    # SLOPE as an assemble ARGUMENT, so the manifest can name it (see scene.assemble).
    _actor = char["fixed"]["name"].lower()
    # Recall decay needs the RUN's turn, not the character's — the ledger owns it. Until
    # 2026-09-04 none of these four reached the gate, so every recall ran at turn 0 with
    # no history and no elapsed time, i.e. no decay at all. fold_recall_history derives
    # {bid: {last_turn, count}} from the append-only decision_manifests table rather than
    # reading it off the belief, keeping "cause is logged once; effect is derived at
    # replay" (decay.py:30).
    packet = assemble(char, world, scene_slice, affect, char["current"]["condition"],
                      prev_affect=led.previous_affect(run_id, _actor, turn_no),
                      current_turn=turn_no,
                      relationships=char["current"].get("relationships", {}),
                      recall_history=_decay.fold_recall_history(led.con, run_id, _actor),
                      elapsed=_clock.elapsed_since(led.con, run_id, turn_no))
    record_faults(detect_world_faults(packet, scene_slice, event_text, world, turn_no), book_dir)
    actor = char["fixed"]["name"].lower()
    rels = char["current"].get("relationships", {})

    # THE ACT SEAM (docs/orchestration.md, unwired seam 1). `--prompt-only` emits exactly the
    # messages the engine would have sent; `--turn-json` hands a turn back. Between them, ANY model
    # anywhere can act a character and the chronicle cannot tell which one did — argv in, stdout
    # out, the one interface every harness shares. critic.py and narrate.py have had this pair since
    # the beginning; direct.py and scene.py, the two that ACT, had neither, which is why the
    # character-simulator agent could not do its job.
    if prompt_only:
        print(json.dumps(build_turn_messages(packet, event_text, temperament, rels), indent=2))
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
        print("  [supplied turn accepted for validation — %d char action]" % len(turn["action"]))
    else:
      try:
        # name hygiene rides in build_turn_messages: assemble saw RAW text (so pell->holloway resolves);
        # the PROMPT masks every name this actor never acquired (passed via relationships). faithful_turn
        # then REGENERATES on any name-leak the masking wall couldn't stop (latent weights leak) —
        # and, since 2026-09-01, on any tracked FACT the actor is not a knower of, because the wall
        # was name-shaped and not every secret is a name.
        turn, leaks = faithful_turn(packet, event_text, temperament, model, stub, seed=turn_no,
                                    relationships=rels,
                                    information=(led.fold(run_id, max(turn_no - 1, 0)) or {}).get("information"),
                                    char_id=actor)
      except Exception as exc:                       # degrade, never crash; no silent skips
        led.record_turn_skipped(run_id, turn_no, actor, str(exc))
        print("  [turn failed, recorded as turn-skipped: %s]" % str(exc)[:80])
        return affect, False, char, profile

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
    # THE SEVERITY SEAM. Resolve event-strength WORDS to floats on the existing 0..1 scale
    # before anything reads them, so validate_tags / appraise / wound / bonds / arc all see
    # exactly the float they always have (src/engine/severity.py). Floats pass through.
    tags = normalise_dimensions(turn["tags"])
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
    target, target_group = resolve_subject(packet["volatile"]["edges"], groups_index, named)
    if target is None and by:
        target = by
        target_group = (groups_index.get(by) or [None])[0]
    if target is not None:
        applied = dict(applied, target=target)
        if target_group is not None:
            applied["target_group"] = target_group
    # aboutness first, so this event's pushes bind the party the event was about
    targets = retarget(char["current"].get("targets") or {}, applied,
                       temperament=temperament, affect=affect, me=actor)
    char["current"]["targets"] = dict(targets)
    appraised = appraise(affect, applied, profile, targets=targets)
    impact = sum(abs(appraised[p] - affect[p]) for p in PRIMARIES)
    new_affect = decay(appraised, temperament, profile)
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
    rel_deltas, bond_line = [], None
    if by:
        # `applied["target"]` comes from resolve_subject, which validates the named subject against
        # the actor's EDGES — so it can never resolve to the actor THEMSELVES, and "Joss took the
        # purse from ME" would read as a bystander's view of a stranger's business. The raw tag is
        # what carries that, so read it here: an act the character reports as being about them IS
        # aimed at them, which is what makes the second order fire.
        raw_subject = str((tags or {}).get("subject", "") or "").strip().lower()
        bact = bonds.act_from_tags(
            dict(applied, target=actor) if raw_subject in (actor, str(char["fixed"].get("id", actor)).lower()) else applied,
            by, actor)
        if bact:
            bmodel = char["baseline"].get("model", {})
            rels = char["current"].setdefault("relationships", {})
            edge = rels.get(by, {})
            deltas = bonds.observe(edge, bact, bmodel)
            view = bonds.reflect(edge, bact, bmodel)
            if deltas or view:
                if deltas:
                    edge = bonds.apply_deltas(edge, deltas)
                if view:
                    edge = bonds.apply_reflection(edge, view)
                rels[by] = edge
                rel_deltas = (
                    [RelationshipDelta(perceiver=actor, target=by, axis=ax, delta=d, order="first")
                     for ax, d in sorted(deltas.items())]
                    + [RelationshipDelta(perceiver=actor, target=by, axis=ax, delta=d, order="second")
                       for ax, d in sorted(view.items())])
                bond_line = "  BOND   : %s -> %s  %s%s" % (
                    actor, by, "  ".join("%s %+0.3f" % (a, d) for a, d in sorted(deltas.items())),
                    ("   | reads them as: " + "  ".join("%s %+0.3f" % (a, d)
                                                        for a, d in sorted(view.items()))) if view else "")

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
    _wounds = (char["baseline"].get("drives") or {}).get("fears_wounds") or []
    wound_deltas = []
    for _w in _wounds:
        if not isinstance(_w, dict) or not str(_w.get("id", "")).strip():
            continue
        _d = wound.trial(_w, _dims, _res, packet["manifest"].get("surfaces") or [])
        if _d:
            wound_deltas.append(WoundDelta(char_id=actor, wound_id=str(_w["id"]),
                                           delta=_d, kind="event", source=event_text[:200]))
    toward_deltas = []
    _subj = _applied.get("subject") or _applied.get("target")
    if _subj:
        for _prim, _td in toward.observe(_dims).items():
            toward_deltas.append(TowardDelta(perceiver=actor, target=str(_subj),
                                             primary=_prim, delta=_td, source=event_text[:200]))
    led.append_turn(TurnCommit(
        run_id=run_id, turn=turn_no, actor=char["fixed"]["name"].lower(),
        thought=str(turn["thought"]), action=str(turn["action"]),
        tags=tags if isinstance(tags, dict) else {}, affect=dict(new_affect),
        condition=dict(char["current"]["condition"]), validation=validation,
        wound_deltas=wound_deltas, toward_deltas=toward_deltas,
        events=[Event(type=str(tags.get("type", "mundane")),
                      payload={"text": event_text, "dimensions": tags.get("dimensions", {}),
                               "durability": tags.get("durability", "transient"),
                               "subject": target, "subject_group": target_group},
                      target=target,          # THE SUBJECT. Omitted at every Event site until 2026-08-30, so
                                              # ledger._project's `victim = ev['target'] or ev['actor']` always
                                              # fell through and a terminal harm marked the ACTOR dead, never the
                                              # person harmed; the betray/bond branch was unreachable entirely.
                      actor=char["fixed"]["name"].lower())],
        manifest=packet["manifest"], recall=packet["recall_refs"], rel_deltas=rel_deltas))
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
    # (faithfulness is enforced pre-commit by faithful_turn above — a committed turn is leak-free by construction)

    # ---- the arc engine: a durable event moves the BASELINE (who they now are), persists, evolves char ----
    diff = arc.assess(applied, impact, char, char["current"]["condition"])
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
    print("  %s — %s; %s." % (char["fixed"]["name"],
                              direct_affect(affect, temperament),
                              direct_condition(char["current"]["condition"])))


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
    ap.add_argument("--db", default=None, help="db path (default <book>/runs/<slug>.db)")
    args = ap.parse_args()

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
        for diff in led.arc_diffs_for(run_id, char_id):       # rehydrate durable baseline evolution (the arc)
            char = arc.apply(char, diff)
        acquired = led.acquisitions_for(run_id, char_id)       # rehydrate the grown vault (lived memory)
        if acquired:
            char["current"].setdefault("vault", []).extend(acquired)
        from src.engine.acquisition import fold_vault
        char["current"]["vault"] = fold_vault(char["current"].get("vault", []))
        # EDGES — the chair writes none of its own (its TurnCommit is built before the tags are
        # read for bonds), but the SAME run may have played scenes, and those movements are this
        # character's. Reading is free correctness even while writing stays open.
        _moves = led.edge_deltas_for(run_id, char_id)
        # ORDERED REHYDRATE. This driver declares no elapsed of its own, but the SAME run
        # may have played scenes that did, and losing those was the defect.
        bonds.rehydrate(char["current"].setdefault("relationships", {}),
                        char["baseline"].get("relationship_priors", {}),
                        led.timeline_for(run_id, char_id))
        if _moves:                           # OPERATOR output, not the prompt — rule 5 is the prompt
            print("refolded %d edge movement(s) toward %s"
                  % (len(_moves), ", ".join(sorted({m[0] for m in _moves}))))
        # THE WOUND TIER — the same refold, on the single-character driver. Wiring only one of the
        # two drivers is indistinguishable from working until someone runs the other path.
        # THE MICRO TIER refolds here too. A test asserting both drivers refold caught this
        # missing, after a gate of mine had CLAIMED it was already wired — the claim was written
        # from intent rather than from the file.
        _tmoves = led.toward_deltas_for(run_id, char_id)
        toward.replay(char, _tmoves)
        if _tmoves:
            print("refolded %d micro movement(s) toward %d person(s)"
                  % (len(_tmoves), len({m[0] for m in _tmoves})))
        _wmoves = led.wound_deltas_for(run_id, char_id)
        levers.replay_wound_deltas(
            (char["baseline"].get("drives") or {}).get("fears_wounds") or [], _wmoves)
        if _wmoves:
            print("refolded %d wound movement(s) on %s"
                  % (len(_wmoves), ", ".join(sorted({m[0] for m in _wmoves}))))

        latest = led.latest_affect(run_id, char_id)
        affect = latest["affect"] if latest else dict(char["current"]["affect"])
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

    profile = build_profile(char)
    temperament = char["baseline"]["temperament"]
    groups_index = subject_groups(world)            # entity -> class, built once (the subject's regard key)
    recent = []
    record_faults(startup_faults(char, world), args.vault)
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
            affect, ok, char, profile = run_turn(
                led, run_id, char, world, groups_index, profile, temperament, affect, turn_no,
                args.circumstance, [], args.model, args.stub, book_dir=book_dir,
                supplied=supplied, prompt_only=args.prompt_only)
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
        affect, ok, char, profile = run_turn(led, run_id, char, world, groups_index, profile, temperament, affect,
                                             turn_no, cmd, recent, args.model, args.stub, book_dir=args.vault, by=by)
        temperament = char["baseline"]["temperament"]   # re-bind: the arc may have moved the baseline
        if ok:
            recent.append(cmd)
            turn_no += 1
        print("\n  now: %s\n" % direct_affect(affect, temperament))

    led.persist_snapshot(run_id, max(turn_no - 1, 0), led.fold(run_id, max(turn_no - 1, 0)))
    led.set_status(run_id, "parked")
    print(faults.render(faults.scan_run(led, run_id)))   # engine-faults: recurring vocab/representation gaps (the world-fault twin)
    src_arg = ('--vault "%s"' % args.vault) if args.vault else ("--book %s" % args.book)
    print("parked %s at turn %d — resume with: python scripts/direct.py %s --char %s%s --resume %s" % (
        run_id, turn_no - 1, src_arg, args.char, " --stub" if args.stub else "", run_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
