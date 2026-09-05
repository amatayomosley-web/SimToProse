#!/usr/bin/env python3
"""test_consolidation.py — Gate 4 proof for consolidation validation.

Script-style (plain asserts, main(), exit code) matching tests/test_ledger.py style.
Mutation-falsifying assertions with concrete values.

Contracts verified:
  consolidation-loop.md — pipeline (schema-conformance / containment / capability),
                          confidence composition (open-q 2 RESOLVED), escalation.
  record-contract.md    — event catalog completeness.
  ledger.py _project    — all fold types have CATALOG rows.
  coherence_probe.py    — all 25 EVENTS stubs validate ok=True with zero escalations.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.consolidation import (   # noqa: E402
    validate_tags,
    CATALOG,
    THETA_CONF,
    SOFT_FAIL_CAP_FACTOR,
)

# ---- Minimal fixture helpers -----------------------------------------------

def _percept(ref, attributes, recognized_as=None):
    """Minimal Percept dict (gate.py _make_percept schema)."""
    p = {"ref": ref, "channel": "event", "fidelity": 1.0,
         "attributes": list(attributes), "must_surface": False}
    if recognized_as is not None:
        p["recognized_as"] = recognized_as
    return p


def _clean(tag_type="mundane", dims=None, durability="transient",
           target=None, confidence=None):
    """Build a clean (schema-valid) tag dict."""
    t = {"type": tag_type,
         "dimensions": dict(dims) if dims else {},
         "durability": durability}
    if target is not None:
        t["target"] = target
    if confidence is not None:
        t["confidence"] = confidence
    return t


# ---- Maren's baseline skills (maren-healer.json §baseline.skills) ----------
MAREN_SKILLS = {
    "healing_lore": 0.85, "insight": 0.75, "perception": 0.78,
    "persuasion": 0.55,   "streetwise": 0.40, "combat": 0.15,
}

BRYN_PERCEPTS = [
    _percept("evt.child_fever", ["fever", "child", "threat"], recognized_as="Bryn"),
]

EMPTY_PERCEPTS = []


# ==== 1. Schema-conformance — hard checks (ok=False) ====


def _codes(r):
    """The codes a verdict carries — what an assertion should name, instead of prose."""
    return [f.get("code") for f in r["flags"] if isinstance(f, dict)]


def _of(r, code):
    """Every flag carrying `code`."""
    return [f for f in r["flags"] if isinstance(f, dict) and f.get("code") == code]


def _has(r, code):
    return bool(_of(r, code))


def test_schema_unknown_type():
    """Unknown type -> ok=False. consolidation-loop.md Principle 3 (typed schema)."""
    r = validate_tags({"type": "DOES_NOT_EXIST", "dimensions": {}, "durability": "transient"},
                      [], {})
    assert r["ok"] is False, "unknown type must set ok=False"
    assert _has(r, "TAG_TYPE_UNKNOWN"), \
        "expected 'unknown type' flag, got: %s" % r["flags"]


def test_schema_bad_dim_value():
    """Dimension value 1.5 outside [0,1] -> ok=False."""
    r = validate_tags(_clean("mundane", dims={"mastery": 1.5}), [], MAREN_SKILLS)
    assert r["ok"] is False, "out-of-range dim must set ok=False"
    assert _has(r, "TAG_DIMENSION_VALUE_RANGE"), \
        "expected range flag, got: %s" % r["flags"]


def test_schema_bad_durability():
    """Durability 'ephemeral' (not in {transient, durable}) -> ok=False."""
    r = validate_tags({"type": "mundane", "dimensions": {}, "durability": "ephemeral"},
                      [], MAREN_SKILLS)
    assert r["ok"] is False, "bad durability must set ok=False"
    assert _has(r, "TAG_DURABILITY_INVALID"), \
        "expected durability flag, got: %s" % r["flags"]


def test_schema_bad_confidence():
    """Confidence 1.5 outside [0,1] -> ok=False."""
    r = validate_tags(_clean("mundane", confidence=1.5), [], MAREN_SKILLS)
    assert r["ok"] is False, "confidence > 1 must set ok=False"
    assert _has(r, "TAG_CONFIDENCE_RANGE"), \
        "expected confidence flag, got: %s" % r["flags"]


# ==== 2. Containment — soft flags ====

def test_containment_target_perceived():
    """Target 'bryn' against PerceptSet that perceived Bryn -> NO containment flag."""
    r = validate_tags(_clean("care", target="bryn"), BRYN_PERCEPTS, MAREN_SKILLS)
    assert r["ok"] is True, "valid care tag with perceived target must be ok"
    containment_flags = _of(r, "TAG_TARGET_NOT_PERCEIVED")
    assert containment_flags == [], \
        "no containment flag expected for perceived target, got: %s" % containment_flags


def test_containment_target_not_perceived():
    """Target 'the king' (never in PerceptSet) -> containment flag + confidence capped."""
    r = validate_tags(_clean("threaten", target="the king", confidence=0.8),
                      EMPTY_PERCEPTS, {"combat": 0.50})
    containment_flags = _of(r, "TAG_TARGET_NOT_PERCEIVED")
    assert len(containment_flags) >= 1, \
        "expected containment flag for unperceived target, got: %s" % r["flags"]
    # confidence must be capped below self-rated 0.8
    assert r["confidence"] < 0.8, \
        "confidence should be capped below 0.8 on containment miss, got %.4f" % r["confidence"]
    # with one soft-fail and self-rated 0.8: 0.8 * 0.65 = 0.52 >= THETA_CONF (0.45)
    # so escalate depends on whether that one miss is enough
    # Deterministic: 0.52 >= 0.45 -> escalate=False with one flag at 0.8 base
    # but THETA_CONF = 0.45, so: 0.52 >= 0.45 -> no escalate (just one flag)
    # This tests the confidence cap happened without over-asserting on escalation
    assert abs(r["confidence"] - 0.8 * SOFT_FAIL_CAP_FACTOR) < 1e-9, \
        "expected %.6f, got %.6f" % (0.8 * SOFT_FAIL_CAP_FACTOR, r["confidence"])


def test_containment_target_not_perceived_escalates():
    """Low self-rated + containment miss -> composite < THETA_CONF -> escalate=True."""
    # self_rated=0.5 (default), one containment miss: 0.5 * 0.65 = 0.325 < 0.45
    r = validate_tags(_clean("mundane", target="the king"), EMPTY_PERCEPTS, MAREN_SKILLS)
    assert r["escalate"] is True, \
        "unperceived target with default confidence must escalate, confidence=%.4f" % r["confidence"]


# ==== 3. Dimension-type mismatch (soft flag) ====

def test_dim_type_mismatch_mundane_threat():
    """'mundane' claiming {threat: 0.9} -> soft flag (mundane appraisal_map excludes threat
    and value >= _MISMATCH_THRESHOLD 0.5)."""
    r = validate_tags(_clean("mundane", dims={"threat": 0.9}), [], MAREN_SKILLS)
    assert r["ok"] is True, "dim mismatch is a soft flag, not a hard failure"
    mismatch_flags = _of(r, "TAG_DIMENSION_NOT_IN_APPRAISAL_MAP")
    assert len(mismatch_flags) >= 1, \
        "expected appraisal_map mismatch flag for threat=0.9, got: %s" % r["flags"]
    assert "threat" in mismatch_flags[0]["detail"], \
        "flag should name 'threat', got: %s" % mismatch_flags[0]


def test_dim_type_mismatch_mundane_valid_dims():
    """'mundane' claiming {mastery: 0.3, relief: 0.2} (both in appraisal_map) -> no mismatch."""
    r = validate_tags(_clean("mundane", dims={"mastery": 0.3, "relief": 0.2}),
                      [], MAREN_SKILLS)
    mismatch_flags = _of(r, "TAG_DIMENSION_NOT_IN_APPRAISAL_MAP")
    assert mismatch_flags == [], "valid dims must not trigger mismatch, got: %s" % r["flags"]


# ==== 4. Capability checks ====

def test_capability_harm_maren_fails():
    """'harm' tag with Maren's combat 0.15 < required 0.30 -> capability flag."""
    r = validate_tags(_clean("harm"), [], MAREN_SKILLS)
    cap_flags = _of(r, "TAG_CAPABILITY_BELOW_REQ")
    assert len(cap_flags) >= 1, \
        "expected capability flag for Maren on 'harm', got: %s" % r["flags"]
    assert "combat" in cap_flags[0]["detail"], \
        "capability flag should name 'combat', got: %s" % cap_flags[0]


