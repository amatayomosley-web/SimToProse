"""tellings.py — what a character is TOLD becomes what they know (gate knowledge-tellings, 2026-09-29).

The owner's model (2026-09-28): a person's knowledge is the set of facts they are linked to, and what is told in play
writes new links sourced to the teller. The producer already ran: since 2026-09-18 the event seat reports each beat's
`told` rows - [{what, to, cost}], `what` a span of that beat's own action - and they reached two readers only:
`scene_facts` (a few beats of in-run facts, shown to whoever was in the room) and `bonds` (trust arithmetic). What a
hearer was told never became something they KNEW: nothing in their vault, nothing `read_api.knows` could return, nothing
a later scene could bring to mind.

A telling is heard by everyone in the room but the teller - the addressee and anyone who overheard. Each hearer credits
it by their own trust in the teller, through `acquisition.credit` (the one spelling a witnessed account already uses):
at or below its reported line the hearer keeps it as "<Name> claims: ..."; above it, as the claim itself, told by that
person, never above the ceiling that keeps a told thing short of certainty (Fable review 3, 8.3).

THREE DECISIONS, each named where it lives:
  * IDENTITY FROM THE EVENT (Fable M5): every hearer's copy of one telling carries one `fact` id, made from the beat and
    the row - so "who holds this fact" is one query, whatever each hearer made of it. The claim is the seat's quote,
    holder-neutral; the hearer's phrasing ("claims:") and provenance are the link's.
  * READINESS IS NOT SURENESS (Fable 8.3): a told belief carries `readiness` - how readily the hearing comes back - apart
    from `confidence`, how far it is believed. Recall is priced by readiness (`associative._ready`), the prompt renders
    confidence, so village gossip can be vivid and doubted at once instead of doubted AND buried.
  * TOLD TOGETHER COMES BACK TOGETHER through the teller: every telling links the person who told it, so bringing one
    thing Jory said to mind reaches the rest of what he said by the graph's own hops (the drag, associative.py) -
    what the owner asked for ("memory doesn't work only by recalling one specific thing"). A separate per-beat
    anchor was built first and taken out: the mutant that removed it survived, because the teller already joins them.

Stores: the acquisitions log, which resume, `read_api.knows` and `ask.py who` already fold - no second table for the
same relation (Fable M6). Deterministic, stdlib only, no LLM.
"""
from .acquisition import _WITNESS_BASE, credit
from .facets import stamp as _stamp_facets

# How readily a hearing comes back, whatever the hearer makes of the teller: a telling is as vivid as an act witnessed
# at neutral trust. [JUDGMENT] - the witnessed account's own neutral value, so the two ways of learning from another
# person price alike; decay takes it from there like any durable memory.
READINESS = _WITNESS_BASE
_SELF = "self"


def told_beliefs(rows, teller, teller_name, hearers, trust_of, turn, world=None):
    """One beat's `told` rows -> {hearer_id: [belief, ...]}.

    `rows` is the event seat's list; a row with no `what` is skipped (the seat's parser already refuses a malformed
    reply, and a --stub beat's own tags may carry nothing). `hearers` are the ids in the room; the teller is never
    their own hearer. `trust_of(hearer)` is that hearer's trust in the teller, or None for no edge (neutral credit).
    """
    out = {}
    for i, row in enumerate(rows or []):
        if not isinstance(row, dict):
            continue
        what = str(row.get("what") or "").strip()
        if not what:
            continue
        to = str(row.get("to") or "").strip()
        told = {"by": str(teller), "to": str(teller) if to.lower() == _SELF else to, "turn": int(turn),
                "cost": str(row.get("cost") or "none").strip().lower()}
        for h in hearers:
            if not h or h == teller:
                continue
            conf, reported = credit(trust_of(h))
            name = str(teller_name or teller)
            b = _stamp_facets({
                "claim": ("%s claims: %s" % (name, what)) if reported else what,
                "confidence": conf,
                "readiness": READINESS,
                "provenance": "reported" if reported else "told by %s" % name,
                "durability": "durable",
                "believed_value": True,
                "links": [str(teller)],
            }, world)
            b["told"] = dict(told)
            b["fact"] = "told.%d.%s.%d" % (int(turn), teller, i)
            b["created_turn"] = int(turn)
            out.setdefault(h, []).append(b)
    return out
