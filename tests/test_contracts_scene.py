#!/usr/bin/env python3
"""test_contracts_scene.py — the scene file, declared once (gate scene-contract, 2026-09-25).

THE CONTRACTS PLAN, G2 for the scene file (the owner's "Go"; agreed with Symphony on the board, convo #4). The scene
linter only ever saw a scene after the loader had rewritten it - severity words already numbers, `elapsed` already
refused, a bad voice already an exit - and it checked nothing of `pov`, `subject`'s shape, `voice` or `knowledge`,
while it accepted a cast id the run refuses; the docs' example scene files used `elapsed` and left out `at`.
src/engine/contracts_scene.py declares every key; lint_scene checks the file as written.

  [1] a well-formed scene file is clean
  [2] each key refused in the words of the module that owns it
  [3] what reaches nothing, and what is retired
  [4] lint_scene: the file as written, the cast as the run has it, the loader's own refusal
  [5] the table is generated; the docs' example scene files carry `at` and no `elapsed`

Script-style: check(), main(), exit code. Stdlib only. Every scene here is invented.
"""
import copy
import json
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.engine import contracts, contracts_scene, systems          # noqa: E402

FAILS = []
SCENE = {"name": "the-marquee", "at": {"day": 1, "time": "09:00"}, "lasts": "1h",
         "situation": "Rain is coming down hard and the marquee roof has started to sag over the cake tables.",
         "subject": ["pru", "stallholders"], "location": "the-marquee", "pov": "pru", "voice": "close-third",
         "knowledge": "pov", "props": ["a bucket", "a broom", "a folding ladder"],
         "opening_tags": {"dimensions": {"threat": "moderate", "care_relevant": 0.4}},
         "cast": [{"id": "pru", "drive": "keep the judging table dry until the prizes are given"},
                  {"id": "ned", "drive": "get the cakes judged before the rain ruins them"}],
         "condition": [{"char": "pru", "energy": "tired"}]}


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else " - %s" % (detail,)))
    if not ok:
        FAILS.append("%s: %s" % (name, detail))


def run(cfg, on=None):
    return contracts.check(cfg, contracts_scene.SCENE, systems.defaults() if on is None else on)


def at(findings, path, severity=None):
    return [f for f in findings if f["path"] == path and (severity is None or f["severity"] == severity)]


def errors_at(cfg, path, **k):
    return at(run(cfg, **k), path, "error")


def clean():
    print("[1] a well-formed scene file")
    got = run(SCENE)
    check("nothing-to-report", not got, got)


def refused():
    print("[2] each key refused in its owner's words")
    cases = (
        ("at", {"day": 1, "time": "25:00"}, "CLOCK_AT_TIME_INVALID"),
        ("lasts", "a while", "CLOCK_SPAN_NOT_A_SPAN"),
        ("subject", "pru", "must be [id, group]"),
        ("pov", "wren", "not in this scene's cast"),
        ("voice", "omniscient-ish", "NARRATION_VOICE_UNKNOWN"),
        ("knowledge", "everything", "NARRATION_KNOWLEDGE_UNKNOWN"),
        ("condition", [{"char": "pru", "energy": "exhausted"}], "not one of"),
        ("condition", [{"char": "wren", "energy": "tired"}], "not in this scene's cast"),
        ("attachments", [{"char": "pru", "entity": "loc.the-marquee", "relation": "adores"}], "not one of"),
    )
    for key, value, want in cases:
        cfg = copy.deepcopy(SCENE)
        cfg[key] = value
        path = key + ("[]" if key == "attachments" else "")
        f = errors_at(cfg, path)
        check("%s=%r" % (key, value), f and want in f[0]["message"], f or run(cfg))
    cfg = copy.deepcopy(SCENE)
    cfg["opening_tags"]["dimensions"] = {"threat": "overwhelming", "dread": 0.5, "loss": 1.4}
    f = errors_at(cfg, "opening_tags.dimensions")
    msg = f[0]["message"] if f else ""
    # each part matched on its own finding's words: "loss" alone also sits in the list of legal dimensions the
    # unknown key's message prints, and a check on it passed with the range check deleted (mutant X5)
    check("dimensions:-an-off-ladder-word,-an-unknown-key,-a-number-out-of-range", "threat = 'overwhelming'" in msg
          and "'dread' is not one of the seven" in msg and "loss = 1.4" in msg, f)
    cfg = copy.deepcopy(SCENE)
    cfg["cast"].append({"id": "wren", "drive": ""})
    check("a-cast-member-with-no-drive", errors_at(cfg, "cast[]"))
    f = errors_at(copy.deepcopy(SCENE), "condition", on=systems.for_book({"systems": {"condition": False}}))
    check("a-condition-in-a-book-without-the-system", f and "switches the condition system off" in f[0]["message"], f)
    cfg = copy.deepcopy(SCENE)
    cfg["subject"] = [None, None]
    check("[null,-null]-is-no-one,-said-on-purpose", not errors_at(cfg, "subject"))
    for key in ("situation", "cast", "at"):
        cfg = copy.deepcopy(SCENE)
        del cfg[key]
        check("%s-is-required" % key, errors_at(cfg, key))


