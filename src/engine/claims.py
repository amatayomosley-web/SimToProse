"""claims.py — what an actor asserted about the world, and when two assertions cannot both be true.

`docs/keeper-of-truth.md` is normative for the tier model. This module is the ENGINE's half and only
that half: it DETECTS, it never resolves. Hard rule 3 puts the resolving in an agent; hard rule 4
keeps this deterministic.

TWO LEVELS, AND THE SPLIT IS THE POINT (cairn 0067, adopted from the Vela shard blueprint):

    an UTTERANCE   what was said, verbatim, by one speaker on one turn
      -> EXTRACTS  the (subject, predicate, object) facts it asserts — ONE OR MORE

One utterance carries as many facts as it carries. "We held the festival at midwinter, and my mother
led the procession" is one utterance and two facts, and an earlier draft of this module stored a
single triple per claim — it recorded one and silently dropped the other.

THE EXTRACT IS NEVER THE ANSWER. Contradiction is found by comparing extracts, and what is RETURNED
is the parent utterance. The triple is an index INTO what was said, never a substitute for it: the
extract drops "when I was a girl", and that clause may be the whole point — perhaps they no longer
do. The engine compares the fact; the keeper reads the sentence.

TIER IS DERIVED, NEVER STORED. Hard rule 2 makes the log append-only and schema v9 enforces it with
triggers, so a claim cannot have a `tier` column that flips superposed -> fiction; that is an UPDATE.
A resolution is a new row and the tier folds forward from the resolution list, exactly as the world
snapshot folds from events. An earlier draft stored the field and would have fought the database.

RETRIEVAL IS A JOIN, NOT A SEARCH. Utterances are about entities, and entities have ids
(`bible_entities.entity_id`). `about()` returns EVERY utterance touching a subject, unranked: a
keeper that misses one contradicting claim adopts a false fact as ground truth, so completeness is
the requirement and top-k is a correctness regression.

WHAT THIS CANNOT DO, because the doc says so plainly: structural detection catches DIRECT
contradiction — same subject, same predicate, different object. It does not catch "the guards are
all women" against "Captain Aldric commands the gate", which needs knowing Aldric is a man and a
guard. That is inference, and it is the keeper's. A floor, not a ceiling.
"""
import re

from .errors import EngineError

# Tiers, from docs/keeper-of-truth.md. T0/T1 bind; T2 binds nothing; FICTION was tested and declined
# — it stays in the log and in the speaker's beliefs, and the world simply does not adopt it.
AUTHORED = "authored"        # T0
ESTABLISHED = "established"  # T1
SUPERPOSED = "superposed"    # T2 — the default, because speaking binds nothing
FICTION = "fiction"

BINDING = (AUTHORED, ESTABLISHED)
TIERS = (AUTHORED, ESTABLISHED, SUPERPOSED, FICTION)

_ARTICLES = ("the", "a", "an")


class ClaimError(EngineError):
    """An utterance that cannot be compared, or a resolution that names no verdict."""


def normalise(text):
    """One field -> its comparison form. Lowercase, unpunctuated, articles dropped, spaces joined.

    Deliberately blunt. It exists so "the Festival" and "festival" collide, not to do morphology —
    an aggressive stemmer would collapse distinctions the keeper needs to see, and a missed
    collision costs one undetected contradiction while a false one costs a wrong alert and teaches
    the keeper the detector cannot be trusted.
    """
    words = re.sub(r"[^a-z0-9\s-]", " ", str(text).lower()).split()
    kept = [w for w in words if w not in _ARTICLES] or words
    return "-".join(kept)


def extracts_of(said):
    """One utterance -> its list of `(subject, predicate, object)` extracts, normalised.

    An utterance may carry its facts in an `extracts` list, or — when it asserts exactly one — as
    subject/predicate/object at the top level. Both are legal, mirroring the blueprint's rule that
    an atom without particles is a complete atom.
    """
    if not isinstance(said, dict):
        raise ClaimError("CLAIM_UTTERANCE_NOT_AN_OBJECT",
                         "claims.extracts_of: utterance must be a dict, got %r"
                         % type(said).__name__)
    rows = said.get("extracts")
    if not rows:
        rows = [said] if said.get("subject") else []
    out = []
    for i, row in enumerate(rows):
        missing = [f for f in ("subject", "predicate") if not str(row.get(f, "")).strip()]
        if missing:
            raise ClaimError("CLAIM_EXTRACT_INCOMPLETE",
                             "claims.extracts_of: extract %d of %r is missing %s"
                             % (i, said.get("id", "an unidentified utterance"), ", ".join(missing)))
        out.append((normalise(row["subject"]), normalise(row["predicate"]),
                    normalise(row.get("object", ""))))
    return out


