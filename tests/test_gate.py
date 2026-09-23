#!/usr/bin/env python3
"""test_gate.py — Gate-3 proof, gate-machinery half (split from test_scene.py for the 500-line rule).

Covers the relevancy-gate checks that run THROUGH assemble():
  2. ABSENCE          — detail gated behind high DC absent for low-skill char, present for high-skill
  3. IDENTITY GATING  — recognized_as filled only on passed insight check
  4. ENERGY NARROWING — low energy recalls fewer; 0.6-confidence Joss belief drops first
  7. TRIGGER WALL     — percept-failed detail cannot trigger vault recall
The packet/assembly half (whitelist, stable prefix, manifest, fail-loud, probe pre-flight)
lives in tests/test_scene.py. Script-style, stdlib only, exit 0 = all pass.
"""
import copy
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.scene import assemble                             # noqa: E402
from src.engine.gate import extract_triggers, _energy_budget      # noqa: E402
from src.engine.records import PATHS                                 # noqa: E402

# ---- fixtures + harness (mirrors test_scene.py) ----

def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _char():
    return _load("characters/maren-healer.json")


def _world():
    return _load("world/ashford-slice.json")


def _flat_affect(v=0.5):
    return {k: v for k in PATHS}     # DERIVED - see tests/test_cut.py


def _ss(text, kind):
    return {"event": {"text": text, "kind": kind}, "recent": [], "location": None}


def _joss_night_ss():
    """Turn 6: fires both 'night' (vault[1]) and 'joss' (vault[2]) triggers."""
    return _ss("Joss, her apprentice, asks to take the night watch on Bryn alone.", "threat")


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


# ---- 2. ABSENCE ON FAILED CHECK ----

def test_absence_on_failed_check():
    """A subtle cue gated at PERCEPTION_DC_SUBTLE is absent for a low-skill character,
    present for a high-skill one (scene-assembly.md: a failed check REMOVES a detail)."""
    print("\n[2] ABSENCE ON FAILED CHECK")
    ch, w = _char(), _world()
    af    = _flat_affect()
    cond  = ch["current"]["condition"]

    ch_low = copy.deepcopy(ch)                       # test data, not schema extension
    ch_low["baseline"]["skills"]["perception"] = 0.10
    ch_low["baseline"]["skills"]["insight"]    = 0.10
    ch_high = ch                                     # perception=0.78, insight=0.75

    ss = _ss("Bryn, a child, is carried in with a climbing fever.", "threat")
    packet_low  = assemble(ch_low,  w, ss, af, cond)
    packet_high = assemble(ch_high, w, ss, af, cond)

    def attrs_for(packet):
        out = set()
        for p in packet["volatile"]["percepts"]:
            out.update(p.get("attributes", []))
        return out

    attrs_low, attrs_high = attrs_for(packet_low), attrs_for(packet_high)
    check("subtle-cue-absent-for-low", "fever-climbing" not in attrs_low,
          "low-skill char got subtle cue: %s" % attrs_low)
    check("subtle-cue-present-for-high", "fever-climbing" in attrs_high,
          "high-skill char missing subtle cue; attrs=%s" % attrs_high)
    check("overt-attr-present-for-low", "fever" in attrs_low or "child" in attrs_low,
          "low-skill char missing overt attrs: %s" % attrs_low)
    check("overt-attr-present-for-high", "fever" in attrs_high or "child" in attrs_high,
          "high-skill char missing overt attrs: %s" % attrs_high)


# ---- 3. IDENTITY GATING ----

def test_identity_gating():
    """recognized_as is filled only when the insight check passes (scene-assembly.md)."""
    print("\n[3] IDENTITY GATING")
    ch, w = _char(), _world()
    af    = _flat_affect()
    cond  = ch["current"]["condition"]
    ss = _joss_night_ss()

    ch_low = copy.deepcopy(ch)
    ch_low["baseline"]["skills"]["insight"] = 0.10   # < DC_IDENTITY (0.55) -> fails
    ch_low["current"]["relationships"] = {}          # a STRANGER: isolate the insight gate (acquaintance recognizes the KNOWN)
    ch_high = ch                                     # insight 0.75 -> passes

    packet_low  = assemble(ch_low,  w, ss, af, cond)
    packet_high = assemble(ch_high, w, ss, af, cond)

    def has_recognized(packet):
        return any(p.get("recognized_as") for p in packet["volatile"]["percepts"])

    check("recognized_as-absent-for-low-insight", not has_recognized(packet_low),
          "low-insight char got recognized_as: %s" % [p for p in packet_low['volatile']['percepts'] if p.get('recognized_as')])
    check("recognized_as-present-for-high-insight", has_recognized(packet_high),
          "high-insight char missing recognized_as — percepts: %s" % packet_high['volatile']['percepts'])


