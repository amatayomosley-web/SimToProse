"""contracts.py — the checker every author-file contract shares: fields declared once, a file walked against them.

WHY (gate sheet-contract, 2026-09-25; G2 of the contracts plan the owner approved, agreed with Symphony on the shared
board). No author file had one declaration of its fields. What a sheet may carry lived in three places that
disagreed: the blueprint (drives.orientation "REQUIRED", while the engine reads none of it), the linter's hand-kept
lists (every `_note` in a number table reported as "not a number" - 19 of the 57 errors on the owner's four books),
and the readers themselves (an absent baseline.skills crashes both drivers; the linter only warned). A contract
module now declares each field ONCE - its shape, whether a book must author it, and where it stands:

  active   the engine reads it
  retired  it was read and was replaced: `replaced_by` names what took its place, `policy` what to do
           (prune | move | refuse - refuse: the owner's ruling says replaced, not translated)
  unread   an author wrote it and nothing reads it: it reaches nothing
  runtime  the engine writes it; an author may seed it

and an ANNOTATION - any key beginning with `_`, or named `note` - is ignored everywhere, the rule
`scene._strip_notes` applies. `check` walks a file against the declarations and REPORTS, which is all a linter
does: a draft always loads. `require_at_start` is the second stage (gate run-start-refusal, G4): both drivers
hand it the files a run is about to start from, and what `refuses` stops the run before the chronicle is opened.
`table` renders the declarations as the rows the blueprints carry between their GENERATED markers, so the docs
cannot drift from the checker.

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

import copy
import difflib
import importlib
from dataclasses import dataclass
from typing import Callable, Optional

from .records import RecordError

STATUSES = ("active", "retired", "unread", "runtime")
KINDS = ("section", "map", "list", "text", "unit", "signed", "number", "bool",
         "word", "word|unit", "word|number", "prose", "any", "delegated")
COVERING = ("prose", "any", "delegated")              # a declaration that answers for everything beneath it


@dataclass(frozen=True)
class Field:
    """One declared path. `path` is dotted; a segment ending `[]` is a list's items; `<PATH>` `<PRIMITIVE>`
    `<OLD_AXIS>` are keys from the named engine vocabulary (see PLACEHOLDERS); `<id>` `<name>` are any key."""
    path: str
    kind: str
    status: str = "active"
    required: str = ""                     # "always", or a system's name: absent is an error (while that one runs)
    system: str = ""                       # the system that owns it: off, it is neither demanded nor checked - so only
                                           # a block nothing reads while its system is off carries one (strip empties
                                           # condition and body; every injuries reader is gated on the system); wounds
                                           # and attitude are stamped and folded before strip, so they carry none
    blank: Optional[bool] = None           # a blank here is read as absent (None: by kind - see _blank_absent)
    vocab: str = ""                        # word kinds: "module.CONSTANT", read by heritable.word
    check: Optional[Callable] = None       # f(value, sheet, ctx): raises -> an error; returns text -> advice
    replaced_by: str = ""                  # retired: what took its place ("{successor}" = the placeholder's mapping)
    policy: str = ""                       # retired: prune | move | refuse
    reader: str = ""                       # where the engine reads it
    doc: str = ""                          # what it is, one line
    absent: str = ""                       # advice when an optional field is absent; "" says nothing


# the engine vocabularies a placeholder names - resolved at call time, never copied here
PLACEHOLDERS = {"<PATH>": ("records", "PATHS"), "<PRIMITIVE>": ("records", "RETIRED_PRIMITIVES"),
                "<OLD_AXIS>": ("heritable", "OLD_AXES")}
ANY_KEY = ("<id>", "<name>")


def _vocab(ref):
    mod, _, name = ref.rpartition(".")
    return getattr(importlib.import_module("src.engine." + mod), name)


def _placeholder(seg):
    return _vocab(".".join(PLACEHOLDERS[seg])) if seg in PLACEHOLDERS else None


def ignored(key):
    """An annotation: `_`-prefixed, or `note` - read by nothing, stripped from every prompt."""
    return str(key).startswith("_") or str(key) == "note"


def _split(path):
    return tuple(path.split("."))


def _seg_matches(pat, seg):
    """-> specificity (2 literal, 1 an engine vocabulary, 0 any key) or None."""
    pl, sl = pat.endswith("[]"), seg.endswith("[]")
    if pl != sl:
        return None
    p, s = (pat[:-2], seg[:-2]) if pl else (pat, seg)
    if p == s:
        return 2
    if p in PLACEHOLDERS:
        return 1 if s in _placeholder(p) else None
    return 0 if p in ANY_KEY else None


def match(segs, fields):
    """The most specific declaration of a concrete path, or None."""
    best, score = None, None
    for f in fields:
        pat = _split(f.path)
        if len(pat) != len(segs):
            continue
        sc = [_seg_matches(p, s) for p, s in zip(pat, segs)]
        if None in sc:
            continue
        if score is None or sc > score:
            best, score = f, sc
    return best


def _successor(f, segs):
    """`replaced_by` in this path's own words: a placeholder becomes the key it matched, and `{successor}` the
    key's mapping in its vocabulary (the old primitive's path)."""
    out = f.replaced_by
    for p, s in zip(_split(f.path), segs):
        p, s = p[:-2] if p.endswith("[]") else p, s[:-2] if s.endswith("[]") else s
        src = _placeholder(p)
        if isinstance(src, dict) and s in src:
            out = out.replace("{successor}", str(src[s]))
        if p in PLACEHOLDERS:
            out = out.replace(p, s)
    return out


def _shape_error(f, v):
    """-> why `v` is not of the field's kind, or ''."""
    num = isinstance(v, (int, float)) and not isinstance(v, bool)
    k = f.kind
    if k in ("section", "map"):
        return "" if isinstance(v, dict) else "must be an object"
    if k == "list":
        return "" if isinstance(v, list) else "must be a list"
    if k == "text":
        return "" if isinstance(v, str) else "must be text"
    if k == "bool":
        return "" if isinstance(v, bool) else "must be true or false"
    if k == "number":
        return "" if num else "must be a number"
    if k == "unit":
        return "" if num and 0.0 <= v <= 1.0 else "must be a number in [0,1]"
    if k == "signed":
        return "" if num and -1.0 <= v <= 1.0 else "must be a number in [-1,1]"
    if k.startswith("word"):
        if num and (k == "word|number" or (k == "word|unit" and 0.0 <= v <= 1.0)):
            return ""
        from .heritable import word
        words = tuple(_vocab(f.vocab))
        return "" if isinstance(v, str) and word(v, default="") in words else (
            "must lead with one of %s%s" % ("|".join(words), "" if k == "word" else ", or be a number"))
    return ""


