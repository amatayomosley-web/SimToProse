#!/usr/bin/env python3
"""test_critic.py — the continuity + voice critic (design.md layer 6, detect-only).

Proves gate swe-critic-continuity-voice: the stub path is clean, the prompt carries the world canon +
transcript, and a strong-model reply parses into the structured {continuity, voice} report. The
strong-model dispatch (critic._openrouter) is monkeypatched so the parse is exercised with no API.
Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import critic                                                # noqa: E402

WORLD = {
    "standing_facts": ["Ashford is remote: the nearest second healer is two days' walk.",
                       "Maren is the only healer; if she fails, there is no one else nearby."],
    "people": [{"id": "edda_elder", "what": "the village elder"},
               {"id": "joss_apprentice", "name": "Joss"}],
    "locations": [{"id": "cottage", "what": "Maren's cottage at the village edge"}],
}
TURNS = [
    {"turn": 0, "actor": "maren", "action": "I will ride to the town for the other healer.", "thought": ""},
    {"turn": 1, "actor": "edda", "action": "There is no other healer within two days. You are all we have.", "thought": ""},
]
FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def main():
    print("test_critic.py — continuity + voice critic\n")

    # 1. stub + empty -> clean
    check("stub-clean", critic.review_scene(TURNS, WORLD, stub=True) == {"continuity": [], "voice": []})
    check("empty-scene-clean", critic.review_scene([], WORLD) == {"continuity": [], "voice": []})

    # 2. the prompt carries the canon + the transcript
    msgs = critic.build_critic_prompt(TURNS, WORLD)
    blob = " ".join(m["content"] for m in msgs)
    check("prompt-has-standing-fact", "only healer" in blob, "facts missing from prompt")
    check("prompt-has-transcript", "ride to the town" in blob, "transcript missing from prompt")
    check("prompt-has-who", "joss_apprentice" in blob and "Joss" in blob, "people summary missing")
    check("prompt-json-serializable", len(json.loads(json.dumps(msgs))) == 2)  # --prompt-only must round-trip for Claude-in-the-loop

    # 3. a strong-model reply parses into the structured report (dispatch monkeypatched)
    _real = critic._openrouter
    try:
        def canned(messages, model, max_tokens=1200):
            return ('Here is my review:\n{"continuity": [{"turn": 1, "issue": "contradicts: a second '
                    'healer two days off vs none nearby"}], "voice": []}\nThanks.')
        critic._openrouter = canned
        rep = critic.review_scene(TURNS, WORLD, stub=False)
        check("parses-continuity-flag", len(rep["continuity"]) == 1 and rep["continuity"][0]["turn"] == 1, str(rep))
        check("parses-empty-voice", rep["voice"] == [])

        def garbage(messages, model, max_tokens=1200):
            return "I could not produce JSON."
        critic._openrouter = garbage
        rep2 = critic.review_scene(TURNS, WORLD, stub=False)
        check("malformed-reply-empty", rep2 == {"continuity": [], "voice": []}, str(rep2))
    finally:
        critic._openrouter = _real

    if FAILS:
        print("\ntest_critic: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_critic: OK (stub clean, prompt carries canon+transcript, strong-model reply parses)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
