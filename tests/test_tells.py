"""test_tells.py — the signs a sharp eye catches, and a listener who misses them never reads (gates tells, tells-direction).

WHAT THIS PINS. The design: "A failed check removes a detail (they didn't notice)" (docs/scene-assembly.md:46).
Gate tells (2026-09-22) had the EVENT READER quote the signs in an act and cut them by regex for a listener who
does not catch them. William's ruling (via the showrunner, 2026-10-16 21:44): tells come from the SCENE BRIEF. The
author gives a character their tells (cast[].tells); the actor is told what they give away without meaning to and,
when it shows, writes it in its reply's `tell` field in its own words, never in `action`; a listener who catches it
(`tells.catches`, the lexicon's subtle-cue line) reads it after the act and is told it as a percept, one who does not
reads the act alone, and one's own rows read whole. No reader rubric, no regex cut. No cast[].tells, no tells.

  [1] the scene file and the direction: cast[].tells is a list of the author's lines, checked; a book with the
      system off refuses a scene that states one;
  [2] the prompt: only the character with tells is told, and only their reply skeleton carries "tell";
  [3] the reply: `tell` is a key of the actor's reply, kept apart from `action`;
  [4] `for_listener`: a dull listener reads the act alone and the miss is recorded, a sharp one reads act and tell
      and is told, one's own row whole, and only the beats the moment shows are recorded;
  [5] through scripts/scene.py main: the sharp keeper reads the other's tell and is told it as a percept, the dull
      one never reads it, the record keeps each tell (turns.tell) and what each beat hid and caught, and the event
      reader is never asked for tells; each keeper's FEELING reads the whole window through their own eye (gate
      tells-feel);
  [6] [7] a worn mind catches less, and the room's subtle cues dim alike (gates tired-eyes, tired-lexicon).

The book is invented here (two keepers on a rock), per hard rule 1. Script-style; exit 0 = all pass.
"""
import contextlib
import glob
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine import contracts, contracts_scene, handoff, prompt, replies, systems, tells   # noqa: E402
from src.engine.gate import PERCEPTION_DC_SUBTLE               # noqa: E402
from src.engine.records import RecordError                     # noqa: E402
from test_systems import _book, _cfg                           # noqa: E402  (one fixture)

FAILS = []
MIRA_TELL = "Her hands will not settle on the wick."
ADA_TELL = "She glances twice at the door."
ACTS = {"mira": "Mira trims the lamp. \"The wind is backing,\" she says.",
        "ada": "Ada coils the boat line. \"The tide is turning,\" she says."}
BRIEF = {"mira": ["her hands fuss at whatever is nearest when she is afraid"],
         "ada": ["she watches the door when she means to leave"]}
TELLS = {"mira": MIRA_TELL, "ada": ADA_TELL}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _code(fn):
    try:
        fn()
    except RecordError as e:
        return e.code
    return None


def _scene(tells_of=None):
    return {"name": "gale", "at": {"day": 1, "time": "21:00"}, "situation": "The keepers wait out the gale.",
            "cast": [dict({"id": i, "drive": "keep the lamp lit"}, **({"tells": tells_of[i]} if i in (tells_of or {})
                                                                      else {})) for i in ("mira", "ada")]}


def _refused(cfg, on=("tells",)):
    """-> the refusing findings' codes, each with its message (a check's own code rides in the message)."""
    return " | ".join("%s %s" % (f["code"], f["message"]) for f in contracts.check(cfg, contracts_scene.SCENE, on)
                      if contracts.refuses(f))


def test_contract():
    print("\n[1] the scene file and the direction")
    check("a-cast-member-s-tells-are-declared-and-pass", _refused(_scene(BRIEF)) == "", _refused(_scene(BRIEF)))
    for name, bad in (("a-string-not-a-list", "her hands"), ("an-empty-list", []), ("a-blank-line", ["  "]),
                      ("a-line-that-is-not-text", [3])):
        got = _refused(_scene({"mira": bad}))
        check("refused-SCENE_TELLS_INVALID:%s" % name, "SCENE_TELLS_INVALID" in got, got)
    got = _refused(_scene(BRIEF), on=())
    check("a-book-with-the-system-off-refuses-a-scene-that-states-tells", "SCENE_TELLS_INVALID" in got
          and "system off" in got, got)
    ok = _code(lambda: handoff.parse_direction({"book": "x", "kind": "scene", "intent": "x",
                                                "cast": [{"id": "mira", "tells": BRIEF["mira"]}, "ada"]}))
    bad = _code(lambda: handoff.parse_direction({"book": "x", "kind": "scene", "intent": "x",
                                                 "cast": [{"id": "mira", "tells": "her hands"}, "ada"]}))
    check("a-direction-may-carry-a-character-s-tells-and-a-bad-one-is-refused", ok is None
          and bad == "HANDOFF_CAST_INVALID", (ok, bad))
    lost = _code(lambda: handoff.dropped({"book": "x", "kind": "scene", "intent": "x",
                                          "cast": [{"id": "mira", "tells": BRIEF["mira"]}]}, _scene()))
    check("...and-a-scene-file-that-drops-them-is-refused", lost == "HANDOFF_DIRECTION_DROPPED", lost)


