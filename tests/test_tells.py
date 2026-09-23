"""test_tells.py — the signs a sharp eye catches, and a listener who misses them never reads (gate tells).

WHAT THIS PINS (2026-09-22). The design: "A failed check removes a detail (they didn't notice)"
(docs/scene-assembly.md:46). As built, every listener read the other actors' acts word for word, so a failed
check removed nothing. The owner asked where the tells could come from when the actors play the scenes, and said
"Yes" to this: the EVENT READER marks the parts of an act only a sharp eye would catch; a listener who does not
catch them never reads those words; one who does is told. `tells` is a NEW system, OFF by default.

  [1] `cut` removes the quoted signs and tidies the prose around them;
  [2] `for_listener`: a dull listener's copy is cut and the cut recorded, a sharp one's kept and named, a
      character's own acts never cut, and only the beats the moment shows are recorded;
  [3] the reader: its prompt is byte-identical unless asked; asked, every quote must be in the act, at most three;
  [4] through scripts/scene.py main with the system on: the sharp keeper reads the other's tell and is told it as
      a percept, the dull one never reads it, each beat records what was hidden and noticed; with it off the dull
      keeper reads it whole and the reader is never asked.

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

from src.engine import systems, tells                         # noqa: E402
from src.engine.gate import PERCEPTION_DC_SUBTLE               # noqa: E402
from src.engine.records import RecordError                     # noqa: E402
from test_systems import _book, _cfg                           # noqa: E402  (one fixture)

FAILS = []
MIRA_TELL = "Her hands will not settle on the wick."
ADA_TELL = "She glances twice at the door."
ACTS = {"mira": "Mira trims the lamp. %s \"The wind is backing,\" she says." % MIRA_TELL,
        "ada": "Ada coils the boat line. %s \"The tide is turning,\" she says." % ADA_TELL}


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


def test_cut():
    print("\n[1] cut")
    act = ACTS["mira"]
    check("the-sign-is-cut-and-the-prose-closes-up", tells.cut(act, [MIRA_TELL]) == 'Mira trims the lamp. "The wind is backing," she says.',
          tells.cut(act, [MIRA_TELL]))
    check("case-and-spacing-do-not-hide-it", tells.cut(act, ["her   hands will NOT settle on the wick."]) == tells.cut(act, [MIRA_TELL]))
    check("a-mid-sentence-sign-leaves-clean-punctuation", tells.cut("He said nothing, jaw working, and left.", ["jaw working"])
          == "He said nothing, and left.", tells.cut("He said nothing, jaw working, and left.", ["jaw working"]))
    check("no-sign-changes-nothing", tells.cut(act, []) == act)


def test_for_listener():
    print("\n[2] for_listener")
    log = [{"who": "ada", "action": ACTS["ada"], "tags": {"tells": [ADA_TELL]}},
           {"who": "mira", "action": ACTS["mira"], "tags": {"tells": [MIRA_TELL]}}]
    dull, hidden, noticed = tells.for_listener(log, "mira", False)
    check("a-dull-listener-reads-the-other-s-act-without-the-sign", ADA_TELL not in dull[0]["action"] and "coils the boat line" in dull[0]["action"])
    check("...and-the-cut-is-recorded", hidden == [{"who": "ada", "quote": ADA_TELL}] and noticed == [], (hidden, noticed))
    check("...and-her-own-act-is-never-cut", dull[1]["action"] == ACTS["mira"])
    sharp, hidden, noticed = tells.for_listener(log, "mira", True)
    check("a-sharp-listener-reads-it-whole-and-is-told", sharp[0]["action"] == ACTS["ada"] and noticed == [{"who": "ada", "quote": ADA_TELL}]
          and hidden == [], (hidden, noticed))
    old = [{"who": "ada", "action": ACTS["ada"], "tags": {"tells": [ADA_TELL]}}] + [{"who": "mira", "action": "Mira waits.", "tags": {}}] * 6
    out, hidden, _n = tells.for_listener(old, "mira", False)
    check("a-sign-older-than-the-moment-shows-is-cut-but-not-recorded", ADA_TELL not in out[0]["action"] and hidden == [], hidden)
    check("the-check-is-the-subtle-cue-line", tells.catches({"baseline": {"skills": {"perception": PERCEPTION_DC_SUBTLE}}})
          and not tells.catches({"baseline": {"skills": {"perception": PERCEPTION_DC_SUBTLE - 0.01}}}))
    check("the-system-is-off-by-default", "tells" not in systems.for_book({}) and "tells" in systems.for_book({"systems": {"tells": True}}))


def test_reader():
    print("\n[3] the reader")
    import appraiser
    kw = dict(moment="The gale has dropped.", present=["mira", "ada"], actor="Mira", attachments=None)
    plain = appraiser.build_event_messages(ACTS["mira"], **kw)
    check("not-asked-the-prompt-is-byte-identical", plain == appraiser.build_event_messages(ACTS["mira"], tells=False, **kw)
          and "TELLS" not in plain[0]["content"])
    check("asked-it-carries-the-question", tells.RUBRIC in appraiser.build_event_messages(ACTS["mira"], tells=True, **kw)[0]["content"])
    base = {"type": "mundane", "dimensions": {}, "durability": "transient"}

    def parse(t, asked=True):
        return appraiser.parse_event_reply(json.dumps(dict(base, tells=t)), objects=["ada"], action=ACTS["mira"], tells=asked)
    check("a-quoted-sign-rides-the-tags", parse([{"quote": MIRA_TELL}])["tells"] == [MIRA_TELL])
    check("none-is-an-empty-list", parse([])["tells"] == [])
    check("not-asked-a-stray-key-is-dropped", "tells" not in parse([{"quote": MIRA_TELL}], asked=False))
    for code, t in (("APPRAISER_TELLS_SHAPE", "her hands"), ("APPRAISER_TELLS_SHAPE", [{"quote": MIRA_TELL}] * 4),
                    ("APPRAISER_TELLS_SHAPE", ["her hands"]), ("APPRAISER_QUOTE_MISSING", [{"quote": " "}]),
                    ("APPRAISER_FACT_NOT_IN_ACTION", [{"quote": "she weeps openly"}])):
        check("refuses-%s-%s" % (code, json.dumps(t)[:30]), _code(lambda: parse(t)) == code, _code(lambda: parse(t)))


def _skills(book, perception):
    for name, value in perception.items():
        p = os.path.join(book, "characters", "%s.md" % name)
        txt = open(p, encoding="utf-8").read()
        m = re.search(r"```json\n(.*)\n```", txt, re.S)
        eng = json.loads(m.group(1))
        eng["baseline"].setdefault("skills", {})["perception"] = value
        open(p, "w", encoding="utf-8").write(txt[:m.start(1)] + json.dumps(eng, indent=1) + txt[m.end(1):])


def _run(tmp, decl, cfg_extra=None):
    """One scene of four beats through scripts/scene.py main IN PROCESS: each keeper's act carries a sign, the event
    seat (faked) marks it when asked. -> (db, [(speaker, moment, percept attributes)], [asked?])."""
    import scene
    book = _book(tmp, decl)
    _skills(book, {"Mira": 0.85, "Ada": 0.40})
    seen, asked = [], []

    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        me = "mira" if other == "ada" else "ada"
        attrs = [a for p in packet["volatile"]["percepts"] for a in (p.get("attributes") or [])]
        seen.append((me, event_text, attrs))
        return ({"action": ACTS[me], "thought": "", "exit": False, "addressee": other, "act": "",
                 "tags": {"type": "mundane", "summary": "tends the lamp", "dimensions": {}, "durability": "transient",
                          "subject": other}}, [])

    def event(action, model, tells=False, **_k):
        asked.append(bool(tells))
        out = {"type": "mundane", "dimensions": {}, "durability": "transient"}
        if tells:
            out["tells"] = [MIRA_TELL if MIRA_TELL in action else ADA_TELL]
        return out

    def emotion(action, thought, model, me=None, present=(), **_k):
        return [], [p for p in present if p != me], "sure", []

    saved = (scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv)
    scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion = fake_turn, event, emotion
    cfg_path = _cfg(tmp, "gale", "21:00", "1h")
    if cfg_extra:                                 # e.g. the director stating how someone arrives
        body = json.load(open(cfg_path, encoding="utf-8"))
        body.update(cfg_extra)
        json.dump(body, open(cfg_path, "w", encoding="utf-8"))
    sys.argv = ["scene.py", "--book", book, "--scene", cfg_path, "--budget", "4",
                "--model", "fake/model", "--no-keeper"]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            scene.main()
    finally:
        scene.faithful_turn, scene.appraiser.read_event, scene.appraiser.read_emotion, sys.argv = saved
    return glob.glob(os.path.join(book, "runs", "*.db"))[0], seen, asked


def test_through_the_driver(tmp):
    print("\n[4] through scripts/scene.py main")
    db, seen, asked = _run(os.path.join(tmp, "on"), {"tells": True})
    ada_moments = [m for who, m, _a in seen if who == "ada"]
    mira_moments = [m for who, m, _a in seen if who == "mira"]
    check("both-keepers-spoke", ada_moments and mira_moments and any("coils" in m for m in mira_moments), [w for w, _m, _a in seen])
    check("the-reader-was-asked-every-beat", asked and all(asked), asked)
    check("the-dull-keeper-never-reads-the-sign-the-sharp-one-let-slip",
          any("trims the lamp" in m for m in ada_moments) and not any(MIRA_TELL in m for m in ada_moments), ada_moments[-1:])
    check("the-sharp-keeper-reads-the-other-s-sign", any(ADA_TELL in m for m in mira_moments), mira_moments[-1:])
    check("...and-is-told-it-as-a-percept", any(ADA_TELL in a for who, _m, attrs in seen if who == "mira" for a in attrs),
          [attrs for who, _m, attrs in seen if who == "mira"][-1:])
    con = sqlite3.connect(db)
    mans = [(r[0], json.loads(r[1])) for r in con.execute("SELECT turn, manifest FROM decision_manifests ORDER BY turn")]
    actors = dict(con.execute("SELECT turn, actor FROM turns"))
    hidden = [t for t, m in mans if actors[t] == "ada" and (m.get("tells") or {}).get("hidden")]
    noticed = [t for t, m in mans if actors[t] == "mira" and (m.get("tells") or {}).get("noticed")]
    check("each-beat-records-what-was-hidden-and-what-was-caught", hidden and noticed, (hidden, noticed))
    logged = [json.loads(t) for (t,) in con.execute("SELECT tags FROM turns")]
    check("the-reader-s-marks-ride-the-turns-into-the-log", all(t.get("tells") for t in logged), logged[:1])
    db, seen, asked = _run(os.path.join(tmp, "off"), None)
    check("with-it-off-the-dull-keeper-reads-every-act-whole", any(MIRA_TELL in m for who, m, _a in seen if who == "ada"))
    check("...the-reader-is-never-asked", asked and not any(asked), asked)
    check("...and-no-beat-records-tells", not any("tells" in json.loads(m) for (m,) in sqlite3.connect(db).execute(
        "SELECT manifest FROM decision_manifests")))


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
        _db, seen, _asked = _run(os.path.join(tmp, word + str(len(decl))), decl,
                                 {"condition": [{"char": "mira", "energy": word}]})
        mira = [m for who, m, _a in seen if who == "mira"]
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
        by_scene = _spied_tired(_scene_driver, ["scene.py", "--book", book, "--scene", _cfg(here, "gale", "21:00", "30m"),
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
        test_cut()
        test_for_listener()
        test_reader()
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
