# Primitive Evolution: v1 vs. Mined vs. v2

> **Objective:** Shed accidental complexity and replace external dependencies (Redis) with local-first, high-performance primitives.

---

## 1. State Management

| Feature | v1 (v0.9.9.8) | Mined (LangGraph/Pydantic AI) | v2 (perpetua-core) |
|---------|---------------|-------------------------------|--------------------|
| **Backend** | Redis or In-Memory | SQLite (LangGraph) | **aiosqlite (Durable)** |
| **Atomicity** | Manual \`set_task_state\` | Per-node atomic checkpoint | **Node-level \`SqliteCheckpointer\`** |
| **Concurrency** | Shared KV store | Thread-based versioning | **\`session_id\` indexing** |
| **Type Safety** | JSON Dicts | Pydantic v2 Models | **\`PerpetuaState\` (Pydantic v2)** |

**Lesson from v1:** v1's reliance on Redis made "Quickstart" difficult and airgapped use-cases impossible without setup overhead. v2's move to SQLite (mined from LangGraph) provides the same durability with zero setup.

---

## 2. Messaging & Orchestration

| Feature | v1 (v0.9.9.8) | Mined (Swarm/CrewAI) | v2 (MiniGraph) |
|---------|---------------|----------------------|----------------|
| **Pattern** | Async Pub/Sub Bus | Handoffs & Hierarchy | **Graph-Edge Routing** |
| **Log** | Console/Standard Log | N/A | **\`GossipBus\` Audit Trail** |
| **Handoff** | \`parallel_delegate\` | \`transfer_to_agent\` | **Conditional Edges** |
| **State Sync** | Manual Message Passing | Shared State Object | **Shared \`PerpetuaState\`** |

**Lesson from v1:** Manual message passing (\`AgentMessage\`) in v1 led to context loss and complex "result subscription" loops. v2 uses the shared state model (mined from LangGraph/Swarm), where edges determine the next node based on the state itself.

---

## 3. Tool Ergonomics

| Feature | v1 (v0.9.9.8) | Mined (Pydantic AI) | v2 (Graph Tools) |
|---------|---------------|---------------------|------------------|
| **Schema** | Manual JSON Defs | Type-Hint Extraction | **\`@tool\` Decorator (4h)** |
| **Context** | Passed in payload | \`RunContext\` injection | **State Auto-Injection** |
| **Validation** | Post-execution check | Pre-execution schema | **Pydantic v2 Validation** |

**Lesson from v1:** Boilerplate for tool definitions made adding new skills slow. v2 adopts Pydantic AI's "Code-as-Schema" approach, reducing skill authoring time by ~70%.

---

## 4. Synthesis: The v2 Integration
We are housing these mined features in a **Microkernel**.
- **Ghost Ready**: By using the \`GossipBus\` (SQLite) instead of a message bus, we can "ghost" into an existing environment and leave a permanent audit trail without disturbing other processes.
- **Nimble Structure**: The entire \`perpetua_core\` engine is smaller than just the v1 \`message_bus.py\`, yet it provides atomic resumption and HITL interrupts.
