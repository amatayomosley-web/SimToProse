# `runs/<book-slug>/` — a book's production notes (template)

Copy this directory to `runs/<book-slug>/` to start a book. The **showrunner** (`.claude/agents/showrunner.md`, designed in `docs/orchestration.md`) maintains these files as it runs the production. They are the production's **process memory** — not canon: together with the run DB (`runs/<book>.db` — the canonical world-truth ledger, `docs/world-state-ledger.md`), they fully reconstruct where the story is and what has been done at any pause, so a fresh showrunner — or a human — can resume mid-book.

| File | Holds | Kind |
|---|---|---|
| `canon-ledger.md` | append-only event log + folded "now" (`docs/world-state-ledger.md`) | digest — generated view of the run DB; non-authoritative |
| `production-journal.md` | chronological log of what was done + why: beats, gate results, decisions, revisions | process |
| `story-map.md` | the plan + per-item status + current position | process |
| `threads.md` | open threads, promises, setups awaiting payoff, reveal schedule | process |
| `continuity-register.md` | facts fixed as the bible grows from the sim | process-truth — working index; the authoritative home of a fixed fact is the bible / the DB event that fixed it |
| `cast/` | the character sheets (`docs/character-schema.md`), one file per character | process-truth — materialized by the showrunner from the character-generator's returned sheet; state fields mirror the run DB |

These are **runtime builds** (`docs/world-state-ledger.md`): the line items fill as the sim runs; the template ships only the shape. The gates that govern what may be written to them are in `docs/orchestration.md`.
