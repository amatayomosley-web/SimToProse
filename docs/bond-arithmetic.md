# Bond arithmetic — how one person's belief about another is priced, moved, and shown

*(NORMATIVE for what SHOULD BE. `relationships.md` owns the design intent — what an edge is and why it
has four axes; this owns the SCALE, the LAW and the CALIBRATION, the way `emotion-arithmetic.md` does
for the emotion paths. Designed 2026-09-17 with the owner, one piece at a time; reviewed twice by
Fable (`cairn/projects/reviews/2026-09-17-simtoprose-bond-*`). NOT BUILT: the seam and the read ladder
of 2026-09-16 (`bonds.observations_from_social`, `severity._READ`) are the scaffolding this replaces.
Status per section is marked. Nothing here is wired until its gate lands.)*

## 0. The owner's rule, which the rest serves

> "We need to design how bonds grow — along the lines of perceived positive actions towards
> something the viewer holds personal belief in. A woman can believe all children need to eat, but
> someone arranging food for children won't move the bond. Someone arranging food at the orphanage
> she works for would, since the action affects her personal view."

An act moves A's belief about B only through **what A holds** that the act touched. Values in the
abstract move nothing; what is *hers* moves her. Everything below is the machinery for that sentence.

## 1. Two per-person tiers, never confused

| | attitude (`toward.py`) | bond (`bonds.py`) |
|---|---|---|
| what it is | what B makes A **feel** — one float per emotion path | what A **believes** about B — trust · affinity · respect · debt |
| fed by | the emotion seat's person-bound *readings* | the event seat's read of what B *did* — the act |
| read by | the composer (the rung the actor plays toward B) | decisions, transmission, the floor, and the connection multiplier on emotion accrual |

"I love him and I don't trust him": attitude GOODWILL high, bond trust low. Both true. Feeling vs belief.

## 2. The scale — two vocabularies per axis, both on 0..1 [BUILT 2026-09-17, gate 1: `severity.ACT_WORDS` / `act_value_of` / `act_rubric`, `STANDING_WORDS` / `standing_of`, `DEBT_ENTRIES`]

**The act ladder** — inbound, the seat's word: what *this act* showed. Four rungs a side, **no neutral
word**: an axis the act says nothing about is omitted, and omission is the common answer.

| height | .10 | .22 | .34 | .44 | — | .56 | .66 | .78 | .90 |
|---|---|---|---|---|---|---|---|---|---|
| trust | treacherous | dishonest | unreliable | slack | *omit* | dependable | straight (DERIVED from `told`, never named by the seat — 2026-09-18) | loyal | steadfast |
| affinity | cruel | harsh | cold | curt | *omit* | civil | kind | generous | selfless |
| respect | disgraceful | inept | careless | middling | *omit* | capable | sharp | masterly | commanding |
| debt | not a ladder and NOT THE SEAT'S TO RATE (2026-09-18): the seat reports **transfers** — what changed hands, from whom, to whom, on what **terms** (`none · price · loan · repayment`, what was SAID) — and the engine posts **gave** on the receiver's account or **repaid** on the giver's own (§6); each carries the beat's dimension severity as its magnitude; the account is positive-only until gate 6 | | | | | | | | |

The floor word on each axis is the only one that reaches the cliff, and the contract says so: `treacherous`
means betrayal, not unreliability. Each rung carries a gloss AND a boundary test against the rung below,
as the severity words do (`severity.py` `_GLOSS`), so a read is arguable and a number is not.

**The standing ladder** — outbound: where the edge *sits*. Derived from the float by band (`rung_at`'s
twin), read by the thermometer, rendered to the actor. The live beat seat never answers in standing
words — it rates what an onlooker could see (its rule 1), and a standing level is an interior it
cannot see; asking it for one is how yesterday's `social` block fed a level into the arithmetic as if
it were an act. The thermometer (offline, reading a whole book) and the composition pass do read
standing and relation words, by design.

| axis | ← cold pole | | | | stranger | warm pole → | | | |
|---|---|---|---|---|---|---|---|---|---|
| trust | betrayer | distrust | suspicion | caution | — | reliance | assurance | faith | absolute |
| affinity | hatred | dislike | coolness | reserve | — | amity | affection | closeness | devotedness |
| respect | contempt | disdain | dismissal | doubt | — | credit | esteem | admiration | reverence |
| debt | an account: owed to you · square · a favour · an obligation · a debt · bound | | | | | | | | |

Bands: the stranger band is `[.47, .53)`; the eight others tile the rest evenly, four a side. Checked
against all 92 emotion rung names, the nine path names, and the engine's own tokens (`regard` is
`model.regard`, `confidence` is the reply field, `attachment` is the block below — none used).

**Nine words, four blocks.** The standing words exist for the thermometer and the log. The actor keeps
the four decision-shaped blocks `direct_edge` already renders (`_EDGE_PHRASES`, four bands), reached
through a 9→4 map; nine authored blocks per axis are written only after `block_fidelity` shows an actor
plays *faith* differently from *assurance*. `_EDGE_BANDS` stays — `identity_view.py` imports it.

**Retired by this section (done, gate 1):** `severity._READ` / `READ_WORDS` (2026-09-16), whose `neutral`
word the seat would fill; `bond_replay.py`'s `read` arm went with it, and the actor's own reply
contract (2026-09-19, gate actor-contract-cleanup).

## 3. Attachments — what a person holds that is not a person [BUILT 2026-09-18, gate 5: `src/engine/attachments.py`, schema v30 `attachment_declared`, `connection.held_map`, the lint, the composition classifier; the keeper→rubric path BUILT 2026-09-19 (`scripts/keeper.py:attach_scene`, gate `keeper-attachment-rubric`); a transfer to a held thing still DEFERRED]

