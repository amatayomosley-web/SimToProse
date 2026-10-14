"""bands.py — the world's register of bands: groups that exist before anyone belongs to them (gate band-register, 2026-10-13).

WHY. A fact is saved with its holders, and a holder that is a group used to be registered only by a cast member
carrying its tag (`people[].groups`, Fable review 3, M1: "no parallel registry"). So a band could not hold a fact until
the cast reached it, and in a big world most bands are never reached: the owner, 2026-10-13, "the world is so big it
will be easy to forget what the world contains" - a tale saved for one town, then a character from that town written as
never having heard it. The owner's "Yes" (2026-10-13 18:02) reverses M1: a band is written in the world on its own,
registered as `grp.<id>` beside the people[] tags, and holds facts with no member yet. Groups still believe nothing;
they are how links are made (docs/knowledge-model.md).

A BAND: `id` (the name after grp.), `kind` (one of KINDS), `rule` (who belongs, in plain words - required, because it
is what the author checks a person against), and optionally `parent` (another band), `nation` (words), `requires`
({nation, place, role}: the typed half of the rule, which scripts/place.py matches against a sheet - `place` is a
world.locations id) and `defines` (the notes or sheet rows the band is drawn from). Written in the world note's
engine block, or in <book>/bands/*.md notes (`vault.load_book` merges them after the world's own).

Deterministic, stdlib only.
"""
from .records import RecordError

# the kinds a band can be [the owner's list, backlog swe-knowledge-scopes 2026-10-13]
KINDS = ("people", "government", "office", "guild", "order", "conspiracy", "place-folk")
REQUIRES = ("nation", "place", "role")


def rows(world):
    """world["bands"] as a list of dicts, malformed entries skipped (a draft loads whatever its shape; the contract
    reports it)."""
    b = world.get("bands") if isinstance(world, dict) else None
    return [r for r in b if isinstance(r, dict)] if isinstance(b, list) else []


def band_ids(world):
    """Every band id the register names -> ["<id>", ...], in register order."""
    return [str(r["id"]).strip() for r in rows(world) if str(r.get("id") or "").strip()]


def validate_bands(world):
    """world["bands"] -> None, or raise naming the first band the register cannot hold."""
    reg = world.get("bands") if isinstance(world, dict) else None
    if reg is None:
        return None
    if not isinstance(reg, list):
        raise RecordError("BANDS_NOT_A_LIST", "world.bands must be a list of bands, got %s" % type(reg).__name__)
    places = {str(l.get("id")) for l in (world.get("locations") or []) if isinstance(l, dict) and l.get("id")}
    seen = []
    for i, b in enumerate(reg):
        where = "bands[%d]" % i
        if not isinstance(b, dict):
            raise RecordError("BANDS_ENTRY_NOT_A_DICT", "%s is not an object with an id, a kind and a rule" % where)
        bid = str(b.get("id") or "").strip()
        if not bid or "." in bid or any(c.isspace() for c in bid):
            raise RecordError("BANDS_ID_INVALID", "%s: id %r must be one word with no dot - the name after grp." % (where, b.get("id")))
        if bid in seen:
            raise RecordError("BANDS_ID_DUPLICATE", "%s: band %r is already in the register" % (where, bid))
        seen.append(bid)
        if b.get("kind") not in KINDS:
            raise RecordError("BANDS_KIND_UNKNOWN", "%s: kind %r is not one of %s" % (where, b.get("kind"), ", ".join(KINDS)))
        if not isinstance(b.get("rule"), str) or not b["rule"].strip():
            raise RecordError("BANDS_RULE_EMPTY", "%s: band %r has no rule - say in words who belongs to it" % (where, bid))
        req = b.get("requires")
        if req is not None:
            if not isinstance(req, dict) or not req:
                raise RecordError("BANDS_REQUIRES_INVALID", "%s: requires must be an object of %s" % (where, ", ".join(REQUIRES)))
            for k, v in req.items():
                if k not in REQUIRES or not isinstance(v, str) or not v.strip():
                    raise RecordError("BANDS_REQUIRES_INVALID", "%s: requires.%s = %r - the keys are %s, each words"
                                      % (where, k, v, ", ".join(REQUIRES)))
            if "place" in req and req["place"] not in places:
                raise RecordError("BANDS_REQUIRES_INVALID", "%s: requires.place %r is not a world.locations id"
                                  % (where, req["place"]))
        d = b.get("defines")
        if d is not None and (not isinstance(d, list) or not all(isinstance(x, str) and x.strip() for x in d)):
            raise RecordError("BANDS_DEFINES_INVALID", "%s: defines must list the notes or rows the band is drawn from" % where)
    ids = set(seen)
    for i, b in enumerate(reg):
        if b.get("parent") is not None and str(b["parent"]) not in ids:
            raise RecordError("BANDS_PARENT_UNKNOWN", "bands[%d]: parent %r is not a band in the register" % (i, b["parent"]))
    return None
