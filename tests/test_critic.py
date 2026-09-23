#!/usr/bin/env python3
"""test_critic.py — the continuity + voice critic (design.md layer 6, detect-only).

Proves gate swe-critic-continuity-voice: the stub path is clean, the prompt carries the world canon +
transcript, and a strong-model reply parses into the structured {continuity, voice} report. The
strong-model dispatch (critic._openrouter) is monkeypatched so the parse is exercised with no API.
Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import world_events                          # noqa: E402
from src.engine.ledger import Ledger                         # noqa: E402
from src.engine.records import Event, PATHS, TurnCommit      # noqa: E402
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

    # 4. ONE REVIEW PER RECORDED SCENE (2026-09-18). The first model run over a live book reached
    # the critic with only its first few beats: main() reviewed the whole run as one transcript under a cap
    # sized for 121-char beats. review_run walks the scene rows and reviews each with its own turns.
    class _Led:
        """A stand-in with the two reads review_run makes; Ledger.scenes_for itself is covered by
        tests/test_narrate.py, and writing real turns here would mean running two stub scenes."""
        def __init__(self, scenes):
            self._scenes = scenes
        def scenes_for(self, run_id):
            return list(self._scenes)
    four = TURNS + [{"turn": 2, "actor": "maren", "action": "The ward is quiet.", "thought": ""},
                    {"turn": 3, "actor": "edda", "action": "Quiet is not the same as well.", "thought": ""}]
    _real_turns = critic.scene_turns
    critic.scene_turns = lambda led, run_id: list(four)
    seen = []
    try:
        def per_scene(messages, model, max_tokens=1200):
            seen.append(messages[1]["content"])
            return '{"continuity": [], "voice": []}'
        critic._openrouter = per_scene
        two = [{"scene_no": 0, "label": "fireside", "pov": "maren", "start_turn": 0, "end_turn": 1},
               {"scene_no": 1, "label": "the-ward", "pov": "edda", "start_turn": 2, "end_turn": 3}]
        rep = critic.review_run(_Led(two), "bk", WORLD, stub=False)
        check("per-scene-two-entries", [e["scene_no"] for e in rep.get("scenes", [])] == [0, 1], str(rep))
        check("per-scene-two-model-calls", len(seen) == 2, len(seen))
        check("per-scene-first-call-carries-only-scene-0", "ride to the town" in seen[0] and "ward is quiet" not in seen[0])
        check("per-scene-second-call-carries-only-scene-1", "ward is quiet" in seen[1] and "ride to the town" not in seen[1])
        check("per-scene-entries-name-their-turns", [e["turns"] for e in rep["scenes"]] == [[0, 1], [2, 3]], str(rep))
        flat = critic.review_run(_Led([]), "bk", WORLD, stub=True)
        check("no-scene-rows-is-the-flat-shape", flat == {"continuity": [], "voice": []}, str(flat))
        prompts = critic.prompts_for_run(_Led(two), "bk", WORLD)
        check("prompt-only-is-one-prompt-per-scene", len(prompts) == 2 and all(len(p) == 2 for p in prompts))
        # the caps are sized to the book that measured them, not the probe
        check("transcript-cap-holds-a-fourteen-beat-scene", critic._TRANSCRIPT_CAP >= 45000, critic._TRANSCRIPT_CAP)
        check("canon-cap-holds-the-live-cast-and-places", critic._CANON_CAP >= 1500, critic._CANON_CAP)
    finally:
        critic._openrouter = _real
        critic.scene_turns = _real_turns

    # 5. THE CORRECTION HALF (2026-09-19) — consolidation-loop.md open-q 3's emitter. The critic
    # still never edits: a continuity flag becomes an APPENDED `correction` row naming the flagged
    # turn's world-moving event ids, and the fold treats those as superseded (tests/test_fold.py).
    # A real Ledger here, not a stand-in: the whole point is that the flags reach the RECORD.
    tmp = tempfile.mkdtemp(prefix="swe_critic_correct_")
    try:
        led = Ledger(os.path.join(tmp, "chronicle.db"))
        led.create_run("bk", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
        led.register_character("bk", "maren", {"name": "Maren"}, {})
        led.register_character("bk", "edda", {"name": "Edda"}, {})
        aff = {p: 0.5 for p in PATHS}
        for turn, actor in ((0, "maren"), (1, "edda"), (2, "maren"), (3, "edda")):
            # EVERY turn carries the actor's own appraisal row — `mundane` has world_map "none", so
            # it is exactly what `supersedes` must NOT name. Turn 3 carries only that.
            led.append_turn(TurnCommit(run_id="bk", turn=turn, actor=actor, thought="", action="a%d" % turn,
                                       tags={"type": "mundane"}, affect=dict(aff), condition={},
                                       events=[Event(type="mundane", actor=actor, payload={})],
                                       validation={}))
        # ...and turn 2 also moved the world, twice.
        world_events.append(led, "bk", 2, [Event(type="move", actor="maren", payload={"to": "ward"}),
                                           Event(type="seize", actor="maren", payload={"asset": "the-mill"})])
        on_turn_2 = led.con.execute(
            "SELECT event_id, type FROM events WHERE run_id='bk' AND turn=2").fetchall()
        moving = {r["event_id"] for r in on_turn_2 if r["type"] in critic.world_moving_types()}

        review = {"scenes": [{"scene_no": 0, "label": "the-ward", "turns": [0, 3],
                              "continuity": [{"turn": 2, "issue": "the second healer was re-invented"}],
                              "voice": [{"chars": ["maren", "edda"], "issue": "alike"}]}]}
        appended = critic.correct_run(led, "bk", review)
        rows = led.corrections_for("bk")
        check("one-flag-one-correction", len(appended) == 1 and len(rows) == 1, str(appended))
        payload = json.loads(rows[0]["payload"])
        check("supersedes-is-the-turn's-WORLD-MOVING-ids", set(payload["supersedes"]) == moving,
              "%s vs %s" % (payload["supersedes"], sorted(moving)))
        check("...which-is-2-of-the-3-events-that-turn-recorded",
              len(moving) == 2 and len(on_turn_2) == 3, "%d of %d" % (len(moving), len(on_turn_2)))
        check("the-issue-text-is-carried", payload["issue"] == "the second healer was re-invented", str(payload))
        check("the-flagged-turn-is-named", payload["turn"] == 2 and payload["source"] == "critic")
        check("the-actor-is-the-flagged-turn's", rows[0]["actor"] == "maren", rows[0]["actor"])
        check("visibility-is-the-catalog's", rows[0]["visibility"] == "private-to-actor", rows[0]["visibility"])
        check("it-landed-at-the-run's-NEXT-tick", rows[0]["effective_at"] == 4, rows[0]["effective_at"])
        check("a-voice-flag-writes-nothing", len(rows) == 1, str(rows))

        # a flag on a turn that moved NOTHING still appends — the audit trail (detector #6)
        flat = {"continuity": [{"turn": 3, "issue": "the lamp relights itself"}], "voice": []}
        critic.correct_run(led, "bk", flat)
        rows = led.corrections_for("bk")
        empty = [json.loads(r["payload"]) for r in rows if json.loads(r["payload"])["turn"] == 3]
        check("a-flag-with-no-world-event-still-appends", len(empty) == 1, str(rows))
        check("...with-an-EMPTY-supersedes-list", empty[0]["supersedes"] == [], str(empty))
        check("the-flat-review-shape-is-walked-too", len(rows) == 2, str(rows))

        # IDEMPOTENT ON (turn, issue) — the log cannot be de-duplicated afterwards (hard rule 2)
        check("re-running-the-same-review-appends-nothing", critic.correct_run(led, "bk", review) == [])
        check("...and-the-log-still-has-two", len(led.corrections_for("bk")) == 2)
        check("a-DIFFERENT-issue-on-the-same-turn-does-append",
              len(critic.correct_run(led, "bk", {"continuity": [{"turn": 2, "issue": "the poultice made twice"}]})) == 1)

        # and the fold now agrees: the flagged turn's move no longer lands
        check("the-fold-drops-the-superseded-move",
              led.fold("bk", 4)["agents"]["maren"]["location"] is None,
              str(led.fold("bk", 4)["agents"]["maren"]))
        check("a-clean-review-appends-nothing",
              critic.correct_run(led, "bk", {"continuity": [], "voice": []}) == [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if FAILS:
        print("\ntest_critic: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_critic: OK (stub clean, prompt carries canon+transcript, strong-model reply parses)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
