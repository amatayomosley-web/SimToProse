#!/usr/bin/env python3
"""lint_book.py — pre-run validation of a book's world + characters (production-hardening).

Catches the authoring-error class BEFORE a run instead of at runtime: a missing baseline primary
(KeyError mid-run), a relationship key that is not a world-people id (its edge SILENTLY never
surfaces — content-guide), a malformed vault belief. A mechanical CHECK (the project's discipline);
report-only — authoring stays human. Consolidates + extends scripts/direct.py:startup_faults.

Usage:
  python scripts/lint_book.py --vault "<book>"                 # a real book (Obsidian vault)
  python scripts/lint_book.py --book ashford --char maren      # engine test fixtures
"""
import argparse
import json
import re
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIXTURE_SUFFIXES = ("", "-slice", "-healer")   # this repo's fixture stems — they live HERE, not in src/engine (hard rule 1)
sys.path.insert(0, REPO)

from src.engine.records import PATHS, RecordError               # noqa: E402
from src.engine import books
from src.engine import attachments                               # noqa: E402  (gate 5: the block beside relationships)
from src.engine import systems as _systems                       # noqa: E402  (which systems the book runs)
from src.engine import body as _body                             # noqa: E402  (strength, when the book runs the body)
from src.engine import injuries as _injuries                     # noqa: E402  (page-one injuries, when the book runs them)
from src.engine import bonds                                     # noqa: E402  (rates_of: a prose rate word refuses at the first witnessed beat)
from src.engine.state import _DIM_TO_PATH                        # noqa: E402  (the appraisal vocabulary, DERIVED)

# Never a second hand-written list: `state._DIM_TO_PATH` IS the engine's dimension
# vocabulary, and a copy here would be the eighth row of CLAUDE.md's duplicates table.
_APPRAISAL_DIMS = frozenset(_DIM_TO_PATH)

# DERIVED from the gate's own list, never a second copy — the words a percept drops.
from src.engine.gate import _words_from_attr as _wfa                 # noqa: E402
_STOPWORDS = frozenset(w for w in
                       ("the a an to of and is in at on by for with her his their its"
                        " she he they it who was has have").split())

_OPTIONAL_BASELINE = ("traits", "model", "skills", "voice", "drives")



_DECIMAL_IN_PROSE = re.compile(r"\d+\.\d+")


def _identity_strings(fixed, baseline):
    """Every (path, string) the STABLE IDENTITY PREFIX carries to the actor verbatim.

    Mirrors what `scene._build_stable` selects — persona / genotype / traits / model / drives /
    voice / provenance — and skips the keys `_strip_notes` already removes (`note`, and anything
    leading with an underscore), because those never reach the prompt.
    """
    out = []

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k) == "note" or str(k).startswith("_"):
                    continue
                walk(v, "%s.%s" % (path, k) if path else str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, "%s[%d]" % (path, i))
        elif isinstance(obj, str):
            out.append((path, obj))

    walk({"persona": {k: fixed.get(k) for k in ("id", "name", "people", "position")},
          "genotype": fixed.get("genotype", {})}, "")
    for key in ("traits", "model", "drives", "voice", "provenance"):
        walk(baseline.get(key, {}), key)
    return out



# Every key whose value the engine will hand to arithmetic. A sentence in ANY of these passes a
# JSON parse and dies later, deep, with no field path attached.
#
# MEASURED 2026-08-30, and this is why the check exists: a novice author following the character
# blueprint's "circle one" ladder wrote `"intensity": "it takes me over"`. The book linted with
# ZERO ERRORS — this very file even printed the offending sentence inside an unrelated WARNING
# ("intensity it takes hold of me when it comes reaches no arithmetic") and still called it clean —
# and then died on its first beat at identity_view.py with a bare
# `ValueError: direction: value must be a number in [0,1]`, naming no character and no field.
# A pre-flight that passes a book which cannot run is not a pre-flight.
#
# The list is explicit, and tests/test_numeric_slots.py derives the engine's own `_check_num` call
# names from source and fails if this set stops covering them — a hand-maintained list is this
# repo's most expensive failure class, so it does not stand alone.
_NUMERIC_KEYS = frozenset((
    "intensity", "priority", "satisfaction", "urgency", "mean", "variability",
    "trust", "affinity", "respect", "debt",
    "energy", "allostatic_load", "health", "fatigue",
    "confidence", "fidelity",
))
# Numeric, but NOT bounded to [0,1]. `catalog[].magnitude` is a MULTIPLIER when the row's op is
# "x" — standard-vectors.md sizes disposition-grade rows at x0.6-1.5 and the live reference book
# carries 1.45 — and an ADDITIVE delta when the op is "+", where a negative value is a legitimate
# debuff. A first version of this sweep put magnitude in the bounded set and reported five errors
# against the reference book itself, every one of them correct authoring. Caught by running the
# guard against a real book before trusting it.
_NUMERIC_UNBOUNDED = frozenset(("magnitude",))
# Keys whose value is a MAP of name -> number (the worth menus and skill tables).
_NUMERIC_MAPS = frozenset(("schwartz", "moral_foundations", "needs", "regard", "skills",
                           "relevance_weights", "gains"))