def test_prompt():
    print("\n[2] the prompt")
    from test_prompt_sections import _packet
    told = prompt.build_turn_messages(_packet(), "The gale has dropped.", {}, stance="speaker",
                                      tell=BRIEF["mira"])[1]["content"]
    plain = prompt.build_turn_messages(_packet(), "The gale has dropped.", {}, stance="speaker")[1]["content"]
    check("the-character-with-tells-is-told-what-they-give-away",
          "You give this away without meaning to: %s." % BRIEF["mira"][0] in told
          and "write it in the 'tell' field, in your own words, not in 'action'" in told, told[-900:])
    check("...and-their-reply-skeleton-carries-tell", '"tell": ""' in told)
    check("one-without-is-told-nothing-and-their-skeleton-has-no-tell",
          "give this away" not in plain and '"tell"' not in plain)
    check("a-blank-tell-is-refused-by-name", _code(lambda: prompt.build_turn_messages(
        _packet(), "x", {}, stance="speaker", tell=[" "])) == "PROMPT_TELL_MALFORMED")


def test_reply():
    print("\n[3] the reply")
    r = replies.actor_reply({"action": ACTS["mira"], "thought": "-", "tell": MIRA_TELL,
                                  "tags": {"type": "mundane", "summary": "x", "dimensions": {}, "durability": "transient"}})
    check("tell-is-a-key-the-actor-s-reply-carries", "tell" in replies.ACTOR_KEYS and "tell" not in r.extra, r.extra)
    check("...kept-apart-from-the-action", r.tell == MIRA_TELL and MIRA_TELL not in r.action, (r.tell, r.action))


def test_for_listener():
    print("\n[4] for_listener")
    log = [{"who": "ada", "action": ACTS["ada"], "tell": ADA_TELL},
           {"who": "mira", "action": ACTS["mira"], "tell": MIRA_TELL}]
    dull, hidden, noticed = tells.for_listener(log, "mira", False)
    check("a-dull-listener-reads-the-other-s-act-alone", dull[0]["action"] == ACTS["ada"], dull[0]["action"])
    check("...and-the-miss-is-recorded", hidden == [{"who": "ada", "tell": ADA_TELL}] and noticed == [], (hidden, noticed))
    check("...and-her-own-row-reads-whole", dull[1]["action"] == "%s %s" % (ACTS["mira"], MIRA_TELL), dull[1]["action"])
    sharp, hidden, noticed = tells.for_listener(log, "mira", True)
    check("a-sharp-listener-reads-act-and-tell-and-is-told", sharp[0]["action"] == "%s %s" % (ACTS["ada"], ADA_TELL)
          and noticed == [{"who": "ada", "tell": ADA_TELL}] and hidden == [], (sharp[0]["action"], hidden, noticed))
    old = [{"who": "ada", "action": ACTS["ada"], "tell": ADA_TELL}] + [{"who": "mira", "action": "Mira waits."}] * (
        prompt.MOMENT_BEATS + 2)
    out, hidden, _n = tells.for_listener(old, "mira", False)
    check("a-tell-older-than-the-moment-shows-is-unread-but-not-recorded", ADA_TELL not in out[0]["action"]
          and hidden == [], hidden)
    check("a-row-with-no-tell-is-untouched", tells.for_listener([{"who": "ada", "action": "x"}], "mira", True)[0]
          == [{"who": "ada", "action": "x"}])
    check("the-check-is-the-subtle-cue-line", tells.catches({"baseline": {"skills": {"perception": PERCEPTION_DC_SUBTLE}}})
          and not tells.catches({"baseline": {"skills": {"perception": PERCEPTION_DC_SUBTLE - 0.01}}}))
    check("the-system-is-off-by-default", "tells" not in systems.for_book({}) and "tells" in systems.for_book(
        {"systems": {"tells": True}}))


