# Continuing a Story — what to author for each generation step (LLM guide)

For a session (human or LLM) **extending a book** on this engine. Answers the operator's question:
*what data does each step need, and how much?* Grounded in the loader contract (`src/engine/vault.py`)
and the pipeline (`docs/guide-operating.md`). The discipline is the **depth rule**: author only the
hinges the story levers on; class-default the long tail; let the bible grow from the sim.

## The one-paragraph answer

To drive **one scene** you need, at minimum: the **world note** (a slice with teeth) + every acting
character as a **character note** (full substrate) + a **people note** for each present entity + **one
scene cfg** (the situation + each actor's drive). To drive a **chapter** you add a **chapter blueprint**
(the beats — the director's *hidden* targets) and run a scene per beat, **steering by circumstance**.
You do **not** author the arc — destination fixed (the blueprint), route discovered (the sim). The only
thing authored per character is its **starting state**; its baseline drifts from what it lives.

## The data hierarchy (authored once → per-chapter → per-scene → per-turn)

| Tier | Artifact | Cadence | The engine reads it as |
|---|---|---|---|
| World bible | `world/*.md` (one `type:world`) + `people/*.md` | once per book (grows lazily) | the canon + the live perception slice |
| Chapter blueprint | `chapters/*.md` | per chapter | **the director's hidden beats** (NOT fed to the sim) |
| Scene cfg | a `--scene` JSON | per scene | the situation + cast + drives the runner opens with |
| Character | `characters/*.md` (full substrate) | per acting character | the actor's `fixed/baseline/current` + vault |
| Person | `people/*.md` | per present entity | a `world.people` entry (recognition + regard) |
| The run | the chronicle DB | per turn (machine-written) | append-only turns/events/scenes/acquisitions |

## Step 1 — the World bible (author once; grows from the sim)

**File:** one `world/<name>.md`, `type: world`, with a fenced ```json engine block.
**Engine block (the LIVE machinery — `vault.py` + `gate.py`):**
- `lexicon.attribute_classes {class: [keywords]}` — the nouns this book's events are ABOUT; the keywords
  (incl. character first names) that register as overt percepts in event text.
- `lexicon.subtle_cues {cue: [markers]}` + `subtle_cue_classes [...]` — detail only a perception check surfaces.
- `locations [{id, what}]`, and `people` may be inlined or come from `people/` notes.
**Canon-only fields (stored, INERT to the per-turn sim — read by the critic/narrator/director, not the actor):**
`world` title, `season`, `standing_facts`. (See `docs/guide-continuing-the-story.md` companion finding in
guide-content.md: a fact reaches the actor only via event text, a vault belief, or the lexicon/people/locations.)
**How much:** only the hinges — enough world that a lever can be plausibly **denied** (world-model.md "teeth").
Missing world the sim reaches for is auto-queued to `world-faults.md` (the chair) — author it then, not before.

## Step 2 — the Chapter blueprint (author per chapter; the director's targets)

**File:** `chapters/Chapter N.md`, `type: chapter` — a **scene-by-scene outline of what happens**: the POV,
the timeline, a micro 3-act shape, and each scene's beats (SC1, SC2…) with the key turns and payoffs.
**This is the DIRECTOR's artifact, never the simulator's** (the beat-blind wall, design.md): it names the
beats you steer *toward*; the actors never see it. It is prose/outline, not an engine block — nothing loads it.
**How much:** the beats + their payoffs (what must land, and what later chapter it sets up). Not the prose,
not the dialogue — those EMERGE. A blueprint is the spine; the flesh is run.

## Step 3 — Scene cfgs (author per scene; derived from the blueprint)

**File:** a JSON passed to `scripts/scene.py --scene <file>`. Shape (`scene.py:load_scene_cfg`):
```json
{ "name": "the-third-night", "pov": "joss_apprentice",
  "situation": "<the circumstance the actors open in — plain text>",
  "subject": ["<entity_id>", "<group>"], 
  "opening_tags": {"type": "threat", "dimensions": {"threat": 0.6}, "durability": "transient"},
  "cast": [ {"id": "joss_apprentice", "drive": "<a standing WANT, blind to the scene's outcome>"}, ... ] }
```
**The drive discipline (design.md scene-goals):** a drive is a genuine standing want — **never the ending in
a costume.** "Get the squad off this rock alive" is a drive; "heroically sacrifice himself" is foreknowledge.
Set up *our* wants (from the blueprint) → build each actor's drive **backward** from them → the beat must
**emerge**, verified by simulation. If it doesn't, retune the **drive**, never script the line.
**How much:** one cfg per scene; the situation + one drive per present actor. The director re-runs / re-tunes.

## Step 4 — Characters (author per acting character; the substrate)

**Two notes per actor:**
1. `characters/<Name>.md`, `type: character`, with the FULL engine block (`fixed`/`baseline`/`current`) +
   a `## Beliefs` section (→ the vault). This is the actor's substrate — what it acts FROM.
2. `people/<Name>.md`, `type: person`, engine block `{"groups": [...]}` + a first prose line (the gated
   identity record). This makes the actor a present entity others can **perceive and regard**. An actor who
   is never perceived by anyone can skip it; in practice every acting character needs both.

**The character engine block (required by `build_profile`/`assemble`; template: `characters/` in any book or
`characters/maren-healer.json`):**
- `fixed`: `name`, `genotype` (6 axes: threat_reactivity, approach_drive, affiliation_attachment,
  anger_proneness, effortful_control, sensitivity — each low|typical|elevated|high), plus `position`/`people`.
- `baseline`: `temperament` (ALL 8 primaries × `{mean, variability}`), `traits`, `model`
  (`schwartz`/`moral_foundations`/`needs`/`regard`), `drives`, `skills`, `voice`.
- `current`: `affect` (8 primaries 0..1), `condition` (a dict), `active_goals`, `relationships`
  (keys MUST be `world.people` ids or the edge never surfaces), `location`.

**The discipline — design SUBSTRATE for the TARGET, never a label (Writing Conventions §1c):** a character's
canon ("a bigot who feels bad") is the **acceptance target**, not a rule. Build the person from whom the
behavior **falls out** — usually an **opposable tension** (e.g. innate CARE in genotype/temperament vs a
formative bigotry in `model.regard` + a vault belief) — then **verify by simulation** that the target emerges.
If it misses, adjust the substrate, never add a classifying rule. Lint before you run: `scripts/lint_book.py`.

**Depth by role (recording-model):** **principal depth** (full, carefully-tuned substrate + rich vault) for
POV-candidates — anyone who might anchor a future cut; **lighter** substrate for supporting actors (still
runnable: the 8 primaries, an affect, a drive, a few beliefs). Capture depth = the future cut-space; you
cannot deepen interiority post-hoc.

**How much:** one full substrate per principal; a lighter one per supporting actor; a people-note per present
entity. All numbers start **UNCALIBRATED** — proposed by the session, ratified/tuned by the author (§3).

## Step 5 — Run → critic → cut → narrate (no new authoring)

These consume Steps 1–4; they author nothing the author must write:
- **Run:** `scene.py --scene <cfg>` (and `--resume <run_id>` for a later scene in the same chronicle) →
  the chronicle DB fills (turns, events, scene boundaries, acquired memory).
- **Critic / Narrate:** strong-model, **Claude-in-the-loop** (`--prompt-only` emits the prompt).
- **Cut:** `cut.py` shows the dailies; the cut **discussion** (human) writes the EDL — not authored upfront.

## "How much data?" — the cheat sheet

- **Smallest runnable thing (one scene):** 1 world note + N character notes (the present cast) + N people
  notes + 1 scene cfg. That is the whole input; everything else is generated.
- **A chapter:** + 1 blueprint (the beats) + 1 scene cfg per beat. The director times the levers; the arc runs.
- **A character's arc:** authored ONCE (its starting state). It is **run, not written** — no waypoints, no
  time-skips; the baseline drifts from consequences (Ilsa's sheet is the worked example).
- **The long tail (props, bystanders, geography):** class-defaults; refine only at a hinge a scene reaches
  for; let `world-faults.md` tell you what's missing. Never pre-author the whole world.

## Worked example — continuing the Ashford fixture to a second chapter

A second chapter needs four things, and the shape is the same whatever the book. Say the next
chapter turns on a fever season reaching the upland farms, told from the apprentice's POV. You author:
the **new world slice** (the farms, the road that closes in snow, the lexicon for sickness and
scarcity — a slice with *teeth*, so the world can deny a lever), the **new faces as characters**
(the farmholder, the carter who stops coming) with people-notes, and **scene cfgs** for each beat
the chapter must reach. The chapter blueprint is the director's beat-list. Author each character's
**starting state** (the substrate), run the beats, and steer by circumstance only.

Flag anything built on a blueprint that is still provisional — a beat-list you have not committed to
is not canon, and downstream work that assumes it will need revisiting.
