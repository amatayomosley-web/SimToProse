"""test_targets.py — per-primitive targets: what each feeling is ABOUT.

`docs/emotion-basis.md` is normative and prescribes this exact change:

    "So the model is {primitive -> (magnitude, target)}. Each primitive in a compound carries its
     own target."
    "This is a change to what exists, not an addition. `state.appraise` takes ONE `target` per
     EVENT... Per-primary targets move the target from the event onto the state, and `_regard`
     becomes a per-primitive evaluation."

Its motivating measurement is about SWE's own output and cites no vocabulary: the best shame
coordinate expressible by mixture alone is indistinguishable from grief-plus-fear, so **"a man who
just buried his brother and a man just publicly humiliated receive identical directions."**

Measured before the build, from two independent origins:
  * `src/engine/direction.py` — of the 32 stage directions, DISGUST's four all assume an object, so
    a self-bound DISGUST told the actor "you will not be in the room with it, and you say so on your
    way out". You cannot walk out of a room away from yourself.
  * `src/engine/state.py` — `subj_regard = _regard(profile, tags.get("target"), ...)`: one target
    for the whole event, and no field in which per-primitive aboutness could be stored even if a
    caller knew it.

THE REGISTRY IS UPSTREAM. `records.DIRECTEDNESS` is argued from what each Panksepp system makes a
body do, NOT from how often `compounds.py` happens to use a role — the owner's standing rule is that
downstream aligns to SWE and never the reverse. Following it caught two places the compound table
had already drifted FROM the basis, which `validate()["drift"]` now reports (group 6).

The law the registry encodes, so a ninth primitive does not re-litigate it: **a primitive needs its
own reflexive directions exactly when its action tendency becomes incoherent aimed at the self.**
Attack survives, shutdown survives (it never pointed), pursuit inverts to display, expulsion inverts
to concealment.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.compounds import COMPOUNDS, separability, validate         # noqa: E402
from src.engine.direction import _PHRASES, _REFLEXIVE_PHRASES, direct_affect  # noqa: E402
from src.engine.records import DIRECTEDNESS, PRIMARIES, admits_role        # noqa: E402
from src.engine.state import appraise, build_profile, decay                # noqa: E402
from src.engine.targets import retarget                                     # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _maren():
    ch = json.load(open(os.path.join(REPO, "characters", "maren-healer.json"), encoding="utf-8"))
    return ch, build_profile(ch), ch["baseline"]["temperament"]


def test_the_registry_is_upstream():
    print("\n[1] THE REGISTRY — one row per primitive, and it is the single source")
    check("covers-every-primitive", set(DIRECTEDNESS) == set(PRIMARIES),
          set(DIRECTEDNESS) ^ set(PRIMARIES))
    for p in PRIMARIES:
        row = DIRECTEDNESS[p]
        check("%s-is-complete" % p,
              set(row) == {"reflexive", "kinds", "direction_changes"} and row["kinds"], row)
    # THE LAW: variants exist exactly where the action tendency breaks under reflexivization
    need = sorted(p for p in PRIMARIES
                  if DIRECTEDNESS[p]["reflexive"] and DIRECTEDNESS[p]["direction_changes"])
    print("       admits reflexive AND direction changes: %s" % need)
    check("only-two-need-variants", need == ["DISGUST", "SEEKING"], need)
    check("and-exactly-those-have-them", sorted(_REFLEXIVE_PHRASES) == need, sorted(_REFLEXIVE_PHRASES))
    # PANIC_GRIEF is the point of separating the two columns
    check("PANIC_GRIEF-admits-reflexive", DIRECTEDNESS["PANIC_GRIEF"]["reflexive"])
    check("...but-needs-NO-variant", not DIRECTEDNESS["PANIC_GRIEF"]["direction_changes"],
          "its shutdown never pointed at anything — that is WHY all four of its phrases are posture")
    check("fails-closed-on-an-unknown-primitive", not admits_role("NOPE", "self"))
    check("beneficiary-is-CARE's-object", admits_role("CARE", "beneficiary")
          and not admits_role("CARE", "self"))
    check("self.act-is-an-object-bind", admits_role("PANIC_GRIEF", "self.act"))


def test_the_binding_rules():
    print("\n[2] BINDING — five rules, each with a reason")
    _, _, temp = _maren()
    t = retarget({}, {"dimensions": {"threat": 0.8}, "target": "wolf"}, me="maren")
    print("       threat about the wolf -> %s" % t)
    check("1-a-positive-push-binds-the-subject", t.get("FEAR") == "wolf", t)
    check("2-a-negative-push-never-binds", "PLAY" not in t,
          "threat pushes PLAY DOWN; a target on a suppression is meaningless")
    t = retarget(t, {"dimensions": {"social_violation": 0.8}, "target": "gerrold"}, me="maren")
    print("       then a violation by the man -> %s" % t)
    check("THE-SPEC'S-OWN-EXAMPLE", t.get("FEAR") == "wolf" and t.get("RAGE") == "gerrold",
          "fear of the wolf and rage at the man who let it in, in one state")
    t3 = retarget({"RAGE": "gerrold"},
                  {"dimensions": {"social_violation": 0.9}, "target": "maren"}, me="maren")
    print("       a violation SHE committed -> %s" % t3)
    check("3-reflexive-binds-where-admitted", t3.get("DISGUST") == "maren", t3)
    check("3-and-DROPS-the-bind-where-not", "RAGE" not in t3,
          "the magnitude still applies — shame plus irritability at the room, which is how "
          "humiliated people act")
    check("4-no-subject-leaves-binds-alone",
          retarget(t, {"dimensions": {"threat": 0.5}}, me="maren") == t)
    check("bad-tags-fail-loud", _raises(lambda: retarget({}, "nope")))


def test_a_bind_clears_when_the_feeling_does():
    print("\n[3] RULE 5 — aboutness with no feeling behind it is stale")
    ch, prof, temp = _maren()
    a = dict(ch["current"]["affect"])
    at_rest = retarget({"FEAR": "wolf"}, {"dimensions": {}},
                       temperament=temp, affect=a, me="maren")
    check("at-rest-the-bind-clears", "FEAR" not in at_rest, at_rest)
    spiked = dict(a, FEAR=0.95)
    check("while-elevated-it-holds",
          retarget({"FEAR": "wolf"}, {"dimensions": {}},
                   temperament=temp, affect=spiked, me="maren").get("FEAR") == "wolf")
    # the test that caught the first version: Maren RESTS at FEAR 0.62, so a quiet-band gate would
    # have meant her binds never cleared while a calm character's cleared normally
    print("       (Maren rests at FEAR %.2f — far above the 0.25 quiet band)" % temp["FEAR"]["mean"])
    check("a-high-resting-character-still-clears", "FEAR" not in at_rest,
          "absolute level is disposition; DEVIATION from your own mean is the response, and only a "
          "response can be about something")
    # end to end: spike, decay, bind releases itself
    t = retarget({}, {"dimensions": {"threat": 0.9}, "target": "wolf"}, me="maren")
    aa = decay(appraise(a, {"dimensions": {"threat": 0.9}}, prof, targets=t), temp, prof)
    beats = 0
    for beats in range(1, 15):
        aa = decay(aa, temp, prof)
        t = retarget(t, {"dimensions": {}}, temperament=temp, affect=aa, me="maren")
        if "FEAR" not in t:
            break
    print("       spike -> released after %d quiet beats (FEAR %.3f, mean %.2f)"
          % (beats, aa["FEAR"], temp["FEAR"]["mean"]))
    check("the-lifecycle-closes-itself", "FEAR" not in t and beats < 14, beats)


def test_shame_and_contempt_render_differently():
    print("\n[4] THE DEFECT, CLOSED — identical numbers, different instruction")
    ch, prof, temp = _maren()
    out = {}
    for subject, label in (("gerrold", "CONTEMPT"), ("maren", "SHAME")):
        a = dict(ch["current"]["affect"])
        t = {}
        tags = {"dimensions": {"social_violation": 0.9}, "durability": "durable", "target": subject}
        for _ in range(3):
            t = retarget(t, tags, temperament=temp, affect=a, me="maren")
            a = decay(appraise(a, tags, prof, targets=t), temp, prof)
        out[label] = (a, t, direct_affect(a, temp, targets=t, me="maren"))
    (ac, tc, dc), (as_, ts, ds) = out["CONTEMPT"], out["SHAME"]
    print("       DISGUST %.3f both; RAGE %.3f both" % (ac["DISGUST"], ac["RAGE"]))
    check("the-numbers-really-are-identical",
          abs(ac["DISGUST"] - as_["DISGUST"]) < 1e-9 and abs(ac["RAGE"] - as_["RAGE"]) < 1e-9,
          "if these diverge the test proves nothing — the whole point is same magnitudes, different aim")
    check("but-the-directions-differ", dc != ds)
    print("       contempt: %s" % dc.split("; ")[-1])
    print("       shame   : %s" % ds.split("; ")[-1])
    check("contempt-gets-the-object-phrase", _PHRASES["DISGUST"][2] in dc, dc[-90:])
    check("shame-gets-the-reflexive-one", _REFLEXIVE_PHRASES["DISGUST"][2] in ds, ds[-90:])
    check("shame-does-NOT-leave-the-room", "will not be in the room" not in ds,
          "the measured defect: you cannot walk out of a room away from yourself")
    check("RAGE-unbound-in-shame", "RAGE" not in ts and tc.get("RAGE") == "gerrold", (tc, ts))


def test_backwards_compatible():
    print("\n[5] NO TARGETS -> BYTE-IDENTICAL to the pre-targets engine")
    ch, prof, temp = _maren()
    a = dict(ch["current"]["affect"])
    tags = {"dimensions": {"social_violation": 0.7}, "durability": "durable", "target": "gerrold"}
    check("appraise-unchanged-without-targets",
          appraise(a, tags, prof) == appraise(a, tags, prof, targets=None))
    check("direct_affect-unchanged-without-targets",
          direct_affect(a, temp) == direct_affect(a, temp, targets=None, me=None))
    check("...and-with-targets-but-no-me",
          direct_affect(a, temp, targets={"DISGUST": "maren"}, me=None)
          == direct_affect(a, temp, targets={"DISGUST": "maren"}, me="someone-else"),
          "reflexivity is DERIVED from the bound id matching the character; with no character id "
          "there is nothing to derive it from, so it renders as an ordinary object bind")

    # NO TARGET MAP AT ALL IS NOT THE SAME INPUT AS A MAP THAT LEAVES A PRIMITIVE UNBOUND, and
    # these two checks used to assert that it was. `_phrase_for` has always encoded the
    # distinction — its unbound branch reads `bound is None and targets is not None` — because
    # supplying a map means the engine KNOWS nothing is aimed, which is different from not having
    # asked. The assertions survived only because the one primitive with unbound cover (LUST) sits
    # at band 0 in this fixture and the branch needs band >= 1: raise LUST to 0.60 and the code as
    # it stood in 2026-08-22 already fails them. Corrected to the contract the design states.
    check("an-object-bind-changes-nothing-for-the-BOUND-primitive",
          direct_affect(dict(a, DISGUST=0.60), temp, targets={"DISGUST": "gerrold"}, me="maren")
          == direct_affect(dict(a, DISGUST=0.60), temp, targets={"DISGUST": "wren"}, me="maren"),
          "who an object bind names must not change the words — only WHETHER it is the self does")
    check("an-unbound-primitive-under-a-map-is-covered",
          direct_affect(dict(a, LUST=0.60), temp)
          != direct_affect(dict(a, LUST=0.60), temp, targets={"DISGUST": "gerrold"}, me="maren"),
          "LUST live and unbound must take its unbound phrase — that is what the cover is FOR")


def test_regard_is_per_primitive():
    print("\n[6] _REGARD IS NOW A PER-PRIMITIVE EVALUATION (emotion-basis.md)")
    ch, prof, temp = _maren()
    prof = dict(prof, regard={"vermin": 0.0})
    a = dict(ch["current"]["affect"])
    tags = {"dimensions": {"care_relevant": 0.9}, "durability": "transient", "target": "kin"}
    scoped = appraise(a, tags, prof, targets={"CARE": "vermin"},
                      )["CARE"]
    plain = appraise(a, tags, prof, targets={"CARE": "kin"})["CARE"]
    print("       CARE pushed while pointed at a disregarded party: %.4f" % scoped)
    print("       ...and at an ordinary one:                        %.4f" % plain)
    check("the-bound-party-scopes-the-empathy", scoped < plain, (scoped, plain))
    check("but-never-to-zero", scoped > a["CARE"],
          "_CARE_FLOOR — you can train someone to believe a being does not count, not to feel "
          "nothing when it bleeds")


def test_the_drift_the_registry_caught():
    print("\n[7] THE REGISTRY IS ENFORCEABLE — and it caught downstream drift")
    v = validate()
    check("validate-reports-drift", "drift" in v)
    # It found 5 on the day it was written: jealousy binding FEAR reflexively (the basis says FEAR
    # of *the loss*, a prospect) and pride / spite / smug / passive_aggressive binding PLAY
    # reflexively (covertness is a delivery register, not aboutness — the `sarcastic` precedent).
    # All five were re-authored to object binds in gate `compound-drift-repair`. The check stays
    # because the NEXT drift is what it is for.
    print("       drift now: %s" % (sorted(v["drift"]) or "EMPTY"))
    check("the-table-now-conforms-to-the-basis", not v["drift"], sorted(v["drift"]))
    check("every-role-passes-the-registry",
          all(admits_role(p, r) for rec in COMPOUNDS.values() for p, (_w, r) in rec.items()))
    check("jealousy-fear-is-an-object", COMPOUNDS["jealousy"]["FEAR"][1] == "object",
          COMPOUNDS["jealousy"]["FEAR"])
    check("no-PLAY-is-reflexive",
          not [n for n, r in COMPOUNDS.items() if r.get("PLAY", (0, ""))[1] == "self"],
          [n for n, r in COMPOUNDS.items() if r.get("PLAY", (0, ""))[1] == "self"])
    check("pride-keeps-its-reflexive-SEEKING", COMPOUNDS["pride"]["SEEKING"][1] == "self",
          "the basis licenses SEEKING-satisfied(self); only the PLAY bind was wrong")
    # the repair must not have created a duplicate — measured, not assumed
    worst = sorted(separability(), key=lambda t: -t[2])[0]
    print("       closest pair after the repair: %s~%s %.3f" % worst)
    check("no-duplicate-was-created", worst[2] < 0.99, "%s~%s %.3f" % worst)
    check("passive_aggressive-survived-as-a-shade", "passive_aggressive" in COMPOUNDS,
          "predicted to possibly collapse into `mocking`; measured 0.962, inside the shade band "
          "decision-engine.md deliberately populates — kept on the measurement, not the prediction")


def _raises(fn):
    try:
        fn()
        return False
    except ValueError:
        return True


def main():
    print("test_targets.py — per-primitive targets: what each feeling is ABOUT")
    for t in (test_the_registry_is_upstream, test_the_binding_rules,
              test_a_bind_clears_when_the_feeling_does, test_shame_and_contempt_render_differently,
              test_backwards_compatible, test_regard_is_per_primitive,
              test_the_drift_the_registry_caught):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
