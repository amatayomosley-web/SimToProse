#!/usr/bin/env python3
"""test_narrate.py — the POV-bound narrator (design.md layer 7, narration.md).

Proves gate swe-narrator-pov: the POV wall (pov_split keeps the POV's thought, drops others'), the
prompt boundary (POV's thought present, a non-POV thought ABSENT), the stub path, and the strong-
model dispatch parse. critic._openrouter is reused by narrate; monkeypatched here so no API runs.
Script-style, stdlib only, exit 0 = all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import copy                                                  # noqa: E402
import io                                                    # noqa: E402
import json                                                  # noqa: E402
import tempfile                                              # noqa: E402

import narrate                                                # noqa: E402
import scene                                                  # noqa: E402
from src.engine.ledger import Ledger                          # noqa: E402

WORLD = {"world": "Ashford — a small upland village"}
TURNS = [
    {"turn": 0, "actor": "maren", "action": "She set the cup down and said the fever would break by dawn.",
     "thought": "It will not break by dawn. I am lying to keep them calm."},
    {"turn": 1, "actor": "edda", "action": "Edda nodded and thanked her, easier now.",
     "thought": "SECRET-EDDA-DOUBT: I do not believe her, but I will not say so."},
]
FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def main():
    print("test_narrate.py — POV-bound narrator\n")

    # 1. the POV wall: POV keeps thought; the other actor loses it
    split = narrate.pov_split(TURNS, "maren")
    maren = next(e for e in split if e["actor"] == "maren")
    edda = next(e for e in split if e["actor"] == "edda")
    check("pov-keeps-thought", "thought" in maren and "lying" in maren["thought"])
    check("nonpov-drops-thought", "thought" not in edda, str(edda))

    # 2. the prompt boundary: POV's interiority is in, the non-POV SECRET is OUT
    blob = " ".join(m["content"] for m in narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren"))
    check("prompt-names-pov", "Maren" in blob)
    check("prompt-has-pov-thought", "lying to keep them calm" in blob)
    check("prompt-hides-nonpov-secret", "SECRET-EDDA-DOUBT" not in blob, "non-POV thought leaked into the prompt")
    check("prompt-has-nonpov-action", "thanked her" in blob)  # observable action still rendered
    msgs = narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren")
    check("prompt-json-serializable", len(json.loads(json.dumps(msgs))) == 2)  # --prompt-only must round-trip for Claude-in-the-loop

    # 3. stub path: POV's actions strung deterministically (no API)
    s = narrate.narrate(TURNS, "maren", WORLD, stub=True)
    check("stub-pov-actions", "fever would break by dawn" in s and "thanked her" not in s,
          "stub should render only the POV's actions")
    check("stub-empty-scene", narrate.narrate([], "maren", WORLD, stub=True) == "")

    # 4. strong-model dispatch returns the rendered prose (monkeypatched)
    _real = narrate._openrouter
    try:
        narrate._openrouter = lambda messages, model, max_tokens=2000: "The cup met the table without a sound."
        out = narrate.narrate(TURNS, "maren", WORLD, stub=False)
        check("dispatch-returns-prose", out == "The cup met the table without a sound.", out)
    finally:
        narrate._openrouter = _real

    # 5. book-scale: narrate a whole multi-scene chronicle, POV per recorded scene
    _book_narration()

    # 6. the scene's setting and what the POV knows (gate narrator-context)
    _context()

    # 7. the source contract: wording free, substance fixed, the thought record is evidence (gate narrator-source-contract)
    _source_contract()
    _floor_labels()

    if FAILS:
        print("\ntest_narrate: FAIL")
        for f in FAILS:
            print("  - " + f)
        return 1
    print("\ntest_narrate: OK (POV wall holds; the non-POV secret never reaches the prose; book narrates per-scene POV)")
    return 0


def _book_chars():
    base = json.load(open(os.path.join(REPO, "characters/maren-healer.json"), encoding="utf-8"))
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    chars = {}
    for cid, name in (("maren", "Maren"), ("edda", "Edda")):
        ch = copy.deepcopy(base)
        ch["fixed"]["id"] = cid
        ch["fixed"]["name"] = name
        chars[cid] = ch
    return world, chars


def _book_narration():
    print("\n[book] narrate_book — whole chronicle, POV per scene")
    world, chars = _book_chars()
    led = Ledger(os.path.join(tempfile.mkdtemp(prefix="narrate_book_"), "chronicle.db"))
    led.create_run("bk", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    for cid in ("maren", "edda"):
        led.register_character("bk", cid, chars[cid]["fixed"], chars[cid]["baseline"])
    cfg = {"name": "fireside", "at": {"day": 1, "time": "09:00"}, "situation": "Two healers by the fire.", "subject": (None, None),
           "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
           "cast": [{"id": "maren", "drive": "rest"}, {"id": "edda", "drive": "talk"}]}
    nt0 = scene.run_scene(world, chars, cfg, led, "bk", 0, "stub", True, 2, think=False)
    led.append_scene("bk", 0, "fireside", "maren", 0, nt0 - 1)           # scene 0 POV = maren (the actor)
    cfg2 = dict(cfg, name="the-ward", situation="Later, in the sickroom.")
    w2, c2 = _book_chars()
    # budget 1: a two-hander asks the other after every move since gate round-loop, so it no longer lulls before
    # edda acts - one row keeps her out of her own POV scene, which is what this fixture is for
    nt1 = scene.run_scene(w2, c2, cfg2, led, "bk", nt0, "stub", True, 1, think=False)
    # scene 1 POV = edda (who did NOT act -> proves POV is per-scene), and it is recorded in a
    # DIFFERENT voice from scene 0 so the mixed-voice book has something to prove.
    led.append_scene("bk", 1, "the-ward", "edda", nt0, nt1 - 1, voice="first", knowledge="omniscient")
    # ---- the two axes (schema v13; William unlocked omniscient 2026-09-01) ------------------
    # VOICE is a rendering instruction over the SAME transcript; KNOWLEDGE decides what the
    # narrator is shown. They were conflated by one hardcoded string, so each gets its own check.

    for v in sorted(narrate.VOICES):
        blob = json.dumps(narrate.build_narration_prompt(TURNS, "maren", WORLD, voice=v))
        # compare in the SAME encoding: json.dumps escapes the em-dash to —, so a raw
        # substring test fails on distant-third alone and would read as a wiring bug.
        check("voice-%s-reaches-the-prompt" % v, json.dumps(narrate.VOICES[v])[1:-1] in blob, blob[:160])

    # the wall is unchanged by voice: a first-person render still cannot see the non-POV thought
    first = json.dumps(narrate.build_narration_prompt(TURNS, "maren", WORLD, voice="first"))
    check("voice-does-NOT-move-the-wall", "SECRET-EDDA-DOUBT" not in first,
          "a voice change leaked a non-POV thought — voice and knowledge are not orthogonal")

    # KNOWLEDGE does move it, and only when asked
    omni = narrate.pov_split(TURNS, "maren", "omniscient")
    check("omniscient-keeps-EVERY-thought", all("thought" in e for e in omni), str(omni))
    check("pov-is-still-the-default",
          "thought" not in next(e for e in narrate.pov_split(TURNS, "maren") if e["actor"] == "edda"))
    oblob = json.dumps(narrate.build_narration_prompt(TURNS, "maren", WORLD, knowledge="omniscient"))
    check("omniscient-prompt-carries-the-nonpov-thought", "SECRET-EDDA-DOUBT" in oblob)
    check("omniscient-prompt-DROPS-the-head-hop-ban", "do NOT" not in oblob or "head-hop" not in oblob,
          "the POV wall instruction survived into an omniscient render")
    check("omniscient-prompt-FORBIDS-inventing-interiority", "invent interiority" in oblob,
          "omniscience over the record must not read as omniscience over the world")

    # an unknown value on either axis must fail loud, not render something plausible
    for bad, call in (("voice", lambda: narrate.build_narration_prompt(TURNS, "maren", WORLD, voice="epic")),
                      ("knowledge", lambda: narrate.pov_split(TURNS, "maren", "everything"))):
        try:
            call()
            check("bad-%s-raises" % bad, False, "accepted an unknown %s" % bad)
        except ValueError:
            check("bad-%s-raises" % bad, True)

    # THE PROSE-LAYER FAITHFULNESS GUARD. Omniscient removes the wall that made this unnecessary:
    # the narrator may now enter any mind, so what stops it entering a mind the run never recorded
    # is the TRANSCRIPT. Every interiority offered must trace to a `thought` on a real turn — the
    # prose-layer twin of faithfulness.check_name_leaks. Bounded, checkable, still faithful.
    recorded = {(t["actor"], t["thought"]) for t in TURNS}
    for know in narrate.KNOWLEDGE:
        offered = {(e["actor"], e["thought"]) for e in narrate.pov_split(TURNS, "maren", know)
                   if "thought" in e}
        check("%s-invents-no-interiority" % know, offered <= recorded,
              "offered an interiority no turn recorded: %s" % (offered - recorded))

    # THE ASSERTION WITH TEETH. The subset check above is true by construction — pov_split's output
    # is built from its input and cannot fabricate a string. What CAN go wrong is the transcript
    # template: an actor whose thought was withheld must be rendered observable-only, and if that
    # line ever gains a "privately thinks" clause the wall is gone while the subset check stays
    # green. So the rendered PROMPT is checked, per actor, against who actually has interiority.
    for know in narrate.KNOWLEDGE:
        blob = narrate.build_narration_prompt(TURNS, "maren", WORLD, knowledge=know)[1]["content"]
        # the label is `beat N · THOUGHT (<name>, private; ...)` since gate narrator-source-contract
        thinkers = {ln.split(" · THOUGHT (")[1].split(",")[0]
                    for ln in blob.splitlines() if " · THOUGHT (" in ln}
        expected = ({t["actor"] for t in TURNS} if know == "omniscient" else {"maren"})
        check("%s-transcript-gives-interiority-to-EXACTLY-the-right-actors" % know,
              thinkers == expected, "rendered %s, expected %s" % (sorted(thinkers), sorted(expected)))
    check("omniscient-is-the-UNION-of-what-was-recorded",
          {(e["actor"], e["thought"]) for e in narrate.pov_split(TURNS, "maren", "omniscient")
           if "thought" in e} == recorded)

    # per-scene voice is READ, not merely stored — a column with no reader is the defect class
    # this repo keeps re-finding (learnings/2026-07-29).

    book = narrate.narrate_book(led, "bk", world, chars, stub=True)
    check("book-has-scene0-header", "## fireside" in book, book[:120])
    check("book-has-scene1-header", "## the-ward" in book, book[:200])
    check("scene0-renders-maren-pov", "two healers by the fire" in book.lower())
    # scene 1's recorded actor is maren, but its POV is edda -> edda has no actions in range -> quiet
    check("scene1-uses-edda-pov", "the scene passes quietly" in book.lower(),
          "scene1 should be quiet (POV edda did not act) — proves per-scene POV: %s" % book[-160:])

    # the per-scene columns SURVIVE the round trip and REACH the render. A column written and never
    # read is the defect this session spent the day removing; it is not being reintroduced here.
    rows = {r["scene_no"]: r for r in led.scenes_for("bk")}
    check("scene0-defaults-to-close-third-pov",
          (rows[0]["voice"], rows[0]["knowledge"]) == ("close-third", "pov"), str(rows[0]))
    check("scene1-kept-its-own-voice-and-knowledge",
          (rows[1]["voice"], rows[1]["knowledge"]) == ("first", "omniscient"), str(rows[1]))

    seg1 = [t for t in narrate.scene_turns(led, "bk")
            if rows[1]["start_turn"] <= t["turn"] <= rows[1]["end_turn"]]
    per_scene = json.dumps(narrate.build_narration_prompt(
        seg1, "edda", world, "edda", False, None, rows[1]["voice"], rows[1]["knowledge"]))
    check("a-scene-renders-in-ITS-OWN-voice",
          json.dumps(narrate.VOICES["first"])[1:-1] in per_scene, per_scene[:160])
    check("and-in-ITS-OWN-knowledge", "invent interiority" in per_scene, per_scene[:200])


    # THE WRITER. Until 2026-09-01 the only production caller of append_scene passed no voice and
    # no knowledge, and load_scene_cfg had no such fields — so the columns were reachable from
    # tests and the raw API and by no director alive. A column with no writer is the same defect
    # as a column with no reader, which this session spent the day removing.
    import scene as scene_driver
    import json as _json
    import tempfile as _tf
    _cfg = {"name": "the-ward", "at": {"day": 1, "time": "09:00"}, "situation": "s",
            "cast": [{"id": "maren", "drive": "to be believed"}],
            "voice": "first", "knowledge": "omniscient"}
    _d = _tf.mkdtemp(prefix="swe_voice_cfg_")
    _p = os.path.join(_d, "c.json")
    with open(_p, "w", encoding="utf-8") as _fh:
        _json.dump(_cfg, _fh)
    _loaded = scene_driver.load_scene_cfg(_p)
    check("a-scene-cfg-CARRIES-voice-and-knowledge",
          (_loaded.get("voice"), _loaded.get("knowledge")) == ("first", "omniscient"),
          str({k: _loaded.get(k) for k in ("voice", "knowledge")}))

    _cfg2 = dict(_cfg); _cfg2.pop("voice"); _cfg2.pop("knowledge")
    with open(_p, "w", encoding="utf-8") as _fh:
        _json.dump(_cfg2, _fh)
    _d2 = scene_driver.load_scene_cfg(_p)
    check("and-DEFAULTS-when-the-director-says-nothing",
          (_d2["voice"], _d2["knowledge"]) == ("close-third", "pov"),
          str({k: _d2.get(k) for k in ("voice", "knowledge")}))

    for _bad, _field in (({"voice": "epic"}, "voice"), ({"knowledge": "everything"}, "knowledge")):
        _c = dict(_cfg2); _c.update(_bad)
        with open(_p, "w", encoding="utf-8") as _fh:
            _json.dump(_c, _fh)
        try:
            scene_driver.load_scene_cfg(_p)
            check("a-bad-%s-in-a-cfg-fails-LOUD" % _field, False, "accepted it")
        except SystemExit:
            check("a-bad-%s-in-a-cfg-fails-LOUD" % _field, True)

    # and the ledger refuses BOTH on a MIGRATED db, which has no CHECK constraints at all (SQLite
    # cannot add one by ALTER). `voice` was unguarded here while `knowledge` was — the same failure
    # one column over, and this suite did not notice because it only ever tested `knowledge`.
    # The error TYPE is the load-bearing part. A fresh database also has a CHECK constraint, so a
    # bad value raises either way and a test that accepted any exception could not tell the Python
    # guard from the SQL one — measured: disabling the ledger guard left this green. LedgerError
    # means the PYTHON guard fired, which is the one a MIGRATED database (no CHECK, because SQLite
    # cannot add one by ALTER) has to rely on.
    from src.engine.ledger import LedgerError
    for _f, _bad in (("knowledge", "everything"), ("voice", "epic")):
        try:
            led.append_scene("bk", 9, "x", "maren", 0, 0, **{_f: _bad})
            check("the-ledger-refuses-a-bad-%s" % _f, False, "accepted it")
        except LedgerError as _e:
            check("the-ledger-refuses-a-bad-%s" % _f, _f in str(_e), str(_e)[:90])
        except Exception as _e:
            check("the-ledger-refuses-a-bad-%s" % _f, False,
                  "only the SQL CHECK caught it (%s) — a migrated db has no CHECK and would "
                  "accept this quietly" % type(_e).__name__)


    # THE VOCABULARY IS IN ONE PLACE, and the schema must not drift from it. `scenes.voice` and
    # `scenes.knowledge` carry CHECK constraints written as SQL string literals — a copy of the
    # tuple, in a file that cannot import it. Derived here so the copy cannot rot: this is the
    # seventh instance of the class CLAUDE.md tabulates, and it is a copy by necessity, so it gets
    # a guard rather than a promise.
    _schema = open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read()
    import re as _re
    for _col, _want in (("voice", set(narrate.VOICES)), ("knowledge", set(narrate.KNOWLEDGE))):
        _m = _re.search(r"CHECK \(%s IN \(([^)]*)\)\)" % _col, _schema)
        check("the-schema-CHECKs-%s" % _col, _m is not None,
              "no CHECK constraint on scenes.%s — a migrated db has none either, so the guard "
              "would live nowhere" % _col)
        if _m:
            _got = {v.strip().strip("'") for v in _m.group(1).split(",")}
            check("and-its-%s-vocabulary-MATCHES-the-engine" % _col, _got == _want,
                  "schema says %s, narration_modes says %s" % (sorted(_got), sorted(_want)))

    # and the whole-book override still wins when the caller asks for one
    # Checked at the PROMPT, not the stub render. The first version asserted only that the render
    # was a non-empty string — and the stub is voice-independent, so it passed whether the override
    # was honoured or ignored entirely. A guard that cannot fail is a coverage claim.
    forced = json.dumps(narrate.build_narration_prompt(
        seg1, "edda", world, "edda", False, None, "second", rows[1]["knowledge"]))
    check("a-whole-book-override-REACHES-the-prompt",
          json.dumps(narrate.VOICES["second"])[1:-1] in forced, forced[:160])
    check("and-DISPLACES-the-scene-own-voice",
          json.dumps(narrate.VOICES["first"])[1:-1] not in forced, forced[:160])

    # ...and the PLUMBING in narrate_book, which the prompt check above does not reach. The stub
    # render is voice-independent, so the only way to see what narrate_book passed down is to
    # capture it. Without this, the override could be dropped between the flag and the renderer and
    # every other assertion here would still pass.
    _real_narrate = narrate.narrate
    seen = []
    try:
        narrate.narrate = (lambda turns, pov, world_, *a, **kw:
                           seen.append((a[5] if len(a) > 5 else kw.get("voice"),
                                        a[6] if len(a) > 6 else kw.get("knowledge"))) or "x")
        narrate.narrate_book(led, "bk", world, chars, stub=True, voice="second")
        check("narrate_book-PASSES-the-override-down",
              seen and all(v == "second" for v, _k in seen), str(seen))
        seen[:] = []
        narrate.narrate_book(led, "bk", world, chars, stub=True)
        check("and-uses-each-scene-OWN-voice-when-none-is-given",
              sorted({v for v, _k in seen}) == ["close-third", "first"], str(seen))
    finally:
        narrate.narrate = _real_narrate


SETTING = {"situation": "Rain over the ford. The kettle is on the hob.",
           "props": ["the copper kettle, dented", "a bundle of feverfew drying by the door"]}


def _sheet_with_facts():
    """A sheet whose vault holds band facts (`shared`), one own belief, a digit, and a duplicate."""
    rows = [{"claim": "Ashford folk tell of a drowned miller.", "shared": "grp.ashford"},
            {"claim": "The ford floods each spring.", "shared": "grp.ashford"},
            {"claim": "A healer's kettle is never left cold.", "shared": "grp.ashford"},
            {"claim": "Feverfew is cut before it flowers.", "shared": "grp.healers"},
            {"claim": "A fever bed costs 3 pennies a night.", "shared": "grp.healers"},
            {"claim": "Ashford folk tell of a drowned miller.", "shared": "grp.healers"},
            {"claim": "My own private belief.", "confidence": 0.9}]
    return {"current": {"vault": rows}}


def _context():
    print("\n[context] the scene's setting and what the POV knows (gate narrator-context)")
    plain = narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren")
    check("control:-no-setting-and-no-facts-builds-the-same-prompt",
          narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren", setting=None, background=[])
          == plain == narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren",
                                                     setting={"situation": "", "props": []}, background=None)
          and "WORLD: %s\n\nRECORDED SCENE" % WORLD["world"] in plain[1]["content"])
    facts = narrate.held_background(_sheet_with_facts(), SETTING)
    check("held_background:-scene-words-first,-then-the-narrowest-band,-no-digit,-no-own-belief,-no-duplicate",
          facts == ["Feverfew is cut before it flowers.", "The ford floods each spring.",
                    "A healer's kettle is never left cold.", "Ashford folk tell of a drowned miller."], facts)
    check("held_background:-bounded", len(narrate.held_background(_sheet_with_facts(), SETTING, cap=2)) == 2
          and narrate.BACKGROUND_CAP == 8)
    check("held_background:-no-sheet-or-no-vault-is-no-facts",
          narrate.held_background(None) == [] and narrate.held_background({"current": {}}) == [])
    user = narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren", setting=SETTING,
                                          background=facts)[1]["content"]
    check("the-prompt-carries-the-situation-and-every-prop,-marked-as-atmosphere-not-events",
          "SETTING (atmosphere, not events)" in user and SETTING["situation"] in user
          and all("- %s" % p in user for p in SETTING["props"]) and "the only events" in user, user[:900])
    check("...and-the-facts,-marked-as-background-not-events,-before-the-recorded-scene",
          "WHAT MAREN KNOWS (background, not events)" in user and all("- %s" % f in user for f in facts)
          and user.index("WHAT MAREN KNOWS") < user.index("RECORDED SCENE"), user[:1200])
    check("no-digit-from-a-held-fact-reaches-the-prompt", "3 pennies" not in user)
    book = {"spines": {"a": "SPINE-A", "b": "SPINE-B"}, "default_spine": "a"}
    check("default_spine-is-the-spine-when-the-world-sets-no-timeline",
          narrate.narration_lens("maren", {}, {}, book)["spine"] == "SPINE-A")
    check("...and-the-world's-timeline-still-wins-when-it-sets-one",
          narrate.narration_lens("maren", {"timeline": "b"}, {}, book)["spine"] == "SPINE-B"
          and narrate.narration_lens("maren", {}, {}, {"spines": {"a": "SPINE-A"}})["spine"] is None)

    # the plumbing: narrate_book hands each scene its OWN pinned situation and props, and the POV's facts
    world, chars = _book_chars()
    chars["maren"].setdefault("current", {})["vault"] = _sheet_with_facts()["current"]["vault"]
    led = Ledger(os.path.join(tempfile.mkdtemp(prefix="narrate_ctx_"), "chronicle.db"))
    led.create_run("cx", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    for cid in ("maren", "edda"):
        led.register_character("cx", cid, chars[cid]["fixed"], chars[cid]["baseline"])
    cfg = {"name": "fireside", "at": {"day": 1, "time": "09:00"}, "situation": SETTING["situation"],
           "props": SETTING["props"], "subject": (None, None),
           "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
           "cast": [{"id": "maren", "drive": "rest"}, {"id": "edda", "drive": "talk"}]}
    nt0 = scene.run_scene(world, copy.deepcopy(chars), cfg, led, "cx", 0, "stub", True, 2, think=False)
    led.append_scene("cx", 0, "fireside", "maren", 0, nt0 - 1, cfg=dict(cfg, subject=None))
    nt1 = scene.run_scene(world, copy.deepcopy(chars), dict(cfg, props=[], situation="Later."), led, "cx", nt0,
                          "stub", True, 2, think=False)
    led.append_scene("cx", 1, "later", "maren", nt0, nt1 - 1)                # recorded with no cfg pinned
    seen = []
    real = narrate.narrate
    try:
        narrate.narrate = lambda *a, **kw: seen.append((kw.get("setting"), kw.get("background"))) or "x"
        narrate.narrate_book(led, "cx", world, chars, stub=True)
    finally:
        narrate.narrate = real
    check("narrate_book-hands-a-pinned-scene-its-situation-and-props-and-the-POV's-facts",
          len(seen) == 2 and seen[0][0] == SETTING and seen[0][1] == facts, str(seen)[:600])
    check("...and-a-scene-with-no-pin-no-setting-(unknown,-not-invented)",
          len(seen) == 2 and seen[1][0] is None, str(seen)[-300:])


TURNS_SRC = TURNS + [
    {"turn": 2, "actor": "maren", "action": "She read the gauge and said, \"Six. That's how high it is.\"",
     "thought": "Two pulls. Keep the peace, or name the flood. The flood wins. So I read it and say the number."},
    {"turn": 3, "actor": "edda", "thought": "She is tired; keep her talking.",
     "action": "Edda talked for a long while about the ford and the miller and the spring floods " * 7},
]
_LOAD_BEARING = ("source material, not a script", "never text for the page", "Do not copy a recorded speech")


def _source_contract():
    print("\n[source] the narrator's source contract (gate narrator-source-contract)")
    names = {"maren": "Maren", "edda": "Edda"}
    sys_, user = (m["content"] for m in narrate.build_narration_prompt(TURNS_SRC, "maren", WORLD, pov_name="Maren",
                                                                      names=names))
    lines = user.splitlines()
    check("the-transcript-labels-each-kind-of-source",
          any(" · THOUGHT (Maren, private" in ln for ln in lines) and any(" · DID/SAID (Maren)" in ln for ln in lines)
          and any(" · DID/SAID (Edda, as Maren saw and heard it" in ln for ln in lines)
          and not any(" · THOUGHT (Edda" in ln for ln in lines), user[-1200:])
    check("...and-the-old-testimony-labels-are-gone",
          "(privately thinks)" not in user and "(observed to do/say)" not in user)
    check("the-pov-thought-precedes-the-act-it-explains",
          user.index("beat 1 · THOUGHT (Maren") < user.index("beat 1 · DID/SAID (Maren)")
          and user.index("beat 3 · THOUGHT (Maren") < user.index("beat 3 · DID/SAID (Maren)"))
    blob = sys_ + "\n" + user
    check("the-contract-frees-wording-and-fixes-substance", "free in wording" in user
          and "Do not copy a recorded speech onto the page" in sys_
          and "Nothing is said on the page that the record does not say" in sys_)
    legend_thought = next((ln for ln in lines if ln.startswith("  THOUGHT (")), "")
    check("the-thought-record-is-named-as-machinery", "THE THOUGHT RECORD" in sys_
          and "never text for the page" in sys_ and "evidence" in legend_thought.lower(), legend_thought)
    edda_long = [ln for ln in lines if " · DID/SAID (Edda" in ln and LEGACY_FLAG in ln]
    check("long-speeches-get-the-rule-and-the-long-turn-is-flagged", "LONG SPEECHES" in sys_ and len(edda_long) == 1
          and not any(LEGACY_FLAG in ln for ln in lines if " · DID/SAID (Maren)" in ln), str(edda_long))
    check("the-wall-holds-under-the-new-labels", "SECRET-EDDA-DOUBT" not in blob)
    omni = narrate.build_narration_prompt(TURNS_SRC, "maren", WORLD, pov_name="Maren", names=names,
                                          knowledge="omniscient")
    check("...and-omniscient-gives-Edda-her-THOUGHT-line", " · THOUGHT (Edda" in omni[1]["content"]
          and "SECRET-EDDA-DOUBT" in omni[1]["content"])
    check("names-not-ids-reach-the-narrator", "DID/SAID (Edda," in user and not any(
        tok in user for tok in ("(edda", "(maren", "edda (", "maren (")), user[-600:])
    check("...and-an-actor-without-a-name-is-shown-by-id",
          " · DID/SAID (edda, as Maren" in narrate.build_narration_prompt(TURNS_SRC, "maren", WORLD,
                                                                            pov_name="Maren")[1]["content"])
    spine = "SPINE-TEXT a plain close third."
    book = {"spines": {"a": spine}, "default_spine": "a", "casting": {"maren": spine}}
    lens = narrate.narration_lens("maren", {}, {}, book)
    sent = narrate.build_narration_prompt(TURNS, "maren", WORLD, pov_name="Maren", lens=lens)[0]["content"]
    check("a-lens-whose-author-equals-its-spine-is-sent-once", lens["author"] is None and sent.count(spine) == 1
          and narrate.narration_lens("maren", {}, {}, dict(book, casting={"maren": "plain, clipped"}))["author"]
          == "plain, clipped", sent[-400:])
    osys = omni[0]["content"]
    check("the-omniscient-prompt-keeps-the-source-contract", "Do not copy a recorded speech onto the page" in osys
          and "Nothing is said on the page that the record does not say" in osys and "THE THOUGHT RECORD" in osys
          and "never text for the page" in osys and "LONG SPEECHES" in osys)
    role = io.open(os.path.join(REPO, ".claude", "agents", "narrator.md"), encoding="utf-8").read()
    contract = blob                              # the RENDERED prompt (source literals wrap mid-phrase)
    check("the-load-bearing-phrases-are-in-both-the-prompt-and-the-role-file",
          all(ph in contract and ph in role for ph in _LOAD_BEARING),
          str([ph for ph in _LOAD_BEARING if ph not in contract or ph not in role]))
    import narration_contract as nc
    copied = "The room was dim. " + " ".join(TURNS[0]["action"].split()[:8]) + " and then the light went."
    hits = nc.copied_runs(copied, TURNS)
    check("copied_runs-finds-an-8-word-run-copied-from-an-action",
          len(hits) == 1 and hits[0][:2] == ("maren", "action") and len(hits[0][2].split()) == 8, str(hits))
    para = "She put the cup down and told them the fever would be gone by morning."
    check("...and-none-in-a-paraphrase", nc.copied_runs(para, TURNS) == [], str(nc.copied_runs(para, TURNS)))
    from_thought = "Then: " + TURNS[0]["thought"]
    check("...and-names-the-thought-when-the-run-is-copied-from-one",
          [h[:2] for h in nc.copied_runs(from_thought, TURNS)] == [("maren", "thought")],
          str(nc.copied_runs(from_thought, TURNS)))


LEGACY_FLAG = "long move, recorded before floor words; break it"
SPEECH = " ".join(["Maren told of the ford and the miller and the spring floods and the mill."] * 20)   # ~300 words
TURNS_FLOOR = [
    {"turn": 0, "actor": "maren", "action": SPEECH, "thought": "She must hear all of it.", "floor": "keep",
     "addressee": "edda"},
    {"turn": 1, "actor": "edda", "action": "Edda turns the cup in her hands.", "thought": "SECRET-EDDA-DOUBT",
     "floor": "hold", "addressee": ""},
    {"turn": 2, "actor": "maren", "action": SPEECH, "thought": "Go on.", "floor": "keep", "addressee": "edda"},
    {"turn": 3, "actor": "edda", "action": "\"That is not so!\"", "thought": "SECRET-EDDA-DOUBT", "floor": "interject",
     "addressee": "maren"},
    {"turn": 4, "actor": "maren", "action": SPEECH, "thought": "Finish it.", "floor": "yield", "addressee": "edda"},
    {"turn": 5, "actor": "edda", "action": "", "thought": "SECRET-EDDA-DOUBT", "floor": "hold", "addressee": ""},
    {"turn": 6, "actor": "edda", "action": "\"When does the ferry run?\"", "thought": "SECRET-EDDA-DOUBT", "floor": "take",
     "addressee": "maren"},
    {"turn": 7, "actor": "maren", "action": "", "thought": "Let her ask again.", "floor": "hold", "addressee": ""},
]


def _floor_labels():
    """Gate narrator-labels (conversation design v2 s6, s7 F): a row with a floor word is labelled by it - SAID
    (who -> whom; keeps|yields|takes|interjects), HELD (who; acts), a silence HELD (POV; silent) or HELD (other) -
    and the SPEECHES and EXCHANGE rules replace LONG SPEECHES, so a 300-word move inside a speech is never flagged
    to be broken. A row recorded before floor words keeps the legacy flag and the old rule."""
    print("\n[floor] the narrator's labels by floor word (gate narrator-labels)")
    names = {"maren": "Maren", "edda": "Edda"}
    sys_, user = (m["content"] for m in narrate.build_narration_prompt(TURNS_FLOOR, "maren", WORLD, pov_name="Maren",
                                                                      names=names))
    lines = user.splitlines()
    want = ["beat 1 · SAID (Maren → Edda; keeps)", "beat 2 · HELD (Edda; acts)", "beat 3 · SAID (Maren → Edda; keeps)",
            "beat 4 · SAID (Edda → Maren; interjects)", "beat 5 · SAID (Maren → Edda; yields)", "beat 6 · HELD (Edda)",
            "beat 7 · SAID (Edda → Maren; takes)", "beat 8 · HELD (Maren; silent)"]
    check("each-row-is-labelled-by-its-floor-word-and-addressee",
          all(any(ln.startswith(w) for ln in lines) for w in want),
          str([w for w in want if not any(ln.startswith(w) for ln in lines)]))
    check("three-keep-rows-of-300-words-are-never-flagged-to-break", not any(
        "break it" in ln or "long" in ln.split(":")[0] for ln in lines if ln.startswith("beat")), user[-800:])
    check("the-speeches-and-exchange-rules-replace-long-speeches", "SPEECHES." in sys_ and "EXCHANGE." in sys_
          and "LONG SPEECHES" not in sys_ and "one speech" in sys_ and "a cut-in" in sys_, sys_[-1500:])
    check("the-wall-holds-under-the-floor-labels", "SECRET-EDDA-DOUBT" not in sys_ + user
          and not any(" · THOUGHT (Edda" in ln for ln in lines) and "Let her ask again." in user)
    check("the-legend-defines-SAID-and-HELD", any(ln.startswith("  SAID (") for ln in lines)
          and any(ln.startswith("  HELD (") for ln in lines), user[:900])
    mixed = TURNS_SRC + TURNS_FLOOR[:1]
    msys, muser = (m["content"] for m in narrate.build_narration_prompt(mixed, "maren", WORLD, pov_name="Maren",
                                                                       names=names))
    check("a-row-recorded-before-floor-words-keeps-the-legacy-flag-and-the-old-rule",
          sum(LEGACY_FLAG in ln for ln in muser.splitlines()) == 1 and "LONG SPEECHES" in msys
          and "SPEECHES." in msys, muser[-900:])
    role = io.open(os.path.join(REPO, ".claude", "agents", "narrator.md"), encoding="utf-8").read()
    check("the-load-bearing-speech-phrases-are-in-both-the-prompt-and-the-role-file",
          all(ph in sys_ and ph in role for ph in ("one speech", "a cut-in")),
          str([ph for ph in ("one speech", "a cut-in") if ph not in sys_ or ph not in role]))


if __name__ == "__main__":
    sys.exit(main())
