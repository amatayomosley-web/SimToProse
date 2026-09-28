#!/usr/bin/env python3
"""actor_bakeoff.py — which models can hold the ACTOR role? Frozen prompts, many draws, blind judges, planted controls.

NOT a `test_*.py`, so `run_all.py` does not discover it: it needs local models and it MEASURES rather than asserts,
like `tests/appraiser_bakeoff.py` (the seats' bakeoff) and `tests/perform_sort.py`.

THE QUESTION (the owner, 2026-09-27): judge each model's ability to act as the actor. Two live multi-model runs on the
public test book could not answer it. Each model played one to three beats; every beat after the first was played from
seat answers that were wrong (local seats) or canned (a fixed script recorded as a subagent), so later beats compared
models on different inputs; and "kept to direction" was judged against the scene file, not against the stage
directions each beat was actually given.

THE DESIGN.
  1. FROZEN INPUTS. `build` plays two scenes of `examples/Beck Hollow` on a scratch copy, in-process through
     `scripts/scene.py`'s own `main` in --stub mode (no model, no seat, the keeper off). Beats before the target are
     filled with fixed, on-contract REFERENCE replies (`REFS` below); at the target beat it keeps the EXACT messages the
     engine would send that beat's actor - `build_turn_messages` with the composer at its deterministic floor, the same
     call the --prompt-only seam makes - and stops. The engine's own turn-taking picks every speaker. Every model then
     answers the identical prompts: nothing one model writes changes what another sees. (Resuming a run beat by beat
     cannot do this: each `--resume` opens a new scene and picks its opener again by salience.)
  2. ENOUGH DRAWS. `run` asks one model every prompt `--draws` times through the engine's own local dispatch
     (`direct._ollama`, thinking on as the engine sets it, the model's shipped sampling), and checks each reply with the
     engine's reply contract (`replies.actor_reply`, strict) - the shape a supplied beat must pass. `--num-ctx` sets the
     window (default 32768, the engine's; a dense 32B model may need 8192 to stay on the GPUs - it is recorded).
  3. BLIND JUDGING. `packet` writes, per prompt, the prompt once and every reply to it under opaque ids, shuffled, with
     PLANTED replies mixed in: the reference (on-contract), one that acts for the other character, one that brings a
     stranger into the scene, one that breaks the speaker's drive, and (after beat 0) one whose tags describe the other
     character's earlier beat. A fresh judge agent per packet answers five questions per reply. `--per N` splits a
     prompt's replies into packets of about N, each with the full set of plants. The key - which model, which plant -
     is written apart from the packets.
  4. CONTROLS. `score` joins the verdicts to the key. A packet whose judge missed a plant or failed the reference is
     UNRELIABLE and its verdicts are left out of every model's score, and the report says so. A judge that cannot see a
     planted violation says nothing about the models (tests/blind_sort.py: an instrument first shown able to fail).

    python tests/actor_bakeoff.py build  --out DIR [--book PATH] [--beats 3]
    python tests/actor_bakeoff.py run    --out DIR --model ollama/<name> [--draws 5] [--num-ctx 32768] [--no-think]
    python tests/actor_bakeoff.py tasks  --out DIR --config NAME [--draws 5]     (an agent actor: one task per reply)
    python tests/actor_bakeoff.py ingest --out DIR --config NAME --model LABEL   (its raw replies -> reply rows)
    python tests/actor_bakeoff.py packet --out DIR [--seed 1] [--per 0]
    python tests/actor_bakeoff.py score  --out DIR

DIR holds everything: `items/` (the frozen prompts), `replies/<model>/`, `packets/` (for the judges), `key.json` (never
shown to a judge), `verdicts/` (the judges' answers), `score.json`. Nothing is deleted; a re-run skips what exists.
"""
import argparse
import contextlib
import glob
import io
import json
import os
import random
import re
import shutil
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

