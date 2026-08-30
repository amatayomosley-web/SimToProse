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

        # A PARSE FAILURE MUST BE DISTINGUISHABLE FROM A CLEAN SCENE. This assertion used to read
        # `rep2 == {"continuity": [], "voice": []}` — the exact value a genuinely clean scene
        # returns — which froze the defect as the specification: a refusal, an empty body or a
        # greedy-regex overshoot all reported "no problems found" and the suite called it correct.
        def garbage(messages, model, max_tokens=1200):
            return "I could not produce JSON."
        critic._openrouter = garbage
        rep2 = critic.review_scene(TURNS, WORLD, stub=False)
        check("malformed-reply-flagged", rep2.get("parse_error"), str(rep2))
        check("malformed-reply-not-clean", rep2 != {"continuity": [], "voice": []}, str(rep2))

        # the overshoot case: a REAL finding followed by an unrelated brace later in the prose
        def overshoot(messages, model, max_tokens=1200):
            return ('{"continuity": [{"turn": 1, "issue": "count contradicts the ledger"}], '
                    '"voice": []}\n\nYou may also want to check the {other} scenes.')
        critic._openrouter = overshoot
        rep3 = critic.review_scene(TURNS, WORLD, stub=False)
        check("overshoot-does-not-read-clean", rep3 != {"continuity": [], "voice": []}, str(rep3))

        def clean(messages, model, max_tokens=1200):
            return '{"continuity": [], "voice": []}'
        critic._openrouter = clean
        rep4 = critic.review_scene(TURNS, WORLD, stub=False)
        check("genuinely-clean-has-no-error-key", "parse_error" not in rep4, str(rep4))
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
