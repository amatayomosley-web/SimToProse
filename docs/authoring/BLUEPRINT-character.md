# The Character Blueprint

**A fill-in-by-hand form for building one person.**

---

## What this is, and what you get at the end

This is a form you can print and fill in with a pen. Work top to bottom. Nothing on page one asks
you a question you can only answer on page nine. When you reach the end you will have written one
whole person — their name and station, the temperament they were born with, what they want, what
they are afraid of, how they talk, who they know, and what they believe — and someone can type your
answers straight into a character note that the engine loads and an actor can play. You are not
asked to do arithmetic anywhere in this document. Where the machine needs a number, this form gives
you a short list of sentences and asks you to circle the true one; a separate person turns your
circle into the number. Every field below tells you what it is, shows you a real filled example,
and cites the exact line of code that reads it — so you can always see whether the thing you just
wrote actually does anything.

**Print this. Fill it in. Hand it to whoever types the sheet.**

---

## A few words you will need

Only five, and then we stop.

- **The sheet** — the fenced `json` block inside the character's markdown note. This is the part the
  machine reads.
- **The actor** — the language model that plays this character for one beat. It does not see your
  sheet's numbers; it sees sentences the engine builds from them.
- **The packet** — everything the engine hands the actor for one beat. Built fresh each time.
- **Live / inert** — a *live* field changes what happens. An *inert* field is read by nothing. This
  document tells you which is which and never asks you to fill in an inert one.
- **A primitive** — one of the engine's eight named feelings. There are exactly eight and you cannot
  add a ninth: `SEEKING, FEAR, RAGE, LUST, CARE, PANIC_GRIEF, PLAY, DISGUST`
  (`src/engine/records.py:19`).

---

## The shape of the file you are filling

One character is **one markdown file**, and it holds four things in this order:

````
---
type: character
id: tam
---

# Tam Rill

Free prose about them. Nobody's code reads this. Write it for yourself
and for whoever picks the book up after you.

```json
{ "fixed": {...}, "baseline": {...}, "current": {...} }
```

## Beliefs
- (0.95, I was twenty yards behind him and I stopped) When it matters I will not go.
````

- The `---` block at the very top is **frontmatter**. Only flat `key: value` lines are read
  (`src/engine/vault.py:54-63`). Every key you put there is kept.
- The prose between the heading and the code block is yours. It reaches nothing. Write it anyway.
- The **first** fenced `json` block is the sheet (`src/engine/vault.py:65-66`). If it is not valid
  JSON the book refuses to load and names your file and the parse error —
  `[VAULT_ENGINE_BLOCK_INVALID_JSON]` (`src/engine/vault.py:70-71`).
- `## Beliefs` is the memory section, and it has a strict bullet shape. Section 13 covers it.

The file lives at `<book>/characters/<Name>.md`. The book folder also needs exactly one world note
in `<book>/world/`, and any scene that runs this character needs a scene cfg in `<book>/scenes/`.
Neither format is this document's to give — the world note's shape is **BLUEPRINT-world.md** and
the scene cfg's is **BLUEPRINT-scene.md**. You need both, but not yet.

---

# PART ZERO — WHICH SYSTEMS YOUR BOOK RUNS

## 0.1 — The parts you may not need

Not every book needs everything the engine can do. A book says which of the engine's **systems** it
runs, once, in its **world note**, beside `switches`:

```json
"systems": {"wounds": false, "attitude": false}
```

Say nothing and every system runs — the engine exactly as it was before this switch existed. A
system you switch off is one whose part of this form **you can leave blank**, and whose work the
engine stops doing from the next scene on. What it already did stays in the story: a resting level
an earlier scene moved stays moved.

| System | What it does | The part of this form that feeds it | Off means |
|---|---|---|---|
| `condition` | energy and stress: the memory budget, and how much they have left | 11.2 | no condition block is needed; the stage directions say nothing of energy; memory runs on a full budget |
| `wounds` | scars: minted by lasting beats, tested by later ones, shown under what has marked you | Part Five | no scar is minted, tested or shown |
| `attitude` | what each person makes this character feel (`current.toward`, written by the engine) | none — the engine writes it | no attitude accrues, fades or is shown |
| `arc` | lasting beats move a character's resting levels | none — Part Three's resting levels stay as you wrote them | resting levels move no further |
| `condition_flow` — **OFF unless your book says `true`** | energy and stress MOVE: each beat costs its minutes and (for whoever acted) what it did to them; stress builds while fear, anger or grief run high; a declared gap between scenes is rest; a scene can state how worn someone arrives | 11.2 (both keys required) | energy and stress stay where the sheet or a scene put them — the engine as it always was |
| `tells` — **OFF unless your book says `true`** | subtle signs are REAL: the reader of each beat marks the small signs an actor let slip (a tremor, a glance at the door); a character sharp enough to catch them (9.1, perception) reads them and is told, one who is not never reads those words; with `condition_flow` on too, a tired mind catches less | 9.1 (perception) — nothing new to write | every listener reads every act whole, as before |
| `body` — **OFF unless your book says `true`; needs `condition_flow`** | each character has a strength, the reader of each beat names how physically hard the act was, and the engine charges it against that strength | 9.2 (required) | no act costs physical effort; the reader is never asked; no strength is needed |
| `injuries` — **OFF unless your book says `true`** | bodily harm is kept: the reader of each beat marks who was hurt, the words that show it and how badly (minor, serious or grave); each injury heals over story time by that word - a grave one leaves a lasting mark - and the one hurt and whoever saw it are told it every scene until it heals; with `body` on too, a serious or grave hurt weakens the body until then (9.2) | 11.2 (`injuries`, optional) | no injury is marked, kept or shown |
| `emotion`, `perception`, `memory`, `bonds`, `attachments`, `laws` | the core: moods, what they notice, what they know and recall, their edges, what they hold, what the world permits | Parts Two, Three, Ten; the world note | cannot be switched off yet — each needs its own proof that off changes nothing else |

**YOUR JOB — for the book, not the person.** Circle the systems your book does **not** need, and ask
whoever keeps the world note to write them `false`.

( ) condition   ( ) wounds   ( ) attitude   ( ) arc

And circle the one your book **does** want that is off until asked for:

( ) condition_flow — energy and stress move (needs `condition` on)
( ) body — strength and physical effort (needs `condition_flow` on)
( ) tells — a sign a character misses is one they never read
( ) injuries — a hurt is kept, told and healed over time

**What the machine does with it** (`src/engine/systems.py`). The pre-run check
(`scripts/lint_book.py`) and both drivers read the key. A name the engine does not know is refused
before the first beat (`SYSTEMS_UNKNOWN` — a typo would otherwise switch nothing off and say nothing),
as is anything but `true` / `false`, and a core system set `false`. Right before a scene's people are
built, an off system's block is emptied on every sheet, so every reader sees it absent, and its
per-beat mover is skipped. A book that declares a set records it on every beat, so the replay knows
which systems each beat ran.

**If you write a block for a system your book switched off**, the pre-run check warns you: it will
do nothing.

---

# PART ONE — WHO THEY ARE

Everything in this part goes in the sheet's `fixed` block. It is set once and never changes for the
life of the book.

---

## 1.1 — The file's type and id

**Where it goes:** the frontmatter at the very top, above everything.

**REQUIRED.**

```
---
type: character
id: tam
---
```

**What it is.** `type: character` is how the loader knows this file is a person and not a place or a
world note. `id:` is the short, all-lowercase handle the machine uses for this character everywhere
else — in other people's relationship lists, in the world's cast list, in the run log. Pick a single
lowercase word, usually their first name. No spaces, no capitals.

**Worked example.** `type: character` / `id: tam`

>> **HOW THIS IS USED:** `parse_note` reads flat frontmatter keys and gives `type` and `id` their own
>> slots (`src/engine/vault.py:53-62`); `load_book` then skips any note in `characters/` whose type
>> is not `character` (`src/engine/vault.py:142-143`) and files the rest under the id, lowercased
>> with spaces turned into underscores (`src/engine/vault.py:152`).

**IF YOU LEAVE IT BLANK:** the loader falls back to the filename, so `Tam Rill.md` becomes the id
`tam_rill` — and then every relationship anyone wrote pointing at `tam` silently points at nobody.
Declare the id. It costs one line and it is the join everything else hangs off.

**Common mistake.** Writing `id: Tam`. Ids are compared lowercased in some places and not in
others. Type it lowercase and it can never bite you.

---

## 1.2 — Their id, again, inside the sheet

**Key path:** `fixed.id`

**REQUIRED.** Write the same word you wrote in the frontmatter.

**What it is.** The name the actor's own identity block carries. It looks like a duplicate of the
frontmatter id. It is not — they are read by different code, and only this one reaches the actor.

**Worked example.** `"id": "tam"`

>> **HOW THIS IS USED:** the stable identity prefix the actor receives is built from
>> `fixed.get("id")` (`src/engine/scene.py:222`), and the engine uses that same value to decide
>> whether a feeling is pointed at *this* character or at someone else (`src/engine/prompt.py:53`).

**IF YOU LEAVE IT BLANK:** the actor's identity block reads `"id": null`. The pre-run check names
this exactly — it prints that `fixed.id` is missing and warns that a character-level `"id"` written
*outside* `fixed` does not fill it (`scripts/lint_book.py:182-184`).

**Common mistake.** Putting `"id"` at the top level of the sheet, next to `fixed`, instead of inside
`fixed`. It looks right on the page and reaches nothing.

---

## 1.3 — Their name

**Key path:** `fixed.name`

**REQUIRED.**

**What it is.** The full name a reader would call them. Written out, with capitals, the way it would
appear in the book.

**Worked example.** `"name": "Nell Harrow"`

>> **HOW THIS IS USED:** it goes straight into the actor's identity block
>> (`src/engine/scene.py:223`) — the actor is told, in words, who it is.

**IF YOU LEAVE IT BLANK:** the pre-run check treats it as an error, not a warning, and prints
`fixed.name missing` for that character (`scripts/lint_book.py:128-129`).

---

## 1.4 — What kind of creature they are

**Key path:** `fixed.people`

**REQUIRED.**

**What it is.** One word for their species or kind. In a book with only humans in it, this is
`"human"` for everybody, and that is fine — it is not wasted, it is the line that stops the actor
from wondering.

**Worked example.** `"people": "human"`

>> **HOW THIS IS USED:** it is carried into the actor's identity block
>> (`src/engine/scene.py:224`) and reaches the actor as a word. Nothing computes from it — searched
>> the whole engine and every consumer of `fixed.people` is that one line. It is prose for the
>> actor, not a lever.

**IF YOU LEAVE IT BLANK:** the actor's identity reads `"people": null`, and the pre-run check warns
you (`scripts/lint_book.py:185-186`).

---

## 1.5 — Where they stand in the world

**Key path:** `fixed.position` — four sub-fields: `place`, `class`, `era`, `niche`

**REQUIRED. This is one of the four fields every character owes, at any size of part.**

**What it is.** The four sentences that tell the actor what it is like to be this person in this
world. Not labels — sentences. **Write each one so the actor can act on it without looking anything
else up.** A culture's *name* is a pointer; a pointer is not grounding.

| sub-field | the question it answers |
|---|---|
| `place` | Where are they from, and how far does that reach? |
| `class` | What are they owed, what do they owe, what does everyone assume about them? |
| `era` | What is going on right now, in their lifetime, that they cannot ignore? |
| `niche` | What do they actually *do* all day, and what are they good at? |

**Worked example (all four, from Tam):**

- `place`: *"Beck Hollow — born in the mill, has never slept a night outside the valley"*
- `class`: *"the working freehold: not poor, not owed to anyone, and of no consequence. The mill is
  his father's and will be his, which is the only status he has and the only one he wants"*
- `era`: *"the third early winter in a row. The pack has been on the fell road in daylight, which is
  new, and the Hollow has begun to talk about what to do"*
- `niche`: *"the miller's son. Keeps the race clear through a frost, alone, before light. Competent
  with his hands, exact with the wheel, and does not count any of it as courage because nobody
  watches him do it"*

**Teach the judgement — a good answer and a weak one, side by side:**

| weak | good |
|---|---|
| `"class": "peasant"` | `"class": "the working freehold: not poor, not owed to anyone, and of no consequence"` |
| `"era": "medieval"` | `"era": "the third early winter in a row. The pack has been on the fell road in daylight, which is new"` |

The weak ones are true and useless. The actor cannot play "peasant". It can play "of no
consequence, and content with that".

>> **HOW THIS IS USED:** the whole `position` dictionary is copied into the actor's identity block
>> verbatim (`src/engine/scene.py:225`) and is carried through the words-only layer untouched,
>> because strings pass through it unchanged (`src/engine/identity_view.py:196-198`). What you write
>> here is read, word for word, by the thing playing this person.

**IF YOU LEAVE IT BLANK:** the actor receives an empty position and simply has no place, class or
station — it will invent one, differently, every beat. The pre-run check calls this out in those
words (`scripts/lint_book.py:169-171`).

**Common mistake, and it is the expensive one.** Writing this material into a block called
`formative` (with `culture`, `history`, `class` inside it). That block is read by no engine code and
no prompt. The pre-run check now names it and tells you to fold it into `fixed.position`
(`scripts/lint_book.py:176-181`). Beautiful, precise, and invisible.

**Extra sub-fields are allowed.** The dictionary is copied whole, so if you want a fifth key it will
reach the actor too. Keep them sentences.

---

## 1.6 — How big a part they play

**Key path:** `fixed.role_tier` — one of `principal` / `supporting` / `background`

**OPTIONAL — nothing reads it. Write it anyway.**

**What it is.** A promise you make to yourself about how deep to fill this form. It sets your fill
target and nothing else.

| tier | how much of this form to fill |
|---|---|
| `principal` | all of it, deep — every goal, profile picks that scar them at least once, six or more beliefs |
| `supporting` | the required fields, one goal, a profile pick or two that names a wound, a light voice, three or four beliefs |
| `background` | the required fields and nothing else — no beliefs, no profile pick that names a wound |

>> **HOW THIS IS USED:** it is not. Searched the engine and the scripts; `role_tier` appears in no
>> Python file. It is a note to the next person, and the reason to write it is that an undeclared
>> tier makes the next session guess, and guesses drift upward.