def _prose_errors(v, segs):
    """A subtree the actor reads verbatim: text, lists and objects of it, or a number in [0,1] (banded)."""
    if isinstance(v, dict):
        return [e for k, x in v.items() if not ignored(k) for e in _prose_errors(x, segs + (str(k),))]
    if isinstance(v, list):
        return [e for x in v for e in _prose_errors(x, segs[:-1] + (segs[-1] + "[]",))]
    if isinstance(v, bool) or (isinstance(v, (int, float)) and not 0.0 <= v <= 1.0):
        return [(segs, "reaches the actor verbatim: a number here must be in [0,1] (it is banded to words)")]
    return []


def _finding(severity, code, segs, message):
    return {"severity": severity, "code": code, "path": ".".join(segs), "message": message}


def _walk(node, segs, fields, out, sheet, ctx):
    for key, value in (node.items() if isinstance(node, dict) else ()):
        if ignored(key):
            continue
        here = segs + (str(key),)
        _visit(value, here, fields, out, sheet, ctx)


def _visit(value, segs, fields, out, sheet, ctx):
    f = match(segs, fields)
    if f is None:
        sib = {_split(x.path)[-1] for x in fields if len(_split(x.path)) == len(segs)
               and all(_seg_matches(p, s) is not None for p, s in zip(_split(x.path)[:-1], segs[:-1]))}
        near = difflib.get_close_matches(segs[-1], sorted(k for k in sib if not k.startswith("<")), n=1)
        out.append(_finding("unknown", "CONTRACT_FIELD_UNKNOWN", segs, "is not declared - nothing reads it%s; an "
                            "annotation begins with `_`" % ("; did you mean %r?" % near[0] if near else "")))
        return
    if f.system and f.system not in ctx.get("systems", ()):
        return                                          # nothing reads it while its system is off
    if f.status == "retired":
        # judged by its PRESENCE, whatever it holds: the engine refuses some of these keys on sight (an old primitive
        # in the mood, a rest in the genotype), so an emptied one is deleted, not left
        out.append(dict(_finding("retired", "CONTRACT_FIELD_RETIRED", segs, "is RETIRED: replaced by %s (policy: %s)"
                                 % (_successor(f, segs), f.policy)), policy=f.policy))
        return
    if f.status == "unread":
        out.append(_finding("unread", "CONTRACT_FIELD_UNREAD", segs, "is read by nothing - it reaches no prompt and "
                            "computes nothing%s" % ("; " + f.doc if f.doc else "")))
        return
    if (value is None and not segs[-1].endswith("[]")) or (
            isinstance(value, str) and not value.strip() and _blank_absent(f, value)):
        return          # not authored: absence is the required check's (a null ITEM is no absence - it is a bad item)
    why = _shape_error(f, value)
    if why:
        out.append(_finding("error", "CONTRACT_FIELD_TYPE", segs, "%s, got %s" % (why, _short(value))))
        return
    if f.kind == "prose":
        for where, msg in _prose_errors(value, segs):
            out.append(_finding("error", "CONTRACT_FIELD_TYPE", where, msg))
    _hook(f, value, segs, out, sheet, ctx)
    if isinstance(value, dict) and f.kind not in COVERING:
        _walk(value, segs, fields, out, sheet, ctx)
    elif isinstance(value, list) and f.kind == "list":
        item = segs[:-1] + (segs[-1] + "[]",)
        own = match(item, fields)                      # items declared as such (a delegated row) are visited whole
        for x in value:
            if own is not None:
                _visit(x, item, fields, out, sheet, ctx)
            elif isinstance(x, dict):
                _walk(x, item, fields, out, sheet, ctx)