def test_capability_harm_high_combat_passes():
    """'harm' tag with combat 0.90 (>= 0.30) -> no capability flag."""
    high_combat_skills = dict(MAREN_SKILLS, combat=0.90)
    r = validate_tags(_clean("harm"), [], high_combat_skills)
    cap_flags = _of(r, "TAG_CAPABILITY_BELOW_REQ")
    assert cap_flags == [], \
        "no capability flag expected for high-combat actor, got: %s" % cap_flags


def test_capability_no_req_types():
    """Types with no capability_req (aid, bond, reveal) -> never capability-flag."""
    for t in ("aid", "bond", "reveal"):
        # Use a zero-skill actor to ensure we would catch any cap req
        r = validate_tags(_clean(t), [], {})
        cap_flags = _of(r, "TAG_CAPABILITY_BELOW_REQ")
        assert cap_flags == [], "type %r should have no capability req, got: %s" % (t, cap_flags)


# ==== 5. Confidence composition ====

def test_confidence_composition_one_soft_fail():
    """self-rated 0.9 with one soft-fail -> composite strictly < 0.9."""
    # Use a dim-mismatch to produce exactly one soft-fail.
    # threat=0.7 >= _MISMATCH_THRESHOLD (0.5) -> mismatch fires.
    r = validate_tags(_clean("mundane", dims={"threat": 0.7}, confidence=0.9),
                      [], MAREN_SKILLS)
    assert r["ok"] is True, "dim mismatch does not set ok=False"
    assert len(_of(r, "TAG_DIMENSION_NOT_IN_APPRAISAL_MAP")) == 1, \
        "expected exactly one mismatch flag"
    expected = 0.9 * SOFT_FAIL_CAP_FACTOR
    assert abs(r["confidence"] - expected) < 1e-9, \
        "expected %.6f, got %.6f" % (expected, r["confidence"])
    assert r["confidence"] < 0.9, "composite must be strictly < self-rated on one soft-fail"


