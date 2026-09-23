#!/usr/bin/env python3
"""test_orc_hooks.py — the orchestrator's three hooks, each with its corrupt control.

THE POINT OF THIS SUITE. Every guard in this repo that turned out to be dead
looked exactly like a live one from the outside: it ran, it exited 0, nothing
complained. The only thing that distinguishes a gate from a decoration is a test
that proves it DENIES on the bad input — so every `test_corrupt_*` below asserts a
denial, and if any of them starts passing the input, the gate has become theatre
and this suite must go red.

The hooks are exercised the way the harness invokes them: as SUBPROCESSES, with
the event payload on stdin. Testing the functions directly would skip the exact
seam (json in, permissionDecision out) most likely to break.

  citation_gate     PreToolUse  — no ungrounded fact becomes an artifact
  beat_blind_guard  PreToolUse  — the simulator never learns the intended beat
  ground_from_book  UserPromptSubmit — facts reach the model before it answers

Stdlib only, script-style. Exit 0 = all pass.
"""
import json
import re
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import db                                        # noqa: E402

HOOKS = os.path.join(REPO, ".claude", "hooks")
CITE = os.path.join(HOOKS, "citation_gate.py")
BEAT = os.path.join(HOOKS, "beat_blind_guard.py")
GROUND = os.path.join(HOOKS, "ground_from_book.py")

RUN = "run-hooks"


# --- harness simulation ----------------------------------------------------

def _fire(script, payload, env=None):
    """Invoke a hook the way the harness does. -> (stdout, stderr)."""
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run([sys.executable, script], input=json.dumps(payload),
                       capture_output=True, text=True, env=e, timeout=60)
    return p.stdout, p.stderr


def _denied(out):
    """True when the hook returned a DENY decision."""
    try:
        d = json.loads(out or "{}")
    except ValueError:
        return False
    return (d.get("hookSpecificOutput") or {}).get("permissionDecision") == "deny"


def _write_payload(path, content):
    return {"tool_name": "Write", "tool_input": {"file_path": path, "content": content}}


def _envelope(*tokens):
    return ("prose above\n\n```json\n%s\n```\n"
            % json.dumps({"kind": "REPORT",
                          "claims": [{"mode": "cited", "cite": list(tokens)}]}))


# --- a real book on disk, with a real run ----------------------------------

def _book(tmp):
    """<tmp>/thebook/{world,runs}/ with a chronicle holding one citable turn."""
    book = os.path.join(tmp, "thebook")
    os.makedirs(os.path.join(book, "world"))
    os.makedirs(os.path.join(book, "runs"))
    con = db.connect(os.path.join(book, "runs", "thebook.db"))
    con.execute("INSERT INTO runs(run_id, created_at, status, config) VALUES(?,?,?,?)",
                (RUN, "2026-07-24T00:00:00Z", "active",
                 json.dumps({"catalog_version": 1})))
    con.execute("INSERT INTO turns(run_id, turn, actor, thought, action, tags, validation, "
                "committed_at) VALUES(?,?,?,?,?,?,?,?)",
                (RUN, 7, "wren", "t", "a", "{}", "{}", "2026-07-24T00:00:00Z"))
    con.commit()
    con.close()
    return book


def _book_with_laws(tmp):
    """Same, but the run PINS a bible carrying laws — so the grounding hook has
    something real to retrieve and rank against the prompt."""
    from src.engine import bible                                 # noqa: E402
    book = os.path.join(tmp, "lawbook")
    os.makedirs(os.path.join(book, "world"))
    os.makedirs(os.path.join(book, "runs"))
    con = db.connect(os.path.join(book, "runs", "lawbook.db"))
    world = {"world": "Lawbook",
             "switches": {"magic": False, "divine": False, "beings": False},
             "laws": [{"id": "curfew", "domain": "legal", "modality": "FORBIDS",
                       "statement": "No one may walk the streets after the third bell.",
                       "act": "move", "teeth": "the watch detains you until dawn"}]}
    chars = {"wren": {"fixed": {"name": "Wren"}, "baseline": {}, "current": {}}}
    fp = bible.build(con, world, chars)          # projects curfew + the 5 defaults
    con.execute("INSERT INTO runs(run_id, created_at, status, config) VALUES(?,?,?,?)",
                (RUN, "2026-07-24T00:00:00Z", "active",
                 json.dumps({"catalog_version": 1, bible.CONFIG_KEY: fp})))
    con.commit()
    con.close()
    return book


