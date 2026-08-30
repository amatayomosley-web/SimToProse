# small-model-mode — how a weak LLM drives this engine, and what it costs the human

**Status: DESIGN, not built. 2026-08-24.** Nothing here has been implemented. The measurements are
real and reproducible; the architecture is a proposal. Read §7 before treating any of it as settled.

This doc exists because the design otherwise lived only in one conversation and two subagent
transcripts — the shape of thing this repo re-derives from scratch three weeks later.

---

## 1. The finding: this system has two minimum specs and only ever defined one

Games ship a minimum spec. This engine has two, because two different LLMs touch it:

| role | what it does | context cost | who set it |
|---|---|---|---|
| **the ACTOR** | is a character for one turn | **~2,200 tok** | nobody — `assemble` + `direction.py` forced it |
| **the DRIVER** | operates the system: authors, runs, judges, narrates | **~25,000–37,500 tok** | nobody — it drifted to "whatever Claude has" |

The actor's smallness was not tuned. `docs/design.md`'s compute/generate split guaranteed it: the
packet is computed, the perception gate filters it, `direction.py` renders numbers to prose, and
`gate.scope_names` masks unacquired names. The result measures 8,639 chars against 784,708 chars of
design docs — **91×** — and it runs on anything.

The driver got no such treatment. Measured 2026-08-24 (bytes/4, conservative for prose), the cost to
read what `MAP.md` routes you to, on top of ~15,900 tok of orientation:

    author a character ....... 30,000 tok
    author a world ........... 29,100 tok
    run and judge a scene .... 25,700 tok
    whole docs corpus ....... 197,000 tok

A 32k model is at its ceiling before it writes a line, holds a file, runs a test, or keeps one prior
turn. **That is a design defect, not a fact of life** — the actor proves the same repo can produce a
2.2k interface when it decides to.

## 2. The driver minimum spec is 10k, and the narrator sets it

Every task from nothing to rendered prose fits, on rails. The binding lane is narration: a scene
transcript costs ~200 tok/beat, so a 14-beat scene is ~2.9k and the worst measured prompt is ~7.9k
with its reply. That is why the number is 10k and not 8k.

Three lanes need no rails at all — they are already bounded in code:

- **actor** — ~2.3k/turn, dispatched to a local model by default (`scripts/direct.py` `DEFAULT_MODEL`)
- **critic** — capped at ~2.9k by slice arithmetic in `scripts/critic.py:75`, emitted key-free by `--prompt-only`
- **narrator** — already per-scene, `scripts/narrate.py --prompt-only`

Half the job was small-model-ready before anyone asked. What remains is the authoring half.

**OUT OF SCOPE, deliberately:** engine work. The point of this repo is to be USED, not modified by
the models using it. `src/engine/state.py` alone is ~7.5k tok; reading it leaves nothing. Anyone
changing the engine needs 16k for a leaf fix, 32k single-module, 64k cross-module. That is a
different tier of work and it belongs to a different tier of model.

## 3. Rails = decompose + scriptify, and the glue must be scripted

"On rails" means two mechanisms, and they only work together:

1. **Decompose** each task into parts small enough to fit the budget alone, with a defined input and
   output, so the model does one bounded thing per step.
2. **Scriptify** anything that does not need a model. Determinism is free context.

They interact: decomposition is only affordable if the glue is scripted, **because otherwise the
model pays context to remember where it is.** State between steps lives on disk, not in the window.

The topology is a **conveyor, not a graph**: a rail with two foreach loops (per character, per beat)
and a retry cycle per station. There is no dynamic routing for anyone to perform, and that absence
is the design — a general graph's freedom (arbitrary conditional edges, model-driven routing) is
precisely what this exists to remove. Position is a cursor on a rail, not a walker on a web.

Three station kinds: **SCRIPT** (no model), **SHEET** (one call, one bounded transformation), **HOLD**
(an operator artifact is required). Seven lines: container → world → cast → plan → simulate →
render → accept.

