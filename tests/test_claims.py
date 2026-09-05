"""test_claims.py — the structural collapse detector, exercised on the Clifford case.

Two properties carry this suite, and both were defects in the first draft:
  * an utterance carries as many facts as it carries, not one
  * a tier is folded from append-only resolutions, never stored and flipped
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.claims import (AUTHORED, BINDING, ESTABLISHED, FICTION,  # noqa: E402
                               SUPERPOSED, ClaimError, about, contradictions,
                               extracts_of, live, normalise, tested, tier_of)


def _said(uid, speaker, text, *facts):
    """An utterance and the fact(s) it asserts. `facts` are (subject, predicate, object)."""
    return {"id": uid, "speaker": speaker, "text": text,
            "extracts": [{"subject": s, "predicate": p, "object": o} for s, p, o in facts]}


MAREN = _said("u1", "maren",
              "we held the festival at midwinter, and my mother led the procession",
              ("clifford", "festival season", "midwinter"),
              ("clifford", "procession leader", "maren's mother"))
REN = _said("u2", "ren", "Clifford keeps its festival after the harvest",
            ("clifford", "festival season", "harvest"))


# ---- THE DEFECT THAT PROMPTED THE REWRITE ----

def test_ONE_utterance_carries_AS_MANY_facts_as_it_carries():
    """The first draft stored a single triple per claim and silently dropped the rest."""
    got = extracts_of(MAREN)
    assert len(got) == 2, "a two-fact sentence must yield two extracts, got %r" % (got,)
    assert ("clifford", "festival-season", "midwinter") in got
    assert ("clifford", "procession-leader", "maren-s-mother") in got, (
        "the apostrophe is stripped, consistently on both sides of any comparison")


def test_an_utterance_asserting_ONE_fact_needs_no_extracts_list():
    """An atom without particles is a complete atom."""
    flat = {"id": "u9", "speaker": "ren", "text": "Clifford is on the river",
            "subject": "clifford", "predicate": "sits on", "object": "the river"}
    assert extracts_of(flat) == [("clifford", "sits-on", "river")]


def test_an_extract_missing_subject_or_predicate_FAILS_LOUD():
    for broken in ([{"predicate": "p", "object": "o"}], [{"subject": " ", "predicate": "p"}]):
        try:
            extracts_of({"id": "u", "extracts": broken})
        except ClaimError as e:
            assert "missing" in str(e)
        else:
            raise AssertionError("an uncomparable extract must not pass: %r" % broken)


# ---- THE OTHER DEFECT: tier was a stored field that would have needed an UPDATE ----

def test_tier_defaults_to_superposed_because_speaking_binds_nothing():
    assert tier_of(MAREN) == SUPERPOSED
    assert SUPERPOSED not in BINDING


def test_tier_is_FOLDED_from_append_only_resolutions_not_read_from_a_field():
    """Hard rule 2 forbids UPDATE; schema v9 enforces it with triggers. A collapse appends."""
    resolutions = [{"id": "u1", "verdict": FICTION, "turn": 40}]
    assert tier_of(MAREN, resolutions) == FICTION
    assert MAREN.get("tier") is None, "the utterance must carry no mutable tier field"


def test_the_LAST_resolution_wins_so_the_world_may_change_its_mind():
    resolutions = [{"id": "u1", "verdict": FICTION, "turn": 40},
                   {"id": "u1", "verdict": ESTABLISHED, "turn": 90}]
    assert tier_of(MAREN, resolutions) == ESTABLISHED


def test_a_resolution_for_another_utterance_does_not_touch_this_one():
    assert tier_of(MAREN, [{"id": "u2", "verdict": FICTION}]) == SUPERPOSED


def test_an_invented_tier_or_verdict_is_refused_by_name():
    try:
        tier_of({"id": "u", "subject": "s", "predicate": "p", "tier": "probably"})
    except ClaimError as e:
        assert "probably" in str(e) and e.code == "CLAIM_TIER_UNKNOWN", e.code
    else:
        raise AssertionError("an invented tier must not pass")
    try:
        tier_of(MAREN, [{"id": "u1", "verdict": "maybe"}])
    except ClaimError as e:
        assert "maybe" in str(e) and e.code == "CLAIM_VERDICT_UNKNOWN", e.code
    else:
        raise AssertionError("an invented verdict must not pass")


def test_EVERY_refusal_in_this_module_carries_a_REGISTERED_code():
    """The module answered an operator two ways: three coded refusals in `record` and five in prose,
    added the same morning. A code is the grep handle a runbook cites; a sentence is not.

    The scan READS THE FILE rather than trusting this list to be complete — a hand-kept list of
    raise sites is the seventh duplicate CLAUDE.md tabulates, and it would go stale the first time
    someone adds a refusal."""
    import re
    from src.engine import codes
    src = io.open(os.path.join(REPO, "src", "engine", "claims.py"), encoding="utf-8").read()
    uncoded = []
    for m in re.finditer(r"raise (\w*Error)\(\s*", src):
        if not re.match(r'"[A-Z][A-Z0-9_]{3,}"\s*,', src[m.end():m.end() + 90]):
            uncoded.append(src[:m.start()].count(chr(10)) + 1)
    assert not uncoded, "claims.py raises without a code at line(s) %s" % uncoded

    raised = set(re.findall(r'raise \w*Error\(\s*"([A-Z][A-Z0-9_]+)"', src))
    assert raised, "the scan found no coded raises at all, which means it is not reading the module"
    unregistered = sorted(c for c in raised if not codes.is_registered(c))
    assert not unregistered, "claims.py raises unregistered code(s) %s" % unregistered


def test_the_refusals_a_KEEPER_meets_fire_with_their_own_codes():
    """One case per code, so the registry's other half holds: a code listed and never raised is the
    same lie as a code raised and never listed."""
    from src.engine.claims import record, resolve, extracts_of
    cases = [
        ("CLAIM_UTTERANCE_NOT_AN_OBJECT", lambda: extracts_of("not an utterance")),
        ("CLAIM_EXTRACT_INCOMPLETE",
         lambda: extracts_of({"id": "u", "extracts": [{"subject": "clifford"}]})),
        ("CLAIM_TIER_UNKNOWN", lambda: record(None, "r1", 0, "maren", "x", tier="probably")),
        ("CLAIM_SPEAKER_EMPTY", lambda: record(None, "r1", 0, "", "x")),
        ("CLAIM_SAID_EMPTY", lambda: record(None, "r1", 0, "maren", "")),
    ]
    for want, call in cases:
        try:
            call()
        except ClaimError as e:
            assert e.code == want, "expected %s, got %r" % (want, e.code)
        else:
            raise AssertionError("%s: the malformed input was ACCEPTED" % want)


def test_the_WRITER_refuses_an_unattributed_or_empty_utterance():
    """One writer, one wall. `scripts/keeper.py` guarded the verbatim text and this function — the
    OTHER way in — did not, so a module whose doctrine is "the extract is an index into what was
    said, never a substitute for it" would happily store an utterance that said nothing.

    No connection is needed: both refusals fire before the INSERT, which is the point of putting
    them here rather than relying on the schema to catch it downstream."""
    from src.engine.claims import record
    for speaker, said, code in (("", "the levy was doubled", "CLAIM_SPEAKER_EMPTY"),
                                ("   ", "the levy was doubled", "CLAIM_SPEAKER_EMPTY"),
                                ("maren", "", "CLAIM_SAID_EMPTY"),
                                ("maren", "   ", "CLAIM_SAID_EMPTY")):
        try:
            record(None, "r1", 1, speaker, said)
        except ClaimError as e:
            assert e.code == code, "%r/%r refused with %r, expected %r" % (speaker, said, e.code, code)
        else:
            raise AssertionError("record accepted speaker=%r said=%r" % (speaker, said))


# ---- THE CLIFFORD CASE ----

def test_two_actors_disagreeing_on_one_fact_is_DETECTED_on_that_key_alone():
    found = contradictions([MAREN, REN])
    assert len(found) == 1, "they disagree on the festival only, not on the procession"
    a, b, k = found[0]
    assert {a["speaker"], b["speaker"]} == {"maren", "ren"}
    assert k == ("clifford", "festival-season")


def test_what_is_returned_is_the_PARENT_utterance_so_the_keeper_reads_the_SENTENCE():
    """The extract is never the answer. 'when I was a girl' survives only on the utterance."""
    a, _, _ = contradictions([MAREN, REN])[0]
    assert a["text"] == MAREN["text"], "the keeper was handed a flattened fact, not what was said"
    assert "when I was a girl" not in str(extracts_of(MAREN)), "and the extract does drop it"


def test_the_UNCONTESTED_fact_in_a_contested_utterance_raises_nothing():
    """Maren's procession claim stands even though her festival claim is in dispute."""
    keys = [k for _, _, k in contradictions([MAREN, REN])]
    assert ("clifford", "procession-leader") not in keys


