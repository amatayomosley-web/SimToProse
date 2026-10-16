#!/usr/bin/env python3
"""narration_contract.py — the narrator's source contract: what the prompt tells it, how the transcript is labelled,
and the copy check that measures a telling against the record (gate narrator-source-contract).

`scripts/narrate.py` builds the prompt from these texts; `.claude/agents/narrator.md` carries the same contract for
the agent route, and tests/test_narrate.py holds its load-bearing phrases in both files. Kept apart from narrate.py
so the contract is one readable page, and the measurement sits beside the rule it measures.

    python scripts/narration_contract.py copy-check <prose.md> --vault <book> --run <run_id> [--db PATH] [--n 8]
        every run of n+ consecutive words the prose shares with a recorded action or thought, and the share of
        the prose inside them. Not a pass/fail gate: a character's short idiom line will and should match.
"""
import argparse
import io
import os
import re
import sys

# ---- THE SOURCE CONTRACT (gate narrator-source-contract, 2026-10-16) ----------------------------
# The owner: "the narrators job is to take what's generated and turn it into the story." Three tellings
# of one scene copied every recorded speech and turned the actor's deliberation record ("two pulls ...
# X wins") into paragraphs of interiority, because nothing said the WORDING of the record is free and
# the labels presented speech and thought as quotable testimony. The review that found it is the
# source of these texts. `.claude/agents/narrator.md` says the same thing for the agent route, and
# tests/test_narrate.py holds the load-bearing phrases in both files.
SOURCE = (
    "THE SOURCE. The recorded scene below is source material, not a script. FIXED, and you may not change, "
    "add or drop it: who is present; every act and what changed hands; every choice and which way it went; "
    "the order in which one person's words or acts answer another's; and the SUBSTANCE of what was said - "
    "every claim, order, question, refusal, name and amount a character put into words, and the stance it "
    "was said with. Nothing is said on the page that the record does not say. Nothing one character told "
    "another vanishes: it may be shortened, reported ('she told him where the key was kept: under the "
    "step') or summarized, but the reader receives it. FREE, and expected to change: the WORDING of speech. "
    "A recorded line is the actor's draft of what the character said. Write the line the character would "
    "say in this book's voice - shorter, split, merged, paraphrased, or reported. Keep the words that carry "
    "the speaker's voice (their idiom, oaths, forms of address, the one phrase that is theirs); free the "
    "rest. Do not copy a recorded speech onto the page. Also free: the order of sentences inside one turn; "
    "which beats you dramatize and which you summarize; repetition - a gesture or an order the record "
    "repeats appears once unless the repetition means something; and the actor's own descriptions (its "
    "similes, its 'as if') - the gesture is the fact, the actor's phrasing of it is not.")
THOUGHT_RECORD = (
    "THE THOUGHT RECORD. Lines marked THOUGHT are the engine's record of what %(who)s weighed before "
    "acting, written by the actor to a contract that makes it name its competing pulls and which one won "
    "('Two pulls ... X wins. So I ...'). That shape is machinery, like a stat: it is evidence, never text "
    "for the page - no 'two pulls', no 'X wins', no plan stated and then carried out by the next sentence. "
    "Use the record as EVIDENCE: it tells you the motive behind the act that follows, what %(whom)s noticed "
    "in the other person, what %(whom)s feared and wanted, and which way the decision went. Render that the "
    "way this book renders a mind: through the act, the body, what %(whom)s looks at and handles, and at "
    "most a line or two of interiority in %(idiom)s. The direction of the decision is fixed. Do not add a "
    "motive the record does not hold, and do not narrate a plan the next act shows.")
LONG_SPEECHES = (
    "LONG SPEECHES. A recorded turn is often one whole speech, because each actor spoke once per beat. Do "
    "not render alternating speeches. Break a speech into its points; keep the two or three that carry the "
    "beat as spoken words and report or drop the rest (a told fact is reported, never dropped); and let "
    "%(p)s's recorded acts, perceptions and reactions fall between the points they answer. An act recorded "
    "at the end of a beat may happen during the other person's speech when nothing it answers comes later; "
    "a reply stays after what it answers. You may not give %(p)s a word the record does not hold. A silence "
    "is not a reaction: when %(p)s said nothing, show what %(p)s did, handled, or saw, never 'he said "
    "nothing'.")
