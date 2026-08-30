# Normative Rules for Authoring SWE Character Notes

**Status: CANONICAL CONTRACT.**
Companion to `docs/scene-authoring-rules.md` (scene configs and drives) and
`docs/world-authoring-rules.md` (the world note and its people). Derived from the loader
(`src/engine/vault.py`), the live-field table in `docs/guide-content.md`, and the relevancy gate.

Written after a measured audit of a working book found **zero** loaded beliefs across its whole
cast, with `recall_events.belief_refs` empty on every turn of every run ever made — the recall
engine had never fired once, in a book whose belief *prose* was rich. Examples use an invented
book so this file stays upstreamable to the template.

---

## 1. Rule 1: The `## Beliefs` Section IS The Vault — And Only The Parsed Form Loads
- **The Law**: Beliefs are parsed line-by-line by `_BELIEF_RE` (`vault.py:22`):
  `- (confidence, provenance) claim [[links]]`
  A bullet that does not match this shape **loads as nothing**. It is not partially loaded, and no
  error is raised. The note body is *not* the vault; only the parsed section is.
- **The Violation**: `- He has no gift. An auditor tested him as a child and closed the file.`
  Beautiful, load-bearing, and invisible to the machine.
- **The Valid Form**: `- (1.0, the file itself) He has no gift — an auditor tested him as a child
  and closed the file [[Auditor_Vane]]`
- **Enforced**: `scripts/lint_book.py` warns when `current.vault` is empty. A book that runs clean
  with an empty vault is a book whose memory layer is switched off.

---

## 1b. Rule 1b: Culture And Station Are DECLARED In `fixed.position` — `formative` Reaches Nothing
- **The Law**: The stable prefix the actor receives is built from **`fixed` + `baseline` only**
  (`scene.py:_build_stable`). The whole `formative` block — `culture`, `class`, `history`,
  `species_prior` — is read by **no engine code and no prompt**. It is an author's note.
  The live slot is **`fixed.position` = place · class · era · niche** (`character-schema.md:13`;
  `character-anatomy.md:40` — *"the priors others read through"*).
- **The Violation**: `"formative": {"culture": "Osserian martial-fatalism (utility as virtue,
  emotional containment)"}`. Precise, evocative, and invisible. The actor playing this character
  never learns they have a culture.
- **The Valid Form**: put it in `fixed.position.class` / `.place`, written as **self-sufficient
  prose the actor can act on without opening a world note**:
  `"class": "the powerless underclass — audited at seven, stamped Blank, and finished with by the
  paperwork the same day. Unlettered. No house, no patron, no surname, nothing that opens a door."`
- **The test that found this**: build the packet and print `persona`. A protagonist came back as
  `{"id": null, "name": "Maren", "people": null, "position": {}}` while a supporting character in the
  same book carried a full three-field position. Both sheets *looked* richly authored on the page.
- **Corollary — do not make the reader connect dots.** A culture NAME is a pointer; a pointer is not
  grounding. The sheet states what this character's culture means *for them*: what they were owed,
  what they owe, what they were never taught, what everyone around them assumes. The world note
  exists for the author's consistency, not as the actor's lookup table.
- **Also live, also easy to miss**: `fixed.id` and `fixed.people` sit in the same persona block. A
  character-level `"id"` outside `fixed` does NOT populate `persona.id` — it reads `fixed.get("id")`.

---

## 1c. Rule 1c: Adding A Character Is A FOUR-PLACE TRANSACTION, Not One File
- **The Law**: The packet is built by **joins on ids and on literal name strings**. The engine never
  infers a connection. For character B to reach character A's turn at all, **four** conditions must
  hold simultaneously, in three different files:

  | # | condition | where | if missing |
  |---|---|---|---|
  | 1 | `world.people` has `{id: "b", what: "..."}` | the world note | `_extract_named_entities` finds nobody — no entity percept, ever |
  | 2 | B's **first name appears in the event text** | the scene config | same: presence must be *evidenced by the text* (`gate.py`, "No invention") |
  | 3 | A passes the identity check: **insight ≥ 0.55** | A's `baseline.skills` | percept exists but `recognized_as` is empty — A sees *a person*, not B |
  | 4 | `A.current.relationships["b"]` exists, keyed by the **same id** | A's character note | `_build_edges` finds no record and emits no edge — B is present but A has no stance toward them |

