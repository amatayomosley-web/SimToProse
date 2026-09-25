# Actor Direction Format — what an agent actually receives

This is the **Tier 2 → Tier 3 contract**: the exact shape of what reaches one actor's decision
engine on a single turn, and where each part comes from. It is the companion to
`template-scene-blueprint.md` — that document covers what the author writes, this one covers what
the actor is handed. Together they are what a book references to know what the engine needs.

Transcribed from `src/engine/prompt.py:build_turn_messages` and rendered with the repo's own
fixture (`characters/maren-healer.json`, `world/ashford-slice.json`), not paraphrased.

Two messages per turn. Nothing else reaches the model.

| | Message | Lifetime | Source |
|---|---|---|---|
| 1 | **system** — the identity prefix | stable, cacheable, built once per character | `fixed` + `baseline` via `scene._build_stable` → `identity_view.direct_identity` |
| 2 | **user** — the volatile body | rebuilt every beat | the packet's `volatile` half + the moment |

Both are passed last through `gate.scope_names(text, relationships)`, which masks — across the
whole prompt, identity and recall and edges and moment alike — the name of anyone this actor has
not acquired. **A name never acquired never reaches the model.** That is the one epistemic
boundary enforced by code rather than by instruction; the canonical id stays engine-side.

---

## The law that governs both messages

> `design.md`: **"The LLM never sees raw stats."**

Every `[0,1]` scalar becomes a phrase before serialisation. `identity_view._say_scalars` makes this
true *by construction* — it recurses the whole structure and bands anything left over by field
name, rather than relying on a hand-written renderer per field. A number outside `[0,1]` raises
rather than passing through, because that is not a weight, it is something else wearing a float.
The guard is `tests/test_no_digits.py`.

Two consequences for authors:

1. **You tune behaviour by writing a different life, not a different decimal.** The actor cannot
   see that you moved a weight from 0.6 to 0.7 — only that the band changed, and most small moves
   do not change the band at all.
2. **A new numeric field is a five-minute phrase table, not a silent loss.** `direct_identity`
   *carries* keys it has no renderer for and then refuses the packet by path name. Silent dropping
   would be worse than leaking: the guard comes back green and the next authored field disappears
   with it.

---

## Message 1 — SYSTEM (the identity prefix)

```
You ARE the person defined below. Be them, faithfully — including hesitating, over-controlling,
or refusing when that is true to them. Do not perform a story; do not resolve drama; just be them.
IDENTITY (stable):
{ ...json, sort_keys=True... }
```

The JSON is `direct_identity(stable)`. It keeps the sheet's **structure** — the model already
parses that shape reliably — and replaces only the values. Real rendered output for the Ashford
healer fixture, abridged:

```json
{
 "disposition": {
  "agreeableness": "you give people the benefit of the doubt",
  "conscientiousness": "you cannot leave a thing half-done",
  "emotionality": "you feel things hard and they stay a while",
  "extraversion": "you speak when spoken to",
  "honesty_humility": "you keep to your word when it costs you",
  "openness": "you try a new thing when it is put in front of you"
 },
 "what has marked you": [
   {
    "about": "illness in a body — fever, plague, a sore that will not heal",
    "what happened": "her daughter Súil died of a fever she could not break (Maren age 31)",
    "how it takes you": "it takes you over",
    "what sets it off": ["a child with fever", "a patient she might lose"]
   }
  ],
 "drives": {
  "goals": [
   { "goal": "keep the valley's people alive and whole",
     "how much": "something you mean to get to",
     "priority": "nothing you want outranks this",
     "satisfaction": "this is mostly where you want it" }
  ]
 },
 "how you are built": { "...": "genotype alleles as reactivity, e.g. 'you are afraid before you know why'" },
 "what you weigh": {
   "you will not trade these away": ["...top-ranked, pooled across schwartz / moral_foundations / needs..."],
   "these weigh little with you": ["...bottom-ranked..."],
   "how you hold each people": { "<group>": "you take them as they come" }
 },
 "persona": { "id": "...", "name": "...", "position": { "...place · class · era · niche..." } },
 "voice": { "...authored strings, passed through untouched..." }
}
```

### Where each block comes from — and its trap

