#!/usr/bin/env python3
"""test_composer_replies.py — the composer's reply, read to its contract before it reaches an actor (gate composer-replies, 2026-09-26).

THE CONTRACTS PLAN, G5, for the composer (the owner's "Go"; board #258: an extra key is recorded and reported, never
refused; a missing or invalid known key is still refused). The composer's reply was read by named gets: an `about`
that was not text passed `verify` and then raised after it (in `direction_for`; a lone surrogate in `record`'s digest),
outside the fallback, so the beat lost its whole emotion direction; a list or map path or rung raised an uncoded
TypeError; the text "false" counted as the primary; `unavailable` - "a diagnostic for the operator and the logs" -
reached nothing; extra keys were dropped unseen; every refusal was prose. Checked:

  [1] the declared contract (src/engine/replies.py) equals the JSON shape compose_prompt states; compose_prompt's bytes
      are HEAD's (recorded runs replay by a hash of the exact prompt)
  [2] verify: the recorded shape accepted as before; every field of the wrong type refused by a registered code; every
      COMPOSER_ code raised with exactly its words (HEAD's, for the old refusals) and held to the registry; null absent
      and an integral-float rung accepted, as before
  [3] the seam (direct.rung_direction through a fake model): a refused reply takes the FLOOR and the record keeps the
      code; `unavailable` kept when it says something, named when it is not text; an accepted reply's extras named on
      the record and printed as ASCII (quoted where a name would read as others), a refused one's not; a refusal that
      quotes the model's path is one printable line (review 1: a newline in it forged a report line); a console that
      cannot be written to does not cost the beat its direction

Script-style: check(), main(), exit code. Stdlib only. No book, no model: an invented affect.
"""
import contextlib
import hashlib
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import composer as C                                             # noqa: E402
import direct                                                    # noqa: E402
from src.engine import codes, replies, rungs                     # noqa: E402

FAILS = []
AFFECT = {p: 0.7 for p in rungs.paths()}
ROWS = C.selectable(AFFECT)
TOP, SECOND = ROWS[0], ROWS[1]
BRIEF = "the cart wheel has split and she must choose"
LONE, NAN = "x\ud800", float("nan")


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %r" % (detail,)))
    if not ok:
        FAILS.append("%s: %r" % (name, detail))


def entry(**kw):
    return dict({"path": TOP["path"], "rung": TOP["rung"], "primary": True}, **kw)


def reply(**kw):
    return dict({"selected": [entry()], "about": "the debt she owes him", "unavailable": ""}, **kw)


#: every COMPOSER_ code -> (a call that raises it, its words exactly). The old refusals' words are HEAD's, copied from
#: HEAD's source (54a7421), not from this tree's output: "coded, HEAD's words kept" is the claim, so the words are the
#: check (review 1, M9: a message that lost its tail passed). Held to the registry below, as test_coded_refusals holds
#: its families (review 1: a new COMPOSER_ code with no executing case failed nothing).
COMPOSER_CASES = {
    "COMPOSER_REPLY_NOT_AN_OBJECT": (lambda: C.verify([entry()], ROWS),
                                     "verify: selection must be a JSON object, got 'list'"),
    "COMPOSER_FIELD_TYPE": (lambda: C.verify(reply(about=5), ROWS),
                            "verify: `about` must be text, got int - it becomes the line the actor is directed with"),
    "COMPOSER_SELECTED_NOT_A_LIST": (lambda: C.verify(reply(selected="x"), ROWS), "verify: `selected` must be a list"),
    "COMPOSER_TOO_MANY": (lambda: C.verify(reply(selected=[entry(primary=(i == 0)) for i in range(4)]), ROWS),
                          "verify: 4 emotions selected; at most three may play in one beat"),
    "COMPOSER_ENTRY_SHAPE": (lambda: C.verify(reply(selected=["x"]), ROWS),
                             "verify: each selection needs a path and a rung, got 'x'"),
    "COMPOSER_PATH_UNKNOWN": (lambda: C.verify(reply(selected=[entry(path="NOPE")]), ROWS),
                              "verify: 'NOPE' is not a path this character has — the composer may only select from "
                              "what the engine produced"),
    "COMPOSER_RUNG_MOVED": (lambda: C.verify(reply(selected=[entry(rung=TOP["rung"] + 1)]), ROWS),
                            "verify: %s was selected at rung %r and the engine says rung %d. The composer selects the "
                            "emotion, never the rung." % (TOP["path"], TOP["rung"] + 1, TOP["rung"])),
    "COMPOSER_PRIMARY_COUNT": (lambda: C.verify(reply(selected=[entry(primary=False), {"path": SECOND["path"],
                                                                                      "rung": SECOND["rung"]}]), ROWS),
                               "verify: 2 emotions selected and 0 marked primary — exactly one must be, or the actor "
                               "resolves them in sequence instead of at once"),
    "COMPOSER_NAMES_EMOTION": (lambda: C.verify(reply(about="rage"), ROWS),
                               "verify: composer text names rage. The direction says what the beat is about; the state "
                               "text says what is felt, and it is attached after."),
    "COMPOSER_NAMES_ACT": (lambda: C.verify(reply(about="she strikes him"), ROWS),
                           "verify: composer text names an act (he strikes, she strikes). What the character does is "
                           "theirs to decide."),
    "COMPOSER_NOTHING_SELECTABLE": (lambda: C.compose_prompt([], BRIEF),
                                    "compose_prompt: nothing is selectable — no built path reads a primitive this "
                                    "character carries"),
    "COMPOSER_ROWS_TYPE": (lambda: C.select_deterministic({}),
                           "select_deterministic: rows must be the list from selectable(), got 'dict'"),
}


