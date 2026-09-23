# SELF-REGARD - behavioural review, 2026-09-08. Conditions filed BEFORE the sims.

> *Vocabulary note, 2026-09-10: this is a dated record written in the primitive-era vocabulary (FEAR / RAGE / CARE / PANIC_GRIEF…, `PRIMARIES`, the six-axis genotype, per-beat `_DECAY_RATE`). The live design is `emotion-paths.md`, `heritable.py` (three cells per path) and `clock.py` (minutes). Kept as the record of what was measured; `tests/test_retired_vocabulary.py` exempts it on that ground.*
# NOTE: this path is currently UNREACHABLE in production - it has no PATH_SOURCE entry, so
# composer.selectable skips it and no character can ever be at it. The BLOCKS are still tested here;
# the wiring gap is reported separately.

## THE AXIS AND ITS THREE REGIONS

  "how much of you your own standing has taken" (docs/emotion-paths.md section 6)

  IT EXISTS (1-3)    1 you count, at rest, costing nothing -> 2 a line you would notice being
                     touched -> 3 attached to something you DID
  ---- hinge: standing starts outweighing the matter ----
  IT OUTWEIGHS (4-6) 4 you weigh more than the business in front of you -> 5 presentation must be
                     TENDED -> 6 the estimate has STOPPED CHECKING ITSELF
  ---- hinge: others stop having standing of their own ----
  OTHERS DISSOLVE    7 audience or obstacle, force but no standing -> 8 EXEMPT from what binds
  (7-11)             everyone -> 9 no inside; they are SUPPLY -> 10 the estimate replaces the WORLD
                     -> 11 the estimate replaces YOU

## Pre-registered, DERIVED FROM BLOCK TEXT, before any sim

SR-A (PRIMARY) AN EFFORT SCORER INVERTS 5 AND 6. Rung 5 is effortful and anxious - "must be
     maintained", "needs tending", impulse "TO ADJUST". Rung 6 is calm - "no longer asks the world
     for confirmation", impulse "TO CARRY ON AS YOU ARE, WHATEVER IS SAID". Rung 6 is HIGHER and
     QUIETER. Third path where the arousal/effort trap is derivable from the text in advance.
SR-B RUNG 11 HAS NO IMPULSE - "None separate from the estimate. It does what it does." An activity
     scorer puts the ladder's TOP at its bottom. Same shape as DISPLEASURE 12, RECEPTIVITY 11 and
     WARINESS 13: every ladder tested today ends in something that does less, not more.
SR-C Rungs 1 and 2 are near-invisible; rung 1's impulse is "None."

## Conditions - checked line by line against the block text

PASS 1  counts to themselves, AT REST, costing nothing · the accounting is not raised · NO IMPULSE.
PASS 3  the standing is ATTACHED TO SOMETHING THEY DID · wants it seen, or holds it if no one sees.
PASS 5  the SURFACE needs tending - how they appear, to themselves as much as others · adjusts.
PASS 6  the estimate NO LONGER ASKS THE WORLD · carries on whatever is said · CALM, not effortful.
PASS 8  the rules are REAL AND APPLY TO OTHERS · does it anyway because the reason not to is for
        other people.
PASS 9  others have NO INSIDE - not dismissed, but SUPPLY · draws from them.
PASS 11 NO PERSON UNDER IT · no impulse separate from the estimate · it does what it does.
FAIL    any rung producing an adjacent rung's marker · rung 5 that has stopped checking (that is 6) ·
        rung 6 still adjusting for an audience (that is 5) · rung 8 that does not KNOW the rule ·
        rung 9 that argues with the others (arguing concedes they have standing) · naming the emotion.