**IF YOU LEAVE IT BLANK:** nothing breaks. You just lose the record of how deep you meant to go.

**The thing that is NOT optional at any tier.** Four fields are owed by a one-line walk-on exactly
as much as by the protagonist, because they are wiring and not depth: `fixed.id`, `fixed.name`,
`fixed.people`, `fixed.position`, and `fixed.genotype` below. A background extra with no position is
not a thin character; it is a broken one.

---

# PART TWO — HOW HARD IT LANDS, HOW LONG IT STAYS

## 2.1 — The genotype: two cells per path

**Key path:** `fixed.genotype` — one `{hit, hold}` cell per PATH (STIRRING, WARINESS,
DISPLEASURE, GOODWILL, DEFLATION, DISTASTE, RECEPTIVITY, SELF-REGARD, LEVITY — the ninth since 2026-09-11)

**REQUIRED.** The key itself is one of the four fields owed by a one-line walk-on exactly as much
as by the protagonist (Part One). An individual PATH left out of the block defaults to the species
prior for that path — that is legal — but leaving the whole thing out flattens the character the
same way it always has.

**What it is.** Owner's ruling, 2026-09-09 (decision 2): a genotype used to be six dials shared
across every feeling, then for a day it was one dial per path carrying everything a path needed.
Neither survived contact with a real character. It is now two independent dials PER PATH
(`src/engine/heritable.py:1-55`, the module docstring is the design record):

| cell | the question it answers | vocabulary |
|---|---|---|
| `hit` | how hard does a reading on this path land? | `low \| typical \| elevated \| high` |
| `hold` | how long does an excursion on this path stay with them before it lets go? | `brief \| typical \| long \| lasting` |

`hit` and `hold` have to be independent of EACH OTHER: a person can take a fright hard and shake it
off inside the hour (`hit: high`, `hold: brief`), or barely feel it and never quite let it go
(`hit: low`, `hold: lasting`) — one allele cannot say both, so it is two.

And both of them have to be independent of a THIRD thing that used to live in this same cell and no
longer does: **where the path sits when nothing is happening.** Two people can share every `hit`
and `hold` on WARINESS and still read as completely different people, because one of them rests
at `quiet` and the other at `raised` — the same allele is an occasional fright in one and permanent
vigilance in the other. That is not a heritable rate; it is a character-design choice, exactly like
their voice, and you author it in **Part Three**, not here. Owner's ruling, later the same
2026-09-10: *"Have temperament be a character design question, along with their voice and other
personality options."*

### The retired shapes — refused, not translated

Two shapes are GONE and the engine refuses to run either rather than guess a translation:

- **The old six-axis genotype** — `threat_reactivity`, `approach_drive`, `affiliation_attachment`,
  `anger_proneness`, `effortful_control`, `sensitivity` (all retired 2026-09-10). A genotype block
  that still carries any of them fails outright — error `GENOTYPE_OLD_AXES`
  (`heritable.OLD_AXES`, `src/engine/heritable.py:104-105`, refused at `:129-158`; the pre-run
  check repeats the same refusal, `scripts/lint_book.py:317-321`).
- **A `rest` key inside a genotype cell** — the shape this section itself described for the few
  hours between the two rulings above. A cell that still carries `rest` fails outright too — error
  `GENOTYPE_REST_MOVED`, naming the path and telling you where the word goes now
  (`src/engine/heritable.py:151-157`; the pre-run check repeats it,
  `scripts/lint_book.py:333-338`).

Nothing maps an old sheet onto the new shape automatically, on purpose: a real book migrates once,
by hand, with its author's eyes on every line — the same way the two fixtures below were rewritten,
twice, on the same day.

### The annotation rule — same trap as before, same fix

**The engine reads only the first word of a cell, lowercased**, and nothing else
(`src/engine/heritable.py:111-118` — `word()`, the one parse every module now calls; before the
2026-09-10 rebuild four modules each carried their own copy of the split and a fifth reader did not
do it at all, which silently made `hold` a no-op on every annotated sheet). Put the vocabulary word
first, then your note in parentheses:

```
"hit": "high (anxious-leaning bond style)"
```

reads as `high`. `"very high"` reads as `typical` — the fallback — silently, exactly as it always
has for this project's word-first fields.

### Numbers, when a word will not say it

Either cell may instead carry a NUMBER, used exactly as authored rather than drawn from a preset:

- `hit` as a number is the gain itself.
- `hold` as a number is the half-life multiplier itself.

Reach for a number only when no word says the thing — the preset words are what most characters
should use, and the preset numbers themselves are carried, unmeasured placeholders from before the
rebuild (`GAIN`, `heritable.py:84-89`; `PERSIST`, `heritable.py:95-100`); nothing here claims they
are the right numbers, only that the code has to run on something while they get derived properly.

**Worked example (Maren, the healer — `characters/maren-healer.json`):**

```json
"genotype": {
  "STIRRING":    { "hit": "low",                                 "hold": "typical" },
  "WARINESS":    { "hit": "elevated",                            "hold": "long" },
  "DISPLEASURE": { "hit": "low",                                 "hold": "typical" },
  "GOODWILL":    { "hit": "high (anxious-leaning bond style)",   "hold": "long" },
  "DEFLATION":   { "hit": "elevated (loss goes deep, but it was the affiliation axis that made it
                    read high; grief pinned the probe at high under the minute clock)", "hold": "lasting" },
  "DISTASTE":    { "hit": "typical",                             "hold": "typical" },
  "RECEPTIVITY": { "hit": "typical",                             "hold": "typical" },
  "SELF-REGARD": { "hit": "typical",                             "hold": "typical" },
  "LEVITY":      { "hit": "typical",                             "hold": "typical" }
}
```

Attaches hard (GOODWILL hit `high`), keeps it (GOODWILL hold `long`, DEFLATION hold `lasting`), and
takes a threat harder than most (WARINESS hit `elevated`) — two independent dials pointed at one
central tension, care warped by control. Where she is watchful and sad even on an ordinary day
(WARINESS and DEFLATION resting `raised`) is not on this sheet at all; it is authored in Part
Three, beside her voice.

**Worked example (Ren, the traveler — `characters/ren-traveler.json`):**

```json
"genotype": {
  "STIRRING":    { "hit": "typical", "hold": "typical" },
  "WARINESS":    { "hit": "low (steady under danger; the road taught him early that panic is what kills you)",
                   "hold": "brief" },
  "DISPLEASURE": { "hit": "low",     "hold": "brief" },
  "GOODWILL":    { "hit": "elevated (attaches hard to the few he travels with)", "hold": "long" },
  "DEFLATION":   { "hit": "typical", "hold": "long" },
  "DISTASTE":    { "hit": "typical", "hold": "typical" },
  "RECEPTIVITY": { "hit": "typical", "hold": "typical" },
  "SELF-REGARD": { "hit": "typical", "hold": "typical" },
  "LEVITY":      { "hit": "typical", "hold": "typical" }
}
```

This is the "brave, but terrified of one specific thing" fixture, and nothing above mentions
spiders — that is the wound tier's job (Part Five, `baseline.wounds`, never authored by hand). The genotype only says he takes a threat
lightly and lets it go fast (WARINESS hit `low`, hold `brief`) — a level-headed man on the ladder,
before anything situational ever touches him. That he is *watchful* by disposition anyway (WARINESS
rests `raised`) is authored separately, in Part Three — the whole point of pulling rest out of this
cell was to let a character be steady under fire (the allele) and still carry worry into every scene
before anything happens (where he rests), without one field having to say both.

>> **HOW THIS IS USED:** `state.build_profile` reads exactly these two things per path off the
>> genotype (`src/engine/state.py:266-320`). The `hit` cell becomes the path's gain — the one
>> per-character term in the accumulation rule, clamped to `[0.5, 2.5]`
>> (`heritable.hit`, `src/engine/heritable.py:168-172`). The `hold` cell bends the path's own decay
>> rate in HALF-LIFE units, never as an absolute rate, which is what lets the per-character system
>> and the global system be balanced separately (`heritable.hold`, `src/engine/heritable.py:175-178`;
>> `state.half_life_minutes` / `state.retention_for`, `src/engine/state.py:120-143`). Separately, any
>> cell authored as a WORD (never a number) is turned into a sentence the actor reads about itself
>> (`identity_view._ALLELE_PHRASES`, `src/engine/identity_view.py:140-205`, applied at
>> `src/engine/identity_view.py:319-335`): WARINESS hit `high` becomes *"you are afraid before you
>> know why"*; GOODWILL hold `lasting` becomes *"you do not stop caring for people who have stopped
>> deserving it"*; DEFLATION hold `lasting` becomes *"you do not recover from losses; you learn to
>> walk with them"*. `typical` has no sentence on purpose: an unremarkable cell is not
>> self-knowledge. Where they REST is a different field entirely now — see Part Three — and reaches
>> the actor as its own sentences, beside these.

**IF YOU LEAVE A PATH BLANK:** that path defaults to `{hit: typical, hold: typical}` — the species
prior (`heritable._DEFAULT_WORD`, `src/engine/heritable.py:107`) — same as before. Leave all nine
blank and this person reacts to everything exactly like everyone else; your cast converges.

**IF YOU GET A WORD WRONG:** the pre-run check treats it as an error, not a warning, and names the
path, the cell, what you typed, and the legal words for that specific cell
(`scripts/lint_book.py:339-350`). Run the check. It is the only thing standing between you and a
silently flattened character.

**Two ways to fill this in.** For background and supporting people, have someone draw them — there
is a script that draws both cells per path from a seed, and the same seed always yields the same
person (`scripts/make_genotype.py`'s `draw()`, described in `docs/guide-emotional-authoring.md`; the
same script's `draw_rest()` draws where they rest, for Part Three, from the same seed on a separate
salt, so the two never collide). For a principal, do it the way Maren and Ren were done: start from
the person the story needs and pick the words that produce them — then do the same again in Part
Three for where they rest.

---

# PART THREE — WHERE THEY REST, AND WHAT THEY FEEL ON PAGE ONE

For a few hours on the morning of 2026-09-10, `baseline.temperament` (3.1) was not authored at all
— it fell straight out of the genotype's `rest` cells you had just finished in Part Two. That did
not last the day. Later the same 2026-09-10, the owner moved it back out: *"Have temperament be a
character design question, along with their voice and other personality options."* **Temperament
is yours again — as words, not numbers.** You write where a character rests the same way you write
their voice: backward from the person the story needs. `current.affect` (3.2) still works the way
it always has: describe the opening mood in a sentence, and hand it over.

---

## 3.1 — Where they rest — a design choice, beside their voice

**Key path:** `baseline.temperament[path] = {rest, mean}` — one entry per PATH

**REQUIRED for principals and supporting characters, the same rule the voice owes (Part Eight).**
An individual PATH left out of the block is legal — it rests at `quiet`, the species floor, seeded
the first time the sheet reaches the engine — but leaving the whole block off means this person has
no legible resting face at all, the same flattening a blank genotype produces.

**What it is.** Where a path sits on an ordinary day, when nothing is happening to this person —
not an episode, a disposition. `rest` is a word naming a rung, 1-based, off `REST_WORDS`
(`src/engine/heritable.py:63`):

| word | rung |
|---|---|
| `quiet` | 1 |
| `low` | 2 |
| `raised` | 3 |
| `high` | 4 |

### THE REST CAP — a word only goes so high

`rest` is capped PER PATH, because past a certain rung a resting level stops reading as a
disposition and starts reading as an episode that never ends — nobody is written as *loathing*
things all day as their baseline:

| path | REST_CAP (rung) | what the cap is guarding |
|---|---|---|
| STIRRING | 3 | noticing / wanting reads as a trait; episode-grade wanting needs an object |
| WARINESS | 5 | worry reads as a disposition all the way up |
| DISPLEASURE | 4 | bristling reads as a disposition; past it, riled is an episode |
| GOODWILL | 5 | tenderness reads as a disposition (arguably 6) |
| DEFLATION | 4 | sorrow reads as a disposition; past it, misery is an episode |
| DISTASTE | 2 | squeamishness reads as a disposition; past it, revulsion is an episode |
| RECEPTIVITY | 5 | gladness reads as a disposition; wonder is an episode |
| SELF-REGARD | 4 | self-importance reads as a disposition (arguably 5); vanity is an episode |
| LEVITY | 3 | playfulness reads as a disposition; banter needs a second mind, so it is an episode (unmeasured, 2026-09-11) |

(`src/engine/heritable.py`, `REST_CAP`.) **A word can only ever name rungs 1-4** (`quiet / low / raised /
high`), so the cap only actually stops a WORD on three paths — STIRRING and LEVITY (capped at 3: `high`
is above it) and DISTASTE (capped at 2: `raised` and `high` are both above it). On the other six paths
the cap still matters for an authored NUMBER, which can land on a rung no word reaches.

A rest above the cap — word or number — is HONOURED exactly as written, never blocked: the pre-run
check WARNS instead, naming the rung, so a character resting at genuine loathing is a decision you
made on purpose, with a receipt, and never a typo (`scripts/lint_book.py:379-383`).

### The annotation rule — same trap as before, same fix

**The engine reads only the first word, lowercased**, and nothing else (`heritable.word`,
`src/engine/heritable.py:111-118` — the one parse every module calls). Put the vocabulary word
first, then your note in parentheses:

```
"rest": "raised (watchful by habit)"
```

reads as `raised`.

**IF YOU GET A WORD WRONG:** the pre-run check treats it as an error, not a warning, and names the
path and the legal words for `rest` (`scripts/lint_book.py:371-375`).

### Numbers, when a word will not say it

`rest` may instead carry a NUMBER — the resting mean directly, clamped to `0.0`-`1.0`
(`heritable.rest_mean`, `src/engine/heritable.py:235-240`) — bypassing the rung system entirely
except for the cap warning above.

### The derived mean, and why it is stored

The first time a character sheet reaches the engine, every path's `rest` word is read ONCE into a
`mean` — the rung's band midpoint off the live ladder at that moment
(`heritable.rest_mean`, `src/engine/heritable.py:235-240`; `heritable.ensure_temperament`,
`src/engine/heritable.py:276-298`, called at `src/engine/scene.py:96` and
`src/engine/state.py:301`) — and STORED onto the row. You never write `mean` yourself.

