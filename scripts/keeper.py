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
from src.engine import attachments                               # noqa: E402  (bond gate 5: the third writer of a hold)
from src.engine.severity import normalise_dimensions, gloss      # noqa: E402
from src.engine import tensions as _tensions                     # noqa: E402
from src.engine import world_events                              # noqa: E402
from src.engine.ledger import Ledger                             # noqa: E402
from src.engine.records import Event, RecordError                # noqa: E402
from critic import scene_turns                                   # noqa: E402
from composition_pass import build_attach_classify_prompt, holds_from_classification  # noqa: E402
from appraiser import _json_object                               # noqa: E402  (derive, not duplicate: the same brace-matcher appraiser's two seats already share)


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
                              led.elapsed_days_since(run_id, row.get("last_heated_at", 0)))
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

    # THE PRODUCER SIDE OF THE ATTACHMENT-RUBRIC MATCH (2026-09-19, gate keeper-attachment-rubric,
    # follow-up review). attach_candidates needs a claim extract whose OBJECT normalises to a
    # registered `loc.<id>` / `grp.<tag>` name — and until this block existed, the keeper was never
    # SHOWN those names, so a live reply could only ever phrase an object in prose ("this house"),
    # which can never match one. BYTE-IDENTICAL WHEN `world` IS NOT A DICT (canon_gate's own
    # default, and every caller before this follow-up): nothing below fires, so the prompt this
    # function has always built is untouched unless a world is actually in hand.
    names_block = ""
    if isinstance(world, dict):
        names_block = (
            "THE REGISTERED PLACES AND GROUPS:" + chr(10)
            + chr(10).join(attachments.names_for(world) or ["(none registered)"]) + chr(10) + chr(10)
            + "When a claim's extract OBJECT is one of these, write the object as that registered "
            "name — exactly, letter for letter: a saying that binds the speaker to a place he "
            "keeps, serves, belongs to or calls his own must carry it that way. Any other object "
            "stays the words said. No numbers here either." + chr(10) + chr(10))

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
        names_block +
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


# ---------------------------------------------------------------------------------------------
# THE RULING SEAT (2026-09-11) — the keeper of truth's other half: collapse.
# ---------------------------------------------------------------------------------------------

_RULING_SYSTEM = (
    "You are the KEEPER OF TRUTH of a simulated world. Characters say things about the world as "
    "they speak, and every such claim enters the record SUPERPOSED: said, binding nothing. You "
    "rule on the claims that have been TESTED and leave the rest alone.\n\n"
    "THE RULES:\n"
    "1. A claim that contradicts an AUTHORED or ESTABLISHED fact is FICTION: the speaker was wrong "
    "or lying, and the world does not adopt it. It stays in the record and stays theirs.\n"
    "2. Two superposed claims that contradict each other: keep the one the world can better afford "
    "as ESTABLISHED and mark the other FICTION — or leave both SUPERPOSED if nothing yet depends on "
    "either.\n"
    "3. A claim the story now relies on — later speech built on it, an act that assumed it — becomes "
    "ESTABLISHED, and from then on it is a fact for everyone.\n"
    "4. A claim nothing has tested stays SUPERPOSED. Leaving it out of your reply is the same as "
    "saying so.\n"
    "5. You do not invent. Every ruling names an utterance id from the list you are given; you rule "
    "on nothing else, and you never write a fact of your own.\n\n"
    "Reply with a JSON list, possibly empty: "
    '[{"utterance_id": int, "verdict": "established" | "fiction" | "superposed", "rationale": str}]. '
    "Nothing else.")