def _numeric_slot_errors(tag, node, path=""):
    """Walk a character's engine block; report every numeric slot holding something that is not a
    number in [0,1]. Returns [str]. Reports ALL of them, not the first — an author should not have
    to re-run once per mistake."""
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            here = "%s.%s" % (path, k) if path else k
            if k in _NUMERIC_MAPS and isinstance(v, dict):
                for name, val in v.items():
                    out += _check_slot(tag, "%s.%s" % (here, name), val)
            elif k in _NUMERIC_KEYS:
                out += _check_slot(tag, here, v)
            elif k in _NUMERIC_UNBOUNDED:
                out += _check_slot(tag, here, v, bounded=False)
            else:
                out += _numeric_slot_errors(tag, v, here)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            out += _numeric_slot_errors(tag, item, "%s[%d]" % (path, i))
    return out


def _check_slot(tag, path, v, bounded=True):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return ["%s: %s = %r is not a number. The engine hands this straight to arithmetic; a "
                "sentence here passes JSON, passes lint's other checks, and stops the run when the "
                "prompt is built (direction.py _check_num). If a form gave you a phrase to circle, "
                "the number it stands for goes in the sheet." % (tag, path, v)]
    if bounded and not (0.0 <= float(v) <= 1.0):
        return ["%s: %s = %r is outside [0,1]" % (tag, path, v)]
    return []


