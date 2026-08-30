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
| `principal` | all of it, deep — every goal, every wound, six or more beliefs |
| `supporting` | the required fields, one goal, one wound, a light voice, three or four beliefs |
| `background` | the required fields and nothing else — no beliefs, no wound |

>> **HOW THIS IS USED:** it is not. Searched the engine and the scripts; `role_tier` appears in no
>> Python file. It is a note to the next person, and the reason to write it is that an undeclared
>> tier makes the next session guess, and guesses drift upward.

**IF YOU LEAVE IT BLANK:** nothing breaks. You just lose the record of how deep you meant to go.

**The thing that is NOT optional at any tier.** Four fields are owed by a one-line walk-on exactly
as much as by the protagonist, because they are wiring and not depth: `fixed.id`, `fixed.name`,
`fixed.people`, `fixed.position`, and `fixed.genotype` below. A background extra with no position is
not a thin character; it is a broken one.

---

# PART TWO — THE TEMPERAMENT THEY WERE BORN WITH

## 2.1 — The six inborn axes

**Key path:** `fixed.genotype` — six sub-fields, all six required

**REQUIRED.**

**What it is.** Six dials fixed at birth. They do not say what this person *feels*; they say **how
hard the same thing hits them compared to anybody else**. Two people stand in the same avalanche;
this is why one of them is more frightened. Nothing in the whole engine can ever change these — not
the story, not trauma, not growth. That is the point: two people who then live identical lives still
come out different.

**THE LEGAL VALUES ARE EXACTLY FOUR WORDS:**

```
low   |   typical   |   elevated   |   high
```

Taken from the code's own table (`src/engine/state.py:26-31`), which is the only place these words
are defined.

### THE FIRST-WORD TRAP — read this before you write anything

**The engine reads only the FIRST WORD of what you type, lowercased.** It splits your text on the
first space and looks that single token up (`src/engine/state.py:236-240`). Anything it does not
recognise falls back to `typical`, **silently**.

So:

| you write | the engine hears |
|---|---|
| `"high"` | high |
| `"high (he cannot hold anyone loosely)"` | high — the note after the space is safely ignored |
| `"very high"` | **typical** — because the first word is "very" |
| `"exceptional"` | **typical** |
| `"selective and gated"` | **typical** |

This has happened for real. On one live book, three of six axes on the protagonist read as typical
— `"very high"`, `"selective and gated"`, `"exceptional"` — understating the man's drive by about a
third and giving a person who trusted nobody perfectly ordinary attachment. Nothing was printed.

**How to write a note safely:** put the allele word first, then a space, then your note in
parentheses. `"high (the innate empathy — she cannot hold someone loosely)"` works: the engine takes
`high`, and the parenthetical is stripped off before anything reaches the actor
(`src/engine/scene.py:251-255`).

### The six axes, and what each one turns up

| axis | write one of the four words | what raising it does |
|---|---|---|
| `threat_reactivity` | ______________ | how hard FEAR lands |
| `approach_drive` | ______________ | how hard SEEKING lands — reaching, wanting, going after |
| `affiliation_attachment` | ______________ | how hard CARE **and** PANIC_GRIEF land — attaching, and losing |
| `anger_proneness` | ______________ | how hard RAGE lands |
| `effortful_control` | ______________ | how fast any feeling settles back down afterwards |
| `sensitivity` | ______________ | how much lands at all |

**Worked example (Tam, the frightened one):**

```json
"genotype": {
  "threat_reactivity": "high",
  "approach_drive": "low",
  "affiliation_attachment": "elevated",
  "anger_proneness": "low",
  "effortful_control": "typical",
  "sensitivity": "elevated"
}
```

**Worked example (Nell, the one who goes up the hill alone):**

```json
"genotype": {
  "threat_reactivity": "typical",
  "approach_drive": "elevated",
  "affiliation_attachment": "high",
  "anger_proneness": "typical",
  "effortful_control": "high",
  "sensitivity": "typical"
}
```

>> **HOW THIS IS USED:** `build_profile` turns each axis into the character's per-feeling gain —
>> `threat_reactivity` → FEAR, `approach_drive` → SEEKING, `affiliation_attachment` → both CARE and
>> PANIC_GRIEF, `anger_proneness` → RAGE (`src/engine/state.py:311-316`); `effortful_control`
>> becomes how quickly feeling decays back to rest (`src/engine/state.py:333`) and `sensitivity` a
>> global gain (`src/engine/state.py:336`). Separately, each allele is turned into a sentence the
>> actor reads about itself — `high` on attachment becomes *"you cannot hold someone loosely"*
>> (`src/engine/identity_view.py:103-122`, rendered at `src/engine/identity_view.py:220-224`).
>> `typical` deliberately has no sentence: an unremarkable dial is not self-knowledge.