def retired_and_unread():
    print("[3] what is retired, and what reaches nothing")
    cfg = copy.deepcopy(SCENE)
    cfg["elapsed"] = 60
    f = at(run(cfg), "elapsed", "retired")
    check("elapsed-is-refused-in-favour-of-at-and-lasts", f and "lasts" in f[0]["message"] and "refuse" in f[0]["message"], f)
    cfg = copy.deepcopy(SCENE)
    cfg["opening_tags"].update({"type": "threat", "durability": "transient", "act": "sell_before_judging"})
    got = run(cfg)
    for key in ("type", "durability", "act"):
        check("opening_tags.%s-reaches-nothing" % key, at(got, "opening_tags." + key, "unread"), got)
    cfg = copy.deepcopy(SCENE)
    cfg["subjet"] = ["pru", None]
    f = at(run(cfg), "subjet", "unknown")
    check("an-undeclared-key-with-a-did-you-mean", f and "did you mean 'subject'" in f[0]["message"], f)


def lint():
    print("[4] lint_scene")
    import lint_scene
    world = {"world": "w", "people": [{"id": "pru", "what": "the stall holder"}, {"id": "ned", "what": "the judge"},
                                      {"id": "wren", "what": "a passer-by"}],
             "locations": [{"id": "the-marquee", "what": "the fete marquee"}], "laws": []}
    chars = {"pru": {}, "ned": {}}
    e, _w, _u = lint_scene.lint_cfg(copy.deepcopy(SCENE), world, chars)
    check("the-clean-file-lints-clean", e == [], e)
    cfg = copy.deepcopy(SCENE)
    cfg["cast"].append({"id": "wren", "drive": "watch the rain"})
    e, _w, _u = lint_scene.lint_cfg(cfg, world, chars)
    check("a-person-who-is-not-a-character-is-refused,-as-the-run-refuses-them",
          any("'wren' is not a character in this book" in x for x in e), e)
    tmp = tempfile.mkdtemp(prefix="scene_contract_")
    from test_systems import _book
    book = _book(tmp)
    raw = copy.deepcopy(SCENE)
    raw["cast"] = [{"id": "mira", "drive": "keep the lamp lit"}, {"id": "ada", "drive": "get the boat ready"}]
    raw.update(pov="mira", subject=["mira", None], location=None, condition=[{"char": "mira", "energy": "tired"}])
    raw.pop("location")
    raw["elapsed"] = 30
    raw["voice"] = "omniscient-ish"
    path = os.path.join(tmp, "scene.json")
    json.dump(raw, open(path, "w", encoding="utf-8"))
    r = subprocess.run([sys.executable, os.path.join("scripts", "lint_scene.py"), "--book", book, "--scene", path],
                       cwd=REPO, capture_output=True, text=True)
    out = r.stdout + r.stderr
    check("the-file-as-written:-elapsed-and-a-bad-voice-both-reported,-no-traceback",
          "elapsed" in out and "NARRATION_VOICE_UNKNOWN" in out and "Traceback" not in out and r.returncode == 1, out[-800:])


def docs():
    print("[5] the table, and the docs' example scene files")
    r = subprocess.run([sys.executable, os.path.join("scripts", "gen_contracts.py"), "--check"], cwd=REPO,
                       capture_output=True, text=True)
    check("the-blueprint's-table-matches-the-declarations", r.returncode == 0, r.stdout + r.stderr)
    for rel in ("docs/authoring/BLUEPRINT-scene.md", "docs/template-scene-blueprint.md", "docs/guide-continuing-the-story.md"):
        text = open(os.path.join(REPO, rel), encoding="utf-8").read()
        shapes = [b for b in re.findall(r"```json\n(.*?)```", text, re.S) if '"situation"' in b and '"cast"' in b]
        check("%s:-every-example-scene-carries-at-and-no-elapsed" % rel,
              bool(shapes) and all('"at"' in b and '"elapsed"' not in b for b in shapes), [b[:80] for b in shapes])


def main():
    clean()
    refused()
    retired_and_unread()
    lint()
    docs()
    print("\n%s: %d failure(s)" % ("FAIL" if FAILS else "OK", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
