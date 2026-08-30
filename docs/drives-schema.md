# Drives schema — goals, fears, and orientation as opposable fields (Layer 3)
*The companion `decision-engine.md` flagged as "still to detail." This is the standing motivational structure the decision engine resolves: **what pulls a character toward and away, and how they engage** — `character-anatomy.md` Layer 3.*

## First, the boundary: drives are not values
The README's shorthand "goals/values/fears" is loose, and `decision-engine.md` already corrected it (§"Where the weights live", the Layer-2 note): **values are not stored as drives.** The clean split:
- **Layer 2 (Worth)** — the *shared menu* (needs / Schwartz values / Moral Foundations). Universal, not per-person.
- **Layer 10 (the Model)** — the *per-person weighting* over that menu, and the conflict resolver.
- **Layer 3 (Drives, this doc)** — the per-person **operands**: the concrete goals a person pursues, the fears/wounds they protect, and the orientation biases (locus, coping) that color how. Drives *reference* values (they instantiate them) but don't store the value weighting — that's the Model's job.

So a drive is not "she weights benevolence 0.8." A drive is "she will get her brother out of that prison" (a goal) — which *serves* benevolence + a concrete attachment, and the Model says whether it wins when it collides with her own safety. **Goals/fears are the instantiated pulls; values are the abstract menu they point at.** This supersedes "goals/values/fears" wherever it appears.

## The three families

### 1. Goals — what pulls toward
```
goal:
  id
  statement            # "get her brother out", "be ordained", "never go hungry again"
  priority:   0–1      # BASELINE pull strength (effective = ×state×situation×relationships)
  kind:       terminal | instrumental   # end-in-itself vs serves-another
  serves:     [ref...] # what it instantiates: value(s) from the menu, a concrete attachment,
                       #   self-image, and/or a parent goal (instrumental → terminal). For opposability.
  status:     active | dormant | achieved | abandoned | blocked
  origin:     ref?     # the backstory/event that set it (Layer 6) — optional
  triggers:   [cond...]# scene-features that raise its salience (the relevance-gate hook)
  view:       truth | self   # default truth; `self` = a stated goal that masks the real one
```
Goals chain: instrumental goals `serve` terminal goals, terminal goals `serve` menu values + attachments. The chain is load-bearing for opposability — sacrificing an instrumental goal to save its terminal parent is coherent; sacrificing the terminal to keep an instrumental is a crisis.

**`blocked` — transitions defined (audit B7):** the **engine** sets `blocked` when pursuit is denied by recorded outcome — a plan-step fails against world state (a ledger event), the path is rule-impossible (`world-dynamics.md` denial), or the enabling entity is lost. Effect on pull: an **instrumental** goal re-routes — its effective priority redistributes to sibling goals serving the same terminal (the `serves` chain exists for exactly this); a blocked **terminal** goal converts its pull to *pressure*, colored by orientation — internal locus + approach-coping → seek-another-way urgency (spawn a new instrumental); external locus / avoid-coping → resignation drift toward `dormant`. **Unblock:** the goal's `triggers` re-fire on relevant ledger change (the gate already watches them) → back to `active`. `blocked` is a routing state, never a terminal state by fiat.

### 2. Fears / wounds — what pulls away (the friction engine)
```
fear:
  id
  statement            # "being abandoned", "being exposed as a fraud", "losing control"
  intensity:  0–1      # BASELINE avoidance pull
  protects:   [ref...] # what worth it guards: self-image, an attachment, status, an absolute line
  avoids:     [cond...]# scene-features that trigger it (relevance-gate hook)
  wound:      ref?     # the formative injury that generated it (Layer 6 backstory) — the "ghost"
  defense:    pattern  # the protective behavior it produces: withdraw | control | attack | please | perform
  view:       truth | self   # a fear can be UNCONSCIOUS — truth-only, absent from self-image
```
A **wound** is the origin; the **fear** is the standing avoidance; the **defense** is the behavior it drives. Modeling them as one family (fear, with `wound` as provenance and `defense` as output) keeps the friction engine in one place. Fears are opposable to goals: the goal pulls toward the very thing the fear guards against — that internal collision is most of a character's drama.

### 3. Orientation — how they engage (not what they pursue)
Two dispositional biases that color the pursuit of *every* goal/fear. Layer-3, not HEXACO (Layer 1) — these are motivational stance, not behavioral style.
```
orientation:
  locus_of_control:   -1..+1   # external(−) fate/accept ↔ internal(+) act/fix     (Rotter)
  agency:              0–1     # how strongly they act on the world at all
  coping_engagement:  -1..+1   # avoid(−) ↔ approach(+)
  coping_expression:  -1..+1   # suppress(−) ↔ express(+)
```
Stored as means; a per-axis **variability** is allowed (whole-trait style — usually-internal but fatalistic under enough load) but optional. These are the `locus/coping bias` the decision engine lists as Layer-3 operands.

