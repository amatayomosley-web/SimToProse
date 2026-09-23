"""test_rung_delivery.py — the rung block actually reaches the actor, and nothing else moved.

WHAT THIS CLOSES. Until 2026-09-08 the emotion ladders reached no actor at all. `rungs.rung_at` and
`rungs.block_for` were built, `composer.selectable` computed rows carrying the block text, and
`composer.direction_for` assembled the actor-facing wording — and NOTHING CALLED ANY OF IT.
`build_turn_messages` staged the actor's state from `direction.direct_affect` alone, so the ladder
and the prompt were two parallel renderings of the same affect vector with only the thin one
connected. `grep -c rung scripts/direct.py` returned 0.

WHAT IT ASSERTS, and each is a way the seam could be wired and still be wrong:
  1. the block arrives VERBATIM — not paraphrased, not truncated, not re-wrapped;
  2. it arrives UNDER direction_for's lead, so the actor is told it is a state and not an
     instruction — the wording that every 2026-09-08 sim was validated against;
  3. the DEFAULT is byte-identical to the pre-rung engine, so every existing caller is unaffected;
  4. NO DIGIT enters the prompt through the new path (CLAUDE.md hard rule 5) — the ladder carries a
     rung INDEX and a rung NAME, and neither may reach an actor;
  5. the rung NAME does not reach the actor either. Measured 2026-09-07: the label is inert, and
     identical text under a WRONG label scored higher than under its own. `direction_for` attaches
     `block` and never `name`; this asserts that stays true through the whole seam.
  6. SELECTION IS DETERMINISTIC — the same packet composes the same prompt twice (hard rule 4).

WHAT IT DOES NOT ASSERT, and the distinction is the point: this proves DELIVERY, not FIDELITY.
Every block validated on 2026-09-08 was delivered ALONE, in a neutrally-named file, with no other
state text around it. Composed alongside the stage-direction line, recall, edges and sureness it is
a DIFFERENT STIMULUS, and whether it still moves an actor there is a separate measurement.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine.prompt import build_turn_messages        # noqa: E402
from src.engine import rungs                             # noqa: E402
from src.engine.records import PATHS                     # noqa: E402
import composer as C                                     # noqa: E402

_PATHS = PATHS                       # DERIVED - see tests/test_cut.py


def _packet(affect):
    return {
        "stable": {"persona": {"id": "a", "name": "A"}},
        "volatile": {
            "state": {"affect": affect,
                      "condition": {"energy": 0.5, "allostatic_load": 0.2}},
            "goals": [{"goal": "g", "urgency": 0.5}],
            "percepts": [{"ref": "p.1", "channel": "visual", "attributes": ["x"], "fidelity": 0.9}],
            "recall": [{"claim": "c", "confidence": 0.8, "provenance": "seen"}],
            "edges": [{"label": "B", "target": "b", "trust": 0.5,
                       "affinity": 0.5, "respect": 0.5, "debt": 0.5}],
        },
    }


def _temperament():
    return {p: {"mean": 0.3, "variability": 0.1} for p in _PATHS}


def _usr(affect, rung_direction=None):
    return build_turn_messages(_packet(affect), "the moment", _temperament(),
                               rung_direction=rung_direction)[1]["content"]


def _hot():
    """An affect vector that puts at least one BUILT path well above its floor."""
    a = {p: 0.10 for p in _PATHS}
    a["DISPLEASURE"] = 0.62
    a["GOODWILL"] = 0.41
    return a


def _compose(affect):
    rows = C.selectable(affect)
    return rows, C.direction_for(rows, C.select_deterministic(rows))


def test_block_arrives_verbatim():
    affect = _hot()
    rows, text = _compose(affect)
    assert rows, "no built path reads this affect — fixture is not exercising the seam"
    usr = _usr(affect, text)
    for r in rows:
        if r["path"] == "DISPLEASURE":
            assert r["block"] in usr, "the DISPLEASURE block did not arrive verbatim in the prompt"
            break
    else:
        raise AssertionError("DISPLEASURE not selectable at RAGE 0.62 — fixture drifted")
    print("  PASS  the block arrives verbatim in the actor's user message")


def test_arrives_as_a_state_not_an_instruction():
    affect = _hot()
    _, text = _compose(affect)
    usr = _usr(affect, text)
    lead = ("This is what is true inside you; it is not a list of actions and it does not tell you "
            "what to do. Act from it.")
    assert lead in usr, "the block arrived without direction_for's lead — the actor is not told it is a state"
    print("  PASS  it arrives under the state lead, not as an instruction")


def test_default_is_unchanged():
    affect = _hot()
    assert _usr(affect, None) == _usr(affect), "the default changed the prompt"
    _, text = _compose(affect)
    assert _usr(affect, text) != _usr(affect, None), "passing a direction changed nothing"
    print("  PASS  default is byte-identical to the pre-rung prompt; the seam is additive")


def test_no_digit_and_no_rung_name_reach_the_actor():
    affect = _hot()
    rows, text = _compose(affect)
    assert not any(ch.isdigit() for ch in text), "a digit reached the direction (hard rule 5)"
    usr = _usr(affect, text)
    for r in rows:
        assert r["name"] not in text, (
            "the rung name %r reached the actor — measured inert 2026-09-07, and identical text "
            "under a WRONG label scored higher than under its own" % r["name"])
    assert isinstance(usr, str) and usr
    print("  PASS  no digit and no rung name reach the actor")


def test_selection_is_deterministic():
    affect = _hot()
    a = C.select_deterministic(C.selectable(affect))
    b = C.select_deterministic(C.selectable(affect))
    assert a == b, "the same affect selected differently twice (hard rule 4)"
    assert a["selected"][0]["primary"] is True, "no primary marked"
    assert sum(1 for r in a["selected"] if r["primary"]) == 1, "more than one primary"
    assert len(a["selected"]) <= 3, "direction_for takes at most three"
    print("  PASS  selection is deterministic, capped, exactly one primary")


def test_quiet_affect_composes_nothing():
    """A character no built ladder reads must not get an EMPTY state section - it must get none.

    The principle is unchanged; what satisfies it is. Until 2026-09-08 a quiet character composed a
    well-formed direction out of FLOOR rungs, on the reasoning that a floor rung is a real state.
    It is a real READING and a wrong stage direction: measured, an all-zero vector and one with LUST
    at 0.95 both delivered DISTASTE 1, DEFLATION 1 and GOODWILL 1 - identical text for two entirely
    different characters, describing mild distaste, deflation and fondness to someone in none of
    those states. `select_deterministic` now drops floor rungs, so a quiet character composes
    NOTHING and `build_turn_messages` emits no state section at all.
    """
    quiet = {p: 0.02 for p in _PATHS}
    rows = C.selectable(quiet)
    sel = C.select_deterministic(rows)
    assert sel["selected"] == [], "a quiet character selected %r" % (sel["selected"],)
    assert C.direction_for(rows, sel) == "", "empty selection still composed text"
    print("  PASS  a quiet character composes nothing (every row is at its ladder floor)")


def test_no_floor_rung_ever_reaches_an_actor():
    """The filter is the point, so prove it holds across the whole range and not just when quiet.

    A floor rung block must never appear in a composed direction, at any affect vector. This is the
    guard that would catch the padding coming back: before the filter, a vector with ONE elevated
    primary still shipped two floor blocks alongside it to fill the cap of three.
    """
    from src.engine.rung_blocks import BLOCKS
    floors = {path: BLOCKS[path][1] for path in BLOCKS}
    bad = []
    for probe in list(_PATHS) + [None]:
        v = {p: 0.0 for p in _PATHS}
        if probe:
            v[probe] = 0.95
        rows = C.selectable(v)
        text = C.direction_for(rows, C.select_deterministic(rows))
        for path, block in floors.items():
            if block and block in text:
                bad.append((probe or "all-zero", path))
    assert not bad, "floor block reached the actor: %r" % (bad[:4],)
    print("  PASS  no floor rung reaches an actor, across %d probe vectors"
          % (len(_PATHS) + 1))


def test_one_elevated_primary_ships_alone():
    """Padding the cap is not neutral. A character elevated on exactly one primary must receive that
    one block and nothing else - not it plus two floor states they are not in."""
    v = {p: 0.0 for p in _PATHS}
    v["DISPLEASURE"] = 0.95
    rows = C.selectable(v)
    sel = C.select_deterministic(rows)
    paths = [r["path"] for r in sel["selected"]]
    assert paths == ["DISPLEASURE"], "expected DISPLEASURE alone, got %r" % (paths,)
    print("  PASS  a single elevated primary ships alone (no floor padding)")


# ---------------------------------------------------------------------------------------------------
# THE DIRECTION IS RECORDED (gate composer-direction-recorded, 2026-09-22). `direct.rung_direction`
# writes what it sent into the packet's manifest, which both drivers commit with the turn. The model
# is faked at the transport (`direct._openrouter`), so the real composer prompt, `verify`, the
# fallback and the retry loop all run.
# ---------------------------------------------------------------------------------------------------
def _direct():
    import direct
    return direct


def _mpacket(affect, descending=None):
    p = _packet(affect)
    p["manifest"] = {}
    if descending is not None:
        p["volatile"]["state"]["descending"] = descending
    return p


def _faked(composer=(), actor=()):
    """Script `direct._openrouter`: composer calls (max_tokens=700) and actor calls pop their own queue.
    -> (queues, restore)."""
    import json as _json
    d = _direct()
    real = d._openrouter
    q = {"composer": list(composer), "actor": list(actor)}

    def fake(messages, model, max_tokens=750):
        item = q["composer" if max_tokens == 700 else "actor"].pop(0)
        return item if isinstance(item, str) else _json.dumps(item)
    d._openrouter = fake
    return q, (lambda: setattr(d, "_openrouter", real))


def _in_order(selected):
    return sorted(selected, key=lambda s: (not s.get("primary"), s["path"]))


def test_the_floor_direction_is_recorded_as_refs():
    import json as _json
    d = _direct()
    affect = _hot()
    pk = _mpacket(affect)
    text = d.rung_direction(pk)                                    # no brief: the deterministic floor
    rec = pk["manifest"].get("direction")
    rows = C.selectable(affect)
    want = _in_order(C.select_deterministic(rows)["selected"])
    assert rec and rec["by"] == "floor" and rec["fell_back"] == "" and rec["about"] == "", rec
    assert rec["offered"] == {r["path"]: r["name"] for r in rows}, rec["offered"]
    assert [(s["path"], s["index"], s["primary"]) for s in rec["selected"]] == \
        [(s["path"], s["rung"], s["primary"]) for s in want], (rec["selected"], want)
    for s in rec["selected"]:
        assert s["rung"] == rungs.rung_at(s["path"], affect[s["path"]])[1], s
        assert s["block"] == C._digest(rungs.block_for(s["path"], s["index"], descending=s["descending"])), s
        assert rungs.block_for(s["path"], s["index"]) not in _json.dumps(rec), "block prose was stored"
    assert text and rec["text"] == C._digest(text), "the text hash does not pin what the actor received"
    print("  PASS  the floor's direction is recorded as refs: rung names, block hashes, the text hash")


def test_the_descent_block_is_recorded_as_the_one_sent():
    from src.engine.rung_blocks import BLOCKS
    d = _direct()
    hit = next(((p, i) for p in sorted(BLOCKS) for i in range(1, len(BLOCKS[p]))
                if rungs.block_for(p, i, descending=True) != rungs.block_for(p, i)), None)
    assert hit, "no authored descent block to test against"
    path, idx = hit
    affect = {p: 0.02 for p in _PATHS}
    affect[path] = next(v / 1000.0 for v in range(1001) if rungs.rung_at(path, v / 1000.0)[0] == idx)
    pk = _mpacket(affect, descending={path: True})
    d.rung_direction(pk)
    s = next(s for s in pk["manifest"]["direction"]["selected"] if s["path"] == path)
    assert s["descending"] is True and s["block"] == C._digest(rungs.block_for(path, idx, descending=True)), s
    assert s["block"] != C._digest(rungs.block_for(path, idx)), "the climb block's hash was recorded"
    print("  PASS  a descending path records the DESCENT block it was sent (%s rung %d)" % (path, idx))


def test_the_composers_selection_is_recorded_with_its_about():
    d = _direct()
    affect = _hot()
    rows = C.selectable(affect)
    top = [r for r in rows if r["rung"] > 1][:2]
    reply = {"selected": [{"path": top[0]["path"], "rung": top[0]["rung"], "primary": True},
                          {"path": top[1]["path"], "rung": top[1]["rung"]}],
             "about": "the split cart wheel"}
    q, restore = _faked(composer=[reply])
    try:
        pk = _mpacket(affect)
        d.rung_direction(pk, brief="the cart wheel has split", model="fake/model")
    finally:
        restore()
    rec = pk["manifest"]["direction"]
    assert not q["composer"], "the composer was never asked"
    assert rec["by"] == "composer" and rec["fell_back"] == "" and rec["about"] == "the split cart wheel", rec
    assert [(s["path"], s["index"]) for s in rec["selected"]] == \
        [(s["path"], s["rung"]) for s in _in_order(reply["selected"])], rec["selected"]
    print("  PASS  a verified composer selection is recorded, by=composer, with its about")


def test_a_composer_refusal_is_recorded_as_the_fallback():
    d = _direct()
    affect = _hot()
    rows = C.selectable(affect)
    r0 = [r for r in rows if r["rung"] > 1][0]
    bad = {"selected": [{"path": r0["path"], "rung": r0["rung"] + 1, "primary": True}], "about": ""}
    q, restore = _faked(composer=[bad])
    try:
        pk = _mpacket(affect)
        d.rung_direction(pk, brief="the cart wheel has split", model="fake/model")
    finally:
        restore()
    rec = pk["manifest"]["direction"]
    assert rec["by"] == "floor" and rec["fell_back"].startswith("ComposerError"), rec
    assert [s["path"] for s in rec["selected"]] == \
        [s["path"] for s in _in_order(C.select_deterministic(rows)["selected"])], rec["selected"]
    print("  PASS  a refused composer reply is recorded: by=floor, the refusal named in fell_back")


def test_no_affect_records_why_no_direction_was_built():
    d = _direct()
    pk = _mpacket(None)
    pk["volatile"]["state"].pop("affect")
    assert d.rung_direction(pk) is None
    assert pk["manifest"]["direction"] == {"by": "none", "why": "the packet carries no affect"}, pk["manifest"]
    print("  PASS  no direction built -> by=none with the reason")


def test_a_retry_records_the_attempt_that_was_kept():
    d = _direct()
    affect = _hot()
    rows = C.selectable(affect)
    top = [r for r in rows if r["rung"] > 1][:2]
    first = {"selected": [{"path": top[0]["path"], "rung": top[0]["rung"], "primary": True}], "about": "first"}
    second = {"selected": [{"path": top[1]["path"], "rung": top[1]["rung"], "primary": True}], "about": "second"}
    kept = {"action": "He sweeps the step twice.", "thought": "", "tags": {"dimensions": {}}}
    q, restore = _faked(composer=[first, second], actor=["{}", kept])     # an empty draw is resampled
    try:
        pk = _mpacket(affect)
        turn, leaks = d.faithful_turn(pk, "the moment", _temperament(), "fake/model", False,
                                      relationships={}, brief="the cart wheel has split")
    finally:
        restore()
    rec = pk["manifest"]["direction"]
    assert turn["action"] == kept["action"] and not leaks and not q["composer"] and not q["actor"], (turn, q)
    assert rec["about"] == "second" and [s["path"] for s in rec["selected"]] == [top[1]["path"]], rec
    print("  PASS  across a retry the manifest holds the direction of the attempt that was returned")


def test_the_record_is_committed_with_the_turn():
    import json as _json
    import sqlite3 as _sq
    from src.engine.ledger import Ledger
    from src.engine.records import TurnCommit
    d = _direct()
    pk = _mpacket(_hot())
    d.rung_direction(pk)
    led = Ledger(":memory:")
    led.create_run("r1", {"catalog_version": 1, "models": {"turn": "stub"}, "prompt_versions": {"turn": 1}})
    led.append_turn(TurnCommit(run_id="r1", turn=0, actor="a", thought="t", action="x", tags={"type": "mundane"},
                               affect={p: 0.5 for p in _PATHS}, events=[], manifest=pk["manifest"]))
    row = led.con.execute("SELECT manifest FROM decision_manifests WHERE run_id='r1' AND turn=0").fetchone()
    assert row and _json.loads(row[0])["direction"] == pk["manifest"]["direction"], row
    for name in ("direct.py", "scene.py"):
        src = open(os.path.join(REPO, "scripts", name), encoding="utf-8").read()
        assert 'manifest=packet["manifest"]' in src, "%s no longer commits the packet's manifest" % name
    print("  PASS  the record rides the turn's commit into decision_manifests, in both drivers")


def main():
    print("test_rung_delivery.py - the rung block reaches the actor\n")
    fails = 0
    for fn in (test_block_arrives_verbatim,
               test_arrives_as_a_state_not_an_instruction,
               test_default_is_unchanged,
               test_no_digit_and_no_rung_name_reach_the_actor,
               test_selection_is_deterministic,
               test_quiet_affect_composes_nothing,
               test_no_floor_rung_ever_reaches_an_actor,
               test_one_elevated_primary_ships_alone,
               test_the_floor_direction_is_recorded_as_refs,
               test_the_descent_block_is_recorded_as_the_one_sent,
               test_the_composers_selection_is_recorded_with_its_about,
               test_a_composer_refusal_is_recorded_as_the_fallback,
               test_no_affect_records_why_no_direction_was_built,
               test_a_retry_records_the_attempt_that_was_kept,
               test_the_record_is_committed_with_the_turn):
        try:
            fn()
        except AssertionError as exc:
            fails += 1
            print("  FAIL  %s: %s" % (fn.__name__, exc))
    print("\nVERDICT: %s" % ("PASS" if not fails else "FAIL (%d)" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