def tier_of(said, resolutions=()):
    """The utterance's tier, DERIVED by folding resolutions in order. Never read from a field.

    An unresolved utterance is SUPERPOSED — speaking binds nothing. An authored fact declares its
    tier because it entered from the bible rather than from a mouth; that is the one legitimate
    stored tier, and it is a property of provenance, not a mutable state.
    """
    tier = str((said or {}).get("tier", SUPERPOSED)).strip().lower()
    if tier not in TIERS:
        raise ClaimError("CLAIM_TIER_UNKNOWN",
                         "claims.tier_of: %r is not a tier; expected one of: %s"
                         % (tier, ", ".join(TIERS)))
    uid = (said or {}).get("id")
    for r in (resolutions or []):
        if uid is None or r.get("id") != uid:
            continue
        verdict = str(r.get("verdict", "")).strip().lower()
        if verdict not in TIERS:
            raise ClaimError("CLAIM_VERDICT_UNKNOWN",
                             "claims.tier_of: resolution for %r has verdict %r; expected one of: %s"
                             % (uid, r.get("verdict"), ", ".join(TIERS)))
        tier = verdict
    return tier


def live(utterances, resolutions=()):
    """The utterances still asserting something. FICTION was declined and no longer contests.

    Declined does not mean deleted: the text stays in the log and stays a fact about its speaker.
    """
    return [u for u in (utterances or []) if tier_of(u, resolutions) != FICTION]


def about(utterances, subject, resolutions=()):
    """Every live utterance carrying an extract on this subject — THE RETRIEVAL.

    A filter, in input order, unranked and uncapped. There is no scoring here that could justify
    dropping one, because the cost of dropping the wrong one is a false fact in the world.
    """
    want = normalise(subject)
    return [u for u in live(utterances, resolutions)
            if any(s == want for s, _, _ in extracts_of(u))]


def contradictions(utterances, resolutions=()):
    """Pairs of utterances that cannot both be true, with the key they collide on.

    Returns `(utterance_a, utterance_b, (subject, predicate))` — the PARENT utterances, so the
    keeper receives what was actually said and not only the flattened fact.

    Two BINDING utterances that disagree are returned like any other pair. That is not a state to
    be silent about: it means the bible contradicts itself or a collapse adopted something it
    should not have, and the keeper is exactly who should be told.
    """
    rows = live(utterances, resolutions)
    facts = [(u, extracts_of(u)) for u in rows]
    out = []
    for i, (a, a_ex) in enumerate(facts):
        for b, b_ex in facts[i + 1:]:
            seen = set()
            for s, p, o in a_ex:
                for s2, p2, o2 in b_ex:
                    if (s, p) != (s2, p2) or o == o2 or (s, p) in seen:
                        continue
                    seen.add((s, p))
                    out.append((a, b, (s, p)))
    return out


def tested(utterances, said, resolutions=()):
    """Is this utterance under test — does anything live contradict it?

    The first of the two collapse triggers in docs/keeper-of-truth.md. The second is RELIANCE
    (something load-bearing read it), which needs the read path instrumented and is not done here;
    the doc names it the hard trigger for that reason.
    """
    return any(a is said or b is said
               for a, b, _ in contradictions(utterances, resolutions))


# ---------------------------------------------------------------------------------------------
# PERSISTENCE. Everything above is pure and takes lists; everything below is where those lists come
# from. The split matters: the detector stays testable without a database, and the writer stays the
# only thing that knows SQL.


def record(con, run_id, turn, speaker, said, extracts=None, tier=SUPERPOSED):
    """Store one utterance and the facts it asserts -> utterance_id.

    `extracts` is the keeper's reading, not this module's: hard rule 3 puts extraction in an agent.
    Passing none stores the sentence with no facts indexed, which is honest — it says someone spoke
    and nothing was extracted, rather than pretending the utterance asserted nothing.

    Subjects and predicates are normalised on the way in, so the index agrees with the comparator
    the pure functions use instead of racing it.
    """
    if tier not in TIERS:
        raise ClaimError("CLAIM_TIER_UNKNOWN",
                         "claims.record: %r is not a tier; expected one of: %s"
                         % (tier, ", ".join(TIERS)))
    # THE WALL BELONGS TO THE WRITER, NOT TO ONE CALLER. `scripts/keeper.py:record_utterances`
    # already refused empty verbatim text, and this function — the OTHER way in — accepted it, so a
    # module whose whole doctrine is "the extract is an index into what was said, never a substitute
    # for it" would store an utterance that said nothing. One writer, one guard, here.
    if not str(speaker or "").strip():
        raise ClaimError("CLAIM_SPEAKER_EMPTY",
                         "claims.record: an utterance at turn %r names no speaker. Attribution IS "
                         "the claim — `tier_of` folds a keeper's rulings per utterance and "
                         "`faithfulness` asks who knew what, and neither question has an answer "
                         "about nobody." % (turn,))
    if not str(said or "").strip():
        raise ClaimError("CLAIM_SAID_EMPTY",
                         "claims.record: %r's utterance at turn %r carries no verbatim text. The "
                         "extract is an index INTO what was said, never a substitute for it."
                         % (speaker, turn))
    rows = extracts_of({"extracts": extracts, "id": "(new)"}) if extracts else []
    with con:
        cur = con.execute(
            "INSERT INTO utterances (run_id, turn, speaker, said, tier) VALUES (?, ?, ?, ?, ?)",
            (run_id, int(turn), str(speaker), str(said), tier))
        uid = cur.lastrowid
        for i, (subj, pred, obj) in enumerate(rows):
            con.execute("INSERT INTO claim_extracts (utterance_id, ord_no, subject, predicate, "
                        "object) VALUES (?, ?, ?, ?, ?)", (uid, i, subj, pred, obj))
    return uid


