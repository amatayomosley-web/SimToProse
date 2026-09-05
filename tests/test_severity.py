"""test_severity.py — the event-strength vocabulary resolves onto the EXISTING 0..1 scale.

The whole value of this change is that the scale did not move. These tests assert that twice: once
directly (the words land where the already-calibrated thresholds sit), and once by construction
(a float still passes through untouched, so every recorded run is unaffected).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.severity import (WORDS, SeverityError, normalise_dimensions,  # noqa: E402
                                 value_of, _MAGNITUDE)


def test_words_are_ordered_floor_to_ceiling():
    vals = [_MAGNITUDE[w] for w in WORDS]
    assert vals == sorted(vals), "WORDS must run floor to ceiling, got %s" % (list(zip(WORDS, vals)),)
    assert len(set(vals)) == len(vals), "two words share a value — one of them is unreachable"


def test_every_word_is_on_the_unit_scale():
    for w in WORDS:
        assert 0.0 <= _MAGNITUDE[w] <= 1.0, "%s=%s is off the 0..1 severity scale" % (w, _MAGNITUDE[w])


def test_a_word_resolves_to_its_float():
    out = normalise_dimensions({"type": "affront", "dimensions": {"social_violation": "marked"}})
    assert out["dimensions"]["social_violation"] == 0.60


def test_a_float_passes_through_untouched():
    """THE MIGRATION GUARANTEE. Every existing fixture and recorded run must be unaffected."""
    tags = {"type": "threat", "dimensions": {"threat": 0.5, "loss": 0.125}}
    assert normalise_dimensions(tags)["dimensions"] == {"threat": 0.5, "loss": 0.125}


def test_words_and_floats_mix_in_one_block():
    out = normalise_dimensions({"dimensions": {"threat": "severe", "loss": 0.2}})
    assert out["dimensions"] == {"threat": 0.78, "loss": 0.2}


def test_normalise_is_pure():
    tags = {"dimensions": {"threat": "mild"}}
    normalise_dimensions(tags)
    assert tags["dimensions"]["threat"] == "mild", "input dict was mutated"


def test_off_ladder_word_fails_loud_and_names_the_vocabulary():
    """Hard rule 6 — modules fail loud. An unpriceable event is not a degraded reading."""
    try:
        normalise_dimensions({"dimensions": {"threat": "catastrophic"}})
    except SeverityError as e:
        for w in WORDS:
            assert w in str(e), "the error must name every legal word; %r missing" % w
    else:
        raise AssertionError("an off-ladder word must raise SeverityError")


def test_case_and_whitespace_are_tolerated():
    assert value_of("  MARKED ") == value_of("marked")


def test_non_dict_inputs_are_returned_unchanged():
    assert normalise_dimensions(None) is None
    assert normalise_dimensions({"type": "mundane"}) == {"type": "mundane"}
    assert normalise_dimensions({"dimensions": "not-a-dict"})["dimensions"] == "not-a-dict"


def test_the_words_land_on_the_thresholds_ALREADY_calibrated_against_this_scale():
    """THE POINT OF THE CHANGE. Six tiers key thresholds off the 0..1 severity meaning. If a word
    stopped clearing the gate it used to clear, the scale moved and the change is wrong."""
    from src.engine.arc import _DURABLE_DIM
    from src.engine.bonds import _CLIFF_SEVERITY, _OVERT_SEVERITY
    from src.engine.consolidation import _MISMATCH_THRESHOLD

    assert value_of("marked") >= _DURABLE_DIM, "marked must remain a durable arc candidate"
    assert value_of("marked") >= _OVERT_SEVERITY, "marked must remain an overt act"
    assert value_of("marked") >= _MISMATCH_THRESHOLD, "marked must remain mismatch-checkable"
    assert value_of("moderate") < _DURABLE_DIM, "moderate must NOT be durable — that is the line"
    assert value_of("extreme") >= _CLIFF_SEVERITY, "extreme must reach the relationship cliff"
    assert value_of("severe") < _CLIFF_SEVERITY, "only extreme may reach the cliff"


def test_the_full_ladder_survives_the_engine_and_stays_ordered():
    """End to end: a word through normalise -> appraise must produce monotonically larger impact.
    Guards against a rung that resolves but prices identically to its neighbour."""
    import json
    from src.engine.state import PRIMARIES, appraise, build_profile

    ch = json.load(open("characters/maren-healer.json", encoding="utf-8"))
    prof = build_profile(ch)
    base = {p: 0.0 for p in PRIMARIES}
    impacts = []
    for w in WORDS:
        tags = normalise_dimensions({"type": "threat", "dimensions": {"threat": w},
                                     "durability": "transient"})
        out = appraise(base, tags, prof)
        impacts.append(sum(abs(out[p] - base[p]) for p in PRIMARIES))
    assert impacts == sorted(impacts), "impact must rise with the word: %s" % list(zip(WORDS, impacts))
    assert len(set(round(i, 6) for i in impacts)) == len(impacts), \
        "two rungs price identically through the engine: %s" % list(zip(WORDS, impacts))


def test_the_contract_never_asks_for_a_NUMERIC_severity_anywhere():
    """THE GUARD THAT WAS MISSING. The first pass changed the reply SKELETON to words and left the
    CALIBRATION sentence saying "emit 0.1-0.3 ... reserve >0.6", so the actor was told to write
    words in one place and floats in another. The original check only read a 720-char window after
    `"dimensions": {` and never reached it. This reads the WHOLE rendered contract."""
    import re
    from src.engine.prompt import _DIMS

    src = open("src/engine/prompt.py", encoding="utf-8").read()
    i = src.index("usr = (")
    j = src.index("# final name-hygiene wall")
    contract = src[i:j]

    for dim in _DIMS:
        assert '"%s": 0..1' % dim not in contract, "dimension %r still offered as a bare float" % dim
    for bad in ("0.1-0.3", ">0.6", "0.6 for", "emit 0."):
        assert bad not in contract, (
            "the contract still instructs a NUMERIC severity (%r) while the skeleton asks for a "
            "word — the actor gets contradictory instructions" % bad)


def test_every_word_is_defined_in_the_contract_the_actor_receives():
    """A closed ordinal set is not calibration. Without a gloss the model knows `severe` outranks
    `mild` and nothing tells it which one a given event earns."""
    from src.engine.severity import gloss
    text = gloss()
    for w in WORDS:
        assert w in text, "%r has no definition in the contract gloss" % w
    assert "change them if it kept happening" in text, (
        "the gloss must anchor `marked` to the durable line — that is the one boundary the engine "
        "acts on differently, and the only anchor a writer can check")


def test_the_rubric_gives_every_rung_a_BOUNDARY_not_just_a_meaning():
    """THE GRADER'S ACTUAL PROBLEM. An ordering is free — every model knows `severe` outranks
    `mild`. What no model has is the test that separates two neighbours, so each rung must carry
    one, phrased as something a reader of the scene can run."""
    from src.engine.severity import rubric, _GLOSS

    text = rubric()
    for w in WORDS:
        assert w in text, "%r missing from the rubric" % w
    for w, meaning, boundary in _GLOSS:
        assert meaning.strip(), "%r has no meaning" % w
        assert boundary.strip(), "%r has no boundary test" % w
    lower = [b for w, m, b in _GLOSS[1:]]
    for b in lower:
        assert b.startswith("vs "), (
            "every rung above the floor must name the rung it is being told apart FROM; got %r" % b)
    assert _GLOSS[0][2].startswith("the floor"), "the bottom rung has nothing below it and must say so"


def test_the_rubric_anchors_the_two_boundaries_the_ENGINE_acts_on():
    """marked and extreme are not ordinary rungs — they are where engine behaviour changes.
    If the rubric stops naming them, a grader has no way to hit them deliberately."""
    from src.engine.severity import rubric
    from src.engine.arc import _DURABLE_DIM
    from src.engine.bonds import _CLIFF_SEVERITY

    text = rubric()
    assert "would begin to change them if it kept happening" in text, (
        "marked is _DURABLE_DIM (%s) — the rubric must say that is what it means" % _DURABLE_DIM)
    assert "no version of this event that could be worse" in text, (
        "extreme is the only rung reaching _CLIFF_SEVERITY (%s) — the rubric must give it a "
        "test a reader can actually run" % _CLIFF_SEVERITY)


def test_gloss_and_rubric_are_the_same_ladder():
    """One source of truth. Two renderings of _GLOSS, never two tables."""
    from src.engine.severity import gloss, rubric, _GLOSS
    for w in WORDS:
        assert w in gloss() and w in rubric()
    assert len(_GLOSS) == len(WORDS) == len(_MAGNITUDE)



def test_a_scene_CFG_may_write_the_word_the_docs_tell_it_to_write():
    """THE SURFACE THE REWRITE BROKE. On 2026-09-01 `template-scene-blueprint.md` was rewritten
    to say opening-tag dimensions are "a WORD, not a number" — while `lint_scene.py` rejected words
    and `appraise` raised on one. An author following the rewritten path wrote a word and their
    scene failed pre-flight: the exact defect class the rewrite existed to end, in the opposite
    direction, and no test noticed because the severity guard only read the ACTOR contract.

    The doc was right about the design, so the engine was told: `scripts/scene.py` resolves the
    word at the cfg parse seam, exactly as the reply seam does."""
    import json
    import os
    import sys
    import tempfile
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(repo, "scripts"))
    import scene as scene_driver
    from src.engine.severity import value_of

    cfg = {"name": "t", "situation": "s", "cast": [{"id": "a", "drive": "to be believed"}],
           "opening_tags": {"type": "loss", "durability": "durable",
                            "dimensions": {"loss": "marked", "threat": 0.3}}}
    d = tempfile.mkdtemp(prefix="swe_sev_cfg_")
    path = os.path.join(d, "cfg.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh)
    loaded = scene_driver.load_scene_cfg(path)
    dims = loaded["opening_tags"]["dimensions"]

    assert dims["loss"] == value_of("marked"), (
        "a severity WORD in a scene cfg did not resolve at the parse seam: %r" % (dims,))
    assert dims["threat"] == 0.3, "a NUMBER in the same block stopped working: %r" % (dims,)
    assert all(isinstance(v, float) for v in dims.values()), (
        "appraise() receives floats or it raises — %r" % (dims,))

    # and the LINTER accepts the word rather than reporting it as not-a-number — checked against
    # its own source, because that message is what an author actually hits at pre-flight.
    src = open(os.path.join(repo, "scripts", "lint_scene.py"), encoding="utf-8").read()
    assert "is not a number in [0,1]" not in src, (
        "lint_scene still calls a severity WORD not-a-number, which is the message an author sees "
        "after following the doc that tells them to write one")
    assert "is not a severity word" in src, (
        "lint_scene must name the ladder when the word is off it")

def test_no_DOC_still_teaches_the_numeric_severity_bands():
    """THE GUARD THAT WAS MISSING, widened. On 2026-09-01 the reply contract moved to a word ladder
    and SIX authoring docs kept teaching the old numeric bands, so the path the README sends new
    users down asked for numbers the engine had stopped accepting.

    tests/test_citations.py cannot catch this — its own docstring says "mechanical only; this suite
    cannot read intent". standard-vectors.md cited prompt.py:82 as the anchor for a numeric band,
    that line changed, and the citation still RESOLVED. Only the claim went stale."""
    import glob
    import io
    import os
    import re

    nl = chr(10)
    docs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    banned = [
        # THE ORIGINAL FOUR — the exact phrasings the reply contract used. These were DELETED by
        # a careless splice while adding the fifth, which narrowed the guard in the act of
        # widening it. Restored 2026-09-01 after an adversarial review caught the regression.
        (r"0[.]1\s*[-–]\s*0[.]3", "the old ordinary-friction band"),
        (r">\s*0[.]6", "the old severe threshold"),
        (r"dimensions:\s*[{]dim:\s*0[.][.]1", "the old numeric dimension schema"),
        (r"emit\s+0[.]\d", "an instruction to emit a numeric severity"),
        # AND the shapes those four could not see. A guard reports on what it READS: the four
        # above read STRINGS, so three docs kept teaching bands in table rows and mid-sentence.
        # Scoped by a severity GLOSS word, because an unscoped range also matches a temperament
        # mean, a multiplier and a validity window — measured, four false positives in one run.
        (r"0[.]\d\s*[-–—]\s*0[.]\d.{0,60}\b(grave|severe|reserve|"
         r"ordinary friction|real but bounded|retell|genuine stake|recoverable|irreversible)\b",
         "a numeric severity BAND being taught (write the word instead)"),
        # ...and the single-value and threshold forms, which the range pattern cannot match.
        (r"(write|use|emit|reserve)\s+`?[<>]?\s*0[.]\d`?[^—]{0,20}?\b"
         r"(faint|slight|mild|moderate|marked|severe|extreme)\b",
         "a numeric severity equated to a ladder word"),
    ]
    # COVERAGE IS PART OF THE CLAIM. A green sweep means nothing without knowing what it walked —
    # this globbed docs/*.md only, and docs/ has subdirectories.
    scanned = sorted(glob.glob(os.path.join(docs, "**", "*.md"), recursive=True))
    subdirs = {os.path.dirname(p) for p in scanned} - {docs}
    assert subdirs, ("the sweep found no docs SUBDIRECTORY — either the tree changed or the glob "
                     "stopped recursing, and a non-recursive sweep silently exempts whole folders")
    hits = []
    # RECURSIVE. The first version globbed `docs/*.md` only, so any authoring doc in a subdirectory
    # was outside the sweep entirely — and a guard reports on what it READS, which is a claim about
    # COVERAGE before it is a claim about content (CLAUDE.md, on the private-content sweep that
    # passed for three days while 42 tracked files were never walked).
    for path in sorted(glob.glob(os.path.join(docs, "**", "*.md"), recursive=True)):
        text = io.open(path, encoding="utf-8").read()
        for pattern, why in banned:
            for m in re.finditer(pattern, text):
                line = text[:m.start()].count(nl) + 1
                hits.append("%s:%d  %s (%r)" % (os.path.basename(path), line, why, m.group(0)))
    assert not hits, (
        "docs still teach a numeric severity scale the engine no longer accepts — the author writes "
        "a WORD from severity.WORDS:" + nl + "  " + (nl + "  ").join(hits))


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("  PASS  %s" % name)
            except Exception as e:                       # noqa: BLE001 — a test harness reports, never raises
                fails += 1
                print("  FAIL  %s: %s" % (name, e))
    print("%s" % ("ALL PASS" if not fails else "%d FAILED" % fails))
    sys.exit(1 if fails else 0)
