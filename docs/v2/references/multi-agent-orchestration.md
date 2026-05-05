# Feature Extraction: Multi-Agent Orchestration Patterns

> **Ref:** OpenAI Swarm, CrewAI, AutoGen

## 1. OpenAI Swarm: The "Handoff" Pattern
Swarm treats orchestration as a series of transfers. Agent A returns a "Transfer" object that tells the runner to switch context to Agent B.

### oramasys v2 Adaptation: Handoffs as Edges
In our \`MiniGraph\`, Swarm handoffs are represented by **Conditional Edges**.
- **Mechanic**: A node (Agent A) returns a delta containing \`{"next_agent": "Agent B"}\`. 
- **The Edge**: \`add_edge("Agent A", lambda state: state.scratchpad["next_agent"])\`.
- **Benefit**: Keeps the kernel stateless and fast while allowing dynamic routing.

## 2. CrewAI: The "Managerial" Hierarchy
CrewAI uses a "Manager" agent to break down tasks and assign them to workers. The manager maintains the "Parent" context.

### oramasys v2 Adaptation: Managers as Subgraphs
Instead of a single heavy manager node, we use **Subgraphs**.
- **Mechanic**: The "Manager" is a \`MiniGraph\` that contains nodes for "Planning," "Delegation," and "Aggregation."
- **Benefit**: Each step is deterministic and auditable via the \`GossipBus\`, preventing the manager from "hallucinating" the process.

## 3. AutoGen: "Nested Chats" & Multi-directional Flow
AutoGen allows agents to "talk it out" in group chats or spawn private side-chats to solve sub-problems.

### oramasys v2 Adaptation: Sentinel-Gated Recursion
- **Mechanic**: We use **Recursive Node Calls**. A node can trigger a subgraph (Side-Chat) and wait for its completion before merging the results back into the main state.
- **Enforcement**: This is where the \`max_steps\` guard (Gemini Hardening 7b) is critical. It prevents agents from getting stuck in an infinite "nested chat" loop.

## 4. Summary: The oramasys Way
We mine the **flexibility** of AutoGen but enforce it with the **determinism** of our graph engine.

| Pattern | Source | oramasys Implementation |
|---------|--------|-------------------------|
| Simple Transfer | Swarm | Conditional Edges |
| Task Delegation | CrewAI | Subgraph Nodes |
| Side-Bar Problem Solving | AutoGen | Recursive Subgraphs + Sentinel Guard |
