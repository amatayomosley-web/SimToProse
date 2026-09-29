"""knowledge.py — what a group knows, written once, linked to each member (gate knowledge-links, 2026-09-28).

THE OWNER'S MODEL (2026-09-28): a person's knowledge is the set of facts they are LINKED to. A fact a whole village
holds is written ONCE, in the world, with the groups that hold it; a character who belongs to one of those groups is
linked to it when the book loads. Groups believe nothing — they are how links are made. And what is familiar belongs
to the PERSON, not the fact: "What's familiar to a tax collector may be obscure for a farmer." So each link carries its
own familiarity word, and a member who LEFT holds only what the group knew before they left, aged by how long ago that
was — "last saw him ten years ago" is a link's age, and a later death is a fact the link-maker never reached.

THE REGISTRY IS THE ONE THAT EXISTS (Fable review 3, M1): a group is `grp.<people[].groups tag>` and a place is
`loc.<locations id>`, exactly `attachments.names_for`; the domain is the lexicon's attribute classes (`topics`, the
words `facets` already stamps). No parallel registry.

WHAT A LINK IS: a vault belief like any other — decay, the gate, the bible pin and the prompt already carry it — with
keys of its own: `shared` (the holder that made it), `familiarity`, `learned_days` (a member who left: how long since
they last shared the group's life), and the fact's topic and about-names in `links`, so today's matcher reaches it.

AGE IS READINESS, NOT SURENESS (Fable review 3, 8.3: they are two quantities). `learned_days` does NOT feed decay:
decay's per-day retention takes anything a year old to its floor, which would render "Ambrose is sheriff" as doubt when
Aren is sure of it — his knowledge is OLD, not uncertain. The age is told to the actor in words ("you last knew it
years ago") and priced through the `faded` familiarity, so an old link comes to mind less readily, and not when tired.

WHY A PRICE OF ITS OWN (Fable review 3, B1, reproduced 2026-09-28): a belief's recall cost is 1 - confidence, so a
fact written confident costs nearly nothing, and the gate orders by confidence — 150 shared facts at .90 took every
slot from a character's own memory at .70, at every budget. A shared link costs at least SHARED_FLOOR plus its
familiarity's price, is recalled from its OWN budget after the character's own memories, and at most SHARED_SLOTS of
them reach one beat. A character's own beliefs keep today's law untouched, so a book without shared knowledge recalls
exactly as before.
"""
from .records import RecordError

FAMILIARITY = ("everyday", "familiar", "faded")
# what familiarity adds to a shared link's recall cost [JUDGMENT, gate knowledge-links - tune by running scenes,
# relevancy-gate.md "calibrate, don't guess"]
PRICE = {"everyday": 0.0, "familiar": 0.10, "faded": 0.25}
# the least a shared link costs; a lived memory at .90 costs .10, so at equal confidence a shared link prices ABOVE a
# lived one (Fable review 3, B1 fix iv) [JUDGMENT]
SHARED_FLOOR = 0.15
# shared links one beat can recall, in their own budget [JUDGMENT - today's beats bring up four or five of a
# character's own memories (Fable review 3, measured on three run databases)]
SHARED_SLOTS = 3
# a group's knowledge in a member's head when the world names no number: sure, and one band below "you do not
# entertain the alternative" (direction._SURENESS turns at .90) [JUDGMENT]
KNOWN_CONFIDENCE = 0.85
_DAYS = {"d": 1.0, "w": 7.0, "y": 365.0}
# how long ago, in words: no digit reaches the prompt (hard rule 5) [JUDGMENT]
AGE_BANDS = ((30.0, "lately"), (365.0, "within the past year"), (5 * 365.0, "some years back"),
             (20 * 365.0, "years ago"))
AGE_OLDEST = "long ago"
_LOC, _GRP = "loc.", "grp."


def days(span, where="a span"):
    """An authored age -> days. "<n>d", "<n>w" or "<n>y" (a year is 365 days); a bare number is days."""
    if isinstance(span, bool):
        raise RecordError("KNOWLEDGE_AGE_NOT_A_SPAN", "%s: %r is not an age" % (where, span))
    if isinstance(span, (int, float)):
        n, unit = float(span), 1.0
    else:
        txt = str(span or "").strip().lower()
        unit = _DAYS.get(txt[-1:], None) if txt else None
        try:
            n = float(txt[:-1] if unit else txt)
        except ValueError:
            raise RecordError("KNOWLEDGE_AGE_NOT_A_SPAN",
                              "%s: %r is not an age - write <n>d, <n>w or <n>y" % (where, span))
        unit = unit or 1.0
    if n <= 0:
        raise RecordError("KNOWLEDGE_AGE_NOT_A_SPAN", "%s: an age must be more than nothing, got %r" % (where, span))
    return n * unit


