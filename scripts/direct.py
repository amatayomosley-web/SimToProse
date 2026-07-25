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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.scene import assemble, resolve_subject, subject_groups   # noqa: E402
from src.engine.prompt import build_turn_messages                  # noqa: E402
from src.engine.consolidation import validate_tags, CATALOG        # noqa: E402
from src.engine.state import build_profile, appraise, decay        # noqa: E402
from src.engine.direction import direct_affect, direct_condition   # noqa: E402
from src.engine.ledger import Ledger                               # noqa: E402
from src.engine.records import Event, TurnCommit, PRIMARIES        # noqa: E402
from src.engine import arc                                         # noqa: E402  (the arc engine)
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
        return json.load(r)["choices"][0]["message"]["content"]


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
    the param) never receive it. num_ctx 8192 gives gemma4's thinking trace room while keeping the KV cache
    small — the KV is a fixed, num_ctx-sized buffer Ollama allocates ONCE at load (server.log device.go:251),
    NOT a per-beat-growing thing; each beat is a fresh stateless /api/chat that refills it (scene memory is
    the ledger/vault, not the model KV). keep_alive is left at Ollama's default so the model stays warm
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
                           "num_ctx": 8192, "num_predict": max_tokens}}
    if seed is not None:                  # Ollama uses a FIXED seed by default (deterministic even at temp>0); vary the seed to sample
        payload["options"]["seed"] = seed
    if _ollama_can_think(model):          # capable -> always think (honor the flag); incapable -> omit (Ollama 400s)
        payload["think"] = bool(think)
    body = json.dumps(payload).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["message"]["content"]


def _parse_reply(text):
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    try:
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        d = {}
    tags = d.get("tags") if isinstance(d.get("tags"), dict) else {"dimensions": {}}
    return {"action": d.get("action", ""), "thought": d.get("thought", ""),
            "exit": bool(d.get("exit", False)), "addressee": d.get("addressee", ""), "tags": tags}


def llm_turn(packet, event_text, temperament, model, stub, think=True, seed=None, relationships=None, corrections=None):
    if stub:
        return {"action": "(stub) the character meets the moment — %s" % event_text.lower(),
                "thought": "(stub) steady; do what it needs",
                "tags": {"type": "mundane", "summary": event_text, "dimensions": {"mastery": 0.2},
                         "durability": "transient"}}
    messages = build_turn_messages(packet, event_text, temperament, relationships)
    if corrections:                                                  # faithful_turn appends corrective turns on a name-leak retry
        messages = list(messages) + list(corrections)
    if model.startswith("ollama/"):                                  # local on-disk dispatch (free, pinned)
        return _parse_reply(_ollama(messages, model[len("ollama/"):], think=think, seed=seed))
    return _parse_reply(_openrouter(messages, model))


def faithful_turn(packet, event_text, temperament, model, stub, think=True, seed=None, relationships=None, max_retries=2):
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
        turn = llm_turn(packet, event_text, temperament, model, stub, think=think, seed=s,
                        relationships=relationships, corrections=(corrections or None))
        if not str(turn.get("action", "")).strip() and attempt < max_retries:
            continue                          # empty/unparseable draw (no action) — resample. At temp 1.0
                                              # generation is non-reproducible, so a fresh draw of the SAME
                                              # prompt usually parses (measured 2026-06-14: in-scene empty,
                                              # standalone resample full). Nothing to correct — just redraw.
        leaks = faithfulness.check_name_leaks("%s %s" % (turn.get("action", ""), turn.get("thought", "")), rels)
        if not leaks:
            return turn, []
        corrections.append({"role": "user", "content": (
            "You used a name your character does not know: %s. They know this person only as %s. "
            "Rewrite your ENTIRE reply (same JSON shape) using only that descriptor — never the name."
            % (", ".join(n for n, k in leaks), "; ".join("%r" % k for n, k in leaks)))})
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

