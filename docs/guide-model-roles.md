# Guide — choosing a model for each role

**For the author, the partner, and any model reading this system.** Every place a language model does
work here is a ROLE. This page says, for each role, what the job is, what reads its output, what
checks it, and so what kind of model can fill it — with the reason, so the choice can be re-made when
model names change. Requirements come first; today's example models come last, because names age and
requirements do not.

## Six questions decide a role's floor

1. **What reads its output, and does anything check it?** A CHECKED output — the engine verifies it,
   refuses it by name, or a person reads it before it counts — tolerates a cheaper model: a miss costs
   a retry or a flag. A TRUSTED output — nothing downstream can tell a well-formed wrong answer from a
   right one — needs the strongest judgment available.
2. **Does its error stay put, or compound?** The log is append-only (CLAUDE.md hard rule 2). A wrong
   value that becomes a recorded fact is read by every later beat. An error that compounds needs a
   higher floor than one that stays in the beat it happened in.
3. **How often does it run?** One call per beat per speaker is high volume; once per scene or once per
   character is low. High volume with a check behind it can drop a class; a single gate that everything
   downstream depends on rises a class.
4. **Does it have to answer in an exact shape?** The engine's seats reply as one JSON object in a fixed
   vocabulary (rung names, path names, concept ids). Even the strongest model drifts: on 2026-09-11 it
   wrote a path name in lower case in 105 of 221 answers, each refused until the parsers learned to
   forgive case (`docs/guide-operating.md`). A weaker model drifts more, and each drift is a lost beat.
5. **Does it drive tools?** An AGENT role runs scripts, spawns specialists, reads refusals and stops at
   them, over many steps. That needs a model built to drive Claude Code's tools. A local chat model
   cannot fill any agent role; agent roles run on Claude models only, chosen when the agent is spawned.
6. **What must it not see?** Some roles are walled: the character's actor never sees the director's
   intended beat, and each seat answer must not see another's. A wall decides HOW a role is run (a fresh
   agent per prompt, never one agent answering a batch), not how strong the model must be.

## The classes, by capability

| class | what it can be trusted with | today's examples |
|---|---|---|
| **Local** | high-volume work that something checks; free per call, private, slower; weaker at long instructions and exact vocabulary | an open-weights model through Ollama on this machine (the actor's default: gemma4 26B-A4B) |
| **Mid** | long instructions followed exactly, reliable tool use, procedural judgment | Claude Sonnet |
| **Top** | judgment where a wrong answer is recorded as fact and nothing catches it | Claude Opus (on OpenRouter: `anthropic/claude-opus-5`) |
| **Best prose** | writing that is itself the product | the strongest writer available: Claude Fable, or Opus |

**How an engine role reaches a model.** Engine roles are single calls made by the scripts. Each can be
answered by a local model, by OpenRouter (needs a key: the `OPENROUTER_API_KEY` line of the file
`SWE_ENV_FILE` names, or of a gitignored `.env` at the repo root), or by a subagent answering each
prompt out of process (the replay backend in `scripts/provider.py`: no key, but every answer is a
spawned agent, and a spawn opens at about 67.5k tokens of context before it reads its prompt —
measured 2026-09-27). Agent roles are Claude subagents and take a Claude model only.

## Engine roles

**Actor** — plays one character's beat (`scripts/direct.py`, `scripts/scene.py` `--model`).
- Output: the beat (what they do and say, their private thought, their own tags), recorded as-is.
- Checked by: the faithfulness guard — a name the character does not hold, or an empty draw, is asked
  again (up to two retries); a turn is never edited (`direct.faithful_turn`).
- Needs: stay inside one person's voice, knowledge and senses from a bounded prompt (measured at about
  3,000 tokens for a principal); return one JSON object.
- Floor: **Local**, at the size class tested (26B). Why: it runs once per beat per speaker, the guard
  catches its worst failure, and the NUMBERS come from the seats, not from the actor — a weaker actor
  writes flatter beats, which is a quality cost, not a corrupted record. Smaller local models are
  untested here: run the test before trusting one.
- Test a candidate: a burst on a scratch copy of a book with `--model ollama/<candidate>`; read the
  beats, and count the guard's re-asks and empty draws in the run's output.

**Composer** — picks the register the actor plays at, from rows the engine offers.
- Checked by: `composer.verify` refuses any pick the engine cannot back, and any refusal or failure falls
  back to the deterministic floor (`direct._compose_selection`).
- Floor: **Local** — the same model as the actor, so a local server never swaps models between calls.
  Why: a bounded choice from a verified menu, with a fallback.

