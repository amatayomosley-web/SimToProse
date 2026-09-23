"""associative.py — Track 2 & 3: Multi-Hop Associative Graph Traversal with Temporal Decay.

Normative contract:
  docs/relevancy-gate.md §'Backlinks / graph distance — use as cost + difficulty, NEVER as a cutoff'
  docs/relevancy-gate.md §'Worked example — how many hops? (the shopkeeper sigil)'
  docs/character-model.md §'DECAY AND CONNECTION (NORMATIVE, 2026-08-31)'
  docs/relevancy-gate.md §'Connection energy — traversal as a resource'

Pure + deterministic graph traversal over a character's vault beliefs and [[links]].
Finds multi-hop associative recall chains bounded by cognitive connection energy,
with edge faintness naturally modulated by temporal memory decay.
"""
__layer__ = "engine"

import heapq
import math
import re

from .decay import calculate_effective_confidence
from .gate import _normalize, belief_id

MIN_STEP_COST = 0.05
RUNTIME_MAX_HOPS = 16


def _keyword_overlap(claim_norm, text_norm):
    w1 = set(claim_norm.split())
    w2 = set(text_norm.split())
    return bool(w1 & w2 - {"the", "a", "an", "to", "of", "and", "is", "in", "it", "on", "for", "at", "by"})


def build_vault_graph(vault, current_turn=0, relationships=None, recall_history=None, elapsed=None):
    """Build a weighted bidirectional adjacency graph from vault beliefs.

    Anchors come strictly from authored [[links]] and `about` facets.
    Edge weights reflect effective confidence modulated by temporal decay and relationship connection.

    Nodes:
      - 'b:<hash>': Belief nodes
      - '<concept>': Authored concept / entity / link target nodes
    """
    adj = {}
    node_beliefs = {}
    degrees = {}

    def _add_edge(u, v, weight):
        if u not in adj:
            adj[u] = []
        adj[u].append((v, float(weight)))

    for b in vault:
        if not isinstance(b, dict):
            continue
        if b.get("status") in ("superseded", "refuted") and not b.get("must_surface"):
            continue

        bid = b.get("bid") or belief_id(b)
        node_beliefs[bid] = b
        eff_conf = calculate_effective_confidence(
            b, current_turn=current_turn, relationships=relationships,
            recall_history=recall_history, elapsed=elapsed)
        cost = max(MIN_STEP_COST, 1.0 - eff_conf)

        anchors = set()
        for l in (b.get("links") or []):
            if l:
                anchors.add(_normalize(str(l)).strip())
        for a in (b.get("about") or []):
            if a:
                anchors.add(_normalize(str(a)).strip())

        for anc in sorted(anchors):
            if not anc:
                continue
            _add_edge(anc, bid, cost)
            _add_edge(bid, anc, 0.0)

    for node, edges in adj.items():
        degrees[node] = len(edges)

    return {"adj": adj, "beliefs": node_beliefs, "degrees": degrees}