def test_confidence_composition_clean_tag():
    """Clean tag (no soft-fails, self-rated 0.8) -> composite == self-rated."""
    r = validate_tags(_clean("mundane", dims={"mastery": 0.3}, confidence=0.8),
                      [], MAREN_SKILLS)
    assert r["flags"] == [], "clean tag must produce no flags, got: %s" % r["flags"]
    assert abs(r["confidence"] - 0.8) < 1e-9, \
        "clean tag: composite must equal self-rated, got %.6f" % r["confidence"]


def test_confidence_default_no_flags():
    """No confidence key in tag -> default 0.5; clean tag -> composite == 0.5."""
    r = validate_tags(_clean("mundane"), [], MAREN_SKILLS)
    assert r["ok"] is True
    assert abs(r["confidence"] - 0.5) < 1e-9, \
        "default confidence must be 0.5, got %.6f" % r["confidence"]


# ==== 6. Escalation boundary ====

def test_escalation_below_theta():
    """Composite just below THETA_CONF -> escalate=True."""
    # Construct a tag with confidence slightly below THETA_CONF
    just_below = THETA_CONF - 0.01
    r = validate_tags(_clean("mundane", confidence=just_below), [], MAREN_SKILLS)
    assert r["escalate"] is True, \
        "confidence %.4f < THETA_CONF %.4f must escalate" % (just_below, THETA_CONF)


