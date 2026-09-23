# Emotion paths — what a path is, and what makes one coherent

> *Vocabulary note, 2026-09-10: this is a dated record written in the primitive-era vocabulary (FEAR / RAGE / CARE / PANIC_GRIEF…, `PRIMARIES`, the six-axis genotype, per-beat `_DECAY_RATE`). The live design is `emotion-paths.md`, `heritable.py` (three cells per path) and `clock.py` (minutes). Kept as the record of what was measured; `tests/test_retired_vocabulary.py` exempts it on that ground.*

**Status: DESIGN, v3, 2026-09-05. This document owns the FORM of an emotion path and nothing else.**
**WHICH paths exist — the nine, their axes and their rungs — is `docs/emotion-paths.md` (2026-09-06).**
Rates, decay numbers, the accumulation arithmetic and the prompt wording are all deliberately
absent — see §6, and do not build them from this document.

Two earlier drafts are kept in `staging/docs/`: v1 (absolute coordinates) and v2 (rest-relative).
Both were written under the compound architecture and both are superseded. §7 records what they got
wrong, because the errors are instructive and cheaper to keep than to re-derive.

---

## 0. What changed

**The old architecture: emotions were MIXTURES.** Eight irreducible primitives, and every other
emotion was a recipe over them — contempt is RAGE and DISGUST in proportion; `src/engine/compounds.py`
holds forty-one of them and names a state by cosine similarity to the nearest recipe. The admission
test for a new primitive was IRREDUCIBILITY: can it be built from the others? If yes, it is a
compound; if no, it joins the basis.

**The new architecture: emotions are PATHS.** One axis per emotion, running from its first step to
1.0, and the NAME CHANGES AT BANDS as a character walks up it. `annoyance → anger → fury → rage` is
one path with four named regions, not four mixtures. A character holds a position on every path at
once, and events are increments applied to those positions.

**So the admission test changes, and this is the load-bearing consequence.** Irreducibility is a
question about a compositional basis, and there is no longer a compositional basis. The test is now:

> **Is there a coherent walk from the first step to the full thing?**

This is far more permissive, deliberately. Shame failed the old test — it decomposes into
self-directed disgust plus grief, so it was filed as a compound. As a *walk* it is obvious and
clean: sheepish → embarrassed → mortified → humiliated → shame. It is a path.

Paths do not need to be orthogonal to each other. Shame overlapping with disgust is fine; they are
different walks and a character can be on both at once. Orthogonality was a requirement of a basis
you decompose into, and nothing decomposes any more.

**`docs/emotion-basis.md` is now wrong on its central test** and needs rewriting. It argues the
whole eight from irreducibility — *"Contempt can be built — anger and disgust, in proportion. Fear
cannot be built from anything. That asymmetry is the whole test, and it is the only test."* That
sentence was correct for the architecture it was written under and is not correct for this one.

---

## 1. The requirement, stated exactly

> **Every emotion is a path. A path maps the closed interval `[0.01, 1.0]` onto named states, with
> no gaps and no overlaps. `0.0` means the emotion is ABSENT — off the path entirely. Every value in
> `[0.01, 1.0]` resolves to exactly one rung on that path.**

### The target resolution is 0.05, and paths that cannot fill it get wider rungs

**Aim for twenty rungs — boundaries on the 0.05 grid.** A path that genuinely distinguishes twenty
stages gets twenty; a path that distinguishes eight has eight, and its rungs are simply wider. The
grid is the TARGET, never a quota: an invented distinction is worse than a coarse one, because the
engine will emit a change the character did not undergo.

```
rungs are half-open intervals on the 0.05 grid:
    rung 1  = (0.00, 0.05]        <- 0.01 lands here; this is the first step
    rung 2  = (0.05, 0.10]
    ...
    rung 20 = (0.95, 1.00]
a coarser path merges adjacent slots: (0.00, 0.15] is one rung, not three.
```

Boundaries fall ON the grid whether a path uses all twenty or eight, so every path's rungs stay
comparable and the tiling check in §3(c) is arithmetic.

**CORRECTION, 2026-09-05: the twenty bands are not merely decided — THEY ARE WRITTEN.**
`docs/phrases-rage.md` and seven sibling files (`phrases-care`, `-disgust`, `-fear`, `-lust`,
`-panic-grief`, `-play`, `-seeking`) hold **280 authored bands** on the 0.05 grid — twenty per
primitive per role variant, complete. `phrases-rage.md` states the variable as *"how much of your
response to a wrong is still under your own supervision"*, forbids any band encoding volume
("MEASURED: at the top of this scale sound is subtracted, not added"), and notes that 0.95 is a
change in kind because "the scale is supervision, and at the top there is no supervisor."

