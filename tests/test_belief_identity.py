"""test_belief_identity.py — a recorded belief reference must still name that belief tomorrow.

WHY. The gate's only handle on a belief was `vault[N]`, its POSITION in the character's vault list,
and `scene.assemble` wrote that string into `recall_events` — a table the schema-v9 triggers refuse
to UPDATE or DELETE. Add one bullet above an entry and every stored reference below it names a
different belief, permanently, in a table that cannot be corrected.

This is not hypothetical. Measured 2026-08-30: the Beck Hollow chronicle spans two bible
fingerprints, so its stored `vault[2]` strings are ALREADY ambiguous across the note edit between
them. And the defect was invisible for a second reason worth recording — a survey of recall
variance derived each character's VAULT SIZE from the highest index that appeared in
`recall_events`, which can only ever show what was recalled. By that circular measure Nell had four
beliefs. She has six. The two that never surfaced in fourteen recall events were her theory of Tam
and her wound-earned wisdom: the two beliefs that constitute her arc.

Run: python tests/test_belief_identity.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from src.engine.gate import belief_id, run_gate                      # noqa: E402

_FAILS = []


def check(name, cond, detail=""):
    if not cond:
        _FAILS.append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  - " + detail) if (detail and not cond) else ""))


CLAIM = "The man with the dogs killed a wolf on the fell road with a bill-hook."


def test_identity_is_content_not_position():
    """THE POINT. The same belief at a different index keeps its id; the index does not."""
    print("\n[1] content, not position")
    vault_before = [{"claim": CLAIM, "confidence": 0.8}]
    vault_after = [{"claim": "A newly authored bullet, inserted above.", "confidence": 0.9},
                   {"claim": CLAIM, "confidence": 0.8}]
    before = belief_id(vault_before[0])
    after = belief_id(vault_after[1])
    check("survives-an-insert-above", before == after, "%s != %s" % (before, after))
    check("position-did-move", vault_before.index(vault_before[0]) != vault_after.index(vault_after[1]),
          "the fixture must actually move the belief, or this test proves nothing")


def test_trivial_edits_do_not_forge_a_new_belief():
    """An author recasing or reflowing a line has not changed what the character believes."""
    print("\n[2] trivial edits")
    base = {"claim": CLAIM}
    check("case-insensitive", belief_id(base) == belief_id({"claim": CLAIM.upper()}))
    check("whitespace-collapsed",
          belief_id(base) == belief_id({"claim": "  " + CLAIM.replace(" ", "  ") + "  "}))
    check("newline-collapsed",
          belief_id(base) == belief_id({"claim": CLAIM.replace(" on ", "\non ")}))


def test_a_changed_claim_is_a_different_belief():
    """The other half. A claim whose WORDS changed is a different thing to have believed — which is
    what the monotonic-add vault and the append-only log both say."""
    print("\n[3] a changed claim is a new belief")
    a = belief_id({"claim": CLAIM})
    b = belief_id({"claim": CLAIM.replace("killed", "did not kill")})
    check("negation-is-a-different-id", a != b, "%s == %s" % (a, b))
    check("ids-are-stable-strings", a.startswith("b:") and len(a) == 14, a)


def test_identity_is_stable_across_processes():
    """hashlib, never Python's salted hash(). A per-process id in an append-only table would be
    worse than a positional one — it would look stable and not be."""
    print("\n[4] stable across processes")
    import subprocess
    code = ("import sys; sys.path.insert(0, %r);"
            "from src.engine.gate import belief_id;"
            "print(belief_id({'claim': %r}))" % (REPO, CLAIM))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         cwd=REPO).stdout.strip()
    check("same-id-in-a-fresh-interpreter", out == belief_id({"claim": CLAIM}),
          "%r vs %r" % (out, belief_id({"claim": CLAIM})))


def test_the_gate_stamps_it_on_every_candidate():
    """It has to reach the recorded row, or it is an authored-but-inert field — the defect class
    this repo keeps shipping."""
    print("\n[5] it reaches the candidate")
    vault = [{"claim": "the wolf came down the fell road", "confidence": 0.9},
             {"claim": "the mill race must be kept clear", "confidence": 0.8}]
    out = run_gate(["wolf", "race"], vault, {}, [], {"energy": 1.0, "allostatic_load": 0.0})
    check("gate-returned-candidates", bool(out), str(out))
    for e in out:
        check("candidate-carries-bid:%s" % e.get("ref"), bool(e.get("bid")), str(e))
        check("bid-matches-its-claim:%s" % e.get("ref"),
              e.get("bid") == belief_id({"claim": e.get("claim", "")}), str(e))


def test_the_old_rows_are_documented_as_unrecoverable():
    """NOT a behaviour test — a written record. recall_events refuses UPDATE and DELETE (schema v9),
    so rows already written with only a positional ref cannot be back-filled. They stay resolvable
    only against the note revision that produced them. Rebuilding the table to migrate them would
    break the very guarantee this identity exists to serve, so it is deliberately not done."""
    print("\n[6] the rows already written")
    schema = open(os.path.join(REPO, "src", "engine", "schema.sql"), encoding="utf-8").read()
    check("recall_events-still-refuses-update", "recall_events_no_update" in schema)
    check("recall_events-still-refuses-delete", "recall_events_no_delete" in schema)


def main():
    print("test_belief_identity.py - a recorded reference must still name its belief tomorrow")
    for t in (test_identity_is_content_not_position,
              test_trivial_edits_do_not_forge_a_new_belief,
              test_a_changed_claim_is_a_different_belief,
              test_identity_is_stable_across_processes,
              test_the_gate_stamps_it_on_every_candidate,
              test_the_old_rows_are_documented_as_unrecoverable):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
