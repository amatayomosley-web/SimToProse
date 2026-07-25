# Prior Art — what's paved, what isn't (researched 2026-06-10)

**Provenance:** deep-research harness, 2026-06-10 — 5 search angles → 26 sources fetched → 129 claims extracted → top 25 adversarially verified (3 independent votes each). 19 confirmed, 1 genuinely refuted, 5 unresolved (verifier budget exhausted mid-pass; those claims are quoted from fetched primary sources and labeled **[unverified]** below — corroborated by training knowledge, pending a re-verify). Synthesis authored by cairn from the verified claim set.

**Claim labels:** **[3-0]/[2-1]/[2-0]** = adversarial votes for/against · **[unverified]** = fetched + quoted, verification incomplete · **[refuted]** = killed 0-3 · **[prior]** = training knowledge, no fresh source.

## Verdict per component

### 1. Event-sourced ground-truth ledger + lazy fold-forward — *combination unpaved; safety principle proven*
- Smallville (Park et al., UIST '23) advances the world by **eager tick-stepping** — every 10-second step computed for all agents regardless of observation **[3-0]**. The opposite of fold-forward.
- The closest structural analog we probed — AI Town's append-only inputs table as a command-sourcing ledger — was **[refuted]** 0-3: it logs commands, not world events; not an event-sourcing precedent.
- But the *safety* of our approach has direct mechanistic support: temporal causality in LLM multi-agent sims can be preserved **without lockstep synchronization** by gating execution on real causal reach (perception radius + movement bounds) — arXiv:2411.03519 **[2-1]**. They use it as a performance optimization; nobody in the set uses it as the *architecture*.
- Ryan reports (from building Sheldon County) that procedural curation of simulated histories is "greatly assisted" by extensive event records **[unverified]** — the ledger-feeds-curation pattern, prefigured.

### 2. Layered fidelity + promotion/demotion by causal coupling — *paved as heuristics; our formalization is cleaner, not new*
- Causal-coupling gating exists in the parallelism literature (above, **[2-1]**).
- Nemesis System (NPC promotion-by-interaction), Dwarf Fortress (thousands of lives at graded fidelity), Crusader Kings (off-screen abstraction) — sources fetched (GDC talks, interviews), claims not reached by the verifier **[prior]**. Industry practice for decades; the causal-hops-to-stakes formalization and the books-balance-across-layers rule are our sharpening.

### 3. Knowledge-bounded agents (vaults, false beliefs, thought-vs-action) — *vault machinery paved in 2015; the visibility split is ours, and empirically motivated*
- Smallville's per-agent **memory streams** are the LLM-era analog — raw observation/reflection records, no false-belief modeling, no thought/action split **[2-1]**.
- **Talk of the Town (Ryan et al. 2015) prefigured the vault hard** **[unverified ×3]**: perception-bounded knowledge (firsthand observation + hearsay only); an explicit ground-truth-vs-belief split where each belief facet carries an **Accuracy flag** plus evidence metadata (source, location, time, strength); false beliefs produced by **named deterministic mechanisms** — transference, confabulation, lying, mutation, forgetting — governed by per-character memory attributes and salience. They even stated post-hoc **information-trajectory reconstruction** as a design goal. Ten years ahead; we should lift their false-belief mechanism taxonomy rather than reinvent it.
- Our thought-vs-action split has fresh empirical motivation: **Project Sid documents thought-action incoherence** as a core failure of concurrent LLM agents — the chat says "Sure thing!" while the function call does something else **[3-0]**. Capturing both streams as separate records is the containment.

### 4. Director-by-circumstance with refusal as integrity check — *the aesthetic is theorized; the protocol is unpaved*
- Ryan's "**contract of emergent narrative**": the audience's interestingness boost comes from the guarantee that recounted events actually happened, and it **dissipates to the degree the simulation is inhibited by interventionist techniques** (drama management, narrative planning) **[unverified]**. That is the theoretical case for circumstance-only steering: forcing destroys the value being sold.
- Drama managers (Façade/Oz lineage; Mateas & Stern AIIDE '05 fetched) are the *contrast class* — they reach into the story **[prior]**. RimWorld's storytellers steer by event placement — circumstance-shaped — but over simple sims, not faithful minds **[prior]**.
- Nothing in the set operationalizes *beat-blind simulation + faithful refusal as plot-integrity check*. This component looks genuinely ours.

### 5. Deterministic engine computes, LLM only acts — *PAVED: convergent best practice. Validating, not novel.*
- **AI Town** ships it: single-threaded deterministic engine per world; LLM work runs async and **cannot write game state** — it submits inputs **[3-0]**.
- 2025 academic prior art names it: "**Hybrid Constitutional Architectures**" — the LLM is a *proposal engine* generating candidate behaviors; a deterministic validation layer commits **[3-0]** (arXiv:2507.19364). Same paper uses "world model" to mean the deterministic ABM ground truth gating LLM proposals — our usage exactly **[3-0]**.
- The contrast class: Project Sid's PIANO keeps coherence **inside the LLM stack** (a Cognitive Controller bottleneck) **[3-0]** — and Sid is also where the incoherence and hallucination-cascade failures are documented. The architecture we chose is the one the failure reports argue for.

### 6. The cut — novel-grade prose with per-line provenance — *the problem is famous; the deliverable is unpaved*
- **The curation problem is confirmed as the field's named bottleneck**: "raw event streams are not narrative... narrative only obtains when the raw stream is curated" — Ryan, *Curating Simulated Storyworlds* **[2-0]**. The cutting room exists because of exactly this.
- Story sifting (Kreminski — Felt/Winnow/WAWLT; sources fetched, unreached) extracts **vignette-scale** material from sim logs **[prior]**.
- The flagship Generative Agents lineage went the *other way*: the 1,052-person follow-up (arXiv:2411.10109) does social-science replication — survey/experiment fidelity per individual — leaving persistent story-worlds and narrative extraction unaddressed **[3-0 ×2]**.
- Nobody in the set renders **book-length shaped prose with per-line provenance to recorded events**. Faithfulness-by-construction at novel grade is the unpaved stretch — consistent with it being our ranked risk #2.

## The failure-mode catalog (design-against list, all verified)
1. **Cost blowup with agent count + API instability** — documented in the Smallville README itself **[3-0]**. *Our mitigations: layered fidelity (LLM only at layers 0–1), lazy fold-forward, model-tiering.*
2. **Thought-action incoherence** — Sid **[3-0]**. *Ours: actor self-reports both streams in one pass (`consolidation-loop.md` P1); the split is recorded, not assumed.*
3. **Hallucination cascades** — small per-call rates compound through agent interaction; miscommunicated thoughts propagate **[3-0]**. *Ours: containment check (every referent ∈ PerceptSet), vault provenance, critic gate.*
4. **Long-horizon behavioral drift** from context-window limits **[3-0]** (arXiv:2507.19364). *Ours: state lives in the DB, not the context; the coherence probe measures exactly this before anything is built.*
5. **Lockstep serialization waste** — Smallville averages 1.94 concurrent LLM queries because strict global time-stepping serializes work **[2-1]**. *Ours: causal-coupling layers + fold-forward avoid global lockstep by design.*
6. **The curation problem** — life ≠ story **[2-0]**. *Ours: the cutting room, with the transcription-baseline control in its probe.*

## The "world model" term audit
The collision is superficial, with one genuine overlap: Genie/JEPA-class research means a *learned predictive model* (next-state prediction in latents/pixels) **[prior]**; the LLM-ABM hybrid literature already uses "world model" for **deterministic ground-truth constraints that gate LLM-proposed actions** **[3-0]** — which is precisely our architecture. We are building a world model in the second sense, and the term is already established for it.

## What this changes in the design
1. **Lift Talk of the Town's false-belief mechanism taxonomy** (transference / confabulation / lying / mutation / forgetting) into `knowledge-model.md`'s vault dynamics rather than inventing our own — pending a proper read of the primary paper (eis.ucsc.edu PDF, in sources).
2. **Cite Sid's incoherence finding** in `recording-model.md`/`consolidation-loop.md` as the empirical motivation for the dual-stream capture.
3. **No architecture changes warranted** — components 1, 4, 6 hold as the novel surface; component 5 is validated convergent practice; components 2, 3 should consciously reuse named prior mechanisms.

## Sources (verified-claim set)
- github.com/joonspk-research/generative_agents (Smallville) · arXiv:2411.00114 (Project Sid / PIANO) · arXiv:2411.10109 (1,052-person agents, v2 2026) · arXiv:2507.19364 (Hybrid Constitutional Architectures) · github.com/a16z-infra/ai-town · arXiv:2411.03519 (causality without lockstep) · Ryan, *Curating Simulated Storyworlds* (excerpt PDF) · Ryan et al. 2015, *Toward Characters Who Observe, Tell, Misremember, and Lie* (unverified pass).
- Fetched but unreached by the verifier (claims not used except as [prior]): Kreminski WAWLT · Mateas & Stern AIIDE '05 (Façade) · GDC: Nemesis System · GDC: Crusader Kings · RimWorld storytellers · Tarn Adams interview · + 8 further 2024–2026 arXiv papers (one flagged unreliable by the harness: arXiv:2601.04170 — do not cite).