# ---- 4. ENERGY NARROWING ----

def test_energy_narrowing():
    """Energy 0.2 recalls strictly fewer beliefs than 0.9; the lowest-confidence belief
    (Joss, conf=0.6, cost=0.4) drops first (relevancy-gate.md §Connection energy)."""
    print("\n[4] ENERGY NARROWING")
    ch, w = _char(), _world()
    af    = _flat_affect()
    ss = _joss_night_ss()   # fires vault[1] (night, cost 0.2) and vault[2] (joss, cost 0.4)

    cond_low  = {"energy": 0.2, "allostatic_load": 0.55, "health": 0.80, "fatigue": 0.8, "injuries": []}
    cond_high = {"energy": 0.9, "allostatic_load": 0.10, "health": 0.80, "fatigue": 0.1, "injuries": []}
    budget_low, budget_high = _energy_budget(cond_low), _energy_budget(cond_high)

    packet_low  = assemble(ch, w, ss, af, cond_low)
    packet_high = assemble(ch, w, ss, af, cond_high)
    recall_low  = packet_low["volatile"]["recall"]
    recall_high = packet_high["volatile"]["recall"]

    check("high-energy-recalls-more", len(recall_high) > len(recall_low),
          "low=%d high=%d (budgets: low=%.3f high=%.3f)" % (
              len(recall_low), len(recall_high), budget_low, budget_high))

    joss_in_low  = any("joss" in r.get("claim", "").lower() for r in recall_low)
    joss_in_high = any("joss" in r.get("claim", "").lower() for r in recall_high)
    check("joss-belief-absent-at-low-energy", not joss_in_low,
          "Joss belief appeared at low energy (budget %.3f); recall=%s" % (
              budget_low, [r["claim"][:40] for r in recall_low]))
    check("joss-belief-present-at-high-energy", joss_in_high,
          "Joss belief missing at high energy (budget %.3f); recall=%s" % (
              budget_high, [r["claim"][:40] for r in recall_high]))

    if len(recall_high) >= 2:
        confs = [r["confidence"] for r in recall_high]
        check("high-confidence-first", confs[0] >= confs[-1],
              "recall not ordered by confidence: %s" % confs)


# ---- 7. TRIGGER WALL ----

def test_trigger_wall():
    """A vault belief whose trigger appears ONLY behind a failed perception check does NOT
    fire — you cannot be triggered by what you didn't perceive (scene-assembly.md step 3).
    Entity recognition for joss_apprentice needs insight >= DC_IDENTITY (0.55); at 0.10 the
    entity is unrecognized, "joss" never enters the PerceptSet, vault[2] stays silent."""
    print("\n[7] TRIGGER WALL")
    ch, w = _char(), _world()
    af    = _flat_affect()
    ss = _joss_night_ss()

    # Ample energy so the budget is NOT the limiting factor — only the wall is under test.
    cond_ample = {"energy": 0.9, "allostatic_load": 0.10, "health": 0.80, "fatigue": 0.1, "injuries": []}

    ch_low = copy.deepcopy(ch)
    ch_low["baseline"]["skills"]["insight"]    = 0.10
    ch_low["baseline"]["skills"]["perception"] = 0.10
    ch_low["current"]["relationships"] = {}          # a STRANGER: isolate the wall (acquaintance recognizes the KNOWN)
    ch_high = ch

    packet_low  = assemble(ch_low,  w, ss, af, cond_ample)
    packet_high = assemble(ch_high, w, ss, af, cond_ample)

    low_triggers  = extract_triggers(packet_low["volatile"]["percepts"])
    high_triggers = extract_triggers(packet_high["volatile"]["percepts"])

    check("joss-trigger-absent-for-low-perception", "joss" not in low_triggers,
          "low-perception char has 'joss' in triggers: %s" % low_triggers)
    check("joss-trigger-present-for-high-perception", "joss" in high_triggers,
          "high-perception char missing 'joss' trigger: %s" % high_triggers)

    joss_in_low_recall  = any("joss" in r.get("claim", "").lower()
                              for r in packet_low["volatile"]["recall"])
    joss_in_high_recall = any("joss" in r.get("claim", "").lower()
                              for r in packet_high["volatile"]["recall"])
    check("joss-belief-absent-low-perception-wall", not joss_in_low_recall,
          "Joss belief fired despite failed trigger wall: %s" % [r["claim"] for r in packet_low["volatile"]["recall"]])
    check("joss-belief-present-high-perception-wall", joss_in_high_recall,
          "Joss belief missing for high-perception char: %s" % [r["claim"] for r in packet_high["volatile"]["recall"]])


