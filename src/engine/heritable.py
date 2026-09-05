"""heritable.py — the genotype: how it is READ, and what each allele does.

`docs/baseline-generation.md` calls the genotype *"a combinatorial preset draw — one allele per
heritable axis (the tuple = a preset)"*. Six words, authored on the sheet, and authors annotate them:

    "affiliation_attachment": "high (anxious-leaning bond style)"

So every consumer has to take the leading token and drop the rationale. **Four places did that
independently** — `state._allele`, `arc._allele`, `scene._allele_word` and `lint_book`'s inline
`split()[0].lower()` — and on 2026-09-01 a fifth reader was added that DIDN'T, which is the whole
reason this file exists.

That fifth reader was `state._persist`, the persistence half of "one allele, two effects". It looked
the raw string up in its own table, missed every key on an annotated allele, and returned the species
prior. The GAIN fired at 1.3 and the PERSISTENCE silently did nothing — on the repo's own reference
fixture — while the suite stayed green, because every persistence test used bare words.

`CLAUDE.md` tabulates seven instances of one class: *a hand-written list that mirrors something the
code already knows.* A hand-repeated PARSE is the same defect wearing different clothes, and it fails
the same way — silently, in the copy nobody re-checked. One reading, here, and every consumer calls
it.

TWO EFFECTS, TWO TABLES. An allele scales how hard a primitive is hit (`GAIN`) and how long it is
held (`PERSIST`). Separate maps on purpose: the relationship between magnitude and duration is not
known to be 1:1, and forcing it would make one of them untunable. `PERSIST`'s spread is the narrower
one because retention compounds every beat, so the same multiplier is a far larger effect there.
"""

# The allele vocabulary. Mirrored by `tests/coherence_probe.py` ALLELE and validated at the
# authoring boundary by `scripts/lint_book.py`, which reports an unrecognised leading token rather
# than letting it read as TYPICAL and lose the authored trait.
GAIN = {
    "low":      0.75,
    "typical":  1.0,
    "elevated": 1.2,
    "high":     1.3,
}

PERSIST = {
    "low":      0.85,
    "typical":  1.0,
    "elevated": 1.10,
    "high":     1.15,
}

# Which axis lends itself to which primitive — the SAME wiring for both effects, so the two cannot
# drift apart. LUST, PLAY and DISGUST are absent because no heritable axis feeds them; they take the
# species prior in both directions. Whether they SHOULD have axes changes what a genotype IS, and is
# an authoring decision rather than an engine one.
AXIS_FOR = {
    "FEAR":        "threat_reactivity",
    "SEEKING":     "approach_drive",
    "RAGE":        "anger_proneness",
    "CARE":        "affiliation_attachment",
    "PANIC_GRIEF": "affiliation_attachment",
}

AXES = ("threat_reactivity", "approach_drive", "affiliation_attachment",
        "anger_proneness", "effortful_control", "sensitivity")


def word(value, default="typical"):
    """An authored allele value -> its bare allele word.

    `"high (anxious-leaning bond style)"` -> `"high"`. THE one reading; call this rather than
    writing `.split()[0].lower()` again.
    """
    tok = str(default if value is None else value).split()
    return tok[0].lower().rstrip("(") if tok else str(default).lower()


def word_of(axis, genotype, default="typical"):
    """The allele word for one axis of a genotype, or the species default."""
    return word((genotype or {}).get(axis, default), default)


def gain(axis, genotype):
    """How hard this axis makes its primitives land. Unknown allele -> 1.0, the species prior."""
    return GAIN.get(word_of(axis, genotype), 1.0)


def persist(primary, genotype):
    """How long this character holds this primitive, from the allele that already sets its gain.

    1.0 for a primitive with no heritable axis and for an unknown allele — the species prior.
    Never 0: callers divide by it.
    """
    axis = AXIS_FOR.get(primary)
    return 1.0 if axis is None else PERSIST.get(word_of(axis, genotype), 1.0)