A new authored block on the sheet. Named `attachments`, not "holdings": `holdings` is already a world
snapshot kind (`snapshots.KINDS`, `schema.sql`). **Two key spaces, not four** (built 2026-09-18):
`loc.<world.locations id>` and `grp.<tag>` where the tag appears in some `world.people[].groups`. A
registry concept already reaches `held_map` through a WOUND (keyed per path); a value already IS the
worth-menu weight — letting this block carry either would give one key two writers with two shapes.
There is no institution type: the orphanage is a location, the guild a group; a cause is held through
its place or its people.

    "attachments": {"loc.orphanage": {"hold": 0.85, "sign": "+", "note": "life: eleven years there"}}

People stay in `relationships` — a person's hold is read off the edge. **`in_group` is retired**
(2026-09-18): across the owner's books and the two fixture templates, a sheet that named a PERSON
lost it (the edge already carries it), a sheet that named a group got a `grp.<tag>` at `member`, and
the empty ones were dropped; `scripts/lint_book.py` refuses the key from this gate on. `sign` is
reserved; v1 arithmetic treats only `+`.

**The rows and the fold.** A hold is a ROW, never a mutable value: `attachment_declared` (schema v30,
append-only by trigger; `source ∈ authored | director | keeper`) — `authored` seeded from the sheet at
run creation / late join / a pre-v30 run's first resume (`attachments.seed`, idempotent), `director`
from the scene cfg's `attachments` declarations at the scene's first turn (`attachments.declare`; a
typed row with a RELATION WORD, `none` for a hold that ended — a director typing a float is the same
defect as a model emitting one), `keeper` deferred. `bond_rest.rehydrate(attachments=)` folds them in
log order at slot 1 — **rest, then hold, then the turn's time declaration, then its movements** — onto
the sheet block in place. The slot is about the resumed SHEET, not the edge: a delta is priced live and
logged as a number, the fold never re-prices it.

**One registry, two readers, two floors** (settled review 1k). `connection.held_map` folds `+` entries
in beside wounds, goals and values; `connection.for_about` reads `loc.`/`grp.` under the feeling floor
(.20 — an `acquainted` .15 amplifies no feeling); `bonds.stake_of` reads the same number unfloored (a
gate is not a multiplier: it gates belief at .15). `floor.bond_moves` and the chair compute the map
once per witness and pass it to `act_from_tags` (`received` by hold), `stake_of` and `reflect(stake=)`.
What a place-object does to the OTHER witness: in a two-hander where the seat names the workshop instead
of the man, the man's stake drops from 1 to his hold and the second order scales with it — correct by
the law, and the measurable risk of listing places at all (the seat's rule-4b sentence is the defence:
a place that is merely WHERE the act happened is not its object). A held object changes the bond tier's
object and not the beat's subject (`resolve_subject` falls to the one other party present) until the
emotion seat can name places.

**Written by three, never by speech:**

1. **The author.** Beside `relationships`, same lint: an unregistered key is an error.
2. **The composition pass**, once per character — the classifier returns a RELATION WORD per registered
   entity with the backstory sentence that supports it; the script prices it. An entity the backstory
   names that the world lacks is reported as a gap, never minted.

   | relation word | hold | boundary test |
   |---|---|---|
   | `life` | .85 | losing it would change her days: her livelihood, her home, her child's home, her life's work |
   | `post` | .60 | her position, crew, parish, ship — hers while she keeps it |
   | `member` | .40 | belongs, attends, native of — one of several such things |
   | `acquainted` | .15 | knows it, passes through, has dealings |

3. **The log, in play** — `attachment_declared(char, entity, hold, sign, source)` rows, folded on
   `rehydrate`. The director declares (dismissed, ship sinks, oath taken). **The keeper triggers the
   rubric [BUILT 2026-09-19, gate `keeper-attachment-rubric`: `scripts/keeper.py:attach_candidates` /
   `attach_price` / `attach_scene`, called from `canon_gate` after `rule_scene`]** once per
   newly-kept entity that the speaker's own utterance bound to himself ("my hand-built ship, she's
   family" → `life`): classifier in `scripts/composition_pass.py:build_attach_classify_prompt` over
   the kept sentence, price table in the engine, the classifier never shown the table. **Guards
   against talking oneself into holdings** (the reliance test is satisfied by relying on one's own
   claim) — THREE, all in `attach_candidates` / `attach_price`:
     1. never a per-beat call — only an utterance THIS PASS's `rule_scene` actually kept, never the
        raw turn stream;
     2. never a T2 claim — only a ruling whose verdict is ESTABLISHED (a superposed boast prices
        nothing);
     3. never a re-price of an existing hold — split across the classifier call because the word is
        not known until it answers: BEFORE, an entity the speaker already holds at or above the
        highest a self-sourced price can ever reach (`post`, since a self-sourced hold always prices
        one rung below the word) is skipped outright; AFTER, a priced row that does not improve on
        the entity's latest existing hold is a silent skip, never a refusal.

   **The match has a producer side too, not only guard 1's consumer side.** An extract's object can
   only equal a registered `loc.`/`grp.` name if the NOTICING pass (the one that writes the extract)
   was shown those names — `build_keeper_prompt` names them, and only when handed a world; `world=None`
   leaves the prompt exactly as it has always been. Without this half the classifier side is
   unreachable from a live reply: a keeper never shown the registry can only phrase an object in
   prose, which no amount of guard-1 correctness downstream can match.

   A self-sourced hold prices one rung below the rubric's word (`word_below`) until an act
   corroborates it; the per-character cap on `life` holds (`attachments._LIFE_CAP`) is enforced at
   the WORD the classifier names, not the discounted stored price — a self-sourced `life` prices at
   `post`'s .60 and could never itself trip the `>= .85` check `validate_block` makes, so the cap is
   applied directly against the word rather than through it; the four boundary tests require *shown*
   dependence, not asserted. A T2 (unkept) entity carries no hold for arithmetic — T2 binds nothing —
   but may be rendered to the actor as a phrase. The arc tier moving holds from durable beats is v2.