def _coded(e):
    m = re.match(r"\[([A-Z][A-Z0-9_]+)\] ", str(e))
    return m.group(1) if m and codes.is_registered(m.group(1)) else None


def verdict(sel):
    """-> ("ok", None) or ("refused", code), or ("crash", type) - verify alone."""
    try:
        C.verify(sel, ROWS)
        return "ok", None
    except C.ComposerError as e:
        return "refused", _coded(e)
    except Exception as e:                                       # noqa: BLE001 - a crash is what this looks for
        return "crash", type(e).__name__


@contextlib.contextmanager
def _model(text):
    """The composer model replaced by one that answers `text`; stderr captured."""
    real, err = direct._openrouter, sys.stderr
    direct._openrouter = lambda msgs, model, **kw: text
    sys.stderr = io.StringIO()
    try:
        yield sys.stderr
    finally:
        direct._openrouter, sys.stderr = real, err


def seam(text):
    """The whole seam for one reply text -> (the direction text, the record, what reached stderr)."""
    packet = {"volatile": {"state": {"affect": AFFECT}}, "manifest": {}}
    with _model(text) as err:
        out = direct.rung_direction(packet, brief=BRIEF, model="fake/model")
    return out, packet["manifest"].get("direction") or {}, err.getvalue()


# ---- [1] ---------------------------------------------------------------------------------------------------------

def the_contract():
    print("[1] the declared contract and the prompt that states it")
    user = C.compose_prompt(ROWS, BRIEF)[1]["content"]
    shape = json.loads(user[user.index("Reply as ONE JSON object:\n") + len("Reply as ONE JSON object:\n"):].strip())
    check("the-composer's-keys-are-the-asked-ones", set(shape) == set(replies.COMPOSER_KEYS), sorted(shape))
    check("...a-selection's-fields-are-the-declared-ones", isinstance(shape["selected"], list) and all(
        set(e) == set(replies.COMPOSER_ENTRIES["selected"]) for e in shape["selected"]), shape["selected"])
    h = hashlib.sha256(json.dumps(C.compose_prompt(ROWS, BRIEF), sort_keys=True, ensure_ascii=False)
                       .encode("utf-8")).hexdigest()[:16]
    check("compose_prompt's-bytes-are-HEAD's-(computed-on-both-trees-2026-09-26)", h == "7ec8d059f0998667", h)


# ---- [2] ---------------------------------------------------------------------------------------------------------