The paragraph below was written earlier today and is WRONG. It searched for the DECISION RECORD,
found it absent from `connection-model.md`, and concluded the artifact did not exist — without ever
checking for the artifact. The decision record is genuinely missing; the phrases are genuinely
present. Kept as written because the error is the instructive part: a missing citation was read as a
missing product.

**The claim below is superseded and false:** `emotion-scales.md:27` says
*"the twenty prompt bands (`docs/connection-model.md` records the 0.05 quantisation decision)"* and
`:350` says *"The 0.05 quantisation and its hysteresis are decided; the phrases are"* unwritten.
**Checked 2026-09-05: `docs/connection-model.md` contains no `0.05`, no quantisation, and no twenty
bands.** Its one hysteresis section (`connection-model.md:144`) governs the connection floor —
whether a concept BINDS — which is a different mechanism. `tests/test_citations.py` passes on the
reference because it resolves the file, and its own docstring says it is "mechanical only; this
suite cannot read intent". So the decision is being made here for the first time.

### Hysteresis, which twenty rungs makes mandatory

At 0.05 granularity a value resting near a boundary renames itself every beat, and the actor is told
the character changed state when nothing happened. `connection-model.md:144-148` already states the
rule in its own domain and the form carries over exactly:

> *"Bind high, unbind lower. A concept sitting exactly on the threshold would otherwise flicker
> between scenes and jitter every number in the run."*

For rungs: **climb high, drop lower.** A character enters rung N+1 on crossing its boundary, and
does not leave it until falling below that boundary by a margin. The margin's SIZE is a number and
therefore belongs to the later pass; that hysteresis is required at all is a property of the twenty
rungs and belongs here.

Four further things follow, and all four are consequences rather than separate decisions.

**The first rung starts at 0.01.** There is no unnamed region at the bottom of a path. Absence is
not a band — it is the single point `0.0`. This RETIRES `emotion-scales.md`'s first table row,
`*(below)* 0.00-0.25, it does not register as a wrong`, as a path concept: a character at RAGE 0.10
is on the rage path, at its faintest, and must have a name.

**Coverage is total and mechanically checkable.** The rungs must TILE the interval: the first
begins at 0.01, the last ends at 1.0, each begins where the previous ends. A gap is a value the
engine can hold and cannot name; an overlap is a value with two answers.

**Total coverage is not total surfacing, and conflating them would ruin the prompt.** Decay relaxes
toward the character's resting position, which is above zero on most paths, so a character is
almost always somewhere on almost every path. Naming all thirteen every beat would drown the actor.
So: **every value has a name; only some names are said out loud.** `direction.py` already draws
that line — it gates on band and on deviation from the character's own mean before emitting
(the notability gate, RETIRED 2026-09-08 with the clause renderer) — and the question it answered now belongs to the composer's selection. This document owns the naming; the
gate owns the saying.

**`0.0` must stay reachable, or absence is unreachable.** A path whose character can never return to
zero has no off state. This is a real open question rather than a settled one, because decay
converges on the temperament mean and not on zero — noted here, and it belongs to the later pass.

> **BOTH DECAY TABLES, NAMED (2026-09-19, gate `attitude-staircase` — a later note on this dated
> page).** There are two of them now, one shape between them. The MOOD's is `state._HALF_LIFE`: two
> anchors per path, `state._rung_half_life` deriving one half-life per RUNG, `state.decay_over`
> stepping a value down the ladder toward the temperament mean. The ATTITUDE's — what one specific
> person has earned — is `toward._attitude_half_life`: the SAME staircase at a slower per-path
> scale, whose bottom rung is the old per-day `toward._RETENTION` converted to minutes, stepping
> toward ZERO. So the question above is answered for one tier and still open for the other: what a
> person has earned does return to zero (it is a signed delta over the mood, and its rest is the
> authored character), while the mood still converges on the mean. Both read the one declaration in
> minutes. The arithmetic is `docs/emotion-arithmetic.md` §4; this page still owns the naming.

---

## 2. What a path is

A path is one emotion, as a walk. It has:

| part | what it is |
|---|---|
| **the name** | what the emotion is, as a path — RAGE, not "anger" (which is one band of it) |
| **the first step** | the faintest form that is still this emotion. Below it the emotion is ABSENT, not calm — absence is off the path, it is not the bottom of it |
| **the rungs** | the points where the FEELING changes, in order — one canonical name each, and its own authored prompt saying what is true inside the character there |
| **the top** | the word at 1.0, which is a change in kind rather than one more degree |
| **the descent vocabulary** | the words for coming down, which are NOT the climb words in reverse |
| **what raises it** | the appraisal dimension(s) that push a character up this path |
| **what lowers it** | the appraisal dimension(s) that push a character down it |

### Every rung gets its own prompt, and that is what a rung IS

The design endpoint, and it decides the rest of this document: **each rung carries its own authored
prompt.** Annoyance and anger are told to the actor in genuinely different words, so the actor knows
how the character feels in this moment rather than being handed one phrase stretched over a third of
the scale.

