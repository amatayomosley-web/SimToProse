"""code_families.py — the code DATA. One dict per module family; `codes.py` holds the contract.

SPLIT OUT ON 2026-09-02 because only this half grows. `codes.py` carries the rules — a raised code
must be registered, a registered code must be raised, the `<MODULE>_<WHAT_WENT_WRONG>` naming, and
the note recording why the one-module-per-gate pacing was relaxed — and those are fixed. The
entries below are 231 lines that gain one for every future refusal, and they took the file past
CLAUDE.md hard rule 6's 500-line bound the moment the taxonomy landed.

SPLIT, NOT SANDED. The alternative was deleting comments until the file fit, which is the same file
with less explanation in it, and it would have crossed again on the next code.

This is still ONE source of truth: `codes.py` imports these and merges them, and every consumer
reads `codes.CODES` / `codes.DESCRIPTIONS` exactly as before.

NAMING and the two-way rule live in `codes.py`. Read them there before adding an entry here.
"""

# ---- RECORD_* — the record contract: what a committed turn must BE (src/engine/records.py) ----
# The surface a malformed commit meets, and it had no handles at all until 2026-09-02. It stayed
# invisible because the conversion audit read `_require(cond, msg)` — a parameter as the sole
# argument — as an already-coded doorway, so this module reported as raising nothing. Several
# codes are shared across record types on purpose: a code names the CONDITION, and
# `RelationshipDelta.delta`, `WoundDelta.delta` and `TowardDelta.delta` fail the same way.
_RECORD = {
    "RECORD_ACTOR_EMPTY":                   "a turn commit names no actor, and a turn nobody took cannot be folded",
    "RECORD_AFFECT_MISSING_PRIMARIES":      "a commit's affect omits a primary, so a feeling would be recorded as absent rather than unrendered",
    "RECORD_AFFECT_UNKNOWN_KEYS":           "a commit's affect carries a key that is not a primary",
    "RECORD_AFFECT_VALUE_RANGE":            "a primary's value in a commit is outside [0,1]",
    "RECORD_AXIS_UNKNOWN":                  "a relationship delta names an axis outside trust/affinity/respect/debt",
    "RECORD_CHAR_ID_EMPTY":                 "a wound delta names no character",
    "RECORD_DELTA_RANGE":                   "a delta on any tier is not a number in [-1,1]",
    "RECORD_EVENT_CAUSED_AT_INVALID":       "an event's caused_at is not an int >= 0",
    "RECORD_EVENT_EFFECTIVE_AT_INVALID":    "an event's effective_at is not an int",
    "RECORD_EVENT_EFFECTIVE_AT_UNANCHORED": "an event sets effective_at with no caused_at to anchor it",
    "RECORD_EVENT_EFFECT_BEFORE_CAUSE":     "an event would take effect before it was caused",
    "RECORD_EVENT_PAYLOAD_TYPE":            "an event payload is not a dict",
    "RECORD_EVENT_TYPE_EMPTY":              "an event carries no type, so the fold has no branch to take",
    "RECORD_EVENT_VISIBILITY_UNKNOWN":      "an event's visibility is neither public nor private-to-actor",
    "RECORD_FIELD_TYPE":                    "a commit field is not the type the record contract declares",
    "RECORD_LIST_ITEM_TYPE":                "a commit's list carries an item of the wrong record type",
    "RECORD_ORDER_UNKNOWN":                 "a relationship delta's order is neither first nor second",
    "RECORD_PERCEIVER_EMPTY":               "a delta names no perceiver, so there is nobody whose regard moved",
    "RECORD_PRIMARY_UNKNOWN":               "a toward delta names something that is not an affective primitive",
    "RECORD_RUN_ID_EMPTY":                  "a turn commit names no run",
    "RECORD_SOURCE_TYPE":                   "a delta's source is not a string",
    "RECORD_TARGET_EMPTY":                  "a delta names no target, so there is nobody the regard is about",
    "RECORD_TURN_INVALID":                  "a turn commit's turn index is not an int >= 0",
    "RECORD_WOUND_ID_EMPTY":                "a wound delta names no wound, and one with no id can never be folded back",
    "RECORD_WOUND_KIND_UNKNOWN":            "a wound delta's kind is not one of the authored causes",
}
# ---- VAULT_* — the authoring contract for a book's .md notes (src/engine/vault.py) ----
# These are the first refusals any book author meets: the loader reads their files before anything
# else runs. Every one of them names a field a human wrote by hand, which is why they are also the
# codes the authoring blueprints cite in their "what happens if you leave this blank" column.
_VAULT = {
    "VAULT_CHARACTER_UNKNOWN":         "a character was asked for by name and the loaded book does not have them",
    "VAULT_ENGINE_BLOCK_INVALID_JSON":  "a note's ```json engine block is not parseable json",
    "VAULT_BELIEF_CONFIDENCE_RANGE":    "a Beliefs bullet's confidence is outside [0,1]",
    "VAULT_BELIEFS_SECTION_UNPARSED":   "'## Beliefs' has bullets and none match the authoring contract",
    "VAULT_BOOK_FOLDER_MISSING":        "the book folder does not exist",
    "VAULT_WORLD_NOTE_COUNT":           "a book needs exactly one type:world note",
    "VAULT_WORLD_NO_ENGINE_BLOCK":      "the world note carries no ```json engine block",
    "VAULT_CHARACTER_NO_ENGINE_BLOCK":  "a character note carries no ```json engine block",
    "VAULT_CHARACTER_BLOCK_INCOMPLETE": "a character engine block is missing a required top-level key",
    "VAULT_NO_CHARACTERS":              "a book has no character notes at all",
}

