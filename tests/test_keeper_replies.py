#!/usr/bin/env python3
"""test_keeper_replies.py — the keeper's three replies: the keys each contract names, the types it writes, and what a report carried beyond it (gate keeper-replies, 2026-09-25).

THE CONTRACTS PLAN, G5, for the keeper (the owner's "Go"; board #258: an extra key is recorded and reported, never
refused; a missing or invalid known key is still refused). The keeper read its replies by named gets: a world change's
payload went whole into the append-only log, where readers that take every event's payload read a stray `injuries`
as the beat's own; a field of the wrong type crashed the pass before the scene was parked, or went in as its string;
an unreadable reply vanished; every refusal it built was prose, and the noticing pass printed only a count. Checked:

  [1] the declarations in src/engine/replies.py and the shapes the keeper's prompts state agree, parsed not grepped;
      the prompts' bytes pinned; world_events.payload_keys (per type and per tension form) equals what the REAL fold
      reads, recorded at run time through any helper it calls, over a grid of payloads in two worlds (each state
      branch of the fold taken both ways)
  [2] a world change: each HEAD crash and accident the fold reads refused by a registered code with nothing written;
      what HEAD accepted and nothing names still applies; a key nothing reads - a stray payload key, an unknown
      dimension, a severity word the type never reads, junk in an id the fold does not read for the report - is left
      out and named, never the reason a report is refused; text the record cannot hold refused where it would be
      written; each strip checked against the fold itself, report by report
  [3] a claim and a ruling: routed by world type (a claim labelled "claim" is a claim); a speaker, said or extract
      field that is not storable text refused; one that indexes nothing refused by name; an optional value that is
      not (an extract's object, a ruling's rationale) written as "" and named; extras named on kept reports only
  [4] a reply the keeper cannot read, named and never refused - the first list found by brackets OUTSIDE strings
  [5] the canon gate end to end through a fake provider on a strict cp1252 console: every pass prints its refusals
      and what it left out, as printable ASCII, and completes; the CLI routes and reads its files the same way

Script-style: check(), main(), exit code. Stdlib only. Every book here is invented (a millhouse, maren and edda).
"""
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import keeper                                                    # noqa: E402
import provider                                                  # noqa: E402
from composition_pass import build_attach_classify_prompt        # noqa: E402
from src.engine import claims, codes, fold, injuries, replies, scene_facts, world_events  # noqa: E402
from src.engine.ledger import Ledger                             # noqa: E402
from src.engine.records import Event, PATHS, TurnCommit          # noqa: E402

FAILS = []
TMP = tempfile.mkdtemp(prefix="swe_keeper_replies_")
WORLD = {"locations": [{"id": "millhouse", "what": "the old millhouse on the ford"}], "people": []}
SAID = "the millhouse is mine"
SEED = {"id": "the-levy", "temperature": 0.1, "factions": ["millers"], "interests": {"threat": 0.5},
        "watches": {"parties": ["maren"], "locations": []}, "cooling": "slow"}
ARROW = "→"                                                 # not in cp1252
LONE = "x\ud800"                                                 # a lone surrogate: JSON carries it, sqlite cannot
NAN, INF = float("nan"), float("inf")


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


_N = [0]


def _led(turns=3, tension=False):
    _N[0] += 1
    led = Ledger(os.path.join(TMP, "k%d.db" % _N[0]))
    led.create_run("r1", {"catalog_version": 1, "models": {}, "prompt_versions": {}})
    for cid in ("maren", "edda"):
        led.register_character("r1", cid, {"name": cid.title()}, {"temperament": "authored", "world_seed": {}})
    for t in range(turns):
        led.append_turn(TurnCommit(run_id="r1", turn=t, actor="maren", thought="t%d" % t,
                                   action='she said "%s"' % SAID, tags={"type": "mundane"},
                                   affect={p: 0.5 for p in PATHS}, events=[]))
    if tension:
        world_events.append(led, "r1", 0, [Event(type="tension", payload=dict(SEED))])
    return led


def _events(led):
    """The keeper's rows: every event but the fixture's own seeded tension."""
    rows = led.con.execute("SELECT type, actor, target, location, payload FROM events ORDER BY event_id").fetchall()
    out = [(r[0], r[1], r[2], r[3], json.loads(r[4])) for r in rows]
    return [r for r in out if not (r[0] == "tension" and r[4].get("id") == SEED["id"] and "interests" in r[4])]


def _coded(why):
    m = re.match(r"\[([A-Z][A-Z0-9_]+)\] ", why or "")
    return m.group(1) if m and codes.is_registered(m.group(1)) else None


def _one(led, p, dry_run=False):
    """One proposal through apply_proposals -> (applied, reason or None, the code or None, crashed)."""
    try:
        applied, rejected = keeper.apply_proposals(led, "r1", [p], dry_run=dry_run)
    except Exception as e:                                       # noqa: BLE001 - a crash is what this looks for
        return [], "%s: %s" % (type(e).__name__, e), None, True
    why = rejected[0][1] if rejected else None
    return applied, why, _coded(why) if why else None, False


def _refused(name, p, code, tension=True):
    led = _led(tension=tension)
    applied, why, got, crashed = _one(led, p)
    check("%s:-refused-%s,-nothing-written" % (name, code),
          not crashed and not applied and got == code and not _events(led), (why, _events(led)))
    return led


# ---- [1] ---------------------------------------------------------------------------------------------------------

def _annotated(s):
    """A shape written with type words (int, str, str|null, {...}) and word alternatives ("a" | "b") -> parsed JSON."""
    s = re.sub(r'("(?:[^"\\]|\\.)*")(?:\s*\|\s*"(?:[^"\\]|\\.)*")+', r"\1", s)
    s = s.replace("{...}", "{}")
    s = re.sub(r"\b(?:int|str|null)(?:\|(?:int|str|null))*\b", "0", s)
    return json.loads(s)


def _between(text, a, b):
    i = text.index(a) + len(a)
    return text[i:text.index(b, i)]


class _Rec(dict):
    """A dict that records every key asked of it into `log` ("*" when it is walked whole, "#len" when its size or
    emptiness is asked), and every key TESTED for membership while absent into `probes` - a guard such as
    `if "fact" in payload`, or `tensions.is_seed` asking a delta for `interests`. The second review's D1b and D4 read a
    new key behind exactly such a guard; the fourth's W3 read one by `pop`, which the recorder did not override, so
    `pop`, `setdefault`, `copy` and `==` are recorded too. `prefix` names a nested map ("dimensions."). What it cannot
    see: an unbound `dict.get(payload, k)`, which bypasses every override - declared, not recorded."""
    def __init__(self, d, log, probes, prefix=""):
        super().__init__(d)
        self._log, self._probes, self._pre = log, probes, prefix

    def _read(self, k):
        self._log.add(self._pre + str(k))

    def get(self, k, *a):
        self._read(k)
        return dict.get(self, k, *a)

    def __getitem__(self, k):
        self._read(k)
        return dict.__getitem__(self, k)

    def pop(self, k, *a):
        self._read(k)
        return dict.pop(self, k, *a)

    def setdefault(self, k, *a):
        self._read(k)
        return dict.setdefault(self, k, *a)

    def __contains__(self, k):
        here = dict.__contains__(self, k)
        (self._log if here else self._probes).add(self._pre + str(k))
        return here

    def __iter__(self):
        self._read("*")
        return dict.__iter__(self)

    def keys(self):
        self._read("*")
        return dict.keys(self)

    def items(self):
        self._read("*")
        return dict.items(self)

    def values(self):
        self._read("*")
        return dict.values(self)

    def copy(self):
        self._read("*")
        return dict.copy(self)

    def __eq__(self, other):
        self._read("*")
        return dict.__eq__(self, other)

    __hash__ = None

    def __len__(self):
        self._read("#len")
        return dict.__len__(self)


_ID_VARIANTS = ({}, {"actor": None}, {"target": None}, {"location": None}, {"actor": "a_stranger"},
                {"target": "a_stranger"}, {"actor": "edda"}, {"actor": None, "target": None})
# The fold's own FORM test: the one key it may probe for while absent that the keeper need not keep - a delta has no
# `interests`, and carrying one makes it a seed (`tensions.is_seed`).
_FORM_TESTS = {"tension": {"interests"}}


def _grid(payload):
    """A payload and its variants: the whole; each key absent; each true-or-false value flipped - so a read behind a
    value the whole payload never takes (the second review's D3b: a harm's `terminal` false) is reached."""
    out = [dict(payload)]
    out += [{k: v for k, v in payload.items() if k != drop} for drop in payload]
    out += [dict(payload, **{k: not v}) for k, v in payload.items() if isinstance(v, bool)]
    return out


_SNAP = []


def _worlds():
    """The worlds the grid is folded in: each state branch the fold has, taken both ways. The third review: a read
    that fires only when a fact is already known (its G1), or only for an actor new to the snapshot (G2), passed a grid
    folded in one world - and the keeper's own check sees only the world a report is judged in. The first world: the
    cast alive, nothing known or held, the levy watching maren. The second: a fact known, edda dead, an asset held and
    one destroyed, maren and edda allied, maren elsewhere; the seed's tension already live, a tension watching only a
    place, and the delta's tension absent. The third (fourth review): no tension at all. The id variants add a
    stranger as actor and as target, the dead edda as actor, and no ids at all."""
    if not _SNAP:
        _SNAP.append(_led(tension=True).fold("r1", 1))
        _SNAP.append(_led().fold("r1", 1))
        led = _led()
        place_only = dict(SEED, id="the-watch", watches={"parties": [], "locations": ["the mill"]})
        world_events.append(led, "r1", 0, [
            Event(type="tension", payload=dict(SEED, id="the-weir")), Event(type="tension", payload=place_only),
            Event(type="reveal", actor="maren", payload={"fact": "f", "to": ["edda"]}),
            Event(type="harm", actor="maren", target="edda", payload={"terminal": True}),
            Event(type="seize", actor="maren", payload={"asset": "a"}),
            Event(type="destroy-asset", actor="maren", payload={"asset": "b"}),
            Event(type="bond", actor="maren", target="edda", payload={}),
            Event(type="move", actor="maren", payload={"to": "the ridge"})])
        _SNAP.append(led.fold("r1", 1))
    return _SNAP


