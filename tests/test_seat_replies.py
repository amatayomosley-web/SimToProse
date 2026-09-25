#!/usr/bin/env python3
"""test_seat_replies.py — the seats' replies: the keys each contract names, and what a reply carried beyond it (gate seat-replies, 2026-09-25).

THE CONTRACTS PLAN, G5, for the seats (the owner's "Go"; the policy agreed with Symphony on the board, convo #4). The
event, emotion and thermometer seats' parsers read their fields by name, so every other key - an entry's too - was
dropped unseen, and a `showed` in any shape but a map was skipped unseen with it; a seat that did not answer left the
committed turn looking seated, its refusal printed after the commit and recorded nowhere. Checked here:

  [1] the declarations in src/engine/replies.py and the prompts in scripts/appraiser.py agree BLOCK BY BLOCK - each
      prompt's JSON shape is parsed, not grepped; the engine cannot import a script, so this suite holds the two
  [2] what a reply carried beyond its contract, named by an unambiguous path; never raising; printed as ASCII; a
      refusal told from a reply that never came
  [3] the parsers collect it only for a reply they accept and return the same thing with or without it; they refuse
      what they refused before (a non-text `about` or `lands_on` entry where a PerceptSet or a present list checks
      it) and nothing more; where nothing checks, a value they stringified into the record is left out and named (a
      non-text `about`, `about_missing` or `lands_on` entry), as is a `showed` they skip; an actor's non-text tag
      type or durability is refused by code, not a crash; every key `UNREAD` names changes nothing its seat returns
  [4] the drivers, over several beats: a seat's extra keys, its refusal, and a reply that never came land on that
      beat's committed turn and no other; nothing new when there is none of them; an arrow in a key does not crash a
      cp1252 console; a refused beat's error names the seat whose silence made its tags the actor's own; the
      read-along writes its seats' on its turns and rows, and reports them

Script-style: check(), main(), exit code. Stdlib only. Every book here is invented (two keepers on a rock).
"""
import contextlib
import glob
import io
import json
import os
import re
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

import appraiser                                                 # noqa: E402
import provider                                                  # noqa: E402
from src.engine import injuries, replies, rungs, tells           # noqa: E402
from src.engine.records import RecordError                       # noqa: E402

FAILS = []
RAISED = []                                                      # what an in-process driver let out, to inspect
ACTION = "She trims the wick and turns up the lamp."
EVENT = {"type": "mundane", "dimensions": {}, "durability": "transient", "confidence": "sure"}
RUNG = rungs.names_on("WARINESS")[1]
EMOTION = {"readings": [{"path": "WARINESS", "rung": RUNG, "about": ""}], "lands_on": [], "confidence": "sure"}
THERMOMETER = {"levels": {"WARINESS": rungs.names_on("WARINESS")[0]}, "confidence": "sure"}
REFUSED_EVENT = dict(EVENT, dimensions={"nonsense": "slight"}, mood="calm")        # refused - and carrying an extra
REFUSED_EMOTION = dict(EMOTION, readings=[dict(EMOTION["readings"][0], rung="nonsense")], mood="calm")
# a replay with no answer names its folder - built here at run time, since a machine path written into this tree is
# exactly what tests/test_self_contained.py and tests/test_no_private_content.py refuse
UNANSWERED = RecordError("PROVIDER_REPLY_MISSING", "appraise-event: no answer under %s for prompt 06351ded"
                         % os.path.join(tempfile.gettempdir(), "private-books", "My Book", "replies"))
NO_KEY = RecordError("PROVIDER_NO_KEY", "key file %r unreadable" % os.path.join(tempfile.gettempdir(), "private-books", ".env"))


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def _shape(system):
    """The JSON shape under a seat prompt's WHAT YOU RETURN heading, parsed: each alternative list ("a" | "b") keeps
    its first, and a trailing `, ...` goes. A prompt whose shape stops parsing fails here, loudly."""
    body = system[system.index("{", system.index("WHAT YOU RETURN")):]
    return _parse(body[:body.index("}\n\n") + 1])


def _block(text, key):
    """The one-line `"key": ...` block a system's question adds to the event prompt, parsed."""
    line = next(ln for ln in text.splitlines() if ln.strip().startswith('"%s":' % key))
    return _parse("{%s}" % line)


def _parse(s):
    s = re.sub(r'("(?:[^"\\]|\\.)*")(?:\s*\|\s*"(?:[^"\\]|\\.)*")+', r"\1", s)
    return json.loads(re.sub(r",\s*\.\.\.", "", s))


def _entry(v):
    return v[0] if isinstance(v, list) else v


def _kind_and_fields(blk, v, fields):
    """True when a prompt's block has the declared container - a list of entries for a block in replies.LISTS, one
    object otherwise - and EVERY entry it shows asks exactly the declared fields (a second example asking a new
    field, or an object where a list is parsed, passed a first-entry key check)."""
    rows = v if isinstance(v, list) else [v]
    return (isinstance(v, list) == (blk in replies.LISTS) and bool(rows)
            and all(isinstance(r, dict) and set(r) == set(fields) for r in rows))