def _skills(book, perception):
    for name, value in perception.items():
        p = os.path.join(book, "characters", "%s.md" % name)
        txt = open(p, encoding="utf-8").read()
        m = re.search(r"```json\n(.*)\n```", txt, re.S)
        eng = json.loads(m.group(1))
        eng["baseline"].setdefault("skills", {})["perception"] = value
        open(p, "w", encoding="utf-8").write(txt[:m.start(1)] + json.dumps(eng, indent=1) + txt[m.end(1):])


def _run(tmp, decl, cfg_extra=None, brief=BRIEF, shared=False):
    """One scene of four beats through scripts/scene.py main IN PROCESS: each keeper writes a tell when the scene
    brief gave them one. -> (db or None, [(speaker, moment, percept attributes, the tells they were told)],
    [the reader's tells= per call], the run's exit text or None). `shared`: the speaker keeps the floor and the
    listener puts in a word, so both keepers' rows fall in one window; the emotion seat's (participant, moment)
    per read is left on `_run.feels`."""
    import scene
    book = _book(tmp, decl)
    _skills(book, {"Mira": 0.85, "Ada": 0.40})
    seen, asked, feels = [], [], []

    def fake_turn(packet, event_text, temperament, model, stub, **k):
        me = k["char_id"]
        other = "ada" if me == "mira" else "mira"
        attrs = [a for p in packet["volatile"]["percepts"] for a in (p.get("attributes") or [])]
        told = (k.get("floor") or {}).get("tell")
        seen.append((me, event_text, attrs, told))
        reply = {"action": ACTS[me], "thought": "", "exit": False, "addressee": other, "act": "",
                 "tags": {"type": "mundane", "summary": "tends the lamp", "dimensions": {}, "durability": "transient",
                          "subject": other}}
        if told:
            reply["tell"] = TELLS[me]
        if shared:
            reply["floor"] = "keep" if (k.get("floor") or {}).get("stance") == "speaker" else "interject"
        return reply, []

    def event(action, model, **kw):
        asked.append(kw.get("tells"))
        return {"type": "mundane", "dimensions": {}, "durability": "transient"}

    def emotion(action, thought, model, me=None, present=(), moment="", **_k):
        feels.append((me, moment))
        return [], [p for p in present if p != me], "sure", []

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, event, emotion
    cfg_path = _cfg(tmp, "gale", "21:00", "1h")
    body = json.load(open(cfg_path, encoding="utf-8"))
    for c in body["cast"]:
        if c["id"] in (brief or {}):
            c["tells"] = brief[c["id"]]
    body.update(cfg_extra or {})                  # e.g. the director stating how someone arrives
    json.dump(body, open(cfg_path, "w", encoding="utf-8"))
    sys.argv = ["scene.py", "--no-direction", "--book", book, "--scene", cfg_path, "--budget", "4",
                "--model", "fake/model", "--no-keeper"]
    exited = None
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            scene.main()
    except SystemExit as e:
        exited = str(e)
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv = saved
    dbs = glob.glob(os.path.join(book, "runs", "*.db"))
    _run.feels = feels
    return (dbs[0] if dbs else None), seen, asked, exited


