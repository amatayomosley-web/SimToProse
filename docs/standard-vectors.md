# Standard — how a vector is derived, sized, and judged

*(NORMATIVE. This doc owns the METHOD for any number that describes an EVENT or a MOMENT: an
event's `{dimension: magnitude}` tag, a `baseline.catalog` row's magnitude, a compound recipe's
weights and sum. It does NOT own character fields (`reference-species-prior.md` owns those
values, `baseline-generation.md` the composition), the basis (`emotion-basis.md`), the registry's
design (`decision-engine.md` §effective-state), or the words (`direction.py`). Events cannot be
enumerated — "if a human is attacked by a green lizard, these are the vectors" is not authorable —
so this is a derivation procedure plus acceptance criteria, never a lookup table. Constants
proposed here carry the provenance tags of `reference-species-prior.md:27-31`:
**[DEFINITIONAL]** / **[LITERATURE-ORDERED]** / **[CALIBRATION]**, plus one this doc needs:
**[DERIVED]** — arithmetic consequence of other named constants; recompute when they move.)*

## 0. The law chain this standard lives under

1. **Numbers move STATE; the LLM resolves the ACT.** No argmax, ever (`decision-engine.md:5,103`;
   `levers.py:41-44`). Every number governed here terminates in `state.appraise()` /
   `levers.effective()` — an affect vector, never an action score
   (`bounds-experiment-design.md:69-75`, verified route map).
2. **Numbers never reach the prompt** (`CLAUDE.md` rule 5; `design.md:87`). Event vectors live in
   tags and the ledger; the actor sees only `direction.py`'s banded phrases, staged from the
   EFFECTIVE tier (`prompt.py:44-46`). This standard adds no prompt surface. Three routes already
   leak digits (identity JSON, goal urgency, percept fidelity — `SPEC-LEDGER.md` §Numbers→words;
   `bounds-experiment-design.md:63-67`); nothing here may widen them.
3. **No randomness in the engine** (`CLAUDE.md` rule 4). Every check in §8 is deterministic or an
   explicitly-labelled sampled experiment run OUTSIDE the engine (`driving-the-engine.md:23-30`).
4. **The actor's number is the DIMENSION magnitude only.** Each dimension fans out into fixed
   per-primary pushes (`state.py:53-70` — "every dimension is a vector, not a single push",
   :37-45). The push weights, decay rates, band edges are Class-B engine constants
   (`state-engine.md:65-69`); authors never touch them per event.

**Where event vectors are authored.** Four surfaces, one method:
(a) the actor's same-pass self-tag at runtime — the bulk of all vectors, governed by the prompt's
calibration clause (`prompt.py:80-84`) and enforced by `validate_tags`
(`consolidation.py:337-491`); (b) a scene's `opening_tags` (`scripts/scene.py:63,92`) — the
director's hand; (c) probe/experiment `hint`s — ground truth the round-trip detector scores actors
against (`guide-content.md:87-88`, `tests/coherence_probe.py:135-159`); (d) the formative/arc
side, where the same dimensions describe a life event (`arc-engine.md:5-6`,
`baseline-generation.md` §history). (b), (c) and (d) are human-authored and this standard binds
them directly; (a) is bound through the prompt text and validation, which must stay consistent
with §3.

---

## 1. The fork, resolved: outcome-class dimensions are the TAG basis; OCC/Scherer is the FUNCTION