def declarations_and_prompts():
    print("[1] the declarations and the prompts agree, block by block")
    top = _shape(appraiser._EVENT_SYSTEM)
    check("the-event-seat's-top-level-keys", set(top) == set(replies.EVENT_KEYS), (sorted(top), replies.EVENT_KEYS))
    for blk, fields in replies.EVENT_ENTRIES.items():
        if blk in top:
            check("...its-%s-block:-container-and-every-entry" % blk, _kind_and_fields(blk, top[blk], fields), top[blk])
    for blk, fields in replies.EVENT_MAPS.items():
        check("...its-%s-map's-entries" % blk, isinstance(top[blk], dict) and top[blk]
              and all(isinstance(e, dict) and set(e) == set(fields) for e in top[blk].values()), top.get(blk))
    for key, text in (("exertion", appraiser._EXERTION_BLOCK), ("tells", tells.RUBRIC), ("injuries", injuries.RUBRIC)):
        blk = _block(text, key)
        check("the-%s-question-asks-for-exactly-its-declared-block" % key,
              list(blk) == [key] and _kind_and_fields(key, blk[key], replies.EVENT_ENTRIES[key]), blk)
        flags = dict(exertion=False, tells=False, injuries=False)
        off = appraiser.build_event_messages(ACTION, **flags)[0]["content"]
        on = appraiser.build_event_messages(ACTION, **dict(flags, **{key: True}))[0]["content"]
        check("...asked-only-when-its-flag-is-set", '"%s":' % key not in off and '"%s":' % key in on)
    check("the-event-seat's-asked-blocks-are-exactly-the-three", set(replies.EVENT_ASKED) == {"exertion", "tells", "injuries"})
    top = _shape(appraiser._EMOTION_SYSTEM)
    check("the-emotion-seat's-top-level-keys", set(top) == set(replies.EMOTION_KEYS), sorted(top))
    check("...its-readings-block:-container-and-every-entry",
          _kind_and_fields("readings", top["readings"], replies.EMOTION_ENTRIES["readings"]), top["readings"])
    check("every-declared-list-block-is-a-block-some-seat-has", set(replies.LISTS) <= set(replies.EVENT_ENTRIES)
          | set(replies.EMOTION_ENTRIES), replies.LISTS)
    top = _shape(appraiser._THERMOMETER_SYSTEM)
    check("the-thermometer's-top-level-keys", set(top) == set(replies.THERMOMETER_KEYS), sorted(top))
    shapes = {"event": _shape(appraiser._EVENT_SYSTEM), "thermometer": top}
    check("every-key-UNREAD-names-is-one-its-seat-is-asked-for", replies.UNREAD and all(
        k in shapes[seat] for seat, keys in replies.UNREAD.items() for k in keys), replies.UNREAD)


def what_a_reply_carried():
    print("[2] what a reply carried beyond its contract")
    check("a-well-formed-event-reply-carries-nothing-extra", replies.event_extra(EVENT) == ())
    full = dict(EVENT, mood="calm", showed={"affinity": {"word": "w", "quote": "q", "note": "n"}},
                transfers=[{"what": "a", "from": "b", "to": "c", "terms": "none", "why": "y"}],
                told=[{"what": "a", "to": "b", "cost": "none", "aside": "x"}],
                attribution={"word": "intent", "quote": "q", "note": "n"})
    got = replies.event_extra(full)
    check("a-top-level-key-and-each-entry's-by-path", got == ("attribution.note", "mood", "showed.affinity.note",
                                                             "told[].aside", "transfers[].why"), got)
    for key, block, extra in (("exertion", {"word": "none", "note": "n"}, "exertion.note"),
                              ("tells", [{"quote": "q", "note": "n"}], "tells[].note"),
                              ("injuries", [{"who": "self", "quote": "q", "severity": "minor", "where": "w"}],
                               "injuries[].where")):
        got = replies.event_extra(dict(EVENT, **{key: block}))
        check("the-%s-block-not-asked-is-extra-whole" % key, got == (key,), got)
        got = replies.event_extra(dict(EVENT, **{key: block}), **{key: True})
        check("...asked,-only-its-entry's-stray-key-is", got == (extra,), got)
    check("a-retired-block-left-empty-is-extra", replies.event_extra(dict(EVENT, social={})) == ("social",))
    got = replies.emotion_extra(dict(EMOTION, mood="calm",
                                     readings=[dict(EMOTION["readings"][0], intensity=2, about_missing="x")]))
    check("the-emotion-seat:-a-top-level-key-and-a-reading's,-about_missing-declared", got == ("mood", "readings[].intensity"), got)
    check("the-thermometer:-a-top-level-key", replies.thermometer_extra(dict(THERMOMETER, note="n")) == ("note",))
    got = replies.event_extra(dict(EVENT, **{"told[].why": 1}, told=[{"what": "a", "to": "b", "cost": "none", "why": 2}]))
    check("a-top-level-key-spelled-like-a-path-is-quoted,-so-the-two-never-read-alike",
          got == ('"told[].why"', "told[].why"), got)
    got = replies.event_extra(dict(EVENT, attribution={"word": "intent", "quote": "q", "a.b": 1}))
    check("...and-an-entry-key-holding-a-dot", got == ('attribution."a.b"',), got)
    bad = {"told": "x", "transfers": {"what": "a", "odd": 1}, "showed": ["x"], "attribution": 3, "readings": [None, 3]}
    try:
        got = (replies.event_extra(bad), replies.emotion_extra(bad), replies.thermometer_extra(None),
               replies.extra_keys(["a"], ()), replies.extra_keys("text", ()), replies.emotion_extra(None),
               replies.emotion_extra(["a"]), replies.event_extra("text"))
        check("total:-a-malformed-block-or-a-reply-that-is-not-an-object-never-raises", got[2:] == ((),) * 6, got)
    except Exception as e:                                        # noqa: BLE001 - the check is that nothing raises
        check("total:-a-malformed-block-or-a-reply-that-is-not-an-object-never-raises", False, repr(e))
    check("a-key-is-printed-as-ASCII,-whatever-it-holds", replies.shown(["\u2192note", "mood"]) == "\\u2192note, mood",
          replies.shown(["\u2192note", "mood"]))
    check("a-reply-its-parser-refused-is-a-refusal,-with-its-detail",
          replies.seat_failure(RecordError("APPRAISER_TYPE_UNKNOWN", "x y")) == ("seat_refused", "[APPRAISER_TYPE_UNKNOWN] x y"))
    for exc in (UNANSWERED, NO_KEY, RecordError("PROVIDER_HTTP_ERROR", "503 from the model")):
        check("a-reply-that-never-came-is-unanswered,-its-code-alone:-" + exc.code,
              replies.seat_failure(exc) == ("seat_unanswered", exc.code), replies.seat_failure(exc))
    note = replies.failure_note({"seat_refused": {"event": "[A] a"}, "seat_unanswered": {"emotion": "PROVIDER_X"}})
    check("a-refused-beat's-error-says-the-EVENT-seat-is-why-the-tags-were-the-actor's",
          "because the event seat refused: [A] a" in note and "emotion seat" in note
          and note.index("because the event seat") < note.index("emotion seat") and "because the emotion" not in note, note)
    check("...and-that-the-emotion-seat's-silence-left-no-readings",
          "the emotion seat was never answered, so the beat carries no readings: PROVIDER_X" in note, note)


