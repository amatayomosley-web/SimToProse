"""test_appraiser.py — the two seats: what each is shown, and what each refuses.

`docs/emotion-arithmetic.md` §1 and §7. Two seats, not one, because the outputs have incompatible
blindness contracts — the emotion seat must read the character's private `thought`, and the event
seat must not, because `bonds.act_from_tags` turns its dimensions into what a WITNESS made of the
act (`bonds.witnessed`: presence is not perception).

**THE BLINDNESS ASSERTIONS ARE THE POINT OF THIS SUITE.** Everything else here is parser hygiene. A
prompt builder that quietly starts including the character's current rung, or the direction text the
actor was handed, produces a sensor that reports what is CARRIED rather than what AROSE — and the
receipt step then adds a character to themselves every beat. That failure is invisible from the
output (the readings look plausible) and shows up only as an engine that climbs to the top rung and
stays there. It has to be caught at the prompt.

Each assertion is written against the RENDERED prompt, not against the builder's arguments, for the
reason `tests/test_prompt_sections.py` records: a section-order bug put six sections in the wrong
slots for weeks while every argument was correct.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

import appraiser                                                   # noqa: E402
from src.engine import readings as R                               # noqa: E402
from src.engine import rungs                                       # noqa: E402
from src.engine.records import RecordError                         # noqa: E402

PASS, FAIL = [], []

# An evening at a puppet theatre, invented for this suite (hard rule 1).
ACTION = "He set the marionette down and said the thing about the matinee rota, evenly, and did not look up."
THOUGHT = "One more word out of him and I will say something I cannot take back."
PRESENT = ["idris", "oona"]
PERCEPTS = [{"who": "idris", "what": "standing by the stage"}, {"who": "oona", "what": "seated in the front row"}]


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %s" % detail))
    (PASS if ok else FAIL).append(name)


def _rendered(msgs):
    return "\n".join(m["content"] for m in msgs)


def test_the_emotion_seat_sees_the_interior():
    print("\n[1] THE EMOTION SEAT — sees the thought, and the ladders")
    text = _rendered(appraiser.build_emotion_messages(ACTION, THOUGHT, present=PRESENT, me="ren"))
    check("the-thought-reaches-it", THOUGHT in text,
          "a stoic's climb is only visible from inside")
    check("the-action-reaches-it", ACTION in text)
    check("every-built-path-is-offered", all(p in text for p in rungs.paths()))
    # the ladders must arrive as NAME + BLOCK, not names alone: the seat picks a label and can only
    # do that honestly if it can read what the label means
    check("rung-names-arrive", all(n in text for n in rungs.names_on("DISPLEASURE")))
    check("block-text-arrives", rungs.block_for("DISPLEASURE", 7)[:40].strip() in text)
    check("silence-is-named-as-legitimate", "EMPTY LIST" in text,
          "an idle beat must be an expected answer, not an error")


def test_the_emotion_seat_is_blind_to_what_it_must_not_see():
    print("\n[2] BLINDNESS — the assertions that keep it a sensor")
    text = _rendered(appraiser.build_emotion_messages(ACTION, THOUGHT, present=PRESENT, me="ren"))

    # NO NUMBER. Hard rule 5 binds what reaches a model about a character; a rung index or a float
    # here would hand the seat the scale it is supposed to be reporting in words.
    body = text.split("WHAT YOU RETURN")[0]
    digits = [ln for ln in body.split("\n") if any(c.isdigit() for c in ln)
              and not ln.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7."))]
    check("no-number-in-the-ladders-or-instructions", not digits, digits[:2])

    # THE BUILDER HAS NOWHERE TO PUT STORED STATE. This is a signature assertion, not a text scan:
    # if someone adds an `affect=` or `baseline=` parameter, this fails and they must argue for it.
    import inspect
    params = set(inspect.signature(appraiser.build_emotion_messages).parameters)
    forbidden = params & {"affect", "baseline", "temperament", "profile", "char", "sheet",
                          "rung", "direction", "tags", "packet"}
    check("no-stored-state-parameter", not forbidden, sorted(forbidden))
    check("its-parameters-are-the-beat-and-the-room",
          params == {"action", "thought", "moment", "present", "me"}, sorted(params))


def test_the_event_seat_is_blind_to_the_interior():
    print("\n[3] THE EVENT SEAT — the act only, and that IS its contract")
    text = _rendered(appraiser.build_event_messages(ACTION, present=PRESENT, actor="ren"))
    check("the-action-reaches-it", ACTION in text)
    check("THE-THOUGHT-DOES-NOT", THOUGHT not in text,
          "a rating made with the interior in view is not a bystander's rating")
    check("no-ladder-reaches-it", "DISPLEASURE" not in text,
          "it rates events, not rungs")
    check("the-dimension-vocabulary-arrives", all(d in text for d in appraiser.DIMENSIONS))
    check("the-severity-words-arrive", all(w in text for w in appraiser.SEVERITY_WORDS))

    import inspect
    params = set(inspect.signature(appraiser.build_event_messages).parameters)
    check("it-cannot-be-handed-a-thought", "thought" not in params, sorted(params))

    # THE VOCABULARY IS DERIVED, NOT RESTATED — the defect class CLAUDE.md tabulates seven times
    from src.engine.state import _DIM_TO_PATH
    check("the-vocabulary-is-derived-from-the-engine",
          set(appraiser.DIMENSIONS) == set(_DIM_TO_PATH),
          "%s vs %s" % (sorted(appraiser.DIMENSIONS), sorted(_DIM_TO_PATH)))


def test_the_two_prompts_actually_differ():
    print("\n[4] THE SPLIT IS REAL — same beat, two different prompts")
    a = _rendered(appraiser.build_emotion_messages(ACTION, THOUGHT, present=PRESENT, me="ren"))
    b = _rendered(appraiser.build_event_messages(ACTION, present=PRESENT, actor="ren"))
    check("they-are-not-the-same-prompt", a != b)
    check("only-one-carries-the-interior", (THOUGHT in a) and (THOUGHT not in b))
    check("only-one-carries-the-ladders", ("amok" in a) and ("amok" not in b))
    # determinism: the same beat composes the same prompt twice
    again = _rendered(appraiser.build_emotion_messages(ACTION, THOUGHT, present=PRESENT, me="ren"))
    check("prompt-building-is-deterministic", a == again)


def test_the_emotion_parser_refuses_rather_than_repairs():
    print("\n[5] THE TRUST BOUNDARY — every refusal names a real failure mode")
    ok = '{"readings": [{"path": "DISPLEASURE", "rung": "anger", "about": "idris"}], ' \
         '"lands_on": ["idris"], "confidence": "sure"}'
    rs, lands, conf = appraiser.parse_emotion_reply(ok, percepts=PERCEPTS, present=PRESENT, me="ren")
    check("a-good-reply-parses", len(rs) == 1 and lands == ["idris"] and conf == "sure")

    # AN IDLE BEAT IS VALID AND MUST NOT RAISE — §8's stability argument rests on the seat's silence
    rs, _l, _c = appraiser.parse_emotion_reply('{"readings": [], "lands_on": [], "confidence": "sure"}',
                                               percepts=PERCEPTS, present=PRESENT)
    check("an-empty-readings-list-is-valid", rs == [],
          "refusing an idle beat would train the caller to treat silence as an error")

    # A SELF-BOUND READING — the capability restored 2026-09-09; shame must survive the boundary
    rs, _l, _c = appraiser.parse_emotion_reply(
        '{"readings": [{"path": "DISTASTE", "rung": "revulsion", "about": "ren"}], "confidence": "sure"}',
        percepts=PERCEPTS, present=PRESENT, me="ren")
    check("a-reading-about-the-character-himself-passes", rs and rs[0].about == "ren")

    # A CONCEPT (gate three, 2026-09-11): validated by identity against the closed registry, never
    # against the PerceptSet — sickness is recognised, not seen. An unknown id is refused by code.
    rs, _l, _c = appraiser.parse_emotion_reply(
        '{"readings": [{"path": "WARINESS", "rung": "dread", "about": "concept:sickness"}], "confidence": "sure"}',
        percepts=PERCEPTS, present=PRESENT, me="ren")
    check("a-reading-about-a-registry-concept-passes", rs and rs[0].about == "concept:sickness")
    try:
        appraiser.parse_emotion_reply(
            '{"readings": [{"path": "WARINESS", "rung": "dread", "about": "concept:zebras"}], "confidence": "sure"}',
            percepts=PERCEPTS, present=PRESENT, me="ren")
        check("an-unknown-concept-is-refused-by-code", False, "did NOT raise")
    except RecordError as exc:
        check("an-unknown-concept-is-refused-by-code", "READING_CONCEPT_UNKNOWN" in str(exc), str(exc)[:80])
    check("about_missing-is-measured-never-applied",
          appraiser.missing_concepts('{"readings": [{"path": "WARINESS", "rung": "dread", "about": "", "about_missing": "ghosts"}], "confidence": "sure"}') == ["ghosts"]
          and appraiser.parse_emotion_reply('{"readings": [{"path": "WARINESS", "rung": "dread", "about": "", "about_missing": "ghosts"}], "confidence": "sure"}',
                                            percepts=PERCEPTS, present=PRESENT, me="ren")[0][0].about == "")
    check("the-live-helpers-exist-on-the-seam", callable(appraiser.read_emotion) and callable(appraiser.read_event))
    sys_text = appraiser.build_emotion_messages(ACTION, "a thought", present=PRESENT, me="ren")[0]["content"]
    check("the-seat-is-shown-the-concept-menu", "concept:sickness" in sys_text and "concept:loss_of_a_child" in sys_text)

    for name, raw in (
            ("not-json", "I think he was angry."),
            ("an-unbuilt-path", '{"readings": [{"path": "COURAGE", "rung": "banter"}]}'),
            ("a-cross-path-rung", '{"readings": [{"path": "DISPLEASURE", "rung": "dread"}]}'),
            ("an-invented-rung", '{"readings": [{"path": "DISPLEASURE", "rung": "quite cross"}]}'),
            ("a-NUMERIC-rung", '{"readings": [{"path": "DISPLEASURE", "rung": "7"}]}'),
            ("an-unknown-confidence", '{"readings": [], "confidence": "pretty sure"}'),
            ("about-someone-never-perceived",
             '{"readings": [{"path": "GOODWILL", "rung": "warmth", "about": "joss"}]}'),
            ("lands_on-someone-absent", '{"readings": [], "lands_on": ["joss"]}'),
            ("readings-is-not-a-list", '{"readings": "anger"}')):
        try:
            appraiser.parse_emotion_reply(raw, percepts=PERCEPTS, present=PRESENT, me="ren")
            check(name, False, "did NOT raise")
        except RecordError:
            check(name, True)


def test_the_thermometer_parser():
    """The measurement seat's reader: a lower-case path key is the same ladder (Red Badge on Opus,
    2026-09-11: 36 of 37 thermometer answers were cased that way and the run died on the first);
    an invented rung refuses by a RecordError name, never by an engine error the harness cannot
    catch; a number refuses; a reply without `levels` refuses."""
    print("\
[6b] THE THERMOMETER PARSER")
    low = rungs.names_on("WARINESS")[0]
    out = appraiser.parse_thermometer_reply('{"levels": {"wariness": "%s", "DEFLATION": "%s"}, "confidence": "likely"}'
                                    % (low, rungs.names_on("DEFLATION")[0]))
    check("a-lower-case-path-key-is-the-ladders-own-name", set(out) == {"WARINESS", "DEFLATION"} and out["WARINESS"] == low, out)
    for name, raw, code in (
        ("an-invented-rung-refuses-by-a-record-error-name", '{"levels": {"WARINESS": "courage"}}', "READING_RUNG_NOT_ON_PATH"),
        ("an-unknown-path-refuses-by-a-record-error-name", '{"levels": {"COURAGE": "%s"}}' % low, "READING_RUNG_NOT_ON_PATH"),
        ("a-number-refuses", '{"levels": {"WARINESS": "rung 3"}}', "READING_RUNG_IS_NUMERIC"),
        ("no-levels-refuses", '{"readings": []}', "APPRAISER_REPLY_NOT_JSON"),
    ):
        try:
            appraiser.parse_thermometer_reply(raw)
            check(name, False, "did not raise")
        except RecordError as exc:
            check(name, code in str(exc), str(exc)[:90])


def test_the_event_parser_refuses_rather_than_repairs():
    print("\n[6] THE EVENT BOUNDARY")
    ok = '{"type": "affront", "dimensions": {"social_violation": "mild"}, "durability": "transient"}'
    tags = appraiser.parse_event_reply(ok)
    check("a-good-reply-parses", tags["dimensions"] == {"social_violation": "mild"})
    # THE TYPE IS CLOSED (2026-09-11). The first live beat on a real book answered a phrase here;
    # the parser passed it and consolidation killed the run with TAG_TYPE_UNKNOWN. The seat is now
    # SHOWN the six words the actor is shown, and refuses anything else by name — before the engine.
    from src.engine.consolidation import ACTOR_TAG_TYPES
    rendered = _rendered(appraiser.build_event_messages(ACTION, present=PRESENT, actor="ren"))
    check("the-seat-is-shown-every-closed-type-word",
          all(w in rendered for w in ACTOR_TAG_TYPES) and "exactly ONE word from" in rendered,
          [w for w in ACTOR_TAG_TYPES if w not in rendered])
    check("a-known-type-is-canonicalised",
          appraiser.parse_event_reply('{"type": "Aid", "dimensions": {}}')["type"] == "aid")
    try:
        appraiser.parse_event_reply('{"type": "the weather turned while they talked", "dimensions": {}}')
        check("a-phrase-for-a-type-is-refused-by-name", False, "did NOT raise")
    except RecordError as exc:
        check("a-phrase-for-a-type-is-refused-by-name", "APPRAISER_TYPE_UNKNOWN" in str(exc), str(exc)[:80])
    check("it-emits-the-shape-the-engine-already-reads",
          set(tags) >= {"type", "dimensions", "durability"}, sorted(tags))

    # and it must survive the resolver the ACTOR's own tags go through — one resolver, not two
    from src.engine.severity import normalise_dimensions
    check("severity-words-resolve-through-the-existing-resolver",
          isinstance(normalise_dimensions(dict(tags))["dimensions"]["social_violation"], float))

    for name, raw in (
            ("not-json", "it was rude"),
            ("an-unknown-dimension", '{"dimensions": {"betrayal": "mild"}}'),
            ("a-NUMERIC-severity", '{"dimensions": {"threat": 0.8}}'),
            ("an-invented-severity-word", '{"dimensions": {"threat": "quite bad"}}'),
            ("an-unknown-durability", '{"dimensions": {}, "durability": "forever"}'),
            ("dimensions-is-not-an-object", '{"dimensions": ["threat"]}')):
        try:
            appraiser.parse_event_reply(raw)
            check(name, False, "did NOT raise")
        except RecordError:
            check(name, True)

    # THE QUOTE CHECK (2026-09-18): every `showed` word carries the span of the action that shows it,
    # and the parser holds the seat to it. A gloss is advice; a span the seat has to copy is a claim.
    act = "He set the marionette down and said the thing about the matinee rota, evenly, and did not look up."
    quoted = ('{"type": "affront", "dimensions": {"social_violation": "mild"}, "object": "oona", '
              '"showed": {"affinity": {"word": "curt", "quote": "said the thing about the matinee rota,  EVENLY"}}, '
              '"transfers": [{"what": "the marionette", "from": "self", "to": "oona", "terms": "none"}]}')
    tags = appraiser.parse_event_reply(quoted, objects=PRESENT, action=act)
    check("a-quoted-word-is-priced-and-its-span-kept", abs(tags["showed"]["affinity"] - 0.44) < 1e-9
          and tags["quotes"]["affinity"].startswith("said the thing"), tags)
    # THE TRANSFERS (2026-09-18): a fact the seat reports — what changed hands, from whom, to whom, on what
    # terms — shape-checked here; the engine prices it. The `debt` verdict is refused, like `social`.
    check("a-transfer-row-passes-with-its-thing-quoted", tags["transfers"] == [{"what": "the marionette", "from": "self", "to": "oona", "terms": "none"}], tags.get("transfers"))
    check("the-contract-asks-for-transfers-and-forbids-the-verdict", '"transfers":' in rendered and "Do not write a `debt` key" in rendered)
    for name, raw, code in (
            ("the-debt-verdict-is-refused", '{"type": "aid", "dimensions": {}, "object": "oona", "debt": "gave"}', "APPRAISER_DEBT_RETIRED"),
            ("...inside-showed-too", '{"type": "aid", "dimensions": {}, "object": "oona", "showed": {"debt": "gave"}}', "APPRAISER_DEBT_RETIRED"),
            ("terms-off-the-list-refused", '{"type": "aid", "dimensions": {}, "transfers": [{"what": "the marionette", "from": "self", "to": "oona", "terms": "gift"}]}', "APPRAISER_TERMS_UNKNOWN"),
            ("a-transfer-to-oneself-refused", '{"type": "aid", "dimensions": {}, "transfers": [{"what": "the marionette", "from": "oona", "to": "oona", "terms": "none"}]}', "APPRAISER_TRANSFER_SHAPE"),
            ("a-party-off-the-lists-refused", '{"type": "aid", "dimensions": {}, "transfers": [{"what": "the marionette", "from": "self", "to": "nobody", "terms": "none"}]}', "APPRAISER_TRANSFER_SHAPE"),
            ("a-thing-not-in-the-action-refused", '{"type": "aid", "dimensions": {}, "transfers": [{"what": "the moon", "from": "self", "to": "oona", "terms": "none"}]}', "APPRAISER_FACT_NOT_IN_ACTION")):
        try:
            appraiser.parse_event_reply(raw, objects=PRESENT, action=act)
            check(name, False, "did NOT raise")
        except RecordError as exc:
            check(name, code in str(exc), str(exc)[:90])
    check("the-contract-shows-the-quoted-skeleton-and-the-rule",
          '"quote":' in rendered and "QUOTES ITS EVIDENCE" in rendered)
    for name, raw, action, code in (
            ("a-bare-word-is-refused", '{"type": "affront", "dimensions": {}, "object": "oona", "showed": {"affinity": "curt"}}', act, "APPRAISER_QUOTE_MISSING"),
            ("an-empty-quote-is-refused", '{"type": "affront", "dimensions": {}, "object": "oona", "showed": {"affinity": {"word": "curt", "quote": ""}}}', act, "APPRAISER_QUOTE_MISSING"),
            ("a-quote-not-in-the-action-is-refused", '{"type": "affront", "dimensions": {}, "object": "oona", "showed": {"affinity": {"word": "curt", "quote": "threw the marionette"}}}', act, "APPRAISER_FACT_NOT_IN_ACTION")):
        try:
            appraiser.parse_event_reply(raw, objects=PRESENT, action=action)
            check(name, False, "did NOT raise")
        except RecordError as exc:
            check(name, code in str(exc), str(exc)[:90])
    check("no-action-skips-containment-but-still-wants-the-quote",
          appraiser.parse_event_reply('{"type": "affront", "dimensions": {}, "object": "oona", "showed": {"affinity": {"word": "curt", "quote": "anything"}}}', objects=PRESENT)["quotes"] == {"affinity": "anything"})


def test_the_told_list_derives_the_rung_the_seat_is_not_offered():
    print("\n[6c] TOLD — the trust rung the seat is not offered is derived from a fact it reports")
    # THE SIXTH TRUST RUNG (2026-09-18, gate seat-told). Three instruments on the same 28 beats had the
    # seat naming it on 11, 9 and 9 of 14 against a 4-8 band: the span it quoted was in the text and did
    # not show the word. The seat now reports what was SAID at a COST to the teller (fault | exposure |
    # none), quoted, and the parser derives the rung; the seat's own trust word stands; the word itself
    # is refused. Invented beat, invented names.
    from src.engine import severity as S
    from src.engine.consolidation import ACTOR_TAG_TYPES
    rendered = _rendered(appraiser.build_event_messages(ACTION, present=PRESENT, actor="ren"))
    rubric = S.act_rubric("trust")
    check("the-derived-rung-is-not-offered-on-the-trust-ladder", "straight —" not in rubric and "derived from `told`" in rubric, rubric)
    check("the-other-seven-trust-words-stay", all(("%s —" % w) in rubric for w in S.ACT_WORDS["trust"] if w != "straight"))
    check("the-contract-asks-for-told-with-a-closed-cost", '"told":' in rendered and '"fault" | "exposure" | "none"' in rendered)
    act = ("Linnea hung the puppet up and said it plain: I tangled the strings before the matinee, the lost scene is mine. "
           "Then she said she had never worked a puppet in front of children before this spring, which nobody backstage had known, and asked for the scissors.")
    base = '{"type": "mundane", "dimensions": {"mastery": "slight"}, "durability": "transient", "object": "oona", '
    fault = base + '"told": [{"what": "I tangled the strings before the matinee", "to": "oona", "cost": "fault"}]}'
    tags = appraiser.parse_event_reply(fault, objects=PRESENT, action=act)
    check("a-fault-owned-derives-the-sixth-rung-with-its-span-as-the-quote",
          abs(tags["showed"]["trust"] - 0.66) < 1e-9 and tags["quotes"]["trust"] == "I tangled the strings before the matinee", tags)
    check("the-told-row-is-kept-on-the-tags", tags["told"] == [{"what": "I tangled the strings before the matinee", "to": "oona", "cost": "fault"}], tags.get("told"))
    exposure = base + '"told": [{"what": "she had never worked a puppet in front of children before this spring", "to": "oona", "cost": "exposure"}]}'
    check("an-exposure-named-derives-it-too",
          abs(appraiser.parse_event_reply(exposure, objects=PRESENT, action=act)["showed"]["trust"] - 0.66) < 1e-9)
    none = base + '"told": [{"what": "asked for the scissors", "to": "oona", "cost": "none"}]}'
    t2 = appraiser.parse_event_reply(none, objects=PRESENT, action=act)
    check("cost-none-derives-nothing", "trust" not in (t2.get("showed") or {}) and t2["told"][0]["cost"] == "none", t2)
    loyal = base + ('"showed": {"trust": {"word": "loyal", "quote": "the lost scene is mine"}}, '
                    '"told": [{"what": "I tangled the strings before the matinee", "to": "oona", "cost": "fault"}]}')
    t3 = appraiser.parse_event_reply(loyal, objects=PRESENT, action=act)
    check("the-seats-own-higher-trust-word-stands-over-the-derivation",
          abs(t3["showed"]["trust"] - 0.78) < 1e-9 and t3["quotes"]["trust"] == "the lost scene is mine", t3)
    # THE LIFT (measured 2026-09-18 on the re-answer): the seat wrote `dependable` beside an owned fault on
    # three beats; the boundary between that rung and the derived one IS the told fact, so the fact lifts
    # it. A cold word is never touched: the derivation never lowers and never warms a lie.
    dep = base + ('"showed": {"trust": {"word": "dependable", "quote": "hung the puppet up"}}, '
                  '"told": [{"what": "I tangled the strings before the matinee", "to": "oona", "cost": "fault"}]}')
    t4 = appraiser.parse_event_reply(dep, objects=PRESENT, action=act)
    check("a-warm-word-below-the-rung-is-lifted-by-a-told-at-a-cost",
          abs(t4["showed"]["trust"] - 0.66) < 1e-9 and t4["quotes"]["trust"] == "I tangled the strings before the matinee", t4)
    cold = base + ('"showed": {"trust": {"word": "dishonest", "quote": "hung the puppet up"}}, '
                   '"told": [{"what": "I tangled the strings before the matinee", "to": "oona", "cost": "fault"}]}')
    t5 = appraiser.parse_event_reply(cold, objects=PRESENT, action=act)
    check("a-cold-word-stands-the-derivation-never-warms-it", abs(t5["showed"]["trust"] - 0.22) < 1e-9, t5)
    for name, raw, code in (
            ("naming-the-derived-word-is-refused", base + '"showed": {"trust": {"word": "straight", "quote": "the lost scene is mine"}}}', "APPRAISER_WORD_DERIVED"),
            ("a-free-text-cost-is-refused", base + '"told": [{"what": "the lost scene is mine", "to": "oona", "cost": "candour"}]}', "APPRAISER_COST_UNKNOWN"),
            ("a-told-span-not-in-the-action-is-refused", base + '"told": [{"what": "I never touched the strings", "to": "oona", "cost": "fault"}]}', "APPRAISER_FACT_NOT_IN_ACTION"),
            ("a-told-row-without-to-is-refused", base + '"told": [{"what": "the lost scene is mine", "cost": "fault"}]}', "APPRAISER_TOLD_SHAPE"),
            ("a-told-row-to-nobody-on-the-lists-is-refused", base + '"told": [{"what": "the lost scene is mine", "to": "the stage manager", "cost": "fault"}]}', "APPRAISER_TOLD_SHAPE"),
            ("told-is-not-a-list-is-refused", base + '"told": {"what": "the lost scene is mine", "to": "oona", "cost": "fault"}}', "APPRAISER_TOLD_SHAPE"),
            ("a-costly-told-with-no-object-is-refused", '{"type": "mundane", "dimensions": {}, "told": [{"what": "the lost scene is mine", "to": "oona", "cost": "fault"}]}', "APPRAISER_SHOWED_WITHOUT_OBJECT")):
        try:
            appraiser.parse_event_reply(raw, objects=PRESENT, action=act)
            check(name, False, "did NOT raise")
        except RecordError as exc:
            check(name, code in str(exc), str(exc)[:90])
    check("an-empty-told-list-is-the-usual-answer-and-carries-nothing",
          "told" not in appraiser.parse_event_reply(base + '"told": []}', objects=PRESENT, action=act))


def test_the_attribution_field_is_optional_and_quote_checked():
    print("\n[6d] ATTRIBUTION — the law's fifth input: optional, closed, quote-checked like showed")
    from src.engine import severity as S
    from src.engine import bonds as B
    check("malice-and-unknown-are-not-in-the-offered-set",
          "malice" not in S.ATTRIBUTION_WORDS and "unknown" not in S.ATTRIBUTION_WORDS
          and set(S.ATTRIBUTION_WORDS) == {"intent", "negligence", "coerced", "accident"}, S.ATTRIBUTION_WORDS)

    rendered = _rendered(appraiser.build_event_messages(ACTION, present=PRESENT, actor="ren"))
    check("the-contract-names-the-four-words", all(w in rendered for w in S.ATTRIBUTION_WORDS), S.ATTRIBUTION_WORDS)
    check("the-contract-states-the-omission-rule",
          "OMITTING IT IS THE USUAL ANSWER" in rendered and "prices as fully intended" in rendered, rendered)
    check("the-skeleton-carries-the-optional-field",
          '"attribution":' in rendered and '"word": "<intent|negligence|coerced|accident>"' in rendered)

    act = ACTION
    base = '{"type": "affront", "dimensions": {"social_violation": "mild"}, "durability": "transient"}'

    good = base[:-1] + ', "attribution": {"word": "accident", "quote": "did not look up"}}'
    tags = appraiser.parse_event_reply(good, action=act)
    check("a-closed-word-with-a-quote-in-the-action-parses-through", tags.get("attribution") == "accident", tags)

    # OMISSION IS THE USUAL ANSWER: no key at all -> no key in the parsed tags, and act_from_tags then
    # reads "unknown" (bonds._ATTRIBUTION: full weight) — exactly what an untagged act always read.
    plain = appraiser.parse_event_reply(base, action=act)
    check("an-omitted-attribution-carries-no-key", "attribution" not in plain, plain)
    # act_from_tags reads resolved (float) dimensions, same as the drivers: normalise_dimensions
    # runs between the seat and the fold (scene.py/direct.py: `normalise_dimensions(read_event(...))`).
    seat_shaped = dict(S.normalise_dimensions(plain), object="oona", showed={"affinity": 0.44})
    stamped = B.act_from_tags(seat_shaped, "ren", "oona")
    check("act_from_tags-then-reads-the-omission-as-unknown", stamped["attribution"] == "unknown", stamped)

    for name, raw, code in (
            ("malice-is-not-offered-and-is-refused",
             base[:-1] + ', "attribution": {"word": "malice", "quote": "did not look up"}}', "APPRAISER_ATTRIBUTION_UNKNOWN"),
            ("unknown-is-not-offered-either",
             base[:-1] + ', "attribution": {"word": "unknown", "quote": "did not look up"}}', "APPRAISER_ATTRIBUTION_UNKNOWN"),
            ("a-quote-the-action-lacks-is-refused",
             base[:-1] + ', "attribution": {"word": "accident", "quote": "threw the marionette across the room"}}', "APPRAISER_FACT_NOT_IN_ACTION"),
            ("intent-with-an-empty-quote-is-refused",
             base[:-1] + ', "attribution": {"word": "intent", "quote": ""}}', "APPRAISER_QUOTE_MISSING"),
            ("intent-with-no-quote-key-at-all-is-refused",
             base[:-1] + ', "attribution": {"word": "intent"}}', "APPRAISER_QUOTE_MISSING")):
        try:
            appraiser.parse_event_reply(raw, action=act)
            check(name, False, "did NOT raise")
        except RecordError as exc:
            check(name, code in str(exc), str(exc)[:100])


def test_the_stub_is_gone():
    print("\n[7] THE RATCHET — the p=1 sensor does not survive the seat")
    check("stub_readings-is-deleted", not hasattr(R, "stub_readings"),
          "it reported the rung the character was ALREADY at: every beat re-adds the carried state")
    check("parse-took-its-place", callable(getattr(R, "parse", None)))


def main():
    for t in (test_the_emotion_seat_sees_the_interior,
              test_the_emotion_seat_is_blind_to_what_it_must_not_see,
              test_the_event_seat_is_blind_to_the_interior,
              test_the_two_prompts_actually_differ,
              test_the_emotion_parser_refuses_rather_than_repairs,
              test_the_thermometer_parser,
              test_the_event_parser_refuses_rather_than_repairs,
              test_the_told_list_derives_the_rung_the_seat_is_not_offered,
              test_the_attribution_field_is_optional_and_quote_checked,
              test_the_stub_is_gone):
        t()
    print("\n%d / %d passed" % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        print("VERDICT: FAIL -> %s" % FAIL)
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