def _hook(f, value, segs, out, sheet, ctx):
    """A field's own check: the engine module that reads it refuses (-> an error carrying its message), or says
    something about a well-shaped value (-> advice). -> whether it said anything."""
    ctx = ctx or {}
    if f.check is None:                                 # (a switched-off system's fields never reach here)
        return False
    try:
        said = f.check(value, sheet, ctx)
    except (RecordError, ValueError) as e:
        out.append(_finding("error", "CONTRACT_FIELD_REFUSED", segs, "%s%s" % (
            e, " (this book runs the %s system)" % f.system if f.system else "")))
        return True
    except (TypeError, AttributeError, KeyError, IndexError) as e:
        # a value of a shape its reader cannot even walk: refused by name, never a traceback out of a run's start
        out.append(_finding("error", "CONTRACT_FIELD_TYPE", segs, "is not the shape its reader takes (%s: %s)"
                            % (type(e).__name__, e)))
        return True
    if said:
        out.append(_finding("advice", "CONTRACT_FIELD_ADVICE", segs, str(said)))
    return bool(said)


def _blank_absent(f, value):
    """Whether a blank here is read as absent, by what its reader does with one: a word field's reader
    (heritable.word) takes any blank as its default; a text or prose reader takes "" (`or default`) but not spaces
    (a pov of spaces is written to the scene row); a field that says otherwise (`blank`) is taken at its word."""
    if f.blank is not None:
        return f.blank
    return f.kind.startswith("word") or (value == "" and f.kind in ("text", "prose"))


def _short(v):
    s = repr(v)
    return s if len(s) <= 40 else s[:37] + "..."


def _get(sheet, segs):
    node = sheet
    for s in segs:
        if not isinstance(node, dict) or s not in node:
            return None, False
        node = node[s]
    return node, True


