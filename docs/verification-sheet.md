# verification-sheet — run these to prove the machinery works, not that the book is good

**Different question from `acceptance-criteria.md`.** That doc asks *is the finished novel any good*
— continuity, dramatic shape, prose. This one asks *does the machine do what it says*. A book can
fail acceptance while every check here passes; that is the point of separating them.

**Last executed 2026-08-24.** Every MACHINE row below was run to produce the result recorded beside
it. A verification sheet nobody has run is the defect class this repo has found nine times — a
promise with no producer. Re-run and update the results column; do not trust this header.

---

## Part A — MACHINE. Automated, no judgment, no model calls except where noted.

**Run all of it: `python scripts/verify.py --slow`** (drop `--slow` to skip A7, which is
reported SKIPPED rather than omitted). The script exists because Part A as prose is a
checklist, and this repo's record with checklists is poor — CLAUDE.md's verify block named
21 suites by hand while `tests/` held 39, and three of the eighteen never run were RED while
the block reported green. It shells out to the real commands rather than importing, so what
is verified is that the command a human would type produces the result this table claims.

| # | what it proves | command | pass condition | 2026-08-24 |
|---|---|---|---|---|
| A1 | every suite green | `python tests/run_all.py` | `43 passed, 0 failed` | **43/43** |
| A2 | the detectors can detect | `python tests/coherence_probe.py --stub` | `VERDICT: PASS` | **PASS** |
| A3 | **and can FAIL** — the control | `python tests/coherence_probe.py --corrupt` | `VERDICT: FAIL` with flags | **FAIL, 14 flags** |
| A4 | the routing table matches the tree | `python scripts/gen_map.py --check` | `MAP.md matches the tree` | **clean** |
| A5 | no private content, anywhere tracked | `python tests/test_no_private_content.py` | `VERDICT: PASS` + the terms line | **PASS** |
| A6 | no path outside this repo | `python tests/test_self_contained.py` | `VERDICT: PASS` | **PASS** |
| A7 | **the whole pipeline, end to end** | `python tests/test_pipeline_e2e.py` | `lint -> scenes -> boundaries -> dailies -> critic -> manuscript` | **OK** |

A3 is the row that matters most. A suite that has only ever passed has not been shown to be able to
fail — and this repo has shipped a guard with 19 green tests that would never have fired once.

## Part B — MECHANISM. Each closed defect, proved by the behaviour rather than by the test name.

Set `BOOK` to a book slug or path first. The fixture book used on 2026-08-24 was a scratch copy of
`world/ashford-slice.json` + `characters/*.json` in vault-note form.

| # | what it proves | command | pass condition | 2026-08-24 |
|---|---|---|---|---|
| B1 | props reach the actor | assemble a packet with `props` and grep the built prompt | the prop text appears in the user message | **3 props → 3 percepts → in prompt** |
| B2 | scene cfgs are validated against the BOOK | `python scripts/lint_scene.py --book $BOOK --scene <cfg>` | a cfg naming an unknown id ERRORS; a clean one exits 0 | **6 errors on the bad cfg, 0 on the good** |
| B3 | …and says what it did NOT check | same command | prints rules 4 and 6 as NOT CHECKED | **declared** |
| B4 | the canon digest has a producer | `python scripts/canon_digest.py --book $BOOK --stdout` | one line per event, folded snapshot, non-authoritative header | **4 events rendered** |
| B5 | an empty run says EMPTY | same, on a run with no events | the words "The log is EMPTY" | **stated** |
| B6 | the log cannot be rewritten | `UPDATE events …` on any chronicle | raises `append-only (CLAUDE.md hard rule 2)` | **refused** |
| B7 | …and an OLD db gains the protection | open a pre-v9 db with `db.connect` | `user_version` → 9, row count unchanged, UPDATE refused | **v1→v9, 300 events kept** |
| B8 | the caches stay mutable | `UPDATE runs SET status=…` | succeeds | **succeeds** |
| B9 | the act seam emits a prompt | `direct.py --prompt-only --circumstance "…"` | JSON messages on stdout, DB untouched | **emitted** |
| B10 | …and accepts a turn from outside | `direct.py --turn-json turn.json --circumstance "…"` | `committed`, and the turn appears in the DB | **committed + acquisition** |
| B11 | a supplied turn passes the faithfulness wall | supply a turn using a masked name | refused, recorded as turn-skipped | **wall fires on masked names** |
| B12 | bible drift is detected on resume | edit a character note, then `--resume` | `[!] bible drifted: run pinned X, on disk Y` | **fires on both drivers** |
| B13 | edges survive a resume | resume a run with committed deltas | `refolded N edge movement(s) toward …` | **refolded** |

## Part C — HUMAN. These need a person. No command proves them.

| # | the question | how to look | what a failure looks like |
|---|---|---|---|
| C1 | do the stage directions read as instructions, not moods? | run any scene, read the `now :` line | "you are anxious" rather than "you check the ways out" |
| C2 | can you tell two characters apart with the names removed? | take 10 lines from a scene, strip attributions, guess | you cannot beat chance |
| C3 | does a beat land without being forced? | read a scene against its intended beat | the character does the plot-required thing for no reason of their own |
| C4 | does the critic catch a real contradiction? | plant one, run `critic.py` | it reports clean |
| C5 | is the prose a story or a transcript? | read `manuscript.md` cold | stage-direction log, scene-by-scene summary |

C2 is the one with a measured protocol behind it — `docs/measurement.md` §4, blinded, n≥2 judges,
anchored scoring. The others are honest human reads and should be labelled as such when reported.

## Part D — NOT VERIFIED BY ANYTHING HERE

Stated so a full green sheet is never mistaken for a working system:

- **No book has ever been produced.** `CLAUDE.md`'s Status has said "next genuine step: run one"
  since 2026-07-24. A7 runs two stub scenes on a fixture; that is a pipeline test, not a book.
- **Quality at any model size is unmeasured.** Part C has never been run with real judges on real
  output.
- **The small-model design is unbuilt.** `docs/small-model-mode.md` is a design; nothing in Part A
  or B exercises it, and its 10k claim rests on measurements of parts.
- **`scene.py` has no act seam.** B9–B11 cover `direct.py` only.
- **Rules 4 and 6** of scene authoring are semantic and unmechanized — B3 asserts only that the
  linter SAYS so.
