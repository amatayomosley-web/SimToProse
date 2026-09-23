# Narration — "who says this?" (the prose voice and its knowledge boundary)

We specified the simulation thoroughly (characters act, walled to their vaults) but left the PROSE VOICE implicit. "Who says this?" exposes a real **second boundary**: the narrator has its own knowledge boundary, separate from the characters'. Get it wrong and you re-open the omniscience leak at the prose layer even when the simulation was clean.

## Two steps, two boundaries
1. **Simulation (what happens):** each character ACTS, hard-walled to *their own* vault → EVENTS (actions, dialogue, choices). (Designed.)
2. **Narration (how it's told):** a narrator RENDERS the events into prose → bounded by the **POV character's** vault. (This doc.)
Same injection discipline, applied twice. "Who says this" is about the second pass.

## Recommendation: POV-bounded narrator (close third or first). Omniscient is AVAILABLE, not default.
If you simulate cleanly per-character and then narrate *omnisciently*, the prose betrays the simulation — it tells the reader things the POV character can't know, collapsing the dramatic irony the whole vault model exists to create. Narration mode must MATCH the simulation discipline: **the narrator's knowledge = the POV character's vault (for that scene).**

Renders:
- POV character's **perceptions** (what they witness),
- POV character's **interiority** (beliefs, feelings, relationship-reads = their vault),
- other characters' **observable** actions and words (public; the POV saw/heard them).

Does NOT render:
- other characters' interiors, secrets, true motives — only the POV's **(mis)reading** of them.

**That last line is the payoff:** close-third through a vault-bounded narrator *automatically* produces dramatic irony. "Marcus smiled, and she took it for warmth" — the reader sees Marcus as the POV sees him, and is wrong *exactly where she is wrong*. That literary gold only works if the narrator is POV-bounded. (Omniscient is a legitimate literary mode — but choosing it here throws away what the architecture was built to give you.)

## Voice and knowledge are TWO axes, and only one of them touches the wall

Everything above argues one default. It used to read as a prohibition, and until 2026-09-01 it was
enforced as one: `narrate.py` hardcoded *"close-third-person"* into the prompt, so no other voice
could be asked for, and `pov_split` had no branch that could show a narrator anything else. The
argument was about the default; the hardcoding made it a rule. William unlocked both
(*"as a literary machine we shouldn't handicap the voice used for writing"*, and *"unlock
omniscient, let user decide what they need"*).

| axis | what it is | constrained by |
|---|---|---|
| **voice** | grammatical person and distance — `first`, `close-third`, `distant-third`, `second` | **nothing.** A rendering instruction over the same transcript. |
| **knowledge** | whose recorded interiority the narrator is shown — `pov`, `omniscient` | `narrate.pov_split` — the wall is in the INPUT, so a prompt cannot un-see what it was handed. |

`python scripts/narrate.py --voice first --knowledge pov` and every other pairing. Defaults stay
`close-third` + `pov`, because the argument above is still the right default.

**What omniscient IS here, stated so it does not drift into something larger.** The simulation
records every character's thought; `pov_split` hides the non-POV ones at render time. So the
guarantee is RESTATED, not abandoned:

    was:  the narrator's knowledge = the POV character's vault, for that scene
    now:  the narrator's knowledge = the UNION of recorded interiority, for that scene

Still bounded, still checkable, still faithful by construction — nothing is invented, the narrator
is simply not blindfolded. What is traded away is the dramatic irony this doc argues for, which is
exactly the trade that belongs to the author rather than the engine.

**Omniscience over the RECORD is not omniscience over the world.** The narrator still may not render
what no character thought, felt or observed. `tests/test_narrate.py` asserts it: every interiority in
the transcript must trace to a `thought` on a real turn, for both knowledge settings — the
prose-layer twin of `faithfulness.check_name_leaks`.

## Mixed voice is a per-scene row

`scenes` carries `voice` and `knowledge` beside the `pov` the director already chooses (schema v13).
`narrate.py --book` renders each scene in its own, so a manuscript can alternate — *Bleak House*
alternates first and third, *Gone Girl* alternates two first-person narrators, *As I Lay Dying*
gives fifteen narrators a chapter each. Passing `--voice` or `--knowledge` explicitly overrides
every scene; omitting them lets each scene's recorded choice stand.

## Multi-POV: switch the boundary, never violate it
To show what a *different* character knows, switch POV by scene/chapter — each scene's narrator is bounded by that scene's POV vault. You cover the whole story's knowledge across scenes without an omniscient voice. Change boundaries; don't break one.

## Two sub-questions inside "who says this"
- **WHICH entity:** a character's POV (close-third / first), or a **frame-narrator** — a specific character telling the story (one named character narrating the whole book). A frame-narrator is still vault-bounded, by *their* knowledge.
- **FROM WHEN:** *real-time* (knows only up to the scene moment → pure dramatic irony) vs *retrospective* (telling it after → knows the arc, can foreshadow: "I didn't know then…"). Retrospective expands the boundary to the narrator's *eventual* knowledge — not unlimited.

## The narrator is just another vault-bounded entity
It uses the **same injection** as the simulator: feed the renderer the POV character's relevance-gated vault slice + the scene's recorded events. No new machinery — narration is a render-mode of the injection model.

## Hard parts
- **Head-hopping = the prose-layer omniscience leak.** The simulator runs *all* characters (each walled); the narrator must pick ONE POV per scene and render only that one's interiority. LLMs drift into rendering everyone's thoughts — constrain explicitly to one vault per scene. (Prose-layer beat-blind.)
- **Unwitnessed scenes.** A secret meeting no POV attends *cannot* be narrated by a POV-bounded narrator. Options: don't show it (the reader learns of it later, the way a character does — consistent with the knowledge model), or anchor it to a present POV. A feature (information reaches the reader the way it reaches the cast) but it constrains which scenes you can cut to.

## Prior art
Scribe's **A5 (Prose Generation)** is the narrator/render node — but its Context Assembler feeds A5 an *omniscient* context (author-mode, verify-after). For sim-mode, A5's context must be the **POV character's vault slice**, not the full picture — the same inversion as the injection layer: the narrator sees only what the POV knows.