- **The Violation, and it is the easy one to commit**: author `characters/<Someone>.md` beautifully, put
  him in the scene config, and stop. He is a complete, playable character who is **invisible** to the
  person he is talking to. Worse, the prompt then tells the actor to set `addressee` and
  `tags.subject` by copying an id from *"Those present"* — which is empty — so the actor cannot
  legally address the person in the room with them.
- **A character is NOT automatically an entity.** `load_book` builds `world.people` from
  `people/*.md` notes and from `world.people` in the engine block. Characters in `characters/` are
  loaded into a **separate** dict and never added. Every character who will be *perceived* by
  another character needs an entry in both places.
- **Edges are directional and must be authored BOTH ways.** `A.relationships["b"]` gives A a stance
  toward B. It gives B nothing. A one-way edge is the signature of a half-finished cast addition.
- **The Valid Form** — the full transaction for one new character:
  1. `characters/<Name>.md` — the sheet (Rule 1, 1b, 8).
  2. `world.people` — `{id, what}`, `what` written as the identity record a knower would have.
  3. `current.relationships` on **every existing character who knows them**, and on the new
     character for each of them. Reciprocal, keyed by id.
  4. `world.locations` — any location they occupy (`world-authoring-rules.md` Rule 6).
  5. `lexicon.attribute_classes` — their first name as a keyword, if events will name them.
  6. Beliefs on both sides that carry the other's name, so recall can fire (Rule 3).
- **Enforced**: `scripts/lint_book.py` warns on a character absent from `world.people`, and on any
  one-way relationship between two characters.

---

## 1d. Rule 1d: Declare `role_tier` FIRST — It Is The Fill Target, And It Is Not A Floor
- **The Law**: `fixed.role_tier` is `principal | supporting | background`, and
  `character-schema.md` §"Depth by role" states what each earns:

  | tier | fill |
  |---|---|
  | **principal** | every field, deep — full drives, vault, provenance, fine traits |
  | **supporting** | genotype + position + an archetype-model + light drives/skills; **thin vault** |
  | **background** | genotype + position + archetype; **no vault, no provenance** |

- **But four fields are owed at EVERY tier**, because they are not depth, they are wiring:
  `fixed.id` · `fixed.people` · `fixed.position` · `fixed.genotype`. These are the persona block
  (Rule 1b) and the perception join (Rule 1c). A background extra with no `position` is not a thin
  character, it is a broken one — the actor beside them receives `position: {}`.
- **The Violation, measured in a live book**: three supporting cadets carried
  `role_tier: "principal"` while the **protagonist and the chapter-1 scene partner carried no tier
  at all** — and both of those two also had `genotype` filed under the inert `formative` block, so
  neither reached their actor. The declared tiers and the actual fill depth had no relationship.
- **`role_tier` is read by no code.** It is a promise the author makes to themselves about how deep
  to fill. That is exactly why it must be written down: an undeclared tier means the next session
  guesses, and guesses drift upward — every field is free to add and expensive to keep consistent.
- **The real cost of over-building is not tokens, it is contradiction.** A supporting character with
  a full Layer-10 model and six HEXACO facets has thirty more places to disagree with themselves
  three chapters later. Fill to tier and stop.
- **The Valid Form** — a supporting character who appears in one scene:
  1. `role_tier: "supporting"`, plus the four wiring fields.
  2. `temperament` (all 8 — the engine requires them), `traits`, a light `model`, `voice`.
  3. `drives` — one goal and one wound is enough; the wound is what makes the scene move.
  4. **A thin vault: three or four beliefs**, phrased with the nouns the scene will actually use.
  5. Reciprocal `relationships` with whoever they share the scene with (Rule 1c).
- **The completion test is a scene, not a checklist**: build the packet for the scene they appear
  in. If their edges are non-empty and at least one belief fires, they are built enough. If nothing
  fires, more baseline detail will not help — beliefs will.

---

## 2. Rule 2: Confidence Is The Recall Cost, Not A Flavour Dial
- **The Law**: `cost = 1 − confidence`, charged against a per-turn budget of
  `energy × (1 − load/2)`. A 1.0 belief costs nothing and surfaces whenever its words are echoed;
  a 0.6 belief costs 0.4 and surfaces only on a sharp day.
- **The Violation**: Setting every belief to 0.8 because it "feels about right". You have made
  every memory equally expensive and equally faint.
- **The Valid Form**: Constitutive wounds — the ones that made the character — are **1.0**.
  Half-noticed suspicions, secondhand rumours, and things they have not let themselves conclude
  are **0.5–0.7**, and will legitimately fail to surface when the character is tired.
