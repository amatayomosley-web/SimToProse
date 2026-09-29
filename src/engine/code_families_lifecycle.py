"""code_families_lifecycle.py — the code DATA for a book's life after adoption: drafts, the lineage log, the lease.

A SECOND DATA FILE, split, not sanded (`code_families.py`'s own rule): that file reached 791 of CLAUDE.md hard rule 6's
800 total lines with the record-role codes, and the draft flow (gate draft-flow, 2026-09-27) is the first of several
gates that add families about what happens to a book once it has a record - drafts and approval here, the author's
declarations and a struck beat after it. `codes.py` imports these and merges them with the rest: still ONE registry,
read through `codes.CODES` / `codes.DESCRIPTIONS`. NAMING and the two-way rule live in `codes.py`.
"""

# ---- DRAFT_* — the approval flow (src/engine/drafts.py, scripts/draft.py) ----
_DRAFT_F = {
    "DRAFT_BOOK_NOT_ADOPTED": "a draft flow met a book whose database is not its record (never adopted, or missing), so there is no approved state to copy a draft from or land one on - `draft.py adopt` first",
    "DRAFT_NOT_FOUND":       "no open draft there - never opened, already promoted, set aside or left stale (the refusal names which), or, once a book is adopted, a writer's database that is not a draft in its runs/drafts at all",
    "DRAFT_NOT_OURS":        "a file in runs/drafts is not the draft the lineage opened under that id - no open entry, a role row with another id or parent, or no database at all - so it could be a forged file, which must not be written or promoted (gate record-role review 3); `draft.py reject` sets it aside",
    "DRAFT_IN_USE":          "a database is still open somewhere - an SQLite connection whose -wal or -shm outlives a close of our own, or another program's handle that refuses a move - so promoting, adopting or moving it would lose what that run writes next",
    "DRAFT_NOT_EXTENDING":   "a draft does not hold every run and turn of the record it names as its parent, which a real draft always does (it began as a copy, and the log is append-only) - another book's draft copied in, most likely",
    "DRAFT_RECORD_MISSING":  "the record the lineage adopted is not where the lineage names it, or is no longer a record - or a book to adopt has no database yet (adopt --new starts one empty); adopting again would abandon every approved state",
    "DRAFT_BOOK_ADOPTED":    "adopt was asked of a book the lineage already adopted; a book is adopted once",
    "DRAFT_NOT_A_BOOK":      "a draft flow was given a folder with no world/ in it (books._book_dirs' marker of a book), and writes nothing into one - not even its lease",
    "DRAFT_APPROVAL_MISSING": "a promote or restore was asked for without the owner's words - none, no letter or digit in them, or a <placeholder>; the record changes only on a yes, recorded exactly as given",
    "DRAFT_APPROVER_UNKNOWN": "who gave the yes was not `owner` or `partner-relayed`; a relayed yes is recorded as relayed, never as the owner's own",
    "DRAFT_HEAD_UNKNOWN":    "a restore named a state the lineage never kept a history copy of",
    "DRAFT_HEAD_CURRENT":    "a restore named the state the record is already in",
    "DRAFT_HISTORY_CHANGED": "the history copy of a state is missing, carries another state, or its bytes no longer match the digest the lineage logged when it was kept - something wrote it since",
}

# ---- LINEAGE_* — the book's lineage log and lease (src/engine/lineage.py) ----
_LINEAGE_F = {
    "LINEAGE_UNREADABLE":  "a line of the book's runs/lineage.jsonl is not a lineage entry (not JSON, not an object, an unknown op, or a field its op needs is missing); it is refused, never skipped, since a skipped line is a promote or restore the checks would miss",
    "LINEAGE_OP_UNKNOWN":  "an entry was appended under an op the lineage does not know",
    "LINEAGE_LEASE_HELD":  "another process holds the book's lease - another flow is running on this book; the operating system frees it when that process ends",
}