LONG_SPEECH_WORDS = 60     # a turn longer than this is flagged on its label for the LONG SPEECHES rule


def transcript(entries, pov, povn, names, knowledge):
    """`narrate.pov_split`'s entries -> (the legend, the typed transcript). The POV's THOUGHT comes BEFORE
    the act it explains (it is the reason for the act, not a second event); every other actor is DID/SAID
    as the POV saw it. The labels are the contract: they say which lines are fixed and which are evidence."""
    lines, others = [], []
    for i, e in enumerate(entries, 1):
        name = names.get(e["actor"], e["actor"])
        long_ = " · long speech, break it" if len(str(e["action"]).split()) > LONG_SPEECH_WORDS else ""
        if "thought" in e:
            lines.append("beat %d · THOUGHT (%s, private; engine deliberation record - evidence, never text for "
                         "the page): %s" % (i, name, e["thought"]))
        if e["actor"] == pov:
            lines.append("beat %d · DID/SAID (%s)%s: %s" % (i, name, long_, e["action"]))
            continue
        if name not in others:
            others.append(name)
        closed = "" if "thought" in e else "; %s's mind is closed" % name
        lines.append("beat %d · DID/SAID (%s, as %s saw and heard it%s)%s: %s"
                     % (i, name, povn, closed, long_, e["action"]))
    omni = knowledge == "omniscient"
    legend = ["RECORDED SCENE (POV = %s). One actor turn per beat, in order. The labels say what each line is:" % povn,
              "  THOUGHT (%s, private)  %s before acting, in the engine's deliberation format. Evidence of "
              "motive and direction. Never text for the page."
              % ("each character" if omni else povn, "each character's private weighing" if omni
                 else "what %s weighed" % povn),
              "  DID/SAID (%s)  %s's recorded act and words. The act is fixed. The words are fixed in substance "
              "and free in wording." % (povn, povn)]
    for o in others:
        legend.append("  DID/SAID (%s, as %s saw and heard it)  another character's observable act and words, "
                      "same rule.%s" % (o, povn, "" if omni else " %s's mind is closed to you." % o))
    return "\n".join(legend), "\n".join(lines)


def _tokens(text):
    return re.findall(r"[a-z0-9']+", str(text or "").lower().replace("\u2019", "'"))


def copied_runs(prose, turns, n=8):
    """Every run of n+ consecutive words the prose shares with a recorded action or thought
    -> [(actor, field, run)]. Deterministic; the copy test for a telling, not a judge of it. A maximal
    run is reported once, at its longest."""
    words = _tokens(prose)
    hits = []
    for t in turns:
        for field in ("action", "thought"):
            src = _tokens(t.get(field))
            if len(src) < n:
                continue
            grams = {tuple(src[i:i + n]) for i in range(len(src) - n + 1)}
            i = 0
            while i <= len(words) - n:
                if tuple(words[i:i + n]) not in grams:
                    i += 1
                    continue
                j = i + n
                while j < len(words) and tuple(words[j - n + 1:j + 1]) in grams:
                    j += 1
                hits.append((t["actor"], field, " ".join(words[i:j])))
                i = j
    return hits


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    ap = argparse.ArgumentParser(description="the narrator's source contract - the copy check")
    sub = ap.add_subparsers(dest="cmd", required=True)
    cc = sub.add_parser("copy-check", help="the runs a telling copies from the record")
    cc.add_argument("prose")
    cc.add_argument("--vault", required=True)
    cc.add_argument("--run", required=True)
    cc.add_argument("--db", default=None)
    cc.add_argument("--n", type=int, default=8)
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.engine import books
    from src.engine.ledger import Ledger
    from critic import scene_turns
    with io.open(a.prose, encoding="utf-8") as fh:
        prose = fh.read()
    led = Ledger(a.db or books.db_path(a.vault), create=False)
    hits = copied_runs(prose, scene_turns(led, a.run), a.n)
    inside = sum(len(r.split()) for _a, _f, r in hits)
    for actor, field, run in hits:
        print("%s %s: %s" % (actor, field, run))
    print("%d copied run(s); %d of %d prose words (%.0f%%) inside them"
          % (len(hits), inside, len(_tokens(prose)), 100.0 * inside / max(1, len(_tokens(prose)))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
