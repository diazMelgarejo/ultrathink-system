# 09 — Comparative Analysis & Merging Plan

> **Status:** Active | Added 2026-05-02
> **Goal:** Align v2 implementation at \`/Users/lawrencecyremelgarejo/Documents/oramasys/\` with Gemini hardening standards while extracting best practices from the broader agentic ecosystem.

---

## 1. Comparative Analysis: Learning from the Ecosystem

We strictly adhere to the **"Never Adopt, Always Mine"** policy for external frameworks.

| Framework | What to "Mine" (Repurpose) | Why we don't adopt |
|-----------|----------------------------|-------------------|
| **LangGraph** | Checkpointer interface, State Reducers, Compiled Graph mental model. | Cannot enforce hardware affinity *before* node execution; too many dependencies. |
| **Pydantic AI** | \`@tool\` ergonomics, type-hint-to-schema extraction, \`RunContext\` dependency injection. | Too heavyweight; opinionated \`Agent\` runtime conflicts with our microkernel. |
| **CrewAI / AutoGen** | Swarm collaboration patterns, agent role-playing templates. | High-latency; assume cloud LLM reliability; weak deterministic control. |
| **LangChain** | Integrations (standard tool schemas), prompt templates. | \"Kitchen sink\" complexity; violates our 70-line engine target. |

### Unique V2 Advantage: The \"Ghost\" Differentiator
Most frameworks treat hardware as a config string (\`device=\"cuda\"\`). **oramasys v2** is the only system where the **Policy Resolver** (L2) can veto an execution plan (L3) based on live LAN telemetry before the LLM is even called.

For a detailed breakdown of how v2 primitives improve upon our v1 baseline and mined features, see [**primitive-evolution.md**](./references/primitive-evolution.md).


---

## 2. Merging Plan (Phase 1 & 2 Integration)

This plan details how we will merge the "Gemini Hardening" suggestions into the initialized repositories without breaking existing commits.

### Step 1: \`perpetua-core\` Primitives
1. **\`gossip.py\`**: Refactor from "Direct-Write" to "Queue-Worker".
    - *Preserve*: SQLite schema and \`EventType\` definitions.
    - *Add*: \`asyncio.Queue\` and a background coroutine for batched commits.
2. **\`policy.py\`**: Update to support "Capability Rules".
    - *Enhance*: The \`model_hardware_policy.yml\` parser to handle ranges (e.g., \`min_vram: 12GB\`).

### Step 2: \`perpetua-core\` Engine
1. **\`engine.py\`**: Implement \`GraphPlugin\` and \`max_steps\`.
    - *Action*: Wrap the \`while node and node != END\` loop with a step counter.
    - *Action*: Inject \`plugin.on_node_start\` and \`on_node_end\` calls into the main loop.
2. **\`plugins/sentinel.py\`**: Create the new Sentinel Node (v2.5 early landing).
    - *Action*: Monitor \`state.metadata["risk_score"]\` after every node execution.

### Step 3: \`oramasys\` API Layer
1. **\`api/server.py\`**: Harden the "Glass Window".
    - *Action*: Ensure all endpoints wrap \`ainvoke\` in a \`try/except\` block that converts \`HardwareAffinityError\` to HTTP 400.

---

## 3. Best Practice Adoption: "Agentic Engineering" Roadmap

Based on the technical review of Karpathy's "March of Nines":

1. **Deterministic Probes**: Before an agent is allowed to write a file, a "Probe Node" must verify that the file exists and is accessible.
2. **Lesson-Triggered CI**: Future enhancement: the system should refuse to commit if a \`LESSONS.md\` entry hasn't been generated for a fixed bug.
3. **Structured Handoffs**: Every node handoff must include a "Why" in the \`PerpetuaState.metadata\`, ensuring the audit trail is human-readable.

---

## 4. Next Technical Steps (Plan Only)
1. **Audit existing tests** in \`/Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core/tests/\` to ensure they don't depend on "Monkey Patching."
2. **Draft the \`GraphPlugin\` base class** and prepare to migrate the existing \`checkpointer.py\` to use the new protocol.
---

## 5. Legacy Feature Migration: 4-Tier Discovery Recovery

The v1.0 RC implementation of \`discover.py\` provided a "clunky but crucial" disaster recovery mechanism that we must elevate into an elegant v2 primitive.

### The v1 Baseline (Archived in docs/archive/AGENT_RESUME_v1_legacy.md)
- **Mechanic**: 4-tier fallback: Live Probe → Last Discovery JSON → Backups → Static Profiles.
- **Impact**: Guaranteed system availability even when LAN endpoints (LM Studio/Ollama) were intermittently offline.

### The v2 "Ghost" Evolution
1. **Tiered Discovery Provider**: Implement a \`DiscoveryProvider\` class in \`perpetua-core/policy.py\`.
2. **Gossip Integration**: Discovered endpoints are emitted as \`load\` events to the \`GossipBus\`, making the latest "Live Truth" available to all agents without disk-polling.
3. **Resilient Routing**: The \`HardwarePolicyResolver\` will query the \`DiscoveryProvider\` to resolve \`PREFER\` tags against actual reachable hardware, defaulting to Tier 2/3/4 state if the live probe fails.

---

## 6. Engineering Mandate: Non-Destructive Operations (2026-05-02)

Following the accidental overwriting of v1 documentation, the following rules are now enforced:
- **Archive First**: Any legacy file (like \`AGENT_RESUME.md\`) being superseded must be moved to \`/docs/archive/\` before replacement.
- **Additive Edits**: We prioritize merging and appending over deleting.
- **Reference Integrity**: All updated documents must link to their archived predecessors to preserve historical logic (e.g., the 4-tier discovery logic).
