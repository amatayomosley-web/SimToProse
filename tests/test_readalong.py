"""test_readalong.py — a synthetic book through the read-along harness, under the stub seat.

scripts/readalong.py reads a novel through the appraiser seat and runs the engine's arithmetic
downstream, into a chronicle in the book's own runs/. Real books live outside the repo, so this
suite builds a SYNTHETIC one in a temp directory (hard rule 1 holds: no book content here — the
text below is engine-fixture prose, invented for the segmenter and the stub seat) and pins:

  1. SEGMENTATION. Beats never cross a chapter; a break line ends one; the heading is not a beat.
  2. THE SIDECAR IS THE CLOCK. `at` per chapter is refused when malformed, by name.
  3. THE RUN. Under --stub a passage that names a registry concept in a durable-height reading
     mints a scar on the right path, the readings ride the turns, the binds are logged, and the
     chronicle is append-only.
  4. THE REPORT'S COMPARISON. `patterns` carries `state_vs_thermometer` — the independent
     thermometer seat against the engine's carried state, at every logged point — and no longer
     `score`, the older, self-referential comparison (both sides read off the same readings table),
     retired 2026-09-19 (gate emotion-tier-tidy; docs/emotion-arithmetic.md section 5).
  5. THE REGISTRY'S GAPS are collected as measurement, never applied.
  6. EMIT AND REPLAY (2026-09-11; owner: one agent per prompt, never a batch). `emit` writes one
     prompt per seat call, keyed on the prompt; a run over the replies refuses BEFORE any turn is
     written while one is unanswered; answered, it replays into readings, mints the scar, logs
     every call with the model, and treats a malformed answer as an idle beat with a row of its own.

Stdlib only. Exit 0 = all pass.
"""
import io
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import readalong as RA                                        # noqa: E402
from src.engine import rungs as _rungs                        # noqa: E402
from src.engine.records import PATHS, RecordError             # noqa: E402

_FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        _FAILS.append(name)


_CH1 = "CHAPTER I\n\n" + "\n\n".join([
    "The healer walked the long road home with the basket on her arm and the light going.",
    "Nothing had happened all day. The cart was mended. The bread was bought. She counted the coins twice.",
    "* * *",
    "At the door the boy was waiting, and his face was hot, and she knew the sickness before he spoke! It was the fever again!!",
])
_CH2 = "CHAPTER II\n\n" + "\n\n".join([
    "The next morning the road was dry and the boy was asleep and breathing evenly.",
    "She thought about the sickness while she worked, and then she did not think about it, and the day went on.",
])


def _book(tmp, slug="synthetic", ch2_lasts=None, bonds=None):
    d = os.path.join(tmp, "readalong", slug)
    os.makedirs(os.path.join(d, "characters"))
    text = _CH1 + "\n\n\n" + _CH2 + "\n"
    io.open(os.path.join(d, "text.txt"), "w", encoding="utf-8").write(text)
    s1 = text.index("CHAPTER I")
    s2 = text.index("CHAPTER II")
    chapters = [{"index": 1, "title": "CHAPTER I", "start": s1, "end": s2, "at": {"day": 1, "time": "18:00"}, "lasts": 60},
                {"index": 2, "title": "CHAPTER II", "start": s2, "end": len(text), "at": {"day": 2, "time": "08:00"}, "lasts": ch2_lasts}]
    io.open(os.path.join(d, "chapters.json"), "w", encoding="utf-8").write(json.dumps(chapters))
    sheet = {"fixed": {"id": "healer", "name": "Healer", "genotype": {}},
             "baseline": {"temperament": {"WARINESS": {"rest": "raised"}}},
             "current": {"relationships": bonds} if bonds else {}}
    io.open(os.path.join(d, "characters", "healer.json"), "w", encoding="utf-8").write(json.dumps(sheet))
    io.open(os.path.join(d, "cast.json"), "w", encoding="utf-8").write(json.dumps({"protagonist": "healer", "people": {"boy": {"name": "the boy"}}}))
    return d


