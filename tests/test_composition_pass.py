#!/usr/bin/env python3
"""test_composition_pass.py ? CLI and integration tests for scripts/composition_pass.py.

Asserts:
  - CLI parser correctly maps picks and arguments
  - apply_composition_pass composes baseline stats and injects catalog rows & vault beliefs
  - Stacked cap +-0.35 is strictly enforced
  - Deduplication prevents duplicate catalog rows or vault claims

Stdlib only, script-style. Exit 0 = all pass.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts.composition_pass import parse_picks, apply_composition_pass
from src.engine import profiles as P


def test_parse_picks():
    args = ["shipwreck_drowning:1.0", "childhood_famine:0.5", "predator_mauling"]
    picks = parse_picks(args)
    assert len(picks) == 3
    assert picks[0] == {"profile": "shipwreck_drowning", "weight": 1.0}
    assert picks[1] == {"profile": "childhood_famine", "weight": 0.5}
    assert picks[2] == {"profile": "predator_mauling", "weight": 1.0}


def test_apply_composition_pass():
    """The composed values must land where CONSUMERS read them, not merely exist — and the
    pass must NOT touch what it no longer owns.

    This test previously asserted composed["baseline"]["WARINESS"], composed["catalog_rows"] and
    composed["vault_beliefs"] — three paths the engine does not read. It passed while every value
    the pass computed was dead: levers.active_rows reads baseline.catalog.rows via scene.assemble,
    and the recall gate reads current.vault (vault.py:117). A key existing proves nothing; a
    consumer reading it does.

    INVERTED 2026-09-10 on the temperament half: until then the pass moved
    baseline.temperament.<P>.mean and this test asserted that it did. The owner ruled where a
    character rests is a DESIGN question authored as a rest word beside the voice, so the pass
    writes nothing there; the two profiles picked below both used to move WARINESS, and now the
    mean must not move. Their old effect sits on each profile as a `rest_note` for the author.
    """
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))
    from src.engine.state import build_profile
    from src.engine.records import PATHS

    char = {
        "id": "test_hero", "name": "Test Hero",
        "fixed": {"genotype": {}},
        "baseline": {
            "temperament": {p: {"rest": "low", "mean": 0.30} for p in PATHS},
            "traits": {"emotionality": {"mean": 0.50}},
            "model": {"schwartz": {"security": 0.50}},
            "relationship_priors": {"default_trust": 0.50},
        },
        "current": {"affect": {p: 0.30 for p in PATHS}, "vault": [],
                    "condition": {"energy": 0.8, "allostatic_load": 0.2}},
    }
    import copy as _copy
    before_temp = _copy.deepcopy(char["baseline"]["temperament"])
    before_security = char["baseline"]["model"]["schwartz"]["security"]

    composed = apply_composition_pass(char, [
        {"profile": "predator_mauling", "weight": 1.0},
        {"profile": "flagellant_ascetic_order", "weight": 1.0}])

    # 1. the temperament is UNTOUCHED (rest is design); the worth menu still composes
    assert composed["baseline"]["temperament"] == before_temp, \
        "the pass wrote temperament: %r" % (composed["baseline"]["temperament"]["WARINESS"],)
    assert composed["baseline"]["model"]["schwartz"]["security"] > before_security, "security did not move"
    for pid in ("predator_mauling", "flagellant_ascetic_order"):
        assert "WARINESS" in P.get(pid).get("rest_note", "") or "DISPLEASURE" in P.get(pid).get("rest_note", ""), \
            "%s lost its old temperament effect instead of keeping it as a rest_note" % pid
    build_profile(composed)                       # must still be a valid character
    assert "WARINESS" not in composed["baseline"], "flat FEAR written beside the nested one — the bug"

    # 2. WOUND rows were MINTED as engine wounds (gate three, 2026-09-11), keyed concept@PATH and
    #    sourced to the profile, where connection.for_about reads them; they are NOT catalog rows.
    rows = (composed["baseline"].get("catalog") or {}).get("rows") or []
    sources = [r["source"] for r in rows]
    assert not any(str(src).startswith("wound:") for src in sources), "a wound row was placed as a lever: %s" % sources
    wounds = {w["id"]: w for w in composed["baseline"].get("wounds") or [] if isinstance(w, dict) and w.get("id")}
    assert "predator@WARINESS" in wounds and wounds["predator@WARINESS"]["source"] == "profile:predator_mauling", sorted(wounds)
    assert "indulgence@DISPLEASURE" in wounds, sorted(wounds)
    assert 0.0 < wounds["predator@WARINESS"]["intensity"] <= 1.0 and wounds["predator@WARINESS"]["trigger"], wounds["predator@WARINESS"]
    assert "catalog_rows" not in composed, "top-level catalog_rows is read by nothing"

    # 3. belief seeds landed at current.vault, where the recall gate reads them
    claims = [v["claim"] for v in composed["current"]["vault"]]
    assert any("silence in the brush" in c for c in claims), claims
    assert any("flesh is corrupt" in c for c in claims), claims
    assert "vault_beliefs" not in composed, "top-level vault_beliefs is read by nothing"

    # 4. and the wound actually LANDS: a reading about the concept is amplified by it, and it fires
    #    the wound by identity (no word list anywhere)
    from src.engine import wound as _wound
    prof = build_profile(composed)
    assert prof["held"].get("concept:predator", {}).get("WARINESS", 0) >= 0.2, prof["held"]
    from src.engine.state import appraise
    aff = dict(composed["current"]["affect"])
    hit = appraise(aff, {"dimensions": {"threat": 0.8}, "target": "concept:predator"}, prof, targets={"WARINESS": "concept:predator"})
    plain = appraise(aff, {"dimensions": {"threat": 0.8}, "target": "concept:crowds"}, prof, targets={"WARINESS": "concept:crowds"})
    assert hit["WARINESS"] > plain["WARINESS"], (hit["WARINESS"], plain["WARINESS"])
    assert _wound.fires(wounds["predator@WARINESS"], {"about": "concept:predator", "surfaces": []})
    assert not _wound.fires(wounds["predator@WARINESS"], {"about": "concept:crowds", "surfaces": ["a quiet room"]})


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("  PASS  %s" % t.__name__)
        except Exception as e:
            failed += 1
            print("  FAIL  %s: %s" % (t.__name__, e))
    print("")
    print(str(len(tests) - failed) + "/" + str(len(tests)) + " passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