# ---- TAG_* — the actor's self-reported event tags (src/engine/consolidation.py) ----
# The hard half (ok=False) is what the drivers raise on. The soft half only flags: it narrows or
# reports, and a beat carrying only soft flags still moves state.
_TAG = {
    # hard — the beat is refused
    "TAG_TAGS_NOT_AN_OBJECT":            "something that is not a tag map reached the consolidator",
    "TAG_PERCEPTS_NOT_A_LIST":           "the percept set handed to the consolidator is not a list",
    "TAG_SKILLS_NOT_AN_OBJECT":          "the skill map handed to the consolidator is not a dict",
    "TAG_TYPE_UNKNOWN":                  "tags.type is not a CATALOG key",
    "TAG_DIMENSIONS_TYPE":               "tags.dimensions is present but is not a dict",
    "TAG_DIMENSION_VALUE_NOT_NUMERIC":   "a dimension's magnitude is not a number",
    "TAG_DIMENSION_VALUE_RANGE":         "a dimension's magnitude is outside [0,1]",
    "TAG_DURABILITY_MISSING":            "tags.durability is absent",
    "TAG_DURABILITY_INVALID":            "tags.durability is not one of {transient, durable}",
    "TAG_CONFIDENCE_NOT_NUMERIC":        "tags.confidence is present but is not a number",
    "TAG_CONFIDENCE_RANGE":              "tags.confidence is outside [0,1]",
    # soft — reported and narrowed, never fatal
    "TAG_TYPE_NOT_ACTOR_OFFERED":        "a CATALOG type an actor is never offered was self-reported",
    "TAG_DIMENSION_UNKNOWN":             "a dimension key outside the known vocabulary (dropped)",
    "TAG_TARGET_NOT_PERCEIVED":          "the tag names a subject absent from the PerceptSet",
    "TAG_DIMENSION_NOT_IN_APPRAISAL_MAP": "a primary-driver dimension the chosen type does not legitimize",
    "TAG_CAPABILITY_BELOW_REQ":          "the actor's skill is below the type's capability_req",
}

# ---- LEDGER_* / RECORD_* / DB_* — the append-only spine (ledger.py, records.py, db.py) ----
_SPINE = {
    "LEDGER_ARC_DIFF_REWRITE": "a second, DIFFERENT arc diff arrived for a (run, char, turn) that already has one",
    # LEDGER_ and not CLOCK_: the naming rule says the prefix names the module that OWNS the
    # refusal, not the one that detects it. `clock.py` detects the rewrite; the append-only
    # contract it violates is the ledger's.
    "LEDGER_TIME_DECL_REWRITE": "a second, DIFFERENT elapsed span arrived for a (run, turn) that already declares one",
}

# ---- DIRECTION_* — turning stored numbers into words (src/engine/direction.py) ----
_DIRECTION = {
    "DIRECTION_PACKET_NOT_AN_OBJECT":
        "something that is not a state packet reached the translation layer",
    "DIRECTION_AFFECT_MISSING_PRIMARY":
        "an affect packet omits a primary, so the actor would be told less is happening than the state says",
    "DIRECTION_VALUE_NOT_IN_UNIT_INTERVAL":
        "a value bound for a stage direction is not a number in [0,1] - usually prose in a numeric slot",
}

# ---- WORLD_* / TENSION_* / CLOCK_* — the world-appraisal chassis and its first register ----
# Built 2026-09-02 and converted the same day, because these five modules were written across a
# session spent on this very defect class and given bare prose messages anyway — the surface the
# taxonomy exists to convert, grown while converting it.
_WORLD_APPRAISAL = {
    "WORLD_INTERESTS_EMPTY":       "a register entry declares no standing interests, so nothing could ever move it",
    "WORLD_INTEREST_DIM_UNKNOWN":  "an interest names something outside the seven appraisal dimensions",
    "WORLD_INTEREST_WEIGHT_RANGE": "an interest weight is not in [0,1]",
    "WORLD_WATCHES_TYPE":          "a watch scope is not a dict of parties/locations",
    "WORLD_WATCHES_EMPTY":         "an entry watches neither a party nor a location, so nothing is ever in scope",
    "WORLD_WATCHES_FIELD_TYPE":    "watches.parties or watches.locations is not a list",
    "WORLD_WATCHES_MEMBER_EMPTY":  "a watch list carries a blank member, which can never match an actor, target or location",
    "WORLD_DIMENSIONS_TYPE":       "an event's dimensions is not a dict",
    "WORLD_DIMENSION_NOT_NUMERIC": "a dimension value is not a number (if it is a severity WORD, the parse seam was bypassed)",
    "WORLD_COOLING_UNKNOWN":       "a cooling rate is not one of the authored words",
    "WORLD_COOL_INPUT_NOT_NUMERIC": "a value or elapsed span handed to cooling is not a number",
}

_TENSION = {
    "TENSION_NOT_AN_OBJECT":      "a tension payload is not an object",
    "TENSION_ID_MISSING":         "a tension carries no id, so it cannot be heated, cited or resolved",
    "TENSION_TEMPERATURE_RANGE":  "a tension temperature is neither a severity word nor a number in [0,1]",
    "TENSION_TEMPERATURE_WORD_UNKNOWN": "an authored temperature word is off the severity ladder",
    "TENSION_COOLING_UNKNOWN":    "a tension names a cooling rate that does not exist",
    "TENSION_FACTIONS_TYPE":      "a tension's factions is not a list",
    "TENSION_DELTA_HEAT_TYPE":    "a heat delta's heat is not a number",
    "TENSION_FACTION_EMPTY":      "a tension's factions list carries a blank member",
    "TENSION_WORLD_FIELD_TYPE":   "world.tensions is not a list",
}

_CLOCK = {
    "CLOCK_ELAPSED_NOT_NUMERIC":  "a declared elapsed span is not a number",
    "CLOCK_ELAPSED_NOT_POSITIVE": "a declared elapsed span is <= 0 - nothing passing is the absence of a declaration",
}