def test_segmentation_and_the_sidecar(tmp):
    print("\n[1/2] SEGMENTATION AND THE SIDECAR")
    d = _book(tmp)
    text, chapters, sheet, cast = RA.load_book(d)
    beats = RA.segment(text, chapters, beat_words=40)
    check("beats-never-cross-a-chapter", all(b["chapter"] in (1, 2) for b in beats) and any(b["chapter"] == 2 for b in beats))
    check("a-break-line-ends-a-beat", any("sickness" in b["text"] and "basket" not in b["text"] for b in beats), [b["text"][:40] for b in beats])
    check("the-heading-is-not-a-beat", not any(b["text"].strip().startswith("CHAPTER") and b["words"] < 8 for b in beats))
    check("the-sheet-was-seeded", "mean" in sheet["baseline"]["temperament"]["WARINESS"] and sheet["baseline"]["wounds"] == [])
    bad = json.load(io.open(os.path.join(d, "chapters.json"), encoding="utf-8"))
    del bad[0]["at"]
    io.open(os.path.join(d, "chapters.json"), "w", encoding="utf-8").write(json.dumps(bad))
    try:
        RA.load_book(d)
        check("a-chapter-without-at-is-refused-by-name", False, "did not raise")
    except RecordError as exc:
        check("a-chapter-without-at-is-refused-by-name", "READALONG_SIDECAR_INVALID" in str(exc), str(exc)[:80])
    shutil.rmtree(d)