**Why store it if it is only derived once:** the arc engine writes durable diffs into `mean` over
the life of a run, and `arc.erode` relaxes a character back toward the value stamped here — so a
row that already carries a mean KEEPS IT, on every later read, rather than being recomputed and
losing the run's own history.

**If a sheet already carries a mean that disagrees with its rest word** by a whole rung, the
pre-run check WARNS, naming both — this is how an old primitive-scale sheet, or a rest word moved
without its mean, gets caught (`scripts/lint_book.py:387-393`). Delete the mean to re-seed it from
the current rest word, or move the rest word to match.

**IF YOU LEAVE A PATH BLANK:** it rests `quiet` — the species floor
(`heritable._DEFAULT_REST`, `src/engine/heritable.py:108`) — seeded the first time the sheet is
used. There is no way to "get a blank wrong."

### The sentence the actor is shown

A rest word is not kept from the actor the way an allele word once was in this same slot — it is
said outright, under `disposition`, beside the six HEXACO sentences of 7.3, because a resting point
is exactly the kind of thing a person knows about themselves. `quiet` and `low` have no sentence on
purpose: an unremarkable resting point is not self-knowledge.

**Circle one per path** (all sixteen sentences below are the engine's own,
`identity_view._REST_PHRASES`, `src/engine/identity_view.py:115-138`):

**STIRRING**
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) there is always something you are half reaching for ( ) you are never quite at rest; something always has your attention

**WARINESS**
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) some part of you is always listening for trouble ( ) you live braced, and have for as long as you remember

**DISPLEASURE**
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) there is a low irritation in you most days ( ) you are easily put on edge and rarely fully off it

**GOODWILL**
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) you are warm to people before they have earned it ( ) caring for someone is your resting state, not a decision

**DEFLATION**
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) there is a sadness under you that ordinary days do not lift ( ) you carry a weight most people never notice you carrying

**DISTASTE**
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) much of what people do sits badly with you ( ) you are hard to please and quick to turn from what fails you

**LEVITY** (the ninth path, 2026-09-11)
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) you are quick to take an opening when one comes, and the room is lighter for it ( ) you are rarely wholly in earnest; the frame is where you live

**RECEPTIVITY**
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) you are open to being pleased by ordinary things ( ) you walk into most rooms already glad

**SELF-REGARD**
( ) no sentence — an ordinary resting point says nothing about you ( ) no sentence — an ordinary resting point says nothing about you
( ) you think well of yourself without needing to be told ( ) you carry yourself as someone who matters, and expect it to be noticed

Rendered under `disposition` as keys like *"wariness at rest"*, beside the trait sentences of 7.3
(`src/engine/identity_view.py:303-317`). `scene._build_stable` carries only the WORD per path, never
the seeded mean — a number in `rest` has no phrase and reaches the actor as nothing at all
(`src/engine/scene.py:271-280` `_rest_words`, used at `:325`).