# ---- EDL_* — the cutting room's record (src/engine/edl.py) ----
_EDL = {
    "EDL_RUN_UNKNOWN":            "a cut entry was appended for a run this database does not have — the foreign key would refuse it, and an uncoded constraint error is what routing this module set out to stop reporting",
    "EDL_KIND_UNKNOWN":           "an entry kind is not one of SCENE/SUMMARY/BREAK/NOTE",
    "EDL_PAYLOAD_TYPE":           "an entry payload is not a dict",
    "EDL_SCENE_NO_MISSING":       "a SCENE entry names no scene_no",
    "EDL_SCENE_NO_TYPE":          "a SCENE entry's scene_no is not an int",
    "EDL_TRIM_TYPE":              "a trim is neither FULL nor a list of event ids",
    "EDL_PLACEMENT_UNKNOWN":      "a placement is not chrono or flashback",
    "EDL_FLASHBACK_NO_ANCHOR":    "a flashback names no recall_event_id to anchor to",
    "EDL_SUMMARY_SPAN_SHAPE":     "a SUMMARY span is not [tick_a, tick_b]",
    "EDL_SUMMARY_SPAN_BACKWARDS": "a SUMMARY span runs backwards",
    "EDL_SUMMARY_BASIS_EMPTY":    "a SUMMARY carries no basis - a summary with no basis is invention",
    "EDL_BREAK_LEVEL_UNKNOWN":    "a BREAK level is not chapter or act",
    "EDL_NOTE_NO_RATIONALE":      "a NOTE carries no rationale, so it is not the room's memory",
    "EDL_ORD_COLLISION":          "a generation already holds this ord_no - revise by appending a new generation",
    "EDL_TRACES_NEEDS_ROWS":      "traces was handed scene numbers instead of scene rows, so membership cannot be checked",
}

# ---- NARRATION_* — the two axes (src/engine/narration_modes.py) ----
_NARRATION = {
    "NARRATION_POV_NOT_PRESENT":       "a POV-bound narrator was pointed at a run its POV never appeared in",
    "NARRATION_VOICE_UNKNOWN":     "a voice is not one of the four rendering instructions",
    "NARRATION_KNOWLEDGE_UNKNOWN": "a knowledge setting is not pov or omniscient",
}

# ---- ACQUISITION_* — what a character learns from a committed turn ----
_ACQUISITION_F = {
    "ACQUISITION_WITNESS_TRUST_INVALID": "a witness's trust value handed to witness_belief is not a number in [0,1], so no confidence, provenance, or claim-framing could be derived from it",
}

# ---- ARC_* — the slow trait tier (src/engine/arc.py) ----
_ARC_F = {
    "ARC_APPLY_INPUT_NOT_A_DICT":      "apply received a char or a diff that is not a dict, so no baseline change could be written",
    "ARC_ASSESS_TAGS_NOT_A_DICT":      "the event tags handed to arc.assess are not a dict, so no durability judgement can be made for the beat",
    "ARC_ELAPSED_NOT_NUMERIC":         "an elapsed span handed to arc.erode is not a number",
    "ARC_ERODE_CHAR_NOT_A_DICT":       "arc.erode received a char that is not a dict, so no temperament mean could be relaxed toward baseline",
    "ARC_RESILIENCE_INPUT_NOT_A_DICT": "derive_resilience received a char or a condition that is not a dict, so no resilience number can be derived for the beat",
}

# ---- BOOK_* — resolving which book a run belongs to (src/engine/books.py) ----
_BOOK_F = {
    "BOOK_FIXTURE_NOT_FOUND":          "no engine test fixture of that stem exists in this repo",
    "BOOK_DB_MISSING":                 "a reader was pointed at a chronicle that does not exist yet",
    "BOOK_DB_CROSS_BOOK":  "an explicit --db points at a chronicle outside the book being run, and the append-only log means a mistaken write could not be undone",
    "BOOK_NOT_FOUND":      "a book spec resolved to neither an existing directory nor a slug under the configured books root",
    "BOOK_ROOT_UNSET":     "a bare slug was given but SWE_BOOKS is unset, so there is no root to resolve it under",
    "BOOK_SLUG_AMBIGUOUS": "two or more folders under the books root share the same slug, so a bare slug cannot pick one",
    "BOOK_SPEC_EMPTY":     "resolve() was given no book spec at all — neither a path nor a slug — so there is nothing to look up",
}

# ---- COMPOUND_* — the emotion-recipe vocabulary (src/engine/compounds.py) ----
_COMPOUND_F = {
    "COMPOUND_BASELINE_NOT_AN_OBJECT": "a character's resting temperament baseline handed to blend is not an object, so there is nothing to fill the unsteered remainder with",
    "COMPOUND_INTENSITY_RANGE":        "a compose intensity is not a number in [0,1], so the recipe's weights cannot be scaled to a valid magnitude",
    "COMPOUND_NAME_UNKNOWN":           "a compound name is not one of the authored recipes in COMPOUNDS, so there is no recipe to turn into a coordinate",
    "COMPOUND_RECIPE_BLOCKED":         "a compound's recipe cites a primitive the emotion basis does not carry, so composing it would silently drop an ingredient",
    "COMPOUND_VECTOR_NOT_AN_OBJECT":   "a live affect vector handed to recognise is not an object, so no compound name can be matched against it",
}

# ---- CONNECTION_* — how invested a character is in the person a moment is about ----
_CONNECTION_F = {
    "CONNECTION_EDGE_AXIS_NOT_NUMERIC": "a relationship edge's affinity, trust, or respect value is not a number, so no investment-based amplification or slowed-forgetting multiplier can be computed from it",
}

