"""code_families.py — the DATA half of the error registry.

Split from `codes.py` on 2026-09-04, the same split the sibling instance made and for
the same reason: the contract (is_registered, describe, the two-way rule) is stable and
small, while the families GROW with every migration. Keeping them together pushed
codes.py past the 500-line limit in hard rule 6 the moment 188 codes landed, and
`tests/test_portability.py` caught it.

Nothing here is logic. Add a code beside the raise that uses it, never in advance.
"""

_VAULT = {
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
}

# ---- DIRECTION_* — turning stored numbers into words (src/engine/direction.py) ----
_DIRECTION = {
    "DIRECTION_VALUE_NOT_IN_UNIT_INTERVAL":
        "a value bound for a stage direction is not a number in [0,1] - usually prose in a numeric slot",
}


# ---- MIGRATION 2026-09-04 ----
# The channel shipped 2026-08-30 with 11 sites coded and 190 left constructing prose,
# so `.code` was None almost everywhere and no failure could be grepped or branched on.
# These 188 codes were read back OUT of their raise sites by an AST walk AFTER the
# conversion, never written in advance — a registry that lists a code nothing raises is
# the documented-key-with-no-reader shape this whole channel exists to end.
#
# Deliberately ONE dict grouped by module, not one dict per module: the per-module
# names collided with the existing _VAULT and _DIRECTION families and silently replaced
# them, dropping their codes. Caught by the constructor refusing a code that had been
# registered ten minutes earlier.
_MIGRATED = {
    # --- acquisition.py ---
    "ACQUISITION_WITNESS_BELIEF_TRUST_NOT_NUMERIC":
        "witness_belief: trust must be a number in [0,1], got %r",
    # --- arc.py ---
    "ARC_APPLY_CHAR_DIFF_INVALID":
        "apply: char and diff must be dicts",
    "ARC_ASSESS_TAGS_NOT_A_DICT":
        "assess: tags must be a dict",
    "ARC_DERIVE_RESILIENCE_CHAR_CONDITION_INVALID":
        "derive_resilience: char and condition must be dicts",
    # --- bible.py ---
    "BIBLE_CHARACTERS_NOT_A_DICT":
        "characters must be a dict, got %s",
    "BIBLE_DUPLICATE_LAW_DUPLICATE":
        "duplicate law id %r",
    "BIBLE_EXCEPTS_CITE_UNKNOWN":
        "law %r: excepts cite unknown law ids %s",
    "BIBLE_EXCEPTS_NAME_INVALID":
        "law %r: excepts must name at least one law id",
    "BIBLE_EXCEPTS_ONLY_INVALID":
        "law %r: excepts is only meaningful on a PERMITS row",
    "BIBLE_ID_LAW_INVALID":
        "%s has no id — a law must be citable",
    "BIBLE_INVALID":
        "bible is not JSON-serialisable: %s",
    "BIBLE_LAW_DOMAIN_NOT_IN_SET":
        "law %r domain %r not in %s",
    "BIBLE_LAW_EPISTEMIC_NOT_IN_SET":
        "law %r epistemic %r not in %s",
    "BIBLE_LAW_MODALITY_NOT_IN_SET":
        "law %r modality %r not in %s",
    "BIBLE_LAW_STATEMENT_INVALID":
        "law %r has no statement — a denial must be able to quote the rule",
    "BIBLE_NOT_A_DICT":
        "%s must be a dict",
    "BIBLE_UNKNOWN":
        "unknown entity kind %r (known: %s)",
    "BIBLE_WORLD_ANSWERED_INVALID":
        "world has not answered step 1 (universal-law.md): %s",
    "BIBLE_WORLD_LAWS_NOT_A_LIST":
        "world 'laws' must be a list, got %s",
    "BIBLE_WORLD_NOT_A_DICT":
        "world must be a dict, got %s",
    # --- bonds.py ---
    "BONDS_APPLY_DELTAS_NOT_A_DICT":
        "apply_deltas: deltas must be a dict, got %r",
    "BONDS_APPLY_DELTAS_NOT_IN_SET":
        "apply_deltas: %r not in %s",
    "BONDS_APPLY_REFLECTION_DELTAS_NOT_A_DICT":
        "apply_reflection: deltas must be a dict, got %r",
    "BONDS_DRIFT_ELAPSED_NOT_NUMERIC":
        "drift: elapsed must be a number, got %r",
    "BONDS_OBSERVE_ACT_NOT_A_DICT":
        "observe: act must be a dict, got %r",
    "BONDS_OBSERVE_MODEL_NOT_A_DICT":
        "observe: model must be a dict, got %r",
    "BONDS_REFLECT_ACT_NOT_A_DICT":
        "reflect: act must be a dict, got %r",
    "BONDS_REPLAY_RELATIONSHIPS_NOT_A_DICT":
        "replay: relationships must be a dict, got %r",
    "BONDS_REPLAY_UNKNOWN_AXIS_UNKNOWN":
        "replay: unknown axis %r (log disagrees with RELATIONSHIP_AXES)",
    "BONDS_WITNESSED_ACT_NOT_A_DICT":
        "witnessed: act must be a dict, got %r",
    "BONDS_WITNESSED_SKILLS_NOT_A_DICT":
        "witnessed: skills must be a dict or None, got %r",
    # --- books.py ---
    "BOOKS_BOOK_GIVEN_INVALID":
        "no book given",
    "BOOKS_DB_DOES_INVALID":
        "db does not belong to this book — refusing to write across books. book: %s db: %s A book's chronic",
    "BOOKS_DIRECTORY_ON_INVALID":
        "no book %r: not a directory on disk, and %s is unset so a slug cannot be resolved. Pass a path, or",
    "BOOKS_DIRECTORY_UNDER_NOT_FOUND":
        "no book %r: not a directory, and not found under %s=%s (available: %s)",
    "BOOKS_FOLDERS_UNDER_INVALID":
        "ambiguous book %r: %d folders under %s=%s share that slug (%s). Rename one, or pass the full path.",
    # --- citation.py ---
    "CITATION_ARGS_MALFORMED":
        "citation %r is not '<kind>:<args>'",
    "CITATION_CLAIM_MODE_NOT_IN_SET":
        "claim[%d] mode %r not in %s",
    "CITATION_CLAIM_NOT_A_DICT":
        "claim[%d] must be a dict",
    "CITATION_CLAIM_NOT_A_LIST":
        "claim[%d] %r must be a list",
    "CITATION_EMPTY_NOT_A_STRING":
        "citation must be a non-empty string, got %r",
    "CITATION_ENVELOPE_CLAIMS_NOT_A_LIST":
        "envelope 'claims' must be a list",
    "CITATION_ENVELOPE_KIND_NOT_IN_SET":
        "envelope kind %r not in %s",
    "CITATION_ENVELOPE_NOT_A_DICT":
        "envelope must be a dict, got %r",
    "CITATION_ENVELOPE_UNKNOWNS_NOT_A_LIST":
        "envelope 'unknowns' must be a list",
    "CITATION_INTEGER_NOT_AN_INT":
        "citation expected an integer, got %r",
    "CITATION_TAKES_INVALID":
        "citation %r takes 1 argument, got %d",
    "CITATION_TAKES_WRONG_ARITY":
        "citation %r takes %d argument(s), got %d",
    "CITATION_UNKNOWN":
        "unknown citation namespace %r (known: %s)",
    # --- compounds.py ---
    "COMPOUNDS_BLEND_BASELINE_NOT_A_DICT":
        "blend: baseline must be a dict, got %r",
    "COMPOUNDS_COMPOSE_INTENSITY_NOT_NUMERIC":
        "compose: intensity must be a number in [0,1], got %r",
    "COMPOUNDS_COMPOSE_REQUIRES_PRIMITIVE_INVALID":
        "compose: %r requires primitive(s) %s which the basis does not carry. Either the recipe is wrong or",
    "COMPOUNDS_COMPOSE_UNKNOWN_COMPOUND_UNKNOWN":
        "compose: unknown compound %r (known: %s)",
    "COMPOUNDS_RECIPE_SUM_UNKNOWN_COMPOUND_UNKNOWN":
        "recipe_sum: unknown compound %r",
    "COMPOUNDS_RECOGNISE_VECTOR_NOT_A_DICT":
        "recognise: vector must be a dict, got %r",
    # --- consolidation.py ---
    "CONSOLIDATION_VALIDATE_TAGS_NOT_A_DICT":
        "validate_tags: tags must be a dict, got %r",
    "CONSOLIDATION_VALIDATE_TAGS_PERCEPTS_NOT_A_LIST":
        "validate_tags: percepts must be a list, got %r",
    "CONSOLIDATION_VALIDATE_TAGS_SKILLS_NOT_A_DICT":
        "validate_tags: skills must be a dict, got %r",
    # --- db.py ---
    "DB_PATH_NOT_A_PATH":
        "db_path must be a filesystem path, got %r",
    "DB_SCHEMA_VERSION_MISMATCH":
        "db schema is v%d but this engine knows v%d — refusing to open",
    # --- direction.py ---
    "DIRECTION_AFFECT_MISSING_PRIMARIES":
        "direction: affect missing primaries: %s",
    "DIRECTION_AFFECT_TEMPERAMENT_INVALID":
        "direction: affect and temperament must be dicts",
    "DIRECTION_CONDITION_NOT_A_DICT":
        "direction: condition must be a dict",
    "DIRECTION_EDGE_NOT_A_DICT":
        "direction: edge must be a dict",
    # --- faults.py ---
    "FAULTS_RENDER_RESULT_NOT_A_DICT":
        "render: result must be the dict scan_run returns",
    "FAULTS_SCAN_RUN_NOT_A_LEDGER":
        "scan_run: ledger must be a Ledger (got %r)",
    # --- gate.py ---
    "GATE_EXTRACT_TRIGGERS_PERCEPTS_NOT_A_LIST":
        "extract_triggers: percepts must be a list",
    "GATE_PERCEPTION_SCOPE_CONDITION_NOT_A_DICT":
        "perception_scope: condition must be a dict",
    "GATE_PERCEPTION_SCOPE_SCENE_SLICE_EVENT_NOT_A_DICT":
        "perception_scope: scene_slice.event must be a dict with 'text'",
    "GATE_PERCEPTION_SCOPE_SCENE_SLICE_NOT_A_DICT":
        "perception_scope: scene_slice must be a dict",
    "GATE_PERCEPTION_SCOPE_SKILLS_NOT_A_DICT":
        "perception_scope: skills must be a dict",
    "GATE_PERCEPTION_SCOPE_WORLD_NOT_A_DICT":
        "perception_scope: world must be a dict",
    "GATE_RUN_GATE_CONDITION_NOT_A_DICT":
        "run_gate: condition must be a dict",
    "GATE_RUN_GATE_GOALS_NOT_A_LIST":
        "run_gate: goals must be a list",
    "GATE_RUN_GATE_SKILLS_NOT_A_DICT":
        "run_gate: skills must be a dict",
    "GATE_RUN_GATE_TRIGGERS_NOT_A_LIST":
        "run_gate: triggers must be a list",
    "GATE_RUN_GATE_VAULT_NOT_A_LIST":
        "run_gate: vault must be a list",
    # --- identity_view.py ---
    "IDENTITY_VIEW_DIRECTION_GOALS_NOT_A_LIST":
        "direction: goals must be a list",
    "IDENTITY_VIEW_DIRECTION_OUTSIDE_WEIGHT_INVALID":
        "direction: %s is %r — outside [0,1], so it is not a weight this layer can band. It would reach the",
    "IDENTITY_VIEW_DIRECTION_PERCEPTS_NOT_A_LIST":
        "direction: percepts must be a list",
    "IDENTITY_VIEW_DIRECTION_STABLE_NOT_A_DICT":
        "direction: stable must be a dict",
    # --- ledger.py ---
    "LEDGER_ACQUISITION_BELIEF_NOT_A_DICT":
        "acquisition belief must be a dict carrying a claim",
    "LEDGER_APPEND_TURN_TAKES_INVALID":
        "append_turn takes a TurnCommit, got %r",
    "LEDGER_ARC_DIFF_NOT_A_DICT":
        "arc diff must be a dict",
    "LEDGER_FIXED_BASELINE_INVALID":
        "fixed and baseline must be dicts",
    "LEDGER_RUN_APPENDING_RUN_NOT_ACTIVE":
        "run %r is %s — appending to a non-active run",
    "LEDGER_RUN_CONFIG_NOT_A_DICT":
        "run config must be a dict carrying at least catalog_version (run-lifecycle.md)",
    "LEDGER_RUN_ID_EMPTY_NOT_A_STRING":
        "run_id must be a non-empty string",
    "LEDGER_SNAPSHOT_TAIL_RESUME_DIVERGENCE":
        "RESUME DIVERGENCE on run %r at turn %d: snapshot+tail replay != from-zero fold. The cached snapsho",
    "LEDGER_TURN_COMMIT_ROLLED_BACK":
        "turn-commit (run=%s turn=%s actor=%s) rolled back: %s",
    "LEDGER_UNKNOWN_RUN_UNKNOWN":
        "unknown run %r",
    # --- levers.py ---
    "LEVERS_CATALOG_NOT_A_LIST":
        "levers: catalog must be a list of rows or {'rows': [...]}, got %r",
    "LEVERS_EFFECTIVE_CURRENT_MISSING_PRIMARIES":
        "effective: current missing primaries: %s",
    "LEVERS_EFFECTIVE_CURRENT_NOT_A_DICT":
        "effective: current must be a dict, got %r",
    "LEVERS_EFFECTIVE_ROW_LEVER_INVALID":
        "effective: row %d lever %r is not one of the bounded levers %s (the catalog is a BOUNDED set, auth",
    "LEVERS_EFFECTIVE_ROW_MAGNITUDE_NOT_NUMERIC":
        "effective: row %d magnitude must be numeric, got %r",
    "LEVERS_EFFECTIVE_ROW_MULTIPLIER_NEGATIVE":
        "effective: row %d multiplier %r is negative; use op '+' to subtract",
    "LEVERS_EFFECTIVE_ROW_NOT_A_DICT":
        "effective: row %d must be a dict, got %r",
    "LEVERS_EFFECTIVE_ROW_OP_INVALID":
        "effective: row %d op %r must be one of %s",
    "LEVERS_UNKNOWN_EDGE_UNKNOWN":
        "levers: unknown edge clause %r (axes: %s, or <axis>_at_most)",
    "LEVERS_WHEN_ENTRY_NOT_A_DICT":
        "levers: when.%s must be a dict",
    "LEVERS_WHEN_NOT_A_DICT":
        "levers: `when` must be a dict, got %r",
    "LEVERS_WHEN_PERCEPT_NOT_A_LIST":
        "levers: when.percept must be a list of words",
    # --- profiles.py ---
    "PROFILES_AVAILABLE_UNKNOWN":
        "Unknown profile ID: %r (available: %s)",
    "PROFILES_BASELINE_DIFFS_CONTAINS_INVALID":
        "baseline_diffs contains unconsumed/invalid field: %r",
    "PROFILES_BASELINE_DIFFS_NOT_A_DICT":
        "baseline_diffs must be a dict",
    "PROFILES_CATALOG_ROW_ADDITIVE_INVALID":
        "catalog_row additive (%f) exceeds max 0.35",
    "PROFILES_CATALOG_ROW_LEVER_INVALID":
        "catalog_row lever must be one of %s, got %r",
    "PROFILES_CATALOG_ROW_MAGNITUDE_NOT_NUMERIC":
        "catalog_row magnitude must be numeric",
    "PROFILES_CATALOG_ROW_MULTIPLIER_INVALID":
        "catalog_row multiplier (%f) exceeds max 2.5",
    "PROFILES_CATALOG_ROW_NOT_A_DICT":
        "catalog_row must be a dict",
    "PROFILES_CATALOG_ROW_OP_INVALID":
        "catalog_row op must be 'x' or '+', got %r",
    "PROFILES_DIFF_F_INVALID":
        "diff for %r (%f) exceeds max magnitude +-0.35",
    "PROFILES_DIFF_NUMERIC_NOT_NUMERIC":
        "diff for %r must be numeric, got %r",
    "PROFILES_INVALID":
        "Malformed pick: %r",
    "PROFILES_MISSING":
        "Profile missing required key: %r",
    "PROFILES_PICKS_NOT_A_LIST":
        "picks must be a list or tuple",
    "PROFILES_PICK_WEIGHT_INVALID":
        "Pick weight must be in [0.0, 1.0], got %f",
    "PROFILES_PLACE_CHAR_COMPOSED_INVALID":
        "place: char and composed must both be dicts",
    "PROFILES_PRIOR_NOT_A_DICT":
        "prior must be a dict",
    "PROFILES_PROFILESPATH_FOR_ENGINE_PATH_INVALID":
        "profiles.path_for: no engine path for %r - a composed value with nowhere to go must fail loud, nev",
    "PROFILES_PROFILE_NOT_A_DICT":
        "Profile must be a dict, got %r",
    # --- prompt.py ---
    "PROMPT_BUILD_TURN_MESSAGES_EVENT_TEXT_EMPTY_NOT_A_STRING":
        "build_turn_messages: event_text must be a non-empty string",
    "PROMPT_BUILD_TURN_MESSAGES_PACKET_CARRY_INVALID":
        "build_turn_messages: packet must carry stable and volatile halves",
    # --- read_api.py ---
    "READ_API_AS_OF_INVALID":
        "as_of must be >= 0, got %d",
    "READ_API_AS_OF_NOT_AN_INT":
        "as_of must be an int turn index, got %r",
    "READ_API_SAID_TURN_NOT_AN_INT":
        "turn must be an int, got %r",
    "READ_API_SCENE_OF_TURN_NOT_AN_INT":
        "turn must be an int, got %r",
    # --- records.py ---
    "RECORDS_EVENT_CAUSED_AT_INVALID":
        "Event.caused_at must be int >= 0",
    "RECORDS_EVENT_EFFECTIVE_AT_BEFORE_CAUSED_AT":
        "Event.effective_at %s < caused_at %s",
    "RECORDS_EVENT_EFFECTIVE_AT_NOT_AN_INT":
        "Event.effective_at must be int",
    "RECORDS_EVENT_EFFECTIVE_AT_WITHOUT_CAUSED_AT":
        "Event.effective_at set without caused_at",
    "RECORDS_EVENT_PAYLOAD_NOT_A_DICT":
        "Event.payload must be a dict",
    "RECORDS_EVENT_TYPE_NOT_A_STRING":
        "Event.type must be a non-empty string",
    "RECORDS_EVENT_VISIBILITY_NOT_IN_SET":
        "Event.visibility %r not in %s",
    "RECORDS_MISSING_PRIMARIES":
        "TurnCommit.affect missing primaries: %s",
    "RECORDS_RELATIONSHIPDELTA_AXIS_NOT_IN_SET":
        "RelationshipDelta.axis %r not in %s",
    "RECORDS_RELATIONSHIPDELTA_DELTA_NOT_NUMERIC":
        "RelationshipDelta.delta must be a number in [-1, 1], got %r",
    "RECORDS_RELATIONSHIPDELTA_ORDER_INVALID":
        "RelationshipDelta.order must be 'first' or 'second', got %r",
    "RECORDS_RELATIONSHIPDELTA_PERCEIVER_EMPTY":
        "RelationshipDelta.perceiver must be non-empty",
    "RECORDS_RELATIONSHIPDELTA_TARGET_EMPTY":
        "RelationshipDelta.target must be non-empty",
    "RECORDS_TURNCOMMIT_ACTION_INVALID":
        "TurnCommit.action must be str",
    "RECORDS_TURNCOMMIT_ACTOR_EMPTY":
        "TurnCommit.actor must be non-empty",
    "RECORDS_TURNCOMMIT_AFFECT_NOT_A_DICT":
        "TurnCommit.affect must be dict",
    "RECORDS_TURNCOMMIT_AFFECT_VALUE_OUT_OF_RANGE":
        "TurnCommit.affect[%s] must be in [0, 1], got %r",
    "RECORDS_TURNCOMMIT_CONDITION_INVALID":
        "TurnCommit.condition must be dict",
    "RECORDS_TURNCOMMIT_EVENTS_INVALID":
        "TurnCommit.events items must be Event, got %r",
    "RECORDS_TURNCOMMIT_EVENTS_NOT_A_LIST":
        "TurnCommit.events must be a list",
    "RECORDS_TURNCOMMIT_MANIFEST_INVALID":
        "TurnCommit.manifest must be dict",
    "RECORDS_TURNCOMMIT_RECALL_NOT_A_LIST":
        "TurnCommit.recall must be a list of belief refs",
    "RECORDS_TURNCOMMIT_REL_DELTAS_INVALID":
        "TurnCommit.rel_deltas items must be RelationshipDelta",
    "RECORDS_TURNCOMMIT_REL_DELTAS_NOT_A_LIST":
        "TurnCommit.rel_deltas must be a list",
    "RECORDS_TURNCOMMIT_RUN_ID_EMPTY":
        "TurnCommit.run_id must be non-empty",
    "RECORDS_TURNCOMMIT_TAGS_INVALID":
        "TurnCommit.tags must be dict",
    "RECORDS_TURNCOMMIT_THOUGHT_INVALID":
        "TurnCommit.thought must be str",
    "RECORDS_TURNCOMMIT_TURN_INVALID":
        "TurnCommit.turn must be int >= 0",
    "RECORDS_UNKNOWN_KEYS":
        "TurnCommit.affect has unknown keys: %s",
    # --- scene.py ---
    "SCENE_ASSEMBLE_AFFECT_NOT_A_DICT":
        "assemble: affect must be a dict",
    "SCENE_ASSEMBLE_CHAR_MISSING_SECTION":
        "assemble: char missing section %r",
    "SCENE_ASSEMBLE_CHAR_NOT_A_DICT":
        "assemble: char must be a dict",
    "SCENE_ASSEMBLE_CONDITION_NOT_A_DICT":
        "assemble: condition must be a dict",
    "SCENE_ASSEMBLE_EVENT_NO_TEXT":
        "assemble: scene_slice.event must have 'text'",
    "SCENE_ASSEMBLE_SCENE_SLICE_NOT_A_DICT":
        "assemble: scene_slice must be a dict",
    "SCENE_ASSEMBLE_SCENE_SLICE_NO_EVENT":
        "assemble: scene_slice must have 'event' dict",
    "SCENE_ASSEMBLE_WORLD_NOT_A_DICT":
        "assemble: world must be a dict",
    "SCENE_RESOLVE_SUBJECT_EDGES_NOT_A_LIST":
        "resolve_subject: edges must be a list and groups_index a dict",
    "SCENE_SUBJECT_GROUPS_WORLD_NOT_A_DICT":
        "subject_groups: world must be a dict",
    # --- state.py ---
    "STATE_APPRAISE_AFFECT_MISSING_PRIMARIES":
        "appraise: affect missing primaries: %s",
    "STATE_APPRAISE_AFFECT_NOT_A_DICT":
        "appraise: affect must be a dict, got %r",
    "STATE_APPRAISE_AFFECT_NUMERIC_NOT_NUMERIC":
        "appraise: affect[%s] must be numeric, got %r",
    "STATE_APPRAISE_AFFECT_OUT_OF_RANGE":
        "appraise: affect[%s]=%r out of [0,1]",
    "STATE_APPRAISE_AFFECT_UNKNOWN_KEYS":
        "appraise: affect has unknown keys: %s",
    "STATE_APPRAISE_DIMENSION_MAGNITUDE_NOT_NUMERIC":
        "appraise: dimension %r magnitude must be numeric, got %r",
    "STATE_APPRAISE_PROFILE_MISSING_KEY":
        "appraise: profile missing key %r",
    "STATE_APPRAISE_TAGS_DIMENSIONS_NOT_A_DICT":
        "appraise: tags['dimensions'] must be a dict",
    "STATE_APPRAISE_TAGS_NOT_A_DICT":
        "appraise: tags must be a dict, got %r",
    "STATE_DECAY_AFFECT_MISSING_PRIMARIES":
        "decay: affect missing primaries: %s",
    "STATE_DECAY_AFFECT_NOT_A_DICT":
        "decay: affect must be a dict, got %r",
    "STATE_DECAY_AFFECT_NUMERIC_NOT_NUMERIC":
        "decay: affect[%s] must be numeric",
    "STATE_DECAY_AFFECT_OUT_OF_RANGE":
        "decay: affect[%s]=%r out of [0,1]",
    "STATE_DECAY_AFFECT_UNKNOWN_KEYS":
        "decay: affect has unknown keys: %s",
    "STATE_DECAY_PROFILE_NOT_A_DICT":
        "decay: profile must be a dict with 'decay_rates'",
    "STATE_DECAY_TEMPERAMENT_ENTRY_NOT_A_DICT":
        "decay: temperament[%r] must be a dict with 'mean'",
    "STATE_DECAY_TEMPERAMENT_MISSING_PRIMARY":
        "decay: temperament missing primary %r",
    "STATE_DECAY_TEMPERAMENT_NOT_A_DICT":
        "decay: temperament must be a dict",
    "STATE_DIM_TO_PRIMARY_PUSHES_INVALID":
        "_DIM_TO_PRIMARY[%r] pushes %r, which is not a primitive. Add it to PRIMARIES or remove the push - ",
    # --- targets.py ---
    "TARGETS_RETARGET_TAGS_DIMENSIONS_NOT_A_DICT":
        "retarget: tags['dimensions'] must be a dict",
    "TARGETS_RETARGET_TAGS_NOT_A_DICT":
        "retarget: tags must be a dict, got %r",
}



# ---- DECAY_* — the one relaxation law (src/engine/decay_law.py) ----
_DECAY = {
    "DECAY_INPUT_NOT_NUMERIC":
        "relax: value, rest, retention and elapsed must all be numbers",
    "DECAY_ELAPSED_NEGATIVE":
        "relax: elapsed must be >= 0 - a negative exponent AMPLIFIES the deviation",
    "DECAY_RETENTION_OUT_OF_RANGE":
        "relax: retention must be in [0,1] - outside it the deviation grows or alternates sign",
}