Herself is 1, implicit. A hold does **not** follow from values, and does **not** walk the edge graph in
v1. `connection.held_map` folds attachments in beside wounds/goals/values on the same scale, so one
number scales what she feels about an event at the orphanage AND gates what she comes to believe about
the man who caused it.

## 4. The seat's contract [BUILT 2026-09-17, gate 1: `scripts/appraiser.py` `build_event_messages` + `parse_event_reply`; the thermometer and the composition pass are gates 6 and 5]

**The event seat** (live, every beat) gains three fields and loses two (`social`; then, 2026-09-18,
the `debt` verdict — refused as `APPRAISER_DEBT_RETIRED`):

    "object": "<who or what the act was ABOUT: a person here, a person spoken of, self,
               a name from THE ATTACHMENTS, or empty>",
    "showed": {"<axis>": {"word": "<act word>",
                          "quote": "<the words of the action that show it>"}}   ← only the axes this act
                                                                                  spoke to; `social` retired
    "transfers": [{"what": "<the thing, quoted>", "from": <id | self>, "to": <id | self>,
                   "terms": "none" | "price" | "loan" | "repayment"}]           ← usually []; a THING that
                                                                                  ended this beat in the
                                                                                  other's keeping (§6 DEBT)
    "told":      [{"what": "<the words, quoted>", "to": <id>,
                   "cost": "fault" | "exposure" | "none"}]                       ← usually []; what was SAID
                                                                                  at a cost to the teller
    "attribution": {"word": "intent" | "negligence" | "coerced" | "accident",
                    "quote": "<the words of the action that show it>"}           ← OPTIONAL; omitted means
                                                                                  unknown, priced at full
                                                                                  weight (§6)

**The told list and the derived rung (2026-09-18, gate `seat-told`).** The .66 trust word is no
longer on the ladder the seat is shown (`severity.ACT_DERIVED`; the engine's ladder keeps it and
`act_value_of` still prices it). Three instruments on the same 28 beats — bare words, the quote check,
the transfers contract — had the seat naming it on 11, 9 and 9 of 14 first-scene beats against the
review's 4–8 band, and reading the quotes showed why: the span was in the text and did not show the
word. The seat now reports the FACT under the word: `told` rows — what was said, to whom, and the COST
to the teller in the words themselves, a closed choice (`severity.TOLD_COSTS`): `fault` — owned an
error or a wrong of their own; `exposure` — named a loss, a weakness or a liability of their own the
other could use; `none` — plain speech, an answer, an order, a warning. `parse_event_reply`
shape-checks the row (`APPRAISER_TOLD_SHAPE`, `APPRAISER_COST_UNKNOWN`, the quote check), and when a
row's cost is not `none`, derives the rung at the seam: `showed.trust = .66` with the told span as
its quote — when the seat named no trust word, and ALSO when it named a warm word below the rung
(`dependable`): the boundary between those two rungs is "it cost them something to say", and a told
row at a cost is that boundary as a fact. A higher word stands (`loyal` / `steadfast` are explicit);
a cold word stands (a plainly owned lie is `dishonest` only if the seat says so — the derivation never
lowers and never warms a lie). A seat that writes the derived word is refused
(`APPRAISER_WORD_DERIVED`): one read, one source. Not a field: `unwelcome` (the listener's interior —
the seat is thought-blind by contract, and the listener's reaction is the next beat).
**Measured (2026-09-18, `staging/reanswer-told1`, 28 blind opus agents, bands pre-registered):**
28/28 parsed, 0 refusals, nobody wrote the forbidden word; 13 told rows on 11 beats — 5 owned
faults, 8 named exposures — and none on the beats of plain speech that had carried 3 of the 9
`straight` reads. Derived `straight` scene 1 6/14 (band 4–8, against 9 on three instruments), scene 2
5/14 (band 3–6), with one beat the earlier instruments had misread no longer among them.
The lift was written AFTER the data: the rule as pre-registered ("the seat's word stands") scored
3/14 on scene 1, one under band, because the seat wrote `dependable` beside an owned fault on three
beats; the same 28 replies re-parsed under the lift score 6/14 — the amendment is the ladder's own
boundary and is recorded as post hoc. Untouched ladders matched the previous instrument on 9/14 and
12/14; transfer rows on the same 8 beats, same terms, postings 2 + 2 again.

**The quote check (2026-09-18, gate `seat-quote-check`).** Every word in `showed` carries the span of
the action an onlooker would point to. `parse_event_reply` refuses a bare word
(`APPRAISER_QUOTE_MISSING`) and a span the action does not contain, whitespace and case aside
(`APPRAISER_FACT_NOT_IN_ACTION`); the spans are stored beside the priced heights as `quotes` in
`turns.tags` / `events.payload`, so a read can be audited word by word from the log. Why a quote and
not a tighter gloss: the boundary test for the .66 trust word ("it cost them something to say") was
in the prompt when the seat named it on 11 of 14 first-scene beats — a gloss is advice the model can
ignore; a span it has to copy is a claim the parser holds it to (the owner, 2026-09-18: build around
the hardcoding, not more of it). **Measured on the same 28 beats (2026-09-18, `staging/reanswer-quote1`):**
28/28 parsed, 0 refusals — the seat can always find a span; `straight` scene 1 11 → 9 of 14 (band 4–8:
MISSED), scene 2 5 → 4 (in band); axes/beat 2.36 → 2.21 and 1.93 → 2.00; the control ladders MOVED
(affinity+respect words matched the stored reads on 8/14 and 5/14 — respect fired 12 vs 7 and 6 vs 4),
so the scene-2 comparison is void by its own pre-registration and scene 1 sits at the floor. The residual the
parser cannot catch is exactly the one the pre-registration named: a span that is in the text but does
not show the word (a `straight` read quoting a plain statement of fact that cost the speaker nothing). A quote proves
the evidence exists; it does not make the judgment right. The quote check stays — it is the audit
trail, and a refusal path for invented spans — and the conditioned words get their facts (`told`,
`transfers`) in the next gates.

**Attribution (2026-09-19, gate `seat-attribution`).** The law's fifth input (§6) had no producer:
`bonds.act_from_tags` has read `tags["attribution"]` since gate 4 and `_ATTRIBUTION` has priced it
since the same day, but nothing live ever wrote the key, so every beat priced at `unknown` — full
weight. THE SEAT is the producer, not the actor: a closed four (`severity.ATTRIBUTION_WORDS` —
`intent | negligence | coerced | accident`, the same four `bonds._ATTRIBUTION` prices short of
`malice`, which folds into `intent` here, and `unknown`, which is never written, only left out),
with a quote checked exactly as `showed`'s is (`APPRAISER_FACT_NOT_IN_ACTION`; a missing quote
refuses `APPRAISER_QUOTE_MISSING`; an off-list word refuses `APPRAISER_ATTRIBUTION_UNKNOWN`).
Omitting the field is the usual answer and means unknown, unchanged from before this gate. The
actor's own `tags.attribution` self-tag (`prompt.py`) stays as the stub double and the seat-refusal
fallback; the seat's word wins whenever the seat answers.

