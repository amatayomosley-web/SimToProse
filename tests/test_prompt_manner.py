#!/usr/bin/env python3
"""test_prompt_manner.py — a rate is spent ONCE, and the actor is never told its own rates.

THE DEFECT THIS PINS. `state.build_profile` reads `fixed.genotype`, the trait means and
`baseline.model` and turns them into gains, relevance and regard — how hard an event moves this
person. Until 2026-09-06 `scene._build_stable` put the SAME fields into the stable prefix and
`identity_view.direct_identity` rendered them to the actor as sentences, from phrase tables that
module's own comment calls "reactivity rather than configuration". So a character was damped once
in the arithmetic and again in the prose.

WHY THAT IS NOT A FEATURE, which is how I had it. The path model gives every emotion one axis and
a rung on it, and a rung has to mean the same thing for two different people or the scale is not
shared. Let the sheet speak twice and rung 9 means "assault" for one character and "mildly cross"
for another — which is the one property the whole design cannot lose. The owner's ruling,
2026-09-06: the disposition sets the RATES and the baseline; it must not act mid-story.

THE LINE, in two prongs and in this order:
  1. RATE   — if the engine reads the field as a number, the actor never sees it. Grep-checkable.
  2. AXIS   — of what is left, a line stays only if it makes no claim any path also makes, i.e. it
              holds at every one of the 92 rungs. A laconic man is laconic when furious and when
              bored; a man who "can set anything aside" is contradicted by rung 9 outright.

WHAT SURVIVES is manner and biography: who he is, how he sounds, what he is trying to do, and what
was done to him.

Script-style, stdlib only, exit 0 = all pass.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine.scene import assemble, _build_stable          # noqa: E402
from src.engine.prompt import build_turn_messages             # noqa: E402
from src.engine.identity_view import direct_identity          # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + detail) if (detail and not cond) else ""))


def _ren():
    ch = json.load(open(os.path.join(REPO, "characters/ren-traveler.json"), encoding="utf-8"))
    world = json.load(open(os.path.join(REPO, "world/ashford-slice.json"), encoding="utf-8"))
    return ch, world


def _real_prompt():
    """The prompt the driver actually sends — not a hand-built dict.

    Built through `assemble`, because four separate conclusions on 2026-09-06 turned out to be about
    a hand-made harness rather than the engine. If a test can go through the real path, it does.
    """
    ch, world = _ren()
    packet = assemble(ch, world,
                      {"event": {"text": "a cart comes back broken", "kind": "mundane"},
                       "recent": [], "location": ch["current"].get("location")},
                      dict(ch["current"]["affect"]), ch["current"]["condition"])
    msgs = build_turn_messages(packet, "a cart comes back broken",
                               ch["baseline"]["temperament"], {})
    return packet, "\n".join(m["content"] for m in msgs)


def test_the_rate_blocks_are_gone_from_the_prefix():
    """`traits` LEFT THIS TUPLE on 2026-09-09, by owner ruling: the character sheet is what
    defines who the character is, so the assembler does not choose which parts of them reach
    a scene.

    It joined genotype/model/provenance on 2026-09-06 under one argument -- a rate is spent
    once, and saying it again in prose damps the character twice. That holds for the three
    facets that DO slope arithmetic (emotionality, agreeableness, extraversion, through
    `state._HEXACO_SENSITIVITY_MAP`). It never held for conscientiousness, openness and
    honesty_humility, which slope nothing and make no claim the state layer also makes --
    the same test this suite applies to voice and biography.

    THE NAMED DEFECT IS NOT REINTRODUCED. The two sentences section [2] guards -- "it takes
    a great deal to make you angry" and "you can set anything aside and mean it" -- live in
    `_ALLELE_PHRASES`, the GENOTYPE table, and genotype is still cut. Verified 2026-09-09.

    NOT SETTLED: whether restoring the three SLOPED facets makes an actor play a rung harder
    than the rung says. Empirical, untested -- see the gate's OMISSIONS."""
    print("\n[1] THE RATES DO NOT REACH THE ACTOR")
    packet, _ = _real_prompt()
    stable = packet["stable"]
    for block in ("model", "provenance"):
        check("prefix-has-no-%s" % block, block not in stable, sorted(stable))
    # `temperament` JOINED 2026-09-10: the rest WORDS (never the seeded mean — scene._rest_words
    # sends only strings) travel so `direct_identity` can say where the character rests under
    # `disposition`, beside the trait sentences. Owner: temperament is a character design
    # question, along with their voice.
    check("...and-what-is-left-is-manner-biography-and-disposition",
          sorted(stable) == ["drives", "genotype", "persona", "temperament", "traits", "voice", "wounds"],
          sorted(stable))
    temper = stable.get("temperament") or {}
    check("the-rest-words-travel-and-the-means-do-not",
          bool(temper) and all(set(row) == {"rest"} and isinstance(row["rest"], str) for row in temper.values()),
          temper)