# ---- NAME HYGIENE: render by acquaintance, mask unacquired names ----

def test_name_hygiene():
    """scope_names masks a name ONLY where the actor's edge sets known_as to a descriptor (opt-in);
    family/unflagged names stay (default = common knowledge). _display_name prettifies an id and
    never leaks the engine id form. (knowledge-model.md — keep unacquired names OUT.)"""
    print("\n[H] NAME HYGIENE")
    from src.engine.gate import scope_names, _display_name
    t = "Esme took the viola part home; ask Esme to bring it back."
    masked = scope_names(t, {"esme": {"known_as": "the new violist"}})
    check("unacquired-name-masked", "Esme" not in masked, masked)
    check("masked-uses-actor-term", "the new violist" in masked, masked)
    check("acquainted-name-kept", scope_names(t, {"esme": {"trust": 0.45}}) == t,
          "name masked despite no known_as — default must be common knowledge")
    fam = "Halvard and Suze sat together."
    check("family-not-overmasked", scope_names(fam, {"halvard_moss": {"trust": 0.7}}) == fam,
          "family name masked when it should be known")
    check("display-name-single", _display_name("esme") == "Esme")
    check("display-name-compound", _display_name("halvard_moss") == "Halvard Moss")


def test_acquaintance_recognition():
    """A named entity is recognized (recognized_as filled) if the char KNOWS them (relationship), even
    at low insight; a stranger at low insight stays 'person present'. (gate.py acquaintance keying)"""
    print("\n[I] ACQUAINTANCE RECOGNITION")
    from src.engine.gate import perception_scope
    world  = {"people": [{"id": "tamsin", "what": "the cinema's projectionist"}]}
    skills = {"perception": 0.9, "insight": 0.1}        # low insight — would FAIL the identity check
    cond   = {"energy": 1.0, "allostatic_load": 0.0}
    ss     = {"event": {"text": "Tamsin waves from the projection booth.", "kind": "mundane"}, "recent": [], "location": None}
    stranger = [p for p in perception_scope(ss, world, skills, cond, {}) if p.get("ref") == "entity.tamsin"]
    check("stranger-low-insight-unrecognized", bool(stranger) and "recognized_as" not in stranger[0], str(stranger))
    known = [p for p in perception_scope(ss, world, skills, cond, {"tamsin": {"trust": 0.55}}) if p.get("ref") == "entity.tamsin"]
    check("acquaintance-recognized-low-insight", bool(known) and known[0].get("recognized_as") == "Tamsin", str(known))


