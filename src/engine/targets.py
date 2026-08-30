"""targets.py — what each feeling is ABOUT.

Split out of `state.py` (2026-08-22) on the same seam the field split uses: MAGNITUDE and TARGET
have different lifetimes. A magnitude decays toward temperament every beat — that is `state.decay`.
A target never decays; it is replaced, or it is released when the feeling behind it subsides. Two
lifetimes, two modules, the way this project separates fixed / baseline / current everywhere else.

`docs/emotion-basis.md` is normative: "Per-primary targets move the target from the event onto the
state, and `_regard` becomes a per-primitive evaluation." The per-primitive `_regard` stayed in
`state.py` because it is part of the appraisal arithmetic; the BINDING lives here.

Pure, deterministic, stdlib. The registry it consults (`records.DIRECTEDNESS`) is upstream of both.
"""
from .records import admits_role
from .state import _AT_REST, _DIM_TO_PRIMARY


def retarget(targets, tags, temperament=None, affect=None, me=None):
    """What each primitive is ABOUT after this event. Pure; returns a NEW map.

    `emotion-basis.md` moves the target off the event and onto the state, which is what lets a
    character fear the wolf and rage at the man who let it in: one event cannot supply two subjects,
    so per-primitive aboutness has to ACCUMULATE ACROSS BEATS or it cannot exist at all.

    Five rules, each with a reason:

      1. A POSITIVE push binds the event's subject as that primitive's object. The event was about
         S, so the fear it raised is fear OF S.
      2. A NEGATIVE push never binds. A target on a suppression is meaningless — PLAY collapsing
         under threat does not thereby point at the threat.
      3. REFLEXIVITY IS DERIVED. Subject == the character -> a reflexive bind, but only where
         `records.DIRECTEDNESS` admits one. Where it does not, THE MAGNITUDE STILL APPLIES AND THE
         BIND IS DROPPED. That is not a fallback, it is the behaviour: a self-authored social
         violation yields DISGUST(self) plus RAGE-unbound — shame, and irritability at the room,
         which is how humiliated people act.
      4. A positive push with NO subject leaves any existing bind untouched. Nothing new was learned
         about what the feeling is about.
      5. A primitive that has DECAYED BACK TO REST clears its bind. Aboutness with no feeling behind
         it is stale, and it would otherwise re-attach to a later unrelated spike.

    One target per primitive means simultaneous rage at two parties is inexpressible. That is the
    basis shape's own trade, accepted when it chose one slot; recency wins. LEAVE ALONE unless
    renders show targets ping-ponging or stale aboutness — this is deliberately not arbitrated.
    """
    if not isinstance(tags, dict):
        raise ValueError("retarget: tags must be a dict, got %r" % type(tags).__name__)
    out = dict(targets) if isinstance(targets, dict) else {}

    dimensions = tags.get("dimensions") or {}
    if not isinstance(dimensions, dict):
        raise ValueError("retarget: tags['dimensions'] must be a dict")
    subject = tags.get("target")

    if subject:
        reflexive = me is not None and str(subject).lower() == str(me).lower()
        for dim, mag in dimensions.items():
            try:
                if float(mag) <= 0.0:
                    continue
            except (TypeError, ValueError):
                continue
            for primary, base_push in _DIM_TO_PRIMARY.get(dim, []):
                if base_push <= 0.0:
                    continue                                   # rule 2: suppressions do not bind
                if reflexive and not admits_role(primary, "self"):
                    out.pop(primary, None)                     # rule 3: magnitude keeps, bind drops
                    continue
                out[primary] = str(subject)                    # rule 1

    # rule 5 — a primitive back at rest is no longer about anything
    if isinstance(temperament, dict) and isinstance(affect, dict):
        for primary in list(out):
            v = affect.get(primary)
            mean = (temperament.get(primary) or {}).get("mean")
            if isinstance(v, (int, float)) and isinstance(mean, (int, float)):
                if abs(float(v) - float(mean)) <= _AT_REST:
                    out.pop(primary, None)
    return out