def age_words(learned_days):
    """How long ago a link was last lived, in words; "" for a link with no age."""
    try:
        d = float(learned_days or 0)
    except (TypeError, ValueError):
        return ""
    if d <= 0:
        return ""
    for upto, words in AGE_BANDS:
        if d <= upto:
            return words
    return AGE_OLDEST


def _registered(world):
    """Every name a fact may be held by (grp./loc.) and every name it may be about (those, and people ids)."""
    from .attachments import names_for
    holders = set(names_for(world))
    about = set(holders)
    for p in (world.get("people") or []):
        if isinstance(p, dict) and p.get("id"):
            about.add(str(p["id"]))
    return holders, about


def validate_world(world):
    """world["knowledge"] -> None, or raise naming the first entry the loader could not link."""
    rows = world.get("knowledge") if isinstance(world, dict) else None
    if rows is None:
        return None
    if not isinstance(rows, list):
        raise RecordError("KNOWLEDGE_NOT_A_LIST", "world.knowledge must be a list of facts, got %s" % type(rows).__name__)
    holders, about = _registered(world)
    classes = set(((world.get("lexicon") or {}).get("attribute_classes") or {}).keys())
    for i, f in enumerate(rows):
        where = "knowledge[%d]" % i
        if not isinstance(f, dict):
            raise RecordError("KNOWLEDGE_ENTRY_NOT_A_DICT", "%s is not an object with a claim and its holders" % where)
        if not str(f.get("claim") or "").strip():
            raise RecordError("KNOWLEDGE_CLAIM_EMPTY", "%s has no claim - there is nothing to know" % where)
        held = f.get("held_by")
        if not isinstance(held, list) or not held:
            raise RecordError("KNOWLEDGE_HELD_BY_EMPTY", "%s names no holder - a fact nobody holds is the author's "
                              "truth, not knowledge; list the groups or places that know it" % where)
        for h in held:
            if str(h) not in holders:
                raise RecordError("KNOWLEDGE_HOLDER_UNREGISTERED", "%s: holder %r is not a registered group or place "
                                  "(grp.<a people[].groups tag> or loc.<a locations id>)" % (where, h))
        for a in (f.get("about") or []):
            if str(a) not in about:
                raise RecordError("KNOWLEDGE_ABOUT_UNREGISTERED", "%s: %r is not a person, place or group this world "
                                  "registers - register it with the fact" % (where, a))
        if f.get("topic") is not None and str(f["topic"]) not in classes:
            raise RecordError("KNOWLEDGE_TOPIC_UNKNOWN", "%s: topic %r is not a lexicon attribute class" % (where, f["topic"]))
        if f.get("since") is not None:
            days(f["since"], where + ".since")
        if f.get("confidence") is not None:
            c = f["confidence"]
            if isinstance(c, bool) or not isinstance(c, (int, float)) or not 0.0 < float(c) <= 1.0:
                raise RecordError("KNOWLEDGE_CONFIDENCE_RANGE", "%s: confidence %r is not a number in (0, 1]" % (where, c))
        validate_same_as(f.get("same_as"), {str(p.get("id")) for p in (world.get("people") or [])
                                           if isinstance(p, dict) and p.get("id")}, where)
        if f.get("norm") is not None and not isinstance(f["norm"], bool):
            raise RecordError("KNOWLEDGE_NORM_INVALID", "%s: norm must be true or false, got %r" % (where, f["norm"]))
        if f.get("sanction") is not None:
            if f.get("norm") is not True:
                raise RecordError("KNOWLEDGE_NORM_INVALID", "%s: a sanction belongs to a norm - mark the entry "
                                  "norm: true, or put the consequence in the claim of a plain fact" % where)
            if not isinstance(f["sanction"], str) or not f["sanction"].strip():
                raise RecordError("KNOWLEDGE_NORM_INVALID", "%s: a sanction is words - what breaking the norm costs, "
                                  "got %r" % (where, f["sanction"]))
    return None


def validate_same_as(value, people, where="a belief"):
    """An identity - `same_as` - -> None, or raise: two or more ids of the world's people, the ids one person goes by.
    `people` None (a caller with no world to hand) checks the shape alone."""
    if value is None:
        return None
    if not isinstance(value, list) or len({str(v) for v in value}) < 2:
        raise RecordError("KNOWLEDGE_SAME_AS_INVALID", "%s: same_as must list two or more ids one person goes by, got %r"
                          % (where, value))
    for v in value:
        if people is not None and str(v) not in people:
            raise RecordError("KNOWLEDGE_SAME_AS_INVALID", "%s: same_as names %r, who is not among the world's people - "
                              "each identity is a people[] entry of its own" % (where, v))
    return None


