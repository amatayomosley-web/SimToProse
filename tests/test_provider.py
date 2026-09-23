"""test_provider.py — the one frontier-model seam, without a socket.

scripts/provider.py is the only place the repo opens a connection to a model (2026-09-11, owner:
no local models for the seats — accuracy). What can be pinned without a key or a network:

  1. THE REQUEST SHAPE. The model is the one asked for; the seats' temperature is 0 and the
     actor's is left to the model; the FIRST system message goes out as one content block marked
     cache_control ephemeral (the ladders and the concept menu are the constant prefix); every
     other message passes through untouched.
  2. THE KEY. No key file -> PROVIDER_NO_KEY by name, before any request is built; a key file
     with the line yields the key; one without the line refuses by the same name.
  3. THE DEFAULT SEAT MODEL is the pinned slug and SWE_SEAT_MODEL overrides it.
  4. NOTHING IN src/engine/ IMPORTS THE SEAM (hard rule 3).
  5. THE REPLAY BACKEND (2026-09-11, owner: one agent per prompt, never a batch). A prompt's key
     is a function of its messages alone; `emit` writes the prompt once and the constant system
     text once; with a replay root in force `call` returns the answer written for that exact
     prompt, logs the call with the model and no token counts, and touches neither the key file
     nor a socket; a missing answer refuses by name; switching the root off restores HTTP.

Stdlib only. Exit 0 = all pass.
"""
import io
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import provider as P                                          # noqa: E402
from src.engine.records import RecordError                    # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def test_the_request_shape():
    print("\n[1] THE REQUEST SHAPE")
    msgs = [{"role": "system", "content": "THE LADDERS"}, {"role": "user", "content": "the beat"}]
    body = P.shape(msgs, "anthropic/claude-opus-5")
    check("the-model-is-the-one-asked-for", body["model"] == "anthropic/claude-opus-5")
    check("the-seats-run-at-temperature-zero", body["temperature"] == 0.0)
    sysm = body["messages"][0]
    check("the-system-prefix-is-one-cached-block",
          sysm["role"] == "system" and isinstance(sysm["content"], list) and len(sysm["content"]) == 1
          and sysm["content"][0]["text"] == "THE LADDERS" and sysm["content"][0]["cache_control"] == {"type": "ephemeral"}, sysm)
    check("the-user-message-passes-through", body["messages"][1] == {"role": "user", "content": "the beat"})
    actor = P.shape(msgs, "anthropic/claude-opus-5", temperature=None)
    check("the-actor-keeps-the-models-own-sampling", "temperature" not in actor)
    plain = P.shape(msgs, "m", cache=False)
    check("caching-can-be-switched-off", plain["messages"][0]["content"] == "THE LADDERS")


def test_the_key(tmp):
    print("\n[2] THE KEY")
    saved = os.environ.get("SWE_ENV_FILE")
    try:
        os.environ["SWE_ENV_FILE"] = os.path.join(tmp, "absent.env")
        try:
            P.read_key()
            check("no-key-file-refuses-by-name", False, "did not raise")
        except RecordError as exc:
            check("no-key-file-refuses-by-name", "PROVIDER_NO_KEY" in str(exc), str(exc)[:80])
        p = os.path.join(tmp, "with.env")
        io.open(p, "w", encoding="utf-8").write("OTHER=1\nOPENROUTER_API_KEY=\"sk-test-123\"\n")
        os.environ["SWE_ENV_FILE"] = p
        check("a-key-file-yields-the-key", P.read_key() == "sk-test-123")
        q = os.path.join(tmp, "without.env")
        io.open(q, "w", encoding="utf-8").write("OTHER=1\n")
        try:
            P.read_key(q)
            check("a-file-without-the-line-refuses", False, "did not raise")
        except RecordError as exc:
            check("a-file-without-the-line-refuses", "PROVIDER_NO_KEY" in str(exc))
        # the call refuses before any network when there is no key
        os.environ["SWE_ENV_FILE"] = os.path.join(tmp, "absent.env")
        try:
            P.call([{"role": "user", "content": "x"}], "m", "test")
            check("call-refuses-before-the-network-without-a-key", False, "did not raise")
        except RecordError as exc:
            check("call-refuses-before-the-network-without-a-key", "PROVIDER_NO_KEY" in str(exc))
    finally:
        if saved is None:
            os.environ.pop("SWE_ENV_FILE", None)
        else:
            os.environ["SWE_ENV_FILE"] = saved


