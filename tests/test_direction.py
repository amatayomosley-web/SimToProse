#!/usr/bin/env python3
"""test_direction.py — gate-5 proof: numbers never reach the prompt (design.md guardrail).

Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.direction import direct_affect, direct_condition, direct_edge, sureness  # noqa: E402
from src.engine.direction import (  # noqa: E402  the TABLES themselves, walked whole below
    _PHRASES, _REFLEXIVE_PHRASES, _EDGE_PHRASES, _THEIR_VIEW_PHRASES, _COND,
    _UNBOUND_PHRASES, _phrase_for)
from src.engine.records import PRIMARIES                                                 # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


def flat(v):
    return {p: v for p in PRIMARIES}


def temp(mean=0.5):
    return {p: {"mean": mean, "variability": 0.1} for p in PRIMARIES}


def test_no_digits_ever():
    """THE guardrail: across a sweep of vectors, no numeral appears in any output."""
    print("\n[1] DIGIT-FREE OUTPUT")
    maren_temp = json.load(open(os.path.join(REPO, "characters/maren-healer.json"), encoding="utf-8"))["baseline"]["temperament"]
    outs = []
    for v in (0.0, 0.13, 0.27, 0.42, 0.56, 0.71, 0.85, 0.99, 1.0):
        outs.append(direct_affect(flat(v), temp(0.5)))
        outs.append(direct_affect(flat(v), maren_temp))
        outs.append(direct_condition({"energy": v, "allostatic_load": 1.0 - v}))
        outs.append(direct_edge({"trust": v, "affinity": 1.0 - v, "respect": v, "debt": v}))
        outs.append(sureness(v))
    bad = [o for o in outs if re.search(r"\d", o)]
    check("no-numerals-in-any-direction", not bad, "leaked: %s" % bad[:3])


def test_monotone_bands():
    """Higher value -> strictly later band phrase for FEAR (monotone strength)."""
    print("\n[2] MONOTONE BANDS")
    t = temp(0.1)   # low mean so every level deviates -> always surfaces
    seen = []
    for v in (0.05, 0.4, 0.7, 0.95):
        line = direct_affect(dict(flat(0.1), FEAR=v), t)
        seen.append(line)
    check("fear-quiet-low", "act as you ordinarily would" in seen[0] or "face value" in seen[0], seen[0])
    check("fear-watchful-mid", "ways out in view" in seen[1], seen[1])
    check("fear-pressing-strong", "give ground" in seen[2], seen[2])
    check("fear-gripped-peak", "protect yourself first" in seen[3], seen[3])
    # every band must be an INSTRUCTION, not a report of feeling (the whole point of the module)
    for i, line in enumerate(seen[1:], start=1):
        check("fear-band-%d-is-a-direction" % i, line.startswith("you ") or ", you " in line, line)


def test_deviation_markers():
    """A primary far above its mean reads 'more than is usual'; far below reads 'quieter'.

    BAND 0 TAKES DIFFERENT WORDS, and this test used to pin the wrong ones for it. Band-0 phrases
    are ABSENCE descriptions by construction (the reflexive tables depend on that), so an
    intensity marker on one asserts a stronger nothing: a placid character whose RAGE was rising
    rendered "you let slights pass without marking them, more than is usual for you" while the
    value CLIMBED, and a warm character gone cold rendered "no one here has a claim on you...,
    quieter than your usual". An absence SLIPS, or it is out of character; those are the two
    things it can do. Both branches are pinned below — the old test exercised only the band-0 one
    and called it the general case, which is how the wrong wording stayed green.
    """
    print("\n[3] DEVIATION MARKERS")
    t = temp(0.5)
    up = direct_affect(dict(flat(0.5), FEAR=0.9), t)
    down0 = direct_affect(dict(flat(0.5), CARE=0.1), t)           # CARE 0.1 vs mean 0.5 -> band 0
    down1 = direct_affect(dict(flat(0.5), CARE=0.3), temp(0.6))   # CARE 0.3 vs mean 0.6 -> band 1
    check("rising-marker", "more than is usual" in up, up)
    check("settling-marker-band-0", "which is not like you" in down0, down0)
    check("settling-marker-above-band-0", "quieter than your usual" in down1, down1)
    check("band-0-never-takes-an-intensity-marker",
          "quieter than your usual" not in down0 and "more than is usual" not in down0, down0)
    rising0 = direct_affect(dict(flat(0.5), RAGE=0.24),
                            dict(temp(0.5), RAGE={"mean": 0.05, "variability": 0.1}))
    check("a-rising-absence-slips-rather-than-intensifies",
          "though that is beginning to slip" in rising0 and "more than is usual" not in rising0,
          rising0)
    # at-rest at an ANXIOUS baseline must NOT read as a spike (the anxious-baseline rule)
    anxious = {p: {"mean": 0.5, "variability": 0.1} for p in PRIMARIES}
    anxious["FEAR"] = {"mean": 0.72, "variability": 0.1}
    at_rest = direct_affect(dict(flat(0.5), FEAR=0.72), anxious)
    check("anxious-baseline-not-a-spike", "more than is usual" not in at_rest, at_rest)


def test_monotone_presence():
    """A primary at PRESENT level or above must always reach the actor.

    Regression for the non-monotonic notability gate. Measured at temperament mean 0.65, CARE 0.30
    and 0.45 surfaced while 0.54 emitted the empty-line default: the actor was told LESS was
    happening at higher care. The old gate was `band >= 2 or |dev| > _DEV_THRESH`, leaving a hole
    for any value both mid-band and near the character's own resting mean.

    Silence IS legitimate in the quiet band near your own mean -- a character whose resting care is
    low needs no direction about being ordinarily cold. So the invariant is not "once surfaced,
    always surfaced" (that fails correctly at a low mean, where a notable ABSENCE surfaces first and
    then relaxes to rest). The invariant is: band >= 1 always reaches the actor.
    """
    print("\n[4] MONOTONE PRESENCE (present-or-above always reaches the actor)")
    from src.engine.direction import _BANDS, _band
    missed = []
    for mean in (0.05, 0.20, 0.35, 0.50, 0.65, 0.80, 0.95):
        t = {p: {"mean": 0.20} for p in PRIMARIES}
        t["CARE"] = {"mean": mean}
        for i in range(101):
            v = i / 100.0
            if _band(v, _BANDS) < 1:
                continue
            line = direct_affect(dict(flat(0.20), CARE=v), t)
            if "act as you ordinarily would" in line:
                missed.append((mean, v))
    check("present-or-above-always-surfaces", not missed, "silent at (mean, CARE): %s" % missed[:4])
    # the specific measured case that motivated the fix
    t = {p: {"mean": 0.20} for p in PRIMARIES}
    t["CARE"] = {"mean": 0.65}
    seq = [direct_affect(dict(flat(0.20), CARE=v), t) for v in (0.30, 0.45, 0.54, 0.60)]
    check("care-054-not-silent-at-mean-065", "act as you ordinarily would" not in seq[2], seq[2])
    check("care-band-rises-at-060", seq[3] != seq[2], seq[3])
    bands = [_band(i / 100.0, _BANDS) for i in range(101)]
    check("band-index-non-decreasing", all(b <= c for b, c in zip(bands, bands[1:])))


def test_separator_not_in_phrases():
    """No phrase may contain the clause separator "; " -- it would break any consumer that splits."""
    print("\n[5] SEPARATOR HYGIENE")
    from src.engine.direction import _PHRASES, _COND, _EDGE_PHRASES, _SURENESS
    bad = []
    for table in (_PHRASES, _EDGE_PHRASES):
        for k, tup in table.items():
            bad += ["%s:%s" % (k, ph) for ph in tup if ";" in ph]
    bad += [ph for _, ph in _COND if ";" in ph]
    bad += [ph for _, ph in _SURENESS if ";" in ph]
    check("separator-not-in-phrases", not bad, "contain ';': %s" % bad[:3])


def test_condition_bands():
    print("\n[4] CONDITION BANDS")
    check("drained", "shortest path" in direct_condition({"energy": 0.1, "allostatic_load": 0.9}))
    check("worn", "none of the extra" in direct_condition({"energy": 0.5, "allostatic_load": 0.5}))
    check("rested", "reserve to spend" in direct_condition({"energy": 0.95, "allostatic_load": 0.05}))


def test_edges_and_sureness():
    print("\n[5] EDGES + SURENESS")
    e = direct_edge({"trust": 0.9, "affinity": 0.6, "respect": 0.3, "debt": 0.05})
    # trust 0.9 -> band 3, affinity 0.6 -> band 2, respect 0.3 -> band 1, debt 0.05 -> band 0
    check("edge-renders-all-axes", all(s in e for s in ("against your own read", "make time for them",
                                                       "hear them out", "owe them nothing")), e)
    check("sureness-low", sureness(0.2) == "you would not stake anything on it")
    check("sureness-high", sureness(0.95) == "you do not entertain the alternative")


def test_fail_loud():
    print("\n[6] FAIL LOUD")
    for bad_call in (lambda: direct_affect({"FEAR": 0.5}, temp()),          # missing primaries
                     lambda: direct_affect(dict(flat(0.5), FEAR=1.5), temp()),
                     lambda: direct_condition({"energy": "high"}),
                     lambda: direct_edge({"trust": 2.0}),
                     lambda: sureness(-0.1)):
        try:
            bad_call()
            check("fail-loud", False, "malformed input accepted")
            return
        except ValueError:
            pass
    check("fail-loud-all-five", True)




# Floating intensifiers: words that state a BAND as a quantity instead of enacting it. THE LAW
# (design.md's compute/generate split) bans numbers reaching the prompt, and these are numbers
# wearing words — three cells carried them until 2026-08-23 ("show a little", "a little more
# distance", "one small joke"). ANCHORED comparatives are NOT here and are deliberately allowed:
# "no more of it than you must" and "more than is usual FOR YOU" measure against a standard the
# actor can act on. The banned thing is the comparison to nothing.
_SCALE_WORDS = ("a little", "a bit", "slightly", "somewhat", "very", "quite", "rather",
                "one small", "a touch", "mildly", "extremely", "moderately", "a lot")
# WORD boundaries, not substrings. The first draft of this check used "very " and fired on
# "e[very] question" in a phrase that is measured-good — a check that flags correct prose is worse
# than no check, because the fix it invites is to damage the prose.
_SCALE_RE = re.compile(r"\b(%s)\b" % "|".join(w.replace(" ", r"\s+") for w in _SCALE_WORDS))


def test_no_floating_intensifiers():
    """No phrase may state its band as a quantity."""
    print("\n")
    print("[9] NO FLOATING INTENSIFIERS — a band is acted, never measured")
    tables = {"_PHRASES": _PHRASES, "_REFLEXIVE_PHRASES": _REFLEXIVE_PHRASES,
              "_EDGE_PHRASES": _EDGE_PHRASES, "_THEIR_VIEW_PHRASES": _THEIR_VIEW_PHRASES}
    bad = []
    for tname, table in tables.items():
        for key, bands in table.items():
            for i, phrase in enumerate(bands):
                if not phrase:
                    continue
                m = _SCALE_RE.search(phrase.lower())
                if m:
                    bad.append("%s[%s][%d] carries %r: %s" % (tname, key, i, m.group(0), phrase))
    check("no-scale-word-states-a-band", not bad, " | ".join(bad))
    check("the-check-can-fire",                       # the exact string this pass removed
          bool(_SCALE_RE.search("you keep a little more distance than the moment needs")))
    check("and-does-not-fire-on-a-word-that-merely-contains-one",
          not _SCALE_RE.search("you carry it like the answer to every question"))


def test_every_phrase_is_a_direction():
    """Every cell in every table, not just FEAR's four.

    test_monotone_bands walks ONLY the FEAR ladder for the is-a-direction property, so PANIC_GRIEF
    band 1 sat at "you ARE slower to answer" — a report of a property, the frame prompt.py records
    fixing for the affect halves — and stayed green because nothing looked at it.
    """
    print("\n")
    print("[10] EVERY PHRASE IS A DIRECTION — all tables, not one ladder")
    bad, seen = [], 0
    for tname, table in (("_PHRASES", _PHRASES), ("_REFLEXIVE_PHRASES", _REFLEXIVE_PHRASES),
                         ("_EDGE_PHRASES", _EDGE_PHRASES)):
        for key, bands in table.items():
            for i, phrase in enumerate(bands):
                if not phrase:
                    continue
                seen += 1
                if not re.search(r"\byou\b", phrase):
                    bad.append("%s[%s][%d]: %s" % (tname, key, i, phrase))
    print("       %d phrases checked" % seen)
    check("every-phrase-directs-an-act", not bad, " | ".join(bad))

    # NOT MECHANIZED, TWO CLASSES, and saying so is the point.
    #
    # (1) REPORT-VS-DIRECTION. A draft of this test banned "you are" outright, because that frame
    # is what made _PHRASES["PANIC_GRIEF"][1] a report ("you ARE slower to answer"). It fired on
    # _EDGE_PHRASES["affinity"][1], "you are civil, and you do not seek them out" — which is a
    # MANNER the actor enacts, not a property being described. No pattern separates those; the
    # difference is whether the complement is something you do or something you merely are.
    #
    # (2) SEMANTIC TWINS. The worst defect this pass fixed was
    # _PHRASES["PANIC_GRIEF"][2] rendering one period from _COND band 2 — "you do the least the
    # moment requires and no more" beside "you do what is asked and none of the extra". Those are
    # SEMANTIC twins with a two-word lexical overlap, so no span or n-gram check catches them.
    # Only a reader can. basis_probe.py --compare is that reader; this test is not.
    dup = [x for x in _PHRASES.values() for x in x if x in [c[1] for c in _COND]]
    check("no-phrase-is-LITERALLY-a-condition-line", not dup, str(dup))



# A PERSON-deictic. "them" whose referent is a THING (slights, objects) is not one, which is why
# this is a word list and a human-reviewed exclusion rather than a bare regex — RAGE band 0's "you
# let slights pass without marking them" trips the pattern and is correct as written.
_PERSON_DEICTIC = re.compile(r"\b(them|they|their|theirs)\b", re.I)
_REFERENT_IS_A_THING = {
    ("RAGE", 0),        # "...without marking them" -> the slights
    ("DISGUST", 0),     # "...do not find them beneath you" -> things taken as they come
}


def test_no_unbound_phrase_hands_over_a_deictic():
    """The rule `_UNBOUND_PHRASES` exists for, applied to every primitive instead of one.

    `direction.py`'s own comment states it: an unbound primitive renders its object phrase unless
    that phrase carries a deictic, because an actor handed "you act for THEM" with nothing bound
    "will attach it to whoever is in the room and INVENT A DESIRE THE NUMBERS NEVER AIMED, and with
    it a relationship the ledger never earned. That is canon created by a rendering accident."

    It was written for LUST when targets landed and never applied to the other seven. Scanned
    2026-08-24: CARE bands 2-3 and DISGUST band 2 were handing over a person-deictic with no
    unbound cover. RAGE was not — its only hit is band 0, referring to slights — which is how this
    scan CHANGED the plan: a RAGE entry had been scoped and is not warranted.
    """
    print("%s[11] UNBOUND DEICTICS — nothing invents a person the numbers never aimed" % "\n")
    naked = []
    for primary, bands in _PHRASES.items():
        cover = _UNBOUND_PHRASES.get(primary)
        for band in range(1, len(bands)):                 # band 0 never reaches the unbound branch
            phrase = bands[band]
            if not phrase or not _PERSON_DEICTIC.search(phrase):
                continue
            if (primary, band) in _REFERENT_IS_A_THING:
                continue
            covered = (isinstance(cover, tuple) and cover[band] is not None) or                       (cover is not None and not isinstance(cover, tuple))
            if not covered:
                naked.append("%s band %d: %s" % (primary, band, phrase))
    check("every-deictic-band-has-unbound-cover", not naked, " | ".join(naked))

    # and the cover itself must not reintroduce one
    bad = []
    for primary, cover in _UNBOUND_PHRASES.items():
        for phrase in (cover if isinstance(cover, tuple) else (cover,)):
            if phrase and _PERSON_DEICTIC.search(phrase):
                bad.append("%s: %s" % (primary, phrase))
    check("the-cover-is-itself-objectless", not bad, " | ".join(bad))

    check("RAGE-is-deliberately-uncovered", "RAGE" not in _UNBOUND_PHRASES,
          "a RAGE entry was added — the scan says its bands carry no person-deictic")


def test_binding_a_primitive_is_unchanged_by_the_cover():
    """The cover must fire ONLY when nothing is bound, or it rewrites measured renders."""
    print("%s[12] THE COVER IS FOR THE UNBOUND CASE ONLY" % "\n")
    for primary in ("CARE", "DISGUST"):
        for band in (2, 3):
            bound = _phrase_for(primary, band, {primary: "other"}, "me")
            check("%s-b%d-bound-is-the-object-phrase" % (primary.lower(), band),
                  bound == _PHRASES[primary][band], bound)
    check("no-target-map-at-all-is-untouched",
          _phrase_for("CARE", 3, None, "me") == _PHRASES["CARE"][3])
    check("and-the-unbound-case-does-differ",
          _phrase_for("CARE", 3, {}, "me") != _PHRASES["CARE"][3])
    check("lusts-single-string-form-still-resolves",
          _phrase_for("LUST", 2, {}, "me") == _UNBOUND_PHRASES["LUST"])

def main():
    print("test_direction.py — gate 5 backstage guardrail\n")
    for t in (test_no_digits_ever, test_monotone_bands, test_deviation_markers,
              test_monotone_presence, test_separator_not_in_phrases, test_condition_bands, test_edges_and_sureness,
              test_no_floating_intensifiers, test_every_phrase_is_a_direction,
              test_no_unbound_phrase_hands_over_a_deictic,
              test_binding_a_primitive_is_unchanged_by_the_cover,
              test_fail_loud):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
