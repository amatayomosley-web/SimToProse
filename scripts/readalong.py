#!/usr/bin/env python3
"""readalong.py — read a novel through the appraiser seat and run the engine's arithmetic on it.

THE BENCH NOBODY HERE WROTE. Owner, 2026-09-11: take real books, wire them into the engine, run
the systems over them — and no local models, because the seat is the basis of the system and it
has to be accurate. A published novel is a stimulus with no stake in the result (the 2026-09-10
learning: an author-built stimulus encodes its own answer), and its emotional arc is legible to
any reader. So: the emotion seat is the ONLY model in the loop; everything downstream is the same
arithmetic the drivers run — decay first, the receipt from readings (`state.receive`), aboutness
from readings, the mint, the trial — into a chronicle in the book's own `runs/`.

WHAT THE LIVE RUNS ARE FOR — owner, 2026-09-11: *"we need to test real text to define real
patterns we can use to make the rules for our numbers."* Not a grade. An instrument. `patterns`
reads the run's readings, the chapter clock and the thermometer's levels and reports, per path
and per book, the shapes each number is a rule about:

  * PERSISTENCE after a peak — beats and story-minutes an elevated path stays elevated, and the
    thermometer's level over story time after the peak -> the HALF-LIFE per path.
  * BUILD — how many consecutive elevated readings before the level stands at the rung -> LAMBDA.
  * REPETITION — the same about again on the same path: does the next reading sit higher or
    lower, split (for people) by whether they are on the page -> q and its two directions.
  * PRESENCE — elevation while the object is on the page versus after it leaves.
  * SCARS — the rung at which a concept once read at the top comes back, against a concept never
    peaked -> the wound's multiplier and how long it lasts.
  * THE IDLE RATE — the fraction of beats with no reading at all, and with only low-rung readings;
    on the two CONTROL books this is the noise floor every other number is read against.
  * THE BASIS — which paths fire together, which never do.

`score` (the older question: does the engine's pre-beat rung predict the seat's reading better
than rest, both sides read off the same readings table) was RETIRED 2026-09-19 (gate
emotion-tier-tidy) — self-referential, and superseded by `state_vs_thermometer`, above: an
INDEPENDENT thermometer seat against the engine's carried state, the comparison
`emotion-arithmetic.md` section 5 actually reports.

THE THERMOMETER. The emotion seat is a sensor for what AROSE and is blind to the standing level by
design (spec section 7). A half-life is a statement about the level over time, so every
`--thermometer N` beats a second, measurement-only seat is asked where the character STANDS on
each ladder; its answers are logged beside the run (`<run>.levels.jsonl`) and never applied.

THE BOOK LIVES OUTSIDE THE REPO (hard rule 1): `$SWE_BOOKS/readalong/<slug>/` holds `text.txt`,
`chapters.json` (offsets + the story clock `at`/`lasts` per chapter, authored from the text),
`characters/<id>.json` (the protagonist's sheet — rest words, genotype, no wounds) and `cast.json`.
The chronicle goes to `<slug>/runs/`. Nothing in this file names a book.

BEATS. Paragraphs grouped to about `--beat-words` words, never crossing a chapter boundary; a
run of blank lines or a `* * *` line ends a beat. The chapter's `at` opens it; its `lasts` (when
the sidecar gives one) is shared across its beats as the per-beat minutes; between chapters the
gap is derived from the next `at`, exactly as scenes do.

    python scripts/readalong.py --book red-badge --stub          # deterministic, no model
    python scripts/readalong.py --book red-badge                 # the seat on the frontier model
    python scripts/readalong.py --book red-badge --patterns <run>  # the report for a finished run
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import arc as _arc                                  # noqa: E402
from src.engine import bond_rest as _bond_rest                      # noqa: E402
from src.engine import clock as _clock                              # noqa: E402
from src.engine import concepts as _concepts                        # noqa: E402
from src.engine import passage as _passage                          # noqa: E402
from src.engine import readings as _readings                        # noqa: E402
from src.engine import replies as _replies                          # noqa: E402
from src.engine import rungs as _rungs                              # noqa: E402
from src.engine import targets as _targets                          # noqa: E402
from src.engine import wound as _wound                              # noqa: E402
from src.engine.ledger import Ledger                                # noqa: E402
from src.engine.records import PATHS, Event, RecordError, TurnCommit, WoundDelta   # noqa: E402
from src.engine.state import build_profile, decay, receive          # noqa: E402
from src.engine.heritable import ensure_temperament                 # noqa: E402
import appraiser                                                    # noqa: E402
import provider as _provider                                        # noqa: E402

_BREAK = re.compile(r"^\s*(\*\s*){3,}\s*$|^\s*[-_]{3,}\s*$")


# ---------------------------------------------------------------------------------------------
# THE BOOK
# ---------------------------------------------------------------------------------------------

def books_root():
    root = os.environ.get("SWE_BOOKS")
    if not root:
        raise RecordError("READALONG_TEXT_MISSING", "set SWE_BOOKS: the read-along corpus lives under $SWE_BOOKS/readalong/")
    return os.path.join(root, "readalong")


def load_book(book_dir):
    """book dir -> (text, chapters, sheet, cast). Refuses a malformed sidecar by name."""
    tp = os.path.join(book_dir, "text.txt")
    if not os.path.isfile(tp):
        raise RecordError("READALONG_TEXT_MISSING", "no text.txt in %s" % book_dir)
    text = io.open(tp, encoding="utf-8").read()
    cp = os.path.join(book_dir, "chapters.json")
    try:
        chapters = json.load(io.open(cp, encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise RecordError("READALONG_SIDECAR_INVALID", "%s: %s" % (cp, e))
    if not isinstance(chapters, list) or not chapters:
        raise RecordError("READALONG_SIDECAR_INVALID", "%s is not a non-empty list" % cp)
    for ch in chapters:
        for k in ("index", "start", "end", "at"):
            if not isinstance(ch, dict) or k not in ch:
                raise RecordError("READALONG_SIDECAR_INVALID", "%s: a chapter lacks %r" % (cp, k))
        ch["at_minutes"] = _clock.parse_at(ch["at"])
        ch["lasts_minutes"] = _clock.span_minutes(ch.get("lasts")) if ch.get("lasts") else None
    cast_p = os.path.join(book_dir, "cast.json")
    cast = json.load(io.open(cast_p, encoding="utf-8")) if os.path.isfile(cast_p) else {}
    pid = cast.get("protagonist")
    cdir = os.path.join(book_dir, "characters")
    if not pid:
        sheets = sorted(f for f in os.listdir(cdir)) if os.path.isdir(cdir) else []
        if len(sheets) != 1:
            raise RecordError("READALONG_SHEET_MISSING", "%s: cast.json names no protagonist and characters/ holds %d sheets" % (book_dir, len(sheets)))
        pid = sheets[0][:-5]
    sp = os.path.join(cdir, "%s.json" % pid)
    if not os.path.isfile(sp):
        raise RecordError("READALONG_SHEET_MISSING", "no sheet at %s" % sp)
    sheet = json.load(io.open(sp, encoding="utf-8"))
    for sec in ("fixed", "baseline", "current"):
        sheet.setdefault(sec, {})
    sheet["fixed"].setdefault("id", pid)
    ensure_temperament(sheet)
    sheet["current"].setdefault("affect", {p: sheet["baseline"]["temperament"][p]["mean"] for p in PATHS})
    sheet["current"].setdefault("condition", {"energy": 0.8, "allostatic_load": 0.2})
    sheet["current"].setdefault("relationships", {})
    sheet["current"].setdefault("targets", {})
    sheet["baseline"].setdefault("wounds", [])
    return text, chapters, sheet, cast


def segment(text, chapters, beat_words=300):
    """text + chapters -> [beat dicts]. Never crosses a chapter; a break line or blank run ends one."""
    beats = []
    for ch in chapters:
        body = text[int(ch["start"]):int(ch["end"])]
        paras, cur = [], []
        for line in body.split("\n"):
            if _BREAK.match(line) or not line.strip():
                if cur:
                    paras.append(" ".join(cur).strip())
                    cur = []
                if _BREAK.match(line):
                    paras.append(None)                       # a hard break
                continue
            cur.append(line.strip())
        if cur:
            paras.append(" ".join(cur).strip())
        title = str(ch.get("title", "")).strip().lower()
        if paras and paras[0] is not None and title and paras[0].strip().lower().rstrip(".") == title.rstrip("."):
            paras = paras[1:]                                # the heading is not a beat's prose
        buf, n = [], 0
        for p in paras:
            if p is None:
                if buf:
                    beats.append({"chapter": ch["index"], "text": "\n\n".join(buf), "words": n})
                    buf, n = [], 0
                continue
            w = len(p.split())
            if buf and n + w > beat_words:
                beats.append({"chapter": ch["index"], "text": "\n\n".join(buf), "words": n})
                buf, n = [], 0
            buf.append(p)
            n += w
        if buf:
            beats.append({"chapter": ch["index"], "text": "\n\n".join(buf), "words": n})
    # the chapter heading itself is not a beat: drop a first beat that is only the title
    return [b for b in beats if b["words"] >= 8]


def _surfaces(passage):
    """The passage's sentences — what the character perceived, for the wound's phrase match."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", passage) if s.strip()]