**Event seat and emotion seat** — the sensors (`scripts/appraiser.py`). The event seat rates what
happened (severity words per dimension); the emotion seat says what arose in the person who acted.
- Output: the readings every emotional movement is computed from (`docs/emotion-arithmetic.md`).
- Checked by: the parser only — shape and vocabulary. A malformed reply is refused (the beat falls back
  to the actor's own tags for the event, and to no readings for the emotion), but a well-formed WRONG
  reading is recorded as fact, and nothing downstream can tell.
- Needs: follow a long fixed system prompt (the nine ladders and the concept menu, thousands of
  tokens) to the letter; judge subtext; copy the allowed words exactly.
- Floor: **Top**. Why: "a confidently wrong reading poisons the log for the rest of the book"
  (`docs/constant-register.md`, `DEFAULT_SEAT_MODEL`); the log is append-only; two calls per beat. The
  owner ruled on 2026-09-11 "we need accuracy"; on 2026-09-27 the owner made the seats' backend a choice
  set per session (local, OpenRouter or subagents). A run on seats below the floor is a knowing trade — a cheap draft the author can
  reject and run again on Top seats — never a default.
- Test a candidate: `python tests/appraiser_bakeoff.py --model <candidate>` scores rung accuracy
  against 542 passages whose true rung is known; compare with a Top model on the same passages.

**Keeper** — notices world facts spoken or done in a scene (someone moved, learned, now holds
something), rules on claims, classifies attachments (`scripts/keeper.py`).
- Checked by: the fold — a proposal lands only if folding it would change the world snapshot
  (`world_events.would_change`). Whether the notice is TRUE to the text is judgment, and is not checked.
- Floor: **Top**. Why: a wrong notice moves canon — a location, a holding, a secret — for the rest of
  the book.

**Critic** — reviews a recorded scene for continuity and voice (`scripts/critic.py`).
- Checked by: a reader — in the scene playbook its flags go to the author, who decides; nothing is
  corrected unless someone runs `critic.py --correct`.
- Floor: **Mid**. Why: a miss costs a flag, not canon. (In the scene playbook the showrunner reads the
  critic's prompt and judges it itself, which costs no extra spawn.)

**Narrator** — renders a recorded scene as prose from one point of view (`scripts/narrate.py`).
- Checked by: the author, reading it.
- Needs: follow voice, tense and point-of-view rules exactly; use only what the recorded scene shows;
  invent no inner life for anyone but the point-of-view character.
- Floor: **Best prose**. Why: the prose is the product; it runs once per scene, so the cost is small.

**Character classifier** — at character creation, reads a backstory and picks formative profiles
(`scripts/composition_pass.py --classify`, `--attach-classify`).
- Floor: **Top**. Why: it runs once per character, and a wrong pick can mint a wound or a belief the
  character never had into their sheet.

**Thermometer** — reads the feeling of an existing text, for read-alongs only (`scripts/readalong.py`).
Not used in scenes. Floor: **Top**, for the same reason as the seats.

## Agent roles (Claude models only)

**Partner** — the session the author talks to. It turns the author's wishes into directions, keeps the
author's words verbatim, runs the mechanical steps itself, and relays reports (`docs/CONTRACTS.md`).
- Floor: **Top** — the model the session is opened on. Why: it is the only role that talks with the
  author; a paraphrased yes would change the book's record, and it decides what the other roles are
  asked to do.

**Showrunner** — runs one scene: opens a draft, runs the scripts in its playbook, spawns specialists,
judges continuity itself, stops at the first refusal, and reports in a fixed JSON shape.
- Floor: **Mid**. Why: its work is procedural — a playbook, a fixed command list, a report shape — and
  its walls are enforced by the engine, not by its judgment (the record changes only through
  `scripts/draft.py`, and only with the author's words). Measured 2026-09-27: Sonnet ran the scene
  playbook end to end on a fixture book, and on a real book stopped at the first refusal and reported
  it correctly. A model that cannot drive tools over many steps cannot hold this role at all.

**Director** — shapes a scene toward the story the author agreed; says no, and why, when the world
cannot produce it. Floor: **Top**. Why: story judgment; its placement becomes the circumstance every
beat of the scene is played in.

**Recorder** — reviews the turns the engine flagged when consolidating what a character lived. Floor:
**Top**. Why: its agent file names this "the one error class that COMPOUNDS".

**Cutter** — turns the recorded lives into the novel's scene list. Floor: **Top**. Why: judgment over
the whole record at once; what it leaves out never reaches the page.

**World-builder, character-generator** — author the world and its people; every number must trace to a
life, never to taste. Floor: **Top**. Why: they are the foundation everything is computed from.
Measured 2026-09-27: a Top agent migrated two character sheets to the current emotion model (lint 36
errors to 0) and declined to invent wounds where no profile fit.

**Character-simulator, appraiser (as agents)** — the actor and the event seat, answered by a Claude
agent instead of an engine call. Same floors as those roles, and ONE fresh agent per prompt: an agent
that has seen another answer breaks the wall in question 6.

**Continuity-critic (as an agent)** — the critic, as an agent. Floor: **Mid**.

## Setting the roles: the session profile

The roles are set once per session, when it opens, and hold until it closes (the owner, 2026-09-27). The partner asks
the author and writes the answer with `scripts/profile.py new --out <file> --preset standard|local|subagents [--set
ROLE=MODEL ...]` (`docs/CONTRACTS.md` section 0); every `brief.py` and `scene.py` call then carries `--profile <file>`.
The table and the floors are `src/engine/roles.py`:
- **Hard floors refuse.** An agent role takes a Claude tier only (question 5); the showrunner needs at least Mid.
- **Every other floor warns.** The profile stands, and the warning names the role and the trade - a draft on local
  seats is the author's knowing choice, never a default.
- A model the table cannot place carries its class after an `@` (`qwen/qwen3-235b@mid`), written by the author, so no
  model is ranked by a guess.

Without a profile, each role is set by hand: the actor with `scripts/scene.py --model`; the seats and keeper with
`SWE_SEAT_MODEL` and the key file, or `SWE_SEAT_REPLIES` and `SWE_SEAT_WAIT` for subagents
(`docs/guide-operating.md`); the critic and narrator scripts with `--model`, or `--prompt-only` and a Claude agent;
an agent with the model given when it is spawned.