def lint(world, chars):
    """Validate (world, chars). Returns {"errors": [...], "warnings": [...]}. Errors would break a
    run; warnings flag thin or silently-degrading authoring (the content-guide's live-field rules)."""
    errors, warnings = [], []
    if not isinstance(world, dict):
        return {"errors": ["world is not a dict"], "warnings": []}

    people_ids = {p.get("id") for p in (world.get("people") or []) if isinstance(p, dict) and p.get("id")}
    _registered = attachments.names_for(world)
    location_ids = {l.get("id") for l in (world.get("locations") or []) if isinstance(l, dict) and l.get("id")}
    if not world.get("lexicon"):
        warnings.append("world: no lexicon — perception falls back to generic extraction (kind + leading words), thin")
    # ABSENCE checks. Every per-item check below iterates a collection, so an EMPTY collection is
    # structurally invisible to it: zero beliefs, zero relationships and zero people all lint clean
    # while the mechanism they feed is switched off. A dark mechanism is the expensive failure —
    # it degrades silently and the prose merely reads thin. Name it here, once, up front.
    if not world.get("people"):
        warnings.append("world.people is EMPTY — entity recognition (insight >= 0.55) has nothing to "
                        "recognize, and every relationship edge below is disabled with it. "
                        "people/*.md notes load ONLY when frontmatter says type: person")
    if not world.get("locations"):
        warnings.append("world.locations is EMPTY — no scene can produce a location percept")
    if not world.get("laws"):
        warnings.append("world.laws is EMPTY — the world refuses nothing; laws_bearing_on/verdict_for "
                        "have no rule to return")
    # LAWS REACHABILITY. src/engine/bible.py:_applies narrows a law by its `act` ONLY when the
    # CALLER supplies one, so a law carrying an act fires only if some scene cfg declares that
    # act (scripts/scene.py pre-flight). A law nothing can key is a rule the world states and
    # never applies -- verdict_for had no caller at all until 2026-08-22.
    _acts = sorted({str(l.get("act")) for l in (world.get("laws") or []) if l.get("act")})
    if _acts:
        warnings.append("world.laws: %d law(s) are keyed by an `act`; a scene cfg must declare the "
                        "matching act or the law never fires. Acts: %s%s"
                        % (len(_acts), ", ".join(_acts[:4]), " ..." if len(_acts) > 4 else ""))
    for i, loc in enumerate(world.get("locations") or []):
        if not (isinstance(loc, dict) and loc.get("id")):
            warnings.append("world.locations[%d]: missing id" % i)
    for i, p in enumerate(world.get("people") or []):
        if not (isinstance(p, dict) and p.get("id")):
            warnings.append("world.people[%d]: missing id" % i)
    # AUTHORED TENSIONS — the fifth live field (world-state-ledger.md). Validated at the authoring
    # boundary, because a tension with an unusable interest or an empty watch looks live and can
    # never move: nothing would be in scope, nothing would price, and it would sit inert for a whole
    # book with no error anywhere. Also cross-checked against the world's own ids, so a tension that
    # watches a place the world does not register is caught here rather than by silence.
    try:
        from src.engine.tensions import from_world as _tensions_from_world
        from src.engine.errors import EngineError as _EngErr
        _tensions = _tensions_from_world(world)
    except _EngErr as _te:
        _tensions = []
        errors.append("world.tensions: %s" % _te)
    except ImportError:
        _tensions = []
    _people_ids = {p.get("id") for p in (world.get("people") or []) if isinstance(p, dict)}
    for _t in _tensions:
        _w = _t.get("watches") or {}
        for _loc in (_w.get("locations") or []):
            if location_ids and _loc not in location_ids:
                warnings.append("world.tensions[%s] watches location %r, which is not registered — "
                                "no act there can ever be in scope for it (Rule 6)"
                                % (_t.get("id"), _loc))
        for _who in (_w.get("parties") or []):
            if _people_ids and _who not in _people_ids and _who not in (chars or {}):
                warnings.append("world.tensions[%s] watches party %r, which is neither a registered "
                                "person nor a cast member — check the id" % (_t.get("id"), _who))

    # WHICH SYSTEMS THE BOOK RUNS (gate systems-registry, 2026-09-22): a declaration the engine cannot
    # honour is an error here, not a crash at the first beat; the systems it switches off stop being
    # demanded of the sheets below.
    try:
        _enabled = _systems.for_book(world)
    except RecordError as e:
        errors.append("world.systems: %s" % e)
        _enabled = _systems.defaults()

    # CAST-JOIN checks (character-authoring-rules.md Rule 1c). The packet is built by JOINS on ids;
    # the engine never infers a connection. A character authored only in characters/ is invisible to
    # gate._extract_named_entities ("Identity derives from world.people"), so no entity percept is
    # produced and scene._build_edges emits no edge — the scene partner is simply absent from the
    # packet while every file involved lints clean.
    for cid in sorted(chars or {}):
        if people_ids and cid not in people_ids:
            warnings.append("char %r: not in world.people — no other character can PERCEIVE them. "
                            "A character is not automatically an entity; add {id: %r, what: ...}" % (cid, cid))
    for cid, ch in sorted((chars or {}).items()):
        if not isinstance(ch, dict):
            continue
        for target in ((ch.get("current") or {}).get("relationships") or {}):
            if target in (chars or {}):
                back = ((chars[target].get("current") or {}).get("relationships") or {})
                if cid not in back:
                    warnings.append("char %r -> %r is ONE-WAY: %r has no relationship record back to "
                                    "%r, so %r gets no edge for %r in any scene they share"
                                    % (cid, target, target, cid, target, cid))

    for cid, ch in (chars or {}).items():
        tag = "char %r" % cid
        if not isinstance(ch, dict):
            errors.append("%s: not a dict" % tag)
            continue
        for sec in ("fixed", "baseline", "current"):
            if not isinstance(ch.get(sec), dict):
                errors.append("%s: missing/invalid section %r (assemble requires it)" % (tag, sec))
        fixed, baseline, current = ch.get("fixed", {}), ch.get("baseline", {}), ch.get("current", {})

        if not str(fixed.get("name", "")).strip():
            errors.append("%s: fixed.name missing" % tag)
        aff = current.get("affect") or {}
        miss_a = [p for p in PATHS if p not in aff]
        if miss_a:
            errors.append("%s: current.affect missing primaries %s (appraise needs all %d)"
                          % (tag, miss_a, len(PATHS)))
        for p, v in aff.items():
            if p in PATHS and not (isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0):
                errors.append("%s: current.affect[%s]=%r not in [0,1]" % (tag, p, v))
        # EVERY other numeric slot, at any depth. The affect check above was the only one, so
        # intensity / priority / satisfaction / the relationship axes / condition / the worth
        # menus all accepted prose and failed later with no field path.
        errors.extend(_numeric_slot_errors(tag, ch))
        if "condition" in _enabled:
            if not isinstance(current.get("condition"), dict):
                errors.append("%s: current.condition missing or not a dict (assemble requires a dict)" % tag)
            elif "condition_flow" in _enabled and not {"energy", "allostatic_load"} <= set(current["condition"]):
                # the flow MOVES both keys (src/engine/condition.py); the drivers refuse such a sheet before the
                # first beat, so it is an error here, not a warning
                errors.append("%s: this book runs condition_flow, which moves energy AND allostatic_load - "
                              "current.condition must author both" % tag)
            elif ("energy" in current["condition"]) != ("allostatic_load" in current["condition"]):
                warnings.append("%s: current.condition carries only one of energy / allostatic_load - the readers "
                                "assume different values for the missing one (memory budget, stage line, arc, catalog)" % tag)
        if "body" in _enabled:                        # every act is weighed against it (gate body-exertion)
            try:
                _body.capacity(ch)
            except RecordError as e:
                errors.append("%s: this book runs the body system - %s" % (tag, e))
        if "injuries" in _enabled:                    # page-one injuries must be readable (gate injuries)
            try:
                _injuries.require(ch)
            except RecordError as e:
                errors.append("%s: this book runs the injuries system - %s" % (tag, e))
        for _off in _systems.authored_for_off(ch, _enabled):
            warnings.append("%s: a %s block is authored, but this book switches the %s system off - it does "
                            "nothing" % (tag, _off, _off))

        # THE LAW, the half the engine cannot enforce. `direction.direct_identity` bands every
        # engine SCALAR before it reaches the actor, but an authored STRING is the author's prose
        # and the engine must not rewrite it — so a design note like "patience x0.4 ·
        # temper x1.2" written into a value reaches the actor as a raw stat, and only a human
        # can decide whether that is wanted. Found on a real book the first time this ran.
        for path, text in _identity_strings(fixed, baseline):
            hits = sorted(set(_DECIMAL_IN_PROSE.findall(text)))
            if hits:
                warnings.append(
                    "%s: %s carries %s in AUTHORED TEXT — the identity prefix reaches the actor "
                    "verbatim, so these land as raw stats (design.md: 'The LLM never sees raw "
                    "stats'). The engine bands its own numbers and will not rewrite your prose: "
                    "move the calibration into a `note` key (stripped) or say it in words."
                    % (tag, path, ", ".join(hits[:4])))

        # content-guide rule: a relationship key must be a world.people id or the edge never surfaces
        for k in (current.get("relationships") or {}):
            if people_ids and k not in people_ids:
                warnings.append("%s: relationship %r is not a world.people id — its edge will never surface in a scene" % (tag, k))
        # ATTACHMENTS beside relationships (bond-arithmetic.md s3, gate 5): an unregistered key is an
        # error; `in_group` is retired (four shapes across ten sheets, zero readers); a prose rate word
        # refuses at the character's first witnessed beat, so it is named here instead.
        priors = (baseline.get("relationship_priors") or {})
        if "in_group" in priors:
            errors.append("%s: relationship_priors.in_group is RETIRED (2026-09-18, bond-arithmetic.md s3) and was read by "
                          "nothing: a person belongs in current.relationships (the edge is the hold), a group in "
                          "current.attachments as grp.<tag> at member — migrate per shape and delete the key" % tag)
        for dead in ("out_group", "in_group_capacity"):
            if dead in priors:
                warnings.append("%s: relationship_priors.%s is read by NO engine code" % (tag, dead))
        try:
            bonds.rates_of(priors)
        except RecordError as e:
            errors.append("%s: relationship_priors.update: %s" % (tag, e))
        block = current.get("attachments")
        if block is not None:
            try:
                attachments.validate_block(block, registered=_registered)
            except RecordError as e:
                errors.append("%s: current.attachments: %s" % (tag, e))
        else:
            warnings.append("%s: current.attachments absent — nothing but a person can move this character's "
                            "bonds (bond-arithmetic.md s0); the composition pass's --attach-classify fills it" % tag)
        # PERSONA checks (character-authoring-rules.md Rule 1b). scene.py:_build_stable reads
        # fixed.id / fixed.people / fixed.position into the persona block the ACTOR sees. The whole
        # `formative` block — culture, class, history — is read by no engine code and no prompt, so a
        # sheet can look richly authored on the page and hand the actor an empty identity.
        if not fixed.get("position"):
            warnings.append("%s: fixed.position is EMPTY — the actor receives no place, class or "
                            "station at all" % tag)
        # DEAD `formative` IS ITS OWN CHECK, not a footnote on an empty position. Gated on
        # `not fixed.position` it could never fire on the shape it targets — a populated position
        # AND a top-level formative block — which is exactly the state most characters of a live
        # book were in, warning-free. The two fields are independent; so are the checks.
        formative = ch.get("formative") or fixed.get("formative") or {}
        if formative:
            warnings.append("%s: a `formative` block is authored (%s) and is read by NO engine code "
                            "— it reaches no prompt and computes nothing. Fold what matters into "
                            "fixed.position (place/class/era/niche), which is the live slot"
                            % (tag, ", ".join(sorted(formative)[:6])))
        if not fixed.get("id"):
            warnings.append("%s: fixed.id missing — persona.id reads null (a character-level \"id\" "
                            "outside `fixed` does not populate it)" % tag)
        if not fixed.get("people"):
            warnings.append("%s: fixed.people missing — persona.people reads null" % tag)

        # ABSENCE checks, per character (character-authoring-rules.md Rule 8)
        if not current.get("vault"):
            warnings.append("%s: current.vault is EMPTY — this character recalls NOTHING. The `## Beliefs`"
                            " section loads only lines matching `- (confidence, provenance) claim`;"
                            " prose bullets parse to zero with no error (vault.py:22)" % tag)
        if not current.get("relationships"):
            warnings.append("%s: current.relationships absent — no edges reach the prompt, so every "
                            "prior bond is re-inferred from prose each turn" % tag)
        # GENOTYPE VOCABULARY. src/engine/state.py:_allele takes the leading token and falls
        # back to 1.0 for anything it does not know, SILENTLY. Measured 2026-08-22: three of six
        # axes on one book's protagonist were written as phrases whose first word is no allele
        # word, so all three read as typical, and a deliberately extreme temperament ran as an
        # ordinary one on every axis the author had marked. An ERROR, not a warning: it changes
        # who the character IS and says nothing.
        try:
            # THE one reading, from `heritable.py`. A genotype is one {hit, hold} cell per PATH
            # since 2026-09-10; the retired six-axis shape is an ERROR (heritable.entry refuses
            # it by name, and so does this, earlier and with the fix attached). A `rest` inside
            # a genotype cell is the morning-of-2026-09-10 shape and an ERROR too: where a
            # character rests is authored at baseline.temperament[path].rest, beside the voice.
            from src.engine import heritable as _her
            from src.engine.records import PATHS as _PATHS, RecordError as _RE
            _vocab = {"hit": tuple(_her.GAIN), "hold": tuple(_her.PERSIST)}
            geno = fixed.get("genotype") or {}
            stale = [k for k in geno if k in _her.OLD_AXES]
            if stale:
                errors.append("%s: genotype uses the retired axes %s. It is now one {hit, hold} "
                              "cell per path — see docs/guide-emotional-authoring.md" % (tag, stale))
            for p in _PATHS:
                cell = geno.get(p)
                if cell is None:
                    continue
                if not isinstance(cell, dict):
                    errors.append("%s: genotype.%s must be a dict of {hit, hold}, got %r"
                                  % (tag, p, str(cell)[:34]))
                    continue
                for ax, val in sorted(cell.items()):
                    if ax.startswith("_"):
                        continue
                    if ax == "rest":
                        errors.append("%s: genotype.%s.rest — where they rest is a DESIGN choice now, not "
                                      "a genotype cell: move it to baseline.temperament.%s.rest, beside "
                                      "their voice (docs/authoring/BLUEPRINT-character.md Part Three)"
                                      % (tag, p, p))
                        continue
                    if ax not in _her.AXES:
                        errors.append("%s: genotype.%s.%s is not a cell; the cells are %s"
                                      % (tag, p, ax, "|".join(_her.AXES)))
                        continue
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        continue                      # an authored NUMBER is honoured as written
                    lead = _her.word(val, default="")
                    if lead not in _vocab[ax]:
                        errors.append("%s: genotype.%s.%s starts %r, which is not a %s word - it reads "
                                      "as the default and the authored trait is lost. Use one of %s as "
                                      "the FIRST word; keep your prose after it"
                                      % (tag, p, ax, str(val)[:34], ax, "|".join(_vocab[ax])))
            # THE RESTING FACE — baseline.temperament[path].rest, authored beside the voice.
            # A word must be a rest word (the same silent-default trap as the genotype cells);
            # a rest above the cap (word or number) is honoured and gets a receipt naming the
            # rung, so it is a decision and never an accident; a stored mean whose rung is not
            # the rest word's rung is the old primitive-era scale, or a rest that was moved
            # without the mean — the arc engine writes there, so it is kept and WARNED.
            temp = baseline.get("temperament") or {}
            if isinstance(temp, dict):
                for p in _PATHS:
                    row = temp.get(p)
                    if row is None:
                        continue                      # absent = quiet, seeded on first use
                    if not isinstance(row, dict):
                        errors.append("%s: baseline.temperament.%s must be a dict of {rest, mean}, got %r"
                                      % (tag, p, str(row)[:34]))
                        continue
                    val = row.get("rest")
                    if val is not None and not (isinstance(val, (int, float)) and not isinstance(val, bool)):
                        lead = _her.word(val, default="")
                        if lead not in _her.REST_WORDS:
                            errors.append("%s: baseline.temperament.%s.rest starts %r, which is not a rest "
                                          "word - it reads as quiet and the authored disposition is lost. "
                                          "Use one of %s as the FIRST word; keep your prose after it"
                                          % (tag, p, str(val)[:34], "|".join(_her.REST_WORDS)))
                            continue
                    try:
                        over, rung = _her.over_cap(p, temp)
                        if over:
                            warnings.append("%s: baseline.temperament.%s.rest sits at rung %d (%s) — above the "
                                            "cap of %d for a resting disposition. Deliberate? Then this note "
                                            "is the receipt." % (tag, p, rung, _her.BANDS[p][rung - 1][2],
                                                                 _her.REST_CAP[p]))
                        if "mean" in row:
                            have = _her.rung_of_mean(p, float(row["mean"]))
                            want = _her.rest_rung(p, temp) or _her.rung_of_mean(p, _her.rest_mean(p, temp))
                            if have != want:
                                warnings.append("%s: baseline.temperament.%s.mean %.2f sits at rung %d (%s) but "
                                                "rest says %r (rung %d). The mean is seeded from the rest word "
                                                "once and the arc engine moves it after; a whole rung apart "
                                                "is the old scale, or a rest moved without its mean — delete "
                                                "the mean to re-seed it, or move the rest"
                                                % (tag, p, float(row["mean"]), have, _her.BANDS[p][have - 1][2],
                                                   _her.word(row.get("rest"), default="quiet"), want))
                    except (_RE, ValueError, TypeError):
                        pass
        except ImportError:
            pass

        # TIER-3 CATALOG (decision-engine.md buff/debuff registry). Rows are validated by the
        # engine at assembly and fail loud there; here we catch the AUTHORING half early.
        cat = (baseline.get("catalog") or {})
        rows = cat.get("rows") if isinstance(cat, dict) else cat
        rows = rows or []
        try:
            from src.engine.levers import _check_row
            for i, row in enumerate(rows):
                _check_row(row, i)
        except ValueError as e:
            errors.append("%s: baseline.catalog %s" % (tag, e))
        except ImportError:
            pass
        # WOUNDS ARE ENGINE STATE (gate three, 2026-09-11). Owner: "wounds are a multiplier, so
        # move it out of character sheet". A sheet that still carries the authored prose block is
        # refused by name, with the fix attached; what a sheet may carry is `baseline.wounds` —
        # rows the composition pass minted from the formative library (source profile:<id>) or a
        # run minted from a beat (source run:<turn>) — each keyed by a registry concept and a path.
        if (baseline.get("drives") or {}).get("fears_wounds"):
            errors.append("%s: baseline.drives.fears_wounds is not read since 2026-09-11 — a wound is "
                          "engine state at baseline.wounds, keyed by a concept (src/engine/concepts.py) "
                          "and a path, minted by scripts/composition_pass.py from a formative profile "
                          "or by a run from a beat. Move each wound to a profile pick, or write it as "
                          "{concept, path, intensity, source, text, trigger} under baseline.wounds "
                          "(docs/authoring/BLUEPRINT-character.md Part Five)" % tag)
        try:
            from src.engine import wound as _wound
            _wl = baseline.get("wounds")
            if _wl is not None and not isinstance(_wl, list):
                errors.append("%s: baseline.wounds must be a list" % tag)
            for wi, wnd in enumerate(_wl or []):
                if isinstance(wnd, dict) and all(str(k).startswith("_") for k in wnd):
                    continue                                   # an author's _note row
                try:
                    _wound._check(wnd)
                except Exception as e:               # noqa: BLE001 — one line per bad wound
                    errors.append("%s: baseline.wounds[%d]: %s" % (tag, wi, str(e)[:160]))
                    continue
                src_ = str(wnd.get("source", ""))
                if not (src_.startswith("profile:") or src_.startswith("run:")):
                    errors.append("%s: baseline.wounds[%d] source %r must be profile:<id> or run:<turn> — a "
                                  "wound is minted, never hand-written" % (tag, wi, src_))
        except ImportError:
            pass
        _wids = {str(w.get("id")) for w in (baseline.get("wounds") or []) if isinstance(w, dict)}
        for ri, row in enumerate(rows if isinstance(rows, list) else []):
            if not isinstance(row, dict):
                continue
            named = str(row.get("wound", "") or "").strip()
            if named and named not in _wids:
                errors.append(
                    "%s: baseline.catalog row %d names wound %r, which baseline.wounds does not carry. "
                    "The row would fire at full magnitude no matter what happens to that wound. Known "
                    "ids: %s" % (tag, ri, named, sorted(_wids) or "none"))
        if not current.get("active_goals"):
            warnings.append("%s: current.active_goals is EMPTY — nothing weights goal-salience for recall" % tag)
        loc = current.get("location")
        if loc and location_ids and loc not in location_ids:
            warnings.append("%s: current.location %r is not a world.locations id — no location percept "
                            "will be produced there" % (tag, loc))
        for opt in _OPTIONAL_BASELINE:
            if not baseline.get(opt):
                warnings.append("%s: baseline.%s absent — thin (read where present)" % (tag, opt))
        for j, b in enumerate(current.get("vault") or []):
            if not (isinstance(b, dict) and str(b.get("claim", "")).strip()):
                warnings.append("%s: vault[%d] has no claim" % (tag, j))
            elif "provenance" not in b:
                warnings.append("%s: vault[%d] missing provenance (seed/authored/lived/witnessed/learned)" % (tag, j))

    return {"errors": errors, "warnings": warnings}


