# Playbook: declare - the author's own events, corrections and facts

The partner normally runs this itself: `python scripts/brief.py --run <direction.json>` does steps 1-2 and sets a
refused draft aside (docs/CONTRACTS.md). This playbook is for a showrunner handed a declaration.

The direction names the declaration file (`file`, the shape in `docs/CONTRACTS.md`) and carries the author's `words`:
the instruction was the yes.

1. **Adopted book:** `python scripts/draft.py open --book "<book>" --note "declaration"`; then
   `python scripts/declare.py --book "<book>" --run <run> --file "<file>" --db "<draft>"`; then promote it at once:
   `python scripts/draft.py promote --book "<book>" --draft <draft> --approved "<words>" --by partner-relayed
   --in-advance`.
2. **Unadopted book:** `python scripts/declare.py --book "<book>" --run <run> --file "<file>"` writes the book directly.
3. Report `done` with what declare.py printed. On a refusal, report it with its code - `DECLARE_NAME_UNKNOWN`,
   `DECLARE_PLACE_UNKNOWN` and `DECLARE_ENTRY_REFUSED` name the entry the partner should fix; after a refusal on a
   draft, set the draft aside (`draft.py reject`).
