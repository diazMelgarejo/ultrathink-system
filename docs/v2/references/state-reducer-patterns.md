# Feature Extraction: LangGraph State Reducers & Parallelism

> **Goal:** Repurpose the "Reducer" pattern for conflict-free state updates during parallel node execution.

## 1. The "V1 Hack" Baseline

In v0.9.9.8, orchestration was strictly sequential:

```python
# v1 style (sequential)

for stage in STAGE_SEQUENCE:
    output = await run_stage(stage, state)
    state.stage_outputs[stage.value] = output
```

**Problem**: No support for parallel agent work (e.g., 5 parallel Executors). If two agents write to the same key, the last one wins, leading to data loss.

## 2. LangGraph "Magic" (Technical Analysis)

LangGraph uses **Reducers** defined in the state schema:

- **\`Annotated[list, operator.add]\`**: Appends all updates into a single list.
- **Custom Reducers**: Functions like \`merge_dicts(old, new)\` that can handle deep-merging or deduplication.

## 3. oramasys v2: The "Reducer" Implementation

Our \`perpetua_core/state.py\` (\`PerpetuaState\`) will implement a native \`merge()\` method that acts as a global reducer.

### Key Logic (Planned for state.py)

```python
class PerpetuaState(BaseModel):
    messages: list[dict] = Field(default_factory=list)
    scratchpad: dict = Field(default_factory=dict)

    def merge(self, delta: dict) -> "PerpetuaState":
        # Accumulation Pattern (Mined from LangGraph)
        new_messages = self.messages + delta.get("messages", [])
        
        # Merge Pattern (Custom Logic)
        new_scratchpad = {**self.scratchpad, **delta.get("scratchpad", {})}
        
        return self.model_copy(update={
            "messages": new_messages,
            "scratchpad": new_scratchpad,
            "nodes_visited": [*self.nodes_visited, delta.get("current_node")]
        })
```

## 4. Integration with Primitives

- **Parallel Fan-Out**: The \`MiniGraph\` engine can now spawn multiple \`await\` calls for nodes in a "Superstep." Their returned deltas are then sequentially piped through \`state.merge()\`.
- **Audit Trace**: Because every merge appends to \`nodes_visited\`, we have a deterministic proof of which parallel agent finished first.
- **Safety**: Prevents the "Last Write Wins" race condition without requiring a heavy lock mechanism.