def _load_fixture(book, char):
    def find(folder, stem):
        try:                           # ONE copy of this search — direct.py carried the other
            return books.fixture_path(REPO, folder, stem, _FIXTURE_SUFFIXES)
        except books.BookError as e:
            raise SystemExit(str(e))
    with open(find("world", book), encoding="utf-8") as fh:
        world = json.load(fh)
    with open(find("characters", char), encoding="utf-8") as fh:
        ch = json.load(fh)
    return world, {ch.get("fixed", {}).get("name", char).lower(): ch}


def main():
    ap = argparse.ArgumentParser(description="lint a book's world + characters before a run")
    ap.add_argument("--vault", default=None, help="BOOK folder (Obsidian vault)")
    ap.add_argument("--book", default=None, help="engine test-fixture world stem (use with --char)")
    ap.add_argument("--char", default=None, help="fixture character stem (with --book)")
    args = ap.parse_args()

    if args.vault:
        from src.engine.vault import load_book, VaultError
        try:
            world, chars = load_book(args.vault)
        except VaultError as e:            # a contract breach IS a lint error, not a traceback
            print("  ERROR %s" % e)
            print("\nlint: 1 error(s), 0 warning(s)")
            return 1
    elif args.book and args.char:
        world, chars = _load_fixture(args.book, args.char)
    else:
        raise SystemExit("pass --vault <book>, or --book <stem> --char <stem>")

    report = lint(world, chars)
    for w in report["warnings"]:
        print("  WARN  %s" % w)
    for e in report["errors"]:
        print("  ERROR %s" % e)
    n_e, n_w = len(report["errors"]), len(report["warnings"])
    # "clean" means nothing fired. A run with warnings is NOT clean - saying so is how 8
    # warnings naming an empty vault got read as a pass.
    print("\nlint: %d error(s), %d warning(s)%s" % (n_e, n_w, " — clean" if not (n_e or n_w) else ""))
    return 1 if n_e else 0


if __name__ == "__main__":
    sys.exit(main())
