#!/usr/bin/env python3
"""test_compose_event.py — what the next actor PERCEIVES (src/engine/prompt.py).

These three assertions travelled with the function: `scripts/scene.py` -> `floor.py` -> `prompt.py`,
all on 2026-09-03. They pin the three things `compose_event` is scarred by, each measured before it
was fixed: unconditional dinner-fixture text on an empty log, a 300-character truncation that fed
the next actor a fragment, and a window that must show only the last n beats.

Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.prompt import compose_event                       # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % detail))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def test_compose_event_returns_the_situation_UNTOUCHED_on_an_empty_log():
    """The bug this function is scarred by: on an empty log it used to append "The table has just
    been served; the evening is beginning" — dinner-fixture text, unconditionally, so the FIRST
    BEAT OF EVERY SCENE IN EVERY BOOK was told it was evening at a table. Measured on a dawn dock
    scene. The situation is the director's, and it comes back as written."""
    sit = "Dawn on the dock. The tide is out."
    check("empty-log-returns-the-situation-verbatim", compose_event(sit, []) == sit,
          repr(compose_event(sit, [])))
    check("no-fixture-furniture-leaks-in",
          "table" not in compose_event(sit, "").lower(), "the dinner fixture reappeared")


def test_compose_event_does_not_TRUNCATE_a_long_beat():
    """It cut each action to 300 characters, so a long beat reached the next actor mid-sentence and
    they answered a fragment. The whole action must survive."""
    long_action = "x" * 900 + "THE-END-OF-THE-SENTENCE"
    out = compose_event("A room.", [{"who": "a", "action": long_action}], {"a": "Ada"})
    check("the-whole-action-survives", long_action in out,
          "%d chars of %d present" % (len(out), len(long_action)))
    check("the-speaker-is-named", "Ada" in out, out[:80])


def test_compose_event_shows_only_the_LAST_n_beats():
    log = [{"who": "a", "action": "beat-%d" % i} for i in range(10)]
    out = compose_event("A room.", log, n=3)
    check("keeps-the-last-3", all("beat-%d" % i in out for i in (7, 8, 9)), out[-90:])
    check("drops-the-earlier-ones", "beat-6" not in out, "an older beat leaked in")



def main():
    print("test_compose_event.py - what the next actor perceives\n")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print("\n%s" % ("test_compose_event: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