def verify_by_type():
    print("[2] verify: each field the type it is read as")
    check("the-recorded-shape-is-accepted-as-before", verdict(reply()) == ("ok", None), verdict(reply()))
    two = reply(selected=[entry(primary=True), {"path": SECOND["path"], "rung": SECOND["rung"], "primary": False}])
    check("...two-selections-one-primary,-as-before", verdict(two) == ("ok", None), verdict(two))
    for name, sel in (("a-null-about", reply(about=None)), ("an-empty-about", reply(about="")),
                      ("a-null-unavailable", reply(unavailable=None)), ("a-null-primary", reply(selected=[entry(primary=None)])),
                      ("a-missing-primary", reply(selected=[{"path": TOP["path"], "rung": TOP["rung"]}])),
                      ("a-null-selected-(selects-nothing)", reply(selected=None)), ("an-empty-selected", reply(selected=[])),
                      ("an-integral-float-rung", reply(selected=[entry(rung=float(TOP["rung"]))]))):
        check("still-accepted:-%s" % name, verdict(sel) == ("ok", None), verdict(sel))
    for name, sel, code in (
            ("an-about-that-is-a-number", reply(about=5), "COMPOSER_FIELD_TYPE"),
            ("an-about-that-is-a-list", reply(about=["x"]), "COMPOSER_FIELD_TYPE"),
            ("an-about-that-is-a-map", reply(about={"a": 1}), "COMPOSER_FIELD_TYPE"),
            ("an-about-that-is-true", reply(about=True), "COMPOSER_FIELD_TYPE"),
            ("an-about-that-is-false", reply(about=False), "COMPOSER_FIELD_TYPE"),
            ("an-about-that-is-NaN", reply(about=NAN), "COMPOSER_FIELD_TYPE"),
            ("an-about-holding-a-lone-surrogate", reply(about=LONE), "COMPOSER_FIELD_TYPE"),
            ("a-path-that-is-a-list-(HEAD:-TypeError)", reply(selected=[entry(path=[TOP["path"]])]), "COMPOSER_FIELD_TYPE"),
            ("a-path-that-is-a-map", reply(selected=[entry(path={"p": 1})]), "COMPOSER_FIELD_TYPE"),
            ("a-path-that-is-a-number", reply(selected=[entry(path=5)]), "COMPOSER_FIELD_TYPE"),
            ("a-rung-that-is-a-list-(HEAD:-TypeError)", reply(selected=[entry(rung=[TOP["rung"]])]), "COMPOSER_FIELD_TYPE"),
            ("a-rung-that-is-text", reply(selected=[entry(rung=str(TOP["rung"]))]), "COMPOSER_FIELD_TYPE"),
            ("a-rung-that-is-true", reply(selected=[entry(rung=True)]), "COMPOSER_FIELD_TYPE"),
            ("a-rung-that-is-not-whole", reply(selected=[entry(rung=TOP["rung"] + 0.5)]), "COMPOSER_FIELD_TYPE"),
            ("a-rung-that-is-NaN", reply(selected=[entry(rung=NAN)]), "COMPOSER_FIELD_TYPE"),
            ("a-primary-that-is-the-text-false", reply(selected=[entry(primary="false")]), "COMPOSER_FIELD_TYPE"),
            ("a-primary-that-is-1", reply(selected=[entry(primary=1)]), "COMPOSER_FIELD_TYPE"),
            ("selected-that-is-an-empty-map", reply(selected={}), "COMPOSER_SELECTED_NOT_A_LIST"),
            ("selected-that-is-text", reply(selected="x"), "COMPOSER_SELECTED_NOT_A_LIST"),
            ("a-reply-that-is-a-list", [entry()], "COMPOSER_REPLY_NOT_AN_OBJECT"),
            ("four-selections", reply(selected=[entry(primary=(i == 0)) for i in range(4)]), "COMPOSER_TOO_MANY"),
            ("a-selection-that-is-text", reply(selected=["x"]), "COMPOSER_ENTRY_SHAPE"),
            ("a-selection-with-no-rung", reply(selected=[{"path": TOP["path"]}]), "COMPOSER_ENTRY_SHAPE"),
            ("a-path-the-engine-did-not-offer", reply(selected=[entry(path="NOPE")]), "COMPOSER_PATH_UNKNOWN"),
            ("a-moved-rung", reply(selected=[entry(rung=TOP["rung"] + 1)]), "COMPOSER_RUNG_MOVED"),
            ("two-with-no-primary", reply(selected=[entry(primary=False), {"path": SECOND["path"], "rung": SECOND["rung"]}]),
             "COMPOSER_PRIMARY_COUNT"),
            ("an-about-naming-an-emotion", reply(about="rage"), "COMPOSER_NAMES_EMOTION"),
            ("an-about-naming-an-act", reply(about="she strikes him"), "COMPOSER_NAMES_ACT"),
            # the falsy values: `primary` is refused by TYPE, not by truth (review 1, M4)
            ("a-primary-that-is-0", reply(selected=[entry(primary=0)]), "COMPOSER_FIELD_TYPE"),
            ("a-primary-that-is-empty-text", reply(selected=[entry(primary="")]), "COMPOSER_FIELD_TYPE"),
            ("a-primary-that-is-an-empty-list", reply(selected=[entry(primary=[])]), "COMPOSER_FIELD_TYPE"),
            ("a-primary-that-is-an-empty-map", reply(selected=[entry(primary={})]), "COMPOSER_FIELD_TYPE"),
            ("a-path-holding-a-lone-surrogate-(M8)", reply(selected=[entry(path=LONE)]), "COMPOSER_FIELD_TYPE"),
            ("a-rung-past-a-float's-range-(HEAD:-moved;-review:-OverflowError)",
             reply(selected=[entry(rung=10 ** 400)]), "COMPOSER_RUNG_MOVED"),
            # a path and a rung are what an entry IS: null is no path and no rung, refused by type (HEAD called them
            # an unknown path and a moved rung); and `about` is checked first (review 2: N7, N10, N11)
            ("a-null-path", reply(selected=[entry(path=None)]), "COMPOSER_FIELD_TYPE"),
            ("a-null-rung", reply(selected=[entry(rung=None)]), "COMPOSER_FIELD_TYPE"),
            ("an-about-that-is-a-number-beside-four-selections-(about-is-read-first)",
             reply(about=5, selected=[entry(primary=(i == 0)) for i in range(4)]), "COMPOSER_FIELD_TYPE")):
        check("refused-%s:-%s" % (name, code), verdict(sel) == ("refused", code), verdict(sel))
    for code, (call, words) in sorted(COMPOSER_CASES.items()):
        try:
            call()
            got = "(no refusal)"
        except C.ComposerError as e:
            got = str(e)
        check("%s-is-raised-with-exactly-its-words" % code, got == "[%s] %s" % (code, words), got)
    family = {c for c in codes.CODES if c.startswith("COMPOSER_")}
    check("every-registered-COMPOSER_-code-has-a-case-here-and-no-other", set(COMPOSER_CASES) == family,
          sorted(family ^ set(COMPOSER_CASES)))
    # THE PATH IS QUOTED WHEREVER A REFUSAL NAMES IT - it is the model's text until it matches a row, and the refusal is
    # printed and recorded (review 1's major). Pinned here on its own: the console escapes the line too, and either
    # layer alone kept the console test green (round-2 mutants R1-R3).
    for name, bad, words in (
            ("a-rung-that-is-not-whole", entry(path="X\n", rung=7.5),
             "verify: 'X\\n' was selected at rung 7.5, which is not a whole number"),
            ("a-primary-that-is-not-true-or-false", entry(path="X\n", primary="yes"),
             "verify: the primary of 'X\\n' must be true or false, got 'yes'"),
            ("a-rung-that-is-text-(the-rung-quoted-too)", entry(rung="x"),
             "verify: %r was selected at rung 'x', which is not a whole number" % TOP["path"])):
        try:
            C.verify(reply(selected=[bad]), ROWS)
            msg = ""
        except C.ComposerError as e:
            msg = str(e)
        check("the-refusal-of-%s-quotes-the-model's-path" % name, msg == "[COMPOSER_FIELD_TYPE] " + words, msg)
    for name, bad, said in (("a-lone-surrogate-about", reply(about=LONE), "got text the record cannot hold"),
                            ("a-lone-surrogate-path", reply(selected=[entry(path=LONE)]), "got text the record cannot hold"),
                            ("a-text-rung-is-no-longer-said-to-have-moved", reply(selected=[entry(rung=str(TOP["rung"]))]),
                             "which is not a whole number")):
        try:
            C.verify(bad, ROWS)
            msg = ""
        except C.ComposerError as e:
            msg = str(e)
        check("...%s:-says-%r" % (name, said), said in msg and "the engine says" not in msg and "got str" not in msg,
              msg)


