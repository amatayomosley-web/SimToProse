"""targets.py — what each feeling is ABOUT.

Split out of `state.py` (2026-08-22) on the same seam the field split uses: MAGNITUDE and TARGET
have different lifetimes. A magnitude decays toward temperament every beat — that is `state.decay`.
A target never decays; it is replaced, or it is released when the feeling behind it subsides. Two
lifetimes, two modules, the way this project separates fixed / baseline / current everywhere else.

`docs/emotion-basis.md` is normative: "Per-primary targets move the target from the event onto the
state, and `_regard` becomes a per-primitive evaluation." The per-primitive `_regard` stayed in
`state.py` because it is part of the appraisal arithmetic; the BINDING lives here.

Pure, deterministic, stdlib. The registry it consults (`records.DIRECTEDNESS`) is upstream of both.
"""
import json

from . import window as _window        # which of a character's rows count (gate flashback-windows)

from .records import admits_role, RecordError
from .state import _AT_REST, _DIM_TO_PATH


def retarget(targets, tags, temperament=None, affect=None, me=None):
    """What each primitive is ABOUT after this event. Pure; returns a NEW map.

    `emotion-basis.md` moves the target off the event and onto the state, which is what lets a
    character fear the wolf and rage at the man who let it in: one event cannot supply two subjects,
    so per-primitive aboutness has to ACCUMULATE ACROSS BEATS or it cannot exist at all.

    Five rules, each with a reason:

      1. A POSITIVE push binds the event's subject as that primitive's object. The event was about
         S, so the fear it raised is fear OF S.
      2. A NEGATIVE push never binds. A target on a suppression is meaningless — PLAY collapsing
         under threat does not thereby point at the threat.
      3. REFLEXIVITY IS DERIVED. Subject == the character -> a reflexive bind, but only where
         `records.DIRECTEDNESS` admits one. Where it does not, THE MAGNITUDE STILL APPLIES AND THE
         BIND IS DROPPED. That is not a fallback, it is the behaviour: a self-authored social
         violation yields DISGUST(self) plus RAGE-unbound — shame, and irritability at the room,
         which is how humiliated people act.
      4. A positive push with NO subject leaves any existing bind untouched. Nothing new was learned
         about what the feeling is about.
      5. A primitive that has DECAYED BACK TO REST clears its bind. Aboutness with no feeling behind
         it is stale, and it would otherwise re-attach to a later unrelated spike.

    One target per primitive means simultaneous rage at two parties is inexpressible. That is the
    basis shape's own trade, accepted when it chose one slot; recency wins. LEAVE ALONE unless
    renders show targets ping-ponging or stale aboutness — this is deliberately not arbitrated.
    """
    if not isinstance(tags, dict):
        raise RecordError("TAG_TAGS_NOT_AN_OBJECT", "retarget: tags must be a dict, got %r" % type(tags).__name__)
    out = dict(targets) if isinstance(targets, dict) else {}

    dimensions = tags.get("dimensions") or {}
    if not isinstance(dimensions, dict):
        raise RecordError("TAG_DIMENSIONS_TYPE", "retarget: tags['dimensions'] must be a dict")
    subject = tags.get("target")

    if subject:
        reflexive = me is not None and str(subject).lower() == str(me).lower()
        for dim, mag in dimensions.items():
            try:
                if float(mag) <= 0.0:
                    continue
            except (TypeError, ValueError):
                continue
            for primary, base_push in _DIM_TO_PATH.get(dim, []):
                if base_push <= 0.0:
                    continue                                   # rule 2: suppressions do not bind
                if reflexive and not admits_role(primary, "self"):
                    out.pop(primary, None)                     # rule 3: magnitude keeps, bind drops
                    continue
                out[primary] = str(subject)                    # rule 1

    # rule 5 — a primitive back at rest is no longer about anything
    if isinstance(temperament, dict) and isinstance(affect, dict):
        for primary in list(out):
            v = affect.get(primary)
            mean = (temperament.get(primary) or {}).get("mean")
            if isinstance(v, (int, float)) and isinstance(mean, (int, float)):
                if abs(float(v) - float(mean)) <= _AT_REST:
                    out.pop(primary, None)
    return out


