# Verdict — Self-Assessment and Pilot Findings

## Grade Against Acceptance Criteria

### Criterion #2 — Character Integrity

**Grade: PASS, with one caveat.**

Every major action in the piece traces to a stated goal, value, or flaw from the character sheet. The delegation refusal (t6: "No. Flat.") traces directly to "do-it-myself > delegate (guilt → control: trusting another with a life feels like the failure that killed her child)." The inability to receive Bryn's survival (t10: "Not enough. It was not enough last time") traces to the "never-fail-again" goal being unattainable by construction. The washing rite (t17) traces to her relationship to craft-as-ritual, plain in the voice rules. The Joss redirect (t19: "I carry that. That's mine") traces to the wound-as-goal entry: "she will not speak her own wound."

The voice passes attribution: clipped command sentences to patients, flat affect under fear, counting aloud as the anxiety signal, deflection-by-action when confronted with emotional questions. A blind reader could identify Maren from the speech patterns without attribution.

The caveat: the piece does not dramatize the full CARE-vs-CONTROL tension because the control side always wins in this chronicle. Maren never delegates, never softens, never cracks. The character sheet identifies this as the defining tension but the sim's 25-turn record never produces a moment where care defeats control. The character is internally consistent, but the tension is stated, not enacted. This is a structural limitation of the chronicle, not the prose rendering.

### Criterion #3 — Dramatic Shape

**Grade: CONDITIONAL PASS.**

The piece has a shape: act one (the child she saves through control) → act two (the man control cannot hold) → coda (back to counting, nothing resolved). There is a setup (the "enough" dread established at t0), a complication (t4, the Súil ghost), a false resolution (Bryn lives), a true test (Tobin dies), and an aftermath that is not catharsis but continuation. The tension escalates from a scraped knee through a child with climbing fever through a dying elder, and the climax is a man's hand going cold. The piece ends not with resolution but with the loop restarting, which is a legitimate shape for a character study — the reader understands what Maren is and that she will not change.

A test reader would likely call it "a story." The Joss scene is the emotional climax in retrospect: the moment she cannot give the weight away, which proves the wound is load-bearing. That beat earns its placement.

The conditional: the shape is mild. There is no reversal, no moment of genuine choice. The climax (Tobin's death) is something that happens to her, not a decision she makes. She does everything right and loses. That is thematically coherent but dramatically passive. A stronger arc would hinge on a moment where the choice mattered — and the chronicle does not provide one.

### Criterion #5 — Reads as Prose

**Grade: PASS.**

POV is maintained throughout, close-third, no head-hopping. Interior access is Maren's only. Other characters (Joss, Tobin, Edda, Bryn's family) are rendered through her perception and her vault-bounded interpretations. The counting tic is threaded as a continuous voice marker, not introduced at crisis points only. Scene-craft is present: the lamp moved to the child's face "not for herself but because she needed to see" is a dramatization of the stated action that stays fully faithful to the recorded event while adding a POV-specific reason. Sensory texture is light but present (frost on the glass, the candle burned a finger-width, the basin gone lukewarm).

The piece does not read as a stage-direction log. The interiority is the primary mode; action is embedded in thought.

---

## Contained vs Imposed Verdict

**Primary verdict: MOSTLY CONTAINED, one significant imposition.**

### What was genuinely there in the record

The dramatic shape of acts one and two was in the chronicle. The two-arc structure (Bryn: controlled survival; Tobin: uncontrollable death) was visible in the turn sequence without any narrative invention — turns 2-11 and turns 15-20 are structurally the same story told with opposite outcomes, and that structural relationship existed in the data before any cutting-room decision. The Súil ghost was threaded through both arcs via explicit mentions in the thought-record ("It was the second night with Súil too" at t4; "I should have tried the willow bark earlier" at t17). This is a recorded causal loop, not an imposed one.

The ending symmetry — counting yarrow at t0, counting yarrow at t24, nothing resolved — was in the chronicle. The final turn was recorded before any cutting decision; the piece uses it as a coda because it was there to use.

