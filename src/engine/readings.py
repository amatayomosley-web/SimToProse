"""readings.py — what the appraiser saw, stored so the state stays derivable.

`docs/emotion-arithmetic.md` §1 and §5 step 8. A READING is one path moving in one beat, for one
character, about one party:

    {"path": "DISPLEASURE", "rung": "anger", "about": "anouk"}

and a beat's set of them carries two more facts that are not readings: `lands_on` (which present
characters the beat bears on, for `floor.urge` in Phase 5) and `confidence` (a WORD, which gates
escalation to the recorder and never enters arithmetic).

WHY THIS IS A TABLE AND NOT A FIELD. §5 step 8 is explicit: *"Without it `f` and `R` are not
re-derivable and hard rule 2 is false for emotion."* The affect vector on a committed turn is a
SNAPSHOT; the readings are the CAUSE. Keep only the snapshot and a replay from zero cannot reach the
same numbers, which is the exact defect schema v23 fixed for aboutness and v12 fixed for elapsed
time — both discovered the same way, by asking what a resume could not reconstruct.

THE RUNG IS STORED BY NAME. §1: *"No number leaves the appraiser"* — hard rule 5's inbound twin. A
name also survives a re-band, where an index does not; `gate.py:249` records what positional
references already cost this repo once.

Deterministic, stdlib only, no LLM (CLAUDE.md hard rule 3). The seat that PRODUCES readings is an
LLM and lives outside the engine; what is here is the record and a test double.
"""
from __future__ import annotations

import json

from . import concepts as _concepts
from . import rungs
from .records import PATHS, Reading, RecordError

# A reading with no party is not an error — plenty of feeling is about nothing nameable, and §5
# step 3 rule 4 says an empty `about` leaves an existing bind untouched rather than clearing it.
UNBOUND = ""

# `confidence` is a word by contract (§1). The set is small and closed so a typo fails loudly
# instead of silently reading as low confidence.
CONFIDENCE_WORDS = ("sure", "likely", "unsure")


def canonical_path(name):
    """A path name as the seat wrote it -> the ladder's own name, matched WITHOUT REGARD TO CASE;
    anything else is returned untouched for `Reading.validate` to refuse by name.

    WHY (2026-09-11, the first live read-along, Red Badge on Opus): the emotion seat's contract says
    `"path": "<one of the eight>"` and the ladders are headed in capitals, and the model wrote the
    eight in lower case in 105 of 221 answers. Every one was refused as READING_RUNG_NOT_ON_PATH —
    a refusal that named the wrong defect, since the rung was verbatim and only the ladder's name
    was cased differently. A capitalization difference is not a different ladder — and the RUNG name
    was already matched without regard to case by `rungs.index_of`; the path key was the one exact
    comparison left, which is why only the path failed. An unknown name is still refused by name."""
    key = str(name or "").strip().lower()
    for p in PATHS:
        if p.lower() == key:
            return p
    return str(name or "").strip()