**The divergence** (SPEC-LEDGER incident #4, `SPEC-LEDGER.md:52-61`): `state-engine.md:21-30`
specifies appraisal as five OCC/Scherer dimensions — goal-congruence · agency · certainty ·
control · norm-violation — with a CONJUNCTIVE mapping ("blocked goal **+** other-agency → RAGE"
:26; "threat-to-self **+** low control → FEAR" :27). Shipped `state.py:53-70` `_DIM_TO_PRIMARY`
uses six outcome classes (threat, loss, care_relevant, mastery, social_violation, relief), each an
independent additive push-vector; `control` appears nowhere (the only "control" in `state.py` is
`effortful_control`, a decay input).

**This standard adopts the outcome-class basis as the tag vocabulary, normatively — not as a
concession to shipped code.** The reasoning, in order of weight:

1. **Only outcome classes keep the tag OBJECTIVE.** The tag contract is "what OBJECTIVELY
   happened … NOT how you feel about it; temperament amplifies downstream; do not pre-amplify"
   (`prompt.py:80-81`). Three of Scherer's five dimensions are appraisals *proper* — they depend
   on the perceiver (goal-congruence on THEIR goals, control on THEIR skill, norm-violation on
   THEIR norms). Making them the tag vocabulary moves per-perceiver judgment into the LLM's
   self-report — the exact job `design.md:64` reserves for the engine ("the LLM never calculates
   a stat"). Outcome classes are perceiver-neutral facts about the event; the engine then
   personalizes them. The shipped basis is the only one compatible with actor-self-tagging
   (`consolidation-loop.md:12-15`) plus engine-side appraisal.
2. **The spec's dimensions are not discarded — they are already distributed across the machinery,
   under other names.** Goal-congruence IS the relevance term (`state.py:125-144`
   `_DIM_VALUE_KEYS` × the character's Model weights — "where two people diverge",
   `state-engine.md:40`). Norm-violation IS `social_violation` scored against moral-foundation
   weights (`state.py:139-140`). Agency is carried by the event TYPE (`betray`/`harm` = other
   agency; `loss` = circumstance; `mastery` = own — `consolidation.py:88-256` CATALOG) and by
   `target`/`subject` resolution. The conjunctions became (i) the per-dimension push VECTOR
   (threat raises FEAR **and** SEEKING **and** a little RAGE while collapsing PLAY —
   `state.py:54-55`) and (ii) the type-level constraint that only a type's `appraisal_map`
   dimensions legitimately co-fire (`record-contract.md:19-31`, enforced
   `consolidation.py:451-468`).
3. **Two spec dimensions are genuinely missing, and each has a designated home that is NOT a new
   tag.** **Control** — "same blade, different fear, by their skill" (`state-engine.md:38`) — is
   the defender's own skill filling a severity modulator. It is engine-derivable from
   `baseline.skills` and MUST stay engine-side; an author or actor never writes it. Until the
   deferred severity factoring is built (`state-engine.md:34-39`; explicitly deferred,
   `state.py` appraise docstring; `SPEC-LEDGER.md:86`), control is authored per character as
   catalog rows with skill provenance (§4, §6). **Certainty** (surprise) is already ruled an
   appraisal-dimension-shaped thing, not a lever (`emotion-basis.md:48-51`); adding it later is
   cheap — `appraise` ignores unknown dimensions (`state.py:397-398`), so a new dimension is an
   extension, not a migration.

**What this costs, stated plainly.** (a) Certainty stays unrepresented: expected loss and
surprising loss appraise identically until a `certainty`-class dimension is added through
`emotion-basis.md`'s procedure. (b) Agency is only type-granular: a loss CAUSED by someone must be
tagged `betray`/`harm` (other-agency types), not `loss` + a wish — pick the type BY agency, the
standard's rule, or the distinction is silently dropped. (c) The conjunctive nuance "threat + HIGH
control → mastery-coloured vigilance rather than fear" is expressible only through catalog rows
today; a child and a veteran differ by their sheets, not by the event (worked in §4 — this is the
design's intent, but the interim mechanism is authored rather than derived from skills).
(d) `state-engine.md:21-30` should eventually be revised to describe the shipped basis and name
:34-39 as the successor severity module — until then this doc is the tie-breaker, which is a
maintenance burden. Note the spec itself left the dimension set open (`state-engine.md:82`, open
question #1: "the minimal 5 above, or a different compression?"); this section answers that
question rather than overruling settled law.

**Falsification.** If the blind-vocabulary pass (`emotion-basis.md:148-177`) finds a family of
states or the round-trip probe finds a family of events that the six outcome classes cannot
separate — and catalog rows cannot express the difference — the basis is too coarse and the
OCC-style decomposition gets re-opened. Until measured, six-plus-machinery stands.

---

## 2. The derivation procedure — any event in prose → `{dimension: magnitude}`

Run the steps in order. Two authors following them should disagree only within a band (§8 D3 is
the check).

1. **TYPE first.** Pick the one CATALOG row (`consolidation.py:88-256`) whose class the event
   objectively is. Choose by act-class AND agency: someone caused it → `harm`/`betray`/
   `threaten`/`affront`/`aid`; circumstance → `threat`/`loss`/`care`/`mundane`. The type's
   `appraisal_map` now lists the only dimensions that may carry a magnitude ≥ 0.5; off-map
   dimensions are legal only under 0.5, as background scene colour (`consolidation.py:42,451-468`
   — `_MISMATCH_THRESHOLD` 0.5 **[CALIBRATION]**, probe-calibrated).
2. **STAKES per dimension.** For each dimension the map allows, name the menu item the event
   touches, from the harm-vector rule (`values-and-stakes.md:25-30`): physical events hit the
   survival/body need; social acts violate a Moral Foundation by definition (betrayal =
   loyalty+fairness, an insult = a status-threat). **No stake named → omit the dimension** —
   omission is the default ("or omit the dimension entirely", `prompt.py:82`). Silence is
   average, not absence (`reference-species-prior.md:113-114`); an all-dimensions vector is an
   anti-pattern (§10.1).
3. **MAGNITUDE per dimension**, from the severity rubric (§3): worst credible outcome ×
   how-likely-in-context, read off the event's own properties (`state-engine.md:34-36` —
   damage-potential × hit-probability × context; property-based, never class-based).
4. **PERCEIVER-NEUTRALITY sweep.** Delete anything that depends on WHO is standing there: their
   skill, phobia, values, exhaustion, love for the victim. Each has a sheet field the engine
   already multiplies in — gains (`state.py:268-296`), relevance (`:224-240`), regard
   (`:202-221`), the catalog (`levers.py`), condition. The one test: *would this vector be
   identical if a different character stood in the scene?* If not, move the difference into a
   sheet, not the event. Context is NOT perceiver: "a sniffle during fever season" is objectively
   riskier than a sniffle in summer (`state-engine.md:35` — context re-ranks;
   `coherence_probe.py:156-157` tags the in-season sniffle `threat 0.6` and the verified-nothing
   next beat `0.2` — the season moved it, not the healer's nerves).
5. **TARGET / SUBJECT.** Name who the event is about (`target`, `target_group`) — it routes
   empathy scoping (`state.py:386-387`), `target_edge` rows (`levers.py:184-196`), and arc
   relationship diffs (`arc.py:83,97`). Aboutness is not presence (`guide-emotional-authoring.md:112-115`).
6. **DURABILITY.** Vocabulary is exactly `transient | durable` (`consolidation.py:25`; anything
   else — including the tri-level `marking`/`reshaping` older docs mention — hard-fails schema
   and the event moves NO state, `consolidation.py:412-415`, `direct.py:262-263`). `durable` is
   rare: an event that would change a person for years (`prompt.py:83-84`). Know what you are
   signing: a `durable` flag OR any dimension ≥ 0.6 makes the event an ARC candidate
   (`arc.py:20,65` `_DURABLE_DIM` 0.6 **[CALIBRATION]**), and if its appraised impact clears 0.18
   (`arc.py:19,70`) it permanently moves a baseline. **A 0.6 is not a loud 0.5 — it is a
   candidate scar.**
7. **VERIFY** per §8 before the vector is used anywhere.

**The formative/arc corollary.** A backstory event is derived with the SAME procedure — arc and
generation are one engine (`arc-engine.md:44-49`). The diff it justifies then obeys the species
prior's composition caps (±0.35 total per field, `reference-species-prior.md:171-179`), and the
event text becomes the vault entry (provenance seeds memory, `baseline-generation.md:32`).

---

## 3. The severity anchor scale

The scale answers "what does 0.3 vs 0.7 vs 1.0 MEAN" in describable terms, per dimension. Its
spine is `state-engine.md:34-39`'s factoring, restated as two author-answerable questions:
**worst credible outcome if this runs its course** (damage-potential, from the event's and the
world's own properties — a bible fact, never a mood) × **how live is that outcome here**
(hit-probability × context — distance, escape routes, season, witnesses).

| magnitude | means (per dimension) | anchors |
|---|---|---|
| omit / 0.0 | the stake is not touched | the default; most dimensions of most events |
| 0.1–0.3 | ordinary friction: recoverable, routine, the texture of a day | the prompt's own calibration clause (`prompt.py:82`) **[CALIBRATION]**; probe corpus routine rows sit here (`coherence_probe.py:135-136,142`) |
| 0.3–0.5 | real but bounded: a genuine stake, recoverable on a normal path | probe: an outsider collapses, ill not dying — `threat 0.5` (`:148`) |
| 0.5–0.7 | severe: a menu item genuinely at risk; the event people retell | `>0.6` = "genuinely severe (a child dying, a betrayal, a rescue from real danger)" (`prompt.py:82-83`) **[CALIBRATION]**; 0.6 is also the arc-candidate line (`arc.py:20`) and the primary-driver line is 0.5 (`consolidation.py:42`) — three constants, deliberately kept in agreement |
| 0.7–0.9 | grave: irreversible loss probable, not merely possible | probe: third fever night "past which fevers here rarely turn" `threat 0.85` (`:143`); a death in your hands `loss 0.8` (`:151`) |
| 1.0 | the maximum this world can deliver on that stake: certain death, total loss | reserve; a 1.0 leaves the engine nowhere to go (§10.3) |

**What one unit of severity buys, on the reference sheet** — the species prior
(`reference-species-prior.md`), neutral genotype. Per-dimension delta into the pushed primary is
`sev × relevance × gain × sensitivity × push` (`state.py:404`), and the beat commits POST-decay
(`direct.py:278-280`), so the retained next-beat trace is that × r:

| channel | rel (species sheet) | push | Δ per unit sev | × r retained | sev for a visible next-beat trace (> 0.15 marker) |
|---|---|---|---|---|---|
| loss → PANIC_GRIEF | 0.64 | 0.50 | 0.32 | ×0.90 → 0.288 | **≈ 0.52** |
| care_relevant → CARE | 0.66 | 0.40 | 0.26 | ×0.82 → 0.216 | ≈ 0.69 |
| social_violation → RAGE | 0.53 | 0.45 | 0.24 | ×0.80 → 0.189 | ≈ 0.79 |
| threat → FEAR | 0.56 | 0.45 | 0.25 | ×0.72 → 0.181 | ≈ 0.83 |

All four rows **[DERIVED]** from `_DIM_TO_PRIMARY` pushes, `_DECAY_RATE`, `_DIM_VALUE_KEYS`, the
species prior, and `_DEV_THRESH` 0.15 — recompute this table when any of those move. Read it
honestly: **a single appraisal on a neutral sheet almost never changes the next staging line, by
design.** Grief lingers (the one sub-0.6 visible channel — matching `state.py:87-88`'s theory
note); fear spikes and is re-absorbed (`r` 0.72). The MEASURED confirmation: the spider event
moved FEAR 0.25 → 0.329 and the staging line was byte-identical
(`goal-alignment-review.md:113-116`). What visibly moves an actor is, in order: the event text
itself (route R1, the strongest lever — `bounds-experiment-design.md:52`), a catalog row
(instantaneous, §6), accumulation under a sustained cause (§5), and the arc (the floor moves).
The event vector is first the RECORD and the arc/accumulation currency, only secondarily a
same-scene theatrical dial. Sizing it "up a bit so something shows" is anti-pattern §10.1.

---

## 4. Worked end to end — the green lizard

*Event:* "A green lizard, long as a forearm, darts from the rocks and stands its ground, throat
flaring, an arm's length away."

1. TYPE: `threat` (externally sourced danger, circumstance-agency — `consolidation.py:119-126`).
   Legitimate dims: threat, care_relevant, loss.
2. STAKES: survival/body is touched (an animal in striking range). No one else present →
   care_relevant omitted. Nothing irreversible at stake → loss omitted.
3. MAGNITUDE: worst credible outcome = a bad bite, recoverable (a forearm lizard, unarmed threat
   properties); likelihood real at arm's length; open ground, retreat available (context) →
   **`{threat: 0.3}`**. If this book's bible says green lizards are venom-dealers, the worst
   credible outcome is death and the vector is `{threat: 0.7}` — the WORLD moved it, and the
   provenance is the bible line, not anyone's nerves.
4. PERCEIVER-NEUTRALITY: "the child is terrified" and "the veteran has seen worse" are sheet
   facts. The vector is the same for both. That is the entire answer to "we can't author vectors
   per attacker-species-and-victim": you author the lizard's objective stake profile once; the
   cast diverges by machinery.
5. TARGET: none (no party it is about). 6. DURABILITY: transient.

**The same lizard, two people — where `control` actually lives** (`state-engine.md:38`, "same
blade, different fear, by their skill"):

- **The child** — genotype `threat_reactivity: high` (gain 1.3, `state.py:26-31`), security-heavy
  model (relevance 0.8), and — because a wound needs its operational twin
  (`guide-emotional-authoring.md:109-111`, `lint_book.py:166-183`) — a catalog row from the bite
  in their history: `{when: {percept: ["lizard","scales"]}, lever: "FEAR", op: "x",
  magnitude: 3.0, source: "the bite, age six"}`. Appraisal: Δ = 0.3 × 0.8 × 1.3 × 0.45 ≈ 0.14 —
  the jolt, real but sub-marker. The ROW is what the scene shows: resting FEAR 0.30 → effective
  0.90 → band 3, "you protect yourself first and account for it afterwards"
  (`direction.py:32-35`).
- **The veteran** — combat 0.8. Their skill SHOULD fill the appraisal's control term and cut
  severity; that module is deferred (`SPEC-LEDGER.md:86`). The interim, authored form is a
  catalog row carrying the skill as provenance: `{when: {percept: ["lizard","snake","blade"]},
  lever: "FEAR", op: "x", magnitude: 0.6, source: "twenty years of field work"}` — a spiked 0.6
  reads 0.36, band 1: "you keep the ways out in view." Same event vector, same engine, two
  renders. When severity factoring lands, these rows retire in favour of skill-derived control —
  which is why their `source` must name the skill, so they are findable.

The register difference (a scream vs a measured step back) is then the LLM's resolution over the
staged direction — never a second number.

---

## 5. The band-crossing rule — what counts as a change at all

The actor sees exactly one rendering of state: `direct_affect(effective, temperament)`
(`prompt.py:44-46`). Its resolution is fixed (`direction.py:16,55` — **[CALIBRATION]**,
probe-calibrated): band edges `_BANDS = (0.25, 0.55, 0.80)` (edge-inclusive upward: 0.25 is band
1), the deviation marker `_DEV_THRESH = 0.15` versus the temperament mean (strict >), and
notability (band ≥ 1, or past the marker — `direction.py:122`).

**The rule: a magnitude is sized against those edges, from the position it will actually act on —
and a movement that crosses nothing is a NO-OP and must be called one.** It is still a legitimate
record (the ledger keeps it; the arc may consume it) — but as a *steering* choice it does
nothing, and pretending otherwise is how "the engine registered the spider and the actor's
instructions did not change" happens (`goal-alignment-review.md:113-116`; predicted for the CARE
floor at `bounds-experiment-design.md:77-83`).

The arithmetic an author needs, all **[DERIVED]** from named constants:

- **One beat, committed:** next-beat trace = `Δ × r` (appraise then decay, `direct.py:278-280`);
  visible iff it crosses an edge or exceeds the 0.15 marker from the mean. §3's table gives the
  per-channel severity floors.
- **Sustained cause** (re-appraised each beat, `state-engine.md:47`): standing elevation
  converges to `Δ × r/(1−r)` above the mean — ×2.6 for FEAR, ×4 RAGE, ×4.6 CARE, **×9
  PANIC_GRIEF** (`state.py:100-108`). A modest recurring grief reminder (Δ 0.05/beat) holds
  +0.45 — the slow channels are accumulation channels.
- **The ceiling:** current-state saturates at `mean + (1−mean) × r`
  (`goal-alignment-review.md:222-228`; the reason tier 3 exists, `levers.py:26-39`). A resting
  FEAR below ≈ 0.28 can NEVER reach band 3 through appraisal — only a catalog row gets it there.
  Bravery without rows is immunity, which is a bug, not a character.

---

## 6. Catalog-row magnitudes — anchored, not tasted

A row is `{when, lever, op (x|+), magnitude, source}`; `effective = current × Π(mult) + Σ(add)`,
clamped, multipliers before adds (`decision-engine.md:94,101`; `levers.py:70-111`). Effective is
instantaneous and never committed (`levers.py:35-39`), so rows do not accumulate across beats —
their entire meaning is the band they land you in *while firing*.

**The sizing rule: derive the magnitude from the intended band transition and the value the row
will actually multiply — never free-pick it.**

- **Multiplier:** `magnitude ≈ target_edge / expected_current`, stating which current you assumed
  (the character's resting mean for always-relevant rows; a plausibly spiked value for rows that
  fire mid-crisis). Worked, against the guide's own rows (`guide-emotional-authoring.md:80-89`):
  a phobia that must grip from rest 0.25 needs ≥ 0.80/0.25 = ×3.2 → the authored ×3.4 clears it
  with headroom. An ally-calm row ×0.62 takes rest 0.25 to 0.155 — the fear clause disappears
  entirely — and a spiked 0.7 to 0.43, one band down. Both are real transitions; ×1.2 on 0.25 →
  0.30 crosses nothing and is a dead row.
- **Additive:** an add of **≥ 0.30 is guaranteed to cross at least one edge from any start below
  0.80** — 0.30 is the widest inter-edge gap **[DEFINITIONAL]**. Use `+` for absolute
  displacements that must not scale with the current level; use `x` for dispositions. Negative
  multipliers are refused — debuff by `+` with a negative magnitude (`levers.py:64-66`).
- **Ranges by row kind**, anchored to existing engine numbers, all **[CALIBRATION]** starts:
  *disposition-grade* (a standing lean) ×0.6–1.5 — the allele gain range 0.75–1.3
  (`state.py:26-31`) is the precedent, and `make_genotype --rows` emits genotypes as exactly such
  rows (`guide-emotional-authoring.md:38-39`); *wound-grade* (a phobia, a trigger) ×2–3.5 — must
  clear band 3 from that character's own rest; *comfort/suppression-grade* ×0.5–0.8 — must drop
  the spiked value below an edge.
- **Stacking is multiplicative** (two ×2 rows = ×4, `levers.py:92-99`) and rows AND within
  themselves but stack freely across. The check is not a cap but a render: compute effective
  under the maximum plausible co-firing and confirm it does not pin at 1.0/0.0 unless the book
  means it — a pinned lever is the saturation that kills drama
  (`reference-species-prior.md:174-178`), and per-action rows ("courage in scene 47") are the
  buff-soup the guardrails forbid (`decision-engine.md:107-111`).
- **No double-count with appraisal.** The event's vector fires on the CHANGE; the row applies on
  the STANDING FACT (`state-engine.md:49-54`, `levers.py:127-131`). A spider appearing is
  appraised once; a spider present multiplies every beat it remains. Both, by design — do not
  shave one because the other exists.
- **`source` is load-bearing.** It is the row's provenance line (§9) and the only trace in the
  manifest (`scene.py:157`); a row whose source cannot name the life fact or skill it encodes is
  the arbitrary insert.

---

## 7. Compound recipes — what governs the weights, and what governs the sum

A recipe is `{primitive: (weight, role)}` (`compounds.py:45-124`); weights are SHAPES (similarity
is cosine, so contempt at 0.4 and 0.9 are one state at two strengths — `compounds.py:42-44`), and
the SUM is the identity dial: `blend` fills `(1 − sum)` with the character's resting self
(`compounds.py:248-296`; `emotion-recipes.md:15-25`). Today the 42 sums "span 0.60–1.10 (mean
0.84) as a side effect of authoring the weights" (`emotion-recipes.md:83-85`) — unchosen. This
section makes both deliberate. (Honesty first: the module has zero runtime consumers
(`SPEC-LEDGER.md` §Emotion basis); until it is wired, these rules govern authoring for the
read-back and verification jobs — `recognise`, `separability`, the blind-judge pass.)

1. **Choose the SUM first**, by answering the one question it encodes: *how much of the person
   survives this state?* Tiers, **[CALIBRATION]** anchored to the existing distribution:
   **0.60–0.80** social texture — warmth, wariness, banter; the person is mostly still there.
   **0.80–1.00** seized states — grief, fury, dread; the state is most of what is visible.
   **≥ 1.00** totalizing, reserve — only for states whose phenomenology IS self-loss (the sole
   existing case, jealousy 1.10, is defensibly "three primitives at three objects … precisely
   what makes it feel unstable" — `emotion-basis.md:89-91`). A sum above 1.0 erases the baseline
   entirely (`compounds.py:283-284`); spending that on mild fondness is a category error.
2. **Then distribute the weights** as a dominance structure: the defining primitive carries
   roughly half the sum or more (existing range 50–65%: contempt 0.55/0.90, shame 0.50/0.95);
   every ingredient ≥ 0.15 (the observed floor in the table) or it is decoration — drop it;
   single-primitive rows are reserved for the plain states (`grief`, `fury`, `revulsion`).
3. **Roles are part of the shape.** Same magnitudes, different role signature = a different state
   (pride vs excitement — `compounds.py:236-241`); shame vs guilt separate on roles, not
   numbers (`emotion-basis.md:84-86`). A new recipe must declare a role per primitive from the
   closed set (`compounds.py:40`).
4. **Admission gates, both deterministic:** `validate()` clean (no primitive the basis lacks —
   blocked loudly, never truncated, `compounds.py:30-34,144-162`), and `separability()` at 0.95
   finds no same-role-signature neighbour (`compounds.py:224-245`) — a duplicate shape is a
   redundant name, and the repair table for every other failure is `emotion-basis.md:166-173`.
5. **The vocabulary-level health checks bind the whole table**, not one row: no dead primitive,
   mean mixture ≈ 3, > 90% of states mixed (`emotion-basis.md:158-163`). A proposed recipe that
   nudges the table toward single-primitive word-listing is making the basis worse.

---

## 8. Evaluating a vector you have written — the acceptance criteria

Deterministic first (no LLM, run every time), behavioural second (sampled, for vectors that will
carry a scene). Precedents: `compounds.separability`, `scripts/lint_book.py`,
`tests/test_direction.py`.

**D1 — schema and legitimacy.** Run the vector through `validate_tags(tags, percepts, skills)`
(`consolidation.py:337`) with the scene's percepts: type in CATALOG, dims known and in [0,1],
durability in `{transient, durable}`, target perceived, off-map dims < 0.5, capability met.
Anything it flags at authoring time will be stripped or zeroed at runtime
(`direct.py:261-268`) — fix it now.

**D2 — the render diff (the only check that sees what the actor sees).** Assemble and render
before/after for each intended character (`guide-emotional-authoring.md:141-149` gives the
one-liner: `assemble` → `direct_affect(effective, temperament)`). Assert BOTH directions: the
staging line CHANGES for the characters the event is meant to move, and DOES NOT change for
those it is not. `effective == affect` means no row fired; an unchanged line means the whole
vector stayed inside a band — a no-op (§5), to be either resized or accepted explicitly as
record-only.

**D3 — two-author band agreement.** Reproducibility is judged in band-effects, not digits: two
authors' vectors for the same event must produce the same set of crossed edges and marker flips
on the REFERENCE SHEET (a character authored straight from `reference-species-prior.md` — the
species is the reference reader) plus the book's principals. Numbers that agree within a band are
the same vector for every observable purpose; disagreement in band-effect means step 2 of §2 was
ambiguous — resolve by naming the stake, never by averaging digits.

**D4 — saturation render.** For arc-candidate vectors (≥ 0.6 or durable) and for new rows:
render the worst-case stack (§6) and the arc consequence (`arc.assess` is pure — feed it the
vector and the impact; `arc.py:52-105`) and confirm no primitive pins and no baseline walks past
the ±0.35 composition cap over the planned arc (`reference-species-prior.md:171-179`).

**B1 — behavioural, when the vector carries a scene.** The `driving-the-engine.md:23-30`
template: K ≥ 6 seeded samples at temp 1.0, A/B against the prior vector, a grep-able primary
outcome registered first (tag magnitudes, exit flag, verb lists — `bounds-experiment-design.md`
§3). Expect state-shaped effects, not outcome-shaped ones: across ~90 sampled turns no lever ever
bought an exit (`driving-the-engine.md:83`); a vector that fails to force an action is working as
designed (§10.6). **B2** — where ground truth exists, the round-trip: actor tags vs authored
hints, error and slope (`coherence_probe.py:208-244`); a rising slope is recording drift, not an
authoring fault.

| observation | verdict → repair |
|---|---|
| D1 flags an off-map dim ≥ 0.5 | wrong TYPE, or a smuggled perceiver read — re-run §2 steps 1/4 |
| D2: no line change on the target | no-op — resize against §5, add the row, or accept as record-only in writing |
| D2: a line changes on a bystander it shouldn't | mis-targeted subject, or a row keyed too broadly |
| D3: band-effects diverge between authors | the stake naming was ambiguous — sharpen step 2, not the digits |
| D4: a primitive pins / cap exceeded | saturation — the ceiling is where drama dies; shrink or stage across events |
| B1: rate unmoved | the number moves state, not this behaviour — stop pushing it (EXP-1's lesson) |

---

## 9. Provenance, applied to events

The character-side rule: "a number you can't trace to their life is the arbitrary insert the
design rejects" (`baseline-generation.md:32`; discipline at `guide-content.md:112-117`). The
event-side equivalent:

> **A dimension you cannot point to in the event's own text or the world's own facts is a
> perceiver's reading smuggled into the record.**

Every non-zero dimension in an authored vector (opening_tags, hints, formative events) carries a
one-line *why* naming its ground, from three admissible sources — **TEXT** (the words of the
event: what is present, at what range, doing what), **WORLD** (a bible/lexicon fact: the venom,
the law, the season — cite the note), **CONTEXT** (the standing situation that re-ranks
likelihood: the corridor, the fever season). **PERCEIVER is never admissible** — that is what
gains, relevance, regard, condition and the catalog are for, and the runtime prompt already
states it as law to the actor (`prompt.py:80-81`). For catalog rows the same duty is discharged
by `source` (§6); for compounds, by the definition-and-role argument of §7. Like the baseline
rule, this one does double duty: the why is what a second author checks in D3, and for formative
events it is the vault entry itself.

Constants proposed by THIS doc, tagged: the severity tiers (§3) **[CALIBRATION]** anchored on
`prompt.py:82-83` and the probe corpus; the per-channel visibility floors and the ≥0.30 add
**[DERIVED]**; row ranges (§6) and sum tiers (§7) **[CALIBRATION]**. None is presented as more
settled than its tag; the falsification for each calibration is named where it is proposed. The
derived rows are downstream of `_BANDS`, `_DEV_THRESH`, `_DIM_TO_PRIMARY`, `_DECAY_RATE`,
`_DIM_VALUE_KEYS` and the species prior — a change to any of those obsoletes them; recompute
before trusting.

---

## 10. Anti-patterns, each with the failure it causes — all from this repo

1. **Pre-amplification** — baking the perceiver's read (or the author's wish for drama) into the
   magnitude. The engine multiplies temperament, relevance and regard in AGAIN
   (`state.py:404`): double-counted intensity, saturated primaries, a cast that converges. The
   prompt carries an explicit measured counter-instruction because actors do this unprompted
   (`prompt.py:7-8,80-84`).
2. **The within-band no-op believed in** — a magnitude or row that crosses no edge, trusted to
   "do something." Measured: the spider's staging line came back byte-identical
   (`goal-alignment-review.md:113-116`); the CARE floor is predicted invisible outside sustained
   bombardment (`bounds-experiment-design.md:77-83`). Failure: authored content that reaches
   nothing — this repo's dominant defect class (`compounds.py:30-31`).
3. **Saturation** — resting means or stacked diffs near 1.0, or 1.0 severities spent on
   non-maximal events. "At FEAR 0.95 resting there is nowhere left for an event to take them …
   the ceiling is where drama dies" (`reference-species-prior.md:174-178`). The composition cap
   and D4 exist for this.
4. **The prose-only number** — an intensity in `fears_wounds` with no catalog row: it reaches no
   arithmetic, and its digits leak into the prompt instead (route R3). Four such wounds were
   found in an active book the day the lint was written (`guide-emotional-authoring.md:109-111`;
   `lint_book.py:166-183`).
5. **Coined vocabulary** — a new dimension, primitive or synonym ("vectors" for levers) instead
   of the bounded sets. Unknown dims are *silently ignored* by `appraise`
   (`state.py:397-398`) and unknown allele words silently read `typical` (`lint_book.py:131-151`,
   an ERROR since it changes who the character is) — the invention moves nothing and says
   nothing. The registry rebuild this caused is documented at `MAP.md:3-9`. Extend a bounded set
   only through its owning doc (`emotion-basis.md` for the basis; the CATALOG for types).
6. **Buying the outcome** — sizing a vector to force the act you want. The number stops at state
   (`decision-engine.md:103`); measured, no magnitude ever bought an exit
   (`driving-the-engine.md:83,114-121` — EXP-1 falsified). Failure: escalating numbers, no
   rupture, saturation as a side effect. Ruptures are arc-or-narrator beats.
7. **The per-instance table** — a severity per weapon-species pair, a row per scene ("courage in
   scene 47", `decision-engine.md:108`), the enumeration `values-and-stakes.md:25` calls the
   "system per action, impossible" trap. Failure: unbounded authoring debt and a catalog rotted
   to buff-soup. Derive from properties; refine only at hinges (`design.md:40`).
8. **Trusting digits over the render** — validating by reading numbers. The number can change
   while the actor's world does not (D2's whole point: "check by rendering, not by reading the
   number", `guide-emotional-authoring.md:122-124`), and a lint pass with warnings is not clean
   (`lint_book.py:242-244`).
9. **Stale-vocabulary drift** — following an older doc's wording into a hard schema fail:
   `durability: marking` (suggested at `driving-the-engine.md:99-100`) fails
   `_VALID_DURABILITY` and the whole event moves no state (`consolidation.py:25,412-415`,
   `direct.py:262-263`). When a doc and a validator disagree, the validator is what runs —
   then file the divergence in `SPEC-LEDGER.md`.

---

## Cross-links, and what is NOT settled

- **Feeds:** the prompt's calibration clause (`prompt.py:80-84`) must stay consistent with §3 —
  they are one scale, stated twice; `scene-authoring-rules.md` (opening_tags obey §2);
  `guide-emotional-authoring.md` §4 (rows obey §6).
- **Consumes:** `consolidation.py` CATALOG (types), `state.py` (the arithmetic §3/§5 derive
  from), `direction.py` (the edges everything is sized against), `arc.py` (what a 0.6 signs up
  for), `compounds.py` (§7's gates).
- **Not settled:** the severity tier boundaries and row ranges are **[CALIBRATION]** starts —
  falsified the first time a K-sampled scene or the blind-judge pass shows a tier producing
  systematically wrong-band behaviour on the reference sheet. The §1 resolution stands until the
  blind-vocabulary/round-trip falsification fires. The visibility-floor table goes stale the day
  any of its five source constants moves — it is a maintenance obligation, named in §9. D3's
  band-agreement check has never been run between two real authors; its tolerance (same
  band-effect) is a proposal, not a measurement. And when DISGUST joins `PRIMARIES` and
  `social_violation` gains its second push (`state.py:61-68`), §3's RAGE row and every derived
  number touching that channel must be recomputed — the push table is the input, not this doc.