Rules beside its six: the act, not the person; omit is the common answer (the skeleton shows ONE axis
filled); the floor word is betrayal-grade; the object comes from the lists shown — people present,
people referenced (a T2 name the speaker just invented is legal), THE ATTACHMENTS as world names — never
invented. The seat sees no hold, no owner, no scale. `parse_event_reply` refuses by code an off-ladder
word, an unlisted object, and a `showed` with no object. The seat rates once per beat for every
witness; it is shown the world's attachable names, not any witness's holds.

**The thermometer** (calibration only; read-alongs; every N beats; a separate seat never shown act
reads): *"As of here, where does X stand toward Y?"* → one standing word per axis, both directions,
logged beside the run in `<run>.bonds.jsonl`, never applied.

**The composition pass:** one relation word per registered entity + the supporting sentence.

## 5. The object [BUILT 2026-09-17, gate 3: the seat's object feeds `resolve_subject`; `received` from the object (+ the `held=` hook for gate 5); `events.payload` and `relationship_deltas` (schema v27) carry `object`]

The seat names it; the driver stops guessing. Today `scene.py` sets the bond tier's target from the
beat subject or "the one other party present" — stake 1 both ways in a two-hander, `None` in a
three-hander, where debt, `received`, the second order and acquisition then go dark. Under this design:

- the seat's `object` is the bond tier's object; when it names a person it is also fed to
  `resolve_subject` so the event subject and the act object agree unless the seat says otherwise;
- **`received := object == witness OR hold(witness, object) > 0`** — an act on her orphanage is done
  *to her*, for debt and for the second order, scaled by the hold;