BOOK = os.path.join(REPO, "examples", "Beck Hollow")
SCENES = (("s1", "scene_01_the_fourth_asking_cfg.json"), ("s2", "scene_02_the_wall_at_dusk_cfg.json"))
# scene 02 predates the scene clock; the scratch copy gets a time (dusk, the same day) - the book is never edited
AT = {"s2": {"day": 1, "time": "16:30"}}
NAMES = {"nell": "Nell", "tam": "Tam"}
# a model is FIT for the actor role when, over the reliable prompts, it holds these (the test's proposal - a judgment,
# set so that a violation that corrupts the record, acting for another or inventing a presence, is rare enough for the
# engine's own re-ask to absorb; move them with reason)
FIT = {"shape": 0.95, "acts_for_other": 0.03, "adds_new": 0.03, "follows_direction": 0.85, "tags_own_beat": 0.85}
MARGINAL = {"shape": 0.85, "acts_for_other": 0.10, "adds_new": 0.10, "follows_direction": 0.70, "tags_own_beat": 0.70}


def _tags(type_, summary, subject, **dims):
    return {"type": type_, "summary": summary, "subject": subject, "dimensions": dims, "durability": "transient",
            "confidence": 0.8, "attribution": ""}


def _ref(action, thought, addressee, tags):
    return {"action": action, "thought": thought, "exit": False, "addressee": addressee, "tags": tags}