def build_ruling_prompt(led, run_id, first_turn, last_turn):
    """The ruling seat's messages: the facts in force on every subject the scene's claims touch,
    the scene's claims verbatim with their extracted facts, and the contradictions the engine
    found structurally. The keeper reads the sentence; the engine only compared the triples."""
    from src.engine import read_api as _read_api
    utts = claims.for_run(led.con, run_id, as_of=last_turn)
    resolutions = claims.resolutions_for(led.con, run_id, as_of=last_turn)
    scene = [u for u in utts if first_turn <= int(u["turn"]) <= last_turn]
    subjects = sorted({e["subject"] for u in scene for e in (u.get("extracts") or [])})
    facts = _read_api.established(led.con, run_id, subjects, as_of=last_turn).rows if subjects else []
    lines = []
    for f in facts:
        if f["authored"] or f["kept"]:
            lines.append("- %s: %s%s" % (f["subject"], f["authored"] or "",
                                          (" | kept as true: " + " / ".join(f["kept"])) if f["kept"] else ""))
    in_force = "\n".join(lines) or "(nothing authored or established touches these subjects)"
    said = "\n".join("- id %d, turn %d, %s said: %s\n    asserts: %s"
                      % (u["id"], u["turn"], u["speaker"], u["text"],
                         "; ".join("%s %s %s" % (e["subject"], e["predicate"], e["object"]) for e in (u.get("extracts") or [])) or "(nothing extractable)")
                      for u in scene) or "(no claims this scene)"
    pairs = claims.contradictions(utts, resolutions)
    ids = {u["id"] for u in scene}
    found = "\n".join("- id %d vs id %d on (%s %s): \"%s\" / \"%s\""
                       % (a["id"], b["id"], key[0], key[1], a["text"], b["text"])
                       for a, b, key in pairs if a["id"] in ids or b["id"] in ids) or "(none found structurally)"
    user = ("THE FACTS IN FORCE:\n%s\n\nTHE CLAIMS OF THIS SCENE (turns %d-%d):\n%s\n\n"
            "CONTRADICTIONS THE ENGINE FOUND:\n%s\n\nRule on what has been tested."
            % (in_force, first_turn, last_turn, said, found))
    return [{"role": "system", "content": _RULING_SYSTEM}, {"role": "user", "content": user}]


def parse_rulings(raw):
    """A raw reply -> the list of ruling dicts, or [] when no JSON list is there. Refuses nothing
    here; `apply_rulings` names what is wrong with each ruling."""
    text = str(raw or "")
    start = text.find("[")
    if start < 0:
        return []
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                try:
                    out = json.loads(text[start:i + 1])
                except ValueError:
                    return []
                return [r for r in out if isinstance(r, dict)] if isinstance(out, list) else []
    return []


def apply_rulings(led, run_id, rulings, at_turn, dry_run=False):
    """Write the keeper's verdicts -> (applied, left, rejected). ESTABLISHED and FICTION append a
    resolution (`claims.resolve`, append-only; the tier folds from it); SUPERPOSED writes nothing
    and is reported as left; an unknown utterance id is invention and an unknown verdict is
    refused, each with its reason."""
    known = {u["id"] for u in claims.for_run(led.con, run_id)}
    applied, left, rejected = [], [], []
    for r in rulings:
        uid = r.get("utterance_id")
        verdict = str(r.get("verdict") or "").strip().lower()
        if not isinstance(uid, int) or isinstance(uid, bool) or uid not in known:
            rejected.append((r, "utterance %r is not in this run — a ruling on what nobody said is invention" % (uid,)))
            continue
        if verdict == claims.SUPERPOSED:
            left.append(r)
            continue
        if verdict not in (claims.ESTABLISHED, claims.FICTION):
            rejected.append((r, "verdict %r is not one of established / fiction / superposed" % (verdict,)))
            continue
        if not dry_run:
            try:
                claims.resolve(led.con, run_id, uid, int(at_turn), verdict, str(r.get("rationale") or "")[:500])
            except Exception as e:                       # noqa: BLE001 — the seat reports, never crashes
                rejected.append((r, str(e)))
                continue
        applied.append(r)
    return applied, left, rejected


def rule_scene(led, run_id, first_turn, last_turn, model, stub, log=print):
    """THE CANON GATE's ruling pass: build the prompt, ask the seat, write the verdicts.
    Under `stub` nothing is ruled — the contested claims are printed as the alert the design
    requires (nothing collapses silently) and every claim stays superposed."""
    utts = claims.for_run(led.con, run_id, as_of=last_turn)
    scene = [u for u in utts if first_turn <= int(u["turn"]) <= last_turn]
    if not scene:
        log("  KEEPER: no claims in turns %d-%d — nothing to rule on" % (first_turn, last_turn))
        return {"applied": [], "left": [], "rejected": [], "contested": 0}
    resolutions = claims.resolutions_for(led.con, run_id, as_of=last_turn)
    ids = {u["id"] for u in scene}
    contested = [(a, b, k) for a, b, k in claims.contradictions(utts, resolutions) if a["id"] in ids or b["id"] in ids]
    if stub:
        log("  KEEPER (stub): %d claim(s) this scene stay superposed; %d contested pair(s)" % (len(scene), len(contested)))
        for a, b, k in contested:
            log("    contested (%s %s): \"%s\" / \"%s\"" % (k[0], k[1], a["text"], b["text"]))
        return {"applied": [], "left": scene, "rejected": [], "contested": len(contested)}
    import provider as _provider
    messages = build_ruling_prompt(led, run_id, first_turn, last_turn)
    try:
        raw = _provider.call(messages, model, "keeper-rule", led=led, run_id=run_id, turn=last_turn)
    except RecordError as exc:
        log("  KEEPER refused: %s" % str(exc)[:160])
        return {"applied": [], "left": scene, "rejected": [({}, str(exc))], "contested": len(contested)}
    applied, left, rejected = apply_rulings(led, run_id, parse_rulings(raw), at_turn=last_turn)
    log("  KEEPER: %d ruled (%s), %d left superposed, %d refused, %d contested pair(s)"
        % (len(applied), ", ".join("%s->%s" % (r["utterance_id"], r["verdict"]) for r in applied) or "none",
           len(scene) - len(applied), len(rejected), len(contested)))
    for r, why in rejected:
        log("    refused: %s" % why[:140])
    return {"applied": applied, "left": left, "rejected": rejected, "contested": len(contested)}


