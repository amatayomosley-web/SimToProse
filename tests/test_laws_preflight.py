"""test_laws_preflight.py — the world refuses something.

`src/engine/bible.py:411` `verdict_for` implements the modality contract from
`docs/guide-content.md:146-158` — IMPOSSIBLE denies the circumstance, FORBIDS allows and attaches
teeth — and it had **no caller anywhere in src/ or scripts/**. The only other occurrence of the name
in the repo was inside a lint warning string. So an authored world refused nothing at runtime.

Nor was it caught later: `scripts/critic.py:62-76` asks CONTINUITY and VOICE only, and contains zero
occurrences of law / verdict / forbid / impossible / modality. A breach was caught **nowhere** — not
before the beat, not after it, not by the critic.

THE ACT IS AUTHORED, NOT INFERRED, and that is the load-bearing decision. Measured on a real book:
with an unset act every law bears and 24 of them deny, so a blanket call would refuse every scene.
An act supplied by the author keys precisely; one inferred from prose is a classifier problem
wearing a call site's clothes.

What this pins:
  1. IMPOSSIBLE denies, and names the law that did it.
  2. FORBIDS ALLOWS — and surfaces teeth. A gate that denied every illegal act would make crime
     unwritable (`guide-content.md:154`), which is the opposite of what laws are for.
  3. An act no law bears on is allowed. The check must not over-refuse.
  4. No act means no check — every scene authored before this ran unchanged.
"""
import hashlib as _hashlib
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import bible                              # noqa: E402
from src.engine.ledger import Ledger                      # noqa: E402
from src.engine.vault import load_book                    # noqa: E402

_FAILS = []
_BOOKS = os.environ.get("SWE_BOOKS")   # no fallback: a hardcoded path is a machine-local leak


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _fixture():
    """A minimal invented world carrying one law of each modality. Engine-owned, corpus-free."""
    world = {
        "world": "lawtest",
        "switches": {"magic": True, "divine": False, "beings": False},
        "locations": [{"id": "yard", "what": "the yard"}],
        "laws": [
            {"id": "stone-does-not-float", "domain": "supernatural", "modality": "IMPOSSIBLE",
             "epistemic": "known-true", "act": "float-a-stone",
             "statement": "Stone does not float. Nothing lifts it but hands or rope."},
            {"id": "no-blades-in-the-yard", "domain": "custom", "modality": "FORBIDS",
             "epistemic": "known-true", "act": "draw-a-blade",
             "teeth": "The yard-master takes the blade and the week's pay.",
             "statement": "No blade is drawn in the yard."},
            {"id": "the-old-road", "domain": "supernatural", "modality": "IMPOSSIBLE",
             "epistemic": "known-false", "act": "walk-the-old-road",
             "statement": "The old road eats those who walk it after dark."},
        ],
    }
    return world, {}


def _con(world, chars):
    led = Ledger(":memory:")
    return led.con, bible.build(led.con, world, chars)


def test_impossible_denies():
    print("\n[1] IMPOSSIBLE denies, and names the law")
    con, fp = _con(*_fixture())
    v = bible.verdict_for(con, fp, act="float-a-stone")
    check("denied", v["allowed"] is False, v)
    check("names-the-law", v["denied_by"] == ["stone-does-not-float"], v["denied_by"])
    check("gives-a-reason", bool(v.get("reason")), v.get("reason"))


def test_forbids_allows_with_teeth():
    print("\n[2] FORBIDS ALLOWS — crime must stay writable")
    con, fp = _con(*_fixture())
    v = bible.verdict_for(con, fp, act="draw-a-blade")
    check("allowed", v["allowed"] is True, v)
    check("recorded-as-a-violation", v["violations"] == ["no-blades-in-the-yard"], v["violations"])
    check("teeth-surface", v["teeth"] and "yard-master" in v["teeth"][0], v["teeth"])


def test_does_not_over_refuse():
    print("\n[3] An act no law bears on is ALLOWED")
    con, fp = _con(*_fixture())
    v = bible.verdict_for(con, fp, act="carry-a-sack")
    check("allowed", v["allowed"] is True, v)
    check("no-denials", not v["denied_by"], v["denied_by"])
    check("no-violations", not v["violations"], v["violations"])


def test_known_false_does_not_bind():
    print("\n[4] A superstition constrains nothing")
    con, fp = _con(*_fixture())
    v = bible.verdict_for(con, fp, act="walk-the-old-road")
    check("known-false-law-does-not-deny", v["allowed"] is True,
          "a world where people BELIEVE the road eats them is not a world where it does")


def test_blanket_call_is_the_wrong_call():
    print("\n[5] WHY THE ACT IS AUTHORED — act=None is not a general check")
    con, fp = _con(*_fixture())
    v = bible.verdict_for(con, fp)                       # no act
    bearing = bible.laws_bearing_on(con, fp)
    # NOT == 3: bible._project_laws adds surviving BLUEPRINT DEFAULTS on top of the authored
    # laws, so a 3-law fixture yields more. The point is that ALL of them bear when no act narrows.
    authored = {"stone-does-not-float", "no-blades-in-the-yard", "the-old-road"}
    ids = {r["law_id"] for r in bearing}
    check("every-authored-law-bears-when-no-act-is-given", authored <= ids, sorted(authored - ids))
    check("and-the-blueprint-defaults-bear-too", len(bearing) > len(authored), len(bearing))
    check("and-so-it-denies", v["allowed"] is False,
          "act=None is exhaustive by construction, so a blanket call refuses everything")