def parse(obj, percepts=None, present=None, me=""):
    """A parsed appraiser reply -> (readings, lands_on, confidence). THE TRUST BOUNDARY.

    `docs/emotion-arithmetic.md` section 1 defines the shape; this is the validating parser that
    stands between a model and the ledger, and it REFUSES rather than repairs. Every refusal below
    names something the seat is structurally able to get wrong, and a repaired refusal makes the
    boundary advisory -- the same rule `scripts/direct.py` `_compose_selection` follows on a
    composer refusal, for the same reason.

    WHAT IT CHECKS THAT `Reading.validate` CANNOT. `validate` resolves a rung name against the live
    ladder, which catches LEVITY, a cross-path rung (`dread` on DISPLEASURE) and a typo. It cannot
    see the SCENE -- so aboutness and `lands_on` are checked here, where the PerceptSet is in hand:

      * `about` must be someone the character actually perceived, or empty, or themselves. Section 1
        binds it to the PerceptSet, and a feeling bound to someone who was never perceived is a
        false relationship the aboutness tier will then carry for the rest of the book.
      * `lands_on` must name people who are present. It is the term section 5 step 5 gives
        `floor.urge` in place of the counterfactual `salience` call, so a name nobody can hear moves
        the wrong character to speak.
      * `confidence` must be one of `CONFIDENCE_WORDS`. That tuple has been declared and enforced
        nowhere since Phase 2 -- a constant nothing checks is a comment.

    AN EMPTY READINGS LIST IS VALID AND EXPECTED. Most beats are quiet; section 8's whole stability
    argument rests on the seat staying silent when nothing arose. Refusing an idle beat would train
    the caller to treat silence as an error.
    """
    if not isinstance(obj, dict):
        raise RecordError("READING_REPLY_NOT_AN_OBJECT",
                          "parse: the reply must be an object, got %r" % type(obj).__name__)

    conf = str(obj.get("confidence", "sure"))
    if conf not in CONFIDENCE_WORDS:
        raise RecordError("READING_CONFIDENCE_UNKNOWN",
                          "parse: confidence %r is not one of %s" % (conf, list(CONFIDENCE_WORDS)))

    rows = obj.get("readings", [])
    if not isinstance(rows, list):
        raise RecordError("READING_REPLY_NOT_AN_OBJECT",
                          "parse: readings must be a list, got %r" % type(rows).__name__)

    me_norm = str(me or "").strip().lower()
    out = []
    for row in rows:
        if not isinstance(row, dict):
            raise RecordError("READING_REPLY_NOT_AN_OBJECT",
                              "parse: each reading must be an object, got %r" % (row,))
        # `about` IS TEXT OR NOTHING (gate seat-replies). A value that is not text was stringified - "['ada']" - and
        # then refused where a PerceptSet checks it (below, unchanged), but bound as a target where none does (the
        # read-along). There it is read as unbound now, and the reply's record names it (replies.emotion_extra). A
        # falsy one was unbound before too.
        raw_about = row.get("about")
        about = raw_about.strip() if isinstance(raw_about, str) and raw_about.strip() else UNBOUND
        path = canonical_path(str(row.get("path", "")).strip())
        # A number where a rung name belongs is the seat leaking the scale it was never shown.
        rung = str(row.get("rung", "")).strip()
        if rung and any(ch.isdigit() for ch in rung):
            raise RecordError("READING_RUNG_IS_NUMERIC",
                              "parse: %r is a number, not a rung name; no number leaves the "
                              "appraiser (section 1)" % rung)
        r = Reading(path=path, rung=rung, about=about, confidence=conf)
        r.validate()                       # the ladder is the authority; raises on path or rung
        # A CONCEPT (gate three, 2026-09-11): `concept:<id>` from the closed registry. Validated by
        # identity, never against the PerceptSet — sickness is not a thing one perceives, it is a
        # thing the seat recognised. An unknown id is the seat inventing a category: refused.
        if _concepts.looks_like_concept(about):
            if not _concepts.is_concept(about):
                raise RecordError("READING_CONCEPT_UNKNOWN",
                                  "parse: a reading is about %r, which is not in the concept registry "
                                  "(src/engine/concepts.py). The list is closed; leave the reading "
                                  "unbound rather than name a category the engine has no name for." % about)
        elif raw_about and not isinstance(raw_about, str) and percepts is not None:
            # refused where it always was: its stringified form named no one perceived - bar the accidents, which
            # bound targets like "7": a string form found inside a percept's text (7 in a fidelity 0.7, True in a
            # flag) or equal to the character's own id. Those are refused now too.
            raise RecordError("READING_ABOUT_NOT_PERCEIVED",
                              "parse: a reading is about %r, which names no one in the PerceptSet. Section 1 "
                              "binds `about` to what the character perceived." % (raw_about,))
        elif about and about.lower() != me_norm and percepts is not None:
            if not _perceived(about, percepts):
                raise RecordError("READING_ABOUT_NOT_PERCEIVED",
                                  "parse: a reading is about %r, who is not in the PerceptSet. "
                                  "Section 1 binds `about` to what the character perceived." % about)
        out.append(r)

    lands = obj.get("lands_on", []) or []
    if not isinstance(lands, list):
        raise RecordError("READING_LANDS_ON_TYPE",
                          "parse: lands_on must be a list, got %r" % type(lands).__name__)
    # NAMES ONLY (gate seat-replies). An entry that is not text - null, a list, a number - was stringified: where a
    # present list checks the names (the scene, the read-along) that refused the reply - bar a string form equal to
    # a present id, "None" for a character with that id - and still does, before the floor can read a list emptied
    # of it as "reached no one"; where none does (the chair) it became a row of the append-only lands_on table
    # ("None", "['ada']"). It is left out there now, and the reply's record names it (replies.emotion_extra).
    odd = [x for x in lands if not isinstance(x, str)]
    if odd and present is not None:
        raise RecordError("READING_LANDS_ON_ABSENT",
                          "parse: lands_on names %r, which are not names of anyone present. It decides who speaks "
                          "next (floor.urge), so a name that is not one moves the wrong character." % (odd,))
    lands = [x.strip() for x in lands if isinstance(x, str) and x.strip()]
    if present is not None:
        here = {str(x).strip().lower() for x in present}
        stray = sorted(x for x in lands if x.lower() not in here)
        if stray:
            raise RecordError("READING_LANDS_ON_ABSENT",
                              "parse: lands_on names %s, who are not present. It decides who speaks "
                              "next (floor.urge), so an absent name moves the wrong character."
                              % stray)
    return out, lands, conf