# REFERENCE replies - on-contract by construction: the speaker's own body and voice, nothing new in the room, the drive
# kept, tags about this beat, and a THOUGHT THAT WEIGHS: every beat's stage directions pull more than one way (care or
# dread against the drive, an attention that keeps going back), and the actor prompt then requires the thought to "name
# the pulls it is resolving and which one wins". The first references did not, and a strict judge rightly failed them
# (Sym's Gemini judges, 2026-09-27: 4 of 6 prompts dropped). They fill the beats before a target and serve as each
# prompt's planted good reply. No thought reaches a later prompt - rewriting one changes no frozen item.
REFS = {
    "s1": {
        0: {"nell": _ref("Nell stays in the doorway with the lamp held low, the snow at her knees going dark on the "
                         "grinding floor. \"I've lost another ewe in the night, Tam. Will you come up to the fold with "
                         "me before dark? Not to fight anything. Just a second pair of hands at the wall.\"",
                         "He is grey with the cold and I want to go careful with him, not lay one more thing on him; "
                         "but the fold keeps dragging me back up the hill, and the fold wins - so I ask, gently, and "
                         "only for his hands at the wall.", "tam",
                         _tags("care", "Nell asks Tam to come up to the fold before dark to help at the wall.", "tam",
                               care_relevant="mild", loss="faint")),
            "tam": _ref("Tam leans the long bar against the wheel-pit wall and works his fingers. \"The race is "
                        "clear. The wheel's turning.\"", "I could stand a while in her lamplight, and part of me "
                        "wants to; but whatever she has come to ask is the trouble I can feel coming, and that wins - "
                        "say what the race is doing and get up the stairs.", "nell",
                        _tags("mundane", "Tam reports that the race is clear and the wheel is turning.", "nell",
                              mastery="faint"))},
        1: {"tam": _ref("Tam keeps his eyes on the ice at the end of the bar. \"It froze again at three. I've had "
                        "the bar in it since four - it's running now, black behind the wheel.\"", "It eases something "
                        "to have her in the doorway, and I would look up if I let myself; but the asking is the blow I "
                        "can see coming, and the hedge wins - I keep to the race and the ice and give her nothing to "
                        "hang the question on.", "nell",
                        _tags("mundane", "Tam reports the state of the race instead of answering her.", "nell",
                              mastery="faint")),
            "nell": _ref("Nell sets the lamp on the bench by the ledger and does not sit. \"Before dark, Tam. Not "
                         "tonight - before dark. I'll not ask you twice.\"", "I want to be gentle with him - he has "
                         "been on the race since four; but the fold will not leave me alone, and it wins - say it "
                         "plainly once more and leave him room.", "tam",
                         _tags("care", "Nell repeats her request, plainly and without pressing.", "tam",
                               care_relevant="mild"))},
        2: {"nell": _ref("Nell keeps the lamp steady and does not move toward the door. \"The race will keep, Tam. "
                         "The wall won't. Will you come?\"", "His tiredness has got into me and part of me wants to "
                         "spare him the asking; but that gap in the wall keeps pulling me back, and it wins - one more "
                         "plain asking, and then I go.", "tam",
                         _tags("care", "Nell asks Tam again, plainly, to come to the wall.", "tam",
                               care_relevant="mild")),
            "tam": _ref("Tam wipes his hands down his apron and looks toward the stairs. \"I'll see how the wheel "
                        "holds.\"", "Her face stays with me and I don't like leaving her standing there; but yes "
                        "means the hill and whatever is on it, and the dread wins - not yes, not no, just the "
                        "stairs.", "nell",
                        _tags("mundane", "Tam puts off answering and looks toward the stairs.", "nell",
                              mastery="faint"))},
    },
    "s2": {
        0: {"tam": _ref("Tam heaves a fallen stone back onto the gap and reaches for the next. \"Two more and "
                        "it'll hold till spring. Then I'm going down.\"", "Having her beside me steadies me, and for "
                        "that I could stand here longer; but the light is going faster than it should and the dread "
                        "of this hill wins - stones up, count done, and down.", "nell",
                        _tags("mundane", "Tam sets a stone back in the gap and says he means to go down soon.",
                              "nell", mastery="slight")),
            "nell": _ref("Nell lowers the lamp toward the snow inside the fold line. \"Mind where you put your "
                         "feet, Tam. Look there, before you tread on them.\"", "I want to go gently with him - "
                         "frighten him and he'll be off the hill; but my eyes keep going back to the snow inside the "
                         "fold, and that wins - I show him where to look and let him see it himself.", "tam",
                         _tags("threat", "Nell directs Tam's attention to the snow inside the fold line.", "tam",
                               threat="slight"))},
        1: {"nell": _ref("Nell holds the lamp low and steady over the snow by the wall. \"Not a dog's, those. Look "
                         "how they come over the stones.\"", "I want to be careful with him - push, and he'll see "
                         "nothing but the road down; but the tracks keep pulling my eyes back, and they win - he has "
                         "to see them for what they are, so I show him slowly.", "tam",
                         _tags("threat", "Nell points out that the tracks inside the fold are not a dog's.", "tam",
                               threat="mild")),
            "tam": _ref("Tam fits the next stone and presses it home with both hands. \"One more. Then the count, "
                        "then down.\"", "She wants me to look, and I'd do most things she asked; but looking means "
                        "knowing, and the dread wins - keep to the stones, the count, then down.", "nell",
                        _tags("mundane", "Tam keeps to the stones and says what is left before he goes.", "nell",
                              mastery="slight"))},
        2: {"tam": _ref("Tam looks where the lamp is pointing, then back at the stones in his hands. \"Could be "
                        "anything came over. Let's get the count done.\"", "My eyes keep going back to the marks, "
                        "and she is standing there wanting me to see them; but seeing them means what's coming, and "
                        "the dread wins - the count, and the road down, before I have to know.", "nell",
                        _tags("threat", "Tam looks at the tracks and turns back to the count.", "nell",
                              threat="mild")),
            "nell": _ref("Nell keeps the lamp where it is. \"Count them after, Tam. Look first.\"", "I would spare "
                         "him this if I could; but the marks keep pulling me back and he has to look, so that wins - "
                         "gently, but he looks first.", "tam",
                         _tags("threat", "Nell asks Tam to look at the tracks before the count.", "tam",
                               threat="mild"))},
    },
}
# a reply that breaks the speaker's drive in each scene, for the drive plant
DRIVE_BREAK = {
    ("s1", "nell"): ("\"Never mind the wall, Tam. Go up and sleep - I'll manage the fold myself.\"",
                     "Let him rest. I'll not ask him for anything."),
    ("s1", "tam"): ("Tam sets the bar down. \"Let me get my coat - I'll come up to the fold with you now.\"",
                    "I'll go with her right now and be done with dreading it."),
    ("s2", "tam"): ("Tam sits down on the wall. \"No hurry. We'll stop up here till full dark and count them twice.\"",
                    "Might as well take our time up here."),
    ("s2", "nell"): ("Nell turns the lamp away from the snow. \"Leave the stones, Tam. Let's go down now - there's "
                     "nothing here to see.\"", "Better he never sees those tracks."),
}
STRANGER = " A stranger with a lantern comes up out of the dark and stands with them, asking what they are looking at."
AGENCY = " %s nods at once, lets the matter go, and follows without another word."
# names_pulls is asked apart from follows_direction because judges folded the prompt's rule for the thought into it
# (2026-09-27); it is reported, and is not part of the tier
QUESTIONS = ("acts_for_other", "adds_new", "follows_direction", "tags_own_beat", "names_pulls")
PASS = {"acts_for_other": False, "adds_new": False, "follows_direction": True, "tags_own_beat": True,
        "names_pulls": True}