def test_referenced_is_not_present():
    """NAMED IS NOT SEEN. Every person the event text named was emitted at channel "visual" — so a
    third party reported to be acting elsewhere was rendered to the actor as SEEN, in a room they
    are not in, and took an EDGE wherever a relationship row existed. Measured on a live book.
    """
    print("")
    print("[J] REFERENCED IS NOT PRESENT")
    from src.engine.gate import perception_scope
    from src.engine.scene import _build_edges
    world  = {"people": [{"id": "noor", "what": "the station's producer"},
                         {"id": "ivo_brandt", "what": "the breakfast presenter"}]}
    skills = {"perception": 0.9, "insight": 0.9}
    cond   = {"energy": 1.0, "allostatic_load": 0.0}
    text   = "Noor says that Ivo has taken the outside-broadcast van to the fairground."
    def ents(slice_extra):
        ss = dict({"event": {"text": text, "kind": "mundane"}, "recent": [], "location": None},
                  **slice_extra)
        got = perception_scope(ss, world, skills, cond, {})
        return {p["ref"]: p for p in got if p["ref"].startswith("entity.")}

    # ---- presence SUPPLIED: the one here is seen, the one spoken of is reported
    here = ents({"present": ["noor"]})
    check("present-entity-is-visual",
          here["entity.noor"].get("present") is True and here["entity.noor"]["channel"] == "visual",
          str(here.get("entity.noor")))
    check("referenced-entity-is-reported",
          here["entity.ivo_brandt"].get("present") is False
          and here["entity.ivo_brandt"]["channel"] == "reported",
          str(here.get("entity.ivo_brandt")))

    # THE ID SPACES DIFFER — the cast says "ivo", the registry says "ivo_brandt". Joined raw,
    # every present cast member reads ABSENT and the scene loses all its edges with nothing raised.
    short = ents({"present": ["ivo"]})
    check("short-cast-id-matches-full-registry-id",
          short["entity.ivo_brandt"].get("present") is True, str(short.get("entity.ivo_brandt")))

    # ---- PRESENT IS SEEN (2026-09-18): the opener's prose names nobody, the cast list says who is
    # here. Before this the PerceptSet carried only the people the TEXT named, so on a live scene's
    # first beat the emotion seat's `about:` naming someone in the room was refused as not perceived
    # while the event seat accepted them. A present person is a percept; the perceiver is not.
    quiet = "The on-air light glowed red. Nobody had spoken since the weather report."
    def ents_quiet(slice_extra, me=None, rels=None):
        ss = dict({"event": {"text": quiet, "kind": "mundane"}, "recent": [], "location": None}, **slice_extra)
        got = perception_scope(ss, world, skills, cond, rels or {}, me=me)
        return {p["ref"]: p for p in got if p["ref"].startswith("entity.")}
    room = ents_quiet({"present": ["noor", "ivo"]}, me="noor")
    check("a-present-person-the-text-never-named-is-perceived-as-here",
          room.get("entity.ivo_brandt", {}).get("present") is True
          and room["entity.ivo_brandt"]["channel"] == "visual", str(room))
    check("the-perceiver-is-not-a-percept-of-themself", "entity.noor" not in room, str(room))
    check("recognition-still-runs-on-the-unnamed-present",
          room["entity.ivo_brandt"].get("recognized_as") == "Ivo"
          and "the breakfast presenter" in room["entity.ivo_brandt"]["attributes"], str(room))
    low = perception_scope({"event": {"text": quiet, "kind": "mundane"}, "recent": [], "location": None,
                            "present": ["noor", "ivo"]}, world, {"perception": 0.1, "insight": 0.1}, cond, {}, me="noor")
    lowp = {p["ref"]: p for p in low if p["ref"].startswith("entity.")}
    check("a-stranger-present-at-low-insight-is-a-person-present-and-no-more",
          lowp.get("entity.ivo_brandt", {}).get("attributes") == ["person present"]
          and "recognized_as" not in lowp["entity.ivo_brandt"], str(lowp))
    from src.engine import readings as _readings
    _got = _readings.parse({"readings": [{"path": "WARINESS", "rung": "unease", "about": "ivo"}], "lands_on": []},
                           me="noor", percepts=list(room.values()))
    check("the-emotion-seat-may-now-be-about-someone-in-the-room",
          len(_got[0]) == 1 and _got[0][0].about == "ivo", str(_got[0]))
    check("no-presence-list-adds-nobody", "entity.ivo_brandt" not in ents_quiet({}, me="noor"), str(ents_quiet({}, me="noor")))

    # ---- NEGATIVE CONTROL: no present key -> no presence fact at all, and channel unchanged.
    # Goes red if anyone makes the default strict, which would silently zero direct.py's edges.
    legacy = ents({})
    check("no-present-key-adds-no-fact",
          all("present" not in p for p in legacy.values()), str(legacy))
    check("no-present-key-keeps-visual",
          all(p["channel"] == "visual" for p in legacy.values()), str(legacy))

    # ---- the edge consequence, which is the whole point
    rels = {"noor": {"trust": 0.65}, "ivo_brandt": {"trust": 0.35}}
    with_presence = [e["target"] for e in
                     _build_edges({"relationships": rels}, list(ents({"present": ["noor"]}).values()), world)]
    without       = [e["target"] for e in
                     _build_edges({"relationships": rels}, list(legacy.values()), world)]
    check("referenced-takes-no-edge", with_presence == ["noor"], str(with_presence))
    # NEGATIVE CONTROL #2: the same relationship rows, the same text, edges DIFFER only because of
    # the present list. A guard hard-wired to "always present" cannot pass this pair.
    check("legacy-still-edges-both", sorted(without) == ["ivo_brandt", "noor"], str(without))


def main():
    print("test_gate.py — Gate 3 relevancy-gate machinery (split from test_scene.py)\n")
    test_absence_on_failed_check()
    test_identity_gating()
    test_energy_narrowing()
    test_trigger_wall()
    test_name_hygiene()
    test_acquaintance_recognition()
    test_referenced_is_not_present()

    total = len(PASS) + len(FAIL)
    print("\n--- summary ---")
    print("  %d / %d passed" % (len(PASS), total))
    if FAIL:
        print("  FAILED:")
        for f in FAIL:
            print("    " + f)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
