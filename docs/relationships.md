# Relationships — growth, diminishment, and how they gate everything

A relationship is **not** a separate subsystem. It is a **high-salience, per-character, multi-axis BELIEF** living in the vault — which is why it composes with knowledge, transmission, energy, decisions, and the director instead of sitting beside them.

## Per-perceiver and belief-based (asymmetric)
There is no single objective "relationship." There is **A's belief about A↔B** and, separately, **B's belief about B↔A** — two directed edges, each in the respective character's vault. They can diverge hard (A thinks they're close friends; B is using A). Consequences:
- It can be **false** (A wrongly believes B is loyal) — the false-belief layer applies directly; a manipulator plants a false relationship-belief.
- It's **per-character** — injected and relevance-gated like any belief.
- The objective truth (B really *is* betraying A) lives in the **world-state ledger** (events), separate from either read.

Three layers: **events** (objective, ledger) → **perception** (per-character, possibly wrong) → **relationship-belief** (per-character state).

## State: a few orthogonal axes, not one "liking" scalar
Each directed edge carries (MVP: first two):
- **Trust** — do I rely on their word/loyalty/competence? → gates whether I *believe what they tell me*.
- **Affinity / warmth** — do I like them, feel close? → gates whether I *help / sacrifice*.
- **Respect** — do I rate their judgment/status? → gates whether I *defer or override*.
- **Debt / power** — who owes whom; who holds leverage? → gates *comply / call-in-a-favor*.
They move independently (you can love someone you don't trust). Each axis gates a *different* class of decision — that's why they're separate, not decoration.

## Trust is load-bearing — it gates KNOWLEDGE transmission
From the transmission rule: when A tells B something, whether B records it as a *believed fact* or a *discounted rumor* scales with **B's trust in A**. High trust → A's words become B's beliefs; low trust → stored as "A claims X (untrusted)." **Relationships are the gain on information flow** — the relationship and knowledge systems are coupled here, not adjacent.

## How they GROW / DIMINISH — the update rule
Change is driven by **events evaluated against expectation, through the perceiver's values** — not raw events.
1. **Prediction-error, not raw event.** You update most on *surprises*. A kindness from an enemy moves trust more than the same from a friend; a betrayal by a *trusted* friend is catastrophic, the same from a known schemer barely registers. `Δ ∝ (observed − expected)`.
2. **Negativity bias / asymmetry.** Trust is slow to build, fast to lose — betrayals drop it far more than equal kindnesses raise it ("trust arrives on foot, leaves on horseback"). Some acts are **cliffs**, not slopes (one unforgivable act → discontinuous drop).
3. **Scored by the perceiver's VALUES.** What counts as positive/negative depends on the character: a loyalty-valuer is destroyed by betrayal; an honesty-valuer drops trust at a *kind* lie; a power-valuer loses respect at weakness. The character sheet's values are the scoring function.
4. **Runs through PERCEPTION (belief, not ground truth).** A updates on what A *believes* B did and *why A attributes it* (malice? force? accident?) — not what B actually did. A misunderstanding drives a real cooling; deception (frame B) drops A's trust over nothing. Tragic misunderstandings are first-class.
5. **Drift toward baseline.** Without reinforcement, relationships slowly decay toward a resting state (absence cools warmth, softens grudges); affinity fades faster than trust. (Richer layer; MVP can skip.)

## Plugs into everything (not a bolt-on)
- **Is a belief** → vault-resident, injectable, falsifiable, relevance-gated.
- **Trust gates transmission** → relationships set how much of what's said becomes known.
- **Axes gate decisions** → the simulator reads the edges when choosing actions (help/betray, believe/doubt, defer/override, comply/refuse).
- **Updates via perception + values** → false beliefs and attributions drive *real* relationship change.
- **Director lever** → to turn A against B, stage an event (real, or a framed misperception) that A — given A's values — reads as betrayal. Never fiat "A now distrusts B." Same circumstance discipline as steering action.
- **Charged events are strong vault links** → the betrayal is a low-energy-cost, always-salient memory; you don't forget it (ties to edge-weight / energy).

## Guardrails
- **Backstage (planning-mode).** Numbers decide behavior; the prose never says "affinity +5" — it surfaces as "she found herself trusting him despite herself." (Same rule as energy / deception.)
- **Calibrate, don't guess.** Deltas, negativity-bias coefficient, decay rates, cliff thresholds = tuned by testing.
- **MVP vs rich.** MVP: trust + affinity, prediction-error + negativity bias, no decay. Rich: respect/debt axes, drift, attribution modeling, second-order ("what A thinks B feels about A").

## Prior art
Prior author-mode work stored a directed edge per pair carrying `trust` + `affinity` as floats in
0–1 — a two-axis directed edge store. That shape is the starting point and is fully described by
the preceding sections; this design adds the remaining axes (respect, debt), the
prediction-error/negativity-bias update rule, and perception-routing on top of it.

---

## What is BUILT (2026-08-22)

`src/engine/bonds.py` is this document made executable. It is a third tier beside `state.py`
(affect, per beat) and `arc.py` (the durable self, per actor-turn), and it runs **per WITNESS per
turn** — that cadence is the whole design, not an implementation detail.

| this doc says | where it lives now |
|---|---|
| §5 the edge is the PERCEIVER's | `scene.py:_bond_moves` — every OTHER person in the room re-reads the speaker |
| §26 prediction error | `bonds.observe` — **the current edge IS the expectation** |
| §27 negativity bias | `_ALPHA_NEG` 0.30 > `_ALPHA_POS` 0.12 |
| §27 cliffs | gated on severity AND the perceiver's relevance AND attribution |
| §28 scored by values | `state._relevance`, the same worth-menu machinery affect uses |
| §29 attribution | the actor tags it; the witness's charity to believe it scales with trust |
| §30 drift | `bonds.drift`, at scene start on `cfg["elapsed"]` |
| §21-22 trust gates transmission | `acquisition.witness_belief(..., trust=)` |
| §14-19 all four axes | `respect` from witnessed mastery, `debt` from received care, both also addressable directly through the optional `tags.social` block |

### What this replaced, and what it was doing wrong

Edges used to be written by `arc.assess`, which runs on the **speaker**. Two defects followed, and
neither was visible from reading the code — both had to be measured:

1. **The direction was inverted.** A betrays B → **A's** trust in B fell 0.80 → 0.7828, and B's edge
   was never computed. The betrayer lost trust in their victim.
2. **Negativity bias ran backwards.** `arc.py` buffers damage by resilience, so at resilience 0.90 a
   kindness moved trust **6.0×** further than an equal-impact betrayal. Resilience belongs on
   temperament scars (where it still is) and never belonged on an edge.

### The one place this engine goes beyond the doc

§29 requires a perceiver's attribution to be able to diverge from the truth — *"tragic
misunderstandings are first-class"* — but names no rule for HOW it diverges. `bonds.py` uses
**trust**: a witness extends charity for an accident in proportion to how far they credit the person
claiming it, since §15 already defines trust as *"do I rely on their word"*. The consequence is a
feedback loop and it is deliberate: low trust reads an accident as malice, which lowers trust
further. **Falsifiable** — a cast that spirals into mutual contempt out of nothing means the charity
curve is too steep.

### Still not built

- **A per-character learning rate.** How readily someone revises their opinion of a person is a
  plausible genotype axis and is not one today — `_ALPHA_POS` / `_ALPHA_NEG` are the same for
  everybody, so two people watching the same betrayal update at the same *rate* even though the
  *size* of their update already differs by values and expectation.
- **Third order** — what A thinks B thinks A feels. The second order is built; this is not, and
  there is no evidence in a beat that would drive it.
- **`their_view` does not drift.** Drift relaxes toward `relationship_priors.default_trust`, which
  describes a disposition *toward others*; no field says what a character assumes others feel about
  *them* by default, so a second-order belief formed once stands until something else moves it.
- **Misperception as CONTENT.** A witness who fails the perception check forms no belief about the
  act rather than a wrong one. `relationships.md:29`'s "A misunderstanding drives a real cooling"
  is half-served: the attribution half is built (a distrusted person's excuse is disbelieved), the
  saw-it-wrong half needs the false-belief layer, which is unbuilt engine-wide.
- **`scripts/direct.py` writes no `RelationshipDelta` rows.** Its edges move, but its `TurnCommit`
  is built before the tags are read for bonds, so the citable delta row is scene-only.
- **Nothing authors `their_view`.** It accretes from play; a character sheet cannot start someone
  with an existing misreading of how they are regarded.

### Built since this section last said otherwise

Perception now gates the update (`bonds.witnessed` — a subtle act needs noticing, and pinning an act
on a stranger needs recognising them), the second order exists (`bonds.reflect`, rendered by
`direct_edge` as *"and as you read them, …"*), and the single-actor chair moves edges when the
director names who acted (`by:<entity_id> <text>`). The claim that single-actor mode "has no second
party" was wrong — it has exactly one perceiver, which is all an edge needs; what it lacked was any
field recording WHO performed a placed circumstance.