# === citation_gate =========================================================

def test_a_write_outside_a_book_is_not_this_gates_business(tmp):
    out, _ = _fire(CITE, _write_payload(os.path.join(tmp, "notes.md"), "anything"))
    assert not _denied(out), out


def test_a_non_write_tool_is_ignored(tmp):
    out, _ = _fire(CITE, {"tool_name": "Read", "tool_input": {"file_path": "x/runs/y.md"}})
    assert not _denied(out), out


def test_a_process_note_without_an_envelope_is_allowed(tmp):
    book = _book(tmp)
    out, _ = _fire(CITE, _write_payload(os.path.join(book, "runs", "production-journal.md"),
                                        "Ran three turns. Beat did not land."))
    assert not _denied(out), out


def test_corrupt_a_canon_note_with_no_envelope_is_DENIED(tmp):
    """THE CONTROL for absence. A world-fact written into a canon-bearing note
    with no provenance is exactly what a later turn would read back as truth."""
    book = _book(tmp)
    out, _ = _fire(CITE, _write_payload(os.path.join(book, "runs", "canon-ledger.md"),
                                        "The mill burned on the third night."))
    assert _denied(out), "a canon note with no envelope was allowed through: %r" % out


def test_corrupt_an_unresolved_citation_is_DENIED(tmp):
    """THE CONTROL. `turn:999` does not exist in the fixture run. If this ever
    passes, the gate is decoration."""
    book = _book(tmp)
    out, _ = _fire(CITE, _write_payload(os.path.join(book, "runs", "notes.md"),
                                        _envelope("turn:999")))
    assert _denied(out), "an unresolvable citation was allowed: %r" % out


def test_a_resolved_citation_is_allowed(tmp):
    """The paired positive. Without it, a gate that denies everything looks
    identical to a gate that works."""
    book = _book(tmp)
    out, _ = _fire(CITE, _write_payload(os.path.join(book, "runs", "notes.md"),
                                        _envelope("turn:7")))
    assert not _denied(out), "a resolvable citation was denied: %r" % out


def test_an_unverifiable_citation_does_NOT_deny(tmp):
    """The rule a reimplementation would get wrong. `chronicle:` has no store,
    which means NO CHECKER — not a negative verdict. Denying here would turn a
    missing store into a fabricated 'false'."""
    book = _book(tmp)
    out, err = _fire(CITE, _write_payload(os.path.join(book, "runs", "notes.md"),
                                          _envelope("chronicle:the-long-winter")))
    assert not _denied(out), "an unverifiable citation was treated as a denial: %r" % out
    assert "unverifiable" in err.lower(), "the gap was not surfaced: %r" % err


def test_corrupt_a_malformed_envelope_is_DENIED(tmp):
    book = _book(tmp)
    bad = "```json\n{not json at all,,}\n```"
    out, _ = _fire(CITE, _write_payload(os.path.join(book, "runs", "canon-ledger.md"), bad))
    assert _denied(out), "an unparseable envelope was allowed: %r" % out


def test_corrupt_a_missing_db_DENIES_rather_than_passing(tmp):
    """Fail-closed. A gate that cannot run must say so, not wave the write
    through — that is the dead-guard shape this whole suite exists to prevent."""
    book = os.path.join(tmp, "bookless")
    os.makedirs(os.path.join(book, "runs"))
    out, _ = _fire(CITE, _write_payload(os.path.join(book, "runs", "notes.md"),
                                        _envelope("turn:7")))
    assert _denied(out), "the gate passed a write while unable to check it: %r" % out


