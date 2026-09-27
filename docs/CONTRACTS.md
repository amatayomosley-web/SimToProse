# Talking to the showrunner — the partner's contracts

**For the author's partner** — the AI the author talks with about the book. You need this page and nothing else of
the system: the author tells you what they want, you hand the showrunner a **direction**, it runs the engine and hands
back a **report**, and you relay. For a question about the book, ask the engine yourself (section 4); no showrunner is
needed. (The owner, 2026-09-27: the partner "can write the directions using the contract to hand to the showrunner.
This keeps the context window for both smaller".)

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

## 2. Hand it over

1. Write the direction to a file.
2. `python scripts/brief.py <direction.json>` prints the showrunner's whole brief (its core, the one playbook the kind
   needs, and the direction), or refuses the direction with a coded reason - fix it and run again.
3. Spawn a general-purpose subagent (sonnet is enough) whose prompt is that whole output; it may run in the background.
   Its last message is the report.

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