**This gives the rung boundary an operational test, and it is the cheapest one available:**

> **Two adjacent values are the same rung if you would write them the same prompt.**

If no genuinely different stage direction can be authored for 0.45 and 0.50, they are one rung.
Finding the rungs and writing the prompts therefore stop being two phases — they are one operation,
and it checks itself. A rung nobody can write a distinct prompt for does not exist, whatever the
word list suggests.

**The prompt is FELT STATE, never behaviour.** `emotion-scales.md:350-353` states this and states
why: *"They must be authored as FELT STATE, never as behaviour — all 32 current phrases in
`direction._PHRASES` are behavioural, which makes the engine decide what the character does and
leaves the actor nothing to act."* Verified 2026-09-05 — every one of the 32 is an action:

```
RAGE band 2: "you name the offence out loud and refuse to let it pass"
FEAR band 2: "you give ground, you hedge, you commit to nothing you cannot leave"
CARE band 3: "you put yourself between them and it"
```

Those are performances. The engine has decided what the character does, and the actor has nothing
left to decide. The felt-state form of the same rung says what is true INSIDE the character — the
wrong is the only thing in the room and will not go quiet — and lets the actor choose whether that
comes out as a raised voice, a silence, or walking away. That choice is the entire reason there is
an actor.

### The prompt's form, and the reference specimen

**Authored by the owner, 2026-09-05. This is the shape every rung on every path takes.**

```
[State: Anger]
A violent, pressurized heat spikes from the core. An intolerable boundary has been breached,
triggering an absolute refusal to accept what just happened. The entire perceptual field
collapses onto the source of the rupture—demanding an immediate, forceful pushback to restore
control.

Internal Keys for the Actor:
  The Sensation: A contained thermal surge. Blood pressure spikes instantly, creating a
    pressurized heat behind the eyes and in the chest. It feels like an internal vessel being
    pushed past its structural capacity.
  The Belief: Absolute, uncompromising refusal. A total collapse of tolerance or willingness to
    negotiate. The internal monologue is stripped down to a visceral, non-negotiable:
    "No. This does not get to stand."
  The Impulse: An intolerable kinetic buildup. Staying passive feels physically agonizing; the
    internal state is a pressurized force looking for any crack, seam, or vector through which
    to push back against the intrusion.
```

So the form is a header naming the rung, an opening that gives the state whole — the body and what
happens to attention — and then three named keys.

**`The Impulse` is the load-bearing part, and it is where the current engine goes wrong.** It names
the PRESSURE and refuses to spend it: *a pressurized force looking for any crack, seam, or vector*.
It does not say what the character does. Compare what `direction._PHRASES` ships for the same region
today — *"you square up and end it now, whatever it costs"* — which has already chosen the act. The
specimen holds the urge unresolved, so the actor decides whether it surfaces as a raised voice, a
silence, or walking out. That decision is the entire reason there is an actor.

**The three keys are also three axes to order rungs on**, which is far more tractable than asking
whether one word is stronger than another. Annoyance and anger differ in all three: the sensation (a
prickle at the jaw against a thermal surge), the belief (*this is tiresome* against *this does not
get to stand*), the impulse (wanting to be elsewhere against kinetic buildup). If you cannot write
three genuinely different keys for two adjacent values, they are one rung.

### The rung prompt is a BASELINE, and it carries no target

**The owner's design, 2026-09-05:** the showrunner builds the actor's prompt; within it are the
targets for the emotions and what is happening; and the emotion prompts give the actor *"a baseline
to use to express the built scene."*

So the rung prompt is a **reusable component, not a finished instruction**, and this settles a
question the specimen leaves open. `[State: Anger]` has no slot saying who the anger is aimed at —
and it should not have one. The baseline is generic by design: one artifact per (path, rung),
authored once, correct for every character in every scene. Binding it to a target would mean one
block per target, which is unbounded. **The target is attached at assembly, not at authoring.**

Three layers, and the seam between them is the whole point:

| layer | supplies | changes per beat? |
|---|---|---|
| **the engine** | which paths are live, the rung each sits at, what each is bound to, direction of travel | yes — computed |
| **the baseline library** | per (path, rung): the felt-state block. Target-free, character-free, scene-free | no — authored once |
| **the assembler** | the live baselines + their targets + what is happening + the scene | yes — composed |

The actor then reads *this is what anger at this height feels like*, plus *it is aimed at Emmet*,
plus *here is what Emmet just did* — and expresses the scene against that baseline. The baseline is
the floor it plays from, never the performance itself.

**Where the library must live, and why it is not a free choice.** Assembly happens today in
`src/engine/prompt.py:27` (`build_turn_messages`), and the showrunner CONSUMES the result rather than
composing it — `docs/orchestration.md:87-93` wires it through `--prompt-only`. So there are two
drivers over one assembler. If the baseline text lived in the agent layer, the two modes could drift
apart, and `CLAUDE.md` is explicit that `.claude/skills/` holds craft and *"never facts; facts reach
an agent only through the engine-computed packet."* Which rung a character is on is a fact.

