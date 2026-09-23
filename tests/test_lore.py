"""test_lore.py — the lore licence: the fence in the packet, the licence in the prompt, the ruling
seat at the canon gate (2026-09-11; owner: "I legitimately want them to make up lore in their
turns, but only when that specific info isn't established").

  1. THE FENCE. `read_api.established` returns, per subject, the authored line and the KEPT
     sayings (tiers authored/established), and marks a subject with neither OPEN. A superposed
     claim is not a fact; a fiction ruling removes a saying from the fence.
  2. THE PACKET carries it (`volatile.established`) and the manifest names the subjects.
  3. THE PROMPT renders the fence in its own section, the old prohibition is gone, the licence
     line is present, and an open subject is named as the actor's ground.
  4. THE RULING. `apply_rulings` writes established/fiction through `claims.resolve`, leaves
     superposed alone, refuses an unknown utterance and an unknown verdict; the stub pass rules
     nothing and counts the contested pairs; a kept ruling reaches the next packet as a fact.

Stdlib only. Exit 0 = all pass.
"""
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "tests"))

import keeper                                                  # noqa: E402
import test_scene as TS                                        # noqa: E402  (the packet fixtures)
from src.engine import claims, read_api                        # noqa: E402
from src.engine.ledger import Ledger                           # noqa: E402
from src.engine.prompt import build_turn_messages, direct_established   # noqa: E402
from src.engine.records import PATHS, TurnCommit               # noqa: E402
from src.engine.scene import assemble                          # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _led(tmp):
    led = Ledger(os.path.join(tmp, "lore.db"))
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    for cid in ("maren", "cobb"):
        led.register_character("r1", cid, {"name": cid.title()}, {"temperament": "authored"})
    rows = (("maren", "The mill burned the winter my mother died.", [{"subject": "mill", "predicate": "burned", "object": "the winter my mother died"}]),
            ("cobb", "The mill has never burned. My father raised it and it stands.", [{"subject": "mill", "predicate": "burned", "object": "never"}]),
            ("maren", "Cobb keeps the ledger at the mill.", [{"subject": "cobb", "predicate": "keeps", "object": "the ledger at the mill"}]))
    for t, (who, said, ex) in enumerate(rows):
        led.append_turn(TurnCommit(run_id="r1", turn=t, actor=who, thought="t%d" % t, action='"%s"' % said,
                                   tags={"type": "mundane"}, affect={p: 0.3 for p in PATHS}, events=[]))
        # AS THE NOTICING PASS RECORDS THEM: the verbatim line with its extracted facts. A line
        # committed with the turn carries no extracts and is invisible to the fence until then.
        claims.record(led.con, "r1", t, who, said, ex)
    return led


def _uid(led, contains):
    for u in claims.for_run(led.con, "r1"):
        if contains in u["text"]:
            return u["id"]
    raise AssertionError("no utterance containing %r" % contains)


def test_the_fence(tmp):
    print("\n[1] THE FENCE — what is established, per subject")
    led = _led(tmp)
    res = read_api.established(led.con, "r1", ["mill", "cobb", "ferry"], as_of=2)
    rows = {r["subject"]: r for r in res.rows}
    check("one-row-per-subject-in-order", [r["subject"] for r in res.rows] == ["mill", "cobb", "ferry"], res.rows)
    check("a-superposed-claim-is-not-a-fact", rows["mill"]["kept"] == [] and rows["mill"]["open"], rows["mill"])
    check("an-unknown-subject-is-open", rows["ferry"]["open"] and not rows["ferry"]["authored"], rows["ferry"])
    uid = _uid(led, "never burned")
    claims.resolve(led.con, "r1", uid, 2, claims.ESTABLISHED, "the world can afford a standing mill")
    rows = {r["subject"]: r for r in read_api.established(led.con, "r1", ["mill"], as_of=2).rows}
    check("a-kept-saying-becomes-the-fence", rows["mill"]["kept"] == ["The mill has never burned. My father raised it and it stands."]
          and not rows["mill"]["open"], rows["mill"])
    claims.resolve(led.con, "r1", uid, 3, claims.FICTION, "retracted")
    rows = {r["subject"]: r for r in read_api.established(led.con, "r1", ["mill"], as_of=3).rows}
    check("a-fiction-ruling-leaves-the-fence", rows["mill"]["kept"] == [] and rows["mill"]["open"], rows["mill"])
    check("the-trace-names-the-open-subject", any("OPEN" in s for s in res.trace), res.trace)


