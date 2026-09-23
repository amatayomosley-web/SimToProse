#!/usr/bin/env python3
"""coherence_judge.py — blind coherence judge for the haiku-vs-sonnet runs (measurement.md protocol).

Reads the two full-run transcripts, extracts each per-turn ACTION+THOUGHT arc, and asks two no-ties
THIRD models (not haiku/sonnet) to score each arc BLIND on a 0-10 coherence rubric. A planted control
(one arc with its turn order scrambled — effects before causes) must score LOWEST, or the judge is hollow.
Then a paired A/B pick: which intact run is the more coherent single person. Writes runs/coherence_judgment.md.
"""
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUDGE_MODELS = ["deepseek/deepseek-v4-pro"]  # no-ties, != run models. n=1 (reliable) — a 2nd judge is a noted TODO; flaky burst-throttle made n=2 null half its calls.


def extract_arc(rel):
    """Parse the verbose run transcript -> [{turn, event, action, thought}]."""
    path = os.path.join(REPO, rel)
    arc, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^\s*(\d+)\s+[\d.]+.*\|\s*(.*)$", line)
        if m:
            if cur:
                arc.append(cur)
            cur = {"turn": int(m.group(1)), "event": m.group(2).strip(), "action": "", "thought": ""}
        elif cur is not None and "ACTION :" in line:
            cur["action"] = line.split("ACTION :", 1)[1].strip()
        elif cur is not None and "THOUGHT:" in line:
            cur["thought"] = line.split("THOUGHT:", 1)[1].strip()
    if cur:
        arc.append(cur)
    return arc


def scramble(arc):
    """Planted control: fixed permutation that breaks the causal/emotional order (grief before the death)."""
    n = len(arc)
    order = sorted(range(n), key=lambda k: (k * 7 + 3) % n)
    return [dict(arc[i], turn=j) for j, i in enumerate(order)]


def render(arc):
    def cl(s):
        return (s or "").replace("�", "-")   # repair console-mangled em-dashes from the redirect
    return "\n".join("[%d] ACTION: %s\n    THOUGHT: %s" % (a["turn"], cl(a["action"]), cl(a["thought"])) for a in arc)


def _env_path():
    """Path to the .env holding OPENROUTER_API_KEY.

    Machine-local and therefore NEVER hardcoded — a committed absolute path
    publishes the operator's directory layout and signposts their credentials.
    Set SWE_ENV_FILE, or fall back to a .env beside the repo.
    """
    p = os.environ.get("SWE_ENV_FILE")
    if p:
        return p
    local = os.path.join(REPO, ".env")
    if os.path.exists(local):
        return local
    raise RuntimeError(
        "no .env found: set SWE_ENV_FILE to the file holding OPENROUTER_API_KEY, "
        "or place a .env at the repo root (it is gitignored)")


