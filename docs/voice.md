# Voice — the speech layer and the craft standards (WORKING)

**Status: working.** Audit gap C2: acceptance criterion #2 ("blind voice-attribution beats chance") had a schema slot but **no generation path**, and criterion #6's quality bar — "voice rules, structural lessons, the An Axle standard" — existed nowhere in the repo. This doc gives voice a producer, a consumer chain, and a test; and gives the craft standards a home.

## The voice profile (a BASELINE field — `character-schema.md`)
Voice is **who they sound like**, slow-clock, written at generation, moved only by the arc engine (a character coarsened by years of camps *can* drift registers — a durable diff like any other):
```
voice:
  register:        formal ↔ rough · plain ↔ ornate     # 2 axes, continuous
  vocab_domains:   [trade, scripture, street, court…]  # where their metaphors and idioms come from
  rhythm:          clipped ↔ rolling; interruption-proneness
  assertiveness:   hedges ↔ declaratives (maps from traits: HEXACO extraversion/honesty facets)
  tics:            [verbal habits, oaths, pet phrases]  # few, distinctive, sparse
  code_switch:     [{context, shift}]                   # "in front of the magistrate → formal register"
  silence_profile: when they DON'T speak                # the inhibition side; feeds social_inhibition
```

## Generation (the missing producer — extends `baseline-generation.md`)
Voice composes from the same formative stack as everything else, **no new pipeline**: position/class/culture → register + vocab domains (a dockworker's metaphors are cargo, tide, debt); education/history → complexity + second-register availability (the seminary dropout code-switches); traits → rhythm + assertiveness (the mapping is mechanical from already-generated facets); individuation → tics (authored for principals, archetype-default for the rest). Provenance discipline applies: "why does she sound like that? — the docks," never "the slider was at ornate-0.7."

## Consumption (two readers, same profile)
1. **The character turn** — the profile rides the stable prefix (`scene-assembly.md`): the LLM speaks *as* the voice. Dialogue distinctness is born here, in-sim, where the biography records it.
2. **Narration** — for close-third/first POV prose, the narrator's diction leans toward the POV's voice profile (interiority in their idiom, not house style). `narration.md` owns the knowledge boundary; this profile is the *texture* input it was missing (audit B5d: voice mechanics were attributed to narration.md, which never had them — they live here, narration consumes them).

## The craft standards (criterion #6's artifact, given a home)
The author's codified standards — voice rules, structural lessons, **the An Axle standard** — are *content*, not machinery, and they already exist outside this repo (the writers-desk corpus). The contract:
- **Home:** `books/standards/` — imported as versioned files when book production begins (`craft-voice.md`, `craft-structure.md`, `an-axle.md`). Until imported, criterion #6 is **explicitly unsatisfiable** — that status is now visible instead of dangling.
- **Consumers:** the narration prompt (register/prose rules), the cutting room (structural lessons inform shape discussion), the cut probe's reader rubric (the standards *are* the anchored quality bar — `measurement.md` §4).
- **Never consumed by:** the character turn. Characters speak from their voice profile, not from the author's prose standards — the standards govern the *telling*, not the *living* (the same one-way arrow as everything else).

## The test (closes the criterion-#2 chain)
**Blind voice-attribution** (`measurement.md` §4): unlabeled dialogue lines from the record, judges attribute to character sheets; pass = beats chance per principal pair. Runnable mid-sim (catching voice collapse early — LLM drift toward one house voice is the known failure), not just at acceptance. If two principals' profiles are too close to attribute, that's a *generation* finding: differentiate the profiles or merge the characters.

## Open questions
1. The trait→rhythm/assertiveness mapping table (mechanical, small — author with the first cast).
2. Voice under state: does a terrified formal speaker break register? (Lean: yes — a `state-override` rule per zone, the vocal analog of out-of-character tails; needs the same recorded-tail-sample discipline.)
3. Import format for the writers-desk standards (verbatim files vs distilled rules — decide at import).

## Cross-links
- **Producer:** `baseline-generation.md` (the formative stack; this doc extends its output schema).
- **Schema home:** `character-schema.md` BASELINE `voice` row.
- **Consumers:** `scene-assembly.md` (stable prefix), `narration.md` (POV texture), `cutting-room.md` (standards in the shape discussion).
- **Tested by:** `measurement.md` §4 voice-attribution; serves `acceptance-criteria.md` #2 and #6.