- per witness, `stake(witness, object)`: herself → 1; a person → the edge's affinity above neutral,
  **no dead zone** (a gate is not a multiplier; `connection`'s .20 floor is for magnitude); an
  attachment → its hold; a group → its hold; a class merely *regarded* (`model.regard`) → 0;
  established-but-unheld → 0; T2 → 0;
- one primary object per act; `events.payload` and `relationship_deltas` both gain `object`.

## 6. The law — signed, level-anchored [BUILT 2026-09-17, gate 4: `bonds.law_delta` / `observe` / `stake_of` / `rates_of` / `cliff_axes` / `debt_postings` (2026-09-18); `bond_rest.py` for drift, the rest rows and the fold; simulated and pinned (`tests/test_bond_law.py`), not fitted]

Per witness, per axis the act spoke to. `o` = the act word's height; `e` = the witness's edge;
`d = o − .5`, `x = e − .5` (deviations from the stranger); `β` = one rung = .12 (`_BETA`, the ladder's
rung gap); `g` = the gain:

    g_affinity = stake × attribution × relevance(dominant, worth menu)
    g_trust    = (0.3 + 0.7·stake) × attribution × relevance          a liar seen lying to a stranger still costs him (`_TRUST_STAKE_FLOOR`)
    g_respect  = attribution × relevance                              stake-free: a stranger's mastery earns respect
    g_debt     = stake × attribution

    SAME WING  (x and d on one side of the stranger, or x = 0):
        target t = clamp(d ± β, −.45, +.45)          the act's rung, one rung further out, is the ceiling of what it can teach
        if |x| ≥ |t|: Δ = 0                           the edge already holds more than the act shows: nothing
        else:         Δ = α · g · (t − x)             α = α_pos moving UP the scale, α_neg moving DOWN it
    CROSSING   (x and d on opposite sides):
        Δ = α · g · 2|d| · (o − e)                    α by the sign of (o − e); 2|d| is the evidence weight —
                                                      a near-neutral word barely moves a strong edge
    OMITTED:   nothing. Not neutral, not derived from the dimensions (the dimension route is retired;
               a stub beat, which names no act, moves no edge and the driver prints that it did not).
    CLIFF:     the act word at the FLOOR (o ≤ `_CLIFF_FLOOR` .15) AND relevance ≥ `_CLIFF_RELEVANCE` .60,
               on trust → the edge lands at floor + (e − floor)·(1 − attribution): at full attribution the
               floor, an accident never a cliff. No strength term (`_CLIFF_SEVERITY` retired): `treacherous`
               cliffs at `slight`; `extreme` on its own cliffs nothing. Fires for ANY witness whose relevance
               clears the bar, a bystander included — unforgivability is a stance about the man. The schemer
               row below lands at .150 with the cliff on top of its slope. `cliff_axes` names the axes; the
               driver turns them into a `cliff` rest row (below).
    DEBT:      the account on P→Q is what P OWES Q, in [0, 1]. It moves on a TRANSFER — a fact the
               seat reports (`transfers`: what changed hands, quoted from the action; from; to; `terms`
               as SAID: none | price | loan | repayment) — priced by `bonds.debt_postings`, never on a
               word (the `gave | repaid | refused | called in` verdict retired 2026-09-18: measured
               on the first live scene it fired on 10 of 14 beats, and on one beat it was signed
               backwards — the posting landed on the wrong party of the pair). Per
               ordered pair (from, to) with a transfer: terms none | loan → `gave` +m on TO's account
               toward FROM; terms repayment → `repaid` −m on FROM's own account toward TO, iff FROM
               owes TO (a repayment of nothing owed posts nothing); terms price → nothing, square by
               its own words. ONE gave and ONE repaid per pair per beat, however many things (five
               small things must not outrank one purse). The engine never reads the account to CHOOSE
               the entry — a priced thing is a price whichever way it passes, even between two who
               owe, never a repayment — only to refuse a repayment of nothing; the sign comes from the words.
               m = `_DEBT_RATE` .05 × the beat's dimension severity × attribution × hold (1 for a
               person present; a transfer TO a held thing posts nothing until its rule is ruled — gate 5
               plan section 7: the candidate is every present holder owing at m × her hold, and the
               seat's contract restricts from/to to THE PEOPLE today). `refused` and `called in` are
               DEAD: words, not transfers — the account moves when the owed thing is DELIVERED. The
               row carries `cause` = the thing (schema v29). The signed "owed to you" side is gate 6.
    SECOND ORDER: when the act is RECEIVED, its AFFINITY read also moves `their_view.affinity`
               (`reflect`: expectation = their_view, cliffs off, the same stake and rates). Trust and
               respect never feed `their_view`; a bystander reflects nothing. `_SECOND_ORDER_EXTRA` retired.

**Attribution's producer** (§4, gate `seat-attribution`, 2026-09-19): the event seat writes the word; the actor's own self-tag is the stub double and the seat-refusal fallback only.

**The reach and the clamp.** The same-wing target clamp ±.45 puts the law's reach at .95 / .05 — the
top word .90 plus one rung of grace. The crossing branch cannot overshoot (|Δ| ≤ α·2|d|·|o − e| < |o − e|
at any α below 1/(2|d|)); `apply_deltas` keeps [0, 1]. So an authored .95 or .05 holds: nothing confirms
it, nothing erodes it short of a crossing read.

**Stake** (`stake_of`, §5): herself → 1; a person she holds an edge to → max(0, 2·(affinity − .5)), no
dead zone (a gate is not a multiplier); a thing she holds → the hold (gate 5); anything else → 0, the
owner's rule as a number. **`self`** resolves per witness to the actor as a person (`act_from_tags`
maps the seat's `self` to the actor's id before stake and `received` are computed — it passed the
literal until 2026-09-18 and priced every self beat at stake 0): a stranger's act on himself moves her
affinity by nothing, her trust by the floor, her respect in full; a friend's moves her affinity by how
she holds him. A bystander call
without a stake is REFUSED (`BONDS_STAKE_MISSING`) — never silently 1.

**Per-witness rates** (`rates_of`): `relationship_priors.update` — `grant_threshold` low/moderate/high
→ α_pos .18/.12/.06, `withdraw_speed` slow/typical/fast → α_neg .20/.30/.45 [JUDGMENT: the constant
±50% / ×⅔ and ×1.5]. No `update` → the constants; an off-table word is refused (`BONDS_RATE_WORD_UNKNOWN`).
The two fixture templates and the owner's live sheets that set it are its only authored users. A high threshold to grant
is a slow grant; a fast withdrawer leans 7.5× against a moderate/slow one's 1.67×.

**Why this shape** (`cairn/projects/reviews/2026-09-17-…`; simulated on the ladder above at g = 1 and
pinned number by number in `tests/test_bond_law.py` [1]):

