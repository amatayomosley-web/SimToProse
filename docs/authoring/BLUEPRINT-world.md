# The World Blueprint

**A hand-fillable sheet for building a world and the people who live in it.**

Print this. Sit with it and a pen. Work top to bottom — nothing on this sheet asks you for
something that depends on an answer further down. When you reach the end you will have written
one file, `world/YourWorld.md`, and optionally a small stack of `people/*.md` files, and the
engine will load them and run.

You are not writing code. Every box on this sheet is a sentence, a name, or a yes/no. There is
no arithmetic anywhere in this document, and there is none in the file you are about to write.

Every field below tells you four things:

- **what it is**, in plain words;
- **the legal values**, where the engine only accepts certain ones — always quoted from the
  actual code, never from a guide;
- **>> HOW THIS IS USED** — the one or two sentences of what the machine really does with your
  answer, with the exact file and line so you can go look;
- **IF YOU LEAVE IT BLANK** — what actually happens.

Where a field reaches no code at all, this sheet says so and tells you to skip it. You will
not be asked to fill in anything inert.

---

## Contents

1. Before you start — how the file is shaped
2. The name and the premise
3. The three switches — the only questions you are not allowed to skip
4. Inherited defaults (`blueprint_defaults`)
5. Standing facts — the things that are simply true
6. Locations — the places a scene can be set
7. People — the walk-on cast
8. The lexicon — the words the engine watches for
9. Laws — what the world refuses, forbids, and demands
10. Check your work
11. A complete filled example
12. Blank template to copy out
13. Footnotes: where the project's own docs are wrong

---

# 1. Before you start — how the file is shaped

Your world lives in **one markdown file** inside a folder called `world/`, sitting beside two
sibling folders:

```
YourBook/
  world/       <- exactly ONE file, the world note. This blueprint.
  people/      <- optional. One file per walk-on person.
  characters/  <- the full character sheets (a separate blueprint)
  runs/        <- the engine writes here. Never you.
```

The world note has three parts, in this order:

**(a) Frontmatter** — two lines between `---` fences at the very top.

```
---
type: world
id: A one-line sentence naming this world and its pressure
---
```

**(b) Prose** — write whatever you like. Headings, paragraphs, your own notes to yourself.
Only the parts named below are read by the machine; the rest is yours, and it is worth
writing, because you will re-read this file more often than the engine will.

**(c) One fenced JSON block.** This is the part the engine reads. It is a line of three
backticks followed by the word `json`, then your content, then a line of three backticks.

Three mechanical facts about that block, because getting them wrong is the most common way a
first draft fails to load:

- **Only the FIRST fenced json block in the file is read.** A second one further down is
  ignored entirely — no warning. (`src/engine/vault.py:64-69` takes `blocks[0]`.)
- **It must be valid JSON.** Straight double quotes, not curly ones. A comma between every
  pair of entries and *no* comma after the last one. If it is malformed the book refuses to
  load and the error names your file and the position of the problem
  (`src/engine/vault.py:66-69`).
- **JSON has no comments.** If you want a note to yourself, put it in the prose above the
  block, or add a `"note"` key with your sentence in it — an unrecognised key is carried, not
  refused (`src/engine/vault.py:33-48`).

> **A tip worth the ten minutes.** Before you fill in section 8 (the lexicon), write out the
> text of one scene's opening event — two or three sentences of what happens. You will harvest
> your lexicon words straight out of it, and they will then be the right words. Do it now, on
> the back of this page.

**Exactly one world note.** If `world/` holds two files that both count as world notes, the
book refuses to load and says how many it found. Zero does the same
(`src/engine/vault.py:116-118`). A file with no JSON block at all is also refused, by name
(`src/engine/vault.py:120-121`).

---

# 2. The name and the premise

## 2.1 `type` (frontmatter)

**REQUIRED.** Write the literal word `world`.

Legal value: the loader keeps a note from `world/` when its type is `world`, or when it has no
`type` line at all — `worlds = [n for n in notes_in("world") if (n["type"] or "world") == "world"]`
(`src/engine/vault.py:116`). Anything else (`type: concept`, `type: note`) makes the file
invisible, and if it was your only world note the book will not load.

>> **HOW THIS IS USED:** it is the filter that decides whether this file is your world at all
(`src/engine/vault.py:116`).

**IF YOU LEAVE IT BLANK:** it defaults to `world`, so a blank works — but write it anyway. The
blank only holds while this is the only file in `world/`, and the day you add a second one you
will not remember which rule you were relying on.

```
type:  ____________________
```

## 2.2 `id` (frontmatter)

**REQUIRED.** One line. Not a filename, not a slug — a sentence that names the world *and* the
thing pressing on it.

Worked example, from the reference book (`Beck Hollow/world/BeckHollow.md:3`):

> `id: Beck Hollow — a valley village under a hard winter, and the wolves working down off the fell`

>> **HOW THIS IS USED:** it becomes the world's title if you do not set one inside the JSON
block — `world.setdefault("world", wnote["id"])` (`src/engine/vault.py:122-123`). That title is
handed to the narrator when a scene is rendered into prose (`scripts/narrate.py:134`).

**IF YOU LEAVE IT BLANK:** the loader falls back to the file's own name without its extension
(`src/engine/vault.py:51`), so your world will be called `BeckHollow` — and the narrator will
be told the world is called `BeckHollow` and nothing else.

```
id:  __________________________________________________________________
```

## 2.3 The premise prose

**REQUIRED of you, not of the machine.** Above the JSON block, write two things:

- a paragraph or two of what this place is;
- a short section headed something like *"The premise this world exists to test"* — one claim
  the whole book is an apparatus for.

The reference book's is three sentences (`Beck Hollow/world/BeckHollow.md:16-20`):

> A man who is afraid can be made brave by his circumstances, or broken further by them, and
> the difference is not courage — it is whether he is rested and whether he is loved. The
> village is the apparatus. The wolves are the pressure. Nobody writes what he does.

>> **HOW THIS IS USED:** it reaches no code. It reaches *you*, every time you sit down to
decide whether a law or a location earns its place. The project's own rubric makes it the first
meta-rule: "Every law choice must serve the one-line conceit, or it's arbitrary"
(`docs/universal-law.md:9`).

**IF YOU LEAVE IT BLANK:** nothing breaks and everything gets harder. You will find yourself
adding laws because they sound like the genre rather than because this book needs them.

**A good premise vs a weak one.**

| weak | good |
|---|---|
| "A grim medieval village in winter." | "A man who is afraid can be made brave by his circumstances, or broken further by them, and the difference is whether he is rested and whether he is loved." |
| Describes the set. Nothing can fail it. | Names a claim. A scene can prove it, and a scene can prove it wrong. |

## 2.4 `world` (the title, inside the JSON block)

**REQUIRED.** Key path: `world`

A short proper name. Not the long premise line — that was `id`.

Worked example: `"world": "Beck Hollow"` (`Beck Hollow/world/BeckHollow.md:24`).

>> **HOW THIS IS USED:** it is put in front of the narrator model as the world's name when a
recorded scene is turned into prose — `"WORLD: %s" % str(world.get("world", ""))`
(`scripts/narrate.py:131-134`).

**IF YOU LEAVE IT BLANK:** the loader fills it from the frontmatter `id`
(`src/engine/vault.py:122-123`), so the narrator gets your whole premise sentence as the
world's name. Not fatal. Untidy.

*(Footnote 1 at the end of this sheet: two of the project's own docs list this field as inert.
They are out of date.)*

```
"world":  ____________________
```

## 2.5 `timeline` — OPTIONAL

Key path: `timeline`

A single word or short phrase naming which *stretch of the story* this world note describes —
`"early"`, `"the siege year"`, `"after the thaw"`. It is a label you choose; the engine has no
list of legal values.

>> **HOW THIS IS USED:** it is a lookup key. When a scene is rendered to prose, the narrator
looks up `cfg.spines[world.timeline]` in the book's `book.json` and uses whatever prose-register
it finds there as the section's authorial spine (`scripts/narrate.py:76`; the spine is injected
into the narrator's instructions at `scripts/narrate.py:109-111`).