def test_the_rendered_phrases_are_gone_too():
    """Absence from the dict is not enough — `direct_identity` renames the blocks it renders, so a
    block could vanish by key and still arrive under its rendered name."""
    print("\n[2] AND NOT UNDER THEIR RENDERED NAMES EITHER")
    _, told = _real_prompt()
    # `disposition` INVERTED 2026-09-09 -- REQUIRED now, not forbidden.
    # BLUEPRINT-character.md 7.3 has an author circle one of four sentences per facet and
    # promises in bold they are "word for word, the sentences the actor will be shown".
    # That promise was false from 2026-09-06 to 2026-09-09 and no suite caught it, because
    # none asserted what the prefix CONTAINS -- only what it lacks.
    check("HAS-disposition-section", '"disposition"' in told,
          "the blueprint promises the actor is shown these")
    # `how you are built` INVERTED 2026-09-09 with genotype, same ruling as disposition.
    check("HAS-how-you-are-built", "how you are built" in told,
          "a person knows their own constitution")
    for name, needle in (
                         ("no-what-you-weigh", "what you weigh"),
                         ("no-resolution-priority", "resolution_priority")):
        check(name, needle not in told, needle)
    # THESE TWO WERE NAMED THE DEFECT ON 2026-09-06 AND ARE NOW REQUIRED. Both are
    # `_ALLELE_PHRASES`; restoring genotype reinstates precisely the sentences this suite was
    # written to forbid. That is the owner's ruling and it is stated here rather than
    # quietly deleted, so a reader meets the reversal instead of an absence.
    #
    # The open risk, unchanged: anger_proneness sets DISPLEASURE gain, so this sentence and a
    # DISPLEASURE rung block make claims about the same primary. Untested.
    # 2026-09-10: `effortful_control` was cut with the primitive-era genotype, so "you can set
    # anything aside and mean it" no longer exists. Ren's WARINESS hold is `brief`; that cell's
    # phrase is the second required sentence now.
    for name, needle in (("anger-constitution-in-words", "it takes a great deal to make you angry"),
                         ("hold-constitution-in-words", "once the danger passes, it is gone from you")):
        check(name, needle in told, needle)
    # 2026-09-10: Ren's WARINESS rests `raised`. That is DESIGN, said under `disposition` beside
    # the trait sentences — and NOT under "how you are built", which is the genotype's block.
    rest_needle = "some part of you is always listening for trouble"
    check("rest-sentence-is-in-the-prompt", rest_needle in told, rest_needle)
    built_at = told.find("how you are built")
    disp_at = told.find('"disposition"')
    seg_disp = told[disp_at:built_at] if 0 <= disp_at < built_at else told[disp_at:disp_at + 2000]
    seg_built = told[built_at:built_at + 2000] if built_at >= 0 else ""
    check("rest-sentence-is-under-disposition", rest_needle in seg_disp, "disposition block: %s" % seg_disp[:200])
    check("rest-sentence-is-not-under-how-you-are-built", rest_needle not in seg_built, seg_built[:200])


def test_manner_and_biography_survive():
    print("\n[3] AND THE CHARACTER IS STILL THERE")
    packet, told = _real_prompt()
    for name, needle in (("the-name-survives", "Ren"),
                         ("the-position-survives", "never once failed to arrive"),
                         ("the-register-survives", "level and unhurried"),
                         ("a-manner-tic-survives", "says 'right' before he moves"),
                         ("the-goal-text-survives", "bring whoever is with him back"),
                         ("the-wound-text-survives", "hunting spider's bite")):
        check(name, needle in told, needle)