def _needed(f, systems):
    """Demanded now: always, or while the system `required` names runs - never while the system that owns it is off."""
    if f.system and f.system not in systems:
        return False
    return f.required == "always" or bool(f.required and f.required in systems)


def _authored(value):
    """Whether a value says anything: not null, not blank text, not an empty list. An empty OBJECT is said on
    purpose - `{}` is "none of these", which its readers take as their defaults (a blank skills block, a condition
    block with neither key) - so it is present, and the field's advice, if it has one, says what it costs."""
    if value is None or value == []:
        return False
    return bool(value.strip()) if isinstance(value, str) else True


def _must_carry(f, fields, systems):
    """The keys a field holds that a book must author -> [field] (an empty mood lacks all nine paths)."""
    n = len(_split(f.path)) + 1
    return [g for g in fields if g.status == "active" and len(_split(g.path)) == n and g.path.startswith(f.path + ".")
            and _needed(g, systems)]


def _missing(f, carry):
    """What an absent required field, or an empty one that must carry keys, is told - naming the system that asks."""
    if carry:
        asks = sorted({g.required for g in carry if g.required not in ("", "always")})
        return "is required and empty - it must carry %s%s" % (
            ", ".join(_split(g.path)[-1].replace("<PATH>", "every path") for g in carry),
            " (this book runs the %s system)" % ", ".join(asks) if asks else "")
    asks = f.required if f.required != "always" else f.system
    return "is required%s and absent" % (" (this book runs the %s system)" % asks if asks else "")


def _required(sheet, fields, systems, out):
    """A field a book must author, absent -> an error; one with advice, absent -> advice. `{}` is present (a blank
    skills block: every skill at its default) unless the field holds keys a book must author - an empty mood - when
    it is reported once, as empty, for all of them. A path under an enumerated placeholder is required for every key
    of it (all nine paths); `<id>`/`<name>` paths never are. A switched-off system's fields are not asked for."""
    for f in fields:
        if f.status != "active" or (f.system and f.system not in systems) or not (_needed(f, systems) or f.absent):
            continue
        segs = _split(f.path)
        if any(s.endswith("[]") or s.rstrip("[]") in ANY_KEY for s in segs):
            continue
        concrete = [()]
        for s in segs:
            keys = _placeholder(s) if s in PLACEHOLDERS else (s,)
            concrete = [c + (k,) for c in concrete for k in keys]
        for c in concrete:
            parent, there = _get(sheet, c[:-1])
            if not there or not isinstance(parent, dict) or (parent == {} and c[:-1]):
                continue                                   # an absent or empty parent is reported once, there
            value, present = _get(sheet, c)
            carry = _must_carry(f, fields, systems) if value == {} else []
            if present and _authored(value) and not carry:
                if value == {} and f.absent:
                    out.append(_finding("advice", "CONTRACT_FIELD_ABSENT", c, f.absent))
                continue
            if _needed(f, systems):
                # a delegated block's own module says why in its own words (BODY_STRENGTH_MISSING); if it says
                # nothing, the absence is still reported
                if not (f.kind == "delegated" and _hook(f, value, c, out, sheet, {"systems": systems})):
                    out.append(_finding("error", "CONTRACT_FIELD_MISSING", c, _missing(f, carry)))
            else:
                out.append(_finding("advice", "CONTRACT_FIELD_ABSENT", c, f.absent))


def check(sheet, fields, systems=(), ctx=None):
    """-> [finding] for one file against its declarations: {severity, code, path, message}, severity one of
    error | retired | unread | unknown | advice. Reports; never raises on the file's content, and never changes it:
    the checks run on a copy (a module's own validator may normalise what it reads - tensions turn a temperature word
    into its number - and the run pins the file as its author wrote it)."""
    out = []
    if not isinstance(sheet, dict):
        return [_finding("error", "CONTRACT_FIELD_TYPE", (), "the file's engine block must be an object")]
    sheet = copy.deepcopy(sheet)
    ctx = dict(ctx or {}, systems=set(systems or ()))
    _walk(sheet, (), fields, out, sheet, ctx)
    _required(sheet, fields, set(systems or ()), out)
    return out