def test_through_the_driver(tmp):
    print("\n[5] through scripts/scene.py main")
    db, seen, asked, exited = _run(os.path.join(tmp, "on"), {"tells": True})
    ada_moments = [m for who, m, _a, _t in seen if who == "ada"]
    mira_moments = [m for who, m, _a, _t in seen if who == "mira"]
    check("both-keepers-spoke", exited is None and ada_moments and mira_moments
          and any("coils" in m for m in mira_moments), (exited, [w for w, _m, _a, _t in seen]))
    check("each-keeper-is-told-their-own-tells-from-the-brief",
          seen and all(t == BRIEF[who] for who, _m, _a, t in seen), [(w, t) for w, _m, _a, t in seen])
    check("the-reader-is-never-asked-for-tells", asked and not any(asked), asked)
    check("the-dull-keeper-never-reads-the-sign-the-sharp-one-let-slip",
          any("trims the lamp" in m for m in ada_moments) and not any(MIRA_TELL in m for m in ada_moments),
          ada_moments[-1:])
    check("the-sharp-keeper-reads-the-other-s-sign", any(ADA_TELL in m for m in mira_moments), mira_moments[-1:])
    check("...and-is-told-it-as-a-percept", any(ADA_TELL in a for who, _m, attrs, _t in seen if who == "mira"
                                                 for a in attrs),
          [attrs for who, _m, attrs, _t in seen if who == "mira"][-1:])
    con = sqlite3.connect(db) if db else None
    rows = list(con.execute("SELECT actor, action, tell FROM turns ORDER BY turn")) if con else []
    check("the-record-keeps-each-tell-apart-from-the-action", rows and all(t == TELLS[a] and t not in x
                                                                           for a, x, t in rows), rows)
    mans = [(r[0], json.loads(r[1])) for r in con.execute("SELECT turn, manifest FROM decision_manifests")] if con else []
    actors = dict(con.execute("SELECT turn, actor FROM turns")) if con else {}
    hidden = [t for t, m in mans if actors[t] == "ada" and (m.get("tells") or {}).get("hidden")]
    noticed = [t for t, m in mans if actors[t] == "mira" and (m.get("tells") or {}).get("noticed")]
    check("each-beat-records-what-was-hidden-and-what-was-caught", hidden and noticed, (hidden, noticed))
    # THE NARRATOR GETS THE TELLS THE POV CAUGHT (gate tells-narrated): the record says who caught each row's tell
    # (a later manifest's tells.noticed names it); a POV's narration shows another's tell only where the POV caught
    # it, the POV's own only behind narration_contract.OWN_TELL_SHOWN (William's call, off by default), and
    # omniscient narration shows every tell
    import critic
    import narrate
    import narration_contract
    from src.engine.ledger import Ledger
    led = Ledger(db)
    turns = critic.scene_turns(led, con.execute("SELECT run_id FROM turns LIMIT 1").fetchone()[0])
    caught = {t["turn"]: (t["actor"], t["caught"]) for t in turns}
    check("the-record-says-the-sharp-keeper-caught-ada-s-tell-and-nobody-caught-mira-s",
          any(a == "ada" and c == ["mira"] for a, c in caught.values())
          and all(c == [] for a, c in caught.values() if a == "mira"), caught)
    names = {"mira": "Mira", "ada": "Ada"}

    def told(pov, knowledge="pov"):
        return "\n".join(m["content"] for m in narrate.build_narration_prompt(
            turns, pov, {}, pov_name=names[pov], names=names, knowledge=knowledge))
    # William's ruling 2026-10-17 (gate own-tell-shown): the POV's own sign is SHOWN, as a body fact it does not name
    own_line = "gave away without knowing it"
    check("mira-s-telling-carries-ada-s-caught-sign-and-her-own-as-a-body-fact",
          ADA_TELL in told("mira") and MIRA_TELL in told("mira") and own_line in told("mira"), told("mira")[-900:])
    check("ada-s-telling-carries-her-own-sign-and-none-she-missed", ADA_TELL in told("ada")
          and MIRA_TELL not in told("ada"), told("ada")[-900:])
    check("omniscient-carries-every-sign", ADA_TELL in told("ada", "omniscient") and MIRA_TELL in told("ada", "omniscient"))
    saved_own = narration_contract.OWN_TELL_SHOWN
    narration_contract.OWN_TELL_SHOWN = False
    try:
        check("the-one-switch-off-hides-the-pov-its-own-sign", MIRA_TELL not in told("mira") and ADA_TELL in told("mira")
              and own_line not in told("mira"))
    finally:
        narration_contract.OWN_TELL_SHOWN = saved_own
    led.con.close()
    # THE FEELING READS THE WHOLE WINDOW AS ITS OWNER DID (gate tells-feel): both keepers in one window (Mira keeps
    # the floor, Ada puts in a word after each move), and each one's emotion read is given the window through to its
    # close, through their own eye - Ada's last word, after Mira's last row, reaches Mira's feeling with the sign
    # Mira catches; the dull keeper's never carries the sharp one's sign; each reads their own lines as "You"
    db, seen, asked, exited = _run(os.path.join(tmp, "shared"), {"tells": True}, shared=True)
    felt = {w: [m for x, m in _run.feels if x == w] for w in ("mira", "ada")}
    closes = [t for (t,) in sqlite3.connect(db).execute(
        "SELECT json_extract(manifest, '$.window.close') FROM decision_manifests")] if db else []
    ada_rows = [t for (t,) in sqlite3.connect(db).execute("SELECT turn FROM turns WHERE actor='ada'")] if db else []
    check("one-window-holds-both-keepers-and-ada-closes-it", exited is None and len(set(closes)) == 1
          and closes[0] == max(ada_rows or [-1]) and all(len(v) == 1 for v in felt.values()), (exited, closes, ada_rows))
    check("the-sharp-keeper-s-feeling-reads-every-word-the-other-put-in-with-its-sign",
          [m.count(ADA_TELL) for m in felt["mira"]] == [len(ada_rows)], felt["mira"])
    # WHAT THE FEELING CAUGHT, THE TELLING SHOWS (gate tells-caught-at-close): the window's close records each
    # participant's catches, so Ada's last word - after Mira's last call - is caught by Mira in the record and in
    # Mira's telling, and Ada catches nothing
    import critic
    import narrate
    from src.engine.ledger import Ledger
    led = Ledger(db)
    turns = critic.scene_turns(led, sqlite3.connect(db).execute("SELECT run_id FROM turns LIMIT 1").fetchone()[0])
    last_ada = max(t["turn"] for t in turns if t["actor"] == "ada")
    check("the-close-records-mira-caught-ada-s-last-sign", [t["caught"] for t in turns if t["turn"] == last_ada]
          == [["mira"]] and all(t["caught"] == [] for t in turns if t["actor"] == "mira"),
          [(t["turn"], t["actor"], t["caught"]) for t in turns])
    mira_told = narrate.build_narration_prompt(turns, "mira", {}, pov_name="Mira", names={"mira": "Mira", "ada": "Ada"})
    check("...and-mira-s-telling-shows-every-sign-ada-let-slip", mira_told[1]["content"].count(ADA_TELL) == len(ada_rows),
          mira_told[1]["content"][-700:])
    led.con.close()
    check("the-dull-keeper-s-feeling-never-reads-the-sharp-one-s-sign",
          any("trims the lamp" in m for m in felt["ada"]) and not any(MIRA_TELL in m for m in felt["ada"]),
          felt["ada"])
    check("each-keeper-s-feeling-reads-their-own-lines-as-you",
          not any(line.startswith(nm) for w, nm in (("mira", "Mira"), ("ada", "Ada")) for m in felt[w]
                  for line in m.splitlines()), _run.feels)
    db, seen, asked, exited = _run(os.path.join(tmp, "none"), {"tells": True}, brief=None)
    check("no-tells-in-the-brief-no-tells", exited is None and seen and all(t is None for _w, _m, _a, t in seen)
          and not any(t for (t,) in sqlite3.connect(db).execute("SELECT tell FROM turns")),
          (exited, [t for _w, _m, _a, t in seen]))
    db, seen, asked, exited = _run(os.path.join(tmp, "off"), None)
    check("a-book-with-the-system-off-refuses-a-scene-with-tells-before-a-turn", "SCENE_TELLS_INVALID" in str(exited)
          and not seen, exited)