def test_the_runner_wires_it():
    print("\n[6] THE CALL SITE EXISTS")
    src = open(os.path.join(REPO, "scripts", "scene.py"), encoding="utf-8").read()
    check("run_scene-calls-verdict_for", "verdict_for" in src)
    check("skips-cleanly-without-an-act", 'cfg.get("act")' in src,
          "a scene cfg with no act must run exactly as before")
    check("refuses-rather-than-warning", "scene refused" in src)


def test_real_book_if_present():
    print("\n[7] AGAINST A REAL BOOK (skipped if none)")
    root = _BOOKS
    if not root or not os.path.isdir(root):
        print("       no books root — skipped")
        return
    # pick a book that HAS laws, not merely the first alphabetically
    world = chars = None
    for d in sorted(os.listdir(root)):
        if not os.path.isdir(os.path.join(root, d, "world")):
            continue
        try:
            w, c = load_book(os.path.join(root, d))
        except Exception:
            continue
        if w.get("laws"):
            world, chars = w, c
            # NEVER print the directory name — it is a real book TITLE, and this suite
            # runs on every `python tests/run_all.py`, i.e. on every verification the
            # operator does, into whatever terminal, scrollback or shared log is open.
            # Hard rule 1 says no book title lives in this repo; a title STREAMING OUT of
            # it on every run is the same leak with a shorter half-life. Measured
            # 2026-09-04: SWE_BOOKS was set and the name was being emitted.
            #
            # Fixed in CODE rather than by "remember to unset SWE_BOOKS", because a rule
            # enforced by habit is a rule that has never been tested. The digest is stable
            # across runs, so a reader can still tell WHICH book was used run-to-run
            # without the name ever existing outside the vault.
            print("       using book %s (name withheld — hard rule 1)"
                  % _hashlib.sha256(d.encode("utf-8")).hexdigest()[:8])
            break
    if world is None:
        print("       no book carries laws — skipped")
        return
    laws = world.get("laws") or []
    con, fp = _con(world, chars)
    reachable = [l["id"] for l in laws
                 if l.get("act") and not bible.verdict_for(con, fp, act=l["act"])["allowed"]
                 or l.get("modality") in ("FORBIDS", "REQUIRES")]
    print("       %d laws, %d reachable by their own act" % (len(laws), len(reachable)))
    check("every-law-is-reachable-by-its-own-act", len(reachable) == len(laws),
          "unreachable: %s" % [l["id"] for l in laws if l["id"] not in reachable][:3])


def test_post_action_teeth():
    """A reported act is put through the laws AFTER the beat — and never retracts it.

    `verdict_for` computed `teeth` for every violated FORBIDS from the day it was written, and
    nothing consumed them: a law the world declares BREAKABLE cost nothing. That is the half of the
    modality contract that makes a rule dramatic rather than merely physical.

    It cannot deny. The turn already happened, and CLAUDE.md hard rule 2 makes the log append-only —
    a correction is a new event, never an edit. So an IMPOSSIBLE act reported here is RECORDED for
    the critic and the arc; refusing it is the pre-flight's job.
    """
    print("\n[8] POST-ACTION - FORBIDS teeth land, and nothing is retracted")
    import importlib.util as _u
    _sp = _u.spec_from_file_location("_sc", os.path.join(REPO, "scripts", "scene.py"))
    sc = _u.module_from_spec(_sp)
    _sp.loader.exec_module(sc)
    world, chars = _fixture()
    led = Ledger(":memory:")

    ev = sc._law_events(led, "r1", world, chars, {"act": "draw-a-blade"}, "someone")
    check("forbids-produces-an-event", len(ev) == 1, len(ev))
    check("teeth-are-carried", "yard-master" in str(ev[0].payload.get("teeth")), ev[0].payload)
    check("typed-as-a-law-violation", ev[0].type == "law-violation", ev[0].type)

    ev = sc._law_events(led, "r1", world, chars, {"act": "float-a-stone"}, "someone")
    check("impossible-is-RECORDED-not-retracted", len(ev) == 1 and ev[0].payload["modality"] == "IMPOSSIBLE",
          ev[0].payload if ev else None)

    for empty in ("", None, "carry-a-sack"):
        check("no-event-for-%r" % (empty,), not sc._law_events(led, "r1", world, chars, {"act": empty}, "x"))
    check("no-act-key-at-all", not sc._law_events(led, "r1", world, chars, {}, "x"))

    # the vocabulary reaches the actor only when the world declares laws
    from src.engine.prompt import build_turn_messages
    check("prompt-takes-acts", "acts" in build_turn_messages.__code__.co_varnames)


def main():
    print("test_laws_preflight.py — the world refuses something")
    for t in (test_impossible_denies, test_forbids_allows_with_teeth, test_does_not_over_refuse,
              test_known_false_does_not_bind, test_blanket_call_is_the_wrong_call,
              test_the_runner_wires_it, test_post_action_teeth, test_real_book_if_present):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