def resolve(con, run_id, utterance_id, at_turn, verdict, rationale=""):
    """Record the keeper's verdict on one utterance. APPEND-ONLY; the tier is never written back.

    A keeper that changes its mind appends a second resolution and `tier_of` folds them in order,
    last wins — the same shape as the world snapshot folding from events, and for the same reason.
    """
    if verdict not in TIERS:
        raise ClaimError("CLAIM_VERDICT_UNKNOWN",
                         "claims.resolve: %r is not a verdict; expected one of: %s"
                         % (verdict, ", ".join(TIERS)))
    # LAST WINS IS LAST-BY-TURN, not last-appended: `resolutions_for` orders by (at_turn, id) so the
    # FOLD can be reproduced at any `as_of`. That is correct and it has a sharp edge — a keeper
    # correcting itself with an EARLIER at_turn would be silently overruled by its own prior
    # verdict. Refused rather than documented: a correction that does not take effect is worse than
    # an error, because nothing reports it.
    prior = con.execute(
        "SELECT MAX(at_turn) AS t FROM claim_resolutions WHERE run_id = ? AND utterance_id = ?",
        (run_id, int(utterance_id))).fetchone()
    if prior is not None and prior["t"] is not None and int(at_turn) < prior["t"]:
        raise ClaimError(
            "CLAIM_RESOLUTION_BACKDATED",
            "claims.resolve: utterance %s already has a verdict at turn %d, and this one is dated "
            "turn %d — it would be overruled by the earlier ruling and take no effect. Date a "
            "correction at or after the verdict it corrects."
            % (utterance_id, prior["t"], int(at_turn)))
    with con:
        con.execute("INSERT INTO claim_resolutions (run_id, utterance_id, at_turn, verdict, "
                    "rationale) VALUES (?, ?, ?, ?, ?)",
                    (run_id, int(utterance_id), int(at_turn), verdict, str(rationale)))
    return True


def for_run(con, run_id, as_of=None):
    """Every utterance in the run -> the dict shape the pure functions above take.

    `as_of` bounds by TURN, so "what was known about this town in chapter 2" is answerable without
    the later chapters leaking in — the same discipline `read_api` applies everywhere else.
    """
    sql = "SELECT utterance_id, turn, speaker, said, tier FROM utterances WHERE run_id = ?"
    params = [run_id]
    if as_of is not None:
        sql += " AND turn <= ?"
        params.append(int(as_of))
    out = []
    for r in con.execute(sql + " ORDER BY turn, utterance_id", tuple(params)).fetchall():
        ex = con.execute("SELECT subject, predicate, object FROM claim_extracts "
                         "WHERE utterance_id = ? ORDER BY ord_no", (r["utterance_id"],)).fetchall()
        out.append({"id": r["utterance_id"], "turn": r["turn"], "speaker": r["speaker"],
                    "text": r["said"], "tier": r["tier"],
                    "extracts": [{"subject": e["subject"], "predicate": e["predicate"],
                                  "object": e["object"]} for e in ex]})
    return out


def resolutions_for(con, run_id, as_of=None):
    """The keeper's verdicts, in the order they were made — the fold order `tier_of` needs."""
    sql = "SELECT utterance_id, at_turn, verdict, rationale FROM claim_resolutions WHERE run_id = ?"
    params = [run_id]
    if as_of is not None:
        sql += " AND at_turn <= ?"
        params.append(int(as_of))
    return [{"id": r["utterance_id"], "turn": r["at_turn"], "verdict": r["verdict"],
             "rationale": r["rationale"]}
            for r in con.execute(sql + " ORDER BY at_turn, resolution_id", tuple(params)).fetchall()]