- **This is a lever**: draining `current.condition.energy` makes a character *miss what they know*.
  That is the director's sanctioned cognition control, not a bug.

---

## 3. Rule 3: Claims Must Carry The Words The Events Will Echo
- **The Law**: Trigger matching is normalised **word overlap** between the event text and the
  claim text. A belief fires because a word is shared.
- **The Violation**: `- (0.9, memory) What happened that year changed everything.` It shares words
  with nothing and can never fire.
- **The Valid Form**: Name the nouns your scenes will use — *silver*, *debt*, *the levy*, *the
  quarry*. If a belief is about conscription, the word "levy" or "draft" must be in it.
- **Corollary**: `[[links]]` are live recall edges — a belief also fires when a **linked note's
  name** appears. Author links deliberately; they are the edges you control by hand.

---

## 4. Rule 4: Relationship Keys Must Equal `world.people` Ids
- **The Law**: `current.relationships {target: {trust, affinity, respect, debt}}` becomes
  `volatile.edges` and reaches the prompt as direction phrases — but **only for entities
  recognised in the PerceptSet**. A key that does not match a `world.people` id never appears.
- **The Violation**: A harbourmaster and a protagonist with three years of shared history and
  `current.relationships` absent on both. The engine sees two strangers and the LLM re-infers the
  bond from prose every single turn.
- **The Valid Form**: Author the edge on **both** sides, keyed to the exact `world.people` id, with
  `debt` carrying real weight for a character whose wound is debt.
- **Why it matters**: a misspelled key fails silently. There is no warning for an edge that never
  surfaced — which is why `lint_book.py` now warns when `relationships` is absent entirely.

---

## 5. Rule 5: Only Three Traits And Three Skills Are Read Today
- **The Law**: Of `baseline.traits`, only **emotionality** (→ FEAR/GRIEF sensitivity),
  **agreeableness** (→ RAGE, negatively) and **extraversion** (→ PLAY/SEEKING) slope gains. Of
  `baseline.skills`, only **perception ≥ 0.60** (subtle cues), **insight ≥ 0.55** (entity
  recognition) and **combat** (harm/threaten capability) gate anything.
- **The Violation**: Tuning `conscientiousness` from 0.85 to 0.92 expecting behaviour to move.
- **The Valid Form**: Author the other facets as honest context — they ride the stable prefix and
  the LLM reads them — but do not expect them to compute. Spend your tuning on the six that do.
- **Also live**: `baseline.model` weights (schwartz / moral_foundations / needs) do relevance
  weighting. A **missing** key reads as neutral 0.5, not zero — silence is average, not absence.

---

## 6. Rule 6: Voice, Wounds And Orientation Are Written For The Actor, Not The Parser
- **The Law**: `baseline.voice`, `drives.fears_wounds` and `orientation` are passed to the LLM
  **verbatim** in the stable prefix. The engine never parses them.
- **The Violation**: Writing them as config — terse keys, numeric proxies, abbreviations.
- **The Valid Form**: Craft text. These are the lines that make the actor sound like a person;
  write them as prose you would be willing to see quoted.

---

## 7. Rule 7: `current` Must Be Consistent With The Scene You Are About To Run
- **The Law**: `current.location` must be a **registered** `world.locations` id
  (`world-authoring-rules.md` Rule 6). `current.active_goals` must stay in sync with
  `drives.goals` — they feed the same salience path. `current.affect` starts at or near the
  temperament means unless the book opens mid-crisis.
- **The Violation**: A protagonist whose `current.location` is the final-act stronghold while
  chapter one opens on a river wharf.
- **The Valid Form**: Advance `current` as the book advances. It is turn-zero state, not a
  character summary.
- **Goal phrasing**: salience is word overlap with vault claims — phrase goals with the **same
  nouns** the beliefs use, or goal-bearing beliefs will not win the recall budget.

---

## 8. Rule 8: The Engine Block Is The Contract; The Prose Is For You
- **The Law**: A character note is two artifacts in one file — the fenced `json` engine block the
  machine validates, and the surrounding prose canon that no code reads. Both matter; only one
  runs.
- **The Test Before Any Run**: `python scripts/lint_book.py --vault "<book>"`. It asserts, per
  character — `vault` non-empty · `relationships` present and keyed to real people ids ·
  `location` registered · `active_goals` non-empty. Four assertions. They would have caught every
  defect this document was written after.
