# Scene Blueprint — the authoring contract every book writes against

A **Scene** is the fundamental unit of simulation. A blueprint establishes the physical
circumstance, who is present, and what each person is doing or wanting, then lets them live
through the moment organically in any mode — calm, atmospheric, technical, sparring, social,
triage, crisis.

This document and its companion, `actor-direction-format.md`, are the two contracts a book
references to know what the engine needs. This one covers **what the author writes**; that one
covers **what the actor receives**. Neither is book-specific: every example here uses the repo's
own fixtures (`characters/*.json`, `world/ashford-slice.json`, and the invented default scene in
`scripts/scene.py`).

---

## The rule that governs the whole document

**The engine reads the cfg JSON. It never reads your markdown.**

Anything you author in a blueprint that does not appear in the §7 payload reaches no actor. That
is not a bug to route around; it is the seam. But it means a blueprint section can look like a
constraint while binding nothing — the repo's own recurring defect class, written up in
`learnings/2026-07-29-a-documented-key-with-no-reader-is-a-lie-with-a-citation.md`.

So every section below is labelled:

- 🟢 **ENGINE** — compiled into the cfg, reaches the actor.
- ⚪ **AUTHOR** — for you, the critic, and continuity. Reaches nothing. Fine, as long as you are
  not relying on it to constrain a character.

Ship every scene as a **pair**: `Scene_<id>_Blueprint.md` (this form) and `scene_<id>_cfg.json`
(§7 extracted). If a field is in the blueprint and not in the cfg, it does not exist.

---

## 1. Staging & Environment

- 🟢 **POV Actor** — `[character_id]`. Close third-person focaliser. Must be in `cast`.
- ⚠ **Location ID** — `[location_id]`, registered in the book's world note under `locations`.
  Goes in the cfg as `"location"`. **Setting it puts the cast there** — it is the scene's staging.
  - `gate.perception_scope` receives it: `scripts/scene.py` builds `scene_slice["location"]` from
    the cfg, falling back to the acting character's own `current.location` when the cfg omits it.
    So the cast perceives the place you stage the scene at, and a cfg with no location behaves
    exactly as before.
  - `bible.verdict_for(..., location=…)` receives it in the pre-flight when the cfg also sets a
    top-level `act`, AND on every reported act during the scene.
  - `scripts/lint_scene.py` checks it is a registered id.

  > **History, so it does not get re-broken.** Until 2026-08-30 the percept builder read the
  > character sheet and the cfg value reached only the pre-flight, itself behind an `if _act:`
  > guard most scenes never set — so a scene staged at the fold handed both actors the mill's
  > description while its own prose described a hillside at dusk. This paragraph previously
  > documented that as a design property and told authors to set each sheet by hand. It was a
  > defect, and it is fixed.
- 🟢 **Present Cast** — `["actor_1", "actor_2"]`. Each needs a sheet in `characters/` **and** an
  entry in `world.people`. A character is not automatically an entity: `vault.load_book` builds
  `world.people` from `people/*.md` notes only. Missing that entry, the other actor in the room
  cannot perceive them.
- ⚪ **Mode / Tone** — atmospheric / domestic / technical / sparring / social / conflict / triage.
  Your framing for the composition pass. Not a cfg field.

### Tangible Props (3–5 objects) — 🟢 ENGINE, and the most-missed field

List the physical objects in the space. They go in the cfg as a **flat array of strings**:

```json
"props": ["a tin lamp guttering on the sill", "the ledger, open to a page nobody has signed"]
```

`scripts/scene.py:101` normalises the array; declared props then "reach the actor as percepts via
`gate.perception_scope`" (`scene.py:98`). **Absent the `props` key the array is empty and the
objects do not exist to anyone** — the only remaining way a prop reaches an actor is if it also
appears in the `situation` prose.

Write props as **phrases an actor could perceive**, not as identifiers. `timber_window_north` is a
key; *"a timber window over the wet alley, its shutter unlatched"* is a percept.

**Check before shipping:** does any actor's drive reference an object? Then that object must be in
`props` or in `situation`. A drive of *"gauge the window and door exits"* against a cfg with no
props directs a character at furniture they cannot see.

---

## 2. The Single Tension (sizing rule) — ⚪ AUTHOR