def test_agreeing_actors_produce_NO_alert():
    echo = _said("u3", "ren", "Clifford's Festival is at Midwinter",
                 ("Clifford", "Festival Season", "Midwinter"))
    assert contradictions([MAREN, echo]) == [], "casing must not manufacture a conflict"


def test_the_same_fact_about_DIFFERENT_towns_does_not_collide():
    ashby = _said("u4", "ren", "Ashby holds its festival at harvest",
                  ("ashby", "festival season", "harvest"))
    assert contradictions([MAREN, ashby]) == []


def test_a_claim_contradicting_an_AUTHORED_fact_is_detected():
    """Trigger 1 in docs/keeper-of-truth.md — a T2 claim against a binding fact."""
    bible = dict(_said("u5", "author", "The guard of Clifford is mixed",
                       ("clifford", "guard composition", "mixed")), tier=AUTHORED)
    maren = _said("u6", "maren", "the guards there were all women",
                  ("clifford", "guard composition", "women"))
    found = contradictions([bible, maren])
    assert len(found) == 1
    assert AUTHORED in (tier_of(found[0][0]), tier_of(found[0][1]))


def test_two_BINDING_facts_that_disagree_are_NOT_silently_tolerated():
    """The bible contradicting itself, or a bad collapse. Silence would hide the worst case."""
    a = dict(_said("u7", "author", "midwinter", ("clifford", "festival season", "midwinter")),
             tier=AUTHORED)
    b = dict(_said("u8", "keeper", "harvest", ("clifford", "festival season", "harvest")),
             tier=ESTABLISHED)
    assert len(contradictions([a, b])) == 1


