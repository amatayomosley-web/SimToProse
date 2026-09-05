# Normative Rules for Authoring the SWE World & Its People

**Status: CANONICAL CONTRACT.**
Companion to `docs/scene-authoring-rules.md`. Derived from the loader (`src/engine/vault.py`),
the live-field table in `docs/guide-content.md`, and the bible builder (`src/engine/bible.py`).

Written after a measured audit of a working book found **1,972 lines of world canon of which 264
reached the engine**, and the rest had zero runtime effect. Examples below use an invented book —
a harbour town, a levy, a ferryman — so this file stays upstreamable to the template.

---

## 1. Rule 1: Exactly One Note Reaches The Machine
- **The Law**: The loader takes **exactly one** `type: world` note and reads **only its fenced
  `json` engine block** (`vault.py:81-88`). Every other file in `world/` is author reference. It
  never enters a packet, never gates a check, never produces a refusal.
- **The Violation**: Writing a governing rule into `world/TheHarbourGuild.md` as `type: concept`
  prose and believing the simulation now enforces it.
- **The Valid Form**: Prose lives in the concept doc for you; the *mechanism* is copied into the
  world note's engine block as a law, a location, a lexicon class, or a person.
- **Why it matters**: Two `type: world` notes raise `VaultError`. Zero engine block raises
  `VaultError`. Silent invisibility is the failure mode with no error at all.

---

## 2. Rule 2: Five Fields Are Live — The Rest Is Stored, Not Executed
- **The Law**: Of the world engine block, only **`lexicon`, `locations`, `people`, `laws`,
  `tensions`** have runtime effect. `world` title, `season`, and `standing_facts` are **INERT**
  (`guide-content.md:74`) — excellent authorial anchors, zero machine consequence.
- **The Violation**: Rewriting `standing_facts` to change how characters behave. Nothing changes.
- **The Valid Form**: If a standing fact must reach an actor *today*, route it: into a **law** (if
  the world refuses something), a **lexicon class** (if it must be perceived), a **belief** on the
  character who holds it, or the **event text** of the scene.
- **Falsification**: edit a standing fact, rebuild the bible, diff behaviour. It will not move.


### 2a. `tensions` — the fifth live field (added 2026-09-02)

A tension is a **standing, named grievance** the world already carries: the contested border, the
old feud, the suppressed faction. `history.md` says where they come from — *"History's output is the
present's **unresolved** tensions… the **fuel** for the director's circumstances."* You author them;
nothing invents one. A model may report that an act happened; naming new world structure is a
willful act and `world-dynamics.md` seats will with the director: *"the world is **directed** (the
room acts it)… its will is the director."*

```json
"tensions": [
  {"id": "harbour-levy",
   "what": "the levy on the ferry crossing, resented by the boatmen",
   "temperature": 0.1,
   "factions": ["guild", "boatmen"],
   "watches": {"parties": ["guild", "boatmen", "ferryman_tam"], "locations": ["crossing"]},
   "interests": {"social_violation": 0.6, "threat": 0.3, "loss": 0.4},
   "cooling": "slow"}
]
```

- **`watches`** is SCOPE: whose acts, and where, can touch this at all. Name at least one party or
  location, or nothing can ever be in scope and the tension sits inert while looking live.
- **`interests`** is WHAT IT IS ABOUT, weighted over the seven appraisal dimensions the engine
  already prices events in. **This is why you never say which tension an act is about**:
  `world-dynamics.md` specifies *"(typed event × standing interests) → state delta, computed, never
  guessed"*, so an act is priced against EVERY live tension and lands on the ones that watch it. One
  act may heat several — a public killing raising both the levy dispute and the old feud is two true
  facts, not a collision.
- **`cooling`** is `slow` / `typical` / `fast` — heat fades absent fuel, applied at read.
- **The Violation**: authoring a tension nothing watches, or whose interests name a dimension
  outside the seven. `scripts/lint_book.py` refuses both, and warns when a watch names a location or
  person the world does not register.
- **Falsification**: author a tension watching nobody and nowhere; the linter fails before a run.

**A threat that no tension watches is not a world event.** It is a beat, the appraisal tier already
recorded it, and the emitting seat refuses it saying so. That is how *"only the levered is
written"* (`world-state-ledger.md`) stays true without anyone policing it.

---