# ---------------------------------------------------------------------------------------------
# THE SEAT
# ---------------------------------------------------------------------------------------------

def stub_seat(passage, cast_ids):
    """A deterministic double for --stub: a reading when the passage names a registry concept's
    gloss word or a cast id, at a rung read off the ladder by the passage's exclamation count.
    Measures nothing about the seat; exercises everything after it."""
    low = passage.lower()
    rows = []
    for cid, gloss in _concepts.REGISTRY.items():
        key = cid.replace("_", " ")
        if re.search(r"\b%s\b" % re.escape(key), low):
            path = {"sickness": "WARINESS", "loss of a child": "DEFLATION", "death": "DEFLATION",
                    "betrayal": "DISPLEASURE", "shame": "SELF-REGARD"}.get(key, "WARINESS")
            names = _rungs.names_on(path)
            k = min(len(names), 2 + low.count("!") * 4)      # three marks reach the top of a 13-rung ladder
            rows.append({"path": path, "rung": names[k - 1], "about": _concepts.about(cid)})
    for pid in cast_ids:
        if re.search(r"\b%s\b" % re.escape(pid.lower()), low) and not rows:
            rows.append({"path": "GOODWILL", "rung": _rungs.names_on("GOODWILL")[1], "about": pid})
    return {"readings": rows, "lands_on": [], "confidence": "sure"}


