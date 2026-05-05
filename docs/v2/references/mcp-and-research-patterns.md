# Feature Extraction: MCP & Perplexity Research Patterns

> **Ref:** Model Context Protocol (Anthropic), Perplexity (Research Agent)

## 1. MCP: The "Standardized Context" Standard
MCP provides a standard way to connect agents to tools and data. It uses a client-server architecture where the agent is the client and the tool provider is the server.

### oramasys v2 Adaptation: MCP-as-a-Language
We will not just "support" MCP; we will use its **Tool Definition Schema** as our internal tool format.
- **Mechanic**: All \`@tool\` decorated functions (4h) will automatically generate an MCP-compliant JSON schema.
- **Interoperability**: This makes our tools "Ghost-ready"—any external MCP-aware system (like Claude Code) can consume our \`perpetua-core\` tools without modification.

## 2. Perplexity: Multi-step Research Iteration
Perplexity succeeds by not just "searching," but by **Reasoning over Search Results**. It performs a search, reads the results, and then *proposes a follow-up search* if the answer is incomplete.

### oramasys v2 Adaptation: The "Deep Search" Graph
In our \`oramasys\` graph layer, research is not a single node; it is a **Recurrent Subgraph**.
- **The Loop**: 1. Search Node → 2. Analysis Node → 3. "Is Complete?" Router → (if no) → Back to Search.
- **Efficiency**: We use the **Sentinel Node** to monitor the token cost of this loop, ensuring it doesn't exceed the user's budget.

## 3. Summary: The oramasys Way
We mine the **connectivity** of MCP and the **persistence** of Perplexity research.

| Feature | Source | oramasys Implementation |
|---------|--------|-------------------------|
| Tool Interface | MCP | Pydantic-to-MCP Schema Autogen |
| Data Grounding | Perplexity | Recurrent "Deep Search" Subgraph |
| Security | MCP/MAESTRO | Capability-Gated ToolNode Access |
