"""test_directedness.py — can a feeling be about the character who has it?

`docs/emotion-arithmetic.md` §5 step 3 requires a PATH-keyed DIRECTEDNESS. Until 2026-09-09 the
table was still keyed to the eight retired Panksepp primitives, and `records.admits_role` fails
closed on an unknown key (`records.py` `admits_role`), so **every** path refused a reflexive bind.
Nothing raised. Three paths that used to admit one — DISTASTE, DEFLATION, STIRRING, via DISGUST,
PANIC_GRIEF and SEEKING — lost it to a lookup miss rather than to a decision.

WHY THE TEST IS KEYED OFF `records.PATHS` AND NOT A LIST OF NAMES. That is the whole defect: a
hand-written list is what rotted, and CLAUDE.md tabulates seven instances of the same class. If a
future rename moves the basis again, this suite fails loudly on the missing row instead of quietly
returning False for everyone.

THE OWNER'S RULING, 2026-09-09: every path admits self, and NO reflexive stage directions are
authored. The 83 rung blocks were written to be universal, so a block aimed inward is the actor's
application of prose that already works — not a second block. `direction_changes` therefore stays
False on every row, and this suite asserts that rather than leaving it as an accident.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import records                                    # noqa: E402
from src.engine.records import PATHS, DIRECTEDNESS, admits_role   # noqa: E402
from src.engine.targets import retarget                           # noqa: E402

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    (PASS if ok else FAIL).append(name)


def test_every_path_has_a_row():
    print("\n[1] THE TABLE IS KEYED TO THE LIVE BASIS")
    missing = [p for p in PATHS if p not in DIRECTEDNESS]
    check("every-path-in-PATHS-has-a-row", not missing, missing)
    stale = [k for k in DIRECTEDNESS if k not in PATHS]
    check("no-row-names-a-path-that-does-not-exist", not stale, stale)
    check("the-counts-match", len(DIRECTEDNESS) == len(PATHS),
          "%d rows vs %d paths" % (len(DIRECTEDNESS), len(PATHS)))


def test_every_path_admits_self():
    print("\n[2] THE RULING — every path may be about the one who has it")
    for p in PATHS:
        check("%s-admits-self" % p, admits_role(p, "self"))
    check("...and-object-too", all(admits_role(p, "object") for p in PATHS))


def test_no_reflexive_stage_directions():
    print("\n[3] NO SECOND BLOCK — the actor applies the one that exists")
    changed = [p for p in PATHS if DIRECTEDNESS[p].get("direction_changes")]
    check("direction_changes-is-False-everywhere", not changed, changed)


def test_the_fail_closed_path_still_fails_closed():
    print("\n[4] CONTROL — the refusal still works where it should")
    check("an-unknown-name-is-refused", admits_role("PANIC_GRIEF", "self") is False,
          "a retired primitive must not resolve")
    check("a-nonsense-name-is-refused", admits_role("BANANA", "self") is False)
    check("an-unknown-role-is-refused", admits_role("DISTASTE", "banana") is False)


def test_ren_can_be_disgusted_with_himself():
    """The USER-OBSERVABLE half. Ren does something shameful; the log must record that the disgust
    is about REN, not drop the bind and leave the actor told he is disgusted at nothing."""
    print("\n[5] THE USER-OBSERVABLE CASE — shame binds")
    tags = {"dimensions": {"social_violation": 0.8}, "target": "ren"}
    temp = {p: {"mean": 0.20} for p in PATHS}
    aff = dict({p: 0.20 for p in PATHS}, DISPLEASURE=0.80, DISTASTE=0.70)

    mine = retarget({}, tags, temp, aff, me="ren")
    check("DISTASTE-binds-to-himself", mine.get("DISTASTE") == "ren", mine)
    check("DISPLEASURE-binds-to-himself", mine.get("DISPLEASURE") == "ren", mine)

    # the control: the SAME event aimed at someone else must be unchanged
    theirs = retarget({}, dict(tags, target="joss_apprentice"), temp, aff, me="ren")
    check("the-other-directed-case-is-unchanged",
          theirs.get("DISTASTE") == "joss_apprentice" and theirs.get("DISPLEASURE") == "joss_apprentice", theirs)

    # rule 5 still governs: a path back at its own mean is about nobody, self or not
    at_rest = retarget({}, tags, temp, {p: 0.20 for p in PATHS}, me="ren")
    check("a-spent-feeling-is-about-nobody", at_rest == {}, at_rest)


def main():
    for t in (test_every_path_has_a_row,
              test_every_path_admits_self,
              test_no_reflexive_stage_directions,
              test_the_fail_closed_path_still_fails_closed,
              test_ren_can_be_disgusted_with_himself):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("VERDICT: FAIL -> %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