def test_a_missing_weight_is_silence_not_a_middle_one():
    """The renderer used to default an absent weight to 0.5 and band it into a sentence, so cutting
    a field caused the prompt to INVENT one — "it catches you sometimes" for a wound carrying no
    intensity. Fabricating is worse than leaking or dropping: a leak is visible and a drop is
    absent, but an invented middle reads exactly like an authored one."""
    print("\n[4] AN ABSENT WEIGHT IS NOT A MIDDLING ONE")
    _, told = _real_prompt()
    # INVERTED 2026-09-11 (gate three): a wound is engine state and CARRIES an intensity by
    # contract (wound._check refuses one without), so Ren's spider scar is said — "it takes you
    # over" — and the invented-middle defect cannot arise from an absent field. The fabrication
    # guard moves to the renderer check below, on a wound the renderer was not given a weight for.
    check("the-wound-intensity-is-said-from-engine-state", "it takes you over" in told)
    # TOLERATING ONE "how much" WAS THE WEAK FORM, and it hid a second fabricator. The count test
    # passes whether the volatile goal's weight was AUTHORED or INVENTED, so it certified exactly
    # the defect it was written to catch. Assert the source instead: every rendered weight must
    # trace to an authored one.
    from src.engine.identity_view import direct_goals
    packet, _ = _real_prompt()
    vol_goals = packet["volatile"]["goals"]
    rendered = direct_goals(vol_goals)
    said = sum(1 for g in rendered if isinstance(g, dict) and "how much" in g)
    authored = sum(1 for g in vol_goals if isinstance(g, dict) and "urgency" in g)
    check("every-rendered-urgency-was-authored", said == authored,
          "%d rendered from %d authored" % (said, authored))
    check("a-goal-with-no-urgency-gets-no-phrase",
          "how much" not in direct_goals([{"goal": "unweighted"}])[0],
          str(direct_goals([{"goal": "unweighted"}])))
    rendered = json.dumps(direct_identity({"drives": {"fears_wounds": [{"wound": "the spider"}]}}))
    check("the-renderer-says-nothing-about-a-weight-it-was-not-given",
          "how it takes you" not in rendered, rendered)
    check("...and-still-renders-the-wound", "the spider" in rendered, rendered)


def test_a_voice_phrase_holds_at_every_rung():
    """Voice is the instrument; a path is the pressure on it. `voice.md:12` defines assertiveness as
    hedges vs declaratives — sentence FORM. It had been written as conduct ("you press a point until
    it is answered"), which states a position on DISPLEASURE's supervision axis, and the top phrase
    sat around `phrases-rage.md` 0.70."""
    print("\n[5] A VOICE PHRASE IS SYNTAX, NOT PRESSURE")
    from src.engine.identity_view import _SCALARS
    bad = ("press a point", "take the room", "hold it", "until it is answered")
    hits = [p for p in _SCALARS["assertiveness"] for b in bad if b in p]
    check("assertiveness-names-no-conduct", not hits, "; ".join(hits))
    check("...and-names-sentence-form",
          any("qualify" in p or "hedge" in p or "declarative" in p for p in _SCALARS["assertiveness"]),
          str(_SCALARS["assertiveness"]))


def test_the_builder_drops_an_unknown_drives_block():
    """The prefix builder is the ONE place whose default must be to drop rather than carry, and that
    is the opposite of `direct_identity`'s rule on purpose. That function must never silently lose an
    authored field; this one decides what a character may be told about ITSELF, so a block nobody has
    ruled on must not reach the actor by default. A new drives field is a decision, not a merge."""
    print("\n[6] AN UNRULED FIELD DOES NOT REACH THE ACTOR BY DEFAULT")
    ch, _ = _ren()
    ch["baseline"]["drives"]["something_invented_next_month"] = [{"whatever": "a new idea"}]
    ch["baseline"]["drives"]["goals"][0]["a_new_weight"] = 0.9
    stable = _build_stable(ch["fixed"], ch["baseline"])
    blob = json.dumps(stable)
    check("an-unknown-drives-block-is-dropped", "something_invented_next_month" not in blob)
    check("an-unknown-key-inside-a-goal-is-dropped", "a_new_weight" not in blob)
    check("...and-the-goal-itself-is-kept", "bring whoever is with him back" in blob)


def main():
    print("test_prompt_manner.py — the sheet is spent once\n")
    for t in sorted((v for k, v in globals().items()
                     if k.startswith("test_") and callable(v)),
                    key=lambda f: f.__code__.co_firstlineno):
        try:
            t()
        except Exception as e:                       # noqa: BLE001 — a harness reports, never raises
            check("%s RAISED %s" % (t.__name__, type(e).__name__), False, str(e)[:140])
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("FAILED: %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