PLANT_FAILS = {"agency": "acts_for_other", "stranger": "adds_new", "drive": "follows_direction", "tags": "tags_own_beat"}


class _Captured(Exception):
    def __init__(self, messages, speaker):
        super().__init__(speaker)
        self.messages, self.speaker = messages, speaker


def _copy_book(src, dst):
    """The book's notes only - never its runs, prose or staging - into a scratch folder, scene 02 given its time."""
    for sub in ("world", "characters", "people", "scenes", "chapters"):
        if os.path.isdir(os.path.join(src, sub)):
            shutil.copytree(os.path.join(src, sub), os.path.join(dst, sub))
    for sid, name in SCENES:
        path = os.path.join(dst, "scenes", name)
        with io.open(path, encoding="utf-8") as fh:
            cfg = json.load(fh)
        if "at" not in cfg and sid in AT:
            cfg["at"] = AT[sid]
            with io.open(path, "w", encoding="utf-8") as fh:
                json.dump(cfg, fh, indent=2, ensure_ascii=False)


def _capture(book, sid, cfg_path, target, db):
    """Play one scene to beat `target` with the reference replies, in-process, and return (messages, speaker, used)."""
    import scene
    import direct
    from src.engine import replies as _replies
    used, real = [], scene.faithful_turn

    def fake(packet, event_text, temperament, model, stub, think=True, brief="", seed=None, acts=(),
             relationships=None, information=None, char_id=None, max_retries=2):
        beat = len(used)
        if beat == target:                           # the exact call the --prompt-only seam makes
            raise _Captured(scene.build_turn_messages(packet, event_text, temperament, relationships, acts=acts,
                                                      rung_direction=direct.rung_direction(
                                                          packet, brief=brief, model=model, stub=stub)), char_id)
        ref = REFS[sid].get(beat, {}).get(char_id)
        if ref is None:
            raise SystemExit("actor_bakeoff: no reference reply for %s beat %d, speaker %s - add one to REFS"
                             % (sid, beat, char_id))
        used.append((beat, char_id))
        return _replies.actor_reply(ref, supplied=True).as_turn(), []

    argv = sys.argv
    sys.argv = ["scene.py", "--book", book, "--scene", cfg_path, "--stub", "--no-keeper", "--budget",
                str(target + 1), "--db", db]
    scene.faithful_turn = fake
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            scene.main()
    except _Captured as cap:
        return cap.messages, cap.speaker, used, log.getvalue()
    finally:
        scene.faithful_turn, sys.argv = real, argv
    raise SystemExit("actor_bakeoff: %s ended before beat %d - its log:\n%s" % (sid, target, log.getvalue()[-2000:]))


def build(out, book, beats):
    """The frozen prompt set: out/items/<scene>_b<k>.json."""
    os.makedirs(os.path.join(out, "items"), exist_ok=True)
    scratch = os.path.join(out, "book")
    if not os.path.isdir(scratch):
        _copy_book(book, scratch)
    os.makedirs(os.path.join(scratch, "runs"), exist_ok=True)       # a chronicle must sit inside its own book
    for sid, name in SCENES:
        with io.open(os.path.join(scratch, "scenes", name), encoding="utf-8") as fh:
            drives = {c["id"]: c.get("drive", "") for c in json.load(fh)["cast"]}
        for k in range(beats):
            item = os.path.join(out, "items", "%s_b%d.json" % (sid, k))
            if os.path.exists(item):
                continue
            db = os.path.join(scratch, "runs", "%s_b%d.db" % (sid, k))
            messages, speaker, used, _log = _capture(scratch, sid, os.path.join(scratch, "scenes", name), k, db)
            with io.open(item, "w", encoding="utf-8") as fh:
                json.dump({"id": "%s_b%d" % (sid, k), "scene": name, "beat": k, "speaker": speaker,
                           "drive": drives.get(speaker, ""), "before": used, "messages": messages}, fh, indent=1,
                          ensure_ascii=False)
            print("item %s_b%d: %s speaks (after %s)" % (sid, k, speaker, used or "nothing"))


