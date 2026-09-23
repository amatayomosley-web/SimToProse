# narrative-craft — reference index

The deep reference files for the `narrative-craft` skill. **These are authored in a later pass**; this index is the plan. The parent `SKILL.md` holds the one-line framework catalogue and the how-to-use method — read it first. Each file below expands its `SKILL.md` section on the shared toolbox format (`docs/agent-toolboxes.md`): **When to load · Canon (the `docs/` file it digests) · the menu of frameworks (peers, not a ladder) · the repo default (flagged swappable) · in-practice examples · limits.** Every file stays **framework-neutral** (rival modes held side by side) and keeps the craft pointed at the one non-negotiable it serves: the narrator's knowledge for a scene = the POV character's vault for that scene (`docs/narration.md`).

Files are ordered to the narrator's decision-flow: **perspective → distance & mind → time → surface texture** — the same order as the `SKILL.md` index.

---

## A. Perspective & the knowledge boundary

### 1. `point-of-view.md` — person & perspective
- **When to load:** first, before any other craft choice — fixing whose knowledge bounds the scene, and from when, governs everything downstream.
- **Canon:** `docs/narration.md` (the second boundary; which-entity and from-when; multi-POV switching; the frame-narrator; head-hopping as the prose-layer leak), `docs/design.md` (LLM call 4 — narration as the output stage).
- **Holds:** first / second / third-limited / -omniscient / -objective · free indirect "deep third" · Stanzel's three narrative situations (narrator vs reflector) · witness/peripheral narrator · frame & embedded narration · multi-POV rotation · real-time vs retrospective (FROM-WHEN) · Genette's narrative person (homo/hetero/autodiegetic) · head-hopping (the failure mode).
- **Repo default (swappable):** **POV-bounded close third** — the mode whose knowledge equals the POV vault, and which `narration.md` recommends over omniscient precisely because it renders the boundary automatically. Omniscient is held in the well as a legitimate mode, flagged as the choice that discards the architecture's gift.