# ---- DB_* — opening and migrating a chronicle (src/engine/db.py) ----
# ---- DECAY_* — the one relaxation law every tier obeys (src/engine/decay_law.py) ----
_DECAY_F = {
    "DECAY_INPUT_NOT_NUMERIC":      "relax was handed a value, rest, retention or elapsed that is not a number, so the law cannot be applied to it",
    "DECAY_ELAPSED_NEGATIVE":       "time was passed as negative, and a negative exponent AMPLIFIES the deviation from rest instead of shrinking it — a memory that gets sharper with age",
    "DECAY_RETENTION_OUT_OF_RANGE": "a retention outside [0,1] was supplied: above 1 the value diverges away from its rest point, below 0 it oscillates across it",
}

_DB_F = {
    "DB_PATH_INVALID":   "connect was given something that is not a filesystem path, so there is no database file to open or create",
    "DB_SCHEMA_TOO_NEW": "the database's on-disk schema version is newer than this engine understands, so opening it risks silently misreading rows a newer migration wrote",
    "DB_BUSY_TIMEOUT":    "another writer held the database past the busy timeout — a TIMEOUT, not a refusal: the same call succeeds unchanged once the lock clears, which is why it is not folded into any _EXISTS or ROLLED_BACK code",
    "DB_TRANSACTION_OPEN": "a write-once writer was handed a connection with uncommitted DML on it, where its pre-check would read a stale snapshot and its rollback would discard the caller's work",
}

# ---- DIRECTION_* ----
_DIRECTION_F = {
    "DIRECTION_LIST_PACKET_NOT_A_LIST": "a volatile list packet (goals or percepts) reached the translation layer as something other than a list, so none of its entries could be phrased",
}

# ---- FAULT_* — the fault miner over recorded validation flags (src/engine/faults.py) ----
_FAULT_F = {
    "FAULT_LEDGER_HANDLE_INVALID": "the engine-fault scanner was handed something that is not a Ledger, so there is no run of turns to read validation flags from",
    "FAULT_SCAN_RESULT_INVALID":   "the engine-fault report renderer was handed something other than a scan_run result, so there is no fault list or stats to print",
}

# ---- GATE_* — perception and recall: what a character can SEE and what surfaces (gate.py) ----
# Kept SEPARATE from the SCENE_ codes that guard the same objects one call up. A subagent review
# proposed merging them on the ground that scene.assemble is the only caller, so these could never
# fire — but tests/test_scene.py:291 and :295 call perception_scope and run_gate DIRECTLY to assert
# exactly these guards. A code's prefix names the module that OWNS the refusal, not one that
# happens to sit above it.
_GATE_F = {
    "GATE_CONDITION_NOT_AN_OBJECT":   "a character's condition (energy/allostatic_load) is not an object, so the perception or recall budget cannot be computed",
    "GATE_EVENT_MISSING_TEXT":        "the scene slice names no event text, so there is no core percept to anchor the PerceptSet on",
    "GATE_GOALS_NOT_A_LIST":          "a character's active-goals list is not a list, so goal-salience cannot rank the recall budget",
    "GATE_PERCEPTS_NOT_A_LIST":       "the PerceptSet handed in is not a list, so what was actually perceived cannot be read back",
    "GATE_SCENE_SLICE_NOT_AN_OBJECT": "the scene slice handed to perception is not an object, so nothing in it can be perceived",
    "GATE_SKILLS_NOT_AN_OBJECT":      "a character's skill map is not an object, so no perception/insight check has a value to test against",
    "GATE_TRIGGERS_NOT_A_LIST":       "the trigger list handed to the recall gate is not a list, so nothing in the vault could ever be matched",
    "GATE_VAULT_NOT_A_LIST":          "a character's belief vault is not a list, so the recall gate has nothing to match triggers against",
    "GATE_WORLD_NOT_AN_OBJECT":       "the book's world slice handed to perception is not an object, so no location, lexicon or entity in it can be read",
}

# ---- PROMPT_* — assembling the messages an actor receives (src/engine/prompt.py) ----
_PROMPT_F = {
    "PROMPT_EVENT_TEXT_EMPTY":  "the moment handed to the turn-message builder carries no event text, so the actor would be staged into a scene with nothing happening",
    "PROMPT_PACKET_INCOMPLETE": "the packet handed to the turn-message builder carries no stable half, no volatile half, or both, so there are no facts to stage into the reasoning contract",
}

# ---- SCENE_* — assembling the packet an actor is handed (src/engine/scene.py) ----
_SCENE_F = {
    "SCENE_AFFECT_NOT_AN_OBJECT":     "the affect state (the seven primaries) handed to assembly is not a dict",
    "SCENE_CFG_NOT_AN_OBJECT":        "a scene cfg being fingerprinted is neither a dict nor absent, so there is nothing pinnable to hash",
    "SCENE_CFG_NOT_SERIALIZABLE":     "a scene cfg contains something json.dumps cannot encode, so its fingerprint cannot be computed and nothing can be pinned",
    "SCENE_CHAR_NOT_AN_OBJECT":       "the character handed to scene assembly is not a dict, so no fixed/baseline/current layer can be read from it",
    "SCENE_CHAR_SECTION_MISSING":     "a character sheet omits fixed, baseline or current",
    "SCENE_CONDITION_NOT_AN_OBJECT":  "the condition state (energy, allostatic load, ...) handed to assembly is not a dict",
    "SCENE_SLICE_EVENT_MISSING":      "a scene slice carries no event dict, so the pipeline has nothing for the character to perceive this turn",
    "SCENE_SLICE_EVENT_TEXT_MISSING": "a scene slice's event carries no text, so there is nothing to extract triggers or percepts from",
    "SCENE_SLICE_NOT_AN_OBJECT":      "the scene slice handed to assembly is not a dict, so there is no ground truth for the pipeline to perceive from",
    "SCENE_SUBJECT_INPUTS_INVALID":   "the edges list or the group index handed to subject resolution is not the required shape, so no event subject or subject class can be resolved",
    "SCENE_WORLD_NOT_AN_OBJECT":      "the book's world slice handed to assembly (or here, to subject-group indexing) is not a dict, so no locations, people or lexicon can be read from it",
}

