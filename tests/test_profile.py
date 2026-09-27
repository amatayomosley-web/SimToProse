#!/usr/bin/env python3
"""test_profile.py - the session profile (gate session-profile): the role table refuses what cannot do the job and
warns about every other floor (src/engine/roles.py); profile.py writes a profile or refuses it; provider.py answers a
seat on a local model and replays only the seats for subagents; scene.py and brief.py carry the profile; seats.py lists
the prompts waiting for an answer. Script-style, stdlib only - no model is called (the local client is a double)."""
import io
import json
import os
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))
from src.engine import books, roles                                       # noqa: E402
from src.engine.records import RecordError                                # noqa: E402
from test_vault import _mk_vault                                          # noqa: E402
from test_draft_flow import _run, _scene_cfg                              # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    detail = str(detail)[-300:].encode("ascii", "backslashreplace").decode("ascii")
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        FAILS.append(name)


def _code(fn):
    try:
        fn()
    except RecordError as exc:
        return exc.code
    return None


def _profile(**roles_):
    base = dict(roles.AGENT_DEFAULTS, actor="ollama/local-actor", seats="anthropic/claude-opus-5")
    base.update(roles_)
    return {"profile": 1, "roles": base}


def table():
    print("[1] the role table: hard floors refuse, soft floors warn")
    got, warns = roles.check(_profile())
    check("the-guide's-defaults-pass-with-no-warning", got["showrunner"] == "sonnet" and warns == [], warns)
    check("a-qwen-7B-showrunner-is-ROLES_CLAUDE_ONLY",
          _code(lambda: roles.check(_profile(showrunner="ollama/qwen2.5:7b"))) == "ROLES_CLAUDE_ONLY")
    check("a-haiku-showrunner-is-ROLES_BELOW_FLOOR",
          _code(lambda: roles.check(_profile(showrunner="haiku"))) == "ROLES_BELOW_FLOOR")
    got, warns = roles.check(_profile(seats="ollama/local-actor", director="sonnet"))
    check("local-seats-and-a-sonnet-director-only-warn,-naming-each-role", len(warns) == 2
          and any(w.startswith("seats ") for w in warns) and any(w.startswith("director ") for w in warns), warns)
    check("an-unknown-role-is-ROLES_UNKNOWN",
          _code(lambda: roles.check(_profile(poet="opus"))) == "ROLES_UNKNOWN")
    check("an-OpenRouter-id-the-table-cannot-place-is-ROLES_MODEL_UNKNOWN...",
          _code(lambda: roles.check(_profile(seats="qwen/qwen3-235b"))) == "ROLES_MODEL_UNKNOWN")
    got, warns = roles.check(_profile(seats="qwen/qwen3-235b@mid"))
    check("...unless-the-author-writes-its-class,-which-the-provider-never-sees", len(warns) == 1
          and roles.model_id(got["seats"]) == "qwen/qwen3-235b" and roles.class_of("seats", "subagent:opus") == "top",
          warns)
    check("not-a-profile-is-ROLES_PROFILE_UNREADABLE", _code(lambda: roles.check({"roles": {}})) == "ROLES_PROFILE_UNREADABLE")


def cli(tmp):
    print("\n[2] profile.py: a profile written once, or refused before anything is written")
    out = os.path.join(tmp, "local.json")
    rc, text = _run(os.path.join("scripts", "profile.py"), "new", "--out", out, "--preset", "local")
    written = json.load(io.open(out, encoding="utf-8")) if os.path.isfile(out) else {}
    check("the-local-preset-writes-every-role,-the-seats-on-the-actor's-model,-and-warns", rc == 0
          and written.get("roles", {}).get("seats") == written.get("roles", {}).get("actor")
          and set(written.get("roles", {})) == set(roles.ROLES) and "warning: seats is below its floor" in text, text)
    bad = os.path.join(tmp, "bad.json")
    rc, text = _run(os.path.join("scripts", "profile.py"), "new", "--out", bad, "--set", "showrunner=ollama/qwen2.5:7b")
    check("a-refused-profile-is-never-written", rc == 1 and "ROLES_CLAUDE_ONLY" in text and not os.path.exists(bad),
          text)
    rc, text = _run(os.path.join("scripts", "profile.py"), "show", out)
    check("show-reads-it-back-with-its-warning", rc == 0 and "seats" in text and "warning:" in text, text)
    return out


class _Led:
    def __init__(self):
        self.rows = []

    def log_llm_call(self, run_id, turn, purpose, model, tokens_in=None, tokens_out=None, scene=None):
        self.rows.append((purpose, model, tokens_in, tokens_out))


