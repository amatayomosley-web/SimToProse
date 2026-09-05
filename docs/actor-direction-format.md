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
 "drives": {
  "fears_wounds": [
   {
    "wound": "her daughter died of a fever she could not break",
    "how it takes you": "it catches you sometimes",
    "trigger": ["a child with fever", "a patient she might lose", "being asked to trust someone else with a life"],
    "avoidance": ["over-control / cannot delegate", "will not name the grief aloud", "works past exhaustion rather than stop"]
   }
  ],
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
| `drives.goals`, `drives.fears_wounds` | `baseline.drives` | Each authored weight becomes a phrase. Two weights on one goal become two independent phrases and **can disagree** — see Known quirks. |
| `persona`, `voice` | `fixed.persona`, `fixed.voice` | Strings, passed through untouched. **`fixed.position` (place · class · era · niche) is the live slot** — content filed under `formative.*` reaches nothing, because `_build_stable` reads `fixed` + `baseline` only. |

---

## Message 2 — USER (the volatile body)

Seven parts, in this order. This is the concrete form of the seven operands.

```
How to play this moment - stage directions, drawn from your state. Act on them;
they are what you DO, not a mood to describe: {STAGING}
Active goals: {GOALS}
What you perceive THIS moment (your whole knowledge of the scene — act ONLY on what is here;
do not invent people, outcomes, or WORLD facts beyond it. Your own interior is yours: memories,
feelings, the texture of what you carry may surface freely):
{PERCEPTS}
What it brings to mind: {RECALL}
Those present, as you stand with them: {EDGES}
The moment: {EVENT}
Reply as ONE JSON object: { ...contract... }
```

### 1. `{STAGING}` — affect + condition as stage directions

`direct_affect(effective, temperament, targets, me)` + `direct_condition(condition)`. Rendered
from the **effective** levers rather than raw affect — what the decision actually sees after
context (`state-engine.md:12`). Real output for the fixture:

> *you ask the next question and reach for the next step; you give ground, you hedge, you commit to
> nothing you cannot leave; you put yourself between them and it, and what you wanted for yourself
> does not survive this; you lose the thread of what you were doing, and you leave it where it
> fell. you do what is asked and none of the extra*

These are **instructions to act**, deliberately not reports of feeling — second-person imperative,
never "You are…". A primary surfaces only if it is at present level or above, or deviating past
threshold from its resting mean with a rising/settling marker, so an anxious baseline does not read
as a fresh spike and a primary in the quiet band is genuinely not asking for attention.

### 2. `{GOALS}` — `direct_goals(volatile.goals)`

```json
[{"goal": "get lanterns and bodies onto the upland road tonight", "how much": "pressing on you"}]
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

For B to reach A's turn, four things must all be true: a `world.people` entry for B, B's first
name in the event text, A's insight ≥ 0.55, and `A.current.relationships["b"]` keyed by the same
id. **Adding a character is a four-place transaction, not one file.** A fully playable character
missing the `world.people` entry is invisible to the person they are talking to.

### 6. `{EVENT}` — the moment

The standing `situation` plus a rolling transcript of the last four beats, so the actor can see
what they have already said and not repeat it.

### 7. The epistemic horizon

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
    "attribution": "",
    "social": {}
  },
  "act": ""
}
```

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
- **`social`** — optional; how the act would read to a watcher on `trust` / `affinity` / `respect`
  / `debt`, each 0..1 with 0.5 neutral. Reports what the act *shows*, never what the actor wants
  concluded.
- **`act`** — injected **only when the world declares laws**. A closed list drawn from those laws;
  empty is allowed and is right for most beats. It exists so a law can be keyed to what happened
  after the fact: `bible.verdict_for` runs at `scripts/scene.py:194,229` and records teeth for
  violations. It runs *after* the beat and never retracts the turn — the log is append-only, and a
  correction is a new event. Refusing an impossible act is the pre-flight's job, before the beat.
- **The weighing is the point.** If the stage directions pull in different directions, `thought`
  **must** name the pulls it is resolving and which one wins. If they agree, say what you are doing
  and no more.
- **`exit`** — true only if the action is to physically leave the scene now.

---

## Known quirks, verified 2026-08-28

1. **Two weights on one goal can disagree.** The fixture's top goal renders as
   `"how much": "something you mean to get to"` (from `urgency`) beside
   `"priority": "nothing you want outranks this"`. Both are faithful to the sheet; together they
   read as contradictory. Author `urgency` and `priority` as one story, or expect the actor to
   split the difference.
2. **Spacing artifact in `{STAGING}`.** The line is assembled as `"%s. %s."` and `direct_affect`
   can return a string already ending in whitespace, producing `"… where it fell . you do what is
   asked"`. Cosmetic, present in every prompt.
3. **`opening_tags.type` never reaches an actor** and does not affect appraisal. Only
   `opening_tags.dimensions` does anything.
4. **`world.standing_facts` never reaches an actor** (`src/engine/gate.py:101-104`). A fact that
   must be known goes in the event text or a vault belief.
5. **`formative.*` is read by no engine code.** Culture, class and genotype filed there reach
   nothing; `fixed.position` is the live slot.
