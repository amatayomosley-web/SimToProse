# Normative Rules for Authoring SWE Scenes & Characters

**Enforcement:** `python scripts/lint_scene.py --book <slug> --scene <cfg.json>` checks rules 1-3 mechanically against the BOOK (ids, subject, location, act, drives) and prints what it did NOT check. Rules 4 and 6 are semantic and unmechanized; rule 5 is UNBACKED (see below). A clean lint is not 'all six rules verified' and the tool says so.

**Status: CANONICAL CONTRACT.**
Derived from engine architecture (`docs/world-model.md`, `docs/scene-assembly.md`, `docs/design.md`) to prevent authorial forcing, unnatural exposition dumps, and conversational stalling.

---

## 1. Rule 1: Circumstance Over Scripting (Pressure, Not Plot)
- **The Law**: Directives in scene configs must establish **physical conditions, external pressures, and immediate stakes**—NEVER dialogue topics.
- **The Violation**: Writing `"The senior stylist explains the history of the salon to the junior"`. (Forces the model into textbook mode).
- **The Valid Form**: Writing `"The wedding car is booked for eleven; the bride is in the chair with half her hair pinned, and the senior stylist is standing behind the junior with her hand held out for the comb."` (Sets a physical conflict).

---

## 2. Rule 2: In-Room Character Drives (No Meta-Goals)
- **The Law**: An actor's active goal must answer: *“What do I want to extract from, force upon, or protect in the person in front of me right now?”*
- **The Violation**: Setting a goal as `"Explain the salon's booking rules to the reader"` or `"Introduce the world lore"`.
- **The Valid Form**: Setting a goal as `"Get the comb out of her hand before the bride can tell anything is wrong"`.

---

## 3. Rule 3: Beliefs as Ammunition (Grievances, Not Legal Texts)
- **The Law**: In-world lore in a character's sheet must be stored as **lived convictions, emotional grievances, or practical survival heuristics**, not dry statutory decrees.
- **The Violation**: Giving the senior stylist the belief `"The hairdressing qualification was introduced to raise standards across the trade"`.
- **The Valid Form**: Giving the senior stylist the belief `"A bride remembers the one thing that went wrong on the day for the rest of her life, and I will not let it be her hair."`
- **Exposition Law**: A character only cites lore when it serves as **ammunition in an immediate emotional dispute or justification for an action**.

---

## 4. Rule 4: Wound Collision (The Dynamic Engine)
- **The Law**: Every scene must pair one actor's active primary drive against another actor's core psychological wound or threat trigger.
- **The Mechanism**:
  - Actor A pushes a **CARE / DEMAND** vector (the senior stylist pushes to take the bride's hair over so it holds through the photographs).
  - Actor B receives it as an **AFFRONT / THREAT** (a standing wound: *she was taken off a client halfway through once before, and told it was nothing personal*).
- **Why it matters**: If two actors have aligned goals with no friction, the engine calculates zero conversational urge and immediately drops into a `lull`. Friction generates beats.

---

## 5. Rule 5: Grounded Tangible Props
> **BACKED as of 2026-08-24**, after being unbacked for months. This rule named a `props`
> field the engine read NOWHERE — the ninth specified-but-reaching-nothing defect found
> in this repo. Props now reach the actor as percepts (`gate.perception_scope`, channel
> `visual`, fidelity 1.0, must_surface) and `scripts/lint_scene.py` enforces the 3-5
> count. Deliberately NOT perception-gated: the rule's own argument is that these are
> the plainly-present objects of the room, and gating them would withdraw the
> affordances exactly when a character most needs something to do with their hands.

---

## 6. Rule 6: Strict Epistemic Containment
- **The Law**: Strictly enforce the knowledge boundaries of a character's position — their standing, their membership, the rooms they are let into.
- **The Rule**:
  - The stylists at the chairs know only what gets said over the basins (*"the owner's been in a mood all week"*, *"there's talk of a new manager"*).
  - What is decided behind the owner's office door (*"the salon is being sold"*, *"the offer from the chain across town"*) is strictly forbidden from appearing in their character sheets or their dialogue.

---

## 7. Rule 7: Magnitudes Are Anchored, Not Tasted

- **The Law**: Every number you write in `opening_tags.dimensions` obeys the severity anchor scale
  in **`docs/standard-vectors.md` §3**. That document is NORMATIVE and owns the method for any
  number describing an event; this rule is the binding it already assumes
  (`standard-vectors.md:489` — *"opening_tags obey §2"*).
- **The Violation**: Picking a magnitude by how much the scene is *about* a thing. A senior stylist
  taking over a bride's hair is not `care_relevant: 0.9`; that band is reserved for a child dying,
  a betrayal, a rescue from real danger.
- **The Valid Form**: Size by the two author-answerable questions in §3 — **worst credible outcome
  if this runs its course** × **how live that outcome is here** — then place it:

  | magnitude | means |
  |---|---|
  | omit | the stake is not touched — the default for most dimensions of most events |
  | `faint` / `slight` / `mild` | ordinary friction: recoverable, routine, the texture of a day |
  | `moderate` | real but bounded: a genuine stake, recoverable on a normal path |
  | `marked` | a menu item genuinely at risk; the event people retell |
  | `severe` | grave: irreversible loss probable, not merely possible |
  | `extreme` | reserve it — the top of the scale leaves the engine nowhere to go |

  The words are the authored form and `src/engine/severity.py` owns their values; `scripts/scene.py`
  resolves them at the cfg parse seam, so a number still works and still means what it did. Write
  the word: the rows above used to be numeric ranges, which invited a choice between two numbers
  nobody could tell apart — the miscalibration the ladder exists to remove.

- **The trap this rule exists to prevent**: sizing a number up so that something visibly happens.
  `standard-vectors.md` §3 is explicit that **a single appraisal on a neutral sheet almost never
  changes the next staging line, by design** — `care_relevant` needs ≈0.69 merely to leave a
  visible next-beat trace, and a measured spider event moved FEAR 0.25 → 0.329 with a
  byte-identical staging line. Inflating the vector to force motion is anti-pattern §10.1.
- **What to reach for instead when a scene lulls**, in the order §3 gives: the **event text**
  (route R1, the strongest lever by a wide margin), then a catalog row, then accumulation under a
  sustained cause, then the arc. The event vector is first the RECORD and the arc currency, only
  secondarily a same-scene theatrical dial.
- **Enforcement**: unmechanized. `lint_scene.py` checks no magnitudes. Read §3.

**Legal dimension keys** — only these seven, from `state._DIM_TO_PATH`: `attraction`,
`care_relevant`, `loss`, `mastery`, `relief`, `social_violation`, `threat`. Anything else is
dropped by `validate_tags` as an unknown dimension.