# ---- run start (gate run-start-refusal, G4 of the contracts plan) ---------------------------------------------------
# WHAT STOPS A RUN, before its chronicle is opened (a schema migration, one way) or a beat is paid for. An error: a
# field the engine would misread, or a required one absent. An undeclared key: a typo loses what it held, and a free
# key carries something its author believes reaches the actor, which it does not. A retired field whose content must
# MOVE (where it stands it is ignored) or which the owner REFUSED. What loses nothing - a pruned field, an unread one,
# advice - is counted in one line and never refused; the linters list it.
def refuses(finding):
    """Whether a finding stops a run at its start."""
    sev = finding["severity"]
    return sev in ("error", "unknown") or (sev == "retired" and finding.get("policy") in ("move", "refuse"))


def require_at_start(world, sheets, scene=None, scene_name="the scene file"):
    """The files a run is about to start from, each against its contract -> one line counting what was not refused
    ("" when nothing was found). `world` the world note's engine block; `sheets` {id: sheet} for the characters who
    PLAY (no beat of this run reads anyone else's; the bible still pins every sheet); `scene` the scene file AS
    WRITTEN - the loader rewrites it - or None (the chair). Raises CONTRACT_RUN_REFUSED naming every finding that
    stops it: file, path, its words. Changes nothing it is handed."""
    from . import attachments, contracts_scene, contracts_sheet, contracts_world, systems
    try:
        on, guessed = systems.for_book(world), False
    except (RecordError, ValueError):                   # the world's own check below names the bad declaration
        on, guessed = systems.defaults(), True
    try:
        registered = attachments.names_for(world)
    except (RecordError, ValueError, TypeError):        # the world's own check names the bad locations or groups;
        registered = None                               # None: the holds are not checked against a register
    files = [("world", world, contracts_world.WORLD, None)]
    files += [(cid, sheets[cid], contracts_sheet.SHEET, {"registered": registered}) for cid in sorted(sheets)]
    if scene is not None:
        files.append((scene_name, scene, contracts_scene.SCENE, None))
    stops, kept = {}, {}
    for name, value, fields, ctx in files:
        for f in check(value, fields, on, ctx):
            if refuses(f):
                line = "%s: %s" % (name, " ".join(x for x in (f["path"], f["message"]) if x))
                stops[line] = stops.get(line, 0) + 1
            else:
                kept[f["severity"]] = kept.get(f["severity"], 0) + 1
    if stops:
        raise RecordError("CONTRACT_RUN_REFUSED", "the run cannot start: %d thing(s) in its files are not what the "
                          "engine reads, and nothing has been written -\n%s\n%s  scripts/lint_book.py and "
                          "scripts/lint_scene.py list the same, with what reaches nothing" % (len(stops), "\n".join(
                              "  %s%s" % (line, " (x%d)" % n if n > 1 else "") for line, n in stops.items()),
                              "  (world.systems could not be read, so the sheets were checked against the default "
                              "systems - fix it, and a system it turns on may ask for more)\n" if guessed else ""))
    return ("contract: nothing refused; %s - scripts/lint_book.py and scripts/lint_scene.py list them" % ", ".join(
        "%d %s" % (n, sev) for sev, n in sorted(kept.items()))) if kept else ""


def table(fields):
    """The declarations as markdown rows - what the blueprints carry between their GENERATED markers."""
    rows = ["| field | shape | must author | status | read by | what it is |", "|---|---|---|---|---|---|"]
    for f in fields:
        runs = f.required if f.required not in ("", "always") else f.system
        need = ("when the book runs %s" % runs if runs else "yes") if f.required else "no"
        where = f.reader or ("-" if f.status != "retired" else "replaced by %s (%s)" % (
            f.replaced_by.replace("{successor}", "the one records.RETIRED_PRIMITIVES names"), f.policy))
        cells = (f.kind.replace("|", " or ") + (" (%s)" % f.vocab if f.vocab else ""), need, f.status, where, f.doc or "")
        rows.append("| `%s` | %s |" % (f.path, " | ".join(c.replace("|", "\|") for c in cells)))
    return "\n".join(rows)