# ---- DECLARE_* — the author's hand: a file of the owner's declarations (scripts/declare.py) ----
_DECLARE_F = {
    "DECLARE_FILE_UNREADABLE": "a declaration file is not there, not JSON, or not a list of entries - nothing of it is written",
    "DECLARE_ENTRY_MALFORMED": "a declaration entry is not an object, names no kind or one this version does not declare (event, correction, fact), lacks a field its kind needs, carries one of the wrong type, or carries a field nothing reads (a declaration never picks its own turn or source) - nothing of the file is written",
    "DECLARE_WORDS_MISSING":   "a declaration entry carries no owner's words (`words`: none, no letter or digit, or a <placeholder>) - the author's hand is recorded exactly as the owner gave it, or not at all",
    "DECLARE_RUN_UNKNOWN":     "a declaration named a run the chronicle does not hold, or a chronicle that does not exist - a declaration lands in a run that was played, and creates no database",
    "DECLARE_RUN_EMPTY":       "a declaration named a run with no committed turn yet - there is no moment for it to land at; what is true before the first beat belongs in the book's notes, which the run pins",
    "DECLARE_TURN_UNKNOWN":    "a correction named a turn the run never recorded",
    "DECLARE_NAME_UNKNOWN":    "an event names someone the run does not know - its actor, target, a reveal's knowers or a tension's watched parties must be of the run's cast or a person its pinned bible names; the fold would take the name as given and grow a phantom",
    "DECLARE_PLACE_UNKNOWN":   "an event names a place the run's pinned bible does not - a move's destination, an event's location or a tension's watched place; the world moves people only to places it names",
    "DECLARE_ENTRY_REFUSED":   "a writer's own gates refused a declared entry when the whole file was rehearsed on a scratch copy of the database (the keeper's for an event, the claims' for a fact, the critic's for a correction), or kept only part of it - the reason carries that writer's code, and nothing of the file is written",
    "DECLARE_ALREADY_DECLARED": "this exact file (by its sha256) was declared into this run before, and the database already holds every row it wrote - running it again would double them",
    "DECLARE_DRAFT_STALE":     "a declaration was aimed at a draft taken from a state the record has since left - a stale take, whose promote would be refused; open a new draft",
    # ---- HANDOFF_* — the partner's direction to the showrunner (src/engine/handoff.py, scripts/brief.py) ----
    "HANDOFF_DIRECTION_UNREADABLE": "a direction is not there, not JSON, or not one JSON object - nothing is spawned",
    "HANDOFF_KIND_UNKNOWN":    "a direction names a kind of work with no playbook (scene, render, declare, adopt, approve, reject, rewind, release)",
    "HANDOFF_FIELD_MISSING":   "a direction lacks a field its kind needs - the book always, and e.g. the draft and the author's words for an approval",
    "HANDOFF_WORDS_MISSING":   "a direction's `words` are blank, punctuation, or a <placeholder> - they must be the author's own words, verbatim",
    "HANDOFF_FIELD_UNKNOWN":   "a direction carries a field nothing reads - refused, so an instruction is never silently dropped",
    "HANDOFF_NEEDS_SPAWN":     "brief.py --run was asked for work that needs judgment and a specialist (a scene, a render) - pass the brief to the showrunner or the narrator instead",
    "ASK_NO_CHRONICLE":        "an info request (scripts/ask.py) named a book or draft with no chronicle yet - there is nothing to read, and none is created",
    # ---- ROLES_* — the session profile: which model fills each role (src/engine/roles.py, scripts/profile.py) ----
    "ROLES_PROFILE_UNREADABLE":      "a session profile is not there, not JSON, not {\"profile\": 1, \"roles\": {...}}, or a --set is not ROLE=MODEL - scripts/profile.py writes one",
    "ROLES_UNKNOWN":    "a profile names a role the table (src/engine/roles.py ROLES) does not have - refused, so a choice is never silently dropped",
    "ROLES_CLAUDE_ONLY":     "an agent role was given something other than a Claude tier - an agent drives Claude Code's tools, which a local or other model cannot",
    "ROLES_BELOW_FLOOR":     "a role with a HARD floor was given a model below it - the showrunner needs at least Mid to hold its playbook, commands and report over many steps",
    "ROLES_MODEL_UNKNOWN":   "a profile names a model the table cannot place (not ollama/..., subagent:<tier>, or a known OpenRouter id) - write its class after an @, so no model is ranked by a guess",
    # ---- the author's hand as other writers meet it ----
    "CLAIM_SPEAKER_RESERVED":  "a claim was recorded as spoken by `author` under a tier other than authored - that name speaks only the owner's own facts (scripts/declare.py), so any other claim under it would read as the owner's hand",
    "KEEPER_RULING_AUTHORED":  "a keeper's ruling named an authored fact - the owner's own fact binds as written and is ruled by nobody",
}

# ---- KNOWLEDGE_* — what a group or place knows, linked to each member (src/engine/knowledge.py, gate knowledge-links) ----
_KNOWLEDGE_F = {
    "KNOWLEDGE_NOT_A_LIST":            "world.knowledge is not a list of facts",
    "KNOWLEDGE_ENTRY_NOT_A_DICT":      "a world.knowledge entry is not an object with a claim and its holders",
    "KNOWLEDGE_CLAIM_EMPTY":           "a world.knowledge entry has no claim - there is nothing to know",
    "KNOWLEDGE_HELD_BY_EMPTY":         "a world.knowledge entry names no holder - a fact nobody holds is the author's truth, not knowledge",
    "KNOWLEDGE_HOLDER_UNREGISTERED":   "a fact's holder is not a registered group or place (grp.<a people[].groups tag> or loc.<a locations id>)",
    "KNOWLEDGE_ABOUT_UNREGISTERED":    "a fact is about a name the world does not register - register the person, place or group with the fact",
    "KNOWLEDGE_TOPIC_UNKNOWN":         "a fact's topic is not one of the lexicon's attribute classes - the domain is the world's own vocabulary",
    "KNOWLEDGE_AGE_NOT_A_SPAN":        "an age (a fact's `since`, a membership's `left`) is not <n>d, <n>w or <n>y, or is not more than nothing",
    "KNOWLEDGE_CONFIDENCE_RANGE":      "a fact's confidence is not a number in (0, 1]",
    "KNOWLEDGE_MEMBERSHIPS_NOT_A_LIST": "current.memberships is not a list",
    "KNOWLEDGE_MEMBERSHIP_NOT_A_DICT": "a current.memberships entry is not an object with `of`",
    "KNOWLEDGE_MEMBERSHIP_UNREGISTERED": "a membership names a group or place the world does not register - a member of nothing knows nothing by it",
    "KNOWLEDGE_FAMILIARITY_UNKNOWN":   "a membership's familiarity is not everyday, familiar or faded",
    "KNOWLEDGE_NORM_INVALID":          "a knowledge entry's `norm` is not true/false, or its `sanction` is not words or stands on a plain fact",
    "KNOWLEDGE_SAME_AS_INVALID":       "an identity (`same_as`) does not list two or more ids of the world's people - each name a person goes by is a people[] entry of its own",
}
