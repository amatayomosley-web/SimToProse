"""injuries.py — bodily injuries as dated STATE that heals over story time (the `injuries` system).

WHY THIS EXISTS (gate injuries, 2026-09-22). No act could leave anyone hurt: the event seat was never asked about
harm, a sheet's `current.condition.injuries` was read by no code, and no actor was told that they, or anyone they
saw, was hurt. The owner ruled (D5): "Track injuries as state similar to props but for now I'm not interested in
health bars" - and then "Heal over time", after being told that healing on a clock needs a severity per injury.

WHAT IT IS - the props precedent (`scene_facts`), for bodies:
  * the EVENT READER marks harm done to a body in a beat - who, the words of the act that show it, and one
    SEVERITY word from a closed ladder - asked only when the book runs `injuries` (`RUBRIC`, `parse_seat`);
  * each marking rides the committed event (`events.payload["injuries"]`) and is folded ON DEMAND, like
    `scene_facts.run_rows`: no new table, nothing to migrate, a `correction` supersedes it the same way;
  * each HEALS OVER STORY TIME, read off the one clock (`clock.at_turn`): `fresh` for the first part of its
    healing, then `healing`, then gone - except a grave one, which leaves a lasting MARK;
  * a sheet's `current.condition.injuries` are the ones a character carries where their own story begins - the
    opening of their first scene (`clock.first_presence`; page one until gate own-timelines) - `ago` before it; with
    no `ago`, long healed.

WHO IS TOLD: the one hurt, the one who acted, and whoever was PRESENT at that beat (`scene_facts.witnessed`, the
same recorded presence). A sheet's injuries: that character alone.

NO BAR, NO NUMBER: a severity is a word, a stage is a word; nothing here reaches a prompt but words and the
reader's own quote. ONE MECHANICAL EFFECT (gate injury-weakens, the owner's ruling D6): in a book that also runs
`body`, an injury still fresh or healing makes the body count strength words lower (`WEAKENS`, `weakening`, read by
`body.capacity`), so effort and waking time cost it more until it heals. Deterministic, stdlib only, no LLM (hard
rules 3, 4).
"""
from __future__ import annotations

from . import clock as _clock
from . import scene_facts as _scene_facts
from .records import RecordError

# word -> (days to heal, leaves a lasting mark?, the reader's line). START values from the ordinary course of
# such hurts, each with a falsifier: minor 3 days (FALSIFIER: a scraped knee still reading fresh a week on);
# serious 3 weeks (FALSIFIER: a deep cut reading healed after a few days); grave 3 months, then a mark for good
# (FALSIFIER: a broken arm reading healed within a fortnight).
# THE READER'S LINES WERE PROBED before they shipped (2026-09-22): two raters, same model family, same prompt, on
# public-domain novel passages chosen by a fixed rule - 39 of 39 alike and 18 of 18 alike (count and word). Each
# round both raised the same doubts, and the wording now carries the fixes both reached (the old wound still
# bleeding, the fight that only implies, the bare blow, one entry per harm, the head blow, the unstated depth).
# The probe saw no `serious` or `grave` harm, so where those rungs divide is still untested.
SEVERITY = {
    "minor":   (3.0, False, "a bruise, a scrape, a shallow cut, a bloody nose, a jarred or wrenched finger: it "
                            "smarts, and the body works as before"),
    "serious": (21.0, False, "a deep cut, a cracked rib, a sprained joint, a blistering burn, a blow the words put "
                             "on the head that stuns or fells: the body is hampered for a while"),
    "grave":   (90.0, True, "a broken bone, a stab, a bullet in the flesh, a lost finger or eye, a wound that will "
                            "not stop bleeding: the body will not work as it did, and may never fully"),
}
# The share of its healing an injury reads `fresh` [START; FALSIFIER: a cut from yesterday morning reading as
# healing by the evening].
FRESH_SHARE = 1.0 / 3.0
FRESH, HEALING, MARK = "fresh", "healing", "mark"
# How far a hurt that has not healed weakens the body (gate injury-weakens; the owner's ruling D6): strength words
# down while fresh or healing. A minor one does nothing; a healed one - a grave one's mark too - nothing.
WEAKENS = {"minor": 0, "serious": 1, "grave": 2}
MAX_PER_BEAT = 3
_SELF = "self"