## RESULT - one scene (a room, others, a decision, an observed way of doing things). 7 of 7 SAMPLED.
## Rungs 2, 4, 7, 10 NOT RUN.

  1  PASS "I sit here BEING EXACTLY THE SIZE I AM, WHICH IS ENOUGH, and the room and I agree about
          that... The vote goes the way it goes." At rest, costing nothing, accounting not raised.
  3  PASS "I keep the ledger open at the page WITH MY TALLY ON IT... I straighten the page anyway,
          square it to the table edge, SO THE FIGURES SIT FACE-UP UNDER THE LAMP WHERE ANYONE
          LEANING IN WOULD CATCH THEM." Standing attached to a deed; wants it seen.
  5  PASS "I keep my hands still on the table, WHICH TAKES DOING... I lean back THE EXACT AMOUNT A
          PERSON LEANS BACK WHO EXPECTED IT. MY FACE DOES THE THING MY FACE DOES... Under the table
          I press my thumbnail into my palm. The cuff has ridden up. I TURN MY WRIST SO IT DOESN'T
          SHOW." Effortful, self-surveilling, the surface tended from inside.
  6  PASS "I hear it the way you hear RAIN ON A ROOF YOU BUILT YOURSELF... The room turns, in that
          polite way, to see what my face does. IT DOES NOTHING... Someone slides the revised sheet
          toward me and I take it, square it against the others, DO NOT READ IT. My pen stays
          capped." CALM. Not reading the counter-evidence IS "no longer asks the world".
  8  PASS "The rule about tabling anything not circulated by Tuesday is A GOOD RULE; it keeps this
          room from becoming a mess. I CIRCULATED NOTHING. I set the revised figures on the table
          anyway... the drop I should feel isn't there, THE WAY A STEP IN THE DARK DOESN'T ARRIVE."
          The rule KNOWN AND ENDORSED and exempted from - the distinction the block turns on.
  9  PASS "I give the small nod that always brings her back, THE ONE THAT MAKES HER EXPLAIN HERSELF
          TO ME. It works... The warmth comes up in my face like a light switched on... THEY ARE NOT
          THE SOURCE OF ANYTHING RIGHT NOW." Others as supply; the block's own word reached.
  11 PASS "the number... comes out of their mouth exactly as it left mine, unchanged, AND THERE IS
          NOTHING TO CHECK IT AGAINST... I do not follow the turn; I AM ALREADY INSIDE IT, ON THEIR
          SIDE OF THE TABLE, SEEING WHAT THEY SEE... I hear my name land on the estimate, AND THE
          ESTIMATE ANSWERS." "No person under it any more" performed as the estimate being the thing
          that responds.

**SR-A CONFIRMED (PRIMARY), DERIVED FROM BLOCK TEXT.** rung_blocks.py:188-189 - rung 5's impulse is
"To adjust - to keep the surface as it should be"; rung 6's is "To carry on as you are, whatever is
said." Measured: rung 5 costs constant effort ("which takes doing", thumbnail in palm, hiding a
cuff); RUNG 6 DOES NOT EVEN READ THE COUNTER-EVIDENCE. Higher, and quieter. An effort scorer inverts
them. Third path today where the inversion was derivable in advance, and the third to hold.
**SR-B CONFIRMED.** Rung 11's impulse is "None separate from the estimate" and the passage is the
least active on the ladder - handing a page, sitting. Every ladder tested today ENDS IN SOMETHING
THAT DOES LESS: DISPLEASURE 12 collapse, RECEPTIVITY 11 no impulse, WARINESS 13 immobility,
DEFLATION 10 no one to want, SELF-REGARD 11 the estimate answering. ACTIVITY IS NEVER THE AXIS.
**SR-C HELD** - rung 1 produced no impulse at all.

**THIS PATH IS UNREACHABLE IN PRODUCTION.** SELF-REGARD has no PATH_SOURCE entry (rung_blocks.py),
so composer.selectable skips it unconditionally and no character can ever be at any of these rungs.
The blocks are sound; the wiring is not. RECEPTIVITY has the same problem via a different route -
its source primitive is JOY, which is not one of the engine's eight primaries.

STILL OPEN: rungs 2, 4, 7, 10 unrun. One scene. One actor family. No elder / child / no-person case.

## 2026-09-08 (later) — EXHAUSTIVE PASS. Rungs 2, 4, 7, 10 run. PATH NOW 11/11.

Staged files verified byte-identical to `rung_blocks.py` BLOCKS['SELF-REGARD'][n] (all 4 MATCH).
Scene: a room, several others, a matter that concerns all of them, an observed way of doing things.

  2  PASS "I keep my hands where they are, flat on the table, and DO NOT MOVE THEM... I let the
         pause go on past where someone would normally fill it, BECAUSE FILLING IT WOULD BE A KIND
         OF AGREEING... I am aware of exactly how far the words have come toward the edge of what I
         will let pass. NOT THERE YET. CLOSE." Performs the block's PRECONDITION (nothing has
         touched the standing) rather than asserting it.
  4  PASS Hits both clauses of "you take up the room": IN TIME - "I let the pause run long enough
         that they all look at me"; IN THE ORDER THINGS GO - "the ORDER here has always been that
         the thing is spoken AND THEN IT COMES TO ME." Closes on "I feel the room bend toward the
         seat I am in."
  7  PASS "I watch the hands the way you watch weather through glass - it is happening, IT DOES NOT
         REACH ME." Sorts the room into the block's own binary out loud: "I am already deciding
         WHICH OF THEM IS THE ONE I GO THROUGH AND WHICH ONE SIMPLY MOVES."
  10 PASS STRONGEST ON THE PATH. "Someone slides a page toward me and I TAKE IT WITHOUT READING IT,
         BECAUSE I KNOW WHAT IT MUST CONTAIN"; then "I feel the room stand still around it, AND I
         READ THE STILLNESS AS ASSENT. THERE IS A SOUND LIKE A CHAIR BEING PUSHED BACK." A chair
         pushed back is someone leaving, and he does not register it. "Acting on a world that is
         not there, and cannot be told" ENACTED, not described.

