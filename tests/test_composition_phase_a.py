#!/usr/bin/env python3
"""test_composition_phase_a.py — the classify half of the composition pass.

WHAT WAS MISSING. `docs/composition-pass.md` specifies two phases and calls their separation the
whole design: an LLM decides WHICH formative profiles a backstory matches, and a script does the
arithmetic. Phase B shipped with a 94-profile library. Phase A did not, so the only route to picks
was typing `profile_id:weight` on the command line — which is why `guide-emotional-authoring.md`
says the creation pass is unbuilt, and why having built a world bought the author nothing
mechanically.

THE TEST THAT MATTERS MOST is the refusal of a reply carrying final NUMBERS. The doc states the
consequence exactly: reproducibility goes, the ±0.35 cap stops being enforceable, and a
classification error becomes indistinguishable from a calibration one. A validator that shrugged at
that would have given away the seam while looking like it worked.

Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import composition_pass as cp                              # noqa: E402
from src.engine import profiles as P                       # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if not cond:
        FAILS.append("%s%s" % (name, ("  — " + detail) if detail else ""))
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _a_real_profile():
    return sorted(P.LIBRARY)[0]


def test_the_prompt_shows_the_library_WITH_its_diffs():
    """"A classifier that cannot see what a profile DOES is guessing at labels" — the doc's own
    reason for showing the diffs rather than only the names."""
    msgs = cp.build_classify_prompt("Raised in a lighthouse by a grandmother who barely spoke.")
    blob = json.dumps(msgs)
    check("the-backstory-reaches-the-prompt", "lighthouse" in blob, blob[:160])
    check("every-profile-is-listed",
          all(pid in blob for pid in list(sorted(P.LIBRARY))[:5]), "profiles missing")
    check("and-their-DIFFS-are-visible", "DIFFS:" in blob, blob[:200])
    check("the-rules-say-an-EMPTY-answer-is-legitimate",
          "legitimate answer" in blob, blob[:200])
    check("and-forbid-final-numbers", "never write final numbers" in blob, blob[:200])


def test_a_reply_carrying_final_NUMBERS_is_refused():
    """THE SEAM. The doc: if the LLM emits final numbers, reproducibility goes, the cap stops being
    enforceable, and a classification error becomes indistinguishable from a calibration one."""
    for banned in ("baseline", "temperament", "traits", "model"):
        try:
            cp.picks_from_classification({"picks": [], banned: {"DISPLEASURE": 0.7}})
            check("refuses-a-reply-carrying-%s" % banned, False, "accepted it")
        except ValueError as e:
            check("refuses-a-reply-carrying-%s" % banned, "final numbers" in str(e), str(e))


def test_a_malformed_pick_is_refused_with_the_reason():
    """Each refusal exists because the doc names the failure it prevents; the message says which."""
    pid = _a_real_profile()
    bad = [
        ("no-profile",      {"picks": [{"weight": 0.5}]},                       "not in the library"),
        ("unknown-profile", {"picks": [{"profile": "not_a_profile"}]},          "not in the library"),
        ("weight-too-high", {"picks": [{"profile": pid, "weight": 1.4}]},       "(0, 1]"),
        ("weight-zero",     {"picks": [{"profile": pid, "weight": 0.0}]},       "(0, 1]"),
        ("weight-not-num",  {"picks": [{"profile": pid, "weight": "a lot"}]},   "non-numeric"),
        ("not-an-object",   {"picks": ["neglect"]},                             "not an object"),
    ]
    for name, reply, want in bad:
        try:
            cp.picks_from_classification(reply)
            check("refuses-%s" % name, False, "accepted it")
        except ValueError as e:
            check("refuses-%s" % name, want in str(e), str(e))


def test_a_good_reply_becomes_picks_and_an_empty_one_is_allowed():
    """An empty picks list is a legitimate answer — some people are genuinely unremarkable, and
    inventing a formative wound for them is worse than saying so."""
    pid = _a_real_profile()
    picks, report = cp.picks_from_classification(
        {"picks": [{"profile": pid, "weight": 0.3, "why": "partial match only"}]})
    check("a-good-reply-becomes-picks",
          picks == [{"profile": pid, "weight": 0.3, "why": "partial match only"}], str(picks))
    check("and-carries-no-proposal-report", report is None, str(report))

    empty, _ = cp.picks_from_classification({"picks": []})
    check("an-EMPTY-classification-is-allowed", empty == [], str(empty))


def test_a_proposed_profile_goes_through_the_ADMIT_gate():
    """`profiles.admit` is the separability check. Trusting a proposal instead of running it would
    let a near-duplicate into the library, which is exactly what that gate exists to stop — so the
    report says admitted or not, and the caller composes only the picks either way."""
    pid = _a_real_profile()
    # a near-duplicate of something already in the library must NOT be admitted
    dupe = dict(P.get(pid))
    dupe["name"] = "a different name for the same thing"
    picks, report = cp.picks_from_classification({"picks": [], "propose": dupe})
    check("a-proposal-is-REPORTED", report is not None and "admitted" in report, str(report))
    check("a-near-duplicate-is-NOT-admitted", report and not report["admitted"], str(report))
    check("and-the-reason-is-given", report and report["reason"], str(report))
    check("picks-are-unaffected-by-a-rejected-proposal", picks == [], str(picks))


def test_phase_B_still_works_untouched():
    """The compatibility contract: every existing --picks invocation must behave exactly as before,
    because Phase A is additive and nobody's authored characters may move."""
    pid = _a_real_profile()
    parsed = cp.parse_picks(["%s:0.5" % pid, pid])
    check("parse_picks-is-unchanged",
          parsed == [{"profile": pid, "weight": 0.5}, {"profile": pid, "weight": 1.0}], str(parsed))