**IF YOU LEAVE IT BLANK:** every axis defaults to `typical` and this person feels exactly like the
species average — your cast converges and every character reacts to the same event the same way.

**IF YOU GET A WORD WRONG:** the pre-run check treats it as an **error**, not a warning, and prints
which axis, what you typed, and the four legal words (`scripts/lint_book.py:196-214`). Run the check.
It is the only thing standing between you and a silently flattened character.

**Two ways to fill this in.** For background and supporting people, have someone draw them — there
is a script that does it from a seed, and the same seed always yields the same person
(`scripts/make_genotype.py`, described in `docs/guide-emotional-authoring.md:31-53`). For a
principal, do it the way you just did: start from the person the story needs and pick the words that
produce them.

---

# PART THREE — THE NUMBERS THAT ARE NOT YOURS TO PICK

There are two blocks on every sheet that are made of numbers only. **You are not being asked to
choose those numbers.** You are being asked to describe the person in words; whoever sizes the
sheet turns your description into the figures, using the species reference table and the emotional
authoring guide. Fill these two boxes in sentences and hand them over.

---

## 3.1 — Their resting face

**Key path:** `baseline.temperament` — one entry per primitive, all eight

**REQUIRED — all eight names must be present, or the book stops.**

**What it is.** Where this person sits when nothing at all is happening. Not their mood on page one
— their *default*. An anxious person is someone whose resting fear is high, which is a different
claim from "she is frightened in chapter one".

**The eight, and what each one means** (from `docs/emotion-basis.md:27-35`):

| primitive | the thing nothing else produces |
|---|---|
| `SEEKING` | forward pull toward what might be found |
| `FEAR` | withdrawal from anticipated harm |
| `RAGE` | approach to remove an obstacle or redress a wrong |
| `LUST` | approach toward union |
| `CARE` | act on another's behalf at cost to yourself |
| `PANIC_GRIEF` | distress at a broken bond |
| `PLAY` | engagement for its own sake, without stake |
| `DISGUST` | expel — *this would contaminate me* |

**YOUR JOB — write one sentence per primitive.** Where does this person sit when the room is quiet?

```
SEEKING ______________________________________________
FEAR ________________________________________________
RAGE ________________________________________________
LUST ________________________________________________
CARE ________________________________________________
PANIC_GRIEF _________________________________________
PLAY ________________________________________________
DISGUST _____________________________________________
```

**Worked example (Tam, in sentences, then as the sizer wrote it):** *"low forward drive, high
resting fear — this is the cowardice, and it is a disposition not an immunity; real care, which is
what makes him reachable; very little play."* The sizer produced
`"FEAR": {"mean": 0.62, "variability": 0.16, "note": "resting fear, high — this is the cowardice"}`.

>> **HOW THIS IS USED:** the resting level is what every stage direction is measured *against* — the
>> engine only tells the actor about a feeling when it has departed from this person's own rest, so
>> a character who is always a little afraid is not told so every beat, and one who is suddenly
>> afraid is (`src/engine/direction.py:230-256`). When the affect vector clearly matches a named
>> compound emotion — disdain, say — the stage-direction line now also names it; when the two
>> closest compounds are too close to tell apart, it says nothing rather than guess
>> (`src/engine/direction.py:210-227`, applied at `src/engine/direction.py:269-271`). It is also the
>> input to how feeling decays (`src/engine/state.py:485`).

**IF YOU LEAVE A PRIMITIVE OUT:** the pre-run check errors and lists exactly which names are
missing, saying that decay and profile-building need all eight
(`scripts/lint_book.py:130-133`). This one is a hard stop, not a warning.

**A note you can use, and should.** Any entry may carry a `"note"` key. Notes are stripped out
before anything reaches the actor (`src/engine/scene.py:237-248`), so a note is the safe place to
record *why* a number is what it is. Tam's SEEKING entry carries
`"note": "THE TARGET. Courage in this engine is agency, and this is the number the growth fork
raises"` — that is a message to a future author, and the actor never sees it.

