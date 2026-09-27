# Playbook: render - an approved scene to prose

1. `python scripts/narrate.py --vault "<book>" --run <run> --prompt-only` > a file (add `--db "<draft>"` only when the
   direction names a draft). Spawn the narrator with it.
2. Save its prose to `<book>/prose/<run>/<scene name>.md`, first line `APPROVED - rendered from the record` (or
   `REVIEW - draft <id>` when it came from a draft).
3. Report `done` with `read: [the file]`.
