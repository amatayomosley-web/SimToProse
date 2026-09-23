#!/usr/bin/env python3
"""test_rungs.py — the float-to-rung resolver, and the two properties it exists to guarantee.

WHY THIS MODULE EXISTS AT ALL. Until 2026-09-07 nothing in `src/engine/` turned a number into a rung.
`direction.py` bands a float into a PHRASE and never into a named position, and the only resolver
ever built was parked in staging/ because it derived position from RANK in word-pool files that
turned out not to be ordered. The composer must select the rung a character is ALREADY at — never
choose one — so without this function every downstream design was blocked.

THE TWO PROPERTIES, and both are the kind that fail silently:

  1. THE BANDS TILE. Half-open [lo, hi), no gap, no overlap, covering 0.0 through 1.0 inclusive. A
     gap means some affect value resolves to nothing; an overlap means two rungs claim one value and
     which wins depends on iteration order. Neither would raise — the first returns a confusing
     error at a random threshold, the second returns a plausible wrong answer forever.

  2. NO NAME REACHES THE BLOCK. The rung name is an authoring and selection handle and is measured
     INERT as direction: 2026-09-07, nine draws across three label conditions with byte-identical
     text beneath, the arm labelled `annoyance` over violent text scored HIGHER than the arm labelled
     `fury`, and a blind judge's grouping cut clean across the label conditions. Since the label buys
     nothing, delivering it only risks a future model weighting the word over the paragraph. This
     asserts the delivered text carries no path name, no primitive name and no rung name.

Script-style, stdlib only, exit 0 = all pass.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import rungs                                    # noqa: E402
from src.engine.rung_blocks import BANDS, BLOCKS                # noqa: E402
from src.engine.records import PATHS                        # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  - " + detail) if (detail and not cond) else ""))


def test_the_bands_tile_the_interval():
    """A gap resolves some value to nothing; an overlap makes two rungs claim one value and lets
    iteration order decide. Neither raises on its own, so both are asserted here."""
    print("\n[1] THE BANDS TILE 0..1 WITH NO GAP AND NO OVERLAP")
    for path in rungs.paths():
        band = BANDS[path]
        check("%s-starts-at-zero" % path, band[0][0] == 0.0, str(band[0]))
        check("%s-top-edge-covers-a-saturated-vector" % path, band[-1][1] > 1.0,
              "top edge %r must exceed 1.0 or affect==1.0 falls through" % (band[-1][1],))
        gaps = [(band[i][1], band[i + 1][0]) for i in range(len(band) - 1)
                if abs(band[i][1] - band[i + 1][0]) > 1e-9]
        check("%s-has-no-gap-or-overlap" % path, not gaps, str(gaps))
        widths = [round(hi - lo, 6) for lo, hi, _ in band[:-1]] + [round(1.0 - band[-1][0], 6)]
        check("%s-widths-sum-to-one" % path, abs(sum(widths) - 1.0) < 1e-9, str(sum(widths)))


def test_every_value_resolves_and_the_order_is_monotone():
    print("\n[2] EVERY VALUE RESOLVES, AND CLIMBING THE FLOAT CLIMBS THE RUNG")
    for path in rungs.paths():
        seen, last = [], 0
        v = 0.0
        while v <= 1.0 + 1e-9:
            i, _ = rungs.rung_at(path, min(v, 1.0))
            if i != last:
                seen.append(i)
                last = i
            v += 0.001
        check("%s-visits-every-rung-once-climbing" % path,
              seen == list(range(1, len(BANDS[path]) + 1)), str(seen))
        check("%s-a-saturated-vector-lands-on-the-peak" % path,
              rungs.rung_at(path, 1.0)[0] == len(BANDS[path]), str(rungs.rung_at(path, 1.0)))


def test_the_delivered_block_carries_no_name():
    """The property the label experiment bought. A block is what the actor reads; a rung name in it
    would let the word do the work the paragraph is supposed to do."""
    print("\n[3] NO PATH, PRIMITIVE OR RUNG NAME REACHES THE DELIVERED BLOCK")
    paths_designed = ["DISPLEASURE", "WARINESS", "GOODWILL", "RECEPTIVITY", "SELF-REGARD",
                      "DISTASTE", "DEFLATION", "LEVITY", "STIRRING"]
    for path in rungs.paths():
        names = [nm for _, _, nm in BANDS[path]]
        for i in range(1, len(BANDS[path]) + 1):
            text = rungs.block_for(path, i).lower()
            own = names[i - 1]
            check("%s-r%02d-does-not-name-its-own-rung" % (path, i), own not in text, own)
            leaked = [p for p in paths_designed if re.search(r"\b%s\b" % re.escape(p.lower()), text)]
            check("%s-r%02d-names-no-path" % (path, i), not leaked, str(leaked))
            prim = [p for p in PATHS if re.search(r"\b%s\b" % p.lower(), text)]
            check("%s-r%02d-names-no-primitive" % (path, i), not prim, str(prim))
            check("%s-r%02d-carries-no-state-label" % (path, i), "[state:" not in text, "label survived")


def test_an_unbuilt_path_fails_loudly():
    """Eight of nine paths are designed and unwritten. Returning empty for those would be the
    declared-but-never-connected defect this repo names as its dominant class."""
    print("\n[4] A DESIGNED-BUT-UNBUILT PATH RAISES RATHER THAN READING EMPTY")
    for path in ("WARINESS", "DEFLATION", "LEVITY"):
        if path in rungs.paths():
            continue
        for fn, args in ((rungs.rung_at, (path, 0.5)), (rungs.block_for, (path, 1))):
            try:
                fn(*args)
                check("%s-%s-refused" % (path, fn.__name__), False, "it returned instead of raising")
            except rungs.RungError as e:
                # ASSERT THE CODE, NOT THE PROSE. A first draft matched on the words "not built" and
                # went red on `block_for`, whose message says the same thing differently — a test of
                # the wording, not of the behaviour.
                check("%s-%s-refused" % (path, fn.__name__), e.code == "RUNG_PATH_NOT_BUILT", str(e)[:70])


def test_bad_input_is_refused():
    print("\n[5] A VALUE THE ENGINE COULD NOT HAVE PRODUCED IS REFUSED")
    for value, label in ((1.4, "above one"), (-0.2, "below zero"), ("x", "not a number"), (None, "none")):
        try:
            rungs.rung_at("DISPLEASURE", value)
            check("refuses-%s" % label.replace(" ", "-"), False, "accepted %r" % (value,))
        except rungs.RungError:
            check("refuses-%s" % label.replace(" ", "-"), True)
    try:
        rungs.block_for("DISPLEASURE", 99)
        check("refuses-an-index-that-does-not-exist", False)
    except rungs.RungError:
        check("refuses-an-index-that-does-not-exist", True)


def test_descent_is_fallback_safe_until_authored():
    """Redesign gate 3 (2026-09-12): block_for gains `descending`, driven by the resolver's
    hysteresis. Until DESCENT_BLOCKS is authored it is INERT — a falling value plays the same climb
    block, so the flag can be wired in the drivers before any prose exists. PIVOTS names the rung
    above which a descent block WILL take over; DISPLEASURE's is anger (in-doc), GOODWILL/DISTASTE
    have none (care cannot fall; revulsion ends when the thing is gone)."""
    print("\n[7] DESCENT IS FALLBACK-SAFE UNTIL AUTHORED")
    for path in rungs.paths():
        n = len(BANDS[path])
        for i in range(1, n + 1):
            if rungs.DESCENT_BLOCKS.get(path, {}).get(i):
                continue                                  # an authored descent block legitimately differs
            check("%s-r%02d-descent-falls-back-to-climb" % (path, i),
                  rungs.block_for(path, i, descending=True) == rungs.block_for(path, i), path)
    check("DISPLEASURE-pivot-is-anger", rungs.PIVOTS["DISPLEASURE"] == rungs.index_of("DISPLEASURE", "anger"))
    check("GOODWILL-and-DISTASTE-have-no-descent", "GOODWILL" not in rungs.PIVOTS and "DISTASTE" not in rungs.PIVOTS)


def test_the_descent_signal():
    """Redesign gate 3, the wiring (2026-09-15): `descending` is the ONE place the direction of travel
    is decided — origin == mood AND no reading at the actor's last beat AND the MOOD's rung above the
    pivot. Every clause is necessary; the table below flips one at a time. No peak, no prior rung."""
    print("\n[8] THE DESCENT SIGNAL — origin, fuel, pivot, each necessary")
    top = {p: BANDS[p][-1][0] + 1e-6 for p in rungs.paths()}         # every path at its top rung
    rest = {p: 0.0 for p in rungs.paths()}
    quiet = {p: "mood" for p in rungs.paths()}
    # 1. above every pivot, mood-set, no reading ever, actor has a last beat -> descending where a pivot exists
    d = rungs.descending(top, quiet, {}, 4)
    for p in rungs.paths():
        check("%s-top-no-fuel-%s" % (p, "descends" if p in rungs.PIVOTS else "never"),
              d[p] == (p in rungs.PIVOTS), d[p])
    # 2. fuel at the last beat -> climbing, even at the top
    fed = rungs.descending(top, quiet, {p: 4 for p in rungs.paths()}, 4)
    check("fuel-at-last-beat-is-climbing", not any(fed.values()), fed)
    # 3. fuel at an OLDER beat is no fuel
    stale = rungs.descending(top, quiet, {p: 3 for p in rungs.paths()}, 4)
    check("a-reading-two-beats-ago-is-not-fuel", all(stale[p] for p in rungs.PIVOTS), stale)
    # 4. a plateau held by attitude or lift is not a come-down
    held = rungs.descending(top, {p: "attitude" for p in rungs.paths()}, {}, 4)
    check("attitude-plateau-keeps-the-climb", not any(held.values()), held)
    lifted = rungs.descending(top, {p: "lift" for p in rungs.paths()}, {}, 4)
    check("lift-plateau-keeps-the-climb", not any(lifted.values()), lifted)
    # 5. at or below the pivot nothing swaps, whatever the fuel
    for p, piv in rungs.PIVOTS.items():
        at = dict(rest); at[p] = BANDS[p][piv - 1][0] + 1e-6                # exactly the pivot rung
        check("%s-at-the-pivot-is-not-descending" % p, not rungs.descending(at, quiet, {}, 4)[p])
        above = dict(rest); above[p] = BANDS[p][piv][0] + 1e-6              # one rung above it
        check("%s-one-above-the-pivot-is" % p, rungs.descending(above, quiet, {}, 4)[p])
    # 6. beat one: no last turn -> no fuel, but every mood at rest -> nothing swaps
    first = rungs.descending(rest, quiet, {}, None)
    check("beat-one-at-rest-swaps-nothing", not any(first.values()), first)
    # 7. a path missing from the mood, or an origin missing, defaults safe
    part = rungs.descending({"DISPLEASURE": top["DISPLEASURE"]}, {}, {}, 4)
    check("missing-origin-reads-mood", part["DISPLEASURE"] is True)
    check("missing-path-is-not-descending", all(not part[p] for p in rungs.paths() if p != "DISPLEASURE"))
    try:
        rungs.descending("not a mood", {}, {}, 1)
        check("refuses-a-non-dict-mood", False, "accepted")
    except rungs.RungError as e:
        check("refuses-a-non-dict-mood", e.code == "RUNG_MOOD_NOT_A_DICT", e.code)


def test_the_generator_compiles_a_descent_section():
    """Gate 3, step 2 (2026-09-15): `gen_rungs` reads a '## The descent blocks' section per rung doc
    into DESCENT_BLOCKS, and refuses the shapes that would put the wrong text on the way down —
    a rung at or below the pivot, a path with no pivot, a section that covers only some of the rungs
    above the pivot, a name that disagrees with BANDS, a duplicate rung. The climb parser stops at
    the descent section, so no climb block is overwritten. Proven on a temp copy of DISPLEASURE.md."""
    print("\n[9] THE GENERATOR COMPILES A DESCENT SECTION")
    import io as _io
    import shutil
    import tempfile
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import gen_rungs as G
    piv = rungs.PIVOTS["DISPLEASURE"]
    names = {i: nm for i, (_, _, nm) in enumerate(BANDS["DISPLEASURE"], start=1)}
    top = len(BANDS["DISPLEASURE"])

    def block(i, text=None):
        return "\n### %d — %s\n\n**[State: %s]**\n%s\n\n- **The Sensation.** s.\n- **The Belief.** b.\n- **The Impulse.** i.\n" % (
            i, names[i], names[i], text or "DESCENT %d: coming down through %s. What ends this is rest." % (i, names[i]))

    def section(*idxs, **over):
        body = "\n## The descent blocks\n\nRules paragraph.\n" + "".join(block(i) for i in idxs)
        for i, txt in over.items():
            body += "\n### %s — %s\n\n%s\n" % (i.lstrip("r"), names[int(i.lstrip("r"))], txt)
        return body

    def stripped(path):
        """The tree's doc WITHOUT its descent section (the tree carries one since gate 3b)."""
        src = _io.open(os.path.join(REPO, "docs", "rungs", "%s.md" % path), encoding="utf-8").read()
        head, tail = src.split("## What must still be measured", 1)
        head = head.split("## The descent blocks", 1)[0]
        return head, tail

    def doc_with(sec, path="DISPLEASURE"):
        head, tail = stripped(path)
        return head + sec + "\n## What must still be measured" + tail

    saved_docs = G.DOCS
    tmp = tempfile.mkdtemp(prefix="rungs-descent-")
    try:
        G.DOCS = tmp
        def write(path, text):
            _io.open(os.path.join(tmp, "%s.md" % path), "w", encoding="utf-8").write(text)

        for p in rungs.paths():                      # every doc, with its descent section removed
            write(p, doc_with("", p))

        def refuses(label, path, sec, needle):
            write(path, doc_with(sec, path))
            try:
                G.descent_blocks_from(path)
                check(label, False, "it was ACCEPTED")
            except SystemExit as e:
                check(label, needle in str(e), str(e)[:90])

        # a doc with no section -> {}
        check("no-section-is-empty", G.descent_blocks_from("DISPLEASURE") == {})
        # a complete section above the pivot compiles, the label is stripped, the climb is untouched
        write("DISPLEASURE", doc_with(section(*range(piv + 1, top + 1))))
        out = G.descent_blocks_from("DISPLEASURE")
        check("compiles-every-rung-above-the-pivot", sorted(out) == list(range(piv + 1, top + 1)), sorted(out))
        check("the-label-does-not-reach-the-text", all("[State:" not in t for t in out.values()))
        check("the-text-is-the-descent-text", out[top].startswith("DESCENT %d" % top), out[top][:40])
        check("the-climb-parser-stops-at-the-section", G.blocks_from("DISPLEASURE") == BLOCKS["DISPLEASURE"])
        # an empty section is a scaffold, not an error
        write("DISPLEASURE", doc_with(section()))
        check("an-empty-section-is-a-scaffold", G.descent_blocks_from("DISPLEASURE") == {})
        # the refusals, one shape each
        refuses("refuses-a-rung-at-the-pivot", "DISPLEASURE", section(*range(piv, top + 1)), "at or below the pivot")
        refuses("refuses-a-partial-section", "DISPLEASURE", section(*range(piv + 1, top)), "all or nothing")
        refuses("refuses-a-path-with-no-pivot", "GOODWILL", "\n## The descent blocks\n\n### %d — %s\n\ntext\n" % (len(BANDS["GOODWILL"]), BANDS["GOODWILL"][-1][2]),
                "no pivot")
        bad_name = section(*range(piv + 1, top + 1)).replace("### %d — %s" % (top, names[top]), "### %d — hostility" % top)
        refuses("refuses-a-name-that-disagrees-with-BANDS", "DISPLEASURE", bad_name, "one of them is wrong")
        dup = section(*range(piv + 1, top + 1)) + block(top)
        refuses("refuses-a-duplicate-rung", "DISPLEASURE", dup, "appears twice")
        empty_text = section(*range(piv + 1, top)) + "\n### %d — %s\n\n**[State: %s]**\n\n" % (top, names[top], names[top])
        refuses("refuses-an-empty-block", "DISPLEASURE", empty_text, "no block text")
        # served: a compiled section reaches block_for above the pivot and not at it
        write("DISPLEASURE", doc_with(section(*range(piv + 1, top + 1))))
        compiled = G.descent_blocks_from("DISPLEASURE")
        saved = rungs.DESCENT_BLOCKS
        rungs.DESCENT_BLOCKS = {"DISPLEASURE": compiled}
        try:
            check("served-above-the-pivot-when-descending", rungs.block_for("DISPLEASURE", top, descending=True) == compiled[top])
            check("not-served-when-climbing", rungs.block_for("DISPLEASURE", top, descending=False) == BLOCKS["DISPLEASURE"][top])
            check("not-served-at-the-pivot", rungs.block_for("DISPLEASURE", piv, descending=True) == BLOCKS["DISPLEASURE"][piv])
        finally:
            rungs.DESCENT_BLOCKS = saved
    finally:
        G.DOCS = saved_docs
        shutil.rmtree(tmp, ignore_errors=True)
    # the generated module carries the table, one key per path
    from src.engine import rung_blocks as RB
    check("rung_blocks-carries-DESCENT_BLOCKS-for-every-path", set(RB.DESCENT_BLOCKS) == set(BANDS))
    check("GOODWILL-and-DISTASTE-are-empty-by-design", RB.DESCENT_BLOCKS["GOODWILL"] == {} and RB.DESCENT_BLOCKS["DISTASTE"] == {})