# ---- SEVERITY_* — the severity-word ladder (src/engine/severity.py) ----
_SEVERITY_F = {
    "SEVERITY_WORD_UNKNOWN": "an event-strength word is not one of the seven ladder rungs (faint..extreme), so no threshold that reads severity can price it",
}

# ---- WOUND_* — the durable injury tier (src/engine/wound.py) ----
_WOUND_F = {
    "WOUND_ELAPSED_NOT_NUMERIC":     "an elapsed span handed to wound.erode is not a number",
    "WOUND_INTENSITY_MISSING":       "a wound carries no `intensity`, so there is no prediction for a trial's error to compare against",
    "WOUND_NOT_A_DICT":              "something that is not a wound dict reached trial(), so there is no sheet to update",
    "WOUND_PERMANENCE_RANGE":        "a wound's authored permanence is not a number in [0,1], so no easing floor can be computed for it",
    "WOUND_TRIAL_INPUT_NOT_NUMERIC": "the observed dimension, the wound's intensity, or the resilience handed to a trial is not a number",
}
# ---- LEVER_* — the durable tier: wounds, and the movements folded onto them (levers.py) ----
_LEVERS = {
    "LEVER_CATALOG_NOT_A_LIST":            "the catalog handed to active_rows is neither a list of rows nor {'rows': [...]}, so no row in it can be checked or fired",
    "LEVER_CURRENT_MISSING_PRIMARIES":     "the current-state vector omits one or more of the bounded primaries, so the effective vector would be computed with a hole in it",
    "LEVER_CURRENT_NOT_A_DICT":            "the current-state vector handed to effective() is not a dict, so no primary on it can be read",
    "LEVER_EDGE_CLAUSE_UNKNOWN":           "a when.present_edge or when.target_edge clause names an axis outside trust/affinity/respect/debt (or its _at_most form)",
    "LEVER_MAGNITUDE_NOT_NUMERIC":         "a row's magnitude is not a number, so it cannot multiply or add against the current-state vector",
    "LEVER_MULTIPLIER_NEGATIVE":           "a row multiplies (op 'x') by a negative number instead of using op '+' to debuff, which would invert rather than suppress the primary",
    "LEVER_OP_UNKNOWN":                    "a row's op is neither 'x' (multiply) nor '+' (add), so the row cannot be folded into the vector",
    "LEVER_ROW_NOT_A_DICT":                "a catalog row (buff/debuff entry) is not a dict, so no field on it can be read",
    "LEVER_UNKNOWN":                       "a row names a lever outside the bounded PRIMARIES set the catalog is authored against",
    "LEVER_WHEN_EDGE_REQ_NOT_A_DICT":      "a row's when.present_edge or when.target_edge trigger is not a dict of axis clauses",
    "LEVER_WHEN_NOT_A_DICT":               "a row's when (trigger) clause is not a dict, so no condition on it can be checked",
    "LEVER_WHEN_PERCEPT_NOT_A_LIST":       "a row's when.percept trigger is not a list of words to match against the turn's text",
    "LEVER_WOUNDS_NOT_A_LIST":             "the wounds sheet handed to the delta replay is not a list, so no wound in it can be located and updated",
    "LEVER_WOUND_AUTHORED_INTENSITY_ZERO": "a wound's authored (baseline) intensity is zero or negative, so the now/authored scaling ratio has no defined value",
    "LEVER_WOUND_INTENSITY_NOT_NUMERIC":   "a wound linked to an active row carries a non-numeric intensity, so the row's magnitude cannot be scaled to how much of the wound remains",
}

# ---- CITATION_* — the wall between a claim and the record (src/engine/citation.py) ----
# These are the refusals `.claude/hooks/citation_gate.py` surfaces when it DENIES a write, so an
# operator meets them at the moment a claim is refused rather than while reading code.
_CITATION = {
    "CITATION_ARG_NOT_INT":            "a citation argument that a resolver requires as an integer (turn, event id, scene no, etc.) is not one",
    "CITATION_ARITY_MISMATCH":         "a citation carries the wrong number of colon-separated arguments for its namespace's resolver",
    "CITATION_CLAIM_MODE_UNKNOWN":     "a claim's mode is not one of the two the contract allows (cited/derived)",
    "CITATION_CLAIM_NOT_A_DICT":       "one claim inside an envelope's claims list is not an object",
    "CITATION_CLAIM_TOKENS_TYPE":      "a claim's cite (or from) field is present but is not a list of tokens",
    "CITATION_ENVELOPE_CLAIMS_TYPE":   "an envelope's claims field is present but is not a list",
    "CITATION_ENVELOPE_KIND_UNKNOWN":  "an envelope's kind is not one of the six the orchestrator vocabulary defines (ANSWER/VERDICT/DIAGNOSIS/PROPOSAL/REPORT/NOTICE)",
    "CITATION_ENVELOPE_NOT_A_DICT":    "something that is not an envelope object reached the grounding gate",
    "CITATION_ENVELOPE_UNKNOWNS_TYPE": "an envelope's unknowns field is present but is not a list",
    "CITATION_NAMESPACE_UNKNOWN":      "a citation names a namespace outside the resolver/unbacked/bible set the grounding contract recognizes",
    "CITATION_TOKEN_EMPTY":            "a citation token is not a string at all, or is blank/whitespace, so there is nothing to parse",
    "CITATION_TOKEN_SHAPE":            "a citation token does not match the '<kind>:<args>' shape the grounding contract requires",
}

