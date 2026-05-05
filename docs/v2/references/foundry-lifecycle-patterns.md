# Feature Extraction: Foundry Lifecycle & Evaluation

> **Ref:** Microsoft Foundry (Azure AI Foundry)

## 1. Evaluation: "Golden Datasets" & LLM-as-a-Judge
Foundry treats evaluation as a mandatory unit test. It uses high-reasoning models to score sub-agent outputs against a "Golden Dataset" of expected results.

### oramasys v2 Adaptation: Verification Nodes
In our \`MiniGraph\`, every critical task node is followed by a **Verification Node**.
- **Mechanic**: The Verification Node uses a "Critic" model (e.g., Qwen 35B) to score the \`PerpetuaState.scratchpad\` contents.
- **The Logic**: If the score is below the \`elegance_threshold\` (defined in \`agent_registry.json\`), the conditional edge routes the graph back to the "Refiner" node rather than the "End".

## 2. Infrastructure: Isolated MicroVMs & Identity
Foundry runs each session in an isolated microVM and assigns each agent a unique identity (Entra ID).

### oramasys v2 Adaptation: ToolNode Sandboxing (MAESTRO Layer 4)
We cannot provide full microVMs in a "nimble" stack, but we can repurpose the **Sandbox Constraint**.
- **Mechanic**: Our \`ToolNode\` (4f) will use the \`bubblewrap\` (Linux) or \`sandbox-exec\` (macOS) command-line utilities to restrict the subprocess's filesystem access to a temporary \`session_id\` directory.
- **Identity**: Every \`GossipBus\` event is tagged with the \`session_id\` and \`agent_id\`, creating an immutable audit trail of which "identity" took which action.

## 3. The "Magentic" Pattern: Dynamic Routing
Foundry supports "Magentic" orchestration where the system determines the best agent for the task on the fly.

### oramasys v2 Adaptation: Policy-Gated Dynamic Routing
- **Mechanic**: We use our **HardwarePolicyResolver** (L2) as the "Magentic" gate.
- **The Flow**: The Orchestrator proposes a list of 3 agents. The Resolver filters them based on **live LAN telemetry**. The best reachable agent is then selected.

## 4. Summary: The oramasys Way
We mine the **Accountability** of Foundry but implement it using **Subprocess Sandboxing** and **Graph-Level Verification**.

| Feature | Foundry Implementation | oramasys Adaptation |
|---------|------------------------|---------------------|
| Evaluation | LLM-as-a-Judge | Verification Nodes + State Reducers |
| Isolation | MicroVMs | Subprocess Sandboxing (OS-native) |
| Routing | Magentic | Policy-Gated Dynamic Routing |