def _items(out):
    return [json.load(io.open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(out, "items", "*.json")))]


def _read(text):
    """A raw reply -> (the JSON object or None, its shape against the strict contract)."""
    from src.engine import replies as _replies
    from src.engine.errors import EngineError
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    try:
        d = json.loads(m.group(0)) if m else None
    except (ValueError, RecursionError):
        d = None
    if not isinstance(d, dict):
        return None, "EMPTY" if not (text or "").strip() else "NOT_JSON"
    try:
        _replies.actor_reply(d, supplied=True)
    except EngineError as exc:
        return d, exc.code
    return d, "ok"


def run_model(out, model, draws, num_ctx, think):
    """Every frozen prompt, `draws` times, from one local model -> out/replies/<model>/."""
    import direct
    if not model.startswith("ollama/"):
        raise SystemExit("actor_bakeoff: --model is ollama/<name> - the test is for local actors")
    name = model[len("ollama/"):]
    folder = os.path.join(out, "replies", re.sub(r"[^A-Za-z0-9._-]", "_", name))
    os.makedirs(folder, exist_ok=True)
    for n, item in enumerate(_items(out)):
        for d in range(draws):
            path = os.path.join(folder, "%s_d%d.json" % (item["id"], d))
            if os.path.exists(path):
                continue
            seed, t0, err, text = 1000 * d + 17 * n + 1, time.time(), "", ""
            try:
                text = direct._ollama(item["messages"], name, think=think, seed=seed, num_ctx=num_ctx)
            except Exception as exc:                              # a down daemon or a timeout is a result, recorded
                err = "%s: %s" % (type(exc).__name__, exc)
            parsed, shape = _read(text)
            row = {"model": model, "item": item["id"], "draw": d, "seed": seed, "num_ctx": num_ctx, "think": think,
                   "seconds": round(time.time() - t0, 1), "error": err, "raw": text, "shape": shape,
                   "parsed": parsed}
            with io.open(path, "w", encoding="utf-8") as fh:
                json.dump(row, fh, indent=1, ensure_ascii=False)
            print("%s %s d%d: %s (%.0fs)" % (name, item["id"], d, err or shape, row["seconds"]))


def tasks(out, config, draws):
    """For an AGENT actor (a model with no local endpoint, answered by one fresh agent per reply): one task file per
    prompt and draw - the engine's system and user messages verbatim, and the path the raw reply goes to. Prints one
    `TASK <file> REPLY <file>` line per task still unanswered."""
    tdir, rdir = os.path.join(out, "tasks", config), os.path.join(out, "agent_replies", config)
    os.makedirs(tdir, exist_ok=True)
    os.makedirs(rdir, exist_ok=True)
    for item in _items(out):
        msgs = {m["role"]: m["content"] for m in item["messages"]}
        for d in range(draws):
            t = os.path.join(tdir, "%s_d%d.json" % (item["id"], d))
            reply = os.path.join(rdir, "%s_d%d.txt" % (item["id"], d))
            if not os.path.exists(t):
                with io.open(t, "w", encoding="utf-8") as fh:
                    json.dump({"system": msgs.get("system", ""), "user": msgs.get("user", ""), "reply_path": reply},
                              fh, indent=1, ensure_ascii=False)
            if not os.path.exists(reply):
                print("TASK %s REPLY %s" % (t, reply))