# ---- BONDS_* — what one person's regard for another does over time (src/engine/bonds.py) ----
_BONDS = {
    "BONDS_ACT_NOT_A_DICT":            "something that is not an objective act (act_from_tags's output) reached a witness-facing function",
    "BONDS_DELTAS_NOT_A_DICT":         "an edge-delta payload handed to the edge fold is not a dict",
    "BONDS_DRIFT_ELAPSED_NOT_NUMERIC": "the elapsed span handed to relationship drift is not a number",
    "BONDS_EDGE_AXIS_UNKNOWN":         "a computed edge delta names an axis outside RELATIONSHIP_AXES, so applying it would write a field the fold never reads back",
    "BONDS_LOG_AXIS_UNKNOWN":          "a logged relationship movement names an axis the current RELATIONSHIP_AXES no longer recognizes, so the code and the persisted log disagree",
    "BONDS_MODEL_NOT_A_DICT":          "a witness's worth-menu model handed to observe() is not a dict, so relevance cannot be scored",
    "BONDS_RELATIONSHIPS_NOT_A_DICT":  "the character's relationships sheet handed to the edge rebuild is not a dict",
    "BONDS_SKILLS_INVALID":            "a character-sheet skills map handed to the witness check is neither a dict nor None",
}

# ---- TOWARD_* — the MICRO tier: what one specific person makes you feel (src/engine/toward.py) ----
_TOWARD = {
    "TAG_DIMENSION_VALUE_NOT_NUMERIC": "a dimension's magnitude is not a number",
    "TOWARD_CHAR_NOT_A_DICT":          "the character record handed to the micro-tier fold or decay is not a dict",
    "TOWARD_CONNECTION_NOT_NUMERIC":   "the connection weight handed to the micro-feeling update is not a number",
    "TOWARD_DIMS_NOT_A_DICT":          "the event's dimension map handed to the micro-feeling update is not a dict",
    "TOWARD_ELAPSED_NOT_NUMERIC":      "the elapsed span handed to micro-feeling decay is not a number",
}
# ---- PROFILE_* — the composition library the character-generator writes against (profiles.py) ----
# AUTHOR-FACING. Every one of these refuses something a person wrote by hand — a profile id that
# resolves to nothing, a diff field outside the schema, a magnitude past its cap — which is the same
# job the VAULT_ family does for the .md notes, and the reason those are cited by name in the
# authoring blueprints' "what happens if you leave this blank" column.
_PROFILE = {
    "PROFILE_BASELINE_DIFFS_NOT_A_DICT":         "a profile's baseline_diffs is not a dict, so no field diff can be read from it",
    "PROFILE_CATALOG_ROW_ADDITIVE_EXCEEDED":     "a catalog_row's additive magnitude exceeds the +-0.35 lever cap",
    "PROFILE_CATALOG_ROW_LEVER_UNKNOWN":         "a catalog_row names a lever outside the eight Panksepp primaries",
    "PROFILE_CATALOG_ROW_MAGNITUDE_NOT_NUMERIC": "a catalog_row's magnitude is not a number",
    "PROFILE_CATALOG_ROW_MULTIPLIER_EXCEEDED":   "a catalog_row's multiplicative magnitude exceeds the 2.5x lever cap",
    "PROFILE_CATALOG_ROW_NOT_A_DICT":            "a profile's catalog_row is not a dict",
    "PROFILE_CATALOG_ROW_OP_UNKNOWN":            "a catalog_row's op is neither the multiplicative nor additive operator",
    "PROFILE_DIFF_FIELD_UNKNOWN":                "a baseline diff names a field outside the engine's active baseline fields, so the diff would move nothing",
    "PROFILE_DIFF_MAGNITUDE_EXCEEDED":           "a baseline diff exceeds the +-0.35 stacked movement cap",
    "PROFILE_DIFF_VALUE_NOT_NUMERIC":            "a baseline diff's magnitude is not a number",
    "PROFILE_FIELD_PATH_UNKNOWN":                "a composed field name has no known nested engine path, so writing it would leave an authored-but-inert dead field",
    "PROFILE_ID_UNKNOWN":                        "a profile id was requested that the library does not contain",
    "PROFILE_MISSING_REQUIRED_KEY":              "a profile omits one of id/name/category/baseline_diffs, a field every consumer assumes is present",
    "PROFILE_NOT_A_DICT":                        "something that is not a profile dict reached the validator",
    "PROFILE_PICKS_NOT_A_LIST":                  "compose() was handed picks that are not a list or tuple",
    "PROFILE_PICK_MALFORMED":                    "a pick is not a dict or names no profile, so it cannot be looked up in the library",
    "PROFILE_PICK_WEIGHT_RANGE":                 "a pick's weight is outside [0.0, 1.0]",
    "PROFILE_PLACE_ARGS_NOT_DICTS":              "place() was handed a char or composed argument that is not a dict",
    "PROFILE_PRIOR_NOT_A_DICT":                  "compose() was handed a prior that is not a dict, so there is nothing to diff the picks against",
}