# ---------------------------------------------------------------------------------------------
# THE RUN
# ---------------------------------------------------------------------------------------------

def stub_level(affect):
    """The stub thermometer: the engine's own float, read as a rung. Measures nothing."""
    return {p: _rungs.rung_at(p, float(affect[p]))[1] for p in PATHS}


def _seat_prompts(beats, cast_ids, pid, thermometer=0):
    """Every prompt the run sends, in the run's order -> (turn, purpose, messages). ONE builder for
    the emit and for the run's pre-check, so the keys cannot drift apart: the emotion seat sees the
    passage, the cast and the protagonist; the thermometer sees the passage and the protagonist."""
    for turn, b in enumerate(beats):
        yield turn, "appraise-emotion", appraiser.build_emotion_messages(b["text"], "", moment="", present=cast_ids, me=pid)
        if thermometer and turn % int(thermometer) == 0:
            yield turn, "thermometer", appraiser.build_thermometer_messages(b["text"], me=pid)


def emit(book_dir, out_dir, beat_words=300, limit=None, thermometer=0, model=None):
    """Write every seat prompt the run would send, for out-of-process answers (one agent per prompt,
    never a batch), touching nothing in the engine -> {"prompts", "emotion", "thermometer", "dir"}.
    The prompts carry book text, so `out_dir` must live beside the book, never in the repo."""
    text, chapters, sheet, cast = load_book(book_dir)
    beats = segment(text, chapters, beat_words)
    if limit:
        beats = beats[:int(limit)]
    pid = sheet["fixed"]["id"]
    cast_ids = sorted((cast.get("people") or {}).keys())
    model = model or "subagent:opus"
    slug = os.path.basename(book_dir.rstrip("/\\"))
    counts = {"appraise-emotion": 0, "thermometer": 0}
    for turn, purpose, messages in _seat_prompts(beats, cast_ids, pid, thermometer):
        _provider.emit(messages, model, purpose, out_dir, meta={"book": slug, "turn": turn, "chapter": beats[turn]["chapter"]})
        counts[purpose] += 1
    manifest = {"book": slug, "model": model, "beats": len(beats), "beat_words": beat_words, "thermometer": thermometer,
                "prompts": sum(counts.values()), "emotion": counts["appraise-emotion"], "thermometer_prompts": counts["thermometer"]}
    with io.open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    return {"prompts": manifest["prompts"], "emotion": counts["appraise-emotion"], "thermometer": counts["thermometer"], "dir": out_dir}


