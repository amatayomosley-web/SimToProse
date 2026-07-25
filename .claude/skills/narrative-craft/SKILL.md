---
name: narrative-craft
description: The narrator's craft toolbox — point of view (first / second / third-limited / -omniscient / -objective), Genette's narratology and focalization (who-sees vs who-speaks; zero/internal/external; order/duration/frequency; mood vs voice), Stanzel's narrative situations, Chatman's slant/filter, the implied author and narratee; psychic/narrative distance (Gardner's ladder) and deep POV; free indirect discourse (narrated monologue, the dual voice, the Leech-&-Short speech/thought cline, Bakhtin's double-voicing); rendering interiority (Cohn's psycho-narration / quoted / narrated monologue, interior monologue, stream of consciousness, Palmer's fictional minds); unreliable narration (Booth, Riggan's typology, Phelan's axes, bonding vs estranging); tense and its effects (epic preterite, present-tense, historical present); voice and diction (register, Latinate vs Anglo-Saxon, heteroglossia, skaz, distinct voices); show vs tell (Chekhov, Lubbock, the reality effect, the objective correlative); scene vs summary (Genette's five speeds, pacing); and prose rhythm and cadence (cumulative/periodic/balanced sentences, parataxis/hypotaxis, the rhetorical schemes, sound, punctuation as tempo). Open it when choosing a POV and distance, bending a sentence into free indirect discourse, rendering a mind without head-hopping, deciding scene vs summary, giving a voice its own music, or holding the prose inside the POV character's knowledge boundary. Framework-neutral — a well of peers, not one prescribed truth.
---

# Narrative Craft — the narrator's prose well

This is the toolbox the **`narrator`** agent draws on while it works. The agent is the *will* (render recorded events into POV-bounded prose; invent nothing; never head-hop); this skill is the *well* — the frameworks, menus, and exemplars it reaches into to tell a scene well.

**It holds craft, never facts.** How to close the distance, merge a voice, or pace a chapter lives here. *What* happened reaches the narrator through the **cut** (the canonized biography); *who* the characters are and *what the POV knows* reach it through the **POV vault slice** — never through this toolbox.

**The boundary is the spine.** Every craft choice below serves one non-negotiable from `docs/narration.md`: the narrator's knowledge for a scene equals the POV character's vault for that scene. Point of view, focalization, distance, and free indirect discourse are not just style options — they are *how the knowledge boundary is rendered on the page*, and they are what turns a clean simulation into airtight dramatic irony. Get the craft right and the boundary produces the payoff ("Marcus smiled, and she took it for warmth") for free; get it wrong and the prose re-opens the omniscience leak the whole architecture exists to prevent.

**Framework-neutral and open.** Prose has no one true method. Every framework below is a peer in a well, not a rung on a ladder; where this project names a default (close third, past tense, POV-bounded) it is a **reference point, marked swappable**, not a rule. A fork replaces one reference file and inherits the rest. The canon these files digest lives in `docs/` (once); if a reference and its doc disagree, the doc wins.

## How this toolbox is organized
The deep material lives in `references/`, one file per craft-cluster, grouped by the narrator's decision-flow: perspective → distance & mind → time → surface texture. **This `SKILL.md` is the router** — it indexes what each file holds and when to pull it. Read the router to find the one file the moment needs; read that file; skip the rest. (The deep reference files are authored in a **later pass** — see `references/_index.md` for their outlines. The index below is the map they fill in.)

**A missing reference file is not a stall condition.** Entries not yet authored have no file on disk; when the router sends you to one that's missing, act on this index's own one-line summary for that entry and proceed — never stall on, or invent, the file.

---

## The index — what lives where

### A. Perspective & the knowledge boundary — who sees, who knows *(the narrator's first and defining choices)*

**`references/point-of-view.md`** — *the POV menu; load first, before any other craft choice — fixing whose knowledge bounds the scene governs everything after.*
- **First person** — the "I" narrator; intimacy and built-in subjectivity; the split between the narrating-I (telling now) and the experiencing-I (living then).
- **Second person** — the "you" narrator; rare, implicating, estranging (McInerney's *Bright Lights, Big City*; Calvino; Lorrie Moore; Butor); Fludernik's account of its address.
- **Third-person limited (close third)** — bound to one character's knowledge and perception; the project's default vault-render mode.
- **Third-person omniscient** — the all-knowing narrator, free to enter any mind and know the arc; a legitimate mode but the one `narration.md` warns *against* here, because it re-opens the leak.
- **Third-person objective (dramatic / camera-eye)** — external only, no interiority (Hemingway's "Hills Like White Elephants"); behaviorist telling.
- **Free indirect / "deep" third** — limited third fused with the character's idiom; the mode that maximizes vault-bounded irony (see `free-indirect-discourse.md`).
- **Stanzel's three narrative situations** — authorial / figural / first-person, turning on a narrator-vs-reflector axis; an alternative typology to hold beside Genette (*A Theory of Narrative*).
- **Peripheral / witness narrator** — the "I" who watches the real protagonist (Nick Carraway, Dr. Watson); knowledge bounded by a bystander's vantage.
- **Frame narrator & embedded narration** — a specific character telling the tale, still bounded by *their* knowledge (Marlow in *Heart of Darkness*).
- **Multi-POV & POV rotation** — switching the bounded viewpoint by scene or chapter to cover a story no single vault could — *change boundaries, never break one.*
- **Real-time vs retrospective (the FROM-WHEN axis)** — narrating up-to-the-moment (pure irony) vs after-the-fact (knows the arc, may foreshadow — bounded by eventual knowledge).
- **Narrative person (Genette: homo- / hetero- / autodiegetic)** — whether the narrator is a character in the story, outside it, or its protagonist.
- **Head-hopping (the failure mode)** — sliding between characters' interiors within a scene; the prose-layer omniscience leak `narration.md` forbids.

**`references/focalization-and-narratology.md`** — *the formal spine; load for the rigorous vocabulary of the knowledge boundary — who sees vs who speaks — and for handling time (order, speed, frequency).*
- **Genette's who-sees / who-speaks distinction** — focalization (mood) cleanly separated from narration (voice); the move that untangles the muddle called "point of view."
- **Zero focalization** — the narrator knows more than any character (classical omniscience); "vision from behind."
- **Internal focalization (fixed / variable / multiple)** — narration bounded to a character's knowledge; Pouillon's "vision *avec*"; the formal name for the vault-render.
- **External focalization** — the narrator knows less than the characters; behaviorist, camera-eye; "vision from without."
- **Mood: distance & perspective** — Genette's two mood-controls: how mediated the telling is, and through whom it is focalized.
- **Voice: time, level, person** — when the narrating happens (subsequent / prior / simultaneous / interpolated), the narrative level (extra- / intra- / metadiegetic), and the person.
- **Order (anachrony)** — analepsis (flashback) and prolepsis (flashforward); the retrospective narrator's foreshadowing tool.
- **Duration / speed** — pause, scene, summary, ellipsis, stretch; narrative tempo (worked in `scene-and-summary.md`).
- **Frequency** — singulative, repetitive, and iterative telling ("every Sunday she walked to the river").
- **Bal's focalizer / focalized** — the seeing-subject and the seen-object; focalization recast as a relation, extending Genette.
- **Chatman's story vs discourse** — the *what* (events, existents) vs the *how* (their expression); the base narratological split.
- **Chatman's slant & filter** — "slant" for the narrator's attitude, "filter" for the character's perception; a sharper cut than focalization for close third (*Coming to Terms*).
- **The implied author (Booth)** — the authorial persona the text projects, distinct from narrator and real author; the anchor unreliability is measured against.
- **The narratee (Prince)** — the audience the narrator addresses inside the text (Gerald Prince's *narrataire*).
- **Rimmon-Kenan's synthesis** — the standard working reconciliation of Genette and Bal (*Narrative Fiction*).
- **Käte Hamburger's epic preterite** — third-person fiction as the one discourse granting direct access to another mind; the past tense that loses its pastness (see `tense-and-time.md`).

**`references/unreliable-narration.md`** — *the gap between the telling and the truth; load when the POV misperceives, self-deceives, or lies — and to render the recorded thought≠action gap.*
- **Booth's unreliable narrator** — a narrator who departs from the implied author's norms; the coined term and its measure (*The Rhetoric of Fiction*, 1961).
- **The implied author as yardstick** — unreliability exists only relative to the norms the whole work implies; no anchor, no "un-."
- **Riggan's typology** — the pícaro (braggart), the madman, the clown (plays with truth), the naïf (child's-eye), and the liar; five recurring first-person unreliables.
- **Phelan & Martin's three axes** — unreliability along facts/events, values/ethics, and knowledge/perception.
- **Phelan's six subtypes** — mis-reporting / -reading / -regarding (getting it wrong) vs under-reporting / -reading / -regarding (saying too little).
- **Bonding vs estranging unreliability (Phelan)** — unreliability that draws the reader *closer* to the narrator vs that pushes them away.
- **Nünning's cognitive model** — unreliability as a reader's construct, resolved by dramatic irony between narrator and audience; a constructivist reframe of Booth.
- **Discordant vs fallible narration (Olson)** — the narrator who distorts by nature vs one merely mistaken or limited.
- **The naïve / innocent eye** — a child or outsider whose limited frame the reader reads *past* (Huck Finn; Stevens in *The Remains of the Day*).
- **Dramatic irony from unreliability** — the reader knowing more, or truer, than the teller; the general case of the vault-bounded misreading.
- **The deception bridge (project-specific)** — a lie is a recorded thought ≠ action; the reader gets only the action, and the lie-in-progress *only* when the liar is POV (`recording-model.md`).

### B. Distance & the rendering of mind — how close the lens sits, how a mind reaches the page

**`references/narrative-distance.md`** — *the zoom; load when tuning how near or far the prose sits from the POV's consciousness within a scene.*
- **Gardner's psychic distance** — the felt gap between reader and character; a slider from cosmic-remote to skin-close (*The Art of Fiction*).
- **The five-rung ladder** — Gardner's worked example, from "It was winter of the year 1853…" down to "Snow. Under your collar, down inside your shoes…"; each rung closes the gap.
- **Distance as a dial, not a setting** — moving in and out within a scene (wide for context, close for the emotional beat); the zoom, not a fixed lens.
- **Distance ↔ focalization & FID** — the closer the distance, the more the prose takes on the character's idiom; the approach to free indirect discourse.
- **Deep POV / "deep third"** — the contemporary close-third that drops filter words to collapse distance to near-zero.
- **Filtering / filter words** — perception verbs ("she saw," "he felt," "he noticed") that re-insert the narrator between reader and character; removing them closes distance.
- **Authorial vs figural distance** — the narrator standing apart and judging vs dissolving into the character's consciousness (ties to Stanzel).
- **The camera metaphor & its limits** — long shot / close-up as distance, but prose can do what a lens can't: enter the mind.
- **Empathy vs irony as distance-effects** — closeness invites identification; distance enables judgment and comedy — the same event, two effects.

**`references/free-indirect-discourse.md`** — *the dual voice; load to render a character's thought/speech in the narrator's third person — the engine of vault-bounded irony.*
- **Free indirect discourse (FID)** — a character's thought or speech in the narrator's third-person past, but carrying the character's idiom and deixis; the merged voice.
- **Style indirect libre / erlebte Rede** — the French and German names; the technique's continental pedigree.
- **Cohn's "narrated monologue"** — *Transparent Minds*' term for FID: figural thought in the guise of narration (see `rendering-interiority.md`).
- **The dual voice (Pascal)** — FID as two voices at once, narrator and character, neither wholly in control (*The Dual Voice*, 1977).
- **Banfield's "unspeakable sentences"** — the linguistic account: represented speech and thought as sentences with no speaker, only a *self* (1982).
- **Flaubert & Austen** — the technique's masters: *Madame Bovary*'s ironic slippage; *Emma*'s free-indirect misjudgments (the early English practitioner).
- **Leech & Short's speech/thought presentation cline** — FDS / DS / FIS / IS / NRSA for speech and FDT / DT / FIT / IT / NRTA for thought; a precise scale of narratorial control (*Style in Fiction*).
- **Free indirect thought (FIT) vs direct/indirect thought** — where FID sits on that cline, and why it is the close-third default.
- **Bakhtin's double-voiced discourse** — a single utterance carrying two intentions, author's and character's; FID as the novel's characteristic hybrid.
- **Deixis in FID** — "here," "now," "tomorrow" anchored to the *character's* moment inside past-tense narration; the grammatical tell.
- **The irony engine** — FID renders a belief *as* the prose's own, so the reader inhabits the misreading ("Marcus smiled, and she took it for warmth"); why the vault-bounded narrator's gold is FID.
- **Coloring / contagion** — narration taking on a character's vocabulary even outside quoted thought; distance shading toward the figural.

**`references/rendering-interiority.md`** — *turning recorded thought into a mind on the page; load when the POV's inner life must become prose without inventing it.*
- **Cohn's three modes (third-person)** — psycho-narration, quoted monologue, narrated monologue; the map of consciousness-rendering (*Transparent Minds*, 1978).
- **Psycho-narration** — the narrator *reports* the character's mind in their own (narratorial) words; the most distanced, most flexible mode.
- **Quoted monologue** — the character's thought quoted directly (*I can't do this,* she thought); interiority at zero remove.
- **Narrated monologue** — figural thought in free indirect style (= FID; the seam with the previous file).
- **Consonant vs dissonant narration (Cohn)** — the narrator in harmony with the character's mind vs standing above and judging it.
- **Interior monologue (direct / indirect)** — the character's mental voice given continuously; Dujardin's *Les Lauriers sont coupés* (1887), the technique Joyce credited as its origin.
- **Stream of consciousness** — the associative, pre-verbal flow (William James coined the phrase, 1890); Joyce, Woolf, Faulkner in practice.
- **Humphrey's four techniques** — direct and indirect interior monologue, omniscient description, soliloquy (a working taxonomy of the stream, 1954).
- **Soliloquy** — sustained self-address, more ordered and audience-aware than interior monologue.
- **Autonomous monologue** — unframed inner speech with no narratorial tag (Molly Bloom's close of *Ulysses*); the stream at its most radical.
- **Palmer's "fictional minds" / thought report** — the whole-mind, "social minds" approach beyond the speech-category cline (*Fictional Minds*, 2004).
- **Rendering sensation & perception** — the body and senses as interiority's ground floor (heat, nausea, the caught breath); where recorded state becomes felt prose.
- **Grounding rule (project-specific)** — interiority is the POV's *recorded* thought rendered, never confabulated at write-time (`recording-model.md`).

### C. Time — when it's told

**`references/tense-and-time.md`** — *the grammatical footing of the telling; load when choosing past vs present, or coupling tense to a real-time or retrospective POV.*
- **Past tense (the epic preterite)** — fiction's default; Hamburger's point that in fiction the preterite loses its pastness and simply *means* "story."
- **Present tense** — immediacy, restricted knowledge, a cinematic now; its contemporary rise and the fatigue/backlash it draws.
- **Historical present** — telling past events in the present for vividness; the oral-anecdote and set-piece device.
- **Future & conditional tense** — rare, prophetic or hypothetical (Butor's second-person future in *La Modification*); the road-not-taken register.
- **Tense ↔ POV coupling** — real-time narration pairs with the present or a pastness-less past; retrospection needs a past that *knows* the arc.
- **Order revisited (analepsis / prolepsis)** — flashback and flashforward as the retrospective narrator's foreshadowing (formalized in `focalization-and-narratology.md`).
- **Tense shifts as signal** — moving between tenses to mark memory, dream, or a change of temporal footing; and the risk of incoherence.
- **Duration & the "now" of narration** — whether telling-time and told-time coincide (simultaneous narration) or diverge.

### D. The texture of the prose — the sentence-level surface

**`references/voice-and-diction.md`** — *the felt personality of the telling; load when establishing or distinguishing a narrator's voice, or matching diction to a POV.*
- **Voice** — the felt personality of the prose: the sum of diction, syntax, rhythm, and stance; what makes a page unmistakably one narrator's.
- **Diction / lexical register** — high / middle / low; formal vs colloquial; the word-choice that sets a narrator's class, era, and cast of mind.
- **Latinate vs Anglo-Saxon diction** — abstract, polysyllabic, cool vs concrete, monosyllabic, blunt; the English writer's central tonal lever.
- **Concrete vs abstract language** — the named thing vs the category; the grain that makes prose felt rather than argued.
- **Tone & attitude** — the narrator's stance toward the material and the reader (ironic, elegiac, wry, clinical).
- **The three classical styles (genera dicendi)** — grand, middle, and plain; the rhetorical registers matched to matter and aim.
- **Idiolect, dialect, sociolect** — the individual, regional, and class markings of speech; how a voice signals *who* is speaking.
- **Persona & ethos** — the constructed speaker the prose projects, and the credibility it earns (rhetoric's *ethos*).
- **Bakhtin's heteroglossia** — the novel as a collision of many social voices, no single authorial monotone; the polyphonic ideal.
- **Skaz** — narration miming a spoken, vernacular teller (the Russian term; Gogol, Twain, Salinger); voice foregrounded as performance.
- **Distinct voices (the critic's check)** — each POV rendered in a separable idiom so the reader never confuses two minds (`design.md`'s continuity/critic gate — the LLM-side "distinct voice" test).
- **Word music & connotation** — the sound and freight a word carries beyond its denotation; diction as feeling, not only meaning.

**`references/show-vs-tell.md`** — *dramatize or report, at the prose grain; load when deciding whether a moment should be rendered in the senses or stated.*
- **Show vs tell** — render the experience so it lands vs state the conclusion; the craft chestnut, and its real (narrow) truth.
- **Chekhov's dictum** — "Don't tell me the moon is shining; show me the glint of light on broken glass"; the origin-quote of the maxim.
- **Lubbock's "dramatize"** — *The Craft of Fiction* (1921): the novel that *shows* so it "tells itself"; the scenic ideal, after Henry James.
- **James's scenic method** — "Dramatize, dramatize"; rendering over narrating as the Jamesian standard.
- **The reality effect (Barthes)** — the concrete, "useless" detail that signals *this is real* (*l'effet de réel*, 1968); showing as authentication.
- **The objective correlative (Eliot)** — emotion conveyed through an external object, situation, or chain of events, never asserted (1919).
- **The significant detail / synecdoche** — the one telling particular standing for the whole; selection, not accumulation.
- **"Thisness" / haecceitas (Wood)** — the irreducible concrete detail that gives fiction its lifelike density (*How Fiction Works*).
- **Filtering and the removed narrator** — cutting "she saw / he noticed" so the image lands directly (ties to `narrative-distance.md`).
- **The honest counter** — telling is not the enemy: summary, transition, and earned authorial statement are indispensable; "show don't tell" over-applied flattens prose (Gardner's and modern pushback).
- **What to show vs tell** — dramatize the load-bearing, emotionally hinged moment; tell the connective tissue (ties to `scene-and-summary.md`).

**`references/scene-and-summary.md`** — *the pace of the telling; load when deciding to stage a moment blow-by-blow or compress it, and how the two alternate.*
- **Scene vs summary** — the moment rendered blow-by-blow (scene) vs time compressed and reported (summary); the pacing pair.
- **Genette's five speeds** — pause, scene, summary, ellipsis, and stretch/slow-down; narrative duration as the ratio of story-time to text-time.
- **Scene (isochrony)** — dialogue and moment-to-moment action, where telling-time ≈ told-time; the reader's real-time.
- **Summary** — the acceleration that covers weeks in a sentence; how a narrative breathes and travels between scenes.
- **Ellipsis** — the elided gap, time skipped entirely; what a story *doesn't* narrate, and how the reader infers it.
- **Descriptive pause** — narration halts while description runs; setting and the held image.
- **Bentley's scene / summary / description** — Phyllis Bentley's practitioner triad of narrative modes and their alternation (1946).
- **Pacing & the rhythm of alternation** — the breathing pattern of scene → summary → scene; density where it matters, speed where it doesn't.
- **Enter late, leave early** — cutting a scene to its charged center; where to start and stop rendering.
- **The depth rule for prose (project link)** — dramatize the hinges, summarize the tail; the "resolve to what the book levers on" discipline at the render layer (`design.md`).
- **The unwitnessed-scene constraint** — what *can* be a scene, vs only summary, is bounded by whether a POV was present (`narration.md`).

**`references/prose-rhythm-and-cadence.md`** — *the music of the sentence; load when a passage needs to move — for punch, momentum, weight, or fall.*
- **Sentence as the unit of style** — rhythm, emphasis, and meaning built at the sentence; the working grain of prose music.
- **Loose / cumulative sentence** — the base clause first, modifiers trailing; Christensen's "generative rhetoric of the sentence."
- **Periodic sentence** — meaning suspended to the end; tension held, then released.
- **Balanced sentence** — symmetrical clauses (isocolon, antithesis); poise and contrast.
- **Parataxis vs hypotaxis** — clauses set side by side (short, blunt, Hemingway) vs subordinated and nested (long, architectural); the master syntactic dial.
- **Sentence-length variation** — the long-then-short contrast; the short sentence's punch after a long run.
- **Schemes of repetition** — anaphora, epistrophe, anadiplosis; structural repetition for emphasis and momentum.
- **Asyndeton & polysyndeton** — dropping conjunctions (speed, clipped) vs piling them ("and… and… and," biblical, accumulating).
- **Tricolon & isocolon** — the three-part and equal-membered patterns the ear expects and remembers.
- **Chiasmus & antithesis** — crossed and opposed structures; the shapeliness of reversal.
- **Sound devices** — alliteration, assonance, consonance, sibilance; euphony vs cacophony as felt texture.
- **Cadence & the fall of a sentence** — the rhythm of the close; the "dying fall" and end-weight / end-focus.
- **Punctuation as tempo** — the comma, dash, colon, and full stop as the score's rests and beats.
- **Prose rhythm (the tradition)** — Saintsbury's *A History of English Prose Rhythm* (1912); the stress-patterning below the meaning.
- **Practitioner guides** — Le Guin's *Steering the Craft*, Tufte's *Artful Sentences*, Fish's *How to Write a Sentence*, Forsyth's *The Elements of Eloquence*; the craft well for sentence music.

---

## How to use this well — the method
1. **Set the boundary first.** Before any craft choice, fix the POV and its vault: *whose* knowledge bounds this scene, and *from when*. This is not a style decision — it is the knowledge wall (`point-of-view.md`), and every choice below serves it.
2. **Route by decision.** Perspective & the knowledge boundary → files **A**. How close, and how a mind reaches the page → files **B**. When it's told → file **C**. The sentence-level surface → files **D**. Read the router, pull the one file the moment needs, skip the rest.
3. **Read the field, not one truth.** Each reference is a menu of peers; the repo's defaults (close third, past tense, POV-bounded) are reference points, marked swappable — reach for what fits *this* POV and moment.
4. **Let the boundary do the drama.** Reach for free indirect discourse and close psychic distance to make the reader *inhabit* the POV's misreading; that vault-bounded irony is the payoff to render toward, not something to write around.
5. **Render, don't invent.** Interiority is recorded thought made prose; the cut is what happened. The toolbox shapes *how* it's told, never *what* is told — facts and minds come only from the cut and the vault slice.
6. **Match voice to POV.** Give each viewpoint a distinct diction and rhythm (`voice-and-diction.md`) so two minds never sound alike — the continuity critic checks exactly this.
7. **Pace by the hinge.** Dramatize the load-bearing, emotionally charged moment; summarize the connective tissue (`show-vs-tell.md`, `scene-and-summary.md`) — the depth rule, at the prose layer. And never stage a scene no POV witnessed.

## Cross-file spine
Files **A–D** are the field of craft, arranged by the narrator's decision-flow. The **POV/vault boundary** is the spine that runs through all of them: whatever device a file offers — a focalization, a distance, a free-indirect turn, a summary — it lands in this project only as prose bounded by what the POV character knows. Read the craft file for the *how*; hold `docs/narration.md` and `docs/recording-model.md` for *why the boundary is non-negotiable*.

## Status
Router + index complete; the eleven `references/` files are outlined in `references/_index.md` and authored in a **later pass**. Until then, use the one-line entries above as pointers and reach for the named framework and its provenance directly. Nothing here is prescriptive: it is a well to draw from, framework-neutral, holding rival modes side by side so the scene — not the toolbox — decides.
