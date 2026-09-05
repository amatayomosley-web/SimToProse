# Memory Engine Roadmap — the four advanced character memory tracks

**Status: TRACKED ROADMAP & CHECKLIST.**  
**Companion Docs:** [`docs/knowledge-model.md`](docs/knowledge-model.md) · [`docs/relevancy-gate.md`](docs/relevancy-gate.md) · [`docs/consolidation-loop.md`](docs/consolidation-loop.md) · [`docs/scene-assembly.md`](docs/scene-assembly.md)

This roadmap tracks the four open development tracks required to advance the character memory architecture from its current operational baseline (1-hop deterministic recall, Obsidian vault parsing, turn-by-turn acquisition) to full epistemic maturity.

---

## The Four Tracks at a Glance

| Track | Core Problem | Key Seam | Target Invariant |
|---|---|---|---|
| **Track 1: Belief Revision** | Monotonic storage keeps refuted beliefs active. | `acquisition.py` → `vault.py` | Append-only supersession; refuted claims cease to drive action. |
| **Track 2: Multi-Hop Retrieval** | Recall matches only 1-hop link anchors & keywords. | `gate.py` (`run_gate`) | Associative graph traversal across `[[links]]` bounded by cognitive energy. |
| **Track 3: Memory Decay** | Acquired beliefs persist indefinitely at fixed strength. | `gate.py` + `records.py` | Ebbinghaus decay modulated by emotional charge and reinforcement. |
| **Track 4: Second-Order Theory of Mind** | No representation of what A thinks B knows. | `prompt.py` + `facets.py` | Bounded depth-2 epistemic attribution to power secrets and dramatic irony. |

---

## Track 1: Belief Contradiction & Revision (The Supersession Operator)

### Problem Statement
Currently, [`src/engine/acquisition.py:24-63`](src/engine/acquisition.pyL63) is strictly additive. If a character acquires a belief that directly refutes a prior belief (e.g., believing an ally was dead, then seeing them alive), both beliefs reside in the character's vault simultaneously, competing for trigger recall without resolution.

### Checklist
- [x] **1.1 Schema Definition**: Added `supersedes`, `refutes`, and `status` (`active | superseded | refuted`) fields to internal belief representations.
- [x] **1.2 Promotion Logic**: Updated [`src/engine/acquisition.py:assess()`](src/engine/acquisition.pyL63) with `detect_contradiction()` and explicit/semantic supersession linking.
- [x] **1.3 Storage & Persistence**: Preserved append-only SQLite chronicle (Hard Rule 2) and added `acquisition.fold_vault()` across `scene.py` and `direct.py` rehydration.
- [x] **1.4 Gate Filtering**: Updated [`src/engine/gate.py:run_gate()`](src/engine/gate.pyL440) to suppress superseded/refuted beliefs from active prompt recall while preserving `must_surface`.
- [x] **1.5 Automated Verification**: Created `tests/test_belief_revision.py` (19 passed, 0 failed); all 68 suites in `tests/run_all.py` passing.

---

## Track 2: Multi-Hop Associative Graph Traversal

### Problem Statement
[`src/engine/gate.py:379-397`](src/engine/gate.pyL397) currently matches triggers against a flat list of beliefs using 1-hop string keywords and direct `[[links]]` anchors. Complex associative leaps (e.g. *Sigil $\to$ Smuggler Crates $\to$ Harbor Contact $\to$ Secret Society* per [`docs/relevancy-gate.md:60-98`](docs/relevancy-gate.mdL98)) cannot surface if the connection requires multiple cognitive hops.

