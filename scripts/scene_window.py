"""scene_window.py - a window's reads and its rows (conversation design v2 s5, gate window-reads).

A WINDOW is one speaker's uninterrupted stretch - one move in a plain exchange, a whole speech otherwise - with the
listeners' hold and interject rows inside it. scripts/scene.py run_scene buffers the rows as the actors answer and
hands them to `close` when someone else makes a move or the scene ends. Here:
  the reads  the event seat once over the speaker's moves as one act, and once per listener row that is an act or an
             interjection (a silent hold has no event); the emotion seat once per participant - the speaker on their
             moves and thoughts, each listener on their own rows'. Under --stub the actor's own tags stand in and no
             feeling is read, as before.
  the rows   committed in order. Every row before the last commits decay-only - the room's minutes pass over everyone
             present, its own actor included - with a manifest note naming the window. The last row carries every
             act's Event and bond moves, and every participant's receipt, binds, attitude, wounds, scars and arc: its
             actor's on the commit itself, the others' as `TurnCommit.readers`, each one's applied tags in the
             manifest's `window.reads`, which is what `mood_fold.replay` re-derives them from.
TELLS are the actor's, from the scene brief (gate tells-direction): a row carries the `tell` its actor wrote and the
commit keeps it; no seat marks one, so every window is read once, at its end.
Inside a window the mood does not move: Macbeth holds his tongue on the mood he had before her first paragraph. That
is the design's stated cost (s5), the same approximation the clock already makes within a beat.
"""
from src.engine.scene import resolve_subject, referenced_ids
from src.engine import acquisition, arc, attachments, bond_rest, bonds, claims, rungs, toward, wound
from src.engine import body as _body
from src.engine import concepts as _concepts
from src.engine import condition as _condition
from src.engine import floor as _floor
from src.engine import injuries as _injuries
from src.engine import passage as _passage
from src.engine import replies as _replies
from src.engine import tells as _tells
from src.engine import targets as _targets
from src.engine import tellings as _tellings
from src.engine.consolidation import CATALOG, TagError, tag_refusal, validate_tags
from src.engine.errors import EngineError
from src.engine.prompt import compose_event
from src.engine.records import PATHS, Event, RecordError, RelationshipDelta, TowardDelta, TurnCommit, WoundDelta
from src.engine.severity import normalise_dimensions
from src.engine.state import appraise, decay, receive

_bond_moves = _floor.bond_moves
import appraiser
import provider as _provider

SILENCE = {"type": "mundane", "summary": "", "dimensions": {}, "durability": "transient"}


def _own_tags(reply):
    return normalise_dimensions(reply["tags"] if isinstance(reply.get("tags"), dict) else {"dimensions": {}})


def _text(rows, key):
    return "\n\n".join(s for s in (str(r["reply"].get(key, "") or "") for r in rows) if s.strip())


def _act(ctx, who, rows, at):
    """One act's event read -> {who, rows, tags, answered, failed, notes, extra}: the seat over the act's text joined,
    or the actor's own tags on the last of its rows (--stub, or the seat did not answer)."""
    last = rows[-1]
    act = {"who": who, "rows": rows, "answered": False, "failed": {}, "notes": [], "extra": [], "silent": False}
    if ctx["stub"]:
        act["tags"] = _own_tags(last["reply"])
    else:
        try:
            # THE SUMMARY IS THE ACTOR'S (gate wounds-and-memory-inputs): the seat rates and never writes one
            act["tags"] = acquisition.with_actor_summary(normalise_dimensions(appraiser.read_event(
                _text(rows, "action"), _provider.seat_model(), led=ctx["led"], run_id=ctx["run_id"], turn=at,
                scene=ctx["cfg"].get("name"), moment=last["event_text"], present=list(last["present"]),
                actor=ctx["names"].get(who, who), target=str(last["reply"].get("addressee", "") or ""),
                attachments=attachments.names_for(ctx["world"]), exertion="body" in ctx["sys"],
                injuries="injuries" in ctx["sys"], extra=act["extra"])),
                last["reply"].get("tags"))
            act["answered"] = True
        except RecordError as e:
            k, v = _replies.seat_failure(e)
            act["failed"].setdefault(k, {})["event"] = v
            act["notes"].append("event seat %s: %s" % (_replies.SEAT_VERB[k], v[:120]))
            try:
                act["tags"] = _own_tags(last["reply"])
            except EngineError as ne:          # the fallback fails too: name the seat whose silence made it the tags
                raise type(ne)(ne.code, ne.detail + _replies.failure_note(act["failed"])) from None
    if "body" in ctx["sys"] and not act["answered"]:     # the reader's word only (owner ruling C3b2)
        act["tags"] = {k: v for k, v in act["tags"].items() if k != "exertion"}
    return act


