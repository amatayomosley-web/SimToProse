# Constant register — every number in the emotion and relationship stack

*(Descriptive, not normative. It records what each number IS, what it DOES, and WHAT IT RESTS ON.
The source is the authority; where this file and the code disagree, the code is right and this file
is stale. `docs/emotion-arithmetic.md` owns the arithmetic; `docs/relationships.md` owns the edges;
this owns the inventory.)*

**Why it exists.** Asked on 2026-09-09 whether the stack was "compounds and vectors with no basis."
A first census said fifteen of thirty-two constants named no basis. **That census was wrong** —
comment blocks in these modules cover GROUPS of constants and the instrument attributed each block
to the first name under it only. Read by hand, thirty-one of thirty-two carry a stated basis. The
real finding is different, and worth having in one place: **the bases are overwhelmingly
CALIBRATION — owned judgment — and exactly one constant records a measurement.**

## The basis classes

| class | means |
|---|---|
| `DERIVED` | computed from another table, or anchored to one; cannot drift independently |
| `MEASURED` | a number a run produced, with the run named |
| `LITERATURE` | anchored to a published finding, cited in the source |
| `DOC` | fixed by a design doc that states the ordering or the rule |
| `CALIBRATION` | a starting value someone chose; the repo's own honest label (`Class-B`) |
| `NONE` | nothing stated |

---