def test_the_default_model_and_the_boundary():
    print("\n[3] THE DEFAULT MODEL, AND THE ENGINE BOUNDARY")
    saved = os.environ.pop("SWE_SEAT_MODEL", None)
    try:
        check("the-default-seat-model-is-pinned", P.seat_model() == "anthropic/claude-opus-5")
        os.environ["SWE_SEAT_MODEL"] = "anthropic/claude-sonnet-5"
        check("the-override-wins", P.seat_model() == "anthropic/claude-sonnet-5")
    finally:
        os.environ.pop("SWE_SEAT_MODEL", None)
        if saved is not None:
            os.environ["SWE_SEAT_MODEL"] = saved
    eng = os.path.join(REPO, "src", "engine")
    offenders = [fn for fn in os.listdir(eng) if fn.endswith(".py")
                 and ("import provider" in io.open(os.path.join(eng, fn), encoding="utf-8").read()
                      or "openrouter.ai" in io.open(os.path.join(eng, fn), encoding="utf-8").read())]
    check("nothing-in-the-engine-imports-the-seam", not offenders, offenders)


def test_the_replay(tmp):
    print("\n[5] THE REPLAY BACKEND — one answer per prompt, keyed on the prompt")
    import glob
    import json
    msgs = [{"role": "system", "content": "THE LADDERS"}, {"role": "user", "content": "the beat"}]
    other = [{"role": "system", "content": "THE LADDERS"}, {"role": "user", "content": "another beat"}]
    check("the-key-is-a-function-of-the-messages-alone",
          P.prompt_key(msgs) == P.prompt_key([dict(m) for m in msgs]) and P.prompt_key(msgs) != P.prompt_key(other))
    d = os.path.join(tmp, "seats")
    key = P.emit(msgs, "subagent:test", "appraise-emotion", d, meta={"turn": 3})
    P.emit(other, "subagent:test", "appraise-emotion", d)
    check("emit-writes-one-prompt-file-per-prompt-and-the-system-text-once",
          os.path.isfile(os.path.join(d, key + ".prompt.json")) and len(glob.glob(os.path.join(d, "*.prompt.json"))) == 2
          and len(glob.glob(os.path.join(d, "system.appraise-emotion.*.txt"))) == 1)
    row = json.load(io.open(os.path.join(d, key + ".prompt.json"), encoding="utf-8"))
    check("the-prompt-file-carries-the-user-turn-and-points-at-the-system",
          row["messages"] == [msgs[1]] and row["system"].startswith("system.appraise-emotion.") and row["meta"] == {"turn": 3}
          and io.open(os.path.join(d, row["system"]), encoding="utf-8").read() == "THE LADDERS")
    saved = os.environ.get("SWE_ENV_FILE")
    os.environ["SWE_ENV_FILE"] = os.path.join(tmp, "nowhere.env")            # no key anywhere
    try:
        P.use_replies(d)
        try:
            P.call(msgs, "subagent:test", "appraise-emotion")
            check("a-missing-answer-refuses-by-name", False, "did not raise")
        except RecordError as exc:
            check("a-missing-answer-refuses-by-name", "PROVIDER_REPLY_MISSING" in str(exc), str(exc)[:80])
        io.open(P.reply_path(d, key), "w", encoding="utf-8").write('{"readings": []}')
        calls = []

        class Led:                                     # the ledger's logging seam, and nothing else
            def log_llm_call(self, run_id, turn, purpose, model, tokens_in=None, tokens_out=None, scene=None):
                calls.append((run_id, turn, purpose, model, tokens_in, tokens_out, scene))

        out = P.call(msgs, "subagent:test", "appraise-emotion", led=Led(), run_id="r", turn=3, scene="ch1")
        check("the-answer-replays-without-a-key-file-or-a-socket", out == '{"readings": []}', out)
        check("the-call-is-logged-with-the-model-and-no-token-counts",
              calls == [("r", 3, "appraise-emotion", "subagent:test", None, None, "ch1")], calls)
        check("last-usage-names-the-replayed-prompt", P.LAST_USAGE.get("replayed") == key, P.LAST_USAGE)
    finally:
        P.use_replies(None)
        if saved is None:
            os.environ.pop("SWE_ENV_FILE", None)
        else:
            os.environ["SWE_ENV_FILE"] = saved
    check("the-http-path-is-back-when-the-root-is-off", P.replies_dir() is None)
    os.environ["SWE_SEAT_REPLIES"] = d
    try:
        check("the-env-var-is-the-other-way-in", P.replies_dir() == d)
    finally:
        os.environ.pop("SWE_SEAT_REPLIES", None)