def _silence(row):
    return {"who": row["who"], "rows": [row], "answered": False, "failed": {}, "notes": [], "extra": [], "silent": True,
            "tags": normalise_dimensions(dict(SILENCE))}


def _apply(ctx, act):
    """The act's tags validated against its last row's percepts, its subject resolved -> act + validation, applied,
    target, tgroup. A refused self-report raises, as it did per row (consolidation.tag_refusal)."""
    last, who, tags = act["rows"][-1], act["who"], act["tags"]
    pk = last["packet"]["volatile"]
    target, tgroup = resolve_subject(pk["edges"], ctx["gi"], tags.get("object") or tags.get("subject"),
                                     referenced_ids(pk["percepts"]))
    v = validate_tags(tags, pk["percepts"], ctx["actors"][who]["char"]["baseline"]["skills"])
    if not v["ok"]:
        code, detail = tag_refusal(v, ctx["names"].get(who, who), last["turn"])
        raise TagError(code, detail + _replies.failure_note(act["failed"]))
    applied = tags
    if v["flags"]:
        legit = CATALOG.get(tags.get("type", ""), {}).get("appraisal_map", [])
        applied = dict(tags, dimensions={d: x for d, x in tags.get("dimensions", {}).items() if d in legit})
    if target:
        applied = dict(applied, target=target)
        if tgroup:
            applied["target_group"] = tgroup
    act.update(validation=v, applied=applied, target=target, tgroup=tgroup)
    if "injuries" in ctx["sys"]:    # WHO WAS HURT (gate injuries): the reader's marks only, and only where it runs
        act["injury_key"] = {"injuries": list(applied.get("injuries") or []) if act["answered"] else []}
    return act


def _mark(act):
    """THE READS REACH THE LOG the later calls read: each row of the act carries the act's applied tags."""
    for r in act["rows"]:
        if "log" in r:
            r["log"]["tags"] = dict(act["applied"])


def _seen(ctx, who, window=()):
    """THE WINDOW AS THIS PARTICIPANT LIVED IT (gate tells-feel): the exchange through to the window's close - the
    scene log ends on its last row when `close` runs - composed for them, their own lines "You", and under the
    `tells` system through their own eye (tells.for_listener: a sign they catch reads after the act, one they miss
    never does). Their own last row's moment stopped before it, so a word put in after it never reached the feeling.
    -> (the moment, the signs they caught among the `window` rows: [{turn, who, tell}] - gate tells-caught-at-close,
    the same eye, kept so the narrator can show what the feeling read)."""
    log, caught = ctx["log"], []
    if "tells" in ctx["sys"]:
        sharp = _tells.catches(ctx["actors"][who]["char"], tired="condition_flow" in ctx["sys"])
        log = _tells.for_listener(log, who, sharp)[0]
        caught = [{"turn": r["turn"], "who": r["who"], "tell": t} for r in window if sharp and r["who"] != who
                  for t in (" ".join(str(r["reply"].get("tell") or "").split()),) if t]
    return compose_event(ctx["cfg"]["situation"], log, ctx["names"], me=who), caught