def test_the_run_and_the_report(tmp):
    print("\n[3/4/5] THE RUN, THE REPORT'S COMPARISON, THE GAPS")
    d = _book(tmp)
    lines = []
    run_id = RA.run(d, stub=True, beat_words=40, log=lines.append)
    db = os.path.join(d, "runs", "%s.db" % run_id)
    check("a-chronicle-was-written-in-the-books-runs", os.path.isfile(db))
    import sqlite3
    con = sqlite3.connect(db)
    n_turns = con.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    n_read = con.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    scars = con.execute("SELECT concept, path, intensity FROM wound_minted").fetchall()
    check("every-beat-is-a-turn", n_turns >= 3, n_turns)
    check("the-readings-ride-the-turns", n_read >= 1, n_read)
    check("the-fever-beat-minted-a-sickness-scar-on-WARINESS", any(c == "sickness" and p == "WARINESS" for c, p, _i in scars), scars)
    check("the-scar-was-announced", any("SCAR" in ln for ln in lines), lines[:3])
    try:
        con.execute("DELETE FROM readings")
        check("the-chronicle-is-append-only", False, "DELETE succeeded")
    except sqlite3.IntegrityError as exc:
        check("the-chronicle-is-append-only", "append-only" in str(exc))
    con.close()
    # THE PATTERNS REPORT — what the text shows, with counts (owner: the live runs define the
    # patterns the rules for the numbers come from). `score` (the self-referential prediction
    # check, both sides off the same readings table) is retired (2026-09-19, gate
    # emotion-tier-tidy); `state_vs_thermometer`, checked below, is the comparison that means
    # something, and it is the only one checked here now.
    run2 = RA.run(d, stub=True, beat_words=40, log=lambda *_a: None, thermometer=1)
    pat = RA.patterns(d, run2)
    check("no-score-key-in-the-report", "score" not in pat, sorted(pat))
    check("the-gap-list-is-empty-under-the-stub", pat["concept_gaps"] == [])
    check("the-report-counts-the-beats", pat["beats"] == n_turns, pat["beats"])
    con = sqlite3.connect(os.path.join(d, "runs", "%s.db" % run2))
    read_beats = con.execute("SELECT COUNT(DISTINCT turn) FROM readings").fetchone()[0]
    con.close()
    check("the-idle-rate-is-arithmetic-on-the-log",
          pat["idle"]["silent"] == pat["beats"] - read_beats
          and abs(pat["idle"]["silent_rate"] - pat["idle"]["silent"] / float(pat["beats"])) < 1e-3, pat["idle"])
    check("every-read-path-carries-its-counts",
          all({"readings", "rungs", "peaks", "persistence_beats_after_peak", "repetition_delta"} <= set(v) for v in pat["per_path"].values()), pat["per_path"])
    check("the-thermometer-was-logged", pat["thermometer_points"] == n_turns, pat["thermometer_points"])
    check("a-half-life-slot-exists-per-read-path", set(pat["half_life_from_thermometer"]) == set(pat["per_path"]))
    check("the-scar-table-is-a-list", isinstance(pat["scars"], list))
    # THE SCARS RUN ON STORY TIME, NOT ON CHAPTERS (gate bench-clock, 2026-09-24). The bench aged only the mood and
    # refolded its scars with no time in the fold, so the fever's scar stood at full strength through the night
    # before chapter two. It now takes the drivers' one step (`passage.age`) and their fold (`passage.fold_wounds`).
    from src.engine import clock as _ck, passage as _pas, wound as _wd
    from src.engine.ledger import Ledger
    bond = {"trust": 0.8, "affinity": 0.9, "respect": 0.7, "debt": 0.0}
    dc = _book(tmp, slug="synthetic-clock", ch2_lasts=120, bonds={"boy": dict(bond)})   # chapter two takes two hours
    held, steps, real_age = [], [], _pas.age
    _pas.age = lambda chars, minutes, rest_rows: (held.append(chars), steps.append(float(minutes or 0.0)),
                                                  real_age(chars, minutes, rest_rows))[2]
    try:
        run3 = RA.run(dc, stub=True, beat_words=40, log=lambda *_a: None)
    finally:
        _pas.age = real_age
    led3 = Ledger(os.path.join(dc, "runs", "%s.db" % run3))
    stretches = [m for _t, _s, m in _ck.time_items(led3.con, run3)]
    check("chapter-two's-beats-carry-minutes", any(s_ == 3 and t_ > 0 for t_, s_, _m in _ck.time_items(led3.con, run3)))
    check("every-stretch-the-log-holds-is-a-step-the-bench-took-in-order", [m for m in steps if m > 0] == stretches,
          repr(([m for m in steps if m > 0], stretches)))
    folded = _pas.fold_wounds(led3.con, run3, "healer", RA.load_book(dc)[2])
    timeless = RA.load_book(dc)[2]
    _wd.fold(timeless, _wd.mints_for(led3.con, run3, "healer"), led3.wound_deltas_for(run3, "healer"))
    scar = lambda ws: [w["intensity"] for w in ws if w.get("concept") == "sickness"]
    check("the-bench's-own-scar-is-the-fold-of-its-log", held and scar(held[-1]["healer"]["baseline"]["wounds"]) == scar(folded)
          and scar(folded), repr((scar(held[-1]["healer"]["baseline"]["wounds"]) if held else None, scar(folded))))
    check("...and-the-night-before-chapter-two-eased-it", scar(folded) and scar(folded)[0] < scar(timeless["baseline"]["wounds"])[0],
          repr((scar(folded), scar(timeless["baseline"]["wounds"]))))
    check("an-unreinforced-bond-rests-where-the-sheet-put-it", held and held[-1]["healer"]["current"]["relationships"]["boy"] == bond,
          held[-1]["healer"]["current"]["relationships"]["boy"] if held else None)
    led3.con.close()
    svt = pat["state_vs_thermometer"]
    check("the-state-is-compared-with-the-thermometer-at-every-point",
          svt["points"] == pat["thermometer_points"] and svt["compared"] == svt["points"] * len(PATHS)
          and isinstance(svt["mean_abs_error_state"], float) and isinstance(svt["mean_abs_error_rest"], float), svt)
    check("every-read-path-carries-its-bias-and-lowest-rung-rate",
          all({"bias_median", "state_median", "level_median", "lowest_rung_rate"} <= set(v) for v in svt["per_path"].values())
          and set(svt["per_path"]) >= set(pat["per_path"]), list(svt["per_path"]))


