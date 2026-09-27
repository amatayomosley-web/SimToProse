# Playbook: scene - run the next scene on a draft, render it for review, ask the author

1. **Adopted?** If `ask.py where` shows the record role is not `record`, stop: report `needs-author` - "Adopt the book
   so this scene waits for your yes?" (recommend yes). A scene never writes an unadopted book.
2. **Open a draft:** `python scripts/draft.py open --book "<book>" --note "<the intent, in a few words>"` - it prints the
   draft's path. Every command below runs with `--db "<draft>"`.
3. **Shape the scene:** write the director's input (the direction's `intent`, `cast`, `where`, `at`; the story
   position from `ask.py where`; the book's `runs/story-map.md` if it has content) and spawn the director. From its
   placement, write the scene cfg to `<book>/scenes/<name>.json` in the shape of `docs/authoring/BLUEPRINT-scene.md`.
4. **Run it:** `python scripts/scene.py --book "<book>" --db "<draft>" --scene "<cfg>" --budget <direction budget, at
   most 5>` - add `--resume <run>` when the direction continues a run, and `--stub` when the direction says `stub`.
5. **Check it:** `python scripts/critic.py --vault "<book>" --db "<draft>" --run <run> --prompt-only` > a file; spawn
   the continuity-critic with it. Note its flags for the summary; do not correct anything yourself.
6. **Render it for review:** `python scripts/narrate.py --vault "<book>" --db "<draft>" --run <run> --prompt-only` > a
   file; spawn the narrator with it. Save its prose to `<book>/prose/<run>/<scene name>.md`, first line
   `REVIEW - draft <id>, not yet approved`.
7. **Report** `needs-author`: `draft`, `run`, `read: [the prose file]`, the critic's flags in the summary, and the
   question "Keep this scene?" - options: keep (approve), set it aside (reject), revise (say what). Recommend from the
   flags.