def _feel(ctx, who, rows, at, present, window=()):
    """One participant's emotion read over their rows, in the window as they saw it -> {readings, lands, failed,
    notes, extra, caught}."""
    out = {"readings": [], "lands": None, "failed": {}, "notes": [], "extra": [], "caught": []}
    if ctx["stub"]:
        return out
    last = rows[-1]
    moment, out["caught"] = _seen(ctx, who, window)
    try:
        rd, lands, _conf, missing = appraiser.read_emotion(
            _text(rows, "action"), _text(rows, "thought"), _provider.seat_model(), led=ctx["led"], run_id=ctx["run_id"],
            turn=at, scene=ctx["cfg"].get("name"), moment=moment, present=list(present), me=who,
            percepts=last["packet"]["volatile"]["percepts"], extra=out["extra"])
        out["readings"], out["lands"] = list(rd), lands
        if missing:
            out["notes"].append("concepts the registry lacks: %s" % ", ".join(missing))
    except RecordError as e:
        k, v = _replies.seat_failure(e)
        out["failed"].setdefault(k, {})["emotion"] = v
        out["notes"].append("emotion seat %s: %s" % (_replies.SEAT_VERB[k], v[:120]))
    return out


def _caught(feel):
    """-> {"caught": {participant: [{turn, who, tell}]}} for the window manifest, or {} when nobody caught a sign."""
    c = {x: f["caught"] for x, f in feel.items() if f.get("caught")}
    return {"caught": c} if c else {}


def _spend(ctx, moved, at, tags_of):
    """{id: (mood, impact)} -> {id: next condition} when the book runs condition_flow: each one's minutes against their
    own strength, and a participant's act priced from the reader's exertion word (gates condition-flow, body-exertion)."""
    sys_, led, actors = ctx["sys"], ctx["led"], ctx["actors"]
    if "condition_flow" not in sys_:
        return {}
    out = {}
    for c, (mood, impact) in moved.items():
        ch = actors[c]["char"]
        cap = (_body.capacity(ch, _injuries.weakening(led.con, ctx["run_id"], c, ch, at, actors[c]["view"])
                              if "injuries" in sys_ else 0) if "body" in sys_ else 1.0)
        out[c] = _condition.spend(ch["current"]["condition"], ctx["per_beat"], impact, mood, 1.0 / cap)
        if "body" in sys_ and c in tags_of:
            out[c] = _body.exert(out[c], tags_of[c].get("exertion"), ctx["per_beat"], cap)
    return out


def _age(ctx, present):
    actors = ctx["actors"]
    _passage.age({i: actors[i]["char"] for i in present}, ctx["per_beat"],
                 lambda i: bond_rest.rows_for(ctx["led"].con, ctx["run_id"], i, actors[i]["view"]))


def _shown(ctx, row, note=""):
    reply, names = row["reply"], ctx["names"]
    print("-- beat %d (turn %d) -- %s [%s%s]%s" % (row["beat"] + 1, row["turn"], names.get(row["who"], row["who"]),
                                                  row["word"], ", silent" if row["silent"] else "", note))
    print("   ACTION : %s" % str(reply["action"]).replace("\n", " "))
    print("   THOUGHT: %s" % str(reply["thought"]).replace("\n", " "))


