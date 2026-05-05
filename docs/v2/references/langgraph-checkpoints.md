# Feature Extraction: LangGraph Checkpointers

> **Goal:** Repurpose the "Compiled Graph" persistence model for our \`SqliteCheckpointer\`.

## 1. The Core Mechanic
LangGraph uses a **Thread ID + Checkpoint** key-value pair. This allows the same graph to handle multiple concurrent sessions (threads) while maintaining a versioned history of state.

## 2. Best Practices to Mine
- **State Reducers**: LangGraph allows defining *how* new data merges with old data (e.g., \`operator.add\` for message lists).
- **Atomic Writes**: Each node execution is wrapped in a transaction. If a node fails, the checkpoint remains at the *start* of that node, enabling perfect resumption.
- **Async Efficiency**: Use \`aiosqlite\` to ensure the checkpointer never blocks the event loop (aligned with Gemini Hardening 7c).

## 3. oramasys v2 Adaptation
We will adopt the **Thread ID** concept as our \`session_id\`. Our \`SqliteCheckpointer\` (Tier 3 plugin) will store the full \`PerpetuaState\` blob after every successful node transition, indexed by \`session_id\`.

**Reference Implementation Hint:**
```python
# We copy the "re-entry" logic:
def aresume(session_id: str, user_input: str):
    last_checkpoint = load_latest(session_id)
    # Re-inject into the node that raised the Interrupt
```
