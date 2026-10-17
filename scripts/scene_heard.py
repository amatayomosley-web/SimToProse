"""scene_heard.py - the ones a window reached who did not act in it (gate listener-read, showrunner ruling 2026-10-17
09:00, amending conversation design v2 s5): who they are, what they took in, what they were thinking, and the row
they are read against. scripts/scene_window.py close reads each of them once, at the window's end."""


def listeners(ctx, rows, present, parts):
    """THE ONES WHO TOOK IT IN (gate listener-read, showrunner ruling 2026-10-17 09:00): every present member of the
    cast with no row in the window, when the window did something - the one it was aimed at first. A person refused
    feels it whether or not they spoke. Under --stub nothing is read, so they stay bystanders, as before."""
    acted = [r for r in rows if not r["silent"]]
    if ctx["stub"] or not acted:
        return []
    aimed = {str(r["reply"].get("addressee") or "") for r in acted}
    cand = [i for i in present if i in ctx["actors"] and i not in parts]
    return sorted(cand, key=lambda i: (not ({i, ctx["names"].get(i, i)} & aimed), cand.index(i)))


def took_in(ctx, who, window, caught):
    """What a listener who did not act took in: the others' acts in the window, a sign they caught after it."""
    signs = {(c["turn"], c["who"]): c["tell"] for c in caught}
    return "\n\n".join("%s: %s%s" % (ctx["names"].get(r["who"], r["who"]), str(r["reply"].get("action") or "").strip(),
                                     "\n(without meaning to: %s)" % signs[(r["turn"], r["who"])]
                                     if (r["turn"], r["who"]) in signs else "")
                       for r in window if r["who"] != who and not r["silent"])


def last_thought(ctx, who):
    """Their own last thought in the scene log - the unsteered one where a steer drew it (gate thought-unsteered)."""
    mine = [b for b in ctx["log"] if b.get("who") == who]
    return str((mine[-1].get("carried") or mine[-1].get("thought") or "") if mine else "")


def stand_in(last, who, feel):
    """The row a listener who did not act is read against: the window's last, theirs in name, silent, never committed."""
    return dict(last, who=who, reply={"action": "", "thought": "", "tags": None, "addressee": ""}, silent=True,
                move=False, event_text=feel.get("moment") or last["event_text"])


def inputs(ctx, who, rows, window, caught, text):
    """-> (action, thought, took_in, percepts) for the emotion seat: a participant's own rows (took_in None), or, with
    none, what they took in against their last thought - the people who acted among what they perceived."""
    last = rows[-1] if rows else window[-1]
    percepts = list(last["packet"]["volatile"]["percepts"])
    if rows:
        return text(rows, "action"), text(rows, "thought"), None, percepts
    return "", last_thought(ctx, who), took_in(ctx, who, window, caught), percepts + [
        {"id": i, "name": ctx["names"].get(i, i)} for i in dict.fromkeys(r["who"] for r in window)]
