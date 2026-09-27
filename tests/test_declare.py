#!/usr/bin/env python3
"""test_declare.py - the author's hand through the real command: the owner's declarations written into a run with the
source word `author`, rehearsed whole on a copy and refused whole on any flaw, and on an adopted book carried by a draft
the owner's yes lands (gate author-declarations).

The owner, 2026-09-26: "a way to add content directly into the db". scripts/declare.py writes three kinds - an
off-page world event (the keeper's writer and gates), a correction (the critic's writer), an authored fact (the
AUTHORED tier, docs/keeper-of-truth.md T0) - on scratch copies of the invented vault book. Sections [2] to [5] carry
review 1's findings.

SUBPROCESSES, as tests/test_draft_flow.py: what is tested is that the COMMAND gives the result. Script-style, stdlib
only, exit 0 = all pass.
"""
import hashlib
import json
import os
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))
from src.engine import books, lineage                                    # noqa: E402
from src.engine.ledger import Ledger                                     # noqa: E402
from test_vault import _mk_vault                                          # noqa: E402  one fixture, many suites
from test_draft_flow import _adopted_book, _draft, _one, _opened, _run   # noqa: E402  the same harness

FAILS = []
EVENT = {"kind": "event", "words": "Mira took the brass lamp for her own.", "type": "seize", "actor": "mira",
         "payload": {"asset": "the brass lamp"}}
FACT = {"kind": "fact", "words": "Every keeper on the Rock is sworn to the Lamp Guild.",
        "extracts": [{"subject": "keepers of the rock", "predicate": "sworn to", "object": "the lamp guild"}]}
WORDS = "She never\r\ntrimmed\tthe wick — not once, café light or none. "


def check(name, ok, detail=""):
    detail = str(detail)[-400:].encode("ascii", "backslashreplace").decode("ascii")
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    if not ok:
        FAILS.append(name)


def _declare(book, run_id, entries, tmp, *args, name="decl.json", raw=None):
    """Write `entries` (a list, or raw text; or `raw` bytes) to a file, then run declare.py on it -> (rc, output, the
    file's path)."""
    path = os.path.join(tmp, name)
    with open(path, "wb") as fh:
        fh.write(raw if raw is not None else (entries if isinstance(entries, str) else json.dumps(entries)).encode())
    rc, out = _run(os.path.join("scripts", "declare.py"), "--book", book, "--run", run_id, "--file", path, *args)
    return rc, out, path


def _rows(path, run_id):
    """(event rows, utterance rows) of a run, read raw - [] when the file is not there."""
    if not os.path.isfile(path):
        return [], []
    con = sqlite3.connect(path)
    try:
        ev = [(r[0], r[1], r[2], json.loads(r[3])) for r in con.execute(
            "SELECT event_id, turn, type, payload FROM events WHERE run_id = ? ORDER BY event_id", (run_id,))]
        ut = [tuple(r) for r in con.execute("SELECT turn, speaker, said, tier FROM utterances WHERE run_id = ? "
                                            "ORDER BY utterance_id", (run_id,))]
        return ev, ut
    finally:
        con.close()


def _fold(path, run_id, turn):
    """The world at a turn, the connection closed after (a left-open one strands the temp folder on Windows)."""
    led = Ledger(path, create=False)
    try:
        return led.fold(run_id, turn)
    finally:
        led.con.close()


def _holder_of(path, run_id, turn, asset):
    return ((_fold(path, run_id, turn).get("holdings") or {}).get(asset) or {}).get("controller")


def _played(tmp, name, beats=2):
    """A fresh fixture book in its own folder, `beats` chair turns played (so the last turn is not the first) -> (book,
    its database, the run, its last turn)."""
    book = _mk_vault(os.path.join(tmp, name))
    _run(os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira", "--stub",
         typed="".join("the lamp gutters, beat %d\n" % k for k in range(beats)) + "quit\n")
    rec = books.db_path(book)
    return book, rec, _one(rec, "SELECT run_id FROM runs ORDER BY rowid LIMIT 1"), _one(rec, "SELECT MAX(turn) FROM turns")