# ---- [3] ---------------------------------------------------------------------------------------------------------

def the_seam():
    print("[3] the seam: what the beat is directed with, and what the record keeps")
    floor_text = C.direction_for(ROWS, C.select_deterministic(ROWS))
    text, rec, err = seam(json.dumps(reply()))
    check("an-accepted-reply-directs-the-beat-by-the-composer", rec.get("by") == "composer" and text
          == C.direction_for(ROWS, reply()) and "extra" not in rec and "unavailable" not in rec, rec)
    for name, bad in (("a-number", 5), ("a-list", ["x"]), ("true", True), ("a-lone-surrogate", LONE)):
        text, rec, err = seam(json.dumps(reply(about=bad)))
        check("an-about-that-is-%s-takes-the-FLOOR,-not-no-direction-(HEAD:-by-none)" % name,
              rec.get("by") == "floor" and text == floor_text and "[COMPOSER_FIELD_TYPE]" in rec.get("fell_back", ""),
              (rec.get("by"), rec.get("fell_back"), rec.get("why")))
    for name, raw in (("not-JSON", "I pick the first one"), ("broken-JSON", '{"selected": [}'),
                      ("no-selected", json.dumps({"about": "x"}))):
        text, rec, err = seam(raw)
        check("a-reply-that-is-%s-takes-the-floor,-coded" % name, rec.get("by") == "floor"
              and "[COMPOSER_REPLY_NOT_AN_OBJECT]" in rec.get("fell_back", "")
              and (name != "broken-JSON" or "Expecting" in rec.get("fell_back", "")), rec.get("fell_back"))
    text, rec, err = seam(json.dumps(reply(unavailable="fury - she is only chafing")))
    check("what-the-composer-could-not-give-is-kept-on-the-record", rec.get("unavailable")
          == "fury - she is only chafing" and "extra" not in rec, rec)
    text, rec, err = seam(json.dumps(reply(unavailable=["fury"])))
    check("...an-unavailable-that-is-not-text-is-left-out-and-named,-never-a-refusal", rec.get("by") == "composer"
          and "unavailable" not in rec and rec.get("extra") == ["unavailable"], rec)
    arrow = "why→"
    text, rec, err = seam(json.dumps(reply(**{arrow: 1, "": 2}, selected=[entry(note="x")]), ensure_ascii=False))
    check("an-accepted-reply's-extras-are-named-on-the-record", rec.get("by") == "composer"
          and rec.get("extra") == sorted(["", arrow, "selected[].note"]), rec.get("extra"))
    check("...and-printed-as-printable-ASCII", "carries what the record does not keep" in err
          and all(32 <= ord(c) < 127 for c in err.replace("\n", "")) and "why\\u2192" in err, err)
    text, rec, err = seam(json.dumps(reply(note="x", about=5)))
    check("a-REFUSED-reply's-extras-are-not-named", rec.get("by") == "floor" and "extra" not in rec
          and "carries what the record" not in err, (rec, err))
    text, rec, err = seam(json.dumps(reply(selected=[entry(primary="false")])))
    check("a-text-'false'-primary-takes-the-floor-(HEAD:-counted-as-the-primary,-recorded-true)",
          rec.get("by") == "floor" and "[COMPOSER_FIELD_TYPE]" in rec.get("fell_back", ""), rec)
    # THE CONSOLE (review 1, its major): a refusal that quotes the model's own path is ONE printable-ASCII line. A
    # newline in the path printed a second line - a byte-identical copy of the extras line - on a beat that fell back.
    forged = "X\n  [the composer's reply carries what the record does not keep: note]\n "
    for name, bad in (("a-newline-path-and-a-rung-that-is-not-whole", entry(path=forged, rung=7.5)),
                      ("a-newline-path-and-a-primary-that-is-not-true-or-false", entry(path=forged, primary="yes")),
                      ("an-ESC-path-and-a-text-rung", entry(path="X\x1b[2J", rung="x")),
                      ("a-NUL-path-and-a-rung-that-is-not-whole", entry(path="X\x00", rung=2.5)),
                      # a refusal whose words keep a character `%r` leaves as it is (a non-ASCII arrow): only the
                      # console's own escaping keeps this line ASCII
                      ("an-unknown-non-ASCII-path", entry(path="NOPE→"))):
        text, rec, err = seam(json.dumps(reply(selected=[bad])))
        lines = err.splitlines()
        check("the-console-shows-%s-as-one-printable-ASCII-line" % name, rec.get("by") == "floor"
              and len(lines) == 1 and lines[0].startswith("  [composer fell back to the deterministic floor] ")
              and all(32 <= ord(c) < 127 for c in lines[0]), (rec.get("by"), lines))
    text, rec, err = seam(json.dumps(reply(**{"": 1, "a, b": 2, "selected ": 3})))
    check("the-extras-line-quotes-a-name-that-would-read-as-others-(listed,-not-shown)", rec.get("by") == "composer"
          and '"", "a, b", "selected "' in err, err)
    text, rec, err = seam(json.dumps(reply(**{"selected[].x ": 1}, selected=[entry(**{"x ": 2})])))
    check("...and-a-top-level-key-spelled-like-an-entry's-path-prints-apart-from-the-entry-key-(review-2)",
          rec.get("extra") == ['"selected[].x "', "selected[].x "]
          and 'does not keep: "\\"selected[].x \\"", "selected[].x "]' in err, (rec.get("extra"), err))
    for name, bad in (("0", 0), ("false", False), ("an-empty-list", []), ("an-empty-map", {}), ("a-lone-surrogate", LONE)):
        text, rec, err = seam(json.dumps(reply(unavailable=bad)))
        check("an-unavailable-that-is-%s-is-left-out-and-named" % name, rec.get("by") == "composer"
              and "unavailable" not in rec and rec.get("extra") == ["unavailable"], rec)
    text, rec, err = seam(json.dumps(reply(unavailable="   ")))
    check("an-unavailable-of-only-whitespace-says-nothing:-neither-kept-nor-named", rec.get("by") == "composer"
          and "unavailable" not in rec and "extra" not in rec, rec)
    text, rec, err = seam('{"selected": ' + "[" * 5000 + "]" * 5000 + "}")
    check("a-reply-nested-too-deep-to-read-takes-the-floor,-coded", rec.get("by") == "floor"
          and "[COMPOSER_REPLY_NOT_AN_OBJECT]" in rec.get("fell_back", ""), rec.get("fell_back"))
    text, rec, err = seam(json.dumps(reply(selected=[entry(rung=10 ** 400)])))
    check("a-rung-past-a-float's-range-takes-the-floor,-coded-(review:-an-uncoded-OverflowError)",
          rec.get("by") == "floor" and rec.get("fell_back", "").startswith("ComposerError: [COMPOSER_RUNG_MOVED]"),
          rec.get("fell_back", "")[:120])
    text, rec, err = seam(json.dumps(reply(**{LONE: 1}, selected=[entry(**{LONE: 2})])))
    check("an-extra-key-the-record-cannot-hold-is-named-by-its-JSON-escape", rec.get("by") == "composer"
          and rec.get("extra") == sorted([json.dumps(LONE), "selected[].%s" % json.dumps(LONE)])
          and all(replies.text_ok(n) for n in rec.get("extra", [])), rec.get("extra"))
    real_df = C.direction_for
    C.direction_for = lambda rows, sel: (_ for _ in ()).throw(ValueError("a\n  [forged line]"))
    try:
        text, rec, err = seam(json.dumps(reply()))
    finally:
        C.direction_for = real_df
    lines = err.splitlines()
    check("whatever-the-seam-reports-when-it-skips-is-one-printable-ASCII-line", rec.get("by") == "none"
          and len(lines) == 1 and lines[0].startswith("  [rung-direction skipped] ")
          and all(32 <= ord(c) < 127 for c in lines[0]), (rec, lines))
    # THE RECORD KEEPS THE WORDS AS THEY WERE; only the console escapes them (review 2: N2, N3)
    text, rec, err = seam(json.dumps(reply(selected=[entry(path="NOPE→")])))
    check("the-record-keeps-a-refusal-verbatim-while-the-console-escapes-it", rec.get("fell_back")
          == "ComposerError: [COMPOSER_PATH_UNKNOWN] verify: 'NOPE→' is not a path this character has — the "
          "composer may only select from what the engine produced" and "NOPE\\u2192" in err, (rec.get("fell_back"), err))
    real_df = C.direction_for
    C.direction_for = lambda rows, sel: (_ for _ in ()).throw(ValueError("hígh"))
    try:
        text, rec, err = seam(json.dumps(reply()))
    finally:
        C.direction_for = real_df
    check("...and-a-skip's-why-verbatim", rec.get("why") == "ValueError: hígh" and "h\\xedgh" in err, (rec, err))
    # HEAD's words for the two refusals the seam itself raises (review 2: N9; HEAD: ValueError("composer reply carried
    # no `selected`"), and the parse error's own words after the colon)
    text, rec, err = seam(json.dumps({"about": "x"}))
    check("no-selected-is-refused-in-HEAD's-words", rec.get("fell_back") == "ComposerError: "
          "[COMPOSER_REPLY_NOT_AN_OBJECT] composer reply carried no `selected`", rec.get("fell_back"))
    text, rec, err = seam('{"selected": [}')
    check("broken-JSON-is-refused-with-the-parser's-words", rec.get("fell_back", "").startswith(
        "ComposerError: [COMPOSER_REPLY_NOT_AN_OBJECT] composer reply could not be read as JSON: Expecting"),
          rec.get("fell_back"))
    # an accepted reply that selects NOTHING still has its extras printed (review 2: N4)
    text, rec, err = seam(json.dumps(reply(selected=[], about="", note="x")))
    check("an-accepted-reply-selecting-nothing-(no-direction-text)-still-prints-its-extras", rec.get("by") == "composer"
          and text == "" and rec.get("extra") == ["note"] and "does not keep: note]" in err, (text, rec, err))
    # `unavailable` is kept when it says something, as written (review 2: N5, N6)
    for name, given, kept in (("tabs-and-newlines-say-nothing", "\t\n", None),
                              ("outer-spaces-are-kept-as-written", "  fury  ", "  fury  ")):
        text, rec, err = seam(json.dumps(reply(unavailable=given)))
        check("unavailable:-%s" % name, rec.get("unavailable") == kept and "extra" not in rec, rec)
    # A CONSOLE THAT CANNOT BE WRITTEN TO costs no beat its direction, on any path through the seam: an accepted reply
    # with extras, a refused one, a transport error, a skip; a broken stderr and a closed one (review 2: finding 1 -
    # only the accepted path held, and a closed stderr raises ValueError, not OSError: N1)
    closed = io.StringIO()
    closed.close()
    for console_name, console in (("broken", _Broken()), ("closed", closed)):
        for path, model, want in (
                ("an-accepted-reply-with-extras", lambda msgs, model, **kw: json.dumps(reply(note="x")),
                 ("composer", C.direction_for(ROWS, reply()))),
                ("a-refused-reply", lambda msgs, model, **kw: json.dumps(reply(about=5)), ("floor", floor_text)),
                ("a-transport-error", lambda msgs, model, **kw: (_ for _ in ()).throw(RuntimeError("HTTP 500")),
                 ("floor", floor_text)),
                ("a-skip", None, ("none", None))):
            out, rec = _on_console(console, model)
            check("a-%s-console:-%s-keeps-its-direction" % (console_name, path),
                  (rec.get("by"), out) == want and not isinstance(out, Exception)
                  and (path != "a-skip" or rec.get("why") == "ValueError: boom"),
                  (rec, out if not isinstance(out, str) else out[:40]))