def run_turn(led, run_id, char, world, groups_index, profile, temperament, affect, turn_no, event_text, recent, model, stub, book_dir=None):
    """One placed circumstance through the full spine. Returns (new_affect, ok, char, profile) —
    char/profile may be EVOLVED if the event wrote a durable baseline diff (the arc engine)."""
    scene_slice = {"event": {"text": event_text, "kind": "mundane"}, "recent": recent[-2:],
                   "location": char["current"].get("location")}
    packet = assemble(char, world, scene_slice, affect, char["current"]["condition"])
    record_faults(detect_world_faults(packet, scene_slice, event_text, world, turn_no), book_dir)
    actor = char["fixed"]["name"].lower()
    try:
        # name hygiene rides in build_turn_messages: assemble saw RAW text (so kestra->fenmark resolves);
        # the PROMPT masks every name this actor never acquired (passed via relationships). faithful_turn
        # then REGENERATES on any name-leak the masking wall couldn't stop (latent weights leak).
        turn, leaks = faithful_turn(packet, event_text, temperament, model, stub, seed=turn_no,
                                    relationships=char["current"].get("relationships", {}))
    except Exception as exc:                       # degrade, never crash; no silent skips
        led.record_turn_skipped(run_id, turn_no, actor, str(exc))
        print("  [turn failed, recorded as turn-skipped: %s]" % str(exc)[:80])
        return affect, False, char, profile
    if leaks:                                      # name(s) the actor cannot hold survived retries -> reject; never commit a leak
        led.record_turn_skipped(run_id, turn_no, actor,
                                "faithfulness: used name(s) not theirs after retries: %s" % ", ".join(n for n, k in leaks))
        print("  [faithfulness reject: %s used %s after retries — turn skipped]" % (actor, ", ".join(n for n, k in leaks)))
        return affect, False, char, profile
    tags = turn["tags"]
    validation = validate_tags(tags, packet["volatile"]["percepts"], char["baseline"]["skills"])
    if not validation["ok"]:
        applied = {"dimensions": {}}               # schema-invalid never moves state
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
    if target is not None:
        applied = dict(applied, target=target)
        if target_group is not None:
            applied["target_group"] = target_group
    appraised = appraise(affect, applied, profile)                 # the event's raw impact (pre-decay)
    impact = sum(abs(appraised[p] - affect[p]) for p in PRIMARIES)
    new_affect = decay(appraised, temperament, profile)
    led.append_turn(TurnCommit(
        run_id=run_id, turn=turn_no, actor=char["fixed"]["name"].lower(),
        thought=str(turn["thought"]), action=str(turn["action"]),
        tags=tags if isinstance(tags, dict) else {}, affect=dict(new_affect),
        condition=dict(char["current"]["condition"]), validation=validation,
        events=[Event(type=str(tags.get("type", "mundane")),
                      payload={"text": event_text, "dimensions": tags.get("dimensions", {}),
                               "durability": tags.get("durability", "transient"),
                               "subject": target, "subject_group": target_group},
                      actor=char["fixed"]["name"].lower())],
        manifest=packet["manifest"], recall=packet["recall_refs"]))
    print("\n  ACTION : %s" % str(turn["action"]).replace("\n", " ")[:300])
    print("  THOUGHT: %s" % str(turn["thought"]).replace("\n", " ")[:240])
    print("  TAGS   : %s %s [%s]  valid=%s conf=%.2f%s" % (
        tags.get("type", "?"), json.dumps(tags.get("dimensions", {})), tags.get("durability", "?"),
        validation["ok"], validation["confidence"],
        "  ** ESCALATE: %s" % "; ".join(validation["flags"])[:100] if validation["escalate"] else ""))
    if target is not None:                          # who the event was about + the class regard scoped by
        print("  SUBJECT: %s%s" % (target, ("  [%s]" % target_group) if target_group else "  [unregarded]"))
    # (faithfulness is enforced pre-commit by faithful_turn above — a committed turn is leak-free by construction)

    # ---- the arc engine: a durable event moves the BASELINE (who they now are), persists, evolves char ----
    diff = arc.assess(applied, impact, char, char["current"]["condition"])
    if diff:
        char = arc.apply(char, diff)
        led.append_arc_diff(run_id, actor, turn_no, diff)
        profile = build_profile(char)              # re-derive from the evolved baseline
        m = diff.get("_meta", {})
        moved = list(diff.get("temperament", {})) + ["%s.%s" % (t, a) for t, ax in diff.get("relationships", {}).items() for a in ax] + ["regard.%s" % g for g in diff.get("regard", {})]
        print("  ARC    : durable (%s, impact %.2f) -> baseline moved: %s" % (m.get("dominant", "?"), m.get("impact", 0.0), ", ".join(moved)))

    # acquisition: a durable, subject-bearing turn becomes a recallable belief in the actor's vault
    # (knowledge-model.md). The ENGINE reads the committed turn — never the model's introspection;
    # provenance 'lived' marks it apart from an authored .md seed. Folds forward now so the next turn's
    # recall gate can surface it; persisted to the ledger for the record.
    acquired = acquisition.assess(applied, tags, char)
    if acquired:
        char["current"].setdefault("vault", []).append(acquired)
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
    print("  %s — %s. They are %s." % (char["fixed"]["name"],
                                       direct_affect(affect, temperament),
                                       direct_condition(char["current"]["condition"])))