**Therefore: the baselines belong in the engine, as a generated module**, the same split the code
registry already uses — authored as data, generated into Python, read by the one assembler, emitted
identically to both drivers. That also keeps the numbers out of the prompt by construction (hard
rule 5): the engine resolves value to rung and emits only the rung's prose.

### Why the courier rule exists: POV isolation

The owner's reasoning, 2026-09-05: *"The logic is hygiene, the showrunner will handle many scenes and
prompts. If it was to translate emotions it can easily leak into the composed prompt. The more
deterministic we can make the actors briefs the better the actor can portray the character in a
vacuum which is how most people experience the world. So the actor should only ever have their pov."*

**The aesthetic argument is the smaller half; hygiene is the load-bearing one.** The showrunner knows
the whole book — every scene, every character's interior, what is coming. Once it is authoring prose
about how someone feels, nothing structurally separates that from authoring prose about what someone
knows. The pen that can write *"furious but still loves his brother"* can as easily write *"furious,
though he doesn't yet know Emmet was coerced."* Same pen, same omniscience, and the second one hands
the actor a fact its character does not have.

**And the constraint is realism, not just safety.** A person experiences the world from inside one
head, without access to other minds or to what the story needs next. An actor briefed the same way is
not being handicapped — it is being put in the only position from which a person can be played.

### The wall that exists, and the class it cannot see

This is not a new principle; it is an existing wall widened. `.claude/hooks/beat_blind_guard.py` is a
PreToolUse hook on Task that denies the simulator's spawn when the brief leaks the director's intent,
and it fails closed. Its reasoning is the same one: *"A character told what is supposed to happen will
produce it, and the probe becomes a machine for confirming the director's guess."*

But it catches exactly one class — **directive language about intended outcome**. Its seven patterns
match "the intended beat", "the beat is:", "make her…", "so that she will…", "we need him to…". Three
classes it cannot see, all of which POV isolation forbids:

| leak | example | caught today? |
|---|---|---|
| director's intent | *"the intended beat is reconciliation"* | **yes** |
| interpreted interiority | *"Gideon is furious but still loves his brother"* | no — descriptive, not directive |
| knowledge the character lacks | *"though he doesn't yet know Emmet was coerced"* | no |
| another mind's interior | *"Emmet is ashamed"* | no — only Emmet's observable behaviour is his |

The guard's own docstring explains why it stays narrow: *"SCOPED AND DUMB, on purpose… A guard that
gets clever produces false denials, and a guard that produces false denials gets switched off."* That
is correct, and it means the other three classes cannot be caught by making this guard smarter.

**The emotion class escapes the tradeoff, because it is catchable by EQUALITY rather than by reading
prose.** The block either is the library entry byte-for-byte or it is not. No pattern matching, no
inference, no false positives — the exact opposite of the "gets clever" failure. That makes the
emotion half of POV isolation the one piece of it that can be enforced perfectly, which is a reason to
enforce it there rather than trusting the rule to hold in an agent file. The remaining two classes
(unknown facts, other minds) are a harder problem and are not solved here.

**The showrunner is a COURIER, not an interpreter.** The owner, 2026-09-05: *"the showrunner
delivers the emotion and the prompt from the emotion. The actor decides how to express it, the
showrunner isn't to translate the emotions for the actor."*

This draws a hard line, and an earlier draft of this section crossed it — it said the assembler must
add "which state is primary… said in prose", which hands the showrunner a pen and lets it write
about how the character feels. It must not.

> **Everything the actor reads about the emotion is either the authored baseline VERBATIM, or an
> engine-computed fact in a FIXED form. Never showrunner prose.**

| the showrunner delivers | the showrunner must NOT |
|---|---|
| the baseline block for each live rung, unmodified | paraphrase, condense or "adapt it for this character" |
| the target each state is bound to | summarise the state ("furious but still loves him") |
| which state is primary, in a fixed rendering | decide what the emotion means here |
| what is happening, and the scene | resolve a contradiction between two states |

The last row is the one that would do the damage. A summary like *"Gideon is furious but still loves
his brother"* reads as helpful and is the exact failure the blind test caught above: it resolves the
tension before the actor gets it, and what comes back is the sequence take, not the held one.

**This is a guard, not a rule, because the showrunner is an LLM and paraphrase is its default.** The
check is determinism: **the emotion portion of an actor prompt must be byte-identical for the same
(rung, target, ordering), across runs and across characters.** A courier reproduces; an interpreter
varies. That is directly testable in this repo's idiom — `tests/test_no_digits.py` already scans the
RENDERED string for a forbidden class, and the same shape catches affect language appearing outside
the sanctioned block.