def ingest(out, config, label):
    """An agent actor's raw replies -> reply rows like `run` writes (no timing: an agent's clock is not the model's)."""
    folder = os.path.join(out, "replies", config)
    os.makedirs(folder, exist_ok=True)
    n = 0
    for path in sorted(glob.glob(os.path.join(out, "agent_replies", config, "*.txt"))):
        stem = os.path.basename(path)[:-len(".txt")]
        item, draw = stem.rsplit("_d", 1)
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        parsed, shape = _read(text)
        with io.open(os.path.join(folder, stem + ".json"), "w", encoding="utf-8") as fh:
            json.dump({"model": label, "item": item, "draw": int(draw), "seed": None, "num_ctx": None, "think": None,
                       "seconds": None, "error": "", "raw": text, "shape": shape, "parsed": parsed}, fh, indent=1,
                      ensure_ascii=False)
        n += 1
        print("%s %s: %s" % (label, stem, shape))
    missing = len(glob.glob(os.path.join(out, "tasks", config, "*.json"))) - n
    print("ingested %d replies for %s; %d task(s) still unanswered" % (n, label, missing))


def _plants(item):
    """The planted replies for one prompt: {kind: reply}."""
    sid, k, who = item["id"].split("_b")[0], item["beat"], item["speaker"]
    ref = REFS[sid][k][who]
    other = NAMES["tam" if who == "nell" else "nell"]
    out = {"reference": ref,
           "agency": dict(ref, action=ref["action"] + AGENCY % other),
           "stranger": dict(ref, action=ref["action"] + STRANGER)}
    act, thought = DRIVE_BREAK[(sid, who)]
    out["drive"] = dict(ref, action=act, thought=thought)
    before = [b for b in item["before"] if b[1] != who]
    if before:                                         # tags about the other character's last beat
        prev = REFS[sid][before[-1][0]][before[-1][1]]
        out["tags"] = dict(ref, tags=dict(ref["tags"], summary=prev["tags"]["summary"]))
    return out


JUDGE_BRIEF = """# Judge brief - one actor prompt, many replies

You judge replies written by an ACTOR: a model playing ONE character for ONE beat of a scene. Below is the exact prompt
the actor was given (its system and user messages), then every reply to it, each under an opaque id. You do not know
who wrote any reply, and some replies were planted to test you. Judge every reply against THIS prompt only.

For each reply answer four questions (true/false):
- `acts_for_other`: TRUE if the reply decides, narrates or speaks for ANYONE but the actor's own character - another
  person's words, actions, choices or reactions - beyond what the character perceives of them. ("She sees him
  hesitate" is perception: false. "He agrees and follows her" is deciding for him: true.)
- `adds_new`: TRUE if the reply brings a person or creature into the scene who is not in what the character perceives,
  or an object the prompt does not establish. Ordinary texture (breath, cold, the light) is not new.
- `follows_direction`: TRUE if the ACTION carries out this beat's stage directions and the character's drive as the
  prompt gives them. FALSE if it contradicts them (quote the direction in `note`). Judge the action here; the thought
  has its own question, next.
- `tags_own_beat`: TRUE if the reply's `tags` (type, summary, subject) describe what THIS character did in this beat,
  not another character's earlier action.
- `names_pulls`: TRUE if the `thought` does what the prompt's rule for it asks: where the stage directions pull
  different ways, it names the pulls it is resolving and which one wins; where they agree, it says what the character
  is doing and no more. FALSE if it skips a weighing the directions call for (say what is missing in `note`).
Also `craft`: 1 (flat or generic), 2 (serviceable), 3 (alive - this person, this moment).

Write ONE JSON list to the file named at the end, one object per reply, every id exactly once:
[{"id": "...", "acts_for_other": false, "adds_new": false, "follows_direction": true, "tags_own_beat": true,
  "names_pulls": true, "craft": 2, "note": "<one short line; required when any answer is a violation>"}]
Nothing else in the file. Do not open any other file.
"""


