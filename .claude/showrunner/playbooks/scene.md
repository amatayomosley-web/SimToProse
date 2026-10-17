# Playbook: scene - run the next scene on a draft, render it for review, ask the author

If this brief carries a **Session profile**, it governs: every `scene.py` call takes its `--profile`, every specialist
is spawned at its tier, and subagent seats are answered by its loop while the scene runs.

1. **Adopted?** If `ask.py where` shows the record role is not `record`, stop: report `needs-author` - "Adopt the book
   so this scene waits for your yes?" (recommend yes). A scene never writes an unadopted book.
2. **Open a draft:** `python scripts/draft.py open --book "<book>" --note "<the intent, in a few words>"` - it prints the
   draft's path. Every command below runs with `--db "<draft>"`.
3. **Shape the scene:** write the director's input (the direction's `intent`, `cast`, `where`, `at`; the story
   position from `ask.py where`; the book's `runs/story-map.md` if it has content) and spawn the director. From its
   placement, write the scene cfg to `<book>/scenes/<name>.json` in this shape (the full field guide is
   `docs/authoring/BLUEPRINT-scene.md`; open it only if a field below does not cover what the director placed).
   **What the author directed is copied VERBATIM:** every member of the direction's `cast` with each field it gives
   (`to` - whom that character's moves are aimed at; `tells` - what they give away without meaning to, a list of
   the author's lines, shown only to a sharp eye when the book runs `tells`; and `drive`), and its `at`. The director may add (a drive the
   direction left open, props, a situation), never drop or change a directed value; the run refuses a cfg that does:
   ```json
   {"name": "scene_01_keeping_the_light", "at": {"day": 1, "time": "21:00"}, "lasts": "40m", "pov": "mira",
    "location": "lamp_room",
    "situation": "Full dark on day one of storm season; Mira is alone in the lamp room while the gale builds...",
    "props": ["the wick guttering each time the draft catches it", "the oil fount at hand, wanting a trim"],
    "cast": [{"id": "mira", "drive": "get the flame back to full before the next gust finds it", "to": "tomas"},
             {"id": "tomas", "drive": "keep Mira from climbing the gallery in this wind",
              "tells": ["he rubs the old break in his wrist when he is lying"]}],
    "opening_tags": {"dimensions": {"threat": "moderate"}}}
   ```
   `python scripts/lint_scene.py` is not needed; the run below refuses a malformed cfg by name.
4. **Run it:** `python scripts/scene.py --book "<book>" --db "<draft>" --scene "<cfg>" --direction "<the direction's
   file, as the brief names it>"` - add `--budget <the direction's budget>` only when the direction gives one (without it the scene file's `moves`, else 24, is the ceiling), `--resume <run>` when the direction continues a run, and `--stub` when the direction says `stub`.
5. **Check it yourself:** `python scripts/critic.py --vault "<book>" --db "<draft>" --run <run> --prompt-only` > a
   file; read it and judge continuity and voice against what it shows, in its own reply shape. Note any flags for the
   summary; do not correct anything.
6. **Render it for review:** `python scripts/narrate.py --vault "<book>" --db "<draft>" --run <run> --prompt-only` > a
   file; spawn the narrator with it. Save its prose to `<book>/prose/<run>/<scene name>.md`, first line `draft <id>`
   (whether it was approved is the lineage's to say: `ask.py where`).
7. **Report** `needs-author`: `draft`, `run`, `read: [the prose file]`, the continuity flags in the summary, and the
   question "Keep this scene?" - options: keep (approve), set it aside (reject), revise (say what). Recommend from the
   flags.
