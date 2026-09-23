#!/usr/bin/env python3
"""composition_pass.py ? deterministic Phase B composition pass for character authoring.

`docs/composition-pass.md` is normative:
  - Phase A: classify backstory -> profile picks (LLM, generation-time, 1x/char)
  - Phase B: compose prior + sum(weight * diffs) -> baseline (Deterministic script)

Usage:
  python scripts/composition_pass.py --character path/to/char.json --picks profile1:1.0 profile2:0.5 --output path/to/out.json
  python scripts/composition_pass.py --list-profiles
  python scripts/composition_pass.py --show-profile <profile_id>

Stdlib only.
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import profiles as P
from src.engine import attachments as _attachments                  # gate 5: the relation-word rubric and the price table
from src.engine import vault as _vault                              # a book folder as the world source
from src.engine.records import RecordError

NL = chr(10)


# ---------------------------------------------------------------------------------------------
# ATTACHMENTS — the first LLM classification step in character generation with a coded parser
# (bond-arithmetic.md s3, gate 5). The classifier names a RELATION WORD per registered place or
# group with the backstory sentence that shows it; the script prices the word from a table the
# classifier is never shown. A thing the backstory names that the world lacks is a GAP: reported,
# never minted. Same key-free seam as Phase A: emit the prompt, validate the reply.


def _world_lines(world):
    names = _attachments.names_for(world)
    whats = {}
    for loc in world.get("locations") or []:
        if isinstance(loc, dict) and loc.get("id"):
            whats[_attachments.LOC + str(loc["id"])] = str(loc.get("what") or "")
    carriers = {}
    for p in world.get("people") or []:
        if isinstance(p, dict):
            for tag in p.get("groups") or []:
                carriers.setdefault(_attachments.GRP + str(tag), []).append(str(p.get("id") or ""))
    rows = []
    for n in names:
        if n in whats:
            rows.append("  %s — %s" % (n, whats[n]))
        else:
            rows.append("  %s — a group tag carried by: %s" % (n, ", ".join(sorted(carriers.get(n, []))) or "nobody"))
    return rows


def build_attach_classify_prompt(backstory, world):
    """The attachment classifier's messages: the backstory, the world's registered places and groups
    (id — what), the four relation words with their boundary tests. No numbers, no table: the
    classifier names the word; attachments.hold_of prices it (settled review s2 rule 3)."""
    sys_msg = (
        "You read a character's BACKSTORY and say what, among THE WORLD'S PLACES AND GROUPS, this person "
        "HOLDS — and how. You answer with a RELATION WORD per entity and the sentence of the backstory that "
        "shows it. You never write a number: a script prices the word, and a number from you would make a "
        "misreading on your part indistinguishable from a miscalibration on its part."
        + NL + NL +
        "THE FOUR WORDS, closest to farthest. Each carries the test that separates it from the one below "
        "it; when the backstory does not pass the test, use the word below."
        + NL + NL + _attachments.rubric() + NL + NL +
        "RULES." + NL +
        "- Only entities from THE WORLD'S PLACES AND GROUPS, copied exactly by id. A thing the backstory "
        "names that the list lacks goes in `gaps` with its sentence — it is reported, never invented." + NL +
        "- One entry per entity. Leave out what the backstory does not touch: most people hold two or "
        "three things, and an EMPTY list is a legitimate answer." + NL +
        "- `because` is a sentence COPIED from the backstory — the words a reader would point to and say "
        "\"there\". Do not paraphrase. If you cannot point to the sentence, the backstory does not show it: "
        "leave the entity out." + NL +
        "- People are not here. What this person holds of another person is on the relationship sheet." + NL +
        "- No numbers anywhere in your reply."
        + NL + NL +
        "Reply with JSON only:" + NL +
        '{"holds": [{"entity": "<id from the list>", "relation": "life" | "post" | "member" | "acquainted",' + NL +
        '            "because": "<a sentence copied from the backstory>"}],' + NL +
        ' "gaps":  [{"named": "<what the backstory names that the list lacks>", "because": "<copied sentence>"}]}' + NL +
        "`gaps` is usually empty.")
    user_msg = ("BACKSTORY:" + NL + str(backstory).strip() + NL + NL
                + "THE WORLD'S PLACES AND GROUPS (id — what):" + NL + (NL.join(_world_lines(world)) or "  (none registered)"))
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]


def _norm(text):
    return " ".join(str(text or "").split()).lower()


def _has_number(obj):
    if isinstance(obj, bool):
        return False
    if isinstance(obj, (int, float)):
        return True
    if isinstance(obj, dict):
        return any(_has_number(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_number(v) for v in obj)
    return False


def holds_from_classification(reply, backstory, world):
    """A classifier reply -> ({entity: (word, sentence)}, gaps). Refuses by code, in this order:
    REPLY_NOT_AN_OBJECT, NUMBER_IN_REPLY, ENTITY_UNLISTED, WORD_UNKNOWN, BECAUSE_NOT_IN_BACKSTORY,
    ENTITY_REPEATED. Nothing is minted from `gaps`; they are returned for printing."""
    if not isinstance(reply, dict):
        raise RecordError("COMPOSITION_ATTACH_REPLY_NOT_AN_OBJECT", "the attachment classifier's reply is not an object, got %r" % type(reply).__name__)
    holds, gaps = reply.get("holds", []), reply.get("gaps", [])
    if not isinstance(holds, list) or not isinstance(gaps, list) or not all(isinstance(x, dict) for x in holds + gaps):
        raise RecordError("COMPOSITION_ATTACH_REPLY_NOT_AN_OBJECT", "the attachment classifier's reply must be {holds: [objects], gaps: [objects]}")
    if _has_number(holds) or _has_number(gaps) or any("hold" in h for h in holds):
        raise RecordError("COMPOSITION_ATTACH_NUMBER_IN_REPLY", "the attachment classifier wrote a number; it names a WORD and the script prices it")
    registered = set(_attachments.names_for(world))
    norm_back = _norm(backstory)
    out = {}
    for h in holds:
        entity = str(h.get("entity") or "").strip()
        if entity not in registered:
            raise RecordError("COMPOSITION_ATTACH_ENTITY_UNLISTED", "the attachment classifier named %r, which is not on the world's list (%s)" % (entity, ", ".join(sorted(registered)) or "nothing registered"))
        word = str(h.get("relation") or "").strip().lower()
        if word not in _attachments.RELATION_WORDS:
            raise RecordError("COMPOSITION_ATTACH_WORD_UNKNOWN", "the attachment classifier's relation %r is not one of %s" % (h.get("relation"), ", ".join(_attachments.RELATION_WORDS)))
        because = str(h.get("because") or "").strip()
        if not because or _norm(because) not in norm_back:
            raise RecordError("COMPOSITION_ATTACH_BECAUSE_NOT_IN_BACKSTORY", "the attachment classifier's sentence for %r is not in the backstory: %r" % (entity, because[:80]))
        if entity in out:
            raise RecordError("COMPOSITION_ATTACH_ENTITY_REPEATED", "the attachment classifier named %r twice" % entity)
        out[entity] = (word, because)
    kept_gaps = []
    for g in gaps:
        named = str(g.get("named") or "").strip()
        if not named:
            raise RecordError("COMPOSITION_ATTACH_REPLY_NOT_AN_OBJECT", "a gap entry names nothing")
        kept_gaps.append({"named": named, "because": str(g.get("because") or "").strip()})
    return out, kept_gaps


def apply_attachments(char_data, holds, world):
    """{entity: (word, sentence)} -> char_data with current.attachments = attachments.block_from_words(holds),
    validated against attachments.names_for(world). Returns char_data."""
    block = _attachments.block_from_words(holds)
    _attachments.validate_block(block, registered=_attachments.names_for(world))
    char_data.setdefault("current", {})["attachments"] = block
    return char_data


def _load_world(arg):
    """A world JSON path or a book folder -> the world dict."""
    if os.path.isdir(arg):
        world, _chars = _vault.load_book(arg)
        return world
    with open(arg, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------------------------
# PHASE A — classify a backstory into profile picks. The half that was missing.
#
# `docs/composition-pass.md` separates two operations and calls the separation the whole design:
#
#     classify   which profiles this backstory matches, and how strongly   LLM, once per character
#     compose    prior + sum(weighted diffs), summed, clamped, capped      script
#
# Phase B shipped; Phase A did not, so the only route to picks was typing `profile_id:weight` on the
# command line. That is why `guide-emotional-authoring.md` says the creation pass is unbuilt, and why
# having built a world bought the author nothing mechanically: the chain the design names — the world
# produces the baseline — had no middle.
#
# THE SEAM IS LOAD-BEARING, and the doc says why: if the model emits final NUMBERS instead of picks,
# reproducibility goes, the ±0.35 cap stops being enforceable, and a classification error becomes
# indistinguishable from a calibration one. So `picks_from_classification` REFUSES a reply carrying
# numbers where picks belong, rather than quietly composing them.


def build_classify_prompt(backstory, library=None):
    """The classifier messages: the backstory, the library WITH ITS DIFFS, and the rules.

    Three things and nothing else — no character sheet, no other characters, no target numbers
    (`docs/composition-pass.md`). The diffs are shown deliberately: a classifier that cannot see
    what a profile DOES is guessing at labels.
    """
    lib = library if library is not None else P.LIBRARY
    rows = []
    for pid in sorted(lib):
        prof = lib[pid] or {}
        diffs = prof.get("diffs") or {}
        desc = prof.get("description") or ""
        rows.append("%s — %s%s  DIFFS: %s" % (
            pid, prof.get("name", ""), (" (" + desc + ")") if desc else "",
            ", ".join("%s %+.2f" % (k, v) for k, v in sorted(diffs.items())) or "(none)"))

    sys_msg = (
        "You classify a character's BACKSTORY against a library of formative profiles. You pick "
        "from the library with weights; you never write final numbers. The arithmetic is done by a "
        "script that enforces a cap, and a number from you would make a misreading on your part "
        "indistinguishable from a miscalibration on its part."
        + NL + NL +
        "RULES. Pick from the library with a weight in (0, 1]. Every pick names WHY. Propose a NEW "
        "profile ONLY if nothing in the library above 0.5 fits the dominant feature of this "
        "backstory, and say what gap it fills. An EMPTY list of picks is a legitimate answer: some "
        "people are genuinely unremarkable, and inventing a formative wound for them is worse than "
        "saying so."
        + NL + NL +
        "Reply with JSON only: "
        '{"picks": [{"profile": str, "weight": float, "why": str}], '
        '"propose": {"name": str, "gap": str, "diffs": {field: float}, "why": {field: str}}}. '
        "`propose` is optional and usually absent.")

    user_msg = ("BACKSTORY:" + NL + str(backstory).strip() + NL + NL
                + "LIBRARY (%d profiles):" % len(rows) + NL + NL.join(rows))
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}]


def picks_from_classification(reply, library=None):
    """A classifier reply -> (picks, proposal_report). Validates; never composes numbers it was given.

    Four refusals, each because the doc names the failure it prevents:
      * a pick naming no profile, or one the library does not hold — a label with no diffs
      * a weight outside (0, 1] — the cap is enforced on the SUM, so an out-of-range weight
        silently defeats it
      * a reply carrying final baseline numbers where picks belong — the seam the doc calls the
        whole design
      * a `propose` block is run through `profiles.admit`, never trusted: that gate is the
        separability check, and bypassing it lets a near-duplicate into the library
    """
    lib = library if library is not None else P.LIBRARY
    if not isinstance(reply, dict):
        raise ValueError("classification must be a JSON object, got %s" % type(reply).__name__)
    for banned in ("baseline", "temperament", "traits", "model"):
        if banned in reply:
            raise ValueError(
                "classification carries %r — the classifier picks profiles, it does not write "
                "final numbers (docs/composition-pass.md: the cap has to be enforceable)" % banned)

    picks = []
    for i, row in enumerate(reply.get("picks") or []):
        if not isinstance(row, dict):
            raise ValueError("pick %d is not an object: %r" % (i, row))
        pid = row.get("profile")
        if not pid or pid not in lib:
            raise ValueError("pick %d names %r, which is not in the library — a label with no "
                             "diffs composes nothing" % (i, pid))
        try:
            w = float(row.get("weight", 1.0))
        except (TypeError, ValueError):
            raise ValueError("pick %d has a non-numeric weight %r" % (i, row.get("weight")))
        if not (0.0 < w <= 1.0):
            raise ValueError("pick %d has weight %r; weights are in (0, 1] because the cap is "
                             "enforced on their SUM" % (i, w))
        picks.append({"profile": pid, "weight": w, "why": row.get("why", "")})

    report = None
    prop = reply.get("propose")
    if prop:
        admitted, reason = P.admit(prop, lib)
        report = {"proposal": prop, "admitted": admitted, "reason": reason}
    return picks, report


def parse_picks(pick_args):
    """Parse pick arguments in format 'profile_id:weight' or 'profile_id' (defaults to weight 1.0)."""
    picks = []
    for arg in pick_args:
        if ":" in arg:
            pid, w_str = arg.split(":", 1)
            weight = float(w_str)
        else:
            pid, weight = arg, 1.0
        picks.append({"profile": pid, "weight": weight})
    return picks


def apply_composition_pass(char_data, picks):
    """Apply deterministic Phase B composition pass to a character dictionary.

    1. Composes baseline stats over prior enforcing the +-0.35 stacked movement cap.
    2. Injects catalog_rows from picked profiles.
    3. Injects vault_belief_seeds into character memory/vault.
    """
    # The prior is the character's CURRENT values read from the NESTED paths the engine uses.
    # Reading a flat `baseline` here was the bug: compose then wrote its result flat, beside the
    # real traits/model, and state.build_profile went on reading the originals.
    # baseline.temperament is NOT composed (2026-09-10): the rest word is character design,
    # authored beside the voice; a profile's old temperament diff sits on it as a `rest_note`.
    prior = P.prior_from(char_data)

    # 1. Compose (flat arithmetic, +-0.35 cap) then PLACE at the paths consumers read.
    P.place(char_data, P.compose(prior, picks))

    # 2. Catalog rows -> baseline.catalog.rows, which levers.active_rows reads via scene.assemble.
    #    A ROW THAT NAMES A CONCEPT IS A WOUND (gate three, 2026-09-11) and is MINTED, not placed:
    #    it becomes an engine wound at baseline.wounds keyed (concept, path), source profile:<id>,
    #    with the row's trigger phrases as the words the actor is told set it off. The library's
    #    vocation/passion/conditioning rows carry no concept and stay levers (dampeners work as
    #    multipliers; a wound's investment cannot dampen).
    from src.engine import wound as _wound
    cat = char_data.setdefault("baseline", {}).setdefault("catalog", {})
    rows = cat.setdefault("rows", [])
    wounds = char_data["baseline"].setdefault("wounds", [])
    seen_sources = {r.get("source") for r in rows if isinstance(r, dict)}
    seen_wounds = {w.get("id") for w in wounds if isinstance(w, dict)}
    for pick in picks:
        for row in P.get(pick["profile"]).get("catalog_rows", []):
            minted = _wound.from_profile_row(row, pick["profile"])
            if minted is not None:
                if minted["id"] not in seen_wounds:
                    wounds.append(minted)
                    seen_wounds.add(minted["id"])
                continue
            if row.get("source") not in seen_sources:
                rows.append(dict(row))
                seen_sources.add(row.get("source"))

    # 3. Belief seeds -> current.vault, where the recall gate reads them (vault.py:117).
    #    This is provenance seeding the vault: the reason a number moved becomes a thing the
    #    character remembers (baseline-generation.md).
    vault = char_data.setdefault("current", {}).setdefault("vault", [])
    seen_claims = {v.get("claim") for v in vault if isinstance(v, dict)}
    for pick in picks:
        for seed in P.get(pick["profile"]).get("vault_belief_seeds", []):
            if seed.get("claim") not in seen_claims:
                vault.append(dict(seed, believed_value=True))
                seen_claims.add(seed.get("claim"))

    char_data["formative_picks"] = list(picks)
    return char_data


def main():
    parser = argparse.ArgumentParser(description="the formative composition pass - Phase A classifies a backstory into profile picks (LLM, key-free via --classify), Phase B composes them (deterministic)")
    parser.add_argument("--character", help="Path to character JSON file")
    parser.add_argument("--picks", nargs="*", help="Formative profile picks in format profile_id:weight (e.g. fire_survival_acute:1.0)")
    parser.add_argument("--output", help="Path to write output character JSON")
    parser.add_argument("--list-profiles", action="store_true", help="List all available formative profiles by category")
    parser.add_argument("--show-profile", help="Show details for a specific profile ID")

    # PHASE A. Key-free by default, the same shape narrate.py and keeper.py use: the script emits
    # the prompt, a model fills it, and the reply comes back through --classification for
    # validation. Nothing here calls a model (hard rule 3 lives one directory over, but the habit
    # of keeping the dispatch at the edge is the reason it stays true).
    parser.add_argument("--classify", metavar="FILE_OR_TEXT",
                        help="Phase A: emit the classifier prompt for this backstory "
                             "(a path, or the prose itself)")
    parser.add_argument("--classification", metavar="FILE",
                        help="Phase A: a classifier reply (JSON) to validate into picks, then compose")
    # ATTACHMENTS (gate 5): the same seam, one table over — the classifier names a relation word per
    # registered place or group; the script prices it; a gap is printed, never minted.
    parser.add_argument("--attach-classify", metavar="FILE_OR_TEXT",
                        help="emit the attachment classifier prompt for this backstory (needs --world)")
    parser.add_argument("--attachments-classification", metavar="FILE",
                        help="an attachment classifier reply (JSON) to validate and price (needs --world; "
                             "with --character it writes current.attachments into the sheet)")
    parser.add_argument("--world", metavar="PATH_OR_BOOK", help="a world JSON path or a book folder")
    args = parser.parse_args()

    if args.attach_classify or args.attachments_classification:
        if not args.world:
            print("Error: --world is required (a world JSON path or a book folder).", file=sys.stderr)
            return 1
        world = _load_world(args.world)
        if args.attach_classify:
            backstory = args.attach_classify
            if os.path.isfile(backstory):
                with open(backstory, "r", encoding="utf-8") as fh:
                    backstory = fh.read()
            print(json.dumps(build_attach_classify_prompt(backstory, world), indent=2))
            return 0
        with open(args.attachments_classification, "r", encoding="utf-8") as fh:
            reply = json.load(fh)
        backstory = ""
        if args.character:
            with open(args.character, "r", encoding="utf-8") as f:
                char_data = json.load(f)
            backstory = str((char_data.get("formative") or {}).get("backstory") or char_data.get("backstory") or "")
        else:
            char_data = {}
        if args.attach_classify is None and not backstory and args.classify and os.path.isfile(args.classify):
            with open(args.classify, "r", encoding="utf-8") as fh:
                backstory = fh.read()
        holds, gaps = holds_from_classification(reply, backstory or reply.get("_backstory", ""), world)
        for g in gaps:
            print("  GAP  %s: %s" % (g["named"], g["because"]))
        updated = apply_attachments(char_data, holds, world)
        for k, v in sorted(updated["current"]["attachments"].items()):
            print("  hold  %-28s %s" % (k, v["note"]))
        if args.character and args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(updated, f, indent=2)
            print("Wrote %s" % args.output)
        elif not args.character:
            print(json.dumps(updated["current"]["attachments"], indent=2))
        return 0

    if args.classify:
        backstory = args.classify
        if os.path.isfile(backstory):
            with open(backstory, "r", encoding="utf-8") as fh:
                backstory = fh.read()
        print(json.dumps(build_classify_prompt(backstory), indent=2))
        return 0

    if args.list_profiles:
        cats = P.categories()
        print("Available Formative Profiles (%d total across %d categories):" % (len(P.available()), len(cats)))
        for cat, pids in sorted(cats.items()):
            print("\n  [%s] (%d profiles)" % (cat.upper(), len(pids)))
            for pid in pids:
                p = P.get(pid)
                print("    - %-32s : %s" % (pid, p.get("name", "")))
        return 0

    if args.show_profile:
        p = P.get(args.show_profile)
        print(json.dumps(p, indent=2))
        return 0

    if not args.character:
        parser.print_help()
        return 1

    with open(args.character, "r", encoding="utf-8") as f:
        char_data = json.load(f)

    picks = []
    if args.classification:
        with open(args.classification, "r", encoding="utf-8") as fh:
            reply = json.load(fh)
        picks, report = picks_from_classification(reply)
        for pk in picks:
            print("  pick  %-32s %.2f  %s" % (pk["profile"], pk["weight"], pk.get("why", "")))
        if not picks:
            # docs/composition-pass.md: an empty result is a legitimate answer. Said out loud so it
            # does not read as a failed run.
            print("  (no picks — this backstory matched nothing above threshold, which is allowed)")
        if report:
            print("  PROPOSAL %r: %s — %s" % (report["proposal"].get("name"),
                                              "ADMITTED" if report["admitted"] else "REJECTED",
                                              report["reason"]))
            if not report["admitted"]:
                print("        (it is NOT composed; profiles.admit is the separability gate)")
    elif args.picks:
        picks = parse_picks(args.picks)
    elif "formative_picks" in char_data:
        picks = char_data["formative_picks"]
    else:
        print("Error: No picks provided via --picks and no 'formative_picks' field in character JSON.", file=sys.stderr)
        return 1

    updated = apply_composition_pass(char_data, picks)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2)
        print("Wrote composed character to %s" % args.output)
    else:
        print(json.dumps(updated, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
