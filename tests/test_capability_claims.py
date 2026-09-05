"""test_capability_claims.py — a mechanism a doc NAMES as available must have a code path.

PORTED 2026-09-04 from the sibling instance, and RE-CLASSIFIED against this tree rather
than inherited. Every one of the sibling's twelve BUILT claims failed here on the first
run — not as regressions but because the sibling built them after this template was
exported, while the template's own docs kept promising them. For a PUBLIC template that
is the finding that matters: a reader clones it and reads promises the engine does not
keep.

Ten are now DEFERRED — still promised by a doc that is IN THIS REPO, still unbuilt, and
now reported every run instead of read as shipped. Two were removed rather than deferred,
because nothing here promises them: "lore accretes about a place" cites
docs/keeper-of-truth.md and src/engine/claims.py, neither of which exists in this tree,
and "omniscient narration" was promised in conversation and a cairn backlog, not by any
document a cloner would read.

The control was re-pointed too: it asserted on `ledger.previous_affect`, a method only the
sibling has, so it failed for a portability reason and not a real one. A control asserting
on another repo's shapes is this suite's own defect class, one level up.


WHY THIS EXISTS. `tests/test_citations.py` verifies that a cited `symbol :NN` is DEFINED at that
line. Its own docstring says the rest of the job is out of scope: "mechanical only — this suite
cannot read intent". So it catches a citation that DRIFTED and cannot catch a capability that was
never built, because those are promised in PROSE and never cited at all.

Five instances of that were found in one day's reading, 2026-09-01, spanning four subsystems and
written months apart by the same careful hand:

    fork              guide-user-path.md   "the log is never rewound; it is forked"
    first person      narration.md         "POV-bounded narrator (close third or first)"
    direction_changes records.py           set on 8 primitives, cited in direction.py's docstring
    threaten          consolidation.py     world_map: "tensions", with no fold branch
    the EDL           cutting-room.md      "decisions append to the EDL; narration renders from it"

Every one reads as true. That is the signature of a CLASS, not of carelessness: the docs are written
as the design intends and the implementation lags with nothing noticing. The repo already named it
once — `learnings/2026-07-29-a-documented-key-with-no-reader-is-a-lie-with-a-citation.md` — and five
more appeared a month later, so naming it was not enough.

WHAT THIS CHECKS, and what it deliberately does not:
  * BUILT claims must still resolve. A capability that shipped and then lost its code path fails
    here — this is the regression half, and it is the half that grows in value as items land.
  * DEFERRED claims are PRINTED, never failed. A known gap stays loud without blocking the suite,
    the same shape as `test_world_events.py`'s threaten DEBT and `test_map.py`'s 500-line list.
  * A claim's status must match reality BOTH WAYS. A DEFERRED claim that now resolves fails too —
    it means someone built it and left the registry stale, which is how this rot starts.

It does NOT scan prose for arbitrary capability assertions. That would be unbounded and would rot.
The registry is a hand-kept list of promises the repo makes to its users — the same discipline as
`test_no_private_content.py`'s banned terms, and it carries the same duty: extend it when you make
a new promise.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BUILT, DEFERRED = "BUILT", "DEFERRED"


def _read(rel):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return ""
    return open(path, encoding="utf-8").read()


def _defines(rel, name):
    """A def/class/module-level assignment of `name` in one file."""
    return re.search(r"^(def|class)\s+%s\b|^%s\s*=" % (re.escape(name), re.escape(name)),
                     _read(rel), re.M) is not None


def _method(rel, name):
    """A `def name(` at ANY indentation — i.e. a method on a class.

    `_defines` is anchored at column 0 on purpose (a module-level def or assignment), so it reports
    False for every method. Measured 2026-09-01: a resolver used it for `Ledger.previous_affect`
    and turned the suite red on a capability that was in fact built. Two helpers, two questions.
    """
    return re.search(r"^\s*def\s+%s\b" % re.escape(name), _read(rel), re.M) is not None


def _calls(rel, name):
    """`name(` appears OUTSIDE an import line. A bare substring match is satisfied by the import
    itself — measured 2026-09-01: unwiring the call from a driver left the guard green because
    `from ... import name` still matched. A guard reports on what it READS."""
    body = chr(10).join(l for l in _read(rel).splitlines()
                        if not l.lstrip().startswith(("import ", "from ")))
    body = re.sub(r"#.*", "", body)
    return ("%s(" % name) in body


def _cli_flag(rel, flag):
    return ('"%s"' % flag) in _read(rel) or ("'%s'" % flag) in _read(rel)


def _reads_field(rel, field):
    """The field is READ as code, not merely named in a comment or docstring."""
    body = re.sub(r'"""[\s\S]*?"""', "", _read(rel))
    body = re.sub(r"#.*", "", body)
    return re.search(r"\[[\"']%s[\"']\]|\.get\([\"']%s[\"']" % (field, field), body) is not None


def _fold_branches(etype):
    # THE FOLD MOVED to `src/engine/fold.py` on 2026-09-03. This reads `_project`'s branch table out
    # of its SOURCE, so it moved with it — left on ledger.py it found `i == -1`, an EMPTY body, and
    # reported every BUILT capability as no longer resolving. Red, which is the safe direction.
    src = _read("src/engine/fold.py")
    i = src.find("def project")
    body = src[i:src.find("def events_between")] if i >= 0 else ""
    found = set(re.findall(r'etype == "([\w-]+)"', body))
    for m in re.finditer(r"etype in \(([^)]*)\)", body):
        found |= {x.strip().strip("\"'") for x in m.group(1).split(",")}
    return etype in found


# name -> (status, where the promise is made, what must resolve, resolver)
CLAIMS = {
    "run fork": (
        DEFERRED,
        'docs/guide-user-path.md — "the log is never rewound; it is forked"',
        "a fork function on the ledger, or a driver flag that branches a run",
        lambda: _defines("src/engine/ledger.py", "fork") or _cli_flag("scripts/scene.py", "--fork"),
    ),
    "first-person narration": (
        DEFERRED,
        'docs/narration.md — "POV-bounded narrator (close third or first)"',
        "a voice selector on narrate.py",
        lambda: _cli_flag("scripts/narrate.py", "--voice") or _cli_flag("scripts/narrate.py", "--first-person"),
    ),
    "direction_changes is read": (
        DEFERRED,
        "src/engine/records.py sets it on 8 primitives; direction.py cites it in _phrase_for's docstring",
        "records.direction_changes existing AND _phrase_for calling it, not admits_role",
        lambda: _defines("src/engine/records.py", "direction_changes")
        and _calls("src/engine/direction.py", "direction_changes"),
    ),
    "threaten moves tensions": (
        DEFERRED,
        'src/engine/consolidation.py CATALOG — threaten carries world_map: "tensions"',
        "a branch in ledger._project AND the chassis it delegates to",
        lambda: _fold_branches("threaten"),
    ),
    "uprising moves tension-state": (
        DEFERRED,
        'docs/world-state-ledger.md — "an uprising updates tension-state"',
        "an uprising type in the CATALOG *and* a fold branch — a bare substring would count a "
        "comment as a build, and a catalog row with no branch as a resolution",
        lambda: re.search(r'^\s*"uprising":', _read("src/engine/consolidation.py"), re.M) is not None
        and _fold_branches("uprising"),
    ),
    "the EDL": (
        DEFERRED,
        'docs/cutting-room.md — "decisions append to the EDL; narration renders from it"',
        "an edl table, a validating writer, AND narration reading from it — a record with no "
        "reader would be this suite's own defect class",
        lambda: "edl" in _read("src/engine/schema.sql").lower()
        and _defines("src/engine/edl.py", "append")
        and _calls("scripts/narrate.py", "edl_mod.entries_for")
        and _calls("scripts/cut.py", "edl_mod.append"),
    ),
    "severity words": (
        DEFERRED,
        "docs/standard-vectors.md §3 — the author writes a WORD",
        "severity.normalise_dimensions resolving words at the parse seam",
        lambda: _defines("src/engine/severity.py", "normalise_dimensions")
        and _calls("scripts/direct.py", "normalise_dimensions")
        and _calls("scripts/scene.py", "normalise_dimensions"),
    ),
    "the world snapshot moves": (
        DEFERRED,
        'docs/guide-operating.md — "sparse until move/harm/reveal events populate it"; '
        "src/engine/world_events.py states the warrant rule",
        "an emitter for the eight world-moving types, plus the fold-and-diff warrant test",
        lambda: _defines("src/engine/world_events.py", "append")
        and _defines("src/engine/world_events.py", "would_change")
        and _calls("scripts/keeper.py", "world_events.append"),
    ),
    "the leak wall is fact-shaped": (
        DEFERRED,
        "src/engine/faithfulness.py caught leaked NAMES only; not every secret is a name",
        "check_fact_leaks existing AND both drivers passing the information registry",
        lambda: _defines("src/engine/faithfulness.py", "check_fact_leaks")
        and _calls("scripts/direct.py", "faithfulness.check_fact_leaks")
        and "information=" in _read("scripts/scene.py"),
    ),
    "the slope is rendered": (
        DEFERRED,
        "src/engine/direction.py's only movement marker compares to the temperament MEAN, so a "
        "leap and a climb read identically",
        "a slope marker reading the previous committed turn, and drivers supplying it",
        lambda: _defines("src/engine/direction.py", "_slope_marker")
        and _method("src/engine/ledger.py", "previous_affect")
        and _calls("scripts/scene.py", "led.previous_affect"),
    ),
    "composition pass phase A": (
        DEFERRED,
        "docs/composition-pass.md specifies classify (LLM) + compose (script); only compose shipped",
        "a classifier prompt builder and a validator that refuses final numbers",
        lambda: _defines("scripts/composition_pass.py", "build_classify_prompt")
        and _defines("scripts/composition_pass.py", "picks_from_classification")
        and _cli_flag("scripts/composition_pass.py", "--classify"),
    ),
    "scene cfg is pinned": (
        DEFERRED,
        "the bible is pinned by fingerprint (src/engine/bible.py); the scene cfg now is too (v14)",
        "a scene_cfg module with fingerprint/record/drifted, and append_scene calling record",
        lambda: _defines("src/engine/scene_cfg.py", "fingerprint")
        and _defines("src/engine/scene_cfg.py", "drifted")
        and "scene_cfg.record(" in _read("src/engine/ledger.py")
        and _calls("scripts/scene.py", "scene_cfg_mod.drifted"),
    ),
}


def test_BUILT_claims_still_resolve():
    """The regression half. A capability that shipped and lost its code path fails here."""
    broken = ["%s — promised in %s; needs %s" % (name, where, needs)
              for name, (status, where, needs, ok) in sorted(CLAIMS.items())
              if status == BUILT and not ok()]
    assert not broken, ("a capability the docs promise no longer resolves:\n  "
                        + "\n  ".join(broken))


def test_DEFERRED_claims_are_REPORTED_not_forgotten():
    """The visibility half. Known gaps print every run; they never block the suite."""
    for name, (status, where, needs, ok) in sorted(CLAIMS.items()):
        if status == DEFERRED and not ok():
            print("       DEBT  %-26s promised in %s" % (name, where))


def test_a_DEFERRED_claim_that_now_RESOLVES_must_be_reclassified():
    """The other direction, and the one that keeps the registry honest: if a gap was closed and
    nobody updated its status, the registry has started lying in the reassuring direction."""
    stale = ["%s now resolves — mark it BUILT" % name
             for name, (status, _w, _n, ok) in sorted(CLAIMS.items())
             if status == DEFERRED and ok()]
    assert not stale, ("the registry is stale; these are built and still marked DEFERRED:\n  "
                       + "\n  ".join(stale))


def test_every_claim_names_where_it_is_promised_and_what_would_satisfy_it():
    """A registry entry with no citation is an assertion. Each must say where the promise lives and
    what resolving it means, so the next reader can check rather than trust."""
    for name, (status, where, needs, ok) in sorted(CLAIMS.items()):
        assert status in (BUILT, DEFERRED), "%s has an unknown status %r" % (name, status)
        assert where.strip() and (".md" in where or ".py" in where or "William" in where), (
            "%s does not name where it is promised: %r" % (name, where))
        assert needs.strip(), "%s does not say what would satisfy it" % name
        assert callable(ok), "%s has no resolver" % name


def test_the_checker_can_fail():
    """CONTROL — a resolver that cannot resolve must be reported, or this suite proves nothing."""
    assert not _defines("src/engine/ledger.py", "a_function_that_does_not_exist")
    assert not _cli_flag("scripts/narrate.py", "--not-a-real-flag")
    assert not _fold_branches("not-an-event-type")
    assert not _calls("scripts/direct.py", "a_function_nobody_calls")
    # and the specific blindness this suite was measured to have: an import must not satisfy a call
    assert not _calls("tests/test_capability_claims.py", "sys")
    # and the two def-finders answer DIFFERENT questions: a method is not a module-level def.
    # Uses `create_run`, a method THIS ledger has — the ported version named
    # `previous_affect`, which exists only in the sibling, so the control failed for a
    # portability reason and not a real one. A control asserting on another repo's shapes
    # is the same defect class this suite exists to catch, one level up.
    assert _method("src/engine/ledger.py", "create_run")
    assert not _defines("src/engine/ledger.py", "create_run")


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("  PASS  %s" % name)
            except Exception as e:                       # noqa: BLE001 — a harness reports, never raises
                fails += 1
                print("  FAIL  %s: %s" % (name, e))
    print("%s" % ("ALL PASS" if not fails else "%d FAILED" % fails))
    sys.exit(1 if fails else 0)