def _perceived(name, percepts):
    """Is `name` anywhere in the PerceptSet? Case- and substring-tolerant, like gate.py's read.

    DELIBERATELY PERMISSIVE on matching and STRICT on membership. A character perceived as "the tall
    one" and named "Anouk" in the reply should not be refused on spelling, but a name that appears
    NOWHERE in what they saw is a bind the scene cannot support.
    """
    needle = str(name).strip().lower()
    if not needle:
        return True
    for p in (percepts or []):
        blob = json.dumps(p, default=str).lower() if not isinstance(p, str) else p.lower()
        if needle in blob:
            return True
    return False


def write(con, run_id, turn, actor, readings):
    """Append this beat's readings. NO TRANSACTION OF ITS OWN — the caller's `with con:` owns it.

    Same rule as `targets.write_binds` and `claims.write`, and for the same reason: opening `with
    con:` here would COMMIT the turn's transaction early, and a crash between the turn and the
    readings would leave the turn permanently committed with its cause lost — which `turns`'
    PRIMARY KEY then refuses to let a replay re-append.
    """
    n = 0
    for r in (readings or []):
        r.validate()
        # THE LADDER'S OWN SPELLING is what the log keeps (gate record-guards). `rungs.index_of` reads a rung name
        # case- and space-blind, so "Anger" validated and was stored as written; the database's insert guard holds the
        # column to the ladder's names exactly, and it must never refuse what the record layer accepted. Every one of
        # the 21,346 readings recorded before this line already held the ladder's spelling (measured 2026-09-26).
        spelled = rungs.names_on(r.path)[rungs.index_of(r.path, r.rung) - 1]
        con.execute(
            "INSERT INTO readings (run_id, turn, actor, path, rung, about, confidence) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, int(turn), str(actor), r.path, spelled, r.about or UNBOUND, r.confidence))
        n += 1
    return n


def write_lands_on(con, run_id, turn, actor, lands):
    """Append this beat's lands_on. NO TRANSACTION OF ITS OWN — the caller's `with con:` owns it.

    `write`'s sibling, same reason: opening `with con:` here would COMMIT the turn's transaction
    early, and a crash between the turn and this write would leave the turn committed with the
    seat's judgment of who it reached lost — the same hazard `write` exists to avoid for readings.

    One row per id, in the order the seat listed them (`ord`) — `floor.next_speaker` only tests
    membership, but a row that dropped the order would make a replay of this table a set where the
    seat wrote a list. Ids are stored AS GIVEN, stripped, and are text (gate seat-replies);
    `readings.parse` (:143-166) is the trust boundary — it checked each one against the present list,
    where the caller passes one (the chair passes none), before it ever reached a TurnCommit, so this
    write does not re-validate, the way `write` above trusts `r.validate()` to have run before a
    Reading is handed to it. NOT checked there: a repeated id - it fails this table's primary key and
    rolls the beat back (found by the gate seat-replies review; its own gate).
    """
    n = 0
    for i, char_id in enumerate(lands or []):
        con.execute(
            "INSERT INTO lands_on (run_id, turn, actor, char_id, ord) VALUES (?, ?, ?, ?, ?)",
            (run_id, int(turn), str(actor), str(char_id).strip(), i))
        n += 1
    return n


def readings_for(con, run_id, actor=None):
    """Every reading in this run, in beat order -> [(turn, actor, path, rung, about, confidence)].

    Ordered by (turn, reading_id) so a replay applies them in the order they landed. Unlike the
    aboutness fold this is NOT last-write-wins: two readings on one path in one beat are two
    separate additions, and collapsing them would lose one.
    """
    if actor is None:
        rows = con.execute(
            "SELECT turn, actor, path, rung, about, confidence FROM readings "
            "WHERE run_id = ? ORDER BY turn, reading_id", (run_id,)).fetchall()
    else:
        rows = con.execute(
            "SELECT turn, actor, path, rung, about, confidence FROM readings "
            "WHERE run_id = ? AND actor = ? ORDER BY turn, reading_id",
            (run_id, str(actor))).fetchall()
    return [tuple(r) for r in rows]


def lands_on_for(con, run_id, turn):
    """This beat's lands_on, in the order the seat listed them -> [char_id, ...]; [] when none.

    Scoped by (run_id, turn) alone, with no `actor` parameter — `turn` already picks out one beat
    (turns.py's own PRIMARY KEY includes actor, but a turn number is never shared by two actors in
    this engine's own writer), the same scope `Ledger.lands_on_for` hands back untouched.
    """
    rows = con.execute(
        "SELECT char_id FROM lands_on WHERE run_id = ? AND turn = ? ORDER BY ord",
        (run_id, int(turn))).fetchall()
    return [str(r["char_id"]) for r in rows]