def _parsed(fn, reply, **kw):
    """-> (result, extra, refusal code) of one parser call with a collecting list."""
    extra = []
    try:
        return fn(json.dumps(reply), extra=extra, **kw), extra, None
    except RecordError as e:
        return None, extra, e.code


def the_parsers():
    print("[3] the parsers")
    kw = dict(objects=["ada"], action=ACTION)
    plain = dict(EVENT, attribution={"word": "intent", "quote": "trims the wick"},
                 told=[{"what": "turns up the lamp", "to": "ada", "cost": "none"}])
    dressed = dict(plain, mood="calm", attribution=dict(plain["attribution"], note="n"),
                   told=[dict(plain["told"][0], why="w")])
    base, none_extra, _c = _parsed(appraiser.parse_event_reply, plain, **kw)
    got, extra, code = _parsed(appraiser.parse_event_reply, dressed, **kw)
    check("the-event-parser-names-what-an-accepted-reply-carried", code is None and extra == ["attribution.note", "mood",
                                                                                          "told[].why"], (code, extra))
    check("...and-returns-the-same-tags-as-without-it", got == base and none_extra == [] and base, (got, base))
    got, extra, code = _parsed(appraiser.parse_event_reply, REFUSED_EVENT, **kw)
    check("...and-collects-nothing-from-a-reply-it-refuses", code == "APPRAISER_DIMENSION_UNKNOWN" and extra == [],
          (code, extra))
    # NOTHING NEW IS REFUSED: what a parser cannot read it leaves out, the rest of the reading kept, and names it
    base_ev = _parsed(appraiser.parse_event_reply, dict(EVENT, object="ada"), **kw)[0]
    for label, value in (("a-list-of-entries", [{"axis": "affinity", "word": "w", "quote": "trims the wick"}]),
                         ("a-word", "warm"), ("the-rubric's-omit", "omit"), ("none", "none"), ("a-flag", True),
                         ("a-number", 3)):
        got, extra, code = _parsed(appraiser.parse_event_reply, dict(EVENT, object="ada", showed=value), **kw)
        check("a-showed-that-is-not-a-map-is-left-out-and-named,-the-reading-kept:-" + label,
              code is None and got == base_ev and extra == ["showed"], (code, got, extra))
    for label, value in (("null", None), ("an-empty-map", {}), ("an-empty-list", []), ("empty-text", ""), ("false", False)):
        got, extra, code = _parsed(appraiser.parse_event_reply, dict(EVENT, object="ada", showed=value), **kw)
        check("...an-empty-one-is-nothing,-named-nowhere:-" + label, code is None and got == base_ev and extra == [],
              (code, got, extra))
    # WHERE A CHECK EXISTS, WHAT IT REFUSED IT STILL REFUSES; WHERE NONE DOES, A STRINGIFIED VALUE IS LEFT OUT, NAMED
    for label, value in (("a-list", ["ada"]), ("a-number", 7), ("an-object", {"id": "ada"}), ("a-flag", True)):
        reply = dict(EMOTION, readings=[dict(EMOTION["readings"][0], about=value)])
        got, extra, code = _parsed(appraiser.parse_emotion_reply, reply)
        check("with-no-PerceptSet,-an-about-that-is-not-text-is-unbound-and-named,-not-stringified:-" + label,
              code is None and got and got[0][0].about == "" and extra == ["readings[].about"], (code, got, extra))
        got, extra, code = _parsed(appraiser.parse_emotion_reply, reply, percepts=[])
        check("...with-one,-it-is-refused,-as-its-string-form-was:-" + label,
              code == "READING_ABOUT_NOT_PERCEIVED" and extra == [], (code, extra))
    percept = [{"entity": "ada", "fidelity": 0.7, "must_surface": True}]
    for label, value, kws in (("7-inside-a-fidelity-0.7", 7, dict(percepts=percept)),
                              ("true-inside-a-flag", True, dict(percepts=percept)),
                              ("7-equal-to-the-character's-own-id", 7, dict(percepts=[], me="7"))):
        got, extra, code = _parsed(appraiser.parse_emotion_reply,
                                   dict(EMOTION, readings=[dict(EMOTION["readings"][0], about=value)]), **kws)
        check("an-about-its-string-form-passed-by-accident-is-refused-like-the-rest:-" + label,
              code == "READING_ABOUT_NOT_PERCEIVED", (code, got))
    got, extra, code = _parsed(appraiser.parse_emotion_reply, dict(EMOTION, lands_on=[None]), present=["none"])
    check("...and-a-lands_on-entry-whose-string-form-was-a-present-id", code == "READING_LANDS_ON_ABSENT", (code, got))
    for label, value in (("null", None), ("empty", ""), ("false", False), ("zero", 0)):
        got, extra, code = _parsed(appraiser.parse_emotion_reply,
                                   dict(EMOTION, readings=[dict(EMOTION["readings"][0], about=value)]), percepts=[])
        check("...an-empty-one-is-unbound,-as-it-always-was,-and-not-named:-" + label,
              code is None and got and got[0][0].about == "" and extra == [], (code, got, extra))
    for label, value in (("null", None), ("a-list", ["ada"]), ("a-number", 7), ("a-flag", True), ("zero", 0),
                         ("an-object", {"id": "ada"})):
        got, extra, code = _parsed(appraiser.parse_emotion_reply, dict(EMOTION, lands_on=[value, " Ada "]))
        check("with-no-present-list,-a-lands_on-entry-that-is-not-text-is-left-out-and-named:-" + label,
              code is None and got[1] == ["Ada"] and extra == ["lands_on[]"], (code, got, extra))
        got, extra, code = _parsed(appraiser.parse_emotion_reply, dict(EMOTION, lands_on=[value]), present=["ada"])
        check("...with-one,-it-is-refused,-as-its-string-form-was,-never-read-as-reached-no-one:-" + label,
              code == "READING_LANDS_ON_ABSENT" and extra == [], (code, got))
    got, extra, code = _parsed(appraiser.parse_emotion_reply, dict(EMOTION, lands_on=["", "  ", "Ada"]))
    check("an-empty-text-lands_on-entry-is-dropped-as-it-always-was,-and-not-named", code is None and got[1] == ["Ada"]
          and extra == [], (code, got, extra))
    for label, value in (("null", None), ("a-list", ["x"]), ("zero", 0)):
        raw = json.dumps(dict(EMOTION, readings=[dict(EMOTION["readings"][0], about_missing=value)]))
        extra = []
        appraiser.parse_emotion_reply(raw, extra=extra)
        check("an-about_missing-that-is-not-text-is-no-concept-gap-and-is-named:-" + label,
              appraiser.missing_concepts(raw) == [] and extra == ["readings[].about_missing"],
              (appraiser.missing_concepts(raw), extra))
    raw = json.dumps(dict(EMOTION, readings=[dict(EMOTION["readings"][0], about_missing="the sea")]))
    check("...a-text-one-is-still-the-concept-gap-it-was", appraiser.missing_concepts(raw) == ["the sea"],
          appraiser.missing_concepts(raw))
    from src.engine.consolidation import validate_tags
    for label, tags, want in (("type,-a-list", {"type": ["mundane"], "durability": "transient"}, "TAG_TYPE_UNKNOWN"),
                              ("type,-an-object", {"type": {"t": 1}, "durability": "transient"}, "TAG_TYPE_UNKNOWN"),
                              ("durability,-a-list", {"type": "mundane", "durability": ["transient"]},
                               "TAG_DURABILITY_INVALID"),
                              ("durability,-an-object", {"type": "mundane", "durability": {}}, "TAG_DURABILITY_INVALID")):
        try:
            got = validate_tags(dict(tags, dimensions={}), [], {})
        except Exception as e:                        # noqa: BLE001 - a crash is the failure this check names
            got = {"ok": None, "flags": [], "raised": repr(e)}
        check("an-actor's-tag-that-is-not-text-is-refused-by-code,-not-a-crash:-" + label,
              got["ok"] is False and [f.get("code") for f in got["flags"]] == [want], got)
    got, extra, code = _parsed(appraiser.parse_event_reply, dict(EVENT, exertion={"word": "none"}), **kw)
    check("an-exertion-block-the-seat-was-not-asked-for-is-extra-and-unread", extra == ["exertion"]
          and "exertion" not in (got or {}), (extra, got))
    got, extra, code = _parsed(appraiser.parse_event_reply, dict(EVENT, exertion={"word": "none"}), exertion=True, **kw)
    check("...asked-for,-it-is-read-and-not-extra", extra == [] and (got or {}).get("exertion") == "none", (extra, got))
    parsers = {"event": (appraiser.parse_event_reply, EVENT, kw), "thermometer": (appraiser.parse_thermometer_reply,
                                                                                 THERMOMETER, {})}
    for seat, keys in sorted(replies.UNREAD.items()):
        fn, reply, kws = parsers[seat]
        for key in keys:
            outs = [_parsed(fn, dict(reply, **{key: v}) if v is not None else {k: x for k, x in reply.items() if k != key},
                            **kws)[0] for v in ("sure", "unsure", None)]
            check("UNREAD:-the-%s's-%s-changes-nothing-it-returns" % (seat, key),
                  outs[0] and outs[0] == outs[1] == outs[2], outs)
    base = _parsed(appraiser.parse_emotion_reply, EMOTION)[0]
    got, extra, code = _parsed(appraiser.parse_emotion_reply,
                               dict(EMOTION, mood="calm", readings=[dict(EMOTION["readings"][0], intensity=2)]))
    check("the-emotion-parser-names-what-an-accepted-reply-carried", extra == ["mood", "readings[].intensity"], extra)
    check("...and-returns-the-same-readings-as-without-it", got == base and base and base[0], (got, base))
    got, extra, code = _parsed(appraiser.parse_emotion_reply, REFUSED_EMOTION)
    check("...and-collects-nothing-from-a-reply-it-refuses", code is not None and extra == [], (code, extra))
    base = _parsed(appraiser.parse_thermometer_reply, THERMOMETER)[0]
    got, extra, code = _parsed(appraiser.parse_thermometer_reply, dict(THERMOMETER, note="n"))
    check("the-thermometer-parser-names-what-an-accepted-reply-carried", extra == ["note"] and got == base and base,
          (extra, got))
    got, extra, code = _parsed(appraiser.parse_thermometer_reply, {"note": "n"})
    check("...and-collects-nothing-from-a-reply-it-refuses", code == "APPRAISER_REPLY_NOT_JSON" and extra == [],
          (code, extra))


