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
Scribe already stores `(c1)-[r:RELATIONSHIP]->(c2)` with `trust` + `affinity` floats (Context Assembler KZ-5; the-writers-desk used trust/affinity 0–1 per relationship). Reuse the edge store; add multi-axis + the prediction-error/negativity-bias update + perception-routing on top.
