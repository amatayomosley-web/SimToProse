#!/usr/bin/env python3
"""test_reachable.py — every engine capability is REACHED, or is explained.

THE DEFECT CLASS THIS EXISTS FOR. CLAUDE.md records three instances and 2026-09-03 added two more:

    run_config          guarded by `if hasattr(led, "run_config")` — always false, so the pinned-bible
                        divergence check never once ran.
    verdict_for's teeth computed from the day they were written and consumed by nothing.
    bible.drifted       advertised in hard rule 1, invoked from a test and nowhere else.
    fold_vault          called ONLY inside `if args.resume:` in both drivers, so belief supersession
                        did nothing for the life of a running process — a character recalled "Torin
                        is alive" and "Torin was confirmed dead" in the same packet.
    decay               wired end-to-end and never invoked with real time context in production.

Every one of those was CORRECT CODE behind a call site that never fired, and every one was found by
a person noticing rather than by a guard. Unit tests cannot see this: they call the function
directly, so the function passes and the pipeline never runs it. That is the whole gap — "the
function works" and "the engine uses it" are two claims, and the suite only ever checked the first.

WHAT THIS ASSERTS: every public function in src/engine/ is either CALLED somewhere in src/ or
scripts/, or is named in EXEMPT below with a written reason. Protected-or-explained, the same
inversion `tests/test_place.py` uses — a new unreached function FAILS by default, so the cost of
adding one is a sentence explaining why, paid at the time rather than discovered a month later.

WHAT IT DOES NOT ASSERT, said plainly because a guard's coverage is a claim before its result is:
this is REACHABILITY BY NAME, not execution. A function called only inside `if args.resume:` counts
as reached here — which is exactly the fold_vault case, so this guard would NOT have caught it. That
is a real limit and the reason `tests/test_driver_main.py` exists alongside it: that suite runs both
drivers' main() as subprocesses against a fixture book, which is the only thing that proves a path
actually executes. This file catches the never-wired; that one catches the wired-but-unreached.

Stdlib only, script-style like the repo's other tests. Exit 0 = all pass.
"""
import ast
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

ENGINE = os.path.join(REPO, "src", "engine")
SCAN = (os.path.join(REPO, "src", "engine"), os.path.join(REPO, "scripts"))

FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % detail))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