@contextlib.contextmanager
def _seats(answers, calls):
    """The frontier model, faked at the one seam every seat calls (provider.call). Each purpose answers from a list,
    one per call, the last repeating; an exception in the list is raised, as the provider raises its own."""
    real, seen = provider.call, {}

    def fake(messages, model, purpose, **_kw):
        calls.append(purpose)
        if purpose not in answers:
            raise AssertionError("an unexpected model call: %s" % purpose)
        queue = answers[purpose] if isinstance(answers[purpose], list) else [answers[purpose]]
        n = seen[purpose] = seen.get(purpose, -1) + 1
        got = queue[min(n, len(queue) - 1)]
        if isinstance(got, Exception):
            raise got
        return json.dumps(got)
    provider.call = fake
    try:
        yield
    finally:
        provider.call = real


def _validation(book):
    dbs = glob.glob(os.path.join(book, "runs", "*.db"))
    if not dbs:
        return []
    con = sqlite3.connect(dbs[0])
    try:
        return [json.loads(v) for (v,) in con.execute("SELECT validation FROM turns ORDER BY turn")]
    finally:
        con.close()


def _drive(script, book, argv, out=None):
    """One driver's main, in process, with live (faked) seats. -> (stdout text, the SystemExit text or None)."""
    import direct
    import scene
    mod = scene if script == "scene" else direct
    saved = sys.argv
    sys.argv = ["%s.py" % script, "--book", book, "--model", "fake/model", "--no-keeper"] + argv
    out = out if out is not None else io.StringIO()
    exited = None
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            mod.main()
    except SystemExit as e:
        exited = str(e)
    except Exception as e:                    # noqa: BLE001 - scene.py lets a refused beat's TagError out; kept to check
        exited = "%s: %s" % (type(e).__name__, e)
        RAISED.append(e)
    finally:
        sys.argv = saved
    out.flush()
    text = out.getvalue() if isinstance(out, io.StringIO) else out.buffer.getvalue().decode("cp1252")
    return text, exited


