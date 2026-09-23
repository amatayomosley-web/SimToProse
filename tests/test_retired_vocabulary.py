"""test_retired_vocabulary.py — a migration's old words may not stay alive anywhere in the tree.

THE DEFECT CLASS. Every migration retires a vocabulary — a table, a field, a function, a unit — and
the code that was migrated stops using it. The scripts and docs that were NOT in the gate keep it,
silently, and read as live: `scripts/gen_rungs.py` carried `PATH_SOURCE` two days after the engine
deleted it and regenerated the old shape on demand; `docs/SPEC-LEDGER.md` listed "Seven Panksepp
primaries as the state vector — BUILT" after the paths replaced them. Owner, 2026-09-10: "my
concern is scripts that should be deprecated or updated that are flying under the radar." This is
the radar.

WHAT IT ASSERTS. Every retired symbol below is either absent from a line, or the line MARKS it as
retired (the words in `_RETIREMENT_MARKERS`), or the file is a DATED RECORD (a review or
measurement written in that day's vocabulary — listed in `_DATED_RECORDS` with a reason, and
required to carry a vocabulary note near its top so a reader is told). In src/ and scripts/ the
count of live uses must be ZERO. In docs/ and .claude/ it is a RATCHET: the baseline below may
shrink and may not grow, and any new file with a live use fails by name — the same shape as
tests/test_reachable.py's debt list.

HOW TO ADD A MIGRATION. Append its symbols to `RETIRED` with the date and the replacement, run this
file, clean what it names or put a dated record on the list with a reason, and set the baseline to
what remains. The cost is paid at the migration, not discovered a month later.

Stdlib only. Exit 0 = all pass.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")      # a doc line with a glyph must not crash the radar

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

_FAILS = []

# (symbol regex, retired on, replaced by)
RETIRED = (
    # 2026-09-08: the eight PATHS became the stored state; the Panksepp primitives left the engine
    (r"\bPATH_SOURCE\b",            "2026-09-08", "nothing — the paths ARE the state (records.PATHS)"),
    (r"\bPRIMARIES\b",              "2026-09-08", "records.PATHS (error-code NAMES containing the word are allowed)"),
    (r"\b_DIM_TO_PRIMARY\b",        "2026-09-08", "state._DIM_TO_PATH"),
    (r"\bdirect_affect\b",          "2026-09-08", "the rung blocks (composer.select + direction_for)"),
    (r"\bcompounds\.py\b",          "2026-09-08", "staging/src/engine/compounds.py — retired with the primitives"),
    # 2026-09-09: the recovery tier
    (r"\brecovery_state_for_peak\b", "2026-09-09", "nothing — moved to staging/RETIRED-RECOVERY-TIER.md"),
    (r"\bis_recovery_active\b",     "2026-09-09", "nothing — retired"),
    # 2026-09-10: the three-cell genotype
    (r"\bthreat_reactivity\b",      "2026-09-10", "genotype[WARINESS].hit"),
    (r"\bapproach_drive\b",         "2026-09-10", "genotype[STIRRING].hit"),
    (r"\baffiliation_attachment\b", "2026-09-10", "genotype[GOODWILL].hit / genotype[DEFLATION].hit"),
    (r"\banger_proneness\b",        "2026-09-10", "genotype[DISPLEASURE].hit"),
    (r"\beffortful_control\b",      "2026-09-10", "nothing — cut; resilience renormalised (arc.py)"),
    (r"\b_HEXACO_SENSITIVITY_MAP\b", "2026-09-10", "nothing — cut (a second source of g)"),
    (r"\bAXIS_FOR\b",               "2026-09-10", "nothing — axis == path"),
    (r"\b_REG_FLOOR\b",             "2026-09-10", "nothing — cut with effortful_control"),
    (r"\bapply_hold\b",             "2026-09-10", "state.half_life_minutes / state.retention_for"),
    (r"profile\[.sensitivity.\]",   "2026-09-10", "nothing — cut"),
    (r"\bdecay_rates\b",            "2026-09-10", "profile[\"hold\"] + state._HALF_LIFE"),
    # 2026-09-10: the minute clock
    (r"\b_DECAY_RATE\b",            "2026-09-10", "state._HALF_LIFE (minutes, two zones)"),
    (r"\"elapsed\"\s*:",            "2026-09-10", "cfg `at` (+ optional `lasts`); elapsed is DERIVED (clock.py)"),
    (r"cfg\.get\(\"elapsed\"\)",    "2026-09-10", "clock.gap_before"),
    # 2026-09-10: the lever-eval harness (dead cast, primitive vocabulary, no test, no results file)
    (r"\bexp\.py\b",                "2026-09-10", "nothing — staging/scripts/exp.py; a harness is re-authored against the clock when levers are tuned (bounds-experiment-design.md)"),
    # 2026-09-11: gate three — wounds are engine state at baseline.wounds, keyed by a registry concept
    (r"fears_wounds",           "2026-09-11", "baseline.wounds (engine state: wound.py, concepts.py); the sheet block is refused by lint"),
)

# A line that says the thing is gone is not a live use.
_RETIREMENT_MARKERS = re.compile(
    r"retired|RETIRED|was |gone|no longer|superseded|until 2026|cut |CUT |refus|OLD_AXES|staging/|"
    r"replaced|renamed|used to|before 2026|pre-clock|primitive-era|the old |~~", re.I)

# Error-code names are not uses of a retired table. (PRIMARIES inside RECORD_AFFECT_MISSING_PRIMARIES.)
_CODE_NAME = re.compile(r"[A-Z]+_[A-Z_]*PRIMARIES")

# DATED RECORDS: reviews and measurements written in that day's vocabulary. Rewriting them would
# falsify the record; instead each carries a vocabulary note near the top and is exempt below.
_DATED_RECORDS = {
    "docs/goal-alignment-review.md":  "a dated audit (2026-08) of the engine against the design; its numbers were measured in the primitive vocabulary",
    "docs/standard-vectors.md":       "a dated measurement doc (2026-08) of the standard vectors; the recipes cite staging paths already",
    "docs/basis-verification.md":     "a dated verification (2026-08) of the emotion basis",
    "docs/emotion-basis.md":          "the primitive-era basis doc, superseded by emotion-paths.md; kept as the record of why",
    "docs/emotion-recipes.md":        "the compound recipes, retired with compounds.py; kept as the record",
    "docs/emotion-dynamics.md":       "primitive-era dynamics notes; superseded by emotion-arithmetic.md",
    "docs/composition-pass.md":       "spec written before the genotype rebuild; its genotype examples are dated",
    "docs/rungs/SELF-REGARD-behavioural-review.md": "a dated behavioural review",
    "docs/rungs/DISPLEASURE-behavioural-review.md": "a dated behavioural review (2026-09-08)",
    "docs/rungs/RECEPTIVITY-behavioural-review.md": "a dated behavioural review (2026-09-08)",
    "docs/rungs/SELF-REGARD.md":      "rung doc whose STATUS notes are dated",
    "docs/rungs/STIRRING.md":         "rung doc whose STATUS notes are dated",
    "docs/bounds-experiment-design.md": "a pre-registered DESIGN (2026-08-22) whose runner is specified as 'exp.py's shape'; exp.py retired 2026-09-10",
}
_NOTE_RE = re.compile(r"vocabulary|dated|retired|superseded|primitive-era", re.I)

# THE RATCHET: live doc/.claude uses per file. May shrink, may not grow. A file not listed here must have ZERO.
_DOC_BASELINE = {
    # MEASURED 2026-09-10 after the sweep: every live doc use was cleaned or the file was listed as a
    # dated record, so the baseline is EMPTY and the ratchet is already the rule — any live use in
    # any doc fails by name.
}

SCAN = ("src", "scripts", "tests", "docs", ".claude")
SKIP_DIRS = ("staging", "__pycache__", ".git", "runs",
             "emotion-names")   # the retired naming corpus (docs/emotion-names/) — staging/WHY-EMOTION-NAMES-IS-HERE.md


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


def _files():
    for top in SCAN:
        root = os.path.join(REPO, top)
        if not os.path.isdir(root):
            continue
        for d, dirs, fns in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for fn in fns:
                if fn.endswith((".py", ".md")) and fn != os.path.basename(__file__):
                    yield os.path.relpath(os.path.join(d, fn), REPO).replace(os.sep, "/")


def live_uses():
    """-> {relpath: [(lineno, symbol, line)]} of retired symbols used as if live."""
    out = {}
    pats = [(re.compile(p), p, when, repl) for p, when, repl in RETIRED]
    for rel in _files():
        try:
            lines = io.open(os.path.join(REPO, rel), encoding="utf-8").read().splitlines()
        except UnicodeDecodeError:
            continue
        in_doc = False                        # .py: a comment or a docstring is history, not a use
        for i, line in enumerate(lines, 1):
            if rel.endswith(".py"):
                q = line.count('"""') + line.count("\'\'\'")
                if in_doc:
                    if q % 2 == 1:
                        in_doc = False
                    continue
                if q % 2 == 1:
                    in_doc = True
                    continue
                if q >= 2:                    # a one-line docstring
                    continue
                if line.lstrip().startswith("#"):
                    continue
                if "#" in line and _RETIREMENT_MARKERS.search(line.split("#", 1)[1]):
                    continue
            if _RETIREMENT_MARKERS.search(line):
                continue
            for rx, p, when, repl in pats:
                if rx.search(line):
                    if "PRIMARIES" in p and _CODE_NAME.search(line) and not re.search(r"\bPRIMARIES\b(?![_A-Z])", line.replace(_CODE_NAME.search(line).group(0), "")):
                        continue
                    out.setdefault(rel, []).append((i, p, line.strip()[:110]))
    return out