## 3. Rule 3: A Rule The World Enforces Must Be A Law, Not A Paragraph
- **The Law**: Anything the world *refuses*, *mandates*, or *adjudicates* belongs in `laws[]` with
  `{id, domain, act, ...}`. `domain` is one of the accepted domains — `supernatural`, `legal`,
  `persons`, `cosmology`. `act` is the thing a character might attempt.
- **The Violation**: A universal conscription mandate that exists only as prose in a concept doc.
  The engine cannot consult it, so no scene can be refused by it and no character can be caught
  breaking it.
- **The Valid Form**: `{"id": "levy-binds-at-majority", "domain": "legal",
  "act": "evade-the-harbour-levy"}` — now `laws_bearing_on()` and `verdict_for()`
  (`law.py:324,340`) can reach it.
- **Test**: for every rule your book states out loud in dialogue, grep the engine block for its
  `act`. If it is absent, the scene is asserting a law the world does not have.

---

## 4. Rule 4: The Lexicon Is Your Event Register, Not Your Glossary
- **The Law**: `lexicon.attribute_classes {class: [keywords]}` drives overt percept extraction.
  Classes are **the nouns your events are ABOUT**; keywords must be the words your event text will
  actually use — **including character first names**.
- **The Violation**: Authoring elegant taxonomy classes whose keywords never appear in a scene's
  prose. They extract nothing.
- **The Valid Form**: Write a scene's event text first, then harvest its live nouns into classes.
- **Why it matters**: No lexicon at all is legal but thin — generic extraction, kind plus leading
  words, no subtle percepts (`guide-operating.md`, "start a new book").

---

## 5. Rule 5: Subtle Cues Are Gated Detail, Not Just Important Detail
- **The Law**: `lexicon.subtle_cues {cue: [markers]}` surfaces only to a character with
  **perception ≥ 0.60**. `lexicon.subtle_cue_classes` names which classes carry gated detail.
- **The Violation**: Putting a fact everyone must know behind a subtle cue. Half the cast is blind
  to it and the scene stalls.
- **The Valid Form**: Subtle cues are progressions, tells, and concealments — *what only the
  skilled notice*. The danger-bearing classes are the ones that belong in `subtle_cue_classes`.

---

## 6. Rule 6: Every Location A Scene Names Must Be Registered
- **The Law**: `locations[{id, what}]` produces the location percept when `scene_slice.location`
  is set. An id used in a scene config or in a character's `current.location` that is absent from
  `world.locations` yields no percept.
- **The Violation**: A scene directive set at `harbour_pier_four_shack` while `world.locations`
  holds only the interior rooms of the destination the book ends in.
- **The Valid Form**: Register the location the moment a scene is drafted there — **before** the
  run, not after the prose reads flat.
- **Enforced**: `scripts/lint_book.py` names any `current.location` absent from `world.locations`.

---

## 7. Rule 7: People Notes Must Declare `type: person`
- **The Law**: `people/*.md` becomes `world.people` **only** if the note's frontmatter type is
  `person` — the loader skips anything else (`vault.py:92-93`). A note with *no* type defaults to
  person; an explicit `type: concept` is dropped.
- **The Violation**: Authoring the sergeant who physically triggers the protagonist's first fight
  as `type: concept`. He is unrecognisable to the engine and cannot carry a relationship edge.
- **The Valid Form**: `type: person`, and the first prose line is the **identity record** —
  revealed only on a passed insight check (≥0.55), so write it as *what a knower knows*, not as a
  neutral description.
- **Corollary**: `id`'s first token is the name matched in event text. If your prose says "Edda",
  the id must start `Edda`.

---

## 8. Rule 8: The Promotion Test — Reference Or Mechanism?
- **The Law**: For every fact sitting in a concept doc, ask which of these a character does with
  it. It earns a place in the engine block only if the answer is not "none":

  | the character must… | it becomes |
  |---|---|
  | **perceive** it | a `lexicon` class or subtle cue |
  | **stand in** it | a `location` |
  | **be refused or bound by** it | a `law` |
  | **recognise someone** by it | a `people` entry |
  | **believe** it | a belief on that character (see `character-authoring-rules.md`) |
  | none of the above | leave it as reference — it is doing its job |

- **Why it matters**: The instinct on finding a thin simulation is to *write more world*. Usually
  the world is already written and merely unrouted. Adding a twenty-fifth concept document moves
  the engine exactly as much as adding none.