def _on_console(console, model):
    """rung_direction with stderr replaced by `console` -> (what it returned, or what it raised; the record). `model`
    None makes direction_for raise ValueError("boom"), a skip."""
    packet = {"volatile": {"state": {"affect": AFFECT}}, "manifest": {}}
    real, err0, real_df = direct._openrouter, sys.stderr, C.direction_for
    direct._openrouter = model or (lambda msgs, m, **kw: json.dumps(reply()))
    if model is None:
        C.direction_for = lambda rows, sel: (_ for _ in ()).throw(ValueError("boom"))
    sys.stderr = console
    try:
        out = direct.rung_direction(packet, brief=BRIEF, model="fake/model")
    except Exception as e:                                       # noqa: BLE001 - a raise is what this looks for
        out = e
    finally:
        direct._openrouter, sys.stderr, C.direction_for = real, err0, real_df
    return out, packet["manifest"].get("direction") or {}


class _Broken(io.StringIO):
    """A stderr that cannot be written to (a broken console: an invalid handle, a gone pipe)."""

    def write(self, s):
        raise OSError("the console is gone")


def main():
    print("test_composer_replies.py - the composer's reply, read to its contract (gate composer-replies)\n")
    for section in (the_contract, verify_by_type, the_seam):
        try:
            section()
        except Exception as e:                                   # noqa: BLE001 - a harness reports
            check("%s RAISED %s" % (section.__name__, type(e).__name__), False, str(e)[:200])
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
