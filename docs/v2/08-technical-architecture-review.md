# 08 — Technical Architecture Review (Gemini-Analyzer)

> **Status:** Active | Added 2026-05-02
> **Purpose:** Address feasibility concerns from `05-feasibility-review.md` and resolve OQ1–OQ12 from `06-open-questions.md` by synthesizing industry-standard research (MAESTRO, SWARM, Karpathy) into the oramasys v2 microkernel.

---

## 1. Executive Summary

The oramasys v2 architecture succeeds where other frameworks (LangGraph, CrewAI) fail by treating **hardware as a primary citizen**. This review hardens the "Ghost Orchestrator" model by introducing deterministic safety primitives, capability-based routing, and a high-performance event bus. We maintain the "ruthless minimalism" of v2 while ensuring that safety and reliability are baked into the kernel, not just the prompts.

---

## 2. Ecosystem Synthesis & Reference Mapping

### A. MAESTRO 7-Layer Alignment (Ref: Perplexity)

We will map our kernel hooks directly to MAESTRO layers to ensure no security "wrinkles" are missed:

- **Layer 3 (Agent Frameworks)**: Resolved via `MiniGraph` (D8) — deterministic handoffs.
- **Layer 5 (Evaluation/Observability)**: Resolved via `GossipBus` (P9) — queryable audit trail.
- **Layer 6 (Security/Compliance)**: Resolved via `HardwarePolicyResolver` (P8) — hard affinity gate.
- **Layer 7 (Ecosystem)**: Resolved via `HITL Interrupts` (4d) — mandatory human-in-the-loop for high-risk tool calls.

### B. Karpathy’s "Agentic Engineering" (Ref: 2-GPT-5.5)

To address the "Compounding Failure" risk (March of Nines):

- **LLM-Wiki Pattern**: Our `LESSONS.md` and `SKILL.md` documents are the "Project Memory." v2 will enforce that every graph run concludes with a `GossipBus` event that triggers a "Lesson Proposal."
- **Test-Driven Spawning**: Agents must not spawn without a "Success Criterion" defined in their `PerpetuaState.scratchpad`.

---

## 3. Resolving Feasibility Concerns (`05-feasibility-review.md`)

### F1: The `GraphPlugin` Protocol

**Decision:** Standardize the plugin interface to prevent "Monkey Patching."

```python
# perpetua_core/graph/engine.py
from typing import Protocol

class GraphPlugin(Protocol):
    def on_node_start(self, state: PerpetuaState, node_name: str) -> None: ...
    def on_node_end(self, state: PerpetuaState, node_name: str, delta: dict) -> None: ...
```

This resolves the "leaky abstraction" risk by providing stable hooks for the Checkpointer and Interrupts.

### F2: Infinite Loop Protection (OQ12)

**Decision:** The `ainvoke` loop MUST include a step counter.

```python
async def ainvoke(self, state: PerpetuaState, max_steps: int = 50) -> PerpetuaState:
    steps = 0
    while node and node != self.end:
        if steps >= max_steps:
            raise RuntimeError(f"Max steps ({max_steps}) exceeded - possible infinite loop.")
        # ... execution logic ...
        steps += 1
```

### F3: GossipBus Scaling (OQ11)

**Decision:** Implement the "Hot-Write" pattern.

- Use `asyncio.Queue` for non-blocking `emit()`.
- A single background task manages the SQLite connection and performs batched commits every 500ms or 50 events. This reduces disk I/O overhead by ~90% in high-frequency graphs.

---

## 4. Resolving Open Questions (`06-open-questions.md`)

| # | Question | Resolved Decision |
|---|----------|-------------------|
| **OQ1** | **Pydantic AI** | Keep as a **Tool Schema Provider** ONLY. We use their \`@tool\` ergonomics but our own \`MiniGraph\` runtime. Stays out of the kernel. |
| **OQ2** | **GGUF Spec** | **Do not wait.** \`agate\` (OQ3) will be our de facto bridge. If GGUF adds metadata later, we will update our \`HardwarePolicyResolver\` to read it as a priority hint. |
| **OQ10** | **Capability-Based** | **Approved.** The \`model_hardware_policy.yml\` schema will support a \`requirements\` block (e.g., \`vram_min_gb: 12\`). |
| **OQ8** | **Naming** | Standardize on **\`optimize_for\`** (GPT scaffold) for consistency across the LAN API. |
| **OQ13** | **Shadow Model Pattern** | **Approved.** Adopt the Pydantic AI pattern of using \`inspect\` + \`create_model\` to generate tool schemas (MCP-ready) at import time. See \`references/pydantic-ai-extraction-deep-dive.md\`. |
| **OQ14** | **State Reducers** | **Approved.** Implement LangGraph-style reducers in \`PerpetuaState.merge()\` to handle parallel node updates without data loss. See \`references/state-reducer-patterns.md\`. |
| **OQ15** | **Prompt Primitives** | **Approved.** Move personas and task templates to \`agent_registry.json\`. Use a runtime \`build_agent_prompt\` utility to inject state variables. See \`references/prompt-and-task-primitives.md\`. |

---

## 5. Unique Contribution: The "Sentinel" Node

I am introducing the **Sentinel Node** concept as a built-in "SWARM Misalignment Kill-switch" (P2).

**The Structure:**
A special plugin that injects a `check_integrity()` call after every `N` nodes. It evaluates the `metadata["risk_score"]` and `metadata["goal_drift"]`. If thresholds are exceeded, it raises a `MAESTRO_VIOLATION` Interrupt immediately, forcing human intervention before the next agent is spawned.

---

## 6. Implementation Recommendation (The "Nimble" Vehicle)

- **Repo 1 (`perpetua-core`)**: Stays under 1,000 lines. Focuses on the "March of Nines" by making every operation retryable and auditable.
- **Repo 2 (`oramasys`)**: Acts as the "Glass Window." Handlers remain ≤ 10 lines. It is the composition layer where the 7-agent network is defined as a YAML-based graph.

**Next Course of Action:**

1. Update `perpetua_core/graph/engine.py` with the `max_steps` guard and `GraphPlugin` protocol.

---

## 7. Repository Locations (Amended 2026-05-02)

The active v2 repositories are confirmed to be located at:
\`/Users/lawrencecyremelgarejo/Documents/oramasys/\`

- \`agate/\`: Hardware Policy Specification
- \`oramasys/\`: Orchestration & API Layer
- \`perpetua-core/\`: Microkernel & Safety Primitives

All subsequent implementation and merging plans will target these paths.