# EXEMPT — unreached ON PURPOSE, each with the reason. A bare name is not enough: the reason is the
# artifact, because it is what a future reader weighs when deciding whether the exemption still
# holds. "Add it to the list" without one is how the other guard rotted (CLAUDE.md's `_BANNED`).
EXEMPT = {
    # THE NO-DECLARATION REFERENCE (gate erosion-derived-at-replay, 2026-09-22). No driver calls it
    # since the attitude refold moved to `passage.fold_toward`, which keeps each opening's fade;
    # tests/test_passage.py [7] pins the fold EQUAL to it on a log with no time declaration, so a
    # change to either one's sum-then-clamp arithmetic goes red there. Delete both together or neither.
    ("toward.py", "replay"):         "the no-declaration reference passage.fold_toward is pinned equal to (tests/test_passage.py [7])",
    # THE SAME FOR THE WOUNDS (gate bench-clock, 2026-09-24): the read-along bench was their last caller and now folds
    # through `passage.fold_wounds`, which carries story time; tests/test_passage.py [7] pins that fold EQUAL to these
    # on a log with no stretch of time, and tests/test_readalong.py [3] reads them as the timeless comparison.
    ("wound.py", "fold"):            "the no-stretch reference passage.fold_wounds is pinned equal to (tests/test_passage.py [7], tests/test_readalong.py [3])",
    ("wound.py", "mints_for"):       "reads the mints for that same reference, wound.fold (tests/test_passage.py [7], tests/test_readalong.py [3])",

    # `state.py:zone_of` LEFT THIS LIST 2026-09-19 (gate emotion-tier-tidy), and not by being
    # wired: it was deleted along with `_ZONE_EPISODE`/`_ZONE_DISPOSITION`, the retired two-zone
    # apparatus the redesign's gate 2 (2026-09-12) had already stopped calling from decay. The one
    # remaining reader was `tests/test_state.py`'s own asymmetry spike, re-based onto
    # `_rung_half_life`'s two ladders directly. Do not restore the entry; the function it named is
    # gone.

    # The READ TIER is a public API for consumers outside this repo — the whole point is that the
    # engine does not call it. docs/MAP.md routes to it as the read surface.
    ("read_api.py", "state"):        "read tier: public API for external consumers, not engine-internal",
    ("read_api.py", "knows"):        "read tier: public API for external consumers, not engine-internal",
    ("read_api.py", "said"):         "read tier: public API for external consumers, not engine-internal",
    ("read_api.py", "edges"):        "read tier: public API for external consumers, not engine-internal",
    ("read_api.py", "snapshot_at"):  "read tier: public API for external consumers, not engine-internal",
    ("read_api.py", "scene_of"):     "read tier: public API for external consumers, not engine-internal",
    ("read_api.py", "place"):        "read tier: public API for external consumers, not engine-internal",

    # ORCHESTRATOR SURFACES (Mode B). Each is named by a doc or an agent as the thing the agent
    # layer calls, and the scripts (Mode A) do not: moved here from the ratchet 2026-09-10 when the
    # owner asked which unwired code should be removed and which merely has no Mode-A caller.
    ("citation.py", "verify_envelope"):  "the grounding contract's enforcement, named by SPEC-LEDGER as the orchestrator's check on an answer envelope",
    ("claims.py", "tested"):             "keeper-of-truth's first collapse trigger (docs/keeper-of-truth.md); the keeper seat asks it, the scripts do not",
    ("severity.py", "rubric"):           "the severity-word rubric the appraiser and keeper seats are shown (.claude/agents/appraiser.md)",
    ("scene_cfg.py", "for_scene"):       "the v14 pin's read surface — a replay names its inputs by this; the resume path passes the cfg explicitly",

    # `compounds.py:recognise` LEFT THIS LIST 2026-09-08, and not by being wired. When the eight
    # paths replaced the Panksepp primitives as the stored state, every compound recipe stopped
    # naming anything the engine holds, and the module moved to staging/src/engine/compounds.py.
    # The exemption said it would end "when a path resolver replaces it" -- that is what
    # happened: the composer reads a RUNG per path, which is position on an axis, exactly the
    # thing cosine could not see. Do not restore the entry; the file it names is gone.

    # PHASE 1 OF THE EMOTION-ARITHMETIC MIGRATION, 2026-09-09. `docs/emotion-arithmetic.md`
    # section 3 step 2 is `f <- f + v_k * g`; this is `v_k`, and the receipt step that spends it is
    # Phase 3. Unwired ON PURPOSE and for one reason: the vector table must be provably correct
    # BEFORE anything accumulates with it, because an error here is invisible downstream -- every
    # character would simply feel slightly wrong, forever, with no test able to say why. It is
    # exercised by tests/test_rung_vectors.py against the doc's own published table (transcribed,
    # not derived) plus two deliberate-breakage controls. The exemption ends when the receipt step
    # calls it; delete this entry then rather than adding a caller to satisfy the guard.
    #
    # THE EXEMPTION LEFT THIS LIST 2026-09-10, and NOT because the receipt step landed: it has
    # not. `scripts/derive_genotype.py` reads `vector_for` to solve the genotype's hit and hold
    # ceilings against the idle-floor coupling, which is a legitimate consumer of the vector table
    # (the balance sweep needs what a rung is worth) and not a caller added to satisfy this guard.
    # The receipt step is still Phase 3 and still owed; `state.appraise` still prices through
    # `_DIM_TO_PATH`, not through `vector_for`.

    # PHASE 2 OF THE EMOTION-ARITHMETIC MIGRATION, 2026-09-09.
    # `stub_readings` WAS EXEMPTED HERE AND IS NOW DELETED, 2026-09-09, when the appraiser seats
    # landed -- which is exactly what its exemption instructed ("DELETE when the appraiser seat
    # lands -- do not wire it"). The ratchet worked: it named the deletion condition in advance and
    # this suite refused to let the exemption outlive the function. Preserved with its reasoning in
    # `staging/src/engine/RETIRED-stub_readings.py`.
    #
    # WHY IT COULD NEVER BE WIRED, restated here because it is the trap the replacement must avoid:
    # it reported the rung a character was ALREADY at, which makes it the p = 1 sensor -- every beat
    # reports carried state as if it had just arisen, the receipt step adds the character to
    # themselves, and the float climbs from a quiet room to the top rung. Phase 3's test double is a
    # hand-built `[Reading(...)]` fixture, which `tests/test_readings.py` already uses; an ENGINE
    # FUNCTION was never the right shape for it.
    #
    # `readings.py:readings_for` LEFT THIS LIST 2026-09-22 (gate mood-from-readings), by being wired:
    # `mood_fold.replay` reads every beat's readings through it to re-derive the mood, which is the
    # re-derivability the readings table was built for (docs/emotion-arithmetic.md section 5 step 8).

    # RECOVERY TIER — RETIRED 2026-09-09, owner's call. The three exemptions that stood here named
    # `is_recovery_active`, `recovery_block_for` and `recovery_state_for_peak` as "unwired until turn
    # loop adds descent hook". The hook was never scheduled, and three findings on 2026-09-09 said it
    # should not be: the overlay HID the float instead of moving it (so `spent` lifting dropped the
    # character onto `fury`), it keyed on a remembered peak rung nothing stores, and the asymmetry
    # argument underneath it was retracted as symmetric by construction. Moved whole to
    # `staging/`, with the reasoning, in `staging/RETIRED-RECOVERY-TIER.md`.
    #
    # THE PROBLEM IT ADDRESSED IS STILL OPEN and this comment is the pointer to it: an emotion ladder
    # runs one direction, so a man descending from `amok` is handed `annoyance` on the way down.

    # THE GENOTYPE REBUILD, 2026-09-10. `heritable.typical()` is a sheet CONSTRUCTOR — a full
    # genotype at the species prior with per-path overrides — that tests and authoring tools use to
    # build characters. The engine consumes genotypes and never produces one (hard rule 4 puts the
    # draw in scripts/make_genotype.py), so nothing in src/ or scripts/ calls it on purpose.
    ("heritable.py", "typical"):     "sheet constructor for tests and authoring; the engine consumes genotypes, never builds one",
    ("heritable.py", "resting"):     "the temperament twin of typical() (2026-09-10): a full resting face from rest words, for tests and authoring; the engine seeds a sheet's own rows in place (ensure_temperament) and never builds one",

    # The bond seam went live 2026-09-17 (bond gate 1): observations_from_showed is called from
    # scripts/appraiser.py:parse_event_reply. standing_of is the calibration thermometer's word and
    # tests/bond_replay.py's report column; direction keeps its four bands for the actor.
    ("severity.py", "standing_of"):  "the standing ladder (bond-arithmetic.md s2): the thermometer's word and bond_replay's report; the actor keeps direction's four-band blocks until block_fidelity shows nine read differently",
}