def test_the_packet_and_the_prompt():
    print("\n[2/3] THE PACKET CARRIES IT; THE PROMPT RENDERS THE LICENCE")
    ch, w = TS._char(), TS._world()
    af, cond = TS._flat_affect(), ch["current"]["condition"]
    est = [{"subject": "loc.mill", "authored": "the mill on the fold, three storeys of grey stone", "kept": ['"the miller keeps a ledger"'], "open": False},
           {"subject": "ferry", "authored": "", "kept": [], "open": True}]
    p = assemble(ch, w, TS._fever_ss(), af, cond, established=est)
    check("volatile-carries-the-rows", p["volatile"]["established"] == est)
    check("the-manifest-names-the-subjects", p["manifest"]["established"] == ["loc.mill", "ferry"], p["manifest"].get("established"))
    p0 = assemble(ch, w, TS._fever_ss(), af, cond)
    check("absent-it-is-empty-not-missing", p0["volatile"]["established"] == [] and p0["manifest"]["established"] == [])
    temperament = {q: {"mean": 0.3, "variability": 0.1} for q in PATHS}
    usr = build_turn_messages(p, "the fever climbs", temperament)[1]["content"]
    i = usr.index("What is established about who and what is here")
    section = usr[i:usr.index("Those present, as you stand with them:")]
    check("the-fence-is-in-its-own-section", "three storeys of grey stone" in section and "the miller keeps a ledger" in section, section[:200])
    check("an-open-subject-is-named-as-the-actors-ground", "Nothing is yet established about ferry" in section and "that ground is yours" in section, section[-160:])
    check("the-licence-is-there", "speak as someone who knows their world" in usr and "binds nothing until it is kept" in usr)
    check("the-prohibition-is-gone", "do not invent people, outcomes, or WORLD facts" not in usr)
    check("the-two-fences-that-stay", "put no one new in the room" in usr and "decide nothing for anyone else" in usr)
    check("no-rows-reads-as-nothing-established", direct_established([]) == "nothing about anyone or anything here")


def test_the_ruling(tmp):
    print("\n[4] THE RULING SEAT — verdicts written, superposed left, invention refused")
    led = _led(tmp)
    a, b = _uid(led, "burned the winter"), _uid(led, "never burned")
    gate = keeper.canon_gate(led, "r1", 0, 2, "subagent:none", True, log=lambda *_: None)
    stub = gate["ruled"]
    check("the-stub-gate-notices-nothing-and-rules-nothing", gate["noticed"]["recorded"] == [] and stub["applied"] == [] and len(stub["left"]) == 3, gate)
    check("and-counts-the-contest", stub["contested"] >= 1, stub["contested"])
    msgs = keeper.build_ruling_prompt(led, "r1", 0, 2)
    check("the-ruling-prompt-carries-the-claims-and-the-contradiction",
          "never burned" in msgs[1]["content"] and "CONTRADICTIONS" in msgs[1]["content"] and "id %d vs id %d" % (a, b) in msgs[1]["content"]
          or "id %d vs id %d" % (b, a) in msgs[1]["content"], msgs[1]["content"][-400:])
    rulings = keeper.parse_rulings('here you are:\n[{"utterance_id": %d, "verdict": "established", "rationale": "the story leans on it"},'
                                   ' {"utterance_id": %d, "verdict": "fiction", "rationale": "contradicts it"},'
                                   ' {"utterance_id": 999, "verdict": "established"}, {"utterance_id": %d, "verdict": "maybe"},'
                                   ' {"utterance_id": %d, "verdict": "superposed"}]' % (b, a, a, a))
    applied, left, rejected = keeper.apply_rulings(led, "r1", rulings, at_turn=2)
    check("established-and-fiction-are-written", [r["verdict"] for r in applied] == ["established", "fiction"], applied)
    check("superposed-is-left", len(left) == 1)
    check("an-unknown-utterance-and-an-unknown-verdict-are-refused", len(rejected) == 2 and "invention" in rejected[0][1] and "verdict" in rejected[1][1], rejected)
    rows = {r["subject"]: r for r in read_api.established(led.con, "r1", ["mill"], as_of=2).rows}
    check("the-kept-ruling-is-the-next-packets-fact", rows["mill"]["kept"] == ["The mill has never burned. My father raised it and it stands."], rows["mill"])
    n = led.con.execute("SELECT COUNT(*) FROM claim_resolutions").fetchone()[0]
    check("two-resolution-rows-and-no-more", n == 2, n)
    check("parse-tolerates-no-list", keeper.parse_rulings("nothing here") == [] and keeper.parse_rulings("[not json") == [])