## state.py — the emotion tier

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `_AT_REST` | 0.15 | how close to your OWN mean counts as back at rest | clears a path's aboutness bind once the feeling is spent | `DOC` — kept in step with `direction._DEV_THRESH`. The rejected alternative is recorded with its failure: gating on the quiet band meant a character whose resting WARINESS is 0.62 would never clear |
| ~~`_REG_FLOOR`~~ | — | RETIRED 2026-09-10 with `effortful_control`; decay is `r_p ** (1/hold)` and nothing can collapse it | — | — |
| `heritable.GAIN` | 0.75 / 1.0 / 1.2 / 1.3 | the hit cell's words → `g` | `f <- f + v_k * g` | **`START`** (adopted 2026-09-10, tuned in runs) — carried from the primitive era; `scripts/derive_genotype.py` reports the ceilings the idle-floor envelope admits (at p 0.2 today: high rest × high hit leaves its rung on DEFLATION, GOODWILL, SELF-REGARD, DISPLEASURE — 97 of 464 combinations, ratcheted in `tests/test_genotype_balance.py`) |
| `heritable.PERSIST` | 0.85 / 1.0 / 1.10 / 1.15 | the hold cell's words → half-life multiplier | `half_life × hold` (`state.half_life_minutes`) | **`START`** (adopted 2026-09-10, tuned in runs) — carried; spread kept narrow because retention is the hyperbolic channel (`1/(1-r)`) |
| `heritable.REST_CAP` | per path 2..5 (LEVITY 3, playfulness — banter needs a second mind; 2026-09-11, unmeasured) | last rung a rest word may name without a receipt | bounds `make_genotype.draw_rest`; an authored rest above it (word or number, at `baseline.temperament[path].rest`) is honoured and lint-warned; ~~`state.zone_of`'s disposition/episode boundary~~ — **corrected 2026-09-19**: `zone_of` and the two-zone apparatus were retired the same day (gate `emotion-tier-tidy`, `c008a4b`); decay no longer consults `REST_CAP` at all — the per-rung staircase (`state._rung_half_life`, deriving 92 cells from `_HALF_LIFE`'s two anchors per path, gate 2 2026-09-12) reads its own boundary directly | `JUDGMENT` — read off each ladder's words 2026-09-10 (last rung used as a trait in plain English), owner agreed; a numeric cross-check (band top ≤ 0.45) agreed 6/8 |
| ~~`heritable.REST_VARIABILITY`~~ | — | RETIRED 2026-09-10 when the rest word moved to `baseline.temperament` (a design choice beside the voice); nothing read the row's spread | — | — |
| `_RELEVANCE_FALLBACK` | 0.5 | relevance when a dimension has no value-key | keeps an unmapped dimension neutral rather than silent | `CALIBRATION` (Class-B) |
| `_CARE_FLOOR` | 0.25 | the innate-empathy floor regard cannot scale below | *"a learned low regard for a subject can dampen the response to their harm, never delete it"* | `CALIBRATION` with a stated principle |
| `_DIM_TO_PATH` | 21 weights (PLAY's six restored under LEVITY 2026-09-11: threat −0.22, loss −0.20, social_violation −0.15, mastery +0.15, relief +0.20, attraction +0.10) | dimension to path push-vectors | the whole event-to-emotion route | `DOC` — `standard-vectors.md` §1; secondaries from Panksepp/OCC, primaries unchanged since the single-push version |
| ~~`_DECAY_RATE`~~ | — | RETIRED 2026-09-10: a retention per BEAT, and a beat had no duration | — | — |
| `_HALF_LIFE` | 9 × 2 anchors → ~92 per-rung cells | the EPISODE + DISPOSITION anchors per path; `state._rung_half_life` derives one half-life per rung (short at top via `_TOP_BURN`, long at bottom), `state.decay_over` steps down the ladder | `TEMPORARY`/per-rung since 2026-09-12 (redesign gate 2, owner: decay per emotion AND per rung); anchors are the measured medians, each cell a START a thermometer can replace | `START` |
| `_MID_RUNG` / `_TOP_BURN` | 3 / 0.33 | the rung the EPISODE anchor sits at; the top rung's half-life as a fraction of it | one judgment governs the whole top half of every staircase | `JUDGMENT` (owner: the top burns out) |
| `clock.UNIT` | minutes | the one clock's unit | every `elapsed` on the ledger is minutes; the four older tiers read it in days | `JUDGMENT` — owner 2026-09-10, "lock duration to the minute" |

## rungs.py — what a rung is worth

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `LAMBDA` | per path: STIRRING .070 · WARINESS .100 · DISPLEASURE .054 · GOODWILL .030 · DEFLATION .066 · DISTASTE .026 · RECEPTIVITY .042 · SELF-REGARD .042 · LEVITY .066 | per-path multiplier on a rung's height | `v_k = LAMBDA[path] * height_k` — the vector one tag is worth | **`MEASURED`** 2026-09-11 (`tests/calibrate_accrual.py`, `emotion-arithmetic.md` §2): the 0.15 start ran away on real readings; each path's value is its reachability floor (E2, `test_genotype_balance.py` — set by the half-life), which scores like a 0.25× global against both thermometers. §9 decision 1 answered per-path, by the data |

## bonds.py — the relationship edges

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `_ALPHA_POS` / `_ALPHA_NEG` | 0.12 / 0.30 | the rate up the scale / down it, per unit gap to the anchor or on a crossing (bond-arithmetic.md s6) | that NEG exceeds POS **is** the negativity bias; the DEFAULT pair — a witness's own comes from `_RATE_POS` / `_RATE_NEG` | `LITERATURE` — `relationships.md:27`; the 2.5x ratio is `CALIBRATION`; fitted at gate 6 |
| `_BETA` | 0.12 | one rung of the act ladder: an act's reach is one rung past its own height | `kind` (.66) can carry an edge to `generous` (.78) and no further — the anchor, not the count, sets the ceiling | `DERIVED` — equals `severity._ACT`'s rung gap |
| `_REACH` | 0.45 | the same-wing target clamp, as a deviation from the stranger | puts the law's reach at .95 / .05: the top word .90 plus β, clamped | `DERIVED` from the top word + `_BETA` |
| `_TRUST_STAKE_FLOOR` | 0.30 | trust's stake floor: g_trust = (floor + (1 − floor)·stake)·attribution·relevance | a liar seen lying to a stranger still costs him; loyalty to HER costs more | `JUDGMENT` (Fable, settled review) |
| `_DEBT_RATE` | 0.05 | per transfer PAIR per beat, × the beat's dimension severity × attribution × hold (`bonds.debt_postings`, 2026-09-18 — the entry is derived from the seat's `transfers` and their `terms`, never from a verdict) | five `marked` gifts cross "a favour" (.15), twenty reach "a debt" (.60); at the old .35 three gifts saturated. **Falsifier:** an account reaching "a debt" inside one ordinary scene | `JUDGMENT`, anchored to `severity.DEBT_STANDING` |
| `severity.TRANSFER_TERMS` | none / price / loan / repayment | what a transfer was SAID to be — the one judgment the seat keeps on the account, a fact about the words of the beat | none and loan post `gave` on the receiver; repayment posts `repaid` on the giver iff something is owed; price posts nothing | `DOC` — bond-arithmetic.md s6; the direction cases are pinned on invented transfers in `tests/test_bond_law.py` [8] |
| `severity.ACT_DERIVED` | trust: straight | the one rung per axis the seat is NOT offered — derived at the parse seam from a `told` row at a cost; a seat that names it is refused (`APPRAISER_WORD_DERIVED`) | measured 2026-09-18: named on 11 / 9 / 9 of the 14 beats of one recorded scene under three contracts against a 4-8 band, the quoted span in the text but not showing the word | `DOC` — bond-arithmetic.md s4 (the told paragraph); the facts-in-tags review s1 |
| `severity.TOLD_COSTS` | fault / exposure / none | what a thing said cost the teller, in the words: owned a fault of their own / named a loss, weakness or liability of their own the other could use / neither — the one judgment the seat keeps on the trust rung, closed so the parser can hold it | fault or exposure -> the .66 rung with the told span as its quote, when no trust word was named or a warm word below the rung was (the lift, 2026-09-18, post hoc: the seat wrote `dependable` beside an owned fault on 3 of 28 beats); a higher or a cold word stands; none derives nothing | `DOC` — the review s1 (a free-text cost is the gloss restated: "candour" on 11/14) |
| `severity.DEBT_ENTRIES` | gave / repaid | the two POSTINGS the engine can make (`refused` and `called in` retired 2026-09-18: words, not transfers — the account moves when the owed thing is delivered) | the names on a debt row | `DOC` |
| `_RATE_POS` / `_RATE_NEG` | low .18 / moderate .12 / high .06 ; slow .20 / typical .30 / fast .45 | `relationship_priors.update`'s six words → a witness's own (α_pos, α_neg) (`rates_of`; an off-table word refuses) | a high threshold to grant is a slow grant; high/fast leans 7.5×, moderate/slow 1.67× | `JUDGMENT` — the constant ±50% / ×⅔ and ×1.5 |
| `_CLIFF_RELEVANCE` / `_CLIFF_FLOOR` | 0.60 / 0.15 | the discontinuity gate on trust: the act word at the floor (≤ `_CLIFF_FLOOR`) AND relevance ≥ `_CLIFF_RELEVANCE` | one unforgivable act drops trust to floor + (e − floor)·(1 − attribution) instead of down a slope; gated on RELEVANCE, so the same act is a cliff for the loyalty-valuer and a slope for someone else; the driver writes the `cliff` rest row | `DOC` — `relationships.md:27`; values `CALIBRATION` |
| `_CLIFF_SEVERITY` | — | RETIRED (gate 4, 2026-09-17) | the dimensions gate overtness only; the cliff reads the act ladder's floor word | — |
| `_ATTRIBUTION` | 6 factors | malice / intent / unknown 1.0, negligence 0.70, coerced 0.35, accident 0.15 | damps how hard an act lands by why it was done. `unknown` is FULL, not damped — absent an explanation, people attribute to intent. **Producer** (gate `seat-attribution`, 2026-09-19): the event seat writes the word (`severity.ATTRIBUTION_WORDS`, a closed four — `malice` folds into `intent`, `unknown` is the omission, neither offered); before this gate nothing live wrote the key and every beat priced at `unknown` | `DOC` — `relationships.md:29` |
| `_CHARITY_FLOOR` | 0.15 | how far a witness will believe the actor's account of WHY | charity scales with trust, so **low trust reads an accident as malice, which lowers trust further** | `CALIBRATION`, and explicitly an EXTENSION of the doc rather than a reading of it. **Carries its own falsifier**: a cast that spirals into mutual contempt from nothing means the curve is too steep |
| `_NEUTRAL` | trust/affinity/respect 0.5, debt 0.0 | what an edge means when none is authored; also the stranger's rest on affinity / respect / debt | definitional | `DOC` |
| `_OVERT_SEVERITY` | 0.55 | above this, an act is public and unmissable | splits acts into overt, and those that take noticing — EXCEPT an act done TO the witness (`act["received"]`), which is overt regardless (s6) | `DERIVED` from precedent — maps `gate.py`'s existing percept split rather than inventing a second axis; the received rule is `DOC` |
| `_DIM_AXES` | — | RETIRED (gate 4): the dimension route — s6 OMITTED means nothing | kept verbatim as `tests/bond_replay.py`'s `_DIMS_CONTROL`, the labelled control arm | — |
| `_RECEIVED_ONLY` | (`debt`,) | axes that move only for the party the act was ABOUT | you owe someone who helped YOU; watching them help a stranger raises your regard, not your debt | `DOC` |
| `severity._ACT` heights | .10 / .22 / .34 / .44 — / .56 / .66 / .78 / .90 | what an act WORD is worth on the bipolar axis scale (four rungs a side, no middle word; the floor word is the only one at or below `_CLIFF_FLOOR`) | the event seat answers in these words and the parse seam prices them (bond-arithmetic.md s2, s4) | `CALIBRATION` — symmetric about the stranger by construction; the anchor/β law (gate 4) and the thermometer fit (gate 6) will move them, and only DOWNSTREAM of a picture |
| `severity._STRANGER` | [.47, .53) | the standing ladder's stranger band; the other eight bands tile the rest evenly | a standing WORD for the thermometer and the log; the actor keeps `direction._EDGE_BANDS` | `DOC` (Fable, settled review item 4: the band had zero width as first derived) |

