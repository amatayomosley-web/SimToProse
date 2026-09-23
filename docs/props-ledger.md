# Props ledger — where things are, folded from what the seat already reports [DESIGNED 2026-09-19, NOT BUILT; FALSIFIED AS WRITTEN 2026-09-22 — a contract change comes first]

> **SUPERSEDED 2026-09-22 by the scene-facts design** (the falsification RESULT at the end of this
> file, addenda 13:25 and 13:45). The defect was this design's SHAPE, not its field: an object-state
> snapshot needs one thing's identity resolved across beats, and the seat's `what` is a span of that
> beat's action, so it cannot supply one. The replacement is a ledger of DATED FACTS, which needs no
> identity resolution, and it covers four more forms of the error than props do. Nothing here is built.


*(Design only — the owner reviews before any gate. Written by Cairn under the 2026-09-19 build-out
plan, step 12, after the critic's first pass on real prose. Normative for what SHOULD BE once
approved; nothing here is wired. The falsification this doc asked for was RUN on 2026-09-22 — see the
RESULT section at the end before reading the design as a plan.)*

## The defect it answers

The first model critic pass over the owner's three live scenes (2026-09-18, a critic log kept beside
the book, 14 flags) found the actor tier contradicting itself on OBJECTS AND COUNTS inside a scene:
a thing's holder, its state, its count or its identity changing between beats with nobody touching
it — the RESULT section at the end counts the flags by kind. Every one of these is a fact about
WHERE A THING IS or WHO HOLDS IT, and nothing in the
engine records that today:

- a scene's `props` are a static list of strings in the cfg (`scripts/scene.py`, load_scene_cfg),
  rendered every turn as unconditional percepts (`src/engine/gate.py` "PROPS — the room's physical
  affordances … NOT perception-gated") — the same line at beat 1 and beat 14, whatever happened;
- the world snapshot already CARRIES the fields for it and nothing writes them: `fold.seed` gives
  every agent `possessions: []` (`src/engine/fold.py`) and `docs/world-state-ledger.md` names
  `agents.possessions` and `holdings` as snapshot fields — no event type today moves either for an
  ordinary object (only `seize` / `destroy-asset` touch `holdings`, for assets);
- the event seat ALREADY REPORTS what changed hands: `transfers` = [{what, from, to, terms}]
  (bond-arithmetic.md s4/s6, 2026-09-18), stored on every event payload, read only by
  `bonds.debt_postings` for the account. The fact exists in the log; the world never learns it.

So the actor is told the room's affordances as authored, never as they stand, and the critic can
only flag the drift after the prose is written (gate 11 lets it record a correction; it cannot
prevent the next one).

## The design — one rule

**A thing's whereabouts is a fold of the transfers the seat already reports, seeded by the director's
props, and rendered to the actor as state — never as a number, never as a new seat.**

1. **Seed.** The scene cfg's `props` stay as they are (strings, three to five, rule 5), and gain an
   optional structured form the linter accepts beside the string form:
   `{"what": "the chalk bag", "where": "on the bench", "held_by": null}` —
   a string prop is `{"what": <string>, "where": "in the room", "held_by": null}`. At the scene's
   first turn the driver seeds one `place` event per prop (type `place`, world_map → holdings: the
   prop keyed by a stable slug, its `where`, its `held_by`), the way the director already seeds
   attachments and the keeper seeds world events — as EVENTS, never a decree.
2. **Fold.** `fold.project` gains two branches: `place` sets `snap["holdings"][slug] = {"what", "where",
   "held_by", "since"}`; and every event whose payload carries `transfers` moves each `what` to
   `held_by = to` (matching the transfer's `what` to a seeded prop by normalised substring, the same
   match `parse_event_reply` already runs to check the span is in the action; an unmatched `what` is a
   NEW prop the scene produced — folded in with `where` unknown, so nothing the seat reported is
   dropped). `agents[id].possessions` is derived from `holdings` (every slug whose `held_by` is that
   agent) — one source of truth, the second field a view.
3. **Render.** The props percept (`gate.perception_scope`, the PROPS block) reads the folded holdings
   for the scene's props instead of the cfg strings: "the chalk bag — on the bench" at beat 1,
   "the chalk bag — in the climber's hand" after the transfer. Digit-free; the `since`
   turn is never shown (test_no_digits). Perception-gating stays off for props (an affordance withheld
   is an affordance that does not exist), which is also why the state must be TRUE: an unconditional
   percept that lies is the worst percept.
4. **The critic reads the same state.** `build_critic_prompt`'s facts section carries the holdings
   at the scene's start and end, so a flag can name the fold's own answer ("the chalk bag was in the
   climber's hand from beat 3; beat 7 has it on the bench") — and a correction (gate 11) supersedes the
   transfer event that put it there, which the fold then skips.

## What it deliberately does not do

- **No new seat.** The transfer read is the event seat's existing contract; its measured double-post
  rate (0–1 per scene on the recorded runs) is the noise this inherits, and the correction path is the
  remedy. A "props seat" would be a second reader of the same span.
- **No consumption.** "Spent" (the petrol put in the tank, the fare handed to the driver) is a transfer TO a
  container or a person under `terms: price`; a thing that ceases to exist (a balloon popped) is out of
  scope until a `destroy` transfer term exists — recorded as an open item, not designed here.
- **No numbers to the actor.** Counts ("six eggs") are prose facts the seat reports as `what`;
  the fold keeps the string, the render shows the string. Arithmetic on counts is not this design.
- **Not a schema change.** `holdings` is a snapshot kind already; `place` is a new CATALOG row
  (record-contract.md's registration path, like `tension`); `transfers` are already on the payload.

## Falsification, before any build

Replay the three recorded scenes' transfers through the fold on a COPY of the db (the reply files
carry them) and print the holdings after each beat. The design earns its gate if, on the 14 critic
flags, at least the three contradictions about things that changed hands are decidable from the folded
state alone (the fold says where the thing was when the prose said otherwise). If the seat's
`transfers` miss most of the placements (things set down or put away, not handed over), the seed needs a
`where` per prop and the seat needs a `placed` term — a contract change to register first.

## Size

M once approved: the CATALOG row + `fold.project` branches (S), the cfg form + lint + the seed at
scene start (S), the percept render (S), the critic's facts feed (S), tests over the three recorded
scenes' transfers (M). Owner's review first: the seed's shape (string vs structured props), whether a
transfer TO a container counts as consumption, and whether the render should name the holder by id
or by the world's display line.

## Falsification RESULT — 2026-09-22 (Cairn, session 1d871251; measurement only, nothing built)

**Method.** The fold above, run literally, on a COPY of the live run's db (`live-run.db`; sqlite backup
API; the live db untouched): each scene's cfg `props` seeded as `{what, where: "in the room", held_by: null}` at
the scene's first turn; every `transfers` row moves its `what` to `held_by = to`, matched to a seeded
prop by normalised substring (articles and punctuation stripped, either direction); an unmatched
`what` becomes a new prop with `where` unknown. The recorded event payloads carry NO `transfers` for
the first two scenes (the contract post-dates them) and `[]` on every beat of the third, so the rows come from the
three re-answer arms that carry them — `<book>/staging/reanswer-{transfers1,told1,attach1}/reanswered.json`,
the same 28 beats under three successive contracts. Holdings were printed after every beat and each
of the 14 critic flags judged by hand against the printed state. The replay was a scratch script of
that session, not repo code.

**The seat's transfers over the three scenes:** 12 / 13 / 14 rows per arm. 3 / 3 / 4 of them matched a seeded
prop; 9 / 10 / 10 became new props. The same object arrives under different quotes and becomes
different props: three objects did, each split across two quotes some beats apart, and one of them
matched its seeded string only when a later beat quoted it bare. That is the contract working as
written — `what` must be a span of that beat's action (`appraiser.py:630`), so it is a quote, and a
quote is not an identity. Five physical placements that are not transactions produced 0 rows in
every arm — one of them although `terms: none` exists (`severity.py:233`) and fits it; the seat
wrote nothing. In one arm (attach1) the seat reported an ACCOUNT event, on a beat where nothing
changed hands, as a hand-over.
And `from`/`to` must be persons from the
shown lists or `self` (`appraiser.py:625`), so a transfer to a container or a place cannot exist
under this contract at all.

**The 14 flags against the folded state, by kind.** C = decidable from the state as designed · H =
half · N = not decidable · X = not an object flag.

| kind of flag | flags | verdict | why |
|---|---|---|---|
| who holds a thing | 3 | C 2 · H 1 | in both C cases an earlier transfer row refutes the prose (for one, the seat reported nothing at the flagged beat, so the state after it is stale); the H flag is decided on its holder, not on its count |
| an object's STATE | 4 | N 3 · H 1 | a state change is not a transfer: seeded once, the state never moves, so the props percept would render the wrong state on every beat after the change; the H flag paired a state with a transfer that arrived as a NEW prop while the seeded string still described the thing in place, so the folded state contradicts itself until the seed is split |
| a count, or a thing's identity | 3 | N 3 | counts are outside the design by its own rule; a description is not whereabouts; one thing quoted two ways is two props with no substring between them, and the fold reproduces the duplication instead of seeing it |
| not an object fact (something said, a gaze, a remembered line) | 3 | X 3 | — |
| the voice flag | 1 | X | not this design's |

**Against the bar this doc set** (the three contradictions about things that changed hands): one
decidable by half, and only with a split seed; two not — one of them on either reading of which flag
was meant. **One of three, and that one by half: the design as written does not earn its gate.** The escape clause in
the section above fires exactly — the seat's transfers miss most of the placements. Three premises
measured false on this data: (1) "the event seat already reports what changed hands" — it reports
the ACCOUNT (who owes whom, on what terms), which is what `transfers` was built for on 2026-09-18; a
hand-over without a debt and a debt without a hand-over both occur; (2) normalised-substring
matching — 9 of 12 rows are new props, and identity across beats is not in a quote; (3) "every one
of these is a fact about where a thing is or who holds it" — three flags are not object facts, four
are object STATE, three are counts or identity.

**What it would take — for the owner's ruling, NOT built.** The producer side, in the shape the
2026-09-19 gates used: (a) seed props as a NAMED registry (stable ids, the way `loc.`/`grp.` names
are) with a holder-or-place and a small closed state word where one matters (open|shut,
on|off, in hand|set down); (b) show that registry to the EVENT seat every
beat and add ONE field to its contract — `moved: [{what: <registered name, or a quoted new thing>,
to: <person id | place phrase>, state?}]` — the `seat-attribution` pattern: one more field on the
same reader, no new seat; a new thing the seat names is registered under its own name and reused by
it (the keeper-attach rule); (c) the fold refuses, or flags, a move of a thing the mover does not
hold — that is where a duplicated thing becomes visible; (d) counts stay out. Its
falsifier is this section's, re-run: re-answer the same 28 beats under the `moved` contract (28
Opus prompts — a spend, so it waits on testing) and require the who-holds flags, the duplication and
the state flags above to be decidable. Of the three review items in the Size section, the seed's shape and the holder's
naming are answered by (a); a transfer TO a container as consumption cannot be a seat fact under
the current `from`/`to` rule and belongs, if anywhere, to (b)'s place phrase.
