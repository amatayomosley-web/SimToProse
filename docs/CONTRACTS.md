# Talking to the showrunner — the partner's contracts

**For the author's partner** — the AI the author talks with about the book. You need this page and nothing else of
the system: the author tells you what they want and you write it as a **direction**. A record step, a declaration or a
render you run yourself; a scene goes to the showrunner, which runs the engine and hands back a **report** you relay
(section 2). For a question about the book, ask the engine yourself (section 4); no showrunner is needed. (The owner, 2026-09-27: the partner "can write the directions using the contract to hand to the showrunner.
This keeps the context window for both smaller".)

## 0. Open the session — once

When the session opens, ask the author how it should run, once; it holds until the session closes (the owner: "you
open a session prepare how you want it ran and then it continues until close"). The three presets differ only in the
seats - the calls every emotion number is computed from:
- `standard` - the seats on OpenRouter at the frontier model: the most accurate; needs a key file (`scripts/provider.py`).
- `local` - the seats on the local model: no key, no spend; below the seats' floor, so a draft to judge by reading.
- `subagents` - no key: a fresh agent answers each seat prompt; Claude tokens, a spawn per prompt.

Any role can be changed with `--set ROLE=MODEL`; `docs/guide-model-roles.md` says what each role needs, and why. Then
`python scripts/profile.py new --out "<your session's scratch folder>/profile.json" --preset <name> [--set ...]`. A
refusal names the role (an agent role runs on a Claude model; the showrunner at least Sonnet-class); a warning names a
trade - tell the author. Pass `--profile "<that file>"` to every `brief.py` call, and spawn each agent at the tier the
profile gives it.

## 1. A direction — one JSON object, one piece of work

| kind | what it asks | needs (beside `book` and `kind`) | may carry |
|---|---|---|---|
| `scene` | run the next scene on a draft and bring it back for review | `intent` - what the author wants from it, in their words | `run` (continue a run), `cast`, `where`, `at` ({"day": 3, "time": "06:00"}), `budget` (turns, at most 5), `stub` (a test: no paid model) |
| `approve` | make a draft the book's record | `draft`, `words` | `in_advance` (the change was dictated before it was written) |
| `reject` | set a draft aside | `draft` | `words` (why) |
| `rewind` | return the record to an earlier state | `to`, `words` | |
| `render` | an approved scene to prose | `run` | `draft` |
| `declare` | the author's own off-page events, corrections, facts | `run`, `file` (a declaration file: `scripts/declare.py`), `words` | |
| `adopt` / `release` | start / stop keeping the book's record behind the author's yes | `words` | |

`book` is the book's folder or slug. **`words` are the author's own words, verbatim** - never yours, never a summary;
without them nothing reaches the record. A field nothing reads is refused, so an instruction is never dropped quietly.

```json
{"book": "The Rock and the Rose", "kind": "scene", "intent": "Mira keeps the lamp lit through the gale",
 "cast": ["mira"], "budget": 4}
```

## 2. Hand it over - run the mechanical steps yourself, spawn only for a scene

A spawned agent carries about 70k tokens of opening context before it reads a word of its task (measured), so a spawn
is kept for work that needs judgment and specialists.

- **approve, reject, rewind, release, adopt, declare:** `python scripts/brief.py --run <direction.json>` checks the
  direction and runs it now - one draft.py command, or for a declaration: a draft opened, the file declared, and the
  draft promoted in advance on the author's words (set aside if the declaration is refused). Its output is the result.
- **scene:** `python scripts/brief.py <direction.json> --profile <profile>` prints the showrunner's whole brief (its
  core, the scene playbook, the session's choices, the direction) and names the showrunner's tier. Spawn a
  general-purpose subagent at that tier whose prompt is that whole output; it may run in the background. Its last
  message is the report.
- **render:** `python scripts/narrate.py --vault "<book>" --run <run> --prompt-only` > a file, then spawn a
  general-purpose subagent at the profile's narrator tier with `python scripts/brief.py --specialist narrator --input
  <that file>` as its prompt, and save its prose to `<book>/prose/<run>/<scene>.md` (first line `record <state>`).

A direction that fails its check is refused with a coded reason before anything runs - fix it and run again.
Which model fills each role - and why - is `docs/guide-model-roles.md`.

## 3. The report

```json
{"status": "done | needs-author | refused", "kind": "...", "book": "...", "run": "...", "draft": "...",
 "read": ["<files for the author>"], "summary": "...", "question": {"ask": "...", "options": ["..."], "recommend": "..."},
 "refusal": "<CODE: text>"}
```
- `needs-author`: put the question to the author, with the file to read; their answer becomes the next direction
  (`approve` with their words, `reject`, or a new `scene`).
- `done`: tell the author what changed. `refused`: tell them what stopped it and what it needs.

## 4. Ask the engine yourself

`python scripts/ask.py <what> --book "<book>" [...]` answers one question as JSON, reading only:
`where` (the record's state, open drafts, each run's turns) · `scene --run R --turn T` · `knows --run R --char C` ·
`state --run R --char C` · `edges --run R --char C --with D` · `facts --run R --subject S` · `place --run R --place P`
· `--db "<draft>"` to read a draft · `--as-of T` for an earlier turn.
