# Building a world — the procedure

**Status: PROCEDURE.** Written 2026-09-01 to fill a measured gap. The repo had a CONTRACT
(`world-authoring-rules.md` — what is legal) and a LIBRARY (`.claude/skills/worldbuilding-frameworks/`
— what is plausible) and nothing that walked a blank page to a loadable world. `world-model.md` says
so in its own status line: *"seed … does not yet invent world content (laws, religion, economy) —
that's the directorial work we'll do together"*, which is written for a conversation rather than for
someone sitting down alone.

This is that walk. It does not replace either of the other two: the contract still says what the
machine accepts, the library still says what makes a choice defensible, and this says **what order to
decide things in, and what each decision has to become.**

## The one thing to know before you start

**Four fields are LIVE. Everything else is an anchor.**

    lexicon · locations · people · laws        the machine reads these
    world title · season · standing_facts      inert — excellent for you, invisible to the engine

That is `world-authoring-rules.md` Rule 2, and it is the rule most likely to cost you a day. You can
write a magnificent paragraph about how the river guild controls the crossings, rebuild the bible,
and watch nothing change. Every step below therefore ends with **what it becomes** — because a world
decision that lands in `standing_facts` is a decision you have documented, not one you have made.

The routing, when a decision must actually reach an actor:

| the decision is… | it becomes… |
|---|---|
| the world REFUSES something, or permits it only under conditions | a **law** |
| a thing must be PERCEIVABLE — noticed, smelled, overheard | a **lexicon** class |
| a place a scene can name | a **location** |
| someone who exists whether or not they act | a **person** |
| something one character believes | a **belief on that character**, not a world fact |
| true only right now, in this scene | the **event text** |

## The order, and why it is this order

The order is the one `.claude/skills/worldbuilding-frameworks/` already names — premise → universal
law → broader community → planet → history → present systems. It runs from the least revisable to
the most: a universal law changes everything downstream of it, and a present system changes almost
nothing upstream. Deciding in this order means you revise forward, not backward.

Each step names the framework file that grounds it. **Ground the invented in the real** is the
library's own discipline and it is the difference between a world and a mood: never "poverty is
high", always "poor *because that war*, on *that* exhausted soil".

### 1. Premise — what this world is FOR

One or two sentences: the pressure the story lives on. Not the plot; the condition that makes the
plot possible.

*Becomes:* nothing machine-readable, and that is correct. It is the thing you check every later
decision against.

*Done when:* you can say what would have to be true for this world to be boring, and it isn't.

### 2. Universal law — what is possible here

The physics, the magic, the metaphysics. Everything downstream inherits it, which is why it is
second and not later.

*Library:* magic-system design (Sanderson's Laws — cost and limit before capability),
speculative biology.

*Becomes:* a **law** for anything the world REFUSES (`world-authoring-rules.md` Rule 3 — a rule the
world enforces must be a law, not a paragraph). `src/engine/bible.py` distinguishes IMPOSSIBLE from
FORBIDS, and the distinction is worth getting right: impossible is physics, forbidden is a choice
someone made and could unmake.

*Done when:* every law names what it refuses and what, if anything, excepts it.

### 3. Broader community — who lives with whom

Kinship, stratification, authority, and what people owe each other.

*Library:* social structure and kinship (descent, the six terminology systems, marriage and
residence, honor/dignity/face), political structures (Service/Fried typology, Weber's authority,
Mann's IEMP).

*Becomes:* **people** (`type: person`, Rule 7) for anyone who exists independent of a scene; a
**lexicon** class for any status that must be VISIBLE — if a character can read someone's rank off
their clothing, that is a perception, and perceptions are lexicon.

*Done when:* you can say who a stranger owes deference to and how they can tell.

### 4. Planet — where it happens

Terrain, climate, biomes, water, and what can be grown or dug.

*Library:* physical geography (plate tectonics, Köppen/Whittaker/Holdridge climate, hydrology,
resource genesis and spread), ecology (trophic webs, island biogeography).

*Becomes:* **locations** — and Rule 6 is strict about it: *every location a scene names must be
registered.* A place that exists only in prose cannot be moved to, perceived at, or scoped by a law.
This is also the step the engine can now answer questions about: `read_api.place()` reports what is
known about a location as of a turn, once the keeper has recorded anything.

*Done when:* every place you intend to open a scene in is registered, and each one has a reason to
be where it is.

### 5. History — how it got this way

The prior shape of the present. Not a timeline for its own sake: the causes still exerting force.

*Library:* historical causation (secular cycles, elite overproduction, complexity collapse, the
longue durée), technology levels (three-age system, energy capture, tech trees).

*Becomes:* mostly **beliefs on people** and **standing_facts** — and this is the step where the
inert/live distinction bites hardest. History reaches the machine through who remembers it. A war
forty years ago is not a world field; it is a belief in the people who fought it, and a law if it
left a rule behind.

*Done when:* at least one present-day constraint traces to a specific past event, by name.

### 6. Present systems — what is running right now

Economy, faith, law-in-practice, the things a character bumps into on an ordinary day.

*Library:* economic systems (subsistence → market, Polanyi's forms of integration, money and debt,
trade networks), religion and mythology (pantheon design, real-vs-believed).

*Becomes:* **laws** for what is enforced, **lexicon** for what is perceivable, **locations** for
where it happens. If a system produces none of those three, it is scenery — which is allowed, as long
as you know that is what you chose.

*Done when:* an ordinary character walking an ordinary day meets at least one of these.

## Verify

```bash
python scripts/lint_book.py --vault "<book>"
```

The linter enforces the CONTRACT: one note reaching the machine, locations registered, people
declaring `type: person`, laws well-formed. **It cannot tell you the world is good** — it tells you
the world is loadable. The `Done when` lines above are the other half, and they are yours to judge.

Two checks the linter will not run for you:

- **The inert check.** Pick a `standing_fact` you believe is doing work. Edit it, rebuild, and diff
  behaviour. It will not move (that is Rule 2's own falsification). If you expected movement, that
  fact needs routing per the table at the top.
- **The analog check.** Take any invented element and name the real framework it traces to. If you
  cannot, it is arbitrary — which the library exists to prevent.

## What is still unbuilt, so you can plan around it

- **Character generation from the world.** `docs/composition-pass.md` specifies classify → compose;
  both halves now ship (`scripts/composition_pass.py --classify`), but the wider creation pass the
  design names — position → formative environment → baseline → individuation — is still partly
  authored by hand. See `docs/guide-emotional-authoring.md`.
- **A world that grows on its own.** The engine records what characters do and say
  (`scripts/keeper.py`), so lore accretes from play — but nothing invents world content for you.
  This procedure is the human half and is meant to stay that way.

## Where to go next

`docs/guide-content.md` for the field-by-field shape of the notes · `docs/world-authoring-rules.md`
for the contract in full · `.claude/skills/worldbuilding-frameworks/` for the library (keep it even
if you skip the agents — it is reference an author reads, not code an agent runs) ·
`docs/guide-user-path.md` for what happens after the world is built.