def test_the_descent_prose_obeys_the_block_rules():
    """Gate 3b (2026-09-15): the 22 descent blocks are compiled and each obeys, mechanically, what the
    climb blocks obey — no rung name, no path, no digit, no [State:] label, the three bullets — plus
    the descent rules: a terminator clause on its own clock, and text that is NOT the climb's. Every
    pivoted path covers exactly the rungs above its pivot; GOODWILL and DISTASTE carry none."""
    print("\n[10] THE DESCENT PROSE — every pivoted path, above the pivot only, by the rules")
    from src.engine.rung_blocks import DESCENT_BLOCKS as D
    paths_designed = ["DISPLEASURE", "WARINESS", "GOODWILL", "RECEPTIVITY", "SELF-REGARD",
                      "DISTASTE", "DEFLATION", "LEVITY", "STIRRING"]
    total = 0
    for path in rungs.paths():
        names = [nm for _, _, nm in BANDS[path]]
        have = sorted(D.get(path, {}))
        if path not in rungs.PIVOTS:
            check("%s-has-no-descent-by-design" % path, have == [], str(have))
            continue
        piv = rungs.PIVOTS[path]
        want = list(range(piv + 1, len(BANDS[path]) + 1))
        check("%s-descent-covers-exactly-the-rungs-above-the-pivot" % path, have == want, "%s vs %s" % (have, want))
        for i in have:
            total += 1
            text = D[path][i]
            low = text.lower()
            tag = "%s-r%02d-descent" % (path, i)
            check(tag + "-differs-from-the-climb", text != BLOCKS[path][i])
            check(tag + "-is-served-by-block_for", rungs.block_for(path, i, descending=True) == text)
            check(tag + "-does-not-name-its-own-rung", names[i - 1] not in low, names[i - 1])
            leaked = [p for p in paths_designed if re.search(r"\b%s\b" % re.escape(p.lower()), low)]
            check(tag + "-names-no-path", not leaked, str(leaked))
            check(tag + "-carries-no-digit", not re.search(r"\d", text), "digit")
            check(tag + "-carries-no-state-label", "[state:" not in low, "label survived")
            check(tag + "-has-the-three-bullets", all(k in text for k in ("**The Sensation.**", "**The Belief.**", "**The Impulse.**")))
            check(tag + "-names-what-ends-it", ("What ends this is" in text) or ("What would take this away is" in text))
            # rule 3 of the descent: the terminator is this rung's own clock, never the cause answered
            term = re.search(r"(What ends this is|What would take this away is)[^.]*\.", text)
            check(tag + "-terminator-is-not-the-climbs",
                  bool(term) and not re.search(r"confront|repudiat|neutraliz|reckoning|reversal", term.group(0).lower()),
                  term.group(0)[:80] if term else "no terminator sentence")
    check("twenty-two-descent-blocks", total == 22, total)


def main():
    print("test_rungs.py - the float-to-rung resolver\n")
    for t in sorted((v for k, v in globals().items() if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        try:
            t()
        except Exception as e:                       # noqa: BLE001 - a harness reports, never raises
            check("%s RAISED %s" % (t.__name__, type(e).__name__), False, str(e)[:150])
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