def _refusal(fn, reply, **kw):
    """What the driver records for a reply its parser refuses: that parser's own words, cut as the record cuts them."""
    try:
        fn(json.dumps(reply), **kw)
    except RecordError as e:
        return str(e)[:200]
    return None


def _fake_turns(calls, extras=(), kind="mundane", dims=None, addressed=True):
    """The actor, faked (the seats are what is tested): each beat a reply to the other keeper (or to no one), carrying
    the beat's entry of `extras` as keys nothing reads, its tags of `kind` with `dims` for dimensions."""
    def fake_turn(packet, event_text, temperament, model, stub, **_k):
        other = next((e.get("target") for e in ((packet.get("volatile") or {}).get("edges") or []) if e.get("target")), "")
        extra = tuple(extras[len(calls)]) if len(calls) < len(extras) else ()
        calls.append(other)
        return ({"action": ACTION, "thought": "", "exit": False, "addressee": other if addressed else "", "act": "",
                 "extra": extra,
                 "tags": {"type": kind, "summary": "tends the lamp", "dimensions": dict(dims or {}),
                          "durability": "transient", "subject": other}}, [])
    return fake_turn


def the_drivers():
    print("[4] the drivers")
    import scene
    from test_replies import TURN, _book, _file, _scene_cfg
    tmp = tempfile.mkdtemp(prefix="seat_replies_")
    ev_x = dict(EVENT, mood="calm", attribution={"word": "intent", "quote": "trims the wick", "note": "n"})
    ev_refusal = _refusal(appraiser.parse_event_reply, REFUSED_EVENT)
    em_refusal = _refusal(appraiser.parse_emotion_reply, REFUSED_EMOTION)
    # SEVEN BEATS OF ONE SCENE, on a strict cp1252 console: what each beat's seats did lands on that beat's turn and
    # no other; beat five's arrows (a seat's key, the actor's) commit and print as ASCII; beat six's lands_on holds
    # only a null - refused as it always was, so the floor keeps its own count and beat seven still comes (read as
    # "reached no one", it pruned every listener and the scene lulled)
    book, calls, actors = _book(os.path.join(tmp, "scene-beats")), [], []
    saved = scene.faithful_turn
    scene.faithful_turn = _fake_turns(actors, extras=((), (), (), (), ("→mood",)))
    console = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    lands_refusal = _refusal(appraiser.parse_emotion_reply, dict(EMOTION, lands_on=[None]), present=["ada"])
    try:
        with _seats({"appraise-event": [ev_x, REFUSED_EVENT, NO_KEY, EVENT, dict(EVENT, **{"→note": 1}), EVENT, EVENT],
                     "appraise-emotion": [REFUSED_EMOTION, dict(EMOTION, readings=[dict(EMOTION["readings"][0], intensity=2)]),
                                          UNANSWERED, EMOTION, EMOTION, dict(EMOTION, lands_on=[None]), EMOTION]}, calls):
            out, exited = _drive("scene", book, ["--scene", _scene_cfg(tmp), "--budget", "7"], out=console)
    finally:
        scene.faithful_turn = saved
    vals = _validation(book)
    want = [{"seat_extra": {"event": ["attribution.note", "mood"]}, "seat_refused": {"emotion": em_refusal}},
            {"seat_extra": {"emotion": ["readings[].intensity"]}, "seat_refused": {"event": ev_refusal}},
            {"seat_unanswered": {"event": "PROVIDER_NO_KEY", "emotion": "PROVIDER_REPLY_MISSING"}},
            {},
            {"seat_extra": {"event": ["→note"]}},
            {"seat_refused": {"emotion": lands_refusal}},
            {}]
    got = [{k: v for k, v in val.items() if k.startswith("seat_")} for val in vals]
    check("scene.py:-seven-beats,-each-turn-records-its-own-seats-and-no-other's,-a-null-lands_on-no-lull",
          exited is None and got == want and lands_refusal.startswith("[READING_LANDS_ON_ABSENT]"), (exited, got))
    check("...a-refused-reply's-extra-key-recorded-nowhere", "mood" not in json.dumps(got[1:2]), got[1:2])
    check("...a-reply-that-never-came-leaves-no-path-in-the-log-or-on-the-console",
          "private-books" not in json.dumps(vals) and "private-books" not in out
          and "event seat was never answered: PROVIDER_NO_KEY" in out, out[-600:])
    check("...and-each-beat's-extras-reported", "event: attribution.note, mood" in out
          and "emotion: readings[].intensity" in out, out[-600:])
    check("...an-arrow-in-a-seat's-key-and-the-actor's-commits-on-a-cp1252-console,-printed-as-ASCII",
          len(vals) == 7 and vals[4].get("reply_extra") == ["→mood"] and "event: \\u2192note" in out
          and "nothing reads: \\u2192mood" in out, (exited, vals[4:], out[-400:]))
    # THE FLOOR, where it can prune: no one addressed, the act a threat, so a listener speaks only on salience. The
    # seat's own "reached no one" ([]) prunes it and the scene lulls - the control that proves the floor is seen; a
    # refused lands_on must not read as that, or one bad entry ends the scene (the round-4 cut did)
    threat = dict(EVENT, type="threat", dimensions={"threat": "moderate"})
    floor_runs = {}
    for label, lands in (("the-seat's-own-reached-no-one", []), ("a-null-entry", [None]), ("everyone", ["ada", "mira"])):
        book = _book(os.path.join(tmp, "scene-floor-" + label))
        scene.faithful_turn = _fake_turns([], addressed=False)
        try:
            with _seats({"appraise-event": [threat], "appraise-emotion": [dict(EMOTION, lands_on=lands)]}, []):
                out, exited = _drive("scene", book, ["--scene", _scene_cfg(tmp), "--budget", "4"])
        finally:
            scene.faithful_turn = saved
        floor_runs[label] = (exited, _validation(book))
    exited, vals = floor_runs["the-seat's-own-reached-no-one"]
    check("the-floor-scene-can-prune:-the-seat's-own-reached-no-one-lulls-it-after-one-beat",
          exited is None and len(vals) == 1, (exited, len(vals)))
    exited, vals = floor_runs["a-null-entry"]
    check("...a-refused-lands_on-leaves-the-floor-its-own-count:-all-four-beats",
          exited is None and len(vals) == 4 and all(
              (v.get("seat_refused") or {}).get("emotion", "").startswith("[READING_LANDS_ON_ABSENT]") for v in vals),
          (exited, [v.get("seat_refused") for v in vals]))
    exited, vals = floor_runs["everyone"]
    check("...and-a-reply-naming-everyone-runs-all-four-too", exited is None and len(vals) == 4, (exited, len(vals)))
    # THE FALLBACK FAILS TOO, in the scene - at validation (a bad type) and before it (an off-ladder severity word,
    # which fails where the fallback is read): either way the error names the seat whose silence made the tags
    for label, kind, dims, seat, want in (
            ("at-validation", "not-a-type", None, REFUSED_EVENT,
             ("TAG_TYPE_UNKNOWN", "because the event seat refused: [APPRAISER_DIMENSION_UNKNOWN]")),
            ("at-its-severity-words", "mundane", {"threat": "none"}, UNANSWERED,
             ("SEVERITY_WORD_UNKNOWN", "because the event seat was never answered: PROVIDER_REPLY_MISSING"))):
        book = _book(os.path.join(tmp, "scene-fallback-" + label))
        scene.faithful_turn = _fake_turns([], kind=kind, dims=dims)
        del RAISED[:]
        try:
            with _seats({"appraise-event": [seat], "appraise-emotion": [EMOTION]}, []):
                out, exited = _drive("scene", book, ["--scene", _scene_cfg(tmp), "--budget", "1"])
        finally:
            scene.faithful_turn = saved
        check("scene.py:-the-fallback-fails-%s:-the-error-names-the-seat" % label, exited is not None
              and all(w in exited for w in want) and "private-books" not in exited and not _validation(book),
              (exited or "")[-400:])
        if label == "at-its-severity-words":         # scene.py lets it out, and Python prints the chain it carries
            e = RAISED[-1] if RAISED else None
            check("...and-carries-no-chain-that-would-print-the-seat's-own-error,-path-and-all",
                  e is not None and e.__cause__ is None and e.__suppress_context__, repr(e)[:200])
    # THE LAW CHECK'S FAILURE LINE, on a strict cp1252 console: an act is model text, printed before the commit
    from src.engine import bible

    class _Led:
        con = None

        def run_config(self, _run_id):
            return {bible.CONFIG_KEY: "a-pinned-bible"}

    def _fails(*_a, **_k):
        raise bible.BibleError("BIBLE_WORLD_NOT_A_DICT", "the check could not run")
    real_verdict, bible.verdict_for = bible.verdict_for, _fails
    console = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    try:
        with contextlib.redirect_stdout(console):
            got = scene._law_events(_Led(), "r", {}, {}, {"act": "lights the lamp → signal"}, "mira")
        console.flush()
        said = console.buffer.getvalue().decode("cp1252")
    except Exception as e:                            # noqa: BLE001 - the check is that it does not raise
        got, said = e, ""
    finally:
        bible.verdict_for = real_verdict
    check("scene.py:-the-law-check's-failure-line-survives-a-cp1252-console-and-prints-ASCII",
          isinstance(got, list) and got and got[0].type == "law-violation" and "\\u2192 signal" in said, (got, said))
    # THE CHAIR, one supplied turn per book
    turn = _file(tmp, "turn.json", TURN)
    argv = ["--char", "Mira", "--circumstance", "the lamp gutters", "--turn-json", turn]
    for label, event, emotion, want in (
            ("extra", ev_x, dict(EMOTION, readings=[dict(EMOTION["readings"][0], intensity=2)]),
             {"seat_extra": {"event": ["attribution.note", "mood"], "emotion": ["readings[].intensity"]}}),
            ("event-refused", REFUSED_EVENT, EMOTION, {"seat_refused": {"event": ev_refusal}}),
            ("emotion-refused", EVENT, REFUSED_EMOTION, {"seat_refused": {"emotion": em_refusal}}),
            ("event-unanswered", UNANSWERED, EMOTION, {"seat_unanswered": {"event": "PROVIDER_REPLY_MISSING"}}),
            ("emotion-unanswered", EVENT, NO_KEY, {"seat_unanswered": {"emotion": "PROVIDER_NO_KEY"}}),
            ("plain", EVENT, EMOTION, {})):
        book, calls = _book(os.path.join(tmp, "chair-" + label)), []
        with _seats({"appraise-event": [event], "appraise-emotion": [emotion]}, calls):
            out, exited = _drive("direct", book, argv)
        vals = _validation(book)
        got = {k: v for k, v in (vals[0] if vals else {}).items() if k.startswith("seat_")}
        check("direct.py:-%s" % label, exited is None and len(vals) == 1 and got == want
              and calls == ["appraise-event", "appraise-emotion"], (exited, got, calls))
        if label.endswith("unanswered"):
            check("...a-reply-that-never-came-leaves-no-path-in-the-log-or-on-the-console",
                  "private-books" not in json.dumps(vals) and "private-books" not in out
                  and "seat was never answered: PROVIDER_" in out, out[-400:])
    # AN ARROW IN A KEY, ON A CP1252 CONSOLE: the beat commits and the key prints as ASCII
    book = _book(os.path.join(tmp, "chair-arrow"))
    console = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    with _seats({"appraise-event": [dict(EVENT, **{"\u2192note": 1})], "appraise-emotion": [EMOTION]}, []):
        out, exited = _drive("direct", book, ["--char", "Mira", "--circumstance", "the lamp gutters", "--turn-json",
                                              _file(tmp, "arrow.json", dict(TURN, act="lights the lamp \u2192 signal",
                                                                            **{"\u2192mood": 1}))], out=console)
    vals = _validation(book)
    check("an-arrow-in-a-seat's-key,-the-actor's-key-and-its-act-commits-on-a-cp1252-console", exited is None
          and len(vals) == 1 and vals[0].get("seat_extra") == {"event": ["\u2192note"]}
          and vals[0].get("reply_extra") == ["\u2192mood"], (exited, vals))
    check("...printed-as-ASCII", "event: \\u2192note" in out and "nothing reads: \\u2192mood" in out
          and "reads none: lights the lamp \\u2192 signal" in out, out[-600:])
    # THE FALLBACK FAILS TOO, in the chair: at validation and before it, the error names the seat
    for label, tags, seat, want in (
            ("at-validation", dict(TURN["tags"], type="not-a-type"), REFUSED_EVENT,
             ("TAG_TYPE_UNKNOWN", "because the event seat refused: [APPRAISER_DIMENSION_UNKNOWN]")),
            ("at-its-severity-words", dict(TURN["tags"], dimensions={"threat": "none"}), UNANSWERED,
             ("SEVERITY_WORD_UNKNOWN", "because the event seat was never answered: PROVIDER_REPLY_MISSING")),
            ("at-validation,-a-type-that-is-not-text", dict(TURN["tags"], type=["mundane"]), UNANSWERED,
             ("TAG_TYPE_UNKNOWN", "because the event seat was never answered: PROVIDER_REPLY_MISSING"))):
        book = _book(os.path.join(tmp, "chair-fallback-" + label))
        bad = _file(tmp, "bad-%s.json" % label, dict(TURN, tags=tags))
        with _seats({"appraise-event": [seat], "appraise-emotion": [EMOTION]}, []):
            out, exited = _drive("direct", book, ["--char", "Mira", "--circumstance", "the lamp gutters", "--turn-json", bad])
        check("direct.py:-the-fallback-fails-%s:-the-error-names-the-seat" % label, exited is not None
              and all(w in exited for w in want) and "private-books" not in exited and not _validation(book),
              (exited or "")[-400:])
    # THE CHAIR'S LANDS_ON (no present list is passed, so nothing else checks the entries): a null or a list was
    # stringified into rows of the append-only lands_on table - "None", "['ada']"
    book = _book(os.path.join(tmp, "chair-lands"))
    with _seats({"appraise-event": [EVENT], "appraise-emotion": [dict(EMOTION, lands_on=[None, ["ada"], "Ada"])]}, []):
        out, exited = _drive("direct", book, argv)
    vals = _validation(book)
    con = sqlite3.connect(glob.glob(os.path.join(book, "runs", "*.db"))[0]) if not exited else None
    rows = [r[0] for r in con.execute("SELECT char_id FROM lands_on")] if con else None
    check("direct.py:-a-lands_on-entry-that-is-not-a-name-never-reaches-the-lands_on-table,-and-is-named",
          exited is None and rows == ["Ada"] and vals and vals[0].get("seat_extra") == {"emotion": ["lands_on[]"]},
          (exited, rows, vals))
    the_readalong(tmp)