def _deferred(ctx, row, win):
    """A row before the window's last: the room's minutes pass over everyone present, its actor included, and nothing
    is read from it until the window ends."""
    led, actors, who, present = ctx["led"], ctx["actors"], row["who"], list(row["present"])
    _age(ctx, present)
    here = set(present)
    dec = _passage.bystanders({i: actors[i] for i in present}, None, ctx["per_beat"], here)
    nxt = _spend(ctx, {c: (dec[c], 0.0) for c in dec}, row["turn"], {})
    tags = normalise_dimensions(dict(SILENCE))
    validation = validate_tags(tags, row["packet"]["volatile"]["percepts"], actors[who]["char"]["baseline"]["skills"])
    validation.update(row["checks"])
    cond = lambda c: dict(nxt.get(c) or actors[c]["char"]["current"].get("condition", {}))
    led.append_turn(TurnCommit(
        run_id=ctx["run_id"], turn=row["turn"], actor=who, thought=str(row["reply"]["thought"]),
        action=str(row["reply"]["action"]), floor=row["word"], addressee=str(row["reply"].get("addressee") or ""),
        tell=str(row["reply"].get("tell") or ""),
        tags=tags, affect=dict(dec[who]), condition=cond(who), validation=validation,
        events=ctx["law_events"](row["reply"], who, row["turn"]) + row.get("placed", []),   # the director's (placements)
        manifest=dict(row["packet"]["manifest"], window=dict(win),
                      decay={"minutes": ctx["per_beat"], "here": sorted(here), "bystanders": sorted(c for c in dec if c != who)}),
        recall=row["packet"]["recall_refs"], utterances=claims.spoken(str(row["reply"]["action"])),
        bystanders={b: {"affect": dict(dec[b]), "condition": cond(b)} for b in dec if b != who}))
    for c, aff in dec.items():
        actors[c]["affect"] = dict(aff)
    for c, cd in nxt.items():
        actors[c]["char"]["current"]["condition"] = cd
    _shown(ctx, row, "  (window from turn %d; read at its end)" % win["from"])


def _event(act):
    tags, applied, last = act["tags"], act["applied"], act["rows"][-1]
    return Event(type=str(tags.get("type", "mundane")),
                 payload=dict({"text": last["event_text"], "dimensions": tags.get("dimensions", {}),
                               "durability": tags.get("durability", "transient"),
                               "subject": act["target"], "subject_group": act["tgroup"],
                               "object": str(applied.get("object") or ""), "showed": dict(applied.get("showed") or {}),
                               "quotes": dict(applied.get("quotes") or {}), "transfers": list(applied.get("transfers") or []),
                               "told": list(applied.get("told") or [])},
                              **act.get("injury_key", {})),
                 target=act["target"], actor=act["who"])


def _bond_rows(ctx, act, present):
    """The act's bond tier: every other present person re-reads its actor (bond-arithmetic s4-s6) -> rel_deltas,
    rest_rows; the moves and postings stay on the act for the after-commit application."""
    actors, led, y, applied = ctx["actors"], ctx["led"], act["who"], act["applied"]
    obj = str(applied.get("object") or "")
    moves = _bond_moves(actors, present, y, applied)
    rel = ([RelationshipDelta(perceiver=w, target=y, axis=ax, delta=d, order="first", object=str(applied.get("object") or ""))
            for w, deltas, _v, _c in moves for ax, d in sorted(deltas.items())]
           + [RelationshipDelta(perceiver=w, target=y, axis=ax, delta=d, order="second", object=obj)
              for w, _d, view, _c in moves for ax, d in sorted((view or {}).items())])
    rest = []
    for w, deltas, _v, cliffs in moves:
        if cliffs:
            after = bonds.apply_deltas(actors[w]["char"]["current"].get("relationships", {}).get(y, {}), deltas)
            cur = bond_rest.resolve(bond_rest.rows_for(led.con, ctx["run_id"], w, actors[w]["view"]),
                                    actors[w]["char"]["baseline"].get("relationship_priors", {}), y)
            rest += bond_rest.cliff_rows(w, y, after, cliffs, cur)
    accounts = {i: {t: float((e or {}).get("debt", 0.0) or 0.0)
                    for t, e in (actors[i]["char"]["current"].get("relationships") or {}).items() if isinstance(e, dict)}
                for i in present}
    posts = bonds.debt_postings(applied, y, accounts, present=list(present))
    rel += [RelationshipDelta(perceiver=p, target=t, axis="debt", delta=d, order="first", object=obj, cause=cause)
            for p, t, _e, d, cause in posts]
    act.update(moves=moves, posts=posts)
    return rel, rest