# THE RATCHET, and why it is a ratchet rather than a failure. On the day this guard was written it
# found THIRTEEN capabilities that are built, TESTED, and reached from nowhere in src/ or scripts/ —
# a green test over code the pipeline never runs, which is this suite's whole subject. Failing
# run_all on thirteen pre-existing instances would get the guard switched off in a week, so the
# debt is RECORDED instead: these may not grow, and every one that gets wired must be deleted from
# here. A NEW unreached function still fails immediately, which is the property that matters.
#
# Each entry names where it IS tested, because "tested but unwired" is the specific shape and a
# reader should not have to re-derive it. Measured 2026-09-03.
UNWIRED_AT_FIRST_MEASUREMENT = {
    # THREE MORE LEFT 2026-09-10, by retirement not wiring: bonds.replay,
    # decay.record_belief_recall, toward.apply_deltas — bodies and reasons in
    # staging/src/engine/RETIRED-DEAD-FUNCTIONS-2026-09-10.py. And FIVE moved to EXEMPT above as
    # orchestrator surfaces: verify_envelope, resolve, tested, rubric, for_scene.
    # FOUR compounds.py ENTRIES REMOVED 2026-09-08 (blend, recipe_sum, separability, validate).
    # The ratchet's rule is that an entry leaves when its function gets WIRED; these left by the
    # other door -- the module was retired to staging with the primitive set it is keyed to. That
    # is still a legitimate exit: the ratchet exists to stop unreached code from GROWING, and
    # code that no longer exists cannot be unreached. Recipes preserved for the co-occurrence
    # future in docs/emotion-dynamics.md.
    # fold_recall_history left this list on 2026-09-04 — both chronicle drivers now call it
    # and feed the result to assemble(). Do not re-add it.
}


def _module_files():
    return sorted(f for f in os.listdir(ENGINE) if f.endswith(".py") and f != "__init__.py")


def _public_defs():
    """-> {(file, name): lineno} for every public top-level function in the engine."""
    out = {}
    for f in _module_files():
        tree = ast.parse(io.open(os.path.join(ENGINE, f), encoding="utf-8").read())
        for n in tree.body:
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
                out[(f, n.name)] = n.lineno
    return out