def same_ids(vault):
    """The ids a character holds as ONE person -> {id: the id it is joined under} (Fable review 3, M3; gate
    knowledge-identity). An identity is itself a belief - `same_as: [maudie, brisk]` (the beekeeper is the
    basket-seller), on a sheet or linked from a group's knowledge - and it joins the ids for whoever HOLDS it, never
    for anyone else: to everyone else the beekeeper and the basket-seller stay two people. `about` is the knower's
    referent, so this is where a knower's two referents become one. Deterministic: the lesser id is the one the
    others join under."""
    parent = {}

    def root(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x
    for b in vault or []:
        if not isinstance(b, dict) or b.get("status") in ("superseded", "refuted"):
            continue
        ids = [str(i).strip().lower() for i in b.get("same_as") or [] if str(i).strip()] \
            if isinstance(b.get("same_as"), list) else []
        for i in ids:
            parent.setdefault(i, i)
        for other in ids[1:]:
            a, c = root(ids[0]), root(other)
            if a != c:
                parent[max(a, c)] = min(a, c)
    return {x: root(x) for x in parent}


def validate_memberships(rows, registered):
    """A sheet's current.memberships -> None, or raise naming the first membership the loader could not read."""
    if rows is None:
        return None
    if not isinstance(rows, list):
        raise RecordError("KNOWLEDGE_MEMBERSHIPS_NOT_A_LIST", "current.memberships must be a list")
    names = None if registered is None else set(registered)      # None: no world to check against (shape only)
    for i, m in enumerate(rows):
        where = "current.memberships[%d]" % i
        if not isinstance(m, dict):
            raise RecordError("KNOWLEDGE_MEMBERSHIP_NOT_A_DICT", "%s is not an object with `of`" % where)
        if names is not None and str(m.get("of") or "") not in names:
            raise RecordError("KNOWLEDGE_MEMBERSHIP_UNREGISTERED", "%s: %r is not a registered group or place "
                              "(grp.<tag> or loc.<id>)" % (where, m.get("of")))
        if m.get("left") is not None:
            days(m["left"], where + ".left")
        if m.get("familiarity") is not None and m["familiarity"] not in FAMILIARITY:
            raise RecordError("KNOWLEDGE_FAMILIARITY_UNKNOWN", "%s: familiarity %r is not one of %s"
                              % (where, m["familiarity"], ", ".join(FAMILIARITY)))
    return None


def _display(name, world):
    """A holder's name as a person would say it: a place's `name` (or its id), a group's tag in words."""
    if name.startswith(_LOC):
        lid = name[len(_LOC):]
        for loc in (world.get("locations") or []):
            if isinstance(loc, dict) and str(loc.get("id") or "") == lid:
                return str(loc.get("name") or lid.replace("_", " ").title())
        return lid.replace("_", " ").title()
    return "the " + name[len(_GRP):].replace("-", " ").replace("_", " ")


def _niche_topics(char, world):
    """The lexicon classes a character's own position names: their everyday domains."""
    from .facets import topics_in
    pos = (char.get("fixed") or {}).get("position")
    text = " ".join(str(v) for v in pos.values()) if isinstance(pos, dict) else str(pos or "")
    return set(topics_in(text, world)) if text.strip() else set()


def _safe_days(span):
    try:
        return days(span) if span is not None else None
    except RecordError:
        return None


def links_for(char, world):
    """One character's links: one vault belief per fact held by a group or place they belong to - and, for a
    membership that ended, only facts the group knew before they left. Malformed entries are skipped here and
    reported by the contracts at lint and at a run's start (a draft loads whatever its shape)."""
    facts = world.get("knowledge") if isinstance(world, dict) else None
    cur = char.get("current") if isinstance(char, dict) else None
    members = cur.get("memberships") if isinstance(cur, dict) else None
    if not isinstance(facts, list) or not isinstance(members, list):
        return []
    everyday = _niche_topics(char, world)
    out = []
    for m in members:
        if not isinstance(m, dict) or not m.get("of"):
            continue
        holder, left = str(m["of"]), _safe_days(m.get("left"))
        for f in facts:
            if not isinstance(f, dict) or holder not in [str(h) for h in (f.get("held_by") or [])]:
                continue
            claim = str(f.get("claim") or "").strip()
            if not claim:
                continue
            since = _safe_days(f.get("since"))
            if left is not None and since is not None and since <= left:
                continue                                  # the group learned it after this member left
            # A NORM (gate knowledge-norms): the way a group does things, and what breaking it costs. A member lives by it
            # every day whatever their trade, and it does not fade - a custom is replaced when you move, not forgotten
            # (the design's "norms do not decay"): so `core`, told as "the way of" the group, the sanction beside it.
            norm = f.get("norm") is True
            if m.get("familiarity") in FAMILIARITY:
                fam = m["familiarity"]
            elif left is not None:
                fam = "faded"
            elif norm or (f.get("topic") and str(f["topic"]) in everyday):
                fam = "everyday"
            else:
                fam = "familiar"
            if norm and str(f.get("sanction") or "").strip():
                claim = "%s %s" % (claim, str(f["sanction"]).strip())
            tail = holder.split(".", 1)[1]
            link = {"claim": claim, "confidence": float(f.get("confidence") or KNOWN_CONFIDENCE),
                    "provenance": ("the way of %s" if norm else "known in %s") % _display(holder, world),
                    "durability": "core" if norm else "durable",
                    "links": sorted({str(a) for a in (f.get("about") or [])} | ({str(f["topic"])} if f.get("topic") else set())
                                    | {tail}),
                    "shared": holder, "familiarity": fam}
            if left is not None:
                link["learned_days"] = left
            if isinstance(f.get("same_as"), list):
                link["same_as"] = [str(i) for i in f["same_as"]]      # an identity the group holds, joined for its members
            if norm:
                link["norm"] = holder
            for key in ("evidence", "source"):          # the note's words it was kept from (scripts/facts.py approve)
                if isinstance(f.get(key), str) and f[key].strip():
                    link[key] = f[key]
            out.append(link)
    return out


def validate_last_seen(value):
    """A relationship edge's `last_seen` -> None, or raise: an age like any other (<n>d, <n>w, <n>y)."""
    if value is not None:
        days(value, "last_seen")
    return None


def acquaintances(char, world):
    """A DATED ACQUAINTANCE (Fable review 3, M4; gate knowledge-fold): for each relationship edge that says when the
    character last saw that person (`last_seen`), one belief of their own - "You know Ambrose: the sheriff of Millbrook." -
    about that person, lived, and aged. The edge stays the feeling; this is the knowing, and it is what a scene's
    mention of an absent person reaches. An edge with no `last_seen` adds nothing (the edge itself renders when the
    person is present)."""
    cur = char.get("current") if isinstance(char, dict) else None            # a draft loads whatever its shape:
    rels = cur.get("relationships") if isinstance(cur, dict) else None       # a malformed sheet is the contracts'
    if not isinstance(rels, dict):                                           # finding, never a crash at load
        return []
    roster = world.get("people") if isinstance(world, dict) else None
    people = {str(p.get("id")): p for p in (roster if isinstance(roster, list) else []) if isinstance(p, dict) and p.get("id")}
    out = []
    for pid, edge in rels.items():
        if not isinstance(edge, dict):
            continue
        ago = _safe_days(edge.get("last_seen"))
        if ago is None:
            continue
        p = people.get(str(pid), {})
        name = str(p.get("name") or str(pid).replace("_", " ").title())
        what = str(p.get("what") or "").strip()
        out.append({"claim": "You know %s%s." % (name, (": " + what) if what else ""), "confidence": 0.9,
                    "provenance": "lived", "durability": "durable", "links": [str(pid)],
                    "acquaintance": str(pid), "learned_days": ago})
    return out


def materialise(world, chars):
    """Link every character to what their groups hold and to the people they last saw long ago, appending to
    current.vault -> {char_id: links added}."""
    added = {}
    for cid, char in (chars or {}).items():
        links = links_for(char, world or {}) + acquaintances(char, world or {})
        if links:
            char["current"] = dict(char["current"], vault=list(char["current"].get("vault") or []) + links)
        added[cid] = len(links)
    return added


def shared_cost(belief, cost):
    """A shared link's recall cost: never below SHARED_FLOOR, plus what its familiarity adds."""
    return max(float(cost), SHARED_FLOOR) + PRICE.get(belief.get("familiarity"), PRICE["familiar"])


def knows_about(char, name):
    """The beliefs in a character's vault about `name` (a person id, a place or group tail, or a registered name) - and,
    for someone who holds that two ids are one person (`same_as`), about that person under either."""
    vault = ((char or {}).get("current") or {}).get("vault") or []
    same = same_ids(vault)
    want = str(name).split(".", 1)[-1].lower()
    want = same.get(want, want)
    return [b for b in vault if isinstance(b, dict) and
            want in {same.get(t, t) for t in (str(x).split(".", 1)[-1].lower()
                                               for x in (b.get("links") or []) + (b.get("about") or []))}]
