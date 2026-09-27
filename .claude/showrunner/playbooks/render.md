# Playbook: render - an approved scene to prose

The partner normally does this itself (docs/CONTRACTS.md section 2) - the narrator is the only spawn a render needs.

1. `python scripts/narrate.py --vault "<book>" --run <run> --prompt-only` > a file (add `--db "<draft>"` only when the
   direction names a draft). Spawn the narrator with it.
2. Save its prose to `<book>/prose/<run>/<scene name>.md`, first line `record <state>` (or `draft <id>` when it
   came from a draft).
3. Report `done` with `read: [the file]`.
