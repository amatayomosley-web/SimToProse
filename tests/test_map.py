"""test_map.py — the routing table must describe the tree it routes into.

`docs/MAP.md` is the file CLAUDE.md orders every session to read FIRST, and its whole justification
is a measured failure: a session that skipped it spent hours re-deriving the decision layer, coined
a parallel vocabulary, and rebuilt a worse copy of a registry `decision-engine.md` already
specified. A routing table that omits things sends the reader to re-derive them — the exact cost it
exists to prevent, paid by the index itself.

It had drifted. Measured 2026-08-24: 18 of 24 modules listed, 49 of 62 docs, 29 of 40 suites — six
modules, thirteen docs and eleven suites invisible to the file that exists to make them visible.
`bonds`, `targets`, `levers`, `compounds`, `identity_view` and `profiles` were all missing, which is
most of what the preceding two days built.

MAP said its inventories "cannot drift from the code without the code changing". That was true for
a RENAMED title and false for an ADDED file, and additions were the entire failure — the
regeneration was a shell one-liner pasted into the doc, and nobody runs those. This suite runs
`scripts/gen_map.py --check`, so the claim is now enforced rather than asserted.
"""
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import gen_map                                                  # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def test_map_matches_the_tree():
    print("\n[1] MAP.md DESCRIBES THE TREE — every doc, module and suite has a row")
    out = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "gen_map.py"), "--check"],
                         cwd=REPO, capture_output=True, text=True)
    check("gen_map --check is clean", out.returncode == 0,
          (out.stdout + out.stderr).strip() or "run: python scripts/gen_map.py")

    text = io.open(gen_map.MAP, encoding="utf-8").read()
    missing = []
    for _pat, _heading, rows in gen_map.sections():
        for row in rows:
            name = row.split("`")[1]
            if ("`%s`" % name) not in text:
                missing.append(name)
    check("every-artifact-has-a-row", not missing, ", ".join(missing))


def test_regeneration_is_a_fixed_point():
    """Rendering twice must equal rendering once, or --check can never be clean.

    MAP listed ITSELF, and the rows carry line counts, so each regeneration changed MAP's length,
    which changed the row describing MAP. Self-inclusion is why this inventory could not be checked
    mechanically before — not a cosmetic detail, the reason the guard was impossible.
    """
    print("\n[2] FIXED POINT — the index does not index itself")
    cur = io.open(gen_map.MAP, encoding="utf-8").read()
    once = gen_map.render(cur)
    check("render-is-idempotent", gen_map.render(once) == once)
    check("map-does-not-list-itself",
          not any("`MAP`" in r for _p, _h, rows in gen_map.sections() for r in rows))


def test_the_check_can_fail():
    """A guard that has only ever passed has not been shown to be able to fail."""
    print("\n[3] CONTROL — a missing row is detected")
    cur = io.open(gen_map.MAP, encoding="utf-8").read()
    damaged = cur.replace("| `bonds` |", "| `bonds-REMOVED-BY-THE-CONTROL` |", 1)
    check("the-damage-applied", damaged != cur, "no bonds row to remove — the table shape changed")
    check("and-render-restores-it", "| `bonds` |" in gen_map.render(damaged))
    check("so-the-check-would-have-flagged-it", gen_map.render(damaged) != damaged)


# The Layer 1 engine modules already over CLAUDE.md rule 6's bound when the rule was first
# MEASURED (2026-08-24). This is DEBT, listed by name so it is visible on every run — not a
# tolerance. The test below fails if the set grows AND if it shrinks: a new name means a module
# crossed the line, and a departing name means this list is stale and should be tightened.
# Splitting these four is its own arc; recording them is not the same as accepting them.
# A RATCHET, not a permission slip. This was a set of NAMES, so a grandfathered file could grow
# without limit and the guard structurally could not object — measured 2026-09-01 by an adversarial
# review: bible 515->546, consolidation 525->650, gate 505->597, state 531->665, and this session
# added ~130 lines to state.py while the suite stayed green.
#
# It is a CEILING PER FILE now. Debt is allowed to persist and is not allowed to grow: work on one
# of these either shrinks it or splits it, and the number below only ever moves DOWN. A file that
# needs to grow is a file that needs splitting — which is what `snapshots.py`, `scene_cfg.py` and
# `world_events.py` are, each carved out the moment `ledger.py` crossed the line.
_OVER_AT_FIRST_MEASUREMENT = {
    # bible.py LEFT this list on 2026-09-03 at 546 lines — split into bible.py (the PIN) and
    # law.py (the RULING) because the debt had stopped being debt and started blocking work: a
    # ready delegation took it to 562 and this ratchet refused it. Removing it here is the point
    # of the ratchet, not a concession to it — the list is a high-water mark that must fall.
    "consolidation.py": 650,
    "gate.py":          521,
    "state.py":         606,
}


