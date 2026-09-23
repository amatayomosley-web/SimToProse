# Relationships — growth, diminishment, and how they gate everything

> **Normative for the LAW, the scale and the calibration: `bond-arithmetic.md` (2026-09-17).** This
> doc keeps the design intent — why relationships exist, the per-perceiver/belief-based framing, the
> four axes and what each gates. The **update rule** below ("How they GROW / DIMINISH") is
> superseded in part by `bond-arithmetic.md`'s signed, level-anchored law; skim that banner before
> reading the five points below as current mechanism rather than design history. Pointer added
> 2026-09-19 so a skim of this file's top catches it before scrolling to the banner four sections
> down.

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

> **SUPERSEDED IN PART, 2026-09-17 — `bond-arithmetic.md` is normative for the law, the scale and the
> calibration.** Point 1 below (prediction error as the whole law) survives only as the CROSSING branch
> of a signed, level-anchored law; an act now moves an edge through the witness's STAKE in the act's
> object (the owner's rule: what is hers moves her; values in the abstract move nothing), with the
> worth menu kept as a factor inside the gain. Point 5's resting state is a per-edge `rest`, not
> `default_trust`. The four points are kept below as the design intent they still are.

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

**What a person holds that is not a person** (2026-09-18, bond gate 5): a place or a group is on the
sheet as `current.attachments` (`bond-arithmetic.md` s3) — an act on it is done TO the holder at her
hold, and the same number is the emotion tier's investment in it. People are never there: the edge is
the hold.

## What is BUILT (2026-08-22)

`src/engine/bonds.py` is this document made executable. It is a third tier beside `state.py`
(affect, per beat) and `arc.py` (the durable self, per actor-turn), and it runs **per WITNESS per
turn** — that cadence is the whole design, not an implementation detail.

| this doc says | where it lives now |
|---|---|
| §5 the edge is the PERCEIVER's | `scene.py:_bond_moves` — every OTHER person in the room re-reads the speaker |
| §26 prediction error | `bonds.law_delta` — the CROSSING branch (since gate 4, 2026-09-17); on the same wing the law is level-anchored: the act's rung, one rung further out, is the ceiling of what it can teach (`bond-arithmetic.md` s6) |
| §27 negativity bias | `_ALPHA_NEG` 0.30 > `_ALPHA_POS` 0.12 — PER WITNESS since gate 4: `relationship_priors.update` → `bonds.rates_of` |
| §27 cliffs | the floor ACT word (`treacherous`) AND the perceiver's relevance ≥ .60; attribution shapes the target; no strength term (gate 4) |
| §28 scored by values | `state._relevance`, the same worth-menu machinery affect uses — inside the gain, beside the witness's STAKE in the act's object (`bonds.stake_of`, the owner's rule) |
| §29 attribution | the EVENT SEAT answers it since gate `seat-attribution` (`e7d38ee`, 2026-09-19) — a closed four (`severity.ATTRIBUTION_WORDS`: intent/negligence/coerced/accident), `parse_event_reply` writes `out["attribution"]`; corrected 2026-09-19, was "the actor tags it" here. The actor's own `tags.attribution` self-tag is the stub double / seat-refusal fallback; the witness's charity to believe it scales with trust |
| §30 drift | `bond_rest.drift`, at scene start on the declared gap, toward the edge's own REST (`rest_declared`, schema v28) |
| §21-22 trust gates transmission | `acquisition.witness_belief(..., trust=)` |
| §14-19 all four axes | the seat's `showed` word per axis (`severity.ACT_WORDS`) — except the .66 trust rung, which the seat is not offered (`severity.ACT_DERIVED`) and the parser derives from a `told` row at a cost (fault / exposure); `debt` from the seat's `transfers` (what changed hands, on what terms) through `bonds.debt_postings` — never from a dimension, and since 2026-09-18 never from a verdict |

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

- **A per-character learning rate** — BUILT 2026-09-17 (gate 4): `relationship_priors.update`
  (`grant_threshold` low/moderate/high, `withdraw_speed` slow/typical/fast) → `bonds.rates_of` → the
  witness's own (α_pos, α_neg); two people watching the same act now update at their own rates.
- **Third order** — what A thinks B thinks A feels. The second order is built; this is not, and
  there is no evidence in a beat that would drive it.
- **`their_view` does not drift.** Drift relaxes toward the edge's declared rest (`rest_declared`);
  `their_view` has no rest row, and no field says what a character assumes others feel about *them*
  by default, so a second-order belief formed once stands until something else moves it.
- **Misperception as CONTENT.** A witness who fails the perception check forms no belief about the
  act rather than a wrong one. `relationships.md:29`'s "A misunderstanding drives a real cooling"
  is half-served: the attribution half is built (a distrusted person's excuse is disbelieved), the
  saw-it-wrong half needs the false-belief layer, which is unbuilt engine-wide.
- **Nothing authors `their_view`.** It accretes from play; a character sheet cannot start someone
  with an existing misreading of how they are regarded.

### Built since this section last said otherwise

Perception now gates the update (`bonds.witnessed` — a subtle act needs noticing, and pinning an act
on a stranger needs recognising them), the second order exists (`bonds.reflect`, rendered by
`direct_edge` as *"and as you read them, …"*), and the single-actor chair moves edges when the
director names who acted (`by:<entity_id> <text>`). The claim that single-actor mode "has no second
party" was wrong — it has exactly one perceiver, which is all an edge needs; what it lacked was any
field recording WHO performed a placed circumstance.


### Dormant on seat output — measured, and the seam built but not wired (2026-09-16)

> **2026-09-17, bond gate 1 — LIVE on seat output.** The event seat now answers `object` + `showed`
> on the act ladders (`bond-arithmetic.md` s2/s4) and the parse seam prices the words; the `social`
> block is refused (APPRAISER_SOCIAL_RETIRED). The section below is the record of the dormancy and
> the measurement that ended it. Re-answered the first scene under the new contract: 14/14 parsed, an
> object on every beat, 2.36 named axes per beat (target ≤ 1.5 — missed; `straight` fires on plain
> speech), one party still blind to the other's quiet acts (overtness: gate 4).
> **2026-09-18, the first live scene + the quote check.** The next scene ran live under s6 (record in cairn);
> the anchor held and the one finding was the seat's — `gave` over-fired 10/14 and once signed
> backwards. The fix is structural, not a gloss: every `showed` word now quotes its span of the
> action and the parser refuses one it cannot find (`APPRAISER_FACT_NOT_IN_ACTION`); the debt
> verdict is next to become a fact the seat reports (`transfers`) and the engine prices.
> **Gate 4 (2026-09-17): the law is `bond-arithmetic.md` s6** — signed, level-anchored, per-witness
> rates, the stake gain, the cliff on the floor word, always-overt when received, a per-edge rest.
> The ledger rule on live scenes lifted with it. Replayed the first scene under it: unwitnessed 0 of 14,
> one edge held at its anchor and the other moved by a few hundredths.

**The tier has not moved an edge on any live performance.** `relationship_deltas` holds 0 rows
across four runs of the first generated scene (5, 7, 6 and 14 beats) while the stub probe writes
them. Cause: the event seat's `social` block is severity WORDS (`{"trust": "moderate", "affinity":
"marked"}`); `bonds.act_from_tags` does `float(word)`, catches the error and skips the axis, and
because the block is non-empty the `_DIM_AXES` fallback is never entered — `None` every beat, and
nothing printed. Found by Fable's review of the seat findings
(`cairn/projects/reviews/2026-09-16-simtoprose-seat-review-fable.md`), corroborated by the connection
multiplier sitting unmoved for fourteen beats.

**Under it, a semantic fault the parse fix alone would expose.** The axes are bipolar with 0.5
neutral (`observe` computes observed − expected against the witness's own edge); the strength words
are unipolar — "slight affinity" (0.15) means *little was shown*, and the arithmetic would read it as
a cold act against a warm authored edge and cool its holder on every reserved beat. Measured
(`tests/bond_replay.py --all` on the first scene's longest run, from the authored edges):

| mapping | edge A, authored warm (tru/aff/res/deb) | edge B | notes |
|---|---|---|---|
| authored | as the sheet has it | as the sheet has it | |
| severity words AS observations | **trust, affinity and respect all fall; affinity loses more than half; a debt of over half the scale appears** | small falls on trust, affinity and respect; its debt more than doubles | unipolar words read as cold acts: the warm-authored edge loses more than half its affinity — the mismatch, pictured |
| dimensions only (block ignored) | unchanged — *its holder witnesses 0 of 7* | warms a little on every axis; its debt grows several-fold | every act from B's side is below `_OVERT_SEVERITY` .55, under what A's holder can notice (the subtle-act DC), so A's holder witnesses none of them |
| read ladder | refuses all 14 | | the replies carry strength words; the contract has not been asked of a seat yet |

**What is built (this commit), deliberately not wired** — owner: *"build but do not wire, right now
we don't have the metrics to guide the bonds numbers"*:

- `severity.READ_WORDS` — a bipolar read ladder with a named neutral: hostile .10 · cold .22 · cool
  .36 · neutral .50 · warm .64 · close .78 · devoted .90; `read_value_of` refuses a strength word by
  code; `read_gloss()` is the contract line a future seat prompt will carry. The floor word is the
  only read that reaches `_CLIFF_FLOOR` — the prompt must say it means betrayal.
- `bonds.observations_from_social(social, dims, ladder)` — the seam: an axis the block names wins; an
  axis it OMITS derives from the dimensions (omission means *nothing shown* and must not blind the
  other axes, as the live either/or does); a value on neither ladder is refused, never skipped.
- `bonds.act_from_tags(…, observations=)` — takes the seam's floats in place of the block. Without it
  the live route still returns `None`; `tests/test_bonds.py` [18] pins that dormancy by name so the
  wiring gate has to flip it on purpose.
- `tests/bond_replay.py` — the instrument above; `scripts/scene.py` prints `durability` on TAGS and a
  `BOND: dormant` line whenever a social block was present and no edge moved.

**What wiring will take, in order:** (1) the seat's `social` contract becomes the read ladder with
per-axis omission (`appraiser.py` rule 4 gains "omit an axis the act says nothing about"; the floor
word means betrayal); (2) `parse_event_reply` normalises through `observations_from_social` and
refuses off-ladder — `test_bonds.py:212`'s "junk skipped" splits into "junk refused at parse"; (3)
`floor.bond_moves` and `direct.py` hand `observations=`; (4) re-answer the cached first-scene event prompts
out of process under the new contract and replay them here before a live scene sees it; (5) the
numbers — `_ALPHA_*`, `_OVERT_SEVERITY` (the two-hander blindness above), `_DEBT_RATE` (most of the
scale owed in seven quiet beats), `_CLIFF_*` — chosen against those pictures, not before them.