def notice_scene(led, run_id, first_turn, last_turn, model, stub, log=print, world=None):
    """THE NOTICING HALF at the canon gate: read the scene's turns, report what moved the world and
    what was SAID about it (with the extracted facts the fence and the ruling are keyed on).
    Utterances land at commit WITHOUT extracts (`claims.write` from the ledger carries the
    verbatim line only), so until this pass runs a saying is in the log but invisible to
    `claims.about` — the seat is what makes lore addressable. Under `stub` nothing is asked.

    `world`, passed straight to `build_keeper_prompt`: the producer side of the attachment-rubric
    match (2026-09-19, follow-up to gate keeper-attachment-rubric). Absent one this pass reports
    exactly as it always has — a claim's object stays whatever words were said, never a registered
    name, and `attach_candidates` downstream finds nothing to match (fails closed, not silently)."""
    turns = [t for t in scene_turns(led, run_id) if first_turn <= t["turn"] <= last_turn]
    if stub or not turns:
        log("  KEEPER (%s): noticing pass skipped for turns %d-%d" % ("stub" if stub else "no turns", first_turn, last_turn))
        return {"applied": [], "recorded": [], "rejected": []}
    import provider as _provider
    snap = led.fold(run_id, last_turn)
    try:
        raw = _provider.call(build_keeper_prompt(turns, snap, world=world, led=led, run_id=run_id), model, "keeper-notice",
                             led=led, run_id=run_id, turn=last_turn, max_tokens=1400)
    except RecordError as exc:
        log("  KEEPER noticing refused: %s" % str(exc)[:160])
        return {"applied": [], "recorded": [], "rejected": [({}, str(exc))]}
    reports = parse_rulings(raw)                       # the same "first JSON list" reader
    events = [p for p in reports if p.get("type")]
    said = [p for p in reports if not p.get("type") and p.get("said")]
    applied, rej_e = apply_proposals(led, run_id, events)
    recorded, rej_u = record_utterances(led, run_id, said)
    log("  KEEPER: %d world change(s) applied, %d saying(s) recorded, %d refused" % (len(applied), len(recorded), len(rej_e) + len(rej_u)))
    return {"applied": applied, "recorded": recorded, "rejected": rej_e + rej_u}


# ---------------------------------------------------------------------------------------------
# THE ATTACHMENT RUBRIC (2026-09-19, bond gate 5's THIRD WRITER of a hold) — the keeper prices a
# SELF-SOURCED hold when a character's own ESTABLISHED claim binds them to a registered place or
# group (docs/bond-arithmetic.md s3 point 3). Until now this was designed and never called
# (src/engine/attachments.py:14 said so by name); `canon_gate` below is the call.
#
# THREE GUARDS, split across `attach_candidates` (before the classifier ever answers) and
# `attach_price` (after):
#   1. NEVER PER-BEAT — only what `rule_scene` actually KEPT this pass (`attach_candidates` reads
#      the ruling list, never the raw turn stream).
#   2. NEVER A T2 CLAIM — only a ruling whose verdict is ESTABLISHED; a superposed boast prices
#      nothing (docs/keeper-of-truth.md: T2 binds nothing).
#   3. NEVER A RE-PRICE OF AN EXISTING HOLD — split in two because the word is not known until the
#      classifier answers: `attach_candidates` skips an entity already held at or above the highest
#      a self-sourced price can ever reach (`post`, since `declared_row(self_sourced=True)` always
#      prices one rung below the word); `attach_price` skips — silently, a SKIP and never a refusal
#      — a priced row that would not improve on the entity's latest existing hold.
# ---------------------------------------------------------------------------------------------