**This does NOT independently locate the library, and an earlier draft claimed it did.** The courier
rule constrains what the showrunner may COMPOSE; it says nothing about where the text is STORED. A
static asset in the agent layer, read and passed through unmodified, satisfies "deliver verbatim"
just as well. Only the argument above — two drivers over one assembler at `prompt.py:27`, and
`CLAUDE.md`'s rule that facts reach an agent through the engine packet — places the library, and it
is one line of reasoning from one reading, not two converging on the same answer.

**Measured 2026-09-05 — the target and the ordering are load-bearing, not polish.** Three actors were
given the same beat (a man whose brother has just admitted selling their dead father's horse to pay
a debt he had kept from the family) and differed ONLY in how the state reached them. A blind judge,
who did not know which was which, ranked them:

| condition | result |
|---|---|
| two baselines, **both targets attached, primary named** | **achieved** — held both at full strength |
| two baselines, no target, no primary | failed by SEQUENCE — anger drained, tenderness replaced it |
| the engine's current behavioural phrases | not achieved — "reads as simply enraged" |

The winning take's proof, in the judge's words: *"some part of him was using the grip for two things
at once: to keep Emmet from stepping back, and to keep Emmet from being anywhere Gideon couldn't reach
him"*, and *"a hand deciding not to become a fist"* — one act that is coercive and protective at the
same time, with the sentence refusing to resolve which. And the thing that proves nothing was spent:
*"Gideon saw the flinch happen and waited to feel something settle because of it, and nothing did."*

The failure of the untargeted condition is worth quoting because it is subtle and would pass a casual
read: *"His hand twisted tighter in the shirt... and then, slowly, it opened. Flattened. Settled
against his brother's chest."* That is anger draining out and tenderness arriving to replace it — a
small arc with a beginning and an end, where the design needs a held contradiction. **Sequence is the
failure mode that targeting prevents.**

One authoring note from the same judgment: in the winning take the love was never spoken, only
staged, and the judge flagged that a reader could mistake the restraint for pride. A baseline whose
felt state is legible only through inference is weaker than one that also reaches language.

*Scope of the claim: one take per condition, one judge, blind. A strong signal, not a proof.*

**And what the assembler must NOT do: name the blend.** The retired architecture would have resolved
anger-plus-love into a single recipe called `bitter` and handed the actor one smoothed state. Two
full-strength states aimed at one person hold a contradiction that the actor exists to resolve; a
computed blend resolves it first and leaves nothing to play.

### Why behavioural phrases cannot be kept: they do not compose

Measured 2026-09-05, a real actor line from the repo's own fixture
(`scripts/direct.py --fixture ashford-slice --char maren-healer`), five paths active at once:

> *"Maren — you ask the next question and reach for the next step; you give ground, you hedge, you
> commit to nothing you cannot leave; you put yourself between them and it, and what you wanted for
> yourself does not survive this; you lose the thread of what you were doing, and you leave it where
> it fell; you do what is asked and none of the extra."*

She is instructed to hedge, to throw herself in front of it, and to do the minimum — in one
sentence. **Five feelings can coexist in one body; five chosen actions cannot.** Behavioural phrases
collide the moment more than one path is active, which is most beats. Sensation, Belief and Impulse
compose without contradiction — a chest can hold a thermal surge and a hollowness at once — and the
actor is the thing that resolves them into a single act.

This is not an argument for authoring the new rungs carefully. It is an argument that the 32
existing phrases are wrong and must be rewritten, independently of the resolution change.

### Two failure modes to author against

**Register drift.** Every rung will be written to be vivid, and the specimen above is vivid because
anger at that height is. Write annoyance in the same register and twenty rungs collapse into three
that all read as crisis. The prose intensity must track the rung, not the author's enthusiasm.
*Testable:* strip the names from one path's rungs, shuffle them, and sort by intensity alone. If a
reader cannot recover the order, the rungs have collapsed and the resolution is fictional.

**Prompt budget.** The specimen is roughly 150 words. Maren above had five paths live at once; at
150 words each that is 750 words of internal state before the situation, the cast, the goals or the
reply contract. The notability gate (RETIRED 2026-09-08) therefore stopped being a nicety and became
the thing that makes the design affordable — total coverage of `[0.01, 1.0]` in NAMING, a strict
budget in SAYING. How many paths may speak in one beat is a real constraint and is not decided here.

**The structure already exists at the wrong resolution.** `direction._PHRASES` is
`[primary][band] -> phrase`, four bands per primary. Twenty rungs is the same table with more rows —
this is a filling-in, not a rewrite. What must change is the CONTENT (felt, not behavioural), and
that change applies to the 32 phrases already written as much as to the ones still to come.

### The first step is not the absence