| case | result |
|---|---|
| Watson .75, twelve `kind` acts | → .774 and stops: an edge rises to what the acts show, one rung past, no runaway (68 warm acts reached *devotedness* under headroom-only growth); sixty → .78, three hundred → .78 |
| Watson .75, three `curt` acts | → .718: a near-neutral word moves a strong edge by the evidence it carries, not by the gap |
| distrusted .30, one `dishonest` act | → .24: falls (the unsigned draft made this RISE +.005) |
| stranger .50, one `dishonest` act | → .38: a stranger can be distrusted (the draft could not); at a fast withdrawer's rates .32, at a slow one's .42 |
| stranger .50, one `dependable` act | → .52: slow |
| `generous` from an enemy .20 / a friend .90 | +.04 / 0: a kindness from an enemy moves more (relationships.md's first example) |
| `treacherous` by the trusted .90 / a schemer .20 | −.19 then the cliff / −.045 then the cliff: both land at .150; the trusted fall furthest before it (the second example) |
| Jane, on trust: six `steadfast`, one `treacherous` (slope), eight `straight` | .50 → .74 → .59 → .71: a climb, a fall, a recovery over chapters (the .66 trust word is `straight`; `kind` is the affinity word at that height) |
| a stranger under forty `kind` acts | → .78 and stops; forty `selfless` → .95: the anchor, not the count, sets the ceiling |

What it gives up, deliberately: neutral evidence does not correct a false belief (the governess in
*The Turn of the Screw* holds hers against a book of it). What it keeps from the built law: the
crossing side IS prediction error, with its betrayal numbers.

**Overtness** (`witnessed`) takes severity from the dimensions, not from `|o − .5|` — the read is a
quality, not a strength, and reading it as strength blinded a witness to every act done in front of
her. An act whose object is the witness, or a thing she holds, is always overt: that is
`act["received"]` (gate 3's definition, held-extended in gate 5), tested nowhere else. Recognition
(pinning an act on a stranger needs insight) is unchanged.

**Drift** (`bond_rest.drift`) relaxes each edge toward its own REST. An AUTHORED edge rests where it was
authored, seeded from the sheet as `authored` rows in `rest_declared` (schema v28) at run creation, at a
late join, or at a pre-v28 run's first resume — and lowered by a cliff, as a `cliff` row riding the
causing turn. An edge the sheet did NOT author rests where a stranger does: `default_trust` on trust,
`_NEUTRAL` elsewhere (`stranger_rest`) — `default_trust`'s one remaining job, and what
BLUEPRINT-character 10.3's "what they assume about a stranger" now literally means. **It is also BORN
there** (`bond_rest.whole`, 2026-09-19): the first act that prices an undeclared edge — the law's read
in `floor.bond_moves`, both drivers' apply, the fold's first movement, the replay tool — creates it
whole at the stranger's rest, so the sheet's assumption about a stranger applies at the first meeting
and not only after days of drift. Until then the edge was created EMPTY and every reader defaulted the
axis it lacked to `_NEUTRAL`: on the first live stranger case three beats of a stranger's acts left
the witness with affinity and respect and NO trust axis, read as .50 where the witness's sheet assumed
far less of a stranger, and `drift` skips an axis the edge lacks. Two consequences, both the sheet's
own: a wary sheet's first `dependable` read of a stranger is a CROSSING and moves less than it would
from .50 (the crossing branch weighs the word; `tests/test_bond_law.py` [13] pins the numbers); and the
actor reads the stance from the edge's first movement on (a wary sheet's trust renders `distrust`,
where an absent axis rendered nothing). Birth is not
acquaintance: `witnessed` keys recognition on the STORED edge, which the callers hand it before
`whole`. A rest moves DOWN,
never up. The rest is log-derived and never stored on the edge (a mutable value with no log row is the
v12 defect): `resolve` reads the latest row per axis, `rehydrate` walks rests, declarations and movements
in log order (rest, then time, then edge within a turn). The pre-v28 replay rule: a log written before
the table replays toward the stranger's rest, which is what its numbers were computed against.
`their_view` has no rest row and does not drift.

## 7. What the actor sees [BUILT 2026-09-19, gate attachments-to-actor: `direction.direct_holds` over `volatile.holds`; the four standing blocks, the second order and the stirs line were already built]

The line the actor already reads, extended. Per present person: the four standing blocks (stranger
band omitted), the second order ("and as you read them, …"), the stirs line from the attitude tier.
NEW: **"What is yours here: the *Marguerite* — your life's work"** for any attachment present or the
beat's subject, the relation word rendered as a phrase. No digit anywhere; `test_no_digits` and
`test_prompt_sections` police the line. He is never handed his own prior prose: what his words
became reaches him as state, the fence, and a relevance-gated memory. **Built exactly this
way, with the presence rule spelled out:** an entity qualifies when it is a percept this turn
(a `loc.` ref, `gate.py`'s own namespace) or is the beat's own subject/target; a `grp.` hold has
no percept of its own to be present as, so a group renders only when it is the beat's subject,
not yet for a present member of it.

## 8. The constants and what pins each [BUILT, NONE FITTED — `docs/constant-register.md` carries the register rows]

| constant | START | what it governs | fitted from |
|---|---|---|---|
| α_pos (`_ALPHA_POS`) | .12 | rise per unit gap toward the anchor / on an upward crossing | single charged acts: Jane→Rochester, Henry→Wilson — well; fitted at gate 6 |
| β (`_BETA`) | .12 | one rung; the anchor's reach — DERIVED: the ladder's rung gap | Holmes: standing never exceeds the highest act read by more than a rung — well |
| α_neg (`_ALPHA_NEG`) | .30 | fall per unit gap; NEG > POS is the negativity bias, 2.5× the choice | one drop per book — weakly |
| reach (`_REACH`) | .45 | the same-wing clamp: .95 / .05 as deviations — DERIVED: the top word + β | — |
| trust's stake floor (`_TRUST_STAKE_FLOOR`) | .30 | honesty to a stranger is still evidence about him; loyalty to HER is more | JUDGMENT (settled review) |
| cliff (floor word, `_CLIFF_RELEVANCE` .60, `_CLIFF_FLOOR` .15) | | when betrayal is a discontinuity; the trigger is the floor ACT word | the altar; Victor→creature — two events: a design knob, checked |
| `_CLIFF_SEVERITY` | — | RETIRED: the dimensions gate overtness only | — |
| per-witness rates (`_RATE_POS` .18/.12/.06, `_RATE_NEG` .20/.30/.45) | | `relationship_priors.update`'s six words | JUDGMENT: the constant ±50% / ×⅔ and ×1.5 |
| retention per axis (`bond_rest._RETENTION` .97/.90/.95/.99 per day) | | drift toward the edge's declared rest | the Moor House gap — weakly |
| debt rate (`_DEBT_RATE`) | .05 × severity × attribution × hold, per transfer pair per beat (`bonds.debt_postings`) | how fast a thing taken on the book becomes an obligation | JUDGMENT, anchored to `severity.DEBT_STANDING`: five `marked` gifts cross "a favour" (.15), twenty reach "a debt" (.60); at the earlier ~.03 a scene of gifts cannot cross a band, at the old .35 three gifts saturate. Falsifier: an account reaching "a debt" inside one ordinary scene |
| `_OVERT_SEVERITY`, the two DCs | .55 | who notices a quiet act; a received act is overt regardless | not in prose; set so a witness sees the acts done in front of her |
| relation-word prices | .85/.60/.40/.15 | attachments | authoring rubric, not fitted |

**Method** — the emotion method exactly: (a) the event seat under this contract reads every beat of a
read-along; (b) the thermometer samples the standing words every N beats; (c) `bond_replay` + a scorer
replays the acts from the authored edges under candidate constants and scores edge-vs-thermometer per
axis against the baseline *authored edge held static* (as λ was scored against rest). Holmes must not
move Watson→Holmes by more than a rung. **After gate 6, re-run the λ fit once**: edges feed
`connection._W`, and on one pair the multiplier swings 1.00–1.61 once edges move; λ was fitted at 1.38.
Measured over the owner's first live scene under the built law: one direction's multiplier moves only
in the third decimal and the other stays at 1.0 (below the .20 floor both ways) — a book, not a scene,
moves an edge across the floor or a cliff, which is why the re-fit waits.

## 9. Build order [GATES 1, 3, 4 DONE; 5, 6 OPEN]

1. **Rename** `holdings`-in-design → `attachments`; retire `_READ`, the `read` arm, [18]'s seven checks.
2. **Contract + parser + re-answer** — DONE 2026-09-17. `object` and `showed` in the seat; the parser
   refuses by code (off-ladder, unlisted object, `showed` without object, the retired `social`); the 14
   event prompts of the first live scene's longest run rebuilt from the run's log (`tests/reanswer_event_seat.py`; the user turns
   match the cached originals byte for byte modulo the swapped lines) and re-answered out of process,
   one agent per prompt at the seat's own tier. **Measured:** 14/14 parsed, 0 refused; an object on
   14/14 (a two-hander — always the other party; the field is exercised, not yet discriminating);
   **2.36 named axes per beat against the GREEN of ≤ 1.5 — missed.** `trust: straight` fired on 11 of
   14 beats: the seat reads plain speech as a trust showing, though the gloss's boundary ("it cost them
   something to say") should exclude most of it. The reads are otherwise sane — every read but one
   is warm-wing; `durable` still 5/14. Replay under the OLD law (`bond_replay --mapping act`): one
   edge moved a few hundredths; the other did not move at all, because its holder witnessed 0 of the
   7 acts in front of them (every one below `_OVERT_SEVERITY` .55, and the subtle-act check failed) —
   the defect gate 4's overtness fix answers. The severity control arm still cools trust; the act arm
   does not. **Open before gate 6:** tighten the `straight` and `sharp` glosses (or add "name at most
   one axis unless the act plainly shows two") and re-answer once more — one re-answer is one data
   point per beat, so the rate is a finding, not a fit. `test_bonds` [18] flipped.
3. **Object plumbing** — DONE 2026-09-17. The seat's object is `resolve_subject`'s `named` (the actor's
   `subject` stays as the stub's fallback); `received := object resolves to the witness`, with a `held=`
   hook that gate 5 fills; the beat's event payload carries `object` + `showed`; `relationship_deltas`
   gains `object` at schema v27 (ALTER on a migrated db). A three-hander now receives for the named
   party only and the second order fires for them only (test_bonds [19]).
4. **The signed law + per-edge rest** — DONE 2026-09-17. `observe` rewritten on the form in §6
   (`law_delta` is the ungained law; `stake_of`, `rates_of`, `cliff_axes` beside it; `own_account_entry` retired for `debt_postings` 2026-09-18);
   the module SPLIT at the 500-line pin along the seam the two clocks already had — `bonds.py` is the act
   and the law, `bond_rest.py` is drift, the rest rows (`write` / `rows_for` / `seed` / `cliff_rows` /
   `resolve`) and the ordered fold (`rehydrate`); `rest_declared` at schema v28 (append-only, two sources);
   both drivers seed at create / late join / pre-v28 resume, write a `cliff` row on the causing turn, post
   the actor's own `repaid`, and print CLIFF / repaid lines; a stub beat says "no act — the tags carry no
   `showed`". The first scene's replay under the built law (`bond_replay --mapping act`): unwitnessed 0
   (was 7 of 7), and both edges moved within a few hundredths — the replay exercised the anchor, growth
   from a stranger, the near-neutral crossing, debt at the new rate, per-witness α and always-overt; the
   negative wing, the cliff, attribution, the stake gate and drift are `tests/test_bond_law.py`'s, and
   its [12] drives the replay path itself over invented beats. **The ledger rule lifts here: the
   next live scene runs under §6.** `test_bonds` re-based on seat-shaped fixtures; `ledger.py` sits at the
   300-code-line bound after the split (the rest table's I/O lives in `bond_rest`, the seam
   `claims` / `targets` / `readings` / `wound` already use).
   **2026-09-18, after the first live scene: facts in tags.** The seat's `gave` verdict fired on 10 of
   14 beats and once signed backwards; the gloss route was closed by
   measurement (a quote proves the evidence exists, not that the judgment is right — s4). Gate
   `seat-transfers`: the seat reports `transfers` (what, from, to, terms as said), `bonds.debt_postings`
   derives the entry from the words and the accounts, `relationship_deltas.cause` (v29) carries the
   thing; `refused` / `called in` dead; the chair gained its roster (the packet's edges) so the seat
   can name a party there at all. MEASURED (28 fresh blind opus agents, user turns byte-identical
   to the live prompts, bands pre-registered): parsed 28/28, refused 0; transfer rows 6 + 6 on exactly
   the eight beats where a thing changed hands, none on the
   twenty beats where nothing did; every row's terms read as the prose said them; the engine derived
   2 + 2 postings against the verdict's 7 + 10, every one on the receiving party of its transfer (the
   beat the verdict had signed backwards now posts the right way); both accounts after both scenes
   ended well below what the live verdict had posted, one at zero where the verdict had posted a debt.
   The ladders the change did
   not touch matched the previous instrument on 12/14 and 10/14 beats; `durable` 4/14 + 4/14 against
   5 and 10 (the coupling of a transfer to a `durable` tag gone). `straight` unchanged at 9/14 + 5/14 — the quote alone
   does not bring it into band; `told` is the next fact.
   **2026-09-18, gate `seat-told`:** the .66 trust rung leaves the seat's ladder and is derived from a
   `told` row at a cost (s4): derived 6/14 + 5/14 against 9 + 5, plain speech no longer a
   trust showing; the lift over `dependable` written after the data and marked so.
   **2026-09-19, gate `stranger-edge-birth` (the rest half):** an undeclared edge is BORN whole at the
   stranger's rest (`bond_rest.whole`, s6) at every birth site — the fold, `floor.bond_moves`, both
   drivers, the replay tool — instead of empty-then-.50. Found by the first live stranger case (a
   stranger's first scene with the witness): the witness's edge carried affinity and respect and no
   trust after three beats. Measured on a copy of that run's db: the born trust axis appears at the
   sheet's `default_trust` and every other
   number on all three edges is unchanged to four decimals (`tests/test_bond_law.py` [13] pins the
   birth, the fold, the law's read from the born value, and that birth is not acquaintance).
5. **Attachments** — DONE 2026-09-18 (gate `bond-attachments`): sheet block, `attachment_declared`
   (v30), `held_map`, lint, the `in_group` sheets migrated per shape (a person — deleted; a group —
   a `grp.` hold; empty — dropped), the composition-pass classifier (a relation word per registered
   entity, never a number; a gap reported, never minted). **The keeper→rubric path BUILT 2026-09-19**
   (gate `keeper-attachment-rubric`): `keeper.attach_candidates` / `attach_price` / `attach_scene`,
   called from `canon_gate` after `rule_scene`, with all three guards named at s3 point 3 above (the
   two this row used to call built — `word_below` for a self-sourced hold, the `life` cap — plus the
   third, never a re-price, split across the classifier call). `canon_gate` gained a `world=None`
   keyword (both drivers now pass `world=world`); absent a world the pass fails closed and asks
   nothing. Still no LIVE scene has produced the trigger (testing paused; see the gate's own
   OMISSIONS). A transfer to a held thing stays DEFERRED, pinned as posting nothing. **Measured (28
   beats, two arms):** the control replay on
   the migrated sheets is identical to three decimals (the fold is clean); the re-answer with the
   world's places on the seat's line named a PERSON on 28/28 (band 1-6 places, missed below —
   in the safe direction: no object drift), because nothing in the two scenes is done TO a place. The
   engine side is pinned by `tests/test_attachments.py`; the seat's held-object read is unexercised on
   prose until a scene acts on a place.
6. **Thermometer + fits** — the seat, the scorer, the constants; then the λ re-fit. **POST-BOOK by
   its own design (marked 2026-09-18):** the thermometer reads a WHOLE BOOK offline (every N beats,
   never shown act words) and the scorer fits the constants edge-vs-thermometer across it — there is
   nothing for it to read until the book has been run. It is not an unfinished gate blocking the run;
   it is the calibration the run produces the material for. Until then every `CALIBRATION`-tagged
   constant in `docs/constant-register.md` keeps its design value and λ stays 1.383.

**Migration:** every sheet that carried `in_group` (the repo's two fixture templates included); authored edge floats stay floats
(standing words are read-only); `in_group` per shape with lint; `_READ` retires with its tests.

## 10. What this retires

`relationships.md:26`'s "prediction-error, not raw event" as the whole law (it survives as the crossing
branch); drift toward `default_trust` for an authored edge (it stays the STRANGER's rest); `social` as a
severity-word block; the driver guessing the object; `severity._READ`; the worth menu as the ONLY
relevance (it stays as a factor inside `g`; the owner's rule adds the stake); `bonds._DIM_AXES` (the
dimension route — kept only as `bond_replay`'s labelled control arm); `_CLIFF_SEVERITY`;
`_SECOND_ORDER_EXTRA`; `_DEBT_DIMS`.
