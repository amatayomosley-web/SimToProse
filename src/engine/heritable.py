"""heritable.py — one parser for the allele vocabulary, which three readers had spelled apart.

`docs/baseline-generation.md` defines the genotype as one allele per heritable axis, drawn from a
CLOSED four-word vocabulary. Authors write the word plus an optional parenthetical rationale:

    "affiliation_attachment": "high (anxious-leaning bond style)"

MEASURED IN THIS TREE 2026-09-04, THREE READERS PARSED THAT INDEPENDENTLY:

    state._allele        str(...).split()[0].lower()          # gain math
    arc._allele          str(raw).split()[0].lower()          # gain math, same spelling
    scene._allele_word   str(value).split(" (", 1)[0].strip() # display, splits on a LITERAL " ("

`arc.py` already imports the `_ALLELE` gain TABLE from `state`, so the table was shared while the
PARSE was not — and the parse is the half that drifted. `scene`'s version never lowercases, so on
a capitalised allele it returned "High" where the gain math read "high". No fixture carries one
today, which is exactly why it went unnoticed: a disagreement that only fires on input nobody has
written yet is still a disagreement, and it fires the day someone writes it.

WHY A SHARED PARSER IS SAFE HERE, and would not be everywhere: the vocabulary is CLOSED and every
token is a single word (`state._ALLELE` has four keys — low, typical, elevated, high). So
"first whitespace-delimited word, lowercased" and "everything before the parenthetical" return the
same token for every value this repo can hold. On an open or multi-word vocabulary they would
diverge and this lift would be wrong.

WHAT IS DELIBERATELY NOT HERE. The sibling instance's version of this module also carries a
`PERSIST` table and a `persist()` reader — the duration half of the same allele, one allele with
two effects. This tree has no mechanism for it: `state.build_profile` computes
`eff_r = 1.0 - (1.0 - base_r) * regulation` with no persistence divisor. Landing that half now
would either fail `tests/test_reachable.py` on arrival or change genotype behaviour under cover of
a refactor. It comes back WITH its caller, or not at all.
"""
from __future__ import annotations

#: allele -> multiplicative gain on the axis's trait sensitivity. The vocabulary is closed;
#: `state._ALLELE` is bound to this table so there is one owner rather than two copies.
GAIN = {
    "low":      0.75,
    "typical":  1.0,
    "elevated": 1.2,
    "high":     1.3,
}


def word(value):
    """The allele token from an authored value, without its rationale.

    'high (anxious-leaning bond style)' -> 'high';  'High' -> 'high'.

    Lowercased, because the gain table is lowercase and an author who capitalises should not
    silently fall through to the default. Splitting on whitespace rather than on the literal
    " (" handles both the parenthetical form and a bare word, and is what the two gain-math
    readers already did.
    """
    return str(value).split()[0].lower() if str(value).split() else ""


def word_of(genotype, axis, default="typical"):
    """The allele token for one axis of a genotype mapping, defaulted when absent."""
    if not isinstance(genotype, dict):
        return default
    return word(genotype.get(axis, default))


def gain(axis, genotype, default=1.0):
    """The numeric gain for one heritable axis. Unknown alleles fall back to `default`.

    Unknown rather than refused, deliberately: an author's typo should damp the axis to neutral
    and keep the run going, not abort a chronicle mid-beat. The authoring lint is where a bad
    allele should be caught loudly.
    """
    return GAIN.get(word_of(genotype, axis), default)
