#!/usr/bin/env python3
"""test_replies.py — a model's reply read into its record, one policy for every reply (gate actor-reply, 2026-09-25).

THE CONTRACTS PLAN, G5 (the owner's "Go"; agreed with Symphony on the board, convo #4). The actor's reply was a dict
built from six `.get()`s with everything else dropped unseen, and `bool("false")` read as an exit; its hand-supplied
twin (`--turn-json`) was checked by two copies raising a bare ValueError after the run row was written, and the chair
crashed on a file holding JSON that was not an object. `replies.actor_reply` reads both:

  [1] a MODEL's reply: the same turn as before, an extra key kept (never refused), only a JSON true exits, a
      falsy act no act, a null action or thought empty (never the word "None")
  [2] a SUPPLIED turn: refused by a registered code naming the missing or wrong-typed key; a null optional key
      absent; an extra key kept
  [3] the drivers: a malformed `--turn-json` refused before any chronicle exists; an extra key recorded in the
      committed turn's validation record, and nothing new recorded for a reply that carried none; `act` named in
      the scene driver's help, and the chair saying it keys no law by one

Script-style: check(), main(), exit code. Stdlib only. Every book here is invented (two keepers on a rock).
"""
import glob
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import replies                                  # noqa: E402
from src.engine.records import RecordError                      # noqa: E402

FAILS = []
TURN = {"action": "She trims the wick and turns up the lamp.", "thought": "steady now",
        "tags": {"type": "mundane", "summary": "tended the lamp", "dimensions": {"mastery": 0.3},
                 "durability": "transient", "confidence": 0.9, "subject": ""}}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def code(fn):
    try:
        fn()
    except RecordError as e:
        return e.code, str(e)
    return None, ""


def model_reply():
    print("[1] a model's reply")
    import direct
    r = replies.actor_reply(dict(TURN, exit=False, addressee="ada", act="trim"))
    check("a-well-formed-reply-reads-as-the-turn-always-did",
          r.as_turn() == dict(TURN, exit=False, addressee="ada", act="trim", extra=()), r.as_turn())
    r = replies.actor_reply(dict(TURN, mood="uneasy", _scratch=1))
    check("a-key-nothing-reads-is-kept-in-extra,-sorted,-not-dropped-unseen", r.extra == ("_scratch", "mood"), r.extra)
    check("...and-the-turn-it-carried-is-still-read", r.action == TURN["action"] and r.tags == TURN["tags"])
    for label, value, want in (("the-string-false", "false", False), ("the-string-true", "true", False),
                               ("a-one", 1, False), ("JSON-true", True, True), ("absent", None, False)):
        obj = dict(TURN) if value is None else dict(TURN, exit=value)
        check("exit-is-only-a-JSON-true:-%s" % label, replies.actor_reply(obj).exit is want)
    empty = replies.actor_reply(["not", "an", "object"]).as_turn()
    check("a-non-object-is-an-empty-draw-(the-retry-loop-redraws-it)",
          empty == {"action": "", "thought": "", "exit": False, "addressee": "", "act": "", "tags": {"dimensions": {}},
                    "extra": ()}, empty)
    check("a-non-object-tags-is-replaced-by-an-empty-block",
          replies.actor_reply(dict(TURN, tags="calm")).tags == {"dimensions": {}})
    for label, value in (("null", None), ("false", False), ("zero", 0), ("an-empty-list", [])):
        check("a-%s-act-is-no-act-(never-the-word,-which-the-law-check-would-weigh)" % label,
              replies.actor_reply(dict(TURN, act=value)).act == "", replies.actor_reply(dict(TURN, act=value)).act)
    r = replies.actor_reply(dict(TURN, action=None, thought=None))
    check("a-null-action-or-thought-is-empty,-never-the-word-None", r.action == "" and r.thought == "", r)
    turn = direct._parse_reply('Here you go: {"action": "She sits.", "thought": "", "exit": "false", "mood": 2} ok')
    check("_parse_reply:-the-text-is-read-through-the-record", turn["action"] == "She sits." and turn["exit"] is False
          and turn["extra"] == ("mood",), turn)
    check("_parse_reply:-garbage-is-an-empty-draw", direct._parse_reply("no json here")["action"] == "")