def main():
    print("test_retired_vocabulary.py — a migration's old words may not stay alive")
    uses = live_uses()
    code = {k: v for k, v in uses.items() if k.startswith(("src/", "scripts/", "tests/"))}
    docs = {k: v for k, v in uses.items() if not k.startswith(("src/", "scripts/", "tests/"))}

    print("\n[1] CODE — zero live uses in src/, scripts/, tests/")
    for rel, hits in sorted(code.items()):
        for ln, sym, text in hits[:4]:
            print("       %s:%d  %s   | %s" % (rel, ln, sym, text))
    check("no-retired-symbol-is-used-live-in-code", not code, "%d file(s): %s" % (len(code), sorted(code)[:5]))

    print("\n[2] DATED RECORDS — exempt, but each must SAY it is in an older vocabulary")
    missing_note = []
    for rel, why in sorted(_DATED_RECORDS.items()):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            continue
        head = "\n".join(io.open(p, encoding="utf-8").read().splitlines()[:12])
        if not _NOTE_RE.search(head):
            missing_note.append(rel)
    check("every-dated-record-carries-a-vocabulary-note-near-its-top", not missing_note, missing_note)

    print("\n[3] DOCS — the ratchet: live uses per file may shrink, never grow; new files must be clean")
    grew, new = [], []
    for rel, hits in sorted(docs.items()):
        if rel in _DATED_RECORDS:
            continue
        n = len(hits)
        base = _DOC_BASELINE.get(rel)
        line = "       %-48s %3d live (baseline %s)" % (rel, n, "—" if base is None else base)
        print(line)
        for ln, sym, text in hits[:2]:
            print("           :%d %s | %s" % (ln, sym, text[:80]))
        if base is None:
            new.append(rel)
        elif n > base:
            grew.append("%s %d>%d" % (rel, n, base))
    shrank = [rel for rel, base in _DOC_BASELINE.items()
              if len([h for h in docs.get(rel, [])]) < base]
    if shrank:
        print("       shrank (lower the baseline): %s" % ", ".join(shrank))
    check("no-doc-grew-its-live-uses", not grew, grew)
    check("no-new-doc-carries-a-live-use", not new, new)

    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
