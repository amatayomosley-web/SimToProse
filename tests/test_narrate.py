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
    cfg = {"name": "fireside", "situation": "Two healers by the fire.", "subject": (None, None),
           "opening_tags": {"type": "mundane", "dimensions": {}, "durability": "transient"},
           "cast": [{"id": "maren", "drive": "rest"}, {"id": "edda", "drive": "talk"}]}
    nt0 = scene.run_scene(world, chars, cfg, led, "bk", 0, "stub", True, 2, think=False)
    led.append_scene("bk", 0, "fireside", "maren", 0, nt0 - 1)           # scene 0 POV = maren (the actor)
    cfg2 = dict(cfg, name="the-ward", situation="Later, in the sickroom.")
    w2, c2 = _book_chars()
    nt1 = scene.run_scene(w2, c2, cfg2, led, "bk", nt0, "stub", True, 2, think=False)
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
        thinkers = {ln.split(" (privately thinks)")[0]
                    for ln in blob.splitlines() if "(privately thinks)" in ln}
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
    _cfg = {"name": "the-ward", "situation": "s",
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


if __name__ == "__main__":
    sys.exit(main())