**IF YOU LEAVE IT BLANK:** the lookup returns nothing, the spine line is omitted, and the prose
renders in a neutral register (`scripts/narrate.py:73-74`: "Any piece may be absent;
build_narration_prompt omits what is None and degrades to a neutral render"). The reference book
leaves it blank.

**Common mistake:** setting `timeline` when your `book.json` has no `spines` entry with that
exact key. The lookup quietly finds nothing and you get the neutral render you would have got by
leaving it blank. If you set it, go add the matching spine.

```
"timeline":  ____________________          (or leave out entirely)
```

## 2.6 `season` — LEAVE BLANK. Nothing reads it.

Key path: `season`

**Nothing reads it.** Not the gate, not the bible, not the scene assembler, not the critic, not
the narrator. It is stored in the book's pinned record and read back by nothing. There is no
consumer anywhere in `src/` or `scripts/`.

**Where the answer actually belongs:** if the season must reach a character, it goes in one of
three live places — a **standing fact** so the continuity critic holds you to it (section 5), a
**lexicon class** so a character can perceive it (section 8), or the **event text** of the
scene itself, which is the only world a character perceives on a given turn.

The reference book fills it in anyway, as an author's anchor
(`Beck Hollow/world/BeckHollow.md:25`: `"the third week of a winter that came a month early"`).
That is a fine reason to write it. Just do not expect it to do anything.

---

# 3. The three switches

**All three REQUIRED. These are the only questions on this sheet you are not permitted to leave
unanswered.**

Key paths: `switches.magic`, `switches.divine`, `switches.beings`

Each takes exactly `true` or `false` — the bare JSON words, no quotes around them.

| switch | the question you are answering |
|---|---|
| `magic` | Does magic exist in this world at all? |
| `divine` | Are there gods, fate, or an operative moral order? |
| `beings` | Can supernatural beings exist — undead, spirits, demons, magical beasts? |

Ordinary animals need no permission here. A wolf, a bear, a plague are step-2 ecology. Only the
*supernatural* kind needs a yes on `beings` (`docs/universal-law.md:34`).

**Why these three are mandatory.** Everything downstream forks on them. The project's own rubric
names the switches as the single exception to its otherwise-permissive "only settle what the
story actually leans on" rule (`docs/universal-law.md:12`).

>> **HOW THIS IS USED:** the completeness check walks exactly these three names —
`_SWITCHES = ("magic", "divine", "beings")` (`src/engine/bible.py:106`) — and requires each to
be a real true/false. Anything that is not produces a problem coded `switch-unanswered`
(`src/engine/bible.py:299-307`). A world can be built with that check switched off, but when it
is on, an unanswered switch stops the build and names the switch
(`src/engine/bible.py:339-354`).

**IF YOU LEAVE ONE BLANK:** the book still loads. But the world's completeness report will name
the switch you skipped, and any run that asks for a strict build will refuse and say so. More
importantly, you will not have decided — and the first scene that reaches for the supernatural
will decide for you.

**The trap that catches people who answer YES.** If you switch any of the three on, you must
also write at least one law in the `supernatural` domain that says what the thing *cannot* do.
The check is exactly that blunt: if any switch is true and no authored law has
`domain: "supernatural"`, you get a problem coded `unbounded-switch`
(`src/engine/bible.py:312-321`), quoting the rubric's line that "a power with no stated limit is
the director's get-out-of-jail card and makes the probe hollow." Author the ceiling, not just
the ability.

**A worked YES.** Premise: *a world where the dead can be bargained with.* You would set
`beings: true` and `magic: true`, and then owe a supernatural law such as: *the dead cannot be
compelled, only bargained with; the price compounds; they cannot lie about the past and cannot
be trusted about the future.* Now the world can refuse a lever, and the scene where somebody
tries to raise an obedient army has a rule to be refused by (`docs/universal-law.md:58-60` works
the same example through).

**A worked NO.** The reference book answers all three false
(`Beck Hollow/world/BeckHollow.md:26-30`) and then writes a prose note saying so out loud
(`:192-196`): "No magic, no gods, no monsters... The wolves are the whole threat and they are
ordinary." Answering no is not a smaller answer than answering yes. It is a commitment that
everything that happens has to come from cold, hunger, dark, other people, and hungry animals.

```
"switches": {
  "magic":   ____________     (true / false)
  "divine":  ____________     (true / false)
  "beings":  ____________     (true / false)
}
```

If you wrote any `true` above, write here the name of the law you now owe, then go and write it
in section 9:

```
supernatural law bounding it: ______________________________________
```

---

# 4. `blueprint_defaults` — the five rules you inherit for free

**OPTIONAL.** Key path: `blueprint_defaults`

Every world starts out mundane. Before you write a single law of your own, five laws are already
in force. You did not write them and you do not have to.

Here they are, exactly as they exist in the code (`src/engine/bible.py:79-100`):

| what it says | the act it is keyed to | domain |
|---|---|---|
| "People cannot fly." | `fly` | physical |
| "There is no magic." | `cast` | supernatural |
| "The dead do not return." | `resurrect` | persons |
| "The future is not fixed and cannot be foreseen." | `foresee` | fate |
| "The physical world is all there is; there is nowhere else to go." | `planar-travel` | cosmology |

All five are `IMPOSSIBLE` and all five are `known-true`. They are why a world that has not
answered a single law-question can still refuse something — and why, when it refuses, the
refusal names a rule beginning `default-` rather than shrugging (`src/engine/bible.py:229-238`).

**How one drops out.** You do not delete a default. You *overwrite* it, by writing a law of
your own with the same `act`, or the same `id`. The suppression is deliberately dumb: a default
drops out if and only if one of your laws carries the identical `act` string or the identical
`id` — `if d["act"] in taken_acts or d["id"] in taken_ids: continue`
(`src/engine/bible.py:245-249`). It never *infers*. Writing a lot of supernatural laws does not
quietly switch off "there is no magic"; only a law keyed to the act `cast` does that.

**How to turn all five off.** Write `"blueprint_defaults": false`.

>> **HOW THIS IS USED:** the check is literally `if world.get("blueprint_defaults") is False`
(`src/engine/bible.py:243`). Read that as strictly as it is written. **Only the bare JSON word
`false` opts out.** The string `"false"`, the number `0`, an empty list, the word `no` — none of
them are the actual value `false`, so all of them leave the five defaults switched **on**. This
is the one place on this sheet where a near-miss silently does the opposite of what you meant.

**IF YOU LEAVE IT OUT ENTIRELY:** the five defaults apply. That is the intended state for almost
every book. The reference book writes `"blueprint_defaults": true`
(`Beck Hollow/world/BeckHollow.md:31`) — which is exactly the same as leaving it out, and is
worth writing anyway because it makes the choice visible to the next person who reads the file.

**Only turn them off** when you have authored the whole law layer yourself and want no inherited
rules at all. If you turn them off and write nothing, your world refuses nothing.

```
"blueprint_defaults":  ____________     (true / false / omit)
```

---

# 5. `standing_facts` — the things that are simply true

**REQUIRED.** Key path: `standing_facts`

A list of plain sentences. Each one is a fact about this world that no scene may contradict.
Not atmosphere — *facts*, of the sort you could catch a draft breaking.

Worked examples, all from `Beck Hollow/world/BeckHollow.md:32-42`:

> - "Beck Hollow holds about forty people. There is no garrison, no lord in reach, and no help
>   coming before the thaw."
> - "The beck drives the mill. If the race ices over the mill stops, and a stopped mill in
>   winter means no flour."
> - "Sheep are the Hollow's whole wealth. A fold lost is a family ruined, not inconvenienced."
> - "Wolves are animals. They are not spirits, they are not sent, and nothing in this valley is
>   supernatural."
> - "Nobody in the Hollow has killed a wolf. Two men have tried, in living memory, and both were
>   hurt doing it."

Notice the shape. Each one carries a *consequence* — "a fold lost is a family ruined, **not
inconvenienced**." That second clause is what makes a fact catchable.

>> **HOW THIS IS USED:** they are the canon handed to the continuity critic. After a scene runs,
the critic is given your standing facts under the heading "WORLD FACTS (canon — must not be
contradicted)" together with the transcript, and asked to report any line that contradicts one
(`scripts/critic.py:81-82` builds the list; `scripts/critic.py:97-104` places it in the prompt).
It is the only place in the pipeline that reads them.

**Two things this field does NOT do**, and both matter:

- **A standing fact never reaches a character.** During a scene, what a character perceives
  comes from the event text and their own vault, and nothing else — the world's standing facts
  are present in memory but deliberately untouched by perception
  (`src/engine/gate.py:100-103`: "standing_facts is ALSO present but INERT here — read only by
  the out-of-loop critic, never by perception"; the same note at `src/engine/scene.py:64-67`).
- **Rewriting a standing fact will not change how anyone behaves.** If you want a fact to change
  behaviour today, route it: into a **law** if the world should refuse something, a **lexicon
  class** if a character must perceive it, a **belief** on the character who holds it, or the
  **event text** of the scene.

**IF YOU LEAVE IT BLANK:** the book loads and runs. The critic is handed an empty canon and can
only report contradictions a scene makes against itself and against the cast/place lists. In
practice, nothing in your world can be contradicted, because nothing has been written down as
true.

**Common mistake:** writing atmosphere as a standing fact. *"The winter is bleak and the
villagers are frightened"* cannot be contradicted, so the critic can never use it. *"Winter dark
comes by mid-afternoon and holds until nine"* (`:39`) can be — the moment a scene has someone
reading by daylight at six o'clock, that is a catch.

Write six to ten. Fewer than about five and the critic has nothing to hold a draft against.

```
"standing_facts": [

  1. _____________________________________________________________________

  2. _____________________________________________________________________

  3. _____________________________________________________________________

  4. _____________________________________________________________________

  5. _____________________________________________________________________

  6. _____________________________________________________________________

  7. _____________________________________________________________________

  8. _____________________________________________________________________

]
```
---

# 6. `locations` — the places a scene can be set

**REQUIRED.** Key path: `locations`, a list of `{id, what}` pairs.

This is the register of every place a scene can happen. **The `id` is what a scene points at.**
When you (or a director) write a scene, the scene names a location by its id, and the engine
looks it up in this list. If the id is not here, the lookup finds nothing.

## 6.1 `locations[].id`

**REQUIRED.** A short lowercase handle. One word, or words joined by hyphens. No spaces.

Worked examples (`Beck Hollow/world/BeckHollow.md:43-68`): `mill`, `beck`, `fold`, `fell-road`,
`long-hall`, `winter-store`.

>> **HOW THIS IS USED:** a scene's `location` string is matched against these ids — the match
succeeds if either string contains the other, or if the scene's string appears in the `what`
text (`src/engine/gate.py:454-465`). On a match, the location becomes a percept every character
in the scene receives at full clarity, with no check to pass (`src/engine/gate.py:221-230`).

**IF YOU LEAVE A LOCATION OUT:** the scene runs, but nobody is anywhere. No location percept is
produced. Two separate tools will tell you: the scene linter refuses the scene outright —
"location %r is not in world.locations — no scene can produce a location percept for it"
(`scripts/lint_scene.py:118-121`) — and a live run logs a world-fault saying the location has no
world note (`scripts/direct.py:246-249`). If a character's own sheet records them as standing
somewhere unregistered, the book linter names that too (`scripts/lint_book.py:251-254`).

**IF YOU LEAVE THE WHOLE LIST BLANK:** the linter warns "world.locations is EMPTY — no scene can
produce a location percept" (`scripts/lint_book.py:78-79`). Every scene happens nowhere.

## 6.2 `locations[].what`

**REQUIRED.** One or two sentences. This is what a person standing there apprehends.

Worked example (`Beck Hollow/world/BeckHollow.md:57-58`):

> `"fell-road"` — "the track climbing out of the hollow onto open fell. Above the last wall
> there is no cover, no light, and no help. This is where the pack is seen"

Compare a weak one:

| weak | good |
|---|---|
| "A road going up the hill out of the village." | "the track climbing out of the hollow onto open fell. Above the last wall there is no cover, no light, and no help. This is where the pack is seen" |
| Geography. Nothing to act on. | Names what is absent — cover, light, help — which is exactly what a frightened person notices, and gives the place its meaning in one clause. |

Write them as **conditions and affordances**, not as scenery. What is warm, what is freezing,
what can be climbed, what can be heard from here, who can see you.

>> **HOW THIS IS USED:** the `what` text is handed to every character in the scene verbatim, as
the sole attribute of the location percept (`src/engine/gate.py:225-230`). It also goes to the
continuity critic as the "WHERE" line (`scripts/critic.py:84`), and is stored as this place's
description in the book's pinned entity register (`src/engine/bible.py:159-161`).

**IF YOU LEAVE IT BLANK:** the location percept is produced with an empty description — the
character knows they are somewhere, and nothing about it.

```
LOCATION 1
  id:    ____________________
  what:  _____________________________________________________________
         _____________________________________________________________

LOCATION 2
  id:    ____________________
  what:  _____________________________________________________________
         _____________________________________________________________

LOCATION 3
  id:    ____________________
  what:  _____________________________________________________________
         _____________________________________________________________

LOCATION 4
  id:    ____________________
  what:  _____________________________________________________________
         _____________________________________________________________

LOCATION 5
  id:    ____________________
  what:  _____________________________________________________________
         _____________________________________________________________

LOCATION 6
  id:    ____________________
  what:  _____________________________________________________________
         _____________________________________________________________
```

**Register a location the moment you draft a scene there** — before the run, not after the prose
reads flat.

---

# 7. `people` — the walk-on cast

**REQUIRED.** Key path: `people`, a list of entries.

These are the people of the world who are *not* full simulated characters: the hall-keeper, the
shepherd, the drover wintering over. They can be seen, recognised, named, and talked about. They
do not act on their own.

**A full character is not automatically one of these.** If somebody has a sheet in `characters/`
but no entry here, no other character can perceive them — the entity-recognition machinery reads
only this list. The book linter says exactly that: "not in world.people — no other character can
PERCEIVE them. A character is not automatically an entity"
(`scripts/lint_book.py:104-107`). So put your principals in this list too.

## 7.1 The two ways to declare a person — and how they combine

There are **two** routes into `world.people`, and both are live:

**Route A — inline, in the world note's JSON block.** Add entries to the `people` array. This is
the array you are filling in below.

**Route B — one file per person, in `people/`.** A markdown note with `type: person` in its
frontmatter and its own small JSON block.

The loader **starts from the inline array and then appends the files**:

```
people = list(world.get("people", []))          # vault.py:125 — the INLINE array, FIRST
for p in notes_in("people"):                    # vault.py:126 — then the files
    ...
    people.append(entry)                        # vault.py:136
```
(`src/engine/vault.py:125-138`)

So the two routes do not compete — they combine, inline first. Use whichever suits: inline for a
name that needs one line, a file for someone who needs a paragraph of prose you will re-read.
The reference book deliberately uses both, and its `people/Faron.md` note says so out loud
(`Beck Hollow/people/Faron.md:16-17`).

*(Footnote 3 at the end of this sheet: `docs/new-book-manifest.md:128` says `world.people` comes
from `people/*.md` **only**. That is wrong, and the line above is why.)*

**Route B's own rules**, if you use it:

- The frontmatter **must** say `type: person`, or say nothing at all. An explicit `type: concept`
  makes the note invisible — `if (p["type"] or "person") != "person": continue`
  (`src/engine/vault.py:126-128`).
- If you give no `id`, one is made from the filename, lowercased, spaces to underscores
  (`src/engine/vault.py:130`).
- If you give no `what`, the **first prose line** of the note becomes it — the first non-blank
  line that is not a heading, a bullet, or a code fence (`src/engine/vault.py:131-135`).

Here is the reference book's whole person note, which is as short as one can be
(`Beck Hollow/people/Faron.md:1-12`): frontmatter saying `type: person` and `id: faron`, one
paragraph of prose, and a one-line JSON block giving `id`, `name`, and `what`.

## 7.2 `people[].id`

**REQUIRED.** Lowercase handle, no spaces. Underscores are fine.

Worked examples: `tam`, `nell`, `orrin` (`Beck Hollow/world/BeckHollow.md:69-85`), and `faron`
(`Beck Hollow/people/Faron.md:3`).

**The rule that catches everyone: the id's FIRST WORD is the name matched in your event text.**
The engine takes the id, splits it on underscores, and looks for the *first* token in the event
text — `first_name = name_parts[0]`, then `if first_name and _normalize(first_name) in t`
(`src/engine/gate.py:443-446`). So if your scenes say "Edda", the id must begin `edda`. An id of
`the_baker` will be searched for as the word "the", which matches almost every sentence in
English.

>> **HOW THIS IS USED:** three things at once. It is the key that produces an entity percept
when this person is named in a scene (`src/engine/gate.py:430-451`). It is the key a character's
relationship record must point at, or that edge never surfaces
(`scripts/lint_book.py:162-164`; also `scripts/direct.py:258-261`). And it is registered in the
book's pinned entity store, so a citation naming this person resolves as real rather than
fabricated (`src/engine/bible.py:154-158`).

**IF YOU LEAVE IT BLANK:** the entry is skipped when entities are projected
(`src/engine/bible.py:155-156`), and the linter names the index that has no id
(`scripts/lint_book.py:95-97`).

## 7.3 `people[].name`

**REQUIRED.** The full name a person in the room would say aloud.

Worked example: `"name": "Nell Harrow"` (`Beck Hollow/world/BeckHollow.md:77`).

>> **HOW THIS IS USED:** three live consumers, none of them cosmetic.
>
> 1. It is the display name for every entity in the run — built once from this list, falling
>    back to a title-cased id when absent (`scripts/scene.py:77-92`).
> 2. That display name is written into **other characters' memories**. When a character does
>    something durable in front of a witness, the witness's new belief is worded with this name
>    (`scripts/scene.py:518` hands `names.get(speaker, speaker)` to
>    `acquisition.witness_belief`, `src/engine/acquisition.py:109-114`). Leave it blank and a
>    witness remembers a database handle where a person would have remembered a name.
> 3. It is how a name gets *learned* mid-scene. If a character knows somebody only by a
>    descriptor — "the man with the dogs" — and then hears the real name spoken aloud, they
>    learn it, and the canonical name comes from this field, never guessed
>    (`src/engine/acquisition.py:158-179`, especially `name_by_id` at `:168-169`, driven from
>    `scripts/scene.py:534-536`).
>
> It also goes to the continuity critic's "WHO" line (`scripts/critic.py:43-46` and `:83`).

**IF YOU LEAVE IT BLANK:** the id is title-cased and used instead (`scripts/scene.py:91`), so
`nell` becomes "Nell" — survivable for a one-word id, and wrong for `old_orrin`.

*(Footnote 4: an earlier audit of this engine recorded `people[].name` as reaching only the
optional critic. That is wrong — the three consumers above are all live.)*

## 7.4 `people[].what`

**REQUIRED.** One sentence. **Write it as what a knower knows, not as a neutral description.**

This is the identity record, and it is *withheld behind a check*. A character who does not
recognise this person perceives only the words "person present" and nothing else — no role, no
label (`src/engine/gate.py:210-219`). Only a character who either already has a standing
relationship with them, or is perceptive enough, gets this sentence
(`src/engine/gate.py:200-209`; the threshold constant is `PERCEPTION_DC_IDENTITY = 0.55`,
`src/engine/gate.py:41`, meaning roughly "better than an average reader of people").

Worked examples (`Beck Hollow/world/BeckHollow.md:71-84`):

> - `tam` — "the miller's son, thirty-one, who keeps the race clear and does not go up the fell road"
> - `nell` — "shepherd, forty, blunt and warm, who has lost four ewes to the pack and walks the fold at night alone"
> - `orrin` — "the hall-keeper, sixty, who counts the winter store and says out loud what everyone is thinking"

Each carries a role, an age, and **the thing about them a neighbour would actually mention** —
"does not go up the fell road", "walks the fold at night alone". That last clause is what makes
them a person rather than a job title.

| weak | good |
|---|---|
| "The village shepherd." | "shepherd, forty, blunt and warm, who has lost four ewes to the pack and walks the fold at night alone" |
| True of anyone with that job. | Says what she has lost and what she does about it — which is what someone who knows her would tell you. |

>> **HOW THIS IS USED:** it is the sole attribute of the entity percept when recognition
succeeds (`src/engine/gate.py:203-209`). It is also the description stored in the book's pinned
entity register (`src/engine/bible.py:157`) and the "WHO" line the critic gets
(`scripts/critic.py:83`).

**IF YOU LEAVE IT BLANK:** recognition still fires, but hands over the person's first name and
nothing else (`src/engine/gate.py:447-449` falls back to the first name when `what` is empty).

## 7.5 `people[].groups` — OPTIONAL, and more useful than it looks

Key path: `people[].groups`, a list of short strings.

The classes this person belongs to: `"outsider"`, `"guild"`, `"drovers"`, `"fell folk"`. You
choose the vocabulary; the engine has no fixed list.

>> **HOW THIS IS USED:** it builds the index that gives an event's *subject* a class
(`src/engine/scene.py:393-407`). That class is the key a character's own regard map is looked up
by — the mechanism by which a character can feel less for someone because of what they *are*,
while still being liftable above it by an individual bond (`src/engine/state.py:243-250`). Group
membership is authored here on purpose; it is never guessed by a model.

**IF YOU LEAVE IT BLANK:** the person belongs to no class, and any regard rule written against a
class simply never fires for them. That is the right default for most people in most books.

Fill this in only when your book has a bigotry, a caste, or an in-group/out-group line a
character actually feels.

```
PERSON 1
  id:      ____________________   (first word = the name your event text will use)
  name:    ____________________
  what:    ___________________________________________________________
  groups:  ____________________   (optional)

PERSON 2
  id:      ____________________
  name:    ____________________
  what:    ___________________________________________________________
  groups:  ____________________

PERSON 3
  id:      ____________________
  name:    ____________________
  what:    ___________________________________________________________
  groups:  ____________________

PERSON 4
  id:      ____________________
  name:    ____________________
  what:    ___________________________________________________________
  groups:  ____________________

PERSON 5
  id:      ____________________
  name:    ____________________
  what:    ___________________________________________________________
  groups:  ____________________
```

**IF YOU LEAVE THE WHOLE LIST BLANK:** the linter is blunt — "world.people is EMPTY — entity
recognition has nothing to recognize, and every relationship edge below is disabled with it"
(`scripts/lint_book.py:74-77`). Nobody can see anybody.

---

# 8. The `lexicon` — the words the engine watches for

**REQUIRED.** Key path: `lexicon`

This is the part of the sheet that surprises people, so read this paragraph before you fill in
anything.

**The engine does not understand your scenes. It scans them for words you gave it.** When a
scene happens, the engine takes the event's text and looks through it for the words listed here.
Each word it finds hands the character a tag. Those tags are what the character's memory is
searched by. A wound that fires on "wolves" fires because the word *wolves* was in the text and
because *wolves* was in your lexicon — nothing else.

So this is not a glossary and not a taxonomy. **It is the register your events are written in.**

> If you skipped the tip in section 1, go back and do it now: write out the text of one scene's
> event, two or three sentences, in the voice you will actually write in. Then harvest the nouns
> out of it. That is your lexicon, and it will be right the first time.

## 8.1 `lexicon.attribute_classes`

**REQUIRED.** Key path: `lexicon.attribute_classes`

A short list of named buckets. Each bucket has a name — the thing your events are *about* — and
a list of words that, when they appear in a scene, mean that thing is present.

Worked example, the reference book's five buckets
(`Beck Hollow/world/BeckHollow.md:87-141`):

| bucket | the words in it |
|---|---|
| `threat` | wolf, wolves, pack, tracks, howl, blood, carcass, teeth, growl |
| `cold` | frost, ice, snow, sleet, wind, frozen, numb, thaw |
| `work` | race, wheel, flour, grain, hurdle, fold, ewe, lamb, fleece, pail |
| `light` | lamp, lantern, oil, hearth, dark, dusk, torch, coal |
| `harm` | wound, bite, bone, blade, axe, spear, bandage, limp |

Five buckets of eight to ten words each. That is a good size for a book.

>> **HOW THIS IS USED:** for every bucket, if any of its words appears anywhere in the event
text, the bucket's *name* is handed to the character as something they perceive
(`src/engine/gate.py:403-417`). Those names then become the search terms their memory is queried
with (`src/engine/gate.py:237-258`). Matching is case- and accent-insensitive and works on
substrings (`src/engine/gate.py:70-85`) — so `wolf` also catches "wolves" and "wolfish".

**Do the words in a bucket have to be single tokens? No.** The check is a plain substring test
against the whole normalised event text — `_normalize(kw) in t` (`src/engine/gate.py:410`) — not a
word-by-word comparison. A phrase works exactly the way one word does; it is the identical
mechanism `subtle_cues` phrases use two sections down (`src/engine/gate.py:425`). Nothing stops
you writing `"wolf pack"` instead of just `"pack"`, if that is the phrase your prose will actually
contain — the list just has to contain a string the event text will contain.

**Put your characters' first names in here too.** The guide is explicit that keywords must be
"the words your event text will actually use — **including character first names**"
(`docs/guide-content.md:70`).

**IF YOU LEAVE THE WHOLE LEXICON BLANK:** it is legal, and it is thin. Perception falls back to
a generic floor: the character perceives the event's *kind* and its first six words, and nothing
else (`src/engine/gate.py:412-416`). The linter warns you — "world: no lexicon — perception
falls back to generic extraction (kind + leading words), thin"
(`scripts/lint_book.py:68-69`).

**IF YOU AUTHOR CLASSES WHOSE WORDS NEVER APPEAR:** they extract nothing, silently. A live run
notices and logs a world-fault — "the lexicon has no vocabulary for this event" — naming the
first eighty characters of the offending text (`scripts/direct.py:251-254`). If you see that
fault, the fix is to harvest words out of the scene, not to add another bucket.

**Common mistake:** authoring the taxonomy you would put in a series bible — `politics`,
`religion`, `commerce`. Those are the subjects of your *book*. The buckets want to be the
subjects of your *sentences*.

```
"attribute_classes": {

  bucket name: ______________
    words:  ____________  ____________  ____________  ____________  ____________
            ____________  ____________  ____________  ____________  ____________

  bucket name: ______________
    words:  ____________  ____________  ____________  ____________  ____________
            ____________  ____________  ____________  ____________  ____________

  bucket name: ______________
    words:  ____________  ____________  ____________  ____________  ____________
            ____________  ____________  ____________  ____________  ____________

  bucket name: ______________
    words:  ____________  ____________  ____________  ____________  ____________
            ____________  ____________  ____________  ____________  ____________

  bucket name: ______________
    words:  ____________  ____________  ____________  ____________  ____________
            ____________  ____________  ____________  ____________  ____________
}
```

## 8.2 `lexicon.subtle_cues` — OPTIONAL

Key path: `lexicon.subtle_cues`

The same shape as above — named buckets of phrases — but for **what only the observant notice.**
These are progressions, tells, and concealments: the things that are in the room and that a less
perceptive character walks straight past.

Worked example (`Beck Hollow/world/BeckHollow.md:142-153`):

| cue | the phrases in it |
|---|---|
| `watched` | "the dogs went quiet", "the sheep bunched", "something moved at the wall" |
| `unspoken` | "nobody looked at him", "the hall went quiet when he came in", "she did not ask again" |

Notice these are **whole phrases**, not single words. They are the sentence you would write in
the event text anyway; the cue name is what a sharp character takes away from it.

>> **HOW THIS IS USED:** if the event carries gated detail at all (see 8.3 below), and the
character is perceptive enough, then every cue whose phrase appears in the text is handed to
them as a second, fainter percept (`src/engine/gate.py:419-427`, produced at
`src/engine/gate.py:147-159`). The threshold is `PERCEPTION_DC_SUBTLE = 0.60`
(`src/engine/gate.py:42`) — a character better than averagely observant. A character below it
receives nothing from this bucket at all, and does not know they missed anything.

**IF YOU LEAVE IT BLANK:** no subtle percepts are ever produced. Every character perceives the
same overt layer. Nothing breaks; the scenes get flatter, because two characters in one room
always apprehend the same thing.

**Common mistake:** putting something everyone must know behind a subtle cue. Half your cast
will be blind to it and the scene will stall. Subtle cues are for what the *sharp* one catches.

```
"subtle_cues": {

  cue name: ______________
    phrases:  _______________________________________________________
              _______________________________________________________
              _______________________________________________________

  cue name: ______________
    phrases:  _______________________________________________________
              _______________________________________________________
              _______________________________________________________
}
```

## 8.3 `lexicon.subtle_cue_classes` — OPTIONAL, and there is a trap here

Key path: `lexicon.subtle_cue_classes`, a list of names.

This list answers one question: **which kinds of event carry hidden detail worth a perceptive
character's attention?**

**THE RULE, and it is the single most-missed rule on this sheet: the names in this list must be
names of your `attribute_classes` buckets — from section 8.1. Not the names of your
`subtle_cues` buckets.**

Look at what the code does. It walks your `subtle_cue_classes` names and, for each one, looks
that name up **in `attribute_classes`**:

```
classes, _cues, cue_classes = _lexicon(world)
for cls in cue_classes:
    if any(_normalize(kw) in t for kw in classes.get(cls, [])):
        return True
return kind in ("threat", "loss")
```
(`src/engine/gate.py:396-400`; `classes` is `attribute_classes`, bound at
`src/engine/gate.py:387-389`.)

So a name that is not an `attribute_classes` key looks up an empty list, matches nothing, and
the loop falls through.

**The shipped reference book gets this wrong.** `Beck Hollow/world/BeckHollow.md:154-157` lists
`"watched"` and `"unspoken"` — which are the names of its **`subtle_cues`** buckets
(`:142-152`), not of its `attribute_classes` buckets (`:87-141`). So
`classes.get("watched", [])` is empty, `classes.get("unspoken", [])` is empty, and the loop at
`src/engine/gate.py:397-398` finds nothing. Do not copy those two lines.

**What Beck Hollow should have written** is the names of the danger-bearing buckets it actually
has:

```
"subtle_cue_classes": ["threat", "harm"]
```

Now an event mentioning a wolf or a wound is marked as carrying gated detail, and a perceptive
character gets a shot at the `watched` and `unspoken` cues inside it.

>> **HOW THIS IS USED:** it is the gate on whether subtle cues are looked for at all in a given
event (`src/engine/gate.py:392-400`, called at `src/engine/gate.py:150`).

**IF YOU LEAVE IT BLANK:** you do **not** lose subtle cues entirely. The check has a fallback:
any event whose kind is `threat` or `loss` counts as cue-bearing regardless
(`src/engine/gate.py:400`). So an empty list means "only threats and losses hide anything" —
which is a defensible answer, and a much better one than a list of names that match nothing.

**Choose the danger-bearing buckets.** Not all of them — the ones where something might be
being concealed.

```
"subtle_cue_classes": [ ______________ , ______________ ]

   ^ these MUST be names you wrote in 8.1, not names you wrote in 8.2. Go back and check.
```
---

# 9. `laws` — what the world refuses, forbids, and demands

**REQUIRED.** Key path: `laws`, a list of law objects.

A law is a rule the world itself holds. Not a rule your characters believe in — a rule the
engine can consult and answer with. Anything your world *refuses*, *mandates*, or *punishes*
belongs here. A rule that exists only as prose in a document cannot refuse anything, and no
scene can be caught breaking it.

**How a law reaches a scene.** A scene may declare an `act` — one word for what is being
attempted. The engine collects every law bearing on that act and returns a verdict: allowed or
not, with the rules that decided it and any consequences attached
(`src/engine/bible.py:441-490`, called from the scene pre-flight at
`scripts/scene.py:281-299`). If the verdict is a refusal, the scene does not run and the
refusal quotes the rule.

Start with three to six laws. The reference book has three
(`Beck Hollow/world/BeckHollow.md:159-188`).

## 9.1 `laws[].id`

**REQUIRED.** A short hyphenated handle, unique within your book. It is how a refusal names
itself, so make it readable in a sentence.

Worked examples (`Beck Hollow/world/BeckHollow.md:167, 176, 186`): `no-help-before-thaw`,
`a-wolf-is-an-animal`, `the-mill-must-run`.

>> **HOW THIS IS USED:** it is the citation. A refusal reports `denied_by: ["no-help-before-thaw"]`
(`src/engine/bible.py:482`) and the scene pre-flight prints it
(`scripts/scene.py:290-293`). It is also what a `law:` citation elsewhere in the system
resolves against (`src/engine/bible.py:380-388`).

**IF YOU LEAVE IT BLANK:** the book refuses to load and says so directly — "has no id — a law
must be citable" (`src/engine/bible.py:175-176`). Two laws with the same id also refuse, naming
the duplicate (`src/engine/bible.py:223-224`).

## 9.2 `laws[].statement`

**REQUIRED.** One or two sentences, in your own voice, saying what the rule is.

Worked example (`Beck Hollow/world/BeckHollow.md:183`):

> "The race must be kept clear through a frost. A stopped mill in deep winter is the village
> going hungry."

>> **HOW THIS IS USED:** it is quoted verbatim when the law fires. The verdict's `reason` field
is built by joining the statements of the laws that denied or were violated
(`src/engine/bible.py:486-488`), and that text is printed in the refusal
(`scripts/scene.py:290-293`).

**IF YOU LEAVE IT BLANK:** the book refuses to load, by name — "has no statement — a denial
must be able to quote the rule" (`src/engine/bible.py:178-179`).

**Write it as the rule, plus what it means.** The second sentence in the example above — "a
stopped mill in deep winter is the village going hungry" — is what makes the refusal land as a
fact about this world rather than a rules lawyer's note.

## 9.3 `laws[].domain`

**REQUIRED.** One of exactly eight words. Any other value refuses the book and lists all eight
back at you (`src/engine/bible.py:180-182`).

The eight, from the code (`src/engine/bible.py:44-49`):

| domain | what belongs in it |
|---|---|
| `physical` | how matter, gravity, time and distance work |
| `supernatural` | magic, gods, spirits, anything more-than-physical |
| `persons` | mind, soul, and death — whether death is final |
| `fate` | whether the future is fixed, whether prophecy operates |
| `cosmology` | the shape of reality — other planes, other worlds, whether there is anywhere else |
| `legal` | what an authority forbids or requires |
| `custom` | what a community forbids or requires without an authority |
| `economic` | what the market, the debt, or the scarcity forbids or requires |

The first five are the deep ground truth; the last three are how people organise themselves on
top of it.

>> **HOW THIS IS USED:** it is validated against that exact list
(`src/engine/bible.py:180-182`), and it is what the switch check counts — if you switched a
supernatural switch on, this check looks for at least one law whose domain is `supernatural`
(`src/engine/bible.py:312-321`).

**IF YOU LEAVE IT BLANK:** the book refuses to load and names the law.

## 9.4 `laws[].modality` — the field that decides everything

**REQUIRED.** One of exactly four words, in capitals. Anything else refuses the book and lists
all four (`src/engine/bible.py:184-185`). The four are
`("IMPOSSIBLE", "FORBIDS", "REQUIRES", "PERMITS")` (`src/engine/bible.py:50`).

Here is what each one actually does to a scene, in plain words.

### `IMPOSSIBLE` — it cannot happen

The scene is **refused**. It does not run. The pre-flight raises and prints which law stopped
it and what that law says (`scripts/scene.py:290-293`).

This is the *only* modality that denies. That is deliberate and it is stated in the code:
`_DENYING = ("IMPOSSIBLE",)` (`src/engine/bible.py:65`), with the reason written beside it —
"a gate that denied every ILLEGAL act would make crime unwritable... A character breaking a law
is not a gate failure, it is the story" (`src/engine/bible.py:61-64`).

Use it for things that are not *possible*: people cannot fly, the dead do not return, no rider
can reach the valley before the thaw.

### `FORBIDS` — it may not, but it can

The scene **runs**. The act is against the rules and it happens anyway, and then it costs
something. The verdict returns it as a violation with its `teeth` attached
(`src/engine/bible.py:477, 485`), the pre-flight prints "is FORBIDDEN but possible - it runs,
and it costs" together with the consequence (`scripts/scene.py:294-297`), and after the beat a
law-violation event is recorded in the run's log (`scripts/scene.py:252-255`).

Use it for curfews, oaths, taboos, crimes. Your thief *can* break the curfew — that is the
story; the teeth are what make it cost.

### `REQUIRES` — an obligation

The scene **runs**, and the *omission* is recorded as a violation, with teeth, exactly like a
`FORBIDS` (they are handled by the same branch — `r["modality"] in ("FORBIDS", "REQUIRES")`,
`src/engine/bible.py:476-477`).

Use it for duties. The reference book's third law is one: the mill race must be kept clear
through a frost (`Beck Hollow/world/BeckHollow.md:178-187`), which hands a character a duty he
already discharges without counting it as courage.

### `PERMITS` — an explicit allowance

The scene **runs**, and this rule *disarms other rules*. A permit with no `excepts` list is a
general allowance: while it bears on the act, nothing else denies and nothing else counts as
violated (`src/engine/bible.py:469, 472-477`).

Use it sparingly, and prefer the narrow form — see `excepts` at 9.9.

**The mistake to avoid:** reaching for `IMPOSSIBLE` when you mean "characters shouldn't."
`IMPOSSIBLE` stops the scene from existing. If you want the scene to happen and to cost
something, you want `FORBIDS`.

```
modality:  ____________________   (IMPOSSIBLE / FORBIDS / REQUIRES / PERMITS)
```

## 9.5 `laws[].epistemic` — is this actually true, or only believed?

**REQUIRED in four domains, and worth writing everywhere.** One of exactly three values
(`src/engine/bible.py:57`):

| value | what it means | what the engine does |
|---|---|---|
| `known-true` | this is really how the world works | the law binds — it can deny and it can be violated (`src/engine/bible.py:466`) |
| `known-false` | people believe it; it is not so | the law **never** constrains anything — excluded by the same line above; a world where people believe the dead walk is not a world where they do |
| `contested-unknowable` | the world deliberately never decides | the verdict comes back **undecidable** rather than allowed. The gate refuses to invent the ground truth in either direction (computed at `src/engine/bible.py:467-468, 480`); the pre-flight prints "the world declines to rule" (`scripts/scene.py:298-299`) |

Two shorthands are accepted and quietly translated: `true` becomes `known-true` and `believed`
becomes `known-false` — `_EPISTEMIC_ALIASES = {"true": "known-true", "believed": "known-false"}`
(`src/engine/bible.py:58`). Anything else refuses the book and lists the three
(`src/engine/bible.py:188-189`).

>> **HOW THIS IS USED:** only `known-true` laws bind. Everything else is filtered out before the
verdict is computed (`src/engine/bible.py:466`).

**IF YOU LEAVE IT BLANK:** it silently becomes `known-true` (`src/engine/bible.py:186`). For a
law about physics or the market that is fine. For a law about the supernatural, about souls and
death, about fate, or about the shape of reality, it means you have fixed a truth you never
chose — so the completeness check names it, coded `epistemic-unstated`, in exactly those four
domains (`_EPISTEMIC_REQUIRED_IN = ("supernatural", "persons", "fate", "cosmology")`,
`src/engine/bible.py:113`; the problem is raised at `:328-335`).

**`contested-unknowable` is the interesting one.** It is how you write a world that refuses to
say whether the gods are real. Both the devout and the sceptic are simulated identically; only
the ground truth differs, and you have declined to fix it
(`docs/universal-law.md:19` argues the case).

**A worked pair.** Same premise — *the dead can be bargained with* — two books:

| `epistemic` | what the book becomes |
|---|---|
| `known-true` | a horror of the real. The dead actually answer. |
| `known-false` | a tragedy of delusion. The bargainers are charlatans or self-deceived, and the engine will never let their "power" constrain anything. |

That single word is the whole difference (`docs/universal-law.md:60`).

## 9.6 `laws[].act` — the one word a scene points at

**REQUIRED.** A short hyphenated verb phrase naming the thing a character might attempt. Nothing
in the loader raises if you leave it blank — the field is not schema-required — but the measured
consequence below is severe enough that this sheet no longer hedges it as merely "required in
practice." Treat it as required, full stop.

Worked examples (`Beck Hollow/world/BeckHollow.md:164, 173, 182`):
`summon-outside-help`, `treat-the-pack-as-sent`, `let-the-race-ice-over`.

>> **HOW THIS IS USED:** it is the key that decides whether a law bears on a moment at all. A
law bears when its act matches the act the scene declared, or when the law names no act —
`if row["act"] and act is not None and row["act"] != act: return False`
(`src/engine/bible.py:408`). The match is exact, never fuzzy; the code says why — "a near-match
would deny the wrong thing" (`src/engine/bible.py:392-393`).

**IF YOU LEAVE IT BLANK:** the law bears on **everything**. Every scene that declares any act
gets this law in its bearing set. On a live book measured by the engine's own authors, an
unscoped check made all 27 laws bear and 24 of them deny, so every scene would have been
refused (`scripts/scene.py:278-280`). Give every law an act.

**Your acts and your scenes must use the same strings.** The book linter reminds you that a law
keyed by an act only fires if some scene declares that act, and prints your act vocabulary back
at you (`scripts/lint_book.py:83-91`). The scene linter checks the other direction and errors on
a scene whose act is keyed by no law (`scripts/lint_scene.py:137-140`).

**Common mistake:** writing acts as nouns (`help`, `wolves`) or as whole sentences. Write them
as the attempt: `summon-outside-help`, `climb-the-fell-road`, `take-from-the-store`.

## 9.7 `laws[].teeth` — OPTIONAL, and the point of a FORBIDS

Key path: `laws[].teeth`

One clause naming what it costs. Not a number — a consequence in the world.

Worked example (`Beck Hollow/world/BeckHollow.md:184`):

> "the Hollow goes short, and everyone knows whose work it was"

>> **HOW THIS IS USED:** the teeth of every violated law are collected into the verdict
(`src/engine/bible.py:485`), printed beside the law when the scene pre-flight allows a forbidden
act (`scripts/scene.py:294-297`), and recorded in the run's log as part of the law-violation
event (`scripts/scene.py:252-255`).

**They are recorded, not applied.** The engine will not deduct a rank or inflict a wound on your
behalf; turning a consequence into a real change is the director's judgement
(`scripts/scene.py:214-216`).

**IF YOU LEAVE IT BLANK:** the violation is still recorded, but the reason line reads "no stated
consequence" (`src/engine/bible.py:487`). A `FORBIDS` with no teeth is a rule that costs
nothing, which is the same as no rule.

**A good teeth clause vs a weak one.**

| weak | good |
|---|---|
| "There are consequences." | "the Hollow goes short, and everyone knows whose work it was" |
| Nothing to dramatise. | Two consequences — material and social — and the second is the one that will actually drive a scene. |

## 9.8 The scope fields — narrowing who a law binds, and when

All four are **OPTIONAL**. Leave them out and the law binds on everyone, everywhere, always.
**All four are LIVE — this section used to be the one place this sheet could not give you a
straight answer, and it now can. If you read an earlier copy that hedged this, that hedge is
gone; every scope below narrows a law the moment you write it, subject to the one caller-support
caveat in the grey box further down.**

| key path | what it narrows | worked example |
|---|---|---|
| `laws[].actor_class` | who may attempt the act | `"guild"` — only the guild may |
| `laws[].target_class` | who or what it may be done to | `"outsider"` |
| `laws[].location_scope` | where the law is in force | `"quay"` — the curfew holds on the quay and nowhere else |
| `laws[].time_from` / `laws[].time_to` | when it is in force | turn 40 to turn 52 — a window measured in your book's own turn numbers, not a clock (see below) |

The class names are yours to choose, but the two class fields are matched against two DIFFERENT
places, and this is the trap: `target_class` matches the `groups` you wrote on your people in
7.5 (same vocabulary, same mechanism). `actor_class` does **not** — the one place this engine
currently reads it is the ACTING character's own sheet, `fixed.position.class`
(`scripts/scene.py:227`), a field on the character blueprint, not this one. If you want one word
to mean the same thing in both places, write it in both places — `people[].groups` here, and
`fixed.position.class` on the character sheet — because nothing keeps them in sync for you.

>> **HOW THIS IS USED — all six scopes are wired.** Each scope is parsed and carried onto the
law's row (`src/engine/bible.py:204-208`) and stored with it (`src/engine/bible.py:369-375`). The
narrowing lives in one function, `bible._applies`, and as of 2026-08-30 it checks all six —
`act`, `location_scope`, `actor_class`, `target_class`, `time_from`/`time_to` — where it used to
read only the first two. A scope left blank on the law bears on all; a scope you set must match,
exactly, never fuzzily — `location_scope` for instance is a plain string equality against the
location the scene declared, never a substring or a fuzzy guess
(`src/engine/bible.py:391-421`, the six checks themselves at `:408-420`).

**The one thing "live" does not mean: that every scope narrows every decision.** `_applies`
treats a scope argument the CALLER never supplies as "cannot tell, so don't narrow" — never as a
mismatch (`src/engine/bible.py:402-406` states why: a law the gate misses is a false PASS, and a
caller ignorant of the actor's class must not get a quieter world than the one you wrote). This
engine has exactly two callers, and they do not supply the same facets:

| caller | what it can do | scopes it supplies |
|---|---|---|
| the scene **pre-flight**, before the beat runs — the only place that can DENY a scene on an `IMPOSSIBLE` law (`scripts/scene.py:281-297`) | refuse the scene outright | `act`, `location` only |
| the per-beat **law recorder**, after the beat — records a `FORBIDS`/`REQUIRES` violation for the critic and the arc; it never denies (`scripts/scene.py:202-231`, `_law_events`) | log a violation | `act`, `location`, `actor_class` (read off the speaker's `fixed.position.class`), `tick` (the turn number) |

So today: `location_scope` is the one scope that reliably narrows a law everywhere, including at
the refusal gate. `actor_class` and the time window narrow what gets *recorded* as a violation
after a beat, but not whether an `IMPOSSIBLE` law denies the scene in the first place — an
`actor_class`-scoped `IMPOSSIBLE` law still refuses every actor, not just the class you named,
because the pre-flight never tells `_applies` who is acting. `target_class` is parsed, validated
and stored, but no caller anywhere in this engine supplies it (verified by searching every call
site) — write it if your book wants the fact on record, but nothing narrows on it yet.

**IF YOU LEAVE THEM ALL BLANK — and this is the important sentence in this section — the law
binds on everyone, everywhere, for the whole book.** That is very often not what an author
means. "Nobody may carry a blade in the hall" is usually "nobody except the hall-keeper", and
"the gate is shut" is usually "the gate is shut after dusk."

**Worked: "only the guild may."**

```json
{ "id": "only-the-guild-may-mill", "domain": "legal", "modality": "FORBIDS",
  "epistemic": "known-true", "act": "grind-grain",
  "actor_class": "guild",
  "statement": "Grinding grain for sale is the guild's alone.",
  "teeth": "the guild takes the flour and the quern both" }
```

Written as `FORBIDS`, on purpose: the act runs and is recorded, and `actor_class` narrows that
recording today (via the per-beat law recorder, above) — this is the modality where the scope
you just wrote actually does something. Written as `IMPOSSIBLE` instead, a non-guild miller's
scene would still be refused at the pre-flight, because the refusal gate does not supply
`actor_class` (see the grey box above).

**Worked: "not after dusk."**

```json
{ "id": "the-gate-shuts-at-dusk", "domain": "custom", "modality": "FORBIDS",
  "epistemic": "known-true", "act": "leave-the-village",
  "time_from": 40, "time_to": 52,
  "statement": "Nobody goes past the wall between dusk and first light.",
  "teeth": "you find the gate barred on your return and the village knows you were out" }
```

**Write `time_from`/`time_to` as bare integers, never as words.** They are compared against
`tick`, and the one caller that ever supplies `tick` hands it the beat's own turn number
(`scripts/scene.py:488`: `tick=turn_no`) — not a time of day. The column is declared `INTEGER` in
the schema (`src/engine/schema.sql:219-220`). An earlier draft of this worked example wrote
`"dusk"`/`"dawn"` as the values, matching how the field reads in prose; that is now a documented
mistake, not a style choice — comparing an integer tick against a string time crashes with a raw
Python `TypeError` the moment a beat inside the window is recorded, and that error is not a
`BibleError`, so nothing in the pipeline catches it (`src/engine/bible.py:416-420` does the
comparison; `scripts/scene.py:232` only catches `bible.BibleError`). Pick the turn numbers this
window should span the way you would pick any other number for this sheet: ask what beat the gate
closes on and what beat it opens again, and write those.

## 9.9 `laws[].excepts` — OPTIONAL, and only on a PERMITS

Key path: `laws[].excepts`, a list of law ids.

A `PERMITS` with no `excepts` disarms **everything** bearing on that act. That is usually too
much. `excepts` narrows it: this permit disarms only the laws you name.

>> **HOW THIS IS USED:** a permit with an `excepts` list disarms only the ids in it; one without
disarms every law bearing on the act (`src/engine/bible.py:469-477`). Every id you name is
checked against the final rule set — including the five inherited defaults, so a permit may
legitimately except `default-no-flight` — and an unknown id refuses the book by name
(`src/engine/bible.py:264-271`).

**Must an excepted id share this permit's own `act`? No — nothing checks that, and nothing works
unless it effectively does anyway.** The only validation `excepts` gets is that every id names a
real law somewhere in the final rule set — checked against ALL of them, not just the ones sharing
this permit's `act` (`src/engine/bible.py:264-271`, the same lines as above). But the disarm
itself only ever happens inside `verdict_for`, against `bearing` — a set already narrowed to laws
matching the CURRENT act (and location, and so on) before `excepts` is even consulted
(`src/engine/bible.py:464`, disarm logic at `:469-477`). So excepting a law with a different,
specific `act` parses cleanly, refuses nothing when the book loads, and then does **nothing** at
runtime — that law can never appear in the set this permit is evaluated against. Except only a
law that shares this permit's own `act`, or one that carries no `act` at all (an unscoped law
bears on every act, this one included, so excepting it always has an effect).

**IF YOU PUT IT ON ANYTHING BUT A PERMITS:** the book refuses to load — "excepts is only
meaningful on a PERMITS row" (`src/engine/bible.py:194-195`). An empty list, or a list with a
blank entry, also refuses (`src/engine/bible.py:198-201`).

## 9.10 `laws[].source_note` — write it for yourself

Key path: `laws[].source_note`

One line saying *why this law exists in this book*. It is a note from you to the next person who
reads the file, which is usually you in three weeks.

Worked examples (`Beck Hollow/world/BeckHollow.md:166, 175, 185`):

> - "the world's isolation is the premise; removing it removes the pressure"
> - "switches.magic is false; this law makes the mundane frame refusable rather than assumed"
> - "gives Tam a duty he already discharges — competence he does not count as courage"

>> **HOW THIS IS USED:** it is carried onto the law's row (`src/engine/bible.py:210`) and stored
with the pinned bible (`src/engine/bible.py:369-375`) — but nothing reads it back out. It is
recorded, not consumed. The one place the engine writes into it itself is on the five inherited
defaults, where it stamps which meta-rule the default came from
(`src/engine/bible.py:253-254`).

**IF YOU LEAVE IT BLANK:** nothing happens. Write it anyway. A law with no stated reason is the
first one you will delete by mistake.

## 9.11 The law worksheet

```
LAW 1
  id:              ____________________________________
  domain:          ____________________  (physical / supernatural / persons / fate /
                                          cosmology / legal / custom / economic)
  modality:        ____________________  (IMPOSSIBLE / FORBIDS / REQUIRES / PERMITS)
  epistemic:       ____________________  (known-true / known-false / contested-unknowable)
  act:             ____________________
  statement:       __________________________________________________________
                   __________________________________________________________
  teeth:           __________________________________________________________
  actor_class:     ______________  target_class: ______________   (both optional)
  location_scope:  ______________  time_from: _______ time_to: _______  (optional)
  source_note:     __________________________________________________________

LAW 2
  id:              ____________________________________
  domain:          ____________________
  modality:        ____________________
  epistemic:       ____________________
  act:             ____________________
  statement:       __________________________________________________________
                   __________________________________________________________
  teeth:           __________________________________________________________
  actor_class:     ______________  target_class: ______________
  location_scope:  ______________  time_from: _______ time_to: _______
  source_note:     __________________________________________________________

LAW 3
  id:              ____________________________________
  domain:          ____________________
  modality:        ____________________
  epistemic:       ____________________
  act:             ____________________
  statement:       __________________________________________________________
                   __________________________________________________________
  teeth:           __________________________________________________________
  actor_class:     ______________  target_class: ______________
  location_scope:  ______________  time_from: _______ time_to: _______
  source_note:     __________________________________________________________

LAW 4
  id:              ____________________________________
  domain:          ____________________
  modality:        ____________________
  epistemic:       ____________________
  act:             ____________________
  statement:       __________________________________________________________
                   __________________________________________________________
  teeth:           __________________________________________________________
  actor_class:     ______________  target_class: ______________
  location_scope:  ______________  time_from: _______ time_to: _______
  source_note:     __________________________________________________________
```

**IF YOU WRITE NO LAWS AT ALL:** the book loads and runs. The five inherited defaults still
apply, so the world can still refuse someone who tries to fly or raise the dead — but nothing
about *your* world refuses anything. The linter says so: "world.laws is EMPTY — the world
refuses nothing" (`scripts/lint_book.py:80-82`).

---

# 10. Check your work

**Before either tool will tell you anything about this world: the book needs one character.**
Both linters start by loading the whole book, and the loader hard-refuses a book with zero notes
in `characters/` — coded `VAULT_NO_CHARACTERS`, raised the moment either linter starts, before a
single line of your world note is looked at: `if not chars: raise VaultError("VAULT_NO_CHARACTERS",
"%s: no character notes found" % book_dir)` (`src/engine/vault.py:161-162`). `lint_book.py` catches
this and prints it as a single error (`scripts/lint_book.py:288-295`); `lint_scene.py` does not
catch it at all, and exits with a bare "could not load book: ..." (`scripts/lint_scene.py:172-177`).
Either way, with `characters/` empty, you get back nothing about your world — not even a warning.

**You do not need a finished character to get past this, and you do not need to open the
character blueprint to write one.** The loader's own requirement is presence-only: a note in
`characters/` whose engine block carries all three of `fixed`, `baseline` and `current` as
top-level keys, with any content, even none — `for key in ("fixed", "baseline", "current"): if
key not in char: raise VaultError("VAULT_CHARACTER_BLOCK_INCOMPLETE", ...)`
(`src/engine/vault.py:154-157`). Write this whole file, `characters/Stub.md`, before you run
either linter. It begins:

```
---
type: character
id: stub
---

A placeholder character, authored only so this book has one and both linters will run at all.
Replace this with a real person before the book is played — nothing here is meant to survive
into a run.

## Beliefs

- (0.8, seed) This is a placeholder belief, written only so the shape below is not empty.
```

Then the one fenced json block:

```json
{ "fixed": {}, "baseline": {}, "current": {} }
```

That satisfies `load_book()`. It will **not** satisfy `lint_book.py`'s own, much stricter
per-character checks — a real character needs `fixed.name`, a complete `baseline.temperament`,
and a complete `current.affect`, among others, and those are the character blueprint's territory,
not this one's (`scripts/lint_book.py:129-144`). Expect `lint_book.py` to print several `ERROR`
lines naming this stub's missing fields. **That is fine, and expected — ignore them for now.**
`lint()` collects every problem it finds into one report and prints all of it; it never stops at
the first error (`scripts/lint_book.py:59, 301-305`), so the lines that actually matter here — the
ones naming `world.*`, `laws`, `locations`, `people` and `lexicon` — print in full regardless of
what else is wrong with the stub. Come back and write the character for real once this world note
is done.

Two commands, run from the project root. Neither of them changes your file.

**The book linter** reads your whole world and your characters and prints warnings and errors:

```
python scripts/lint_book.py --vault "<path to your book folder>"
```

An error means a run would break. A warning means something is authored but switched off — an
empty people list, a lexicon that is missing, a relationship pointing at nobody. A run with
warnings is **not** clean; the tool says so itself (`scripts/lint_book.py:307-309`).

**The scene linter** checks one scene config against this world — that its location is
registered, its act is keyed by a law, and its cast exists
(`scripts/lint_scene.py:65-140`).

### A hand checklist before you type anything in

Walk this list with your filled sheet in front of you. It catches the things a linter cannot.

- [ ] Exactly one file in `world/`, and its frontmatter says `type: world`.
- [ ] Exactly one fenced `json` block, and it is the first one in the file.
- [ ] All three switches answered with bare `true` or `false`.
- [ ] If any switch is `true`, there is at least one law with `domain: "supernatural"` saying
      what it **cannot** do.
- [ ] Every `subtle_cue_classes` name also appears as a bucket name in `attribute_classes`.
      (Not in `subtle_cues`. This is the one everybody gets wrong — see 8.3.)
- [ ] Every location a scene will name is in `locations`.
- [ ] Every character with a sheet in `characters/` also has an entry in `people`.
- [ ] Every person id's **first word** is the name your event text will actually print.
- [ ] Every law has an `act`, and the acts are spelled the same way your scenes will spell them.
- [ ] Every `FORBIDS` and `REQUIRES` has `teeth`.
- [ ] Every law in `supernatural`, `persons`, `fate` or `cosmology` states its `epistemic`.
- [ ] Read your five to ten `standing_facts` and ask of each: *could a draft contradict this?*
      If not, it is atmosphere. Move it into the prose.

### Before you go on to the character sheets

The character blueprint is a separate document, but four traps there have bitten real authors
of this engine, and it is cheaper to hear about them now:

1. **A genotype value is read by its FIRST WORD only.** Writing "very high" gets you the word
   *very*, which is not a known value, so it falls back to typical and says nothing
   (`src/engine/state.py:236-240`; the four known words are at `src/engine/state.py:26-31`). On
   a real book this understated a character's drive by a third. The linter now treats it as an
   error and tells you which words are legal (`scripts/lint_book.py:202-214`).
2. **A wound with triggers but no matching lever row computes nothing.** The fear is prose the
   engine cannot act on. The linter warns and names the trigger
   (`scripts/lint_book.py:239-248`).
3. **`current.active_goals` on a character sheet is overwritten every scene** by whatever drive
   the scene gave that character — `ch["current"]["active_goals"] = [{"goal": c["drive"], ...}]`
   (`scripts/scene.py:309`). Sheet goals matter to the linter and to you; they do not survive
   into a running scene.
4. **Drive orientation must be written in words, not numbers.** The identity renderer refuses
   any number it has no phrase for and names the path rather than dropping it silently
   (`src/engine/identity_view.py:201-207`, enforced at `:254-256`). A guide that tells you to
   write it as a number between minus one and plus one is out of date.

---

# 11. A complete filled example

This is the reference book's world note, with **two corrections** applied: `season` is dropped
because nothing reads it, and `subtle_cue_classes` is fixed to name `attribute_classes` buckets
instead of `subtle_cues` buckets (see 8.3). Everything else is as shipped, at
`$SWE_BOOKS/Beck` Hollow/world/BeckHollow.md`.

The file begins:

```
---
type: world
id: Beck Hollow — a valley village under a hard winter, and the wolves working down off the fell
---

# Beck Hollow

Forty-odd people in a fold of the hills, a mill on the beck, sheep on the low pasture and the
fell above them going white. No lord within three days' ride, no garrison, no one coming. What
the Hollow has, the Hollow does itself.

This is the third winter in a row that has come early, and the second in which the pack has
been seen on the fell road. Last winter they took lambs. This winter they have started coming
down in daylight.

## The premise this world exists to test

A man who is afraid can be made brave by his circumstances, or broken further by them, and the
difference is not courage — it is whether he is rested and whether he is loved. The village is
the apparatus. The wolves are the pressure. Nobody writes what he does.
```

Then the one fenced json block:

```json
{
  "world": "Beck Hollow",
  "switches": { "magic": false, "divine": false, "beings": false },
  "blueprint_defaults": true,

  "standing_facts": [
    "Beck Hollow holds about forty people. There is no garrison, no lord in reach, and no help coming before the thaw.",
    "The beck drives the mill. If the race ices over the mill stops, and a stopped mill in winter means no flour.",
    "Sheep are the Hollow's whole wealth. A fold lost is a family ruined, not inconvenienced.",
    "The pack came down off the fell twice last winter and took lambs. This winter they have been seen on the fell road in daylight, which is new.",
    "Wolves are animals. They are not spirits, they are not sent, and nothing in this valley is supernatural.",
    "A hard frost holds the beck for three or four days at a stretch; the ice has to be broken by hand or the race stops.",
    "Winter dark comes by mid-afternoon and holds until nine. Most of the day is not lit.",
    "The long hall is the only building with a hearth big enough for the whole village. People gather there when something is decided.",
    "Nobody in the Hollow has killed a wolf. Two men have tried, in living memory, and both were hurt doing it."
  ],

  "locations": [
    { "id": "mill", "what": "the mill house on the beck — the wheel, the race, the grinding floor, and the cot above it where Tam sleeps. Warm when the wheel turns, freezing when it stops" },
    { "id": "beck", "what": "the stream through the hollow, running fast and shallow, iced at the edges. The mill race is cut from it and must be kept clear by hand in a frost" },
    { "id": "fold", "what": "the drystone sheep fold on the low pasture, walls chest-high, a hurdle gate. Close enough to the village to hear a dog from, far enough that nobody sees what happens at night" },
    { "id": "fell-road", "what": "the track climbing out of the hollow onto open fell. Above the last wall there is no cover, no light, and no help. This is where the pack is seen" },
    { "id": "long-hall", "what": "the village hall — one hearth, benches, the tithe chest. Where the Hollow argues and where it decides" },
    { "id": "winter-store", "what": "the turf-roofed store behind the hall: grain, salt meat, lamp oil, and the count of how many weeks are left" }
  ],

  "people": [
    { "id": "tam", "name": "Tam Rill", "what": "the miller's son, thirty-one, who keeps the race clear and does not go up the fell road" },
    { "id": "nell", "name": "Nell Harrow", "what": "shepherd, forty, blunt and warm, who has lost four ewes to the pack and walks the fold at night alone" },
    { "id": "orrin", "name": "Orrin Cade", "what": "the hall-keeper, sixty, who counts the winter store and says out loud what everyone is thinking" }
  ],

  "lexicon": {
    "attribute_classes": {
      "threat": ["wolf", "wolves", "pack", "tracks", "howl", "blood", "carcass", "teeth", "growl"],
      "cold":   ["frost", "ice", "snow", "sleet", "wind", "frozen", "numb", "thaw"],
      "work":   ["race", "wheel", "flour", "grain", "hurdle", "fold", "ewe", "lamb", "fleece", "pail"],
      "light":  ["lamp", "lantern", "oil", "hearth", "dark", "dusk", "torch", "coal"],
      "harm":   ["wound", "bite", "bone", "blade", "axe", "spear", "bandage", "limp"]
    },
    "subtle_cues": {
      "watched":  ["the dogs went quiet", "the sheep bunched", "something moved at the wall"],
      "unspoken": ["nobody looked at him", "the hall went quiet when he came in", "she did not ask again"]
    },
    "subtle_cue_classes": ["threat", "harm"]
  },

  "laws": [
    {
      "id": "no-help-before-thaw",
      "domain": "legal",
      "modality": "IMPOSSIBLE",
      "epistemic": "known-true",
      "act": "summon-outside-help",
      "statement": "There is no authority within reach of Beck Hollow before the thaw. Nobody can send for anyone.",
      "source_note": "the world's isolation is the premise; removing it removes the pressure"
    },
    {
      "id": "a-wolf-is-an-animal",
      "domain": "cosmology",
      "modality": "IMPOSSIBLE",
      "epistemic": "known-true",
      "act": "treat-the-pack-as-sent",
      "statement": "The pack is animals following food down off the fell. It is not sent, not cursed, and not owed anything.",
      "source_note": "switches.magic is false; this law makes the mundane frame refusable rather than assumed"
    },
    {
      "id": "the-mill-must-run",
      "domain": "legal",
      "modality": "REQUIRES",
      "epistemic": "known-true",
      "act": "let-the-race-ice-over",
      "statement": "The race must be kept clear through a frost. A stopped mill in deep winter is the village going hungry.",
      "teeth": "the Hollow goes short, and everyone knows whose work it was",
      "source_note": "gives Tam a duty he already discharges — competence he does not count as courage"
    }
  ]
}
```

And it closes with prose again — a section headed "Note on what is deliberately absent", saying
in the author's own voice that all three switches are false and why
(`Beck Hollow/world/BeckHollow.md:192-196`).

## And one person, as a separate file

`people/Faron.md`, complete (`Beck Hollow/people/Faron.md:1-12`):

```
---
type: person
id: faron
---

A drover wintering over in the long hall with three dogs, waiting out the weather before he
takes the road south. Keeps to himself, feeds his dogs before he feeds himself, and has said
perhaps forty words since he arrived.
```

followed by a one-line json block giving `id`, `name` and `what`. Both the inline `people`
array above and this file end up in the same list (`src/engine/vault.py:125-138`).

---

# 12. Blank template to copy out

Copy this into `world/YourWorld.md` and replace everything in angle brackets. Delete any
optional line you are not using — an absent key is always safer than an empty one.

```
---
type: world
id: <the world's name — the pressure on it>
---

# <World Name>

<Two or three paragraphs: what this place is, who lives here, what is pressing on them.>

## The premise this world exists to test

<One claim this whole book is an apparatus for. A scene should be able to prove it wrong.>
```

Then the single fenced json block:

```json
{
  "world": "<Short Proper Name>",
  "switches": { "magic": false, "divine": false, "beings": false },
  "blueprint_defaults": true,

  "standing_facts": [
    "<a fact a draft could contradict, with its consequence in the same sentence>",
    "<...>",
    "<...>",
    "<...>",
    "<...>",
    "<...>"
  ],

  "locations": [
    { "id": "<handle>", "what": "<what a person standing here apprehends — conditions, not scenery>" },
    { "id": "<handle>", "what": "<...>" },
    { "id": "<handle>", "what": "<...>" }
  ],

  "people": [
    { "id": "<firstname>", "name": "<Full Name>", "what": "<what a neighbour would tell you about them>" },
    { "id": "<firstname>", "name": "<Full Name>", "what": "<...>" },
    { "id": "<firstname>", "name": "<Full Name>", "what": "<...>", "groups": ["<class>"] }
  ],

  "lexicon": {
    "attribute_classes": {
      "<bucket>": ["<word>", "<word>", "<word>", "<word>", "<word>"],
      "<bucket>": ["<word>", "<word>", "<word>", "<word>", "<word>"],
      "<bucket>": ["<word>", "<word>", "<word>", "<word>", "<word>"]
    },
    "subtle_cues": {
      "<cue>": ["<a phrase you would actually write>", "<another>"]
    },
    "subtle_cue_classes": ["<a bucket name from attribute_classes above>"]
  },

  "laws": [
    {
      "id": "<hyphenated-handle>",
      "domain": "<physical|supernatural|persons|fate|cosmology|legal|custom|economic>",
      "modality": "<IMPOSSIBLE|FORBIDS|REQUIRES|PERMITS>",
      "epistemic": "<known-true|known-false|contested-unknowable>",
      "act": "<the-thing-someone-might-attempt>",
      "statement": "<the rule, and what it means>",
      "teeth": "<what it costs — required for FORBIDS and REQUIRES>",
      "source_note": "<why this law exists in this book>"
    },
    {
      "id": "<hyphenated-handle>",
      "domain": "<...>",
      "modality": "<...>",
      "epistemic": "<...>",
      "act": "<...>",
      "actor_class": "<only this class may — optional>",
      "time_from": "<optional>",
      "time_to": "<optional>",
      "location_scope": "<a locations id — optional>",
      "statement": "<...>",
      "teeth": "<...>",
      "source_note": "<...>"
    }
  ]
}
```

Then close with prose again — a short section saying what you deliberately left out of this
world, and why. It costs you five minutes and it will save you an argument with yourself later.

---

# 13. Footnotes: where the project's own docs are wrong

Where a guide and the code disagree, this blueprint follows the code. These four disagreements
are the ones you are most likely to trip over.

**1. `world` (the title) is described as inert. It is not.**
`docs/world-authoring-rules.md:27-29` and `docs/guide-content.md:76-80` both list the `world`
title among fields with "zero runtime effect today". But the narrator is handed it by name every
time a scene is rendered to prose — `"WORLD: %s" % str(world.get("world", ""))`
(`scripts/narrate.py:131-134`). Fill it in.

**2. `standing_facts` is described as inert. Half true.**
The same two doc lines list `standing_facts` as inert. That is correct *for perception* — no
character ever receives one (`src/engine/gate.py:100-103`). It is wrong overall: the continuity
critic is handed the whole list as the canon a draft may not contradict
(`scripts/critic.py:81-82`, `:97-104`). Treat it as live, and write facts that can be
contradicted.

**3. `world.people` is described as coming from `people/*.md` only. It does not.**
`docs/new-book-manifest.md:128` says "`load_book` builds `world.people` from `people/*.md` notes
only." The loader starts from the world note's own inline `people` array and appends the files
to it — `people = list(world.get("people", []))` at `src/engine/vault.py:125`, then the file
loop at `:126-136`. Both routes work, and they combine.

**4. `people[].name` was recorded in an earlier audit as reaching only the optional critic.**
It reaches three live paths: display naming for the whole run
(`scripts/scene.py:77-92`), the wording of beliefs that witnesses form about each other
(`scripts/scene.py:518` into `src/engine/acquisition.py:109-114`), and the mid-scene learning of
a name by someone who knew only a descriptor (`src/engine/acquisition.py:158-179`).

**5. Line citations inside `docs/world-authoring-rules.md` are stale.**
That document cites `vault.py:81-88` for the json-block rule and `vault.py:92-93` for the
`type: person` filter. Those line numbers no longer point where the document says. The rules
themselves are right; the current lines are `src/engine/vault.py:64-69` and
`src/engine/vault.py:126-128`. Every line number in *this* blueprint was read from the file it
names.

**6. This sheet used to carry a "What could not be resolved" section here, about the law scope
fields in 9.8.** It said the wiring that reads `actor_class`, `target_class`, `time_from` and
`time_to` was "in flight" and only `act`/`location_scope` were confirmed live. That wiring has
since landed (`src/engine/bible.py:_applies`, 2026-08-30) and section 9.8 now describes the
shipped mechanism directly, including which of this engine's two callers supply which scope —
read 9.8, not this footnote, for the current state of that question.