def test_escalation_above_theta():
    """Composite just above THETA_CONF -> escalate=False."""
    just_above = THETA_CONF + 0.01
    r = validate_tags(_clean("mundane", confidence=just_above), [], MAREN_SKILLS)
    assert r["escalate"] is False, \
        "confidence %.4f >= THETA_CONF %.4f must not escalate" % (just_above, THETA_CONF)


def test_escalation_at_theta():
    """Composite exactly equal to THETA_CONF -> escalate=False (boundary: composite < theta)."""
    r = validate_tags(_clean("mundane", confidence=THETA_CONF), [], MAREN_SKILLS)
    assert r["escalate"] is False, \
        "confidence == THETA_CONF must NOT escalate (strict <), got escalate=%s" % r["escalate"]


# ==== 7. Catalog completeness ====

def test_affront_hosts_social_violation():
    """Gate fix (engine-fault detector's social_violation gap): the dimension now has an
    actor-taggable home. An affront carrying social_violation validates clean, where the SAME
    dims under 'threat' (the old forced mis-type) flag — the gap, closed and held by a control."""
    r = validate_tags(_clean("affront", dims={"social_violation": 0.65, "threat": 0.5, "mastery": 0.7}, confidence=0.6),
                       EMPTY_PERCEPTS, MAREN_SKILLS)
    assert r["ok"], "affront tag must be schema-valid: %s" % r
    assert not any(f.get("code") == "TAG_DIMENSION_NOT_IN_APPRAISAL_MAP" and "social_violation" in f.get("detail", "")
                for f in r["flags"] if isinstance(f, dict)), \
        "social_violation must be legitimate under affront: %s" % r["flags"]
    assert not r["escalate"], "a coherent affront must not escalate: %s" % r
    # control: the same dims under 'threat' still mismatch social_violation (the gap pre-fix)
    r2 = validate_tags(_clean("threat", dims={"social_violation": 0.65, "threat": 0.5, "mastery": 0.7}),
                       EMPTY_PERCEPTS, MAREN_SKILLS)
    assert any(f.get("code") == "TAG_DIMENSION_NOT_IN_APPRAISAL_MAP"
               and "social_violation" in f.get("detail", "")
               for f in r2["flags"] if isinstance(f, dict)), \
        "control: social_violation should still mismatch under 'threat': %s" % r2["flags"]


def test_catalog_completeness():
    """Every type emitted by probe stubs AND every ledger fold type must be in CATALOG.

    Sources:
      - coherence_probe.py EVENTS kinds: mundane, threat, care, loss
      - coherence_probe.py calibration prompt types: mundane, care, loss, threat
      - ledger.py _project etypes: move, harm, reveal, seize, destroy-asset,
                                   betray, bond, tension
      - ledger.py record_turn_skipped type: turn-skipped
      - consolidation-loop.md open-q 3 (compensating path): correction
    """
    # probe kinds (coherence_probe.py EVENTS / calibration prompt — these are the
    # types the LLM picks from in _openrouter_consolidate)
    probe_types = ["mundane", "care", "loss", "threat"]

    # ledger._project branches (ledger.py _project — each etype listed below):
    #   line ~141: "move"
    #   line ~143: "harm" (+ terminal check)
    #   line ~148: "reveal"
    #   line ~153: "seize", "destroy-asset"
    #   line ~155: "betray", "bond"
    #   line ~158: "tension"
    ledger_types = ["move", "harm", "reveal", "seize", "destroy-asset",
                    "betray", "bond", "tension"]

    # ledger.record_turn_skipped (ledger.py line ~113): type = 'turn-skipped'
    bookkeeping = ["turn-skipped"]

    # consolidation-loop.md open-q 3: correction
    loop_types = ["aid", "threaten", "correction"]

    required = set(probe_types + ledger_types + bookkeeping + loop_types)
    missing  = required - set(CATALOG.keys())
    assert not missing, "CATALOG missing required types: %s" % sorted(missing)