| Block in the prompt | Authored at | Trap |
|---|---|---|
| `disposition` | `baseline.traits.<facet>.mean` | HEXACO facet **means** only. `variability` is a sampling parameter and is dropped — it is not self-knowledge. |
| `how you are built` | `fixed.genotype` | Only the six known alleles render. `typical` deliberately has **no phrase** — an unremarkable allele is not self-knowledge, and it vanishes by design rather than by accident. |
| `what you weigh` | `baseline.model.{schwartz,moral_foundations,needs}` | Ranked, not banded, and **pooled across all three families** — ranked per family, a character with three authored values had all three returned as things they would not trade away, including one at 0.15. Only weights that *depart* from 0.5 rank at all; an authored 0.5 is "average" and is correctly invisible. |
| `drives.goals` | `baseline.drives` | Each authored weight becomes a phrase. Two weights on one goal become two independent phrases and **can disagree** — see Known quirks. |
| `what has marked you` | `baseline.wounds` (engine state since 2026-09-11 — the old `drives.fears_wounds` prose block is retired and refused by lint) | One entry per wound: the concept's gloss (never its id), what happened, the intensity banded into one of four sentences, the perceived words that set it off. The path the wound is keyed to is the engine's and is dropped. |
| `persona`, `voice` | `fixed.persona`, `fixed.voice` | Strings, passed through untouched. **`fixed.position` (place · class · era · niche) is the live slot** — content filed under `formative.*` reaches nothing, because `_build_stable` reads `fixed` + `baseline` only. |

---

## Message 2 — USER (the volatile body)

Nine parts, in this order (corrected 2026-09-19 — this template drifted to list `{RECALL}` twice
and omit `{HOLDS}`; it was seven parts before `{ESTABLISHED}` (2026-09-11) and `{HOLDS}`
(2026-09-19) joined, and eight before `{FACTS}` (2026-09-22)). This is the concrete form of the seven operands, plus the two knowledge-fence
additions below.

```
How to play this moment - stage directions, drawn from your state. Act on them;
they are what you DO, not a mood to describe: {STAGING}
Active goals: {GOALS}
What you perceive THIS moment (your whole knowledge of the scene — act ONLY on what is here;
put no one new in the room, and decide nothing for anyone else or for what happens next. Your own
interior is yours: memories, feelings, the texture of what you carry may surface freely):
{PERCEPTS}
What it brings to mind: {RECALL}
What is established about who and what is here — the world's facts; do not contradict them. Beyond
them, speak as someone who knows their world: name things, recall customs, fill in what a person of
your station would know. What you say binds nothing until it is kept: {ESTABLISHED}
What is yours here: {HOLDS}
What has happened here, as you saw it (most recent first, from beats you were in the room for.
What changed hands you saw happen: act consistently with it. What was said is only what you heard
said, not proof that it is true): {FACTS}
Those present, as you stand with them: {EDGES}
The moment: {EVENT}
Reply as ONE JSON object: { ...contract... }
```

### 1. `{STAGING}` — the selected rung blocks, then condition

`composer.direction_for(...)` + `direct_condition(condition)`. Read from the **effective** levers
rather than raw affect — what the decision actually sees after context (`state-engine.md:12`).

**RETIRED 2026-09-08: `direct_affect` and the band-phrase tables.** This slot used to carry an
exhaustive per-primary clause list — *"you give ground, you hedge, you commit to nothing you cannot
leave; ..."* — alongside the rung blocks. The two were in CONFLICT, not merely redundant:
`direct_affect`'s contract was *"every primary is described or the actor is told less is happening
than the state says"*, while the composer's is *"SELECTION — which two or three of a character's
live emotions this beat is played on"*. The exhaustive line re-supplied precisely what the selection
had chosen to leave out. The engine now runs one form.

Real output for the fixture (`--fixture ashford --char ren-traveler`), abridged at the bullets:

> *Your state as you come into this moment. This is what is true inside you; it is not a list of
> actions and it does not tell you what to do. Act from it.*
>
> *Your day has arranged itself around them. It is not one act now but a standing orientation; what
> you do and when has started to answer to how they are. Outwardly your choices have a centre, and
> it is them. What would take this away is them no longer needing anything.*
>
> *- **The Sensation.** A constant low readiness. Ease only when they are seen to.*
> *- **The Belief.** What they need has moved to the front. First them.*
> *- **The Impulse.** To see to them.*
>
> *Also true of you right now. ...* [second block] *... Also true of you right now. ...* [third]
>
> *You can do the thorough version where it matters.*

**At most three blocks reach an actor** (`composer.select_deterministic`, cap 3), primary first,
each under its own lead. The rung NAME and index never appear — measured 2026-09-07, the label is
inert, and identical text under a WRONG label scored higher than under its own.