def test_the_attachment_classifier_names_a_word_and_never_a_number():
    """GATE 5 (bond-arithmetic.md s3): the first LLM classification step with a coded parser. The
    prompt shows the four relation words with their boundary tests and the world's registered ids —
    and no digit; the parser refuses six shapes by code; the engine prices; a gap is never minted."""
    import re
    from src.engine.records import RecordError
    world = {"locations": [{"id": "mill", "what": "the water-mill at the ford"}, {"id": "chapel", "what": "the chapel on the hill"}],
             "people": [{"id": "ash", "groups": ["guild"]}, {"id": "bel"}]}
    back = "Ash was born at the mill and has run it since her father died. She attends the guild when it sits, which is seldom."
    msgs = cp.build_attach_classify_prompt(back, world)
    text = msgs[0]["content"] + msgs[1]["content"]
    check("attach-prompt-shows-the-four-words", all(w in text for w in ("life", "post", "member", "acquainted")))
    check("attach-prompt-shows-the-registered-ids-with-their-what", "loc.mill — the water-mill at the ford" in text and "grp.guild" in text)
    check("attach-prompt-carries-no-digit", re.search(r"\d", text) is None, re.findall(r"\d", text)[:5])
    good = {"holds": [{"entity": "loc.mill", "relation": "life", "because": "has run it since her father died"}],
            "gaps": [{"named": "the ford", "because": "born at the mill"}]}
    holds, gaps = cp.holds_from_classification(good, back, world)
    check("attach-a-good-reply-becomes-a-word-and-its-sentence", holds == {"loc.mill": ("life", "has run it since her father died")}, holds)
    check("attach-a-gap-is-returned-not-minted", gaps == [{"named": "the ford", "because": "born at the mill"}] and "the ford" not in holds, gaps)
    applied = cp.apply_attachments({}, holds, world)
    check("attach-apply-prices-from-the-table-with-the-word-in-the-note",
          abs(applied["current"]["attachments"]["loc.mill"]["hold"] - .85) < 1e-9 and applied["current"]["attachments"]["loc.mill"]["note"].startswith("life:"), applied)
    for name, reply, code in (
            ("not-an-object", ["loc.mill"], "COMPOSITION_ATTACH_REPLY_NOT_AN_OBJECT"),
            ("a-number-in-the-reply", {"holds": [{"entity": "loc.mill", "relation": "life", "hold": 0.9, "because": "has run it since her father died"}]}, "COMPOSITION_ATTACH_NUMBER_IN_REPLY"),
            ("an-unlisted-entity", {"holds": [{"entity": "mill", "relation": "life", "because": "has run it since her father died"}]}, "COMPOSITION_ATTACH_ENTITY_UNLISTED"),
            ("an-unknown-word", {"holds": [{"entity": "loc.mill", "relation": "fond", "because": "has run it since her father died"}]}, "COMPOSITION_ATTACH_WORD_UNKNOWN"),
            ("a-sentence-not-in-the-backstory", {"holds": [{"entity": "loc.mill", "relation": "life", "because": "she loves the mill"}]}, "COMPOSITION_ATTACH_BECAUSE_NOT_IN_BACKSTORY"),
            ("a-repeated-entity", {"holds": [{"entity": "loc.mill", "relation": "life", "because": "has run it since her father died"},
                                             {"entity": "loc.mill", "relation": "post", "because": "born at the mill"}]}, "COMPOSITION_ATTACH_ENTITY_REPEATED")):
        try:
            cp.holds_from_classification(reply, back, world)
            check("attach-refuses-%s" % name, False, "accepted")
        except RecordError as e:
            check("attach-refuses-%s" % name, e.code == code, e.code)
    three = {"loc.mill": ("life", "has run it since her father died"), "loc.chapel": ("life", "born at the mill"), "grp.guild": ("life", "She attends the guild")}
    try:
        cp.apply_attachments({}, three, world); check("attach-three-life-holds-refused-by-the-engine", False, "accepted")
    except RecordError as e:
        check("attach-three-life-holds-refused-by-the-engine", e.code == "ATTACH_LIFE_CAP", e.code)


def main():
    print("test_composition_phase_a.py — classify a backstory into picks\n")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print("\n%s" % ("test_composition_phase_a: OK (the classifier picks; it never writes numbers)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
