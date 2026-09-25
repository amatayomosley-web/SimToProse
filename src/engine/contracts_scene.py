"""contracts_scene.py — the scene file, declared once: every key a scene may carry, its shape, and where it stands.

The declarations `contracts.check` walks a scene file against (gate scene-contract, 2026-09-25), and the rows
BLUEPRINT-scene carries between its GENERATED markers. Built from an inventory of every key scripts/scene.py
(load_scene_cfg, run_scene, main), lint_scene, the narrator and the pinned-cfg readers take from a scene file,
file:line per key. It checks the file AS WRITTEN: the loader rewrites severity words to numbers, refuses `elapsed`
and exits on a bad voice, so a check after it could see none of those. Each vocabulary is the engine's own - the
clock's for `at` and `lasts`, the seven appraisal dimensions and the severity ladder for the opening tags, the
narration modes for `voice` and `knowledge`, the relation words for `attachments`, the condition words for
`condition` - one rule per thing.

Pure, deterministic, stdlib. No LLM (rule 3), no randomness (rule 4).
"""
from __future__ import annotations

__layer__ = "engine"

from .contracts import Field as F
from .records import RecordError


def _refuse(msg):
    raise RecordError("CONTRACT_FIELD_TYPE", msg)


def _cast_ids(cfg):
    cast = cfg.get("cast")
    return [str(c.get("id")) for c in (cast if isinstance(cast, list) else []) if isinstance(c, dict) and c.get("id")]


def _cast(cast, cfg, ctx):
    """Each character once: the run registers a cast member once and refuses a second registration mid-launch,
    after the run row is written."""
    ids = _cast_ids(cfg)
    twice = sorted({i for i in ids if ids.count(i) > 1})
    if twice:
        _refuse("names %s more than once - one character, one place in the room" % ", ".join(repr(i) for i in twice))


def _member(c, cfg, ctx):
    if not (str(c.get("id") or "").strip() and str(c.get("drive") or "").strip()):
        _refuse("every cast entry needs both an id and a drive - the loader refuses the scene without them")


def _at(at, cfg, ctx):
    from .clock import parse_at
    parse_at(at)


def _lasts(value, cfg, ctx):
    from .clock import span_minutes
    span_minutes(value)


def _named(name, cfg, ctx):
    if not name.strip():
        _refuse("a blank name labels the scene with nothing, so unrelated scenes share the label (and the resume's drift "
                "check compares them) - leave the key out to use the file's own name")


def _subject(subj, cfg, ctx):
    if isinstance(subj, (list, tuple)) and not subj:
        return                                              # [] - no one, as the loader reads it
    ok = isinstance(subj, (list, tuple)) and len(subj) == 2 and (
        subj[0] is None or (isinstance(subj[0], str) and subj[0].strip())) and (subj[1] is None or isinstance(subj[1], str))
    if not ok:
        _refuse("must be [id, group] ([null, null] for no one) - anything else the loader turns into no one, silently, "
                "and the regard scoping it exists for never fires; got %r" % (subj,))


def _dimensions(dims, cfg, ctx):
    """The seven appraisal dimensions (state._DIM_TO_PATH), each a severity word or a number in [0,1]: an unknown key
    is ignored by appraise without a word, and a word off the ladder refuses the whole scene."""
    from .severity import WORDS, value_of
    from .state import _DIM_TO_PATH
    if not isinstance(dims, dict):
        _refuse("must be an object of the seven dimensions ({dimension: word or number}), got %s" % type(dims).__name__)
    bad = []
    for key, v in dims.items():
        if key not in _DIM_TO_PATH:
            bad.append("%r is not one of the seven (%s) - appraise ignores it silently" % (key, ", ".join(sorted(_DIM_TO_PATH))))
        elif isinstance(v, str):
            try:
                value_of(v)
            except ValueError:
                bad.append("%s = %r is not a severity word (%s)" % (key, v, ", ".join(WORDS)))
        elif isinstance(v, bool) or not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
            bad.append("%s = %r is neither a severity word nor a number in [0,1]" % (key, v))
    if bad:
        _refuse("; ".join(bad))


def _pov(pov, cfg, ctx):
    if pov not in _cast_ids(cfg):
        _refuse("%r is not in this scene's cast - the narrator would be handed a point of view no one here holds" % (pov,))


def _voice(voice, cfg, ctx):
    from .narration_modes import DEFAULT_KNOWLEDGE, validate
    validate(voice, DEFAULT_KNOWLEDGE)


def _knowledge(knowledge, cfg, ctx):
    from .narration_modes import DEFAULT_VOICE, validate
    validate(DEFAULT_VOICE, knowledge)


