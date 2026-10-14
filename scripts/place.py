#!/usr/bin/env python3
"""place.py — place a person in the bands whose rules they meet, and list what they then know (gate place-a-person).

The owner, 2026-10-13: a tale saved for town X, forgotten, then a character from town X written as never having heard
of it - "What guards against this? How do we ask who should know this info so we can assign individuals?" This asks:

    python scripts/place.py candidates --book B --person P     the bands P's sheet meets, and the ones only you can judge
    python scripts/place.py confirm    --book B --person P --keep grp.a,grp.b --words "<the author's own words>"
    python scripts/place.py knows      --book B --person P     what P holds, by the band or place that holds it

`candidates` reads the sheet's typed facts - where they are (`current.location`), the places they belong or belonged
to (`loc.` memberships, even one they left), their people (`fixed.people`) - and matches each band's `requires`. A band
whose rule is plain words only, or whose `requires` names a ROLE, is listed for the author with the reason: the sheet
has no structured role, `fixed.position` is prose told to the actor word for word, and a match is never claimed from
prose (the parent session, 2026-10-13). `confirm` writes the confirmed bands - on the author's words - to
<book>/memberships/<person>.md, which `vault.load_book` adds to the sheet's `current.memberships`; the sheet itself is
never written.
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import attachments, bands, books, vault           # noqa: E402
from src.engine.errors import EngineError                           # noqa: E402

ROLE_WHY = ("a role is matched only from a structured role field and the sheet has none: fixed.position is prose told "
            "to the actor word for word, so whether they fill this role is yours to judge")


def _norm(text):
    return " ".join(str(text or "").split()).lower()


def _sheet(char):
    """A sheet's typed facts -> (places, people, held): where they are and have belonged, their people, their bands."""
    fixed = char.get("fixed") if isinstance(char.get("fixed"), dict) else {}
    cur = char.get("current") if isinstance(char.get("current"), dict) else {}
    ms = [m for m in (cur.get("memberships") or []) if isinstance(m, dict) and m.get("of")]
    places = ([str(cur["location"])] if cur.get("location") else []) + \
        [str(m["of"])[4:] for m in ms if str(m["of"]).startswith("loc.")]
    people = fixed.get("people") if isinstance(fixed.get("people"), str) and fixed["people"].strip() else None
    return places, people, [str(m["of"]) for m in ms]


def candidates(world, char):
    """-> {places, people, matched, check_by_hand, already}: each band of the register, sorted by what the sheet says."""
    places, people, held = _sheet(char)
    out = {"places": places, "people": people, "matched": [], "check_by_hand": [], "already": []}
    for b in bands.rows(world):
        if not str(b.get("id") or "").strip():
            continue
        name = "grp." + str(b["id"]).strip()
        if name in held:
            out["already"].append(name)
            continue
        req = b.get("requires") if isinstance(b.get("requires"), dict) else {}
        row = {"band": name, "kind": b.get("kind"), "rule": b.get("rule")}
        if not req:
            out["check_by_hand"].append(dict(row, why="the rule is in plain words only - nothing typed to match"))
            continue
        meets, hand, miss = [], [], False
        if "place" in req:
            if req["place"] in places:
                meets.append("lives or lived in %s" % req["place"])
            else:
                miss = True
        if "nation" in req:
            if people is None:
                hand.append("the sheet names no people (fixed.people) to match requires.nation against")
            elif _norm(people) == _norm(req["nation"]):
                meets.append("their people are %s" % req["nation"])
            else:
                miss = True
        if "role" in req:
            hand.append(ROLE_WHY)
        if miss:
            continue                                  # a typed rule the sheet contradicts: not theirs
        if hand:
            out["check_by_hand"].append(dict(row, why="; ".join(hand), meets=meets))
        else:
            out["matched"].append(dict(row, why="; ".join(meets)))
    return out


def _load(book_dir, person):
    world, chars = vault.load_book(book_dir)
    return world, vault.character_or_raise(chars, person)


def _candidates(book_dir, a):
    world, char = _load(book_dir, a.person)
    return dict(candidates(world, char), person=a.person)


def _confirm(book_dir, a):
    words = str(a.words or "").strip()
    if not any(ch.isalnum() for ch in words):
        raise EngineError("PLACE_WORDS_MISSING", "confirm needs the author's own words (--words) - a person is placed in "
                          "a band only on the author's say")
    world, _char = _load(book_dir, a.person)
    keep = [k.strip() for k in str(a.keep).split(",") if k.strip()]
    registered = set(attachments.names_for(world))
    bad = [k for k in keep if k not in registered]
    if not keep or bad:
        raise EngineError("PLACE_BAND_UNREGISTERED", "keep only registered bands or places (grp.<id>, loc.<id>); not %s"
                          % (bad or "nothing"))
    d = os.path.join(book_dir, "memberships")
    os.makedirs(d, exist_ok=True)
    target = os.path.join(d, a.person + ".md")
    rows, log = [], []
    if os.path.isfile(target):
        old = vault.parse_note(target)
        rows = list((old["engine"] or {}).get("memberships") or []) if isinstance(old["engine"], dict) else []
        in_log = False
        for line in old["body"].splitlines():
            if line.startswith("## "):
                in_log = line.strip().lower() == "## approvals"
            elif in_log and line.startswith("- "):
                log.append(line[2:])
    have = {str(r.get("of")) for r in rows if isinstance(r, dict)}
    added = [k for k in keep if k not in have]
    rows += [{"of": k} for k in added]
    log.append('%s: placed in %s - "%s"' % (datetime.datetime.now().isoformat(timespec="seconds"), ", ".join(keep),
                                            words.replace("\n", " ")))
    nl = "\n"
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("---" + nl + "type: memberships" + nl + "person: %s" % a.person + nl + "---" + nl +
                 "# Where %s belongs" % a.person + nl + nl +
                 "Placed by the author, band by band (scripts/place.py confirm). Added to the sheet's current.memberships "
                 "when the book loads; edit or delete a row here." + nl + nl + "## Approvals" + nl +
                 nl.join("- %s" % line for line in log) + nl + nl + "```json" + nl +
                 json.dumps({"memberships": rows}, indent=1, ensure_ascii=False) + nl + "```" + nl)
    return {"written": os.path.relpath(target, book_dir), "added": added, "memberships": len(rows)}


def _knows(book_dir, a):
    _world, char = _load(book_dir, a.person)
    held, own = {}, 0
    for b in ((char.get("current") or {}).get("vault") or []):
        if not isinstance(b, dict):
            continue
        if b.get("shared"):
            held.setdefault(str(b["shared"]), []).append(b.get("claim"))
        else:
            own += 1
    return {"person": a.person, "by_holder": held, "own_beliefs": own}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="place a person in the bands whose rules they meet")
    ap.add_argument("what", choices=("candidates", "confirm", "knows"))
    ap.add_argument("--book", required=True, help="the book's slug or folder")
    ap.add_argument("--person", required=True, help="a character's id")
    ap.add_argument("--keep", help="confirm: the bands or places to place them in, like grp.a,loc.b")
    ap.add_argument("--words", help="confirm: the author's own words")
    a = ap.parse_args(argv)
    if a.what == "confirm" and a.keep is None:
        ap.error("confirm needs --keep")
    try:
        book_dir = books.resolve(a.book)
        out = {"candidates": _candidates, "confirm": _confirm, "knows": _knows}[a.what](book_dir, a)
    except EngineError as exc:
        print("place.py: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