def test_emit_and_replay(tmp):
    print("\n[6] EMIT AND REPLAY — one answer per prompt, keyed on the prompt")
    import glob
    import sqlite3
    d = _book(tmp, slug="synthetic-replay")          # its own book: an open chronicle blocks rmtree on Windows
    seats = os.path.join(d, "seats")
    counts = RA.emit(d, seats, beat_words=40, thermometer=2)
    text, chapters, _sheet, _cast = RA.load_book(d)
    n_beats = len(RA.segment(text, chapters, beat_words=40))
    check("one-prompt-per-beat-plus-the-thermometer",
          counts["emotion"] == n_beats and counts["thermometer"] == (n_beats + 1) // 2, (counts, n_beats))
    prompts = sorted(glob.glob(os.path.join(seats, "*.prompt.json")))
    check("the-prompt-files-match-the-count", len(prompts) == counts["prompts"], len(prompts))
    check("the-prompts-carry-the-book-and-the-turn",
          all({"book", "turn", "chapter"} <= set(json.load(io.open(p, encoding="utf-8"))["meta"]) for p in prompts))
    try:
        RA.run(d, replies=seats, beat_words=40, thermometer=2, log=lambda *_a: None)
        check("an-unanswered-prompt-refuses-the-run-by-name", False, "did not raise")
    except RecordError as exc:
        check("an-unanswered-prompt-refuses-the-run-by-name", "PROVIDER_REPLY_MISSING" in str(exc), str(exc)[:80])
    check("no-chronicle-was-written-for-the-refused-run", not glob.glob(os.path.join(d, "runs", "*.db")))
    # ANSWER EVERY PROMPT: the fever beat reads sickness at the top of WARINESS, the rest are quiet;
    # the thermometer reads one level. One quiet beat's answer is garbage, on purpose.
    top = _rungs.names_on("WARINESS")[-1]
    garbage = None
    for p in prompts:
        row = json.load(io.open(p, encoding="utf-8"))
        user = row["messages"][-1]["content"]
        if row["purpose"] == "thermometer":
            reply = json.dumps({"levels": {"WARINESS": _rungs.names_on("WARINESS")[3]}})
        elif "fever" in user:
            reply = json.dumps({"readings": [{"path": "WARINESS", "rung": top, "about": "concept:sickness"}],
                                "lands_on": [], "confidence": "sure"})
        elif garbage is None:
            garbage, reply = row["key"], "not a json object at all"
        else:
            reply = json.dumps({"readings": [], "lands_on": [], "confidence": "sure"})
        io.open(RA._provider.reply_path(seats, row["key"]), "w", encoding="utf-8").write(reply)
    lines = []
    run_id = RA.run(d, replies=seats, beat_words=40, thermometer=2, log=lines.append)
    check("the-replay-run-leaves-the-http-path-off-for-the-process", RA._provider.replies_dir() == seats)
    RA._provider.use_replies(None)
    con = sqlite3.connect(os.path.join(d, "runs", "%s.db" % run_id))
    n_turns = con.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    scars = con.execute("SELECT concept, path FROM wound_minted").fetchall()
    llm = {(p, m): n for p, m, n in con.execute("SELECT purpose, model, COUNT(*) FROM llm_calls GROUP BY purpose, model")}
    refused = [m for (p, m), n in llm.items() if p == "seat-refused"]
    con.close()
    check("every-beat-replayed-into-a-turn", n_turns == n_beats, (n_turns, n_beats))
    check("the-replayed-fever-beat-minted-the-sickness-scar", ("sickness", "WARINESS") in scars, scars)
    check("every-replayed-call-is-logged-with-the-model",
          llm.get(("appraise-emotion", "subagent:opus")) == n_beats and llm.get(("thermometer", "subagent:opus")) == counts["thermometer"], llm)
    check("the-garbage-answer-is-an-idle-beat-with-a-row-of-its-own",
          len(refused) == 1 and "APPRAISER_REPLY_NOT_JSON" in refused[0], refused)
    levels = io.open(os.path.join(d, "runs", "%s.levels.jsonl" % run_id), encoding="utf-8").read().splitlines()
    check("the-thermometer-levels-were-logged", len(levels) == counts["thermometer"], len(levels))


def main():
    print("test_readalong.py — a synthetic book through the read-along harness")
    tmp = tempfile.mkdtemp(prefix="stp-readalong-")
    saved = os.environ.get("SWE_BOOKS")
    os.environ["SWE_BOOKS"] = tmp
    try:
        test_segmentation_and_the_sidecar(tmp)
        test_the_run_and_the_report(tmp)
        test_emit_and_replay(tmp)
    finally:
        if saved is None:
            os.environ.pop("SWE_BOOKS", None)
        else:
            os.environ["SWE_BOOKS"] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nVERDICT: %s" % ("PASS" if not _FAILS else "FAIL -> %s" % _FAILS))
    return 1 if _FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