## attachments.py — what a person holds that is not a person (gate 5, 2026-09-18)

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `attachments.RELATION_HOLDS` | life .85 / post .60 / member .40 / acquainted .15 / none 0 | the relation-word price table (bond-arithmetic.md s3) | the classifier, the director and (later) the keeper name a WORD; `hold_of` prices it; the seat and the classifier never see the numbers | `DOC` s3 — an authoring rubric, not fitted; "so a read is arguable and a number is not" |
| `attachments.RELATION_WORDS` | the four, warm to cool | what a classifier is offered (`none` withheld: a hold that ended is the director's word) | `rubric()` renders them with the boundary tests, digit-free | `DOC` s3 |
| `attachments._LIFE_CAP` | 2 | per-character budget of `life`-tier holds, any source | `validate_block` and `block_from_words` refuse a third (`ATTACH_LIFE_CAP`) — the settled review's guard (b) against "my ship, my crew, my port, my guild, all family" | `JUDGMENT` — settled review s4. **Falsifier:** an authored sheet the owner wants with three life holds |
| `attachments.word_below` | one rung | the self-sourced discount: a hold whose only evidence is the holder's own claim | `declared_row(self_sourced=True)` prices life as post, post as member… until an act corroborates | `DOC` s3 (guard a); the shape of `acquisition._WITNESS_CEILING` |
| `connection._FLOOR` on attachments | .20 (existing) | the feeling reader's dead zone, now applied to `loc.`/`grp.` too | an `acquainted` .15 amplifies no feeling and still gates belief at .15 — one registry, two readers, two floors | `DOC` — settled review 1k; the value is connection.py's own `CALIBRATION` |
| `_DEBT_RATE`'s `hold` term | 1 for a person; a transfer to a thing posts nothing | unchanged | deferred — gate 5 plan section 7 | — |

## bond_rest.py — where an edge rests (gate 4, 2026-09-17)

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `_RETENTION` | trust .97, affinity .90, respect .95, debt .99 | drift per elapsed DAY toward the edge's own rest (`resolve` of the `rest_declared` rows; a stranger's rest where none) | *"affinity fades faster than trust"*; a favour owed is not forgotten in a week; an authored edge at its own rest does not move | `DOC` for the ORDERING; values `CALIBRATION` (bond-arithmetic.md s8: the Moor House gap pins it weakly) |
| `relationship_priors.default_trust` | authored | the stranger's rest on trust (`stranger_rest`) — where an edge the sheet did NOT author relaxes to | its one remaining reader; an authored edge rests where it was authored, or lower after a cliff | `DOC` — BLUEPRINT-character 10.3 |
| `records.REST_SOURCES` | `authored`, `cliff` | the two ways a rest row arrives | seeded from the sheet at run creation / late join / a pre-v28 resume; lowered by a cliff on the causing turn; a rest moves DOWN, never up | `DOC` — bond-arithmetic.md s6 |