### 2. `focalization-and-narratology.md` — the formal spine (who sees vs who speaks)
- **When to load:** for the rigorous vocabulary of the knowledge boundary, and for handling narrative time (order, speed, frequency).
- **Canon:** `docs/narration.md` ("who says this" — the entity and the boundary), `docs/recording-model.md` (the visibility asymmetry the boundary cuts along: POV thoughts + everyone's actions).
- **Holds:** Genette's who-sees/who-speaks split · zero / internal (fixed·variable·multiple) / external focalization · mood (distance & perspective) vs voice (time·level·person) · order (analepsis/prolepsis) · duration/speed · frequency (singulative/repetitive/iterative) · Bal's focalizer/focalized · Chatman's story/discourse and slant/filter · the implied author (Booth) · the narratee (Prince) · Rimmon-Kenan's synthesis · Hamburger's epic preterite.
- **Repo default (swappable):** **internal focalization** as the formal name for the vault-render — Genette's exact term for "the narrator knows what this character knows and no more." The file supplies the vocabulary; the *why* stays in `narration.md`.

### 3. `unreliable-narration.md` — the gap between the telling and the truth
- **When to load:** when the POV misperceives, self-deceives, or lies — and to render the recorded thought≠action gap on the page.
- **Canon:** `docs/recording-model.md` (a lie = thought ≠ action, recorded as both; the reader sees only the action unless the liar is POV), `docs/knowledge-model.md` (thoughts never transmit → misreading is structural), `docs/narration.md` (the POV's (mis)reading is all the reader gets of another mind).
- **Holds:** Booth's unreliable narrator & the implied author as yardstick · Riggan's typology (pícaro / madman / clown / naïf / liar) · Phelan & Martin's three axes (facts / values / knowledge) · Phelan's six subtypes (mis- vs under- reporting/reading/regarding) · bonding vs estranging unreliability · Nünning's cognitive/constructivist model · Olson's discordant vs fallible · the naïve/innocent eye · dramatic irony from unreliability · the project's deception bridge.
- **Repo default (swappable):** **unreliability by construction, not by authorial trick** — in this system the "gap" is already in the record (thought vs action); the narrator renders the action and, when the liar is POV, the lie-in-progress. The literary typologies are the craft face of that recorded gap.

## B. Distance & the rendering of mind

### 4. `narrative-distance.md` — the zoom (psychic distance)
- **When to load:** when tuning how near or far the prose sits from the POV's consciousness, within a scene.
- **Canon:** `docs/narration.md` (close third as the recommended render), `docs/design.md` (append the *direction*, not the stats — distance is the qualitative-render analog: the prose renders "gripped by fear," never "fear 8/10"), `docs/recording-model.md`.
- **Holds:** Gardner's psychic distance · the five-rung ladder (the worked example) · distance as a movable dial · distance ↔ focalization & FID · deep POV / deep third · filtering / filter words · authorial vs figural distance · the camera metaphor & its limits · empathy vs irony as distance-effects.
- **Repo default (swappable):** **close, and movable** — sit near the POV's consciousness by default (the vault is right there to render), pulling back for context and pressing in for the emotional beat. A fork may hold a more distanced, authorial default.

### 5. `free-indirect-discourse.md` — the dual voice
- **When to load:** to render a character's thought or speech in the narrator's third person — the engine of vault-bounded irony.
- **Canon:** `docs/narration.md` (the payoff line: "Marcus smiled, and she took it for warmth" — dramatic irony from a vault-bounded narrator), `docs/recording-model.md` (narration renders the POV's recorded interiority; FID is how it fuses with the telling voice).
- **Holds:** FID / style indirect libre / erlebte Rede · Cohn's narrated monologue · Pascal's dual voice · Banfield's unspeakable sentences · Flaubert & Austen · the Leech & Short speech/thought cline (FDS…NRSA / FDT…NRTA) · free indirect thought vs direct/indirect · Bakhtin's double-voiced discourse · deixis in FID · the irony engine · coloring/contagion.
- **Repo default (swappable):** **FID as the house irony-engine** — the preferred means of rendering the POV's misreading *as* the prose's own claim, so the reader is wrong exactly where the POV is. This is craft in service of the boundary, not a mandatory style.

### 6. `rendering-interiority.md` — turning recorded thought into a mind on the page
- **When to load:** when the POV's inner life must become prose — without inventing it.
- **Canon:** `docs/recording-model.md` (thoughts are the source of interiority; "narration renders recorded interiority, doesn't invent it" — the grounding rule), `docs/narration.md` (the POV's interiority is theirs alone to render).
- **Holds:** Cohn's three modes (psycho-narration / quoted monologue / narrated monologue) · consonant vs dissonant narration · interior monologue (direct/indirect; Dujardin) · stream of consciousness (James's term; Joyce/Woolf/Faulkner) · Humphrey's four techniques · soliloquy · autonomous monologue (Molly Bloom) · Palmer's fictional minds / thought report · rendering sensation & perception · the grounding rule.
- **Repo default (swappable):** **grounded interiority** — render the POV's *recorded* thoughts, never confabulate depth at write-time. Which of Cohn's modes to use is a free craft choice per scene; that the content is recorded, not invented, is the non-negotiable.

## C. Time

### 7. `tense-and-time.md` — when it's told
- **When to load:** when choosing past vs present, or coupling tense to a real-time or retrospective POV.
- **Canon:** `docs/narration.md` (the FROM-WHEN axis: real-time → pure irony vs retrospective → knows the arc, may foreshadow), `docs/design.md` (narration as the output stage).
- **Holds:** past / epic preterite (Hamburger) · present tense (immediacy, restricted knowledge, the rise & the backlash) · historical present · future/conditional (Butor) · tense ↔ POV coupling · order revisited (analepsis/prolepsis) · tense shifts as signal · duration & the "now" of narration.
- **Repo default (swappable):** **past tense, real-time knowledge** — the pastness-less preterite paired with a narrator who knows only up to the moment, for the cleanest dramatic irony. Present tense and retrospection are peers in the well, each changing what the narrator is allowed to know.

## D. The texture of the prose

### 8. `voice-and-diction.md` — the felt personality of the telling
- **When to load:** when establishing or distinguishing a narrator's voice, or matching diction to a POV.
- **Canon:** `docs/design.md` (the continuity/critic gate is hybrid — "distinct-voice / tone is LLM"; this file is that check's craft face), `docs/narration.md` (each scene's narrator is bounded by, and colored by, its POV).
- **Holds:** voice (the sum of diction/syntax/rhythm/stance) · lexical register (high/middle/low) · Latinate vs Anglo-Saxon · concrete vs abstract · tone & attitude · the three classical styles (genera dicendi) · idiolect/dialect/sociolect · persona & ethos · Bakhtin's heteroglossia · skaz · distinct voices (the critic's check) · word music & connotation.
- **Repo default (swappable):** **one distinct voice per POV** — a separable idiom for each viewpoint so the reader never confuses two minds (the property the continuity critic validates). The specific register is a per-book, per-character choice.

### 9. `show-vs-tell.md` — dramatize or report (the prose grain)
- **When to load:** when deciding whether a moment should be rendered in the senses or stated.
- **Canon:** `docs/design.md` (LLM call 4 — narration; the prose renders *direction*, not stats), `docs/narration.md`, `docs/recording-model.md` (mechanics manifest in the recorded thought, which the narrator renders — not as exposition).
- **Holds:** show vs tell (and its narrow truth) · Chekhov's dictum · Lubbock's "dramatize" · James's scenic method · the reality effect (Barthes) · the objective correlative (Eliot) · the significant detail / synecdoche · "thisness" (Wood) · filtering & the removed narrator · the honest counter (telling is not the enemy) · what to show vs tell.
- **Repo default (swappable):** **show the hinge, tell the tail** — dramatize the load-bearing, emotionally charged moment; tell the connective tissue. A discipline against both the "never tell" dogma and undramatized summary; the counter-case (earned telling) is held explicitly.

### 10. `scene-and-summary.md` — the pace of the telling
- **When to load:** when deciding to stage a moment blow-by-blow or compress it, and how the two alternate.
- **Canon:** `docs/narration.md` (the unwitnessed-scene constraint — what *can* be a scene is bounded by whether a POV was present), `docs/design.md` (the depth rule / value-granularity: resolve to what the book levers on — here, at the prose layer).
- **Holds:** scene vs summary · Genette's five speeds (pause / scene / summary / ellipsis / stretch) · scene (isochrony) · summary · ellipsis · descriptive pause · Bentley's scene/summary/description · pacing & the rhythm of alternation · enter late, leave early · the depth rule for prose · the unwitnessed-scene constraint.
- **Repo default (swappable):** **dramatize the hinges, summarize between** — the depth rule as pacing; density where the book levers, speed where it doesn't. Bounded by the hard constraint that only a POV-witnessed moment can become a scene at all.

### 11. `prose-rhythm-and-cadence.md` — the music of the sentence
- **When to load:** when a passage needs to move — for punch, momentum, weight, or fall.
- **Canon:** `docs/narration.md`, `docs/design.md` ("every word is generated" — the LLM is the voice; sentence music is the irreducibly generative surface no engine computes).
- **Holds:** the sentence as the unit of style · loose/cumulative (Christensen) · periodic · balanced · parataxis vs hypotaxis · sentence-length variation · schemes of repetition (anaphora/epistrophe/anadiplosis) · asyndeton & polysyndeton · tricolon & isocolon · chiasmus & antithesis · sound (alliteration/assonance/consonance/sibilance; euphony/cacophony) · cadence & the fall · punctuation as tempo · prose rhythm (Saintsbury) · practitioner guides (Le Guin, Tufte, Fish, Forsyth).
- **Repo default (swappable):** **none — rhythm serves the moment.** No house cadence is prescribed; the file is a well of devices to match sound to sense, POV, and pace. The only rule is that the music serve the scene, never decorate it.

---

## Authoring notes for the later pass
- **One file per section of `SKILL.md`, same order, same names** — the index and the catalogue stay in lockstep.
- **Per framework, the toolbox format's fields:** what it is · real-world provenance + key source (accurate, cited, never invented — verify names, dates, and attributions before writing) · its Limit / contested edge · a vivid exemplar (a real passage where possible) · how to use it at the render layer.
- **Neutrality is mandatory:** where modes rival (limited vs omniscient, past vs present, show vs tell, hard FID vs distanced psycho-narration), present both and name the trade-off; the scene chooses, not the file.
- **Keep the boundary load-bearing:** every file ties its craft back to the POV/vault wall (`docs/narration.md`, `docs/recording-model.md`) — the craft exists to *render* the boundary, and never to leak past it.
- **Cross-link to `docs/`:** each file points back to the narration-layer canon it digests (`narration.md`, `recording-model.md`, `design.md` LLM call 4, `knowledge-model.md`), and to the sibling craft files it seams with (distance ↔ FID ↔ interiority; show-vs-tell ↔ scene-and-summary). The `docs/` file stays canon; the reference is its work-time face.