**Rage's base is not peace. It is the first flicker where a wrong registers.** A path that starts at
`serenity` has spent its bottom quarter naming a state that is not the emotion at all.
`emotion-scales.md`'s region table already gets this right — its first row is `*(below)* 0.00-0.25,
it does not register as a wrong`, unnamed, off the ladder, with `annoyance` as the first named
region. That is the pattern every path follows.

### Rungs, not vocabulary — the ladders are evidence, not output

**A path does not need synonyms.** The consumer of a path name is the actor: an LLM playing the
character. It does not need vocabulary — it has vocabulary. What it cannot supply for itself is
where the character actually IS, and one precise word carries that as well as forty do.

So the fifteen ladders in `docs/emotion-names/` are **raw material for finding the rungs, not the
artifact**. You read 245 rage words to discover that there is a real boundary between *it registers
and you let it pass* and *you answer it, and you know you are answering*. Then you keep one name for
each side, and the other 240 words have done their job.

`emotion-scales.md` already works this way and is the model: its five anchors are not words, they
are behavioural statements — *"it registers, and you let it pass without marking it"*, *"you are
answering sharper than you meant to, and you notice that you are"*, *"the one in you who keeps watch
has stepped out"*. The words `annoyance / anger / fury / rage` are LABELS on those rungs, not the
content of them. The content is what changes.

**This is why the rung COUNT is per-path even though the GRID is shared.** Boundaries always fall on
the 0.05 grid (§1), so paths stay comparable; but a path takes only as many rungs as the behaviour
genuinely changes times, merging adjacent slots where it does not. Aim for twenty, accept eight, and
never invent a boundary to reach the target — a rung that names no change will be emitted as a
change the character did not undergo.

**What this deletes.** Ordering hundreds of near-synonyms was going to be the most expensive part of
this work, and it is now not part of it. "Is `pique` above or below `nettled`" is close to
unanswerable, and it was never the question.

### A ladder file holds THREE data types, and only one of them is the path

Measured 2026-09-05. **In two files, confirmed by reading them; the other thirteen are unchecked.**
The origins are named because an earlier draft of this section claimed the finding was corroborated
by five independent audits, and it was not — three of those five restated a digest they had been
given, which is propagation, not corroboration. What follows is what was read directly:

* `RAGE.md` idx 177-190 — `ataraxia, phlegm, stolidity, even-temperedness, placability, irenicism`,
  then `irascibility, iracundity, bad temper, hot-headedness, a short fuse`. Dispositional poles.
* `FEAR.md` idx 156-175 — `temerity, rashness, recklessness, foolhardiness, audacity, derring-do,
  ... valor, gallantry, boldness, pluck, mettle`. A courage cluster: how a person characteristically
  meets danger, which is a different variable from how afraid they are now.
* **Counter-evidence, which is why this is not stated as a general rule:** `PLAY.md` and
  `CARE-outward.md` at the same depth are CLEAN — `Deep flow, Peak experience, White moment, Flow`
  and `Devotedness, Dedication, Fidelity, Constancy, ... Sacrifice, Martyrdom` are climb tops, not
  trait poles. Contamination is a per-file defect to be checked for, not a property of the corpus.

`docs/emotion-names/RAGE.md` is one file containing three different kinds of thing:

| data type | example from RAGE.md | where it belongs |
|---|---|---|
| **state** — where the character is right now | `annoyance, irritation, ... tantrum, meltdown` | THE PATH |
| **trait** — what kind of person they are | `ataraxia, phlegm, stolidity, even-temperedness, placability, irenicism` at the calm pole; `irascibility, iracundity, bad temper, hot-headedness, a short fuse` at the angry pole | the character sheet — a disposition, not a walk |
| **descent** — after the state, not below it | `being reconciled, burying the hatchet, water under the bridge, being propitiated, spent anger, the cooling-off, being over it` | the path's descent list (below) |

**This corrects an earlier reading in this session.** The apparent "restart" at index 177 of 245 —
the file climbing to `amok` and then beginning again at the calmest words it contains — was recorded
as a sweep that ran twice and needed reordering. It is not. Index 177 is where the TRAIT sweep
begins. The words are in a perfectly sensible order for what they are; they are simply not states.

So the first operation on a ladder is not sorting, it is **separating** — and separating is a check
each file must be put through, not a transformation to apply blind. A trait word sorted into a rung
is worse than an unsorted file, because it will be emitted as a state the character is in when it is
a description of who they are.

### The descent words are a separate list, not the bottom of the climb

`docs/emotion-names/RAGE.md` opens with `being mollified, being placated, being appeased, spent
anger, the cooling-off, being over it`. They are filed at the low end because they are
low-intensity. **They are not low rage. They are AFTER rage**, and unreachable without having been
angry — you cannot be `spent` without having spent something. Every path needs its descent words
separated out of the climb, because a character at 0.3 on the way up and a character at 0.3 on the
way down are in different states and take different words.

---

## 3. The coherence test

A candidate is a path when all five hold. The first two are the ones that do the work.

**(a) Every rung FEELS different, and the rungs are ordered.** A rung earns its place by feeling
unlike the rung below — by warranting its own prompt — not by being a stronger word and not by
naming a different action. **An earlier draft of this criterion said a rung earns its place by
naming "something a character DOES at it that they do not do one rung below". That was wrong**, and
wrong in the way `emotion-scales.md:350-353` specifically warns about: a rung defined by behaviour
makes the engine decide the performance. The rung is the felt state; what the character does about
it is the actor's. Two words describing the same felt state are one rung with two labels, and the
second label is discarded. *Mechanically checkable in part:* no rung may be empty, and a name may
appear on only one rung of one path. *The real test is authorial and is stated above:* if you cannot
write them different prompts, they are not different rungs.

**(b) The same thing throughout.** The top and the bottom are one emotion at different degrees. Test
it by asking whether "X, more so" gets you the next rung. If getting up the ladder requires changing
what the emotion is ABOUT, it is two paths that have been spliced. *Needs a human eye.*

**(c) The rungs TILE `[0.01, 1.0]`.** Not merely "every band has words" — the rung boundaries must
partition the interval exactly: the first rung begins at 0.01, the last ends at 1.0, and each begins
where the previous ends. A gap is a value the engine can hold and cannot name. An overlap is a value
with two answers. *Mechanically checkable, fully, and it is the single cheapest check in the set —
it is arithmetic on the boundaries and needs no judgment at all.*

**(d) Not a segment of another path.** If sorrow's ladder turns out to be a stretch of grief's
ladder, it is not a second path — it is a region of the first. **This is the only surviving piece of
irreducibility, and it is the right piece**: it stops the path list growing without bound while
still allowing paths that overlap. *Partly checkable — the same word appearing on two ladders is a
flag, not a verdict; `_COLLISIONS.md` already tracks these.*

**(e) Reachable.** Something in the world must push it up, and something must push it down. A path
nothing can move is a channel that emits and never receives — this repo's named defect class, and it
has happened here before: LUST sat at its authored value forever, emitting four phrases and
receiving nothing, until a seventh appraisal dimension was added for it. *Mechanically checkable
against `state._DIM_TO_PRIMARY`.*

**Measured, and it bears on (e) for four existing paths:** RAGE, LUST, CARE and DISGUST have **no
appraisal dimension that lowers them**. Only PLAY (threat/loss/social_violation), FEAR
(mastery/relief), PANIC_GRIEF (relief) and SEEKING (loss) can be pushed down by an event. For the
other four, time is the only way down. Any new path must name both directions or it inherits the
same gap.

---

## 4. The fifteen we already have are not walks yet

`docs/emotion-names/` holds fifteen ladders — RAGE, FEAR, PLAY, SEEKING×2, CARE×3, PANIC_GRIEF×2,
LUST×2, DISGUST×3. **They are the data structure this architecture needs, and nothing in the engine
reads them.** The only reference in the tree is `scripts/gen_map.py`, which indexes the directory as
documentation.

**They are not ordered.** Measured 2026-09-05:

* `RAGE.md` climbs to `amok` and then **restarts at index 177 of 245** with `ataraxia, phlegm,
  stolidity, irenicism` — the calmest words in the file. A position derived from list order puts
  `irenicism` (peacemaking) at RAGE 0.75.
* Contiguous out-of-order suffixes, for the eight ladders with a `_RAW_SWEEPS.json` record:
  RAGE @177/245, SEEKING-reflexive @138/188, FEAR @205/236, LUST-bound @73/93,
  PANIC_GRIEF-reflexive @104/119, PANIC_GRIEF-bound @144/155, SEEKING-outward @152/158,
  LUST-unbound @84/88.
* Only three of those eight are cleanly "one sweep, then one appended block" (RAGE,
  SEEKING-reflexive, PANIC_GRIEF-reflexive). The other five carry out-of-order words interleaved
  throughout — FEAR 49 of them, SEEKING-outward 35, PANIC_GRIEF-bound 18, LUST-unbound 10,
  LUST-bound 5.
* CARE×3, DISGUST×3 and PLAY have no sweep record at all, so their order is **unknown**, not
  known-good.
* Three files hold FEWER names than their own sweep (LUST-bound 93 < 103, LUST-unbound 88 < 97,
  PANIC_GRIEF-reflexive 119 < 120), so the files are edited artifacts rather than logs.

**They are word collections, not walks.** Ordering the fifteen is therefore the larger half of the
work, and adding the missing paths is the smaller half.

A second question the files raise: the role suffixes. `CARE-outward`, `CARE-reflexive` and
`CARE-unbound` may be three paths, or one path with target-conditioned vocabulary. Self-compassion,
agape and love-for-a-person top out in different places, which argues for three; they are driven by
the same appraisal, which argues for one. Decided from the words, not from theory.

---

## 5. What a finished path looks like

The form, so every path lands in the same shape:

```
PATH: <NAME>
  first step:   <the faintest form that is still this emotion>
  rungs:        <name> : <the prompt — what is true INSIDE the character at this rung,
                                 felt state, never an action the engine has chosen>
                ...                        (in order, low to high; as many as the
                                            behaviour actually changes times, no more)
  top (1.0):    <the change in kind>
  descent:      <the words for coming down, which are not the climb reversed>
  raised by:    <appraisal dimension(s)>
  lowered by:   <appraisal dimension(s), or NONE — which is a gap, not an answer>
  persists:     <in words: does this flash and pass, or linger, and why —
                 a fact about the emotion, and the input a later pass needs>