def backends(tmp):
    print("\n[3] provider.py: a local seat, and subagents that answer the seats only")
    import direct
    import provider
    seen = []

    def fake_ollama(messages, model, max_tokens=4096, think=True, temperature=1.0, seed=None):
        seen.append((model, think))
        direct.LAST_USAGE.clear()
        direct.LAST_USAGE.update({"model": model, "tokens_in": 11, "tokens_out": 7})
        return '{"dimensions": {}}'

    real = direct._ollama
    direct._ollama = fake_ollama
    try:
        label = provider.configure_seats("ollama/local-seat")
        led = _Led()
        text = provider.call([{"role": "user", "content": "rate it"}], provider.seat_model(), "appraise-event",
                             led=led, run_id="r", turn=3)
        check("an-ollama-seat-is-answered-by-the-local-client,-thinking-off,-and-logged", text == '{"dimensions": {}}'
              and label == provider.seat_model() == "ollama/local-seat" and seen == [("local-seat", False)]
              and led.rows == [("appraise-event", "ollama/local-seat", 11, 7)], (seen, led.rows))
    finally:
        direct._ollama = real
    empty = os.path.join(tmp, "no-key.env")
    io.open(empty, "w", encoding="utf-8").close()
    os.environ["SWE_ENV_FILE"] = empty
    folder = os.path.join(tmp, "seats")
    provider.configure_seats("subagent:opus", replies=folder, wait=0)
    msgs = [{"role": "user", "content": "what arose?"}]
    check("a-subagent-seat-replays-from-the-seats-folder",
          _code(lambda: provider.call(msgs, provider.seat_model(), "appraise-emotion")) == "PROVIDER_REPLY_MISSING")
    check("...while-the-actor's-own-call-is-not-replayed",
          _code(lambda: provider.call(msgs, "anthropic/claude-sonnet-4.6", "act")) == "PROVIDER_NO_KEY")
    provider.use_replies(None)
    provider._REPLAY_ONLY = None
    provider._SEAT_MODEL = None
    os.environ.pop("SWE_ENV_FILE", None)


def carried(tmp, profile_file):
    print("\n[4] scene.py and brief.py carry the profile")
    book = _mk_vault(os.path.join(tmp, "profiled"))
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", _scene_cfg(tmp), "--stub",
                   "--budget", "1", "--no-keeper", "--profile", profile_file)
    con = sqlite3.connect(books.db_path(book))
    cfg = json.loads(con.execute("SELECT config FROM runs").fetchone()[0])
    con.close()
    check("scene.py-records-the-session's-choices-in-the-run's-config", rc == 0
          and cfg.get("profile", {}).get("seats") == cfg.get("models", {}).get("seats")
          and cfg["models"]["seats"].startswith("ollama/") and "profile: seats is below its floor" in out, out[-400:])
    sub = os.path.join(tmp, "sub.json")
    _run(os.path.join("scripts", "profile.py"), "new", "--out", sub, "--preset", "subagents")
    direction = os.path.join(tmp, "scene.json")
    with open(direction, "w", encoding="utf-8") as fh:
        json.dump({"book": book, "kind": "scene", "intent": "Mira keeps the lamp lit"}, fh)
    rc, out = _run(os.path.join("scripts", "brief.py"), direction, "--profile", sub)
    check("brief.py-gives-the-showrunner-the-tiers-and-the-subagent-seat-loop", rc == 0
          and "## Session profile" in out and "director opus" in out and "--profile" in out
          and "seats.py pending" in out and "spawn the showrunner at sonnet" in out, out[-600:])


def waiting(tmp):
    print("\n[5] seats.py: the prompts that wait for an answer")
    folder = os.path.join(tmp, "waiting")
    os.makedirs(folder)
    with open(os.path.join(folder, "k1.prompt.json"), "w", encoding="utf-8") as fh:
        json.dump({"key": "k1", "purpose": "appraise-event", "meta": {"turn": 4}}, fh)
    rc, out = _run(os.path.join("scripts", "seats.py"), "pending", folder)
    check("an-unanswered-prompt-is-PENDING-with-its-purpose-and-turn", rc == 0
          and "PENDING k1 appraise-event turn=4" in out, out)
    rc, out = _run(os.path.join("scripts", "seats.py"), "brief", folder, "k1")
    check("its-brief-is-the-seat-agent-naming-the-two-files", rc == 0 and "# Seat" in out
          and "k1.prompt.json" in out and "k1.reply.txt" in out and not out.startswith("---"), out[:300])
    io.open(os.path.join(folder, "k1.reply.txt"), "w", encoding="utf-8").write("{}")
    log = os.path.join(tmp, "scene.log")
    io.open(log, "w", encoding="utf-8").write("beat 1\nparked scene-x at turn 1\n")
    rc, out = _run(os.path.join("scripts", "seats.py"), "pending", folder, "--log", log)
    check("with-every-prompt-answered-and-the-run-parked:-ENDED", rc == 2 and "ENDED" in out, out)
    rc, out = _run(os.path.join("scripts", "seats.py"), "pending", folder)
    check("with-nothing-waiting-and-no-log:-TIMEOUT", rc == 3 and "TIMEOUT" in out, out)


def main():
    print("test_profile.py - the session profile (gate session-profile)\n")
    with tempfile.TemporaryDirectory(prefix="swe_profile_", ignore_cleanup_errors=True) as tmp:
        table()
        local = cli(tmp)
        backends(tmp)
        carried(tmp, local)
        waiting(tmp)
    print("\n%s: %d failure(s)" % ("OK" if not FAILS else "FAIL", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