RUBRIC = """

INJURIES. This book also tracks bodily INJURY: harm done to someone's body in this beat - a blow that bruises,
a cut, a burn, a break. Add to the JSON:

 "injuries": [{"who": "<the one hurt: an id from PRESENT, or self for the one named under WHO ACTED>", "quote": "<the words of the action that show the harm, copied exactly>", "severity": "<one word from the ladder below>"}]

Most beats have NONE: leave the list empty. Only harm the words show happening to a particular body in this
beat, now - not a threat or a near miss, not hurts a fight only implies, not a hurt remembered, recounted or
feared, not a wound from before this beat even if it still aches, bleeds or is bandaged in it, not tiredness (the
engine weighs effort on its own), and not a wound to pride or feeling. A blow the words show landing on someone
counts, minor unless the words show more ("a fight only implies" means no blow is shown landing on anyone). Each
blow that lands and each wound is its own entry: a blow that knocks someone down and the cut they take in falling
are two. Rate the harm itself, not who suffered it or how bravely: the same cut is the same word on anyone. At
most three.

severity - from least to most:
%s

When the words do not say which rung fits, go by the clause after its colon, and take the lower rung unless the
words show that effect.
"""


def rubric():
    """The reader's ladder, one line per word, least first - DERIVED from the table the engine heals by."""
    return "\n".join("  %-8s - %s" % (w, SEVERITY[w][2]) for w in SEVERITY)


def _severity(word):
    w = str(word or "").strip().lower()
    if w not in SEVERITY:
        raise RecordError("INJURY_SEVERITY_UNKNOWN", "injury severity %r is not one of %s" % (word, ", ".join(SEVERITY)))
    return w


def stage(severity, minutes):
    """How an injury reads `minutes` of story time after it was taken -> fresh | healing | mark | None (gone)."""
    days, lasting, _line = SEVERITY[_severity(severity)]
    elapsed = max(0.0, float(minutes)) / _clock.MINUTES_PER_DAY
    if elapsed < days * FRESH_SHARE:
        return FRESH
    if elapsed < days:
        return HEALING
    return MARK if lasting else None


def require(char):
    """Refuse, before the first beat, a sheet whose injuries the system cannot read -> the char.

    `current.condition.injuries`: a list (empty is the usual answer) of {what, severity, ago?} - `what` in the
    author's words, `severity` one of the ladder's, `ago` an optional span before their first scene ("12h", "5d")."""
    cond = ((char or {}).get("current") or {}).get("condition") or {}
    rows = cond.get("injuries", [])
    if not isinstance(rows, list):
        raise RecordError("INJURY_SHAPE", "current.condition.injuries must be a list, got %s" % type(rows).__name__)
    for r in rows:
        if not isinstance(r, dict) or not str(r.get("what") or "").strip() or set(r) - {"what", "severity", "ago"}:
            raise RecordError("INJURY_SHAPE", "an injury on a sheet is {what, severity, ago?}, got %r" % (r,))
        _severity(r.get("severity"))
        if r.get("ago") is not None:
            try:
                _clock.span_minutes(r["ago"])
            except RecordError as e:
                raise RecordError("INJURY_AGO_NOT_A_SPAN", "an injury's `ago` %r is not a span (%s)" % (r["ago"], e))
    return char