```

`persists` is prose on purpose. It says *fear disengages once the threat resolves* and *grief holds
because the loss does not un-happen*. It does not say a number, because the number is not this
document's business.

---

## 6. Deliberately not here

**Rates, decay numbers, the accumulation arithmetic, and the prompt wording are all out of scope,**
in that order, and they come after the path set is settled. The reason is the owner's, and it is
right: the math has to be built to work with the emotions and their decay characters, so designing
it first means designing it against a path set that does not exist yet.

One measured constraint is recorded here so the later pass has it, **not as a problem to solve now**:

> `state.decay()` runs unconditionally after every `appraise()` at both production call sites
> (`scripts/scene.py:513-515`, `scripts/direct.py:435-437`), documented as mandatory every beat in
> `docs/state-engine.md`. Driven that way, five small pushes of 0.025 on a character at RAGE 0.6
> with a mean of 0.3 and `r=0.80` drive rage **down** to 0.4655, not up. Break-even at 0.6 is a push
> of 0.075 — three times an annoyance-class event, which prices to about +0.025. **Repeated small
> provocations currently lose ground to decay rather than accumulating.**

That is a requirement the arithmetic does not yet meet. It is written down so it is not rediscovered,
and it is not addressed here.

Also deferred, and tracked so they are not lost:

* **What happens to `compounds.py`.** Forty-one recipes and a cosine matcher, built for the retired
  architecture. Measured broken independently of the architecture change: `recognise` scores by
  cosine, which is scale-invariant by construction, so a pure RAGE vector returns `fury` at
  **0.10, 0.20, 0.35, 0.60 and 0.95** — the same name at every intensity, including `fury` for a
  character in the band that "does not register as a wrong". The likely answer is that compounds
  stop being a basis and become a way to name CO-OCCURRENCE across paths, which must read positions
  rather than the angle of a vector.
* **The relationship between `PRIMARIES` and paths.** If paths outnumber primitives, a primitive may
  be just a path, or primitives may survive as the things dimensions push while paths are the naming
  layer. This is the seam everything else hangs off.
* **The drop from 1.0.** `emotion-scales.md:101-111` makes 1.00 a change in kind — *"the one in you
  who keeps watch has stepped out."* Coming back from that is the observer returning, which is not
  the same event as anger cooling, and `spent anger` is the wrong name for it.

---

## 7. What the two earlier drafts got wrong

Both were written under the compound architecture, before the path model existed.

**v1 (`staging/docs/emotion-dynamics-v1-absolute-coordinates.md`)** measured every constant as a
distance from 0.0. Its descent formula `fallen = (peak - value) / peak` treats zero as the bottom of
a fall, but values relax toward the character's resting position, never toward zero — so its
`settled` stage was unreachable for any character resting above a quarter of their peak. Measured: a
mean of 0.30 parks permanently at `fallen = 0.70`, describing a fully recovered character as still
cooling off, forever.

**v2 (`staging/docs/emotion-dynamics-v2-rest-relative.md`)** over-corrected. It made the scale
per-character — "eight rest points per character" — which destroys the consistency the whole design
needs. **The scale belongs to the emotion, not to the character.** RAGE 0.6 is RAGE 0.6 for
everybody; what a character brings is where they currently stand on that shared path.

**And the engine was already right about this, which is the part worth keeping.** Measured
2026-09-05 (the renderer described here is RETIRED 2026-09-08): `direction.py` held `_BANDS = (0.25, 0.55, 0.80)` as fixed global cut points with no
character parameter; it banded the RAW value one line *before* the temperament mean was
read at 330. The mean is used at exactly two sites, neither of them naming — a gate on whether to
mention the primary at all, and a suffix appended after the phrase is chosen. Running `direct_affect`
with an identical RAGE of 0.62 under temperament means of 0.10 and 0.75 produced **byte-identical**
stage-direction text; only the trailing marker differed.

So the correct split, which v3 keeps: **the name comes from the position on the shared path; the
character's own baseline only decides whether the state is worth remarking on, and whether it counts
as a departure from them.**