def _propose(book, run_id, reports, tmp, *args):
    path = os.path.join(tmp, "report.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(reports, fh)
    return _run(os.path.join("scripts", "keeper.py"), "--vault", book, "--run", run_id, *args, path)


def written(tmp):
    print("[1] an unadopted book: an event, a correction and a fact, each with the source word author")
    book, rec, run_id, at = _played(tmp, "unadopted")
    correction = {"kind": "correction", "words": WORDS, "turn": at}
    fact = dict(FACT, words=WORDS + "The Guild keeps every keeper.")
    rc, out, path = _declare(book, run_id, [correction, EVENT, fact], tmp, "--dry-run")
    check("a-dry-run-writes-nothing", rc == 0 and "would declare" in out and _rows(rec, run_id)[1] == []
          and not any(e[2] == "seize" for e in _rows(rec, run_id)[0]), out)
    rc, out, path = _declare(book, run_id, [correction, EVENT, fact], tmp)
    ev, ut = _rows(rec, run_id)
    seize = [e for e in ev if e[2] == "seize"]
    fixes = [e for e in ev if e[2] == "correction"]
    check("the-event-lands-at-the-run's-last-committed-turn-with-source-author", rc == 0 and len(seize) == 1
          and seize[0][1] == at and seize[0][3] == {"asset": "the brass lamp", "source": "author"}, (out, seize))
    check("...and-the-fold-shows-it", _holder_of(rec, run_id, at, "the brass lamp") == "mira", out)
    check("the-correction-lands-at-the-next-tick-with-source-author-and-the-words-as-its-issue", len(fixes) == 1
          and fixes[0][1] == at + 1 and fixes[0][3]["source"] == "author"
          and fixes[0][3]["issue"] == WORDS and fixes[0][3]["turn"] == at, fixes)
    check("the-fact-is-an-authored-utterance-spoken-by-author,-its-words-exactly-as-given",
          ut == [(at, "author", fact["words"], "authored")], ut)
    check("...with-its-extract-indexed", _one(rec, "SELECT COUNT(*) FROM claim_extracts") == 1)
    with open(path, "rb") as fh:
        raw = fh.read()
    stem = os.path.join(book, "runs", "declarations", hashlib.sha256(raw).hexdigest()[:16])
    check("the-file-is-kept-in-the-book-byte-for-byte", os.path.isfile(stem + ".json")
          and open(stem + ".json", "rb").read() == raw and "runs/declarations/" in out, out)
    receipt = [json.loads(line) for line in open(stem + ".rows.jsonl", encoding="utf-8")] if os.path.isfile(
        stem + ".rows.jsonl") else []
    check("...beside-a-receipt-of-the-rows-it-wrote,-on-an-unadopted-book-too", len(receipt) == 1
          and sorted(e["id"] for e in receipt[0]["events"]) == sorted(e[0] for e in seize + fixes)
          and [u["said"] for u in receipt[0]["utterances"]] == [fact["words"]] and receipt[0]["run"] == run_id, receipt)
    check("...and-an-unadopted-book-has-no-lineage", not os.path.exists(lineage.log_path(book)))
    rc, out, _p = _declare(book, run_id, [correction, EVENT, fact], tmp)
    check("the-same-file-again-is-DECLARE_ALREADY_DECLARED-and-nothing-is-doubled", rc == 1
          and "[DECLARE_ALREADY_DECLARED]" in out and _rows(rec, run_id) == (ev, ut), out)
    rc, out, _p = _declare(book, run_id, [FACT], tmp, name="facts.json")
    rc2, out2, _p = _declare(book, run_id, [FACT], tmp, name="facts.json")
    check("...and-so-is-a-file-of-facts-alone", rc == 0 and rc2 == 1 and "[DECLARE_ALREADY_DECLARED]" in out2
          and [u[2] for u in _rows(rec, run_id)[1]].count(FACT["words"]) == 1, (out, out2))
    bom = json.dumps([dict(FACT, words="The Guild's seal is a lamp.")]).encode()
    rc, out, path = _declare(book, run_id, None, tmp, name="bom.json", raw=b"\xef\xbb\xbf" + bom)
    kept = os.path.join(book, "runs", "declarations", "%s.json" % hashlib.sha256(b"\xef\xbb\xbf" + bom).hexdigest()[:16])
    check("a-file-with-a-byte-order-mark-is-read,-and-kept-as-it-was", rc == 0 and os.path.isfile(kept)
          and open(kept, "rb").read()[:3] == b"\xef\xbb\xbf", out)
    fix2 = {"kind": "correction", "words": "The wind never turned.", "turn": at}
    rc, out, _p = _declare(book, run_id, [fix2, dict(EVENT, words="The logbook is hers now.",
                                                     payload={"asset": "the logbook"})], tmp)
    ev2 = _rows(rec, run_id)[0]
    fix = [e for e in ev2 if e[2] == "correction" and e[3]["issue"] == fix2["words"]]
    log = [e for e in ev2 if e[2] == "seize" and e[3].get("asset") == "the logbook"]
    check("a-correction-of-the-last-beat-never-supersedes-an-event-the-same-file-adds", rc == 0 and len(fix) == 1
          and len(log) == 1 and log[0][0] not in fix[0][3]["supersedes"], (out, fix, log))
    return book, rec, run_id, at


def corrections(tmp):
    print("\n[2] a correction retracts what the beat did, never what the owner declared on that turn")
    book, rec, run_id, at = _played(tmp, "corrections")
    _declare(book, run_id, [EVENT], tmp)
    rc, out, _p = _declare(book, run_id, [{"kind": "correction", "words": "No wick was trimmed.", "turn": at}], tmp,
                           name="later.json")
    check("the-owner's-later-correction-of-that-turn-leaves-the-declared-event-standing", rc == 0
          and _holder_of(rec, run_id, at + 1, "the brass lamp") == "mira", out)
    code = ("import sys; sys.path[:0] = [%r, %r]\nfrom src.engine.ledger import Ledger\nimport critic\n"
            "led = Ledger(%r, create=False)\ncritic.correct_run(led, %r, {'continuity': [{'turn': %d, 'issue': "
            "'the critic saw a slip'}]})\nled.con.close()\n") % (REPO, os.path.join(REPO, "scripts"), rec, run_id, at)
    rc, out = _run("-c", code)
    check("...and-so-does-the-critic's", rc == 0 and _holder_of(rec, run_id, at + 1, "the brass lamp") == "mira", out)
    rc, out = _propose(book, run_id, [{"turn": at, "type": "seize", "actor": "mira", "payload": {"asset": "the oil store"}}],
                       tmp, "--propose")
    beat = [e[0] for e in _rows(rec, run_id)[0] if e[2] == "seize" and e[3] == {"asset": "the oil store"}]
    rc, out, _p = _declare(book, run_id, [{"kind": "correction", "words": "The oil store was not hers that night.",
                                           "turn": at},
                                          dict(EVENT, words="She took the oil store at dawn, off the page.",
                                               payload={"asset": "the oil store"})], tmp, name="restate.json")
    fix = [e for e in _rows(rec, run_id)[0] if e[2] == "correction" and "oil store" in e[3]["issue"]]
    check("a-corrected-beat's-change-can-be-restated-as-the-author's-own-in-the-same-file", rc == 0 and len(beat) == 1
          and len(fix) == 1 and beat[0] in fix[0][3]["supersedes"]
          and _holder_of(rec, run_id, at + 1, "the oil store") == "mira", out)


def keeper_meets_the_author(tmp, book, rec, run_id, at):
    print("\n[3] the keeper: a report cannot pass for the author, a ruling cannot touch the author's fact")
    rc, out = _propose(book, run_id, [{"turn": at, "type": "seize", "actor": "mira",
                                       "payload": {"asset": "the spare oil", "source": "author"}}], tmp, "--propose")
    row = [e for e in _rows(rec, run_id)[0] if e[2] == "seize" and e[3].get("asset") == "the spare oil"]
    check("the-keeper's-row-has-no-source", rc == 0 and len(row) == 1 and "source" not in row[0][3], (out, row))
    before = _rows(rec, run_id)[1]
    rc, out = _propose(book, run_id, [{"turn": at, "speaker": "author", "said": "The lamp was never lit.",
                                       "extracts": [{"subject": "the lamp", "predicate": "never", "object": "lit"}]}],
                       tmp, "--propose")
    check("a-keeper-claim-spoken-by-author-is-CLAIM_SPEAKER_RESERVED", "CLAIM_SPEAKER_RESERVED" in out
          and _rows(rec, run_id)[1] == before, out)
    rc, out = _run(os.path.join("scripts", "keeper.py"), "--vault", book, "--run", run_id, "--rule", "--prompt-only")
    claims_part = out.split("THE CLAIMS OF THIS SCENE")[-1].split("CONTRADICTIONS")[0]
    check("the-ruling-prompt-does-not-offer-the-author's-fact-for-a-verdict", rc == 0 and "author said" not in claims_part,
          claims_part)
    uid = _one(rec, "SELECT MIN(utterance_id) FROM utterances WHERE tier = 'authored'")
    rc, out = _propose(book, run_id, [{"utterance_id": uid, "verdict": "fiction"}], tmp, "--rule", "--rulings")
    check("...and-a-ruling-on-it-is-KEEPER_RULING_AUTHORED", "KEEPER_RULING_AUTHORED" in out
          and _one(rec, "SELECT COUNT(*) FROM claim_resolutions") == 0, out)


def refused(tmp):
    print("\n[4] a flawed file is refused whole, and nothing of it is written")
    book, rec, run_id, at = _played(tmp, "refusals")
    before = _rows(rec, run_id)
    reveal = {"kind": "event", "words": "Mira has known since the wreck.", "type": "reveal", "actor": "mira",
              "payload": {"fact": "the wreck was no accident", "to": ["mira"]}}
    cases = (
        ("an-object-not-a-list-is-DECLARE_FILE_UNREADABLE", json.dumps(EVENT), "DECLARE_FILE_UNREADABLE"),
        ("an-empty-list-is-DECLARE_FILE_UNREADABLE", "[]", "DECLARE_FILE_UNREADABLE"),
        ("not-json-is-DECLARE_FILE_UNREADABLE", "[{", "DECLARE_FILE_UNREADABLE"),
        ("a-kind-this-version-does-not-declare-is-DECLARE_ENTRY_MALFORMED",
         [FACT, {"kind": "hold", "words": "She loves the boathouse."}], "DECLARE_ENTRY_MALFORMED"),
        ("an-entry-without-the-owner's-words-is-DECLARE_WORDS_MISSING", [FACT, dict(EVENT, words="  ")],
         "DECLARE_WORDS_MISSING"),
        ("...and-so-is-a-placeholder", [dict(FACT, words="<the owner's words>")], "DECLARE_WORDS_MISSING"),
        ("an-event-naming-its-own-turn-is-refused:-the-path-sets-it", [FACT, dict(EVENT, turn=0)],
         "never picks its own turn"),
        ("...and-so-is-one-naming-its-own-source", [dict(FACT, source="author")], "DECLARE_ENTRY_MALFORMED"),
        ("a-payload-key-nothing-reads-is-refused,-never-dropped", [FACT, dict(EVENT, payload={
            "asset": "the brass lamp", "why": "she needed light"})], "kept only in part (payload.why)"),
        ("an-actor-no-one-the-run-knows-is-DECLARE_NAME_UNKNOWN", [FACT, dict(EVENT, actor="tomas")],
         "DECLARE_NAME_UNKNOWN"),
        ("...and-so-is-a-reveal's-knower", [FACT, dict(reveal, payload={"fact": "the tide tables were forged",
                                                                        "to": ["Tomas"]})], "DECLARE_NAME_UNKNOWN"),
        ("a-move-to-a-place-the-bible-does-not-name-is-DECLARE_PLACE_UNKNOWN",
         [FACT, {"kind": "event", "words": "Mira walked down to the boat-house.", "type": "move", "actor": "mira",
                 "payload": {"to": "the boat-house"}}], "DECLARE_PLACE_UNKNOWN"),
        ("a-correction-of-a-turn-never-recorded-is-DECLARE_TURN_UNKNOWN",
         [FACT, {"kind": "correction", "words": "Not so.", "turn": at + 50}], "DECLARE_TURN_UNKNOWN"),
        ("an-event-the-keeper's-gates-refuse-is-DECLARE_ENTRY_REFUSED-with-their-code",
         [FACT, dict(EVENT, type="sing")], "WORLD_EVENT_TYPE_UNKNOWN"),
        ("...and-a-sound-event-before-it-is-not-written-either",
         [dict(EVENT, payload={"asset": "the spare wick"}), dict(EVENT, type="sing")], "WORLD_EVENT_TYPE_UNKNOWN"),
        ("two-entries-on-one-world-change-are-refused-whole:-the-rehearsal-writes-them-in-order",
         [FACT, reveal, dict(reveal, words="Mira learned the wreck was no accident.")], "KEEPER_NOT_A_WORLD_EVENT"),
        ("...and-so-are-a-correction-and-two-seizures-of-one-asset",
         [{"kind": "correction", "words": "Not that way.", "turn": at}, dict(EVENT, payload={"asset": "the flint"}),
          dict(EVENT, words="The flint was hers.", payload={"asset": "the flint"})], "KEEPER_NOT_A_WORLD_EVENT"),
        ("a-fact-indexing-nothing-is-DECLARE_ENTRY_MALFORMED", [dict(FACT, extracts=[])], "DECLARE_ENTRY_MALFORMED"),
        ("a-fact-whose-extract-lacks-a-subject-is-refused-before-anything-opens",
         [{"kind": "correction", "words": "Not so.", "turn": at}, EVENT,
          dict(FACT, extracts=[{"predicate": "sworn to", "object": "the guild"}])], "[DECLARE_ENTRY_MALFORMED]"),
    )
    for name, entries, code in cases:
        rc, out, _p = _declare(book, run_id, entries, tmp)
        check(name, rc == 1 and code in out and _rows(rec, run_id) == before, out)
    rc, out, _p = _declare(book, run_id, [dict(reveal, payload={"fact": "the keeper's oath", "to": ["tomas_keeper"]})],
                           tmp, "--dry-run")
    check("a-person-the-run's-bible-names-may-be-a-knower", rc == 0 and "would declare" in out, out)
    rc, out, _p = _declare(book, "no-such-run", [FACT], tmp)
    check("an-unknown-run-is-DECLARE_RUN_UNKNOWN", rc == 1 and "[DECLARE_RUN_UNKNOWN]" in out, out)
    fresh = _mk_vault(os.path.join(tmp, "never run"))
    rc, out, _p = _declare(fresh, "any", [FACT], tmp)
    check("...and-so-is-a-book-never-run,-and-no-database-is-made", rc == 1 and "[DECLARE_RUN_UNKNOWN]" in out
          and not os.path.exists(books.db_path(fresh)), out)
    empty = _mk_vault(os.path.join(tmp, "empty run"))
    _run(os.path.join("scripts", "direct.py"), "--book", empty, "--char", "Mira", "--stub", typed="quit\n")
    erec = books.db_path(empty)
    erun = _one(erec, "SELECT run_id FROM runs") if os.path.isfile(erec) else "none"
    rc, out, _p = _declare(empty, erun, [FACT], tmp)
    check("a-run-with-no-committed-turn-is-DECLARE_RUN_EMPTY", rc == 1 and "[DECLARE_RUN_EMPTY]" in out, out)
    other, orec, _orun, _oat = _played(tmp, "other")
    rc, out = _run(os.path.join("scripts", "declare.py"), "--book", book, "--run", run_id, "--file",
                   os.path.join(tmp, "decl.json"), "--db", orec)
    check("another-book's-database-is-BOOK_DB_CROSS_BOOK", rc == 1 and "BOOK_DB_CROSS_BOOK" in out, out)
    rc, out, _p = _declare(os.path.dirname(book), run_id, [FACT], tmp)
    check("a---book-that-is-no-book-folder-is-DRAFT_NOT_A_BOOK", rc == 1 and "[DRAFT_NOT_A_BOOK]" in out, out)
    _run(os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira", "--stub",
         typed="".join("a second run, beat %d\n" % k for k in range(4)) + "quit\n")
    second = _one(rec, "SELECT run_id FROM runs WHERE run_id <> '%s'" % run_id)
    led = Ledger(rec, create=False)
    try:
        led.register_character(second, "wren", {}, {})
    finally:
        led.con.close()
    before = _rows(rec, run_id)
    rc, out, _p = _declare(book, run_id, [{"kind": "correction", "words": "Not so.", "turn": 3}], tmp)
    rc2, out2, _p = _declare(book, run_id, [dict(EVENT, actor="wren")], tmp)
    check("a-turn-or-a-name-of-another-run-in-the-book-is-refused", rc == 1 and "[DECLARE_TURN_UNKNOWN]" in out
          and rc2 == 1 and "[DECLARE_NAME_UNKNOWN]" in out2 and _rows(rec, run_id) == before, (out, out2))
    code = ("import sys; sys.path[:0] = [%r, %r]\nimport declare\nreal, calls = declare._write, []\n"
            "def once(led, run, plan):\n    calls.append(1)\n    return {'events': [], 'utterances': []} if len(calls) == 1 "
            "else real(led, run, plan)\ndeclare._write = once\nsys.exit(declare.main(['--book', %r, '--run', %r, "
            "'--file', %r]))\n") % (REPO, os.path.join(REPO, "scripts"), book, run_id, os.path.join(tmp, "twice.json"))
    with open(os.path.join(tmp, "twice.json"), "w", encoding="utf-8") as fh:
        json.dump([dict(EVENT, payload={"asset": "the tinderbox"}), dict(EVENT, words="The tinderbox is hers.",
                                                                        payload={"asset": "the tinderbox"})], fh)
    rc, out = _run("-c", code)
    check("a-book-that-changed-after-the-rehearsal-is-refused-naming-what-was-written", rc == 1
          and "after a rehearsal that wrote the whole file" in out and "KEEPER_NOT_A_WORLD_EVENT" in out, out)


def adopted(tmp):
    print("\n[5] an adopted book: the record refuses it, a draft carries it, the owner's yes lands it")
    book, rec = _adopted_book(tmp, "adopted")
    run_id, at = _one(rec, "SELECT run_id FROM runs"), _one(rec, "SELECT MAX(turn) FROM turns")
    before = _rows(rec, run_id)
    rc, out, _p = _declare(book, run_id, [EVENT, FACT], tmp)
    check("the-record-is-refused-up-front", rc == 1 and "[DB_IS_RECORD]" in out and "draft.py open" in out
          and _rows(rec, run_id) == before, out)
    rc, out, _p = _declare(book, run_id, [EVENT, FACT], tmp, "--dry-run")
    check("...and-so-is-a-dry-run-on-it:-a-rehearsal-needs-a-draft", rc == 1 and "[DB_IS_RECORD]" in out
          and _rows(rec, run_id) == before, out)
    d1 = _opened(_draft(book, "open")[1])
    with lineage.hold(book, "test-holder"):
        rc, out, _p = _declare(book, run_id, [EVENT, FACT], tmp, "--db", d1)
    check("a-held-lease-refuses-it-and-nothing-is-written", rc == 1 and "[LINEAGE_LEASE_HELD]" in out
          and _rows(d1, run_id) == before, out)
    rc, out, path = _declare(book, run_id, [EVENT, FACT], tmp, "--db", d1)
    line = ([e for e in lineage.read(book) if e["op"] == "declare"] or [{}])[-1]
    kept = os.path.join(book, line.get("file", "missing"))
    ev, ut = _rows(d1, run_id)
    check("a-draft-takes-it-and-the-record-is-untouched", rc == 0 and any(e[2] == "seize" and e[3].get("source")
                                                                          == "author" for e in ev)
          and ut[-1:] == [(at, "author", FACT["words"], "authored")] and _rows(rec, run_id) == before, out)
    check("the-lineage-logs-the-kept-file-and-its-digest", line.get("draft") == "d1" and line.get("run") == run_id
          and line.get("entries") == 2 and os.path.isfile(kept) and line.get("digest") == lineage.digest(kept)
          and open(kept, "rb").read() == open(path, "rb").read() and len(line.get("utterances") or []) == 1
          and len(line.get("events") or []) == 1, line)
    check("...and-the-hint-lands-it-in-advance", "--in-advance" in out and "draft.py promote" in out, out)
    rc, out = _draft(book, "promote", "--draft", "d1", "--approved", "Declare it so.", "--by", "owner", "--in-advance")
    ev, ut = _rows(rec, run_id)
    check("the-owner's-yes-lands-the-authored-rows-in-the-record", rc == 0 and any(
        e[2] == "seize" and e[3].get("source") == "author" for e in ev) and ut[-1:] == [(at, "author", FACT["words"],
                                                                                        "authored")], out)
    rc, out, _p = _declare(book, run_id, [FACT], tmp, "--db", d1)
    check("the-promoted-draft's-old-path-is-refused-and-no-file-is-made", rc == 1 and "[DRAFT_NOT_FOUND]" in out
          and not os.path.exists(d1), out)
    d2 = _opened(_draft(book, "open")[1])
    rc, out, _p = _declare(book, run_id, [EVENT, FACT], tmp, "--db", d2)
    check("a-file-the-record-already-holds-is-DECLARE_ALREADY_DECLARED-on-a-new-draft", rc == 1
          and "[DECLARE_ALREADY_DECLARED]" in out, out)
    once = [dict(FACT, words="The Guild meets at the spring tide.")]
    _declare(book, run_id, once, tmp, "--db", d2, name="once.json")
    _draft(book, "reject", "--draft", "d2")
    d3 = _opened(_draft(book, "open")[1])
    rc, out, _p = _declare(book, run_id, once, tmp, "--db", d3, name="once.json")
    check("...but-a-file-declared-only-into-a-rejected-draft-may-be-declared-again", rc == 0, out)
    _run(os.path.join("scripts", "direct.py"), "--book", book, "--char", "Mira", "--stub", "--db", d3,
         "--resume", run_id, typed="the lamp gutters again\nquit\n")
    rc, out, _p = _declare(book, run_id, [dict(FACT, words="The Guild's hall has one door.")], tmp, "--db", d3,
                           name="after.json")
    check("the-hint-after-a-played-beat-says-approve-it-after-review,-never-in-advance", rc == 0
          and "partner-relayed> --in-advance" not in out and "without --in-advance" in out
          and "played since it opened" in out, out)
    _draft(book, "promote", "--draft", "d3", "--approved", "Keep it.", "--by", "owner")
    d4 = _opened(_draft(book, "open")[1])
    _draft(book, "restore", "--to", "d1", "--approved", "Back.", "--by", "owner")
    rc, out, _p = _declare(book, run_id, [dict(FACT, words="The tide rises.")], tmp, "--db", d4, name="stale.json")
    check("a-draft-taken-from-a-state-the-record-has-left-is-DECLARE_DRAFT_STALE", rc == 1
          and "[DECLARE_DRAFT_STALE]" in out, out)


def main():
    print("test_declare.py - the author's hand (gate author-declarations)\n")
    with tempfile.TemporaryDirectory(prefix="swe_declare_", ignore_cleanup_errors=True) as tmp:
        book, rec, run_id, at = written(tmp)
        corrections(tmp)
        keeper_meets_the_author(tmp, book, rec, run_id, at)
        refused(tmp)
        adopted(tmp)
    print("\n%s: %d failure(s)" % ("OK" if not FAILS else "FAIL", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