One pressure per scene, in one sentence. If you need two sentences joined by "and", it is two
scenes. This is the sizing test, and it is the difference between a link that exits at eight beats
and one that lulls at two.

---

## 3. Cast & Drives — 🟢 ENGINE (and it overwrites, so write it carefully)

One `drive` per actor: a natural, in-the-moment, **blind-to-outcome** want or activity.

```json
"cast": [{"id": "arden", "drive": "not raise the valley over a girl who is probably sheltering somewhere dry"}]
```

Two mechanics you are working against, both at `scripts/scene.py:249`:

```python
ch["current"]["active_goals"] = [{"goal": c["drive"], "urgency": 0.8}]   # the scene DRIVE overrides sheet goals
```

1. **The drive replaces the sheet's standing goals for the whole scene.** An authored three-goal
   stack is not blended with the drive; it is gone. So the drive must carry whatever of the
   character's standing wants still matters in this room. If a long-running goal is load-bearing
   here, say it in the drive.
2. **Urgency is hardcoded 0.8 for every actor in every scene.** You cannot express "he wants this
   badly, she barely does" through drives. Relative pressure is expressed through
   `opening_tags.dimensions` (§5), which is what actually decides who speaks first.

Write drives as **physical goals, not topics.** Measured on a real book: same cast, same sheets,
zero numbers changed — moving one character's drive from a topic to a physical goal took the scene
from *lull at 2 beats* to *exit at 8*, with urges climbing 0.29 → 0.40 → 0.53. One observation, not
a replication, but the tuning arm was never what moved it.

---

## 4. The Wound Collision Matrix — ⚪ AUTHOR

Name the vector each character brings and why the scene will not lull: whose want collides with
whose boundary. This is your check that §2's pressure is real before you spend a run on it. The
engine derives its own version from the sheets; this section does not feed it.

---

## 5. Opening Tags — 🟢 ENGINE (`dimensions` only)

```json
"opening_tags": {"type": "mundane", "dimensions": {"threat": "slight", "care_relevant": "marked"}, "durability": "durable"}
```

A number still works and still means what it always did — `scripts/scene.py` resolves the word
at the cfg parse seam, so nothing authored before the ladder changed. Write the word: the point
of the ladder is that choosing between 0.45 and 0.5 is a choice nobody can defend, and the two
forms hash identically, so switching one for the other never reads as cfg drift.

- **`dimensions`** — 🟢 the live field. Legal keys, and only these seven:
  `attraction`, `care_relevant`, `loss`, `mastery`, `relief`, `social_violation`, `threat`.
  They decide **opening salience** — which actor gets the first beat (`scripts/scene.py:281`) — by
  appraising the opening event against each listener's profile.

  **Size them against `standard-vectors.md` §3, which is normative and owns this** — do not
  calibrate by feel, and do not treat the summary below as the source:
  a WORD, not a number: `faint` · `slight` · `mild` ordinary friction · `moderate` real but
  bounded · `marked` the event people retell · `severe` grave, irreversible loss probable ·
  `extreme` reserve it. Omission is the default for most dimensions of most events, and a word you
  cannot defend against its neighbour is a word to leave out. `scene-authoring-rules.md` Rule 7
  states the binding; `scripts/scene.py` resolves the word to its value at the cfg parse seam, so
  a number still works and means exactly what it always did.

  **Do not inflate a magnitude to make something happen.** §3 is explicit that a single appraisal
  on a neutral sheet almost never changes the next staging line, *by design* — `care_relevant`
  needs ≈0.69 just to leave a visible next-beat trace. When a scene lulls, the lever is the event
  text (route R1), not the vector; see §3's ordering and anti-pattern §10.1.
- **`type`** — ⚪ **inert.** Not validated, and it does not affect appraisal. Measured: six
  different type strings against identical dimensions produced identical salience (0.2595 each),
  including two invented ones and `betray`. `appraise` reads `dimensions` and never `type`.
  Two vocabularies exist and neither is a cfg-side constraint: `consolidation.CATALOG` holds 17
  rows (affront, aid, betray, bond, care, correction, destroy-asset, harm, loss, move, mundane,
  reveal, seize, tension, threat, threaten, turn-skipped), while an **actor** may self-tag only the
  6 pure-appraisal rows — `affront, aid, care, loss, mundane, threat`. If you set a type, use a
  CATALOG row so it reads honestly to a human; the engine ignores it either way.
