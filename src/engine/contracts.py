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
`scene._strip_notes` applies. `check` walks a file against the declarations and REPORTS; nothing here refuses
(refusal at run start is a later gate, after the owner's books have migrated). `table` renders the declarations
as the rows the blueprints carry between their GENERATED markers, so the docs cannot drift from the checker.

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

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
    required: str = ""                     # "always": absent is an error (while its system, if any, runs)
    system: str = ""                       # the system that owns it: off, it is neither demanded nor checked
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
    if f.status == "retired":
        out.append(_finding("retired", "CONTRACT_FIELD_RETIRED", segs, "is RETIRED: replaced by %s (policy: %s)"
                            % (_successor(f, segs), f.policy)))
        return
    if f.status == "unread":
        out.append(_finding("unread", "CONTRACT_FIELD_UNREAD", segs, "is read by nothing - it reaches no prompt and "
                            "computes nothing%s" % ("; " + f.doc if f.doc else "")))
        return
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
    something about a well-shaped value (-> advice). Skipped for a system the book does not run. -> whether it
    said anything."""
    ctx = ctx or {}
    if f.check is None or (f.system and f.system not in ctx.get("systems", ())):
        return False
    try:
        said = f.check(value, sheet, ctx)
    except (RecordError, ValueError) as e:
        out.append(_finding("error", "CONTRACT_FIELD_REFUSED", segs, "%s%s" % (
            e, " (this book runs the %s system)" % f.system if f.system else "")))
        return True
    if said:
        out.append(_finding("advice", "CONTRACT_FIELD_ADVICE", segs, str(said)))
    return bool(said)


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
    return f.required == "always" and (not f.system or f.system in systems)


def _required(sheet, fields, systems, out):
    """A field a book must author, absent -> an error; one with advice, absent -> advice. A path under an
    enumerated placeholder is required for every key of it (all nine paths); `<id>`/`<name>` paths never are."""
    for f in fields:
        if f.status != "active" or not (_needed(f, systems) or f.absent):
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
            if not there or parent in (None, "", [], {}):
                continue                                   # its parent's own absence is reported once, there
            value, present = _get(sheet, c)
            if present and value not in (None, "", [], {}):
                continue
            if _needed(f, systems):
                # a delegated block's own module says why in its own words (BODY_STRENGTH_MISSING); if it says
                # nothing, the absence is still reported
                if not (f.kind == "delegated" and _hook(f, value, c, out, sheet, {"systems": systems})):
                    out.append(_finding("error", "CONTRACT_FIELD_MISSING", c, "is required%s and absent" % (
                        " (this book runs the %s system)" % f.system if f.system else "")))
            else:
                out.append(_finding("advice", "CONTRACT_FIELD_ABSENT", c, f.absent))


def check(sheet, fields, systems=(), ctx=None):
    """-> [finding] for one file against its declarations: {severity, code, path, message}, severity one of
    error | retired | unread | unknown | advice. Reports; never raises on the file's content."""
    out = []
    if not isinstance(sheet, dict):
        return [_finding("error", "CONTRACT_FIELD_TYPE", (), "the file's engine block must be an object")]
    ctx = dict(ctx or {}, systems=set(systems or ()))
    _walk(sheet, (), fields, out, sheet, ctx)
    _required(sheet, fields, set(systems or ()), out)
    return out


def table(fields):
    """The declarations as markdown rows - what the blueprints carry between their GENERATED markers."""
    rows = ["| field | shape | must author | status | read by | what it is |", "|---|---|---|---|---|---|"]
    for f in fields:
        need = ("when the book runs %s" % f.system if f.system else "yes") if f.required == "always" else "no"
        where = f.reader or ("-" if f.status != "retired" else "replaced by %s (%s)" % (
            f.replaced_by.replace("{successor}", "the one records.RETIRED_PRIMITIVES names"), f.policy))
        cells = (f.kind.replace("|", " or ") + (" (%s)" % f.vocab if f.vocab else ""), need, f.status, where, f.doc or "")
        rows.append("| `%s` | %s |" % (f.path, " | ".join(c.replace("|", "\|") for c in cells)))
    return "\n".join(rows)