def _bonds_land(ctx, act):
    """After the commit: the act's edge moves and postings applied in memory, in the order the log holds them."""
    actors, names, y, ap = ctx["actors"], ctx["names"], act["who"], act["applied"]
    if not act["moves"] and ap.get("showed"):
        print("   BOND   : no move - object %s (below the overtness gate, or nobody else present)" % (ap.get("object") or "-"))
    elif not act["moves"]:
        print("   BOND   : no act - the seat named no showed%s" % (" (stub)" if ctx["stub"] else ""))
    for w, deltas, view, cliffs in act["moves"]:
        rels = actors[w]["char"]["current"].setdefault("relationships", {})
        edge = bond_rest.whole(rels.get(y), actors[w]["char"]["baseline"].get("relationship_priors", {}))
        if deltas:
            edge = bonds.apply_deltas(edge, deltas)
        if view:
            edge = bonds.apply_reflection(edge, view)
        rels[y] = edge
        print("   BOND   : %s -> %s  %s" % (names.get(w, w), names.get(y, y),
                                           "  ".join("%s %+0.3f" % (ax, d) for ax, d in sorted(deltas.items()))))
        for ax in cliffs:
            print("   CLIFF  : %s -> %s  %s rests at %.3f from here" % (names.get(w, w), names.get(y, y), ax, edge.get(ax, 0.0)))
    for p, t, entry, d, cause in act["posts"]:
        prels = actors[p]["char"]["current"].setdefault("relationships", {})
        prels[t] = bonds.apply_deltas(bond_rest.whole(prels.get(t), actors[p]["char"]["baseline"].get("relationship_priors", {})),
                                      {"debt": d})
        print("   BOND   : %s %s %s  debt %+0.3f  - %s" % (names.get(p, p), "owes" if entry == "gave" else "repaid",
                                                         names.get(t, t), d, cause or "(unnamed)"))


def _known(ctx, act, present, at):
    """After the commit: what the act becomes in each mind - its actor's lived belief, each witness's account, a name
    heard aloud, and what was told (acquisition, witness-propagation, name-transmission, knowledge-tellings)."""
    led, actors, names, y, ap, tags = ctx["led"], ctx["actors"], ctx["names"], act["who"], act["applied"], act["tags"]
    world_b, ok = act["rows"][-1]["world"], act["validation"]["ok"]
    got = acquisition.assess(ap, tags, actors[y]["char"], world_b) if ok else None
    if got:
        actors[y]["char"]["current"].setdefault("vault", []).append(got)
        acquisition.fold_vault(actors[y]["char"]["current"]["vault"])
        led.append_acquisition(ctx["run_id"], y, at, got)
    for wid in present:
        if wid == y:
            continue
        wchar = actors[wid]["char"]
        wedge = (wchar["current"].get("relationships") or {}).get(y) or {}
        wb = acquisition.witness_belief(names.get(y, y), tags, y, trust=wedge.get("trust"), world=world_b, witness_id=wid)
        if wb:
            wvault = wchar["current"].setdefault("vault", [])
            wb.setdefault("created_turn", at)
            if not any(isinstance(x, dict) and x.get("claim") == wb["claim"] for x in wvault):
                wvault.append(dict(wb))
                acquisition.fold_vault(wvault)
                led.append_acquisition(ctx["run_id"], wid, at, dict(wb))
        for eid, nm in acquisition.overheard_names(_text(act["rows"], "action"), wchar["current"].get("relationships", {}),
                                                   world_b.get("people", [])):
            belief = acquisition.reveal_name(wchar, eid, nm, world_b)
            if belief:
                led.append_acquisition(ctx["run_id"], wid, at, belief)
                print("   >> %s overhears the name %r (learned)" % (wid, nm))
    heard = _tellings.told_beliefs(
        ap.get("told") if ok else [], y, names.get(y, y), [w for w in present if w != y],
        lambda w: ((actors[w]["char"]["current"].get("relationships") or {}).get(y) or {}).get("trust"), at, world=world_b)
    for wid, told in heard.items():
        wvault = actors[wid]["char"]["current"].setdefault("vault", [])
        for tb in told:
            if any(isinstance(x, dict) and x.get("claim") == tb["claim"] for x in wvault):
                continue
            wvault.append(dict(tb))
            acquisition.fold_vault(wvault)
            led.append_acquisition(ctx["run_id"], wid, at, dict(tb))
            print("   >> %s is told: %s" % (names.get(wid, wid), tb["claim"]))