**A primitive with no built ladder is silent here.** That is the composer's stated doctrine — *"a
designed-but-unbuilt path is ABSENT, NOT EMPTY"* — and it currently means **LUST and PLAY produce
no emotional direction at all**: LUST has no `PATH_SOURCE` entry (a lookup retired 2026-09-08), and PLAY's LEVITY ladder is
recorded NOT BUILT BY DECISION in `docs/rungs/LEVITY.md`.

**Three things this slot no longer says**, retired with the renderer and not expressible by any
rung block (measured: 0 of 83 encode them): deviation from the character's own temperament mean
(*"more than is usual for you"*), slope since the previous turn, and target-sensitivity — the
reflexive variant and the unbound-LUST phrase. `ledger.previous_affect` still records the movement
data; only the rendering is gone.

### 2. `{GOALS}` — `direct_goals(volatile.goals)`

```json
[{"goal": "have the upper beds shared out by seniority tonight", "how much": "pressing on you"}]
```

**In a scene run this is the cfg `drive` and nothing else** — `scripts/scene.py:249` replaces the
sheet's standing goals for the scene's duration, at a hardcoded urgency of 0.8. Write drives
accordingly; see `template-scene-blueprint.md` §3.

### 3. `{PERCEPTS}` — `direct_percepts(volatile.percepts)`

Built by `gate.perception_scope(scene_slice, world, skills, condition, relationships)` from the
event text, the recent transcript, the **location**, and the cfg **props**. Each percept carries
`"how well you caught it"` in place of a raw `fidelity` float — how well you caught a thing is
state an actor should feel rather than read.

This is the actor's *whole* knowledge of the scene. An object neither in `props` nor in the
situation prose does not exist to them.

### 4. `{RECALL}` — the vault

`claim (provenance — sureness)`, joined by `;`. Empty renders as *"nothing in particular"*.
Beliefs are parsed from the character note's `## Beliefs` section by `_BELIEF_RE`
(`src/engine/vault.py:22`), contract `- (confidence, provenance) claim`. Bullets that do not match
raise rather than loading as zero beliefs — the section fails loud instead of silently emptying.

This is also the only carrier for state that must survive across runs: a run's DB is per-run, so a
debt, a grudge or a thing learned in a previous pass reaches the next one as an authored belief or
not at all.

### 5. `{EDGES}` — the relationship ledger

`label: direction` per present party, from `current.relationships`. Empty renders as *"no one in
mind"*.