def test_the_wait(tmp):
    print("\n[6] THE WAIT — a missing answer is emitted and waited for, only when asked")
    import glob
    import threading
    import time as _time
    msgs = [{"role": "system", "content": "THE LADDERS"}, {"role": "user", "content": "beat N, unknown before the run"}]
    d = os.path.join(tmp, "live-seats")
    key = P.prompt_key(msgs)
    saved = os.environ.get("SWE_ENV_FILE")
    os.environ["SWE_ENV_FILE"] = os.path.join(tmp, "nowhere.env")            # no key anywhere
    try:
        # (a) no wait in force: refuses at once and writes NOTHING — today's behaviour, asserted
        P.use_replies(d)
        try:
            P.call(msgs, "subagent:test", "act")
            check("no-wait-refuses-at-once", False, "did not raise")
        except RecordError as exc:
            check("no-wait-refuses-at-once", "PROVIDER_REPLY_MISSING" in str(exc), str(exc)[:80])
        check("no-wait-emits-nothing", not glob.glob(os.path.join(d, "*")), glob.glob(os.path.join(d, "*")))
        # (b) a wait with no writer: the prompt is emitted, then it refuses by the same name after the wait
        P.use_replies(d, wait=1.5)
        t0 = _time.monotonic()
        try:
            P.call(msgs, "subagent:test", "act")
            check("a-wait-with-no-answer-still-refuses", False, "did not raise")
        except RecordError as exc:
            check("a-wait-with-no-answer-still-refuses", "PROVIDER_REPLY_MISSING" in str(exc), str(exc)[:80])
        check("the-refusal-came-after-the-wait", _time.monotonic() - t0 >= 1.4, "%.2fs" % (_time.monotonic() - t0))
        check("the-prompt-was-emitted-for-the-answering-side",
              os.path.isfile(os.path.join(d, key + ".prompt.json"))
              and len(glob.glob(os.path.join(d, "system.act.*.txt"))) == 1)
        # (c) a wait with a late writer: the answer is read through the ordinary replay path
        P.use_replies(d, wait=10)
        calls = []

        class Led:
            def log_llm_call(self, run_id, turn, purpose, model, tokens_in=None, tokens_out=None, scene=None):
                calls.append((run_id, turn, purpose, model, tokens_in, tokens_out, scene))

        def writer():
            _time.sleep(0.5)
            io.open(P.reply_path(d, key), "w", encoding="utf-8").write('{"action": "He shuts the door."}')

        threading.Thread(target=writer, daemon=True).start()
        t0 = _time.monotonic()
        out = P.call(msgs, "subagent:test", "act", led=Led(), run_id="r", turn=7, scene="s1")
        check("the-late-answer-is-returned", out == '{"action": "He shuts the door."}', out)
        check("it-returned-once-the-file-settled-not-at-the-deadline", _time.monotonic() - t0 < 8, "%.2fs" % (_time.monotonic() - t0))
        check("the-waited-call-is-logged-like-a-replay", calls == [("r", 7, "act", "subagent:test", None, None, "s1")], calls)
        # (d) the env var is the other way in, and a bad value refuses by name
        P.use_replies(d)
        os.environ["SWE_SEAT_WAIT"] = "2.5"
        check("the-env-var-sets-the-wait", P.wait_seconds() == 2.5, P.wait_seconds())
        os.environ["SWE_SEAT_WAIT"] = "soon"
        try:
            P.wait_seconds()
            check("a-non-numeric-wait-refuses-by-name", False, "did not raise")
        except RecordError as exc:
            check("a-non-numeric-wait-refuses-by-name", "PROVIDER_WAIT_INVALID" in str(exc), str(exc)[:80])
    finally:
        os.environ.pop("SWE_SEAT_WAIT", None)
        P.use_replies(None)
        if saved is None:
            os.environ.pop("SWE_ENV_FILE", None)
        else:
            os.environ["SWE_ENV_FILE"] = saved
    check("the-wait-is-off-with-the-root", P.wait_seconds() == 0.0 and P.replies_dir() is None)


def main():
    print("test_provider.py — the one frontier-model seam")
    tmp = tempfile.mkdtemp(prefix="stp-provider-")
    try:
        test_the_request_shape()
        test_the_key(tmp)
        test_the_default_model_and_the_boundary()
        test_the_replay(tmp)
        test_the_wait(tmp)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