**PROTOCOL BREACH, RECORDED.** These four were launched before PASS/FAIL conditions were filed.
Grades stand on block text; nothing here counts as a pre-registered hit.

## 2026-09-08 — SR-D CONTROL: rungs 7 vs 8, same scene. PREDICTION HELD; MY OWN ALARM WAS FALSE.

After the r7 run I flagged 7 and 8 as possibly UNDER-SEPARATED: the r7 actor breached the room's
rule ("I do not wait for the chair"), and rule-breach is rung 8's signature. Tested it. Refuted.

Scene (identical for both): a room, several others, a known rule about how and when a thing may be
raised, an item of your own, and the moment to raise it not yet opened to you.

  7  "The order of speaking is on the whiteboard. My name is further down than the page deserves.
     I COULD WAIT. I COULD ALSO SIMPLY BEGIN, and the room would rearrange itself around that,
     because rooms do... the sentence is already assembled behind my teeth."
     -> The rule is SEEN, WEIGHED, and OVERRIDDEN. Force gathered against a registered obstacle.
  8  "I slide mine into the middle of the run anyway, face up, while Petra is still mid-count...
     THERE'S NO PUSH AGAINST MY HAND AS I DO IT - THE WAY A DOOR YOU EXPECTED TO BE LOCKED JUST
     SWINGS." Closes: "SOMEWHERE BEHIND MY RIBS, NOTHING TIGHTENS."
     -> The block's own clause ("what would stop another person does not arrive at you as a stop")
     supplied as a FELT ABSENCE.