# ---- BIBLE_* — the pinned world contract a run is computed against (src/engine/bible.py) ----
# Also author-facing, and load-bearing for hard rule 1: a run PINS the bible it ran against so a
# mid-book edit cannot silently change what earlier turns were computed from. These refuse the
# bible that cannot be pinned in the first place.
_BIBLE = {
    "BIBLE_ACT_IMPOSSIBLE":            "the pinned world does not permit the act a scene was about to run",
    "BIBLE_CHARACTERS_NOT_A_DICT":   "the authored character map handed to the bible store is not a dict, so nothing about the cast can be fingerprinted or projected",
    "BIBLE_ENTITY_KIND_UNKNOWN":     "entity_exists was asked to filter by an entity kind outside the store's three (character/person/location), so the lookup has no such column to check",
    "BIBLE_LAWS_FIELD_NOT_A_LIST":   "the world's laws field is not a list, so no authored law can be read from it at all",
    "BIBLE_LAW_DOMAIN_UNKNOWN":      "a law's domain is not one of the eight authoring-blueprint domains (universal-law.md's A-E plus present-systems.md's three), so the law has nowhere in the taxonomy to live",
    "BIBLE_LAW_ENTRY_NOT_A_DICT":    "an entry in the authored laws list is not itself a dict, so it carries no fields a law could be built from",
    "BIBLE_LAW_EPISTEMIC_UNKNOWN":   "a law's epistemic status is not one of known-true/known-false/contested-unknowable, so the gate cannot decide whether the rule actually binds reality or only belief",
    "BIBLE_LAW_EXCEPTS_EMPTY":       "a PERMITS law's excepts field is present but names no law id, so the narrowing it was supposed to declare says nothing",
    "BIBLE_LAW_EXCEPTS_NOT_PERMITS": "a law declares an excepts list but its modality is not PERMITS, and excepts only narrows what a permit disarms — it means nothing on any other modality",
    "BIBLE_LAW_EXCEPTS_UNKNOWN_ID":  "a law's excepts names a law id that does not exist among the projected laws, so the permit's narrowing points at nothing it can actually disarm",
    "BIBLE_LAW_ID_DUPLICATE":        "two authored laws share the same id, so a citation naming that id would resolve ambiguously between two different rules",
    "BIBLE_LAW_ID_MISSING":          "a law is authored with no id, and an uncitable law can never be named as the reason a gate denied or permitted an act",
    "BIBLE_LAW_MODALITY_UNKNOWN":    "a law's modality is not one of IMPOSSIBLE/FORBIDS/REQUIRES/PERMITS, so the gate has no rule for how it should bind",
    "BIBLE_LAW_STATEMENT_MISSING":   "a law carries no statement, so a refusal citing it would have no rule to quote back to the author",
    "BIBLE_NOT_JSON_SERIALIZABLE":   "the authored world/characters cannot be turned into a stable byte form, so the bible has no fingerprint to pin a run against",
    "BIBLE_WORLD_NOT_A_DICT":        "the authored world handed to the bible store is not a dict, so nothing about it can be fingerprinted or projected",
    "BIBLE_WORLD_STEP1_INCOMPLETE":  "a strict build was requested on a world that has not answered universal-law.md's step 1 (switches, bounding laws, or epistemic status), so the build refuses rather than pin an incomplete premise",
}
# ---- STATE_* — the pricing engine every turn passes through twice (src/engine/state.py) ----
# `appraise` and `decay` check six conditions identically, so those six carry ONE code each rather
# than twelve: the two messages differed only by a function-name prefix, and a code names the
# CONDITION. STATE_DIM_TO_PRIMARY_UNKNOWN_PRIMITIVE is the odd one — it fires at import over this
# module's own table and can only trip from a developer editing state.py wrong. It stays a raise
# rather than becoming an assert, because `python -O` strips asserts and rule 6 says fail loud.
_STATE = {
    "STATE_AFFECT_NOT_A_DICT":            "the affect vector handed to the pricing engine is not a dict",
    "STATE_AFFECT_MISSING_PRIMARIES":     "the affect vector omits one or more primaries, so a feeling would be priced as absent rather than unrendered",
    "STATE_AFFECT_UNKNOWN_KEYS":          "the affect vector carries a key that is neither a primary nor an author comment",
    "STATE_AFFECT_VALUE_NOT_NUMERIC":     "a primary's value in the affect vector is not a number",
    "STATE_AFFECT_VALUE_RANGE":           "a primary's value in the affect vector is outside [0,1]",
    "STATE_TAGS_NOT_A_DICT":              "something that is not a tag map reached the appraisal step",
    "STATE_TAGS_DIMENSIONS_TYPE":         "tags.dimensions handed to the appraisal step is not a dict",
    "STATE_PROFILE_MISSING_KEY":          "the profile omits a key build_profile always produces",
    "STATE_PROFILE_MISSING_DECAY_RATES":  "the profile handed to decay carries no decay_rates",
    "STATE_TEMPERAMENT_NOT_A_DICT":       "the temperament map handed to decay is not a dict",
    "STATE_TEMPERAMENT_MISSING_PRIMARY":  "the temperament map omits one of the primaries, so that feeling would have no resting point to fall toward",
    "STATE_TEMPERAMENT_ENTRY_INVALID":    "a temperament entry is not a dict carrying a mean",
    "STATE_DIMENSION_MAGNITUDE_NOT_NUMERIC": "an event dimension's magnitude is not a number, on either the appraisal or the durable tier",
    "STATE_DIM_TO_PRIMARY_UNKNOWN_PRIMITIVE": "this module's own dimension table pushes a primitive PRIMARIES does not carry — a developer edit, never a book",
}

# ---- LEDGER_* — the spine: the run, the turn, the resume (src/engine/ledger.py) ----
# LEDGER_RESUME_DIVERGENCE is the most operator-facing refusal in the engine: it is what a person
# reads when a book will not reopen. It carried no handle a runbook could cite until 2026-09-02.
_LEDGER = {
    "LEDGER_CHARACTER_EXISTS":         "a character already in a run's cast was registered again; the table refuses UPDATE and DELETE, so a sheet is registered once",
    "LEDGER_RUN_EXISTS":               "a run id already in this database was created again — a run is minted once and continued with --resume",
    "LEDGER_SCENE_EXISTS":             "a scene number already recorded for a run was appended again — a scene boundary is written once, and re-cutting one is a NEW scene_no",
    "LEDGER_TURN_EXISTS":              "a turn already in the log was re-appended — the log is append-only, so a correction is a NEW turn at a NEW index",
    "LEDGER_RUN_ID_EMPTY":            "a run is created with no id, and the id scopes every read and write in the database",
    "LEDGER_RUN_CONFIG_INVALID":      "a run config is not a dict carrying at least catalog_version",
    "LEDGER_RUN_UNKNOWN":             "a run this database does not have was opened",
    "LEDGER_CHARACTER_SHEET_INVALID": "a character is registered with a fixed or baseline that is not a dict",
    "LEDGER_NOT_A_TURN_COMMIT":       "something that is not a TurnCommit was handed to append_turn",
    "LEDGER_RUN_NOT_ACTIVE":          "a turn is appended to a run that is no longer active",
    "LEDGER_ARC_DIFF_INVALID":        "an arc diff is not a dict",
    "LEDGER_ACQUISITION_INVALID":     "an acquisition belief is not a dict carrying a claim",
    "LEDGER_TURN_COMMIT_ROLLED_BACK": "a turn commit failed and the whole turn was rolled back",
    "LEDGER_RESUME_DIVERGENCE":       "snapshot-plus-tail replay disagrees with the from-zero fold, so the cache or the projection is corrupt and the run refuses to resume",
}

