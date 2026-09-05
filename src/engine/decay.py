"""decay.py — Track 3: Memory Decay & Temporal Forgetting Curves.

Normative contract:
  docs/character-model.md §'DECAY AND CONNECTION (NORMATIVE, 2026-08-31)'
  value <- rest + (value - rest) x retention ^ elapsed
  docs/character-model.md §'Two clocks and no third: declared elapsed for everything else'
  docs/relevancy-gate.md §'Connection energy — traversal as a resource'

Pure + deterministic temporal decay for character memory retrieval strength.
Derives recall history from append-only chronicle tables without mutating stored records.
"""
__layer__ = "engine"

import json
from . import connection
from .decay_law import relax

# Baseline retention rates (per declared time unit / season) [CALIBRATION]
RETENTION_TRANSIENT = 0.85   # Mundane episodic details fade rapidly
RETENTION_DURABLE = 0.96     # Meaningful life events fade slowly to a high floor
RETENTION_CORE = 1.00        # Core identity beliefs do not decay (Law 1)

# Asymptotic retention floors [CALIBRATION]
FLOOR_TRANSIENT = 0.05
FLOOR_DURABLE = 0.35


def fold_recall_history(con, run_id, actor):
    """Fold append-only chronicle tables to derive {bid: {'last_turn': int, 'count': int}}.

    In accordance with 'cause is logged once; effect is derived at replay'.
    Keys strictly on content-derived belief_id (bid) from decision_manifests.
    """
    if not con or not run_id or not actor:
        return {}

    history = {}
    try:
        rows = con.execute(
            "SELECT turn, manifest FROM decision_manifests WHERE run_id = ? AND actor = ? ORDER BY turn ASC",
            (run_id, actor)
        ).fetchall()
        for r in rows:
            try:
                turn = int(r["turn"] if isinstance(r, dict) else r[0])
                raw = r["manifest"] if isinstance(r, dict) else r[1]
                m = json.loads(raw) if isinstance(raw, str) else raw
                r_ids = m.get("recall_ids") or []
                for bid in r_ids:
                    if bid not in history:
                        history[bid] = {"last_turn": turn, "count": 0}
                    history[bid]["last_turn"] = turn
                    history[bid]["count"] += 1
            except Exception:
                continue
    except Exception:
        # Tables might not exist in uninitialized test db
        pass

    return history


def calculate_effective_confidence(belief, current_turn=0, relationships=None,
                                   recall_history=None, elapsed=None):
    """Compute current retrieval confidence of a belief under temporal decay.

    Formula:
      confidence_eff = floor + (base_conf - floor) * (retention_eff ^ delta_t)

    Parameters:
      belief         : dict representing the belief
      current_turn   : int current scene turn (used if elapsed is None)
      relationships  : dict of live character relationship edges {target: edge_dict}
      recall_history : dict derived from fold_recall_history {bid: {last_turn, count}}
      elapsed        : float declared story time elapsed (from clock.elapsed_since)
    """
    if not isinstance(belief, dict):
        return 0.5

    try:
        base_conf = max(0.0, min(1.0, float(belief.get("confidence", 0.5))))
    except (TypeError, ValueError):
        base_conf = 0.5

    durability = belief.get("durability", "transient")
    if belief.get("provenance") == "core" or durability == "core":
        return base_conf

    # Derive last recall and recall count from chronicle fold if available
    bid = belief.get("bid")
    try:
        if bid and recall_history and bid in recall_history:
            last_recalled = int(recall_history[bid]["last_turn"])
            recall_count = int(recall_history[bid]["count"])
        else:
            created_turn = int(belief.get("created_turn", 0))
            last_recalled = int(belief.get("last_recalled_turn", created_turn))
            recall_count = int(belief.get("recall_count", 0))
    except (TypeError, ValueError):
        last_recalled = 0
        recall_count = 0

    if elapsed is not None:
        delta_t = max(0.0, float(elapsed))
    else:
        delta_t = float(max(0, int(current_turn) - last_recalled))

    if delta_t == 0.0:
        return base_conf

    if durability == "durable":
        base_retention = RETENTION_DURABLE
        floor = min(base_conf, FLOOR_DURABLE)
    else:
        base_retention = RETENTION_TRANSIENT
        floor = min(base_conf, FLOOR_TRANSIENT)

    # Live connection scaling: if belief is linked to a subject, connection slows decay
    subject = None
    links = belief.get("links") or []
    if links:
        subject = links[0]
    elif belief.get("about"):
        subject = (belief.get("about") or [])[0]

    if subject and relationships:
        c = connection.for_target(relationships, subject)
        retention_eff = connection.retention_scale(base_retention, c)
    else:
        retention_eff = base_retention

    # Spaced repetition: bounded headroom scaling so rehearsal cannot grant immortality
    if recall_count > 0:
        retention_eff = connection.retention_scale(retention_eff, min(0.6, 0.15 * recall_count))

    effective = relax(base_conf, floor, retention_eff, delta_t)
    return max(0.0, min(1.0, round(effective, 4)))


def record_belief_recall(belief, current_turn):
    """Pure helper returning updated copy of belief with refreshed recall metadata."""
    if not isinstance(belief, dict):
        return belief
    updated = dict(belief)
    updated["last_recalled_turn"] = int(current_turn)
    updated["recall_count"] = int(updated.get("recall_count", 0)) + 1
    return updated
