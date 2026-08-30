"""vault.py — the Obsidian book-vault loader (machine/content seam at the repository level).

A BOOK lives as linked markdown notes in an Obsidian vault (relevancy-gate.md: "the vault is an
Obsidian graph — notes + [[links]] + backlinks"); the machine reads it, never writes it. Note
format (authoring contract, guide-content.md):

  prose canon + [[links]]            <- the human layer, reads as canon in Obsidian
  one fenced ```json block           <- the engine payload (stdlib has no yaml; json is exact)
  ## Beliefs                         <- character notes only: the vault entries
  - (0.9, lived) claim text [[Linked Note]] [[Another]]

[[links]] are LIVE machinery: a belief's linked note names become trigger anchors (gate.py) —
author-controlled edges, not substring luck. The vault path is always explicit; the engine
defaults to no user location (the seam law, applied to paths).
"""
import json
import os
import re
from .errors import EngineError

_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
_BELIEF_RE = re.compile(r"^\s*[-*]\s*\(([0-9.]+)\s*,\s*([^)]*)\)\s*(.+)$")


class VaultError(EngineError):
    """A note failed the authoring contract — named loudly, never coerced."""


def parse_note(path):
    """One .md note -> {"id", "type", "frontmatter", "engine", "links", "beliefs", "body"}.
    type/id come from flat frontmatter keys when present, else the filename.

    EVERY frontmatter key is CARRIED, in note["frontmatter"]. It used to keep type and id and
    silently discard the rest — matched by the regex, checked against a whitelist, thrown away with
    nothing said. Measured across the three real books on 2026-08-24: type 36, id 32, source 3,
    pulled 3, note 1. Seven authored values reaching nothing, and no message telling the author.

    Third time this shape has been found here. consolidation._KNOWN_DIMS went stale and discarded
    EVERY appraisal in a live run; THE LAW's first draft dropped unknown identity keys and the guard
    came back green. The beliefs check below exists for the same reason and records its own cost —
    41 of 77 beliefs across 5 notes. Dropping is worse than failing.

    CARRIED, not refused: an Obsidian note legitimately holds keys the engine has no opinion about,
    and refusing them would make the engine the arbiter of the author's note format — the mistake
    THE LAW's refusal draft made when it took down two of three real books. Nothing is coerced
    either; `pulled` stays the string the author typed, because a guessed date format yields a
    confident wrong value where the raw string yields an honest one.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    note = {"id": os.path.splitext(os.path.basename(path))[0], "type": None, "frontmatter": {},
            "engine": None, "links": [], "beliefs": [], "body": text}
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if fm:
        for line in fm.group(1).splitlines():       # flat keys only — yaml subset by design
            m = re.match(r"^(\w+)\s*:\s*(.+?)\s*$", line)
            if not m:
                continue
            key, value = m.group(1), m.group(2).strip().strip(chr(34))
            note["frontmatter"][key] = value
            if key in ("type", "id"):       # these two ALSO get their own slot, as before
                note[key] = value
    note["links"] = list(dict.fromkeys(l.strip() for l in _LINK_RE.findall(text)))
    blocks = _JSON_BLOCK_RE.findall(text)
    if blocks:
        try:
            note["engine"] = json.loads(blocks[0])
        except json.JSONDecodeError as e:
            raise VaultError("VAULT_ENGINE_BLOCK_INVALID_JSON",
                             "%s: engine block is not valid json (%s)" % (path, e))
    in_beliefs = False
    saw_section = False
    bullets = 0
    for line in text.splitlines():
        if line.strip().lower().startswith("## beliefs"):
            in_beliefs = True
            saw_section = True
            continue
        if in_beliefs and line.startswith("## "):
            in_beliefs = False
        if in_beliefs:
            if re.match(r"^\s*[-*]\s+\S", line):
                bullets += 1
            m = _BELIEF_RE.match(line)
            if m:
                conf, prov, rest = float(m.group(1)), m.group(2).strip(), m.group(3).strip()
                links = [l.strip() for l in _LINK_RE.findall(rest)]
                claim = _LINK_RE.sub(lambda mm: mm.group(1).strip(), rest).strip()
                if not (0.0 <= conf <= 1.0):
                    raise VaultError("VAULT_BELIEF_CONFIDENCE_RANGE",
                                     "%s: belief confidence %s out of [0,1]" % (path, conf))
                note["beliefs"].append({"claim": claim, "confidence": conf, "provenance": prov,
                                        "believed_value": True, "links": links})
    # Rule 6, fail loud: a note that DECLARES beliefs and parses none of them has authored content
    # that reaches nothing. Silence here cost 41 of 77 beliefs across 5 notes before it was caught,
    # with current.vault never set (below) and every recall_events.belief_refs empty.
    if saw_section and bullets and not note["beliefs"]:
        raise VaultError(
            "VAULT_BELIEFS_SECTION_UNPARSED",
            "%s: '## Beliefs' has %d bullet(s) and none match the authoring contract "
            "`- (confidence, provenance) claim` — they would load as zero beliefs. "
            "Fix the bullets, or delete the section." % (path, bullets))
    return note


def load_book(book_dir):
    """Book folder -> (world dict, {char_id: char dict}). Layout:
       <book>/world/*.md (exactly one type:world note), <book>/characters/*.md (type:character),
       <book>/people/*.md (type:person -> world.people entries). The runs/ db lives beside them."""
    if not os.path.isdir(book_dir):
        raise VaultError("VAULT_BOOK_FOLDER_MISSING", "book folder not found: %s" % book_dir)

    def notes_in(sub):
        d = os.path.join(book_dir, sub)
        if not os.path.isdir(d):
            return []
        return [parse_note(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".md")]

    worlds = [n for n in notes_in("world") if (n["type"] or "world") == "world"]
    if len(worlds) != 1:
        raise VaultError("VAULT_WORLD_NOTE_COUNT",
                         "%s: need exactly one world note, found %d" % (book_dir, len(worlds)))
    wnote = worlds[0]
    if not isinstance(wnote["engine"], dict):
        raise VaultError("VAULT_WORLD_NO_ENGINE_BLOCK",
                         "world note %r has no engine block" % wnote["id"])
    world = dict(wnote["engine"])
    world.setdefault("world", wnote["id"])

    people = list(world.get("people", []))
    for p in notes_in("people"):
        if (p["type"] or "person") != "person":
            continue
        entry = dict(p["engine"] or {})
        entry.setdefault("id", p["id"].lower().replace(" ", "_"))
        if "what" not in entry:                     # first prose line is the identity record
            body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", p["body"], flags=re.DOTALL)
            prose = [l for l in body.splitlines()
                     if l.strip() and not l.startswith(("#", "-", "```"))]
            entry["what"] = prose[0].strip() if prose else p["id"]
        people.append(entry)
    if people:
        world["people"] = people

    chars = {}
    for c in notes_in("characters"):
        if (c["type"] or "character") != "character":
            continue
        if not isinstance(c["engine"], dict):
            raise VaultError("VAULT_CHARACTER_NO_ENGINE_BLOCK",
                             "character note %r has no engine block" % c["id"])
        char = dict(c["engine"])
        for key in ("fixed", "baseline", "current"):
            if key not in char:
                raise VaultError("VAULT_CHARACTER_BLOCK_INCOMPLETE",
                                 "character %r engine block missing %r" % (c["id"], key))
        if c["beliefs"]:                            # the Beliefs section IS the vault
            char["current"] = dict(char["current"], vault=c["beliefs"])
        chars[c["id"].lower().replace(" ", "_")] = char
    if not chars:
        raise VaultError("VAULT_NO_CHARACTERS", "%s: no character notes found" % book_dir)
    return world, chars