def main():
    ap = argparse.ArgumentParser(description="the director's chair — place circumstance, read the life")
    ap.add_argument("--vault", default=None, help="BOOK FOLDER in your Obsidian vault (world/, characters/, people/ notes) — real books live here, never in this repo")
    ap.add_argument("--book", default=None, help="fixture world stem under world/ (engine TEST fixtures only)")
    ap.add_argument("--char", required=True, help="character: note name (--vault) or fixture file stem (--book)")
    ap.add_argument("--stub", action="store_true", help="deterministic stand-in, no API")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--resume", default=None, help="run_id to continue")
    ap.add_argument("--db", default=None, help="db path (default runs/<book>.db)")
    args = ap.parse_args()

    if bool(args.vault) == bool(args.book):
        raise SystemExit("pass exactly one of --vault (a real book) or --book (an engine test fixture)")
    if args.vault:
        from src.engine.vault import load_book
        world, chars = load_book(args.vault)
        key = args.char.lower().replace(" ", "_")
        if key not in chars:
            raise SystemExit("character %r not in book (have: %s)" % (args.char, ", ".join(sorted(chars))))
        char = chars[key]
        book_name = os.path.basename(os.path.normpath(args.vault)).lower().replace(" ", "-")
        default_db = os.path.join(args.vault, "runs", "%s.db" % book_name)   # the chronicle lives WITH the book
    else:
        def find(folder, stem):
            for cand in (stem, stem + "-slice", stem + "-healer"):
                p = os.path.join(REPO, folder, cand + ".json")
                if os.path.exists(p):
                    return os.path.relpath(p, REPO)
            raise SystemExit("no %s/%s*.json found" % (folder, stem))
        world = _load(find("world", args.book))
        char = _load(find("characters", args.char))
        book_name = args.book
        default_db = os.path.join(REPO, "runs", "%s.db" % args.book)
    char_id = char["fixed"]["name"].lower()
    led = Ledger(args.db or default_db)

    if args.resume:
        run_id = args.resume
        led.set_status(run_id, "active")
        state = led.resume(run_id)
        for diff in led.arc_diffs_for(run_id, char_id):       # rehydrate durable baseline evolution (the arc)
            char = arc.apply(char, diff)
        acquired = led.acquisitions_for(run_id, char_id)       # rehydrate the grown vault (lived memory)
        if acquired:
            char["current"].setdefault("vault", []).extend(acquired)
        latest = led.latest_affect(run_id, char_id)
        affect = latest["affect"] if latest else dict(char["current"]["affect"])
        turn_no = state["turn"] + 1
        print("resumed %s at turn %d (determinism OK)" % (run_id, state["turn"]))
    else:
        run_id = "directed-%s-%d" % (book_name, int(time.time()))
        led.create_run(run_id, {"catalog_version": 1,
                                "models": {"turn": "stub" if args.stub else args.model},
                                "prompt_versions": {"turn": 1}})
        led.register_character(run_id, char_id, char["fixed"], char["baseline"])
        affect = dict(char["current"]["affect"])
        turn_no = 0
        print("new chronicle: %s" % run_id)

    profile = build_profile(char)
    temperament = char["baseline"]["temperament"]
    groups_index = subject_groups(world)            # entity -> class, built once (the subject's regard key)
    recent = []
    record_faults(startup_faults(char, world), args.vault)
    show_status(led, run_id, char, affect, temperament)
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
            belief = acquisition.reveal_name(char, parts[1], parts[2])
            if belief:
                led.append_acquisition(run_id, char_id, turn_no, belief)
                print("  REVEAL : %s now known to %s as %r — %s" % (parts[1], char_id, parts[2], belief["claim"]))
            else:
                print("  (no %r in %s's relationships — reveal skipped)" % (parts[1], char_id))
            continue
        affect, ok, char, profile = run_turn(led, run_id, char, world, groups_index, profile, temperament, affect,
                                             turn_no, cmd, recent, args.model, args.stub, book_dir=args.vault)
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