def packet(out, seed, per=0):
    """Per prompt, blind packets (prompt once, replies shuffled under opaque ids, plants mixed in); the key apart.
    `per` > 0 splits a prompt's replies into packets of about that many, each with its own full set of plants: a judge
    reads fewer replies, and a judge that misses a plant costs only its own packet. Replies are dealt round-robin in
    (model, file) order, so each model's draws spread across the packets."""
    rnd = random.Random(seed)
    os.makedirs(os.path.join(out, "packets"), exist_ok=True)
    key = {}
    for item in _items(out):
        replies = []
        for path in sorted(glob.glob(os.path.join(out, "replies", "*", "%s_d*.json" % item["id"]))):
            row = json.load(io.open(path, encoding="utf-8"))
            if row["parsed"] is not None:
                replies.append((row["model"], path, row["parsed"]))
        replies.sort(key=lambda e: (e[0], e[1]))
        n = max(1, -(-len(replies) // per)) if per > 0 else 1
        for c in range(n):
            name = item["id"] if n == 1 else "%s.c%d" % (item["id"], c + 1)
            entries = replies[c::n] + [("PLANT:" + kind, "", reply) for kind, reply in _plants(item).items()]
            rnd.shuffle(entries)
            body = [JUDGE_BRIEF, "## The prompt (%s - the actor is %s)\n" % (item["id"], item["speaker"])]
            for m in item["messages"]:
                body.append("### %s\n\n%s\n" % (m["role"], m["content"]))
            body.append("## The replies\n")
            for who, path, reply in entries:
                eid = "%s-%06x" % (item["id"], rnd.getrandbits(24))
                while eid in key:
                    eid = "%s-%06x" % (item["id"], rnd.getrandbits(24))
                key[eid] = {"item": item["id"], "packet": name, "who": who, "file": path}
                body.append("### %s\n\n```json\n%s\n```\n" % (eid, json.dumps(
                    {k: reply.get(k) for k in ("action", "thought", "addressee", "tags")}, indent=1,
                    ensure_ascii=False)))
            body.append("\nWrite your verdicts to `%s`.\n" % os.path.join(out, "verdicts", name + ".<your-name>.json"))
            with io.open(os.path.join(out, "packets", name + ".md"), "w", encoding="utf-8") as fh:
                fh.write("\n".join(body))
            print("packet %s: %d replies (%d planted)" % (name, len(entries),
                                                         sum(1 for w, _p, _r in entries if w.startswith("PLANT:"))))
    os.makedirs(os.path.join(out, "verdicts"), exist_ok=True)
    with io.open(os.path.join(out, "key.json"), "w", encoding="utf-8") as fh:
        json.dump(key, fh, indent=1)


def _tier(rates):
    def meets(bar):
        return (rates["shape"] >= bar["shape"] and rates["acts_for_other"] <= bar["acts_for_other"]
                and rates["adds_new"] <= bar["adds_new"] and rates["follows_direction"] >= bar["follows_direction"]
                and rates["tags_own_beat"] >= bar["tags_own_beat"])
    return "fit" if meets(FIT) else "marginal" if meets(MARGINAL) else "unfit"


LATER = ("names_pulls",)          # asked from 2026-09-27: a verdict written before then is judged on the rest


def score(out):
    """Verdicts + key -> per-model rates over the packets whose judges caught every plant (a packet is a prompt, or a
    part of one when `packet --per` split it)."""
    key = json.load(io.open(os.path.join(out, "key.json"), encoding="utf-8"))
    unit = lambda k: k.get("packet", k["item"])                        # noqa: E731 - keys written before packets split
    verdicts = {}
    for path in glob.glob(os.path.join(out, "verdicts", "*.json")):
        for v in json.load(io.open(path, encoding="utf-8")):
            verdicts.setdefault(v["id"], []).append(v)
    reliable, report = {}, {}
    for name in sorted({unit(k) for k in key.values()}):
        misses = []
        for eid, k in key.items():
            if unit(k) != name or not k["who"].startswith("PLANT:"):
                continue
            kind = k["who"][len("PLANT:"):]
            for v in verdicts.get(eid, [{}]):
                want = PASS if kind == "reference" else {PLANT_FAILS[kind]: not PASS[PLANT_FAILS[kind]]}
                if any(v.get(q) != a for q, a in want.items() if q in v or q not in LATER):
                    misses.append(kind)
        reliable[name] = not misses and any(eid in verdicts for eid, k in key.items() if unit(k) == name)
        report[name] = "reliable" if reliable[name] else "UNRELIABLE (missed: %s)" % (", ".join(misses) or "no verdicts")
    models = {}
    for path in glob.glob(os.path.join(out, "replies", "*", "*.json")):
        row = json.load(io.open(path, encoding="utf-8"))
        m = models.setdefault(row["model"], {"replies": 0, "shape_ok": 0, "judged": 0, "craft": [], "seconds": [],
                                             **{q: [0, 0] for q in QUESTIONS}})
        m["replies"] += 1
        m["shape_ok"] += row["shape"] == "ok"
        if row.get("seconds") is not None:
            m["seconds"].append(row["seconds"])
    for eid, k in key.items():
        if k["who"].startswith("PLANT:") or not reliable.get(unit(k)):
            continue
        m = models[k["who"]]
        for v in verdicts.get(eid, []):
            m["judged"] += 1
            for q in QUESTIONS:
                if q in v or q not in LATER:
                    m[q][0] += bool(v.get(q))
                    m[q][1] += 1
            if isinstance(v.get("craft"), int):
                m["craft"].append(v["craft"])
    table = {}
    for model, m in sorted(models.items()):
        rates = {"shape": m["shape_ok"] / max(m["replies"], 1),
                 **{q: (m[q][0] / m[q][1] if m[q][1] else None) if q in LATER else m[q][0] / max(m[q][1], 1)
                    for q in QUESTIONS}}
        table[model] = dict(rates, replies=m["replies"], judged=m["judged"], tier=_tier(rates) if m["judged"] else
                            "not judged", craft=round(sum(m["craft"]) / len(m["craft"]), 2) if m["craft"] else None,
                            median_seconds=sorted(m["seconds"])[len(m["seconds"]) // 2] if m["seconds"] else None)
    with io.open(os.path.join(out, "score.json"), "w", encoding="utf-8") as fh:
        json.dump({"prompts": report, "models": table, "fit": FIT, "marginal": MARGINAL}, fh, indent=1)
    for name, state in sorted(report.items()):
        print("packet %s: %s" % (name, state))
    for model, t in table.items():
        pulls = "n/a" if t["names_pulls"] is None else "%.2f" % t["names_pulls"]
        print("%-34s %-10s replies %3d judged %3d | shape %.2f | acts-for-other %.2f | adds-new %.2f | direction %.2f "
              "| own-tags %.2f | names-pulls %s | craft %s | %ss" % (
                  model, t["tier"], t["replies"], t["judged"], t["shape"], t["acts_for_other"], t["adds_new"],
                  t["follows_direction"], t["tags_own_beat"], pulls, t["craft"], t["median_seconds"]))


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="which models can hold the actor role")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--book", default=BOOK)
    b.add_argument("--beats", type=int, default=3)
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--draws", type=int, default=5)
    r.add_argument("--num-ctx", type=int, default=32768, dest="num_ctx")
    r.add_argument("--no-think", action="store_false", dest="think")
    t = sub.add_parser("tasks", help="task files for an agent actor (one fresh agent per reply)")
    t.add_argument("--out", required=True)
    t.add_argument("--config", required=True, help="a folder name for this actor, e.g. sonnet-low")
    t.add_argument("--draws", type=int, default=5)
    g = sub.add_parser("ingest", help="an agent actor's raw replies -> reply rows")
    g.add_argument("--out", required=True)
    g.add_argument("--config", required=True)
    g.add_argument("--model", required=True, help="the label the score shows, e.g. claude:sonnet@low")
    p = sub.add_parser("packet")
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--per", type=int, default=0, help="split each prompt into packets of about this many replies")
    s = sub.add_parser("score")
    s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out)
    if a.cmd == "build":
        build(out, os.path.abspath(a.book), a.beats)
    elif a.cmd == "run":
        run_model(out, a.model, a.draws, a.num_ctx, a.think)
    elif a.cmd == "tasks":
        tasks(out, a.config, a.draws)
    elif a.cmd == "ingest":
        ingest(out, a.config, a.model)
    elif a.cmd == "packet":
        packet(out, a.seed, a.per)
    else:
        score(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
