# Recording model — two streams: thoughts + actions

The simulation captures TWO streams per character per turn: **thoughts** (private interior reasoning/feeling/perception) and **actions** (observable behavior + dialogue). The split is the keystone connecting the simulation to narration, transmission, and deception — because the two streams have *different visibility*, and that difference is the design.

## Visibility asymmetry — this IS the mechanism
| Stream | What | Visibility | Flows to |
|---|---|---|---|
| **Action** | observable behavior + spoken words | PUBLIC — witnessed by others present | other characters' vaults (transmission) · the event ledger · narration (always) |
| **Thought** | interior reasoning, feeling, perception, relationship-read | PRIVATE — only that character | narration **only when that character is POV** · verification/continuity (always) · **never** another character's vault |

This is exactly the line the POV boundary cuts (`narration.md`): the narrator renders **the POV character's thoughts + everyone's actions** — nothing else. Thoughts are the source of interiority; actions are the source of events.

## Why capture thoughts at all (not just actions)
1. **Narration renders recorded interiority, doesn't invent it.** Close-third interiority = the POV character's *recorded thoughts*, not confabulation at write-time. The inner life is grounded in what the character actually reasoned in the sim.
2. **Deception becomes exact and auditable.** A lie = **thought ≠ stated action**, recorded as both: *"I know the cure is fake"* (thought) + *"This will save her, I swear"* (action). The gap **is** the lie, in the record. The director/verifier sees the divergence; the reader sees only the action — unless the liar is POV, then they get the lie-in-progress. (The same recorded gap also catches the *unintended* divergence class: Project Sid documents LLM agents whose speech and executed action desynchronize as a failure mode (`prior-art.md`, verified 3-0). In our record that divergence is visible by construction — a deliberate gap is a lie; an incoherent one is a defect the critic flags. Without both streams, the two are indistinguishable and invisible.)
3. **Thoughts never transmit → misreading is structural.** Actions propagate to witnesses' vaults; thoughts never do. Another character can only *infer* a motive from actions → a possibly-false belief. Telepathy is impossible by construction; dramatic irony and misattribution are guaranteed, not bolted on.
4. **The thought-stream is where the backstage mechanics surface.** Trust ("he didn't buy the smile"), energy ("she couldn't place where she'd seen the sigil"), beliefs, relationship-reads — all manifest in the thought. Mechanics drive the thought → the thought is captured → narration renders it (for POV). Full loop from backstage numbers to prose, grounded.

## The thought IS the simulator's reasoning trace
One model call per character-turn → structured output **{thought, action}**, thought first. The character's chain-of-thought (deliberating from their vault slice toward a decision) *is* their interiority; the committed output *is* their action. Both bounded by the same vault wall — a character can't *think* about a secret they don't have any more than they can act on it.

## Cost / depth (layered, like character depth)
- **POV character:** full thought capture — it becomes prose.
- **Non-POV characters in scene:** lighter — action + brief rationale (enough to verify consistency + seed continuity for when they later become POV). Their full interiority isn't rendered this scene anyway (no head-hopping).
- Non-POV thoughts are **planning-mode/backstage** for that scene: in the record, absent from the rendered prose.

## Ties together
- → `narration.md`: narrator = POV thoughts + all actions; the split here is the boundary there.
- → `knowledge-model.md` (transmission): actions transmit, thoughts don't.
- → deception: a lie is a recorded thought≠action gap.
- → ledger: actions are the public event log; thoughts attach privately to the character.