The Joss delegation refusal (t6) and the Joss guilt-redirect (t19) are 13 turns apart in the record, and they rhyme structurally (same doorway, same dynamic, inverse outcome — she refuses to give him the night watch; she refuses to give him the grief). That rhyme was in the chronicle; it was not constructed.

The governing dread — "not enough / it's never enough" — appears at turns 0, 3, 10, 15, and 16 with consistent phrasing. It is a repeated signal in the record, not an editorial imposition.

**Evidence for "contained":** The most dramatically resonant lines in the piece are direct transcriptions or near-direct transcriptions from the record. "He needed more time and I could not make more time" (t16). "I carry that. That's mine" (t19). "He is warm the right way now" (t10). "I did not miss the turn of it" (t16). The prose renders these; it did not invent them.

### What was imposed

One structural choice was imposed: **making the piece about Tobin's death rather than Bryn's survival.** The chronicle has higher affective intensity in the Bryn arc (FEAR peaks at 0.92 at t4, PANIC peaks at 0.58 at t8). Bryn's arc gets more turns and more recorded thought-weight. A naive magnitude-following cut would have centered on Bryn.

Choosing Tobin as the story's center required a craft judgment — that the inversion (control fails) is narratively stronger than the confirmation (control succeeds) — that was not in the record. The record provided both arcs. The decision that the death is the story and the survival is the context was imposed.

A second imposition: the interpretation of t18 ("I boiled it wrong the second night — too long, too long") as irresolvable self-accusation (she may be right or confabulating) is the prose's framing, not the sim's. The chronicle records this as a thought with no counter-evidence. The prose reads it as psychologically ambiguous because the character sheet says she "will not speak her own wound" — which is vault data, not event data. That reading is faithful to the character design but it was assembled from two different files, not from a single self-contained record.

### Implication for the Cutting-Room Design

**The key signal the chronicle doesn't record: which arc is the story.**

The two arcs were mechanically distinguishable (durable vs transient tags, arc-engine magnitude) but they were not tagged with relative priority. The cutting room had to make that choice editorially. This is correct — the design doc explicitly says "magnitude is consequence, not meaning. The quiet scene that carries the book may be numerically flat" — but it means the view that would most help the cut doesn't exist yet: **a "structural inversion" detector** that flags when the same character arc plays out twice with opposite outcomes, because the second instance (the failure) is usually the story and the first (the success) is the setup.

Concretely: the consequence graph would show both Bryn and Tobin as high-consequence events. It would not show their structural relationship (same arc-shape, opposite outcome) or that the death is narratively downstream of the survival. The EDL needs a way to record that relationship as a NOTE entry when the room recognizes it — and the room should know to look for that pattern as a recurring cutting-room heuristic.

**Secondary implication:** the "not enough" language appears five times across the record at different turns, explicitly and in variations. The cutting room needed to recognize this as a governing motif — a through-word, not just repeated dread — and use it to anchor the selection. The chronicle has no MOTIF tag or recurring-phrase index. A lightweight query ("which phrases or formulations recur across turns?") would have surfaced this faster. Not a blocker, but useful.

**Third implication:** the Joss subplot (turns 6 and 19) has narrative payoff only if the cutter recognized the t6 setup when selecting t19. Thirteen turns of separation. This is exactly the consequence-graph gap identified in the design doc (the "planted setups whose payoffs were dropped" audit). The graph would catch it mechanically — but only if the cutter declares t6 as a setup when including it. The EDL NOTE entry is the right mechanism; this pilot confirms it's necessary, not optional.

**On the contained-vs-imposed distinction:** the story was mostly in the record, but a single large craft judgment was imposed (Tobin over Bryn as the center). The design's approach — "the room recognizes meaning, the engine surfaces candidates" — was exactly right here: no engine would have correctly picked Tobin's arc as primary from magnitude alone. The room had to see the relationship between the arcs. What would have helped is the structural-inversion view flagging that Bryn and Tobin had isomorphic arc shapes.