# ---------------------------------------------------------------------------------------------
# PERSISTENCE. Everything above is pure and takes maps; everything below is where those maps come
# from and go. Aboutness was the ONE accumulating tier with no log — `retarget` ran every beat and
# both drivers wrote its answer onto `char["current"]["targets"]` in memory, so it died at process
# exit. Measured 2026-09-06: neither driver's rehydrate block replayed targets while all five of
# its siblings did (arc, vault, edges, toward, wounds), and `current.targets` was `{}` for 18 of 18
# characters across four books. A man enraged at Cobb all scene resumed enraged at nobody.
#
# THE FOLD IS LAST-WRITE-WINS, NOT A SUM, which is why this is not shaped like `toward.replay`.
# Those deltas are signed and accumulate; a target is REPLACED (see this module's header). Summing
# would be a category error, so `replay` assigns in turn order.
#
# The module owns its own SQL, the way `claims.py` does and for the same stated reason — one writer
# knows the table. `ledger.py` was at 497 lines against the >=500 bound `tests/test_map.py:136`
# ratchets, so a `Ledger.target_binds_for` twin of `toward_deltas_for` would not fit; callers reach
# `binds_for(led.con, ...)` directly, as `scripts/direct.py` already does for
# `decay.fold_recall_history(led.con, ...)`.

def bind_readings(targets, readings, temperament=None, affect=None, me=None):
    """What each path is ABOUT after this beat's READINGS. Pure; returns a NEW map. Phase 3's
    successor to `retarget` (docs/emotion-arithmetic.md section 5 step 3):

      * a reading with an `about` binds path -> about                    (rule 1's successor)
      * a reading with no `about` leaves the existing bind untouched      (rule 4)
      * a path back at rest clears its bind                               (rule 5)
      * a reflexive about (== me) binds only where DIRECTEDNESS admits `self`; where it does not,
        the reading's magnitude still applied and the bind is dropped     (rule 3)
    """
    out = dict(targets) if isinstance(targets, dict) else {}
    me_norm = str(me or "").strip().lower()
    for r in (readings or []):
        about = str(getattr(r, "about", "") or "").strip()
        if not about:
            continue                                            # rule 4
        if me_norm and about.lower() == me_norm and not admits_role(r.path, "self"):
            out.pop(r.path, None)                               # rule 3
            continue
        out[r.path] = about                                     # rule 1
    if isinstance(temperament, dict) and isinstance(affect, dict):
        for path in list(out):                                  # rule 5
            v = affect.get(path)
            mean = (temperament.get(path) or {}).get("mean")
            if isinstance(v, (int, float)) and isinstance(mean, (int, float)):
                if abs(float(v) - float(mean)) <= _AT_REST:
                    out.pop(path, None)
    return out


RELEASED = ""     # a bind that was DROPPED. Not None: it is written to a NOT NULL column, on purpose.


def binds_from(before, after):
    """Two targets maps -> the [(primary, target)] rows that turn the first into the second. Pure.

    A RELEASE IS A ROW. `retarget` rule 3 drops a bind the DIRECTEDNESS registry does not admit, and
    rule 5 clears one whose feeling has decayed back to rest. Logging only the positive binds would
    leave un-binding underivable, and a replay would then diverge from the live run it is meant to
    reproduce — the character would carry an aboutness the beat had already released. So a dropped
    primitive emits `RELEASED` and the fold deletes on it.

    Emits nothing for a primitive that did not move, which is most of them on most beats.
    """
    before = before if isinstance(before, dict) else {}
    after = after if isinstance(after, dict) else {}
    rows = []
    for primary in sorted(set(before) | set(after)):
        was, now = before.get(primary), after.get(primary)
        if was != now:
            rows.append((primary, str(now) if now else RELEASED))
    return rows


