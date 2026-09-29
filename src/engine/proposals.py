"""proposals.py — facts proposed from a world note, each held to the words it came from (gate knowledge-proposals).

WHY. A world session writes prose: a people's ways, a town's history, what everyone there knows. That prose reaches no
character until each fact is a `knowledge` entry, and typing them by hand is the burden that keeps a world thin. Fable
review 3 (M7) measured three to five admissible facts per kilobyte of world notes, and named how an extractor goes wrong:
it merges two facts into one claim, states author-only truth as if the world knew it, paraphrases, and invents who a
fact is about. The composition pass already answers this for its own classifier - an output must COPY its evidence
sentence and is refused otherwise - and this is that rule for facts. Only the mechanical is checked here; whether a fact
is worth keeping is the author's call, fact by fact.

THE FLOW (scripts/facts.py): `propose` builds the prompt from the note's VISIBLE text -> the partner answers it ->
`check` keeps or refuses each proposal, by name -> the author keeps what he approves, in his own words -> the facts are
written to <book>/knowledge/<note>.md, which `vault.load_book` merges into world.knowledge. The author's own notes are
never written.

AUTHOR-ONLY TRUTH is fenced in a note between a line `%% truth %%` and a line `%% /truth %%` (Obsidian hides `%%`
comments in reading view): the proposer never sees it, and a fact whose evidence quotes it is refused. An unclosed fence
hides the rest of the note (fail closed).

Deterministic, stdlib only, no LLM (hard rule 3).
"""
import json
import re

from .records import RecordError

FENCE_OPEN, FENCE_CLOSE = "%% truth %%", "%% /truth %%"
FIELDS = ("claim", "held_by", "about", "topic", "since", "confidence", "norm", "sanction", "same_as", "evidence")
_FRONT = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
_CODE = re.compile(r"```.*?```", re.DOTALL)
_TWO = re.compile(r"[.!?;](?=\s+[A-Z])")           # a sentence ends and another begins: two facts in one claim


def squash(text):
    return " ".join(str(text or "").split()).lower()


def _split(note_text):
    """A note -> (the visible prose, the fenced author-only truth), frontmatter and code blocks removed from both."""
    t = _CODE.sub("", _FRONT.sub("", str(note_text or ""), count=1))
    seen, hidden, fenced = [], False, []
    for line in t.splitlines():
        s = line.strip()
        if s == FENCE_OPEN:
            hidden = True
            continue
        if s == FENCE_CLOSE:
            hidden = False
            continue
        (fenced if hidden else seen).append(line)
    return "\n".join(seen).strip(), "\n".join(fenced).strip()


def visible_text(note_text):
    """The prose a proposer may see: no frontmatter, no code block (the engine payload), no author-only truth."""
    return _split(note_text)[0]


def _registry(world):
    from .attachments import names_for
    holders = sorted(names_for(world))
    people = sorted(str(p.get("id")) for p in (world.get("people") or []) if isinstance(p, dict) and p.get("id"))
    topics = sorted(((world.get("lexicon") or {}).get("attribute_classes") or {}).keys())
    return holders, people, topics


def prompt(note_id, note_text, world):
    """The proposer's messages for one note: the admission tests, the world's registry and the reply contract."""
    holders, people, topics = _registry(world)
    nl = "\n"
    system = (
        "You propose FACTS for a simulated world, from one of its author's notes. A fact is something a group or place in "
        "this world KNOWS, written once and linked to every member. Keep a sentence of the note as a fact only if:" + nl +
        "- someone in the world could know it (the author's hidden truth is not shown to you, and history nobody in the "
        "world remembers is not knowledge - but what people BELIEVE about it is, even if it is false);" + nl +
        "- knowing it could change what someone does, says or feels;" + nl +
        "- it is about people, places or groups the world registers (below) - or about none of them in particular;" + nl +
        "- it can be known on its own: ONE fact per claim. The reason for a thing is a fact of its own." + nl + nl +
        "RULES." + nl +
        "- `held_by`: who knows it, from THE HOLDERS below, copied exactly (a group grp.<tag>, a place loc.<id>)." + nl +
        "- `about`: people ids from THE PEOPLE below, or holders; leave it out when the fact is about no one in them." + nl +
        "- `topic`: one of THE TOPICS, or leave it out." + nl +
        "- A CUSTOM - how things are done there, and what breaking it costs - is `norm`: true, with the cost in "
        "`sanction`." + nl +
        "- `evidence`: the sentence of the note this fact comes from, COPIED word for word. Do not paraphrase it. If you "
        "cannot point to the sentence, leave the fact out." + nl +
        "- Write `claim` as the world would say it - plain, one sentence, in the note's own terms." + nl +
        "- No numbers except where the note itself writes one." + nl + nl +
        "Reply with JSON only:" + nl +
        '{"facts": [{"claim": "...", "held_by": ["grp.<tag>" | "loc.<id>"], "about": ["<id>"], "topic": "<topic>",' + nl +
        '            "norm": true, "sanction": "...", "evidence": "<a sentence copied from the note>"}]}' + nl +
        "Leave out every key you do not need. An empty list is a legitimate answer.")
    user = ("THE NOTE (%s):" % note_id + nl + visible_text(note_text) + nl + nl +
            "THE HOLDERS: " + (", ".join(holders) or "(none registered - add groups or places to the world first)") + nl +
            "THE PEOPLE: " + (", ".join(people) or "(none)") + nl +
            "THE TOPICS: " + (", ".join(topics) or "(none)"))
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _refusal(code, message):
    """A proposal's verdict, coded like every refusal: '<CODE>: <what is wrong>'."""
    return "%s: %s" % (code, message)


