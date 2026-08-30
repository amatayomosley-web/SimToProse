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
    parser = argparse.ArgumentParser(description="Deterministic Phase B Formative Composition Pass")
    parser.add_argument("--character", help="Path to character JSON file")
    parser.add_argument("--picks", nargs="*", help="Formative profile picks in format profile_id:weight (e.g. fire_survival_acute:1.0)")
    parser.add_argument("--output", help="Path to write output character JSON")
    parser.add_argument("--list-profiles", action="store_true", help="List all available formative profiles by category")
    parser.add_argument("--show-profile", help="Show details for a specific profile ID")

    args = parser.parse_args()

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
    if args.picks:
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
