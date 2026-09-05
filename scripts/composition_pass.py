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

NL = chr(10)


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
    # real temperament/traits/model, and state.build_profile went on reading the originals.
    prior = P.prior_from(char_data)

    # 1. Compose (flat arithmetic, +-0.35 cap) then PLACE at the paths consumers read.
    P.place(char_data, P.compose(prior, picks))

    # 2. Catalog rows -> baseline.catalog.rows, which levers.active_rows reads via scene.assemble.
    cat = char_data.setdefault("baseline", {}).setdefault("catalog", {})
    rows = cat.setdefault("rows", [])
    seen_sources = {r.get("source") for r in rows if isinstance(r, dict)}
    for pick in picks:
        for row in P.get(pick["profile"]).get("catalog_rows", []):
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
    args = parser.parse_args()

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