def check(reply, note_text, world):
    """A proposer's reply -> [{"n", "fact", "ok", "why"}], one verdict per proposal, numbered from 1.

    Refused by name: FACTS_EVIDENCE_MISSING, FACTS_EVIDENCE_IS_AUTHOR_TRUTH, FACTS_EVIDENCE_NOT_IN_NOTE, FACTS_TWO_FACTS,
    FACTS_FIELD_UNKNOWN, FACTS_ALREADY_KNOWN, and any KNOWLEDGE_* the world's own check raises. Raises
    FACTS_REPLY_NOT_AN_OBJECT for a reply that is not {"facts": [objects]}."""
    if isinstance(reply, str):
        try:
            reply = json.loads(reply)
        except ValueError:
            raise RecordError("FACTS_REPLY_NOT_AN_OBJECT", "the proposer's reply is not JSON")
    rows = reply.get("facts") if isinstance(reply, dict) else None
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise RecordError("FACTS_REPLY_NOT_AN_OBJECT", "the proposer's reply must be {\"facts\": [objects]}")
    from .knowledge import validate_world
    seen, fenced = (squash(t) for t in _split(note_text))
    known = {squash(f.get("claim")) for f in (world.get("knowledge") or []) if isinstance(f, dict)}
    out = []
    for n, r in enumerate(rows, 1):
        fact = {k: r[k] for k in FIELDS if k in r}
        why = ""
        ev = squash(r.get("evidence"))
        extra = sorted(k for k in r if k not in FIELDS)
        if extra:
            why = _refusal("FACTS_FIELD_UNKNOWN", "%s is not a field of a fact (%s)" % (", ".join(extra), ", ".join(FIELDS)))
        elif not ev:
            why = _refusal("FACTS_EVIDENCE_MISSING", "no sentence of the note is given for it")
        elif ev in fenced and ev not in seen:
            why = _refusal("FACTS_EVIDENCE_IS_AUTHOR_TRUTH", "it quotes the note's fenced author-only truth, which nobody "
                           "in the world knows")
        elif ev not in seen:
            why = _refusal("FACTS_EVIDENCE_NOT_IN_NOTE", "the evidence is not the note's own words")
        elif _TWO.search(str(r.get("claim") or "").strip()):
            why = _refusal("FACTS_TWO_FACTS", "the claim holds more than one sentence - one fact per claim (the reason is "
                           "its own fact)")
        elif squash(r.get("claim")) in known:
            why = _refusal("FACTS_ALREADY_KNOWN", "the world already holds this claim")
        else:
            try:
                validate_world(dict(world, knowledge=[{k: v for k, v in fact.items() if k != "evidence"}]))
            except RecordError as e:
                why = str(e)
        out.append({"n": n, "fact": fact, "ok": not why, "why": why})
    return out


def note_text(facts, source, log):
    """The knowledge note for one source note -> its markdown: who it was drawn from, the author's approvals in their
    own words (`log`, one line each), and the engine block the loader reads."""
    nl = "\n"
    return ("---" + nl + "type: knowledge" + nl + "source: %s" % source + nl + "---" + nl +
            "# Knowledge drawn from [[%s]]" % source + nl + nl +
            "Kept by the author, fact by fact (scripts/facts.py approve). Edit a fact here, or veto it by deleting it." +
            nl + nl + "## Approvals" + nl + nl.join("- %s" % line for line in log) + nl + nl +
            "```json" + nl + json.dumps({"knowledge": facts}, indent=1, ensure_ascii=False) + nl + "```" + nl)