def close(ctx, rows):
    """Read the window and commit its rows (the module docstring). `rows` are run_scene's buffered rows, in order;
    `ctx` carries the scene's state: led, run_id, cfg, world, names, actors, gi, stub, sys, per_beat, law_events
    (reply, who, turn -> [Event]) and state["target"], the subject carried to the next call."""
    if not rows:
        return
    led, actors, names, sys_ = ctx["led"], ctx["actors"], ctx["names"], ctx["sys"]
    last = rows[-1]
    at, R, present = last["turn"], last["who"], list(last["present"])
    spk = next((r["who"] for r in rows if r["move"]), rows[0]["who"])
    parts = list(dict.fromkeys(r["who"] for r in rows))
    # THE READS: one act for the speaker's moves, one per listener row that did something, one feeling per participant
    moves = [r for r in rows if r["who"] == spk and not r["silent"]]
    acts = ([_act(ctx, spk, moves, at)] if moves else []) + [_act(ctx, r["who"], [r], at) for r in rows
                                                             if r["who"] != spk and not r["silent"]]
    feel = {x: _feel(ctx, x, [r for r in rows if r["who"] == x], at, present, rows) for x in parts}
    for act in acts:
        _apply(ctx, act)
        _mark(act)
    for act in sorted(acts, key=lambda a: a["rows"][-1]["turn"]):
        if act["target"]:
            ctx["state"]["target"] = act["target"]      # carries into the next call's ctx (target_edge)
    own = {a["who"]: a for a in sorted(acts, key=lambda a: a["rows"][-1]["turn"])}   # each one's last act
    for x in parts:
        if x not in own:                                 # a listener who only held: read against the silence
            own[x] = _apply(ctx, _silence([r for r in rows if r["who"] == x][-1]))
    row_act = next((a for a in acts if any(r is last for r in a["rows"])), None)
    if row_act is None:
        row_act = own[R] if own[R]["silent"] and own[R]["rows"][-1] is last else _apply(ctx, _silence(last))
    win = {"from": rows[0]["turn"], "close": at}
    for r in rows[:-1]:
        _deferred(ctx, r, win)
    # THE LAST ROW: the minutes, then each participant's receipt
    _age(ctx, present)
    here = set(present) | {str(a["applied"].get("target")) for a in acts
                           if _concepts.looks_like_concept(a["applied"].get("target"))}
    by = _passage.bystanders({i: actors[i] for i in present if i not in parts}, None, ctx["per_beat"], here)
    before, impact, heights = {}, {}, {}
    for x in parts:
        a, ap, rs = actors[x], own[x]["applied"], feel[x]["readings"]
        before[x] = dict(a.get("targets") or {})
        a["targets"] = _targets.bind_readings(before[x], rs, me=x) if rs else _targets.retarget(before[x], ap, me=x)
        rested = decay(a["affect"], a["temperament"], a["profile"], elapsed=ctx["per_beat"], targets=before[x], present=here)
        reps = {ab: _targets.repeat_count(led.con, ctx["run_id"], x, ab, before_turn=at, view=a["view"])
                for ab in {str(t) for t in a["targets"].values() if t}}
        if rs:
            a["affect"], impact[x] = receive(rested, rs, a["profile"], targets=a["targets"], repeats=reps, present=here)
        else:
            a["affect"] = appraise(rested, ap, a["profile"], targets=a["targets"], repeats=reps, present=here)
            impact[x] = sum(abs(a["affect"][p] - rested[p]) for p in PATHS)
        heights[x] = {}
        for r in rs:                                     # what the seat saw, per path, for arc + wounds
            heights[x][r.path] = max(heights[x].get(r.path, 0.0), rungs.height_of(r.path, rungs.index_of(r.path, r.rung)))
    nxt = _spend(ctx, dict({x: (actors[x]["affect"], impact[x]) for x in parts}, **{b: (m, 0.0) for b, m in by.items()}),
                 at, {x: own[x]["applied"] for x in parts})
    # EACH ACT'S BONDS AND ATTITUDE, EACH PARTICIPANT'S ATTITUDE, WOUNDS AND SCARS - computed here, riding the commit
    rel, rest, toward_deltas = [], [], []
    for act in acts:
        r_, s_ = _bond_rows(ctx, act, present)
        rel, rest = rel + r_, rest + s_
        subj = act["applied"].get("subject") or act["applied"].get("target")
        if subj and "attitude" in sys_:
            toward_deltas += [TowardDelta(perceiver=act["who"], target=str(subj), primary=p, delta=d,
                               source=act["rows"][-1]["event_text"][:200])
                   for p, d in toward.observe(act["applied"].get("dimensions") or {}).items()]
    wds, mints, binds = [], {}, {}
    for x in parts:
        a, ap, rs, xrow = actors[x], own[x]["applied"], feel[x]["readings"], [r for r in rows if r["who"] == x][-1]
        _durable = str(ap.get("durability") or "").lower() == "durable"
        toward_deltas += [TowardDelta(perceiver=x, target=str(w), primary=p, delta=d, source=_text([xrow], "action")[:200])
                          for w, p, d in (toward.observe_readings(rs, me=x, profile=a["profile"], durable=_durable)
                               if "attitude" in sys_ else ())]
        res = arc.derive_resilience(a["char"], a["char"]["current"].get("condition", {}))
        cue = {"about": ap.get("target"), "surfaces": xrow["packet"]["manifest"].get("surfaces") or [], "heights": heights[x]}
        for w in a["char"]["baseline"].get("wounds") or []:
            if not isinstance(w, dict) or not str(w.get("id", "")).strip():
                continue
            d = wound.trial(w, ap.get("dimensions") or {}, res, dict(cue, about=wound.about_for(w, rs) or cue["about"]))
            if d:
                wds.append(WoundDelta(char_id=x, wound_id=str(w["id"]), delta=d, kind="event", source=xrow["event_text"][:200]))
        _durable = _durable or any(float(v) >= arc._DURABLE_DIM for v in (ap.get("dimensions") or {}).values())
        mints[x] = (wound.mint(a["char"], heights[x], a["targets"], _durable, surfaces=xrow["packet"]["manifest"].get("surfaces")
                               or [], text=xrow["event_text"], turn=at) if "wounds" in sys_ else [])
        a["targets"] = _targets.bind_readings(a["targets"], [], temperament=a["temperament"], affect=a["affect"])  # rule 5
        a["char"]["current"]["targets"] = dict(a["targets"])
        binds[x] = _targets.binds_from(before[x], a["targets"])
    toward_deltas = toward.coalesce(toward_deltas)
    # THE COMMIT: the last row's own act, every other act's Event before it, the readers beside its actor
    validation = dict(row_act["validation"])
    validation.update(last["checks"])
    extra = {k: v for k, v in (("event", row_act["extra"]), ("emotion", feel[R]["extra"])) if v}
    if extra:
        validation["seat_extra"] = extra
    for k, v in list(row_act["failed"].items()) + list(feel[R]["failed"].items()):
        validation.setdefault(k, {}).update(v)
    others = {}
    for x in parts:
        for k, v in [kv for a in acts if a["who"] == x and a is not row_act for kv in a["failed"].items()] + (
                list(feel[x]["failed"].items()) if x != R else []):
            others.setdefault(x, {}).setdefault(k, {}).update(v)
    if any(others.values()):
        validation["window_seats"] = {x: v for x, v in others.items() if v}
    cond = lambda c: dict(nxt.get(c) or actors[c]["char"]["current"].get("condition", {}))
    led.append_turn(TurnCommit(
        run_id=ctx["run_id"], turn=at, actor=R, thought=str(last["reply"]["thought"]), action=str(last["reply"]["action"]),
        floor=last["word"], addressee=str(last["reply"].get("addressee") or ""), tell=str(last["reply"].get("tell") or ""),
        tags=row_act["tags"],
        affect=dict(actors[R]["affect"]), condition=cond(R), validation=validation,
        events=ctx["law_events"](last["reply"], R, at) + [_event(a) for a in acts if a is not row_act] + [_event(row_act)]
               + last.get("placed", []),
        manifest=dict(last["packet"]["manifest"], window=dict(win, reads={x: own[x]["applied"] for x in parts},
                                                                     **_caught(feel)),
                      decay={"minutes": ctx["per_beat"], "here": sorted(here), "bystanders": sorted(by)}),
        recall=last["packet"]["recall_refs"], rel_deltas=rel, wound_deltas=wds, toward_deltas=toward_deltas, wound_mints=mints[R],
        utterances=claims.spoken(str(last["reply"]["action"])), target_binds=binds[R], readings=list(feel[R]["readings"]),
        lands_on=list(feel[R]["lands"] or []) if R == spk else [], rest_rows=rest,
        bystanders={b: {"affect": dict(m), "condition": cond(b)} for b, m in by.items()},
        readers={x: {"affect": dict(actors[x]["affect"]), "condition": cond(x), "readings": list(feel[x]["readings"]),
                     "target_binds": binds[x], "wound_mints": mints[x]} for x in parts if x != R}))
    for ex in [{"event": a["extra"]} for a in acts if a["extra"]] + [{"emotion": feel[x]["extra"]} for x in parts
                                                                      if feel[x]["extra"]]:
        print("   [a seat's reply carries key(s) nothing reads - %s]"
              % "; ".join("%s: %s" % (k, _replies.shown(v)) for k, v in ex.items()))
    notes = [n for a in acts for n in a["notes"]] + [n for x in parts for n in feel[x]["notes"]]
    if notes:
        print("   SEATS  : " + " | ".join(notes))
    # the commit held, so the in-memory sheets may now follow the log
    for b, m in by.items():
        actors[b]["affect"] = dict(m)
    for x in sorted({t.perceiver for t in toward_deltas}):
        _passage.fold_toward(led.con, ctx["run_id"], x, actors[x]["char"], view=actors[x]["view"])
    for x in parts:
        if mints[x] or any(w.char_id == x for w in wds):
            _passage.fold_wounds(led.con, ctx["run_id"], x, actors[x]["char"], view=actors[x]["view"])
            actors[x]["profile"] = _profile(actors[x]["char"])
            for m in mints[x]:
                print("   SCAR   : %s  %s on %s at %.2f" % (names.get(x, x), m["concept"], m["path"], m["intensity"]))
    for act in acts:
        _bonds_land(ctx, act)
    for x in parts:
        a = actors[x]
        diff = (arc.assess(own[x]["applied"], impact[x], a["char"], a["char"]["current"]["condition"], heights=heights[x])
                if "arc" in sys_ else None)
        if diff:
            a["char"] = arc.apply(a["char"], diff)
            led.append_arc_diff(ctx["run_id"], x, at, diff)
            a["profile"] = _profile(a["char"])
            a["temperament"] = a["char"]["baseline"]["temperament"]
    for c, cd in nxt.items():
        actors[c]["char"]["current"]["condition"] = cd
    _shown(ctx, last, "  (window from turn %d, read here)" % win["from"] if len(rows) > 1 else "")
    for act in acts:
        print("   TAGS   : %s  %s %s [%s]  subj=%s" % (names.get(act["who"], act["who"]), act["tags"].get("type", "?"),
                                                     act["applied"].get("dimensions", {}),
                                                     act["applied"].get("durability", "?"), act["target"] or "-"))
    for act in acts:
        _known(ctx, act, present, at)


def _profile(ch):
    from src.engine.state import build_profile
    return build_profile(ch)