**LEAVE ALONE: `variability`.** You will see a second key beside `mean` on real sheets. Nothing
reads it — searched the engine and the scripts, and the only mention is a docstring
(`src/engine/state.py:485`); the words-only layer explicitly drops it before the actor sees anything
(`src/engine/identity_view.py:218`). Do not spend a minute on it.

---

## 3.2 — What they are feeling on page one

**Key path:** `current.affect` — the same eight names, one number each

**REQUIRED — all eight, again.**

**What it is.** Their actual mood at the moment the book opens. **Unless your book opens
mid-crisis, this should sit at or very near the resting face you just described** — the difference
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
primitive, and says the appraisal step needs all eight (`scripts/lint_book.py:134-141`).

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

# PART FIVE — WHAT THEY ARE AFRAID OF

## 5.1 — Their wounds and fears

**Key path:** `baseline.drives.fears_wounds` — a list. Each entry has a `wound` **or** a `fear`, a
strength, a `trigger` list and an `avoidance` list.

**REQUIRED for principals and supporting characters. This is the field that makes scenes move.**

**What it is.** A **wound** is the thing that happened. A **fear** is the standing dread it left
behind. An **avoidance** is what they *do* instead. One entry can hold all three, and the strongest
version does.

**YOUR JOB, per wound — four boxes:**

```
WHAT HAPPENED (the wound) — one sentence, concrete, with the details in it:
_______________________________________________________________________
_______________________________________________________________________

HOW HARD IT TAKES THEM  (circle one, then write its number)
  ( ) an old scar I rarely feel            -> intensity 0.15
  ( ) it catches me sometimes              -> intensity 0.40
  ( ) it takes hold of me when it comes    -> intensity 0.65
  ( ) it takes me over                     -> intensity 0.90

WHAT SETS IT OFF (trigger) — 2-4 short phrases, in the words a scene would actually use:
  1. _______________________  2. _______________________
  3. _______________________  4. _______________________

WHAT THEY DO INSTEAD (avoidance) — 2-3 concrete behaviours, not feelings:
  1. ___________________________________________________________________
  2. ___________________________________________________________________
  3. ___________________________________________________________________
```

> **The circled sentence is for you. The sheet stores the number.**
> This is the one ladder in this document whose worked example used to show only the phrase, and
> in a controlled trial on 2026-08-30 one writer in three left the sentence in the slot. Their book
> passed both linters and stopped the run the moment the prompt was built. `lint_book.py` now
> catches it as an ERROR naming the field — but write the number here and it never comes up.
> The sheet holds `"intensity": 0.90`, not `"intensity": "it takes me over"`.