def attach_candidates(led, run_id, ruled_applied, first_turn, last_turn, world):
    """Guards 1 + 2, and the first half of guard 3 -> [(speaker_id, entity, sentence, utterance_id)].

    THE MATCH, both sides normalised through `claims.normalise` — the SAME comparator `claims.about`
    uses, applied at both ends of the triple rather than one:

      * SUBJECT vs SPEAKER. `row["speaker"]` is whatever the noticing pass wrote (the keeper prompt
        shows the actor's id in the turn stream, so a live reply should echo it back) — normalised
        and compared against the extract's subject, which `claims.for_run` already stores normalised
        (schema: `claim_extracts` holds what `claims.write` put through `extracts_of` on the way in).
        Calling `extracts_of` again here is idempotent re-normalisation, the same thing `about` does
        to every utterance it filters. A CASE difference (the id "maren" vs a title-cased "Maren")
        washes out through `normalise`'s lower-casing; a genuinely DIFFERENT display name would not
        match, and the match simply yields no candidate rather than guessing — FAIL CLOSED, exactly
        the gate's own FRAME_ASSUMPTIONS entry: a live pass that misses every self-bound saying is
        the falsifier, and the printed candidate count is the check.
      * OBJECT vs THE WORLD'S NAMES. `attachments.names_for(world)` returns prefixed ids
        ("loc.<id>", "grp.<tag>"); `claims.normalise` folds the prefix's period to a hyphen exactly
        like any other punctuation ("loc.mill" -> "loc-mill"), and `extracts_of` normalises every
        extract field the same way — so a registered name compared UN-normalised against a
        normalised extract object could never match, for ANY entity, ever (every registered name
        carries that period). The registered names are normalised the identical way before the
        membership test, with a reverse map back to the canonical "loc."/"grp." form the pricing
        functions need.
    """
    registered = attachments.names_for(world)
    registered_norm = {claims.normalise(name): name for name in registered}
    # THE CEILING: the highest a SELF-SOURCED price can ever reach. `declared_row(self_sourced=True)`
    # always prices one rung below the word, and `life` is the warmest word on the table — so
    # `post`'s hold is the ceiling no keeper-priced row can cross. Read from the table, never a
    # second literal.
    ceiling = attachments.hold_of(attachments.word_below("life"))
    utts_by_id = {u["id"]: u for u in claims.for_run(led.con, run_id, as_of=last_turn)}
    existing_cache = {}
    seen, out = set(), []
    for ruling in ruled_applied or ():
        if str(ruling.get("verdict") or "").strip().lower() != claims.ESTABLISHED:
            continue                                          # guard 2: never a T2 claim
        row = utts_by_id.get(ruling.get("utterance_id"))
        if row is None or not (first_turn <= int(row["turn"]) <= last_turn):
            continue                                          # not this pass's own scene
        speaker = row["speaker"]
        want_subject = claims.normalise(speaker)
        for subj, _pred, obj in claims.extracts_of(row):
            if subj != want_subject or obj not in registered_norm:
                continue
            entity = registered_norm[obj]
            key = (speaker, entity)
            if key in seen:
                continue
            seen.add(key)
            if speaker not in existing_cache:
                existing_cache[speaker] = attachments.rows_for(led.con, run_id, speaker)
            latest = None
            for _t, e, h, sign, _src in existing_cache[speaker]:
                if e == entity and sign == "+":
                    latest = h                                # rows_for is in log order; last wins
            if latest is not None and latest >= ceiling:
                continue                                      # guard 3, first half
            out.append((speaker, entity, row["text"], row["id"]))
    return out