**The move that satisfies "no higher-level thinking" completely:** anything that *is* higher-level
thinking — beats, the cut, canon waivers — is not handed to the model at all. It becomes a hold. That
is not a compromise imposed by weakness: `docs/orchestrator-design.md` §2 already rules that story
meaning, beats and endings are always the author's, at every tier.

### Recovery

Typed rejection slips carry the validator's message **verbatim** — `scripts/lint_book.py`'s errors
already name the field, the rule and the fix, which is exactly what makes the loop workable for a
weak model. A `{"need": "..."}` escape is resolved only from a per-station whitelist; an
un-whitelisted need does not loop, it parks labelled **"sheet design gap"**, which is the most
valuable telemetry the system emits. Bounded attempts, then park.

Parking writes the full call sheet to `HALTED.md`. Because sheets are self-contained, **escalating to
a stronger model costs nothing** — you hand it the identical sheet. That is the dividend of never
holding threads.

## 4. Station kind is a function of tier, not a fixed property

Offload is conserved. What the model cannot carry, the human does. A 3B user is not running a
degraded workflow; they are running a **different division of labour**.

So the same station is a HOLD at 3B, a SHEET at 30B, and automatic at frontier tier. The station
table carries a tier requirement and the runner resolves SHEET-vs-HOLD at dispatch. **One rail,
several labour splits** — not a small-model fork maintained beside the real one.

This makes the honest metric **decisions-per-finished-scene at tier X**, logged from the run,
surfaced before the first beat rather than discovered at the fourth. "Does a 10k model finish a
book" is the wrong question; it will, if the human absorbs enough.

**Holds are graded, not binary.** A hold that says "decide" is expensive. A hold that computes the
option set first — "beat 4 didn't land; here are the three revisions consistent with the plan" —
costs a decision instead of an analysis. Lowering the *cost* of a hold is available even when
lowering the *rate* is not, and at weak tiers that is where the leverage is.

## 5. The craft toolboxes compile into menus; they are never loaded

Measured 2026-08-24: `.claude/skills/` totals **922,593 chars ≈ 230,000 tok**. `character-frameworks`
alone is ~156,700. No toolbox fits a 10k window. Even the smallest useful one eats the budget whole.

**The repo already solved this once without naming it.** `data/formative_profiles.json` is 94
profiles (98.7 KB) compiled out of the character-frameworks craft. The model never reads it — it
reads a **7,156-char menu** of names and one-liners, picks two or three, and `composition_pass.py`
does deterministic arithmetic on the full diffs. Craft applied at BUILD time, collapsed into a finite
choice set. Not summarized — **compiled**.

Generalised: toolboxes become **menus**, and menus serve two consumers differently.

**The model does not need explanation to pick.** Vela's shipped retrieval engine decided this
empirically: `signal_caller.dart:165` skips LLM judging entirely for candidate sets of **≤7**, because
"the cost of losing a real candidate outweighs the value of pruning one hallucinated noise hit." Craft
axes are 3–8 options. They sit under that threshold. The model gets names and one-liners — ~100–300
tok per axis — and its low-confidence path is **defer to the human**, never *read more*.

**The human does need explanation, and it is free.** Tiers 2 and 3 are human-only, so they escape
token economics entirely: their constraint is a screenful, not a context window.

| tier | face | size | consumer |
|---|---|---|---|
| T0 | name + aliases | ~50 chars | both — this IS the menu line |
| T1 | gloss + the consequence line (what it commits you to mechanically) | 15–30 words | both — all the model ever sees |
| T2 | one **contrast block per axis**: when it wins / when it breaks / worked instance | ~1,000 tok/axis | **human only** |
| T3 | pointer into the toolbox section — no copy | a path | human only |

T3 is a pointer rather than a copy because canon lives once. A deep tier that does not exist twice
cannot drift.