def test_FICTION_stops_contesting_but_is_never_deleted():
    """Fiction is a first-class outcome. Maren was wrong; that is characterisation."""
    resolutions = [{"id": "u1", "verdict": FICTION, "turn": 40}]
    assert contradictions([MAREN, REN], resolutions) == [], "a declined claim must stop alerting"
    assert MAREN["text"], "and it must still be there"
    assert MAREN not in live([MAREN, REN], resolutions)


def test_tested_answers_the_collapse_question_for_ONE_utterance():
    quiet = [MAREN, _said("u9", "ren", "the guards were women",
                          ("clifford", "guard composition", "women"))]
    assert tested(quiet, MAREN) is False, "nothing contradicts her yet; she stays superposed"
    assert tested(quiet + [REN], MAREN) is True


# ---- retrieval ----

def test_about_returns_EVERY_utterance_on_a_subject_not_a_top_k():
    others = [_said("u%d" % i, "ren", "t", ("clifford", "p%d" % i, "o")) for i in range(5)]
    ashby = _said("uA", "ren", "t", ("ashby", "festival season", "harvest"))
    got = about([MAREN] + others + [ashby], "Clifford")
    assert len(got) == 6, "casing or subject drift must not hide an utterance from the keeper"
    assert ashby not in got


def test_about_finds_an_utterance_by_ANY_of_its_extracts():
    """Maren's sentence is about Clifford AND about her mother; both must retrieve it."""
    mother = about([MAREN], "clifford")
    assert MAREN in mother


def test_about_excludes_what_was_declined():
    assert about([MAREN], "clifford", [{"id": "u1", "verdict": FICTION}]) == []


# ---- determinism ----

def test_the_detector_is_pure_and_order_stable():
    third = _said("uX", "joss", "spring", ("clifford", "festival season", "spring"))
    claims = [MAREN, REN, third]
    before = [dict(c) for c in claims]
    first, second = contradictions(claims), contradictions(claims)
    assert len(first) == 3, "three mutually exclusive objects is three pairs"
    assert [(id(a), id(b), k) for a, b, k in first] == [(id(a), id(b), k) for a, b, k in second]
    assert claims == before, "the detector mutated its input"


def test_an_empty_or_missing_set_is_quiet():
    assert contradictions([]) == [] and contradictions(None) == []
    assert about(None, "clifford") == [] and live(None) == []


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("  PASS  %s" % name)
            except Exception as e:                       # noqa: BLE001 — a harness reports, never raises
                fails += 1
                print("  FAIL  %s: %s" % (name, e))
    print("%s" % ("ALL PASS" if not fails else "%d FAILED" % fails))
    sys.exit(1 if fails else 0)