def test_tired_eyes(tmp):
    print("\n[5] a worn mind catches less (gate tired-eyes; the book runs tells AND condition_flow)")

    def ch(p, energy, load=0.2):
        return {"baseline": {"skills": {"perception": p}}, "current": {"condition": {"energy": energy, "allostatic_load": load}}}
    check("a-sharp-eye-arriving-fresh-still-catches", tells.catches(ch(0.85, 0.95), tired=True))
    check("...arriving-spent-it-misses", not tells.catches(ch(0.85, 0.15), tired=True))
    check("...and-without-the-energy-system-the-condition-is-not-read", tells.catches(ch(0.85, 0.15), tired=False))
    check("a-mind-with-nothing-left-keeps-half-its-eye", tells.catches(ch(1.2, 0.0, 0.0), tired=True)
          and not tells.catches(ch(1.19, 0.0, 0.0), tired=True))
    check("a-heavy-load-dulls-the-eye-as-it-dulls-memory", tells.catches(ch(0.79, 1.0, 0.0), tired=True)
          and not tells.catches(ch(0.79, 1.0, 1.0), tired=True))
    both = {"tells": True, "condition_flow": True}
    for decl, word, sees in ((both, "spent", False), (both, "fresh", True), ({"tells": True}, "spent", True)):
        _db, seen, _asked, _x = _run(os.path.join(tmp, word + str(len(decl))), decl,
                                     {"condition": [{"char": "mira", "energy": word}]})
        mira = [m for who, m, _a, _t in seen if who == "mira"]
        check("the-sharp-keeper-arriving-%s-%s-the-other-s-sign%s" % (
                  word, "reads" if sees else "never-reads", "" if "condition_flow" in decl else "-without-the-energy-system"),
              mira and any(ADA_TELL in m for m in mira) == sees, mira[-1:])