- **`durability`** — `transient` | `durable`. `durable` is rare: an event that would change a
  person for years.
- **`subject`** — 🟢 `["actor_id", "group"]`. Who the moment is *about*. Scales the empathy
  dimensions (`care_relevant`, `loss`) by each listener's regard for that subject.

---

## 6. Epistemic Boundaries & Forbidden Lore — ⚪ AUTHOR (**enforced by nothing**)

State what is known in the room and what is off-limits — then be honest about what this section is.

**No code reads it.** The only mechanical epistemic enforcement is `gate.scope_names`, which masks
the *name* of anyone this actor has not acquired: a name never acquired never reaches the model.
Everything else is a sentence in the prompt instructing the model to *"act ONLY on what is here; do
not invent people, outcomes, or WORLD facts beyond it."*

So a forbidden-lore list is a **discipline for the author**, and the discipline is: keep the
forbidden thing out of `situation`, out of `props`, out of every `drive`, and out of the world
note. If it is not in the compiled cfg and not in the world bible, the actor cannot reach it.

Two related facts worth knowing while you are here:

- `world.standing_facts` is **inert to perception** (`src/engine/gate.py:101-104` — "read only by
  the out-of-loop critic, never by perception"). A fact that must reach an actor goes in the event
  text or a vault belief. It does not arrive by being true in the world.
- A plot outline misfiled into the book's `world/` directory is inert as long as it carries a
  `type:` that is not `world` — the filter is `vault.py:116`, `(n["type"] or "world") == "world"`.
  An **untyped** note there defaults to world, which with a real world note present makes
  `load_book` raise (`found 2`) rather than leak. The one leaking case is an outline that is the
  *sole* world-typed note. Outlines belong in `chapters/`; see `new-book-manifest.md` for the full
  table.

Format:

- **Known in the room**: …
- **Strictly forbidden**: … *(then verify each term appears nowhere in §7)*

---

## 7. The Simulation Engine Payload — 🟢 the only thing that runs

```json
{
  "name": "scene_<id>",
  "location": "<location_id registered in the book's world note>",
  "situation": "<Plain-text circumstance, environment and sensory ground. No scripted lines.>",
  "props": [
    "<a perceivable phrase, not an identifier>",
    "<3-5 of them>"
  ],
  "subject": ["<actor_id>", "<group>"],
  "opening_tags": {
    "type": "mundane",
    "dimensions": { "threat": 0.0, "care_relevant": 0.0 },
    "durability": "transient"
  },
  "elapsed": 0,
  "cast": [
    { "id": "<actor_1>", "drive": "<physical, in-the-moment, blind to outcome>" },
    { "id": "<actor_2>", "drive": "<physical, in-the-moment, blind to outcome>" }
  ]
}
```

**Required** — `load_scene_cfg` fails loud without them: `situation` (non-empty string), `cast`
(non-empty list, every entry `{id, drive}`).

**Optional but consumed**: `name`, `location`, `props`, `subject`, `opening_tags`, `elapsed`.
`elapsed` is how much time the director says has passed since the last scene, in the director's own
unit; it relaxes every cast edge toward its resting prior.

Anything else in the object is carried and read by nothing.

---

## 8. Post-Sim Narration & Transition Seam — ⚪ AUTHOR

- **Value shift**: the scene's (+ / − / 0) movement, for the chapter ledger.
- **Director-placed transition**: the physical event that ends this link and opens the next. You
  place it in the *next* scene's `situation`; the actors never generate it.

---

## Pre-flight checklist

1. Does `cfg.location` exist and match a registered location?
2. Does `cfg.props` exist, containing every object any drive references?
3. Is every `cast[].id` both a `characters/` sheet **and** a `world.people` entry?
4. Are all `dimensions` keys drawn from the legal seven?
5. Does the forbidden-lore list appear nowhere in `situation`, `props` or any `drive`?
6. Is there exactly **one** pressure in §2?
7. Is every drive a physical goal rather than a topic?

`scripts/lint_scene.py --book <book> --scene <cfg>` covers the mechanical subset. Items 5–7 are
yours.