def _wrapped(obj, log, probes):
    """A parsed payload as the recorder: the payload itself, and a threat's `dimensions` read as dotted names."""
    if isinstance(obj.get("dimensions"), dict):
        obj = dict(obj, dimensions=_Rec(obj["dimensions"], log, probes, prefix="dimensions."))
    return _Rec(obj, log, probes)


def _held(reads, probes, kept, form=()):
    """Do the recorded reads stay within what the keeper keeps? -> (ok, what escaped). Top level: only kept keys, never
    a walk or a size; a threat's dimensions: only the seven, never a walk (its emptiness may be asked)."""
    from src.engine.world_appraisal import DIMENSIONS
    top = {r for r in reads if not r.startswith("dimensions.")}
    dims = {r[len("dimensions."):] for r in reads | probes if r.startswith("dimensions.")} - {"#len"}
    tprobes = {r for r in probes if not r.startswith("dimensions.")}
    bad = (top - set(kept)) | (tprobes - set(kept) - set(form)) | {"dimensions." + d for d in dims - set(DIMENSIONS)}
    return not bad, sorted(bad)


def _fold_reads(etype, payload, worlds=None):
    """(keys read, keys probed while absent) - the REAL fold projecting this payload in every world under every id
    variant, recorded through any helper it calls, a separate `if`, a local, a membership guard. A projection that
    raises still records what it read before raising (a mutant's `payload["wound"]` on an absent key raises after the
    read)."""
    import copy
    reads, probes = set(), set()
    real = fold.json
    for snap in (worlds or _worlds()):
        for over in _ID_VARIANTS:
            ids = dict({"actor": "maren", "target": "edda", "location": "the mill"}, **over)
            row = world_events._candidate_row(Event(type=etype, payload=dict(payload), **ids), 1)
            fold.json = types.SimpleNamespace(loads=lambda s, _r=reads, _p=probes: _wrapped(real.loads(s), _r, _p),
                                              dumps=real.dumps)
            try:
                fold.project(copy.deepcopy(snap), _Rec(row, set(), set()))
            except Exception:                                    # noqa: BLE001 - what it read is what counts
                pass
            finally:
                fold.json = real
    return reads, probes