# ==== 8. Fail-loud on malformed inputs ====

def test_fail_loud_non_dict_tags():
    """Non-dict tags -> ValueError."""
    try:
        validate_tags("not a dict", [], {})
        assert False, "expected ValueError"
    except ValueError as e:
        assert "tags must be a dict" in str(e), "wrong message: %s" % e


def test_fail_loud_non_list_percepts():
    """Non-list percepts -> ValueError."""
    try:
        validate_tags({}, "not a list", {})
        assert False, "expected ValueError"
    except ValueError as e:
        assert "percepts must be a list" in str(e), "wrong message: %s" % e


def test_fail_loud_non_dict_skills():
    """Non-dict skills -> ValueError."""
    try:
        validate_tags({}, [], "not a dict")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "skills must be a dict" in str(e), "wrong message: %s" % e


# ==== 9. Pre-flight: all 25 EVENTS stubs validate ok=True with zero escalations ====

# Inline EVENTS from coherence_probe.py (copied here so the pre-flight is self-contained
# and does not import the probe — which has API wiring).
# Source: coherence_probe.py EVENTS list (25 entries, lines ~148-174).
_EVENTS = [
    {"text": "Morning. She walks the upland edge gathering late herbs.", "kind": "mundane", "hint": {"mastery": 0.2}},
    {"text": "A boy's scraped knee at the well — easy, cleaned and bound.", "kind": "mundane", "hint": {"care_relevant": 0.2, "mastery": 0.3}},
    {"text": "Bryn, a child, is carried in with a climbing fever.", "kind": "threat", "hint": {"threat": 0.6, "care_relevant": 0.8}},
    {"text": "She works the remedies through the night, watching the heat.", "kind": "mundane", "hint": {"mastery": 0.3, "threat": 0.2}},
    {"text": "Second night: Bryn's fever climbs higher, not lower.", "kind": "threat", "hint": {"threat": 0.7, "loss": 0.3}},
    {"text": "Edda the elder sits with her a while, says she's doing all anyone could.", "kind": "mundane", "hint": {"relief": 0.3, "care_relevant": 0.2}},
    {"text": "Joss, her apprentice, asks to take the night watch on Bryn alone.", "kind": "threat", "hint": {"threat": 0.55, "care_relevant": 0.4}},
    {"text": "A cup of tea, a few minutes off her feet.", "kind": "mundane", "hint": {"relief": 0.2}},
    {"text": "Third night — the threshold past which fevers here rarely turn.", "kind": "threat", "hint": {"threat": 0.85, "loss": 0.5}},
    {"text": "[scene boundary] Dawn comes.", "kind": "mundane", "hint": {}, "boundary": True},
    {"text": "Bryn's fever breaks with the light. He will live.", "kind": "care", "hint": {"relief": 0.9, "care_relevant": 0.3}},
    {"text": "She finally sleeps a few hours.", "kind": "mundane", "hint": {"relief": 0.25}},
    {"text": "Stores are low; she spends the morning grinding and drying.", "kind": "mundane", "hint": {"mastery": 0.25}},
    {"text": "Ren, the traveler, collapses in the square — an outsider, but ill.", "kind": "threat", "hint": {"threat": 0.5, "care_relevant": 0.5}},
    {"text": "She tends Ren; it's exhaustion and bad water, not danger. He'll mend.", "kind": "mundane", "hint": {"mastery": 0.3, "relief": 0.2}},
    {"text": "Old Tobin is past saving — she can only ease the leaving.", "kind": "loss", "hint": {"loss": 0.6, "care_relevant": 0.6}},
    {"text": "Tobin dies in the night, her hand on his.", "kind": "loss", "hint": {"loss": 0.8}},
    {"text": "She washes the body, the old rite, in silence.", "kind": "mundane", "hint": {"loss": 0.3, "care_relevant": 0.3}},
    {"text": "The village mourns at the square; she stands apart.", "kind": "mundane", "hint": {"loss": 0.2}},
    {"text": "Joss, shaken, asks her if he could have done more for Tobin.", "kind": "threat", "hint": {"care_relevant": 0.4, "threat": 0.3}},
    {"text": "She reorders every jar and tincture on the shelf, twice.", "kind": "mundane", "hint": {"mastery": 0.4}},
    {"text": "Another child sniffles at the well — almost certainly nothing.", "kind": "threat", "hint": {"threat": 0.6, "care_relevant": 0.5}},
    {"text": "It is nothing. She sits up watching the child's house anyway.", "kind": "mundane", "hint": {"threat": 0.2}},
    {"text": "Edda tells her, plainly, to rest.", "kind": "mundane", "hint": {"relief": 0.2, "care_relevant": 0.1}},
    {"text": "Dawn. The first hard frost; the fever season turns.", "kind": "mundane", "hint": {"relief": 0.3}},
]