# ---- WORLD_EVENT_* / CLAIM_* — the two keeper-facing write gates (world_events.py, claims.py) ----
# These are the refusals a KEEPER meets, not a book author: they fire on a proposal an agent wrote,
# at the last boundary before the append-only log. That is why the value check below exists at all —
# a bad identity accepted here cannot be corrected afterwards, only lived with.
_WORLD_EVENT = {
    "WORLD_EVENT_TYPE_UNKNOWN":         "a proposed event type moves no snapshot field",
    "WORLD_EVENT_PAYLOAD_KEY_MISSING":  "a payload omits a key the fold reads, so the branch would not fire",
    "WORLD_EVENT_PAYLOAD_VALUE_EMPTY":  "a payload key the fold reads carries an empty string, which would write an identity nothing can name",
}

_CLAIM = {
    "CLAIM_TIER_UNKNOWN":  "an utterance is filed under something that is not one of the truth tiers",
    "CLAIM_SPEAKER_EMPTY": "an utterance names no speaker, and an unattributed quote is not evidence of anything",
    "CLAIM_SAID_EMPTY":    "an utterance carries no verbatim text, so there is nothing for a keeper to rule on",
    "CLAIM_UTTERANCE_NOT_AN_OBJECT": "something that is not an utterance was handed to the extractor",
    "CLAIM_EXTRACT_INCOMPLETE":      "an extract names no subject or no predicate, so it indexes nothing",
    "CLAIM_VERDICT_UNKNOWN":         "a resolution names a verdict that is not one of the truth tiers",
    "CLAIM_RESOLUTION_BACKDATED":    "a correction is dated before the verdict it corrects, so the fold would overrule it and it would take no effect",
}

# ---- READ_* — the orchestrator's typed read surface (src/engine/read_api.py) ----
# Small on purpose. This tier REFUSES only a malformed REQUEST; a miss is reported in the trace
# ("MISS: no persisted snapshot at turn 3; persisted turns: [0, 1]") and is a legitimate answer, not
# an error. The codes below are therefore all argument contracts, and there is deliberately no
# READ_NOT_FOUND — inventing one would turn every honest absence into a refusal.
# READ_RUN_UNKNOWN is not that code and is the line's one exception, argued in `_known_run`: the run
# is the aggregate every read is scoped BY, so an unknown one has no world for a fact to be absent
# from. `tests/test_errors.py` holds the family to an ALLOWLIST rather than a substring filter,
# because a synonym (READ_NO_SUCH_TURN, READ_EMPTY_RESULT) would walk straight past NOT_FOUND.
_READ = {
    "READ_AS_OF_NOT_AN_INT":   "an as_of turn index is not an int (a bool is not an int here either)",
    "READ_AS_OF_NEGATIVE":     "an as_of turn index is negative",
    "READ_TURN_NOT_AN_INT":    "a turn argument is not an int",
    "READ_PLACE_ID_EMPTY":     "a place_id is not a non-empty string",
    "READ_RUN_UNKNOWN":        "a read names a run this database does not have, which is the one absence that is a malformed question rather than a true answer",
}

# THE PACING RULE ABOVE WAS RELAXED ON 2026-09-02, deliberately and with the reason written down
# rather than quietly. It said the registry grows ONE MODULE AT A TIME and never ahead of the
# raises, and the batch-exception note below records what the one prior deviation cost: a raise
# shipped with its code embedded in prose, unregistered, and the gate's own measurement could not
# see it. That was true when NOTHING measured the result. Four guards now do, and none existed then:
#
#   * tests/test_errors.py:test_NO_ENGINE_MODULE_IS_HALF_CONVERTED — an AST audit that resolves the
#     `_require(cond, code, msg)` doorway, so a module with any coded raise and any prose one is RED
#   * the every-registered-code-is-raised scan over src/ and scripts/ (NOT tests/ — asserting a code
#     is not raising it), which catches the registry growing ahead of the raises
#   * `EngineError.__init__` refusing to construct an unregistered code at all
#   * the runtime choke point for a one-arg message opening with a code-shaped token — the exact
#     blindness the prior batch fell into
#
# The last four gates therefore converted four, then fifteen modules at a time. The rule's PREMISE
# changed; the rule is not being ignored.

# BATCH EXCEPTION, recorded because the rule above says this is not how it goes. The five families
# below `_DIRECTION` (WORLD, TENSION, CLOCK, EDL, NARRATION) landed in ONE gate on 2026-09-02, not
# one module at a time. The modules were same-day siblings and the alternative was leaving five
# fresh surfaces uncoded — but the deviation cost exactly what the pacing rule protects against: one
# raise slipped through the certified surface (`clock.py`'s rewrite refusal, code embedded in prose
# and unregistered) and the gate's own measurement did not see it. Read this gate as the exception,
# not the norm.