def the_readalong(tmp):
    import readalong
    from test_readalong import _book
    book, lines = _book(os.path.join(tmp, "dressed")), []
    with _seats({"appraise-emotion": dict(EMOTION, mood="calm"), "thermometer": dict(THERMOMETER, note="n")}, []):
        run_id = readalong.run(book, stub=False, model="fake/model", beat_words=40, thermometer=1, log=lines.append)
    vals = _validation(book)
    check("the-read-along:-its-emotion-seat's-extra-key-lands-on-each-turn", vals and all(
        v.get("seat_extra") == {"emotion": ["mood"]} for v in vals), vals[:2])
    rows = [json.loads(line) for line in io.open(os.path.join(book, "runs", "%s.levels.jsonl" % run_id), encoding="utf-8")]
    check("...and-its-thermometer's-on-each-levels-row", rows and all(r.get("extra") == ["note"] for r in rows), rows[:2])
    said = [ln for ln in lines if "nothing reads" in ln]
    check("...and-reports-both,-once", len(said) == 1 and "emotion mood x%d" % len(vals) in said[0]
          and "thermometer note x%d" % len(rows) in said[0], said)
    book, lines = _book(os.path.join(tmp, "plain")), []
    with _seats({"appraise-emotion": EMOTION, "thermometer": THERMOMETER}, []):
        run_id = readalong.run(book, stub=False, model="fake/model", beat_words=40, thermometer=1, log=lines.append)
    vals = _validation(book)
    rows = [json.loads(line) for line in io.open(os.path.join(book, "runs", "%s.levels.jsonl" % run_id), encoding="utf-8")]
    check("...and-nothing-new-when-they-answered-plainly", vals and rows and all(set(v) == {"ok", "flags"} for v in vals)
          and all("extra" not in r for r in rows) and not any("nothing reads" in ln for ln in lines), (vals[:1], rows[:1]))


def main():
    declarations_and_prompts()
    what_a_reply_carried()
    the_parsers()
    the_drivers()
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
