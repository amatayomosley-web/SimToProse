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
_NAMESPACES = ("loc.", "grp.", "entity.")


def _referent(s):
    """One spelling of a referent for anchors, `about` ids and triggers alike (gate knowledge-about-index): lower-cased
    and accent-folded, a registry namespace dropped ("loc.millbrook" -> "millbrook"), underscores as spaces
    ("old_man" -> "old man", the spelling extract_triggers gives a recognized person). Before, an anchor kept its raw
    spelling and a namespaced or multi-word referent never met its trigger."""
    t = _normalize(str(s or "")).strip()
    for p in _NAMESPACES:
        if t.startswith(p):
            t = t[len(p):]
            break
    return " ".join(t.replace("_", " ").split())


def _ready(b, eff_conf, current_turn=0, relationships=None, recall_history=None, elapsed=None):
    """How readily a belief comes back, which is what recall is PRICED by. A belief with its own `readiness` (a telling:
    tellings.py) fades from that value, apart from how far it is believed - so a doubted rumour is not also buried
    (Fable review 3, 8.3: sureness and readiness are two numbers). Every other belief is as ready as it is sure."""
    r = b.get("readiness")
    if r is None:
        return eff_conf
    try:
        r = max(0.0, min(1.0, float(r)))
    except (TypeError, ValueError):
        return eff_conf
    return calculate_effective_confidence(dict(b, confidence=r), current_turn=current_turn, relationships=relationships,
                                          recall_history=recall_history, elapsed=elapsed)


def _word_hit(trigger):
    """A trigger's matcher: it meets text at WORD boundaries, never inside another word, and a single word meets its
    plural either way ("hunter" / "hunters"). Raw substring let 'low' qualify a belief about the Hollow and 'out' one
    that says "about" - the accidents facets.py closed at the write on 2026-08-30 and this step kept making. A phrase
    must appear whole. -> compiled pattern, or None for an empty trigger."""
    t = _referent(trigger)
    if not t:
        return None
    forms = {t}
    if " " not in t:
        forms |= {t + "s", t + "es"}
        if len(t) > 4 and t.endswith("es"):
            forms.add(t[:-2])
        if len(t) > 3 and t.endswith("s"):
            forms.add(t[:-1])
    return re.compile(r"(?<![0-9a-z])(?:%s)(?![0-9a-z])" % "|".join(sorted(re.escape(f) for f in forms)))


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
        cost = max(MIN_STEP_COST, 1.0 - _ready(b, eff_conf, current_turn, relationships, recall_history, elapsed))

        anchors = set()
        for l in (b.get("links") or []):
            if l:
                anchors.add(_referent(l))
        for a in (b.get("about") or []):
            if a:
                anchors.add(_referent(a))

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
    matchers = [(trig, _referent(trig), _word_hit(trig)) for trig in triggers]

    # --- Step 1: Direct 1-Hop Matching (words of the claim and its [[links]], or what it is ABOUT) ---
    # A belief is a direct candidate when a trigger is a WORD of it, or when a trigger names what it is about - its
    # `about` ids, the KNOWER's referent (Fable review 3, M3): "He will come up that hill one day", stamped about tam,
    # is reached when tam is recognized though it never names him. Two identities are two ids and stay apart.
    for idx, b in enumerate(vault):
        if not isinstance(b, dict):
            continue
        if b.get("status") in ("superseded", "refuted") and not b.get("must_surface"):
            continue

        claim = str(b.get("claim", ""))
        eff_conf = calculate_effective_confidence(
            b, current_turn=current_turn, relationships=relationships,
            recall_history=recall_history, elapsed=elapsed)
        cost = max(0.0, 1.0 - _ready(b, eff_conf, current_turn, relationships, recall_history, elapsed))
        surface = _normalize(claim) + " " + " ".join(_referent(l) for l in (b.get("links") or []))
        about = {_referent(a) for a in (b.get("about") or []) if a}

        matched = [trig for trig, ref, pat in matchers
                   if (ref and ref in about) or (pat is not None and pat.search(surface))]
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
        norm_triggers = [_referent(t) for t in triggers if t]
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
        # THE DRAG (gate knowledge-tellings; the owner: memory "can and does drag other facts or ideas along"): a
        # belief brought to mind directly is itself a start, at what it cost, so what it shares an anchor with - the
        # same subject, the same authored link, the same telling - comes along by the graph's own hops and costs.
        # Before, only a trigger that was itself an anchor started the walk, and a fact matched by its words
        # dragged nothing.
        for c in candidates:
            bid = c["bid"]
            if bid in beliefs and c["cost"] <= budget and c["cost"] < best_cost.get(bid, float("inf")):
                best_cost[bid] = c["cost"]
                heapq.heappush(pq, (c["cost"], bid, 1, [str(c["triggered"][0]), bid]))

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
                "cost": 0.0 if b.get("must_surface") else max(
                    MIN_STEP_COST, 1.0 - _ready(b, eff_conf, current_turn, relationships, recall_history, elapsed)),
                "triggered": [chain_label],
                "is_goal_bearing": is_goal_bearing or bool(b.get("must_surface")),
                "hops": data["hops"],
                "path": data["path"],
            }
            if b.get("target_actor"): c2["target_actor"] = b["target_actor"]
            if b.get("epistemic_stance"): c2["epistemic_stance"] = b["epistemic_stance"]
            candidates.append(c2)

    return candidates