**Worked example (Maren's temperament, `characters/maren-healer.json`):**

```json
"temperament": {
  "STIRRING":    { "rest": "low",    "mean": 0.13 },
  "WARINESS":    { "rest": "raised", "mean": 0.175 },
  "DISPLEASURE": { "rest": "quiet",  "mean": 0.035 },
  "GOODWILL":    { "rest": "high",   "mean": 0.315 },
  "DEFLATION":   { "rest": "raised", "mean": 0.24 },
  "DISTASTE":    { "rest": "quiet",  "mean": 0.075 },
  "RECEPTIVITY": { "rest": "low",    "mean": 0.125 },
  "SELF-REGARD": { "rest": "low",    "mean": 0.16 },
  "LEVITY":      { "rest": "quiet",  "mean": 0.05 }
}
```

Raised on WARINESS, raised on DEFLATION, high on GOODWILL — watchful and a little sad on an
ordinary day, and warmer than most before anyone has earned it. Her `hit`/`hold` cells (Part Two)
say how much harder a threat or a loss lands on top of that, and how long it stays; this block says
where she starts from before either ever fires.

**Worked example (Ren's temperament, `characters/ren-traveler.json`):**

```json
"temperament": {
  "STIRRING":    { "rest": "quiet", "mean": 0.04 },
  "WARINESS":    { "rest": "raised (watchful by habit — the road and the old workings; the HIT is
                    what is steady)", "mean": 0.175 },
  "DISPLEASURE": { "rest": "quiet", "mean": 0.035 },
  "GOODWILL":    { "rest": "raised", "mean": 0.225 },
  "DEFLATION":   { "rest": "quiet", "mean": 0.04 },
  "DISTASTE":    { "rest": "quiet", "mean": 0.075 },
  "RECEPTIVITY": { "rest": "low", "mean": 0.125 },
  "SELF-REGARD": { "rest": "low", "mean": 0.16 },
  "LEVITY":      { "rest": "quiet", "mean": 0.05 }
}
```

Quiet almost everywhere except WARINESS and GOODWILL, both `raised` — watchful by habit and warm to
the very few he travels with. That is the disposition his low WARINESS `hit` and brief `hold` (Part
Two) sit underneath: steady when a threat actually lands, never mistake that for a man who is not
also, quietly, always listening.

**Background and supporting cast: draw it, from the same seed as the genotype.**

```bash
python scripts/make_genotype.py --seed <anything>
```

prints both blocks — `genotype` and `temperament` — from one seed, `temperament`'s rest word drawn
on its own salt so it never collides with `hit`/`hold` (`make_genotype.draw_rest`,
`scripts/make_genotype.py:89-99`), and never above the path's cap.

---

## 3.2 — What they are feeling on page one

**Key path:** `current.affect` — the same eight names, one number each

**REQUIRED — all nine, again.**

**What it is.** Their actual mood at the moment the book opens. **Unless your book opens
mid-crisis, this should sit at or very near the resting face you authored in 3.1** — the difference
between "she is an anxious person" and "she is frightened right now" is exactly this gap.

**YOUR JOB.** One sentence: *"Where is this person, emotionally, in the first scene?"* If the answer
is "ordinary, for them", say that and the sizer will copy the resting values across.

```
On page one they are ________________________________________________
```

**Worked example (Tam):** resting FEAR 0.62, opening affect 0.58 — very slightly *below* his own
rest, because chapter one opens on an ordinary cold morning at the mill and the ordinary is where
he is most himself.

>> **HOW THIS IS USED:** it is the live feeling every beat starts from, handed to the packet as the
>> character's current state (`src/engine/scene.py:136-143`) and rendered as stage directions the
>> actor acts on.

**IF YOU LEAVE A PRIMITIVE OUT, OR PUT ONE OUTSIDE THE SCALE:** the pre-run check errors, names the
primitive, and says the appraisal step needs all nine (`scripts/lint_book.py:134-141`).

---

# PART FOUR — WHAT THEY WANT

## 4.1 — Their goals

**Key path:** `baseline.drives.goals` — a list. Each entry has `goal`, and a strength.

**REQUIRED for principals and supporting characters. A walk-on may have none.**

**What it is.** The concrete things this person is actually trying to bring about. Not values — a
value is "she cares about family"; a goal is **"she will get her brother out of that prison."** A
goal is something a scene can advance or block.

**THE KEY IS `goal`.** Not `statement`. Write:

```json
{ "goal": "keep the race clear so the mill never stops", "priority": 0.8, "satisfaction": 0.7 }
```

*(Footnote: `docs/drives-schema.md:18` calls this field `statement`. The code does not. Every place
that reads a goal's text reads the key `goal` — `src/engine/gate.py:313`, `src/engine/gate.py:346`,
`src/engine/identity_view.py:273`. Follow the code. The doc is wrong and is being corrected.)*

**How many.** A principal: three or four. A supporting character: one. Sparse is correct — most
people are not driven on most axes, and an unwritten goal is not a missing goal, it is an honest
"nothing pulls her there."

**YOUR JOB — write each goal as a sentence in their own terms, then circle how much it matters:**

```
GOAL 1: ______________________________________________________________

  How much does it matter?  (circle one)
    ( ) I would drop this before anything else
    ( ) it matters, and it yields to the rest
    ( ) it outranks most of what I want
    ( ) nothing I want outranks this

  How settled is it already?  (circle one)
    ( ) nothing about this is settled
    ( ) I have made a start and it is not enough
    ( ) this is mostly where I want it
    ( ) this one is handled and I can leave it alone
```

*(Those two ladders are the engine's own words, not invented for this form — they are the exact
sentences the actor is shown for `priority` and `satisfaction` at
`src/engine/identity_view.py:80-87`. Whoever sizes the sheet turns your circle into the number; the
band edges live in `src/engine/direction.py:133`.)*

**Worked example (Nell, all three):**

| goal | priority band | satisfaction band |
|---|---|---|
| *"keep the fold whole through to the thaw"* | nothing I want outranks this — **0.88** | I have made a start and it is not enough — **0.30** |
| *"stop being the only one who walks up there after dark"* | it outranks most of what I want — **0.70** | nothing about this is settled — **0.15** |
| *"get Tam Rill onto the hill once, on any pretext"* | it matters, and it yields to the rest — **0.40** | nothing about this is settled — **0.05** |

> **Corrected 2026-08-30.** This table previously showed the phrases without their numbers, and
> two of its rows had drifted from the sheet they quote: the band edges are 0.25 / 0.55 / 0.80,
> so `satisfaction: 0.30` renders as *"you have made a start and it is not enough"*, and
> `priority: 0.55` renders as *"it outranks most of what you want"*, not the milder phrase. The
> numbers above are the ones that produce the sentence beside them.

Her third goal carries `"note": "she thinks he would be all right afterwards. She has not told him
that"` — the note is stripped before the actor sees it, so it is a message to you, not to her.

**Phrase them with the nouns your scenes will use.** This is not style advice, it is mechanical: a
belief surfaces during a scene partly because its words overlap the words of an active goal
(`src/engine/gate.py:335-348`). A goal about conscription that never says *levy* or *draft* cannot
lift a belief that does.

>> **HOW THIS IS USED:** the whole `drives` block is copied into the actor's identity prefix
>> (`src/engine/scene.py:230`); each goal's strength is replaced with one of the four sentences above
>> and every other key you wrote is carried through unchanged
>> (`src/engine/identity_view.py:244-252` and `src/engine/identity_view.py:259-266`). The actor reads
>> your goals in your words.

**IF YOU LEAVE IT BLANK:** nothing errors. The actor is simply told nothing about what this person
is for, and it will invent something plausible and different every beat.

**LEAVE BLANK — nothing reads these.** The drives design document lists six more keys on a goal:
`kind`, `serves`, `status`, `origin`, `triggers`, `view` (`docs/drives-schema.md:16-27`). No engine
code reads any of them; they are carried into the identity prefix as extra text if you write them,
and computed with nowhere. Skip them. **The exception:** if a phrase like `"view": "self"` genuinely
tells the actor something useful about the character, it will reach the actor as words — but it will
not *do* anything, and you should not fill it in expecting a mechanism.

---

# PART FIVE — WHAT HAS MARKED THEM

## 5.1 — Their wounds

**Key path:** `baseline.wounds` — a list. **Engine state. Not yours to write.** A book that switches
`wounds` off (Part Zero) mints, tests and shows no scar; skip this part.

**GATE THREE, 2026-09-11.** The owner: *"wounds are a multiplier, so move it out of character
sheet and make it an engine script"* and *"link wounds to the emotion paths, the wound multiplies
that linked emotion."* The block this section used to have you fill in by hand —
`baseline.drives.fears_wounds`, a `wound`, a strength, a `trigger` list, an `avoidance` list — is
not read any more. It is now ENGINE STATE, minted, and it is a MULTIPLIER on a reading, not a
paragraph the actor recites.

**How one comes to exist — two ways, and both are recorded, never authored as prose:**

**(a) At creation.** You do not write a wound; you pick a formative profile (Part 1), the same
composition pass that seeds temperament and the worth menu. If a profile's library row names a
concept, the composition pass mints the wound for you
(`scripts/composition_pass.py:163-176`, calling `src/engine/wound.py:308-326`,
`from_profile_row`). The row's `magnitude` — the number that used to size an old-style
`baseline.catalog` multiplier, `1.4..2.5` — becomes the wound's `intensity` on a linear map onto
`0.40..0.95`: `x1.4 -> 0.40`, `x2.5 -> 0.95` (`src/engine/wound.py:314-324`). If your story needs a
specific backstory scar, find the profile that carries that concept, or propose one through the
formative library's admission gate. There is no other door onto the sheet.

**(b) Mid-story.** A DURABLE beat — the arc engine's own candidate test: the actor tagged it
durable, or a dimension reached 0.6 or more — in which the seat READ a path bound to a registry
concept at one of the top two rungs of that path's ladder mints the wound, at the reading's height,, if none already exists for
that (concept, path) pair (`src/engine/wound.py:329-362`, `mint`; the two-rung cutoff is
`_MINT_RUNGS_FROM_TOP = 2` at `src/engine/wound.py:121`). Its `intensity` is the path's own value
at that moment; its `text` is the beat's own words; its `trigger` is the surfaces the character
actually perceived, kept as the words the actor is told set it off. It is written as an
append-only `wound_minted` row and folded back onto the sheet on the next resume — stop a run and
restart it, and the character carries the same scar (`tests/test_multipliers.py`, case 4,
`a-resumed-sheet-carries-the-same-scar`).

**What the sheet carries, once minted:**

```json
{"id":        "<concept>@<PATH>",
 "concept":   "<a registry id — the table below>",
 "path":      "<one of the nine emotion paths>",
 "intensity": 0.0,
 "source":    "profile:<id>  |  run:<turn>",
 "text":      "<what happened, in words>",
 "trigger":   ["<a surface the character perceived>", "..."]}
```

`id` is derived — `concept@PATH` — never authored (`src/engine/wound.py:279-281`, `wound_id`).
`source` must start `profile:` or `run:`; anything else is a wound hand-written rather than minted,
and the pre-run check refuses it by name (`scripts/lint_book.py:437-440`). The shape itself —
`concept` in the registry, `path` one of the nine, `intensity` in `[0,1]` — is checked at
`src/engine/wound.py:284-295`, `_check`.

**You do not write this. Here is what it looks like when you read a sheet.** Maren carries three:

```json
{"id": "sickness@WARINESS", "concept": "sickness", "path": "WARINESS", "intensity": 0.85,
 "source": "profile:fixture-suil",
 "text": "her daughter Súil died of a fever she could not break (Maren age 31)",
 "trigger": ["a child with fever", "a patient she might lose"]},
{"id": "loss_of_a_child@DEFLATION", "concept": "loss_of_a_child", "path": "DEFLATION",
 "intensity": 0.85, "source": "profile:fixture-suil",
 "text": "her daughter Súil died of a fever she could not break (Maren age 31)",
 "trigger": ["a child with fever", "being asked to trust someone else with a life"]},
{"id": "helplessness@WARINESS", "concept": "helplessness", "path": "WARINESS", "intensity": 0.5,
 "source": "profile:fixture-too-late", "text": "being too late / not enough",
 "trigger": ["delay", "a case beyond her skill"]}
```
(`characters/maren-healer.json:218-258`.) Ren carries one — the spider scar that used to be a
`baseline.catalog` row multiplying FEAR x3.4 by itself is gone; a wound is an investment now, never
a bare float:

```json
{"id": "predator@WARINESS", "concept": "predator", "path": "WARINESS", "intensity": 0.95,
 "source": "profile:fixture-spider",
 "text": "a hunting spider's bite swelled his face shut and left him three days blind when he was
          a boy; he was alone in a barn loft and nobody came until it had run its course",
 "trigger": ["spider", "web", "something moving in the dark above"]}
```
(`characters/ren-traveler.json:255-272`.)

**The concept registry — closed, 49 entries** (`src/engine/concepts.py:40-96`). A wound's
`concept` must be one of these ids, spelled exactly this way, and there is no fuzzy match: a scar
keyed on `sickness` is matched later by a beat about `concept:sickness`, by string equality, or it
is not matched at all.

| id | what it is |
|---|---|
| *the body in danger* | |
| `fire` | fire, smoke, burning, being trapped by flame |
| `drowning` | deep water, sinking, a storm at sea, going under |
| `predator` | a beast, a hunting animal, fangs and claws, being stalked |
| `cold` | freezing, exposure, a blizzard, the body shutting down |
| `confinement` | a locked cell, chains, a cage, a space too small to leave |
| `collapse` | a roof or a tunnel coming down, crushing weight, being buried |
| `poison` | something in the food or the cup; a taste that should not be there |
| `contamination` | a substance that sickens by touch or air; a place that is unclean |
| `sickness` | illness in a body — fever, plague, a sore that will not heal |
| `injury` | a wound to the body, blood, a limb that will not work |
| `bombardment` | a blast, artillery, a noise that shakes the ground |
| *want and lack* | |
| `hunger` | no food, an empty larder, rations cut, watching others eat |
| `thirst` | no water, a dry throat, a cracked land |
| `debt` | money owed, a ledger against you, the bailiff, eviction |
| `siege` | gates closed, supply cut, waiting inside walls for the end |
| `exile` | being cast out — a border, a camp, a home you cannot return to |
| `servitude` | forced labour, the whip, the bench, a life that is not yours |
| *the social world* | |
| `crowds` | a press of people, noise, a mob, too many voices at once |
| `arrest` | the watch, irons, being taken, the law laying hands on you |
| `authority` | officials, edicts, protocol, being made to bend to a rule |
| `isolation` | being alone too long, silence, no one coming |
| `shame` | public disgrace, a mark others can see, being made small before people |
| `outsiders` | strangers, the corrupt city, people not of your kind |
| *what people do to each other* | |
| `betrayal` | trust given and turned against you by someone who had it |
| `disownment` | cast out by your own family or clan |
| `infidelity` | a lover or spouse who lied about love |
| `broken_oath` | a sworn promise broken; a pact abandoned |
| `abandonment` | left behind — by allies, by those who should have come |
| `helplessness` | watching harm come to someone and being unable to stop it |
| `loss_of_a_child` | a child dead or dying; the one loss that does not un-happen |
| `death` | a death witnessed or learned of; a body; the fact of it |
| *violence* | |
| `war` | a raid, a sacking, a town put to the sword |
| `combat` | steel drawn, being cornered, a fight to the end |
| `conscription` | the levy, the muster, drums and drill, being taken to fight |
| `pursuit` | being hunted — patrols, searchlights, an informant's whisper |
| `execution` | a sentence of death; the scaffold; the firing line |
| `interrogation` | questioning under duress; a tribunal; being made to confess |
| `assassination` | an attempt on a life — the bolt from the gallery, the sudden stop |
| *vocation and station* | |
| `shoddy_work` | bad craft, a flawed joint, waste of good material |
| `accounts` | a ledger that does not balance; a coin missing; an audit |
| `sacrilege` | a holy thing defiled — scripture burned, a shrine desecrated |
| `heresy` | false belief, blasphemy, the apostate |
| `indulgence` | luxury, gluttony, comfort of the flesh |
| `court_intrigue` | flattery with a hook in it; the gift, the private audience |
| `forced_marriage` | a betrothal made for alliance; a dowry; a contract on a body |
| `usurpation` | a birthright taken; an estate confiscated; a rival on your seat |
| `omens` | a comet, an eclipse, a prophecy demanded or feared |
| `excommunication` | cast out of the faith; the seal broken; the decree read |
| `possession` | a demonic accusation; the rite; the bindings |

**The four intensity sentences** — the engine's own, and the only place the number becomes words
(`src/engine/identity_view.py:69-70`):

| intensity | how it reads |
|---|---|
| below ~0.25 | *"an old scar you rarely feel"* |
| ~0.25 – 0.55 | *"it catches you sometimes"* |
| ~0.55 – 0.80 | *"it takes hold of you when it comes"* |
| above ~0.80 | *"it takes you over"* |

**IF YOU LEAVE IT BLANK:** a character with no profile picks that name a concept has no scars. That
is not a hole in the sheet — it means nothing has marked this life that way yet. The story may
still give them one, path (b) above; you are not required to pre-author every wound a run might
mint.

**IF YOU WRITE `fears_wounds` ANYWAY:** the pre-run check errors, naming `baseline.wounds` and the
profile route as the fix (`scripts/lint_book.py:417-423`). This is not a warning you can leave in —
the field is not read at all, so a run built against it is missing the friction you meant to write,
and nothing will tell you that until someone goes looking.

**Where the old `avoidance` list goes.** What the character *does* instead of feeling it was never
read by the engine — it is conduct the rung owns, not the wound. It still belongs somewhere real:
`voice.register`, or the persona, beside the other things that are simply who they are. Maren's
sheet leaves a note explaining why the old avoidance lists are gone
(`characters/maren-healer.json:178`) and folds the actual behaviour into `voice.tics`, below it
(`characters/maren-healer.json:202-206`) — *"deflects praise," "counts doses/steps aloud when
anxious," "refers to the dead by what they needed, never by grief."*

>> **HOW THIS IS USED:** the engine strips a wound down to what a person could actually say about
>> their own scar and renders it under `"what has marked you"` in the actor's identity prefix
>> (`src/engine/scene.py:271-283`, `_wounds_for_prefix`, feeding `src/engine/scene.py:297-326`,
>> `_build_stable`). What reaches the actor is `{about: the concept's gloss — never the id, what
>> happened: your text, how it takes you: one of the four sentences above, what sets it off: your
>> trigger words}` (`src/engine/identity_view.py:363-382`). The `path` is the engine's own key for
>> matching a later beat and is never shown — it is not something a character introspects.

---

## 5.2 — WHAT MAKES A SCAR FIRE (it is not the trigger list)

**Your `trigger` list, on its own, still computes nothing — and there is no catalog row left to
hand it to.** Before gate three, an unmatched trigger list was a warning pointing you at a sizer who
would build the arithmetic twin. That warning, and the tier it pointed at, are both gone: a wound
is never sized by hand, and there is no `baseline.catalog` row for one any more.

**The link a later beat needs is a CONCEPT, not a word.** Owner: *"wounds are conceptual, a mother
with a sick kid gets a wound for sickness. That's not a word but a concept."* A wound keyed
`(sickness, WARINESS)` fires when a later beat is ABOUT `concept:sickness` on WARINESS — matched by
plain string equality on the concept id the beat resolved to, never by scanning the event text for
a word (`src/engine/wound.py:178-186`, the identity-first branch of `fires`). Naming what a beat is
about is one semantic step — today the appraiser seat (`scripts/appraiser.py`) or the actor's own
self-tags — always validated against the closed registry (`src/engine/concepts.py:111-123`,
`id_of`) and refused by code if it names anything the registry does not carry.

**Your trigger list still does one real job.** `wound.fires` also matches the perceived surfaces of
the scene against your `trigger` phrases directly — the cue-in-the-room case, where nobody names
the concept in words but the thing that caused the wound is simply *there* (a spider on the wall;
no one says "predator"). That match is against what the character actually PERCEIVED, never the
ground-truth event text — you cannot be triggered by what you did not perceive
(`src/engine/wound.py:160-166`, `188-201`).

**What you can actually do to make a scar fire:**
- **Write the scene about the concept, in words a reader would recognise.** If the appraiser (or
  the actor's own self-tag) can look at the beat and say "this is about sickness," the concept link
  fires, whatever words are on the page.
- **Pick the profile whose concept matches what your story needs.** The wound's concept comes from
  the formative profile at creation (5.1a). A character who needs a scar about drowning needs a
  profile that names `drowning` — there is no other way onto the sheet.
- **Keep writing trigger phrases in the plain words a scene would use**, exactly as before — they
  still matter for the cue-in-the-room case; they are simply no longer the whole mechanism.

---

# PART SIX — HOW THEY FACE THE WORLD

## 6.1 — Orientation

**Key path:** `baseline.drives.orientation` — four sub-fields

**REQUIRED for principals and supporting characters.**

### WRITE WORDS. NEVER NUMBERS. This one will take the book down.

**What it is.** Not what they pursue — *how*. Four short answers that colour every goal and every
fear they have.

| sub-field | the question | words that work |
|---|---|---|
| `locus` | Do things happen *to* them, or do they cause things? | `external` / `internal` |
| `agency` | How hard do they push on the world at all? | `low` / `moderate` / `high` |
| `coping_engagement` | Do they go at a problem or away from it? | `avoidant` / `approach` |
| `coping_expression` | Does it come out, or stay in? | `suppressed` / `practical` / `expressive` |

Those are the words the real books use. **They are not a closed list** — nothing validates them —
so `"locus": "external, except about the mill"` is legal and will reach the actor exactly as typed.
What is *not* legal is a number.

**Worked example (Tam):**
```json
"orientation": { "locus": "external", "agency": "low",
                 "coping_engagement": "avoidant", "coping_expression": "practical" }
```

**Worked example (Nell):**
```json
"orientation": { "locus": "internal", "agency": "high",
                 "coping_engagement": "approach", "coping_expression": "practical" }
```

>> **HOW THIS IS USED:** it rides inside the `drives` block into the actor's identity prefix
>> (`src/engine/scene.py:230`) and is passed to the actor verbatim — strings are carried through the
>> words-only layer untouched (`src/engine/identity_view.py:196-198`).

**IF YOU WRITE A NUMBER HERE, THE BOOK CRASHES.** Not silently — loudly, mid-run, when the prompt is
being built. The layer that converts the sheet into words refuses any number that is not between
zero and one and names the field path in the message
(`src/engine/identity_view.py:186-190`). A design document tells you to write `locus_of_control` on
a scale from minus one to plus one (`docs/drives-schema.md:49-53`); **that document is wrong and is
being corrected.** A negative number there stops the run.

**And a number between zero and one is worse than a crash.** It will not raise — it will quietly be
turned into a generic sentence like *"some of this"*, which says nothing about the person
(`src/engine/identity_view.py:97-98` and `:191`). A crash you notice. A bland sentence you do not.

**IF YOU LEAVE IT BLANK:** nothing errors; the actor is told nothing about *how* this person engages,
and defaults to a generically capable one.

---

# PART SEVEN — WHAT THEY WEIGH, AND WHAT THEY ARE LIKE

## 7.1 — The worth menu

**Key path:** `baseline.model` — three families of weights, plus `regard`

**REQUIRED for principals and supporting characters. The numbers are not yours.**

**What it is.** The dial-set that decides *why an event lands on this person at all*. Two people
watch the same slight; the one who weighs status heavily is hurt and the one who does not shrugs.
The families are the standard three: `schwartz` (values), `moral_foundations` (morals), `needs`.

**YOUR JOB — answer two questions in words:**

```
The three or four things this person will NOT trade away:
  _____________________________________________________________________

The two or three things that weigh very little with them:
  _____________________________________________________________________
```

That is genuinely all that reaches the actor. The engine pools all three families, ranks them, and
tells the actor *"you will not trade these away: security, care/harm, conformity"* and *"these weigh
little with you: stimulation, power"* — a ranking, not the numbers
(`src/engine/identity_view.py:133-158`, rendered at `:226-241`).

**Worked example (Tam, in words):** will not trade away — *security, care for the harmed,
conformity, loyalty*. Weigh little — *stimulation, power, achievement*. That is what his sheet's
figures come out as when ranked.

>> **HOW THIS IS USED:** two things, and they are different. (1) The weights decide how *relevant*
>> each kind of event is to this person, which scales how hard it hits
>> (`src/engine/state.py:265-281`). (2) The ranking — top four and bottom three, pooled across all
>> three families — is turned into two lists of plain words for the actor
>> (`src/engine/identity_view.py:133-158`).

**Silence is average, not absence.** A value you never write is read as exactly neutral, not as
zero (`src/engine/state.py:276`, and the same rule applied on the wording side at
`src/engine/identity_view.py:130`). So you never have to fill in the whole menu — write the ones you
mean, and the rest sit at average, which is usually true.

**IF YOU LEAVE IT BLANK:** every kind of event is equally relevant to this person, and the actor is
told nothing about what they hold. The pre-run check warns that the block is thin
(`scripts/lint_book.py:255-257`).

---

## 7.2 — Regard: the groups they do or do not count as people

**Key path:** `baseline.model.regard` — `{group_name: weight}`

**OPTIONAL. Powerful. The numbers are not yours.**

**What it is.** This is bigotry, or its absence, made mechanical. It names a group and says how much
this person's empathy extends to them. A group they hold low genuinely feels *less* to them when
something happens to one of its members.

**YOUR JOB — one line per group that matters:**

```
Group: ______________  and they  (circle one)
  ( ) do not count them as people
  ( ) hold them cheap, and it shows
  ( ) take them as they come
  ( ) would answer for them as they would for their own
```

*(Again, those four are the engine's own sentences — `src/engine/identity_view.py:67-70`.)*

**Worked example (Nell):** `"regard": {"hollow": 0.78}`. The band edges are 0.25 / 0.55 / 0.80
(`src/engine/identity_view.py` `_EDGE_BANDS`), so 0.78 sits in the THIRD band and the actor is
told *"you take them as they come"* — ordinary regard, no special claim. If you mean *"she would
answer for anyone in the valley as for her own"*, that is the fourth band and you must write
**0.90**. Corrected 2026-08-30: this example previously glossed 0.78 as the fourth band, which
taught the conversion wrong in the one place a reader is learning it.

>> **HOW THIS IS USED:** when an event is *about* a particular person, the engine looks up that
>> person's group and scales this character's empathy by their regard for it
>> (`src/engine/state.py:243-262`); the same map is turned into a sentence per group for the actor
>> (`src/engine/identity_view.py:234-238`).

**One mercy built into the machine, worth knowing.** Affinity toward a specific individual **lifts**
them above their group's floor and never lowers them (`src/engine/state.py:259-261`). A character
who holds a whole class cheap but has come to value one member of it is expressible. That is a real
arc and the code supports it directly.

**The group name must match a group actually declared on a person's entry in the world note**
(`src/engine/scene.py:393-407`), or nothing will ever look it up. That is a world-blueprint job —
tell whoever writes it which groups you used.

---

## 7.3 — Their disposition

**Key path:** `baseline.traits` — the six HEXACO facets, each `{"mean": ...}`

**REQUIRED for principals and supporting characters. The numbers are not yours.**

**What it is.** The behavioural style everything else expresses through. Six facets:
`emotionality`, `agreeableness`, `extraversion`, `conscientiousness`, `openness`,
`honesty_humility`.

**YOUR JOB — for each of the six, circle the sentence that is true of them.** These are, word for
word, the sentences the actor will be shown (`src/engine/identity_view.py:33-58`):

**emotionality**
( ) things land on you lightly and pass ( ) you feel things and set them down again
( ) you feel things hard and they stay a while ( ) you feel everything hard and it stays with you

**agreeableness**
( ) you hold a grudge and see no reason not to ( ) you forgive slowly and remember anyway
( ) you give people the benefit of the doubt ( ) you forgive before you have decided to

**extraversion**
( ) you say less than you think and prefer it that way ( ) you speak when spoken to
( ) you take up room in a conversation ( ) you fill a room and do not notice doing it

**conscientiousness**
( ) you start things and drift off them ( ) you finish what matters and let the rest go
( ) you finish what you start ( ) you cannot leave a thing half-done

**openness**
( ) you want what you already know ( ) you try a new thing when it is put in front of you
( ) you go looking for what you have not seen ( ) the unfamiliar pulls you before the familiar does

**honesty_humility**
( ) you take what you can get and call it fair ( ) you bend a rule when it costs no one you know
( ) you keep to your word when it costs you ( ) you would not take an advantage you had not earned

**Worked example (Tam):** *feels things hard and they stay a while · gives people the benefit of the
doubt · says less than he thinks and prefers it that way · finishes what he starts · wants what he
already knows · keeps to his word when it costs him.*

>> **HOW THIS IS USED:** two things again. (1) Three of the six actually compute: `emotionality`
>> raises how hard FEAR and PANIC_GRIEF land, `agreeableness` **lowers** RAGE, `extraversion` raises
>> PLAY and SEEKING (`src/engine/state.py:210-224`, applied at `src/engine/state.py:322-326`).
>> (2) All six are turned into the sentence you circled and shown to the actor
>> (`src/engine/identity_view.py:213-218`).

**The same `disposition` block carries one more set of sentences beside these six.** The rest word
you authored per path in Part 3.1 renders here too, as keys like *"wariness at rest"*
(`src/engine/identity_view.py:303-317`) — the actor is shown your traits and your resting face in
the same place, because both are self-knowledge and neither is a situational read.

**Be honest about the other three.** `conscientiousness`, `openness` and `honesty_humility` slope no
arithmetic. Write them truthfully — the actor reads them and plays them — but do not expect moving
one to change a computed outcome.

**IF YOU LEAVE IT BLANK:** every facet is treated as exactly average and the actor is told nothing
about their style. The pre-run check warns the block is thin (`scripts/lint_book.py:255-257`).

---

# PART EIGHT — HOW THEY SPEAK

## 8.1 — The voice profile

**Key path:** `baseline.voice` — seven sub-fields, all prose except one

**REQUIRED for anyone who speaks.**

**This block is passed to the actor word for word. The engine never parses it.** So write craft
text — the lines that make the actor sound like a person. Write them as prose you would be willing
to see quoted.

| sub-field | what to write |
|---|---|
| `register.formality` | how formal, and where that came from |
| `register.ornament` | plain or decorated — and what the words look like next to what they mean |
| `rhythm` | the shape of their sentences; do they interrupt, do they trail off |
| `assertiveness` | **circle a sentence, below** |
| `tics` | 2-3 verbal habits, distinctive and few |
| `code_switch` | `[{context, shift}]` — when does the voice change, and into what |
| `silence_profile` | what their not-speaking is like |

**assertiveness — circle one** (the engine's own sentences, `src/engine/identity_view.py:88-91`):

( ) you leave the space for someone else to fill
( ) you say your piece once and let it stand
( ) you press a point until it is answered
( ) you take the room and hold it

**Worked example (Tam, the whole block):**

```json
"voice": {
  "register": {
    "formality": "plain valley speech, no schooling past the parish",
    "ornament": "spare — he says the smallest true thing and stops"
  },
  "rhythm": "hesitant at the start of a sentence, steady once he is describing work",
  "assertiveness": 0.22,
  "tics": ["agrees before he has decided",
           "describes the task instead of answering the question",
           "apologises for taking up room"],
  "code_switch": [
    {"context": "anyone raising their voice",
     "shift": "goes quiet and agrees, regardless of what he thinks"},
    {"context": "the mill, the race, the wheel",
     "shift": "fluent and exact — the one place he speaks without hedging"}
  ],
  "silence_profile": "high, and anxious — he fills a pause only to end it"
}
```

**Worked example (Nell, for contrast):** *"blunt valley speech, no softening" · "plain, and warmer
than the words look on the page" · "unhurried; she lets a silence sit until the other person fills
it" · tics: "asks for the thing directly, once", "says the hard fact and then waits", "uses a
person's name when she wants them to hear it" · silence: "comfortable — she can outwait anyone and
knows it".*

Read those two side by side. That is the whole point of the field: if two principals' voice blocks
could be swapped without anyone noticing, you have one character written twice.

>> **HOW THIS IS USED:** the whole block is copied into the actor's identity prefix
>> (`src/engine/scene.py:231`) and passes through the words-only layer untouched because it is all
>> strings (`src/engine/identity_view.py:196-198`) — except `assertiveness`, which is a number and
>> is replaced by the sentence you circled (`src/engine/identity_view.py:88-91`, applied at `:191`).

**IF YOU LEAVE IT BLANK:** the actor speaks in a competent house voice, and so does everyone else in
your book. The pre-run check warns the block is thin (`scripts/lint_book.py:255-257`).

**Common mistake — and there is a check for it.** Do not write a number into any of the prose
fields. `"rhythm": "clipped 0.3, rolling 0.7"` will reach the actor exactly like that, as a raw
statistic, because the engine will not rewrite your prose. The pre-run check scans every authored
string in the identity prefix for decimals and warns, telling you to move the calibration into a
`note` key or say it in words (`scripts/lint_book.py:151-159`).

**A word about `vocab_domains`.** The voice design doc lists it (`docs/voice.md:8-16`) and neither
worked example uses it. It is not parsed by anything, but the whole block passes through verbatim —
so if you write it, the actor reads it. Treat it as free prose, like everything else here.

---

# PART NINE — WHAT THEY CAN DO

## 9.1 — Skills

**Key path:** `baseline.skills` — `{name: 0-to-1}`

**REQUIRED — but only three names do anything.**

**Three skills gate real machinery, and the rest are honest context.**

| skill | what it gates |
|---|---|
| `perception` | whether they notice the subtle things in a scene at all |
| `insight` | whether they can recognise a **stranger** by sight |
| `combat` | whether they are capable of a threat or a harm that lands |

**YOUR JOB.** Three questions, in words:

```
Do they notice what other people miss?   ( ) no  ( ) about average  ( ) yes, they always have
Do they read strangers well?             ( ) no  ( ) about average  ( ) yes
Could they hurt someone if it came to it? ( ) no ( ) at a push  ( ) yes
```

Then list any other skills that describe them — `millwright`, `shepherding`, `fell_lore` — because
the actor reads them and plays them, even though nothing computes from them.

**Worked example (Tam):** `{"perception": 0.62, "insight": 0.55, "combat": 0.15, "millwright": 0.8,
"ice_work": 0.75}` — he notices, he just about reads people, he could not fight, and he is very good
with a wheel.
**Worked example (Nell):** `{"perception": 0.78, "insight": 0.7, "combat": 0.35,
"shepherding": 0.88, "fell_lore": 0.82}`.

>> **HOW THIS IS USED:** `perception` decides whether the subtle details of an event reach this
>> character at all — below the bar and they are simply absent from what the character apprehends
>> (`src/engine/gate.py:42` and `src/engine/gate.py:147-152`). `insight` decides whether a person in
>> the room is recognised as *someone* or stays *"person present"*
>> (`src/engine/gate.py:41` and `src/engine/gate.py:196-219`). `combat` is checked when the character
>> claims to have threatened or harmed someone, and a claim below the bar is flagged as beyond their
>> capability (`src/engine/consolidation.py:531-539`, with the two bars at
>> `src/engine/consolidation.py:168` and `:189`).

**The mercy in the recognition rule, and it matters for your cast.** A character recognises anyone
they have a relationship with **regardless of insight** — the check is only for strangers
(`src/engine/gate.py:201`). So a low-insight character is not blind to their own family. It just
means new people arrive as shapes.

**LEAVE BLANK — nothing computes from them.** Every other skill name you write. They ride the
identity prefix as context and reach the actor as words; no code reads them. Write the two or three
that say who this person is and stop.

**IF YOU LEAVE THE WHOLE BLOCK BLANK:** every skill is treated as exactly average, which means the
character misses subtle cues (average sits below the bar for noticing) but does recognise most
strangers. The pre-run check warns the block is thin (`scripts/lint_book.py:255-257`).

---

## 9.2 — How strong they are

**Key path:** `baseline.body.strength` — one word.

**ONLY IF YOUR BOOK RUNS `body` (Part Zero); then REQUIRED.** A book that does not run it leaves this
blank, and the pre-run check warns if it is written anyway.

**What it is.** How long this body keeps going. When the book runs `body`, the reader of each beat
names how physically hard the act was — the same word for anyone who did it — and the engine weighs
that against this word: the same hour of hauling spends a frail body about three times as fast as a
powerful one. It also weighs the ordinary tiredness of a waking day. It is not a skill (a skill is
competence at a craft) and it is not a number you write (`src/engine/body.py`).

**YOUR JOB — one circle.** *Set beside an ordinary adult of their world, how long does this body keep going?*

( ) frail — it gives out long before anyone else's
( ) slight — it tires sooner than most
( ) ordinary
( ) strong — it outlasts most
( ) powerful — it outlasts almost everyone

**Worked example.** Tam, a quay porter of fifty: `{"strength": "strong"}`.

**What moves it.** In a book that also runs `injuries` (Part Zero), a hurt not yet healed makes this
body count one word lower for a serious injury and two for a grave one - the worst of them governing -
until it heals; a minor one does nothing, and a healed one (a grave one's mark too) nothing (gate
injury-weakens). Effort and waking time cost the body more meanwhile. Age and training do not move it
yet. `fixed.physical`, if you write one, stays prose for the actor; this word is what the engine reads.

---

# PART TEN — WHO THEY KNOW

This is the part most often half-finished, and a half-finished version is invisible rather than
wrong. Read the whole section before you fill any of it in.

---

## 10.1 — One entry per person they know

**Key path:** `current.relationships.<their id>` — a dictionary keyed by the *other person's id*

**REQUIRED for anyone who will share a scene with anyone.**

**What it is.** What this character makes of that character. It is a *belief*, not a fact — it can
be wrong, and it is one-directional. **A relationship you write on Tam's sheet gives Tam a stance
toward Nell and gives Nell nothing.** You must write both sides, on both sheets, keyed to the same
ids.

**The key must be the other person's id exactly** — the same word that appears in the world note's
cast list. A misspelled key fails in complete silence: the edge is simply never found.

**YOUR JOB — for each person they know, four circles and two sentences.**

```
THEY KNOW: ____________________   (their id: ______________ )

TRUST — (circle one)
  ( ) I check what they tell me against something else before I act on it
  ( ) I act on their word for small things and verify the large ones
  ( ) I act on their word without checking it
  ( ) I would act on their word against my own read of the room

AFFINITY — (circle one)
  ( ) I keep it to the business and leave when the business is done
  ( ) I am civil, and I do not seek them out
  ( ) I make time for them and take their side by default
  ( ) I would put myself out for them before they thought to ask

RESPECT — (circle one)
  ( ) I do not weight their opinion when I decide
  ( ) I hear them out and then decide for myself
  ( ) I weigh their judgment against my own and sometimes it wins
  ( ) where I am unsure, I do what they would do

DEBT — (circle one)
  ( ) I owe them nothing, and I act like it
  ( ) I would do them a small favour unasked
  ( ) I say yes when they ask and do not count it
  ( ) what they ask of me, I do

WHAT I CALL THEM (known_as): _______________________________

WHAT IS BETWEEN US (history) — a sentence or two, for you and not for the machine:
_________________________________________________________________________
```

*(All sixteen sentences are the engine's own — `src/engine/direction.py:134-151`. Circle one per
axis; the sizer converts. The four axis names are fixed at `src/engine/records.py:137`.)*

**Worked example (Tam's edge toward Nell):**

```json
"nell": {
  "trust": 0.62, "affinity": 0.45, "respect": 0.7, "debt": 0.2,
  "known_as": "Nell",
  "history": "she has asked him up to the fold three times this winter and he has found a reason
              not to go three times. She has never once made him say why."
}
```

**And Nell's edge back toward Tam** — note that it is *not* a mirror image; that asymmetry is the
whole point:

```json
"tam": {
  "trust": 0.7, "affinity": 0.66, "respect": 0.55, "debt": 0.0,
  "known_as": "Tam",
  "history": "she has watched him break the race open at first light in weather that would stop
              most men, and she has watched him find a reason not to come up the hill three times.
              She does not think those are two different men."
}
```

>> **HOW THIS IS USED:** for every person actually present in a scene *and* carrying a relationship
>> record, the engine builds an edge (`src/engine/scene.py:315-377`) and the four axes are turned
>> into the sentences you circled (the band-phrase renderer, RETIRED 2026-09-08), which appear in the prompt
>> under *"Those present, as you stand with them"* (`src/engine/prompt.py:57`).

**IF YOU LEAVE IT BLANK:** the engine sees two strangers, and the actor re-invents the entire
relationship from prose every single turn — differently each time. The pre-run check warns when
`relationships` is absent entirely (`scripts/lint_book.py:193-195`).

**IF YOU MISSPELL THE KEY:** the check compares every relationship key against the world note's cast
ids and tells you which one does not match, saying the edge will never surface
(`scripts/lint_book.py:162-164`).

**IF YOU ONLY WRITE ONE SIDE:** the check names it as one-way and tells you exactly which character
gets no edge for which other character in any scene they share (`scripts/lint_book.py:112-121`).

**An axis you leave out is left out, not zeroed.** If you circle nothing for `debt`, omit the key —
the engine emits the edge without it and simply says nothing about debt
(`src/engine/scene.py:371-373`). Do not write `null`; that fails loudly at render time
(the band-phrase renderer, RETIRED 2026-09-08).

**LEAVE ALONE — the engine writes this one.** `their_view` (what this character thinks the *other*
one makes of *them*) accretes during the run as people act toward each other
(`src/engine/bonds.py:350-355`). Do not author it.

**A note on `history`.** It is carried into the packet (`src/engine/scene.py:352`) and no consumer
renders it — the prompt's "Those present" line uses only the label and the four axes
(`src/engine/prompt.py:57`), and the only other readers of the edges use it to work out who a scene
is about. **So `history` does not reach the actor.** Write it anyway, briefly: it is the best place
to record why the four circles are where they are, and both real characters use it exactly that way.

---

## 10.2 — `known_as`: the person known only by a description

**Key path:** `current.relationships.<id>.known_as`

**OPTIONAL, and one of the most useful things on the whole sheet.**

**What it is.** The term *this character* uses for that person. Three ways to use it:

1. **They know the name.** Write the name — `"known_as": "Nell"` — or leave the key out entirely.
   Both mean the same thing. **Knowing names is the default.**
2. **They do not know the name.** Write the description they would use instead:
   `"known_as": "the man with the dogs"`.
3. **They use a nickname or a title.** Write that. `"known_as": "the harbourmaster"`.

**What happens in case 2 — and this is the mechanic worth understanding.** The engine takes the
first part of that person's id — `faron` from the key `faron` — and **erases it from the entire
prompt**, replacing every occurrence with your description. Not just from the relationship line: the
identity block, the voice, the recalled beliefs, the moment itself, all of it
(`src/engine/gate.py:427-449`, applied across both halves of the prompt at
`src/engine/prompt.py:122-127`). The actor is never shown a name its character never learned.

**Worked example (Tam's second edge, which exists precisely to exercise this):**

```json
"faron": {
  "trust": 0.3, "affinity": 0.25, "respect": 0.4, "debt": 0.0,
  "known_as": "the man with the dogs",
  "history": "a drover wintering over in the hall. Tam has not spoken to him and does not know
              his name — he thinks of him as the man with the dogs."
}
```

In every scene those two share, Tam's actor is told about *"the man with the dogs"*. The word
"Faron" does not appear in anything Tam is shown.

**Three things that follow, and you should know all three:**

- **The masking keys off the id.** It masks the id's first segment (`src/engine/gate.py:440-441`). If
  the person's id is `the_drover` and their name is Faron, the mask replaces *"the"* and does
  nothing useful. **Give people ids that are their first names** and this works exactly as you
  expect.
- **If the actor emits the name anyway, that is caught.** There is a separate check that reads the
  actor's *output* and flags any masked name that appears in it — it means the name came from the
  model's own training rather than from anything the engine showed it
  (`src/engine/faithfulness.py:15-34`).
- **The reveal is a real story beat.** When a character finally learns someone's name, the engine
  flips `known_as` to the name and adds a belief recording that they learned it — and deliberately
  does **not** rewrite their older memories, which keep the framing they had at the time
  (`src/engine/acquisition.py:60-87`). *"The one I knew as 'the man with the dogs' is named Faron."*
  You do not author that. You set up the ignorance; the story pays it off.

>> **HOW THIS IS USED:** as the actor's own label for that person on the "Those present" line
>> (`src/engine/scene.py:351`), and as the mask applied across the whole prompt
>> (`src/engine/gate.py:427-449`, `src/engine/prompt.py:126-127`).

**IF YOU LEAVE IT BLANK:** the character knows the name — which is the right default and is almost
always what you want. **You author ignorance; you never blanket-hide.**

---

## 10.3 — What they assume about a stranger

**Key path:** `baseline.relationship_priors` — in practice, `{"default_trust": 0-to-1}`

**OPTIONAL.**

**What it is.** Where a bond the sheet did NOT author settles when nobody is reinforcing it — the
trust this person extends to a stranger, and the level an edge that grew from nothing relaxes toward
across a gap in the story. **An edge you author in 10.2 rests where you wrote it** (the engine seeds
that rest at run creation, and only a cliff — an unforgivable act — lowers it), so a devoted friendship
does not decay into a stranger's over a winter (`docs/bond-arithmetic.md` s6).

**YOUR JOB.** One sentence: *"Left alone for a season, does this person drift back toward trusting
people or away from it?"* — for the people they had no history with.

**Worked example.** Tam: `{"default_trust": 0.55}`. Nell: `{"default_trust": 0.62}`.

**Optional, beside it:** `"update": {"grant_threshold": "low|moderate|high", "withdraw_speed":
"slow|typical|fast"}` — how readily this person lets someone in, and lets them go. A high threshold
is a slow grant; a fast withdrawer leans hard on a bad act. Left out, the engine's defaults apply;
a word off those six is refused at the seam.

>> **HOW THIS IS USED:** when a scene declares that time has passed, every edge on every character
>> relaxes toward its own rest before the scene starts (`scripts/scene.py`, using
>> `src/engine/bond_rest.py`): an authored edge toward where it was authored, an unauthored one
>> toward this prior. `update` sets the rates the bond law moves this person's edges at
>> (`src/engine/bonds.py` `rates_of`).

**IF YOU LEAVE IT BLANK:** unauthored relationships drift toward the engine's own default rather
than this person's. Harmless for a short book; visible across a long one.

`in_group` is RETIRED (2026-09-18): a person you would have listed there belongs in `relationships`
(the edge is the hold); a group belongs below, as `grp.<tag>`.

### What they hold that is not a person — `current.attachments`

**Key path:** `current.attachments.<loc.id | grp.tag>` — `{"hold": <float>, "sign": "+", "note": "<word>: <why>"}`

A place the world registers (`loc.<world.locations id>`) or a group tag some `people[]` entry carries
(`grp.<tag>`). Say it as a RELATION WORD and let the engine price it — `life` (losing it would change
her days: her livelihood, her home, her life's work; the backstory must SHOW the dependence), `post`
(her position, crew, parish, ship — hers while she keeps it), `member` (belongs, attends, native of),
`acquainted` (knows it, passes through). At most two `life` holds. Or leave the block empty and run
`python scripts/composition_pass.py --attach-classify <backstory> --world <book>`, which asks a
classifier for the words with the backstory sentence that shows each.

>> **HOW THIS IS USED:** an act on her held place is done TO her (`bonds.act_from_tags`, `stake_of` —
>> `bond-arithmetic.md` s3/s5), and the same number scales what she feels about an event there
>> (`connection.held_map`). It is seeded as an append-only row at run creation and moves only by a
>> director's declaration in a scene cfg (`attachments: [{char, entity, relation}]`).

**IF YOU LEAVE IT BLANK:** nothing but a person can move this character's bonds — a scene about her
home or her post reads, to the arithmetic, as a scene about nobody's.

---

# PART ELEVEN — WHERE THEY ARE AND HOW THEY ARE, RIGHT NOW

Everything in this part is **turn-zero state**, not a character summary. It describes the character
at the exact moment the book opens, and it moves as the book moves.

---

## 11.1 — Where they are standing

**Key path:** `current.location`

**REQUIRED.**

**What it is.** The id of the place they are in when the book opens. **It must be an id that
actually exists in the world note's list of locations** — not a description, an id.

**Worked example.** Both Tam and Nell open at `"location": "mill"`.

>> **HOW THIS IS USED:** it becomes the location the character perceives — the engine looks the id up
>> in the world's locations and adds what it finds to what the character apprehends
>> (`src/engine/gate.py:220-229`).

**IF YOU LEAVE IT BLANK, OR NAME A PLACE THE WORLD DOES NOT HAVE:** no location reaches the character
at all — they act in an unspecified void. The pre-run check names your value and says no location
percept will be produced there (`scripts/lint_book.py:251-254`).

**Common mistake.** Writing `"location": "the mill on the beck"`. That is a description; the world
note calls it `mill`. Ask whoever wrote the world note for the id list.

---

## 11.2 — How worn out they are

**Key path:** `current.condition` — two live keys: `energy` and `allostatic_load`

**REQUIRED — the block must exist, unless your book switches `condition` off (Part Zero); then
skip this section.**

**What it is.** Two dials describing how much this person has left in them. `energy` is how much
they have; `allostatic_load` is how much wear they are carrying. Together they set both how much the
actor is told they can manage, and — this is the interesting part — **how much they can remember**.

**YOUR JOB — one circle.** *How much has this person got left, on page one?*

( ) they take the shortest path and will not do the thorough version of anything
( ) they do what is asked and none of the extra
( ) they can do the thorough version where it matters
( ) they have reserve to spend on more than is asked

*(Those four are the engine's own sentences — `src/engine/direction.py:17-20`.)*

**Worked example.** Tam: `{"energy": 0.58, "allostatic_load": 0.35}` — *he can do the thorough
version where it matters*, and only just.

>> **HOW THIS IS USED:** two things. (1) It becomes the second half of the actor's stage directions
>> for the beat, as one of the four sentences above (the band-phrase renderer, RETIRED 2026-09-08; used at
>> `src/engine/prompt.py:51-54`). (2) It sets the **memory budget** — the engine spends a budget
>> derived from energy and load when deciding which of the character's beliefs surface, and when the
>> budget runs out the remaining ones simply do not fire (`src/engine/gate.py:47-56`, spent at
>> `src/engine/gate.py:367-373`).

**This is a director's lever, and it is sanctioned.** Draining a character's energy makes them
*miss what they know*. A tired character genuinely fails to recall the thing that would have saved
them. That is not a bug; it is the one control you have over a character's cognition.

**IF YOU LEAVE IT BLANK:** the pre-run check errors — the block must at minimum be a dictionary
(`scripts/lint_book.py:264`) — unless the book switches `condition` off. If the block exists but
both keys are missing, the actor is told nothing of energy and memory runs on the full budget —
exactly what switching the system off does. Write **both** keys or neither: with one missing, the
readers assume different values for the other, and the pre-run check warns.

**LEAVE BLANK — nothing reads these.** `health`, `fatigue`. They appear on the real character
sheets and no code anywhere reads either of them — searched the engine and the scripts. The owner
ruled out health bars for now (2026-09-22); energy (above) is the book's fatigue.

**`injuries` — ONLY IF YOUR BOOK RUNS `injuries` (Part Zero).** The hurts this character carries on
page one: a list, usually empty, of `{"what": "<in your words>", "severity": "minor | serious | grave",
"ago": "<optional: how long before page one, e.g. 12h or 5d>"}`. Leave `ago` out for something long
healed - then only a grave one still shows, as the mark it left. The character is told their own; no
one else notices an old injury they did not see happen (not built). Hurts taken during the story come
from the reader of each beat, not from you (`src/engine/injuries.py`). A book that does not run the
system leaves the list empty: nothing reads it then.

**LEAVE BLANK — nothing reads this either.** `current.zone` (the "psych zone" from the schema
document). No code reads it.

**What moves it after page one (gate condition-flow, 2026-09-22).** Only what your book switches on.
With `condition_flow` off — every book's default — nothing writes `condition.energy` after the
character is created, and a scene can still state how someone arrives (BLUEPRINT-scene 6c), which
then holds. With `condition_flow` on, the engine carries it: every beat costs its minutes, the one
who acted also pays for what the beat did to them, fear, anger and grief running high build the load
slowly, and between scenes the standard day holds — night hours are sleep, day hours awake, counted from each
character's own last scene, unless the next scene's file says otherwise (BLUEPRINT-scene 6c) — so
`docs/relevancy-gate.md:106`'s *"regenerates with rest"* becomes true for that book (`src/engine/condition.py`). A book that also runs `body` splits
the energy three ways (the owner's ruling: one source, with reserves for each - *"a person can never use all
energy for one type of activity"*): a shared pool, a reserve for the mind and one for the body. Thinking and
feeling spend the shared pool and then the mind's reserve, never the body's; physical effort the shared pool
and then the body's reserve, never the mind's. Memory reads the mind's side, and the actor is told both sides
when they differ ("...; your body is spent, and every movement costs you"). You still write one `energy`.

---

## 11.3 — What they are trying to do in the opening scene

**Key path:** `current.active_goals` — a list of `{"goal": "...", "urgency": ...}`

**REQUIRED — but read the note about scenes before you agonise over it.**

**What it is.** The one or two things pressing on them *right now*, in this scene — as distinct from
the standing goals of their life you wrote in Part Four. "Keep the mill running" is a life goal;
"get the race broken open before the wheel seizes" is what he is doing this morning.

**THE KEY IS `goal`.** As in Part Four, and here it is not merely a convention — it is read.

**YOUR JOB.**

```

> **The sentence is chosen off `energy × (1 − allostatic_load ÷ 2)`, not off energy alone**
> (`src/engine/direction.py` `direct_condition`). So `energy 0.58` with `allostatic_load 0.35`
> gives 0.478 and renders *"you do what is asked and none of the extra"* — the band BELOW the one
> the words suggest. To land "the thorough version where it matters" at that load, write
> **energy 0.70**. No sizer can hit the band without knowing the load is in the formula.

In the opening scene they are trying to: ____________________________________

How badly?  (circle one)
  ( ) it is in the back of my mind
  ( ) it is something I mean to get to
  ( ) it is pressing on me
  ( ) it is the thing I would drop everything for
```

*(The engine's own four — `src/engine/identity_view.py:63-64`.)*

**Worked example (Tam):** `[{"goal": "get the race broken open before the wheel seizes",
"urgency": 0.75}]` — *pressing on me.*
**Worked example (Nell):** `[{"goal": "get another pair of hands to the fold before dark",
"urgency": 0.8}]`.

>> **HOW THIS IS USED:** two things. (1) It is shown to the actor as the "Active goals" line, with
>> the urgency replaced by one of the four sentences (`src/engine/identity_view.py:269-274`, printed
>> at `src/engine/prompt.py:62-63`). (2) It decides **which memories win**: a belief whose words
>> overlap an active goal's words is ranked ahead of one that does not, and gets the memory budget
>> first (`src/engine/gate.py:335-348`, sorted at `src/engine/gate.py:363-365`).

### The thing you must know about goals and scenes

**In a multi-character scene, whatever you write here is thrown away and replaced.** The scene's own
configuration file gives each cast member a `drive` for that scene, and the runner overwrites the
sheet's `active_goals` with it before anything else happens
(`scripts/scene.py:286` — the line even says so: *"the scene DRIVE overrides sheet goals"*).

**In a single-character run, what you write here is exactly what is used.** The single-character
driver never touches the field; it builds the packet straight from the sheet
(`scripts/direct.py:292`).

So: fill it in truthfully for the opening moment. It is live for solo runs, it is the thing the
pre-run check asserts on (`scripts/lint_book.py:249-250`), and in a cast scene it is a sensible
default that the scene writer will replace.

**Common mistake.** Writing the character's *life* goal here and their *scene* goal in
`baseline.drives.goals`. It is the other way round.

**IF YOU LEAVE IT BLANK:** nothing weights which memories surface, so recall becomes confidence-order
only. The check warns in exactly those terms (`scripts/lint_book.py:249-250`).

---

# PART TWELVE — WHAT THEY BELIEVE

## 12.1 — The `## Beliefs` section

**Where it goes:** in the markdown, **below** the json block, under a heading `## Beliefs`.

**REQUIRED for principals and supporting characters. A background extra has none.**

This is the character's memory, and it is the most mechanically strict thing in this document.
**Every bullet must match this exact shape:**

```
- (confidence, provenance) the claim itself [[Optional Link]] [[Another]]
```

- Opens with `- ` or `* `.
- Then a bracket containing **a number, a comma, and a source**, in that order.
- Then the claim, in plain prose.
- Then optionally one or more `[[double-bracket links]]`.

**A bullet that does not match this shape loads as nothing.** Not partly — nothing.

**The claim is written in the first person, as the character would put it to themselves.**

**YOUR JOB, per belief — three boxes:**

```
HOW SURE ARE THEY?  (circle one)
  ( ) they would not stake anything on it
  ( ) they act on it, but they would hear an argument
  ( ) they act on it without re-examining it
  ( ) they do not entertain the alternative

WHERE DID IT COME FROM? — a short phrase, in their voice, not a category:
  _____________________________________________________________________

THE CLAIM ITSELF:
  _____________________________________________________________________
  _____________________________________________________________________
```

*(The four sureness sentences are the engine's own — `src/engine/direction.py:153-156`.)*

**Worked example (Tam's six, in full):**

```
- (0.95, I was twenty yards behind him and I stopped) When it matters I will not go, and knowing
  that about myself has never once helped me go.
- (0.90, nobody has ever said it to me) They all know about the wall, and they are being kind, and
  the kindness is worse than saying it.
- (0.85, eleven winters of it) If the race ices the mill stops, and if the mill stops the Hollow
  goes short. That one is mine and I have never failed it.
- (0.80, three refusals this winter) Nell will ask again. She always asks again. One of these times
  I will have to say something true.
- (0.75, what everyone knows) A man who has been hurt by wolves stays hurt. Two men tried and both
  were carried back.
- (0.60, I have thought about it and not moved) If I went up there once and came back, it would be
  different afterwards. I do not know how to make myself start.
```

>> **HOW THIS IS USED:** the section is parsed line by line against a fixed pattern
>> (`src/engine/vault.py:22`) and the results become the character's memory store, replacing
>> anything in the json block (`src/engine/vault.py:150-151`). During a scene the engine pulls out
>> the words of what the character perceived and matches them against every belief's text
>> (`src/engine/gate.py:325-330`); those that match are ranked and injected into the prompt as
>> *"What it brings to mind"*, each rendered with its source and one of the four sureness sentences
>> (`src/engine/prompt.py:55`).

### Three rules that decide whether a belief ever fires

**1. Confidence is the price of remembering, not a flavour dial.** A belief costs
`1 − confidence` out of the memory budget you set in Part 11.2
(`src/engine/gate.py:322`). A belief at full confidence is free and surfaces whenever its words come
up. A belief at 0.6 costs real budget and **legitimately fails to surface when the character is
tired** — which is correct, and is the lever. So: the things that *made* this person are the top
band. Half-noticed suspicions and things they have not let themselves conclude are the second band
and will sometimes not arrive. Setting everything to "they act on it without re-examining it"
because it feels about right makes every memory equally expensive and equally faint.

**2. A belief fires because a WORD is shared.** Matching is word overlap between what the character
perceived and the belief's text (`src/engine/gate.py:325-330`). So:

| cannot ever fire | can fire |
|---|---|
| *"What happened that year changed everything."* | *"They all know about the wall."* |

The first shares words with nothing. Name the nouns your scenes will actually use — *the wall*,
*the fell road*, *the race*, *the pack*. If a belief is about conscription, the word *levy* or
*draft* must be in it.

**3. `[[Links]]` are extra doors, under your control.** A linked note's name joins the belief's
matchable surface (`src/engine/gate.py:325`), so a belief also fires when that name comes up. They
are the edges you author by hand. Use them when the natural phrasing of a claim does not contain the
word you need.

**IF YOU LEAVE THE SECTION OUT:** the character recalls nothing, ever. The pre-run check warns in
exactly those words and reminds you of the required bullet shape
(`scripts/lint_book.py:189-192`).

**IF YOU WRITE BULLETS THAT DO NOT MATCH THE SHAPE:** the book refuses to load, names your file,
counts your bullets, and tells you they would have loaded as zero beliefs —
`[VAULT_BELIEFS_SECTION_UNPARSED]` (`src/engine/vault.py:98-103`). That refusal is deliberate:
dropping is worse than failing. It exists because 41 of 77 beliefs across five notes once vanished
in silence.

**IF YOU WRITE A CONFIDENCE OUTSIDE THE SCALE:** the book refuses to load and names the value —
`[VAULT_BELIEF_CONFIDENCE_RANGE]` (`src/engine/vault.py:90-92`).

**Provenance is prose, not a category.** The pre-run check's message suggests
`seed/authored/lived/witnessed/learned` (`scripts/lint_book.py:261-262`), but nothing validates it,
and it is shown to the actor verbatim (`src/engine/prompt.py:55`). *"nobody has ever said it to
me"* is far better than *"lived"*. Write the sentence.

---

## 12.2 — Where their baseline came from

**Key path:** `baseline.provenance`

**OPTIONAL.**

**What it is.** A free-form note recording *why* this person's baseline is what it is — the docks,
the seminary, the war. Unlike a `note` key, this one is **not** stripped; it reaches the actor.

>> **HOW THIS IS USED:** it is copied into the identity prefix (`src/engine/scene.py:232`) and passes
>> through the words-only layer untouched because it is strings
>> (`src/engine/identity_view.py:196-198`).

**IF YOU LEAVE IT BLANK:** nothing happens. Use it, or use `note` keys inside the blocks themselves
— the difference is that a `note` is for you and this is for the actor.

---

# PART THIRTEEN — THE FOUR THINGS THAT ARE NOT ON THIS SHEET

**A character sheet on its own is not a character in a scene.** The engine joins everything by exact
ids and never infers a connection. For your new person to be *perceived* by anybody, four separate
things must all be true, in three different files:

| # | what | where | if it is missing |
|---|---|---|---|
| 1 | an entry `{id, what}` in the world's cast list | the world note | nobody can perceive them at all |
| 2 | their **first name appears in the scene's event text** | the scene config | same — presence must be evidenced by the text |
| 3 | the other character can recognise them | the other character's `insight`, or a relationship | they are seen as *"person present"*, not as this person |
| 4 | a relationship record on **each** side, keyed to the same ids | both character sheets | the person is in the room and nobody has a stance toward them |

**The easy mistake, and it is very easy:** author this sheet beautifully, put them in the scene, and
stop. You now have a complete, playable character who is **invisible** to the person they are
talking to.

**The checks that catch it.** The pre-run check warns when a character is not in the world's cast
list, saying no other character can perceive them and giving you the entry to add
(`scripts/lint_book.py:108-111`); and it warns on every one-way relationship
(`scripts/lint_book.py:112-121`).

**Hand the world's author this list when you finish:**

```
This character's id: ____________
Their one-line "what" for the world cast list: ____________________________
Groups they belong to (for regard):  ______________________________________
Locations they occupy: ____________________________________________________
Their first name, as a keyword for the world lexicon: ______________________
Everyone who knows them (so the reciprocal edges get written): _____________
```

---

# PART FOURTEEN — CHECK IT BEFORE YOU RUN IT

One command reads every character and every world note and prints what is wrong:

```
python scripts/lint_book.py --vault "<the book folder>"
```

Errors would break a run. Warnings mean something you authored is switched off. **A run with
warnings is not clean** — the tool says so itself (`scripts/lint_book.py:307-309`).

**The messages you are most likely to see, and what each means for you:**

| the message says | what to do |
|---|---|
| `genotype uses the retired axes [...]. It is now one {hit, hold} cell per path` | Part 2.1. Your sheet still has `threat_reactivity`/`approach_drive`/etc. Rewrite the block by hand — nothing translates it. This is an error, not a warning (`GENOTYPE_OLD_AXES`). |
| `genotype.<PATH>.rest — where they rest is a DESIGN choice now, not a genotype cell` | Part 2.1. Your sheet still has a `rest` inside a genotype cell. Move the word to `baseline.temperament.<PATH>.rest`, Part 3.1. This is an error, not a warning (`GENOTYPE_REST_MOVED`). |
| `genotype.<PATH>.<cell> starts '<your text>', which is not a <cell> word` | Part 2.1. Put the vocabulary word for that cell (`hit`/`hold`: their own four words) FIRST. This is an error, not a warning. |
| `baseline.temperament.<PATH>.rest starts '<your text>', which is not a rest word` | Part 3.1. Put `quiet`/`low`/`raised`/`high` FIRST. This is an error, not a warning. |
| `baseline.temperament.<PATH>.rest sits at rung N (...) — above the cap` | Part 3.1. You authored a rest — word or number — above that path's cap. Honoured as written — this warning is only the receipt. Deliberate, or fix it. |
| `baseline.temperament.<PATH>.mean disagrees with rest` | Part 3.1. The mean is seeded from the rest word once; delete the hand-written mean to re-seed it, or move the rest word to match. |
| `current.vault is EMPTY` | Part 12. Your Beliefs bullets did not match the shape, or there is no section. |
| `fixed.position is EMPTY` | Part 1.5. The actor has no place, class or station. |
| `a formative block is authored ... read by NO engine code` | Part 1.5. Move it into `fixed.position`. |
| `relationship 'x' is not a world.people id` | Part 10.1. Fix the spelling, or the world note is missing them. |
| `baseline.drives.fears_wounds is not read since 2026-09-11` | Part 5.1. A wound is engine state at `baseline.wounds` now. Move each wound to a profile pick, or write it as `{concept, path, intensity, source, text, trigger}` under `baseline.wounds` — you should not need to; that block is minted, not authored. This is an error, not a warning. |
| `baseline.wounds[N] source '...' must be profile:<id> or run:<turn>` | Part 5.1. A wound is minted, never hand-written — this fires if a `baseline.wounds` entry's `source` carries anything else. This is an error, not a warning. |
| `baseline.catalog row N names wound '...', which baseline.wounds does not carry` | Part 5.1/5.2. A dampener row named a wound id that no longer exists on the sheet — it would fire at full magnitude regardless. Fix the id, or the profile pick that should have minted it. |
| `carries 0.35 in AUTHORED TEXT` | Part 8.1. You wrote a number inside a sentence the actor reads. Say it in words. |

---

# PART FIFTEEN — A COMPLETE FILLED EXAMPLE

This is a real, working character note, whole, from a real book — frontmatter, prose, sheet and
beliefs. Everything this form asks for is somewhere in it.

````
---
type: character
id: nell
---

# Nell Harrow

Forty, shepherd, four ewes lost to the pack since the first frost. She walks the fold at night
alone with a lamp and a bill-hook because there is nobody else to do it and she has stopped
expecting there to be. Blunt, warm, and entirely without pity — she asks people for things
directly and does not hold it against them when they say no, which is exactly why being asked by
her is so hard to bear.

```json
{
  "fixed": {
    "id": "nell",
    "name": "Nell Harrow",
    "people": "human",
    "position": {
      "place": "Beck Hollow — came down from a fell farm at nineteen and has kept sheep here since",
      "class": "working freehold, land-poor and stock-rich; her wealth walks around on the low
                pasture and can be eaten in a night",
      "era": "the third early winter. She is the only person in the Hollow who has actually seen
              the pack up close, twice, and the only one who talks about them as animals rather
              than as a judgement",
      "niche": "shepherd. Walks the fold after dark alone, lambs in the cold, and has buried four
                ewes this winter. Knows the fell road better than anyone alive in the valley"
    },
    "genotype": {
      "STIRRING":    {"hit": "elevated", "hold": "typical"},
      "WARINESS":    {"hit": "typical",  "hold": "brief"},
      "DISPLEASURE": {"hit": "typical",  "hold": "brief"},
      "GOODWILL":    {"hit": "high (practical rather than tender — care as work done)", "hold": "long"},
      "DEFLATION":   {"hit": "high",     "hold": "typical"},
      "DISTASTE":    {"hit": "typical",  "hold": "typical"},
      "RECEPTIVITY": {"hit": "typical",  "hold": "typical"},
      "SELF-REGARD": {"hit": "typical",  "hold": "typical"}
    }
  },
  "baseline": {
    "temperament": {
      "STIRRING":    {"rest": "low",    "mean": 0.13},
      "WARINESS":    {"rest": "low",    "mean": 0.105},
      "DISPLEASURE": {"rest": "quiet",  "mean": 0.035},
      "GOODWILL":    {"rest": "raised", "mean": 0.225},
      "DEFLATION":   {"rest": "quiet",  "mean": 0.04},
      "DISTASTE":    {"rest": "quiet",  "mean": 0.075},
      "RECEPTIVITY": {"rest": "low",    "mean": 0.125},
      "SELF-REGARD": {"rest": "low",    "mean": 0.16}
    },
    "traits": {
      "emotionality": {"mean": 0.44}, "agreeableness": {"mean": 0.62},
      "extraversion": {"mean": 0.58}, "conscientiousness": {"mean": 0.80},
      "openness": {"mean": 0.48}, "honesty_humility": {"mean": 0.78}
    },
    "model": {
      "schwartz": {"benevolence": 0.84, "security": 0.60, "self_direction": 0.66,
                   "universalism": 0.58, "achievement": 0.40, "conformity": 0.34,
                   "tradition": 0.44, "stimulation": 0.32, "power": 0.16, "hedonism": 0.28},
      "moral_foundations": {"care_harm": 0.82, "fairness": 0.70, "loyalty": 0.66,
                            "authority": 0.36, "sanctity": 0.30},
      "needs": {"competence": 0.70, "relatedness": 0.66, "autonomy": 0.62},
      "regard": {"hollow": 0.78}
    },
    "drives": {
      "goals": [
        {"goal": "keep the fold whole through to the thaw", "priority": 0.88,
         "satisfaction": 0.30},
        {"goal": "stop being the only one who walks up there after dark", "priority": 0.70,
         "satisfaction": 0.15},
        {"goal": "get Tam Rill onto the hill once, on any pretext", "priority": 0.55,
         "satisfaction": 0.05,
         "note": "she thinks he would be all right afterwards. She has not told him that"}
      ],
      "orientation": {"locus": "internal", "agency": "high",
                      "coping_engagement": "approach", "coping_expression": "practical"}
    },
    "skills": {"perception": 0.78, "insight": 0.70, "combat": 0.35,
               "shepherding": 0.88, "fell_lore": 0.82},
    "relationship_priors": {"default_trust": 0.62},
    "voice": {
      "register": {"formality": "blunt valley speech, no softening",
                   "ornament": "plain, and warmer than the words look on the page"},
      "rhythm": "unhurried; she lets a silence sit until the other person fills it",
      "assertiveness": 0.78,
      "tics": ["asks for the thing directly, once", "says the hard fact and then waits",
               "uses a person's name when she wants them to hear it",
               "goes straight at a bad job and gets it over with",
               "does not describe the details afterwards"],
      "code_switch": [{"context": "someone frightened",
                       "shift": "slower and more concrete — she describes the next small task
                                 rather than reassuring"}],
      "silence_profile": "comfortable — she can outwait anyone and knows it"
    },
    "wounds": [
      {"id": "helplessness@WARINESS", "concept": "helplessness", "path": "WARINESS",
       "intensity": 0.70, "source": "profile:fixture-third-ewe",
       "text": "she found the third ewe still alive and had to finish it herself with the
                bill-hook, alone, in the dark",
       "trigger": ["a sheep in distress", "blood on snow", "being the only one there"]}
    ]
  },
  "current": {
    "affect": {"SEEKING": 0.55, "FEAR": 0.36, "RAGE": 0.28, "LUST": 0.30,
               "CARE": 0.72, "PANIC_GRIEF": 0.42, "PLAY": 0.30, "DISGUST": 0.24},
    "condition": {"energy": 0.62, "allostatic_load": 0.40},
    "location": "mill",
    "active_goals": [{"goal": "get another pair of hands to the fold before dark",
                      "urgency": 0.80}],
    "relationships": {
      "tam": {"trust": 0.70, "affinity": 0.66, "respect": 0.55, "debt": 0.0,
              "known_as": "Tam",
              "history": "she has watched him break the race open at first light in weather that
                          would stop most men, and she has watched him find a reason not to come
                          up the hill three times. She does not think those are two different men."}
    }
  }
}
```

## Beliefs

- (0.95, twice, close enough to smell them) They are animals. They are hungry and they are clever
  and they are not a judgement on anybody.
- (0.90, four ewes since the first frost) The pack is working down, not passing through. It will
  not stop on its own.
- (0.90, I have done it since the first frost) Nobody else walks the fold after dark. If I stop,
  it stops.
- (0.85, eleven winters of watching him) Tam Rill is not a coward about work. He is out on that
  race at four in the morning in weather that would keep me in.
- (0.80, three times asked, three times refused) He will come up that hill one day, and it will
  not be because anyone shamed him into it.
- (0.70, I finished her myself and told no one the details) Doing the thing you dread does not get
  easier. You just find out you can, and then you know it.
````

*(The `wounds` block above is shown so you can see the shape — it is not yours to write; it is what
the composition pass would have minted from whichever formative profile gave Nell this scar (Part
5.1). The real note also carries a `baseline.catalog` block for the dampener/vocation rows that stay
levers — omitted here for the same reason. `baseline.temperament`, above, is authored the same way
this example authors traits and voice — see Part 3.1.)*

---

# PART SIXTEEN — THE BLANK

Copy this out and fill in the blanks. Everything marked `<...>` is yours. The three numeric blocks
say `<sizer>` where a figure goes — circle the sentence on the form and hand it over.

````
---
type: character
id: <lowercase-first-name>
---

# <Full Name>

<Prose about them. Nobody's code reads this. Write it anyway.>

```json
{
  "fixed": {
    "id": "<lowercase-first-name>",
    "name": "<Full Name>",
    "people": "<human>",
    "role_tier": "<principal | supporting | background>",
    "position": {
      "place": "<where they are from, and how far that reaches>",
      "class": "<what they are owed, what they owe, what everyone assumes>",
      "era": "<what is going on now that they cannot ignore>",
      "niche": "<what they do all day, and what they are good at>"
    },
    "genotype": {
      "STIRRING":    {"hit": "<low|typical|elevated|high> (optional note after the space)", "hold": "<brief|typical|long|lasting>"},
      "WARINESS":    {"hit": "<low|typical|elevated|high>", "hold": "<brief|typical|long|lasting>"},
      "DISPLEASURE": {"hit": "<low|typical|elevated|high>", "hold": "<brief|typical|long|lasting>"},
      "GOODWILL":    {"hit": "<low|typical|elevated|high>", "hold": "<brief|typical|long|lasting>"},
      "DEFLATION":   {"hit": "<low|typical|elevated|high>", "hold": "<brief|typical|long|lasting>"},
      "DISTASTE":    {"hit": "<low|typical|elevated|high>", "hold": "<brief|typical|long|lasting>"},
      "RECEPTIVITY": {"hit": "<low|typical|elevated|high>", "hold": "<brief|typical|long|lasting>"},
      "SELF-REGARD": {"hit": "<low|typical|elevated|high>", "hold": "<brief|typical|long|lasting>"}
    }
  },
  "baseline": {
    "temperament": {
      "STIRRING":    {"rest": "<quiet|low|raised>"},
      "WARINESS":    {"rest": "<quiet|low|raised|high>"},
      "DISPLEASURE": {"rest": "<quiet|low|raised|high>"},
      "GOODWILL":    {"rest": "<quiet|low|raised|high>"},
      "DEFLATION":   {"rest": "<quiet|low|raised|high>"},
      "DISTASTE":    {"rest": "<quiet|low>"},
      "RECEPTIVITY": {"rest": "<quiet|low|raised|high>"},
      "SELF-REGARD": {"rest": "<quiet|low|raised|high>"},
      "_note": "mean is NOT yours to write — the engine seeds it from `rest` the first time this sheet runs (Part 3.1)"
    },
    "traits": {
      "emotionality": {"mean": <sizer>}, "agreeableness": {"mean": <sizer>},
      "extraversion": {"mean": <sizer>}, "conscientiousness": {"mean": <sizer>},
      "openness": {"mean": <sizer>}, "honesty_humility": {"mean": <sizer>}
    },
    "model": {
      "schwartz":          { "<value they will not trade away>": <sizer> },
      "moral_foundations": { "<moral they will not trade away>": <sizer> },
      "needs":             { "<need that drives them>": <sizer> },
      "regard":            { "<group>": <sizer> }
    },
    "drives": {
      "goals": [
        {"goal": "<what they are trying to bring about, in their words>",
         "priority": <sizer>, "satisfaction": <sizer>,
         "note": "<for you, not for the actor — stripped before the prompt>"}
      ],
      "_wounds_note": "no `fears_wounds` blank here — a wound is never authored (Part 5.1). Pick a
                       formative profile whose library row names the concept your character needs
                       scarred, and the composition pass mints `baseline.wounds` for you.",
      "orientation": {
        "locus":             "<external | internal>",
        "agency":            "<low | moderate | high>",
        "coping_engagement": "<avoidant | approach>",
        "coping_expression": "<suppressed | practical | expressive>"
      }
    },
    "skills": {
      "perception": <sizer>, "insight": <sizer>, "combat": <sizer>,
      "<their actual trade>": <sizer>
    },
    "relationship_priors": {"default_trust": <sizer>},
    "voice": {
      "register": {"formality": "<how formal, and where that came from>",
                   "ornament":  "<plain or decorated, and what that hides>"},
      "rhythm": "<the shape of their sentences>",
      "assertiveness": <sizer>,
      "tics": ["<verbal habit>", "<verbal habit>", "<verbal habit>"],
      "code_switch": [{"context": "<when>", "shift": "<into what>"}],
      "silence_profile": "<what their not-speaking is like>"
    }
  },
  "current": {
    "affect": {
      "SEEKING": <sizer>, "FEAR": <sizer>, "RAGE": <sizer>, "LUST": <sizer>,
      "CARE": <sizer>, "PANIC_GRIEF": <sizer>, "PLAY": <sizer>, "DISGUST": <sizer>
    },
    "condition": {"energy": <sizer>, "allostatic_load": <sizer>},
    "location": "<an id from the world note's locations>",
    "active_goals": [{"goal": "<what they want in the OPENING scene>", "urgency": <sizer>}],
    "relationships": {
      "<their id>": {
        "trust": <sizer>, "affinity": <sizer>, "respect": <sizer>, "debt": <sizer>,
        "known_as": "<their name, OR the description this character uses instead>",
        "history": "<why the four circles are where they are — for you>"
      }
    }
  }
}
```

## Beliefs

- (<0-to-1>, <where it came from, in their voice>) <the claim, first person, with the nouns your
  scenes will actually use>
- (<0-to-1>, <source>) <claim>
- (<0-to-1>, <source>) <claim>
````

---

# APPENDIX — EVERYTHING YOU CAN SKIP

Every field below appears in a design document or on a real sheet, and **no code reads any of
them.** Each was checked by searching the whole engine and every script. They are listed so you
never spend an afternoon filling one in.

| field | where it comes from |
|---|---|
| `fixed.role_tier` | your own promise about fill depth — write it, but it computes nothing |
| the whole `formative` block | an author's note; use `fixed.position` instead |
| `baseline.temperament.<PATH>.mean` | seeded by the engine from `rest` the first time the sheet runs (Part 3.1) — do not author it yourself |
| `baseline.drives.goals[].kind` / `.serves` / `.status` / `.origin` / `.triggers` / `.view` | `docs/drives-schema.md:16-27` |
| every `baseline.skills` name except `perception`, `insight`, `combat` | context for the actor only |
| `current.zone` | the schema document's psych-zone |
| `current.condition.health` / `.fatigue` / `.injuries` | on both real sheets; read by nothing |
| `current.relationships.<id>.history` | reaches the packet, never the actor — keep it as your note |

**And three documented claims that are wrong. Follow the code.**

1. **Goals are keyed `goal`, not `statement`.** `docs/drives-schema.md:18` says `statement`; every
   reader in the code reads `goal` (`src/engine/gate.py:313`, `src/engine/identity_view.py:273`).
2. **Orientation is words, not numbers.** `docs/drives-schema.md:49-53` gives a numeric scale from
   minus one to plus one. A negative number there stops the run
   (`src/engine/identity_view.py:186-190`).
3. **Condition does not regenerate.** `docs/relevancy-gate.md:106` says it does; nothing writes
   `condition.energy` after creation.

---

*Every file:line citation in this document was opened and read while it was written. If one of them
no longer says what this document claims, the code is right and this form is stale — fix the form.*