def _hold(d, cfg, ctx):
    from .attachments import RELATION_HOLDS
    if not (d.get("char") and d.get("entity") and d.get("relation")):
        _refuse("an attachment declaration needs char, entity and relation - the loader refuses the scene without them")
    if str(d.get("relation")).strip().lower() not in RELATION_HOLDS:
        _refuse("relation %r is not one of %s" % (d.get("relation"), ", ".join(RELATION_HOLDS)))


def _condition(entries, cfg, ctx):
    from .condition import declaration_errors
    errs = [m for _code, m in declaration_errors(entries, _cast_ids(cfg))]
    if entries and "condition" not in ctx.get("systems", ("condition",)):
        errs.append("this scene states a condition, but the book switches the condition system off")
    if errs:
        _refuse("; ".join(errs))


SCENE = (
    F("name", "text", blank=False, check=_named, reader="scene (the clock's source label, the scene row, the resume drift check)",
      doc="the scene's name; the file's own name when absent (never blank: the loader keeps a blank as the label)"),
    F("situation", "text", required="always", reader="scene.run_scene", doc="the moment, told to every actor each beat"),
    F("cast", "list", required="always", check=_cast, reader="scene.run_scene; clock._scene_casts; mood_fold.replay",
      doc="who is in the room, each with what they want - each character once"),
    F("cast[]", "map", check=_member, reader="scene.run_scene"),
    F("cast[].id", "text", reader="scene.main (must be a character of the book)"),
    F("cast[].drive", "text", reader="scene.run_scene", doc="what they want from the others here - replaces their goals"),
    F("at", "map", required="always", check=_at, reader="clock.parse_at", doc="when the scene opens: {day, time}"),
    F("at.day", "number", reader="clock.parse_at", doc="a whole day; 0 and below are before page one"),
    F("at.time", "text", reader="clock.parse_at", doc="HH:MM"),
    F("lasts", "any", check=_lasts, reader="clock.span_minutes; passage.open_scene",
      doc="how long it runs: minutes, or 30m / 2h / 1d; absent, nothing decays inside the scene"),
    F("at_minutes", "any", status="runtime", reader="scene (derived from at; an author's value is overwritten)"),
    F("lasts_minutes", "any", status="runtime", reader="scene (derived from lasts; an author's value is overwritten)"),
    F("elapsed", "any", status="retired", policy="refuse",
      replaced_by="at (when the scene opens) and lasts (how long it runs) - the loader refuses elapsed"),
    F("subject", "any", blank=True, check=_subject, reader="scene.run_scene (the first beat's target; regard)",
      doc="[id, group] - whom the moment is about; left blank, no one (the loader reads a blank as absent)"),
    F("opening_tags", "map", reader="scene._salience (the opener)", doc="how hard the opening lands"),
    F("opening_tags.dimensions", "delegated", check=_dimensions, reader="floor; state.appraise",
      doc="the seven appraisal dimensions, each a severity word or a number in [0,1]"),
    F("opening_tags.type", "any", status="unread"),
    F("opening_tags.durability", "any", status="unread"),
    F("opening_tags.act", "any", status="unread", doc="the law check reads the scene's own `act`"),
    F("act", "text", reader="scene.law_preflight", doc="the act the world's laws are asked about before the run"),
    F("location", "text", reader="scene.law_preflight; gate._lookup_location", doc="a world.locations id"),
    F("props", "list", blank=True, reader="gate.perception_scope",
      doc="the room's objects, plainly present - three to five; left blank, none (the loader reads a blank as absent)"),
    F("props[]", "text", reader="gate.perception_scope"),
    F("pov", "text", check=_pov, reader="scene.record_boundary; narrate", doc="whose eyes the narrator uses; the first cast id when absent"),
    F("voice", "text", check=_voice, reader="narrate", doc="close-third | first | distant-third | second"),
    F("knowledge", "text", check=_knowledge, reader="narrate", doc="pov | omniscient"),
    F("attachments", "list", reader="scene.run_scene (priced at the first turn)", doc="the director's holds, in relation words"),
    F("attachments[]", "map", check=_hold, reader="scene.run_scene"),
    F("attachments[].char", "text", reader="scene.run_scene"),
    F("attachments[].entity", "text", reader="scene.run_scene", doc="loc.<id> or grp.<tag>"),
    F("attachments[].relation", "text", reader="attachments.RELATION_HOLDS"),
    F("attachments[].note", "text", reader="scene.run_scene"),
    F("condition", "any", check=_condition, reader="condition.apply_declared; mood_fold",
      doc="how worn someone arrives: {char, energy?, stress?, gap?} in words"),
)
