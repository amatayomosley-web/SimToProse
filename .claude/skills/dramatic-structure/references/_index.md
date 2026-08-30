# References — the deep files (outline / manifest)

The `dramatic-structure` toolbox's deep material. **`SKILL.md` is the router** (the index + when-to-load pointers); these files are the *well* — one per framework-cluster, each read in isolation when the router points to it. **Status: outlined, not yet authored** — this file is the manifest for the later authoring pass. Until then the `SKILL.md` index plus the `docs/` canon each file digests is the working map.

## The format every reference file will follow
Per `docs/agent-toolboxes.md`, each `references/<topic>.md` is an **operational digest** — the "how, right now," not a re-derivation of the design — on this shape:

```
# <Topic> — <the one question this file answers>
**When to load:** <the trigger in the director's work that pulls this file>
**Canon:** docs/<source>.md <the design doc(s) this digests; the source of truth>

## The menu (framework-neutral)   — several frameworks as peers; each: what it's good for, where it breaks
## Repo default → <named>          — this project's default, flagged a REFERENCE POINT, swappable
## In practice                     — 1–3 vivid, concrete examples (the load-bearing part), on real fixtures
## Limits                          — honest edges: what it can't decide, where it double-counts, when to escalate
```

Rules: **canon lives in `docs/`, once** (digest, don't fork the source of truth — if a reference and its doc disagree, the doc wins); **plural by default** (menu before any default); **examples over definitions**; **cite real sources, invent nothing** (a fabricated framework or attribution poisons every agent that draws on it).

---

## A. The macro skeleton — planning the whole story

### `story-structures.md` — which whole-story shape to lay a beat onto
- **When to load:** placing a beat in the arc of the book, choosing a spine, or checking where in the shape a scene sits.
- **Canon:** `docs/design.md` (destination-fixed / route-discovered; hold major beats + ending), `docs/acceptance-criteria.md` (dramatic shape: setups pay off, tension escalates to a climax, reads as "a story").
- **Holds:** three-act (Field) · Freytag's pyramid · Fichtean curve · Hero's Journey (Campbell / Vogler 12) · Story Circle (Harmon 8) · Save the Cat! 15 beats (Snyder) · seven-point (Wells) · kishōtenketsu (four-act, contrast-driven) · Story Grid five commandments (Coyne) · the sequence approach (Daniel / Gulino) · Truby's 22 steps · Hauge's six stages · Watts' eight-point arc · in medias res (Horace) · Yorke's *Into the Woods* · plot & situation taxonomies (Booker's 7 basic plots, Polti's 36 situations, Tobias's 20 master plots, Propp's morphology).
- **Repo default (swappable):** none prescribed — the project holds beats + ending firm and discovers the route, so a skeleton is a *diagnostic overlay* (does this shape earn its climax?), not a template to fill. Save the Cat / Story Grid are the most beat-granular overlays to reach for first.

### `classical-poetics.md` — first principles: plot, reversal, recognition, and the earned resolution
- **When to load:** reasoning about why a turn lands, whether a resolution is earned, or the deep grammar of tragedy/recognition.
- **Canon:** `docs/design.md` (the anti-forcing stance), `docs/acceptance-criteria.md` (the climax must be load-bearing).
- **Holds:** Aristotle's six elements (mythos/ethos/dianoia/lexis/melos/opsis) · mythos & unity of action · peripeteia · anagnorisis · hamartia · catharsis · desis/lysis · **against the *deus ex machina*** · complex vs simple plot · Horace's *Ars Poetica* · the three unities · Hegel's tragic collision · Nietzsche's Apollonian/Dionysian · the well-made play (Scribe/Sardou, the *scène à faire*) · Brechtian anti-catharsis (the counter-tradition).
- **Repo default (swappable):** Aristotle's causal-necessity + anti-*deus-ex-machina* is the project's touchstone — a resolution must arise from the plot's own logic — because it *is* circumstance-not-force stated in classical terms.

### `character-arc.md` — the through-line: durable change as story
- **When to load:** planning the arc, tying a beat to transformation, or deciding what a character must come to believe.
- **Canon:** `docs/arc-engine.md` (durable baseline diffs; resilience forks damage vs growth), `docs/character-model.md` (roadmap #3), `docs/values-and-stakes.md` (the reshape-target menu).
- **Holds:** positive change arc (Weiland: Ghost/Wound → Lie → Want vs Need → truth) · flat/testing arc · negative arcs (disillusionment, fall, corruption) · want vs need · the Lie/Ghost/Wound · the moral argument / self-revelation (Truby) · identity → essence (Hauge) · the engine tie (trauma debuff / eudaimonic buff, resilience fork).
- **Repo default (swappable):** the arc is *placed, not authored* — the director steers circumstance to the trauma/growth events; the engine's appraisal and the character's resilience decide the sign. The craft frameworks name the *targets*; `arc-engine.md` owns the mechanism.

## B. The engine of drama — what makes it move

### `conflict-and-escalation.md` — force pushing back, and the stakes climbing
- **When to load:** a scene needs opposition, the stakes need to rise, or a try/fail sequence needs building.
- **Canon:** `docs/values-and-stakes.md` (conflict = the menu's built-in tensions), `docs/design.md` (the world pushes back — consequence closes the loop), `docs/world-model.md` (consequence as the world's second output).
- **Holds:** conflict taxonomy (person vs person/self/society/nature/fate/supernatural/technology) · inner vs outer · McKee's three levels (inner/personal/extra-personal) · the gap (expectation vs result) · progressive complications (Story Grid) · try/fail cycles (yes-but/no-and) · "but/therefore" (Parker–Stone) & the Pixar spine · turn the screw (James) · the crucible / the lock · the antagonist principle (McKee) · the dilemma (bridge to circumstance-not-force) · escalation shape (intensify, don't repeat).
- **Repo default (swappable):** the **dilemma** is the project's workhorse — a forced trade-off between two menu-weighted stakes is exactly how a hard move becomes the character's own choice. Escalation is drawn from world consequence, not invented pressure.

### `tension-suspense-irony.md` — holding the reader forward
- **When to load:** a scene needs pull, dread, curiosity, or the ache of the reader knowing more than the character.
- **Canon:** `docs/self-and-perception.md` & `docs/knowledge-model.md` (who knows what — the source of dramatic irony), `docs/narration.md` (POV-bounded knowledge; the reader's gap).
- **Holds:** Sternberg's three universals (suspense/prospection, curiosity/retrospection, surprise/recognition) · suspense vs surprise (Hitchcock's bomb) · the information-gap (Loewenstein) · dramatic irony (Oedipus) + the three ironies · hope vs fear (McKee) · the ticking clock / time-lock · the MacGuffin · the dramatic question · narrative drive.
- **Repo default (swappable):** **dramatic irony is native to the architecture** — per-character knowledge vaults mean the sim *already* produces gaps between what a character knows and what the reader (or another character) knows; the director exploits the vaults, it doesn't manufacture irony. Sternberg's three-way split is the grounding vocabulary.

### `stakes-and-motivation.md` — why anyone acts, and why we care
- **When to load:** finding what a lever can pit against a standing goal, or checking the reader wants the goal met.
- **Canon:** `docs/values-and-stakes.md` (the menu of worth; the model = a weighting over it), `docs/drives-schema.md` (goals/fears/orientation), `docs/decision-engine.md` (which stake wins).
- **Holds:** the object of desire / desire line (McKee) · want vs need · GMC (Dixon) · stakes tiers (public/private/internal, Save the Cat) · raising the stakes · the values menu (needs / Schwartz / moral foundations / concrete stakes) · the controlling idea / story question (McKee) · sympathy & the center of good · positive/negative charge.
- **Repo default (swappable):** the **`values-and-stakes.md` menu** is the canonical stake-vocabulary — a lever works by setting a stake the character weights *more* against their current course. The craft frameworks are the work-time face of that menu; the doc is the source of truth.

## C. The working grain — one scene, one exchange

### `scene-craft.md` — building and diagnosing a single scene
- **When to load:** constructing one scene, or diagnosing why a scene is inert (nothing turns).
- **Canon:** `docs/scene-assembly.md` (how world-state becomes the situation a character acts from), `docs/recording-model.md` (the thought/action turn), `docs/consolidation-loop.md` (the beat → structured events).
- **Holds:** scene & sequel (Swain: goal/conflict/disaster · reaction/dilemma/decision; Bickham) · the MRU (motivation-reaction unit) · proactive vs reactive (Ingermanson) · the scene turn / value shift (Story Grid, McKee) · beats & "actioning" · the turning point · French scenes · enter late, leave early.
- **Repo default (swappable):** the **value-turn** is the project's scene test — a scene earns its place only if a value moves; a scene where nothing turns is a candidate for the cut, not the book. Note the seam: the director frames the *situation* (the scene's goal + circumstance); the *disaster/turn* is what the sim + engine produce, not what the director writes.