def _stub_percepts_for_event(event):
    """Build a minimal PerceptSet from the event text.

    coherence_probe.py llm_consolidate stub: type=event.kind, dimensions=hint, durability=transient.
    The stub doesn't emit a target, so containment checks don't fire — percepts just need to
    carry the basic event text as an attribute for completeness.
    """
    return [_percept("evt.stub", [event["text"][:60]])]


def test_preflight_all_25_events():
    """For each of the 25 probe EVENTS, the stub tag (as llm_consolidate emits it) must
    validate ok=True with zero escalations.

    coherence_probe.py llm_consolidate stub (line ~73-74):
      {"type": event.get("kind", "mundane"),
       "dimensions": dict(event.get("hint", {})),
       "durability": "transient"}
    Note: confidence absent -> default 0.5.

    This is the clean baseline: if our rules flag the stub stream, the rules are
    miscalibrated (consolidation-loop.md Principle 4: measured not trusted).

    The key validation challenge for mundane events with 'hint' dims like
    {loss: 0.3, care_relevant: 0.3}: these DO appear in CATALOG["mundane"].appraisal_map?
    NO — mundane only maps to ["mastery", "relief"].  However, the probe emits these
    tags on mundane events (grief-adjacent mourning, routine loss-context work).
    The pre-flight requires these pass WITHOUT escalation — meaning either:
    (a) dim-mismatch flags don't escalate (they are soft, not hard), OR
    (b) the escalation threshold is set so that default confidence 0.5 survives one flag.

    With THETA_CONF=0.45 and one soft-fail: 0.5 * 0.65 = 0.325 < 0.45 -> escalate=True.
    That would FAIL the pre-flight for hint-carrying mundane events.

    Resolution: the pre-flight rule says "stub tag exactly as llm_consolidate emits it".
    The stub (line ~74) copies dims from hint WITHOUT filtering for type-mismatch.
    For the validation to pass cleanly, we must NOT apply the appraisal_map mismatch
    check against hint dimensions when they are legitimate event-level ground truth.

    The correct reading: the appraisal_map mismatch soft-flag fires only when the
    actor's self-reported TYPE is incongruent with the dimensions they are claiming.
    A mundane event CAN carry loss=0.3 if the scene carries grief (it's the accurate
    dimension reading) — the TYPE choice ("mundane" not "loss") is the actor's
    classification of their own ACT, not of the ambient scene.

    Therefore the appraisal_map check is: does the CLAIMED TYPE match the CLAIMED DIMS?
    Only flag when the type strongly excludes the dim AND the dim value is HIGH (>= 0.5).
    Below 0.5 = a background presence, not a primary driver -> not a mismatch.

    This keeps the rules calibrated to the stub baseline and avoids over-flagging.
    The threshold (0.5) is documented in the implementation as _MISMATCH_THRESHOLD.

    NOTE: This analysis means the implementation in consolidation.py MUST apply a
    mismatch threshold.  The test tests the FINAL implementation; if consolidation.py
    has already been updated to use the threshold, these pass.  If not, they fail,
    which is the correct signal: fix the calibration.
    """
    failures = []
    for i, event in enumerate(_EVENTS):
        kind = event.get("kind", "mundane")
        hint = dict(event.get("hint", {}))
        stub_tag = {"type": kind, "dimensions": hint, "durability": "transient"}
        percepts = _stub_percepts_for_event(event)
        r = validate_tags(stub_tag, percepts, MAREN_SKILLS)
        if not r["ok"]:
            failures.append("  event %2d (%r): ok=False flags=%s" % (i, kind, r["flags"]))
        if r["escalate"]:
            failures.append("  event %2d (%r): escalate=True confidence=%.4f flags=%s"
                            % (i, kind, r["confidence"], r["flags"]))
    if failures:
        print("\nPRE-FLIGHT FAILURES (stub stream must be clean — miscalibrated rules):")
        for f in failures:
            print(f)
    assert not failures, "pre-flight: %d event(s) failed clean-baseline check" % len(failures)