def attach_price(speaker_id, entity, reply, sentence, world, existing_rows):
    """One classifier reply for ONE (speaker, entity) candidate -> (row or None, refusal_code or None).

    Reuses `composition_pass.holds_from_classification` — the SAME parser the composition pass uses,
    with its six COMPOSITION_ATTACH_* refusals; those propagate here as this candidate's refusal
    code (derive, never stand up a second parser for the same reply shape).

    TWO REFUSALS BELONG TO THIS SEAT, not the shared parser:
      * KEEPER_ATTACH_OFF_TARGET — the reply parsed clean but named no entry for `entity`, the one
        entity this candidate's prompt ever asked about (`attach_scene` builds the prompt from the
        ONE kept `sentence`, never the whole backstory the composition pass shows).
      * ATTACH_LIFE_CAP — applied directly, not through `validate_block` (shaped for a whole SHEET
        block, not one incoming row), by reading `attachments._LIFE_CAP` — never a second literal —
        against the speaker's EXISTING life-tier rows plus this reply, IF its WORD is `life`. At the
        WORD, not the stored price: a self-sourced row prices one rung below (a `life` claim lands at
        `post`'s .60, under the .85 floor `validate_block` itself tests), so the STORED value could
        never trip that check — and the cap guards the CLAIM ("my ship, my crew, my port, my guild,
        all family"), not only the number that survives the discount.

    GUARD 3'S SECOND HALF (the first is `attach_candidates`, before the call): a row that prices at
    or below the entity's latest existing hold is not an improvement and is not written — returned as
    (None, None), a SKIP, never a refusal (nothing was wrong with the reply).
    """
    try:
        holds, _gaps = holds_from_classification(reply, sentence, world)
        if entity not in holds:
            raise RecordError(
                "KEEPER_ATTACH_OFF_TARGET",
                "the attachment classifier answered about %s, not the one candidate entity it was "
                "asked about (%s)" % (", ".join(sorted(holds)) or "nothing", entity))
        word, _because = holds[entity]
        life_count = sum(1 for (_t, e, h, sign, _src) in existing_rows
                         if sign == "+" and h >= attachments.hold_of("life"))
        if (attachments.hold_of(word) >= attachments.hold_of("life")
                and life_count + 1 > attachments._LIFE_CAP):
            raise RecordError(
                "ATTACH_LIFE_CAP",
                "%s already carries %d life-tier hold(s) (cap %d) — a keeper cannot price a third "
                "%r claim on %s" % (speaker_id, life_count, attachments._LIFE_CAP, word, entity))
        row = attachments.declared_row(speaker_id, entity, word, "keeper", self_sourced=True)
    except RecordError as exc:
        return None, exc.code

    latest = None
    for _t, e, h, sign, _src in existing_rows:
        if e == entity and sign == "+":
            latest = h
    if latest is not None and row.hold <= latest:
        return None, None                                     # guard 3, second half: not an improvement
    return row, None


def attach_scene(led, run_id, ruled_applied, first_turn, last_turn, world, model, stub, log=print):
    """THE THIRD WRITER, live: candidates, one classifier call each, priced, one BATCHED
    `attachments.declare`. -> {"attached": [rows], "refused": [(speaker, entity, code)],
    "candidates": n, "skipped": m}.

    Under `stub`, or with no world at all, nothing is asked. `world is None` is checked here rather
    than left to `attach_candidates`'s own `ATTACH_WORLD_NOT_A_DICT`: a caller with no bible in hand
    is not a malformed reply to refuse, and the correct response is to skip the pass — fail closed —
    not to crash the scene over it (canon_gate's docstring; `attachments.names_for` needs the bible
    the keeper was never handed before this gate).
    """
    if world is None:
        log("  KEEPER: attachment rubric skipped (no world)")
        return {"attached": [], "refused": [], "candidates": 0, "skipped": 0}
    candidates = attach_candidates(led, run_id, ruled_applied, first_turn, last_turn, world)
    if stub:
        log("  KEEPER (stub): %d attachment candidate(s), nothing asked" % len(candidates))
        return {"attached": [], "refused": [], "candidates": len(candidates), "skipped": 0}
    import provider as _provider
    attached, refused, skipped = [], [], 0
    for speaker_id, entity, sentence, _utterance_id in candidates:
        existing = attachments.rows_for(led.con, run_id, speaker_id)
        try:
            raw = _provider.call(build_attach_classify_prompt(sentence, world), model, "keeper-attach",
                                 led=led, run_id=run_id, turn=last_turn)
        except RecordError as exc:
            refused.append((speaker_id, entity, exc.code))
            continue
        row, code = attach_price(speaker_id, entity, _json_object(raw), sentence, world, existing)
        if row is not None:
            attached.append(row)
        elif code is not None:
            refused.append((speaker_id, entity, code))
        else:
            skipped += 1
    written = attachments.declare(led.con, run_id, last_turn, attached) if attached else 0
    log("  KEEPER: %d attachment(s) priced (%s), %d refused, %d skipped of %d candidate(s)"
        % (written, ", ".join("%s:%s" % (r.char_id, r.entity) for r in attached) or "none",
           len(refused), skipped, len(candidates)))
    for speaker_id, entity, code in refused:
        log("    refused: %s %s -> %s" % (speaker_id, entity, code))
    return {"attached": attached, "refused": refused, "candidates": len(candidates), "skipped": skipped}


