#!/usr/bin/env python3
"""facts.py — facts proposed from a world note, kept only by the author's own words (gate knowledge-proposals).

A world session writes prose; a character knows only what is linked to them. This turns one note into `knowledge`
entries the author approves fact by fact (src/engine/proposals.py says why and what is checked):

    python scripts/facts.py propose --book B --note N              the proposer's prompt, from the note's visible prose
    python scripts/facts.py check   --book B --note N --reply R    each proposal kept or refused, numbered, by name
    python scripts/facts.py approve --book B --note N --keep 1,3 --words "<the author's own words>"
    python scripts/facts.py list    --book B                       the knowledge notes and what each holds

`--note` is a path inside the book, or a note's name. The partner answers the prompt (or hands it to one agent) and
saves the JSON reply to a file for `check`. `approve` writes <book>/knowledge/<note>.md, which the book loads into
world.knowledge; nothing else of the author's is written. Check files live in <book>/staging/facts/.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import books, proposals, vault                     # noqa: E402
from src.engine.errors import EngineError                           # noqa: E402

_SKIP = {"runs", "staging", "knowledge", "prose", ".obsidian", ".git"}


def _note(book_dir, name):
    """A note named by path inside the book, or by its name -> (path, id). Raises FACTS_NOTE_MISSING."""
    direct = os.path.join(book_dir, name)
    if os.path.isfile(direct):
        return direct, os.path.splitext(os.path.basename(direct))[0]
    want = (name[:-3] if name.lower().endswith(".md") else name).lower()
    for root, dirs, files in os.walk(book_dir):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP)
        for f in sorted(files):
            if f.lower() == want + ".md":
                return os.path.join(root, f), f[:-3]
    raise EngineError("FACTS_NOTE_MISSING", "no note %r in %s" % (name, book_dir))


def _text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _staging(book_dir, note_id):
    d = os.path.join(book_dir, "staging", "facts")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, note_id + ".proposals.json")


def _propose(book_dir, a):
    path, note_id = _note(book_dir, a.note)
    world, _chars = vault.load_book(book_dir)
    msgs = proposals.prompt(note_id, _text(path), world)
    return "\n\n".join("=== %s ===\n%s" % (m["role"].upper(), m["content"]) for m in msgs)


def _check(book_dir, a):
    path, note_id = _note(book_dir, a.note)
    world, _chars = vault.load_book(book_dir)
    text = _text(path)
    verdicts = proposals.check(_text(a.reply), text, world)
    out = {"note": os.path.relpath(path, book_dir), "note_id": note_id, "digest": _digest(text),
           "checked_at": datetime.datetime.now().isoformat(timespec="seconds"), "verdicts": verdicts}
    with open(_staging(book_dir, note_id), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return out


def _approve(book_dir, a):
    path, note_id = _note(book_dir, a.note)
    words = str(a.words or "").strip()
    if not any(ch.isalnum() for ch in words):
        raise EngineError("FACTS_WORDS_MISSING", "approve needs the author's own words (--words) - a fact is kept only "
                          "by the author's approval")
    sp = _staging(book_dir, note_id)
    if not os.path.isfile(sp):
        raise EngineError("FACTS_NO_PROPOSALS", "no checked proposals for %s - run check first" % note_id)
    with open(sp, encoding="utf-8") as fh:
        checked = json.load(fh)
    if checked.get("digest") != _digest(_text(path)):
        raise EngineError("FACTS_NO_PROPOSALS", "%s changed after its proposals were checked - check again" % note_id)
    by_n = {v["n"]: v for v in checked.get("verdicts") or []}
    try:
        keep = sorted({int(x) for x in str(a.keep).split(",") if x.strip()})
    except ValueError:
        raise EngineError("FACTS_KEEP_REFUSED", "--keep is a list of proposal numbers, like 1,3,4")
    bad = [n for n in keep if n not in by_n or not by_n[n]["ok"]]
    if not keep or bad:
        raise EngineError("FACTS_KEEP_REFUSED", "keep only numbered proposals the check kept; not %s" % (bad or "nothing"))
    kn_dir = os.path.join(book_dir, "knowledge")
    os.makedirs(kn_dir, exist_ok=True)
    target = os.path.join(kn_dir, note_id + ".md")
    facts, log = [], []
    if os.path.isfile(target):
        old = vault.parse_note(target)
        facts = list((old["engine"] or {}).get("knowledge") or []) if isinstance(old["engine"], dict) else []
        in_log = False
        for line in old["body"].splitlines():
            if line.startswith("## "):
                in_log = line.strip().lower() == "## approvals"
            elif in_log and line.startswith("- "):
                log.append(line[2:])
    have = {proposals.squash(f.get("claim")) for f in facts if isinstance(f, dict)}
    added = []
    for n in keep:
        fact = dict(by_n[n]["fact"], source=note_id)
        if proposals.squash(fact.get("claim")) not in have:
            facts.append(fact)
            added.append(n)
    log.append('%s: kept %s - "%s"' % (datetime.datetime.now().isoformat(timespec="seconds"),
                                       ", ".join(str(n) for n in keep), words.replace("\n", " ")))
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(proposals.note_text(facts, note_id, log))
    return {"written": os.path.relpath(target, book_dir), "kept": keep, "added": added, "facts": len(facts)}


def _list(book_dir, a):
    d = os.path.join(book_dir, "knowledge")
    out = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".md"):
            n = vault.parse_note(os.path.join(d, f))
            rows = (n["engine"] or {}).get("knowledge") if isinstance(n["engine"], dict) else None
            out.append({"note": f, "source": n["frontmatter"].get("source", ""), "facts": len(rows or [])})
    return {"knowledge_notes": out}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="facts proposed from a world note, kept by the author's own words")
    ap.add_argument("what", choices=("propose", "check", "approve", "list"))
    ap.add_argument("--book", required=True, help="the book's slug or folder")
    ap.add_argument("--note", help="a note inside the book: its path, or its name")
    ap.add_argument("--reply", help="check: the proposer's JSON reply, as a file")
    ap.add_argument("--keep", help="approve: the proposal numbers to keep, like 1,3,4")
    ap.add_argument("--words", help="approve: the author's own words of approval")
    a = ap.parse_args(argv)
    need = {"propose": ("note",), "check": ("note", "reply"), "approve": ("note", "keep", "words"), "list": ()}[a.what]
    missing = ["--" + f for f in need if getattr(a, f) is None]
    if missing:
        ap.error("%s needs %s" % (a.what, ", ".join(missing)))
    try:
        book_dir = books.resolve(a.book)
        out = {"propose": _propose, "check": _check, "approve": _approve, "list": _list}[a.what](book_dir, a)
    except EngineError as exc:
        print("facts.py: %s" % exc, file=sys.stderr)
        return 1
    print(out if isinstance(out, str) else json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