def supplied_turn():
    print("[2] a supplied turn")
    for label, obj in (("null", None), ("a-list", [TURN]), ("a-number", 42)):
        got, msg = code(lambda: replies.actor_reply(obj, supplied=True))
        check("not-an-object-is-refused:-" + label, got == "REPLY_NOT_AN_OBJECT", (got, msg))
    got, msg = code(lambda: replies.actor_reply({"action": "a"}, supplied=True))
    check("a-missing-field-is-refused-naming-it-and-the-contract",
          got == "REPLY_FIELD_MISSING" and "thought, tags" in msg and "act?" in msg, (got, msg))
    for label, edit in (("action-a-number", {"action": 5}), ("exit-a-word", {"exit": "yes"}),
                        ("tags-a-string", {"tags": "calm"}), ("addressee-a-list", {"addressee": ["ada"]}),
                        ("act-a-number", {"act": 3})):
        got, msg = code(lambda: replies.actor_reply(dict(TURN, **edit), supplied=True))
        check("a-wrong-typed-field-is-refused-naming-it:-" + label,
              got == "REPLY_FIELD_TYPE" and ("a supplied turn's %s:" % label.split("-")[0]) in msg, (got, msg))
    got, msg = code(lambda: replies.actor_reply(dict(TURN, action=5, exit="yes"), supplied=True))
    check("two-wrong-typed-fields-are-both-named", got == "REPLY_FIELD_TYPE" and "a supplied turn's action, exit:" in msg,
          (got, msg))
    for label, edit in (("action", {"action": None}), ("tags", {"tags": None})):
        got, msg = code(lambda: replies.actor_reply(dict(TURN, **edit), supplied=True))
        check("a-null-REQUIRED-field-is-wrong-typed,-not-absent:-" + label,
              got == "REPLY_FIELD_TYPE" and ("a supplied turn's %s:" % label) in msg, (got, msg))
    got, msg = code(lambda: replies.actor_reply(dict(TURN, exit=None, addressee=None, act=None), supplied=True))
    r = replies.actor_reply(dict(TURN, exit=None, addressee=None, act=None), supplied=True) if got is None else None
    check("a-null-OPTIONAL-field-is-absent,-as-a-model's-is", got is None and r.exit is False and r.addressee == ""
          and r.act == "" and r.extra == (), (got, msg, r))
    r = replies.actor_reply(dict(TURN, mood="uneasy"), supplied=True)
    check("an-extra-key-is-kept,-not-refused,-in-a-supplied-turn-too", r.extra == ("mood",), r.extra)


def _book(tmp):
    from test_systems import _book as build
    return build(tmp)


def _dbs(book):
    return glob.glob(os.path.join(book, "runs", "*.db"))


def _run(*argv):
    r = subprocess.run([sys.executable] + list(argv), cwd=REPO, capture_output=True, text=True, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _file(tmp, name, content):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content if isinstance(content, str) else json.dumps(content))
    return p


def _scene_cfg(tmp):
    return _file(tmp, "gale.json", {"name": "gale", "at": {"day": 1, "time": "21:00"}, "lasts": "1h",
                                    "situation": "The two keepers wait out the gale in the lamp room.",
                                    "cast": [{"id": "mira", "drive": "keep the lamp lit"},
                                             {"id": "ada", "drive": "get the boat ready"}]})