# === beat_blind_guard ======================================================

def test_corrupt_the_intended_beat_reaching_the_simulator_is_DENIED(tmp):
    """THE WALL. A character told the outcome produces it, and the honest
    refusal becomes unreachable.

    Runs against BOTH spawn tool names. The first version of this test used only
    "Task" — the name I assumed — and passed while the guard was dead, because a
    captured payload later showed the harness reports "Agent". The fixture and
    the code shared one wrong assumption and the suite could not see it."""
    for tool in ("Task", "Agent"):
        for leak in ("The intended outcome is that she refuses the offer.",
                     "Beat: Wren decides to stay.",
                     "She should end up leaving the quay.",
                     "We need her to confess before the bell.",
                     "Place the lantern so that she will follow him."):
            out, _ = _fire(BEAT, {"tool_name": tool,
                                  "tool_input": {"subagent_type": "character-simulator",
                                                 "description": "act one turn",
                                                 "prompt": leak}})
            assert _denied(out), "beat leaked via %s: %r -> %r" % (tool, leak, out)


def test_the_wall_matches_the_REAL_captured_payload(tmp):
    """Not an invented fixture. These are the exact keys a live spawn delivered:
    tool_name 'Agent', tool_input {description, prompt, run_in_background,
    subagent_type}. If the harness changes shape, this is the test that notices."""
    real = {"tool_name": "Agent",
            "tool_input": {"description": "act one turn",
                           "prompt": "The intended outcome is that she stays.",
                           "run_in_background": True,
                           "subagent_type": "character-simulator"}}
    out, _ = _fire(BEAT, real)
    assert _denied(out), "the wall did not fire on a real spawn payload: %r" % out


def test_a_clean_circumstance_reaches_the_simulator(tmp):
    out, _ = _fire(BEAT, {"tool_name": "Task",
                          "tool_input": {"subagent_type": "character-simulator",
                                         "description": "act one turn",
                                         "prompt": "A stranger sets a lantern on the quay "
                                                   "and waits. It is past the third bell."}})
    assert not _denied(out), "a clean circumstance was blocked: %r" % out


def test_the_wall_is_scoped_to_the_simulator(tmp):
    """The director is SUPPOSED to know the beat. A guard that denied this would
    be switched off within a day."""
    out, _ = _fire(BEAT, {"tool_name": "Task",
                          "tool_input": {"subagent_type": "director",
                                         "description": "plan the beat",
                                         "prompt": "The intended outcome is that she "
                                                   "refuses the offer."}})
    assert not _denied(out), "the wall fired on the director: %r" % out


def test_a_non_task_tool_is_ignored_by_the_wall(tmp):
    out, _ = _fire(BEAT, {"tool_name": "Bash", "tool_input": {"command": "the beat is: x"}})
    assert not _denied(out), out


def test_the_write_gate_matches_the_REAL_captured_payload(tmp):
    """Also captured live: tool_name 'Write', tool_input {content, file_path}.
    The gate reads exactly those two keys."""
    book = _book(tmp)
    real = {"tool_name": "Write",
            "tool_input": {"file_path": os.path.join(book, "runs", "canon-ledger.md"),
                           "content": "The mill burned on the third night."}}
    out, _ = _fire(CITE, real)
    assert _denied(out), "the citation gate did not fire on a real write payload: %r" % out


# === ground_from_book ======================================================

def test_grounding_never_blocks_a_turn(tmp):
    """Fail-OPEN, opposite of the write gates. A missing injection costs an
    ungrounded answer; a denial costs the conversation."""
    out, _ = _fire(GROUND, {"prompt": "what happened last scene?"},
                   env={"SWE_ACTIVE_BOOK": ""})
    assert not _denied(out), out
    assert "No active book" in out, out