## Opposability — the structure that makes drama legible
"Structured opposable fields" is the core requirement. The mechanism: **every goal and fear is tagged (`serves`/`protects`) against the shared menu (Layer 2) and given a direction (toward/away).** Two drives are *opposable* when their tags pull opposite directions on the same axis, or compete for the same scarce thing (time, a person, a value, a life). The schema does **not** compute the winner — that is the Model (Layer 10), resolved narratively. The schema's job is to make the collision **legible**: tag the drives so the relevance gate can surface the colliding pair and the `{thought}` stream can name the competing pulls it's resolving.

Opposition is also **cross-layer**: a goal can collide with a *trait* (timid disposition vs *protect-the-child* goal → the out-of-character tail sample, `trait-theory.md`) or with a *value weighting* (a goal that serves achievement vs a high benevolence weight in the Model). The drives schema feeds all three by exposing what each drive serves/protects; the Model weighs across them.

## Baseline vs live — Layer 3 stores the standing pull; Layer 7 activates it
Layer 3 holds **baselines** (priority, intensity) + **triggers**. *Which* goals are currently active and *which* fears are live right now is **State (Layer 7)** — "mood + active goals + current beliefs, the time-sliced present" (`character-anatomy.md`). A goal therefore appears in both: its standing existence/priority/triggers in Layer 3; its `active` status and current heat in Layer 7. The schema here is the catalog; the state layer is the activation.

## Track numerically, resolve narratively — drives are operands, not the resolver
Per `decision-engine.md`: the stored magnitudes (priority, intensity, locus/coping) are **tracked numerically for continuity**; the **effective** pull at decision time is `baseline × state × situation × relationships`; and the resolution is the LLM weighing the *salient subset* injected as framing — **never a code-side weighted sum.** The drives schema supplies the baseline operands and the triggers that make a drive salient. It is computation the Model resolves; it does not resolve itself.

## Three views — the drive a character won't admit
Like everything (`self-and-perception.md`), a drive exists in three views. Ground-truth is the default store. A `view: self` variant is the **self-deception engine**: a fear that is real (truth) but absent from self-image (the man who calls his control "responsibility"); a stated goal that masks the real one (she says she stays for duty; truth is she fears being no one without them). Others-see is *derived*, not stored — observers infer drives from surface behavior (Layer 8), often wrongly. A truth-fear with no self-view is exactly `self-image ≠ behavior` — self-deception, the richest interior material.

## Sparse authoring + salient-subset injection
Same discipline as traits. **Author only the drives that matter** for a character — a principal might have 4–6 goals and 2–3 wounds; a walk-on has one goal and none authored. Unspecified ≠ derived-from-a-parent (unlike facets): absence simply means no salient drive there, which is correct — most people aren't driven on most axes. At decision time the engine surfaces only the *triggered* drives (the relevance gate), never the whole catalog. Fine-grain in storage, salient-subset in the prompt.

## Worked example — one collision, made legible then resolved
Maelle, baseline: goal `g1 = "get my brother out of the work-camp"` (priority 0.9; serves benevolence + attachment[brother] + self-image["I don't abandon family"]); fear `f1 = "being caught and erased like our parents"` (intensity 0.7; protects survival; wound = watched the wardens take her parents; defense = freeze/comply); orientation: locus +0.6 (acts), coping_engagement +0.3 (approaches), expression −0.5 (suppresses).

A scene puts a bribeable guard in front of her, with a patrol due in minutes.
- The **situation** (relevance gate) raises both `g1` (the lever to free her brother is *right here*) and `f1` (acting means exposure). Effective pulls, not baselines, now collide.
- They are **opposable by construction**: `g1` pulls toward the camp (serves attachment); `f1` pulls away (protects survival) — same axis, opposite sign. The schema made this legible without deciding it.
- The **Model (10)** resolves: her self-image goal ("I don't abandon family") + locus(+) tip it — she acts, but her suppression bias (expression −0.5) means the `{thought}` shows the terror she won't voice. **The schema supplied the colliding operands; the Model picked the winner; the thought stream rendered the cost.**
- Flip one weight in the Model (survival over self-image) and she freezes and hates herself — same drives, different resolver. That is the divergence dial working as designed.

## Net
The drives schema is **Layer 3**: per-person **goals** (priority, what-they-serve, chained terminal/instrumental), **fears/wounds** (intensity, what-they-protect, the wound that made them, the defense they drive), and **orientation** (locus + coping). Values live in the menu (2) and the weighting in the Model (10) — drives *reference* values, never store them. Every drive is **opposable** by menu-tagging + direction, so collisions surface for the Model to resolve narratively. Baselines live here; activation lives in State (7); resolution lives in the Model (10). **Tracked numerically, resolved narratively — drives are the operands, never the sum.**

## Cross-links
- `decision-engine.md` — the resolver this feeds (operands → effective weight → narrative resolution); §"Where the weights live" (the boundary this doc formalizes).
- `values-and-stakes.md` — the menu (Layer 2) that drives reference via `serves`/`protects`.
- `character-anatomy.md` — Layer 3 in the 10-layer whole; the baseline/state (3/7) and operand/resolver (3/10) splits.
- `trait-theory.md` — Layer 1 disposition; cross-layer opposition (a drive overriding a trait-lean = the character-defining tail).
- `self-and-perception.md` — the three views; the `view: self` self-deception case.
