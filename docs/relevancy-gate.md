# Relevancy Gate — what to inject from the vault

The vault holds everything a character knows; we never inject all of it. The Relevancy Gate decides, per scene-turn, which slice of a character's vault (+ which skills) enters the simulator's context.

## Relevance is COUNTERFACTUAL, not topical
- **Wrong:** "what's topically related to the scene" (semantic similarity / onion-peeling). Over-injects inert-but-related facts AND misses the hinge — a fact that isn't *about* the scene but decides its outcome.
- **Right (the target):** a fact is relevant iff **its presence changes the character's reaction** — info that causes a reaction that, without it, would not happen. Relevance = outcome-changing.

## Operationalize via TRIGGER-MATCHING (the computable proxy)
You can't run the sim twice per fact to test counterfactual relevance directly. The proxy: the scene emits **triggers** — stimuli being implicitly checked (a symbol shown, a name dropped, a place, a claim, a request). A vault entry is relevant if it **matches a trigger** — it's the character's answer to a check the scene is posing.
> The shopkeeper sees the old symbol (trigger) → vault contains "I know this symbol"? Match → recognition → welcomed into the society. No match → locked out. The symbol isn't topically "about" buying goods; trigger-matching catches the hinge, semantic similarity wouldn't.

Trigger-matching is **high-recall on the consequential** (won't miss the hinge) at the cost of some inert matches (cheap; pruned downstream by goal-salience + onion-peel). Missing the hinge is catastrophic; including an inert fact is not — so this trade is correct.

## Gamified frame: skills + checks (the model)
- Characters have **skills** (Lore, Insight, Streetwise, Persuasion…) with levels.
- Vault entries tagged with skill domain (old symbol → Lore/History).
- A **check** = (trigger, skill domain, difficulty). A character passes via **knowledge** (matching vault entry — binary) OR **skill** (level vs difficulty — graded).
- Two check types:
  - **Knowledge check** — binary, vault membership. You remember the symbol or you don't.
  - **Skill check** — graded. You might notice the lie (Insight) or not.

## Resolution — RESOLVED (2026-06-10): deterministic; the director's lever is STATE, never the outcome
How a check resolves: **deterministic** — stats/knowledge vs DC decide (high Lore → auto-recognize). Plot-controllable, repeatable, replayable. Randomness, if ever used, is seeded texture only (shard PRNG), never a hinge.

**The former "Director-set DC" option is removed.** The design audit (inv:director-never-forces, 2026-06-10) found it was the **only invariant violation in the 33-doc design**: a check outcome is a fact about the character's cognition — whether they recognize the sigil, notice the lie — and setting it by fiat is the director writing into a mind, which the whole architecture reserves for circumstance. The legitimate lever for the identical goal already lives in this doc (§connection energy): to make a character *miss* a connection, **deplete them** — stage the exhausting circumstance first, so the connection costs more than they have; to make them get it, give them the calm morning. To make a check *passable at all*, author the chain fainter or stronger (§worked example — difficulty emerges from authoring). Steer cognition by managing state via in-world events — the same discipline as steering everything else. *(Reversible like any decision; but reopening it means re-accepting the invariant breach knowingly.)*

## Two input domains, one machinery — recall-mode and perception-mode
The `(trigger, skill, DC)` check machinery runs in **two modes** (audit B5a — `scene-assembly.md` asserted the second; it's now defined here):
- **Recall-mode** (this doc's original domain) — source set = the **vault**. A passed check injects a belief into active recall; a failed check is absence.
- **Perception-mode** — source set = the **scene slice** (`scene-assembly.md` step 2). A passed check admits an attribute into the PerceptSet or fills `recognized_as` (identity gating, subtle cues, the concealed blade); a failed check means the detail is simply **not apprehended** — absence again, same semantics.
Same skills, same DC discipline (difficulty emerges from authoring: how subtle the cue *is*), same **energy modulation** (a drained character notices less and recalls less — one budget, two spenders), same absence-is-an-outcome rule. Nothing else in the machinery changes; only the source set differs.

## The gate pipeline (per scene-turn, for the acting character)
1. **Trigger extraction** — what is the scene presenting that could be checked? (entities, symbols, names, claims, requests, place).
2. **Vault match** — beliefs keyed to those triggers (consequential candidates).
3. **Skill match** — skills that could fire on those triggers.
4. **Goal salience** — beliefs/triggers bearing on the character's active goals (goal to find the society → the symbol is maximally relevant). Also prunes inert matches.
5. **Authored hinges** — explicit checks the director planted for this scene (PLOT-CRITICAL). Always surface + branch.
6. **Inject** — matched beliefs + applicable skills + active goals + immediate scene context. NOT the whole vault.
7. **Resolve checks** — pass/fail per the resolution rule; result conditions available reactions and (for hinges) branches the plot.

## Relevant ABSENCE is also relevant
The gate branches on HAVE vs HAVEN'T. The shopkeeper *not* remembering is as consequential as remembering — fail → locked out. For hinge checks the gate evaluates have/haven't and branches both ways; absence is an outcome, not a null.

## Frame-problem resolution
You can't pre-enumerate every relevant fact — you don't need to. **Pre-mark the hinges** (the checks that branch the plot; the director plants these deliberately — this is what plotting *is*). Emergent trigger-matching handles the long tail (texture). Authored hinges + emergent retrieval = coverage without omniscient pre-authoring.

## Composition with scale
**Trigger-matching = primary selector** (precision — surface the consequential). **Onion-peeling = fallback** (if the matched set still blows the token budget, drop lowest-priority). Filter first, trim second.

## Storage requirement
Trigger-matching needs the vault **indexed by entity / symbol / skill-domain** — a knowledge graph. Scribe's KùzuDB (facts keyed to entities) is exactly this; reuse it.

## Hard parts (honest)
- **Trigger extraction is fuzzy** — explicit triggers (a symbol shown) are easy; implicit ones (a dialect phrase that only matters if you know the dialect) are hard. Authored hinges cover plot-critical; emergent extraction is imperfect.
- **The proxy can miss/over-include** — trigger-matching ≈ counterfactual relevance but isn't identical. Hinges catch the plot-critical misses; the rest is acceptable noise.
- **Resolution fork** unresolved (above).

## Backlinks / graph distance — use as cost + difficulty, NEVER as a cutoff
The vault is an Obsidian graph (notes + `[[links]]` + backlinks). Tempting to gate by hop-count ("> X hops = irrelevant"). **Don't — it would prune the hinges.**

**Why a hop-cutoff fails:** counterfactual relevance does NOT decay with hops. The shopkeeper's symbol-memory is decisive *precisely because* it's a faint, many-hops-away connection (symbol → seen-on-a-crate → smugglers → the society). A 1-hop link is often inert (shopkeeper → "bread"); a 5-hop chain is sometimes the whole plot. **Hops measure ASSOCIATION/proximity; relevance is CONSEQUENCE — not the same.** A hard hop-cutoff re-introduces the topical-relevance error we rejected and kills the surprising-but-decisive link.

**Use the graph this way instead:**
1. **Candidate-generation, not cutoff.** Expand from the scene's *trigger* nodes outward to gather a connected subgraph as CANDIDATES; the gate (trigger-match, goal-salience, hinges) then FILTERS. Graph proposes; gate disposes.
2. **Weighted hops, not counted hops.** Weight each edge by tie strength (recency, frequency-of-thought, emotional charge). Traverse by accumulated weight = *cognitive* distance (how readily it comes to mind), not topological distance. A faint 1-hop can be "farther" than a strong 3-hop chain.
3. **Pathfinding from triggers to goals/hinges — length is a cost, not a gate.** Query: "is there a (weighted) PATH from a scene-trigger to something the character knows that bears on a goal/hinge?" If the path exists, it's relevant regardless of length. The symbol→society chain surfaces by targeted pathfinding to the marked hinge, however many hops.
4. **Distance → check DIFFICULTY (unifies with the gamified gate).** Near/strong knowledge = easy/automatic recall (trivial check). Far/faint knowledge = a HARD recall check — only a character with that obscure chain passes. So hop-distance/path-strength *sets the DC of the knowledge check*; it does not decide relevance. The shopkeeper recognizing the symbol across a faint 4-hop memory = passing a hard Lore check → welcomed. That IS "the difference between welcomed or not."
5. **Degree-aware traversal.** Penalize/curtail paths THROUGH hub nodes (the king, the capital — linked by everything). A connection that only routes via a hub is spurious; everything is ~2 hops from a hub, so uniform expansion explodes there. Down-weight high-degree nodes (PageRank / TF-IDF intuition).

**So: no fixed X-hop cutoff.** A soft *decay prior* (nearer = more likely to surface, cheaper to recall) is fine; a hard cutoff is not; and hinge-pathfinding overrides distance entirely for marked-consequential targets.

**Cost:** needs edge weights (tie strength) — MVP can start unweighted + degree-penalty and add weights later; path-strength scoring is a heuristic to calibrate, not guess.

## Worked example — "how many hops?" (the shopkeeper sigil)
No fixed number; the count is per-vault and equals the recognition *difficulty*.

Trigger: the visitor shows the **Coiled Serpent sigil**. Shopkeeper's vault path to the consequence:
```
Coiled Serpent sigil
  └─(weak: "saw it burned on crates ~15 yrs ago")→ the harbor crates
      └─(moderate: "those were Maren's smuggling runs")→ Maren the dockmaster
          └─(weak: "Maren let slip she answered to the Veil")→ the Veil   [hinge: society; rule = bearer is kin → admit]
```
= 3 hops, mostly weak edges → a HARD recall check (dormant; needs the sigil present to fire, maybe a Lore check).

Same trigger, different vaults:
| Character | Path | Hops | Check |
|---|---|---|---|
| Veil initiate | sigil = the Veil's mark (direct) | 0–1 | automatic |
| Shopkeeper | sigil → crates → Maren → Veil (weak) | 3 | hard |
| Farmer | sigil is an orphan; no edge | none (∞) | auto-fail |

Two consequences:
- **The number EMERGES from authoring, it isn't set.** We authored the shopkeeper's smuggler-adjacent past + Maren + the Veil's sigil-use; "3 hops" fell out. The director tunes difficulty by how faint a chain they author, not by picking a number — which is why a passed check feels *earned*, not arbitrary.
- **The count tells the GATE how deep to pull.** Pathfinding sigil → the-Veil(hinge) must inject the *whole 3-hop chain* into the shopkeeper's context, or the simulator can't traverse it — the connection becomes impossible even though the knowledge exists. Gate depth = path length to the hinge, per character; never a fixed N. (Deeper reason a flat hop-cutoff fails: it doesn't just mis-rank — it severs the chain the character needs.)

## Connection energy — traversal as a resource (ADDITIVE; extends the above, replaces nothing)
Links aren't free. Traversing a link = making a mental connection = effort, with a cost. Add a cost/budget economy on top of the distance/difficulty model.

**Edge cost = edge faintness** (the inverse of tie-strength from "weighted hops"). A strong, well-worn link (Mira→mother) costs ~nothing; a faint one ("Maren let slip once") costs a lot. Path cost = Σ edge costs — so the 3-hop faint sigil chain is *expensive*, which is exactly what made it a hard check.

**Each character has ENERGY — a stat AND a state:**
- *Stat (capacity):* Wits / Focus = max energy & efficiency. A sharp mind traverses farther per unit energy — this **is** their skill at making connections.
- *State (current):* depletes with fatigue, stress, emotional load; regenerates with rest. Couple it to Scribe's A11 psych model — hyperarousal / collapse (high allostatic load) → low cognitive energy; optimal zone → full. Energy isn't bolted on; it's read off the existing arousal/allostatic state.

**The unified check:** a connection fires iff **path exists (knowledge) AND path-cost ≤ available energy.** Distance set the *cost* (the DC); energy is the *budget* (capacity). Same check, two sides — difficulty vs capacity.

**What it buys:**
- **Stateful cognition.** Same character, same knowledge, *different outcome by moment* — the shopkeeper places the sigil on a sharp morning, misses it exhausted at close of day. The static graph can't model that; energy does.
- **Stress narrows cognition — emergently.** Low energy → only strong/short (cheap) links fire → the character falls back on the obvious/habitual and misses the faint, clever connection (it costs more). High energy → can afford the deep insight. Psychologically true, and it falls out of the economy for free.
- **In-fiction budget for the gate.** The gate already needed a depth bound (token budget / onion-peel — an out-of-fiction hack). Energy *is* that bound with diegetic meaning: explore from triggers by ascending cost / descending salience until energy runs out. The context-window limit and "how much can be held in mind at once" become the same thing.
- **A new director lever.** To make a character *miss* a connection they could make (plot wants them not to recognize the sigil *yet*), the director doesn't delete the knowledge — they **deplete** the character (stage a stressful/exhausting circumstance first) so the connection costs more than they have. To make them get it, give them a calm, focused moment. Steer cognition by managing state via in-world events — same discipline as steering by circumstance.

**Guardrails:**
- **Backstage only (planning-mode).** Energy decides whether a connection fires; the PROSE never says "spent 3 focus." It surfaces only as effect: "she was too spent to place where she'd seen it."
- **Calibrate, don't guess.** Costs/budgets are heuristics tuned by testing, not picked a priori.
- **MVP vs rich.** MVP: per-scene energy, cost = edge faintness. Rich: a depleting/regenerating pool across scenes (models mental fatigue; enables "too drained to see it" beats) — adds state to track.
