"""swe_router.py -- UserPromptSubmit hook. Surface the skill you forgot you had.

THE FAILURE, measured 2026-07-25: an entire session of book work ran without
`.claude/skills/showrunner/` ever being loaded. The cost was not context -- it
was ENFORCEMENT. That skill declares three hooks in its own frontmatter, and
skill-scoped hooks exist only while the skill is loaded:

    ground_from_book   injects the book's laws in force + story position, per turn
    citation_gate      blocks an uncitable claim from becoming a written record
    beat_blind_guard   keeps a spawned simulator from learning the intended beat

All three were inactive all session. Provable: ground_from_book is itself a
UserPromptSubmit hook and injected nothing. Two of that session's four
confident-error failures are exactly what citation_gate blocks.

WHY THIS IS NOT THE WAKE'S JOB. `swe_wake.py` lists the skills once at session
start. That is inventory, and inventory decays -- the session that wrote the
inventory then failed to load a skill named in it. This fires when the work
arrives, which is when the knowledge is actually needed.

MECHANISM, adapted from cairn's skill router (~/.claude/SKILL-REGISTRY.md):
  * CURATED VOCABULARY ONLY. Each SKILL.md declares its own `triggers:` block
    (keywords + concepts). Nothing is scraped from prose, so the misfire classes
    that come from matching description text -- stopword piles, corpus-rare
    generics, substring hits -- are structurally impossible rather than tuned out.
    Authoring a skill IS authoring its triggers; that field is its routability.
  * FIRING RULE: >=1 concept, OR >=1 multi-word keyword, OR >=2 single keywords.
    A single common word NEVER fires. One single-word hit is logged as a near
    miss -- tuning signal, not output.
  * CONCEPTS ARE PARAPHRASE-TOLERANT: a concept hits when all its content words
    appear anywhere in the prompt, so "let's develop the book idea" matches the
    declared concept "develop the book". No phrase rigidity.
  * DEFENSIVE LADDER: the output assumes it may be wrong and says so. It informs,
    never instructs. Roughly thirty tokens per hit, so three wrong guesses cost
    ~90 tokens instead of the ~5k a wrongly-loaded body would.

DIVERGENCE FROM THE CAIRN ROUTER, deliberate: no prebuilt index and no build
script. That design serves 92 situational skills; this repo has 11, so parsing
frontmatter at runtime costs a few milliseconds and removes the stale-index
failure mode entirely. If this repo ever carries dozens of skills, add the index
then -- not before.

Stdlib only. Silent-failure discipline: never break a turn. Any error returns 0.
"""
from __future__ import annotations

__layer__ = "harness"

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SKILLS = REPO / ".claude" / "skills"
LOG = REPO / ".claude" / ".router_fires.jsonl"
MAX_ROUTES = 3

# Words too common to carry meaning inside a declared concept. Kept tiny on
# purpose: the curated-vocabulary design means concepts are already specific,
# so this only strips the connective tissue.
_STOP = {"the", "a", "an", "of", "to", "in", "is", "it", "this", "that", "and",
         "or", "for", "on", "at", "be", "do", "i", "we", "my", "our"}


def _content_words(phrase: str) -> set:
    """The words a concept actually needs. >=2 required to fire, so a concept
    that reduces to one content word is inert by construction -- the same
    'one word never fires' rule applied at the phrase level."""
    return {w for w in re.findall(r"[a-z0-9]+", phrase.lower()) if w not in _STOP}


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else ""


def _parse_triggers(fm: str) -> tuple[list, list]:
    """Minimal YAML-subset reader for the `triggers:` block. Deliberately not a
    YAML dependency -- stdlib only, and the shape is fixed and shallow."""
    kws, cons, mode = [], [], None
    for raw in fm.splitlines():
        line = raw.rstrip()
        if re.match(r"^\s*keywords:\s*$", line):
            mode = "k"; continue
        if re.match(r"^\s*concepts:\s*$", line):
            mode = "c"; continue
        if re.match(r"^[a-zA-Z_]", line):        # any top-level key ends the block
            mode = None; continue
        m = re.match(r"^\s*-\s+(.*\S)\s*$", line)
        if m and mode:
            (kws if mode == "k" else cons).append(m.group(1).lower())
    return kws, cons


def _load_skills() -> list:
    out = []
    try:
        for d in sorted(SKILLS.iterdir()):
            f = d / "SKILL.md"
            if not f.is_file():
                continue
            try:
                fm = _frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            kws, cons = _parse_triggers(fm)
            if kws or cons:
                out.append((d.name, kws, [(c, _content_words(c)) for c in cons]))
    except Exception:
        pass
    return out


def _log(kind: str, prompt: str, hits: list) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": kind,
                "prompt": prompt[:200],
                "hits": [{"skill": n, "score": s, "matched": m} for s, n, m in hits],
            }) + "\n")
    except Exception:
        pass


def main() -> int:
    try:
        raw = sys.stdin.read()
        try:
            prompt = (json.loads(raw) or {}).get("prompt", "")
        except Exception:
            prompt = raw
        prompt = (prompt or "").lower().replace("-", " ").replace("'", "")
        if not prompt.strip():
            return 0

        words = set(re.findall(r"[a-z0-9]+", prompt))
        fires, nears = [], []

        for name, kws, cons in _load_skills():
            c_hits = [c for c, cw in cons if len(cw) >= 2 and words >= cw]
            k_hits = [k for k in kws
                      if (k in words if " " not in k
                          else re.search(r"\b%s\b" % re.escape(k), prompt))]
            strong_k = [k for k in k_hits if " " in k]
            score = 3 * len(c_hits) + 2 * len(strong_k) + len(k_hits)
            entry = (score, name, (c_hits + k_hits)[:3])
            if c_hits or strong_k or len(k_hits) >= 2:
                fires.append(entry)
            elif len(k_hits) == 1:
                nears.append(entry)

        if nears:
            _log("near_miss", prompt, sorted(nears, reverse=True)[:3])
        if not fires:
            return 0
        fires.sort(reverse=True)
        _log("fire", prompt, fires[:MAX_ROUTES])

        out = ["=== SWE skill router -- POSSIBLE MISFIRE, weigh before loading ==="]
        for _, name, matched in fires[:MAX_ROUTES]:
            out.append("* %s -- matched on: %s" % (name, ", ".join(matched)))
            if name == "showrunner":
                out.append("  NOTE: loading this ACTIVATES THREE HOOKS that exist only while it is")
                out.append("  loaded -- ground_from_book (laws + story position each turn),")
                out.append("  citation_gate (blocks uncitable claims from becoming records),")
                out.append("  beat_blind_guard. Not loading it is a loss of ENFORCEMENT, not detail.")
        out.append("None of this is required. Invoke via the Skill tool if it fits the task.")
        print("\n".join(out))
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