def find_associative_candidates(triggers, vault, goals, budget, current_turn=0,
                                relationships=None, recall_history=None, elapsed=None):
    """Generate recall candidates via 1-hop matching and multi-hop associative traversal.

    Pure & deterministic.
    Returns list of candidate dicts ready for budget sorting & spending.
    """
    if not isinstance(triggers, list) or not isinstance(vault, list):
        return []

    goal_texts = [_normalize(g.get("goal", "")) for g in (goals or []) if isinstance(g, dict)]
    graph = build_vault_graph(
        vault, current_turn=current_turn, relationships=relationships,
        recall_history=recall_history, elapsed=elapsed)
    adj = graph["adj"]
    beliefs = graph["beliefs"]

    candidates = []
    seen_bids = set()

    # --- Step 1: Direct 1-Hop Matching (Surface word & [[links]] overlap) ---
    for idx, b in enumerate(vault):
        if not isinstance(b, dict):
            continue
        if b.get("status") in ("superseded", "refuted") and not b.get("must_surface"):
            continue

        claim = str(b.get("claim", ""))
        eff_conf = calculate_effective_confidence(
            b, current_turn=current_turn, relationships=relationships,
            recall_history=recall_history, elapsed=elapsed)
        cost = max(0.0, 1.0 - eff_conf)
        surface = _normalize(claim) + " " + " ".join(_normalize(str(l)) for l in (b.get("links") or []))

        matched = [trig for trig in triggers if _normalize(trig) in surface]
        if matched or b.get("must_surface"):
            bid = b.get("bid") or belief_id(b)
            seen_bids.add(bid)

            is_goal_bearing = any(gt and _keyword_overlap(_normalize(claim), gt) for gt in goal_texts)
            c1 = {
                "idx": idx,
                "ref": "vault[%d]" % idx,
                "bid": bid,
                "claim": claim,
                "believed_value": b.get("believed_value"),
                "provenance": b.get("provenance", ""),
                "confidence": b.get("confidence", 0.5),
                "confidence_eff": eff_conf,
                "cost": 0.0 if b.get("must_surface") else cost,
                "triggered": matched or ["must_surface"],
                "is_goal_bearing": is_goal_bearing or bool(b.get("must_surface")),
                "hops": 1,
                "path": [matched[0] if matched else "hinge", bid],
            }
            if b.get("target_actor"): c1["target_actor"] = b["target_actor"]
            if b.get("epistemic_stance"): c1["epistemic_stance"] = b["epistemic_stance"]
            candidates.append(c1)

    # --- Step 2: Multi-Hop Dijkstra Expansion from Triggers ---
    if budget > 0.0 and triggers:
        norm_triggers = [_normalize(str(t)).strip() for t in triggers if t]
        start_nodes = set()
        for nt in norm_triggers:
            if nt in adj:
                start_nodes.add(nt)
            else:
                for w in nt.split():
                    if w in adj:
                        start_nodes.add(w)

        pq = []
        best_cost = {}
        for s in sorted(start_nodes):
            heapq.heappush(pq, (0.0, s, 0, [s]))
            best_cost[s] = 0.0

        reached_beliefs = {}
        while pq:
            curr_cost, u, hops, path = heapq.heappop(pq)
            if curr_cost > best_cost.get(u, float("inf")):
                continue

            if u in beliefs:
                b_obj = beliefs[u]
                if u not in seen_bids and (u not in reached_beliefs or curr_cost < reached_beliefs[u]["path_cost"]):
                    reached_beliefs[u] = {
                        "bid": u,
                        "belief": b_obj,
                        "path_cost": round(curr_cost, 4),
                        "hops": hops,
                        "path": list(path),
                    }

            if hops >= RUNTIME_MAX_HOPS:
                continue

            for v, edge_weight in adj.get(u, []):
                next_cost = curr_cost + edge_weight

                if next_cost <= budget or (v in beliefs and beliefs[v].get("must_surface")):
                    if next_cost < best_cost.get(v, float("inf")):
                        best_cost[v] = next_cost
                        next_hops = hops + (1 if v.startswith("b:") else 0)
                        heapq.heappush(pq, (next_cost, v, next_hops, path + [v]))

        # Add reached multi-hop beliefs
        for bid, data in reached_beliefs.items():
            b = data["belief"]
            claim = str(b.get("claim", ""))
            eff_conf = calculate_effective_confidence(
                b, current_turn=current_turn, relationships=relationships,
                recall_history=recall_history, elapsed=elapsed)
            idx = vault.index(b) if b in vault else 0
            is_goal_bearing = any(gt and _keyword_overlap(_normalize(claim), gt) for gt in goal_texts)

            trace_steps = [p for p in data["path"] if not p.startswith("b:")]
            chain_label = " -> ".join(trace_steps) if trace_steps else "associative leap"

            c2 = {
                "idx": idx,
                "ref": "vault[%d]" % idx,
                "bid": bid,
                "claim": claim,
                "believed_value": b.get("believed_value"),
                "provenance": b.get("provenance", ""),
                "confidence": b.get("confidence", 0.5),
                "confidence_eff": eff_conf,
                "cost": 0.0 if b.get("must_surface") else max(MIN_STEP_COST, 1.0 - eff_conf),
                "triggered": [chain_label],
                "is_goal_bearing": is_goal_bearing or bool(b.get("must_surface")),
                "hops": data["hops"],
                "path": data["path"],
            }
            if b.get("target_actor"): c2["target_actor"] = b["target_actor"]
            if b.get("epistemic_stance"): c2["epistemic_stance"] = b["epistemic_stance"]
            candidates.append(c2)

    return candidates