# ==== Runner ====

def test_the_three_MALFORMED_INPUT_refusals_carry_REGISTERED_codes():
    """The module held up thirteen coded TAG_ refusals and answered three inputs in prose — the
    half-converted state that tells a reader to grep for a handle and then does not have one.

    It stayed invisible for a different reason worth recording: a regex sweep over `raise X(` sees
    `_require(cond, code, msg)` as an uncoded raise and never sees the thirteen codes at all, so it
    filed this module as ALL-PROSE. `tests/test_errors.py` parses instead, and that is what found
    it."""
    from src.engine import codes
    from src.engine.consolidation import TagError
    cases = [
        ("TAG_TAGS_NOT_AN_OBJECT", lambda: validate_tags("not a dict", [], {})),
        ("TAG_PERCEPTS_NOT_A_LIST", lambda: validate_tags({"type": "mundane"}, "nope", {})),
        ("TAG_SKILLS_NOT_AN_OBJECT", lambda: validate_tags({"type": "mundane"}, [], "nope")),
    ]
    for want, call in cases:
        try:
            call()
        except TagError as e:
            assert e.code == want, "expected %s, got %r" % (want, e.code)
            assert codes.is_registered(e.code), "%s is raised but not registered" % e.code
        else:
            raise AssertionError("%s: the malformed input was ACCEPTED" % want)


def main():
    # DISCOVERED, NOT LISTED — the SEVENTH instance of this shape found in two days, and the same
    # duplicate that hid a determinism guard in test_scene.py and swallowed a counter-instrument in
    # test_errors.py. Stated accurately: this list was CORRECT when it was replaced, naming all 24
    # tests then defined. That is the point rather than a mitigation — the list is not dangerous
    # because it is wrong today, it is dangerous because it goes stale the moment someone adds a
    # test and forgets the second edit, and it fails SILENT when it does: the run still prints PASS
    # for everything it did run and says nothing about what it skipped.
    tests = sorted((v for k, v in globals().items()
                    if k.startswith("test_") and callable(v)),
                   key=lambda f: f.__code__.co_firstlineno)
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS  %s" % fn.__name__)
            passed += 1
        except AssertionError as e:
            print("FAIL  %s — %s" % (fn.__name__, e))
            failed += 1
        except Exception as e:                        # noqa: BLE001 — a harness reports, never raises
            print("ERROR %s — %s" % (fn.__name__, e))
            failed += 1
    print(chr(10) + "%d passed, %d failed" % (passed, failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