### Checklist
- [x] **2.1 Adjacency Index**: Built in-memory graph index from vault `[[links]]` and entity references in [`src/engine/associative.py`](src/engine/associative.py).
- [x] **2.2 Pathfinding Algorithm**: Implemented weighted Dijkstra traversal in [`src/engine/associative.py`](src/engine/associative.py) expanding outward from scene trigger entities to candidate belief nodes.
- [x] **2.3 Degree Penalty (Hub Suppression)**: Down-weights paths passing through high-degree hub nodes ($\alpha \log(\text{degree})$) to prevent spurious short connections.
- [x] **2.4 Connection Energy Accumulation**: Traversal bounded by the character's cognitive `_energy_budget(condition)` ($\text{energy} \times (1 - \text{allostatic\_load} \times 0.5)$), ensuring exhausted characters only recall direct links.
- [x] **2.5 Automated Verification**: Authored `tests/test_gate_multihop.py` asserting the 3-hop shopkeeper sigil scenario from `docs/relevancy-gate.md` (passes when energized, fails when exhausted; 9/9 passed).

---

## Track 3: Memory Decay & Temporal Forgetting Curves

### Problem Statement
Every acquired belief remains at its original confidence forever. Trivial day-to-day observations made fifty turns ago compete on equal footing with recent, vivid developments.

### Checklist
- [x] **3.1 Temporal Metadata**: Grounded beliefs with `created_turn`, `last_recalled_turn`, and `recall_count` in [`src/engine/decay.py`](src/engine/decay.py).
- [x] **3.2 Attenuation Function**: Implemented deterministic confidence attenuation in [`src/engine/decay.py`](src/engine/decay.py) adhering to `docs/character-model.md:173`:
  $$\text{effective\_confidence} = \text{floor} + (\text{base\_confidence} - \text{floor}) \times (\text{retention})^{\Delta t}$$
  where core identity beliefs never decay, durable beliefs level off at $0.35$, and transient beliefs fade to $0.05$.
- [x] **3.3 Memory Refresh & Spaced Repetition**: Recalling a belief refreshes $\Delta t = 0$, and repeated recall (`recall_count`) flattens future decay rates.
- [x] **3.4 Automated Verification**: Authored [`tests/test_memory_decay.py`](tests/test_memory_decay.py) proving forgetting curves and gate retrieval suppression under decay (16/16 passed).

---

## Track 4: Second-Order Theory of Mind (Epistemic Asymmetry)

### Problem Statement
Characters currently track how they feel about others (`trust`, `affinity`, `respect`, `debt`), but cannot represent asymmetric knowledge (e.g. *"I know the gold was stolen, and I know Corin doesn't know"*). Dramatic irony and deliberate deception depend entirely on prompt coincidence rather than mechanical support.

### Checklist
- [x] **4.1 Epistemic Attribution Schema**: Extended belief representations to support second-order tags: `{holder: "a", target_actor: "b", stance: "believes" | "ignorant_of" | "deceived_about", claim: "..."}` in [`src/engine/acquisition.py`](src/engine/acquisition.py).
- [x] **4.2 Perception of Knowledge & Witness Leak Prevention**: Partitioned witness transmission so private secrets and marked ignorance do not leak to bystanders via `witness_belief()`.
- [x] **4.3 Prompt Rendering**: In [`src/engine/prompt.py`](src/engine/prompt.py), added rendering of second-order knowledge in digit-free words using `sureness()`.
- [x] **4.4 Depth-Partitioned Supersession**: Supersession partitioned by `target_actor` so first-order reality never erases second-order beliefs about other minds, and hardened contradiction matching against substring traps.
- [x] **4.5 Automated Verification**: Authored [`tests/test_theory_of_mind.py`](tests/test_theory_of_mind.py) with 17 rigorous multi-vector tests verifying the omniscience wall at the full prompt boundary, positive rendering, witness leakage prevention, and depth partitioning (17/17 passed).

---

## Recommended Execution Sequencing

```text
Track 1 (Belief Revision)       ───► Fixes immediate logical contradictions in long runs.
Track 2 (Multi-Hop Traversal)   ───► Enables deep associative recall and deduction.
Track 3 (Decay & Forgetting)    ───► Prevents prompt token bloat across 100+ turns.
Track 4 (Second-Order ToM)      ───► Powers advanced political intrigue and deception.
```