def test_the_500_line_rule_is_measured_at_all():
    """CLAUDE.md hard rule 6 — "Files under 500 lines... scoped to the Layer 1 engine".

    It was checked for ONE file. `tests/test_bonds.py:257` asserts it for `bonds.py`; nothing
    asserted it for the other twenty-three modules. A rule enforced on 1 of 24 files is a
    convention. MAP used to carry a `lines` column that let a reader notice by eye, which is
    probably why it was never mechanized; that column is gone (it made MAP stale on every edit to
    any file), so the check moves here.

    The first measurement found FOUR modules already over: bible 515, consolidation 525, gate 505,
    state 531. That is a finding, not a reason to raise the bound — tuning a threshold to the
    damage it just found is the failure this project spent three void probe runs learning to avoid.
    They are frozen by name above and the set is ratcheted in both directions.

    SCOPE: `src/engine/` only. CLAUDE.md:75 scopes the rule to the Layer 1 engine, so `scripts/`
    is deliberately out — and an earlier draft of this test asserted the scripts were "both within
    it" when direct.py is 584 and scene.py 591. Checked now rather than asserted.
    """
    print("")
    print("[4] RULE 6 IS MEASURED — every engine module, not just bonds.py")
    over, checked = {}, 0
    d = os.path.join(REPO, "src", "engine")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".py") or f == "__init__.py":
            continue
        n = sum(1 for _ in io.open(os.path.join(d, f), encoding="utf-8"))
        checked += 1
        if n >= 500:
            over[f] = n
    print("       %d modules checked; %d over the bound" % (checked, len(over)))
    for f, n in sorted(over.items()):
        print("       DEBT  %-22s %d lines" % (f, n))
    check("the-check-walks-the-whole-engine", checked >= 20,
          "only %d modules walked — the listing is wrong" % checked)
    check("no-NEW-module-crossed-500",
          not (set(over) - set(_OVER_AT_FIRST_MEASUREMENT)),
          "newly over: %s" % ", ".join(sorted(set(over) - set(_OVER_AT_FIRST_MEASUREMENT))))
    check("the-debt-list-is-not-stale",
          not (set(_OVER_AT_FIRST_MEASUREMENT) - set(over)),
          "back under the bound, remove from _OVER_AT_FIRST_MEASUREMENT: %s"
          % ", ".join(sorted(set(_OVER_AT_FIRST_MEASUREMENT) - set(over))))
    # THE RATCHET. Existing debt may stay; it may not GROW. Without this the two checks above pass
    # while a 505-line file becomes a 900-line one, which is how all four of these got where they
    # are. Lower the number when you shrink a file; never raise it.
    grew = ["%s %d -> %d" % (f, _OVER_AT_FIRST_MEASUREMENT[f], n)
            for f, n in sorted(over.items())
            if f in _OVER_AT_FIRST_MEASUREMENT and n > _OVER_AT_FIRST_MEASUREMENT[f]]
    check("no-GRANDFATHERED-module-grew", not grew,
          "over-bound files may not grow — split instead: %s" % "; ".join(grew))
    shrank = ["%s %d -> %d" % (f, _OVER_AT_FIRST_MEASUREMENT[f], n)
              for f, n in sorted(over.items())
              if f in _OVER_AT_FIRST_MEASUREMENT and n < _OVER_AT_FIRST_MEASUREMENT[f]]
    for line in shrank:                       # progress is REPORTED, never a failure
        print("       SHRANK  %s — lower it in _OVER_AT_FIRST_MEASUREMENT" % line)


def test_the_layer_marker_has_a_READER():
    """`__layer__ = "engine"` was declared by five modules and read by NOTHING.

    Measured 2026-09-03: grep over src/, scripts/ and tests/ returned zero non-declaration
    references. A declared-never-read key is the class this repo has spent a week removing
    (`_KNOWN_DIMS` discarding every appraisal, `run_config` guarded by an always-false hasattr,
    `verdict_for`'s teeth computed and consumed by no one) — and the fifth instance was added by
    the floor extraction, by me, the same day.

    THIS IS THE WEAK FORM, and the weakness is the point of saying so: it checks that every module
    which DECLARES the marker declares "engine" and lives under src/engine/. It does NOT require
    every engine module to declare one — roughly nineteen do not, and making that mandatory is a
    decision about whether the convention is wanted at all, not a test to smuggle in. What this
    stops is the marker drifting into a second value, or onto a file outside the engine, unnoticed.
    """
    import re
    declared = {}
    for root, _dirs, files in os.walk(os.path.join(REPO, "src")):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            m = re.search("""^__layer__\s*=\s*['"](.+?)['"]""",
                          io.open(path, encoding='utf-8').read(), re.M)
            if m:
                declared[os.path.relpath(path, REPO).replace("\\", "/")] = m.group(1)
    check("the-marker-is-declared-somewhere", bool(declared),
          "nobody declares __layer__ — the convention is gone, retire this test")
    wrong_value = {f: v for f, v in declared.items() if v != "engine"}
    check("every-declarer-says-engine", not wrong_value, wrong_value)
    misplaced = [f for f in declared if not f.startswith("src/engine/")]
    check("every-declarer-lives-in-the-engine", not misplaced, misplaced)
    print("       %d module(s) declare __layer__; this is the marker's only reader" % len(declared))


def main():
    print("test_map.py — the routing table, checked against the tree")
    # DISCOVERED, NOT LISTED — the duplicate CLAUDE.md tabulates, and the shape that hid a
    # determinism guard in test_scene.py for a whole run on 2026-09-01.
    for t in sorted((v for k, v in globals().items()
                     if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        t()
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