def test_unextracted(tmp):
    """[5] THE DEBT — `claims.unextracted`, the licence's other half made visible (2026-09-19,
    gate lore-licence-visible). `_led` above always calls `claims.record` WITH extracts, because it
    is building the FENCE's fixture; this builds the gap `_led` never leaves: a saying committed
    through the ORDINARY turn path, which carries no extracts until the keeper notices it."""
    print("\n[5] THE DEBT — sayings the fence cannot see until the keeper notices them")
    led = Ledger(os.path.join(tmp, "bare.db"))
    led.create_run("bare", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    for cid in ("maren", "cobb"):
        led.register_character("bare", cid, {"name": cid.title()}, {"temperament": "authored"})
    rows = (("maren", 0, '"The mill burned the winter my mother died."'),
            ("cobb", 2, '"The mill has never burned."'))
    for who, t, said in rows:
        # THE ORDINARY COMMIT PATH, not claims.record: `utterances=claims.spoken(action)` is
        # exactly what scripts/scene.py and scripts/direct.py hand `TurnCommit`, and
        # `Ledger.append_turn` writes each through `claims.write` with NO extracts — the shape
        # every live turn actually lands in (keeper.py:449-451's trap).
        led.append_turn(TurnCommit(run_id="bare", turn=t, actor=who, thought="t%d" % t, action=said,
                                   tags={"type": "mundane"}, affect={p: 0.3 for p in PATHS}, events=[],
                                   utterances=claims.spoken(said)))
    debt = claims.unextracted(led.con, "bare")
    check("two-bare-sayings-are-both-counted", debt["count"] == 2, debt)
    check("first-and-last-turn-bracket-them", debt["first_turn"] == 0 and debt["last_turn"] == 2, debt)
    check("speakers-are-sorted-and-deduped", debt["speakers"] == ["cobb", "maren"], debt["speakers"])

    led2 = Ledger(os.path.join(tmp, "mixed.db"))
    led2.create_run("mixed", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    for cid in ("maren", "cobb"):
        led2.register_character("mixed", cid, {"name": cid.title()}, {"temperament": "authored"})
    said0 = '"The mill burned the winter my mother died."'
    led2.append_turn(TurnCommit(run_id="mixed", turn=0, actor="maren", thought="t0", action=said0,
                                tags={"type": "mundane"}, affect={p: 0.3 for p in PATHS}, events=[],
                                utterances=claims.spoken(said0)))
    # THE KEEPER'S OWN PATH: claims.record writes a NEW utterance WITH extracts in the same call —
    # never a retroactive fix to the bare row above. Hard rule 2 makes that structural: utterances
    # and claim_extracts are both append-only (schema.sql triggers), so a saying committed bare
    # stays bare forever, by design — the debt this function measures cannot be paid off in place,
    # only avoided by extracting at write time.
    claims.record(led2.con, "mixed", 1, "cobb", "The mill has never burned.",
                  [{"subject": "mill", "predicate": "burned", "object": "never"}])
    debt2 = claims.unextracted(led2.con, "mixed")
    check("one-bare-and-one-extracted-leaves-the-count-at-one", debt2["count"] == 1, debt2)
    check("...and-names-the-bare-speaker-not-the-extracted-one", debt2["speakers"] == ["maren"], debt2)

    led3 = Ledger(os.path.join(tmp, "empty.db"))
    led3.create_run("empty", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    debt3 = claims.unextracted(led3.con, "empty")
    check("a-run-with-no-utterances-counts-zero-and-brackets-nothing",
          debt3 == {"count": 0, "first_turn": None, "last_turn": None, "speakers": []}, debt3)


def main():
    print("test_lore.py — the lore licence")
    tmp = tempfile.mkdtemp(prefix="stp-lore-")
    try:
        test_the_fence(tmp)
        test_the_packet_and_the_prompt()
        test_the_ruling(os.path.join(tmp, "b"))
        test_unextracted(os.path.join(tmp, "c"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