Since 2026-09-11 the line also says what a present person STIRS, and since 2026-09-12 that is the
BALANCE: what they move the played state by relative to the mood — `toward.balance`'s
`effective − mood` for that person, set on the edge by `scene.assemble` as `stirs` and rendered by
`direction.direct_stirs`: the one or two largest entries as plain phrases (*"you go soft near
them"*, *"they get under your skin"*; a cooler person met halfway down reads as a lowering, *"they
take the heat out of you"*), with *"a little,"* below `_STIRS_PLAIN` and nothing at all below
`_STIRS_FAINT`, so a person met exactly at the mood adds no words. Rung names never appear here
(the composer withholds them from the actor by measurement); the word *toward* never appears
either — `tests/test_toward.py` [6] holds that guard, which is why the edge key is `stirs`. The
state block the actor plays is the composed vector (`volatile.state.effective`) — the engaged
person's, with the mood met in full by whom it is about — never the stored mood alone.

For B to reach A's turn, four things must all be true: a `world.people` entry for B, B's first
name in the event text, A's insight ≥ 0.55, and `A.current.relationships["b"]` keyed by the same
id. **Adding a character is a four-place transaction, not one file.** A fully playable character
missing the `world.people` entry is invisible to the person they are talking to.

### 5b. `{HOLDS}` — what is yours here

`direction.direct_holds(volatile.holds)`. `scene.assemble` scopes `current.attachments`'s `+`
entries to this turn — a held place that is also a percept (a `loc.` ref) or the beat's own
subject/target — and prices each to a relation word with `attachments.word_of`, the inverse of
the table `hold_of` prices FROM. The render is `"<name> — <phrase>"` per row, joined by `; `;
empty is *"nothing here is yours"*, a fixed phrase rather than an omitted section, so the
section-boundary tests can bound on the label whether or not this character holds anything this
turn.

The trap: a number must never leak here either. `word_of` refuses a hold below `acquainted`'s
floor (`ATTACH_HOLD_UNWORDED`) rather than inventing a fifth, colder word for it, and
`direct_holds` refuses a word off the four-entry table (`DIRECTION_HOLD_WORD_UNKNOWN`) rather
than rendering the raw word or the hold that priced it. `test_no_digits` and
`test_prompt_sections` police the line the same way they police every other one.

### 6. `{FACTS}` — what has happened here, as you saw it

The facts of this run that THIS actor witnessed, most recent first, digit-free, in two registers
(`src/engine/scene_facts.py` folds and filters; `direction.direct_facts` renders). **What changed
hands** comes from the event seat's `transfers` and is what the actor saw happen, so it is asked to
act consistently with it. **What was said, as you heard it** comes from the seat's `told` and is only
what was said: a quote of speech, which may be false, misheard or a lie, and is never rendered as
settled fact. Example (invented, hard rule 1 — two birdwatchers out on a heath): *What changed hands:
you handed the flask to Imke; Imke lent the binoculars to you. What was said, as you heard it: Imke
told you: the harriers are back past the gorse.*

**Point of view is the contract.** An actor receives a fact only from a beat it SPOKE or was
PRESENT for. Presence is the engine's own rule, `presence.present_ids` — a percept marked
`present: False` is someone spoken of, not someone in the room — recorded per beat in the
manifest's `present` key. A manifest older than that key is read through its present-only
`edges`: lossy for a present person with no relationship record, never a leak. The first version
read every `entity.<id>` percept key as a witness and so handed a person merely spoken of the facts of
a room he was never in; `tests/test_scene_facts.py` now tests that case first, against an oracle it
does not share with the code.

**Budgets are per kind and never split a beat:** `passed` 24, `told` 6 (both judgments, the first
anchored on a measurement recorded in the module), so a run of speeches cannot push a loan off.

**Why this section exists, measured and independently re-checked.** Of the 13 continuity flags a
model critic raised on the first real prose (2026-09-18), TEN contradict a beat that had already left
the transcript window below. The other three were in view, and in each the actor contradicted its own
immediately preceding beat — the transcript is not consumed as state at any width. The section whose
label promised memory, the long-term recall tier, does not follow the beat.

**Not carried here:** an object's STATE (a door left open, a candle put out) has no producer. Where
someone is looking is out of scope. **Known open defect:** when the event seat quotes one act at two
beats, the ledger shows it as two; this is a pre-registered failure condition of the controlled
re-answer, not yet designed away.

### 7. `{EVENT}` — the moment

The standing `situation` plus a rolling transcript of the last four beats. Its documented job is
ANTI-REPETITION — so the actor can see what they have already said and not repeat it — and since
2026-09-22 that is all it carries: continuity is section 6's, which is bounded by what happened
rather than by a beat count.

### 8. The epistemic horizon

Not its own section — it is the parenthetical inside `{PERCEPTS}` plus `scope_names`. Names are
enforced mechanically; everything else is instruction. See `template-scene-blueprint.md` §6.

---

## The reply contract

The actor must return **one JSON object**:

```json
{
  "action": "what you do or say",
  "thought": "your private inner line",
  "exit": false,
  "addressee": "",
  "tags": {
    "type": "",
    "summary": "",
    "subject": "",
    "dimensions": {"attraction": 0.0, "care_relevant": 0.0, "loss": 0.0, "mastery": 0.0,
                   "relief": 0.0, "social_violation": 0.0, "threat": 0.0},
    "durability": "transient|durable",
    "confidence": 0.0,
    "attribution": ""
  },
  "act": ""
}
```

The social block was retired 2026-09-17 (bond-arithmetic.md §2, `APPRAISER_SOCIAL_RETIRED`) and
removed from the actor's own reply contract 2026-09-19 (gate `actor-contract-cleanup`).

- **`tags.type`** — exactly one of **`affront, aid, care, loss, mundane, threat`**. Narrower than
  the 17-row `consolidation.CATALOG`: an actor may only self-tag pure-appraisal rows that fold
  nothing into the world, and system rows (`turn-skipped`, `correction`) are the engine's own
  records, never an actor's claim. Rules stated in the prompt: if real danger is present the type
  is `threat` even during care work; a slight, insult, dismissal or status conflict is `affront`;
  never combine types.
- **Tags report what OBJECTIVELY happened**, not how the actor feels about it — temperament
  amplifies downstream, so pre-amplifying double-counts. Calibration given to the actor: most
  moments are `faint` or `mild`, or omit the dimension entirely; reserve `marked` and above for an event that would genuinely change someone.
  `durable` is rare — only something that would change a person for years.
- **`addressee`** — the id of the one present party spoken *to*. Distinct from `tags.subject`,
  which is who the moment is *about*.
- **`attribution`** — optional; `accident` / `coerced` / `negligence`, when the act was not
  deliberate. Left empty the act reads as intended, which is usually right.
- **`act`** — injected **only when the world declares laws**. A closed list drawn from those laws;
  empty is allowed and is right for most beats. It exists so a law can be keyed to what happened
  after the fact: `bible.verdict_for` runs at `scripts/scene.py:194,229` and records teeth for
  violations. It runs *after* the beat and never retracts the turn — the log is append-only, and a
  correction is a new event. Refusing an impossible act is the pre-flight's job, before the beat.
- **The weighing is the point.** If the stage directions pull in different directions, `thought`
  **must** name the pulls it is resolving and which one wins. If they agree, say what you are doing
  and no more.
- **`exit`** — true only if the action is to physically leave the scene now. Only a JSON `true` exits: the
  reply's record (`src/engine/replies.py`, `actor_reply`) reads `"exit": "false"` as staying, where `bool()` once
  walked the character out.

**How the reply is read** (gate actor-reply, 2026-09-25). One record for both ways a reply arrives:
`replies.actor_reply`. A key the contract above does not name is kept on the record, written to the committed
turn's validation record (`turns.validation`, as `reply_extra`) and reported - never refused, since nothing reads it
and a refused reply costs a paid retry; a beat that is skipped, or a draw the retry loop throws away, commits
nothing, its extra keys with it. A reply the engine draws from its own model and that holds no JSON object is an
empty draw, which the retry loop redraws; a null action or thought is empty, never the word "None". A turn supplied
through `--turn-json` (`{action, thought, tags, exit?, addressee?}`, plus `act?` for the scene driver - the chair
keys no law by an act, and says so) has its shape checked before anything is opened and is refused by name:
`REPLY_NOT_AN_OBJECT`, `REPLY_FIELD_MISSING`, `REPLY_FIELD_TYPE` (a null optional field is absent). Its tags'
content is checked where the tags are used, as ever.

---

## Known quirks, verified 2026-08-28

1. **Two weights on one goal can disagree.** The fixture's top goal renders as
   `"how much": "something you mean to get to"` (from `urgency`) beside
   `"priority": "nothing you want outranks this"`. Both are faithful to the sheet; together they
   read as contradictory. Author `urgency` and `priority` as one story, or expect the actor to
   split the difference.
2. **~~Spacing artifact in `{STAGING}`~~ — GONE 2026-09-08.** It was a property of the two-part
   `"%s. %s."` join with `direct_affect`, which is retired. The slot is now the blocks followed by
   the condition sentence, whose first letter is lifted because those phrases were authored to
   follow a `you …` clause.
3. **`opening_tags.type` never reaches an actor** and does not affect appraisal. Only
   `opening_tags.dimensions` does anything.
4. **`world.standing_facts` never reaches an actor** (`src/engine/gate.py:106-109`, re-pointed
   2026-09-19 — was :101-104). A fact that must be known goes in the event text or a vault belief.
5. **`formative.*` is read by no engine code.** Culture, class and genotype filed there reach
   nothing; `fixed.position` is the live slot.

## The lore licence (2026-09-11)

The owner: *"I legitimately want them to make up lore in their turns, but only when that specific
info isn't established."* Three moves, all built:

1. **The fence.** `{ESTABLISHED}` is `read_api.established` over the beat's subjects (the present
   cast, the place, whoever acted): per subject the authored bible line and every KEPT saying —
   utterances whose folded tier is authored or established (`claims.py`). A subject with neither is
   named as *nothing is yet established about … — that ground is yours*. Superposed claims are not
   in it: they bind nothing, and handing them on as facts would make every offhand line canon.
2. **The licence** replaces the old *do not invent people, outcomes, or WORLD facts*. Two fences
   stay (no one new in the room; nothing decided for others or for what happens next); the third
   is now drawn by the facts. What the actor says enters the log SUPERPOSED, as before.
3. **The keeper at the canon gate** (`scripts/scene.py --keeper`): the noticing pass records what
   was said with its extracted facts, the ruling pass collapses what was tested to established or
   fiction (`scripts/keeper.py --rule`; `claims.resolve`). Established sayings are in the next
   packet's fence. Under `--stub` nothing is asked and the contested claims are printed.