def test_grounding_says_so_when_there_is_nothing_to_cite(tmp):
    """Silence would let the model assume it was grounded. It must announce the
    absence instead."""
    book = _book(tmp)
    out, _ = _fire(GROUND, {"prompt": "what laws bind her?"},
                   env={"SWE_ACTIVE_BOOK": book})
    assert "ACTIVE BOOK" in out, out
    assert "pinned no bible" in out or "NO laws" in out, out


def test_grounding_surfaces_the_laws_in_force(tmp):
    book = _book_with_laws(tmp)
    out, _ = _fire(GROUND, {"prompt": "what is going on"}, env={"SWE_ACTIVE_BOOK": book})
    assert "LAWS IN FORCE" in out, out
    assert "curfew" in out and "the watch detains you" in out, out


def test_grounding_is_query_aware(tmp):
    """The whole reason UserPromptSubmit beats a static preamble: the hook reads
    the question, so the context is about what was ASKED. If both prompts produce
    identical output the retrieval is wallpaper and this must fail."""
    book = _book_with_laws(tmp)
    flying, _ = _fire(GROUND, {"prompt": "could she fly across the water"},
                      env={"SWE_ACTIVE_BOOK": book})
    curfew, _ = _fire(GROUND, {"prompt": "is walking after the bell allowed"},
                      env={"SWE_ACTIVE_BOOK": book})

    assert flying != curfew, "identical context for different questions — not query-aware"

    marker = "bearing on what was just asked"
    fly_head = flying.split(marker)[1].split("also in force")[0]
    cur_head = curfew.split(marker)[1].split("also in force")[0]
    assert "no-flight" in fly_head, "the flight question did not surface the flight law: %r" % fly_head
    assert "curfew" in cur_head, "the curfew question did not surface the curfew law: %r" % cur_head
    assert "curfew" not in fly_head, "the flight question promoted an unrelated law: %r" % fly_head


# === the wiring itself =====================================================

def test_every_hook_the_skill_declares_actually_exists(tmp):
    """THE FOOT-GUN GUARD. The skill declares its hooks by path. If a path is
    wrong the harness runs python against a missing file, python exits non-zero,
    and a non-zero PreToolUse exit is a DENY — one typo blocks every tool call in
    the session. A path typo must fail HERE, not there."""
    skill = os.path.join(REPO, ".claude", "skills", "showrunner", "SKILL.md")
    assert os.path.exists(skill), skill
    with open(skill, encoding="utf-8") as f:
        head = f.read().split("---")[1]

    declared = re.findall(r'command:\s*python\s+"([^"]+)"', head)
    assert declared, "the skill declares no hook commands: %r" % head

    for path in declared:
        # ${CLAUDE_PROJECT_DIR} is the repo root at runtime
        real = path.replace("${CLAUDE_PROJECT_DIR}", REPO).replace("\\", "/")
        assert os.path.exists(real), (
            "skill frontmatter points at a hook that does not exist: %s -> %s" % (path, real))

    for name in ("ground_from_book.py", "citation_gate.py", "beat_blind_guard.py"):
        assert any(name in d for d in declared), "%s is built but never wired" % name


def test_every_hook_survives_garbage_on_stdin(tmp):
    """The harness owns the payload shape. A hook that crashes on an unexpected
    one exits non-zero, and for the two PreToolUse hooks that means denying
    everything."""
    for script in (CITE, BEAT, GROUND):
        for junk in ("", "not json", "[]", '{"tool_name": null}'):
            p = subprocess.run([sys.executable, script], input=junk,
                               capture_output=True, text=True, timeout=60)
            assert p.returncode == 0, (
                "%s exited %d on %r — a non-zero PreToolUse exit is a DENY"
                % (os.path.basename(script), p.returncode, junk))


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        tmp = tempfile.mkdtemp(prefix="swe_orchooks_")
        try:
            t(tmp)
            print("  PASS  %s" % t.__name__)
        except Exception as e:
            failed += 1
            print("  FAIL  %s: %s" % (t.__name__, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d/%d passed" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
