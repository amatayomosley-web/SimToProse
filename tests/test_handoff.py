#!/usr/bin/env python3
"""test_handoff.py - the partner route's contracts through the real commands (gate partner-contracts): brief.py
builds the showrunner's brief from a direction (the core plus the one playbook its kind names) or refuses it, builds a
specialist's brief, and ask.py answers info requests from the engine as JSON. Script-style, stdlib only."""
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))
from src.engine import books                                              # noqa: E402
from test_vault import _mk_vault                                          # noqa: E402
from test_draft_flow import _one, _run, _turn                             # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    detail = str(detail)[-300:].encode("ascii", "backslashreplace").decode("ascii")
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        FAILS.append(name)


def _brief(tmp, direction, name="d.json"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(direction if isinstance(direction, str) else json.dumps(direction))
    return _run(os.path.join("scripts", "brief.py"), path)


def briefs(tmp):
    print("[1] brief.py: a direction -> the core plus its one playbook, or a coded refusal")
    rc, out = _brief(tmp, {"book": "x", "kind": "scene", "intent": "Mira keeps the lamp lit", "budget": 3})
    check("a-scene-direction-gets-the-core,-the-scene-playbook-and-the-direction", rc == 0
          and "# Showrunner — core" in out and "# Playbook: scene" in out and "# Playbook: record" not in out
          and '"intent": "Mira keeps the lamp lit"' in out and "run every command from" in out, out)
    rc, out = _brief(tmp, {"book": "x", "kind": "approve", "draft": "d1", "words": "Keep it."})
    check("an-approval-gets-the-record-playbook", rc == 0 and "# Playbook: record" in out
          and "# Playbook: scene" not in out, out)
    for name, direction, code in (
            ("no-book-is-HANDOFF_FIELD_MISSING", {"kind": "scene", "intent": "x"}, "HANDOFF_FIELD_MISSING"),
            ("an-unknown-kind-is-HANDOFF_KIND_UNKNOWN", {"book": "x", "kind": "improvise"}, "HANDOFF_KIND_UNKNOWN"),
            ("an-approval-without-the-author's-words-is-refused", {"book": "x", "kind": "approve", "draft": "d1"},
             "HANDOFF_FIELD_MISSING"),
            ("...and-so-is-a-placeholder-for-them", {"book": "x", "kind": "approve", "draft": "d1",
                                                     "words": "<the author's words>"}, "HANDOFF_WORDS_MISSING"),
            ("a-field-nothing-reads-is-HANDOFF_FIELD_UNKNOWN", {"book": "x", "kind": "scene", "intent": "x",
                                                                 "mood": "grim"}, "HANDOFF_FIELD_UNKNOWN"),
            ("not-json-is-HANDOFF_DIRECTION_UNREADABLE", "{", "HANDOFF_DIRECTION_UNREADABLE")):
        rc, out = _brief(tmp, direction)
        check(name, rc == 1 and code in out, out)
    rc, out = _run(os.path.join("scripts", "brief.py"), "--specialist", "narrator")
    rc2, out2 = _run(os.path.join("scripts", "brief.py"), "--specialist", "nobody")
    check("a-specialist's-brief-is-its-agent-file-without-front-matter,-and-an-unknown-one-is-refused", rc == 0
          and "You are the narrator" in out and not out.startswith("---") and rc2 == 1, (out[:200], out2))


def asks(tmp):
    print("\n[2] ask.py: info requests answered as JSON, reading only")
    book = _mk_vault(os.path.join(tmp, "asked"))
    _turn(book)
    rec = books.db_path(book)
    run_id = _one(rec, "SELECT run_id FROM runs")
    rc, out = _run(os.path.join("scripts", "ask.py"), "where", "--book", book)
    got = json.loads(out) if rc == 0 else {}
    check("where-gives-the-record-and-each-run's-turns", rc == 0 and got.get("record", {}).get("role") == "open"
          and [r["run"] for r in got.get("runs", [])] == [run_id] and got["runs"][0]["turns"] >= 1, out)
    for what, extra in (("scene", ("--turn", "0")), ("knows", ("--char", "mira")), ("state", ("--char", "mira")),
                        ("edges", ("--char", "mira", "--with", "tomas_keeper")), ("facts", ("--subject", "the lamp")),
                        ("place", ("--place", "lamp_room"))):
        rc, out = _run(os.path.join("scripts", "ask.py"), what, "--book", book, "--run", run_id, *extra)
        ok = rc == 0
        try:
            json.loads(out)
        except ValueError:
            ok = False
        check("%s-answers-as-JSON" % what, ok, out)
    rc, out = _run(os.path.join("scripts", "ask.py"), "state", "--book", book)
    check("a-request-missing-its-run-is-refused-naming-it", rc != 0 and "--run" in out, out)
    fresh = _mk_vault(os.path.join(tmp, "never run"))
    rc, out = _run(os.path.join("scripts", "ask.py"), "knows", "--book", fresh, "--run", "r", "--char", "mira")
    check("a-book-never-run-is-ASK_NO_CHRONICLE-and-no-database-is-made", rc == 1 and "ASK_NO_CHRONICLE" in out
          and not os.path.exists(books.db_path(fresh)), out)


def main():
    print("test_handoff.py - the partner's contracts (gate partner-contracts)\n")
    with tempfile.TemporaryDirectory(prefix="swe_handoff_", ignore_cleanup_errors=True) as tmp:
        briefs(tmp)
        asks(tmp)
    print("\n%s: %d failure(s)" % ("OK" if not FAILS else "FAIL", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