def canon_gate(led, run_id, first_turn, last_turn, model, stub, log=print, world=None):
    """The keeper's whole pass at the CANON gate (docs/orchestration.md): notice, rule, then price.

    THE ATTACHMENT RUBRIC IS BUILT (bond gate 5, 2026-09-19; docs/bond-arithmetic.md s3 point 3,
    s9 gate 5). The trigger, exactly as the prior draft of this docstring named it: an utterance
    `rule_scene` ruled ESTABLISHED whose extract's subject is the speaker and whose object is a
    registered `loc.`/`grp.` name. THREE GUARDS, all in `attach_candidates` / `attach_price`:
      1. never a per-beat call — only what THIS PASS's `rule_scene` actually kept;
      2. never a T2 claim — only a ruling whose verdict is ESTABLISHED;
      3. never a re-price of an existing hold — before the classifier call, an entity already held
         at or above the highest a self-sourced price can reach is skipped outright; after, a priced
         row that does not improve on the entity's latest existing hold is a silent skip.
    The classifier is `composition_pass.build_attach_classify_prompt` over the kept sentence; the
    price is `attachments.declared_row(..., 'keeper', self_sourced=True)`, one rung below the word
    until an act by someone else on the entity corroborates it; the `life` cap is
    `attachments._LIFE_CAP`; the rows are written with `attachments.declare` at the gate's last turn.

    `world` is the bible dict `attachments.names_for` reads places/groups from — the one thing this
    seat never had before this gate (MIGRATION: both drivers now pass `world=world`). Defaults to
    None so an existing caller that never had a world to pass (a test, an old script) still gets a
    canon_gate that fails closed rather than one that raises. Passed to `notice_scene` too (follow-up,
    2026-09-19): the NOTICING pass is the producer of the claim extracts `attach_candidates` later
    matches, so it is the one that has to be SHOWN the registered names — `attach_scene` receiving
    `world` was necessary but not sufficient on its own.
    """
    noticed = notice_scene(led, run_id, first_turn, last_turn, model, stub, log=log, world=world)
    ruled = rule_scene(led, run_id, first_turn, last_turn, model, stub, log=log)
    attached = attach_scene(led, run_id, ruled["applied"], first_turn, last_turn, world, model, stub, log=log)
    return {"noticed": noticed, "ruled": ruled, "attached": attached}


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
    ap.add_argument("--rule", action="store_true",
                    help="the RULING seat: with --prompt-only emit the ruling prompt for the run's claims; "
                         "with --rulings FILE apply the verdicts")
    ap.add_argument("--rulings", default=None, metavar="FILE", help="a JSON list of rulings to apply (with --rule)")
    args = ap.parse_args()

    led = Ledger(args.db or books.db_path(args.vault))
    turns = scene_turns(led, args.run)
    if not turns:
        print("no committed turns in run %s — nothing to read" % args.run)
        return 0

    if args.rule:
        first, last = min(t["turn"] for t in turns), max(t["turn"] for t in turns)
        if args.prompt_only:
            print(json.dumps(build_ruling_prompt(led, args.run, first, last), indent=2))
            return 0
        if not args.rulings:
            raise SystemExit("--rule needs --prompt-only (emit) or --rulings FILE (apply)")
        with open(args.rulings, encoding="utf-8") as fh:
            rulings = json.load(fh)
        applied, left, rejected = apply_rulings(led, args.run, rulings, at_turn=last, dry_run=args.dry_run)
        print("ruled %d, left superposed %d, refused %d%s" % (len(applied), len(left), len(rejected), " (dry run)" if args.dry_run else ""))
        for r, why in rejected:
            print("  refused: %s" % why)
        return 0
    if args.prompt_only:
        # world STAYS None HERE: this standalone CLI path opens only the chronicle db
        # (books.db_path above) and has no --book/--fixture flag to load a bible from, so it has
        # never had a world to pass and still does not (2026-09-19 follow-up). The prompt this
        # emits is therefore the pre-follow-up prompt, unchanged, same as any other world=None call.
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