**Compiled, not retrieved.** Stdlib-only (`pyproject.toml:11`, `dependencies = []`) bans the retrieval
substrate outright, and the case is stronger than the constraint: every stage of an open-corpus
retriever exists to survive an open corpus, and eleven fixed in-repo toolboxes are the most closed
corpus imaginable. Four failure modes, each with a Vela invoice attached — different paths acquire
different gates; file-granularity retrieval structurally penalises the best-organised toolboxes; craft
vocabulary is saturated with near-duplicates by name (free indirect = narrated monologue = style
indirect libre = erlebte Rede, four names for one technique in `narrative-craft`), which a similarity
retriever returns as rivals and a compiled menu folds into one option with an alias line; and a
156.7k-tok toolbox is a diffuse container that is noisy exactly where the corpus is richest.

The one case retrieval would win — an **open** option space — is already handled the composition-pass
way: **propose + admit**, not retrieve. `src/engine/profiles.py:147` `admit()` with
`MAX_COSINE_SIMILARITY = 0.95` at line 41. Early books propose often; later books mostly pick.

**cairn 0061 binds one design choice.** A T2 render must be ONE contrast block across the options,
**differences first** — never N independently-written same-register paragraphs. Selecting confusable
same-register material and resolving it by attention is the shape 0061 indicts, and it degrades a
human reader for the same reason.

## 6. What must not rot

Every hand-maintained artifact in this repo has gone silently wrong at least once — **eight measured
instances**, the most recent found the same day this was written. Compiled menus would be the ninth.
The containment is the pattern that already worked (`scripts/gen_map.py --check` + `tests/test_map.py`):

- **hash anchoring** — each option's source section is hashed; mismatch fails naming the entry
- **anchor-token check** — the option's name must literally appear in its cited section, which catches
  renames that hash-drift reports only opaquely
- **reader check** — every compiled field has a named consumer verifiable by grep. This repo's single
  most repeated defect is the documented key with no reader: `formative.*`, `verdict_for`,
  `bible.drifted`, `canon-ledger` with no generator. **A field ships only with its reader.**
- **eager, never lazy** — the check runs in the verify block every session. A "recompute when stale"
  flag serves the stale artifact forever; that trap has bitten twice in Vela and once here.
- **detect, never self-heal.** Adaptive machinery on a closed corpus is measured dead weight.

## 7. What is air

Stated plainly, because the rest reads as more settled than it is:

1. **Nobody has run this engine end to end, in any mode.** `CLAUDE.md`'s Status has said "next genuine
   step: run one" since 2026-07-24. Every number above measures a PART. The first real run will find
   what no amount of design does.
2. **Quality at 3B is completely unmeasured.** It was set aside deliberately to answer the context
   question first. It is the thing that decides whether any of this is worth using.
3. **Two stations still contain judgment** — writing a scene cfg, judging whether a beat landed. Both
   have named degradations (operator-authored cfgs; a mechanical-only gate), each costing gate
   strength rather than architecture. The beat judge is where a confidently-wrong small model admits
   bad canon, and bad canon compounds.

## 8. The falsification, runnable before any of this is built

Three arms, mechanical endpoints, no human judge required:

- **A**: small model + rails. **B**: same rails, strong model — separates rail failure from model
  failure. **C**: small model, no rails, handed the guide instead — predicted to fail on context alone.
- Pre-registered pass conditions: the cfg parses within 2 attempts; the scene reaches ≥70% of baseline
  beats-before-lull over 3 seeds; faithfulness-reject and empty-draw rates within 2× of baseline; and
  **context integrity — `prompt_eval_count` ≤ 10,240 on every call, one overflow fails the arm.**

That last condition is the one that matters: it makes "fits in 10k" a measured fact rather than an
estimate, which is the whole claim this document rests on.

---

**Related:** `design.md` (the compute/generate split that made the actor small) · `orchestration.md`
and `orchestrator-design.md` (the agent layer and why beats are the author's) · `composition-pass.md`
(the propose/admit channel this generalises) · `guide-operating.md` (the hybrid tiering this extends)