def declarations_and_prompts():
    print("[1] the declarations, the prompts, and what the fold reads agree")
    system = keeper.build_keeper_prompt([], {})[0]["content"]
    change = _annotated(_between(system, "A world change is ", ". A claim is"))
    check("a-world-change's-keys-are-the-asked-ones-plus-location", set(change) | {"location"} == set(
        replies.CHANGE_KEYS) and "location" not in change, sorted(change))
    claim = _annotated(_between(system, "A claim is ", ". Nothing else."))
    check("a-claim's-keys", set(claim) == set(replies.CLAIM_KEYS), sorted(claim))
    check("...its-extracts-a-list-of-exactly-the-declared-fields", isinstance(claim["extracts"], list) and all(
        set(e) == set(replies.CLAIM_ENTRIES["extracts"]) for e in claim["extracts"]), claim["extracts"])
    ruling = _annotated(_between(keeper._RULING_SYSTEM, "possibly empty: ", ". Nothing else."))
    check("a-ruling's-keys", isinstance(ruling, list) and set(ruling[0]) == set(replies.RULING_KEYS), ruling)
    attach_sys = build_attach_classify_prompt("x", WORLD)[0]["content"]
    attach = _annotated(_between(attach_sys, "Reply with JSON only:\n", "\n`gaps`"))
    check("an-attach-reply's-keys", set(attach) == set(replies.ATTACH_KEYS), sorted(attach))
    for blk, fields in replies.ATTACH_ENTRIES.items():
        check("...its-%s-a-list-of-exactly-the-declared-fields" % blk, isinstance(attach[blk], list) and all(
            set(e) == set(fields) for e in attach[blk]), attach[blk])
    # THE PROMPTS' BYTES: recorded runs replay by a hash of the exact prompt (provider.prompt_key). Pinned to the
    # hashes HEAD produced (computed on both trees, 2026-09-25): a change to the keeper's prompts, or to the rubrics
    # they render, fails here, and is only ever made on purpose.
    h = lambda m: hashlib.sha256(json.dumps(m, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    for name, msgs, want in (("the-noticing-prompt", keeper.build_keeper_prompt([], {}), "d8ed855c7d1d67df"),
                             ("...shown-the-registered-names", keeper.build_keeper_prompt([], {}, world=WORLD),
                              "439d01aba066c5a9"),
                             ("the-ruling-system-prompt", keeper._RULING_SYSTEM, "760d0cfda12efc77"),
                             ("the-attach-prompt", build_attach_classify_prompt(SAID, WORLD), "e5957c533a23e1f3")):
        check("%s's-bytes-are-HEAD's" % name, h(msgs) == want, h(msgs))
    # WHAT THE FOLD READS, recorded at run time over a GRID of payloads (the first review's M1-M3: a read in a separate
    # `if`, through a helper, into a local; the second's D1b, D3b, D4: a read behind a membership guard, or behind a value
    # the fixture never took) - a missed read is data stripped from an append-only log. The keeper's strip also checks
    # itself per report (`keeper._strip_check`); this is what keeps the table from falling behind in the first place.
    cases = [("move", {"to": "the ridge"}), ("harm", {"terminal": True}), ("reveal", {"fact": "f", "to": ["edda"]}),
             ("seize", {"asset": "a"}), ("destroy-asset", {"asset": "b"}), ("seize", {"asset": "b"}),
             ("destroy-asset", {"asset": "a"}), ("betray", {}), ("bond", {}),
             ("threaten", {"dimensions": {"threat": 0.5}}), ("tension", dict(SEED, id="the-weir")),
             ("tension", {"id": "the-levy", "heat": 0.1})]
    check("every-world-type-is-folded-here", {t for t, _p in cases} == set(world_events.TYPES), world_events.TYPES)
    for etype, payload in cases:
        form = "" if etype != "tension" else ("-seed" if "interests" in payload else "-delta")
        reads, probes = _fold_reads(etype, payload)
        want = set(world_events.payload_keys(etype, payload))
        top = {r for r in reads if not r.startswith("dimensions.")}
        held, bad = _held(reads, probes, want, _FORM_TESTS.get(etype, ()))
        check("payload_keys(%s%s)-is-what-the-fold-read-of-the-whole-payload" % (etype, form),
              top == want and held, (sorted(top), sorted(want), bad))
        for variant in _grid(payload)[1:]:
            reads, probes = _fold_reads(etype, variant)
            held, bad = _held(reads, probes, world_events.payload_keys(etype, variant), _FORM_TESTS.get(etype, ()))
            check("...a-variant-%s-reads-and-probes-only-kept-keys" % sorted(variant), held, bad)
        check("...and-starts-with-the-required-keys-%s%s" % (etype, form),
              world_events.payload_keys(etype, payload)[:len(world_events.required_keys(etype))]
              == world_events.required_keys(etype))
    # the recorder can see what an AST scan could not (controls: a read through a helper, and one behind a guard)
    real, log, probes = fold.json, set(), set()
    fold.json = types.SimpleNamespace(loads=lambda s: _Rec(real.loads(s), log, probes), dumps=real.dumps)
    try:
        pl = fold.json.loads('{"to": "x"}')
        (lambda p: p.get("via"))(pl)
        "scope" in pl
    finally:
        fold.json = real
    check("the-recorder-sees-a-read-through-a-helper-and-a-probe-behind-a-guard", "via" in log and "scope" in probes,
          (log, probes))
    # ...and the grid reaches reads that fire only in some WORLD (the third review's G1 and G2, fold mutants that
    # passed a one-world grid): a reveal reading a key only when its fact is already known, a move reading one only
    # for an actor new to the snapshot
    real_project = fold.project

    def gated(snap, ev):
        pl = fold.json.loads(ev["payload"])
        if ev["type"] == "reveal" and pl.get("fact") in snap["information"]:
            pl.get("also")
        if ev["type"] == "move" and ev["actor"] not in snap["agents"]:
            pl.get("from")
        return real_project(snap, ev)
    fold.project = gated
    try:
        first = _fold_reads("reveal", {"fact": "f", "to": ["edda"]}, worlds=_worlds()[:1])[0]
        both = _fold_reads("reveal", {"fact": "f", "to": ["edda"]})[0]
        moved = _fold_reads("move", {"to": "the ridge"})[0]
    finally:
        fold.project = real_project
    check("...and-the-second-world-reaches-a-read-that-fires-only-when-the-fact-is-known", "also" not in first
          and "also" in both, (sorted(first), sorted(both)))
    check("...and-the-stranger-a-read-that-fires-only-for-an-actor-new-to-the-world", "from" in moved, sorted(moved))
    # ...and the fourth review's W1-W4, which the round-4 grid missed: a destroy that reads a key only for a HELD asset,
    # a move that reads one only for a DEAD actor, one read by `pop`, and an eighth dimension read only where a tension
    # watches a place

    def gated4(snap, ev):
        pl = fold.json.loads(ev["payload"])
        if ev["type"] == "destroy-asset" and (snap["holdings"].get(pl.get("asset")) or {}).get("controller"):
            pl.get("by")
        if ev["type"] == "move" and (snap["agents"].get(ev["actor"]) or {}).get("life_status") == "dead":
            pl.get("carried")
        if ev["type"] == "move" and ev["actor"] not in snap["agents"]:
            pl.pop("from", None)
        if ev["type"] == "threaten" and any((t.get("watches") or {}).get("locations") for t in snap["tensions"].values()):
            (pl.get("dimensions") or {}).get("loudness")
        return real_project(snap, ev)
    fold.project = gated4
    try:
        destroyed = _fold_reads("destroy-asset", {"asset": "a"})[0]
        moved = _fold_reads("move", {"to": "the ridge"})[0]
        threat = _fold_reads("threaten", {"dimensions": {"threat": 0.5}})[0]
    finally:
        fold.project = real_project
    check("...and-a-destroy-of-a-HELD-asset,-a-move-by-a-DEAD-actor,-a-read-by-pop-(the-fourth-review's-W1-W3)",
          "by" in destroyed and "carried" in moved and "from" in moved, (sorted(destroyed), sorted(moved)))
    check("...and-an-eighth-dimension-read-where-a-tension-watches-a-place-(W4),-held-to-the-seven",
          "dimensions.loudness" in threat and not _held(threat, set(), ("dimensions",))[0], sorted(threat))
    log, probes = set(), set()
    rec = _Rec({"a": 1, "b": 2}, log, probes)
    rec.setdefault("a")
    rec.copy()
    len(rec)
    check("...and-the-recorder-sees-setdefault,-a-copy-and-a-size", {"a", "*", "#len"} <= log, sorted(log))


# ---- [2] ---------------------------------------------------------------------------------------------------------

def world_changes():
    print("[2] a world change: what is written, what is refused, what is named")
    move = {"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the ridge"}}
    delta = {"turn": 1, "type": "tension", "payload": {"id": "the-levy", "heat": 0.1}}
    # every shape that CRASHED the whole pass at HEAD (the probe log and the differential) - refused, nothing written
    for name, p, code in (
            ("HEAD-crashed-on-a-list-turn", dict(move, turn=[1]), "KEEPER_TURN_UNKNOWN"),
            ("HEAD-crashed-on-a-map-turn", dict(move, turn={"t": 1}), "KEEPER_TURN_UNKNOWN"),
            ("HEAD-crashed-on-a-text-payload", dict(move, payload="to the ridge"), "KEEPER_REPORT_FIELD_TYPE"),
            ("HEAD-crashed-on-a-number-payload", dict(move, payload=5), "KEEPER_REPORT_FIELD_TYPE"),
            ("HEAD-crashed-on-a-true-payload", dict(move, payload=True), "KEEPER_REPORT_FIELD_TYPE"),
            ("HEAD-crashed-on-a-list-actor-on-a-seize",
             {"turn": 1, "type": "seize", "actor": ["maren"], "payload": {"asset": "the mill"}}, "KEEPER_REPORT_FIELD_TYPE"),
            ("HEAD-crashed-on-a-map-target-on-a-betray",
             {"turn": 1, "type": "betray", "actor": "maren", "target": {"id": "edda"}, "payload": {}},
             "KEEPER_REPORT_FIELD_TYPE"),
            ("HEAD-crashed-on-a-list-tension-id-on-a-delta", dict(delta, payload={"id": ["the-levy"], "heat": 0.1}),
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-crashed-on-a-lone-surrogate-actor", dict(move, actor=LONE), "KEEPER_REPORT_FIELD_TYPE"),
            ("HEAD-crashed-on-a-lone-surrogate-target-on-a-harm",
             {"turn": 1, "type": "harm", "actor": "maren", "target": LONE, "payload": {"terminal": True}},
             "KEEPER_REPORT_FIELD_TYPE")):
        _refused(name, p, code)
    # every ACCIDENT HEAD accepted
    for name, p, code in (
            ("HEAD-took-a-true-turn-as-turn-1", dict(move, turn=True), "KEEPER_TURN_UNKNOWN"),
            ("HEAD-took-a-false-turn-as-turn-0", dict(move, turn=False), "KEEPER_TURN_UNKNOWN"),
            ("HEAD-read-a-list-of-pairs-as-a-payload", dict(move, payload=[["to", "the ridge"]]), "KEEPER_REPORT_FIELD_TYPE"),
            ("HEAD-wrote-a-number-actor-as-'5'", dict(move, actor=5), "KEEPER_REPORT_FIELD_TYPE"),
            ("HEAD-made-each-letter-of-a-text-to-a-knower",
             {"turn": 1, "type": "reveal", "actor": "maren", "payload": {"fact": "the fever", "to": "edda"}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-bricked-resume-on-a-number-fact",
             {"turn": 1, "type": "reveal", "actor": "maren", "payload": {"fact": 5, "to": ["edda"]}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-bricked-resume-on-a-number-asset", {"turn": 1, "type": "seize", "actor": "maren", "payload": {"asset": 7}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-bricked-park-and-resume-on-a-lone-surrogate-fact",
             {"turn": 1, "type": "reveal", "actor": "maren", "payload": {"fact": LONE, "to": ["edda"]}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-bricked-park-and-resume-on-a-lone-surrogate-asset",
             {"turn": 1, "type": "seize", "actor": "maren", "payload": {"asset": LONE}}, "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-parked-a-list-as-a-location", dict(move, payload={"to": ["the ridge"]}), "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-killed-on-terminal-'false'",
             {"turn": 1, "type": "harm", "actor": "maren", "target": "edda", "payload": {"terminal": "false"}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-killed-on-terminal-1",
             {"turn": 1, "type": "harm", "actor": "maren", "target": "edda", "payload": {"terminal": 1}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-killed-on-terminal-1.0",
             {"turn": 1, "type": "harm", "actor": "maren", "target": "edda", "payload": {"terminal": 1.0}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-killed-a-phantom-'   '-on-a-whitespace-target",
             {"turn": 1, "type": "harm", "actor": "maren", "target": "   ", "payload": {"terminal": True}},
             "KEEPER_REPORT_ID_EMPTY"),
            ("HEAD-wrote-a-number-tension-id-as-'5'", {"turn": 1, "type": "tension", "payload": dict(SEED, id=5)},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-heated-on-a-dimension-valued-true",
             {"turn": 1, "type": "threaten", "actor": "maren", "payload": {"dimensions": {"threat": True}}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-logged-a-NaN-dimension",
             {"turn": 1, "type": "threaten", "actor": "maren", "payload": {"dimensions": {"threat": NAN}}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-heated-on-a-dimension-past-the-ladder",
             {"turn": 1, "type": "threaten", "actor": "maren", "payload": {"dimensions": {"threat": 2.5}}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-logged-an-Infinity-dimension",
             {"turn": 1, "type": "threaten", "actor": "maren", "payload": {"dimensions": {"threat": INF}}},
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("HEAD-heated-to-the-top-on-a-NaN-heat", dict(delta, payload={"id": "the-levy", "heat": NAN}),
             "WORLD_EVENT_PAYLOAD_VALUE_TYPE")):
        _refused(name, p, code)
    led = _led()
    _one(led, {"turn": 1, "type": "harm", "actor": "maren", "target": "edda", "payload": {"terminal": "false"}})
    _one(led, {"turn": 1, "type": "harm", "actor": "maren", "target": "   ", "payload": {"terminal": True}})
    agents = led.fold("r1", 1)["agents"]
    check("...and-both-are-alive,-no-phantom-agent", agents["edda"]["life_status"] == agents["maren"]["life_status"]
          == "alive" and set(agents) == {"maren", "edda"}, agents)
    # AN ID THAT NAMES NOTHING, decided PER REPORT by projecting it both ways (the second review: `victim = target or
    # actor` reads a harm's actor only when it has no target) - written as null and named where it decides nothing,
    # refused where the fold would read it
    for name, p, want in (
            ("a-blank-target-reads-as-no-target:-written-null,-the-actor-dies-as-with-a-null-target",
             {"turn": 1, "type": "harm", "actor": "maren", "target": "", "payload": {"terminal": True}},
             ("applied", "target", "maren")),
            ("an-explicit-null-target-is-no-target,-nothing-named",
             {"turn": 1, "type": "harm", "actor": "maren", "target": None, "payload": {"terminal": True}},
             ("applied", None, "maren")),
            ("a-number-actor-beside-a-named-victim-decides-nothing:-null,-named,-the-victim-dies",
             {"turn": 1, "type": "harm", "actor": 5, "target": "edda", "payload": {"terminal": True}},
             ("applied", "actor", "edda")),
            ("a-blank-actor-beside-a-named-victim-decides-nothing:-null,-named",
             {"turn": 1, "type": "harm", "actor": "", "target": "edda", "payload": {"terminal": True}},
             ("applied", "actor", "edda")),
            ("a-number-actor-with-no-target-IS-the-victim:-refused",
             {"turn": 1, "type": "harm", "actor": 5, "payload": {"terminal": True}},
             ("KEEPER_REPORT_FIELD_TYPE", None, None))):
        led = _led()
        applied, why, got, crashed = _one(led, p)
        agents = led.fold("r1", 1)["agents"]
        if want[0] == "applied":
            dead = sorted(a for a, v in agents.items() if v["life_status"] == "dead")
            ok = (not crashed and len(applied) == 1 and dead == [want[2]]
                  and (applied[0].get("extra") or ()) == ((want[1],) if want[1] else ()))
        else:
            ok = not crashed and not applied and got == want[0] and not _events(led)
        check(name, ok, (why, applied, _events(led)))
    # JUNK IN BOTH IDS a betrayal or bond reads TOGETHER (`if actor and target`): each alone decides nothing, the two
    # together decide the edge - refused by the first one's code, not as "a beat" (third review)
    for name, p, code in (
            ("a-betrayal's-number-ids", {"turn": 1, "type": "betray", "actor": 5, "target": 7, "payload": {}},
             "KEEPER_REPORT_FIELD_TYPE"),
            ("a-bond's-true-and-number-ids", {"turn": 1, "type": "bond", "actor": True, "target": 1, "payload": {}},
             "KEEPER_REPORT_FIELD_TYPE"),
            ("a-betrayal's-whitespace-ids", {"turn": 1, "type": "betray", "actor": "  ", "target": "\t", "payload": {}},
             "KEEPER_REPORT_ID_EMPTY")):
        led = _led()
        applied, why, got, crashed = _one(led, p)
        check("junk-in-both-ids-read-together:-%s-refused-%s,-nothing-written" % (name, code), not crashed
              and not applied and got == code and "together with target" in why and not _events(led), why)
    led = _led()
    applied, why, got, crashed = _one(led, {"turn": 1, "type": "betray", "actor": "", "target": "", "payload": {}})
    check("...while-two-EMPTY-ids-the-fold-never-reads-leave-a-beat,-as-at-HEAD", not applied
          and got == "KEEPER_NOT_A_WORLD_EVENT", why)
    # THE IDS NAMED ARE THE ONES THE FOLD READS ON THE REPORT AS GIVEN (fourth review): a harm with junk in both ids
    # kills its target, so the target is named, with the target's code; a pair of mixed kinds names its first
    for name, p, code, named in (
            ("a-harm-with-a-number-actor-and-a-blank-target-names-the-TARGET",
             {"turn": 1, "type": "harm", "actor": 5, "target": "  ", "payload": {"terminal": True}},
             "KEEPER_REPORT_ID_EMPTY", "target: blank"),
            ("a-harm-with-a-blank-actor-and-a-number-target-names-the-TARGET",
             {"turn": 1, "type": "harm", "actor": "  ", "target": 7, "payload": {"terminal": True}},
             "KEEPER_REPORT_FIELD_TYPE", "target: the wrong type"),
            ("a-betrayal's-mixed-pair-names-its-FIRST,-by-its-own-code",
             {"turn": 1, "type": "betray", "actor": 5, "target": "  ", "payload": {}},
             "KEEPER_REPORT_FIELD_TYPE", "actor: the wrong type")):
        led = _led()
        applied, why, got, crashed = _one(led, p)
        check("%s,-%s" % (name, code), not crashed and not applied and got == code and named in (why or "")
              and not _events(led), why)
    # NESTED TOO DEEP (third review): an unread key nested past what the fold can parse was refused as a stale table -
    # it cannot have been read, and leaving it out keeps it from bricking every later fold; inside a map the keeper
    # keeps, the depth is refused by code, where HEAD wrote it
    deep = {}
    for _i in range(5000):
        deep = {"n": deep}
    led = _led()
    applied, why, got, crashed = _one(led, dict(move, payload={"to": "the ridge", "note": deep}))
    check("an-unread-key-nested-too-deep-to-fold-is-left-out-and-named,-not-a-stale-table",
          not crashed and applied and applied[0].get("extra") == ("payload.note",)
          and _events(led) == [("move", "maren", None, None, {"to": "the ridge"})],
          (why, applied and applied[0].get("extra")))
    led = _led()
    applied, why, got, crashed = _one(led, {"turn": 1, "type": "tension", "payload": dict(
        SEED, id="the-weir", watches={"parties": ["maren"], "locations": [], "note": deep})})
    check("a-value-nested-too-deep-inside-a-kept-map-is-refused-by-code,-nothing-written",
          not crashed and not applied and got == "WORLD_EVENT_PAYLOAD_VALUE_TYPE" and "too deep" in (why or "")
          and not _events(led), why)
    led = _led(tension=True)
    applied, why, _c, _x = _one(led, {"turn": 1, "type": "threaten", "actor": "maren", "target": None, "location": None,
                                      "payload": {"dimensions": {"threat": "marked"}}})
    check("a-threat-with-the-prompt's-own-null-ids-applies,-nothing-named", applied and "extra" not in applied[0],
          (why, applied))
    # A STALE TABLE REFUSES LOUDLY: were `payload_keys` to forget a key the fold reads, the strip would change the world,
    # and the report is refused rather than written without it
    real_keys = world_events.payload_keys
    world_events.payload_keys = lambda t, pl=None: tuple(k for k in real_keys(t, pl) if k != "cooling")
    try:
        led = _led()
        applied, why, got, crashed = _one(led, {"turn": 1, "type": "tension",
                                                "payload": dict(SEED, id="the-weir", cooling="fast")})
    finally:
        world_events.payload_keys = real_keys
    check("a-left-out-key-the-fold-reads-refuses-the-report-KEEPER_TABLE_STALE,-nothing-written",
          not crashed and not applied and got == "KEEPER_TABLE_STALE" and "cooling" in why and not _events(led), why)
    # ...a DIMENSION the seven do not name, were the fold to read one (the third review's F8: the dimension strip is
    # checked only through the report as given, its dimensions put back - a step no test had pinned)
    from src.engine import world_appraisal
    real_heat = world_appraisal.heat
    world_appraisal.heat = lambda d, i, s: real_heat(d, i, s) + (0.05 if (d or {}).get("loudness") else 0.0)
    try:
        led = _led(tension=True)
        applied, why, got, crashed = _one(led, {"turn": 1, "type": "threaten", "actor": "maren",
                                                "payload": {"dimensions": {"threat": 0.6, "loudness": 0.5}}})
    finally:
        world_appraisal.heat = real_heat
    check("a-left-out-DIMENSION-the-fold-reads-refuses-the-report-KEEPER_TABLE_STALE,-nothing-written",
          not crashed and not applied and got == "KEEPER_TABLE_STALE" and "dimensions.loudness" in why
          and not _events(led), why)
    # ...and a key the fold reads only BESIDE an id the keeper nulls: the report is projected as given, whole, not
    # only as written (third review)
    real_project = fold.project

    def via_when_targeted(snap, ev):
        out = real_project(snap, ev)
        if ev["type"] == "move" and ev["actor"] and ev["target"] and json.loads(ev["payload"]).get("via"):
            out["agents"][ev["actor"]]["via"] = json.loads(ev["payload"])["via"]
        return out
    fold.project = via_when_targeted
    try:
        led = _led()
        applied, why, got, crashed = _one(led, dict(move, target=5, payload={"to": "the ridge", "via": "the ford"}))
        led_b = _led()
        _ab, why_b, got_b, _cb = _one(led_b, dict(move, target=5, payload={"to": "the ridge", "via": "the ford",
                                                                            "note": "x"}))
    finally:
        fold.project = real_project
    check("a-left-out-key-read-only-beside-a-junk-id-refuses-KEEPER_TABLE_STALE,-nothing-written",
          not crashed and not applied and got == "KEEPER_TABLE_STALE" and "via" in why and not _events(led), why)
    check("...naming it alone, key by key, not the unread key beside it", got_b == "KEEPER_TABLE_STALE"
          and (why_b or "").split("]", 1)[-1].strip().startswith("via: ") and not _events(led_b), why_b)

    def via_beside_location(snap, ev):
        out = real_project(snap, ev)
        if ev["type"] == "move" and ev["actor"] and ev["location"] and json.loads(ev["payload"]).get("via"):
            out["agents"][ev["actor"]]["via"] = json.loads(ev["payload"])["via"]
        return out
    fold.project = via_beside_location
    try:
        led = _led()
        applied, why, got, crashed = _one(led, dict(move, target=5, location=True,
                                                    payload={"to": "the ridge", "via": "the ford"}))
    finally:
        fold.project = real_project
    check("...one-read-beside-the-SECOND-of-two-junk-ids-too-(the-report-as-given,-whole)",
          not crashed and not applied and got == "KEEPER_TABLE_STALE" and "via" in (why or "") and not _events(led), why)
    # THE STALE TABLE NAMES ONLY WHAT THE FOLD READS, key by key - and an unread key nested too deep no longer
    # exempts its neighbours (fourth review: the whole projection raised, and every left-out key escaped)

    def from_read(snap, ev):
        out = real_project(snap, ev)
        if ev["type"] == "move" and ev["actor"] and json.loads(ev["payload"]).get("from"):
            out["agents"][ev["actor"]]["origin"] = json.loads(ev["payload"])["from"]
        return out
    deep_note = {}
    for _i in range(5000):
        deep_note = {"n": deep_note}
    fold.project = from_read
    try:
        led = _led()
        _a, why_named, got_named, _c = _one(led, dict(move, payload={"to": "the ridge", "from": "the ford",
                                                                     "note": "x", "injuries": [1]}))
        led2 = _led()
        applied2, why_deep, got_deep, crashed2 = _one(led2, dict(move, payload={"to": "the ridge", "from": "the ford",
                                                                                "note": deep_note}))
    finally:
        fold.project = real_project
    # ...a read that two left-out keys make only TOGETHER is caught by the report as given, whole

    def x_with_y(snap, ev):
        out = real_project(snap, ev)
        pl = json.loads(ev["payload"])
        if ev["type"] == "move" and ev["actor"] and "y" in pl and pl.get("x"):
            out["agents"][ev["actor"]]["xy"] = pl["x"]
        return out
    fold.project = x_with_y
    try:
        led3 = _led()
        applied3, why_xy, got_xy, crashed3 = _one(led3, dict(move, payload={"to": "the ridge", "x": "1", "y": "2"}))
    finally:
        fold.project = real_project
    check("...a-read-two-left-out-keys-make-only-together-refuses-naming-both", not crashed3 and not applied3
          and got_xy == "KEEPER_TABLE_STALE" and "x, y" in (why_xy or "") and not _events(led3), why_xy)
    # ...and an id is named when removing it CURES a raise: a move whose actor is a list raises; its junk target, which
    # a move never reads, is not named beside it
    led4 = _led()
    applied4, why_cure, got_cure, crashed4 = _one(led4, dict(move, actor=["maren"], target=5))
    check("an-id-named-because-removing-it-cures-the-raise,-not-its-unread-neighbour", not crashed4 and not applied4
          and got_cure == "KEEPER_REPORT_FIELD_TYPE" and (why_cure or "").split("]", 1)[-1].strip().startswith("actor:")
          and "together" not in (why_cure or "") and not _events(led4), why_cure)
    check("KEEPER_TABLE_STALE-names-only-the-key-the-fold-reads", got_named == "KEEPER_TABLE_STALE"
          and (why_named or "").split("]", 1)[-1].strip().startswith("from: "), why_named)
    check("...and-an-unread-key-nested-too-deep-exempts-only-itself,-not-its-neighbour",
          not crashed2 and not applied2 and got_deep == "KEEPER_TABLE_STALE" and "from" in (why_deep or "")
          and "note" not in (why_deep or "") and not _events(led2), why_deep)
    # ...and a projection that RAISES on a left-out key has read it: refused as a stale table, what it raised named

    def int_of_n(snap, ev):
        if ev["type"] == "move" and "n" in json.loads(ev["payload"]):
            int(json.loads(ev["payload"])["n"])
        return real_project(snap, ev)
    fold.project = int_of_n
    try:
        led = _led()
        applied, why, got, crashed = _one(led, dict(move, payload={"to": "the ridge", "n": "many"}))
    finally:
        fold.project = real_project
    check("a-projection-that-raises-on-a-left-out-key-refuses-KEEPER_TABLE_STALE,-naming-what-it-raised",
          not crashed and not applied and got == "KEEPER_TABLE_STALE" and "projecting it raised ValueError" in why
          and not _events(led), why)
    # what HEAD REFUSED is refused still - now by the code that names it
    for name, p, code in (
            ("a-list-actor-on-a-move", dict(move, actor=["maren"]), "KEEPER_REPORT_FIELD_TYPE"),
            ("a-list-type", dict(move, type=["move"]), "WORLD_EVENT_TYPE_UNKNOWN"),
            ("a-number-in-a-reveal's-to", {"turn": 1, "type": "reveal", "actor": "maren",
                                           "payload": {"fact": "the fever", "to": [5]}}, "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("a-null-to-on-a-move", dict(move, payload={"to": None}), "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("dimensions-that-are-a-list", {"turn": 1, "type": "threaten", "actor": "maren",
                                            "payload": {"dimensions": ["threat"]}}, "WORLD_EVENT_PAYLOAD_VALUE_TYPE"),
            ("a-blank-actor-on-a-move-(no-one-moves)", dict(move, actor=""), "KEEPER_NOT_A_WORLD_EVENT"),
            ("a-type-that-names-no-world-type", dict(move, type="walk"), "WORLD_EVENT_TYPE_UNKNOWN"),
            ("a-text-heat-(the-keeper's-own-type-check-refuses-it-before-the-fold's)",
             dict(delta, payload={"id": "the-levy", "heat": "hot"}), "WORLD_EVENT_PAYLOAD_VALUE_TYPE")):
        _refused("HEAD-refused-%s-too" % name, p, code)
    # what HEAD accepted and nothing above names: still accepted, the same rows
    for name, p, row in (
            ("an-integral-float-turn", dict(move, turn=1.0), ("move", "maren", None, None, {"to": "the ridge"})),
            ("a-null-payload-on-a-bond", {"turn": 1, "type": "bond", "actor": "maren", "target": "edda", "payload": None},
             ("bond", "maren", "edda", None, {})),
            ("an-empty-list-payload-on-a-bond", {"turn": 1, "type": "bond", "actor": "maren", "target": "edda",
                                                 "payload": []}, ("bond", "maren", "edda", None, {})),
            ("an-actor-no-cast-holds", dict(move, actor="a_stranger"), ("move", "a_stranger", None, None, {"to": "the ridge"})),
            ("a-true-terminal", {"turn": 1, "type": "harm", "actor": "maren", "target": "edda", "payload": {"terminal": True}},
             ("harm", "maren", "edda", None, {"terminal": True})),
            ("a-text-target-on-a-move,-which-the-fold-never-reads", dict(move, target="edda"),
             ("move", "maren", "edda", None, {"to": "the ridge"})),
            ("a-keeper-tension-seed", {"turn": 1, "type": "tension", "payload": dict(SEED, id="the-weir")},
             ("tension", None, None, None, dict(SEED, id="the-weir")))):
        led = _led()
        applied, why, _c, crashed = _one(led, p)
        check("still-applied:-%s" % name, not crashed and len(applied) == 1 and _events(led) == [row],
              (why, _events(led)))
    # JUNK IN AN ID THE FOLD NEVER READS for the type: written as null and named, never the reason for a refusal
    for name, p, field in (("a-move's-number-target", dict(move, target=5), "target"),
                           ("a-move's-true-location", dict(move, location=True), "location"),
                           ("a-move's-list-location", dict(move, location=["mill"]), "location"),
                           ("a-destroy-asset's-number-actor",
                            {"turn": 1, "type": "destroy-asset", "actor": 5, "payload": {"asset": "the barn"}}, "actor"),
                           ("a-seize's-blank-location",
                            {"turn": 1, "type": "seize", "actor": "maren", "location": "", "payload": {"asset": "x"}},
                            "location")):
        led = _led()
        applied, why, _c, crashed = _one(led, p)
        rows = _events(led)
        col = {"actor": 1, "target": 2, "location": 3}[field]
        check("junk-in-%s-is-written-as-null-and-named" % name, not crashed and len(applied) == 1 and rows
              and rows[0][col] is None and field in (applied[0].get("extra") or ()) and applied[0][field] is None,
              (why, rows, applied))
    # THE PAYLOAD KEEPS WHAT THE FOLD READS: the stray keys a type-blind reader took as the beat's own
    led = _led()
    stray = {"to": "the ridge", "injuries": [{"who": "edda", "quote": SAID, "severity": "grave"}],
             "transfers": [{"what": "the key", "from": "maren", "to": "edda"}], "told": [{"what": "the secret", "to": "edda"}],
             "subject_group": "the millers", "why.not": 1}
    applied, why, _c, _x = _one(led, dict(move, payload=stray, reason="she left", confidence=0.9))
    check("a-move-with-stray-keys-is-APPLIED", len(applied) == 1, why)
    check("...its-event-carries-only-what-the-fold-reads", _events(led) == [("move", "maren", None, None, {"to": "the ridge"})],
          _events(led))
    check("...each-stray-key-named,-the-payload's-by-path", applied and applied[0].get("extra") == (
        "confidence", 'payload."why.not"', "payload.injuries", "payload.subject_group", "payload.told",
        "payload.transfers", "reason"), applied and applied[0].get("extra"))
    check("...and-the-applied-report-echoes-what-was-written", applied and applied[0]["payload"] == {"to": "the ridge"})
    check("...the-injury-reader-finds-no-injury-in-it", injuries.run_rows(led.con, "r1") == [], injuries.run_rows(led.con, "r1"))
    check("...the-scene-facts-reader-finds-no-transfer-or-telling", scene_facts.run_rows(led.con, "r1") == [],
          scene_facts.run_rows(led.con, "r1"))
    led = _led()
    applied, why, _c, _x = _one(led, move)
    check("a-plain-move-carries-no-extra", applied and "extra" not in applied[0], applied)
    # A SEVERITY WORD IN A KEY THE TYPE NEVER READS is left out and named - an off-ladder one refused at HEAD
    for name, pl, named in (("a-good-dimensions-word", {"to": "the ridge", "dimensions": {"threat": "marked"}},
                             "payload.dimensions"),
                            ("an-off-ladder-dimensions-word", {"to": "the ridge", "dimensions": {"threat": "zzz"}},
                             "payload.dimensions"),
                            ("an-off-ladder-temperature", {"to": "the ridge", "temperature": "loud"}, "payload.temperature")):
        led = _led()
        applied, why, _c, _x = _one(led, dict(move, payload=pl))
        check("a-move's-%s-is-left-out-and-named,-never-the-reason-it-is-refused" % name, applied
              and applied[0].get("extra") == (named,) and _events(led)[0][4] == {"to": "the ridge"}, (why, _events(led)))
    led = _led(tension=True)
    applied, why, _c, _x = _one(led, {"turn": 1, "type": "threaten", "actor": "maren",
                                      "payload": {"dimensions": {"threat": "zzz"}}})
    check("where-the-fold-reads-the-word,-an-off-ladder-one-still-refuses", not applied
          and _coded(why) == "SEVERITY_WORD_UNKNOWN", why)
    led = _led(tension=True)
    applied, why, _c, _x = _one(led, {"turn": 1, "type": "threaten", "actor": "maren",
                                      "payload": {"dimensions": {"threat": "marked", "loudness": "severe"}, "note": "x"}})
    check("a-threat-keeps-the-seven-dimensions,-names-the-rest", applied and applied[0].get("extra") == (
        "payload.dimensions.loudness", "payload.note") and _events(led)[-1][4] == {"dimensions": {"threat": 0.6}},
        (why, _events(led)))
    led = _led(tension=True)
    applied, why, _c, _x = _one(led, {"turn": 1, "type": "threaten", "actor": "maren",
                                      "payload": {"dimensions": {"threat": "marked", "loudness": "zzz"}}})
    check("an-off-ladder-word-in-a-dimension-the-seven-do-not-name-is-left-out,-not-a-refusal-(declared)", applied
          and applied[0].get("extra") == ("payload.dimensions.loudness",), (why, applied))
    for name, pl, want, named in (
            ("a-delta-keeps-id-and-heat", {"id": "the-levy", "heat": 0.1, "temperature": "loud", "note": "x"},
             {"id": "the-levy", "heat": 0.1}, ("payload.note", "payload.temperature")),
            ("a-seed-keeps-its-structure,-not-a-heat", dict(SEED, id="the-weir", heat=0.2), dict(SEED, id="the-weir"),
             ("payload.heat",))):
        led = _led(tension=True)
        applied, why, _c, _x = _one(led, {"turn": 1, "type": "tension", "payload": pl})
        check("%s,-per-form,-naming-the-rest" % name, applied and applied[0].get("extra") == named
              and _events(led)[-1][4] == want, (why, _events(led)))
    led = _led()
    applied, why, _c, _x = _one(led, dict(move, speaker="maren", said=SAID))
    check("a-mixed-report-is-a-world-change-as-at-HEAD,-its-claim-keys-named",
          applied and applied[0].get("extra") == ("said", "speaker"), (why, applied))
    led = _led()
    applied, _w, _c, _x = _one(led, dict(move, payload={"to": "the ridge", "note": "x"}), dry_run=True)
    check("a-dry-run-writes-nothing-and-still-names", applied and applied[0].get("extra") == ("payload.note",)
          and not _events(led), (applied, _events(led)))
    # every reason opens with a registered code, HEAD's words kept
    led = _led(tension=True)
    _a, rejected = keeper.apply_proposals(led, "r1", [
        dict(move, turn=99), {"turn": 1, "type": "walk", "payload": {}}, dict(move, payload={}),
        dict(move, payload={"to": ""}), {"turn": 1, "type": "tension", "payload": {"id": "no-such", "heat": 0.1}},
        {"turn": 1, "type": "tension", "payload": dict(SEED, id="the-weir", watches=["maren"])},
        {"turn": 0, "type": "move", "actor": "edda", "payload": {"to": None}}, move, move])
    reasons = [w for _p, w in rejected]
    check("every-refusal-opens-with-a-registered-code", reasons and all(_coded(w) for w in reasons),
          [w[:60] for w in reasons if not _coded(w)])
    check("...the-words-of-HEAD's-reasons-kept", any("invention" in w for w in reasons)
          and any("names no live tension" in w for w in reasons) and any("could not judge" in w for w in reasons)
          and any("would not change the snapshot" in w for w in reasons), [w[:70] for w in reasons])
    led = _led()
    applied, why, got, crashed = _one(led, {"turn": 1, "type": "tension", "payload": dict(SEED, id="the-weir",
                                                                                          cooling=["slow"])})
    check("a-seed's-cooling-that-is-a-list-is-refused-by-the-chassis's-own-code,-not-a-TypeError",
          not crashed and not applied and got == "TENSION_COOLING_UNKNOWN", why)
    try:
        world_events.validate_payload("move", {"to": "the ridge", "note": NAN})
        nan_code = None
    except world_events.WorldEventError as e:
        nan_code = e.code
    check("validate_payload-refuses-a-NaN-anywhere-(for-a-caller-that-does-not-strip-first)",
          nan_code == "WORLD_EVENT_PAYLOAD_VALUE_TYPE", nan_code)
    # an uncoded error, out of the fold or out of the write, refuses its one report and never crashes the pass
    for name, target, context in (("the-fold", "would_change", "could not judge it: TypeError"),
                                  ("the-write", "append", "the log refused the write: OperationalError")):
        led = _led()
        real = getattr(world_events, target)

        def boom(*_a, **_k):
            import sqlite3
            raise (TypeError("injected") if target == "would_change" else sqlite3.OperationalError("injected"))
        setattr(world_events, target, boom)
        try:
            applied, why, got, crashed = _one(led, move)
        finally:
            setattr(world_events, target, real)
        check("an-uncoded-error-out-of-%s-refuses-as-KEEPER_UNCODED_ERROR,-its-type-named" % name,
              not crashed and not applied and got == "KEEPER_UNCODED_ERROR" and context in why and not _events(led), why)


# ---- [3] ---------------------------------------------------------------------------------------------------------

def claims_and_rulings():
    print("[3] a claim and a ruling")
    base = {"turn": 1, "speaker": "maren", "said": SAID}
    for name, r, code in (
            ("a-number-speaker", dict(base, speaker=5), "KEEPER_REPORT_FIELD_TYPE"),
            ("a-lone-surrogate-speaker", dict(base, speaker=LONE), "KEEPER_REPORT_FIELD_TYPE"),
            ("a-list-said", dict(base, said=[SAID]), "KEEPER_REPORT_FIELD_TYPE"),
            ("a-lone-surrogate-said", dict(base, said=LONE), "KEEPER_REPORT_FIELD_TYPE"),
            ("a-list-subject", dict(base, extracts=[{"subject": ["mill"], "predicate": "is", "object": "hers"}]),
             "KEEPER_REPORT_FIELD_TYPE"),
            ("a-true-predicate", dict(base, extracts=[{"subject": "mill", "predicate": True}]), "KEEPER_REPORT_FIELD_TYPE"),
            ("a-null-subject", dict(base, extracts=[{"subject": None, "predicate": "is"}]), "CLAIM_EXTRACT_INCOMPLETE"),
            ("a-subject-of-punctuation-alone", dict(base, extracts=[{"subject": "!!!", "predicate": "is"}]),
             "CLAIM_EXTRACT_INCOMPLETE"),
            ("a-subject-in-a-script-the-index-drops", dict(base, extracts=[{"subject": "мельница",
                                                                            "predicate": "is"}]), "CLAIM_EXTRACT_INCOMPLETE"),
            ("extracts-a-map", dict(base, extracts={"subject": "mill"}), "KEEPER_REPORT_FIELD_TYPE"),
            ("an-extract-that-is-text", dict(base, extracts=["mill is hers"]), "KEEPER_REPORT_FIELD_TYPE"),
            ("a-list-turn", dict(base, turn=[1]), "KEEPER_TURN_UNKNOWN"),
            ("a-true-turn", dict(base, turn=True), "KEEPER_TURN_UNKNOWN"),
            ("a-false-turn", dict(base, turn=False), "KEEPER_TURN_UNKNOWN"),
            ("a-zero-speaker", dict(base, speaker=0), "CLAIM_SPEAKER_EMPTY"),
            ("a-blank-said", dict(base, said="  "), "CLAIM_SAID_EMPTY")):
        led = _led()
        try:
            rec, rej = keeper.record_utterances(led, "r1", [r])
            crashed = None
        except Exception as e:                                   # noqa: BLE001
            rec, rej, crashed = [], [], e
        got = _coded(rej[0][1]) if rej else None
        n = led.con.execute("SELECT COUNT(*) FROM utterances").fetchone()[0]
        check("a-claim-with-%s-refused-%s,-nothing-written" % (name, code), crashed is None and not rec
              and got == code and n == 0, (crashed, rej and rej[0][1][:90], n))
    led = _led()
    rec, rej = keeper.record_utterances(led, "r1", [dict(base, confidence=1, extracts=[
        {"subject": "mill", "predicate": "belongs to", "object": None, "note": "x"},
        {"subject": "ford", "predicate": "is", "object": 5}, {"subject": "weir", "predicate": "is", "object": LONE},
        {"subject": "maren", "predicate": "keeps", "object": "mill"}])])
    rows = [tuple(x) for x in led.con.execute("SELECT subject, predicate, object FROM claim_extracts ORDER BY ord_no")]
    check("a-null-or-number-object-is-written-as-empty,-not-'none'-or-'5';-text-normalised-as-at-HEAD",
          rows == [("mill", "belongs-to", ""), ("ford", "is", ""), ("weir", "is", "x"), ("maren", "keeps", "mill")], rows)
    check("...the-claim-recorded-naming-it-and-the-extras", rec and rec[0].get("extra") == (
        "confidence", "extracts[].note", "extracts[].object"), rec and rec[0].get("extra"))
    # AN EXTRACT IS STORED NORMALISED (a-z, 0-9, hyphens), so a lone surrogate in one never reaches the table: text is
    # enough there, and HEAD recorded such a claim correctly (the second review) - it still does, nothing named
    led = _led()
    rec, rej = keeper.record_utterances(led, "r1", [dict(base, extracts=[{"subject": "mill\ud800", "predicate": "is",
                                                                          "object": "old\ud800"}])])
    rows = [tuple(x) for x in led.con.execute("SELECT subject, predicate, object FROM claim_extracts")]
    check("a-lone-surrogate-in-an-extract-is-recorded-normalised-as-at-HEAD,-nothing-named",
          rec and "extra" not in rec[0] and rows == [("mill", "is", "old")], (rec, rej, rows))
    led = _led()
    rec, _r = keeper.record_utterances(led, "r1", [dict(base, extracts=[{"subject": "mill", "predicate": "is"},
                                                                        {"subject": "mill", "predicate": "is", "object": "old"}])])
    check("a-plain-claim-carries-no-extra-and-is-written-as-at-HEAD", rec and "extra" not in rec[0] and [
        tuple(x) for x in led.con.execute("SELECT subject, predicate, object FROM claim_extracts ORDER BY ord_no")] == [
        ("mill", "is", ""), ("mill", "is", "old")], rec)
    # ROUTED BY WORLD TYPE: a claim labelled with its kind is the claim it is (HEAD refused it as a world change)
    changes, said, neither = keeper._route([
        dict(base, type="claim"), dict(base, type="move", payload={"to": "x"}),
        dict(base, type=" Move", payload={"to": "x"}), {"turn": 1, "type": "walk"}, {"turn": 1, "note": "x"}, dict(base), dict(base, type="claim", said=""),
        dict(base, type="killed", actor="maren", target="edda", payload={"terminal": True}),
        dict(base, type="moved", payload={"to": "x"}), dict(base, type="move\u200b", actor="maren"),
        dict(base, actor="maren", payload={"to": "x"}), dict(base, type=" Seize")])
    check("routing:-'claim'-and-a-said-are-claims;-a-world-type-give-or-take-case,-or-a-type-with-a-change's-fields,"
          "-is-a-change;-with-no-type-a-said-is-a-claim-as-at-HEAD;-neither-is-counted",
          [p.get("type") for p in changes] == ["move", " Move", "walk", "killed", "moved", "move\u200b", " Seize"]
          and [p.get("type") for p in said] == ["claim", None, "claim", None] and neither == 1, (changes, said, neither))
    led = _led()
    applied, rejected = keeper.apply_proposals(led, "r1", [dict(base, type="Move", actor="maren", payload={"to": "x"})])
    check("...a-mis-cased-world-type-is-refused-by-its-type,-as-at-HEAD", not applied and rejected
          and _coded(rejected[0][1]) == "WORLD_EVENT_TYPE_UNKNOWN", rejected)
    applied, rejected = keeper.apply_proposals(led, "r1", [dict(base, type="killed", actor="maren", target="edda",
                                                                payload={"terminal": True})])
    check("...a-death-typed-'killed'-with-a-said-is-refused-by-its-type-as-at-HEAD,-never-a-claim-(third-review)",
          not applied and rejected and _coded(rejected[0][1]) == "WORLD_EVENT_TYPE_UNKNOWN", rejected)
    # A CHANGE FIELD COUNTS ONLY WHEN IT CARRIES SOMETHING (fourth review): a labelled claim in a shape shared with
    # world changes - `"target": null` - stays a claim; one that carries a place or an actor is a change, as at HEAD
    changes, said, _n = keeper._route([
        dict(base, type="claim", target=None), dict(base, type="claim", payload=None, actor=None, target=None),
        dict(base, type="claim", payload={}), dict(base, type="claim", actor=" "),
        dict(base, type="claim", location="the millhouse"), dict(base, type="claim", actor="maren")])
    check("...a-null-or-empty-change-field-carries-nothing:-the-claim-is-a-claim;-a-place-or-an-actor-is-a-change",
          len(said) == 4 and [c.get("location") or c.get("actor") for c in changes] == ["the millhouse", "maren"],
          (said, changes))
    rec, rej = keeper.record_utterances(led, "r1", [dict(base, type="claim", said="")])
    check("...a-claim-typed-'claim'-with-an-empty-said-is-refused-as-a-claim,-CLAIM_SAID_EMPTY",
          not rec and rej and _coded(rej[0][1]) == "CLAIM_SAID_EMPTY", rej)
    led = _led()
    rec, rej = keeper.record_utterances(led, "r1", [dict(base, type="claim")])
    check("...and-is-recorded,-its-type-named-as-nothing-read", rec and rec[0].get("extra") == ("type",)
          and keeper._label(rec[0]) == "t1 claim by maren", (rec, rej))
    # rulings
    led = _led()
    uid = claims.record(led.con, "r1", 1, "maren", SAID, [])
    uid2 = claims.record(led.con, "r1", 1, "edda", "the mill is old", [])
    applied, left, rejected = keeper.apply_rulings(led, "r1", [
        {"utterance_id": uid, "verdict": "established", "rationale": ["because"], "why": ARROW},
        {"utterance_id": uid2, "verdict": "superposed", "confidence": 1},
        {"utterance_id": True, "verdict": "fiction"}, {"utterance_id": str(uid), "verdict": "fiction"},
        {"utterance_id": uid2, "verdict": "maybe"}, {"utterance_id": uid2, "verdict": ["established"]}], at_turn=2)
    res = [tuple(x) for x in led.con.execute("SELECT utterance_id, verdict, rationale FROM claim_resolutions")]
    check("a-list-rationale-is-written-as-empty,-not-its-string", res == [(uid, "established", "")], res)
    check("...the-ruling-applied-naming-it-and-the-extra", applied and applied[0].get("extra") == ("rationale", "why"),
          applied)
    check("a-LEFT-ruling-names-its-extra-too", left and left[0].get("extra") == ("confidence",), left)
    check("the-bad-rulings-refused-by-code", [_coded(w) for _r, w in rejected] == [
        "KEEPER_RULING_UNKNOWN", "KEEPER_RULING_UNKNOWN", "KEEPER_VERDICT_UNKNOWN", "KEEPER_VERDICT_UNKNOWN"],
        [w[:60] for _r, w in rejected])
    led = _led()
    uid = claims.record(led.con, "r1", 1, "maren", SAID, [])
    applied, _l, _rj = keeper.apply_rulings(led, "r1", [{"utterance_id": uid, "verdict": "fiction", "rationale": 0},
                                                         {"utterance_id": uid, "verdict": "fiction", "rationale": "a lie"},
                                                         {"utterance_id": uid, "verdict": "fiction", "rationale": LONE}],
                                            at_turn=2)
    res = [tuple(x) for x in led.con.execute("SELECT rationale FROM claim_resolutions")]
    check("a-falsy-rationale-was-empty-at-HEAD-too,-so-not-named;-text-kept;-unstorable-text-empty-and-named",
          res == [("",), ("a lie",), ("",)] and [a.get("extra") for a in applied] == [None, None, ("rationale",)],
          (res, applied))
    _a, _l, rejected = keeper.apply_rulings(led, "r1", [{"utterance_id": uid, "verdict": "established"}], at_turn=1)
    check("a-backdated-ruling-refused-by-its-own-code", rejected and _coded(rejected[0][1]) == "CLAIM_RESOLUTION_BACKDATED",
          rejected)


# ---- [4] ---------------------------------------------------------------------------------------------------------

def unreadable_replies():
    print("[4] what the keeper cannot read is named, never refused")
    deep = "[" * 3000 + "]" * 3000
    for raw, want, notes_want in (
            ("I find nothing to report.", [], ["no JSON list"]), ("", [], ["no JSON list"]),
            ("[not json", [], ["never closes"]), ('[{"turn": 1,}]', [], ["not JSON"]),
            ('Note [1]: [{"utterance_id": 1}]', [], ["1 of its 1 entries are not objects", "went on after"]),
            ('[1, "x", {"utterance_id": 1}]', [{"utterance_id": 1}], ["2 of its 3 entries are not objects"]),
            ('[] and then [{"utterance_id": 1}]', [], ["went on after"]),
            ('[{"a": 1}] then [{"b": 2}]', [{"a": 1}], ["went on after"]),
            ('[{"a": 1}] {"x": 1}', [{"a": 1}], ["went on after"]),
            ('[{"said": "the key ] was hers"}]', [{"said": "the key ] was hers"}], []),
            ('[{"said": "she wrote [x"}]', [{"said": "she wrote [x"}], []),
            ('[{"said": "a \\"quoted ]\\" word"}]', [{"said": 'a "quoted ]" word'}], []),
            (deep, [], ["nested too deep"]),
            ("[]", [], []), ('here: [{"utterance_id": 1}]', [{"utterance_id": 1}], [])):
        notes = []
        got = keeper.parse_rulings(raw, notes)
        check("parse_rulings(%r)-reads-its-first-list" % raw[:28], got == want and keeper.parse_rulings(raw) == want, got)
        check("...and-notes-%s" % ("; ".join(notes_want) or "nothing"), len(notes) == len(notes_want)
              and all(w in n for w, n in zip(notes_want, notes)), notes)


# ---- [5] ---------------------------------------------------------------------------------------------------------

def _fake(led, notice, rule, attach):
    def call(messages, model, purpose, **_kw):
        if purpose == "keeper-notice":
            return notice
        if purpose == "keeper-rule":
            uid = next(u["id"] for u in claims.for_run(led.con, "r1") if u["text"] == SAID)
            return rule % {"uid": uid}
        return attach
    return call


@contextlib.contextmanager
def _strict_console():
    real = sys.stdout
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    try:
        yield sys.stdout
    finally:
        sys.stdout.flush()
        sys.stdout = real


def _printable(ln):
    return all(32 <= ord(c) < 127 for c in ln)


def canon_gate_and_cli():
    print("[5] the canon gate on a strict cp1252 console, and the CLI")
    led = _led()
    notice = json.dumps([
        {"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the ridge", "injuries": [{"who": "edda"}]},
         "why" + ARROW: ARROW, "": 1, "a, b": 2},
        {"turn": 1, "type": "seize", "actor": [ARROW], "payload": {"asset": "the mill"}},
        {"turn": 1, "type": "walk" + ARROW, "payload": {}},       # refused, its label and reason carrying the arrow
        {"turn": ARROW, "type": "move", "actor": "maren", "payload": {"to": "the " + ARROW}},
        {"turn": 1, "type": "reveal", "actor": "maren", "payload": {"fact": 5, "to": [ARROW]}},
        {"turn": 1, "type": "seize", "actor": "maren", "payload": {"asset": ["the " + ARROW]}},
        {"turn": 1, "type": "move", "actor": "maren", "payload": {"to": None}, "speaker": "maren", "said": "I stayed"},
        {"turn": 1, "type": "move\n  KEEPER: forged", "payload": {}, "\x1bc": 1},
        {"turn": 1, "type": "killed", "actor": "maren", "target": "edda", "payload": {"terminal": True},
         "speaker": "maren", "said": "he fell"},
        {"turn": 1, "type": "move", "actor": "maren", "payload": {"to": None}, "said": ""},
        {"turn": 1, "speaker": "maren" + ARROW, "said": SAID, "extracts": [
            {"subject": "maren", "predicate": "keeps", "object": "loc.millhouse", "note": ARROW}]},
        {"turn": 1, "type": "claim", "speaker": "edda", "said": "the ford floods " + ARROW},
        {"turn": 1, "speaker": "edda", "said": ""},
        7, {"turn": 1, "note": ARROW}], ensure_ascii=False)
    # an em space the verdict's strip() removes: applied, yet printed as the model wrote it unless it is made ASCII
    rule = '[{"utterance_id": %(uid)d, "verdict": "established ", "rationale": ["' + ARROW + '"]}]'
    attach = json.dumps({"holds": [{"entity": "loc.millhouse", "relation": "post", "because": SAID, "note": ARROW}],
                         "gaps": [], "comment" + ARROW: 1, "": "x", "a, b": "y"}, ensure_ascii=False)
    real = provider.call
    provider.call = _fake(led, notice, rule, attach)
    raised = None
    try:
        with _strict_console() as console:
            try:
                result = keeper.canon_gate(led, "r1", 0, 2, "fake-model", False, world=WORLD)
            except Exception as e:                               # noqa: BLE001
                raised, result = e, None
            console.flush()
            text = console.buffer.getvalue().decode("cp1252")
    finally:
        provider.call = real
    check("the-canon-gate-completes-on-a-strict-cp1252-console-with-arrows-everywhere", raised is None, repr(raised))
    if result is None:
        return
    lines = text.splitlines()
    check("...every-line-it-printed-is-printable-ASCII-(no-raw-newline,-no-ESC,-no-arrow)",
          all(_printable(ln) for ln in lines) and not any(ln.startswith("  KEEPER: forged") for ln in lines),
          [ln for ln in lines if not _printable(ln)] or [ln for ln in lines if "forged" in ln])
    noticed = result["noticed"]
    check("the-noticing-pass-applied-the-move-and-recorded-both-claims", len(noticed["applied"]) == 1
          and len(noticed["recorded"]) == 2, noticed)
    check("...printed-its-refusals-with-their-codes", any("refused: t1 seize: [KEEPER_REPORT_FIELD_TYPE]" in ln
          for ln in lines) and any("refused: t1 walk\\u2192: [WORLD_EVENT_TYPE_UNKNOWN]" in ln and "\\u2192'" in ln
          for ln in lines) and any("refused: t1 killed: [WORLD_EVENT_TYPE_UNKNOWN]" in ln for ln in lines), lines)
    check("...named-what-the-move-and-the-claims-carried,-by-what-became-of-it,-an-empty-name-and-one-holding-',-'"
          "-quoted", any(ln == '    t1 move carried what nothing reads: "", "a, b", why\\u2192' for ln in lines)
          and any(ln == "    t1 move left out of the event (no world rule reads it): payload.injuries" for ln in lines)
          and any("t1 claim by maren\\u2192 carried what nothing reads: extracts[].note" in ln for ln in lines)
          and any("t1 claim by edda carried what nothing reads: type" in ln for ln in lines), lines)
    check("...and-refused-the-claim-with-an-empty-said-as-a-claim", any(
        "refused: t1 claim by edda: [CLAIM_SAID_EMPTY]" in ln for ln in lines), [ln for ln in lines if "edda" in ln])
    check("...and-what-of-the-reply-it-could-not-read,-and-the-claims-refused-changes-carried", noticed["notes"] == [
        "1 of its 15 entries are not objects",
        "1 of its reports are neither a world change (no type) nor a claim (no said)",
        "t1 move also carried a claim (said), not recorded", "t1 killed also carried a claim (said), not recorded"],
        noticed["notes"])
    check("the-ruling-pass-named-the-rationale", result["ruled"]["applied"] and result["ruled"]["applied"][0].get(
        "extra") == ("rationale",), result["ruled"])
    att = result["attached"]
    check("the-attach-pass-priced-the-hold-and-named-its-reply's-extras", len(att["attached"]) == 1 and att["unread"]
          and set(att["unread"][0][2]) == {"", "a, b", "comment" + ARROW, "holds[].note"}, att)
    check("...printed-as-ASCII,-an-empty-name-and-one-holding-',-'-quoted", any(
        'maren\\u2192 loc.millhouse carried what nothing reads: "", "a, b", comment\\u2192, holds[].note' in ln
        for ln in lines), [ln for ln in lines if "carried" in ln])
    # an attach reply nested past the reader's depth is refused as no object, never a crash
    led2 = _led()
    uid = claims.record(led2.con, "r1", 1, "maren", SAID, [{"subject": "maren", "predicate": "keeps",
                                                            "object": "loc.millhouse"}])
    provider.call = lambda *a, **k: '{"a":' * 3000 + "1" + "}" * 3000     # nested JSON, past json's own depth
    try:
        out = keeper.attach_scene(led2, "r1", [{"utterance_id": uid, "verdict": "established"}], 0, 2, WORLD,
                                  "fake-model", False, log=lambda *_a: None)
        crashed = None
    except Exception as e:                                       # noqa: BLE001
        out, crashed = None, e
    finally:
        provider.call = real
    check("an-attach-reply-nested-too-deep-is-refused-as-no-object,-never-a-crash", crashed is None and out
          and out["refused"] and out["refused"][0][2] == "COMPOSITION_ATTACH_REPLY_NOT_AN_OBJECT", (crashed, out))
    real_price = keeper.attach_price
    provider.call = lambda *a, **k: attach
    keeper.attach_price = lambda *a, **k: (_ for _ in ()).throw(TypeError("injected"))
    said_lines = []
    try:
        out = keeper.attach_scene(led2, "r1", [{"utterance_id": uid, "verdict": "established"}], 0, 2, WORLD,
                                  "fake-model", False, log=said_lines.append)
        crashed = None
    except Exception as e:                                       # noqa: BLE001
        out, crashed = None, e
    finally:
        provider.call, keeper.attach_price = real, real_price
    check("an-uncoded-error-pricing-a-candidate-refuses-it-as-KEEPER_UNCODED_ERROR,-its-type-and-message-named",
          crashed is None and out and out["refused"] == [("maren", "loc.millhouse", "KEEPER_UNCODED_ERROR")]
          and any("KEEPER_UNCODED_ERROR (TypeError: injected)" in ln for ln in said_lines), (crashed, out, said_lines))
    provider.call = lambda *a, **k: json.dumps({"holds": [{"entity": "loc.nowhere", "relation": "post", "because": SAID}],
                                                "gaps": [], "comment": 1})
    try:
        out = keeper.attach_scene(led2, "r1", [{"utterance_id": uid, "verdict": "established"}], 0, 2, WORLD,
                                  "fake-model", False, log=lambda *_a: None)
    finally:
        provider.call = real
    check("a-REFUSED-attach-reply-names-nothing-it-carried", out and out["refused"] and out["unread"] == [], out)
    # the CLI: a file of reports routed and read the way the pass reads a reply
    led3 = _led()
    path = os.path.join(TMP, "cli.db")
    led3.con.execute("VACUUM INTO ?", (path,))
    prop = os.path.join(TMP, "props.json")
    with open(prop, "w", encoding="utf-8") as fh:
        json.dump([{"turn": 1, "type": "move", "actor": "maren", "payload": {"to": "the ridge", "note": ARROW},
                    "speaker": "maren", "said": "I went up"},
                   "not an object", {"turn": 1, "type": "seize", "actor": 5, "payload": {"asset": "x"}},
                   {"turn": 1, "note": 1},
                   {"turn": 1, "type": "move", "actor": "maren", "payload": {"to": None}, "speaker": "maren",
                    "said": "I stayed"}], fh)
    rulings = os.path.join(TMP, "rulings.json")
    with open(rulings, "w", encoding="utf-8") as fh:
        json.dump({"utterance_id": 1}, fh)
    prose = os.path.join(TMP, "prose.json")
    with open(prose, "w", encoding="utf-8") as fh:
        fh.write('here are the reports: [{"turn": 1}]')
    deep_file = os.path.join(TMP, "deep.json")
    with open(deep_file, "w", encoding="utf-8") as fh:
        fh.write("[" * 3000 + "]" * 3000)
    for name, argv, want, unwanted in (
            ("--propose-dry-run", ["--propose", prop, "--dry-run"],
             ("(dry run, nothing written) left out of the event (no world rule reads it): payload.note",), ()),
            ("--propose", ["--propose", prop],
             ("applied 1 of 3", "1 of its 5 entries are not objects", "1 of its reports are neither",
              "[KEEPER_REPORT_FIELD_TYPE]", "t1 move carried what nothing reads: said, speaker",
              "t1 move left out of the event (no world rule reads it): payload.note",
              "unread: t1 move also carried a claim (said), not recorded"),
             ("recorded 1 of",)),
            ("--rule-a-map", ["--rule", "--rulings", rulings], ("[KEEPER_REPLY_NOT_A_LIST]",), ()),
            ("--propose-a-file-that-is-not-JSON", ["--propose", prose], ("[KEEPER_REPLY_NOT_A_LIST]", "not JSON"),
             ("Traceback",)),
            ("--rule-a-file-nested-too-deep", ["--rule", "--rulings", deep_file],
             ("[KEEPER_REPLY_NOT_A_LIST]", "nested too deep"), ("Traceback",))):
        argv0 = sys.argv
        sys.argv = ["keeper.py", "--vault", TMP, "--run", "r1", "--db", path] + argv
        try:
            with _strict_console() as console:
                try:
                    keeper.main()
                    out = ""
                except SystemExit as e:
                    out = str(e)
                console.flush()
                out = console.buffer.getvalue().decode("cp1252") + out
        except Exception as e:                                   # noqa: BLE001
            out = "RAISED %r" % e
        finally:
            sys.argv = argv0
        check("the-CLI-%s-routes-and-reads-the-file-as-the-pass-reads-a-reply" % name,
              all(w in out for w in want) and not any(u in out for u in unwanted), out[-500:])
    n = __import__("sqlite3").connect(path).execute("SELECT COUNT(*) FROM utterances").fetchone()[0]
    check("...the-mixed-report's-claim-was-not-recorded-as-well", n == 0, n)


def shown_and_names():
    print("[6] what reaches the console")
    check("shown-escapes-control-characters-and-non-ASCII,-backslashes-kept", replies.shown(
        ["a\nb", "\x1bc", "→", "\x7f", "x\\y"]) == "a\\x0ab, \\x1bc, \\u2192, \\x7f, x\\y",
        replies.shown(["a\nb", "\x1bc", "→", "\x7f", "x\\y"]))
    check("the-record-keeps-each-name-as-it-is-(the-seats'-recorded-names-unchanged)", replies.extra_keys(
        {"": 1, "a, b": 2, "c\nd": 3, "plain": 4, "a.b": 5}, ()) == ("", '"a.b"', "a, b", "c\nd", "plain"),
        replies.extra_keys({"": 1, "a, b": 2, "c\nd": 3, "plain": 4, "a.b": 5}, ()))
    check("...while-a-console-line-quotes-an-empty-name-and-one-holding-',-'", replies.listed(
        ["", "a, b", "c\nd", "plain"]) == '"", "a, b", c\\x0ad, plain', replies.listed(["", "a, b", "c\nd", "plain"]))
    check("a-claim-carrying-a-verdict-is-still-labelled-a-claim",
          keeper._label({"turn": 1, "speaker": "maren", "said": SAID, "verdict": "x"}) == "t1 claim by maren")
    lines = []
    keeper._report(lines.append, kept=[{"utterance_id": 3, "verdict": "fiction", "speaker": "maren", "type": "move",
                                        "extra": ("speaker", "type")}], kind="ruling")
    check("a-ruling-carrying-speaker-and-type-keys-is-labelled-a-ruling-by-the-pass-that-read-it",
          lines == ["    ruling on 3 carried what nothing reads: speaker, type"], lines)
    lines = []
    keeper._report(lines.append, kept=[{"turn": 1, "type": "move", "extra": ("actor", "note", "payload.injuries",
                                                                             "payload.x")}], kind="change")
    check("a-change's-extras-say-what-became-of-each:-read-by-nothing,-left-out,-written-as-null-(third-review)",
          lines == ["    t1 move carried what nothing reads: note",
                    "    t1 move left out of the event (no world rule reads it): payload.injuries, payload.x",
                    "    t1 move written as null (it names nothing): actor"], lines)
    lines = []
    keeper._report(lines.append, kept=[{"turn": 1, "speaker": "maren", "said": SAID,
                                        "extra": ("confidence", "extracts[].object")}], kind="claim")
    keeper._report(lines.append, kept=[{"utterance_id": 3, "verdict": "fiction", "extra": ("rationale",)}], kind="ruling")
    check("...a-claim's-object-written-as-empty,-a-ruling's-rationale-not-kept-(a-LEFT-ruling-writes-nothing)", lines == [
        "    t1 claim by maren carried what nothing reads: confidence",
        "    t1 claim by maren written as empty (not text): extracts[].object",
        "    ruling on 3 not kept (not text the record can hold): rationale"], lines)
    lines = []
    keeper._report(lines.append, kept=[{"turn": 1, "type": "move", "extra": ("payload.x",)}], kind="change", dry=True)
    check("...a-dry-run's-lines-say-nothing-was-written", lines == [
        "    t1 move (dry run, nothing written) left out of the event (no world rule reads it): payload.x"], lines)
    check("...and-a-name-with-leading-or-trailing-space-is-quoted-(never-read-as-the-id-`actor`)",
          replies.listed(["actor ", " x", "plain"]) == '"actor ", " x", plain', replies.listed(["actor ", " x", "plain"]))
    said_lines = []
    keeper.rule_scene(_led(), "r1", 0, 2, "fake-model", False, log=said_lines.append)
    check("...a-scene-with-no-claims-says-so-in-printable-ASCII", said_lines and all(_printable(ln) for ln in said_lines),
          said_lines)


def main():
    print("test_keeper_replies.py - the keeper's three replies, read to a contract (gate keeper-replies)\n")
    for section in (declarations_and_prompts, world_changes, claims_and_rulings, unreadable_replies,
                    canon_gate_and_cli, shown_and_names):
        try:
            section()
        except Exception as e:                                   # noqa: BLE001 - a harness reports
            check("%s RAISED %s" % (section.__name__, type(e).__name__), False, str(e)[:200])
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