## connection.py — how closeness scales what lands

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `_W` | affinity .60, trust .25, respect .15 | the blend that composes closeness from an edge | | ORDERING is `DOC`-backed — `arc.derive_resilience` and `_regard` both already lean on affinity. **The VALUES are `CALIBRATION` and the source says so** |
| `_FLOOR` | 0.20 | hard dead zone below which closeness does nothing | *"the floor buys SILENCE"* — without it every acquaintance at affinity 0.52 shifts every number for no dramatic reason | `CALIBRATION`; the dead-zone FORM is normative. Precedent: `arc._ARC_THRESHOLD` |
| `_GAIN` | 0.75 | how far closeness may amplify | keeps all four affiliation alleles separated at a typical-severe event | `CALIBRATION` **with a named falsifier and the prior failure it prevents**: an unbounded chain once made bravery *"an IMMUNITY rather than a disposition"* |
| `_HOLD_K` | 1.0 | how far investment stretches the emotion half-life: 1 + `_HOLD_K` · c (a full bond or wound doubles it) | the "and the longer it lasts" half of character-model.md's rule, on the emotion tier (gate three, 2026-09-11) | `START` — tuned in runs |
| `_Q_HABITUATE` / `_Q_GRIND` / `_Q_CAP` | 0.80 / 1.15 / 4 | repetition: per repeat of the same about on the same path, softer when absent, harder when present, capped | owner: "Q is good"; the count is read from `turns.tags` (`targets.repeat_count`), never stored | `START` — tuned in runs |
| `PRESENCE_HOLD` | 3.0 | the half-life stretch while the thing a path is about is in the room (a concept is here when the beat names it) | presence stays ONE factor by the owner's ruling | `START` — tuned in runs |
| `_RETENTION_K` | 0.5 | how far closeness may slow forgetting | a fraction of the remaining headroom, so nothing becomes permanent by this route | `CALIBRATION` |
| `SCALED_DIMS` | care_relevant, loss, social_violation | which dimensions closeness scales | wider than `state._REGARD_SCALED_DIMS` by exactly `social_violation` — regard scopes EMPATHY, connection scopes INVESTMENT. **`threat` is held out with an argument**: a threat's subject is the source of danger, so connection-to-subject would be connection to the wolf | `DOC` |