def parse_seat(raw, action, present, actor, norm):
    """The event seat's `injuries` -> [{who, quote, severity}], each checked; `norm` is the seat's own span
    normaliser, so a quote is found in the act exactly as `showed` quotes are."""
    raw = raw or []
    if not isinstance(raw, list) or len(raw) > MAX_PER_BEAT or not all(isinstance(r, dict) for r in raw):
        raise RecordError("APPRAISER_INJURY_SHAPE", "the event seat's injuries %r is not a list of at most %d "
                          "{who, quote, severity}" % (raw, MAX_PER_BEAT))
    allowed = {str(p).strip().lower() for p in (present or [])} | {_SELF}
    out = []
    for r in raw:
        who = str(r.get("who") or "").strip()
        if who.lower() == str(actor or "").strip().lower() and who:
            who = _SELF
        if who.lower() not in allowed:
            raise RecordError("APPRAISER_INJURY_SHAPE", "the event seat named %r as hurt, who is neither present nor "
                              "the one who acted" % (r.get("who"),))
        span = str(r.get("quote") or "").strip()
        if not span:
            raise RecordError("APPRAISER_QUOTE_MISSING", "the event seat named an injury to %r with no quote" % who)
        if action is not None and norm(span) not in norm(action):
            raise RecordError("APPRAISER_FACT_NOT_IN_ACTION",
                              "the event seat quoted %r for an injury, and the action does not contain it" % span)
        severity = str(r.get("severity") or "").strip().lower()
        if severity not in SEVERITY:
            raise RecordError("APPRAISER_INJURY_UNKNOWN", "the event seat's injury severity %r is not one of %s"
                              % (r.get("severity"), ", ".join(SEVERITY)))
        out.append({"who": who if who == _SELF else who.lower(), "quote": span, "severity": severity})
    return out


def run_rows(con, run_id, before_turn=None):
    """Every injury marked in a run, in log order, minus superseded events -> [{turn, speaker, who, what, severity}]."""
    speakers = {int(t): a for t, a in con.execute("SELECT turn, actor FROM turns WHERE run_id=?", (run_id,))}
    rows = []
    for turn, p in _scene_facts.payloads(con, run_id, before_turn):
        speaker = speakers.get(int(turn))
        for r in p.get("injuries") or []:
            if isinstance(r, dict) and str(r.get("quote") or "").strip():
                who = str(r.get("who") or "").strip().lower()
                rows.append({"turn": int(turn), "speaker": speaker, "who": speaker if who == _SELF else who,
                             "what": str(r["quote"]).strip(), "severity": _severity(r.get("severity"))})
    return rows


def weakening(con, run_id, char_id, char, before_turn):
    """How many strength words lower the body counts at the beat `before_turn` -> 0, 1 or 2: the worst of the
    character's OWN injuries still fresh or healing - the log's and the sheet's - never a sum (`body.capacity`)."""
    return max([WEAKENS[r["severity"]] for r in for_actor(con, run_id, char_id, char, before_turn)
                if r["who"] == char_id and r["stage"] in (FRESH, HEALING)] or [0])


def for_actor(con, run_id, actor, char, before_turn):
    """What `actor` knows of injuries still showing at the beat `before_turn` -> [{who, what, severity, stage}].

    The injuries of beats they witnessed (`scene_facts.witnessed`), aged from the beat they were taken; then
    their own sheet's, aged from their first scene less `ago`. Healed ones are gone; a grave one stays as its mark. Most
    recent first; the sheet's last."""
    now = _clock.at_turn(con, run_id, before_turn)
    present = _scene_facts.present_by_turn(con, run_id)
    out = []
    for r in reversed(run_rows(con, run_id, before_turn)):
        if not _scene_facts.witnessed(r, actor, present) and r["who"] != actor:
            continue
        then = _clock.at_turn(con, run_id, r["turn"])
        s = stage(r["severity"], (now - then) if (now is not None and then is not None) else 0.0)
        if s:
            out.append({"who": r["who"], "what": r["what"], "severity": r["severity"], "stage": s})
    start = _clock.first_presence(con, run_id, actor)          # where their story began (gate own-timelines)
    start = now if start is None else start                     # ...or begins, with this very beat
    for r in ((((char or {}).get("current") or {}).get("condition") or {}).get("injuries") or []):
        if r.get("ago") is None:
            s = stage(r["severity"], float("inf"))
        else:
            since = (now - start) if (now is not None and start is not None) else 0.0
            s = stage(r["severity"], since + _clock.span_minutes(r["ago"]))
        if s:
            out.append({"who": actor, "what": str(r["what"]).strip(), "severity": _severity(r["severity"]), "stage": s})
    return out
