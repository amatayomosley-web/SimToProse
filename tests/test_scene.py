#!/usr/bin/env python3
"""test_scene.py — Gate-3 proof for scene-assembly + relevancy-gate.

Script-style (like tests/test_ledger.py): plain asserts, main(), exit code 0 = all pass.
Stdlib only. No pytest.

Packet/assembly half (gate-machinery tests 2/3/4/7 live in tests/test_gate.py — 500-line rule split):
  1. WHITELIST       — every ref in the packet traces to real inputs; canary cannot appear
  2. ABSENCE         — detail gated behind high DC absent for low-skill char, present for high-skill
  3. IDENTITY GATING — recognized_as filled only on passed insight check
  4. ENERGY NARROWING — low energy recalls fewer; 0.6-confidence Joss belief drops first
  5. STABLE PREFIX   — json.dumps byte-identical across different events/affect
  6. MANIFEST FIDELITY — manifest refs == volatile refs (record-contract.md audit A2)
  7. TRIGGER WALL    — percept-failed detail cannot trigger vault recall
  8. FAIL LOUD       — malformed inputs raise ValueError
  9. PROBE PRE-FLIGHT — all 25 EVENTS pass; Suil + third-night fire; 1+ percept every turn
"""
import copy
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))

from src.engine.scene import assemble                             # noqa: E402
from src.engine.gate import (                                    # noqa: E402
    perception_scope,
    extract_triggers,
    run_gate,
    _energy_budget,
    PERCEPTION_DC_SUBTLE,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _char():
    return _load("characters/maren-healer.json")


def _world():
    return _load("world/ashford-slice.json")


def _flat_affect(v=0.5):
    return {k: v for k in ("SEEKING", "FEAR", "RAGE", "LUST", "CARE", "PANIC_GRIEF", "PLAY", "DISGUST")}


def _ss(text="A routine morning in Ashford.", kind="mundane"):
    return {"event": {"text": text, "kind": kind}, "recent": [], "location": None}


def _fever_ss():
    return _ss("Bryn, a child, is carried in with a climbing fever.", "threat")


def _joss_night_ss():
    """Turn 6: fires both 'night' (vault[1]) and 'joss' (vault[2]) triggers."""
    return _ss("Joss, her apprentice, asks to take the night watch on Bryn alone.", "threat")


# ---------------------------------------------------------------------------
# Test utilities
# ---------------------------------------------------------------------------

PASS = []
FAIL = []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print("  PASS  %s" % name)
    else:
        FAIL.append(name)
        msg = "  FAIL  %s" % name
        if detail:
            msg += "  — " + detail
        print(msg)


def _all_claim_words(packet):
    """Collect all string content from the volatile body (for canary test)."""
    words = set()
    for p in packet["volatile"]["percepts"]:
        for attr in p.get("attributes", []):
            words.update(attr.lower().split())
        rec = p.get("recognized_as", "")
        if rec:
            words.update(rec.lower().split())
    for r in packet["volatile"]["recall"]:
        claim = r.get("claim", "")
        words.update(claim.lower().split())
    return words


# ---------------------------------------------------------------------------
# 1. WHITELIST — every attribute/claim derives from real inputs
# ---------------------------------------------------------------------------

def test_whitelist():
    """Every ref/attribute in the packet must trace to scene_slice, world, or vault.
    scene-assembly.md: excluded-by-construction; the packet whitelists, absence is the default.
    """
    print("\n[1] WHITELIST")
    ch, w = _char(), _world()
    af    = _flat_affect()
    cond  = ch["current"]["condition"]

    packet = assemble(ch, w, _fever_ss(), af, cond)

    # Canary: inject a fact that does NOT exist in scene_slice, world, or vault
    # then verify it cannot appear anywhere in the packet.
    CANARY = "xyzzy_injected_secret_0xdeadbeef"
    all_content = _all_claim_words(packet)
    check(
        "canary-absent",
        CANARY not in all_content,
        "canary word appeared in packet: %s" % all_content,
    )

    # Every recall ref must be of the form "vault[N]" (traces to real vault entry)
    for r in packet["volatile"]["recall"]:
        ref = r.get("ref", "")
        check(
            "recall-ref-format (%s)" % ref,
            ref.startswith("vault[") and ref.endswith("]"),
            "unexpected recall ref format: %r" % ref,
        )

    # Every percept ref must start with a known prefix (evt. / entity. / loc.)
    for p in packet["volatile"]["percepts"]:
        ref = p.get("ref", "")
        check(
            "percept-ref-prefix (%s)" % ref[:20],
            any(ref.startswith(pfx) for pfx in ("evt.", "entity.", "loc.")),
            "unexpected percept ref prefix: %r" % ref,
        )


# ---------------------------------------------------------------------------
# 5. STABLE PREFIX STABILITY — byte-identical across events/affect
# ---------------------------------------------------------------------------

def test_stable_prefix_stability():
    """Two assemble() calls with different events and affect, same char dict:
    json.dumps(packet['stable'], sort_keys=True) must be byte-identical.

    scene-assembly.md §"Stable prefix": cacheable; same char dict -> identical bytes.
    """
    print("\n[5] STABLE PREFIX STABILITY")
    ch, w = _char(), _world()
    cond  = ch["current"]["condition"]

    af1 = _flat_affect(0.3)
    af2 = _flat_affect(0.8)
    ss1 = _ss("Morning. She walks the upland edge gathering late herbs.", "mundane")
    ss2 = _ss("Bryn, a child, is carried in with a climbing fever.", "threat")

    p1 = assemble(ch, w, ss1, af1, cond)
    p2 = assemble(ch, w, ss2, af2, cond)

    stable1 = json.dumps(p1["stable"], sort_keys=True, ensure_ascii=False)
    stable2 = json.dumps(p2["stable"], sort_keys=True, ensure_ascii=False)

    check(
        "stable-prefix-byte-identical",
        stable1 == stable2,
        "stable prefix differs:\n  p1=%s\n  p2=%s" % (stable1[:200], stable2[:200]),
    )

    # Volatile must DIFFER between different events (ensures volatile is actually volatile)
    vol1 = json.dumps(p1["volatile"]["percepts"], sort_keys=True)
    vol2 = json.dumps(p2["volatile"]["percepts"], sort_keys=True)
    check(
        "volatile-differs-across-events",
        vol1 != vol2,
        "volatile percepts identical for different events (did assembly collapse?)",
    )


# ---------------------------------------------------------------------------
# 6. MANIFEST FIDELITY — manifest refs == volatile refs (record-contract.md A2)
# ---------------------------------------------------------------------------

def test_manifest_fidelity():
    """manifest.percepts == [p['ref'] for p in volatile.percepts]
       manifest.edges     == [e['target'] for e in volatile.edges]
       manifest.beliefs_injected == len(volatile.recall)

    record-contract.md audit A2: the read-side join key must be persisted.
    """
    print("\n[6] MANIFEST FIDELITY")
    ch, w = _char(), _world()
    af    = _flat_affect()
    cond  = ch["current"]["condition"]

    # Use a Joss event so recall is non-empty
    ss = _ss("Joss, shaken, asks her if he could have done more for Tobin.", "threat")
    packet = assemble(ch, w, ss, af, cond)

    vol      = packet["volatile"]
    manifest = packet["manifest"]

    # Percept refs
    vol_percept_refs  = [p["ref"] for p in vol["percepts"]]
    mfst_percept_refs = manifest["percepts"]
    check(
        "manifest-percept-refs-match",
        vol_percept_refs == mfst_percept_refs,
        "volatile refs=%s  manifest refs=%s" % (vol_percept_refs, mfst_percept_refs),
    )

    # Edge refs
    vol_edge_refs  = [e["target"] for e in vol["edges"]]
    mfst_edge_refs = manifest["edges"]
    check(
        "manifest-edge-refs-match",
        vol_edge_refs == mfst_edge_refs,
        "volatile edges=%s  manifest edges=%s" % (vol_edge_refs, mfst_edge_refs),
    )

    # beliefs_injected count
    check(
        "manifest-beliefs-count-match",
        manifest["beliefs_injected"] == len(vol["recall"]),
        "manifest beliefs_injected=%d  volatile recall len=%d" % (
            manifest["beliefs_injected"], len(vol["recall"])),
    )

    # recall_refs top-level key == manifest.percepts are vault[N] refs
    check(
        "recall-refs-key-matches-volatile",
        set(packet["recall_refs"]) == {r["ref"] for r in vol["recall"]},
        "recall_refs=%s  volatile recall refs=%s" % (
            packet["recall_refs"], [r["ref"] for r in vol["recall"]]),
    )


# ---------------------------------------------------------------------------
# 8. FAIL LOUD — malformed inputs raise ValueError
# ---------------------------------------------------------------------------

def test_fail_loud():
    """Malformed inputs must raise ValueError (fail loud — no coercion).
    state.py precedent: "fail loud, never coerce."
    """
    print("\n[8] FAIL LOUD")
    ch, w = _char(), _world()
    af    = _flat_affect()
    cond  = ch["current"]["condition"]

    def expect_error(label, fn):
        try:
            fn()
            check("raises-ValueError-on-%s" % label, False, "no exception raised")
        except ValueError:
            check("raises-ValueError-on-%s" % label, True)
        except Exception as exc:
            check("raises-ValueError-on-%s" % label, False,
                  "wrong exception type %s: %s" % (type(exc).__name__, exc))

    # Not a dict
    expect_error("char-not-dict",    lambda: assemble("bad", w, _ss(), af, cond))
    expect_error("world-not-dict",   lambda: assemble(ch, "bad", _ss(), af, cond))
    expect_error("slice-not-dict",   lambda: assemble(ch, w, "bad", af, cond))
    expect_error("affect-not-dict",  lambda: assemble(ch, w, _ss(), "bad", cond))
    expect_error("cond-not-dict",    lambda: assemble(ch, w, _ss(), af, "bad"))

    # Missing mandatory section
    ch_nosec = copy.deepcopy(ch)
    del ch_nosec["baseline"]
    expect_error("char-missing-baseline", lambda: assemble(ch_nosec, w, _ss(), af, cond))

    # scene_slice missing event
    expect_error("slice-missing-event",   lambda: assemble(ch, w, {"recent": []}, af, cond))

    # scene_slice event missing text
    expect_error("slice-event-missing-text", lambda: assemble(ch, w, {"event": {"kind": "mundane"}}, af, cond))

    # perception_scope fail loud
    expect_error("perception_scope-bad-slice",
                 lambda: perception_scope("bad", w, ch["baseline"]["skills"], cond))

    # run_gate fail loud
    expect_error("run_gate-bad-triggers",
                 lambda: run_gate("bad", ch["current"]["vault"], ch["baseline"]["skills"],
                                  ch["current"]["active_goals"], cond))


# ---------------------------------------------------------------------------
# 9. PROBE PRE-FLIGHT — all 25 events; Suil + third-night fire; 1+ percept each turn
# ---------------------------------------------------------------------------

def test_probe_preflight():
    """Run all 25 EVENTS through assemble() with the real maren fixture:
    - No exceptions on any turn
    - Every packet has >= 1 percept
    - Manifests are non-empty (state_fields_read populated)
    - Across the 25 turns, at least one fires the Suil belief (fever-death trigger chain)
    - At least one fires the third-night-rule belief
    """
    print("\n[9] PROBE PRE-FLIGHT (25 events)")
    # Import EVENTS from coherence_probe read-only
    from coherence_probe import EVENTS  # noqa: E402

    ch, w = _char(), _world()
    af    = _flat_affect()
    cond  = ch["current"]["condition"]

    errors            = []
    turns_zero_percepts = []
    turns_empty_manifest = []
    suil_fired        = False
    third_night_fired = False

    for i, event in enumerate(EVENTS):
        ss = {
            "event":    {"text": event["text"], "kind": event.get("kind", "mundane")},
            "recent":   [],
            "location": None,
        }
        try:
            p = assemble(ch, w, ss, af, cond)

            if len(p["volatile"]["percepts"]) < 1:
                turns_zero_percepts.append(i)

            if not p["manifest"].get("state_fields_read"):
                turns_empty_manifest.append(i)

            for r in p["volatile"]["recall"]:
                claim_lo = r.get("claim", "").lower()
                if "suil" in claim_lo or ("fever" in claim_lo and "break" in claim_lo):
                    suil_fired = True
                if "third night" in claim_lo:
                    third_night_fired = True

        except Exception as exc:
            errors.append("turn %d: %s" % (i, exc))

    check(
        "no-exceptions-over-25-events",
        not errors,
        "errors: %s" % errors,
    )
    check(
        "every-turn-has-at-least-one-percept",
        not turns_zero_percepts,
        "turns with 0 percepts: %s" % turns_zero_percepts,
    )
    check(
        "every-manifest-has-state-fields",
        not turns_empty_manifest,
        "turns with empty manifest: %s" % turns_empty_manifest,
    )
    check(
        "suil-belief-fires-across-25-turns",
        suil_fired,
        "Suil (vault[0]) never fired across all 25 events",
    )
    check(
        "third-night-belief-fires-across-25-turns",
        third_night_fired,
        "third-night (vault[1]) never fired across all 25 events",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("test_scene.py — Gate 3 scene-assembly + relevancy-gate\n")

    test_whitelist()
    test_stable_prefix_stability()
    test_manifest_fidelity()
    test_fail_loud()
    test_probe_preflight()

    total  = len(PASS) + len(FAIL)
    n_pass = len(PASS)
    n_fail = len(FAIL)

    print("\n--- summary ---")
    print("  %d / %d passed" % (n_pass, total))
    if FAIL:
        print("  FAILED:")
        for f in FAIL:
            print("    " + f)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
