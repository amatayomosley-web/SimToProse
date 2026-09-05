# THE SCENE BLUEPRINT

### A hand-fillable form for writing one scene

---

## What this is, and what you get at the end

This is a form you fill in with a pen. You will describe one moment — where it happens, who
is standing in it, what is physically true about the room, and what each person is trying to get
out of the next few minutes. When you are done, someone types your answers into a small file
called a **scene cfg**, drops it in the book's `scenes/` folder, and the engine runs the scene:
the characters talk and act on their own, nobody's lines are scripted, and what they do gets
written into the book's permanent record. You are not writing dialogue. You are setting a room on
fire and stepping back.

Every field below tells you four things: what it is, what a good answer looks like, exactly what
the machine does with it (with the file and line number, so you can check me), and what happens
if you leave it blank.

The worked examples all come from a real book, **Beck Hollow** — a winter village, a miller
called Tam, a shepherd called Nell, and a wolf pack coming down off the fell.

**One promise before you start:** you can fill this in top to bottom. No question below depends
on an answer that comes later.

---

## Contents

1. [Before you write: the book folder your scene lives in](#1-before-you-write-the-book-folder-your-scene-lives-in)
2. [Where and when — the place](#2-where-and-when--the-place)
3. [Who is in the room](#3-who-is-in-the-room)
4. [Whose eyes we watch through](#4-whose-eyes-we-watch-through)
5. [What is happening — the situation](#5-what-is-happening--the-situation)
6. [What they can pick up — the props](#6-what-they-can-pick-up--the-props)
7. [What they want — the drives](#7-what-they-want--the-drives)
8. [Who the moment is about — the subject](#8-who-the-moment-is-about--the-subject)
9. [How hard it lands — the opening tags](#9-how-hard-it-lands--the-opening-tags)
10. [Optional: the act the world must permit](#10-optional-the-act-the-world-must-permit)
11. [Optional: time since the last scene](#11-optional-time-since-the-last-scene)
12. [Fields you can leave blank — nothing reads them](#12-fields-you-can-leave-blank--nothing-reads-them)
13. [Four traps that catch everybody once](#13-four-traps-that-catch-everybody-once)
14. [Pre-flight — before you spend a run](#14-pre-flight--before-you-spend-a-run)
15. [A complete filled example](#15-a-complete-filled-example)
16. [The blank form, to copy out](#16-the-blank-form-to-copy-out)
17. [Footnotes: places where the existing docs are wrong](#17-footnotes-places-where-the-existing-docs-are-wrong)

---

## 1. Before you write: the book folder your scene lives in

A scene does not live on its own. It lives inside a **book folder**, and the engine expects that
folder to have a particular shape. Here is the whole shape, and what each part is for.

```
<your vault>/books/<book-name>/
├── world/        one file. The place, its rules, its map.
├── characters/   one file per person the engine will act.
├── people/       one file per person anyone must be able to see or name.
├── scenes/       your scene forms and the cfg files made from them.
├── chapters/     your outline. Keep it here, never in world/.
├── runs/         the production notes AND the database. Do not hand-make the database.
└── staging/      retired files. This project never deletes; it stages.
```

### The physical shape of a note file

Every note in `world/`, `characters/`, and `people/` is a plain `.md` file, and every one of them
has the same three-part shape:

```
---
type: world
id: a short id, or a long descriptive one — your choice
---

Plain prose. This is canon, and you may use [[links]] to other notes freely. The engine does not
read this paragraph — it is here for you, and for Obsidian if you use it.

​```json
{ "...": "one fenced json block. Only this block is read by the engine." }
​```

## Beliefs
- (0.9, lived) a claim this character believes, stated in their own words [[an anchor note]]
```

1. **Frontmatter** — `---`, then flat `key: value` lines, then `---`, at the very top of the file
   with nothing before it (`src/engine/vault.py:54`). This is a YAML *subset* by design — flat
   keys only, no nesting. `type` and `id` are read out of it by name; every other key you write is
   carried along untouched, for your own use.

   Write `type: world` on the one note in `world/`, `type: character` on every note in
   `characters/`, `type: person` on every note in `people/`. (The loader actually defaults an
   *untyped* note to the type its own folder expects — `(n["type"] or "world") == "world"` for a
   note sitting in `world/`, `src/engine/vault.py:120` — which is exactly how an untyped outline
   filed in the wrong folder becomes an invisible second world note and trips the count check
   below. Writing the type explicitly is what saves you from that trap, not what the loader
   strictly demands.)

2. **One fenced ` ```json ` block — the engine block.** This is the only part of the file the
   engine actually parses (`_JSON_BLOCK_RE`, `src/engine/vault.py:65-71`) — everything outside it,
   your headings, your prose, your `[[links]]`, is for you and for whoever reads this book later.
   **Engine block** is not my term for it — it is what the loader's own error messages call it by
   name. A world note or a character note with none fails to load: `VAULT_WORLD_NO_ENGINE_BLOCK`
   (`src/engine/vault.py:125-127`) or `VAULT_CHARACTER_NO_ENGINE_BLOCK`
   (`src/engine/vault.py:150-152`). A block that is present but is not valid JSON fails the same
   way, by a different name: `VAULT_ENGINE_BLOCK_INVALID_JSON` (`src/engine/vault.py:65-71`).

3. **`## Beliefs` — characters only.** One belief per bullet, in the exact shape
   `- (confidence, provenance) claim text`: confidence a number in [0,1], provenance a short phrase
   in your own words, and any `[[links]]` inside the claim become the anchors that can trigger it
   later (`_BELIEF_RE`, `src/engine/vault.py:23`). A confidence outside [0,1] fails loud —
   `VAULT_BELIEF_CONFIDENCE_RANGE` (`src/engine/vault.py:90-92`) — and a `## Beliefs` heading whose
   bullets don't match this shape fails loud too, rather than silently loading as zero beliefs —
   `VAULT_BELIEFS_SECTION_UNPARSED` (`src/engine/vault.py:98-103`).

That is the whole physical shape. What actually goes *inside* the engine block for a world note or
a character note belongs to those forms — this one only needs you to recognise the container, so
you can build a book to test a scene against.

### `world/` — exactly one file

One markdown note describing the world: the setting, the seasons, the **locations** (each with an
id and a description), the **people** who exist, and the **laws** — the things that are impossible
or forbidden here. Your scene will point at a location id and possibly an act from this file, so
you need to have read it before you fill in this form.

> **HOW THIS IS USED:** the engine counts the world-typed notes in this folder and refuses to load
> the book unless there is exactly one — `VAULT_WORLD_NOTE_COUNT` (`src/engine/vault.py:120-123`),
> raising *"need exactly one world note, found N"*. A world note with no engine block (see above)
> raises `VAULT_WORLD_NO_ENGINE_BLOCK` (`src/engine/vault.py:125-127`).

> **A common mistake:** filing your plot outline in `world/`. If the outline has no `type:` line at
> the top, it defaults to `type: world` (see above), counts as a second world note, and the book
> stops loading. Outlines go in `chapters/`.

### `characters/` — one file per person the engine acts

A character file is the person's whole interior: their temperament, their traits, their beliefs,
their standing goals, how they feel right now. This is a separate form (the character blueprint) —
you do not fill any of it in here. You only need to know the **id** of each character, because
your scene names them.

> **HOW THIS IS USED:** the engine requires each character note to carry an engine block
> (`VAULT_CHARACTER_NO_ENGINE_BLOCK`, `src/engine/vault.py:150-152`) with `fixed`, `baseline`, and
> `current` top-level keys, and raises by name if any of the three is missing —
> `VAULT_CHARACTER_BLOCK_INCOMPLETE` (`src/engine/vault.py:154-157`).

> **A book with zero character notes will not load at all — not for a scene, not for the linter.**
> This is the one blocker that will stop you before you write a word of this form: a fresh book
> with a `world/` note and nothing yet in `characters/` raises `VAULT_NO_CHARACTERS`
> (`src/engine/vault.py:161-162`), because `load_book` is the one function both
> `scripts/scene.py` (`scripts/scene.py:683`) and `scripts/lint_book.py`
> (`scripts/lint_book.py:291`) call to open a book — there is no path that gets you further without
> at least one character file already sitting in that folder. Copy one real character in before you
> test-run a new book, even a throwaway one.

### `people/` — one file per person anyone must perceive

This is the part everybody gets wrong first. **Having a character file does not make someone
visible.** A character sheet is what a person *is*; a people note is what other people can *see*.
If Nell has a character file but no entry in the world's people list, then Tam standing three feet
away cannot register that anyone is there.

> **HOW THIS IS USED:** the engine builds the world's people list from **two** sources — first the
> inline `people` array written straight into the world note, then every `.md` file in `people/` on
> top of it (`src/engine/vault.py:131-142`). Either place works. Beck Hollow does it the first way:
> Tam, Nell, and Orrin are all declared inside `world/BeckHollow.md`, and only Faron has his own
> file in `people/`.[^1]

### `scenes/` — this form, and the file made from it

Two files per scene: your filled-in blueprint (for you and your continuity reader), and the cfg
JSON (the only thing the engine reads). If something is in your blueprint but not in the cfg, it
does not exist.

### `runs/` — production notes, and the database. **Do not create the database by hand.**

You copy a template of production notes in here (`canon-ledger.md`, `production-journal.md`,
`story-map.md`, `threads.md`, `continuity-register.md`, and a `cast/` folder). Those are for
humans.

The **database** — a file called `<book-slug>.db` — is the book's permanent record of everything
that ever happened. The engine makes it, names it, and builds its internal structure the first
time you run a scene. If the `runs/` folder does not exist yet, the engine creates that too.

**Where the slug comes from:** the book folder's own name, lowercased, with each space turned into
a hyphen — nothing else (`slug()`, `src/engine/books.py:32-39`:
`os.path.basename(book_dir).lower().replace(" ", "-")`). A book folder named `Beck Hollow` gets the
database `runs/beck-hollow.db` — not an invented example: that is the actual file the reference
book runs against. You never choose the slug and never write it anywhere; naming the folder is
naming the database.

> **HOW THIS IS USED:** the database path is computed as `<book>/runs/<book-slug>.db`
> (`src/engine/books.py:125-128`); the connection code creates any missing parent folder and applies
> the schema on first open (`src/engine/db.py:14-34`). The engine also **refuses** a database that
> belongs to a different book, so you cannot accidentally write one book's scenes into another's
> record (`src/engine/books.py:135-157`).

> **Never hand-create, hand-edit, or copy a `.db` file between books.** The record is append-only —
> once a turn is written it can never be rewound, only corrected forward with a new event. That is
> not just policy; individual tables enforce it. A resubmitted arc-baseline diff that matches what
> is already stored for that turn is a harmless replay and quietly no-ops, but a *different* diff
> arriving for a turn that already has one is refused outright — `LEDGER_ARC_DIFF_REWRITE`
> (`src/engine/ledger.py:132-160`). A hand-made file will either be rejected or, worse, quietly
> accepted with the wrong shape.

### `staging/` and `chapters/`

`chapters/` holds your outline. `staging/` holds anything retired. Neither is read by the engine.

---

---

# THE FORM

Work top to bottom. Where you see a blank line, write on it.

---

## 2. Where and when — the place

### 2.1 Scene name

**Write in the cfg as:** `name`
**REQUIRED**

A short title for this scene. This becomes the chapter heading when the book is rendered into
prose, and it is what you will see in the record when you look for this scene later. Use lowercase
words joined by underscores, numbered so scenes sort in order.

**Beck Hollow's real answer:** `scene_02_the_wall_at_dusk`

> **HOW THIS IS USED:** it is stored as the scene's label when the scene boundary is written to the
> record (`scripts/scene.py:753`), and the narrator uses that label as the heading over the
> finished prose (`scripts/narrate.py:171`).

> **IF YOU LEAVE IT BLANK:** the engine quietly falls back to the cfg's filename
> (`scripts/scene.py:122`), so your chapter heading in the finished book becomes something like
> `scene_02_the_wall_at_dusk_cfg`. Not fatal, but ugly, and it will surprise you at the worst
> moment. Write the name.

**Your answer:**

`name:` ______________________________________________________________________

<br>

### 2.2 Location

**Write in the cfg as:** `location`
**REQUIRED**

Where this scene happens. You do not describe the place here — you write its **id**, which is a
short label already registered in the book's world note. Open `world/` and look at the `locations`
list; use one of those ids exactly, spelling and hyphens included.

**Beck Hollow's registered locations:** `mill`, `beck`, `fold`, `fell-road`, `long-hall`,
`winter-store`

**Beck Hollow scene 02's real answer:** `fold`

> **HOW THIS IS USED, and this is the whole point of the field:** setting the scene's location
> **puts the cast there.** Your cfg value travels straight into the scene slice at
> `scripts/scene.py:368`, then into the perception step, where the engine looks it up in the world
> note and hands every character in the room a percept carrying that place's description — full
> clarity, no perception roll (`src/engine/gate.py:221-230`, reading the location off the scene
> slice at `src/engine/gate.py:127`). That is how Tam knows he is standing at a chest-high drystone
> wall on the low pasture and not in a warm mill. The same location also scopes the world's laws: a
> law written to apply only at one place bears on this scene only if the scene is there
> (`src/engine/law.py:292-322`).[^2]

> **IF YOU LEAVE IT BLANK:** each acting character falls back to their **own** character sheet's
> `current.location` for their own percept: `cfg.get("location") or a["char"]["current"].get("location")`
> at `scripts/scene.py:368`. If that character's sheet has no location set either,
> that character perceives no place at all that beat: no walls, no weather, no description beyond
> whatever you happened to write into the situation prose. Because the fallback runs **per
> character**, two cast members whose sheets carry different `current.location` values can end up
> perceiving different rooms in the very same scene — check that the cast's sheets agree, or just
> set the cfg location and stop worrying about it. If this scene also names an `act` (section 10),
> the world's law check reads the cfg location directly, with no fallback to any sheet
> (`scripts/scene.py:289`) — and an omitted location does **not** narrow a location-scoped law
> away; a caller who supplies no location is handed the same laws as one whose location happens to
> match, on purpose (`src/engine/law.py:292-308`, docstring). A blank location does not make a
> location-scoped law go quiet.

> **A common mistake:** inventing a location instead of using a registered id. Writing
> `"the sheep fold"` where the world note says `fold` gives you a location the engine cannot look
> up. The scene linter catches this one as a hard error: *"location X is not in world.locations — no
> scene can produce a location percept for it"* (`scripts/lint_scene.py:118-121`).

**Your answer:**

`location:` ___________________________________________________________________

---

## 3. Who is in the room

**Write in the cfg as:** `cast[].id`
**REQUIRED — at least one, and you want at least two**

List the people who are physically present and will act in this scene. Write each one's **id** —
the short lowercase label from their character file, not their full name. `tam`, not `Tam Rill`.

Everyone you list here must be two things at once:

1. a character with a file in `characters/`, so the engine has an interior to act from, and
2. an entry in the world's people list, so the *other* people in the room can perceive them.

**Beck Hollow scene 02's real answer:** `tam`, `nell`

> **HOW THIS IS USED:** each id is looked up in the loaded book, and that character's whole
> interior — their profile, their current feelings, their temperament, how outgoing they are — is
> built into an actor for the scene (`scripts/scene.py:307-314`). Each cast member is also
> registered against the run in the permanent record before the first beat
> (`scripts/scene.py:739-740`).

> **IF YOU LEAVE IT BLANK:** the book refuses to load the scene and says so plainly — a scene with
> no cast is not runnable. The cast must be a non-empty list, and every entry must carry both an id
> and a drive (`scripts/scene.py:109-112`).

> **A common mistake — three of them, all caught by the linter:**
> - An id that names nobody: *"cast X is not a character in this book and not in world.people — no
>   one can perceive them and the engine has no sheet to act from"* (`scripts/lint_scene.py:74-77`).
> - Listing the same person twice: *"one seat per character per scene"*
>   (`scripts/lint_scene.py:78-81`).
> - Only one person in the room. This is a warning, not an error, but it is a real one: a scene with
>   no second party cannot produce the collision that makes people talk
>   (`scripts/lint_scene.py:82-84`).

**Your answer:**

`cast[0].id:` __________________________________________________________________

`cast[1].id:` __________________________________________________________________

`cast[2].id:` __________________________________________________________________ *(if needed)*

---

## 4. Whose eyes we watch through

**Write in the cfg as:** `pov`
**REQUIRED**

Which one of the cast we experience this scene through. When the finished scene is turned into
prose, everything is written from inside this person's head — their sensations, their guesses, what
they notice and what they miss. Anything the point-of-view character does not know does not appear
on the page.

Pick one of the ids you just wrote in the cast. One per scene. If you want a different lens, that
is a different scene, not a different sentence.

**Beck Hollow's real answer, both scenes:** `tam`

> **HOW THIS IS USED:** the value is read off the cfg when the scene ends
> (`scripts/scene.py:752`), stored on the scene's row in the permanent record
> (`src/engine/ledger.py:215-222`, and read back at `224-230`), and the narrator binds the entire
> passage to it: *"the scene's POV, or its first actor as a fallback"*, then renders the prose
> through that person's knowledge (`scripts/narrate.py:167-170`).

> **IF YOU LEAVE IT BLANK:** the engine silently uses whoever you listed first in the cast
> (`scripts/scene.py:752`). That is a real choice being made for you by the order you happened to
> type two names in, and it decides whose head the entire chapter is written from. Write it down.

> **A common mistake:** naming someone who is not in the cast. Nothing stops you, and nothing warns
> you — you will simply get a chapter narrated from the viewpoint of a person who was not in the
> room and therefore knows nothing about it. Check your own work here; no tool checks it for you.[^3]

**Your answer:**

`pov:` ________________________________________________________________________

---

## 5. What is happening — the situation

**Write in the cfg as:** `situation`
**REQUIRED — this is the one field the engine will not run without**

A paragraph of plain prose describing the physical circumstance at the instant the scene opens.
Weather, light, temperature, what has just happened, what is standing in the doorway. This is the
single most powerful thing you write. Every character in the room reads it before their first
action, and it is the strongest lever you have over how the scene goes.

**Write conditions and pressure. Do not stage the exchange.**

| Weak — this scripts the scene | Strong — this creates pressure |
|---|---|
| "The dockmaster explains the history of the levy to the young man." | "The dockmaster has the levy notice on the desk and pushes extra silver across it; the young man refuses." |
| "Nell tells Tam about the wolves and asks for his help." | "Nell Harrow is standing in the doorway with a lamp still lit from the walk down, snow to the knee of her, and she has not come about flour." |

The difference: the first pair tell the characters what conversation to have, and the model
obediently produces a lecture. The second pair put objects and bodies in a room and let people
work out what to do.

**Never write anyone's lines.** No dialogue, no quoted speech. The characters generate every word
they say; a scripted line is you doing their job badly.

**Beck Hollow scene 01's real answer** (this is the standard to aim at):

> First light at the mill, and the frost has held three days. Tam has been out on the race since
> four with the long bar, breaking the ice back so the wheel will turn, and his hands have stopped
> feeling like his. The wheel is moving. He is about to go up and sleep. Nell Harrow is standing in
> the doorway with a lamp still lit from the walk down, snow to the knee of her, and she has not
> come about flour. She has lost a fourth ewe in the night. This is the fourth time this winter she
> has come to ask him for something.

Notice what that does: it establishes cold, exhaustion, an interrupted intention (he was going to
sleep), an arriving pressure, and a history — *the fourth time* — all without telling anyone what
to say.

> **HOW THIS IS USED:** the situation text is handed to the acting character at the top of every
> single beat, with the recent transcript appended so they can see what has already been said and
> not repeat themselves (`scripts/scene.py:356`, composing the event the actor perceives). It is
> the ground under the entire scene.

> **IF YOU LEAVE IT BLANK:** the book refuses to load the scene and names this field — a scene cfg
> needs a non-empty situation, checked before anything else happens
> (`scripts/scene.py:107-108`).

> **A common mistake:** narrating the conversation you are hoping for. The linter watches for the
> telltale words — *explains, tells X about, describes, recounts, teaches* — and for any long
> quoted string, and warns that *"rule 1 wants physical conditions and pressure, not the exchange
> staged in advance"* (`scripts/lint_scene.py:106-110`). It is a warning, not a block, because a
> word list cannot really tell. You can.

**Your answer:**

`situation:`

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

---

## 6. What they can pick up — the props

**Write in the cfg as:** `props`
**REQUIRED — exactly 3, 4, or 5. Not two. Not six.**

List the physical objects in the room. These are the things a character can hold, count, slide
across a bench, set down, hide behind, or fail to look at. Without them your characters are two
heads floating in a void, and the scene drifts into talking.

**Write each prop as a phrase somebody could see, not as a label.**

| Weak — a database key | Strong — something a person perceives |
|---|---|
| `lamp` | "her lamp, still lit at first light, burning oil nobody can spare" |
| `wall_gap_north` | "the gap in the wall where the stones have come down, wide enough for a sheep or worse" |
| `tracks` | "wolf tracks in the snow inside the fold line, over the wall and out again" |

The strong versions carry a fact and an implication at once. *Burning oil nobody can spare* tells
you she walked here in the dark and that it cost something. That is a prop doing three jobs.

**Beck Hollow scene 02's real answer** — all five:

1. wolf tracks in the snow inside the fold line, over the wall and out again
2. the lamp set low against the drystone so it does not spoil their eyes
3. the gap in the wall where the stones have come down, wide enough for a sheep or worse
4. the drover's three dogs below the wall, tied, and silent since the light went
5. the fell road above them, climbing past the last wall into open ground

> **HOW THIS IS USED:** each prop becomes a percept handed to every character in the room at full
> clarity, marked as something that must be surfaced to them — no perception roll, no chance of
> missing it (`src/engine/gate.py:174-184`). The engine's comment on why says it plainly: *"an
> affordance withheld is an affordance that does not exist."* The props travel from your cfg into
> the scene at `scripts/scene.py:360`.

> **IF YOU LEAVE IT BLANK:** the objects in the room do not exist to anybody. This is the second of
> the two fields that fail silently. The only way a prop still reaches a character with no `props`
> list is if you also named it inside the situation prose. The linter warns: without affordances
> *"the actors have nothing to do with their hands and the scene drifts to talking heads"*
> (`scripts/lint_scene.py:146-150`).

> **IF YOU WRITE THE WRONG NUMBER:** this one is a hard error and the scene will be refused by the
> linter — *"props: N declared, rule 5 wants 3-5"*, with the reason attached: too few to furnish the
> room, or too many to stay in the actor's attention (`scripts/lint_scene.py:151-154`). A prop
> shorter than three characters is also rejected as *"not a graspable object"*
> (`scripts/lint_scene.py:155-157`).

> **The check worth doing before you move on:** read each character's drive (next section). Does any
> drive point at an object? Then that object must be in this list or in the situation. A drive of
> *"get the stones back up"* against a cfg with no wall in it aims a character at furniture they
> cannot see.

**Your answer:**

1. ____________________________________________________________________________

2. ____________________________________________________________________________

3. ____________________________________________________________________________

4. ____________________________________________________________________________ *(optional)*

5. ____________________________________________________________________________ *(optional)*

---

## 7. What they want — the drives

**Write in the cfg as:** `cast[].drive`
**REQUIRED — one for every person you listed in the cast**

This is the heart of the form, and the field most worth getting right.

### What a drive is

A drive is **what this person is trying to get out of the next few minutes, in this room, from the
person standing in front of them.** It is not their life's ambition. It is not their arc. It is
not what the scene is about. It is the small, immediate, physical thing they are pushing for right
now, and it has to be something they could plausibly want *without knowing how the scene ends*.

Ask it this way: *"What am I trying to extract from, force upon, or protect in the person in front
of me, right now?"*

### The mechanic you must know before you write one

**The drive you write here completely replaces that character's standing goals for the whole
scene.** Not blends with. Not adds to. Replaces. Whatever three carefully-authored long-running
ambitions are sitting in that character's file, the moment the scene starts they are gone and this
one sentence is the only thing the character wants.

> **HOW THIS IS USED:** `scripts/scene.py:309` —
> `ch["current"]["active_goals"] = [{"goal": c["drive"], "urgency": 0.8}]`, commented in the source
> itself as *"the scene DRIVE overrides sheet goals"*. It runs unconditionally, for every cast
> member, at the top of every scene.

This is the single most surprising thing about authoring a scene, so say it back to yourself: **if
a long-running want of this character still matters in this room, you have to put it in the drive.
Nothing else will carry it in.** The goals on their character sheet still matter for making them a
coherent person, and the book linter still checks them — but during a scene they are not what the
character is chasing.

You also cannot make one person want it more than another through this field. Every drive is
handed the same weight (`0.8`, hardcoded at `scripts/scene.py:309`). Relative pressure is set
elsewhere — see the opening tags in section 9.

### Good drives and weak drives, side by side

**Beck Hollow scene 01, Nell — strong:**

> "get him to say yes to walking up to the fold with her before dark — not tonight, not to fight
> anything, just to be a second pair of hands at the wall"

**The weak version of the same want:**

> "convince Tam to help her with the wolf problem"

Why the first one is better: it names a *specific physical outcome* (say yes, walk up, before
dark), it names what she is deliberately **not** asking for (not tonight, not a fight) — which
tells you she has already thought about how he will hear it — and it is blind to whether she gets
it. The weak version is a summary of the scene, not a want. A character handed a summary produces
a summary.

**Beck Hollow scene 01, Tam — strong:**

> "finish reporting the state of the race, get up the stairs, and be asleep before she asks him the
> thing she came to ask"

**The weak version:**

> "avoid getting involved"

The strong one is three concrete physical actions in sequence, with a deadline attached — *before
she asks* — that puts him in direct collision with her want. The weak one is a mood. A mood
generates no behaviour.

**Beck Hollow scene 02, both — strong, and notice they collide:**

- Tam: *"get the stones back up, get the count done, and be off this hill and back down at the mill
  before the light is fully gone"*
- Nell: *"keep him here long enough to see the tracks for what they are, and not frighten him off
  the hill doing it"*

He wants to leave. She wants him to stay. Neither of them is arguing about the wolves; they are
arguing about a wall and the light. That is the shape you are aiming for.

### The rule of collision

If two people want compatible things, they agree, and the scene stops. The engine measures how much
each person is moved to speak, and when nobody is moved enough, it ends the scene. **Friction is
what produces beats.** Before you move on, check: does one person's want run into something the
other person is protecting?

> **IF YOU LEAVE IT BLANK:** the book refuses to load the scene and names the field — every cast
> entry must carry both an id and a drive (`scripts/scene.py:109-112`).

> **Common mistakes, all caught by the linter:**
> - **Copying the situation into the drive.** Hard error: *"a drive is what THIS person wants from
>   the other, not a restatement of the moment"* (`scripts/lint_scene.py:92-94`).
> - **Writing a drive aimed at the reader.** Words like *introduce, establish, set up, showcase,
>   demonstrate, the reader, world lore* all trigger a warning: the engine wants an in-room want,
>   not exposition (`scripts/lint_scene.py:95-99`).
> - **Giving everyone the same drive.** Warning: *"aligned goals produce zero urge and the scene
>   lulls immediately"* (`scripts/lint_scene.py:101-104`).
> - **Writing a topic instead of a physical goal.** Nothing catches this one, and it is the most
>   costly. "Discuss the wolves" is a topic. "Get the stones back up before the light goes" is a
>   goal. Give them something to do with their hands and their feet, not a subject to cover.

**Your answers:**

`cast[0].drive:` (for _____________)

_______________________________________________________________________________

_______________________________________________________________________________

<br>

`cast[1].drive:` (for _____________)

_______________________________________________________________________________

_______________________________________________________________________________

<br>

`cast[2].drive:` (for _____________) *(if needed)*

_______________________________________________________________________________

_______________________________________________________________________________

---

## 8. Who the moment is about — the subject

**Write in the cfg as:** `subject`
**REQUIRED**

Two answers: a **person** and a **group**. Together they say who this moment concerns.

The person is a character id — often one of the cast, but it can be someone absent. A child who has
not come home is the subject of a scene she is not in. The group is a label the world note attaches
to people (a village, a household, a faction), and it lets someone who does not care about the
individual still care about the class.

**Where the group label comes from:** you do not invent it here — it is authored once, on the
person, as `people[].groups` in the world note (the world blueprint's §7.5 covers filling that in;
the short version: a list of your own class names — `"outsider"`, `"drovers"`, `"fell folk"` — with
no fixed vocabulary). A worked entry, illustrative rather than shipped in Beck Hollow itself:
Faron is a drover wintering over among villagers, so his `people[]` entry could carry
`"groups": ["drover", "outsider"]`, and a scene whose subject group is `"outsider"` would then land
harder on a character who regards outsiders warily than on one who does not, without you having to
name Faron at all.

**Beck Hollow's real answer, both scenes:** `["tam", "hollow"]`

> **HOW THIS IS USED:** the subject scales how much of the moment lands on each listener. When a
> scene names a subject, the caring dimensions — concern for someone, and grief at loss — are
> multiplied by how much *that particular listener* regards that particular subject
> (`src/engine/state.py:388-389`, computed at `src/engine/state.py:437`). Someone who holds the
> Hollow in high regard is moved by a threat to the Hollow; someone who does not is not. The subject
> also seeds who the scene is *about* for the first beat, so beat one is not blind
> (`scripts/scene.py:351`). The group half is looked up in an index built from `people[].groups`
> across the world's people notes (`src/engine/scene.py:393-407`).

> **IF YOU LEAVE IT BLANK:** the scene runs, but nothing is scaled by regard. Everyone in the room
> reacts to the moment identically regardless of who they care about — which flattens exactly the
> difference you built those characters to have. The engine substitutes an empty pair
> (`scripts/scene.py:113-114`).

> **A common mistake:** naming somebody the book has never heard of. Hard error: *"subject X
> resolves to nobody in this book — the regard scoping it exists for will never fire"*
> (`scripts/lint_scene.py:112-116`).

**Your answers:**

`subject` person: _____________________________________________________________

`subject` group: ______________________________________________________________

---

## 9. How hard it lands — the opening tags

**Write in the cfg as:** `opening_tags.dimensions`
**REQUIRED — pick one to three of the seven**

This is where you say what *kind* of pressure the opening moment carries, and roughly how much.

### The seven, and only these seven

These are the only labels that mean anything. They are fixed in the engine's code, not in prose:

| Label | Roughly means |
|---|---|
| `threat` | something here could hurt someone |
| `loss` | something is gone, or going |
| `care_relevant` | someone's wellbeing is at stake |
| `mastery` | there is something to be good at, or to fail at |
| `attraction` | someone is drawn toward someone or something |
| `relief` | a pressure is coming off |
| `social_violation` | a rule between people has been broken |

> **These come from the code, not from a document:** the legal set is the key list of
> `_DIM_TO_PRIMARY` in `src/engine/state.py:53` and following, which is exactly
> `attraction, care_relevant, loss, mastery, relief, social_violation, threat`.

**Anything else you write here is a hard error**, and the linter says why: *"is not one of the legal
seven — appraise() silently ignores it"* (`scripts/lint_scene.py:127-135`). It is an error precisely
because nothing downstream complains. A misspelled dimension is authored, shown to nobody, and
computes nothing.

### Sizing them

Each label takes a number between 0 and 1. **You are not expected to derive these numbers, and this
form deliberately does not teach you to.** Sizing event magnitudes is a separate, normative
discipline that lives in `docs/standard-vectors.md` §3 — it is owned there, and whoever is
responsible for the book's vector calibration does the sizing.

What you need to supply is the **judgement**, in words, and let them place it:

| In words | Meaning |
|---|---|
| leave it out entirely | this stake is not touched — the right answer for most labels on most events |
| ordinary friction | recoverable, routine, the texture of a day |
| real but bounded | a genuine stake, but recoverable on a normal path |
| severe | something genuinely at risk; the event people retell afterwards |
| grave | irreversible loss is probable, not merely possible |

**Omission is the normal case.** Most events touch one or two of the seven. A scene tagged with all
seven is a scene with no shape.

**Beck Hollow's real answers:**
- Scene 01 (a neighbour asking for help at first light): `care_relevant` and `loss`, both in the
  *real but bounded* band.
- Scene 02 (wolf tracks inside the fold): `threat` in the *severe* band, `care_relevant` *real but
  bounded*.

> **HOW THIS IS USED:** the opening tags are appraised against every person in the room, and
> **whoever the moment lands on hardest speaks first** (`scripts/scene.py:341-342`, choosing the
> opener by the size of the emotional movement). This is the only lever you have over who opens the
> scene, and it is why you cannot express relative urgency through drives. The appraisal reads the
> dimensions and the subject (`src/engine/state.py:423` and `437`) and nothing else in this block.

> **IF YOU LEAVE IT BLANK:** the engine substitutes an empty set of dimensions
> (`scripts/scene.py:121`), nobody is moved by the opening, and the first speaker is decided by a
> tie. The scene still runs. It just starts flat.

> **A common mistake — and this one is important:** inflating a number to make something happen.
> It does not work. A single appraisal on a settled character almost never changes the next line, by
> design. When a scene goes flat, the fix is **the situation text**, by a wide margin — then the
> drives. Not the numbers. Sizing a stake up to force motion is the best-documented anti-pattern in
> this system.

**Your answers:**

| Label (from the seven) | Your judgement in words |
|---|---|
| ______________________ | ______________________________________ |
| ______________________ | ______________________________________ |
| ______________________ | ______________________________________ |

---

## 10. Optional: the act the world must permit

**Write in the cfg as:** `act`
**OPTIONAL — leave it out unless this scene turns on something the world forbids**

Some worlds have laws: things that are impossible here, or forbidden here, or required here. If
this scene hinges on somebody attempting one of those things, name it, and the world will rule on
it before the scene starts.

Use an act exactly as the world note spells it.

**Beck Hollow's three acts:** `summon-outside-help`, `treat-the-pack-as-sent`,
`let-the-race-ice-over`

> **HOW THIS IS USED:** if you set an act, the world is consulted before the first beat. If a law
> declares the act **impossible**, the scene is refused outright and tells you which law denied it
> and why. If a law only **forbids** it, the scene runs and prints the consequences it will cost
> (`scripts/scene.py:281-299`). Which laws bear on the question is scoped: a law is consulted only
> where its act matches and its place matches — so the same act may be permitted in one location and
> impossible in another — and that scoping is honoured, never fuzzy-matched
> (`src/engine/law.py:292-322`, called from `scripts/scene.py:289` with both the act and this
> scene's location). Laws may also be scoped to who is acting, who is acted on, and a window of
> time, and those scopes are live too: a law scoped `actor_class: "noble"` bears on a noble and not
> on a peasant, and a law scoped `time_from: 100` / `time_to: 200` bears at ticks 100–200 inclusive
> and not at 50 or 250. This pre-flight check, though, is run before any actor is chosen, so it can
> only supply the act and the location — not yet an actor's class or a tick. Per the engine's own
> rule, a scope the caller cannot supply does not narrow the law away, it just cannot be ruled out
> on that facet yet. The SAME check runs again on every act an actor actually reports mid-scene,
> and there it also knows the speaker's own class (read off their sheet) and the turn number as the
> time facet (`scripts/scene.py:487-488`, calling `_law_events`, defined at `scripts/scene.py:202`
> and reading the speaker's class at `scripts/scene.py:226-231`) — so
> a class- or time-scoped law that the pre-flight could not rule out can still take hold, or not,
> once the scene reaches the actor and moment it actually names.[^4]

> **IF YOU LEAVE IT BLANK:** the world is not consulted at all, and the scene runs unchecked
> (`scripts/scene.py:281-282`). That is deliberate, not laziness — with no act named, every law in
> the book would bear on the scene at once and most of them would deny it, so every scene would be
> refused. Name an act only when you mean to put it to the world.

> **A common mistake:** inventing an act. Hard error: *"act X is keyed by no law in this world — the
> pre-flight will find nothing to bear on it"*, and the linter lists the acts the world actually
> declares (`scripts/lint_scene.py:137-141`).

**Your answer:**

`act:` _____________________________________________ *(or leave blank)*

---

## 11. Optional: time since the last scene

**Write in the cfg as:** `elapsed`
**OPTIONAL — leave it out for a scene that follows straight on**

How much time has passed since the previous scene. The unit is **yours** — scenes, days, weeks,
whatever you are counting in. The engine holds no clock and converts nothing; it only uses the
number as an amount of settling.

> **HOW THIS IS USED:** at the start of the scene, once, every relationship the cast holds relaxes
> a little way back toward that character's resting disposition (`scripts/scene.py:323-333`). Warmth
> fades fastest, respect and trust more slowly, and a debt owed barely fades at all — a favour is
> not forgotten by the passage of a week (`src/engine/bonds.py:92`, applied at
> `src/engine/bonds.py:359-386`). It happens between scenes, never between beats, because a single
> conversation must not be allowed to cool a friendship.

> **IF YOU LEAVE IT BLANK:** nothing drifts. The cast walks into this scene feeling exactly what
> they felt at the end of the last one. That is correct for a scene that follows immediately, and
> wrong for one that follows a month later.

**Your answer:**

`elapsed:` __________________________ *(and say what unit you mean: ____________)*

---

## 12. Fields you can leave blank — nothing reads them

You will see these in older examples and older documents. **Do not spend time on them.** They are
listed here so you know to skip them rather than wondering what you missed.

| Field | Why you can skip it |
|---|---|
| `opening_tags.type` | A word like `mundane`, `care`, `threat` sitting beside your dimensions. The engine's appraisal reads the dimensions and the subject and never looks at this (`src/engine/state.py:423`, `437` — no read of `type` anywhere in the appraisal). Beck Hollow writes one for human legibility; it changes nothing. If you write one anyway, write something real rather than inventing a word. |
| `opening_tags.durability` | `transient` or `durable`. The two-value vocabulary is genuinely real — it is a frozen set of exactly those two words at `src/engine/consolidation.py:34`, and elsewhere in the engine it decides whether a moment becomes a lasting memory (`src/engine/acquisition.py:36` and `129`) or moves a character permanently (`src/engine/arc.py:78`). **But that is the value the acting character reports about their own action, beat by beat — not the one you write here** — and on THAT value the vocabulary is now enforced by name: an actor's turn with no durability at all raises `TAG_DURABILITY_MISSING`, and one with anything other than `transient`/`durable` raises `TAG_DURABILITY_INVALID` (`src/engine/consolidation.py:568-580`). The only thing the scene's opening tags are used for is choosing the first speaker (`scripts/scene.py:341-342`), and that calculation never reads durability.[^5] |
| anything else you invent | The engine carries unknown keys and reads none of them. A note-to-self in the cfg is harmless and inert. |

**And these belong to other forms, not this one.** If you find yourself wanting to write a
character's fears, skills, health, or standing goals into a scene cfg, stop — those live in the
character blueprint, and several of them reach no code at all. This form covers the scene only.

---

## 13. Four traps that catch everybody once

The first is a scene trap and it is the one that will bite you. The other three are character-sheet
traps, listed here because they produce symptoms that look like a broken scene.

### Trap 1 — the drive erases the character's standing goals

Covered in full in section 7, repeated here because it is the one people do not believe until they
see it. `scripts/scene.py:309` overwrites the character's active goals with your one drive
sentence, unconditionally, for every cast member, at the start of every scene. Their sheet goals
still matter for making them coherent and the book linter still checks they are there — but during
a scene, your sentence is the only thing they want.

**The symptom when it bites you:** a character behaves as though they have forgotten something you
carefully established about them. They have. Put it in the drive.

### Trap 2 — a character trait written as "very high" is read as "typical"

In a character file, the built-in dispositions are written as single words — `low`, `typical`,
`elevated`, `high`. **Only the first word is read.** Writing `"very high"` is parsed by taking the
word before the space, finding no match for `"very"`, and falling back to `typical`
(`src/engine/state.py:239`, and again at `src/engine/arc.py:44`). Measured on a live book, this
understated a real character's drive by about a third, silently.

**The symptom:** a character you wrote as extreme behaves as though they were average.

### Trap 3 — a wound with no matching rule computes nothing

A character can be given a wound with a list of things that trigger it. If nothing in the
character's rule table matches those trigger words, the wound is prose the engine cannot compute —
it never fires, however intense you said it was. The book linter warns about exactly this: *"the
wound is prose the engine cannot compute (intensity X reaches no arithmetic)"*
(`scripts/lint_book.py:235-248`). Four such wounds were found in one live book.

**The symptom:** a character walks straight through the thing that was supposed to break them.

### Trap 4 — a "leaning" written as a number crashes the scene

If a character sheet describes a leaning or orientation as a number on a scale from minus one to
plus one, the run fails when the prompt is built. The layer that turns numbers into plain words
accepts anything between 0 and 1 and **refuses** anything outside that range, on purpose: a number
outside [0,1] *"is not a weight, it is something else wearing a float"*
(`src/engine/identity_view.py:175-177`). Write these as words, not numbers.[^6]

**The symptom:** the scene will not start, and the error names a field on the character sheet.

---

## 14. Pre-flight — before you spend a run

Work down this list with your filled form in front of you.

**The machine will check these for you:**

- [ ] Every cast id names a real character *and* a person the world knows about
- [ ] Nobody is listed in the cast twice
- [ ] The location is one of the world's registered location ids
- [ ] The subject names somebody the book has heard of
- [ ] Exactly 3–5 props, each a real phrase
- [ ] Every dimension is one of the legal seven, and each number sits between 0 and 1
- [ ] If you named an act, some law in the world is keyed to it

Run it:

```
python scripts/lint_scene.py --book <your book> --scene <your cfg file>
```

**Only you can check these:**

- [ ] There is exactly **one** pressure in this scene. If you need two sentences joined by "and" to
      say what it is about, it is two scenes.
- [ ] Every drive is a physical goal, not a topic
- [ ] The drives collide — one person's want runs into something another is protecting
- [ ] Every object any drive points at is in the props or in the situation
- [ ] The point-of-view character is actually in the cast
- [ ] Nothing in the situation, props, or any drive mentions something these characters could not
      possibly know
- [ ] No dialogue anywhere in the situation

**A clean lint is not a verified scene.** The tool prints, in its own output, the things it did not
check — the collision test and the knowledge boundaries are semantic and are yours
(`scripts/lint_scene.py:159-162`).

---

## 15. A complete filled example

This is Beck Hollow scene 02, exactly as it runs. Read it as a model for your own.

**Name:** `scene_02_the_wall_at_dusk`

**Location:** `fold` — *the drystone sheep fold on the low pasture, walls chest-high, a hurdle
gate. Close enough to the village to hear a dog from, far enough that nobody sees what happens at
night.*

**Cast:** `tam`, `nell`

**Point of view:** `tam`

**Situation:**

> Dusk at the fold, and Tam came. He came because it was a task — go up, look at the stones, come
> down — and a task is the one thing he can carry. The light is going faster than either of them
> planned for. Nell has the lamp low against the wall so it does not spoil their eyes. There are
> tracks in the snow inside the fold line, come in over the drystone and gone out again the same
> way, and they are not a dog's. Below the wall the drover wintering in the long hall has his three
> dogs tied and they have not made a sound since the light started to go. Above them the fell road
> climbs out of the hollow past the last wall, and there is nothing up there but open ground.

**Props:**

1. wolf tracks in the snow inside the fold line, over the wall and out again
2. the lamp set low against the drystone so it does not spoil their eyes
3. the gap in the wall where the stones have come down, wide enough for a sheep or worse
4. the drover's three dogs below the wall, tied, and silent since the light went
5. the fell road above them, climbing past the last wall into open ground

**Drives:**

- **tam** — get the stones back up, get the count done, and be off this hill and back down at the
  mill before the light is fully gone
- **nell** — keep him here long enough to see the tracks for what they are, and not frighten him
  off the hill doing it

**Subject:** person `tam`, group `hollow`

**Opening tags:** `threat` — *severe*. `care_relevant` — *real but bounded*.

**Act:** none. **Elapsed:** none — this follows scene 01 the same day.

### Why this scene works

One pressure: *will he stay on this hill long enough to understand what he is looking at?* Both
drives are physical and sequenced — stones, count, get off the hill; keep him here, don't spook
him. They collide directly: his deadline is her obstacle. Every prop is doing work — the gap is
what he came to fix, the tracks are what she needs him to see, the silent dogs are the fact neither
of them has said out loud yet, and the fell road is where this is all going. And nobody is
discussing wolves. They are arguing about a wall and the light.

---

## 16. The blank form, to copy out

Photocopy this page, or copy the block below into a fresh file.

```
SCENE BLUEPRINT

  Name        (required)  ______________________________________________

  Location    (required)  ______________________________________________
              a location id from the world note

  Cast        (required)  ______________________________________________
              character ids, one per line

  Point of view (required) _____________________________________________
              one of the cast

  Situation   (required)
  ____________________________________________________________________
  ____________________________________________________________________
  ____________________________________________________________________
  ____________________________________________________________________
              physical conditions and pressure. no dialogue.

  Props       (required, 3-5)
    1. _______________________________________________________________
    2. _______________________________________________________________
    3. _______________________________________________________________
    4. _______________________________________________________________
    5. _______________________________________________________________
              perceivable phrases, not labels

  Drives      (required, one per cast member)
    ________ : _______________________________________________________
              _______________________________________________________
    ________ : _______________________________________________________
              _______________________________________________________
    ________ : _______________________________________________________
              _______________________________________________________
              what they want out of THIS room, right now.
              REMEMBER: this replaces their standing goals for the scene.

  Subject     (required)  person: ____________  group: ____________

  Opening tags (required, 1-3 of the legal seven)
    attraction / care_relevant / loss / mastery / relief /
    social_violation / threat
    ______________ : ____________________________________
    ______________ : ____________________________________
    ______________ : ____________________________________
              say it in words: ordinary friction / real but bounded /
              severe / grave. omission is normal.

  Act         (optional)  ______________________________________________
              only if the scene turns on something the world's laws rule on

  Elapsed     (optional)  ________  unit: ______________________________
              time since the last scene, in your own unit
```

### And here is the shape of the file it becomes

Whoever types this up will produce exactly this. You do not need to write it, but it helps to
recognise it. The order of the keys does not matter.

```json
{
  "name": "scene_NN_short_title",
  "pov": "character_id",
  "location": "location_id",
  "situation": "Plain prose. Conditions and pressure. No dialogue.",
  "props": [
    "a perceivable phrase, not an identifier",
    "three to five of them",
    "each one something a person could pick up or look at"
  ],
  "subject": ["character_id", "group_name"],
  "opening_tags": {
    "dimensions": { "threat": 0.0, "care_relevant": 0.0 }
  },
  "cast": [
    { "id": "character_id", "drive": "physical, in-the-moment, blind to outcome" },
    { "id": "character_id", "drive": "physical, in-the-moment, blind to outcome" }
  ]
}
```

---

## 17. Footnotes: places where the existing docs are wrong

If you are reading the project's other documents alongside this form, these four will contradict
what you have just read. **This form follows the code.**

[^1]: `docs/new-book-manifest.md:128` says the world's people list is built from `people/*.md`
notes *only*. It is not. `src/engine/vault.py:131` starts from the world note's own inline `people`
array and *then* appends the files in `people/` on top: `people = list(world.get("people", []))`.
Both places work, and Beck Hollow uses the inline form for its three main figures.

[^2]: **Corrected from an earlier version of this document.** This footnote used to say
`docs/template-scene-blueprint.md:40-49` claimed the scene's location "does less than it looks
like" and told you to set each character's own location by hand instead — that paragraph
documented a defect as though it were a design property. As of 2026-08-30 the defect is fixed, and
that document says so too, in its own words: `docs/template-scene-blueprint.md:39-54` now carries a
"History, so it does not get re-broken" note describing the exact same fix section 2.2 above
describes. The location arrives at `scripts/scene.py:368`; what it becomes is
`src/engine/gate.py:221-230`.

[^3]: `pov` fares half-better in `docs/template-scene-blueprint.md` than it used to: §1 now names it
in prose (`docs/template-scene-blueprint.md:38`, "POV Actor"). But it is still absent from the §7
JSON payload template that is supposed to be the whole cfg
(`docs/template-scene-blueprint.md:199-220` — no `"pov"` key anywhere in it) and from that section's own "Required" / "Optional but
consumed" field list (`docs/template-scene-blueprint.md:222-225`) — despite being read at
`scripts/scene.py:752`, stored at `src/engine/ledger.py:215-222`, and binding the entire narration
at `scripts/narrate.py:167`. Treat it as required, as this form does.

[^4]: **Corrected from an earlier version of this document.** This footnote used to say law scoping
by actor class, target class, and time window was stored but "being wired into the bearing check."
As of 2026-08-30 it is wired, and is the live check: `src/engine/law.py:292-322` (`_applies`),
storage at `src/engine/law.py:151-155`, persisted at `370-374`. Verified: a law scoped
`actor_class: "noble"` bears on a noble and not a peasant; a law scoped `time_from: 100` /
`time_to: 200` bears at ticks 100–200 inclusive and not at 50 or 250; an unscoped law still bears
on everyone, always. And the asymmetry that matters for a caller: a scope the caller cannot supply
(an argument left `None`) does **not** narrow the law away — only a scope the caller *can* supply
and that disagrees rules the law out (`src/engine/law.py:292-308`, docstring). Write scoped laws
expecting the scope to be honoured.

[^5]: **Corrected from an earlier version of this document.** This footnote used to say
`docs/driving-the-engine.md:100` and `docs/arc-engine.md:34` described durability in terms of
"marking" and "reshaping", and that those two documents were being corrected. They have been, as of
2026-08-30: `docs/arc-engine.md:34` now reads `transient | durable` and says outright
"**corrected 2026-08-30** — this line read `transient | marking | reshaping`";
`docs/driving-the-engine.md:100-104` says the same and adds that sending either retired value now raises
`TAG_DURABILITY_INVALID` by name. The validator accepts exactly two words and nothing else —
`frozenset(["transient", "durable"])` at `src/engine/consolidation.py:34`, checked at
`src/engine/consolidation.py:568-580` (raising `TAG_DURABILITY_MISSING` or `TAG_DURABILITY_INVALID`
by name) — and every consumer treats it as a simple yes-or-no (`src/engine/acquisition.py:36` and
`129`; `src/engine/arc.py:78` tests `== "durable"`). The two-value vocabulary is, and always was,
the truth.

[^6]: `docs/drives-schema.md:50-53` gives a character's orientation as a number from minus one to
plus one. Authored that way, it crashes the prompt build — see trap 4. Write words.

---

*Other documents worth knowing exist: `docs/scene-authoring-rules.md` (the seven normative rules
this form is built on), `docs/standard-vectors.md` §3 (who owns the sizing of event magnitudes),
`docs/new-book-manifest.md` (the whole book-folder contract). You do not need any of them to fill
in this form.*