## toward.py — what one specific person makes you feel

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `_STEP` | 0.02 | how far one event moves a feeling toward one person | smaller than the arc's 0.07 because it fires on ORDINARY beats, not only durable ones | `CALIBRATION` — flagged in-source as *"the one number here that is somebody's judgement rather than derived"* |
| ~~`_LIMIT`~~ | ~~0.25~~ | RETIRED 2026-09-12 (the redesign's gate 1): the cap on what one person could earn made a sharp-tongued croquet player tender toward her one steady partner unbuildable (from `quiet` it topped out at concern) | attitude is a level on the path's own ladder, any rung; `_UNIT` 1.0 bounds it as every path float is | — |
| *(none)* — the reading-fed step | `rungs.vector_for(path, rung)` × `connection.magnitude_scale(for_about)` × durability gate | how far one PERSON-bound reading moves what that person has EARNED (`observe_readings`, 2026-09-11; re-scaled 2026-09-12) | the reading's own vector, through the receipt's own bond multiplier (a stranger 1.0, the closest bond 1.75), in full on a durable beat | `DERIVED` — deliberately NOT a second `_STEP`; the bond multiplier is the receipt's, so the two feeds scale alike |
| `_ATTITUDE_PASSING` | 0.5 | the fraction of the reading's vector a PASSING beat charges to attitude (a durable beat charges 1.0) | attitude is slow: what a person has earned comes from what stays, not from every passing moment | `JUDGMENT` — measured 2026-09-12 on the live Holmes read (readalong-holmes-1789164611-09007d): Watson→Holmes is 106 passing / 5 durable of 111, so this knob is ~95% of a recurring relationship's accrual; replayed as pure accrual, 0.25 leaves it at the floor over twelve chapters, 1.0 reaches urge/wonder in ~7 beats (the runaway), 0.5 gives one rung per ~14 beats. One verified origin, no ground-truth target; erosion would push it higher |
| `_OTHERS_DAMP` | 0.5 | how much of a present person's attitude lifts a path when someone ELSE is engaged | someone loved in the room softens the anger at B without cancelling it — a floor, never a sum | `START` — the brief names the mechanism, not the number |
| `_RETENTION` → the staircase's BOTTOM RUNG | per path: WARINESS .93 · STIRRING / DISPLEASURE / LEVITY .95 · RECEPTIVITY / SELF-REGARD .96 · GOODWILL .97 · DISTASTE .98 · DEFLATION .99 | the flat per-DAY retention an attitude used to fade at; since 2026-09-19 (gate `attitude-staircase`) it is rung 1 of the attitude staircase and nothing else | `_attitude_half_life(path, 1)` = `MINUTES_PER_DAY · ln(0.5) / ln(_RETENTION[path])` — the half-life in MINUTES that reproduces the old day rate exactly: WARINESS 13754 · STIRRING / DISPLEASURE / LEVITY 19459 · RECEPTIVITY / SELF-REGARD 24451 · GOODWILL 32770 · DISTASTE 49406 · DEFLATION 99313 | `UNMEASURED`, carried over — the ORDERING is `DOC` (the negativity bias `bonds._ALPHA_NEG > _ALPHA_POS` and `wound._A_DEEPEN > _A_EASE` also carry; WARINESS fades fastest, DEFLATION slowest), the values `CALIBRATION` from the pre-redesign day table, re-measured by nothing in this gate. The name and the values are kept BECAUSE the anchor is derived from them — a rename would sever the doc trail |
| `_attitude_half_life` — the rung ratio | the mood staircase's own, per path: DEFLATION .0073 · DISPLEASURE .0183 · STIRRING .0206 · RECEPTIVITY / WARINESS .0275 · DISTASTE / GOODWILL / LEVITY .0330 · SELF-REGARD .0367 (top rung ÷ bottom rung) | how much shorter the TOP of a ladder drains than its bottom, and by interpolation every rung between | `_attitude_half_life(path, k)` = bottom × `state._rung_half_life(path, k) / state._rung_half_life(path, 1)`, so `state._HALF_LIFE`'s anchors and `_TOP_BURN` move BOTH staircases and the two tiers cannot disagree about the shape of forgetting | `DERIVED` from `state._HALF_LIFE` + `_MID_RUNG` / `_TOP_BURN` — this tier mints no anchor of its own. The inherited tags stand: `MEASURED` for the EPISODE anchors, `JUDGMENT` for the DISPOSITION anchors and the burn factor |

The composition itself carries no constant: `compose(m, a, rest)` is `a` when `a ≥ m`, else the
MIDPOINT of `m` and `max(a, rest)` — the owner's "balance", a fixed half unless a scene says
otherwise (the brief). The rendered half lives in `direction.py`: `_STIRS_FAINT` 0.02 (below it the
balance delta says nothing) and `_STIRS_PLAIN` 0.10 (at or above it the phrase drops "a little");
both `CALIBRATION`. Since 2026-09-12 the delta rendered is `effective − mood` for that person, not
the raw attitude.

## arc.py — what changes who you are

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `_ARC_THRESHOLD` | 0.18 | below this durable magnitude, no baseline diff | most events stay transient | `CALIBRATION` — `arc-engine.md` says threshold and magnitudes are calibration, not derived |
| `_DURABLE_DIM` | 0.6 | a dimension this severe marks a durable candidate | | `CALIBRATION` (same block) |
| `_BASE_STEP` | 0.326 | how far one durable event moves a baseline | | `CALIBRATION` (same block) |
| `_REGARD_GENERALIZE` | 0.4 | how far a bond with a disregarded-class member erodes CLASS regard | | **`MEASURED` — the only one in the stack.** Recalibrated 2026-09-01 to twenty durable events per rung (owner's rate). At the previous 0.07 one severe durable affront moved the mean **+0.00108** on the reference fixture — ninety-three events per rung, so a three-rung arc needed ~280 durable events and no book contains that. Base change was *"architecturally present and perceptually absent"* |
| `_PTG_RESILIENCE` | 0.70 | at or above this resilience, a survival threat writes GROWTH instead of damage | flips the sign of what a trauma does to a character | **`NONE`. The only constant in the stack with no stated basis — and it decides whether an event breaks a person or makes them** |
| `_ERODE` | 0.998 | how fast a temperament mean returns toward what the author wrote | the slowest thing in the engine | `DOC` for the ordering — *the more cue-specific a quantity, the faster it fades*; a wound (0.995) outlasts a debt (0.99) because it is more specific, and tonic identity is least specific of all. Value `CALIBRATION` |

## provider.py — the one frontier-model seam (2026-09-11)

| constant | value | what it is | why | class |
|---|---|---|---|---|
| `DEFAULT_SEAT_MODEL` | `anthropic/claude-opus-5` | the model the appraiser seats run on (`SWE_SEAT_MODEL` overrides) | judgement-critical: a confidently wrong reading poisons the log for the rest of the book; slug confirmed on OpenRouter's public models list 2026-09-11 | `JUDGMENT` (owner: no local models, accuracy) |
| `DEFAULT_TEMPERATURE` | 0.0 | the seats' sampling | replay is from the readings log regardless; two reads of one book are two runs to compare | `JUDGMENT` |
| `TIMEOUT` | 180 s | per call | a frontier model on a 6k-token prefix | `CALIBRATION` |
| `REPLIES_ENV` | `SWE_SEAT_REPLIES` | a directory of answered prompts switches `call` to the replay backend (`use_replies` is the in-process form) | one agent per prompt, out of process, never a batch (owner 2026-09-11); the answer is found by `prompt_key`, the sha256 of the messages, so it only ever meets the prompt it was written for | `STRUCTURAL` |
| reply files | `<key>.reply.txt`, `<key>.prompt.json`, `system.<purpose>.<hash>.txt` | the emitted prompt (user turns + a pointer to the constant system text, written once per purpose and content) and its raw answer | an answering agent reads the ladders once and the passage once; a missing answer is `PROVIDER_REPLY_MISSING`, a malformed one refuses at the parsers | `STRUCTURAL` |

## wound.py — durable damage

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| `_A_DEEPEN` / `_A_EASE` | 0.30 / 0.12 | learning rates on deepening vs easing a wound | *"a chapter of progress can go in one night"* | `LITERATURE` — two independent justifications: the negativity bias `bonds._ALPHA_*` was calibrated for, and the finding that re-acquiring a fear after extinction is faster than the extinction was. Deliberately RESTATED rather than imported, so the two tiers may diverge under probe |
| `_DEFAULT_PERMANENCE` | 0.15 | the floor a wound heals to, never zero | *"healing to exactly zero would delete the character's history; healing to here makes it a mark rather than a wound"* | `DERIVED` by anchor — below `direction._EDGE_BANDS`'s lowest edge (0.25) |
| `_MINT_RUNGS_FROM_TOP` | 2 | a durable beat the seat READ at one of this many top rungs of a path bound to a registry concept mints a wound on (concept, path), at the reading's height | the top band alone is rarely reached; a scar only the amok can earn is decoration (gate three, 2026-09-11) | `START` — tuned in runs |
| `from_profile_row` mapping | x1.4..x2.5 -> 0.40..0.95 | a library wound row's multiplier becomes the minted wound's intensity, linearly, so the library's order survives | the composition pass mints wounds instead of placing wound rows | `START` |
| `_RETENTION` | 0.995 | wound decay per declared elapsed unit | one regime, not two: every wound on disk is authored backstory, consolidated by definition | `DOC` by ordering — above `bond_rest._RETENTION["debt"]` (0.99): **a scar outlasts a debt** |

---

## floor.py — the turn-taking economy (gate lands-on-to-floor, 2026-09-19)

| constant | value | what it is | what it does | basis |
|---|---|---|---|---|
| ~~`LANDS_ON_BONUS`~~ | — | NOT BUILT — `docs/emotion-arithmetic.md` §5 step 5's literal spec, a flat additive term for `listener ∈ lands_on` | measured 2026-09-19 on the 31 recorded beats carrying a seat reply: the seat listed EVERY present listener (34 of 34 listener-beats), so a flat bonus would be a constant added to everyone in the room — arithmetically a lowering of `FLOOR_THRESHOLD`, the owner's open drive-term question (D5). `floor.urge`'s `landed` parameter PRUNES the salience term instead (0 of 30 decided beats on the corpus change under pruning) | — |

---

## What the register says, in three lines

1. **The documentation is not the problem.** Thirty-one of thirty-two constants state a basis,
   several carry their own falsifier, and two record the specific failure the current value was
   chosen to prevent.
2. **The EVIDENCE is the problem.** One constant is measured. Three are literature-anchored. The
   rest are reasoned judgment wearing an honest label. `CALIBRATION` is not a defect — it is a
   promise that a probe has not been run yet, and that promise is outstanding across the whole
   stack.
3. **`arc._PTG_RESILIENCE = 0.70` is the single hole**, and it is not a small one.

## Known omissions from this register

- `severity._MAGNITUDE` (the seven severity words to floats) is authored in `severity.py` with its
  anchors reasoned there; not duplicated here.
- The 83 rung band edges in `rung_blocks.BANDS` are authored per path and documented in
  `docs/rungs/<PATH>.md`. `LAMBDA` above derives from them.
- `compounds.py` moved to `staging/` on 2026-09-08 and has no constants in the live tree —
  **but ten docs still specify it**, which is a separate cleanup.