*(The four intensity sentences are the engine's own — `src/engine/identity_view.py:65-66`.)*

**Worked example (Tam's first wound, complete):**

- **wound:** *"at nineteen he stopped at the last wall while his father went on up the fell road in
  bad light, and his father came back on a hurdle. Nobody has ever mentioned it, which he takes as
  everyone agreeing"*
- **intensity:** *it takes me over*
- **trigger:** `["fell road", "the last wall", "someone else walking into danger ahead of him"]`
- **avoidance:** `["finds work that must be done here, now, instead", "volunteers for the cold job
  nobody wants so as not to be asked for the frightening one", "agrees with whatever is decided and
  does not go"]`

**Teach the judgement — avoidances, good and weak:**

| weak | good |
|---|---|
| `"gets anxious"` | `"answers a question with a description of a task"` |
| `"avoids the subject"` | `"leaves to check the race"` |

The weak ones are states. The good ones are things an actor can *do* on camera.

>> **HOW THIS IS USED:** the whole block is copied into the actor's identity prefix
>> (`src/engine/scene.py:230`) with the intensity replaced by one of the four sentences and every
>> other key carried through (`src/engine/identity_view.py:250-251`). The actor reads your wound in
>> your words, every beat, as part of who it is.

**IF YOU LEAVE IT BLANK:** nothing errors — and the character has no friction. In practice this is
the single field that most often makes the difference between a scene that moves and one that
circles.

**LEAVE BLANK — nothing reads these.** The design document also lists `protects` and `defense`
(`docs/drives-schema.md:34-43`). No engine code reads either. Say the protective behaviour in the
`avoidance` list instead, where it will at least reach the actor as words.

---

## 5.2 — THE TRIGGER RULE, and it deserves its own heading

**Your `trigger` list, on its own, computes nothing.**

Write this down, because it is the most common way a beautifully-authored character disappoints
its author. `fears_wounds` is prose. The actor reads it and plays it — that is real and it matters.
But the trigger words do not make the character's *fear go up* when they appear in a scene. Nothing
matches them against the event text.

There is a separate tier that does that arithmetic — a list of rows on the sheet called
`baseline.catalog`, where each row says *"when these words are in the room, multiply this feeling"*
(`src/engine/levers.py:227-249`). **That tier is not yours to write.** It is the number half of the
sheet, and it belongs with the person who sizes the temperament.

**What you owe them: the trigger list.** Your triggers are the *specification* for those rows. Write
them in the plain words a scene would actually use — `"fell road"`, `"blood on snow"`, `"the hall
going quiet"` — and hand them over.

**How you will know it was done.** The pre-run check pairs the two halves. For every wound that has
a trigger list and no matching row, it warns, quoting your trigger words back at you and saying the
wound is prose the engine cannot compute (`scripts/lint_book.py:235-248`). On the day that check was
written it found four such wounds in a live book. **If you see that warning, the arithmetic half of
your wound was never built — that is a message for the sizer, not a mistake in your writing.**

**One thing that helps them enormously:** make the first word of each trigger the word that will
actually be on the page. The check matches on leading words (`scripts/lint_book.py:243`), and a
trigger of `"the sound of the fell road at night"` matches on *"the"*.

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
>> into the sentences you circled (`src/engine/direction.py:280-303`), which appear in the prompt
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
(`src/engine/direction.py:166-169`).

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
(`src/engine/gate.py:510-529`, applied across both halves of the prompt at
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

- **The masking keys off the id.** It masks the id's first segment (`src/engine/gate.py:526`). If
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
>> (`src/engine/gate.py:510-529`, `src/engine/prompt.py:126-127`).

**IF YOU LEAVE IT BLANK:** the character knows the name — which is the right default and is almost
always what you want. **You author ignorance; you never blanket-hide.**

---

## 10.3 — What they assume about a stranger

**Key path:** `baseline.relationship_priors` — in practice, `{"default_trust": 0-to-1}`

**OPTIONAL.**

**What it is.** Where their bonds settle when nobody is reinforcing them. It is the resting level a
relationship relaxes toward across a gap in the story.

**YOUR JOB.** One sentence: *"Left alone for a season, does this person drift back toward trusting
people or away from it?"*

**Worked example.** Tam: `{"default_trust": 0.55}`. Nell: `{"default_trust": 0.62}`.

>> **HOW THIS IS USED:** when a scene declares that time has passed, every edge on every character
>> relaxes toward these priors before the scene starts (`scripts/scene.py:300-310`, using
>> `src/engine/bonds.py:364`).

**IF YOU LEAVE IT BLANK:** relationships drift toward the engine's own default rather than this
person's. Harmless for a short book; visible across a long one.

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

**REQUIRED — the block must exist.**

**What it is.** Two dials describing how much this person has left in them. `energy` is how much
they have; `allostatic_load` is how much wear they are carrying. Together they set both how much the
actor is told they can manage, and — this is the interesting part — **how much they can remember**.

**YOUR JOB — one circle.** *How much has this person got left, on page one?*

( ) they take the shortest path and will not do the thorough version of anything
( ) they do what is asked and none of the extra
( ) they can do the thorough version where it matters
( ) they have reserve to spend on more than is asked

*(Those four are the engine's own sentences — `src/engine/direction.py:127-130`.)*

**Worked example.** Tam: `{"energy": 0.58, "allostatic_load": 0.35}` — *he can do the thorough
version where it matters*, and only just.

>> **HOW THIS IS USED:** two things. (1) It becomes the second half of the actor's stage directions
>> for the beat, as one of the four sentences above (`src/engine/direction.py:244-254`, used at
>> `src/engine/prompt.py:51-54`). (2) It sets the **memory budget** — the engine spends a budget
>> derived from energy and load when deciding which of the character's beliefs surface, and when the
>> budget runs out the remaining ones simply do not fire (`src/engine/gate.py:47-56`, spent at
>> `src/engine/gate.py:367-373`).

**This is a director's lever, and it is sanctioned.** Draining a character's energy makes them
*miss what they know*. A tired character genuinely fails to recall the thing that would have saved
them. That is not a bug; it is the one control you have over a character's cognition.

**IF YOU LEAVE IT BLANK:** the pre-run check errors — the block must at minimum be a dictionary
(`scripts/lint_book.py:142-143`). If the block exists but the two keys are missing, the engine reads
full energy and no load, and the character is inexhaustible.

**LEAVE BLANK — nothing reads these.** `health`, `fatigue`, `injuries`. They appear on both real
character sheets and no code anywhere reads any of them — searched the engine and the scripts. Write
them if you like them as notes to yourself; they compute nothing and reach no actor.

**LEAVE BLANK — nothing reads this either.** `current.zone` (the "psych zone" from the schema
document). No code reads it.

**A doc claim you may run into.** `docs/relevancy-gate.md:106` says condition *"regenerates with
rest"*. Nothing anywhere writes `condition.energy` after the character is created. If you want a
character rested in chapter four, someone has to set it.

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

**The seven messages you are most likely to see, and what each means for you:**

| the message says | what to do |
|---|---|
| `genotype.<axis> starts '<your text>', which is not an allele` | Part 2.1. Put `low`/`typical`/`elevated`/`high` FIRST. This is an error, not a warning. |
| `current.vault is EMPTY` | Part 12. Your Beliefs bullets did not match the shape, or there is no section. |
| `fixed.position is EMPTY` | Part 1.5. The actor has no place, class or station. |
| `a formative block is authored ... read by NO engine code` | Part 1.5. Move it into `fixed.position`. |
| `relationship 'x' is not a world.people id` | Part 10.1. Fix the spelling, or the world note is missing them. |
| `fears_wounds trigger [...] has NO baseline.catalog row` | Part 5.2. Your writing is fine; the arithmetic half was never built. Hand it to the sizer. |
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
      "threat_reactivity": "typical",
      "approach_drive": "elevated",
      "affiliation_attachment": "high",
      "anger_proneness": "typical",
      "effortful_control": "high",
      "sensitivity": "typical"
    }
  },
  "baseline": {
    "temperament": {
      "SEEKING": {"mean": 0.58}, "FEAR": {"mean": 0.34}, "RAGE": {"mean": 0.30},
      "LUST": {"mean": 0.32},
      "CARE": {"mean": 0.74, "note": "high, and practical rather than tender — care as work done"},
      "PANIC_GRIEF": {"mean": 0.40}, "PLAY": {"mean": 0.38}, "DISGUST": {"mean": 0.26}
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
      "fears_wounds": [
        {"wound": "she found the third ewe still alive and had to finish it herself with the
                   bill-hook, alone, in the dark",
         "intensity": 0.70,
         "trigger": ["a sheep in distress", "blood on snow", "being the only one there"],
         "avoidance": ["goes straight at it and gets it over with",
                       "does not describe the details afterwards"]}
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
               "uses a person's name when she wants them to hear it"],
      "code_switch": [{"context": "someone frightened",
                       "shift": "slower and more concrete — she describes the next small task
                                 rather than reassuring"}],
      "silence_profile": "comfortable — she can outwait anyone and knows it"
    }
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

*(The real note also carries a `baseline.catalog` block — the arithmetic tier from Part 5.2. It is
omitted here because it is not yours to write.)*

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
      "threat_reactivity":      "<low|typical|elevated|high> (optional note after the space)",
      "approach_drive":         "<low|typical|elevated|high>",
      "affiliation_attachment": "<low|typical|elevated|high>",
      "anger_proneness":        "<low|typical|elevated|high>",
      "effortful_control":      "<low|typical|elevated|high>",
      "sensitivity":            "<low|typical|elevated|high>"
    }
  },
  "baseline": {
    "temperament": {
      "SEEKING": {"mean": <sizer>}, "FEAR": {"mean": <sizer>}, "RAGE": {"mean": <sizer>},
      "LUST": {"mean": <sizer>}, "CARE": {"mean": <sizer>},
      "PANIC_GRIEF": {"mean": <sizer>}, "PLAY": {"mean": <sizer>}, "DISGUST": {"mean": <sizer>}
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
      "fears_wounds": [
        {"wound": "<what happened, concretely, with the details in it>",
         "intensity": <sizer>,
         "trigger": ["<word a scene will use>", "<another>", "<another>"],
         "avoidance": ["<a thing they DO instead>", "<another>"]}
      ],
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
| `baseline.temperament.<PRIMARY>.variability` | a sampling parameter that nothing samples |
| `baseline.drives.goals[].kind` / `.serves` / `.status` / `.origin` / `.triggers` / `.view` | `docs/drives-schema.md:16-27` |
| `baseline.drives.fears_wounds[].protects` / `.defense` | `docs/drives-schema.md:34-43` |
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
