"""contracts_sheet.py — the character sheet, declared once: every field, its shape, and where it stands.

The table the checker (`contracts.check`) walks a sheet against, the rows BLUEPRINT-character carries between its
GENERATED markers (`scripts/gen_contracts.py`), and what refuses a sheet at a run's start (`contracts.require_at_start`,
gate run-start-refusal) (gate sheet-contract, 2026-09-25). Built from an inventory of every path the engine and its drivers read from a
sheet (file:line per path) and from the paths the owner's books and the fixtures actually carry. A field the
blueprint names and nothing reads is declared `unread`, so a sheet is told it reaches nothing; a field an engine
module already validates is handed to that module (`check`), so there is one rule per thing.

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

from .contracts import Field as F
from .records import RecordError


def _wound(row, sheet, ctx):
    """A wound row is engine state: the wound module's own check, and a source a run or a profile minted it from."""
    from . import wound
    if isinstance(row, dict) and row and all(str(k).startswith("_") for k in row):
        return None                                        # an author's _note row
    _numbers(row)
    if "wounds" not in ctx.get("systems", ("wounds",)):
        # WOUNDS OFF: the run empties this list before a reader, but a resume's fold reads each dict row first
        # (passage.fold_wounds -> wound.erode: its intensity and its permanence) - _numbers above; the rest is the wound
        # module's, and it is off
        return None
    wound._check(row)
    src = str(row.get("source", ""))
    if not (src.startswith("profile:") or src.startswith("run:")):
        raise RecordError("CONTRACT_WOUND_SOURCE", "source %r must be profile:<id> or run:<turn> - a wound is minted, "
                          "never hand-written" % src)


def _numbers(row):
    """The numbers the wound fold reads off a row, wherever the book runs wounds or not: an intensity and a permanence
    (wound.erode -> _floor_of: float(permanence)) - wound._check reads neither the permanence nor, with wounds off, the
    intensity, and a word in either raises at a beat or a resume, after the run row is written."""
    for key in ("intensity", "permanence"):
        v = row.get(key) if isinstance(row, dict) else None
        if isinstance(row, dict) and key in row and (isinstance(v, bool) or not isinstance(v, (int, float))):
            raise RecordError("CONTRACT_FIELD_TYPE", "a wound's %s must be a number - the wound fold reads it; got %r"
                              % (key, v))


def _catalog(cat, sheet, ctx):
    """The tier-3 rows: the lever module's own check per row, and a row naming a wound must name one this sheet has."""
    from .levers import _check_row
    if not isinstance(cat, (dict, list)) or (isinstance(cat, dict) and not isinstance(cat.get("rows") or [], list)):
        raise RecordError("CONTRACT_FIELD_TYPE", "must be a list of rows, or {rows: [...]} - levers.active_rows reads it "
                          "at every beat and refuses anything else; got %r" % (cat,))
    rows = (cat.get("rows") if isinstance(cat, dict) else cat) or []
    wounds = (sheet.get("baseline") or {}).get("wounds")
    have = {str(w.get("id")) for w in (wounds if isinstance(wounds, list) else []) if isinstance(w, dict)}
    wounds_on = "wounds" in ctx.get("systems", ("wounds",))   # off, the run empties every sheet's wounds alike
    for i, row in enumerate(rows if isinstance(rows, list) else []):
        _check_row(row, i)
        named = str((row or {}).get("wound", "") or "").strip() if isinstance(row, dict) else ""
        if named and wounds_on and named not in have:
            raise RecordError("CONTRACT_CATALOG_WOUND_UNKNOWN", "row %d names wound %r, which baseline.wounds does not "
                              "carry - it would fire at full magnitude whatever happens to that wound" % (i, named))


def _attachments(block, sheet, ctx):
    from . import attachments
    attachments.validate_block(block, registered=ctx.get("registered"))


def _rates(update, sheet, ctx):
    from . import bonds
    bonds.rates_of({"update": update})


def _body(block, sheet, ctx):
    from . import body
    body.capacity(sheet)


def _injuries(rows, sheet, ctx):
    from . import injuries
    injuries.require(sheet)


def _condition(cond, sheet, ctx):
    """Both or neither: the readers assume different values for whichever of energy / allostatic_load is missing."""
    if isinstance(cond, dict) and ("energy" in cond) != ("allostatic_load" in cond):
        return ("carries only one of energy / allostatic_load - the readers assume different values for the missing "
                "one (memory budget, stage line, arc, catalog)")
    return None


def _belief(b, sheet, ctx):
    if not (isinstance(b, dict) and str(b.get("claim", "")).strip()):
        return "has no claim"
    if "provenance" not in b:
        return "has no provenance (seed/authored/lived/witnessed/learned)"
    return None