def _key():
    with open(_env_path(), encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"\s*OPENROUTER_API_KEY\s*=\s*(\S+)", line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    return None


def _judge_call(messages, model, max_tokens=700):
    import time
    note = "empty"
    for attempt in range(5):                     # spacing + growing backoff to survive OpenRouter burst-throttle
        time.sleep(2 + attempt * 3)
        try:
            body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode()
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                         headers={"Authorization": "Bearer %s" % _key(), "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=150) as r:
                resp = json.load(r)
            content = (resp.get("choices") or [{}])[0].get("message", {}).get("content")
            if content:
                return content
            note = "empty content from %s" % model
        except Exception as e:
            note = str(e)[:80].replace('"', "'")
    return '{"score": null, "note": "%s"}' % note


def _parse(text):
    if not isinstance(text, str):
        return {"score": None}
    m = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else {}
    except Exception:
        return {"score": None, "raw": text[:200]}


RUBRIC = ("You are assessing whether a sequence of moments depicts ONE coherent, consistent PERSON across a "
          "long arc, or whether the character drifts, fragments, contradicts itself, or breaks character. "
          "Below are a character's ACTIONS and private THOUGHTS across moments, in the given order. "
          "Score 0-10: 10 = flawlessly one consistent person (stable drives, voice, core wound carried across "
          "the whole arc); 5 = mostly consistent, some slips; 0 = fragmented / contradictory / order makes no "
          "causal sense. Note specific moments that break character or contradict earlier ones. "
          "Reply ONLY JSON: {\"score\": 0-10, \"breaks\": [\"...\"], \"note\": \"...\"}\n\nARC:\n%s")

PAIRED = ("Two independent attempts (X and Y) to portray the SAME character across the same long arc. "
          "Which reads as the more coherent, consistent SINGLE person — stable drives, voice, and core wound? "
          "Reply ONLY JSON: {\"winner\": \"X\"|\"Y\"|\"tie\", \"margin\": \"slight\"|\"clear\"|\"large\", "
          "\"tell\": \"what the weaker one does that breaks character, or why a tie\"}\n\nX:\n%s\n\nY:\n%s")


def main():
    haiku, sonnet = extract_arc("runs/maren_haiku.txt"), extract_arc("runs/maren_sonnet.txt")
    if len(haiku) < 5 or len(sonnet) < 5:
        print("ERROR: transcripts too short (haiku=%d sonnet=%d turns) — did the runs finish?" % (len(haiku), len(sonnet)))
        return 1
    control = scramble(haiku)
    # BLIND: fixed source-obscuring labels (judge never told which is which); mapping recorded for us.
    labelled = {"A": ("sonnet", sonnet), "B": ("control(shuffled-haiku)", control), "C": ("haiku", haiku)}

    out = ["# TEST-001 Coherence Judgment — blind, no-ties\n",
           "Runs: haiku=%d turns, sonnet=%d turns. Control = haiku with turn order scrambled (planted negative)." % (len(haiku), len(sonnet)),
           "BLIND MAPPING (hidden from judges): A=sonnet  B=control(shuffled-haiku)  C=haiku",
           "Judge models (no-ties, != run models): %s\n" % ", ".join(JUDGE_MODELS)]
    scores = {lab: [] for lab in labelled}
    for model in JUDGE_MODELS:
        out.append("## Judge: %s" % model)
        for lab, (src, arc) in labelled.items():
            v = _parse(_judge_call([{"role": "user", "content": RUBRIC % render(arc)}], model))
            s = v.get("score")
            scores[lab].append(s if isinstance(s, (int, float)) else None)
            out.append("- %s [%s]: score=%s  breaks=%s" % (lab, src, s, "; ".join(v.get("breaks", []))[:200] or "none"))
        # paired: intact haiku (X) vs intact sonnet (Y), unlabeled
        p = _parse(_judge_call([{"role": "user", "content": PAIRED % (render(haiku), render(sonnet))}], model))
        out.append("- PAIRED (X=haiku, Y=sonnet — hidden): winner=%s margin=%s tell=%s\n" % (
            p.get("winner"), p.get("margin"), str(p.get("tell"))[:300]))

    def avg(lab):
        xs = [x for x in scores[lab] if x is not None]
        return sum(xs) / len(xs) if xs else None
    out.append("## Aggregate (mean coherence score)")
    for lab, (src, _) in labelled.items():
        out.append("- %s [%s]: %s" % (lab, src, avg(lab)))
    ctrl, hk, sn = avg("B"), avg("C"), avg("A")
    teeth = "PASS" if (ctrl is not None and hk is not None and sn is not None and ctrl < hk and ctrl < sn) else "FAIL"
    out.append("\n**Control teeth-check (control must score below both intact runs): %s**" % teeth)
    if hk is not None and sn is not None:
        out.append("**Haiku vs Sonnet: haiku=%.2f sonnet=%.2f -> %s**" % (
            hk, sn, "indistinguishable" if abs(hk - sn) < 0.75 else ("sonnet superior" if sn > hk else "haiku superior")))

    open(os.path.join(REPO, "runs/coherence_judgment.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out[-6:]))
    print("\nfull verdict -> runs/coherence_judgment.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