def drivers():
    print("[3] the drivers")
    tmp = tempfile.mkdtemp(prefix="replies_")
    for label, content, want in (("a-supplied-turn-missing-its-tags",
                                  {"action": "She sits.", "thought": "tired"}, "REPLY_FIELD_MISSING"),
                                 ("a-file-that-is-not-JSON", "{\"action\": ", "is not valid JSON")):
        book = _book(os.path.join(tmp, "scene-" + label))
        rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", _scene_cfg(tmp), "--stub",
                       "--budget", "1", "--no-keeper", "--turn-json", _file(tmp, label + ".json", content))
        check("scene.py:-%s-is-refused-before-any-chronicle-exists" % label,
              rc != 0 and want in out and not _dbs(book) and "Traceback" not in out, out[-500:])
    for label, content, want in (("a-file-holding-null", "null", "REPLY_NOT_AN_OBJECT"),
                                 ("an-exit-that-is-a-word", dict(TURN, exit="no"), "REPLY_FIELD_TYPE")):
        book = _book(os.path.join(tmp, "chair-" + label))
        rc, out = _run(os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira", "--stub",
                       "--circumstance", "the lamp gutters", "--turn-json", _file(tmp, "c-" + label + ".json", content))
        check("direct.py:-%s-is-refused-before-any-chronicle-exists" % label,
              rc != 0 and want in out and not _dbs(book) and "Traceback" not in out, out[-500:])
    book = _book(os.path.join(tmp, "chair-extra"))
    validations = {}
    for label, content in (("plain", TURN), ("extra", dict(TURN, mood="uneasy")), ("act", dict(TURN, act="steal"))):
        rc, out = _run(os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira", "--stub",
                       "--circumstance", "the lamp gutters", "--turn-json", _file(tmp, "x-" + label + ".json", content))
        check("direct.py:-a-supplied-turn-commits-(%s)" % label, rc == 0 and "committed" in out, out[-500:])
        validations[label] = _last_validation(book)
        if label == "extra":
            check("...and-reports-the-key-nothing-reads", "key(s) nothing reads: mood" in out, out[-500:])
        if label == "act":
            check("...and-says-the-chair-keys-no-law-by-an-act", "the chair keys no law by an act, so it reads none: steal]"
                  in out, out[-500:])     # printed as ASCII since gate seat-replies (it was %r, and crashed a cp1252 console)
    check("an-extra-key-is-recorded-in-the-committed-turn's-validation-record",
          validations.get("extra", {}).get("reply_extra") == ["mood"], validations.get("extra"))
    check("...and-a-reply-without-one-records-nothing-new",
          "reply_extra" not in validations.get("plain", {"reply_extra": 1}), validations.get("plain"))
    check("...and-an-act-is-a-contract-key,-never-an-extra-one",
          "reply_extra" not in validations.get("act", {"reply_extra": 1}), validations.get("act"))
    book = _book(os.path.join(tmp, "scene-extra"))
    rc, out = _run(os.path.join("scripts", "scene.py"), "--book", book, "--scene", _scene_cfg(tmp), "--stub", "--budget", "1",
                   "--no-keeper", "--turn-json", _file(tmp, "s-extra.json", dict(TURN, mood="uneasy")))
    got = None
    if rc == 0 and _dbs(book):
        con = sqlite3.connect(_dbs(book)[0])
        try:
            got = [json.loads(v).get("reply_extra") for (v,) in con.execute("SELECT validation FROM turns ORDER BY turn")]
        finally:
            con.close()
    check("scene.py:-the-supplied-beat-records-its-extra-key-in-its-validation-record", got == [["mood"]],
          (rc, got, out[-400:]))
    rc, out = _run(os.path.join("scripts", "scene.py"), "--help")
    check("scene.py:-the---turn-json-help-names-act", "addressee?, act?}" in " ".join(out.split()), out[-400:])
    rc, out = _run(os.path.join("scripts", "direct.py"), "--help")
    flat = " ".join(out.split())
    check("direct.py:-the---turn-json-help-offers-no-act,-and-says-why",
          "addressee?}" in flat and "act?}" not in flat and "the chair keys no law" in flat, out[-600:])


def _last_validation(book):
    """-> the newest committed turn's validation record, as the ledger wrote it."""
    con = sqlite3.connect(_dbs(book)[0])
    try:
        row = con.execute("SELECT validation FROM turns ORDER BY rowid DESC LIMIT 1").fetchone()
    finally:
        con.close()
    return json.loads(row[0]) if row else {}


def main():
    model_reply()
    supplied_turn()
    drivers()
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
