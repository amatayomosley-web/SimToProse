#!/usr/bin/env python3
"""keeper.py — the emitting seat: read the committed stream, move the WORLD.

THE GAP THIS FILLS. `ledger._project` moves six snapshot fields and every world-moving type owns
one of them, but the eight types appeared ONLY inside the fold — never in an emitter. Four sites
proved it: `direct.py` writes one event per turn typed from `tags["type"]`; all six
`consolidation.ACTOR_TAG_TYPES` carry `world_map: "none"`; `scene.py`'s `_law_events` returns `[]`
absent a violation; and nothing else writes an event at all. So `agents[x].location`, `holdings`,
`information` and `tensions` were seeded and then frozen for a whole book. A character could die
and `life_status` stayed `"alive"`.

`characters/*.json` carries `current.location` while the DB does not, which is the same fact in two
places with only the dead one queryable. This seat is what makes the live one move.

THE SPLIT, and why this is a script and not an engine module. CLAUDE.md hard rule 3 keeps model
calls out of `src/engine/`, and the work divides cleanly along that line:

  * NOTICING — that a character is somewhere new, that someone now knows a thing — is reading, and
    reading is what the model is for. That half is `build_keeper_prompt` below.
  * WARRANT — whether the world actually moved — is arithmetic. `world_events.would_change` projects the
    candidate onto a copy of the folded snapshot and `world_events.would_move` diffs it, enforcing
    the rule `world_events.py` states: AN EVENT IS A WORLD EVENT IFF FOLDING IT WOULD CHANGE THE
    SNAPSHOT. No taste, no whitelist. It writes nothing to find out, because it cannot: the log is
    append-only at the database and the first draft's append-then-roll-back was refused by the
    trigger, which is hard rule 2 working.

So a proposal can be well-formed, plausible, and still REJECTED here — because the fold says the
world was already like that. That rejection is the point: it is what keeps a keeper from narrating
the snapshot into motion.

WHAT THIS DOES NOT DO. It does not invent. Every proposal names a turn, and the turn's recorded
`{thought, action}` is the source; a proposal for a turn the run does not have is refused. It does
not touch `threaten`, which declares a world effect it has never had — a world-model decision that
is not this seat's to make (`tests/test_world_events.py` prints it as DEBT every run).

Usage:
  python scripts/keeper.py --vault "<book>" --run <run_id> --prompt-only
  python scripts/keeper.py --vault "<book>" --run <run_id> --propose <file.json>
  python scripts/keeper.py --vault "<book>" --run <run_id> --propose <file.json> --dry-run
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import books                                     # noqa: E402
from src.engine import claims                                    # noqa: E402
from src.engine.severity import normalise_dimensions, gloss      # noqa: E402
from src.engine import tensions as _tensions                     # noqa: E402
from src.engine import world_events                              # noqa: E402
from src.engine.ledger import Ledger                             # noqa: E402
from src.engine.records import Event, RecordError                # noqa: E402
from critic import scene_turns                                   # noqa: E402


def _band_temperatures(snapshot, led=None, run_id=None):
    """Tension temperatures -> the severity WORD for their band, AFTER cooling. Returns a copy.

    THE READER THE DECAY DID NOT HAVE. `tensions.effective` shipped with zero production callers,
    so "tension temperatures cool absent fuel" was true only inside a test — the
    documented-mechanism-with-no-reader class this repo has now named five times, recommitted in the
    build that cites it. The one live consumer of the register is this prompt, so this is where time
    has to be applied: a tension heated two hundred declared units ago must not still read `marked`.

    Hard rule 5 keeps engine scalars out of a prompt. The keeper is not an actor, so the law does
    not bind it the way it binds `build_turn_messages` — but a temperature is exactly the kind of
    number the law exists to keep out of a model's hands, and handing one over invites the keeper
    to reason about deltas instead of reading what happened. The word carries what it needs.

    The `interests` map is withheld outright: it is the pricing table, and a reader who can see it
    can aim at it. The engine prices; the keeper reads.
    """
    from src.engine import world_appraisal as _wa
    snap = dict(snapshot or {})
    tensions = snap.get("tensions")
    if not isinstance(tensions, dict):
        return snap
    banded = {}
    for name, row in tensions.items():
        row = dict(row or {})
        try:
            t = float(row.get("temperature", 0.0))
        except (TypeError, ValueError):
            t = 0.0
        if led is not None and run_id is not None:
            from src.engine import tensions as _tn
            t = _tn.effective(dict(row, temperature=t),
                              led.elapsed_since(run_id, row.get("last_heated_at", 0)))
        row["temperature"] = _wa.band(t)
        row.pop("interests", None)
        banded[name] = row
    snap["tensions"] = banded
    return snap


def build_keeper_prompt(turns, snapshot, world=None, led=None, run_id=None):
    """The keeper's messages: the rubric, the world as it stands, and the stream to read.

    The rubric is `world_events.rubric()` — meaning and boundary per type, generated from the same
    table `_project` folds, so the prompt cannot drift from what the engine will accept. The
    boundary tests are the load-bearing half: each separates a type from the nearest thing it is
    NOT ("crossing a room is not a move"), which is what a reader needs and what a type name alone
    does not give them.
    """
    lines = []
    for t in turns:
        lines.append("turn %d — %s\n  does/says: %s\n  privately thinks: %s"
                     % (t["turn"], t["actor"], t["action"], t.get("thought", "")))
    stream = "\n".join(lines)

    sys_msg = (
        "You are the KEEPER of a simulated world. You read what characters did and said, and you "
        "report only what changed about the WORLD — never what anyone felt, which is recorded "
        "elsewhere and is not yours.\n\n"
        "You do not invent. Every report names the turn it came from, and if the turn does not "
        "say it, you do not report it. Silence is a correct answer and the common one: most beats "
        "move nobody and nothing." + chr(10) + chr(10) + world_events.rubric() + chr(10) + chr(10) + gloss()
        + chr(10) + chr(10) + _tensions.rubric() + chr(10) + chr(10) +
        "You also report what characters SAID ABOUT THE WORLD - a town's traditions, who founded "
        "what, whose mother led the procession. Those bind nothing on their own and are recorded "
        "as claims for a keeper to rule on later, so report them even when you doubt them. Always "
        "carry the VERBATIM sentence: the extracted fact is an index into what was said, never a "
        "substitute for it, and the clause you would drop may be the whole point." + chr(10) + chr(10) +
        "Reply with a JSON list, possibly empty. A world change is "
        '{"turn": int, "type": str, "payload": {...}, "actor": str|null, "target": str|null}. '
        "A claim is "
        '{"turn": int, "speaker": str, "said": str, "extracts": [{"subject": str, '
        '"predicate": str, "object": str}]}. Nothing else.')

    # RULE 5, NOW DUE. This dumps the snapshot into a prompt, and tensions carry a temperature —
    # so the moment the register went live a float describing world state would reach a model
    # here. An adversarial review flagged this gray zone twice while it was harmless; it stops
    # being harmless with this build. Temperatures render as the severity WORD for their band.
    snapshot = _band_temperatures(snapshot, led, run_id)
    user_msg = ("THE WORLD AS IT STANDS:\n%s\n\nTHE RECORDED STREAM:\n%s\n\n"
                "Report what changed about the world."
                % (json.dumps({k: v for k, v in (snapshot or {}).items() if k != "clock"},
                              indent=2, sort_keys=True)[:4000], stream))
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]


def apply_proposals(led, run_id, proposals, dry_run=False):
    """Validate, test warrant by folding, and append what genuinely moves the world.

    -> (applied, rejected) where each rejected entry is (proposal, reason). Reasons are the
    rejection, not a summary of it, so a keeper's operator can see WHICH rule refused a report.

    Three gates in order, cheapest first:
      1. the turn must exist in the run — a proposal about a turn nobody recorded is invention
      2. the payload must carry the keys `_project` reads — `world_events.validate_payload`
      3. folding it must CHANGE the snapshot — `world_events.would_change`, writing nothing

    Gate 3 is the one that cannot be reasoned around, and it is why a plausible report gets
    refused: if the world already said what the proposal says, nothing moved.
    """
    known_turns = {t["turn"] for t in scene_turns(led, run_id)}
    applied, rejected = [], []
    for p in proposals:
        turn = p.get("turn")
        if turn not in known_turns:
            rejected.append((p, "turn %r is not in this run — a report about an unrecorded turn "
                                "is invention" % (turn,)))
            continue
        etype = p.get("type")
        # THE SEVERITY SEAM. `tensions.rubric()` asks the keeper to grade "in the severity words"
        # and `severity.rubric()` names this seat as its consumer — and until 2026-09-02 no seam
        # resolved them here, so every conforming reply died in the fold with a type error. The
        # drivers have had this seam since the ladder landed; the seat that grades world events did
        # not, because every test graded in floats.
        payload = dict(p.get("payload") or {})
        # THE LOG STORES FLOATS. WORDS DIE AT THIS BOUNDARY.
        #
        # A severity word is an AUTHORING convenience; a logged word is a hostage to the ladder.
        # `fold_seed` resolves one through `severity._MAGNITUDE` at replay, so a word left in the log
        # means recalibrating that table silently refolds every historical run into a different
        # world — hard rule 2's "pure function of the log" true in form and false in substance.
        # Measured 2026-09-02: a keeper-minted seed stored "marked" and folded to whatever the
        # ladder said today. The gate for this very build rejected "a fold that accepts words"
        # as a suppressed path, and then shipped one.
        #
        # Both word-carrying fields resolve here, together, so the two cannot drift apart the way
        # they just did — dimensions were normalised pre-write and temperature was not.
        if isinstance(payload.get("temperature"), str):
            from src.engine.severity import WORDS, value_of
            word = payload["temperature"].strip().lower()
            if word not in WORDS:
                rejected.append((p, "temperature %r is not a severity word; expected one of: %s"
                                    % (payload["temperature"], ", ".join(WORDS))))
                continue
            payload["temperature"] = value_of(word)
            p = dict(p, payload=payload)     # so the applied report echoes what was WRITTEN
        if isinstance(payload.get("dimensions"), dict):
            try:
                payload = normalise_dimensions(payload)
            except Exception as e:                   # noqa: BLE001 — the seat reports, never crashes
                rejected.append((p, "a severity word could not be resolved: %s" % e))
                continue
            p = dict(p, payload=payload)
        try:
            world_events.validate_payload(etype, payload)
        except Exception as e:                       # noqa: BLE001 — the seat reports, never crashes
            rejected.append((p, str(e)))
            continue

        # VISIBILITY IS NOT THE KEEPER'S TO SET, and it takes records.py's "public" default. A
        # world event nobody can observe is not a world event; and `consolidation.CATALOG` carries a
        # per-type visibility that nothing reads, which `tests/test_declared_is_read.py` exempts
        # with the reason "wiring it changes who can see what, which is a knowledge-model decision,
        # not a plumbing one". Accepting it here would have made that decision by accident — and
        # the guard caught the attempt, because a `.get("visibility")` is exactly how it detects a
        # reader of that column.
        ev = Event(type=etype, payload=dict(payload),
                   actor=p.get("actor"), target=p.get("target"), location=p.get("location"))
        try:
            ev.validate()
        except RecordError as e:
            rejected.append((p, str(e)))
            continue

        # A DELTA NAMING NO LIVE TENSION is a REFERENCE error, not a warrant failure. The fold
        # treats it as a no-op (it has to stay total over the log), so without this the operator
        # is told "it would not change the snapshot — it is a beat", and goes looking for a scope
        # problem when what they have is a typo.
        if etype == "tension" and payload.get("id") and not _tensions.is_seed(payload):
            _live = (led.fold(run_id, turn) or {}).get("tensions") or {}
            if payload["id"] not in _live:
                rejected.append((p, "names no live tension %r — live here: %s. A tension is "
                                    "authored by the room; the keeper heats one, never mints it."
                                    % (payload["id"], ", ".join(sorted(_live)) or "(none)")))
                continue

        # THE WARRANT TEST, asked BEFORE the write. The first draft appended, folded, diffed and
        # rolled back — and the append-only trigger refused the DELETE, which is hard rule 2 doing
        # its job. `world_events.would_change` projects the candidate onto a COPY of the snapshot with
        # the same `_project` the real fold uses, so nothing is written to find out.
        # Judged at the proposal's OWN turn, which is where `append` puts it. And wrapped, like
        # gates 1 and 2: this was the one gate outside the try/except, so a KeyError in the fold
        # took the whole run down AFTER earlier proposals in the same file had committed. "The seat
        # reports, never crashes" has to hold for every gate or it holds for none.
        try:
            moved = world_events.would_change(led, run_id, turn, ev, at_turn=turn)
        except Exception as e:                       # noqa: BLE001 — the seat reports, never crashes
            rejected.append((p, "the fold could not judge it: %s: %s" % (type(e).__name__, e)))
            continue
        if not moved:
            rejected.append((p, "folding it would not change the snapshot — it is a beat, not a "
                                "world event (%s)" % world_events.field_of(etype)))
            continue
        if not dry_run:
            world_events.append(led, run_id, turn, [ev])
        applied.append(p)
    return applied, rejected


def record_utterances(led, run_id, reports):
    """Store what characters SAID about the world, so lore accretes.

    The other half of the keeper's job, and the one with a different failure mode. A world event
    either moves the snapshot or it does not; an utterance binds NOTHING by default — it enters as
    SUPERPOSED and stays there until a keeper rules on it (`docs/keeper-of-truth.md`). So there is
    no warrant test here: recording that someone said a thing is always warranted, because it is
    always true that they said it.

    -> (recorded, rejected). Refuses a report about a turn the run does not have, for the same
    reason `apply_proposals` does: a report with no source is invention.
    """
    known_turns = {t["turn"] for t in scene_turns(led, run_id)}
    recorded, rejected = [], []
    for r in reports:
        turn = r.get("turn")
        if turn not in known_turns:
            rejected.append((r, "turn %r is not in this run — a report about an unrecorded turn "
                                "is invention" % (turn,)))
            continue
        if not str(r.get("speaker") or "").strip():
            # NAMED HERE AS WELL AS IN `claims.record`, and that is not a duplicate guard: this seat
            # reports to an operator, and before this the blank speaker reached the database and came
            # back through the blanket except below as `CHECK constraint failed: speaker <> ''` —
            # true, and useless to whoever has to fix the report.
            rejected.append((r, "an utterance needs a SPEAKER — an unattributed quote binds nobody, "
                                "and no keeper can rule on what nobody said"))
            continue
        if not str(r.get("said") or "").strip():
            rejected.append((r, "an utterance needs its VERBATIM text — the extract is an index "
                                "into what was said, never a substitute for it"))
            continue
        try:
            uid = claims.record(led.con, run_id, turn, r["speaker"],
                                r["said"], r.get("extracts") or [])
        except Exception as e:                       # noqa: BLE001 — the seat reports, never crashes
            rejected.append((r, str(e)))
            continue
        recorded.append(dict(r, utterance_id=uid))
    return recorded, rejected


def main():
    ap = argparse.ArgumentParser(
        description="the keeper — read the committed stream, move the world",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="A proposal is REFUSED when folding it would not change the snapshot. That is the "
               "rule, not a heuristic: an event that leaves the world identical was a beat, and "
               "the appraisal tier already recorded it.")
    ap.add_argument("--vault", required=True, help="the BOOK folder (vault)")
    ap.add_argument("--run", required=True, help="run_id to read")
    ap.add_argument("--db", default=None, help="chronicle db path (default <vault>/runs/<book>.db)")
    ap.add_argument("--propose", default=None, metavar="FILE",
                    help="a JSON list of proposals to validate and apply")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run",
                    help="report what WOULD be applied; write nothing")
    ap.add_argument("--prompt-only", action="store_true", dest="prompt_only",
                    help="emit the keeper prompt for a model to fill (key-free path)")
    args = ap.parse_args()

    led = Ledger(args.db or books.db_path(args.vault))
    turns = scene_turns(led, args.run)
    if not turns:
        print("no committed turns in run %s — nothing to read" % args.run)
        return 0

    if args.prompt_only:
        snap = led.fold(args.run, max(t["turn"] for t in turns))
        print(json.dumps(build_keeper_prompt(turns, snap, led=led, run_id=args.run), indent=2))
        return 0

    if not args.propose:
        raise SystemExit("pass --prompt-only to emit the prompt, or --propose FILE to apply reports")

    with open(args.propose, encoding="utf-8") as fh:
        proposals = json.load(fh)
    if not isinstance(proposals, list):
        raise SystemExit("--propose file must hold a LIST, got %s" % type(proposals).__name__)

    # A proposal file may carry BOTH world events and utterances; they are different reports with
    # different rules (an event must move the world; an utterance binds nothing and always counts).
    events = [p for p in proposals if p.get("type")]
    saids  = [p for p in proposals if p.get("said")]
    applied, rejected = apply_proposals(led, args.run, events, args.dry_run)
    if saids:
        if args.dry_run:
            # A dry run that silently skipped half the file reported "would apply N of M" against a
            # denominator that counted utterances it never looked at. An operator inspecting an
            # append-only log before writing to it has to see BOTH halves.
            print("would record %d utterance(s) (not validated in --dry-run)" % len(saids))
        else:
            rec, rej = record_utterances(led, args.run, saids)
            print("recorded %d of %d utterances" % (len(rec), len(saids)))
            for r, why in rej:
                print("  -  t%-4s utterance     %s" % (r.get("turn"), why))
    # The denominator is the WORLD-EVENT proposals, not the whole file: utterances are a different
    # report with a different rule, and counting them here made the ratio meaningless.
    print("%s %d of %d world-event reports" % ("would apply" if args.dry_run else "applied",
                                               len(applied), len(events)))
    for p in applied:
        print("  +  t%-4s %-14s %s" % (p.get("turn"), p.get("type"), p.get("payload")))
    for p, why in rejected:
        print("  -  t%-4s %-14s %s" % (p.get("turn"), p.get("type"), why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