def _spied_tired(mod, argv):
    """Run a driver's main() in process with `assemble` spied -> [the `tired` it was handed, per call]."""
    got, real = [], mod.assemble

    def spy(*a, **k):
        got.append(k.get("tired"))
        return real(*a, **k)

    saved = sys.argv
    mod.assemble, sys.argv = spy, argv
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                mod.main()
            except SystemExit:
                pass
    finally:
        mod.assemble, sys.argv = real, saved
    return got


def test_the_rooms_cues_dim_alike(tmp):
    print("\n[6] the room's subtle cues dim with the mind, as a speaker's tells do (gate tired-lexicon)")
    from src.engine import gate
    world = {"lexicon": {"attribute_classes": {"distress": ["trembling"]}, "subtle_cue_classes": ["distress"],
                         "subtle_cues": {"shaking-hands": ["trembling"]}}}
    slice_ = {"event": {"text": "Her hands are trembling on the rail.", "kind": "mundane"}}

    def sees(cond, tired, p=0.7):
        return any(str(x.get("ref", "")).startswith("evt.subtle.")
                   for x in gate.perception_scope(slice_, world, {"perception": p}, cond, tired=tired))
    fresh, spent = {"energy": 0.95, "allostatic_load": 0.0}, {"energy": 0.1, "allostatic_load": 0.0}
    check("a-sharp-eye-arriving-fresh-catches-the-room-s-cue", sees(fresh, True))
    check("...arriving-spent-it-misses-it", not sees(spent, True))
    check("...and-without-the-energy-system-the-condition-is-not-read", sees(spent, False))
    agree = all(sees({"energy": e, "allostatic_load": ld}, True, p) == tells.catches(
                    {"baseline": {"skills": {"perception": p}}, "current": {"condition": {"energy": e, "allostatic_load": ld}}},
                    tired=True)
                for p in (0.55, 0.6, 0.7, 0.85, 1.0, 1.2) for e in (0.0, 0.3, 0.6, 1.0) for ld in (0.0, 0.5, 1.0))
    check("one-rule-the-room-s-cue-and-a-speaker-s-tell-agree-for-every-eye-and-mind", agree)
    # THROUGH THE ASSEMBLER: the flag must reach the wall, not stop at assemble's signature
    from src.engine import scene as _assembler, vault
    mira = vault.load_book(_book(os.path.join(tmp, "asm"), None))[1]["mira"]
    mira["baseline"].setdefault("skills", {})["perception"] = 0.7

    def assembled(tired):
        pk = _assembler.assemble(mira, dict(world, people=[]), dict(slice_, recent=[], location=None),
                                 dict(mira["current"]["affect"]), spent, tired=tired)
        return any(str(x.get("ref", "")).startswith("evt.subtle.") for x in pk["volatile"]["percepts"])
    check("assemble-hands-the-flag-to-the-wall", assembled(False) and not assembled(True), (assembled(False), assembled(True)))
    import scene as _scene_driver
    import direct as _chair
    for decl, want in (({"condition_flow": True}, True), (None, False)):
        here = os.path.join(tmp, "flow" if want else "legacy")
        book = _book(here, decl)
        by_scene = _spied_tired(_scene_driver, ["scene.py", "--no-direction", "--book", book, "--scene", _cfg(here, "gale", "21:00", "30m"),
                                                "--budget", "1", "--stub", "--no-keeper"])
        by_chair = _spied_tired(_chair, ["direct.py", "--book", book, "--char", "Mira", "--stub", "--no-keeper",
                                         "--circumstance", "the lamp gutters", "--prompt-only"])
        check("the-scene-driver-hands-assemble-tired=%s-%s" % (want, "with-the-energy-system" if want else "without-it"),
              bool(by_scene) and all(t is want for t in by_scene), by_scene)
        check("...and-so-does-the-chair", bool(by_chair) and all(t is want for t in by_chair), by_chair)


def main():
    print("test_tells.py — the signs a sharp eye catches\n")
    tmp = tempfile.mkdtemp(prefix="swe_tells_")
    try:
        test_contract()
        test_prompt()
        test_reply()
        test_for_listener()
        test_through_the_driver(tmp)
        test_tired_eyes(os.path.join(tmp, "tired"))
        test_the_rooms_cues_dim_alike(os.path.join(tmp, "lexicon"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("test_tells: OK" if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
