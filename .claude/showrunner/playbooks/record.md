# Playbook: record - adopt, approve, reject, rewind, release

One command each. The author's words come from the direction's `words`, passed exactly as given.

| kind | command |
|---|---|
| adopt | `python scripts/draft.py adopt --book "<book>"` (the author said adopt; quote their words in the summary) |
| approve | `python scripts/draft.py promote --book "<book>" --draft <draft> --approved "<words>" --by partner-relayed` - add `--in-advance` when the direction says `in_advance` (a change dictated before it was written) |
| reject | `python scripts/draft.py reject --book "<book>" --draft <draft> --why "<words or note>"` |
| rewind | `python scripts/draft.py restore --book "<book>" --to <to> --approved "<words>" --by partner-relayed` |
| release | `python scripts/draft.py release --book "<book>" --approved "<words>" --by partner-relayed` |

The partner runs these itself: `python scripts/brief.py --run <direction.json>` runs the one command (docs/CONTRACTS.md).
Without `--run`, brief.py hands a spawn only its one filled-in command; the spawn makes that one call and reports. Report `done` with the command's own output line in the summary; on a refusal, `refused` with
its code.