def _reached():
    """-> {(module_file, funcname)} actually reached, by MODULE-QUALIFIED reference.

    THREE DRAFTS, THREE BLIND SPOTS, each one the failure this suite exists to catch:

      1. CALLS ONLY. Missed `_bond_moves = _floor.bond_moves` re-exports — reported two functions I
         had moved myself that day as dead.
      2. CALLS ONLY, again. Missed higher-order dispatch: `lookup = bible.entity_exists if ... else
         bible.law_exists` (citation.py:176) and `(_t.fold_seed if ... else _t.fold_delta)(...)`
         (fold.py:74). Neither is a Call on the name.
      3. BARE NAMES. Counting any Load of the token `state` as reaching `read_api.state` marks a
         function live because some unrelated local variable shares its name — and `state`, `edges`
         and `said` are exactly the words this codebase uses for locals. That draft reported 207 of
         217 functions reached, which felt like good news and was an artifact of the English
         language.

    So the question is asked properly here: is there a reference QUALIFIED BY THE MODULE that
    defines it? `mod.f`, `from .mod import f`, or either through an aliased module (`from . import
    scene_cfg as _cfg` then `_cfg.for_scene`). A local named `state` cannot satisfy that.
    """
    modules = set(_module_files())
    modaliases = {}          # local name -> engine module basename, e.g. "_cfg" -> "scene_cfg.py"
    qualified = set()        # (module_file, funcname)
    direct = set()           # funcnames imported by name: from .mod import f
    files = []
    for d in SCAN:
        for f in sorted(os.listdir(d)):
            if f.endswith(".py"):
                files.append(os.path.join(d, f))

    for path in files:
        tree = ast.parse(io.open(path, encoding="utf-8").read())
        local = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                mod = (n.module or "").split(".")[-1]
                for a in n.names:
                    # `from src.engine import acquisition` and `from .records import TurnCommit` are
                    # the SAME shape. The third draft guessed by capitalisation and got both wrong.
                    # The module list decides it: if the imported name IS a module, it is an alias.
                    # ORDER MATTERS AND IT BIT ME. Test the SOURCE module first: in
                    # `from .state import decay`, both readings typecheck — `state` is a module and
                    # so, since 2026-09-03, is `decay`. Checking the imported name first read that
                    # as "import the decay module" and reported state.decay unreached. A new module
                    # whose name collides with an existing function silently inverts the parse.
                    if mod + ".py" in modules:
                        direct.add((mod + ".py", a.name))
                    elif a.name + ".py" in modules:
                        local[a.asname or a.name] = a.name + ".py"
            elif isinstance(n, ast.Import):
                for a in n.names:
                    base = a.name.split(".")[-1]
                    if base + ".py" in modules:
                        local[a.asname or base] = base + ".py"
        modaliases[path] = local
        own = os.path.basename(path)
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                mod = local.get(n.value.id)
                if mod:
                    qualified.add((mod, n.attr))
            # A BARE NAME INSIDE THE DEFINING MODULE. `bible.build` calls `fingerprint(...)` with no
            # qualifier, and that reaches it — scoping the bare name to its OWN file keeps this
            # correct without reopening the third draft's hole, where any local called `state`
            # anywhere in the tree marked read_api.state live.
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and own in modules:
                # CALL POSITION ONLY. Any bare Load was too loose even scoped to one file:
                # read_api.py has a LOCAL named `said`, which marked read_api.said() reached — the
                # bare-name hole from draft three, surviving at file scope. `build` calling
                # `fingerprint(...)` is still caught, because that is a Call.
                qualified.add((own, n.func.id))
    return qualified | direct


def _public_names_reached():
    return _reached()


def test_every_public_engine_function_is_REACHED_or_EXPLAINED():
    defs, reached = _public_defs(), _reached()
    unreached = sorted(k for k in defs if k not in reached)
    unexplained = [k for k in unreached if k not in EXEMPT and k not in UNWIRED_AT_FIRST_MEASUREMENT]
    print("       %d public engine function(s); %d unreached — %d exempt (public API), %d on the "
          "ratchet, %d UNEXPLAINED"
          % (len(defs), len(unreached), len([k for k in unreached if k in EXEMPT]),
             len([k for k in unreached if k in UNWIRED_AT_FIRST_MEASUREMENT]), len(unexplained)))
    check("every-unreached-function-is-explained", not unexplained,
          "unreached and unexplained: %s" % ", ".join("%s:%s()" % k for k in unexplained))