_MOVED = "the path that took its place ({successor}); the owner ruled replaced, not translated"
SHEET = (
    # ---- the three sections ------------------------------------------------------------------------------------
    F("fixed", "section", required="always", doc="who they are: identity the actor is told"),
    F("baseline", "section", required="always", doc="how they are made: temperament, values, voice, skills"),
    F("current", "section", required="always", doc="how they are on page one: mood, bonds, condition"),
    # ---- fixed -------------------------------------------------------------------------------------------------
    F("fixed.id", "text", reader="scene._build_stable", doc="their id, told to the actor; the file's id is the join",
      absent="missing - the actor's persona id reads null (a character-level `id` outside `fixed` does not fill it)"),
    F("fixed.name", "text", required="always", reader="scene._build_stable", doc="the name a reader would call them"),
    F("fixed.people", "text", reader="scene._build_stable", doc="their people, told to the actor",
      absent="missing - the actor's persona people reads null"),
    F("fixed.position", "prose", reader="scene._build_stable", doc="place, class, era, niche - told to the actor verbatim",
      absent="EMPTY - the actor receives no place, class or station at all"),
    F("fixed.genotype", "map", reader="heritable.entry", doc="how hard a feeling lands and how long it stays, per path"),
    F("fixed.genotype.<PATH>", "map", reader="heritable.entry"),
    F("fixed.genotype.<PATH>.hit", "word|number", vocab="heritable.GAIN", reader="heritable.entry",
      doc="how hard it lands (a number is clamped)"),
    F("fixed.genotype.<PATH>.hold", "word|number", vocab="heritable.PERSIST", reader="heritable.entry",
      doc="how long it stays (a number is clamped)"),
    F("fixed.genotype.<PATH>.rest", "any", status="retired", policy="move",
      replaced_by="baseline.temperament.<PATH>.rest - where they rest is a design choice, beside the voice"),
    F("fixed.genotype.<OLD_AXIS>", "any", status="retired", policy="refuse",
      replaced_by="one {hit, hold} cell per path (heritable refuses the old axes: GENOTYPE_OLD_AXES)"),
    F("fixed.role_tier", "any", status="unread", doc="nothing reads how big a part they play"),
    F("fixed.physical", "any", status="unread"),
    F("fixed.voice", "any", status="unread", doc="the voice the actor reads is baseline.voice"),
    F("fixed.formative", "any", status="unread"),
    # ---- baseline: temperament and traits ----------------------------------------------------------------------
    F("baseline.temperament", "map", reader="heritable", doc="where each path rests"),
    F("baseline.temperament.<PATH>", "map", reader="heritable"),
    F("baseline.temperament.<PATH>.rest", "word|unit", vocab="heritable.REST_WORDS", reader="heritable.ensure_temperament",
      doc="where the path rests - a word, or a number in [0,1]"),
    F("baseline.temperament.<PATH>.mean", "unit", status="runtime", reader="state.decay",
      doc="the resting mean, seeded from the rest word; the arc moves it"),
    F("baseline.temperament.<PATH>.variability", "any", status="retired", policy="prune",
      replaced_by="nothing - cut on the owner's \"cut what doesn't align\" (heritable); read by nothing"),
    F("baseline.temperament.<PRIMITIVE>", "any", status="retired", policy="refuse", replaced_by=_MOVED),
    F("baseline.traits", "map", reader="identity_view.direct_identity", doc="personality facets"),
    F("baseline.traits.<name>", "map", reader="identity_view.direct_identity"),
    F("baseline.traits.<name>.mean", "unit", reader="identity_view.direct_identity; floor (extraversion)"),
    F("baseline.traits.<name>.variability", "any", status="unread"),
    # ---- baseline: the worth menu --------------------------------------------------------------------------------
    F("baseline.model", "map", reader="state; floor; connection", doc="the worth menu: values, foundations, needs, regard"),
    F("baseline.model.schwartz", "map", reader="state; floor; connection"),
    F("baseline.model.schwartz.<name>", "unit", reader="state; floor; connection"),
    F("baseline.model.moral_foundations", "map", reader="state; connection"),
    F("baseline.model.moral_foundations.<name>", "unit", reader="state; connection"),
    F("baseline.model.needs", "map", reader="state; connection"),
    F("baseline.model.needs.<name>", "unit", reader="state; connection"),
    F("baseline.model.regard", "map", reader="state._regard", doc="whom they count as people, by group or id; the arc moves it"),
    F("baseline.model.regard.<name>", "unit", reader="state._regard"),
    F("baseline.model.resolution_priority", "any", status="unread"),
    # ---- baseline: drives, voice, skills ---------------------------------------------------------------------------
    F("baseline.drives", "map", reader="scene._manner_drives"),
    F("baseline.drives.goals", "list", reader="scene._manner_drives; connection"),
    F("baseline.drives.goals[]", "map", reader="scene._manner_drives", doc="{goal, priority} - an object, never a bare string"),
    F("baseline.drives.goals[].goal", "text", reader="scene._manner_drives", doc="told to the actor"),
    F("baseline.drives.goals[].priority", "unit", reader="connection"),
    F("baseline.drives.goals[].satisfaction", "any", status="unread"),
    F("baseline.drives.goals[].urgency", "any", status="unread", doc="urgency is read on current.active_goals"),
    # drives-schema.md's six design keys (BLUEPRINT-character "LEAVE BLANK"): the actor is told only the goal itself
    F("baseline.drives.goals[].kind", "any", status="unread", doc="the actor is told only the goal (scene._manner_drives)"),
    F("baseline.drives.goals[].serves", "any", status="unread"),
    F("baseline.drives.goals[].status", "any", status="unread"),
    F("baseline.drives.goals[].origin", "any", status="unread"),
    F("baseline.drives.goals[].triggers", "any", status="unread"),
    F("baseline.drives.goals[].view", "any", status="unread"),
    F("baseline.drives.orientation", "any", status="unread", doc="cut from what the actor sees (scene._manner_drives)"),
    F("baseline.drives.fears_wounds", "any", status="retired", policy="move",
      replaced_by="baseline.wounds - a wound is engine state, keyed by a concept and a path"),
    F("baseline.voice", "prose", reader="identity_view.direct_identity; narrate", doc="how they sound - told to the actor verbatim"),
    F("baseline.skills", "map", required="always", reader="gate.perception_scope; bonds; tells; consolidation",
      doc="both drivers index it directly: absent, a run crashes",
      absent="EMPTY - every skill is treated as exactly average"),
    F("baseline.skills.<name>", "unit", reader="gate.perception_scope (perception, insight); consolidation (combat)"),
    F("baseline.provenance", "any", status="unread", doc="where the numbers came from - kept out of the prompt"),
    # ---- baseline: engine state and its gates ---------------------------------------------------------------------
    F("baseline.catalog", "delegated", check=_catalog, reader="levers.active_rows", doc="tier-3 rows: a standing fact multiplies a path"),
    F("baseline.wounds", "list", reader="wound; connection; levers; passage", doc="engine state, minted - never hand-written"),
    F("baseline.wounds[]", "delegated", check=_wound, reader="wound._check (with the wounds system on)"),
    F("baseline.relationship_priors", "map", reader="bond_rest; bonds"),
    F("baseline.relationship_priors.default_trust", "unit", reader="bond_rest", doc="where a stranger's trust rests"),
    F("baseline.relationship_priors.update", "delegated", check=_rates, reader="bonds.rates_of",
      doc="how fast trust is granted and withdrawn, in words"),
    F("baseline.relationship_priors.in_group", "any", status="retired", policy="move",
      replaced_by="current.relationships (a person) or current.attachments grp.<tag> (a group)"),
    F("baseline.relationship_priors.out_group", "any", status="unread"),
    F("baseline.relationship_priors.in_group_capacity", "any", status="unread"),
    F("baseline.body", "delegated", required="always", system="body", check=_body, reader="body.capacity",
      doc="strength, one word - every act is weighed against it"),
    # ---- current -------------------------------------------------------------------------------------------------
    F("current.affect", "map", required="always", reader="state.appraise", doc="the mood on page one, one number per path"),
    F("current.affect.<PATH>", "unit", required="always", reader="state.appraise"),
    F("current.affect.<PRIMITIVE>", "any", status="retired", policy="refuse", replaced_by=_MOVED),
    F("current.condition", "map", required="always", system="condition", check=_condition, reader="condition; gate; direction",
      doc="how worn they arrive",
      absent="EMPTY - the actor is told nothing of energy, and memory runs on the full budget"),
    F("current.condition.energy", "unit", required="condition_flow", system="condition",
      reader="condition; gate._energy_budget"),
    F("current.condition.allostatic_load", "unit", required="condition_flow", system="condition",
      reader="gate._energy_budget; arc"),
    F("current.condition.injuries", "delegated", system="injuries", check=_injuries, reader="injuries.require",
      doc="page-one injuries: {what, severity, ago}"),
    F("current.condition.<name>", "number", reader="levers (a catalog row's condition_at_most)"),
    F("current.relationships", "map", reader="presence; bonds; bond_rest; direction", doc="one edge per person they know",
      absent="absent - no edges reach the prompt, so every prior bond is re-inferred from prose each turn"),
    F("current.relationships.<id>", "map", reader="presence.edge_from_rel"),
    F("current.relationships.<id>.trust", "unit", reader="bonds; bond_rest; direction"),
    F("current.relationships.<id>.affinity", "unit", reader="bonds; bond_rest; direction"),
    F("current.relationships.<id>.respect", "unit", reader="bonds; bond_rest; direction"),
    F("current.relationships.<id>.debt", "unit", reader="bonds; bond_rest; direction"),
    F("current.relationships.<id>.known_as", "text", reader="gate.scope_names; faithfulness; acquisition",
      doc="what they call someone whose name they do not know"),
    F("current.relationships.<id>.history", "any", status="unread", doc="copied onto the edge; no prompt renders it"),
    F("current.relationships.<id>.their_view", "map", status="runtime", reader="bonds.reflect; direction"),
    F("current.relationships.<id>.their_view.<name>", "unit", status="runtime", reader="direction"),
    F("current.attachments", "delegated", check=_attachments, reader="attachments; connection; scene._build_holds",
      doc="what they hold that is not a person: loc.<id> / grp.<tag> -> {hold, sign}",
      absent="absent - nothing but a person can move this character's bonds; the composition pass fills it"),
    F("current.active_goals", "list", reader="gate.run_gate; identity_view",
      absent="EMPTY - nothing weights goal-salience for recall"),
    F("current.active_goals[]", "map", reader="gate.run_gate", doc="{goal, urgency}"),
    F("current.active_goals[].goal", "text", reader="gate.run_gate"),
    F("current.active_goals[].urgency", "unit", reader="identity_view"),
    F("current.location", "text", reader="gate.perception_scope", doc="a world.locations id"),
    F("current.vault", "list", reader="gate.run_gate; decay; acquisition", doc="what they believe - the Beliefs section",
      absent="EMPTY - this character recalls NOTHING; the Beliefs section loads only `- (confidence, provenance) claim` lines"),
    F("current.vault[]", "map", check=_belief, reader="gate.run_gate"),
    F("current.vault[].claim", "text", reader="gate.run_gate"),
    F("current.vault[].confidence", "unit", reader="decay"),
    F("current.vault[].provenance", "text", reader="decay"),
    F("current.vault[].links", "list", reader="gate.run_gate"),
    F("current.vault[].about", "list", status="runtime", reader="facets.stamp"),
    F("current.vault[].topics", "list", status="runtime", reader="facets.stamp"),
    F("current.vault[].place", "text", status="runtime", reader="facets.stamp"),
    F("current.vault[].believed_value", "any", status="runtime", reader="associative (carried; dropped at the packet)"),
    F("current.vault[].durability", "text", reader="decay"),
    F("current.vault[].status", "text", status="runtime", reader="acquisition"),
    F("current.vault[].must_surface", "bool", reader="gate.run_gate"),
    F("current.vault[].bid", "text", status="runtime", reader="acquisition"),
    F("current.vault[].target_actor", "text", reader="associative"),
    F("current.vault[].epistemic_stance", "text", reader="associative"),
    F("current.vault[].created_turn", "number", status="runtime", reader="decay"),
    F("current.vault[].last_recalled_turn", "number", status="runtime", reader="decay"),
    F("current.vault[].recall_count", "number", status="runtime", reader="decay"),
    F("current.vault[].supersedes", "any", status="runtime", reader="acquisition"),
    F("current.vault[].superseded_by", "any", status="runtime", reader="acquisition"),
    F("current.vault[].timestamp", "any", status="unread"),
    F("current.targets", "map", status="runtime", reader="targets; scene", doc="what each path's feeling is about now"),
    F("current.targets.<PATH>", "text", status="runtime", reader="targets"),
    F("current.toward", "map", status="runtime", reader="toward; passage", doc="attitude: signed feeling toward a person"),
    F("current.toward.<id>", "map", status="runtime", reader="toward"),
    F("current.toward.<id>.<PATH>", "signed", status="runtime", reader="toward"),
    F("current.zone", "any", status="unread"),
    # ---- beside the sections -----------------------------------------------------------------------------------------
    F("id", "any", status="unread", doc="the id the engine reads is fixed.id"),
    F("formative", "map", reader="composition_pass (backstory)", doc="the composition pass's input"),
    F("formative.backstory", "text", reader="composition_pass"),
    F("formative.<name>", "any", status="unread", doc="class, culture, history: fold what matters into fixed.position"),
    F("backstory", "text", reader="composition_pass"),
    F("formative_picks", "list", reader="composition_pass", doc="the formative profiles picked, {profile, weight}"),
    F("formative_picks[]", "map", reader="composition_pass"),
    F("formative_picks[].profile", "text", reader="composition_pass", doc="a formative library profile id"),
    F("formative_picks[].weight", "number", reader="composition_pass"),
    F("formative_picks[].why", "text", reader="composition_pass", doc="the classification's reason for the pick"),
)