def run(book_dir, stub=False, model=None, beat_words=300, limit=None, seat=None, log=print, thermometer=0, replies=None):
    """Read the book beat by beat through the seat and the engine into a chronicle. -> run_id.
    `thermometer=N` asks the level every N beats (0 = never) and logs it beside the run.
    `replies=DIR` replays answers written for the emitted prompts (one agent per prompt); every
    prompt must be answered before a single turn is written, or the run refuses by name."""
    text, chapters, sheet, cast = load_book(book_dir)
    beats = segment(text, chapters, beat_words)
    if limit:
        beats = beats[:int(limit)]
    pid = sheet["fixed"]["id"]
    cast_ids = sorted((cast.get("people") or {}).keys())
    if replies:
        _provider.use_replies(replies)
        model = model or "subagent:opus"
        unanswered = [k for _t, _p, m in _seat_prompts(beats, cast_ids, pid, thermometer)
                      for k in (_provider.prompt_key(m),) if not os.path.isfile(_provider.reply_path(replies, k))]
        if unanswered:
            raise RecordError("PROVIDER_REPLY_MISSING", "%d prompt(s) unanswered under %s; first: %s"
                              % (len(unanswered), replies, unanswered[0]))
    model = model or _provider.seat_model()
    runs_dir = os.path.join(book_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    import uuid as _uuid
    run_id = "readalong-%s-%d-%s" % (os.path.basename(book_dir.rstrip("/\\")), int(time.time()), _uuid.uuid4().hex[:6])
    led = Ledger(os.path.join(runs_dir, "%s.db" % run_id))
    led.create_run(run_id, {"catalog_version": 1, "models": {"seat": "stub" if stub else model},
                            "prompt_versions": {"emotion_seat": 4},
                            "readalong": {"beats": len(beats), "beat_words": beat_words, "thermometer": int(thermometer or 0),
                                          "replies": os.path.basename(replies.rstrip("/\\")) if replies else None}})
    led.register_character(run_id, pid, sheet["fixed"], sheet["baseline"])
    _bond_rest.seed(led.con, run_id, 0, pid, sheet["current"].get("relationships") or {})   # where its bonds rest, as the drivers seed
    _rests = lambda i: _bond_rest.rows_for(led.con, run_id, i)
    levels_path = os.path.join(runs_dir, "%s.levels.jsonl" % run_id)
    levels_out = io.open(levels_path, "w", encoding="utf-8") if thermometer else None
    carried = {}                        # (seat, key) -> beats: what the seats' replies carried beyond their contracts
    profile = build_profile(sheet)
    temp = sheet["baseline"]["temperament"]
    affect = dict(sheet["current"]["affect"])
    targets = dict(sheet["current"].get("targets") or {})
    last_at, per_beat = None, 0.0
    by_chapter = {}
    for b in beats:
        by_chapter.setdefault(b["chapter"], []).append(b)
    turn = 0
    for ch in chapters:
        cb = by_chapter.get(ch["index"]) or []
        if not cb:
            continue
        # THE CLOCK: the gap since the last chapter ended, then this chapter's share per beat.
        # MONOTONE: a sidecar may open a chapter before the previous one's authored span has run
        # out (a nominal placeholder `at` on a summary chapter, or a frame's clock against a
        # manuscript's); the story cannot run backwards, so such a chapter opens where the last
        # one ended and the recorded clock says so.
        at_eff = ch["at_minutes"] if last_at is None else max(ch["at_minutes"], last_at)
        gap = 0.0 if last_at is None else max(0.0, at_eff - last_at)
        per_beat = (ch["lasts_minutes"] / float(len(cb))) if ch.get("lasts_minutes") else 0.0
        last_at = at_eff + (ch["lasts_minutes"] or 0.0)
        led.record_scene_clock(run_id, turn, at_eff, ch.get("lasts_minutes"), per_beat)
        if gap > 0:
            led.declare_time(run_id, turn, gap, "derived")
            affect = decay(affect, temp, profile, elapsed=gap, targets=targets)
        # THE SCARS AGE ON STORY TIME, NOT ON CHAPTERS (gate bench-clock; the owner: "chapters don't matter to fade
        # mechanics"): the drivers' one step, over the reader's own time since their last beat - the gap plus what
        # the last chapter left unspent, by the arithmetic `clock.time_items` gives the folds (gate own-timelines)
        # - and below, over every beat's own minutes.
        _passage.age({pid: sheet}, _clock.own_time(led.con, run_id, pid, turn, at_eff) or 0.0, _rests)
        for b in cb:
            passage = b["text"]
            # THE SEAT
            seat_extra = []                    # what its accepted reply carried beyond its contract (gate seat-replies)
            if stub:
                obj = stub_seat(passage, cast_ids)
                rs, lands, conf = _readings.parse(obj, percepts=None, present=None, me=pid)
                missing = []
            else:
                try:
                    rs, lands, conf, missing = seat(passage, model, led, run_id, turn) if seat else appraiser.read_emotion(
                        passage, "", model, led=led, run_id=run_id, turn=turn, scene="ch%d" % ch["index"],
                        moment="", present=cast_ids, me=pid, percepts=None, extra=seat_extra)
                except (RecordError, _rungs.RungError) as exc:
                    # A REFUSED REPLY IS AN IDLE BEAT AND A DATA POINT: the seat's format failures
                    # are measured on the log, never repaired into a reading.
                    rs, lands, conf, missing, seat_extra = [], [], None, [], []
                    led.log_llm_call(run_id, turn, "seat-refused", str(exc)[:200], scene="ch%d" % ch["index"])
            # THE ENGINE, in the spec's order: the beat's minutes age the slow tiers (gate bench-clock), then the mood
            _passage.age({pid: sheet}, per_beat, _rests)
            here = {r.about for r in rs if r.about}
            rested = decay(affect, temp, profile, elapsed=per_beat, targets=targets, present=here)
            targets = _targets.bind_readings(targets, rs, me=pid)              # rules 1, 3, 4
            repeats = {ab: _targets.repeat_count(led.con, run_id, pid, ab, before_turn=turn) for ab in {t for t in targets.values()}}
            affect, impact = receive(rested, rs, profile, targets=targets, repeats=repeats, present=here)
            heights = {}
            for r in rs:
                heights[r.path] = max(heights.get(r.path, 0.0), _rungs.height_of(r.path, _rungs.index_of(r.path, r.rung)))
            durable = any(h >= _arc._DURABLE_DIM for h in heights.values())
            mints = _wound.mint(sheet, heights, targets, durable, surfaces=_surfaces(passage)[:6], text=passage[:200], turn=turn)
            # RULE 5 LAST (a path back at rest clears its bind) — it decides what CARRIES FORWARD, so
            # it runs after the mint, which needs the binds this beat made. Note the tension it
            # exposes: one reading adds at most lambda (0.15) to a path, and _AT_REST is 0.15, so a
            # single reading's aboutness rarely outlives its beat; sustained readings do.
            targets = _targets.bind_readings(targets, [], temperament=temp, affect=affect)
            res = _arc.derive_resilience(sheet, sheet["current"].get("condition", {}))
            cue = {"about": next(iter(here)) if len(here) == 1 else None, "surfaces": _surfaces(passage), "heights": heights}
            deltas = []
            for w in sheet["baseline"].get("wounds") or []:
                if not isinstance(w, dict) or not w.get("id"):
                    continue
                d = _wound.trial(w, {}, res, cue)
                if d:
                    deltas.append(WoundDelta(char_id=pid, wound_id=str(w["id"]), delta=d, kind="event", source=passage[:200]))
            about = next(iter(here)) if len(here) == 1 else ""
            tags = {"type": "mundane", "dimensions": {}, "durability": "durable" if durable else "transient"}
            if about:
                tags["subject"] = about
            led.append_turn(TurnCommit(run_id=run_id, turn=turn, actor=pid, thought="", action=passage,
                                       tags=tags, affect=dict(affect), condition=dict(sheet["current"]["condition"]),
                                       validation=dict({"ok": True, "flags": []},
                                                       **({"seat_extra": {"emotion": seat_extra}} if seat_extra else {})),
                                       events=[Event(type="mundane", payload={"text": passage[:200], "chapter": ch["index"]}, actor=pid)],
                                       readings=list(rs), lands_on=list(lands), wound_mints=mints, wound_deltas=deltas,
                                       target_binds=_targets.binds_from(dict(sheet["current"].get("targets") or {}), targets)))
            sheet["current"]["targets"] = dict(targets)
            sheet["current"]["affect"] = dict(affect)
            if mints or deltas:
                # THE FOLD WITH TIME IN IT (gate bench-clock): `wound.fold` rebuilt the scars from mints and deltas
                # alone, so a scar never faded here however many story days passed
                _passage.fold_wounds(led.con, run_id, pid, sheet)
                profile = build_profile(sheet)
            if missing:
                led.con.execute("INSERT INTO llm_calls (run_id, turn, purpose, model, tokens_in, tokens_out, scene) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (run_id, turn, "concept-gap", "missing:" + "; ".join(missing)[:200], None, None, "ch%d" % ch["index"]))
                led.con.commit()
            for m in mints:
                log("  SCAR  ch%d turn %d: %s on %s at %.2f" % (ch["index"], turn, m["concept"], m["path"], m["intensity"]))
            if levels_out is not None and turn % int(thermometer) == 0:
                lv_extra = []
                try:
                    lv = stub_level(affect) if stub else appraiser.read_level(passage, model, led=led, run_id=run_id,
                                                                                turn=turn, scene="ch%d" % ch["index"], me=pid,
                                                                                extra=lv_extra)
                except (RecordError, _rungs.RungError) as exc:
                    led.log_llm_call(run_id, turn, "thermometer-refused", str(exc)[:200], scene="ch%d" % ch["index"])
                    lv = None
                if lv is not None:
                    levels_out.write(json.dumps(dict({"turn": turn, "chapter": ch["index"], "levels": lv},
                                                     **({"extra": lv_extra} if lv_extra else {}))) + "\n")
                    for k in lv_extra:
                        carried[("thermometer", k)] = carried.get(("thermometer", k), 0) + 1
            for k in seat_extra:
                carried[("emotion", k)] = carried.get(("emotion", k), 0) + 1
            turn += 1
    if levels_out is not None:
        levels_out.close()
    if carried:                         # recorded above AND reported (gate seat-replies), one line for the run
        log("  the seats' replies carried key(s) nothing reads - %s" % "; ".join(
            "%s %s x%d" % (seat, _replies.shown([k]), n) for (seat, k), n in sorted(carried.items())))
    log("read %d beats over %d chapters -> %s" % (turn, len(chapters), run_id))
    return run_id


# ---------------------------------------------------------------------------------------------
# THE SCORE — retired 2026-09-19 (gate emotion-tier-tidy). `score(book_dir, run_id)` compared the
# engine's PRE-BEAT rung against the seat's own reading, against a rest-only baseline: both sides
# of that comparison were read off the SAME `readings` table, so a seat that read itself
# consistently would "predict" itself perfectly regardless of whether the engine's arithmetic was
# any good — self-referential, not a test of the arithmetic. `state_vs_thermometer` (below,
# `_state_vs_levels`) is the comparison that means something: an INDEPENDENT, measurement-only
# thermometer seat against the engine's carried state, which is what `emotion-arithmetic.md`
# section 5 actually reports. The old report's other fields (a scar joined to its chapter, a
# three-way verdict string) had no successor built for them; they retired with the function.
# ---------------------------------------------------------------------------------------------
# THE PATTERNS — what the text shows, per path, with counts
# ---------------------------------------------------------------------------------------------

def _state_vs_levels(led, run_id, pid, temp, levels):
    """The engine's CARRIED state against the thermometer's standing level, in height (0..1), at
    every thermometer point -> {"points", "mean_abs_error_state", "mean_abs_error_rest", "per_path"}.
    This is the figure the arithmetic stands or falls on: the sensor reports what AROSE, the
    thermometer reads what is CARRIED, and the state is the engine's prediction of the latter.
    Rest is the baseline a prediction has to beat."""
    states = {int(r["turn"]): json.loads(r["affect"]) for r in led.con.execute(
        "SELECT turn, affect FROM current_state WHERE run_id = ? AND char_id = ?", (run_id, pid))}
    err_s, err_r, per = [], [], {}
    for lv in levels:
        a = states.get(int(lv["turn"]))
        if not a:
            continue
        for path, rung in (lv.get("levels") or {}).items():
            k = _rungs.index_of(path, rung)
            y = _rungs.height_of(path, k)
            rest_h = float(temp[path]["mean"])
            err_s.append(abs(float(a[path]) - y))
            err_r.append(abs(rest_h - y))
            row = per.setdefault(path, {"bias": [], "state": [], "level": [], "lowest": 0, "n": 0})
            row["bias"].append(float(a[path]) - y)
            row["state"].append(float(a[path]))
            row["level"].append(y)
            row["lowest"] += 1 if k == 1 else 0
            row["n"] += 1
    per_path = {p: {"n": r["n"], "bias_median": round(_median(r["bias"]), 3), "state_median": round(_median(r["state"]), 3),
                    "level_median": round(_median(r["level"]), 3), "lowest_rung_rate": round(r["lowest"] / float(r["n"] or 1), 3)}
                for p, r in sorted(per.items())}
    return {"points": len(levels), "compared": len(err_s),
            "mean_abs_error_state": round(sum(err_s) / len(err_s), 3) if err_s else None,
            "mean_abs_error_rest": round(sum(err_r) / len(err_r), 3) if err_r else None,
            "per_path": per_path}


def _turn_minutes(led, run_id, n_turns):
    """turn -> story minutes, from the scene_clock rows (one per chapter) and the beats per chapter."""
    rows = led.con.execute("SELECT turn, at_minutes AS at, beat_minutes FROM scene_clock WHERE run_id = ? ORDER BY turn", (run_id,)).fetchall()
    out = {}
    for i, r in enumerate(rows):
        start = int(r["turn"])
        end = int(rows[i + 1]["turn"]) if i + 1 < len(rows) else n_turns
        for t in range(start, end):
            out[t] = float(r["at"]) + (t - start) * float(r["beat_minutes"] or 0.0)
    return out


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def patterns(book_dir, run_id, elevated_from=0.34, peak_from=0.67):
    """A finished run -> the patterns report. Every figure carries its count (`n`), so a thin
    pattern reads as thin. Rungs are compared by HEIGHT (a rung's band midpoint, 0..1) so paths
    with different ladder lengths compare; `elevated` is a reading above `elevated_from` of the
    ladder, `peak` above `peak_from`."""
    text, chapters, sheet, cast = load_book(book_dir)
    pid = sheet["fixed"]["id"]
    led = Ledger(os.path.join(book_dir, "runs", "%s.db" % run_id))
    n_turns = int((led.con.execute("SELECT COUNT(*) FROM turns WHERE run_id = ?", (run_id,)).fetchone()[0]) or 0)
    minutes = _turn_minutes(led, run_id, n_turns)
    temp = sheet["baseline"]["temperament"]
    passages = {int(r["turn"]): r["action"] for r in led.con.execute("SELECT turn, action FROM turns WHERE run_id = ?", (run_id,))}
    rows = [(int(r["turn"]), r["path"], r["rung"], r["about"]) for r in led.con.execute(
        "SELECT turn, path, rung, about FROM readings WHERE run_id = ? AND actor = ? ORDER BY turn, reading_id", (run_id, pid))]
    aliases = {}
    for cid, row in (cast.get("people") or {}).items():
        aliases[cid] = [str(row.get("name", cid))] + [str(a) for a in (row.get("aliases") or [])]

    def height(path, rung):
        return _rungs.height_of(path, _rungs.index_of(path, rung))

    def on_page(about, turn):
        low = (passages.get(turn) or "").lower()
        if _concepts.looks_like_concept(about):
            return True                                   # a concept is here when the beat names it
        return any(a.lower() in low for a in aliases.get(about, [about]))

    by_path = {}
    for turn, path, rung, about in rows:
        by_path.setdefault(path, []).append((turn, height(path, rung), rung, about))
    beats_with = {t for t, _p, _r, _a in rows}
    low_only = {t for t in beats_with if all(h <= elevated_from for tt, _p, h, _a in
                                             [(r[0], r[1], height(r[1], r[2]), r[3]) for r in rows] if tt == t)}
    idle = {"beats": n_turns, "silent": n_turns - len(beats_with),
            "silent_rate": round((n_turns - len(beats_with)) / float(n_turns or 1), 3),
            "low_only_rate": round(len(low_only) / float(n_turns or 1), 3)}

    per_path = {}
    for path, seq in sorted(by_path.items()):
        rest_h = float(temp[path]["mean"])
        hist = {}
        for _t, _h, rung, _a in seq:
            hist[rung] = hist.get(rung, 0) + 1
        # PERSISTENCE after a peak: beats (and story minutes) until the path's readings are back
        # within one rung-height of rest, or the path falls silent for 3 beats
        runs, spans = [], []
        turns_of = {}
        for t, h, _r, _a in seq:
            turns_of.setdefault(t, []).append(h)
        peaks = [t for t, hs in turns_of.items() if max(hs) >= peak_from]
        for pt in peaks:
            last = pt
            for t in range(pt + 1, n_turns):
                hs = turns_of.get(t)
                if hs is None:
                    if t - last >= 3:
                        break
                    continue
                if max(hs) <= rest_h + 0.1:
                    break
                last = t
            runs.append(last - pt)
            if pt in minutes and last in minutes:
                spans.append(minutes[last] - minutes[pt])
        # BUILD: the longest run of consecutive elevated beats on this path
        streak, best = 0, 0
        for t in range(n_turns):
            hs = turns_of.get(t)
            if hs and max(hs) > elevated_from:
                streak += 1
                best = max(best, streak)
            else:
                streak = 0
        # REPETITION: consecutive readings about the same thing on this path -> the height delta,
        # split (people) by presence on the page
        rep_present, rep_absent, rep_concept = [], [], []
        prev = None
        for t, h, _r, a in seq:
            if prev and a and prev[3] == a and t - prev[0] <= 2:
                d = h - prev[1]
                if _concepts.looks_like_concept(a):
                    rep_concept.append(d)
                elif on_page(a, t):
                    rep_present.append(d)
                else:
                    rep_absent.append(d)
            prev = (t, h, _r, a)
        per_path[path] = {
            "readings": len(seq), "rungs": hist, "rest_height": round(rest_h, 3),
            "peaks": len(peaks),
            "persistence_beats_after_peak": {"n": len(runs), "median": _median(runs), "max": max(runs) if runs else None},
            "persistence_minutes_after_peak": {"n": len(spans), "median": _median(spans)},
            "longest_elevated_streak_beats": best,
            "repetition_delta": {"person_present": {"n": len(rep_present), "median": _median(rep_present)},
                                  "person_absent": {"n": len(rep_absent), "median": _median(rep_absent)},
                                  "concept": {"n": len(rep_concept), "median": _median(rep_concept)}},
        }
    # SCARS: a concept read at a peak once; later readings about it, against never-peaked concepts
    first_peak, later, unpeaked = {}, {}, []
    for turn, path, rung, about in rows:
        if not _concepts.looks_like_concept(about):
            continue
        h = height(path, rung)
        key = (about, path)
        if key in first_peak and turn > first_peak[key]:
            later.setdefault(key, []).append((turn, h))
        elif h >= peak_from and key not in first_peak:
            first_peak[key] = turn
    for turn, path, rung, about in rows:
        if _concepts.looks_like_concept(about) and (about, path) not in first_peak:
            unpeaked.append(height(path, rung))
    scars = []
    for key, tl in later.items():
        hs = [h for _t, h in tl]
        span = (minutes.get(tl[-1][0], 0) - minutes.get(first_peak[key], 0)) if tl else 0
        scars.append({"concept": key[0], "path": key[1], "peak_turn": first_peak[key], "re_encounters": len(hs),
                      "median_height_after": round(_median(hs), 3), "elevated_after_rate": round(sum(1 for h in hs if h > elevated_from) / float(len(hs)), 3),
                      "story_minutes_spanned": round(span, 1)})
    # THE BASIS: which paths fire together in one beat
    pairs = {}
    for t in beats_with:
        ps = sorted({p for tt, p, _r, _a in rows if tt == t})
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                pairs[ps[i] + "+" + ps[j]] = pairs.get(ps[i] + "+" + ps[j], 0) + 1
    # THE THERMOMETER: level over story time after each peak -> a half-life estimate per path
    levels = []
    lp = os.path.join(book_dir, "runs", "%s.levels.jsonl" % run_id)
    if os.path.isfile(lp):
        for line in io.open(lp, encoding="utf-8"):
            try:
                levels.append(json.loads(line))
            except ValueError:
                continue
    half_lives = {}
    for path in by_path:
        rest_h = float(temp[path]["mean"])
        series = [(int(lv["turn"]), height(path, lv["levels"][path])) for lv in levels if path in lv.get("levels", {})]
        ests = []
        for i, (t0, h0) in enumerate(series):
            exc = h0 - rest_h
            if exc < 0.2:
                continue
            for t1, h1 in series[i + 1:]:
                if h1 - rest_h <= exc / 2.0:
                    if t0 in minutes and t1 in minutes and minutes[t1] > minutes[t0]:
                        ests.append(minutes[t1] - minutes[t0])
                    break
        half_lives[path] = {"n": len(ests), "median_minutes": _median(ests)}
    gaps = {}
    for r in led.con.execute("SELECT model FROM llm_calls WHERE run_id = ? AND purpose = 'concept-gap'", (run_id,)):
        for name in r["model"][len("missing:"):].split("; "):
            if name:
                gaps[name] = gaps.get(name, 0) + 1
    return {"run": run_id, "beats": n_turns, "idle": idle, "per_path": per_path, "scars": scars,
            "co_fire": sorted(pairs.items(), key=lambda kv: -kv[1])[:12],
            "half_life_from_thermometer": half_lives, "thermometer_points": len(levels),
            "state_vs_thermometer": _state_vs_levels(led, run_id, pid, temp, levels),
            "concept_gaps": sorted(gaps.items(), key=lambda kv: -kv[1])}


def main(argv=None):
    ap = argparse.ArgumentParser(description="read a novel through the appraiser seat and the engine")
    ap.add_argument("--book", required=True, help="slug under $SWE_BOOKS/readalong/, or a path")
    ap.add_argument("--stub", action="store_true", help="the deterministic seat double; no model")
    ap.add_argument("--model", default=None, help="OpenRouter model id for the seat (default: provider.seat_model())")
    ap.add_argument("--beat-words", type=int, default=300)
    ap.add_argument("--limit", type=int, default=None, help="read only the first N beats")
    ap.add_argument("--patterns", default=None, help="the patterns report for this run id")
    ap.add_argument("--thermometer", type=int, default=0, help="ask the standing level every N beats (0 = never)")
    ap.add_argument("--emit", default=None, help="write every seat prompt to this directory (beside the book) and stop")
    ap.add_argument("--replies", default=None, help="replay the answers written for the emitted prompts in this directory")
    a = ap.parse_args(argv)
    book_dir = a.book if os.path.isdir(a.book) else os.path.join(books_root(), a.book)
    if a.emit:
        print(json.dumps(emit(book_dir, a.emit, beat_words=a.beat_words, limit=a.limit, thermometer=a.thermometer, model=a.model), indent=2))
        return 0
    if a.patterns:
        print(json.dumps(patterns(book_dir, a.patterns), indent=2))
        return 0
    run_id = run(book_dir, stub=a.stub, model=a.model, beat_words=a.beat_words, limit=a.limit, thermometer=a.thermometer, replies=a.replies)
    print(json.dumps(patterns(book_dir, run_id), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