### `setups-and-payoffs.md` — planting and reincorporation
- **When to load:** wiring an early plant to a later payoff, or auditing whether a payoff was earned.
- **Canon:** `docs/acceptance-criteria.md` (every planted setup pays off), `docs/design.md` (destination fixed — a payoff is a beat held firm while the route to it is discovered).
- **Holds:** Chekhov's gun · setup/payoff (plant/reveal, the "pipe") · foreshadowing · reincorporation (Johnstone) · promise/progress/payoff (Sanderson) · the MICE quotient (Card; nested threads close in reverse order) · the reversal/recognition payoff (→ anagnorisis) · red herrings & misdirection · the rule of three · genre promises / obligatory scenes (Story Grid).
- **Repo default (swappable):** because the book is a **cut of recorded biographies**, a setup is a circumstance *placed* early whose payoff the director steers toward later — plant in the sim, pay off in the sim; the cut then selects both. A payoff invented at narration time would violate faithfulness-by-construction.

## D. The house method — the project's distinctive craft

### `circumstance-not-force.md` — moving a person without pushing them (THE load-bearing file)
- **When to load:** **every steering decision** — whenever choosing or judging a lever.
- **Canon:** `docs/design.md` (load-bearing constraints: beat-blind sim, steering = circumstance, refusal → revise the beat, destination-fixed/route-discovered), `README.md` (directors-not-authors), `docs/probe-plan.md` (the make-or-break test, the negative control, the intent-completion caveat), `docs/world-model.md` (the slice with teeth that can deny a lever).
- **Holds:** the core move (change the world, not the character) · character revealed under pressure (McKee) · the dilemma as engine · the inciting incident (McKee) · the lock / crucible · anti-*deus-ex-machina* (Aristotle) · the world must be able to say no · beat-blindness · faithful refusal as integrity check · the negative control · destination-fixed/route-discovered + adaptive replanning · the intent-completion caveat (genre-completion can fake a hit).
- **Repo default (swappable in framing, not in principle):** this *is* the project's thesis, not a swappable default — circumstance-not-force is the non-negotiable. What a fork may swap is the *craft framing* (which pressure-devices to reach for); the discipline itself (never force; a refusal revises the beat) is load-bearing and stated in `docs/design.md`.

---

## Cross-file spine
Files A–C are the field of craft (structures, drama-engine, scene-grain). File D is the **spine that runs through all of them**: whatever device an A–C file offers, it lands in this project only as a *circumstance the character chooses*. Read the craft file for the *what*; read `circumstance-not-force.md` for *how it becomes the character's own move* without the seam showing.
