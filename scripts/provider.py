#!/usr/bin/env python3
"""provider.py — the ONE frontier-model seam: OpenRouter, pinned model, temperature 0, cached prefix.

Owner, 2026-09-11: *"Since this will be the basis for most of the system we will not use local
models, we need accuracy."* The appraiser seats are the one semantic step in the engine — every
number downstream is arithmetic on what they say — so they run on a frontier model through this
seam, and nothing else in the repo opens a socket to a model. Before this file there were three
hand-copied OpenRouter helpers (scripts/direct.py, tests/coherence_probe.py, and the bakeoff's
ollama-only path), which is the seven-duplicates table in CLAUDE.md one row longer.

WHAT IT PINS
  * THE MODEL is a parameter with one default per job (`seat_model`): `anthropic/claude-opus-5`
    for the seats — confirmed on OpenRouter's public models list 2026-09-11 (1M context, cache-read
    priced), which is the whole reason the slug is written here rather than guessed. Override with
    SWE_SEAT_MODEL. The id is recorded per run in `runs.config["models"]` by the caller.
  * TEMPERATURE 0. Replay is from the readings log regardless (hard rule 2), so provider variance
    cannot break a chronicle; reading the same book twice is two runs to compare, never assumed
    identical.
  * THE CONSTANT PREFIX IS CACHED. Every seat call carries the nine ladders and the concept menu —
    thousands of tokens that never change between beats. The system message is sent as a content
    block with `cache_control: ephemeral`, which OpenRouter forwards to Anthropic; the first live
    run's `llm_calls` rows show whether cached tokens appear (`tokens_cached`), and until then the
    cost estimate assumes they do not.
  * EVERY CALL IS LOGGED when a ledger is in hand (`Ledger.log_llm_call`): model, tokens in/out,
    purpose, scene. `llm_calls` was empty on every real run for months because the counts were
    thrown away; this seam is where they are kept.

THE KEY is read from the file `SWE_ENV_FILE` names (or a gitignored `.env` beside the repo), the
line `OPENROUTER_API_KEY=...`. No key file -> PROVIDER_NO_KEY, by name, before any request is built.

THE SECOND BACKEND: REPLAY (2026-09-11; owner: "Use subagents" / "can you not batch?"). The seat
prompts are built from the passage alone (emotion-arithmetic section 7 - the sensor is blind to
stored state), so every prompt of a run can be written out FIRST (`emit`), answered out of process -
one fresh agent per prompt, never a batch, so no answer can see another - and read back by the
live call that builds the identical messages (`call` with SWE_SEAT_REPLIES set, or `use_replies`).
The key is the sha256 of the messages, so an answer only ever meets the prompt it was written for;
a prompt edited in between finds nothing and refuses by name (PROVIDER_REPLY_MISSING). The
answering agent reports no token counts, so the `llm_calls` row carries the model name and NULLs.

THE WAIT (2026-09-11, the first generated scene on a real book). A read-along can emit every
prompt before it runs because the seat prompts are built from the passage alone. A GENERATED
scene cannot: beat N's prompts are built from beat N-1's committed turn, so they do not exist
until the run reaches them. With `SWE_SEAT_WAIT=<seconds>` (or `use_replies(path, wait=...)`) a
missing answer no longer refuses at once — the prompt is EMITTED into the replay root and the
call POLLS for its answer file until an out-of-process agent writes it, then reads it through the
identical path. Same key, same files, same read; only the ordering constraint is gone. The wait
is opt-in: absent, a missing answer refuses immediately and nothing is written, as before. On
timeout it refuses by the same name (PROVIDER_REPLY_MISSING) — and note that scripts/scene.py
still catches that as a seat refusal and commits the beat on the actor's self-tags, so a driven
run sets the wait long and checks `llm_calls` afterwards (one act + two seat rows per beat).
Nothing here is imported by `src/engine/` (hard rule 3).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.records import RecordError                        # noqa: E402

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_SEAT_MODEL = "anthropic/claude-opus-5"     # the seats: judgement-critical, strongest tier
DEFAULT_TEMPERATURE = 0.0
TIMEOUT = 180

# What the last call cost, for callers that do not hold a ledger (scripts/direct.py reads this).
LAST_USAGE = {}

REPLIES_ENV = "SWE_SEAT_REPLIES"     # a directory of answered prompts -> the replay backend
_REPLIES = None                       # use_replies() override; the env var otherwise
WAIT_ENV = "SWE_SEAT_WAIT"           # seconds a missing answer is waited for (0 / unset: refuse at once)
_WAIT = None                          # use_replies(wait=...) override; the env var otherwise
_POLL_SECONDS = 2.0                   # how often the wait looks for the answer file
_SETTLE_SECONDS = 1.0                 # an answer file is read only once its mtime is this old


def prompt_key(messages):
    """The identity of a prompt: sha256 over its canonical JSON -> 24 hex chars. The same builder
    inputs give the same key, so an answer written for an emitted prompt is found by the live call
    that builds the identical messages; a prompt edited in between finds nothing, by design."""
    blob = json.dumps(messages, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


def use_replies(path, wait=None):
    """Route every call through the replay backend rooted at `path` (None = back to HTTP).
    `wait` (seconds) makes a missing answer emit its prompt and wait for the file instead of
    refusing at once; None defers to SWE_SEAT_WAIT."""
    global _REPLIES, _WAIT
    _REPLIES = path or None
    _WAIT = None if wait is None else float(wait)


def replies_dir():
    """The replay root in force, or None (HTTP)."""
    return _REPLIES or os.environ.get(REPLIES_ENV) or None


def wait_seconds():
    """How long a missing answer is waited for: the use_replies override, else SWE_SEAT_WAIT, else 0."""
    if _WAIT is not None:
        return max(0.0, _WAIT)
    raw = os.environ.get(WAIT_ENV, "").strip()
    try:
        return max(0.0, float(raw)) if raw else 0.0
    except ValueError:
        raise RecordError("PROVIDER_WAIT_INVALID", "%s=%r is not a number of seconds" % (WAIT_ENV, raw))


def _await_reply(p, seconds):
    """Poll for the answer file at `p` up to `seconds`; True once it exists, is non-empty and has
    sat unchanged for _SETTLE_SECONDS (a writer still writing is not an answer)."""
    deadline = time.monotonic() + seconds
    while True:
        try:
            st = os.stat(p)
            if st.st_size > 0 and (time.time() - st.st_mtime) >= _SETTLE_SECONDS:
                return True
        except OSError:
            pass
        if time.monotonic() >= deadline:
            return False
        time.sleep(min(_POLL_SECONDS, max(0.05, deadline - time.monotonic())))


def reply_path(out_dir, key):
    """Where the answer to prompt `key` lives: <out_dir>/<key>.reply.txt - the raw reply text."""
    return os.path.join(out_dir, "%s.reply.txt" % key)


def emit(messages, model, purpose, out_dir, meta=None):
    """Write a prompt for an out-of-process answer -> its key. The constant system text goes once
    per (purpose, content) as system.<purpose>.<hash>.txt and the prompt file carries the user
    turn(s) plus a pointer to it, so an answering agent reads the ladders once and the passage once.
    Idempotent: an existing prompt file is left as it is."""
    key = prompt_key(messages)
    os.makedirs(out_dir, exist_ok=True)
    sys_text = "\n\n".join(m["content"] for m in messages if m.get("role") == "system")
    sys_name = "system.%s.%s.txt" % (purpose, hashlib.sha256(sys_text.encode("utf-8")).hexdigest()[:8])
    sys_path = os.path.join(out_dir, sys_name)
    if not os.path.exists(sys_path):
        with io.open(sys_path, "w", encoding="utf-8") as fh:
            fh.write(sys_text)
    p = os.path.join(out_dir, "%s.prompt.json" % key)
    if not os.path.exists(p):
        row = {"key": key, "purpose": purpose, "model": model, "system": sys_name,
               "messages": [dict(m) for m in messages if m.get("role") != "system"], "meta": dict(meta or {})}
        with io.open(p, "w", encoding="utf-8") as fh:
            json.dump(row, fh, ensure_ascii=False, indent=1)
    return key


def _replay(messages, model, purpose, led, run_id, turn, scene):
    """The replay backend: the answer written for this exact prompt, or PROVIDER_REPLY_MISSING."""
    d = replies_dir()
    key = prompt_key(messages)
    p = reply_path(d, key)
    if not os.path.isfile(p):
        seconds = wait_seconds()
        if seconds > 0:
            # THE WAIT: write the prompt out, then hold for its answer. The key is the same one a
            # pre-emitted prompt would carry, so the answering side is identical either way.
            emit(messages, model, purpose, d, meta={"turn": turn, "scene": scene, "run_id": run_id})
            print("[provider] waiting up to %ds for %s answer %s under %s" % (int(seconds), purpose, key, d),
                  file=sys.stderr, flush=True)
            if not _await_reply(p, seconds):
                raise RecordError("PROVIDER_REPLY_MISSING",
                                  "%s: no answer for prompt %s under %s after %ds (the prompt is emitted; "
                                  "answer it and rerun)" % (purpose, key, d, int(seconds)))
        else:
            raise RecordError("PROVIDER_REPLY_MISSING",
                              "%s: no answer under %s for prompt %s (emit the prompts, answer every one, then replay)"
                              % (purpose, d, key))
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    LAST_USAGE.clear()
    LAST_USAGE.update({"model": model, "tokens_in": None, "tokens_out": None, "tokens_cached": None, "replayed": key})
    if led is not None and run_id is not None:
        led.log_llm_call(run_id, int(turn or 0), purpose, model, None, None, scene=scene)
    return text


def env_path():
    """Path to the file holding OPENROUTER_API_KEY. Machine-local, never hardcoded."""
    p = os.environ.get("SWE_ENV_FILE")
    if p:
        return p
    local = os.path.join(REPO, ".env")
    if os.path.exists(local):
        return local
    raise RecordError("PROVIDER_NO_KEY",
                      "no key file: set SWE_ENV_FILE to the file holding OPENROUTER_API_KEY, or place "
                      "a .env at the repo root (it is gitignored). The seats run on a frontier model "
                      "by the owner's ruling; there is no local fallback for them.")


def read_key(path=None):
    """The OPENROUTER_API_KEY line of the key file -> the key. Raises PROVIDER_NO_KEY when absent."""
    p = path or env_path()
    try:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"\s*OPENROUTER_API_KEY\s*=\s*(\S+)", line)
                if m:
                    return m.group(1).strip().strip('"').strip("'")
    except OSError as e:
        raise RecordError("PROVIDER_NO_KEY", "key file %r unreadable: %s" % (p, e))
    raise RecordError("PROVIDER_NO_KEY", "key file %r carries no OPENROUTER_API_KEY line" % (p,))


def seat_model():
    """The model the appraiser seats run on: SWE_SEAT_MODEL or the pinned default."""
    return os.environ.get("SWE_SEAT_MODEL") or DEFAULT_SEAT_MODEL


def shape(messages, model, temperature=DEFAULT_TEMPERATURE, max_tokens=700, cache=True):
    """The request body, as a dict — separated so a test can see it without a socket.

    The FIRST system message is the constant prefix (ladders + menu); it is sent as one content
    block carrying `cache_control: ephemeral`. Every other message is passed through as is.
    """
    out = []
    cached = False
    for m in messages:
        if cache and not cached and m.get("role") == "system":
            out.append({"role": "system",
                        "content": [{"type": "text", "text": m["content"],
                                     "cache_control": {"type": "ephemeral"}}]})
            cached = True
        else:
            out.append(dict(m))
    body = {"model": model, "messages": out, "max_tokens": int(max_tokens)}
    if temperature is not None:                 # None = the model's own default (the actor performs)
        body["temperature"] = float(temperature)
    return body


def call(messages, model, purpose, led=None, run_id=None, turn=None, scene=None,
         temperature=DEFAULT_TEMPERATURE, max_tokens=700, cache=True):
    """messages -> the reply text. Logs the call on `led` when given. Raises by name on a bad reply.
    With a replay root in force (SWE_SEAT_REPLIES / use_replies) the answer comes from the file
    written for this exact prompt and neither the network nor the key file is touched."""
    if replies_dir():
        return _replay(messages, model, purpose, led, run_id, turn, scene)
    key = read_key()
    body = json.dumps(shape(messages, model, temperature, max_tokens, cache)).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "Authorization": "Bearer %s" % key, "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/simtoprose", "X-Title": "SimToProse"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            reply = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RecordError("PROVIDER_HTTP_ERROR", "%s: HTTP %s for %s — %s" % (purpose, e.code, model, detail))
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise RecordError("PROVIDER_HTTP_ERROR", "%s: %s for %s" % (purpose, e, model))
    try:
        text = reply["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RecordError("PROVIDER_BAD_REPLY", "%s: reply carried no choices[0].message.content: %r"
                          % (purpose, str(reply)[:200]))
    usage = reply.get("usage") or {}
    details = usage.get("prompt_tokens_details") or {}
    LAST_USAGE.clear()
    LAST_USAGE.update({"model": model, "tokens_in": usage.get("prompt_tokens"),
                       "tokens_out": usage.get("completion_tokens"),
                       "tokens_cached": details.get("cached_tokens")})
    if led is not None and run_id is not None:
        led.log_llm_call(run_id, int(turn or 0), purpose, model,
                         usage.get("prompt_tokens"), usage.get("completion_tokens"), scene=scene)
    return text