def test_no_EXEMPTION_outlives_the_thing_it_exempts():
    """The other direction, and the one exemption lists always rot in. An entry that names a function
    which is now reached — or no longer exists — is a reason nobody has re-read, and the list stops
    describing the tree the moment it stops being checked both ways."""
    defs, reached = _public_defs(), _reached()
    gone = [k for k in EXEMPT if k not in defs]
    now_wired = [k for k in EXEMPT if k in defs and k in reached]
    check("no-exemption-names-a-function-that-is-gone", not gone,
          "delete these: %s" % ", ".join("%s:%s()" % k for k in gone))
    check("no-exemption-names-a-function-that-is-now-reached", not now_wired,
          "these are wired now; drop the exemption: %s" % ", ".join("%s:%s()" % k for k in now_wired))


def test_the_RATCHET_only_shrinks():
    """An entry that is now WIRED must be deleted, or the list stops describing the tree. This is the
    direction every exemption list rots in: it is checked one way, so it only ever grows."""
    defs, reached = _public_defs(), _reached()
    fixed = [k for k in UNWIRED_AT_FIRST_MEASUREMENT if k in defs and k in reached]
    gone = [k for k in UNWIRED_AT_FIRST_MEASUREMENT if k not in defs]
    check("nothing-on-the-ratchet-is-wired-now", not fixed,
          "WIRED — delete from UNWIRED_AT_FIRST_MEASUREMENT: %s"
          % ", ".join("%s:%s()" % k for k in fixed))
    check("nothing-on-the-ratchet-has-been-deleted", not gone,
          "these functions no longer exist: %s" % ", ".join("%s:%s()" % k for k in gone))


def test_every_exemption_carries_a_REASON_not_just_a_name():
    both = dict(EXEMPT); both.update(UNWIRED_AT_FIRST_MEASUREMENT)
    thin = [k for k, v in both.items() if len(str(v).strip()) < 25]
    check("every-exemption-has-a-written-reason", not thin,
          "reasonless: %s" % ", ".join("%s:%s()" % k for k in thin))


def test_the_checker_can_FAIL():
    """The control. A guard that has only ever passed has not been shown to be able to fail, and this
    repo keeps a standing sticky about exactly that. Injects a public function no caller could
    reference and asserts the scan reports it."""
    defs, reached = dict(_public_defs()), _reached()
    defs[("__bait__.py", "a_function_nothing_calls")] = 1
    unreached = sorted(k for k in defs if k not in reached
                       and k not in EXEMPT and k not in UNWIRED_AT_FIRST_MEASUREMENT)
    check("an-unreached-function-is-detected",
          ("__bait__.py", "a_function_nothing_calls") in unreached,
          "the scan missed a function that is called nowhere")


def test_the_alias_resolution_is_LOAD_BEARING():
    """Proves the re-export handling matters rather than assuming it. Without it, functions the
    drivers reach only through a `_x = mod.x` re-export read as dead — measured 2026-09-03: two of
    twenty-one hits were this, and both were live."""
    defs = _public_defs()
    naive, resolved = set(), _reached()
    for d in SCAN:
        for f in sorted(os.listdir(d)):
            if not f.endswith(".py"):
                continue
            for n in ast.walk(ast.parse(io.open(os.path.join(d, f), encoding="utf-8").read())):
                if isinstance(n, ast.Call):
                    fn = n.func
                    if isinstance(fn, ast.Name):
                        naive.add(fn.id)
                    elif isinstance(fn, ast.Attribute):
                        naive.add(fn.attr)
    only_via_alias = sorted(k for k in defs if k in resolved and k[1] not in naive)
    check("alias-resolution-rescues-real-functions", bool(only_via_alias),
          "no function is reached only via a re-export; if that is now true, this test is obsolete "
          "and should be deleted rather than left passing vacuously")
    print("       reached ONLY through a re-export: %s"
          % (", ".join("%s:%s()" % k for k in only_via_alias) or "none"))


def main():
    print("test_reachable.py - every engine capability is reached, or is explained\n")
    for fn in sorted((v for k, v in globals().items()
                      if k.startswith("test_") and callable(v)),
                     key=lambda f: f.__code__.co_firstlineno):
        fn()
    print("\n%s" % ("test_reachable: OK (nothing is authored-and-inert without a reason)"
                    if not FAILS else "FAILED:"))
    for f in FAILS:
        print("  - %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