def write_binds(con, run_id, turn, char_id, binds):
    """Log one turn's aboutness changes -> the number of rows written.

    NO TRANSACTION OF ITS OWN, and that is deliberate: this is called from inside
    `Ledger.append_turn`'s `with self.con:` block. `ledger.py:154-159` records what it costs when a
    write lands after the turn instead of with it — a crash between the two leaves the turn
    permanently committed with the write lost, and `turns`' PRIMARY KEY refuses the re-append, so
    replaying the beat cannot recover it. Opening `with con:` here would COMMIT that transaction
    early, which is the same reason `claims.write` exists beside `claims.record`.
    """
    n = 0
    for primary, target in (binds or []):
        con.execute("INSERT INTO target_binds (run_id, turn, char_id, primary_, target) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (run_id, int(turn), str(char_id), str(primary), str(target or RELEASED)))
        n += 1
    return n


def binds_for(con, run_id, char_id, before_turn=None, view=None):
    """Every aboutness change this character made, in turn order -> [(primary, target)].

    Ordered by (turn, bind_id) because the fold is LAST-WRITE-WINS: unlike the summing folds beside
    it, order here changes the answer, so the read cannot be unordered and the ordering is not a
    readability nicety. `bind_id` breaks the tie within a turn, which the UNIQUE constraint makes
    impossible for one primitive but not across two.
    """
    # `before_turn`: only the binds committed before that turn - what a resume there read (gate
    # mood-from-readings, 2026-09-22). None is the whole log, as before. `view`: gate flashback-windows.
    bound = ("" if before_turn is None else " AND turn < %d" % int(before_turn)) + _window.clause(
        _window.of(con, run_id, char_id, view))
    return [(r["primary_"], r["target"]) for r in con.execute(
        "SELECT primary_, target FROM target_binds WHERE run_id = ? AND char_id = ?" + bound +
        " ORDER BY turn, bind_id", (run_id, char_id))]


def repeat_count(con, run_id, char_id, about, before_turn=None, view=None):
    """How many CONSECUTIVE most-recent committed turns of this character were about `about`.

    The repetition term's input (`connection.repetition`), READ FROM THE LOG rather than kept in a
    counter: `turns.tags` already carries the subject of every committed beat, so the count is
    derivable and a second store would duplicate it (the seven-duplicates table in CLAUDE.md).
    Walks the actor's turns newest-first and stops at the first beat about something else or
    about nothing. 0 when the log holds none. Pure over the log; deterministic on replay.
    """
    if not about:
        return 0
    q = "SELECT tags FROM turns WHERE run_id = ? AND actor = ?"
    args = [run_id, str(char_id)]
    if before_turn is not None:
        q += " AND turn < ?"
        args.append(int(before_turn))
    q += _window.clause(_window.of(con, run_id, char_id, view)) + " ORDER BY turn DESC"   # gate flashback-windows
    n = 0
    want = str(about)
    for row in con.execute(q, args):
        try:
            tags = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
        except ValueError:
            break
        subj = (tags or {}).get("subject") or (tags or {}).get("target")
        if str(subj or "") != want:
            break
        n += 1
    return n


def replay(char, binds):
    """Fold logged binds onto a character. Mutates `char["current"]["targets"]`, returns it.

    ONE FUNCTION, called from every resume path — `bonds.py` records what it costs when a replay is
    hand-copied into each driver instead, and `toward.replay` and `levers.replay_wound_deltas`
    follow the same rule.

    STAMPS `_authored_targets` BEFORE APPLYING ANYTHING, as `toward.replay` stamps `_authored_toward`
    and for the same reason: an author may write a starting aboutness, and law 1 of
    docs/character-model.md is that the base survives. Stamp after and the base is gone.

    ASSIGNS, NEVER SUMS. The four sibling folds accumulate signed deltas and are order-independent;
    this one is order-DEPENDENT by construction, because the last thing a beat said a feeling was
    about is what it is about. `binds_for` supplies the order.

    binds: [(primary, target)] in log order; `RELEASED` deletes the bind.
    """
    if not isinstance(char, dict):
        raise RecordError("TAG_CHAR_NOT_A_DICT",
                          "targets.replay: char must be a dict, got %r" % type(char).__name__)
    cur = char.setdefault("current", {})
    base = cur.setdefault("targets", {})
    cur.setdefault("_authored_targets", dict(base))
    for primary, target in (binds or []):
        if target:
            base[primary] = target
        else:
            base.pop(primary, None)
    return base
