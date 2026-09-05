"""errors.py — the single typed refusal channel for the whole engine.

WHY THIS EXISTS. Before 2026-08-30 the engine had nine error classes rooted on two different
builtins (`LedgerError` on RuntimeError, the other eight on ValueError), each carrying prose and
nothing else. Nothing could be grepped, counted, or asserted on. A repo-wide sweep found 214 sites
where a failure, an absence, or an invalid value produced no loud error at all — the dominant class
being a check that discards more than the invalid field and a display that then prints the
pre-transformation value, so the degraded path reads exactly like a healthy one.

The measured incident that forced this: an actor omitted one enum field; `validate_tags` set
ok=False; `scripts/scene.py:403` answered that with `applied = {"dimensions": {}}`, discarding the
WHOLE self-report; affect did not move, the arc wrote nothing, bonds moved nothing, every listener's
salience was 0.0000 and the scene lulled. Three runs burned, because the operator line printed the
raw tags and the beat looked healthy.

THE CONTRACT (owner's directive, 2026-08-30): "if something is missing it should throw the fail with
the code as to why it failed."

  EngineError(code, detail)   ->  str() is "[CODE] detail",  .code is "CODE"
  EngineError(detail)         ->  str() is "detail",         .code is None   (legacy, pre-migration)

TWO INVARIANTS, both load-bearing, both tested in tests/test_errors.py:

1. `EngineError` subclasses `ValueError`. NOT a style choice — 24 test sites catch bare `ValueError`
   for engine raises (tests/test_state.py:272, test_bonds.py:247,252,729, test_arc.py:123,
   test_direction.py:180, test_effective.py:112,119,280, test_scene.py:265, test_subject.py:49,89,
   test_targets.py:248, test_consolidation.py:312,321,330, test_genotype.py:96, test_faults.py:141,
   test_no_digits.py:197,252, test_scene_config.py:70, test_orc_hooks.py:58, ...). Rooting the base
   anywhere else breaks every one of them.

2. The detail is preserved VERBATIM as the suffix. 13 measured tests assert on message substrings
   with `in str(e)` — the tightest is tests/test_no_digits.py:255, which asserts the offending path
   itself appears in `str()`. A prefix keeps all 13 green; replacing or restructuring the wording
   breaks them. Never move the message into an attribute `__str__` does not render.

The two-argument form is what a caller writes AFTER its module is migrated. The one-argument form
is what every unmigrated raise still uses, and it renders exactly as it did before — so a module
can be converted on its own gate without a flag day.

An unregistered code raises at CONSTRUCTION (`UnknownErrorCode`). That is deliberate: a code that
is not in `codes.CODES` is a typo or an unregistered addition, and a mistyped code silently
producing a valid-looking error would be this repo's own dominant defect class reappearing inside
the mechanism built to end it.
"""
from __future__ import annotations

from . import codes


class UnknownErrorCode(ValueError):
    """A code was used that `codes.CODES` does not register.

    Deliberately NOT an EngineError: an EngineError needs a code to be constructed, so raising one
    here would recurse. This is a programming error in the engine, not a refusal of user content.
    """


def _near(code, limit=4):
    """Registered codes sharing this one's prefix, with their descriptions.

    A mistyped code is nearly always a near-miss of a real one (VAULT_NO_CHARACTER for
    VAULT_NO_CHARACTERS), so the refusal that catches it should show the candidates rather than
    send the reader to grep the registry. This is also the production consumer of
    `codes.describe` — without it the descriptions would be read only by their own test, which is
    the declared-never-connected shape this whole module exists to end.
    """
    prefix = code.split("_")[0]
    hits = sorted(c for c in codes.CODES if c.split("_")[0] == prefix)
    if not hits:
        return ""
    shown = hits[:limit]
    lines = "".join("\n    %s — %s" % (c, codes.describe(c)) for c in shown)
    more = "" if len(hits) <= limit else "\n    ... and %d more" % (len(hits) - limit)
    return "\n  Registered %s_* codes:%s%s" % (prefix, lines, more)


class EngineError(ValueError):
    """Base for every coded engine refusal.

    Subclasses ValueError — see invariant 1 in the module docstring. Do not re-root it.
    """

    def __init__(self, *args):
        if len(args) >= 2:
            code, detail = str(args[0]), str(args[1])
            if not codes.is_registered(code):
                raise UnknownErrorCode(
                    "%r is not registered in src/engine/codes.py. Add it beside the raise that "
                    "uses it — the registry must never list a code nothing raises, and must never "
                    "omit a code something does.%s" % (code, _near(code)))
            self.code, self.detail = code, detail
            # `args` HOLDS THE CONSTRUCTOR ARGUMENTS, not the rendered message, because Python
            # reconstructs an exception as `cls(*self.args)` — that is how copy.copy,
            # copy.deepcopy, pickle, multiprocessing and concurrent.futures all rebuild one, and
            # none of them appears at a call site anyone would grep. Storing the rendered string
            # made `args` a ONE-element tuple, so every such reconstruction became a one-argument
            # construction that fell into the legacy branch below and silently returned an error
            # whose `.code` was None. `__str__` keeps the rendering, so the detail is still the
            # verbatim suffix that the message-substring tests assert on.
            super().__init__(code, detail)
        else:
            # THE CHANNEL REFUSES AN UNCODED REFUSAL (2026-09-04).
            #
            # This branch used to ACCEPT a bare prose message, so codes.py's first rule — a raised
            # code must be registered — was enforced by a SCAN rather than by the constructor. The
            # branch existed so a module could migrate on its own gate without a flag day. That
            # reason expired the moment the migration finished, and while it stood, 190 of 202
            # refusal sites stayed uncoded for five weeks after the channel shipped: an escape
            # hatch left open is the path everything takes.
            #
            # WHY A SCAN IS NOT ENOUGH, measured rather than argued: the sibling instance's AST
            # audit read `_require(cond, msg)` as an already-coded doorway and certified the
            # engine converted while 44 prose refusals sat behind it. A constructor cannot be
            # missed by anything that runs.
            raise UnknownErrorCode(
                "an engine refusal was constructed with no code: %r. Pass the code FIRST — "
                "EngineError(CODE, detail) — so it is registered, exposed as .code, and greppable "
                "by an operator who has only the code. Add the code to src/engine/codes.py beside "
                "the raise that uses it." % (str(args[0])[:70] if args else "(no arguments)",))

    def __str__(self):
        """`[CODE] detail`.

        EXPLICIT because `args` no longer holds the rendered string — see `__init__`.
        Without this, `str(e)` would render the tuple and every test asserting a message
        substring with `in str(e)` would break.
        """
        return "[%s] %s" % (self.code, self.detail)

    def __repr__(self):
        return "%s(code=%r, detail=%r)" % (type(self).__name__, self.code, self.detail)