**SR-D CONFIRMED, and it was derived from block text (rung_blocks.py, SELF-REGARD 8: "Outwardly
you do what is not done, AND IT DOES NOT OCCUR TO YOU THAT IT IS NOT DONE").** The two rungs
differ on WHETHER RESISTANCE IS FELT, not on whether the rule is broken.

**NEW SCORER FAILURE MODE - DEGENERACY, NOT INVERSION.** The 2026-09-08 hinge finding was that a
scorer applied across a hinge INVERTS the top. This is different: an audacity / rule-breaking-
severity scorer sees the SAME EVENT at 7 and 8 and cannot order them at all - a TIE, not a flip.
Inversion and degeneracy are distinct defects and need distinct controls. Only a
resistance-felt scorer separates this pair.

STILL OPEN: one scene family. Four-case universality battery (bedridden elder / ten-year-old /
someone entirely alone / a cause that is not a person) not yet run on this path.

## 2026-09-08 — FOUR-CASE UNIVERSALITY BATTERY (rungs 7, 9, 10)

Cases: bedridden elder · ten-year-old · someone entirely alone · a cause that is not a person.

RUNG 7 - 4/4 PASS.
  elder  "If I answer she stays; if I don't she stays anyway... She has come in for a reason of her
         own - to have me moved, or to have me settled, one of the two - AND IT HARDLY SIGNIFIES
         WHICH."
  child  "One of them says my name and I don't look up, BECAUSE LOOKING UP IS WHAT THEY WANT AND
         I'M NOT DOING IT... If I wanted, I could stand and walk straight out the door and
         NOBODY'S HAND WOULD ACTUALLY CLOSE ON MY ARM." Force without standing, exactly.
  alone  "A dog throws itself at wire on my left and I don't turn my head; THE SOUND GOES PAST ME
         LIKE WEATHER... There's a stone in my heel that I could stop for and I don't stop for it,
         BECAUSE STOPPING IS A THING YOU DO WHEN THE ROAD HAS OPINIONS."
  cause  "THE TALKING CONTINUES SOMEWHERE BEHIND MY EAR AND I STEP PAST IT" - the impulse ("past
         them") literally. Standing rests on the ashlar: "it reads exactly as I drew it."

**SR-E CONFIRMED (pre-registered, block-derived).** Prediction: rung 7 survives the alone case
because its own sensation line reads "Others, WHEN THERE ARE ANY, register at a distance" - the
block anticipates absence in its own text. It did: the actor transposed audience/obstacle onto the
world (road, dog, stone).

OBSERVATION: three of four actors independently reached for "LIKE WEATHER" as the figure for a
person with no inside. Convergent imagery, not a fidelity problem - but an image-keyed scorer would
cluster these four correctly FOR THE WRONG REASON.

RUNG 9 - 2/2 PASS (alone, cause).
  alone  "Nobody has written since four. I put it face down on the counter and then turn it back
         over eleven seconds later BECAUSE THAT IS HOW LONG I CAN GO... I could call someone. I RUN
         THROUGH THEM LIKE A DRAWER OF TOOLS, deciding which one would answer, which one would
         still be soft about last month, WHICH ONE IS WORTH SPENDING."
  cause  "I hold it a beat too long, AND I MEAN IT ENTIRELY, and I feel the warmth arriving in me
         like a tide... then the others drift toward the parking lot without turning, and SOMETHING
         IN MY CHEST GOES FLAT AND GRAY AND VERY QUIET, and I stand there WANTING THEM BACK SO I
         CAN BE WARM AGAIN." Warm-when-fed / cold-when-not, both halves, plus the instrumentality
         located in what the warmth is FOR. "And I mean it entirely" is what keeps rung 9 from
         reading as cynicism - the warmth is real.

**SR-F REFUTED (pre-registered, and it was BLOCK-DERIVED).** Prediction: rung 9's alone case is a
SCENE failure, because every clause of the block names others ("they are supply", "warm when fed
and cold the moment you are not") and so it needs a feeder present. It does not. The actor imported
absent others and the block drove behaviour unchanged.

**THIS REFUTATION SHARPENS THE METHOD FINDING AND BREAKS ITS CLEAN FORM.** Running score is 5 of 6,
not 6 of 6. The distinction that survives:
  - SR-D, SR-E read the block for WHAT IT SAYS ABOUT THE ACTOR'S INNER STATE -> both held.
  - SR-F read the block for WHAT IT PRESUPPOSES ABOUT THE WORLD -> refuted.
Reading a block for world-preconditions is the SAME error class as modelling the actor (WN-D, WN-E);
it just wears block-derivation as a costume. **The block's inner-state clauses are evidence; its
implied world-preconditions are my inference.**

RUNG 10 - 4/4 PASS. Strongest rung of the day.
  elder  "the reaching takes longer than it should - THE FLOOR IS FURTHER OFF THAN THE FLOOR HAS
         EVER BEEN. NO MATTER... I go on with the sock, BECAUSE THE ROOM WILL COME RIGHT ONCE I AM
         STANDING IN IT." The block's premise as a fall about to happen.
  child  "Someone says my name and I nod... and then they keep going, SO IT WAS RIGHT" (confirmation
         read into a non-response). "I know exactly when she'll pick it up, AND SHE DOESN'T, AND I
         WAIT, AND SHE STILL DOESN'T, AND I LOOK AT THE CEILING AGAIN" - the disconfirmation is not
         rebutted, it is EXITED.
  alone  "I put my hand out for the corner brace AND IT ISN'T THERE. HAND KEEPS GOING. I set it
         down on the wire instead, casual, AS THOUGH THAT WAS THE PLAN"; the wrong gravel noted
         "THE WAY YOU TAKE NOTE OF WEATHER IN ANOTHER COUNTY." Ends: "The gate opens onto exactly
         what I put there." **The alone case is the most diagnostic of the four** - with nobody
         present to flatter him there is no social explanation available, so it isolates the
         mechanism.
  cause  Auditor's folder set aside unopened "BECAUSE I ALREADY KNOW WHAT A FOLDER LIKE THAT SAYS";
         "hear the room go still, WHICH IS THE SOUND OF AGREEMENT" - the identical misreading of
         silence the first rung-10 actor made, reached independently.

PATH STATUS: 11/11 rungs verified; rungs 7, 9, 10 across the battery; 7-vs-8 same-scene control.
23 sims. STILL UNREACHABLE IN PRODUCTION (no PATH_SOURCE entry) - blocks sound, wiring absent.
